"""Tests for volta_funnel_analysis.py — Project 1 funnel analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import volta_funnel_analysis as vf


def _make_funnel_df() -> pd.DataFrame:
    """Monotonic funnel: 100 installs → 80 reg → 60 kyc_start → 40 kyc_complete
    → 30 card → 20 first_tx. Users 0-19 pass every stage; later users drop off."""
    n = 100
    return pd.DataFrame(
        {
            "app_install": np.ones(n, dtype=int),
            "registration": np.r_[np.ones(80), np.zeros(20)].astype(int),
            "kyc_start": np.r_[np.ones(60), np.zeros(40)].astype(int),
            "kyc_complete": np.r_[np.ones(40), np.zeros(60)].astype(int),
            "card_ordered": np.r_[np.ones(30), np.zeros(70)].astype(int),
            "first_tx": np.r_[np.ones(20), np.zeros(80)].astype(int),
            "device": ["ios"] * n,
            "channel": ["referral"] * n,
            "age_group": ["18-24"] * n,
        }
    )


def test_compute_funnel_counts_and_conversions() -> None:
    metrics = vf.compute_funnel(_make_funnel_df())
    assert metrics["counts"] == [100, 80, 60, 40, 30, 20]
    assert metrics["overall_conv"][-1] == 20.0
    # Step conversion: 100, 80, 75, 66.67, 75, 66.67
    assert metrics["step_conv"][0] == 100.0
    assert metrics["step_conv"][1] == 80.0
    assert metrics["step_conv"][3] == pytest.approx(66.67, abs=0.01)
    assert metrics["drop_off"][1] == 20


def test_compute_funnel_asserts_monotonicity() -> None:
    df = _make_funnel_df()
    # Drop registration below kyc_start (60) to break monotonicity.
    df.loc[:50, "registration"] = 0
    try:
        vf.compute_funnel(df)
    except AssertionError:
        return
    raise AssertionError("compute_funnel should assert on non-monotonic funnel")


def test_biggest_drops_distinguishes_absolute_and_relative() -> None:
    metrics = vf.compute_funnel(_make_funnel_df())
    drops = vf.biggest_drops(metrics)
    # Absolute: Registration loses 20 users (tied with KYC Start, first wins).
    assert drops["abs_step"] == "Registration"
    assert drops["abs_count"] == 20
    # Relative: KYC Complete has the lowest step conversion (66.67%).
    assert drops["rel_step"] == "KYC Complete"
    assert drops["rel_step_conv"] == pytest.approx(66.67, abs=0.01)


def test_wilson_ci_contains_p_hat_and_narrows_with_n() -> None:
    lo, hi = vf.wilson_ci(50, 100)
    assert lo < 0.5 < hi
    assert lo > 0.4  # Wilson pulls toward 0.5, not the naive 0.5 ± 0.098
    # Larger n → narrower interval.
    lo_small, hi_small = vf.wilson_ci(5, 10)
    lo_big, hi_big = vf.wilson_ci(500, 1000)
    assert (hi_big - lo_big) < (hi_small - lo_small)
    # Zero total → degenerate interval, no crash.
    assert vf.wilson_ci(0, 0) == (0.0, 0.0)


def test_step_conversion_cis_first_step_is_certain() -> None:
    metrics = vf.compute_funnel(_make_funnel_df())
    cis = vf.step_conversion_cis(metrics)
    assert cis[0] == (1.0, 1.0)
    assert len(cis) == len(vf.FUNNEL_LABELS)
    # Every CI must contain its point estimate.
    for step_conv, (lo, hi) in zip(metrics["step_conv"], cis, strict=True):
        assert lo <= step_conv / 100 <= hi


def test_chi_square_activation_detects_difference() -> None:
    df = pd.DataFrame(
        {
            "first_tx": np.r_[np.ones(35), np.zeros(15), np.ones(15), np.zeros(35)].astype(int),
            "channel": ["a"] * 50 + ["b"] * 50,
        }
    )
    r = vf.chi_square_activation(df, "channel", "a", "b")
    assert r["a_rate"] == 70.0
    assert r["b_rate"] == 30.0
    assert r["p_value"] < 0.05
    assert r["chi2"] > 0


def test_load_data_normalises_casing() -> None:
    df = vf.load_data()
    assert len(df) == 10_000
    assert set(df["device"]) <= {"ios", "android"}
    assert set(df["channel"]) <= {"app_store", "email", "organic_search", "paid_social", "referral"}


def test_funnel_summary_table_shape() -> None:
    metrics = vf.compute_funnel(_make_funnel_df())
    table = vf.funnel_summary_table(metrics)
    assert list(table.columns) == ["Step", "Users", "Overall Conv %", "Step Conv %", "Drop-off"]
    assert len(table) == len(vf.FUNNEL_LABELS)
