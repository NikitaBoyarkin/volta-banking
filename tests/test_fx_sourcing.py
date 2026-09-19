"""Tests for volta_fx_sourcing.py — FX cost feasibility (RAT v2, risk #2)."""

from __future__ import annotations

import numpy as np
import pandas as pd

import volta_fx_sourcing as vfs
from generate_fx_sourcing_data import (
    GATE_FX_COST_PCT,
    PROVIDER_SPECS,
    TERM_HEDGE,
    quoted_cost,
)


def _make_df() -> pd.DataFrame:
    """Small deterministic quote frame mirroring the generator grid."""
    rng = np.random.default_rng(3)
    rows: list[dict[str, float | str | int]] = []
    for pid, (provider, base, slope, settle, rating) in enumerate(PROVIDER_SPECS, start=1):
        for volume in vfs.VOLUME_TIERS:
            for term in vfs.TERM_ORDER:
                quoted = quoted_cost(base, slope, volume) * float(rng.normal(1.0, 0.01))
                hedging = TERM_HEDGE[term] * float(rng.normal(1.0, 0.03))
                rows.append(
                    {
                        "provider_id": pid,
                        "provider_name": provider,
                        "monthly_volume_eur": volume,
                        "term_months": term,
                        "quoted_cost_pct": quoted,
                        "hedging_cost_pct": hedging,
                        "effective_cost_pct": quoted + hedging,
                        "settlement_days": settle,
                        "credit_rating": rating,
                    }
                )
    return pd.DataFrame(rows)


def test_cost_decreases_with_volume() -> None:
    curve = vfs.best_cost_by_volume(_make_df())
    assert curve.is_monotonic_decreasing


def test_gate_reachable_at_high_volume_only() -> None:
    df = _make_df()
    curve = vfs.best_cost_by_volume(df)
    assert curve.iloc[0] > GATE_FX_COST_PCT
    assert curve.iloc[-1] <= GATE_FX_COST_PCT


def test_required_volume_is_between_tiers() -> None:
    gate_vol = vfs.required_volume_for_gate(_make_df())
    assert 1e8 < gate_vol < 5e8


def test_required_volume_infinite_when_gate_unreachable() -> None:
    df = _make_df()
    df["effective_cost_pct"] = 2.0
    assert np.isinf(vfs.required_volume_for_gate(df))


def test_today_volume_far_below_gate() -> None:
    df = _make_df()
    ref = vfs.traveler_volume_reference()
    gate_vol = vfs.required_volume_for_gate(df)
    assert ref["current"] < gate_vol / 10
    assert ref["som"] > gate_vol


def test_best_quote_improves_with_volume() -> None:
    best = vfs.best_quote_by_volume(_make_df())
    assert best["effective_cost_pct"].is_monotonic_decreasing


def test_provider_ranking_sorted() -> None:
    rank = vfs.provider_ranking(_make_df(), volume=5e7)
    assert rank["effective_cost_pct"].is_monotonic_increasing
    assert rank["effective_cost_pct"].iloc[0] <= rank["effective_cost_pct"].iloc[-1]


def test_term_effect_longer_is_cheaper() -> None:
    term = vfs.term_effect(_make_df())
    assert term.loc[12, "effective_cost_pct"] < term.loc[1, "effective_cost_pct"]


def test_plot_volume_curve_writes_png_and_md(tmp_path) -> None:
    out = tmp_path / "curve.png"
    path = vfs.plot_volume_curve(out)
    assert path == out
    assert out.exists() and out.stat().st_size > 1000
    assert out.with_suffix(".md").exists()


def test_plot_provider_ranking_writes_png(tmp_path) -> None:
    out = tmp_path / "ranking.png"
    vfs.plot_provider_ranking(out)
    assert out.exists() and out.stat().st_size > 1000
