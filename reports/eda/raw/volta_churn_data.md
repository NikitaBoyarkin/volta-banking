# EDA Report

**Rows:** 15000 · **Columns:** 12 · **Memory:** 2.09 MB

## Profile

| Column | dtype |
|---|---|
| customer_id | int64 |
| usage_frequency | float64 |
| avg_transaction_value | float64 |
| days_since_last_activity | int64 |
| support_tickets | int64 |
| device_error_rate | float64 |
| age | int64 |
| is_premium | int64 |
| customer_tenure_months | int64 |
| signup_month | int64 |
| channel | str |
| churned | int64 |

## Data Quality

- Duplicated rows: **0**
- Constant columns: **0**
- Пропусков нет.

## Numeric Distributions

| Column | n | mean | median | std | p25 | p75 | p95 | outliers | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| customer_id | 15000 | 7499.5 | 7499.5 | 4330.2714 | 3749.75 | 11249.25 | 14249.05 | 0.0% | 0.0 |
| usage_frequency | 15000 | 0.2861 | 0.266 | 0.1593 | 0.1615 | 0.3912 | 0.575 | 0.6% | 0.5674 |
| avg_transaction_value | 15000 | 31.3573 | 24.3 | 25.0528 | 15.28 | 39.5175 | 77.1405 | 5.3% | 2.8702 |
| days_since_last_activity | 15000 | 44.5277 | 45.0 | 25.747 | 22.0 | 67.0 | 85.0 | 0.0% | 0.0015 |
| support_tickets | 15000 | 0.6025 | 0.0 | 0.7822 | 0.0 | 1.0 | 2.0 | 2.5% | 1.3076 |
| device_error_rate | 15000 | 0.2078 | 0.1666 | 0.1618 | 0.0877 | 0.2867 | 0.5265 | 3.4% | 1.3726 |
| age | 15000 | 43.4137 | 43.0 | 15.078 | 30.0 | 57.0 | 67.0 | 0.0% | 0.0119 |
| is_premium | 15000 | 0.1777 | 0.0 | 0.3823 | 0.0 | 0.0 | 1.0 | 0.0% | 1.6862 |
| customer_tenure_months | 15000 | 23.8857 | 24.0 | 13.538 | 12.0 | 36.0 | 45.0 | 0.0% | 0.0054 |
| signup_month | 15000 | 12.5668 | 13.0 | 6.9467 | 7.0 | 19.0 | 23.0 | 0.0% | -0.0131 |
| churned | 15000 | 0.4071 | 0.0 | 0.4913 | 0.0 | 1.0 | 1.0 | 0.0% | 0.3781 |

## Categorical Slices

**channel** — кардинальность 4

| Value | Count | Share |
|---|---:|---:|
| app_store | 4469 | 29.8% |
| google_play | 4434 | 29.6% |
| website | 3882 | 25.9% |
| referral | 2215 | 14.8% |

## Correlations

_Пар с |r| >= 0.5 нет._

## Metric by Segment

### channel (overall mean = 0.4071, gap x1.1342)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| app_store | 4469 | 0.3976 | 1777.0 | 29.1% | -2.3% |
| google_play | 4434 | 0.3911 | 1734.0 | 28.4% | -4.0% |
| website | 3882 | 0.4436 | 1722.0 | 28.2% | +8.9% |
| referral | 2215 | 0.3946 | 874.0 | 14.3% | -3.1% |

### is_premium (overall mean = 0.4071, gap x1.2358)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| 0.0 | 12334 | 0.4214 | 5198.0 | 85.1% | +3.5% |
| 1.0 | 2666 | 0.341 | 909.0 | 14.9% | -16.2% |


## Findings

- **[WARN]** Выбросов в avg_transaction_value: 5% — проверить, сигнал или ошибка
- **[INFO]** avg_transaction_value: правосторонний скос (2.8702) — медиана надёжнее среднего

## What We Did Not Cover

- Причинность: корреляции не доказывают влияние.
- Внешние источники и бизнес-контекст, которых нет в датасете.
- Формальные тесты гипотез (это CDA / A-B testing).

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py --input <dataset> \
    [--metric <col>] [--segments <a,b>] [--time-col <col>] [--top <n>]
```
