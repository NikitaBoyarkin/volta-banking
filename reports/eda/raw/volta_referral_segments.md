# EDA Report

**Rows:** 40000 · **Columns:** 7 · **Memory:** 9.68 MB

## Profile

| Column | dtype |
|---|---|
| referral_id | int64 |
| referee_id | int64 |
| jtbd_segment | str |
| cohort | str |
| channel | str |
| status | str |
| reward_eur | float64 |

## Data Quality

- Duplicated rows: **0**
- Constant columns: **0**
- Пропусков нет.

## Numeric Distributions

| Column | n | mean | median | std | p25 | p75 | p95 | outliers | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| referral_id | 40000 | 20000.5 | 20000.5 | 11547.1497 | 10000.75 | 30000.25 | 38000.05 | 0.0% | 0.0 |
| referee_id | 40000 | 20000.5 | 20000.5 | 11547.1497 | 10000.75 | 30000.25 | 38000.05 | 0.0% | 0.0 |
| reward_eur | 40000 | 4.5373 | 0.0 | 7.8989 | 0.0 | 10.0 | 20.0 | 0.0% | 1.2971 |

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
| Casual | 13448 | 33.6% |
| Growth | 12648 | 31.6% |
| Power | 8204 | 20.5% |
| Dormant | 5700 | 14.2% |

**status** — кардинальность 4

| Value | Count | Share |
|---|---:|---:|
| sent | 17129 | 42.8% |
| accepted | 12243 | 30.6% |
| first_tx | 7521 | 18.8% |
| kyc_completed | 3107 | 7.8% |

**channel** — кардинальность 3

| Value | Count | Share |
|---|---:|---:|
| in_app | 19912 | 49.8% |
| email | 12147 | 30.4% |
| link | 7941 | 19.9% |

## Correlations

| Pair | r | Note |
|---|---:|---|
| referral_id ~ referee_id | 1.0 | multicollinearity |

## Metric by Segment

### jtbd_segment (overall mean = 4.5373, gap x7.6248)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| young_professionals | 12000 | 7.1892 | 86270.0 | 47.5% | +58.5% |
| premium_status | 4000 | 8.645 | 34580.0 | 19.1% | +90.5% |
| travelers | 6000 | 5.1183 | 30710.0 | 16.9% | +12.8% |
| family_budgeters | 10000 | 2.086 | 20860.0 | 11.5% | -54.0% |
| digital_newcomers | 8000 | 1.1338 | 9070.0 | 5.0% | -75.0% |

### cohort (overall mean = 4.5373, gap x5.0442)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| Growth | 12648 | 5.3906 | 68180.0 | 37.6% | +18.8% |
| Power | 8204 | 7.4781 | 61350.0 | 33.8% | +64.8% |
| Casual | 13448 | 3.2354 | 43510.0 | 24.0% | -28.7% |
| Dormant | 5700 | 1.4825 | 8450.0 | 4.7% | -67.3% |

### channel (overall mean = 4.5373, gap x1.4354)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| in_app | 19912 | 4.9744 | 99050.0 | 54.6% | +9.6% |
| email | 12147 | 4.5213 | 54920.0 | 30.3% | -0.4% |
| link | 7941 | 3.4656 | 27520.0 | 15.2% | -23.6% |

### status (overall mean = 4.5373, gap x0.0)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| first_tx | 7521 | 20.0 | 150420.0 | 82.9% | +340.8% |
| kyc_completed | 3107 | 10.0 | 31070.0 | 17.1% | +120.4% |
| accepted | 12243 | 0.0 | 0.0 | 0.0% | -100.0% |
| sent | 17129 | 0.0 | 0.0 | 0.0% | -100.0% |


## Findings

- **[WARN]** referral_id ~ referee_id: r=1.0 — мультиколлинеарность или дубль признака
- **[INFO]** Разрыв по jtbd_segment: x7.6248 между сегментами — кандидат в главный вывод
- **[INFO]** Разрыв по cohort: x5.0442 между сегментами — кандидат в главный вывод

## What We Did Not Cover

- Причинность: корреляции не доказывают влияние.
- Внешние источники и бизнес-контекст, которых нет в датасете.
- Формальные тесты гипотез (это CDA / A-B testing).

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py --input <dataset> \
    [--metric <col>] [--segments <a,b>] [--time-col <col>] [--top <n>]
```
