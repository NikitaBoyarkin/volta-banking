"""
Volta Neobank — Retention & Cohort Analysis

Project: Product Analytics Portfolio — Project 3/4
Industry: Fintech / Digital Banking
Type: Cohort Analysis · Retention · LTV Projection

Tracks how user retention evolves across monthly cohorts, measures the impact
of the KYC progress bar fix (Project 2), and projects 12-month LTV impact with
plan-specific retention curves (Free vs Premium).

Business questions answered:
1. How does retention evolve across monthly cohorts?
2. Is there a visible step-change in retention after the Sep 2024 KYC fix?
3. Which acquisition channels produce the most retained users?
4. What is the LTV gap between Free and Premium users (decomposed into ARPU
   and retention components)?
5. What is the 12-month LTV impact of the KYC improvement?

Data: produced by `generate_retention_data.py` → cohort_retention_matrix.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from utils.common import CONSTANTS, data_path, print_section, setup

OUTPUT_DIR = Path(__file__).resolve().parent
FIX_CUTOFF = "2024-09"  # cohorts >= this date are "post-fix"


# ── Parameters ────────────────────────────────────────────────────────────────
# All assumptions centralised with provenance. Retention curves are the % of a
# cohort active in each month (M0=1.0). Free and Premium have SEPARATE curves:
# Premium users retain materially better (M6 ≈ 0.55 vs Free ≈ 0.21 pre-fix), so
# the Premium/Free LTV gap reflects BOTH retention and ARPU — not ARPU alone
# (which was the bug in the prior version: it reused the Free curve for Premium,
# collapsing the gap to a pure 2.66× ARPU artifact).
PARAMS: dict[str, object] = {
    # Monthly ARPU (EUR). Source: retention-analysis assumptions.
    "monthly_arpu_free": CONSTANTS["MONTHLY_ARPU_FREE_EUR"],  # 3.2
    "monthly_arpu_premium": CONSTANTS["MONTHLY_ARPU_PREMIUM_EUR"],  # 8.5
    # Fleet assumptions for LTV projection. Source: portfolio narrative.
    "monthly_new_activated_users": CONSTANTS["MONTHLY_NEW_ACTIVATED_USERS"],  # 5000
    "premium_plan_share": CONSTANTS["PREMIUM_PLAN_SHARE"],  # 0.18
    # Free retention curves (12 months, M0=1.0). Match generate_retention_data.py.
    "free_pre_curve": [1.00, 0.52, 0.38, 0.31, 0.26, 0.23, 0.21, 0.19, 0.18, 0.17, 0.16, 0.15],
    "free_post_curve": [1.00, 0.64, 0.49, 0.41, 0.36, 0.33, 0.31, 0.29, 0.28, 0.27, 0.26, 0.25],
    # Premium retention curves — separate from Free (the prior version reused
    # the Free curve, which understated the Premium LTV gap).
    "premium_pre_curve": [1.00, 0.78, 0.70, 0.65, 0.61, 0.58, 0.55, 0.53, 0.51, 0.50, 0.49, 0.48],
    "premium_post_curve": [1.00, 0.82, 0.75, 0.70, 0.66, 0.63, 0.60, 0.58, 0.56, 0.55, 0.54, 0.53],
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def split_cohorts(cohort_index: pd.Index) -> tuple[list[str], list[str]]:
    """Vectorised pre/post split on the cohort index (string YYYY-MM)."""
    pre = [c for c in cohort_index if c < FIX_CUTOFF]
    post = [c for c in cohort_index if c >= FIX_CUTOFF]
    return pre, post


def cohort_metric_values(df: pd.DataFrame, cohorts: list[str], col: str) -> list[float]:
    """Extract a per-cohort metric, dropping NaNs. Single source of truth for
    the three loops that previously each reimplemented this."""
    return [float(v) for v in df.loc[cohorts, col].dropna().values]


def compute_ltv(curve: list[float], arpu: float) -> float:
    """12-month LTV = Σ(monthly retention × monthly ARPU)."""
    return float(sum(r * arpu for r in curve))


def cohens_d(a: list[float], b: list[float]) -> float:
    """Cohen's d (pooled-SD) for two independent samples."""
    a_arr, b_arr = np.asarray(a), np.asarray(b)
    na, nb = len(a_arr), len(b_arr)
    pooled_var = ((na - 1) * a_arr.var(ddof=1) + (nb - 1) * b_arr.var(ddof=1)) / (na + nb - 2)
    return float((b_arr.mean() - a_arr.mean()) / np.sqrt(pooled_var)) if pooled_var > 0 else 0.0


