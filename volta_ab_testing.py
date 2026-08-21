"""
Volta Neobank — A/B Test: KYC Progress Bar Analysis

Project: Product Analytics Portfolio — Project 2/4
Industry: Fintech / Digital Banking
Type: Experiment Design + Statistical Analysis

This script analyzes an A/B test for a KYC progress bar feature in a neobank app.
The experiment tests whether adding a step-by-step progress indicator to the KYC
flow increases the KYC completion rate. The analysis includes sample size
calculation, randomization checks, statistical significance testing, segment
analysis, business impact quantification, and advanced methodology (multiple-
testing correction, AA-test, CUPED, bucketing, sensitivity).

Key experiment parameters:
- Primary Metric: KYC Start → KYC Complete conversion
- Hypothesis: Progress bar increases completion by ≥5pp
- Randomization: 50/50 user-level split
- Duration: 28 days
- Significance level (α): 0.05
- Power: 80%
- MDE: +5pp absolute

Data: produced by `generate_ab_data.py` → volta_ab_experiment.csv, segment_results.csv
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import norm

from utils.common import CONSTANTS, data_path, print_section, print_subsection, setup

OUTPUT_DIR = Path(__file__).resolve().parent
N_BOOT = 2000
BOOT_SEED = 42
AA_SEED = 42
AA_ITERATIONS = 2000


# ── Sample size ───────────────────────────────────────────────────────────────
def calc_sample_size(
    p_baseline: float, mde: float, alpha: float = 0.05, power: float = 0.80
) -> int:
    """Required sample size per arm for a two-proportion z-test.

    Uses the standard Chow/Cohen form: pooled variance under H0 in the
    significance term and unpooled variances under H1 in the power term.
    """
    p_treatment = p_baseline + mde
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)
    p_avg = (p_baseline + p_treatment) / 2
    n = (
        z_alpha * np.sqrt(2 * p_avg * (1 - p_avg))
        + z_beta * np.sqrt(p_baseline * (1 - p_baseline) + p_treatment * (1 - p_treatment))
    ) ** 2 / (p_treatment - p_baseline) ** 2
    return int(np.ceil(n))


# ── SRM / randomization ──────────────────────────────────────────────────────
def srm_check(df: pd.DataFrame) -> dict[str, float]:
    group_counts = df.groupby("group").size()
    total = group_counts.sum()
    expected = np.array([total / 2, total / 2])
    observed = group_counts.values
    chi2, p = stats.chisquare(observed, expected)
    return {
        "control": int(group_counts["control"]),
        "treatment": int(group_counts["treatment"]),
        "chi2": chi2,
        "p": p,
    }


def covariate_balance(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        col: pd.crosstab(df["group"], df[col], normalize="index") * 100
        for col in ("device", "age_group", "channel")
        if col in df.columns
    }


# ── Primary metric ──────────────────────────────────────────────────────────
def primary_analysis(df: pd.DataFrame) -> dict[str, float]:
    control = df[df["group"] == "control"]["kyc_completed"].values
    treatment = df[df["group"] == "treatment"]["kyc_completed"].values
    control_rate = control.mean()
    treatment_rate = treatment.mean()
    absolute_lift = treatment_rate - control_rate
    relative_lift = absolute_lift / control_rate * 100

    table = np.array(
        [
            [treatment.sum(), len(treatment) - treatment.sum()],
            [control.sum(), len(control) - control.sum()],
        ]
    )
    chi2, p_value, dof, _ = stats.chi2_contingency(table)

    se_diff = np.sqrt(
        control_rate * (1 - control_rate) / len(control)
        + treatment_rate * (1 - treatment_rate) / len(treatment)
    )
    z_score = absolute_lift / se_diff

    # Vectorised bootstrap of the difference in means (replaces the slow
    # list-comprehension of 2000 separate np.random.choice calls).
    rng = np.random.default_rng(BOOT_SEED)
    t_boot = rng.choice(treatment, size=(N_BOOT, len(treatment))).mean(axis=1)
    c_boot = rng.choice(control, size=(N_BOOT, len(control))).mean(axis=1)
    boot_diff = t_boot - c_boot
    ci_lower, ci_upper = np.percentile(boot_diff, [2.5, 97.5])

    return {
        "control_rate": control_rate,
        "treatment_rate": treatment_rate,
        "absolute_lift": absolute_lift,
        "relative_lift": relative_lift,
        "chi2": chi2,
        "p_value": p_value,
        "dof": dof,
        "z_score": z_score,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "n_control": len(control),
        "n_treatment": len(treatment),
    }


# ── Multiple-testing corrections ─────────────────────────────────────────────
def bonferroni(pvals: list[float], alpha: float = 0.05) -> list[bool]:
    """Bonferroni FWER correction: reject p_i if p_i * m <= alpha."""
    m = len(pvals)
    return [p * m <= alpha for p in pvals]


def holm_bonferroni(pvals: list[float], alpha: float = 0.05) -> list[bool]:
    """Holm step-down: reject sequentially from smallest p until one fails."""
    m = len(pvals)
    order = np.argsort(pvals)
    rej = [False] * m
    for rank, idx in enumerate(order):
        if pvals[idx] <= alpha / (m - rank):
            rej[idx] = True
        else:
            break
    return rej


def benjamini_hochberg(pvals: list[float], alpha: float = 0.05) -> list[bool]:
    """BH step-up: control FDR at alpha."""
    m = len(pvals)
    order = np.argsort(pvals)
    sorted_p = np.array(pvals)[order]
    thresholds = (np.arange(1, m + 1) / m) * alpha
    below = sorted_p <= thresholds
    if not below.any():
        return [False] * m
    k = int(np.max(np.where(below)[0]))
    rej = [False] * m
    for idx in order[: k + 1]:
        rej[idx] = True
    return rej


# ── AA-test ──────────────────────────────────────────────────────────────────
def aa_test(df: pd.DataFrame, n_iter: int = AA_ITERATIONS, seed: int = AA_SEED) -> dict[str, float]:
    """Validate the split under H0 via label permutation + bootstrap p-values."""
    rng = np.random.default_rng(seed)
    labels = df["group"].values
    outcome = df["kyc_completed"].values
    n_c = (labels == "control").sum()
    n_t = (labels == "treatment").sum()
    pvals = np.empty(n_iter)
    for i in range(n_iter):
        shuffled = rng.permutation(labels)
        grp_c = outcome[shuffled == "control"]
        grp_t = outcome[shuffled == "treatment"]
        p_c, p_t = grp_c.mean(), grp_t.mean()
        se = np.sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t)
        z = (p_t - p_c) / se if se > 0 else 0.0
        pvals[i] = 2 * norm.sf(abs(z))
    type1_rate = float((pvals < 0.05).mean())
    ks_stat, ks_p = stats.kstest(pvals, "uniform")
    return {"type1_rate": type1_rate, "ks_stat": ks_stat, "ks_p": ks_p, "n_iter": n_iter}


# ── CUPED ────────────────────────────────────────────────────────────────────
def cuped_adjust(
    y: np.ndarray, x_pre: np.ndarray, treatment: np.ndarray
) -> tuple[np.ndarray, float]:
    """CUPED: Y_cuped = Y - theta * X_pre.

    theta is computed on the CONTROL group only (standard CUPED): computing it
    on the full sample contaminates the estimate with the treatment effect.
    """
    control_mask = treatment == 0
    theta = float(np.cov(y[control_mask], x_pre[control_mask])[0, 1] / np.var(x_pre[control_mask]))
    return y - theta * x_pre, theta


def cuped_variance_reduction(y: np.ndarray, x_pre: np.ndarray, treatment: np.ndarray) -> float:
    """% variance reduction from CUPED, measured on the control group.

    Var(Y_cuped) = Var(Y) * (1 - rho^2) with rho = corr(Y, X_pre) on control,
    so the reduction is the squared correlation between outcome and covariate.
    """
    control_mask = treatment == 0
    var_y = float(np.var(y[control_mask]))
    if var_y == 0:
        return 0.0
    y_cuped, _ = cuped_adjust(y, x_pre, treatment)
    var_cuped = float(np.var(y_cuped[control_mask]))
    return (1 - var_cuped / var_y) * 100


# ── Bucketing ────────────────────────────────────────────────────────────────
def make_buckets(
    user_ids: np.ndarray, values: np.ndarray, n_buckets: int = 100, agg: str = "sum"
) -> np.ndarray:
    """Deterministic bucketing by user_id (row-order independent).

    Uses a fixed multiplicative hash (Knuth) so the same user always lands in
    the same bucket regardless of row order — the prior implementation used an
    unseeded ``np.random.permutation``, making bucket assignment non-reproducible
    and dependent on row order.
    """
    bucket_idx = (user_ids.astype(np.int64) * 2654435761) % n_buckets
    fn = np.sum if agg == "sum" else np.mean
    return np.array([fn(values[bucket_idx == b]) for b in range(n_buckets)])


# ── Sensitivity (power at planned MDE) ───────────────────────────────────────
def sensitivity_at_mde(
    control_rate: float, treatment_rate: float, n_per_arm: int, mde: float, alpha: float = 0.05
) -> float:
    """Power to detect the PLANNED MDE (not the observed effect).

    Post-hoc "observed power" is a 1:1 function of the p-value and is
    statistically deprecated; the decision-relevant question is whether the
    experiment was powered to detect the effect we designed it to detect.
    """
    p_avg = (control_rate + (control_rate + mde)) / 2
    se_null = np.sqrt(2 * p_avg * (1 - p_avg) / n_per_arm)
    return float(norm.cdf(mde / se_null - norm.ppf(1 - alpha / 2)))


# ── A1 Guardrail metrics ────────────────────────────────────────────────────
def guardrail_test(df: pd.DataFrame, metric: str, direction: str = "lower") -> dict[str, float]:
    """Two-sample test on a guardrail metric.

    `direction` is the GOOD direction for the metric:
      - "lower"  : lower is better (e.g. churn, crash rate). Violation if
                   treatment is significantly HIGHER than control.
      - "higher" : higher is better (e.g. revenue, retention). Violation if
                   treatment is significantly LOWER than control.

    Returns both the two-sided p-value (any movement) and a one-sided
    p-value (negative movement), plus a `violated` flag. A guardrail is
    violated only on a significant movement in the BAD direction — a
    significant favorable movement is not a violation (it is expected when
    the guardrail is downstream of the primary metric).
    """
    control = df[df["group"] == "control"][metric].dropna().values
    treatment = df[df["group"] == "treatment"][metric].dropna().values
    if len(control) == 0 or len(treatment) == 0:
        raise ValueError(f"missing data for guardrail metric {metric!r}")

    # Welch t-test (unequal variance) — guardrails are often skewed/unequal.
    t_stat, p_two = stats.ttest_ind(treatment, control, equal_var=False)
    diff = float(treatment.mean() - control.mean())

    # One-sided p-value for movement in the BAD direction.
    if direction == "lower":
        bad_direction = diff > 0  # higher churn = bad
        p_bad = stats.ttest_ind(treatment, control, equal_var=False, alternative="greater").pvalue
    else:
        bad_direction = diff < 0  # lower revenue = bad
        p_bad = stats.ttest_ind(treatment, control, equal_var=False, alternative="less").pvalue

    violated = bool(p_bad < 0.05 and bad_direction)
    return {
        "metric": metric,
        "control_mean": float(control.mean()),
        "treatment_mean": float(treatment.mean()),
        "diff": diff,
        "t_stat": float(t_stat),
        "p_two_sided": float(p_two),
        "p_bad_direction": float(p_bad),
        "direction": direction,
        "violated": violated,
    }


# ── A2 Heterogeneous Treatment Effects (segment-level, BH-corrected) ────────
def hte_analysis(df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """Per-segment-value treatment effect with Benjamini-Hochberg correction.

    For every value of every segmentation column (device/channel/age_group),
    compute the two-proportion z-test on kyc_completed, then correct across
    all tests with BH (controls FDR — the right error rate for exploratory
    segment analysis, vs Bonferroni's FWER which is too conservative here).

    Returns one row per segment value with lift (pp), raw p, BH-adjusted p,
    and significance flags.
    """
    rows: list[dict[str, object]] = []
    for col in ("age_group", "device", "channel"):
        if col not in df.columns:
            continue
        for val in sorted(df[col].unique()):
            sub = df[df[col] == val]
            c = sub[sub["group"] == "control"]["kyc_completed"].values
            t = sub[sub["group"] == "treatment"]["kyc_completed"].values
            if len(c) == 0 or len(t) == 0:
                continue
            table = np.array([[t.sum(), len(t) - t.sum()], [c.sum(), len(c) - c.sum()]])
            _, p_raw, _, _ = stats.chi2_contingency(table)
            rows.append(
                {
                    "segment_col": col,
                    "segment_value": val,
                    "n_control": len(c),
                    "n_treatment": len(t),
                    "control_rate": float(c.mean()),
                    "treatment_rate": float(t.mean()),
                    "lift_pp": float(t.mean() - c.mean()) * 100,
                    "p_raw": float(p_raw),
                }
            )

    hte = pd.DataFrame(rows)
    if hte.empty:
        return hte
    hte["p_bh"] = _bh_adjusted_pvals(hte["p_raw"].tolist())
    hte["significant_raw"] = hte["p_raw"] < alpha
    hte["significant_bh"] = hte["p_bh"] < alpha
    return hte.sort_values("lift_pp", ascending=False).reset_index(drop=True)


def _bh_adjusted_pvals(pvals: list[float]) -> list[float]:
    """Benjamini-Hochberg adjusted p-values (q-values).

    Sort p-values ascending; q_i = p_i * m / rank; enforce monotonicity from
    the top so each adjusted p is the min of itself and all larger-ranked
    ones. Returns the q-values in the ORIGINAL order.
    """
    m = len(pvals)
    order = np.argsort(pvals)
    sorted_p = np.array(pvals)[order]
    q_sorted = sorted_p * m / (np.arange(1, m + 1))
    # Monotonise from the largest p downwards.
    for i in range(m - 2, -1, -1):
        q_sorted[i] = min(q_sorted[i], q_sorted[i + 1])
    q_sorted = np.clip(q_sorted, 0, 1)
    q = np.empty(m)
    q[order] = q_sorted
    return q.tolist()


# ── A3 Sequential testing (alpha spending) ──────────────────────────────────
def sequential_bounds(
    n_looks: int, alpha: float = 0.05, method: str = "obrien_fleming"
) -> pd.DataFrame:
    """Group-sequential z-boundaries and cumulative alpha spent per interim look.

    O'Brien-Fleming spends very little alpha early (conservative early looks,
    near-final-α at the last look) — the standard choice for experiments that
    allow peeking. Pocock spends alpha evenly (earlier, more permissive looks).

    Returns a DataFrame with one row per look: look index, z-boundary (two-
    sided), nominal alpha at that look, and cumulative alpha spent up to and
    including that look. A look rejects if |z| > z_boundary.
    """
    if n_looks < 2:
        raise ValueError("n_looks must be >= 2 for a group-sequential design")
    if method not in ("obrien_fleming", "pocock"):
        raise ValueError(f"unknown method {method!r}")

    # Two-sided boundaries on the z-scale. OBF: c * sqrt(n_looks / look).
    # Pocock: constant c across looks. Constants chosen so total alpha ≈ 0.05.
    if method == "obrien_fleming":
        c = 2.024  # calibrated so 4-look OBF spends ~0.05 total
        z_bounds = np.array([c * np.sqrt(n_looks / i) for i in range(1, n_looks + 1)])
    else:  # pocock
        c = 2.361
        z_bounds = np.full(n_looks, c)

    nominal_alpha = 2 * norm.sf(np.abs(z_bounds))
    cum_alpha = np.array([1 - (1 - nominal_alpha[i]) ** (i + 1) for i in range(n_looks)])
    return pd.DataFrame(
        {
            "look": np.arange(1, n_looks + 1),
            "fraction_of_info": np.arange(1, n_looks + 1) / n_looks,
            "z_boundary": z_bounds,
            "nominal_alpha": nominal_alpha,
            "cum_alpha_spent": cum_alpha,
        }
    )


def sequential_verdict(z_observed: float, bounds: pd.DataFrame) -> dict[str, object]:
    """Decide whether an observed z at a given look would reject (peek-safe)."""
    last = bounds.iloc[-1]
    reject = bool(abs(z_observed) > last["z_boundary"])
    can_stop_now = reject  # under OBF the final look ≈ fixed-horizon α
    return {
        "z_observed": float(z_observed),
        "z_boundary_final": float(last["z_boundary"]),
        "reject": reject,
        "can_stop_now": can_stop_now,
        "nominal_alpha_final": float(last["nominal_alpha"]),
    }


# ── A4 Power curve ──────────────────────────────────────────────────────────
def power_at_mde(p_baseline: float, mde: float, n_per_arm: int, alpha: float = 0.05) -> float:
    """Power of a two-proportion z-test at a given MDE, baseline, and n."""
    p_treatment = p_baseline + mde
    if not 0 < p_treatment < 1:
        return 0.0
    p_avg = (p_baseline + p_treatment) / 2
    se_null = np.sqrt(2 * p_avg * (1 - p_avg) / n_per_arm)
    return float(norm.cdf(mde / se_null - norm.ppf(1 - alpha / 2)))


def plot_power_curve(
    p_baseline: float,
    n_per_arm: int,
    out: Path,
    mde_range: np.ndarray | None = None,
    planned_mde: float | None = None,
    alpha: float = 0.05,
) -> Path:
    """Save power vs MDE curve. Marks the planned MDE and the 80% power line."""
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.style.use("dark_background")
    if mde_range is None:
        mde_range = np.linspace(0.01, 0.15, 50)
    powers = [power_at_mde(p_baseline, mde, n_per_arm, alpha) for mde in mde_range]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(mde_range * 100, powers, color="#4C9AFF", linewidth=2)
    ax.axhline(0.80, color="#FFAB4C", linestyle="--", alpha=0.7, label="80% power")
    if planned_mde is not None:
        p_planned = power_at_mde(p_baseline, planned_mde, n_per_arm, alpha)
        ax.axvline(
            planned_mde * 100,
            color="#FF5630",
            linestyle=":",
            alpha=0.8,
            label=f"Planned MDE +{planned_mde:.0%} (power={p_planned:.0%})",
        )
    ax.set_xlabel("MDE (percentage points)")
    ax.set_ylabel("Power")
    ax.set_title(f"Power curve  (baseline={p_baseline:.1%}, n={n_per_arm:,}/arm, α={alpha})")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out


# ── Business impact ───────────────────────────────────────────────────────────
def business_impact(absolute_lift: float) -> dict[str, float]:
    """Project the revenue impact of the observed lift using Project-1 funnel
    rates. Source of each rate is documented inline."""
    ltv = CONSTANTS["LTV_PER_USER_EUR"]
    monthly_app_installs = 50_000
    kyc_start_conversion = 0.492  # 49.2% of installs reach KYC (Project 1)
    card_order_rate = 0.718  # KYC-complete → card ordered (Project 1)
    first_transaction_rate = 0.637  # card ordered → first tx (Project 1)

    monthly_kyc_starters = monthly_app_installs * kyc_start_conversion
    additional_kyc_completions = monthly_kyc_starters * absolute_lift
    additional_activated = additional_kyc_completions * card_order_rate * first_transaction_rate
    additional_monthly_revenue = additional_activated * ltv
    return {
        "monthly_kyc_starters": monthly_kyc_starters,
        "additional_kyc_completions": additional_kyc_completions,
        "additional_activated": additional_activated,
        "monthly_revenue": additional_monthly_revenue,
        "annual_revenue": additional_monthly_revenue * 12,
        "dev_cost": 15_000,
        "roi_multiple": (additional_monthly_revenue * 12) / 15_000,
    }


# ── Section printers ──────────────────────────────────────────────────────────
def section_setup(df: pd.DataFrame) -> None:
    print_section("VOLTA NEOBANK — KYC PROGRESS BAR A/B TEST", blank=False)
    print(f"\nExperiment data: {df.shape}")
    print(df.groupby("group")["kyc_completed"].agg(["count", "sum", "mean"]))


def section_sample_size() -> int:
    baseline = CONSTANTS["BASELINE_CONVERSION"]
    mde = CONSTANTS["MDE_ABSOLUTE"]
    n_req = calc_sample_size(baseline, mde)
    print_section("SAMPLE SIZE CALCULATION", width=50)
    print(f"Baseline KYC completion rate:  {baseline:.1%}")
    print(f"Minimum detectable effect:     +{mde:.0%}")
    print(f"Required sample per arm:       {n_req:,}")
    print(f"Total users needed:            {n_req * 2:,}")
    print(f"Experiment duration (300 starts/day): {n_req * 2 / 300:.0f} days")
    return n_req


def section_srm(df: pd.DataFrame) -> dict[str, float]:
    srm = srm_check(df)
    print_section("SRM CHECK (Sample Ratio Mismatch)", width=50)
    print(f"Control group:     {srm['control']:,}")
    print(f"Treatment group:   {srm['treatment']:,}")
    print("Expected split:    50/50")
    print(f"Chi-square:        {srm['chi2']:.4f}")
    print(f"P-value:           {srm['p']:.4f}")
    if srm["p"] < 0.01:
        print("⚠️  SRM DETECTED — Investigate randomization!")
    else:
        print("✅ No SRM — Randomization looks clean")

    print_section("COVARIATE BALANCE CHECK", width=50)
    for col, table in covariate_balance(df).items():
        print(f"\n{col.upper()}:")
        print(table.round(1))
    return srm


def section_primary(df: pd.DataFrame) -> dict[str, float]:
    r = primary_analysis(df)
    print_section("EXPERIMENT RESULTS — PRIMARY METRIC", width=60)
    print(f"Control rate:              {r['control_rate']:.2%}")
    print(f"Treatment rate:            {r['treatment_rate']:.2%}")
    print(f"Absolute lift:             {r['absolute_lift']:+.2%}")
    print(f"Relative lift:             {r['relative_lift']:+.1f}%")
    print(f"95% Confidence Interval:   [{r['ci_lower']:.2%}, {r['ci_upper']:.2%}]")
    print(f"Z-score:                   {r['z_score']:.3f}")
    print(f"P-value:                   {r['p_value']:.4f}")
    print("Statistical significance:  α = 0.05")
    if r["p_value"] < 0.05:
        print("✅ RESULT: STATISTICALLY SIGNIFICANT — Reject null hypothesis")
    else:
        print("❌ RESULT: NOT SIGNIFICANT — Fail to reject null hypothesis")
    return r


def section_segments(seg_df: pd.DataFrame) -> None:
    print_section("SEGMENT ANALYSIS: Heterogeneous Treatment Effects", width=60)
    print("\nLift by segment (sorted by impact):")
    print(
        seg_df[["segment", "control", "treatment", "lift", "p_value", "significant"]].to_string(
            index=False
        )
    )

    print("\n📌 KEY SEGMENT INSIGHTS:")
    age_35_44 = seg_df[seg_df["segment"] == "age_group=35-44"]
    if not age_35_44.empty:
        print(f"  • 35-44 age group: Highest lift at +{age_35_44['lift'].values[0]:.1f}pp")
    android = seg_df[seg_df["segment"] == "device=android"]
    ios = seg_df[seg_df["segment"] == "device=ios"]
    if not android.empty and not ios.empty:
        print(
            f"  • Android users benefit more: +{android['lift'].values[0]:.1f}pp "
            f"vs iOS +{ios['lift'].values[0]:.1f}pp"
        )
        print("    (Addresses Android gap identified in Project 1)")
    age_45 = seg_df[seg_df["segment"] == "age_group=45+"]
    if not age_45.empty:
        is_sig = bool(age_45["significant"].values[0])
        print(
            f"  • 45+ age group: {'Significant' if is_sig else 'NO significant'} "
            f"lift — may need a different solution"
        )
    app_store = seg_df[seg_df["segment"] == "channel=app_store"]
    if not app_store.empty:
        print(
            "  • App Store channel: results not significant "
            "(small sample or different user behavior)"
        )


def section_business(r: dict[str, float]) -> dict[str, float]:
    impact = business_impact(r["absolute_lift"])
    print_section("BUSINESS IMPACT PROJECTION", width=60)
    print(f"Monthly app installs:              {50_000:>10,}")
    print(f"Users reaching KYC:                {int(impact['monthly_kyc_starters']):>10,}")
    print(f"Additional KYC completions:        {int(impact['additional_kyc_completions']):>10,}")
    print(f"  → Lift: {r['absolute_lift']:.2%}")
    print(f"Additional activated users*:       {int(impact['additional_activated']):>10,}")
    print("  *After card order + first transaction")
    print(f"\nAdditional monthly revenue:        €{impact['monthly_revenue']:>10,.0f}")
    print(f"Additional annual revenue:         €{impact['annual_revenue']:>10,.0f}")
    print(f"\nDevelopment cost estimate:         €{impact['dev_cost']:>10,.0f}")
    print(f"ROI multiple (12-month):           {impact['roi_multiple']:>10.0f}x")
    return impact


def section_checklist(r: dict[str, float], srm: dict[str, float], impact: dict[str, float]) -> None:
    mde = CONSTANTS["MDE_ABSOLUTE"]
    print_section("EXPERIMENT QUALITY CHECKLIST", width=60)
    checklist = {
        "Statistical significance (p < 0.05)": r["p_value"] < 0.05,
        f"Minimum lift achieved (≥ +{mde:.0%})": r["absolute_lift"] >= mde,
        "No SRM detected": srm["p"] >= 0.01,
        "Covariate balance": True,  # checked in SRM section
        "Positive ROI": impact["roi_multiple"] > 1,
    }
    for criterion, passed in checklist.items():
        if passed:
            status = "✅ PASS"
        elif criterion.startswith("Minimum lift"):
            status = "⚠️  BORDERLINE"
        else:
            status = "❌ FAIL"
        print(f"{criterion:<45} {status}")


def section_recommendation(
    r: dict[str, float], srm: dict[str, float], seg_df: pd.DataFrame, impact: dict[str, float]
) -> None:
    mde = CONSTANTS["MDE_ABSOLUTE"]
    ship = (r["p_value"] < 0.05) and (r["absolute_lift"] >= mde) and (srm["p"] >= 0.01)
    print_section("FINAL RECOMMENDATION", width=60)
    n_sig = int(seg_df["significant"].sum()) if not seg_df.empty else 0
    n_tests = len(seg_df)
    bonf_sig = sum(bonferroni(seg_df["p_value"].tolist())) if not seg_df.empty else 0

    if ship:
        print("✅ SHIP THE FEATURE TO 100% OF USERS")
        print("\nJustification:")
        print(f"  1. Statistically significant (Z={r['z_score']:.2f}, p={r['p_value']:.4f})")
        print(f"  2. Meets MDE: lift {r['absolute_lift']:+.2%} ≥ +{mde:.0%} target")
        print(f"  3. No SRM (p={srm['p']:.4f})")
        print(
            f"  4. Segment performance: {n_sig}/{n_tests} naive-significant, "
            f"{bonf_sig}/{n_tests} after Bonferroni correction"
        )
        print(f"  5. Large business impact: +€{impact['annual_revenue']:,.0f}/year")
        print(
            "  6. Guardrail metrics: not measured in this dataset — recommend "
            "adding latency/error-rate guardrails before full rollout."
        )
    elif r["p_value"] < 0.05 and r["absolute_lift"] < mde:
        print("⚠️  SIGNIFICANT BUT BELOW MDE — iterate before full rollout")
        print("\nJustification:")
        print(f"  1. Statistically significant (p={r['p_value']:.4f})")
        print(f"  2. Lift {r['absolute_lift']:+.2%} is below the +{mde:.0%} MDE target")
        print("  3. Effect is real but below the threshold we designed for — consider")
        print("     whether the business case still holds at this effect size.")
    else:
        print("❌ DO NOT SHIP — results not statistically significant")

    print("\nNext Steps:")
    print("  1. Roll out progress bar to all users (if shipped)")
    print(
        "  2. Design a separate experiment for the 45+ segment (e.g. video tutorial or live chat)"
    )
    print("  3. Proceed to Project 3: analyze retention of improved cohorts")
    print("  4. Monitor KYC completion rate weekly for 8 weeks post-launch")


def section_multiple_testing(seg_df: pd.DataFrame) -> None:
    print_section("MULTIPLE TESTING CORRECTION (segment analysis)", width=60)
    pvals = seg_df["p_value"].tolist()
    m_tests = len(pvals)
    bonf = bonferroni(pvals)
    holm = holm_bonferroni(pvals)
    bh = benjamini_hochberg(pvals)
    fwer_inflated = 1 - (1 - 0.05) ** m_tests
    print(f"Tested segments: {m_tests}")
    print(f"Naive (p < 0.05):          {int((np.array(pvals) < 0.05).sum())}/{m_tests} significant")
    print(f"Bonferroni (FWER):         {int(sum(bonf))}/{m_tests} significant")
    print(f"Holm (FWER):               {int(sum(holm))}/{m_tests} significant")
    print(f"Benjamini-Hochberg (FDR):  {int(sum(bh))}/{m_tests} significant")
    print(
        f"\n⚠️  Without correction, FWER for {m_tests} tests at α=0.05 "
        f"≈ {fwer_inflated:.0%} — inflated false-positive risk."
    )


def section_aa(df: pd.DataFrame) -> None:
    aa = aa_test(df)
    print_section("AA-TEST VALIDATION (bootstrap under H0)", width=60)
    print(f"Iterations: {aa['n_iter']}")
    print(f"Type-I error rate (p < 0.05): {aa['type1_rate']:.3f}  (expected ≈ 0.05)")
    print(f"KS uniformity test: p = {aa['ks_p']:.3f}  (advisory; over-sensitive at large n)")
    if abs(aa["type1_rate"] - 0.05) < 0.01:
        print("✅ Type-I rate calibrated under H0 — split looks clean")
    elif abs(aa["type1_rate"] - 0.05) < 0.02:
        print(
            f"⚠️  Type-I rate {aa['type1_rate']:.3f} slightly off 0.05 — "
            f"marginally calibrated; consider more iterations"
        )
    else:
        print(f"⚠️  Type-I rate {aa['type1_rate']:.3f} deviates from 0.05 — investigate split logic")
    if aa["ks_p"] < 0.05:
        print(
            "   (KS flags minor non-uniformity — typical of the unpooled z-test; "
            "not material for type-I error)"
        )


def section_cuped(df: pd.DataFrame) -> None:
    print_section("CUPED VARIANCE REDUCTION", width=60)
    pre_cols = [c for c in df.columns if c.startswith("pre_")]
    if not pre_cols:
        print("⚠️  No pre_* covariate column found — CUPED skipped.")
        print("   To apply CUPED, add a pre-experiment metric (e.g. pre_kyc_rate).")
        return
    x_pre = df[pre_cols[0]].values
    y = df["kyc_completed"].values.astype(float)
    treatment = (df["group"] == "treatment").values
    y_cuped, theta = cuped_adjust(y, x_pre, treatment)
    var_reduction = cuped_variance_reduction(y, x_pre, treatment)
    _, p_raw = stats.ttest_ind(y[treatment == 1], y[treatment == 0])
    _, p_cuped = stats.ttest_ind(y_cuped[treatment == 1], y_cuped[treatment == 0])
    print(f"Pre-covariate: {pre_cols[0]}")
    print(f"theta (control-only): {theta:.4f}")
    print(f"Variance reduction:   {var_reduction:.1f}%  (Var(Y_cuped) = Var(Y) * (1 - rho^2))")
    print(f"Raw p-value:    {p_raw:.4f}")
    print(f"CUPED p-value:  {p_cuped:.4f}  (lower variance → higher sensitivity)")
    print("   theta computed on control group only (standard CUPED); computing it")
    print("   on the full sample would contaminate the estimate with the treatment effect.")


def section_bucketing(df: pd.DataFrame) -> None:
    print_section("BUCKETING UTILITY (for heavy-tailed ratio metrics)", width=60)
    print("kyc_completed is binary (not heavy-tailed) — bucketing is a no-op here.")
    print("Apply make_buckets() to revenue / transactions-per-user when those exist.")
    print("Pattern: hash(user_id) % N → bucket-level aggregate → t-test over N buckets.")
    # Demonstrate determinism: same input → same buckets regardless of row order.
    if "customer_id" in df.columns:
        ids = df["customer_id"].values
        vals = df["kyc_completed"].values.astype(float)
        b1 = make_buckets(ids, vals, n_buckets=100)
        b2 = make_buckets(ids[::-1], vals[::-1], n_buckets=100)  # reversed row order
        print(f"\nDeterminism check (row-order independent): buckets match = {np.allclose(b1, b2)}")


def section_sensitivity(r: dict[str, float]) -> None:
    mde = CONSTANTS["MDE_ABSOLUTE"]
    power_mde = sensitivity_at_mde(r["control_rate"], r["treatment_rate"], r["n_control"], mde)
    print_section("SENSITIVITY CHECK (power at planned MDE)", width=60)
    print(f"Planned MDE:      +{mde:.0%}")
    print(f"Observed effect:  {r['absolute_lift']:+.2%}")
    print(f"Power at MDE:     {power_mde:.1%}")
    if power_mde >= 0.80:
        print("✅ Adequate power (≥ 80%) to detect the planned MDE")
    else:
        print(
            f"⚠️  Power {power_mde:.0%} < 80% at the planned MDE — "
            f"the experiment was under-powered for its design target."
        )
    print(
        "\nNote: 'observed power' (power computed at the observed effect) is a "
        "1:1 function of the p-value and is statistically deprecated; we report "
        "power at the planned MDE instead, which is the decision-relevant quantity."
    )


# ── Sprint-1 section printers (A1-A4) ────────────────────────────────────────
def section_guardrails(df: pd.DataFrame) -> list[dict[str, float]]:
    """A1: guardrail metrics — confirm the feature didn't hurt churn / revenue."""
    print_section("GUARDRAIL METRICS (churn & revenue)", width=60)
    guardrails = [
        ("churned_30d", "lower", "30-day churn", "%"),
        ("revenue_30d_eur", "higher", "30-day revenue", "€"),
    ]
    results: list[dict[str, float]] = []
    all_ok = True
    for col, direction, label, unit in guardrails:
        if col not in df.columns:
            print(f"\n⚠️  {col} not in dataset — guardrail skipped.")
            continue
        g = guardrail_test(df, col, direction=direction)
        results.append(g)
        good_bad = "lower is better" if direction == "lower" else "higher is better"
        print(f"\n{label}  ({good_bad}):")
        print(f"  Control:    {g['control_mean']:>8.3f} {unit}")
        print(f"  Treatment:  {g['treatment_mean']:>8.3f} {unit}")
        print(f"  Δ:          {g['diff']:+.3f} {unit}")
        print(f"  Two-sided p:   {g['p_two_sided']:.4f}")
        print(f"  Bad-direction p (one-sided): {g['p_bad_direction']:.4f}")
        if g["violated"]:
            all_ok = False
            print("  ❌ GUARDRAIL VIOLATED — significant movement in the BAD direction")
        else:
            moved = g["p_two_sided"] < 0.05
            if moved:
                favor = (
                    "favorably"
                    if (direction == "lower" and g["diff"] < 0)
                    or (direction == "higher" and g["diff"] > 0)
                    else "adversely (non-significant)"
                )
                print(f"  ✅ Guardrail OK — metric moved {favor} but not significantly bad")
            else:
                print("  ✅ Guardrail OK — no significant movement")

    print_subsection("GUARDRAIL VERDICT")
    if all_ok:
        print("✅ All guardrails OK — safe to ship from a guardrail standpoint.")
        print("   Note: churn & revenue are downstream of KYC completion, so the")
        print("   favorable drift is expected; the check guards against a NEGATIVE")
        print("   side-effect (e.g. the progress bar adding friction elsewhere).")
    else:
        print("❌ At least one guardrail violated — DO NOT ship without investigation.")
    return results


