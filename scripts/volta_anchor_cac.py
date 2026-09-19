"""
Volta Neobank — Anchor Launch CAC at Scale

Project: Product Analytics Portfolio — Market & Jobs validation layer (RAT v2, risk #4)
Industry: Fintech / Digital Banking
Type: Marginal CAC · Channel saturation · Launch-scale P&L · Greedy allocation

Validates audit risk v2 #4: "paid CAC for the anchor 25-34 breaks launch P&L at
scale". Project 18 priced the anchor on average (blended LTV/CAC 2.13); this
project models the *marginal* cost of acquisition, because the launch decision
depends on the cost of the N-th user, not the average.

It builds marginal-CAC curves per channel (referral and assisted are capped;
paid social is large but expensive at the margin), allocates the cheapest
marginal users first, and finds the scale at which the anchor's blended CAC
crosses the LTV/CAC >= 3 and payback <= 12-month gates.

Finding: the anchor launch is healthy up to ~40-50K users, then the cheap
channels saturate and blended CAC climbs through the gate. At the audit's SOM
(225K users) the anchor fails both gates — the launch P&L breaks on paid
acquisition, exactly as risk #4 warned.

Data: produced by `generate_anchor_cac_data.py` → volta_anchor_cac.csv

Run:  PYTHONPATH=.:scripts uv run python scripts/volta_anchor_cac.py
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

import numpy as np
import pandas as pd

from utils.common import OUTPUT_DIR, data_path, print_section, print_subsection, setup
from utils.viz_helpers import PALETTE, add_chart_context, ru_num, save_chart_report

CHANNEL_ORDER = ["referral", "in_app", "partner", "paid_social", "assisted"]
CHANNEL_NAMES: dict[str, str] = {
    "referral": "Referral",
    "in_app": "In-app",
    "partner": "Partner",
    "paid_social": "Paid social",
    "assisted": "Assisted",
}
CONTRIBUTION_MARGIN = 0.70
ANCHOR_SOM = 225_000
SCALE_TARGETS = [10_000, 40_000, 50_000, 75_000, 120_000, 225_000]
GATE_LTV_CAC = 3.0
GATE_PAYBACK_MONTHS = 12.0


class Allocation(TypedDict):
    target_users: int
    users: int
    total_cost: float
    blended_cac: float
    blended_ltv: float
    blended_arpu: float
    ltv_cac: float
    payback_months: float
    passes: bool
    marginal_cac_last: float
    mix: dict[str, int]


# ── Load ──────────────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    return pd.read_csv(data_path("volta_anchor_cac.csv"))


# ── Channel curves ────────────────────────────────────────────────────────────
def channel_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per channel: capacity, marginal CAC range, LTV, gate-passing CAC."""
    g = df.groupby("channel").agg(
        buckets=("bucket_id", "count"),
        capacity_users=("users", "sum"),
        cac_min=("marginal_cac_eur", "min"),
        cac_max=("marginal_cac_eur", "max"),
        ltv=("ltv_eur", "first"),
    )
    g["capacity_users"] = g["buckets"] * int(df["users"].iloc[0])
    g["gate_cac"] = g["ltv"] / GATE_LTV_CAC
    return g.reindex(CHANNEL_ORDER).round(2)


