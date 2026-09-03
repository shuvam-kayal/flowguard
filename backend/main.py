"""
Person 4 — FastAPI backend / orchestration.
Wires the four modules together behind ONE dashboard endpoint.

Day 1: serves straight from the demo mocks so the frontend is unblocked.
As real modules land, swap the mock loads for imports:
    from ml.predict import predict_risk
    from forecast.predict import forecast_income
    from resilience.engine import evaluate, recommend

Run:  uvicorn backend.main:app --reload --port 8000
"""
import json
import os
from copy import deepcopy
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.schemas.contracts import (
    DashboardResponse, FinancialProfile, ForecastResult, ObligationSummary,
    ResilienceResult, RiskResult,
)
from constants import (
    RECOVERY_MIN_RISK_SCORE, RECOVERY_RISK_DECREMENT,
    RECOVERY_SCORE_INCREMENT, RECOVERY_SHOCK_PROBABILITY_DECREMENT,
    RECOVERY_MIN_SHOCK_PROBABILITY, RECOVERY_SPEND_FACTOR,
    SHOCK_DEFAULT_FACTOR, SHOCK_PROBABILITY_INCREMENT,
    SHOCK_RISK_INCREMENT, SHOCK_MAX_PROBABILITY, SHOCK_MAX_RISK_SCORE,
    SHOCK_SIMULATION_SPEND_FACTOR,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(ROOT, "data", "demo")

app = FastAPI(title="FlowGuard API", version="0.1.0")
_origins = [origin.strip() for origin in os.getenv("FLOWGUARD_ALLOWED_ORIGINS", "*").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_methods=["*"], allow_headers=["*"],
)


def _load(name):
    with open(os.path.join(DEMO, name), encoding="utf-8") as f:
        return json.load(f)


# ---- toggle: use mocks or real modules -------------------------------------
USE_REAL_MODULES = True


def get_dashboard(worker_id: str) -> DashboardResponse:
    dashboards = _load("sample_dashboards.json")
    if worker_id not in dashboards:
        raise HTTPException(404, f"Unknown worker {worker_id}")
    if not USE_REAL_MODULES:
        return DashboardResponse.model_validate(dashboards[worker_id])

    # ---- real orchestration path (enable at checkpoint 2) ----
    import sys
    sys.path.insert(0, ROOT)
    from ml.predict import predict_risk
    from forecast.predict import forecast_income
    from resilience.engine import evaluate, recommend

    personas = {p["worker_id"]: p for p in _load("personas.json")["personas"]}
    obligations = _load("sample_obligations.json")
    profile = FinancialProfile.model_validate(personas[worker_id])
    risk = predict_risk(profile)
    forecast = forecast_income(profile)
    obl = ObligationSummary.model_validate(obligations[worker_id])
    resilience = evaluate(profile, risk, forecast, obl)
    recs = recommend(profile, resilience, forecast)
    return DashboardResponse(
        worker={k: getattr(profile, k) for k in ("worker_id", "name", "occupation", "current_balance")},
        risk=risk, forecast=forecast, resilience=resilience,
        obligations=obl, recommendations=recs,
    )


@app.get("/")
def health():
    return {"status": "ok", "service": "flowguard", "real_modules": USE_REAL_MODULES}


@app.get("/workers")
def list_workers():
    dashboards = _load("sample_dashboards.json")
    return [d["worker"] for d in dashboards.values()]


@app.get("/worker/{worker_id}/dashboard")
def worker_dashboard(worker_id: str) -> DashboardResponse:
    return get_dashboard(worker_id)


@app.post("/ml/risk")
def risk_endpoint(payload: dict):
    from ml.predict import predict_risk
    return predict_risk(FinancialProfile.model_validate(payload.get("profile", payload)), payload.get("history"))


@app.post("/forecast/income")
def forecast_endpoint(payload: dict):
    from forecast.predict import forecast_income
    return forecast_income(FinancialProfile.model_validate(payload.get("profile", payload)), payload.get("history"))


@app.post("/resilience/evaluate")
def resilience_endpoint(payload: dict):
    from resilience.engine import evaluate, recommend
    profile = FinancialProfile.model_validate(payload["profile"])
    risk = RiskResult.model_validate(payload["risk"])
    forecast = ForecastResult.model_validate(payload["forecast"])
    obligations = ObligationSummary.model_validate(payload["obligations"])
    result = evaluate(profile, risk, forecast, obligations)
    return {**result.model_dump(), "recommendations": [item.model_dump() for item in recommend(profile, result, forecast)]}


@app.post("/credit/evaluate")
def credit_evaluate(payload: dict):
    wid = payload.get("worker_id", "W001")
    dashboard = get_dashboard(wid)
    from resilience.credit_guard import evaluate_credit
    personas = {p["worker_id"]: p for p in _load("personas.json")["personas"]}
    if wid not in personas:
        raise HTTPException(404, f"Unknown worker {wid}")
    requested = max(0, int(payload.get("requested_amount", 0)))
    return evaluate_credit(FinancialProfile.model_validate(personas[wid]),
                           ResilienceResult.model_validate(dashboard.resilience),
                           ForecastResult.model_validate(dashboard.forecast), requested)


def _apply_shock(dash: DashboardResponse, factor: float) -> DashboardResponse:
    """Simulate an income shock: cut forecast, spike risk, tighten resilience."""
    d = deepcopy(DashboardResponse.model_validate(dash).model_dump())
    d["forecast"]["next_30_days"] = int(d["forecast"]["next_30_days"] * factor)
    d["forecast"]["next_7_days"] = int(d["forecast"]["next_7_days"] * factor)
    d["forecast"]["weather"] = "SHOCK"
    d["forecast"]["trend"] = "DECLINING"
    d["forecast"]["shock_probability"] = min(SHOCK_MAX_PROBABILITY, d["forecast"]["shock_probability"] + SHOCK_PROBABILITY_INCREMENT)
    d["risk"]["risk_score"] = min(SHOCK_MAX_RISK_SCORE, d["risk"]["risk_score"] + SHOCK_RISK_INCREMENT)
    d["risk"]["risk_level"] = "HIGH"
    r = d["resilience"]
    r["mode"] = "SHOCK"
    r["safe_to_spend_daily"] = int(r["safe_to_spend_daily"] * SHOCK_SIMULATION_SPEND_FACTOR)
    r["wallet_allocation"]["growth"] = 0
    d["recommendations"] = [
        {"type": "USE_BUFFER", "priority": "HIGH", "amount": None,
         "message": "Income shock detected \u2014 protecting your essentials",
         "reason": "Forecast income dropped sharply"},
        {"type": "REDUCE_SPEND", "priority": "HIGH", "amount": None,
         "message": f"Safe-to-spend reduced to \u20b9{r['safe_to_spend_daily']}/day",
         "reason": "Preserving liquidity through the dip"},
        {"type": "AVOID_CREDIT", "priority": "MEDIUM", "amount": None,
         "message": "Hold off on new borrowing",
         "reason": "Buffer still covers near-term needs"},
    ]
    return DashboardResponse(**d)


def _apply_recovery(dash: DashboardResponse) -> DashboardResponse:
    d = deepcopy(DashboardResponse.model_validate(dash).model_dump())
    d["forecast"]["weather"] = "STABLE"
    d["forecast"]["trend"] = "RISING"
    d["forecast"]["shock_probability"] = max(RECOVERY_MIN_SHOCK_PROBABILITY, d["forecast"]["shock_probability"] - RECOVERY_SHOCK_PROBABILITY_DECREMENT)
    d["risk"]["risk_score"] = round(max(RECOVERY_MIN_RISK_SCORE, d["risk"]["risk_score"] - RECOVERY_RISK_DECREMENT), 3)
    d["risk"]["risk_level"] = "MODERATE"
    r = d["resilience"]
    r["mode"] = "RECOVERY"
    r["safe_to_spend_daily"] = int(r["safe_to_spend_daily"] * RECOVERY_SPEND_FACTOR)
    r["resilience_score"] = min(100, r["resilience_score"] + RECOVERY_SCORE_INCREMENT)
    d["recommendations"] = [
        {"type": "SAVE", "priority": "MEDIUM", "amount": 400,
         "message": "Income recovering \u2014 rebuild your buffer with \u20b9400",
         "reason": "Trend turned positive"},
    ]
    return DashboardResponse(**d)


@app.post("/simulate/shock")
def simulate_shock(payload: dict):
    wid = payload.get("worker_id", "W001")
    factor = payload.get("factor", SHOCK_DEFAULT_FACTOR)
    return _apply_shock(get_dashboard(wid), factor)


@app.post("/simulate/recovery")
def simulate_recovery(payload: dict):
    wid = payload.get("worker_id", "W001")
    return _apply_recovery(get_dashboard(wid))
