"""Generate synthetic marketing-campaign data for Volta.

Produces ``data/volta_campaigns.csv`` — campaign-level spend and conversion
funnel (impressions -> clicks -> installs -> KYC -> first tx) per channel. It
connects to the attribution project: channel efficiency here (CAC, KYC rate,
first-tx rate) is the supply-side counterpart of the attribution credit.

Columns:
  - campaign_id     : int, unique
  - channel         : referral | organic_search | app_store | email | paid_social
  - start_date      : datetime, 2024-07-01 .. 2025-12-31
  - end_date        : datetime, start + 7..30 days
  - spend_eur       : float, channel-specific
  - impressions     : int
  - clicks          : int
  - installs        : int
  - kyc_completions : int
  - first_tx_count  : int
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

N_CAMPAIGNS = 250
START = pd.Timestamp("2024-07-01")
END = pd.Timestamp("2025-12-31")
WINDOW_DAYS = (END - START).days

# Channel -> (share, spend mean, CTR, install rate, KYC rate, first-tx rate).
# Referral is cheapest and converts best; paid_social is expensive and weak
# (mirrors the funnel finding that referral converts 11.7pp better).
CHANNELS = {
    "referral": (0.10, 1_500.0, 0.12, 0.30, 0.55, 0.70),
    "organic_search": (0.20, 0.0, 0.08, 0.20, 0.45, 0.60),
    "app_store": (0.25, 8_000.0, 0.05, 0.15, 0.40, 0.55),
    "email": (0.20, 2_000.0, 0.10, 0.10, 0.35, 0.50),
    "paid_social": (0.25, 15_000.0, 0.03, 0.08, 0.25, 0.40),
}
CHANNEL_NAMES = list(CHANNELS)
CHANNEL_SHARE = np.array([v[0] for v in CHANNELS.values()])
CHANNEL_SHARE = CHANNEL_SHARE / CHANNEL_SHARE.sum()


def generate_campaigns() -> pd.DataFrame:
    rng = RNG
    rows: list[dict] = []
    for campaign_id in range(N_CAMPAIGNS):
        channel = rng.choice(CHANNEL_NAMES, p=CHANNEL_SHARE)
        _, spend_mean, ctr, install_rate, kyc_rate, first_tx_rate = CHANNELS[channel]
        start = START + pd.to_timedelta(rng.uniform(0, WINDOW_DAYS), unit="D")
        end = start + pd.to_timedelta(int(rng.integers(7, 31)), unit="D")
        # Organic channels carry no spend; paid channels draw from a lognormal.
        if spend_mean == 0.0:
            spend = 0.0
        else:
            spend = float(np.clip(rng.lognormal(np.log(spend_mean), 0.4), 0, 1e6))
        impressions = int(rng.lognormal(mean=11.0, sigma=0.6))
        clicks = int(impressions * ctr * rng.uniform(0.7, 1.3))
        installs = int(clicks * install_rate * rng.uniform(0.7, 1.3))
        kyc = int(installs * kyc_rate * rng.uniform(0.7, 1.3))
        first_tx = int(kyc * first_tx_rate * rng.uniform(0.7, 1.3))
        rows.append(
            {
                "campaign_id": campaign_id,
                "channel": channel,
                "start_date": start,
                "end_date": end,
                "spend_eur": round(spend, 2),
                "impressions": impressions,
                "clicks": clicks,
                "installs": installs,
                "kyc_completions": kyc,
                "first_tx_count": first_tx,
            }
        )

    df = pd.DataFrame(rows)
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])
    return df.sort_values("start_date").reset_index(drop=True)


def main() -> None:
    df = generate_campaigns()
    out = DATA_DIR / "volta_campaigns.csv"
    df.to_csv(out, index=False)
    print(f"Generated {len(df):,} campaigns -> {out}")


if __name__ == "__main__":
    main()
