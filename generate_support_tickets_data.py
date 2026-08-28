"""Generate synthetic support-ticket data for Volta.

Produces ``data/volta_support_tickets.csv`` — customer-service tickets with
category, priority, resolution time and CSAT. It connects to the churn project:
the per-user ticket count is taken from ``volta_churn_data.csv``'s
``support_tickets`` feature, so this ledger is the ground truth behind that
feature and the two datasets agree. Users who open more tickets — especially
unresolved ones — are more likely to churn.

Columns:
  - ticket_id   : int, unique
  - user_id     : int, 0..N_USERS-1
  - created_at  : datetime, 2024-07-01 .. 2025-12-31
  - resolved_at : datetime or NaN (open tickets)
  - category    : kyc | card | app | fraud | billing | account
  - priority    : low | medium | high | urgent
  - channel     : in_app_chat | email | phone
  - csat_score  : int 1..5 or NaN (unrated)
  - status      : resolved | open | closed_unresolved
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

N_USERS = 8_000
START = pd.Timestamp("2024-07-01")
END = pd.Timestamp("2025-12-31")
WINDOW_DAYS = (END - START).days

# Category -> (share, priority mix, resolution-hours mean).
CATEGORIES = {
    "kyc": (0.18, {"low": 0.10, "medium": 0.50, "high": 0.35, "urgent": 0.05}, 30.0),
    "card": (0.22, {"low": 0.20, "medium": 0.50, "high": 0.25, "urgent": 0.05}, 20.0),
    "app": (0.16, {"low": 0.30, "medium": 0.50, "high": 0.15, "urgent": 0.05}, 12.0),
    "fraud": (0.10, {"low": 0.00, "medium": 0.10, "high": 0.50, "urgent": 0.40}, 6.0),
    "billing": (0.20, {"low": 0.30, "medium": 0.50, "high": 0.15, "urgent": 0.05}, 24.0),
    "account": (0.14, {"low": 0.40, "medium": 0.40, "high": 0.15, "urgent": 0.05}, 18.0),
}
CATEGORY_NAMES = list(CATEGORIES)
CATEGORY_SHARE = np.array([v[0] for v in CATEGORIES.values()])
CATEGORY_SHARE = CATEGORY_SHARE / CATEGORY_SHARE.sum()

CHANNELS = ["in_app_chat", "email", "phone"]
CHANNEL_WEIGHTS = [0.55, 0.30, 0.15]

# Resolution hours and CSAT mean by priority (urgent resolved fast -> higher CSAT).
PRIORITY_HOURS = {"low": 48.0, "medium": 18.0, "high": 6.0, "urgent": 2.0}
PRIORITY_CSAT = {"low": 3.6, "medium": 3.9, "high": 4.2, "urgent": 4.4}


def load_ticket_counts() -> np.ndarray:
    """Per-user ticket counts from the churn dataset's ``support_tickets``.

    The churn generator draws ``support_tickets`` per customer (SEED=42); this
    ledger materialises those counts as actual tickets, so the two datasets
    agree and the CS→churn analysis sees the same signal the churn model uses.
    """
    churn = pd.read_csv(DATA_DIR / "volta_churn_data.csv")
    counts = (
        churn.set_index("customer_id")["support_tickets"]
        .reindex(range(N_USERS))
        .fillna(0)
        .astype(int)
    )
    return counts.to_numpy()


def generate_tickets() -> pd.DataFrame:
    rng = RNG
    # Ticket count per user comes from the churn dataset's support_tickets
    # feature (ground truth behind it), not an independent draw.
    n_tickets = load_ticket_counts()

    rows: list[dict] = []
    ticket_id = 0
    for user_id, count in enumerate(n_tickets):
        for _ in range(count):
            cat = rng.choice(CATEGORY_NAMES, p=CATEGORY_SHARE)
            _, prio_mix, _ = CATEGORIES[cat]
            priority = rng.choice(list(prio_mix), p=list(prio_mix.values()))
            created = START + pd.to_timedelta(rng.uniform(0, WINDOW_DAYS), unit="D")
            status = rng.choice(["resolved", "open", "closed_unresolved"], p=[0.85, 0.08, 0.07])
            resolved = np.nan
            csat = np.nan
            if status == "resolved":
                hours = float(
                    np.clip(rng.lognormal(np.log(PRIORITY_HOURS[priority]), 0.6), 0.1, 720)
                )
                resolved = created + pd.to_timedelta(hours, unit="h")
                if rng.random() < 0.7:
                    csat = int(np.clip(round(rng.normal(PRIORITY_CSAT[priority], 0.7)), 1, 5))
            rows.append(
                {
                    "ticket_id": ticket_id,
                    "user_id": user_id,
                    "created_at": created,
                    "resolved_at": resolved,
                    "category": cat,
                    "priority": priority,
                    "channel": rng.choice(CHANNELS, p=CHANNEL_WEIGHTS),
                    "csat_score": csat,
                    "status": status,
                }
            )
            ticket_id += 1

    df = pd.DataFrame(rows)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["resolved_at"] = pd.to_datetime(df["resolved_at"])
    return df.sort_values("created_at").reset_index(drop=True)


def main() -> None:
    df = generate_tickets()
    out = DATA_DIR / "volta_support_tickets.csv"
    df.to_csv(out, index=False)
    print(f"Generated {len(df):,} tickets -> {out}")


if __name__ == "__main__":
    main()
