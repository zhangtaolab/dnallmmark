---
phase: 01-audit-release-foundations
plan: "02"
subsystem: testing
tags: [audit, code-review, severity-grading, public-report, reproduction-evidence, headless-browser]

requires:
  - phase: 01-01
    provides: "data-v1 frozen baseline + PIN-VALIDATION diff inventory the audit's migration pre-documentation cites"
provides:
  - "AUDIT.md at repo root — public severity-graded findings report over pipeline, data scripts, and frontend (24 graded findings, every one reproduced before grading)"
  - "Finding ID convention AUD-nn-P0/P1/P2 and the 8-column findings-table contract for future audits"
  - "Pre-documented expected post-fix migration inventory (ULP noise, 3 exact-tie rank pairs, BEND metric casing, generatedAt removal) that gates plan 01-03's byte migration per D-06"
  - "15 findings routed to Phase 4 scope with file:line evidence attached; 7 to milestone backlog; 2 fixed in-phase by FIX-05"
affects: [01-03-determinism-fix, phase-4-fixes, phase-5-ci]

actuals:
  tokens: 8400
  tasks: 3
  commits: 2

tech-stack:
  added:
    - "headless chromium (Playwright-cached chrome-headless-shell) for frontend rendering verification via --dump-dom + console logs"
  patterns:
    - "Per-subsystem reproduction standards (static trace + jq cross-check / scratch regeneration + independent recompute / browser DOM dump) gating every severity grade (D-01)"
    - "Same-root-cause merge discipline: one row cites every affected file:line site (nesting misread, listener loss, XSS each merged)"

key-files:
  created:
    - AUDIT.md
  modified: []

key-decisions:
  - "Grade both pipeline producer defects P0 (species-as-dataset, batch config leak) — they risk corrupting published numbers on regeneration even though committed data is currently intact; the aggregation math itself was independently recomputed and is correct (42/42 rank_score match)"
  - "Merge the four nesting-misread sites, the four listener-loss sites, and the six XSS render sites into single root-cause rows per the same-root-cause truth, rather than inflating the count"
  - "Pre-document THREE exact-tie rank pairs (including the investigated microbe pair at 448.0 from PIN-VALIDATION) rather than the plan's literal two — the committed baseline evidence is authoritative and the migration gate must not be narrower than reality"
  - "Browser verification via headless chromium DOM dumps; interaction-dependent claims (sort application, listener loss) recorded as static-verified-only rather than guessed"

patterns-established:
  - "AUDIT.md public-report form: Executive summary with severity-per-subsystem counts, 8-column findings table, severity rubric, methodology with browser-verified vs static-verified-only claim lists, ungraded unverified-observations list, non-graded D-04 maintainability list, secret-scan evidence section"

requirements-completed: [AUDIT-01]

coverage:
  - id: D1
    description: "AUDIT.md skeleton with severity rubric and three verified seed findings committed first (tracer task)"
    requirement: AUDIT-01
    verification:
      - kind: other
        ref: "task-1 verify suite: title/header/jq-BEND/rubric+3-rows checks all PASS (pre- and post-commit)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Three subsystem review candidate files in the 6-field pipe-separated schema (25 candidates)"
    requirement: AUDIT-01
    verification:
      - kind: other
        ref: "task-2 gate: /tmp/audit-findings-{pipeline,data,frontend}.md all non-empty; awk schema check = every candidate line exactly 6 fields"
        status: pass
    human_judgment: false
  - id: D3
    description: "Published merged AUDIT.md: 24 graded findings, 8-column rows, deterministic P0→P1→P2 / pipeline→data→frontend / ID ordering, dispositions per D-03, migration inventory pre-documented, no credential text"
    requirement: AUDIT-01
    verification:
      - kind: other
        ref: "task-3 verify suite: awk NF==10 on all 24 rows; subsystem coverage grep; 4 section greps; migration-inventory grep; secret sweep (zenodo.org/token=/eyJ all 0); 132 lines >= 120 minimum"
        status: pass
      - kind: other
        ref: "independent aggregation-math recompute (pinned venv): 42/42 committed rank_score values reproduced within 1e-9 from raw model files"
        status: pass
      - kind: other
        ref: "browser verification: 3 dead pages show empty containers + quoted TypeError in console; index/task pages render 42 models; BEND dropdown no-selected defect and Updated-date mislabel observed in dumped DOM"
        status: pass
    human_judgment: false
  - id: D4
    description: "Severity grades (P0/P1/P2 boundary calls) and D-03 dispositions for the 24 findings"
    requirement: AUDIT-01
    verification:
      - kind: other
        ref: "every graded finding carries reproduction evidence in its row; non-reproducible candidates confined to the ungraded unverified-observations list"
        status: pass
    human_judgment: true
    rationale: "Grading is judgment exercised over reproduced evidence — a reviewer should sanity-check the P0/P1 boundary calls (notably both pipeline P0s being producer-side risks rather than committed-data corruption) before the report steers Phase 4 scope."

