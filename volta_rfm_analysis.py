"""Volta Neobank — RFM Customer Segmentation.

Computes Recency / Frequency / Monetary value from the transaction log, scores
each customer 1-5 on each dimension, and assigns them to meaningful lifecycle
segments (Champions, Loyal, Potential, New, At Risk, Lost). Visualizes segment
sizes and the average R/F/M profile per segment.

Run:  uv run python volta_rfm_analysis.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from utils.common import OUTPUT_DIR, data_path, print_section, print_subsection, setup

REF_DATE = pd.Timestamp("2025-12-31")


def load_data() -> pd.DataFrame:
    df = pd.read_csv(data_path("volta_rfm_transactions.csv"), parse_dates=["tx_date"])
    return df


def compute_rfm(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-customer Recency (days), Frequency (count), Monetary (sum)."""
    g = df.groupby("customer_id")["tx_date"].agg(["max", "count"])
    monetary = df.groupby("customer_id")["amount"].sum()
    rfm = pd.DataFrame(
        {
            "recency_days": (REF_DATE - g["max"]).dt.days,
            "frequency": g["count"].astype(int),
            "monetary": monetary,
        }
    )
    return rfm.reset_index()


def score_rfm(rfm: pd.DataFrame) -> pd.DataFrame:
    """Map each dimension to a 1-5 score. Recency is inverted (5 = most recent)."""
    out = rfm.copy()
    out["R"] = pd.qcut(rfm["recency_days"], 5, labels=[5, 4, 3, 2, 1], duplicates="drop").astype(
        int
    )
    out["F"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    out["M"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    return out


def segment_customers(s: pd.DataFrame) -> pd.DataFrame:
    """Assign lifecycle segments from R/F/M scores (>=5 distinct labels)."""
    r, f, m = s["R"], s["F"], s["M"]
    seg = np.select(
        [
            (r >= 4) & (f >= 4) & (m >= 4),
            (f >= 4) & (m >= 4),
            (r == 5) & (f < 3),
            (r >= 4) & (f < 3),
            (r <= 2) & (f >= 3),
            (r <= 2) & (f < 3),
        ],
        ["Champions", "Loyal", "New", "Potential", "At Risk", "Lost"],
        default="Needs Attention",
    )
    out = s.copy()
    out["segment"] = seg
    return out


def segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Segment sizes + average R/F/M (normalized 0-1) for heatmap."""
    norm = df[["R", "F", "M"]].copy()
    norm[["R", "F", "M"]] = norm[["R", "F", "M"]] / 5
    summary = df.assign(**norm[["R", "F", "M"]]).groupby("segment")[["R", "F", "M"]].mean().round(2)
    summary["share"] = (
        df["segment"].value_counts(normalize=True).reindex(summary.index) * 100
    ).round(1)
    return summary


def plot_segment_sizes(summary: pd.DataFrame, out: Path) -> Path:
    plt.figure(figsize=(8, 4.5))
    bars = summary.sort_values("share", ascending=False)
    plt.bar(bars.index, bars["share"], color="#4c72b0")
    plt.ylabel("% of customers")
    plt.title("RFM Segment Sizes")
    plt.xticks(rotation=30, ha="right")
    for i, v in enumerate(bars["share"]):
        plt.text(i, v + 0.4, f"{v:.1f}%", ha="center")
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()
    return out


def plot_rfm_heatmap(summary: pd.DataFrame, out: Path) -> Path:
    plt.figure(figsize=(7, 4.5))
    sns.heatmap(
        summary[["R", "F", "M"]],
        annot=True,
        fmt=".2f",
        cmap="YlGnBu",
        cbar_kws={"label": "normalized score (0-1)"},
    )
    plt.title("Average R / F / M by Segment")
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()
    return out


def section_setup(df: pd.DataFrame) -> None:
    print_section("VOLTA NEOBANK — RFM SEGMENTATION")
    print_subsection("Data")
    print(f"  Transactions: {len(df):,}")
    print(f"  Customers:    {df['customer_id'].nunique():,}")
    print(f"  Date range:   {df['tx_date'].min().date()} .. {df['tx_date'].max().date()}")


def section_rfm(rfm: pd.DataFrame) -> None:
    print_subsection("RFM Scores (1-5)")
    print(rfm.head(10).to_string(index=False))
    print(f"\n  Mean: R={rfm['R'].mean():.2f}, F={rfm['F'].mean():.2f}, M={rfm['M'].mean():.2f}")


def section_segments(scored: pd.DataFrame, summary: pd.DataFrame) -> tuple[Path, Path]:
    print_subsection("Segments")
    print(summary.to_string())
    print(f"\n  Distinct segments: {len(summary)}")
    bar = plot_segment_sizes(summary, OUTPUT_DIR / "rfm_segment_sizes.png")
    heat = plot_rfm_heatmap(summary, OUTPUT_DIR / "rfm_heatmap.png")
    print(f"  Saved: {bar.name}, {heat.name}")
    return bar, heat


def section_strategy(summary: pd.DataFrame) -> None:
    print_subsection("Strategy")
    print("  Champions  — retain & upsell premium; ask for referrals.")
    print("  Loyal      — reward frequency; cross-sell adjacent products.")
    print("  Potential  — high intent, low spend; nudge first repeat purchase.")
    print("  New        — activate quickly before they cool off.")
    print("  At Risk    — win back with targeted offers; fix friction.")
    print("  Lost       — low priority; cheap reactivation, else let go.")


def main() -> None:
    setup()
    df = load_data()
    section_setup(df)
    rfm = compute_rfm(df)
    scored = score_rfm(rfm)
    section_rfm(scored)
    segmented = segment_customers(scored)
    summary = segment_summary(segmented)
    section_segments(segmented, summary)
    section_strategy(summary)

    print("\n" + "=" * 60)
    print("Analysis complete. Review recommendations above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
