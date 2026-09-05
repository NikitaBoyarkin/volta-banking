"""Generate synthetic A/B test data for the Volta KYC progress-bar experiment.

Produces two CSVs consumed by `volta_ab_testing.py`:
  - volta_ab_experiment.csv : user-level outcomes + covariates
  - segment_results.csv     : per-segment-value lift + p-value (Section 5 & 9.1)

Experiment parameters (match the analysis script docstring):
  - Primary metric: KYC Start -> KYC Complete conversion
  - Baseline CR (control): ~0.566
  - MDE: +5pp absolute (overall)
  - Split: 50/50 user-level
  - Heterogeneous effects: age 35-44 and android benefit most; 45+ and app_store weak

The `pre_kyc_rate` column is a pre-experiment engagement covariate correlated with
the outcome, so CUPED (Section 9.3) can activate when this data is loaded.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from utils.common import DATA_DIR

N_PER_ARM = 5000
SEED = 42
RNG = np.random.default_rng(SEED)

BASE_CONTROL = 0.566
BASE_LIFT = 0.05

# Small per-segment offsets on the control rate (additive on the logit-ish scale,
# kept small so the overall mean stays ~0.566).
CONTROL_OFFSET = {
    "age_group=18-24": -0.04,
    "age_group=25-34": 0.01,
    "age_group=35-44": 0.03,
    "age_group=45+": -0.06,
    "device=android": -0.02,
    "device=ios": 0.02,
    "device=web": -0.01,
    "channel=app_store": 0.01,
    "channel=google_play": 0.02,
    "channel=website": -0.03,
    "channel=referral": 0.04,
}
# Per-segment additive lift on top of the +5pp base (heterogeneous treatment effect).
LIFT_DELTA = {
    "age_group=18-24": -0.01,
    "age_group=25-34": 0.00,
    "age_group=35-44": 0.03,
    "age_group=45+": -0.04,
    "device=android": 0.02,
    "device=ios": -0.01,
    "device=web": 0.00,
    "channel=app_store": -0.03,
    "channel=google_play": 0.01,
    "channel=website": 0.00,
    "channel=referral": 0.02,
}

AGE_GROUPS = ["18-24", "25-34", "35-44", "45+"]
DEVICES = ["android", "ios", "web"]
CHANNELS = ["app_store", "google_play", "website", "referral"]


def _clip(p: np.ndarray, lo: float = 0.05, hi: float = 0.95) -> np.ndarray:
    return np.clip(p, lo, hi)


def generate_users(n: int, group: str) -> pd.DataFrame:
    """Generate n users for one arm with heterogeneous per-segment rates."""
    age = RNG.choice(AGE_GROUPS, size=n, p=[0.20, 0.35, 0.30, 0.15])
    device = RNG.choice(DEVICES, size=n, p=[0.45, 0.40, 0.15])
    channel = RNG.choice(CHANNELS, size=n, p=[0.30, 0.30, 0.25, 0.15])

    control_p = np.full(n, BASE_CONTROL, dtype=float)
    lift = np.full(n, BASE_LIFT, dtype=float)
    for agg, vals in [("age_group", age), ("device", device), ("channel", channel)]:
        for v in np.unique(vals):
            key = f"{agg}={v}"
            mask = vals == v
            control_p[mask] += CONTROL_OFFSET.get(key, 0.0)
            lift[mask] += LIFT_DELTA.get(key, 0.0)
    control_p = _clip(control_p)
    lift = np.clip(lift, -0.02, 0.15)

    p = control_p + (lift if group == "treatment" else 0.0)
    p = _clip(p)
    kyc_completed = RNG.binomial(1, p)

    # Pre-experiment covariate: correlated with the user's underlying propensity,
    # NOT with treatment assignment (CUPED assumption). Adds noise so theta != 1.
    pre_kyc_rate = _clip(control_p + RNG.normal(0, 0.08, size=n))

    # Guardrail metrics — MUST be unaffected by treatment (the whole point of a
    # guardrail is to confirm the feature didn't break something outside the
    # primary metric). They depend on kyc_completed (completers churn less and
    # generate more revenue) but NOT on `group`, so the guardrail t-test should
    # land non-significant. This is what a clean guardrail looks like.
    churn_p = np.where(kyc_completed == 1, 0.06, 0.34) + RNG.normal(0, 0.02, size=n)
    churned_30d = (RNG.random(n) < _clip(churn_p, 0.02, 0.6)).astype(int)
    # 30-day revenue: completers transact more. Lognormal-ish, non-negative.
    rev_base = np.where(kyc_completed == 1, 18.0, 3.5)
    revenue_30d_eur = np.clip(
        rev_base + RNG.normal(0, 6.0, size=n) * np.where(kyc_completed == 1, 1.0, 0.6),
        0.0,
        None,
    )

    return pd.DataFrame(
        {
            "customer_id": np.arange(n) + (0 if group == "control" else N_PER_ARM),
            "group": group,
            "age_group": age,
            "device": device,
            "channel": channel,
            "pre_kyc_rate": pre_kyc_rate.round(4),
            "kyc_completed": kyc_completed,
            "churned_30d": churned_30d,
            "revenue_30d_eur": revenue_30d_eur.round(2),
        }
    )


def compute_segment_results(df: pd.DataFrame) -> pd.DataFrame:
    """Per-segment-value control/treatment means, lift (pp), p-value, significance."""
    rows = []
    for col, vals in [
        ("age_group", df["age_group"].unique()),
        ("device", df["device"].unique()),
        ("channel", df["channel"].unique()),
    ]:
        for v in vals:
            sub = df[df[col] == v]
            c = sub[sub["group"] == "control"]["kyc_completed"]
            t = sub[sub["group"] == "treatment"]["kyc_completed"]
            if len(c) == 0 or len(t) == 0:
                continue
            control_rate = c.mean()
            treatment_rate = t.mean()
            lift_pp = (treatment_rate - control_rate) * 100
            table = np.array(
                [
                    [t.sum(), len(t) - t.sum()],
                    [c.sum(), len(c) - c.sum()],
                ]
            )
            _, p_value, _, _ = stats.chi2_contingency(table)
            rows.append(
                {
                    "segment": f"{col}={v}",
                    "control": round(control_rate, 4),
                    "treatment": round(treatment_rate, 4),
                    "lift": round(lift_pp, 1),
                    "p_value": round(p_value, 4),
                    "significant": bool(p_value < 0.05),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    control = generate_users(N_PER_ARM, "control")
    treatment = generate_users(N_PER_ARM, "treatment")
    df = pd.concat([control, treatment], ignore_index=True)

    seg = compute_segment_results(df)

    df.to_csv(DATA_DIR / "volta_ab_experiment.csv", index=False)
    seg.to_csv(DATA_DIR / "segment_results.csv", index=False)

    print(f"Generated {len(df)} users ({N_PER_ARM}/arm)")
    print(f"  Control CR:   {control['kyc_completed'].mean():.3f}")
    print(f"  Treatment CR: {treatment['kyc_completed'].mean():.3f}")
    print(
        f"  Overall lift: {(treatment['kyc_completed'].mean() - control['kyc_completed'].mean()) * 100:+.1f}pp"
    )
    print(f"  Segments:     {len(seg)} ({seg['significant'].sum()} significant at p<0.05)")
    print("\nSegment results:")
    print(seg.to_string(index=False))
    print("\nWrote: volta_ab_experiment.csv, segment_results.csv")


if __name__ == "__main__":
    main()
