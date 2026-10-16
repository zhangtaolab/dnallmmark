---
phase: quick-261016-vxr
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tests/tui/test_services_sweep_monitor.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_pilot_run_config.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_nav_shell.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_strings_phase11.py
  - tui/services/sweep_monitor.py
  - tui/screens/monitor.py
  - tui/app.py
  - tui/strings.py
  - .planning/STATE.md
  - .planning/quick/261016-vxr-slot-5-monitor-batch-eta-remaining-time-/261016-vxr-SUMMARY.md
autonomous: true
requirements: [VXR-1, VXR-2, VXR-3, VXR-4]

user_setup: []

estimate:
  tokens: 66000
  raw_tokens: 35000
  tasks: 4
  confidence: low

must_haves:
  truths:
    - "VXR-1 (step-cadence ETA on the slot-5 progress row): a RUNNING entry row whose progress parses renders an ETA suffix derived from its seed's TWO NEWEST checkpoint-*/trainer_state.json files — rate = Δglobal_step / Δ(trainer_state.json file mtime) between the newest pair, eta_seconds = (max_steps − newest step) / rate; every underivable case (only one checkpoint, non-positive Δstep or Δmtime, damaged second trainer_state, max_steps ≤ current step, max_steps unparseable) renders the dim — (the module's _DASH), never a fabricated number; rows whose progress does not parse at all keep the MON_PROGRESS_INDETERMINATE constant byte-identical; non-running rows keep the bare dim dash byte-identical; the narrow (80-col) form keeps the steps text + ETA segment and drops only the bar (existing rule)."
    - "VXR-2 (slot-5 k stop key + confirm): MonitorScreen.BINDINGS gains k -> action_kill_running (visible MON_KILL_KEYCAP keycap, declared after r); with an attached root that is LIVE in the launcher (str(resolved attached root) in live_sweeps()) and not below the minimum grid, k opens KillConfirmModal — a ConfirmModal subclass with y = the ONLY confirm key, n/esc cancel, enter STRUCTURALLY inert (the LaunchConfirmModal/EHC-2 idiom), border title MON_KILL_TITLE with the root, message MON_KILL_CONFIRM verbatim; y dispatches an exclusive mon-kill thread worker calling the launcher's kill_sweep through the TOLERANT getattr seam (a fake without the method reads noop — the entries_progress/single_gpu_launch_blocked precedent) so the blocking SIGTERM/grace-poll/SIGKILL-escalation never runs on the event loop, then a KillFinished message renders the outcome toast (signalled -> MON_KILL_TOAST; already_dead -> MON_KILL_TOAST_DEAD; noop -> MON_KILL_UNAVAILABLE; a raised exception -> MON_KILL_FAILED error toast, the WR-03 posture); the console NEVER exits on this path (stop training ≠ exit console); an attached root NOT in live_sweeps() (CLI-launched or already dead) refuses BEFORE the confirm with the MON_KILL_UNAVAILABLE toast; no attached root returns silently (the [f]/[t] precedent); below-minimum grid opens nothing; the single-GPU serialization guard is NEVER consulted on the kill path (kill is the EHC-3 remedy, not a launch — pinned by test)."
    - "VXR-3 (uppercase Q priority exit): DnallmMarkTui gains an on_event override intercepting events.Key with key == 'Q' when a screen is mounted and its top screen is NOT modal, routing to the SAME guarded action_quit chain v0z landed (below-min-grid -> nothing; live sweep -> ExitModal; neither -> QuitConfirmModal) and consuming the key so it is NEVER typed into a base-screen Input; Q under ANY modal is inert (never typed as an exit, never stacks a second modal — capital-Q text stays typeable in modal Inputs, e.g. an E2' phrase or path containing Q); lowercase q semantics are byte-unchanged (types in Inputs, confirm chain elsewhere); the help modal gains a Q row (APP_Q_LABEL, appended in _binding_rows after the ctrl+c row — the ctrl+q manual-row precedent) and the slot-5 k row appears automatically via the screen BINDINGS projection."
    - "VXR-4 (gates + goldens + discipline): make lint + make typecheck green; full pytest at EXACTLY the 7F baseline membership (test_determinism 1, test_schemas 5, test_services_run_config 1) with zero new failures and every new test passing — read the actual pass count at execution time (v0z lands ~10 tests first), the 7F MEMBERSHIP is the invariant; node --test 26/26 via make test; the seven new MON_ constants and APP_Q_LABEL are bilingual through _t and MON_KILL_* join EXPECTED_MON_CONSTANTS (the closed bidirectional inventory); commits are PLAIN (zero attribution trailers); the executor does NOT push; tui/ scope only."
    - "Golden discipline: monitor_running.svg AND monitor_empty.svg CHANGE (the k keycap row in the bottom bar) — regenerate both via make snapshot-update, do NOT commit them, report to the orchestrator for the maintainer's D-03 review (the committed tree fails test_snapshots until the maintainer lands them — state this in the SUMMARY); every OTHER golden stays byte-identical (the ETA suffix lands only in the parsed-progress branch the golden fixtures never reach — their running row is the tolerant-seam indeterminate); the pre-existing worktree modification to tests/tui/__snapshots__/run_config.svg (the 261016-poa D-03 artifact) is byte-preserved — snapshot it at Task 1 and byte-compare at Task 4."
  artifacts:
    - tui/services/sweep_monitor.py
    - tui/screens/monitor.py
    - tui/app.py
    - tui/strings.py
    - tests/tui/test_services_sweep_monitor.py
    - tests/tui/test_pilot_monitor.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_strings_phase11.py
    - .planning/quick/261016-vxr-slot-5-monitor-batch-eta-remaining-time-/261016-vxr-SUMMARY.md
  key_links:
    - "two newest checkpoint-*/trainer_state.json (step + file mtime each) -> sweep_monitor.cell_progress -> CellProgress.eta_seconds -> entries_progress passthrough -> MonitorScreen._entry_progress_cell -> '≈' format_eta segment | dim '—' (VXR-1)"
    - "k -> action_kill_running -> below-grid/attached/live-attached guards -> KillConfirmModal (y-only, enter inert) -> @work(group='mon-kill') worker -> getattr(_launcher, 'kill_sweep') -> killpg SIGTERM + SIGKILL escalation -> KillFinished -> outcome toast; console stays up (VXR-2)"
    - "terminal key 'Q' -> DnallmMarkTui.on_event intercept (screen not modal) -> action_quit legs (v0z) -> ExitModal | QuitConfirmModal | below-grid return (VXR-3)"
    - "MON_KILL_* _t registrations <-> EXPECTED_MON_CONSTANTS in tests/tui/test_strings_phase11.py (the closed inventory lock) (VXR-2/VXR-4)"
    - "k keycap in MonitorScreen.BINDINGS -> BottomBar binding_row + help modal rows -> monitor_running.svg / monitor_empty.svg (D-03 regeneration, uncommitted) (VXR-2/VXR-4)"
