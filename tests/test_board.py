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
    # 8 sections → 8 inline SVG charts.
    assert html.count("<svg") == len(REQUIRED_SECTIONS)
    assert "NaN" not in html and "nan" not in html


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
    assert 0.04 < lift < 0.06


def test_causal_att_positive() -> None:
    did = bb.causal_did(bb._read("volta_causal_kyc.csv"))
    assert did["att"] > 0.05
    assert did["in_post"] > did["in_pre"]


def test_build_og_image_writes_png(tmp_path) -> None:
    out = bb.build_og_image(tmp_path / "og.png")
    assert out.exists()
    assert out.stat().st_size > 5000
