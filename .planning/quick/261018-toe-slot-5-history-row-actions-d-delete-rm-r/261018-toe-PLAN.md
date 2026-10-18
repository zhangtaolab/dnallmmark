---
phase: quick-261018-toe
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tui/services/sweep_monitor.py
  - tui/services/sweep_launcher.py
  - tui/screens/monitor.py
  - tui/screens/nav.py
  - tui/strings.py
  - tests/tui/test_services_sweep_monitor.py
  - tests/tui/test_services_sweep_launcher.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_strings_phase11.py
  - tests/tui/test_pty_driver.py
autonomous: true
requirements: ["UX-slot5-history-row-actions"]
user_setup: []

estimate:
  tokens: 110000
  raw_tokens: 55000
  tasks: 3
  confidence: low

must_haves:
  truths:
    - "On the History tab with a focused row, [d] opens a strong delete confirm naming the FULL root path and the 训练项 count; ONLY y/Y confirms, n/N/esc cancel, enter is structurally inert (the KillConfirmModal contract matched exactly)"
    - "A live/running root can NEVER be deleted and never opens the delete modal: screen-side refusal toast (scan state running OR registry live_sweeps, covering probed CLI roots and dual-presence badge rows) plus a worker-side re-check closing the confirm-to-worker race"
    - "Deletion executes rm -rf in a WORKER THREAD (never the event loop), tolerant of missing dirs; completion posts back to the loop (LogTailModal read-once precedent) as a toast plus an immediate full rescan so the row disappears; a manual-root entry is removed best-effort (tolerant)"
    - "On the History tab with a focused row, [e] re-runs the root's INCOMPLETE items: the (model, task) pairs whose fold state is failed or interrupted, over the root's own seed set — completed cells skip via the existing trainer_state.json resume markers; the confirm names the honest pairs × seeds enumeration"
    - "The E2' phrase gate applies when the incomplete set equals the full matrix — through the EXISTING launch_from_failures stage machinery, reused not duplicated (phrase re-prompt routes back through the resume launch worker)"
    - "Footer: [d]/[e] keycaps render ONLY while the History tab is active; the Running-tab footer stays byte-identical (the uncommitted monitor goldens must not change); the refresh fires on mount and tab switch ONLY, never on the 2s cadence (the rze byte-silence gates hold)"
    - "zh copy uses 训练项 (never 细胞); the [e] label is 续跑 / en resume"
    - "Single-GPU serialization, env preflight, and the shared outcome toasts govern [e] exactly as they govern [f]→[r] today"
  artifacts:
    - "tui/services/sweep_monitor.py: incomplete_pairs_view (pure) + the rerun_lane alias-dir fallback leg"
    - "tui/services/sweep_launcher.py: SweepLauncher.launch_from_pairs (materialize + delegate through launch_from_failures verbatim)"
    - "tui/screens/monitor.py: DeleteConfirmModal, the [d]/[e] actions + workers + messages, MonitorServiceProtocol.delete_root / MonitorLauncherProtocol.launch_from_pairs and their MonitorBackend implementations, the per-tab footer refresh"
    - "tui/screens/nav.py: BottomBar.refresh_left_pairs + KeycapsStatic.refresh_pairs (the only justified out-of-scope-list file)"
    - "tui/strings.py: 11 new bilingual MON_ constants, mirrored in the test_strings_phase11.py inventory"
    - "tests: tier-1 service tests for the two new seams; Pilot tests for both flows over extended fakes; 2 new pty spawns (delete flow end-to-end, resume confirm + cancel)"
  key_links:
    - "[e] incomplete set <- sweep_monitor.incomplete_pairs_view(root) over the live-evidence-threaded cells_view (dead root = strict-miss empty pair set -> non-terminal cells derive interrupted, the uwr leg)"
    - "[e] launch <- SweepLauncher.launch_from_pairs -> state-dir pairs file -> launch_from_failures (gate + composition + child --from-failures validation all reused); seeds <- the ONE shared derive_rerun_seeds over the root's cell rows; lane <- sweep_monitor.rerun_lane"
    - "[d] execution <- MonitorServiceProtocol.delete_root (adapter-tier impl in MonitorBackend — sweep_monitor stays a pure scanner) called inside a @work(thread=True) mon-delete worker"
    - "[d]/[e] focus <- _focused_root() on the History tab (row-key identity); silent refusal off-tab or without selection (the [f]/[t] precedent)"
    - "Footer <- BottomBar.refresh_left_pairs(binding_row(BINDINGS) minus d/e unless history active), driven from on_mount + action_switch_tab only"
