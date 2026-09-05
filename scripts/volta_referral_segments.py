"""Project 17 — Referral conversion by JTBD segment (audit risk #5).

Validates the JTBD audit's risk #5: "referral doesn't scale to new segments".
The referral funnel (sent → accepted → kyc_completed → first_tx) is cut by
JTBD segment. The anchor (young professionals) and status-seekers convert
well; digital newcomers 45+ and family budgeters barely do — the referral
value prop doesn't transfer. Channel (in_app > email > link) helps but can't
close the gap.

Conclusion: don't scale referral budget to gap segments without segment-
specific incentives (assisted onboarding for 45+, cashback for family
budgeters). Referral stays an anchor-channel acquisition lever.

Run:  PYTHONPATH=.:scripts uv run python scripts/volta_referral_segments.py
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import TypedDict

import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

from utils.common import OUTPUT_DIR, data_path, print_section, print_subsection, setup

SEGMENT_ORDER = [
    "young_professionals",
    "digital_newcomers",
    "travelers",
    "family_budgeters",
    "premium_status",
]
SEGMENT_NAMES: dict[str, str] = {
    "young_professionals": "Young Professionals 25-34",
    "digital_newcomers": "Digital Newcomers 45+",
    "travelers": "Travelers / Nomads",
    "family_budgeters": "Family Budgeters 30-45",
    "premium_status": "Premium Status-Seekers",
}
ANCHOR_SEGMENT = "young_professionals"
GAP_SEGMENTS = ["digital_newcomers", "family_budgeters"]
COHORT_ORDER = ["Power", "Growth", "Casual", "Dormant"]
CHANNEL_ORDER = ["in_app", "email", "link"]
STATUS_ORDER = ["sent", "accepted", "kyc_completed", "first_tx"]


class ChiSquareResult(TypedDict):
    chi2: float
    p_value: float
    dof: int
    expected_min: float


def load_data() -> pd.DataFrame:
    return pd.read_csv(data_path("volta_referral_segments.csv"))


def two_proportion_ztest(n1: int, x1: int, n2: int, x2: int) -> tuple[float, float]:
    """Two-proportion z-test; returns (z, two-sided p)."""
    p1 = x1 / n1
    p2 = x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    return z, p_value


def chi_square_segment_status(df: pd.DataFrame) -> ChiSquareResult:
    """Segment × final status independence test (risk #5: does segment matter?)."""
    ctab = pd.crosstab(df["jtbd_segment"], df["status"]).reindex(
        index=SEGMENT_ORDER, columns=STATUS_ORDER, fill_value=0
    )
    chi2, p, dof, expected = stats.chi2_contingency(ctab)
    return {
        "chi2": float(chi2),
        "p_value": float(p),
        "dof": int(dof),
        "expected_min": float(expected.min()),
    }


def funnel_by_segment(df: pd.DataFrame) -> pd.DataFrame:
    """Per-segment referral funnel: counts + step + overall conversion."""
    rows: list[dict[str, float | int]] = []
    for seg in SEGMENT_ORDER:
        sub = df[df["jtbd_segment"] == seg]
        n = len(sub)
        accepted = int((sub["status"] != "sent").sum())
        kyc = int(sub["status"].isin(["kyc_completed", "first_tx"]).sum())
        first_tx = int((sub["status"] == "first_tx").sum())
        rows.append(
            {
                "referrals": n,
                "accepted": accepted,
                "kyc": kyc,
                "first_tx": first_tx,
                "accept_rate": accepted / n * 100,
                "kyc_given_accepted": kyc / accepted * 100 if accepted else 0.0,
                "first_tx_given_kyc": first_tx / kyc * 100 if kyc else 0.0,
                "overall_conv": first_tx / n * 100,
            }
        )
    return pd.DataFrame(rows, index=SEGMENT_ORDER)


def conversion_by_channel(df: pd.DataFrame) -> pd.DataFrame:
    """Sent → first-tx conversion by invite channel (all segments)."""
    g = df.groupby("channel")["first_tx"].agg(["count", "sum", "mean"])
    g["conv_rate"] = g["mean"] * 100
    return g.reindex(CHANNEL_ORDER).round(2)


def channel_within_gap(df: pd.DataFrame) -> pd.DataFrame:
    """Channel effect inside the gap segments — can a better channel close it?"""
    gap = df[df["jtbd_segment"].isin(GAP_SEGMENTS)]
    g = gap.groupby("channel")["first_tx"].agg(["count", "sum", "mean"])
    g["conv_rate"] = g["mean"] * 100
    return g.reindex(CHANNEL_ORDER).round(2)


def plot_conversion_by_segment(df: pd.DataFrame, out: Path) -> None:
    """Bar chart of sent → first-tx conversion by segment (anchor teal, gap red)."""
    rates = funnel_by_segment(df)["overall_conv"]
    colors = [
        "#4ec9b0" if s == ANCHOR_SEGMENT else "#e06c75" if s in GAP_SEGMENTS else "#569cd6"
        for s in SEGMENT_ORDER
    ]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(range(len(SEGMENT_ORDER)), rates, color=colors)
    ax.set_xticks(range(len(SEGMENT_ORDER)))
    ax.set_xticklabels([SEGMENT_NAMES[s] for s in SEGMENT_ORDER], rotation=20, ha="right")
    ax.set_ylabel("Sent → first-tx conversion (%)")
    ax.set_title("Referral conversion by JTBD segment")
    for i, v in enumerate(rates):
        ax.text(i, v + 0.3, f"{v:.1f}%", ha="center")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def section_1_overview(df: pd.DataFrame) -> None:
    print_section("1. Overview — referral funnel by JTBD segment")
    print(f"Referrals: {len(df):,} | Segments: {df['jtbd_segment'].nunique()}")
    overall = (df["first_tx"] == 1).mean() * 100
    print(f"Overall sent → first-tx conversion: {overall:.2f}%")
    print("\nReferral volume by segment:")
    print(df["jtbd_segment"].value_counts().reindex(SEGMENT_ORDER).to_string())


def section_2_funnel(df: pd.DataFrame) -> None:
    print_section("2. Referral funnel by segment")
    funnel = funnel_by_segment(df)
    print(funnel.round(1).to_string())
    print("\nStep-conversion contrast (anchor vs gap):")
    anchor = funnel.loc[ANCHOR_SEGMENT]
    for gap in GAP_SEGMENTS:
        g = funnel.loc[gap]
        print(
            f"  {SEGMENT_NAMES[gap]}: accept {g['accept_rate']:.1f}% vs "
            f"{SEGMENT_NAMES[ANCHOR_SEGMENT]} {anchor['accept_rate']:.1f}% | "
            f"overall {g['overall_conv']:.1f}% vs {anchor['overall_conv']:.1f}%"
        )


def section_3_tests(df: pd.DataFrame) -> None:
    print_section("3. Statistical tests")
    chi = chi_square_segment_status(df)
    print(
        f"Chi-square segment × status: chi2={chi['chi2']:.1f}, dof={chi['dof']}, "
        f"p={chi['p_value']:.4g} (expected min {chi['expected_min']:.1f})"
    )
    print(
        "  → segment and referral outcome are NOT independent"
        if chi["p_value"] < 0.05
        else "  → independent"
    )

    print_subsection("Anchor vs gap — two-proportion z-test on first-tx conversion")
    for gap in GAP_SEGMENTS:
        n1 = int((df["jtbd_segment"] == ANCHOR_SEGMENT).sum())
        x1 = int(((df["jtbd_segment"] == ANCHOR_SEGMENT) & (df["first_tx"] == 1)).sum())
        n2 = int((df["jtbd_segment"] == gap).sum())
        x2 = int(((df["jtbd_segment"] == gap) & (df["first_tx"] == 1)).sum())
        z, p = two_proportion_ztest(n1, x1, n2, x2)
        print(f"  {SEGMENT_NAMES[gap]} vs {SEGMENT_NAMES[ANCHOR_SEGMENT]}: z={z:.2f}, p={p:.4g}")


def section_4_channel(df: pd.DataFrame) -> None:
    print_section("4. Channel effect")
    print("Sent → first-tx conversion by channel (all segments):")
    print(conversion_by_channel(df).to_string())
    print("\nChannel effect within gap segments (can a better channel close it?):")
    print(channel_within_gap(df).to_string())


def section_5_conclusion(df: pd.DataFrame) -> None:
    print_section("5. Conclusion — does referral scale to new segments?")
    funnel = funnel_by_segment(df)
    anchor_conv = funnel.loc[ANCHOR_SEGMENT, "overall_conv"]
    gap_conv = funnel.loc[GAP_SEGMENTS, "overall_conv"].mean()
    print(f"Anchor ({SEGMENT_NAMES[ANCHOR_SEGMENT]}) referral conversion: {anchor_conv:.1f}%")
    print(
        f"Gap segments ({', '.join(SEGMENT_NAMES[s] for s in GAP_SEGMENTS)}) mean: {gap_conv:.1f}%"
    )
    print("\nVerdict: referral does NOT scale to gap segments — the value prop")
    print("(invite a friend, both get a reward) lands only where the product")
    print("already fits. Channel (in_app) helps but cannot close the gap.")
    print("\nImplication: don't scale referral budget blindly. Segment-specific")
    print("incentives — assisted onboarding for 45+, cashback for family")
    print("budgeters — before expanding referral beyond the anchor.")


def main() -> None:
    setup(float_format="{:.2f}")
    df = load_data()
    df["first_tx"] = (df["status"] == "first_tx").astype(int)

    section_1_overview(df)
    section_2_funnel(df)
    section_3_tests(df)
    section_4_channel(df)
    section_5_conclusion(df)

    out = OUTPUT_DIR / "referral_conversion_by_segment.png"
    plot_conversion_by_segment(df, out)
    print(f"\nSaved: {out}")
    print("Analysis complete.")


if __name__ == "__main__":
    main()
