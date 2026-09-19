"""
Volta Neobank — Segment-Specific Premium Offers (A/B)

Project: Product Analytics Portfolio — Market & Jobs validation layer (RAT v2, risk #3)
Industry: Fintech / Digital Banking
Type: Randomized experiment · Segment × arm interaction · Ship gate

Validates audit risk v2 #3: "segment-specific premium offers won't lift
gap-segment conversion (the fix is untested)". Project 15 showed the *generic*
premium upsell doesn't transfer (anchor 17% vs Digital Newcomers 45+ 2%) and
recommended segment-specific offers — but never tested them. This project runs
that test: a randomized A/B of a generic upsell (control) vs a segment-specific
offer (treatment) in four segments.

Finding: risk #3 is partially refuted. Segment-specific offers DO lift
conversion in the gap segments (+3.3pp 45+, +4.2pp family budgeters) and the
lift is significantly larger there than in the anchor (segment × arm
interaction) — but conversion still lands well below the anchor, so the fix
narrows the value-prop gap without closing it.

Data: produced by `generate_premium_offers_data.py` → volta_premium_offers.csv

Run:  PYTHONPATH=.:scripts uv run python scripts/volta_premium_offers.py
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import TypedDict

import numpy as np
import pandas as pd
from scipy import stats

from utils.common import CONSTANTS, OUTPUT_DIR, data_path, print_section, print_subsection, setup
from utils.viz_helpers import PALETTE, add_chart_context, save_chart_report

SEGMENT_ORDER = [
    "young_professionals",
    "digital_newcomers",
    "family_budgeters",
    "travelers",
]
SEGMENT_NAMES: dict[str, str] = {
    "young_professionals": "Young Professionals 25-34",
    "digital_newcomers": "Digital Newcomers 45+",
    "family_budgeters": "Family Budgeters 30-45",
    "travelers": "Travelers / Nomads",
}
ANCHOR_SEGMENT = "young_professionals"
GAP_SEGMENTS = ["digital_newcomers", "family_budgeters", "travelers"]
CONTROL, TREATMENT = "control", "treatment"

ALPHA = 0.05
POWER = 0.80
# Premium ARPU uplift per converted user (EUR/month), from the shared constants.
PREMIUM_ARPU_DELTA = CONSTANTS["MONTHLY_ARPU_PREMIUM_EUR"] - CONSTANTS["MONTHLY_ARPU_FREE_EUR"]
# Ship gate: significant after correction and a positive absolute lift.
MIN_SHIP_LIFT_PP = 0.0


class LiftRow(TypedDict):
    control_rate: float
    treatment_rate: float
    lift_pp: float
    se_pp: float
    ci_lo_pp: float
    ci_hi_pp: float
    z: float
    p: float


# ── Load ──────────────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    return pd.read_csv(data_path("volta_premium_offers.csv"))


# ── Stats ─────────────────────────────────────────────────────────────────────
def calc_sample_size(
    p_baseline: float, mde: float, alpha: float = ALPHA, power: float = POWER
) -> int:
    """Required sample size per arm for a two-proportion z-test."""
    from scipy.stats import norm

    p_treatment = p_baseline + mde
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)
    p_avg = (p_baseline + p_treatment) / 2
    n = (
        z_alpha * np.sqrt(2 * p_avg * (1 - p_avg))
        + z_beta * np.sqrt(p_baseline * (1 - p_baseline) + p_treatment * (1 - p_treatment))
    ) ** 2 / (p_treatment - p_baseline) ** 2
    return int(np.ceil(n))


def two_proportion_ztest(n1: int, x1: int, n2: int, x2: int) -> tuple[float, float]:
    """Two-proportion z-test; returns (z, two-sided p)."""
    p1, p2 = x1 / n1, x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return 0.0, 1.0
    z = (p1 - p2) / se
    return float(z), float(2 * (1 - stats.norm.cdf(abs(z))))


def srm_check(df: pd.DataFrame) -> dict[str, float]:
    """Sample-ratio mismatch: are the two arms equal within each segment?"""
    counts = df.groupby(["jtbd_segment", "group"]).size().unstack()
    chi2, p, dof, _ = stats.chi2_contingency(counts.values)
    return {"chi2": float(chi2), "p": float(p), "dof": int(dof)}


def conversion_by_segment_arm(df: pd.DataFrame) -> pd.DataFrame:
    """Conversion rate (%) by segment × arm."""
    tab = df.pivot_table(index="jtbd_segment", columns="group", values="converted", aggfunc="mean")
    tab = tab.reindex(index=SEGMENT_ORDER, columns=[CONTROL, TREATMENT]) * 100
    return tab.round(2)


def lift_by_segment(df: pd.DataFrame) -> pd.DataFrame:
    """Per-segment treatment lift (pp) with SE, 95% CI, z and p."""
    rows: dict[str, LiftRow] = {}
    for seg in SEGMENT_ORDER:
        sub = df[df["jtbd_segment"] == seg]
        c = sub[sub["group"] == CONTROL]["converted"]
        t = sub[sub["group"] == TREATMENT]["converted"]
        n_c, n_t = len(c), len(t)
        p_c, p_t = float(c.mean()), float(t.mean())
        lift = (p_t - p_c) * 100
        se = math.sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t) * 100
        z, p = two_proportion_ztest(n_t, int(t.sum()), n_c, int(c.sum()))
        rows[seg] = {
            "control_rate": p_c * 100,
            "treatment_rate": p_t * 100,
            "lift_pp": lift,
            "se_pp": se,
            "ci_lo_pp": lift - 1.96 * se,
            "ci_hi_pp": lift + 1.96 * se,
            "z": z,
            "p": p,
        }
    return pd.DataFrame(rows).T


def holm(pvals: list[float], alpha: float = ALPHA) -> list[bool]:
    """Holm step-down correction across segments."""
    m = len(pvals)
    order = np.argsort(pvals)
    rej = [False] * m
    for rank, idx in enumerate(order):
        if pvals[idx] <= alpha / (m - rank):
            rej[idx] = True
        else:
            break
    return rej


def interaction_test(lift: pd.DataFrame, segment: str) -> dict[str, float]:
    """DiD z-test: is the lift in `segment` larger than in the anchor?"""
    l_gap = lift.loc[segment, "lift_pp"]
    l_anchor = lift.loc[ANCHOR_SEGMENT, "lift_pp"]
    se = math.sqrt(
        float(lift.loc[segment, "se_pp"]) ** 2 + float(lift.loc[ANCHOR_SEGMENT, "se_pp"]) ** 2
    )
    z = (l_gap - l_anchor) / se
    p = float(2 * (1 - stats.norm.cdf(abs(z))))
    return {"diff_pp": float(l_gap - l_anchor), "se_pp": se, "z": float(z), "p": p}


def residual_gap(df: pd.DataFrame) -> pd.DataFrame:
    """Treatment conversion vs the anchor's *control* conversion — the remaining gap."""
    tab = conversion_by_segment_arm(df)
    anchor_control = float(tab.loc[ANCHOR_SEGMENT, CONTROL])
    rows: list[dict[str, float | str]] = []
    for seg in GAP_SEGMENTS:
        treat = float(tab.loc[seg, TREATMENT])
        rows.append(
            {
                "segment": SEGMENT_NAMES[seg],
                "treatment_rate": treat,
                "anchor_control": anchor_control,
                "residual_gap_pp": treat - anchor_control,
                "multiple_vs_anchor": anchor_control / treat if treat else float("nan"),
            }
        )
    return pd.DataFrame(rows).set_index("segment")


