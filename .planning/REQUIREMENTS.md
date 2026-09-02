# Requirements: Volta Banking — Analytics Extension

**Defined:** 2026-05-02
**Core Value:** Employers can read and run each script independently to see end-to-end analytical thinking, from business question through data generation to insight and visualization.

## v1 Requirements

### Churn Prediction

- [ ] **CHURN-01**: Script generates synthetic fintech user data (demographics, engagement, financial behavior) with a ~20% churn rate
- [ ] **CHURN-02**: Data is split into train/test with stratification; features are scaled/encoded using scikit-learn transformers
- [ ] **CHURN-03**: At least two models are trained and compared (e.g., Logistic Regression, Random Forest)
- [ ] **CHURN-04**: Model performance is reported with ROC-AUC, precision, recall, and F1-score for each model
- [ ] **CHURN-05**: Top feature importances are visualized and interpreted in business terms
- [ ] **CHURN-06**: A confusion matrix and ROC curve are plotted for the best-performing model

### RFM Analysis

- [ ] **RFM-01**: Script generates synthetic transaction data with customer_id, order_date, and amount
- [ ] **RFM-02**: Recency, Frequency, and Monetary values are computed per customer using pandas groupby
- [ ] **RFM-03**: RFM scores are assigned using quantile-based scoring (rank-first to avoid edge cases)
- [ ] **RFM-04**: Customers are segmented into at least 5 business-meaningful groups (e.g., Champions, At-Risk, Hibernating, New, Regulars)
- [ ] **RFM-05**: Segment distribution and average R/F/M per segment are visualized
- [ ] **RFM-06**: A summary table of recommended actions per segment is printed

### CLV Modeling

- [ ] **CLV-01**: Script generates synthetic transaction history data with customer_id, date, and revenue
- [ ] **CLV-02**: Historical CLV is computed as total revenue per customer
- [ ] **CLV-03**: Predictive CLV is estimated using observed purchase frequency × average order value × expected lifespan
- [ ] **CLV-04**: Probabilistic CLV is approximated using simplified BG/NBD expected transactions × Gamma-Gamma expected value (no external CLV library)
- [ ] **CLV-05**: Distribution comparison of the three CLV methods is visualized (histograms or box plots)
- [ ] **CLV-06**: Top 10 customers by probabilistic CLV are ranked and displayed

### Marketing Attribution

- [ ] **ATTR-01**: Script generates synthetic multi-touch journey data (user_id, touchpoints, channel, timestamp, converted)
- [ ] **ATTR-02**: Last Touch attribution weights are computed per channel
- [ ] **ATTR-03**: First Touch attribution weights are computed per channel
- [ ] **ATTR-04**: Linear attribution weights are computed per channel
- [ ] **ATTR-05**: Data-driven attribution is computed using a simplified Markov chain removal effect
- [ ] **ATTR-06**: Attribution results across all four models are visualized for comparison (bar chart)

### Anomaly Detection

- [ ] **ANOM-01**: Script generates synthetic daily transaction volume and user activity data with injected known anomalies
- [ ] **ANOM-02**: Z-score method flags anomalies on transaction volume
- [ ] **ANOM-03**: IQR method flags anomalies on transaction volume
- [ ] **ANOM-04**: Isolation Forest flags multivariate anomalies using volume, active users, and average transaction size
- [ ] **ANOM-05**: Time series plot highlights anomalies detected by each method
- [ ] **ANOM-06**: A comparison table shows overlap between statistical and ML detection methods

## v2 Requirements

Deferred to future release.

## v3 Requirements (implemented 2026-09-02)

### Spend Analysis

- [x] **SPEND-01**: Script generates synthetic spend ledger data with category, merchant, channel, status, and country
- [x] **SPEND-02**: Spend share is broken down by category, channel, and top merchants
- [x] **SPEND-03**: Decline rate is computed by category
- [x] **SPEND-04**: Monthly spend trend is visualized (`spend_monthly_trend.png`, `spend_by_category.png`)

### Customer-Support Experience vs Churn

- [x] **CSCHURN-01**: Script joins support tickets with churn data on customer id
- [x] **CSCHURN-02**: Churn rate is computed by ticket volume, unresolved-ticket status, and CSAT band
- [x] **CSCHURN-03**: Support category mix is reported separately for churned vs retained customers
- [x] **CSCHURN-04**: Ticket-volume vs churn relationship is visualized (`cs_churn_by_tickets.png`)

### NPS Trends & Drivers

- [x] **NPS-01**: Script loads survey data with NPS 0–10, driver, and promoter/passive/detractor segment
- [x] **NPS-02**: Monthly NPS and promoter/passive/detractor mix are computed
- [x] **NPS-03**: NPS is broken down by driver and by comment length segment
- [x] **NPS-04**: Monthly trend and driver breakdown are visualized (`nps_monthly_trend.png`, `nps_by_driver.png`)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Interactive dashboard (Streamlit/Dash) | Portfolio is script-based for readability |
| Real API or database integration | Synthetic data only, local execution |
| External CLV/attribution libraries (lifetimes, pymc-marketing, mta) | Keep dependencies minimal; match existing script complexity |
| XGBoost/LightGBM/CatBoost | Extra dependencies beyond scikit-learn; Random Forest is sufficient |
| Unit tests or CI/CD | Not needed for a portfolio/demo repo |
| Shared utility modules | Each script must remain independently runnable |
| Model serialization (joblib/pickle) | Portfolio scripts are one-off demonstrations |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CHURN-01 | Phase 1 | Pending |
| CHURN-02 | Phase 1 | Pending |
| CHURN-03 | Phase 1 | Pending |
| CHURN-04 | Phase 1 | Pending |
| CHURN-05 | Phase 1 | Pending |
| CHURN-06 | Phase 1 | Pending |
| RFM-01 | Phase 2 | Pending |
| RFM-02 | Phase 2 | Pending |
| RFM-03 | Phase 2 | Pending |
| RFM-04 | Phase 2 | Pending |
| RFM-05 | Phase 2 | Pending |
| RFM-06 | Phase 2 | Pending |
| CLV-01 | Phase 3 | Pending |
| CLV-02 | Phase 3 | Pending |
| CLV-03 | Phase 3 | Pending |
| CLV-04 | Phase 3 | Pending |
| CLV-05 | Phase 3 | Pending |
| CLV-06 | Phase 3 | Pending |
| ATTR-01 | Phase 4 | Pending |
| ATTR-02 | Phase 4 | Pending |
| ATTR-03 | Phase 4 | Pending |
| ATTR-04 | Phase 4 | Pending |
| ATTR-05 | Phase 4 | Pending |
| ATTR-06 | Phase 4 | Pending |
| ANOM-01 | Phase 5 | Pending |
| ANOM-02 | Phase 5 | Pending |
| ANOM-03 | Phase 5 | Pending |
| ANOM-04 | Phase 5 | Pending |
| ANOM-05 | Phase 5 | Pending |
| ANOM-06 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 30 total
- v3 requirements: 12 total (3 domains × 4)
- Mapped to phases: 30 + 12
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-02*
*Last updated: 2026-05-02 after initial definition*
