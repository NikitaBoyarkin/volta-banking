"""Tests for volta_assisted_cac.py — 45+ acquisition economics (RAT v2, risk #1)."""

from __future__ import annotations

import numpy as np
import pandas as pd

import volta_assisted_cac as vac
from generate_assisted_cac_data import (
    CHANNEL_CAC,
    CHANNEL_CHURN_MULT,
    SEGMENT_ARPU,
    SEGMENT_CHURN,
    effective_churn,
    user_ltv,
)


def _make_df() -> pd.DataFrame:
    """Small deterministic frame mirroring the generator's segment × channel grid."""
    rng = np.random.default_rng(1)
    rows: list[dict[str, float | str | int]] = []
    uid = 0
    for segment in vac.SEGMENT_ORDER:
        for channel in vac.CHANNEL_ORDER:
            for _ in range(120):
                uid += 1
                arpu = SEGMENT_ARPU[segment]
                churn = effective_churn(segment, channel)
                months = int(min(rng.geometric(churn), 60))
                cac = CHANNEL_CAC[channel]
                rows.append(
                    {
                        "user_id": uid,
                        "segment": segment,
                        "channel": channel,
                        "cac_eur": cac,
                        "monthly_arpu_eur": arpu,
                        "contribution_margin": 0.70,
                        "monthly_churn_rate": churn,
                        "months_retained": months,
                        "ltv_eur": user_ltv(arpu, months),
                    }
                )
    return pd.DataFrame(rows)


def test_45_plus_fails_ltv_cac_gate() -> None:
    blended = vac.blended_by_segment(_make_df())
    assert blended.loc[vac.GAP_SEGMENT, "ltv_cac"] < vac.GATE_LTV_CAC
    assert not blended.loc[vac.GAP_SEGMENT, "passes"]


def test_anchor_beats_gap_blended() -> None:
    blended = vac.blended_by_segment(_make_df())
    assert blended.loc[vac.ANCHOR_SEGMENT, "ltv_cac"] > blended.loc[vac.GAP_SEGMENT, "ltv_cac"]


def test_referral_is_best_channel() -> None:
    ue = vac.segment_channel_economics(_make_df())
    for seg in vac.SEGMENT_ORDER:
        referral = ue.loc[(seg, "referral"), "ltv_cac"]
        others = [ue.loc[(seg, c), "ltv_cac"] for c in vac.CHANNEL_ORDER if c != "referral"]
        assert referral > max(others)


def test_assisted_has_lowest_churn_multiplier() -> None:
    assert CHANNEL_CHURN_MULT["assisted"] == min(CHANNEL_CHURN_MULT.values())
    assert CHANNEL_CHURN_MULT["assisted"] < 1.0


def test_bootstrap_ci_below_gate_for_gap() -> None:
    ci = vac.bootstrap_ltv_cac(_make_df(), vac.GAP_SEGMENT, vac.ASSISTED_CHANNEL, n_boot=500)
    assert ci["hi"] < vac.GATE_LTV_CAC
    assert ci["lo"] < ci["ratio"] < ci["hi"]


def test_bootstrap_empty_slice_is_nan() -> None:
    ci = vac.bootstrap_ltv_cac(_make_df(), "nonexistent_segment", n_boot=50)
    assert np.isnan(ci["ratio"])


def test_anchor_gap_contrast_positive() -> None:
    contrast = vac.anchor_gap_contrast(_make_df())
    assert contrast["diff"] > 0
    assert contrast["p"] < 0.05


def test_gate_table_marks_failures() -> None:
    gates = vac.gate_table(_make_df())
    assert not gates.loc[(vac.GAP_SEGMENT, "assisted"), "passes"]
    assert gates.loc[(vac.ANCHOR_SEGMENT, "referral"), "passes"]


def test_assisted_failure_detail_gap_to_gate_negative() -> None:
    detail = vac.assisted_failure_detail(_make_df())
    assert (detail["gap_to_gate"] < 0).all()


def test_plot_ltv_cac_writes_png_and_md(tmp_path) -> None:
    out = tmp_path / "ltv_cac.png"
    path = vac.plot_ltv_cac(out)
    assert path == out
    assert out.exists() and out.stat().st_size > 1000
    assert out.with_suffix(".md").exists()


def test_plot_payback_writes_png(tmp_path) -> None:
    out = tmp_path / "payback.png"
    vac.plot_payback(out)
    assert out.exists() and out.stat().st_size > 1000


def test_effective_churn_bounds() -> None:
    assert 0.005 <= effective_churn("digital_newcomers", "assisted") <= 0.5
    assert SEGMENT_CHURN["digital_newcomers"] > SEGMENT_CHURN["young_professionals"]