---

<objective>
The maintainer's 2026-10-16 live-session batch on slot 5 (monitor): (1) an honest per-training-run ETA beside the entries progress row; (2) a `k` stop key with its own kill confirmation (stop training without exiting the console); (3) uppercase `Q` exiting from any focus — including the filter-input focus trap the maintainer hit tonight — through the v0z confirmation chain.

Purpose: the operator can watch a long sweep and answer the only two questions that matter at a glance (how long, how do I stop it) without leaving the console or reaching for an external orchestrator kill.
Output: extended CellProgress ETA derivation + KillConfirmModal + k binding + Q on_event intercept, bilingual strings + inventory, RED-first tests, full gates at the exact 7F baseline, two regenerated monitor goldens riding the D-03 review path (uncommitted).
</objective>

<required_reading>
/home/forrest/Github/dnallmmark/.planning/STATE.md
/home/forrest/Github/dnallmmark/.planning/quick/261016-vxr-slot-5-monitor-batch-eta-remaining-time-/PLANNER-CONTRIBUTIONS.md
/home/forrest/Github/dnallmmark/tui/services/sweep_monitor.py
/home/forrest/Github/dnallmmark/tui/screens/monitor.py
/home/forrest/Github/dnallmmark/tui/app.py
/home/forrest/Github/dnallmmark/tests/tui/test_pilot_monitor.py
</required_reading>

<context>
SERIAL CONSTRAINT (hard precondition, from the orchestrator): the 261016-v0z executor is landing QuitConfirmModal + the action_quit restructure + the ctrl+q/ctrl+c help rows in app.py/strings.py in parallel. Before starting Task 1, verify (a) .planning/quick/261016-v0z-guard-ctrl-q-exit-route-the-inherited-te/261016-v0z-SUMMARY.md exists and (b) the v0z feat/docs commits are at HEAD (git log). Halt and report if not. Align every reuse point to the LANDED v0z state read from disk at execution time — the worktree already carries v0z's changes uncommitted at planning time.

Planning-time probes (live, throwaway /tmp scripts — never committed). These facts are load-bearing:

ETA data source (item 1) — probed on real artifacts:
- trainer_state.json carries NO wall-clock field (probed finetuned-smoke/plant-dnabert-6mer/iDNA_ABF_datasets__5mC/seed_42/checkpoint-528: keys include global_step/max_steps/log_history; log_history entries carry only epoch/step/loss-family fields — no timestamps). The reliable wall-clock source is each checkpoint's trainer_state.json FILE mtime (probed pair checkpoint-520/checkpoint-528: mtimes 2s apart).
- The tee log's HF tqdm training bar DOES carry cadence (e.g. `3/20480 [00:12<22:43:18, 3.99s/it]`) but lives in carriage-return-separated segments (one physical line holds the whole bar history), interleaves Filter/Encoding/loading bars, and exists ONLY for TUI-launched sweeps (CLI-launched renders MON_LOG_UNAVAILABLE in the [t] modal). DECISION: checkpoint-pair derivation — same files cell_progress already parses, works for every launch mode, no log-format coupling. The coordinator's alternative reading "trainer_state checkpoint 时间戳" is implemented as the checkpoint trainer_state.json file mtime.