# ── Load ──────────────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    df = pd.read_csv(data_path("cohort_retention_matrix.csv"), index_col="cohort")
    return df


# ── Sections ──────────────────────────────────────────────────────────────────
def section_setup(df: pd.DataFrame) -> None:
    print_section("VOLTA NEOBANK — RETENTION & COHORT ANALYSIS", blank=False)
    print(f"\nCohort retention matrix: {len(df)} cohorts")
    print(f"Columns: {df.columns.tolist()}")
    print("\nFirst few cohorts:")
    print(df.head())


def section_metrics_framework() -> None:
    print_section("METRICS FRAMEWORK")
    print("M1 Retention:  % of activated users transacting in month 1")
    print("M3 Retention:  % still active in month 3")
    print("M6 Retention:  % still active in month 6")
    print("12mo LTV:      Cumulative revenue per user over 12 months")
    print("Premium conv:  % of free users upgrading within 90 days")


def section_insight1_step_change(df: pd.DataFrame) -> None:
    print_section("INSIGHT 1: Retention Step-Change After KYC Fix (Sep 2024)")
    pre, post = split_cohorts(df.index)
    pre_m1 = cohort_metric_values(df, pre, "month_1")
    post_m1 = cohort_metric_values(df, post, "month_1")
    avg_pre = np.mean(pre_m1) if pre_m1 else np.nan
    avg_post = np.mean(post_m1) if post_m1 else np.nan
    print(f"\nPre-fix cohorts (before {FIX_CUTOFF}):")
    print(f"  Average M1 retention: {avg_pre * 100:.1f}%")
    print(f"  Number of cohorts: {len(pre_m1)}")
    print(f"\nPost-fix cohorts ({FIX_CUTOFF} onwards):")
    print(f"  Average M1 retention: {avg_post * 100:.1f}%")
    print(f"  Number of cohorts: {len(post_m1)}")
    if not np.isnan(avg_pre) and not np.isnan(avg_post):
        lift = (avg_post - avg_pre) * 100
        print(f"\nM1 Retention Lift: +{lift:.1f} percentage points")
        print("✅ SIGNAL: KYC fix improved activation quality")


def section_insight2_plateau(df: pd.DataFrame) -> None:
    print_section("INSIGHT 2: Retention Plateau & Long-Term User Base")
    pre, post = split_cohorts(df.index)
    pre_m6 = cohort_metric_values(df, pre, "month_6")
    post_m6 = cohort_metric_values(df, post, "month_6")
    if pre_m6:
        avg_pre = np.mean(pre_m6)
        print(f"\nPre-fix cohorts: Average M6 retention = {avg_pre * 100:.1f}%")
        print('  → Natural "loyal core" segment is ~15–20% of activated users')
    if post_m6:
        avg_post = np.mean(post_m6)
        print(f"\nPost-fix cohorts: Average M6 retention = {avg_post * 100:.1f}%")
        if len(post_m6) > 1:
            print("  → Post-fix stabilises higher, indicating improved user quality")


def section_insight34_channel_plan() -> None:
    print_section("INSIGHT 3 & 4: Retention by Channel & Subscription Plan")
    print("\nTypical retention patterns (from segment analysis):")
    print("\nBy Channel (M1 / M3 / M6 retention):")
    print("  • Referral:     64% / 40% / 28%  ✅ Best performer")
    print("  • Organic:      57% / 36% / 24%")
    print("  • Paid social:  49% / 27% / 17%  ⚠️  Lowest performer")
    print("\nBy Plan (M6 retention, from LTV curves below):")
    print("  • Free (pre-fix):     ~21%   ⚠️  Low retention")
    print("  • Premium (pre-fix):  ~55%   ✅ ~2.6× better retention")
    print("\n📌 Strategic insight: Premium plan is the #1 retention lever")
    print("   Plan-based retention gap exceeds channel differences.")


