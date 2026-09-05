# CLAUDE.md

Guidance for Claude Code working in this repository.

## Project Overview

Product analytics portfolio for a fictional fintech neobank ("Volta"). Four
sequential, standalone Python analysis scripts form an end-to-end narrative:
**funnel → A/B testing → retention/cohort → segmentation**. Synthetic data,
educational/demonstrative. Each script picks up where the previous one ended.

## Development Environment

- **Python:** ≥3.10 (`pyproject.toml`; `.python-version` may pin a newer interpreter)
- **Package manager:** `uv` (preferred). Keep `uv.lock` in sync with `pyproject.toml`.
- **Linter/formatter:** `ruff` (dev dependency; configured in `pyproject.toml`:
  `select = ["E","W","F","I","B","C4","UP"]`, `ignore = ["E501"]`, excludes `*.ipynb`).
- **Type checking:** `mypy` (config in `pyproject.toml`; the four legacy scripts are
  marked `# mypy: ignore-errors`, new Sprint 3+ code is typed and checked).
- **Coverage:** `pytest-cov` (default `addopts` in `pyproject.toml`; ~96% on active
  code). Legacy `utils/pdf_processor.py` + `utils/report_generator.py` are omitted.
- **Pre-commit:** `.pre-commit-config.yaml` runs ruff + pytest before commits
  (`uv run pre-commit install` once).

## Common Commands

```bash
# Install (dev group required for ruff)
uv sync --all-groups

# Generate the synthetic datasets (seeded, reproducible)
uv run python generate_ab_data.py
uv run python generate_retention_data.py
uv run python generate_segmentation_data.py

# Run analyses (from repo root)
uv run python volta_funnel_analysis.py
uv run python volta_ab_testing.py
uv run python volta_retention_analysis.py
uv run python volta_segmentation.py

# Lint / format / type
uv run ruff check .
uv run ruff format .
uv run mypy

# Tests (with coverage) — or the Makefile shortcuts below
uv run pytest

# Makefile shortcuts
make data     # regenerate all synthetic datasets
make test     # uv run pytest
make lint     # uv run ruff check .
make format   # uv run ruff format .
make type     # uv run mypy
make all      # data + test + lint + type
```

## High-Level Architecture

### Fourteen-Project Portfolio

Each `volta_*.py` is self-contained, structured as **functions + `main()`** +
`if __name__ == "__main__": main()`. Importing a module does **not** execute the
analysis. All import shared helpers from `utils/common.py`.

1. **`volta_funnel_analysis.py`** — onboarding funnel. Loads
   `data/volta_funnel_data.csv` (committed; augmented with `install_date` /
   `first_tx_date` by `generate_funnel_data.py`). Step conversion, drop-offs
   (split into absolute/relative — Registration = biggest absolute, KYC Complete
   = biggest relative), Chi-square channel test, device/age segments, plots
   (`viz1/viz2/viz3*.png`). **Sprint 1 additions:** F1 step×segment chi-square
   with Holm correction (`step_segment_tests`, `section_step_segment_tests`);
   F2 time-to-convert by channel (`time_to_convert`, `section_time_to_convert`);
   F3 funnel heatmap PNG (`plot_funnel_heatmap` → `viz4_funnel_heatmap.png`).
2. **`volta_ab_testing.py`** — KYC progress bar A/B test. Loads
   `volta_ab_experiment.csv` (now with `churned_30d` + `revenue_30d_eur`
   guardrail columns) + `segment_results.csv`. Sample-size calc, SRM check,
   bootstrap CI, Bonferroni/Holm/BH correction, AA-test under H₀, CUPED
   (control-only θ), sensitivity at MDE, ship-gate (p<0.05 ∧ lift≥MDE ∧ no SRM).
   **Sprint 1 additions:** A1 guardrail metrics with directional violation
   logic (`guardrail_test`, `section_guardrails`); A2 HTE with BH-adjusted
   q-values (`hte_analysis`, `_bh_adjusted_pvals`, `section_hte`); A3 group-
   sequential O'Brien-Fleming boundaries (`sequential_bounds`,
   `sequential_verdict`, `section_sequential`); A4 power-vs-MDE curve PNG
   (`power_at_mde`, `plot_power_curve` → `ab_power_curve.png`).
