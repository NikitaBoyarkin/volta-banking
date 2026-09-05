"""
Volta Neobank — Traveler Unit Economics

Project: Product Analytics Portfolio — Market & Jobs layer (Sprint 6, T3)
Industry: Fintech / Digital Banking
Type: Unit economics · Break-even · Sensitivity · Scale projection

Validates audit risk #1: "Юнит-экономика путешественников ломается на
масштабе" (traveler unit economics break at scale). The traveler segment's
core job is "honest rate" multi-currency banking — thin FX spread, no fees.
But FX transactions carry real cost (interbank + hedging), so per-transaction
margin is negative and the loss scales with volume.

Data: produced by `generate_unit_economics_data.py` → volta_unit_economics.csv
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

import numpy as np
import pandas as pd

from utils.common import OUTPUT_DIR, data_path, print_section, print_subsection, setup

SEGMENT_ORDER = [
    "travelers",
    "young_professionals",
    "family_budgeters",
    "digital_newcomers",
    "premium_status",
]
SEGMENT_NAMES: dict[str, str] = {
    "travelers": "Travelers",
    "young_professionals": "Young Professionals",
    "family_budgeters": "Family Budgeters",
    "digital_newcomers": "Digital Newcomers 45+",
    "premium_status": "Premium Status",
}
# Audit SOM for the traveler segment (scale projection).
TRAVELER_SOM = 180_000
# Per-€100 FX transaction economics (mirrors the generator).
FX_SPREAD = 0.004
FX_INTERCHANGE = 0.003
FX_COST = 0.010
FX_OTHER_COST = 0.15  # processing + support


# ── Load ──────────────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    return pd.read_csv(data_path("volta_unit_economics.csv"))


# ── Unit economics ────────────────────────────────────────────────────────────
def segment_unit_economics(df: pd.DataFrame) -> pd.DataFrame:
    """Per-segment: users, tx, avg amount, revenue/cost/margin per tx, margin %."""
    rows: list[dict[str, float | int]] = []
    for seg in SEGMENT_ORDER:
        sub = df[df["segment"] == seg]
        rows.append(
            {
                "users": int(sub["user_id"].nunique()),
                "tx": int(len(sub)),
                "avg_amount": float(sub["amount_eur"].mean()),
                "revenue_per_tx": float(sub["revenue_eur"].mean()),
                "cost_per_tx": float(sub["cost_eur"].mean()),
                "margin_per_tx": float(sub["margin_eur"].mean()),
                "margin_pct": float(sub["margin_eur"].sum() / sub["revenue_eur"].sum() * 100),
            }
        )
    return pd.DataFrame(rows, index=SEGMENT_ORDER)


def traveler_margin_by_type(df: pd.DataFrame) -> pd.DataFrame:
    """Traveler margin per tx by transaction type."""
    trav = df[df["segment"] == "travelers"]
    g = trav.groupby("tx_type")[["amount_eur", "revenue_eur", "cost_eur", "margin_eur"]].mean()
    return g.round(4)


def traveler_fx_share(df: pd.DataFrame) -> float:
    trav = df[df["segment"] == "travelers"]
    return float((trav["tx_type"] == "fx").mean() * 100)


# ── Break-even ────────────────────────────────────────────────────────────────
def break_even_fx_cost() -> float:
    """FX cost % where a €100 FX tx breaks even (spread 0.4%, interchange 0.3%)."""
    amount = 100.0
    revenue = FX_SPREAD * amount + FX_INTERCHANGE * amount
    return (revenue - FX_OTHER_COST) / amount * 100


def break_even_spread() -> float:
    """FX spread % where a €100 FX tx breaks even (FX cost 1.0%)."""
    amount = 100.0
    cost = FX_COST * amount + FX_OTHER_COST
    return (cost - FX_INTERCHANGE * amount) / amount * 100


# ── Sensitivity + scale ──────────────────────────────────────────────────────
class SensitivityRow(TypedDict):
    scenario: str
    value: float
    margin_per_tx: float


def sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    """Blended traveler margin/tx as FX cost and FX spread vary (one at a time)."""
    trav = df[df["segment"] == "travelers"]
    fx_mask = (trav["tx_type"] == "fx").values
    amounts = trav["amount_eur"].values
    base_margin = trav["margin_eur"].values
    fx_amounts = amounts[fx_mask]
    fx_interchange = FX_INTERCHANGE * fx_amounts

    rows: list[SensitivityRow] = []
    for c in np.arange(0.004, 0.015, 0.001):
        m = base_margin.copy()
        m[fx_mask] = fx_interchange + FX_SPREAD * fx_amounts - (c * fx_amounts + FX_OTHER_COST)
        rows.append(
            {
                "scenario": "fx_cost",
                "value": round(float(c * 100), 1),
                "margin_per_tx": float(m.mean()),
            }
        )
    for s in np.arange(0.002, 0.011, 0.001):
        m = base_margin.copy()
        m[fx_mask] = s * fx_amounts + fx_interchange - (FX_COST * fx_amounts + FX_OTHER_COST)
        rows.append(
            {
                "scenario": "fx_spread",
                "value": round(float(s * 100), 1),
                "margin_per_tx": float(m.mean()),
            }
        )
    return pd.DataFrame(rows)


def scale_projection(df: pd.DataFrame) -> dict[str, float]:
    """Traveler monthly P&L at the audit's SOM (180K travelers)."""
    trav = df[df["segment"] == "travelers"]
    margin_per_user_month = float(trav["margin_eur"].sum() / trav["user_id"].nunique())
    monthly_pnl = margin_per_user_month * TRAVELER_SOM
    return {
        "margin_per_user_month": margin_per_user_month,
        "som": float(TRAVELER_SOM),
        "monthly_pnl": monthly_pnl,
    }


