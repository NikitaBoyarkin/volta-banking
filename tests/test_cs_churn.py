"""Tests for volta_cs_churn.py."""

from __future__ import annotations

import pytest

from volta_cs_churn import (
    category_mix_by_churn,
    churn_by_csat,
    churn_by_ticket_bucket,
    churn_by_unresolved,
    load_churn,
    load_tickets,
    merge_churn,
    plot_churn_by_tickets,
    ticket_features,
)


def test_load_tickets_has_expected_columns() -> None:
    df = load_tickets()
    assert {"ticket_id", "user_id", "created_at", "status", "csat_score"} <= set(df.columns)
    assert len(df) > 0


def test_load_churn_has_label() -> None:
    df = load_churn()
    assert {"customer_id", "churned"} <= set(df.columns)
    assert df["churned"].isin([0, 1]).all()


def test_ticket_features_aggregates() -> None:
    feats = ticket_features(load_tickets())
    assert {"n_tickets", "n_unresolved", "avg_csat"} <= set(feats.columns)
    assert (feats["n_tickets"] >= feats["n_unresolved"]).all()


def test_merge_churn_fills_zero_for_no_tickets() -> None:
    merged = merge_churn(load_tickets(), load_churn())
    assert len(merged) == len(load_churn())
    assert merged["n_tickets"].isna().sum() == 0
    assert merged["n_unresolved"].isna().sum() == 0


def test_churn_by_ticket_bucket_buckets() -> None:
    merged = merge_churn(load_tickets(), load_churn())
    bucket = churn_by_ticket_bucket(merged)
    assert list(bucket.index) == ["0", "1", "2", "3+"]
    assert bucket["churn_rate"].between(0, 100).all()


def test_churn_by_unresolved_buckets() -> None:
    merged = merge_churn(load_tickets(), load_churn())
    bucket = churn_by_unresolved(merged)
    assert list(bucket.index) == ["0", "1", "2+"]
    assert bucket["churn_rate"].between(0, 100).all()


def test_churn_by_csat_bands() -> None:
    merged = merge_churn(load_tickets(), load_churn())
    g = churn_by_csat(merged)
    assert set(g.index) == {"1-2", "3", "4", "5"}
    assert g["churn_rate"].between(0, 100).all()


def test_category_mix_rows_sum_to_100() -> None:
    mix = category_mix_by_churn(load_tickets(), load_churn())
    assert set(mix.index) == {"retained", "churned"}
    # Six rounded percentages can sum to 100.1; allow rounding slack.
    assert mix.sum(axis=1).apply(lambda s: s == pytest.approx(100, abs=0.5)).all()


def test_plot_churn_by_tickets_writes_png(tmp_path) -> None:
    merged = merge_churn(load_tickets(), load_churn())
    bucket = churn_by_ticket_bucket(merged)
    out = plot_churn_by_tickets(bucket, tmp_path / "churn.png")
    assert out.exists() and out.stat().st_size > 0
