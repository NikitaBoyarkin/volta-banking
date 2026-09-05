# Volta Banking — Product Analytics Portfolio

## What This Is

A product analytics portfolio for a fictional fintech neobank ("Volta"). Twelve Python scripts covering the full analytics lifecycle: funnel → A/B experiment → retention → segmentation → churn → RFM → CLV → attribution → anomaly → spend → support-churn → NPS — plus a Market & Jobs product-thinking layer (JTBD audit).

## Core Value

Employers can read and run each script independently to see end-to-end analytical thinking, from business question through data generation to insight and visualization.

## Requirements

### Validated

- ✓ **FUNNEL-01**: Onboarding funnel analysis — `volta_funnel_analysis.py`
- ✓ **ABTEST-01**: KYC progress bar A/B test analysis — `volta_ab_testing.py`
- ✓ **RETAIN-01**: Cohort retention and LTV projection — `volta_retention_analysis.py`
- ✓ **SEGMENT-01**: K-means clustering and monetization strategy — `volta_segmentation.py`
- ✓ **CHURN-01**: Churn prediction with train/test split, feature importance, and model comparison (Logistic Regression vs Random Forest) — `volta_churn_prediction.py`
- ✓ **RFM-01**: RFM (Recency, Frequency, Monetary) analysis with scoring tiers and customer lifecycle segmentation — `volta_rfm_analysis.py`
- ✓ **CLV-01**: Customer Lifetime Value modeling using historical, predictive (retention-curve), and probabilistic (Gamma-Gamma) approaches — `volta_clv_modeling.py`
- ✓ **ATTR-01**: Marketing attribution covering first-touch, last-touch, linear, and data-driven (Shapley value) models — `volta_attribution.py`
- ✓ **ANOM-01**: Anomaly detection using statistical (Z-score, IQR) and ML (Isolation Forest) methods — `volta_anomaly_detection.py`
- ✓ **SPEND-01**: Spend analysis — category/channel/merchant breakdown, decline rate, monthly trend — `volta_spend_analysis.py`
- ✓ **CSCHURN-01**: Customer-support experience vs churn (ticket volume, unresolved, CSAT) — `volta_cs_churn.py`
- ✓ **NPS-01**: NPS trends & drivers (monthly NPS, promoter mix, drivers) — `volta_nps_trends.py`
- ✓ **MARKET-01**: Market & Jobs (JTBD) product-thinking layer — top-5 segments, RAT risks, recommendations (source: `Obsidian/Z-core/AJTBD - Volta Full Audit.md`)

### Active

None — all twelve domains are complete.

### Out of Scope

- Interactive dashboard or web app — portfolio is script/notebook-based for readability (executed `.ipynb` notebooks provided instead)
- Real data integration — synthetic data only, local execution

## Context

- Twelve-project portfolio: four core narrative scripts (funnel/A-B/retention/segmentation) plus eight extensions, with codebase map and CLAUDE.md; Market & Jobs JTBD layer (2026-09-05)
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
| Keep single-file pattern | Portfolio readability — each script tells a complete story | ✓ Done |
| Fresh synthetic data per script | Independence, no hidden dependencies between scripts | ✓ Done |
| Match existing complexity | Consistent employer experience across all twelve scripts | ✓ Done |
| Shared utilities | `utils/common.py` centralizes setup/constants/paths | ✓ Done |
| Separate seeded generators | Reproducible `data/*.csv` + `make data` | ✓ Done |
| Engineering quality | ruff + mypy (new code) + pytest-cov (97%) + pre-commit + CI | ✓ Done |
| Market & Jobs layer | JTBD audit as documentation domain (not a script) | ✓ Done |

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
*Last updated: 2026-09-05 — all twelve domains + Market & Jobs layer validated; engineering + presentation sprints complete; PRD snapshot at `docs/prd.md`*
