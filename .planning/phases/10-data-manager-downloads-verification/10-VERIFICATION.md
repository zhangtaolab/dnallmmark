---
phase: 10-data-manager-downloads-verification
verified: 2026-10-17T07:49:18Z
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
covered_digest: "v3:sha256:7b456bff7c367663f381f2ce8cb5b2f977751af50d15ccb90c26c6a2a83972cf"
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
    reason: "Carried forward unchanged — tui/services/selection.py is byte-identical since the prior verified pass (0 diff lines, numstat-verified). Model presence column is dcl/mlc scope layered after phase 10; models are not n_audit subjects; no phase-10 SC covers it. Disposition-open in 10-REVIEW-DISPOSITION.md"
    evidence_status: "git diff eed1f75..HEAD: zero services/selection.py hunks; is_dir seam re-read at :544 this pass"
  - finding: "IN-01 (carried) — z pressed during the mount probe-in-flight window fires DL_ZENODO_DISABLED_TOAST while _zenodo_state is still None (data_manager.py:640 init; the != PROBE_PUBLIC arm at :1300)"
    category: other
    reason: "Carried forward unchanged — data_manager.py is byte-identical since the prior verified pass (0 diff lines). Transient copy issue; SC4 reachability and never-silent behavior unaffected (a toast always fires). Disposition-open"
    evidence_status: "git diff eed1f75..HEAD: zero data_manager.py hunks; the != PROBE_PUBLIC arm re-read at :1300 this pass"
  - finding: "IN-02 (carried) — ABOUT_MILESTONE_STAGE stale (names phase 9) in tui/strings.py:1021-1025"
    category: other
    reason: "Carried forward — strings.py is byte-identical since the prior verified pass (0 diff lines). Cosmetic milestone metadata; no SC relevance. Disposition-open"
    evidence_status: "git diff eed1f75..HEAD: zero strings.py hunks; text re-read this pass — still 'delivered: Phases 7-8 · current: Phase 9' in both languages"
resolved_advisories:
  - finding: "08-REVIEW IN-01 — slot-2 apply_queue_progress stored live percent/speed BEFORE the kind/state guard (tui/screens/selection.py), the hygiene twin of the fixed slot-3 item"
    resolution: "RESOLVED by quick-261017-klw (commit 0d02e18): the two live-dict stores moved BELOW the (model, downloading) guard — the exact ordering of the fixed slot-3 twin (data_manager.py, quick-261016-hhx). Regression test test_dataset_kind_tick_stores_no_live_dict_residue added in the same commit and green by name this pass (a dataset-kind downloading tick stores nothing in either slot-2 live dict). Dropped from the carried-advisory list"
    evidence: "git diff eed1f75..HEAD selection.py hunk @@ -1603,12 +1603,19 @@ (store-then-guard → guard-then-store); named test green in the 13-pass batch; full delta lane 28/28"
---

# Phase 10: Data Manager (Downloads & Verification) Verification Report — Micro Refresh (Post-klw, Round 6)

**Phase Goal:** Dataset gaps are closable in-session before launch — one-click ModelScope download driven by the registry's authoritative `download_url`, a persistent resumable queue, and row-count reconciliation against n_audit — so an env-check presence FAIL is always diagnosable and fixable from the console
**Verified:** 2026-10-17T07:49:18Z at HEAD 6bb768f (branch autorun)
**Status:** passed — 5/5 SCs hold at the refreshed HEAD; zero regressions from the post-eed1f75 delta; the 08-REVIEW IN-01 advisory is RESOLVED and dropped from the carried list
**Re-verification:** Yes — micro refresh (round 6, post-klw). Prior pass 5/5, report verified 2026-10-17T05:12:20Z at HEAD 46b898a, committed as eed1f75 (digest `v3:sha256:bba6fc3e…`). Since eed1f75 the delta touching this phase's covered set is the quick-261017-klw fix batch ONLY: 06d2679 (WR-01/02/03 exit-channel trio — tui/app.py +134 lines and test_pilot_run_config.py, the latter outside the covered set), 0d02e18 (IN-01/02/03 screen-hygiene trio — tui/screens/selection.py +13, tests/tui/test_pilot_selection_custom.py +35, plus env_check.py/run_config.py screens and their tests, outside the covered set), and 6e331d3 (07-CR-01 pipeline guard — pipeline/run_finetune.py, outside the covered set). Numstat over the full 24-file covered implementation set: **exactly three files changed** (app.py 134, selection.py 13, test_pilot_selection_custom.py 35); the download_queue engine, the data-manager screen, the zenodo service, strings.py, nav.py, and every service module are **byte-identical** (0 diff lines each). Caller note: the caller framed the delta as "selection.py only" — the measured delta is the three files above; the caller's substantive claim (cores byte-untouched) is confirmed, and the app.py exit-channel delta was audited hunk-by-hunk for queue-spine impact (below).

