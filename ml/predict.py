"""Explainable Random Forest inference with a safe cold-start fallback."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import shap
except ImportError:  # SHAP is optional when no trained model is deployed.
    shap = None

try:
    from .features import FEATURE_NAMES, build_features
except ImportError:
    from features import FEATURE_NAMES, build_features

MODEL_PATH = Path(__file__).with_name("model.pkl")
LEVEL_SCORE = {"LOW": 0.2, "MODERATE": 0.5, "HIGH": 0.85}
WEIGHTS = {
    "income_volatility": 0.24, "income_trend": 0.24, "expense_burden": 0.20,
    "low_buffer_coverage": 0.16, "debt_service_burden": 0.10, "income_gap": 0.16,
    "payment_frequency_variance": 0.15, "essential_spend_ratio": 0.15,
}


def _value(profile: Any, name: str, default: Any = None) -> Any:
    if hasattr(profile, name):
        return getattr(profile, name)
    return profile.get(name, default) if isinstance(profile, dict) else default


def _fallback(profile: Any, history: list[Any] | None) -> dict[str, Any]:
    features = build_features(profile, history)
    contributions = {
        "income_volatility": WEIGHTS["income_volatility"] * min(1, features["income_volatility"]),
        "income_trend": WEIGHTS["income_trend"] * max(0, -features["income_trend_score"]),
        "expense_burden": WEIGHTS["expense_burden"] * min(1, features["expense_burden"]),
        "low_buffer_coverage": WEIGHTS["low_buffer_coverage"] * max(0, 1 - min(1, features["buffer_coverage"])),
        "debt_service_burden": WEIGHTS["debt_service_burden"] * min(1, features["debt_service_burden"]),
        "income_gap": WEIGHTS["income_gap"] * min(1, features["income_gap_ratio"]),
        "payment_frequency_variance": WEIGHTS["payment_frequency_variance"] * min(1, features["payment_frequency_variance"]),
        "essential_spend_ratio": WEIGHTS["essential_spend_ratio"] * min(1, features["essential_spend_ratio"]),
    }
    score = max(0, min(1, 0.08 + sum(contributions.values())))
    factors = [{"feature": name, "impact": round(value, 3), "direction": "increases_risk"}
               for name, value in sorted(contributions.items(), key=lambda item: item[1], reverse=True)[:5] if value > 0.01]
    return {
        "worker_id": str(_value(profile, "worker_id", "unknown")), "risk_score": round(score, 3),
        "risk_level": "LOW" if score < 0.34 else "MODERATE" if score < 0.67 else "HIGH",
        "confidence": round(min(0.95, 0.52 + min(0.30, len(history or []) / 40)), 3),
        "top_factors": factors, "features": features, "source": "fallback",
    }


def _shap_factors(model: Any, vector: list[float], feature_names: list[str], class_index: int) -> list[dict[str, Any]]:
    if shap is None:
        raise ImportError("SHAP is required for model explanations")
    import numpy as np

    values = shap.TreeExplainer(model).shap_values(np.asarray([vector], dtype=float))
    if isinstance(values, list):
        values = values[class_index][0]
    else:
        values = values[0, :, class_index] if getattr(values, "ndim", 0) == 3 else values[0]
    ranked = sorted(zip(feature_names, values), key=lambda item: abs(float(item[1])), reverse=True)
    return [{"feature": name, "impact": round(abs(float(value)), 3),
             "direction": "increases_risk" if float(value) > 0 else "decreases_risk"}
            for name, value in ranked[:5]]


def predict_risk(profile: Any, history: list[Any] | None = None) -> dict[str, Any]:
    """Return risk score, SHAP factors, features, and model provenance."""
    fallback = _fallback(profile, history)
    if not MODEL_PATH.exists():
        return fallback
    try:
        import joblib
        import pandas as pd

        artifact = joblib.load(MODEL_PATH)
        features = build_features(profile, history)
        feature_names = list(artifact.get("features", FEATURE_NAMES))
        vector = [features[name] for name in feature_names]
        model, encoder = artifact["model"], artifact["encoder"]
        X_inf = pd.DataFrame([vector], columns=feature_names)
        probabilities = model.predict_proba(X_inf)[0]
        class_index = int(model.predict(X_inf)[0])
        label = str(encoder.inverse_transform([class_index])[0]).upper()
        score = sum(float(probability) * LEVEL_SCORE.get(str(label_name).upper(), 0.5)
                    for probability, label_name in zip(probabilities, encoder.classes_))
        top_factors = _shap_factors(model, vector, feature_names, class_index)
        return {**fallback, "risk_score": round(score, 3), "risk_level": label,
                "confidence": round(float(max(probabilities)), 3),
                "top_factors": top_factors, "source": "random_forest_shap"}
    except (OSError, KeyError, ValueError, ImportError, AttributeError, TypeError, IndexError):
        return fallback


if __name__ == "__main__":
    print(json.dumps(predict_risk({"worker_id": "demo", "monthly_income_avg": 24000,
        "total_monthly_expenses": 18500, "fixed_expenses": 11000,
        "emergency_buffer": 2000, "monthly_emi": 2000}, [22000, 18000, 16000]), indent=2))
