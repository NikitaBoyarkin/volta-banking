"""Generate synthetic acquisition-economics data for the assisted-onboarding audit.

Produces `volta_assisted_cac.csv` consumed by `volta_assisted_cac.py`:

  user_id, segment, channel, cac_eur, monthly_arpu_eur, contribution_margin,
  monthly_churn_rate, months_retained, ltv_eur

Design — the audit's v2 risk #1: "assisted onboarding 45+ costs more than 45+
LTV". Each row is one acquired user with the economics of the channel that
brought them in and the segment they belong to:

  segment  drives ARPU and baseline churn (45+ monetizes less, churns more)
  channel  drives CAC and a retention multiplier (assisted onboarding buys
           trust → better retention, but at a human-touch cost)

Per-user LTV is a distribution, not a point estimate, so the analysis can
bootstrap confidence intervals:

  LTV_user = ARPU × contribution_margin × months_retained

where months_retained ~ Geometric(effective_churn) — the expected lifetime of
a user churning at that monthly rate.

The generator encodes the known contrast the analysis must recover: the anchor
(young professionals) clears the LTV/CAC ≥ 3 gate through referral, while 45+
fails on every channel and worst of all on assisted onboarding.

Run from the repo root:
    uv run python generate_assisted_cac_data.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

# ── Segment economics ────────────────────────────────────────────────────────
# (segment, n_users, avg_monthly_arpu, baseline_monthly_churn)
SEGMENT_SPECS: list[tuple[str, int, float, float]] = [
    ("young_professionals", 6000, 4.50, 0.035),
    ("digital_newcomers", 6000, 3.40, 0.060),
    ("family_budgeters", 5000, 3.20, 0.045),
]

# ── Channel economics ────────────────────────────────────────────────────────
# (channel, cac_eur, churn_multiplier, acquisition_mix)
# churn_multiplier < 1 means the channel buys better retention (assisted
# onboarding = human trust); the mix is the share of a segment acquired there.
CHANNEL_SPECS: list[tuple[str, float, float, dict[str, float]]] = [
    (
        "assisted",
        120.0,
        0.75,
        {"young_professionals": 0.03, "digital_newcomers": 0.25, "family_budgeters": 0.08},
    ),
    (
        "partner",
        55.0,
        0.90,
        {"young_professionals": 0.07, "digital_newcomers": 0.25, "family_budgeters": 0.12},
    ),
    (
        "referral",
        25.0,
        0.85,
        {"young_professionals": 0.40, "digital_newcomers": 0.15, "family_budgeters": 0.30},
    ),
    (
        "in_app",
        35.0,
        1.00,
        {"young_professionals": 0.35, "digital_newcomers": 0.20, "family_budgeters": 0.35},
    ),
    (
        "paid_social",
        70.0,
        1.05,
        {"young_professionals": 0.15, "digital_newcomers": 0.15, "family_budgeters": 0.15},
    ),
]

CHANNEL_ORDER = [c for c, _, _, _ in CHANNEL_SPECS]
SEGMENT_ORDER = [s for s, _, _, _ in SEGMENT_SPECS]
CHANNEL_CAC: dict[str, float] = {c: cac for c, cac, _, _ in CHANNEL_SPECS}
CHANNEL_CHURN_MULT: dict[str, float] = {c: mult for c, _, mult, _ in CHANNEL_SPECS}
CHANNEL_MIX: dict[str, dict[str, float]] = {c: mix for c, _, _, mix in CHANNEL_SPECS}
SEGMENT_ARPU: dict[str, float] = {s: arpu for s, _, arpu, _ in SEGMENT_SPECS}
SEGMENT_CHURN: dict[str, float] = {s: churn for s, _, _, churn in SEGMENT_SPECS}

# Blended contribution margin per user (revenue minus variable cost to serve).
CONTRIBUTION_MARGIN = 0.70
# Users are observed for at most this many months (right-censoring horizon).
MAX_MONTHS = 60
# LTV/CAC gate: standard healthy-acquisition threshold.
GATE_LTV_CAC = 3.0
# Payback gate: months of contribution to recover acquisition cost.
GATE_PAYBACK_MONTHS = 12.0


def effective_churn(segment: str, channel: str) -> float:
    """Monthly churn for a segment × channel, after the channel retention effect."""
    return float(np.clip(SEGMENT_CHURN[segment] * CHANNEL_CHURN_MULT[channel], 0.005, 0.5))


def draw_months_retained(segment: str, channel: str, rng: np.random.Generator) -> int:
    """Simulated lifetime (months) for one user: geometric with a 60-month cap."""
    churn = effective_churn(segment, channel)
    months = int(rng.geometric(churn))
    return int(min(months, MAX_MONTHS))


def user_ltv(arpu: float, months_retained: int) -> float:
    """Lifetime value for one user (contribution margin applied to ARPU)."""
    return float(arpu * CONTRIBUTION_MARGIN * months_retained)


def generate_users() -> pd.DataFrame:
    """One row per acquired user: CAC, ARPU, churn, lifetime, LTV."""
    rows: list[dict[str, float | str | int]] = []
    user_id = 0
    for segment, n, arpu, _ in SEGMENT_SPECS:
        mix = np.array([CHANNEL_MIX[c][segment] for c in CHANNEL_ORDER])
        mix = mix / mix.sum()
        channels = RNG.choice(CHANNEL_ORDER, size=n, p=mix)
        for channel in channels:
            user_id += 1
            # Per-user ARPU varies around the segment mean (older users hold
            # higher balances, but the spread is modest).
            user_arpu = max(0.2, float(RNG.normal(arpu, arpu * 0.25)))
            months = draw_months_retained(segment, str(channel), RNG)
            cac = CHANNEL_CAC[str(channel)] * float(RNG.normal(1.0, 0.08))
            rows.append(
                {
                    "user_id": user_id,
                    "segment": segment,
                    "channel": str(channel),
                    "cac_eur": round(cac, 2),
                    "monthly_arpu_eur": round(user_arpu, 2),
                    "contribution_margin": CONTRIBUTION_MARGIN,
                    "monthly_churn_rate": round(effective_churn(segment, str(channel)), 4),
                    "months_retained": months,
                    "ltv_eur": round(user_ltv(user_arpu, months), 2),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    df = generate_users()
    df.to_csv(DATA_DIR / "volta_assisted_cac.csv", index=False)

    print(f"Generated {len(df):,} acquired users across {df['segment'].nunique()} segments")
    print("Wrote: volta_assisted_cac.csv")

    print("\nBlended LTV/CAC by segment:")
    g = df.groupby("segment").apply(
        lambda d: d["ltv_eur"].mean() / d["cac_eur"].mean(), include_groups=False
    )
    print(g.round(2).to_string())

    print("\nLTV/CAC by segment × channel:")
    pivot = df.pivot_table(
        index="segment", columns="channel", values="ltv_eur", aggfunc="mean"
    ) / df.pivot_table(index="segment", columns="channel", values="cac_eur", aggfunc="mean")
    print(pivot.reindex(index=SEGMENT_ORDER, columns=CHANNEL_ORDER).round(2).to_string())
    print(f"\nGate: LTV/CAC >= {GATE_LTV_CAC:.1f} and payback <= {GATE_PAYBACK_MONTHS:.0f} months.")


if __name__ == "__main__":
    main()
