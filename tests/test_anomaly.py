"""Tests for volta_anomaly_detection.py."""

from __future__ import annotations

import numpy as np
import pytest

from volta_anomaly_detection import (
    add_features,
    build_scores,
    evaluate,
    iqr_detector,
    isolation_forest_detector,
    load_data,
    plot_detections,
    zscore_detector,
)


def test_load_data() -> None:
    df = load_data()
    assert {"transaction_id", "user_id", "amount", "is_anomaly"} <= set(df.columns)
    assert len(df) > 0


def test_add_features() -> None:
    df = add_features(load_data())
    assert {"log_amount", "user_tx_count"} <= set(df.columns)
    assert df["log_amount"].ge(0).all()


def test_detectors_return_boolean_mask() -> None:
    df = add_features(load_data())
    for fn in (zscore_detector, iqr_detector):
        mask = fn(df)
        assert isinstance(mask, np.ndarray)
        assert mask.shape == (len(df),)
        assert mask.dtype == bool


def test_isolation_forest_mask() -> None:
    df = add_features(load_data())
    mask = isolation_forest_detector(df, contamination=0.05)
    assert mask.shape == (len(df),)
    assert mask.sum() > 0


def test_evaluate_exact() -> None:
    pred = np.array([True, True, False, False, True])
    truth = np.array([True, False, True, False, True])
    # tp=2 (idx0,4), fp=1 (idx1), fn=1 (idx2)
    res = evaluate(pred, truth)
    assert res["precision"] == pytest.approx(2 / 3)
    assert res["recall"] == pytest.approx(2 / 3)
    assert res["f1"] == pytest.approx(2 / 3)


def test_build_scores_has_three_methods() -> None:
    df = add_features(load_data())
    truth = df["is_anomaly"].to_numpy(dtype=bool)
    scores = build_scores(df, truth)
    assert set(scores.index) == {"Z-score (log-amount)", "IQR (Tukey fences)", "Isolation Forest"}
    for col in ("n_detected", "precision", "recall", "f1"):
        assert col in scores.columns


def test_plot_writes_png(tmp_path) -> None:
    df = add_features(load_data())
    truth = df["is_anomaly"].to_numpy(dtype=bool)
    out = plot_detections(df, truth, tmp_path / "anom.png")
    assert out.exists() and out.stat().st_size > 0
