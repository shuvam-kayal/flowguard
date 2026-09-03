"""
Person 3 — resilience engine + credit guard tests.

These call the REAL engine (no re-implemented maths) and assert both the
behaviour and that every output validates against the frozen Pydantic
contracts. Run:  python tests/test_resilience.py   (or: pytest tests/test_resilience.py)
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)                       # for `resilience` package
sys.path.insert(0, os.path.join(ROOT, "backend"))  # for `schemas`

from resilience.engine import (
    evaluate, recommend, decide_mode, resilience_score,
    resilience_days, buffer_target, days_to_shock, CAP,
)
from resilience.credit_guard import evaluate_credit
from schemas.contracts import ResilienceResult, Recommendation, CreditGuardResult

D = os.path.join(ROOT, "data", "demo")


def _load(name):
    return json.load(open(os.path.join(D, name), encoding="utf-8"))


PERSONAS = {p["worker_id"]: p for p in _load("personas.json")["personas"]}
RISK = _load("sample_risk.json")
FC = _load("sample_forecasts.json")
OBL = _load("sample_obligations.json")


def _eval(wid):
    p = PERSONAS[wid]
    return p, evaluate(p, RISK[wid], FC[wid], OBL[wid])


def _profile(**overrides):
    """A minimal, valid-shaped profile for synthetic edge-case tests, based
    on Ravi (W001) with specific fields overridden."""
    base = dict(PERSONAS["W001"])
    base.update(overrides)
    return base


def _forecast(**overrides):
    base = dict(FC["W001"])
    base.update(overrides)
    return base


def _obligations(**overrides):
    base = dict(OBL["W001"])
    base.update(overrides)
    return base


def _risk(**overrides):
    base = dict(RISK["W001"])
    base.update(overrides)
    return base


# ---------------------------------------------------------------- contract shape

def test_evaluate_matches_contract_for_all_personas():
    """Every persona's ResilienceResult validates against the frozen contract."""
    for wid in PERSONAS:
        _, res = _eval(wid)
        ResilienceResult(**res)  # raises if any field/shape is wrong


def test_recommendations_match_contract_for_all_personas():
    for wid in PERSONAS:
        p, res = _eval(wid)
        recs = recommend(p, res, FC[wid], OBL[wid])
        assert len(recs) >= 1
        for r in recs:
            Recommendation(**r)


# ---------------------------------------------------------------- score

def test_resilience_score_never_exceeds_100():
    for wid in PERSONAS:
        _, res = _eval(wid)
        assert 0 <= res["resilience_score"] <= 100


def test_score_breakdown_sums_to_score():
    """The five components must add up to the reported resilience_score."""
    for wid in PERSONAS:
        _, res = _eval(wid)
        assert sum(res["score_breakdown"].values()) == res["resilience_score"]


def test_score_components_respect_caps():
    for wid in PERSONAS:
        _, res = _eval(wid)
        for k, v in res["score_breakdown"].items():
            assert 0 <= v <= CAP[k], f"{wid} {k}={v} exceeds cap {CAP[k]}"


def test_resilience_days_consistent_with_breakdown_denominator():
    """Bug guard: top-level resilience_days uses the obligation essential_daily,
    and the score breakdown must use the SAME denominator (not fixed_expenses/30)."""
    for wid in PERSONAS:
        p, res = _eval(wid)
        ess = OBL[wid]["essential_daily_spend"]
        assert res["resilience_days"] == resilience_days(p["emergency_buffer"], ess)
        assert resilience_score(p, ess) == res["score_breakdown"]


def test_debt_burden_uses_threshold_not_arbitrary_multiplier():
    """A worker with EMI at exactly the 30% safe-threshold scores zero on
    debt_burden; well below it scores near the cap."""
    p_high_debt = _profile(monthly_emi=6000, monthly_income_avg=20000)   # 30% ratio
    p_low_debt = _profile(monthly_emi=200, monthly_income_avg=20000)     # 1% ratio
    high = resilience_score(p_high_debt, 400)
    low = resilience_score(p_low_debt, 400)
    assert high["debt_burden"] == 0
    assert low["debt_burden"] > high["debt_burden"]
    assert low["debt_burden"] >= CAP["debt_burden"] - 1  # near-full cap