def business_impact(lift_pp: float, per_users: int = 10_000) -> dict[str, float]:
    """Annual premium ARPU created per 10K treated users at a given lift."""
    incremental_users = lift_pp / 100 * per_users
    annual_arpu = incremental_users * PREMIUM_ARPU_DELTA * 12
    return {"incremental_users": incremental_users, "annual_arpu_eur": annual_arpu}


# ── Charts ────────────────────────────────────────────────────────────────────
def plot_conversion(df: pd.DataFrame, out: Path) -> Path:
    """Grouped bars: conversion by segment × arm."""
    import matplotlib.pyplot as plt

    tab = conversion_by_segment_arm(df)
    x = np.arange(len(SEGMENT_ORDER))
    width = 0.38
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width / 2, tab[CONTROL], width, label="Control (generic)", color=PALETTE[6])
    ax.bar(
        x + width / 2, tab[TREATMENT], width, label="Treatment (segment-specific)", color=PALETTE[0]
    )
    for i, seg in enumerate(SEGMENT_ORDER):
        ax.text(
            i + width / 2,
            tab.loc[seg, TREATMENT] + 0.3,
            f"{tab.loc[seg, TREATMENT]:.1f}%",
            ha="center",
            fontsize=9,
        )
    ax.set_xticks(x)
    ax.set_xticklabels([SEGMENT_NAMES[s] for s in SEGMENT_ORDER], rotation=12, ha="right")
    ax.set_ylabel("Premium conversion (%)")
    ax.set_title("Premium conversion by segment × offer arm")
    ax.legend(fontsize=9)
    add_chart_context(
        fig,
        title="Segment-Specific Premium Offers — Conversion by Segment × Arm",
        description="Generic upsell (control) vs segment-specific offer (treatment).",
    )
    return save_chart_report(
        fig,
        out,
        title="Segment-Specific Premium Offers — Conversion by Segment × Arm",
        description_ru="Конверсия в Premium: generic-апселл (control) vs сегментный оффер (treatment).",
        findings=[
            "Сегментные офферы поднимают конверсию во всех gap-сегментах, "
            "но не дотягивают до якоря.",
            "Якорь почти не двигается (+0,9 п.п.): его уже обслуживает generic-оффер.",
            "Остаточный разрыв: 45+ treatment всё ещё в ~4 раза ниже control якоря.",
            "Вывод: фикс работает, но закрывает разрыв лишь частично.",
        ],
        script="scripts/volta_premium_offers.py",
        source="data/volta_premium_offers.csv",
    )


