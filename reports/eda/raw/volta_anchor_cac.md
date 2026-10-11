# EDA Report

**Rows:** 460 · **Columns:** 7 · **Memory:** 0.05 MB

## Profile

| Column | dtype |
|---|---|
| bucket_id | int64 |
| channel | str |
| users | int64 |
| marginal_cac_eur | float64 |
| arpu_eur | float64 |
| monthly_churn_rate | float64 |
| ltv_eur | float64 |

## Data Quality

- Duplicated rows: **0**
- Constant columns: **1** (users)
- Пропусков нет.

## Numeric Distributions

| Column | n | mean | median | std | p25 | p75 | p95 | outliers | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bucket_id | 460 | 230.5 | 230.5 | 132.9348 | 115.75 | 345.25 | 437.05 | 0.0% | 0.0 |
| users | 460 | 1000.0 | 1000.0 | 0.0 | 1000.0 | 1000.0 | 1000.0 | 0.0% | 0.0 |
| marginal_cac_eur | 460 | 112.6674 | 80.96 | 81.4982 | 54.705 | 145.5325 | 299.588 | 5.9% | 1.256 |
| arpu_eur | 460 | 4.3478 | 4.4 | 0.1381 | 4.2 | 4.5 | 4.5 | 0.0% | 0.0953 |
| monthly_churn_rate | 460 | 0.0359 | 0.035 | 0.0039 | 0.033 | 0.04 | 0.04 | 0.0% | -0.273 |
| ltv_eur | 460 | 86.0887 | 88.0 | 12.3685 | 73.5 | 95.45 | 102.67 | 0.0% | 0.4229 |

## Categorical Slices

**channel** — кардинальность 5

| Value | Count | Share |
|---|---:|---:|
| paid_social | 200 | 43.5% |
| in_app | 120 | 26.1% |
| partner | 80 | 17.4% |
| referral | 40 | 8.7% |
| assisted | 20 | 4.3% |

## Correlations

| Pair | r | Note |
|---|---:|---|
| monthly_churn_rate ~ ltv_eur | -0.9959 | multicollinearity |
| arpu_eur ~ ltv_eur | 0.9334 | multicollinearity |
| arpu_eur ~ monthly_churn_rate | -0.9248 | multicollinearity |
| bucket_id ~ marginal_cac_eur | 0.8637 | multicollinearity |
| bucket_id ~ monthly_churn_rate | 0.6361 | moderate |
| bucket_id ~ arpu_eur | -0.6031 | moderate |
| bucket_id ~ ltv_eur | -0.5826 | moderate |
| marginal_cac_eur ~ arpu_eur | -0.5161 | moderate |
| marginal_cac_eur ~ monthly_churn_rate | 0.5143 | moderate |

## Metric by Segment

### channel (overall mean = 86.0887, gap x1.5646)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| paid_social | 200 | 73.5 | 14700.0 | 37.1% | -14.6% |
| in_app | 120 | 95.45 | 11454.0 | 28.9% | +10.9% |
| partner | 80 | 88.0 | 7040.0 | 17.8% | +2.2% |
| referral | 40 | 102.67 | 4106.8 | 10.4% | +19.3% |
| assisted | 20 | 115.0 | 2300.0 | 5.8% | +33.6% |


## Findings

- **[WARN]** Константная колонка users — не несёт информации
- **[WARN]** Выбросов в marginal_cac_eur: 6% — проверить, сигнал или ошибка
- **[WARN]** monthly_churn_rate ~ ltv_eur: r=-0.9959 — мультиколлинеарность или дубль признака
- **[WARN]** arpu_eur ~ ltv_eur: r=0.9334 — мультиколлинеарность или дубль признака
- **[WARN]** arpu_eur ~ monthly_churn_rate: r=-0.9248 — мультиколлинеарность или дубль признака
- **[WARN]** bucket_id ~ marginal_cac_eur: r=0.8637 — мультиколлинеарность или дубль признака
- **[INFO]** Разрыв по channel: x1.5646 между сегментами — кандидат в главный вывод

## What We Did Not Cover

- Причинность: корреляции не доказывают влияние.
- Внешние источники и бизнес-контекст, которых нет в датасете.
- Формальные тесты гипотез (это CDA / A-B testing).

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py --input <dataset> \
    [--metric <col>] [--segments <a,b>] [--time-col <col>] [--top <n>]
```
