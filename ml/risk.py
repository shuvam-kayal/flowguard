"""Adaptive deterministic policy; card decisions can consume this policy."""
from typing import Any

def adaptive_policy(profile: Any, risk: dict[str, Any], forecast: dict[str, Any]) -> dict[str, Any]:
    def get(name: str, default: float = 0.0) -> float:
        value = getattr(profile, name, profile.get(name, default) if isinstance(profile, dict) else default)
        try: return max(0.0, float(value))
        except (TypeError, ValueError): return default
    score = float(risk.get("risk_score", .5)); buffer = get("emergency_buffer", get("savings_balance")); expenses = get("total_monthly_expenses"); predicted = float(forecast.get("next_period_income", 0))
    pct = max(10, min(50, 10 + round(score * 35) + (10 if forecast.get("trend") == "DECLINING" else 0)))
    safe = max(0, predicted - expenses - predicted * pct / 100)
    if score >= .67 or forecast.get("trend") == "DECLINING": action, rec = "PROTECT_BUFFER", "Reduce discretionary spending and preserve cash runway."
    elif score >= .34: action, rec = "BUILD_BUFFER", "Maintain a moderate reserve before increasing discretionary spend."
    else: action, rec = "MAINTAIN_BALANCE", "Income is comparatively stable; keep monitoring weekly."
    return {"action": action, "recommended_buffer_percent": pct, "recommended_weekly_release": round(max(0, predicted - expenses) / 4, 2), "safe_to_spend": round(safe, 2), "buffer_runway_months": round(buffer / max(1, expenses), 2), "credit_caution": score >= .67, "recommendation": rec}
