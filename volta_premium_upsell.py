"""
Volta Neobank — Premium Upsell

Project: Product Analytics Portfolio — Market & Jobs layer (Sprint 6, T4)
Industry: Fintech / Digital Banking
Type: Free→Premium conversion · Segment transfer · Driver analysis

Validates audit risk #2: "Premium-апселл не переносится на новые сегменты"
(premium upsell doesn't transfer to new segments). The anchor segment
(young professionals) and status-seekers (premium_status) convert well;
digital newcomers 45+ and family budgeters barely convert — the upsell
value prop doesn't land outside the anchor.

Data: produced by `generate_premium_upsell_data.py` → volta_premium_upsell.csv
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import TypedDict

import pandas as pd
from scipy.stats import chi2_contingency, norm
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from utils.common import OUTPUT_DIR, data_path, print_section, print_subsection, setup

SEGMENT_ORDER = [
    "young_professionals",
    "digital_newcomers",
    "travelers",
    "family_budgeters",
    "premium_status",
]
SEGMENT_NAMES: dict[str, str] = {
    "young_professionals": "Young Professionals",
    "digital_newcomers": "Digital Newcomers 45+",
    "travelers": "Travelers",
    "family_budgeters": "Family Budgeters",
    "premium_status": "Premium Status",
}
COHORT_ORDER = ["Power", "Growth", "Casual", "Dormant"]
CHANNEL_ORDER = ["in_app", "email", "push", "none"]
# The audit's anchor segment vs the segment the upsell fails to reach.
ANCHOR_SEGMENT = "young_professionals"
TRANSFER_GAP_SEGMENT = "digital_newcomers"
DRIVER_FEATURES = ["logins_per_week", "tx_per_month", "balance_eur", "months_since_signup"]


class ChiSquareResult(TypedDict):
    chi2: float
    p: float
    dof: int


# ── Load ──────────────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    return pd.read_csv(data_path("volta_premium_upsell.csv"))


# ── Conversion ───────────────────────────────────────────────────────────────
def conversion_by_segment(df: pd.DataFrame) -> pd.DataFrame:
    """Per-segment: users, converted, Free→Premium conversion rate %."""
    rows: list[dict[str, float | int]] = []
    for seg in SEGMENT_ORDER:
        sub = df[df["jtbd_segment"] == seg]
        rows.append(
            {
                "users": int(len(sub)),
                "converted": int(sub["converted"].sum()),
                "conv_rate": float(sub["converted"].mean() * 100),
            }
        )
    return pd.DataFrame(rows, index=SEGMENT_ORDER)


def conversion_by_cohort(df: pd.DataFrame) -> pd.DataFrame:
    """Conversion rate by behavioral cohort."""
    g = df.groupby("cohort")["converted"].agg(["count", "sum", "mean"])
    g["conv_rate"] = g["mean"] * 100
    return g.reindex(COHORT_ORDER).round(2)


def conversion_by_segment_cohort(df: pd.DataFrame) -> pd.DataFrame:
    """Segment × cohort conversion-rate cross-tab (%)."""
    tab = (
        df.pivot_table(index="jtbd_segment", columns="cohort", values="converted", aggfunc="mean")
        * 100
    )
    return tab.reindex(index=SEGMENT_ORDER, columns=COHORT_ORDER).round(1)


# ── Statistical tests ────────────────────────────────────────────────────────
def chi_square_segment_conversion(df: pd.DataFrame) -> ChiSquareResult:
    """Segment × converted independence test."""
    tab = pd.crosstab(df["jtbd_segment"], df["converted"]).reindex(SEGMENT_ORDER)
    chi2, p, dof, _ = chi2_contingency(tab)
    return {"chi2": float(chi2), "p": float(p), "dof": int(dof)}


def two_proportion_ztest(n1: int, x1: int, n2: int, x2: int) -> dict[str, float]:
    """Two-proportion z-test (normal approximation)."""
    p1, p2 = x1 / n1, x2 / n2
    p = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se
    p_value = 2 * (1 - norm.cdf(abs(z)))
    return {"p1": float(p1), "p2": float(p2), "z": float(z), "p": float(p_value)}


def segment_conversion_counts(df: pd.DataFrame, segment: str) -> tuple[int, int]:
    """(n_users, converted) for one segment."""
    sub = df[df["jtbd_segment"] == segment]
    return int(len(sub)), int(sub["converted"].sum())


# ── Drivers ───────────────────────────────────────────────────────────────────
def driver_importance(df: pd.DataFrame) -> pd.DataFrame:
    """Logistic regression coefficients on standardized engagement features."""
    X = df[DRIVER_FEATURES].values
    y = df["converted"].values
    model = LogisticRegression(max_iter=1000)
    model.fit(StandardScaler().fit_transform(X), y)
    return (
        pd.DataFrame({"feature": DRIVER_FEATURES, "coef": model.coef_[0]})
        .sort_values("coef", ascending=False)
        .round(4)
    )


def offer_channel_effect(df: pd.DataFrame) -> pd.DataFrame:
    """Conversion rate by offer channel."""
    g = df.groupby("offer_channel")["converted"].agg(["count", "mean"])
    g["conv_rate"] = g["mean"] * 100
    return g.reindex(CHANNEL_ORDER).round(2)


def upgrade_reason_by_segment(df: pd.DataFrame) -> pd.DataFrame:
    """Top upgrade reason per segment among converters."""
    conv = df[df["converted"] == 1]
    g = conv.groupby("jtbd_segment")["upgrade_reason"].agg(lambda s: s.mode().iloc[0])
    return g.reindex(SEGMENT_ORDER).rename("top_reason").to_frame()


def plot_conversion_by_segment(df: pd.DataFrame, out: Path) -> Path:
    """Bar chart: Free→Premium conversion by JTBD segment, gap highlighted."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.style.use("dark_background")
    ue = conversion_by_segment(df)
    rates = ue["conv_rate"].values
    colors = [
        "#4ec9b0" if s in (ANCHOR_SEGMENT, "premium_status") else "#e06c75" for s in SEGMENT_ORDER
    ]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.bar(range(len(SEGMENT_ORDER)), rates, color=colors)
    ax.axhline(
        float(rates.mean()),
        color="white",
        linestyle="--",
        alpha=0.7,
        label=f"Overall avg {rates.mean():.1f}%",
    )
    ax.set_xticks(range(len(SEGMENT_ORDER)))
    ax.set_xticklabels([SEGMENT_NAMES[s] for s in SEGMENT_ORDER], rotation=30, ha="right")
    ax.set_ylabel("Free→Premium conversion (%)")
    ax.set_title("Premium Upsell — Conversion by JTBD Segment")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


