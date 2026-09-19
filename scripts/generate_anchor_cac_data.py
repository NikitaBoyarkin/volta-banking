"""Generate synthetic acquisition-cost curves for the anchor segment launch.

Produces `volta_anchor_cac.csv` consumed by `volta_anchor_cac.py`:

  bucket_id, channel, users, marginal_cac_eur, arpu_eur, monthly_churn_rate,
  ltv_eur

Design — the audit's v2 risk #4: "paid CAC for the anchor 25-34 breaks launch
P&L at scale". Project 18 priced the anchor *on average* (blended LTV/CAC 2.13);
this dataset models the *marginal* cost of each acquisition channel as spend
scales, so the launch P&L can be evaluated at any target user count.

Each row is a bucket of 1,000 acquirable users in one channel. Marginal CAC
rises within a channel (auction saturation, referral exhaustion, diminishing
audiences):

  marginal_cac(bucket i of C) = base * exp(saturation * i / (C - 1)) + noise

Channels also differ in capacity (referral and assisted are capped; paid social
is large but expensive at the margin) and in the LTV of the users they bring
(paid users churn faster). The analysis must therefore allocate the cheapest
marginal users first and find the scale at which the blended CAC crosses the
LTV/CAC >= 3 and payback <= 12-month gates.

Run from the repo root:
    uv run python generate_anchor_cac_data.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

BUCKET_USERS = 1000
CONTRIBUTION_MARGIN = 0.70

# (channel, capacity_buckets, base_cac_eur, saturation, arpu_eur, monthly_churn)
CHANNEL_SPECS: list[tuple[str, int, float, float, float, float]] = [
    ("referral", 40, 18.0, 1.20, 4.40, 0.030),
    ("in_app", 120, 30.0, 1.00, 4.50, 0.033),
    ("partner", 80, 50.0, 1.00, 4.40, 0.035),
    ("paid_social", 200, 60.0, 1.80, 4.20, 0.040),
    ("assisted", 20, 120.0, 0.80, 4.60, 0.028),
]

CHANNEL_ORDER = [c for c, _, _, _, _, _ in CHANNEL_SPECS]
# Anchor segment SOM from the audit (young professionals 200-250K).
ANCHOR_SOM = 225_000
# Acquisition gates.
GATE_LTV_CAC = 3.0
GATE_PAYBACK_MONTHS = 12.0


def marginal_cac(base: float, saturation: float, index: int, capacity: int) -> float:
    """Marginal CAC (EUR) of the index-th bucket in a channel of given capacity."""
    if capacity <= 1:
        return base
    return base * float(np.exp(saturation * index / (capacity - 1)))


def generate_buckets() -> pd.DataFrame:
    """One row per channel × 1,000-user bucket, with marginal CAC and LTV."""
    rows: list[dict[str, float | str | int]] = []
    bucket_id = 0
    for channel, capacity, base, saturation, arpu, churn in CHANNEL_SPECS:
        for i in range(capacity):
            bucket_id += 1
            cac = marginal_cac(base, saturation, i, capacity) * float(RNG.normal(1.0, 0.03))
            ltv = arpu * CONTRIBUTION_MARGIN / churn
            rows.append(
                {
                    "bucket_id": bucket_id,
                    "channel": channel,
                    "users": BUCKET_USERS,
                    "marginal_cac_eur": round(cac, 2),
                    "arpu_eur": arpu,
                    "monthly_churn_rate": churn,
                    "ltv_eur": round(ltv, 2),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    df = generate_buckets()
    df.to_csv(DATA_DIR / "volta_anchor_cac.csv", index=False)

    print(f"Generated {len(df):,} buckets ({len(df) * BUCKET_USERS:,} acquirable users)")
    print("Wrote: volta_anchor_cac.csv")

    print("\nChannel capacity and marginal CAC range (EUR):")
    g = df.groupby("channel")["marginal_cac_eur"].agg(["count", "min", "max"]).round(2)
    print(g.reindex(CHANNEL_ORDER).to_string())

    print("\nChannel LTV (EUR):")
    print(df.groupby("channel")["ltv_eur"].first().reindex(CHANNEL_ORDER).round(2).to_string())
    print(
        f"\nGates: LTV/CAC >= {GATE_LTV_CAC:.1f} and payback <= {GATE_PAYBACK_MONTHS:.0f} months."
    )


if __name__ == "__main__":
    main()