3. **`volta_retention_analysis.py`** — cohort retention + LTV. Loads
   `cohort_retention_matrix.csv`. Pre/post Welch t-test + Cohen's d, **separate
   Free vs Premium retention curves** (M6 ≈ 0.21 vs 0.55), ARPU × retention
   LTV decomposition, fleet impact projection. **Sprint 1 additions:** R1
   cohort heatmap PNG (`plot_cohort_heatmap` → `cohort_heatmap.png`); R2 churn
   curve = 1−retention pre/post (`churn_curve`, `section_churn_curve`); R3 LTV
   bootstrap CI grounded in cohort variability (`ltv_bootstrap_ci`,
   `section_ltv_bootstrap_ci`).
4. **`volta_segmentation.py`** — K-means + PCA + monetization. Loads
   `volta_users_features.csv` + `segment_profiles.csv`. **Data-driven K**
   (marginal-gain elbow rule, silhouette validation; `select_k` subsamples to
   10k for the O(n²) `silhouette_score` on 50k+ users), segment names guarded by
   `assert len == optimal_k`, size_pct derived from `seg_summary`, Lorenz
   concentration curve, churn sensitivity, monetization scenarios. **Sprint 1
   additions:** S1 classic per-sample silhouette plot PNG (`plot_silhouette`
   → `segmentation_silhouette.png`, subsamples to 5k for O(n²)); S2 centroid
   z-score profiles vs global mean (`centroid_zscores`,
   `section_centroid_profiles`); S3 bootstrap segment stability via adjusted
   Rand index (`segment_stability`, `segment_stability_section`).
5. **`volta_churn_prediction.py`** — LR vs Random Forest, ROC-AUC + feature
   importance. `prep_features` one-hot encodes channel; `fit_models`/`evaluate`
   compare models; RF beats LR by ≥0.02 on the synthetic data.
6. **`volta_rfm_analysis.py`** — R/F/M 1-5 scoring (recency inverted) +
   lifecycle `segment_customers` (≥5 labels) + size bar chart + R/F/M heatmap.
7. **`volta_clv_modeling.py`** — 3 CLV methods: historical, retention-curve
   (power-law fit `fit_power_retention`), and probabilistic Gamma-Gamma MLE
   (`_gamma_gamma_mle`, inline). Segments mirror Project 4.
8. **`volta_attribution.py`** — first/last/linear + Shapley value
   (`shapley_credit`, normalized per journey). Imports `CHANNEL_WEIGHT` from
   `generate_attribution_data.py`.
9. **`volta_anomaly_detection.py`** — Z-score / IQR / Isolation Forest scored
   against ground truth (precision/recall/F1). `add_features` builds log-amount +
   user velocity.
10. **`volta_spend_analysis.py`** — spend analysis. Loads
   `volta_transactions.csv`. Category / channel / merchant breakdown, decline
   rate by category, monthly spend trend.
11. **`volta_cs_churn.py`** — support experience vs churn. Joins
   `volta_support_tickets.csv` with `volta_churn_data.csv`. Churn rate by ticket
   volume, unresolved tickets and CSAT band; category mix churned vs retained.
12. **`volta_nps_trends.py`** — NPS trends & drivers. Loads
   `volta_nps_surveys.csv`. Monthly NPS, promoter/passive/detractor mix, NPS by
   driver, comment length by segment.
