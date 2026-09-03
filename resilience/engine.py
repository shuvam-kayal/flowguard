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


def days_to_shock(forecast: dict, essential_daily: int) -> int | None:
    """First day index (0-based) in the forecast window where expected daily
    income dips below what's needed to cover essentials. Returns None if the
    window never dips that low, so callers must not assume a number exists.

    This reads Person 2's actual `daily_forecast` points — it is NOT a
    hardcoded lead time. If `daily_forecast` is missing or empty (e.g. an
    older/mocked forecast shape), we return None rather than guessing.
    """
    daily_fc = forecast.get("daily_forecast") or []
    for i, point in enumerate(daily_fc):
        if point["expected"] < essential_daily:
            return i
    return None


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


MODE_CAUTION = {"NORMAL": 1.0, "RECOVERY": 0.9, "WATCH": 0.75, "SHOCK": 0.5}


def safe_to_spend(profile: dict, forecast: dict, obligations: dict,
                  target_buffer: int, mode: str) -> tuple[int, int, int]:
    """
    Safe-to-spend, defined against conservative liquidity rather than a
    fixed fraction of average income:

        discretionary = (cash on hand + conservative 30-day income)
                         - mandatory obligations
                         - protected buffer cash

    We use `forecast["lower_bound"]` (the model's worst-case 30-day estimate)
    instead of an arbitrary share of the point forecast, so the number is
    defensible as "safe even if income comes in low," not a guess. On top of
    that we apply a mode-based caution multiplier: safe-to-spend is scaled
    down further in WATCH/SHOCK because forecast uncertainty is highest
    exactly when things are going wrong.

    Returns (daily, discretionary_cash, protected_cash).
    """
    cash_available = profile["current_balance"]
    conservative_income = forecast["lower_bound"]
    required_obligations = obligations["total_upcoming"]

    # never protect more cash than we actually expect to have on hand
    protected_cash = min(target_buffer, cash_available + conservative_income)

    discretionary_cash = max(0, cash_available + conservative_income
                             - required_obligations - protected_cash)

    horizon_days = 30
    daily = int(discretionary_cash / horizon_days * MODE_CAUTION[mode])
    return daily, discretionary_cash, protected_cash


def _days_coverage_fraction(days: float) -> float:
    """Piecewise-linear mapping from days-of-essential-cover to a 0..1 score
    fraction. Front-loaded on purpose: the first week of cover matters far
    more than the twentieth (0d=0%, 7d=35%, 14d=60%, 30d=100%), because going
    from 0 to 7 days changes whether a worker survives a bad week at all,
    while going from 23 to 30 days is comfort, not survival.
    """
    points = [(0, 0.0), (7, 0.35), (14, 0.60), (30, 1.0)]
    if days <= 0:
        return 0.0
    if days >= 30:
        return 1.0
    for (d0, f0), (d1, f1) in zip(points, points[1:]):
        if d0 <= days <= d1:
            t = (days - d0) / (d1 - d0)
            return f0 + t * (f1 - f0)
    return 1.0


DEBT_SAFE_THRESHOLD = 0.30  # standard debt-service-to-income guideline


def resilience_score(profile: dict, essential_daily: int | None = None) -> dict:
    """Score breakdown (caps sum to 100).

    `essential_daily` should be the obligation-derived essential spend so the
    emergency_buffer component agrees with the top-level `resilience_days`.
    Falls back to fixed_expenses/30 only when it isn't supplied.

    Every days-of-cover component (emergency_buffer, savings_consistency)
    uses the same `_days_coverage_fraction` curve, so "how many days can this
    person survive" is the consistent story behind the score \u2014 just applied
    to two different pools of money (dedicated buffer vs. general savings).
    debt_burden is scored against a standard debt-service-to-income
    threshold rather than an arbitrary multiplier.
    """
    p = profile
    inc_stab = round(CAP["income_stability"] *
                     (1 - _clamp(p["monthly_income_std"] / max(1, p["monthly_income_avg"]), 0, 1)))
    ess_daily = essential_daily if essential_daily and essential_daily > 0 else max(1, int(p["fixed_expenses"] / 30))

    buffer_days = resilience_days(p["emergency_buffer"], ess_daily)
    buf = round(CAP["emergency_buffer"] * _days_coverage_fraction(buffer_days))

    exp_cov = round(CAP["expense_coverage"] * _clamp(1 - (p["expense_to_income_ratio"] - 0.3), 0, 1))

    debt_ratio = p["monthly_emi"] / max(1, p["monthly_income_avg"])
    debt = round(CAP["debt_burden"] * _clamp(1 - debt_ratio / DEBT_SAFE_THRESHOLD, 0, 1))

    # general savings measured the same way as the buffer: days of essential
    # cover it would add on top, not a raw ratio to income.
    savings_days = resilience_days(p["savings_balance"], ess_daily)
    sav = round(CAP["savings_consistency"] * _days_coverage_fraction(savings_days))

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
    daily, discretionary, protected_cash = safe_to_spend(profile, forecast, obligations, target, mode)
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
            "bills": obligations["total_upcoming"],
            "buffer": profile["emergency_buffer"],
            "growth": 0 if mode in ("SHOCK", "WATCH") else int(profile["current_balance"] * 0.05),
        },
        "score_breakdown": breakdown,
    }


def recommend(profile: dict, res: dict, forecast: dict, obligations: dict | None = None) -> list:
    """Mode-aware, contract-shaped recommendations (see contract #6).

    `obligations` is optional and defaults to None so existing 3-arg callers
    (e.g. the backend before it's updated) keep working; when omitted we
    estimate essential_daily from fixed_expenses/30 instead of the real
    obligation figure. Pass `obligations` whenever you have it for an
    accurate days-to-shock estimate.
    """
    recs = []
    mode = res["mode"]
    essential_daily = (obligations["essential_daily_spend"] if obligations
                       else max(1, int(profile["fixed_expenses"] / 30)))

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
        days = days_to_shock(forecast, essential_daily)
        if days is not None:
            reason = ("Income dip predicted in the next few hours" if days == 0
                     else f"Income dip predicted in {days} day{'s' if days != 1 else ''}")
        else:
            # Weather flags elevated risk even though the visible window doesn't dip
            # below essentials \u2014 don't invent a day count we can't support.
            reason = "Forecast shows elevated income volatility ahead"
        recs.append({"type": "SAVE", "priority": "HIGH", "amount": amt,
                     "message": f"Move \u20b9{amt} to your emergency buffer",
                     "reason": reason})
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