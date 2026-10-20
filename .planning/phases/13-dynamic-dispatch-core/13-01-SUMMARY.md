---
phase: 13-dynamic-dispatch-core
plan: 01
subsystem: infra
tags: [multi-gpu, dispatch, work-queue, subprocess, o-excl, threading, resume]

# Dependency graph
requires:
  - phase: 12-mgpu-static-orchestration
    provides: pipeline/run_sweep_shard.py launch+merge modes, the injectable main(spawner, clock) seam, _parse_gpus, WORKER_LOG_TIMESTAMP_FORMAT, and the 49-test static suite used as the byte-identity tripwire
provides:
  - pipeline/dispatch_core.py — the dispatch engine (remainder re-parse, validation mirror, enumeration+priority queue, singleton O_EXCL dispatcher lock, per-cell O_EXCL claim ledger, per-GPU worker threads, minimal dispatch_state.json writer, run_dispatch entry)
  - "--mode {static,dispatch} CLI surface on run_sweep_shard.py with mode routing + the dispatch×merge combination refusal"
  - "Frozen on-disk formats: {root}/dispatch_ledger/*.json claims, {root}/dispatch_ledger/dispatcher.lock, {root}/dispatch_state.json, {base}-dispatch-w{i}-{stamp}.log tees"
  - "Resume semantics proven under mid-cell kill (SC2): marker-or-ledger-completed skip, stale-claim requeue with atomic replacement, pid-liveness lock reclaim"
affects: [13-02 (mode coexistence/merge evidence), phase-14 MGPU-03/04/05 (state-file rendering, failure re-run, verify/cleanup), phase-15 VAL (N=2 smoke)]

# Actuals (#2632) — pairs with the plan's estimate to calibrate future estimates.
# Same estimateTokens scale (chars/4 over the realized diff), never a harness token count.
actuals:
  tokens: 25151   # chars/4 over the 100,607-char diff 13b1b4c..e5ff382 (estimate was 26000)
  tasks: 2
  commits: 2      # MEASURED: git rev-list --count 13b1b4c..HEAD

plan_head_before: 13b1b4c832b9d45c8b19330317529294b6d3fad2
plan_head_after: e5ff38216fc86cea3a78d3389ae106aa949b381d

# Tech tracking
tech-stack:
  added: []        # zero-dependency phase — Python stdlib only (threading, os.open O_EXCL, uuid, hashlib, urllib.parse)
  patterns:
    - "sys.argv swap remainder re-parse through run_sweep.parse_args (run_sweep stays the single flag owner, D-07)"
    - "O_EXCL create-or-refuse as a structural guard (claims + singleton lock; EEXIST is the refusal, never check-then-write)"
    - "Pure per-cell relaunch_decision (skip|fresh|requeue) — order-independent skip sets by construction"
    - "Per-GPU worker threads popping one in-memory queue under a lock; Popen.wait releases the GIL"

key-files:
  created:
    - pipeline/dispatch_core.py
    - tests/test_dispatch_core.py
  modified:
    - pipeline/run_sweep_shard.py

key-decisions:
  - "Claim filename frozen: percent-encoded (safe='') model/task/seed{n}[/frac{f}] fields joined with '--', plus '-' + sha256(canonical JSON of the tuple)[:12] + '.json' — the digest suffix guarantees injectivity over + aliases, __ task keys, float fractions, and '--'-containing names (Pitfall 5)"
  - "Worker tee logs are {base}-dispatch-w{i}-{stamp}.log siblings (distinct from static -mgpu-w naming); WR-02 fresh stamp per launch via the injectable clock"
  - "dispatch_state.json is written BEFORE any claim/spawn (mode evidence), atomically (tmp+os.replace), single writer under a state lock; counts total/completed/failed/skipped"
  - "A2 held: failed cells finalize their claim to 'failed' and are NEVER requeued within a live run — Phase 14 MGPU-04 owns re-run"
  - "A5 held: lock reclaim is pid-liveness only — live pid/PermissionError refuses loudly naming pid + run_id; ProcessLookupError or malformed lock reclaims by atomic overwrite; orphan-children kill-before-relaunch caveat documented in the module docstring"
  - "Output-root precedence locked: the shard --output-root (default ./finetuned) IS the dispatch root; directories.json output_root never redirects the orchestrator (the other four keys do apply flag > file > default)"

