# External Integrations

**Analysis Date:** 2026-05-01

## APIs & External Services

None. This is a fully local, offline analytics portfolio using synthetic data.

## Data Storage

**Databases:**
- None — All data loaded from local CSV files

**File Storage:**
- Local filesystem only
- Input CSVs: `data/volta_funnel_data.csv`, `volta_ab_experiment.csv`, `cohort_retention_matrix.csv`, `volta_users_features.csv`, `segment_profiles.csv`
- Output: PNG visualizations (`viz*.png`) and Excel reports (`output/*.xlsx`)

**Caching:**
- None

## Authentication & Identity

- None — No auth system, no users, no sessions

## Monitoring & Observability

- None — No error tracking, analytics, or logging services
- Scripts print progress to stdout

## CI/CD & Deployment

**Hosting:**
- Not deployed — Local execution only

**CI Pipeline:**
- None — No GitHub Actions, no tests, no linting

## Environment Configuration

**Development:**
- Required: Python 3.10+, `uv` or `pip`
- Secrets: None
- Mock/stub services: All data is synthetic

**Staging / Production:**
- Not applicable

## Webhooks & Callbacks

None.

---

*Integration audit: 2026-05-01*
*Update when adding external services*
