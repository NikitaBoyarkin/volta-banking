"""Generate synthetic NPS survey data for Volta.

Produces ``data/volta_nps_surveys.csv`` — Net Promoter Score responses with a
driver category and comment length. It connects to the retention project: NPS
trends and driver mix explain why retention changed after the KYC fix.

Columns:
  - response_id   : int, unique
  - user_id       : int, 0..N_USERS-1
  - survey_date   : datetime, 2024-07-01 .. 2025-12-31
  - nps_score     : int 0..10
  - driver        : product | fees | app_quality | support | trust | onboarding
  - segment       : promoter | passive | detractor (derived from score)
  - comment_length: int 0..200 (0 = no comment)
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

# Score distribution: ~40% promoters (9-10), ~30% passive (7-8), ~30% detractors (0-6).
SCORES = np.arange(11)
SCORE_WEIGHTS = np.array([0.03, 0.03, 0.04, 0.05, 0.05, 0.05, 0.05, 0.15, 0.15, 0.20, 0.20])

# Driver -> additive score offset (before clipping to 0..10).
DRIVER_OFFSET = {
    "product": 1.5,
    "app_quality": 1.0,
    "trust": 0.5,
    "support": 0.0,
    "onboarding": -0.5,
    "fees": -2.0,
}
DRIVER_NAMES = list(DRIVER_OFFSET)
DRIVER_WEIGHTS = np.array([0.25, 0.20, 0.15, 0.15, 0.10, 0.15])


def score_to_segment(score: int) -> str:
    if score >= 9:
        return "promoter"
    if score >= 7:
        return "passive"
    return "detractor"


def generate_nps() -> pd.DataFrame:
    rng = RNG
    # Each user responds 0..2 times.
    n_responses = np.minimum(rng.poisson(0.9, size=N_USERS).astype(int), 2)

    rows: list[dict] = []
    response_id = 0
    for user_id, count in enumerate(n_responses):
        for _ in range(count):
            driver = rng.choice(DRIVER_NAMES, p=DRIVER_WEIGHTS)
            base = rng.choice(SCORES, p=SCORE_WEIGHTS)
            score = int(np.clip(round(base + DRIVER_OFFSET[driver]), 0, 10))
            # Detractors and promoters write longer comments than passives.
            if score_to_segment(score) == "passive":
                comment_len = int(rng.integers(0, 40))
            else:
                comment_len = int(rng.integers(0, 200))
            rows.append(
                {
                    "response_id": response_id,
                    "user_id": user_id,
                    "survey_date": START + pd.to_timedelta(rng.uniform(0, WINDOW_DAYS), unit="D"),
                    "nps_score": score,
                    "driver": driver,
                    "segment": score_to_segment(score),
                    "comment_length": comment_len,
                }
            )
            response_id += 1

    df = pd.DataFrame(rows)
    df["survey_date"] = pd.to_datetime(df["survey_date"])
    return df.sort_values("survey_date").reset_index(drop=True)


def main() -> None:
    df = generate_nps()
    out = DATA_DIR / "volta_nps_surveys.csv"
    df.to_csv(out, index=False)
    print(f"Generated {len(df):,} NPS responses -> {out}")


if __name__ == "__main__":
    main()