def plot_lift(lift: pd.DataFrame, out: Path) -> Path:
    """Per-segment lift (pp) with 95% CI and the anchor reference line."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(SEGMENT_ORDER))
    colors = [PALETTE[6] if s == ANCHOR_SEGMENT else PALETTE[0] for s in SEGMENT_ORDER]
    ax.bar(x, lift["lift_pp"], color=colors)
    ax.errorbar(
        x, lift["lift_pp"], yerr=1.96 * lift["se_pp"], fmt="none", ecolor="#111827", capsize=4
    )
    ax.axhline(0, color="#111827", linewidth=0.8)
    ax.axhline(
        float(lift.loc[ANCHOR_SEGMENT, "lift_pp"]),
        color="#EF4444",
        linestyle="--",
        linewidth=1.3,
        label="Anchor lift",
    )
    ax.set_xticks(x)
    ax.set_xticklabels([SEGMENT_NAMES[s] for s in SEGMENT_ORDER], rotation=12, ha="right")
    ax.set_ylabel("Lift vs control (pp)")
    ax.set_title("Treatment lift by segment (95% CI)")
    ax.legend(fontsize=9)
    add_chart_context(
        fig,
        title="Segment-Specific Premium Offers — Treatment Lift by Segment",
        description="Absolute lift in premium conversion (pp) with 95% confidence intervals.",
    )
    return save_chart_report(
        fig,
        out,
        title="Segment-Specific Premium Offers — Treatment Lift by Segment",
        description_ru="Абсолютный lift конверсии (п.п.) с 95% доверительными интервалами.",
        findings=[
            "Gap-сегменты дают lift в 3–5 раз больше якоря — сегментный оффер "
            "работает именно там, где generic провалился.",
            "Все gap-lift значимы после Holm-коррекции.",
            "Якорь: lift в пределах шума — generic-оффер ему достаточен.",
            "Сегментный оффер — не «серебряная пуля»: он сужает разрыв, но не убирает его.",
        ],
        script="scripts/volta_premium_offers.py",
        source="data/volta_premium_offers.csv",
    )


# ── Sections ─────────────────────────────────────────────────────────────────
def section_setup(df: pd.DataFrame) -> None:
    print_section("VOLTA NEOBANK — SEGMENT-SPECIFIC PREMIUM OFFERS (A/B)", blank=False)
    print(f"\nDataset shape: {df.shape}")
    print(
        f"Users: {len(df):,} | Segments: {df['jtbd_segment'].nunique()} | Arms: {df['group'].nunique()}"
    )
    print("\nUsers by segment × arm:")
    print(df.groupby(["jtbd_segment", "group"]).size().unstack().to_string())


def section_srm(df: pd.DataFrame) -> None:
    print_section("SAMPLE-RATIO MISMATCH (SRM)")
    srm = srm_check(df)
    print(
        f"\n  Chi-square across segment × arm: chi2={srm['chi2']:.2f}, p={srm['p']:.4f}, dof={srm['dof']}"
    )
    print("  → allocation balanced, no SRM." if srm["p"] >= ALPHA else "  → SRM detected!")
    print_subsection("REQUIRED SAMPLE SIZE (per arm, two-proportion z-test)")
    for seg in SEGMENT_ORDER:
        base = float(conversion_by_segment_arm(df).loc[seg, CONTROL]) / 100
        # Target a 50% relative lift, floored at +1pp, for a comparable yardstick.
        mde = max(base * 0.5, 0.01)
        n = calc_sample_size(base, mde)
        print(
            f"  {SEGMENT_NAMES[seg]:<26} baseline {base * 100:>5.1f}%  MDE +{mde * 100:>4.1f}pp  → n≥{n:,}/arm"
        )


def section_conversion(df: pd.DataFrame) -> None:
    print_section("CONVERSION BY SEGMENT × ARM")
    print("\nPremium conversion (%):")
    print(conversion_by_segment_arm(df).to_string())


def section_lift(lift: pd.DataFrame) -> None:
    print_section("TREATMENT LIFT BY SEGMENT")
    display = lift.copy()
    display.index = [SEGMENT_NAMES[s] for s in display.index]
    print(display.round(3).to_string())
    print_subsection("MULTIPLE-TESTING CORRECTION (Holm, m=4)")
    pvals = [float(lift.loc[s, "p"]) for s in SEGMENT_ORDER]
    rejects = holm(pvals)
    for seg, p, rej in zip(SEGMENT_ORDER, pvals, rejects, strict=True):
        print(f"  {SEGMENT_NAMES[seg]:<26} p={p:.2e}  {'significant' if rej else 'ns'}")


def section_interaction(lift: pd.DataFrame) -> None:
    print_section("SEGMENT × ARM INTERACTION (gap lift vs anchor lift)")
    print("\nDifference-in-differences per gap segment:")
    for seg in GAP_SEGMENTS:
        it = interaction_test(lift, seg)
        print(
            f"  {SEGMENT_NAMES[seg]:<26} +{it['diff_pp']:.2f}pp vs anchor "
            f"(z={it['z']:.1f}, p={it['p']:.2e})"
        )
    print_subsection("READING THE TEST")
    print("  The segment-specific offer helps significantly more in the gap")
    print("  segments than in the anchor — evidence the generic offer, not the")
    print("  segment, was the binding constraint.")


def section_residual(df: pd.DataFrame) -> None:
    print_section("RESIDUAL GAP — DOES THE FIX CLOSE IT?")
    print(residual_gap(df).round(2).to_string())
    print_subsection("READING THE TABLE")
    print("  Even with the segment-specific offer, gap segments convert well")
    print("  below the anchor's generic offer — the value-prop gap narrows but")
    print("  does not close.")


def section_business(lift: pd.DataFrame) -> None:
    print_section("BUSINESS IMPACT (per 10,000 treated users)")
    for seg in GAP_SEGMENTS:
        impact = business_impact(float(lift.loc[seg, "lift_pp"]))
        print(
            f"  {SEGMENT_NAMES[seg]:<26} +{impact['incremental_users']:.0f} premium users/yr "
            f"→ €{impact['annual_arpu_eur']:,.0f} annual ARPU"
        )
    print(f"\n  Premium ARPU uplift per user: €{PREMIUM_ARPU_DELTA:.1f}/month.")


def section_conclusion(lift: pd.DataFrame, df: pd.DataFrame) -> None:
    print_section("CONCLUSION: THE FIX WORKS — BUT ONLY PARTIALLY")
    tab = conversion_by_segment_arm(df)
    gap = float(tab.loc[GAP_SEGMENTS[0], TREATMENT])
    anchor = float(tab.loc[ANCHOR_SEGMENT, CONTROL])
    print(f"""
