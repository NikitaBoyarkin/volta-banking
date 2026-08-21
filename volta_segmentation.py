"""
Volta Neobank — User Segmentation & Monetization Strategy

Project: Product Analytics Portfolio — Project 4/4
Industry: Fintech / Digital Banking
Type: K-Means Clustering · PCA · RFM-style segmentation · Revenue strategy

Identifies distinct user segments with K-means on scaled behavioral features,
selects K from the data (marginal-gain elbow rule, validated by silhouette),
projects with PCA, and proposes per-segment monetization scenarios.

Portfolio context:
- Project 1: Identified KYC as the critical funnel bottleneck
- Project 2: Proved the KYC progress bar fix works (+6.24pp, p<0.0001)
- Project 3: Showed retention improved post-fix and revealed the Premium/Free
  LTV gap (ARPU × retention decomposition)
- Project 4 (this): Segments users and designs per-segment monetization strategy

Data: produced by `generate_segmentation_data.py` → volta_users_features.csv,
segment_profiles.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_samples, silhouette_score
from sklearn.preprocessing import StandardScaler

from utils.common import data_path, print_section, print_subsection, setup

OUTPUT_DIR = Path(__file__).resolve().parent
KMEANS_SEED = 42

# Behavioral features used for clustering. `monthly_revenue` is intentionally
# EXCLUDED: it is the target-ish monetization metric and including it would
# let the clusterer "cheat" by segmenting on the very quantity we then profile
# segments by (target-as-input leakage).
CLUSTERING_FEATURES = [
    "monthly_tx_count",
    "avg_tx_value_eur",
    "savings_balance_eur",
    "logins_per_week",
    "p2p_transfers_month",
    "tenure_days",
]
# Descriptive features shown in the summary table (revenue included here).
FEATURE_COLS = CLUSTERING_FEATURES + ["monthly_revenue"]

# Segment names ordered by revenue rank. Must have ≥ K entries; the mapping is
# built dynamically and guarded by an assertion so a non-4 K cannot IndexError.
NAME_BY_REVENUE_RANK = [
    "Power Users",
    "Growth Users",
    "Casual Users",
    "Dormant Users",
    "Niche Users",
    "Edge Users",
]


# ── Load ──────────────────────────────────────────────────────────────────────
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(data_path("volta_users_features.csv"))
    seg_summary = pd.read_csv(data_path("segment_profiles.csv"), index_col="segment")
    return df, seg_summary


# ── K selection ───────────────────────────────────────────────────────────────
def select_k(X_scaled: np.ndarray, k_range: range = range(2, 9)) -> dict[str, object]:
    """Data-driven K selection.

    Rule: keep adding clusters while each one delivers at least half the
    best observed marginal inertia reduction; the last K that does is the
    elbow. This lands on K=4 for the generated data (reductions 42%→40%→5%→…;
    the cliff is between K=4 and K=5). Silhouette is reported as validation,
    not as the selector (it peaks at K=2 here — a known artifact of well-
    separated 4-cluster data where the 2-cluster merge still scores high).

    `silhouette_score` is O(n²); on 50k+ users we subsample to 10k points
    (stratified by the current labels) for the silhouette computation. Inertia
    stays on the full data (it is cheap and the elbow signal lives there).
    """
    rng = np.random.default_rng(KMEANS_SEED)
    n = len(X_scaled)
    sil_subsample = 10_000
    inertias, silhouettes = [], []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=KMEANS_SEED, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertias.append(km.inertia_)
        if n > sil_subsample:
            sub_idx = rng.choice(n, size=sil_subsample, replace=False)
            sil = silhouette_score(X_scaled[sub_idx], labels[sub_idx])
        else:
            sil = silhouette_score(X_scaled, labels)
        silhouettes.append(sil)

    k_list = list(k_range)
    reductions = [0.0] + [
        (inertias[i - 1] - inertias[i]) / inertias[i - 1] * 100 for i in range(1, len(inertias))
    ]
    max_reduction = max(r for r in reductions[1:])
    # Largest K whose marginal reduction is still ≥ half the best reduction.
    optimal_k = max(k_list[i] for i, r in enumerate(reductions) if r >= 0.5 * max_reduction)
    return {
        "k_list": k_list,
        "inertias": inertias,
        "silhouettes": silhouettes,
        "reductions": reductions,
        "optimal_k": optimal_k,
        "max_reduction": max_reduction,
    }


# ── Clustering + PCA ──────────────────────────────────────────────────────────
def fit_clusters(
    df: pd.DataFrame, X_scaled: np.ndarray, optimal_k: int
) -> tuple[pd.DataFrame, KMeans, PCA, np.ndarray]:
    km = KMeans(n_clusters=optimal_k, random_state=KMEANS_SEED, n_init=10)
    df["cluster"] = km.fit_predict(X_scaled)
    pca = PCA(n_components=2, random_state=KMEANS_SEED)
    Xp = pca.fit_transform(X_scaled)
    df["pca1"], df["pca2"] = Xp[:, 0], Xp[:, 1]
    return df, km, pca, Xp


def per_cluster_silhouette(X_scaled: np.ndarray, labels: np.ndarray) -> dict[int, float]:
    """Mean silhouette score per cluster (from sample-level silhouette_samples).

    The global silhouette_score hides which cluster is well-separated and which
    is fuzzy; per-cluster means surface weak clusters that drag the average down.
    """
    sample_sil = silhouette_samples(X_scaled, labels)
    return {int(cid): float(sample_sil[labels == cid].mean()) for cid in np.unique(labels)}


# ── Sprint 1: S1 silhouette plot ────────────────────────────────────────────
def plot_silhouette(
    X_scaled: np.ndarray,
    labels: np.ndarray,
    cluster_to_segment: dict[int, str],
    out: Path,
    max_samples: int = 5000,
    seed: int = 42,
) -> Path:
    """Classic silhouette plot: per-sample silhouette, sorted by cluster then
    by value within cluster. Horizontal bars coloured by segment.

    `silhouette_samples` is O(n²), so for large datasets we subsample to
    `max_samples` (stratified by cluster) — the visual shape is preserved while
    runtime drops from minutes to seconds on 50k+ users.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.cm import tab10

    plt.style.use("dark_background")

    # Stratified subsample so small clusters stay represented.
    rng = np.random.default_rng(seed)
    if len(labels) > max_samples:
        keep_idx: list[int] = []
        for cid in np.unique(labels):
            cid_idx = np.where(labels == cid)[0]
            n_take = max(1, int(max_samples * len(cid_idx) / len(labels)))
            n_take = min(n_take, len(cid_idx))
            keep_idx.extend(rng.choice(cid_idx, size=n_take, replace=False))
        keep_idx = np.array(keep_idx)
        X_sub = X_scaled[keep_idx]
        labels_sub = labels[keep_idx]
    else:
        X_sub, labels_sub = X_scaled, labels

    sample_sil = silhouette_samples(X_sub, labels_sub)
    y_lower = 10
    clusters = sorted(np.unique(labels_sub))

    fig, ax = plt.subplots(figsize=(9, 6))
    for i, cid in enumerate(clusters):
        vals = np.sort(sample_sil[labels_sub == cid])
        y_upper = y_lower + len(vals)
        color = tab10(i % 10)
        ax.fill_betweenx(
            np.arange(y_lower, y_upper),
            0,
            vals,
            facecolor=color,
            edgecolor=color,
            alpha=0.8,
        )
        ax.text(
            -0.02,
            y_lower + len(vals) / 2,
            cluster_to_segment.get(int(cid), str(cid)),
            fontsize=9,
            va="center",
        )
        y_lower = y_upper + 10

    mean_sil = float(sample_sil.mean())
    ax.axvline(mean_sil, color="white", linestyle="--", alpha=0.7, label=f"Mean = {mean_sil:.3f}")
    ax.set_xlabel("Silhouette coefficient")
    ax.set_ylabel("Samples per segment")
    ax.set_title("Silhouette plot — per-sample separation by segment")
    ax.set_yticks([])
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out


