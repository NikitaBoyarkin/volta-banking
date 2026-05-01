# Project State: Volta Banking — Analytics Extension

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-05-02)

**Core value:** Employers can read and run each script independently to see end-to-end analytical thinking, from business question through data generation to insight and visualization.
**Current focus:** Phase 1 — Churn Prediction

---

## Phase Status

| Phase | Status | Requirements | Notes |
|-------|--------|--------------|-------|
| 1 — Churn Prediction | 🔵 Not Started | CHURN-01..06 | Independent — can run in parallel with other phases |
| 2 — RFM Analysis | 🔵 Not Started | RFM-01..06 | Independent — can run in parallel with other phases |
| 3 — CLV Modeling | 🔵 Not Started | CLV-01..06 | Independent — can run in parallel with other phases |
| 4 — Marketing Attribution | 🔵 Not Started | ATTR-01..06 | Independent — can run in parallel with other phases |
| 5 — Anomaly Detection | 🔵 Not Started | ANOM-01..06 | Independent — can run in parallel with other phases |

---

## Milestones

| Milestone | Target | Status |
|-----------|--------|--------|
| v1 — Five New Scripts Complete | All 5 phases done | 🔵 Not Started |

---

## Active Decisions

| Decision | Status | Notes |
|----------|--------|-------|
| Single-file pattern | ✓ Confirmed | Each script self-contained |
| Fresh synthetic data per script | ✓ Confirmed | No shared data dependencies |
| Match existing complexity | ✓ Confirmed | ~200-400 lines, 3-5 visualizations |
| scikit-learn only (no XGBoost) | ✓ Confirmed | Minimal dependencies |
| No external CLV/attribution libraries | ✓ Confirmed | Inline implementations |

---

## Blockers

None.

---
*State updated: 2026-05-02*
*Next update: After Phase 1 completion*
