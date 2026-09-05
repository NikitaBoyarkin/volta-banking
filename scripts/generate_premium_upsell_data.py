"""Generate synthetic premium-upsell data for the Volta neobank.

Produces `volta_premium_upsell.csv` consumed by `volta_premium_upsell.py`:

  user_id, jtbd_segment, cohort, months_since_signup, logins_per_week,
  tx_per_month, balance_eur, offer_channel, converted, upgrade_reason

Design — Free→Premium conversion across five JTBD segments. The audit's
risk #2: "premium upsell doesn't transfer to new segments". The anchor
(young professionals) and status-seekers (premium_status) convert well;
digital newcomers 45+ and family budgeters barely convert. Conversion also
rises with engagement (logins, tx volume, balance) and the offer channel
(in-app > email > push > none).

Run from the repo root:
    uv run python generate_premium_upsell_data.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

COHORT_ORDER = ["Power", "Growth", "Casual", "Dormant"]
CHANNEL_ORDER = ["in_app", "email", "push", "none"]

# (segment, n_users, cohort_dist, base_conv, avg_logins, avg_tx, avg_balance)
SEGMENT_SPECS: list[tuple[str, int, tuple[float, ...], float, float, float, float]] = [
    ("young_professionals", 12000, (0.30, 0.40, 0.25, 0.05), 0.12, 9.0, 15.0, 1200.0),
    ("digital_newcomers", 8000, (0.02, 0.15, 0.43, 0.40), 0.03, 2.5, 6.0, 300.0),
    ("travelers", 6000, (0.25, 0.40, 0.30, 0.05), 0.08, 7.0, 25.0, 800.0),
    ("family_budgeters", 10000, (0.08, 0.30, 0.47, 0.15), 0.05, 5.0, 12.0, 500.0),
    ("premium_status", 4000, (0.55, 0.30, 0.12, 0.03), 0.20, 11.0, 20.0, 3000.0),
]
SEGMENT_BASE_CONV: dict[str, float] = {name: base for name, _, _, base, _, _, _ in SEGMENT_SPECS}
SEGMENT_COHORT_DIST: dict[str, tuple[float, ...]] = {
    name: dist for name, _, dist, _, _, _, _ in SEGMENT_SPECS
}

COHORT_MULT: dict[str, float] = {"Power": 1.5, "Growth": 1.2, "Casual": 0.8, "Dormant": 0.4}
CHANNEL_MULT: dict[str, float] = {"in_app": 1.4, "email": 1.15, "push": 1.0, "none": 0.6}

# Top upgrade reason per segment (weighted; first = most common).
UPGRADE_REASONS: dict[str, list[str]] = {
    "young_professionals": ["premium_features", "cashback", "status", "support"],
    "digital_newcomers": ["support", "premium_features", "cashback", "status"],
    "travelers": ["premium_features", "cashback", "support", "status"],
    "family_budgeters": ["cashback", "support", "premium_features", "status"],
    "premium_status": ["status", "premium_features", "cashback", "support"],
}
REASON_WEIGHTS = [0.5, 0.25, 0.15, 0.1]


def conversion_probability(
    segment: str, cohort: str, logins: float, tx: int, balance: float, channel: str
) -> float:
    """Free→Premium conversion probability for one user."""
    base = SEGMENT_BASE_CONV[segment]
    cohort_mult = COHORT_MULT[cohort]
    channel_mult = CHANNEL_MULT[channel]
    engagement = 1.0 + 0.02 * (logins - 5.0) + 0.01 * (tx - 10.0) + 0.0001 * (balance - 1000.0)
    p = base * cohort_mult * channel_mult * engagement
    return float(min(0.9, max(0.001, p)))


def generate_users() -> pd.DataFrame:
    """One row per user: engagement, offer channel, conversion outcome."""
    rows: list[dict[str, float | str | int]] = []
    user_id = 0
    for segment, n, cohort_dist, _, avg_logins, avg_tx, avg_balance in SEGMENT_SPECS:
        for _ in range(n):
            user_id += 1
            cohort = RNG.choice(COHORT_ORDER, p=cohort_dist)
            months = int(RNG.integers(1, 25))
            logins = max(0.0, float(RNG.normal(avg_logins, avg_logins * 0.4)))
            tx = int(RNG.poisson(avg_tx))
            balance = max(0.0, float(RNG.normal(avg_balance, avg_balance * 0.5)))
            channel = RNG.choice(CHANNEL_ORDER, p=[0.3, 0.3, 0.2, 0.2])
            p = conversion_probability(segment, cohort, logins, tx, balance, channel)
            converted = int(RNG.random() < p)
            reason = RNG.choice(UPGRADE_REASONS[segment], p=REASON_WEIGHTS) if converted else "none"
            rows.append(
                {
                    "user_id": user_id,
                    "jtbd_segment": segment,
                    "cohort": cohort,
                    "months_since_signup": months,
                    "logins_per_week": round(logins, 1),
                    "tx_per_month": tx,
                    "balance_eur": round(balance, 2),
                    "offer_channel": channel,
                    "converted": converted,
                    "upgrade_reason": reason,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    df = generate_users()
    df.to_csv(DATA_DIR / "volta_premium_upsell.csv", index=False)

    print(f"Generated {len(df):,} users across {df['jtbd_segment'].nunique()} segments")
    print("Wrote: volta_premium_upsell.csv")
    print("\nFree→Premium conversion by segment (%):")
    g = df.groupby("jtbd_segment")["converted"].mean().mul(100).round(1)
    print(g.to_string())


if __name__ == "__main__":
    main()
