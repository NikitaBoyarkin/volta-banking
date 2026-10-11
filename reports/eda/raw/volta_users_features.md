# EDA Report

**Rows:** 50000 · **Columns:** 8 · **Memory:** 3.05 MB

## Profile

| Column | dtype |
|---|---|
| user_id | int64 |
| monthly_tx_count | float64 |
| avg_tx_value_eur | float64 |
| savings_balance_eur | float64 |
| logins_per_week | float64 |
| p2p_transfers_month | float64 |
| tenure_days | float64 |
| monthly_revenue | float64 |

## Data Quality

- Duplicated rows: **0**
- Constant columns: **0**
- Пропусков нет.

## Numeric Distributions

| Column | n | mean | median | std | p25 | p75 | p95 | outliers | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| user_id | 50000 | 24999.5 | 24999.5 | 14433.9011 | 12499.75 | 37499.25 | 47499.05 | 0.0% | 0.0 |
| monthly_tx_count | 50000 | 13.9998 | 11.6468 | 11.4108 | 5.2045 | 19.7275 | 38.8916 | 2.4% | 0.9501 |
| avg_tx_value_eur | 50000 | 19.6004 | 16.7883 | 13.266 | 9.5506 | 27.6033 | 46.3202 | 0.7% | 0.728 |
| savings_balance_eur | 50000 | 1421.772 | 550.2189 | 1792.6532 | 15.1207 | 2348.868 | 5602.8334 | 2.9% | 1.3455 |
| logins_per_week | 50000 | 4.8399 | 4.2493 | 3.3169 | 2.1823 | 6.9528 | 11.3477 | 0.3% | 0.6672 |
| p2p_transfers_month | 50000 | 4.9809 | 3.6625 | 4.5565 | 1.2521 | 7.8083 | 14.4279 | 0.4% | 0.9087 |
| tenure_days | 50000 | 266.0102 | 266.435 | 89.4526 | 195.1408 | 323.0961 | 428.6565 | 0.1% | 0.2486 |
| monthly_revenue | 50000 | 9.4664 | 6.4193 | 9.6223 | 2.6364 | 12.7367 | 32.5581 | 10.9% | 1.4269 |

## Categorical Slices

_Категориальных колонок нет._

## Correlations

| Pair | r | Note |
|---|---:|---|
| savings_balance_eur ~ monthly_revenue | 0.9213 | multicollinearity |
| monthly_tx_count ~ monthly_revenue | 0.8898 | multicollinearity |
| monthly_tx_count ~ savings_balance_eur | 0.889 | multicollinearity |
| savings_balance_eur ~ p2p_transfers_month | 0.8812 | multicollinearity |
| p2p_transfers_month ~ monthly_revenue | 0.8625 | multicollinearity |
| monthly_tx_count ~ p2p_transfers_month | 0.8578 | multicollinearity |
| avg_tx_value_eur ~ savings_balance_eur | 0.8521 | multicollinearity |
| user_id ~ monthly_tx_count | -0.85 | multicollinearity |
| monthly_tx_count ~ logins_per_week | 0.8487 | multicollinearity |
| monthly_tx_count ~ avg_tx_value_eur | 0.844 | multicollinearity |
| user_id ~ logins_per_week | -0.8413 | multicollinearity |
| savings_balance_eur ~ logins_per_week | 0.8409 | multicollinearity |

## Findings

- **[WARN]** Выбросов в monthly_revenue: 11% — проверить, сигнал или ошибка
- **[WARN]** savings_balance_eur ~ monthly_revenue: r=0.9213 — мультиколлинеарность или дубль признака
- **[WARN]** monthly_tx_count ~ monthly_revenue: r=0.8898 — мультиколлинеарность или дубль признака
- **[WARN]** monthly_tx_count ~ savings_balance_eur: r=0.889 — мультиколлинеарность или дубль признака
- **[WARN]** savings_balance_eur ~ p2p_transfers_month: r=0.8812 — мультиколлинеарность или дубль признака
- **[WARN]** p2p_transfers_month ~ monthly_revenue: r=0.8625 — мультиколлинеарность или дубль признака
- **[WARN]** monthly_tx_count ~ p2p_transfers_month: r=0.8578 — мультиколлинеарность или дубль признака
- **[WARN]** avg_tx_value_eur ~ savings_balance_eur: r=0.8521 — мультиколлинеарность или дубль признака
- **[WARN]** user_id ~ monthly_tx_count: r=-0.85 — мультиколлинеарность или дубль признака
- **[WARN]** monthly_tx_count ~ logins_per_week: r=0.8487 — мультиколлинеарность или дубль признака
- **[WARN]** monthly_tx_count ~ avg_tx_value_eur: r=0.844 — мультиколлинеарность или дубль признака
- **[WARN]** user_id ~ logins_per_week: r=-0.8413 — мультиколлинеарность или дубль признака
- **[WARN]** savings_balance_eur ~ logins_per_week: r=0.8409 — мультиколлинеарность или дубль признака

## What We Did Not Cover

- Причинность: корреляции не доказывают влияние.
- Внешние источники и бизнес-контекст, которых нет в датасете.
- Формальные тесты гипотез (это CDA / A-B testing).

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py --input <dataset> \
    [--metric <col>] [--segments <a,b>] [--time-col <col>] [--top <n>]
```
