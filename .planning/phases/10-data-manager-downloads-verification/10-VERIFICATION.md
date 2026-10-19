---
phase: 10-data-manager-downloads-verification
verified: 2026-10-19T12:14:40Z
status: passed
score: 5/5 must-haves verified
covered_files:
  - .planning/phases/10-data-manager-downloads-verification/10-01-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-01-SUMMARY.md
  - .planning/phases/10-data-manager-downloads-verification/10-02-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-02-SUMMARY.md
  - .planning/phases/10-data-manager-downloads-verification/10-03-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-03-SUMMARY.md
  - .planning/phases/10-data-manager-downloads-verification/10-04-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-04-SUMMARY.md
  - .planning/phases/10-data-manager-downloads-verification/10-05-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-05-SUMMARY.md
  - .planning/phases/10-data-manager-downloads-verification/10-06-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-06-SUMMARY.md
  - .planning/phases/10-data-manager-downloads-verification/10-07-PLAN.md
  - .planning/phases/10-data-manager-downloads-verification/10-07-SUMMARY.md
  - pipeline/directories_config.py
  - tests/tui/fixtures/modelscope_stderr_interrupted.txt
  - tests/tui/fixtures/modelscope_stderr_success.txt
  - tests/tui/test_pilot_data_manager.py
  - tests/tui/test_pilot_nav_shell.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_pilot_selection_custom.py
  - tests/tui/test_services_download_queue.py
  - tests/tui/test_services_gauntlet.py
  - tests/tui/test_services_zenodo_bundle.py
  - tui/__main__.py
  - tui/app.py
  - tui/screens/data_manager.py
  - tui/screens/nav.py
  - tui/screens/selection.py
  - tui/services/download_queue.py
  - tui/services/env_check.py
  - tui/services/gauntlet.py
  - tui/services/registries.py
  - tui/services/run_config.py
  - tui/services/selection.py
  - tui/services/zenodo_bundle.py
  - tui/strings.py
  - tui/styles.tcss
covered_digest: "v3:sha256:5309c629ed496cbb3beee68feff2117b12782ea7e4629b5925a09f115aac007b"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions: []
advisory:
  - finding: "WR-01 (carried) — a failed KIND_MODEL download can flip the selection models 下载 column: model_presence gates on is_dir only (tui/services/selection.py) while the model-lane done gate requires config.json (MODEL_DONE_MARKER)"
    category: other
    reason: "Carried forward unchanged — tui/services/selection.py is byte-identical since the prior verified pass (0 diff lines, numstat-verified over 6bb768f..HEAD). Model presence column is dcl/mlc scope layered after phase 10; models are not n_audit subjects; no phase-10 SC covers it. Disposition-open in 10-REVIEW-DISPOSITION.md"
    evidence_status: "git diff 6bb768f..HEAD: zero services/selection.py hunks"
  - finding: "IN-01 (carried) — z pressed during the mount probe-in-flight window fires DL_ZENODO_DISABLED_TOAST while _zenodo_state is still None (data_manager.py init region; the != PROBE_PUBLIC arm)"
    category: other
    reason: "Carried forward unchanged — data_manager.py is byte-identical since the prior verified pass (0 diff lines). Transient copy issue; SC4 reachability and never-silent behavior unaffected (a toast always fires). Disposition-open"
    evidence_status: "git diff 6bb768f..HEAD: zero data_manager.py hunks"
resolved_advisories:
  - finding: "IN-02 (carried prior) — ABOUT_MILESTONE_STAGE stale (named phase 9) in tui/strings.py"
    resolution: "RESOLVED out-of-band by the milestone-closeout version commits (effb5bf v1.2.0 bump + 3961d2c about pin): the string now reads 'v1.2.0 — full TUI console delivery (Phases 7-12)' in both languages (tui/strings.py:1035-1041, re-read this pass). Dropped from the carried list"
    evidence: "strings.py re-read at :1035-1041 this pass; the strings delta since 6bb768f touches APP_TITLE/ABOUT/LNC_/MON_ blocks only — zero DL_/QUEUE_/ZENODO lines (delta grep empty); DL_/QUEUE_ census 57 before and after"
---

# Phase 10: Data Manager (Downloads & Verification) Verification Report — Staleness Refresh (Round 7, post-pe0)

