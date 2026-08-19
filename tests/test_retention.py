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
