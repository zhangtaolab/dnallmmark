---
gsd_state_version: "1.0"
milestone: v0.7.1
current_phase: 4
current_phase_name: Correctness & Methodology Core
status: executing
stopped_at: Completed 04-02-PLAN.md (unified exporter)
last_updated: "2026-10-10T05:25:54.721Z"
last_activity: 2026-10-10
last_activity_desc: Phase 4 execution started
state_head: 5b111d7312b949de54f3ad110b48925adbf5e7f1
progress:
  total_phases: 6
  completed_phases: 3
  total_plans: 15
  completed_plans: 14
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-09)

**Core value:** Every number on the public leaderboard is correct and reproducible from code that external reviewers can trust.
**Current focus:** Phase 4 — Correctness & Methodology Core

## Current Position

Phase: 4 (Correctness & Methodology Core) — EXECUTING
Plan: 5 of 5
Status: Ready to execute
Last activity: 2026-10-10 — Phase 4 execution started

Progress: [█████░░░░░] 50% (1/6 phases)

## Performance Metrics

**Velocity:**
- Total plans completed: 10
- Average duration: -
- Total execution time: -

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 3 | - | - |
| 02 | 3 | - | - |
| 3 | 4 | - | - |

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
| Phase 03 P03 | 10 min | 2 tasks | 6 files |
| Phase 03 P04 | 16 min | 3 tasks | 7 files |
| Phase 04 P01 | 17 min | 4 tasks | 11 files |
| Phase 04 P03 | 15 min | 3 tasks | 16 files |
| Phase 04 P04 | 43 min | 2 tasks | 5 files |
| Phase 04 P02 | 19 min | 3 tasks | 9 files |
| Phase 04 P02 | 19 min | 3 tasks | 9 files |

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
- [Phase 03]: [Phase 03]: 03-03: [gpu] group replaces [pipeline] with exact pins torch==2.11.0+cu130 / transformers==5.17.0 via the explicit torch-scoped pytorch-cu130 index (T-03-07) — definition-only per D-05, never synced; dev env provably torch-free; uv.lock re-resolved same-commit
- [Phase 03]: [Phase 03]: 03-03: ty 0.0.85 joins dev group with [tool.ty] config + make typecheck zero-diagnostics gate; torch_npu.** added empirically to replace-imports-with-any (research glob missed run_finetune.py:44 Huawei NPU import)
- [Phase 03]: [Phase 03]: 03-03: PlantHelixSeek card filled from the D-09 ModelScope card inside the unified registry — 62 entries unchanged, complete cards 44->45, card-absent enumeration 18->17 (plan's post-fill '44 complete' was the stale pre-fill count; 62-17=45); PIPE-02/PIPE-03 deliberately stay Pending — only their D-05 deferred metadata form landed
- [Phase 03]: 03-04: run_sweep failure capture is (subprocess.SubprocessError, OSError), not except Exception — D-08's noqa prohibition + widened lint scope force a specific-exception boundary at the launch seam; driver bugs abort loudly (BLE001 probed to fire even on underscore bindings)
- [Phase 03]: 03-04: F401 torch_npu fixed via importlib.import_module (import removal would break Ascend NPU support — the import's registration side effect makes torch.npu exist); SIM115 fixed by wrapping the model-loop body in a with-open block, break/continue semantics preserved
- [Phase 03]: 03-04: G1 dead (seed_{seed}/ outdir + seed-scoped resume marker), D-07 grad_accum and D-11 head_config leaks fixed, run_sweep.py landed with --dry-run + fake-executor proof only — zero model runs (D-05/D-06 held; E2' stays gated at F1->F2->E2')
- [Phase 04]: [Phase 04]: 04-01: Multiple->Animals majority mapping maintainer-approved at the blocking Category gate (verbatim 'approved', 50-row record committed as 04-CATEGORY-REVIEW.md); regeneration matched the previewed inventory exactly (total+plant byte-identical, animal/microbe 42/42 via the single membership swap, 22/13 counts preserved)
- [Phase 04]: [Phase 04]: 04-01: all three Phase-2 xfail locks (AUD-01/WR-02/WR-03) unmarked to permanent green contracts per D-13, each in the same commit as its fix; comparator gains INT + BOOL_CROSS labels (IN-01/WR-02); get_float isfinite guard proven number-neutral on committed data
- [Phase 04]: 04-03: shared navbar.js is the single navbar source; static <nav> blocks removed from ALL 5 real shells (plan named only models/datasets — every shell carried one; one-navbar-per-page invariant required all five)
- [Phase 04]: 04-03: live Playwright verification 48/48 (zero console errors on all 6 pages, sort/modal/delegation interactions, submission flow, hostile-string inert) via CLI driver fallback — MCP browser tools absent in executor session
- [Phase 04]: 04-04: four quirk registries ported with LEGACY_NAME_MAP parity (rename PlantCAD2-Large-l48-d1536→PlantCAD2-Large; drops prokbert-mini-c/-long/MutBERT); safetensors is the 11-entry union (plant-dnamamba-6mer + PlantGFM); limited-length dict WIRED (AUD-15 dead config made functional); tier table composes min(bs_new, cap) before the VRAM estimators with legacy grad_accum compensation — parity tests mutation-proven 8/8
- [Phase 04]: 04-04: 62/62 complete cards — 10 from confirmed public pages, 7 (no locatable upstream: Chaoba×3, denseSSM, mamba2×2, prokbert) from the operational row + "" absent-convention, never fabricated; context_len "" not 0 (schema would render a wrong number vs fail loudly at E2'); space≡SPACE confirmed same model under two keys, kept distinct, merge surfaced to maintainer

### Pending Todos

None yet.

### Blockers/Concerns

- Zenodo preview-token revocation remains a manual out-of-repo action; recorded as a post-publish option (D-08, token read-only scoped)
- Phase 3: GPU work runs on the NVIDIA GB10 aarch64 machine against the local dnallm dev clone (`/home/forrest/Github/DNALLM` @ c99fa9d) — permanently outside CI scope
- Phase 6: Dataset-by-dataset license terms for murkier genomics datasets may need spot verification during execution
- Maintainer registry decisions from 04-04: (1) space and SPACE are the same model under two registry keys (committed info block identical; no distinct lowercase-space upstream) — merge decision (62→61) is the maintainer's; (2) 7 models (Chaoba×3, denseSSM_plant_genome, mamba2_370M, mamba2_plant_genome, prokbert) have no locatable public card — "" card fields await maintainer backfill (will fail exporter schema loudly if exported); (3) prokbert↔neuralbioinfo/prokbert-mini size-correspondence ambiguity (existing prokbert-mini card links the 20.6M repo while its own op row says 25M ≡ prokbert-mini-c)

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-10-10T05:25:54.659Z
Stopped at: Completed 04-02-PLAN.md (unified exporter)
Resume file: None