**Phase Goal:** Dataset gaps are closable in-session before launch — one-click ModelScope download driven by the registry's authoritative `download_url`, a persistent resumable queue, and row-count reconciliation against n_audit — so an env-check presence FAIL is always diagnosable and fixable from the console
**Verified:** 2026-10-19T12:14:40Z at HEAD 5783567 (branch autorun)
**Status:** passed — 5/5 SCs hold at the refreshed HEAD; zero regressions from the post-6bb768f delta; the carried IN-02 advisory is RESOLVED (milestone string updated) and dropped
**Re-verification:** Yes — staleness refresh (round 7). Prior pass 5/5 `passed`, report verified 2026-10-17T07:49:18Z at HEAD 6bb768f (digest `v3:sha256:7b456bff…`). The staleness trigger: quick-tasks 261017-uwr → 261019-pe0 (37 commits, slot-5 monitor redesign + footer keycap seams + version bump) evolved shared TUI surfaces — app.py, strings.py, styles.tcss, nav.py, selection.py, run_config.py are all inside this phase's covered set. Numstat over the 24 covered implementation files: **8 files changed** (app.py +162/-113, strings.py +179/-70, styles.tcss +119/-32, nav.py +26/-0, selection.py +9/-0, services/run_config.py +132/-0, test_pilot_nav_shell.py +35/-12, test_pilot_selection.py +10/-4); **16 files byte-identical** (0 diff lines), including the entire SC core — download_queue.py, zenodo_bundle.py, data_manager.py, env_check.py, registries.py, gauntlet.py, services/selection.py, __main__.py, directories_config.py, both stderr fixtures, and the download_queue/gauntlet/pilot_data_manager/pilot_selection_custom test modules.

