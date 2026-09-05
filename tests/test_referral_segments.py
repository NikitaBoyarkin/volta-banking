"""Tests for volta_referral_segments.py — referral conversion by JTBD segment (risk #5)."""

from __future__ import annotations

import numpy as np
import pandas as pd

import volta_referral_segments as vrs
from generate_referral_segments_data import (
    P_FIRST_TX_GIVEN_KYC,
    SEGMENT_BASE_KYC,
    SEGMENT_COHORT_DIST,
    SEGMENT_SPECS,
    acceptance_probability,
)


def _make_df() -> pd.DataFrame:
    """Small deterministic frame mirroring the generator (segment-dependent funnel)."""
    rng = np.random.default_rng(0)
    rows: list[dict[str, float | str | int]] = []
    for segment, n, _, _, _ in SEGMENT_SPECS:
        for r in range(n):
            cohort = rng.choice(vrs.COHORT_ORDER, p=SEGMENT_COHORT_DIST[segment])
            channel = rng.choice(vrs.CHANNEL_ORDER, p=[0.5, 0.3, 0.2])
            p_accept = acceptance_probability(segment, cohort, channel)
            if rng.random() > p_accept:
                status = "sent"
            elif rng.random() > SEGMENT_BASE_KYC[segment]:
                status = "accepted"
            elif rng.random() > P_FIRST_TX_GIVEN_KYC:
                status = "kyc_completed"
            else:
                status = "first_tx"
            rows.append(
                {
                    "referral_id": r,
                    "referee_id": r,
                    "jtbd_segment": segment,
                    "cohort": cohort,
                    "channel": channel,
                    "status": status,
                    "reward_eur": 0.0,
                    "first_tx": int(status == "first_tx"),
                }
            )
    return pd.DataFrame(rows)


def test_funnel_anchor_beats_gap() -> None:
    funnel = vrs.funnel_by_segment(_make_df())
    assert (
        funnel.loc["young_professionals", "overall_conv"]
        > funnel.loc["digital_newcomers", "overall_conv"]
    )
    assert (
        funnel.loc["premium_status", "overall_conv"]
        > funnel.loc["family_budgeters", "overall_conv"]
    )


def test_chi_square_significant() -> None:
    df = _make_df()
    chi = vrs.chi_square_segment_status(df)
    assert chi["p_value"] < 0.05
    assert chi["dof"] == (len(vrs.SEGMENT_ORDER) - 1) * (len(vrs.STATUS_ORDER) - 1)


def test_two_proportion_ztest_significant() -> None:
    df = _make_df()
    n1 = int((df["jtbd_segment"] == vrs.ANCHOR_SEGMENT).sum())
    x1 = int(((df["jtbd_segment"] == vrs.ANCHOR_SEGMENT) & (df["first_tx"] == 1)).sum())
    n2 = int((df["jtbd_segment"] == "digital_newcomers").sum())
    x2 = int(((df["jtbd_segment"] == "digital_newcomers") & (df["first_tx"] == 1)).sum())
    z, p = vrs.two_proportion_ztest(n1, x1, n2, x2)
    assert p < 0.05
    assert x1 / n1 > x2 / n2
    assert z > 0


def test_channel_inapp_beats_link() -> None:
    ch = vrs.conversion_by_channel(_make_df())
    assert ch.loc["in_app", "conv_rate"] > ch.loc["link", "conv_rate"]


def test_channel_within_gap_inapp_beats_link() -> None:
    ch = vrs.channel_within_gap(_make_df())
    assert ch.loc["in_app", "conv_rate"] > ch.loc["link", "conv_rate"]


def test_plot_writes_png(tmp_path) -> None:
    df = _make_df()
    out = tmp_path / "referral.png"
    vrs.plot_conversion_by_segment(df, out)
    assert out.exists()
    assert out.stat().st_size > 1000
