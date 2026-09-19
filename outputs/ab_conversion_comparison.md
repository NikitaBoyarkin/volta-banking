# KYC Progress Bar A/B Test — Conversion Comparison

![KYC Progress Bar A/B Test — Conversion Comparison](ab_conversion_comparison.png)

*Конверсия KYC start → complete по веткам эксперимента с 95%-ми доверительными интервалами.*

## Выводы

- Treatment: 61.54% против Control: 55.82% (лифт +5.72%).
- 95%-й ДИ лифта: [+3.78%, +7.66%].
- Результат статистически значим (Z=5.82, p=0.0000).
- Гейт выката пройден: p<0.05, лифт ≥ +5 п.п. MDE, SRM нет → раскатка на 100%.

---
<sub>Источник: `scripts/volta_ab_testing.py` · данные: `data/volta_ab_experiment.csv`</sub>
