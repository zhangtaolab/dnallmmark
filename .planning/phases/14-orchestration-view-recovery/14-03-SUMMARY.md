---
phase: 14-orchestration-view-recovery
plan: 03
subsystem: pipeline
tags: [dispatch, failure-recovery, rerun, genealogy, lane-replay, mgpu]

requires:
  - phase: 13-dynamic-dispatch-core
    provides: "dispatch_core.py claim ledger with lane flags at claim time, relaunch_decision marker/claim layers, _spawn_worker claim-before-spawn, the fake-children harness"
  - phase: 14-orchestration-view-recovery
    provides: "wave-1 dispatch_state.json schema v2 + _publish_state/_write_state choke point (the re-run renders through it); run_sweep_shard main() A6 combo-refusal + sibling-mode routing precedent"
provides:
  - "run_sweep_shard.py --rerun-failed — the orchestrator-owned MGPU-04 flag (implies dispatch mode; one command re-runs the ledger's failed cells across ALL prior runs on the root)"
  - "claim-time lane dict completeness: cache_dir (the D14-06 gap) + model_root/dataset_root/log_dir (A8) recorded and replayed verbatim through build_argv (tolerant absent-parity reads)"
  - "archive_superseded_claim + rerun_of genealogy (Option C): originals preserved verbatim O_EXCL under dispatch_ledger/archive/, canonical slot atomically replaced with the fresh claim carrying the link"
  - "the re-run branch: tolerant ledger scan, base_model_name registry join, _canonical_lane_value homogeneity refusal (per flag per cell), marker-vs-failed precedence, zero-failed verdict exit 0, forbidden-token passthrough validation"
affects: [15-validation (VAL-03 real sweep recovery uses --rerun-failed), docs/multi-gpu.md runbook (re-run command now exists — doc update is later scope), 16-TUI (slot-5 re-run affordance can shell out to the flag)]

actuals:
  tokens: 18936   # 75744 diff chars / 4 over pipeline/dispatch_core.py, pipeline/run_sweep_shard.py, tests/test_dispatch_core.py (estimate: 18000)
  tasks: 2
  commits: 3      # measured 171584e..5815797 (Task 1 RED + Task 1 GREEN + Task 2 matrix/fixes)

plan_head_before: 171584ef8da6225660e95d2e5b74f6383788ab54e
plan_head_after: 5815797a236b85408bce0c5a6d9466677561945b

tech-stack:
  added: []        # stdlib only over existing modules (T-14-SC: zero installs)
  patterns:
    - "union-key lane-signature normalization: absent == None projected onto the union of lane keys — the Pitfall 4 absent-parity discipline extended from replay to COMPARISON (an old-shape and new-shape lane with equal values are ONE lane)"
    - "pre-launch named refusal over the same state the structural guard protects (archive collisions refuse by name before any spawn; the worker's O_EXCL create stays the T-14-06 backstop)"
    - "GPU-token-keyed first-cell failure injection: which worker pops which cell races with thread scheduling, so per-worker failures key on the worker's permanent CUDA_VISIBLE_DEVICES token, not the cell"

key-files:
  created: []
  modified: [pipeline/dispatch_core.py, pipeline/run_sweep_shard.py, tests/test_dispatch_core.py]

