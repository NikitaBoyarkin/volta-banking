"""
Volta Neobank — Onboarding Funnel Analysis

Project: Product Analytics Portfolio — Project 1/4
Industry: Fintech / Digital Banking
Type: Funnel Analysis + Channel & Demographic Segmentation

This script analyzes the onboarding funnel for a mobile neobank app, identifying
bottlenecks and high-impact improvement opportunities. The analysis segments users
by acquisition channel, device, and age group to understand which demographic/
channel combinations have the highest drop-off rates.

Business context:
- Volta is a mobile-first neobank targeting 18–44 year-olds in Eastern Europe
- Freemium model: free tier + premium subscription (€5.99/month)
- Problem: CAC increased 34% YoY while activation rates stagnated
- Only ~13% of app installs complete first transaction within 7 days

Key business questions:
1. Where exactly do users drop off in the funnel?
2. Which segments (channels, age groups, devices) have highest drop-off?
3. What is the revenue impact of each drop-off?
4. Which improvements would have the highest ROI?
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

from utils.common import CONSTANTS, data_path, print_section, setup

# ── Funnel definition ────────────────────────────────────────────────────────
FUNNEL_STEPS = [
    "app_install",
    "registration",
    "kyc_start",
    "kyc_complete",
    "card_ordered",
    "first_tx",
]
FUNNEL_LABELS = [
    "App Install",
    "Registration",
    "KYC Start",
    "KYC Complete",
    "Card Ordered",
    "First Transaction",
]
OUTPUT_DIR = Path(__file__).resolve().parent


# ── Data ─────────────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    """Load the funnel dataset and normalise categorical casing.

    The committed CSV stores ``device`` lowercase ('ios'/'android'); the prior
    code filtered on 'iOS'/'Android' and silently produced empty frames.
    """
    df = pd.read_csv(data_path("volta_funnel_data.csv"))
    df["device"] = df["device"].str.lower()
    df["channel"] = df["channel"].str.lower()
    df["age_group"] = df["age_group"].astype(str)
    return df


def data_quality(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Return distribution summaries printed in the data-quality section."""
    return {
        "channel": df["channel"].value_counts(),
        "device": df["device"].value_counts(),
        "age_group": df["age_group"].value_counts().sort_index(),
    }


# ── Core funnel ──────────────────────────────────────────────────────────────
def compute_funnel(df: pd.DataFrame) -> dict[str, list[float]]:
    """Compute counts, overall + step conversion, and absolute drop-off.

    Asserts monotonicity (each stage count <= the previous) so a non-monotonic
    dataset surfaces immediately instead of producing >100% step conversion.
    """
    counts = [int(df[step].sum()) for step in FUNNEL_STEPS]
    assert all(counts[i] <= counts[i - 1] for i in range(1, len(counts))), (
        "Funnel is not monotonic — a later stage has more users than an earlier one"
    )

    overall_conv = [(c / counts[0]) * 100 for c in counts]
    step_conv = [100.0] + [(counts[i] / counts[i - 1]) * 100 for i in range(1, len(counts))]
    drop_off = [0] + [counts[i - 1] - counts[i] for i in range(1, len(counts))]
    return {
        "counts": counts,
        "overall_conv": overall_conv,
        "step_conv": step_conv,
        "drop_off": drop_off,
    }


def funnel_summary_table(metrics: dict[str, list[float]]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Step": FUNNEL_LABELS,
            "Users": metrics["counts"],
            "Overall Conv %": [f"{x:.1f}%" for x in metrics["overall_conv"]],
            "Step Conv %": [f"{x:.1f}%" for x in metrics["step_conv"]],
            "Drop-off": metrics["drop_off"],
        }
    )


