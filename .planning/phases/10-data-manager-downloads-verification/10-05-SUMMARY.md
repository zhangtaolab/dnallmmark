---
phase: 10-data-manager-downloads-verification
plan: 05
subsystem: tui-screens
tags: [selection-d-enqueue, presence-overlay, merge-presence, live-flip, shared-queue, env-route, d14, d11, pilot]
requires:
  - phase: 10-data-manager-downloads-verification
    provides: "10-01..10-03's frozen queue surface — enqueue/EnqueueOutcome, reconciled_rows/merge_presence (the D-11 substrate), the DL_/QUEUE_/SEL_ENQUEUE_/ENV_ROUTE_ string inventory"
  - phase: 10-data-manager-downloads-verification
    provides: "10-04's app-level execution spine — the shared DownloadQueueService, kick_download_queue, the generic on_queue_event_message forward (any screen defining apply_queue_event receives the stream), and the DataManagerBackend two-Protocol seam shape"
  - phase: 08-selection-screen
    provides: "the selection screen's binding table, exclusive _load_data worker, _cursor_key guards, and the presence-cell render contract"
provides:
  - D-14 fully landed — the selection datasets table's d enqueues presence-✗ rows into the SHARED queue with the data-manager screen's exact outcome-toast vocabulary; the bottom bar carries [d]入队 between the toggle and matrix keycaps; the env-check route hint renders the [3] keycap segment with digit 3 as the one navigation path (zero env_check.py code changes)
  - D-11 in the selection snapshot — SelectionBackend.load_selection_data builds presence over merge_presence(load_n_audit(), reconciled_rows()); audit_available is (committed n_audit) or (overlay non-empty); the flip is ✗->✓ exactly on reconcile-pass (mismatch/failed never flip, test-pinned)
  - The live flip — SelectionScreen.apply_queue_event re-runs the exclusive snapshot worker on a done event through the landed 10-04 app forward; the cell flips in place on the mounted screen, never remounting
  - The shared-instance wiring — build_selection_screen bridges the app-level queue into the screen's minimal enqueue Protocol (SelectionQueueBackend, the DataManagerBackend two-Protocol shape)
affects: [10-06 e2e (the operator-visible d -> flip loop over the real service), Phase 11 launch gate (presence now reflects live reconcile truth)]
actuals:
  tokens: 9690     # chars/4 over the realized diff (2782853..11c0ca2)
  tasks: 2
  commits: 4       # MEASURED: git rev-list --count 2782853..11c0ca2 (2 RED test + 2 GREEN feat, TDD)
plan_head_before: 2782853b53cad631359e29f2b5d4b03012a3e0a3
plan_head_after: 11c0ca2f60aec7c80d6bf1d816decddedc3d3455
tech-stack:
  added: []
  patterns:
    - "Two-Protocol bridge at the screen seam: the app's QueueDriverProtocol does not declare enqueue, so SelectionQueueBackend (Any-typed ctor, the documented DataManagerBackend boundary pattern) bridges the shared instance into the screen's minimal SelectionQueueServiceProtocol — ty-clean without loosening either Protocol"
    - "Green-from-birth pinning tests: negative constraints (mismatch never flips) and already-landed semantics (the env route hint) are pinned by tests that pass at RED time — only the positive flip behaviors drive RED"
key-files:
  created: []
  modified:
    - tui/screens/selection.py
    - tui/app.py
    - tests/tui/test_pilot_selection_custom.py
    - tests/tui/test_pilot_data_manager.py
    - tests/tui/test_pilot_selection.py
