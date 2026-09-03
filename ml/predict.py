"""Explainable Random Forest inference with a safe cold-start fallback.

Design invariants
-----------------
1.  ``predict_risk`` **never raises** — every failure mode produces a valid
    ``RiskResult``-compatible dict.
2.  Risk scores are **monotonic** with risk level: LOW < MODERATE < HIGH.
3.  Artifact schema is validated before inference so a stale ``model.pkl``
    (mismatched feature order) is caught immediately and triggers fallback.
4.  SHAP failures are isolated; they fall back to deterministic weighted
    contributions without propagating any exception.
"""
from __future__ import annotations

import json
import math
import warnings
from pathlib import Path
from typing import Any

try:
    import shap as _shap_lib  # noqa: N812
    _SHAP_AVAILABLE = True
except ImportError:
    _shap_lib = None          # type: ignore[assignment]
    _SHAP_AVAILABLE = False

try:
    from .features import FEATURE_NAMES, _DEFAULTS, build_features
except ImportError:
    from features import FEATURE_NAMES, _DEFAULTS, build_features  # type: ignore[no-redef]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODEL_PATH   = Path(__file__).with_name("model.pkl")
SCHEMA_PATH  = MODEL_PATH.with_suffix(MODEL_PATH.suffix + ".schema.json")

# Risk-level thresholds (inclusive lower bound, exclusive upper bound).
# Must be monotonically ascending and consistent with LEVEL_SCORE midpoints.
#   LOW:      [0.00, 0.34)
#   MODERATE: [0.34, 0.67)
#   HIGH:     [0.67, 1.00]
_LOW_THRESHOLD  = 0.34
_HIGH_THRESHOLD = 0.67

# Representative scores used when converting class probabilities to a scalar.
# Values are the *midpoints* of each level's threshold range so the weighted
# sum stays monotonic: more HIGH probability → higher score.
_LEVEL_SCORE: dict[str, float] = {
    "LOW":      0.17,   # midpoint of [0.00, 0.34)
    "MODERATE": 0.505,  # midpoint of [0.34, 0.67)
    "HIGH":     0.835,  # midpoint of [0.67, 1.00]
}
_LEVEL_SCORE_DEFAULT = 0.505  # used for unrecognised class names

# Fallback contribution weights, keyed by FEATURE_NAMES exactly.
# Each weight represents how much a unit-saturated feature contributes to
# the heuristic risk score.  Must match len(FEATURE_NAMES) == 8.
_FALLBACK_WEIGHTS: dict[str, float] = {
    "income_volatility":          0.22,
    "income_trend_score":         0.22,  # used as (1 - trend) contribution
    "expense_burden":             0.18,
    "buffer_coverage":            0.14,  # used as (1 - coverage) contribution
    "debt_service_burden":        0.10,
    "income_gap_ratio":           0.14,
    "payment_frequency_variance": 0.12,
    "essential_spend_ratio":      0.08,
}

