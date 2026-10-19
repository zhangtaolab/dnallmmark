---
phase: quick-261018-toe
plan: 01
status: complete
task: 261018-toe
title: "Slot-5 History row actions — [d] delete (rm -rf behind a strong confirm) + [e] 续跑 (resume-from-history)"
date: 2026-10-18
commits:
  - "a4f9df7 feat(quick-261018-toe): service seams — incomplete_pairs_view, rerun_lane alias-dir fallback, launch_from_pairs"
  - "351d280 feat(quick-261018-toe): [d] delete — strong y-only confirm, worker-thread rm -rf, live refusal, per-tab footer keycaps"
  - "7257f02 feat(quick-261018-toe): [e] 续跑 — incomplete derivation, honest confirm, shared pipeline stages, E2' re-prompt routing"
duration: ~33 min wall (1982s)
tests:
  whole_tui_suite: "1244 passed, 1 failed — the documented environment collateral (test_storage_overview_defaults_mirror_real_consumers fails while the maintainer's live run keeps pipeline/logs/ existing; out of scope, untouched)"
  pty_lane: "10 passed (2 new spawns: delete end-to-end, resume confirm + n cancel; the rze quiet-cadence byte-silence pin passes unmodified)"
  pilot_monitor: "78 passed (15 new: 8 [d]-family, 7 [e]-family)"
  services: "145 passed (6 new tier-1 pins)"
  strings_inventory: "11 new MON_ constants mirrored (bidirectional lock green)"
  gates: "ruff clean, ty clean (whole [tool.ty] include set)"
audit_acknowledged:
  milestone: v1.2
  at: 2026-10-19
  status: complete
---

# 261018-toe SUMMARY — Slot-5 History row actions: [d] 删除 / [e] 续跑

One line: the Monitor's History tab gained fail-safe row lifecycle — [d]
deletes a dead run's output root behind a KillConfirmModal-contract y-only
confirm executed in a worker thread (live roots structurally undeletable,
pre-modal AND in-worker), and [e] resumes a dead run's incomplete items
(failed + interrupted pairs) through the existing failures pipeline via a
materialized pairs file — plus per-active-tab footer keycaps.

## Task 1 — service seams (commit a4f9df7)

