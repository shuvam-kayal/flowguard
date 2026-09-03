"""Transaction-derived feature engineering for the FlowGuard risk model.

Contract
--------
``build_features`` always returns a ``dict`` with exactly the eight keys
listed in ``FEATURE_NAMES``, in order, with finite float values in the
documented range.  Callers must never see a NaN, ±inf, or KeyError.
"""
from __future__ import annotations

import math
from statistics import mean, pstdev
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Feature contract
# ---------------------------------------------------------------------------

# The canonical order here is the only source of truth for column ordering.
# train.py, predict.py, and generate_data.py all import this tuple.
# Do not reorder without retraining the model and regenerating the schema.
FEATURE_NAMES: tuple[str, ...] = (
    "income_volatility",        # [0, 2]  coefficient of variation of income
    "income_trend_score",       # [-1, 1] sign: negative = declining
    "expense_burden",           # [0, 2]  total expenses / avg income
    "buffer_coverage",          # [0, 2]  buffer / fixed expenses
    "debt_service_burden",      # [0, 2]  monthly EMI / avg income
    "income_gap_ratio",         # [0, 2]  max(0, expenses − income) / income
    "payment_frequency_variance",  # [0, 2]  irregular payment proxy
    "essential_spend_ratio",    # [0, 1]  fixed / total expenses
)

# Per-feature valid range for final clipping.  Keeps the vector in the same
# domain that the training data occupies.
_CLIP: dict[str, tuple[float, float]] = {
    "income_volatility":           (0.0, 2.0),
    "income_trend_score":          (-1.0, 1.0),
    "expense_burden":              (0.0, 2.0),
    "buffer_coverage":             (0.0, 2.0),
    "debt_service_burden":         (0.0, 2.0),
    "income_gap_ratio":            (0.0, 2.0),
    "payment_frequency_variance":  (0.0, 2.0),
    "essential_spend_ratio":       (0.0, 1.0),
}

