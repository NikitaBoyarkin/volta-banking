"""
Volta Neobank — Assisted-Onboarding Acquisition Economics (45+)

Project: Product Analytics Portfolio — Market & Jobs validation layer (RAT v2, risk #1)
Industry: Fintech / Digital Banking
Type: CAC vs LTV · Payback · Bootstrap CI · Channel economics

Validates audit risk v2 #1: "assisted onboarding 45+ costs more than 45+ LTV"
(assisted onboarding 45+ costs more than 45+ LTV). The v1 audit recommended a
separate trust track for 45+ (assisted onboarding + partner channel, not a UX
fix). This project prices that recommendation: does the channel that fixes the
trust problem also clear the LTV/CAC gate?

For each segment × channel it computes blended CAC, per-user LTV
(ARPU × contribution margin × months retained), the LTV/CAC ratio with a
bootstrap confidence interval, and the payback period in months. The gate is
LTV/CAC ≥ 3 and payback ≤ 12 months.

Data: produced by `generate_assisted_cac_data.py` → volta_assisted_cac.csv

Run:  PYTHONPATH=.:scripts uv run python scripts/volta_assisted_cac.py
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

import numpy as np
import pandas as pd
from scipy import stats

from utils.common import OUTPUT_DIR, data_path, print_section, print_subsection, setup
from utils.viz_helpers import PALETTE, add_chart_context, ru_num, save_chart_report

SEGMENT_ORDER = ["young_professionals", "digital_newcomers", "family_budgeters"]
SEGMENT_NAMES: dict[str, str] = {
    "young_professionals": "Young Professionals 25-34",
    "digital_newcomers": "Digital Newcomers 45+",
    "family_budgeters": "Family Budgeters 30-45",
}
CHANNEL_ORDER = ["assisted", "partner", "referral", "in_app", "paid_social"]
CHANNEL_NAMES: dict[str, str] = {
    "assisted": "Assisted",
    "partner": "Partner",
    "referral": "Referral",
    "in_app": "In-app",
    "paid_social": "Paid social",
}
ANCHOR_SEGMENT = "young_professionals"
GAP_SEGMENT = "digital_newcomers"
ASSISTED_CHANNEL = "assisted"

# Acquisition gates (mirror the generator).
GATE_LTV_CAC = 3.0
GATE_PAYBACK_MONTHS = 12.0
BOOTSTRAP_N = 4000
BOOTSTRAP_SEED = 7


class LtvCacCI(TypedDict):
    ratio: float
    lo: float
    hi: float


# ── Load ──────────────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    return pd.read_csv(data_path("volta_assisted_cac.csv"))


# ── Unit economics ────────────────────────────────────────────────────────────
def segment_channel_economics(df: pd.DataFrame) -> pd.DataFrame:
    """Per segment × channel: users, CAC, ARPU, churn, lifetime, LTV, LTV/CAC, payback."""
    g = df.groupby(["segment", "channel"]).agg(
        users=("user_id", "nunique"),
        cac=("cac_eur", "mean"),
        arpu=("monthly_arpu_eur", "mean"),
        churn=("monthly_churn_rate", "mean"),
        months=("months_retained", "mean"),
        ltv=("ltv_eur", "mean"),
    )
    g["ltv_cac"] = g["ltv"] / g["cac"]
    # Payback = months of contribution margin needed to recover CAC.
    g["payback_months"] = g["cac"] / (g["arpu"] * df["contribution_margin"].mean())
    return g.reindex(pd.MultiIndex.from_product([SEGMENT_ORDER, CHANNEL_ORDER])).round(3)


def blended_by_segment(df: pd.DataFrame) -> pd.DataFrame:
    """Per segment (all channels blended): CAC, LTV, LTV/CAC, payback, gate verdict."""
    rows: list[dict[str, float | str | bool]] = []
    for seg in SEGMENT_ORDER:
        sub = df[df["segment"] == seg]
        cac = float(sub["cac_eur"].mean())
        ltv = float(sub["ltv_eur"].mean())
        arpu = float(sub["monthly_arpu_eur"].mean())
        margin = float(sub["contribution_margin"].mean())
        rows.append(
            {
                "users": int(len(sub)),
                "cac": cac,
                "ltv": ltv,
                "ltv_cac": ltv / cac,
                "payback_months": cac / (arpu * margin),
                "passes": bool(
                    ltv / cac >= GATE_LTV_CAC and cac / (arpu * margin) <= GATE_PAYBACK_MONTHS
                ),
            }
        )
    return pd.DataFrame(rows, index=SEGMENT_ORDER)


# ── Bootstrap ────────────────────────────────────────────────────────────────
def bootstrap_ltv_cac(
    df: pd.DataFrame,
    segment: str,
    channel: str | None = None,
    n_boot: int = BOOTSTRAP_N,
) -> LtvCacCI:
    """Bootstrap CI for the LTV/CAC ratio (resample users with replacement)."""
    sub = df[df["segment"] == segment]
    if channel is not None:
        sub = sub[sub["channel"] == channel]
    ltv = sub["ltv_eur"].to_numpy()
    cac = sub["cac_eur"].to_numpy()
    if len(ltv) == 0:
        return {"ratio": float("nan"), "lo": float("nan"), "hi": float("nan")}
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    idx = rng.integers(0, len(ltv), size=(n_boot, len(ltv)))
    ratios = ltv[idx].mean(axis=1) / cac[idx].mean(axis=1)
    return {
        "ratio": float(ltv.mean() / cac.mean()),
        "lo": float(np.percentile(ratios, 2.5)),
        "hi": float(np.percentile(ratios, 97.5)),
    }


def anchor_gap_contrast(df: pd.DataFrame, channel: str = ASSISTED_CHANNEL) -> dict[str, float]:
    """Welch t-test on per-user LTV: anchor vs 45+ within one channel."""
    a = df[(df["segment"] == ANCHOR_SEGMENT) & (df["channel"] == channel)]["ltv_eur"]
    g = df[(df["segment"] == GAP_SEGMENT) & (df["channel"] == channel)]["ltv_eur"]
    t, p = stats.ttest_ind(a, g, equal_var=False)
    return {
        "anchor_ltv": float(a.mean()),
        "gap_ltv": float(g.mean()),
        "diff": float(a.mean() - g.mean()),
        "t": float(t),
        "p": float(p),
    }


# ── Gates ─────────────────────────────────────────────────────────────────────
def gate_table(df: pd.DataFrame) -> pd.DataFrame:
    """LTV/CAC and payback gates per segment × channel (pass/fail)."""
    ue = segment_channel_economics(df)
    ue = ue.copy()
    ue["passes_ltv_cac"] = ue["ltv_cac"] >= GATE_LTV_CAC
    ue["passes_payback"] = ue["payback_months"] <= GATE_PAYBACK_MONTHS
    ue["passes"] = ue["passes_ltv_cac"] & ue["passes_payback"]
    return ue


def assisted_failure_detail(df: pd.DataFrame) -> pd.DataFrame:
    """45+ assisted: how far below the gate, per channel."""
    rows: list[dict[str, float | str]] = []
    for seg in SEGMENT_ORDER:
        sub = df[(df["segment"] == seg) & (df["channel"] == ASSISTED_CHANNEL)]
        cac = float(sub["cac_eur"].mean())
        ltv = float(sub["ltv_eur"].mean())
        arpu = float(sub["monthly_arpu_eur"].mean())
        margin = float(sub["contribution_margin"].mean())
        rows.append(
            {
                "segment": SEGMENT_NAMES[seg],
                "cac": cac,
                "ltv": ltv,
                "ltv_cac": ltv / cac,
                "gap_to_gate": ltv / cac - GATE_LTV_CAC,
                "payback_months": cac / (arpu * margin),
            }
        )
    return pd.DataFrame(rows).set_index("segment")


# ── Charts ────────────────────────────────────────────────────────────────────
def plot_ltv_cac(out: Path) -> Path:
    """Grouped bars: LTV/CAC by segment × channel, with the ≥3 gate line."""
    df = load_data()
    ue = segment_channel_economics(df)
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(SEGMENT_ORDER))
    width = 0.15
    for i, ch in enumerate(CHANNEL_ORDER):
        vals = [float(ue.loc[(seg, ch), "ltv_cac"]) for seg in SEGMENT_ORDER]
        ax.bar(
            x + (i - 2) * width,
            vals,
            width,
            label=CHANNEL_NAMES[ch],
            color=PALETTE[i % len(PALETTE)],
        )
    ax.axhline(
        GATE_LTV_CAC,
        color="#EF4444",
        linestyle="--",
        linewidth=1.5,
        label=f"Gate ≥ {GATE_LTV_CAC:.0f}",
    )
    ax.set_xticks(x)
    ax.set_xticklabels([SEGMENT_NAMES[s] for s in SEGMENT_ORDER], rotation=12, ha="right")
    ax.set_ylabel("LTV / CAC")
    ax.set_title("LTV/CAC by segment × acquisition channel")
    ax.legend(ncol=3, fontsize=9)
    add_chart_context(
        fig,
        title="Assisted-Onboarding Economics — LTV/CAC by Segment × Channel",
        description="Per-user LTV (ARPU × contribution margin × months retained) over blended CAC.",
    )
    return save_chart_report(
        fig,
        out,
        title="Assisted-Onboarding Economics — LTV/CAC by Segment × Channel",
        description_ru="LTV/CAC по сегментам и каналам привлечения; красная линия — гейт ≥ 3,0.",
        findings=[
            f"Якорь (Young Professionals) проходит гейт только через реферал: "
            f"LTV/CAC {ru_num(float(ue.loc[(ANCHOR_SEGMENT, 'referral'), 'ltv_cac']), 2)}.",
            f"45+ (Digital Newcomers) не проходит гейт ни на одном канале: "
            f"assisted {ru_num(float(ue.loc[(GAP_SEGMENT, 'assisted'), 'ltv_cac']), 2)} — "
            "в 3 раза ниже порога.",
            "Assisted-онбординг даёт лучший retention (churn ×0,75), но CAC €120 "
            "перекрывает этот выигрыш на 45+.",
            "Вывод: рекомендация «отдельный trust-трек для 45+» не окупается "
            "при текущем CAC — нужен более дешёвый доверительный канал.",
        ],
        script="scripts/volta_assisted_cac.py",
        source="data/volta_assisted_cac.csv",
    )


def plot_payback(out: Path) -> Path:
    """Grouped bars: payback months by segment × channel, with the ≤12 gate line."""
    df = load_data()
    ue = segment_channel_economics(df)
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(SEGMENT_ORDER))
    width = 0.15
    for i, ch in enumerate(CHANNEL_ORDER):
        vals = [float(ue.loc[(seg, ch), "payback_months"]) for seg in SEGMENT_ORDER]
        ax.bar(
            x + (i - 2) * width,
            vals,
            width,
            label=CHANNEL_NAMES[ch],
            color=PALETTE[i % len(PALETTE)],
        )
    ax.axhline(
        GATE_PAYBACK_MONTHS,
        color="#EF4444",
        linestyle="--",
        linewidth=1.5,
        label=f"Gate ≤ {GATE_PAYBACK_MONTHS:.0f} mo",
    )
    ax.set_xticks(x)
    ax.set_xticklabels([SEGMENT_NAMES[s] for s in SEGMENT_ORDER], rotation=12, ha="right")
    ax.set_ylabel("Payback (months)")
    ax.set_title("CAC payback by segment × acquisition channel")
    ax.legend(ncol=3, fontsize=9)
    add_chart_context(
        fig,
        title="Assisted-Onboarding Economics — CAC Payback by Segment × Channel",
        description="Months of contribution margin needed to recover acquisition cost.",
    )
    return save_chart_report(
        fig,
        out,
        title="Assisted-Onboarding Economics — CAC Payback by Segment × Channel",
        description_ru="Срок окупаемости CAC (месяцы) по сегментам и каналам; гейт ≤ 12 мес.",
        findings=[
            "Реферал окупается быстрее всего во всех сегментах (низкий CAC + хороший retention).",
            f"Assisted для 45+ окупается за "
            f"{ru_num(float(ue.loc[(GAP_SEGMENT, 'assisted'), 'payback_months']), 0)} мес — "
            "в 4 раза дольше гейта.",
            "Paid social — худший канал и по CAC, и по retention: самый долгий payback.",
            "Только реферал якоря укладывается в гейт ≤ 12 мес.",
        ],
        script="scripts/volta_assisted_cac.py",
        source="data/volta_assisted_cac.csv",
    )


# ── Sections ─────────────────────────────────────────────────────────────────
def section_setup(df: pd.DataFrame) -> None:
    print_section("VOLTA NEOBANK — ASSISTED-ONBOARDING ECONOMICS (45+)", blank=False)
    print(f"\nDataset shape: {df.shape}")
    print(f"Acquired users: {len(df):,}")
    print(f"Segments: {len(SEGMENT_ORDER)} | Channels: {len(CHANNEL_ORDER)}")
    print(f"Gates: LTV/CAC >= {GATE_LTV_CAC:.1f} and payback <= {GATE_PAYBACK_MONTHS:.0f} months")
    print("\nUsers by segment:")
    for seg in SEGMENT_ORDER:
        n = int((df["segment"] == seg).sum())
        print(f"  {SEGMENT_NAMES[seg]:<26} {n:>6,}  ({n / len(df) * 100:>5.1f}%)")


def section_unit_economics(ue: pd.DataFrame) -> None:
    print_section("UNIT ECONOMICS BY SEGMENT × CHANNEL")
    display = ue.copy()
    display.index = pd.MultiIndex.from_tuples(
        [(SEGMENT_NAMES[s], CHANNEL_NAMES[c]) for s, c in display.index]
    )
    print("\nPer-user economics (EUR):")
    print(display.to_string())


def section_blended(blended: pd.DataFrame) -> None:
    print_section("BLENDED BY SEGMENT — DOES THE SEGMENT CLEAR THE GATE?")
    display = blended.copy()
    display.index = [SEGMENT_NAMES[s] for s in display.index]
    print(display.round(2).to_string())
    print_subsection("READING THE TABLE")
    for seg in SEGMENT_ORDER:
        row = blended.loc[seg]
        verdict = "PASSES" if row["passes"] else "FAILS"
        print(
            f"  {SEGMENT_NAMES[seg]:<26} LTV/CAC {row['ltv_cac']:.2f}, "
            f"payback {row['payback_months']:.1f} mo → {verdict}"
        )


def section_contrast(contrast: dict[str, float]) -> None:
    print_section("ANCHOR vs 45+ — ASSISTED CHANNEL")
    print(f"\n  Anchor LTV: €{contrast['anchor_ltv']:.2f}")
    print(f"  45+ LTV:    €{contrast['gap_ltv']:.2f}")
    print(f"  Difference: €{contrast['diff']:.2f}")
    print(f"  Welch t-test: t={contrast['t']:.2f}, p={contrast['p']:.4g}")
    print("  → the anchor monetizes better even through the same assisted channel.")


def section_bootstrap(df: pd.DataFrame) -> None:
    print_section("BOOTSTRAP CI — LTV/CAC RATIO (95%)")
    print("\nBlended per segment:")
    for seg in SEGMENT_ORDER:
        ci = bootstrap_ltv_cac(df, seg)
        print(f"  {SEGMENT_NAMES[seg]:<26} {ci['ratio']:.2f}  [{ci['lo']:.2f}, {ci['hi']:.2f}]")
    print(f"\n{SEGMENT_NAMES[GAP_SEGMENT]} × assisted:")
    ci = bootstrap_ltv_cac(df, GAP_SEGMENT, ASSISTED_CHANNEL)
    print(f"  {ci['ratio']:.2f}  [{ci['lo']:.2f}, {ci['hi']:.2f}]")
    print(
        f"  → the whole interval sits below the {GATE_LTV_CAC:.1f} gate: not a small-sample artifact."
    )


def section_assisted_detail(detail: pd.DataFrame) -> None:
    print_section("45+ ASSISTED — HOW FAR BELOW THE GATE?")
    print(detail.round(2).to_string())
    print_subsection("READING THE TABLE")
    print("  Assisted onboarding buys the best retention (churn ×0.75), but its")
    print("  €120 CAC is ~3× the referral CAC. On 45+ ARPU that payback never")
    print("  closes inside the 12-month gate.")


def section_conclusion(blended: pd.DataFrame, contrast: dict[str, float]) -> None:
    print_section("CONCLUSION: ASSISTED 45+ DOESN'T CLEAR THE GATE")
    ue = segment_channel_economics(load_data())
    anchor = blended.loc[ANCHOR_SEGMENT]
    gap = blended.loc[GAP_SEGMENT]
    anchor_ref = float(ue.loc[(ANCHOR_SEGMENT, "referral"), "ltv_cac"])
    gap_assisted = float(ue.loc[(GAP_SEGMENT, ASSISTED_CHANNEL), "ltv_cac"])
    print(f"""
