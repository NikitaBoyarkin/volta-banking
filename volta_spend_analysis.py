"""Volta Neobank — Transaction Spend Analysis.

Breaks down the transaction ledger by category, channel, merchant and status:
where money flows, which merchants concentrate spend, and where declines
cluster. Complements the RFM project (who spends) with the what/where/why of
spending.

Run:  uv run python volta_spend_analysis.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from utils.common import OUTPUT_DIR, data_path, print_section, print_subsection, setup

TOP_MERCHANTS = 10


def load_data() -> pd.DataFrame:
    df = pd.read_csv(data_path("volta_transactions.csv"), parse_dates=["tx_date"])
    return df


def spend_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Total spend, tx count and avg amount per category."""
    g = df.groupby("category").agg(
        total_eur=("amount_eur", "sum"),
        tx_count=("amount_eur", "count"),
        avg_eur=("amount_eur", "mean"),
    )
    g["share_pct"] = (g["total_eur"] / g["total_eur"].sum() * 100).round(1)
    return g.sort_values("total_eur", ascending=False).round(2)


def spend_by_channel(df: pd.DataFrame) -> pd.DataFrame:
    """Total spend and tx count per channel."""
    g = df.groupby("channel").agg(
        total_eur=("amount_eur", "sum"),
        tx_count=("amount_eur", "count"),
    )
    g["share_pct"] = (g["total_eur"] / g["total_eur"].sum() * 100).round(1)
    return g.sort_values("total_eur", ascending=False).round(2)


def top_merchants(df: pd.DataFrame) -> pd.DataFrame:
    """Top merchants by total spend."""
    g = df.groupby("merchant").agg(
        total_eur=("amount_eur", "sum"),
        tx_count=("amount_eur", "count"),
    )
    return g.sort_values("total_eur", ascending=False).head(TOP_MERCHANTS).round(2)


def declined_by_category(df: pd.DataFrame) -> pd.Series:
    """Decline rate per category (declined / all tx in that category)."""
    declined = df[df["status"] == "declined"]
    rate = declined.groupby("category").size() / df.groupby("category").size()
    return rate.sort_values(ascending=False).round(3).rename("decline_rate")


def monthly_spend(df: pd.DataFrame) -> pd.Series:
    """Monthly total spend series (completed tx only)."""
    completed = df[df["status"] == "completed"]
    return completed.set_index("tx_date")["amount_eur"].resample("ME").sum().rename("monthly_eur")


def plot_category_spend(cat: pd.DataFrame, out: Path) -> Path:
    plt.figure(figsize=(8, 4.5))
    plt.bar(cat.index, cat["total_eur"], color="#4c72b0")
    plt.ylabel("Total spend (EUR)")
    plt.title("Spend by Category")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()
    return out


def plot_monthly_trend(monthly: pd.Series, out: Path) -> Path:
    plt.figure(figsize=(8, 4.5))
    plt.plot(monthly.index, monthly.values, marker="o", color="#55a868")
    plt.ylabel("Spend (EUR)")
    plt.title("Monthly Spend Trend")
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()
    return out


def section_setup(df: pd.DataFrame) -> None:
    print_section("VOLTA NEOBANK — SPEND ANALYSIS")
    print_subsection("Data")
    print(f"  Transactions: {len(df):,}")
    print(f"  Users:        {df['user_id'].nunique():,}")
    print(f"  Date range:   {df['tx_date'].min().date()} .. {df['tx_date'].max().date()}")
    print(f"  Total spend:  EUR {df['amount_eur'].sum():,.0f}")


def section_categories(cat: pd.DataFrame) -> None:
    print_subsection("Spend by Category")
    print(cat.to_string())
    print(f"\n  Top category: {cat.index[0]} ({cat['share_pct'].iloc[0]}% of spend)")


def section_channels(ch: pd.DataFrame) -> None:
    print_subsection("Spend by Channel")
    print(ch.to_string())


def section_merchants(merch: pd.DataFrame) -> None:
    print_subsection(f"Top {TOP_MERCHANTS} Merchants")
    print(merch.to_string())


def section_declined(rate: pd.Series) -> None:
    print_subsection("Decline Rate by Category")
    print(rate.to_string())
    print(f"\n  Highest decline: {rate.index[0]} ({rate.iloc[0]:.1%})")


def section_trend(monthly: pd.Series) -> None:
    print_subsection("Monthly Spend Trend")
    print(monthly.to_string())
    print(f"\n  Peak month: {monthly.idxmax().date()} (EUR {monthly.max():,.0f})")


def main() -> None:
    setup()
    df = load_data()
    section_setup(df)
    cat = spend_by_category(df)
    section_categories(cat)
    ch = spend_by_channel(df)
    section_channels(ch)
    merch = top_merchants(df)
    section_merchants(merch)
    rate = declined_by_category(df)
    section_declined(rate)
    monthly = monthly_spend(df)
    section_trend(monthly)
    bar = plot_category_spend(cat, OUTPUT_DIR / "spend_by_category.png")
    line = plot_monthly_trend(monthly, OUTPUT_DIR / "spend_monthly_trend.png")
    print(f"\n  Saved: {bar.name}, {line.name}")

    print("\n" + "=" * 60)
    print("Analysis complete. Review recommendations above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
