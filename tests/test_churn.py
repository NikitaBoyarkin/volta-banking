"""Tests for volta_churn_prediction.py."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from volta_churn_prediction import (
    evaluate,
    feature_importance,
    fit_models,
    load_data,
    plot_importance,
    plot_roc,
    prep_features,
)

SEED = 42


def test_load_data_shape() -> None:
    df = load_data()
    assert "churned" in df.columns
    assert len(df) > 0
    assert df.shape[1] > 5


def test_prep_features_drops_id_and_target() -> None:
    df = load_data()
    X, y, names = prep_features(df)
    assert y.shape[0] == len(df)
    assert "churned" not in names
    assert "customer_id" not in names
    # channel is one-hot encoded (drop_first -> one fewer column than categories)
    assert "channel_google_play" in names


def test_fit_models_returns_two_fitted_models() -> None:
    rng = np.random.default_rng(SEED)
    X = rng.normal(size=(200, 5))
    y = (X[:, 0] > 0).astype(int)
    models = fit_models(X, y)
    assert set(models) == {"Logistic Regression", "Random Forest"}
    assert isinstance(models["Logistic Regression"], LogisticRegression)
    assert isinstance(models["Random Forest"], RandomForestClassifier)


def test_evaluate_returns_expected_metrics() -> None:
    rng = np.random.default_rng(SEED)
    X = rng.normal(size=(100, 5))
    y = (X[:, 0] > 0).astype(int)
    models = fit_models(X, y)
    metrics = evaluate(models, X, y)
    assert list(metrics.index) == ["Logistic Regression", "Random Forest"]
    for col in ("ROC-AUC", "Accuracy", "Precision", "Recall", "F1"):
        assert col in metrics.columns
    assert metrics["ROC-AUC"].between(0, 1).all()


def test_feature_importance_returns_top_n_sorted() -> None:
    df = load_data()
    X, y, names = prep_features(df)
    rf = fit_models(X[:500], y[:500])["Random Forest"]
    imp = feature_importance(rf, names, top_n=5)
    assert len(imp) == 5
    assert imp["Importance"].is_monotonic_decreasing
    assert (imp["Importance"] >= 0).all()


def test_rf_beats_lr_on_committed_data() -> None:
    """The core portfolio claim: RF ROC-AUC exceeds LR by >= 0.02 on the data."""
    df = load_data()
    X, y, _ = prep_features(df)
    models = fit_models(X, y)
    metrics = evaluate(models, X, y)
    gap = metrics.loc["Random Forest", "ROC-AUC"] - metrics.loc["Logistic Regression", "ROC-AUC"]
    assert gap >= 0.02


def test_plot_roc_writes_png(tmp_path) -> None:
    df = load_data()
    X, y, _ = prep_features(df)
    models = fit_models(X, y)
    out = plot_roc(models, X, y, tmp_path / "roc.png")
    assert out.exists() and out.stat().st_size > 0


def test_plot_importance_writes_png(tmp_path) -> None:
    imp = pd.DataFrame({"Feature": ["a", "b", "c"], "Importance": [0.5, 0.3, 0.2]})
    out = plot_importance(imp, tmp_path / "imp.png")
    assert out.exists() and out.stat().st_size > 0
