---
phase: quick-261017-klw
plan: 01
subsystem: tui-exit-channel + screen-hygiene + pipeline-custom-entry
tags: [exit-channel, ctrl-c-copy, off-loop-kill, mixed-roots, gate-error-staleness, env-remount, custom-registry]
requires:
  - "08-REVIEW.md WR-01/02/03 + IN-01/02/03 (the reviewer's per-finding sketches)"
  - "07-VERIFICATION.md Warning W4 (the 07-CR-01 adjudication)"
provides:
  - "Base-screen ctrl+c copy delegation for selection-holding Inputs (WR-01)"
  - "App-level exit-kill worker (group=exit-kill) with per-root broad guard + unconditional ExitKillsDone (WR-02)"
  - "Mixed one-TUI-root + one-attached-CLI-root MULTI ExitModal form (WR-03)"
  - "Slot-2 live-dict store-below-guard ordering (IN-01, the slot-3 twin's shape)"
  - "GateWorkerError scope-tagged single-counter staleness filter (IN-02)"
  - "Synchronous _check_in_flight set in env action_refresh (IN-03)"
  - "Guarded Model_name/Mean_token_length model-loop reads (07-CR-01) + AST source-contract pin"
affects:
  - tui/app.py (on_event, action_quit, ExitModal, new exit-kill worker)
  - tui/screens/selection.py (apply_queue_progress)
  - tui/screens/run_config.py (GateWorkerError + 4 posting sites + filter)
  - tui/screens/env_check.py (action_refresh)
  - pipeline/run_finetune.py (2 guarded reads at :1008/:1021)
tech-stack:
  added: []
  patterns:
    - "TYPE_CHECKING getters.app narrowing replaced by a string cast for same-module (ExitModal-in-app.py) delegation — the RunConfigScreen idiom cannot forward-reference its own module's App class"
    - "App-level one-shot @work(exclusive, thread, group, exit_on_error=False) + per-root broad guard + unconditional completion Message — the monitor mon-kill template on the exit path"
key-files:
  created: []
  modified:
    - tui/app.py
    - tui/screens/selection.py
    - tui/screens/run_config.py
    - tui/screens/env_check.py
    - pipeline/run_finetune.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_pilot_selection_custom.py
    - tests/tui/test_pilot_env_check.py
    - tests/test_run_finetune_contracts.py
decisions:
  - "WR-01 delegation gated to exactly isinstance(focused, Input) AND truthy selected_text AND non-modal top screen — the EHC-ratified gesture, never an exit bypass (empty selection / non-Input / modal keep today's routing)"
  - "WR-02 exit lands ONLY on ExitKillsDone (posted unconditionally after the fan-out); esc-after-k no longer cancels the exit — k is committed intent (previously esc-after-k was unreachable because k froze the loop)"
  - "WR-03 mixed form: len(roots) > 1 or (roots and attached_extra) -> MULTI with combined = tuple(roots) + ((attached_root,) if attached_extra else ()); the three existing forms byte-unchanged"
  - "IN-02 scope strings are internal discriminators in the screen module, NOT strings.py copy (zero user-facing strings)"
  - "07-CR-01 defaults: Model_name -> ix (what land() stamps; --target_model filtering keeps working over the key), Mean_token_length -> 1 (no-compression floor; consumer degrades over-long, never truncating)"
actuals:
  tokens: 60000    # chars/4 over the realized diff (10 files, ~700 changed lines incl. docstrings/comments)
  tasks: 3
  commits: 3       # measured: git rev-list --count 70c733e..HEAD
plan_head_before: 70c733e18efff90f9930040074e945a549006342
plan_head_after: 6e331d3afa78cf20758e64a97b921c6121adbc80
status: complete
---

# Quick Task 261017-klw: 08-review fix batch (WR-01..03 + IN-01..03 + 07-CR-01) Summary

**One-liner:** The maintainer's pre-closeout fix batch — the exit-channel trio in tui/app.py (ctrl+c copy delegation on selection-holding Inputs, off-loop kill-and-exit through an app-level exit-kill worker, the mixed TUI+CLI live-root MULTI modal form), the three screen-hygiene seams (slot-2 live-dict store ordering, GateWorkerError scope-tagged staleness filter, synchronous env-refresh in-flight flag), and the two guarded run_finetune model-loop reads that stop schema-legal minimal custom entries crashing the pipeline — all seven findings RED-first, full gates at the exact 1F baseline membership, three plain commits, not pushed.

## What Was Built

### Task 1 — the exit-channel trio (tui/app.py) — commit 06d2679

