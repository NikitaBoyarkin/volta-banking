# План дальнейшего улучшения volta-banking

**Дата:** 2026-08-19
**Статус:** предложен, не утверждён
**Контекст:** базовый слой готов — 4 скрипта с методологией (Wilson CI, CUPED %,
bootstrap CI, per-cluster silhouette + PNG), 33 теста, ruff чист, CI зелёный,
README полный. Дальше — три трека: углубление аналитики, инженерное качество,
расширение портфолио.

---

## Трек A: Углубление аналитики в существующих 4 скриптах (P0)

### A/B testing (`volta_ab_testing.py`)

| # | Задача | Зачем | Критерий успеха |
|---|--------|-------|-----------------|
| A1 | **Guardrail-метрики** | Сейчас только `kyc_completed`; нет проверки, что тест не сломал churn/revenue | `section_guardrails()`: t-тест на churn + revenue, вывод «guardrail OK / нарушен» |
| A2 | **HTE / статистика по сегментам** | `section_segments` есть, но без значимости | Chi-square или logistic-взаимодействие на каждом сегменте (device/channel/age) с BH-коррекцией |
| A3 | **Sequential testing / alpha spending** | Peeking искажает p-value при мониторинге | O'Brien-Fleming границы или alpha-spending функция; вывод «можно ли смотреть сейчас» |
| A4 | **Power curve PNG** | Визуализировать мощность при разных MDE | `power_curve.png`: power vs MDE, отметка планируемого MDE |

### Funnel (`volta_funnel_analysis.py`)

| # | Задача | Зачем | Критерий успеха |
|---|--------|-------|-----------------|
| F1 | **Статтесты на каждом шаге между сегментами** | Сейчас chi-square только на активации | Chi-square per step (channel/device/age) с Holm-коррекцией |
| F2 | **Time-to-convert** | Нет скорости прохождения воронки | Медиана/распределение времени install→first_tx по каналам |
| F3 | **Funnel heatmap PNG** | Визуальный слой для README/презентации | `funnel_heatmap.png`: шаг × сегмент, % конверсии |

### Retention (`volta_retention_analysis.py`)

| # | Задача | Зачем | Критерий успеха |
|---|--------|-------|-----------------|
| R1 | **Cohort heatmap PNG** | Стандарт для cohort-аналитики | `cohort_heatmap.png`: когорта × месяц, цвет = retention |
| R2 | **Churn rate curve** | Churn = 1 − retention, читается иначе | `section_churn_curve()`: churn по месяцам pre/post |
| R3 | **LTV bootstrap CI** | LTV сейчас точечный | Bootstrap CI на 12-мес LTV (free/premium, pre/post) |

### Segmentation (`volta_segmentation.py`)

| # | Задача | Зачем | Критерий успеха |
|---|--------|-------|-----------------|
| S1 | **Silhouette plot PNG** | Per-cluster mean есть, per-sample нет | `segmentation_silhouette.png`: классический silhouette plot |
| S2 | **Centroid profiles** | Какие фичи отличают сегмент от среднего | Таблица: сегмент × z-score по каждой фиче |
| S3 | **Segment stability** | Один прогон KMeans может быть случайным | Bootstrap-кластеризация: % совпадений сегментов при ресемплинге |

---

## Трек B: Инженерное качество (P1)

| # | Задача | Зачем | Критерий успеха |
|---|--------|-------|-----------------|
| B1 | **mypy type checking** | Скрипты растут, `# type: ignore` накапливаются | `uv run mypy .` зелёный; убрать лишние ignores |
| B2 | **pytest-cov ≥ 80%** | Сейчас 33 теста, покрытие не измеряется | `uv run pytest --cov` ≥ 80% по модулям |
| B3 | **Pre-commit hooks** | ruff + pytest до каждого коммита | `.pre-commit-config.yaml`: ruff check, ruff format, pytest |
| B4 | **Makefile / task runner** | Единые команды вместо длинных `uv run` | `make test`, `make lint`, `make data`, `make all` |
| B5 | **Data pipeline** | Генераторы разбросаны, CSV коммитятся вручную | `make data` пересобирает все 4 датасета; версия данных в README |
| B6 | **Executed notebooks** | Презентационный формат для интервью | 4 `.ipynb` (по проекту), выполненные, с выводами |

---

## Трек C: Расширение портфолио (P1–P2)

Уже скоуплено в `.planning/ROADMAP.md` (5 фаз, 30 требований). Порядок — по
ценности для портфолио:

| # | Фаза | Ценность | Статус |
|---|------|----------|--------|
| C1 | **Churn prediction** | ML-навык, связка с сегментацией | Контекст готов: `.planning/phases/01-churn-prediction/` |
| C2 | **RFM analysis** | Классика продуктовой аналитики | Требования готовы (RFM-01..06) |
| C3 | **CLV modeling** | Дополняет LTV из Project 3 | Требования готовы (CLV-01..06) |
| C4 | **Marketing attribution** | Атрибуция каналов, связка с funnel | Требования готовы (ATTR-01..06) |
| C5 | **Anomaly detection** | Статистика + ML, детект фрода | Требования готовы (ANOM-01..06) |

Каждая фаза — по паттерну текущих скриптов: `volta_<topic>.py`, генератор данных,
секции с `===`, PNG-визуализации, тесты, CI.

---

## Трек D: Презентация (P2)

| # | Задача | Зачем | Критерий успеха |
|---|--------|-------|-----------------|
| D1 | **Streamlit dashboard** | 4 проекта в одном интерактивном дашборде | `app.py`: воронка, A/B, retention, сегменты; `uv run streamlit run app.py` |
| D2 | **Executive summary deck** | Для интервью/портфолио | Marp/HTML-дека: 4 проекта, ключевые цифры, выводы |
| D3 | **Case study writeup** | LinkedIn/резюме | Текст: проблема → метод → результат → рекомендации |
| D4 | **Charts в README** | README сейчас текстовый | Встроить PNG (funnel, cohort heatmap, PCA scatter) |

---

## Приоритеты и последовательность

1. **Спринт 1 (P0):** A1–A4, F1–F3, R1–R3, S1–S3 — углубление 4 скриптов.
   Каждая задача = функция + тест + PNG (где уместно). ~2–3 сессии.
2. **Спринт 2 (P1):** B1–B6 — инженерный слой. mypy и coverage сначала
   (поймают регрессии от Спринта 1).
3. **Спринт 3 (P1–P2):** C1 (churn) — первая фаза расширения, затем C2–C5
   по мере интереса.
4. **Спринт 4 (P2):** D1–D4 — презентация, когда аналитика устаканится.

**Правило:** каждая задача в Спринте 1–2 = тест + ruff чист + скрипт запускается.
CI уже ловит регрессии автоматически.

---

## Открытые вопросы

- Нужен ли Streamlit (D1) или достаточно executed notebooks (B6)? — дублируют друг друга.
- Churn prediction (C1) — приоритетнее углубления (A) или после?
- Публиковать ли проект публично (GitHub Pages для дашборда)?