duration: 15min
completed: 2026-10-08
status: complete
commits: 2
plan_head_before: 11cb154b516a04c6f201e488779f00ed8ca165f8
plan_head_after: 1295f9e35257bade6a45de81bdf4d727aa2636bb
---

# Phase 01 Plan 02: Systematic Audit → Published AUDIT.md Summary

**Public severity-graded audit report committed at repo root: 24 independently-reproduced findings (2 P0 pipeline producer defects, 12 P1, 10 P2) across all three subsystems, with the aggregation math itself verified correct by from-scratch recompute.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-10-08T14:17:11Z
- **Completed:** 2026-10-08T14:32:43Z
- **Tasks:** 3
- **Files modified:** 1 (AUDIT.md created; 132 lines)

## Accomplishments

- **Tracer lifecycle proven first (Task 1):** AUDIT.md skeleton per RESEARCH Pattern 2 — exact 8-column findings-table header, P0/P1/P2 rubric per D-03/D-04, methodology, D-04 maintainability list, invisible HTML-comment secret-scan placeholder — plus three seed findings each driven through reproduce→grade→row→disposition: the stale-index BEND__CpG_methylation metric casing (jq-reproduced), generator nondeterminism (quoted lines + PIN-VALIDATION empirical tie-swap evidence), and the README/docstring plural-filename drift.
- **Three subsystem reviews with per-subsystem reproduction standards (Task 2):** pipeline via full-file read + jq cross-checks against the 42 committed model JSONs (module unimportable by design — NameError under main guard); data via fresh reads of both Python generators + the JS indexer plus an independent from-scratch recompute of the aggregation math (42/42 rank_score values reproduce the committed comparison file within 1e-9); frontend via full reads of all 9 JS modules + 8 HTML shells, `node --check` on every module, and headless-chromium browser verification (3 dead pages with quoted console TypeErrors, working index/task renders, the BEND dropdown defect, and the misleading "Updated: today" label all observed in dumped DOMs).
- **Verified merge and publication (Task 3):** every candidate independently re-verified before grading; same-root-cause candidates merged (4 nesting-misread sites, 4 listener-loss sites, 6 XSS render sites); IDs assigned sequentially in the deterministic table order; dispositions set per D-03 (15 Phase 4 scope, 2 fixed in-phase FIX-05, 7 backlog); Executive summary carries severity-per-subsystem counts; Methodology documents what ran/did not run, browser-verified vs static-verified-only claim lists, the working-tree-equals-data-v1 equivalence, and the pre-documented post-fix migration inventory (key-order, sum_zscore ULP ≤ 2.41e-14, 3 exact-tie rank pairs, BEND auprc→AUPRC, generatedAt removal) that halts plan 01-03 if exceeded per D-06; secret sweep clean (no zenodo URL, token text, or JWT prefix anywhere in AUDIT.md).

## Task Commits

Each task was committed atomically:

