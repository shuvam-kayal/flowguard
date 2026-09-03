"""End-to-end checks owned by the income-forecast module."""
from __future__ import annotations

from datetime import date, timedelta

from backend.schemas.contracts import FinancialProfile, ForecastResult
from forecast.evaluate import evaluate_model
from forecast.predict import forecast_income
from forecast.train import train_forecast_model


def _profile() -> FinancialProfile:
    return FinancialProfile(
        worker_id="TEST-001", name="Test Worker", occupation="Delivery partner", current_balance=1_000,
        monthly_income_avg=18_000, monthly_income_std=2_500, income_trend="STABLE",
        total_monthly_expenses=12_000, fixed_expenses=7_000, variable_expenses=5_000,
        savings_balance=2_000, emergency_buffer=1_000, total_debt=0, monthly_emi=0,
        dependents=0, avg_work_hours_per_week=48, active_platforms=["Test platform"],
        expense_to_income_ratio=0.67,
    )


def _history() -> list[dict]:
    start = date(2026, 1, 1)
    return [
        {"worker_id": "TEST-001", "date": (start + timedelta(days=index)).isoformat(),
         "income": 500 + (index % 7) * 35 + (index // 21) * 10}
        for index in range(70)
    ]


def test_forecast_pipeline_trains_evaluates_and_returns_contract(monkeypatch, tmp_path) -> None:
    """This verifies the complete Person 2 flow without relying on team demo data."""
    history = _history()
    model_path = tmp_path / "income_model.joblib"
    training = train_forecast_model(history, model_path)
    metrics = evaluate_model(history, model_path)
    assert training["training_examples"] > 0
    assert metrics["observations"] > 0
    assert metrics["mae"] >= 0
    monkeypatch.setattr("forecast.predict.MODEL_PATH", model_path)
    result = forecast_income(_profile(), history)
    ForecastResult.model_validate(result)
    assert len(result.daily_forecast) == 30
    assert result.next_7_days == sum(point.expected for point in result.daily_forecast[:7])
    assert result.next_30_days == sum(point.expected for point in result.daily_forecast)
    assert 0 <= result.shock_probability <= 1
    assert result.weather in {"STABLE", "WATCH", "SHOCK"}
    assert all(point.lower <= point.expected <= point.upper for point in result.daily_forecast)
