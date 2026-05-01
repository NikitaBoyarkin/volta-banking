# 🏦 Volta Neobank — Onboarding Funnel Analysis

> **Portfolio Project 1/4** | Product Analytics | Fintech

---

## 📌 Business Problem

Volta's growth team flagged that **CAC increased 34% YoY** while activation remained flat.
Only **~13% of users who install the app** complete their first transaction within 7 days.

This analysis identifies exactly **where users drop off** in the onboarding funnel
and which **segments present the highest opportunity** for improvement.

---

## 🔍 Analytical Questions

1. What is the conversion rate at each step of the onboarding funnel?
2. Which step has the highest absolute and relative drop-off?
3. Do acquisition channels differ significantly in activation quality?
4. Are there demographic or device-based segments with worse conversion?
5. What is the estimated revenue impact of the main drop-off points?

---

## 📊 Key Findings

| Finding | Metric | Impact |
|---------|--------|--------|
| KYC completion is critical bottleneck | 56.6% step conversion | ~€181K lost per 10K installs |
| Registration loses 27% of users | 73.2% step conversion | Largest absolute drop (2,682 users) |
| Referral converts 5–8pp better than paid social | Statistical significance p<0.05 | Lower CAC, higher LTV |
| 45+ users drop at KYC disproportionately | Document upload friction | Untapped older demographic |
| iOS outperforms Android at every step | ~2–3pp per step | Compounding effect on activation |

---

## 🛠️ Tech Stack

```
Python 3.10    pandas · numpy · matplotlib · seaborn · scipy
```

---

## 📁 Project Structure

```
01_funnel_analysis/
├── volta_funnel_analysis.ipynb   ← Main analysis notebook
├── volta_funnel_data.csv         ← Synthetic dataset (10,000 users)
├── funnel_metrics.csv            ← Aggregated funnel table
├── viz1_main_funnel.png          ← Main funnel + step conversion chart
├── viz2_channel_breakdown.png    ← Channel activation & KYC heatmap
├── viz3_segments.png             ← Age × channel heatmap + device comparison
└── README.md
```

---

## 📐 Methodology

- **Funnel analysis** — step-by-step conversion with absolute and relative drop-off
- **Segmentation** — acquisition channel, device (iOS/Android), age group
- **Statistical testing** — Chi-square test for channel significance
- **Revenue impact** — estimated LTV × drop-off user count

---

## 💡 Recommendations

1. **Redesign KYC UX** — add progress bar, real-time photo guidance, better error messages
2. **Simplify Registration** — A/B test removing phone number field
3. **Double down on Referral** — launch referral bonus program, reallocate 15% paid social budget
4. **Android-specific sprint** — QA audit of Android funnel to close the iOS gap
5. **First Transaction nudge** — push notification + cashback incentive on card activation

---

## 🔗 Next Projects

| Project | Description |
|---------|-------------|
| [02 — A/B Testing](../02_ab_testing/) | Test KYC progress bar redesign |
| [03 — Retention & Cohort](../03_retention_cohort/) | Which cohorts retain best? |
| [04 — User Segmentation](../04_user_segmentation/) | Monetization strategy by segment |
****