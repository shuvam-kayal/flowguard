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
    """State machine: NORMAL / WATCH / SHOCK / RECOVERY.

    Forecast is the forward-looking signal, so its `trend`/`weather` win when
    present; the profile's historical `income_trend` is only a fallback. This
    means RECOVERY is driven by Person 2's forecast, not just a static persona
    field, so it still fires once real forecasts flow in.
    """
    weather = forecast["weather"]
    trend = forecast.get("trend") or profile["income_trend"]  # forecast wins, profile is fallback
    if weather == "SHOCK" or risk["risk_score"] > 0.8:
        return "SHOCK"
    if trend == "RISING" and risk["risk_level"] != "HIGH":
        # income climbing back — RECOVERY while the buffer is still thin, else NORMAL
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


def resilience_score(profile: dict, essential_daily: int | None = None) -> dict:
    """Score breakdown (caps sum to 100).

    `essential_daily` should be the obligation-derived essential spend so the
    emergency_buffer component agrees with the top-level `resilience_days`.
    Falls back to fixed_expenses/30 only when it isn't supplied.
    """
    p = profile
    inc_stab = round(CAP["income_stability"] *
                     (1 - _clamp(p["monthly_income_std"] / max(1, p["monthly_income_avg"]), 0, 1)))
    ess_daily = essential_daily if essential_daily and essential_daily > 0 else max(1, int(p["fixed_expenses"] / 30))
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
    breakdown = resilience_score(profile, ess_daily)
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
    """Mode-aware, contract-shaped recommendations (see contract #6).

    Ordered by urgency; the frontend renders the list top-down. Each mode
    produces a distinct, human-readable action so the demo visibly changes
    when the worker's state changes.
    """
    recs = []
    mode = res["mode"]

    if mode == "SHOCK":
        # Income has collapsed: protect essentials, stop discretionary, don't borrow blindly.
        recs.append({"type": "REDUCE_SPEND", "priority": "HIGH", "amount": None,
                     "message": "Protect essentials \u2014 pause all non-essential spending",
                     "reason": "Income shock detected; preserving your buffer is the priority"})
        recs.append({"type": "RESERVE_BILL", "priority": "HIGH", "amount": None,
                     "message": "Ring-fence money for rent and EMI first",
                     "reason": "Upcoming obligations must be covered before anything else"})
        recs.append({"type": "AVOID_CREDIT", "priority": "HIGH", "amount": None,
                     "message": "Hold off on borrowing for now",
                     "reason": "Take on debt only through Credit Guard, never as a first response"})
        return recs

    if res["resilience_days"] < 7:
        recs.append({"type": "SAVE", "priority": "HIGH", "amount": max(200, res["recommended_save"]),
                     "message": "Your safety buffer is critically low \u2014 prioritise saving",
                     "reason": f"Only {res['resilience_days']} days of cover remaining"})

    if mode == "RECOVERY":
        amt = max(200, res["recommended_save"])
        recs.append({"type": "SAVE", "priority": "HIGH", "amount": amt,
                     "message": f"Income is climbing back \u2014 rebuild your buffer with \u20b9{amt}",
                     "reason": "Recovering after a dip; restore cover before increasing spending"})
        return recs

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