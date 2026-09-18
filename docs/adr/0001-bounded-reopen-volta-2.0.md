# Bounded reopen of the Volta portfolio for a conversion-focused "2.0" sprint

- **Status:** accepted
- **Date:** 2026-09-19
- **Supersedes:** the "fixate as-is, no new features" scope decision in `docs/prd.md` v1

`docs/prd.md` v1 froze the portfolio ("fixate as-is, no new features") and out-scoped dashboards, external libraries, and new domains. We reopen a **bounded** 2.0 sprint because the portfolio's job is conversion, and breadth was already saturated at 17 projects / 170 tests / 98% coverage — the marginal script adds no conversion, while the missing signals are a zero-install face and a depth signal. In scope: a causal-inference layer that tests the portfolio's own central claim (`REQ-201`), SHAP explainability on churn (`REQ-202`), a self-contained HTML board (`REQ-203`), and a bounded polish set. Explicitly still out: Streamlit, `src/` refactor, new analytical domains, real data, external CLV/attribution libraries, XGBoost. The single new dependency is `shap`.

## Considered Options

- **Honor fixate (polish only)** — rejected: polish alone creates no depth signal; the portfolio survives a scan but is not memorable.
- **Full reopen (new domains, dashboard, architecture)** — rejected: a weekend cannot absorb it, and it would put a working, fully-tested repo at risk.
- **Bounded reopen (chosen)** — one window, three carve-outs, everything else explicitly excluded.

## Consequences

- v1 remains in the repo unchanged as the historical as-is snapshot; the active document is `docs/prd-v2.md`.
- The "fixate" decision can no longer be cited to reject improvements — it is superseded by this ADR.
- The HTML board replaces the out-scoped interactive dashboard as the recruiter-facing artifact; Streamlit remains out.
- The bounded reopen is bounded by an explicit list (`docs/prd-v2.md` §10) plus a compression rule (§9); any future widening needs a new ADR.
