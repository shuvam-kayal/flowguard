# Person 3 → Person 4 integration handoff

My resilience engine and Credit Guard are done and tested. Two things live in
`backend/main.py` (your folder), so I'm not editing them directly — here are the
exact changes to apply.

## 1. Wire real Credit Guard into `POST /credit/evaluate`

The endpoint currently returns `sample_credit.json` (mock). Swap the body of
`credit_evaluate` for the real waterfall:

```python
@app.post("/credit/evaluate")
def credit_evaluate(payload: dict):
    """payload: {worker_id, requested_amount}."""
    if not USE_REAL_MODULES:
        credits = _load("sample_credit.json")
        wid = payload.get("worker_id", "W001")
        if wid not in credits:
            raise HTTPException(404, f"Unknown worker {wid}")
        return credits[wid]

    import sys
    sys.path.insert(0, ROOT)
    from resilience.credit_guard import evaluate_credit

    wid = payload.get("worker_id", "W001")
    requested = int(payload.get("requested_amount", 0))
    dash = get_dashboard(wid)  # gives profile-ish worker + resilience + forecast
    personas = {p["worker_id"]: p for p in _load("personas.json")["personas"]}
    return evaluate_credit(personas[wid], dash["resilience"], dash["forecast"], requested)
```

Validated output (real mode):
```
W001 req ₹5000  -> PARTIAL_CREDIT    credit ₹90    repay ₹30/mo
W004 req ₹50000 -> PARTIAL_CREDIT    credit ₹8400  repay ₹2800/mo
W002 req ₹1000  -> NO_CREDIT_NEEDED  credit ₹0
```

## 2. Route `/simulate/shock` and `/simulate/recovery` back through my engine

Right now `_apply_shock` scales the resilience numbers directly. For a truthful
demo, build the degraded **forecast** (drop `next_30_days`, set `weather="SHOCK"`,
raise `shock_probability`) and re-run my `evaluate()` + `recommend()` on it, so
mode → SHOCK and safe-to-spend recomputes from real logic rather than a multiplier.
Same for recovery with a `trend="RISING"` forecast. Ping me and we'll pair on it.

## Contract note
Everything I emit validates against `ResilienceResult`, `Recommendation`, and
`CreditGuardResult`. No contract fields changed.