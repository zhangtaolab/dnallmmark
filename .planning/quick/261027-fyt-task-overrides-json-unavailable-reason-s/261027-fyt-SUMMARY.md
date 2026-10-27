---
phase: quick-261027-fyt
plan: 01
subsystem: tui
tags: [task-overrides, availability-overlay, run-sweep, tui-wizard, fail-open, xdg-config]

requires:
  - phase: 261014-f4w
    provides: directories_config.config_dir() — the SAME-ROOT resolver task_overrides.json reuses (never duplicated)
  - phase: 08-03/08-04
    provides: tui/services/registries.py presence layer (PRESENCE_*, presence_for) — the committed 2-state contract the overlay merges AFTER
  - phase: 11-02
    provides: validate_composition / preview in tui/services/run_config.py — the problem vocabulary the task_unavailable code joins
provides:
  - pipeline/task_overrides.py — the ONE tolerant fail-open loader over the user-owned task_overrides.json (unavailable + reason + since per registry task key, fully reversible by deleting the entry)
  - The registries availability overlay (AVAILABILITY_UNAVAILABLE, Availability, unavailable_tasks(), availability_for()) with the presence contract untouched
  - run_sweep enumerate_matrix flagged-task drop (one authority for every matrix: CLI, TUI preview, gate) + _warn_unavailable_tasks (collect-all warning, all-flagged fatal, malformed-file warning)
  - Operator surfaces — wizard badge/refusal/sanitize/#cfg-hint-tasks/degraded note, matrix ⊘ 暂不可用 column glyph, selection preset/template loud skip, task_unavailable preview problem
affects: [run_sweep, tui-wizard, tui-selection, tui-matrix, future temporarily-broken tasks]

actuals:
  tokens: 24351   # chars/4 over the realized diff (97407 diff chars)
  tasks: 2
  commits: 2      # measured: git rev-list --count 4881366..HEAD
plan_head_before: 48813669573f0d59fb2771979271e33a9c3b70b3
plan_head_after: ac10c333e0cec57c4fa49c07e1b1a843de0d0aa6

tech-stack:
  added: []   # stdlib-only (json/os/pathlib + the existing sibling imports) — no new dependencies anywhere
  patterns:
    - "Fail-open exclusion overlay (the ruled opposite of directories.json's fail-loud): absent = normal zero state; malformed = zero overrides + degraded PATH carrier, surfaced visibly on every consumer"
    - "Layer split by construction: presence stays the committed 2-state contract; availability is a runtime overlay merged AFTER — pinned by a byte-identity test with overrides present"
    - "Overlay-to-UI threading through existing chokepoints: flagged rows join PickerList's disabled list (zero widget change); presets ride the existing unknown-key loud skip"

key-files:
  created:
    - pipeline/task_overrides.py
    - tests/test_task_overrides.py
  modified:
    - pipeline/run_sweep.py
    - tui/services/registries.py
    - tui/services/run_config.py
    - tui/strings.py
    - tui/screens/run_config.py
    - tui/screens/selection.py
    - tui/screens/matrix.py
    - tests/test_sweep.py
    - tests/tui/test_services_registries.py
    - tests/tui/test_services_run_config.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_pilot_selection.py
    - tests/tui/test_pilot_matrix.py
    - tests/tui/test_strings_phase11.py

key-decisions:
  - "Fail-open for the overrides file (the ruled policy): an exclusion list must never block the benchmark — worst case a task runs instead of skipping (recoverable), the opposite hazard class of directories.json's fail-loud data-loss guard; documented side-by-side in the loader's docstring"
  - "registries.unavailable_tasks() returns the pipeline TaskOverrides NamedTuple verbatim (mapping + degraded in ONE read); screens project to {reason, since} dicts for SelectionData/PickerEntries"
  - "Flagged wizard rows join the EXISTING disabled row list — PickerList.action_select refuses both keyboard and mouse marks with zero widget change; the warning branches on the overrides lookup and passes markup=False (the reason is user free text; App.notify defaults to markup=True)"
  - "Hint/Label rendering of override-derived text goes through literal Text(str) construction only — Static.update parses str content markup (textual 8.2.8), so the reason can never inject rich markup (T-261027-01)"
  - "The ⊘ 暂不可用 glyph is 10 cells in the matrix's pinned 8-cell column — the plan pins both the copy and the unchanged column geometry, so the rendered cell clips (leading ⊘ carries the NO_COLOR meaning); the cell VALUE carries the full constant"
  - "validate_composition's third param is optional-additive (None = check skipped) — every existing caller and test unchanged; preview() threads the registries-surface read on the worker thread it already runs on"

