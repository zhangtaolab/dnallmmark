---
phase: quick-261016-vxr
plan: 01
subsystem: tui
tags: [monitor, eta, kill, exit, i18n]
status: complete
requirements: [VXR-1, VXR-2, VXR-3, VXR-4]
commits: 3
plan_head_before: f506ed4
plan_head_after: ef2e365031f6
key-files:
  created:
    - .planning/quick/261016-vxr-slot-5-monitor-batch-eta-remaining-time-/RED-EVIDENCE.json
    - .planning/quick/261016-vxr-slot-5-monitor-batch-eta-remaining-time-/261016-vxr-SUMMARY.md
  modified:
    - tui/services/sweep_monitor.py
    - tui/screens/monitor.py
    - tui/app.py
    - tui/strings.py
    - tests/tui/test_services_sweep_monitor.py
    - tests/tui/test_pilot_monitor.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_pilot_env_check.py
    - tests/tui/test_pilot_nav_shell.py
    - tests/tui/test_pilot_selection.py
    - tests/tui/test_strings_phase11.py
decisions:
  - ETA data source = the checkpoint-pair trainer_state.json FILE mtimes (probed: the JSON carries no wall-clock field; the tee tqdm bar is CR-carriage-interleaved and CLI-launched-invisible)
  - Q = an App.on_event intercept, never a BINDINGS entry (probe P1 printable-key consume filter + P9 modal stacking); the base-screen capital-Q typing sacrifice is the maintainer's chosen tradeoff, modals exempt
  - KillConfirmModal added ALONGSIDE v0z's QuitConfirmModal (assumption-delta: stop-training vs quit-console are distinct operator acts; a generic confirm would erase the EHC-2 launch-vs-kill distinction)
metrics:
  duration: 178 min
  completed: 2026-10-17
actuals:
  tokens: 22000
  tasks: 4
  commits: 3
---

# Quick Task 261016-vxr: slot-5 monitor batch — entry ETA, [k] kill confirm, uppercase Q any-focus exit

The maintainer's 2026-10-16 live-session batch on slot 5: an honest per-training-run ETA beside the entries progress row, a `k` stop key with its own kill confirmation (stop training without exiting the console), and uppercase `Q` exiting from any focus — including the filter-input focus trap — through the v0z confirmation chain.

## VXR-1 — the checkpoint-pair ETA (file:line)

**Data-source decision (probe-driven).** `trainer_state.json` carries NO wall-clock field (probed on the real smoke artifacts at `finetuned-smoke/plant-dnabert-6mer/iDNA_ABF_datasets__5mC/seed_42/checkpoint-528`: keys are `global_step`/`max_steps`/`log_history`; every `log_history` entry carries only epoch/step/loss-family fields). The tee log's HF tqdm bar does carry cadence (`3/20480 [00:12<22:43:18, 3.99s/it]`) but lives in carriage-return-separated physical lines, interleaves Filter/Encoding/loading bars, and exists only for TUI-launched sweeps (a CLI launch renders MON_LOG_UNAVAILABLE in the [t] modal). DECISION: checkpoint-pair derivation — the same files `cell_progress` already parses, every launch mode, zero log-format coupling. The coordinator's "checkpoint 时间戳" reading is implemented as the checkpoint `trainer_state.json` FILE mtime (probed pair checkpoint-520/checkpoint-528: mtimes 2s apart — resolvable).

**Landed surface:**
- `tui/services/sweep_monitor.py:261` — `CellProgress.eta_seconds: float | None = None` (frozen dataclass; the default keeps every existing 3-field construction valid)
- `tui/services/sweep_monitor.py:930` — `_trainer_state_mtime` (the FILE mtime read, OSError-tolerant)
- `tui/services/sweep_monitor.py:940` — `_eta_from_checkpoint_pair`: rate = Δglobal_step / Δ(trainer_state.json file mtime) over the TWO newest checkpoints; strict gates (both parse as dicts, both steps non-bool ints, step_new > step_old, mtime_new > mtime_old, max_steps > step_new); every failure → None. No clamping (a stalled run shows a large honest ETA), no tee-log parsing, tolerant end to end (never raises into the cadence)
- `tui/services/sweep_monitor.py:980` — `cell_progress` now tracks the two numerically-largest checkpoint dirs on the existing bounded walk (`_SCAN_DIR_ENTRY_CAP` kept)
- `entries_progress` — pure passthrough, zero code change (the best-by-step pick carries the field; pinned by test)
- `tui/screens/monitor.py:1678-1697` — `_entry_progress_cell` appends one segment after the text/bar: `format_eta(progress.eta_seconds)` when derivable, else the dim `_DASH`; the NARROW form keeps steps text + eta and still drops only the bar; the indeterminate and non-running branches are byte-untouched. Zero new operator copy (format_eta is CJK-free data; `_DASH` is the existing table symbol) — zero strings.py change for this item.

