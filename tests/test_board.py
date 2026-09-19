"""Tests for build_board.py — the zero-install HTML board (REQ-203)."""

from __future__ import annotations

import build_board as bb

REQUIRED_SECTIONS = [
    "funnel",
    "ab",
    "retention",
    "causal",
    "segmentation",
    "jobs",
    "referral",
    "scale",
    "offers",
    "fx",
    "assisted",
    "jtbd",
]


def test_build_html_is_self_contained() -> None:
    html = bb.build_html()
    assert html.startswith("<!DOCTYPE html>")
    # No JavaScript and no external resources — must open with a double-click.
    assert "<script" not in html
    assert "<link" not in html
    assert 'src="http' not in html
    # The only allowed URLs are the SVG XML namespace and the repo hyperlink.
    residual = html.replace("http://www.w3.org/2000/svg", "").replace(
        "https://github.com/NikitaBoyarkin/volta-banking", ""
    )
    assert "http" not in residual


def test_build_html_has_every_section_and_chart() -> None:
    html = bb.build_html()
    for sec in REQUIRED_SECTIONS:
        assert f'id="{sec}"' in html, sec
    # One inline SVG chart per section.
    assert html.count("<svg") == len(REQUIRED_SECTIONS)
    assert "NaN" not in html and "nan" not in html


def test_assisted_ltv_cac_ordering() -> None:
    labels, values = bb.assisted_ltv_cac_by_segment(bb._read("volta_assisted_cac.csv"))
    assert labels[0] == "Young Professionals"
    assert values[0] > values[-1]
    assert values[-1] < 1.0


def test_fx_cost_decreases_with_volume() -> None:
    labels, values = bb.fx_cost_by_volume(bb._read("volta_fx_sourcing.csv"))
    assert len(labels) == len(values) == 9
    assert values[0] > values[-1]
    assert values[-1] <= 0.0055


def test_anchor_ltv_cac_decreases_with_scale() -> None:
    labels, values = bb.anchor_ltv_cac_vs_scale(bb._read("volta_anchor_cac.csv"))
    assert labels == ["10K", "40K", "70K", "120K", "225K"]
    assert values[0] > values[-1]
    assert values[0] >= 3.0
    assert values[-1] < 3.0


def test_premium_offers_treatment_beats_control() -> None:
    labels, control, treatment = bb.premium_offers_by_segment(bb._read("volta_premium_offers.csv"))
    assert len(labels) == 4
    assert all(t > c for t, c in zip(treatment, control, strict=True))
    # The anchor still converts far above the 45+ treatment.
    assert treatment[0] > treatment[1] * 2


def test_chart_helpers_emit_svg() -> None:
    bar = bb.bar_chart(["a", "b"], [0.2, 0.4])
    assert bar.startswith("<svg") and bar.count("<rect") >= 2
    line = bb.line_chart(["M0", "M1"], [("s", [0.5, 0.3], "#fff")])
    assert line.startswith("<svg") and "<polyline" in line
    grouped = bb.grouped_bar_chart(["x", "y"], [("s", [0.1, 0.2], "#fff")])
    assert grouped.startswith("<svg")


def test_empty_input_does_not_crash() -> None:
    assert bb.bar_chart([], []).startswith("<svg")
    assert bb.line_chart([], []).startswith("<svg")
    assert bb.grouped_bar_chart([], []).startswith("<svg")


def test_funnel_bottleneck_is_kyc_complete() -> None:
    labels, values = bb.funnel_step_conversion(bb._read("volta_funnel_data.csv"))
    assert labels[values.index(min(values))] == "kyc_complete"


def test_ab_lift_matches_committed_data() -> None:
    control, treatment, lift = bb.ab_lift(bb._read("volta_ab_experiment.csv"))
    assert 0.5 < control < 0.6
    assert treatment > control
    assert 0.04 < lift < 0.08


def test_causal_att_positive() -> None:
    did = bb.causal_did(bb._read("volta_causal_kyc.csv"))
    assert did["att"] > 0.05
    assert did["in_post"] > did["in_pre"]


def test_build_og_image_writes_png(tmp_path) -> None:
    out = bb.build_og_image(tmp_path / "og.png")
    assert out.exists()
    assert out.stat().st_size > 5000