Risk v2 #3 — partially refuted: segment-specific offers DO lift gap conversion.

  • Digital Newcomers 45+: +{lift.loc["digital_newcomers", "lift_pp"]:.2f}pp
    (p={lift.loc["digital_newcomers", "p"]:.2e}); Family Budgeters +
    {lift.loc["family_budgeters", "lift_pp"]:.2f}pp — both significant after Holm.
  • The anchor barely moves (+{lift.loc["young_professionals", "lift_pp"]:.2f}pp) — the
    segment × arm interaction is large and significant.
  • But 45+ treatment ({gap:.1f}%) is still ~{anchor / gap:.1f}× below the anchor's
    generic offer ({anchor:.1f}%): the fix narrows, doesn't close, the gap.

  • Implication: ship segment-specific offers (positive, significant ROI),
    but plan for a persistent gap. The offer lifts the *ceiling* on conversion;
    it does not make the 45+ value proposition equal to the anchor's.
""")


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    setup(float_format="{:.2f}")
    df = load_data()

    section_setup(df)
    section_srm(df)
    section_conversion(df)

    lift = lift_by_segment(df)
    section_lift(lift)
    section_interaction(lift)
    section_residual(df)
    section_business(lift)

    out1 = OUTPUT_DIR / "premium_offers_conversion_by_segment_arm.png"
    plot_conversion(df, out1)
    print(f"\nSaved: {out1.name} (+ .md sidecar)")

    out2 = OUTPUT_DIR / "premium_offers_lift_by_segment.png"
    plot_lift(lift, out2)
    print(f"Saved: {out2.name} (+ .md sidecar)")

    section_conclusion(lift, df)
    print("=" * 70)
    print("Analysis complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
