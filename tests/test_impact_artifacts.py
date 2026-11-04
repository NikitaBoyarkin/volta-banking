"""Tests for outputs/impact.json — the published effect numbers (REQ-001).

`outputs/impact.json` is the machine-readable source of every effect number the
README quotes. These tests bind three claims:

1. the artifact exists and has the declared shape (keys, units, horizons);
2. each value is a number computed by the analysis code, not a string literal
   (re-running `build_impact.build_impact()` reproduces the file);
3. every euro / ratio / pp effect number the README attributes to these keys
   matches the artifact within display tolerance.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

from utils.common import DATA_DIR, OUTPUT_DIR, REPO_ROOT

IMPACT_PATH = OUTPUT_DIR / "impact.json"
README_PATH = REPO_ROOT / "README.md"

# key -> (unit, horizon) as declared by the artifact contract.
EXPECTED: dict[str, tuple[str, str]] = {
    "ab_cumulative_12m_revenue_eur": ("eur", "12m"),
    "ab_roi_multiple_12m": ("ratio", "12m"),
    "retention_incremental_ltv_eur": ("eur", "1y"),
    "kyc_lift_pp": ("pp", "28d"),
}

# README claim → artifact key. Each pattern anchors on the phrase that says
# WHAT the number measures, so unrelated euros on the same line are ignored.
_EUR = r"€\s*(\d+(?:[.,]\d+)?)\s*([KM])?"
CLAIM_PATTERNS: dict[str, re.Pattern[str]] = {
    # "+€208,5K за 12 месяцев" — the A/B effect over 12 months.
    "ab_cumulative_12m_revenue_eur": re.compile(_EUR + r"[^\n]{0,60}?12\s*месяц"),
    # "+€282K в год" — the annualised retention increment.
    "retention_incremental_ltv_eur": re.compile(_EUR + r"[^\n]{0,40}?в\s+год"),
    # "13,9× ROI".
    "ab_roi_multiple_12m": re.compile(r"(\d+[.,]\d+)\s*×\s*ROI"),
    # "+5,72 п.п. конверсии".
    "kyc_lift_pp": re.compile(r"(\d+[.,]\d+)\s*п\.\s?п\.\s*конверсии"),
}

REL_TOL = 0.01  # README rounds to 4-5 significant figures


def _impact() -> dict[str, dict[str, Any]]:
    assert IMPACT_PATH.exists(), (
        f"{IMPACT_PATH} is missing — run `make impact` (or "
        "PYTHONPATH=.:scripts uv run python scripts/build_impact.py)"
    )
    return json.loads(IMPACT_PATH.read_text(encoding="utf-8"))


def _parse_number(raw: str, suffix: str | None = None) -> float:
    """Parse a README-style number: comma decimal separator, optional K/M."""
    value = float(raw.replace(",", "."))
    if suffix:
        value *= {"K": 1_000, "M": 1_000_000}[suffix]
    return value


def test_impact_artifact_has_declared_shape() -> None:
    impact = _impact()
    assert set(impact) == set(EXPECTED)

    for key, (unit, horizon) in EXPECTED.items():
        entry = impact[key]
        assert isinstance(entry, dict), f"{key} must be an object"
        assert set(entry) == {"value", "source_file", "unit", "horizon"}, key
        assert entry["unit"] == unit, key
        assert entry["horizon"] == horizon, key
        assert isinstance(entry["source_file"], str) and entry["source_file"], key
        assert (REPO_ROOT / entry["source_file"]).is_file(), (
            f"{key}.source_file does not exist: {entry['source_file']}"
        )


def test_impact_values_are_numbers_not_strings() -> None:
    impact = _impact()
    for key, entry in impact.items():
        value = entry["value"]
        assert isinstance(value, int | float), f"{key}.value is {type(value).__name__}"
        assert not isinstance(value, bool), f"{key}.value must not be a bool"
        assert value == value, f"{key}.value is NaN"  # NaN != NaN


def test_impact_artifact_matches_current_computation() -> None:
    """The file is a build product, not hand-tuned: recomputing reproduces it."""
    if not (DATA_DIR / "volta_ab_experiment.csv").exists():
        pytest.skip("generated datasets missing — run `make data` first")

    from build_impact import build_impact

    fresh = build_impact()
    published = _impact()
    assert set(fresh) == set(published)
    for key in fresh:
        assert fresh[key]["value"] == pytest.approx(published[key]["value"], rel=1e-6), key


def test_readme_effect_numbers_match_artifact() -> None:
    impact = _impact()
    readme = README_PATH.read_text(encoding="utf-8")

    for key, pattern in CLAIM_PATTERNS.items():
        matches = pattern.findall(readme)
        assert matches, (
            f"README no longer cites {key} in a recognised form "
            f"(pattern: {pattern.pattern!r}) — update the wording or this map"
        )
        expected = impact[key]["value"]
        for groups in matches:
            raw, suffix = (groups, None) if isinstance(groups, str) else groups
            claimed = _parse_number(raw, suffix or None)
            assert claimed == pytest.approx(expected, rel=REL_TOL), (
                f"README claims {claimed:,.2f} for {key}, artifact says "
                f"{expected:,.2f} (tolerance {REL_TOL:.0%})"
            )
