"""
Person 3 — Resilience Engine ("Financial Autopilot").
This is the NOVEL CORE: it turns risk + forecast + obligations into banking actions.

Unlike the ML/forecast stubs, this ships with a REAL calculation skeleton so you
can start refining formulas immediately. The functions below already produce
contract-shaped output. Tune the numbers; keep the shapes.

Inputs (all dicts, shapes in docs/api-contract.md):
  profile     : FinancialProfile
  risk        : RiskResult
  forecast    : ForecastResult
  obligations : ObligationSummary
Output:
  ResilienceResult (#5)  +  list[Recommendation] (#6)
"""
from __future__ import annotations

# score component caps (must sum to 100)
CAP = {"income_stability": 25, "emergency_buffer": 25,
       "expense_coverage": 20, "debt_burden": 15, "savings_consistency": 15}


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def decide_mode(risk: dict, forecast: dict, profile: dict) -> str:
    """State machine: NORMAL / WATCH / SHOCK / RECOVERY."""
    weather = forecast["weather"]
    trend = forecast["trend"]
    if weather == "SHOCK" or risk["risk_score"] > 0.8:
        return "SHOCK"
    if trend == "RISING" and profile["income_trend"] == "RISING" and risk["risk_level"] != "HIGH":
        # income climbing back after a dip
        return "RECOVERY" if profile["emergency_buffer"] < profile["monthly_income_avg"] * 0.3 else "NORMAL"
    if weather == "WATCH" or risk["risk_level"] == "HIGH":
        return "WATCH"
    return "NORMAL"


def resilience_days(buffer_current: int, essential_daily: int) -> int:
    if essential_daily <= 0:
        return 0
    return int(buffer_current / essential_daily)


def buffer_target(essential_daily: int, risk_level: str) -> int:
    target_days = {"HIGH": 30, "MODERATE": 21, "LOW": 14}[risk_level]
    return essential_daily * target_days


def safe_to_spend(profile: dict, forecast: dict, obligations: dict,
                  buffer_gap: int, mode: str) -> int:
    """
    Discretionary money spread over the next 30 days, after protecting
    obligations and a gentle buffer top-up. Forecast income helps cover bills.
    In SHOCK mode we tighten the belt (protect liquidity).
    """
    balance = profile["current_balance"]
    incoming = forecast["next_30_days"]
    # obligations not already covered by expected income
    net_obligations = max(0, obligations["total_upcoming"] - int(incoming * 0.5))
    # contribute toward buffer gap gently (more when safe, less in shock)
    topup_rate = {"NORMAL": 0.10, "RECOVERY": 0.08, "WATCH": 0.06, "SHOCK": 0.0}[mode]
    buffer_topup = max(0, min(buffer_gap, int(balance * topup_rate)))
    discretionary = max(0, balance - net_obligations - buffer_topup)
    daily = int(discretionary / 30)
    if mode == "SHOCK":
        daily = int(daily * 0.6)  # extra caution
    return daily, discretionary, net_obligations


def resilience_score(profile: dict) -> dict:
    p = profile
    inc_stab = round(CAP["income_stability"] *
                     (1 - _clamp(p["monthly_income_std"] / max(1, p["monthly_income_avg"]), 0, 1)))
    ess_daily = max(1, int(p["fixed_expenses"] / 30))
    rdays = resilience_days(p["emergency_buffer"], ess_daily)
    buf = round(CAP["emergency_buffer"] * _clamp(rdays / 30, 0, 1))
    exp_cov = round(CAP["expense_coverage"] * _clamp(1 - (p["expense_to_income_ratio"] - 0.3), 0, 1))
    debt = round(CAP["debt_burden"] *
                 (1 - _clamp(p["monthly_emi"] * 3 / max(1, p["monthly_income_avg"]), 0, 1)))
    sav = round(CAP["savings_consistency"] * _clamp(p["savings_balance"] / max(1, p["monthly_income_avg"]), 0, 1))
    return {
        "income_stability": inc_stab, "emergency_buffer": buf,
        "expense_coverage": exp_cov, "debt_burden": debt,
        "savings_consistency": sav,
    }


def evaluate(profile: dict, risk: dict, forecast: dict, obligations: dict) -> dict:
    mode = decide_mode(risk, forecast, profile)
    ess_daily = obligations["essential_daily_spend"]
    rdays = resilience_days(profile["emergency_buffer"], ess_daily)
    target = buffer_target(ess_daily, risk["risk_level"])
    gap = max(0, target - profile["emergency_buffer"])
    daily, discretionary, net_obl = safe_to_spend(profile, forecast, obligations, gap, mode)
    breakdown = resilience_score(profile)
    score = sum(breakdown.values())
    recommended_save = 0 if mode == "SHOCK" else int(gap / 20)

    return {
        "worker_id": profile["worker_id"],
        "safe_to_spend_daily": daily,
        "resilience_score": int(score),
        "resilience_days": rdays,
        "buffer_target": target,
        "buffer_current": profile["emergency_buffer"],
        "recommended_save": recommended_save,
        "mode": mode,
        "wallet_allocation": {
            "daily": discretionary,
            "bills": net_obl,
            "buffer": profile["emergency_buffer"],
            "growth": 0 if mode in ("SHOCK", "WATCH") else int(profile["current_balance"] * 0.05),
        },
        "score_breakdown": breakdown,
    }


def recommend(profile: dict, res: dict, forecast: dict) -> list:
    recs = []
    if res["resilience_days"] < 7:
        recs.append({"type": "SAVE", "priority": "HIGH", "amount": 300,
                     "message": "Your safety buffer is critically low \u2014 prioritise saving",
                     "reason": f"Only {res['resilience_days']} days of cover remaining"})
    if forecast["weather"] in ("WATCH", "SHOCK"):
        amt = max(200, res["recommended_save"])
        recs.append({"type": "SAVE", "priority": "HIGH", "amount": amt,
                     "message": f"Move \u20b9{amt} to your emergency buffer",
                     "reason": "Income dip predicted in the next 8 days"})
        recs.append({"type": "AVOID_CREDIT", "priority": "HIGH", "amount": None,
                     "message": "You don't need a loan right now",
                     "reason": "Your buffer + expected income can cover the shortfall"})
    else:
        recs.append({"type": "SAVE", "priority": "MEDIUM", "amount": res["recommended_save"],
                     "message": f"On track \u2014 save \u20b9{res['recommended_save']} toward your buffer",
                     "reason": "Income is stable; build toward 30 resilience days"})
    return recs


if __name__ == "__main__":
    import json, os
    demo = os.path.join(os.path.dirname(__file__), "..", "data", "demo")
    personas = {p["worker_id"]: p for p in json.load(open(os.path.join(demo, "personas.json")))["personas"]}
    risks = json.load(open(os.path.join(demo, "sample_risk.json")))
    fc = json.load(open(os.path.join(demo, "sample_forecasts.json")))
    obl = json.load(open(os.path.join(demo, "sample_obligations.json")))
    for wid in personas:
        r = evaluate(personas[wid], risks[wid], fc[wid], obl[wid])
        print(f"{wid} {personas[wid]['name'][:12]:12} safe/day \u20b9{r['safe_to_spend_daily']:4} "
              f"score {r['resilience_score']:3} days {r['resilience_days']:2} mode {r['mode']}")