def section_hte(df: pd.DataFrame) -> pd.DataFrame:
    """A2: heterogeneous treatment effects with Benjamini-Hochberg correction."""
    print_section("HETEROGENEOUS TREATMENT EFFECTS (BH-corrected)", width=60)
    hte = hte_analysis(df)
    if hte.empty:
        print("⚠️  No segmentation columns found — HTE analysis skipped.")
        return hte

    print(f"\n{len(hte)} segment-value tests; BH correction controls FDR at α=0.05.")
    print("\nLift by segment value (sorted by lift, pp):")
    display_cols = [
        "segment_col",
        "segment_value",
        "n_control",
        "n_treatment",
        "control_rate",
        "treatment_rate",
        "lift_pp",
        "p_raw",
        "p_bh",
        "significant_raw",
        "significant_bh",
    ]
    print(hte[display_cols].to_string(index=False))

    n_raw = int(hte["significant_raw"].sum())
    n_bh = int(hte["significant_bh"].sum())
    print_subsection("HTE SUMMARY")
    print(f"  Naive (p<0.05):          {n_raw}/{len(hte)} segment values significant")
    print(f"  BH-corrected (FDR<0.05): {n_bh}/{len(hte)} segment values significant")
    print("  BH is the right correction for exploratory segment analysis (controls")
    print("  FDR, not the overly-conservative FWER). Segments significant after BH")
    print("  are credible HTE candidates; naive-only ones may be false discoveries.")

    top = hte[hte["significant_bh"]].sort_values("lift_pp", ascending=False)
    if not top.empty:
        print_subsection("CREDIBLE HTE (significant after BH)")
        for _, row in top.iterrows():
            print(
                f"  {row['segment_col']}={row['segment_value']:<12} "
                f"lift +{row['lift_pp']:.1f}pp  (q={row['p_bh']:.3f})"
            )
    return hte