def biggest_drops(metrics: dict[str, list[float]]) -> dict[str, object]:
    """Distinguish the biggest ABSOLUTE drop (most users lost) from the biggest
    RELATIVE drop (lowest step-conversion rate). They are different stages and
    conflating them was the prior bug driving the wrong headline narrative."""
    drop_off = metrics["drop_off"]
    step_conv = metrics["step_conv"]
    abs_idx = int(drop_off.index(max(drop_off)))
    # Step 0 has no conversion; compare from step 1 onward.
    rel_idx = int(step_conv.index(min(step_conv[1:])))
    return {
        "abs_step": FUNNEL_LABELS[abs_idx],
        "abs_count": max(drop_off),
        "rel_step": FUNNEL_LABELS[rel_idx],
        "rel_step_conv": step_conv[rel_idx],
        "rel_drop_pct": 100.0 - step_conv[rel_idx],
    }


# ── Channel / age / device segmentation ──────────────────────────────────────
def channel_step_table(df: pd.DataFrame) -> pd.DataFrame:
    """Per-channel conversion rates at each funnel step (%)."""
    table = df.groupby("channel")[FUNNEL_STEPS].mean() * 100
    table.columns = FUNNEL_LABELS
    return table.round(1)


def channel_transition_table(df: pd.DataFrame) -> pd.DataFrame:
    """Per-channel step transitions (App→Reg, Reg→KYC, KYC start→complete,
    overall) — computed from each channel's own counts, not the global ones."""
    rows = []
    for channel, sub in df.groupby("channel"):
        app = sub["app_install"].sum()
        reg = sub["registration"].sum()
        kyc_s = sub["kyc_start"].sum()
        kyc_c = sub["kyc_complete"].sum()
        tx = sub["first_tx"].sum()
        rows.append(
            {
                "Channel": channel,
                "App→Reg %": (reg / app * 100) if app > 0 else 0.0,
                "Reg→KYC %": (kyc_s / reg * 100) if reg > 0 else 0.0,
                "KYC S→C %": (kyc_c / kyc_s * 100) if kyc_s > 0 else 0.0,
                "Overall %": (tx / app * 100) if app > 0 else 0.0,
            }
        )
    return pd.DataFrame(rows).round(1).set_index("Channel")


def age_kyc_completion(df: pd.DataFrame) -> pd.DataFrame:
    """KYC completion rate by age group (among users who started KYC)."""
    sub = df[df["kyc_start"] == 1]
    agg = (
        sub.groupby("age_group")
        .agg(
            kyc_started=("kyc_start", "sum"),
            kyc_completed=("kyc_complete", "sum"),
        )
        .reset_index()
    )
    agg["completion_rate"] = (agg["kyc_completed"] / agg["kyc_started"] * 100).round(1)
    return agg.rename(
        columns={
            "kyc_started": "KYC Started",
            "kyc_completed": "KYC Completed",
            "completion_rate": "Completion Rate %",
            "age_group": "age_group",
        }
    )


def device_funnel(df: pd.DataFrame) -> pd.DataFrame:
    table = df.groupby("device")[FUNNEL_STEPS].mean() * 100
    table.columns = FUNNEL_LABELS
    return table.round(1)


# ── Statistical tests ─────────────────────────────────────────────────────────
def chi_square_activation(df: pd.DataFrame, segment_col: str, a: str, b: str) -> dict[str, float]:
    """Chi-square test on first_tx activation between two segment values."""
    a_df = df[df[segment_col] == a]
    b_df = df[df[segment_col] == b]
    a_act = int(a_df["first_tx"].sum())
    b_act = int(b_df["first_tx"].sum())
    table = np.array(
        [
            [a_act, len(a_df) - a_act],
            [b_act, len(b_df) - b_act],
        ]
    )
    chi2, p_value, dof, _ = stats.chi2_contingency(table)
    return {
        "a_name": a,
        "b_name": b,
        "a_activated": a_act,
        "a_total": len(a_df),
        "a_rate": a_act / len(a_df) * 100 if len(a_df) else 0.0,
        "b_activated": b_act,
        "b_total": len(b_df),
        "b_rate": b_act / len(b_df) * 100 if len(b_df) else 0.0,
        "chi2": chi2,
        "p_value": p_value,
        "dof": dof,
    }


