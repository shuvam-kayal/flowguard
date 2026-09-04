"""
Person 3 — Credit Guard. The waterfall: savings -> buffer -> delay -> future income -> credit.
Real skeleton, contract-shaped output (CreditGuardResult, #7).
"""
try:
    from resilience.utils import get_value
except ModuleNotFoundError:  # Support direct execution from the resilience folder
    from utils import get_value

def evaluate_credit(profile, resilience, forecast, requested: int) -> dict:
    """Credit Guard waterfall: savings -> buffer -> delay expense -> future income -> credit.

    Credit is the LAST resort, capped at what the worker can safely repay out
    of money they ALREADY have safely free to spend \u2014 not a flat share of
    gross income, and not a second, independent essentials/obligations
    subtraction (that double-counts: `essential_daily_spend` already
    represents ~full monthly essential cost, and rent/EMI/utilities in
    `total_upcoming` are already part of that figure).

    Instead we anchor to `resilience["safe_to_spend_daily"]`, the engine's
    own conservative-liquidity number: essentials, mandatory obligations,
    and buffer protection are already netted out of it exactly once. Safe
    repayment is a fraction of that already-safe monthly surplus, so
    repayment can never eat into essentials or the buffer by construction.
    """
    requested = max(0, int(requested))
    savings = 0  # keep long-term savings untouched by default
    buffer_available = get_value(resilience, "buffer_current", 0)
    safe_to_spend_daily = get_value(resilience, "safe_to_spend_daily", 0)
    next_30_days = get_value(forecast, "next_30_days", 0)
    worker_id = get_value(profile, "worker_id", "")

    # 1) savings + buffer
    remaining = max(0, requested - savings - buffer_available)

    # 2) delay expense: a portion of the gap can be deferred rather than funded now
    #    (bounded, so it never magically erases the whole need)
    delay = min(remaining, int(requested * 0.15))
    remaining_after_delay = remaining - delay

    # 3) a slice of expected income can absorb part of the remaining need
    future = min(remaining_after_delay, int(next_30_days * 0.10))
    gap = max(0, remaining_after_delay - future)

    # 4) credit is the last resort, capped at what's safely repayable out of
    #    the worker's own already-conservative monthly discretionary surplus.
    monthly_discretionary = safe_to_spend_daily * 30
    safe_repay = max(0, int(monthly_discretionary * 0.20))  # 20% of already-safe surplus
    repayment_months = 3
    max_safe_credit = safe_repay * repayment_months

    credit = min(gap, max_safe_credit)
    safe_repay = int(credit / repayment_months) if credit > 0 else 0
    unfunded = gap - credit  # gap credit still cannot safely cover

    if requested <= savings + buffer_available:
        decision = "NO_CREDIT_NEEDED"
    elif gap <= 0:
        decision = "NO_CREDIT_NEEDED"          # delay + future income closed it
    elif credit <= 0:
        decision = "CREDIT_DECLINED"           # no safe discretionary surplus to lend against
    elif unfunded > 0:
        decision = "PARTIAL_CREDIT"            # safe credit helps but can't cover it all
    elif credit >= gap and credit >= requested - buffer_available:
        decision = "FULL_CREDIT"
    else:
        decision = "PARTIAL_CREDIT"

    if decision == "CREDIT_DECLINED":
        msg = ("Borrowing this amount isn't safe right now \u2014 your safe discretionary "
               "surplus can't cover repayment without cutting into essentials or your "
               "buffer. Use your buffer and delay non-urgent expenses instead.")
    elif credit > 0:
        msg = (f"Use \u20b9{buffer_available} buffer + \u20b9{credit} responsible credit. "
               f"Safe repayment \u20b9{safe_repay}/month over {repayment_months} months, "
               f"capped by your safe discretionary surplus.")
    else:
        msg = "Your buffer and expected income cover this \u2014 no credit needed."

    return {
        "worker_id": worker_id,
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
