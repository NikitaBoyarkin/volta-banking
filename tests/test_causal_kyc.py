"""Tests for volta_causal_kyc.py — difference-in-differences causal layer (REQ-201)."""

from __future__ import annotations

import pandas as pd
import pytest

import volta_causal_kyc as vck
from generate_causal_kyc_data import (
    ATT_ACTIVATED,
    ATT_M1_TOTAL,
    ATT_M3_TOTAL,
    generate_panel,
)


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return generate_panel()


def _tiny_frame() -> pd.DataFrame:
    """Minimal 2x2 frame with hand-computable DiD."""
    rows = [
        # comparison: 0.2 -> 0.3 (change +0.1)
        {"treated": 0, "post": 0, "y": 0.2},
        {"treated": 0, "post": 0, "y": 0.2},
        {"treated": 0, "post": 1, "y": 0.3},
        {"treated": 0, "post": 1, "y": 0.3},
        # treated: 0.4 -> 0.6 (change +0.2) → DiD = +0.1
        {"treated": 1, "post": 0, "y": 0.4},
        {"treated": 1, "post": 0, "y": 0.4},
        {"treated": 1, "post": 1, "y": 0.6},
        {"treated": 1, "post": 1, "y": 0.6},
    ]
    return pd.DataFrame(rows)


def test_did_2x2_math() -> None:
    assert abs(vck.did_2x2(_tiny_frame(), "y") - 0.1) < 1e-9


def test_naive_pre_post_math() -> None:
    assert abs(vck.naive_pre_post(_tiny_frame(), "y") - 0.15) < 1e-9


def test_regression_did_recovers_known_effect(panel: pd.DataFrame) -> None:
    """The estimator recovers the injected total ATT, and the CI covers it."""
    for outcome, truth in [
        ("activated", ATT_ACTIVATED),
        ("retained_m1", ATT_M1_TOTAL),
        ("retained_m3", ATT_M3_TOTAL),
    ]:
        r = vck.regression_did(panel, outcome)
        assert r["att"] > 0
        assert abs(r["att"] - truth) < 0.02, (outcome, r["att"], truth)
        assert r["ci_lower"] <= truth <= r["ci_upper"], outcome
        assert r["p"] < 0.05


def test_placebo_is_null(panel: pd.DataFrame) -> None:
    """A fake cutoff in the pre-period should produce an effect of ~0."""
    for outcome in vck.OUTCOMES:
        r = vck.regression_did(panel, outcome, cutoff=vck.PLACEBO_CUTOFF, restrict_pre=vck.CUTOFF)
        assert r["ci_lower"] <= 0 <= r["ci_upper"]


def test_parallel_trends_no_pretrend(panel: pd.DataFrame) -> None:
    for outcome in vck.OUTCOMES:
        t = vck.parallel_trends(panel, outcome)
        assert t["p"] > 0.05


def test_balance_passes_smd_gate(panel: pd.DataFrame) -> None:
    balance = vck.balance_table(panel)
    assert float(balance["abs_smd"].max()) < vck.SMD_BLOCK_THRESHOLD


def test_overlap_is_substantial(panel: pd.DataFrame) -> None:
    overlap = vck.overlap_diagnostic(panel)
    assert overlap["share_in_support"] > 0.95
    assert overlap["support_lower"] < overlap["support_upper"]


def test_plot_trends_writes_png(panel: pd.DataFrame, tmp_path) -> None:
    out = tmp_path / "causal.png"
    path = vck.plot_trends(panel, out)
    assert path == out
    assert out.exists()
    assert out.stat().st_size > 1000


def test_main_runs(capsys) -> None:
    vck.main()
    out = capsys.readouterr().out
    assert "Analysis complete" in out
    assert "LIMITATION" in out
