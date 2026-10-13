# EDA Report

**Rows:** 10000 · **Columns:** 9 · **Memory:** 0.94 MB

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

### group (overall mean = 0.5868, gap x1.1025)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| treatment | 5000 | 0.6154 | 3077.0 | 52.4% | +4.9% |
| control | 5000 | 0.5582 | 2791.0 | 47.6% | -4.9% |

### age_group (overall mean = 0.5868, gap x1.2013)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| 25-34 | 3457 | 0.5959 | 2060.0 | 35.1% | +1.6% |
| 35-44 | 2993 | 0.6308 | 1888.0 | 32.2% | +7.5% |
| 18-24 | 2053 | 0.5524 | 1134.0 | 19.3% | -5.9% |
| 45+ | 1497 | 0.5251 | 786.0 | 13.4% | -10.5% |

### device (overall mean = 0.5868, gap x1.022)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| android | 4512 | 0.5816 | 2624.0 | 44.7% | -0.9% |
| ios | 4031 | 0.5944 | 2396.0 | 40.8% | +1.3% |
| web | 1457 | 0.582 | 848.0 | 14.4% | -0.8% |

### channel (overall mean = 0.5868, gap x1.094)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| google_play | 2949 | 0.6066 | 1789.0 | 30.5% | +3.4% |
| app_store | 3026 | 0.5829 | 1764.0 | 30.1% | -0.7% |
| website | 2569 | 0.5562 | 1429.0 | 24.3% | -5.2% |
| referral | 1456 | 0.6085 | 886.0 | 15.1% | +3.7% |


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
