"""Generate synthetic win-back experiment data for dormant 45+ users.

Produces `volta_dormant_winback.csv` consumed by `volta_dormant_winback.py`:

  user_id, jtbd_segment, dormancy_bucket, group, balance_eur, prior_logins,
  reactivated_60d, retained_m3, arpu_eur

Design — the audit's v2 risk #5: "assisted onboarding actually recovers Dormant
45+ (dormancy is UX, but recovery is unproven)". Project 13 showed dormancy
concentrates in Digital Newcomers 45+ and looks UX-driven; Project 18 showed
assisted *acquisition* doesn't pay back. This dataset tests assisted
*reactivation* — a different economics, because there is no CAC to recover.

Three arms, randomized within four dormancy buckets:

  control     — automated email/push win-back (cheap)
  light_touch — guided in-app flow + SMS with optional callback (mid cost)
  human       — support-agent call + simplified flow (high cost)

Reactivation probability rises with the intervention and falls with dormancy
depth; the light-touch arm captures a fixed fraction of the human lift. The
analysis must show the mechanism works AND find the targeting/ROI boundary —
mass human calls are unaffordable on a low-ARPU segment.

Run from the repo root:
    uv run python generate_dormant_winback_data.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

DORMANCY_BUCKETS = ["30-60d", "60-90d", "90-180d", "180d+"]
BUCKET_WEIGHTS = [0.30, 0.25, 0.25, 0.20]
ARMS = ["control", "light_touch", "human"]
N_PER_CELL = 3000

# Control (automated) reactivation rate by dormancy depth — deeper = colder.
CONTROL_RATE: dict[str, float] = {
    "30-60d": 0.090,
    "60-90d": 0.060,
    "90-180d": 0.035,
    "180d+": 0.015,
}
# Human-assisted multiplier vs control (Project 13: dormancy is UX, so a human
# + simplified flow should move the recently dormant most).
HUMAN_MULT: dict[str, float] = {
    "30-60d": 2.2,
    "60-90d": 2.0,
    "90-180d": 1.6,
    "180d+": 1.2,
}
# The light-touch arm captures this fraction of the human *incremental* lift.
LIGHT_FRACTION = 0.60

# Cost per treated user (EUR) — automated vs guided vs human call.
COST_PER_ARM: dict[str, float] = {"control": 0.50, "light_touch": 2.50, "human": 11.00}
# LTV of a reactivated user by dormancy depth (recency → stickiness, EUR).
LTV_REACTIVATED: dict[str, float] = {
    "30-60d": 85.0,
    "60-90d": 75.0,
    "90-180d": 62.0,
    "180d+": 50.0,
}


def reactivation_probability(arm: str, bucket: str) -> float:
    """Probability of reactivation at 60 days for one arm × bucket."""
    c = CONTROL_RATE[bucket]
    human = c * HUMAN_MULT[bucket]
    if arm == "control":
        return c
    if arm == "human":
        return human
    return c + LIGHT_FRACTION * (human - c)  # light_touch


def generate_users() -> pd.DataFrame:
    """One row per dormant 45+ user: arm, dormancy, reactivation outcome."""
    rows: list[dict[str, float | str | int]] = []
    user_id = 0
    for arm in ARMS:
        for bucket in DORMANCY_BUCKETS:
            p = reactivation_probability(arm, bucket)
            for _ in range(N_PER_CELL):
                user_id += 1
                # Engagement covariates (higher balance → more likely to return).
                balance = max(0.0, float(RNG.lognormal(5.5, 0.8)))
                prior_logins = max(1.0, float(RNG.normal(6.0, 2.5)))
                engagement = 1.0 + 0.00008 * (balance - 300.0) + 0.02 * (prior_logins - 6.0)
                p_eff = float(np.clip(p * max(0.3, engagement), 0.0005, 0.95))
                reactivated = int(RNG.random() < p_eff)
                retained = int(reactivated and RNG.random() < 0.62)
                rows.append(
                    {
                        "user_id": user_id,
                        "jtbd_segment": "digital_newcomers",
                        "dormancy_bucket": bucket,
                        "group": arm,
                        "balance_eur": round(balance, 2),
                        "prior_logins": round(prior_logins, 1),
                        "reactivated_60d": reactivated,
                        "retained_m3": retained,
                        "arpu_eur": 3.40,
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    df = generate_users()
    df.to_csv(DATA_DIR / "volta_dormant_winback.csv", index=False)

    print(f"Generated {len(df):,} dormant 45+ users across {len(ARMS)} arms")
    print("Wrote: volta_dormant_winback.csv")

    print("\n60-day reactivation (%) by arm × dormancy:")
    pivot = df.pivot_table(
        index="dormancy_bucket", columns="group", values="reactivated_60d", aggfunc="mean"
    ).mul(100)
    print(pivot.reindex(DORMANCY_BUCKETS)[ARMS].round(2).to_string())

    print("\nCost per treated user (EUR):", COST_PER_ARM)
    print("LTV per reactivated user (EUR):", LTV_REACTIVATED)


if __name__ == "__main__":
    main()
