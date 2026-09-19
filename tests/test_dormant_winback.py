"""Tests for volta_dormant_winback.py — Dormant 45+ win-back (RAT v2, risk #5)."""

from __future__ import annotations

import numpy as np
import pandas as pd

import volta_dormant_winback as vdw
from generate_dormant_winback_data import (
    ARMS,
    COST_PER_ARM,
    DORMANCY_BUCKETS,
    LTV_REACTIVATED,
    reactivation_probability,
)


def _make_df() -> pd.DataFrame:
    """Small deterministic frame mirroring the generator's arm × bucket grid."""
    rng = np.random.default_rng(11)
    rows: list[dict[str, float | str | int]] = []
    uid = 0
    for arm in ARMS:
        for bucket in DORMANCY_BUCKETS:
            p = reactivation_probability(arm, bucket)
            for _ in range(4000):
                uid += 1
                rows.append(
                    {
                        "user_id": uid,
                        "jtbd_segment": "digital_newcomers",
                        "dormancy_bucket": bucket,
                        "group": arm,
                        "balance_eur": 300.0,
                        "prior_logins": 6.0,
                        "reactivated_60d": int(rng.random() < p),
                        "retained_m3": 0,
                        "arpu_eur": 3.40,
                    }
                )
    return pd.DataFrame(rows)


def test_reactivation_ordering_by_arm() -> None:
    rates = vdw.reactivation_by_arm(_make_df()).reindex(ARMS)
    assert rates.loc["human", "reactivation_pct"] > rates.loc["light_touch", "reactivation_pct"]
    assert rates.loc["light_touch", "reactivation_pct"] > rates.loc["control", "reactivation_pct"]


def test_reactivation_falls_with_dormancy() -> None:
    tab = vdw.reactivation_by_bucket_arm(_make_df())
    for arm in ARMS:
        assert tab.loc["30-60d", arm] > tab.loc["180d+", arm]


def test_arm_lift_significant_for_both_assisted() -> None:
    df = _make_df()
    for arm in ("light_touch", "human"):
        r = vdw.arm_lift(df, arm)
        assert r["lift_pp"] > 0
        assert r["p"] < 0.05


def test_human_lift_exceeds_light_touch() -> None:
    df = _make_df()
    assert vdw.arm_lift(df, "human")["lift_pp"] > vdw.arm_lift(df, "light_touch")["lift_pp"]


def test_human_never_pays_back() -> None:
    df = _make_df()
    for bucket in DORMANCY_BUCKETS:
        assert vdw.bucket_economics(df, "human", bucket)["roi"] < 1.0


def test_light_touch_pays_on_recent_buckets() -> None:
    df = _make_df()
    assert vdw.bucket_economics(df, "light_touch", "30-60d")["roi"] > 1.0
    assert vdw.bucket_economics(df, "light_touch", "60-90d")["roi"] > 1.0


def test_light_touch_fails_on_deep_dormant() -> None:
    df = _make_df()
    assert vdw.bucket_economics(df, "light_touch", "90-180d")["roi"] < 1.0


def test_targeting_rule() -> None:
    df = _make_df()
    assert "30-60d" in vdw.targeting_rule(df, "light_touch")
    assert vdw.targeting_rule(df, "human") == []


def test_roi_table_has_overall_row() -> None:
    table = vdw.roi_table(_make_df(), "light_touch")
    assert "overall (equal mix)" in table.index
    assert table.loc["overall (equal mix)", "recovered_ltv"] > 0


def test_break_even_ltv_ordering() -> None:
    df = _make_df()
    be_recent = vdw.break_even_ltv(df, "light_touch", "30-60d")
    be_deep = vdw.break_even_ltv(df, "light_touch", "90-180d")
    assert 0 < be_recent < be_deep


def test_break_even_ltv_infinite_without_lift() -> None:
    df = _make_df()
    df["reactivated_60d"] = 0
    assert np.isinf(vdw.break_even_ltv(df, "human", "30-60d"))


def test_costs_and_ltv_positive() -> None:
    assert all(v > 0 for v in COST_PER_ARM.values())
    assert all(v > 0 for v in LTV_REACTIVATED.values())
    assert COST_PER_ARM["human"] > COST_PER_ARM["light_touch"] > COST_PER_ARM["control"]


def test_plot_reactivation_writes_png_and_md(tmp_path) -> None:
    out = tmp_path / "react.png"
    path = vdw.plot_reactivation(_make_df(), out)
    assert path == out
    assert out.exists() and out.stat().st_size > 1000
    assert out.with_suffix(".md").exists()


def test_plot_roi_writes_png(tmp_path) -> None:
    out = tmp_path / "roi.png"
    vdw.plot_roi(_make_df(), out)
    assert out.exists() and out.stat().st_size > 1000
