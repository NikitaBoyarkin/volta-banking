# Volta Banking — Product Analytics Portfolio

## What This Is

A product analytics portfolio for a fictional fintech neobank ("Volta"). Originally four sequential Python analysis scripts, now expanding to nine scripts covering the full analytics lifecycle: funnel → experiment → retention → segmentation → churn → RFM → CLV → attribution → anomaly.

## Core Value

Employers can read and run each script independently to see end-to-end analytical thinking, from business question through data generation to insight and visualization.

## Requirements

### Validated

- ✓ **FUNNEL-01**: Onboarding funnel analysis — `volta_funnel_analysis.py` (existing)
- ✓ **ABTEST-01**: KYC progress bar A/B test analysis — `volta_ab_testing.py` (existing)
- ✓ **RETAIN-01**: Cohort retention and LTV projection — `volta_retention_analysis.py` (existing)
- ✓ **SEGMENT-01**: K-means clustering and monetization strategy — `volta_segmentation.py` (existing)

### Active

- [ ] **CHURN-01**: Churn prediction with train/test split, feature importance, and model comparison (Random Forest vs XGBoost vs Logistic Regression)
- [ ] **RFM-01**: RFM (Recency, Frequency, Monetary) analysis with scoring tiers and customer lifecycle segmentation
- [ ] **CLV-01**: Customer Lifetime Value modeling using historical, predictive, and probabilistic (BG/NBD + Gamma-Gamma) approaches
- [ ] **ATTR-01**: Marketing attribution analysis covering last-touch, first-touch, linear, and data-driven (Shapley value) models
- [ ] **ANOM-01**: Anomaly detection across transaction volume and user activity using statistical (Z-score, IQR) and ML (Isolation Forest) methods

### Out of Scope

- Interactive dashboard or web app — portfolio is script-based for readability
- Real data integration — synthetic data only, local execution
- CI/CD or test suite — not needed for a portfolio/demo repo
- Shared utilities / package structure — each script remains self-contained

## Context

- Brownfield project: existing codebase with four working scripts, codebase map, and CLAUDE.md
- Target audience: hiring managers evaluating analytical Python skills
- Consistent style: dark-themed matplotlib, pandas + scikit-learn, synthetic CSV generation inline, print statements for progress
- Each script independently executable from repo root via `uv run python volta_*.py`

## Constraints

- **Tech stack**: Python 3.10+, pandas, numpy, matplotlib, seaborn, scikit-learn, scipy — must stay consistent with existing scripts
- **Complexity**: Match existing scripts (single-file, ~200-400 lines, inline data generation, 3-5 visualizations, printed summary table)
- **Data**: Synthetic only; generate within each script, save to CSV for reproducibility
- **Timeline**: Portfolio extension, not production system

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep single-file pattern | Portfolio readability — each script tells a complete story | — Pending |
| Fresh synthetic data per script | Independence, no hidden dependencies between scripts | — Pending |
| Match existing complexity | Consistent employer experience across all nine scripts | — Pending |
| No shared utilities | Each script must be runnable after a single `git clone` | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-01 after initialization*
