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


# ── Sprint 1: A1-A4 ──────────────────────────────────────────────────────────
def _make_guardrail_df(
    n: int = 2000, treat_churn_effect: float = 0.0, seed: int = 0
) -> pd.DataFrame:
    """Build a df with churn + revenue guardrails. `treat_churn_effect` > 0
    simulates a guardrail violation (treatment increases churn)."""
    rng = np.random.default_rng(seed)
    group = np.where(rng.random(n) < 0.5, "treatment", "control")
    kyc = (rng.random(n) < 0.6).astype(int)
    churn_p = np.where(kyc == 1, 0.06, 0.30)
    churn_p[group == "treatment"] += treat_churn_effect
    churned = (rng.random(n) < churn_p).astype(int)
    revenue = np.where(kyc == 1, 18.0, 3.5) + rng.normal(0, 5, n)
    return pd.DataFrame(
        {
            "group": group,
            "kyc_completed": kyc,
            "churned_30d": churned,
            "revenue_30d_eur": np.clip(revenue, 0, None),
        }
    )


def test_guardrail_test_clean_when_no_effect() -> None:
    df = _make_guardrail_df(treat_churn_effect=0.0)
    g = ab.guardrail_test(df, "churned_30d", direction="lower")
    assert g["violated"] is False
    # Revenue also clean.
    gr = ab.guardrail_test(df, "revenue_30d_eur", direction="higher")
    assert gr["violated"] is False


def test_guardrail_test_detects_violation() -> None:
    df = _make_guardrail_df(treat_churn_effect=0.10, seed=1)
    g = ab.guardrail_test(df, "churned_30d", direction="lower")
    assert g["violated"] is True
    assert g["p_bad_direction"] < 0.05
    assert g["diff"] > 0  # treatment churn higher


def test_hte_analysis_returns_bh_corrected_table() -> None:
    df = _make_experiment_df(n_control=2000, n_treatment=2000)
    # Add segmentation columns.
    rng = np.random.default_rng(2)
    df["age_group"] = rng.choice(["18-24", "25-34", "35-44", "45+"], size=len(df))
    df["device"] = rng.choice(["android", "ios", "web"], size=len(df))
    df["channel"] = rng.choice(["app_store", "google_play", "website", "referral"], size=len(df))
    hte = ab.hte_analysis(df)
    assert len(hte) == 4 + 3 + 4  # 11 segment values
    assert {"p_bh", "significant_bh", "lift_pp"} <= set(hte.columns)
    # BH-adjusted p must be >= raw p (adjustment inflates p-values).
    assert (hte["p_bh"] >= hte["p_raw"] - 1e-9).all()
    # Lift in pp = (treatment - control) * 100.
    assert hte["lift_pp"].between(-100, 100).all()


def test_bh_adjusted_pvals_monotone_and_bounded() -> None:
    pvals = [0.001, 0.02, 0.03, 0.5, 0.9]
    q = ab._bh_adjusted_pvals(pvals)
    assert all(0.0 <= x <= 1.0 for x in q)
    # Sorted q-values must be monotone non-decreasing.
    order = np.argsort(pvals)
    q_sorted = np.array(q)[order]
    assert all(q_sorted[i] <= q_sorted[i + 1] + 1e-9 for i in range(len(q_sorted) - 1))


def test_sequential_bounds_obf_decreasing() -> None:
    bounds = ab.sequential_bounds(n_looks=4, method="obrien_fleming")
    assert len(bounds) == 4
    # OBF boundaries decrease as info accumulates (early looks hardest).
    z = bounds["z_boundary"].values
    assert all(z[i] > z[i + 1] for i in range(len(z) - 1))
    # Nominal alpha increases toward the final look.
    a = bounds["nominal_alpha"].values
    assert a[-1] > a[0]


def test_sequential_bounds_rejects_large_z() -> None:
    bounds = ab.sequential_bounds(n_looks=4, method="obrien_fleming")
    verdict = ab.sequential_verdict(5.0, bounds)
    assert verdict["reject"] is True
    verdict_neg = ab.sequential_verdict(1.0, bounds)
    assert verdict_neg["reject"] is False


def test_power_at_mde_increases_with_mde_and_n() -> None:
    p1 = ab.power_at_mde(0.5, 0.03, n_per_arm=1000)
    p2 = ab.power_at_mde(0.5, 0.08, n_per_arm=1000)
    assert p2 > p1  # bigger effect → more power
    p3 = ab.power_at_mde(0.5, 0.05, n_per_arm=5000)
    assert p3 > ab.power_at_mde(0.5, 0.05, n_per_arm=500)  # more n → more power
    assert 0.0 <= p1 <= 1.0


def test_plot_power_curve_writes_png(tmp_path) -> None:
    out = tmp_path / "power.png"
    path = ab.plot_power_curve(0.5, 5000, out, planned_mde=0.05)
    assert path == out
    assert out.exists()
    assert out.stat().st_size > 1000
