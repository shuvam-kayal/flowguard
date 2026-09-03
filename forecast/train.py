"""Train a Random Forest income model from chronological worker-income data."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterable

import joblib
from sklearn.ensemble import RandomForestRegressor

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from forecast.features import FEATURE_NAMES, build_training_rows, daily_income_series
else:
    from .features import FEATURE_NAMES, build_training_rows, daily_income_series


def train_forecast_model(records: Iterable[dict], model_path: str | Path) -> dict[str, float | int]:
    """Persist a model from records with date, income/amount, and optional worker_id.

    The final 20% of each worker's chronology is validation; no random split is
    used, so a model never trains on future income.
    """
    groups: dict[str, list[dict]] = {}
    for record in records:
        groups.setdefault(str(record.get("worker_id", "default")), []).append(record)
    training: list[tuple[dict[str, float], float]] = []
    validation: list[tuple[dict[str, float], float]] = []
    for worker_records in groups.values():
        rows = build_training_rows(daily_income_series(worker_records))
        split = max(1, int(len(rows) * 0.8))
        training.extend(rows[:split])
        validation.extend(rows[split:])
    if len(training) < 10 or not validation:
        raise ValueError("Need at least 10 train and 1 validation examples (roughly 40 daily records).")
    matrix = [[row[name] for name in FEATURE_NAMES] for row, _ in training]
    model = RandomForestRegressor(n_estimators=200, min_samples_leaf=2, random_state=42, n_jobs=-1)
    model.fit(matrix, [target for _, target in training])
    predicted = model.predict([[row[name] for name in FEATURE_NAMES] for row, _ in validation])
    errors = [abs(target - estimate) for (_, target), estimate in zip(validation, predicted)]
    artifact = {"model": model, "feature_names": FEATURE_NAMES, "residual_mae": sum(errors) / len(errors),
                "training_examples": len(training), "validation_examples": len(validation)}
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, model_path)
    return {"training_examples": len(training), "validation_examples": len(validation), "mae": round(artifact["residual_mae"], 2)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train FlowGuard's income forecast model.")
    parser.add_argument("csv", type=Path, help="CSV with date, income/amount, and optional worker_id columns")
    parser.add_argument("--model-out", type=Path, default=Path(__file__).with_name("income_model.joblib"))
    args = parser.parse_args()
    with args.csv.open(encoding="utf-8", newline="") as input_file:
        print(train_forecast_model(csv.DictReader(input_file), args.model_out))
