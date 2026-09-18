"""Generate synthetic panel data for the causal (difference-in-differences) layer.

Produces `volta_causal_kyc.csv` consumed by `volta_causal_kyc.py`.

Design — a natural-experiment panel around the Sep 2024 KYC fix:

  two KYC entry flows share the same month-by-month trend in the pre-period
  (parallel trends hold by construction), but the fix only changes the
  in-app flow:

    in_app_kyc    (treated)    — subject to the KYC progress-bar fix
    partner_kyc   (comparison) — agent-assisted flow, UX fix does not apply

  The generator injects a *known* treatment effect (the true ATT) on three
  outcomes, so the difference-in-differences estimator can be checked against
  a ground truth:

    activated    +0.057   (matches Project 2's +5.72pp activation lift)
    retained_m1  +0.085
    retained_m3  +0.090   (matches the +9.2pp M3 retention claim)

  Covariates (age_group, device, pre_activity) drive retention and differ
  slightly between flows, so covariate balance and propensity overlap are
  non-trivial diagnostics rather than a foregone conclusion.

Everything is synthetic and seeded — the "estimate" is a methods
demonstration, not an empirical finding about a real bank.

Run from the repo root:
    uv run python generate_causal_kyc_data.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

# 24 monthly signup cohorts (2023-01 .. 2024-12): 20 pre, 4 post.
MONTHS = pd.date_range("2023-01-01", periods=24, freq="MS")
CUTOFF = "2024-09"
N_PER_COHORT = 3500
TREATED_SHARE = 0.60

# Retention baseline (comparison flow, first cohort) and shared monthly drift.
BASE_ACTIVATED = 0.48
BASE_M1 = 0.44
BASE_M3 = 0.30
TREND_PER_MONTH = 0.0015
SEG_LEVEL_EFFECT = -0.02  # treated flow starts slightly below comparison

# True average treatment effects on the treated (known by construction).
# Retention is affected both directly by the fix and indirectly through
# activation, so we declare the *total* effect (what a DiD identifies) and
# derive the direct coefficient the generator actually injects.
ATT_ACTIVATED = 0.057
ATT_M1_TOTAL = 0.085
ATT_M3_TOTAL = 0.090

# Covariate effects (interview-realistic directions).
AGE_EFFECT = {"18-24": -0.010, "25-34": 0.010, "35-44": 0.0, "45+": -0.040}
DEVICE_EFFECT = {"ios": 0.012, "android": -0.008, "web": 0.0}
PRE_ACTIVITY_EFFECT = 0.030  # per +1 SD of first-30d logins
ACTIVATION_CARRY_M1 = 0.20
ACTIVATION_CARRY_M3 = 0.15

# Direct effects net of the activation channel (what is added to the DGP).
ATT_M1_DIRECT = ATT_M1_TOTAL - ACTIVATION_CARRY_M1 * ATT_ACTIVATED
ATT_M3_DIRECT = ATT_M3_TOTAL - ACTIVATION_CARRY_M3 * ATT_ACTIVATED

AGE_CHOICES = ["18-24", "25-34", "35-44", "45+"]
DEVICE_CHOICES = ["ios", "android", "web"]

# (flow, treated, age probabilities, device probabilities) — the two flows
# differ only modestly, so pre-period balance stays under the SMD gate.
FLOW_SPECS: list[tuple[str, int, list[float], list[float]]] = [
    ("in_app_kyc", 1, [0.16, 0.31, 0.29, 0.24], [0.29, 0.26, 0.45]),
    ("partner_kyc", 0, [0.12, 0.27, 0.30, 0.31], [0.24, 0.25, 0.51]),
]


def _clip(p: np.ndarray) -> np.ndarray:
    return np.clip(p, 0.01, 0.99)


def generate_panel() -> pd.DataFrame:
    """Build the user-level DiD panel with a known treatment effect."""
    rows: list[dict[str, object]] = []
    user_id = 0
    for month_index, month in enumerate(MONTHS):
        cohort = month.strftime("%Y-%m")
        post = int(cohort >= CUTOFF)
        for flow, treated, age_p, dev_p in FLOW_SPECS:
            n = int(round(N_PER_COHORT * (TREATED_SHARE if treated else 1 - TREATED_SHARE)))
            age = RNG.choice(AGE_CHOICES, size=n, p=age_p)
            device = RNG.choice(DEVICE_CHOICES, size=n, p=dev_p)
            # Pre-activity is mildly higher in the in-app flow (selection).
            pre_activity = RNG.normal(8.0 + 0.3 * treated, 3.0, size=n)

            age_eff = np.array([AGE_EFFECT[a] for a in age])
            dev_eff = np.array([DEVICE_EFFECT[d] for d in device])
            activity_eff = PRE_ACTIVITY_EFFECT * ((pre_activity - pre_activity.mean()) / 3.0)
            cov = age_eff + dev_eff + activity_eff

            trend = TREND_PER_MONTH * month_index
            did = (ATT_ACTIVATED, ATT_M1_DIRECT, ATT_M3_DIRECT)

            p_act = _clip(
                np.full(n, BASE_ACTIVATED)
                + trend
                + SEG_LEVEL_EFFECT * treated
                + did[0] * treated * post
                + cov
            )
            activated = (RNG.random(n) < p_act).astype(int)

            p_m1 = _clip(
                np.full(n, BASE_M1)
                + trend
                + SEG_LEVEL_EFFECT * treated
                + did[1] * treated * post
                + cov
                + ACTIVATION_CARRY_M1 * activated
            )
            retained_m1 = (RNG.random(n) < p_m1).astype(int)

            p_m3 = _clip(
                np.full(n, BASE_M3)
                + trend
                + SEG_LEVEL_EFFECT * treated
                + did[2] * treated * post
                + cov
                + ACTIVATION_CARRY_M3 * activated
            )
            retained_m3 = (RNG.random(n) < p_m3).astype(int)

            for i in range(n):
                user_id += 1
                rows.append(
                    {
                        "user_id": user_id,
                        "cohort": cohort,
                        "month_index": month_index,
                        "segment": flow,
                        "treated": treated,
                        "post": post,
                        "age_group": str(age[i]),
                        "device": str(device[i]),
                        "pre_activity": round(float(pre_activity[i]), 3),
                        "activated": int(activated[i]),
                        "retained_m1": int(retained_m1[i]),
                        "retained_m3": int(retained_m3[i]),
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    df = generate_panel()
    df.to_csv(DATA_DIR / "volta_causal_kyc.csv", index=False)

    print(f"Generated {len(df):,} users across {df['cohort'].nunique()} cohorts")
    print(f"Cutoff: {CUTOFF} (pre < cutoff <= post)")
    print("Wrote: volta_causal_kyc.csv")

    print("\nRaw pre/post means by flow (M3 retention):")
    g = df.groupby(["segment", "post"])["retained_m3"].mean().unstack()
    print(g.round(4).to_string())

    print("\nTrue TOTAL ATT injected (ground truth for the DiD check):")
    print(f"  activated   +{ATT_ACTIVATED:.3f}")
    print(f"  retained_m1 +{ATT_M1_TOTAL:.3f}  (direct {ATT_M1_DIRECT:.3f} + activation channel)")
    print(f"  retained_m3 +{ATT_M3_TOTAL:.3f}  (direct {ATT_M3_DIRECT:.3f} + activation channel)")


if __name__ == "__main__":
    main()