key-decisions:
  - "Genealogy per the Q1 ruling (Option C): archive_superseded_claim copies the ORIGINAL payload verbatim to dispatch_ledger/archive/{claim stem}--run-{original run_id[:8]}.json (O_CREAT|O_EXCL, the claim_cell no-follow guarantee, T-14-06); the archive name is keyed by the ORIGINAL attempt's run_id so it is injective across attempts (a re-run of a re-run archives under the re-run's own run_id); the fresh claim lands in the canonical slot via tmp+os.replace carrying rerun_of {archive, run_id, claimed_at} — the exact JSON shape the plan froze"
  - "The archive/ SUBDIRECTORY keeps every invariant: ledger scans glob *.json NON-recursively, so the canonical slot keeps its O(1) read_claim meaning and archive files never mix into the failed-claim scan"
  - "The re-run branch sits in run_dispatch AFTER the --workers/--gpus validation but BEFORE the --models requirement and WITHOUT parse_sweep_remainder (Pitfall 7): the failed claims define models AND seeds; the raw passthrough accepts only --registry-dir (space and equals form) — scoping tokens get the D14-05 double-scope wording, lane tokens the D14-06 replay wording, unknown tokens refuse generically (T-14-08)"
  - "The SC3 silent skip is structurally unreachable for rerun-tagged cells: on the EEXIST knot (Pitfall 1) the worker archives + replaces; an EEXIST whose original read yields nothing usable raises into the CR-04 containment (loud per-cell failure, exit 1), never a skip"
  - "run_dispatch tail extracted to _launch_and_drain shared by both entry paths — the ordinary path's render progression is preserved exactly (skip filter still runs AFTER the mode-evidence write; 66 baseline tests green unmodified)"
  - "Explicit --mode static detection scans raw sys.argv tokens (static is also the parser DEFAULT — an implicit static must not refuse); --rerun-failed x --cleanup added to the A6 combo family so mode routing stays deterministic (the plan listed four combos; cleanup closes the hole the cleanup block's earlier return would otherwise leave)"

patterns-established:
  - "Deterministic per-worker failure injection under a racy pop: key the scripted failure on the worker's permanent GPU token (structural) instead of the cell (scheduling-dependent)"
  - "Content-verbatim vs byte-verbatim archive assertions: run-produced claims archive byte-identical (both written through _dump_json_handle); hand fixtures assert parsed-equality because the fixture's compact serialization re-canonicalizes through the ledger writer"

requirements-completed: [MGPU-04]

coverage:
  - id: D1
    description: "ONE --rerun-failed command re-runs exactly the ledger's failed cells across workers; healthy/completed cells never re-spawned; lane flags replay verbatim (D14-15 fixture)"
    requirement: MGPU-04
    verification:
      - kind: integration
        ref: "tests/test_dispatch_core.py#test_rerun_failed_d14_15_two_worker_fixture"
        status: pass
  - id: D2
    description: "Original failed claims preserved verbatim under dispatch_ledger/archive/ with rerun_of links back from the fresh claims (D14-07); archiving twice refuses (append-only)"
    requirement: MGPU-04
    verification:
      - kind: unit
        ref: "tests/test_dispatch_core.py#test_rerun_failed_d14_15_two_worker_fixture (byte-identical archive + rerun_of pins) + #test_rerun_archive_collision_refuses_loudly + #test_rerun_stale_pre_phase14_claim_replays_absent_parity (genealogy over a stale original)"
        status: pass
  - id: D3
    description: "Refusal matrix: heterogeneous lanes per-flag per-cell (D14-08), every forbidden passthrough token class, 5 combo refusals before any ledger work, unknown-registry refusal, zero-failed verdict exit 0, marker-precedence skip"
    requirement: MGPU-04
    verification:
      - kind: unit
        ref: "tests/test_dispatch_core.py#test_rerun_refuses_heterogeneous_lanes_naming_flag_and_cells, #test_rerun_refuses_every_forbidden_passthrough_token (14 cases), #test_rerun_combo_refusals_fire_before_any_ledger_work (5 cases), #test_rerun_refuses_unknown_registry_model_loudly, #test_rerun_zero_failed_verdict_with_registry_dir_accepted, #test_rerun_skips_failed_cell_that_gained_the_marker"
        status: pass
  - id: D4
    description: "Stale pre-Phase-14 claims replay with absent-parity argv (no cache_dir key = zero argv elements, never a KeyError/refusal); old/new lane shapes with equal values are one lane"
    requirement: MGPU-04
    verification:
      - kind: unit
        ref: "tests/test_dispatch_core.py#test_rerun_stale_pre_phase14_claim_replays_absent_parity + #test_rerun_old_and_new_lane_shapes_with_equal_values_are_one_lane"
        status: pass
  - id: D5
    description: "Static mode byte-identical, zero CI/Makefile changes, stdlib-headless held (D14-16)"
    requirement: MGPU-04
    verification:
      - kind: unit
        ref: "tests/test_dispatch_core.py static pins (test_mode_static_explicit_matches_default + test_static_mode_explicit_pins_argv_roots_and_logs: 2 passed)"
        status: pass
      - kind: other
        ref: "make lint && make typecheck (All checks passed); node --test tests/js/*.test.js (26/26); git hash-object .github/workflows/ci.yml == 33d2252eb594e0faecece9e8015a332d8d6479ef; git status --porcelain Makefile empty"
        status: pass

