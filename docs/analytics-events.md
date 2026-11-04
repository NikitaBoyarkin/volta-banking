# Reader-path analytics — event contract (REQ-006)

**Status:** contract only — **nothing in this repository emits events**
**Owner:** maintainer
**Companion:** [`prd-v2.md` §4 Goal A.1](prd-v2.md#goal-a--conversion-primary), [`prd-improvement.md` REQ-006](prd-improvement.md)

This file defines the events that measure the Volta portfolio's north-star metric, so the
landing site can be implemented against a fixed contract. Instrumentation lives in the
portfolio site repo, not here (see [§6 PENDING](#6-pending--what-is-not-implemented)).

**Verified:** `rg -i "posthog|capture\(|track\("` across this repo (excluding `*.html`) returns
only documentation mentions. No event is emitted from `scripts/`, the board, or CI today.

---

## 1. North-star metric

**Click-to-repository rate (30 days).** The share of readers who open the Volta landing page
and then click through to the GitHub repository within 30 days of that first pageview.

```
numerator   = unique persons with `repo_clicked` (repo = volta-banking)
              who also have a `$pageview` on /projects/volta/
denominator = unique persons with a `$pageview` on /projects/volta/
rate        = numerator / denominator
window      = 30 days from each person's first landing pageview
```

The numerator is **restricted to the denominator cohort**, so the ratio cannot exceed 100%.
A reader who reaches the repo from the README without ever visiting the landing page is
counted in neither term.

| Field | Value |
|---|---|
| Baseline | **unknown (no instrumentation before release)**. The first 30-day window establishes it. |
| Target | **10%** — an assumption, recalibrated against the first measured window. |
| Secondary ratio | `repo_clicked` ÷ `board_opened` — "of readers who opened the board, how many went to the source?" Diagnoses a leak between board and repo. |

### 1.1 PostHog insight shape

Two shapes, for two jobs. Both use **unique persons**, never total events.

**Faithful shape — Funnel (used for the headline number):**

| Step | Event | Filter |
|---|---|---|
| 1 | `$pageview` | `pathname = /projects/volta/` (and `/en/projects/volta/`) |
| 2 | `repo_clicked` | `repo = volta-banking` |

Settings: conversion window **30 days**, "unique users" aggregation, breakdown by
`first_utm_source` and `locale`. The funnel's step-1 count is the denominator and step-2 the
numerator.

**Reporting shape — Trends with a formula (used on the dashboard):**

```
Series A:  repo_clicked         → Aggregation: Unique users   → Filter: repo = volta-banking
Series B:  $pageview            → Aggregation: Unique users   → Filter: pathname = /projects/volta/
Formula:   A / B * 100
Interval:  week, displayed over a rolling 30-day window
```

**Hygiene rules.** Exclude local/dev traffic (the site already refuses to initialise on
`localhost` / `127.0.0.1`, see `Analytics.astro`). Exclude the maintainer's own sessions with a
PostHog filter on `initial_referrer_class` or an internal-users rule. Record the exclusion
rule alongside the number — a rate computed over unfiltered traffic is not the metric.

---

## 2. Events

All three events use the site's existing `track()` helper
(`src/lib/analytics.ts:215–229`) and the delegated `[data-analytics]` click handler in
`src/components/Analytics.astro`, which attaches `{ path }` automatically.

### 2.1 `board_opened`

**Trigger:** a click on the "Открыть дашборд →" anchor on the Volta project page
(`href={demoHref}`). In the site this is `src/pages/projects/[slug].astro:299–306` (RU) and
`src/pages/en/projects/[slug].astro:305–312` (EN). The board target is
`demo: demos/volta/index.html` (`src/content/projects/volta.md:44`).

| Prop | Type | Required | Meaning |
|---|---|---|---|
| `page` | string | yes | Pathname of the page the click happened on, e.g. `/projects/volta/` |
| `source` | enum | yes | `project_page` \| `readme` \| `board_direct` — where the opener came from |
| `board_version` | string | yes | Build identifier of the board (`make board` output; e.g. git short SHA or build date) |
| `locale` | `ru` \| `en` | yes | Derived from the path (`localeFromPath`) |
| `utm_*` | string | via super props | `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term` — see §3 |

**Must NOT capture:** anything typed, query strings beyond the UTM keys, element text, or the
visitor's identity.

### 2.2 `repo_clicked`

**Trigger:** a click on the "Смотреть на GitHub →" anchor (`href={project.data.github}`,
value `https://github.com/NikitaBoyarkin/volta-banking`). Wiring point in the site:
`src/pages/projects/[slug].astro:315–322` (RU) and
`src/pages/en/projects/[slug].astro:321–328` (EN).

| Prop | Type | Required | Meaning |
|---|---|---|---|
| `page` | string | yes | Pathname of the page the click happened on |
| `source` | enum | yes | `project_meta` \| `readme` \| `board` \| `footer` — placement of the link |
| `repo` | string | yes | `volta-banking` — keeps the event reusable if other repos are tracked later |
| `board_version` | string | conditional | Required when `source = board`; the board build the reader came from |
| `locale` | `ru` \| `en` | yes | Derived from the path |
| `utm_*` | string | via super props | See §3 |

**Must NOT capture:** GitHub referrer, the visitor's GitHub identity, or the code path they
open. The event marks intent only.

### 2.3 `contact_clicked`

**Trigger:** a click on any contact-intent CTA — Telegram, email, booking, or the link that
opens `/contact/`. Fires **before** navigation; it does not observe whether a message was sent.

| Prop | Type | Required | Meaning |
|---|---|---|---|
| `page` | string | yes | Pathname of the page the click happened on |
| `source` | enum | yes | `nav` \| `footer` \| `hero` \| `case_next_step` \| `post_next_step` — placement |
| `channel` | enum | yes | `telegram` \| `email` \| `booking` \| `contact_page` — destination class |
| `locale` | `ru` \| `en` | yes | Derived from the path |
| `utm_*` | string | via super props | See §3 |

**Must NOT capture:** form field values, message text, the visitor's email or phone, or the
Telegram username they clicked. `session_recording.maskAllInputs` is already enabled; that is
not a substitute for omitting these props.

---

## 3. `utm_*` — carried as super properties, not per-event

The site already registers campaign attribution once per page load in
`registerSuperProperties()` (`src/lib/analytics.ts:481–516`):

- `first_utm_source` / `first_utm_medium` / `first_utm_campaign` / `first_utm_content` / `first_utm_term`
- `visit_utm_source` / … (same five keys, per visit)
- plus `locale`, `initial_referrer_class`, `landing_path`

Events **must not re-implement UTM capture**. Read the campaign from these properties. If a
surface sits outside the site's `Analytics.astro` (for example the standalone board file),
pass the five `utm_*` keys explicitly on the event — and only then.

---

## 4. Report and gate

| Item | Where |
|---|---|
| Dashboard | A PostHog dashboard named `Volta — reader funnel`, link recorded in the report below |
| Report | `reports/reader-funnel-YYYY-MM-DD.md` in this repo — the numbered rate, its window, denominator, exclusions, and the dashboard link |
| Owner | maintainer |

**Rule.** Thirty days after instrumentation ships, the report must contain a number. A missing
measurement is **gate failure** (REQ-006 AC3) — not "no signal", not "inconclusive", not a
reason to extend the window. If the PostHog project has zero `repo_clicked` events, the gate
still fails: zero is a measurement, absence of data is not.

---

## 5. Evidence status

| Claim | Class | Basis |
|---|---|---|
| No instrumentation exists in this repo | Verified | `rg -i "posthog\|capture(\|track\("` outside docs returns nothing |
| Site repo is reachable and has a `track()` helper | Verified | `NikitaBoyarkin.github.io/src/lib/analytics.ts:215` |
| Repo link is rendered at the cited lines | Verified | `[slug].astro:315–322` (RU), `:321–328` (EN); `volta.md:27` |
| 10% is the right target | **Inferred** | Reasoning, not a benchmark — recalibrate on the first window |
| The metric will reach the target | **Not verified** | No event has ever fired |

---

## 6. PENDING — what is not implemented

Every row below is owed and blocked outside this repository.

| # | Action | Owner | Blocking dependency |
|---|---|---|---|
| 1 | Add `board_opened` + `data-analytics` attribute to the board anchor | site maintainer | PR to `NikitaBoyarkin.github.io`; this repo's scope stops at the contract |
| 2 | Add `repo_clicked` + `data-analytics="repo_clicked"` to the GitHub anchor | site maintainer | same PR |
| 3 | Add `contact_clicked`, or map it onto existing `contact_page_click` / `booking_click` | site maintainer | decision on whether a new name is worth a second series |
| 4 | Declare all three in `AnalyticsEventMap` | site maintainer | `src/lib/analytics.ts:31` — the typed map currently has no such names |
| 5 | Emit `board_version` from the board build | board build (REQ-203, `make board`) | board build must inject a version string |
| 6 | Create the PostHog dashboard and record its link | maintainer | events 1–4 shipped; `PUBLIC_POSTHOG_KEY` set in site CI |
| 7 | Write the 30-day report in `reports/` | maintainer | 30 days of traffic after 1–6 |

### 6.1 Where the events would be wired

The portfolio site **was found** at:

```
/Users/nikitaboarkin/Desktop/00 ide/00 portfolio/NikitaBoyarkin.github.io
```

Remote: `git@github.com:NikitaBoyarkin/NikitaBoyarkin.github.io.git`.

| Event | File | Line | Anchor today |
|---|---|---|---|
| `repo_clicked` | `src/pages/projects/[slug].astro` | 315–322 | `<a class="project-meta-link" href={project.data.github}>Смотреть на GitHub →` |
| `repo_clicked` | `src/pages/en/projects/[slug].astro` | 321–328 | same anchor, English page |
| `board_opened` | `src/pages/projects/[slug].astro` | 299–306 | `<a class="project-meta-link" href={demoHref}>Открыть дашборд →` |
| `board_opened` | `src/pages/en/projects/[slug].astro` | 305–312 | same anchor, English page |
| event map | `src/lib/analytics.ts` | 31 | `interface AnalyticsEventMap { … }` |
| click dispatch | `src/components/Analytics.astro` | `handleClick` | delegated `[data-analytics]` → `track(kind, { path })` |

**Not edited.** This contract deliberately stops at naming the files. Changing the site is a
separate PR in a separate repository, against a separate CI and Lighthouse budget.
