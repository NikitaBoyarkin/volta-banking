# Project State: Volta Banking — Analytics Extension

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-05-02)

**Core value:** Employers can read and run each script independently to see end-to-end analytical thinking, from business question through data generation to insight and visualization.
**Current focus:** All phases complete — maintenance + engineering layer active.

---

## Phase Status

| Phase | Status | Requirements | Notes |
|-------|--------|--------------|-------|
| 1 — Churn Prediction | ✅ Complete | CHURN-01..06 | RF beats LR by +0.03 ROC-AUC |
| 2 — RFM Analysis | ✅ Complete | RFM-01..06 | 6 lifecycle segments |
| 3 — CLV Modeling | ✅ Complete | CLV-01..06 | 3 methods (historical/retention/Gamma-Gamma) |
| 4 — Marketing Attribution | ✅ Complete | ATTR-01..06 | 4 models incl. Shapley |
| 5 — Anomaly Detection | ✅ Complete | ANOM-01..06 | Z-score/IQR/Isolation Forest |

---

## Milestones

| Milestone | Target | Status |
|-----------|--------|--------|
| v1 — Five New Scripts Complete | All 5 phases done | ✅ Complete |
| v2 — Engineering + Presentation | ruff/mypy/cov/pre-commit/notebooks/deck | ✅ Complete |

---

## Active Decisions

| Decision | Status | Notes |
|----------|--------|-------|
| Single-file pattern | ✓ Confirmed | Each script self-contained |
| Fresh synthetic data per script | ✓ Confirmed | Generators write to `data/`, `make data` |
| Shared utilities | ✓ Confirmed | `utils/common.py` (setup, CONSTANTS, data_path, OUTPUT_DIR) |
| scikit-learn only (no XGBoost) | ✓ Confirmed | Churn uses LR vs RandomForest |
| No external CLV/attribution libraries | ✓ Confirmed | Inline Gamma-Gamma + Shapley |
| Engineering layer | ✓ Done | ruff, mypy (new code), pytest-cov 97%, pre-commit, CI |
| Presentation layer | ✓ Done | README charts, executed notebooks, executive deck |
| Market & Jobs layer | ✓ Done | JTBD audit (segments + RAT) as documentation domain |

---

## Blockers

None.

---
*State updated: 2026-09-05*
*Next update: On new phase or major change*