textual 8.2.8 priority semantics (item 3) — probed with live Pilot runs (P1-P14):
- P1: App-level Binding("Q", ..., priority=True) does NOT fire while an Input is focused — the character types into the Input. Mechanism: screen.py _binding_chain (~408) applies a consume-key filter — a focused widget's check_consume_key (Input returns True for EVERY printable character, widgets/_input.py:498) strips the key from every later namespace's binding map INCLUDING the app's; the priority walk (app.py:3966 _check_bindings, priority branch walks reversed(screen._binding_chain)) then finds no Q anywhere. The maintainer's 方案 (a) cannot be realized by a Binding alone for a PRINTABLE key.
- P3/P8: ctrl+q (priority, non-printable) DOES fire over a focused Input — the filter only strips keys the widget would consume, and Input does not consume ctrl-combos.
- P9: a priority binding FIRES over a plain open modal (the priority path uses the full _binding_chain, not the modal-cut chain). Consequence for design: Q-as-binding would stack modals over modals — so Q is implemented as an App.on_event intercept with an explicit not-screen.is_modal guard, NOT as a BINDINGS entry.
- P10-P14 (the adopted seam, probed live): overriding App.on_event to intercept events.Key with key == "Q" when self.screen is not None and not self.screen.is_modal, routing to the guarded quit and returning WITHOUT super() delivers exactly the intent — Q fires over a focused Input and is never typed (P10: fired, input value unchanged); lowercase q still types normally (P11); Q inside a modal Input TYPES the character and never quits (P12 — an E2' phrase or path containing a capital Q stays enterable); Q over a focused DataTable (P13) and with no focus (P14) fires. Base is App.on_event (app.py:4060, `async def on_event(self, event: events.Event) -> None`); is_modal is a property on Screen (screen.py:336).
- Documented consequence of 方案 (a), reported not deviated: a capital Q can no longer be typed into BASE-screen Inputs (the selection filter, run-config inputs) — it is reserved as the exit key; under modals it types normally. The maintainer chose this tradeoff explicitly.

Live-code anchors (re-verify on disk before editing — mutable scope, and v0z may have shifted app.py line numbers):
- tui/screens/monitor.py — BINDINGS ~760-772 (enter/f/t/a/r + nav digits; k joins after r); _entry_progress_cell ~1501-1525 (the render seam: parsed branch builds MON_PROGRESS_STEPS text + bar, narrow drops the bar); the modal family FailuresModal/LogTailModal/CellDetailModal ~429-650 (KillConfirmModal joins here); request_rerun ~1206 is the confirm+worker+tolerant-getattr precedent (below-grid return, single_gpu_launch_blocked getattr, LaunchConfirmModal push, mon-rerun worker, run-id-tagged messages); _entries_progress_of ~964 is the tolerant getattr seam precedent; on_unmount stops timers.
- tui/services/sweep_monitor.py — CellProgress ~224-242 (frozen, add eta_seconds with default None so existing 3-field constructions stay valid); cell_progress ~910-946 (parses only the NEWEST checkpoint via _checkpoint_number numeric ordering; extend to track the two newest + their trainer_state.json file mtimes); entries_progress ~978-1016 (passthrough — its best-by-step pick ignores eta); format_eta ~1282 returns the ≈-prefixed human form (services CJK-free; reuse verbatim); _SCAN_DIR_ENTRY_CAP 512, _CHECKPOINT_PREFIX "checkpoint-", RESUME_MARKER imported from run_sweep.
- tui/services/sweep_launcher.py — kill_sweep ~876-907 (killpg SIGTERM -> poll-with-grace -> SIGKILL escalation; returns signalled / already_dead / noop; noop = unknown root = CLI-launched); live_sweeps ~931-959 (prunes dead entries; returns resolved roots). The screen already holds this object as its _launcher; MonitorLauncherProtocol does NOT declare kill_sweep — use the tolerant getattr seam, never a Protocol change (a required method would ty-flag every existing fake).
- tui/app.py — post-v0z: QuitConfirmModal ~226-273, ExitModal ~169-223 (k=kill_quit — the review item), BINDINGS ~460-482 (q, ctrl+q declared mirror, ?, L), action_quit ~986-1040 (the three legs — Q routes here, do NOT modify), _binding_rows ~1054-1079 (ctrl+q/ctrl+c manual rows — the Q row joins after ctrl+c), remap_binding_descriptions ~378-425 (walks every BINDINGS-owning class on the L toggle — the new k keycap remaps automatically).
- tui/strings.py — APP_ chrome block ~145-176 (APP_Q_LABEL beside APP_CTRLQ_LABEL; APP_* registers via _t with no separate tripwire); MON_ block from ~1561 (the seven MON_KILL_* constants land in the MON block with a 261016-vxr comment; the keycap mirrors MON_FAILURES_KEYCAP/MON_LOG_KEYCAP style; the [Y]/[N] pair mirrors LNC_GATE_CONFIRM/LNC_EXIT_CONFIRM).
- tests/tui/test_strings_phase11.py — EXPECTED_MON_CONSTANTS ~90-143 (closed bidirectional inventory: test_cfg_lnc_mon_inventory_complete_no_unlisted_constants fails on ANY unlisted MON_ constant — all seven new names MUST join the tuple; plain strings, RED-safe).
- tests/tui/test_pilot_monitor.py — FakeMonitorService ~144-272 (progress dict {(model, task): CellProgress} at entries_progress ~223); FakeMonitorLauncher ~275-324 (grows a scripted kill_sweep for the new tests); the exact progress-cell pins that MUST be amended for the ETA segment: ~615-618 (wide "300/1000 30% ███·······" gains the trailing eta segment — "—" in that fixture) and ~696 (narrow "5/10 50%" likewise); the indeterminate pin ~671-674 stays byte-identical.
- tests/tui/test_pilot_run_config.py — the v0z exit-triple section ~1497-1700 (FakeLauncherService ~240, _app ~478, _open_run_config ~513, QuitConfirmModal function-local imports — the Q tests join this section; the run-config screen carries compact Inputs for the focused-Input legs).
- tests/tui/test_snapshots.py — _MonitorGoldenService ~456-509 has NO entries_progress method (the tolerant seam) — the golden running row renders the indeterminate constant, which is why the ETA suffix cannot touch the goldens; the k keycap DOES (BottomBar projects screen BINDINGS, nav.py ~219-238); make snapshot-update regenerates from the frozen factories (Makefile ~132, maintainer-only by D-03).
- Test baseline: at planning time exactly 7 failed / 1818 passed (membership: test_determinism 1, test_schemas 5, test_services_run_config 1) + v0z's ~10 landing before this task runs — read the real counts at execution; the 7F MEMBERSHIP is the invariant. node 26/26. The worktree M on tests/tui/__snapshots__/run_config.svg is the 261016-poa D-03 review artifact — preserve byte-identically (the v0z precedent).
- Rulings that bind: EHC-2 (enter can never confirm a Y/N gate — extends to the kill confirm), EHC-3 (single-GPU guard gates LAUNCHES only — the kill path never consults it), D-03 (goldens maintainer-reviewed — regenerate, never commit), the i18n single-home + bilingual-pair + closed-inventory locks, zh terminology (停止/训练任务/控制台 are approved-family; no retired phrasings), WR-02/WR-03 (run-id-tagged worker messages; a post-confirm worker death surfaces, never a silent no-op), plain commits / no push, tui/ scope only.
- Assumption-delta note (advisory hook, recorded per the contribution fragment): this batch adds a SECOND confirmation modal family member (KillConfirmModal beside v0z's QuitConfirmModal) — decision add-alongside, deliberately: stop-training and quit-console are distinct operator acts with distinct copy/keycaps; promoting one generic confirm would erase the EHC-2 launch-vs-kill distinction LaunchConfirmModal already documents. No identity-model change.

Item-2 review deliverable (no pre-change, per the coordinator): record in the SUMMARY (a) the App-level ExitModal k=kill_quit context review — k consistently means kill in both surfaces; ExitModal IS itself the quit confirmation (its enter/k/esc triple answers the quit the operator already invoked; the live-sweep quit carries no double confirm by v0z design), while slot-5 k starts a NEW destructive act needing its own confirm — consistent under the EHC-2 philosophy; and (b) the probe finding that v0z's ctrl+q (priority=True) fires while ANY modal is top (P9 mechanism: the priority walk uses the full _binding_chain, not the modal-cut chain), so ctrl+q pressed inside e.g. the HelpModal or ExitModal re-runs action_quit and stacks a second modal — RECOMMEND a follow-up guard (e.g. action_quit returning when an ExitModal/QuitConfirmModal is already top), NOT changed in this task (surgical scope; v0z-owned surface mid-flight).
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: RED — the failing test surface for all three items</name>
  <files>tests/tui/test_services_sweep_monitor.py, tests/tui/test_pilot_monitor.py, tests/tui/test_pilot_run_config.py, tests/tui/test_pilot_env_check.py, tests/tui/test_pilot_nav_shell.py, tests/tui/test_pilot_selection.py, tests/tui/test_strings_phase11.py</files>
  <precondition>v0z has landed: .planning/quick/261016-v0z-guard-ctrl-q-exit-route-the-inherited-te/261016-v0z-SUMMARY.md exists and v0z's commits are at HEAD (the serial constraint); snapshot the worktree's tests/tui/__snapshots__/run_config.svg bytes (cp to the task dir) before any change.</precondition>
  <behavior>
    Service tier (tests/tui/test_services_sweep_monitor.py — real tmp_path fixture dirs, the established pattern):
    - Test 1: two checkpoint dirs (numeric suffixes, e.g. checkpoint-500/checkpoint-1000) each with a valid trainer_state.json; os.utime the two trainer_state.json files to controlled mtimes (e.g. 100s apart, steps 500 apart, max_steps 2000) -> cell_progress returns step/max/percent AND eta_seconds == the computed remaining/rate (500 steps remaining over 5 steps/s -> 100.0).
    - Test 2: only ONE checkpoint -> eta_seconds is None.
    - Test 3: two checkpoints but IDENTICAL trainer_state mtimes (or equal steps) -> None.
    - Test 4: second-newest trainer_state damaged/unparseable -> newest steps still parse, eta None.
    - Test 5: newest global_step >= max_steps (run at/past its end) -> eta None.
    - Test 6: entries_progress passthrough — a running seed's CellProgress carries the computed eta_seconds.
    - Test 7 (regression pin, expected GREEN): every existing cell_progress/entries_progress test passes unmodified (the eta default None keeps old assertions true).
    Pilot ETA render (tests/tui/test_pilot_monitor.py):
    - Test 8: running entry with CellProgress(step=300, max_steps=1000, percent=30, eta_seconds=1800.0) -> the wide progress cell is the existing grammar + the format_eta(1800.0) segment; a second running entry with eta_seconds=None -> trailing dim "—".
    - Test 9 (AMEND the two exact pins): ~615-618 wide cell gains the trailing "—" (fixture has no eta); ~696 narrow cell becomes steps text + "—" (bar still dropped).
    - Test 10 (regression pin, expected GREEN): the indeterminate pin ~671-674 passes unmodified.
    Pilot k-kill (tests/tui/test_pilot_monitor.py; FakeMonitorLauncher gains kill_outcomes scripting + kill_calls recording):
    - Test 11: attached root in live_sweeps(); press k -> KillConfirmModal on top (function-local import from tui.screens.monitor), message == MON_KILL_CONFIRM (function-local strings import), border title names the root; press enter -> still the modal, kill_sweep NOT called (EHC-2); press n -> back to the monitor, not called; reopen with k, press esc -> not called; reopen, press y -> the worker called kill_sweep exactly once with the RESOLVED attached root, the app did NOT exit, the MON_KILL_TOAST notify fired.
    - Test 12: scripted already_dead -> MON_KILL_TOAST_DEAD; scripted noop -> MON_KILL_UNAVAILABLE; a raising kill_sweep -> the MON_KILL_FAILED error toast (never a silent no-op).
    - Test 13: attached root NOT in live_sweeps() (CLI-launched) -> k surfaces MON_KILL_UNAVAILABLE, NO modal pushed, kill_sweep never called.
    - Test 14: no attached root -> k is silent (no modal, no toast); below-min-grid (resize 60x20) with a live attached root -> no modal.
    - Test 15 (EHC-3 pin): a fake whose single_gpu_launch_blocked() returns live roots AND kill_sweep records -> k -> y still kills (the guard is never consulted on the kill path).
    - Test 16: kill_sweep blocks (a threading.Event gate, the responsiveness precedent) -> the UI stays responsive / the call lands off the event loop (assert via the gate + posted message).
    Pilot Q (tests/tui/test_pilot_run_config.py — the v0z exit-triple section, reuse _app/FakeLauncherService):
    - Test 17: focus an Input on the run-config screen; press "Q" -> QuitConfirmModal on top (no live sweep), app._exit False, AND the Input value is UNCHANGED (Q never typed); press y -> app._exit True.
    - Test 18: same with a live sweep fake (FakeLauncherService live=(root,)) -> Q opens ExitModal (the v0z live leg), input unchanged, not exited.
    - Test 19: press q on the same focused Input -> the Input value gains "q" and NO modal (lowercase semantics byte-unchanged).
    - Test 20 (modal guard): with QuitConfirmModal already open (via q), press Q -> still exactly one modal on the stack, not exited; with an Input-bearing modal top (e.g. the E2/path modal or a pushed Input modal), press Q -> the Q TYPES into the modal input (value gains "Q"), no quit, no second modal.
    - Test 21: below-min-grid + Q -> nothing (not exited, no modal).
    Help rows + inventory:
    - Test 22 (three files): each exact help-row pin (test_pilot_env_check ~879, test_pilot_nav_shell ~657, test_pilot_selection ~1205 — as landed by v0z) gains, after the ctrl+c row, APP_HELP_ROW.format(key="Q", label=APP_Q_LABEL) (function-local imports — RED-safe).
    - Test 23: the monitor help (open ? on the monitor screen) contains the k row (MON_KILL_KEYCAP label) — a NEW test in test_pilot_monitor.py.
    - Test 24: EXPECTED_MON_CONSTANTS gains the seven plain strings MON_KILL_KEYCAP, MON_KILL_TITLE, MON_KILL_CONFIRM, MON_KILL_TOAST, MON_KILL_TOAST_DEAD, MON_KILL_UNAVAILABLE, MON_KILL_FAILED.
  </behavior>
  <action>
    Write every test BEFORE any production change (the 261016-poa/v0z RED precedent). All new-constant and new-class imports FUNCTION-LOCAL inside test bodies (module-top imports of not-yet-existing names break collection and falsify the RED evidence). Reuse the existing fakes: FakeMonitorService(progress={...: CellProgress(..., eta_seconds=...)}) — constructing with the not-yet-existing kwarg raises TypeError, which IS the honest RED for the service lane; extend FakeMonitorLauncher with kill scripting mirroring its existing outcome-list pattern; Q tests join the v0z exit section reusing FakeLauncherService and the run-config screen's own Inputs. The mtime fixtures use os.utime on real tmp files (never monkeypatched clocks). Do NOT touch the unmodified regression pins (tests 7, 10, and every existing rerun/exit test). Confirm the expected split: RED = 1-6, 8, 9, 11-18 (the Q-over-Input legs 17/18 — Q currently types), 22, 23, 24; GREEN = 7, 10, 19 (q types today), 20 (Q in a modal already does nothing/types), 21. Record RED-EVIDENCE.json in this task directory (command, exitCode, targetTests, expected vs actual per failure, semanticAssessment, redCommit hash). Commit PLAIN: test(261016-vxr): RED — entry ETA, slot-5 k kill confirm, uppercase Q any-focus exit.
  </action>
  <verify>
    <automated>.venv/bin/python -m pytest tests/tui/test_services_sweep_monitor.py tests/tui/test_pilot_monitor.py tests/tui/test_pilot_run_config.py tests/tui/test_strings_phase11.py -q 2>&1 | tail -5</automated>
  </verify>
  <done>RED committed with evidence: the ETA/kill/Q tests fail for the planned reasons (TypeError on eta_seconds, ImportError on KillConfirmModal/constants, Q typing instead of quitting, missing help rows/inventory names); the regression pins (7, 10, 19, 20, 21 and every unmodified existing test) pass; run_config.svg snapshot recorded in the task dir; commit is plain.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: GREEN item 1 — the checkpoint-pair ETA derivation + render</name>
  <files>tui/services/sweep_monitor.py, tui/screens/monitor.py</files>
  <behavior>
    - Task-1 tests 1-10 turn green; the existing sweep_monitor suite stays green.
  </behavior>
  <action>
    In tui/services/sweep_monitor.py: extend CellProgress with eta_seconds: float | None = None (frozen dataclass; the default keeps every existing 3-field construction valid) documented as the checkpoint-pair estimate (None = underivable, the screen's honest dash). Extend cell_progress to track the TWO newest checkpoint dirs (the existing _checkpoint_number numeric ordering; keep the _SCAN_DIR_ENTRY_CAP bound), parse the newest trainer_state exactly as today, and derive eta ONLY when ALL hold: both trainer_state.json files parse as dicts, both global_step values are non-bool ints, step_new > step_old, the two trainer_state.json FILE mtimes differ (mtime_new > mtime_old), max_steps parses and exceeds step_new; eta_seconds = (max_steps - step_new) / ((step_new - step_old) / (mtime_new - mtime_old)). No clamping and no tee-log parsing — honesty over motion (a stalled run shows a large honest ETA; a resumed run's first interval is simply underivable). Tolerant end to end (any failure -> eta None, never a raise). Update the module docstring's progress paragraph. entries_progress is a pure passthrough (its best-by-step pick already carries the field).
    In tui/screens/monitor.py (_entry_progress_cell): in the parsed-progress branch append one segment after the existing text/bar — format_eta(progress.eta_seconds) when eta_seconds is not None, else Text(_DASH) styled _STYLE_SKIPPED (dim); keep the segment in the NARROW form (the narrow branch keeps steps text + eta, still dropping only the bar); the indeterminate and non-running branches are byte-untouched. Zero new operator copy (format_eta is CJK-free data; _DASH is the existing table symbol) — zero strings.py changes for this item.
    Run the Task-1 service + monitor ETA tests, then the whole tests/tui/test_services_sweep_monitor.py + tests/tui/test_pilot_monitor.py lanes. Commit PLAIN: feat(261016-vxr): entry ETA from checkpoint-pair step cadence, honest dash when underivable.
  </action>
  <verify>
    <automated>.venv/bin/python -m pytest tests/tui/test_services_sweep_monitor.py tests/tui/test_pilot_monitor.py -q 2>&1 | tail -3</automated>
  </verify>
  <done>Running entries with two live checkpoints render the ≈-prefixed remaining time; single-checkpoint/degraded/past-end rows render the dim dash; indeterminate and non-running cells byte-identical; narrow form keeps text+eta without the bar; the whole monitor + sweep_monitor lanes green.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: GREEN items 2+3 — KillConfirmModal + k binding, Q on_event intercept, strings</name>
  <files>tui/screens/monitor.py, tui/app.py, tui/strings.py</files>
  <behavior>
    - Every remaining Task-1 test (11-24) turns green; the whole tests/tui lane green.
  </behavior>
  <action>
    tui/strings.py first (tests consume constants). Seven bilingual _t constants in the MON block (a 261016-vxr comment naming the consumers): MON_KILL_KEYCAP (zh 停止 / en Kill — the keycap style of MON_FAILURES_KEYCAP), MON_KILL_TITLE (zh 停止训练 — {root} / en Stop training — {root}), MON_KILL_CONFIRM (zh 确认停止当前训练任务？— [Y] 停止 / [N] 取消 / en Stop the current training task? — [Y] stop / [N] cancel — the coordinator's copy verbatim, the [Y]/[N] pair of LNC_EXIT_CONFIRM), MON_KILL_TOAST (✓ 已发送停止信号：{root} / ✓ Stop signal sent: {root}), MON_KILL_TOAST_DEAD (任务已先行结束：{root} / Already finished before the stop: {root}), MON_KILL_UNAVAILABLE (无法停止：{root} 上没有本控制台启动的运行中训练 / Cannot stop: no live TUI-launched sweep at {root}), MON_KILL_FAILED (✗ 停止失败: {error} / ✗ stop failed: {error}). One APP_ chrome constant beside APP_CTRLQ_LABEL: APP_Q_LABEL (zh 退出（任意焦点生效） / en Quit (works at any focus)). Zero Chinese literals anywhere else (i18n single-home).
    In tui/screens/monitor.py: KillConfirmModal(ConfirmModal) beside FailuresModal (import ConfirmModal from tui.screens.selection) — the LaunchConfirmModal idiom with kill naming: ClassVar BINDINGS add Binding("y", "confirm_kill", show=False) and Binding("n", "dismiss", show=False) (escape inherited from ConfirmModal); action_confirm overridden to a documented no-op (EHC-2: enter can never confirm a kill); action_confirm_kill dismisses then fires the on_confirm callback; the border title is MON_KILL_TITLE.format(root=...) set in on_mount; class docstring records y-only/n-esc/enter-inert and that this modal NEVER exits the console. MonitorScreen.BINDINGS gains Binding("k", "kill_running", S.MON_KILL_KEYCAP) immediately after the r entry. action_kill_running: return when below_minimum_grid or no attached root (the action_show_failures precedent); resolve root_key = str(self._attached_root); when root_key is NOT in self._launcher.live_sweeps() surface the MON_KILL_UNAVAILABLE toast and return (never open a confirm the channel cannot execute); otherwise push KillConfirmModal(message=S.MON_KILL_CONFIRM, root=..., on_confirm=worker kick). The kill executes in a NEW @work(exclusive=True, thread=True, group="mon-kill", exit_on_error=False) worker (kill_sweep blocks up to the 2s grace — never on the event loop) reaching the launcher through the TOLERANT getattr seam (kill_getter = getattr(self._launcher, "kill_sweep", None); absent -> the noop outcome string), posting a run-id-tagged KillFinished message (bump a _kill_stage_id per the WR-02 idiom); the handler maps signalled -> MON_KILL_TOAST, already_dead -> MON_KILL_TOAST_DEAD, noop -> MON_KILL_UNAVAILABLE; an exception posts KillFailed -> the MON_KILL_FAILED error toast (WR-03). The single-GPU guard is NEVER consulted here (kill is the EHC-3 remedy — comment cites the ruling).
    In tui/app.py: add from textual import events to the textual imports. Override on_event on DnallmMarkTui with the probe-pinned contract (P10-P14): when the event is an events.Key with event.key == "Q", a screen is mounted, and not self.screen.is_modal — await self.action_quit() (the v0z three-leg chain, unmodified) and RETURN WITHOUT calling super (the key is consumed: never forwarded, never typed); every other event delegates to super().on_event(event). The docstring records the probe facts (the consume-key filter that defeats a printable priority Binding over a focused Input; the P9 modal-stacking reason Q is NOT a BINDINGS entry; the base-screen-only typing sacrifice per the maintainer's 方案 a; modals exempt so an E2' phrase/path containing Q stays typeable). In _binding_rows append ("Q", S.APP_Q_LABEL) immediately after the ("ctrl+c", ...) row (the same manual-row pattern, show=False-equivalent surface).
    Run the full tests/tui lane; then make lint and make typecheck (the on_event signature must match the App base: async, events.Event, -> None; the new ClassVar list stays RUF012-clean). Commit PLAIN: feat(261016-vxr): slot-5 k kill confirm via launcher channel + uppercase Q any-focus guarded exit.
  </action>
  <verify>
    <automated>.venv/bin/python -m pytest tests/tui -q 2>&1 | tail -3 && make lint && make typecheck</automated>
  </verify>
  <done>Every Task-1 test green; whole tests/tui lane green; ruff + ty green; k opens the y-only confirm for a live attached TUI sweep and SIGTERMs it off-loop without exiting; CLI-launched/absent/below-grid degrade honestly; Q quits from any base-screen focus through the v0z chain, stays inert under modals, q unchanged; help modal carries the Q row and the monitor k row; all seven MON_KILL_* constants + APP_Q_LABEL bilingual and inventoried.</done>
</task>

<task type="auto">
  <name>Task 4: Full gates, D-03 golden regeneration, review deliverable, bookkeeping</name>
  <files>.planning/STATE.md, .planning/quick/261016-vxr-slot-5-monitor-batch-eta-remaining-time-/261016-vxr-SUMMARY.md</files>
  <action>
    Full gates: make lint, make typecheck, make test — the pytest lane lands at EXACTLY the 7F baseline membership (test_determinism 1, test_schemas 5, test_services_run_config 1; read the actual pass count — v0z added tests first) with zero new failures and every Task-1 test passing; node --test 26/26.
    Golden D-03 path: run make snapshot-update, then verify git status over tests/tui/__snapshots__/ shows EXACTLY three modifications — the pre-existing run_config.svg (byte-identical to the Task-1 snapshot; cmp it) PLUS monitor_running.svg and monitor_empty.svg (the k keycap row; the ETA change contributes nothing — their running rows are tolerant-seam indeterminate). Do NOT commit any SVG. Run .venv/bin/python -m pytest tests/tui/test_snapshots.py -q — green against the regenerated on-disk SVGs. State explicitly in the SUMMARY: the committed tree fails test_snapshots until the maintainer reviews and commits the two regenerated monitor SVGs (the D-03 flow).
    Review deliverable (the item-2 顺审, no pre-change): in the SUMMARY record (a) the ExitModal k=kill_quit context review — k means kill in both surfaces; ExitModal is itself the quit confirmation (enter/k/esc answer the already-invoked quit; no double confirm by v0z design) while slot-5 k starts a new destructive act needing its own confirm; (b) the probe finding that v0z's ctrl+q (priority=True) fires while any modal is top (the priority walk uses the full _binding_chain, not the modal-cut chain — P9), enabling modal stacking, with the recommended follow-up guard; explicitly NOT changed here.
    Bookkeeping: append the 261016-vxr row to the Quick Tasks Completed table in .planning/STATE.md (description: slot-5 批 — 训练行 ETA（checkpoint 对推算，不可推显 —）+ k 停止确认（Y-only，不退 console）+ 大写 Q 任意焦点退出（on_event 拦截，modal 内惰性）; date 2026-10-16; commit = the Task 3 short hash; directory = this task dir). Write 261016-vxr-SUMMARY.md covering: the ETA data-source decision (probe evidence: no timestamps in trainer_state; the tee tqdm fragility; the checkpoint-pair choice), the priority-binding probe results P1-P14 (the consume-key filter, the P9 modal finding, the adopted on_event seam and its documented typing sacrifice), the kill-path design (tolerant seam, off-loop worker, EHC-3 non-interference), per-fix file:line references, the RED evidence summary, the golden-integrity proof output (the three-SVG git status + the run_config.svg byte-compare), and the exact final gate numbers. Commit PLAIN: docs(261016-vxr): quick-task summary + STATE row. Do NOT push.
  </action>
  <verify>
    <automated>make test 2>&1 | tail -6 && git status --porcelain tests/tui/__snapshots__/ && .venv/bin/python -m pytest tests/tui/test_snapshots.py -q 2>&1 | tail -2</automated>
  </verify>
  <done>make lint + typecheck + test green at the exact 7F baseline membership with zero new failures and node 26/26; exactly run_config.svg (byte-preserved) + the two regenerated monitor SVGs modified and all uncommitted; snapshot suite green against the regenerated SVGs; the review deliverable recorded; STATE row + SUMMARY committed plain; nothing pushed.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| keyboard input -> app/screen action dispatch | the exit and kill surfaces: Q intercept, k binding, confirm-modal keys |
| console process -> spawned sweep process groups | kill_sweep signals a whole process group (killpg) — a wrong-root signal destroys an unrelated run |
| checkpoint artifacts -> displayed numbers | untrusted on-disk JSON feeds the ETA derivation shown to the operator |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-261016vxr-01 | DoS (availability of running sweeps) | action_kill_running -> kill_sweep killpg | high | mitigate | y-only confirm (enter structurally inert, EHC-2); the target is the RESOLVED attached root matched against launcher.live_sweeps() (the launcher keys its registry by resolved root and signals only its own registered Popen group); attached-but-not-live refuses BEFORE the confirm; tests pin the exact root passed |
| T-261016vxr-02 | Tampering (integrity of displayed numbers) | cell_progress ETA derivation | medium | mitigate | strict validity gates (both trainer_states parse, Δstep > 0, Δmtime > 0, max_steps > step); every failure degrades to the dim dash, never a fabricated estimate; tolerant parsing never raises into the cadence |
| T-261016vxr-03 | DoS (typing availability) | Q on_event intercept | low | accept | the maintainer's 方案 (a) tradeoff: capital Q is reserved on base screens (cannot be typed into base-screen Inputs); modals are exempt so phrase/path entry keeps Q; documented in the code and reported in the SUMMARY |
| T-261016vxr-SC | Tampering | package installs | high | mitigate | no package installs in this task (tui/ + tests only, zero dependency changes) — the legitimacy gate is not triggered; recorded per template |
</threat_model>

<verification>
- VXR-1: two-checkpoint running entries show the ≈ remaining time; every underivable shape shows the dim dash; the indeterminate/non-running/narrow render rules hold; the service derivation is pinned on real tmp fixtures with controlled mtimes.
- VXR-2: k opens the y-only kill confirm only for a live TUI-launched attached sweep; y SIGTERMs the group off the event loop and the console stays up; noop/already-dead/exception/CLI-launched/no-attach/below-grid each degrade to their designed honest surface; the single-GPU guard is provably not consulted.
- VXR-3: Q quits from any base-screen focus (Input focus included, never typed) through the v0z chain; Q is inert under every modal (no stacking, capital Q still typeable in modal inputs); lowercase q semantics byte-unchanged; help modal documents Q and slot-5 k bilingually.
- VXR-4: ruff + ty green; full pytest at the exact 7F membership with zero new failures and every new test green; node 26/26; goldens — only the two monitor SVGs regenerated (uncommitted, D-03-reported), run_config.svg byte-preserved; plain commits, no push.
</verification>

<success_criteria>
- The maintainer, watching a long sweep on slot 5, sees an honest remaining-time estimate that never guesses, can stop the attached training with two deliberate keystrokes without leaving the console, and can always quit — even from inside a filter input — with a confirmation step on every path.
- The ExitModal k context review and the ctrl+q-over-modal probe finding are delivered as review notes (no pre-change).
- RED-first discipline with recorded evidence; all gates green at the exact baseline membership; the D-03 golden artifacts staged for maintainer review, never committed by the executor.
</success_criteria>

<output>
Create .planning/quick/261016-vxr-slot-5-monitor-batch-eta-remaining-time-/261016-vxr-SUMMARY.md when done
</output>