**Method:** goal-backward re-verification of every SC chain against the CURRENT tree at 5783567. This pass's own executions: the caller-directed evidence lane (`-k "download or data_manager or queue"` — 277 passed), a 14-test named SC pin batch, the full zenodo module (SC4's lane — 19 of its 23 tests fall outside the `-k` filter, so the whole module was run), the two delta-touched test modules in full, both data_manager golden snapshot tests by name, scoped ruff + ty over the delta files, debt-marker greps, the decision-coverage gate, and a symbol-level audit of every delta against the SC chain endpoints. Full suite NOT re-run per caller instruction (caller-documented known-good gates; documented collateral: `test_storage_overview_defaults_mirror_real_consumers` fails while `pipeline/logs` exists — not in any lane run here; intermittent slot-4 pty TIMEOUT under load — no pty test in this phase's lanes).

---

## Staleness Resolution (the delta's interaction with the SC chains)

The trigger was real — shared surfaces did evolve — but every delta is disjoint from or additive to the SC chains:

1. **app.py (+162/-113): monitor imports / QuitConfirmModal / footer + the ctrl+c redesign; zero queue-spine impact.** Delta grep for every queue-spine symbol (`kick_download_queue`, `run_download_queue`, `boot_resume_queue`, `QueueEventMessage`, `apply_queue_event`, `download_queue`, `DownloadQueueService`) returns **zero matching delta lines**. Spine re-read at HEAD: `QueueEventMessage` :415, the shared `DownloadQueueService()` :665-688, `kick_download_queue` :870 (busy-lock check-and-set intact), the exclusive `@work(exclusive=True, thread=True)` driver :893-894, `boot_resume_queue` :991/:1003; `tui/__main__.py:100` still `app.call_later(app.boot_resume_queue)` before `run` (byte-identical). Worker-group isolation preserved: driver uses its default group (:893) while the WR-02 `_exit_kill_worker` keeps `group="exit-kill"` (:1267-1269) — no exclusivity interaction. The one large deletion (66 lines, the old `on_event` ctrl+c intercept) is exit-channel UX replaced by the 261017-mad/261018-08g redesign (`ctrl+c` is no longer an exit key; the WR-02 kill worker and its `ExitKillsDone` completion survived intact at :1250-1291) — no queue interaction, no phase-10 SC surface.
2. **strings.py (+179/-70): APP_TITLE / ABOUT / LNC_ / MON_ blocks only.** Delta grep for `DL_`/`QUEUE_`/`ZENODO` returns zero matching lines; the DL_/QUEUE_ block census is 57 before and after (the 10-03 Copywriting Contract home is untouched); `ENV_ROUTE_MISSING_DATASETS` intact at :324 with its in-block "stays byte-identical" note at :992.
3. **styles.tcss (+119/-32): monitor-only selectors.** Delta hunks sit in the `WizardModal`/`DirPickerModal`/`#mon-*` regions (the 261019 slot-5 no-fill law work); zero data-manager/queue/zenodo selectors touched. Proof by behavior: both data_manager golden snapshots (`data_manager.svg`, `data_manager_presence.svg`) are content-unchanged since 6bb768f AND their snapshot tests pass at HEAD under the evolved stylesheet — the phase-10 render surface is byte-stable.
4. **nav.py (+26): additive footer-refresh seams** (`refresh_pairs`/`refresh_left_pairs` on KeycapsStatic, the 261018-toe per-tab footer work). `NAV_SLOTS` untouched — slot 3 still `NavSlot(3, S.NAV_LABEL_DATA, "data_manager", None)` at :87.
5. **screens/selection.py (+9): additive `Y`/`N` binding twins** in `LaunchConfirmModal` (261018-08g, slot-4 gate scope). The presence overlay, `apply_queue_event`, `apply_queue_progress`, and the model-lane `d` action are untouched (purely additive bindings with `show=False`).
6. **services/run_config.py (+132/-0): purely additive** — `_argv_flag_values`, `_comma_filter_names`, `argv_matrix` appended after :1207 (monitor rerun-lane helpers). `load_state`/`resolve_dirs` (the SC1/10-07 `_datasets_base` chain endpoint) have zero delta lines.
7. **test deltas are in-place body updates** (nav help modal / priority-binding / help-modal tests evolving with the footer work) — no phase-10 test removed or renamed; both modules green in full (53 passed).

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP SC) | Status | Evidence |
|---|--------------------|--------|----------|
| 1 | SC1 one-click download via registry `download_url`; on landing, presence flips to ✓ in the selection table AND the environment check | ✓ VERIFIED | **Chain intact at HEAD 5783567 — every chain endpoint byte-identical or delta-disjoint.** Engine (download_queue.py), env_check.py, registries.py byte-identical (0 diff lines); run_config.py's `resolve_dirs`/`load_state` untouched (delta purely additive after :1207); screens/selection.py delta is 9 additive Y/N modal bindings (slot-4 scope), zero changes to the presence overlay or `apply_queue_event`; `pipeline/datasets_info.json` untouched. Behavioral: the three `_cr01` agreement tests (spec-without-file, relative-file CWD≠repo, default control), the R-02 dataset census (46/4), the model-channel census (38/21), `test_missing_datasets_flips_over_done_reconciled_entries_cr01`, and `test_backend_missing_snapshot_flips_over_real_seeded_state_cr01` all green in this pass's named batch. |
| 2 | SC2 queue persists across TUI exit/crash and resumes where it stopped after restart | ✓ VERIFIED | **Persistence spine byte-identical (download_queue.py 0 diff lines) and provably avoided by the app.py delta** (zero queue-spine symbols in the +162/-113). Spine re-read at HEAD: `QueueEventMessage` :415, shared service :665-688, kick guard :870-891 (busy-lock check-and-set, synchronous flag before any await), exclusive thread driver :893, `boot_resume_queue` :991/:1003; `tui/__main__.py:100` `call_later` before `run` (byte-identical). Worker-group isolation re-checked (:893 default group vs :1267 `exit-kill`). Behavioral: `test_boot_resume_rehydrates_and_kicks_once` + `test_boot_resume_without_pending_never_kicks` green by name this pass. |
| 3 | SC3 every landed download reconciles rows vs n_audit; mismatches prominent, never silently accepted | ✓ VERIFIED | Reconcile kernel byte-identical (download_queue.py 0 diff lines): candidate-only temp registry, absolute `Dataset_path`, all four output flags at temp paths, empty-overlay env; `merge_presence` overlays done keys only; mismatch never auto-deletes; `reaudit_baseline` explicit-only. Presentation byte-identical (data_manager.py 0 diff lines): `_render_banners` mismatch block, mismatch+failed sorted to top. The strings delta contains zero QUEUE_ lines (census 57→57). Behavioral: `test_mismatch_banner_block_and_sort_to_top` green by name this pass. |
| 4 | SC4 Zenodo bulk bundle (record 19135551, once public) reachable as alternate whole-package entry | ✓ VERIFIED | zenodo_bundle.py and data_manager.py both byte-identical (0 diff lines): `ZENODO_RECORD_ID` frozen-record pin + API URL guarded by `test_constants_frozen_record_id_and_api_url` (green this pass in the full module run), four-state probe, guarded enqueue, never-silent `DL_ZENODO_DISABLED_TOAST` (the string is untouched — zero ZENODO delta lines in strings.py). Behavioral: the FULL zenodo module (23 tests, 19 of which fall outside the `-k` filter) green this pass, including `test_enqueue_zenodo_persist_failure_refused_no_ghost_row` and `test_z_enqueues_only_when_public_never_silent_otherwise`. |
| 5 | SC5 subprocess/thread-worker discipline (console never freezes); zero credentials stored or echoed | ✓ VERIFIED | Popen discipline byte-identical (download_queue.py 0 diff lines): LIST argv + `start_new_session=True` + PIPEs + `env=dict(os.environ)` on both lanes (:1846, :2006) and the audit leg (:2576, the documented one-override reroute at :2512/:2701 — no credential env). Credential-free `_ENTRY_FIELDS` re-read at HEAD (:237): the 12-field set (key/kind/state/attempts/enqueued_at/started_at/finished_at/last_percent/interrupted/log_path/problems/reconcile) — nothing else survives persist (:1432). `test_service_module_never_imports_modelscope` green by name this pass. The exit-channel redesign since the prior pass (ctrl+c no longer an exit key; the on_event intercept removed) touches no queue interaction — the WR-02 exit-kill worker and its unconditional `ExitKillsDone` completion are intact (:1250-1291), and the download driver's exclusivity group is distinct from every new worker's. |

