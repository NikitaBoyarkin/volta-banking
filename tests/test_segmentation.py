"""Tests for volta_segmentation.py — Project 4 segmentation analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

import volta_segmentation as vs


def _make_separable_data(n_per_cluster: int = 200) -> np.ndarray:
    """Four well-separated 6-D Gaussian clusters → elbow should land on K=4."""
    rng = np.random.default_rng(0)
    centers = np.array(
        [
            [0, 0, 0, 0, 0, 0],
            [10, 10, 10, 10, 10, 10],
            [20, 20, 20, 20, 20, 20],
            [30, 30, 30, 30, 30, 30],
        ],
        dtype=float,
    )
    return np.vstack([rng.normal(c, 1.0, size=(n_per_cluster, 6)) for c in centers])


def test_select_k_lands_on_four() -> None:
    X = _make_separable_data()
    k_info = vs.select_k(X)
    assert k_info["optimal_k"] == 4
    # Inertia must be monotonically decreasing as K grows.
    assert all(
        k_info["inertias"][i] > k_info["inertias"][i + 1]
        for i in range(len(k_info["inertias"]) - 1)
    )


def test_assign_segment_names_maps_by_revenue() -> None:
    df = pd.DataFrame(
        {
            "cluster": [0, 0, 1, 1, 2, 2, 3, 3],
            "monthly_revenue": [5, 5, 10, 10, 20, 20, 40, 40],
        }
    )
    df, mapping = vs.assign_segment_names(df, 4)
    assert mapping[3] == "Power Users"  # highest revenue → rank 1
    assert mapping[2] == "Growth Users"
    assert mapping[1] == "Casual Users"
    assert mapping[0] == "Dormant Users"
    assert df["segment"].nunique() == 4


def test_fit_clusters_adds_columns() -> None:
    X = _make_separable_data(n_per_cluster=50)
    df = pd.DataFrame(X, columns=vs.CLUSTERING_FEATURES)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[vs.CLUSTERING_FEATURES])
    df, km, pca, Xp = vs.fit_clusters(df, X_scaled, 4)
    assert {"cluster", "pca1", "pca2"} <= set(df.columns)
    assert df["cluster"].nunique() == 4
    assert Xp.shape == (len(df), 2)


def test_per_cluster_silhouette_well_separated_clusters_score_high() -> None:
    X = _make_separable_data(n_per_cluster=100)
    labels = np.repeat([0, 1, 2, 3], 100)
    sil = vs.per_cluster_silhouette(X, labels)
    assert set(sil) == {0, 1, 2, 3}
    # Well-separated Gaussian clusters → every cluster mean silhouette ≥ 0.5.
    assert all(v >= 0.5 for v in sil.values())


def test_seg_size_pct() -> None:
    seg_summary = pd.DataFrame(
        {"n_users": [100, 300], "total_monthly_rev": [1000, 3000]},
        index=["Power Users", "Casual Users"],
    )
    assert vs._seg_size_pct(seg_summary, "Power Users") == 25.0
    assert np.isnan(vs._seg_size_pct(seg_summary, "Missing"))


# ── Sprint 1: S1-S3 ──────────────────────────────────────────────────────────
def _make_clustered_df() -> tuple[pd.DataFrame, np.ndarray]:
    """4 separable clusters with segment names assigned."""
    rng = np.random.default_rng(0)
    centers = np.array(
        [
            [0, 0, 0, 0, 0, 0],
            [10, 10, 10, 10, 10, 10],
            [20, 20, 20, 20, 20, 20],
            [30, 30, 30, 30, 30, 30],
        ],
        dtype=float,
    )
    X = np.vstack([rng.normal(c, 1.0, size=(100, 6)) for c in centers])
    df = pd.DataFrame(X, columns=vs.CLUSTERING_FEATURES)
    df["monthly_revenue"] = np.repeat([5, 15, 25, 40], 100)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[vs.CLUSTERING_FEATURES])
    df, km, pca, Xp = vs.fit_clusters(df, X_scaled, 4)
    df, c2s = vs.assign_segment_names(df, 4)
    return df, X_scaled


def test_centroid_zscores_shape_and_sign() -> None:
    df, _ = _make_clustered_df()
    z = vs.centroid_zscores(df)
    assert list(z.columns) == vs.CLUSTERING_FEATURES
    assert len(z) == 4
    # Power Users (highest revenue) should be above average on all features.
    assert (z.loc["Power Users"] > 0).all()
    # Dormant Users (lowest) below average on most features.
    assert (z.loc["Dormant Users"] < 0).sum() >= 4


def test_segment_stability_high_for_separable_data() -> None:
    df, X_scaled = _make_clustered_df()
    stab = vs.segment_stability(df, X_scaled, 4, n_boot=5)
    assert stab["n_boot"] == 5
    assert stab["mean_ari"] > 0.85  # well-separated → very stable


def test_plot_silhouette_writes_png(tmp_path) -> None:
    df, X_scaled = _make_clustered_df()
    out = tmp_path / "sil.png"
    path = vs.plot_silhouette(X_scaled, df["cluster"].values, {0: "A", 1: "B", 2: "C", 3: "D"}, out)
    assert path == out
    assert out.exists()
    assert out.stat().st_size > 1000