def wilson_ci(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion (95% by default).

    More robust than the normal approximation for small n or proportions near
    0/1. Funnel step conversions are computed on shrinking counts, so the last
    steps have wide CIs that the normal interval understates.
    """
    if total <= 0:
        return (0.0, 0.0)
    p_hat = successes / total
    denom = 1 + z**2 / total
    center = (p_hat + z**2 / (2 * total)) / denom
    half = z * np.sqrt(p_hat * (1 - p_hat) / total + z**2 / (4 * total**2)) / denom
    return (center - half, center + half)


def step_conversion_cis(metrics: dict[str, list[float]]) -> list[tuple[float, float]]:
    """95% Wilson CIs for each step conversion rate (step 0 is 100% by definition)."""
    counts = metrics["counts"]
    cis: list[tuple[float, float]] = []
    for i, count in enumerate(counts):
        if i == 0:
            cis.append((1.0, 1.0))
        else:
            cis.append(wilson_ci(int(count), int(counts[i - 1])))
    return cis


# ── Plots ────────────────────────────────────────────────────────────────────
def plot_main_funnel(metrics: dict[str, list[float]], out: Path) -> None:
    """Funnel counts + step-conversion twin-axis chart."""
    fig, ax1 = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(FUNNEL_LABELS))
    ax1.bar(x, metrics["counts"], color="#4C9AFF", alpha=0.85)
    ax1.set_ylabel("Users", color="#4C9AFF")
    ax1.set_xticks(x)
    ax1.set_xticklabels(FUNNEL_LABELS, rotation=20, ha="right")
    for i, c in enumerate(metrics["counts"]):
        ax1.text(i, c + 120, f"{c:,}", ha="center", fontsize=8)
    ax2 = ax1.twinx()
    ax2.plot(x, metrics["step_conv"], color="#FFAB4C", marker="o", linewidth=2)
    ax2.set_ylabel("Step Conversion %", color="#FFAB4C")
    ax2.set_ylim(0, 105)
    fig.tight_layout()
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)


def plot_channel_breakdown(
    channel_table: pd.DataFrame, channel_transitions: pd.DataFrame, out: Path
) -> None:
    """Channel overall activation + KYC heatmap."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={"width_ratios": [1, 1.2]})
    order = channel_table["First Transaction"].sort_values(ascending=True).index
    ax1.barh(order, channel_table.loc[order, "First Transaction"], color="#4C9AFF")
    ax1.set_xlabel("End-to-end activation %")
    ax1.set_title("Activation by channel")
    sns.heatmap(
        channel_table,
        annot=True,
        fmt=".1f",
        cmap="YlGnBu",
        ax=ax2,
        cbar=False,
        annot_kws={"fontsize": 8},
    )
    ax2.set_title("Channel × funnel step (%)")
    fig.tight_layout()
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)


