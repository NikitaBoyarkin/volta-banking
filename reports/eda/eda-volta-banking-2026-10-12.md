# EDA — volta-banking (2026-10-12)

Разведочный анализ 28 датасетов проекта `00 ide/00 portfolio/volta-banking`.
Долговечный синтез — в vault: `Obsidian/Z-core/eda-volta-banking-2026-Q4.md`.
Сырые профили по каждому датасету — `reports/eda-volta/raw/<dataset>.md` (28 файлов).

## Ключевые цифры

| Метрика | Значение | Датасет |
|---|---|---|
| Средняя маржа / транзакция | **−0.15 €** | unit_economics (58 771) |
| Маржа FX / ATM | −0.49 € / −0.80 € | unit_economics |
| Воронка install → first_tx | **12.7%** | funnel_data (10 000) |
| KYC start → complete | 56.6% | funnel_data |
| first_tx: paid_social vs referral | 6.1% vs 17.8% | funnel_data |
| Churn overall | 40.7% | churn_data (15 000) |
| Churn premium vs non | 34.1% vs 42.1% | churn_data |
| Апселл premium_status | 41.2% | premium_upsell (40 001) |
| AB treatment lift (revenue) | +3.5% | ab_experiment (10 000) |

## Флаги качества данных

- Усечённая последняя неделя (`2026-01-04`, −68…−74% во всех рядах) — **артефакт окна**, не инцидент.
- `first_tx_date` 87% пропусков в funnel — ожидаемо (не дошли до шага).
- ID-колонки дают r≈1.0 (`event_id~user_id`, `transaction_id~user_id`) — суррогатные ключи, не коллинеарность.

## Reproducibility

```bash
uv run python .claude/skills/eda/scripts/eda_profile.py \
    --input <dataset.csv> [--metric <col>] [--segments a,b] [--time-col <col>] --out <file.md>
```

Пересчёт воронки: пошаговые конверсии по `volta_funnel_data.csv` (columns: app_install … first_tx).