**Method:** goal-backward re-verification of every SC chain against the CURRENT code on disk. This pass's own executions: the delta-touched selection-custom pilot lane (28 passed), a 13-test named behavioral batch (three `_cr01` agreement tests, both census pins, zenodo persist rollback, boot-resume pair, z-never-silent, mismatch banner, backend-flip `_cr01`, and the new IN-01 residue regression), scoped ruff + ty on the three delta files, debt-marker greps, and the byte-diff of every covered file against eed1f75. Full suite NOT re-run per caller instruction — caller-provided known-good gates on this exact HEAD (6bb768f): full suite 1F/1867P (sole machine-local member), node 26/26, ruff+ty green, data_manager goldens green.

---

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP SC) | Status | Evidence |
|---|--------------------|--------|----------|
| 1 | SC1 one-click download via registry `download_url`; on landing, presence flips to ✓ in the selection table AND the environment check | ✓ VERIFIED | **Chain intact at HEAD 6bb768f — every chain file byte-identical to the prior verified pass except selection.py's progress-internals fix (presence overlay untouched).** Byte-diff vs eed1f75: download_queue.py, env_check.py, run_config.py, registries.py, data_manager.py = 0 lines. The selection.py delta is ONE hunk inside `apply_queue_progress` (:1603-1619) — the IN-01 store reordering — with zero changes to `load_selection_data`'s presence build (`reconciled_rows()` + `merge_presence`), `apply_queue_event`'s done-refresh, or the model-lane `d` action. Registry `download_url` authority: channel resolution unchanged in the byte-identical engine; `pipeline/datasets_info.json` untouched by the klw batch. Behavioral: the three `_cr01` agreement tests (spec-without-file :4145, relative-file CWD≠repo :4169, default control :4191), the R-02 dataset census (46 downloadable / 4 disabled), the model-channel census (38 clean / 21 not_adapted), `test_missing_datasets_flips_over_done_reconciled_entries_cr01`, and `test_backend_missing_snapshot_flips_over_real_seeded_state_cr01` all green by name in this pass's 13-test batch. |
| 2 | SC2 queue persists across TUI exit/crash and resumes where it stopped after restart | ✓ VERIFIED | **Persistence spine byte-identical (download_queue.py 0 diff lines since eed1f75, and since 190d1c4 before that); the app.py delta provably avoids the queue spine.** Targeted grep of the full app.py delta for every queue-spine symbol (`kick_download_queue`, `run_download_queue`, `boot_resume_queue`, `QueueEventMessage`, `apply_queue_event`, `download_queue`, `DownloadQueueService`) returns **zero matching delta lines**. Spine re-read at HEAD (line numbers shifted by the +134 delta): `QueueEventMessage` :398, the shared `DownloadQueueService()` :630, `kick_download_queue` :793, the exclusive `@work(exclusive=True, thread=True)` driver :816-817, `boot_resume_queue` :914; `tui/__main__.py:100` still `app.call_later(app.boot_resume_queue)` before `run`. Worker-isolation check: the WR-02 `_exit_kill_worker` declares `group="exit-kill"` (:1231) while `run_download_queue` uses its default method-name group — Textual exclusivity is per-group, so the new exit worker can never cancel the download driver. Behavioral: `test_boot_resume_rehydrates_and_kicks_once` + `test_boot_resume_without_pending_never_kicks` green by name this pass. |
| 3 | SC3 every landed download reconciles rows vs n_audit; mismatches prominent, never silently accepted | ✓ VERIFIED | Reconcile kernel byte-identical (download_queue.py 0 diff lines): candidate-only temp registry with absolute `Dataset_path` against the rerouted base, all four output flags at temp paths, empty-overlay env; `merge_presence` overlays done keys only; mismatch state carries declared/measured and never auto-deletes; `reaudit_baseline` stays explicit-only. Presentation byte-identical (data_manager.py 0 diff lines): `_render_banners` mounts one QUEUE_BANNER_MISMATCH block per number-carrying mismatch, `_sorted_entries` sorts mismatch+failed to the top. Behavioral: `test_mismatch_banner_block_and_sort_to_top` green by name this pass. |
| 4 | SC4 Zenodo bulk bundle (record 19135551, once public) reachable as alternate whole-package entry | ✓ VERIFIED | zenodo_bundle.py and data_manager.py both byte-identical since the prior verified pass (0 diff lines each): `ZENODO_RECORD_ID = "19135551"` and the frozen API URL intact, four-state `_render_zenodo_line`, `action_zenodo_bundle` enqueues only when public, the never-silent `DL_ZENODO_DISABLED_TOAST` on every other z press, and the hhx WR-02 persist-rollback (failed `_persist_locked()` pops the appended entry — no ghost row) untouched. Behavioral: `test_enqueue_zenodo_persist_failure_refused_no_ghost_row` and `test_z_enqueues_only_when_public_never_silent_otherwise` green by name this pass. |
| 5 | SC5 subprocess/thread-worker discipline (console never freezes); zero credentials stored or echoed | ✓ VERIFIED | Popen discipline byte-identical (download_queue.py 0 diff lines): LIST argv + `start_new_session=True` + PIPEs + `env=dict(os.environ)` on both lanes. `test_service_module_never_imports_modelscope` green by name this pass. The app.py exit-channel delta STRENGTHENS this SC rather than touching it: WR-02 moves the [k] kill fan-out off the event loop onto an exclusive `exit-kill` thread worker (per-root broad guard, unconditional `ExitKillsDone` completion, exit lands on the message — never a frozen loop); WR-01's ctrl+c Input-copy delegation and WR-03's multi-root exit modal are exit-channel UX with zero queue interaction. Credential surface unchanged: the 12-field credential-free `_ENTRY_FIELDS` set and zero env overrides in the byte-identical engine. |

