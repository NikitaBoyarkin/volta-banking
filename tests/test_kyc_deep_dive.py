"""Tests for volta_kyc_deep_dive.py — 45+ KYC deep-dive (risk #4)."""

from __future__ import annotations

import pandas as pd

import volta_kyc_deep_dive as vk

# (age, control_rate, treatment_rate) per channel — referral (trust) converts
# 45+ best, so the 45+ vs 25-34 gap is smallest there.
_RATES: dict[str, dict[str, dict[str, float]]] = {
    "18-24": {
        "control": {"app_store": 0.50, "google_play": 0.52, "website": 0.48, "referral": 0.56},
        "treatment": {"app_store": 0.60, "google_play": 0.62, "website": 0.58, "referral": 0.66},
    },
    "25-34": {
        "control": {"app_store": 0.60, "google_play": 0.62, "website": 0.58, "referral": 0.64},
        "treatment": {"app_store": 0.62, "google_play": 0.64, "website": 0.60, "referral": 0.66},
    },
    "35-44": {
        "control": {"app_store": 0.55, "google_play": 0.57, "website": 0.53, "referral": 0.61},
        "treatment": {"app_store": 0.70, "google_play": 0.72, "website": 0.66, "referral": 0.74},
    },
    "45+": {
        "control": {"app_store": 0.50, "google_play": 0.52, "website": 0.48, "referral": 0.58},
        "treatment": {"app_store": 0.50, "google_play": 0.52, "website": 0.48, "referral": 0.60},
    },
}
_N_PER_CELL = 100


def _make_df() -> pd.DataFrame:
    """Small deterministic frame mirroring the A/B data with the risk-#4 contrast."""
    rows: list[dict[str, float | str | int]] = []
    uid = 0
    for age, groups in _RATES.items():
        for group, channels in groups.items():
            for channel, rate in channels.items():
                k = int(round(rate * _N_PER_CELL))
                for i in range(_N_PER_CELL):
                    rows.append(
                        {
                            "customer_id": uid,
                            "group": group,
                            "age_group": age,
                            "device": "ios",
                            "channel": channel,
                            "pre_kyc_rate": 0.5,
                            "kyc_completed": int(i < k),
                            "churned_30d": 0,
                            "revenue_30d_eur": 0.0,
                        }
                    )
                    uid += 1
    return pd.DataFrame(rows)


def test_hte_45_plus_lift_not_significant() -> None:
    hte = vk.hte_by_age(_make_df())
    assert hte.loc["45+", "p"] > vk.ALPHA
    assert hte.loc["45+", "lift_pp"] < 2.0


def test_hte_young_lift_significant() -> None:
    hte = vk.hte_by_age(_make_df())
    assert hte.loc["35-44", "p"] < vk.ALPHA
    assert hte.loc["35-44", "lift_pp"] > 5.0


def test_45_plus_gap_persists_in_treatment() -> None:
    df = _make_df()
    n1, x1 = vk.age_conversion_counts(df, vk.ANCHOR_AGE, "treatment")
    n2, x2 = vk.age_conversion_counts(df, vk.GAP_AGE, "treatment")
    z = vk.two_proportion_ztest(n1, x1, n2, x2)
    assert z["p"] < vk.ALPHA
    assert z["p1"] > z["p2"]


def test_channel_gap_referral_smallest() -> None:
    gap = vk.channel_gap(_make_df())
    assert gap.loc["referral", "gap_pp"] > gap.loc["app_store", "gap_pp"]
    assert gap.loc["referral", "gap_pp"] > gap.loc["website", "gap_pp"]


def test_chi_square_significant() -> None:
    chi = vk.chi_square_age_completion(_make_df())
    assert chi["p"] < vk.ALPHA
    assert chi["dof"] == (len(vk.AGE_ORDER) - 1) * 1


def test_hte_by_age_shape() -> None:
    hte = vk.hte_by_age(_make_df())
    assert list(hte.index) == vk.AGE_ORDER
    assert set(hte.columns) == {
        "n_control",
        "n_treatment",
        "control_rate",
        "treatment_rate",
        "lift_pp",
        "z",
        "p",
    }


def test_plot_writes_png(tmp_path) -> None:
    df = _make_df()
    out = tmp_path / "kyc_hte.png"
    path = vk.plot_hte_by_age(df, out)
    assert path == out
    assert out.exists()
    assert out.stat().st_size > 1000
