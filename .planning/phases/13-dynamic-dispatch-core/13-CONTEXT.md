---
phase: 13-dynamic-dispatch-core
title: 动态调度核心 (Dynamic Dispatch Core)
status: approved
created: 2026-10-20
---

# Phase 13: 动态调度核心 - Context

**Gathered:** 2026-10-20
**Status:** Ready for planning

<domain>
## Phase Boundary

The orchestrator (`pipeline/run_sweep_shard.py`) gains a dispatch mode: a single
dispatcher process owns a deterministic (model×dataset×seed) cell queue and feeds
idle per-GPU workers, each cell running entirely on exactly one GPU via the frozen
child argv surface. Cell outputs land at worker-independent paths under ONE shared
root guarded by an exactly-once O_EXCL claim ledger, with resume semantics proven
under mid-cell kill via fake children. Legacy static-shard mode coexists behind an
explicit mode declaration. State-file rendering, failure re-run, and cleanup are
Phase 14; GPU validation is Phase 15.

</domain>

<decisions>
## Implementation Decisions

### Worker Process Shape
- **D13-01:** Thin per-GPU worker loop owned by the dispatcher: claim cell → spawn one child per cell → wait → record → claim next (research Shape 1; run_sweep stays the single-sweep authority, run_finetune argv surface untouched)
- **D13-02:** Child argv built by importing `run_sweep.build_argv()` verbatim — orchestrator composes, never re-implements (D-07 discipline)
- **D13-03:** Cell enumeration via `run_sweep.enumerate_matrix` unchanged; priority tiers reapplied for queue order
- **D13-04:** Single dispatcher owns an in-memory queue; idle workers pull the next cell (no cost-prediction — explicitly out of scope)

### Mode Declaration & CLI Grammar (MGPU-06)
- **D13-05:** Explicit `--mode {static,dispatch}` on `run_sweep_shard.py`, default `static`; legacy static launch stays byte-identical (test-pinned)
- **D13-06:** Dispatch mode writes ONE shared root with ordinary per-cell subpaths (`{root}/{model}/{task}/seed{k}`) — worker-independent; `--merge` refuses dispatch-mode roots with a named "dispatch roots need no merge" error; static merge untouched
- **D13-07:** Mode is recorded by the run (dispatch state / manifest marker) so refusal is evidence-based, never inferred from directory shape
- **D13-08:** Help text in English, matching the run_sweep/run_sweep_shard CLI convention (D-10)

### Claim Ledger & Resume (MGPU-02)
- **D13-09:** Per-cell claim file via `os.open(O_CREAT|O_EXCL)` in a dispatch ledger dir inside the shared root (tee O_EXCL precedent); JSON content: cell key, lane flags, gpu, pid, run_id, timestamps
- **D13-10:** Child `trainer_state.json` marker stays the authoritative completion guard; the dispatcher additionally skips ledger-completed cells on relaunch (D-06 two-layer guard extended)
- **D13-11:** Singleton dispatcher lock per root (O_EXCL): a second orchestrator on the same root is refused loudly; stale claims from a dead run are reclaimable precisely because no second dispatcher can exist — no lease/timeout protocol
- **D13-12:** Worker death mid-cell ⇒ claim is unfinished ⇒ relaunch requeues it; exactly-once (no duplicates, no orphans) is proven by the fake-children kill test (SC2 — the P1 acceptance test)

### Testing & CI Shape (SC1/SC2/SC5)
- **D13-13:** Kill-test harness uses fake children through the existing `main(spawner=...)` seam: scripted exits incl. SIGKILL mid-cell; assertions read the ledger + artifact counts
- **D13-14:** Dry-run enumeration committed as a golden: byte-identical across runs AND equal to static-mode enumeration for identical inputs
- **D13-15:** CI stays CPU-only: no GPU, no dnallm, no N>1 device assumptions anywhere; fake children + injected seams only
- **D13-16:** Full CPU gates stay green (pytest/ruff/ty + node lanes); zero CI changes; new code keeps the stdlib-headless contract

### Claude's Discretion
- Internal module split inside `run_sweep_shard.py` vs a new sibling module (e.g. `dispatch_core.py`) — follow the existing compose-as-sibling-modules pattern and file-size ergonomics
- Exact ledger directory name/layout and claim-file naming, provided O_EXCL semantics and the frozen naming tests cover it
- Queue hand-off mechanics (in-process thread vs select loop over Popen handles) as long as single-dispatcher semantics hold

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pipeline/run_sweep_shard.py` (1252 lines): launch + merge modes; injectable `main(spawner=None, clock=None)` seam and `_DEFAULT_SPAWNER = subprocess.Popen`; `worker_root()` naming authority; `MERGE_ALLOWLIST`; lane-signature equality refusal; frozen-root collision collect-all refusal pattern
- `pipeline/run_sweep.py` (1964 lines): `enumerate_matrix`, `build_argv`, `launch_subprocess`, `cell_dir_for`, `load_failure_pairs`, `apply_priority_order`, manifest recording (D-13 present-flags-only)
- `pipeline/run_finetune.py`: `trainer_state.json` resume marker per cell (D-06 authority)
- `tests/test_sweep_shard.py`: LPT disjointness/determinism, worker argv/spawn kwargs, frozen naming, merge lane refusals, dry-run subprocess chain — the suite dispatch mode must not weaken

### Established Patterns
- Orchestrator COMPOSES: imports `run_sweep` / `registry_loader` as sibling modules, never re-implements enumeration/argv/validation (D-07)
- Collect-all problem reporting with named errors and nonzero exit; per-worker tee logs with timestamps; `start_new_session=True` process groups; `CUDA_VISIBLE_DEVICES` pinning per worker
- Atomic JSON writes (single-writer) and O_EXCL create-or-refuse as structural guards
- Stdlib-headless contract: pipeline orchestration code imports no GPU/torch at module top; CI never assumes N>1 devices

### Integration Points
- `run_sweep_shard.parse_args()` gains the mode surface; `main()` dispatches to static (existing path, byte-identical) vs dispatch runner
- Dispatch state file (`{root}/dispatch_state.json`) is created here minimally (queue/claims ground truth) and gains the live-view contract in Phase 14 (MGPU-03)
- Failure ledger content (lane flags at claim time) is the Phase 14 `--from-failures` union re-run feed (MGPU-04)

</code_context>

<specifics>
- Research `.planning/research/ARCHITECTURE.md` §A is the design backbone (HIGH confidence, integration points verified against live code)
- Build order pinned by research: dispatch core first — everything else consumes its state/ledger
- Binding constraints: legacy static-shard mode coexists (2026-10-20 ruling); leaderboard numbers move only through zero-drift-proven additive changes; DNALLM suite repo read-only

</specifics>

<deferred>
- Live terminal table + `dispatch_state.json` consumer contract → Phase 14 (MGPU-03)
- Cross-worker failure re-run + post-merge verify/cleanup helper → Phase 14 (MGPU-04/05)
- N=2 real-GPU smoke + subsets → Phase 15 (VAL)

</deferred>
