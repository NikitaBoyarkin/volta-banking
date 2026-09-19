"""Tests for volta_premium_offers.py — segment-specific premium offers (RAT v2, risk #3)."""

from __future__ import annotations

import numpy as np
import pandas as pd

import volta_premium_offers as vpo
from generate_premium_offers_data import (
    SEGMENT_BASE_CONV,
    SEGMENT_TREAT_MULT,
    conversion_probability,
)


def _make_df() -> pd.DataFrame:
    """Small deterministic frame mirroring the generator's segment × arm grid."""
    rng = np.random.default_rng(5)
    rows: list[dict[str, float | str | int]] = []
    uid = 0
    for seg in vpo.SEGMENT_ORDER:
        for group in (vpo.CONTROL, vpo.TREATMENT):
            for _ in range(8000):
                uid += 1
                p = conversion_probability(seg, group, "Growth", 5.0, 12, 500.0)
                rows.append(
                    {
                        "user_id": uid,
                        "jtbd_segment": seg,
                        "cohort": "Growth",
                        "group": group,
                        "logins_per_week": 5.0,
                        "tx_per_month": 12,
                        "balance_eur": 500.0,
                        "converted": int(rng.random() < p),
                        "upgrade_reason": "cashback" if rng.random() < p else "none",
                    }
                )
    return pd.DataFrame(rows)


def test_gap_segments_lift_positive() -> None:
    lift = vpo.lift_by_segment(_make_df())
    for seg in vpo.GAP_SEGMENTS:
        assert lift.loc[seg, "lift_pp"] > 0


def test_gap_lift_exceeds_anchor_lift() -> None:
    lift = vpo.lift_by_segment(_make_df())
    for seg in vpo.GAP_SEGMENTS:
        assert lift.loc[seg, "lift_pp"] > lift.loc[vpo.ANCHOR_SEGMENT, "lift_pp"]


def test_anchor_lift_smallest() -> None:
    lift = vpo.lift_by_segment(_make_df())
    assert lift.loc[vpo.ANCHOR_SEGMENT, "lift_pp"] == lift["lift_pp"].min()


def test_interaction_positive_and_significant() -> None:
    lift = vpo.lift_by_segment(_make_df())
    for seg in vpo.GAP_SEGMENTS:
        it = vpo.interaction_test(lift, seg)
        assert it["diff_pp"] > 0
        assert it["p"] < 0.05


def test_residual_gap_negative() -> None:
    residual = vpo.residual_gap(_make_df())
    assert (residual["residual_gap_pp"] < 0).all()
    assert (residual["multiple_vs_anchor"] > 1).all()


def test_holm_rejects_strong_signals() -> None:
    rejects = vpo.holm([1e-12, 1e-6, 0.2, 0.4])
    assert rejects[0] and rejects[1]
    assert not rejects[2] and not rejects[3]


def test_sample_size_grows_as_mde_shrinks() -> None:
    n_small = vpo.calc_sample_size(0.02, 0.02)
    n_large = vpo.calc_sample_size(0.02, 0.01)
    assert n_large > n_small > 0


def test_business_impact_scales_with_lift() -> None:
    low = vpo.business_impact(1.0)
    high = vpo.business_impact(4.0)
    assert high["annual_arpu_eur"] > low["annual_arpu_eur"]
    assert low["incremental_users"] == 100.0


def test_srm_balanced_on_symmetric_data() -> None:
    srm = vpo.srm_check(_make_df())
    assert srm["p"] > 0.05


def test_treatment_multipliers_target_gap_segments() -> None:
    assert SEGMENT_TREAT_MULT["digital_newcomers"] > SEGMENT_TREAT_MULT["young_professionals"]
    assert SEGMENT_BASE_CONV["young_professionals"] > SEGMENT_BASE_CONV["digital_newcomers"]


def test_plot_conversion_writes_png_and_md(tmp_path) -> None:
    out = tmp_path / "conv.png"
    path = vpo.plot_conversion(_make_df(), out)
    assert path == out
    assert out.exists() and out.stat().st_size > 1000
    assert out.with_suffix(".md").exists()


def test_plot_lift_writes_png(tmp_path) -> None:
    lift = vpo.lift_by_segment(_make_df())
    out = tmp_path / "lift.png"
    vpo.plot_lift(lift, out)
    assert out.exists() and out.stat().st_size > 1000


def test_two_proportion_ztest_direction() -> None:
    z, p = vpo.two_proportion_ztest(1000, 100, 1000, 50)
    assert z > 0
    assert p < 0.05
    assert np.isfinite(z)
