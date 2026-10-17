---
phase: quick-261017-klw
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tui/app.py
  - tui/screens/selection.py
  - tui/screens/run_config.py
  - tui/screens/env_check.py
  - pipeline/run_finetune.py
  - tests/tui/test_pilot_run_config.py
  - tests/tui/test_pilot_selection_custom.py
  - tests/tui/test_pilot_env_check.py
  - tests/test_run_finetune_contracts.py
  - .planning/STATE.md
  - .planning/quick/261017-klw-fix-batch-feedback-round-review-wr-01-03/261017-klw-SUMMARY.md
autonomous: true
requirements: [WR-01, WR-02, WR-03, IN-01, IN-02, IN-03, CR-01-07]

user_setup: []

estimate:
  tokens: 52000
  raw_tokens: 26000
  tasks: 3
  confidence: low

must_haves:
  truths:
    - "WR-01 (ctrl+c vs Input copy): on a BASE screen with a focused Input holding a NON-EMPTY selection, ctrl+c now COPIES (the key delegates through super().on_event to textual 8.2.8's own ctrl+c,super+c -> copy Input binding at .venv .../widgets/_input.py:139) instead of opening the exit confirm; the delegation fires ONLY for isinstance(self.focused, Input) with truthy selected_text while the top screen is non-modal — an empty-selection Input, a non-Input focus, or no focus still routes ctrl+c into the action_quit chain exactly as today (no exit bypass: a selection-holding Input + ctrl+c is the EHC-ratified explicit operator gesture on selected text, not an exit dodge); ctrl+c under modals stays inert (existing delegation, byte-unchanged); the on_event docstring records the delegation."
    - "WR-02 (off-loop exit kill): ExitModal [k] no longer runs kill_sweep serially on the event loop — action_kill_quit delegates to ONE app-level @work(exclusive=True, thread=True, group='exit-kill', exit_on_error=False) worker that SIGTERM-fans-out over every modal root with a per-root broad guard (a raising kill logs and the fan-out CONTINUES), then unconditionally posts an ExitKillsDone message whose handler calls App.exit() — the exit lands on worker completion, never before every root was attempted, and a kill_sweep that raises can never strand a killed-but-unexited console; the monitor.py:1530-1540 mon-kill discipline (blocks up to kill grace — NEVER on the event loop) is now honored on the exit path too; the new @work site satisfies tests/tui/test_work_site_hardening.py's structural pin (exit_on_error=False AND an internal broad guard) with zero edits to that test; action_detach_quit stays synchronous (detach is a registry handle drop, non-blocking)."
    - "WR-03 (mixed live roots): when the launcher holds exactly ONE live TUI root AND the monitor's attached root is a DIFFERENT running sweep (attached_running and attached_root not in roots), action_quit now uses the MULTI-root ExitModal form with combined = tuple(roots) + (attached_root,) — the modal names BOTH full paths via LNC_EXIT_MESSAGE_MULTI and [k]/[enter] act on BOTH (no CLI-launched sweep survives a kill-and-exit silently, no unnamed sweep keeps the GPU on detach-and-exit); the pure single-TUI-root form, the >1-TUI-roots form, and the attached-running-ONLY form (empty roots — kill stays the documented launcher-noop) are byte-unchanged; an attached root that IS the TUI root (attached_root in roots) never duplicates."
    - "IN-01 (slot-2 progress residue): selection.apply_queue_progress now performs the _live_model_entries()/state check FIRST and stores _live_percents/_live_speeds only for passing (model, downloading) ticks — the exact ordering mirror of the fixed slot-3 twin at tui/screens/data_manager.py:799-826 — so dataset keys can never accumulate in the slot-2 live dicts; the model-tick in-place cell update behavior is byte-unchanged (the existing test_pilot_selection_custom.py:1521 test stays green unmodified)."
    - "IN-02 (gate id-space collision): GateWorkerError carries a scope tag ('stage' from the enumeration/preflight/confirm-data workers, 'launch' from the launch worker, None only for the run_id-None mount worker); the staleness filter compares run_id against EXACTLY ONE counter — scope 'launch' vs _gate_launch_id, everything else vs _gate_stage_id — so a superseded gate-stage error whose id numerically equals the CURRENT _gate_launch_id is dropped (no spurious 'launch failed' toast after a successful launch); a genuinely-current stage or launch error still surfaces the error toast and releases _gate_active exactly as before; the mount worker's run_id-None error still always surfaces."
    - "IN-03 (remount stale-cache window): action_refresh sets _check_in_flight = True SYNCHRONOUSLY (on the event loop, immediately after _run_id += 1 and BEFORE dispatching run_full_check) — an L-toggle remount landing between the refresh dispatch and the worker thread's first line now hits the elif _check_in_flight branch and renders pending rows, never the same-day cached pre-refresh outcome; the worker-body flag set (env_check.py:523) stays as the belt for the mount-path dispatch; the completion handler's flag release and all run-id-tagged message drops are unchanged."
    - "07-CR-01 (minimal custom entry): pipeline/run_finetune.py's model loop reads model_name = model_row.get('Model_name', ix) (the registry key — the exact value custom_entries.land() stamps, so wizard-landed entries never even hit the fallback) and mean_token_len = model_row.get('Mean_token_length', 1) (the no-compression floor every official singlebase/one-hot row carries — max_length degrades to data_length + 2, over-long never truncating) — a schema-legal minimal custom model entry ({Model_path, size (M), type, Tokenizer} per schemas/custom_registry.json) no longer raises KeyError at loop entry; Model_path (line ~1019) and Tokenizer (~1020) stay hard-indexed (schema-required); a RED-first source-contract test in tests/test_run_finetune_contracts.py (AST pin — the file is read as source text, never imported: torch/dnallm at module top) pins the guarded shape."
    - "GATES: make lint and make typecheck green; make test at EXACTLY the pre-batch baseline membership — 1 failed (tests/tui/test_services_run_config.py::test_storage_overview_defaults_mirror_real_consumers, machine-local pipeline/logs state) / 1858 passed before this batch's new tests, every NEW test green, zero new failures (read the actual counts at execution time; the 1F MEMBERSHIP is the invariant); node lane 26/26 (make test's node --test tests/js/*.test.js); tests/tui/test_snapshots.py goldens green — if any golden goes unexpectedly red STOP and report the D-03 path, NEVER run make snapshot-update; zero new user-facing strings (no i18n inventory churn — if a fix unexpectedly needs copy, it becomes bilingual via _t plus both inventories, but by design none does); ONE plain commit, zero attribution trailers, executor does NOT push."
  artifacts:
    - tui/app.py
    - tui/screens/selection.py
    - tui/screens/run_config.py
    - tui/screens/env_check.py
    - pipeline/run_finetune.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_pilot_selection_custom.py
    - tests/tui/test_pilot_env_check.py
    - tests/test_run_finetune_contracts.py
    - .planning/quick/261017-klw-fix-batch-feedback-round-review-wr-01-03/261017-klw-SUMMARY.md
  key_links:
    - "base-screen ctrl+c -> App.on_event (key=='ctrl+c', screen mounted, not modal) -> focused isinstance Input and selected_text -> await super().on_event(event) -> Input's own ctrl+c copy binding (WR-01)"
    - "base-screen ctrl+c (no selection) -> action_quit chain byte-unchanged (below-min-grid return | ExitModal | QuitConfirmModal) (WR-01)"
    - "ExitModal [k] -> app-level request_kill_and_exit(tuple(self._roots)) -> @work thread worker group='exit-kill' -> per-root launcher.kill_sweep under broad guard -> ExitKillsDone message -> App.exit() (WR-02)"
    - "action_quit mixed case (len(roots)==1 and attached_running and attached_root not in roots) -> combined roots tuple -> ExitModal MULTI message naming both -> [k]/[enter] act on both (WR-03)"
    - "selection.apply_queue_progress(key, percent, speed) -> _live_model_entries().get(key) guard FIRST -> stores + _update_download_cell only for (model, downloading) (IN-01)"
    - "gate worker exception -> GateWorkerError(text, run_id, scope='stage'|'launch') -> handler compares against exactly the tagged counter -> drop stale / toast current (IN-02)"
    - "action_refresh -> synchronous _check_in_flight=True before run_full_check dispatch -> remount elif branch skips the same-day cache (IN-03)"
    - "minimal custom model entry -> registry overlay merge -> run_finetune model loop .get reads with (ix, 1) defaults -> no KeyError at loop entry (07-CR-01)"
