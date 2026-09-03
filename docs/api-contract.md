# FlowGuard — Frozen API Contracts

> **This file is FROZEN. Do not change any field name or type without a team-wide agreement.**
> Every module builds against these shapes. Mocks match these exactly.
> If you need a new field, add it as *optional* and announce it — never rename or remove.

Currency amounts are integers in **rupees** (no paise, no decimals) unless noted.
Dates are ISO strings `YYYY-MM-DD`. Timestamps are ISO 8601.

---

## 0. The core flow

```
FinancialProfile ──┬──> RiskResult      (Person 1, /ml/risk)
                   ├──> ForecastResult  (Person 2, /forecast/income)
                   └──> ObligationSummary (Person 4, derived from transactions)
                              │
        RiskResult + ForecastResult + ObligationSummary + FinancialProfile
                              │
                              ▼
                        ResilienceResult (Person 3, /resilience/evaluate)
                              │
                              ▼
                        Recommendation[] (Person 3)
                              │
                              ▼
                  DashboardResponse (Person 4, GET /worker/{id}/dashboard)
                              │
                              ▼
                        Frontend (Person 5)
```

---

## 1. FinancialProfile  (input to everything — Person 4 produces it)

Normalized snapshot of one worker. Person 4 builds this from raw transactions.
Persons 1, 2, 3 consume it.

```json
{
  "worker_id": "W001",
  "name": "Ravi Kumar",
  "occupation": "Food Delivery Partner",
  "current_balance": 11200,
  "monthly_income_avg": 24000,
  "monthly_income_std": 6800,
  "income_trend": "DECLINING",
  "total_monthly_expenses": 18500,
  "fixed_expenses": 11000,
  "variable_expenses": 7500,
  "savings_balance": 5400,
  "emergency_buffer": 2000,
  "total_debt": 8000,
  "monthly_emi": 2000,
  "dependents": 3,
  "avg_work_hours_per_week": 52,
  "active_platforms": ["Zomato", "Swiggy"],
  "expense_to_income_ratio": 0.77
}
```

Field notes:
- `income_trend`: one of `"RISING" | "STABLE" | "DECLINING"`.
- `monthly_income_std`: standard deviation of monthly income = the volatility signal.
- All amounts integers, rupees.

---

## 2. RiskResult  (Person 1 — `POST /ml/risk`)

```json
{
  "worker_id": "W001",
  "risk_score": 0.72,
  "risk_level": "HIGH",
  "confidence": 0.86,
  "top_factors": [
    { "feature": "income_volatility", "impact": 0.24, "direction": "increases_risk" },
    { "feature": "low_savings",       "impact": 0.19, "direction": "increases_risk" },
    { "feature": "upcoming_emi",      "impact": 0.11, "direction": "increases_risk" }
  ]
}
```

Field notes:
- `risk_score`: float `0.0`–`1.0`. Higher = more distress-likely.
- `risk_level`: `"LOW" | "MODERATE" | "HIGH"`. Thresholds: LOW `<0.34`, MODERATE `0.34–0.66`, HIGH `>0.66`.
- `confidence`: float `0.0`–`1.0`.
- `top_factors`: 2–5 items, sorted by `impact` descending. `impact` is a float (SHAP value or deterministic contribution). `direction`: `"increases_risk" | "decreases_risk"`.

---

## 3. ForecastResult  (Person 2 — `POST /forecast/income`)

```json
{
  "worker_id": "W001",
  "next_7_days": 4200,
  "next_30_days": 18200,
  "lower_bound": 14500,
  "upper_bound": 22600,
  "trend": "DECLINING",
  "shock_probability": 0.63,
  "weather": "WATCH",
  "daily_forecast": [
    { "date": "2026-09-04", "expected": 620, "lower": 400, "upper": 880 },
    { "date": "2026-09-05", "expected": 610, "lower": 380, "upper": 870 }
  ]
}
```

Field notes:
- `next_7_days`, `next_30_days`: expected total income (rupees) over those windows.
- `lower_bound` / `upper_bound`: bounds on `next_30_days` (worst/best case).
- `trend`: `"RISING" | "STABLE" | "DECLINING"`.
- `shock_probability`: float `0.0`–`1.0` — probability of a significant income dip in the window.
- `weather`: `"STABLE" | "WATCH" | "SHOCK"` — the Financial Weather status.
  Mapping guide: `STABLE` if shock_prob `<0.35`, `WATCH` if `0.35–0.65`, `SHOCK` if `>0.65`.
- `daily_forecast`: array of ~30 points for the chart. Frontend plots `expected` with a `lower`–`upper` band.

---

## 4. ObligationSummary  (Person 4 — derived, part of the profile bundle)

Upcoming committed outflows the resilience engine must reserve for.

```json
{
  "worker_id": "W001",
  "upcoming_obligations": [
    { "name": "Rent",        "amount": 8000, "due_date": "2026-09-15", "category": "FIXED" },
    { "name": "EMI",         "amount": 2000, "due_date": "2026-09-10", "category": "DEBT"  },
    { "name": "Electricity", "amount": 1200, "due_date": "2026-09-12", "category": "UTILITY" }
  ],
  "total_upcoming": 11200,
  "essential_daily_spend": 320
}
```