key-decisions:
  - "The enqueue seam is SelectionQueueBackend — a thin Any-typed adapter over the app's shared instance (the DataManagerBackend two-Protocol shape), not a direct pass: the app's driver Protocol does not declare enqueue and ty checks the declared type, so the bridge keeps both Protocols honest"
  - "The merged presence uses truthiness (if audit:) not is-not-None: merge_presence returns {} (not None) for a None+empty input, and truthiness preserves the Phase 8 byte-exact degenerate behavior (presence {} + audit_available False -> the column-level copy) while the overlay path still computes"
  - "audit_available = (committed is not None) or bool(overlay_rows): an audit-less machine with a done queue entry renders its flip; every other key renders the unknown cell (never a fabricated verdict)"
  - "apply_queue_event reuses the existing exclusive _load_data worker exactly as _on_custom_registry_changed does — no new worker, no new group, no remount; the 10-04 forward needed zero changes to reach the screen"
  - "The d outcome mapping is a verbatim re-statement of the data-manager screen's pair (same constants, same severities, kick only on enqueued) — the one-vocabulary rule is structural, not documented"
requirements-completed: [DATA-01, DATA-03]
coverage:
  - id: D1
    description: "D-14 first half: the selection d binding, the shared-service seam, the outcome toasts, the models-view no-op, the bottom-bar keycap order"
    requirement: DATA-01
    verification:
      - kind: integration
        ref: "tests/tui/test_pilot_selection_custom.py (d on missing -> recorded key + kick spy + toast + never navigates + already-queued second press; present-row no-op toast; shape-D DL_DISABLED_TOAST with the key; models-view silent no-op; [d] keycap between [e] and [v])"
        status: pass
  - id: D2
    description: "D-11/SC1 second half: the merged presence snapshot, the audit_available rule, the seeded-state flip + back, the mismatch/failed exclusion"
    requirement: DATA-03
    verification:
      - kind: integration
        ref: "tests/tui/test_pilot_selection_custom.py (done entry -> present cell with thousands-separated measured counts; state-file removal -> missing again; mismatch + failed entries never flip)"
        status: pass
  - id: D3
    description: "The live flip through the landed 10-04 app forward + the env-route ENV-03 landing proof"
    requirement: DATA-03
    verification:
      - kind: integration
        ref: "tests/tui/test_pilot_selection_custom.py (done QueueEvent through app.on_queue_event_message -> in-place cell flip, same screen instance, QUEUE_FLIP_TOAST) + tests/tui/test_pilot_data_manager.py (rendered route line carries [3] 前往数据管理 through the real render path; digit 3 switches to DataManagerScreen over the fake queue)"
        status: pass
  - id: D4
    description: "Full gates green, zero out-of-scope tree changes, env_check.py zero-byte diff"
    requirement: DATA-01
    verification:
      - kind: integration
        ref: "make test (pytest 1135 = 1126 wave-4 baseline + 9 new; node 18/18, exit 0); make lint (ruff All checks passed); make typecheck (ty All checks passed); git diff 2782853..HEAD over pipeline/ script/ scripts/ dnallm-mark/ pyproject.toml uv.lock tui/services/ tui/screens/env_check.py = EMPTY"
        status: pass
duration: 31min
completed: 2026-10-12
status: complete
---

# Phase 10 Plan 05: Selection d + Presence Overlay + Env Route Summary

**One-liner:** The selection screen's presence-✗ rows gained the `d` enqueue binding over the app-level shared queue (the data-manager screen's exact outcome-toast vocabulary), the presence snapshot became the merge_presence(load_n_audit(), reconciled_rows()) merged view so reconcile-pass flips ✗->✓ in-table (mismatch never flips), a done QueueEvent through the landed 10-04 app forward re-runs the snapshot worker for a live in-place flip, and the env-check route hint renders the [3] keycap with digit 3 as the one navigation path — zero env_check.py code changes.

## What Was Built

### Task 1 — Selection d binding + shared-service seam + outcome toasts

