# EDA Report

**Rows:** 58771 · **Columns:** 8 · **Memory:** 11.59 MB

## Profile

| Column | dtype |
|---|---|
| user_id | int64 |
| segment | str |
| currency | str |
| tx_type | str |
| amount_eur | float64 |
| revenue_eur | float64 |
| cost_eur | float64 |
| margin_eur | float64 |

## Data Quality

- Duplicated rows: **0**
- Constant columns: **0**
- Пропусков нет.

## Numeric Distributions

| Column | n | mean | median | std | p25 | p75 | p95 | outliers | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| user_id | 58771 | 1494.65 | 1267.0 | 1068.3154 | 586.0 | 2321.0 | 3458.0 | 0.0% | 0.4851 |
| amount_eur | 58771 | 91.0895 | 81.06 | 48.6986 | 50.855 | 127.275 | 178.035 | 0.2% | 0.5932 |
| revenue_eur | 58771 | 0.5085 | 0.4318 | 0.3497 | 0.2102 | 0.7702 | 1.153 | 0.2% | 0.7007 |
| cost_eur | 58771 | 0.6614 | 0.2111 | 0.6528 | 0.0782 | 1.2476 | 1.7979 | 0.0% | 0.6107 |
| margin_eur | 58771 | -0.1529 | 0.0692 | 0.3699 | -0.486 | 0.1508 | 0.3498 | 0.0% | -0.21 |

## Categorical Slices

**segment** — кардинальность 5

| Value | Count | Share |
|---|---:|---:|
| travelers | 25390 | 43.2% |
| young_professionals | 14855 | 25.3% |
| family_budgeters | 9488 | 16.1% |
| premium_status | 6097 | 10.4% |
| digital_newcomers | 2941 | 5.0% |

**currency** — кардинальность 5

| Value | Count | Share |
|---|---:|---:|
| EUR | 31828 | 54.2% |
| USD | 6936 | 11.8% |
| THB | 6739 | 11.5% |
| GBP | 6639 | 11.3% |
| JPY | 6629 | 11.3% |

**tx_type** — кардинальность 4

| Value | Count | Share |
|---|---:|---:|
| card | 28686 | 48.8% |
| fx | 26943 | 45.8% |
| atm | 1606 | 2.7% |
| transfer | 1536 | 2.6% |

## Correlations

| Pair | r | Note |
|---|---:|---|
| cost_eur ~ margin_eur | -0.9125 | multicollinearity |
| revenue_eur ~ cost_eur | 0.9016 | multicollinearity |
| amount_eur ~ revenue_eur | 0.8295 | multicollinearity |
| amount_eur ~ cost_eur | 0.6546 | moderate |
| revenue_eur ~ margin_eur | -0.6458 | moderate |
| user_id ~ cost_eur | -0.5726 | moderate |
| user_id ~ margin_eur | 0.5604 | moderate |

## Metric by Segment

### segment (overall mean = -0.1529, gap x0.0)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| premium_status | 6097 | 0.1096 | 667.96 | -7.4% | -171.6% |
| family_budgeters | 9488 | 0.0653 | 619.26 | -6.9% | -142.7% |
| young_professionals | 14855 | 0.0415 | 616.25 | -6.9% | -127.1% |
| digital_newcomers | 2941 | 0.0522 | 153.62 | -1.7% | -134.2% |
| travelers | 25390 | -0.435 | -11044.66 | 122.9% | +184.4% |

### currency (overall mean = -0.1529, gap x0.0)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| EUR | 31828 | 0.1332 | 4240.04 | -47.2% | -187.1% |
| JPY | 6629 | -0.4922 | -3263.08 | 36.3% | +221.9% |
| GBP | 6639 | -0.494 | -3279.81 | 36.5% | +223.1% |
| THB | 6739 | -0.4911 | -3309.57 | 36.8% | +221.1% |
| USD | 6936 | -0.4866 | -3375.13 | 37.5% | +218.2% |

### tx_type (overall mean = -0.1529, gap x0.0)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| card | 28686 | 0.1738 | 4985.72 | -55.5% | -213.6% |
| transfer | 1536 | 0.3505 | 538.3 | -6.0% | -329.2% |
| atm | 1606 | -0.7995 | -1283.99 | 14.3% | +422.8% |
| fx | 26943 | -0.4909 | -13227.59 | 147.2% | +221.0% |


## Findings

- **[WARN]** cost_eur ~ margin_eur: r=-0.9125 — мультиколлинеарность или дубль признака
- **[WARN]** revenue_eur ~ cost_eur: r=0.9016 — мультиколлинеарность или дубль признака
- **[WARN]** amount_eur ~ revenue_eur: r=0.8295 — мультиколлинеарность или дубль признака

## What We Did Not Cover

- Причинность: корреляции не доказывают влияние.
- Внешние источники и бизнес-контекст, которых нет в датасете.
- Формальные тесты гипотез (это CDA / A-B testing).

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py --input <dataset> \
    [--metric <col>] [--segments <a,b>] [--time-col <col>] [--top <n>]
```
