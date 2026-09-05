"""Generate synthetic marketing-attribution data for Volta.

Produces `data/volta_attribution_journeys.csv` consumed by
`volta_attribution.py`: converted customer journeys as ordered touchpoints,
each with a revenue value.

Channels carry an intrinsic "influence" weight used by the Shapley value model
as the set-value function v(S) = revenue * min(1, sum of weights in S).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

N_JOURNEYS = 6_000

CHANNELS = ["paid_social", "organic", "referral", "email", "display"]
# Intrinsic conversion-influence weight per channel (used by Shapley value model).
CHANNEL_WEIGHT = {
    "paid_social": 0.30,
    "organic": 0.25,
    "referral": 0.35,
    "email": 0.20,
    "display": 0.10,
}


def generate_journeys(n: int = N_JOURNEYS) -> pd.DataFrame:
    rng = RNG
    rows: list[dict[str, object]] = []
    n_touch_dist = np.array([0.35, 0.35, 0.20, 0.10])  # 1..4 touches
    for jid in range(n):
        n_touch = int(rng.choice([1, 2, 3, 4], p=n_touch_dist))
        channels = rng.choice(CHANNELS, size=n_touch, replace=True)
        # Vary journey revenue by the channels present (higher-influence => more).
        revenue = 50.0 + 200.0 * min(1.0, sum(CHANNEL_WEIGHT[c] for c in channels))
        revenue = max(revenue, float(rng.lognormal(np.log(120), 0.4)))
        for order, ch in enumerate(channels):
            rows.append(
                {
                    "journey_id": jid,
                    "touch_order": order,
                    "channel": ch,
                    "revenue": round(revenue, 2),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    df = generate_journeys()
    df.to_csv(DATA_DIR / "volta_attribution_journeys.csv", index=False)
    n_journeys = df["journey_id"].nunique()
    print(f"Generated {len(df):,} touchpoints across {n_journeys:,} converted journeys")
    print(f"  -> {DATA_DIR / 'volta_attribution_journeys.csv'}")
    print("\nChannel touchpoint share:")
    print(df["channel"].value_counts(normalize=True).round(3).to_string())


if __name__ == "__main__":
    main()
