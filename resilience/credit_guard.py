"""Credit Guard waterfall: savings → buffer → future income → credit."""
from __future__ import annotations

from backend.schemas.contracts import CreditGuardResult, FinancialProfile, ForecastResult, ResilienceResult
from constants import CREDIT_FUTURE_INCOME_RATE, CREDIT_MIN_SERVICE_RATE, CREDIT_REPAYMENT_CAP_RATE


def evaluate_credit(profile: FinancialProfile, resilience: ResilienceResult,
                    forecast: ForecastResult, requested: int) -> CreditGuardResult:
    profile = FinancialProfile.model_validate(profile)
    resilience = ResilienceResult.model_validate(resilience)
    forecast = ForecastResult.model_validate(forecast)
    requested = max(0, int(requested))
    savings = 0  # keep long-term savings untouched by default
    buffer_available = min(requested, max(0, resilience.buffer_current))
    remaining = max(0, requested - savings - buffer_available)
    # a slice of expected income can absorb part of the need
    future = min(remaining, int(forecast.next_30_days * CREDIT_FUTURE_INCOME_RATE))
    credit = max(0, remaining - future)
    disposable = max(0, profile.monthly_income_avg - profile.total_monthly_expenses)
    safe_repay = min(int(credit * CREDIT_REPAYMENT_CAP_RATE), int(disposable * CREDIT_REPAYMENT_CAP_RATE))

    if requested <= savings + buffer_available:
        decision = "NO_CREDIT_NEEDED"
    elif credit <= 0:
        decision = "NO_CREDIT_NEEDED"
    elif safe_repay < int(credit * CREDIT_MIN_SERVICE_RATE):
        decision = "CREDIT_DECLINED"
    elif credit == requested:
        decision = "FULL_CREDIT"
    else:
        decision = "PARTIAL_CREDIT"

    msg = (f"Use \u20b9{buffer_available} buffer + \u20b9{credit} responsible credit. "
           f"Safe repayment \u20b9{safe_repay}/month.") if credit > 0 \
          else "Your buffer covers this \u2014 no credit needed."

    return CreditGuardResult(worker_id=profile.worker_id, requested_amount=requested,
        buffer_available=buffer_available, expected_shortfall=remaining,
        recommended_credit=credit, safe_monthly_repayment=safe_repay, decision=decision,
        waterfall=[
            {"source": "savings", "amount": savings, "used": savings > 0},
            {"source": "emergency_buffer", "amount": buffer_available, "used": buffer_available > 0},
            {"source": "delay_expense", "amount": 0, "used": False},
            {"source": "future_income", "amount": future, "used": future > 0},
            {"source": "credit", "amount": credit, "used": credit > 0},
        ], message=msg)
