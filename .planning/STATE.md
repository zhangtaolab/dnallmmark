---
gsd_state_version: "1.0"
milestone: v0.7.1
current_phase: 03
current_phase_name: Dev-Branch Reconciliation & P0 Revision Blockers
status: executing
stopped_at: Completed 03-02-PLAN.md (D-10 unification, F1 dev splits, EVAL-01 refusal guard)
last_updated: "2026-10-09T16:58:02.085Z"
last_activity: 2026-10-10
last_activity_desc: Phase 03 execution started
state_head: 883eafb3e35b05e2df11b401ebb10986bab75824
progress:
  total_phases: 6
  completed_phases: 2
  total_plans: 10
  completed_plans: 8
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-09)

**Core value:** Every number on the public leaderboard is correct and reproducible from code that external reviewers can trust.
**Current focus:** Phase 03 — Dev-Branch Reconciliation & P0 Revision Blockers

## Current Position

Phase: 03 (Dev-Branch Reconciliation & P0 Revision Blockers) — EXECUTING
Plan: 3 of 4
Status: Ready to execute
Last activity: 2026-10-10 — Phase 03 execution started

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
| Phase 03 P01 | 15 min | 3 tasks | 7 files |
| Phase 03 P02 | 19 min | 3 tasks | 13 files |

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
- [Phase 03]: 03-01: merge resolved mechanically per verified inventory (checkout --ours x51, git rm -f x6 dev-added data files) — zero hand-edited generated JSON; byte-empty staged diff proven before the merge commit
- [Phase 03]: 03-01: README Run Pipeline section updated beyond the two named lines (args block, models_info.txt, --fix_token_len dropped, --auto_batch_size) so the renamed entry point is not misdocumented by adjacent prose; exporter sentence deferred to REV-03
- [Phase 03]: 03-01: D-03 lock = species in {Animals,Plants,Microbe,Multiple} AND == datasets_info Category (OQ-1 recommendation); fixture-injectable, --runxfail-proven non-vacuous on athaliana defect
- [Phase 03]: 03-01: D-04 review of commit 8d99daf verdict CLEAN, 4 observations recorded (2 AUD-16-interaction edges, pre-existing inert drawBorder, aria-pressed) — no new AUD rows
- [Phase 03]: [Phase 03]: 03-02: D-10 unification — name-column lands as a field on every merged entry (key == Model_name/Dataset_name), required by the dict read site; converter extensions --rename-name (merge-key + cell rewrite) and --derive-operational (card-only entries) were the only conversion code authored
- [Phase 03]: [Phase 03]: 03-02: registry counts are disk-authoritative — 5 stale dev-side counts corrected (4 Train + 4 Test header-inclusive on Deep4mC x3/iPro-WAEL; BEND Dev/Test transposed); --check extended to verify Train/Dev/Test against disk, 7 unlocatable GUE dirs (partial extraction) WARNING-excluded to the E2E gate
- [Phase 03]: [Phase 03]: 03-02: REFUSED guard sits after the selection filters and before task-config/model load (fires only for datasets that would actually run, still precedes load_model_and_tokenizer and data_dict); two-layer EVAL-01 enforcement closed — suite opt-in contract + driver fail-fast + config purity (allow_test_as_eval never set)

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

Last session: 2026-10-09T16:58:02.052Z
Stopped at: Completed 03-02-PLAN.md (D-10 unification, F1 dev splits, EVAL-01 refusal guard)
Resume file: None
