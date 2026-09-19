# PRD v2: Volta Banking — Portfolio 2.0 (Improvement)

**Author:** Nikita Boyarkin
**Date:** 2026-09-19
**Status:** Approved (pending sprint execution)
**Version:** 2.0
**Supersedes:** `docs/prd.md` v1 as the *active* document (v1 is retained unchanged as the as-is snapshot)
**Decision record:** [`docs/adr/0001-bounded-reopen-volta-2.0.md`](adr/0001-bounded-reopen-volta-2.0.md)

---

## 1. Executive Summary

The portfolio is complete and healthy: 17 projects (12 analytical scripts + a Market & Jobs layer), 170 passing tests, 98% coverage on active code, `ruff`/`mypy` clean, CI green, public on GitHub (4★) with an external landing page. v1 deliberately froze this state ("fixate as-is, no new features") and out-scoped dashboards, external libraries, and new domains.

PRD v2 reopens exactly one bounded window — a weekend "2.0" sprint — whose job is **conversion (Goal A)** backed by **analytical credibility (Goal B)**: one causal-inference layer that tests the portfolio's own central claim, one explainability layer on churn, one **zero-install HTML board** that a recruiter can open in a browser, plus a bounded polish set. Everything that is not one of those carve-outs stays out of scope, and that list is restated explicitly (§10) so the bounded reopen cannot drift into a full one.

## 2. Problem Statement

### 2.1 Why v1's "fixate" is now the wrong call

- **The portfolio's job is conversion, not completion.** It must turn a hiring manager's attention into an interview; a museum of 17 finished scripts does not do that on its own.
- **Breadth is saturated; the missing signals are elsewhere.** 17 scripts + 170 green tests + 98% coverage already prove engineering discipline. The 18th script adds ≈0 conversion. What is missing is (a) a face a recruiter can open **without installing anything**, and (b) a depth signal that separates this repo from the hundreds of "funnel + churn" portfolios.
- **The central narrative claim is currently causal-sounding but correlation-only.** The story asserts the KYC progress bar *caused* +5.72pp activation → +9.2pp M3 retention. Project 3 supports the retention half with a pre/post Welch t-test — a **correlation**, not a causal estimate. A senior evaluator who reads Project 3 will notice.

### 2.2 Impact on the user

- **Who is affected:** hiring managers and tech leads evaluating product-analyst candidates (primary); BI-analyst screeners (secondary).
- **How:** they decide within one screen whether the portfolio is memorable, and within a few minutes whether it shows seniority.
- **Severity:** High — the repo survives a scan today, but does not yet stand out or prove senior judgment.

### 2.3 Business impact

- **Cost of the problem:** opportunity cost — a portfolio that fails to convert attention loses interview slots for a data/product analyst in fintech.
- **Strategic importance:** the repo is the primary evidence artifact for the candidate's product-analyst hiring goal.

### 2.4 Why solve it now

v1's freeze was correct while the project was being built. It is now the binding constraint: the gap between "good enough to scan" and "memorable enough to call" is exactly the one sprint this PRD defines.

## 3. Decision Summary (v1 → v2 delta)

| Area | v1 decision | v2 decision | Why |
|------|-------------|-------------|-----|
| Scope | Fixate as-is; no new features | **Bounded reopen** — one 2.0 sprint | Conversion + depth need content v1 forbade |
| Dashboard | Out of scope (Streamlit/Dash) | **Self-contained HTML board in scope** (Streamlit still out) | Recruiter needs a zero-install face |
| External libraries | scikit-learn only | **+ `shap`** (single targeted add) | Explainability is expected for churn models |
| Causal analysis | Not present | **In scope** (`REQ-201`) | The core claim deserves a causal test |
| New analytical domains (18+) | Out | **Stays out** | Scope-creep guard |
| `src/` package refactor | Out | **Stays out** | High risk, zero recruiter value |
| Causal / SHAP / board | — | **The only three carve-outs** | Bounded reopen definition |

## 4. Goals & Success Metrics

