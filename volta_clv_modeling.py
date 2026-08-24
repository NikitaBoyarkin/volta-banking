"""Volta Neobank — Customer Lifetime Value Modeling.

Estimates CLV three ways and compares them per segment:
  A. Historical  — total observed revenue per customer.
  B. Predictive  — retention-curve projection: LTV = ARPU x sum of survival
     probability over a horizon (power-law retention fit), mirroring Project 3.
  C. Probabilistic — Gamma-Gamma model of average transaction value (MLE, inline
     per the "no external CLV libraries" constraint) times expected future
     purchases from the retention curve.

Run:  uv run python volta_clv_modeling.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import optimize, special

from utils.common import OUTPUT_DIR, data_path, print_section, print_subsection, setup

HORIZON_MONTHS = 24


def load_customers() -> pd.DataFrame:
    return pd.read_csv(data_path("volta_clv_customers.csv"))


def load_cohorts() -> pd.DataFrame:
    return pd.read_csv(data_path("volta_clv_cohorts.csv"))


def fit_power_retention(curve: pd.Series) -> tuple[float, float]:
    """Fit R(t) = a * t^-b in log space via OLS on the cohort retention curve."""
    t = np.arange(1, len(curve) + 1, dtype=float)
    r = curve.to_numpy(dtype=float)
    valid = (r > 0) & (t > 0)
    log_r = np.log(np.clip(r[valid], 1e-6, None))
    log_t = np.log(t[valid])
    slope, intercept = np.polyfit(log_t, log_r, 1)
    return float(np.exp(intercept)), float(-slope)


def monthly_revenue_by_segment(customers: pd.DataFrame) -> pd.Series:
    """Mean monthly spend per segment = total_spend / lifetime_months."""
    m = customers["total_spend"] / customers["lifetime_months"].clip(lower=1)
    return m.groupby(customers["segment"]).mean()


def historical_clv(customers: pd.DataFrame) -> pd.DataFrame:
    return customers.groupby("segment")["total_spend"].mean().rename("historical").to_frame()


def predictive_clv(
    customers: pd.DataFrame, cohorts: pd.DataFrame, monthly_rev: pd.Series
) -> pd.DataFrame:
    """LTV = segment monthly revenue x sum of survival over the horizon."""
    rows: dict[str, float] = {}
    for _, row in cohorts.iterrows():
        seg = row["segment"]
        curve = row[[c for c in cohorts.columns if c.startswith("month_")]]
        a, b = fit_power_retention(curve)
        t = np.arange(1, HORIZON_MONTHS + 1, dtype=float)
        survival = a * np.power(t, -b)
        rows[seg] = float(monthly_rev.get(seg, 0.0) * survival.sum())
    return pd.DataFrame({"predictive": rows})


def _gamma_gamma_mle(x: np.ndarray, s: np.ndarray) -> tuple[float, float, float]:
    """MLE for Gamma-Gamma (p, q, gamma) on frequency x and total spend s (x>0)."""

    def neg_ll(params: np.ndarray) -> float:
        p, q, gamma = np.exp(params)
        if p <= 0 or q <= 0 or gamma <= 0:
            return 1e12
        with np.errstate(divide="ignore", invalid="ignore"):
            term = (
                special.gammaln(p * x + q)
                - special.gammaln(p * x)
                - special.gammaln(q)
                + q * np.log(gamma)
                + p * x * np.log(x)
                - (p * x + q) * np.log(gamma + s)
            )
        return -float(term.sum())

    init = np.log(np.array([1.0, 1.0, 1.0]))
    res = optimize.minimize(neg_ll, init, method="Nelder-Mead", options={"maxiter": 5000})
    p, q, gamma = np.exp(res.x)
    return float(p), float(q), float(gamma)


def probabilistic_clv(
    customers: pd.DataFrame, cohorts: pd.DataFrame, monthly_rev: pd.Series
) -> pd.DataFrame:
    """Gamma-Gamma E[future tx value] x expected future purchases from retention."""
    out: dict[str, float] = {}
    for seg in customers["segment"].unique():
        sub = customers[customers["segment"] == seg]
        pos = sub[sub["frequency"] > 0]
        if pos.empty:
            out[seg] = 0.0
            continue
        x = pos["frequency"].to_numpy(dtype=float)
        s = pos["total_spend"].to_numpy(dtype=float)
        p, q, gamma = _gamma_gamma_mle(x, s)
        # E[future tx value] = p*(gamma+s)/(q+p*x-1)  (Gamma-Gamma posterior mean)
        emv = p * (gamma + s) / (q + p * x - 1.0)
        # Expected future purchases over horizon, from the segment retention curve.
        curve = cohorts.loc[cohorts["segment"] == seg].iloc[0]
        r = curve[[c for c in cohorts.columns if c.startswith("month_")]].to_numpy(float)
        freq_per_month = (pos["frequency"] / pos["lifetime_months"].clip(lower=1)).mean()
        expected = float((emv * freq_per_month * r.sum()).mean())
        out[seg] = round(expected, 2)
    return pd.DataFrame({"probabilistic": out})


def compare(historical: pd.DataFrame, predictive: pd.DataFrame, prob: pd.DataFrame) -> pd.DataFrame:
    return historical.join(predictive).join(prob)


def plot_clv_by_method(comp: pd.DataFrame, out: Path) -> Path:
    df = comp.reset_index().melt(id_vars="segment", var_name="method", value_name="CLV (EUR)")
    plt.figure(figsize=(9, 5))
    for method in df["method"].unique():
        sub = df[df["method"] == method]
        plt.plot(sub["segment"], sub["CLV (EUR)"], marker="o", label=method)
    plt.xlabel("Segment")
    plt.ylabel("CLV (EUR)")
    plt.title(f"CLV by Method and Segment (horizon {HORIZON_MONTHS} mo)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()
    return out


def section_setup(customers: pd.DataFrame) -> None:
    print_section("VOLTA NEOBANK — CLV MODELING")
    print_subsection("Data")
    print(f"  Customers: {len(customers):,}")
    print(f"  Segments:  {customers['segment'].nunique()}")
    print(f"  Horizon:   {HORIZON_MONTHS} months")


def section_compare(comp: pd.DataFrame) -> None:
    print_subsection("CLV by Method (EUR)")
    print(comp.round(2).to_string())
    print("\n  Method notes:")
    print("    historical   — observed revenue to date (no future value).")
    print("    predictive   — ARPU x projected survival over the horizon.")
    print("    probabilistic— Gamma-Gamma E[tx value] x expected future purchases.")


def main() -> None:
    setup()
    customers = load_customers()
    cohorts = load_cohorts()
    section_setup(customers)

    hist = historical_clv(customers)
    monthly_rev = monthly_revenue_by_segment(customers)
    pred = predictive_clv(customers, cohorts, monthly_rev)
    prob = probabilistic_clv(customers, cohorts, monthly_rev)
    comp = compare(hist, pred, prob)
    section_compare(comp)
    out = plot_clv_by_method(comp, OUTPUT_DIR / "clv_by_method.png")
    print(f"  Saved: {out.name}")

    print("\n" + "=" * 60)
    print("Analysis complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
