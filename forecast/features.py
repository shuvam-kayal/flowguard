"""Time-series feature engineering shared by the income forecast pipeline."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from statistics import mean, pstdev
from typing import Any

from constants import MONTH_DAYS

FEATURE_NAMES = (
    "lag_1", "lag_2", "lag_3", "lag_7", "mean_7", "mean_14", "mean_28",
    "std_7", "std_14", "zero_days_7", "momentum_7", "acceleration", "weekday",
)
MIN_MODEL_HISTORY = 28


def _is_income(item: dict[str, Any]) -> bool:
    return str(item.get("type", item.get("direction", "CREDIT"))).upper() not in {"DEBIT", "EXPENSE", "OUTFLOW"}


def normalize_history(history: list | None) -> list[float]:
    """Return non-negative income amounts, excluding debit-like transactions."""
    values: list[float] = []
    for item in history or []:
        if isinstance(item, dict) and not _is_income(item):
            continue
        raw = item.get("amount", item.get("income", 0)) if isinstance(item, dict) else item
        try:
            amount = float(raw)
        except (TypeError, ValueError):
            continue
        if amount >= 0:
            values.append(amount)
    return values


def daily_income_series(history: list | None) -> list[tuple[date, float]]:
    """Aggregate dated transactions per day; number-only values are consecutive days."""
    dated: dict[date, float] = {}
    undated: list[float] = []
    for item in history or []:
        if not isinstance(item, dict):
            try:
                amount = float(item)
            except (TypeError, ValueError):
                continue
            if amount >= 0:
                undated.append(amount)
            continue
        if not _is_income(item):
            continue
        try:
            amount = float(item.get("amount", item.get("income", 0)))
        except (TypeError, ValueError):
            continue
        if amount < 0:
            continue
        try:
            day = datetime.fromisoformat(str(item.get("date") or item.get("timestamp")).replace("Z", "+00:00")).date()
        except (TypeError, ValueError):
            undated.append(amount)
            continue
        dated[day] = dated.get(day, 0.0) + amount
    if dated:
        start, end = min(dated), max(dated)
        return [(start + timedelta(days=index), dated.get(start + timedelta(days=index), 0.0)) for index in range((end - start).days + 1)]
    start = date.today() - timedelta(days=max(0, len(undated) - 1))
    return [(start + timedelta(days=index), amount) for index, amount in enumerate(undated)]


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


def feature_row(values: list[float], target_date: date) -> dict[str, float]:
    """Build leakage-free features from daily values preceding ``target_date``."""
    if len(values) < MIN_MODEL_HISTORY:
        raise ValueError(f"At least {MIN_MODEL_HISTORY} prior daily values are required")
    def window(days: int) -> list[float]: return values[-days:]
    mean_7, mean_14, mean_28 = mean(window(7)), mean(window(14)), mean(window(28))
    previous_7, previous_14 = mean(values[-14:-7]), mean(values[-21:-7])
    return {"lag_1": values[-1], "lag_2": values[-2], "lag_3": values[-3], "lag_7": values[-7],
            "mean_7": mean_7, "mean_14": mean_14, "mean_28": mean_28,
            "std_7": pstdev(window(7)), "std_14": pstdev(window(14)),
            "zero_days_7": float(sum(value == 0 for value in window(7))),
            "momentum_7": mean_7 - previous_7,
            "acceleration": (mean_7 - previous_7) - (previous_7 - previous_14),
            "weekday": float(target_date.weekday())}


def build_training_rows(series: list[tuple[date, float]]) -> list[tuple[dict[str, float], float]]:
    """Create chronological supervised examples, where every target is in the future."""
    values = [value for _, value in series]
    return [(feature_row(values[:index], day), value) for index, (day, value) in enumerate(series) if index >= MIN_MODEL_HISTORY]
