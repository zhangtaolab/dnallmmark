---
phase: 10-data-manager-downloads-verification
verified: 2026-10-13T05:52:00Z
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
  - tui/services/gauntlet.py
  - tui/services/zenodo_bundle.py
  - tui/strings.py
  - tui/styles.tcss
covered_digest: "v3:sha256:740c080dbe6aaa69784fa66927323782796e8f914a215607a1ecfc7ee8c7e9df"
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "GB10 live smoke (10-06-SUMMARY procedure steps 1-7): on the GB10 host, `make tui` -> 3 -> cursor GUE__emp_H3 -> d; observe the queue row run, land, reconcile; press 2 and confirm the selection presence cell flips to present; rerun env check (r) and confirm the dataset-dir item flips"
    expected: "Enqueued toast -> pending -> downloading with live percents -> done + QUEUE_FLIP_TOAST; the key leaves the data-manager missing list (在场 44/50); selection cell flips in-place; env dataset_dirs check no longer lists the key"
    result: "pass (2026-10-13 live, orchestrator per maintainer delegation; key GUE__virus_species_40 — emp_H3 already present on disk; evidence 10-UAT.md item 1: toast/pending/downloading-percents/done + 在场 43→44, selection cell ✓ 4,000/500/500, env re-run green)"
    why_human: "Requires the real modelscope CLI + SDK token + a real multi-GB network download on the GB10 host — CI is network-free by binding constraint; every seam below the CLI is machine-proven (fake spawner lanes, real audit subprocess, real landing checks, Pilot e2e through the real app forward) and the CLI's own behavior (progress format, .msc skip, SIGTERM/143, Range resume) was live-probed at research time against modelscope 1.34.0"
  - test: "The `g` re-audit four-artifact live check (10-06 procedure step 5): press g on a mismatch row (or run `python script/audit_n_frequencies.py` from repo root), then `git status`"
    expected: "EXACTLY four modified artifacts: dnallm-mark/data/n_audit.json, dnallm-mark/data/n_audit.csv, pipeline/eval_subsets.json, DATA.md — nothing else; maintainer reviews the diff and commits it as the new baseline (R-03)"
    result: "pass (2026-10-13 live, service-tier real run — same argv the g binding drives, 23.9s; git status EXACTLY the four artifacts; maintainer committed the refresh as the new baseline 2f7211d per R-03 ruling; evidence 10-UAT.md item 2)"
    why_human: "No CI test may execute a default-outputs audit (it would rewrite the four committed artifacts by design); the argv/no-flags/env contract is machine-pinned (test_reaudit_argv_exactly_interpreter_and_script_no_flags), the real invocation is deliberately maintainer-only"
---

# Phase 10: Data Manager (Downloads & Verification) Verification Report

