# EDA Report

**Rows:** 11 · **Columns:** 6 · **Memory:** 0.0 MB

## Profile

| Column | dtype |
|---|---|
| segment | str |
| control | float64 |
| treatment | float64 |
| lift | float64 |
| p_value | float64 |
| significant | bool |

## Data Quality

- Duplicated rows: **0**
- Constant columns: **0**
- Пропусков нет.

## Numeric Distributions

| Column | n | mean | median | std | p25 | p75 | p95 | outliers | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| control | 11 | 0.5546 | 0.558 | 0.0229 | 0.537 | 0.5711 | 0.5836 | 0.0% | -0.2106 |
| treatment | 11 | 0.6119 | 0.612 | 0.0423 | 0.5885 | 0.6363 | 0.6716 | 0.0% | -0.1128 |
| lift | 11 | 5.7273 | 5.3 | 3.4109 | 3.1 | 8.45 | 10.5 | 0.0% | 0.241 |
| p_value | 11 | 0.1087 | 0.0179 | 0.1974 | 0.0001 | 0.0772 | 0.4789 | 18.2% | 2.2976 |

## Categorical Slices

**segment** — кардинальность 11

| Value | Count | Share |
|---|---:|---:|
| age_group=35-44 | 1 | 9.1% |
| age_group=25-34 | 1 | 9.1% |
| age_group=45+ | 1 | 9.1% |
| age_group=18-24 | 1 | 9.1% |
| device=android | 1 | 9.1% |
| device=ios | 1 | 9.1% |
| device=web | 1 | 9.1% |
| channel=website | 1 | 9.1% |
| channel=app_store | 1 | 9.1% |
| channel=google_play | 1 | 9.1% |

**significant** — кардинальность 2

| Value | Count | Share |
|---|---:|---:|
| True | 6 | 54.5% |
| False | 5 | 45.5% |

## Correlations

| Pair | r | Note |
|---|---:|---|
| treatment ~ lift | 0.8405 | multicollinearity |
| treatment ~ p_value | -0.6858 | moderate |
| lift ~ p_value | -0.6815 | moderate |
| control ~ treatment | 0.5909 | moderate |

## Metric by Segment

### segment (overall mean = 5.7273, gap x7.8571)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| age_group=35-44 | 1 | 11.0 | 11.0 | 17.5% | +92.1% |
| channel=referral | 1 | 10.0 | 10.0 | 15.9% | +74.6% |
| device=android | 1 | 9.1 | 9.1 | 14.4% | +58.9% |
| channel=google_play | 1 | 7.8 | 7.8 | 12.4% | +36.2% |
| device=web | 1 | 6.8 | 6.8 | 10.8% | +18.7% |
| age_group=18-24 | 1 | 5.3 | 5.3 | 8.4% | -7.5% |
| channel=website | 1 | 3.8 | 3.8 | 6.0% | -33.7% |
| age_group=25-34 | 1 | 3.1 | 3.1 | 4.9% | -45.9% |
| channel=app_store | 1 | 3.1 | 3.1 | 4.9% | -45.9% |
| device=ios | 1 | 1.6 | 1.6 | 2.5% | -72.1% |
| age_group=45+ | 1 | 1.4 | 1.4 | 2.2% | -75.6% |


## Findings

- **[WARN]** Выбросов в p_value: 18% — проверить, сигнал или ошибка
- **[INFO]** p_value: правосторонний скос (2.2976) — медиана надёжнее среднего
- **[WARN]** treatment ~ lift: r=0.8405 — мультиколлинеарность или дубль признака
- **[INFO]** Разрыв по segment: x7.8571 между сегментами — кандидат в главный вывод

## What We Did Not Cover

- Причинность: корреляции не доказывают влияние.
- Внешние источники и бизнес-контекст, которых нет в датасете.
- Формальные тесты гипотез (это CDA / A-B testing).

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py --input <dataset> \
    [--metric <col>] [--segments <a,b>] [--time-col <col>] [--top <n>]
```
