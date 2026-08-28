"""Generate synthetic feature-usage event data for Volta.

Produces ``data/volta_feature_events.csv`` — a product event stream of feature
usage (KYC, card controls, budget, transfers, invest, savings, rewards, ATM
locator). It connects to the funnel and segmentation projects: feature adoption
differs sharply by segment, so the data supports adoption-curve and
feature-to-revenue analysis.

Columns:
  - event_id   : int, unique
  - user_id    : int, 0..N_USERS-1
  - event_date : datetime, 2025-01-01 .. 2025-12-31
  - feature    : kyc | card_control | budget | transfer | invest | savings |
                 rewards | atm_locator
  - session_id : int, groups events from one app session
  - device     : ios | android
  - platform   : app | web
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.common import DATA_DIR

SEED = 42
RNG = np.random.default_rng(SEED)

N_USERS = 8_000
START = pd.Timestamp("2025-01-01")
END = pd.Timestamp("2025-12-31")
WINDOW_DAYS = (END - START).days  # 364

# Segment shares mirror Project 4; per-segment monthly event volume.
SEGMENT_SHARE = {"power": 0.12, "growth": 0.24, "casual": 0.32, "dormant": 0.32}
SEGMENT_EVENTS = {"power": 3.0, "growth": 1.5, "casual": 0.6, "dormant": 0.15}

# Feature -> (share, per-segment affinity multiplier).
FEATURES = {
    "kyc": (0.10, {"power": 0.5, "growth": 0.8, "casual": 1.0, "dormant": 1.5}),
    "card_control": (0.12, {"power": 1.8, "growth": 1.2, "casual": 0.8, "dormant": 0.4}),
    "budget": (0.14, {"power": 1.4, "growth": 1.3, "casual": 0.9, "dormant": 0.3}),
    "transfer": (0.20, {"power": 1.0, "growth": 1.2, "casual": 1.0, "dormant": 0.6}),
    "invest": (0.10, {"power": 2.2, "growth": 1.0, "casual": 0.4, "dormant": 0.1}),
    "savings": (0.12, {"power": 1.8, "growth": 1.1, "casual": 0.7, "dormant": 0.2}),
    "rewards": (0.12, {"power": 1.2, "growth": 1.2, "casual": 1.0, "dormant": 0.5}),
    "atm_locator": (0.10, {"power": 0.6, "growth": 0.8, "casual": 1.2, "dormant": 1.0}),
}
FEATURE_NAMES = list(FEATURES)
FEATURE_SHARE = np.array([v[0] for v in FEATURES.values()])
FEATURE_SHARE = FEATURE_SHARE / FEATURE_SHARE.sum()

DEVICES = ["ios", "android"]
DEVICE_WEIGHTS = [0.55, 0.45]
PLATFORMS = ["app", "web"]
PLATFORM_WEIGHTS = [0.85, 0.15]


def generate_events() -> pd.DataFrame:
    rng = RNG
    segments = rng.choice(list(SEGMENT_SHARE), size=N_USERS, p=list(SEGMENT_SHARE.values()))

    rows: list[dict] = []
    event_id = 0
    session_id = 0
    for user_id, seg in enumerate(segments):
        n_events = rng.poisson(SEGMENT_EVENTS[seg] * WINDOW_DAYS / 30.4)
        if n_events == 0:
            continue
        dates = START + pd.to_timedelta(rng.uniform(0, WINDOW_DAYS, size=n_events), unit="D")
        # Feature mix weighted by segment affinity.
        weights = FEATURE_SHARE * np.array([FEATURES[f][1][seg] for f in FEATURE_NAMES])
        weights = weights / weights.sum()
        feats = rng.choice(FEATURE_NAMES, size=n_events, p=weights)
        for i in range(n_events):
            if i % 3 == 0:
                session_id += 1
            rows.append(
                {
                    "event_id": event_id,
                    "user_id": user_id,
                    "event_date": dates[i],
                    "feature": feats[i],
                    "session_id": session_id,
                    "device": rng.choice(DEVICES, p=DEVICE_WEIGHTS),
                    "platform": rng.choice(PLATFORMS, p=PLATFORM_WEIGHTS),
                }
            )
            event_id += 1

    df = pd.DataFrame(rows)
    df["event_date"] = pd.to_datetime(df["event_date"])
    return df.sort_values("event_date").reset_index(drop=True)


def main() -> None:
    df = generate_events()
    out = DATA_DIR / "volta_feature_events.csv"
    df.to_csv(out, index=False)
    print(f"Generated {len(df):,} feature events -> {out}")


if __name__ == "__main__":
    main()
