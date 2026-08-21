"""Tests for volta_retention_analysis.py — Project 3 retention analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd

import volta_retention_analysis as vr


def test_compute_ltv() -> None:
    assert vr.compute_ltv([1.0, 0.5], 10.0) == 15.0
    assert vr.compute_ltv([1.0, 0.0], 5.0) == 5.0


def test_bootstrap_ci_contains_mean_and_narrows_with_n() -> None:
    lo, hi = vr.bootstrap_ci([0.3, 0.31, 0.29, 0.3, 0.32, 0.3, 0.29, 0.31])
    assert lo < 0.30 < hi
    # Degenerate sample → CI collapses to the single value.
    lo_single, hi_single = vr.bootstrap_ci([0.4])
    assert lo_single == hi_single == 0.4
    # Empty sample → NaN, no crash.
    assert np.isnan(vr.bootstrap_ci([])[0])


def test_cohens_d() -> None:
    d = vr.cohens_d([1, 2, 3], [4, 5, 6])
    assert d == 3.0  # means 2 vs 5, pooled SD = 1


def test_split_cohorts_pre_post() -> None:
    idx = pd.Index(["2024-01", "2024-08", "2024-09", "2024-12"])
    pre, post = vr.split_cohorts(idx)
    assert pre == ["2024-01", "2024-08"]
    assert post == ["2024-09", "2024-12"]


def test_cohort_metric_values_drops_nan() -> None:
    df = pd.DataFrame(
        {"month_3": [0.3, np.nan, 0.4, 0.5]},
        index=["2024-01", "2024-02", "2024-03", "2024-04"],
    )
    vals = vr.cohort_metric_values(df, ["2024-01", "2024-02", "2024-03"], "month_3")
    assert vals == [0.3, 0.4]


def _make_retention_df() -> pd.DataFrame:
    """8 pre-fix cohorts (M3 ≈ 0.30) + 4 post-fix cohorts (M3 ≈ 0.40)."""
    pre = [0.28, 0.30, 0.29, 0.31, 0.30, 0.29, 0.32, 0.30]
    post = [0.40, 0.41, 0.39, 0.42]
    rows = []
    for i, (_, m3) in enumerate(zip(range(1, 13), pre + post, strict=True)):
        rows.append({"cohort": f"2024-{i + 1:02d}", "cohort_size": 5000, "month_3": m3})
    return pd.DataFrame(rows).set_index("cohort")


def test_section_stat_test_detects_improvement() -> None:
    df = _make_retention_df()
    result = vr.section_stat_test(df)
    assert result["difference"] > 0
    assert result["p_value"] < 0.05
    assert result["cohens_d"] > 0
    assert result["n_pre"] == 8
    assert result["n_post"] == 4


# ── Sprint 1: R1-R3 ──────────────────────────────────────────────────────────
def _make_full_retention_df() -> pd.DataFrame:
    """12 cohorts × 12 months with a pre/post step-change."""
    pre_curve = [1.0, 0.52, 0.38, 0.31, 0.26, 0.23, 0.21, 0.19, 0.18, 0.17, 0.16, 0.15]
    post_curve = [1.0, 0.64, 0.49, 0.41, 0.36, 0.33, 0.31, 0.29, 0.28, 0.27, 0.26, 0.25]
    rows = []
    for i in range(12):
        cohort = f"2024-{i + 1:02d}"
        curve = post_curve if cohort >= "2024-09" else pre_curve
        row = {"cohort": cohort, "cohort_size": 5000}
        for m, r in enumerate(curve):
            row[f"month_{m}"] = r
        rows.append(row)
    return pd.DataFrame(rows).set_index("cohort")


def test_churn_curve_complements_retention() -> None:
    df = _make_full_retention_df()
    churn = vr.churn_curve(df)
    assert len(churn) == 12
    # Churn = 1 - retention; M0 retention is 1.0 → churn 0.
    m0 = churn.iloc[0]
    assert m0["pre_churn"] == 0.0
    assert m0["post_churn"] == 0.0
    # Post-fix churn should be lower than pre-fix (retention improved).
    m1 = churn[churn["month"] == "M1"].iloc[0]
    assert m1["post_churn"] < m1["pre_churn"]


def test_ltv_bootstrap_ci_post_above_pre() -> None:
    df = _make_full_retention_df()
    arpu = 3.2
    pre_lo, pre_hi = vr.ltv_bootstrap_ci(df, arpu, side="pre")
    post_lo, post_hi = vr.ltv_bootstrap_ci(df, arpu, side="post")
    assert pre_lo > 0 and post_lo > 0
    # Post-fix LTV CI should sit above pre-fix (retention improved).
    assert post_lo > pre_lo


def test_ltv_bootstrap_ci_empty_side_returns_nan() -> None:
    df = _make_full_retention_df()
    # No cohorts before 2023 → empty pre side.
    df_only_post = df[df.index >= "2024-09"]
    lo, hi = vr.ltv_bootstrap_ci(df_only_post, 3.2, side="pre")
    assert np.isnan(lo) and np.isnan(hi)


def test_ltv_bootstrap_ci_premium_multiplier_scales_ltv() -> None:
    df = _make_full_retention_df()
    lo_free, hi_free = vr.ltv_bootstrap_ci(df, 3.2, side="pre", premium_multiplier=1.0)
    lo_prem, hi_prem = vr.ltv_bootstrap_ci(df, 3.2, side="pre", premium_multiplier=2.0)
    # 2× retention multiplier → ~2× LTV.
    assert lo_prem > 1.8 * lo_free


def test_plot_cohort_heatmap_writes_png(tmp_path) -> None:
    df = _make_full_retention_df()
    out = tmp_path / "cohort.png"
    path = vr.plot_cohort_heatmap(df, out)
    assert path == out
    assert out.exists()
    assert out.stat().st_size > 1000
