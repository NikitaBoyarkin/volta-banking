"""Generate synthetic unit-economics data for the Volta traveler segment.

Produces `volta_unit_economics.csv` consumed by `volta_unit_economics.py`:

  user_id, segment, currency, tx_type, amount_eur, revenue_eur, cost_eur,
  margin_eur

Design — transaction-level economics across five JTBD segments. The traveler
segment is the risk-#1 focus: high volume, multi-currency, thin FX spread
("honest rate" job) but real FX cost. Per-€100 FX transaction:

  revenue = spread 0.4% + interchange 0.3% = €0.70
  cost    = FX cost 1.0% + processing + support = €1.15
  margin  = −€0.45   ← negative

Other segments transact mostly in EUR where interchange covers cost:

  revenue = interchange 0.3% + €0.05 = €0.35
  cost    = funding 0.1% + processing = €0.12
  margin  = +€0.23   ← positive

So travelers lose money per transaction and the loss scales with volume —
the audit's risk #1 ("unit economics breaks at scale").

Run from the repo root:
    uv run python generate_unit_economics_data.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

FX_CURRENCIES = ["USD", "GBP", "THB", "JPY"]

# (segment, n_users, tx_per_month, avg_amount_eur, fx_share)
SEGMENT_SPECS: list[tuple[str, int, float, float, float]] = [
    ("travelers", 1000, 25.0, 120.0, 0.90),
    ("young_professionals", 1000, 15.0, 60.0, 0.15),
    ("family_budgeters", 800, 12.0, 45.0, 0.05),
    ("digital_newcomers", 500, 6.0, 30.0, 0.05),
    ("premium_status", 300, 20.0, 150.0, 0.20),
]


def tx_economics(tx_type: str, amount: float) -> tuple[float, float]:
    """Revenue and cost (EUR) for one transaction.

    fx:       spread 0.4% + interchange 0.3% vs FX cost 1.0% + processing + support
    card:     interchange 0.3% + €0.05 vs funding 0.1% + processing
    atm:      free for travelers (revenue 0) vs network fee €0.80
    transfer: flat €0.50 vs €0.15
    """
    if tx_type == "fx":
        revenue = 0.004 * amount + 0.003 * amount
        cost = 0.010 * amount + 0.05 + 0.10
    elif tx_type == "card":
        revenue = 0.003 * amount + 0.05
        cost = 0.001 * amount + 0.02
    elif tx_type == "atm":
        revenue = 0.0
        cost = 0.80
    else:  # transfer
        revenue = 0.50
        cost = 0.15
    return revenue, cost


def generate_transactions() -> pd.DataFrame:
    """One month of transactions for a sample of users per segment."""
    rows: list[dict[str, float | str | int]] = []
    user_id = 0
    for segment, n_users, tx_per_month, avg_amount, fx_share in SEGMENT_SPECS:
        for _ in range(n_users):
            user_id += 1
            n_tx = int(RNG.poisson(tx_per_month))
            for _ in range(n_tx):
                is_fx = RNG.random() < fx_share
                currency = RNG.choice(FX_CURRENCIES) if is_fx else "EUR"
                tx_type = (
                    "fx" if is_fx else RNG.choice(["card", "atm", "transfer"], p=[0.9, 0.05, 0.05])
                )
                amount = max(1.0, float(RNG.normal(avg_amount, avg_amount * 0.3)))
                revenue, cost = tx_economics(tx_type, amount)
                revenue *= float(RNG.normal(1.0, 0.05))
                cost *= float(RNG.normal(1.0, 0.05))
                rows.append(
                    {
                        "user_id": user_id,
                        "segment": segment,
                        "currency": currency,
                        "tx_type": tx_type,
                        "amount_eur": round(amount, 2),
                        "revenue_eur": round(revenue, 4),
                        "cost_eur": round(cost, 4),
                        "margin_eur": round(revenue - cost, 4),
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    df = generate_transactions()
    df.to_csv(DATA_DIR / "volta_unit_economics.csv", index=False)

    print(f"Generated {len(df):,} transactions across {df['segment'].nunique()} segments")
    print("Wrote: volta_unit_economics.csv")
    print("\nMargin per transaction by segment (EUR):")
    g = df.groupby("segment")["margin_eur"].mean().round(4)
    print(g.to_string())


if __name__ == "__main__":
    main()
