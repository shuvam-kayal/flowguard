"""Income forecast and Financial Weather for cold-start and history-backed users."""
from __future__ import annotations
import json
import sys
from datetime import date, timedelta
from math import sqrt
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from constants import (
    FORECAST_BASE_SHOCK_PROBABILITY, FORECAST_BAND_VOLATILITY_FACTOR,
    FORECAST_DECLINE_SHOCK_BONUS, FORECAST_HORIZON_DAYS,
    FORECAST_MAX_SHOCK_PROBABILITY, FORECAST_MIN_BAND_FACTOR,
    FORECAST_MIN_SHOCK_PROBABILITY, FORECAST_TREND_FACTOR,
    FORECAST_VOLATILITY_WEIGHT, FORECAST_WEEKDAY_MULTIPLIERS,
    FORECAST_DECLINING_TREND_SCORE, FORECAST_RISING_TREND_SCORE,
    FORECAST_TREND_THRESHOLD, FORECAST_WEATHER_SHOCK_THRESHOLD,
    FORECAST_WEATHER_STABLE_THRESHOLD, FORECAST_MIN_DAILY_BAND_FACTOR,
    MONTH_DAYS,
)
from backend.schemas.contracts import FinancialProfile, ForecastResult
try:
    from .features import normalize_history, summarize_history
except ImportError:  # supports `python forecast/predict.py` from repository root
    from features import normalize_history, summarize_history


def forecast_income(profile: FinancialProfile, history: list | None = None) -> ForecastResult:
    """
    Input:  FinancialProfile dict (+ optional daily earnings history list)
    Output: ForecastResult dict (see docs/api-contract.md #3)

    Uses rolling averages, trend, volatility and day-of-week effects. This is
    intentionally transparent and works without a pre-trained artifact.
    """
    profile = FinancialProfile.model_validate(profile)
    summary = summarize_history(history, profile.model_dump())
    daily = summary["daily_avg"]
    volatility = min(1.0, summary["daily_std"] / max(1.0, daily))
    history_size = len(normalize_history(history))
    label = profile.income_trend
    trend_score = summary["trend"] if history_size >= 2 else {"DECLINING": FORECAST_DECLINING_TREND_SCORE, "RISING": FORECAST_RISING_TREND_SCORE}.get(label, 0.0)
    trend = "DECLINING" if trend_score < -FORECAST_TREND_THRESHOLD else "RISING" if trend_score > FORECAST_TREND_THRESHOLD else "STABLE"
    shock_probability = max(FORECAST_MIN_SHOCK_PROBABILITY, min(FORECAST_MAX_SHOCK_PROBABILITY,
        FORECAST_BASE_SHOCK_PROBABILITY + FORECAST_VOLATILITY_WEIGHT * volatility +
        (FORECAST_DECLINE_SHOCK_BONUS if trend == "DECLINING" else 0)))
    expected = daily * FORECAST_HORIZON_DAYS * (1 + FORECAST_TREND_FACTOR * trend_score)
    spread = max(daily * FORECAST_MIN_BAND_FACTOR, expected * min(0.45, FORECAST_BAND_VOLATILITY_FACTOR * volatility))
    start = date.today()
    points = []
    for offset in range(FORECAST_HORIZON_DAYS):
        factor = FORECAST_WEEKDAY_MULTIPLIERS[(start + timedelta(days=offset)).weekday()]
        point = max(0, int(daily * factor * (1 + trend_score * offset / FORECAST_HORIZON_DAYS)))
        band = max(1, int(max(daily * FORECAST_MIN_DAILY_BAND_FACTOR, spread / sqrt(MONTH_DAYS))))
        points.append({"date": (start + timedelta(days=offset)).isoformat(), "expected": point,
                       "lower": max(0, point - band), "upper": point + band})
    return ForecastResult(
        worker_id=profile.worker_id,
        next_7_days=int(sum(p["expected"] for p in points[:7])),
        next_30_days=int(sum(p["expected"] for p in points)),
        lower_bound=max(0, int(expected - spread)),
        upper_bound=int(expected + spread),
        trend=trend,
        shock_probability=round(shock_probability, 3),
        weather=to_weather(shock_probability),
        daily_forecast=points,
    )


def to_weather(shock_probability: float) -> str:
    if shock_probability < FORECAST_WEATHER_STABLE_THRESHOLD:
        return "STABLE"
    if shock_probability <= FORECAST_WEATHER_SHOCK_THRESHOLD:
        return "WATCH"
    return "SHOCK"


if __name__ == "__main__":
    import json as _json
    demo = {"worker_id": "W001", "name": "Demo", "occupation": "Demo", "current_balance": 0,
            "monthly_income_avg": 24000, "monthly_income_std": 6800, "income_trend": "DECLINING",
            "total_monthly_expenses": 18500, "fixed_expenses": 11000, "variable_expenses": 7500,
            "savings_balance": 5400, "emergency_buffer": 2000, "total_debt": 8000, "monthly_emi": 2000,
            "dependents": 0, "avg_work_hours_per_week": 0, "active_platforms": [], "expense_to_income_ratio": 0.77}
    print(_json.dumps(forecast_income(FinancialProfile(**demo)).model_dump(), indent=2, ensure_ascii=False)[:600])
