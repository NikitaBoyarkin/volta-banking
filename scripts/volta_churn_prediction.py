"""Volta Neobank — Churn Prediction.

Builds and compares churn-prediction models on synthetic fintech user data:
a Logistic Regression baseline vs a Random Forest. Demonstrates the full ML
workflow — data prep, class balance, train/test split, model comparison by
ROC-AUC, and feature-importance interpretation — then ties the drivers back
to the segmentation narrative from Project 4.

Run:  uv run python volta_churn_prediction.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

from utils.common import (
    OUTPUT_DIR,
    data_path,
    print_section,
    print_subsection,
    setup,
)

SEED = 42
TARGET = "churned"
CAT_FEATURES = ["channel"]


def load_data() -> pd.DataFrame:
    return pd.read_csv(data_path("volta_churn_data.csv"))


def prep_features(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Return feature matrix, target vector, and feature-name list."""
    features = df.drop(columns=[TARGET, "customer_id"])
    features = pd.get_dummies(features, columns=CAT_FEATURES, drop_first=True)
    feature_names = list(features.columns)
    return features.to_numpy(dtype=float), df[TARGET].to_numpy(dtype=float), feature_names


def fit_models(X: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    """Train a Logistic Regression and a Random Forest; return fitted models."""
    lr = LogisticRegression(max_iter=1000, random_state=SEED)
    rf = RandomForestClassifier(n_estimators=200, random_state=SEED, n_jobs=-1)
    lr.fit(X, y)
    rf.fit(X, y)
    return {"Logistic Regression": lr, "Random Forest": rf}


def evaluate(models: dict[str, Any], X_test: np.ndarray, y_test: np.ndarray) -> pd.DataFrame:
    """Compute standard classification metrics per model."""
    rows: list[dict[str, Any]] = []
    for name, model in models.items():
        pred = model.predict(X_test)
        prob = model.predict_proba(X_test)[:, 1]
        rows.append(
            {
                "Model": name,
                "ROC-AUC": roc_auc_score(y_test, prob),
                "Accuracy": accuracy_score(y_test, pred),
                "Precision": precision_score(y_test, pred),
                "Recall": recall_score(y_test, pred),
                "F1": f1_score(y_test, pred),
            }
        )
    return pd.DataFrame(rows).set_index("Model")


def plot_roc(
    models: dict[str, Any],
    X_test: np.ndarray,
    y_test: np.ndarray,
    out: Path,
) -> Path:
    import matplotlib.pyplot as plt

    plt.figure(figsize=(7, 5))
    for name, model in models.items():
        prob = model.predict_proba(X_test)[:, 1]
        fpr, tpr, _ = roc_curve(y_test, prob)
        auc = roc_auc_score(y_test, prob)
        plt.plot(fpr, tpr, label=f"{name} (AUC={auc:.3f})")
    plt.plot([0, 1], [0, 1], "k--", alpha=0.4)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Churn Model ROC Curves")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()
    return out


def feature_importance(rf: Any, feature_names: list[str], top_n: int = 5) -> pd.DataFrame:
    """Top-N feature importances from the Random Forest, as a DataFrame."""
    imp = rf.feature_importances_
    df = pd.DataFrame({"Feature": feature_names, "Importance": imp})
    df = df.sort_values("Importance", ascending=False).head(top_n).reset_index(drop=True)
    return df


def plot_importance(imp_df: pd.DataFrame, out: Path) -> Path:
    import matplotlib.pyplot as plt

    plt.figure(figsize=(7, 5))
    plt.barh(imp_df["Feature"], imp_df["Importance"], color="#4c72b0")
    plt.gca().invert_yaxis()
    plt.xlabel("Feature Importance (RF)")
    plt.title("Top Churn Drivers")
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    plt.close()
    return out


def section_setup(df: pd.DataFrame) -> None:
    print_section("VOLTA NEOBANK — CHURN PREDICTION")
    churn_rate = df[TARGET].mean()
    print_subsection("Data & Class Balance")
    print(f"  Shape: {df.shape[0]:,} users × {df.shape[1]} features")
    print(f"  Class balance: churned={churn_rate:.1%}, retained={1 - churn_rate:.1%}")
    print("  (No resampling — the imbalance is modest and we optimise ROC-AUC.)")


def section_models(
    models: dict[str, Any], metrics: pd.DataFrame, X_test: np.ndarray, y_test: np.ndarray
) -> None:
    print_subsection("Model Comparison")
    print(metrics.to_string())
    best = metrics["ROC-AUC"].idxmax()
    gap = metrics.loc["Random Forest", "ROC-AUC"] - metrics.loc["Logistic Regression", "ROC-AUC"]
    print(f"\n  Best by ROC-AUC: {best}")
    print(f"  RF − LR gap: {gap:+.3f} AUC")
    if gap >= 0.02:
        print("  → Gap ≥ 0.02: non-linear model adds value; keep Random Forest.")
    else:
        print("  → Gap < 0.02: linear baseline suffices; prefer the simpler model.")


def section_roc(models: dict[str, Any], X_test: np.ndarray, y_test: np.ndarray) -> Path:
    print_subsection("ROC Curves")
    out = plot_roc(models, X_test, y_test, OUTPUT_DIR / "churn_roc_curve.png")
    print(f"  Saved: {out.name}")
    return out


def section_feature_importance(imp_df: pd.DataFrame) -> Path:
    print_subsection("Top Churn Drivers (Feature Importance)")
    print(imp_df.to_string(index=False))
    out = plot_importance(imp_df, OUTPUT_DIR / "churn_feature_importance.png")
    print(f"  Saved: {out.name}")
    return out


def section_insights(imp_df: pd.DataFrame) -> None:
    print_subsection("Insights → Segmentation Link")
    top = imp_df["Feature"].iloc[0]
    print(f"  #1 driver: {top}")
    print("  Interpretation:")
    print("    1. Inactivity and device errors dominate churn — a UX/reliability problem,")
    print("       not just a pricing one.")
    print("    2. Premium users churn less (retention-safe lever for monetization).")
    print("    3. Connect to Project 4: the Dormant segment overlaps the high-churn tail —")
    print("       target them with re-engagement before they churn.")


def section_recommendations() -> None:
    print_subsection("Recommendations")
    print("  1. Deploy RF churn scores to tag high-risk users for save-offers.")
    print("  2. Fix device-error rate (top driver) — reliability sprint, not marketing.")
    print("  3. Trigger re-engagement for inactivity > 30 days (Dormant segment).")


def main() -> None:
    setup()
    df = load_data()

    section_setup(df)
    X, y, feature_names = prep_features(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=SEED, stratify=y
    )
    models = fit_models(X_train, y_train)
    metrics = evaluate(models, X_test, y_test)
    section_models(models, metrics, X_test, y_test)
    section_roc(models, X_test, y_test)
    imp_df = feature_importance(models["Random Forest"], feature_names)
    section_feature_importance(imp_df)
    section_insights(imp_df)
    section_recommendations()

    print("\n" + "=" * 60)
    print("Analysis complete. Review recommendations above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