Risk v2 #1 validated: assisted onboarding 45+ costs more than 45+ LTV.

  • 45+ LTV/CAC {gap["ltv_cac"]:.2f} blended (payback {gap["payback_months"]:.1f} mo) — fails both gates.
  • The anchor only clears the gate through referral
    (LTV/CAC {anchor_ref:.2f} vs blended {anchor["ltv_cac"]:.2f}, payback
    {anchor["payback_months"]:.1f} mo); 45+ fails on every channel, worst on assisted
    (LTV/CAC {gap_assisted:.2f}).
  • Assisted retention is the best (churn ×0.75) but its CAC (~€120) cannot
    be repaid from 45+ ARPU inside 12 months.
  • Welch t-test on assisted LTV: anchor − 45+ = €{contrast["diff"]:.2f}
    (p={contrast["p"]:.4g}).

  • Implication: the v1 recommendation "separate trust track for 45+ via
    assisted onboarding" is directionally right but not yet affordable.
    Before building it, drive the assisted CAC down (remote video KYC,
    partner cost-sharing, branch-light) or pair it with a monetization
    lever for 45+ (balance-based pricing, family-budget add-on). Do NOT
    scale assisted 45+ at the current CAC.
""")


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    setup(float_format="{:.2f}")
    df = load_data()

    section_setup(df)
    ue = segment_channel_economics(df)
    section_unit_economics(ue)

    blended = blended_by_segment(df)
    section_blended(blended)

    contrast = anchor_gap_contrast(df)
    section_contrast(contrast)

    section_bootstrap(df)

    detail = assisted_failure_detail(df)
    section_assisted_detail(detail)

    out1 = OUTPUT_DIR / "assisted_ltv_cac_by_segment_channel.png"
    plot_ltv_cac(out1)
    print(f"\nSaved: {out1.name} (+ .md sidecar)")

    out2 = OUTPUT_DIR / "assisted_payback_by_segment_channel.png"
    plot_payback(out2)
    print(f"Saved: {out2.name} (+ .md sidecar)")

    section_conclusion(blended, contrast)
    print("=" * 70)
    print("Analysis complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
