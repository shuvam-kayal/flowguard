"""Small, dependency-free income-history feature builder for forecasting."""
from __future__ import annotations

from statistics import mean, pstdev
from constants import MONTH_DAYS


def normalize_history(history: list | None) -> list[float]:
    values = []
    for item in history or []:
        if isinstance(item, dict) and str(item.get("type", item.get("direction", "CREDIT"))).upper() in {"DEBIT", "EXPENSE", "OUTFLOW"}:
            continue
        raw = item.get("amount", 0) if isinstance(item, dict) else item
        try:
            amount = float(raw)
        except (TypeError, ValueError):
            continue
        if amount >= 0:
            values.append(amount)
    return values


def summarize_history(history: list | None, profile: dict) -> dict[str, float]:
    values = normalize_history(history)
    fallback = max(0.0, float(profile.get("monthly_income_avg", 0))) / MONTH_DAYS
    if not values:
        values = [fallback]
    avg = max(1.0, mean(values))
    recent = mean(values[-7:])
    previous = mean(values[-14:-7]) if len(values) >= 14 else avg
    return {"daily_avg": avg, "daily_std": pstdev(values) if len(values) > 1 else float(profile.get("monthly_income_std", 0)) / MONTH_DAYS,
            "recent_avg": recent, "trend": max(-1.0, min(1.0, (recent - previous) / avg))}
