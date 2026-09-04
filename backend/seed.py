import json
import os
import sys

# Ensure ROOT is in sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.database import engine, Base, SessionLocal
from backend.models import (
    User, Obligation, RiskResultModel, ForecastResultModel, 
    ResilienceResultModel, Recommendation
)
from backend.schemas.contracts import FinancialProfile
from backend.auth.security import get_password_hash

def load_json(filename):
    path = os.path.join(ROOT, "data", "demo", filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def seed():
    print("Recreating database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    print("Loading personas...")
    personas_data = load_json("personas.json").get("personas", [])
    
    print("Loading obligations...")
    obligations_data = load_json("sample_obligations.json")

    print("Loading dashboards (for pre-computed risk/forecast/resilience)...")
    dashboards_data = load_json("sample_dashboards.json")

    default_password_hash = get_password_hash("password123")

    for p_data in personas_data:
        worker_id = p_data["worker_id"]
        
        # 1. Create User
        # Filter p_data to match FinancialProfile / User model
        profile_data = {k: v for k, v in p_data.items() if hasattr(User, k)}
        demo_number = 9000000000 + int(worker_id[1:])
        user = User(**profile_data, email=f"{worker_id.lower()}@demo.flowguard.local",
                    phone=str(demo_number), hashed_password=default_password_hash)
        db.add(user)

        # 2. Create Obligations
        obs = obligations_data.get(worker_id, {}).get("upcoming_obligations", [])
        for o in obs:
            ob = Obligation(
                worker_id=worker_id,
                name=o["name"],
                amount=o["amount"],
                due_date=o["due_date"],
                category=o["category"]
            )
            db.add(ob)

        # 3. Create Pre-computed Results if available
        dash = dashboards_data.get(worker_id)
        if dash:
            # Risk
            risk = dash["risk"]
            risk_model = RiskResultModel(
                worker_id=worker_id,
                risk_score=risk["risk_score"],
                risk_level=risk["risk_level"],
                confidence=risk["confidence"],
                top_factors=risk["top_factors"]
            )
            db.add(risk_model)

            # Forecast
            fc = dash["forecast"]
            fc_model = ForecastResultModel(
                worker_id=worker_id,
                next_7_days=fc["next_7_days"],
                next_30_days=fc["next_30_days"],
                lower_bound=fc["lower_bound"],
                upper_bound=fc["upper_bound"],
                trend=fc["trend"],
                shock_probability=fc["shock_probability"],
                weather=fc["weather"],
                daily_forecast=fc["daily_forecast"]
            )
            db.add(fc_model)

            # Resilience
            rs = dash["resilience"]
            rs_model = ResilienceResultModel(
                worker_id=worker_id,
                safe_to_spend_daily=rs["safe_to_spend_daily"],
                resilience_score=rs["resilience_score"],
                resilience_days=rs["resilience_days"],
                buffer_target=rs["buffer_target"],
                buffer_current=rs["buffer_current"],
                recommended_save=rs["recommended_save"],
                mode=rs["mode"],
                wallet_allocation=rs["wallet_allocation"],
                score_breakdown=rs["score_breakdown"]
            )
            db.add(rs_model)

            # Recommendations
            for r in dash.get("recommendations", []):
                rec_model = Recommendation(
                    worker_id=worker_id,
                    type=r["type"],
                    priority=r["priority"],
                    amount=r.get("amount"),
                    message=r["message"],
                    reason=r["reason"]
                )
                db.add(rec_model)

    db.commit()
    db.close()
    print("Seed complete!")

if __name__ == "__main__":
    seed()
