"""Validate the trained FlowGuard model against the five demo personas.

Run from the repository root with:
    .venv\\Scripts\\python.exe ml\\test_personas.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from backend.schemas.contracts import FinancialProfile  # noqa: E402
from ml.predict import predict_risk  # noqa: E402


PERSONAS_PATH = REPOSITORY_ROOT / "data" / "demo" / "personas.json"
CORE_HERO_IDS = {"W001", "W002"}


def _as_dict(value: Any) -> dict[str, Any]:
    """Support both the current dict result and future Pydantic result types."""
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return dict(value)


def _score_is_wildly_off(expected: str, score: float) -> bool:
    boundaries = {
        "LOW": (0.0, 0.45),
        "MODERATE": (0.25, 0.80),
        "HIGH": (0.55, 1.0),
    }
    lower, upper = boundaries[expected]
    return score < lower or score > upper


def load_personas() -> list[dict[str, Any]]:
    with PERSONAS_PATH.open(encoding="utf-8") as file:
        payload = json.load(file)
    personas = payload.get("personas")
    if not isinstance(personas, list) or len(personas) != 5:
        raise ValueError("Expected exactly 5 personas in data/demo/personas.json")
    return personas


def main() -> int:
    personas = load_personas()
    passed = 0
    warnings: list[str] = []

    print("FlowGuard persona model validation")
    print(f"Model: {Path(__file__).with_name('model.pkl')}")
    print("=" * 88)

    for persona in personas:
        profile = FinancialProfile.model_validate(persona)
        result = _as_dict(predict_risk(profile))
        expected_level = str(persona["expected_risk_level"]).upper()
        predicted_level = str(result["risk_level"]).upper()
        score = float(result["risk_score"])
        level_match = predicted_level == expected_level

        if level_match:
            passed += 1
        if persona["worker_id"] in CORE_HERO_IDS and _score_is_wildly_off(expected_level, score):
            warnings.append(
                f"{persona['worker_id']} {persona['name']}: score {score:.3f} "
                f"is outside the expected {expected_level} boundary"
            )
        if "shap" not in str(result.get("source", "")).lower():
            warnings.append(f"{persona['worker_id']} did not return SHAP-backed explanations")

        print(f"\n{persona['worker_id']} — {persona['name']} ({persona['occupation']})")
        print(f"Story: {persona['story']}")
        print(f"Expected risk: {expected_level} | Predicted risk: {predicted_level} | Score: {score:.3f} | {'PASS' if level_match else 'CHECK'}")
        print(f"Explanation source: {result.get('source', 'unknown')}")
        print("Top factors:")
        for factor in result.get("top_factors", []):
            print(
                f"  - {factor['feature']}: impact={float(factor['impact']):.3f}, "
                f"{factor['direction']}"
            )

    print("\n" + "=" * 88)
    print(f"Exact risk-level matches: {passed}/{len(personas)}")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("Warnings: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
