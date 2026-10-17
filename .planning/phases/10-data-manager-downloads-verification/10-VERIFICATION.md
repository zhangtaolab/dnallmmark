---
phase: 10-data-manager-downloads-verification
verified: 2026-10-17T05:12:20Z
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
covered_digest: "v3:sha256:bba6fc3ef47ce3a43bdd051d419700b475809447c7f8504cf4231f1ae8fc07d8"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions: []
advisory:
  - finding: "WR-01 (carried) — a failed KIND_MODEL download can flip the selection models 下载 column: model_presence gates on is_dir only (tui/services/selection.py:501+, the gate at :544) while the model-lane done gate requires config.json (MODEL_DONE_MARKER)"
    category: other
    reason: "Carried forward unchanged (model_presence re-read at this pass: still the is_dir seam; the delta did not touch it). Model presence column is dcl/mlc scope layered after phase 10; models are not n_audit subjects; no phase-10 SC covers it. Disposition-open in 10-REVIEW-DISPOSITION.md"
    evidence_status: "code-read at this pass: is_dir seam intact at tui/services/selection.py:544"
  - finding: "IN-01 (carried) — z pressed during the mount probe-in-flight window fires DL_ZENODO_DISABLED_TOAST while _zenodo_state is still None (data_manager.py:640 init; the != PROBE_PUBLIC arm at :1300)"
    category: other
    reason: "Carried forward unchanged — data_manager.py is byte-identical since the prior verified HEAD (not in this delta). Transient copy issue; SC4 reachability and never-silent behavior unaffected (a toast always fires). Disposition-open"
    evidence_status: "git diff 2e8dcfa..HEAD shows zero data_manager.py hunks; behavior unchanged from the prior pass"
  - finding: "IN-02 (carried) — ABOUT_MILESTONE_STAGE stale (names phase 9) in tui/strings.py:1021-1025"
    category: other
    reason: "Carried forward (bilingual _t form; text still reads 本相位: 9 / current: Phase 9 custom onboarding). Cosmetic milestone metadata; no SC relevance; the 152-line strings delta (exit-confirm + launch-confirm copy) did not touch it. Disposition-open"
    evidence_status: "code-read at this pass: still 'delivered: Phases 7-8 · current: Phase 9' in both languages"
  - finding: "08-REVIEW IN-01 (carried, disposition-open) — slot-2's apply_queue_progress stores the live percent/speed before the kind guard (tui/screens/selection.py:1593+); the stored values are never read for non-model keys"
    category: other
    reason: "Hygiene-only twin of the fixed slot-3 item; the model lane is not an n_audit subject and no phase-10 SC reads those values for dataset keys. Disposition-open in the 08 review of the feedback-round delta. Non-blocking per that review"
    evidence_status: "code-read at this pass: store-then-guard order intact at tui/screens/selection.py:1593; unchanged by this delta (selection.py delta is ConfirmModal-only)"
---

# Phase 10: Data Manager (Downloads & Verification) Verification Report — Convergence Re-Verification (Staleness Refresh, Round 5)

**Phase Goal:** Dataset gaps are closable in-session before launch — one-click ModelScope download driven by the registry's authoritative `download_url`, a persistent resumable queue, and row-count reconciliation against n_audit — so an env-check presence FAIL is always diagnosable and fixable from the console
**Verified:** 2026-10-17T05:12:20Z at HEAD 46b898a (branch autorun)
**Status:** passed — 5/5 SCs hold at the refreshed HEAD; zero regressions from the post-2e8dcfa delta
**Re-verification:** Yes — staleness refresh (round 5). Prior pass 5/5 at HEAD 2e8dcfa (2026-10-16T07:23:52Z, digest `v3:sha256:14d6970a…`). Since then the delta touching this phase's covered set: **hhx-tail + exit-confirm quicks** (v0z a32d74a guarded exit/ctrl+q, vxr ef2e365 slot-5 kill + Q exit, cdr 0980956 ctrl+c any-focus, dnr 8c995da/b270920 prominent Y/N + ExitModal affordances — all app.py/strings.py/monitor/run_config-centric), **poa** (cf6335c/6b14a0f launch-confirmation copy + picker toggle anchor — selection.py ConfirmModal-adjacent), **2478cfc** (compat v1.3 adoption: `pipeline/dnallm_compat.json` regenerated against DNALLM v1.3@44c22d4, PlantHelixSeek + FungiHelixSeek flipped to adapted → the MODEL-channel census pin moved 36→38 clean / 23→21 not_adapted, updated in the same commit), and **eea** (d22903a version-independent corrupt-zip fixture in the zenodo test module; data-chain work outside the covered set). The engine, the zenodo service, and the data-manager screen are **byte-identical** to the prior verified pass; the app/selection/strings deltas were audited hunk-by-hunk for queue-spine impact (see the delta-interaction section).