# Default (safe, mid-risk) feature values used when the profile and history
# together cannot produce a meaningful estimate.
_DEFAULTS: dict[str, float] = {
    "income_volatility":           0.5,
    "income_trend_score":          0.0,
    "expense_burden":              0.75,
    "buffer_coverage":             0.5,
    "debt_service_burden":         0.1,
    "income_gap_ratio":            0.0,
    "payment_frequency_variance":  0.5,
    "essential_spend_ratio":       0.7,
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe(value: float, default: float = 0.0) -> float:
    """Return *value* if it is a finite float, otherwise *default*."""
    try:
        f = float(value)
        return default if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return default


def _number(value: Any, default: float = 0.0) -> float:
    """Parse *value* as a non-negative float, with a floor of 0."""
    try:
        result = float(value)
        return max(0.0, result) if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default


def _clip(name: str, value: float) -> float:
    """Clip *value* to the documented range for feature *name*."""
    lo, hi = _CLIP.get(name, (0.0, 2.0))
    clamped = max(lo, min(hi, value))
    # Final NaN/inf guard — should never trigger after _safe(), but be safe.
    return clamped if math.isfinite(clamped) else _DEFAULTS[name]


# ---------------------------------------------------------------------------
# Transaction splitting
# ---------------------------------------------------------------------------

def split_transactions(history: Iterable[Any] | None) -> tuple[list[float], list[float]]:
    """Return non-negative credits and debits from mixed transaction records.

    Accepts both numeric scalars (treated as credits) and dicts with
    ``amount``/``type`` keys.  Empty or None *history* returns two empty lists.
    """
    credits: list[float] = []
    debits: list[float] = []
    for item in history or []:
        if isinstance(item, dict):
            amount = _number(item.get("amount", item.get("value", 0)))
            direction = str(item.get("type", item.get("direction", "CREDIT"))).upper()
            if direction in {"DEBIT", "EXPENSE", "OUTFLOW", "WITHDRAWAL"}:
                debits.append(amount)
            else:
                credits.append(amount)
        else:
            amount = _number(item)
            if amount > 0:
                credits.append(amount)
    return credits, debits


# ---------------------------------------------------------------------------
# Feature calculators
# ---------------------------------------------------------------------------

def _income_volatility(income: list[float], average_income: float) -> float:
    """Coefficient of variation of income.  Zero when only one data point."""
    if len(income) < 2 or average_income <= 0:
        return 0.0
    std = _safe(pstdev(income), 0.0)
    return _safe(std / average_income, 0.0)


def _trend(values: list[float]) -> float:
    """Normalised slope in [-1, 1]; 0 when fewer than two points or mean ≤ 0."""
    if len(values) < 2:
        return 0.0
    avg = _safe(mean(values), 0.0)
    if avg <= 0:
        return 0.0
    midpoint = max(1, len(values) // 2)
    first_half = values[:midpoint]
    second_half = values[midpoint:]
    # Guard against empty halves after split.
    if not first_half or not second_half:
        return 0.0
    slope = _safe((mean(second_half) - mean(first_half)) / avg, 0.0)
    return max(-1.0, min(1.0, slope))


def _payment_frequency_variance(history: list[Any] | None) -> float:
    """Bounded proxy for irregular payment frequency when timestamps are absent.

    Returns a value in [0, 2].  Falls back to 0.5 (mid-risk) when there is no
    history so that inference is conservative rather than falsely optimistic.
    """
    if not history:
        return 0.5
    credits, _ = split_transactions(history)
    # Length component: how far the number of transactions is from a "normal"
    # fortnightly window of ~6 transactions.
    length_component = _safe(abs(len(history) - 6) / 6, 0.0)
    # Amount component: coefficient of variation of credit amounts.
    if len(credits) > 1:
        avg_c = _safe(mean(credits), 0.0)
        amount_component = _safe(pstdev(credits) / avg_c, 0.0) if avg_c > 0 else 0.0
    else:
        amount_component = 0.0
    return min(2.0, max(0.0, 0.25 + length_component + amount_component))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_features(profile: Any, history: list[Any] | None = None) -> dict[str, float]:
    """Build the eight-feature model vector from *profile* and *history*.

    Guarantees
    ----------
    * Always returns a dict with exactly the keys in ``FEATURE_NAMES``.
    * All values are finite floats within the ranges documented in ``_CLIP``.
    * Never raises; degraded inputs produce conservative (mid-risk) defaults.
    """
    # --- Normalise profile to a plain dict --------------------------------
    if hasattr(profile, "model_dump"):
        profile = profile.model_dump()
    profile = dict(profile) if profile else {}

    # --- Parse history ----------------------------------------------------
    credits, debits = split_transactions(history)

    # --- Income -----------------------------------------------------------
    # Use transaction credits when available; fall back to profile field.
    income: list[float] = credits if credits else [_number(profile.get("monthly_income_avg"))]
    # Guard: ensure at least one positive value so we never divide by zero.
    income = [v for v in income if v > 0] or [1.0]
    average_income = max(1.0, _safe(mean(income), 1.0))

    # --- Expenses ---------------------------------------------------------
    if debits:
        expenses = _safe(sum(debits), 0.0)
    else:
        expenses = _number(profile.get("total_monthly_expenses"))

    fixed_expenses = _number(profile.get("fixed_expenses", expenses))
    # fixed_expenses should never exceed total expenses.
    fixed_expenses = min(fixed_expenses, expenses) if expenses > 0 else fixed_expenses

    # --- Buffer & debt ----------------------------------------------------
    buffer = _number(profile.get("emergency_buffer", profile.get("savings_balance", 0)))
    monthly_emi = _number(profile.get("monthly_emi"))

    # --- Compute raw features --------------------------------------------
    raw: dict[str, float] = {
        "income_volatility":
            _income_volatility(income, average_income),
        "income_trend_score":
            _trend(income),
        "expense_burden":
            _safe(expenses / average_income, _DEFAULTS["expense_burden"]),
        "buffer_coverage":
            _safe(buffer / max(1.0, fixed_expenses), _DEFAULTS["buffer_coverage"]),
        "debt_service_burden":
            _safe(monthly_emi / average_income, 0.0),
        "income_gap_ratio":
            _safe(max(0.0, expenses - average_income) / average_income, 0.0),
        "payment_frequency_variance":
            _payment_frequency_variance(history),
        "essential_spend_ratio":
            _safe(fixed_expenses / max(1.0, expenses), _DEFAULTS["essential_spend_ratio"])
            if expenses > 0 else _DEFAULTS["essential_spend_ratio"],
    }

    # --- Clip, NaN-guard, and return in canonical order ------------------
    return {name: _clip(name, raw.get(name, _DEFAULTS[name])) for name in FEATURE_NAMES}


def vectorize(features: dict[str, float]) -> list[float]:
    """Return features as a list in the canonical ``FEATURE_NAMES`` order.

    Raises ``KeyError`` if *features* is missing any required key — callers
    should always use ``build_features`` to construct the dict.
    """
    return [float(features[name]) for name in FEATURE_NAMES]