`BINDINGS` gained `Binding("d", "enqueue_dataset", SEL_ENQUEUE_LABEL)` between the `e` pair and the `v` auxiliary action (declaration order = bottom-bar order; the [d]入队 keycap renders between 停用 and 矩阵). The new seam: `SelectionQueueServiceProtocol` (enqueue(key) -> EnqueueOutcome, the minimal shared surface — the kick lives on the app) + `SelectionQueueBackend` (the EnvCheckBackend idiom; an Any-typed ctor bridging the app's shared instance, the documented DataManagerBackend two-Protocol boundary — ty checks the app field's declared `QueueDriverProtocol`, which does not declare enqueue, so the bridge keeps both Protocols honest). `action_enqueue_dataset`: models view returns first (models are not n_audit subjects); `_cursor_key()` None stays silent (state rows); a PRESENT row toasts SEL_ENQUEUE_PRESENT_TOAST before any service call (never silent, never duplicate work); the outcome mapping is the data-manager pair verbatim — enqueued -> QUEUE_TOAST_ENQUEUED + `app.kick_download_queue()`; already_queued -> its toast; disabled -> DL_DISABLED_TOAST with the key (always diagnosable, R-02); cli_unavailable -> QUEUE_CLI_UNAVAILABLE; unknown_key -> silent. Never navigates. `app.build_selection_screen` now passes `queue_service=SelectionQueueBackend(self._download_queue)` — the selection d, the data-manager screen, and the driver mutate ONE queue.

### Task 2 — Presence overlay + live flip + env route proof

`SelectionBackend.load_selection_data` builds presence over the MERGED audit: `committed = load_n_audit()`; `overlay = reconciled_rows()` (the tolerant state-file read — no service instance, no write); `merge_presence(committed, overlay)`; the unchanged `presence_for` maps the merged view (registries.py untouched, the 10-02 contract). `audit_available = (committed is not None) or bool(overlay)` — presence renders even when only live truth exists. `SelectionScreen.apply_queue_event(event)`: a done event (done IS reconcile-pass, the service's done gate) re-runs the existing exclusive `_load_data` worker; the 10-04 generic forward (`on_queue_event_message` -> the current screen's `apply_queue_event` when the attribute exists) reaches the mounted screen with zero app changes. The env route proof is test-only: the amended ENV_ROUTE_MISSING_DATASETS (10-03 strings) already carries `[3] 前往数据管理`; the new Pilot test renders it through the real verdict path (the dataset_dirs failure fixture) and presses digit 3 to the DataManagerScreen — env_check.py has a zero-byte diff this plan.

## Performance

- **Duration:** ~31 min (2026-10-12T16:53Z -> 17:24Z)
- **Tasks:** 2/2
- **Files:** 5 modified (0 created — all planned files + the one Rule-3 test-allowlist amendment)

## Task Commits

Each task ran RED -> GREEN with separate commits:

1. **Task 1: the d binding** — `7cdfeec` (test, RED: 5 failed — the seam/binding absent) / `7139165` (feat)
2. **Task 2: the overlay + live flip** — `f417862` (test, RED: the flip tests failed on the planned assertion — the seeded done entry rendered ✗ 缺失) / `11c0ca2` (feat)

RED semantics note: the mismatch/failed-exclusion test and the env-route test were green-from-birth pins (negative constraints over absent semantics cannot fail; the route hint landed with 10-03/10-04) — the plan's own "verified by test, not assumed" requirement; the positive flip behaviors were the RED drivers.

## Verification Evidence

- `uv run --group dev --group tui pytest tests/tui/test_pilot_selection_custom.py tests/tui/test_pilot_data_manager.py tests/tui/test_pilot_env_check.py -q` — **77 passed** (19 + 33 + 25).
- `make test` — **exit 0**: pytest **1135 passed** (1126 wave-4 baseline + 9 new), node lane 18/18.
- `make lint` — ruff **All checks passed**. `make typecheck` — ty **All checks passed** (zero ty:ignore, unchanged).
- Scope: `git diff 2782853..HEAD` touches exactly `tui/screens/selection.py`, `tui/app.py`, and the three test files; over `pipeline/ script/ scripts/ dnallm-mark/ pyproject.toml uv.lock tui/services/ tui/screens/env_check.py` the diff is **EMPTY** (services frozen, env_check.py zero-byte — the prohibition held).

