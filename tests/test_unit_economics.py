"""Tests for volta_unit_economics.py — traveler unit economics (risk #1)."""

from __future__ import annotations

import numpy as np
import pandas as pd

import volta_unit_economics as vue
from generate_unit_economics_data import tx_economics


def _make_df() -> pd.DataFrame:
    """Small deterministic transaction frame mirroring the generator."""
    rng = np.random.default_rng(0)
    rows: list[dict[str, float | str | int]] = []
    for segment, n, tx_per_user, avg_amount, fx_share in [
        ("travelers", 200, 25, 120.0, 0.90),
        ("young_professionals", 200, 15, 60.0, 0.15),
        ("family_budgeters", 150, 12, 45.0, 0.05),
        ("digital_newcomers", 100, 6, 30.0, 0.05),
        ("premium_status", 50, 20, 150.0, 0.20),
    ]:
        for u in range(n):
            for _ in range(int(rng.poisson(tx_per_user))):
                is_fx = rng.random() < fx_share
                currency = rng.choice(["USD", "GBP", "THB", "JPY"]) if is_fx else "EUR"
                tx_type = (
                    "fx" if is_fx else rng.choice(["card", "atm", "transfer"], p=[0.9, 0.05, 0.05])
                )
                amount = max(1.0, float(rng.normal(avg_amount, avg_amount * 0.3)))
                revenue, cost = tx_economics(tx_type, amount)
                rows.append(
                    {
                        "user_id": u,
                        "segment": segment,
                        "currency": currency,
                        "tx_type": tx_type,
                        "amount_eur": amount,
                        "revenue_eur": revenue,
                        "cost_eur": cost,
                        "margin_eur": revenue - cost,
                    }
                )
    return pd.DataFrame(rows)


def test_travelers_negative_others_positive() -> None:
    ue = vue.segment_unit_economics(_make_df())
    assert ue.loc["travelers", "margin_per_tx"] < 0
    for seg in ["young_professionals", "family_budgeters", "digital_newcomers", "premium_status"]:
        assert ue.loc[seg, "margin_per_tx"] > 0


def test_break_even_fx_cost() -> None:
    assert abs(vue.break_even_fx_cost() - 0.55) < 0.01


def test_break_even_spread() -> None:
    assert abs(vue.break_even_spread() - 0.85) < 0.01


def test_sensitivity_crosses_zero() -> None:
    sens = vue.sensitivity(_make_df())
    fx_cost = sens[sens["scenario"] == "fx_cost"]
    assert fx_cost["margin_per_tx"].min() < 0 < fx_cost["margin_per_tx"].max()
    fx_spread = sens[sens["scenario"] == "fx_spread"]
    assert fx_spread["margin_per_tx"].min() < 0 < fx_spread["margin_per_tx"].max()


def test_scale_projection_negative() -> None:
    proj = vue.scale_projection(_make_df())
    assert proj["monthly_pnl"] < 0
    assert proj["som"] == vue.TRAVELER_SOM


def test_traveler_fx_share_high() -> None:
    assert vue.traveler_fx_share(_make_df()) > 80.0


def test_plot_sensitivity_writes_png(tmp_path) -> None:
    sens = vue.sensitivity(_make_df())
    out = tmp_path / "sens.png"
    path = vue.plot_sensitivity(sens, out)
    assert path == out
    assert out.exists()
    assert out.stat().st_size > 1000