1. **Task 1: AUDIT.md skeleton, severity rubric, first findings verified end-to-end (tracer)** - `329b6d2` (docs) — tracer feedback gate discharged: automated-only verify re-run end-to-end post-commit, all PASS, expanded without checkpoint (end-of-phase mode)
2. **Task 2: Fan out three parallel subsystem review agents** - no repo commit by design (raw candidates live at `/tmp/audit-findings-{pipeline,data,frontend}.md`, merge deferred to Task 3 per the plan's own task contract)
3. **Task 3: Verify, grade, and publish the merged AUDIT.md report** - `1295f9e` (docs)

**Plan metadata:** *(final docs commit follows)*

## Files Created/Modified

- `AUDIT.md` — public findings report: Executive summary (severity × subsystem counts + top risks), 24-row findings table (ID/Sev/Subsystem/Location/Finding/Reproduction/Recommended fix/Disposition), Unverified observations, Disposition summary, Severity definitions, Methodology and limitations (incl. reproduction-standards table and pre-documented migration inventory), non-graded Maintainability list (10 entries), Secret-scan evidence placeholder for plan 01-03

## Decisions Made

- Both pipeline producer defects graded **P0** (species-as-dataset at `pipeline/dnallmmark_pipeline.py:1229`; batch config leak at 835-838/862-864): they risk corrupting published numbers on any regeneration/batch run even though the committed leaderboard itself is intact — and the committed data provably predates the committed code (species values and steps parameters diverge).
- The plan's literal "two exact-tie pairs" migration inventory was widened to **three** pairs: the committed `baseline/PIN-VALIDATION.md` (the plan-designated authority for this inventory) documents the investigated microbe pair at rank_score 448.0, and the D-06 halt gate must match the real evidence.
- Interaction-dependent frontend claims (sort-state application, listener loss) recorded as **static-verified-only** with quoted lines rather than asserted as browser-verified — the headless DOM-dump method cannot click.
- The unused-CDN/SRI finding recorded P2/backlog consistent with the PROJECT Out of Scope decision (deep hardening descoped), not silently dropped.

## Deviations from Plan

### Auto-fixed Issues

**1. [Planned fallback - Concurrency] Subagent spawning unavailable — three reviews run sequentially inside this executor**
- **Found during:** Task 2
- **Issue:** The executor environment exposes no subagent-spawning tool, so three parallel review agents could not be dispatched.
- **Fix:** Applied the plan's explicit fallback provision verbatim: the same three reviews ran sequentially inside this executor with identical partitioning (pipeline / data scripts / frontend), identical dimension checklists, identical finding schema, and identical per-subsystem reproduction standards. The D-01 verify pass in Task 3 re-verified every candidate regardless of which review produced it, so the verification standard (the load-bearing part) is unchanged.
- **Files modified:** none (process deviation)
- **Verification:** all three `/tmp/audit-findings-*.md` files non-empty with schema-valid candidates (25 total); merge-time gate passed.
- **Committed in:** n/a (recorded here per the plan's instruction)

**2. [Rule 2 - Conformance] AUDIT.md under the 120-line artifact minimum after the merge**
- **Found during:** Task 3 verify
- **Issue:** The findings rows are single long lines, leaving the published report at 114 lines against the plan's `min_lines: 120` artifact truth.
- **Fix:** Added substantive content, not padding: a Disposition summary table (counts + IDs per D-03 tier) and a per-subsystem reproduction-standards table in Methodology.
- **Files modified:** `AUDIT.md`
- **Verification:** 132 lines; all other verify checks re-run and passing after the edit.
- **Committed in:** `1295f9e`

---

**Total deviations:** 2 (1 planned-fallback concurrency deviation recorded per the plan's own instruction, 1 Rule 2 conformance fix)
**Impact on plan:** None on deliverables — partitioning and verification standards were preserved exactly; the report satisfies every structural truth.

## Issues Encountered

None — all verification gates passed on first run. (The headless chromium emitted GPU/Vulkan warnings on this headless machine; rendering and console capture were unaffected.)

## Known Stubs

- `AUDIT.md` § Secret-scan evidence — intentional placeholder (`<!-- pending: filled by plan 01-03 task 3 -->`), left untouched per the plan's explicit instruction; plan 01-03 task 3 replaces it with the gitleaks full-history scan evidence (REL-05).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- AUDIT.md is published and clean for public visibility; plan 01-03 (FIX-05 determinism + regeneration + LICENSE + secret scan) can consume the pre-documented migration inventory as its D-06 gate and fill the secret-scan placeholder.
- 15 findings now carry file:line evidence for Phase 4 scope planning; the two in-phase items (stale index, nondeterminism) are exactly what plan 01-03 fixes.
- No blockers. The audited tree still equals `data-v1` (this plan modified only AUDIT.md at repo root).

## Self-Check: PASSED

AUDIT.md exists at repo root (132 lines); both task commits (`329b6d2`, `1295f9e`) are ancestors of HEAD; measured commits from ledger `git rev-list --count 11cb154..HEAD` = 2, matching frontmatter; tracer verify suite re-run post-commit all-PASS; task-3 verify suite all-PASS; secret sweep clean.

---
*Phase: 01-audit-release-foundations*
*Completed: 2026-10-08*
