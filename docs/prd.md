# PRD: Volta Banking — Product Analytics Portfolio

**Author:** Nikita Boyarkin
**Date:** 2026-09-02
**Status:** Approved (as-is snapshot)
**Version:** 1.0

---

## 1. Executive Summary

Volta Banking is a self-contained product-analytics portfolio for a fictional fintech neobank. Twelve standalone Python scripts plus a Market & Jobs product-thinking layer (JTBD audit) cover the full analytics lifecycle — onboarding funnel, A/B testing, cohort retention, segmentation, churn prediction, RFM, CLV, marketing attribution, anomaly detection, spend analysis, customer-support churn, and NPS trends — each driven by seeded synthetic data. The portfolio demonstrates end-to-end analytical thinking in every script (business question → data generation → insight → visualization), backed by production-grade engineering (96% test coverage, ruff, mypy, pre-commit, CI). Expected effect: an employer can run any `volta_*.py` from the repo root in a single command and independently evaluate the analytical skill on display.

## 2. Problem Statement

### Текущая ситуация
The job market for product/data analysts in fintech is saturated with portfolios that are either one-dimensional (a single notebook) or shallow (generated data with no analytical narrative). Existing candidates often present raw notebooks with no engineering discipline, which fails to signal production readiness to hiring managers. This repo exists to close that gap with a breadth-first demonstration: twelve distinct analytical domains.

### Влияние на пользователя
- **Кто затронут:** hiring managers and tech leads evaluating Python analytics skills.
- **Как затронут:** they must quickly judge analytical reasoning, statistical rigor, and code quality without a live product or company background.
- **Серьёзность:** High — a portfolio that cannot be run independently or is domain-narrow loses the evaluation within one screen.

### Бизнес-влияние
- **Стоимость проблемы:** opportunity cost — a portfolio that fails to convert attention loses interview slots for a data-analyst / BI candidate in fintech.
- **Стратегическая важность:** portfolio is the primary evidence artifact for the candidate's product-analyst hiring goal (see vault notes on fintech portfolio projects).

### Почему решать сейчас
The repo is complete and validated (all requirements met, CI green). This PRD fixes the current state as a contract so future additions (if any) are measured, and so recruiters get a single canonical document describing what the project is and why each script exists.

## 3. Goals & Success Metrics

### Goal 1: Breadth of analytical domains
- **Описание:** cover the full analytics lifecycle across independent, standalone scripts — each a complete story from business question to visualization — plus a Market & Jobs product-thinking layer (JTBD audit).
- **Метрика:** number of independently runnable `volta_*.py` scripts + Market & Jobs documentation layer.
- **Baseline:** 12 scripts + Market & Jobs (as of 2026-09-05).
- **Target:** 12 maintained (no regression below this count without a documented removal).
- **Срок:** ongoing.
- **Метод измерения:** count of `volta_*.py` files passing an end-to-end smoke run.

### Goal 2: Independent runnability
- **Описание:** every script executes from repo root with `uv run python <script>.py` with no hidden ordering or external dependencies.
- **Метрика:** % of scripts that run standalone on a clean checkout.
- **Baseline:** 100% (all 12 verified via smoke tests).
- **Target:** 100%.
- **Срок:** ongoing.
- **Метод измерения:** CI test suite; `python -c "import volta_X"` must not print analysis output.

### Goal 3: Engineering quality
- **Описание:** portfolio held to production standards, not throwaway analysis.
- **Метрики:**
  - Test coverage on active code: baseline 97% (2026-09-02 CI) → target ≥ 90%.
  - `ruff check .` passes clean.
  - `mypy` passes on new (Sprint 3+) code.
  - pre-commit runs ruff + pytest before commits.
- **Срок:** ongoing.
- **Метод измерения:** `uv run pytest` (addopts coverage), `uv run ruff check .`, `uv run mypy`, `make all`.

## 4. User Stories

### Story 1: Hiring Manager — breadth scan
**As a** hiring manager for a fintech analyst role, **I want to** skim the repo and see the analytical lifecycle covered end-to-end, **So that I can** decide within minutes whether the candidate matches the role's breadth.