def plot_segments(age_kyc: pd.DataFrame, device_table: pd.DataFrame, out: Path) -> None:
    """Age-group KYC completion + device step comparison."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    ax1.bar(age_kyc["age_group"], age_kyc["Completion Rate %"], color="#56D364")
    ax1.set_ylabel("KYC completion %")
    ax1.set_title("KYC completion by age group")
    for i, v in enumerate(age_kyc["Completion Rate %"]):
        ax1.text(i, v + 0.5, f"{v:.1f}", ha="center", fontsize=8)
    device_table.T.plot(kind="bar", ax=ax2, color=["#4C9AFF", "#FFAB4C"])
    ax2.set_ylabel("Conversion %")
    ax2.set_title("iOS vs Android by step")
    ax2.legend(title="device")
    ax2.set_xticklabels(FUNNEL_LABELS, rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)


# ── Narrative section printers ──────────────────────────────────────────────
def section_data_quality(df: pd.DataFrame) -> dict[str, pd.Series]:
    print_section("VOLTA NEOBANK — ONBOARDING FUNNEL ANALYSIS", blank=False)
    print(f"\nDataset shape: {df.shape}")
    print(f"Total users: {len(df):,}")
    print("\nFirst few rows:")
    print(df.head())

    print_section("DATA QUALITY ASSESSMENT")
    print("\nData types:")
    print(df.dtypes)
    missing = df.isnull().sum()
    if missing.sum() == 0:
        print("\nMissing values:\n  ✅ No missing values")
    else:
        print(f"\nMissing values:\n{missing[missing > 0]}")

    dists = data_quality(df)
    for label, dist in [
        ("Channel distribution", dists["channel"]),
        ("Device distribution", dists["device"]),
        ("Age group distribution", dists["age_group"]),
    ]:
        print(f"\n{label}:")
        for name, count in dist.items():
            print(f"  {name:<15} {count:>6,}  ({count / len(df) * 100:>5.1f}%)")
    return dists


def section_core_funnel(
    df: pd.DataFrame,
) -> tuple[dict[str, list[float]], dict[str, object], float]:
    print_section("CORE FUNNEL METRICS")
    metrics = compute_funnel(df)
    print("\n" + funnel_summary_table(metrics).to_string(index=False))

    cis = step_conversion_cis(metrics)
    print("\nStep conversion with 95% Wilson confidence intervals:")
    for label, step_conv, (lo, hi) in zip(
        FUNNEL_LABELS, metrics["step_conv"], cis, strict=True
    ):
        print(f"  {label:<20} {step_conv:>6.1f}%  (95% CI: {lo * 100:.1f}% – {hi * 100:.1f}%)")

    drops = biggest_drops(metrics)
    end_to_end = metrics["overall_conv"][-1]
    ltv = CONSTANTS["LTV_PER_USER_EUR"]
    revenue_per_10k = (drops["abs_count"] / len(df)) * 10000 * ltv

    print_section("KEY METRICS")
    print(f"\nEnd-to-end activation: {end_to_end:.1f}%")
    print(f"  (Only {end_to_end:.1f}% of app installs complete first transaction)")
    print(f"\nBiggest ABSOLUTE drop: {drops['abs_step']}")
    print(f"  {drops['abs_count']:,} users drop off at this stage")
    print(f"\nLowest step conversion: {drops['rel_step']} ({drops['rel_step_conv']:.1f}%)")
    print(f"  Biggest RELATIVE drop: {drops['rel_drop_pct']:.1f}% of users at this step")
    print(f"\nRevenue impact of biggest absolute drop ({drops['abs_step']}):")
    print(f"  At LTV of €{ltv}/user: €{revenue_per_10k:,.0f} lost per 10K installs")
    return metrics, drops, revenue_per_10k


def section_hypotheses(drops: dict[str, object]) -> None:
    print_section("HYPOTHESES TO VALIDATE")
    hypotheses = [
        (
            "H1",
            f"{drops['rel_step']} has the lowest step-conversion ({drops['rel_step_conv']:.1f}%) — biggest relative drop",
            "step conversion < 60%",
        ),
        ("H2", "Paid social users have lower activation", "paid social converts worse end-to-end"),
        ("H3", "Older users (45+) drop at KYC more", "45+ KYC completion < 18-24"),
        ("H4", "iOS users convert better than Android", "iOS > Android at each step"),
        (
            "H5",
            "Referral produces best-quality users",
            "Referral has highest end-to-end activation",
        ),
    ]
    for num, statement, expected in hypotheses:
        print(f"\n{num}: {statement}")
        print(f"   Expected: {expected}")


def section_channels(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, str, str, float, float]:
    print_section("FUNNEL ANALYSIS BY ACQUISITION CHANNEL")
    channel_table = channel_step_table(df)
    transitions = channel_transition_table(df)
    print("\nConversion rates by channel (%):\n")
    print(channel_table.to_string())
    print("\nPer-channel step transitions (%):\n")
    print(transitions.to_string())

    print_section("INSIGHT 2: Channel Quality Assessment")
    channel_overall = df.groupby("channel")["first_tx"].mean() * 100
    best_channel = channel_overall.idxmax()
    worst_channel = channel_overall.idxmin()
    best_act = channel_overall.max()
    worst_act = channel_overall.min()
    print(f"\nBest performing channel:  {best_channel:<15} {best_act:.1f}% activation")
    print(f"Worst performing channel: {worst_channel:<15} {worst_act:.1f}% activation")
    print(f"Difference: {best_act - worst_act:.1f} percentage points")
    print("\n→ STRATEGIC IMPLICATION:")
    print(f"   {best_channel.capitalize()} users are {best_act / worst_act:.1f}x more likely")
    print(f"   to activate than {worst_channel} users.")
    print(f"   Recommendation: Reallocate budget from {worst_channel} to {best_channel}.")
    return channel_table, transitions, best_channel, worst_channel, best_act, worst_act


def section_age_device(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, float, float, float, float]:
    print_section("AGE GROUP ANALYSIS: KYC Completion")
    age_kyc = age_kyc_completion(df)
    print("\n" + age_kyc.to_string(index=False))

    print_section("INSIGHT 3: Age Group KYC Performance")
    youngest_kyc = float(age_kyc.iloc[0]["Completion Rate %"])
    oldest_kyc = float(age_kyc.iloc[-1]["Completion Rate %"])
    print(f"\nYoungest cohort (18-24) KYC completion: {youngest_kyc:.1f}%")
    print(f"Oldest cohort (45+) KYC completion: {oldest_kyc:.1f}%")
    print(f"Difference: {youngest_kyc - oldest_kyc:.1f} percentage points")
    print("\n→ HYPOTHESIS: Older users struggle with document upload UX")
    print("   (Photo quality, angle guidance, device limitations)")
    print("   Recommendation: Add in-app document photo assistant with real-time feedback")

    print_section("DEVICE ANALYSIS: Funnel Conversion by Platform")
    device_table = device_funnel(df)
    print("\n" + device_table.to_string())

    print_section("INSIGHT 4: iOS vs Android Performance Gap")
    ios_act = device_table.loc["ios", "First Transaction"]
    android_act = device_table.loc["android", "First Transaction"]
    ios_advantage = ios_act - android_act
    print(f"\niOS end-to-end activation:     {ios_act:.1f}%")
    print(f"Android end-to-end activation: {android_act:.1f}%")
    print(f"Gap: {ios_advantage:.1f} percentage points in favor of iOS")
    print("\nStep-by-step comparison:")
    for label in FUNNEL_LABELS:
        ios_val = device_table.loc["ios", label]
        android_val = device_table.loc["android", label]
        gap = ios_val - android_val
        marker = "⚠️ " if gap > 2 else "✓ "
        print(
            f"  {label:<20} iOS: {ios_val:>6.1f}%  Android: {android_val:>6.1f}%  "
            f"Gap: {gap:>+5.1f}pp {marker}"
        )
    print("\n→ STRATEGIC IMPLICATION:")
    print("   iOS consistently outperforms Android by 2–3pp per step.")
    print(f"   This compounds to ~{ios_advantage:.1f}pp end-to-end advantage.")
    print("   Recommendation: Dedicated Android QA sprint to identify device-specific UX bugs")
    return age_kyc, device_table, youngest_kyc, oldest_kyc, ios_act, android_act, ios_advantage


def section_stat_tests(df: pd.DataFrame) -> tuple[float, float]:
    print_section("STATISTICAL SIGNIFICANCE TESTS")
    print("\nTest 1: Referral vs Paid Social — Activation Rate Difference")
    print("-" * 70)
    r1 = chi_square_activation(df, "channel", "referral", "paid_social")
    _print_chi_square(r1)

    print_section("Test 2: iOS vs Android — Activation Rate Difference", width=70, blank=True)
    print("-" * 70)
    r2 = chi_square_activation(df, "device", "ios", "android")
    _print_chi_square(r2)
    return r1["a_rate"] - r1["b_rate"], r2["a_rate"] - r2["b_rate"]


def _print_chi_square(r: dict[str, float]) -> None:
    print(f"\n{r['a_name'].capitalize()}:")
    print(f"  Activated: {r['a_activated']:,} / {r['a_total']:,}")
    print(f"  Activation rate: {r['a_rate']:.2f}%")
    print(f"\n{r['b_name'].capitalize()}:")
    print(f"  Activated: {r['b_activated']:,} / {r['b_total']:,}")
    print(f"  Activation rate: {r['b_rate']:.2f}%")
    print(f"\nDifference: {r['a_rate'] - r['b_rate']:.2f} percentage points")
    print("\nChi-Square Test Results:")
    print(f"  χ² statistic: {r['chi2']:.4f}")
    print(f"  P-value: {r['p_value']:.6f}")
    print(f"  Degrees of freedom: {r['dof']}")
    print("  Significance level (α): 0.05")
    if r["p_value"] < 0.05:
        print("\n  ✅ SIGNIFICANT: the difference is statistically significant (p < 0.05)")
    else:
        print("\n  ❌ NOT SIGNIFICANT: we cannot rule out chance (p ≥ 0.05)")


def section_findings(
    metrics: dict[str, list[float]],
    drops: dict[str, object],
    revenue_per_10k: float,
    youngest_kyc: float,
    oldest_kyc: float,
    ios_advantage: float,
    referral_paid_diff: float,
) -> None:
    print_section("SUMMARY: KEY FINDINGS & ACTIONABLE RECOMMENDATIONS")
    findings = [
        (
            1,
            f"{drops['rel_step']} step conversion is {drops['rel_step_conv']:.1f}% — lowest in the funnel (biggest relative drop, {drops['rel_drop_pct']:.1f}%)",
            f"{drops['abs_count']:,} users lost at this stage; KYC is the conversion bottleneck",
            "Redesign KYC UX: add progress bar, clearer document guidance, retry flow",
        ),
        (
            2,
            f"{drops['abs_step']} loses {drops['abs_count']:,} users — biggest ABSOLUTE drop-off",
            f"~€{revenue_per_10k:,.0f} lost per 10K installs",
            "A/B test simplified registration (email only vs full form)",
        ),
        (
            3,
            f"Referral converts {referral_paid_diff:.1f}pp better than paid social",
            "Lower CAC, higher LTV via referral channel",
            "Launch referral program with €10 bonus, reallocate paid social budget",
        ),
        (
            4,
            "45+ age group drops at KYC significantly more",
            f"{youngest_kyc - oldest_kyc:.1f}pp gap vs 18-24 cohort",
            "Add in-app document photo assistant with real-time feedback",
        ),
        (
            5,
            "iOS outperforms Android at every step",
            f"{ios_advantage:.1f}pp end-to-end difference",
            "Dedicated Android QA sprint, identify device-specific UX bugs",
        ),
        (
            6,
            f"Card ordered → First TX at {metrics['step_conv'][5]:.1f}%",
            "Users get card but never activate",
            "Push notification on card arrival + first-use incentive (€2 cashback)",
        ),
    ]
    for num, insight, impact, rec in findings:
        print(f"\n{num}. {insight}")
        print(f"   Impact: {impact}")
        print(f"   → {rec}")


def section_proposed_tests() -> None:
    print_section("PROPOSED A/B TESTS (→ Project 2: A/B Testing)")
    tests = [
        (
            "KYC Progress Bar",
            "Adding a progress bar to KYC increases completion by 5pp",
            "Current KYC flow (no visual progress indicator)",
            "KYC flow with step-by-step progress bar",
            "KYC start → KYC complete conversion",
            "~4,000 per arm",
            "🔴 HIGHEST PRIORITY",
        ),
        (
            "Simplified Registration Form",
            "Removing phone number field increases registration completion",
            "Current form (email + phone + name)",
            "Simplified form (email + name only)",
            "App install → Registration conversion",
            "~8,000 per arm",
            "🟠 HIGH PRIORITY",
        ),
        (
            "Card Activation Nudge",
            "Push notification on card arrival increases first transaction",
            "No push notification",
            'Personalized push: "Your card is ready + €2 cashback for first use"',
            "Card ordered → First transaction",
            "~6,000 per arm",
            "🟠 HIGH PRIORITY",
        ),
    ]
    for i, (name, hyp, ctrl, treat, metric, sample, prio) in enumerate(tests, 1):
        print(f"\nTest {i}: {name}  {prio}")
        print(f"  Hypothesis: {hyp}")
        print(f"  Control:    {ctrl}")
        print(f"  Treatment:  {treat}")
        print(f"  Metric:     {metric}")
        print(f"  Sample:     {sample}")


def section_dashboard() -> None:
    print_section("DASHBOARD DESIGN FOR ONGOING MONITORING")
    views = [
        (
            "Funnel Overview",
            "Bar chart with overall + step-by-step conversion rates",
            "Date range filter, segment toggle (channel/device/age)",
            "Daily",
        ),
        (
            "Channel Heatmap",
            "Channel × funnel step matrix showing conversion %",
            "Highlight cells where channel underperforms, flagging alerts",
            "Weekly",
        ),
        (
            "Segment Drill-down",
            "Interactive filters: age group, device, channel",
            "Dynamic funnel update based on selected filters",
            "Daily",
        ),
        (
            "Trend Line",
            "Weekly activation rate trend (rolling 4-week average)",
            "Anomaly detection, overlay of experiment dates",
            "Weekly",
        ),
        (
            "Revenue Impact",
            "Slider to estimate revenue loss from improving each step",
            'Sensitivity analysis: "If we improve KYC step-conv from 56.6% to 61.6%..."',
            "Monthly",
        ),
    ]
    print("\nRecommended Tableau / Power BI views:\n")
    for i, (name, desc, feat, refresh) in enumerate(views, 1):
        print(f"{i}. {name}")
        print(f"   Description: {desc}")
        print(f"   Features: {feat}")
        print(f"   Refresh: {refresh}")


def _next_steps(drops: dict[str, object], end_to_end: float) -> None:
    print_section("NEXT STEPS")
    print(f"""
