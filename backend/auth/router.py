from datetime import timedelta
import random
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Obligation, RiskResultModel, ForecastResultModel, ResilienceResultModel, Recommendation
from backend.auth.schemas import Token, LoginRequest, SignupRequest
from backend.auth.security import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.auth.dependencies import get_current_user

router = APIRouter()

@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.worker_id == request.worker_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.worker_id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/signup", response_model=Token)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.worker_id == request.worker_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Worker ID already registered"
        )
    
    # Gig-worker realistic mock data
    monthly_income = random.randint(12000, 25000)
    fixed_exp = random.randint(6000, 10000)
    var_exp = random.randint(3000, 8000)
    total_exp = fixed_exp + var_exp
    balance = max(500, monthly_income - total_exp + random.randint(0, 2000))
    savings = random.randint(0, 5000)
    debt = random.randint(0, 15000)
    emi = random.randint(0, 2000) if debt > 0 else 0
    ratio = round(total_exp / monthly_income, 2)
    
    new_user = User(
        worker_id=request.worker_id,
        name=request.name,
        occupation=request.occupation,
        hashed_password=get_password_hash(request.password),
        current_balance=balance,
        monthly_income_avg=monthly_income,
        monthly_income_std=random.randint(2000, 5000),
        income_trend="VARIABLE",
        total_monthly_expenses=total_exp,
        fixed_expenses=fixed_exp,
        variable_expenses=var_exp,
        savings_balance=savings,
        emergency_buffer=savings,
        total_debt=debt,
        monthly_emi=emi,
        dependents=random.randint(0, 3),
        avg_work_hours_per_week=random.randint(35, 60),
        active_platforms=["Uber", "Zomato"] if "driver" in request.occupation.lower() or "delivery" in request.occupation.lower() else ["UrbanCompany"],
        expense_to_income_ratio=ratio
    )
    db.add(new_user)
    
    # Add obligations
    rent = Obligation(worker_id=request.worker_id, name="Rent", amount=fixed_exp - 2000, due_date="2026-10-01", category="HOUSING")
    db.add(rent)
    
    # Add Risk
    risk = RiskResultModel(
        worker_id=request.worker_id,
        risk_score=random.uniform(30.0, 70.0),
        risk_level="MODERATE" if ratio < 0.8 else "HIGH",
        confidence=0.85,
        top_factors=["High expense ratio", "Variable income"]
    )
    db.add(risk)
    
    # Add Forecast
    fc = ForecastResultModel(
        worker_id=request.worker_id,
        next_7_days=int(monthly_income/4),
        next_30_days=monthly_income,
        lower_bound=int(monthly_income * 0.8),
        upper_bound=int(monthly_income * 1.2),
        trend="STABLE",
        shock_probability=random.uniform(0.1, 0.4),
        weather="STABLE",
        daily_forecast=[]
    )
    db.add(fc)
    
    # Add Resilience
    rs = ResilienceResultModel(
        worker_id=request.worker_id,
        safe_to_spend_daily=int((monthly_income - fixed_exp - emi) / 30),
        resilience_score=random.randint(40, 75),
        resilience_days=int(savings / (fixed_exp/30)) if fixed_exp > 0 else 0,
        buffer_target=fixed_exp * 3,
        buffer_current=savings,
        recommended_save=int(monthly_income * 0.1),
        mode="NORMAL",
        wallet_allocation={"essential": 60, "growth": 20, "discretionary": 20},
        score_breakdown={"liquidity": 50, "debt": 60, "income_stability": 40}
    )
    db.add(rs)
    
    # Commit all
    db.commit()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.worker_id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "worker_id": current_user.worker_id,
        "name": current_user.name,
        "occupation": current_user.occupation
    }
