# EDA Report

**Rows:** 4 · **Columns:** 10 · **Memory:** 0.0 MB

## Profile

| Column | dtype |
|---|---|
| segment | str |
| n_users | int64 |
| avg_rev | float64 |
| revenue_share | float64 |
| pct_premium | float64 |
| avg_tx | float64 |
| avg_savings | float64 |
| avg_logins | float64 |
| avg_tenure | float64 |
| total_monthly_rev | float64 |

## Data Quality

- Duplicated rows: **0**
- Constant columns: **0**
- Пропусков нет.

## Numeric Distributions

| Column | n | mean | median | std | p25 | p75 | p95 | outliers | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| n_users | 4 | 12500.0 | 14000.0 | 4725.8156 | 10500.0 | 16000.0 | 16000.0 | 0.0% | -1.1938 |
| avg_rev | 4 | 13.2 | 9.27 | 13.2737 | 4.7475 | 17.7225 | 29.1045 | 0.0% | 1.3838 |
| revenue_share | 4 | 25.0 | 25.85 | 14.571 | 16.05 | 34.8 | 39.36 | 0.0% | -0.2392 |
| pct_premium | 4 | 0.2926 | 0.1878 | 0.3444 | 0.0618 | 0.4186 | 0.7048 | 0.0% | 1.3452 |
| avg_tx | 4 | 18.1 | 15.45 | 14.8641 | 9.125 | 24.425 | 35.285 | 0.0% | 0.8965 |
| avg_savings | 4 | 2119.75 | 1373.5 | 2463.0833 | 318.5 | 3174.75 | 5034.15 | 0.0% | 1.1744 |
| avg_logins | 4 | 5.925 | 5.5 | 4.0194 | 3.425 | 8.0 | 10.4 | 0.0% | 0.5072 |
| avg_tenure | 4 | 289.75 | 284.5 | 104.1805 | 237.5 | 336.75 | 403.35 | 0.0% | 0.279 |
| total_monthly_rev | 4 | 118330.0 | 122365.5 | 68990.8763 | 75959.75 | 164735.75 | 186313.55 | 0.0% | -0.2398 |

## Categorical Slices

**segment** — кардинальность 4

| Value | Count | Share |
|---|---:|---:|
| Power Users | 1 | 25.0% |
| Growth Users | 1 | 25.0% |
| Casual Users | 1 | 25.0% |
| Dormant Users | 1 | 25.0% |

## Correlations

| Pair | r | Note |
|---|---:|---|
| revenue_share ~ total_monthly_rev | 1.0 | multicollinearity |
| n_users ~ avg_savings | -0.9998 | multicollinearity |
| avg_rev ~ pct_premium | 0.9992 | multicollinearity |
| pct_premium ~ avg_savings | 0.9968 | multicollinearity |
| n_users ~ pct_premium | -0.996 | multicollinearity |
| avg_tx ~ avg_logins | 0.9947 | multicollinearity |
| avg_rev ~ avg_savings | 0.9929 | multicollinearity |
| n_users ~ avg_rev | -0.9917 | multicollinearity |
| avg_rev ~ avg_tx | 0.99 | multicollinearity |
| pct_premium ~ avg_tx | 0.988 | multicollinearity |
| avg_tx ~ avg_savings | 0.9822 | multicollinearity |
| n_users ~ avg_tx | -0.9785 | multicollinearity |

## Metric by Segment

### segment (overall mean = 13.2, gap x13.8312)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| Power Users | 1 | 31.95 | 31.95 | 60.5% | +142.1% |
| Growth Users | 1 | 12.98 | 12.98 | 24.6% | -1.7% |
| Casual Users | 1 | 5.56 | 5.56 | 10.5% | -57.9% |
| Dormant Users | 1 | 2.31 | 2.31 | 4.4% | -82.5% |


## Findings

- **[WARN]** revenue_share ~ total_monthly_rev: r=1.0 — мультиколлинеарность или дубль признака
- **[WARN]** n_users ~ avg_savings: r=-0.9998 — мультиколлинеарность или дубль признака
- **[WARN]** avg_rev ~ pct_premium: r=0.9992 — мультиколлинеарность или дубль признака
- **[WARN]** pct_premium ~ avg_savings: r=0.9968 — мультиколлинеарность или дубль признака
- **[WARN]** n_users ~ pct_premium: r=-0.996 — мультиколлинеарность или дубль признака
- **[WARN]** avg_tx ~ avg_logins: r=0.9947 — мультиколлинеарность или дубль признака
- **[WARN]** avg_rev ~ avg_savings: r=0.9929 — мультиколлинеарность или дубль признака
- **[WARN]** n_users ~ avg_rev: r=-0.9917 — мультиколлинеарность или дубль признака
- **[WARN]** avg_rev ~ avg_tx: r=0.99 — мультиколлинеарность или дубль признака
- **[WARN]** pct_premium ~ avg_tx: r=0.988 — мультиколлинеарность или дубль признака
- **[WARN]** avg_tx ~ avg_savings: r=0.9822 — мультиколлинеарность или дубль признака
- **[WARN]** n_users ~ avg_tx: r=-0.9785 — мультиколлинеарность или дубль признака
- **[INFO]** Разрыв по segment: x13.8312 между сегментами — кандидат в главный вывод

## What We Did Not Cover

- Причинность: корреляции не доказывают влияние.
- Внешние источники и бизнес-контекст, которых нет в датасете.
- Формальные тесты гипотез (это CDA / A-B testing).

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py --input <dataset> \
    [--metric <col>] [--segments <a,b>] [--time-col <col>] [--top <n>]
```
