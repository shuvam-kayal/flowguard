"""Deterministic income forecast for the policy layer."""
from statistics import mean
from typing import Any
from .features import split_transactions

def forecast_income(history: list[Any] | None, periods: int = 4) -> dict[str, Any]:
    credits, _ = split_transactions(history)
    if not credits: return {"next_period_income": 0.0, "periods": [0.0] * periods, "trend": "UNKNOWN", "confidence": .1}
    recent = credits[-min(4, len(credits)):]; baseline = mean(recent)
    slope = (mean(recent[-2:]) - mean(recent[:2])) / max(1, baseline) if len(recent) > 1 else 0
    values = [round(max(0, baseline * (1 + slope * (i + 1) / max(1, periods))), 2) for i in range(periods)]
    return {"next_period_income": values[0], "periods": values, "trend": "DECLINING" if slope < -.05 else "GROWING" if slope > .05 else "STABLE", "confidence": round(min(.95, .35 + len(credits) / 20), 3)}