**Golden non-interaction proof:** the golden fixtures' `_MonitorGoldenService` has no `entries_progress` method (the tolerant seam) — their running rows render the indeterminate constant, so the ETA suffix cannot touch any golden byte (verified: only the k keycap moved the monitor SVGs).

## VXR-2 — the [k] kill confirm (file:line)

**Design:** stop-training is a NEW destructive act with its own confirm — it never reuses the quit surfaces and NEVER exits the console (stop training ≠ exit console).

- `tui/strings.py:1773-1790` — seven bilingual `MON_KILL_*` constants (keycap 停止/Kill mirroring MON_FAILURES_KEYCAP style; the [Y]/[N] confirm pair mirrors LNC_GATE_CONFIRM/LNC_EXIT_CONFIRM)
- `tui/screens/monitor.py:536` — `KillConfirmModal(ConfirmModal)` beside FailuresModal: y-only (`Binding("y", "confirm_kill", show=False)`, n/esc cancel, escape inherited), `action_confirm` a documented no-op (EHC-2: enter can never confirm a kill), border title `MON_KILL_TITLE.format(root=…)` with the RESOLVED root (WR-05 basename-collision rationale)
- `tui/screens/monitor.py:813` — `Binding("k", "kill_running", S.MON_KILL_KEYCAP)` immediately after the r entry (bottom bar + help project it)
- `tui/screens/monitor.py:1465` — `action_kill_running`: below-min-grid → return (WR-06); no attached root → silent return (the [f]/[t] precedent); attached root NOT in `live_sweeps()` → the MON_KILL_UNAVAILABLE toast BEFORE any confirm (never a confirm the channel cannot execute); the single-GPU guard is deliberately never consulted (kill is the EHC-3 REMEDY, not a launch — comment cites the ruling, pinned by test)
- `tui/screens/monitor.py:1493-1519` — `_kill_confirmed` bumps `_kill_stage_id` (the WR-02 run-id idiom) and dispatches `@work(exclusive=True, thread=True, group="mon-kill", exit_on_error=False)` reaching `kill_sweep` through the TOLERANT getattr seam (a launcher face without the method reads the noop outcome — the entries_progress/single_gpu_launch_blocked precedent; `MonitorLauncherProtocol` deliberately does NOT declare it, so no existing fake is ty-flagged). kill_sweep blocks up to the kill grace polling the group — never on the event loop
- `tui/screens/monitor.py:887/898/1521/1538` — `KillFinished`/`KillFailed` run-id-tagged messages; outcomes map signalled → MON_KILL_TOAST, already_dead → MON_KILL_TOAST_DEAD, noop → MON_KILL_UNAVAILABLE; a raised exception → the MON_KILL_FAILED error toast (WR-03 — a confirmed kill that dies is never a silent no-op). The handlers only toast; the console stays up.

**Assumption-delta note (recorded per the contribution fragment):** this batch adds a SECOND confirmation-modal family member beside v0z's QuitConfirmModal — decision add-alongside, deliberately (distinct operator acts, distinct copy/keycaps; a generic confirm would erase the EHC-2 launch-vs-kill distinction LaunchConfirmModal documents).

## VXR-3 — uppercase Q any-focus exit (file:line)