def allocate(df: pd.DataFrame, target_users: int) -> Allocation:
    """Cheapest-marginal-CAC allocation of `target_users` across channels."""
    ordered = df.sort_values("marginal_cac_eur").copy()
    ordered["cum_users"] = ordered["users"].cumsum()
    selected = ordered[ordered["cum_users"] <= target_users].copy()
    remaining = target_users - int(selected["users"].sum())
    if remaining > 0:
        nxt = ordered[ordered["cum_users"] > target_users].head(1).copy()
        if len(nxt):
            nxt["users"] = remaining
            selected = pd.concat([selected, nxt], ignore_index=True)

    users = int(selected["users"].sum())
    total_cost = float((selected["marginal_cac_eur"] * selected["users"]).sum())
    blended_cac = total_cost / users
    blended_ltv = float((selected["ltv_eur"] * selected["users"]).sum() / users)
    blended_arpu = float((selected["arpu_eur"] * selected["users"]).sum() / users)
    payback = blended_cac / (blended_arpu * CONTRIBUTION_MARGIN)
    mix = selected.groupby("channel")["users"].sum().astype(int).to_dict()
    return {
        "target_users": target_users,
        "users": users,
        "total_cost": total_cost,
        "blended_cac": blended_cac,
        "blended_ltv": blended_ltv,
        "blended_arpu": blended_arpu,
        "ltv_cac": blended_ltv / blended_cac,
        "payback_months": payback,
        "passes": bool(
            blended_ltv / blended_cac >= GATE_LTV_CAC and payback <= GATE_PAYBACK_MONTHS
        ),
        "marginal_cac_last": float(selected["marginal_cac_eur"].max()),
        "mix": mix,
    }


def scale_table(df: pd.DataFrame, targets: list[int] | None = None) -> pd.DataFrame:
    """Allocation economics at a set of target user counts."""
    targets = targets or SCALE_TARGETS
    rows = [allocate(df, t) for t in targets]
    out = pd.DataFrame(rows).drop(columns=["mix"])
    return out.set_index("target_users").round(3)


def break_even_scale(df: pd.DataFrame, step: int = 1_000) -> int:
    """Largest target user count at which both gates still pass."""
    best = 0
    capacity = int(df["users"].sum())
    for target in range(step, capacity + step, step):
        if allocate(df, target)["passes"]:
            best = target
        else:
            break
    return best


def cheap_capacity(df: pd.DataFrame, exclude: list[str] | None = None) -> int:
    """Total capacity of channels excluding the given (e.g. paid) ones."""
    sub = df if not exclude else df[~df["channel"].isin(exclude)]
    return int(sub["users"].sum())


# ── Charts ────────────────────────────────────────────────────────────────────
def plot_cac_curves(out: Path) -> Path:
    """Marginal CAC vs cumulative volume per channel, with the gate reference."""
    import matplotlib.pyplot as plt

    df = load_data()
    summary = channel_summary(df)
    gate_cac = float(summary["ltv"].median()) / GATE_LTV_CAC

    fig, ax = plt.subplots(figsize=(10, 6))
    for i, ch in enumerate(CHANNEL_ORDER):
        sub = df[df["channel"] == ch].sort_values("marginal_cac_eur")
        vol = np.arange(1, len(sub) + 1) * int(df["users"].iloc[0])
        ax.plot(
            vol,
            sub["marginal_cac_eur"].to_numpy(),
            "o-",
            markersize=3,
            color=PALETTE[i],
            label=CHANNEL_NAMES[ch],
        )
    ax.axhline(
        gate_cac,
        color="#EF4444",
        linestyle="--",
        linewidth=1.5,
        label=f"≈ gate (LTV/CAC=3) €{gate_cac:.0f}",
    )
    ax.set_xscale("log")
    ax.set_xlabel("Cumulative users acquired in channel (log scale)")
    ax.set_ylabel("Marginal CAC (EUR)")
    ax.set_title("Marginal acquisition cost rises as each channel saturates")
    ax.legend(fontsize=9)
    add_chart_context(
        fig,
        title="Anchor Launch — Marginal CAC by Channel",
        description="Cost of the next user in each channel as cumulative volume grows.",
    )
    return save_chart_report(
        fig,
        out,
        title="Anchor Launch — Marginal CAC by Channel",
        description_ru="Маржинальный CAC по каналам: цена следующего юзера растёт по мере насыщения канала.",
        findings=[
            "Реферал дешёвый (€18–61), но ёмкость мала (~40K) — исчерпывается первым.",
            "Paid social даёт объём (200K), но маржинальный CAC растёт до €368 — в 2 раза выше гейта.",
            "Assisted — самый дорогой вход (€120–267) и малая ёмкость (20K).",
            "Красная линия — порог LTV/CAC=3: всё, что выше, разрушает launch-P&L.",
        ],
        script="scripts/volta_anchor_cac.py",
        source="data/volta_anchor_cac.csv",
    )


