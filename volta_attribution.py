"""Volta Neobank — Marketing Attribution.

Compares four attribution models across channels on converted customer journeys:
  - First-touch   : 100% credit to the first touchpoint
  - Last-touch    : 100% credit to the converting (last) touchpoint
  - Linear        : equal credit across all touchpoints in the journey
  - Data-driven   : Shapley value, using a set-value function
    v(S) = revenue * min(1, sum of channel influence weights in S)

Run:  uv run python volta_attribution.py
"""

from __future__ import annotations

import math
from itertools import combinations
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from generate_attribution_data import CHANNEL_WEIGHT
from utils.common import OUTPUT_DIR, data_path, print_section, print_subsection, setup


def load_data() -> pd.DataFrame:
    return pd.read_csv(data_path("volta_attribution_journeys.csv"))


def build_journeys(df: pd.DataFrame) -> list[dict[str, Any]]:
    journeys: list[dict[str, Any]] = []
    for _jid, group in df.sort_values("touch_order").groupby("journey_id"):
        journeys.append(
            {
                "channels": group["channel"].tolist(),
                "revenue": float(group["revenue"].iloc[0]),
            }
        )
    return journeys


def _set_value(channels: tuple[str, ...], revenue: float) -> float:
    total = sum(CHANNEL_WEIGHT.get(c, 0.0) for c in channels)
    return revenue * min(1.0, total)


def shapley_credit(channels: list[str], revenue: float) -> dict[str, float]:
    """Shapley value per unique channel for a single journey."""
    uniq = list(dict.fromkeys(channels))
    n = len(uniq)
    credit = dict.fromkeys(uniq, 0.0)
    for i, ch in enumerate(uniq):
        others = [c for j, c in enumerate(uniq) if j != i]
        for k in range(n):
            for subset in combinations(others, k):
                with_i = _set_value(tuple(subset) + (ch,), revenue)
                without_i = _set_value(subset, revenue)
                perm = math.factorial(k) * math.factorial(n - k - 1) / math.factorial(n)
                credit[ch] += perm * (with_i - without_i)
    # Normalize so per-journey Shapley credits sum to the journey revenue,
    # keeping totals comparable with the single-touch / linear models.
    total = sum(credit.values())
    if total > 0:
        credit = {c: v * revenue / total for c, v in credit.items()}
    return credit


def first_touch_credit(journeys: list[dict[str, Any]]) -> dict[str, float]:
    credit: dict[str, float] = {}
    for j in journeys:
        ch = j["channels"][0]
        credit[ch] = credit.get(ch, 0.0) + float(j["revenue"])
    return credit


def last_touch_credit(journeys: list[dict[str, Any]]) -> dict[str, float]:
    credit: dict[str, float] = {}
    for j in journeys:
        ch = j["channels"][-1]
        credit[ch] = credit.get(ch, 0.0) + float(j["revenue"])
    return credit


def linear_credit(journeys: list[dict[str, Any]]) -> dict[str, float]:
    credit: dict[str, float] = {}
    for j in journeys:
        share = float(j["revenue"]) / len(j["channels"])
        for ch in j["channels"]:
            credit[ch] = credit.get(ch, 0.0) + share
    return credit


def shapley_credit_all(journeys: list[dict[str, Any]]) -> dict[str, float]:
    credit: dict[str, float] = {}
    for j in journeys:
        for ch, val in shapley_credit(j["channels"], float(j["revenue"])).items():
            credit[ch] = credit.get(ch, 0.0) + val
    return credit


def build_comparison(journeys: list[dict[str, Any]]) -> pd.DataFrame:
    models = {
        "first_touch": first_touch_credit(journeys),
        "last_touch": last_touch_credit(journeys),
        "linear": linear_credit(journeys),
        "shapley": shapley_credit_all(journeys),
    }
    df = pd.DataFrame(models)
    df["share_pct"] = df.sum(axis=1) / df.sum().sum() * 100
    df = df.sort_values("shapley", ascending=False)
    return df.round(2)


def plot_attribution(comp: pd.DataFrame, out: Path) -> Path:
    x = np.arange(len(comp))
    width = 0.2
    plt.figure(figsize=(10, 6))
    for i, col in enumerate(["first_touch", "last_touch", "linear", "shapley"]):
        plt.bar(x + (i - 1.5) * width, comp[col], width, label=col)
    plt.xticks(x, comp.index, rotation=20, ha="right")
    plt.ylabel("Attributed revenue (EUR)")
    plt.title("Channel Attribution Across Models")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()
    return out


def section_setup(df: pd.DataFrame) -> None:
    print_section("VOLTA NEOBANK — MARKETING ATTRIBUTION")
    print_subsection("Data")
    print(f"  Touchpoints: {len(df):,}")
    print(f"  Journeys:    {df['journey_id'].nunique():,}")
    print(f"  Channels:    {', '.join(sorted(df['channel'].unique()))}")


def section_compare(comp: pd.DataFrame) -> None:
    print_subsection("Attributed Revenue by Model (EUR)")
    print(comp.to_string())
    print("\n  Reading the table:")
    print("    first_touch credits awareness channels; last_touch credits the")
    print("    converter. Shapley spreads credit by marginal contribution, so a")
    print("    high-influence mid-funnel channel (e.g. referral) wins vs naive")
    print("    first/last-touch which overweight the edges.")


def section_insight(comp: pd.DataFrame) -> None:
    print_subsection("Budget Implication")
    top_shapley = comp["shapley"].idxmax()
    top_naive = comp["last_touch"].idxmax()
    print(f"  Shapley top channel:   {top_shapley}")
    print(f"  Last-touch top channel: {top_naive}")
    if top_shapley != top_naive:
        print("  → Single-touch models mis-allocate budget; use Shapley to rebalance.")


def main() -> None:
    setup()
    df = load_data()
    section_setup(df)
    journeys = build_journeys(df)
    comp = build_comparison(journeys)
    section_compare(comp)
    section_insight(comp)
    out = plot_attribution(comp, OUTPUT_DIR / "attribution_models.png")
    print(f"  Saved: {out.name}")

    print("\n" + "=" * 60)
    print("Analysis complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
