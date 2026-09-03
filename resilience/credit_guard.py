"""
Person 3 — Credit Guard. The waterfall: savings -> buffer -> delay -> future income -> credit.
Real skeleton, contract-shaped output (CreditGuardResult, #7).
"""


def evaluate_credit(profile: dict, resilience: dict, forecast: dict, requested: int) -> dict:
    """Credit Guard waterfall: savings -> buffer -> delay expense -> future income -> credit.

    Credit is the LAST resort, and only ever offered up to what the worker can
    safely repay. If even the safe credit slice can't close the gap, we decline
    rather than hand out an unaffordable loan.
    """
    requested = max(0, int(requested))
    savings = 0  # keep long-term savings untouched by default
    buffer_available = resilience["buffer_current"]

    # 1) savings + buffer
    remaining = max(0, requested - savings - buffer_available)

    # 2) delay expense: a portion of the gap can be deferred rather than funded now
    #    (bounded, so it never magically erases the whole need)
    delay = min(remaining, int(requested * 0.15))
    remaining_after_delay = remaining - delay

    # 3) a slice of expected income can absorb part of the remaining need
    future = min(remaining_after_delay, int(forecast["next_30_days"] * 0.10))
    gap = max(0, remaining_after_delay - future)

    # 4) credit is the last resort, capped at safe repayment capacity.
    #    Safe monthly repayment ~= 20% of expected monthly income; assume a
    #    3-month responsible term, so max safe principal = 3 * that.
    safe_repay_capacity = int(forecast["next_30_days"] * 0.20)
    max_safe_credit = safe_repay_capacity * 3
    credit = min(gap, max_safe_credit)
    safe_repay = int(credit / 3) if credit > 0 else 0
    unfunded = gap - credit  # gap credit still cannot safely cover

    if requested <= savings + buffer_available:
        decision = "NO_CREDIT_NEEDED"
    elif gap <= 0:
        decision = "NO_CREDIT_NEEDED"          # delay + future income closed it
    elif credit <= 0:
        decision = "CREDIT_DECLINED"           # nothing safe to lend
    elif unfunded > 0:
        decision = "PARTIAL_CREDIT"            # safe credit helps but can't cover it all
    elif credit >= gap and credit >= requested - buffer_available:
        decision = "FULL_CREDIT"
    else:
        decision = "PARTIAL_CREDIT"

    if decision == "CREDIT_DECLINED":
        msg = ("Borrowing this amount isn't safe right now \u2014 repayment would strain "
               "your income. Use your buffer and delay non-urgent expenses instead.")
    elif credit > 0:
        msg = (f"Use \u20b9{buffer_available} buffer + \u20b9{credit} responsible credit. "
               f"Safe repayment \u20b9{safe_repay}/month over 3 months.")
    else:
        msg = "Your buffer and expected income cover this \u2014 no credit needed."

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
            {"source": "delay_expense", "amount": delay, "used": delay > 0},
            {"source": "future_income", "amount": future, "used": future > 0},
            {"source": "credit", "amount": credit, "used": credit > 0},
        ],
        "message": msg,
    }