---

<objective>
Slot-5 History-tab row actions (maintainer-approved 2026-10-18 21:21): [d] 删除 (delete a history run's output root behind a strong y-only confirm, fail-safe against live roots, executed off the event loop, followed by a rescan) and [e] 续跑 (one-click resume of a dead run's incomplete items — failed + interrupted cells — reusing the existing rerun pipeline's confirm/preflight/launch/E2' stages), plus per-active-tab footer keycaps.

Purpose: History rows are currently read-only; the maintainer ruled the two destructive/lifecycle actions into the slot-5 surface with the repo's exit-family confirm idioms and the honesty disciplines (live refusal, honest enumeration counts, worker-thread mutation).

Output: two new service seams (incomplete-pairs derivation, pairs-materializing launch), the DeleteConfirmModal + both screen flows, per-tab footer mechanism, 11 strings constants, extended Pilot/pty/service/string-inventory tests. No real GPU launches in any test lane.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
tui/screens/monitor.py          (the screen being extended — read fully: BINDINGS, _focused_root, request_rerun/_rerun_pipeline/_run_rerun_* workers + message handlers, KillConfirmModal, LogTailModal, on_mount/action_switch_tab)
tui/services/sweep_launcher.py  (launch_from_failures + _from_failures_refusal + REFUSAL_STAGE_* — the machinery [e] reuses)
tui/services/sweep_monitor.py   (cells_view/entry_fold/rerun_lane/manual_roots/remove_manual_root — read-only reuse + two additions)
tui/screens/selection.py        (ConfirmModal/LaunchConfirmModal — the y-only idiom to match; PathInputModal)
tui/screens/nav.py              (BottomBar/KeycapsStatic/binding_row/keycaps_text — the footer seam)
tui/strings.py                  (MON_ block ~1612-1866: MON_RERUN_CONFIRM/MON_KILL_* shapes to mirror)
tests/tui/test_pilot_monitor.py (FakeMonitorService/FakeMonitorLauncher fixtures, _app/_open_monitor/_settle helpers)
tests/tui/test_pty_driver.py    (the permanent pty lane — _spawn_tui/_fabricate_running_root/_boot helpers)
</context>

