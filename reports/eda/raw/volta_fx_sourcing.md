# EDA Report

**Rows:** 162 · **Columns:** 9 · **Memory:** 0.03 MB

## Profile

| Column | dtype |
|---|---|
| provider_id | int64 |
| provider_name | str |
| monthly_volume_eur | float64 |
| term_months | int64 |
| quoted_cost_pct | float64 |
| hedging_cost_pct | float64 |
| effective_cost_pct | float64 |
| settlement_days | int64 |
| credit_rating | str |

## Data Quality

- Duplicated rows: **0**
- Constant columns: **0**
- Пропусков нет.

## Numeric Distributions

| Column | n | mean | median | std | p25 | p75 | p95 | outliers | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| provider_id | 162 | 3.5 | 3.5 | 1.7131 | 2.0 | 5.0 | 6.0 | 0.0% | 0.0 |
| monthly_volume_eur | 162 | 104833333.3333 | 25000000.0 | 159253811.2496 | 5000000.0 | 100000000.0 | 500000000.0 | 22.2% | 1.6831 |
| term_months | 162 | 6.3333 | 6.0 | 4.5109 | 1.0 | 12.0 | 12.0 | 0.0% | 0.1118 |
| quoted_cost_pct | 162 | 0.9007 | 0.9124 | 0.2049 | 0.7541 | 1.0562 | 1.222 | 0.0% | -0.135 |
| hedging_cost_pct | 162 | 0.0831 | 0.0796 | 0.0287 | 0.0508 | 0.1169 | 0.1227 | 0.0% | 0.182 |
| effective_cost_pct | 162 | 0.9839 | 0.9989 | 0.2068 | 0.8354 | 1.141 | 1.3034 | 0.0% | -0.134 |
| settlement_days | 162 | 2.0 | 2.0 | 0.819 | 1.0 | 3.0 | 3.0 | 0.0% | 0.0 |

## Categorical Slices

**provider_name** — кардинальность 6

| Value | Count | Share |
|---|---:|---:|
| Interbank Prime | 27 | 16.7% |
| Fintech Liquidity | 27 | 16.7% |
| Global FX Desk | 27 | 16.7% |
| Prime Broker A | 27 | 16.7% |
| Regional Bank | 27 | 16.7% |
| Aggregator X | 27 | 16.7% |

**credit_rating** — кардинальность 4

| Value | Count | Share |
|---|---:|---:|
| AA | 54 | 33.3% |
| A | 54 | 33.3% |
| AAA | 27 | 16.7% |
| BBB | 27 | 16.7% |

## Correlations

| Pair | r | Note |
|---|---:|---|
| quoted_cost_pct ~ effective_cost_pct | 0.9903 | multicollinearity |
| term_months ~ hedging_cost_pct | -0.9878 | multicollinearity |
| provider_id ~ settlement_days | 0.7171 | moderate |
| monthly_volume_eur ~ quoted_cost_pct | -0.6915 | moderate |
| monthly_volume_eur ~ effective_cost_pct | -0.6852 | moderate |

## Metric by Segment

### credit_rating (overall mean = 0.9839, gap x1.3576)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| A | 54 | 1.0071 | 54.38 | 34.1% | +2.4% |
| AA | 54 | 0.9418 | 50.86 | 31.9% | -4.3% |
| BBB | 27 | 1.1548 | 31.18 | 19.6% | +17.4% |
| AAA | 27 | 0.8506 | 22.97 | 14.4% | -13.6% |


## Findings

- **[WARN]** Выбросов в monthly_volume_eur: 22% — проверить, сигнал или ошибка
- **[WARN]** quoted_cost_pct ~ effective_cost_pct: r=0.9903 — мультиколлинеарность или дубль признака
- **[WARN]** term_months ~ hedging_cost_pct: r=-0.9878 — мультиколлинеарность или дубль признака

## What We Did Not Cover

- Причинность: корреляции не доказывают влияние.
- Внешние источники и бизнес-контекст, которых нет в датасете.
- Формальные тесты гипотез (это CDA / A-B testing).

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py --input <dataset> \
    [--metric <col>] [--segments <a,b>] [--time-col <col>] [--top <n>]
```
