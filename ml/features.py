"""Transaction-derived feature engineering for the FlowGuard risk model."""
from __future__ import annotations

from statistics import mean, pstdev
from typing import Any, Iterable

FEATURE_NAMES = (
    "income_volatility", "income_trend_score", "expense_burden", "buffer_coverage",
    "debt_service_burden", "income_gap_ratio", "payment_frequency_variance",
    "essential_spend_ratio",
)


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return default


def split_transactions(history: Iterable[Any] | None) -> tuple[list[float], list[float]]:
    """Return non-negative credits and debits from mixed transaction records."""
    credits, debits = [], []
    for item in history or []:
        if isinstance(item, dict):
            amount = _number(item.get("amount", item.get("value", 0)))
            direction = str(item.get("type", item.get("direction", "CREDIT"))).upper()
            (debits if direction in {"DEBIT", "EXPENSE", "OUTFLOW", "WITHDRAWAL"} else credits).append(amount)
        else:
            amount = _number(item)
            if amount:
                credits.append(amount)
    return credits, debits


def _trend(values: list[float]) -> float:
    if len(values) < 2 or mean(values) <= 0:
        return 0.0
    midpoint = max(1, len(values) // 2)
    return max(-1.0, min(1.0, (mean(values[midpoint:]) - mean(values[:midpoint])) / mean(values)))


def _payment_frequency_variance(history: list[Any] | None) -> float:
    """Bounded proxy for irregular payment frequency when timestamps are absent."""
    if not history:
        return 0.5
    credits, _ = split_transactions(history)
    length_component = abs(len(history) - 6) / 6
    amount_component = pstdev(credits) / mean(credits) if len(credits) > 1 and mean(credits) > 0 else 0.0
    return min(2.0, max(0.0, 0.25 + length_component + amount_component))


def build_features(profile: Any, history: list[Any] | None = None) -> dict[str, float]:
    """Build the eight-feature model vector from profile and transactions."""
    if hasattr(profile, "model_dump"):
        profile = profile.model_dump()
    profile = dict(profile or {})
    credits, debits = split_transactions(history)
    income = credits or [_number(profile.get("monthly_income_avg"))]
    average_income = max(1.0, mean(income))
    income_std = pstdev(income) if len(income) > 1 else _number(profile.get("monthly_income_std"))
    expenses = sum(debits) if debits else _number(profile.get("total_monthly_expenses"))
    fixed_expenses = _number(profile.get("fixed_expenses", expenses))
    buffer = _number(profile.get("emergency_buffer", profile.get("savings_balance", 0)))
    monthly_emi = _number(profile.get("monthly_emi"))
    return {
        "income_volatility": min(2.0, income_std / average_income),
        "income_trend_score": _trend(income),
        "expense_burden": min(2.0, expenses / average_income),
        "buffer_coverage": min(2.0, buffer / max(1.0, fixed_expenses)),
        "debt_service_burden": min(2.0, monthly_emi / average_income),
        "income_gap_ratio": min(2.0, max(0.0, expenses - average_income) / average_income),
        "payment_frequency_variance": _payment_frequency_variance(history),
        "essential_spend_ratio": fixed_expenses / max(1.0, expenses),
    }


def vectorize(features: dict[str, float]) -> list[float]:
    return [float(features[name]) for name in FEATURE_NAMES]