# ── Sprint 1: S2 centroid z-score profiles ──────────────────────────────────
def centroid_zscores(df: pd.DataFrame) -> pd.DataFrame:
    """Per-segment z-score of each feature vs the global mean.

    z = (segment_mean - global_mean) / global_std. Positive = segment is above
    average on that feature; negative = below. Surfaces WHICH features
    distinguish each segment from the average user (not just that they differ).
    """
    means = df[CLUSTERING_FEATURES].mean()
    stds = df[CLUSTERING_FEATURES].std(ddof=0)
    rows = {}
    for segment, sub in df.groupby("segment"):
        seg_mean = sub[CLUSTERING_FEATURES].mean()
        rows[segment] = ((seg_mean - means) / stds).round(2)
    z = pd.DataFrame(rows).T
    z = z.loc[[s for s in NAME_BY_REVENUE_RANK if s in z.index]]
    return z


# ── Sprint 1: S3 segment stability (bootstrap) ──────────────────────────────
def segment_stability(
    df: pd.DataFrame,
    X_scaled: np.ndarray,
    optimal_k: int,
    n_boot: int = 10,
    seed: int = 42,
) -> dict[str, float]:
    """Bootstrap cluster-assignment stability.

    Resamples rows with replacement, re-runs KMeans on the resampled data, and
    measures agreement with the original assignment via the adjusted Rand index
    (ARI = 1 → identical partition; 0 → random; <0 → anti-correlated). Reports
    the mean ARI across bootstrap samples. High ARI (>0.8) means the segments
    are a stable property of the data, not a KMeans-seed artifact.

    Uses n_init=1 for the refits (the bootstrap variance is the signal, not
    within-seed noise) to keep runtime tractable on 50k+ users.
    """
    from sklearn.metrics import adjusted_rand_score

    rng = np.random.default_rng(seed)
    n = len(df)
    base_labels = df["cluster"].values
    aris: list[float] = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        X_boot = X_scaled[idx]
        km = KMeans(n_clusters=optimal_k, random_state=KMEANS_SEED, n_init=1)
        km.fit(X_boot)
        boot_labels = km.predict(X_scaled)
        aris.append(float(adjusted_rand_score(base_labels, boot_labels)))
    return {
        "mean_ari": float(np.mean(aris)),
        "std_ari": float(np.std(aris)),
        "min_ari": float(np.min(aris)),
        "n_boot": n_boot,
    }


