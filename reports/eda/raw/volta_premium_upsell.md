# EDA Report

**Rows:** 40000 · **Columns:** 10 · **Memory:** 10.51 MB

## Profile

| Column | dtype |
|---|---|
| user_id | int64 |
| jtbd_segment | str |
| cohort | str |
| months_since_signup | int64 |
| logins_per_week | float64 |
| tx_per_month | int64 |
| balance_eur | float64 |
| offer_channel | str |
| converted | int64 |
| upgrade_reason | str |

## Data Quality

- Duplicated rows: **0**
- Constant columns: **0**
- Пропусков нет.

## Numeric Distributions

| Column | n | mean | median | std | p25 | p75 | p95 | outliers | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| user_id | 40000 | 20000.5 | 20000.5 | 11547.1497 | 10000.75 | 30000.25 | 38000.05 | 0.0% | 0.0 |
| months_since_signup | 40000 | 12.5362 | 13.0 | 6.8955 | 7.0 | 19.0 | 23.0 | 0.0% | -0.0069 |
| logins_per_week | 40000 | 6.5955 | 6.0 | 3.9641 | 3.4 | 9.1 | 14.0 | 0.9% | 0.744 |
| tx_per_month | 40000 | 14.4249 | 14.0 | 7.0698 | 9.0 | 19.0 | 27.0 | 0.5% | 0.5441 |
| balance_eur | 40000 | 969.5867 | 662.575 | 973.8436 | 358.87 | 1239.015 | 3000.594 | 6.6% | 2.3774 |
| converted | 40000 | 0.126 | 0.0 | 0.3319 | 0.0 | 0.0 | 1.0 | 0.0% | 2.2538 |

## Categorical Slices

**jtbd_segment** — кардинальность 5

| Value | Count | Share |
|---|---:|---:|
| young_professionals | 12000 | 30.0% |
| family_budgeters | 10000 | 25.0% |
| digital_newcomers | 8000 | 20.0% |
| travelers | 6000 | 15.0% |
| premium_status | 4000 | 10.0% |

**upgrade_reason** — кардинальность 5

| Value | Count | Share |
|---|---:|---:|
| none | 34959 | 87.4% |
| premium_features | 1909 | 4.8% |
| status | 1257 | 3.1% |
| cashback | 1173 | 2.9% |
| support | 702 | 1.8% |

**cohort** — кардинальность 4

| Value | Count | Share |
|---|---:|---:|
| Casual | 13481 | 33.7% |
| Growth | 12459 | 31.1% |
| Power | 8324 | 20.8% |
| Dormant | 5736 | 14.3% |

**offer_channel** — кардинальность 4

| Value | Count | Share |
|---|---:|---:|
| in_app | 12000 | 30.0% |
| email | 11975 | 29.9% |
| none | 8030 | 20.1% |
| push | 7995 | 20.0% |

## Correlations

_Пар с |r| >= 0.5 нет._

## Metric by Segment

### jtbd_segment (overall mean = 0.126, gap x23.0168)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| young_professionals | 12000 | 0.1725 | 2070.0 | 41.1% | +36.9% |
| premium_status | 4000 | 0.412 | 1648.0 | 32.7% | +226.9% |
| travelers | 6000 | 0.119 | 714.0 | 14.2% | -5.6% |
| family_budgeters | 10000 | 0.0466 | 466.0 | 9.2% | -63.0% |
| digital_newcomers | 8000 | 0.0179 | 143.0 | 2.8% | -85.8% |

### cohort (overall mean = 0.126, gap x12.1991)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| Power | 8324 | 0.2574 | 2143.0 | 42.5% | +104.3% |
| Growth | 12459 | 0.1482 | 1846.0 | 36.6% | +17.6% |
| Casual | 13481 | 0.0691 | 931.0 | 18.5% | -45.2% |
| Dormant | 5736 | 0.0211 | 121.0 | 2.4% | -83.3% |

### offer_channel (overall mean = 0.126, gap x2.3391)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| in_app | 12000 | 0.1628 | 1953.0 | 38.7% | +29.1% |
| email | 11975 | 0.132 | 1581.0 | 31.4% | +4.8% |
| push | 7995 | 0.1186 | 948.0 | 18.8% | -5.9% |
| none | 8030 | 0.0696 | 559.0 | 11.1% | -44.8% |


## Findings

- **[WARN]** Выбросов в balance_eur: 7% — проверить, сигнал или ошибка
- **[INFO]** balance_eur: правосторонний скос (2.3774) — медиана надёжнее среднего
- **[INFO]** converted: правосторонний скос (2.2538) — медиана надёжнее среднего
- **[INFO]** Разрыв по jtbd_segment: x23.0168 между сегментами — кандидат в главный вывод
- **[INFO]** Разрыв по cohort: x12.1991 между сегментами — кандидат в главный вывод
- **[INFO]** Разрыв по offer_channel: x2.3391 между сегментами — кандидат в главный вывод

## What We Did Not Cover

- Причинность: корреляции не доказывают влияние.
- Внешние источники и бизнес-контекст, которых нет в датасете.
- Формальные тесты гипотез (это CDA / A-B testing).

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py --input <dataset> \
    [--metric <col>] [--segments <a,b>] [--time-col <col>] [--top <n>]
```
