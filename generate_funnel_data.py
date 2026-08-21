"""Augment the committed funnel dataset with install / first-tx timestamps.

The committed `data/volta_funnel_data.csv` ships with binary step flags only
(no timing). Time-to-convert analysis (Project 1, Sprint 1 / F2) needs
timestamps, so this script reads the existing CSV, attaches deterministic
seeded timestamps, and writes it back IN PLACE — the binary flag columns are
preserved byte-for-byte, so every existing test and narrative number still
holds.

Columns added:
  - install_date   : datetime, uniform over a 28-day acquisition window.
  - first_tx_date  : datetime, install_date + a per-channel lognormal gap
                     (referral fastest, paid_social slowest). NaN for users
                     who never reached first_tx.

Run from the repo root:
    uv run python generate_funnel_data.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA_PATH = Path(__file__).resolve().parent / "data" / "volta_funnel_data.csv"
SEED = 42
WINDOW_DAYS = 28

# Per-channel median time-to-first-tx (hours). Referral users are highest-
# intent (fastest); paid social is slowest (less qualified traffic).
CHANNEL_MEDIAN_HOURS = {
    "referral": 18.0,
    "organic_search": 36.0,
    "app_store": 30.0,
    "email": 48.0,
    "paid_social": 72.0,
}
# Lognormal shape (sigma) — shared across channels; only the median varies.
SIGMA = 0.9


def augment(df: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    n = len(df)

    # Install timestamps: uniform over the 28-day window.
    offset_hours = rng.uniform(0, WINDOW_DAYS * 24, size=n)
    df["install_date"] = pd.Timestamp("2024-07-01") + pd.to_timedelta(offset_hours, unit="h")

    # Time to first tx: lognormal gap from install, parameterised per channel.
    # Only users with first_tx == 1 get a first_tx_date.
    medians = df["channel"].map(CHANNEL_MEDIAN_HOURS).to_numpy(dtype=float)
    mu = np.log(medians)
    gap_hours = rng.lognormal(mean=mu, sigma=SIGMA, size=n)
    first_tx_date = df["install_date"] + pd.to_timedelta(gap_hours, unit="h")
    df["first_tx_date"] = first_tx_date.where(df["first_tx"] == 1, pd.NaT)
    return df


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    df = augment(df)
    df.to_csv(DATA_PATH, index=False)

    converted = df[df["first_tx"] == 1].copy()
    converted["hours_to_tx"] = (
        converted["first_tx_date"] - converted["install_date"]
    ).dt.total_seconds() / 3600
    print(f"Augmented {len(df)} rows → {DATA_PATH}")
    print(f"  Install window: {df['install_date'].min()} → {df['install_date'].max()}")
    print(f"  Converted users: {len(converted)} / {len(df)}")
    print("\nMedian hours-to-first-tx by channel:")
    print(converted.groupby("channel")["hours_to_tx"].median().round(1).sort_values().to_string())


if __name__ == "__main__":
    main()
