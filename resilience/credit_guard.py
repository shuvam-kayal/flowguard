"""
Person 3 — Credit Guard. The waterfall: savings -> buffer -> delay -> future income -> credit.
Real skeleton, contract-shaped output (CreditGuardResult, #7).
"""


def evaluate_credit(profile: dict, resilience: dict, forecast: dict, requested: int) -> dict:
    savings = 0  # keep long-term savings untouched by default
    buffer_available = resilience["buffer_current"]
    remaining = max(0, requested - savings - buffer_available)
    # a slice of expected income can absorb part of the need
    future = min(remaining, int(forecast["next_30_days"] * 0.1))
    credit = max(0, remaining - future)
    safe_repay = int(credit * 0.25)  # cap repayment ~25% of credit/month

    if requested <= savings + buffer_available:
        decision = "NO_CREDIT_NEEDED"
    elif credit <= 0:
        decision = "NO_CREDIT_NEEDED"
    elif credit >= requested:
        decision = "FULL_CREDIT"
    else:
        decision = "PARTIAL_CREDIT"

    msg = (f"Use \u20b9{buffer_available} buffer + \u20b9{credit} responsible credit. "
           f"Safe repayment \u20b9{safe_repay}/month.") if credit > 0 \
          else "Your buffer covers this \u2014 no credit needed."

    return {
        "worker_id": profile["worker_id"],
        "requested_amount": requested,
        "buffer_available": buffer_available,
        "expected_shortfall": remaining,
        "recommended_credit": credit,
        "safe_monthly_repayment": safe_repay,
        "decision": decision,
        "waterfall": [
            {"source": "savings", "amount": savings, "used": savings > 0},
            {"source": "emergency_buffer", "amount": buffer_available, "used": buffer_available > 0},
            {"source": "delay_expense", "amount": 0, "used": False},
            {"source": "future_income", "amount": future, "used": future > 0},
            {"source": "credit", "amount": credit, "used": credit > 0},
        ],
        "message": msg,
    }
