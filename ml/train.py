"""Train an optional slim Random Forest from a CSV of transaction-derived rows.

Expected columns are the six feature names plus ``risk_label`` (LOW, MODERATE,
or HIGH). The runtime has a deterministic fallback, so the API never depends
on a binary model artifact being present.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .features import FEATURE_NAMES
except ImportError:  # supports python ml/train.py from the repository root
    from features import FEATURE_NAMES


def train(input_csv: str, output_path: str = "ml/model.pkl") -> dict[str, object]:
    try:
        import pandas as pd
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import LabelEncoder
    except ImportError as exc:
        raise RuntimeError("Training requires pandas, scikit-learn, and joblib; install project requirements first") from exc
    frame = pd.read_csv(input_csv)
    missing = [name for name in (*FEATURE_NAMES, "risk_label") if name not in frame]
    if missing:
        raise ValueError(f"Training data is missing columns: {', '.join(missing)}")
    frame = frame.dropna(subset=[*FEATURE_NAMES, "risk_label"])
    if len(frame) < 3 or frame["risk_label"].nunique() < 2:
        raise ValueError("Training data needs at least 3 complete rows and 2 risk classes")
    encoder = LabelEncoder()
    labels = encoder.fit_transform(frame["risk_label"].astype(str).str.upper())
    model = RandomForestClassifier(
        n_estimators=160,
        max_depth=4,
        min_samples_split=15,
        min_samples_leaf=10,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )
    model.fit(frame[list(FEATURE_NAMES)], labels)
    import joblib
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "encoder": encoder, "features": list(FEATURE_NAMES), "version": 1}, destination)
    schema = {"features": list(FEATURE_NAMES), "classes": list(encoder.classes_), "rows": len(frame)}
    destination.with_suffix(destination.suffix + ".schema.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
    return schema


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("output_path", nargs="?", default="ml/model.pkl")
    args = parser.parse_args()
    print(json.dumps(train(args.input_csv, args.output_path), indent=2))
