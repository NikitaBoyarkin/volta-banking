"""Generate synthetic referral data with segment-dependent conversion.

Produces `volta_referral_segments.csv` consumed by `volta_referral_segments.py`:

  referral_id, referee_id, jtbd_segment, cohort, channel, status, reward_eur

Design — referral funnel (sent → accepted → kyc_completed → first_tx) across
five JTBD segments. The audit's risk #5: "referral doesn't scale to new
segments". The anchor (young professionals) and status-seekers (premium_status)
convert well; digital newcomers 45+ and family budgeters barely convert — the
referral value prop doesn't land outside the anchor. Acceptance also rises with
cohort engagement (Power > Dormant) and the invite channel (in_app > email > link).

Run from the repo root:
    PYTHONPATH=.:scripts uv run python scripts/generate_referral_segments_data.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

COHORT_ORDER = ["Power", "Growth", "Casual", "Dormant"]
CHANNEL_ORDER = ["in_app", "email", "link"]
STATUS_ORDER = ["sent", "accepted", "kyc_completed", "first_tx"]

# (segment, n_referrals, cohort_dist, base_accept, base_kyc_given_accepted)
# base_accept = P(referee accepts the invite); base_kyc = P(KYC | accepted).
# The risk-#5 contrast: anchor + status-seekers accept and convert; digital
# newcomers 45+ and family budgeters barely do.
SEGMENT_SPECS: list[tuple[str, int, tuple[float, ...], float, float]] = [
    ("young_professionals", 12000, (0.30, 0.40, 0.25, 0.05), 0.70, 0.55),
    ("digital_newcomers", 8000, (0.02, 0.15, 0.43, 0.40), 0.30, 0.25),
    ("travelers", 6000, (0.25, 0.40, 0.30, 0.05), 0.60, 0.45),
    ("family_budgeters", 10000, (0.08, 0.30, 0.47, 0.15), 0.40, 0.30),
    ("premium_status", 4000, (0.55, 0.30, 0.12, 0.03), 0.75, 0.60),
]
SEGMENT_BASE_ACCEPT: dict[str, float] = {name: a for name, _, _, a, _ in SEGMENT_SPECS}
SEGMENT_BASE_KYC: dict[str, float] = {name: k for name, _, _, _, k in SEGMENT_SPECS}
SEGMENT_COHORT_DIST: dict[str, tuple[float, ...]] = {
    name: dist for name, _, dist, _, _ in SEGMENT_SPECS
}

# P(first transaction | KYC completed) — uniform across segments.
P_FIRST_TX_GIVEN_KYC = 0.70

COHORT_MULT: dict[str, float] = {"Power": 1.3, "Growth": 1.1, "Casual": 0.9, "Dormant": 0.6}
CHANNEL_MULT: dict[str, float] = {"in_app": 1.2, "email": 1.0, "link": 0.8}

REWARD_KYC = 10.0
REWARD_FIRST_TX = 10.0


def acceptance_probability(segment: str, cohort: str, channel: str) -> float:
    """P(referee accepts the invite) — segment × cohort × channel (pure)."""
    p = SEGMENT_BASE_ACCEPT[segment] * COHORT_MULT[cohort] * CHANNEL_MULT[channel]
    return min(p, 0.95)


def referral_status(segment: str, cohort: str, channel: str) -> tuple[str, float]:
    """Draw one referral's funnel outcome: (status, reward_eur)."""
    if RNG.random() > acceptance_probability(segment, cohort, channel):
        return "sent", 0.0
    if RNG.random() > SEGMENT_BASE_KYC[segment]:
        return "accepted", 0.0
    if RNG.random() > P_FIRST_TX_GIVEN_KYC:
        return "kyc_completed", REWARD_KYC
    return "first_tx", REWARD_KYC + REWARD_FIRST_TX


def generate_referrals() -> pd.DataFrame:
    """One row per referral invite; referee carries a JTBD segment + cohort."""
    rows: list[dict[str, float | str | int]] = []
    referral_id = 0
    for segment, n, cohort_dist, _, _ in SEGMENT_SPECS:
        for _ in range(n):
            referral_id += 1
            cohort = RNG.choice(COHORT_ORDER, p=cohort_dist)
            channel = RNG.choice(CHANNEL_ORDER, p=[0.5, 0.3, 0.2])
            status, reward = referral_status(segment, cohort, channel)
            rows.append(
                {
                    "referral_id": referral_id,
                    "referee_id": referral_id,
                    "jtbd_segment": segment,
                    "cohort": cohort,
                    "channel": channel,
                    "status": status,
                    "reward_eur": reward,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    df = generate_referrals()
    df.to_csv(DATA_DIR / "volta_referral_segments.csv", index=False)

    print(f"Generated {len(df):,} referrals across {df['jtbd_segment'].nunique()} segments")
    print("Wrote: volta_referral_segments.csv")
    print("\nSent→first-tx conversion by segment (%):")
    g = (
        df[df["status"] == "first_tx"].groupby("jtbd_segment").size()
        / df.groupby("jtbd_segment").size()
    )
    print((g * 100).round(1).to_string())


if __name__ == "__main__":
    main()
