"""Generate synthetic user-feature data for the Volta segmentation analysis.

Produces two CSVs consumed by `volta_segmentation.py`:
  - volta_users_features.csv : per-user behavioral features
  - segment_profiles.csv      : pre-aggregated segment profile (index = segment name)

`volta_users_features.csv` columns:
  user_id, monthly_tx_count, avg_tx_value_eur, savings_balance_eur,
  logins_per_week, p2p_transfers_month, tenure_days, monthly_revenue

`segment_profiles.csv` columns (index = segment):
  n_users, avg_rev, revenue_share, pct_premium, avg_tx, avg_savings,
  avg_logins, avg_tenure, total_monthly_rev

Design — four cleanly separable behavioral segments so the elbow/silhouette
land at K=4 and revenue ranking maps to Power > Growth > Casual > Dormant:

  segment   tx   tx_val  savings  logins  p2p  tenure  rev   premium
  Power     38   45      5500     11      14   420      32    0.77
  Growth    20   28      2400     7        8   260      13    0.30
  Casual    11   15       250     4        3   170       5.5   0.08
  Dormant    3    8        60     1.5     0.8  310       1.8   0.02

`monthly_revenue` is intentionally NOT a clustering feature in the analysis
script (it is the ranking target); it is generated here only so the script's
describe() and revenue-ranking work on real numbers.

Run from the repo root:
    uv run python generate_segmentation_data.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

# (segment_label, n_users, mean vector for the 6 clustering features +
# monthly_revenue + premium probability). Feature order MUST match
# clustering_features below.
# cols: tx, tx_val, savings, logins, p2p, tenure, rev, premium_p
SEGMENT_SPECS: list[tuple[str, int, tuple[float, ...], float]] = [
    ("power", 6000, (38.0, 45.0, 5500.0, 11.0, 14.0, 420.0, 32.0), 0.77),
    ("growth", 12000, (20.0, 28.0, 2400.0, 7.0, 8.0, 260.0, 13.0), 0.30),
    ("casual", 16000, (11.0, 15.0, 250.0, 4.0, 3.0, 170.0, 5.5), 0.08),
    ("dormant", 16000, (3.0, 8.0, 60.0, 1.5, 0.8, 310.0, 1.8), 0.02),
]
# Per-feature noise SDs (kept small relative to between-segment gaps so the
# 4 clusters stay separable and the silhouette peaks at K=4).
NOISE = np.array([4.0, 6.0, 500.0, 1.5, 2.0, 40.0, 3.0])

CLUSTERING_FEATURES = [
    "monthly_tx_count",
    "avg_tx_value_eur",
    "savings_balance_eur",
    "logins_per_week",
    "p2p_transfers_month",
    "tenure_days",
]
FEATURE_COLS = [*CLUSTERING_FEATURES, "monthly_revenue"]

# Final display names, ordered by descending revenue (matches the script's
# revenue-rank -> segment-name mapping).
NAME_BY_REVENUE_RANK = ["Power Users", "Growth Users", "Casual Users", "Dormant Users"]


def generate_users() -> pd.DataFrame:
    """Generate one row per user across the four segments."""
    frames: list[pd.DataFrame] = []
    user_id = 0
    for _label, n, means, premium_p in SEGMENT_SPECS:
        means_arr = np.array(means, dtype=float)
        X = means_arr[:7] + RNG.normal(0.0, NOISE, size=(n, 7))
        # Clip non-negative features; floor activity features.
        X[:, 0] = np.clip(X[:, 0], 0.0, None)  # tx_count
        X[:, 1] = np.clip(X[:, 1], 0.0, None)  # tx_value
        X[:, 2] = np.clip(X[:, 2], 0.0, None)  # savings
        X[:, 3] = np.clip(X[:, 3], 0.5, None)  # logins
        X[:, 4] = np.clip(X[:, 4], 0.0, None)  # p2p
        X[:, 5] = np.clip(X[:, 5], 1.0, None)  # tenure
        X[:, 6] = np.clip(X[:, 6], 0.0, None)  # revenue

        df = pd.DataFrame(X, columns=FEATURE_COLS)
        df.insert(0, "user_id", np.arange(user_id, user_id + n))
        df["_true_segment"] = _label
        df["_is_premium"] = RNG.binomial(1, premium_p, size=n)
        user_id += n
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def compute_segment_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per true-segment, then name by revenue rank (matches the
    analysis script's revenue-ranking convention)."""
    df = df.copy()
    # Revenue ranking of the TRUE segments -> display names.
    seg_rev = df.groupby("_true_segment")["monthly_revenue"].mean().sort_values(ascending=False)
    name_map = {seg: NAME_BY_REVENUE_RANK[i] for i, seg in enumerate(seg_rev.index)}

    rows: list[dict[str, float | str]] = []
    for seg, sub in df.groupby("_true_segment"):
        n_users = len(sub)
        total_rev = float(sub["monthly_revenue"].sum())
        rows.append(
            {
                "segment": name_map[seg],
                "n_users": n_users,
                "avg_rev": round(float(sub["monthly_revenue"].mean()), 2),
                "revenue_share": round(total_rev / df["monthly_revenue"].sum() * 100, 1),
                "pct_premium": round(float(sub["_is_premium"].mean()), 4),
                "avg_tx": round(float(sub["monthly_tx_count"].mean()), 1),
                "avg_savings": round(float(sub["savings_balance_eur"].mean()), 0),
                "avg_logins": round(float(sub["logins_per_week"].mean()), 1),
                "avg_tenure": round(float(sub["tenure_days"].mean()), 0),
                "total_monthly_rev": round(total_rev, 0),
            }
        )
    prof = pd.DataFrame(rows).set_index("segment")
    # Order index by the canonical revenue-descending order.
    prof = prof.loc[[n for n in NAME_BY_REVENUE_RANK if n in prof.index]]
    return prof


def _verify_k4_elbow(df: pd.DataFrame) -> None:
    """Print inertia + silhouette for K=2..8 so a reviewer can confirm K=4 is
    data-driven (used by the analysis script's Phase-6 k-selection fix)."""
    from sklearn.metrics import silhouette_score

    X = StandardScaler().fit_transform(df[CLUSTERING_FEATURES])
    # silhouette_score is O(n^2); subsample to 10k (matches volta_segmentation.py)
    sample_idx = np.random.default_rng(SEED).choice(len(X), size=10_000, replace=False)
    X_sample = X[sample_idx]
    print("\nK-selection diagnostics (generator sanity check):")
    print(f"{'K':<4}{'Inertia':<14}{'Silhouette':<12}")
    for k in range(2, 9):
        km = KMeans(n_clusters=k, random_state=SEED, n_init=10).fit(X)
        sil = silhouette_score(X_sample, km.labels_[sample_idx])
        print(f"{k:<4}{km.inertia_:<14.1f}{sil:<12.3f}")


def main() -> None:
    df = generate_users()
    profiles = compute_segment_profiles(df)

    features = df.drop(columns=["_true_segment", "_is_premium"])
    features.to_csv(DATA_DIR / "volta_users_features.csv", index=False)
    profiles.to_csv(DATA_DIR / "segment_profiles.csv")

    print(f"Generated {len(features)} users across {len(profiles)} segments")
    print("Wrote: volta_users_features.csv, segment_profiles.csv")
    print("\nSegment profiles:")
    print(profiles.to_string())
    _verify_k4_elbow(df)


if __name__ == "__main__":
    main()
