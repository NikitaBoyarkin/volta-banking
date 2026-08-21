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

# Lint / format
uv run ruff check .
uv run ruff format .
```

## High-Level Architecture

### Four-Project Portfolio

Each `volta_*.py` is self-contained, structured as **functions + `main()`** +
`if __name__ == "__main__": main()`. Importing a module does **not** execute the
analysis. All four import shared helpers from `utils/common.py`.

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

### Shared Helpers (`utils/common.py`)

- `setup(style="dark_background", float_format="{:.2f}")` — scoped warnings
  (FutureWarning/UserWarning only), plt style, pandas float format.
- `print_section(title, width=70, blank=True)` / `print_subsection()`.
- `data_path(filename)` — resolves repo-root first, then `data/` fallback.
- `CONSTANTS` — LTV, ARPU free/premium, MDE, baseline conversion, α, power,
  fleet assumptions. Centralised so the four scripts don't drift apart.

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

### Legacy Utility Modules (`utils/`)

- `utils/report_generator.py` — Excel report generation (`openpyxl`). Not imported
  by the four main scripts; available for future report automation.
- `utils/pdf_processor.py` — PDF table extraction (`pdfplumber`, `pypdf`). Not
  imported by the main scripts.

### Data Files

- `data/volta_funnel_data.csv` — committed funnel dataset (Project 1, 10k rows).
- Other CSVs are produced by the generators above (repo root). `data_path()`
  resolves both locations, so scripts run from repo root regardless of where the
  CSV lands.

### Outputs

- `viz*.png` — funnel visualizations (generated by Project 1, tracked in git).
- `.planning/` — GSD workflow artifacts (see below).
- `doc/`, `presentations/` — PRD and slide artifacts (legacy/speculative).

## Working with This Codebase

- **No test suite.** Verify changes by running the relevant `volta_*.py` and
  checking printed output + generated files. `uv run python -c "import volta_X"`
  must not print analysis (confirms the `main()` structure). *(Note: a 33→54-
  test pytest suite was added in Sprint 1 — `uv run pytest` now runs it.)*
- **Ruff is configured.** `uv run ruff check .` should pass clean; `ruff format .`
  for whitespace/style.
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
*CLAUDE.md updated: 2026-08-21 (Sprint 1 — углубление аналитики: A1-A4, F1-F3, R1-R3, S1-S3)*