"""
Generate consistent mock JSON for every module, for all 5 personas.
Run:  python data/demo/generate_mocks.py
Produces the sample_*.json files each teammate uses as a stand-in
for other people's modules on day 1.

These are DETERMINISTIC hand-tuned mocks (not the real models) so the
numbers tell a coherent story across risk / forecast / resilience.
"""
import json
import os
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "personas.json")) as f:
    PERSONAS = json.load(f)["personas"]

START = date(2026, 9, 4)


def risk_for(p):
    # Hand-tuned so levels match persona expectations.
    table = {
        "W001": (0.72, "HIGH", 0.86, [
            ("income_volatility", 0.24, "increases_risk"),
            ("low_savings", 0.19, "increases_risk"),
            ("upcoming_emi", 0.11, "increases_risk"),
            ("expense_to_income_ratio", 0.14, "increases_risk"),
        ]),
        "W002": (0.21, "LOW", 0.90, [
            ("emergency_buffer", 0.28, "decreases_risk"),
            ("income_stability", 0.22, "decreases_risk"),
            ("high_emi", 0.12, "increases_risk"),
        ]),
        "W003": (0.48, "MODERATE", 0.79, [
            ("income_volatility", 0.31, "increases_risk"),
            ("large_buffer", 0.25, "decreases_risk"),
            ("no_debt", 0.10, "decreases_risk"),
        ]),
        "W004": (0.88, "HIGH", 0.91, [
            ("expense_to_income_ratio", 0.30, "increases_risk"),
            ("near_zero_buffer", 0.27, "increases_risk"),
            ("dependents", 0.15, "increases_risk"),
        ]),
        "W005": (0.44, "MODERATE", 0.82, [
            ("rising_income", 0.20, "decreases_risk"),
            ("thin_buffer", 0.18, "increases_risk"),
            ("moderate_debt", 0.12, "increases_risk"),
        ]),
    }
    score, level, conf, factors = table[p["worker_id"]]
    return {
        "worker_id": p["worker_id"],
        "risk_score": score,
        "risk_level": level,
        "confidence": conf,
        "top_factors": [
            {"feature": f, "impact": i, "direction": d} for f, i, d in factors
        ],
    }


def forecast_for(p):
    table = {
        "W001": (0.63, "WATCH", "DECLINING"),
        "W002": (0.20, "STABLE", "STABLE"),
        "W003": (0.55, "WATCH", "RISING"),
        "W004": (0.71, "SHOCK", "STABLE"),
        "W005": (0.30, "STABLE", "RISING"),
    }
    shock, weather, trend = table[p["worker_id"]]
    monthly = p["monthly_income_avg"]
    std = p["monthly_income_std"]
    # 30-day expected ~ monthly, adjusted slightly by trend
    trend_mult = {"RISING": 1.06, "STABLE": 1.0, "DECLINING": 0.90}[trend]
    n30 = int(monthly * trend_mult)
    n7 = int(n30 / 30 * 7)
    lower = int(n30 - std * 0.6)
    upper = int(n30 + std * 0.6)

    daily = []
    base = n30 / 30.0
    # weekday pattern: weekends higher for delivery/ride, dip midweek
    weekday_mult = [0.85, 0.9, 1.0, 1.05, 1.15, 1.25, 1.1]  # Mon..Sun
    for i in range(30):
        d = START + timedelta(days=i)
        m = weekday_mult[d.weekday()]
        # inject a dip window for WATCH/SHOCK personas around days 7-16
        dip = 1.0
        if weather in ("WATCH", "SHOCK") and 7 <= i <= 16:
            dip = 0.7 if weather == "SHOCK" else 0.8
        exp = int(base * m * dip)
        band = int(exp * 0.35)
        daily.append({
            "date": d.isoformat(),
            "expected": exp,
            "lower": max(0, exp - band),
            "upper": exp + band,
        })

    return {
        "worker_id": p["worker_id"],
        "next_7_days": n7,
        "next_30_days": n30,
        "lower_bound": lower,
        "upper_bound": upper,
        "trend": trend,
        "shock_probability": shock,
        "weather": weather,
        "daily_forecast": daily,
    }


