"""Transaction-derived, explainable financial vulnerability inference."""
import json
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from constants import (RISK_BASE_SCORE, RISK_CONFIDENCE_BASE, RISK_CONFIDENCE_HISTORY_SCALE,
                       RISK_CONFIDENCE_MAX, RISK_CONFIDENCE_MIN, RISK_HIGH_THRESHOLD,
                       RISK_LOW_THRESHOLD, RISK_WEIGHTS)
from backend.schemas.contracts import FinancialProfile, RiskResult

try:
    from .features import build_features
except ImportError:  # supports `python ml/predict.py` from repository root
    from features import build_features

DEMO = os.path.join(os.path.dirname(__file__), "..", "data", "demo", "sample_risk.json")


MODEL_PATH = Path(__file__).with_name("model.pkl")


def _level(score: float) -> str:
    return "LOW" if score < RISK_LOW_THRESHOLD else "MODERATE" if score <= RISK_HIGH_THRESHOLD else "HIGH"


def _fallback(profile: FinancialProfile, history: list | None = None) -> RiskResult:
    f = build_features(profile.model_dump(), history)
    # Positive contributions are distress signals; coverage is protective.
    contributions = {
        "income_volatility": RISK_WEIGHTS["income_volatility"] * min(1.0, f["income_volatility"]),
        "income_trend": RISK_WEIGHTS["income_trend"] * max(0.0, -f["income_trend_score"]),
        "expense_burden": RISK_WEIGHTS["expense_burden"] * min(1.0, f["expense_burden"]),
        "low_buffer_coverage": RISK_WEIGHTS["low_buffer_coverage"] * min(1.0, f["buffer_coverage"]),
        "debt_service_burden": RISK_WEIGHTS["debt_service_burden"] * min(1.0, f["debt_service_burden"]),
        "income_gap": RISK_WEIGHTS["income_gap"] * min(1.0, f["income_gap_ratio"]),
    }
    # 0.18 is a neutral base; protective coverage lowers the result.
    score = max(0.0, min(1.0, RISK_BASE_SCORE + sum(contributions.values())))
    ranked = sorted(contributions.items(), key=lambda item: abs(item[1]), reverse=True)[:5]
    factors = [{"feature": name, "impact": round(abs(value), 3),
                "direction": "increases_risk" if value >= 0 else "decreases_risk"}
               for name, value in ranked if abs(value) > 0.01]
    confidence = max(RISK_CONFIDENCE_MIN, min(RISK_CONFIDENCE_MAX,
        RISK_CONFIDENCE_BASE + min(0.12, len(history or []) / RISK_CONFIDENCE_HISTORY_SCALE)))
    return RiskResult(worker_id=profile.worker_id, risk_score=round(score, 3),
                      risk_level=_level(score), confidence=round(confidence, 2), top_factors=factors)


def predict_risk(profile: FinancialProfile, history: list | None = None) -> RiskResult:
    """
    Input:  FinancialProfile dict (see docs/api-contract.md #1)
    Output: RiskResult dict (see docs/api-contract.md #2)

    A trained ``model.pkl`` is used when available. The fallback remains
    explainable and is suitable for demo data and cold-start workers.
    """
    profile = FinancialProfile.model_validate(profile)
    if MODEL_PATH.exists():
        try:
            import joblib
            artifact = joblib.load(MODEL_PATH)
            features = build_features(profile.model_dump(), history)
            vector = [features[name] for name in artifact["features"]]
            model = artifact["model"]
            label = artifact["encoder"].inverse_transform(model.predict([vector]))[0]
            probabilities = model.predict_proba([vector])[0]
            class_scores = {"LOW": 0.2, "MODERATE": 0.5, "HIGH": 0.85}
            score = float(sum(p * class_scores.get(str(cls).upper(), 0.5)
                              for p, cls in zip(probabilities, artifact["encoder"].classes_)))
            return RiskResult(worker_id=profile.worker_id, risk_level=str(label).upper(),
                              risk_score=round(score, 3), confidence=round(float(max(probabilities)), 3),
                              top_factors=_fallback(profile, history).top_factors)
        except (OSError, KeyError, ValueError, ImportError):
            pass
    return _fallback(profile, history)


if __name__ == "__main__":
    from backend.schemas.contracts import FinancialProfile
    demo_profile = {"worker_id": "W001", "name": "Demo", "occupation": "Demo", "current_balance": 0,
                    "monthly_income_avg": 24000, "monthly_income_std": 6800, "income_trend": "DECLINING",
                    "total_monthly_expenses": 18500, "fixed_expenses": 11000, "variable_expenses": 7500,
                    "savings_balance": 5400, "emergency_buffer": 2000, "total_debt": 8000, "monthly_emi": 2000,
                    "dependents": 0, "avg_work_hours_per_week": 0, "active_platforms": [], "expense_to_income_ratio": .77}
    print(json.dumps(predict_risk(FinancialProfile(**demo_profile)).model_dump(), indent=2, ensure_ascii=False))
