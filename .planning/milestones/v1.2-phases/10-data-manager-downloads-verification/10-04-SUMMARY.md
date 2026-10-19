---
phase: 10-data-manager-downloads-verification
plan: 04
subsystem: tui-screens
tags: [data-manager, slot-3, driver-worker, five-state-queue, progress-cells, mismatch-banner, drill-down, zenodo-line, boot-resume, pilot]
requires:
  - phase: 10-data-manager-downloads-verification
    provides: "10-01..10-03's complete queue surface (claim_next/run_task/entries, EnqueueOutcome, QueueEntry.reconcile, enqueue_zenodo) and the 47-name DL_/QUEUE_ string inventory this screen renders"
  - phase: 10-data-manager-downloads-verification
    provides: "the 10-UI-SPEC binding design contract (five-state glyph table, item-11 accent progress cells, two panes, d/r/x/a/enter + g/z, mismatch banners, Zenodo four states, WR-06 guard)"
  - phase: 09-custom-model-dataset-onboarding
    provides: "the nav shell (NAV_SLOTS, TopMenuBar/BottomBar, action_nav routing, build_selection_screen factory rationale) and the selection idioms (column geometry, ConfirmModal, state rows, below_minimum_grid)"
provides:
  - The slot-3 data-manager screen — NAV_SLOTS 3 targets data_manager with zero placeholder artifacts; the two-pane surface (missing fixed + queue flex) renders every UI-SPEC state over the Protocol seam
  - The app-level execution spine — ONE shared DownloadQueueService, the exclusive driver worker (claim -> run_task -> post; exits on drain so wait_for_complete never hangs), the synchronous kick busy-guard, generation-tagged messages, and boot_resume_queue wired ONLY through tui/__main__
  - The app -> screen event forward (QueueEventMessage -> apply_queue_event / QueueProgressMessage -> apply_queue_progress) — the exact seam 10-05's selection screen consumes for the live presence flip
  - apply_queue_event as persisted-state-as-truth row refresh + the done-triggered missing-list reload (the D-11 flip surface)
affects: [10-05 selection/env cross-screen integration (the same event forward + the SEL_/ENV_ROUTE constants), 10-06 e2e (the operator-visible loop), Phase 11 monitoring (the driver/worker idioms)]
actuals:
  tokens: 32633     # chars/4 over the realized diff (5bb324e..57d37fe)
  tasks: 3
  commits: 6        # MEASURED: git rev-list --count 5bb324e..57d37fe (3 RED test + 3 GREEN feat, TDD)
plan_head_before: 5bb324ee1b876667a3d478bc5f605a23482bf6d7
plan_head_after: 57d37fec7913160e92c305673088198f06c08fbf
tech-stack:
  added: []          # textual 8.2.8 only (the [tui] group); zero new dependencies
  patterns:
    - "Per-worker @work groups: textual exclusivity cancels by (node, group) — two exclusive mount workers sharing the default group silently cancel each other (probe-pinned; per-worker groups are the fix)"
    - "The indeterminate claim tick: the driver posts one percent=None progress message at claim so the row flips to downloading before any CLI percent parses (unparsed output may never fire a real tick)"
    - "Persisted-state-as-truth event application: apply_queue_event/apply_queue_progress re-read the entry from the service and re-render — late or duplicated events can never overwrite a newer state (T-10-04-01)"
    - "Column width = TOTAL including 2x cell padding (probe-pinned on 8.2.8) — the 15-cell progress composition needs width 17, not the spec's 14"
key-files:
  created:
    - tui/screens/data_manager.py
    - tests/tui/test_pilot_data_manager.py
  modified:
    - tui/screens/nav.py
    - tui/app.py
    - tui/__main__.py
    - tui/styles.tcss
    - tests/tui/test_pilot_nav_shell.py
    - tests/tui/test_pilot_selection_custom.py