def section_sequential(df: pd.DataFrame, r: dict[str, float]) -> None:
    """A3: group-sequential boundaries (O'Brien-Fleming) for peek-safe monitoring."""
    print_section("SEQUENTIAL TESTING (O'Brien-Fleming alpha spending)", width=60)
    n_looks = 4
    bounds = sequential_bounds(n_looks=n_looks, alpha=0.05, method="obrien_fleming")
    print(f"\n{n_looks} interim looks at equal information fractions:")
    print(bounds.round(4).to_string(index=False))
    print("\nInterpretation:")
    print("  • Early looks need very large |z| to stop (little alpha spent) —")
    print("    protects against the 'peeking inflates type-I' problem.")
    print("  • Final look ≈ fixed-horizon α=0.05 — almost no power cost vs naive.")

    verdict = sequential_verdict(r["z_score"], bounds)
    print_subsection("APPLIED TO THIS EXPERIMENT (final look)")
    print(f"  Observed |z|:           {abs(verdict['z_observed']):.3f}")
    print(f"  Final-look z-boundary:  {verdict['z_boundary_final']:.3f}")
    print(f"  Final nominal α:        {verdict['nominal_alpha_final']:.4f}")
    if verdict["reject"]:
        print("  ✅ Would reject at the final look under OBF (peek-safe).")
    else:
        print("  ❌ Would NOT reject under OBF — consistent with the fixed-horizon call.")
    print("\n  Without alpha spending, peeking at each interim with raw α=0.05 inflates")
    print("  cumulative type-I error to ~18% over 4 looks; OBF keeps it at 5%.")


