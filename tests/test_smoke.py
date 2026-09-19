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


@pytest.fixture(scope="module")
def spend_output() -> str:
    return _run_main("volta_spend_analysis")


@pytest.fixture(scope="module")
def cs_churn_output() -> str:
    return _run_main("volta_cs_churn")


@pytest.fixture(scope="module")
def nps_output() -> str:
    return _run_main("volta_nps_trends")


@pytest.fixture(scope="module")
def jtbd_output() -> str:
    return _run_main("volta_jtbd_mapping")


@pytest.fixture(scope="module")
def unit_economics_output() -> str:
    return _run_main("volta_unit_economics")


@pytest.fixture(scope="module")
def premium_upsell_output() -> str:
    return _run_main("volta_premium_upsell")


@pytest.fixture(scope="module")
def kyc_deep_dive_output() -> str:
    return _run_main("volta_kyc_deep_dive")


@pytest.fixture(scope="module")
def referral_segments_output() -> str:
    return _run_main("volta_referral_segments")


@pytest.fixture(scope="module")
def causal_kyc_output() -> str:
    return _run_main("volta_causal_kyc")


@pytest.fixture(scope="module")
def assisted_cac_output() -> str:
    return _run_main("volta_assisted_cac")


@pytest.fixture(scope="module")
def fx_sourcing_output() -> str:
    return _run_main("volta_fx_sourcing")


@pytest.fixture(scope="module")
def premium_offers_output() -> str:
    return _run_main("volta_premium_offers")


@pytest.fixture(scope="module")
def anchor_cac_output() -> str:
    return _run_main("volta_anchor_cac")


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


def test_spend_runs(spend_output: str) -> None:
    assert "Analysis complete" in spend_output


def test_cs_churn_runs(cs_churn_output: str) -> None:
    assert "Analysis complete" in cs_churn_output


def test_nps_runs(nps_output: str) -> None:
    assert "Analysis complete" in nps_output


def test_jtbd_runs(jtbd_output: str) -> None:
    assert "Analysis complete" in jtbd_output


def test_unit_economics_runs(unit_economics_output: str) -> None:
    assert "Analysis complete" in unit_economics_output


def test_premium_upsell_runs(premium_upsell_output: str) -> None:
    assert "Analysis complete" in premium_upsell_output


def test_kyc_deep_dive_runs(kyc_deep_dive_output: str) -> None:
    assert "Analysis complete" in kyc_deep_dive_output


def test_referral_segments_runs(referral_segments_output: str) -> None:
    assert "Analysis complete" in referral_segments_output
    assert "does NOT scale" in referral_segments_output


def test_causal_kyc_runs(causal_kyc_output: str) -> None:
    assert "Analysis complete" in causal_kyc_output
    assert "RECOVERY CHECK" in causal_kyc_output
    assert "LIMITATION" in causal_kyc_output


def test_assisted_cac_runs(assisted_cac_output: str) -> None:
    assert "Analysis complete" in assisted_cac_output
    assert "DOESN'T CLEAR THE GATE" in assisted_cac_output


def test_fx_sourcing_runs(fx_sourcing_output: str) -> None:
    assert "Analysis complete" in fx_sourcing_output
    assert "COLD-START" in fx_sourcing_output.upper()


def test_premium_offers_runs(premium_offers_output: str) -> None:
    assert "Analysis complete" in premium_offers_output
    assert "PARTIALLY" in premium_offers_output.upper()


def test_anchor_cac_runs(anchor_cac_output: str) -> None:
    assert "Analysis complete" in anchor_cac_output
    assert "BREAKS ON PAID CAC" in anchor_cac_output.upper()
