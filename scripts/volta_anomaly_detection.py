"""Volta Neobank — Transaction Anomaly Detection.

Detects unusual transactions with three methods and scores them against the
generator's ground-truth labels (precision / recall / F1):
  - Z-score      : |z| on log-amount beyond a threshold
  - IQR          : amount beyond Tukey's fences (Q3 + 1.5*IQR)
  - Isolation Forest : unsupervised on [log_amount, hour, user velocity]

Run:  uv run python volta_anomaly_detection.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from utils.common import OUTPUT_DIR, data_path, print_section, print_subsection, setup

Z_THRESH = 3.0


def load_data() -> pd.DataFrame:
    df = pd.read_csv(data_path("volta_anomaly_transactions.csv"), parse_dates=["tx_time"])
    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["log_amount"] = np.log1p(out["amount"])
    out["user_tx_count"] = out["user_id"].map(out["user_id"].value_counts())
    return out


def zscore_detector(df: pd.DataFrame) -> np.ndarray:
    z = (df["log_amount"] - df["log_amount"].mean()) / df["log_amount"].std()
    return (z.abs() > Z_THRESH).to_numpy(dtype=bool)


def iqr_detector(df: pd.DataFrame) -> np.ndarray:
    q1, q3 = df["log_amount"].quantile([0.25, 0.75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return ((df["log_amount"] < lower) | (df["log_amount"] > upper)).to_numpy(dtype=bool)


def isolation_forest_detector(df: pd.DataFrame, contamination: float, seed: int = 42) -> np.ndarray:
    feats = ["log_amount", "hour", "user_tx_count"]
    X = StandardScaler().fit_transform(df[feats].to_numpy(dtype=float))
    iso = IsolationForest(contamination=contamination, random_state=seed, n_jobs=-1)
    pred = iso.fit_predict(X)
    return (pred == -1).astype(bool)


def evaluate(pred: np.ndarray, truth: np.ndarray) -> dict[str, float]:
    tp = int(np.sum(pred & truth))
    fp = int(np.sum(pred & ~truth))
    fn = int(np.sum(~pred & truth))
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def build_scores(df: pd.DataFrame, truth: np.ndarray) -> pd.DataFrame:
    truth_bool = truth.astype(bool)
    contamination = float(truth.mean())
    scores = {
        "Z-score (log-amount)": evaluate(zscore_detector(df), truth_bool),
        "IQR (Tukey fences)": evaluate(iqr_detector(df), truth_bool),
        "Isolation Forest": evaluate(isolation_forest_detector(df, contamination), truth_bool),
    }
    table = pd.DataFrame(scores).T.round(3)
    table.insert(
        0,
        "n_detected",
        [
            np.sum(zscore_detector(df)),
            np.sum(iqr_detector(df)),
            np.sum(isolation_forest_detector(df, contamination)),
        ],
    )
    return table


def plot_detections(df: pd.DataFrame, truth: np.ndarray, out: Path) -> Path:
    plt.figure(figsize=(9, 5))
    normal = df[~truth]
    anom = df[truth]
    plt.scatter(normal["hour"], normal["amount"], s=4, alpha=0.25, label="Normal")
    plt.scatter(anom["hour"], anom["amount"], s=10, alpha=0.7, c="#d62728", label="Anomaly (truth)")
    plt.yscale("log")
    plt.xlabel("Hour of day")
    plt.ylabel("Amount (EUR, log)")
    plt.title("Transactions by Hour — Ground-Truth Anomalies")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()
    return out


def section_setup(df: pd.DataFrame) -> None:
    print_section("VOLTA NEOBANK — TRANSACTION ANOMALY DETECTION")
    print_subsection("Data")
    print(f"  Transactions: {len(df):,}")
    print(f"  Users:        {df['user_id'].nunique():,}")
    print(f"  Ground-truth anomaly rate: {df['is_anomaly'].mean():.1%}")


def section_scores(scores: pd.DataFrame) -> None:
    print_subsection("Detector Performance (vs ground truth)")
    print(scores.to_string())
    print("\n  Reading: Precision = flagged that were truly anomalous; Recall = share")
    print("  of true anomalies caught. Isolation Forest balances both; a single")
    print("  Z-score on amount alone under-recalls because some anomalies are")
    print("  'small but unusual-in-time' rather than huge.")


def section_insight() -> None:
    print_subsection("Recommendations")
    print("  1. Use Isolation Forest as the primary real-time scorer.")
    print("  2. Keep the amount Z-score as a cheap, interpretable first filter.")
    print("  3. Review flags by velocity + amount; route to fraud team with context.")


def main() -> None:
    setup()
    df = load_data()
    section_setup(df)
    feats = add_features(df)
    truth = feats["is_anomaly"].to_numpy(dtype=bool)
    scores = build_scores(feats, truth)
    section_scores(scores)
    section_insight()
    out = plot_detections(feats, truth, OUTPUT_DIR / "anomaly_detections.png")
    print(f"  Saved: {out.name}")

    print("\n" + "=" * 60)
    print("Analysis complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