patterns-established:
  - "Task-scoped join discipline: keys unknown to the dataset registry stay in the loader's mapping and are ignored STRUCTURALLY at every consumer — a model key in the file affects nothing (pinned by a sweep test and a selection Pilot test)"
  - "Overlay-first render check: _presence_glyph consults task_overrides BEFORE presence so the runtime layer can never be confused with the committed view; reason never reaches the matrix (constant copy only)"

requirements-completed: [OVERRIDES-FILE-TOLERANT-LOADER, AVAILABILITY-OVERLAY-LAYER-PRESENCE-CONTRACT-UNTOUCHED, SWEEP-CLI-WARN-SKIP-ALL-UNAVAILABLE-ERROR, WIZARD-PICKER-BADGE-MARK-REFUSAL-SANITIZE-HINT, MATRIX-PRESENCE-VIEW-BADGE, SELECTION-PRESET-TEMPLATE-LOUD-SKIP, GOLDENS-BYTE-IDENTICAL-ZERO-OVERRIDES]

coverage:
  - id: D1
    description: "The tolerant loader: resolution chain (same-root as directories.json), absent = zero overrides, malformed = zero + degraded path, entry tolerance table, unknown keys retained"
    requirement: OVERRIDES-FILE-TOLERANT-LOADER
    verification:
      - kind: unit
        ref: "tests/test_task_overrides.py (29 tests)"
        status: pass
  - id: D2
    description: "The availability overlay: unavailable_tasks() delegation, availability_for merge table (overlay wins over every presence status, passthrough verbatim otherwise), and the layer-split pin (presence_for byte-identical with overrides present; the :398 purity test over the grown source)"
    requirement: AVAILABILITY-OVERLAY-LAYER-PRESENCE-CONTRACT-UNTOUCHED
    verification:
      - kind: unit
        ref: "tests/tui/test_services_registries.py (the availability overlay section)"
        status: pass
  - id: D3
    description: "CLI: enumerate drops flagged tasks always (byte-identical with no file, model keys ignored); main warns collect-all naming key (reason), all-requested-flagged exits fatally, malformed file warns + proceeds, untrainable refusal wins"
    requirement: SWEEP-CLI-WARN-SKIP-ALL-UNAVAILABLE-ERROR
    verification:
      - kind: unit
        ref: "tests/test_sweep.py (the task_overrides section, 7 tests)"
        status: pass
  - id: D4
    description: "Wizard surfaces: badge after the key, space-refusal with reason-carrying markup=False warning through the existing chokepoint, mount-time sanitize twin, #cfg-hint-tasks flagged list + degraded note, _problem_line branch"
    requirement: WIZARD-PICKER-BADGE-MARK-REFUSAL-SANITIZE-HINT
    verification:
      - kind: automated_ui
        ref: "tests/tui/test_pilot_run_config.py (the task-unavailability overlay surfaces section, 5 tests)"
        status: pass
  - id: D5
    description: "Matrix: a flagged task column renders the ⊘ 暂不可用 glyph in every cell; zero overrides renders the grid byte-identically"
    requirement: MATRIX-PRESENCE-VIEW-BADGE
    verification:
      - kind: automated_ui
        ref: "tests/tui/test_pilot_matrix.py::test_flagged_task_column_renders_the_unavailable_glyph + test_zero_overrides_grid_renders_presence_glyphs_verbatim"
        status: pass
  - id: D6
    description: "Selection slot 2: a preset referencing a flagged task rides the existing loud skip (named, never marked); a model key in the file blocks nothing (task-scoped join)"
    requirement: SELECTION-PRESET-TEMPLATE-LOUD-SKIP
    verification:
      - kind: automated_ui
        ref: "tests/tui/test_pilot_selection.py::test_preset_referencing_flagged_task_rides_the_loud_skip + test_model_key_in_overrides_never_blocks_a_model_mark"
        status: pass
  - id: D7
    description: "Zero-override parity everywhere: validate_composition default skips (existing tests unedited), preview absent-file byte-identity, goldens byte-identical (test_snapshots green, NO regeneration)"
    requirement: GOLDENS-BYTE-IDENTICAL-ZERO-OVERRIDES
    verification:
      - kind: unit
        ref: "tests/tui/test_services_run_config.py (the task_unavailable section) + tests/tui/test_snapshots.py in the Task-2 lane (459 passed)"
        status: pass

