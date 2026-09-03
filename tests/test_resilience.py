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
    resilience_days, buffer_target, CAP,
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


# ---------------------------------------------------------------- contract shape

def test_evaluate_matches_contract_for_all_personas():
    """Every persona's ResilienceResult validates against the frozen contract."""
    for wid in PERSONAS:
        _, res = _eval(wid)
        ResilienceResult(**res)  # raises if any field/shape is wrong


def test_recommendations_match_contract_for_all_personas():
    for wid in PERSONAS:
        p, res = _eval(wid)
        recs = recommend(p, res, FC[wid])
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
        # recompute the breakdown with the same essential_daily and confirm it matches
        assert resilience_score(p, ess) == res["score_breakdown"]


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
    recs = recommend(p, shock, {**FC["W001"], "weather": "SHOCK"})
    types = {r["type"] for r in recs}
    assert "REDUCE_SPEND" in types
    assert "AVOID_CREDIT" in types


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


def test_credit_is_capped_to_safe_repayment():
    """A large request must not produce credit above safe repayment capacity."""
    p, res = _eval("W004")  # crisis persona, low income
    out = evaluate_credit(p, res, FC["W004"], 50000)
    safe_cap = int(FC["W004"]["next_30_days"] * 0.20) * 3
    assert out["recommended_credit"] <= safe_cap
    assert out["decision"] in ("PARTIAL_CREDIT", "CREDIT_DECLINED")


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