# EDA Report

**Rows:** 10000 · **Columns:** 12 · **Memory:** 3.69 MB

## Profile

| Column | dtype |
|---|---|
| user_id | str |
| channel | str |
| device | str |
| age_group | str |
| app_install | int64 |
| registration | int64 |
| kyc_start | int64 |
| kyc_complete | int64 |
| card_ordered | int64 |
| first_tx | int64 |
| install_date | str |
| first_tx_date | str |

## Data Quality

- Duplicated rows: **0**
- Constant columns: **1** (app_install)

| Column | Nulls | Share |
|---|---:|---:|
| first_tx_date | 8731 | 87.3% |

**Datetime columns (excluded from categorical):** `install_date`, `first_tx_date`

## Numeric Distributions

| Column | n | mean | median | std | p25 | p75 | p95 | outliers | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| app_install | 10000 | 1.0 | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 | 0.0% | 0.0 |
| registration | 10000 | 0.7318 | 1.0 | 0.443 | 0.0 | 1.0 | 1.0 | 0.0% | -1.0466 |
| kyc_start | 10000 | 0.4917 | 0.0 | 0.5 | 0.0 | 1.0 | 1.0 | 0.0% | 0.0332 |
| kyc_complete | 10000 | 0.2781 | 0.0 | 0.4481 | 0.0 | 1.0 | 1.0 | 0.0% | 0.9906 |
| card_ordered | 10000 | 0.1993 | 0.0 | 0.3995 | 0.0 | 0.0 | 1.0 | 0.0% | 1.5057 |
| first_tx | 10000 | 0.1269 | 0.0 | 0.3329 | 0.0 | 0.0 | 1.0 | 0.0% | 2.2421 |

## Categorical Slices

**user_id** — кардинальность 10000

| Value | Count | Share |
|---|---:|---:|
| U000000 | 1 | 0.0% |
| U000001 | 1 | 0.0% |
| U000002 | 1 | 0.0% |
| U000003 | 1 | 0.0% |
| U000004 | 1 | 0.0% |
| U000005 | 1 | 0.0% |
| U000006 | 1 | 0.0% |
| U000007 | 1 | 0.0% |
| U000008 | 1 | 0.0% |
| U000009 | 1 | 0.0% |

**channel** — кардинальность 5

| Value | Count | Share |
|---|---:|---:|
| organic_search | 3053 | 30.5% |
| paid_social | 2553 | 25.5% |
| referral | 1981 | 19.8% |
| email | 1452 | 14.5% |
| app_store | 961 | 9.6% |

**age_group** — кардинальность 4

| Value | Count | Share |
|---|---:|---:|
| 25-34 | 4032 | 40.3% |
| 35-44 | 2582 | 25.8% |
| 18-24 | 1941 | 19.4% |
| 45+ | 1445 | 14.4% |

**device** — кардинальность 2

| Value | Count | Share |
|---|---:|---:|
| ios | 5460 | 54.6% |
| android | 4540 | 45.4% |

## Correlations

| Pair | r | Note |
|---|---:|---|
| kyc_complete ~ card_ordered | 0.8038 | multicollinearity |
| card_ordered ~ first_tx | 0.7642 | moderate |
| kyc_start ~ kyc_complete | 0.6311 | moderate |
| kyc_complete ~ first_tx | 0.6142 | moderate |
| registration ~ kyc_start | 0.5954 | moderate |
| kyc_start ~ card_ordered | 0.5073 | moderate |
## Trend & Anomalies

**Aggregation:** weekly `row_count` · flow vs behavior: `count` vs `per_unit`

| Period | Value | Count | Per unit | Δ value | Δ count | Δ per unit |
|---|---:|---:|---:|---:|---:|---:|
| 2024-07-07 | 2545.0 | 2545 | 1.0 | +0.0% | +0.0% | +0.0% |
| 2024-07-14 | 2470.0 | 2470 | 1.0 | -2.9% | -2.9% | +0.0% |
| 2024-07-21 | 2543.0 | 2543 | 1.0 | +3.0% | +3.0% | +0.0% |
| 2024-07-28 | 2442.0 | 2442 | 1.0 | -4.0% | -4.0% | +0.0% |

## Findings

- **[WARN]** Пропуски в first_tx_date: 87% — риск смещения выборки
- **[WARN]** Константная колонка app_install — не несёт информации
- **[INFO]** first_tx: правосторонний скос (2.2421) — медиана надёжнее среднего
- **[WARN]** user_id: кардинальность 10000 (100% строк) — похоже на ID, не группировать
- **[WARN]** kyc_complete ~ card_ordered: r=0.8038 — мультиколлинеарность или дубль признака

## What We Did Not Cover

- Причинность: корреляции не доказывают влияние.
- Внешние источники и бизнес-контекст, которых нет в датасете.
- Формальные тесты гипотез (это CDA / A-B testing).

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py --input <dataset> \
    [--metric <col>] [--segments <a,b>] [--time-col <col>] [--top <n>]
```
