"""Generate synthetic referral-program data for Volta.

Produces ``data/volta_referrals.csv`` — referral invites with a status funnel
(sent -> accepted -> KYC completed -> first transaction). It connects to the
funnel project, where referral is the highest-converting acquisition channel.

Columns:
  - referral_id : int, unique
  - referrer_id : int, 0..N_USERS-1
  - referee_id  : int, new user id (>= N_USERS)
  - invite_date : datetime, 2024-07-01 .. 2025-12-31
  - status      : sent | accepted | kyc_completed | first_tx
  - reward_eur  : float, 0 unless the referee reached KYC / first tx
  - channel     : in_app | email | link
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

N_REFERRALS = 15_000
N_USERS = 8_000
START = pd.Timestamp("2024-07-01")
END = pd.Timestamp("2025-12-31")
WINDOW_DAYS = (END - START).days

# Status funnel: conditional conversion probabilities.
P_ACCEPTED = 0.60
P_KYC_GIVEN_ACCEPTED = 0.40
P_FIRST_TX_GIVEN_KYC = 0.70

REWARD_KYC = 10.0
REWARD_FIRST_TX = 10.0

CHANNELS = ["in_app", "email", "link"]
CHANNEL_WEIGHTS = [0.50, 0.30, 0.20]


def generate_referrals() -> pd.DataFrame:
    rng = RNG
    rows: list[dict] = []
    referee_id = N_USERS
    for referral_id in range(N_REFERRALS):
        referrer = int(rng.integers(0, N_USERS))
        invite_date = START + pd.to_timedelta(rng.uniform(0, WINDOW_DAYS), unit="D")
        if rng.random() < P_ACCEPTED:
            if rng.random() < P_KYC_GIVEN_ACCEPTED:
                if rng.random() < P_FIRST_TX_GIVEN_KYC:
                    status = "first_tx"
                    reward = REWARD_KYC + REWARD_FIRST_TX
                else:
                    status = "kyc_completed"
                    reward = REWARD_KYC
            else:
                status = "accepted"
                reward = 0.0
        else:
            status = "sent"
            reward = 0.0
        rows.append(
            {
                "referral_id": referral_id,
                "referrer_id": referrer,
                "referee_id": referee_id,
                "invite_date": invite_date,
                "status": status,
                "reward_eur": reward,
                "channel": rng.choice(CHANNELS, p=CHANNEL_WEIGHTS),
            }
        )
        referee_id += 1

    df = pd.DataFrame(rows)
    df["invite_date"] = pd.to_datetime(df["invite_date"])
    return df.sort_values("invite_date").reset_index(drop=True)


def main() -> None:
    df = generate_referrals()
    out = DATA_DIR / "volta_referrals.csv"
    df.to_csv(out, index=False)
    print(f"Generated {len(df):,} referrals -> {out}")


if __name__ == "__main__":
    main()
