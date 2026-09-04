"""Generate reproducible synthetic training rows for FlowGuard."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .features import FEATURE_NAMES
except ImportError:
    from features import FEATURE_NAMES


def generate_dataset(rows: int = 2500, seed: int = 42) -> pd.DataFrame:
    """Generate eight transaction-derived features and heuristic risk labels."""
    rng = np.random.default_rng(seed)
    data = {
        "income_volatility": np.clip(rng.gamma(2.0, 0.24, rows), 0.0, 2.0),
        "income_trend_score": np.clip(rng.normal(-0.02, 0.42, rows), -1.0, 1.0),
        "expense_burden": np.clip(rng.beta(2.2, 3.0, rows) * 1.8, 0.0, 2.0),
        "buffer_coverage": np.clip(rng.gamma(2.0, 0.45, rows), 0.0, 2.0),
        "debt_service_burden": np.clip(rng.beta(1.6, 5.0, rows) * 1.6, 0.0, 2.0),
        "income_gap_ratio": np.clip(rng.beta(1.5, 5.0, rows) * 1.7, 0.0, 2.0),
        "payment_frequency_variance": np.clip(rng.gamma(2.0, 0.30, rows), 0.0, 2.0),
        "essential_spend_ratio": np.clip(rng.beta(5.0, 2.0, rows), 0.0, 1.0),
    }
    frame = pd.DataFrame(data, columns=FEATURE_NAMES)
    risk_signal = (
        0.85 * frame["income_volatility"]
        - 0.65 * frame["income_trend_score"]
        + 0.90 * frame["expense_burden"]
        - 0.55 * frame["buffer_coverage"]
        + 0.65 * frame["debt_service_burden"]
        + 0.75 * frame["income_gap_ratio"]
        + 0.45 * frame["payment_frequency_variance"]
        + 0.50 * frame["essential_spend_ratio"]
        + rng.normal(0.0, 0.12, rows)
    )
    frame["risk_label"] = pd.cut(
        risk_signal,
        bins=[-np.inf, 0.0, 0.30, np.inf],
        labels=["LOW", "MODERATE", "HIGH"],
    ).astype(str)
    return frame


def main() -> None:
    output_path = Path(__file__).with_name("synthetic_dataset.csv")
    generate_dataset().to_csv(output_path, index=False)
    print(f"Wrote 2,500 rows to {output_path}")


if __name__ == "__main__":
    main()
