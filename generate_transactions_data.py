"""Generate a synthetic transaction ledger for Volta.

Produces ``data/volta_transactions.csv`` — the rawest dataset in the portfolio:
card / online / P2P / ATM transactions with merchant, category, channel and
status. It extends the RFM transaction data (aggregated per customer) with a
full spend ledger, ready for spend-category analysis, merchant concentration,
cashflow and declined-transaction analysis.

Columns:
  - transaction_id : int, unique
  - user_id        : int, 0..N_USERS-1 (consistent with the other generators)
  - tx_date        : datetime, 2025-01-01 .. 2025-12-31
  - amount_eur     : float, category-specific lognormal, clipped 0.5..5000
  - category       : groceries | dining | transport | shopping | bills |
                     entertainment | health | travel | cash | p2p
  - merchant       : realistic merchant per category
  - channel        : card | online | p2p | atm
  - status         : completed | declined | refunded
  - country        : DE | FR | ES | IT | NL | PL | AT | BE

Spend intensity follows the Project-4 segments (Power / Growth / Casual /
Dormant), so frequency and amount are separable by segment.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

N_USERS = 5_000
START = pd.Timestamp("2025-01-01")
END = pd.Timestamp("2025-12-31")
WINDOW_DAYS = (END - START).days  # 364

# Segment shares mirror Project 4 (Power 12 / Growth 24 / Casual 32 / Dormant 32).
SEGMENT_SHARE = {"power": 0.12, "growth": 0.24, "casual": 0.32, "dormant": 0.32}
# Per-segment monthly transaction count and amount multiplier.
SEGMENT_TX = {"power": 4.0, "growth": 2.0, "casual": 1.0, "dormant": 0.3}
SEGMENT_AMOUNT_MULT = {"power": 1.6, "growth": 1.2, "casual": 0.9, "dormant": 0.7}

# Category -> (share, amount mean, merchant pool).
CATEGORIES = {
    "groceries": (0.22, 32.0, ["Lidl", "Aldi", "Rewe", "Edeka", "Carrefour", "Tesco"]),
    "dining": (0.16, 18.0, ["Starbucks", "McDonald's", "Deliveroo", "Cafe Nero", "Pizza Express"]),
    "transport": (0.12, 14.0, ["Uber", "Bolt", "DB Bahn", "FlixBus", "City Metro"]),
    "shopping": (0.14, 48.0, ["Amazon", "Zalando", "H&M", "IKEA", "MediaMarkt"]),
    "bills": (0.10, 120.0, ["Utility Co", "Rent Direct", "Allianz", "Vodafone", "E.ON"]),
    "entertainment": (0.08, 15.0, ["Netflix", "Spotify", "Cinema City", "Steam", "Disney+"]),
    "health": (0.06, 25.0, ["Pharmacy Plus", "FitLife Gym", "Dr. Klein", "Apollo"]),
    "travel": (0.05, 180.0, ["Booking.com", "Ryanair", "Airbnb", "Lufthansa", "Trainline"]),
    "cash": (0.04, 60.0, ["ATM Withdrawal"]),
    "p2p": (0.03, 40.0, ["P2P Transfer"]),
}
CATEGORY_NAMES = list(CATEGORIES)
CATEGORY_SHARE = np.array([v[0] for v in CATEGORIES.values()])
CATEGORY_SHARE = CATEGORY_SHARE / CATEGORY_SHARE.sum()

CHANNELS = ["card", "online", "p2p", "atm"]
CHANNEL_WEIGHTS = [0.62, 0.24, 0.09, 0.05]
COUNTRIES = ["DE", "FR", "ES", "IT", "NL", "PL", "AT", "BE"]
COUNTRY_WEIGHTS = [0.30, 0.16, 0.14, 0.12, 0.10, 0.08, 0.05, 0.05]
STATUS_WEIGHTS = [0.95, 0.03, 0.02]


def generate_transactions() -> pd.DataFrame:
    rng = RNG
    segments = rng.choice(list(SEGMENT_SHARE), size=N_USERS, p=list(SEGMENT_SHARE.values()))

    rows: list[dict] = []
    tx_id = 0
    for user_id, seg in enumerate(segments):
        n_tx = rng.poisson(SEGMENT_TX[seg] * WINDOW_DAYS / 30.4)
        if n_tx == 0:
            continue
        dates = START + pd.to_timedelta(rng.uniform(0, WINDOW_DAYS, size=n_tx), unit="D")
        cats = rng.choice(CATEGORY_NAMES, size=n_tx, p=CATEGORY_SHARE)
        mult = SEGMENT_AMOUNT_MULT[seg]
        for i in range(n_tx):
            cat = cats[i]
            _, cat_mean, merchants = CATEGORIES[cat]
            amount = float(np.clip(rng.lognormal(np.log(cat_mean * mult), 0.55), 0.5, 5000))
            rows.append(
                {
                    "transaction_id": tx_id,
                    "user_id": user_id,
                    "tx_date": dates[i],
                    "amount_eur": round(amount, 2),
                    "category": cat,
                    "merchant": rng.choice(merchants),
                    "channel": rng.choice(CHANNELS, p=CHANNEL_WEIGHTS),
                    "status": rng.choice(["completed", "declined", "refunded"], p=STATUS_WEIGHTS),
                    "country": rng.choice(COUNTRIES, p=COUNTRY_WEIGHTS),
                }
            )
            tx_id += 1

    df = pd.DataFrame(rows)
    df["tx_date"] = pd.to_datetime(df["tx_date"])
    return df.sort_values("tx_date").reset_index(drop=True)


def main() -> None:
    df = generate_transactions()
    out = DATA_DIR / "volta_transactions.csv"
    df.to_csv(out, index=False)
    print(f"Generated {len(df):,} transactions -> {out}")


if __name__ == "__main__":
    main()