**Acceptance Criteria:**
- [ ] Twelve distinct analytical domains are discoverable from a single README index.
- [ ] Each script's README/CLAUDE entry states its business question and key result.
- [ ] Visual outputs (PNG) exist for every domain.

**Dependencies:** None

### Story 2: Tech Lead — run and verify
**As a** tech lead, **I want to** run any script on a clean machine, **So that I can** verify the analysis independently rather than trusting claims.

**Acceptance Criteria:**
- [ ] `uv sync` + `uv run python volta_<domain>.py` runs without error on Python 3.10+.
- [ ] The script generates its CSV into `data/` and PNGs into `outputs/`.
- [ ] A printed summary table contains interpretable business metrics.
- [ ] Importing the module (`import volta_<domain>`) executes no analysis (guarded by `main()`).

**Dependencies:** None

### Story 3: Recruiter — quick orientation
**As a** recruiter screening portfolios, **I want to** read a short PRD that names domains, stack, and quality bar, **So that I can** relay a confident summary to the hiring panel.

**Acceptance Criteria:**
- [ ] PRD lists all domains with one-line descriptions.
- [ ] PRD states stack and engineering metrics.
- [ ] PRD links to the repo root and vault note.

**Dependencies:** None

## 5. Functional Requirements

> All REQ-001..REQ-012 are **implemented and verified** (status: Done). Engineering requirements REQ-013..REQ-016 are partially enforced by CI and are the maintenance focus; REQ-017 (Market & Jobs) is a documentation layer added 2026-09-05. Every requirement below is atomic with ≥3 acceptance criteria.

### Must Have (P0) — core analytical domains

#### REQ-001: Onboarding funnel analysis
**Описание:** `volta_funnel_analysis.py` analyses the onboarding funnel from synthetic user data: step conversion, drop-offs (absolute and relative), channel chi-square test, device/age segment breakdown, time-to-convert by channel, funnel heatmap, and step×segment chi-square with Holm correction.

**Acceptance Criteria:**
- [ ] Loads `data/volta_funnel_data.csv` (10k rows committed) via `data_path()`.
- [ ] Prints step-level conversion and drop-off table with absolute and relative drop-offs.
- [ ] Runs channel chi-square test and reports p-value; reports step×segment tests with Holm correction (Sprint 1: `step_segment_tests`, `section_step_segment_tests`).
- [ ] Produces ≥4 PNGs in `outputs/` (viz1_main_funnel, viz2_channel_breakdown, viz3_segments, viz4_funnel_heatmap).
- [ ] `uv run python volta_funnel_analysis.py` exits 0 from repo root.

**Dependencies:** None

#### REQ-002: KYC progress bar A/B test
**Описание:** `volta_ab_testing.py` analyses a KYC progress-bar A/B experiment: sample-size calc, SRM check, bootstrap CI, multiple-comparison corrections (Bonferroni/Holm/BH), AA-test under H₀, CUPED (control-only θ), sensitivity at MDE, ship-gate (p<0.05 ∧ lift≥MDE ∧ no SRM). Sprint 1 additions: guardrail metrics with directional violation logic, HTE with BH-adjusted q-values, O'Brien-Fleming group-sequential boundaries, power-vs-MDE curve.

**Acceptance Criteria:**
- [ ] Loads `volta_ab_experiment.csv` (with `churned_30d`, `revenue_30d_eur` guardrail columns) + `segment_results.csv`.
- [ ] Reports SRM check result; fails or passes explicitly.
- [ ] Computes bootstrap CI for the primary metric and applies a multiplicity correction.
- [ ] Applies CUPED variance reduction and reports adjusted lift + CI.
- [ ] Applies ship-gate verdict: "ship" only if p<0.05 ∧ lift≥MDE ∧ SRM passed; otherwise explicit "no ship" with reason.
- [ ] Evaluates guardrail metrics with directional violation logic (`guardrail_test`, `section_guardrails`).
- [ ] Produces `ab_power_curve.png` (power-vs-MDE) and prints sequential O'Brien-Fleming verdict.

**Dependencies:** generate_ab_data.py

