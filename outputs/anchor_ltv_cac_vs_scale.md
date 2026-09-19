# Anchor Launch — Blended LTV/CAC vs Scale

![Anchor Launch — Blended LTV/CAC vs Scale](anchor_ltv_cac_vs_scale.png)

*Blended LTV/CAC по мере масштабирования запуска; гейт ≥3 ломается на дешёвых каналах.*

## Выводы

- Гейт LTV/CAC ≥ 3 держится только до ≈ 70K юзеров — пока не исчерпаны referral и дешёвый in_app.
- На SOM (225K) blended LTV/CAC падает до 1,76 — launch-P&L ломается.
- Причина — маржинальный CAC: последний юзер SOM приходит из partner/paid по €100–368.
- Рычаг — не бюджет, а ёмкость дешёвых каналов (реферал, in-app) и их конверсия.

---
<sub>Источник: `scripts/volta_anchor_cac.py` · данные: `data/volta_anchor_cac.csv`</sub>