<seam_decision>
The [e] composition seam (the maintainer's investigate-and-document item): **option (a) — in-memory incomplete pairs derived from cells_view states, MATERIALIZED as a failures-shaped pairs file and routed through the EXISTING launch_from_failures verbatim.** Option (b) (re-launch the original matrix relying on resume-skip) is rejected as unimplementable-honestly: an interrupted root has NO manifest (the manifest lands only at sweep end), so the "original matrix" is not recoverable from disk — only the discovered incomplete cells are. Option (a) matches the ruling's incomplete-set definition exactly (failed + interrupted pairs; completed cells inside those pairs skip via the existing trainer_state resume markers — the ruling's own parenthetical). Materializing to a file (not extending run_config.compose_from_failures_argv to take pairs) keeps run_config.py untouched and reuses the driver's own --from-failures validation in BOTH the gate (_from_failures_refusal re-reads the file via run_sweep.load_failure_pairs) and the child — zero duplicated gate logic, and the E2' full-matrix phrase stage fires over the materialized pairs exactly as the ruling demands. The file lands under the XDG STATE root (settings.state_dir()/resume/resume_pairs_{rootname}.json, settings.atomic_write — the monitor_roots/tee precedent), NEVER inside the output root (sweep_failures.json is the driver's own end-of-sweep artifact; overwriting it corrupts rerun_lane and WR-06 stale-manifest semantics).
</seam_decision>

<scope_justification>
Production scope per the quick-task constraint is monitor.py + the two services + strings.py. Two files outside that list are touched, both explicitly justified:

1. **tui/screens/nav.py** (~15 lines): the per-active-tab footer ruling requires the shared BottomBar's left keycap segment to be refreshable (KeycapsStatic.refresh_pairs + BottomBar.refresh_left_pairs). The alternative — the monitor screen reaching into another widget's children to remount them — is strictly worse architecture for the same diff size. The initial-mount projection and every other screen are byte-unchanged.
2. **tests/tui/test_strings_phase11.py**: the EXPECTED_MON_CONSTANTS inventory tripwire (the 10-03 W1-mirror discipline) must list every new MON_ constant or the suite fails by construction — not touching it is not an option.

Test scope beyond the two named files: **tests/tui/test_services_sweep_monitor.py + tests/tui/test_services_sweep_launcher.py** are the canonical tier-1 homes of the two new pure service seams (the repo's tier separation); squeezing service-tier tests into the Pilot lane would break that discipline.

NOT touched: the 3 uncommitted D-03 SVGs in tests/tui/__snapshots__/ (the Running-tab footer stays byte-identical because d/e are filtered out there — the goldens must remain valid UNMODIFIED; never run make snapshot-update), pipeline/*, tui/app.py, run_config.py.
</scope_justification>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Service seams — incomplete_pairs_view, rerun_lane alias fallback, launch_from_pairs</name>
  <files>tui/services/sweep_monitor.py, tui/services/sweep_launcher.py, tests/tui/test_services_sweep_monitor.py, tests/tui/test_services_sweep_launcher.py</files>
  <behavior>
    - incomplete_pairs_view(root, live_pairs=None): distinct (model, task) pairs — model identity VERBATIM (alias names included) — over cells_view rows whose entry_fold state is failed OR interrupted; sorted deterministically; completed/skipped/queued/running rows contribute nothing; live_pairs threads the live evidence exactly as cells_view does (a dead root's strict-miss empty set is what derives interrupted).
    - rerun_lane(root): unchanged when the manifest or failures file speaks; NEW fallback leg — when peft is still "none" after the failures loop, the discovered model-dir names' "+lora"/"+ia3" suffixes (the same two-suffix vocabulary run_sweep.load_failure_pairs strips) recover the lane for interrupted alias roots; config_variant stays manifest-only (head/probe/curve are not dir-recoverable — honest "none", documented).
    - SweepLauncher.launch_from_pairs(pairs, seeds, output_root, peft="none", config_variant="none", phrase=None, run_config_service=None, spawner=None, clock=None): writes the pairs file under settings.state_dir()/"resume"/f"resume_pairs_{Path(output_root).name}.json" as a JSON list of {"model", "task"} entries (adding "base_model" with the stripped base when the model carries a +lora/+ia3 suffix — the driver's own failures-entry shape), then DELEGATES to self.launch_from_failures(path, ...) — single-GPU stage-0, official-keys, the E2' phrase gate over the pairs×seeds effective matrix, composition, and spawn all reused verbatim.
    - A full-matrix incomplete set over >= 3 seeds refuses at the phrase stage exactly like a complete failures manifest (proven by test).
    - The pairs file is written BEFORE delegation and NEVER deleted after spawn (the child reads it at startup; per-root naming bounds growth; a same-root re-[e] is blocked by the live-root/single-GPU guards before it could overwrite a file a live child still reads).
  </behavior>
  <action>
    (1) sweep_monitor.py: add incomplete_pairs_view next to cells_view — iterate cells_view(root, live_pairs=live_pairs), fold each row via the existing entry_fold, keep rows whose state is CELL_FAILED or CELL_INTERRUPTED, collect sorted distinct (row.model, row.task). Module docstring gains one line (the function reads; the pure-scanner declaration is untouched — deletion deliberately does NOT live here).
    (2) sweep_monitor.py rerun_lane: after the existing failures loop, when peft is still "none", scan the root's direct model-dir names for the "+lora"/"+ia3" suffixes over run_config.PEFT_MODES minus "none" (reuse the suffix-derivation shape the function already uses on failures entries); first match wins; keep every existing branch byte-identical when the manifest/failures already speak.
    (3) sweep_launcher.py: add RESUME_PAIRS_DIR_NAME = "resume" near TEE_DIR_NAME; add the launch_from_pairs method per <behavior> — settings.atomic_write (mkdir the resume dir first, the state_dir() logs precedent), base_model derivation mirrors run_sweep.load_failure_pairs' removesuffix chain, then full delegation to launch_from_failures with every kwarg threaded. Docstring documents the seam decision (option (a), why (b) is impossible for interrupted roots, why the file lives under the state root).
    (4) tests/tui/test_services_sweep_monitor.py: pin (a) incomplete pairs over a tmp tree with failed + interrupted + completed + skipped cells (old mtimes, checkpoint residue, no manifest — the maintainer-scenario fixture family already in this file), (b) alias model names pass through verbatim, (c) rerun_lane's alias-dir fallback (a "+lora" model dir, no manifest/failures -> ("lora", "none")) and the unchanged ("none","none") for plain roots, (d) manifest-present roots keep the manifest lane byte-identically.
    (5) tests/tui/test_services_sweep_launcher.py: pin_state_dir hermeticity (the existing fixture); pin (a) launch_from_pairs writes the pairs file with the expected entry shape (alias + base_model), (b) delegates through the SAME gate — a full-matrix pairs×3-seeds set with a wrong phrase returns GateRefusal(stage=phrase) and the spawner is never called (call-count proof, the CR-01 tier-1 idiom), a correct phrase spawns with the --from-failures argv naming the state-dir file and the threaded peft/config_variant, (c) single-GPU busy refuses first. No real subprocess anywhere (the recorded spawner fake).
    TDD: write the failing service tests first, then implement.
  </action>
  <verify>
    <automated>cd /home/forrest/Github/dnallmmark && .venv/bin/python -m pytest tests/tui/test_services_sweep_monitor.py tests/tui/test_services_sweep_launcher.py -x -q && make lint typecheck</automated>
  </verify>
  <done>Both service seams green with tier-1 tests: incomplete-pairs derivation (failed+interrupted only, alias verbatim), the alias-dir lane fallback, and launch_from_pairs proven to ride the existing gate (E2' phrase refusal over the materialized pairs, spawner call counts, single-GPU order); ruff + ty clean; no textual import added to either service.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: [d] delete — strong y-only confirm, worker-thread rm -rf, live refusal, per-tab footer keycaps</name>
  <files>tui/screens/monitor.py, tui/screens/nav.py, tui/strings.py, tests/tui/test_pilot_monitor.py, tests/tui/test_strings_phase11.py, tests/tui/test_pty_driver.py</files>
  <behavior>
    - [d] on the History tab with a focused row opens DeleteConfirmModal naming the FULL root path and the training-item count (sum of per-row seed counts from one off-loop cells_view read — Test 1); without a focused History row, or on the Running tab, or below the minimum grid: silent/no-op (the [f]/[t] scoping precedent).
    - A live root NEVER opens the modal: refusal toast before it (predicate = last-scan state SWEEP_RUNNING — covers probed CLI roots and dual-presence badge rows — OR root in launcher.live_sweeps()).
    - The modal matches KillConfirmModal EXACTLY: y (show, MON_DELETE_KEYCAP keycap) + Y (hidden twin) confirm; n (show, LNC_EXIT_CONFIRM_NO exact-pair reuse) + N (hidden twin) and esc dismiss; enter lands on a documented no-op; the message's [Y]/[y]/[N]/[n] tokens render bold (the cdr Rich-Text pattern); the border title names the root.
    - y dispatches a @work(exclusive=True, thread=True, group="mon-delete") worker that (a) RE-CHECKS liveness (the confirm-to-worker race; live -> refused outcome, nothing deleted), (b) calls the NEW MonitorServiceProtocol.delete_root seam — shutil.rmtree(ignore_errors=True) implemented in MonitorBackend (adapter tier; sweep_monitor stays pure), then best-effort tolerant remove_manual_root — (c) posts DeleteFinished back to the loop (LogTailModal read-once precedent; WR-02 _delete_stage_id drops superseded posts; WR-03 exception -> DeleteFailed error toast).
    - Completion: the success toast fires and _tick_full() rescans so the row disappears (the [r] idiom, without the rescan count toast).
    - Footer: BottomBar.refresh_left_pairs + KeycapsStatic.refresh_pairs (nav.py); the monitor computes binding_row(BINDINGS) MINUS the d/e rows unless _active_tab == "history", refreshing on mount and on tab switch ONLY (never inside _render_all — the rze byte-silence gates); the Running-tab footer stays byte-identical so the uncommitted goldens remain valid untouched.
  </behavior>
  <action>
    (1) nav.py: KeycapsStatic.refresh_pairs(pairs) — set self._pairs and update(keycaps_text(pairs, budget=self.size.width, key_style=self._key_style, label_style=self._label_style)); BottomBar.refresh_left_pairs(pairs) — delegate to the #nav-left-keycaps child. No other behavior change; initial mount path byte-identical (verify test_pilot_nav_shell.py stays green unmodified).
    (2) strings.py: add MON_DELETE_KEYCAP (删除/Delete), MON_DELETE_TITLE (删除运行 — {root}/Delete run — {root}), MON_DELETE_CONFIRM (keys {root},{n}: zh 将永久删除结果目录：{root}（{n} 训练项，不可恢复）？— [Y] 删除 / [N] 取消), MON_DELETE_TOAST (✓ 已删除：{root}), MON_DELETE_FAILED (✗ 删除失败: {error}), MON_DELETE_REFUSED_LIVE (运行中的任务不可删除（先停止再删除）：{root}); 训练项 only, never 细胞. Mirror all six into test_strings_phase11.py EXPECTED_MON_CONSTANTS.
    (3) monitor.py: add Binding("d", "delete_history", S.MON_DELETE_KEYCAP) and Binding("e", "resume_history", S.MON_RESUME_KEYCAP) to BINDINGS (after the k row); the per-tab _footer_pairs()/ _refresh_footer_keys() helpers; call _refresh_footer_keys from on_mount and action_switch_tab.
    (4) monitor.py DeleteConfirmModal(ConfirmModal): clone the KillConfirmModal shape (bindings, bold-token compose, border title, inert action_confirm, action_confirm_delete) with the delete constants; a _delete_stage_id; DeleteReady/ DeleteFinished/ DeleteFailed messages (outcome vocabulary "deleted"|"failed"|"refused_live" — machine strings the handler maps to toasts).
    (5) monitor.py flow: action_delete_history (guards -> live refusal toast -> _read_delete_count worker -> DeleteReady -> handler pushes the modal) and _delete_confirmed -> _run_delete worker (live re-check -> self._service.delete_root -> post) -> handlers (deleted: toast + _tick_full; refused_live: MON_DELETE_REFUSED_LIVE; failed: MON_DELETE_FAILED; DeleteFailed: error toast). Extend MonitorServiceProtocol with delete_root and implement it in MonitorBackend (import shutil at module top; the None-launcher/None-service guards follow the existing adapter idiom).
    (6) tests/tui/test_pilot_monitor.py: extend FakeMonitorService with scripted delete_root (recorded calls + outcome list, the kill_outcomes pattern); new tests mirroring the kill-family suite: modal opens with root+count; y deletes through the seam and the rescan fires (_tick_full observable via full_calls); uppercase twins; enter inert; live root refuses with the toast and NO modal (KillConfirmModal-absence assertion shape); no-selection and off-tab silent; below-grid silent; exception -> error toast; footer keycaps present on History / absent on Running (query the KeycapsStatic content after switch). Keep the existing suite green (the BottomBar mount path unchanged).
    (7) tests/tui/test_pty_driver.py: ONE new spawn — fabricate a finished history root (a sweep_manifest.json with two planned cells under tmp, registered via _spawn_tui manual_roots), then: 5 -> running empty marker -> right arrow -> a history marker -> footer "Delete"/"resume" keycaps paint -> d -> the "Delete run —" modal marker -> y -> the "✓ deleted:" toast marker -> "No past runs yet". Bounded timeouts, close(force=True) in finally (the lane discipline). NEVER press y on any launch-family modal.
  </action>
  <verify>
    <automated>cd /home/forrest/Github/dnallmmark && .venv/bin/python -m pytest tests/tui/test_pilot_monitor.py tests/tui/test_strings_phase11.py tests/tui/test_pilot_nav_shell.py tests/tui/test_snapshots.py -x -q && .venv/bin/python -m pytest tests/tui/test_pty_driver.py -q</automated>
  </verify>
  <done>[d] flow proven end-to-end in Pilot and under a real pty (modal -> worker-thread deletion -> toast -> row gone); live roots structurally undeletable (pre-modal and in-worker checks pinned); the delete confirm matches the exit-family key contract exactly; [d]/[e] keycaps render only on the History tab with the Running-tab footer byte-identical (snapshots green UNMODIFIED); strings inventory updated; ruff + ty clean.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: [e] 续跑 — incomplete derivation, honest confirm, shared pipeline stages, E2' re-prompt routing</name>
  <files>tui/screens/monitor.py, tui/strings.py, tests/tui/test_pilot_monitor.py, tests/tui/test_strings_phase11.py, tests/tui/test_pty_driver.py</files>
  <behavior>
    - [e] on the History tab with a focused row: silent refusal off-tab/without selection/below-grid (the [d] family); a live/running root refuses with a toast before any modal (same predicate as [d]); the single-GPU guard pre-checks before the confirm (the request_rerun EHC-3 mirror — y never reached on a busy single-GPU machine).
    - The derivation runs off-loop (a @work mon-resume worker): cells_view -> sweep_monitor.incomplete_pairs_view pairs + derive_rerun_seeds((), rows) seeds + rerun_lane lane; posts ResumeReady. Empty incomplete set -> the nothing-to-resume toast, no modal, launcher never consulted.
    - The confirm is a LaunchConfirmModal with MON_RESUME_CONFIRM naming pairs × seeds = {n} and the completed-cells-skip honesty note (y starts, n/esc cancel, enter inert — unchanged family semantics).
    - y runs the SAME staged pipeline as [f]→[r]: preflight worker (env gate; EnvBlockModal on failure) -> launch worker that RE-DERIVES the pairs/seeds/lane off-loop (the WR-02/03 one-shared-derivation discipline; underivable -> refuse loudly) -> launcher.launch_from_pairs -> the SHARED RerunFinished outcome handling (GateRefusal phrase re-prompt routed back through the RESUME launch worker; single-GPU/problems error toasts; spawned success toast).
    - A phrase-stage refusal re-prompts via the existing E2PhraseModal and the typed phrase threads through the resume launch (full-matrix incomplete set -> the gate fires over the materialized pairs, Task 1's proof).
  </behavior>
  <action>
    (1) strings.py: add MON_RESUME_KEYCAP (续跑/resume), MON_RESUME_CONFIRM (keys {pairs},{seeds},{n}: zh 续跑 {pairs} 个未完成组合 × 种子 {seeds} = {n} 个训练项（已完成训练项将按标记自动跳过）？— [y] 续跑 / Esc 取消), MON_RESUME_TOAST (✓ 续跑已启动 — {cells} 训练项 → {root}), MON_RESUME_NOTHING (无未完成训练项，无需续跑：{root}), MON_RESUME_REFUSED_LIVE (运行中的任务不可续跑（同根二次启动会冲突）：{root}); mirror all five into the strings inventory.
    (2) monitor.py seam declarations: MonitorLauncherProtocol.launch_from_pairs + MonitorBackend delegation (None-launcher guard, the launch_from_failures adapter twin).
    (3) monitor.py wiring: RerunPreflightDone and RerunFinished gain a resume: bool = False constructor kwarg (existing post sites unchanged); _run_rerun_preflight threads a resume flag; a private _dispatch_rerun_launch(root, resume, run_id, phrase=None) routes to _run_rerun_launch or the NEW _run_resume_launch; the RerunPreflightDone handler and the phrase-re-prompt closure in on_monitor_screen_rerun_finished dispatch through it — the shared outcome handler's behavior is otherwise UNTOUCHED.
    (4) monitor.py resume flow: action_resume_history (guards -> live refusal -> _derive_resume worker); ResumeReady(root, pairs, seeds, lane) handler (empty pairs -> MON_RESUME_NOTHING toast; else the single-GPU pre-check then LaunchConfirmModal(MON_RESUME_CONFIRM, on_confirm=lambda: self._resume_pipeline(root))); _resume_pipeline bumps _rerun_stage_id and runs the parameterized preflight; _run_resume_launch @work(exclusive=True, thread=True, group="mon-rerun") re-derives (incomplete_pairs_view + derive_rerun_seeds over {f"{m}__{t}": row} + rerun_lane; empty -> RerunFailed(MON_RESUME_NOTHING)) then self._launcher.launch_from_pairs(pairs, seeds, root, peft, config_variant, phrase) and posts RerunFinished(..., resume=True).
    (5) tests/tui/test_pilot_monitor.py: extend FakeMonitorLauncher with recorded launch_from_pairs (the rerun_calls pattern); tests mirroring the rerun family: the confirm names pairs × seeds honestly over scripted failed+interrupted+completed cells; y reaches launch_from_pairs with the derived pairs/seeds/lane (worker re-derivation equality); empty incomplete set -> toast, launcher untouched; live root -> refusal toast, no modal; single-GPU busy refuses before the confirm; env-block modal path; E2' phrase refusal re-prompts and the typed phrase threads through the RESUME worker (the resume=True routing pin — the [f] path must still route to _run_rerun_launch); worker exception -> error toast. The existing [f]→[r] rerun tests must stay green unmodified (the resume=False default).
    (6) tests/tui/test_pty_driver.py: ONE new spawn — fabricate an interrupted history root (checkpoint residue with mtimes pushed ~2000s into the past via os.utime, no manifest, manual root) -> 5 -> right -> the history row paints -> e -> the resume confirm marker (a distinctive en substring of MON_RESUME_CONFIRM, e.g. "incomplete pairs") -> n cancels -> the history row still paints (NEVER press y — no real launches in any lane).
  </action>
  <verify>
    <automated>cd /home/forrest/Github/dnallmmark && .venv/bin/python -m pytest tests/tui/test_pilot_monitor.py tests/tui/test_strings_phase11.py tests/tui/test_services_sweep_launcher.py -x -q && .venv/bin/python -m pytest tests/tui/test_pty_driver.py -q && make lint typecheck</automated>
  </verify>
  <done>[e] proven in Pilot and pty: honest confirm, worker-thread re-derivation, launch through the materialized-pairs seam with the E2' phrase stage reused (re-prompt routes through the resume worker), live/single-GPU refusals ordered before the confirm, the [f]→[r] failures path byte-unchanged; zh copy uses 训练项 only; strings inventory, ruff, and ty green.</done>
</task>

</tasks>

<verification>
Full-lane close-out (cwd at checkout root):
- `.venv/bin/python -m pytest tests/tui/ -q` — the whole tui suite (known pre-existing environment collateral: test_storage_overview_defaults_mirror_real_consumers fails while the maintainer's live run keeps pipeline/logs/ existing — out of scope, do not chase).
- `make lint typecheck` — the standing gates.
- `git status` confirms tests/tui/__snapshots__/*.svg are UNTOUCHED (the three uncommitted D-03 goldens keep their bytes; the Running-tab footer is byte-identical by construction).
- Grep audits: no 细胞 in any new MON_ constant; zero Chinese literals in tui/screens/monitor.py (the existing grep lock); no new textual import in tui/services/ (the import lock).
</verification>

<success_criteria>
- The maintainer's contract is implementable verbatim from this plan: [d] fail-safe delete (confirm-only path, live roots undeletable, worker-thread rm -rf, rescan, manual-root hygiene) and [e] honest resume (failed+interrupted pairs, completed-skip semantics, shared confirm/preflight/launch/E2' machinery, seam choice documented in <seam_decision> and the code docstrings).
- Every new operator string is bilingual with an inventory row; the pty lane carries one spawn per new flow; no test lane ever performs a real GPU launch or a real subprocess spawn.
- The cadence render gates (261018-rze) hold: the footer refresh fires only on mount and tab switch; steady ticks stay byte-silent (the existing pty quiet-cadence test must pass unmodified).
</success_criteria>

<output>
Create `.planning/quick/261018-toe-slot-5-history-row-actions-d-delete-rm-r/261018-toe-SUMMARY.md` when done (quick-task summary template; record the seam decision, the justified file deviations, and the golden-untouched proof in the deviations section).
</output>
