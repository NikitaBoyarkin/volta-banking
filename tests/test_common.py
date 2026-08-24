"""Tests for utils/common.py — shared helpers used by all four scripts."""

from __future__ import annotations

from utils.common import CONSTANTS, data_path, print_section


def test_constants_has_expected_keys() -> None:
    for key in (
        "LTV_PER_USER_EUR",
        "MONTHLY_ARPU_FREE_EUR",
        "MONTHLY_ARPU_PREMIUM_EUR",
        "MDE_ABSOLUTE",
        "BASELINE_CONVERSION",
        "ALPHA",
        "POWER",
        "MONTHLY_NEW_ACTIVATED_USERS",
        "PREMIUM_PLAN_SHARE",
    ):
        assert key in CONSTANTS


def test_data_path_resolves_committed_funnel_csv() -> None:
    """volta_funnel_data.csv lives in data/ — data_path must find it."""
    p = data_path("volta_funnel_data.csv")
    assert p.exists()
    assert p.name == "volta_funnel_data.csv"


def test_data_path_prefers_data_dir() -> None:
    """Generated CSVs live in data/ — data_path must prefer the canonical dir."""
    p = data_path("volta_ab_experiment.csv")
    assert p.exists()
    assert p.parent.name == "data"


def test_print_section_prints_banner(capsys) -> None:
    print_section("TEST SECTION", width=20, blank=False)
    out = capsys.readouterr().out
    assert "TEST SECTION" in out
    assert "=" * 20 in out
