"""Tests for volta_nps_trends.py."""

from __future__ import annotations

import pytest

from volta_nps_trends import (
    comment_by_segment,
    load_data,
    monthly_nps,
    nps_by_driver,
    nps_score,
    plot_driver_nps,
    plot_monthly_nps,
    segment_mix,
)


def test_load_data_has_expected_columns() -> None:
    df = load_data()
    assert {"response_id", "user_id", "survey_date", "nps_score", "segment"} <= set(df.columns)
    assert len(df) > 0


def test_nps_score_in_range() -> None:
    assert -100 <= nps_score(load_data()) <= 100


def test_monthly_nps_shape() -> None:
    monthly = monthly_nps(load_data())
    assert {"nps", "responses"} <= set(monthly.columns)
    assert len(monthly) > 0
    assert monthly["nps"].between(-100, 100).all()


def test_nps_by_driver_sorted_desc() -> None:
    by_driver = nps_by_driver(load_data())
    assert by_driver["nps"].is_monotonic_decreasing
    assert by_driver["responses"].sum() == len(load_data())


def test_segment_mix_sums_to_100() -> None:
    mix = segment_mix(load_data())
    assert set(mix.index) == {"promoter", "passive", "detractor"}
    assert mix.sum() == pytest.approx(100, abs=0.5)


def test_comment_by_segment_reindexed() -> None:
    by_seg = comment_by_segment(load_data())
    assert list(by_seg.index) == ["promoter", "passive", "detractor"]
    assert {"mean", "count"} <= set(by_seg.columns)


def test_plot_monthly_nps_writes_png(tmp_path) -> None:
    monthly = monthly_nps(load_data())
    out = plot_monthly_nps(monthly, tmp_path / "nps.png")
    assert out.exists() and out.stat().st_size > 0


def test_plot_driver_nps_writes_png(tmp_path) -> None:
    by_driver = nps_by_driver(load_data())
    out = plot_driver_nps(by_driver, tmp_path / "drivers.png")
    assert out.exists() and out.stat().st_size > 0