def test_savings_and_buffer_score_use_days_coverage_curve():
    """Both components should reward more days of coverage, front-loaded:
    the jump from 0->7 days should score higher than an equal-sized jump
    from 21->28 days."""
    ess = 400
    p_0d = _profile(emergency_buffer=0, savings_balance=0)
    p_7d = _profile(emergency_buffer=ess * 7, savings_balance=ess * 7)
    p_21d = _profile(emergency_buffer=ess * 21, savings_balance=ess * 21)
    p_28d = _profile(emergency_buffer=ess * 28, savings_balance=ess * 28)

    s0 = resilience_score(p_0d, ess)
    s7 = resilience_score(p_7d, ess)
    s21 = resilience_score(p_21d, ess)
    s28 = resilience_score(p_28d, ess)

    gain_0_to_7 = s7["emergency_buffer"] - s0["emergency_buffer"]
    gain_21_to_28 = s28["emergency_buffer"] - s21["emergency_buffer"]
    assert gain_0_to_7 > gain_21_to_28 > 0


# ---------------------------------------------------------------- buffer

def test_buffer_calculation_target_by_risk():
    """Higher risk demands more days of buffer target."""
    ess = 400
    assert buffer_target(ess, "HIGH") == ess * 30
    assert buffer_target(ess, "MODERATE") == ess * 21
    assert buffer_target(ess, "LOW") == ess * 14
    assert buffer_target(ess, "HIGH") > buffer_target(ess, "LOW")


def test_buffer_target_present_and_non_negative_gap():
    for wid in PERSONAS:
        _, res = _eval(wid)
        assert res["buffer_target"] >= 0
        assert res["buffer_current"] == PERSONAS[wid]["emergency_buffer"]


# ---------------------------------------------------------------- safe-to-spend

def test_safe_to_spend_non_negative():
    for wid in PERSONAS:
        _, res = _eval(wid)
        assert res["safe_to_spend_daily"] >= 0


def test_safe_to_spend_uses_conservative_lower_bound_not_average():
    """A wide forecast band (low lower_bound, high next_30_days) should pull
    safe-to-spend toward the pessimistic case, not the average."""
    p = PERSONAS["W001"]
    optimistic_avg_fc = _forecast(lower_bound=20000, next_30_days=20000)
    pessimistic_band_fc = _forecast(lower_bound=2000, next_30_days=20000)
    risk = _risk(risk_score=0.3, risk_level="MODERATE")
    obl = OBL["W001"]

    a = evaluate(p, risk, optimistic_avg_fc, obl)
    b = evaluate(p, risk, pessimistic_band_fc, obl)
    assert b["safe_to_spend_daily"] < a["safe_to_spend_daily"]


def test_income_shock_mode_tightens_safe_to_spend():
    """SHOCK must cut safe-to-spend vs. an otherwise-identical calm forecast."""
    p = PERSONAS["W001"]
    calm_fc = {**FC["W001"], "weather": "STABLE", "trend": "STABLE"}
    calm_risk = {**RISK["W001"], "risk_score": 0.2, "risk_level": "LOW"}
    shock_fc = {**FC["W001"], "weather": "SHOCK"}
    shock_risk = {**RISK["W001"], "risk_score": 0.9, "risk_level": "HIGH"}

    calm = evaluate(p, calm_risk, calm_fc, OBL["W001"])
    shock = evaluate(p, shock_risk, shock_fc, OBL["W001"])

    assert calm["mode"] == "NORMAL"
    assert shock["mode"] == "SHOCK"
    assert shock["safe_to_spend_daily"] < calm["safe_to_spend_daily"]


def test_shock_mode_pauses_growth_and_recommends_protection():
    p = PERSONAS["W001"]
    shock = evaluate(p, {**RISK["W001"], "risk_score": 0.9},
                     {**FC["W001"], "weather": "SHOCK"}, OBL["W001"])
    assert shock["wallet_allocation"]["growth"] == 0
    recs = recommend(p, shock, {**FC["W001"], "weather": "SHOCK"}, OBL["W001"])
    types = {r["type"] for r in recs}
    assert "REDUCE_SPEND" in types
    assert "AVOID_CREDIT" in types


# ---------------------------------------------------------------- days_to_shock

def test_days_to_shock_reads_real_forecast_not_hardcoded():
    """days_to_shock must find the actual first dip day, not return a fixed
    number regardless of input."""
    ess = 400
    daily_fc = [{"date": f"day{i}", "expected": 600, "lower": 400, "upper": 800} for i in range(5)]
    daily_fc += [{"date": f"day{i}", "expected": 200, "lower": 100, "upper": 300} for i in range(5, 10)]
    fc = _forecast(daily_forecast=daily_fc)
    assert days_to_shock(fc, ess) == 5  # first day expected (200) < essential (400)