### Goal A — Conversion (primary)

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Zero-install recruiter artifact | none | HTML board live, opens in a browser with no install, renders from committed CSVs | HTTP 200; manual open test |
| README above-the-fold | plain text index | badges + one-paragraph hook + hero image + board link | visual check |
| License present | none | `LICENSE` (MIT) | file exists |
| Landing visibility | board not linked | board linked from README and landing page | link check |
| Outcome proxy (30 days, non-blocking) | lander pageviews | increase + 1 case-study post published | PostHog on the landing site (`red-monitoring` skill) |

### Goal B — Credibility (engine)

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Causal test of the core claim | pre/post Welch only | DiD estimate + parallel-trends check + placebo test, effect size recovered | `REQ-201` script + test |
| Churn explainability | feature importance only | SHAP global summary + local waterfall | `REQ-202` script + PNG |
| Senior-signal presence | 0 of 2 carve-out analyses | 2 of 2 | script count |

### Goal C — Non-regression (gate)

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Tests | 170 passed | ≥ 170 passed | `make all` |
| Coverage (active code) | 98% | ≥ 90% | `uv run pytest` |
| Lint / types / CI | green | green | `ruff`, `mypy`, GitHub Actions |
| Doc drift | README (17 projects) ≠ prd (12 domains) | v2 is the single source of truth; README + `.planning/` reconciled | `REQ-206` check |

## 5. User Stories

### Story 1 — Recruiter: fast scan (5 minutes)
**As a** recruiter screening product-analyst portfolios, **I want to** open one link and see the whole story as living visuals, **so that I can** decide in minutes whether to forward the candidate.

**Acceptance Criteria:**
- [ ] A single HTML board opens from a link with no installation and no build step.
- [ ] It shows, per project, the business question, the key metric, and a rendered chart sourced from the repo's committed CSVs.
- [ ] The README's first screen links to the board and carries a one-paragraph hook.

### Story 2 — Hiring manager: depth signal
**As a** hiring manager who knows the standard portfolyo tropes, **I want to** see the candidate test their *own* claim rather than assert it, **so that I can** read seniority and statistical judgment.

**Acceptance Criteria:**
- [ ] The causal layer states a design (DiD), tests parallel trends, and reports a placebo/robustness check.
- [ ] It explicitly states the limitation that the data is synthetic, and frames the result as a methods demonstration that recovers a known effect.
- [ ] The churn model carries a SHAP global summary and at least one local explanation.

### Story 3 — Tech lead: run and verify
**As a** tech lead, **I want to** clone, run one command, and see everything green, **so that I can** trust the repo without reading every line.

**Acceptance Criteria:**
- [ ] `uv sync --all-groups && make all` is green on a clean checkout.
- [ ] New analyses follow the repository invariants (single-file `volta_*.py`, `functions + main()`, seeded data, PNG to `outputs/`).
- [ ] The ADR explains why the 2.0 sprint exists and what it excludes.

### Story 4 — Candidate (self): case-study artifact
**As the** candidate, **I want** a written case study that pairs with the board, **so that** I have a ready artifact for LinkedIn, the résumé, and interviews.

**Acceptance Criteria:**
- [ ] A problem → method → result → recommendation write-up exists and links to the board and repo.
- [ ] It reuses only numbers already verified in the repo.

## 6. Scope — Bounded 2.0

### 6.1 In scope

#### REQ-201: Causal layer on the KYC fix (Must)
**Description:** a new single-file analysis that tests the portfolio's central causal claim ("the KYC progress bar caused higher activation and retention") with a difference-in-differences design, instead of the pre/post Welch test alone. Ships as `scripts/volta_causal_kyc.py` plus a data extension/`generate_*` update if the design needs a never-treated comparison group.

**Acceptance Criteria:**
- [ ] States the design explicitly: treatment = post-fix cohorts vs a valid comparison group, outcome = M1/M3 retention (and activation as a secondary).
- [ ] Reports the DiD estimate with a confidence interval.
- [ ] Runs and reports a **parallel-trends** check on pre-period data.
- [ ] Runs a **placebo** test (fake cutoff / fake group) and reports the null.
- [ ] Prints an explicit limitation that the data is synthetic and the result is a methods demonstration, not an empirical finding about a real bank.
- [ ] Follows repo invariants (single-file, seeded, PNG to `outputs/`, `functions + main()`), with a test and green CI.
- [ ] **Skill:** `causal-inference-workflow`.

