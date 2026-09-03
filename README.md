# FlowGuard

AI financial-resilience platform for gig / irregular-income workers.
**Predict → Detect → Protect → Guide → Recover.**

The core: don't give volatile-income workers more credit — make their income
behave like a stable salary, and use credit only as a last resort.

## Quick start

### Backend (Person 4)
```bash
pip install -r requirements.txt
python data/demo/generate_mocks.py        # (re)build demo data
uvicorn backend.main:app --reload --port 8000
# open http://localhost:8000/docs
```

### Frontend (Person 5)
```bash
cd frontend
# scaffold Next.js here (npx create-next-app .), then:
# import components/DashboardStarter.jsx and lib/api.js
# set NEXT_PUBLIC_API_URL=http://localhost:8000
```
Frontend also works with **zero backend** via `public/mock_dashboards.json`.

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

## Personas (shared test characters)
W001 Ravi (hero, HIGH/WATCH) · W002 Aisha (healthy, LOW) · W003 Arjun (freelancer, volatile) ·
W004 Meena (crisis, SHOCK) · W005 Suresh (RECOVERY).

## Docs
`docs/api-contract.md` · `docs/checkpoints.md` · `docs/demo-script.md` · `CONTRIBUTING.md`
