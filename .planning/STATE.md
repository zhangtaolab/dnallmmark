---
gsd_state_version: "1.0"
milestone: v0.7.1
current_phase: 3
current_phase_name: Dev-Branch Reconciliation & P0 Revision Blockers
status: executing
stopped_at: Phase 3 context gathered (code-first directive)
last_updated: "2026-10-09T10:55:10.389Z"
last_activity: 2026-10-09
last_activity_desc: Phase 3 planning complete
state_head: e14e159a39188d5db26e31218c74ce41c8c1b293
progress:
  total_phases: 6
  completed_phases: 2
  total_plans: 10
  completed_plans: 6
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-09)

**Core value:** Every number on the public leaderboard is correct and reproducible from code that external reviewers can trust.
**Current focus:** Phase 2 — Data Contracts & Test Harness

## Current Position

Phase: 3 (Dev-Branch Reconciliation & P0 Revision Blockers) — READY TO EXECUTE
Plan: Not started
Status: Ready to execute
Last activity: 2026-10-09 — Phase 3 planning complete

Progress: [███░░░░░░░] 33% (1/6 phases)

## Performance Metrics

**Velocity:**
- Total plans completed: 6
- Average duration: -
- Total execution time: -

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 3 | - | - |
| 02 | 3 | - | - |

**Recent Trend:**
- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01 P01 | 9 min | 2 tasks | 8 files |
| Phase 01 P02 | 15 min | 3 tasks | 1 files |
| Phase 01 P03 | 16 min | 3 tasks | 59 files |
| Phase 02 P02-01 | 6 min | 3 tasks | 11 files |
| Phase 02 P02 | 14 min | 3 tasks | 13 files |
| Phase 02 P03 | 7 min | 2 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: 6-phase dependency spine (determinism → manifests → schemas/tests → dnallm-dev pipeline adaptation → fixes → CI → recompute → packaging); ordering is load-bearing
- Roadmap: PIPE-01..03 (dnallm dev adaptation, added to requirements mid-roadmap per user) became Phase 3 — schemas from Phase 2 define PIPE-03's structural validity, and the Phase 4 species fix lands in the adapted pipeline
- Roadmap: REL-05 (Zenodo token revocation) added to REQUIREMENTS.md — release-blocking item listed in PROJECT.md Active but had no requirement ID
- [Phase 01]: Baseline artifact form: annotated data-v1 tag + tracked SHA256 manifest + tracked comparator, no duplicated golden copies (git stores exact bytes at the tag; 52 copies would rot)
- [Phase 01]: Dependency pins: floor bounds pandas>=2.2,<3.0 + numpy>=2.0,<3 in pyproject, exactness from committed uv.lock (pandas 2.3.3 / numpy 2.5.3); pipeline GPU group never CI-installed
- [Phase 01]: Pin validation (D-06) discharged: all regeneration diffs root-caused (sum_zscore ULP <=2.4e-14, exact-tie rank swaps incl. investigated third microbe pair at 448.0, tasks.json metric-casing + generatedAt); pins authoritative
- [Phase 01]: baseline/compare.py --summary-json is the machine-readable migration-gate contract consumed by plan 01-03 (complete untruncated diff inventory)
- [Phase 01]: Audit grading: both pipeline producer defects P0 (species-as-dataset, batch config leak) — committed leaderboard intact but unreproducible from committed code; aggregation math independently recomputed correct (42/42)
- [Phase 01]: AUDIT.md migration inventory pre-documents THREE exact-tie rank pairs (PIN-VALIDATION's investigated microbe pair included, not just the plan's literal two) — baseline evidence is authoritative for the D-06 gate
- [Phase 01]: Frontend audit verified via headless-chromium DOM dumps; interaction-dependent claims recorded static-verified-only — 15 findings routed to Phase 4 scope with file:line evidence
- [Phase 01]: FIX-05 landed: deterministic generators (sorted iteration, sort_keys, no live clock) with the one-time 52-file migration fully attributed against data-v1; fourth exact-tie pair investigated into the inventory (6-group census recorded in AUDIT.md)
- [Phase 01]: Secret scan settled behaviorally: gitleaks 8.30.1 default jwt rule misses markdown-paren-closed JWTs (detection rule added) and global path allowlists act as file-level exclusion (rule-scoped AND allowlist used) — probe finds exactly the 1 intentional link, production scan clean over all refs
- [Phase 01]: License landed: MIT for code (LICENSE + README section, atomic with CC BY 4.0 derived-data terms and upstream-terms disclaimer); copyright holder confirmed by maintainer 2026-10-09 as 'zhangtaolab and DNALLM-Mark contributors' (D-09 resolved in UAT)
- [Phase 02]: Plan 02-01: self-contained schema files (defs duplicated, no cross-file $ref) — per-file strictness, local forced versioning (resolved Open Question 1)
- [Phase 02]: Plan 02-01: make test excludes node --test until tests/js/ exists in plan 02-02; lint scope tests/-only this phase (D-04, ~21 pre-existing production findings deferred with Makefile comment)
- [Phase 02]: Plan 02-02: constant-score guard test uses binary-exact 0.5 (np.std([0.7]*3) is one ULP > 0, so the std==0 guard never fires for decimal constants); gamma aggregate total asserted as 0 (plan's '=1' slip); goldens chain-produced and walk()-compared
- [Phase 02]: Plan 02-03: D-10's ~40s/chain estimate never re-timed — measured ~0.3s/run; docstring records reality, slow marker stays by lane quality not cost
- [Phase 02]: Plan 02-03: research Pattern 2's parents[2] anchor resolved outside the repo (false-lock hazard) — corrected to parents[1], --runxfail probe proves locks fail on real defects
- [Phase 02]: Plan 02-03: three xfail(strict=True) defect locks landed (AUD-01-P0 AST, WR-02 walk, WR-03 get_float nan/inf/-inf) — Phase 4 contract is fix + remove marker in same commit

### Pending Todos

None yet.

### Blockers/Concerns

- Zenodo preview-token revocation remains a manual out-of-repo action; recorded as a post-publish option (D-08, token read-only scoped)
- Phase 3: GPU work runs on the NVIDIA GB10 aarch64 machine against the local dnallm dev clone (`/home/forrest/Github/DNALLM` @ c99fa9d) — permanently outside CI scope
- Phase 6: Dataset-by-dataset license terms for murkier genomics datasets may need spot verification during execution

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-10-09T09:22:53.390Z
Stopped at: Phase 3 context gathered (code-first directive)
Resume file: .planning/phases/03-dev-reconciliation-revision-blockers/03-CONTEXT.md
