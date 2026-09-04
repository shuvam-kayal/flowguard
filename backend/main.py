"""
Person 4 — FastAPI backend / orchestration.
Wires the four modules together behind ONE dashboard endpoint.
Uses SQLite database via SQLAlchemy.

Run:  uvicorn backend.main:app --reload --port 8000
"""
import os
from copy import deepcopy
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.services.income import get_income_history
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
from backend.database import get_db, engine, Base, initialize_database
from backend.models import (
    User, Obligation, RiskResultModel, ForecastResultModel, 
    ResilienceResultModel, Recommendation as RecommendationModel
)
from backend.models import Transaction, IncomeRecord, Expense
from backend.auth.router import router as auth_router
from backend.auth.dependencies import get_current_user
from backend.schemas.api import ProfileUpdate, TransactionCreate, IncomeCreate, ExpenseCreate, ObligationCreate
from backend.services.recompute import recompute_worker

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="FlowGuard API", version="0.1.0")
_origins = [origin.strip() for origin in os.getenv("FLOWGUARD_ALLOWED_ORIGINS", "*").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_methods=["*"], allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
initialize_database()

# ---- toggle: use mocks or real modules -------------------------------------
# Set to False to read pre-computed risk/resilience from the DB. 
# Set to True to evaluate on-the-fly using the actual ML/engine modules.
USE_REAL_MODULES = True

def get_dashboard(worker_id: str, db: Session) -> DashboardResponse:
    user = db.query(User).filter(User.worker_id == worker_id).first()
    if not user:
        raise HTTPException(404, f"Unknown worker {worker_id}")

    obs = db.query(Obligation).filter(Obligation.worker_id == worker_id).all()
    total_upcoming = sum(o.amount for o in obs)
    obl_summary = ObligationSummary(
        worker_id=worker_id,
        upcoming_obligations=[
            {"name": o.name, "amount": o.amount, "due_date": o.due_date, "category": o.category}
            for o in obs
        ],
        total_upcoming=total_upcoming,
        essential_daily_spend=user.fixed_expenses // 30
    )

    if not USE_REAL_MODULES:
        risk_m = db.query(RiskResultModel).filter_by(worker_id=worker_id).first()
        fc_m = db.query(ForecastResultModel).filter_by(worker_id=worker_id).first()
        rs_m = db.query(ResilienceResultModel).filter_by(worker_id=worker_id).first()
        recs_m = db.query(RecommendationModel).filter_by(worker_id=worker_id).all()

        if not (risk_m and fc_m and rs_m):
            raise HTTPException(500, "Dashboard data not seeded for this worker.")

        risk = RiskResult(
            worker_id=risk_m.worker_id, risk_score=risk_m.risk_score, 
            risk_level=risk_m.risk_level, confidence=risk_m.confidence, top_factors=risk_m.top_factors
        )
        forecast = ForecastResult(
            worker_id=fc_m.worker_id, next_7_days=fc_m.next_7_days, next_30_days=fc_m.next_30_days,
            lower_bound=fc_m.lower_bound, upper_bound=fc_m.upper_bound, trend=fc_m.trend,
            shock_probability=fc_m.shock_probability, weather=fc_m.weather, daily_forecast=fc_m.daily_forecast
        )
        resilience = ResilienceResult(
            worker_id=rs_m.worker_id, safe_to_spend_daily=rs_m.safe_to_spend_daily,
            resilience_score=rs_m.resilience_score, resilience_days=rs_m.resilience_days,
            buffer_target=rs_m.buffer_target, buffer_current=rs_m.buffer_current,
            recommended_save=rs_m.recommended_save, mode=rs_m.mode,
            wallet_allocation=rs_m.wallet_allocation, score_breakdown=rs_m.score_breakdown
        )
        recs = [
            {"type": r.type, "priority": r.priority, "amount": r.amount, "message": r.message, "reason": r.reason}
            for r in recs_m
        ]
    else:
        # ---- real orchestration path ----
        import sys
        if ROOT not in sys.path:
            sys.path.insert(0, ROOT)
        from ml.predict import predict_risk
        from forecast.predict import forecast_income
        from resilience.engine import evaluate, recommend

        profile_data = {c.name: getattr(user, c.name) for c in user.__table__.columns}
        profile = FinancialProfile(**profile_data)

        history = get_income_history(worker_id, db)
        risk = predict_risk(profile, history)
        forecast = forecast_income(profile, history)
        resilience = evaluate(profile, risk, forecast, obl_summary)
        recs = recommend(profile, resilience, forecast, obl_summary)

    return DashboardResponse(
        worker={"worker_id": user.worker_id, "name": user.name, "occupation": user.occupation, "current_balance": user.current_balance},
        risk=risk, forecast=forecast, resilience=resilience,
        obligations=obl_summary, recommendations=recs,
    )


def _profile_dict(user: User) -> dict:
    return {c.name: getattr(user, c.name) for c in user.__table__.columns
            if c.name not in {"hashed_password"}}


def _refresh(user: User, db: Session):
    recompute_worker(user.worker_id, db)
    db.commit()


@app.get("/api/profile/me")
def profile_me(current_user: User = Depends(get_current_user)):
    return _profile_dict(current_user)


@app.put("/api/profile/me")
def update_profile(payload: ProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, key, value)
    if current_user.monthly_income_avg:
        current_user.expense_to_income_ratio = round(current_user.total_monthly_expenses / current_user.monthly_income_avg, 2)
    _refresh(current_user, db)
    return _profile_dict(current_user)


def _owned_query(model, user: User, db: Session):
    return db.query(model).filter(model.worker_id == user.worker_id)


@app.get("/api/transactions")
def list_transactions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _owned_query(Transaction, current_user, db).order_by(Transaction.date.desc(), Transaction.id.desc()).all()


@app.post("/api/transactions")
def add_transaction(payload: TransactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = Transaction(worker_id=current_user.worker_id, **payload.model_dump())
    db.add(item)
    if item.type.upper() == "CREDIT": current_user.current_balance += item.amount
    else: current_user.current_balance = max(0, current_user.current_balance - item.amount)
    _refresh(current_user, db)
    return item


@app.delete("/api/transactions/{item_id}")
def delete_transaction(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = _owned_query(Transaction, current_user, db).filter(Transaction.id == item_id).first()
    if not item: raise HTTPException(404, "Transaction not found")
    db.delete(item); db.flush(); _refresh(current_user, db)
    return {"deleted": item_id}


@app.get("/api/income")
def list_income(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _owned_query(IncomeRecord, current_user, db).order_by(IncomeRecord.date.desc()).all()


@app.post("/api/income")
def add_income(payload: IncomeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = IncomeRecord(worker_id=current_user.worker_id, amount=payload.amount, date=payload.date)
    db.add(item); current_user.current_balance += item.amount; db.flush(); _refresh(current_user, db)
    return item


@app.delete("/api/income/{item_id}")
def delete_income(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = _owned_query(IncomeRecord, current_user, db).filter(IncomeRecord.id == item_id).first()
    if not item: raise HTTPException(404, "Income record not found")
    db.delete(item); db.flush(); _refresh(current_user, db)
    return {"deleted": item_id}


@app.get("/api/expenses")
def list_expenses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _owned_query(Expense, current_user, db).order_by(Expense.date.desc()).all()


@app.post("/api/expenses")
def add_expense(payload: ExpenseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = Expense(worker_id=current_user.worker_id, **payload.model_dump())
    db.add(item); current_user.current_balance = max(0, current_user.current_balance - item.amount)
    current_user.total_monthly_expenses += item.amount
    current_user.variable_expenses += item.amount
    db.flush(); _refresh(current_user, db)
    return item


@app.delete("/api/expenses/{item_id}")
def delete_expense(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = _owned_query(Expense, current_user, db).filter(Expense.id == item_id).first()
    if not item: raise HTTPException(404, "Expense not found")
    current_user.total_monthly_expenses = max(0, current_user.total_monthly_expenses - item.amount)
    current_user.variable_expenses = max(0, current_user.variable_expenses - item.amount)
    db.delete(item); db.flush(); _refresh(current_user, db)
    return {"deleted": item_id}


@app.get("/api/obligations")
def list_obligations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _owned_query(Obligation, current_user, db).all()


@app.post("/api/obligations")
def add_obligation(payload: ObligationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = Obligation(worker_id=current_user.worker_id, **payload.model_dump())
    db.add(item); db.flush(); _refresh(current_user, db)
    return item


@app.put("/api/obligations/{item_id}")
def update_obligation(item_id: int, payload: ObligationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = _owned_query(Obligation, current_user, db).filter(Obligation.id == item_id).first()
    if not item: raise HTTPException(404, "Obligation not found")
    for key, value in payload.model_dump().items(): setattr(item, key, value)
    db.flush(); _refresh(current_user, db)
    return item


@app.delete("/api/obligations/{item_id}")
def delete_obligation(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = _owned_query(Obligation, current_user, db).filter(Obligation.id == item_id).first()
    if not item: raise HTTPException(404, "Obligation not found")
    db.delete(item); db.flush(); _refresh(current_user, db)
    return {"deleted": item_id}


@app.get("/api/dashboard")
def current_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> DashboardResponse:
    return get_dashboard(current_user.worker_id, db)


@app.post("/api/dashboard/recompute")
def refresh_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> DashboardResponse:
    _refresh(current_user, db)
    return get_dashboard(current_user.worker_id, db)


@app.get("/")
def health():
    return {"status": "ok", "service": "flowguard", "real_modules": USE_REAL_MODULES}


@app.get("/workers")
def list_workers(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"worker_id": u.worker_id, "name": u.name, "occupation": u.occupation, "current_balance": u.current_balance} for u in users]


@app.get("/worker/{worker_id}/dashboard")
def worker_dashboard(worker_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> DashboardResponse:
    if current_user.worker_id != worker_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this dashboard")
    return get_dashboard(worker_id, db)


@app.post("/ml/risk")
def risk_endpoint(payload: dict, current_user: User = Depends(get_current_user)):
    from ml.predict import predict_risk
    return predict_risk(FinancialProfile.model_validate(payload.get("profile", payload)), payload.get("history"))


@app.post("/forecast/income")
def forecast_endpoint(payload: dict, current_user: User = Depends(get_current_user)):
    from forecast.predict import forecast_income
    return forecast_income(FinancialProfile.model_validate(payload.get("profile", payload)), payload.get("history"))


@app.post("/resilience/evaluate")
def resilience_endpoint(payload: dict, current_user: User = Depends(get_current_user)):
    from resilience.engine import evaluate, recommend
    profile = FinancialProfile.model_validate(payload["profile"])
    risk = RiskResult.model_validate(payload["risk"])
    forecast = ForecastResult.model_validate(payload["forecast"])
    obligations = ObligationSummary.model_validate(payload["obligations"])
    result = evaluate(profile, risk, forecast, obligations)
    return {**result.model_dump(), "recommendations": [item.model_dump() for item in recommend(profile, result, forecast, obligations)]}


@app.post("/credit/evaluate")
def credit_evaluate(payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    wid = payload.get("worker_id", "W001")
    if current_user.worker_id != wid:
        raise HTTPException(status_code=403, detail="Not authorized")
    dashboard = get_dashboard(wid, db)
    from resilience.credit_guard import evaluate_credit
    
    user = db.query(User).filter(User.worker_id == wid).first()
    if not user:
        raise HTTPException(404, f"Unknown worker {wid}")
    
    profile_data = {
        c.name: getattr(user, c.name)
        for c in user.__table__.columns
        if c.name not in {"email", "phone", "hashed_password"}
    }
    profile = FinancialProfile(**profile_data)
    
    requested = max(0, int(payload.get("requested_amount", 0)))
    return evaluate_credit(profile,
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
def simulate_shock(payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    wid = payload.get("worker_id", "W001")
    if current_user.worker_id != wid:
        raise HTTPException(status_code=403, detail="Not authorized")
    factor = payload.get("factor", SHOCK_DEFAULT_FACTOR)
    return _apply_shock(get_dashboard(wid, db), factor)


@app.post("/simulate/recovery")
def simulate_recovery(payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    wid = payload.get("worker_id", "W001")
    if current_user.worker_id != wid:
        raise HTTPException(status_code=403, detail="Not authorized")
    return _apply_recovery(get_dashboard(wid, db))
