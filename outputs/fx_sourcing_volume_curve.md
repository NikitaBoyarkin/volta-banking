# FX Sourcing Feasibility — Cost vs Monthly Volume

![FX Sourcing Feasibility — Cost vs Monthly Volume](fx_sourcing_volume_curve.png)

*Лучшая достижимая цена FX (интербанк + хедж) по объёму; гейт 0,55% из Project 14.*

## Выводы

- Гейт 0,55% достижим при объёме ≈ €332 млн/мес — это SOM-масштаб (180K путешественников).
- Сегодняшний объём тревел-сегмента (~€3 млн/мес) на два порядка ниже — цена недоступна.
- Кривая лог-линейна: каждый порядок объёма даёт ~0,20 п.п. скидки.
- Риск v2 #2 — не «невозможно», а cold-start: нужен мост до набора объёма.

---
<sub>Источник: `scripts/volta_fx_sourcing.py` · данные: `data/volta_fx_sourcing.csv`</sub>
