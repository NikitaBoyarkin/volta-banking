"""
Volta Neobank — Dormant 45+ Win-Back (Assisted Reactivation)

Project: Product Analytics Portfolio — Market & Jobs validation layer (RAT v2, risk #5)
Industry: Fintech / Digital Banking
Type: Randomized win-back experiment · ROI by intervention · Targeting boundary

Validates audit risk v2 #5: "assisted onboarding actually recovers Dormant 45+
(dormancy is UX, but recovery is unproven)". Project 13 showed dormancy
concentrates in Digital Newcomers 45+ and looks UX-driven; Project 18 showed
assisted *acquisition* doesn't pay back. This project tests assisted
*reactivation* — different economics, because there is no CAC to recover.

Three arms: automated win-back (control), light-touch guided flow (SMS +
in-app + optional callback), and full human-assisted (agent call + simplified
flow), across four dormancy buckets.

Finding: risk #5 is refuted on mechanism — assisted reactivation DOES recover
Dormant 45+ (the recently dormant most strongly), confirming UX was the
barrier. But the ROI boundary is sharp: full human calls never pay back on this
low-ARPU segment, and light-touch only pays back for the 30-90 day dormant.
Target the light touch; reserve humans for high-value escalation.

Data: produced by `generate_dormant_winback_data.py` → volta_dormant_winback.csv

Run:  PYTHONPATH=.:scripts uv run python scripts/volta_dormant_winback.py
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import TypedDict

import numpy as np
import pandas as pd
from scipy import stats

from utils.common import OUTPUT_DIR, data_path, print_section, print_subsection, setup
from utils.viz_helpers import PALETTE, add_chart_context, save_chart_report

DORMANCY_BUCKETS = ["30-60d", "60-90d", "90-180d", "180d+"]
ARMS = ["control", "light_touch", "human"]
ARM_NAMES: dict[str, str] = {
    "control": "Automated (control)",
    "light_touch": "Light-touch assisted",
    "human": "Human-assisted",
}
# Economics (mirror the generator).
COST_PER_ARM: dict[str, float] = {"control": 0.50, "light_touch": 2.50, "human": 11.00}
LTV_REACTIVATED: dict[str, float] = {
    "30-60d": 85.0,
    "60-90d": 75.0,
    "90-180d": 62.0,
    "180d+": 50.0,
}
ALPHA = 0.05
PER_USERS = 10_000
TARGET_ROI = 1.0


class EconoRow(TypedDict):
    bucket: str
    lift_pp: float
    incr_react: float
    recovered_ltv: float
    incr_cost: float
    roi: float


# ── Load ──────────────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    return pd.read_csv(data_path("volta_dormant_winback.csv"))


# ── Reactivation ─────────────────────────────────────────────────────────────
def reactivation_by_arm(df: pd.DataFrame) -> pd.DataFrame:
    """60-day reactivation rate (%) by arm."""
    g = df.groupby("group")["reactivated_60d"].mean().mul(100)
    return g.reindex(ARMS).to_frame("reactivation_pct").round(2)


def reactivation_by_bucket_arm(df: pd.DataFrame) -> pd.DataFrame:
    """Reactivation rate (%) by dormancy bucket × arm."""
    tab = df.pivot_table(
        index="dormancy_bucket", columns="group", values="reactivated_60d", aggfunc="mean"
    ).mul(100)
    return tab.reindex(index=DORMANCY_BUCKETS, columns=ARMS).round(2)


# ── Significance ─────────────────────────────────────────────────────────────
def two_proportion_ztest(n1: int, x1: int, n2: int, x2: int) -> tuple[float, float]:
    """Two-proportion z-test; returns (z, two-sided p)."""
    p1, p2 = x1 / n1, x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return 0.0, 1.0
    z = (p1 - p2) / se
    return float(z), float(2 * (1 - stats.norm.cdf(abs(z))))


def arm_lift(df: pd.DataFrame, arm: str) -> dict[str, float]:
    """Overall lift of an arm vs control, with z and p."""
    t = df[df["group"] == arm]["reactivated_60d"]
    c = df[df["group"] == "control"]["reactivated_60d"]
    z, p = two_proportion_ztest(len(t), int(t.sum()), len(c), int(c.sum()))
    return {
        "arm_rate": float(t.mean() * 100),
        "control_rate": float(c.mean() * 100),
        "lift_pp": float((t.mean() - c.mean()) * 100),
        "z": z,
        "p": p,
    }


def bucket_lift(df: pd.DataFrame, arm: str, bucket: str) -> dict[str, float]:
    """Lift of an arm vs control within one dormancy bucket."""
    t = df[(df["group"] == arm) & (df["dormancy_bucket"] == bucket)]["reactivated_60d"]
    c = df[(df["group"] == "control") & (df["dormancy_bucket"] == bucket)]["reactivated_60d"]
    z, p = two_proportion_ztest(len(t), int(t.sum()), len(c), int(c.sum()))
    return {"lift_pp": float((t.mean() - c.mean()) * 100), "z": z, "p": p}


def holm(pvals: list[float], alpha: float = ALPHA) -> list[bool]:
    """Holm step-down correction."""
    m = len(pvals)
    order = np.argsort(pvals)
    rej = [False] * m
    for rank, idx in enumerate(order):
        if pvals[idx] <= alpha / (m - rank):
            rej[idx] = True
        else:
            break
    return rej


# ── Economics ────────────────────────────────────────────────────────────────
def bucket_economics(df: pd.DataFrame, arm: str, bucket: str) -> EconoRow:
    """ROI of one arm within one bucket, per 10,000 treated users."""
    lift = bucket_lift(df, arm, bucket)["lift_pp"] / 100
    incr_react = lift * PER_USERS
    recovered = incr_react * LTV_REACTIVATED[bucket]
    incr_cost = (COST_PER_ARM[arm] - COST_PER_ARM["control"]) * PER_USERS
    roi = recovered / incr_cost if incr_cost > 0 else float("nan")
    return {
        "bucket": bucket,
        "lift_pp": lift * 100,
        "incr_react": incr_react,
        "recovered_ltv": recovered,
        "incr_cost": incr_cost,
        "roi": roi,
    }


def roi_table(df: pd.DataFrame, arm: str) -> pd.DataFrame:
    """Per-bucket economics for an arm plus an overall row."""
    rows = [bucket_economics(df, arm, b) for b in DORMANCY_BUCKETS]
    table = pd.DataFrame(rows).set_index("bucket")
    total_recovered = float(table["recovered_ltv"].sum())
    total_cost = float(table["incr_cost"].sum())
    overall = {
        "lift_pp": float(arm_lift(df, arm)["lift_pp"]),
        "incr_react": float(table["incr_react"].sum()),
        "recovered_ltv": total_recovered,
        "incr_cost": total_cost,
        "roi": total_recovered / total_cost if total_cost else float("nan"),
    }
    table.loc["overall (equal mix)"] = overall
    return table.round(2)


def break_even_ltv(df: pd.DataFrame, arm: str, bucket: str) -> float:
    """LTV per reactivated user at which the intervention breaks even."""
    lift = bucket_lift(df, arm, bucket)["lift_pp"] / 100
    if lift <= 0:
        return float("inf")
    return float((COST_PER_ARM[arm] - COST_PER_ARM["control"]) / lift)


def targeting_rule(df: pd.DataFrame, arm: str, min_roi: float = TARGET_ROI) -> list[str]:
    """Buckets where the arm clears the ROI gate."""
    out = []
    for bucket in DORMANCY_BUCKETS:
        if bucket_economics(df, arm, bucket)["roi"] >= min_roi:
            out.append(bucket)
    return out


# ── Charts ────────────────────────────────────────────────────────────────────
def plot_reactivation(df: pd.DataFrame, out: Path) -> Path:
    """Grouped bars: reactivation by bucket × arm."""
    import matplotlib.pyplot as plt

    tab = reactivation_by_bucket_arm(df)
    x = np.arange(len(DORMANCY_BUCKETS))
    width = 0.26
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, arm in enumerate(ARMS):
        ax.bar(x + (i - 1) * width, tab[arm], width, label=ARM_NAMES[arm], color=PALETTE[i])
    ax.set_xticks(x)
    ax.set_xticklabels(DORMANCY_BUCKETS)
    ax.set_xlabel("Dormancy depth")
    ax.set_ylabel("60-day reactivation (%)")
    ax.set_title("Dormant 45+ win-back — reactivation by arm × dormancy")
    ax.legend(fontsize=9)
    add_chart_context(
        fig,
        title="Dormant 45+ Win-Back — Reactivation by Arm × Dormancy",
        description="Automated vs light-touch vs human-assisted reactivation at 60 days.",
    )
    return save_chart_report(
        fig,
        out,
        title="Dormant 45+ Win-Back — Reactivation by Arm × Dormancy",
        description_ru="Реактивация (60 дней) по arm × глубине дормантности: автоматический vs light-touch vs human.",
        findings=[
            "Assisted-реактивация работает: human даёт +11.4 п.п. на 30–60 днях против control.",
            "Эффект падает с глубиной дормантности: на 180d+ почти исчезает.",
            "Light-touch даёт ~60% эффекта human за долю цены.",
            "Дормантность 45+ — реально UX-барьер: у человека+упрощённого флоу возврат растёт.",
        ],
        script="scripts/volta_dormant_winback.py",
        source="data/volta_dormant_winback.csv",
    )


def plot_roi(df: pd.DataFrame, out: Path) -> Path:
    """ROI by bucket for light-touch and human, with the ROI=1 gate."""
    import matplotlib.pyplot as plt

    x = np.arange(len(DORMANCY_BUCKETS))
    width = 0.36
    light = [bucket_economics(df, "light_touch", b)["roi"] for b in DORMANCY_BUCKETS]
    human = [bucket_economics(df, "human", b)["roi"] for b in DORMANCY_BUCKETS]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width / 2, light, width, label=ARM_NAMES["light_touch"], color=PALETTE[0])
    ax.bar(x + width / 2, human, width, label=ARM_NAMES["human"], color=PALETTE[2])
    ax.axhline(TARGET_ROI, color="#EF4444", linestyle="--", linewidth=1.5, label="ROI = 1 gate")
    ax.set_xticks(x)
    ax.set_xticklabels(DORMANCY_BUCKETS)
    ax.set_xlabel("Dormancy depth")
    ax.set_ylabel("ROI (recovered LTV / incremental cost)")
    ax.set_title("Win-back ROI by arm × dormancy — where the intervention pays")
    ax.legend(fontsize=9)
    add_chart_context(
        fig,
        title="Dormant 45+ Win-Back — ROI by Arm × Dormancy",
        description="Recovered LTV over incremental intervention cost; ROI=1 is break-even.",
    )
    return save_chart_report(
        fig,
        out,
        title="Dormant 45+ Win-Back — ROI by Arm × Dormancy",
        description_ru="ROI (восстановленный LTV / прирост затрат) по arm × глубине дормантности; ROI=1 — окупаемость.",
        findings=[
            "Human-звонок не окупается ни на одной глубине (ROI < 1) — €11 на юзера слишком дорого.",
            "Light-touch окупается на 30–60d (ROI 2,5) и 60–90d (ROI 1,3), дальше — нет.",
            "Целевой трек: light-touch только на 30–90 дней; глубже — не тратить.",
            "Human — только как эскалация для high-value/high-balance юзеров.",
        ],
        script="scripts/volta_dormant_winback.py",
        source="data/volta_dormant_winback.csv",
    )


# ── Sections ─────────────────────────────────────────────────────────────────
def section_setup(df: pd.DataFrame) -> None:
    print_section("VOLTA NEOBANK — DORMANT 45+ WIN-BACK", blank=False)
    print(f"\nDataset shape: {df.shape}")
    print(f"Users: {len(df):,} | Arms: {len(ARMS)} | Dormancy buckets: {len(DORMANCY_BUCKETS)}")
    print(f"Cost per treated user (EUR): {COST_PER_ARM}")
    print(f"LTV per reactivated user (EUR): {LTV_REACTIVATED}")


def section_reactivation(df: pd.DataFrame) -> None:
    print_section("REACTIVATION BY ARM")
    print(reactivation_by_arm(df).to_string())
    print("\nBy dormancy bucket (%):")
    print(reactivation_by_bucket_arm(df).to_string())


def section_significance(df: pd.DataFrame) -> None:
    print_section("SIGNIFICANCE VS CONTROL")
    print("\nOverall arm lift:")
    for arm in ARMS[1:]:
        r = arm_lift(df, arm)
        print(f"  {ARM_NAMES[arm]:<22} +{r['lift_pp']:.2f}pp  (z={r['z']:.1f}, p={r['p']:.2e})")
    print_subsection("PER-BUCKET LIFT (Holm-corrected)")
    tests = [(arm, b) for arm in ARMS[1:] for b in DORMANCY_BUCKETS]
    pvals = [bucket_lift(df, a, b)["p"] for a, b in tests]
    rejects = holm(pvals)
    for (arm, b), p, rej in zip(tests, pvals, rejects, strict=True):
        lift = bucket_lift(df, arm, b)["lift_pp"]
        print(f"  {ARM_NAMES[arm]:<22} {b:<8} +{lift:>5.2f}pp  p={p:.2e}  {'sig' if rej else 'ns'}")


def section_roi(df: pd.DataFrame) -> None:
    print_section("ECONOMICS — ROI PER 10,000 TREATED USERS")
    for arm in ARMS[1:]:
        print_subsection(
            f"{ARM_NAMES[arm]}  (€{COST_PER_ARM[arm]:.2f}/user vs €{COST_PER_ARM['control']:.2f})"
        )
        print(roi_table(df, arm).to_string())


def section_targeting(df: pd.DataFrame) -> None:
    print_section("TARGETING BOUNDARY")
    for arm in ARMS[1:]:
        buckets = targeting_rule(df, arm)
        answer = ", ".join(buckets) if buckets else "none"
        print(f"  {ARM_NAMES[arm]:<22} ROI >= 1 on: {answer}")
    print_subsection("READING THE RULE")
    print("  Only light-touch on the recently dormant clears the gate. The deeper")
    print("  the dormancy, the lower the reactivation lift and the LTV — so the")
    print("  intervention cost per recovered user rises out of reach.")
    print("\n  Break-even LTV per reactivated user (EUR):")
    for arm in ARMS[1:]:
        parts = []
        for b in DORMANCY_BUCKETS:
            be = break_even_ltv(df, arm, b)
            parts.append(f"{b}: €{be:,.0f}" if np.isfinite(be) else f"{b}: n/a")
        print(f"    {ARM_NAMES[arm]:<22} " + " | ".join(parts))


def section_conclusion(df: pd.DataFrame) -> None:
    print_section("CONCLUSION: THE MECHANISM WORKS — TARGET THE LIGHT TOUCH")
    human = arm_lift(df, "human")
    light = arm_lift(df, "light_touch")
    light_roi = roi_table(df, "light_touch").loc["overall (equal mix)", "roi"]
    human_roi = roi_table(df, "human").loc["overall (equal mix)", "roi"]
    light_targets = targeting_rule(df, "light_touch")
    print(f"""
