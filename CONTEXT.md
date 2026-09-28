# Volta

Флагманский кейс системы портфолио — вымышленный необанк Volta. Контекст описывает язык структуры кейса: как устроена карта подпроектов, что такое слой и какие графики выходят на хаб. Системные термины — в корневом `../CONTEXT.md`.

## Структура кейса

**Project map (Volta)**:
Секция `## Карта проекта` / `## Project map` на хабе Volta — **23** подпроекта, сгруппированные по слоям `core | extended | market-jobs | rat-v2 | causal`. Генерируется из коллекции `volta-parts` скриптом `bun run volta:map` (`scripts/gen-volta-map.mjs`), не пишется руками. На part-страницах слой виден как метка и в навигации (prev/next по `order`).
_Avoid_: досье (это part-страница, не карта), оглавление

**Volta layer**:
Поле `layer` в `voltaPartSchema` — машинночитаемый слой подпроекта: `core` (петля 1–4), `extended` (5–12), `market-jobs` (13–17), `rat-v2` (18–22), `causal` (23, `causal-kyc`). Заменяет prose-таксономию из хаба.
_Avoid_: категория, track (это поле проектов, не частей)

**Curated hub charts**:
Хаб Volta показывает 6 отобранных графиков (`onboarding-funnel`, `kyc-ab-conversion`, `cohort-retention-heatmap`, `retention-pre-post`, `segmentation-size-vs-revenue`, `segmentation-pareto-cumulative`); остальные графики живут на своих part-страницах. Введено PRD v8 (`docs/prd-volta-structure.md`), baseline был 34.
_Avoid_: все графики на хабе