def test_days_to_shock_returns_none_when_no_dip():
    ess = 400
    daily_fc = [{"date": f"day{i}", "expected": 900, "lower": 700, "upper": 1100} for i in range(10)]
    fc = _forecast(daily_forecast=daily_fc)
    assert days_to_shock(fc, ess) is None


def test_recommendation_reason_reflects_real_days_not_fixed_text():
    """The WATCH-mode SAVE recommendation's reason must not always say '8 days'."""
    p = PERSONAS["W001"]
    ess = OBL["W001"]["essential_daily_spend"]
    daily_fc = [{"date": f"day{i}", "expected": 900, "lower": 700, "upper": 1100} for i in range(3)]
    daily_fc += [{"date": f"day{i}", "expected": 100, "lower": 0, "upper": 200} for i in range(3, 10)]
    fc = _forecast(daily_forecast=daily_fc, weather="WATCH")
    risk = _risk(risk_score=0.5, risk_level="MODERATE")
    res = evaluate(p, risk, fc, OBL["W001"])
    recs = recommend(p, res, fc, OBL["W001"])
    reasons = " ".join(r["reason"] for r in recs)
    assert "8 days" not in reasons
    assert "3 days" in reasons  # matches the synthetic dip we constructed


# ---------------------------------------------------------------- mode machine

def test_decide_mode_states():
    p = PERSONAS["W001"]
    assert decide_mode({"risk_score": 0.9, "risk_level": "HIGH"},
                       {"weather": "SHOCK", "trend": "DECLINING"}, p) == "SHOCK"
    assert decide_mode({"risk_score": 0.5, "risk_level": "MODERATE"},
                       {"weather": "WATCH", "trend": "DECLINING"}, p) == "WATCH"
    assert decide_mode({"risk_score": 0.2, "risk_level": "LOW"},
                       {"weather": "STABLE", "trend": "STABLE"}, p) == "NORMAL"


def test_recovery_is_forecast_driven():
    """RECOVERY should fire from a RISING forecast even if the profile is thin,
    and does not depend on the persona's own income_trend field."""
    p = {**PERSONAS["W001"], "income_trend": "DECLINING",
         "emergency_buffer": 500, "monthly_income_avg": 20000}
    mode = decide_mode({"risk_score": 0.3, "risk_level": "MODERATE"},
                       {"weather": "STABLE", "trend": "RISING"}, p)
    assert mode == "RECOVERY"


def test_full_shock_to_recovery_to_normal_transition():
    """The exact arc the live demo relies on: SHOCK -> RECOVERY -> NORMAL as
    forecast and risk improve in sequence, buffer rebuilding along the way."""
    p = _profile(emergency_buffer=500, monthly_income_avg=20000)
    obl = OBL["W001"]

    shock = evaluate(p, _risk(risk_score=0.9, risk_level="HIGH"),
                     _forecast(weather="SHOCK", trend="DECLINING"), obl)
    assert shock["mode"] == "SHOCK"

    recovering = evaluate(p, _risk(risk_score=0.3, risk_level="MODERATE"),
                          _forecast(weather="STABLE", trend="RISING"), obl)
    assert recovering["mode"] == "RECOVERY"

    p_rebuilt = _profile(emergency_buffer=20000, monthly_income_avg=20000)  # buffer now well above 30%
    normal = evaluate(p_rebuilt, _risk(risk_score=0.2, risk_level="LOW"),
                      _forecast(weather="STABLE", trend="RISING"), obl)
    assert normal["mode"] == "NORMAL"


# ---------------------------------------------------------------- edge cases (numeric safety)

def test_zero_income_does_not_crash_or_go_negative():
    p = _profile(monthly_income_avg=0, monthly_income_std=0, current_balance=0,
                 emergency_buffer=0, savings_balance=0, fixed_expenses=0,
                 expense_to_income_ratio=1.0, monthly_emi=0)
    obl = _obligations(total_upcoming=0, essential_daily_spend=1)
    fc = _forecast(lower_bound=0, next_30_days=0)
    risk = _risk(risk_score=0.5, risk_level="MODERATE")
    res = evaluate(p, risk, fc, obl)
    ResilienceResult(**res)
    assert res["safe_to_spend_daily"] >= 0
    assert res["resilience_score"] >= 0


def test_zero_essential_expense_does_not_divide_by_zero():
    obl = _obligations(essential_daily_spend=0, total_upcoming=0)
    p = PERSONAS["W001"]
    res = evaluate(p, RISK["W001"], FC["W001"], obl)
    ResilienceResult(**res)  # resilience_days() guards essential_daily<=0 -> 0
    assert res["resilience_days"] == 0


