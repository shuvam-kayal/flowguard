from backend.models import User, Obligation, RiskResultModel, ForecastResultModel, ResilienceResultModel, Recommendation
from backend.schemas.contracts import FinancialProfile, ObligationSummary
from backend.services.income import get_income_history


def recompute_worker(worker_id: str, db):
    user = db.query(User).filter_by(worker_id=worker_id).first()
    if not user:
        raise ValueError(f"Unknown worker {worker_id}")
    from ml.predict import predict_risk
    from forecast.predict import forecast_income
    from resilience.engine import evaluate, recommend

    obligations = db.query(Obligation).filter_by(worker_id=worker_id).all()
    summary = ObligationSummary(worker_id=worker_id,
        upcoming_obligations=[{"name": o.name, "amount": o.amount, "due_date": o.due_date, "category": o.category} for o in obligations],
        total_upcoming=sum(o.amount for o in obligations), essential_daily_spend=max(1, user.fixed_expenses // 30))
    profile = FinancialProfile(**{c.name: getattr(user, c.name) for c in user.__table__.columns if c.name not in {"email", "phone", "hashed_password"}})
    history = get_income_history(worker_id, db)
    risk, forecast = predict_risk(profile, history), forecast_income(profile, history)
    resilience = evaluate(profile, risk, forecast, summary)
    recommendations = recommend(profile, resilience, forecast, summary)
    db.query(RiskResultModel).filter_by(worker_id=worker_id).delete()
    db.query(ForecastResultModel).filter_by(worker_id=worker_id).delete()
    db.query(ResilienceResultModel).filter_by(worker_id=worker_id).delete()
    db.query(Recommendation).filter_by(worker_id=worker_id).delete()
    db.add(RiskResultModel(worker_id=worker_id, **risk.model_dump(exclude={"worker_id"})))
    db.add(ForecastResultModel(worker_id=worker_id, **forecast.model_dump(exclude={"worker_id"})))
    resilience_data = resilience.model_dump(exclude={"worker_id"}) if hasattr(resilience, "model_dump") else {k: v for k, v in (resilience.items() if isinstance(resilience, dict) else resilience.__dict__.items()) if k != "worker_id"}
    db.add(ResilienceResultModel(worker_id=worker_id, **resilience_data))
    for item in recommendations:
        db.add(Recommendation(worker_id=worker_id, **(item.model_dump() if hasattr(item, "model_dump") else item)))
    return risk, forecast, resilience, recommendations
