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
