# Roadmap: Volta Banking — Analytics Extension

**Project:** Volta Banking Product Analytics Portfolio Extension
**Phases:** 5 | **Requirements:** 30 | **Granularity:** Fine
**Mode:** YOLO | **Parallelization:** Enabled
**Created:** 2026-05-02

---

## Phase Overview

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | Churn Prediction | Build and evaluate churn models on synthetic fintech data | CHURN-01..06 | 4 |
| 2 | RFM Analysis | Segment customers by Recency, Frequency, Monetary value | RFM-01..06 | 4 |
| 3 | CLV Modeling | Estimate customer lifetime value via three methods | CLV-01..06 | 4 |
| 4 | Marketing Attribution | Compare four attribution models across channels | ATTR-01..06 | 4 |
| 5 | Anomaly Detection | Detect unusual transaction patterns with statistical and ML methods | ANOM-01..06 | 4 |

---

## Phase Details

### Phase 1: Churn Prediction

**Goal:** Build and evaluate churn prediction models on synthetic fintech user data, demonstrating end-to-end ML workflow from data generation to model comparison.

**Requirements:** CHURN-01, CHURN-02, CHURN-03, CHURN-04, CHURN-05, CHURN-06

**Success Criteria:**
1. `volta_churn_prediction.py` runs from repo root with `uv run python volta_churn_prediction.py`
2. Script generates `data/volta_churn_data.csv` and prints data shape + class balance
3. Two models are trained; their ROC-AUC scores differ by at least 0.02 (demonstrating model selection value)
4. Feature importance plot clearly shows top 5 drivers of churn

**UI hint:** no

**Dependencies:** None (parallelizable with Phase 2-5)

---

### Phase 2: RFM Analysis

**Goal:** Segment customers into actionable tiers using Recency, Frequency, and Monetary analysis on synthetic transaction data.

**Requirements:** RFM-01, RFM-02, RFM-03, RFM-04, RFM-05, RFM-06

**Success Criteria:**
1. `volta_rfm_analysis.py` runs from repo root with `uv run python volta_rfm_analysis.py`
2. Script generates `data/volta_rfm_transactions.csv` and prints customer count + transaction count
3. At least 5 distinct segments are produced with meaningful labels
4. Bar chart shows segment sizes; heatmap shows average R/F/M per segment

**UI hint:** no

**Dependencies:** None (parallelizable with Phase 1, 3-5)

---

### Phase 3: CLV Modeling

**Goal:** Estimate Customer Lifetime Value using historical, predictive, and probabilistic methods, and compare their distributions.

**Requirements:** CLV-01, CLV-02, CLV-03, CLV-04, CLV-05, CLV-06

**Success Criteria:**
1. `volta_clv_modeling.py` runs from repo root with `uv run python volta_clv_modeling.py`
2. Script generates `data/volta_clv_transactions.csv` and prints customer count + total revenue
3. Three CLV estimates are computed per customer (historical, predictive, probabilistic)
4. Histogram comparison shows all three distributions on one plot; top-10 table is printed

**UI hint:** no

**Dependencies:** None (parallelizable with Phase 1-2, 4-5)

---

### Phase 4: Marketing Attribution

**Goal:** Compare four marketing attribution models (Last Touch, First Touch, Linear, Markov) on synthetic multi-touch journey data.

**Requirements:** ATTR-01, ATTR-02, ATTR-03, ATTR-04, ATTR-05, ATTR-06

**Success Criteria:**
1. `volta_attribution_analysis.py` runs from repo root with `uv run python volta_attribution_analysis.py`
2. Script generates `data/volta_attribution_journeys.csv` and prints journey count + conversion rate
3. All four attribution models produce channel weights that sum to 1.0 (or 100%)
4. Grouped bar chart clearly shows how each model allocates credit differently across channels

**UI hint:** no

**Dependencies:** None (parallelizable with Phase 1-3, 5)

---

### Phase 5: Anomaly Detection

**Goal:** Detect unusual transaction patterns using statistical (Z-score, IQR) and ML (Isolation Forest) methods, with method comparison.

**Requirements:** ANOM-01, ANOM-02, ANOM-03, ANOM-04, ANOM-05, ANOM-06

**Success Criteria:**
1. `volta_anomaly_detection.py` runs from repo root with `uv run python volta_anomaly_detection.py`
2. Script generates `data/volta_daily_metrics.csv` and prints data range + injected anomaly count
3. Time series plot highlights anomalies flagged by each method with distinct markers/colors
4. Comparison table shows overlap counts: Z-score only, IQR only, Isolation Forest only, and consensus (all three)

**UI hint:** no

**Dependencies:** None (parallelizable with Phase 1-4)

---

## Execution Notes

**Parallelization:** All 5 phases are independent — each creates its own synthetic data and produces its own script. They can be executed in any order or in parallel.

**Validation Gate:** After each phase, verify:
- Script runs without errors from repo root
- CSV data file is generated in `data/`
- At least 3 visualizations are produced (saved to PNG or displayed inline)
- Printed summary table contains interpretable business metrics

**Post-Completion:**
- Update `README.md` to list all 9 scripts with execution order
- Ensure `pyproject.toml` dependencies cover all new imports (e.g., `scikit-learn` is already present)

---
*Roadmap created: 2026-05-02*
