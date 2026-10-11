# EDA Report

**Rows:** 12268 · **Columns:** 4 · **Memory:** 0.94 MB

## Profile

| Column | dtype |
|---|---|
| journey_id | int64 |
| touch_order | int64 |
| channel | str |
| revenue | float64 |

## Data Quality

- Duplicated rows: **0**
- Constant columns: **0**
- Пропусков нет.

## Numeric Distributions

| Column | n | mean | median | std | p25 | p75 | p95 | outliers | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| journey_id | 12268 | 3016.1126 | 3023.0 | 1739.5209 | 1509.0 | 4531.25 | 5702.65 | 0.0% | -0.0155 |
| touch_order | 12268 | 0.7572 | 1.0 | 0.8809 | 0.0 | 1.0 | 2.0 | 5.0% | 0.93 |
| revenue | 12268 | 184.8186 | 180.0 | 50.3615 | 150.0 | 220.0 | 250.0 | 0.6% | 0.4104 |

## Categorical Slices

**channel** — кардинальность 5

| Value | Count | Share |
|---|---:|---:|
| referral | 2567 | 20.9% |
| paid_social | 2486 | 20.3% |
| organic | 2443 | 19.9% |
| email | 2405 | 19.6% |
| display | 2367 | 19.3% |

## Correlations

_Пар с |r| >= 0.5 нет._

## Metric by Segment

### channel (overall mean = 184.8186, gap x1.1869)

| Value | Count | Mean | Sum | Share | vs overall |
|---|---:|---:|---:|---:|---:|
| referral | 2567 | 198.5928 | 509787.76 | 22.5% | +7.4% |
| paid_social | 2486 | 193.3863 | 480758.25 | 21.2% | +4.6% |
| organic | 2443 | 183.4648 | 448204.59 | 19.8% | -0.7% |
| email | 2405 | 179.8549 | 432551.09 | 19.1% | -2.7% |
| display | 2367 | 167.3229 | 396053.3 | 17.5% | -9.5% |


## Findings

- Критичных флагов не найдено.

## What We Did Not Cover

- Причинность: корреляции не доказывают влияние.
- Внешние источники и бизнес-контекст, которых нет в датасете.
- Формальные тесты гипотез (это CDA / A-B testing).

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py --input <dataset> \
    [--metric <col>] [--segments <a,b>] [--time-col <col>] [--top <n>]
```