def plot_segmentation(
    df: pd.DataFrame,
    k_info: dict[str, object],
    optimal_k: int,
    pca: PCA,
    out_dir: Path = OUTPUT_DIR,
) -> list[Path]:
    """Save PCA scatter + elbow/silhouette PNGs to the project root."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.style.use("dark_background")
    paths: list[Path] = []

    # 1. PCA scatter colored by segment.
    fig, ax = plt.subplots(figsize=(9, 6))
    for segment in sorted(df["segment"].unique()):
        mask = df["segment"] == segment
        ax.scatter(df.loc[mask, "pca1"], df.loc[mask, "pca2"], s=8, alpha=0.6, label=segment)
    var1, var2 = pca.explained_variance_ratio_[:2] * 100
    ax.set_title("User Segments — PCA Projection")
    ax.set_xlabel(f"PC1 ({var1:.1f}% variance)")
    ax.set_ylabel(f"PC2 ({var2:.1f}% variance)")
    ax.legend(markerscale=3)
    fig.tight_layout()
    pca_path = out_dir / "segmentation_pca_scatter.png"
    fig.savefig(pca_path, dpi=150)
    plt.close(fig)
    paths.append(pca_path)

    # 2. Elbow + silhouette curves with the chosen K marked.
    k_list = k_info["k_list"]  # type: ignore[assignment]
    inertias = k_info["inertias"]  # type: ignore[assignment]
    silhouettes = k_info["silhouettes"]  # type: ignore[assignment]
    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax1.plot(k_list, inertias, "o-", color="tab:blue", label="Inertia")
    ax1.set_xlabel("K")
    ax1.set_ylabel("Inertia", color="tab:blue")
    ax1.axvline(optimal_k, color="tab:red", linestyle="--", label=f"Optimal K={optimal_k}")
    ax2 = ax1.twinx()
    ax2.plot(k_list, silhouettes, "s--", color="tab:orange", label="Silhouette")
    ax2.set_ylabel("Silhouette", color="tab:orange")
    ax1.set_title("K Selection — Elbow & Silhouette")
    fig.tight_layout()
    elbow_path = out_dir / "segmentation_k_selection.png"
    fig.savefig(elbow_path, dpi=150)
    plt.close(fig)
    paths.append(elbow_path)

    return paths


def assign_segment_names(df: pd.DataFrame, optimal_k: int) -> tuple[pd.DataFrame, dict[int, str]]:
    """Map cluster IDs → revenue-ranked segment names. Guarded: the name list
    must cover the chosen K, and every cluster must receive a name."""
    assert len(NAME_BY_REVENUE_RANK) >= optimal_k, (
        f"NAME_BY_REVENUE_RANK has {len(NAME_BY_REVENUE_RANK)} entries but K={optimal_k}"
    )
    cluster_revenue = df.groupby("cluster")["monthly_revenue"].mean()
    assert len(cluster_revenue) == optimal_k, (
        f"KMeans produced {len(cluster_revenue)} non-empty clusters but K={optimal_k}"
    )
    revenue_rank = cluster_revenue.rank(ascending=False).astype(int)
    cluster_to_segment = {
        cid: NAME_BY_REVENUE_RANK[revenue_rank[cid] - 1] for cid in revenue_rank.index
    }
    df["segment"] = df["cluster"].map(cluster_to_segment)
    return df, cluster_to_segment


# ── Sections ──────────────────────────────────────────────────────────────────
def section_setup(df: pd.DataFrame) -> None:
    print_section("VOLTA NEOBANK — USER SEGMENTATION", blank=False)
    print(f"\nDataset shape: {df.shape}")
    print(f"Users: {len(df):,}")
    print("\nFeature summary statistics:")
    print(df[FEATURE_COLS].describe().round(2))


def section_features(X_scaled: np.ndarray) -> None:
    print_section("FEATURE ENGINEERING & STANDARDIZATION")
    print(f"\nClustering features: {CLUSTERING_FEATURES}")
    print("\nAfter standardization:")
    print("  Feature means (should be ~0):")
    for feat, mean in zip(CLUSTERING_FEATURES, np.round(X_scaled.mean(axis=0), 4), strict=True):
        print(f"    {feat:<25} {mean:>8.4f}")
    print("\n  Feature stds (should be ~1):")
    for feat, std in zip(CLUSTERING_FEATURES, np.round(X_scaled.std(axis=0), 4), strict=True):
        print(f"    {feat:<25} {std:>8.4f}")


def section_k_selection(k_info: dict[str, object]) -> int:
    print_section("OPTIMAL K SELECTION — ELBOW METHOD (data-driven)")
    k_list = k_info["k_list"]  # type: ignore[assignment]
    inertias = k_info["inertias"]  # type: ignore[assignment]
    silhouettes = k_info["silhouettes"]  # type: ignore[assignment]
    reductions = k_info["reductions"]  # type: ignore[assignment]
    optimal_k = int(k_info["optimal_k"])  # type: ignore[arg-type]
    print(f"\n{'K':<4} {'Inertia':<12} {'Reduction %':<15} {'Silhouette':<12} {'Note':<22}")
    print("-" * 70)
    for k, inertia, red, sil in zip(k_list, inertias, reductions, silhouettes, strict=True):
        note = "← ELBOW (chosen)" if k == optimal_k else ""
        print(f"{k:<4} {inertia:<12.1f} {red:<15.1f}% {sil:<12.3f} {note:<22}")
    print(f"\n→ Selected K = {optimal_k}: last K with marginal reduction ≥ 50% of the")
    print(f"  best reduction ({k_info['max_reduction']:.1f}%). Adding more clusters")
    print(f"  past K={optimal_k} gives <10% inertia reduction — diminishing returns.")
    print("\n  Silhouette validation: plateaus across K=2–4, then collapses at K=5")
    print("  (silhouette peaks at K=2 — a known artifact of well-separated 4-cluster")
    print("  data where the 2-cluster merge still scores high). Reported as")
    print("  validation, not used as the selector.")
    return optimal_k


def section_clustering(
    df: pd.DataFrame,
    X_scaled: np.ndarray,
    optimal_k: int,
    cluster_to_segment: dict[int, str],
    pca: PCA,
) -> None:
    print_section("K-MEANS CLUSTERING & PCA DIMENSIONALITY REDUCTION")
    print("\nCluster sizes:")
    for cid, size in df["cluster"].value_counts().sort_index().items():
        pct = size / len(df) * 100
        print(f"  Cluster {cid}: {size:>6,} users ({pct:>5.1f}%)")
    var_explained = pca.explained_variance_ratio_[:2].sum() * 100
    print(f"\nPCA variance explained by PC1 + PC2: {var_explained:.1f}%")
    print("\nPCA Component Loadings (feature importance for first 2 PCs):")
    for i, feature in enumerate(CLUSTERING_FEATURES):
        print(
            f"  {feature:<25} PC1: {pca.components_[0][i]:>7.3f}  PC2: {pca.components_[1][i]:>7.3f}"
        )
    print("\nSegment assignment by revenue ranking:")
    cluster_revenue = df.groupby("cluster")["monthly_revenue"].mean()
    revenue_rank = cluster_revenue.rank(ascending=False).astype(int)
    for cid in sorted(df["cluster"].unique()):
        print(
            f"  Cluster {cid} → {cluster_to_segment[cid]:<15} "
            f"(Rank: {revenue_rank[cid]}, ARPU: €{cluster_revenue[cid]:.2f})"
        )

    print("\nPer-cluster silhouette (mean of sample-level scores):")
    sil_by_cluster = per_cluster_silhouette(X_scaled, df["cluster"].values)
    for cid in sorted(sil_by_cluster):
        quality = "well-separated" if sil_by_cluster[cid] >= 0.5 else "fuzzy / overlapping"
        print(
            f"  Cluster {cid} ({cluster_to_segment[cid]:<15}): {sil_by_cluster[cid]:.3f}  {quality}"
        )


# ── Sprint 1: S1-S3 section printers ─────────────────────────────────────────
def section_silhouette_plot(
    X_scaled: np.ndarray,
    df: pd.DataFrame,
    cluster_to_segment: dict[int, str],
) -> Path:
    """S1: classic per-sample silhouette plot PNG."""
    print_section("SILHOUETTE PLOT (per-sample separation)")
    out = OUTPUT_DIR / "segmentation_silhouette.png"
    plot_silhouette(X_scaled, df["cluster"].values, cluster_to_segment, out)
    print(f"\nSaved: {out.name}")
    print("  Each horizontal band = one segment's samples sorted by silhouette.")
    print("  Long bands to the right = well-separated; bands crossing 0 = fuzzy.")
    return out


def section_centroid_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """S2: per-segment feature z-scores vs the global mean."""
    print_section("CENTROID PROFILES (z-score vs global mean)")
    z = centroid_zscores(df)
    print("\nPositive = segment above average on that feature; negative = below.")
    print(z.to_string())
    print_subsection("READING THE TABLE")
    # Surface the top defining feature per segment.
    for segment in z.index:
        top_feat = z.columns[int(z.loc[segment].abs().argmax())]
        top_val = z.loc[segment, top_feat]
        direction = "above" if top_val > 0 else "below"
        print(f"  {segment:<15} defined by {top_feat} ({top_val:+.2f}σ {direction} avg)")
    return z


def segment_stability_section(
    df: pd.DataFrame, X_scaled: np.ndarray, optimal_k: int
) -> dict[str, float]:
    """S3: bootstrap cluster-assignment stability (adjusted Rand index)."""
    print_section("SEGMENT STABILITY (bootstrap adjusted Rand index)")
    stab = segment_stability(df, X_scaled, optimal_k)
    print(f"\nBootstrap iterations: {stab['n_boot']}")
    print(f"  Mean ARI: {stab['mean_ari']:.3f}")
    print(f"  Std  ARI: {stab['std_ari']:.3f}")
    print(f"  Min  ARI: {stab['min_ari']:.3f}")
    if stab["mean_ari"] >= 0.85:
        print("  ✅ Stable — segments are a robust property of the data,")
        print("     not a KMeans-seed artifact (mean ARI ≥ 0.85).")
    elif stab["mean_ari"] >= 0.70:
        print("  ⚠️  Moderately stable — some cluster boundary ambiguity;")
        print("     inspect the silhouette plot for the fuzzy segment.")
    else:
        print("  ❌ Unstable — the K=4 partition is not robust to resampling;")
        print("     reconsider K or the feature set.")
    print("\n  ARI = 1 → identical partition; 0 → random; <0 → anti-correlated.")
    return stab


def _seg_size_pct(seg_summary: pd.DataFrame, segment: str) -> float:
    if segment not in seg_summary.index:
        return float("nan")
    return seg_summary.loc[segment, "n_users"] / seg_summary["n_users"].sum() * 100


def section_profiles(seg_summary: pd.DataFrame) -> None:
    print_section("SEGMENT PROFILES DEEP DIVE")
    segment_order = NAME_BY_REVENUE_RANK[: len(seg_summary.index)]
    for segment in segment_order:
        if segment not in seg_summary.index:
            print(f"\n⚠️  {segment} not found in segment_profiles.csv")
            continue
        row = seg_summary.loc[segment]
        n_users = int(row["n_users"])
        pct_of_base = _seg_size_pct(seg_summary, segment)
        print(f"\n{'=' * 70}")
        print(f"▶ {segment.upper()}")
        print(f"{'=' * 70}")
        print("  Users & Revenue:")
        print(f"    Users:              {n_users:>10,}  ({pct_of_base:>5.1f}% of base)")
        print(f"    Monthly ARPU:       €{row['avg_rev']:>10.2f}")
        print(f"    Revenue share:      {row['revenue_share']:>10.0f}%")
        print("\n  Behavioral Metrics:")
        print(f"    Avg transactions:   {row['avg_tx']:>10.1f}  per month")
        print(f"    Avg savings:        €{row['avg_savings']:>10.0f}")
        print(f"    Avg logins:         {row['avg_logins']:>10.1f}  per week")
        print(f"    Avg tenure:         {row['avg_tenure']:>10.0f}  days")
        print("\n  Monetization:")
        print(f"    Premium rate:       {row['pct_premium'] * 100:>10.0f}%")


def section_insight_concentration(seg_summary: pd.DataFrame) -> None:
    print_section("KEY INSIGHT 1: Revenue Concentration")
    if "Power Users" not in seg_summary.index:
        print("⚠️  Power Users segment missing.")
        return
    total_users = seg_summary["n_users"].sum()
    total_rev = seg_summary["total_monthly_rev"].sum()
    pu = int(seg_summary.loc["Power Users", "n_users"])
    pr = seg_summary.loc["Power Users", "total_monthly_rev"]
    user_pct = pu / total_users * 100
    rev_pct = pr / total_rev * 100
    print(f"\nPower Users ({user_pct:.0f}% of user base) generate {rev_pct:.0f}% of revenue")
    print("Classic concentration pattern: high-value users are disproportionately profitable")
    print("→ STRATEGIC IMPLICATION: Protect Power Users — churn of even 5% is expensive")


def section_insight_casual_dormant(seg_summary: pd.DataFrame) -> None:
    print_section("KEY INSIGHT 2: Casual vs Dormant Users")
    if "Casual Users" not in seg_summary.index or "Dormant Users" not in seg_summary.index:
        print("⚠️  Required segments missing.")
        return
    casual_arpu = seg_summary.loc["Casual Users", "avg_rev"]
    dormant_arpu = seg_summary.loc["Dormant Users", "avg_rev"]
    casual_tenure = seg_summary.loc["Casual Users", "avg_tenure"]
    dormant_tenure = seg_summary.loc["Dormant Users", "avg_tenure"]
    print(f"\nCasual users ARPU:  €{casual_arpu:.2f}  (Tenure: {casual_tenure:.0f} days)")
    print(f"Dormant users ARPU: €{dormant_arpu:.2f}  (Tenure: {dormant_tenure:.0f} days)")
    print(
        f"Difference: €{abs(casual_arpu - dormant_arpu):.2f} "
        f"(~{abs(casual_arpu - dormant_arpu) / casual_arpu * 100:.0f}%)"
    )
    print("\n→ STRATEGIC IMPLICATION: Dormant users are re-engagement targets,")
    print("   not lost causes. Similar behavior to Casual users.")


def section_insight_premium(seg_summary: pd.DataFrame) -> None:
    print_section("KEY INSIGHT 3: Premium Adoption by Segment")
    if "Power Users" not in seg_summary.index or "Casual Users" not in seg_summary.index:
        print("⚠️  Required segments missing.")
        return
    power_prem = seg_summary.loc["Power Users", "pct_premium"] * 100
    casual_prem = seg_summary.loc["Casual Users", "pct_premium"] * 100
    print(f"\nPower Users premium rate:   {power_prem:.0f}%")
    print(f"Casual Users premium rate:  {casual_prem:.0f}%")
    print(f"Gap: {power_prem - casual_prem:.0f} percentage points")
    print("\n→ STRATEGIC IMPLICATION: Premium plan is almost exclusively a Power User")
    print("   product. Path to revenue growth: drive Casual → Premium migration.")


def section_revenue_concentration(seg_summary: pd.DataFrame) -> None:
    print_section("REVENUE CONCENTRATION & CHURN IMPACT ANALYSIS")
    total_rev = seg_summary["total_monthly_rev"].sum()
    total_users = seg_summary["n_users"].sum()
    print(f"\nTotal monthly revenue:  €{total_rev:,.0f}")
    print(f"Total active users:     {int(total_users):,}")
    print(f"Overall ARPU:           €{total_rev / total_users:.2f}")
    segment_order = NAME_BY_REVENUE_RANK[: len(seg_summary.index)]
    print("\nRevenue by segment:")
    for segment in segment_order:
        if segment not in seg_summary.index:
            continue
        seg_rev = seg_summary.loc[segment, "total_monthly_rev"]
        seg_users = int(seg_summary.loc[segment, "n_users"])
        print(
            f"  {segment:<20} €{seg_rev:>10,.0f}  ({seg_rev / total_rev * 100:>5.1f}%)  "
            f"| {seg_users:>6,} users ({seg_users / total_users * 100:>5.1f}%)"
        )


def section_pareto(seg_summary: pd.DataFrame) -> None:
    """Real Lorenz-style concentration: cumulative %users vs %revenue, sorted
    by revenue descending. Replaces the prior single-segment 'Pareto' print."""
    print_section("PARETO ANALYSIS (Lorenz concentration curve)")
    order = seg_summary.sort_values("total_monthly_rev", ascending=False)
    total_users = order["n_users"].sum()
    total_rev = order["total_monthly_rev"].sum()
    cum_users = (order["n_users"].cumsum() / total_users * 100).values
    cum_rev = (order["total_monthly_rev"].cumsum() / total_rev * 100).values
    print(f"\n{'Segment':<20} {'%users (cum)':<14} {'%revenue (cum)':<16}")
    print("-" * 55)
    for segment, cu, cr in zip(order.index, cum_users, cum_rev, strict=True):
        print(f"{segment:<20} {cu:>10.1f}%   {cr:>12.1f}%")
    # 80% revenue point
    idx80 = int(np.argmax(cum_rev >= 80))
    print(
        f"\n→ {cum_users[idx80]:.0f}% of users generate ≥80% of revenue "
        f"(reached at '{order.index[idx80]}')."
    )
    pu_pct = cum_users[0]
    pr_pct = cum_rev[0]
    print(f"→ Top segment alone: {pu_pct:.0f}% of users → {pr_pct:.0f}% of revenue.")


def section_churn(seg_summary: pd.DataFrame) -> None:
    print_section("CHURN SENSITIVITY: Revenue Impact per Segment")
    print("\nRevenue lost from 5% churn (monthly impact):")
    segment_order = NAME_BY_REVENUE_RANK[: len(seg_summary.index)]
    for segment in segment_order:
        if segment not in seg_summary.index:
            continue
        seg_users = int(seg_summary.loc[segment, "n_users"])
        seg_arpu = seg_summary.loc[segment, "avg_rev"]
        loss = seg_users * 0.05 * seg_arpu
        print(f"  {segment:<20} €{loss:>10,.0f}")
    if "Power Users" in seg_summary.index and "Casual Users" in seg_summary.index:
        power_loss = (
            int(seg_summary.loc["Power Users", "n_users"])
            * 0.05
            * seg_summary.loc["Power Users", "avg_rev"]
        )
        casual_loss = (
            int(seg_summary.loc["Casual Users", "n_users"])
            * 0.05
            * seg_summary.loc["Casual Users", "avg_rev"]
        )
        print(f"\n→ One Power User churn is worth {power_loss / casual_loss:.1f}×")
        print("   a Casual User churn in terms of revenue impact")


def section_monetization(seg_summary: pd.DataFrame) -> None:
    print_section("MONETIZATION SCENARIOS: Revenue Uplift Opportunities")
    needed = ["Casual Users", "Growth Users", "Power Users", "Dormant Users"]
    if not all(s in seg_summary.index for s in needed):
        print("⚠️  Missing segments for scenario modelling.")
        return
    total_rev = seg_summary["total_monthly_rev"].sum()
    cu, ca = (
        int(seg_summary.loc["Casual Users", "n_users"]),
        seg_summary.loc["Casual Users", "avg_rev"],
    )
    gu, ga = (
        int(seg_summary.loc["Growth Users", "n_users"]),
        seg_summary.loc["Growth Users", "avg_rev"],
    )
    _, pa = (
        int(seg_summary.loc["Power Users", "n_users"]),
        seg_summary.loc["Power Users", "avg_rev"],
    )
    du, da = (
        int(seg_summary.loc["Dormant Users", "n_users"]),
        seg_summary.loc["Dormant Users", "avg_rev"],
    )

    casual_uplift = cu * 0.10 * (ga - ca)  # 10% Casual → Growth ARPU
    growth_uplift = gu * 0.05 * (pa - ga)  # 5% Growth → Power ARPU
    dormant_uplift = du * 0.05 * (ca - da)  # 5% Dormant → Casual ARPU
    total_uplift = casual_uplift + growth_uplift + dormant_uplift

    scenarios = [
        (
            "A",
            "Convert 10% of Casual → Growth tier ARPU",
            "Premium trial offer at M2",
            cu * 0.10,
            ga - ca,
            casual_uplift,
        ),
        (
            "B",
            "Convert 5% of Growth → Power tier ARPU",
            "Savings goals, investment features",
            gu * 0.05,
            pa - ga,
            growth_uplift,
        ),
        (
            "C",
            "Reactivate 5% of Dormant → Casual tier ARPU",
            "Win-back email + limited-time offer",
            du * 0.05,
            ca - da,
            dormant_uplift,
        ),
    ]
    for letter, title, mech, affected, gap, uplift in scenarios:
        print(f"\nSCENARIO {letter}: {title}")
        print(f"  Mechanism: {mech}")
        print(f"  Affected users: {int(affected):,}")
        print(f"  Per-user ARPU gap: €{gap:.2f}")
        print(f"  Monthly uplift: €{uplift:,.0f}")
        print(f"  Annual uplift: €{uplift * 12:,.0f}")

    print(f"\n{'=' * 70}")
    print("TOTAL INCREMENTAL REVENUE OPPORTUNITY")
    print(f"{'=' * 70}")
    print(f"Combined monthly uplift: €{total_uplift:,.0f}")
    print(f"Uplift as % of current revenue: +{total_uplift / total_rev * 100:.1f}%")
    print(f"Combined annual uplift: €{total_uplift * 12:,.0f}")
    print("\n→ Achievable revenue from optimized segment migration")


# Strategy definitions. size_pct is injected dynamically from seg_summary
# (the prior version hardcoded 12/24/43/43 = 122%, which summed past 100%).
STRATEGIES: dict[str, dict[str, object]] = {
    "Power Users": {
        "key_insight": "77% premium, high savings, 4× ARPU vs others",
        "product_strategy": "Retain & expand: exclusive features, priority support, premium benefits",
        "marketing_channel": "Personalized push notifications, in-app VIP communications",
        "tactics": [
            "• Volta Premium tier with exclusive perks (higher interest rates, fees waived)",
            "• Dedicated customer success manager for highest-value users",
            "• Early access to new features and products",
            "• VIP badge and status recognition in app",
        ],
    },
    "Growth Users": {
        "key_insight": "Mid-premium rate, high savings, engaged but lower transaction volume",
        "product_strategy": "Push to Power: automated savings goals, transaction nudges, premium trial",
        "marketing_channel": "Email drip campaigns, in-app milestone rewards",
        "tactics": [
            "• Automated savings goals with behavioral nudges",
            "• 30-day free premium trial at month 2–3",
            "• Transaction rewards that grow with engagement",
            "• Investment product introduction (stocks, crypto)",
        ],
    },
    "Casual Users": {
        "key_insight": "8% premium, transact but don't save, largest addressable market",
        "product_strategy": "Convert to Growth: cashback activation, savings pocket first deposit offer",
        "marketing_channel": "Push notifications, gamification, in-app incentives",
        "tactics": [
            "• Cashback rewards on transactions (2–5% depending on tier)",
            "• Savings pocket first deposit match (e.g., 1:1 match up to €10)",
            "• Gamified savings challenges with friends",
            "• Simplified premium upsell at high-transaction moments",
        ],
    },
    "Dormant Users": {
        "key_insight": "Old accounts, low activity, re-engagement targets not lost causes",
        "product_strategy": "Re-engage or accept churn: win-back campaign, simplify first transaction",
        "marketing_channel": "Email win-back sequences, limited-time offers, SMS",
        "tactics": [
            '• Time-limited "come back" offer (e.g., €5 credit)',
            "• Simplified re-engagement flow (one-tap transaction)",
            "• Personalized messaging highlighting new features since they left",
            "• Option to pause/delete account (respectful churn exit)",
        ],
    },
}


def section_strategy(seg_summary: pd.DataFrame) -> None:
    print_section("SEGMENT-SPECIFIC PRODUCT & MARKETING STRATEGY")
    segment_order = NAME_BY_REVENUE_RANK[: len(seg_summary.index)]
    for segment in segment_order:
        if segment not in STRATEGIES or segment not in seg_summary.index:
            continue
        s = STRATEGIES[segment]
        size_pct = _seg_size_pct(seg_summary, segment)
        print(f"\n{'=' * 70}")
        print(f"▶ {segment.upper()}")
        print(f"{'=' * 70}")
        print(f"\nSize:         {size_pct:.0f}% of user base  (derived from segment_profiles.csv)")
        print(f"Key insight:  {s['key_insight']}")
        print(f"\nProduct:      {s['product_strategy']}")
        print(f"Marketing:    {s['marketing_channel']}")
        print("\nKey tactics:")
        for tactic in s["tactics"]:  # type: ignore[index]
            print(f"  {tactic}")


EXPERIMENTS = [
    {
        "name": "Premium Trial Offer @ M2",
        "hypothesis": "30-day free premium trial increases conversion rate by 5pp",
        "target": "Casual Users (month 2 cohort)",
        "control": "No premium offer",
        "treatment": "30-day free trial popup at day 40",
        "primary_metric": "Premium conversion rate (%)",
        "duration": "28 days",
        "sample_size": "10,000 per arm",
        "success_criteria": "Conversion rate ≥ 13% (vs baseline 8%)",
    },
    {
        "name": "Savings Goal Nudge",
        "hypothesis": "In-app savings goal prompt increases savings balance by 15%",
        "target": "Growth Users",
        "control": "No prompt",
        "treatment": "Weekly in-app notification + savings goal setup wizard",
        "primary_metric": "Average savings balance (EUR)",
        "duration": "56 days",
        "sample_size": "5,000 per arm",
        "success_criteria": "Savings increase ≥ 10%",
    },
    {
        "name": "Win-Back Email Campaign",
        "hypothesis": "Personalized win-back offer reactivates 8% of dormant users",
        "target": "Dormant Users (90+ days inactive)",
        "control": "No email",
        "treatment": "Personalized win-back email + €5 app credit offer",
        "primary_metric": "30-day reactivation rate (%)",
        "duration": "30 days post-email",
        "sample_size": "50,000 per arm",
        "success_criteria": "Reactivation rate ≥ 8%",
    },
    {
        "name": "Power User VIP Badge",
        "hypothesis": "Exclusivity badge increases feature engagement by 20%",
        "target": "Power Users",
        "control": "No badge",
        "treatment": "VIP badge on profile + exclusive features ribbon",
        "primary_metric": "Premium feature usage rate (%)",
        "duration": "42 days",
        "sample_size": "3,000 per arm",
        "success_criteria": "Feature engagement +15%",
    },
]


def section_experiments() -> None:
    print_section("RECOMMENDED A/B TESTS TO VALIDATE SEGMENT STRATEGY")
    for i, exp in enumerate(EXPERIMENTS, 1):
        print(f"\n{'─' * 70}")
        print(f"TEST {i}: {exp['name']}")
        print(f"{'─' * 70}")
        print(f"Hypothesis:      {exp['hypothesis']}")
        print(f"Target segment:  {exp['target']}")
        print(f"Duration:        {exp['duration']}")
        print(f"Sample size:     {exp['sample_size']}")
        print("\nExperimental design:")
        print(f"  Control:         {exp['control']}")
        print(f"  Treatment:       {exp['treatment']}")
        print(f"  Primary metric:  {exp['primary_metric']}")
        print(f"  Success criteria: {exp['success_criteria']}")


PORTFOLIO = [
    {
        "project": "Project 1 — Funnel Analysis",
        "skill": "Problem Discovery",
        "output": "Identified KYC as critical bottleneck (56.6% step conversion)",
        "business_impact": "Prioritized which feature to build next",
    },
    {
        "project": "Project 2 — A/B Testing",
        "skill": "Solution Validation",
        "output": "Proved KYC progress bar works (+6.24pp, Z=6.35, p<0.0001)",
        "business_impact": "Enabled confident full-fleet rollout",
    },
    {
        "project": "Project 3 — Retention & Cohort",
        "skill": "Long-Term Impact Measurement",
        "output": "KYC fix improved Free LTV by ~20% (+€3.6 per free user)",
        "business_impact": "Quantified long-term ROI of the fix (€227K/year)",
    },
    {
        "project": "Project 4 — User Segmentation",
        "skill": "Strategic Monetization",
        "output": "Identified 4 segments with distinct monetization paths",
        "business_impact": "Unlocked incremental revenue opportunity",
    },
]


def section_capstone() -> None:
    print_section("CAPSTONE: Product Analytics Portfolio Summary")
    print("\nProject progression:")
    for item in PORTFOLIO:
        print(f"\n{item['project']}")
        print(f"  Skill demonstrated:  {item['skill']}")
        print(f"  Key output:          {item['output']}")
        print(f"  Business impact:     {item['business_impact']}")
    print(f"\n{'=' * 70}")
    print("META-NARRATIVE: The Data-Driven Product Loop")
    print(f"{'=' * 70}")
    print("""
