"""Generate synthetic JTBD-segment × behavioral-cohort data for Volta.

Produces `volta_jtbd_segments.csv` consumed by `volta_jtbd_mapping.py`:

  user_id, jtbd_segment, cohort, age, logins_per_week, multi_currency,
  family_status, premium, support_tickets, kyc_duration_days

Design — five JTBD segments (from the Market & Jobs audit) mapped to the four
behavioral cohorts (Power/Growth/Casual/Dormant from the segmentation project).
The mapping is deliberately NON-uniform so the chi-square test in the analysis
script is significant and the risk-#3 hypothesis ("Dormant = UX friction, not
'no job'") is testable:

  segment              n      Power  Growth  Casual  Dormant
  young_professionals  12000  0.30   0.40    0.25    0.05
  digital_newcomers     8000  0.02   0.15    0.43    0.40   ← Dormant over-represented
  travelers             6000  0.25   0.40    0.30    0.05
  family_budgeters     10000  0.08   0.30    0.47    0.15
  premium_status        4000  0.55   0.30    0.12    0.03

Dormant concentrates in digital newcomers (40%) — users who WANT mobile
banking but hit UX friction (high support_tickets, long kyc_duration_days) —
and is under-represented in family budgeters (15%), whose dormancy is
need-driven, not friction-driven. That contrast is the analysis's core claim.

Run from the repo root:
    uv run python generate_jtbd_data.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

COHORTS = ["Power", "Growth", "Casual", "Dormant"]

# (segment, n_users, cohort_distribution, age_mean, logins_mean,
#  multi_currency_p, family_p, premium_p, support_tickets_mean, kyc_days_mean)
SEGMENT_SPECS: list[
    tuple[str, int, tuple[float, ...], float, float, float, float, float, float, float]
] = [
    ("young_professionals", 12000, (0.30, 0.40, 0.25, 0.05), 28.0, 9.0, 0.30, 0.10, 0.25, 0.8, 2.5),
    ("digital_newcomers", 8000, (0.02, 0.15, 0.43, 0.40), 52.0, 2.5, 0.05, 0.40, 0.05, 3.5, 9.0),
    ("travelers", 6000, (0.25, 0.40, 0.30, 0.05), 31.0, 7.0, 0.90, 0.15, 0.30, 1.2, 3.0),
    ("family_budgeters", 10000, (0.08, 0.30, 0.47, 0.15), 38.0, 5.0, 0.10, 0.85, 0.20, 1.5, 4.0),
    ("premium_status", 4000, (0.55, 0.30, 0.12, 0.03), 35.0, 11.0, 0.40, 0.20, 0.90, 0.5, 2.0),
]

# Display names (EN in code; RU equivalents in the audit note).
SEGMENT_NAMES: dict[str, str] = {
    "young_professionals": "Young Professionals",
    "digital_newcomers": "Digital Newcomers 45+",
    "travelers": "Travelers",
    "family_budgeters": "Family Budgeters",
    "premium_status": "Premium Status",
}


def generate_users() -> pd.DataFrame:
    """Generate one row per user across the five JTBD segments."""
    frames: list[pd.DataFrame] = []
    user_id = 0
    for (
        segment,
        n,
        dist,
        age_m,
        logins_m,
        mc_p,
        fam_p,
        prem_p,
        tickets_m,
        kyc_m,
    ) in SEGMENT_SPECS:
        cohort = RNG.choice(COHORTS, size=n, p=dist)
        age = np.clip(RNG.normal(age_m, 4.0, size=n), 18, 75).round().astype(int)
        logins = np.clip(RNG.normal(logins_m, 2.0, size=n), 0.0, None).round(1)
        multi_currency = RNG.binomial(1, mc_p, size=n).astype(bool)
        family_status = RNG.binomial(1, fam_p, size=n).astype(bool)
        premium = RNG.binomial(1, prem_p, size=n).astype(bool)
        tickets = RNG.poisson(tickets_m, size=n)
        kyc = np.clip(RNG.normal(kyc_m, 1.5, size=n), 0.5, None).round(1)

        df = pd.DataFrame(
            {
                "user_id": np.arange(user_id, user_id + n),
                "jtbd_segment": segment,
                "cohort": cohort,
                "age": age,
                "logins_per_week": logins,
                "multi_currency": multi_currency,
                "family_status": family_status,
                "premium": premium,
                "support_tickets": tickets,
                "kyc_duration_days": kyc,
            }
        )
        user_id += n
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    df = generate_users()
    df.to_csv(DATA_DIR / "volta_jtbd_segments.csv", index=False)

    print(f"Generated {len(df):,} users across {df['jtbd_segment'].nunique()} JTBD segments")
    print("Wrote: volta_jtbd_segments.csv")
    print("\nCohort distribution by JTBD segment (row %):")
    ct = pd.crosstab(df["jtbd_segment"], df["cohort"], normalize="index") * 100
    ct = ct.reindex(index=list(SEGMENT_NAMES)).rename(index=SEGMENT_NAMES)
    print(ct.round(1).to_string())


if __name__ == "__main__":
    main()