#### REQ-202: SHAP explainability on churn (Should)
**Description:** add SHAP explanations to Project 5's Random Forest — global summary plot and at least one local waterfall for a representative churned user.

**Acceptance Criteria:**
- [ ] Uses `shap.TreeExplainer` on the trained RF.
- [ ] Produces a global summary PNG in `outputs/`.
- [ ] Produces at least one local explanation PNG with readable feature attributions.
- [ ] `shap` is pinned in `pyproject.toml` + `uv.lock` via `uv add`.
- [ ] Test + green CI.
- [ ] **Skill:** no dedicated skill — implement directly; plot with `matplotlib-scripts`. (Droppable if the weekend compresses — see §9.)

#### REQ-203: Self-contained HTML board (Must)
**Description:** one self-contained `.html` file built from the repo's committed CSVs that presents all projects (question → metric → chart → takeaway), openable with a double-click and no server.

**Acceptance Criteria:**
- [ ] Single file; libraries inlined, **no CDN**, no runtime network.
- [ ] Renders at least the core narrative (funnel, A/B, retention, segmentation) plus the Market & Jobs findings from committed CSVs.
- [ ] Reachable from the README and linked on the landing page.
- [ ] Reproducible via a build command (e.g. `make board`) so it cannot silently drift from the CSVs.
- [ ] **Skill:** `powerbi-style-dashboard` (primary), `html-artifacts` (fallback).

#### REQ-204: README above-the-fold (Must)
**Description:** turn the README's first screen into a conversion surface.

**Acceptance Criteria:**
- [ ] Status badges (CI, Python version, coverage) render correctly.
- [ ] A one-paragraph hook states what the portfolio is and the single strongest result.
- [ ] A hero image (funnel or board screenshot) sits above the fold.
- [ ] The board link and PRD v2 link are in the first screen.
- [ ] **Skill:** `github-profile-readme` (badge/widget patterns), `writing-guidelines`.

#### REQ-205: LICENSE (Must)
**Description:** add an MIT `LICENSE` (the public portfolio currently has none).

**Acceptance Criteria:**
- [ ] `LICENSE` at repo root, MIT, correct copyright holder.
- [ ] README references the license.
- [ ] **Skill:** none required (optionally `opensource-pipeline`).

#### REQ-206: Doc-drift reconciliation (Must)
**Description:** v2 becomes the single source of truth for scope; README and `.planning/` are reconciled to it.

**Acceptance Criteria:**
- [ ] README project count and PRD v2 agree.
- [ ] `.planning/IMPROVEMENT-PLAN.md` gains a Sprint 7 pointing at this PRD.
- [ ] No document contradicts v2's scope/out-of-scope lists.
- [ ] **Skill:** `documentation-and-adrs`, `context-architecture`.

#### REQ-207: Code tour (Should)
**Description:** a CodeTour `.tour` that walks a reader through the repo (entry point → shared utils → one core script → one Market & Jobs script → tests).

**Acceptance Criteria:**
- [ ] `.tour` file(s) with real file/line anchors.
- [ ] Referenced from README.
- [ ] **Skill:** `code-tour`.

#### REQ-208: Social preview (Should)
**Description:** an Open Graph / repository social-preview image so shared links render a branded card.

**Acceptance Criteria:**
- [ ] One 1200×630 image with the portfolio name, the strongest metric, and the board aesthetic.
- [ ] Uploaded as the GitHub social preview.
- [ ] **Skill:** `image`.

#### REQ-209: Case-study post (Must, after the sprint)
**Description:** a written case study (problem → method → result → recommendation) pairing with the board, for LinkedIn/résumé.

**Acceptance Criteria:**
- [ ] Reuses only numbers already verified in the repo.
- [ ] Links to the board and repo.
- [ ] Published and linked from the board/README.
- [ ] **Skill:** `linkedin-content-studio`, `post-writer`.

#### REQ-210: PRD v2 + ADR + vault mirror (Must — this deliverable)
**Description:** this document, the ADR, and the vault mirror note.

