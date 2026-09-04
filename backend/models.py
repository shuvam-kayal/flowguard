from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    worker_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    occupation = Column(String, nullable=False)
    current_balance = Column(Integer, default=0)
    monthly_income_avg = Column(Integer, default=0)
    monthly_income_std = Column(Integer, default=0)
    income_trend = Column(String, default="STABLE")
    total_monthly_expenses = Column(Integer, default=0)
    fixed_expenses = Column(Integer, default=0)
    variable_expenses = Column(Integer, default=0)
    savings_balance = Column(Integer, default=0)
    emergency_buffer = Column(Integer, default=0)
    total_debt = Column(Integer, default=0)
    monthly_emi = Column(Integer, default=0)
    dependents = Column(Integer, default=0)
    avg_work_hours_per_week = Column(Integer, default=0)
    active_platforms = Column(JSON, default=list)
    expense_to_income_ratio = Column(Float, default=0.0)

    obligations = relationship("Obligation", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String, ForeignKey("users.worker_id"))
    amount = Column(Integer)
    date = Column(String)
    type = Column(String)


class IncomeRecord(Base):
    __tablename__ = "income_records"
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String, ForeignKey("users.worker_id"))
    amount = Column(Integer)
    date = Column(String)


class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String, ForeignKey("users.worker_id"))
    amount = Column(Integer)
    category = Column(String)
    date = Column(String)


class Obligation(Base):
    __tablename__ = "obligations"
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String, ForeignKey("users.worker_id"))
    name = Column(String)
    amount = Column(Integer)
    due_date = Column(String)
    category = Column(String)

    user = relationship("User", back_populates="obligations")


class RiskResultModel(Base):
    __tablename__ = "risk_results"
    worker_id = Column(String, ForeignKey("users.worker_id"), primary_key=True)
    risk_score = Column(Float)
    risk_level = Column(String)
    confidence = Column(Float)
    top_factors = Column(JSON)


class ForecastResultModel(Base):
    __tablename__ = "forecasts"
    worker_id = Column(String, ForeignKey("users.worker_id"), primary_key=True)
    next_7_days = Column(Integer)
    next_30_days = Column(Integer)
    lower_bound = Column(Integer)
    upper_bound = Column(Integer)
    trend = Column(String)
    shock_probability = Column(Float)
    weather = Column(String)
    daily_forecast = Column(JSON)


class ResilienceResultModel(Base):
    __tablename__ = "resilience_results"
    worker_id = Column(String, ForeignKey("users.worker_id"), primary_key=True)
    safe_to_spend_daily = Column(Integer)
    resilience_score = Column(Integer)
    resilience_days = Column(Integer)
    buffer_target = Column(Integer)
    buffer_current = Column(Integer)
    recommended_save = Column(Integer)
    mode = Column(String)
    wallet_allocation = Column(JSON)
    score_breakdown = Column(JSON)


class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String, ForeignKey("users.worker_id"))
    type = Column(String)
    priority = Column(String)
    amount = Column(Integer, nullable=True)
    message = Column(String)
    reason = Column(String)

    user = relationship("User", back_populates="recommendations")