- **WR-01 (ctrl+c vs Input copy):** `on_event`'s intercept now delegates through `await super().on_event(event)` when the focused widget is an `Input` holding a NON-EMPTY selection (the verified 8.2.8 property is `selected_text` at `_input.py:854` — the reviewer's sketch said `.selection`, which does not exist; the plan encoded the correction and it held). Textual's own `ctrl+c,super+c -> copy` Input binding (`_input.py:139`) then owns the key — base-screen Inputs get copy parity with modal Inputs. The delegation fires ONLY for `isinstance(self.focused, Input)` with truthy `selected_text` while the top screen is non-modal: empty selection, non-Input focus, no focus, and every modal keep today's routing. The `on_event` docstring records the delegation and its rationale. `APP_CTRLC_LABEL` help copy unchanged.
- **WR-02 (off-loop exit kill):** `ExitModal.action_kill_quit` now delegates to a new public app seam `request_kill_and_exit(roots)` -> ONE `@work(exclusive=True, thread=True, group="exit-kill", exit_on_error=False)` worker `_exit_kill_worker` that loops the roots calling `self._launcher.kill_sweep(root)` under a per-root broad guard (timestamped print + continue — every root attempted even when one raises), then posts the new module-level `ExitKillsDone` message UNCONDITIONALLY; `on_exit_kills_done` calls `self.exit()`. The exit lands on worker completion, never before every root was attempted — the monitor.py mon-kill discipline (never block on the event loop) now honored on the exit path. The new @work site satisfies `tests/tui/test_work_site_hardening.py`'s structural pin with ZERO edits (exit_on_error=False AND an internal broad guard). `action_detach_quit` byte-unchanged (detach is a registry handle drop, non-blocking). Docstrings on both the modal and the seam record the esc-mid-kill edge: k is a committed intent; esc after k no longer cancels the exit (previously unreachable because k froze the loop).
- **WR-03 (mixed live roots):** `action_quit` computes `attached_extra = attached_running and attached_root not in roots`; the MULTI form fires on `len(roots) > 1 or (roots and attached_extra)` with `combined = tuple(roots) + ((attached_root,) if attached_extra else ())` — one TUI root plus a DIFFERENT attached running (CLI-launched) sweep now names and acts on BOTH via `LNC_EXIT_MESSAGE_MULTI`. The single-TUI-root form, the >1-TUI-roots form, and the attached-running-only form (empty roots — kill stays the documented launcher-noop) are byte-unchanged; an attached root that IS the TUI root never duplicates.

### Task 2 — the screen-hygiene trio — commit 0d02e18

- **IN-01 (slot-2 progress residue):** `selection.apply_queue_progress` now performs the `_live_model_entries().get(key)` / state check FIRST and stores `_live_percents`/`_live_speeds` only for passing (model, downloading) ticks — the exact ordering mirror of the fixed slot-3 twin (data_manager.py:820-826). Dataset keys can never accumulate in the slot-2 live dicts; the model-tick in-place cell update is byte-unchanged (the existing :1521 test stayed green unmodified).
- **IN-02 (gate id-space collision):** `GateWorkerError` carries a keyword `scope: str | None = None` ('stage' from the enumeration/preflight/confirm-data workers, 'launch' from the launch worker, None = the run_id-None mount worker — always surfaced). The staleness filter in `on_run_config_screen_gate_worker_error` now compares run_id against EXACTLY ONE counter: scope 'launch' vs `_gate_launch_id`, everything else vs `_gate_stage_id` — a superseded stage error whose id numerically equals the CURRENT `_gate_launch_id` is dropped (no spurious launch-failed toast after a successful launch). Scope strings are internal discriminators in the screen module, NOT strings.py copy.
- **IN-03 (remount stale-cache window):** `action_refresh` sets `_check_in_flight = True` synchronously (on the event loop, immediately after `_run_id += 1`, BEFORE dispatching `run_full_check`) with the why-comment — an L-toggle remount landing in the dispatch window now hits the `elif _check_in_flight` branch and renders pending rows, never the same-day cached pre-refresh outcome. The worker-body set (env_check.py:523) stays as the belt for the mount-path dispatch; the completion release untouched.

### Task 3 — the pipeline custom-entry guard (07-CR-01) — commit 6e331d3

- `pipeline/run_finetune.py` model loop: `model_name = model_row.get("Model_name", ix)` (the registry key — exactly what `custom_entries.land()` stamps, so wizard-landed entries never hit the fallback and `--target_model` filtering keeps working over the key) and `mean_token_len = model_row.get("Mean_token_length", 1)` (the no-compression floor; the sole consumer at :1332 degrades to `data_length + 2` — over-long, never truncating — still bounded by the max_token_len cap and the models_with_limited_length clamp). Inline comments at both sites cite the schema-required subset and the 07-VERIFICATION W4 adjudication. A schema-legal minimal custom entry no longer raises KeyError at loop entry.
- `Model_path` and `Tokenizer` stay hard-indexed (schema-REQUIRED — a missing value is a malformed entry that should fail loudly).
- New AST source-contract test `test_minimal_custom_entry_reads_are_guarded` in `tests/test_run_finetune_contracts.py` (read-source-never-import pattern): pins the guarded `.get` shapes with exact defaults, the negative (no bare `model_row[...]` subscript with a Constant 'Model_name'/'Mean_token_length' slice anywhere in the module), and the hard-index boundary for the required pair.