**Phase Goal:** Dataset gaps are closable in-session before launch — one-click ModelScope download driven by the registry's authoritative `download_url`, a persistent resumable queue, and row-count reconciliation against n_audit — so an env-check presence FAIL is always diagnosable and fixable from the console
**Verified:** 2026-10-13T05:20:00Z at HEAD bfe65e1 (code identical to review HEAD ed34b87; the diff is this .planning doc only — `git diff ed34b87..HEAD --name-only` → `10-REVIEW.md`)
**Status:** human_needed — all 5 SCs VERIFIED in the codebase; the GB10 live smoke (the phase's own documented maintainer confirmation, never CI by design) is the outstanding human step
**Re-verification:** No — initial verification (no prior VERIFICATION.md)

**Method:** goal-backward. Every SC traced through the real code (service → app driver → screens → registry/audit kernels), 21 named SC-evidence tests confirmed to exist with bodies read and asserting what 10-06's checklist claims, full tui lane re-run, live TUI boot in tmux, and all review-fix regression lanes (CR-01/CR-02/WR-01..06) re-confirmed against the fix commits.

**Gate evidence:** `uv run --group dev --group tui pytest tests/tui -q` → **627 passed in 167.26s** (run by this verifier at HEAD; matches review iteration-3's 627 at ed34b87). The orchestrator's full `make test` gate runs in parallel.

---

## Goal Achievement — Per-Success-Criterion Verdicts

### SC1 — One-click download via the registry `download_url`; presence flips on landing (selection + env check): **VERIFIED**

The real chain, traced end-to-end in code:

1. **Registry URL is the only authority.** `resolve_channel`/`_spec_from_entry` (`tui/services/download_queue.py:2359-2412`): `download_url` first, modelscope mirror from `download_url_alternates` only when the primary host is not modelscope.cn (R-01); repo id validated against `^[\w.-]+/[\w.-]+$` before anything reaches argv; the R-02 46/4 shape table is code-owned at module top (`SHAPE_A_REPOS` etc., :181+). Pinned computed over the committed registry by `test_r02_census_46_downloadable_4_disabled_over_committed_registry` (verified present, asserts the census).
2. **The operator action.** Selection `d` binding at `tui/screens/selection.py:1203` (`Binding("d", "enqueue_dataset", SEL_ENQUEUE_LABEL)`), `action_enqueue_dataset` (:1675) → present-row toast gate (:1698) → shared-queue enqueue → `app.kick_download_queue()` (:1703), never navigates; the data-manager `d` at `tui/screens/data_manager.py:529/1001`. Both screens use the SAME service instance (`app.build_selection_screen` passes `SelectionQueueBackend(self._download_queue)` — selection.py:1260).
3. **The driver.** `kick_download_queue` (`tui/app.py:394`, busy check-and-set under `_queue_busy_lock`) → `run_download_queue` worker (:417, `@work(exclusive=True, thread=True)`) → `claim_next` → claim tick → `run_task` → `QueueEventMessage` post (:502).
4. **The engine.** `run_task` (`tui/services/download_queue.py:1470-1606`): CLI re-probe → channel resolve → `compose_download_argv` (LIST argv, absolute `--local_dir`) → spawn via the injectable seam with `start_new_session=True`, PIPEs, `env=dict(os.environ)` (:1522-1524) → daemon stderr pump with integer-percent progress (:1538-1559) → cancel-aware reap (:1608-1626) → **landing gate** (shape-C rename with never-overwrite, then all three split CSVs under `pipeline/datasets/<Group>/<task>`, :1628-1659) → **reconcile gate** (:1589: done = landed AND reconcile pass; mismatch → mismatch state with declared/measured; nothing deleted).
5. **The flip — both surfaces, REAL path (CR-01 fixed and regression-pinned).**
   - Data-manager missing pane: `missing_datasets()` (:2288-2335) computes over `merge_presence(registries.load_n_audit(), reconciled_rows(self._state_path))` — the merged view on the REAL service; `merged_audit_tasks()` (:2337) serves the same view; `DataManagerBackend.missing_snapshot` computes present/total over it. Regression `test_missing_datasets_flips_over_done_reconciled_entries_cr01` (tests/tui/test_services_download_queue.py:618, body read: seeded REAL service + tmp committed n_audit — done+reconciled key leaves the list, mismatched sibling stays) + `test_backend_missing_snapshot_flips_over_real_seeded_state_cr01` (REAL Backend over REAL service).
   - Selection table: `SelectionBackend.load_selection_data` (selection.py:413-433) builds presence over `merge_presence(load_n_audit(), reconciled_rows())`; the live flip via `apply_queue_event` (:1345) re-running the snapshot worker through the WR-03-fixed app forward (`app.py:548` iterates `screen_stack` — reaches the screen under open modals). Pinned: `test_overlay_flips_missing_presence_to_present_and_back`, `test_mismatch_and_failed_entries_never_flip_presence`, `test_live_flip_through_the_app_event_forward` (all present; the live-flip test drives a done `QueueEvent` through the real `app.on_queue_event_message`).
   - Env check: the `dataset_dirs` kernel is a real disk scan (`pipeline/env_smoke.py:390-420`, `expected.is_dir()` over every registry `Dataset_path`) — a landed download physically creates those dirs, so the env check flips on the next recheck (`r`); the FAIL route line carries the `[3] 前往数据管理` keycap (`tui/strings.py:103-106`) and digit 3 mounts the screen (Pilot-proven: `test_env_route_hint_renders_and_digit3_is_the_one_path`).
6. **Live confirmation (this verifier, tmux):** `make tui` booted; slot 3 mounts the data-manager screen rendering the 7 real missing GUE keys with baseline row counts, `在场 43/50 · 缺失 7`, and the empty-queue state — matching the committed n_audit truth.

### SC2 — Persistent resumable queue across TUI exit/crash: **VERIFIED**

- **Persistence:** `download_queue.json` under the XDG state root through `settings.atomic_write` (`_persist_locked`, :1174); the exact 12-field entry set (`_ENTRY_FIELDS`, :162-166); every transition persists.
- **Restart downgrade:** `_load_locked` (:1056-1117) — every persisted `downloading` entry → `pending` + `interrupted=True`, the downgrade itself persisted; the active-key guard (:1091-1097) prevents a mid-flight reload from re-queueing the live entry; IN-11 fixed — the downgrade runs BEFORE the dropped-rows early return (:1083-1100, regression RED-verified on 4079860 per review iteration 3). Corrupt file → quarantined `.corrupt` sidecar + diagnostic, remembered via `last_load_diagnostic` (:1132).
- **Boot:** `boot_resume_queue` scheduled ONLY by `tui/__main__.py` `main()` via `call_later` (file read — the only auto-start path; `App.on_mount` never kicks). Pinned: `test_boot_is_inert_driver_never_autostarts_never_hangs`, `test_boot_resume_rehydrates_and_kicks_once`, `test_boot_resume_without_pending_never_kicks`, `test_second_boot_resume_while_busy_starts_no_second_worker`.
- **The full chain:** `test_restart_resume_end_to_end_service_tier` (tests/tui/test_services_download_queue.py:3714, body read: persist mid-download → `load()` downgrade (pending + interrupted, asserted) → `claim_next` → re-invoke (exit 0 + success marker over the already-complete tree — the `.msc` skip) → landing check on the existing tree → reconcile pass → done). The channel's own resume (.msc skip + Range partials + SIGTERM/143 behavior) was live-probed against modelscope 1.34.0 at research time (10-RESEARCH §live-probe, verbatim captures).
- **No illegal transition silently coerces:** `test_state_machine_transition_table_exhaustive` (20 parametrized rows, 5 states × 4 mutators) + `test_run_task_terminal_transitions_from_downloading`.

### SC3 — Row-count reconciliation against n_audit; mismatches prominent, never silently accepted: **VERIFIED**

- **The kernel is the real audit subprocess.** `reconcile_dataset` (:1939-2040): candidate-only temp registry (exactly `{key: entry}`), `Dataset_path` ABSOLUTIZED so the inert temp datasets-root can never redirect, **all four output flags at temp paths** (the committed artifacts unreachable), env = `os.environ` + exactly one `CUSTOM_DIR_ENV`→empty-temp override; verdict from the PARSED temp `n_audit.json` record with the gauntlet `_audit_verdict` semantics (:2042-2102: missing false, rows>0 per split, unified_eval_n>0, every declared Train/Dev/Test == measured). Real-subprocess evidence: `test_reconcile_real_subprocess_pass_over_fixture_csvs` and `test_reconcile_real_subprocess_mismatch_names_numbers_no_deletion` (body read: declared 999 vs measured 4 → mismatch naming `Train_mismatch_declared=999_measured=4`, measured map complete, and **all three CSVs still on disk** — D-07 no-deletion asserted).
- **done gated on pass; mismatch a first-class state.** `run_task` :1588-1606; `test_run_task_done_populates_entry_reconcile`, `test_run_task_reconcile_mismatch_lands_mismatch_state`.
- **Committed baseline read-only to every automatic path.** `test_committed_artifacts_byte_unchanged_across_real_reconcile_run` (sha256 before/after a full run_task with the REAL reconcile) + `test_no_automatic_path_ever_constructs_a_no_flag_audit_argv`; independently confirmed by the byte-identical diff below (the four artifacts unchanged across the whole phase).
- **`g` re-audit = R-03 default outputs.** `reaudit_baseline` (:2162-2207): argv EXACTLY `[sys.executable, <absolute script path>]`, NO output flags — the script's defaults write the four worktree artifacts for maintainer review/commit. Pinned by `test_reaudit_argv_exactly_interpreter_and_script_no_flags` (body read). The real invocation is the documented maintainer check (human-verification item below) — no CI test may run it.
- **Prominence.** Mismatch banner under the queue title (`queue-banner-mismatch`, data_manager.py:850; copy `⚠ 对账不一致 — {key}: n_audit 基线 {n} 行, 实测 {m} 行（不自动删除）`, strings.py:594), mismatch+failed sort-to-top, the `⚠ {n}≠{m}` reconcile cell (strings.py:586): pinned by `test_mismatch_banner_block_and_sort_to_top`, `test_reconcile_cells_four_vocabularies`. Mismatch never flips presence (semantic 6): `test_mismatch_and_failed_entries_never_flip_presence`.

### SC4 — Zenodo 19135551 alternate whole-package entry: **VERIFIED** (not-public is the live truth; activation = the probe answer flipping, zero code change)

- **Four-state probe.** `probe_zenodo_public` (`tui/services/zenodo_bundle.py:74-104`): ONE stdlib GET against the frozen `ZENODO_API_URL` (:53), 200→public, 404→not_public, everything else→failed; HEAD never used (CDN hangs); no URL/shape parameter exists. Pinned: `test_probe_404_maps_not_public_the_live_today_state`, `test_probe_200_maps_public_and_passes_the_seam_kwargs`, `test_probe_accepts_no_url_or_shape_parameter`.
- **Disabled + explanation while 404 — live-confirmed by this verifier:** the live tmux session rendered `[z] Zenodo 整包 · 未公开（探测于 04:28）` (the real frozen-URL GET answered 404→not_public from this machine), and pressing `z` fired the never-silent toast `Zenodo 记录 19135551 尚未公开 — 公开后此入口自动激活`. Screen states pinned: `test_zenodo_line_four_states`, `test_z_enqueues_only_when_public_never_silent_otherwise`.
- **The offline bundle lane proven end-to-end.** `test_run_task_zenodo_bundle_offline_end_to_end_done` (body read: enqueue_zenodo → claim → run through the REAL zip extraction and the REAL reconcile subprocess over a tmp repo → done with `{"per_key": {"Demo__task": "pass"}}`, CSVs on disk, staging under the state root, `[reconcile]` in the log). Zip-slip, mismatch-no-deletion, not-public refusal, and empty-missing-set (nothing_to_do, IN-08 fix) all have dedicated lanes.
- **Cancel honors the lane (WR-01 fixed):** stage-boundary polls + `should_cancel` seam in `download_bundle_files` + `_finish_cancelled`; regressions `test_run_task_zenodo_cancel_before_stages_fails_never_probes`, `test_run_task_zenodo_cancel_mid_download_fails_cancelled` (confirmed present, added in 1d87cc8).

### SC5 — Subprocess/thread-worker discipline; zero credentials; console never freezes: **VERIFIED**

- **Never in-process.** Zero modelscope imports anywhere in `tui/` (`grep -rn "import modelscope\|from modelscope" tui/` → no matches); the CLI is an external probed subprocess (D-01). Zenodo lane is stdlib urllib only.
- **Subprocess discipline.** LIST argv everywhere, `start_new_session=True` + owned `Popen` + killpg SIGTERM→SIGKILL cancel: `test_spawn_pins_list_argv_env_passthrough_pipes_session`, `test_cancel_mid_run_terminates_process_group_real_subprocess` (real subprocess, group death proven). Env is exactly `dict(os.environ)` — the TUI never touches `~/.modelscope` (credentials remain the CLI's business).
- **Zero credential surface.** `_ENTRY_FIELDS` (:162) is the exact persisted set — nothing else survives `_normalized_entry`; `test_persisted_entries_carry_no_credential_fields` asserts set-equality against the canonical fields AND a forbidden-token intersection.
- **The console never freezes.** All I/O in workers: the driver (`@work(exclusive=True, thread=True)`), per-worker groups (`dl-snapshot`/`dl-probe`/`dl-reaudit`), the snapshot in an exclusive worker. Pinned: `test_blocked_task_never_freezes_the_console` (r-press toasts while a fake run_task blocks), `test_boot_is_inert_driver_never_autostarts_never_hangs`, `test_kick_on_empty_queue_exits_and_wait_for_complete_returns`, `test_worker_exits_on_drain_and_restarts_on_next_kick`.
- **Degradation is honest.** CLI absent → `cli_unavailable` refused enqueue (no file rewrite), corrupt state → quarantined + status line, unknown registry keys tolerated end-to-end (10-06 lanes confirmed present).

**Score: 5/5 truths verified (0 present-but-behavior-unverified).**

---

## Review-Fix Verification (10-REVIEW.md iterations 1-3, final verdict CLEAN)

Spot-verified at HEAD, not taken from the docs:

| Finding | Evidence verified |
|---|---|
| CR-01 (missing-pane flip was fake drift) | Fix real at `download_queue.py:2288-2335` (merged view on the REAL service); regression lanes from commit 356b324 present and real-service (bodies read) |
| CR-02 (driver livelock) | Fix real at `app.py:447-489` (refusal read via `last_claim_refusal` seam → bounded exit + `QueueStalledMessage`); `test_driver_exits_bounded_when_claim_cannot_persist_cr02` (pilot_data_manager.py:1593, REAL service + read-only root) |
| WR-02/WR-03/WR-04/WR-05/WR-06 | Fix code read: busy lock + drain release-and-recheck (app.py:410-485), `screen_stack` forward (:548,559), `_persist_locked` returns diagnostic (:1174+) with `persist_error=` problem on `_finish` (:2249-2252), `errors="replace"` in `_invoke` (:2148-2150) + the gauntlet twin (`tui/services/gauntlet.py` — confirmed in phase manifest, commit 46ddd37), `ACTION_UNKNOWN` + `DL_UNKNOWN_TOAST` (strings.py:558, selection.py toast mapping) |
| Kept open | IN-02 (dead pure function, maintainer choice), IN-03 progress half (indeterminate glyph renders regardless), IN-06 + IN-10 (**pre-activation gate** — see Risks) |

---

## UI-SPEC Contract Check (shipped screen vs binding items)

Live tmux capture at 100×30 + code/constants, all matching the approved contract:

- **Glyph set/colors:** five states verbatim — `◌ 待下载` / `⠋ 下载中` / `✓ 完成` / `✗ 失败` / `⚠ 对账不一致` (strings.py:576-580); reconcile cells `✓ {n} 行一致` / `⠋ 对账中 …` / `⚠ {n}≠{m}` (:584-586); `█` filled progress cells in accent (data_manager.py:908, UI-SPEC item 11); glyph+color dual channel preserved.
- **Bottom bar:** `[d]入队 [r]重试 [x]取消 [a]全部入队 [enter]详情 … [?]帮助 [q]退出` — live-rendered; `g`/`z` show=False (data_manager.py:534-535).
- **Progress cells:** right-aligned percent + 10-cell bar; indeterminate `⠋ …` (Pilot: live 40% bar + `[None,10,25,40,100]` throttle stream).
- **Banners:** mismatch banner under the queue title, per-mismatch rows, sort-to-top.
- **Drill-down:** `enter` → QueueDetailModal RichLog — full key, registry download_url, LIST argv, reconcile numbers, verbatim log incl. `[reconcile]` section; esc returns.
- **z/g:** z public-only enqueue / never-silent toast (live-confirmed); g mismatch-rows-only re-audit in a worker.
- **Nav:** slot 3 `3数据管理` active vocabulary, slots 4/5 still 未开放 (live-confirmed); ENV_ROUTE `[3] 前往数据管理` amendment (strings.py:103-106).
- **Documented deviations (both accepted in-plan):** progress column 17 cells vs spec's 14 (textual width-includes-padding, probe-pinned); bundle-row reconcile cell renders the dash with per_key in the drill-down (no number pair exists for the whole-package lane).

---

## Constraint Checklist (phase-level)

| Constraint | Check | Result |
|---|---|---|
| `pipeline/`, `uv.lock`, `pyproject.toml` byte-identical vs 71b05c4 | `git diff 71b05c4..HEAD --name-only -- pipeline/ uv.lock pyproject.toml` | **EMPTY** |
| Official registries untouched | `git diff 71b05c4..HEAD --name-only -- pipeline/models_info.json pipeline/datasets_info.json` | **EMPTY** |
| Four committed audit artifacts untouched | `--name-only -- dnallm-mark/data/n_audit.json n_audit.csv pipeline/eval_subsets.json DATA.md` | **EMPTY** |
| dnallm-mark/, script/, scripts/ untouched | `--name-only -- dnallm-mark/ script/ scripts/` | **EMPTY** |
| Whole-phase manifest | only `tui/**` (9 files), `tests/tui/**` (8 incl. 2 fixtures), `.planning/**` — nothing else | **PASS** |
| Services zero-textual (AST lock covers new services) | `tests/tui/test_import_lock.py` AST-walks every `tui/services/*.py` via glob — download_queue.py + zenodo_bundle.py auto-covered; 627 green | **PASS** |
| Strings single-home | 48 `DL_`/`QUEUE_` constants in `tui/strings.py`; zero CJK literals in the new/edited tui modules (`grep -rn [一-鿿]` → none outside strings.py; per-module CJK lock tests present); bidirectional inventory tripwire (test at test_services_download_queue.py:3193) | **PASS** |
| CI lanes network-free | All zenodo/modelscope touches in tests are injected openers/spawners or fixture strings; no test reaches zenodo.org or modelscope.cn (`tests/tui` 627 pass offline) | **PASS** |
| Zero new dependencies | uv.lock/pyproject untouched (above); modelscope never imported (above) | **PASS** |

---

## Anti-Patterns Found

None. No TODO/FIXME/XXX/TBD markers in any phase file (the PLACEHOLDER grep hits are legitimate identifiers: `NAV_PLACEHOLDER_TOAST` for slots 4/5, `SEL_FILTER_PLACEHOLDER` input hint). No stubs: the not-public Zenodo state is the live external truth, not a placeholder; fakes exist only in test lanes.

---

## Requirements Coverage

| Requirement | Description | Status | Evidence |
|---|---|---|---|
| DATA-01 | One-click ModelScope download, registry `download_url` sole authority | ✓ SATISFIED | SC1 chain above; census/R-01/argv/landing lanes |
| DATA-02 | Persistent queue + resume across crash/restart | ✓ SATISFIED | SC2 chain above; restart e2e + boot-resume trio |
| DATA-03 | Post-landing row-count reconciliation vs n_audit, mismatches prominent | ✓ SATISFIED | SC3 chain above; real-subprocess pass/mismatch lanes |
| DATA-04 | Zenodo 19135551 whole-package alternate entry | ✓ SATISFIED | SC4 chain above; probe states + offline e2e |

REQUIREMENTS.md marks all four Complete for Phase 10 — no orphaned requirements (no other IDs map to this phase).

---

## Gaps & Risks (known-accepted, none blocking)

1. **Pre-activation gate (IN-06 + IN-10, accepted by disposition + review iteration 3):** before Zenodo record 19135551 publishes, the maintainer must rule bundle-extract overwrite policy / member-size cap / staging prune, and land the per-chunk cancel check inside the single-file transfer loop. Inert today — the lane refuses at the probe (live-confirmed 404→not_public). Tracked in 10-REVIEW-DISPOSITION.md; not a phase gap.
2. **IN-02 (`first_real_error_line` dead code) + IN-03 progress half:** maintainer polish choices, no runtime risk; reopen at next engine touch.
3. **Bundle zip layout assumption (A4):** the fixture pins zip-root == datasets-root; a differently-prefixed real layout fails explicitly (`landed=0` diagnostics), never silently — verify at activation.
4. **`g` re-audit writes four worktree artifacts by design (R-03):** an accidental keypress commits nothing but leaves a dirty worktree until reviewed — the copy and the confirm-free design follow the approved rulings; the live four-artifact check is the human item below.

---

## Human Verification Required

The GB10 live smoke (10-06-SUMMARY §procedure) — the phase's own architecture makes the real-CLI end-to-end a maintainer confirmation, never CI. Two items, detailed in the frontmatter:

1. **The live download chain** — enqueue GUE__emp_H3 via `d`, observe download → landing → reconcile → the missing-pane drop AND the selection presence flip AND the env-check dataset-dir flip. Every seam below the CLI is machine-proven; the CLI's own behavior was live-probed at research time; this run confirms them composed.
2. **The `g` four-artifact check** — press `g` (or run the audit script), confirm `git status` shows exactly the four artifacts, review, commit as the new baseline.

---

## Gaps Summary

None blocking. All five success criteria are delivered and wired in the real codebase with behavioral test evidence at every machine-checkable seam; the phase constraints hold byte-for-byte; the review cycle closed CLEAN with the kept-open set explicitly dispositioned. The outstanding items are the documented maintainer live smoke (human confirmation by design) and the Zenodo pre-activation gate (external event).

**VERDICT: PHASE_GOAL_ACHIEVED**

(Outstanding human step: the GB10 live smoke per the 10-06 procedure — confirmation, not gap closure. No PARTIAL and no NOT-DELIVERED criteria.)

---

_Verified: 2026-10-13T05:20:00Z_
_Verifier: Claude (gsd-verifier)_