#### REQ-003: Cohort retention & LTV
**Описание:** `volta_retention_analysis.py` analyses cohort retention against a product fix: pre/post Welch t-test + Cohen's d, separate Free vs Premium retention curves (M6 ≈ 0.21 vs 0.55), ARPU×retention LTV decomposition, fleet impact projection, cohort heatmap, churn curve, LTV bootstrap CI.

**Acceptance Criteria:**
- [ ] Loads `cohort_retention_matrix.csv` (pre-fix < 2024-09, post-fix ≥ 2024-09).
- [ ] Reports Welch t-test p-value and Cohen's d for the pre/post comparison.
- [ ] Prints separate Free and Premium retention curves.
- [ ] Computes ARPU×retention LTV decomposition and fleet impact projection.
- [ ] Produces `cohort_heatmap.png`; prints churn curve (= 1−retention) and LTV bootstrap CI.

**Dependencies:** generate_retention_data.py

#### REQ-004: Customer segmentation (KMeans + PCA)
**Описание:** `volta_segmentation.py` segments users via KMeans + PCA with data-driven K selection (marginal-gain elbow + silhouette validation, subsampling 10k for O(n²)), named segments guarded by assert, Lorenz concentration curve, churn sensitivity, monetization scenarios. Sprint 1: per-sample silhouette plot, centroid z-score profiles vs global mean, bootstrap segment stability via adjusted Rand index.

**Acceptance Criteria:**
- [ ] Loads `volta_users_features.csv` (50k users, 4 separable clusters) + `segment_profiles.csv`.
- [ ] Selects K via marginal-gain elbow rule with silhouette validation; `select_k` subsamples to 10k for runtime.
- [ ] Names segments; `assert len(...) == optimal_k` guards naming drift.
- [ ] Produces `segmentation_pca_scatter.png`, `segmentation_k_selection.png`, `segmentation_silhouette.png`.
- [ ] Prints segment size shares, monetization scenario results, and centroid z-score profiles.

**Dependencies:** generate_segmentation_data.py

#### REQ-005: Churn prediction
**Описание:** `volta_churn_prediction.py` builds churn models: Logistic Regression vs Random Forest, train/test split with stratification, feature pre-processing (one-hot channel encoding), ROC-AUC + precision/recall/F1 per model, feature importance, confusion matrix + ROC curve for the best model.

**Acceptance Criteria:**
- [ ] Generates synthetic churn data (`volta_churn_data.csv`, ~20% churn, non-linear cliff so RF beats LR).
- [ ] Splits data with stratification; scales/encodes features via scikit-learn transformers.
- [ ] Trains ≥2 models; reports ROC-AUC, precision, recall, F1 per model.
- [ ] Reports feature importances; plots top drivers (churn_feature_importance.png).
- [ ] Plots ROC curve (churn_roc_curve.png) for the best model; RF beats LR by ≥0.02 AUC.

**Dependencies:** generate_churn_data.py

#### REQ-006: RFM analysis
**Описание:** `volta_rfm_analysis.py` scores customers on Recency (inverted), Frequency, Monetary (1–5, quantile-based rank-first) and segments them into ≥5 lifecycle groups; size bar chart + R/F/M heatmap + action table.

**Acceptance Criteria:**
- [ ] Generates synthetic transaction data (`volta_rfm_transactions.csv`) per archetype.
- [ ] Computes R/F/M via pandas groupby; scores rank-first to avoid edge cases.
- [ ] Produces ≥5 named segments (e.g., champions / loyal / potential / at-risk / lost / new).
- [ ] Produces `rfm_segment_sizes.png` and `rfm_heatmap.png`.
- [ ] Prints average R/F/M per segment and per-segment recommended actions.

**Dependencies:** generate_rfm_data.py

#### REQ-007: CLV modeling
**Описание:** `volta_clv_modeling.py` estimates Customer Lifetime Value via three methods: historical (sum revenue), predictive (retention-curve power-law fit), and probabilistic (Gamma-Gamma MLE, inline, no external CLV library); distribution comparison plot + top-10 ranking.