patterns-established:
  - "Compose-as-sibling-module dispatch engine: dispatch_core imports run_sweep/run_sweep_shard at its top; run_sweep_shard imports dispatch_core LAZILY inside main()'s dispatch branch (the 09-06 cycle-breaking precedent)"
  - "Per-cell scripted fake children keyed on (save-name model, task, seed) parsed from the spawned argv — index-scripted returncodes are flaky under multi-worker interleaving (Pitfall 7)"

requirements-completed: [MGPU-01, MGPU-02]

# Coverage metadata (#1602) — one entry per shipped deliverable.
coverage:
  - id: D1
    description: "--mode {static,dispatch} CLI surface with byte-identical static default, explicit --mode static == default, --help visibility, and the dispatch+merge combination refusal (A6/MGPU-06)"
    requirement: MGPU-01
    verification:
      - kind: unit
        ref: tests/test_dispatch_core.py#test_mode_flag_visible_in_help
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_mode_static_explicit_matches_default
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_dispatch_merge_combination_refused
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_static_launch_never_acquires_dispatch_lock
        status: pass
    human_judgment: false
  - id: D2
    description: "Dispatch engine happy path — deterministic (model×task×seed) queue over per-GPU workers, one child per cell with the verbatim static spawn discipline under the ONE shared root, dispatch_state.json mode evidence before any spawn, per-worker verdict table"
    requirement: MGPU-01
    verification:
      - kind: unit
        ref: tests/test_dispatch_core.py#test_dispatch_happy_path_end_to_end
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_dispatch_spawn_kwargs_verbatim_discipline
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_dispatch_state_file_exists_before_any_spawn
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_dispatch_queue_order_is_deterministic
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_dispatch_single_worker_drains_whole_queue
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_dispatch_zero_enumeration_refuses_before_lock
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_dispatch_peft_lane_enumerates_and_spawns_under_alias
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_dispatch_refuses_variant_peft_combination
        status: pass
    human_judgment: false
  - id: D3
    description: "Exactly-once O_EXCL claim ledger with frozen injective naming (digest suffix), filename↔JSON agreement, and the SC3 structural double-claim refusal"
    requirement: MGPU-02
    verification:
      - kind: unit
        ref: tests/test_dispatch_core.py#test_claim_filename_deterministic_and_injective
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_claim_json_agrees_with_filename
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_claim_cell_double_claim_structurally_refused
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_dispatch_worker_log_and_ledger_naming_is_frozen
        status: pass
    human_judgment: false
  - id: D4
    description: "Resume semantics — marker-or-ledger-completed skip filter, stale-claim requeue with atomic claim replacement, pid-liveness singleton-lock reclaim, and the SC2 kill test proving exactly-once re-dispatch under mid-cell SIGKILL"
    requirement: MGPU-02
    verification:
      - kind: unit
        ref: tests/test_dispatch_core.py#test_sc2_kill_test_resume_exactly_once
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_skip_filter_marker_and_claim_layers
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_requeued_claim_atomically_replaced_with_new_identity
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_lock_dead_pid_is_reclaimed
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_lock_live_pid_refuses_naming_holder
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_lock_malformed_content_is_reclaimed
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_skip_set_is_order_independent
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_drained_root_relaunch_is_nothing_to_do
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_malformed_claims_requeue_never_crash_never_skip
        status: pass
    human_judgment: false

# Metrics
duration: 17min
completed: 2026-10-20
status: complete
---

# Phase 13 Plan 01: 动态调度核心 (Dynamic Dispatch Core) Summary

**Work-queue dispatch engine: one dispatcher + per-GPU worker threads over the deterministic cell queue, an O_EXCL claim ledger + singleton lock under ONE shared root, and kill-proven exactly-once resume (SC2) — static mode byte-identical behind `--mode {static,dispatch}`**

## Performance