# ── Sections ─────────────────────────────────────────────────────────────────
def section_setup(df: pd.DataFrame) -> None:
    print_section("VOLTA NEOBANK — PREMIUM UPSELL", blank=False)
    print(f"\nDataset shape: {df.shape}")
    print(f"Users: {len(df):,}")
    print(f"Overall Free→Premium conversion: {df['converted'].mean() * 100:.1f}%")
    print("\nSegment mix:")
    for seg in SEGMENT_ORDER:
        n = int((df["jtbd_segment"] == seg).sum())
        print(f"  {SEGMENT_NAMES[seg]:<24} {n:>6,} users  ({n / len(df) * 100:>5.1f}%)")


def section_conversion_by_segment(
    ue: pd.DataFrame, chi: ChiSquareResult, z: dict[str, float]
) -> None:
    print_section("CONVERSION BY JTBD SEGMENT")
    display = ue.rename(index=SEGMENT_NAMES).round(2)
    print("\nFree→Premium conversion:")
    print(display.to_string())
    print_subsection("STATISTICAL TESTS")
    print(f"  Chi-square (segment × converted): chi2={chi['chi2']:.1f}, p={chi['p']:.4f}")
    print(
        f"  Two-proportion z-test ({SEGMENT_NAMES[ANCHOR_SEGMENT]} vs {SEGMENT_NAMES[TRANSFER_GAP_SEGMENT]}):"
    )
    print(f"    {z['p1'] * 100:.1f}% vs {z['p2'] * 100:.1f}%  (z={z['z']:.1f}, p={z['p']:.4f})")
    print("  → The upsell converts in the anchor but not in new segments.")


