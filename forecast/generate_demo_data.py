"""Generate reproducible, synthetic daily gig-income history for demo training."""
from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path


PLATFORMS = (
    ("Delivery", (0.94, 0.96, 1.00, 1.03, 1.12, 1.23, 1.18)),
    ("Ride hailing", (0.92, 0.94, 0.98, 1.02, 1.12, 1.27, 1.20)),
    ("Freelance", (1.12, 1.10, 1.08, 1.05, 1.00, 0.72, 0.66)),
    ("Home services", (1.03, 1.06, 1.07, 1.04, 1.00, 0.91, 0.88)),
)


def generate_records(workers: int = 200, days: int = 180, seed: int = 42) -> list[dict[str, str | int | float]]:
    """Create varied worker histories with seasonality, trends, missed days, and shocks.

    The data is deliberately labelled synthetic: it is appropriate for a demo
    pipeline and regression test, never evidence of real model accuracy.
    """
    random_source = random.Random(seed)
    start = date(2026, 1, 1)
    records: list[dict[str, str | int | float]] = []
    for worker_index in range(workers):
        platform, weekday_pattern = random_source.choice(PLATFORMS)
        daily_base = random_source.uniform(350, 1_350)
        daily_trend = random_source.uniform(-0.22, 0.20)
        volatility = random_source.uniform(0.07, 0.26)
        hours = random_source.uniform(5.0, 10.0)
        shock_start = random_source.randrange(30, max(31, days - 18))
        shock_length = random_source.randrange(4, 13)
        shock_factor = random_source.uniform(0.35, 0.72)
        for offset in range(days):
            day = start + timedelta(days=offset)
            trend_factor = 1 + daily_trend * (offset / max(1, days - 1))
            shock = shock_factor if shock_start <= offset < shock_start + shock_length else 1.0
            worked = random_source.random() > (0.045 if platform != "Freelance" else 0.16)
            noise = max(0.25, random_source.gauss(1.0, volatility))
            amount = daily_base * weekday_pattern[day.weekday()] * trend_factor * shock * noise if worked else 0
            records.append({
                "worker_id": f"SYN{worker_index + 1:03d}", "date": day.isoformat(),
                "income": round(max(0, amount)), "platform": platform,
                "hours_worked": round(hours * (0.8 + random_source.random() * 0.35), 1) if worked else 0,
                "data_source": "synthetic_demo",
            })
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic daily gig-income training data.")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("demo_income_history.csv"))
    parser.add_argument("--workers", type=int, default=200)
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.workers < 1 or args.days < 40:
        parser.error("--workers must be positive and --days must be at least 40.")
    records = generate_records(args.workers, args.days, args.seed)
    with args.output.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records)} synthetic daily-income records to {args.output}")
