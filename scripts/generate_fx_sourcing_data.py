"""Generate synthetic FX-sourcing quotes for the Volta traveler segment.

Produces `volta_fx_sourcing.csv` consumed by `volta_fx_sourcing.py`:

  provider_id, provider_name, monthly_volume_eur, term_months, quoted_cost_pct,
  hedging_cost_pct, effective_cost_pct, settlement_days, credit_rating

Design — the audit's v2 risk #2: "FX cost can't be negotiated to <=0.55%, so
travelers never scale". Project 14 (traveler unit economics) showed the
break-even FX cost is 0.55% against a current 1.0%. This dataset asks the
supply-side question: is 0.55% actually buyable, and at what volume?

Each row is a quote from one liquidity provider at one monthly-volume tier and
one commitment term. The quoted interbank cost falls log-linearly with volume
(volume tiers) and the hedging cost falls with term length (commitment), so the
effective cost is a function of both:

  effective_cost = quoted_cost + hedging_cost
  quoted_cost    = base - slope * log10(volume_eur / 1e6) + noise
  hedging_cost   = term_hedge[term_months] + noise

Provider base levels and volume slopes differ, so the best provider depends on
scale — the analysis must find the volume at which the gate (0.55%) is
reachable and which provider/term gets there.

Run from the repo root:
    uv run python generate_fx_sourcing_data.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

# Monthly-volume tiers a neobank can aggregate (EUR). SOM-scale is ~500M.
VOLUME_TIERS = [1e6, 2.5e6, 5e6, 1e7, 2.5e7, 5e7, 1e8, 2.5e8, 5e8]
TERM_OPTIONS = [1, 6, 12]  # commitment months

# Hedging cost by commitment term (% of notional). Longer term = cheaper hedge
# but more commitment risk.
TERM_HEDGE: dict[int, float] = {1: 0.120, 6: 0.080, 12: 0.050}

# (provider, base_quoted_pct, slope_per_decade, settlement_days, credit_rating)
PROVIDER_SPECS: list[tuple[str, float, float, int, str]] = [
    ("Interbank Prime", 1.080, 0.230, 1, "AAA"),
    ("Fintech Liquidity", 1.100, 0.200, 2, "AA"),
    ("Global FX Desk", 1.180, 0.210, 2, "AA"),
    ("Prime Broker A", 1.150, 0.215, 1, "A"),
    ("Regional Bank", 1.250, 0.190, 3, "A"),
    ("Aggregator X", 1.300, 0.170, 3, "BBB"),
]

PROVIDER_NAMES = [p for p, _, _, _, _ in PROVIDER_SPECS]
# Gate from Project 14: FX cost must fall 1.0% -> 0.55% to break even.
GATE_FX_COST_PCT = 0.55


def quoted_cost(base: float, slope: float, volume: float) -> float:
    """Interbank quoted cost (%) at a given monthly volume."""
    return base - slope * np.log10(volume / 1e6)


def generate_quotes() -> pd.DataFrame:
    """One row per provider × volume tier × term option."""
    rows: list[dict[str, float | str | int]] = []
    provider_id = 0
    for provider, base, slope, settle, rating in PROVIDER_SPECS:
        provider_id += 1
        for volume in VOLUME_TIERS:
            for term in TERM_OPTIONS:
                quoted = quoted_cost(base, slope, volume) * float(RNG.normal(1.0, 0.01))
                hedging = TERM_HEDGE[term] * float(RNG.normal(1.0, 0.03))
                rows.append(
                    {
                        "provider_id": provider_id,
                        "provider_name": provider,
                        "monthly_volume_eur": volume,
                        "term_months": term,
                        "quoted_cost_pct": round(quoted, 4),
                        "hedging_cost_pct": round(hedging, 4),
                        "effective_cost_pct": round(quoted + hedging, 4),
                        "settlement_days": settle,
                        "credit_rating": rating,
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    df = generate_quotes()
    df.to_csv(DATA_DIR / "volta_fx_sourcing.csv", index=False)

    print(f"Generated {len(df):,} quotes across {df['provider_name'].nunique()} providers")
    print("Wrote: volta_fx_sourcing.csv")

    print("\nBest effective cost (%) by volume tier (any provider, any term):")
    best = df.groupby("monthly_volume_eur")["effective_cost_pct"].min().round(3)
    print(best.to_string())

    print(f"\nGate: effective FX cost <= {GATE_FX_COST_PCT:.2f}% (from Project 14 break-even).")


if __name__ == "__main__":
    main()
