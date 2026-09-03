"""
FlowGuard shared schemas — the API contracts as code.
Every module imports from here so shapes stay in sync.
Mirror of docs/api-contract.md. If you change a field, change the doc too.
"""
from __future__ import annotations
from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field

RiskLevel = Literal["LOW", "MODERATE", "HIGH"]
Trend = Literal["RISING", "STABLE", "DECLINING"]
Weather = Literal["STABLE", "WATCH", "SHOCK"]
Mode = Literal["NORMAL", "WATCH", "SHOCK", "RECOVERY"]


class FinancialProfile(BaseModel):
    worker_id: str
    name: str
    occupation: str
    current_balance: int
    monthly_income_avg: int
    monthly_income_std: int
    income_trend: Trend
    total_monthly_expenses: int
    fixed_expenses: int
    variable_expenses: int
    savings_balance: int
    emergency_buffer: int
    total_debt: int
    monthly_emi: int
    dependents: int
    avg_work_hours_per_week: int
    active_platforms: List[str]
    expense_to_income_ratio: float


class RiskFactor(BaseModel):
    feature: str
    impact: float
    direction: Literal["increases_risk", "decreases_risk"]


class RiskResult(BaseModel):
    worker_id: str
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)
    top_factors: List[RiskFactor]


class DailyForecastPoint(BaseModel):
    date: str
    expected: int
    lower: int
    upper: int


class ForecastResult(BaseModel):
    worker_id: str
    next_7_days: int
    next_30_days: int
    lower_bound: int
    upper_bound: int
    trend: Trend
    shock_probability: float = Field(ge=0.0, le=1.0)
    weather: Weather
    daily_forecast: List[DailyForecastPoint]


class Obligation(BaseModel):
    name: str
    amount: int
    due_date: str
    category: Literal["FIXED", "DEBT", "UTILITY", "OTHER"]


class ObligationSummary(BaseModel):
    worker_id: str
    upcoming_obligations: List[Obligation]
    total_upcoming: int
    essential_daily_spend: int


class WalletAllocation(BaseModel):
    daily: int
    bills: int
    buffer: int
    growth: int


class ScoreBreakdown(BaseModel):
    income_stability: int
    emergency_buffer: int
    expense_coverage: int
    debt_burden: int
    savings_consistency: int


class ResilienceResult(BaseModel):
    worker_id: str
    safe_to_spend_daily: int
    resilience_score: int = Field(ge=0, le=100)
    resilience_days: int
    buffer_target: int
    buffer_current: int
    recommended_save: int
    mode: Mode
    wallet_allocation: WalletAllocation
    score_breakdown: ScoreBreakdown


class Recommendation(BaseModel):
    type: Literal["SAVE", "REDUCE_SPEND", "RESERVE_BILL", "AVOID_CREDIT", "USE_BUFFER", "TAKE_CREDIT"]
    priority: Literal["LOW", "MEDIUM", "HIGH"]
    amount: Optional[int] = None
    message: str
    reason: str


class WaterfallStep(BaseModel):
    source: Literal["savings", "emergency_buffer", "delay_expense", "future_income", "credit"]
    amount: int
    used: bool


class CreditGuardResult(BaseModel):
    worker_id: str
    requested_amount: int
    buffer_available: int
    expected_shortfall: int
    recommended_credit: int
    safe_monthly_repayment: int
    decision: Literal["NO_CREDIT_NEEDED", "PARTIAL_CREDIT", "FULL_CREDIT", "CREDIT_DECLINED"]
    waterfall: List[WaterfallStep]
    message: str


class WorkerSummary(BaseModel):
    worker_id: str
    name: str
    occupation: str
    current_balance: int


class DashboardResponse(BaseModel):
    worker: WorkerSummary
    risk: RiskResult
    forecast: ForecastResult
    resilience: ResilienceResult
    obligations: ObligationSummary
    recommendations: List[Recommendation]
