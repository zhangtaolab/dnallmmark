---
phase: quick-261014-dcl
plan: 01
subsystem: tui
tags: [tui, env-check, selection, data-manager, presence, storage-roots, goldens]

requires:
  - phase: 261014-c2l / 08-04 / 10-04
    provides: the run-config storage-root persistence (RunSpec.model_root/dataset_root + resolve_dirs), the env_smoke CheckResult kernel seam, and the merged n_audit/reconcile presence substrate this plan's three surfaces build on
provides:
  - the model_dirs env-check kernel + override-aware directory kernels (check_model_dirs/check_dataset_dirs over _effective_base, always-annotated root headline, ROUTING disposition)
  - run-config-aware env checks (default_kernels binds resolve_dirs(load_state()) absolute roots into both directory kernels)
  - the selection screen's live models presence column (selection.model_presence pure decision + SEL_MODEL_PRESENCE_* copy)
  - the data manager's v-toggled full official-registry presence view (DownloadQueueService.presence_rows over the merged view, CR-01)
affects: [quick-check launch preflight, env screen cache shape (seven-item state files now miss), selection models table, data-manager bottom bar]

actuals:
  tokens: 116552   # chars/4 over the realized diff 6df795d..25eb849 (466,210 chars incl. the five SVG goldens; code-only is a fraction of that)
  tasks: 3
  commits: 4       # measured: git rev-list --count 6df795d..25eb849 (the task's own commits: 3 feat + 1 fake-conformance fix; a concurrent foreign docs commit d2f77c0 landed mid-run and is excluded)
plan_head_before: 6df795d
plan_head_after: 25eb849

tech-stack:
  added: []         # zero new dependencies anywhere (T-dcl-SC)
  patterns:
    - "override-aware base + verbatim registry-path join shared by three surfaces: _effective_base/root None -> pipeline dir (the run_finetune 261014-c2l expression), root -> rstrip(os.sep)+os.sep; the registry value keeps its own models//datasets/ prefix"
    - "checkout-independent root annotation: the default branch renders the fixed ' (root: pipeline/)' token, never the host-absolute path, so byte goldens stay stable"
    - "per-kernel routing lines (not the route_to_data bool) — a model_dirs failure can never fabricate a zero-count datasets line"
    - "same-day cache coverage guard: a persisted kernel-id set short of ENV_KERNEL_LABELS is a cache MISS, so pre-change state files re-run once instead of stranding the new row pending"

key-files:
  created:
    - tests/tui/__snapshots__/data_manager_presence.svg
  modified:
    - pipeline/env_smoke.py
    - tui/services/env_check.py
    - tui/services/quick_check.py
    - tui/services/env_gate.py
    - tui/services/selection.py
    - tui/services/download_queue.py
    - tui/screens/env_check.py
    - tui/screens/selection.py
    - tui/screens/data_manager.py
    - tui/strings.py
    - tests/test_env_smoke_bytes.py
    - tests/tui/test_services_env_check.py
    - tests/tui/test_services_quick_check.py
    - tests/tui/test_services_env_gate.py
    - tests/tui/test_pilot_env_check.py
    - tests/tui/test_pilot_boot.py
    - tests/tui/test_services_selection.py
    - tests/tui/test_pilot_selection.py
    - tests/tui/test_services_download_queue.py
    - tests/tui/test_pilot_data_manager.py
    - tests/tui/test_pilot_nav_shell.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_pilot_monitor.py
    - tests/tui/test_snapshots.py
    - tests/tui/__snapshots__/env_check.svg
    - tests/tui/__snapshots__/selection_models.svg
    - tests/tui/__snapshots__/data_manager.svg
    - tests/tui/__snapshots__/wizard.svg

key-decisions:
  - "Kernel parameter named root= (the plan's behavior contract + service/test specs pin the root kwarg; the action text's model_root=/dataset_root= names were a plan-internal slip — resolved uniformly with _effective_base(root) and the recording fakes)"
  - "A non-str/empty registry Model_path counts as MISSING in check_model_dirs but maps to UNKNOWN in selection.model_presence (the env kernel has no unknown state; the selection column does — honest per-surface degradation)"
  - "wizard.svg committed as collateral drift: the wizard golden pins env-screen pixels at its left edge (the modal never spans the grid), so the eighth row drifted it — D-03 says commit the golden with the change that drifted it"
  - "The models presence cell is filesystem-driven and never renders the n_audit-absent column copy (that copy is the DATASETS column's state); with no model_presence filled it renders the shared unknown cell"
  - "App-level driver-queue fakes gained the presence_rows leg (nav-shell/run-config/monitor/snapshots inert fakes) — DataManagerBackend delegates the full view through the queue, so every fake a slot-3 mount consumes needs it (Rule 3)"