def obligations_for(p):
    obs = [
        {"name": "Rent", "amount": int(p["fixed_expenses"] * 0.6),
         "due_date": (START + timedelta(days=11)).isoformat(), "category": "FIXED"},
    ]
    if p["monthly_emi"] > 0:
        obs.append({"name": "EMI", "amount": p["monthly_emi"],
                    "due_date": (START + timedelta(days=6)).isoformat(), "category": "DEBT"})
    obs.append({"name": "Electricity", "amount": 1200,
                "due_date": (START + timedelta(days=8)).isoformat(), "category": "UTILITY"})
    total = sum(o["amount"] for o in obs)
    essential_daily = int(p["fixed_expenses"] / 30) + int(p["variable_expenses"] * 0.5 / 30)
    return {
        "worker_id": p["worker_id"],
        "upcoming_obligations": obs,
        "total_upcoming": total,
        "essential_daily_spend": max(1, essential_daily),
    }


def resilience_for(p, risk, forecast, obl):
    mode_table = {
        "W001": "WATCH", "W002": "NORMAL", "W003": "WATCH",
        "W004": "SHOCK", "W005": "RECOVERY",
    }
    mode = mode_table[p["worker_id"]]

    essential_daily = obl["essential_daily_spend"]
    buffer_current = p["emergency_buffer"]
    resilience_days = int(buffer_current / essential_daily) if essential_daily else 0

    # buffer target = ~14 days of essentials in normal, more when risky
    target_days = 30 if risk["risk_level"] == "HIGH" else 20
    buffer_target = essential_daily * target_days

    # safe-to-spend: (balance - obligations due before next payout - small buffer top-up) / days
    # Only reserve obligations due in the NEXT 30 days that aren't covered by incoming forecast,
    # plus a gentle buffer contribution (not the whole gap at once).
    days_left = 30
    incoming = forecast["next_30_days"]
    net_obligations = max(0, obl["total_upcoming"] - incoming * 0.5)  # forecast income helps cover bills
    buffer_topup = max(0, min(buffer_target - buffer_current, p["current_balance"] * 0.08))
    reserve = net_obligations + buffer_topup
    discretionary = max(0, p["current_balance"] - reserve)
    safe_daily = int(discretionary / days_left)

    # score components (caps: 25,25,20,15,15)
    inc_stab = round(25 * (1 - min(1, p["monthly_income_std"] / max(1, p["monthly_income_avg"]))))
    buf = round(25 * min(1, resilience_days / 30))
    exp_cov = round(20 * min(1, 1 - min(1, p["expense_to_income_ratio"] - 0.3)))
    debt = round(15 * (1 - min(1, p["monthly_emi"] / max(1, p["monthly_income_avg"]) * 3)))
    sav = round(15 * min(1, p["savings_balance"] / max(1, p["monthly_income_avg"])))
    exp_cov = max(0, exp_cov)
    debt = max(0, debt)
    score = inc_stab + buf + exp_cov + debt + sav

    recommended_save = 0 if mode == "SHOCK" else int(max(0, (buffer_target - buffer_current) / 20))

    return {
        "worker_id": p["worker_id"],
        "safe_to_spend_daily": safe_daily,
        "resilience_score": int(score),
        "resilience_days": resilience_days,
        "buffer_target": int(buffer_target),
        "buffer_current": buffer_current,
        "recommended_save": recommended_save,
        "mode": mode,
        "wallet_allocation": {
            "daily": int(discretionary),
            "bills": obl["total_upcoming"],
            "buffer": buffer_current,
            "growth": 0 if mode in ("SHOCK", "WATCH") else int(p["current_balance"] * 0.05),
        },
        "score_breakdown": {
            "income_stability": inc_stab,
            "emergency_buffer": buf,
            "expense_coverage": exp_cov,
            "debt_burden": debt,
            "savings_consistency": sav,
        },
    }


