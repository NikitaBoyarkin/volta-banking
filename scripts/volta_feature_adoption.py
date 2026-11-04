"""
Volta Neobank — From Acquisition Economics to Feature Depth

Project: Product Analytics Portfolio — portfolio audit follow-up (PA-07 / REQ-003)
Industry: Fintech / Digital Banking
Type: Acquisition economics · Referral funnel · Feature adoption depth

Question: is cheap acquisition also deep activation?

Three generated datasets answer three legs of that question, and only three:

* ``data/volta_campaigns.csv`` — campaign-level spend and funnel counts per
  channel. No ``user_id``: it ranks channels by cost per first transaction but
  cannot be joined to users.
* ``data/volta_referrals.csv`` — 15,000 referral invites with terminal status
  (sent → accepted → kyc_completed → first_tx). Referees start at user id 8,000
  and never appear in the event stream, so referral-acquired users' feature
  depth is unmeasurable here.
* ``data/volta_feature_events.csv`` — per-user feature usage across 2025. No
  acquisition-channel column. The only defensible user-level join is referrer
  status: 6,448 of 6,804 referrers do appear in the event stream.

The analysis therefore reports three legs plus one honest null result, rather
than implying a channel → depth cohort the data cannot support.

Finding: referral is the cheapest first transaction by a wide margin
(€1.70 media spend vs €1,004.92 for paid social), but referral participation
does not predict feature depth (Mann-Whitney p = 0.93), and referees are
untracked in the event stream. Depth and persistence are one signal (r = 0.92),
not two.

Data: produced by `generate_campaigns_data.py`, `generate_referrals_data.py`,
and `generate_feature_events_data.py`.

Run:  PYTHONPATH=.:scripts uv run python scripts/volta_feature_adoption.py
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from utils.common import OUTPUT_DIR, data_path, print_section, print_subsection, setup
from utils.viz_helpers import PALETTE, add_chart_context, ru_num, save_chart_report

# ── Definitions ──────────────────────────────────────────────────────────────
# The referral CSV stores a terminal status, not one row per step. A referral
# "reached" a step if its terminal status is at or beyond that step.
REFERRAL_STEPS = ["sent", "accepted", "kyc_completed", "first_tx"]
REFERRAL_LABELS = ["Invite sent", "Accepted", "KYC completed", "First transaction"]

# A user is "breadth-heavy" at 5 of 8 features; "persistent" at 6 of 12 months.
BREADTH_THRESHOLD = 5
N_FEATURES = 8
PERSISTENCE_MONTHS = 6
# Latest quarter of the event window — the recency half of the persistence proxy.
RECENT_QUARTER_START = pd.Timestamp("2025-10-01")


class ReferralFunnel(TypedDict):
    reached: dict[str, int]
    step_conv: list[float]
    e2e_pct: float
    reward_eur: float
    cost_per_first_tx_eur: float


class DepthMetrics(TypedDict):
    n_users: int
    mean_depth: float
    median_depth: float
    share_breadth_pct: float
    median_active_months: float
    share_persistent_pct: float
    share_recent_pct: float
    corr_depth_months: float


class ReferrerComparison(TypedDict):
    n_referrers: int
    n_non_referrers: int
    mean_depth_referrers: float
    mean_depth_non_referrers: float
    median_depth_referrers: float
    median_depth_non_referrers: float
    share_breadth_referrers_pct: float
    share_breadth_non_referrers_pct: float
    p_value: float


# ── Load ──────────────────────────────────────────────────────────────────────
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load the three datasets with their date columns parsed."""
    events = pd.read_csv(data_path("volta_feature_events.csv"), parse_dates=["event_date"])
    referrals = pd.read_csv(data_path("volta_referrals.csv"), parse_dates=["invite_date"])
    campaigns = pd.read_csv(
        data_path("volta_campaigns.csv"), parse_dates=["start_date", "end_date"]
    )
    return events, referrals, campaigns


def _pct(part: float, whole: float) -> float:
    """Percent guard: an empty denominator yields 0.0, never a ZeroDivisionError."""
    return (part / whole * 100) if whole else 0.0