status: complete
---

# quick-261027-fyt: Task-level temporary-unavailability overrides — Summary

A user-owned ``task_overrides.json`` (same config root as directories.json) flags registry task keys temporarily unrunnable with a free-text reason: flagged tasks are excluded from every dispatch path (wizard marks refused + sanitized, presets/templates loud-skipped, enumerate_matrix filtered, CLI warn+skip with an all-flagged fatal), badged in every view (wizard picker badge + hint, matrix ⊘ column glyph), and fully reversible by deleting the entry. The fungi diagnosis motivated the mechanism; no task name is keyed in any code path (the single "GUE__fungi_species_20" occurrence in the diff is the loader docstring's motivation narrative, mirroring the plan's own objective text).

## What Ran (verification evidence)

- Task 1 lane: ``uv run --group dev --group tui pytest tests/test_task_overrides.py tests/tui/test_services_registries.py tests/tui/test_services_run_config.py tests/test_sweep.py -q`` — **495 passed**.
- Task 2 lane: ``uv run --group dev --group tui pytest tests/tui/test_services_run_config.py tests/tui/test_pilot_run_config.py tests/tui/test_pilot_selection.py tests/tui/test_pilot_matrix.py tests/tui/test_strings_phase11.py tests/tui/test_snapshots.py -q`` — **459 passed** (goldens byte-identical, zero regeneration).
- Full-lane gate: ``uv run --group dev --group tui pytest -m "not slow" -q`` — **2456 passed, 7 failed, 3 skipped, 1 deselected (41:09)**. All 7 failures are PRE-EXISTING environmental failures, verified by re-running them at the dispatch-base commit 4881366 in a throwaway worktree where they fail identically: 6 chmod-injected persist-failure tests (this box runs as root, so read-only permission bits never block writes — the known environmental issue in MEMORY) + 1 pty quiet-cadence timing test (CPU load from the concurrently running FungiHelixSeek rerun). None of the 7 touch any file or seam in this diff.
- Lint/type gates: ``uv run ruff check`` over all 16 touched files — clean; ``uv run ty check`` over the 8 source files and 8 test files — clean.
- Purity gates rode the suites: the registries Chinese-free source test, the services-tier textual-import lock, the screen-module CJK grep locks, and the strings bidirectional registry tripwires all green.
- The running FungiHelixSeek rerun was never touched (CPU-only tests, no GPU/process interaction; its ``pipeline/finetuned-fhs-full-b32oom-superseded/`` output area untouched).

## The One-Loader Chain (as landed)