## RED-First Evidence (per finding, the quick-task convention)

| Finding | Test | RED output (cited reason) |
|---|---|---|
| WR-01 | `test_ctrlc_copies_when_input_holds_a_real_selection` | `AssertionError: ctrl+c over a selection-holding Input must NOT open the quit confirm` — the quit confirm opened (the intercept killed the copy); the selection-driving assertions before it passed (real key-press selection on 8.2.8 works) |
| WR-02 | `test_exit_k_raising_kill_still_attempts_every_root_and_exits` | `AssertionError: a raising kill must not abort the fan-out` — `assert ['/repo/a'] == ['/repo/a', '/repo/b']`: today the first raise escapes the synchronous action and root B is never attempted (the non-raising WR-02 test is the regression pin — behaviorally identical today, on-loop) |
| WR-03 | `test_mixed_roots_exit_names_and_kills_both_tui_and_attached` + `test_mixed_roots_exit_enter_detaches_both` | `assert ('/repo/tui-root',) == ('/repo/tui-root', '/repo/cli-root')` and `[enter]` detaching only the TUI root — the mixed case fell to the single-root form and dropped the CLI sweep |
| IN-01 | `test_dataset_kind_tick_stores_no_live_dict_residue` | `assert 'GUE__emp_H3' not in {'GUE__emp_H3': 40}` — the dataset key landed in `_live_percents` (stores above the guard) |
| IN-02 | `test_gate_worker_error_scope_tags_split_the_id_spaces` | `TypeError: GateWorkerError.__init__() got an unexpected keyword argument 'scope'` — the scope tag did not exist (the API-addition RED; the collision behavior itself is pinned by the test's post-fix assertions incl. three controls) |
| IN-03 | `test_refresh_sets_in_flight_flag_synchronously` | `assert False is True` — the flag was False the instant `action_refresh` returned (set only in the worker body, which the recorder never ran) |
| 07-CR-01 | `test_minimal_custom_entry_reads_are_guarded` | `AssertionError: a bare model_row['Model_name'] subscript survives` — `assert 'Model_name' not in ['Model_name', 'Tokenizer', 'Mean_token_length', 'Model_path']` (all four bare subscripts enumerated) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - necessary behavior consequence] The two CDR-2 ctrl+c-over-focused-Input tests adapted to the empty-selection form**
- **Found during:** Task 1
- **Issue:** textual 8.2.8's `Input._on_focus` auto-selects the whole content (`select_on_focus`, `_input.py:738`), so `test_ctrlc_no_sweep_opens_quit_confirm_over_focused_input` and `test_ctrlc_live_sweep_routes_to_exit_modal_over_focused_input` (both: focus an Input -> ctrl+c -> expect a modal) encode exactly the corner WR-01 changes — under the delegation, that keypress is now the ratified copy gesture, and the tests would fail.
- **Fix:** added `await pilot.press("end")` after focus in each (collapsing the auto-selection, with a WR-01 comment), preserving every original assertion — each test now pins the empty-selection routing it was written for; the selection-holding case is the new WR-01 test. The plan's unmodified-test enumeration (q/ctrl+q routing, quit-confirm y/n/esc, ctrl+q-with-live-sweep, the three modal forms) is fully honored — every one of those is green unmodified.
- **Files modified:** tests/tui/test_pilot_run_config.py
- **Commit:** 06d2679

**2. [Rule 3 - blocking] ty could not resolve the ExitModal->app delegation through the RunConfigScreen getters.app idiom**
- **Found during:** Task 1 (gates)
- **Issue:** The plan's fallback cited the `self.app.sweep_launched` precedent (run_config.py:2115), which works via a TYPE_CHECKING class-body `app = getters.app(DnallmMarkTui)` narrowing. In tui/app.py that class-body form is impossible: `DnallmMarkTui` is the module's OWN class defined BELOW ExitModal — ruff F821 and ty unresolved-reference both fire on the forward reference, a TYPE_CHECKING self-import fails ty's circular resolution, and a post-definition attribute assignment is ignored by ty.
- **Fix:** a string `cast("DnallmMarkTui", self.app).request_kill_and_exit(...)` inside `action_kill_quit` (method bodies resolve later module names in both tools) — the same narrowing intent, documented at the call site. Both gates green.
- **Files modified:** tui/app.py
- **Commit:** 06d2679

