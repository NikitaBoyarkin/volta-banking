"""Generate synthetic transaction data with injected anomalies for Volta.

Produces `data/volta_anomaly_transactions.csv` consumed by
`volta_anomaly_detection.py`. Includes a ground-truth `is_anomaly` flag so the
detectors (Z-score, IQR, Isolation Forest) can be scored for precision/recall.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

N_TX = 20_000
ANOMALY_RATE = 0.02
START = pd.Timestamp("2025-01-01")
SPAN_DAYS = 180
N_USERS = 800


def generate_transactions(n: int = N_TX) -> pd.DataFrame:
    rng = RNG
    is_anomaly = rng.random(n) < ANOMALY_RATE
    user_id = rng.integers(0, N_USERS, size=n)
    # Transaction time over a 6-month window; normal activity is daytime-focused.
    minutes = rng.integers(0, SPAN_DAYS * 24 * 60, size=n)
    tx_time = START + pd.to_timedelta(minutes, unit="m")
    hour = rng.uniform(8, 22, size=n)  # normal transactions cluster daytime

    # Normal amounts: right-skewed, mostly small.
    amount = np.clip(rng.lognormal(np.log(35), 0.8, size=n), 1, 2000)

    # Anomalies are unusual in ONE of several ways, so a single amount-based
    # detector under-recalls but a multi-feature model (Isolation Forest on
    # amount + hour + velocity) catches all three types.
    anom_type = rng.integers(0, 3, size=n)
    is_a = is_anomaly.astype(bool)
    # (0) amount spikes (clearly separable on log-amount)
    amount = np.where(is_a & (anom_type == 0), amount * rng.uniform(8, 30, size=n), amount)
    # (1) late-night activity (unusual hour 0-4, outside the normal 8-22 band)
    hour = np.where(is_a & (anom_type == 1), rng.uniform(0, 4, size=n), hour)
    # (2) high user velocity: concentrate many tx on a few "burst" users
    burst_users = rng.choice(N_USERS, size=40, replace=False)
    user_id = np.where(is_a & (anom_type == 2), rng.choice(burst_users, size=n), user_id)

    df = pd.DataFrame(
        {
            "transaction_id": np.arange(n),
            "user_id": user_id,
            "tx_time": tx_time,
            "hour": hour.round(3),
            "amount": amount.round(2),
            "is_anomaly": is_a.astype(int),
        }
    )
    # Recompute tx_time hour from the (possibly shifted) hour column isn't needed;
    # the stored `hour` feature drives the detectors.
    return df


def main() -> None:
    df = generate_transactions()
    df.to_csv(DATA_DIR / "volta_anomaly_transactions.csv", index=False)
    print(f"Generated {len(df):,} transactions")
    print(f"  -> {DATA_DIR / 'volta_anomaly_transactions.csv'}")
    print(f"  Anomaly rate: {df['is_anomaly'].mean():.1%} (ground truth)")
    print(f"  Amount range: {df['amount'].min():.0f} .. {df['amount'].max():,.0f} EUR")


if __name__ == "__main__":
    main()
