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
    FORECAST_TREND_THRESHOLD, FORECAST_MIN_DAILY_BAND_FACTOR,
    MONTH_DAYS,
)
from backend.schemas.contracts import FinancialProfile, ForecastResult
try:
    from .features import FEATURE_NAMES, MIN_MODEL_HISTORY, daily_income_series, feature_row, normalize_history, summarize_history
    from .weather import to_weather
except ImportError:  # supports `python forecast/predict.py` from repository root
    from features import FEATURE_NAMES, MIN_MODEL_HISTORY, daily_income_series, feature_row, normalize_history, summarize_history
    from weather import to_weather


MODEL_PATH = Path(__file__).with_name("income_model.joblib")


def _load_model():
    """Load the optional trained artifact without making the API depend on it."""
    if not MODEL_PATH.exists():
        return None
    try:
        import joblib
        artifact = joblib.load(MODEL_PATH)
        if tuple(artifact.get("feature_names", ())) != FEATURE_NAMES:
            return None
        return artifact
    except (ImportError, OSError, ValueError, KeyError):
        return None


def _model_points(history: list | None, horizon: int) -> tuple[list[dict], float] | None:
    """Recursively produce daily estimates from the trained model when eligible."""
    artifact = _load_model()
    series = daily_income_series(history)
    if artifact is None or len(series) < MIN_MODEL_HISTORY:
        return None
    values = [amount for _, amount in series]
    next_day = series[-1][0] + timedelta(days=1)
    points: list[dict] = []
    for offset in range(horizon):
        forecast_day = next_day + timedelta(days=offset)
        row = feature_row(values, forecast_day)
        estimate = max(0, int(round(float(artifact["model"].predict([[row[name] for name in FEATURE_NAMES]])[0]))))
        values.append(estimate)
        points.append({"date": forecast_day.isoformat(), "expected": estimate})
    return points, float(artifact.get("residual_mae", 0.0))


def forecast_income(profile: FinancialProfile, history: list | None = None) -> ForecastResult:
    """
    Input:  FinancialProfile dict (+ optional daily earnings history list)
    Output: ForecastResult dict (see docs/api-contract.md #3)

    Uses a saved Random Forest model for histories of 28+ days when available.
    The explainable rolling-average model remains the cold-start/failure fallback.
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
    model_output = _model_points(history, FORECAST_HORIZON_DAYS)
    expected = daily * FORECAST_HORIZON_DAYS * (1 + FORECAST_TREND_FACTOR * trend_score)
    spread = max(daily * FORECAST_MIN_BAND_FACTOR, expected * min(0.45, FORECAST_BAND_VOLATILITY_FACTOR * volatility))
    if model_output:
        points, residual_mae = model_output
        # This is an estimated range based on observed validation error, not a CI.
        band = max(1, int(round(max(residual_mae, daily * FORECAST_MIN_DAILY_BAND_FACTOR))))
        for point in points:
            point["lower"] = max(0, point["expected"] - band)
            point["upper"] = point["expected"] + band
        expected = sum(point["expected"] for point in points)
        spread = band * sqrt(FORECAST_HORIZON_DAYS)
    else:
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


if __name__ == "__main__":
    import json as _json
    demo = {"worker_id": "W001", "name": "Demo", "occupation": "Demo", "current_balance": 0,
            "monthly_income_avg": 24000, "monthly_income_std": 6800, "income_trend": "DECLINING",
            "total_monthly_expenses": 18500, "fixed_expenses": 11000, "variable_expenses": 7500,
            "savings_balance": 5400, "emergency_buffer": 2000, "total_debt": 8000, "monthly_emi": 2000,
            "dependents": 0, "avg_work_hours_per_week": 0, "active_platforms": [], "expense_to_income_ratio": 0.77}
    print(_json.dumps(forecast_income(FinancialProfile(**demo)).model_dump(), indent=2, ensure_ascii=False)[:600])
