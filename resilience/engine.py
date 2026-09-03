"""Financial Autopilot: convert forecasts and risk into safe spending actions."""
from __future__ import annotations

from constants import (
    BUFFER_TARGET_DAYS, CRITICAL_RESILIENCE_DAYS, GROWTH_ALLOCATION_RATE,
    MIN_RECOMMENDATION_SAVE, RECOMMENDED_SAVE_DAYS, SCORE_CAPS,
    SHOCK_SPEND_FACTOR, TOPUP_RATES,
    MONTH_DAYS, OBLIGATION_INCOME_COVERAGE_RATE, RECOVERY_BUFFER_RATIO,
)
from backend.schemas.contracts import (
    FinancialProfile, ForecastResult, ObligationSummary, Recommendation,
    ResilienceResult, RiskResult,
)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def decide_mode(risk: RiskResult, forecast: ForecastResult, profile: FinancialProfile) -> str:
    if forecast.weather == "SHOCK" or risk.risk_score > 0.8:
        return "SHOCK"
    if forecast.trend == "RISING" and profile.income_trend == "RISING" and risk.risk_level != "HIGH":
        return "RECOVERY" if profile.emergency_buffer < profile.monthly_income_avg * RECOVERY_BUFFER_RATIO else "NORMAL"
    if forecast.weather == "WATCH" or risk.risk_level == "HIGH":
        return "WATCH"
    return "NORMAL"


def resilience_days(buffer_current: int, essential_daily: int) -> int:
    return 0 if essential_daily <= 0 else int(max(0, buffer_current) / essential_daily)


def buffer_target(essential_daily: int, risk_level: str) -> int:
    return essential_daily * BUFFER_TARGET_DAYS.get(risk_level, BUFFER_TARGET_DAYS["MODERATE"])


def compute_spend_plan(profile: FinancialProfile, forecast: ForecastResult,
                       obligations: ObligationSummary, buffer_gap: int, mode: str) -> tuple[int, int, int]:
    """Return ``(safe_daily, discretionary_total, net_obligations)`` for 30 days."""
    net_obligations = max(0, obligations.total_upcoming - int(forecast.next_30_days * OBLIGATION_INCOME_COVERAGE_RATE))
    buffer_topup = max(0, min(buffer_gap, int(profile.current_balance * TOPUP_RATES.get(mode, 0))))
    discretionary = max(0, profile.current_balance - net_obligations - buffer_topup)
    daily = int(discretionary / MONTH_DAYS)
    if mode == "SHOCK":
        daily = int(daily * SHOCK_SPEND_FACTOR)
    return daily, discretionary, net_obligations


def resilience_score(profile: FinancialProfile) -> dict[str, int]:
    income_stability = round(SCORE_CAPS["income_stability"] * (1 - _clamp(profile.monthly_income_std / max(1, profile.monthly_income_avg), 0, 1)))
    essential_daily = max(1, int(profile.fixed_expenses / MONTH_DAYS))
    emergency_buffer = round(SCORE_CAPS["emergency_buffer"] * _clamp(resilience_days(profile.emergency_buffer, essential_daily) / MONTH_DAYS, 0, 1))
    expense_coverage = round(SCORE_CAPS["expense_coverage"] * _clamp(1 - (profile.expense_to_income_ratio - RECOVERY_BUFFER_RATIO), 0, 1))
    debt_burden = round(SCORE_CAPS["debt_burden"] * (1 - _clamp(profile.monthly_emi * 3 / max(1, profile.monthly_income_avg), 0, 1)))
    savings_consistency = round(SCORE_CAPS["savings_consistency"] * _clamp(profile.savings_balance / max(1, profile.monthly_income_avg), 0, 1))
    return {"income_stability": income_stability, "emergency_buffer": emergency_buffer,
            "expense_coverage": expense_coverage, "debt_burden": debt_burden,
            "savings_consistency": savings_consistency}


def evaluate(profile: FinancialProfile, risk: RiskResult, forecast: ForecastResult,
             obligations: ObligationSummary) -> ResilienceResult:
    profile, risk, forecast, obligations = (FinancialProfile.model_validate(profile), RiskResult.model_validate(risk),
                                             ForecastResult.model_validate(forecast), ObligationSummary.model_validate(obligations))
    mode = decide_mode(risk, forecast, profile)
    days = resilience_days(profile.emergency_buffer, obligations.essential_daily_spend)
    target = buffer_target(obligations.essential_daily_spend, risk.risk_level)
    daily, discretionary, net_obligations = compute_spend_plan(profile, forecast, obligations, max(0, target - profile.emergency_buffer), mode)
    breakdown = resilience_score(profile)
    return ResilienceResult(worker_id=profile.worker_id, safe_to_spend_daily=daily,
        resilience_score=sum(breakdown.values()), resilience_days=days, buffer_target=target,
        buffer_current=profile.emergency_buffer, recommended_save=0 if mode == "SHOCK" else int(max(0, target - profile.emergency_buffer) / RECOMMENDED_SAVE_DAYS),
        mode=mode, wallet_allocation={"daily": discretionary, "bills": net_obligations,
        "buffer": profile.emergency_buffer, "growth": 0 if mode in ("SHOCK", "WATCH") else int(profile.current_balance * GROWTH_ALLOCATION_RATE)},
        score_breakdown=breakdown)


def recommend(profile: FinancialProfile, res: ResilienceResult, forecast: ForecastResult) -> list[Recommendation]:
    profile, res, forecast = FinancialProfile.model_validate(profile), ResilienceResult.model_validate(res), ForecastResult.model_validate(forecast)
    recs: list[Recommendation] = []
    if res.resilience_days < CRITICAL_RESILIENCE_DAYS:
        recs.append(Recommendation(type="SAVE", priority="HIGH", amount=300,
            message="Your safety buffer is critically low — prioritise saving",
            reason=f"Only {res.resilience_days} days of cover remaining"))
    if forecast.weather in ("WATCH", "SHOCK"):
        amount = max(MIN_RECOMMENDATION_SAVE, res.recommended_save)
        recs.extend([Recommendation(type="SAVE", priority="HIGH", amount=amount,
            message=f"Move ₹{amount} to your emergency buffer", reason="Income dip predicted in the next 8 days"),
            Recommendation(type="AVOID_CREDIT", priority="HIGH", amount=None,
            message="You don't need a loan right now", reason="Your buffer + expected income can cover the shortfall")])
    else:
        recs.append(Recommendation(type="SAVE", priority="MEDIUM", amount=res.recommended_save,
            message=f"On track — save ₹{res.recommended_save} toward your buffer", reason=f"Income is stable; build toward {BUFFER_TARGET_DAYS['HIGH']} resilience days"))
    return recs