**Method:** goal-backward re-verification of every SC chain against the CURRENT code on disk; 376 green test executions by this verifier across six covered lanes (queue module 202, zenodo module 23, data-manager pilot 61, selection-custom pilot 27, selection pilot 38, nav shell 15) plus the 11-pass snapshot lane; ten named behavioral tests run individually (three `_cr01` agreement, both census pins, zenodo persist rollback, boot-resume pair, z-never-silent, mismatch banner); an independent AST import check; scoped ruff + ty; debt-marker greps. Full suite NOT re-run per caller instruction — caller-provided known-good gates on this exact HEAD (46b898a): full suite 1F/1858P (the single machine-local member), node 26/26, ruff+ty green, data_manager goldens green, CI four lanes green (PR #7), `make data` idempotent.

---

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP SC) | Status | Evidence |
|---|--------------------|--------|----------|
| 1 | SC1 one-click download via registry `download_url`; on landing, presence flips to ✓ in the selection table AND the environment check | ✓ VERIFIED | **The CR-01 reroute and both flip halves are intact — re-proven at HEAD 46b898a.** Chain code-read: `_datasets_base()` (download_queue.py:1211-1240) reads `run_config.resolve_dirs(run_config.load_state()).dataset_root_abs` per call, never memoized; the consumption side binds the SAME chain (env_check.py:182, `_dataset_dirs` kernel on `dirs.dataset_root_abs`); `compose_argv` threads `--dataset_root` (run_config.py:1159+ — the 4-line run_config delta since 2e8dcfa is docstring-only terminology, verified hunk-by-hunk, no code change); the reconcile staged `Dataset_path` absolutization joins against `self._datasets_base()` (download_queue.py:2548). Six landing legs live at :2204/:2233/:2409/:2480/:2548/:2998. Selection half: `SelectionBackend.load_selection_data` builds presence over `reconciled_rows()` + `merge_presence` (selection.py:382-383), `apply_queue_event` refreshes on done (:1564) — both untouched by the delta (selection.py delta since 2e8dcfa is confined to the ConfirmModal class + poa copy). Slot-2 `d` = `action_download_model` (the c4j model lane, :1963); dataset enqueue + the registry-`download_url` authority live on slot 3 (`action_enqueue_cursor` :1172, channel resolution reads `download_url` first — R-01); ENV_ROUTE_MISSING_DATASETS keeps the `[3]` keycap hint in both languages (strings.py:310-314, re-read). Behavioral: the three `_cr01` agreement tests (:4145 spec-without-file, :4169 relative-file CWD≠repo, :4191 default control) run by name — 5/5 green with the two census pins; `test_missing_datasets_flips_over_done_reconciled_entries_cr01`, `test_merged_audit_tasks_overlays_this_services_state_path_cr01`, `test_presence_rows_missing_set_equals_missing_datasets_keys_cr01` green in the 202-pass lane; `test_backend_missing_snapshot_flips_over_real_seeded_state_cr01` green in the 61-pass pilot lane; R-02 dataset census `test_r02_census_46_downloadable_4_disabled_over_committed_registry` green — **the compat v1.3 flip did NOT move the dataset 46/4 census** (it moved the MODEL-channel census pin, a c4j-era lane where models are not n_audit subjects; the model pin was updated in the same commit 2478cfc and is green at 38/21). Live corroboration: the maintainer's 10-16 session d-downloaded the newly-adapted PlantHelixSeek through this exact surface right after the compat flip and launched it through the new gate (sweep ran, GPU 91%) — the full download→presence→launch chain worked live on the current registry state. |
| 2 | SC2 queue persists across TUI exit/crash and resumes where it stopped after restart | ✓ VERIFIED | Persistence spine byte-identical since the prior pass (download_queue.py untouched since 190d1c4, which the prior pass verified): state at `settings.state_dir()/download_queue.json` through `settings.atomic_write`, the credential-free 12-field `_ENTRY_FIELDS` set (:237-241), `load()` tolerant recovery (downloading→pending with `interrupted=true`, `.corrupt` sidecar + diagnostic), the `_last_diagnostic` session memory (:1203-1207). App spine re-read at HEAD **after the exit-confirm restructure** (app.py absorbed +241 lines from v0z/vxr/cdr/dnr): the diff since 2e8dcfa contains ZERO hunks touching `kick_download_queue`/`run_download_queue`/`boot_resume_queue`/`QueueEventMessage`/`apply_queue_event`/the shared `download_queue` service — grep of the delta returns no queue-spine lines. The spine itself: ONE shared `DownloadQueueService()` (app.py:599, constructor-injectable), the exclusive `@work(exclusive=True, thread=True)` driver loop (:786-787) posting `QueueEventMessage` (:368) with the WR-02 generation guard, `kick_download_queue` busy-lock (:763-784), `boot_resume_queue` (:884) scheduled by `tui/__main__.py:100` (`app.call_later(app.boot_resume_queue)` BEFORE `run`). Behavioral: `test_boot_resume_rehydrates_and_kicks_once` + `test_boot_resume_without_pending_never_kicks` run by name — green; restart-resume + interrupted-downgrade + QUEUE_RESTART_NOTE rows in the 202-pass lane. |
| 3 | SC3 every landed download reconciles rows vs n_audit; mismatches prominent, never silently accepted | ✓ VERIFIED | Reconcile kernel byte-identical to the prior pass: candidate-only temp registry with ABSOLUTE `Dataset_path` joined against the rerouted base (:2540-2548), inert temp datasets-root, all four output flags at temp paths, empty-overlay env; `merge_presence` (:515) overlays done keys only; mismatch state carries declared/measured and NEVER auto-deletes (D-07); `reaudit_baseline` (:2724) stays the explicit-only worktree path (R-03). Presentation re-read: `_render_banners` (:978) mounts one `QUEUE_BANNER_MISMATCH` block per number-carrying mismatch (KIND_MODEL excluded), `_sorted_entries` (:492) sorts mismatch+failed to the top, `_reconcile_cell` (:1085) renders pass/running/mismatch. Behavioral: `test_mismatch_banner_block_and_sort_to_top` run by name — green; the real-subprocess reconcile pair, `test_committed_artifacts_byte_unchanged_across_real_reconcile_run` (:2767), and `test_reaudit_argv_exactly_interpreter_and_script_no_flags` (:2615) green in the 202-pass lane. |
| 4 | SC4 Zenodo bulk bundle (record 19135551, once public) reachable as alternate whole-package entry | ✓ VERIFIED | zenodo_bundle.py byte-identical since the prior pass: constants intact (:50-59 — `ZENODO_RECORD_ID = "19135551"`, frozen `ZENODO_API_URL`, PROBE_PUBLIC/NOT_PUBLIC/FAILED), four-state `_render_zenodo_line` (data_manager.py:1004), `action_zenodo_bundle` (:1297) enqueues only when public, otherwise the never-silent `DL_ZENODO_DISABLED_TOAST`. The hhx WR-02 rollback on the bundle lane survives intact (download_queue.py:1579-1588: `_persist_locked()` failure pops the appended entry and answers `ACTION_PERSIST_FAILED` — no ghost row). Behavioral: `test_enqueue_zenodo_persist_failure_refused_no_ghost_row` (:3705) run by name — green; `test_z_enqueues_only_when_public_never_silent_otherwise` (:1286) run by name — green; the eea corrupt-zip fixture rework (d22903a — version-independent for Python 3.14's tightened `is_zipfile` EOCD validation) lands in the 23-pass zenodo lane, all green. |
| 5 | SC5 subprocess/thread-worker discipline (console never freezes); zero credentials stored or echoed | ✓ VERIFIED | Popen discipline byte-identical: LIST argv + `start_new_session=True` + PIPEs + `env=dict(os.environ)` at download_queue.py:1846 and :2006 (dataset + model lanes); the exclusive thread-worker driver + kick busy-lock (app.py:786/:763) keep the console free — the exit-confirm restructure added MORE app-level key handling (ctrl+c/ctrl+q on_event) without touching the worker discipline. Zero modelscope imports: this verifier's own AST walk of download_queue.py returns zero Import/ImportFrom nodes naming modelscope; `test_service_module_never_imports_modelscope` (:850) green in the 202-pass lane. Credential surface: `_ENTRY_FIELDS` is exactly the 12-field credential-free set; env passed through with zero overrides. |

**Score:** 5/5 truths verified (0 present-but-behavior-unverified).

### The delta's interaction with the SC chains (checked, disjoint or additive)

1. **Exit-confirm family (v0z/vxr/cdr/dnr) vs SC2/SC5** — app.py absorbed +241 lines of quit-confirm/ctrl+c/kill-confirm/ExitModal machinery; a targeted grep of the full app.py delta for every queue-spine symbol (`kick_download_queue`, `run_download_queue`, `boot_resume_queue`, `QueueEventMessage`, `apply_queue_event`, `download_queue`) returns **zero matching delta lines** — the restructure completely avoided the queue spine. The spine was then re-read in full at HEAD (:368/:559/:599/:661/:763-784/:786-830/:884/:928) and is behaviorally pinned by the boot-resume pair + the 61-pass pilot lane.
2. **poa + dnr confirm prominence vs the x-cancel path** — selection.py's delta since 2e8dcfa is confined to ONE hunk region: the `ConfirmModal` class at :1221 (Y/N prominence + the new `LaunchConfirmModal` subclass, whose docstring pins "``ConfirmModal`` itself and every non-launch consumer (preset overwrite, **queue cancels**, wizard cancel) stay byte-identical on enter"). data_manager.py — byte-unchanged — imports and pushes the plain `ConfirmModal` for the x cancel; the 61-pass pilot lane exercises both cancel confirms green.
3. **compat v1.3 (2478cfc) vs the census surfaces** — the flip touches `pipeline/dnallm_compat.json` (MODEL adaptation map) and updates four census pins in the same commit: the phase-10 R-02 DATASET census (46 downloadable / 4 disabled over the committed official registry) is **unaffected and green by name at HEAD**; the MODEL-channel census pin (a c4j-era lane inside the covered test module) moved 36/23 → 38/21 and is green at its new values — the two newly-adapted model keys (PlantHelixSeek/FungiHelixSeek) gained clean ModelScope channel specs, which the maintainer then exercised LIVE (real d-download + launch on 10-16). The registry `download_url` authority (R-01) is untouched: `pipeline/datasets_info.json` is not in the compat commit's file set.
4. **eea fixture rework vs SC4** — d22903a rewires the corrupt-zip fixture to be version-independent (Python 3.14 `iszipfile` tightening); test-only, zenodo lane 23/23 green; no production change.
5. **strings delta vs the DL_/QUEUE_ contract** — the +152-line strings delta is exit-confirm/launch-confirm/monitor copy; the 57 `DL_`/`QUEUE_` constants remain the single home (grep: zero `DL_* =`/`QUEUE_* =` operator-copy definitions outside strings.py — only machine constants QUEUE_FILE_NAME/QUEUE_STATES in the service), and the ENV_ROUTE `[3]` amendment is byte-stable in both languages.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tui/services/download_queue.py` | The phase engine: rerouted `_datasets_base`, six landing legs, reconcile kernel, Popen discipline, zenodo branch, credential-free schema | ✓ VERIFIED | Byte-identical since the prior verified pass (last commit 190d1c4); reroute live at :1211-1240; legs at :2204/:2233/:2409/:2480/:2548/:2998; module lane 202 green |
| `tui/services/zenodo_bundle.py` | Four-state probe + guarded bundle driver (record 19135551) | ✓ VERIFIED | Byte-identical; constants :50-59 intact; 23 module tests green incl. the eea reworked fixture |
| `tui/screens/data_manager.py` | Slot-3 data-manager screen: two-pane layout, five-state glyphs, banners, drill-down, Zenodo line, d/r/x/a/enter/g/z | ✓ VERIFIED | Byte-identical since 2e8dcfa (zero delta hunks); all surfaces present; 61 pilot tests green |
| `tui/app.py` | Shared queue service, exclusive driver worker, kick guard, boot resume, QueueEventMessage forward | ✓ VERIFIED | Delta-audited: the +241 exit-confirm lines avoid the queue spine entirely; spine re-read at :559/:599/:661/:763/:786/:884/:928; pilot + nav lanes green |
| `tui/__main__.py` | D-06 boot path | ✓ VERIFIED | `app.call_later(app.boot_resume_queue)` at :100, before `run` |
| `tui/screens/nav.py` | Slot 3 = real data_manager target | ✓ VERIFIED | `NavSlot(3, S.NAV_LABEL_DATA, "data_manager", None)` at :87; nav-shell lane 15 green |
| `tui/screens/selection.py` | Presence overlay + apply_queue_event + shared-service d | ✓ VERIFIED | Overlay :382-383, apply_queue_event :1564, d lane :1963 — untouched by the ConfirmModal-only delta; selection pilot 38 + selection-custom 27 green |
| `tui/strings.py` | The DL_/QUEUE_ operator-copy single home (+ENV_ROUTE amendment) | ✓ VERIFIED | 57 module-attribute constants; ENV_ROUTE `[3]` intact in both languages (:310-314) |
| `tests/tui/test_services_download_queue.py` | Three `_cr01` agreement tests + transition table + reconcile + persist-rollback + census lanes | ✓ VERIFIED | 202 passed in 0.58s (model-census pin updated to 38/21 by 2478cfc in-lockstep with the registry) |
| `tests/tui/test_services_zenodo_bundle.py` | Probe/bundle/never-silent lanes | ✓ VERIFIED | 23 passed in 0.12s (eea version-independent corrupt-zip fixture) |
| `tests/tui/test_pilot_data_manager.py` | Screen-tier Pilot proofs incl. mismatch banner, z-never-silent, boot resume, slot-3 geometry | ✓ VERIFIED | 61 passed in 16.43s |
| `tests/tui/test_pilot_selection_custom.py` | Selection d binding + overlay + toasts | ✓ VERIFIED | 27 passed in 8.72s |
| Golden snapshots (data_manager.svg, data_manager_presence.svg, …) | Goldens match current render | ✓ VERIFIED | Snapshot lane 11 passed in 6.25s — goldens green unmodified on this tree |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `DownloadQueueService._datasets_base()` | `run_config.resolve_dirs(run_config.load_state()).dataset_root_abs` | the same chain the env-check `dataset_dirs` kernel (env_check.py:182) and `compose_argv`'s `--dataset_root` (run_config.py:1159+) consume | ✓ WIRED | Code-read at HEAD (run_config delta docstring-only) + three green `_cr01` agreement tests run by name |
| `tui/app` shared service | driver worker → `QueueEventMessage` → `DataManagerScreen.apply_queue_event` / `SelectionScreen.apply_queue_event` + toasts | the 10-04/10-05 spine | ✓ WIRED | app.py:599/:786/:928; selection.py:1564; pilot lanes green |
| `tui/__main__` | `app.boot_resume_queue` | `call_later` before `run` (:100) | ✓ WIRED | boot-resume pair run by name — green |
| `SelectionBackend` | `download_queue.reconciled_rows` + `merge_presence` → `registries.presence_for` | the D-11 overlay (pure read, no service instance) | ✓ WIRED | selection.py:382-383; overlay + flip tests green in the queue and pilot lanes |
| `tui/screens/nav` NAV_SLOTS slot 3 | `data_manager` target | `action_nav` routing | ✓ WIRED | nav.py:87; nav-shell lane 15 green |
| `tui/screens/data_manager` | `download_queue` + `zenodo_bundle` (Protocol seam) → `S.` strings | service results only, screen computes nothing | ✓ WIRED | 61 pilot tests green |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `_datasets_base()` | `dirs.dataset_root_abs` | `run_config.load_state()` → `resolve_dirs` (REPO_ROOT-anchored) | ✓ | FLOWING — read per call, never memoized; `_cr01` tests pin landing/consumption agreement across all three configurations |
| `_render_missing` / `MissingSnapshot` | `snapshot.missing` / `rows` | `registries.load_n_audit` + disk scan through the Backend | ✓ | FLOWING — overlay + presence-rows `_cr01` tests green |
| `_progress_cell` + `apply_queue_progress` | percent / speed | real stderr pump → `parse_progress`/`parse_speed` (last-token, verbatim) | ✓ | FLOWING — green in both pilot lanes; live rate ticks corroborated on camera |
| `_reconcile_cell` | declared/measured | the audit subprocess's temp n_audit.json verdict | ✓ | FLOWING — real-subprocess reconcile pair + byte-unchanged regression green |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|--------|---------|--------|--------|
| Queue module lane (3 `_cr01` + AST ban + reconcile + persist rollback + census + 190 others) | `.venv/bin/python -m pytest tests/tui/test_services_download_queue.py -q` | 202 passed in 0.58s | ✓ PASS |
| Zenodo module lane (incl. eea version-independent corrupt-zip fixture) | `.venv/bin/python -m pytest tests/tui/test_services_zenodo_bundle.py -q` | 23 passed in 0.12s | ✓ PASS |
| Data-manager pilot lane (mismatch banner, z-never-silent, boot resume, slot-3 geometry, drill-down) | `.venv/bin/python -m pytest tests/tui/test_pilot_data_manager.py -q` | 61 passed in 16.43s | ✓ PASS |
| Selection-custom pilot lane (d binding, overlay, toasts) | `.venv/bin/python -m pytest tests/tui/test_pilot_selection_custom.py -q` | 27 passed in 8.72s | ✓ PASS |
| Selection pilot lane (delta-touched test file, compat census pins) | `.venv/bin/python -m pytest tests/tui/test_pilot_selection.py -q` | 38 passed in 24.66s | ✓ PASS |
| Nav-shell lane (delta-touched test file, exit-confirm pins) | `.venv/bin/python -m pytest tests/tui/test_pilot_nav_shell.py -q` | 15 passed in 3.72s | ✓ PASS |
| Golden snapshots incl. data_manager goldens | `.venv/bin/python -m pytest tests/tui/test_snapshots.py -q` | 11 passed in 6.25s | ✓ PASS |
| Named: three `_cr01` agreement + R-02 dataset census + model census 38/21 | pytest (five test IDs) | 5 passed in 0.06s | ✓ PASS |
| Named: zenodo persist rollback, boot-resume pair, z-never-silent, mismatch banner | pytest (five test IDs) | 5 passed in 1.11s | ✓ PASS |
| Zero modelscope imports (independent of the pinned test) | `.venv/bin/python -c "ast.walk …"` over download_queue.py | 0 Import/ImportFrom nodes naming modelscope | ✓ PASS |
| ruff (scoped to the covered production files) | `.venv/bin/python -m ruff check …` | All checks passed | ✓ PASS |
| ty (scoped to the covered production files) | `.venv/bin/python -m ty check …` | All checks passed | ✓ PASS |
| Debt markers (TBD/FIXME/XXX/TODO/HACK) over covered production files | grep -n -E … | 0 hits (remaining "placeholder" tokens are Textual Input attributes + the slots-4/5 nav toast machinery, by design) | ✓ PASS |

Full-suite note (caller-provided box evidence on this exact HEAD 46b898a, not re-run here per instruction — single-lane discipline): full suite 1F/1858P (single machine-local member), node 26/26, ruff+ty green, data_manager goldens green, CI four lanes green (PR #7), `make data` idempotent. This verifier's own six lanes + snapshot lane (376 executions) are fully green at HEAD.

### Probe Execution

No probe scripts are declared for this phase (plans' verify blocks are pytest/make lanes) — N/A.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DATA-01 | 10-01, 10-04, 10-05, 10-07 | One-click ModelScope download, registry `download_url` sole authority; presence flips in selection table AND env check | ✓ SATISFIED | SC1 row: chain code-read at HEAD + three `_cr01` agreement tests green by name + overlay/flip tests green + live maintainer session (PlantHelixSeek full download→presence→launch chain on the current registry) |
| DATA-02 | 10-01, 10-04, 10-06 | Persistent queue + resume across crash/restart | ✓ SATISFIED | SC2 row: persistence spine byte-identical; app-spine delta audit shows zero queue-spine hunks; boot-resume pair green by name |
| DATA-03 | 10-02, 10-06 | Row-count reconciliation vs n_audit; mismatches prominent, never silent | ✓ SATISFIED | SC3 row: kernel byte-identical; real-subprocess reconcile + banner test green by name; byte-unchanged regression green |
| DATA-04 | 10-03, 10-06 | Zenodo whole-package alternate entry (record 19135551) | ✓ SATISFIED | SC4 row: constants + four-state line + z semantics + persist rollback green by name; 23 zenodo tests green |

No orphaned requirements (REQUIREMENTS.md maps exactly DATA-01..04 to Phase 10; all four marked Complete; every ID claimed in at least one plan's `requirements` frontmatter).

### Decision Coverage

`check.decision-coverage-verify --phase 10` at this pass: **16/16 honored** (the verb now resolves `10-CONTEXT.md`; the prior pass's `skipped` outcome was a resolver limitation, since fixed). Non-blocking gate; no drift.

### Anti-Patterns Found

None. Debt-marker greps (`TBD|FIXME|XXX`, `TODO|HACK`) return zero hits across all covered production files. No stub patterns, no empty implementations. The one textual `from modelscope…` hit in the engine is the FIXED subprocess child program string (`MODEL_DOWNLOAD_PROGRAM` — argv data by design, AST-verified not an import).

### Advisory (Out-of-SC, carried forward)

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | WR-01 failed KIND_MODEL download → models 下载 column 已下载 (is_dir presence vs config.json done gate, selection.py:544) | other | Carried; model presence column is dcl/mlc scope, no phase-10 SC covers it; disposition-open in 10-REVIEW-DISPOSITION.md |
| 2 | IN-01 z probe-in-flight window asserts the disabled toast as fact | other | Carried; data_manager.py byte-identical since the prior pass; transient copy issue, never-silent behavior unaffected; disposition-open |
| 3 | IN-02 ABOUT_MILESTONE_STAGE names phase 9 (strings.py:1021-1025) | other | Carried; cosmetic milestone metadata, untouched by the strings delta; disposition-open |
| 4 | 08-REVIEW IN-01: slot-2 apply_queue_progress stores percent/speed before the kind guard (selection.py:1593) | other | Carried from the delta review; hygiene-only, values never read for non-model keys; disposition-open in 08-REVIEW-DISPOSITION.md; non-blocking per that review |

### Human Verification Required

None. Both prior live items remain discharged (10-UAT.md, 2026-10-13: the GB10 live smoke incl. the presence flip, and the `g` four-artifact check). This refresh's delta was itself code-reviewed (08-REVIEW base 601aa51, 0C/3W/3I, disposition-open) and adds no phase-10 SC surface: the exit-confirm and confirm-prominence work avoids the queue spine entirely (delta-audited), and the compat v1.3 flip is corroborated LIVE — the maintainer d-downloaded the newly-adapted PlantHelixSeek through this exact data-manager surface on 10-16 and launched it through the new gate (sweep ran, GPU 91%), exercising the full download→presence→launch chain on the current registry state. All five SC behaviors are re-proven mechanically here (376 green executions incl. the agreement, flip, banner, boot-resume, z-never-silent, and persist-rollback tests).

### Gaps Summary

None. The staleness trigger is fully cleared and the delta is disjoint from or additive to every SC chain: the engine (`download_queue.py`), the zenodo service, and the data-manager screen are byte-identical to the prior verified pass; the app.py exit-confirm restructure (+241 lines) provably avoids the queue spine (zero delta hunks match any queue-spine symbol; spine re-read + boot-resume tests green); the selection.py delta is confined to the ConfirmModal class whose contract keeps queue cancels byte-identical (pilot lanes green); the compat v1.3 flip moves only the MODEL-channel census pin (updated in-lockstep, green at 38/21, live-corroborated) while the phase's R-02 DATASET census stays 46/4 green; the eea fixture rework is test-only. SC1-SC5 all hold at HEAD 46b898a with zero regressions.

### Fingerprint Refresh

`covered_files`/`covered_digest` in the frontmatter are the verbatim `verification.fingerprint` output at HEAD 46b898a (supersedes `v3:sha256:14d6970a…` of the 2e8dcfa pass; identical file scope, new digest reflecting the exit-confirm/launch-confirm strings + app/selection edits, the compat-driven census-pin update in the queue test module, and the eea zenodo fixture rework).

---

_Verified: 2026-10-17T05:12:20Z (HEAD 46b898a)_
_Verifier: Claude (gsd-verifier, convergence staleness refresh round 5)_
