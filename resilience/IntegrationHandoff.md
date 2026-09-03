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
    dash = get_dashboard(wid)  # gives worker + resilience + forecast
    personas = {p["worker_id"]: p for p in _load("personas.json")["personas"]}
    return evaluate_credit(personas[wid], dash["resilience"], dash["forecast"], requested)
```

**Note:** Credit Guard's affordability cap is anchored to
`resilience["safe_to_spend_daily"]` \u2014 the engine's own conservative
liquidity number, with obligations/buffer already netted out exactly once.
That's deliberate: an earlier version subtracted essentials and obligations
independently and double-counted them (rent/EMI appear in both
`essential_daily_spend` and `total_upcoming`), which made Credit Guard
wrongly decline almost every request. Reusing `safe_to_spend_daily` avoids
that and keeps the two modules' notion of "safe money" consistent.

Signature is unchanged (no new required args) \u2014 no other change needed
beyond swapping the mock for this call.

## 2. Route `/simulate/shock` and `/simulate/recovery` back through my engine

Right now `_apply_shock` scales the resilience numbers directly. For a truthful
demo, build the degraded **forecast** (drop `next_30_days`, set `weather="SHOCK"`,
raise `shock_probability`) and re-run my `evaluate()` + `recommend()` on it, so
mode → SHOCK and safe-to-spend recomputes from real logic rather than a multiplier.
Same for recovery with a `trend="RISING"` forecast. Ping me and we'll pair on it.

## 3. Pass `obligations` to `recommend()` for accurate days-to-shock

`recommend()` now computes a real "income dip predicted in N days" from
Person 2's `daily_forecast`, instead of a hardcoded "8 days". It needs the
real `essential_daily_spend` to do that, which comes from `obligations`. In
`get_dashboard()`'s real-orchestration path, change:

```python
recs = recommend(profile, resilience, forecast)
```
to:
```python
recs = recommend(profile, resilience, forecast, obl)
```

This is backward compatible \u2014 `obligations` is an optional 4th arg, so
nothing breaks if you don't get to this before the demo. Without it, the
reason text falls back to an estimate from `fixed_expenses` instead of the
real obligation figure.

## Contract note
Everything I emit validates against `ResilienceResult`, `Recommendation`, and
`CreditGuardResult`. No contract fields changed.