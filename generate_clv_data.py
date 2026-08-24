"""Generate synthetic CLV data for the Volta CLV modeling project.

Produces two CSVs consumed by `volta_clv_modeling.py`:
  - data/volta_clv_customers.csv : per-customer purchase panel (frequency, avg
    spend, lifetime months, total spend, segment)
  - data/volta_clv_cohorts.csv   : per-segment cohort retention curves
    (month_1..month_24) used by the predictive retention-curve CLV method

Segments mirror Project 4 (Power / Growth / Casual / Dormant) so CLV reconciles
with the segmentation narrative.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

N_CUSTOMERS = 12_000
HORIZON_MONTHS = 24

# Per-segment: (share, purchase_rate_per_month, avg_tx_value, tenure_months_mean)
SEGMENTS = {
    "Power": (0.12, 3.2, 90.0, 30.0),
    "Growth": (0.24, 1.4, 45.0, 18.0),
    "Casual": (0.32, 0.5, 28.0, 12.0),
    "Dormant": (0.32, 0.15, 15.0, 8.0),
}


def generate_customers() -> pd.DataFrame:
    rng = RNG
    seg_names = list(SEGMENTS)
    shares = np.array([SEGMENTS[s][0] for s in seg_names])
    shares /= shares.sum()
    segs = rng.choice(seg_names, size=N_CUSTOMERS, p=shares)

    rows: list[dict[str, object]] = []
    for cid, seg in enumerate(segs):
        _, rate, tx_val, tenure_mean = SEGMENTS[seg]
        tenure = max(1.0, rng.exponential(tenure_mean / 6))  # months active
        n_tx = max(0, int(rng.poisson(rate * tenure)))
        if n_tx == 0:
            rows.append(
                {
                    "customer_id": cid,
                    "segment": seg,
                    "frequency": 0,
                    "avg_tx_value": 0.0,
                    "total_spend": 0.0,
                    "lifetime_months": round(tenure, 1),
                }
            )
            continue
        values = np.clip(rng.lognormal(np.log(tx_val), 0.6, size=n_tx), 1, 1000)
        rows.append(
            {
                "customer_id": cid,
                "segment": seg,
                "frequency": n_tx,
                "avg_tx_value": round(values.mean(), 2),
                "total_spend": round(values.sum(), 2),
                "lifetime_months": round(tenure, 1),
            }
        )
    return pd.DataFrame(rows)


def generate_cohorts() -> pd.DataFrame:
    """Per-segment retention: decays slower for Power, faster for Dormant."""
    base_retention = {
        "Power": 0.96,
        "Growth": 0.90,
        "Casual": 0.82,
        "Dormant": 0.68,
    }
    rows: list[dict[str, object]] = []
    for seg in SEGMENTS:
        r = base_retention[seg]
        curve = {f"month_{m}": round(r**m, 3) for m in range(1, HORIZON_MONTHS + 1)}
        rows.append({"segment": seg, **curve})
    return pd.DataFrame(rows)


def main() -> None:
    customers = generate_customers()
    cohorts = generate_cohorts()
    customers.to_csv(DATA_DIR / "volta_clv_customers.csv", index=False)
    cohorts.to_csv(DATA_DIR / "volta_clv_cohorts.csv", index=False)
    print(f"Generated {len(customers):,} customers + cohort curves")
    print(f"  -> {DATA_DIR / 'volta_clv_customers.csv'}, {DATA_DIR / 'volta_clv_cohorts.csv'}")
    print("\nSegment distribution:")
    print(customers["segment"].value_counts(normalize=True).round(3).to_string())


if __name__ == "__main__":
    main()