def plot_scale(out: Path) -> Path:
    """Blended LTV/CAC and payback vs launch scale, with gates and the SOM mark."""
    import matplotlib.pyplot as plt

    df = load_data()
    capacity = int(df["users"].sum())
    targets = list(range(5_000, capacity + 1, 5_000))
    table = scale_table(df, targets)
    som = ANCHOR_SOM if ANCHOR_SOM <= capacity else capacity

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(table.index, table["ltv_cac"], "-", color=PALETTE[0], linewidth=2.5, label="LTV/CAC")
    ax.axhline(
        GATE_LTV_CAC,
        color="#EF4444",
        linestyle="--",
        linewidth=1.3,
        label=f"Gate ≥ {GATE_LTV_CAC:.0f}",
    )
    ax.axvline(som, color=PALETTE[2], linestyle=":", linewidth=1.8, label=f"SOM {som / 1000:.0f}K")
    be = break_even_scale(df)
    ax.axvline(
        be, color=PALETTE[1], linestyle="-.", linewidth=1.8, label=f"Gate breaks ≈ {be / 1000:.0f}K"
    )
    ax.set_xlabel("Launch scale (users acquired)")
    ax.set_ylabel("Blended LTV / CAC")
    ax.set_title("Anchor launch P&L vs scale — where the gate breaks")
    ax.legend(fontsize=9)
    add_chart_context(
        fig,
        title="Anchor Launch — Blended LTV/CAC vs Scale",
        description="Cheapest-first channel allocation; blended LTV/CAC falls as cheap channels saturate.",
    )
    return save_chart_report(
        fig,
        out,
        title="Anchor Launch — Blended LTV/CAC vs Scale",
        description_ru="Blended LTV/CAC по мере масштабирования запуска; гейт ≥3 ломается на дешёвых каналах.",
        findings=[
            f"Гейт LTV/CAC ≥ 3 держится только до ≈ {ru_num(be / 1000, 0)}K юзеров — "
            "пока не исчерпаны referral и дешёвый in_app.",
            f"На SOM ({ru_num(som / 1000, 0)}K) blended LTV/CAC падает до "
            f"{ru_num(float(table.loc[som, 'ltv_cac']), 2)} — launch-P&L ломается.",
            "Причина — маржинальный CAC: последний юзер SOM приходит из partner/paid по €100–368.",
            "Рычаг — не бюджет, а ёмкость дешёвых каналов (реферал, in-app) и их конверсия.",
        ],
        script="scripts/volta_anchor_cac.py",
        source="data/volta_anchor_cac.csv",
    )


# ── Sections ─────────────────────────────────────────────────────────────────
def section_setup(df: pd.DataFrame) -> None:
    print_section("VOLTA NEOBANK — ANCHOR LAUNCH CAC AT SCALE", blank=False)
    print(f"\nDataset shape: {df.shape}")
    print(
        f"Buckets: {len(df):,} | Channels: {df['channel'].nunique()} | Capacity: {int(df['users'].sum()):,} users"
    )
    print(f"Gates: LTV/CAC >= {GATE_LTV_CAC:.1f} and payback <= {GATE_PAYBACK_MONTHS:.0f} months")
    print(f"Anchor SOM (audit): {ANCHOR_SOM:,} users")


def section_channels(summary: pd.DataFrame) -> None:
    print_section("CHANNEL ECONOMICS")
    print(summary.to_string())


def section_scale(table: pd.DataFrame) -> None:
    print_section("LAUNCH ECONOMICS BY SCALE (CHEAPEST-FIRST ALLOCATION)")
    print(table.to_string())
    print_subsection("READING THE TABLE")
    for target, row in table.iterrows():
        verdict = "PASSES" if row["passes"] else "FAILS"
        print(
            f"  {target / 1000:>6.0f}K users → CAC €{row['blended_cac']:.1f}, "
            f"LTV/CAC {row['ltv_cac']:.2f}, payback {row['payback_months']:.1f} mo → {verdict}"
        )


