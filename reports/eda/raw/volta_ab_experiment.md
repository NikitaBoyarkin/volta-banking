# EDA Report

**Rows:** 10000 · **Columns:** 9 · **Memory:** 2.5 MB

## Profile

| Column | dtype |
|---|---|
| customer_id | int64 |
| group | str |
| age_group | str |
| device | str |
| channel | str |
| pre_kyc_rate | float64 |
| kyc_completed | int64 |
| churned_30d | int64 |
| revenue_30d_eur | float64 |

## Data Quality

- Duplicated rows: **0**
- Constant columns: **0**
- Пропусков нет.

## Numeric Distributions

| Column | n | mean | median | std | p25 | p75 | p95 | outliers | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| customer_id | 10000 | 4999.5 | 4999.5 | 2886.8957 | 2499.75 | 7499.25 | 9499.05 | 0.0% | 0.0 |
| pre_kyc_rate | 10000 | 0.5673 | 0.5686 | 0.0926 | 0.5059 | 0.6304 | 0.7189 | 0.7% | -0.0626 |
| kyc_completed | 10000 | 0.5868 | 1.0 | 0.4924 | 0.0 | 1.0 | 1.0 | 0.0% | -0.3526 |
| churned_30d | 10000 | 0.1728 | 0.0 | 0.3781 | 0.0 | 0.0 | 1.0 | 0.0% | 1.7311 |
| revenue_30d_eur | 10000 | 12.1093 | 11.84 | 8.6506 | 4.2 | 19.11 | 26.35 | 0.0% | 0.2685 |

## Categorical Slices

**age_group** — кардинальность 4

| Value | Count | Share |
|---|---:|---:|
| 25-34 | 3457 | 34.6% |
| 35-44 | 2993 | 29.9% |
| 18-24 | 2053 | 20.5% |
| 45+ | 1497 | 15.0% |

**channel** — кардинальность 4

| Value | Count | Share |
|---|---:|---:|
| app_store | 3026 | 30.3% |
| google_play | 2949 | 29.5% |
| website | 2569 | 25.7% |
| referral | 1456 | 14.6% |

**device** — кардинальность 3

| Value | Count | Share |
|---|---:|---:|
| android | 4512 | 45.1% |
| ios | 4031 | 40.3% |
| web | 1457 | 14.6% |

**group** — кардинальность 2

| Value | Count | Share |
|---|---:|---:|
| control | 5000 | 50.0% |
| treatment | 5000 | 50.0% |

## Correlations

| Pair | r | Note |
|---|---:|---|
| kyc_completed ~ revenue_30d_eur | 0.8119 | multicollinearity |

## Metric by Segment

### group (overall mean = 12.1093, gap x1.0731)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| treatment | 5000 | 12.5365 | 62682.43 | 51.8% | +3.5% |
| control | 5000 | 11.6821 | 58410.54 | 48.2% | -3.5% |

### age_group (overall mean = 12.1093, gap x1.1448)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| 25-34 | 3457 | 12.1942 | 42155.33 | 34.8% | +0.7% |
| 35-44 | 2993 | 12.861 | 38493.06 | 31.8% | +6.2% |
| 18-24 | 2053 | 11.5087 | 23627.29 | 19.5% | -5.0% |
| 45+ | 1497 | 11.234 | 16817.29 | 13.9% | -7.2% |

### device (overall mean = 12.1093, gap x1.0183)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| android | 4512 | 12.0466 | 54354.14 | 44.9% | -0.5% |
| ios | 4031 | 12.2191 | 49255.25 | 40.7% | +0.9% |
| web | 1457 | 11.9997 | 17483.58 | 14.4% | -0.9% |

### channel (overall mean = 12.1093, gap x1.0579)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| google_play | 2949 | 12.4021 | 36573.67 | 30.2% | +2.4% |
| app_store | 3026 | 12.0405 | 36434.65 | 30.1% | -0.6% |
| website | 2569 | 11.7231 | 30116.55 | 24.9% | -3.2% |
| referral | 1456 | 12.3407 | 17968.1 | 14.8% | +1.9% |


## Findings

- **[WARN]** kyc_completed ~ revenue_30d_eur: r=0.8119 — мультиколлинеарность или дубль признака

## What We Did Not Cover

- Причинность: корреляции не доказывают влияние.
- Внешние источники и бизнес-контекст, которых нет в датасете.
- Формальные тесты гипотез (это CDA / A-B testing).

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py --input <dataset> \
    [--metric <col>] [--segments <a,b>] [--time-col <col>] [--top <n>]
```