---

<objective>
The maintainer's 2026-10-17 14:49 fix batch (修复批先走 — the last fix batch before milestone close): seven review findings, every one with a reviewer fix sketch (committed 08-REVIEW.md) or verifier adjudication (07-VERIFICATION.md W4), all live-re-verified on disk at planning time. Three warnings in the exit channel (tui/app.py): the ctrl+c intercept silently kills the base-screen Input copy binding (WR-01), ExitModal [k] runs blocking kill polling on the event loop contradicting the monitor's own off-loop discipline (WR-02), and the mixed one-TUI-root + one-attached-CLI-root case silently drops the CLI sweep from the exit modal (WR-03). Three infos in screen hygiene: slot-2's progress stores before its kind/state guard — the asymmetric twin of the already-fixed slot-3 site (IN-01), the GateWorkerError staleness filter collides two independent id counters (IN-02), and env_check's in-flight flag is set in the worker body leaving a remount stale-cache race window (IN-03). One carried pipeline critical: run_finetune's model loop hard-indexes two schema-OPTIONAL registry fields a minimal custom entry legitimately lacks (07-CR-01 / 07 W4).

Purpose: every exit path names and acts on every live root without freezing the console; the primary exit key no longer breaks copy-on-selection on base screens; the three screen hygiene seams stop leaking stale/wrong state; a schema-legal custom entry stops crashing the pipeline consumer — closing all six 08-REVIEW findings and the one carried 07 W4 row before the milestone audit.
Output: surgical edits to tui/app.py (3 seams), three screen modules (1 seam each), pipeline/run_finetune.py (2 guarded reads), RED-first tests for all seven findings in four existing test files, full gates at the exact 1F/1858P baseline with zero new failures, one plain commit.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/phases/08-tui-foundation-env-check-selection/08-REVIEW.md