**Acceptance Criteria:**
- [ ] Generates synthetic transaction history (`volta_clv_customers.csv` + `volta_clv_cohorts.csv`).
- [ ] Computes historical, predictive, and probabilistic CLV per customer.
- [ ] Predictive uses power-law retention fit (`fit_power_retention`); probabilistic uses inline Gamma-Gamma MLE (`_gamma_gamma_mle`).
- [ ] Produces `clv_by_method.png` (distribution comparison: histograms or box plots).
- [ ] Prints top 10 customers by probabilistic CLV.

**Dependencies:** generate_clv_data.py

#### REQ-008: Marketing attribution
**Описание:** `volta_attribution.py` compares four attribution models on synthetic multi-touch journeys: first-touch, last-touch, linear, and Shapley value (data-driven, normalized per journey); grouped bar comparison.

**Acceptance Criteria:**
- [ ] Generates multi-touch journey data (`volta_attribution_journeys.csv`) with conversion flag.
- [ ] Computes last-touch, first-touch, and linear attribution weights per channel.
- [ ] Computes data-driven attribution via Shapley values (`shapley_credit`), reusing `CHANNEL_WEIGHT` from the generator.
- [ ] All four models produce channel weights that sum to 1.0 (or 100%).
- [ ] Produces `attribution_models.png` (grouped bar chart across channels/models).

**Dependencies:** generate_attribution_data.py

#### REQ-009: Anomaly detection
**Описание:** `volta_anomaly_detection.py` detects anomalies on synthetic daily transaction metrics with statistical (Z-score, IQR) and ML (Isolation Forest) methods, scored against ground truth (precision/recall/F1); multi-method comparison table + time series highlight plot.

**Acceptance Criteria:**
- [ ] Generates daily metric data (`volta_anomaly_transactions.csv`) with injected ground-truth anomalies (amount / late-night / velocity types).
- [ ] Flags anomalies via Z-score and IQR on transaction volume; Isolation Forest on multivariate features (volume, active users, avg transaction size) with log-amount + user-velocity features (`add_features`).
- [ ] Scores each method against ground truth with precision/recall/F1.
- [ ] Produces `anomaly_detections.png` (time series highlighting per-method flags).
- [ ] Prints comparison table: Z-score only / IQR only / Isolation Forest only / consensus (all three).

**Dependencies:** generate_anomaly_data.py

#### REQ-010: Spend analysis
**Описание:** `volta_spend_analysis.py` analyses the spend ledger: category / channel / merchant breakdown, decline rate by category, monthly spend trend.

**Acceptance Criteria:**
- [ ] Loads `volta_transactions.csv` (spend ledger: category / merchant / channel / status / country; segment-driven intensity).
- [ ] Prints spend share by category, channel, and top merchants.
- [ ] Computes decline rate by category.
- [ ] Produces `spend_by_category.png` and `spend_monthly_trend.png`.

**Dependencies:** generate_transactions_data.py

#### REQ-011: Customer-support experience vs churn
**Описание:** `volta_cs_churn.py` joins support tickets with churn data to quantify support experience impact: churn rate by ticket volume, unresolved tickets and CSAT band, category mix churned vs retained.

**Acceptance Criteria:**
- [ ] Joins `volta_support_tickets.csv` with `volta_churn_data.csv` on customer id.
- [ ] Computes churn rate by ticket volume, unresolved-ticket status, and CSAT band.
- [ ] Reports category mix for churned vs retained customers.
- [ ] Produces `cs_churn_by_tickets.png`.

**Dependencies:** generate_support_tickets_data.py, generate_churn_data.py

#### REQ-012: NPS trends & drivers
**Описание:** `volta_nps_trends.py` analyses NPS surveys: monthly NPS, promoter/passive/detractor mix, NPS by driver, comment length by segment.

**Acceptance Criteria:**
- [ ] Loads `volta_nps_surveys.csv` (NPS 0–10 + driver + promoter/passive/detractor segment).
- [ ] Computes monthly NPS and promoter/passive/detractor mix.
- [ ] Computes NPS by driver and comment length by segment.
- [ ] Produces `nps_monthly_trend.png` and `nps_by_driver.png`.

**Dependencies:** generate_nps_data.py

