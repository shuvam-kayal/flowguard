from datetime import date, timedelta
import random

from backend.models import Expense, IncomeRecord, Obligation, Transaction


def generate_worker_scenario() -> dict:
    scenario = random.choice([
        {"income": 24000, "std": 2800, "fixed": 9500, "variable": 6000, "savings": 4500, "debt": 4000, "trend": "STABLE"},
        {"income": 22000, "std": 6500, "fixed": 9000, "variable": 7500, "savings": 1800, "debt": 9000, "trend": "DECLINING"},
        {"income": 27000, "std": 4200, "fixed": 11000, "variable": 7000, "savings": 2500, "debt": 12000, "trend": "RISING"},
        {"income": 18000, "std": 7200, "fixed": 10500, "variable": 6500, "savings": 800, "debt": 15000, "trend": "DECLINING"},
    ])
    scenario["total"] = scenario["fixed"] + scenario["variable"]
    scenario["emi"] = min(scenario["debt"], random.randint(600, 1800)) if scenario["debt"] else 0
    scenario["balance"] = max(500, scenario["income"] - scenario["total"] + random.randint(500, 3000))
    return scenario


def generate_income_records(worker_id: str, scenario: dict, days: int = 75) -> list[IncomeRecord]:
    records = []
    for offset in range(days, 0, -1):
        amount = max(250, int(random.gauss(scenario["income"] / 26, scenario["std"] / 8)))
        records.append(IncomeRecord(worker_id=worker_id, amount=amount,
                                    date=(date.today() - timedelta(days=offset)).isoformat()))
    return records


def generate_expenses(worker_id: str, scenario: dict, days: int = 75) -> list[Expense]:
    records = []
    categories = [("Fuel", 0.25), ("Food", 0.25), ("Utilities", 0.15), ("Other", 0.35)]
    daily = scenario["variable"] / 30
    for offset in range(days, 0, -1):
        category = random.choices([x[0] for x in categories], weights=[x[1] for x in categories])[0]
        amount = max(50, int(random.gauss(daily / 2.2, max(20, daily / 5))))
        records.append(Expense(worker_id=worker_id, amount=amount, category=category,
                               date=(date.today() - timedelta(days=offset)).isoformat()))
    return records


def generate_transactions(worker_id: str, incomes: list[IncomeRecord], expenses: list[Expense]) -> list[Transaction]:
    transactions = [Transaction(worker_id=worker_id, amount=i.amount, date=i.date, type="CREDIT",
                                category="INCOME", description="Platform payout", source="Gig platform") for i in incomes]
    transactions.extend(Transaction(worker_id=worker_id, amount=e.amount, date=e.date, type="DEBIT",
                                    category=e.category, description=e.category, source="Wallet") for e in expenses)
    return transactions


def generate_obligations(worker_id: str, scenario: dict) -> list[Obligation]:
    return [
        Obligation(worker_id=worker_id, name="Rent", amount=max(1000, scenario["fixed"] - 2500),
                   due_date=(date.today().replace(day=1) + timedelta(days=32)).replace(day=1).isoformat(), category="FIXED"),
        Obligation(worker_id=worker_id, name="EMI", amount=scenario["emi"],
                   due_date=(date.today() + timedelta(days=14)).isoformat(), category="DEBT"),
    ]