## Deviations from Plan

**1. [Rule 3 - test allowlist] test_pilot_selection.py help-modal exact rows**
- **Found during:** Task 1 GREEN — `test_help_modal_opens_on_the_selection_screen` pins the modal's rows exactly; the planned BINDINGS insertion adds the shown `d` row between `e` and `v`.
- **Fix:** added the `d` row to the expected list (one line + comment; the auto-reflecting chrome pin — the same class as wave-4's nav-target allowlist). The plan's "existing selection Pilot tests pass unmodified" could not hold simultaneously with its own BINDINGS row. **Commit:** `7139165`.

**2. [Rule 1 - self-inflicted, fixed in-lane] two lint-class defects caught by the gates**
- The Task-1 binding comment carried the Chinese keycap labels (入队/停用/矩阵), tripping the zero-Chinese grep lock on selection.py — rewritten English-only (labels live in tui/strings.py). `7139165`.
- An unused `# noqa: E402` on the env-route test's import (E402 is not enabled; RUF100) — removed. `11c0ca2`.

**3. [Design note] the seam is a bridge adapter, not a direct pass**
- The plan's "build_selection_screen passes the app-level queue service into SelectionScreen" is implemented as `SelectionQueueBackend(self._download_queue)`: the app's declared field type (`QueueDriverProtocol`) does not carry `enqueue`, and ty checks declared types. The bridge is the 10-04 `DataManagerBackend` two-Protocol pattern the 10-04 summary explicitly pointed at; the shared-instance guarantee is identical (the wrap carries the SAME queue object).

---

**Total deviations:** 3 documented (1 Rule-3 test allowlist, 1 batched in-lane lint-fix note, 1 typing-driven design note)
**Impact on plan:** No scope creep — every change inside the plan's files plus the single one-line allowlist amendment; all gates green.

## Issues Encountered

None blocking. `gsd_run` (via `node ~/.claude/gsd-core/bin/gsd-tools.cjs`) was available this wave — state/roadmap/requirements updates went through the CLI handlers.

## Known Stubs

None. Every surface added this plan is wired end-to-end (the d action through the shared service, the overlay through the real merged read, the flip through the real app forward).

## Threat Flags

None — no security-relevant surface beyond the plan's threat model. All four mitigations test-pinned: T-10-05-01 (reconciled_rows' done-only overlay + the mismatch/failed exclusion proof), T-10-05-02 (the same service method + the same toast constants asserted on both screens' suites), T-10-05-03 (the present-row gate before any service call — zero enqueue_calls asserted), T-10-05-04 (reconciled_rows is a tolerant local-file read invoked only inside the exclusive `_load_data` worker thread). T-10-SC: zero packages installed.

## Next Phase Readiness

- **10-06 (hardening + SC checklist):** can assume SC1 is fully Pilot-proven at both halves — the seeded-state and live-event flip chains each run end-to-end over the real merged snapshot; the d action's outcome contract is identical on both screens by construction (same constants); the shared queue reaches selection via `build_selection_screen`'s bridge. The e2e can drive the real `DownloadQueueService` beneath the same seams (`FakeQueueService` stays the CI lane). env_check.py remains pristine — the ENV-03 landing is proven by test, so the SC checklist can cite it directly.
- **Phase 11 (launch gate):** the selection/env presence views now reflect live reconcile truth (not just the committed baseline) — the launch-gate quick-check consumers should re-read through the same merged view if they render presence.

## Self-Check: PASSED

All five modified files exist on disk; all four plan commits are ancestors of HEAD (`7cdfeec`, `7139165`, `f417862`, `11c0ca2`); `commits: 4` measured from the persisted ledger (`2782853..11c0ca2`); full gates green (1135 pytest + node, ruff, ty); env_check.py zero-byte diff verified.

---
*Phase: 10-data-manager-downloads-verification*
*Completed: 2026-10-12*