### Must Have (P0) — data & reproducibility platform

#### REQ-013: Seeded synthetic data generation
**Описание:** 14 standalone generators (`generate_*.py`) produce all datasets with fixed seed (`SEED = 42`) for full reproducibility; `make data` runs them all.

**Acceptance Criteria:**
- [ ] Every dataset is generated by a deterministic script (`uv run python generate_*.py`, `SEED = 42`).
- [ ] Re-running a generator produces byte-identical CSV (given the same seed).
- [ ] Generators write to `data/`; `make data` regenerates all 14 datasets.
- [ ] At least 3 generators encode ground truth consumed by analyses (churn flag, anomaly `is_anomaly`, attribution conversion).

**Dependencies:** None

#### REQ-014: Output & path conventions
**Описание:** scripts route data input through `utils/common.data_path()` (prefer `data/`, fallback to repo root) and write PNGs to `OUTPUT_DIR` (`outputs/`); shared constants are centralized in `utils/common.py` so scripts don't drift.

**Acceptance Criteria:**
- [ ] All scripts load CSVs via `data_path()`; all PNGs land in `outputs/`.
- [ ] Running from repo root never fails on missing-file path errors for committed datasets.
- [ ] Shared analytical constants (LTV, ARPU, MDE, baseline conversion, α, power) live in `utils/common.CONSTANTS`, not duplicated in script bodies.
- [ ] `utils/common.setup()` applies dark_background style + scoped warning filters consistently.

**Dependencies:** None

### Should Have (P1) — engineering quality

#### REQ-015: Test suite & static analysis
**Описание:** the repo is guarded by pytest (incl. end-to-end smoke tests that execute each `main()`), ruff lint/format, mypy on new code, pre-commit, and CI.

**Acceptance Criteria:**
- [ ] `uv run pytest` passes; coverage on active code ≥ 90% (baseline 97%, verified 2026-09-02).
- [ ] Smoke tests execute every `volta_*.py` `main()` end-to-end without error.
- [ ] `ruff check .` passes clean (`select = ["E","W","F","I","B","C4","UP"]`, `ignore = ["E501"]`).
- [ ] `mypy` passes on new code; legacy scripts remain explicitly annotated `# mypy: ignore-errors` (not silent).
- [ ] pre-commit runs ruff + pytest before commits; CI runs `make all`.

**Dependencies:** None

#### REQ-016: Documentation & narrative
**Описание:** README, CLAUDE.md, and `.planning/` GSD artifacts document the twelve-project structure, execution order, and engineering setup so a fresh evaluator or agent can orient.

**Acceptance Criteria:**
- [ ] README lists all 12 scripts with execution order and one-line purpose.
- [ ] CLAUDE.md documents stack, commands (`make data/test/lint/format/type`), and per-script structure.
- [ ] `.planning/` (PROJECT.md, REQUIREMENTS.md, ROADMAP.md) tracks requirements and status.
- [ ] This PRD (`docs/prd.md`) stays in sync with the current script count.

**Dependencies:** None

#### REQ-017: Market & Jobs (JTBD product-thinking layer)
**Описание:** a documentation layer capturing Volta's B2C market: top-5 JTBD segments, RAT risk ranking, and recommendations. Source: `Obsidian/Z-core/AJTBD - Volta Full Audit.md` (2026-09-05). Not a script — a product-thinking domain that signals breadth to recruiters.

**Acceptance Criteria:**
- [ ] README contains a "Market & Jobs" section with top-5 segments and RAT risks.
- [ ] PRD references the JTBD audit note and its recommendations.
- [ ] `.planning/` docs reflect the audit as a product-thinking layer.
- [ ] Vault note `PRD - Volta Banking.md` links the audit.

**Dependencies:** None

## 6. Non-Functional Requirements

### Performance
- Each script completes in ≤ 2 minutes on a mid-range laptop (O(n²) operations — silhouette — are subsampled: `select_k` → 10k, `plot_silhouette` → 5k).
- `uv run python volta_*.py` from repo root is the only command contract; no background services.

### Security
- **Data:** synthetic only — no real customer PII, no secrets, no `.env` required (all synthetic generators, `SEED = 42`).
- **Dependencies:** pinned via `uv.lock`; no runtime network calls in analyses.

