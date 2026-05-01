# Research Summary: Volta Banking Analytics Extension

**Date:** 2026-05-02
**Scope:** Five new analytical scripts extending the existing four-script portfolio.

---

## Churn Prediction

**Standard approach:** Train/test split with stratification, compare 2-3 models (Logistic Regression, Random Forest, XGBoost), report ROC-AUC, precision, recall, F1, and feature importance. Use `class_weight='balanced'` or SMOTE for imbalance. Threshold tuning with `predict_proba()`.

**Portfolio simplification:** Skip SMOTE pipeline, use simple `train_test_split` with `stratify=y`, compare 2 models (Random Forest vs Logistic Regression), show confusion matrix, ROC curve, and top-5 feature importances. Match existing script complexity.

## RFM Analysis

**Standard approach:** `groupby.agg()` to compute Recency/Frequency/Monetary per customer, quintile scoring with `rank(method='first')` before `pd.qcut`, rule-based segments (Champions, At-Risk, Hibernating, New, Regulars), cohort sanity check.

**Portfolio simplification:** Standard pandas `groupby` RFM calculation, 4-quantile scoring, 5 segments with clear business rules, bar chart of segment sizes, and a heatmap of average R/F/M per segment.

## CLV Modeling

**Standard approach:** Three methods: (1) Historical CLV = total revenue per customer, (2) Predictive CLV = BG/NBD expected transactions × Gamma-Gamma expected value, (3) Probabilistic CLV using `lifetimes` package. Requires holdout validation.

**Portfolio simplification:** Implement all three methods inline (no external CLV library): Historical (sum), Predictive (simple linear projection from observed frequency × AOV), and Probabilistic (simplified BG/NBD approximation). Compare distributions across methods with histograms.

## Marketing Attribution

**Standard approach:** Four models: Last Touch, First Touch, Linear, and Shapley value. Compare attribution weights across channels. Use synthetic journey data with touchpoints.

**Portfolio simplification:** Generate synthetic multi-touch journey data, implement Last Touch, First Touch, Linear, and Data-Driven (simplified Markov chain) attribution. Show bar chart comparison and conversion rate by channel.

## Anomaly Detection

**Standard approach:** Start with Z-score and IQR baselines, then Isolation Forest for multivariate patterns. Consensus scoring when both methods flag the same transaction. Visualize time series with anomalies highlighted.

**Portfolio simplification:** Generate synthetic daily transaction volume data, inject known anomalies. Apply Z-score, IQR, and Isolation Forest. Show time series plot with anomalies flagged, and a comparison table of detection rates.

---

## Key Constraints for Portfolio Scripts

1. **Single-file, ~200-400 lines** — no shared modules, no external CLV/attribution libraries
2. **Synthetic data inline** — each script generates and saves its own CSV
3. **Dark-themed matplotlib** — consistent with existing `plt.style.use('dark_background')`
4. **Print-based progress** — no logging framework
5. **scikit-learn only** — no XGBoost/LightGBM (adds dependency complexity), use `RandomForestClassifier` from sklearn

---

*Research sources:*
- Churn: [365 Data Science](https://365datascience.com/tutorials/python-tutorials/how-to-build-a-customer-churn-prediction-model-in-python), [The Python Code](https://www.thepythoncode.com/article/customer-churn-detection-using-sklearn-in-python)
- RFM: [Towards Data Science](https://towardsdatascience.com/eda-in-public-part-3-rfm-analysis-for-customer-segmentation-in-pandas/), [Practical Data Science](https://practicaldatascience.co.uk/data-science/how-to-segment-customers-based-on-their-value-using-rfm-and-abc)
- CLV: [PyMC-Marketing](https://www.pymc-marketing.io/en/0.11.0/notebooks/clv/clv_quickstart.html), [Practical Data Science](https://practicaldatascience.co.uk/data-science/how-to-calculate-clv-using-bgnbd-and-gamma-gamma)
- Attribution: [DigiGrowth](https://diggrowth.com/blogs/marketing-attribution/attribution-analysis-python/), [shapley-attribution](https://github.com/ianchute/shapley-attribution)
- Anomaly: [DataField.Dev](https://datafield.dev/intermediate-data-science/part-04/chapter-22/index.html), [DataCamp Isolation Forest](https://www.datacamp.com/tutorial/isolation-forest)
