# EDA Report

**Rows:** 82000 · **Columns:** 9 · **Memory:** 21.16 MB

## Profile

| Column | dtype |
|---|---|
| user_id | int64 |
| jtbd_segment | str |
| cohort | str |
| group | str |
| logins_per_week | float64 |
| tx_per_month | int64 |
| balance_eur | float64 |
| converted | int64 |
| upgrade_reason | str |

## Data Quality

- Duplicated rows: **0**
- Constant columns: **0**
- Пропусков нет.

## Numeric Distributions

| Column | n | mean | median | std | p25 | p75 | p95 | outliers | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| user_id | 82000 | 41000.5 | 41000.5 | 23671.5054 | 20500.75 | 61500.25 | 77900.05 | 0.0% | 0.0 |
| logins_per_week | 82000 | 5.1625 | 4.3 | 3.3228 | 2.6 | 7.1 | 11.7 | 1.8% | 1.0043 |
| tx_per_month | 82000 | 12.2825 | 11.0 | 7.1989 | 7.0 | 16.0 | 27.0 | 2.7% | 0.9209 |
| balance_eur | 82000 | 611.4663 | 468.245 | 480.6416 | 283.1675 | 806.4625 | 1628.315 | 5.4% | 1.4633 |
| converted | 82000 | 0.0838 | 0.0 | 0.2771 | 0.0 | 0.0 | 1.0 | 0.0% | 3.0038 |

## Categorical Slices

**upgrade_reason** — кардинальность 5

| Value | Count | Share |
|---|---:|---:|
| none | 75127 | 91.6% |
| premium_features | 2759 | 3.4% |
| cashback | 1835 | 2.2% |
| support | 1266 | 1.5% |
| status | 1013 | 1.2% |

**jtbd_segment** — кардинальность 4

| Value | Count | Share |
|---|---:|---:|
| digital_newcomers | 30000 | 36.6% |
| family_budgeters | 24000 | 29.3% |
| young_professionals | 16000 | 19.5% |
| travelers | 12000 | 14.6% |

**cohort** — кардинальность 4

| Value | Count | Share |
|---|---:|---:|
| Casual | 28732 | 35.0% |
| Growth | 24555 | 29.9% |
| Dormant | 16368 | 20.0% |
| Power | 12345 | 15.0% |

**group** — кардинальность 2

| Value | Count | Share |
|---|---:|---:|
| control | 41000 | 50.0% |
| treatment | 41000 | 50.0% |

## Correlations

| Pair | r | Note |
|---|---:|---|
| logins_per_week ~ balance_eur | 0.5024 | moderate |

## Metric by Segment

### jtbd_segment (overall mean = 0.0838, gap x5.811)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| young_professionals | 16000 | 0.1906 | 3049.0 | 44.4% | +127.4% |
| family_budgeters | 24000 | 0.065 | 1559.0 | 22.7% | -22.5% |
| travelers | 12000 | 0.1067 | 1281.0 | 18.6% | +27.4% |
| digital_newcomers | 30000 | 0.0328 | 984.0 | 14.3% | -60.9% |

### cohort (overall mean = 0.0838, gap x3.7721)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| Growth | 24555 | 0.1074 | 2637.0 | 38.4% | +28.1% |
| Casual | 28732 | 0.0705 | 2027.0 | 29.5% | -15.8% |
| Power | 12345 | 0.1324 | 1634.0 | 23.8% | +57.9% |
| Dormant | 16368 | 0.0351 | 575.0 | 8.4% | -58.1% |

### group (overall mean = 0.0838, gap x1.4647)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| treatment | 41000 | 0.0996 | 4084.0 | 59.4% | +18.8% |
| control | 41000 | 0.068 | 2789.0 | 40.6% | -18.8% |


## Findings

- **[WARN]** Выбросов в balance_eur: 5% — проверить, сигнал или ошибка
- **[INFO]** converted: правосторонний скос (3.0038) — медиана надёжнее среднего
- **[INFO]** Разрыв по jtbd_segment: x5.811 между сегментами — кандидат в главный вывод
- **[INFO]** Разрыв по cohort: x3.7721 между сегментами — кандидат в главный вывод

## What We Did Not Cover

- Причинность: корреляции не доказывают влияние.
- Внешние источники и бизнес-контекст, которых нет в датасете.
- Формальные тесты гипотез (это CDA / A-B testing).

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py --input <dataset> \
    [--metric <col>] [--segments <a,b>] [--time-col <col>] [--top <n>]
```
