# EDA Report

**Rows:** 36000 · **Columns:** 9 · **Memory:** 7.75 MB

## Profile

| Column | dtype |
|---|---|
| user_id | int64 |
| jtbd_segment | str |
| dormancy_bucket | str |
| group | str |
| balance_eur | float64 |
| prior_logins | float64 |
| reactivated_60d | int64 |
| retained_m3 | int64 |
| arpu_eur | float64 |

## Data Quality

- Duplicated rows: **0**
- Constant columns: **2** (jtbd_segment, arpu_eur)
- Пропусков нет.

## Numeric Distributions

| Column | n | mean | median | std | p25 | p75 | p95 | outliers | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| user_id | 36000 | 18000.5 | 18000.5 | 10392.4492 | 9000.75 | 27000.25 | 34200.05 | 0.0% | 0.0 |
| balance_eur | 36000 | 337.6402 | 241.955 | 321.7802 | 142.02 | 419.15 | 919.282 | 6.3% | 3.5162 |
| prior_logins | 36000 | 6.0172 | 6.0 | 2.4597 | 4.3 | 7.7 | 10.1 | 0.4% | 0.1382 |
| reactivated_60d | 36000 | 0.0739 | 0.0 | 0.2615 | 0.0 | 0.0 | 1.0 | 0.0% | 3.2588 |
| retained_m3 | 36000 | 0.0462 | 0.0 | 0.2098 | 0.0 | 0.0 | 0.0 | 0.0% | 4.3256 |
| arpu_eur | 36000 | 3.4 | 3.4 | 0.0 | 3.4 | 3.4 | 3.4 | 0.0% | 1.0 |

## Categorical Slices

**dormancy_bucket** — кардинальность 4

| Value | Count | Share |
|---|---:|---:|
| 30-60d | 9000 | 25.0% |
| 60-90d | 9000 | 25.0% |
| 90-180d | 9000 | 25.0% |
| 180d+ | 9000 | 25.0% |

**group** — кардинальность 3

| Value | Count | Share |
|---|---:|---:|
| control | 12000 | 33.3% |
| light_touch | 12000 | 33.3% |
| human | 12000 | 33.3% |

**jtbd_segment** — кардинальность 1

| Value | Count | Share |
|---|---:|---:|
| digital_newcomers | 36000 | 100.0% |

## Correlations

| Pair | r | Note |
|---|---:|---|
| reactivated_60d ~ retained_m3 | 0.779 | moderate |

## Metric by Segment

### jtbd_segment (overall mean = 0.0739, gap x0.0)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| digital_newcomers | 36000 | 0.0739 | 2659.0 | 100.0% | +0.0% |

### dormancy_bucket (overall mean = 0.0739, gap x8.0)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| 30-60d | 9000 | 0.1424 | 1282.0 | 48.2% | +92.8% |
| 60-90d | 9000 | 0.0894 | 805.0 | 30.3% | +21.1% |
| 90-180d | 9000 | 0.0458 | 412.0 | 15.5% | -38.0% |
| 180d+ | 9000 | 0.0178 | 160.0 | 6.0% | -75.9% |

### group (overall mean = 0.0739, gap x2.1432)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| human | 12000 | 0.1003 | 1203.0 | 45.2% | +35.7% |
| light_touch | 12000 | 0.0745 | 894.0 | 33.6% | +0.9% |
| control | 12000 | 0.0468 | 562.0 | 21.1% | -36.6% |


## Findings

- **[WARN]** Константная колонка jtbd_segment — не несёт информации
- **[WARN]** Константная колонка arpu_eur — не несёт информации
- **[WARN]** Выбросов в balance_eur: 6% — проверить, сигнал или ошибка
- **[INFO]** balance_eur: правосторонний скос (3.5162) — медиана надёжнее среднего
- **[INFO]** reactivated_60d: правосторонний скос (3.2588) — медиана надёжнее среднего
- **[INFO]** retained_m3: правосторонний скос (4.3256) — медиана надёжнее среднего
- **[INFO]** Разрыв по dormancy_bucket: x8.0 между сегментами — кандидат в главный вывод
- **[INFO]** Разрыв по group: x2.1432 между сегментами — кандидат в главный вывод

## What We Did Not Cover

- Причинность: корреляции не доказывают влияние.
- Внешние источники и бизнес-контекст, которых нет в датасете.
- Формальные тесты гипотез (это CDA / A-B testing).

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py --input <dataset> \
    [--metric <col>] [--segments <a,b>] [--time-col <col>] [--top <n>]
```
