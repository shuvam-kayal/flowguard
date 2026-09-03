"""Train an optional slim Random Forest from a CSV of transaction-derived rows.

Expected columns are the six feature names plus ``risk_label`` (LOW, MODERATE,
or HIGH). The runtime has a deterministic fallback, so the API never depends
on a binary model artifact being present.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import pandas as pd

from .features import FEATURE_NAMES


def train(input_csv: str, output_path: str) -> None:
    frame = pd.read_csv(input_csv)
    missing = [name for name in (*FEATURE_NAMES, "risk_label") if name not in frame]
    if missing:
        raise ValueError(f"Training data is missing columns: {', '.join(missing)}")
    encoder = LabelEncoder()
    labels = encoder.fit_transform(frame["risk_label"].astype(str).str.upper())
    model = RandomForestClassifier(n_estimators=160, max_depth=5, random_state=42, class_weight="balanced")
    model.fit(frame[list(FEATURE_NAMES)], labels)
    import joblib
    joblib.dump({"model": model, "encoder": encoder, "features": list(FEATURE_NAMES)}, output_path)
    Path(f"{output_path}.schema.json").write_text(json.dumps({"features": FEATURE_NAMES}), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("output_path", nargs="?", default="ml/model.pkl")
    args = parser.parse_args()
    train(args.input_csv, args.output_path)
