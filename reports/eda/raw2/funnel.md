# EDA Report

**Rows:** 10000 · **Columns:** 12 · **Memory:** 1.45 MB

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

## Metric by Segment

### channel (overall mean = 0.1269, gap x2.9165)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| organic_search | 3053 | 0.1464 | 447.0 | 35.2% | +15.4% |
| referral | 1981 | 0.1782 | 353.0 | 27.8% | +40.4% |
| email | 1452 | 0.1612 | 234.0 | 18.4% | +27.0% |
| paid_social | 2553 | 0.0611 | 156.0 | 12.3% | -51.8% |
| app_store | 961 | 0.0822 | 79.0 | 6.2% | -35.2% |

### device (overall mean = 0.1269, gap x1.1631)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| ios | 5460 | 0.1355 | 740.0 | 58.3% | +6.8% |
| android | 4540 | 0.1165 | 529.0 | 41.7% | -8.2% |

### age_group (overall mean = 0.1269, gap x1.0731)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| 25-34 | 4032 | 0.1307 | 527.0 | 41.5% | +3.0% |
| 35-44 | 2582 | 0.1259 | 325.0 | 25.6% | -0.8% |
| 18-24 | 1941 | 0.1242 | 241.0 | 19.0% | -2.2% |
| 45+ | 1445 | 0.1218 | 176.0 | 13.9% | -4.0% |

## Trend & Anomalies

**Aggregation:** weekly `sum(first_tx)` · flow vs behavior: `count` vs `per_unit`

| Period | Value | Count | Per unit | Δ value | Δ count | Δ per unit |
|---|---:|---:|---:|---:|---:|---:|
| 2024-07-07 | 305.0 | 2545 | 0.1198 | +0.0% | +0.0% | +0.0% |
| 2024-07-14 | 316.0 | 2470 | 0.1279 | +3.6% | -2.9% | +6.8% |
| 2024-07-21 | 310.0 | 2543 | 0.1219 | -1.9% | +3.0% | -4.7% |
| 2024-07-28 | 338.0 | 2442 | 0.1384 | +9.0% | -4.0% | +13.5% |

## Findings

- **[WARN]** Пропуски в first_tx_date: 87% — риск смещения выборки
- **[WARN]** Константная колонка app_install — не несёт информации
- **[INFO]** first_tx: правосторонний скос (2.2421) — медиана надёжнее среднего
- **[WARN]** user_id: кардинальность 10000 (100% строк) — похоже на ID, не группировать
- **[WARN]** kyc_complete ~ card_ordered: r=0.8038 — мультиколлинеарность или дубль признака
- **[INFO]** Разрыв по channel: x2.9165 между сегментами — кандидат в главный вывод

## What We Did Not Cover

- Причинность: корреляции не доказывают влияние.
- Внешние источники и бизнес-контекст, которых нет в датасете.
- Формальные тесты гипотез (это CDA / A-B testing).

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py --input <dataset> \
    [--metric <col>] [--segments <a,b>] [--time-col <col>] [--top <n>]
```