**Score:** 5/5 truths verified (0 present-but-behavior-unverified).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tui/services/download_queue.py` | The phase engine: rerouted `_datasets_base`, six landing legs, reconcile kernel, Popen discipline, zenodo branch, credential-free schema | ✓ VERIFIED | Byte-identical since 6bb768f (0 diff lines); reroute, legs, kernel, and schema intact; census pins + agreement tests green this pass |
| `tui/services/zenodo_bundle.py` | Four-state probe + guarded bundle driver (record 19135551) | ✓ VERIFIED | Byte-identical (0 diff lines); constants pin green this pass |
| `tui/screens/data_manager.py` | Slot-3 screen: two-pane layout, five-state glyphs, banners, drill-down, Zenodo line, d/r/x/a/enter/g/z | ✓ VERIFIED | Byte-identical (0 diff lines); module's 64-test lane green inside the 277-pass batch; both goldens green by name |
| `tui/app.py` | Shared queue service, exclusive driver worker, kick guard, boot resume, QueueEventMessage forward | ✓ VERIFIED | Delta-audited: zero queue-spine delta lines; spine re-read at :415/:665-688/:870/:893/:991; boot-resume pair green by name |
| `tui/__main__.py` | D-06 boot path | ✓ VERIFIED | `app.call_later(app.boot_resume_queue)` at :100, before `run` (byte-identical) |
| `tui/screens/nav.py` | Slot 3 = real data_manager target | ✓ VERIFIED | Delta additive footer-refresh seams only; `NAV_SLOTS` slot 3 → `data_manager` at :87 |
| `tui/screens/selection.py` | Presence overlay + apply_queue_event + shared-service d | ✓ VERIFIED | Delta = 9 additive Y/N modal bindings (slot-4 scope); overlay, done-refresh, and d lane untouched; residue regression green in the named batch |
| `tui/services/run_config.py` | SC1 chain endpoint (`resolve_dirs(load_state()).dataset_root_abs`) | ✓ VERIFIED | Delta purely additive after :1207 (argv_matrix helpers); `resolve_dirs`/`load_state` untouched; three `_cr01` agreement tests green |
| `tui/strings.py` | The DL_/QUEUE_ operator-copy single home (+ENV_ROUTE amendment) | ✓ VERIFIED | Delta confined to APP_TITLE/ABOUT/LNC_/MON_; DL_/QUEUE_ census 57→57, zero DL_/QUEUE_/ZENODO delta lines; ENV_ROUTE hint intact at :324 |
| `tui/styles.tcss` | Data-manager surface styles | ✓ VERIFIED | Delta confined to monitor selectors (`#mon-*`, WizardModal/DirPickerModal); zero data-manager selectors touched; data_manager goldens byte-stable and green under the evolved sheet |
| `tests/tui/test_services_download_queue.py` | `_cr01` agreement + transition table + reconcile + persist-rollback + census lanes | ✓ VERIFIED | Byte-identical since 6bb768f; census + agreement + flip + persist + never-imports pins green by name this pass |
| `tests/tui/test_services_zenodo_bundle.py` | Probe/bundle/never-silent lanes | ✓ VERIFIED | Byte-identical since 6bb768f; full module 23/23 green this pass |
| `tests/tui/test_pilot_data_manager.py` | Screen-tier Pilot proofs incl. mismatch banner, z-never-silent, boot resume, goldens | ✓ VERIFIED | Byte-identical since 6bb768f; module lane green inside the 277-pass batch; five named tests green this pass |
| `tests/tui/test_pilot_selection_custom.py` | Selection d binding + overlay + toasts + the IN-01 residue regression | ✓ VERIFIED | Byte-identical since 6bb768f; residue regression green by name this pass |
| `tests/tui/test_pilot_nav_shell.py`, `tests/tui/test_pilot_selection.py` | Shared-surface lanes (delta-touched) | ✓ VERIFIED | In-place body updates only (footer/help-modal evolution); both modules green in full this pass (53 passed) |
| Golden snapshots (`data_manager.svg`, `data_manager_presence.svg`) | Goldens match current render | ✓ VERIFIED | Content unchanged since 6bb768f (snapshot-dir diff shows only monitor/run_config goldens moved); both tests green by name at HEAD — byte-stable render under the evolved styles.tcss |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `DownloadQueueService._datasets_base()` | `run_config.resolve_dirs(run_config.load_state()).dataset_root_abs` | the same chain the env-check `dataset_dirs` kernel and `compose_argv`'s `--dataset_root` consume | ✓ WIRED | Engine byte-identical; run_config delta purely additive (chain functions untouched); three `_cr01` agreement tests green by name this pass |
| `tui/app` shared service | driver worker → `QueueEventMessage` → `DataManagerScreen.apply_queue_event` / `SelectionScreen.apply_queue_event` + toasts | the 10-04/10-05 spine | ✓ WIRED | Spine re-read at :415/:665-688/:870/:893/:991; app.py delta contains zero queue-spine hunks; boot-resume pair green by name |
| `tui/__main__` | `app.boot_resume_queue` | `call_later` before `run` (:100) | ✓ WIRED | Byte-identical; boot-resume pair green by name |
| `SelectionBackend` | `download_queue.reconciled_rows` + `merge_presence` → `registries.presence_for` | the D-11 overlay (pure read, no service instance) | ✓ WIRED | screens/selection.py delta = additive modal bindings only; flip `_cr01` tests green by name |
| `tui/screens/nav` NAV_SLOTS slot 3 | `data_manager` target | `action_nav` routing | ✓ WIRED | nav.py delta additive; slot 3 intact at :87 |
| `tui/screens/data_manager` | `download_queue` + `zenodo_bundle` (Protocol seam) → `S.` strings | service results only, screen computes nothing | ✓ WIRED | Both sides byte-identical; named z/persist tests green |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `_datasets_base()` | `dirs.dataset_root_abs` | `run_config.load_state()` → `resolve_dirs` (REPO_ROOT-anchored) | ✓ | FLOWING — engine byte-identical, chain functions untouched; `_cr01` agreement tests green by name |
| `_render_missing` / `MissingSnapshot` | `snapshot.missing` / `rows` | `registries.load_n_audit` + disk scan through the Backend | ✓ | FLOWING — overlay + presence-rows `_cr01` tests green by name |
| `_progress_cell` + `apply_queue_progress` | percent / speed | real stderr pump → `parse_progress`/`parse_speed` (last-token, verbatim) | ✓ | FLOWING — engine + both screens byte-identical; residue regression green by name |
| `_reconcile_cell` | declared/measured | the audit subprocess's temp n_audit.json verdict | ✓ | FLOWING — kernel byte-identical; mismatch banner test green by name |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|--------|---------|--------|--------|
| Caller-directed evidence lane (download/data_manager/queue) | `.venv/bin/python -m pytest tests/tui -q -k "download or data_manager or queue"` | 277 passed, 999 deselected in 19.18s | ✓ PASS |
| Named SC batch: three `_cr01` agreement + R-02 census 46/4 + model census 38/21 + env-flip `_cr01` + backend-flip `_cr01` + zenodo persist rollback + never-imports-modelscope + boot-resume pair + z-never-silent + mismatch banner + IN-01 residue | `.venv/bin/python -m pytest <14 test IDs>` | 14 passed in 1.32s | ✓ PASS |
| Full zenodo module (SC4 lane — 19 of 23 tests fall outside the `-k` filter) | `.venv/bin/python -m pytest tests/tui/test_services_zenodo_bundle.py -q` | 23 passed in 0.12s | ✓ PASS |
| Delta-touched test modules in full | `.venv/bin/python -m pytest tests/tui/test_pilot_nav_shell.py tests/tui/test_pilot_selection.py -q` | 53 passed in 28.51s | ✓ PASS |
| data_manager golden snapshots under the evolved styles.tcss | `.venv/bin/python -m pytest tests/tui/test_snapshots.py -q -k "data_manager"` | 2 passed, 9 deselected in 0.57s | ✓ PASS |
| Covered-set numstat vs prior verified HEAD | `git diff 6bb768f..HEAD --numstat -- <24 covered files>` | 8 changed / 16 byte-identical; all SC cores in the byte-identical set | ✓ PASS |
| app.py delta queue-spine audit | grep of the full delta for kick/run/boot_resume/QueueEventMessage/apply_queue_event/download_queue/DownloadQueueService | zero matching delta lines | ✓ PASS |
| strings.py delta DL_/QUEUE_/ZENODO audit | grep of the full delta | zero matching delta lines; DL_/QUEUE_ census 57→57 | ✓ PASS |
| Worker-group isolation (driver vs exit-kill vs any new worker) | grep `@work` declarations in tui/app.py | driver default group :893 vs `exit-kill` :1267 — no interaction | ✓ PASS |
| ruff (the seven delta .py files) | `.venv/bin/python -m ruff check …` | All checks passed | ✓ PASS |
| ty (`tui/` tree + both delta test files) | `.venv/bin/python -m ty check …` | All checks passed | ✓ PASS |
| Debt markers (TBD/FIXME/XXX/TODO/HACK) over the delta files | grep -n -E | 0 hits (remaining `PLACEHOLDER` tokens are the SEL_/WIZ_/MON_ Input-attribute string constants, by design) | ✓ PASS |