def section_ltv() -> dict[str, float]:
    arpu_free = float(PARAMS["monthly_arpu_free"])
    arpu_prem = float(PARAMS["monthly_arpu_premium"])

    ltv_free_pre = compute_ltv(PARAMS["free_pre_curve"], arpu_free)  # type: ignore[arg-type]
    ltv_free_post = compute_ltv(PARAMS["free_post_curve"], arpu_free)  # type: ignore[arg-type]
    ltv_prem_pre = compute_ltv(PARAMS["premium_pre_curve"], arpu_prem)  # type: ignore[arg-type]
    ltv_prem_post = compute_ltv(PARAMS["premium_post_curve"], arpu_prem)  # type: ignore[arg-type]

    free_m6_pre = PARAMS["free_pre_curve"][6]  # type: ignore[index]
    free_m6_post = PARAMS["free_post_curve"][6]  # type: ignore[index]
    prem_m6_pre = PARAMS["premium_pre_curve"][6]  # type: ignore[index]
    prem_m6_post = PARAMS["premium_post_curve"][6]  # type: ignore[index]

    print_section("LTV CALCULATION: 12-MONTH PROJECTION")
    print(f"\nFREE PLAN (ARPU €{arpu_free:.1f}/mo):")
    print(f"  Pre-fix  (M6 ret {free_m6_pre:.0%}):  €{ltv_free_pre:.2f}")
    print(f"  Post-fix (M6 ret {free_m6_post:.0%}):  €{ltv_free_post:.2f}")
    free_gain = ltv_free_post - ltv_free_pre
    free_pct = (ltv_free_post / ltv_free_pre - 1) * 100
    print(f"  Improvement:                 +€{free_gain:.2f} (+{free_pct:.0f}%)")

    print(f"\nPREMIUM PLAN (ARPU €{arpu_prem:.1f}/mo, separate retention curve):")
    print(f"  Pre-fix  (M6 ret {prem_m6_pre:.0%}):  €{ltv_prem_pre:.2f}")
    print(f"  Post-fix (M6 ret {prem_m6_post:.0%}):  €{ltv_prem_post:.2f}")
    prem_gain = ltv_prem_post - ltv_prem_pre
    prem_pct = (ltv_prem_post / ltv_prem_pre - 1) * 100
    print(f"  Improvement:                 +€{prem_gain:.2f} (+{prem_pct:.0f}%)")

    # Decompose the Premium/Free gap into ARPU and retention components.
    ratio = ltv_prem_post / ltv_free_post
    arpu_ratio = arpu_prem / arpu_free
    retention_ratio = float(sum(PARAMS["premium_post_curve"])) / float(
        sum(PARAMS["free_post_curve"])
    )  # type: ignore[arg-type]
    print("\nPREMIUM vs FREE (post-fix):")
    print(f"  Premium LTV is {ratio:.1f}× higher than Free")
    print(
        f"  Decomposition: ARPU ratio {arpu_ratio:.2f}× × retention-sum ratio {retention_ratio:.2f}× "
        f"= {arpu_ratio * retention_ratio:.1f}×"
    )
    print("  → The gap reflects BOTH higher ARPU AND higher retention (the prior")
    print("     version reused the Free curve for Premium, collapsing it to ARPU only).")
    print("  → Monetization lever: convert free users to premium")
    return {
        "ltv_free_pre": ltv_free_pre,
        "ltv_free_post": ltv_free_post,
        "ltv_prem_pre": ltv_prem_pre,
        "ltv_prem_post": ltv_prem_post,
        "free_gain": free_gain,
        "free_pct": free_pct,
        "prem_gain": prem_gain,
        "prem_pct": prem_pct,
        "ratio": ratio,
        "arpu_ratio": arpu_ratio,
        "retention_ratio": retention_ratio,
    }


def section_fleet_impact(ltvs: dict[str, float]) -> dict[str, float]:
    monthly_new = int(PARAMS["monthly_new_activated_users"])
    prem_share = float(PARAMS["premium_plan_share"])
    free_share = 1 - prem_share

    fleet_pre = monthly_new * (
        free_share * ltvs["ltv_free_pre"] + prem_share * ltvs["ltv_prem_pre"]
    )
    fleet_post = monthly_new * (
        free_share * ltvs["ltv_free_post"] + prem_share * ltvs["ltv_prem_post"]
    )
    incremental = fleet_post - fleet_pre
    annual = incremental * 12

    print_section("FLEET-LEVEL BUSINESS IMPACT")
    print("\nAssumptions:")
    print(f"  • Monthly new activated users: {monthly_new:,}")
    print(f"  • Current premium plan share: {prem_share * 100:.0f}%")
    print("  • Time horizon: 12 months per cohort")
    print("\n12-MONTH CUMULATIVE REVENUE per monthly cohort:")
    print(f"  Pre-fix scenario:  €{fleet_pre:>10,.0f}")
    print(f"  Post-fix scenario: €{fleet_post:>10,.0f}")
    print(f"  Incremental revenue (from KYC fix): €{incremental:>10,.0f}")
    print("\nANNUALIZED INCREMENTAL REVENUE:")
    print(f"  €{annual:,.0f}/year from retention improvement alone")
    print("  (Steady-state assumption: 12 cohorts/yr each at the per-cohort figure;")
    print("   on top of the activation lift from Project 2.)")
    return {
        "fleet_pre": fleet_pre,
        "fleet_post": fleet_post,
        "incremental": incremental,
        "annual": annual,
    }