**3. [Rule 1 - test-fixture bug] The AST loop matcher initially matched `.items` as an Attribute, not a Call**
- **Found during:** Task 3
- **Issue:** `for ix, model_row in models_info.items():` makes the for-iter a `Call(func=Attribute)`, not an `Attribute` — the helper returned None after the source fix landed (the RED evidence had already fired on the negative branch, before the helper).
- **Fix:** matcher corrected to `isinstance(node.iter, ast.Call)` + `node.iter.func.attr == "items"`. Contract strength unchanged.
- **Files modified:** tests/test_run_finetune_contracts.py
- **Commit:** 6e331d3

**4. [Process note] Three atomic commits instead of the plan's "one plain commit"**
- The orchestrator's dispatch constraints mandate per-task atomic commits (Task 1 exit trio -> Task 2 hygiene trio -> Task 3 pipeline guard); the plan's success-criteria line said one. Every commit is PLAIN (zero attribution trailers) and the commit set is exactly the three task boundaries, so both intents are honored as far as they can be simultaneously.

## Maintainer Items (raised by this batch — NOT changed)

**1. WizardModal keycap treatment still NEEDS A RULING (carried from 261017-dnr, re-raised per this plan's non-goals).**
All six WizardModal bindings (`escape`/`enter`/`b`/`f`/`o`/`u` at wizard.py:564-576) remain `show=False`. Turning them on unconditionally would MISLEAD: `f`/`o` are step-1-only and `u` is landed-state-only (both no-op outside their step). Honest keycaps require step-aware visibility — a redesign of the wizard's binding surface. **Decision needed: (a) leave as-is (the step-view copy carries the affordances), (b) fund a step-aware keycap redesign, or (c) show only the always-valid subset per step.** Untouched by this batch (per the plan's non-goals).

**2. run_finetune.py sibling hard-index sites — recorded, deliberately NOT fixed (outside the ruling's seven).**
The 07-CR-01 fix covered ONLY the two model-loop reads. Three sibling hard-indexes remain and will raise the same KeyError class for schema-legal minimal entries when their code paths run:
- `:849` — the probe-variant guard's enumeration `[row["Model_name"] for row in models_info.values()]` (a minimal entry under `--config-variant probe` with no `--target_model` crashes before the refusal check);
- `:1077` — the dataset loop's `row["Dataset_name"]` (`Dataset_name` is schema-OPTIONAL for custom datasets the same way `Model_name` is for models — `custom_entries.land()` stamps it, minimal hand-written entries lack it);
- `:1322` — `data_length = row["length"]` (the dataset row's `length` field).
These belong to a future maintainer-ruled batch (the same guarded-read pattern + AST pin would apply; the dataset side needs its own defaults adjudicated).

## Gates

| Gate | Result |
|------|--------|
| `make lint` (ruff) | green — All checks passed (twice: after Task 1 gate fixes and at close) |
| `make typecheck` (ty, `--group dev --group tui`) | green — All checks passed |
| Full `make test` | **1 failed / 1867 passed — EXACTLY the 1F baseline membership**: `tests/tui/test_services_run_config.py::test_storage_overview_defaults_mirror_real_consumers` (machine-local pipeline/logs state) is the sole failure; 1867 = the pre-batch 1858 + this batch's 9 new tests, all 9 green, zero new failures |
| Node lane (`node --test tests/js/*.test.js`) | 26/26 pass |
| Snapshot goldens (`pytest tests/tui/test_snapshots.py`) | 11 passed — zero SVG interaction, `make snapshot-update` never run |
| Zero new strings | `git diff -- tui/strings.py` EMPTY |
| Task 1 targeted (`test_pilot_run_config.py + test_work_site_hardening.py`) | 93 passed — hardening pin green with ZERO edits to that file |
| Task 2 targeted (4 Pilot files) | 193 passed — existing slot-2 (:1521), env remount (:439), and every gate/exit test green unmodified |
| Task 3 targeted (`test_run_finetune_contracts.py + test_registry_loader.py`) | 98 passed — all existing contracts + the 24 overlay tests green unmodified |
| Push | NOT pushed (the orchestrator pushes) |

## Self-Check: PASSED

- All 9 modified/created files exist on disk (tui/app.py, tui/screens/{selection,run_config,env_check}.py, pipeline/run_finetune.py, tests/tui/test_pilot_{run_config,selection_custom,env_check}.py, tests/test_run_finetune_contracts.py).
- Commits 06d2679 / 0d02e18 / 6e331d3 all present and ancestors of HEAD.
- No tracked-file deletions in any of the three commits.
