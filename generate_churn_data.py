"""Generate synthetic churn data for the Volta churn-prediction project.

Produces `data/volta_churn_data.csv` consumed by `volta_churn_prediction.py`.

The label is driven by a non-linear combination of features (a threshold-like
interaction between inactivity and device errors, plus a linear logistic core),
so a Random Forest measurably beats Logistic Regression — demonstrating model
selection value in the analysis script.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

N_USERS = 15_000
CHANNELS = ["app_store", "google_play", "website", "referral"]


def generate_users(n: int = N_USERS) -> pd.DataFrame:
    rng = RNG
    usage = rng.beta(2, 5, size=n)  # right-skewed: most users low-usage
    tx_value = np.clip(rng.lognormal(mean=3.2, sigma=0.7, size=n), 1, 500)
    inactive_days = rng.integers(0, 90, size=n).astype(float)
    tickets = rng.poisson(0.6, size=n).astype(float)
    error_rate = np.clip(rng.beta(1.5, 20, size=n) * 3, 0, 1)
    age = rng.integers(18, 70, size=n).astype(float)
    premium = rng.binomial(1, 0.18, size=n).astype(float)
    tenure = rng.integers(1, 48, size=n).astype(float)
    channel = rng.choice(CHANNELS, size=n, p=[0.30, 0.30, 0.25, 0.15])

    # Linear logistic core (main effects only -> what Logistic Regression sees).
    logit = (
        -0.6
        - 3.2 * usage
        - 0.004 * tx_value
        + 0.06 * (inactive_days / 90)
        + 0.9 * tickets
        + 2.0 * error_rate
        - 0.5 * premium
        - 0.02 * tenure
        + 0.3 * (channel == "website")
    )
    p = 1 / (1 + np.exp(-logit))

    # Non-linear churn cliff: high inactivity AND high device-error together is
    # a threshold interaction a linear model cannot capture -> RF wins on AUC.
    inactive_norm = np.clip(inactive_days / 90, 0, 1)
    error_norm = np.clip(error_rate, 0, 1)
    cliff = (inactive_norm > 0.5) & (error_norm > 0.2)
    p = np.where(cliff, np.clip(p + 0.55, 0.01, 0.98), p)
    # Low-usage users churn at a boosted rate too (a second non-linear lever).
    p = np.where(usage < 0.12, np.clip(p + 0.22, 0.01, 0.98), p)

    churned = rng.binomial(1, np.clip(p, 0.01, 0.99)).astype(int)

    return pd.DataFrame(
        {
            "customer_id": np.arange(n),
            "usage_frequency": usage.round(4),
            "avg_transaction_value": tx_value.round(2),
            "days_since_last_activity": inactive_days.astype(int),
            "support_tickets": tickets.astype(int),
            "device_error_rate": error_rate.round(4),
            "age": age.astype(int),
            "is_premium": premium.astype(int),
            "customer_tenure_months": tenure.astype(int),
            "channel": channel,
            "churned": churned,
        }
    )


def main() -> None:
    df = generate_users()
    df.to_csv(DATA_DIR / "volta_churn_data.csv", index=False)

    churn_rate = df["churned"].mean()
    print(f"Generated {len(df)} users -> {DATA_DIR / 'volta_churn_data.csv'}")
    print(f"  Shape: {df.shape}")
    print(f"  Class balance: churned={churn_rate:.1%}, retained={1 - churn_rate:.1%}")
    print("\nFeature preview:")
    print(df.head().to_string(index=False))


if __name__ == "__main__":
    main()