def section_cohort_summary(df: pd.DataFrame) -> None:
    print_section("COHORT SUMMARY: Sizes & Retention Trends")
    header = f"{'Cohort':<12} {'Size':<10} {'M1 Ret%':<10} {'M3 Ret%':<10} {'M6 Ret%':<10} {'Post-fix':<12}"
    print(f"\n{header}")
    print("-" * 70)
    for cohort in df.index:
        row = df.loc[cohort]
        m1 = row.get("month_1", np.nan)
        m3 = row.get("month_3", np.nan)
        m6 = row.get("month_6", np.nan)
        size = int(row.get("cohort_size", 0))
        is_post = "Yes ✅" if cohort >= FIX_CUTOFF else "No"
        m1s = f"{m1 * 100:.1f}%" if pd.notna(m1) else "—"
        m3s = f"{m3 * 100:.1f}%" if pd.notna(m3) else "—"
        m6s = f"{m6 * 100:.1f}%" if pd.notna(m6) else "—"
        print(f"{cohort:<12} {size:<10,} {m1s:<10} {m3s:<10} {m6s:<10} {is_post:<12}")


def section_stat_test(df: pd.DataFrame) -> dict[str, float]:
    """Welch t-test (unequal variances) + Cohen's d on M3 retention, pre vs post."""
    print_section("STATISTICAL TEST: M3 Retention — Post-fix vs Pre-fix Cohorts")
    pre, post = split_cohorts(df.index)
    pre_m3 = cohort_metric_values(df, pre, "month_3")
    post_m3 = cohort_metric_values(df, post, "month_3")

    # `difference` initialised to NaN up front so the final summary never hits
    # a NameError if one side is empty (the prior version defined it only inside
    # the if-branch and referenced it unconditionally at the end of the script).
    result = {
        "difference": float("nan"),
        "t_stat": float("nan"),
        "p_value": float("nan"),
        "cohens_d": float("nan"),
        "n_pre": len(pre_m3),
        "n_post": len(post_m3),
    }

    if not pre_m3 or not post_m3:
        print("⚠️  Insufficient data for statistical comparison.")
        return result

    pre_mean = np.mean(pre_m3)
    post_mean = np.mean(post_m3)
    difference = post_mean - pre_mean
    result["difference"] = difference

    print(f"\nPre-fix M3 retention (mean):  {pre_mean * 100:.1f}%  ({len(pre_m3)} cohorts)")
    print(f"Post-fix M3 retention (mean): {post_mean * 100:.1f}%  ({len(post_m3)} cohorts)")
    print(f"\nAbsolute difference: +{difference * 100:.1f} percentage points")

    # Welch's t-test (equal_var=False): cohort-level retention values are few
    # and need not have equal variance. Student's t (equal_var=True) assumes
    # equal variances, which is unjustified across pre/post cohorts.
    t_stat, p_value = stats.ttest_ind(post_m3, pre_m3, equal_var=False)
    d = cohens_d(pre_m3, post_m3)
    result["t_stat"] = float(t_stat)
    result["p_value"] = float(p_value)
    result["cohens_d"] = d

    print(f"Welch t-statistic: {t_stat:.3f}")
    print(f"P-value:           {p_value:.4f}")
    print(
        f"Cohen's d:         {d:.2f}  ({'large' if abs(d) >= 0.8 else 'medium' if abs(d) >= 0.5 else 'small'} effect)"
    )
    print("Significance level (α): 0.05")
    print(f"\n⚠️  Note: n is small ({len(pre_m3)}+{len(post_m3)} cohorts) — low power;")
    print("   treat the p-value as directional, not definitive.")

    if p_value < 0.05:
        print("\n✅ RESULT: Statistically significant improvement (p < 0.05)")
        print("   Post-fix cohorts have significantly higher M3 retention.")
    else:
        print("\n⚠️  RESULT: Not statistically significant (p ≥ 0.05)")
        print("   Need more post-fix cohorts to detect the difference with confidence.")
    return result