```
~/.config/dnallmmark/task_overrides.json
  -> directories_config.config_dir()            (SAME root as directories.json — resolver reused, never copied)
  -> task_overrides.load_task_overrides()       (the ONE tolerant fail-open reader)
  -> registries.unavailable_tasks()             (the ONE services-surface read — selection snapshot worker, wizard picker worker, run_config.preview)
  -> run_sweep.enumerate_matrix                 (flagged tasks drop ALWAYS — every matrix: CLI, TUI preview, gate recomputes)
  -> run_sweep.main._warn_unavailable_tasks     (operator-visible warning; all-flagged fatal; malformed-file warning)
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `_warn_unavailable_tasks` all-flagged comparison never fired**
- **Found during:** Task 1 (RED->GREEN)
- **Issue:** The fatal branch compared a sorted LIST against a SET (``hits == requested``) — always False, so an all-flagged request printed the warning and proceeded to a 0-cell dry-run instead of exiting.
- **Fix:** Compare ``set(hits) == requested``; caught by ``test_cli_exits_when_every_requested_task_is_flagged`` before commit.
- **Files modified:** pipeline/run_sweep.py
- **Commit:** 3f29c04

**2. [Rule 1 - Bug] commit-amend landed the loader-test key neutralization on the wrong task commit**
- **Found during:** post-task audit (the "no hardcoded task name" success criterion)
- **Issue:** ``git commit --amend`` amended Task 2's HEAD instead of Task 1's, mixing a Task-1 test file into the Task-2 commit.
- **Fix:** Rebuilt both commits from the intact working tree via a mixed reset to the dispatch base (nothing pushed yet, no file contents changed) — Task 1 (3f29c04) now carries exactly its 6 files including the neutralized test key, Task 2 (ac10c33) exactly its 10.
- **Files modified:** git history only
- **Commit:** 3f29c04 / ac10c33

**3. [Rule 2 - Correctness] the screen-action mark path shares the branched refusal warning**
- **Found during:** Task 2 implementation
- **Issue:** The plan names only ``on_disabled_mark_requested`` for the unavailable-warning branch, but ``action_toggle_mark`` (space with focus outside the picker) warns through its own ``SEL_DISABLED_MARK_WARNING`` site — a flagged row would have shown the WRONG copy on that path.
- **Fix:** Factored ``_warn_refused_mark(key)`` (overrides lookup -> unavailable copy with reason + ``markup=False``; else the disabled-custom copy) and routed BOTH sites through it.
- **Files modified:** tui/screens/run_config.py
- **Commit:** ac10c33

Minor test-shape adjustments (not code deviations): the modal-based problem-copy Pilot test was replaced by a direct ``_problem_line`` branch pin (textual's event timing consumes a scripted preview result before the modal opens, making the modal assertion nondeterministic — the rendering pipeline itself stays pinned by the existing numbered-problems tests); the matrix glyph's cell-width assertion was dropped (the pinned copy is 10 cells in the pinned 8-cell column — both values are plan-locked, so the clip is the accepted consequence, noted in the test).

## Threat Mitigations Landed (per the register)

- **T-261027-01 (render injection) — mitigated:** every override-derived render goes through literal ``Text(str)`` construction (picker badge segments, hint Label — verified textual 8.2.8's ``Static.update`` parses str-content markup, so Text construction is load-bearing) or ``notify(..., markup=False)`` (the reason-carrying warning — ``App.notify`` defaults to ``markup=True``); the matrix renders constant copy only.
- **T-261027-02 (fail-open never silent) — mitigated:** degraded carries the path; the CLI prints one ``[Warning]`` naming it; the wizard renders CFG_TASK_OVERRIDES_DEGRADED in #cfg-hint-tasks; absent file stays the normal zero-override state (degraded None).
- **T-261027-03 (CLI injection) — accepted as registered:** reasons are print()-ed only, never evaluated, never in argv.
- **T-261027-04 (state drift) — mitigated:** the layer-split pin holds — with overrides present, ``presence_for`` output is byte-identical and the definite-presence contract tests (:274-298) stayed green untouched; no committed artifact records unavailability.

## Known Stubs

None — every surface is wired to the real loader chain; no placeholder data paths exist in the diff.

## Notes for the Verifier

- Reversibility: deleting the file entry restores the task everywhere on the next read (the file is the only state) — the refusal-toast copy names the restore path.
- The E2' note in the plan holds as implemented: a spec whose tasks equal the deliverable set minus flagged ones is NOT full-E2' (``is_full_e2x`` compares against the complete official trainable set) — intended semantics, unchanged.

## Self-Check: PASSED

- Files: pipeline/task_overrides.py, tests/test_task_overrides.py, and this SUMMARY all exist on disk.
- Commits: 3f29c04 (Task 1) and ac10c33 (Task 2) are ancestors of HEAD; ledger-measured commit count over 4881366..HEAD is 2, matching ``actuals.commits``.
- Working tree: only the pre-existing dispatch-time dirt remains unstaged (.planning bookkeeping, docs/live, the superseded run dir); no golden drift; exactly the 16 plan files committed.