Landed:
- `sweep_monitor.incomplete_pairs_view(cells)` — pure fold over
  cells_view rows; failed+interrupted pairs only, alias identity
  verbatim, sorted distinct. Pinned over dead/live/legacy live-pair
  legs (the dead root's strict-miss is what derives interrupted).
- `sweep_monitor.rerun_lane` alias-dir fallback leg — when peft is
  still "none" after the failures loop, the discovered model-dir names'
  `+lora`/`+ia3` suffixes recover the lane for interrupted roots;
  config_variant stays manifest-only; every branch that already spoke
  is byte-identical (pinned: failures-says-lora beats a +ia3 dir).
- `sweep_launcher.launch_from_pairs(pairs, seeds, output_root, ...)`
  — writes `state_dir()/resume/resume_pairs_{rootname}.json` (driver
  failures-entry shape: `base_model` only for suffixed aliases, the
  run_sweep.load_failure_pairs strip chain), then DELEGATES to
  `launch_from_failures` verbatim. Pinned: full-matrix pairs × 3 seeds
  refuses at the phrase stage with the spawner provably never called;
  the matching phrase spawns naming the state-dir file; single-GPU
  stage-0 refuses first (file already written — the child reads it at
  startup).

Test evidence: `tests/tui/test_services_sweep_monitor.py` +
`test_services_sweep_launcher.py` 145 passed; ruff + ty clean.

## Task 2 — [d] delete (commit 351d280)

Landed:
- `DeleteConfirmModal(ConfirmModal)` — the KillConfirmModal contract
  matched exactly: y (visible MON_DELETE_KEYCAP) + Y (hidden twin)
  confirm; n/N + esc cancel; enter structurally inert; bold [Y]/[y]/
  [N]/[n] tokens (cdr Rich-Text pattern); border title names the root.
- `action_delete_history` (History tab only, focused row, below-grid
  silent — the [f]/[t] precedent) → live refusal toast → the
  `_read_delete_count` worker (one off-loop cells_view read, summed
  per-row seed counts) → DeleteReady → the modal names the FULL root
  path + the honest 训练项 count.
- y → `mon-delete` worker thread: in-worker liveness RE-CHECK (the
  confirm-to-worker race), `delete_root` (adapter-tier
  `shutil.rmtree(ignore_errors=True)`; sweep_monitor stays pure),
  best-effort tolerant `remove_manual_root`, DeleteFinished posted
  back (WR-02 `_delete_stage_id`; WR-03 → DeleteFailed error toast).
  Success → MON_DELETE_TOAST + immediate `_tick_full` rescan.
- Per-tab footer: `nav.py` `KeycapsStatic.refresh_pairs` +
  `BottomBar.refresh_left_pairs` (the only justified out-of-scope-list
  production file, ~30 lines); monitor `_footer_pairs()` filters the
  d/e rows unless `_active_tab == "history"`; refresh fires from
  on_mount (via call_after_refresh) and action_switch_tab ONLY — never
  in `_render_all`, never on the cadence.
- Strings: MON_DELETE_KEYCAP/TITLE/CONFIRM/TOAST/FAILED/REFUSED_LIVE +
  MON_RESUME_KEYCAP (needed by the Task-2 binding), 7 inventory rows.

Test evidence: 8 new Pilot tests (modal+count, y-deletes+rescan,
uppercase twins, live-root pre-modal refusal with NO modal, the
flip-launcher confirm-to-worker race pin, off-tab/no-selection/
below-grid silence, exception toast, footer keycaps History-only both
directions); 1 new pty spawn (real `d` keypress → modal → `y` → toast
→ on-disk disappearance: root gone + manual root unregistered);
snapshots green with the three D-03 goldens UNTOUCHED (the Running-tab
footer is byte-identical by construction — filtered projection, same
7 rows, same order); rze quiet-cadence byte-silence pin unmodified and
green.

## Task 3 — [e] 续跑 (commit 7257f02)

Landed:
- `action_resume_history` (the [d] guard family) → live-root refusal
  (MON_RESUME_REFUSED_LIVE) → the `mon-resume` `_derive_resume` worker
  (cells_view → incomplete_pairs_view + `derive_rerun_seeds((), rows)`
  + rerun_lane) → ResumeReady → empty pairs → MON_RESUME_NOTHING toast
  (no modal, launcher never consulted) → single-GPU pre-check (the
  EHC-3 request_rerun mirror) → LaunchConfirmModal naming
  pairs × seeds = n with the completed-cells-skip note.
- y runs the SAME staged pipeline as [f]→[r]: RerunPreflightDone and
  RerunFinished gained `resume: bool = False` (every existing post
  site unchanged); `_dispatch_rerun_launch` routes [f] to
  `_run_rerun_launch` byte-unchanged and [e] to the new
  `_run_resume_launch` worker, which RE-DERIVES off-loop (WR-02/03),
  refuses loudly when underivable, and calls `launch_from_pairs`; the
  E2' phrase re-prompt closure routes back through the SAME lane
  (resume=True); MON_RESUME_TOAST on spawn; env-block/single-GPU/
  problems/error surfaces all shared.
- `MonitorBackend.launch_from_pairs` delegation (None-launcher guard,
  the launch_from_failures adapter twin).
- Strings: MON_RESUME_CONFIRM/TOAST/NOTHING/REFUSED_LIVE (4 rows).

Test evidence: 7 new Pilot tests (honest confirm over
failed+interrupted+completed cells with worker re-derivation equality
and rerun_calls==[] — resume never touches the failures path;
nothing-to-resume; live refusal; single-GPU before confirm; env block;
E2' phrase re-prompt threading through the RESUME worker; preflight
exception toast); 1 new pty spawn (interrupted root → real `e` → the
"incomplete pairs" confirm → `n` cancel → row still paints; y NEVER
pressed — no lane performs a real launch). The pre-existing [f]→[r]
rerun tests passed unmodified throughout.

## Deviations from plan

### Recorded plan-vs-reality deviations (minimal safe adjustments)

1. **[Rule 1/3 - Bug/Blocking] d/e declared after the tab row, not
   "after the k row"** (monitor.py BINDINGS). Evidence: the bottom
   bar's left segment is `1fr` — 93 cells at the 120-col grid — and
   the D-15 clip policy drops the LEAST-PRIMARY (trailing) keycaps
   first; the full en keycap line is 101 cells, so an after-[k]
   declaration clipped away exactly [d]/[e] on the History tab,
   contradicting the plan's own must-have ("[d]/[e] keycaps render
   ONLY while the History tab is active") and the pty marker. Declared
   after the tab-switch row (the History surface's primary actions)
   they paint; the RUNNING projection filters them and is
   byte-identical (same 7 rows, same order — the snapshot goldens
   prove it). On History, en now clips the trailing Rescan keycap
   instead (zh fits all nine — CJK labels are narrower).
2. **[Rule 3 - Blocking] `incomplete_pairs_view` takes the CELLS, not
   `(root, live_pairs)`** (sweep_monitor.py). The plan's Task-1
   behavior line names `incomplete_pairs_view(root, live_pairs=None)`,
   but its Task-3 screen worker demands the derivation over the
   Pilot-faked, service-seam-threaded cells (the presentation-tier
   contract: the screen never reads the artifact tree). A
   root-parameter signature would bypass `MonitorServiceProtocol` and
   break every scripted Pilot test the plan itself specifies. The
   function is the same pure fold; the caller threads the
   live-evidence cells_view output (pinned in the tier-1 tests over
   dead/live/legacy legs).
3. **[Rule 3 - Blocking] `delete_root` / `launch_from_pairs` are NOT
   declared on the Protocols** — both implemented on `MonitorBackend`
   and reached through the tolerant getattr seam (the documented
   kill_sweep precedent). Evidence: declaring them ty-flags the
   pre-existing `_MonitorShellFake`/`_MonitorLauncherShellFake`/
   `_LauncherFake` in test_pilot_nav_shell.py, test_pilot_run_config.py,
   and test_snapshots.py — files outside the plan's scope. A missing
   seam surfaces loudly (DeleteFailed / RerunFailed), never a false
   success. The plan's artifact-list wording ("MonitorServiceProtocol.
   delete_root ... and their MonitorBackend implementations") is
   realized as the backend implementations + tolerant access.
4. **[Rule 2 - Missing critical functionality] `MonitorBackend.
   remove_manual_root` added** (not in the plan's artifact list).
   Evidence: the first pty run left the deleted root registered in
   monitor_roots.json (the hygiene leg silently skipped — the backend
   had no method for the tolerant getattr to find), which would
   resurrect scanning attempts on every future boot. Delegation added;
   the pty test now pins the unregistration.
5. **[Rule 1 - Bug] the [d] pty marker adapted** — the plan's closing
   marker ("No past runs yet") assumes a clean machine; this host
   carries real default roots (`finetuned/`, `pipeline/finetuned/`)
   that REPO_ROOT-relative DEFAULT_OUTPUT_ROOTS always discover, so
   the empty copy never paints here. The test accepts the either-
   marker (empty copy OR the table header repaint, the kvj precedent)
   and proves the row's disappearance on disk (root removed + manual
   root unregistered) — stronger than the screen-text assertion.

### Justified file deviations (per the plan's scope_justification + these)

- `tui/screens/nav.py` — planned and blessed (~30 lines:
  refresh_pairs/refresh_left_pairs; initial mount byte-identical;
  test_pilot_nav_shell green unmodified).
- `tests/tui/test_strings_phase11.py` — planned and blessed (the
  bidirectional inventory tripwire must list every new MON_ constant).
- `tests/tui/test_services_sweep_monitor.py` +
  `tests/tui/test_services_sweep_launcher.py` — planned and blessed
  (the tier-1 homes of the two new pure seams).

### Golden-untouched proof

`git status` at close: the ONLY working-tree modifications are the
three pre-existing uncommitted D-03 SVGs (`monitor_empty.svg`,
`monitor_running.svg`, `run_config.svg`) — byte-for-byte the session's
starting state, never staged, never regenerated, `make snapshot-update`
never run. `tests/tui/test_snapshots.py` passes against them
UNMODIFIED (109 passed incl. all snapshot goldens), proving the
Running-tab footer renders byte-identically through the d/e filter.

## Environment collateral (out of scope, not fixed)

`tests/tui/test_services_run_config.py::
test_storage_overview_defaults_mirror_real_consumers` fails while the
maintainer's live run keeps `pipeline/logs/` existing — the documented
pre-existing failure; every other test in `tests/tui/` passes
(1244 passed / 1 failed).

## Grep audits (the plan's verification section)

- No 细胞 in any new MON_ constant (zh values checked programmatically;
  the single strings.py hit is an English comment documenting the
  prohibition).
- Zero Chinese literals in `tui/screens/monitor.py` (the existing grep
  lock holds).
- No new textual import in `tui/services/` (the import lock holds;
  the only new stdlib import is `json` in sweep_launcher).
- Registry injectivity (zh↔en, both directions), placeholder parity
  across languages, and the retired-terminology table all green over
  the 11 new constants.