Risk v2 #5 — refuted on mechanism, refined on economics.

  • Assisted win-back DOES recover Dormant 45+: human +{human["lift_pp"]:.2f}pp,
    light-touch +{light["lift_pp"]:.2f}pp vs control overall (both significant),
    strongest on the recently dormant. UX was the barrier, as Project 13 said.
  • But the ROI boundary is sharp: full human calls lose money at any depth
    (overall ROI {human_roi:.2f}); light-touch clears the gate overall
    (ROI {light_roi:.2f}) and strongly on {", ".join(light_targets)}.
  • The deeper the dormancy, the lower the lift and the LTV — intervention
    cost per recovered user rises out of reach.

  • Implication: run a light-touch assisted win-back targeted at the 30-90 day
    dormant 45+ (SMS + guided in-app flow + optional callback). Reserve the
    human call for high-value / high-balance escalation, not mass rollout.
""")


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    setup(float_format="{:.2f}")
    df = load_data()

    section_setup(df)
    section_reactivation(df)
    section_significance(df)
    section_roi(df)
    section_targeting(df)

    out1 = OUTPUT_DIR / "dormant_winback_reactivation.png"
    plot_reactivation(df, out1)
    print(f"\nSaved: {out1.name} (+ .md sidecar)")

    out2 = OUTPUT_DIR / "dormant_winback_roi.png"
    plot_roi(df, out2)
    print(f"Saved: {out2.name} (+ .md sidecar)")

    section_conclusion(df)
    print("=" * 70)
    print("Analysis complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
