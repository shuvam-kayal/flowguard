"""Walk-forward, out-of-time evaluation for the income forecast model."""
from __future__ import annotations

import argparse
import csv
from math import sqrt
from pathlib import Path
import sys
from typing import Iterable

import joblib

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from forecast.features import FEATURE_NAMES, MIN_MODEL_HISTORY, daily_income_series, feature_row
else:
    from .features import FEATURE_NAMES, MIN_MODEL_HISTORY, daily_income_series, feature_row


def evaluate_model(records: Iterable[dict], model_path: str | Path) -> dict[str, float | int]:
    """Report MAE and RMSE on the last 20% of every worker's chronology."""
    artifact = joblib.load(model_path)
    model = artifact["model"]
    groups: dict[str, list[dict]] = {}
    for record in records:
        groups.setdefault(str(record.get("worker_id", "default")), []).append(record)
    feature_matrix: list[list[float]] = []
    actuals: list[float] = []
    for worker_records in groups.values():
        series = daily_income_series(worker_records)
        values = [income for _, income in series]
        start = max(MIN_MODEL_HISTORY, int(len(values) * 0.8))
        for index in range(start, len(values)):
            row = feature_row(values[:index], series[index][0])
            feature_matrix.append([row[name] for name in FEATURE_NAMES])
            actuals.append(values[index])
    if not actuals:
        raise ValueError("Not enough data for an out-of-time evaluation.")
    # One batched call avoids thousands of expensive tiny Random Forest calls.
    predictions = model.predict(feature_matrix)
    errors = [actual - float(prediction) for actual, prediction in zip(actuals, predictions)]
    return {"observations": len(errors), "mae": round(sum(abs(error) for error in errors) / len(errors), 2),
            "rmse": round(sqrt(sum(error ** 2 for error in errors) / len(errors)), 2)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate a FlowGuard income forecast model out of time.")
    parser.add_argument("csv", type=Path, help="The same chronological income CSV used for training")
    parser.add_argument("--model", type=Path, default=Path(__file__).with_name("income_model.joblib"))
    args = parser.parse_args()
    with args.csv.open(encoding="utf-8", newline="") as input_file:
        print(evaluate_model(csv.DictReader(input_file), args.model))