def recommendations_for(p, res, forecast):
    recs = []
    if forecast["weather"] in ("WATCH", "SHOCK"):
        recs.append({
            "type": "SAVE", "priority": "HIGH", "amount": max(200, res["recommended_save"]),
            "message": f"Move \u20b9{max(200, res['recommended_save'])} to your emergency buffer",
            "reason": "Income dip predicted in the next 8 days",
        })
        recs.append({
            "type": "REDUCE_SPEND", "priority": "MEDIUM", "amount": None,
            "message": "Trim discretionary spending this week",
            "reason": f"Forecast trend is {forecast['trend'].lower()}",
        })
        recs.append({
            "type": "AVOID_CREDIT", "priority": "HIGH", "amount": None,
            "message": "You don't need a loan right now",
            "reason": "Your buffer + expected income can cover the shortfall",
        })
    else:
        recs.append({
            "type": "SAVE", "priority": "MEDIUM", "amount": res["recommended_save"],
            "message": f"On track \u2014 save \u20b9{res['recommended_save']} toward your buffer",
            "reason": "Income is stable; build toward 30 resilience days",
        })
    if res["resilience_days"] < 7:
        recs.insert(0, {
            "type": "SAVE", "priority": "HIGH", "amount": 300,
            "message": "Your safety buffer is critically low \u2014 prioritise saving",
            "reason": f"Only {res['resilience_days']} days of cover remaining",
        })
    return recs


def credit_for(p, res):
    requested = 5000
    buffer_available = res["buffer_current"]
    shortfall = max(0, requested - buffer_available)
    future = min(shortfall, int(p["monthly_income_avg"] * 0.1))
    credit = max(0, shortfall - future)
    safe_repay = int(credit * 0.25)
    if requested <= buffer_available:
        decision = "NO_CREDIT_NEEDED"
    elif credit <= 0:
        decision = "NO_CREDIT_NEEDED"
    else:
        decision = "PARTIAL_CREDIT"
    return {
        "worker_id": p["worker_id"],
        "requested_amount": requested,
        "buffer_available": buffer_available,
        "expected_shortfall": shortfall,
        "recommended_credit": credit,
        "safe_monthly_repayment": safe_repay,
        "decision": decision,
        "waterfall": [
            {"source": "savings", "amount": 0, "used": False},
            {"source": "emergency_buffer", "amount": buffer_available, "used": buffer_available > 0},
            {"source": "delay_expense", "amount": 0, "used": False},
            {"source": "future_income", "amount": future, "used": future > 0},
            {"source": "credit", "amount": credit, "used": credit > 0},
        ],
        "message": (f"Use \u20b9{buffer_available} buffer + \u20b9{credit} responsible credit. "
                    f"Safe repayment \u20b9{safe_repay}/month.") if credit > 0
                   else "Your buffer covers this \u2014 no credit needed.",
    }


def build_all():
    risks, forecasts, obligations, resiliences, dashboards, credits = {}, {}, {}, {}, {}, {}
    for p in PERSONAS:
        wid = p["worker_id"]
        r = risk_for(p)
        f = forecast_for(p)
        o = obligations_for(p)
        res = resilience_for(p, r, f, o)
        recs = recommendations_for(p, res, f)
        cr = credit_for(p, res)
        risks[wid] = r
        forecasts[wid] = f
        obligations[wid] = o
        resiliences[wid] = res
        credits[wid] = cr
        dashboards[wid] = {
            "worker": {
                "worker_id": wid, "name": p["name"],
                "occupation": p["occupation"], "current_balance": p["current_balance"],
            },
            "risk": r, "forecast": f, "resilience": res,
            "obligations": o, "recommendations": recs,
        }
    return risks, forecasts, obligations, resiliences, dashboards, credits


def main():
    risks, forecasts, obligations, resiliences, dashboards, credits = build_all()
    out = {
        "sample_risk.json": risks,
        "sample_forecasts.json": forecasts,
        "sample_obligations.json": obligations,
        "sample_resilience.json": resiliences,
        "sample_dashboards.json": dashboards,
        "sample_credit.json": credits,
    }
    for fname, data in out.items():
        path = os.path.join(HERE, fname)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        print(f"wrote {fname}  ({len(data)} personas)")


if __name__ == "__main__":
    main()
