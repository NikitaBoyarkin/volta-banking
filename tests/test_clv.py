"""Tests for volta_clv_modeling.py."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from volta_clv_modeling import (
    _gamma_gamma_mle,
    compare,
    fit_power_retention,
    historical_clv,
    load_cohorts,
    load_customers,
    monthly_revenue_by_segment,
    plot_clv_by_method,
    predictive_clv,
    probabilistic_clv,
)


def test_load_data() -> None:
    customers = load_customers()
    cohorts = load_cohorts()
    assert {"segment", "frequency", "total_spend", "lifetime_months"} <= set(customers.columns)
    assert {"segment", "month_1"} <= set(cohorts.columns)


def test_fit_power_retention() -> None:
    t = np.arange(1, 25, dtype=float)
    r = 3.0 * t ** (-0.5)  # a true power law R(t) = a*t^-b
    a, b = fit_power_retention(pd.Series(r))
    assert a == pytest.approx(3.0, abs=0.05)
    assert b == pytest.approx(0.5, abs=0.05)


def test_historical_clv_indexed_by_segment() -> None:
    hist = historical_clv(load_customers())
    assert set(hist.index) == {"Power", "Growth", "Casual", "Dormant"}
    assert hist["historical"].gt(0).all()


def test_predictive_clv_ordering() -> None:
    customers = load_customers()
    cohorts = load_cohorts()
    pred = predictive_clv(customers, cohorts, monthly_revenue_by_segment(customers))
    order = pred["predictive"].sort_values(ascending=False).index.tolist()
    assert order[0] == "Power"
    assert order[-1] == "Dormant"


def test_gamma_gamma_mle_positive() -> None:
    rng = np.random.default_rng(0)
    x = rng.poisson(5, size=500).astype(float)
    s = rng.lognormal(3, 0.5, size=500) * x
    p, q, gamma = _gamma_gamma_mle(x, s)
    assert p > 0 and q > 0 and gamma > 0


def test_gamma_gamma_mle_recovers_known_params() -> None:
    """Recovery check: data drawn from a true Gamma-Gamma hierarchy
    (nu ~ Gamma(q, gamma); m_bar | nu ~ Gamma(px, nu)) must yield MLE
    close to the generating (p, q, gamma)."""
    rng = np.random.default_rng(7)
    n = 4000
    p_true, q_true, gamma_true = 2.0, 4.0, 1.0
    x = np.clip(rng.poisson(4, size=n).astype(float), 1.0, None)
    rate = rng.gamma(shape=q_true, scale=1.0 / gamma_true, size=n)
    m_bar = rng.gamma(shape=p_true * x, scale=1.0 / rate)
    s = m_bar * x  # total spend; m_bar = s / x is the GG quantity
    p, q, gamma = _gamma_gamma_mle(x, s)
    assert p == pytest.approx(p_true, rel=0.35)
    assert q == pytest.approx(q_true, rel=0.35)
    assert gamma == pytest.approx(gamma_true, rel=0.35)


def test_expected_value_formula_matches_mixing_form() -> None:
    """Compact E[M] = (gamma*q + p*s)/(px + q - 1) must equal the mixing
    form w*m_bar + (1 - w)*gamma*q/(q - 1), w = px/(px + q - 1)
    (cf. lifetimes.GammaGammaFitter.conditional_expected_average_profit)."""
    p, q, gamma = 2.0, 4.0, 1.0
    x = np.array([1.0, 3.0, 5.0])
    s = np.array([60.0, 150.0, 250.0])
    w = p * x / (p * x + q - 1.0)
    mixing = (1 - w) * gamma * q / (q - 1.0) + w * (s / x)
    compact = (gamma * q + p * s) / (p * x + q - 1.0)
    assert np.allclose(mixing, compact)


def test_probabilistic_clv_ordering() -> None:
    customers = load_customers()
    cohorts = load_cohorts()
    prob = probabilistic_clv(customers, cohorts, monthly_revenue_by_segment(customers))
    order = prob["probabilistic"].sort_values(ascending=False).index.tolist()
    assert order[0] == "Power"


def test_compare_joins_all_three() -> None:
    customers = load_customers()
    cohorts = load_cohorts()
    monthly_rev = monthly_revenue_by_segment(customers)
    comp = compare(
        historical_clv(customers),
        predictive_clv(customers, cohorts, monthly_rev),
        probabilistic_clv(customers, cohorts, monthly_rev),
    )
    assert list(comp.columns) == ["historical", "predictive", "probabilistic"]


def test_plot_writes_png(tmp_path) -> None:
    customers = load_customers()
    cohorts = load_cohorts()
    monthly_rev = monthly_revenue_by_segment(customers)
    comp = compare(
        historical_clv(customers),
        predictive_clv(customers, cohorts, monthly_rev),
        probabilistic_clv(customers, cohorts, monthly_rev),
    )
    out = plot_clv_by_method(comp, tmp_path / "clv.png")
    assert out.exists() and out.stat().st_size > 0
