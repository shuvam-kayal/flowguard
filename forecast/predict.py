"""
Person 2 — Income Forecasting + Financial Weather.
STUB: returns mock ForecastResult so downstream can build today.
Replace internals with your rolling-average / XGBoost forecaster later.
OUTPUT SHAPE must match ForecastResult in the contract.
"""
import json
import os

DEMO = os.path.join(os.path.dirname(__file__), "..", "data", "demo", "sample_forecasts.json")


def forecast_income(profile: dict, history: list | None = None) -> dict:
    """
    Input:  FinancialProfile dict (+ optional daily earnings history list)
    Output: ForecastResult dict (see docs/api-contract.md #3)

    TODO(Person 2): engineer features (7/14/30-day avg, day-of-week, trend,
    volatility), fit XGBoost/RandomForest or a time-series model, produce
    daily_forecast + bounds + shock_probability, then map to weather.
    """
    wid = profile.get("worker_id", "W001")
    with open(DEMO) as f:
        mocks = json.load(f)
    return mocks.get(wid, mocks["W001"])


def to_weather(shock_probability: float) -> str:
    if shock_probability < 0.35:
        return "STABLE"
    if shock_probability <= 0.65:
        return "WATCH"
    return "SHOCK"


if __name__ == "__main__":
    print(json.dumps(forecast_income({"worker_id": "W001"}), indent=2, ensure_ascii=False)[:600])
