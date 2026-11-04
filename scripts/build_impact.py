"""Publish the portfolio's effect numbers to one machine-readable artifact.

Runs the same pure functions the analysis scripts print from and writes
`outputs/impact.json` — the single source of truth for every effect number
quoted elsewhere (README, board, portfolio notes).

Run from the repo root:
    PYTHONPATH=.:scripts uv run python scripts/build_impact.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

import volta_ab_testing as ab
import volta_retention_analysis as vr
from utils.common import OUTPUT_DIR, data_path

IMPACT_PATH = OUTPUT_DIR / "impact.json"


def _entry(value: float, source_file: str, unit: str, horizon: str) -> dict[str, Any]:
    return {
        "value": float(value),
        "source_file": source_file,
        "unit": unit,
        "horizon": horizon,
    }


def build_impact() -> dict[str, dict[str, Any]]:
    """Compute the four published effect numbers. Pure: reads data, writes nothing."""
    ab_df = pd.read_csv(data_path("volta_ab_experiment.csv"))
    ab_impact = ab.projected_impact(ab_df)

    return {
        "ab_cumulative_12m_revenue_eur": _entry(
            ab_impact["cumulative_12m_revenue"],
            "scripts/volta_ab_testing.py",
            "eur",
            "12m",
        ),
        "ab_roi_multiple_12m": _entry(
            ab_impact["roi_multiple_12m"],
            "scripts/volta_ab_testing.py",
            "ratio",
            "12m",
        ),
        "retention_incremental_ltv_eur": _entry(
            vr.annual_retention_impact(),
            "scripts/volta_retention_analysis.py",
            "eur",
            "1y",
        ),
        "kyc_lift_pp": _entry(
            ab_impact["absolute_lift"] * 100,
            "scripts/volta_ab_testing.py",
            "pp",
            "28d",
        ),
    }


def write_impact(path: Path = IMPACT_PATH) -> dict[str, dict[str, Any]]:
    """Compute and write the artifact in one place (the only writer)."""
    impact = build_impact()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(impact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return impact


def main() -> None:
    impact = write_impact()
    print(f"Wrote {IMPACT_PATH}")
    for key, entry in impact.items():
        print(f"  {key:<32} {entry['value']:>14,.2f} {entry['unit']:<5} ({entry['horizon']})")


if __name__ == "__main__":
    main()