requirements-completed: [DCL-01, DCL-02, DCL-03]

coverage:
  - id: D1
    description: "DCL-01: the eighth env row (kernel id model_dirs, label 模型目录) reflects live filesystem existence of every registry Model_path under the effective model root; both directory kernels annotate the effective root actually checked; the persisted run-config roots redirect both kernels and the annotation names them; a missing/corrupt state file reads as defaults; model_dirs failures are ROUTING (never block can_launch)"
    requirement: DCL-01
    verification:
      - kind: unit
        ref: "tests/test_env_smoke_bytes.py#test_s1_all_pass_stdout_is_byte_exact, #test_s2_torch_missing_stdout_is_byte_exact, #test_s3_dataset_missing_stdout_is_byte_exact, #test_s4_override_root_annotation_verbatim_join_and_missing_listing"
        status: pass
      - kind: unit
        ref: "tests/tui/test_services_env_check.py#test_default_kernels_bind_persisted_run_config_roots, #test_default_kernels_without_state_file_bind_none_roots, #test_run_full_check_default_sequence_mirrors_main_order, #test_default_sequence_torch_gate_appends_two_false_results"
        status: pass
      - kind: unit
        ref: "tests/tui/test_services_env_gate.py#test_model_dirs_failure_routes_without_blocking, #test_critical_and_routing_sets_are_disjoint_and_cover_all_eight; tests/tui/test_services_quick_check.py#test_quick_check_ids_are_the_seven_non_matmul_kernels_in_main_order"
        status: pass
      - kind: automated_ui
        ref: "tests/tui/test_pilot_env_check.py#test_model_dirs_fail_renders_model_route_without_dataset_line, #test_backend_same_day_seven_item_state_is_a_cache_miss, #test_state_and_verdict_strings_are_glyph_first_and_distinct"
        status: pass
      - kind: automated_ui
        ref: "tests/tui/test_pilot_boot.py#test_boots_on_env_check_screen_quits_on_q + tests/tui/test_snapshots.py#test_env_check_golden (the eighth row)"
        status: pass
  - id: D2
    description: "DCL-02: the models table renders a live presence cell (✓ 已下载 / ✗ 未下载 / ◌ 未知) decided in tui/services/selection.py over each registry Model_path resolved against the effective model root (run-config root when set, pipeline/ default byte-identically when unset); the datasets presence column renders byte-identically to before"
    requirement: DCL-02
    verification:
      - kind: unit
        ref: "tests/tui/test_services_selection.py#test_model_presence_present_missing_unknown_over_real_dirs, #test_model_presence_join_is_verbatim_root_honored, #test_model_presence_is_dir_seam_is_replaceable"
        status: pass
      - kind: automated_ui
        ref: "tests/tui/test_pilot_selection.py#test_boot_columns_toggle_and_marks_persist_independently, #test_presence_cell_formats_pin_the_contract (datasets byte-identical), #test_backend_loads_the_committed_registries_and_presence, #test_backend_model_presence_all_missing_under_empty_configured_root"
        status: pass
      - kind: unit
        ref: "tests/tui/test_services_download_queue.py#test_dl_and_queue_string_inventory_defined (the two SEL_ names registered)"
        status: pass
      - kind: automated_ui
        ref: "tests/tui/test_snapshots.py#test_selection_models_golden (regenerated; selection_datasets.svg byte-identical)"
        status: pass
  - id: D3
    description: "DCL-03: the data manager toggles with v between the missing table (unchanged render) and a full presence view — one row per official registry key with service-decided status over the merged n_audit/reconcile view and declared_total from the registry; the missing-status set equals missing_datasets() exactly; a done-reconciled key flips in both views; the toggle re-renders from the cached snapshot without re-running the worker"
    requirement: DCL-03
    verification:
      - kind: unit
        ref: "tests/tui/test_services_download_queue.py#test_presence_rows_covers_every_official_key_with_declared_totals, #test_presence_rows_missing_set_equals_missing_datasets_keys_cr01, #test_presence_rows_absent_n_audit_still_lists_keys_degraded, #test_presence_rows_unreadable_registry_yields_empty, #test_dl_queue_inventory_complete_no_unlisted_constants"
        status: pass
      - kind: automated_ui
        ref: "tests/tui/test_pilot_data_manager.py#test_v_toggles_to_the_full_presence_view, #test_v_twice_restores_the_missing_view, #test_toggle_rerenders_from_the_cached_snapshot_no_worker, #test_backend_missing_snapshot_flips_over_real_seeded_state_cr01 (presence_rows rides the flip)"
        status: pass
      - kind: automated_ui
        ref: "tests/tui/test_snapshots.py#test_data_manager_golden + #test_data_manager_presence_golden (corpus frozen 8 -> 9)"
        status: pass

