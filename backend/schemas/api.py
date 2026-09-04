from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    occupation: Optional[str] = None
    current_balance: Optional[int] = Field(None, ge=0)
    monthly_income_avg: Optional[int] = Field(None, ge=0)
    monthly_income_std: Optional[int] = Field(None, ge=0)
    income_trend: Optional[str] = None
    total_monthly_expenses: Optional[int] = Field(None, ge=0)
    fixed_expenses: Optional[int] = Field(None, ge=0)
    variable_expenses: Optional[int] = Field(None, ge=0)
    savings_balance: Optional[int] = Field(None, ge=0)
    emergency_buffer: Optional[int] = Field(None, ge=0)
    total_debt: Optional[int] = Field(None, ge=0)
    monthly_emi: Optional[int] = Field(None, ge=0)
    dependents: Optional[int] = Field(None, ge=0)
    avg_work_hours_per_week: Optional[int] = Field(None, ge=0)
    active_platforms: Optional[list[str]] = None


class TransactionCreate(BaseModel):
    amount: int = Field(gt=0)
    date: str = Field(default_factory=lambda: date.today().isoformat())
    type: str = "DEBIT"
    category: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None


class IncomeCreate(BaseModel):
    amount: int = Field(gt=0)
    date: str = Field(default_factory=lambda: date.today().isoformat())
    source: Optional[str] = None


class ExpenseCreate(BaseModel):
    amount: int = Field(gt=0)
    category: str = "OTHER"
    date: str = Field(default_factory=lambda: date.today().isoformat())


class ObligationCreate(BaseModel):
    name: str
    amount: int = Field(gt=0)
    due_date: str
    category: str = "OTHER"