13. **`volta_jtbd_mapping.py`** — JTBD segments × behavioral cohorts (Market &
   Jobs layer, Sprint 6 T2). Loads `volta_jtbd_segments.csv`. Cross-tab JTBD
   segment × cohort, chi-square test of independence, two-proportion z-test on
   Dormant share (Digital Newcomers 45+ vs Family Budgeters), UX-friction
   contrast (support tickets, KYC duration), heatmap PNG
   (`jtbd_segment_cohort_heatmap.png`). Validates audit risk #3: Dormant = UX
   friction, not "no job".
14. **`volta_unit_economics.py`** — traveler unit economics (Market & Jobs
   layer, Sprint 6 T3). Loads `volta_unit_economics.csv`. Per-segment
   revenue/cost/margin per transaction, traveler deep-dive by tx type, FX
   break-even (cost 0.55% / spread 0.85%), sensitivity of blended margin to
   FX cost & spread, scale projection at SOM (180K travelers) → negative
   monthly P&L, sensitivity PNG (`traveler_unit_economics_sensitivity.png`).
   Validates audit risk #1: traveler unit economics break at scale.

### Shared Helpers (`utils/common.py`)

- `setup(style="dark_background", float_format="{:.2f}")` — scoped warnings
  (FutureWarning/UserWarning only), plt style, pandas float format.
- `print_section(title, width=70, blank=True)` / `print_subsection()`.
- `data_path(filename)` — prefers `data/`, falls back to repo root.
- `OUTPUT_DIR` — `outputs/` for all PNGs (imported by the scripts).
- `CONSTANTS` — LTV, ARPU free/premium, MDE, baseline conversion, α, power,
  fleet assumptions. Centralised so the scripts don't drift apart.

### Generators (seeded, reproducible)

- `generate_ab_data.py` → `volta_ab_experiment.csv` (now with `churned_30d` +
  `revenue_30d_eur` guardrail columns — downstream of kyc_completed but
  unaffected by treatment group), `segment_results.csv`
- `generate_retention_data.py` → `cohort_retention_matrix.csv`
  (pre-fix < 2024-09, post-fix ≥ 2024-09; Free retention curves match `volta_retention_analysis.py` PARAMS)
- `generate_segmentation_data.py` → `volta_users_features.csv` (50k users, 4
  separable clusters), `segment_profiles.csv`
- `generate_funnel_data.py` → augments `data/volta_funnel_data.csv` IN PLACE
  with `install_date` + `first_tx_date` (lognormal gap per channel) for the
  time-to-convert analysis. Binary flag columns preserved; run once after
  cloning if timestamps are missing.
- `generate_churn_data.py` → `volta_churn_data.csv` (non-linear churn cliff so
  RF beats LR).
- `generate_rfm_data.py` → `volta_rfm_transactions.csv` (per-archetype buying
  patterns; champions/loyal/potential/at-risk/lost/new).
- `generate_clv_data.py` → `volta_clv_customers.csv` + `volta_clv_cohorts.csv`
  (segments mirror Project 4).
- `generate_attribution_data.py` → `volta_attribution_journeys.csv`
  (`CHANNEL_WEIGHT` reused by `volta_attribution.py`).
- `generate_anomaly_data.py` → `volta_anomaly_transactions.csv` (ground-truth
  `is_anomaly`; amount / late-night / velocity anomaly types).
- `generate_transactions_data.py` → `volta_transactions.csv` (spend ledger;
  category / merchant / channel / status / country; segment-driven intensity).
