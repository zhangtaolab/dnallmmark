---
gsd_state_version: "1.0"
milestone: v0.7.1
current_phase: 2
current_phase_name: Data Contracts & Test Harness
status: planning
stopped_at: Phase 01 complete, ready to plan Phase 2
last_updated: "2026-10-09T00:51:06.719Z"
last_activity: 2026-10-09
last_activity_desc: Phase 01 complete, transitioned to Phase 2
state_head: 38f4f31fe1c2ac241a3a2b1aafba4e1e9ed9bfac
progress:
  total_phases: 6
  completed_phases: 1
  total_plans: 3
  completed_plans: 3
  percent: 17
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-09)

**Core value:** Every number on the public leaderboard is correct and reproducible from code that external reviewers can trust.
**Current focus:** Phase 2 — Data Contracts & Test Harness

## Current Position

Phase: 2 — Data Contracts & Test Harness
Plan: Not started
Status: Ready to plan
Last activity: 2026-10-09 — Phase 01 complete, transitioned to Phase 2

Progress: [██░░░░░░░░] 17% (1/6 phases)

## Performance Metrics

**Velocity:**
- Total plans completed: 3
- Average duration: -
- Total execution time: -

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 3 | - | - |

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

Last session: 2026-10-08T14:56:39.800Z
Stopped at: Phase 01 complete, ready to plan Phase 2
Resume file: None