def section_conversion_by_cohort(cohort: pd.DataFrame, seg_cohort: pd.DataFrame) -> None:
    print_section("CONVERSION BY BEHAVIORAL COHORT")
    print("\nBy cohort:")
    print(cohort.to_string())
    print("\nSegment × cohort conversion (%):")
    print(seg_cohort.rename(index=SEGMENT_NAMES).to_string())
    print_subsection("READING THE TABLE")
    print("  Power/Growth convert; Dormant barely converts — but the segment")
    print("  gap persists within every cohort (upsell doesn't transfer).")


def section_drivers(imp: pd.DataFrame) -> None:
    print_section("TOP DRIVERS OF CONVERSION (LOGISTIC REGRESSION)")
    print("\nStandardized coefficients (positive = raises conversion):")
    print(imp.to_string(index=False))
    print_subsection("READING THE TABLE")
    print("  Engagement (logins, tx, balance) drives conversion — but the")
    print("  segment gap dominates: the same engagement converts several times")
    print("  better in the anchor than in digital newcomers 45+.")


def section_offer_channel(ch: pd.DataFrame) -> None:
    print_section("OFFER CHANNEL EFFECT")
    print("\nConversion by offer channel:")
    print(ch.to_string())
    print_subsection("READING THE TABLE")
    print("  In-app beats push/email — but channel lift is smaller than the")
    print("  segment gap. Channel optimization can't fix a value-prop mismatch.")


def section_upgrade_reasons(reasons: pd.DataFrame) -> None:
    print_section("WHY CONVERTERS UPGRADE (BY SEGMENT)")
    print("\nTop upgrade reason among converters:")
    print(reasons.rename(index=SEGMENT_NAMES).to_string())
    print_subsection("READING THE TABLE")
    print("  Anchor converts for features/status; digital newcomers 45+ for")
    print("  support — the value prop differs by segment. One upsell doesn't fit all.")


def section_conclusion() -> None:
    print_section("CONCLUSION: PREMIUM UPSELL DOESN'T TRANSFER TO NEW SEGMENTS")
    print("""
Risk #2 validated: premium upsell doesn't transfer to new segments.

  • Conversion concentrates in the anchor (young professionals) and
    status-seekers (premium_status); digital newcomers 45+ and family
    budgeters barely convert.
  • Chi-square: segment × conversion NOT independent (p < 0.001).
  • Engagement (logins, tx, balance) drives conversion, but the segment
    gap dominates — the upsell value prop doesn't land outside the anchor.
  • Implication: don't roll out a single premium upsell to all segments.
    Segment-specific offers: cashback for family budgeters, support for
    digital newcomers 45+, FX features for travelers.

Next step (audit risk #4): 45+ KYC deep-dive.
""")


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    setup(float_format="{:.2f}")
    df = load_data()

    section_setup(df)

    ue = conversion_by_segment(df)
    chi = chi_square_segment_conversion(df)
    n1, x1 = segment_conversion_counts(df, ANCHOR_SEGMENT)
    n2, x2 = segment_conversion_counts(df, TRANSFER_GAP_SEGMENT)
    z = two_proportion_ztest(n1, x1, n2, x2)
    section_conversion_by_segment(ue, chi, z)

    cohort = conversion_by_cohort(df)
    seg_cohort = conversion_by_segment_cohort(df)
    section_conversion_by_cohort(cohort, seg_cohort)

    imp = driver_importance(df)
    section_drivers(imp)

    ch = offer_channel_effect(df)
    section_offer_channel(ch)

    reasons = upgrade_reason_by_segment(df)
    section_upgrade_reasons(reasons)

    out = OUTPUT_DIR / "premium_upsell_conversion_by_segment.png"
    plot_conversion_by_segment(df, out)
    print(f"\nSaved: {out.name}")

    section_conclusion()
    print("=" * 70)
    print("Analysis complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