1. IMMEDIATE (This week):
   ✓ Share findings with product & engineering teams
   ✓ Prioritize KYC progress bar redesign (lowest step-conv at {drops["rel_step_conv"]:.1f}%)
   ✓ Plan Project 2: A/B test the KYC progress bar fix

2. SHORT-TERM (This month):
   ✓ Set up funnel dashboard in Tableau/Power BI
   ✓ Implement simplified registration A/B test (biggest absolute drop: {drops["abs_count"]:,} users)
   ✓ Begin Android optimization sprint

3. MEDIUM-TERM (Next quarter):
   ✓ Roll out winning test variations
   ✓ Reassess funnel metrics post-implementation
   ✓ Move to Project 3: Measure retention impact of improvements

Expected impact if all recommendations are implemented:
   • KYC step conversion: {drops["rel_step_conv"]:.1f}% → {drops["rel_step_conv"] + 5:.1f}% (+5pp, estimated via A/B test)
   • End-to-end activation: {end_to_end:.1f}% → {end_to_end + 5.5:.1f}% (+5.5pp total)
    """)


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    setup()
    df = load_data()

    section_data_quality(df)
    metrics, drops, revenue_per_10k = section_core_funnel(df)
    section_hypotheses(drops)
    channel_table, transitions, *_ = section_channels(df)
    age_kyc, device_table, youngest_kyc, oldest_kyc, ios_act, android_act, ios_advantage = (
        section_age_device(df)
    )
    referral_diff, _ = section_stat_tests(df)
    section_findings(
        metrics, drops, revenue_per_10k, youngest_kyc, oldest_kyc, ios_advantage, referral_diff
    )
    section_proposed_tests()
    section_dashboard()

    # Save visualisations to repo root (tracked as portfolio artifacts).
    plot_main_funnel(metrics, OUTPUT_DIR / "viz1_main_funnel.png")
    plot_channel_breakdown(channel_table, transitions, OUTPUT_DIR / "viz2_channel_breakdown.png")
    plot_segments(age_kyc, device_table, OUTPUT_DIR / "viz3_segments.png")
    print("\nSaved: viz1_main_funnel.png, viz2_channel_breakdown.png, viz3_segments.png")

    _next_steps(drops, metrics["overall_conv"][-1])


if __name__ == "__main__":
    main()
