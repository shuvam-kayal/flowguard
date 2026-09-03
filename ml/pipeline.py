"""End-to-end FlowGuard ML pipeline."""
from typing import Any
from .forecast import forecast_income
from .predict import predict_risk
from .risk import adaptive_policy

def financial_weather(risk: dict[str, Any], forecast: dict[str, Any]) -> dict[str, str]:
    level, trend = risk.get("risk_level", "MODERATE"), forecast.get("trend", "UNKNOWN")
    if level == "HIGH" or trend == "DECLINING": return {"condition": "STORM", "summary": "Protect cash and limit discretionary spending."}
    if level == "MODERATE" or trend == "UNKNOWN": return {"condition": "CLOUDY", "summary": "Keep a reserve and monitor income closely."}
    return {"condition": "CLEAR", "summary": "Cash flow is relatively stable."}

def analyze(profile: Any, history: list[Any] | None = None) -> dict[str, Any]:
    risk = predict_risk(profile, history); forecast = forecast_income(history); policy = adaptive_policy(profile, risk, forecast)
    return {"worker_id": risk["worker_id"], "risk": risk, "forecast": forecast, "policy": policy, "financial_weather": financial_weather(risk, forecast)}