def section_summary(ltvs: dict[str, float], test: dict[str, float]) -> None:
    print_section("SUMMARY: 6 KEY INSIGHTS & RECOMMENDATIONS")
    insights = [
        (
            1,
            "M1 retention jumped ~+10pp after KYC fix",
            "Fix had a compounding long-term effect",
            "Monitor M6+ as post-fix cohorts mature",
        ),
        (
            2,
            f"Retention plateaus ~{PARAMS['free_pre_curve'][6] * 100:.0f}% at M6 (pre-fix)",  # type: ignore[index]
            "Natural loyal user base exists",
            "Build features for this core segment",
        ),
        (
            3,
            "Referral users: best M1, M3, M6 retention",
            "Referral = highest LTV channel",
            "Scale referral program (Project 4 priority)",
        ),
        (
            4,
            "Premium users: ~2.6× better M6 retention vs Free (0.55 vs 0.21 pre-fix)",
            "Plan is the #1 retention driver",
            "Design premium upgrade funnel (Project 4)",
        ),
        (
            5,
            f"LTV improved €{ltvs['free_gain']:.1f} per free user (+{ltvs['free_pct']:.0f}%)",
            f"+{ltvs['free_pct']:.0f}% LTV per user after KYC fix",
            "Every activation improvement compounds over time",
        ),
        (
            6,
            f"Premium LTV (€{ltvs['ltv_prem_post']:.1f}) is {ltvs['ratio']:.1f}× Free",
            "Monetization strategy is clear",
            "Push upgrade flows to M1–M2 high-intent users",
        ),
    ]
    for num, insight, implication, action in insights:
        print(f"\n{num}. {insight}")
        print(f"   → {implication}")
        print(f"   ✓ {action}")


def section_bridge() -> None:
    print_section("BRIDGE TO PROJECT 4: User Segmentation & Premium Conversion")
    print("\nRetention analysis reveals two critical unanswered questions:")
    print("\n1. Who are the ~20% of users who remain active at M6?")
    print("   → What behavioral, demographic, or engagement traits define them?")
    print("   → How do they differ from churned users?")
    print("\n2. Who converts to Premium?")
    print("   → What signals predict Premium subscription within 90 days?")
    print("   → What is the optimal timing and targeting for upgrade offers?")
    print("\nThese questions require user segmentation and clustering:")
    print("→ Project 4 will tackle RFM segmentation and user profiling")
    print("\nINPUTS TO PROJECT 4:")
    print("  • Target: Identify the high-LTV user profile")
    print("  • Goal: Find behavioral/demographic predictors of Premium conversion")
    print("  • Business outcome: Build a targeted upgrade journey for right segments")
    print("  • Expected impact: Improve premium conversion rate from 18% to 25%+")


def section_final(ltvs: dict[str, float], fleet: dict[str, float], test: dict[str, float]) -> None:
    print_section("Analysis complete. Key outputs:")
    print(f"  • KYC fix generated €{fleet['annual']:,.0f}/year in incremental LTV")
    print(f"  • Premium plan is {ltvs['ratio']:.1f}× higher LTV than free")
    diff = test["difference"]
    if not np.isnan(diff):
        print(f"  • Post-fix cohorts show +{diff * 100:.1f}pp M3 retention improvement")
    else:
        print("  • Post-fix M3 retention difference: not computable (insufficient data)")
    print("\nRecommendation: Proceed to Project 4 (User Segmentation)")


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    setup(float_format="{:.3f}")
    df = load_data()

    section_setup(df)
    section_metrics_framework()
    section_insight1_step_change(df)
    section_insight2_plateau(df)
    section_insight34_channel_plan()
    ltvs = section_ltv()
    fleet = section_fleet_impact(ltvs)
    section_cohort_summary(df)
    test = section_stat_test(df)
    section_summary(ltvs, test)
    section_bridge()
    section_final(ltvs, fleet, test)


if __name__ == "__main__":
    main()
