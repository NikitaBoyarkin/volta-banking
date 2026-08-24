"""Tests for volta_attribution.py."""

from __future__ import annotations

import pytest

from volta_attribution import (
    build_comparison,
    build_journeys,
    first_touch_credit,
    last_touch_credit,
    linear_credit,
    load_data,
    plot_attribution,
    shapley_credit,
)

TOTAL_REV_EPS = 50.0


def test_load_data() -> None:
    df = load_data()
    assert {"journey_id", "touch_order", "channel", "revenue"} <= set(df.columns)
    assert len(df) > 0


def test_build_journeys_ordered_channels() -> None:
    df = load_data()
    journeys = build_journeys(df)
    assert len(journeys) == df["journey_id"].nunique()
    assert all(len(j["channels"]) >= 1 for j in journeys)
    assert all(j["revenue"] > 0 for j in journeys)


def test_single_touch_journey_full_credit() -> None:
    credit = shapley_credit(["email"], 100.0)
    assert credit["email"] == pytest.approx(100.0, abs=1e-6)


def test_shapley_sums_to_revenue() -> None:
    credit = shapley_credit(["paid_social", "referral", "display"], 300.0)
    assert sum(credit.values()) == pytest.approx(300.0, abs=1e-6)


def test_shapley_prefers_higher_influence_channel() -> None:
    credit = shapley_credit(["display", "referral"], 200.0)
    assert credit["referral"] > credit["display"]


def test_models_sum_to_total_revenue() -> None:
    journeys = build_journeys(load_data())
    total = sum(j["revenue"] for j in journeys)
    for fn in (first_touch_credit, last_touch_credit, linear_credit):
        credit = fn(journeys)
        assert sum(credit.values()) == pytest.approx(total, abs=TOTAL_REV_EPS)


def test_build_comparison_has_all_models() -> None:
    journeys = build_journeys(load_data())
    comp = build_comparison(journeys)
    for col in ("first_touch", "last_touch", "linear", "shapley", "share_pct"):
        assert col in comp.columns


def test_plot_writes_png(tmp_path) -> None:
    journeys = build_journeys(load_data())
    comp = build_comparison(journeys)
    out = plot_attribution(comp, tmp_path / "attr.png")
    assert out.exists() and out.stat().st_size > 0