def test_no_buffer_still_produces_valid_result():
    p = _profile(emergency_buffer=0)
    res = evaluate(p, RISK["W001"], FC["W001"], OBL["W001"])
    ResilienceResult(**res)
    assert res["buffer_current"] == 0
    assert res["resilience_days"] == 0


def test_huge_obligation_crushes_safe_to_spend_but_stays_non_negative():
    obl = _obligations(total_upcoming=10_000_000)
    p = PERSONAS["W001"]
    res = evaluate(p, RISK["W001"], FC["W001"], obl)
    assert res["safe_to_spend_daily"] == 0  # crushed, not negative
    assert res["wallet_allocation"]["daily"] >= 0


def test_huge_savings_does_not_create_unbounded_safe_to_spend():
    """Safe-to-spend is bounded by cash + conservative income minus
    obligations/buffer \u2014 a giant savings_balance (which isn't current_balance)
    must not blow it up."""
    p = _profile(savings_balance=100_000_000, current_balance=11200)
    res = evaluate(p, RISK["W001"], FC["W001"], OBL["W001"])
    # daily is bounded by current_balance + lower_bound, independent of savings_balance
    reasonable_ceiling = int((p["current_balance"] + FC["W001"]["lower_bound"]) / 30) + 1
    assert res["safe_to_spend_daily"] <= reasonable_ceiling


def test_forecast_lower_bound_much_smaller_makes_engine_conservative():
    p = PERSONAS["W001"]
    obl = OBL["W001"]
    risk = _risk(risk_score=0.3, risk_level="MODERATE")
    tight_band = _forecast(lower_bound=FC["W001"]["next_30_days"], weather="STABLE", trend="STABLE")
    wide_band = _forecast(lower_bound=100, weather="STABLE", trend="STABLE")
    tight = evaluate(p, risk, tight_band, obl)
    wide = evaluate(p, risk, wide_band, obl)
    assert wide["safe_to_spend_daily"] <= tight["safe_to_spend_daily"]


# ---------------------------------------------------------------- credit guard

def test_credit_recommendation_matches_contract():
    p, res = _eval("W001")
    out = evaluate_credit(p, res, FC["W001"], 5000)
    CreditGuardResult(**out)


def test_credit_waterfall_order_and_no_credit_when_buffer_covers():
    p, res = _eval("W001")
    small = evaluate_credit(p, res, FC["W001"], max(1, res["buffer_current"] - 1))
    assert small["decision"] == "NO_CREDIT_NEEDED"
    assert small["recommended_credit"] == 0
    order = [s["source"] for s in small["waterfall"]]
    assert order == ["savings", "emergency_buffer", "delay_expense", "future_income", "credit"]


def test_credit_is_capped_to_safe_discretionary_surplus():
    """A massive request must not produce credit above what the worker's own
    safe_to_spend_daily (obligations/buffer already netted out exactly once)
    can support, and should decline or partial-fund rather than fully approve."""
    p, res = _eval("W004")  # crisis persona, low income
    out = evaluate_credit(p, res, FC["W004"], 50000)
    monthly_discretionary = res["safe_to_spend_daily"] * 30
    safe_cap = int(monthly_discretionary * 0.20) * 3
    assert out["recommended_credit"] <= safe_cap
    assert out["decision"] in ("PARTIAL_CREDIT", "CREDIT_DECLINED")


def test_credit_request_smaller_than_buffer_needs_no_credit():
    p, res = _eval("W001")
    tiny_request = max(1, res["buffer_current"] // 2)
    out = evaluate_credit(p, res, FC["W001"], tiny_request)
    assert out["decision"] == "NO_CREDIT_NEEDED"


def test_credit_massively_unaffordable_is_declined():
    """When safe_to_spend_daily is 0 (no safe discretionary surplus to lend
    against) and the request is huge, Credit Guard must decline rather than
    lend, no matter how large the number requested is."""
    p = _profile(emergency_buffer=0)
    res_no_surplus = {**_eval("W001")[1], "buffer_current": 0, "safe_to_spend_daily": 0}
    starved_fc = _forecast(lower_bound=100, next_30_days=100)
    out = evaluate_credit(p, res_no_surplus, starved_fc, 1_000_000)
    assert out["decision"] == "CREDIT_DECLINED"
    assert out["recommended_credit"] == 0


# ---------------------------------------------------------------- runner

def _run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        t()
        print(f"  PASS {t.__name__}")
        passed += 1
    print(f"\n{passed}/{len(tests)} resilience tests passed \u2713")


if __name__ == "__main__":
    _run_all()