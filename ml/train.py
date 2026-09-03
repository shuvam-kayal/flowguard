"""Train an optional slim Random Forest from a CSV of transaction-derived rows.

Expected columns are the eight feature names (from ``FEATURE_NAMES``) plus
``risk_label`` (LOW, MODERATE, or HIGH).  The runtime has a deterministic
fallback, so the API never depends on a binary model artifact being present.

Schema synchronisation
----------------------
After every successful training run:
  * ``model.pkl``             — joblib artifact with ``model``, ``encoder``,
                                ``features`` (list in FEATURE_NAMES order), and ``version``.
  * ``model.pkl.schema.json`` — human-readable JSON recording the feature list,
                                class names, row count, and a ``feature_hash``
                                that ``predict.py`` uses to detect staleness.

These two files must always be written atomically (both succeed or neither is
left in a partially-written state) to prevent artifact desynchronisation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

try:
    from .features import FEATURE_NAMES
except ImportError:  # supports: python ml/train.py from the repository root
    from features import FEATURE_NAMES  # type: ignore[no-redef]

# Schema version — increment whenever the artifact format changes.
_ARTIFACT_VERSION = 2


def _feature_hash(feature_list: list[str]) -> str:
    """SHA-256 of the ordered feature list, truncated to 16 hex chars.

    Both ``train.py`` and ``predict.py`` compute this hash independently;
    a mismatch means the artifact was produced by an older code version.
    """
    payload = json.dumps(feature_list, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()[:16]


def _atomic_write(path: Path, content: bytes) -> None:
    """Write *content* to *path* atomically via a temp file on the same filesystem."""
    dir_ = path.parent
    dir_.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_, prefix=".tmp_", suffix=path.suffix)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(content)
        os.replace(tmp_path, path)  # atomic on POSIX; best-effort on Windows
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def train(input_csv: str, output_path: str = "ml/model.pkl") -> dict[str, object]:
    """Train and persist a Random Forest risk classifier.

    Returns the schema dict that was written to ``model.pkl.schema.json``.

    Raises
    ------
    RuntimeError
        When required libraries (pandas, scikit-learn, joblib) are not installed.
    ValueError
        When the input CSV is missing required columns or has insufficient data.
    """
    try:
        import joblib
        import pandas as pd
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import LabelEncoder
    except ImportError as exc:
        raise RuntimeError(
            "Training requires pandas, scikit-learn, and joblib; "
            "install project requirements first."
        ) from exc

    # ── Load & validate training data ─────────────────────────────────────
    frame = pd.read_csv(input_csv)
    required_columns = (*FEATURE_NAMES, "risk_label")
    missing = [col for col in required_columns if col not in frame.columns]
    if missing:
        raise ValueError(
            f"Training data is missing columns: {', '.join(missing)}\n"
            f"Available columns: {list(frame.columns)}"
        )

    frame = frame.dropna(subset=list(required_columns))
    if len(frame) < 3:
        raise ValueError(
            f"Training data needs at least 3 complete rows; got {len(frame)}."
        )
    if frame["risk_label"].nunique() < 2:
        raise ValueError(
            "Training data must contain at least 2 distinct risk classes "
            f"(LOW, MODERATE, HIGH); found: {sorted(frame['risk_label'].unique())}."
        )

    # ── Encode labels ─────────────────────────────────────────────────────
    encoder = LabelEncoder()
    labels = encoder.fit_transform(frame["risk_label"].astype(str).str.upper())
    class_names: list[str] = [str(c) for c in encoder.classes_]

    # ── Train ─────────────────────────────────────────────────────────────
    model = RandomForestClassifier(
        n_estimators=160,
        max_depth=4,
        min_samples_split=15,
        min_samples_leaf=10,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )
    feature_list = list(FEATURE_NAMES)  # canonical order from features.py
    model.fit(frame[feature_list], labels)

    # ── Build artifact & schema ───────────────────────────────────────────
    fhash = _feature_hash(feature_list)
    artifact = {
        "model":        model,
        "encoder":      encoder,
        "features":     feature_list,
        "version":      _ARTIFACT_VERSION,
        "feature_hash": fhash,
    }
    schema: dict[str, object] = {
        "features":     feature_list,
        "feature_hash": fhash,
        "classes":      class_names,
        "rows":         len(frame),
        "version":      _ARTIFACT_VERSION,
    }

    # ── Atomic write — both files or neither ─────────────────────────────
    destination = Path(output_path)
    schema_destination = destination.with_suffix(destination.suffix + ".schema.json")

    # Serialise both to bytes before touching the filesystem.
    import io
    buf = io.BytesIO()
    joblib.dump(artifact, buf)
    artifact_bytes = buf.getvalue()
    schema_bytes = json.dumps(schema, indent=2).encode("utf-8")

    _atomic_write(destination, artifact_bytes)
    _atomic_write(schema_destination, schema_bytes)

    print(
        f"Wrote {destination} ({len(artifact_bytes) // 1024} KB) "
        f"and {schema_destination.name} (feature_hash={fhash})"
    )
    return schema


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train the FlowGuard risk classifier."
    )
    parser.add_argument("input_csv",   help="Path to training CSV with feature columns + risk_label")
    parser.add_argument("output_path", nargs="?", default="ml/model.pkl",
                        help="Destination for model.pkl (default: ml/model.pkl)")
    args = parser.parse_args()
    print(json.dumps(train(args.input_csv, args.output_path), indent=2))
