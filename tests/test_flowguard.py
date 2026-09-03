"""Regression tests for the live FlowGuard intelligence and HTTP integration."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas.contracts import DashboardResponse, RiskResult
from forecast.predict import forecast_income
from ml.features import build_features
from ml.predict import predict_risk

ROOT = Path(__file__).resolve().parents[1]
PERSONAS = json.loads((ROOT / "data" / "demo" / "personas.json").read_text(encoding="utf-8"))["personas"]


def persona(worker_id: str) -> dict:
    return next(item for item in PERSONAS if item["worker_id"] == worker_id)


def test_feature_builder_ignores_debit_transactions() -> None:
    profile = persona("W001")
    credit_only = build_features(profile, [{"type": "CREDIT", "amount": 800}, {"type": "CREDIT", "amount": 1200}])
    mixed = build_features(profile, [
        {"type": "CREDIT", "amount": 800}, {"type": "DEBIT", "amount": 9_999}, {"type": "CREDIT", "amount": 1200},
    ])
    assert mixed == credit_only


def test_risk_is_explainable_and_transaction_based() -> None:
    result = predict_risk(persona("W001"), [100, 950, 50, 1_200, 0, 900])
    RiskResult(**result)
    assert result["risk_level"] == "HIGH"
    assert result["top_factors"]
    assert all(item["feature"] not in {"age", "education", "marital_status", "dependents"} for item in result["top_factors"])


def test_forecast_has_30_daily_points_and_consistent_totals() -> None:
    result = forecast_income(persona("W002"), [1_100] * 30)
    assert len(result["daily_forecast"]) == 30
    assert result["next_30_days"] == sum(point["expected"] for point in result["daily_forecast"])
    assert result["lower_bound"] <= result["upper_bound"]


def test_dashboard_uses_live_modules_and_validates_contract() -> None:
    client = TestClient(app)
    response = client.get("/worker/W001/dashboard")
    assert response.status_code == 200
    dashboard = response.json()
    DashboardResponse(**dashboard)
    assert dashboard["risk"]["risk_level"] == "HIGH"
    assert dashboard["forecast"]["weather"] == "WATCH"


def test_credit_uses_waterfall_and_affordability_cap() -> None:
    client = TestClient(app)
    result = client.post("/credit/evaluate", json={"worker_id": "W001", "requested_amount": 5_000})
    assert result.status_code == 200
    body = result.json()
    assert body["waterfall"][1]["amount"] == 2_000
    assert body["safe_monthly_repayment"] <= 1_375  # 25% of Ravi's monthly surplus
