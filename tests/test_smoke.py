"""End-to-end smoke tests: run each analysis script's main() and assert it
completes without raising and produces non-trivial output.

These execute every `section_*` printing function and all plotting code, so they
both (a) verify the scripts actually run on the committed/generated data and
(b) give meaningful coverage of the print-heavy sections the unit tests skip.
"""

from __future__ import annotations

import io
from contextlib import redirect_stdout

import pytest


def _run_main(module_name: str) -> str:
    module = __import__(module_name)
    buf = io.StringIO()
    with redirect_stdout(buf):
        module.main()
    return buf.getvalue()


@pytest.fixture(scope="module")
def funnel_output() -> str:
    return _run_main("volta_funnel_analysis")


@pytest.fixture(scope="module")
def ab_output() -> str:
    return _run_main("volta_ab_testing")


@pytest.fixture(scope="module")
def retention_output() -> str:
    return _run_main("volta_retention_analysis")


@pytest.fixture(scope="module")
def segmentation_output() -> str:
    return _run_main("volta_segmentation")


@pytest.fixture(scope="module")
def churn_output() -> str:
    return _run_main("volta_churn_prediction")


@pytest.fixture(scope="module")
def rfm_output() -> str:
    return _run_main("volta_rfm_analysis")


@pytest.fixture(scope="module")
def clv_output() -> str:
    return _run_main("volta_clv_modeling")


@pytest.fixture(scope="module")
def attribution_output() -> str:
    return _run_main("volta_attribution")


@pytest.fixture(scope="module")
def anomaly_output() -> str:
    return _run_main("volta_anomaly_detection")


def test_funnel_runs(funnel_output: str) -> None:
    assert len(funnel_output) > 100


def test_ab_runs(ab_output: str) -> None:
    assert "Analysis complete" in ab_output
    assert "FINAL RECOMMENDATION" in ab_output


def test_retention_runs(retention_output: str) -> None:
    assert len(retention_output) > 100


def test_segmentation_runs(segmentation_output: str) -> None:
    assert len(segmentation_output) > 100


def test_churn_runs(churn_output: str) -> None:
    assert "Analysis complete" in churn_output


def test_rfm_runs(rfm_output: str) -> None:
    assert "Analysis complete" in rfm_output


def test_clv_runs(clv_output: str) -> None:
    assert "Analysis complete" in clv_output


def test_attribution_runs(attribution_output: str) -> None:
    assert "Analysis complete" in attribution_output


def test_anomaly_runs(anomaly_output: str) -> None:
    assert "Analysis complete" in anomaly_output
