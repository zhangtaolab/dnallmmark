---
phase: 04-correctness-methodology-core
plan: 03
subsystem: ui
tags: [static-site, vanilla-js, es-modules, shared-navbar, event-delegation, escapeHTML, submit-flow, playwright-live]

# Dependency graph
requires:
  - phase: 04-correctness-methodology-core
    provides: committed models_comparison*.json data (04-01) that the restored pages render live; the Phase-2 schemas/model_performance.json contract that submit validation mirrors
provides:
  - One shared config-driven navbar renderer (js/navbar.js) on all 6 real pages — the AUD-09 crash class and the nav-less index/task pages are dead
  - All four AUD-10 nesting misreads fixed — finetuning/datasets/models tables render real model x dataset rows
  - AUD-11 sort state honored + AUD-12 re-render-safe delegated listeners at all four sites
  - AUD-20 cased metricMap — the default task view selects AUPRC
  - submit.html as the 6th real page + schema-current validateJSON + corrected PR instructions (FIX-03)
  - DataAPI.escapeHTML (5-char entity set) + node:test unit + live hostile-string inertness proof (FIX-04, bounded scope)
  - Live per-page Playwright evidence: 48/48 assertions, 0 failed, zero console errors on every page (04-03-PLAYWRIGHT-EVIDENCE.txt)