- **Duration:** 17 min
- **Started:** 2026-10-20T04:11:48Z
- **Completed:** 2026-10-20T04:29Z
- **Tasks:** 2/2
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments
- `pipeline/dispatch_core.py` (new sibling, stdlib-headless): remainder re-parse through `run_sweep.parse_args` (sys.argv swap — run_sweep stays the single flag owner), the full `run_sweep.main` startup-validation mirror (collect-all flag_problems incl. the variant×peft refusal), directory-key resolution (flag > file > default; output root from the shard flag only), `enumerate_matrix` + `apply_priority_order` composition with the zero-enumeration refusal BEFORE lock, singleton `dispatcher.lock` (O_EXCL, pid-liveness reclaim), `dispatch_state.json` mode evidence before any claim, frozen injective `claim_filename`, O_EXCL `claim_cell` (SC3), per-GPU worker threads with the verbatim static spawn discipline minus worker-root naming, CR-02 artifact-checked finalize, per-worker verdict table, no in-run requeue (A2)
- `pipeline/run_sweep_shard.py`: `--mode {static,dispatch}` flag (default static, English help) + main() routing — dispatch×merge combination refused by name before either mode runs (A6), lazy `dispatch_core` import (cycle break), static path byte-identical
- `tests/test_dispatch_core.py` (new, 29 tests): happy path (12 spawns, one shared root, zero `-mgpu-w{i}` siblings), state-before-spawn write-order pin, verbatim spawn-kwargs pin, workers-1 degenerate + not-model-bound + gpus-override, queue-order determinism (+priority threading), peft alias lane, validation refusals (variant×peft, missing `--seeds` code 2, empty `--models`, zero enumeration), lock family (live-pid refusal naming pid+run_id, dead-pid reclaim, malformed reclaim, static no-lock), `--help` surface, `--mode static` == default byte-identity, naming freezes, SC3 double-claim, and the SC2 kill test (run 1 one -9 cell → exit 1; relaunch re-dispatches EXACTLY that cell; every cell ends with exactly one artifact set; per-cell spawn counts 1/2)

## Task Commits

Each task was committed atomically:

1. **Task 1: Dispatch tracer — --mode routing + engine happy path** - `b44c6c2` (feat)
2. **Task 2: Resume semantics — skip filter, stale requeue, lock reclaim, SC2 kill test** - `e5ff382` (feat)

**Plan metadata:** (this commit — docs: complete plan)

## Verification Evidence

- `.venv/bin/python -m pytest tests/test_dispatch_core.py tests/test_sweep_shard.py -q` → **78 passed** (29 new dispatch + 49 pre-existing shard — the static-mode tripwire passed UNMODIFIED)
- `make lint` → "All checks passed!" (`tests/` wholesale covers the new test module; `pipeline/dispatch_core.py` also checked directly per the plan note — it joins PHASE13_MODULES only in Plan 13-02)
- `make typecheck` → "All checks passed!" (ty covers pipeline/)
- `git diff 13b1b4c..HEAD -- pipeline/run_sweep.py pipeline/run_finetune.py tests/test_sweep_shard.py Makefile .github/workflows/ci.yml` → **empty** (run_sweep/run_finetune byte-untouched, zero CI changes, zero Makefile changes)
- Tracer feedback gate (Task 1, type=tracer): `<verify>` re-run end-to-end green under `human_verify_mode: end-of-phase` + automated-only verify → expanded without a checkpoint

## Files Created/Modified
- `pipeline/dispatch_core.py` - the dispatch engine (new, ~1,010 lines): naming authorities, claim/lock protocol, skip filter, worker loops, `run_dispatch`
- `tests/test_dispatch_core.py` - the SC2/SC3 + happy-path + naming-freeze + validation-refusal + resume suites (new, 1,204 lines)
- `pipeline/run_sweep_shard.py` - `--mode` flag + mode routing + dispatch×merge guard (+34 lines; nothing else touched)

