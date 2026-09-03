"""Validates every mock against the Pydantic contracts. Run: python tests/test_contracts.py"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from schemas.contracts import (RiskResult, ForecastResult, ObligationSummary,
                               ResilienceResult, CreditGuardResult, DashboardResponse)
D = os.path.join(ROOT, "data", "demo")

def check(fname, model):
    data = json.load(open(os.path.join(D, fname), encoding="utf-8"))
    for wid, obj in data.items():
        model(**obj)
    print(f"  OK {fname} ({len(data)})")

def main():
    print("Validating mocks against contracts:")
    check("sample_risk.json", RiskResult)
    check("sample_forecasts.json", ForecastResult)
    check("sample_obligations.json", ObligationSummary)
    check("sample_resilience.json", ResilienceResult)
    check("sample_credit.json", CreditGuardResult)
    check("sample_dashboards.json", DashboardResponse)
    print("ALL CONTRACTS VALID ✓")

if __name__ == "__main__":
    main()
