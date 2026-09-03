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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(ROOT, "data", "demo")

app = FastAPI(title="FlowGuard API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hackathon: open. Lock down for any real deploy.
    allow_methods=["*"], allow_headers=["*"],
)


def _load(name):
    with open(os.path.join(DEMO, name), encoding="utf-8") as f:
        return json.load(f)


# ---- toggle: use mocks or real modules -------------------------------------
USE_REAL_MODULES = True


def get_dashboard(worker_id: str) -> dict:
    dashboards = _load("sample_dashboards.json")
    if worker_id not in dashboards:
        raise HTTPException(404, f"Unknown worker {worker_id}")
    if not USE_REAL_MODULES:
        return dashboards[worker_id]

    # ---- real orchestration path (enable at checkpoint 2) ----
    import sys
    sys.path.insert(0, ROOT)
    from ml.predict import predict_risk
    from forecast.predict import forecast_income
    from resilience.engine import evaluate, recommend

    personas = {p["worker_id"]: p for p in _load("personas.json")["personas"]}
    obligations = _load("sample_obligations.json")
    profile = personas[worker_id]
    risk = predict_risk(profile)
    forecast = forecast_income(profile)
    obl = obligations[worker_id]
    resilience = evaluate(profile, risk, forecast, obl)
    recs = recommend(profile, resilience, forecast)
    return {
        "worker": {k: profile[k] for k in ("worker_id", "name", "occupation", "current_balance")},
        "risk": risk, "forecast": forecast, "resilience": resilience,
        "obligations": obl, "recommendations": recs,
    }


@app.get("/")
def health():
    return {"status": "ok", "service": "flowguard", "real_modules": USE_REAL_MODULES}


@app.get("/workers")
def list_workers():
    dashboards = _load("sample_dashboards.json")
    return [d["worker"] for d in dashboards.values()]


@app.get("/worker/{worker_id}/dashboard")
def worker_dashboard(worker_id: str):
    return get_dashboard(worker_id)


@app.post("/ml/risk")
def risk_endpoint(payload: dict):
    from ml.predict import predict_risk
    return predict_risk(payload.get("profile", payload), payload.get("history"))


@app.post("/forecast/income")
def forecast_endpoint(payload: dict):
    from forecast.predict import forecast_income
    return forecast_income(payload.get("profile", payload), payload.get("history"))


@app.post("/resilience/evaluate")
def resilience_endpoint(payload: dict):
    from resilience.engine import evaluate, recommend
    profile, risk, forecast, obligations = (payload["profile"], payload["risk"], payload["forecast"], payload["obligations"])
    result = evaluate(profile, risk, forecast, obligations)
    return {**result, "recommendations": recommend(profile, result, forecast)}


@app.post("/credit/evaluate")
def credit_evaluate(payload: dict):
    wid = payload.get("worker_id", "W001")
    dashboard = get_dashboard(wid)
    from resilience.credit_guard import evaluate_credit
    personas = {p["worker_id"]: p for p in _load("personas.json")["personas"]}
    if wid not in personas:
        raise HTTPException(404, f"Unknown worker {wid}")
    requested = max(0, int(payload.get("requested_amount", 0)))
    return evaluate_credit(personas[wid], dashboard["resilience"], dashboard["forecast"], requested)


def _apply_shock(dash: dict, factor: float) -> dict:
    """Simulate an income shock: cut forecast, spike risk, tighten resilience."""
    d = deepcopy(dash)
    d["forecast"]["next_30_days"] = int(d["forecast"]["next_30_days"] * factor)
    d["forecast"]["next_7_days"] = int(d["forecast"]["next_7_days"] * factor)
    d["forecast"]["weather"] = "SHOCK"
    d["forecast"]["trend"] = "DECLINING"
    d["forecast"]["shock_probability"] = min(0.95, d["forecast"]["shock_probability"] + 0.3)
    d["risk"]["risk_score"] = min(0.95, d["risk"]["risk_score"] + 0.25)
    d["risk"]["risk_level"] = "HIGH"
    r = d["resilience"]
    r["mode"] = "SHOCK"
    r["safe_to_spend_daily"] = int(r["safe_to_spend_daily"] * 0.55)
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
    return d


def _apply_recovery(dash: dict) -> dict:
    d = deepcopy(dash)
    d["forecast"]["weather"] = "STABLE"
    d["forecast"]["trend"] = "RISING"
    d["forecast"]["shock_probability"] = max(0.15, d["forecast"]["shock_probability"] - 0.3)
    d["risk"]["risk_score"] = max(0.2, d["risk"]["risk_score"] - 0.2)
    d["risk"]["risk_level"] = "MODERATE"
    r = d["resilience"]
    r["mode"] = "RECOVERY"
    r["safe_to_spend_daily"] = int(r["safe_to_spend_daily"] * 1.4)
    r["resilience_score"] = min(100, r["resilience_score"] + 10)
    d["recommendations"] = [
        {"type": "SAVE", "priority": "MEDIUM", "amount": 400,
         "message": "Income recovering \u2014 rebuild your buffer with \u20b9400",
         "reason": "Trend turned positive"},
    ]
    return d


@app.post("/simulate/shock")
def simulate_shock(payload: dict):
    wid = payload.get("worker_id", "W001")
    factor = payload.get("factor", 0.65)  # 35% income drop by default
    return _apply_shock(get_dashboard(wid), factor)


@app.post("/simulate/recovery")
def simulate_recovery(payload: dict):
    wid = payload.get("worker_id", "W001")
    return _apply_recovery(get_dashboard(wid))
