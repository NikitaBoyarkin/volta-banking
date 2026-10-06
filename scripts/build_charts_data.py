"""Materialise board-ready copies of the raw CSVs for the dbt-charts board.

DuckDB infers nanosecond-precision timestamps from `volta_funnel_data.csv`,
which the dbt-charts file-source loader cannot convert to Python datetimes.
Truncating to microseconds keeps the columns readable without touching the
raw dataset. Run: uv run python scripts/build_charts_data.py
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "charts"

TIMESTAMP_COLUMNS = ("install_date", "first_tx_date")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    funnel = pd.read_csv(DATA / "volta_funnel_data.csv")
    for col in TIMESTAMP_COLUMNS:
        if col in funnel.columns:
            funnel[col] = pd.to_datetime(funnel[col], errors="coerce").dt.strftime(
                "%Y-%m-%d %H:%M:%S.%f"
            )
    funnel.to_csv(OUT / "funnel.csv", index=False)
    print(f"wrote {OUT / 'funnel.csv'} ({len(funnel):,} rows)")


if __name__ == "__main__":
    main()