**Probe results (P1-P14, live Pilot runs, throwaway):**
- **P1** — an App-level `Binding("Q", ..., priority=True)` does NOT fire while an Input is focused: `Screen._binding_chain` applies a consume-key filter and a focused Input's `check_consume_key` returns True for EVERY printable character, stripping the key from every later namespace's map INCLUDING the app's; the priority walk then finds no Q. The maintainer's 方案 (a) cannot be realized by a Binding alone for a printable key.
- **P3/P8** — ctrl+q (non-printable) DOES fire over a focused Input (Input does not consume ctrl-combos) — why the v0z ctrl+q declaration works.
- **P9** — a priority binding fires over a plain open modal too (the priority path walks the full `_binding_chain`, not the modal-cut chain) → Q-as-binding would stack modals over modals. Hence Q is an on_event intercept with an explicit not-modal guard, NOT a BINDINGS entry.
- **P10-P14 (the adopted seam)** — overriding `App.on_event` to intercept `events.Key` with `key == "Q"` when a screen is mounted and not modal, routing to the guarded quit and returning WITHOUT `super()`: Q fires over a focused Input and is never typed (P10); lowercase q still types (P11); Q inside a modal Input TYPES the character and never quits (P12 — an E2' phrase or path containing Q stays enterable); Q over a focused DataTable (P13) and with no focus (P14) fires.

**Landed:** `tui/app.py:1042-1080` — `DnallmMarkTui.on_event` with the probe facts in the docstring; routes to the v0z `action_quit` three-leg chain UNMODIFIED (below-min-grid → nothing; live sweep → ExitModal; neither → QuitConfirmModal); `tui/app.py:1119` — the `("Q", S.APP_Q_LABEL)` help row appended after the ctrl+c row; `tui/strings.py:174` — `APP_Q_LABEL` bilingual beside APP_CTRLQ_LABEL. **Documented consequence (T-261016vxr-03, accept):** a capital Q no longer types into BASE-screen Inputs — reserved as the exit key; modals exempt. The slot-5 k row appears in the help/bottom bar automatically via the BINDINGS projection.

## Item-2 review deliverable (P9 顺审 — review-only, no pre-change)

**(a) The App-level ExitModal `k`=kill_quit context review.** k consistently means KILL in both surfaces, at two different altitudes: the ExitModal's `k` answers a quit the operator ALREADY invoked (ExitModal IS itself the quit confirmation — its enter/k/esc triple is the final decision on that invocation; v0z by design carries no double confirm on top of it), while slot-5's `k` STARTS a new destructive act against a running sweep and therefore needs its own confirm (KillConfirmModal, y-only per EHC-2). Consistent under the EHC-2 philosophy: an already-confirmed decision answers with its triple; a new destructive act opens a fresh gate. The two surfaces also differ correctly in exit semantics (ExitModal k kills-then-exits; slot-5 k stops-and-stays).

**(b) The ctrl+q-inside-modal stacking finding.** v0z's declared `ctrl+q` mirror carries `priority=True`, and the priority binding path walks the FULL `_binding_chain` — not the modal-cut chain (probe P9 mechanism). Consequence: ctrl+q pressed while ANY modal is top (the HelpModal, the ExitModal itself, a KillConfirmModal, the wizard) re-runs `action_quit` and STACKS a second exit modal over the open one. Not a data-loss hazard (every path still confirms before exiting), but a UX wart and a stack-growth path. **RECOMMENDED follow-up guard (v0z-owned surface, NOT changed in this task — surgical scope):** `action_quit` returning early when an `ExitModal`/`QuitConfirmModal` is already the top screen (e.g. `if isinstance(self.screen, (ExitModal, QuitConfirmModal)): return` ahead of the leg dispatch), closing the stack for ctrl+q the same way the modal binding chain already closes it for plain q.

## VXR-4 — gates, goldens, discipline

**Final gate numbers (read at execution time):**
- `make lint` (ruff over tests/ + the full tui/ + pipeline scope) — **All checks passed**
- `make typecheck` (ty) — **All checks passed**
- full pytest — **7 failed / 1842 passed** at EXACTLY the 7F baseline membership (`test_determinism` 1, `test_schemas` 5, `test_services_run_config` 1 — the machine-local pipeline/logs member), zero new failures, all 19 new tests passing (baseline before the change: 7F/1823P)
- node — **26/26**
- `tests/tui/test_snapshots.py` — **11/11 green against the regenerated on-disk SVGs**

**Golden-integrity proof (the D-03 path):** `make snapshot-update` regenerated the corpus; `git status` over `tests/tui/__snapshots__/` shows EXACTLY three modifications —
```
 M tests/tui/__snapshots__/monitor_empty.svg
 M tests/tui/__snapshots__/monitor_running.svg
 M tests/tui/__snapshots__/run_config.svg
```
`cmp` proves `run_config.svg` BYTE-IDENTICAL to the Task-1 snapshot (sha256 `afa89e7e5452e15aebd4ac11584d794a9dd29d002ab9bc8d8b1e92d39ced8ef2` — the pre-existing 261016-poa D-03 artifact; the regeneration reproduced the same bytes, determinism confirmed). The two monitor SVGs differ ONLY by the `[k] 停止` keycap inserted after `[r] 重扫` in the bottom bar (diff-verified; the remaining delta is the SVG content-hash class renumbering). The ETA change contributes nothing (their running rows are tolerant-seam indeterminate). All other six goldens byte-untouched.

**D-03 statement (required):** the regenerated `monitor_running.svg` and `monitor_empty.svg` are deliberately UNCOMMITTED for the maintainer's D-03 review — the COMMITTED TREE FAILS `test_snapshots` on exactly these two goldens until the maintainer reviews and commits them alongside this change (recorded as WINDOWS ledger entry #29). No SVG was committed by the executor.

**RED evidence:** `.planning/quick/261016-vxr-slot-5-monitor-batch-eta-remaining-time-/RED-EVIDENCE.json` — 23 failed / 262 passed at the exact planned split (RED: the 6 service ETA tests on the missing `eta_seconds` field — TypeError/AttributeError; the k-kill lane on ImportError for KillConfirmModal/MON_KILL_*; Q-over-Input legs on Q typing instead of quitting; the three help-row pins + both inventory tests on APP_Q_LABEL/the seven unlisted names. GREEN: the indeterminate pin, q-lowercase, Q-under-modals, Q-below-grid, and every unmodified existing test). RED commit `f1277ff`.

**Commits (all PLAIN, zero attribution trailers, nothing pushed):**
- `f1277ff` test(261016-vxr): RED — entry ETA, slot-5 k kill confirm, uppercase Q any-focus exit
- `5344ace` feat(261016-vxr): entry ETA from checkpoint-pair step cadence, honest dash when underivable
- `ef2e365` feat(261016-vxr): slot-5 k kill confirm via launcher channel + uppercase Q any-focus guarded exit

## Deviations from Plan

**1. [Rule 1 - test-fixture corrections during RED authoring]**
- **Found during:** Task 1
- **Issue:** (a) the run-config seeds Input's displayed value is repopulated by the screen load, so a hardcoded "42,43,44" expectation was brittle; (b) Textual Input's `select_on_focus` selects the content on focus, so the first typed key REPLACES the value (probed: value "42,43,44" → focus → press x → value "x").
- **Fix:** the Q tests capture `value_before` (today: replaced by the typed Q — honest RED; after the fix: unchanged — the consumption pin); the q-lowercase pin asserts the standard replace-typing shape `value == "q"` with a comment documenting the semantics. Also fixed a bar-cell typo in the new ETA-render expectation (60% = 6 filled cells of 10).
- **Files:** tests/tui/test_pilot_run_config.py, tests/tui/test_pilot_monitor.py

**2. [Rule 1 - docstring wording tripped two grep locks]**
- **Found during:** Task 3 (the full-lane verify)
- **Issue:** the on_event docstring's first draft contained 方案 (Chinese — the app-module zero-literal lock) and the literal `` ``Binding("Q", ..., priority=True)`` `` pattern on one line (the priority-typing-binding grep lock reads every source line).
- **Fix:** reworded to "option (a)" and "declared with the priority flag" — the probe facts stay, the locks pass.
- **Files:** tui/app.py

**3. [Rule 3 - lint] `Callable` imported from `typing` in monitor.py** — UP035; moved to `from collections.abc import Callable` (the repo convention in selection/run_config/env_check).

## Threat-model dispositions (all mitigate/accept as planned)

- **T-261016vxr-01 (DoS via killpg)** — mitigated: y-only confirm with enter structurally inert; the target is the RESOLVED attached root matched against `live_sweeps()`; attached-but-not-live refuses BEFORE the confirm; tests pin the exact root passed.
- **T-261016vxr-02 (tampered artifacts → fabricated ETA)** — mitigated: the strict validity gates; every failure degrades to the dim dash, never a fabricated estimate.
- **T-261016vxr-03 (typing availability of Q)** — accepted and documented: the maintainer's 方案 (a) tradeoff; modals exempt.
- **T-261016vxr-SC (package installs)** — no package installs (tui/ + tests only, zero dependency changes).

## Known Stubs

None — no stub patterns introduced; every surface is wired to real data or its designed honest degradation.

## Self-Check: PASSED

All six key files exist on disk; all three task commits (f1277ff, 5344ace, ef2e365) are ancestors of HEAD; the two monitor SVGs plus the byte-preserved run_config.svg remain uncommitted exactly as the D-03 discipline requires.
