# FlowGuard — How we work (READ FIRST)

## Hard folder ownership — nobody edits another person's folder without a Slack ping

| Person | Owns | API contract |
|---|---|---|
| **P1 — ML / Risk** | `/ml/**` | `POST /ml/risk` → `RiskResult` |
| **P2 — Forecast** | `/forecast/**` | `POST /forecast/income` → `ForecastResult` |
| **P3 — Resilience** | `/resilience/**` | `POST /resilience/evaluate` → `ResilienceResult` + `POST /credit/evaluate` |
| **P4 — Backend** | `/backend/**`, `/data/**` | `GET /worker/{id}/dashboard` |
| **P5 — Frontend** | `/frontend/**` | consumes the dashboard endpoint |
| **You — Lead** | `/docs/**`, contracts, checkpoints, demo | — |

Shared file everyone reads, nobody edits alone: **`docs/api-contract.md`** and
**`backend/schemas/contracts.py`**. Contract changes are a team decision.

## Day-1 rule: build against mocks, never wait
Every module has matching mock data in `/data/demo`; runtime modules also have
safe cold-start implementations that preserve the same contracts.
- P5 builds the whole UI from `frontend/public/mock_dashboards.json` — no backend needed.
- P3 tests `resilience/engine.py` against `data/demo/sample_*.json` — no ML needed.
- P1/P2 can retrain models independently; the deployed fallback remains
  deterministic and contract-compatible until a model artifact is available.

## Regenerate mocks after any contract change
```bash
python data/demo/generate_mocks.py
```

## Git
Branch per person, PR into `main`. Never push straight to `main`.
```
feature/ml-risk   feature/income-forecast   feature/resilience-engine
feature/backend   feature/frontend
```

## Integration checkpoints (see docs/checkpoints.md)
T+4h independent · T+8h ML+forecast+backend · T+12h full dashboard · T+16h full demo
