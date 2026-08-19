"""Tests for volta_ab_testing.py — Project 2 A/B test analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd

import volta_ab_testing as ab


def _make_experiment_df(
    n_control: int = 1000,
    n_treatment: int = 1000,
    control_rate: float = 0.5,
    treat_rate: float = 0.6,
    seed: int = 0,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    control = rng.random(n_control) < control_rate
    treatment = rng.random(n_treatment) < treat_rate
    return pd.DataFrame(
        {
            "customer_id": np.arange(n_control + n_treatment),
            "group": ["control"] * n_control + ["treatment"] * n_treatment,
            "kyc_completed": np.r_[control, treatment].astype(int),
            "pre_kyc_rate": rng.random(n_control + n_treatment),
        }
    )


def test_calc_sample_size_positive_and_monotonic() -> None:
    n_small = ab.calc_sample_size(0.5, 0.10)
    n_large = ab.calc_sample_size(0.5, 0.05)
    assert n_small > 0
    assert n_large > n_small  # smaller MDE needs more users


def test_srm_check_balanced_split() -> None:
    df = _make_experiment_df()
    srm = ab.srm_check(df)
    assert srm["control"] == 1000
    assert srm["treatment"] == 1000
    assert srm["p"] > 0.05


def test_primary_analysis_recovers_known_lift() -> None:
    df = _make_experiment_df(control_rate=0.5, treat_rate=0.6)
    r = ab.primary_analysis(df)
    assert abs(r["control_rate"] - 0.5) < 0.05
    assert abs(r["treatment_rate"] - 0.6) < 0.05
    assert r["absolute_lift"] > 0
    assert r["p_value"] < 0.05
    assert r["ci_lower"] < r["absolute_lift"] < r["ci_upper"]


def test_bonferroni() -> None:
    assert ab.bonferroni([0.01, 0.02, 0.5]) == [True, False, False]


def test_holm_bonferroni() -> None:
    assert ab.holm_bonferroni([0.01, 0.02, 0.5]) == [True, True, False]


def test_benjamini_hochberg() -> None:
    assert ab.benjamini_hochberg([0.01, 0.02, 0.5]) == [True, True, False]


def test_make_buckets_row_order_independent() -> None:
    ids = np.arange(1000)
    vals = np.random.default_rng(1).random(1000)
    b1 = ab.make_buckets(ids, vals, n_buckets=50)
    b2 = ab.make_buckets(ids[::-1], vals[::-1], n_buckets=50)
    assert np.allclose(b1, b2)


def test_cuped_adjust_returns_finite_theta() -> None:
    df = _make_experiment_df()
    y = df["kyc_completed"].values.astype(float)
    x_pre = df["pre_kyc_rate"].values
    treatment = (df["group"] == "treatment").values
    y_cuped, theta = ab.cuped_adjust(y, x_pre, treatment)
    assert np.isfinite(theta)
    assert y_cuped.shape == y.shape


def test_cuped_variance_reduction_positive_with_correlated_covariate() -> None:
    # Covariate strongly correlated with outcome → CUPED must cut variance.
    rng = np.random.default_rng(0)
    n = 2000
    x_pre = rng.random(n)
    y = (x_pre > 0.5).astype(float)  # deterministic function of covariate
    treatment = np.r_[np.zeros(n // 2), np.ones(n // 2)].astype(int)
    reduction = ab.cuped_variance_reduction(y, x_pre, treatment)
    assert reduction > 50.0
    # Uncorrelated covariate → near-zero reduction, never negative in practice.
    y_noise = rng.integers(0, 2, n).astype(float)
    reduction_noise = ab.cuped_variance_reduction(y_noise, x_pre, treatment)
    assert reduction_noise < 5.0


def test_aa_test_type1_rate_in_range() -> None:
    df = _make_experiment_df(n_control=500, n_treatment=500)
    aa = ab.aa_test(df, n_iter=200, seed=42)
    assert 0.0 <= aa["type1_rate"] <= 1.0
    assert aa["n_iter"] == 200
