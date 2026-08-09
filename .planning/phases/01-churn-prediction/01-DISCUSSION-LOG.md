# Phase 1: Churn Prediction - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-02
**Phase:** 1-Churn Prediction
**Areas discussed:** Best model selection criteria

---

## Best Model Selection Criteria

| Option | Description | Selected |
|--------|-------------|----------|
| Highest ROC-AUC | Aligns with success criterion #3. Straightforward for portfolio narrative. | |
| Highest F1-score | Balances precision and recall, which matters for churn where false negatives and false positives both have cost. More business-meaningful. | ✓ |
| Composite: ROC-AUC primary, F1 tiebreaker | Uses ROC-AUC to meet the success criterion, but mentions F1 in the printed summary. | |

**User's choice:** Highest F1-score — balances precision and recall for business impact
**Notes:** Follow-up confirmed the user wants full classification reports printed for both models to justify the F1-based selection. ROC-AUC is still reported for both models to satisfy success criteria #3.

---

## Claude's Discretion

The user deferred the following areas to planner/researcher defaults:
- Model pair selection (Logistic Regression + Random Forest per requirements example)
- Feature engineering depth (~10-12 raw features across demographics, engagement, financial behavior)
- Class imbalance handling (stratified split + class_weight='balanced' as starting point)

## Deferred Ideas

None — discussion stayed within phase scope.
