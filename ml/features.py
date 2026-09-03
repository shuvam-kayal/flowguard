"""Feature engineering for the transaction-derived vulnerability model.

The model deliberately avoids demographic and well-being fields from the
reference dataset. Every feature here can be derived from account activity,
balances, obligations, or income history.
"""
from __future__ import annotations

from statistics import mean, pstdev
from typing import Any, Iterable
from constants import RISK_TREND_SCORES

FEATURE_NAMES = (
    "income_volatility",
    "income_trend_score",
    "expense_burden",
    "buffer_coverage",
    "debt_service_burden",
    "income_gap_ratio",
)


def _amounts(values: Iterable[Any] | None) -> list[float]:
    if not values:
        return []
    result = []
    for item in values:
        if isinstance(item, dict) and str(item.get("type", item.get("direction", "CREDIT"))).upper() in {"DEBIT", "EXPENSE", "OUTFLOW"}:
            continue
        value = item.get("amount", 0) if isinstance(item, dict) else item
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        if value >= 0:
            result.append(value)
    return result


def _trend(values: list[float]) -> float:
    """Return a bounded slope proxy: negative means income is falling."""
    if len(values) < 2 or mean(values) == 0:
        return 0.0
    midpoint = len(values) // 2
    earlier, recent = mean(values[:midpoint]), mean(values[midpoint:])
    return max(-1.0, min(1.0, (recent - earlier) / max(1.0, mean(values))))


def build_features(profile: dict, history: list[Any] | None = None) -> dict[str, float]:
    """Build the six-feature model vector from a profile and optional income history."""
    avg = max(1.0, float(profile.get("monthly_income_avg", 0)))
    std = max(0.0, float(profile.get("monthly_income_std", 0)))
    income = _amounts(history)
    if len(income) >= 2:
        avg = max(1.0, mean(income))
        std = pstdev(income)

    expenses = max(0.0, float(profile.get("total_monthly_expenses", 0)))
    fixed = max(0.0, float(profile.get("fixed_expenses", 0)))
    buffer = max(0.0, float(profile.get("emergency_buffer", 0)))
    debt = max(0.0, float(profile.get("monthly_emi", 0)))
    trend_label = str(profile.get("income_trend", "STABLE")).upper()
    label_score = RISK_TREND_SCORES.get(trend_label, 0.0)
    trend_score = _trend(income) if len(income) >= 2 else label_score

    return {
        "income_volatility": min(2.0, std / avg),
        "income_trend_score": trend_score,
        "expense_burden": min(2.0, expenses / avg),
        "buffer_coverage": min(2.0, buffer / max(1.0, fixed)),
        "debt_service_burden": min(2.0, debt / avg),
        "income_gap_ratio": min(2.0, max(0.0, expenses - avg) / avg),
    }


def vectorize(features: dict[str, float]) -> list[float]:
    return [float(features[name]) for name in FEATURE_NAMES]