duration: 104 min
completed: 2026-10-14
status: complete
---

# Quick Task 261014-dcl: TUI presence/directory visibility improvements Summary

**Three operator-console presence surfaces over the 261014-c2l storage roots: a model_dirs env kernel with run-config-aware directory checks (ROUTING, never blocking), a live models download-state column in the selection screen, and a v-toggled full 50-key dataset presence view in the data manager — all service-decided, tier-1/tier-2 tested in the same change, five SVG goldens committed**

## Performance

- **Duration:** 104 min (01:55:18Z → 03:38:56Z)
- **Started:** 2026-10-14T01:55:18Z
- **Completed:** 2026-10-14T03:38:56Z
- **Tasks:** 3
- **Files modified:** 29 (10 production + 14 test + 5 goldens)

## Accomplishments
- Env screen: an eighth 模型目录 row; both directory kernels resolve registry paths against the override-aware `_effective_base` (the run_finetune 261014-c2l verbatim-join semantics) and ALWAYS annotate the effective root (the fixed `pipeline/` token on the default branch keeps byte goldens checkout-independent); `default_kernels()` binds the persisted run-config roots; model_dirs joins ROUTING beside dataset_dirs and never blocks `can_launch`; the quick-check pre-flight subset gains model_dirs (seven ids)
- Selection screen: `selection.model_presence(entries, base, is_dir)` — the pure three-value decision over each registry Model_path; the backend resolves the effective base through run-config roots (else the committed pipeline dir) AFTER the customs union so custom models get statuses too; the models presence column renders ✓ 已下载 / ✗ 未下载 / ◌ 未知 while the datasets SEL-04 column stays byte-identical
- Data manager: `DownloadQueueService.presence_rows()` (PresenceRow over the same merged n_audit/reconcile substrate — CR-01: rows and the missing set move together); the v binding toggles the missing pane to the full 50-key view, glyph-prefixed keys + declared totals, re-rendering from the cached snapshot with zero worker kicks
- Strings inventory sync: ENV_ROUTE_MISSING_MODELS, SEL_MODEL_PRESENCE_PRESENT/MISSING (one-directional SEL_ tuple), DL_PRESENCE_TITLE/DL_PRESENCE_TOGGLE_LABEL (bidirectional DL_ lock) — all registered
- Gates: make lint + make typecheck green; full make test shows EXACTLY the ten documented pre-existing failures (verified identical at the base commit); import purity holds (env_check's new run_config chain leaves torch/dnallm absent)

## Task Commits

Each task was committed atomically (TDD: RED evidence captured per task — the tier-1 blocks failed on the missing symbols before each implementation):

1. **Task 1: model_dirs env kernel + run-config-aware roots (tracer)** - `aa6161d` (feat); tracer feedback gate re-ran `<verify>` end-to-end clean (end-of-phase mode, automated-only verify)
2. **Task 2: live models presence column** - `2281c81` (feat)
3. **Task 3: data-manager full presence view with v toggle** - `c199ff5` (feat)
4. **Rule-3 fix: conform app-level queue fakes to the presence_rows read** - `25eb849` (fix)

## Files Created/Modified
- `pipeline/env_smoke.py` — MODELS_INFO_PATH, `_effective_base`/`_root_annotation`, `check_model_dirs`, re-based `check_dataset_dirs(root=...)`, main() renders model_dirs before dataset_dirs (eight kernels; docstring items renumbered 5-8)
- `tui/services/env_check.py` — run-config root threading into both directory kernels
- `tui/services/quick_check.py` / `tui/services/env_gate.py` — seven-id subset / ROUTING covers both directory kernels
- `tui/screens/env_check.py` — per-kernel routing lines, `_missing_count`, the same-day cache coverage guard
- `tui/services/selection.py` — MODEL_PRESENCE_* vocabulary + the pure `model_presence` decision
- `tui/screens/selection.py` — SelectionData.model_presence (additive), backend base resolution, `_model_presence_cell`
- `tui/services/download_queue.py` — PresenceRow + `presence_rows()`
- `tui/screens/data_manager.py` — MissingSnapshot.presence_rows, the v binding + `_render_presence_view`
- `tui/strings.py` — five new constants, ENV_KERNEL_LABELS gains 模型目录
- Tests: the six Task-1 files, the four Task-2 files, the three Task-3 files, plus the four queue-fake conformance files
- Goldens: env_check.svg, selection_models.svg, data_manager.svg regenerated; data_manager_presence.svg NEW; wizard.svg collateral (see Deviations)

## Decisions Made
- Resolved the plan's kernel-signature inconsistency in favor of `root=` (its behavior contract "both kernels receive root=None", its service call sites, and its test fakes all pin the kwarg; the action text's `model_root=`/`dataset_root=` parameter names were the odd ones out)
- The models presence cell is filesystem-driven: it never renders the datasets column's n_audit-absent copy — with model_presence unfilled it renders the shared ◌ 未知 cell (the n_audit pilot test's model-view assertion updated accordingly)
- A non-str registry Model_path degrades to MISSING in the env kernel (no unknown state exists there) and UNKNOWN in the selection column
- Wizard collateral committed rather than reverting or re-driving the fixture: the modal's non-full-width layout is the golden's own semantics; the eighth env row honestly changed the pixels it pins

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] wizard.svg collateral golden drift (a fifth SVG diff)**
- **Found during:** Task 1 verification (`git status` over `__snapshots__`)
- **Issue:** The plan pinned exactly four SVG diffs, but `wizard.svg` also drifted: the wizard golden renders env-screen pixels at its left edge (the modal never spans the grid), so the eighth row changed them (verified by text-element diff: ✓/版本 pin/dnallm rows at x=0..231)
- **Fix:** Regenerated and committed with the change that drifted it (the D-03 discipline); recorded in the Windows ledger
- **Files modified:** tests/tui/__snapshots__/wizard.svg
- **Commit:** aa6161d

