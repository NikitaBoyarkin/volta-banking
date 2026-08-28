"""Volta Neobank — NPS Trends & Drivers.

Tracks Net Promoter Score over time and by driver: monthly NPS, promoter /
passive / detractor mix, and which drivers push the score. Complements the
retention project — NPS is the voice-of-customer leading indicator behind the
cohort retention curves.

Run:  uv run python volta_nps_trends.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from utils.common import OUTPUT_DIR, data_path, print_section, print_subsection, setup


def load_data() -> pd.DataFrame:
    df = pd.read_csv(data_path("volta_nps_surveys.csv"), parse_dates=["survey_date"])
    return df


def nps_score(df: pd.DataFrame) -> float:
    """NPS = %promoters - %detractors (0-100 scale)."""
    promoters = (df["nps_score"] >= 9).mean()
    detractors = (df["nps_score"] <= 6).mean()
    return (promoters - detractors) * 100


def monthly_nps(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly NPS + response count, indexed by 'YYYY-MM'."""
    out = df.copy()
    out["month"] = out["survey_date"].dt.to_period("M").astype(str)
    rows = [
        {"month": month, "nps": nps_score(g), "responses": len(g)}
        for month, g in out.groupby("month")
    ]
    return pd.DataFrame(rows).set_index("month").round(1)


def nps_by_driver(df: pd.DataFrame) -> pd.DataFrame:
    """NPS + response count per driver, best first."""
    rows = [
        {"driver": driver, "nps": nps_score(g), "responses": len(g)}
        for driver, g in df.groupby("driver")
    ]
    out = pd.DataFrame(rows).set_index("driver").sort_values("nps", ascending=False)
    return out.round(1)


def segment_mix(df: pd.DataFrame) -> pd.DataFrame:
    """Promoter / passive / detractor share overall (%)."""
    return (df["segment"].value_counts(normalize=True) * 100).round(1)


def comment_by_segment(df: pd.DataFrame) -> pd.DataFrame:
    """Mean comment length per segment."""
    g = df.groupby("segment")["comment_length"].agg(["mean", "count"]).round(1)
    return g.reindex(["promoter", "passive", "detractor"])


def plot_monthly_nps(monthly: pd.DataFrame, out: Path) -> Path:
    plt.figure(figsize=(8, 4.5))
    plt.plot(monthly.index, monthly["nps"], marker="o", color="#4c72b0")
    plt.axhline(0, color="gray", linestyle="--", linewidth=0.8)
    plt.ylabel("NPS")
    plt.title("Monthly NPS")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()
    return out


def plot_driver_nps(by_driver: pd.DataFrame, out: Path) -> Path:
    plt.figure(figsize=(8, 4.5))
    colors = ["#55a868" if v >= 0 else "#c44e52" for v in by_driver["nps"]]
    plt.bar(by_driver.index, by_driver["nps"], color=colors)
    plt.axhline(0, color="gray", linestyle="--", linewidth=0.8)
    plt.ylabel("NPS")
    plt.title("NPS by Driver")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()
    return out


def section_setup(df: pd.DataFrame) -> None:
    print_section("VOLTA NEOBANK — NPS TRENDS & DRIVERS")
    print_subsection("Data")
    print(f"  Responses:  {len(df):,}")
    print(f"  Users:      {df['user_id'].nunique():,}")
    print(f"  Date range: {df['survey_date'].min().date()} .. {df['survey_date'].max().date()}")


def section_overall(df: pd.DataFrame, mix: pd.DataFrame) -> None:
    print_subsection("Overall NPS")
    print(f"  NPS = {nps_score(df):.1f}")
    print(mix.to_string())


def section_monthly(monthly: pd.DataFrame) -> None:
    print_subsection("Monthly NPS")
    print(monthly.to_string())


def section_drivers(by_driver: pd.DataFrame) -> None:
    print_subsection("NPS by Driver")
    print(by_driver.to_string())
    print(f"\n  Best driver:  {by_driver.index[0]} ({by_driver['nps'].iloc[0]:.1f})")
    print(f"  Worst driver: {by_driver.index[-1]} ({by_driver['nps'].iloc[-1]:.1f})")


def section_comments(by_seg: pd.DataFrame) -> None:
    print_subsection("Comment Length by Segment")
    print(by_seg.to_string())


def main() -> None:
    setup()
    df = load_data()
    section_setup(df)
    mix = segment_mix(df)
    section_overall(df, mix)
    monthly = monthly_nps(df)
    section_monthly(monthly)
    by_driver = nps_by_driver(df)
    section_drivers(by_driver)
    by_seg = comment_by_segment(df)
    section_comments(by_seg)
    line = plot_monthly_nps(monthly, OUTPUT_DIR / "nps_monthly_trend.png")
    bar = plot_driver_nps(by_driver, OUTPUT_DIR / "nps_by_driver.png")
    print(f"\n  Saved: {line.name}, {bar.name}")

    print("\n" + "=" * 60)
    print("Analysis complete. Review recommendations above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
