"""Tests for volta_premium_upsell.py — Free→Premium conversion (risk #2)."""

from __future__ import annotations

import numpy as np
import pandas as pd

import volta_premium_upsell as vp
from generate_premium_upsell_data import SEGMENT_COHORT_DIST, SEGMENT_SPECS, conversion_probability


def _make_df() -> pd.DataFrame:
    """Small deterministic frame mirroring the generator (segment-specific engagement)."""
    rng = np.random.default_rng(0)
    rows: list[dict[str, float | str | int]] = []
    for segment, n, _, _, avg_logins, avg_tx, avg_balance in SEGMENT_SPECS:
        for u in range(n):
            cohort = rng.choice(vp.COHORT_ORDER, p=SEGMENT_COHORT_DIST[segment])
            logins = max(0.0, float(rng.normal(avg_logins, avg_logins * 0.4)))
            tx = int(rng.poisson(avg_tx))
            balance = max(0.0, float(rng.normal(avg_balance, avg_balance * 0.5)))
            channel = rng.choice(vp.CHANNEL_ORDER, p=[0.3, 0.3, 0.2, 0.2])
            p = conversion_probability(segment, cohort, logins, tx, balance, channel)
            converted = int(rng.random() < p)
            rows.append(
                {
                    "user_id": u,
                    "jtbd_segment": segment,
                    "cohort": cohort,
                    "months_since_signup": int(rng.integers(1, 25)),
                    "logins_per_week": logins,
                    "tx_per_month": tx,
                    "balance_eur": balance,
                    "offer_channel": channel,
                    "converted": converted,
                    "upgrade_reason": "none",
                }
            )
    return pd.DataFrame(rows)


def test_conversion_by_segment_contrast() -> None:
    ue = vp.conversion_by_segment(_make_df())
    assert ue.loc["young_professionals", "conv_rate"] > ue.loc["digital_newcomers", "conv_rate"]
    assert ue.loc["premium_status", "conv_rate"] > ue.loc["family_budgeters", "conv_rate"]


def test_chi_square_significant() -> None:
    df = _make_df()
    chi = vp.chi_square_segment_conversion(df)
    assert chi["p"] < 0.05
    assert chi["dof"] == (len(vp.SEGMENT_ORDER) - 1) * 1


def test_two_proportion_ztest_significant() -> None:
    df = _make_df()
    n1, x1 = vp.segment_conversion_counts(df, vp.ANCHOR_SEGMENT)
    n2, x2 = vp.segment_conversion_counts(df, vp.TRANSFER_GAP_SEGMENT)
    z = vp.two_proportion_ztest(n1, x1, n2, x2)
    assert z["p"] < 0.05
    assert z["p1"] > z["p2"]


def test_driver_importance_engagement_positive() -> None:
    imp = vp.driver_importance(_make_df())
    assert set(imp["feature"]) == set(vp.DRIVER_FEATURES)
    assert imp["coef"].is_monotonic_decreasing
    for feat in ["logins_per_week", "tx_per_month", "balance_eur"]:
        assert imp.loc[imp["feature"] == feat, "coef"].iloc[0] > 0


def test_offer_channel_inapp_beats_none() -> None:
    ch = vp.offer_channel_effect(_make_df())
    assert ch.loc["in_app", "conv_rate"] > ch.loc["none", "conv_rate"]


def test_conversion_by_segment_cohort_shape() -> None:
    tab = vp.conversion_by_segment_cohort(_make_df())
    assert list(tab.index) == vp.SEGMENT_ORDER
    assert list(tab.columns) == vp.COHORT_ORDER


def test_plot_writes_png(tmp_path) -> None:
    df = _make_df()
    out = tmp_path / "upsell.png"
    path = vp.plot_conversion_by_segment(df, out)
    assert path == out
    assert out.exists()
    assert out.stat().st_size > 1000