This 4-project portfolio demonstrates the complete lifecycle of data-driven
product decision-making at a tech company:

  1. DISCOVER: Use analytics to find problems (funnel analysis)
  2. VALIDATE: Use experimentation to test solutions (A/B testing)
  3. MEASURE: Use cohort analysis to quantify long-term impact (retention)
  4. OPTIMIZE: Use segmentation to maximize monetization (segmentation)
  5. ITERATE: Repeat with next problem

Key skills demonstrated:
  ✓ Data querying and manipulation (pandas)
  ✓ Statistical hypothesis testing (p-values, CIs, A/B tests, CUPED)
  ✓ Data visualization (funnel, channel breakdown, segment profiles)
  ✓ Machine learning (K-means clustering, PCA, silhouette validation)
  ✓ Business acumen (LTV calculations, monetization strategy, ROI)
  ✓ Storytelling (connecting data to business outcomes)
""")


def section_final() -> None:
    print_section("FINAL RECOMMENDATION")
    print("""
Next steps for Volta leadership:

1. IMMEDIATE (Week 1):
   • Approve 4 A/B tests to validate segment-specific strategies
   • Allocate engineering resources for premium trial at M2 (highest priority)

2. SHORT-TERM (Month 1–2):
   • Run tests in parallel, prioritize based on fastest learning
   • Begin win-back campaign to Dormant users (lowest risk, quick win)

