# Phase 1: Churn Prediction - Context

**Gathered:** 2026-05-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Build and evaluate churn prediction models on synthetic fintech user data, demonstrating end-to-end ML workflow from data generation to model comparison. The deliverable is a single self-contained Python script `volta_churn_prediction.py` that generates synthetic data, trains two models, compares them, and produces visualizations.

</domain>

<decisions>
## Implementation Decisions

### Best Model Selection Criteria
- **D-01:** The "best" model (selected for confusion matrix and ROC curve plot) is determined by **highest F1-score**, not ROC-AUC. F1 balances precision and recall, which is more business-meaningful for churn where both false negatives (missing churners) and false positives (wasting retention budget) have real cost.
- **D-02:** A **full classification report** (precision, recall, F1-score) is printed for both models to justify the F1-based selection and show the trade-off landscape.

### Claude's Discretion
- **Model pair selection:** Requirements suggest Logistic Regression + Random Forest. Use this pair unless research surfaces a compelling reason to swap (e.g., GradientBoostingClassifier for stronger ensemble performance). Must stay within scikit-learn per Out of Scope.
- **Feature engineering depth:** Match existing script complexity. Generate ~10-12 raw features across demographics (age, tenure), engagement (login frequency, transaction count), and financial behavior (balance, monthly revenue). Keep features interpretable for business storytelling.
- **Class imbalance handling:** ~20% churn rate is moderately imbalanced. Start with stratified train/test split + `class_weight='balanced'` on applicable models. If metrics look poor, research SMOTE as fallback.
- **Visualization layout:** Follow existing script pattern — `plt.style.use('dark_background')`, section headers with `===`, 3-5 figures total (feature importance, confusion matrix, ROC curve, possibly a metrics comparison bar chart).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & Requirements
- `.planning/ROADMAP.md` — Phase boundary, success criteria, and execution notes
- `.planning/REQUIREMENTS.md` — Detailed requirements CHURN-01..CHURN-06
- `.planning/PROJECT.md` — Tech stack, constraints, Out of Scope items, existing decisions
- `CLAUDE.md` — Codebase guidance, run commands, existing script patterns

### Existing Patterns (Code)
- `volta_funnel_analysis.py` — Section structure, print formatting, dark background style
- `volta_ab_testing.py` — Statistical reporting pattern, inline helper functions
- `volta_segmentation.py` — scikit-learn usage pattern (StandardScaler, model training)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- No shared utilities to import — each script is self-contained per PROJECT.md decision
- Existing scripts use `warnings.filterwarnings('ignore')` and `plt.style.use('dark_background')`
- Data generation pattern: inline numpy/pandas random generators, save to CSV via `df.to_csv()`

### Established Patterns
- Docstring opens with business context (industry, type, portfolio position)
- Section headers formatted as `=== SECTION N: Title ===`
- Printed summary tables use `pd.set_option('display.float_format', ...)`
- Each script expects to be run from repo root; CSV paths are relative

### Integration Points
- Output CSV: `data/volta_churn_data.csv` (new file, no conflicts)
- PNG visualizations saved to repo root or `data/` (follow existing pattern)
- Must not import from `utils/` — per PROJECT.md "No shared utilities"

</code_context>

<specifics>
## Specific Ideas

- Success criteria #3 requires ROC-AUC scores to differ by at least 0.02 — ensure models have genuinely different expressive power (e.g., linear vs tree-based)
- Feature importance plot must show top 5 drivers with business interpretation (not just raw feature names)
- Confusion matrix and ROC curve go to the F1-best model, but ROC-AUC is still reported for both to satisfy the success criterion

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Churn Prediction*
*Context gathered: 2026-05-02*