The reviewer's per-finding sketches (WR-01/02/03, IN-01/02/03) live verbatim in the 08-REVIEW.md above; the 07-CR-01 adjudication (minimal-entry reproduction, schema required-subset, ownership) is Warning W4 of .planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-VERIFICATION.md.

Live source anchors (verified at planning time on HEAD 70c733e — re-locate by the quoted code, line numbers drift):
- tui/app.py:250-254 — ExitModal.action_kill_quit (serial kill loop + self.app.exit())
- tui/app.py:1097-1110 — action_quit live-root branch (root = roots[0] if roots else attached_root)
- tui/app.py:1113-1149 — on_event ctrl+c intercept (docstring + the not is_modal guard)
- tui/app.py:75 — from textual.widgets import Footer, Static (extend with Input)
- tui/app.py:332-404 — module-level Message classes + app-level @work worker patterns (kick_download_queue at :763-:786 is the busy-flag/worker idiom)
- tui/screens/monitor.py:1530-1549 — the off-loop kill template (@work exclusive thread group='mon-kill' exit_on_error=False + broad guard + run-id-tagged posts)
- tui/screens/selection.py:1593-1612 — apply_queue_progress (stores at 1607-1608 BEFORE the 1609-1611 guard)
- tui/screens/data_manager.py:799-826 — the FIXED slot-3 twin (guard at 820-824, stores at 825-826 below it) — IN-01's ordering template
- tui/screens/run_config.py:1117-1130 (GateWorkerError class), :1327 (mount post, run_id=None), :1923-1939/:1987-2000/:2014-2027 (stage workers, _gate_stage_id space), :2060-2077 (launch worker, _gate_launch_id space), :2125-2139 (the dual-counter staleness filter)
- tui/screens/env_check.py:460-487 (remount elif chain — the _check_in_flight branch at 471-475), :521-523 (worker-body flag set), :604 (completion release), :688-710 (action_refresh)
- pipeline/run_finetune.py:1007-1021 (model loop head — the four model_row reads; ix is the registry key), :1332 (mean_token_len consumer: max_length = int(data_length / mean_token_len) + 2)
- tests/tui/test_pilot_run_config.py:240-312 (FakeLauncherService — records kill_calls/detach_calls/live), :1497-1599 (Task-3 exit-triple test section — the home for WR tests), :1341 (screen_gate_active helper)
- tests/tui/test_pilot_selection_custom.py:1521-1605 (slot-2 apply_queue_progress/apply_queue_event tests)
- tests/tui/test_pilot_data_manager.py:909-938 (the slot-3 IN-01 test shape to mirror)
- tests/tui/test_pilot_env_check.py:439-488 (the WR-03 remount test to extend)
- tests/test_run_finetune_contracts.py (source-contract precedent: run_finetune.py is read as SOURCE TEXT, never imported)
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Exit-channel trio in tui/app.py — ctrl+c copy delegation (WR-01), off-loop kill-and-exit (WR-02), mixed live roots (WR-03)</name>
  <files>tui/app.py, tests/tui/test_pilot_run_config.py</files>
  <behavior>
    - WR-01 RED first: on a mounted base screen (run-config), focus one of its Inputs, type text, drive a real selection (shift+home / shift+arrow presses; probe the installed 8.2.8 Input selection seam if attributes differ), press ctrl+c — assert the QuitConfirmModal does NOT open, the screen is still the base screen, app._exit stays False (and, if observable on 8.2.8, app.clipboard equals the selected text). Contrast: same Input with an empty selection — ctrl+c opens the QuitConfirmModal (no live sweep) exactly as before.
    - WR-02 RED first: launcher with live=('/repo/a', '/repo/b') opens the multi-root ExitModal; press k — after settling, kill_calls contains BOTH roots and app._exit is True (exit driven by worker completion, kill before exit for every root). Variant: a launcher fake whose kill_sweep raises — the console STILL exits (the broad guard posts the completion regardless).
    - WR-03 RED first: launcher with live=('/repo/tui-root',) plus a monitor stub (assign app._monitor_screen directly) whose attached_running_counts() returns (True, '/repo/cli-root', done, total); ctrl+q — the ExitModal's roots tuple contains BOTH paths and the rendered message uses the MULTI form naming both; [k] kills both; a separate assertion covers [enter] detaching both.
    - Regression pins: the single-TUI-root form, the >1-roots form, and the attached-only form stay byte-unchanged (existing Task-3 tests green unmodified); ctrl+c under modals stays inert; the new @work site passes tests/tui/test_work_site_hardening.py with ZERO edits to that file.
  </behavior>
  <action>
    Write the RED tests into the Task-3 exit section of tests/tui/test_pilot_run_config.py (reuse FakeLauncherService; extend it with a kill_raises knob for the WR-02 variant; for WR-03 build the minimal monitor stub exposing only attached_running_counts — do NOT mount a real MonitorScreen), run them, confirm each fails for the cited reason, THEN implement all three seams in tui/app.py:

    1. WR-01 — extend the import at tui/app.py:75 to `from textual.widgets import Footer, Static, Input` and, inside on_event's intercept branch (currently `if isinstance(event, events.Key) and event.key == 'ctrl+c' and self.screen is not None and not self.screen.is_modal:` → `await self.action_quit(); return`), insert BEFORE the action_quit call: delegate when the focused widget is an Input holding a non-empty selection — read `focused = self.focused`, and when `isinstance(focused, Input) and focused.selected_text` (selected_text is the verified 8.2.8 property at .venv .../widgets/_input.py:854 — the reviewer's sketch said `.selection`, which does not exist; use selected_text) do `await super().on_event(event)` and return (the Input's own ctrl+c,super+c → copy binding at _input.py:139 then owns the key). Do NOT widen the delegation (empty selection, non-Input focus, modal top screen all keep today's routing — the EHC ruling accepts exactly the explicit-gesture-on-selected-text case, and this must not become an exit bypass). Amend the on_event docstring with the delegation paragraph (why: base-screen Inputs get copy parity with modal Inputs — the 08-REVIEW WR-01 asymmetry). APP_CTRLC_LABEL help copy stays unchanged.

    2. WR-02 — add one module-level Message class `ExitKillsDone` (beside MonitorSwitchRequested at :332) and on the App: a public seam `request_kill_and_exit(self, roots)` and a worker `@work(exclusive=True, thread=True, group='exit-kill', exit_on_error=False) def _exit_kill_worker(...)` that loops the roots calling `self._launcher.kill_sweep(root)` with a per-root broad try/except (log the exception — print with a timestamped prefix per the app's logging convention — and CONTINUE to the next root; every root must be attempted even when one raises), then UNCONDITIONALLY posts ExitKillsDone; the handler `on_exit_kills_done` calls `self.exit()`. Rewrite ExitModal.action_kill_quit (:250-254) to delegate: `self.app.request_kill_and_exit(tuple(self._roots))` — no loop, no synchronous self.app.exit(). If ty flags the ExitModal→app call, follow the established self.app.<method> precedent at tui/screens/run_config.py:2115 (self.app.sweep_launched). Update both docstrings (the modal's [k] semantics: dispatched off-loop, exit lands on completion; note the esc-mid-kill edge: k is a committed intent, esc after k no longer cancels the exit — today esc-after-k is unreachable because k froze the loop). action_detach_quit stays byte-unchanged.

    3. WR-03 — in action_quit's live-root branch (:1097-1110), compute `attached_extra = attached_running and attached_root not in roots`; take the MULTI form when `len(roots) > 1 or (roots and attached_extra)` with `combined = tuple(roots) + ((attached_root,) if attached_extra else ())` and message `S.LNC_EXIT_MESSAGE_MULTI.format(n=len(combined), roots=', '.join(combined))`; the single-root line (`root = roots[0] if roots else attached_root`) now runs only for exactly-one-TUI-root-without-a-different-attached-root and attached-only — both byte-unchanged. Amend the action_quit docstring's WR-05 paragraph with the mixed-case sentence (one TUI root + a different attached running root joins the multi form — the modal names EVERY live root). Zero new strings (MULTI constant reused).

    Probe-first discipline (8.2.8 seams, the repo's probe-pinned precedent): verify App.focused / Input.selected_text / the copy binding on the installed package before writing the delegation; record any probe divergence in the SUMMARY. Tests must drive a REAL selection via key presses (home, then shift+end or shift+arrows) after typing into the Input — do not poke private attributes.
  </action>
  <verify>
    <automated>cd /home/forrest/Github/dnallmmark && uv run --group dev --group tui pytest tests/tui/test_pilot_run_config.py tests/tui/test_work_site_hardening.py -x -q</automated>
  </verify>
  <done>All new WR-01/WR-02/WR-03 tests green; the existing exit-triple tests (q/ctrl+q routing, quit-confirm y/n/esc, ctrl+q-with-live-sweep) green unmodified; tests/tui/test_work_site_hardening.py green with zero edits (the new exit-kill site satisfies the never-exit pin); ruff+ty clean on tui/app.py (make lint && make typecheck).</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Screen hygiene trio — slot-2 progress store ordering (IN-01), GateWorkerError scope tag (IN-02), env_check sync in-flight flag (IN-03)</name>
  <files>tui/screens/selection.py, tui/screens/run_config.py, tui/screens/env_check.py, tests/tui/test_pilot_selection_custom.py, tests/tui/test_pilot_run_config.py, tests/tui/test_pilot_env_check.py</files>
  <behavior>
    - IN-01 RED first: on the mounted selection screen, call apply_queue_progress with a key whose queue entry is a DATASET-kind downloading entry — assert the key does NOT land in screen._live_percents/_live_speeds (mirror the test_pilot_data_manager.py:909-938 shape); a model downloading tick still stores (covered by the existing :1521 test, stays green unmodified).
    - IN-02 RED first: with the run-config screen mounted, set _gate_stage_id=1 and _gate_launch_id=3; deliver a stale stage error GateWorkerError('boom', run_id=3, scope='stage') to the handler — assert NO error toast is recorded and _gate_active is untouched (this is the collision case that surfaces a spurious launch-failed toast today); controls: GateWorkerError(..., run_id=3, scope='launch') surfaces the toast; GateWorkerError(..., run_id=1, scope='stage') surfaces; run_id=None (mount) surfaces.
    - IN-03 RED first: on the mounted env screen, monkeypatch/replace the screen's run_full_check with a recorder that does NOT run (so the worker never executes), call action_refresh — assert _check_in_flight is True immediately after action_refresh returns (the synchronous set) and _results is cleared; the WR-03 remount test at test_pilot_env_check.py:439-488 stays green unmodified.
  </behavior>
  <action>
    Write the three RED tests (in their named homes, following each file's local Pilot/fake idioms; capture toasts via the file's existing notify-assertion helper — probe how prior tests assert app notifications and reuse that mechanism), run them, confirm each fails for the cited reason, THEN apply the three surgical edits:

    1. IN-01 — in tui/screens/selection.py apply_queue_progress (:1593-1612), move the two stores (`self._live_percents[key] = percent` / `self._live_speeds[key] = speed`) BELOW the guard, mirroring the fixed slot-3 twin ordering at tui/screens/data_manager.py:820-826 exactly: read `entry = self._live_model_entries().get(key)` first, `if entry is None or entry.state != 'downloading': return`, THEN store and call _update_download_cell. Amend the docstring with the IN-01 note in the data_manager.py:813-818 idiom (stores sit below the ignore guard — non-model keys cannot accumulate).

    2. IN-02 — in tui/screens/run_config.py: extend the GateWorkerError class (:1117-1130) with a keyword `scope: 'str | None' = None` (document the contract in its docstring: 'stage' compares against _gate_stage_id, 'launch' against _gate_launch_id, None keeps the run_id-None mount-worker always-surface semantics); tag the posting sites — the three stage workers (:1935, :1998, :2025) get scope='stage', the launch worker (:2074) gets scope='launch', the mount site (:1327, run_id=None) stays as-is; rewrite the staleness filter in on_run_config_screen_gate_worker_error (:2131-2135) to single-counter comparison: scope 'launch' is stale iff run_id != self._gate_launch_id; anything else (stage or untagged) is stale iff run_id != self._gate_stage_id; run_id None always surfaces. These scope strings are internal discriminators, NOT user copy — plain literals in the screen module, no strings.py entries.

    3. IN-03 — in tui/screens/env_check.py action_refresh (:688-710), insert `self._check_in_flight = True` synchronously immediately after `self._run_id += 1` and BEFORE `self.run_full_check()`, with a comment recording why (the WR-03 remount guard must hold from dispatch, not from the worker thread's first line — the L-toggle remount window would otherwise consult the same-day cache and render the pre-refresh outcome; the app's kick_download_queue busy-flag discipline). The worker-body set at :523 stays (belt for the mount-path dispatch at :486); the completion release at :604 is untouched.
  </action>
  <verify>
    <automated>cd /home/forrest/Github/dnallmmark && uv run --group dev --group tui pytest tests/tui/test_pilot_selection_custom.py tests/tui/test_pilot_selection.py tests/tui/test_pilot_run_config.py tests/tui/test_pilot_env_check.py -x -q</automated>
  </verify>
  <done>All three new tests green; the existing slot-2 progress test (:1521), the existing env remount test (:439), and every existing gate/exit test in the three files green unmodified; make lint && make typecheck clean.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Pipeline custom-entry guard (07-CR-01) — guarded Model_name/Mean_token_length reads + RED source-contract test</name>
  <files>pipeline/run_finetune.py, tests/test_run_finetune_contracts.py</files>
  <behavior>
    - RED first: a new source-contract test (e.g. test_minimal_custom_entry_reads_are_guarded) that AST-parses pipeline/run_finetune.py and asserts, inside the model loop (`for ix, model_row in models_info.items():`), that the Model_name read is a model_row.get('Model_name', ix) call (default = the loop key Name) and the Mean_token_length read is a model_row.get('Mean_token_length', 1) call (default = constant 1); plus the negative: no bare Subscript on model_row with slice Constant 'Model_name' or 'Mean_token_length' remains anywhere in the module; plus the boundary pin: the Model_path and Tokenizer reads stay hard-indexed (schema-required). Test must fail on the current bare subscripts, then pass after the edit.
  </behavior>
  <action>
    Write the RED test into tests/test_run_finetune_contracts.py following that file's documented read-source-never-import pattern (run_finetune.py does `import torch` / `from dnallm import ...` at module top — CPU-unimportable; every contract there is textual/structural AST), run it to confirm the RED, THEN apply the two guarded reads in pipeline/run_finetune.py:

    - :1008 `model_name = model_row['Model_name']` → `model_name = model_row.get('Model_name', ix)` — ix is the registry key (loop header at :1007), and custom_entries.land() stamps Model_name = key for every wizard-landed entry (Pitfall 6/11), so the fallback reproduces exactly what land() would have stamped and wizard entries never hit it; this also keeps --target_model filtering working over the key for minimal hand-written entries.
    - :1021 `mean_token_len = model_row['Mean_token_length']` → `model_row.get('Mean_token_length', 1)` — 1 is the no-compression floor every official singlebase/one-hot row carries (probed across the 59 official entries at planning time); the sole consumer (:1332 `max_length = int(data_length / mean_token_len) + 2`, non-singlebase branch only) degrades to data_length + 2 — over-long (padding waste), NEVER truncating, and the max_token_len cap plus models_with_limited_length clamp still bound it downstream.
    - Inline comment at each site citing schemas/custom_registry.json's required subset ({Model_path, size (M), type, Tokenizer} — these two fields are optional) and the 07-VERIFICATION W4 adjudication. Model_path (:1019) and Tokenizer (:1020) stay hard-indexed.
    - Do NOT touch the dataset-side siblings (row['Dataset_name'] :1077, row['length'] :1322) or the probe-branch read ([row['Model_name'] for ...] :849) — they are OUTSIDE this batch's ruling (recorded below in Non-goals); do NOT refactor the loop or extract helpers (surgical fixes only).
  </action>
  <verify>
    <automated>cd /home/forrest/Github/dnallmmark && uv run --group dev --group tui pytest tests/test_run_finetune_contracts.py tests/test_registry_loader.py -x -q</automated>
  </verify>
  <done>The new source-contract test green; every existing contract in tests/test_run_finetune_contracts.py and the 24 overlay tests in tests/test_registry_loader.py green unmodified (the overlay seam is byte-untouched); make lint covers pipeline/run_finetune.py clean (it is on the lint lane).</done>
</task>

<non_goals>
Explicitly NOT in this batch (maintainer boundary, 2026-10-17 14:49):
- Review findings #26-28 (concurrency deep-holes) — independent debug track, untouched.
- WizardModal keycap treatment — awaiting maintainer ruling; report the question in the SUMMARY after the batch lands (do not change WizardModal).
- directories_config lint lane (WR-02 old account) — WINDOWS disposal round.
- run_finetune dataset-side hard-index siblings (row['Dataset_name'] :1077, row['length'] :1322) and the probe-branch read (:849) — recorded for the maintainer in the SUMMARY as known-unchanged siblings of 07-CR-01; NOT fixed here (outside the ruling's seven).
- No E2' full sweep, no pipeline execution, no golden regeneration, no push.
</non_goals>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| operator keystroke → app exit channel | ctrl+c/q/ctrl+q routing decides console exit and sweep kills |
| registry JSON → pipeline loop | untrusted file input (custom registries) feeds run_finetune's model loop |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-klw-01 | Tampering | App.on_event ctrl+c delegation (WR-01) | medium | mitigate | Delegation requires isinstance(self.focused, Input) AND truthy selected_text AND non-modal top screen — no other widget or empty selection can divert the exit key; the accepted-gesture rationale is on record (EHC ruling). |
| T-klw-02 | DoS | exit-kill worker (WR-02) | low | mitigate | Per-root broad except + unconditional ExitKillsDone post + exit_on_error=False: a raising kill_sweep can never leave a killed-but-unexited console; structural pin (test_work_site_hardening) auto-covers the new site. |
| T-klw-03 | Tampering | GateWorkerError scope filter (IN-02) | low | mitigate | Scope-tagged single-counter comparison drops superseded errors in BOTH id spaces; current-scope errors always surface (never a silent gate failure). |
| T-klw-SC | Tampering | package installs | n/a | accept | No package installs in this batch — no supply-chain surface (pyproject/uv.lock untouched). |
</threat_model>

<verification>
Full gates after Task 3, from the repo root:
1. `make lint` — ruff green over the touched lanes (tui/* via PHASE8_TUI wildcard, pipeline/run_finetune.py explicitly on the lane).
2. `make typecheck` — ty green (tui/app.py carries real textual types; the new Message/worker members type-check).
3. `make test` — pytest at EXACTLY the 1F baseline membership (tests/tui/test_services_run_config.py::test_storage_overview_defaults_mirror_real_consumers is the sole, machine-local failure; read the actual counts — the MEMBERSHIP is the invariant, the passed count grows by this batch's new tests and nothing else); `node --test tests/js/*.test.js` 26/26.
4. `uv run --group dev --group tui pytest tests/tui/test_snapshots.py -q` — goldens green; on any unexpected red STOP and report the D-03 path (never regenerate).
5. Confirm zero new user-facing strings: `git diff -- tui/strings.py` is EMPTY.
</verification>

<success_criteria>
- All seven findings fixed exactly per their reviewer sketches with the planning-time live re-verification honored (selected_text not the sketch's .selection; scope-tag not id-space merge; sync flag in action_refresh).
- Every new test observable RED-first (record the failing run output in the SUMMARY's evidence section, the quick-task convention).
- Full gates at the exact baseline membership; goldens untouched; zero new strings; single PLAIN commit (no attribution trailers, no push); STATE.md quick-task row + 261017-klw-SUMMARY.md written (including the WizardModal ruling question and the run_finetune sibling-sites note for the maintainer).
</success_criteria>

<output>
Create `.planning/quick/261017-klw-fix-batch-feedback-round-review-wr-01-03/261017-klw-SUMMARY.md` when done; update `.planning/STATE.md` (quick-task row + Decisions deltas per the house pattern).
</output>
