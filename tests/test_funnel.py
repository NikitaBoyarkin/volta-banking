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


# ── Sprint 1: F1-F3 ──────────────────────────────────────────────────────────
def _make_segmented_funnel_df() -> pd.DataFrame:
    """Two channels with very different KYC completion to exercise step tests."""
    rng = np.random.default_rng(0)
    n = 400
    channel = np.where(rng.random(n) < 0.5, "referral", "paid_social")
    # Referral: high completion; paid_social: low.
    p_complete = np.where(channel == "referral", 0.85, 0.40)
    kyc_complete = (rng.random(n) < p_complete).astype(int)
    # Everyone reached kyc_start.
    kyc_start = np.ones(n, dtype=int)
    registration = np.ones(n, dtype=int)
    app_install = np.ones(n, dtype=int)
    card_ordered = (kyc_complete & (rng.random(n) < 0.8)).astype(int)
    first_tx = (card_ordered & (rng.random(n) < 0.7)).astype(int)
    return pd.DataFrame(
        {
            "app_install": app_install,
            "registration": registration,
            "kyc_start": kyc_start,
            "kyc_complete": kyc_complete,
            "card_ordered": card_ordered,
            "first_tx": first_tx,
            "channel": channel,
            "device": ["ios"] * n,
            "age_group": ["25-34"] * n,
        }
    )


def test_step_segment_tests_detects_channel_difference() -> None:
    df = _make_segmented_funnel_df()
    results = vf.step_segment_tests(df, "channel")
    # 5 transitions, each testable.
    assert len(results) == 5
    # KYC Start → KYC Complete should be strongly significant (85% vs 40%).
    kyc_test = next(r for r in results if "KYC Start → KYC Complete" in r["transition"])
    assert kyc_test["p_value"] < 0.001
    rates = kyc_test["rates_by_segment"]
    assert rates["referral"] > rates["paid_social"]


def test_step_segment_tests_uniform_segment_non_significant() -> None:
    df = _make_funnel_df()  # single channel "referral" everywhere
    # Only one segment value → chi2 needs ≥2 columns → returns no tests for that col.
    results = vf.step_segment_tests(df, "channel")
    assert results == []


def test_holm_correct() -> None:
    # 3 p-values: 0.01, 0.02, 0.5; Holm at α=0.05 → reject 0.01 and 0.02.
    rej = vf.holm_correct([0.01, 0.02, 0.5])
    assert rej == [True, True, False]


def test_time_to_convert_runs_on_committed_data() -> None:
    df = vf.load_data()
    if "install_date" not in df.columns:
        pytest.skip("install_date column missing — run generate_funnel_data.py")
    summary = vf.time_to_convert(df)
    assert "median_hours" in summary.columns
    assert len(summary) == df["channel"].nunique()
    # Referral should be fastest (generator design).
    assert summary.index[0] == "referral"
    assert (summary["median_hours"] > 0).all()


def test_plot_funnel_heatmap_writes_png(tmp_path) -> None:
    df = _make_segmented_funnel_df()
    out = tmp_path / "heatmap.png"
    path = vf.plot_funnel_heatmap(df, out)
    assert path == out
    assert out.exists()
    assert out.stat().st_size > 1000
