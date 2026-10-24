---
phase: 14-orchestration-view-recovery
plan: 01
subsystem: pipeline
tags: [dispatch, observability, json-schema, pty, pexpect, flush, gen-progress]

requires:
  - phase: 13-dynamic-dispatch-core
    provides: "dispatch_core.py single-writer engine — _write_state choke point, claim ledger with lane flags, per-GPU worker loops, 53-test fake-children harness"
provides:
  - "dispatch_state.json schema v2 (DISPATCH_STATE_SCHEMA_VERSION 2) with additive queue_depth / workers[] / failures consumer fields"
  - "schemas/dispatch_state.json — the frozen v2 consumer contract (draft 2020-12, strict, jsonschema-validated against real fake-run state files)"
  - "_render_state plain-line renderer hooked at the _write_state choke point (render under state_lock, flush=True, output-error containment)"
  - "Claim-time state write — the 8th _write_state call site making in-flight cells visible while children train"
  - "Pty + pipe flush lanes proving the live table survives real-terminal and block-buffered-stdout conditions"
affects: [14-02, 14-03, 16-TUI-slot5, gen-progress, MGPU-04 rerun (reads v2 state)]

actuals:
  tokens: 13800   # 55213 diff chars / 4 over pipeline/, schemas/, tests/ (estimate: 17000)
  tasks: 3
  commits: 4      # measured ca56b95..HEAD — includes the orchestrator's pause-handoff docs commit 60c223d

plan_head_before: ca56b958a967118999a217e401bf573595d00b4e
plan_head_after: 7fb7424b96ff02c2dca26f267ff34b5762134f47

tech-stack:
  added: []        # stdlib + existing dev-group jsonschema/pexpect only (T-14-SC: zero installs)
  patterns:
    - "renderer at the single _write_state choke point rendering the exact frozen payload (never context internals)"
    - "derived queue_depth under one lock — total - completed - failed - skipped - in_flight_count keeps the snapshot identity true at every write"
    - "driver-script pty lane: real drain as a real subprocess over fake children whose first cell holds, so a 3s read window can only be satisfied by a LIVE render"

key-files:
  created: [schemas/dispatch_state.json]
  modified: [pipeline/dispatch_core.py, tests/test_dispatch_core.py]

key-decisions:
  - "queue_depth is DERIVED at publish time inside state_lock (not a len(pending) read across two locks) — the Pitfall 3 consistent-snapshot ruling, identity pinned by test"
  - "Renderer lives inside dispatch_core.py per Q6 — zero Makefile change, ci.yml byte-identical (hash 33d2252eb594e0faecece9e8015a332d8d6479ef re-verified)"
  - "failures is a bounded list of compact {model, task, seed, fraction, finished_at} entries (Q2 ruling) describing the CURRENT run only"
  - "pty exitstatus is reaped via child.close() after expect(EOF) — expect alone leaves exitstatus None (pexpect contract; driver verified exit 0 standalone first)"

patterns-established:
  - "Frozen consumer schema + jsonschema consumer test riding the same commit as the writer change (D14-04 discipline)"
  - "Pipe-leg flush proof without PYTHONUNBUFFERED: the spawned env explicitly strips it so a preset unbuffered env cannot pass trivially"

requirements-completed: [MGPU-03]

coverage:
  - id: D1
    description: "dispatch_state.json is schema v2, validates against the committed frozen schema, carries queue_depth/workers/failures"
    requirement: MGPU-03
    verification:
      - kind: unit
        ref: "tests/test_dispatch_core.py#test_dispatch_state_validates_against_frozen_v2_schema"
        status: pass
      - kind: unit
        ref: "tests/test_dispatch_core.py#test_dispatch_state_failures_view_names_failed_cells"
        status: pass
      - kind: unit
        ref: "tests/test_dispatch_core.py#test_dispatch_state_worker_rows_match_gpus_and_sum_to_counts"
        status: pass
  - id: D2
    description: "Live plain-line table renders on every state write including claims; output errors never fail cells"
    requirement: MGPU-03
    verification:
      - kind: unit
        ref: "tests/test_dispatch_core.py#test_renderer_renders_every_step_of_a_healthy_run"
        status: pass
      - kind: unit
        ref: "tests/test_dispatch_core.py#test_claim_time_row_visible_while_child_runs"
        status: pass
      - kind: unit
        ref: "tests/test_dispatch_core.py#test_queue_depth_identity_holds_at_every_state_write"
        status: pass
      - kind: unit
        ref: "tests/test_dispatch_core.py#test_renderer_broken_pipe_never_fails_cells"
        status: pass
  - id: D3
    description: "First [Dispatch] row observable live under a real pty and through a block-buffered pipe"
    requirement: MGPU-03
    verification:
      - kind: integration
        ref: "tests/test_dispatch_core.py#test_first_dispatch_row_arrives_live_under_a_real_pty"
        status: pass
      - kind: integration
        ref: "tests/test_dispatch_core.py#test_first_dispatch_row_arrives_live_through_a_pipe"
        status: pass
  - id: D4
    description: "gen_progress keeps parsing over a fixture tree carrying a v2 dispatch root (D14-04 keep-parsing)"
    requirement: MGPU-03
    verification:
      - kind: unit
        ref: "tests/test_dispatch_core.py#test_gen_progress_still_parses_over_a_v2_dispatch_root"
        status: pass
  - id: D5
    description: "Static mode byte-identical, lint/typecheck green, zero CI/Makefile changes (D14-16)"
    requirement: MGPU-03
    verification:
      - kind: unit
        ref: "tests/test_dispatch_core.py#test_mode_static_explicit_matches_default + test_static_mode_explicit_pins_argv_roots_and_logs (2 passed)"
        status: pass
      - kind: other
        ref: "make lint && make typecheck (All checks passed)"
        status: pass
      - kind: other
        ref: "git hash-object .github/workflows/ci.yml == 33d2252eb594e0faecece9e8015a332d8d6479ef; git status --porcelain Makefile empty"
        status: pass