metrics:
  duration: 18 min wall
  completed: 2026-10-20

status: complete
---

# Phase 14 Plan 03: Cross-worker failure re-run (--rerun-failed) Summary

Landed MGPU-04: one orchestrator-owned `--rerun-failed` command re-runs the union of the ledger's failed cells with claim-time lane flags replayed verbatim (the 12-04 lane-blindness fix), preserving audit history via archive + `rerun_of` genealogy (Option C) and refusing heterogeneous lanes, double-scoping, and forbidden tokens by name.

## Commits

| Task | Commit | Files |
| ---- | ------ | ----- |
| Task 1 RED: failing D14-15 e2e fixture | 97283de | tests/test_dispatch_core.py |
| Task 1 GREEN: lane completeness + genealogy + re-run branch + flag/routing | 67a64aa | pipeline/dispatch_core.py, pipeline/run_sweep_shard.py, tests/test_dispatch_core.py |
| Task 2: refusal matrix + stale-claim tolerance + archive pre-check | 5815797 | pipeline/dispatch_core.py, tests/test_dispatch_core.py |

## What Was Built

### Task 1 — lane completeness + genealogy + the re-run engine (tracer, TDD)

- **RED** (97283de): the D14-15 e2e fixture. Run 1 (existing machinery) proved
  sound on its own — 8 cells over 2 workers with lane flags
  (`--peft lora`, `--num_train_epochs 1`, `--cache_dir`), exactly one
  structural failure per worker; the `--rerun-failed` launch then died at
  the static path's `--models is required for launch mode` because the
  flag did not exist (the same feature-absent RED shape 14-02 recorded
  for `--dry-run`; run 1 fully green proves the fixture itself).
- **(A) Lane completeness (D14-06 + A8):** `context["lane"]` (now the
  shared `lane_values` dict) gains `cache_dir` plus `model_root` /
  `dataset_root` / `log_dir` — recorded at claim time into every new
  claim, replayed tolerantly.
- **(B) Genealogy (Q1 = Option C):** `archive_superseded_claim`
  O_EXCL-copies the original failed payload VERBATIM to
  `dispatch_ledger/archive/{stem}--run-{run_id[:8]}.json`
  (`_archive_filename` is the one frozen naming helper, shared with the
  pre-check); EEXIST refuses (append-only); the fresh claim then lands
  in the canonical slot via tmp+`os.replace` carrying
  `rerun_of = {archive, run_id, claimed_at}`.
- **(C/D) Flag + routing (Q3):** `--rerun-failed` (store_true) on the
  SHARD parser — orchestrator-owned vocabulary that can never collide
  with run_sweep's passthrough `--from-failures`. `main()` routes it
  into `run_dispatch` with A6-shape combo refusals (merge, explicit
  `--mode static` via a raw-token scan since static is the default,
  dry-run, models, cleanup).
- **(E) Ledger scan:** sorted non-recursive `*.json` glob minus the
  lock; corrupt claims contribute nothing (tolerant read, never
  trusted); a claim qualifies iff `state: failed` AND its cell key
  rebuilds AND matches `claim_filename`. Registry join maps every
  failed cell through `base_model_name` with its OWN claim lane (the
  CR-01 discipline, not the manifest reader). Zero qualified cells →
  explicit no-failed-cells verdict, exit 0 (A7), nothing touched.
- **(F) Homogeneity (D14-08):** lane signature = the claim lane minus
  `train_fraction`, canonicalized via `run_sweep_shard
  ._canonical_lane_value`, compared over the UNION of lane keys with
  absent == None projection; more than one distinct signature refuses
  naming, per cell, each differing flag and its value (the run_merge
  shape).