def plot_sensitivity(sens: pd.DataFrame, out: Path) -> Path:
    """Sensitivity PNG: blended traveler margin vs FX cost and FX spread."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(9, 6))
    for scenario, label in [("fx_cost", "FX cost %"), ("fx_spread", "FX spread %")]:
        sub = sens[sens["scenario"] == scenario]
        ax.plot(sub["value"], sub["margin_per_tx"], "o-", label=label)
    ax.axhline(0, color="white", linestyle="--", alpha=0.7, label="Break-even")
    ax.set_xlabel("Rate (%)")
    ax.set_ylabel("Blended margin per traveler tx (€)")
    ax.set_title("Traveler Unit Economics — Sensitivity to FX cost & spread")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


# ── Sections ─────────────────────────────────────────────────────────────────
def section_setup(df: pd.DataFrame) -> None:
    print_section("VOLTA NEOBANK — TRAVELER UNIT ECONOMICS", blank=False)
    print(f"\nDataset shape: {df.shape}")
    print(f"Transactions: {len(df):,}")
    print(f"Users: {df['user_id'].nunique():,}")
    print("\nSegment transaction mix:")
    for seg in SEGMENT_ORDER:
        n = int((df["segment"] == seg).sum())
        print(f"  {SEGMENT_NAMES[seg]:<24} {n:>6,} tx  ({n / len(df) * 100:>5.1f}%)")


def section_unit_economics(ue: pd.DataFrame) -> None:
    print_section("UNIT ECONOMICS BY SEGMENT")
    display = ue.rename(index=SEGMENT_NAMES).round(4)
    print("\nPer-transaction economics (EUR):")
    print(display.to_string())
    print_subsection("KEY CONTRAST")
    trav = ue.loc["travelers", "margin_per_tx"]
    others = ue.loc[
        ["young_professionals", "family_budgeters", "digital_newcomers", "premium_status"],
        "margin_per_tx",
    ]
    print(f"  Travelers: {trav:+.4f} €/tx  ← negative")
    print(f"  Other segments: {others.min():+.4f} to {others.max():+.4f} €/tx  ← positive")
    print("  → Travelers lose money per transaction; everyone else is profitable.")


def section_traveler_deep_dive(margin_by_type: pd.DataFrame, fx_share: float) -> None:
    print_section("TRAVELER DEEP-DIVE: WHERE THE LOSS COMES FROM")
    print(f"\nFX share of traveler volume: {fx_share:.0f}%")
    print("\nMargin per tx by type:")
    print(margin_by_type.to_string())
    print_subsection("READING THE TABLE")
    print("  fx:  thin spread (0.4%) + interchange (0.3%) vs FX cost (1.0%) → negative")
    print("  atm: free for travelers (job: no fees) but network cost €0.80 → negative")
    print("  card/transfer: positive, but a small share of traveler volume")


def section_break_even() -> None:
    print_section("BREAK-EVEN ANALYSIS (per €100 FX transaction)")
    be_cost = break_even_fx_cost()
    be_spread = break_even_spread()
    print(
        f"\n  Current FX cost:   1.0%  → break-even at {be_cost:.2f}%  (need −{1.0 - be_cost:.2f}pp)"
    )
    print(
        f"  Current FX spread: 0.4%  → break-even at {be_spread:.2f}%  (need +{be_spread - 0.4:.2f}pp)"
    )
    print_subsection("WHICH LEVER IS REALISTIC?")
    print("  The traveler's core job is 'honest rate' — raising the spread to 0.85%")
    print("  (2.1× current) breaks the value proposition. The lever is FX cost:")
    print("  negotiate interbank rates / hedge, not the customer-facing spread.")


def section_sensitivity(sens: pd.DataFrame, out: Path) -> None:
    print_section("SENSITIVITY: MARGIN VS FX COST & SPREAD")
    print("\nBlended traveler margin/tx (€):")
    print(
        sens.pivot(index="value", columns="scenario", values="margin_per_tx").round(4).to_string()
    )
    plot_sensitivity(sens, out)
    print(f"\nSaved: {out.name}")
    print("  fx_cost line crosses zero at ~0.55% (achievable — negotiate rates).")
    print("  fx_spread line crosses zero at ~0.85% (2.1× current — breaks honest-rate job).")


def section_scale(proj: dict[str, float]) -> None:
    print_section("SCALE PROJECTION: TRAVELER P&L AT SOM")
    print(f"\n  Margin per traveler / month: €{proj['margin_per_user_month']:.2f}")
    print(f"  SOM (audit): {proj['som']:,.0f} travelers")
    print(f"  Monthly P&L at SOM: €{proj['monthly_pnl']:,.0f}")
    print(f"  Annual P&L at SOM: €{proj['monthly_pnl'] * 12:,.0f}")
    print("\n  → The loss scales with volume. Scaling travelers without fixing")
    print("    unit economics multiplies the loss, not the profit.")


def section_conclusion() -> None:
    print_section("CONCLUSION: DON'T SCALE TRAVELERS WITHOUT FIXING UNIT ECONOMICS")
    print("""
Risk #1 validated: traveler unit economics break at scale.

  • Travelers lose money per transaction (blended) — high volume, thin FX
    spread ("honest rate" job), real FX cost.
  • Break-even: FX cost must fall from 1.0% to 0.55% (or spread rise to
    0.85% — but that breaks the honest-rate job).
  • At SOM (180K travelers) the segment runs a negative monthly P&L.
  • Implication: do NOT scale travelers without fixing unit economics.
    Levers: negotiate interbank FX cost, hedge, volume-based fee, or a
    premium tier for travelers.

Next step (audit risk #2): premium upsell — does it transfer to new segments?
""")


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    setup(float_format="{:.2f}")
    df = load_data()

    section_setup(df)
    ue = segment_unit_economics(df)
    section_unit_economics(ue)

    margin_by_type = traveler_margin_by_type(df)
    fx_share = traveler_fx_share(df)
    section_traveler_deep_dive(margin_by_type, fx_share)

    section_break_even()

    sens = sensitivity(df)
    out = OUTPUT_DIR / "traveler_unit_economics_sensitivity.png"
    section_sensitivity(sens, out)

    proj = scale_projection(df)
    section_scale(proj)

    section_conclusion()
    print("=" * 70)
    print("Analysis complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