metrics:
  duration: 24 min wall (interrupted by an API usage cap mid-Task-3; resumed same hour from .continue-here.md)
  completed: 2026-10-20

status: complete
---

# Phase 14 Plan 01: Frozen dispatch state v2 + live plain-line table Summary

Extended Phase 13's `dispatch_state.json` into the MGPU-03 consumer contract (schema v2: derived `queue_depth`, per-worker `workers[]` with in-flight cells, bounded `failures` list) and rendered a live `[Dispatch]` plain-line table at the `_write_state` choke point with a claim-time write — proven live under a real pty and through a block-buffered pipe.

## Commits

| Task | Commit | Files |
| ---- | ------ | ----- |
| Task 1: state v2 payload + frozen schema + consumer tests | a3adc3f | pipeline/dispatch_core.py, schemas/dispatch_state.json (new), tests/test_dispatch_core.py |
| Task 2: plain-line renderer at _write_state + claim-time write | c837102 | pipeline/dispatch_core.py, tests/test_dispatch_core.py |
| Task 3: pty flush lane + pipe leg + gen_progress keep-parsing | 7fb7424 | tests/test_dispatch_core.py |

(`commits: 4` in frontmatter is the measured ledger range and also includes
`60c223d` — the orchestrator's pause-handoff docs commit written when the usage
cap interrupted the first run; it touched only `.continue-here.md`.)

## What Was Built

### Task 1 — state v2 payload + frozen schema + consumer test (tracer)

- `DISPATCH_STATE_SCHEMA_VERSION` 1 → 2; every v1 key unchanged.
- `queue_depth` is DERIVED at publish time under `state_lock`
  (`total - completed - failed - skipped - in_flight_count`), not read as
  `len(pending)` across the two locks — the Pitfall 3 consistent-snapshot
  ruling; the pop-to-claim window is counted as in-flight by construction
  (the slot is set before the claim-time write).
- `workers[]`: one `{index, gpu, in_flight, cells, completed, failed}` entry
  per `--workers` index; `in_flight` maintained in `context["in_flight"]`
  (set on successful claim, cleared in the finalize critical section).
- `failures[]`: appended at finalize only on failure, compact
  `{model, task, seed, fraction, finished_at}` entries (fraction null when
  the cell has none); growth bound documented in the schema `$comment`.
- `schemas/dispatch_state.json` committed in the same change: draft 2020-12,
  `$id` following the repo raw.githubusercontent pattern,
  `additionalProperties: false`, `schema_version` const 2, status enum
  running|done|incomplete, the snapshot-identity invariant in `$comment`.
- Consumer tests (D14-14): two-worker fake run with one injected `exit_for`
  failure → the resulting state validates against the schema, reports v2,
  names the failed cell in `failures` with a `finished_at` stamp, worker rows
  match `--gpus` and sum to counts, final `queue_depth == 0` with all
  in-flight null.

### Task 2 — renderer at the choke point + claim-time write

- `_render_state(state)`: one `[Dispatch] status=... queue=... done=.../...
  failed=... skipped=...` header plus one `  w{i} gpu={gpu}: {cell}` row per
  worker (`-` when idle, `/frac_{f}` appended for fraction cells) — every
  print `flush=True`.
- Hooked inside `_write_state` AFTER `_atomic_write_json`, so it renders the
  exact frozen payload just written, under the caller's `state_lock` — never
  `context` internals (the anti-pattern).
- Render body guarded: BrokenPipeError/OSError swallowed best-effort — a
  dying consumer view cannot fail a cell or kill a worker thread (T-14-01).
- The 8th `_write_state` call site: in the worker claim step, after
  `claim_cell` succeeds and before the spawn, the in-flight slot is set and
  state is written (D14-03 — the cell shows while the child trains).
- 7 capsys tests over scripted fake-children sequences: step-by-step header
  progression, claim-time row visibility while a gated spawner blocks,
  failed-finalize rendering, the queue-depth identity at every observed
  state write, monkeypatched-output-error containment, and the incomplete
  containment path's honest status.

### Task 3 — pty flush lane + pipe leg + gen_progress keep-parsing (verification legs)

