"""Tests for volta_anchor_cac.py — anchor launch CAC at scale (RAT v2, risk #4)."""

from __future__ import annotations

import numpy as np
import pandas as pd

import volta_anchor_cac as vac
from generate_anchor_cac_data import (
    ANCHOR_SOM,
    BUCKET_USERS,
    CHANNEL_SPECS,
    GATE_LTV_CAC,
    marginal_cac,
)


def _make_df() -> pd.DataFrame:
    """Small deterministic bucket frame mirroring the generator."""
    rows: list[dict[str, float | str | int]] = []
    bid = 0
    for channel, capacity, base, saturation, arpu, churn in CHANNEL_SPECS:
        for i in range(capacity):
            bid += 1
            rows.append(
                {
                    "bucket_id": bid,
                    "channel": channel,
                    "users": BUCKET_USERS,
                    "marginal_cac_eur": marginal_cac(base, saturation, i, capacity),
                    "arpu_eur": arpu,
                    "monthly_churn_rate": churn,
                    "ltv_eur": arpu * 0.70 / churn,
                }
            )
    return pd.DataFrame(rows)


def test_allocate_fills_cheapest_first() -> None:
    df = _make_df()
    alloc = vac.allocate(df, 10_000)
    assert alloc["mix"].get("referral", 0) == 10_000
    assert alloc["blended_cac"] < 25.0


def test_blended_cac_increases_with_scale() -> None:
    df = _make_df()
    small = vac.allocate(df, 20_000)["blended_cac"]
    large = vac.allocate(df, 200_000)["blended_cac"]
    assert large > small


def test_ltv_cac_decreases_with_scale() -> None:
    df = _make_df()
    small = vac.allocate(df, 20_000)["ltv_cac"]
    large = vac.allocate(df, 200_000)["ltv_cac"]
    assert small > large


def test_small_scale_passes_gates() -> None:
    alloc = vac.allocate(_make_df(), 30_000)
    assert alloc["passes"]
    assert alloc["ltv_cac"] >= GATE_LTV_CAC
    assert alloc["payback_months"] <= vac.GATE_PAYBACK_MONTHS


def test_som_fails_gates() -> None:
    alloc = vac.allocate(_make_df(), ANCHOR_SOM)
    assert not alloc["passes"]
    assert alloc["ltv_cac"] < GATE_LTV_CAC
    assert alloc["payback_months"] > vac.GATE_PAYBACK_MONTHS


def test_break_even_scale_below_som() -> None:
    be = vac.break_even_scale(_make_df())
    assert 0 < be < ANCHOR_SOM


def test_scale_table_monotonic_cac() -> None:
    table = vac.scale_table(_make_df(), [10_000, 50_000, 150_000])
    assert table["blended_cac"].is_monotonic_increasing
    assert table["ltv_cac"].is_monotonic_decreasing


def test_cheap_capacity_excludes_paid() -> None:
    df = _make_df()
    total = int(df["users"].sum())
    no_paid = vac.cheap_capacity(df, exclude=["paid_social"])
    assert no_paid < total
    assert no_paid == total - 200 * BUCKET_USERS


def test_channel_summary_gate_cac() -> None:
    summary = vac.channel_summary(_make_df())
    assert (summary["gate_cac"] > 0).all()
    assert summary.loc["referral", "cac_min"] < summary.loc["assisted", "cac_min"]


def test_allocation_payback_positive() -> None:
    alloc = vac.allocate(_make_df(), 50_000)
    assert alloc["payback_months"] > 0
    assert np.isfinite(alloc["blended_cac"])


def test_plot_cac_curves_writes_png_and_md(tmp_path) -> None:
    out = tmp_path / "curves.png"
    path = vac.plot_cac_curves(out)
    assert path == out
    assert out.exists() and out.stat().st_size > 1000
    assert out.with_suffix(".md").exists()


def test_plot_scale_writes_png(tmp_path) -> None:
    out = tmp_path / "scale.png"
    vac.plot_scale(out)
    assert out.exists() and out.stat().st_size > 1000