Field notes:
- `category`: `"FIXED" | "DEBT" | "UTILITY" | "OTHER"`.
- `essential_daily_spend`: rupees/day the worker needs for essentials — the denominator for resilience-days.

---

## 5. ResilienceResult  (Person 3 — `POST /resilience/evaluate`)

The heart of the product. Consumes profile + risk + forecast + obligations.

```json
{
  "worker_id": "W001",
  "safe_to_spend_daily": 400,
  "resilience_score": 68,
  "resilience_days": 17,
  "buffer_target": 6000,
  "buffer_current": 2000,
  "recommended_save": 300,
  "mode": "WATCH",
  "wallet_allocation": {
    "daily": 3200,
    "bills": 6000,
    "buffer": 2000,
    "growth": 0
  },
  "score_breakdown": {
    "income_stability": 14,
    "emergency_buffer": 12,
    "expense_coverage": 15,
    "debt_burden": 10,
    "savings_consistency": 17
  }
}
```

Field notes:
- `safe_to_spend_daily`: THE hero number. Rupees/day.
- `resilience_score`: int `0`–`100`.
- `resilience_days`: int — how many days the buffer covers essentials = `buffer_current / essential_daily_spend`.
- `mode`: `"NORMAL" | "WATCH" | "SHOCK" | "RECOVERY"` — the Income Shock Mode state machine.
- `wallet_allocation`: the 4 buckets, must sum to a sensible allocation of available funds.
- `score_breakdown`: components summing to `resilience_score`. Max per component: income_stability 25, emergency_buffer 25, expense_coverage 20, debt_burden 15, savings_consistency 15 (total 100).

---

## 6. Recommendation  (Person 3 — array, part of dashboard)

```json
{
  "type": "SAVE",
  "priority": "HIGH",
  "amount": 300,
  "message": "Move ₹300 to your emergency buffer",
  "reason": "Income dip predicted in 8 days"
}
```

Field notes:
- `type`: `"SAVE" | "REDUCE_SPEND" | "RESERVE_BILL" | "AVOID_CREDIT" | "USE_BUFFER" | "TAKE_CREDIT"`.
- `priority`: `"LOW" | "MEDIUM" | "HIGH"`.
- `amount`: rupees, or `null` if not money-specific.
- `message`: user-facing, imperative, one line.
- `reason`: short explanation for the "why" (drives explainability in UI).

---

## 7. CreditGuardResult  (Person 3 — `POST /credit/evaluate`)

Powers the Credit Guard screen. Input: requested amount + current state.

```json
{
  "worker_id": "W001",
  "requested_amount": 5000,
  "buffer_available": 2100,
  "expected_shortfall": 3200,
  "recommended_credit": 1100,
  "safe_monthly_repayment": 280,
  "decision": "PARTIAL_CREDIT",
  "waterfall": [
    { "source": "savings",        "amount": 0,    "used": false },
    { "source": "emergency_buffer","amount": 2100, "used": true  },
    { "source": "delay_expense",  "amount": 0,    "used": false },
    { "source": "future_income",  "amount": 1800, "used": true  },
    { "source": "credit",         "amount": 1100, "used": true  }
  ],
  "message": "Use ₹2,100 buffer + ₹1,100 responsible credit. Safe repayment ₹280/month."
}
```

Field notes:
- `decision`: `"NO_CREDIT_NEEDED" | "PARTIAL_CREDIT" | "FULL_CREDIT" | "CREDIT_DECLINED"`.
- `waterfall`: the ordered fallback chain — savings → buffer → delay → future income → credit.

---

## 8. DashboardResponse  (Person 4 — `GET /worker/{id}/dashboard`)

The ONE endpoint the frontend calls. Bundles everything.

```json
{
  "worker": {
    "worker_id": "W001",
    "name": "Ravi Kumar",
    "occupation": "Food Delivery Partner",
    "current_balance": 11200
  },
  "risk": { "...RiskResult..." : "..." },
  "forecast": { "...ForecastResult..." : "..." },
  "resilience": { "...ResilienceResult..." : "..." },
  "obligations": { "...ObligationSummary..." : "..." },
  "recommendations": [ { "...Recommendation..." : "..." } ]
}
```

The frontend makes **one request** and gets the full worker state. Nested objects are exactly the shapes defined above.

---

## 9. Endpoint summary

| Method | Path | Owner | Returns |
|---|---|---|---|
| `POST` | `/ml/risk` | Person 1 | `RiskResult` |
| `POST` | `/forecast/income` | Person 2 | `ForecastResult` |
| `POST` | `/resilience/evaluate` | Person 3 | `ResilienceResult` |
| `POST` | `/credit/evaluate` | Person 3 | `CreditGuardResult` |
| `GET`  | `/worker/{id}/dashboard` | Person 4 | `DashboardResponse` |
| `GET`  | `/workers` | Person 4 | list of `worker` summaries |
| `POST` | `/simulate/shock` | Person 4 + 3 | `DashboardResponse` (shocked) |
| `POST` | `/simulate/recovery` | Person 4 + 3 | `DashboardResponse` (recovered) |

---

## Rules of the road

1. Everyone builds against the **mock JSON in `/data/demo`** first. Do not wait for another person's real module.
2. Nobody edits another person's folder without a Slack ping.
3. New fields are **optional additions only**. Never rename or delete a frozen field.
4. When your real module is ready, it must produce output that validates against these shapes.
