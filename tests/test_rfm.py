"""Tests for volta_rfm_analysis.py."""

from __future__ import annotations

import pytest

from volta_rfm_analysis import (
    compute_rfm,
    load_data,
    plot_rfm_heatmap,
    plot_segment_sizes,
    score_rfm,
    segment_customers,
    segment_summary,
)


def test_load_data_has_expected_columns() -> None:
    df = load_data()
    assert {"customer_id", "tx_date", "amount"} <= set(df.columns)
    assert len(df) > 0


def test_compute_rfm_shape_and_types() -> None:
    df = load_data()
    rfm = compute_rfm(df)
    assert list(rfm.columns) == ["customer_id", "recency_days", "frequency", "monetary"]
    assert rfm["recency_days"].ge(0).all()
    assert rfm["frequency"].ge(1).all()
    assert rfm["monetary"].ge(0).all()


def test_score_rfm_in_1_to_5() -> None:
    df = load_data()
    scored = score_rfm(compute_rfm(df))
    for col in ("R", "F", "M"):
        assert scored[col].between(1, 5).all()


def test_segment_customers_at_least_five_labels() -> None:
    df = load_data()
    segmented = segment_customers(score_rfm(compute_rfm(df)))
    assert segmented["segment"].nunique() >= 5


def test_segment_summary_has_share() -> None:
    df = load_data()
    segmented = segment_customers(score_rfm(compute_rfm(df)))
    summary = segment_summary(segmented)
    assert {"R", "F", "M", "share"} <= set(summary.columns)
    assert summary["share"].sum() == pytest.approx(100, abs=0.2)


def test_plot_segment_sizes_writes_png(tmp_path) -> None:
    df = load_data()
    segmented = segment_customers(score_rfm(compute_rfm(df)))
    summary = segment_summary(segmented)
    out = plot_segment_sizes(summary, tmp_path / "sizes.png")
    assert out.exists() and out.stat().st_size > 0


def test_plot_rfm_heatmap_writes_png(tmp_path) -> None:
    df = load_data()
    segmented = segment_customers(score_rfm(compute_rfm(df)))
    summary = segment_summary(segmented)
    out = plot_rfm_heatmap(summary, tmp_path / "heat.png")
    assert out.exists() and out.stat().st_size > 0
