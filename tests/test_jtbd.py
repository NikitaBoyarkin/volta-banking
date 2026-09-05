"""Tests for volta_jtbd_mapping.py — JTBD segments × behavioral cohorts."""

from __future__ import annotations

import numpy as np
import pandas as pd

import volta_jtbd_mapping as vj


def _make_df() -> pd.DataFrame:
    """Small deterministic frame with the risk-#3 contrast baked in.

    Cohort distribution per segment mirrors the generator: Dormant is
    over-represented in digital newcomers (40%) and under-represented in
    family budgeters (15%).
    """
    rng = np.random.default_rng(0)
    n = 2000
    segment = pd.Series(
        rng.choice(
            vj.SEGMENT_ORDER,
            size=n,
            p=[0.3, 0.2, 0.15, 0.25, 0.1],
        )
    )
    dist = {
        "young_professionals": (0.30, 0.40, 0.25, 0.05),
        "digital_newcomers": (0.02, 0.15, 0.43, 0.40),
        "travelers": (0.25, 0.40, 0.30, 0.05),
        "family_budgeters": (0.08, 0.30, 0.47, 0.15),
        "premium_status": (0.55, 0.30, 0.12, 0.03),
    }
    cohort = pd.Series([rng.choice(vj.COHORT_ORDER, p=dist[s]) for s in segment])
    return pd.DataFrame(
        {
            "jtbd_segment": segment,
            "cohort": cohort,
            "support_tickets": rng.poisson(2.0, size=n),
            "kyc_duration_days": rng.normal(4.0, 1.0, size=n),
        }
    )


def test_cross_tab_shape_and_normalization() -> None:
    df = _make_df()
    counts, row_pct = vj.cross_tab(df)
    assert list(counts.index) == vj.SEGMENT_ORDER
    assert list(counts.columns) == vj.COHORT_ORDER
    # Row % sums to 100 per segment.
    assert np.allclose(row_pct.sum(axis=1), 100.0)


def test_cross_tab_raises_on_missing_segment() -> None:
    df = _make_df()
    df = df[df["jtbd_segment"] != "travelers"]
    try:
        vj.cross_tab(df)
    except AssertionError:
        return
    raise AssertionError("cross_tab should assert on a missing JTBD segment")


def test_chi_square_significant_on_contrast_data() -> None:
    df = _make_df()
    counts, _ = vj.cross_tab(df)
    chi = vj.chi_square_test(counts)
    assert chi["p"] < 0.05
    assert chi["dof"] == (len(vj.SEGMENT_ORDER) - 1) * (len(vj.COHORT_ORDER) - 1)


def test_dormant_concentrates_in_digital_newcomers() -> None:
    df = _make_df()
    dormant_pct = vj.dormant_share_by_segment(df)
    assert dormant_pct["digital_newcomers"] > dormant_pct["family_budgeters"]
    assert dormant_pct["digital_newcomers"] > 30.0
    assert dormant_pct["family_budgeters"] < 25.0


def test_two_proportion_ztest_significant() -> None:
    df = _make_df()
    n_ux = int((df["jtbd_segment"] == "digital_newcomers").sum())
    x_ux = int(((df["jtbd_segment"] == "digital_newcomers") & (df["cohort"] == "Dormant")).sum())
    n_need = int((df["jtbd_segment"] == "family_budgeters").sum())
    x_need = int(((df["jtbd_segment"] == "family_budgeters") & (df["cohort"] == "Dormant")).sum())
    z = vj.two_proportion_ztest(n_ux, x_ux, n_need, x_need)
    assert z["p"] < 0.05
    assert z["p1"] > z["p2"]


def test_two_proportion_ztest_equal_proportions() -> None:
    z = vj.two_proportion_ztest(100, 50, 100, 50)
    assert abs(z["z"]) < 1e-9
    assert z["p"] > 0.99


def test_friction_by_cohort_orders_by_cohort() -> None:
    df = _make_df()
    friction = vj.friction_by_cohort(df)
    assert list(friction.index) == vj.COHORT_ORDER
    assert {"support_tickets", "kyc_duration_days"} <= set(friction.columns)


def test_dormant_friction_contrast_ux_higher() -> None:
    df = _make_df()
    # Give digital-newcomer Dormant users extra friction.
    mask = (df["jtbd_segment"] == "digital_newcomers") & (df["cohort"] == "Dormant")
    df.loc[mask, "support_tickets"] += 3
    contrast = vj.dormant_friction_contrast(df)
    assert contrast["ux_tickets"] > contrast["need_tickets"]


def test_plot_heatmap_writes_png(tmp_path) -> None:
    df = _make_df()
    _, row_pct = vj.cross_tab(df)
    out = tmp_path / "heat.png"
    path = vj.plot_heatmap(row_pct, out)
    assert path == out
    assert out.exists()
    assert out.stat().st_size > 1000