### Scalability / Compatibility
- **Python:** ≥ 3.10 (`pyproject.toml`); `.python-version` may pin newer (3.14.2 current).
- **OS:** macOS / Linux / Windows; `uv` preferred, `pip` fallback.
- **Growth:** additive model — new domains = one `volta_*.py` + one `generate_*.py` + smoke test; no graph/DB to migrate.

### Reliability
- Not a deployment target (local execution only); reliability contract = reproducibility (seeded) + CI green (ruff, mypy, pytest ≥ 90%).
- `import volta_X` must be side-effect free (no analysis print on import).

## 7. Technical Considerations

### Архитектура
```
utils/common.py (data_path, OUTPUT_DIR, CONSTANTS, setup, print_section)
        │  shared helpers imported by
        ▼
volta_<domain>.py  (functions + main() + if __name__ == "__main__": main())
        │  sources CSV via data_path(); writes PNG to outputs/
        ▼
data/*.csv ⇐ generate_*.py (seeded, SEED=42)   outputs/*.png
```

### Технологический стек
- **Language:** Python 3.10+
- **Data:** pandas 2.3.3+, numpy 2.0.2+
- **Statistics:** scipy 1.13.1+ (Chi-square, Welch t-test, KS, norm)
- **ML:** scikit-learn (StandardScaler, KMeans, PCA, silhouette_score, LogisticRegression, RandomForest, IsolationForest)
- **Visualization:** matplotlib 3.9.4+ (`dark_background`), seaborn 0.13.2+
- **Reports (utils):** openpyxl, pdfplumber, pypdf (legacy, not imported by main scripts)
- **Engineering:** pytest + pytest-cov (~96%), ruff, mypy, pre-commit, GitHub Actions (CI), uv

### Внешние зависимости
1. **PyPI packages** — pinned via `uv.lock`; add with `uv add`, keep lockfile in sync (never edit by hand).
2. **None at runtime** — scripts are self-contained and offline.

### Миграция (для существующих систем)
Not applicable — the repo is a portfolio, not a deployed system. Change control = git + pre-commit + CI.

### Тестирование
- **Unit:** pytest, coverage ≥ 90% on active code.
- **Integration:** end-to-end smoke tests execute each `main()`.
- **Static:** ruff (`E,W,F,I,B,C4,UP`), mypy on new code.
- **Docs claims:** README/CLAUDE sync verified by the smoke + lint gate (`make all`).

## 8. Implementation Roadmap

> Status: **fully implemented.** All twelve domains, the engineering layer, and the Market & Jobs layer are done and verified (2026-08-24 Sprints 2–5; Market & Jobs 2026-09-05). The roadmap below is the as-is snapshot plus a conservative maintenance horizon — per decision, no new features are planned.

### Phase 1 (DONE): Foundation — core narrative (4 scripts)
**Goal:** funnel → A/B → retention → segmentation.
**Tasks:** all complete (`volta_funnel_analysis.py`, `volta_ab_testing.py`, `volta_retention_analysis.py`, `volta_segmentation.py`).
**Validation Checkpoint:** each script runs from repo root, commits CSVs, outputs ≥3 PNGs, prints interpretable summary.

### Phase 2 (DONE): Analytical breadth — projects 5–9
**Goal:** churn, RFM, CLV, attribution, anomaly detection.
**Tasks:** all complete.
**Validation Checkpoint:** all 5 scripts run; RF beats LR by ≥0.02 AUC; attribution weights sum to 1.0; anomaly methods scored vs ground truth.

### Phase 3 (DONE): Engineering + docs — projects 10–12, tests, CI
**Goal:** spend, CS-churn, NPS; pytest smoke coverage, ruff/mypy/pre-commit, CI, notebooks, PRD doc.
**Tasks:** all complete.
**Validation Checkpoint:** `make all` green; coverage ≥ 90%; README lists 12 scripts.