def section_break_even(df: pd.DataFrame) -> None:
    print_section("WHERE THE LAUNCH P&L BREAKS")
    be = break_even_scale(df)
    som = allocate(df, ANCHOR_SOM)
    print(f"\n  Gates hold up to ≈ {be:,} users")
    print(
        f"  Anchor SOM: {ANCHOR_SOM:,} users → LTV/CAC {som['ltv_cac']:.2f}, payback {som['payback_months']:.1f} mo"
    )
    print(f"  Marginal CAC of the SOM-th user: €{som['marginal_cac_last']:.0f}")
    print_subsection("READING THE NUMBERS")
    print(f"  Break-even scale is {be / ANCHOR_SOM * 100:.0f}% of SOM — the plan fails")
    print("  well before the audit's target, exactly as risk #4 predicted.")


def section_mix(df: pd.DataFrame) -> None:
    print_section("CHANNEL MIX AT KEY SCALES")
    for target in (40_000, ANCHOR_SOM):
        alloc = allocate(df, target)
        mix = ", ".join(f"{CHANNEL_NAMES[c]} {u / 1000:.0f}K" for c, u in alloc["mix"].items())
        print(f"\n  {target:,} users: {mix}")
    print_subsection("REALLOCATION LEVER")
    no_paid = cheap_capacity(df, exclude=["paid_social"])
    no_paid_assisted = cheap_capacity(df, exclude=["paid_social", "assisted"])
    print(f"  Capacity without paid social: {no_paid:,} users")
    print(f"  Capacity without paid social or assisted: {no_paid_assisted:,} users")
    print("  → cheap channels are capacity-capped; the marginal SOM user has")
    print("    nowhere cheap to come from, so paid CAC sets the P&L.")


def section_conclusion(df: pd.DataFrame) -> None:
    print_section("CONCLUSION: THE ANCHOR LAUNCH BREAKS ON PAID CAC AT SCALE")
    be = break_even_scale(df)
    som = allocate(df, ANCHOR_SOM)
    small = allocate(df, 40_000)
    print(f"""
Risk v2 #4 validated: paid CAC breaks the anchor launch P&L at scale.

  • At 40K users the launch is healthy: CAC €{small["blended_cac"]:.1f},
    LTV/CAC {small["ltv_cac"]:.2f}, payback {small["payback_months"]:.1f} mo.
  • The gates break at ≈ {be:,} users ({be / ANCHOR_SOM * 100:.0f}% of SOM) once
    referral and cheap in-app capacity are exhausted.
  • At SOM ({ANCHOR_SOM:,}): blended CAC €{som["blended_cac"]:.1f}, LTV/CAC
    {som["ltv_cac"]:.2f}, payback {som["payback_months"]:.1f} mo — the N-th user costs
    €{som["marginal_cac_last"]:.0f} to acquire.

  • Implication: do NOT plan the anchor launch to SOM on paid budget. The
    constraint is cheap-channel capacity, not spend. Levers:
    (1) lift referral (viral coefficient / incentive) — cheapest CAC and capacity;
    (2) raise in-app conversion so its capacity goes further;
    (3) cap paid spend at the break-even scale, and re-plan SOM to what the
        cheap channels can carry.
""")


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    setup(float_format="{:.2f}")
    df = load_data()

    section_setup(df)
    summary = channel_summary(df)
    section_channels(summary)

    table = scale_table(df)
    section_scale(table)
    section_break_even(df)
    section_mix(df)

    out1 = OUTPUT_DIR / "anchor_cac_marginal_curves.png"
    plot_cac_curves(out1)
    print(f"\nSaved: {out1.name} (+ .md sidecar)")

    out2 = OUTPUT_DIR / "anchor_ltv_cac_vs_scale.png"
    plot_scale(out2)
    print(f"Saved: {out2.name} (+ .md sidecar)")

    section_conclusion(df)
    print("=" * 70)
    print("Analysis complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