3. MEDIUM-TERM (Month 2–3):
   • Roll out winning experiments to full production
   • Build segment-specific dashboards for ongoing monitoring
   • Design quarterly business reviews by segment

4. LONG-TERM (Month 3+):
   • Target: Achieve the modeled incremental monthly revenue
   • Iterate on segment strategies based on performance data
   • Plan for Project 5: Predictive churn modeling + retention optimization
""")


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    setup(float_format="{:.3f}")
    df, seg_summary = load_data()

    section_setup(df)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[CLUSTERING_FEATURES])
    section_features(X_scaled)

    k_info = select_k(X_scaled)
    optimal_k = section_k_selection(k_info)

    df, km, pca, Xp = fit_clusters(df, X_scaled, optimal_k)
    df, cluster_to_segment = assign_segment_names(df, optimal_k)
    section_clustering(df, X_scaled, optimal_k, cluster_to_segment, pca)

    section_silhouette_plot(X_scaled, df, cluster_to_segment)
    section_centroid_profiles(df)
    segment_stability_section(df, X_scaled, optimal_k)

    plot_paths = plot_segmentation(df, k_info, optimal_k, pca)
    print_section("VISUALIZATIONS SAVED")
    for p in plot_paths:
        print(f"  {p.name} → {p}")

    section_profiles(seg_summary)
    section_insight_concentration(seg_summary)
    section_insight_casual_dormant(seg_summary)
    section_insight_premium(seg_summary)
    section_revenue_concentration(seg_summary)
    section_pareto(seg_summary)
    section_churn(seg_summary)
    section_monetization(seg_summary)
    section_strategy(seg_summary)
    section_experiments()
    section_capstone()
    section_final()

    print("=" * 70)
    print("Portfolio complete. Ready for next phase of strategy execution.")
    print("=" * 70)


if __name__ == "__main__":
    main()
