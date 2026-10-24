---
phase: 16-tui-multi-gpu-surface
plan: 2
subsystem: ui
tags: [textual, tui, dispatch-state, multi-gpu, tolerant-reader, render-gate, cursor-identity]

requires:
  - phase: 14-orchestration-view-recovery
    provides: the frozen dispatch_state.json v2 schema (schemas/dispatch_state.json) this reader consumes
  - phase: 16-tui-multi-gpu-surface plan 16-01
    provides: the G-panel constructor-injection seam shape + the per-region render-gate law this plan mirrors
provides:
  - tui/services/dispatch_state.py — the textual-free tolerant frozen-v2 reader (None sentinel, DISPATCH_STALE_SECONDS=60.0 single home, snapshot-invariant honesty flag, never reconciles)
  - The dispatch block on the Running card (dispatch line + per-worker rows + stale/malformed warning row) through the ONE _card_content builder with cursor identity pinned (Pitfall 6)
  - The DispatchStateReader constructor-injection seam on MonitorScreen + DnallmMarkTui (16-05's fabricated golden fixtures)
  - The four MON_DISPATCH_* strings constants on the bilingual registry + EXPECTED_MON_CONSTANTS tripwire
affects: [16-tui-multi-gpu-surface (16-05 goldens fabricate DispatchStateView fixtures), tui monitor surface]

actuals:
  tokens: 16268
  tasks: 2
  commits: 2
  plan_head_before: 0ae37f98fa08cacf563165364ae23ae77d237fda
  plan_head_after: 7aca7dde27b5421c0f49924ba22ad4a9c2a68ee0

tech-stack:
  added: []  # zero installs (T-16-SC): stdlib json/dataclasses via artifact_loader only
  patterns:
    - "tolerant frozen-schema reader: per-field type-narrowing helpers degrade wrong-typed values to None; the invariant honesty check returns a verdict ONLY over complete legs (never a guessed one)"
    - "evidence-first cadence threading: the per-root views ride the EXISTING FrontierScanned message (an optional dict param, the plans precedent) and store BEFORE the render that reads them"
    - "dispatch structure legs (has-block, worker count, stale flag) inside _cards_struct_legs — label-count-changing inputs rebuild; value-only flips (busy->idle, counts) ride the in-place label refresh"

key-files:
  created:
    - tui/services/dispatch_state.py
    - tests/tui/test_services_dispatch_state.py
  modified:
    - tui/screens/monitor.py
    - tui/app.py
    - tui/strings.py
    - tests/tui/test_pilot_monitor.py
    - tests/tui/test_strings_phase11.py

key-decisions:
  - "Staleness = (now - mtime) >= 60.0 with the integer age riding the view — the >= boundary makes the MON_DISPATCH_STALE copy ({age}s >= 60s) and the behavior agree at exactly 60s; the now seam is a callable injected per read, never a mutated clock"
  - "The invariant check returns False (not malformed) when a leg is MISSING — tolerance and provable violation stay orthogonal; a missing counts object is a tolerance case, never a guessed verdict (pinned by test_unevaluable_invariant_is_not_malformed)"
  - "A malformed-but-fresh view renders the SAME MON_DISPATCH_STALE marker (UI-SPEC B rule 6's stale/malformed one-marker shape) at its true integer age; the dispatch line still renders the counts VERBATIM (the test pins 8/12 rendering, never a reconciled 9/12)"
  - "Missing values in the block render the existing _DASH honest-dash vocabulary (a dash is data, never a fabricated number) — the schema-required fields of a real writer never hit this path; it exists for the tolerance deep path"
  - "The stale warning row styles rich-native yellow (the $warning analog) — the card Label path's rich-native-only law (the 09-03/MATRIX_GLYPH_STYLES pin); the rows stay dim like the resume-note family"
  - "The dispatch legs join _cards_struct_legs (the mode machine's hold-check tuple) — a dispatch worker-count change resets the manual [w] choice to auto, consistent with the documented 'structure changed' semantics (rare: worker count is fixed per run)"
  - "_app() in the pilot suite defaults to a None-returning dispatch reader — every pre-16-02 pilot card stays byte-identical; only the dispatch tests inject views or the real reader"

patterns-established:
  - "Frozen-schema tolerant consumer: schema FILE as the contract (never the writer module import), literal sibling constant for the file name"
  - "Optional-param message threading for cadence additions (FrontierScanned.dispatch, the plans precedent) — existing message constructors stay source-compatible"

requirements-completed: [TUI-03]

coverage:
  - id: D1
    description: "The textual-free tolerant frozen-v2 reader: fresh 1:1 parse, absent/damaged/non-object -> None (no exception), missing-field tolerance, stale via injectable now, invariant violation flagged without repair, unrecognized status verbatim, import purity (no textual, no dispatch_core)"
    requirement: TUI-03
    verification:
      - kind: unit
        ref: "tests/tui/test_services_dispatch_state.py (11 tests over inline-written fixture files under tmp_path — machine-independent; the real pipeline/finetuned-smoke-r2 artifact consulted read-only)"
        status: pass
      - kind: unit
        ref: "tests/tui/test_import_lock.py (services textual-free glob collects dispatch_state.py automatically)"
        status: pass
  - id: D2
    description: "The dispatch block on the Running card: renders only for view-carrying roots (absent root byte-identical, no placeholder), stale/malformed warning row above the line with rows retained, fresh read clears it, status verbatim, busy/idle worker rows with fraction append, cursor identity over value-only flips + rebuild on worker-count change, one read per live root on the existing frontier pass, the real-read path over a fixture file"
    requirement: TUI-03
    verification:
      - kind: automated_ui
        ref: "tests/tui/test_pilot_monitor.py (9 dispatch Pilot tests over the constructor-injected reader)"
        status: pass
      - kind: unit
        ref: "tests/tui/test_strings_phase11.py (bidirectional EXPECTED_MON_CONSTANTS inventory over the four MON_DISPATCH_ names)"
        status: pass
  - id: D3
    description: "The vocabulary + gates: four constants registered through _t (UI-SPEC wording verbatim), lint/typecheck/ci-hash green, no new timer or worker group"
    requirement: TUI-03
    verification:
      - kind: unit
        ref: "grep strings.py MON_DISPATCH_* count 4 >= 4; make lint + make typecheck; git hash-object .github/workflows/ci.yml == 33d2252eb594e0faecece9e8015a332d8d6479ef; git diff grep proves zero new set_interval/@work/group= lines"
        status: pass

duration: 31min
completed: 2026-10-21
status: complete
---

# Phase 16 Plan 2: TUI-03 Dispatch Rows Summary

**A textual-free tolerant frozen-v2 dispatch_state.json reader (None sentinel, pinned 60s stale constant, never-reconcile invariant flag) feeding dispatch rows on the Running card — dispatch line + per-worker busy/idle rows + stale marking — through the ONE _card_content builder with cursor identity pinned, riding the existing 2s frontier pass.**

## Performance

- **Duration:** 31 min (plan estimate: 2 tasks; actual: 2 tasks, 2 commits)
- **Tokens (actuals, chars/4 over the diff):** 16,268 vs estimate 26,000 — the reader + block landed leaner than the estimate's ceiling; the 8+7 behavior matrix landed as 11 service tests + 9 Pilot tests
- **Commits:** 2 (710b302 reader, 7aca7dd monitor rows), measured `git rev-list 0ae37f9..7aca7dd` = 2

## Tasks Completed

### Task 1 — tui/services/dispatch_state.py tolerant frozen-v2 reader + fixture tests — 710b302

- **RED -> GREEN:** the 11-test fixture suite was written first and failed at the import (module absent) before the reader landed; two GREEN-step cycles earned their keep (below, TDD Notes).
- `tui/services/dispatch_state.py` (300 lines): frozen `DispatchStateView` family (`DispatchCounts`/`DispatchWorker`/`DispatchCellKey`/`DispatchFailure` sub-views) over the frozen v2 schema 1:1, missing-field tolerant (per-field `_as_int`/`_as_str`/`_as_float` narrowing; bool-is-int excluded); `read_dispatch_state(root, now=None)` reuses `artifact_loader.load_json_artifact` for the absent/damaged None sentinel (the Don't-Hand-Roll ruling; `import artifact_loader` top-level, the env_check precedent); `DISPATCH_STATE_FILE_NAME` pinned as a literal sibling of dispatch_core's frozen naming (zero dispatch_core import, D16-07); `DISPATCH_STALE_SECONDS = 60.0` in the documented-tunable style citing D16-08 + the STALE_GRACE_SECONDS precedent; the snapshot-invariant honesty check (`completed + failed + skipped + queue_depth + active_workers == total`) sets `malformed` ONLY over complete legs and NEVER repairs — queue depth is never recomputed client-side (UI-SPEC B rule 6).
- `tests/tui/test_services_dispatch_state.py` (317 lines): inline-written JSON fixtures under tmp_path (the real preserved smoke artifact consulted read-only as the shape reference, never a dependency) — fresh 1:1 (state_mtime from the file), absent, truncated + empty, non-object JSON, missing-field tolerance, stale via the injectable now (120s stale / 10s fresh / the 60.0 constant pin), invariant violation flagged with counts carried verbatim (queue_depth == 0 asserted — never recomputed), unevaluable invariant not malformed, unrecognized status verbatim, import purity in a fresh `-I` subprocess (asserts artifact_loader IS imported — the reuse ruling — and textual/dispatch_core are NOT).

### Task 2 — monitor dispatch rows + strings + Pilot pins — 7aca7dd

- **RED -> GREEN:** the 9-test Pilot block was written first and failed at the import (the strings constants absent) before the screen wiring landed.
- `tui/strings.py`: four `MON_DISPATCH_*` constants registered through `_t` with the UI-SPEC Copywriting wording VERBATIM — `MON_DISPATCH_WORKER_BUSY` data-forward (identical value both languages, the MON_GPU_ROW precedent), `MON_DISPATCH_STALE` glyph-first (⚠); the four names joined `EXPECTED_MON_CONSTANTS` (bidirectional tripwire green).
- `MonitorScreen` (`tui/screens/monitor.py`): the `DispatchStateReader` constructor-injectable seam (None -> `_default_dispatch_state_reader`, the 16-01 gpu-probe provider shape); the read rides the EXISTING `mon-frontier` 2s pass — one additional service read per live root inside the same worker, `FrontierScanned` gained the optional `dispatch` dict param (the `plans` precedent; existing constructors stay source-compatible) and the handler stores it BEFORE the render (the o8e evidence-first ordering); the vanished-root degradation drops the views cache with the other per-root caches.
- The dispatch block joins the ONE `_card_content` builder (A4 interleave: strip -> resume note -> dispatch block -> matrix/tree): `_dispatch_block_lines` renders the stale/malformed warning row (rich-native yellow) ABOVE the dispatch line (status verbatim incl. unrecognized strings, done/total/queue 1:1, `_DASH` for missing), then one worker row per `workers[]` entry in array order (busy ⏵ with the ` × frac_{fraction}` code append when non-null / idle ◌, both dim like the resume family). NO view -> NO block (absent/damaged) — static/CLI sweep roots and `-mgpu-w*` worker roots byte-identical (pinned).
- `_cards_struct_legs` gained the dispatch legs (has-block, worker count, stale-or-malformed flag) — a worker-count or stale-flip change rebuilds the ListItem while value-only changes (busy->idle, counts moving) ride `_refresh_card_labels` in place: cursor identity survives (the f0x law, Pitfall 6). The right pane, wide table, History rows, and drill modal UNCHANGED (UI-SPEC B rule 8).
- `tui/app.py`: the seam threaded `DnallmMarkTui.__init__` -> every `build_monitor_screen` call (the 261018-08g rebuild-per-navigation discipline) — 16-05's goldens fabricate views here.
- 9 Pilot behaviors: block renders with position pin (label[1] directly under the strip, above the matrix body), fraction append, absent root no-block + ONE-read-per-live-root pin, stale AND malformed both render the warning row above with counts verbatim (the malformed leg asserts 8/12 renders — never reconciled), fresh read clears the marker, unrecognized status verbatim, cursor identity over the busy->idle flip (clear spy zero) + rebuild on the worker-count change, and the REAL reader over a tmp fixture file (the real-read path).

## Verification Results

- `pytest tests/tui/test_pilot_monitor.py tests/tui/test_services_dispatch_state.py tests/tui/test_strings_phase11.py -q` -> **146 passed** (re-run green post-commit)
- `pytest tests/tui/test_pty_driver.py -q` -> **15 passed** (the quiet-cadence byte-silence pin over the REAL app holds — the dispatch read only fires for live roots, so an idle machine stays silent)
- `make lint` + `make typecheck` -> **all checks passed**
- `git hash-object .github/workflows/ci.yml` -> **33d2252eb594e0faecece9e8015a332d8d6479ef** (unchanged)
- Grep gates: `MON_DISPATCH_*` in strings.py = 4 >= 4; `DISPATCH_STALE_SECONDS.*60[.]0` present; **zero new `set_interval`/`@work`/`group=` lines in the monitor.py diff** (UI-SPEC B rule 7 — no new timer, no new worker group)
- `pytest tests/tui/test_snapshots.py -q` -> **9 passed, 2 failed** — exactly the two pre-existing monitor golden failures (WINDOWS #46, the standing #mon-gpu panel chrome from 16-01); 16-05 owns the D-03 regeneration. Unchanged by this plan (the golden fixtures carry no dispatch roots, so the dispatch block adds no new golden delta).

## Deviations from Plan

None — the plan executed as written.

### Notes (no rule needed)

- **tui/app.py is modified but absent from the plan's `files_modified` list** — the Task-2 action text itself mandates the composition-root threading ("the app composition root threads it so 16-05 fabricates views"); the same plan-file-list omission as 16-01. Treated as documentation gap, not a deviation.
- **TDD cycle notes (the tdd="true" RED->GREEN loop, not deviations):** (a) the reader's first GREEN run crashed on `for entry in failures_doc if isinstance(failures_doc, list)` — the comprehension's outer iterable evaluates before the guard clause; fixed by guarding the iterable itself (the missing-field test caught it — exactly what Test 4 exists for). (b) Two test-fixture faults in the Pilot stale/malformed test (the malformed view carried the default age 5 while the assertion expected 120; the assertion hard-coded done=9 while the malformed view correctly renders 8/12 verbatim) — fixed on the test side; the 8/12 assertion is now derived from the view and doubles as the never-reconcile pin.

## Known Stubs

None — the reader is wired end-to-end (frontier read -> message -> per-root store -> the ONE content builder -> render gates) and every surface renders real data.

## Handoff Notes (16-05 — goldens)

- The two monitor goldens stay RED on the committed tree by design (WINDOWS #46, the 16-01 standing panel + now the dispatch seam); 16-05 regenerates under the D-03 discipline.
- `_golden_app` (test_snapshots.py) can now thread BOTH fabrication seams: `gpu_probe_provider` (16-01) and `dispatch_state_reader` (this plan) — a fabricated `DispatchStateView` through the constructor seam gives `monitor_running.svg` the dispatch block (running, one busy + one idle worker — the UI-SPEC goldens table shape) with zero GPU and zero real file reads.
- The fabricated-view helper grammar lives in the Pilot suite (`_fabricated_dispatch_view`); 16-05 should mirror it in the snapshot fixtures.

## Threat Mitigations Landed

- **T-16-03 (Tampering — malicious/half-written dispatch_state.json):** stdlib json only through the artifact_loader sentinel (never eval); typed dataclasses with per-field tolerance; a parseable-but-inconsistent snapshot renders the warning marker over VERBATIM values — never executed, never reconciled (pinned by the invariant tests).
- **T-16-04 (Spoofing — stale state presented as current):** `state_mtime` rides the view with `DISPATCH_STALE_SECONDS = 60.0` pinned in the reader (single home, D16-08); the stale row renders ABOVE the dispatch line with last-known-good retained; the marker clears on the next fresh read (pinned).
- **T-16-SC (Tampering — package installs):** zero installs — stdlib json/dataclasses via the existing artifact_loader seam only.

## Self-Check: PASSED

- tui/services/dispatch_state.py, tests/tui/test_services_dispatch_state.py exist; tui/screens/monitor.py, tui/strings.py, tui/app.py, tests/tui/test_pilot_monitor.py, tests/tui/test_strings_phase11.py modified
- Commits 710b302, 7aca7dd are ancestors of HEAD (7aca7dd); `git rev-list 0ae37f9..HEAD` = 2
- All verify lanes re-run green after the final commit (146 + 15 tests, lint, typecheck, grep + hash gates)