# Sanity-check at import time that weights cover every feature name.
_missing_weights = set(FEATURE_NAMES) - set(_FALLBACK_WEIGHTS)
if _missing_weights:
    raise AssertionError(
        f"_FALLBACK_WEIGHTS is missing keys for features: {sorted(_missing_weights)}.  "
        "Align _FALLBACK_WEIGHTS with FEATURE_NAMES after any feature rename."
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _value(profile: Any, name: str, default: Any = None) -> Any:
    if hasattr(profile, name):
        return getattr(profile, name)
    return profile.get(name, default) if isinstance(profile, dict) else default


def _score_to_level(score: float) -> str:
    """Map a risk score in [0, 1] to a ``RiskLevel`` string deterministically."""
    if score >= _HIGH_THRESHOLD:
        return "HIGH"
    if score >= _LOW_THRESHOLD:
        return "MODERATE"
    return "LOW"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        f = float(value)
        return default if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Artifact schema validation
# ---------------------------------------------------------------------------

def _feature_hash(feature_list: list[str]) -> str:
    """SHA-256 of the ordered feature list (truncated).  Must match train.py."""
    import hashlib
    payload = json.dumps(feature_list, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()[:16]


def _load_schema() -> dict[str, Any] | None:
    """Return the on-disk schema dict, or None if the file does not exist."""
    try:
        return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _validate_artifact(artifact: dict[str, Any]) -> list[str]:
    """Return a list of validation errors between *artifact* and the schema file.

    An empty list means the artifact is compatible with the current codebase.
    Checks (in order):
      1. Artifact feature list matches FEATURE_NAMES (order-sensitive).
      2. Schema JSON feature list matches FEATURE_NAMES (if schema exists).
      3. Schema and artifact feature lists agree with each other.
      4. feature_hash values agree (if both are present) — detects stale artifacts.
    """
    errors: list[str] = []

    artifact_features = list(artifact.get("features", []))
    expected_features = list(FEATURE_NAMES)
    expected_hash     = _feature_hash(expected_features)

    if artifact_features != expected_features:
        errors.append(
            f"Artifact feature order mismatch.\n"
            f"  Expected : {expected_features}\n"
            f"  Artifact : {artifact_features}"
        )

    schema = _load_schema()
    if schema is not None:
        schema_features = list(schema.get("features", []))

        if schema_features != expected_features:
            errors.append(
                f"Schema file feature order mismatch.\n"
                f"  Expected : {expected_features}\n"
                f"  Schema   : {schema_features}"
            )

        if schema_features != artifact_features:
            errors.append(
                f"Schema and artifact feature lists disagree — artifact may be stale.\n"
                f"  Artifact : {artifact_features}\n"
                f"  Schema   : {schema_features}"
            )

        # feature_hash cross-check (advisory — old artifacts lack the field).
        artifact_hash = artifact.get("feature_hash")
        schema_hash   = schema.get("feature_hash")
        if artifact_hash and schema_hash and artifact_hash != schema_hash:
            errors.append(
                f"feature_hash mismatch: artifact={artifact_hash}, schema={schema_hash}. "
                "Retrain the model."
            )
        # If the hash field exists in either, verify it matches the live code.
        live_hash = expected_hash
        if artifact_hash and artifact_hash != live_hash:
            errors.append(
                f"Artifact feature_hash ({artifact_hash}) does not match current "
                f"FEATURE_NAMES hash ({live_hash}). Retrain the model."
            )

    return errors



# ---------------------------------------------------------------------------
# Fallback path (no model / cold start)
# ---------------------------------------------------------------------------

def _fallback_contributions(features: dict[str, float]) -> dict[str, float]:
    """Compute deterministic per-feature risk contributions.

    All contributions are in [0, weight_max] and represent how much each
    feature *increases* risk.  Negative-polarity features (income_trend_score,
    buffer_coverage) are inverted so that "bad" always means "high contribution".
    """
    return {
        # Positive-polarity: higher raw value → more risk
        "income_volatility":
            _FALLBACK_WEIGHTS["income_volatility"]
            * min(1.0, _safe_float(features.get("income_volatility", 0))),

        # Negative-polarity: declining trend (negative score) → more risk
        "income_trend_score":
            _FALLBACK_WEIGHTS["income_trend_score"]
            * max(0.0, -_safe_float(features.get("income_trend_score", 0))),

        "expense_burden":
            _FALLBACK_WEIGHTS["expense_burden"]
            * min(1.0, _safe_float(features.get("expense_burden", 0))),

        # Negative-polarity: low coverage → more risk
        "buffer_coverage":
            _FALLBACK_WEIGHTS["buffer_coverage"]
            * max(0.0, 1.0 - min(1.0, _safe_float(features.get("buffer_coverage", 0)))),

        "debt_service_burden":
            _FALLBACK_WEIGHTS["debt_service_burden"]
            * min(1.0, _safe_float(features.get("debt_service_burden", 0))),

        "income_gap_ratio":
            _FALLBACK_WEIGHTS["income_gap_ratio"]
            * min(1.0, _safe_float(features.get("income_gap_ratio", 0))),

        "payment_frequency_variance":
            _FALLBACK_WEIGHTS["payment_frequency_variance"]
            * min(1.0, _safe_float(features.get("payment_frequency_variance", 0))),

        "essential_spend_ratio":
            _FALLBACK_WEIGHTS["essential_spend_ratio"]
            * min(1.0, _safe_float(features.get("essential_spend_ratio", 0))),
    }


def _fallback(profile: Any, history: list[Any] | None) -> dict[str, Any]:
    """Deterministic heuristic fallback when no trained model is available."""
    features = build_features(profile, history)
    contributions = _fallback_contributions(features)

    # Heuristic base of 0.08 reflects the observation that gig workers are
    # structurally at mild risk even with zero adverse features.
    raw_score = 0.08 + sum(contributions.values())
    score = round(max(0.0, min(1.0, raw_score)), 3)

    factors = [
        {"feature": name, "impact": round(val, 3), "direction": "increases_risk"}
        for name, val in sorted(contributions.items(), key=lambda kv: kv[1], reverse=True)
        if val > 0.01
    ][:5]

    # Confidence grows with more history (plateaus at 0.82 with 30+ records).
    confidence = round(min(0.82, 0.52 + min(0.30, len(history or []) / 40)), 3)

    return {
        "worker_id":   str(_value(profile, "worker_id", "unknown")),
        "risk_score":  score,
        "risk_level":  _score_to_level(score),
        "confidence":  confidence,
        "top_factors": factors,
        "features":    features,
        "source":      "fallback",
    }


# ---------------------------------------------------------------------------
# SHAP explainability (isolated from inference)
# ---------------------------------------------------------------------------

def _shap_factors(
    model: Any,
    vector: list[float],
    feature_names: list[str],
    class_index: int,
) -> list[dict[str, Any]]:
    """Compute SHAP-based top factors.

    Raises ``RuntimeError`` on any SHAP failure so the caller can catch it
    and fall back to deterministic contributions without crashing.
    """
    if not _SHAP_AVAILABLE or _shap_lib is None:
        raise RuntimeError("SHAP library is not installed")

    try:
        import numpy as np

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # suppress scikit-learn InconsistencyWarning
            explainer = _shap_lib.TreeExplainer(model)
            shap_values = explainer.shap_values(np.asarray([vector], dtype=float))

        # shap_values can be:
        #   list[ndarray]  — one array per class (multi-class RF)
        #   ndarray shape (1, n_features, n_classes)  — new shap API
        #   ndarray shape (1, n_features)              — binary case
        if isinstance(shap_values, list):
            # Old API: list[ndarray of shape (n_samples, n_features)]
            if class_index >= len(shap_values):
                raise RuntimeError(
                    f"class_index={class_index} out of range for shap_values list "
                    f"of length {len(shap_values)}"
                )
            values = shap_values[class_index][0]
        elif hasattr(shap_values, "ndim"):
            ndim = int(shap_values.ndim)
            if ndim == 3:
                # New API: (n_samples, n_features, n_classes)
                values = shap_values[0, :, class_index]
            elif ndim == 2:
                values = shap_values[0]
            else:
                raise RuntimeError(f"Unexpected SHAP values ndim={ndim}")
        else:
            raise RuntimeError(f"Unexpected SHAP values type: {type(shap_values)}")

        if len(values) != len(feature_names):
            raise RuntimeError(
                f"SHAP values length {len(values)} != feature_names length {len(feature_names)}"
            )

        ranked = sorted(
            zip(feature_names, (float(v) for v in values)),
            key=lambda kv: abs(kv[1]),
            reverse=True,
        )
        return [
            {
                "feature":   name,
                "impact":    round(abs(val), 3),
                "direction": "increases_risk" if val > 0 else "decreases_risk",
            }
            for name, val in ranked[:5]
        ]

    except RuntimeError:
        raise  # re-raise our own structured errors as-is
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"SHAP computation failed: {exc}") from exc


def _deterministic_factors(
    features: dict[str, float],
    feature_names: list[str],
) -> list[dict[str, Any]]:
    """Deterministic SHAP fallback using pre-defined contribution weights.

    Used when SHAP is unavailable or fails at runtime.  Mirrors the logic in
    ``_fallback_contributions`` but scoped to the model's feature list.
    """
    contributions = _fallback_contributions(features)
    # Only surface features that appear in the model's feature list.
    ranked = sorted(
        [(name, contributions.get(name, 0.0)) for name in feature_names],
        key=lambda kv: kv[1],
        reverse=True,
    )
    return [
        {"feature": name, "impact": round(val, 3), "direction": "increases_risk"}
        for name, val in ranked[:5]
        if val > 0.01
    ]


# ---------------------------------------------------------------------------
# Public inference entry point
# ---------------------------------------------------------------------------

def predict_risk(profile: Any, history: list[Any] | None = None) -> dict[str, Any]:
    """Return a ``RiskResult``-compatible dict for *profile*.

    Flow
    ----
    1. Always compute a deterministic fallback first (never fails).
    2. If ``model.pkl`` exists, attempt full RF inference:
       a. Load and validate the artifact against ``FEATURE_NAMES`` and schema.
       b. Build feature vector; run ``predict_proba``.
       c. Derive monotonic risk score from class probabilities.
       d. Attempt SHAP explanation; fall back to deterministic factors on failure.
    3. Any exception in steps 2a-2d causes graceful degradation to the fallback.

    The returned dict always contains:
      ``worker_id``, ``risk_score`` ∈ [0,1], ``risk_level`` ∈ {LOW,MODERATE,HIGH},
      ``confidence`` ∈ [0,1], ``top_factors``, ``features``, ``source``.
    """
    fallback_result = _fallback(profile, history)

    if not MODEL_PATH.exists():
        return fallback_result

    try:
        import joblib  # noqa: PLC0415
        import pandas as pd  # noqa: PLC0415

        # ── Load & validate artifact ──────────────────────────────────────
        artifact: dict[str, Any] = joblib.load(MODEL_PATH)
        validation_errors = _validate_artifact(artifact)
        if validation_errors:
            warnings.warn(
                "ML artifact validation failed; using fallback.\n"
                + "\n".join(validation_errors),
                stacklevel=2,
            )
            return fallback_result

        feature_names: list[str] = list(artifact["features"])
        model   = artifact["model"]
        encoder = artifact["encoder"]

        # ── Feature vector ────────────────────────────────────────────────
        features = build_features(profile, history)
        # KeyError here is now impossible because build_features guarantees
        # all FEATURE_NAMES keys and validation confirmed artifact matches.
        vector = [features[name] for name in feature_names]

        X_inf = pd.DataFrame([vector], columns=feature_names)

        # ── Probability inference ─────────────────────────────────────────
        probabilities: list[float] = [float(p) for p in model.predict_proba(X_inf)[0]]
        class_index = int(model.predict(X_inf)[0])
        label = str(encoder.inverse_transform([class_index])[0]).upper()

        # Monotonic probability-weighted score.
        # Using _LEVEL_SCORE midpoints ensures that a pure-HIGH prediction
        # always scores above a pure-MODERATE prediction, etc.
        score = _safe_float(
            sum(
                prob * _LEVEL_SCORE.get(str(cls).upper(), _LEVEL_SCORE_DEFAULT)
                for prob, cls in zip(probabilities, encoder.classes_)
            ),
            default=fallback_result["risk_score"],
        )
        score = round(max(0.0, min(1.0, score)), 3)

        # Ensure label is consistent with score.  If the model's MAP label
        # disagrees with the threshold mapping, trust the thresholds.
        threshold_label = _score_to_level(score)
        if label != threshold_label:
            label = threshold_label

        # ── SHAP explanation (isolated) ───────────────────────────────────
        try:
            top_factors = _shap_factors(model, vector, feature_names, class_index)
            source = "random_forest_shap"
        except RuntimeError as shap_err:
            warnings.warn(
                f"SHAP explanation failed ({shap_err}); using deterministic factors.",
                stacklevel=2,
            )
            top_factors = _deterministic_factors(features, feature_names)
            source = "random_forest_deterministic"

        return {
            **fallback_result,
            "risk_score":  score,
            "risk_level":  label,
            "confidence":  round(max(probabilities), 3),
            "top_factors": top_factors,
            "source":      source,
        }

    except Exception as exc:  # noqa: BLE001
        warnings.warn(
            f"ML inference failed ({type(exc).__name__}: {exc}); using fallback.",
            stacklevel=2,
        )
        return fallback_result


# ---------------------------------------------------------------------------
# CLI smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    _demo_profile = {
        "worker_id":              "demo",
        "monthly_income_avg":     24000,
        "monthly_income_std":     3500,
        "total_monthly_expenses": 18500,
        "fixed_expenses":         11000,
        "emergency_buffer":       2000,
        "monthly_emi":            2000,
    }
    _demo_history = [22000, 18000, 16000, 24500, 21000]
    result = predict_risk(_demo_profile, _demo_history)
    print(json.dumps(result, indent=2))
    sys.exit(0)
