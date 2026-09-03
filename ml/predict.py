"""Transaction-derived, explainable financial vulnerability inference."""
import json
import os
from pathlib import Path

try:
    from .features import build_features
except ImportError:  # supports `python ml/predict.py` from repository root
    from features import build_features

DEMO = os.path.join(os.path.dirname(__file__), "..", "data", "demo", "sample_risk.json")


MODEL_PATH = Path(__file__).with_name("model.pkl")


def _level(score: float) -> str:
    return "LOW" if score < 0.34 else "MODERATE" if score <= 0.66 else "HIGH"


def _fallback(profile: dict, history: list | None = None) -> dict:
    f = build_features(profile, history)
    # Positive contributions are distress signals; coverage is protective.
    contributions = {
        "income_volatility": 0.34 * min(1.0, f["income_volatility"]),
        "income_trend": 0.20 * max(0.0, -f["income_trend_score"]),
        "expense_burden": 0.40 * min(1.0, f["expense_burden"]),
        "low_buffer_coverage": -0.22 * min(1.0, f["buffer_coverage"]),
        "debt_service_burden": 0.16 * min(1.0, f["debt_service_burden"]),
        "income_gap": 0.22 * min(1.0, f["income_gap_ratio"]),
    }
    # 0.18 is a neutral base; protective coverage lowers the result.
    score = max(0.0, min(1.0, 0.215 + sum(contributions.values())))
    ranked = sorted(contributions.items(), key=lambda item: abs(item[1]), reverse=True)[:5]
    factors = [{"feature": name, "impact": round(abs(value), 3),
                "direction": "increases_risk" if value >= 0 else "decreases_risk"}
               for name, value in ranked if abs(value) > 0.01]
    confidence = max(0.55, min(0.95, 0.82 + min(0.12, len(history or []) / 100)))
    return {"worker_id": profile.get("worker_id", "W001"), "risk_score": round(score, 3),
            "risk_level": _level(score), "confidence": round(confidence, 2), "top_factors": factors}


def predict_risk(profile: dict, history: list | None = None) -> dict:
    """
    Input:  FinancialProfile dict (see docs/api-contract.md #1)
    Output: RiskResult dict (see docs/api-contract.md #2)

    A trained ``model.pkl`` is used when available. The fallback remains
    explainable and is suitable for demo data and cold-start workers.
    """
    if MODEL_PATH.exists():
        try:
            import joblib
            artifact = joblib.load(MODEL_PATH)
            features = build_features(profile, history)
            vector = [features[name] for name in artifact["features"]]
            model = artifact["model"]
            label = artifact["encoder"].inverse_transform(model.predict([vector]))[0]
            probabilities = model.predict_proba([vector])[0]
            class_scores = {"LOW": 0.2, "MODERATE": 0.5, "HIGH": 0.85}
            score = float(sum(p * class_scores.get(str(cls).upper(), 0.5)
                              for p, cls in zip(probabilities, artifact["encoder"].classes_)))
            return {**_fallback(profile, history), "risk_level": str(label).upper(), "risk_score": round(score, 3),
                    "confidence": round(float(max(probabilities)), 3)}
        except (OSError, KeyError, ValueError, ImportError):
            pass
    return _fallback(profile, history)


if __name__ == "__main__":
    demo_profile = {"worker_id": "W001"}
    print(json.dumps(predict_risk(demo_profile), indent=2, ensure_ascii=False))
