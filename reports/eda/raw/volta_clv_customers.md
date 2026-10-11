# EDA Report

**Rows:** 12000 · **Columns:** 6 · **Memory:** 1.09 MB

## Profile

| Column | dtype |
|---|---|
| customer_id | int64 |
| segment | str |
| frequency | int64 |
| avg_tx_value | float64 |
| total_spend | float64 |
| lifetime_months | float64 |

## Data Quality

- Duplicated rows: **0**
- Constant columns: **0**
- Пропусков нет.

## Numeric Distributions

| Column | n | mean | median | std | p25 | p75 | p95 | outliers | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| customer_id | 12000 | 5999.5 | 5999.5 | 3464.2459 | 2999.75 | 8999.25 | 11399.05 | 0.0% | 0.0 |
| frequency | 12000 | 3.3697 | 1.0 | 7.7244 | 0.0 | 3.0 | 15.0 | 11.5% | 5.5238 |
| avg_tx_value | 12000 | 31.8395 | 19.665 | 38.5325 | 0.0 | 51.29 | 110.9285 | 2.0% | 1.4263 |
| total_spend | 12000 | 270.9514 | 22.72 | 811.8813 | 0.0 | 153.615 | 1390.293 | 14.4% | 6.1924 |
| lifetime_months | 12000 | 2.5822 | 1.5 | 2.7495 | 1.0 | 3.1 | 7.6 | 7.6% | 3.7439 |

## Categorical Slices

**segment** — кардинальность 4

| Value | Count | Share |
|---|---:|---:|
| Casual | 3849 | 32.1% |
| Dormant | 3795 | 31.6% |
| Growth | 2931 | 24.4% |
| Power | 1425 | 11.9% |

## Correlations

| Pair | r | Note |
|---|---:|---|
| frequency ~ total_spend | 0.9723 | multicollinearity |
| frequency ~ lifetime_months | 0.8205 | multicollinearity |
| total_spend ~ lifetime_months | 0.7393 | moderate |
| avg_tx_value ~ total_spend | 0.5522 | moderate |
| frequency ~ avg_tx_value | 0.5499 | moderate |

## Metric by Segment

### segment (overall mean = 270.9514, gap x358.3386)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| Power | 1425 | 1678.3862 | 2391700.28 | 73.6% | +519.4% |
| Growth | 2931 | 238.4727 | 698963.49 | 21.5% | -12.0% |
| Casual | 3849 | 37.1467 | 142977.68 | 4.4% | -86.3% |
| Dormant | 3795 | 4.6838 | 17775.02 | 0.5% | -98.3% |


## Findings

- **[WARN]** Выбросов в frequency: 11% — проверить, сигнал или ошибка
- **[INFO]** frequency: правосторонний скос (5.5238) — медиана надёжнее среднего
- **[WARN]** Выбросов в total_spend: 14% — проверить, сигнал или ошибка
- **[INFO]** total_spend: правосторонний скос (6.1924) — медиана надёжнее среднего
- **[WARN]** Выбросов в lifetime_months: 8% — проверить, сигнал или ошибка
- **[INFO]** lifetime_months: правосторонний скос (3.7439) — медиана надёжнее среднего
- **[WARN]** frequency ~ total_spend: r=0.9723 — мультиколлинеарность или дубль признака
- **[WARN]** frequency ~ lifetime_months: r=0.8205 — мультиколлинеарность или дубль признака
- **[INFO]** Разрыв по segment: x358.3386 между сегментами — кандидат в главный вывод

## What We Did Not Cover

- Причинность: корреляции не доказывают влияние.
- Внешние источники и бизнес-контекст, которых нет в датасете.
- Формальные тесты гипотез (это CDA / A-B testing).

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py --input <dataset> \
    [--metric <col>] [--segments <a,b>] [--time-col <col>] [--top <n>]
```
