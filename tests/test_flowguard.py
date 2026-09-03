"""Regression tests for the live FlowGuard intelligence and HTTP integration."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas.contracts import DashboardResponse, FinancialProfile, ForecastResult, RiskResult
from forecast.predict import forecast_income
from ml.features import build_features
from ml.predict import predict_risk

ROOT = Path(__file__).resolve().parents[1]
PERSONAS = json.loads((ROOT / "data" / "demo" / "personas.json").read_text(encoding="utf-8"))["personas"]


def persona(worker_id: str) -> dict:
    return next(item for item in PERSONAS if item["worker_id"] == worker_id)


def profile(worker_id: str) -> FinancialProfile:
    return FinancialProfile.model_validate(persona(worker_id))


def test_feature_builder_ignores_debit_transactions() -> None:
    profile = persona("W001")
    credit_only = build_features(profile, [{"type": "CREDIT", "amount": 800}, {"type": "CREDIT", "amount": 1200}])
    mixed = build_features(profile, [
        {"type": "CREDIT", "amount": 800}, {"type": "DEBIT", "amount": 9_999}, {"type": "CREDIT", "amount": 1200},
    ])
    assert mixed == credit_only


def test_risk_is_explainable_and_transaction_based() -> None:
    result = predict_risk(profile("W001"), [100, 950, 50, 1_200, 0, 900])
    RiskResult.model_validate(result)
    assert result.risk_level == "HIGH"
    assert result.top_factors
    assert all(item.feature not in {"age", "education", "marital_status", "dependents"} for item in result.top_factors)


def test_forecast_has_30_daily_points_and_consistent_totals() -> None:
    result = forecast_income(profile("W002"), [1_100] * 30)
    ForecastResult.model_validate(result)
    assert len(result.daily_forecast) == 30
    assert result.next_30_days == sum(point.expected for point in result.daily_forecast)
    assert result.lower_bound <= result.upper_bound


def test_cold_start_user_with_empty_history() -> None:
    result = predict_risk(profile("W002"), [])
    forecast = forecast_income(profile("W002"), [])
    assert 0 <= result.risk_score <= 1
    assert len(forecast.daily_forecast) == 30


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


def test_credit_full_credit_path() -> None:
    client = TestClient(app)
    result = client.post("/credit/evaluate", json={"worker_id": "W002", "requested_amount": 100})
    assert result.status_code == 200
    assert result.json()["decision"] == "NO_CREDIT_NEEDED"  # healthy user's buffer covers it

    # The branch is exercised directly with a zero-buffer worker and no future income.
    from resilience.credit_guard import evaluate_credit
    from backend.schemas.contracts import ResilienceResult
    state = ResilienceResult(worker_id="W002", safe_to_spend_daily=0, resilience_score=50,
        resilience_days=0, buffer_target=0, buffer_current=0, recommended_save=0, mode="NORMAL",
        wallet_allocation={"daily": 0, "bills": 0, "buffer": 0, "growth": 0},
        score_breakdown={"income_stability": 10, "emergency_buffer": 10, "expense_coverage": 10, "debt_burden": 10, "savings_consistency": 10})
    forecast = ForecastResult(worker_id="W002", next_7_days=0, next_30_days=0, lower_bound=0, upper_bound=0,
        trend="STABLE", shock_probability=0, weather="STABLE", daily_forecast=[])
    assert evaluate_credit(profile("W002"), state, forecast, 100).decision == "FULL_CREDIT"


def test_credit_declined_when_repayment_is_unaffordable() -> None:
    from resilience.credit_guard import evaluate_credit
    from backend.schemas.contracts import ResilienceResult
    state = ResilienceResult(worker_id="W004", safe_to_spend_daily=0, resilience_score=10,
        resilience_days=0, buffer_target=9000, buffer_current=0, recommended_save=0, mode="SHOCK",
        wallet_allocation={"daily": 0, "bills": 0, "buffer": 0, "growth": 0},
        score_breakdown={"income_stability": 2, "emergency_buffer": 0, "expense_coverage": 2, "debt_burden": 3, "savings_consistency": 3})
    forecast = ForecastResult(worker_id="W004", next_7_days=0, next_30_days=0, lower_bound=0, upper_bound=0,
        trend="DECLINING", shock_probability=1, weather="SHOCK", daily_forecast=[])
    assert evaluate_credit(profile("W004"), state, forecast, 5_000).decision == "CREDIT_DECLINED"


def test_simulation_endpoints_return_validated_dashboards() -> None:
    client = TestClient(app)
    for path in ("/simulate/shock", "/simulate/recovery"):
        response = client.post(path, json={"worker_id": "W001"})
        assert response.status_code == 200
        DashboardResponse.model_validate(response.json())
