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
try:
    from resilience.utils import get_value
except ModuleNotFoundError:  # Support direct execution: python resilience/engine.py
    from utils import get_value

# score component caps (must sum to 100)
CAP = {"income_stability": 25, "emergency_buffer": 25,
       "expense_coverage": 20, "debt_burden": 15, "savings_consistency": 15}


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))

def _get(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def days_to_shock(forecast, essential_daily: int) -> int | None:
    """Return the first forecast day where expected income falls below essentials."""
    daily_fc = get_value(forecast, "daily_forecast", []) or []

    for i, point in enumerate(daily_fc):
        expected = get_value(point, "expected", 0)

        if expected < essential_daily:
            return i

    return None


def decide_mode(risk, forecast, profile) -> str:
    """Determine NORMAL / WATCH / SHOCK / RECOVERY.

    Accepts both dictionaries and Pydantic model instances.
    """

    weather = get_value(forecast, "weather")
    trend = get_value(forecast, "trend") or get_value(
        profile, "income_trend"
    )

    risk_score = float(get_value(risk, "risk_score", 0.0))
    risk_level = get_value(risk, "risk_level")

    if weather == "SHOCK" or risk_score > 0.8:
        return "SHOCK"

    if trend == "RISING" and risk_level != "HIGH":
        emergency_buffer = get_value(profile, "emergency_buffer", 0)
        monthly_income_avg = get_value(profile, "monthly_income_avg", 0)

        return (
            "RECOVERY"
            if emergency_buffer < monthly_income_avg * 0.3
            else "NORMAL"
        )

    if weather == "WATCH" or risk_level == "HIGH":
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
    cash_available = get_value(profile, "current_balance", 0)
    conservative_income = get_value(forecast, "lower_bound", 0)
    required_obligations = get_value(obligations, "total_upcoming", 0)

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
    p = (
        profile
        if isinstance(profile, dict)
        else profile.model_dump()
    )
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


def evaluate(profile, risk, forecast, obligations) -> dict:
    mode = decide_mode(risk, forecast, profile)

    ess_daily = get_value(obligations, "essential_daily_spend", 0)

    emergency_buffer = get_value(profile, "emergency_buffer", 0)
    risk_level = get_value(risk, "risk_level", "MODERATE")
    worker_id = get_value(profile, "worker_id", "")

    rdays = resilience_days(emergency_buffer, ess_daily)

    target = buffer_target(ess_daily, risk_level)

    gap = max(0, target - emergency_buffer)

    daily, discretionary, protected_cash = safe_to_spend(
        profile,
        forecast,
        obligations,
        target,
        mode,
    )

    breakdown = resilience_score(profile, ess_daily)

    score = sum(breakdown.values())

    recommended_save = 0 if mode == "SHOCK" else int(gap / 20)

    return {
        "worker_id": worker_id,
        "safe_to_spend_daily": daily,
        "resilience_score": int(score),
        "resilience_days": rdays,
        "buffer_target": target,
        "buffer_current": emergency_buffer,
        "recommended_save": recommended_save,
        "mode": mode,
        "wallet_allocation": {
            "daily": discretionary,
            "bills": get_value(obligations, "total_upcoming", 0),
            "buffer": emergency_buffer,
            "growth": (
                0
                if mode in ("SHOCK", "WATCH")
                else int(get_value(profile, "current_balance", 0) * 0.05)
            ),
        },
        "score_breakdown": breakdown,
    }


def recommend(profile, res, forecast, obligations=None) -> list:
    """Mode-aware, contract-shaped recommendations (see contract #6).

    `obligations` is optional and defaults to None so existing 3-arg callers
    (e.g. the backend before it's updated) keep working; when omitted we
    estimate essential_daily from fixed_expenses/30 instead of the real
    obligation figure. Pass `obligations` whenever you have it for an
    accurate days-to-shock estimate.
    """
    recs = []
    profile_data = profile if isinstance(profile, dict) else profile.model_dump()
    res_data = res if isinstance(res, dict) else res.model_dump()
    forecast_data = forecast if isinstance(forecast, dict) else forecast.model_dump()
    obligations_data = (
        None if obligations is None
        else obligations if isinstance(obligations, dict)
        else obligations.model_dump()
    )

    mode = res_data["mode"]
    essential_daily = (
        obligations_data["essential_daily_spend"]
        if obligations_data
        else max(1, int(profile_data["fixed_expenses"] / 30))
    )

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

    if res_data["resilience_days"] < 7:
        recs.append({"type": "SAVE", "priority": "HIGH", "amount": max(200, res_data["recommended_save"]),
                     "message": "Your safety buffer is critically low \u2014 prioritise saving",
                     "reason": f"Only {res_data['resilience_days']} days of cover remaining"})

    if mode == "RECOVERY":
        amt = max(200, res_data["recommended_save"])
        recs.append({"type": "SAVE", "priority": "HIGH", "amount": amt,
                     "message": f"Income is climbing back \u2014 rebuild your buffer with \u20b9{amt}",
                     "reason": "Recovering after a dip; restore cover before increasing spending"})
        return recs

    if forecast_data["weather"] in ("WATCH", "SHOCK"):
        amt = max(200, res_data["recommended_save"])
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
        recs.append({"type": "SAVE", "priority": "MEDIUM", "amount": res_data["recommended_save"],
                     "message": f"On track \u2014 save \u20b9{res_data['recommended_save']} toward your buffer",
                     "reason": "Income is stable; build toward 30 resilience days"})
    return recs


if __name__ == "__main__":
    import json, os, sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    demo = os.path.join(os.path.dirname(__file__), "..", "data", "demo")
    personas = {p["worker_id"]: p for p in json.load(open(os.path.join(demo, "personas.json")))["personas"]}
    risks = json.load(open(os.path.join(demo, "sample_risk.json")))
    fc = json.load(open(os.path.join(demo, "sample_forecasts.json")))
    obl = json.load(open(os.path.join(demo, "sample_obligations.json")))
    for wid in personas:
        r = evaluate(personas[wid], risks[wid], fc[wid], obl[wid])
        print(f"{wid} {personas[wid]['name'][:12]:12} safe/day \u20b9{r['safe_to_spend_daily']:4} "
              f"score {r['resilience_score']:3} days {r['resilience_days']:2} mode {r['mode']}")
