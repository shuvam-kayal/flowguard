# Integration checkpoints

Don't merge to `main` every 20 minutes. Sync at these gates only.

## T+4h — everything runs independently
- [ ] P1 `python ml/predict.py` prints a valid RiskResult
- [ ] P2 `python forecast/predict.py` prints a valid ForecastResult
- [ ] P3 `python resilience/engine.py` prints all 5 personas
- [ ] P4 `uvicorn backend.main:app` serves `/worker/W001/dashboard` (mock mode)
- [ ] P5 dashboard renders from `mock_dashboards.json`

## T+8h — ML + forecast + backend connected
- [ ] P4 flips `USE_REAL_MODULES = True` in `backend/main.py`
- [ ] Real risk + forecast flow into resilience engine
- [ ] `/worker/W001/dashboard` returns real-model output validating against contracts

## T+12h — frontend + backend connected
- [ ] P5 points `NEXT_PUBLIC_API_URL` at the live backend
- [ ] All 5 screens render live data
- [ ] Simulate shock / recovery buttons work end-to-end

## T+16h — complete user journey (Ravi's story) works start to finish
- [ ] Dashboard → Weather → Wallet → Intervention → Credit Guard
- [ ] Simulate shock visibly changes safe-to-spend, mode, recommendations

## Remaining — polish, PPT, deploy, rehearse the 5-min demo
