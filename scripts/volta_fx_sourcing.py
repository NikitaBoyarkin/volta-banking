"""
Volta Neobank — FX Sourcing Feasibility (Travelers)

Project: Product Analytics Portfolio — Market & Jobs validation layer (RAT v2, risk #2)
Industry: Fintech / Digital Banking
Type: Supply-side feasibility · Volume curve · Break-even reachability

Validates audit risk v2 #2: "FX cost can't be negotiated to <=0.55%, so
travelers never scale". Project 14 established the break-even FX cost (0.55%
vs the current 1.0%) and the levers — but assumed the price was buyable. This
project tests that assumption against the supply side.

It models liquidity-provider quotes (interbank cost falls log-linearly with
monthly volume; hedging cost falls with commitment term), finds the volume at
which the 0.55% gate becomes reachable, and compares that to the traveler
segment's actual volume today and at the audit's SOM (180K travelers).

Finding: the gate is reachable — but only at SOM scale (~€250-500M/month).
Today's traveler volume (~€2.7M/month) sits two orders of magnitude short, so
risk #2 is a cold-start problem, not an impossibility: scaling travelers
requires a bridge (partner volume aggregation, a paid traveler tier, or
interim spread) until the segment's own volume unlocks the price.

Data: produced by `generate_fx_sourcing_data.py` → volta_fx_sourcing.csv

Run:  PYTHONPATH=.:scripts uv run python scripts/volta_fx_sourcing.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from utils.common import OUTPUT_DIR, data_path, print_section, print_subsection, setup
from utils.viz_helpers import PALETTE, add_chart_context, ru_num, save_chart_report

# Gate from Project 14 (traveler unit economics break-even).
GATE_FX_COST_PCT = 0.55
# Traveler segment scale reference (mirrors the audit / Project 14).
TRAVELER_SOM = 180_000
SAMPLE_USERS = 1000
# Monthly FX volume per traveler (EUR), from the Project 14 dataset.
PER_USER_MONTHLY_FX_EUR = 2729.0

VOLUME_TIERS = [1e6, 2.5e6, 5e6, 1e7, 2.5e7, 5e7, 1e8, 2.5e8, 5e8]
TERM_ORDER = [1, 6, 12]


# ── Load ──────────────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    return pd.read_csv(data_path("volta_fx_sourcing.csv"))


# ── Volume curve ─────────────────────────────────────────────────────────────
def best_cost_by_volume(df: pd.DataFrame) -> pd.Series:
    """Best (lowest) effective cost % achievable at each volume tier."""
    return df.groupby("monthly_volume_eur")["effective_cost_pct"].min().sort_index()


def best_quote_by_volume(df: pd.DataFrame) -> pd.DataFrame:
    """The provider/term that wins each volume tier (lowest effective cost)."""
    idx = df.groupby("monthly_volume_eur")["effective_cost_pct"].idxmin()
    return df.loc[idx].sort_values("monthly_volume_eur").reset_index(drop=True)


def required_volume_for_gate(df: pd.DataFrame, gate: float = GATE_FX_COST_PCT) -> float:
    """Smallest monthly volume (EUR) at which the gate is reachable, interpolated.

    Interpolates log10(volume) vs best effective cost; returns +inf if the gate
    is never reached within the quoted tiers.
    """
    curve = best_cost_by_volume(df)
    volumes = curve.index.to_numpy(dtype=float)
    costs = curve.to_numpy(dtype=float)
    if costs.min() > gate:
        return float("inf")
    # First tier that clears the gate; interpolate between it and the prior one.
    hit = int(np.argmax(costs <= gate))
    if hit == 0:
        return float(volumes[0])
    x = np.log10(volumes[hit - 1 : hit + 1])
    y = costs[hit - 1 : hit + 1]
    slope = (y[1] - y[0]) / (x[1] - x[0])
    x_star = x[0] + (gate - y[0]) / slope
    return float(10**x_star)


def traveler_volume_reference() -> dict[str, float]:
    """Current and SOM monthly FX volume for the traveler segment."""
    current = SAMPLE_USERS * PER_USER_MONTHLY_FX_EUR
    som = TRAVELER_SOM * PER_USER_MONTHLY_FX_EUR
    return {"current": current, "som": som}


def provider_ranking(df: pd.DataFrame, volume: float = 5e7) -> pd.DataFrame:
    """Best effective cost per provider at a reference volume (best term)."""
    sub = df[df["monthly_volume_eur"] == volume]
    best = sub.loc[sub.groupby("provider_name")["effective_cost_pct"].idxmin()]
    return (
        best[
            [
                "provider_name",
                "quoted_cost_pct",
                "hedging_cost_pct",
                "effective_cost_pct",
                "credit_rating",
            ]
        ]
        .set_index("provider_name")
        .sort_values("effective_cost_pct")
    )


def term_effect(df: pd.DataFrame) -> pd.DataFrame:
    """Mean effective cost by commitment term (hedging lever)."""
    g = df.groupby("term_months")["effective_cost_pct"].mean()
    return g.reindex(TERM_ORDER).to_frame("effective_cost_pct").round(3)


# ── Charts ────────────────────────────────────────────────────────────────────
def plot_volume_curve(out: Path) -> Path:
    """Best effective FX cost vs monthly volume, with the gate and references."""
    import matplotlib.pyplot as plt

    df = load_data()
    curve = best_cost_by_volume(df)
    vol = curve.index.to_numpy(dtype=float)
    cost = curve.to_numpy(dtype=float)
    ref = traveler_volume_reference()
    gate_vol = required_volume_for_gate(df)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(vol, cost, "o-", color=PALETTE[0], linewidth=2.5, label="Best effective FX cost")
    ax.axhline(
        GATE_FX_COST_PCT,
        color="#EF4444",
        linestyle="--",
        linewidth=1.5,
        label=f"Break-even gate {GATE_FX_COST_PCT:.2f}%",
    )
    ax.axvline(
        ref["current"],
        color=PALETTE[6],
        linestyle=":",
        linewidth=1.8,
        label=f"Today (~€{ref['current'] / 1e6:.0f}M/mo)",
    )
    ax.axvline(
        ref["som"],
        color=PALETTE[2],
        linestyle=":",
        linewidth=1.8,
        label=f"SOM 180K (~€{ref['som'] / 1e6:.0f}M/mo)",
    )
    if np.isfinite(gate_vol):
        ax.axvline(
            gate_vol,
            color=PALETTE[1],
            linestyle="-.",
            linewidth=1.8,
            label=f"Gate reachable (~€{gate_vol / 1e6:.0f}M/mo)",
        )
    ax.set_xscale("log")
    ax.set_xlabel("Monthly FX volume (EUR, log scale)")
    ax.set_ylabel("Best effective FX cost (%)")
    ax.set_title("FX cost vs volume — where the 0.55% gate becomes reachable")
    ax.legend(fontsize=9)
    add_chart_context(
        fig,
        title="FX Sourcing Feasibility — Cost vs Monthly Volume",
        description="Best provider/term effective cost (interbank + hedging) at each volume tier.",
    )
    return save_chart_report(
        fig,
        out,
        title="FX Sourcing Feasibility — Cost vs Monthly Volume",
        description_ru="Лучшая достижимая цена FX (интербанк + хедж) по объёму; гейт 0,55% из Project 14.",
        findings=[
            f"Гейт 0,55% достижим при объёме ≈ €{ru_num(gate_vol / 1e6, 0)} млн/мес — "
            "это SOM-масштаб (180K путешественников).",
            f"Сегодняшний объём тревел-сегмента (~€{ru_num(ref['current'] / 1e6, 0)} млн/мес) "
            "на два порядка ниже — цена недоступна.",
            "Кривая лог-линейна: каждый порядок объёма даёт ~0,20 п.п. скидки.",
            "Риск v2 #2 — не «невозможно», а cold-start: нужен мост до набора объёма.",
        ],
        script="scripts/volta_fx_sourcing.py",
        source="data/volta_fx_sourcing.csv",
    )


def plot_provider_ranking(out: Path, volume: float = 5e7) -> Path:
    """Provider ranking at a reference volume, split into quoted vs hedging cost."""
    import matplotlib.pyplot as plt

    df = load_data()
    rank = provider_ranking(df, volume)
    fig, ax = plt.subplots(figsize=(10, 6))
    y = np.arange(len(rank))
    ax.barh(y, rank["quoted_cost_pct"], color=PALETTE[0], label="Quoted (interbank)")
    ax.barh(
        y, rank["hedging_cost_pct"], left=rank["quoted_cost_pct"], color=PALETTE[1], label="Hedging"
    )
    ax.axvline(
        GATE_FX_COST_PCT,
        color="#EF4444",
        linestyle="--",
        linewidth=1.5,
        label=f"Gate {GATE_FX_COST_PCT:.2f}%",
    )
    ax.set_yticks(y)
    ax.set_yticklabels(
        [f"{n} ({r})" for n, r in zip(rank.index, rank["credit_rating"], strict=True)]
    )
    ax.invert_yaxis()
    ax.set_xlabel("Effective FX cost (%)")
    ax.set_title(f"Provider ranking at €{volume / 1e6:.0f}M/month (best term)")
    ax.legend(fontsize=9)
    add_chart_context(
        fig,
        title="FX Sourcing Feasibility — Provider Ranking",
        description="Effective cost (quoted + hedging) per provider at a reference monthly volume.",
    )
    return save_chart_report(
        fig,
        out,
        title="FX Sourcing Feasibility — Provider Ranking",
        description_ru="Рейтинг FX-провайдеров по эффективной цене (интербанк + хедж) при €50 млн/мес.",
        findings=[
            "Разброс цен между провайдерами ~0,1–0,2 п.п. — выбор провайдера сравним с объёмной скидкой.",
            "Хедж — существенная часть эффективной цены (до 0,12 п.п. на коротком сроке).",
            "Кредитный рейтинг не монотонен с ценой: Prime Broker A дешевле Global FX Desk при том же классе.",
            "Комбинировать: длинный терм хеджа + лучший по цене провайдер даёт максимум экономии.",
        ],
        script="scripts/volta_fx_sourcing.py",
        source="data/volta_fx_sourcing.csv",
    )


# ── Sections ─────────────────────────────────────────────────────────────────
def section_setup(df: pd.DataFrame) -> None:
    print_section("VOLTA NEOBANK — FX SOURCING FEASIBILITY (TRAVELERS)", blank=False)
    print(f"\nDataset shape: {df.shape}")
    print(
        f"Quotes: {len(df):,} | Providers: {df['provider_name'].nunique()} | Terms: {df['term_months'].nunique()}"
    )
    print(f"Gate: effective FX cost <= {GATE_FX_COST_PCT:.2f}% (Project 14 break-even)")
    print("\nVolume tiers (EUR/month):")
    print("  " + ", ".join(f"{v / 1e6:.1f}M" for v in VOLUME_TIERS))


def section_curve(df: pd.DataFrame) -> None:
    print_section("BEST EFFECTIVE COST BY VOLUME TIER")
    curve = best_cost_by_volume(df)
    print("\nBest effective cost (%):")
    for vol, cost in curve.items():
        flag = "  ← clears gate" if cost <= GATE_FX_COST_PCT else ""
        print(f"  €{vol / 1e6:>7.1f}M  {cost:.3f}%{flag}")
    print_subsection("READING THE TABLE")
    print("  Cost falls ~0.20pp per 10× volume — the gate is a scale problem,")
    print("  not a pricing-impossibility problem.")


def section_required_volume(df: pd.DataFrame) -> None:
    print_section("REQUIRED VOLUME FOR THE GATE")
    gate_vol = required_volume_for_gate(df)
    ref = traveler_volume_reference()
    print(f"\n  Gate reachable at ≈ €{gate_vol / 1e6:,.0f}M/month")
    print(
        f"  Today's traveler volume:  ≈ €{ref['current'] / 1e6:,.1f}M/month  ({SAMPLE_USERS:,} users)"
    )
    print(f"  SOM (180K travelers):     ≈ €{ref['som'] / 1e6:,.0f}M/month")
    print_subsection("READING THE NUMBERS")
    print(f"  Today is {gate_vol / ref['current']:,.0f}× below the gate volume;")
    print(
        f"  SOM (€{ref['som'] / 1e6:,.0f}M) is {ref['som'] / gate_vol:,.1f}× the gate volume — the gate opens at scale."
    )
    print("  → cold-start: you need the volume to afford the price, and the")
    print("    price to justify the volume.")


def section_providers(df: pd.DataFrame) -> None:
    print_section("PROVIDER RANKING (€50M/MONTH, BEST TERM)")
    print(provider_ranking(df).to_string())


def section_term(df: pd.DataFrame) -> None:
    print_section("HEDGING TERM EFFECT")
    print(term_effect(df).to_string())
    print_subsection("READING THE TABLE")
    print("  A 12-month commitment roughly halves hedging cost vs 1-month.")
    print("  Term is the second lever after volume — but it adds commitment risk.")


def section_conclusion(df: pd.DataFrame) -> None:
    print_section("CONCLUSION: THE GATE IS REACHABLE — BUT ONLY AT SOM SCALE")
    gate_vol = required_volume_for_gate(df)
    ref = traveler_volume_reference()
    best = best_quote_by_volume(df).iloc[-1]
    print(f"""
