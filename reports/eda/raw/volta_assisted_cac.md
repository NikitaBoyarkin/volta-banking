# EDA Report

**Rows:** 17000 · **Columns:** 9 · **Memory:** 2.9 MB

## Profile

| Column | dtype |
|---|---|
| user_id | int64 |
| segment | str |
| channel | str |
| cac_eur | float64 |
| monthly_arpu_eur | float64 |
| contribution_margin | float64 |
| monthly_churn_rate | float64 |
| months_retained | int64 |
| ltv_eur | float64 |

## Data Quality

- Duplicated rows: **0**
- Constant columns: **1** (contribution_margin)
- Пропусков нет.

## Numeric Distributions

| Column | n | mean | median | std | p25 | p75 | p95 | outliers | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| user_id | 17000 | 8500.5 | 8500.5 | 4907.6216 | 4250.75 | 12750.25 | 16150.05 | 0.0% | 0.0 |
| cac_eur | 17000 | 50.5407 | 36.63 | 30.2599 | 27.37 | 64.1325 | 121.4915 | 6.2% | 1.3602 |
| monthly_arpu_eur | 17000 | 3.7424 | 3.65 | 1.1073 | 2.97 | 4.41 | 5.75 | 1.4% | 0.4375 |
| contribution_margin | 17000 | 0.7 | 0.7 | 0.0 | 0.7 | 0.7 | 0.7 | 0.0% | 0.0 |
| monthly_churn_rate | 17000 | 0.0429 | 0.045 | 0.0102 | 0.035 | 0.051 | 0.063 | 0.0% | 0.4322 |
| months_retained | 17000 | 22.3838 | 17.0 | 18.4105 | 7.0 | 34.0 | 60.0 | 0.0% | 0.8087 |
| ltv_eur | 17000 | 59.7182 | 40.965 | 55.8423 | 17.25 | 86.3025 | 176.8405 | 3.7% | 1.3577 |

## Categorical Slices

**channel** — кардинальность 5

| Value | Count | Share |
|---|---:|---:|
| in_app | 5100 | 30.0% |
| referral | 4801 | 28.2% |
| partner | 2535 | 14.9% |
| paid_social | 2517 | 14.8% |
| assisted | 2047 | 12.0% |

**segment** — кардинальность 3

| Value | Count | Share |
|---|---:|---:|
| young_professionals | 6000 | 35.3% |
| digital_newcomers | 6000 | 35.3% |
| family_budgeters | 5000 | 29.4% |

## Correlations

| Pair | r | Note |
|---|---:|---|
| months_retained ~ ltv_eur | 0.909 | multicollinearity |

## Metric by Segment

### segment (overall mean = 59.7182, gap x1.9885)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| young_professionals | 6000 | 84.8948 | 509368.75 | 50.2% | +42.2% |
| digital_newcomers | 6000 | 42.692 | 256152.3 | 25.2% | -28.5% |
| family_budgeters | 5000 | 49.9376 | 249688.04 | 24.6% | -16.4% |

### channel (overall mean = 59.7182, gap x1.3264)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| referral | 4801 | 70.4557 | 338257.66 | 33.3% | +18.0% |
| in_app | 5100 | 58.4163 | 297923.2 | 29.3% | -2.2% |
| partner | 2535 | 53.1175 | 134652.93 | 13.3% | -11.1% |
| paid_social | 2517 | 53.2721 | 134085.83 | 13.2% | -10.8% |
| assisted | 2047 | 53.8786 | 110289.47 | 10.9% | -9.8% |


## Findings

- **[WARN]** Константная колонка contribution_margin — не несёт информации
- **[WARN]** Выбросов в cac_eur: 6% — проверить, сигнал или ошибка
- **[WARN]** months_retained ~ ltv_eur: r=0.909 — мультиколлинеарность или дубль признака
- **[INFO]** Разрыв по segment: x1.9885 между сегментами — кандидат в главный вывод

## What We Did Not Cover

- Причинность: корреляции не доказывают влияние.
- Внешние источники и бизнес-контекст, которых нет в датасете.
- Формальные тесты гипотез (это CDA / A-B testing).

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py --input <dataset> \
    [--metric <col>] [--segments <a,b>] [--time-col <col>] [--top <n>]
```