- **(G) Replay:** the worker claim step gains the `rerun` tag:
  `claim_cell` first (genuinely-fresh case); on EEXIST (the Pitfall 1
  knot) read the original → archive → write the fresh claim with
  `rerun_of`; an unusable original raises into the CR-04 containment
  (loud cell failure + exit 1) — the SC3 silent skip is unreachable
  for rerun cells. Spawn replays through the existing `build_argv`
  with tolerant `lane.get()` reads (absent key = zero argv elements).
  The `run_dispatch` tail was extracted to `_launch_and_drain`, shared
  by both entry paths (the ordinary path's render progression is
  unchanged — the skip filter still runs after the mode-evidence
  write).
- **(H) The e2e proves:** exactly the two failed cells re-run;
  byte-identical child argv per re-run cell (verifiable lane replay);
  healthy cells never re-spawned and their claims still carry run-1's
  run_id; originals byte-identical under `archive/`; fresh claims
  completed with correct `rerun_of`; final state schema-valid with
  `counts.total == 2, skipped == 0`; lock released; no tmp residue.

### Task 2 — refusal matrix + stale-claim tolerance + gates

- **RED observed (3 failing)** before the fixes:
  1. old/new lane shapes with equal values hit an EMPTY
     heterogeneous-lane refusal (signature groups differed on
     absent-vs-None keys while no per-flag diff was reportable) — a
     genuine Rule-1 production bug;
  2. the archive collision drained into an unnamed exit 1 (no named
     pre-launch refusal existed);
  3. the stale-claim test's verbatim assert compared a hand fixture's
     compact serialization against the canonical archive writer (a
     TEST bug — run-produced claims archive byte-identical, hand
     fixtures are content-verbatim).
- **Rule 1 fix:** homogeneity compares over the union of lane keys with
  absent == None projection — the Pitfall 4 absent-parity discipline
  extended from replay to comparison (pinned by
  `test_rerun_old_and_new_lane_shapes_with_equal_values_are_one_lane`).
- **Archive-collision pre-check:** `_run_rerun_failed` refuses BY NAME
  (collect-all) when the archive for an original attempt already
  exists while the canonical slot still names the same run_id — before
  any spawn; the worker's O_EXCL create remains the structural backstop.
- **Matrix (20 new tests):** heterogeneous-lane per-cell per-flag
  refusal; 14 forbidden-token cases (scoping/lane/unknown classes, the
  `--registry-dir` value-required edge); 5 combo refusals before any
  ledger work; zero-failed verdict with `--registry-dir` accepted;
  marker-precedence skip (`counts.skipped == 1`, nothing spawned);
  stale pre-Phase-14 claim absent-parity replay (argv equals
  `build_argv(..., cache_dir=None, ...)` exactly, genealogy still
  applies); unknown-registry model refusal naming the model.

## Verification Evidence

- `.venv/bin/python -m pytest tests/test_dispatch_core.py -q` → **93
  passed** (66 baseline + 27 new; every baseline test green unmodified
  through the `_launch_and_drain` extraction).
- `.venv/bin/python -m pytest tests/test_dispatch_core.py
  tests/test_sweep_shard.py -q` → **155 passed** (parser/routing
  regressions: none).
- `.venv/bin/python -m pytest tests/test_export_runs.py -q -k "not
  d15"` → **28 passed, 1 deselected** (the d15 leg is the pre-existing
  offline `evaluate.load("pearsonr")` network hang documented in
  14-02-SUMMARY and already recorded in the WINDOWS ledger — unchanged
  by this plan; the plan's verify lane for this suite runs with the
  documented exclusion).
- `make lint` / `make typecheck` → All checks passed.
- `node --test tests/js/*.test.js` → 26/26 pass, 0 fail.
- `git hash-object .github/workflows/ci.yml` →
  `33d2252eb594e0faecece9e8015a332d8d6479ef` (byte-identical);
  `git status --porcelain Makefile` → empty (renderer/re-run stayed
  inside dispatch_core.py per Q6 — no new sibling module).
- Acceptance greps: `rerun_of` x5 in pipeline/dispatch_core.py (>= 2),
  `"--rerun-failed"` x1 in pipeline/run_sweep_shard.py (>= 1),
  `"cache_dir"` x6 in pipeline/dispatch_core.py (>= 5).