**2. [Rule 3 - Blocking] app-level driver-queue fakes lacked the presence_rows leg**
- **Found during:** the plan-level `make test` gate (after Task 3)
- **Issue:** `DataManagerBackend.missing_snapshot` now delegates the full view through the queue, so digit-navigation tests mounting the slot-3 screen over `_QueueDriverFake`-shaped fakes failed with AttributeError
- **Fix:** Added an inert `presence_rows()` to the nav-shell, run-config, monitor, and snapshot app-level queue fakes (files outside the plan's per-task lists — the widened Protocol surface they structurally implement)
- **Files modified:** tests/tui/test_pilot_nav_shell.py, tests/tui/test_pilot_run_config.py, tests/tui/test_pilot_monitor.py, tests/tui/test_snapshots.py
- **Commit:** 25eb849

**3. [Plan-text reconciliation] kernel parameter spelling**
- The plan's action named `check_model_dirs(model_root=None)` / `check_dataset_dirs(dataset_root=None)` while its behavior block, service wiring spec, and test spec all pin the `root=` kwarg — implemented as `root=` uniformly (see Decisions). No behavioral difference.

## Issues Encountered
- The full suite shows EXACTLY the 10 documented pre-existing failures (deferred-items.md of 261014-c2l): 5 stale schema/determinism pins after data commit 9bc68e1 + 5 root-user chmod persist-failure sims — four of the latter live in files this task touches and fail identically before and after; out of scope
- The snapshot golden lane intermittently flakes under load (`test_golden_export_is_deterministic_across_instances` and occasionally a `test_*_golden` compare): probed at the TRUE base commit 6df795d in a scratch worktree — it flakes there too (~2/17 isolated runs), so pre-existing and out of scope; logged to `deferred-items.md` in this directory
- A concurrent foreign commit (d2f77c0, backlog docs — not this task) landed on the branch mid-run; the SUMMARY's commits/plan_head_after exclude it (measured to 25eb849, this plan's last commit)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- The console now sees models/datasets under custom storage roots end-to-end: env check (advisory), selection models table (live), data manager (full view) — all consistent with what a launch will actually consume
- Every new surface is service-decided with tier-1 tests; the golden corpus is 9 (data_manager_presence earns its canonical-state row)

## Self-Check: PASSED

- All created/modified artifacts exist on disk (the 29 files above; data_manager_presence.svg created, wizard.svg + three regenerated goldens committed)
- All four task commits (aa6161d, 2281c81, c199ff5, 25eb849) verified as ancestors of HEAD; `git rev-list --count 6df795d..25eb849` == 4 (matches `commits:` in frontmatter)
- `status: complete` present in frontmatter
- Working tree clean over tests/tui/__snapshots__/; whole-plan SVG diffs are exactly the four planned + the documented wizard collateral
- make lint + make typecheck green; full make test == the ten documented pre-existing failures; import-purity probe green over the three touched services

---
*Quick task: 261014-dcl*
*Completed: 2026-10-14*