### Phase 4 (MAINTENANCE): Conservative horizon — no new features
**Goal:** keep the current breadth runnable and reproducible as the environment drifts.
**Tasks:**
- [ ] Re-run `make data` + `make all` on Python 3.14 (verify no dependency drift) — Small (2h)
- [ ] Refresh README/CLAUDE script index if repository layout changes — Small (1h)
- [ ] Keep `docs/prd.md` requirement count in sync with the repo — Small (1h)
- [ ] Keep Market & Jobs (REQ-017) in sync with the JTBD audit note — Small (1h)
**Validation Checkpoint:** CI green after each maintenance pass; script count stable at 12.

### Зависимости задач
```
Phase 1 → Phase 2 → Phase 3 (sequential narrative build)
Phase 4: independent, recurring
Critical Path: none (all work complete; Phase 4 is periodic upkeep)
```

### Оценка усилий
- Phase 1–3: **DONE** (historical effort ~4 weeks across sprints).
- Phase 4: ~4h per maintenance pass.
- **Итого (future):** ~4h/pass, no risk buffer needed (non-critical upkeep).

## 9. Out of Scope

1. **Interactive dashboard (Streamlit/Dash)** — portfolio is deliberately script/notebook-based for readability; executed `.ipynb` notebooks are provided instead. Future: revisit if a candidate asks for a viz product.
2. **Real data integration** — synthetic data only, local execution; no API/DB layer.
3. **External advanced libraries** — `lifetimes`, `pymc-marketing`, `mta`, or XGBoost/LightGBM/CatBoost — deps stay minimal (scikit-learn only); Random Forest suffices for the demo.
4. **Model serialization** (`joblib`/`pickle`) — scripts are one-off demonstrations.
5. **Deployment / hosting** — not a shipped service; no SLA, no RTO/RPO targets.
6. **New analytical script domains** — explicitly deferred (decision: fixate, don't extend). Exception: Market & Jobs (REQ-017) added as a documentation layer, not a script.

## 10. Open Questions & Risks

### Open Questions
#### Q1: README scope accuracy
- **Статус:** current README (2026-08-24) documents the portfolio through 12 scripts; PRD is the authoritative as-is snapshot.
- **Варианты:** (A) keep README as-is, (B) add a PRD link from README.
- **Владелец:** maintainer.
- **Дедлайн:** 2026-09-16 (next maintenance pass).
- **Влияние:** Low.

### Risks & Mitigation

| Риск | Вероятность | Влияние | Severity | Митигация | Контингенция |
|------|-------------|---------|----------|-----------|--------------|
| Python/dep drift (3.14 vs 3.10) breaks a script | Medium | Medium | **High** | `uv.lock` pinned; `make all` CI; maintenance pass on newest interpreter | Re-pin deps, isolate breakage in a generator, re-run smoke tests |
| O(n²) silhouette runtime regression on large data | Low | Low | **Medium** | subsample pattern documented in CLAUDE.md (`select_k`→10k, `plot_silhouette`→5k) | Raise subsample budget or cap sweep range |
| Script/PRD drift (README says 12, repo gains/churns) | Low | Low | **Low** | REQ-016 binds docs; Phase 4 keeps count in sync | One doc-sync pass in maintenance |
| CI/pre-commit silently disabled | Low | Medium | **Medium** | `claim-mechanism` rule: never disable a failing check | Re-enable, log lesson to repo `.planning` |

## 11. Validation Checkpoints

### Checkpoint 1: Post-completion (2026-08-24)
**Критерии:**
- [ ] All 12 scripts run from repo root (smoke tests green).
- [ ] `make all` passes (data + pytest ≥ 90% + ruff + mypy).
- [ ] README/CLAUDE document all scripts.
**Если провален:** treat as regression, not as "done".

### Checkpoint 2: Each maintenance pass (quarterly)
**Критерии:**
- [ ] `make data` regenerates deterministically (byte-identical CSVs with same seed).
- [ ] `make all` green on current interpreter.
- [ ] `docs/prd.md` script count == repo count.
**Если провален:** fix before announcing repo health.

---

**Конец PRD**

*Scope: comprehensive (as-is snapshot). Full inventory: 17 requirements (12 domains + Market & Jobs + 4 engineering/platform), 12 user stories, all verified.*
