"""Tests for volta_spend_analysis.py."""

from __future__ import annotations

import pytest

from volta_spend_analysis import (
    TOP_MERCHANTS,
    declined_by_category,
    load_data,
    monthly_spend,
    plot_category_spend,
    plot_monthly_trend,
    spend_by_category,
    spend_by_channel,
    top_merchants,
)


def test_load_data_has_expected_columns() -> None:
    df = load_data()
    assert {"transaction_id", "user_id", "tx_date", "amount_eur", "category"} <= set(df.columns)
    assert len(df) > 0


def test_spend_by_category_share_sums_to_100() -> None:
    cat = spend_by_category(load_data())
    assert {"total_eur", "tx_count", "avg_eur", "share_pct"} <= set(cat.columns)
    assert cat["share_pct"].sum() == pytest.approx(100, abs=0.5)
    assert cat["total_eur"].is_monotonic_decreasing


def test_spend_by_channel_has_share() -> None:
    ch = spend_by_channel(load_data())
    assert {"total_eur", "tx_count", "share_pct"} <= set(ch.columns)
    assert ch["share_pct"].sum() == pytest.approx(100, abs=0.5)


def test_top_merchants_capped() -> None:
    merch = top_merchants(load_data())
    assert len(merch) <= TOP_MERCHANTS
    assert merch["total_eur"].is_monotonic_decreasing


def test_declined_by_category_rates_in_unit_interval() -> None:
    rate = declined_by_category(load_data())
    assert rate.between(0, 1).all()
    assert rate.is_monotonic_decreasing


def test_monthly_spend_positive() -> None:
    monthly = monthly_spend(load_data())
    assert len(monthly) > 0
    assert (monthly > 0).all()


def test_plot_category_spend_writes_png(tmp_path) -> None:
    cat = spend_by_category(load_data())
    out = plot_category_spend(cat, tmp_path / "cat.png")
    assert out.exists() and out.stat().st_size > 0


def test_plot_monthly_trend_writes_png(tmp_path) -> None:
    monthly = monthly_spend(load_data())
    out = plot_monthly_trend(monthly, tmp_path / "trend.png")
    assert out.exists() and out.stat().st_size > 0