**Score:** 5/5 truths verified (0 present-but-behavior-unverified).

### The delta's interaction with the SC chains (checked, disjoint or strengthening)

1. **selection.py IN-01 fix vs SC1/SC5** — the delta is one hunk inside `apply_queue_progress`: the two live-dict stores (`_live_percents`/`_live_speeds`) moved BELOW the `(model, downloading)` guard (:1614-1618), mirroring the fixed slot-3 twin. Guard behavior for passing ticks is unchanged (store + in-place cell update in the same order); the only behavioral change is that dataset-key and non-downloading ticks no longer accumulate dict residue. The presence overlay, `apply_queue_event`, and the `d` action are untouched. Regression-pinned by the new `test_dataset_kind_tick_stores_no_live_dict_residue` (green by name).
2. **app.py WR-01/02/03 exit-channel trio vs SC2/SC5** — hunk-by-hunk audited: ExitModal [k] now delegates to `request_kill_and_exit` → `_exit_kill_worker` (group="exit-kill", exclusive, thread, `exit_on_error=False`, per-root broad guard, unconditional `ExitKillsDone` post; exit in `on_exit_kills_done`); WR-01 ctrl+c copy delegation only for a selection-holding non-modal `Input` focus; WR-03 multi-root modal includes an attached running root not among launcher roots. Zero queue-spine symbols in the delta; the new worker's group differs from the download driver's default group, so exclusivity cannot interact. SC5's never-freeze discipline is strengthened (the [k] kill no longer blocks the loop).
3. **test_pilot_selection_custom.py +35** — purely additive: the IN-01 residue regression test; lane 28/28 green (27 prior + 1 new).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tui/services/download_queue.py` | The phase engine: rerouted `_datasets_base`, six landing legs, reconcile kernel, Popen discipline, zenodo branch, credential-free schema | ✓ VERIFIED | Byte-identical since eed1f75 (0 diff lines; last content change 190d1c4); reroute, legs, kernel, and schema intact |
| `tui/services/zenodo_bundle.py` | Four-state probe + guarded bundle driver (record 19135551) | ✓ VERIFIED | Byte-identical (0 diff lines); constants intact |
| `tui/screens/data_manager.py` | Slot-3 data-manager screen: two-pane layout, five-state glyphs, banners, drill-down, Zenodo line, d/r/x/a/enter/g/z | ✓ VERIFIED | Byte-identical (0 diff lines); all surfaces present |
| `tui/app.py` | Shared queue service, exclusive driver worker, kick guard, boot resume, QueueEventMessage forward | ✓ VERIFIED | Delta-audited: the +134 exit-channel lines avoid the queue spine entirely (zero delta hunks match any queue-spine symbol); spine re-read at :398/:630/:793/:816/:914; boot-resume pair green by name |
| `tui/__main__.py` | D-06 boot path | ✓ VERIFIED | `app.call_later(app.boot_resume_queue)` at :100, before `run` (byte-identical) |
| `tui/screens/nav.py` | Slot 3 = real data_manager target | ✓ VERIFIED | Byte-identical (0 diff lines) |
| `tui/screens/selection.py` | Presence overlay + apply_queue_event + shared-service d | ✓ VERIFIED | Delta confined to the apply_queue_progress IN-01 store reordering (+docstring); overlay, done-refresh, and d lane untouched; delta lane 28/28 |
| `tui/strings.py` | The DL_/QUEUE_ operator-copy single home (+ENV_ROUTE amendment) | ✓ VERIFIED | Byte-identical (0 diff lines); ENV_ROUTE `[3]` keycap hint intact |
| `tests/tui/test_services_download_queue.py` | Three `_cr01` agreement tests + transition table + reconcile + persist-rollback + census lanes | ✓ VERIFIED | Census pins hold (R-02 dataset 46/4, model channel 38/21); five named tests green this pass; module byte-identical since eed1f75 |
| `tests/tui/test_services_zenodo_bundle.py` | Probe/bundle/never-silent lanes | ✓ VERIFIED | Byte-identical since eed1f75 |
| `tests/tui/test_pilot_data_manager.py` | Screen-tier Pilot proofs incl. mismatch banner, z-never-silent, boot resume, slot-3 geometry | ✓ VERIFIED | Byte-identical since eed1f75; four named tests green this pass |
| `tests/tui/test_pilot_selection_custom.py` | Selection d binding + overlay + toasts + the new IN-01 residue regression | ✓ VERIFIED | Delta-touched lane run in full this pass: 28 passed in 8.74s |
| Golden snapshots (data_manager.svg, data_manager_presence.svg, …) | Goldens match current render | ✓ VERIFIED | Caller-provided box evidence on this exact HEAD: data_manager goldens green (full-suite lane); no covered screen's render surface changed (data_manager/strings/styles byte-identical; selection.py delta is progress-internals with the same passing-tick composition) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `DownloadQueueService._datasets_base()` | `run_config.resolve_dirs(run_config.load_state()).dataset_root_abs` | the same chain the env-check `dataset_dirs` kernel and `compose_argv`'s `--dataset_root` consume | ✓ WIRED | Both endpoints byte-identical this delta; three `_cr01` agreement tests green by name this pass |
| `tui/app` shared service | driver worker → `QueueEventMessage` → `DataManagerScreen.apply_queue_event` / `SelectionScreen.apply_queue_event` + toasts | the 10-04/10-05 spine | ✓ WIRED | Spine re-read at :398/:630/:793/:816/:914; app.py delta contains zero queue-spine hunks; boot-resume pair green by name |
| `tui/__main__` | `app.boot_resume_queue` | `call_later` before `run` (:100) | ✓ WIRED | Byte-identical; boot-resume pair green by name |
| `SelectionBackend` | `download_queue.reconciled_rows` + `merge_presence` → `registries.presence_for` | the D-11 overlay (pure read, no service instance) | ✓ WIRED | selection.py delta confined to apply_queue_progress internals; flip `_cr01` tests green by name |
| `tui/screens/nav` NAV_SLOTS slot 3 | `data_manager` target | `action_nav` routing | ✓ WIRED | nav.py byte-identical |
| `tui/screens/data_manager` | `download_queue` + `zenodo_bundle` (Protocol seam) → `S.` strings | service results only, screen computes nothing | ✓ WIRED | Both sides byte-identical; named z/persist tests green |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `_datasets_base()` | `dirs.dataset_root_abs` | `run_config.load_state()` → `resolve_dirs` (REPO_ROOT-anchored) | ✓ | FLOWING — engine byte-identical; `_cr01` agreement tests green by name |
| `_render_missing` / `MissingSnapshot` | `snapshot.missing` / `rows` | `registries.load_n_audit` + disk scan through the Backend | ✓ | FLOWING — overlay + presence-rows `_cr01` tests green by name |
| `_progress_cell` + `apply_queue_progress` | percent / speed | real stderr pump → `parse_progress`/`parse_speed` (last-token, verbatim) | ✓ | FLOWING — the IN-01 fix changes only WHERE passing-tick stores sit (below the guard); the in-place cell update and the passing-tick store order are unchanged; delta lane + named residue test green |
| `_reconcile_cell` | declared/measured | the audit subprocess's temp n_audit.json verdict | ✓ | FLOWING — kernel byte-identical; mismatch banner test green by name |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|--------|---------|--------|--------|
| Delta-touched selection-custom pilot lane (incl. the new IN-01 residue regression) | `.venv/bin/python -m pytest tests/tui/test_pilot_selection_custom.py -q` | 28 passed in 8.74s | ✓ PASS |
| Named SC batch: three `_cr01` agreement + R-02 dataset census + model census 38/21 + zenodo persist rollback + never-imports-modelscope + boot-resume pair + z-never-silent + mismatch banner + backend-flip `_cr01` + IN-01 residue | `.venv/bin/python -m pytest <13 test IDs>` | 13 passed in 1.25s | ✓ PASS |
| Covered-set byte-diff vs prior verified HEAD | `git diff eed1f75..HEAD --numstat -- <24 covered files>` | exactly 3 files changed (app.py 134, selection.py 13, test_pilot_selection_custom.py 35); all cores 0 | ✓ PASS |
| app.py delta queue-spine audit | grep of the full delta for kick/run/boot_resume/QueueEventMessage/apply_queue_event/download_queue/DownloadQueueService | zero matching delta lines | ✓ PASS |
| Worker-group isolation (new exit-kill worker vs download driver) | grep `group=` + driver decl in tui/app.py | exit-kill :1231 vs driver default group :816 — no interaction | ✓ PASS |
| ruff (scoped to the three delta files) | `.venv/bin/python -m ruff check tui/app.py tui/screens/selection.py tests/tui/test_pilot_selection_custom.py` | All checks passed | ✓ PASS |
| ty (scoped to the three delta files) | `.venv/bin/python -m ty check …` | All checks passed | ✓ PASS |
| Debt markers (TBD/FIXME/XXX/TODO/HACK) over the three delta files | grep -n -E | 0 hits (remaining "placeholder" tokens are Textual Input attributes + the NAV_PLACEHOLDER_TOAST machinery, by design) | ✓ PASS |

Full-suite note (caller-provided box evidence on this exact HEAD 6bb768f, not re-run here per instruction): full suite 1F/1867P (sole machine-local member), node 26/26, ruff+ty green, data_manager goldens green. This verifier's own executions this pass (42 total) are fully green at HEAD.

### Probe Execution

No probe scripts are declared for this phase (plans' verify blocks are pytest/make lanes) — N/A.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DATA-01 | 10-01, 10-04, 10-05, 10-07 | One-click ModelScope download, registry `download_url` sole authority; presence flips in selection table AND env check | ✓ SATISFIED | SC1 row: chain endpoints byte-identical, selection delta disjoint from the overlay; three `_cr01` agreement + census + flip tests green by name this pass |
| DATA-02 | 10-01, 10-04, 10-06 | Persistent queue + resume across crash/restart | ✓ SATISFIED | SC2 row: engine byte-identical; app.py delta audit shows zero queue-spine hunks and worker-group isolation; boot-resume pair green by name |
| DATA-03 | 10-02, 10-06 | Row-count reconciliation vs n_audit; mismatches prominent, never silent | ✓ SATISFIED | SC3 row: kernel + presentation byte-identical; mismatch banner test green by name |
| DATA-04 | 10-03, 10-06 | Zenodo whole-package alternate entry (record 19135551) | ✓ SATISFIED | SC4 row: service + screen byte-identical; persist rollback + z-never-silent green by name |

No orphaned requirements (REQUIREMENTS.md maps exactly DATA-01..04 to Phase 10; all four marked Complete; every ID claimed in at least one plan's `requirements` frontmatter — 10-01 through 10-07 collectively claim all four).

### Decision Coverage

`check.decision-coverage-verify --phase 10` at this pass: resolver SKIPPED non-blockingly ("CONTEXT.md missing" — the verb does not resolve `10-CONTEXT.md` under this invocation form; the same resolver limitation the round-2 predecessor hit before it was worked around). Non-blocking gate; no drift signal — every covered decision's artifact is byte-identical or delta-audited above.

### Anti-Patterns Found

None. Debt-marker greps over the three delta files return zero hits. No stub patterns, no empty implementations. The `MODEL_DOWNLOAD_PROGRAM` subprocess child string remains the only textual modelscope mention in the engine (argv data by design, AST-verified in prior passes; engine byte-identical).

### Advisory (Out-of-SC, carried forward)

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | WR-01 failed KIND_MODEL download → models 下载 column 已下载 (is_dir presence vs config.json done gate, tui/services/selection.py:544) | other | Carried; services/selection.py byte-identical this delta; model presence column is dcl/mlc scope, no phase-10 SC covers it; disposition-open in 10-REVIEW-DISPOSITION.md |
| 2 | IN-01 z probe-in-flight window asserts the disabled toast as fact (data_manager.py:1300) | other | Carried; data_manager.py byte-identical this delta (0 diff lines); transient copy issue, never-silent behavior unaffected; disposition-open |
| 3 | IN-02 ABOUT_MILESTONE_STAGE names phase 9 (strings.py:1021-1025) | other | Carried; strings.py byte-identical this delta (0 diff lines); cosmetic milestone metadata; disposition-open |

### Advisory Resolved This Round (adjudication)

| Finding | Adjudication | Evidence |
|----------|--------------|----------|
| **08-REVIEW IN-01** — slot-2 `apply_queue_progress` stored live percent/speed BEFORE the kind/state guard (tui/screens/selection.py:1593 region), the hygiene twin of the fixed slot-3 item (data_manager.py, quick-261016-hhx) | **RESOLVED by quick-261017-klw (commit 0d02e18)** — the stores moved below the `(model, downloading)` guard, the exact ordering of the fixed slot-3 twin; only passing (model, downloading) ticks store, so dataset keys cannot accumulate in either slot-2 live dict for the session. Dropped from the carried list | Diff hunk `@@ -1603,12 +1603,19 @@` re-read at HEAD (:1614-1618); the same-commit regression `test_dataset_kind_tick_stores_no_live_dict_residue` asserts both dict non-residues and is green (by name in the 13-pass batch; the full delta lane 28/28). Passing-tick behavior is order-preserved (guard → store → in-place cell update in the same sequence as before for entries that pass) |

### Human Verification Required

None. Both prior live items remain discharged (10-UAT.md, 2026-10-13: the GB10 live smoke incl. the presence flip, and the `g` four-artifact check). This refresh's delta (klw fix batch) was itself code-reviewed (08-REVIEW base 601aa51, disposition recorded) and adds no phase-10 SC surface: the IN-01 fix is inside progress-internals with a passing regression test; the exit-channel trio avoids the queue spine entirely (delta-audited, worker-group isolation checked). All five SC behaviors are re-proven mechanically this pass (42 green executions incl. the agreement, census, flip, banner, boot-resume, z-never-silent, persist-rollback, and residue tests).

### Gaps Summary

None. The staleness trigger is cleared and the delta is disjoint from or strengthening to every SC chain: the engine (`download_queue.py`), the zenodo service, the data-manager screen, strings, nav, and every service module are byte-identical to the prior verified pass (numstat-verified 0 diff lines); the selection.py delta is the IN-01 hygiene fix inside `apply_queue_progress` (guard-then-store, the slot-3 twin's ordering) with its regression test green; the app.py exit-channel delta (+134 lines) provably avoids the queue spine and isolates its new worker under a distinct exclusivity group; the delta-touched test lane and a 13-test named SC batch are fully green. The 08-REVIEW IN-01 carried advisory is RESOLVED and removed from the advisory list. SC1-SC5 all hold at HEAD 6bb768f with zero regressions.

### Fingerprint Refresh

`covered_files`/`covered_digest` in the frontmatter are the verbatim `verification.fingerprint` output at HEAD 6bb768f (supersedes `v3:sha256:bba6fc3e…` of the prior pass; identical file scope, new digest reflecting the klw delta on app.py, selection.py, and test_pilot_selection_custom.py).

---

_Verified: 2026-10-17T07:49:18Z (HEAD 6bb768f)_
_Verifier: Claude (gsd-verifier, micro refresh round 6, post-klw)_
