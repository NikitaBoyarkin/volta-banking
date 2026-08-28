"""Volta Neobank — Support Experience vs Churn.

Joins the support-ticket ledger with the churn dataset to quantify how the
support experience drives churn: churn rate by ticket volume, by unresolved
tickets, and by CSAT. The ticket ledger is the ground truth behind the
``support_tickets`` feature used in the churn-prediction project.

Run:  uv run python volta_cs_churn.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils.common import OUTPUT_DIR, data_path, print_section, print_subsection, setup


def load_tickets() -> pd.DataFrame:
    df = pd.read_csv(
        data_path("volta_support_tickets.csv"), parse_dates=["created_at", "resolved_at"]
    )
    return df


def load_churn() -> pd.DataFrame:
    df = pd.read_csv(data_path("volta_churn_data.csv"))
    return df


def ticket_features(tickets: pd.DataFrame) -> pd.DataFrame:
    """Per-user ticket aggregates: count, unresolved count, avg CSAT."""
    g = tickets.groupby("user_id").agg(
        n_tickets=("ticket_id", "count"),
        n_unresolved=("status", lambda s: (s != "resolved").sum()),
        avg_csat=("csat_score", "mean"),
    )
    return g


def merge_churn(tickets: pd.DataFrame, churn: pd.DataFrame) -> pd.DataFrame:
    """Left-join ticket aggregates onto the churn set (users without tickets -> 0)."""
    feats = ticket_features(tickets)
    out = churn.merge(feats, left_on="customer_id", right_index=True, how="left")
    out["n_tickets"] = out["n_tickets"].fillna(0).astype(int)
    out["n_unresolved"] = out["n_unresolved"].fillna(0).astype(int)
    return out


def churn_by_ticket_bucket(df: pd.DataFrame) -> pd.DataFrame:
    """Churn rate by ticket-count bucket (0, 1, 2, 3+)."""
    out = df.copy()
    out["bucket"] = np.where(out["n_tickets"] >= 3, "3+", out["n_tickets"].astype(str))
    g = out.groupby("bucket").agg(
        users=("customer_id", "count"),
        churn_rate=("churned", "mean"),
    )
    g["churn_rate"] = (g["churn_rate"] * 100).round(1)
    return g.reindex(["0", "1", "2", "3+"])


def churn_by_unresolved(df: pd.DataFrame) -> pd.DataFrame:
    """Churn rate by unresolved-ticket bucket (0, 1, 2+)."""
    out = df.copy()
    out["bucket"] = np.where(out["n_unresolved"] >= 2, "2+", out["n_unresolved"].astype(str))
    g = out.groupby("bucket").agg(
        users=("customer_id", "count"),
        churn_rate=("churned", "mean"),
    )
    g["churn_rate"] = (g["churn_rate"] * 100).round(1)
    return g.reindex(["0", "1", "2+"])


def churn_by_csat(df: pd.DataFrame) -> pd.DataFrame:
    """Churn rate by CSAT band among users with a rated ticket."""
    rated = df[df["avg_csat"].notna()].copy()
    rated["csat_band"] = pd.cut(
        rated["avg_csat"], bins=[0, 2, 3, 4, 5], labels=["1-2", "3", "4", "5"]
    )
    g = rated.groupby("csat_band", observed=True).agg(
        users=("customer_id", "count"),
        churn_rate=("churned", "mean"),
    )
    g["churn_rate"] = (g["churn_rate"] * 100).round(1)
    return g


def category_mix_by_churn(tickets: pd.DataFrame, churn: pd.DataFrame) -> pd.DataFrame:
    """Ticket category share among churned vs retained users (%)."""
    churned_ids = set(churn.loc[churn["churned"] == 1, "customer_id"])
    t = tickets.copy()
    t["is_churned"] = t["user_id"].isin(churned_ids)
    g = t.groupby(["is_churned", "category"]).size().unstack(fill_value=0)
    g = g.div(g.sum(axis=1), axis=0).round(3) * 100
    return g.rename(index={False: "retained", True: "churned"})


def plot_churn_by_tickets(bucket: pd.DataFrame, out: Path) -> Path:
    plt.figure(figsize=(8, 4.5))
    plt.bar(bucket.index, bucket["churn_rate"], color="#c44e52")
    plt.ylabel("Churn rate (%)")
    plt.title("Churn Rate by Ticket Count")
    for i, v in enumerate(bucket["churn_rate"]):
        plt.text(i, v + 0.3, f"{v:.1f}%", ha="center")
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()
    return out


def section_setup(tickets: pd.DataFrame, churn: pd.DataFrame) -> None:
    print_section("VOLTA NEOBANK — SUPPORT EXPERIENCE VS CHURN")
    print_subsection("Data")
    print(f"  Tickets:        {len(tickets):,}")
    print(f"  Users (churn):  {len(churn):,}")
    print(f"  Overall churn:  {churn['churned'].mean():.1%}")


def section_ticket_volume(bucket: pd.DataFrame) -> None:
    print_subsection("Churn Rate by Ticket Count")
    print(bucket.to_string())


def section_unresolved(bucket: pd.DataFrame) -> None:
    print_subsection("Churn Rate by Unresolved Tickets")
    print(bucket.to_string())


def section_csat(g: pd.DataFrame) -> None:
    print_subsection("Churn Rate by CSAT Band")
    print(g.to_string())


def section_category_mix(mix: pd.DataFrame) -> None:
    print_subsection("Ticket Category Mix: Churned vs Retained")
    print(mix.to_string())


def main() -> None:
    setup()
    tickets = load_tickets()
    churn = load_churn()
    section_setup(tickets, churn)
    merged = merge_churn(tickets, churn)
    by_tickets = churn_by_ticket_bucket(merged)
    section_ticket_volume(by_tickets)
    by_unresolved = churn_by_unresolved(merged)
    section_unresolved(by_unresolved)
    by_csat = churn_by_csat(merged)
    section_csat(by_csat)
    mix = category_mix_by_churn(tickets, churn)
    section_category_mix(mix)
    bar = plot_churn_by_tickets(by_tickets, OUTPUT_DIR / "cs_churn_by_tickets.png")
    print(f"\n  Saved: {bar.name}")

    print("\n" + "=" * 60)
    print("Analysis complete. Review recommendations above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