- Tracer feedback gate: full dispatch suite re-run end-to-end after the
  tracer commit — 67/67 green before Task 2 expanded.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Empty heterogeneous-lane refusal on absent-vs-None lane keys**
- **Found during:** Task 2 (RED observation, anticipated by comparing the implementation against Pitfall 4)
- **Issue:** Signature groups keyed on the RAW lane dict treated `{peft: lora, ...}` and `{peft: lora, ..., cache_dir: None, ...}` as different signatures, but the per-flag diff saw `get(cache_dir)` → None for both — refusal fired with an EMPTY problem list (`[Error] `). A Phase-13 failed claim beside a Phase-14 failed claim with equal effective lanes would have refused with no diagnostic.
- **Fix:** Union-key normalization — every lane projects onto the union of lane keys with `lane.get(key)` before canonicalization (absent == None, matching replay semantics). Pinned by `test_rerun_old_and_new_lane_shapes_with_equal_values_are_one_lane`.
- **Files modified:** pipeline/dispatch_core.py
- **Commit:** 5815797

**2. [Rule 2 - Missing correctness guard] Archive collisions lacked a named pre-launch refusal**
- **Found during:** Task 2 (RED observation)
- **Issue:** The O_EXCL archive create lives inside the worker thread; a pre-existing archive surfaced only as an unnamed containment failure (exit 1 with no reason a operator can read — the failed claim's error field never records it because the worker owns no claim path at that point).
- **Fix:** Collect-all pre-check in `_run_rerun_failed` refusing BY NAME (cell, run prefix, archive path, D14-07 rationale) before any spawn; the worker's O_EXCL remains the structural backstop (T-14-06). Pinned by `test_rerun_archive_collision_refuses_loudly`.
- **Files modified:** pipeline/dispatch_core.py
- **Commit:** 5815797

**3. [Rule 1 - test bug] Hand-fixture verbatim assertion compared serializations**
- **Found during:** Task 2 (RED observation)
- **Issue:** The stale-claim test asserted byte-identity between a hand-written compact-JSON fixture and the archive copy, which re-canonicalizes through `_dump_json_handle`. Run-produced claims ARE byte-identical (both written canonically — pinned in the e2e); hand fixtures cannot be.
- **Fix:** Parsed-equality for hand fixtures (content-verbatim), with the distinction documented inline.
- **Files modified:** tests/test_dispatch_core.py
- **Commit:** 5815797

### Plan-text additions (within the plan's own families, noted for review)

- `--rerun-failed x --cleanup` joined the A6 combo refusals (the plan
  listed merge/mode-static/dry-run/models; without it the earlier
  cleanup block would run cleanup and silently ignore the re-run —
  mode routing must be deterministic).
- The zero-failed verdict prints before the registry join (identical
  behavior — `_validate_filters` over empty sets is a no-op — but a
  healthy root never loads registries).

## Auth Gates

None.

## State-Update Notes

`roadmap.update-plan-progress 14` returned `missing_phase_details`
(this ROADMAP uses checkbox plan lists); the Phase 14 wave-2 checkbox
was updated by hand in the Phase 13/14-01 convention. All other
handlers (advance-plan, update-progress, record-metric, add-decision
x3, record-session, requirements.mark-complete MGPU-04) applied
cleanly.

## Known Stubs

None — every refusal path, the genealogy, and the replay are real
behavior exercised by tests; no mocks beyond the injected spawner/clock
seams the harness specifies.

## Threat Flags

None — no surface beyond the plan's threat model. T-14-06 (archive
tampering) mitigated by the O_EXCL no-follow create + EEXIST refusal +
the named pre-check, all pinned; T-14-07 (forged claims) mitigated by
the registry join + tolerant reads + the cell-key/filename integrity
check; T-14-08 (command-line blending) mitigated by the
forbidden-token scan (14 pinned cases); T-14-SC held (zero installs).

## Self-Check: PASSED

- Files exist: pipeline/dispatch_core.py, pipeline/run_sweep_shard.py,
  tests/test_dispatch_core.py — FOUND
- Commits are ancestors of HEAD: 97283de, 67a64aa, 5815797 — FOUND