key-decisions:
  - "The driver lives at APP level and owns the whole kick/claim/run loop; the screen only kicks — test-constructed apps are provably inert because boot_resume_queue is scheduled solely by tui/__main__ (never App.on_mount)"
  - "Two Protocols at one seam: QueueDriverProtocol (app.py — load/entries/claim_next/run_task) and DataManagerServiceProtocol (screen — snapshot/enqueue/probe/reaudit/channel_detail/read_log), bridged by the Any-typed DataManagerBackend adapter over the SHARED queue instance"
  - "The busy-guard proof is the generation counter: two rapid kicks leave _queue_generation at 1 (an unguarded second kick would cancel-and-restart at 2) plus exactly one task claim + one drain check"
  - "Bundle rows (kind=zenodo_bundle) render the dash in the reconcile cell and no banner on mismatch — the contract's {n}/{m} fields are dataset-granular; the per_key verdict map rides the drill-down (no number pair exists for the whole-package lane)"
  - "The Zenodo failed line fills {error} with the data word 'unknown' — the probe API answers a bare state, no diagnostic crosses the service boundary; the probe stays fake-injectable through the queue's optional probe_zenodo attr (the real service falls through to the frozen-URL GET)"
  - "The restart note appends to the task cell (the selection disabled-suffix idiom): truncation may clip it for long keys; short keys show it in full and the drill-down always carries it"
requirements-completed: [DATA-01, DATA-02, DATA-03, DATA-04]
coverage:
  - id: D1
    description: "D-13/D-14/D-15: slot-3 promotion + the two-pane shell + the full d/r/x/a/enter/g/z interaction surface"
    requirement: DATA-01
    verification:
      - kind: integration
        ref: "tests/tui/test_pilot_data_manager.py (digit-3 switch, five states, progress bar, reconcile cells, empty states, banners, restart note, bundle label, drill-downs, 68-char backstop, 80x24 geometry) + tests/tui/test_pilot_nav_shell.py (three sanctioned edits: bare slot text, widgets[3:5], digit-3 switch)"
      - kind: integration
        ref: "tests/tui/test_pilot_data_manager.py (d/a/r/x/z/g happy + noop + confirm paths with every DL_/QUEUE_ toast; the per-screen zero-Chinese lock)"
        status: pass
  - id: D2
    description: "D-02/SC5/D-06: the app-level driver worker — busy-guard, drain-exit no-hang, boot resume only via __main__, progress streaming, responsiveness"
    requirement: DATA-02
    verification:
      - kind: integration
        ref: "tests/tui/test_pilot_data_manager.py (inert boot T-10-04-03, double-kick generation proof T-10-04-02, empty-kick exit, drain + restart, live 40% bar, [None,10,25,40,100] throttle stream, blocked-task live toast T-10-04-05)"
        status: pass
  - id: D3
    description: "D-07/D-09 presentation: mismatch banners under the queue title + sort-to-top; the reconcile cell vocabulary; the D-11 flip surface (done drops the key from the missing list, one snapshot reload only)"
    requirement: DATA-03
    verification:
      - kind: integration
        ref: "tests/tui/test_pilot_data_manager.py (banner block + stable sort, four reconcile cells, e2e rows/toast/missing-refresh with the no-reload-for-failed proof)"
        status: pass
  - id: D4
    description: "D-12: the Zenodo four-state line + z public-only enqueue (never silent otherwise); D-03: the verbatim drill-down (key/url/argv/reconcile/log)"
    requirement: DATA-04
    verification:
      - kind: integration
        ref: "tests/tui/test_pilot_data_manager.py (gated-probe probing pin + three terminal states, z in each state, both drill-down lanes, WR-06 below-min round trip)"
        status: pass
  - id: D5
    description: "Full gates green, zero out-of-scope tree changes"
    requirement: DATA-01
    verification:
      - kind: integration
        ref: "make test (pytest 1126 = 1094 wave-3 baseline + 32 new; node 18/18, exit 0); make lint (ruff All checks passed); make typecheck (ty All checks passed, zero ty:ignore); git diff 5bb324e..HEAD over pipeline/ script/ dnallm-mark/ pyproject.toml uv.lock = EMPTY"
        status: pass
