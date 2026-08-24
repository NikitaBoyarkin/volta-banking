"""Generate synthetic cohort-retention data for the Volta retention analysis.

Produces `cohort_retention_matrix.csv` consumed by `volta_retention_analysis.py`.

Schema (index = cohort, YYYY-MM, lexicographically comparable):
  - cohort_size : int, new activated users in that monthly cohort
  - month_0 .. month_11 : fraction of the cohort still active in month N
                          (month_0 = 1.0 by construction)

Design:
  - 12 monthly cohorts: 2024-01 .. 2024-12.
  - Pre-fix cohorts (2024-01..2024-08): retention follows the pre-fix curve
    (M1~0.52, M3~0.31, M6~0.18) — matches the script's hardcoded pre-fix curve.
  - Post-fix cohorts (2024-09..2024-12): retention follows the post-fix curve
    (M1~0.64, M3~0.41, M6~0.28) — the Sep 2024 KYC-fix step-change.
  - Per-cohort noise so the pre/post M3 t-test has real variance and lands
    significant (post > pre), exercising the script's significance branch.

Run from the repo root:
    uv run python generate_retention_data.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

# Base retention curves — kept identical to the hardcoded curves in
# volta_retention_analysis.py so the narrative numbers are consistent.
PRE_FIX_CURVE = np.array(
    [
        1.00,
        0.52,
        0.38,
        0.31,
        0.26,
        0.23,
        0.21,
        0.19,
        0.18,
        0.17,
        0.16,
        0.15,
    ]
)
POST_FIX_CURVE = np.array(
    [
        1.00,
        0.64,
        0.49,
        0.41,
        0.36,
        0.33,
        0.31,
        0.29,
        0.28,
        0.27,
        0.26,
        0.25,
    ]
)

FIX_CUTOFF = "2024-09"  # cohorts >= this month are "post-fix"
NOISE_STD = 0.02  # per-cell retention noise
COHORT_SIZE_MEAN = 5000
COHORT_SIZE_STD = 400


def _cohorts() -> list[str]:
    """Return the 12 monthly cohort labels 2024-01 .. 2024-12."""
    months = pd.date_range("2024-01-01", periods=12, freq="MS")
    return [m.strftime("%Y-%m") for m in months]


def generate_cohort_matrix() -> pd.DataFrame:
    """Build the cohort retention matrix with per-cohort retention noise."""
    rows: list[dict[str, float]] = []
    for cohort in _cohorts():
        base = POST_FIX_CURVE if cohort >= FIX_CUTOFF else PRE_FIX_CURVE
        noise = RNG.normal(0.0, NOISE_STD, size=base.shape)
        retention = np.clip(base + noise, 0.0, 1.0)
        retention[0] = 1.0  # M0 is always 100%

        size = int(round(COHORT_SIZE_MEAN + RNG.normal(0.0, COHORT_SIZE_STD)))

        record: dict[str, float] = {"cohort": cohort, "cohort_size": size}
        for m in range(12):
            record[f"month_{m}"] = round(float(retention[m]), 4)
        rows.append(record)

    df = pd.DataFrame(rows).set_index("cohort")
    return df


def main() -> None:
    df = generate_cohort_matrix()
    out_path = DATA_DIR / "cohort_retention_matrix.csv"
    df.to_csv(out_path)

    pre = df.loc[df.index < FIX_CUTOFF, "month_3"]
    post = df.loc[df.index >= FIX_CUTOFF, "month_3"]

    print(f"Generated {len(df)} cohorts ({out_path})")
    print(f"  Pre-fix cohorts  ({len(pre)}):  M3 mean = {pre.mean():.3f}")
    print(f"  Post-fix cohorts ({len(post)}): M3 mean = {post.mean():.3f}")
    print(f"  M3 lift: +{(post.mean() - pre.mean()) * 100:.1f}pp")
    print("\nCohort summary:")
    print(df[["cohort_size", "month_1", "month_3", "month_6"]].to_string())


if __name__ == "__main__":
    main()