- **pty lane (D14-13 / research A6):** a temp driver script (bootstraps
  `pipeline/` onto `sys.path`, installs a fake child spawner whose FIRST cell
  `wait()` holds 5s, drives `run_dispatch --workers 2` over 2 cells) is
  spawned by pexpect under a REAL pty. The first `[Dispatch]
  status=running queue=2` header must arrive within 3s — only a LIVE render
  can satisfy that window (a block-buffered stream would emit nothing until
  exit). Then the claim-time view `queue=0 done=0/2`, the terminal
  `status=done queue=0 done=2/2` table, EOF, and exitstatus 0 via the
  pexpect close()-reap contract; the final state file validates against the
  frozen v2 schema.
- **pipe leg:** the same driver over a stdout PIPE (the `| tee` case) — the
  first header within 3s while the drain still holds its cell proves
  `flush=True` works without PYTHONUNBUFFERED (the spawned env strips it so
  the proof cannot pass trivially).
- **gen_progress keep-parsing (D14-04):** over a tree mixing a completed v2
  dispatch root (real fake-run state + ledger + cell artifacts) with a
  static manifest worker root, `gen_progress.main` completes (exit 0) and its
  emitted JSON parses — the v2 state file's presence does not disturb the
  generator (which serializes the tui scanner, never dispatch_state).
- Gates: both static byte-identity pins pass unchanged, `make lint` and
  `make typecheck` green, ci.yml blob hash unchanged, Makefile untouched.

## Verification Evidence

- `.venv/bin/python -m pytest tests/test_dispatch_core.py -q` → **66 passed**
  (53 Phase-13 baseline + 13 new: 3 schema-consumer, 7 renderer, 3 flush/keep-parsing lanes).
- `.venv/bin/python -m pytest tests/test_dispatch_core.py tests/test_sweep_shard.py -q` → **115 passed**.
- `make lint && make typecheck` → All checks passed.
- `git hash-object .github/workflows/ci.yml` → `33d2252eb594e0faecece9e8015a332d8d6479ef` (byte-identical).
- `git status --porcelain Makefile` → empty (renderer stayed in dispatch_core.py per Q6).
- Acceptance greps: `queue_depth` ×9, `_render_state` ×4, `flush=True` ×4 in
  pipeline/dispatch_core.py; `DISPATCH_STATE_SCHEMA_VERSION == 2` importable.
- Driver standalone probe: `exit code 0`, terminal state
  `status=done counts={completed: 2, failed: 0, skipped: 0, total: 2}`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] pexpect exitstatus is None at assert time**
- **Found during:** Task 3 (the interrupted executor's last finding, confirmed on resume)
- **Issue:** `child.expect(pexpect.EOF)` only observes the closed stream; `exitstatus` stays None until the child status is reaped, so `assert child.exitstatus == 0` failed.
- **Fix:** Verified the driver exits 0 standalone first (subprocess probe), then added `child.close()` after `expect(EOF)` — close performs the waitpid reap, after which exitstatus carries the drain's real verdict. Documented inline as the pexpect contract.
- **Files modified:** tests/test_dispatch_core.py
- **Commit:** 7fb7424

**2. [Rule 3 - Blocking] ty rejected `proc.stdout` as `IO[str] | None`**
- **Found during:** Task 3 (`make typecheck`)
- **Issue:** Popen's stdout attribute is Optional-typed; `selector.register(proc.stdout, ...)` and `proc.stdout.readline()` failed the typecheck gate in the pipe test.
- **Fix:** `assert proc.stdout is not None` immediately after Popen (PIPE was requested) — narrows the union for both uses.
- **Files modified:** tests/test_dispatch_core.py
- **Commit:** 7fb7424

### Execution deviation (orchestrator-owned, not a code deviation)

Plan execution was interrupted by an API usage cap mid-Task-3 and resumed the
same hour from `.continue-here.md`; Tasks 1-2 were committed by the first run
(a3adc3f, c837102) and verified against the plan's lanes on resume before
Task 3 was completed. No task was redone.

## Auth Gates

None.

## State-Update Notes

`roadmap.update-plan-progress 14` returned `missing_phase_details` (this
ROADMAP uses checkbox plan lists, not a progress table); the Phase 14 wave-1
checkbox was updated by hand in the Phase 13 convention. All other handlers
(advance-plan, update-progress, record-metric, add-decision ×3,
record-session, requirements.mark-complete MGPU-03) applied cleanly.

## Known Stubs

None — every field the schema declares is written by the real drain, the
renderer renders the frozen payload, and all three verification legs are
real (no mocks in the pty/pipe lanes beyond the injected fake children).

## Threat Flags

None — no surface beyond the plan's threat model. T-14-01 (renderer output
errors) mitigated structurally + pinned by `test_render_state_swallows_output_errors`
and `test_renderer_broken_pipe_never_fails_cells`; T-14-02 unchanged atomic
writes + frozen schema; T-14-SC held (zero installs).

## Self-Check: PASSED

- Files exist: pipeline/dispatch_core.py, schemas/dispatch_state.json, tests/test_dispatch_core.py — FOUND
- Commits are ancestors of HEAD: a3adc3f, c837102, 7fb7424 — FOUND