duration: 58min
completed: 2026-10-12
status: complete
---

# Phase 10 Plan 04: Data-Manager Screen + App Execution Spine Summary

**One-liner:** The slot-3 data-manager screen over the 10-01..10-03 queue surface — a two-pane UI (missing list + five-state download queue with accent progress bars, reconcile cells, mismatch banners, Zenodo line, verbatim drill-down, and the full d/r/x/a/enter/g/z key set) wired to an app-level exclusive driver worker with a synchronous kick busy-guard, generation-tagged events, persisted-state-as-truth row application, and boot resume that fires only from `python -m tui`.

## What Was Built

### Task 1 — Nav promotion + app spine + screen shell

`tui/screens/nav.py`: slot 3 became `NavSlot(3, NAV_LABEL_DATA, "data_manager", None)` — the placeholder suffix and phase toast stop firing for slot 3 only; slots 4/5 untouched. `tui/app.py` gained the `download_queue_service` constructor seam (Protocol | None, real `DownloadQueueService` default) storing the ONE shared instance; `build_data_manager_screen()` wraps it in `DataManagerBackend` (the factory rationale: a zero-arg SCREENS slot would fork the queue state); the `action_nav` data_manager branch (isinstance no-op, else switch); module-level `QueueEventMessage`/`QueueProgressMessage` carrying the driver generation (WR-02); `kick_download_queue()` with the busy flag set synchronously before any await; the `@work(exclusive=True, thread=True)` driver loop (claim -> indeterminate claim tick -> run_task with the throttled progress poster -> event post -> repeat; returns on the drained queue so `wait_for_complete` can never hang); `boot_resume_queue()` (load + kick iff pending); and the two forwarder handlers (done -> `QUEUE_FLIP_TOAST`; forward to the current screen's `apply_queue_event`/`apply_queue_progress` when present). `tui/__main__.py` schedules `boot_resume_queue` via `call_later` — the ONLY auto-start path (App.on_mount never kicks). The shell (`tui/screens/data_manager.py`): the Protocol + `DataManagerBackend` (missing snapshot over registries presence, channel detail with composed argv, read_log under the state root, probe through the queue when it carries one), the D-15 BINDINGS (d/r/x/a/enter visible, g/z show=False, the six nav digits), and the two-region compose (missing fixed-height 5, queue flex with the border-top rule). `tui/styles.tcss`: the region classes, the banner class, the separators — theme tokens only.

### Task 2 — The full interaction surface

Missing pane: glyph+key cells (in-cell truncation at the 31-cell content width, full key in detail), thousands-separated right-aligned baseline rows, the happy-zero state row, the right-aligned Zenodo line in the title row. Queue pane: the five glyph+copy+style state cells, the progress composition (right-aligned 4-cell percent + 10-cell bar, filled `█` spans in the caller-resolved live theme accent — the probe-pinned span limitation; indeterminate `⠋ …`; done/mismatch dim 100%), the reconcile four-cell vocabulary (pass/running-at-100%/mismatch/dash — the running cell is the derived post-landing transient), the restart-note append on interrupted rows, the bundle label, mismatch+failed sort-to-top (stable), and one `queue-banner-mismatch` Static per number-carrying mismatch under the queue title. Actions: d (all four outcome toasts + kick + reload), a (count toast), r (retry + kick / noop toast), x (both ConfirmModal variants with esc back-out / noop toast, WR-06-guarded), g (mismatch-rows-only re-audit in an exclusive worker, reload on done), z (public-only bundle enqueue with the bundle-label toast; the never-silent disabled toast otherwise). The `QueueDetailModal` RichLog drill-down: full key, registry download_url, space-joined LIST argv, reconcile numbers (per_key lines for bundle rows), problems, and the verbatim log lines — data, never elided.

### Task 3 — Driver end-to-end + event application

The e2e over digit-3 + the shared fake: two scripted entries (done + failed) — final states render, the flip toast fires for the done entry only, the reconciled key leaves the missing list, and exactly ONE extra snapshot pass runs (the failed row reached its state through `apply_queue_event` alone — the no-full-reload proof). Live progress: the 40% bar renders mid-flight behind a gate and the post stream is exactly `[None, 10, 25, 40, 100]` (the claim tick leads; duplicate consecutive percents throttle away). Responsiveness: while a fake run_task blocks on an Event, an r-press still toasts (T-10-04-05, the T-08-07 lineage). Worker exit + restart on drain/re-kick; the x-on-downloading confirm copy and the seam signal through the shared queue.

## Performance

- **Duration:** ~58 min (2026-10-12T15:51Z -> 16:48Z)
- **Tasks:** 3/3
- **Files:** 8 (2 created, 6 modified — all planned + the one Rule-3 test-allowlist fix)

## Task Commits

Each task ran RED -> GREEN with separate commits:

1. **Task 1: nav promotion + spine + shell** — `f8ceec0` (test, RED) / `e6c8354` (feat)
2. **Task 2: the interaction surface** — `4d1e063` (test, RED) / `599be15` (feat)
3. **Task 3: driver e2e + gates** — `f159549` (test, RED) / `57d37fe` (feat)

## Verification Evidence

- `uv run --group dev --group tui pytest tests/tui/test_pilot_data_manager.py tests/tui/test_pilot_nav_shell.py -q` — **42 passed** (27 + 15).
- `make test` — **exit 0**: pytest **1126 passed** (1094 wave-3 baseline + 32 new), node lane green.
- `make lint` — ruff **All checks passed**. `make typecheck` — ty **All checks passed** (zero ty:ignore, unchanged).
- Scope: `git diff 5bb324e..HEAD -- pipeline/ script/ dnallm-mark/ pyproject.toml uv.lock` — **EMPTY** (no pipeline edits, no service edits beyond the plan's declared consumer surface, no registry writes, no dependency changes).
- CI network-free: every Zenodo touch is the fake probe; no test lane reaches zenodo.org.
- The tui-design skill was loaded before any visual code (maintainer directive 2026-10-12); its restraint/glyph-discipline/keyboard-first/empty-state principles are applied throughout, subordinate to the locked UI-SPEC.

## Deviations from Plan

**1. [Rule 3 - Blocking] test_pilot_selection_custom.py target allowlist**
- **Found during:** Task 1 full-suite verify — `test_the_menu_carries_no_wizard_item` hardcodes the routing vocabulary `("env_check", "selection", "about", None)`.
- **Fix:** added `"data_manager"` to the tuple (one token + comment). Direct consequence of the planned promotion; the plan's "no existing test modified outside the three sanctioned sites" could not hold simultaneously with its own full-suite-green verify.
- **Commit:** `e6c8354`.

**2. [Rule 1 - Bug] the shared default @work group cancelled the mount workers**
- **Found during:** Task 2 GREEN — the snapshot worker never ran: textual exclusivity cancels by (node, group), and the mount pair (snapshot + probe) both sat in group "default", so the probe's start killed the just-started snapshot thread.
- **Fix:** per-worker groups (`dl-snapshot` / `dl-probe` / `dl-reaudit`). Probe-pinned on 8.2.8; documented at the worker block. `599be15`.

**3. [Rule 1 - Bug] `{HH:MM}` is not a legal str.format field**
- **Found during:** Task 2 GREEN — `DL_ZENODO_NOT_PUBLIC.format(**{"HH:MM": ...})` raises KeyError 'HH' (the colon parses as a format spec).
- **Fix:** the placeholder fills via `str.replace("{HH:MM}", probed_at)`. `599be15`.

**4. [Design adjustment - geometry] the progress column is 17, not the spec's 14**
- **Found during:** Task 2 layout — textual column widths are TOTAL including 2x cell padding (probe-pinned), so a 14-wide column has 12 content cells; the contract's progress composition (4-cell percent + space + 10-cell bar = 15) cannot fit.
- **Fix:** `任务 33 · 状态 10 · 进度 17 · 行数对账 rest` — the same ~74-cell budget, the contract composition intact, the truncation lesson preserved. `599be15`.

**5. [Design note - contract gap] the bundle row's reconcile cell and banner**
- The five-state table's `{n}≠{m}` banner/cell fields are dataset-granular; a mismatched zenodo bundle carries `per_key` verdicts, no number pair. Bundle rows render the dash in the reconcile cell, sort to the top on mismatch, and carry the per-key map in the drill-down. Documented in the module header and key-decisions.

**6. [Rule 1 - test bugs, self-inflicted] five RED-draft defects fixed in-lane**
- The busy-guard test's post-drain claim count (2 = one task claim + one drain check, not 1; the generation==1 counter is the real guard proof), `cursor_down` -> `move_cursor` (8.2.8 API), a wrong sort-stability expectation, cursor-reset-after-rebuild in the d test, and two missing imports. All inside the test commits (`e6c8354`, `599be15`, `57d37fe`).

---

**Total deviations:** 6 documented (1 Rule-3 test-allowlist, 2 Rule-1 code bugs, 1 geometry adjustment, 1 contract-gap design note, 1 batched test-defect note)
**Impact on plan:** No scope creep — every change inside the plan's files plus the single one-token allowlist fix; all gates green.

## Issues Encountered

`gsd_run` CLI unavailable in this environment (same as 10-02/10-03) — state/roadmap/requirements updates applied manually following the documented handler behaviors.

## Known Stubs

None. The not-public Zenodo state remains the live truth (the record is unregistered; activation is the probe answer flipping, zero code change). `_PROBE_ERROR_DETAIL = "unknown"` is a data word for a state whose API carries no diagnostic — not a stub; documented in the module header.

## Threat Flags

None — no security-relevant surface beyond the plan's threat model. All six mitigations test-pinned: T-10-04-01 (generation-tagged messages + handler drops + the persisted-state-as-truth application in both apply methods), T-10-04-02 (the busy-guard generation proof), T-10-04-03 (the inert-boot proof), T-10-04-04 (both x confirms behind ConfirmModal with esc back-out), T-10-04-05 (the blocked-fake live-toast proof), T-10-04-06 (the below-min enter round trip + the guard checks on both push paths).

## Next Phase Readiness

- **10-05 (cross-screen integration):** can assume the app-level event forward exactly as landed — `on_queue_event_message` forwards EVERY `QueueEventMessage` to the current screen's `apply_queue_event` when the attribute exists, so the selection screen needs only to define that method (plus optionally `apply_queue_progress`) to receive the same stream; `DataManagerBackend` shows the two-Protocol seam shape for injecting the shared queue into the selection screen; `SEL_ENQUEUE_LABEL`/`SEL_ENQUEUE_PRESENT_TOAST`/`DL_DISABLED_TOAST` and the amended `ENV_ROUTE_MISSING_DATASETS` are all pinned by name. The presence flip itself stays service-side (`merge_presence(load_n_audit(), reconciled_rows())`) — untouched here.
- **10-06 (e2e):** the operator-visible loop (d -> kick -> progress -> done toast -> missing-list drop) is Pilot-proven end-to-end over fakes; the e2e can drive the real service beneath the same seams.

## Self-Check: PASSED

All eight touched files exist on disk; all six plan commits are ancestors of HEAD (`f8ceec0`, `e6c8354`, `4d1e063`, `599be15`, `f159549`, `57d37fe`); `commits: 6` measured from the persisted ledger (`5bb324e..57d37fe`); full gates green (1126 pytest + node, ruff, ty).

---
*Phase: 10-data-manager-downloads-verification*
*Completed: 2026-10-12*