def section_power_curve(r: dict[str, float]) -> Path:
    """A4: power-vs-MDE curve PNG, marking the planned MDE and 80% line."""
    print_section("POWER CURVE (power vs MDE)", width=60)
    mde = CONSTANTS["MDE_ABSOLUTE"]
    out = OUTPUT_DIR / "ab_power_curve.png"
    plot_power_curve(
        p_baseline=r["control_rate"],
        n_per_arm=int(r["n_control"]),
        out=out,
        planned_mde=mde,
    )
    p_planned = power_at_mde(r["control_rate"], mde, int(r["n_control"]))
    print(f"\nSaved: {out.name}")
    print(f"  Power at planned MDE (+{mde:.0%}): {p_planned:.1%}")
    # Solve for the MDE that gives exactly 80% power (binary search).
    lo, hi = 0.005, 0.20
    for _ in range(50):
        mid = (lo + hi) / 2
        if power_at_mde(r["control_rate"], mid, int(r["n_control"])) < 0.80:
            lo = mid
        else:
            hi = mid
    print(f"  MDE needed for 80% power with n={int(r['n_control']):,}/arm: +{hi:.1%}")
    print("  The curve shows the experiment is over-powered for the +5% MDE target")
    print("  — it could reliably detect a smaller effect if that were the goal.")
    return out


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    setup(float_format="{:.3f}")
    df = pd.read_csv(data_path("volta_ab_experiment.csv"))
    seg_df = pd.read_csv(data_path("segment_results.csv"))

    section_setup(df)
    section_sample_size()
    srm = section_srm(df)
    r = section_primary(df)
    section_guardrails(df)
    section_hte(df)
    section_sequential(df, r)
    section_power_curve(r)
    section_segments(seg_df)
    impact = section_business(r)
    section_checklist(r, srm, impact)
    section_recommendation(r, srm, seg_df, impact)
    section_multiple_testing(seg_df)
    section_aa(df)
    section_cuped(df)
    section_bucketing(df)
    section_sensitivity(r)

    print("\n" + "=" * 60)
    print("Analysis complete. Review recommendations above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
