"""Generate synthetic A/B data for segment-specific premium offers.

Produces `volta_premium_offers.csv` consumed by `volta_premium_offers.py`:

  user_id, jtbd_segment, cohort, group, logins_per_week, tx_per_month,
  balance_eur, converted, upgrade_reason

Design — the audit's v2 risk #3: "segment-specific premium offers won't lift
gap-segment conversion (the fix is untested)". Project 15 showed the *generic*
premium upsell doesn't transfer (anchor 17% vs Digital Newcomers 45+ 2%). This
dataset runs the untested fix as a randomized experiment:

  group = "control"   → the generic premium upsell (Project 15 baseline)
  group = "treatment" → a segment-specific offer:
                        young professionals  → features/status
                        digital newcomers 45+ → support-first
                        family budgeters 30-45 → cashback-first
                        travelers              → FX features

The treatment multiplier is large in the gap segments and small in the anchor
(which the generic offer already serves), so the analysis must recover a
significant segment × arm interaction — the fix helps where the generic offer
failed, but does not erase the value-prop gap.

Run from the repo root:
    uv run python generate_premium_offers_data.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

COHORT_ORDER = ["Power", "Growth", "Casual", "Dormant"]

# (segment, n_per_arm, base_conv, treatment_mult, avg_logins, avg_tx, avg_balance)
SEGMENT_SPECS: list[tuple[str, int, float, float, float, float, float]] = [
    ("young_professionals", 8000, 0.170, 1.06, 9.0, 15.0, 1200.0),
    ("digital_newcomers", 15000, 0.020, 3.20, 2.5, 6.0, 300.0),
    ("family_budgeters", 12000, 0.050, 1.90, 5.0, 12.0, 500.0),
    ("travelers", 6000, 0.080, 1.50, 7.0, 25.0, 800.0),
]
SEGMENT_BASE_CONV: dict[str, float] = {s: base for s, _, base, _, _, _, _ in SEGMENT_SPECS}
SEGMENT_TREAT_MULT: dict[str, float] = {s: mult for s, _, _, mult, _, _, _ in SEGMENT_SPECS}

COHORT_DIST = (0.15, 0.30, 0.35, 0.20)
COHORT_MULT: dict[str, float] = {"Power": 1.5, "Growth": 1.2, "Casual": 0.8, "Dormant": 0.4}

# Upgrade reason by segment (first = most common). The treatment nudges the
# reason toward the segment's own job.
GENERIC_REASONS: dict[str, list[str]] = {
    "young_professionals": ["premium_features", "cashback", "status", "support"],
    "digital_newcomers": ["support", "premium_features", "cashback", "status"],
    "family_budgeters": ["cashback", "support", "premium_features", "status"],
    "travelers": ["premium_features", "cashback", "support", "status"],
}
TREATMENT_REASONS: dict[str, list[str]] = {
    "young_professionals": ["premium_features", "status", "cashback", "support"],
    "digital_newcomers": ["support", "premium_features", "cashback", "status"],
    "family_budgeters": ["cashback", "premium_features", "support", "status"],
    "travelers": ["premium_features", "cashback", "support", "status"],
}
REASON_WEIGHTS = [0.5, 0.25, 0.15, 0.1]


def conversion_probability(
    segment: str, group: str, cohort: str, logins: float, tx: int, balance: float
) -> float:
    """Premium conversion probability for one user."""
    base = SEGMENT_BASE_CONV[segment]
    arm = SEGMENT_TREAT_MULT[segment] if group == "treatment" else 1.0
    engagement = 1.0 + 0.02 * (logins - 5.0) + 0.01 * (tx - 10.0) + 0.0001 * (balance - 1000.0)
    p = base * arm * COHORT_MULT[cohort] * engagement
    return float(min(0.9, max(0.0005, p)))


def generate_users() -> pd.DataFrame:
    """One row per user: segment, arm, engagement, conversion outcome."""
    rows: list[dict[str, float | str | int]] = []
    user_id = 0
    for segment, n_per_arm, _, _, avg_logins, avg_tx, avg_balance in SEGMENT_SPECS:
        for group in ("control", "treatment"):
            for _ in range(n_per_arm):
                user_id += 1
                cohort = str(RNG.choice(COHORT_ORDER, p=COHORT_DIST))
                logins = max(0.0, float(RNG.normal(avg_logins, avg_logins * 0.4)))
                tx = int(RNG.poisson(avg_tx))
                balance = max(0.0, float(RNG.normal(avg_balance, avg_balance * 0.5)))
                p = conversion_probability(segment, group, cohort, logins, tx, balance)
                converted = int(RNG.random() < p)
                reasons = (
                    GENERIC_REASONS[segment] if group == "control" else TREATMENT_REASONS[segment]
                )
                reason = str(RNG.choice(reasons, p=REASON_WEIGHTS)) if converted else "none"
                rows.append(
                    {
                        "user_id": user_id,
                        "jtbd_segment": segment,
                        "cohort": cohort,
                        "group": group,
                        "logins_per_week": round(logins, 1),
                        "tx_per_month": tx,
                        "balance_eur": round(balance, 2),
                        "converted": converted,
                        "upgrade_reason": reason,
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    df = generate_users()
    df.to_csv(DATA_DIR / "volta_premium_offers.csv", index=False)

    print(f"Generated {len(df):,} users across {df['jtbd_segment'].nunique()} segments")
    print("Wrote: volta_premium_offers.csv")

    print("\nPremium conversion (%) by segment × arm:")
    pivot = df.pivot_table(
        index="jtbd_segment", columns="group", values="converted", aggfunc="mean"
    ).mul(100)
    print(pivot.round(2).to_string())


if __name__ == "__main__":
    main()
