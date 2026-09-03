"""
Person 1 — Financial Risk model.
STUB: returns mock RiskResult from sample data so downstream can build today.
Replace `predict_risk` internals with your trained model (model.pkl) later.
The OUTPUT SHAPE must not change — it must match RiskResult in the contract.
"""
import json
import os

DEMO = os.path.join(os.path.dirname(__file__), "..", "data", "demo", "sample_risk.json")


def predict_risk(profile: dict) -> dict:
    """
    Input:  FinancialProfile dict (see docs/api-contract.md #1)
    Output: RiskResult dict (see docs/api-contract.md #2)

    TODO(Person 1): load model.pkl, build features from `profile`, predict,
    and produce top_factors via SHAP or deterministic contributions.
    """
    wid = profile.get("worker_id", "W001")
    with open(DEMO) as f:
        mocks = json.load(f)
    return mocks.get(wid, mocks["W001"])


if __name__ == "__main__":
    demo_profile = {"worker_id": "W001"}
    print(json.dumps(predict_risk(demo_profile), indent=2, ensure_ascii=False))