- `generate_support_tickets_data.py` → `volta_support_tickets.csv` (CS tickets;
  category / priority / CSAT; ground truth behind churn's `support_tickets`).
- `generate_nps_data.py` → `volta_nps_surveys.csv` (NPS 0-10 + driver +
  promoter/passive/detractor segment).
- `generate_feature_events_data.py` → `volta_feature_events.csv` (feature-usage
  event stream; adoption differs by segment).
- `generate_campaigns_data.py` → `volta_campaigns.csv` (campaign spend +
  impressions→clicks→installs→KYC→first-tx funnel per channel).
- `generate_referrals_data.py` → `volta_referrals.csv` (referral status funnel
  sent→accepted→KYC→first-tx; referral converts best).
- `generate_jtbd_data.py` → `volta_jtbd_segments.csv` (40k users, 5 JTBD
  segments × 4 behavioral cohorts; Dormant over-represented in digital
  newcomers — the risk-#3 contrast).
- `generate_unit_economics_data.py` → `volta_unit_economics.csv`
  (transaction-level economics across 5 segments; travelers lose €/tx on FX —
  the risk-#1 contrast).

All generators write to `data/` and are seeded (`SEED = 42`). `make data` runs them all.

### Legacy Utility Modules (`utils/`)

- `utils/report_generator.py` — Excel report generation (`openpyxl`). Not imported
  by the nine main scripts; available for future report automation.
- `utils/pdf_processor.py` — PDF table extraction (`pdfplumber`, `pypdf`). Not
  imported by the main scripts.

### Data Files

- `data/*.csv` — all synthetic datasets (funnel CSV committed with 10k rows; the
  rest produced by generators). `data_path()` prefers `data/` with a repo-root
  fallback, and generators write there, so scripts run from repo root.

### Outputs

- `outputs/*.png` — all visualizations across the nine projects (funnel viz1-4,
  ab_power_curve, cohort_heatmap, segmentation_*, churn_*, rfm_*, clv_by_method,
  attribution_models, anomaly_detections), tracked in git.
- `data/*.csv` — all synthetic datasets (funnel CSV committed; others produced by
  generators), tracked in git. `data_path()` and generators route to `data/`; scripts
  write PNGs to `OUTPUT_DIR` (`outputs/`).
- `.planning/` — GSD workflow artifacts (see below).
- `doc/`, `presentations/` — PRD and slide artifacts (legacy/speculative).

## Working with This Codebase

- **Test suite + coverage.** `uv run pytest` runs 58+ tests including end-to-end
  smoke tests that execute each `main()`. Coverage (~96% on active code) is on by
  default via `addopts`. `uv run python -c "import volta_X"` must not print analysis
  (confirms the `main()` structure).
- **Ruff is configured.** `uv run ruff check .` should pass clean; `ruff format .`
  for whitespace/style. Pre-commit runs both automatically.
- **mypy checks new code only.** The four legacy scripts carry `# mypy: ignore-errors`;
  new Sprint 3+ scripts must be typed and pass `uv run mypy`.
- **`select_k` runtime:** `silhouette_score` is O(n²); on 50k users it
  subsamples to 10k points (~7s for the full K=2..8 sweep). Same subsample
  pattern in `plot_silhouette` (5k) — keep it if you touch either.
- **Dependencies pinned via `uv.lock`.** Add packages with `uv add`, then `uv sync`.
- **Do not edit `uv.lock` by hand.**

## Tech Stack

- `pandas`, `numpy` — data manipulation
- `matplotlib`, `seaborn` — visualization (`plt.style.use('dark_background')`)
- `scipy` — statistical tests (Chi-square, Welch t-test, KS)
- `scikit-learn` — `StandardScaler`, `KMeans`, `PCA`, `silhouette_score` (Project 4)
- `openpyxl` — Excel report generation (utils)
- `pdfplumber`, `pypdf` — PDF processing (utils)

## GSD Workflow

Planning artifacts live in `.planning/`: `PROJECT.md`, `REQUIREMENTS.md`,
`ROADMAP.md`, `STATE.md`, `config.json`. Workflow commands:
`/gsd-discuss-phase N`, `/gsd-plan-phase N`, `/gsd-execute-phase N`,
`/gsd-transition N→N+1`. Mode: YOLO; granularity: fine; phases independent.

---
*CLAUDE.md updated: 2026-08-24 (Sprints 2-5 — engineering layer, projects 5-9, notebooks, docs)*