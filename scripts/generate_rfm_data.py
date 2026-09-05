"""Generate synthetic transaction data for the Volta RFM analysis.

Produces `data/volta_rfm_transactions.csv` consumed by `volta_rfm_analysis.py`.

Each customer gets a heterogeneous buying pattern so that RFM tiers are
data-driven and separable (Champions, Loyal, Potential, At-Risk, Lost, New).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

N_CUSTOMERS = 8_000
# Transaction observation window (days back from "today").
WINDOW_DAYS = 365
TODAY = pd.Timestamp("2025-12-31")

# Per-behavior archetype: (share, n_tx_mean, gap_days_mean, spend_mean)
ARCHETYPES = {
    "champion": (0.10, 24.0, 8.0, 95.0),
    "loyal": (0.22, 10.0, 22.0, 55.0),
    "potential": (0.24, 4.0, 55.0, 32.0),
    "at_risk": (0.20, 3.0, 130.0, 25.0),
    "lost": (0.14, 2.0, 300.0, 18.0),
    "new": (0.10, 2.5, 25.0, 30.0),
}


def generate_transactions() -> pd.DataFrame:
    rng = RNG
    archetypes = list(ARCHETYPES)
    shares = np.array([ARCHETYPES[a][0] for a in archetypes])
    shares /= shares.sum()

    customers = rng.choice(archetypes, size=N_CUSTOMERS, p=shares)
    customer_id = np.arange(N_CUSTOMERS)

    rows: list[dict[str, object]] = []
    for cid, arche in zip(customer_id, customers, strict=True):
        n_tx_mean, gap_mean, spend_mean = ARCHETYPES[arche][1:]
        n_tx = max(1, int(rng.poisson(n_tx_mean)))
        # Recent customers have shorter gaps; "lost"/"at_risk" have long inactivity.
        last_gap = max(1.0, rng.exponential(gap_mean))
        # Build transaction dates backward from today; first purchase ~ n_tx*gap ago.
        gaps = np.maximum(1.0, rng.exponential(gap_mean, size=n_tx))
        # Force the most recent gap to reflect the archetype's recency.
        gaps[0] = last_gap
        dates = TODAY - pd.to_timedelta(np.cumsum(gaps), unit="D")
        for d in dates:
            amount = max(1.0, float(rng.lognormal(np.log(spend_mean), 0.5)))
            rows.append(
                {
                    "customer_id": int(cid),
                    "tx_date": d.date().isoformat(),
                    "amount": round(amount, 2),
                }
            )

    df = pd.DataFrame(rows)
    return df


def main() -> None:
    df = generate_transactions()
    df.to_csv(DATA_DIR / "volta_rfm_transactions.csv", index=False)
    n_cust = df["customer_id"].nunique()
    print(f"Generated {len(df):,} transactions across {n_cust:,} customers")
    print(f"  -> {DATA_DIR / 'volta_rfm_transactions.csv'}")
    print(f"  Date range: {df['tx_date'].min()} .. {df['tx_date'].max()}")
    print("\nTransaction preview:")
    print(df.head().to_string(index=False))


if __name__ == "__main__":
    main()