# ── Leg 1: campaign economics ─────────────────────────────────────────────────
def campaign_channel_table(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate campaigns to one row per channel with rates and unit costs.

    Cost columns are NaN where recorded spend is zero (organic channels): the
    generator records no media cost for organic, so its true cost is unknown,
    not €0.
    """
    table = df.groupby("channel").agg(
        campaigns=("campaign_id", "count"),
        spend_eur=("spend_eur", "sum"),
        impressions=("impressions", "sum"),
        clicks=("clicks", "sum"),
        installs=("installs", "sum"),
        kyc=("kyc_completions", "sum"),
        first_tx=("first_tx_count", "sum"),
    )
    table["ctr_pct"] = table["clicks"] / table["impressions"] * 100
    table["install_rate_pct"] = table["installs"] / table["clicks"] * 100
    table["kyc_rate_pct"] = table["kyc"] / table["installs"] * 100
    table["tx_rate_pct"] = table["first_tx"] / table["kyc"] * 100
    table["e2e_pct"] = table["first_tx"] / table["installs"] * 100

    has_spend = table["spend_eur"] > 0
    table["cost_per_install_eur"] = (table["spend_eur"] / table["installs"]).where(has_spend)
    table["cost_per_kyc_eur"] = (table["spend_eur"] / table["kyc"]).where(has_spend)
    table["cost_per_first_tx_eur"] = (table["spend_eur"] / table["first_tx"]).where(has_spend)
    return table


def _eur(value: float) -> str:
    return "n/a" if pd.isna(value) else f"{value:,.2f}"


def campaign_display_table(table: pd.DataFrame) -> pd.DataFrame:
    """Human-readable view of the campaign table, cheapest paid channel first."""
    ordered = table.sort_values("cost_per_first_tx_eur", na_position="last")
    return pd.DataFrame(
        {
            "Campaigns": ordered["campaigns"].astype(int),
            "Spend €": ordered["spend_eur"].map(lambda v: f"{v:,.0f}"),
            "Installs": ordered["installs"].astype(int),
            "KYC": ordered["kyc"].astype(int),
            "First tx": ordered["first_tx"].astype(int),
            "€/install": ordered["cost_per_install_eur"].map(_eur),
            "€/KYC": ordered["cost_per_kyc_eur"].map(_eur),
            "€/first tx": ordered["cost_per_first_tx_eur"].map(_eur),
            "Install→KYC %": ordered["kyc_rate_pct"].map(lambda v: f"{v:.1f}"),
            "KYC→tx %": ordered["tx_rate_pct"].map(lambda v: f"{v:.1f}"),
        }
    )


# ── Leg 2: referral funnel ───────────────────────────────────────────────────
def referral_funnel(df: pd.DataFrame) -> ReferralFunnel:
    """Count referrals reaching each step from the terminal-status field.

    Statuses are mutually exclusive outcomes ("sent" never reached acceptance),
    so "reached step X" means status rank >= X. Monotonicity follows by
    construction; unknown statuses raise instead of silently under-counting.
    """
    rank = {step: i for i, step in enumerate(REFERRAL_STEPS)}
    status_rank = df["status"].map(rank)
    unknown = sorted(df.loc[status_rank.isna(), "status"].unique())
    assert not unknown, f"Unknown referral status: {unknown}"

    reached = {step: int((status_rank >= i).sum()) for i, step in enumerate(REFERRAL_STEPS)}
    step_conv = [100.0] + [
        _pct(reached[b], reached[a])
        for a, b in zip(REFERRAL_STEPS[:-1], REFERRAL_STEPS[1:], strict=True)
    ]
    reward = float(df["reward_eur"].sum())
    return {
        "reached": reached,
        "step_conv": step_conv,
        "e2e_pct": _pct(reached["first_tx"], reached["sent"]),
        "reward_eur": reward,
        "cost_per_first_tx_eur": reward / reached["first_tx"]
        if reached["first_tx"]
        else float("nan"),
    }


def referral_channel_table(df: pd.DataFrame) -> pd.DataFrame:
    """Referral funnel per invite channel (in_app / email / link)."""
    rows: list[dict[str, float | str]] = []
    for channel, sub in df.groupby("channel"):
        funnel = referral_funnel(sub)
        rows.append(
            {
                "channel": str(channel),
                "invites": float(funnel["reached"]["sent"]),
                "first_tx": float(funnel["reached"]["first_tx"]),
                "e2e_pct": funnel["e2e_pct"],
                "reward_eur": funnel["reward_eur"],
                "cost_per_first_tx_eur": funnel["cost_per_first_tx_eur"],
            }
        )
    return pd.DataFrame(rows).set_index("channel").sort_values("e2e_pct", ascending=False)


# ── Leg 3: feature adoption depth ────────────────────────────────────────────
def user_feature_profile(events: pd.DataFrame) -> pd.DataFrame:
    """One row per user: event count, distinct features, active months, recency."""
    months = (
        events.assign(month=events["event_date"].dt.to_period("M"))
        .groupby("user_id")["month"]
        .nunique()
        .rename("active_months")
    )
    profile = events.groupby("user_id").agg(
        events=("event_id", "count"),
        depth=("feature", "nunique"),
        first_event=("event_date", "min"),
        last_event=("event_date", "max"),
    )
    return profile.join(months)


def feature_penetration(events: pd.DataFrame, n_users: int) -> pd.Series:
    """Share of profiled users who touched each feature at least once (%)."""
    return (events.groupby("feature")["user_id"].nunique() / n_users * 100).sort_values()


def depth_metrics(profile: pd.DataFrame) -> DepthMetrics:
    """Breadth and persistence proxies for the profiled user base."""
    return {
        "n_users": int(len(profile)),
        "mean_depth": float(profile["depth"].mean()),
        "median_depth": float(profile["depth"].median()),
        "share_breadth_pct": float((profile["depth"] >= BREADTH_THRESHOLD).mean() * 100),
        "median_active_months": float(profile["active_months"].median()),
        "share_persistent_pct": float(
            (profile["active_months"] >= PERSISTENCE_MONTHS).mean() * 100
        ),
        "share_recent_pct": float((profile["last_event"] >= RECENT_QUARTER_START).mean() * 100),
        "corr_depth_months": float(profile["depth"].corr(profile["active_months"])),
    }


def join_diagnostics(events: pd.DataFrame, referrals: pd.DataFrame) -> dict[str, float | int]:
    """Measure what can and cannot be joined across the three files."""
    event_users = set(events["user_id"].unique())
    referrers = set(referrals["referrer_id"].unique())
    referees = set(referrals["referee_id"].unique())
    return {
        "event_users": len(event_users),
        "referrers": len(referrers),
        "referrers_in_events": len(referrers & event_users),
        "referees": len(referees),
        "referees_in_events": len(referees & event_users),
    }


def referrer_comparison(profile: pd.DataFrame, referrals: pd.DataFrame) -> ReferrerComparison:
    """Compare feature depth of referrers vs everyone else.

    This is an association, not an effect: being a referrer is self-selected and
    the two groups are unequal (6,448 vs 1,135). A Mann-Whitney test avoids
    assuming normality on an 8-level ordinal depth variable.
    """
    referrers = set(referrals["referrer_id"].unique())
    is_referrer = profile.index.isin(referrers)
    ref = profile.loc[is_referrer]
    non = profile.loc[~is_referrer]
    assert len(ref) > 0 and len(non) > 0, "Both comparison groups must be non-empty"
    _, p_value = stats.mannwhitneyu(ref["depth"], non["depth"], alternative="two-sided")
    return {
        "n_referrers": int(len(ref)),
        "n_non_referrers": int(len(non)),
        "mean_depth_referrers": float(ref["depth"].mean()),
        "mean_depth_non_referrers": float(non["depth"].mean()),
        "median_depth_referrers": float(ref["depth"].median()),
        "median_depth_non_referrers": float(non["depth"].median()),
        "share_breadth_referrers_pct": float((ref["depth"] >= BREADTH_THRESHOLD).mean() * 100),
        "share_breadth_non_referrers_pct": float((non["depth"] >= BREADTH_THRESHOLD).mean() * 100),
        "p_value": float(p_value),
    }


# ── Charts ───────────────────────────────────────────────────────────────────
def plot_channel_economics(table: pd.DataFrame, out: Path) -> Path:
    """Left: paid-channel cost per first tx (log). Right: funnel rates by channel."""
    paid = table[table["spend_eur"] > 0].sort_values("cost_per_first_tx_eur")
    ordered = table.sort_values("cost_per_first_tx_eur", na_position="last")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.5))

    colors = [PALETTE[3] if channel == "paid_social" else PALETTE[0] for channel in paid.index]
    ax1.barh(paid.index, paid["cost_per_first_tx_eur"], color=colors)
    ax1.set_xscale("log")
    ax1.set_xlabel("Cost per first transaction, EUR (log scale)")
    ax1.set_title("Paid channels — cost per first transaction")
    for i, value in enumerate(paid["cost_per_first_tx_eur"]):
        ax1.text(value * 1.15, i, f"€{value:,.2f}", va="center", fontsize=9)
    ax1.set_xlim(right=float(paid["cost_per_first_tx_eur"].max()) * 4)

    x = np.arange(len(ordered))
    width = 0.38
    ax2.bar(x - width / 2, ordered["kyc_rate_pct"], width, label="install → KYC", color=PALETTE[0])
    ax2.bar(
        x + width / 2,
        ordered["tx_rate_pct"],
        width,
        label="KYC → first tx",
        color=PALETTE[1],
    )
    ax2.set_xticks(x)
    ax2.set_xticklabels(ordered.index, rotation=20, ha="right")
    ax2.set_ylabel("Conversion %")
    ax2.set_title("Funnel rates by channel")
    ax2.legend(loc="upper right")

    add_chart_context(
        fig,
        title="Acquisition economics — campaigns",
        description="Cost per first transaction and downstream funnel rates by channel.",
    )
    return save_chart_report(
        fig,
        out,
        title="Acquisition economics — campaigns",
        description_ru=(
            "Стоимость первой транзакции по каналам кампаний и конверсия "
            "установка → KYC → первая транзакция."
        ),
        findings=[
            f"Самый дешёвый первый платёж — referral: €{ru_num(float(paid.loc['referral', 'cost_per_first_tx_eur']), 2)} "
            f"медиазатрат; самый дорогой — paid_social: €{ru_num(float(paid.loc['paid_social', 'cost_per_first_tx_eur']), 2)} "
            f"(в {ru_num(float(paid.loc['paid_social', 'cost_per_first_tx_eur']) / float(paid.loc['referral', 'cost_per_first_tx_eur']), 0)} раз дороже).",
            "organic_search идёт с нулевыми записанными расходами: его стоимость — «н/д», "
            "а не €0; генератор не пишет медиазатраты для органика.",
            f"Конверсия install → KYC у referral — {ru_num(float(table.loc['referral', 'kyc_rate_pct']), 1)}%, "
            f"у paid_social — {ru_num(float(table.loc['paid_social', 'kyc_rate_pct']), 1)}%.",
            "Правый график показывает, что дорогой канал проигрывает уже на входе в KYC, "
            "а не только на последнем шаге.",
        ],
        script="scripts/volta_feature_adoption.py",
        source="data/volta_campaigns.csv",
    )


def plot_referral_funnel(funnel: ReferralFunnel, channel_table: pd.DataFrame, out: Path) -> Path:
    """Left: cumulative referral funnel. Right: end-to-end conversion by channel."""
    counts = [funnel["reached"][step] for step in REFERRAL_STEPS]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.5))

    ax1.bar(REFERRAL_LABELS, counts, color=PALETTE[0])
    for i, count in enumerate(counts):
        label = f"{count:,}" if i == 0 else f"{count:,}\n({funnel['step_conv'][i]:.1f}%)"
        ax1.text(i, count + max(counts) * 0.015, label, ha="center", va="bottom", fontsize=9)
    ax1.set_ylim(0, max(counts) * 1.2)
    ax1.set_ylabel("Referrals")
    ax1.set_title("Referral funnel — cumulative reach")
    ax1.tick_params(axis="x", rotation=15)

    ordered = channel_table.sort_values("e2e_pct")
    ax2.barh(ordered.index, ordered["e2e_pct"], color=PALETTE[2])
    ax2.set_xlabel("Invite → first transaction %")
    ax2.set_title("End-to-end conversion by invite channel")
    for i, value in enumerate(ordered["e2e_pct"]):
        ax2.text(value + 0.1, i, f"{value:.1f}%", va="center", fontsize=9)
    ax2.set_xlim(0, float(ordered["e2e_pct"].max()) * 1.25)

    add_chart_context(
        fig,
        title="Referral programme — funnel and channel spread",
        description="Terminal-status funnel across 15,000 invites, and end-to-end conversion per channel.",
    )
    return save_chart_report(
        fig,
        out,
        title="Referral programme — funnel and channel spread",
        description_ru=(
            "Воронка реферальных приглашений по терминальному статусу и "
            "сквозная конверсия по каналу приглашения."
        ),
        findings=[
            f"Из {ru_num(counts[0])} приглашений до первой транзакции доходят "
            f"{ru_num(counts[-1])} — {ru_num(funnel['e2e_pct'], 1)}%.",
            f"Самое узкое место — accepted → KYC: {ru_num(funnel['step_conv'][2], 1)}% "
            f"({ru_num(counts[2])} из {ru_num(counts[1])}).",
            f"Вознаграждение: €{ru_num(funnel['reward_eur'])} на {ru_num(counts[-1])} "
            f"активированных рефералов = €{ru_num(funnel['cost_per_first_tx_eur'], 2)} за первого.",
            f"Разброс между каналами приглашения — "
            f"{ru_num(float(channel_table['e2e_pct'].max() - channel_table['e2e_pct'].min()), 1)} п.п.; "
            "рекомендация по каналу приглашения не обоснована.",
        ],
        script="scripts/volta_feature_adoption.py",
        source="data/volta_referrals.csv",
    )


def plot_feature_depth(
    profile: pd.DataFrame,
    metrics: DepthMetrics,
    comparison: ReferrerComparison,
    out: Path,
) -> Path:
    """Depth distribution, persistence proxy, and the referrer null result."""
    fig, (ax_depth, ax_months, ax_ref) = plt.subplots(1, 3, figsize=(16, 5))

    depth_counts = profile["depth"].value_counts().sort_index()
    ax_depth.bar(depth_counts.index, depth_counts.values, color=PALETTE[0])
    ax_depth.axvline(metrics["median_depth"], color=PALETTE[3], linestyle="--", label="median")
    ax_depth.set_xlabel("Distinct features used (of 8)")
    ax_depth.set_ylabel("Users")
    ax_depth.set_title("Feature breadth")
    ax_depth.set_xticks(range(1, N_FEATURES + 1))
    ax_depth.legend()

    month_counts = profile["active_months"].value_counts().sort_index()
    ax_months.bar(month_counts.index, month_counts.values, color=PALETTE[4])
    ax_months.axvline(
        PERSISTENCE_MONTHS - 0.5,
        color=PALETTE[1],
        linestyle="--",
        label=f"≥{PERSISTENCE_MONTHS} months",
    )
    ax_months.set_xlabel("Active months (of 12)")
    ax_months.set_ylabel("Users")
    ax_months.set_title("Persistence proxy")
    ax_months.legend()

    ref_means = [
        comparison["mean_depth_referrers"],
        comparison["mean_depth_non_referrers"],
    ]
    ax_ref.bar(["referrers", "non-referrers"], ref_means, color=[PALETTE[2], PALETTE[6]])
    ax_ref.set_ylim(0, N_FEATURES)
    ax_ref.set_ylabel("Mean distinct features")
    ax_ref.set_title(f"Depth by referrer status (p = {comparison['p_value']:.2f})")
    for i, value in enumerate(ref_means):
        ax_ref.text(i, value + 0.15, f"{value:.2f}", ha="center", fontsize=9)

    add_chart_context(
        fig,
        title="Feature depth and persistence — 7,583 users",
        description="Breadth of feature use, months active, and the referrer comparison.",
    )
    return save_chart_report(
        fig,
        out,
        title="Feature depth and persistence — 7,583 users",
        description_ru=(
            "Широта использования функций, число активных месяцев и сравнение "
            "рефереров с остальными пользователями."
        ),
        findings=[
            f"Медиана глубины — {ru_num(metrics['median_depth'], 0)} из {N_FEATURES} функций; "
            f"{ru_num(metrics['share_breadth_pct'], 1)}% пользователей используют "
            f"≥{BREADTH_THRESHOLD} функций.",
            f"Медиана активности — {ru_num(metrics['median_active_months'], 0)} месяцев из 12; "
            f"{ru_num(metrics['share_persistent_pct'], 1)}% активны ≥{PERSISTENCE_MONTHS} месяцев, "
            f"{ru_num(metrics['share_recent_pct'], 1)}% — в IV квартале.",
            f"Глубина и число активных месяцев коррелируют (r = "
            f"{ru_num(metrics['corr_depth_months'], 2)}) — это одна метрика вовлечённости, "
            "а не две независимые.",
            f"Рефереры и не-рефереры не различаются по глубине "
            f"({ru_num(comparison['mean_depth_referrers'], 2)} против "
            f"{ru_num(comparison['mean_depth_non_referrers'], 2)}; p = "
            f"{ru_num(comparison['p_value'], 2)}).",
        ],
        script="scripts/volta_feature_adoption.py",
        source="data/volta_feature_events.csv · data/volta_referrals.csv",
    )


# ── Narrative sections ──────────────────────────────────────────────────────
def section_overview(
    events: pd.DataFrame,
    referrals: pd.DataFrame,
    campaigns: pd.DataFrame,
    profile: pd.DataFrame,
) -> None:
    print_section("VOLTA NEOBANK — ACQUISITION ECONOMICS vs FEATURE DEPTH", blank=False)
    print("""
Three generated datasets, one question: is cheap acquisition also deep activation?

  campaigns.csv        campaign-level spend and funnel counts, no user_id
  referrals.csv        invite -> accepted -> KYC -> first transaction
  feature_events.csv   per-user feature usage across 2025
""")
    print(
        f"  feature events : {len(events):>7,} rows · {len(profile):>5,} users · "
        f"{events['event_date'].min():%Y-%m-%d} .. {events['event_date'].max():%Y-%m-%d}"
    )
    print(
        f"  referrals      : {len(referrals):>7,} invites · "
        f"{referrals['invite_date'].min():%Y-%m-%d} .. {referrals['invite_date'].max():%Y-%m-%d}"
    )
    print(
        f"  campaigns      : {len(campaigns):>7,} campaigns · "
        f"{campaigns['start_date'].min():%Y-%m-%d} .. {campaigns['end_date'].max():%Y-%m-%d}"
    )

    print_subsection("WHAT CAN AND CANNOT BE JOINED")
    diag = join_diagnostics(events, referrals)
    print("  • campaigns: campaign-level rows, no user_id — cannot be joined to users.")
    print(
        f"  • referrals: {int(diag['referees']):,} referees start at user id 8,000; "
        f"{int(diag['referees_in_events'])} appear in the event stream."
    )
    print("    → referral-acquired users' feature depth is UNMEASURABLE in this repo.")
    print(
        f"  • referrers: {int(diag['referrers_in_events']):,} of "
        f"{int(diag['referrers']):,} referrers do appear in the event stream."
    )
    print("    → the only defensible user-level join is referrer status ↔ own depth.")
    print("  • feature_events has no acquisition-channel column.")
    print("\n  The analysis is three legs plus one null result, not one joined cohort.")
    print("  It is stated here rather than implied by a chart.")


def section_acquisition(table: pd.DataFrame) -> None:
    print_section("LEG 1 — ACQUISITION ECONOMICS (campaigns)")
    print(campaign_display_table(table).to_string())

    paid = table[table["spend_eur"] > 0].sort_values("cost_per_first_tx_eur")
    cheapest, priciest = paid.index[0], paid.index[-1]
    cheap_cost = float(paid.loc[cheapest, "cost_per_first_tx_eur"])
    price_cost = float(paid.loc[priciest, "cost_per_first_tx_eur"])

    print_subsection("INSIGHT")
    print(f"  Cheapest paid first transaction: {cheapest} at €{cheap_cost:,.2f}.")
    print(
        f"  Most expensive: {priciest} at €{price_cost:,.2f} — "
        f"{price_cost / cheap_cost:,.1f}× the {cheapest} cost."
    )
    print(
        "  organic_search carries zero recorded spend across its "
        f"{int(table.loc['organic_search', 'campaigns'])} campaigns: its cost is"
    )
    print("  n/a, not €0 — the generator records no media cost for organic.")
    print("\n  → Channel choice moves cost per first transaction by three orders of")
    print("    magnitude. That is the acquisition leg; it says nothing yet about how")
    print("    deeply those users engage with the product.")


def section_referrals(
    funnel: ReferralFunnel, channel_table: pd.DataFrame, table: pd.DataFrame
) -> None:
    print_section("LEG 2 — REFERRAL PROGRAMME (referrals)")
    counts = [funnel["reached"][step] for step in REFERRAL_STEPS]
    for _step, label, count, conv in zip(
        REFERRAL_STEPS, REFERRAL_LABELS, counts, funnel["step_conv"], strict=True
    ):
        print(f"  {label:<20} {count:>7,}   step conversion {conv:>5.1f}%")
    print(f"\n  End-to-end invite → first transaction: {funnel['e2e_pct']:.1f}%")
    print(
        f"  Reward spend: €{funnel['reward_eur']:,.0f} across {counts[-1]:,} activated "
        f"referees = €{funnel['cost_per_first_tx_eur']:,.2f} per first transaction."
    )

    print_subsection("BY INVITE CHANNEL")
    display = channel_table.copy()
    display["invites"] = display["invites"].astype(int)
    display["first_tx"] = display["first_tx"].astype(int)
    display["e2e_pct"] = display["e2e_pct"].round(1)
    display["reward_eur"] = display["reward_eur"].round(0)
    display["cost_per_first_tx_eur"] = display["cost_per_first_tx_eur"].round(2)
    print(display.to_string())

    spread = float(channel_table["e2e_pct"].max() - channel_table["e2e_pct"].min())
    print_subsection("HONEST READING")
    print(f"  • The binding step is accepted → KYC at {funnel['step_conv'][2]:.1f}%, not the")
    print(f"    final KYC → first-transaction step at {funnel['step_conv'][3]:.1f}%.")
    print(f"  • Invite channel is nearly flat: {spread:.1f}pp between best and worst.")
    print("    No channel-specific recommendation is defensible from this cut.")
    campaign_referral_cost = float(table.loc["referral", "cost_per_first_tx_eur"])
    print(f"  • Cross-ledger caveat: €{campaign_referral_cost:,.2f} (campaign referral rows)")
    print(
        f"    and €{funnel['cost_per_first_tx_eur']:,.2f} (reward ledger) measure different costs —"
    )
    print("    media spend vs referee bonus. They are not reconcilable, and neither is")
    print("    the same as paid social's cost.")


def section_depth(profile: pd.DataFrame, metrics: DepthMetrics, penetration: pd.Series) -> None:
    print_section("LEG 3 — FEATURE ADOPTION DEPTH (feature_events)")
    distribution = profile["depth"].value_counts().sort_index()
    print("  Distinct features per user:")
    for depth, count in distribution.items():
        bar = "█" * int(round(count / distribution.max() * 40))
        print(f"    {depth:>2} features  {count:>5,}  {bar}")

    print(f"\n  Users: {metrics['n_users']:,}")
    print(
        f"  Mean depth: {metrics['mean_depth']:.2f} / {N_FEATURES}   "
        f"median: {metrics['median_depth']:.0f}"
    )
    print(f"  Users with ≥{BREADTH_THRESHOLD} features: {metrics['share_breadth_pct']:.1f}%")

    print_subsection("PERSISTENCE PROXY (NOT RETENTION)")
    print(f"  Median active months: {metrics['median_active_months']:.0f} of 12")
    print(f"  Active ≥{PERSISTENCE_MONTHS} months: {metrics['share_persistent_pct']:.1f}%")
    print(f"  Last event in Q4 2025: {metrics['share_recent_pct']:.1f}%")
    print("  This is an engagement proxy built from event dates; it is not a")
    print("  cohort retention curve and should not be cited as retention.")

    print_subsection("FEATURE PENETRATION (% OF PROFILED USERS)")
    for feature, share in penetration.items():
        print(f"  {feature:<14} {share:>5.1f}%")

    print_subsection("READING")
    print(f"  • Depth and persistence move together (r = {metrics['corr_depth_months']:.2f}):")
    print("    breadth is an engagement measure, not an independent product axis.")
    print("  • Breadth is not scarce at the top — most users touch five or more features.")
    print(
        f"  • The thinnest feature is {penetration.index[0]} at {penetration.iloc[0]:.1f}%; "
        f"the widest is {penetration.index[-1]} at {penetration.iloc[-1]:.1f}%."
    )


def section_referrer_join(comparison: ReferrerComparison) -> None:
    print_section("THE ONLY DEFENSIBLE JOIN — REFERRERS vs NON-REFERRERS")
    print(f"  Referrers:      {comparison['n_referrers']:>6,}")
    print(f"  Non-referrers:  {comparison['n_non_referrers']:>6,}")
    print("\n  " + "-" * 50)
    print(f"  {'Metric':<28} {'Referrers':>10} {'Others':>10}")
    print("  " + "-" * 50)
    print(
        f"  {'Mean distinct features':<28} "
        f"{comparison['mean_depth_referrers']:>10.3f} "
        f"{comparison['mean_depth_non_referrers']:>10.3f}"
    )
    print(
        f"  {'Median distinct features':<28} "
        f"{comparison['median_depth_referrers']:>10.0f} "
        f"{comparison['median_depth_non_referrers']:>10.0f}"
    )
    print(
        f"  {'Share ≥5 features, %':<28} "
        f"{comparison['share_breadth_referrers_pct']:>10.1f} "
        f"{comparison['share_breadth_non_referrers_pct']:>10.1f}"
    )
    print(f"\n  Mann-Whitney U, two-sided p = {comparison['p_value']:.3f}")

    print_subsection("VERDICT")
    if comparison["p_value"] < 0.05:
        print("  A statistically detectable difference exists between the groups.")
    else:
        print("  No detectable difference. Referral participation does not select for")
        print("  feature depth in this data. Do not use 'is a referrer' as a quality")
        print("  proxy, and do not expect depth-targeted campaigns to grow referrals.")
    print("  Association only: referrer status is self-selected, and 355 referrers")
    print("  fall outside the event stream. Referees themselves are unmeasured.")


def section_conclusion(
    table: pd.DataFrame,
    funnel: ReferralFunnel,
    metrics: DepthMetrics,
    comparison: ReferrerComparison,
    penetration: pd.Series,
) -> None:
    paid = table[table["spend_eur"] > 0].sort_values("cost_per_first_tx_eur")
    cheapest, priciest = paid.index[0], paid.index[-1]
    cheap_cost = float(paid.loc[cheapest, "cost_per_first_tx_eur"])
    price_cost = float(paid.loc[priciest, "cost_per_first_tx_eur"])

    print_section("CONCLUSION")
    print(f"""
  • {cheapest.capitalize()} is the cheapest first transaction by a wide margin:
    €{cheap_cost:,.2f} in campaign spend vs €{price_cost:,.2f} for {priciest}
    ({price_cost / cheap_cost:,.0f}×). The reward ledger's own €{funnel["cost_per_first_tx_eur"]:,.2f}
    per activated referee stays two orders below {priciest}.

  • The referral funnel's binding step is accepted → KYC ({funnel["step_conv"][2]:.1f}%),
    not the final transaction step ({funnel["step_conv"][3]:.1f}%).

  • Depth is not scarce at the top: {metrics["share_breadth_pct"]:.1f}% of users touch
    ≥{BREADTH_THRESHOLD} of {N_FEATURES} features, and median persistence is
    {metrics["median_active_months"]:.0f} of 12 months. The thinnest feature is
    {penetration.index[0]} at {penetration.iloc[0]:.1f}%.

  • The data cannot connect acquisition channel to feature depth: referrers show
    no depth premium (p = {comparison["p_value"]:.2f}) and referees never enter the event
    stream. Any "referral users are deeper" claim is unsupported here.

  Recommendation:
    1. Optimise accepted → KYC in the referral flow — it is the measured loss,
       not the final step.
    2. Instrument referee ids in the event stream before making any
       channel → depth claim; today the path is unobservable.
    3. Do not build a depth-targeting hypothesis on referrer status.
""")


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    setup(float_format="{:.2f}")
    events, referrals, campaigns = load_data()

    profile = user_feature_profile(events)
    metrics = depth_metrics(profile)
    penetration = feature_penetration(events, metrics["n_users"])
    comparison = referrer_comparison(profile, referrals)
    campaign_table = campaign_channel_table(campaigns)
    funnel = referral_funnel(referrals)
    referral_channels = referral_channel_table(referrals)

    section_overview(events, referrals, campaigns, profile)
    section_acquisition(campaign_table)
    section_referrals(funnel, referral_channels, campaign_table)
    section_depth(profile, metrics, penetration)
    section_referrer_join(comparison)

    out1 = OUTPUT_DIR / "feature_adoption_channel_economics.png"
    plot_channel_economics(campaign_table, out1)
    print(f"\nSaved: {out1.name} (+ .md sidecar)")

    out2 = OUTPUT_DIR / "feature_adoption_referral_funnel.png"
    plot_referral_funnel(funnel, referral_channels, out2)
    print(f"Saved: {out2.name} (+ .md sidecar)")

    out3 = OUTPUT_DIR / "feature_adoption_depth.png"
    plot_feature_depth(profile, metrics, comparison, out3)
    print(f"Saved: {out3.name} (+ .md sidecar)")

    section_conclusion(campaign_table, funnel, metrics, comparison, penetration)
    print("=" * 70)
    print("Analysis complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