Environment notes honored (caller): `test_storage_overview_defaults_mirror_real_consumers` (pipeline/logs collateral) is in no lane run here; no slot-4 pty test is in this phase's lanes (the 28.51s module run contains no pty-lane flake member).

### Probe Execution

No probe scripts are declared for this phase (plans' verify blocks are pytest/make lanes) — N/A.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DATA-01 | 10-01, 10-04, 10-05, 10-07 | One-click ModelScope download, registry `download_url` sole authority; presence flips in selection table AND env check | ✓ SATISFIED | SC1 row: engine byte-identical, chain functions untouched, screen delta disjoint from the overlay; agreement + census + flip tests green by name this pass |
| DATA-02 | 10-01, 10-04, 10-06 | Persistent queue + resume across crash/restart | ✓ SATISFIED | SC2 row: engine byte-identical; app.py delta audit shows zero queue-spine hunks; boot-resume pair green by name |
| DATA-03 | 10-02, 10-06 | Row-count reconciliation vs n_audit; mismatches prominent, never silent | ✓ SATISFIED | SC3 row: kernel + presentation byte-identical, strings census unchanged; mismatch banner test green by name |
| DATA-04 | 10-03, 10-06 | Zenodo whole-package alternate entry (record 19135551) | ✓ SATISFIED | SC4 row: service + screen byte-identical; full 23-test module green this pass |

No orphaned requirements (REQUIREMENTS.md maps exactly DATA-01..04 to Phase 10; all four marked Complete; every ID claimed across 10-01..10-07 plans).

### Decision Coverage

`check.decision-coverage-verify` at this pass: **16/16 honored, zero not-honored** — no resolver skip this round (the prior pass's invocation-form limitation did not recur). All trackable CONTEXT.md decisions are honored by shipped artifacts.

### Anti-Patterns Found

None. Debt-marker greps over the delta files return zero hits (the `_PLACEHOLDER` string constants are Input placeholder attributes, by design — same disposition as every prior pass). No stub patterns, no empty implementations. The `MODEL_DOWNLOAD_PROGRAM` subprocess child string remains the only textual modelscope mention in the byte-identical engine (argv data by design, AST-verified in prior passes). New-scope scan of the delta (e-verification evidence gate #3304): nothing to report — the delta contains no unevidenced blocker-class finding; every shared-surface change is either byte-disjoint from the SC chains or carries its own green tests (the delta-touched modules' 53-pass run).

### Advisory (carried forward)

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | WR-01 failed KIND_MODEL download → models 下载 column 已下载 (is_dir presence vs config.json done gate, tui/services/selection.py) | other | Carried; services/selection.py byte-identical since the prior verified pass (0 diff lines over 6bb768f..HEAD); model presence column is dcl/mlc scope, no phase-10 SC covers it; disposition-open in 10-REVIEW-DISPOSITION.md |
| 2 | IN-01 z probe-in-flight window asserts the disabled toast as fact (data_manager.py, the != PROBE_PUBLIC arm) | other | Carried; data_manager.py byte-identical since the prior verified pass (0 diff lines); transient copy issue, never-silent behavior unaffected; disposition-open |

### Advisory Resolved This Round (adjudication)

| Finding | Adjudication | Evidence |
|----------|--------------|----------|
| **IN-02 (carried prior)** — `ABOUT_MILESTONE_STAGE` named phase 9 (strings.py) | **RESOLVED out-of-band** by the milestone-closeout version commits (effb5bf v1.2.0 bump + 3961d2c about pin): the string now reads "v1.2.0 — full TUI console delivery (Phases 7-12)" in both languages. Dropped from the carried list | strings.py re-read at :1035-1041 this pass; the strings delta since 6bb768f touches APP_TITLE/ABOUT/LNC_/MON_ blocks only (zero DL_/QUEUE_/ZENODO lines — delta grep empty; DL_/QUEUE_ census 57 before and after) |

### Human Verification Required

None. Both prior live items remain discharged (10-UAT.md, 2026-10-13: the GB10 live smoke incl. the presence flip, and the `g` four-artifact check). The staleness delta (slot-5 monitor + footer + version work) adds no phase-10 SC surface — every touched file is either byte-disjoint from the SC chains (verified by symbol-level delta audit) or carries its own green lane (delta-touched modules 53/53). All five SC behaviors are re-proven mechanically this pass (369 green test executions across the six lanes, incl. the agreement, census, flip, banner, boot-resume, z-never-silent, persist-rollback, residue, and golden tests).

### Gaps Summary

None. The staleness trigger is cleared: the delta since the prior verified pass (6bb768f → 5783567, 37 commits of slot-5 monitor/footer/version work) provably avoids every SC chain — the engine (`download_queue.py`), the zenodo service, the data-manager screen, env_check, registries, gauntlet, services/selection, `__main__`, directories_config, and four of six test modules are byte-identical (numstat-verified 0 diff lines); the eight changed files are each either additive-and-disjoint (nav footer seams, selection Y/N modal twins, run_config argv_matrix helpers), monitor-scoped (styles `#mon-*` selectors, strings APP/ABOUT/LNC_/MON_ blocks with DL_/QUEUE_ census unchanged at 57), or delta-audited away from the queue spine (app.py — zero matching delta lines, worker-group isolation re-checked). The data-manager goldens are byte-stable and green under the evolved stylesheet. The carried IN-02 advisory is RESOLVED (milestone string updated by the version commits) and removed from the advisory list. SC1-SC5 all hold at HEAD 5783567 with zero regressions.

### Fingerprint Refresh

`covered_files`/`covered_digest` in the frontmatter are the verbatim `verification.fingerprint` output at HEAD 5783567 (supersedes `v3:sha256:7b456bff…` of the prior pass; identical 38-file scope, new digest reflecting the strings/styles/nav/selection/run_config/app/test deltas).

---

_Verified: 2026-10-19T12:14:40Z (HEAD 5783567)_
_Verifier: Claude (gsd-verifier, staleness refresh round 7, post-pe0)_