Risk v2 #2 — refined: not "impossible", but a cold-start.

  • Best effective cost at SOM scale (€{ref["som"] / 1e6:,.0f}M/mo) ≈
    {best["effective_cost_pct"]:.2f}% — at/under the 0.55% gate, via
    {best["provider_name"]} at a {best["term_months"]:.0f}-month term.
  • The gate needs ≈ €{gate_vol / 1e6:,.0f}M/month. Today's traveler volume is
    ~€{ref["current"] / 1e6:.1f}M/month — {gate_vol / ref["current"]:,.0f}× short;
    SOM (€{ref["som"] / 1e6:,.0f}M) clears it {ref["som"] / gate_vol:,.1f}×.
  • Two levers move the price: volume (log-linear, ~0.20pp/decade) and
    hedging term (12-mo ≈ halves hedge cost vs 1-mo).

  • Implication: scaling travelers is gated by volume, not by a hard price wall.
    Bridge options until the segment's own volume unlocks the price:
    (1) aggregate volume with a partner / other EUR-origin flows,
    (2) a paid traveler tier that lifts spread toward break-even interim,
    (3) start with the cheap provider + long hedge at SOM launch.
    Do NOT scale travelers assuming the 0.55% price is available today.
""")


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    setup(float_format="{:.2f}")
    df = load_data()

    section_setup(df)
    section_curve(df)
    section_required_volume(df)
    section_providers(df)
    section_term(df)

    out1 = OUTPUT_DIR / "fx_sourcing_volume_curve.png"
    plot_volume_curve(out1)
    print(f"\nSaved: {out1.name} (+ .md sidecar)")

    out2 = OUTPUT_DIR / "fx_sourcing_provider_ranking.png"
    plot_provider_ranking(out2)
    print(f"Saved: {out2.name} (+ .md sidecar)")

    section_conclusion(df)
    print("=" * 70)
    print("Analysis complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