**Acceptance Criteria:**
- [ ] `docs/prd-v2.md` exists and is linked from the README.
- [ ] `docs/adr/0001-bounded-reopen-volta-2.0.md` exists.
- [ ] Vault mirror `PRD v2 - Volta Banking.md` exists with frontmatter + ≥3 wikilinks.
- [ ] **Skill:** `prd-writer`, `architecture-decision-records` / `domain-modeling`.

### 6.2 Skill map (feature → skill → artifact)

| Feature | Skill(s) | Artifact |
|---------|----------|----------|
| REQ-201 causal layer | `causal-inference-workflow` | `scripts/volta_causal_kyc.py` + test + PNG |
| REQ-202 SHAP | `matplotlib-scripts` (no dedicated skill) | SHAP PNGs + `shap` dep |
| REQ-203 HTML board | `powerbi-style-dashboard` / `html-artifacts` | `docs/board/volta_board.html` |
| REQ-204 README hero | `github-profile-readme`, `writing-guidelines` | README first screen |
| REQ-205 LICENSE | — | `LICENSE` |
| REQ-206 doc-drift | `documentation-and-adrs`, `context-architecture` | reconciled docs |
| REQ-207 code tour | `code-tour` | `.tours/*.tour` |
| REQ-208 social preview | `image` | OG image |
| REQ-209 case study | `linkedin-content-studio`, `post-writer` | published post |
| REQ-210 PRD/ADR | `prd-writer`, `architecture-decision-records` | this doc + ADR + vault note |
| Verification | `fable-judge`, `code-review` | sign-off report |
| Outcome tracking | `red-monitoring` | PostHog delta on the landing page |

### 6.3 Explicit carve-outs

The bounded reopen grants exactly three exceptions to v1's freeze: **REQ-201** (causal layer), **REQ-202** (SHAP), **REQ-203** (HTML board). Everything else in this sprint is polish, documentation, or verification — no new analytical domains.

## 7. Non-Functional Requirements & Invariants

- **Single-file pattern preserved:** every analysis is a standalone `volta_*.py` with `functions + main()` and an import-safe guard.
- **Reproducibility preserved:** `SEED = 42`, synthetic data only, no runtime network calls.
- **Quality gate is non-negotiable:** all tests green, coverage ≥ 90%, `ruff` clean, `mypy` clean, CI green. Every new analysis ships with a test.
- **No `src/` refactor** in this sprint.
- **Dependencies:** one targeted addition (`shap`), pinned via `uv add` → `uv.lock`; no other new runtime dependency without a stated justification in this PRD.
- **No PII / no secrets:** synthetic data only.

## 8. Technical Considerations

### 8.1 Causal design (REQ-201)
- **Design:** difference-in-differences. Treatment = cohorts after the Sep 2024 KYC fix; comparison = a plausible never-treated / not-yet-treated group (a segment whose KYC flow was unchanged by the fix, or a pre-period placebo group). The generator may need a small extension to guarantee a clean comparison group and a stable pre-trend.
- **Checks:** parallel-trends on pre-period retention; a placebo cutoff in the pre-period (expect a null); sensitivity to the comparison group.
- **Honesty constraint:** the data is synthetic, so the "estimate" recovers the generator's parameter. The script must say so and be framed as a methods demonstration.

### 8.2 SHAP (REQ-202)
- `shap.TreeExplainer` on the RF already trained in Project 5; global `summary_plot` + local `waterfall` for one churned and one retained archetype.

### 8.3 HTML board (REQ-203)
- Built from committed CSVs at build time; libraries inlined; single file; a `make board` target regenerates it so board and CSVs cannot drift silently.
- Placement: `docs/board/volta_board.html` (repo) and linked from the existing landing page `Personal_Projects.github.io/projects/volta/`.

### 8.4 Architecture (unchanged)
```
utils/common.py (data_path, OUTPUT_DIR, CONSTANTS, setup, print_section)
        │
        ▼
volta_<domain>.py  (functions + main())   ← new: volta_causal_kyc.py
        │
        ▼
data/*.csv ⇐ generate_*.py (seeded)   outputs/*.png   docs/board/volta_board.html
```