## Decisions Made
- Discretion items resolved per the plan's locked choices: sibling-module split (dispatch_core.py), frozen claim-filename scheme (percent-encoding + sha256[:12] digest suffix), threads-per-worker queue mechanics with per-cell scripted fakes
- `--models` is dispatch-mode-required (the WR-07 closure: full-registry dispatch must be an explicit run_sweep-side omission, never an orchestrator default)
- Worker tees open in the MAIN thread before threads start (an OSError refuses loudly with tees closed + lock released, mirroring the static spawn-loop failure handling); worker threads close their own tee in finally (SIM115 rationale, Pitfall 10)
- The state file's `skipped` count is written to disk after the skip filter and before any spawn (still before any claim — the crash-safety contract holds)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Refused `--mode dispatch` + `--dry-run` by name**
- **Found during:** Task 1 (engine entry)
- **Issue:** The plan leaves dispatch-mode `--dry-run` to Plan 13-02 (the dry-run plan artifact). `--dry-run` is a shard-owned flag, so it never lands in the remainder — without a guard, a dispatch launch carrying it would SILENTLY ignore the operator's dry-run expectation and spawn real training children (the silently-wrong-direction hazard this codebase refuses everywhere).
- **Fix:** Added a collect-all problem refusing the combination by name ("--dry-run dispatch planning lands with Plan 13-02 — refusing rather than spawning real children under a dry-run expectation"); Plan 13-02 replaces it with the planning artifact.
- **Files modified:** pipeline/dispatch_core.py
- **Verification:** covered by the collect-all path; all 78 tests green (no test yet pins this exact message — Plan 13-02's dry-run work supersedes it)
- **Committed in:** b44c6c2 (Task 1 commit)

**2. [Task-2 contract supersession] Task-1 lock test updated to the live-pid shape**
- **Found during:** Task 2 (lock reclaim)
- **Issue:** Task 1's `test_dispatch_lock_held_refuses_loudly` hand-wrote a lock with a dead pid (999999); once Task 2's pid-liveness reclaim lands, a dead-pid lock is RECLAIMED by design, so the old test's expectation would be wrong (it pinned the pre-reclaim shape, as the plan's Task 1 action explicitly staged: "the live-holder read arrives with Task 2's reclaim").
- **Fix:** Test rewritten to the Task-2 <behavior> contract: a LIVE pid (`os.getpid()`) refuses naming the pid + run_id + lock path; dead-pid reclaim has its own dedicated tests (reaped real subprocess pid + malformed lock).
- **Files modified:** tests/test_dispatch_core.py
- **Verification:** `test_dispatch_lock_live_pid_refuses_naming_holder`, `test_lock_dead_pid_is_reclaimed`, `test_lock_malformed_content_is_reclaimed` all green
- **Committed in:** e5ff382 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 missing critical [Rule 2], 1 planned Task-2 contract supersession)
**Impact on plan:** Both are correctness-preserving and plan-aligned. No scope creep.

## Issues Encountered
None - both tasks landed cleanly on the first verification pass (78/78, lint, typecheck).

## User Setup Required
None - no external service configuration required.

## Known Stubs
None - every code path is real; no placeholder/TODO/fixtures left behind.

## Next Phase Readiness
- Plan 13-02 (mode coexistence) can build on the `--mode` surface, the lazy-import routing, and the frozen `dispatch_state.json`/ledger evidence (its merge-evidence check reads exactly these artifacts); it also owns the Makefile `PHASE13_MODULES` lint-list line and the dispatch dry-run planning artifact that replaces this plan's named refusal
- Phase 14 consumes the ledger's lane flags + `dispatch_state.json` counts (MGPU-03/04) exactly as recorded at claim time
- Phase 15's N=2 real-GPU smoke launches `--mode dispatch --workers 2 --gpus 0,1` unchanged

## Self-Check: PASSED

- pipeline/dispatch_core.py — FOUND
- tests/test_dispatch_core.py — FOUND
- .planning/phases/13-dynamic-dispatch-core/13-01-SUMMARY.md — FOUND
- Task 1 commit b44c6c2 — FOUND (ancestor of HEAD)
- Task 2 commit e5ff382 — FOUND (ancestor of HEAD)
- commits measured from the ledger: `git rev-list --count 13b1b4c..HEAD` = 2 (matches `actuals.commits`)

---
*Phase: 13-dynamic-dispatch-core*
*Completed: 2026-10-20*
