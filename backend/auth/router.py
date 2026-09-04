from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
from backend.auth.schemas import Token, LoginRequest, SignupRequest
from backend.auth.security import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.auth.dependencies import get_current_user
from backend.services.mock_data import (generate_worker_scenario, generate_income_records,
    generate_expenses, generate_transactions, generate_obligations)
from backend.services.recompute import recompute_worker

router = APIRouter()

@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == request.phone).first()
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
    return {"access_token": access_token, "token_type": "bearer", "worker_id": user.worker_id,
            "profile_complete": bool(user.name and user.occupation)}


@router.post("/signup", response_model=Token)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter((User.email == request.email) | (User.phone == request.phone)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or phone already registered"
        )
    last = db.query(User).filter(User.worker_id.like("FG%" )).order_by(User.worker_id.desc()).first()
    number = int(last.worker_id[2:]) + 1 if last and last.worker_id[2:].isdigit() else 10001
    worker_id = f"FG{number:05d}"
    scenario = generate_worker_scenario()
    ratio = round(scenario["total"] / scenario["income"], 2)
    new_user = User(
        worker_id=worker_id, email=request.email, phone=request.phone, name="", occupation="",
        hashed_password=get_password_hash(request.password),
        current_balance=scenario["balance"], monthly_income_avg=scenario["income"], monthly_income_std=scenario["std"],
        income_trend=scenario["trend"], total_monthly_expenses=scenario["total"], fixed_expenses=scenario["fixed"],
        variable_expenses=scenario["variable"], savings_balance=scenario["savings"], emergency_buffer=scenario["savings"],
        total_debt=scenario["debt"], monthly_emi=scenario["emi"], dependents=0, avg_work_hours_per_week=40,
        active_platforms=["Swiggy", "Uber"],
        expense_to_income_ratio=ratio
    )
    db.add(new_user)
    incomes = generate_income_records(worker_id, scenario)
    expenses = generate_expenses(worker_id, scenario)
    db.add_all(incomes + expenses + generate_transactions(worker_id, incomes, expenses) + generate_obligations(worker_id, scenario))
    try:
        db.flush()
        recompute_worker(worker_id, db)
        db.commit()
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Could not initialize financial data: {str(e)}")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.worker_id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "worker_id": worker_id, "profile_complete": False}


@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "worker_id": current_user.worker_id,
        "name": current_user.name,
        "occupation": current_user.occupation,
        "email": current_user.email,
        "phone": current_user.phone,
        "profile_complete": bool(current_user.name and current_user.occupation)
    }