## 9. Implementation Roadmap — Sprint 7 (weekend, ~10–12 h)

| # | Task | Effort | Depends on |
|---|------|--------|-----------|
| 1 | REQ-210 PRD v2 + ADR + vault mirror | 0.5 h | — (done) |
| 2 | REQ-201 causal layer + test | 3.0 h | — |
| 3 | REQ-202 SHAP + `shap` dep | 1.5 h | — |
| 4 | REQ-203 HTML board + `make board` | 3.0 h | data stable |
| 5 | REQ-204/205/206/207/208 polish batch | 2.0 h | REQ-210 |
| 6 | Verification (fable-judge / code-review) + `make all` | 0.5 h | all |
| 7 | REQ-209 case study (post-sprint) | 1.0 h | REQ-203, 209 |

**Compression rule (if the weekend shrinks):** drop in this order — REQ-208 → REQ-207 → REQ-202. Never drop REQ-201, REQ-203, REQ-204, REQ-205, REQ-206, REQ-210.

**Ordering rationale:** the two depth analyses (REQ-201/202) come first because they are the risky, differentiating work; the board (REQ-203) is high-value but mechanical; polish is last because it is cheap and can absorb remaining time.

## 10. Out of Scope (restated)

1. **Streamlit / Dash app** — replaced by the zero-install HTML board (REQ-203). Still out.
2. **`src/` package refactor** — out; high risk to a working, fully-tested repo, zero recruiter value.
3. **New analytical domains (18+)** — out; breadth is saturated.
4. **Real data / API / DB integration** — out; synthetic only.
5. **Model serialization (`joblib`/`pickle`) / deployment** — out; the analyses are demonstrations.
6. **External CLV/attribution libraries** (`lifetimes`, `pymc-marketing`, `mta`) — out.
7. **XGBoost / LightGBM / CatBoost** — out; SHAP works on the existing Random Forest.
8. **Only carve-outs:** REQ-201, REQ-202, REQ-203.

## 11. Risks & Mitigation

| Risk | P | I | Severity | Mitigation | Contingency |
|------|---|---|----------|------------|-------------|
| Bounded reopen drifts into a full reopen | Medium | High | **High** | §10 explicit list + ADR + compression rule | Cut tasks per §9 rule |
| Causal layer reads as a real finding on synthetic data | Medium | Medium | **Medium** | Script states the limitation explicitly; framed as methods demo | Add a prominent callout box |
| Board diverges from CSVs over time | Medium | Medium | **Medium** | `make board` regenerates from committed CSVs | Add to `make all` |
| New `shap` dependency breaks CI/deps | Low | Medium | **Medium** | Pin via `uv add`; verify `make all` after | Make SHAP optional/guarded |
| Doc drift recurs (README vs PRD) | Low | Low | **Low** | v2 is single source; REQ-206 checkpoint | One doc-sync pass |
| Weekend time shortfall | Medium | Medium | **Medium** | §9 compression rule, priority ordering | Ship Must-only |

## 12. Validation Checkpoints

### Checkpoint A — End of Sprint 7
- [ ] REQ-201, 203, 204, 205, 206, 210 complete; REQ-202/207/208 per compression rule.
- [ ] `make all` green; tests ≥ 170; coverage ≥ 90%.
- [ ] Board opens with no install and renders from committed CSVs.
- [ ] README first screen: badges + hook + hero + links.
- [ ] **If failed:** treat as regression, not as "done".

### Checkpoint B — 30 days after
- [ ] Board linked from the landing page; pageview delta observed (PostHog, non-blocking).
- [ ] Case-study post published.
- [ ] No doc drift reintroduced.

## 13. Open Questions

1. **Board placement** — publish the board at the existing landing path `/projects/volta/` or a new `/volta-board/` route? (Owner: maintainer; Low impact.)
2. **Comparison group for DiD** — use a not-yet-treated segment or a fabricated pre-period placebo cohort? Decide during REQ-201 implementation.

---

*Scope: bounded reopen. 10 requirements (3 carve-outs + 7 polish/doc), 4 user stories, all mapping to available skills. v1 remains the historical as-is snapshot; this document is the active contract.*
