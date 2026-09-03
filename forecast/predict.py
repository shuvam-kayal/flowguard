"""Income forecast and Financial Weather for cold-start and history-backed users."""
from __future__ import annotations
from datetime import date, timedelta
from math import sqrt
try:
    from .features import normalize_history, summarize_history
except ImportError:  # supports `python forecast/predict.py` from repository root
    from features import normalize_history, summarize_history


def forecast_income(profile: dict, history: list | None = None) -> dict:
    """
    Input:  FinancialProfile dict (+ optional daily earnings history list)
    Output: ForecastResult dict (see docs/api-contract.md #3)

    Uses rolling averages, trend, volatility and day-of-week effects. This is
    intentionally transparent and works without a pre-trained artifact.
    """
    summary = summarize_history(history, profile)
    daily = summary["daily_avg"]
    volatility = min(1.0, summary["daily_std"] / max(1.0, daily))
    history_size = len(normalize_history(history))
    label = str(profile.get("income_trend", "STABLE")).upper()
    trend_score = summary["trend"] if history_size >= 2 else {"DECLINING": -0.35, "RISING": 0.2}.get(label, 0.0)
    trend = "DECLINING" if trend_score < -0.08 else "RISING" if trend_score > 0.08 else "STABLE"
    shock_probability = max(0.02, min(0.95, 0.18 + 0.55 * volatility + (0.22 if trend == "DECLINING" else 0)))
    expected = daily * 30 * (1 + 0.15 * trend_score)
    spread = max(daily * 0.15, expected * min(0.45, 0.35 * volatility))
    start = date.today()
    points = []
    for offset in range(30):
        factor = (1.08, 1.12, 1.05, 0.92, 0.96, 1.03, 1.10)[(start + timedelta(days=offset)).weekday()]
        point = max(0, int(daily * factor * (1 + trend_score * offset / 30)))
        band = max(1, int(max(daily * 0.2, spread / sqrt(30))))
        points.append({"date": (start + timedelta(days=offset)).isoformat(), "expected": point,
                       "lower": max(0, point - band), "upper": point + band})
    return {"worker_id": profile.get("worker_id", "W001"), "next_7_days": int(sum(p["expected"] for p in points[:7])),
            "next_30_days": int(sum(p["expected"] for p in points)), "lower_bound": max(0, int(expected - spread)),
            "upper_bound": int(expected + spread), "trend": trend, "shock_probability": round(shock_probability, 3),
            "weather": to_weather(shock_probability), "daily_forecast": points}


def to_weather(shock_probability: float) -> str:
    if shock_probability < 0.35:
        return "STABLE"
    if shock_probability <= 0.65:
        return "WATCH"
    return "SHOCK"


if __name__ == "__main__":
    print(json.dumps(forecast_income({"worker_id": "W001"}), indent=2, ensure_ascii=False)[:600])
