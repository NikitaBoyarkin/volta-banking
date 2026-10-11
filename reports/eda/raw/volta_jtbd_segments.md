# EDA Report

**Rows:** 40000 · **Columns:** 10 · **Memory:** 6.21 MB

## Profile

| Column | dtype |
|---|---|
| user_id | int64 |
| jtbd_segment | str |
| cohort | str |
| age | int64 |
| logins_per_week | float64 |
| multi_currency | bool |
| family_status | bool |
| premium | bool |
| support_tickets | int64 |
| kyc_duration_days | float64 |

## Data Quality

- Duplicated rows: **0**
- Constant columns: **0**
- Пропусков нет.

## Numeric Distributions

| Column | n | mean | median | std | p25 | p75 | p95 | outliers | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| user_id | 40000 | 19999.5 | 19999.5 | 11547.1497 | 9999.75 | 29999.25 | 37999.05 | 0.0% | 0.0 |
| age | 40000 | 36.4928 | 35.0 | 9.5067 | 29.0 | 42.0 | 55.0 | 0.2% | 0.6417 |
| logins_per_week | 40000 | 6.6311 | 6.7 | 3.37 | 4.1 | 9.2 | 12.0 | 0.0% | 0.0112 |
| support_tickets | 40000 | 1.5415 | 1.0 | 1.6121 | 0.0 | 2.0 | 5.0 | 2.9% | 1.4527 |
| kyc_duration_days | 40000 | 4.2395 | 3.5 | 2.8507 | 2.2 | 5.6 | 10.0 | 2.5% | 0.8782 |

## Categorical Slices

**jtbd_segment** — кардинальность 5

| Value | Count | Share |
|---|---:|---:|
| young_professionals | 12000 | 30.0% |
| family_budgeters | 10000 | 25.0% |
| digital_newcomers | 8000 | 20.0% |
| travelers | 6000 | 15.0% |
| premium_status | 4000 | 10.0% |

**cohort** — кардинальность 4

| Value | Count | Share |
|---|---:|---:|
| Casual | 13355 | 33.4% |
| Growth | 12730 | 31.8% |
| Power | 8227 | 20.6% |
| Dormant | 5688 | 14.2% |

**multi_currency** — кардинальность 2

| Value | Count | Share |
|---|---:|---:|
| False | 28058 | 70.2% |
| True | 11942 | 29.8% |

**family_status** — кардинальность 2

| Value | Count | Share |
|---|---:|---:|
| False | 25308 | 63.3% |
| True | 14692 | 36.7% |

**premium** — кардинальность 2

| Value | Count | Share |
|---|---:|---:|
| False | 29133 | 72.8% |
| True | 10867 | 27.2% |

## Correlations

| Pair | r | Note |
|---|---:|---|
| age ~ kyc_duration_days | 0.7463 | moderate |
| age ~ logins_per_week | -0.6228 | moderate |
| logins_per_week ~ kyc_duration_days | -0.6226 | moderate |
| support_tickets ~ kyc_duration_days | 0.5433 | moderate |
| age ~ support_tickets | 0.5399 | moderate |

## Metric by Segment

### jtbd_segment (overall mean = 4.2395, gap x4.2082)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| digital_newcomers | 8000 | 8.9913 | 71930.6 | 42.4% | +112.1% |
| family_budgeters | 10000 | 4.0359 | 40359.2 | 23.8% | -4.8% |
| young_professionals | 12000 | 2.5351 | 30421.4 | 17.9% | -40.2% |
| travelers | 6000 | 3.0535 | 18321.0 | 10.8% | -28.0% |
| premium_status | 4000 | 2.1366 | 8546.4 | 5.0% | -49.6% |

### cohort (overall mean = 4.2395, gap x2.3727)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| Casual | 13355 | 4.7978 | 64074.6 | 37.8% | +13.2% |
| Growth | 12730 | 3.5798 | 45570.6 | 26.9% | -15.6% |
| Dormant | 5688 | 6.5462 | 37235.0 | 22.0% | +54.4% |
| Power | 8227 | 2.759 | 22698.4 | 13.4% | -34.9% |

### family_status (overall mean = 4.2395, gap x1.2413)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| False | 25308 | 3.8943 | 98557.6 | 58.1% | -8.1% |
| True | 14692 | 4.834 | 71021.0 | 41.9% | +14.0% |


## Findings

- **[INFO]** Разрыв по jtbd_segment: x4.2082 между сегментами — кандидат в главный вывод
- **[INFO]** Разрыв по cohort: x2.3727 между сегментами — кандидат в главный вывод

## What We Did Not Cover

- Причинность: корреляции не доказывают влияние.
- Внешние источники и бизнес-контекст, которых нет в датасете.
- Формальные тесты гипотез (это CDA / A-B testing).

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py --input <dataset> \
    [--metric <col>] [--segments <a,b>] [--time-col <col>] [--top <n>]
```
