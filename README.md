# FlowGuard

AI financial-resilience platform for gig / irregular-income workers.
**Predict → Detect → Protect → Guide → Recover.**

The core: don't give volatile-income workers more credit — make their income
behave like a stable salary, and use credit only as a last resort.

## Quick start

### Backend (Person 4)
```bash
.venv\Scripts\python -m pip install -r requirements.txt pytest  # Windows
# source .venv/bin/activate && python -m pip install -r requirements.txt pytest  # macOS/Linux
python data/demo/generate_mocks.py        # (re)build demo data
.venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000
# open http://localhost:8000/docs
```

Create the environment once before running the commands above:
```bash
python -m venv .venv
```

### Verify
```bash
.venv\Scripts\python tests\test_contracts.py
.venv\Scripts\python -m pytest -q
```

### Frontend (Person 5)
```bash
python -m http.server 5173 --directory frontend
# open http://localhost:5173
```
The standalone frontend connects to `http://127.0.0.1:8000` by default. Use
`http://localhost:5173/?api=http://localhost:8000` to override the backend URL.
It includes worker switching, Safe-to-Spend, Financial Weather, forecast
visualization, wallet allocation, explainable recommendations, Credit Guard,
and the shock/recovery simulation flow.

## Architecture
```
transactions → FinancialProfile
     ├─ RiskResult      (ml/)        Person 1
     ├─ ForecastResult  (forecast/)  Person 2
     └─ ObligationSummary (backend/) Person 4
            └─ ResilienceResult + Recommendations (resilience/) Person 3
                   └─ DashboardResponse (backend/) Person 4
                          └─ UI (frontend/) Person 5
```

## The contract is the source of truth
- Human: `docs/api-contract.md`
- Code:  `backend/schemas/contracts.py` (Pydantic — validates everything)
- Demo data: `data/demo/sample_*.json` (all validate against the contracts)

## Runtime implementation

Risk and forecasting are live by default. `ml/features.py` uses only
transaction/income-derived signals: volatility, trend, expense burden, buffer
coverage, debt-service burden, and income gap. `ml/predict.py` loads an
optional `ml/model.pkl` trained with `python -m ml.train <csv>` and otherwise
uses an explainable cold-start scorer. `forecast/predict.py` generates rolling
30-day estimates, uncertainty bands, and Financial Weather without an artifact.

Predictions adjust policy; the credit path remains deterministic and applies
the savings → buffer → future income → affordability-capped credit waterfall.

## Personas (shared test characters)
W001 Ravi (hero, HIGH/WATCH) · W002 Aisha (healthy, LOW) · W003 Arjun (freelancer, volatile) ·
W004 Meena (crisis, SHOCK) · W005 Suresh (RECOVERY).

## Docs
`docs/api-contract.md` · `docs/checkpoints.md` · `docs/demo-script.md` · `CONTRIBUTING.md`
