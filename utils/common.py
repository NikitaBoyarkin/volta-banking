"""Shared helpers for the Volta portfolio analysis scripts.

Centralises the boilerplate (warnings/style/display), section banners, and
business constants that were copy-pasted across the four analysis scripts.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = REPO_ROOT / "outputs"


def setup(
    *,
    style: str = "dark_background",
    float_format: str = "{:.2f}",
) -> None:
    """Initialise display + warnings for an analysis script.

    Warnings are scoped to Future/UserWarning only (not blanket-suppressed) so
    real pandas/sklearn issues are not hidden during development.
    """
    import matplotlib.pyplot as plt

    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=UserWarning)
    plt.style.use(style)
    pd.set_option("display.float_format", float_format.format)


def print_section(title: str, width: int = 70, blank: bool = True) -> None:
    """Print a section banner. `blank` prepends a newline for readability."""
    rule = "=" * width
    if blank:
        print(f"\n{rule}")
    else:
        print(rule)
    print(title)
    print(rule)


def print_subsection(title: str, width: int = 70) -> None:
    """Print a lighter subsection line."""
    print(f"\n{'-' * width}")
    print(title)
    print(f"{'-' * width}")


def data_path(filename: str) -> Path:
    """Resolve a data file path. Generated CSVs live in ``data/``; this prefers
    that canonical location and falls back to the repo root for backward
    compatibility with older layouts."""
    data = DATA_DIR / filename
    if data.exists():
        return data
    return REPO_ROOT / filename


# ── Business constants ──────────────────────────────────────────────────────
# Sourced from the portfolio narrative; centralised so the four scripts stop
# drifting apart. Document the provenance of each.
CONSTANTS: dict[str, Any] = {
    # Average lifetime value per activated user (EUR). Used for revenue-impact
    # estimates in funnel and A/B analyses.
    "LTV_PER_USER_EUR": 85,
    # Monthly ARPU by plan (EUR). From retention analysis assumptions.
    "MONTHLY_ARPU_FREE_EUR": 3.2,
    "MONTHLY_ARPU_PREMIUM_EUR": 8.5,
    # A/B test design parameters.
    "MDE_ABSOLUTE": 0.05,  # +5pp minimum detectable effect
    "BASELINE_CONVERSION": 0.566,  # control KYC-complete rate
    "ALPHA": 0.05,
    "POWER": 0.80,
    # Fleet assumptions for retention LTV projection.
    "MONTHLY_NEW_ACTIVATED_USERS": 5000,
    "PREMIUM_PLAN_SHARE": 0.18,
}