affects: [end-of-phase UAT (live spot-check), E2' regeneration frontend consumers, Phase 5 review]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
# Same estimateTokens scale (chars/4 over the realized diff), never a harness token count.
actuals:
  tokens: 8713      # 34,852 diff chars / 4 over base 75320fd..HEAD at SUMMARY time
  tasks: 3
  commits: 2        # MEASURED: git rev-list --count 75320fd..HEAD (Task 3 is evidence-only; docs commit follows)
plan_head_before: 75320fd9aecf0429b2bfbe86fa7f8816fc968f26
plan_head_after: b461268486ae0d294d63a6067bd2a26e3a5bc55b

# Tech tracking
tech-stack:
  added: []          # vanilla ES-module MPA preserved — no libraries, no build step, no npm packages
  patterns:
    - "One shared renderer module (navbar.js) over CONFIG constants replaces per-page copies and static HTML duplicates — single navbar source per page"
    - "Event delegation on persistent containers (closest()-based) for every control whose parent's innerHTML is re-rendered"
    - "Sink-side escapeHTML at bounded DOM-build sites; pinned by node:test unit + live hostile-string e2e"

key-files:
  created:
    - dnallm-mark/js/navbar.js
    - dnallm-mark/submit.html
    - tests/js/data-escape.test.js
    - .planning/phases/04-correctness-methodology-core/04-03-PLAYWRIGHT-EVIDENCE.txt
  modified:
    - dnallm-mark/index.html
    - dnallm-mark/task.html
    - dnallm-mark/finetuning.html
    - dnallm-mark/models.html
    - dnallm-mark/datasets.html
    - dnallm-mark/js/data.js
    - dnallm-mark/js/main.js
    - dnallm-mark/js/task.js
    - dnallm-mark/js/finetuning.js
    - dnallm-mark/js/models.js
    - dnallm-mark/js/datasets.js
    - dnallm-mark/js/submit.js

key-decisions:
  - "Static <nav> blocks removed from ALL 5 real shells, not just models/datasets as the plan named — every shell carried one (research under-detected), and the plan's own 'exactly one navbar source exists per page' invariant required all five (documented as a deviation)"
  - "showParameterModal's dataset lookup fixed to the .performance level in the same change as the AUD-10 row fix — the modal lookup read the document root and would have silently never opened after the row fix (Rule 1 companion)"
  - "models.js's LIVE aggregateSpecies caller (loadData) fixed alongside the plan-named dead caller in data.js recalculateComparison — it is the site that actually populated the models-page species column"
  - "Playwright driven headless via the CLI/driver path (chromium-1243 executablePath) — MCP browser tools unavailable in this executor session; the plan's fallback governs"

patterns-established:
  - "Shared chrome (navbar/footer) renders through one module imported by every page controller — new pages get it by importing navbar.js, not by copying"
  - "Live verification evidence = per-page console-capture transcript + DOM/interaction assertions recorded next to the SUMMARY"

requirements-completed: [FIX-01, FIX-03, FIX-04]

coverage:
  - id: D1
    description: "FIX-01/SC-3: every one of the 6 real pages loads with zero console errors, a shared 6-link navbar, and fully rendered content; all nav links resolve 200 from every page"
    requirement: FIX-01
    verification:
      - kind: automated_ui
        ref: "04-03-PLAYWRIGHT-EVIDENCE.txt — per-page zero-console-error + navbar + content + nav-link assertions (index 8/8, task 7/7, finetuning 8/8, models 7/7, datasets 6/6, submit 12/12)"
        status: pass
    human_judgment: false
  - id: D2
    description: "AUD-10: all four wrong-level consumers iterate the performance dict — finetuning shows 1974 real dataset rows (0 info/performance-named rows), datasets shows 47 real datasets, models species column populated (0/42 N/A)"
    requirement: FIX-01
    verification:
      - kind: automated_ui
        ref: "04-03-PLAYWRIGHT-EVIDENCE.txt — finetuning/datasets/models AUD-10 row assertions with first-row cell values (GUE__emp_H3, BEND__CpG_methylation, 'Microbe, Animals, Plants')"
        status: pass
    human_judgment: false
  - id: D3
    description: "AUD-11/AUD-12: leaderboard sort honors currentSort + sortAscending (name header changes order then reverses; numeric header sorts desc then asc); delegated listeners survive re-renders (modal opens after model-select re-render; header sort works twice on models/datasets)"
    verification:
      - kind: automated_ui
        ref: "04-03-PLAYWRIGHT-EVIDENCE.txt — index AUD-11 x2, finetuning AUD-12 x3, models + datasets delegation assertions"
        status: pass
    human_judgment: false
  - id: D4
    description: "AUD-20: the task page's default BEND__CpG_methylation view shows AUPRC selected in the metric dropdown (value 'auprc', label 'AUPRC ↑') instead of Runtime"
    verification:
      - kind: automated_ui
        ref: "04-03-PLAYWRIGHT-EVIDENCE.txt — task 'AUD-20 default view selects AUPRC' assertion"
        status: pass
    human_judgment: false
  - id: D5
    description: "SC-4/FIX-03: submit.html reachable (200) from every page; a real committed DNABERT-2-117M_performance.json validates to a 47-dataset preview and generates PR instructions naming dnallm-mark/data/model_performance/{alias}_performance.json; malformed root and per-entry shapes rejected with dataset+key-naming messages"
    requirement: FIX-03
    verification:
      - kind: automated_ui
        ref: "04-03-PLAYWRIGHT-EVIDENCE.txt — submit SC-4 x4 assertions (real file, dataset count, PR path, both malformed cases)"
        status: pass
    human_judgment: false
  - id: D6
    description: "SC-5/FIX-04: escapeHTML (5-char entity set, non-string passthrough) exported from data.js, pinned by node:test unit, and applied at the bounded DOM-build sites (shared navbar, all submit-page user-entered renderers + PR block + error messages, touched task dropdown renderer); hostile model-name renders as inert text with the payload flag never set"
    requirement: FIX-04
    verification:
      - kind: unit
        ref: "tests/js/data-escape.test.js (3 tests, node --test green in make test)"
        status: pass
      - kind: automated_ui
        ref: "04-03-PLAYWRIGHT-EVIDENCE.txt — SC-5 x2 (preview inert, PR block inert; window.__pwned=undefined, 0 injected <img>)"
        status: pass
    human_judgment: false
  - id: D7
    description: "Live-UX spot-check of the restored site (plan Task 3 <human-check>): browse all 6 pages — navbar present and visually consistent, leaderboard sortable by clicking headers, finetuning modal opens after changing the model select, submit page accepts a real model_performance file and renders PR instructions, task dropdown shows AUPRC on first load, F12 console clean"
    verification:
      - kind: automated_ui
        ref: "04-03-PLAYWRIGHT-EVIDENCE.txt — the machine-checked shadow of this list (48/48)"
        status: pass
    human_judgment: true
    rationale: "The plan's Task 3 <human-check> is surfaced at end-of-phase UAT: visual consistency and feel of the restored pages (not just DOM presence) are human judgment; the automated pass covers the mechanical facts only."

# Metrics
duration: 15 min
completed: 2026-10-10
status: complete
---

# Phase 4 Plan 03: Static-Site Restoration Summary

**All 6 pages live on one shared config-driven navbar with zero console errors, AUD-10/11/12/20 fixed, the submission flow restored as a schema-current escaped 6th page, and 48/48 live Playwright assertions green**

## Performance

- **Duration:** 15 min
- **Started:** 2026-10-10T02:06:14Z
- **Completed:** 2026-10-10T02:21:22Z
- **Tasks:** 3/3
- **Files modified:** 16 (12 modified + 4 created incl. evidence)

## Accomplishments

- **FIX-01 (SC-3):** `js/navbar.js` is the single navbar source — config-driven over `CONFIG.NAV_LINKS`, pathname-active (root-aware), escaped, null-guarded. All 5 existing shells + the new submit shell carry `.navbar-container`; every static `<nav class="navbar">` block is gone; main.js/task.js render the navbar they never had; the AUD-09 TypeError crash class is dead. Live: zero console errors on every page, 6 nav links everywhere, all 6 targets 200 from every page.
- **AUD-10 (with the crash fix, per Pitfall 2):** finetuning `prepareLeaderboardRows` + `showParameterModal`, datasets `loadData`, the data.js `recalculateComparison` caller, the LIVE models.js `aggregateSpecies` caller, and submit.js all read the `{info, performance}` document's performance map. Live: finetuning renders 1974 real model×dataset rows (zero info/performance-named rows), datasets 47 real datasets, models species column populated 42/42.
- **AUD-11 (D-14):** `filterAndSortModels` switches on `currentSort` (lexical for Model, numeric otherwise) and honors `sortAscending`. Live: Model header click reorders (PlantHelixSeek→SPACE), second click reverses (SPACE→AgroNT); Sum MinMax sorts desc(43.82) then asc(5.74).
- **AUD-12 (D-14):** sortable headers (main/models/datasets) and finetuning rows + modal close/overlay bind via `closest()` delegation on persistent containers. Live: modal opens after a model-select re-render (47 filtered rows, modal head "GENERanno-euskaryote-0.5b-base / GUE__emp_H3"); header sorting works twice on every table.
- **AUD-20:** metricMap carries AUPRC/AUROC/F1/MCC/R2 → lowercase keys. Live: default BEND__CpG_methylation view selects `auprc` ("AUPRC ↑").
- **FIX-03 (SC-4):** `submit.html` (datasets.html shell, shared navbar, FileReader-only) + `validateJSON` enforcing the Phase-2 shape ({info, performance} + per-entry dataset/parameters/performance, per-entry error naming) + PR instructions naming `dnallm-mark/data/model_performance/{alias}_performance.json`. Live: real DNABERT-2-117M file validates to a 47-dataset preview; both malformed fixtures rejected with the exact messages.
- **FIX-04 (SC-5):** `escapeHTML` in data.js pinned by 3 node:test units; applied at the shared navbar, every submit-page user-entered renderer (model name, submitter, email, PR block, validation-error messages), and the touched task dropdown renderer. Live: `<img src=x onerror="window.__pwned=1">` in the model-name field renders as literal text, `window.__pwned` stays undefined, zero injected elements.

## Per-page live Playwright evidence (CONTEXT frontend-Q4)

Full transcript (console captures + DOM/interaction assertions, 48/48 PASS): `.planning/phases/04-correctness-methodology-core/04-03-PLAYWRIGHT-EVIDENCE.txt`

| Page | Assertions | Console errors | Content evidence | Interactions |
|------|-----------|----------------|------------------|--------------|
| index (/) | 8/8 | **0** | 42 leaderboard rows, scatter canvas | sort changes + reverses; numeric desc/asc |
| task (/task.html) | 7/7 | **0** | 48 task options, 42 rows, banner | default selects AUPRC (value `auprc`) |
| finetuning (/finetuning.html) | 8/8 | **0** | 1974 real dataset rows, 0 garbage rows | modal open → close → model-select re-render → modal opens again |
| models (/models.html) | 7/7 | **0** | 42 rows, species 0/42 N/A ("Microbe, Animals, Plants") | header sort works twice |
| datasets (/datasets.html) | 6/6 | **0** | 47 real datasets (first: BEND__CpG_methylation) | header sort works twice |
| submit (/submit.html) | 12/12 | **0** | form present | real file validates (47 datasets); malformed root + per-entry rejected; hostile string inert; PR path correct |

All 6 navbar links (including `/submit.html`) resolve 200 from every page. Harness: Playwright 1.64.0 driver, chromium-1243 headless, over `bash start-server.sh` (:8080, stopped after capture); CDN scripts (Chart.js/SheetJS) loaded live from jsDelivr.

## Task Commits

Each task was committed atomically:

1. **Task 1: Shared navbar on all 6 shells + escapeHTML util + JS-lane unit** — `44cb531` (feat)
2. **Task 2: AUD-10/11/12/20 + submit page restored to schema (FIX-03)** — `b461268` (fix)
3. **Task 3: LIVE Playwright verification (6 pages, interactions, submission flow, hostile string)** — evidence recorded in this SUMMARY + `04-03-PLAYWRIGHT-EVIDENCE.txt`; no product changes needed (48/48 first-clean run after two driver-only harness fixes)

**Plan metadata:** (docs commit follows this SUMMARY)

## Files Created/Modified

- `dnallm-mark/js/navbar.js` — NEW: shared renderNavbar (NAV_LINKS template, pathname-active, escaped, null-guarded)
- `dnallm-mark/submit.html` — NEW: 6th real page (datasets.html shell, `.navbar-container` + `.submit-container`, no CDN tags)
- `tests/js/data-escape.test.js` — NEW: node:test unit for escapeHTML (entity coverage, combined payloads, non-string passthrough)
- `dnallm-mark/{index,task,finetuning,models,datasets}.html` — static `<nav>` replaced by `.navbar-container`
- `dnallm-mark/js/data.js` — escapeHTML helper + aggregateSpecies caller passes `perfData.performance`
- `dnallm-mark/js/main.js` — shared navbar call, dead renderNavbar variant removed, AUD-11 comparator, AUD-12 header delegation
- `dnallm-mark/js/task.js` — shared navbar call, AUD-20 cased metricMap, escaped dropdown renderer
- `dnallm-mark/js/finetuning.js` — shared navbar, AUD-10 row loop + modal lookup, AUD-12 row/modal delegation
- `dnallm-mark/js/models.js` — shared navbar, aggregateSpecies caller level fix, header-sort delegation
- `dnallm-mark/js/datasets.js` — shared navbar, AUD-10 dataset loop, header-sort delegation
- `dnallm-mark/js/submit.js` — shared navbar, schema-current validateJSON, escaped renderers/error messages, PR instructions on the real layout

## Decisions Made

- Static nav removal extended to all 5 shells (deviation, below) — the plan's models/datasets-only instruction rested on an under-detected premise.
- The finetuning modal lookup and the models.js aggregateSpecies caller fixed as Rule 1 companions of the named AUD-10 sites (both would have left user-visible breakage the plan's own live assertions target).
- Validation-error messages escaped along with the named user-entered fields — the message interpolates file-sourced dataset names (T-04-08: a hostile file's name must not execute in the error path).
- Verification harness run via the Playwright CLI driver (executablePath chromium-1243) since MCP browser tools were absent in this executor session; harness-only fixes during the run (template-literal `\s`/`\d` escaping, a truncated-slice check) — zero product changes needed for 48/48.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan-fact mismatch] Static nav removed from all 5 real shells, not only models/datasets**
- **Found during:** Task 1 (shell edits)
- **Issue:** The plan/research state only models.html and datasets.html carry static `<nav class="navbar">` blocks; in fact all 5 real shells do (verified by reading index/task/finetuning HTML). Literal execution would stack a static 2-link nav above the shared 6-link navbar on 3 pages — violating the same instruction's stated goal ("exactly one navbar source exists per page") and the consistency the Playwright/human checks assert.
- **Fix:** Replaced the static nav block with `.navbar-container` in all 5 shells (the plan's verify commands still pass; they only forbid the static nav in models/datasets).
- **Files modified:** dnallm-mark/index.html, dnallm-mark/task.html, dnallm-mark/finetuning.html (beyond the named models/datasets)
- **Verification:** `grep -c 'nav class="navbar"' dnallm-mark/*.html` → only task-mockup.html (dev artifact, untouched by design); live 6-link navbar on every page, zero duplication.
- **Committed in:** 44cb531

**2. [Rule 1 - Bug] finetuning modal dataset lookup read the document root**
- **Found during:** Task 2 (AUD-10 fix)
- **Issue:** `showParameterModal` looked up `performanceData[modelName]?.[datasetName]` — after the row loop iterates `.performance`, the passed datasetName only exists under `.performance`, so the modal would silently never open (failing the plan's own AUD-12 modal assertion).
- **Fix:** `this.state.performanceData[modelName]?.performance?.[datasetName]`.
- **Files modified:** dnallm-mark/js/finetuning.js
- **Verification:** Live modal opens before and after the model-select re-render (evidence finetuning AUD-12 ×3).
- **Committed in:** b461268

**3. [Rule 2 - Missing critical functionality] models.js live aggregateSpecies caller left at the wrong level**
- **Found during:** Task 2 (AUD-10 fix)
- **Issue:** The plan names the data.js:249 caller, which sits in dead `recalculateComparison`; the LIVE caller (models.js loadData) passed the whole document, keeping the models-page species column N/A — the exact symptom AUD-10 describes. (The plan's files_modified comment "AUD-10 downstream (aggregateSpecies)" for models.js confirms intent.)
- **Fix:** `DataAPI.aggregateSpecies(key, performanceData[key]?.performance)`.
- **Files modified:** dnallm-mark/js/models.js
- **Verification:** Live species column 0/42 N/A, first cell "Microbe, Animals, Plants".
- **Committed in:** b461268

---

**Total deviations:** 3 auto-fixed (2 Rule 1 bugs, 1 Rule 2 missing-critical companion)
**Impact on plan:** All three are the plan's own goals applied to facts the research under-detected; no scope creep — untouched renderers remain unescaped by design (frontend-Q3 lock), dev artifacts untouched.

## Issues Encountered

- Playwright MCP browser tools were not present in this executor session → the plan's sanctioned fallback (CLI driver + console capture) was used; chromium launched via explicit executablePath (chromium-1243) because the two npx-cached playwright copies expected newer browser revisions.
- Two driver-side-only defects during the live run (template-literal `\s`→`s` and `\d`→`d` escape collapse corrupting captured text; an `.includes()` run against a truncated slice) produced the only two FAILs of the first clean run — both fixed in the throwaway harness; product behavior was already correct (visible in the same transcripts) and the final run is 48/48 with zero product changes for Task 3.

## User Setup Required

None - no external service configuration required.

## Authentication Gates

None.

## Next Phase Readiness

- Ready for end-of-phase UAT: the Task 3 human-check (browse all 6 pages live) is recorded as coverage D7.
- Residual (documented, threat-model-accepted T-04-07): renderers outside this plan's touched set (main.js leaderboard rows/legend, task table rows/chart labels, models/datasets table cells, finetuning table cells/modal body) remain unescaped by the locked bounded-scope decision; AUD-21 debug-API and AUD-23 stale-cache classes remain out of scope per the plan's flagged assumptions.
- Suite baseline after this plan: 202 passed + 0 xfailed (pytest) + 5 node tests (was node 2), `make lint` and `make typecheck` clean.

## Self-Check: PASSED

- Files verified on disk: dnallm-mark/js/navbar.js, dnallm-mark/submit.html, tests/js/data-escape.test.js, 04-03-PLAYWRIGHT-EVIDENCE.txt — all FOUND
- Commits verified as ancestors of HEAD: 44cb531, b461268 — both FOUND
- All plan verify commands re-run post-commit: PASS (per task sections + gates above)

---
*Phase: 04-correctness-methodology-core*
*Completed: 2026-10-10*
