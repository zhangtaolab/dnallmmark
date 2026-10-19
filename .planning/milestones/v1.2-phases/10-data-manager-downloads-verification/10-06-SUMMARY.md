---
phase: 10-data-manager-downloads-verification
plan: 06
subsystem: tui-hardening
tags: [degradation-sweep, cli-unavailable, corrupt-state, unknown-key, restart-rehydration, transition-table, sc-checklist, phase-gates]
requires:
  - phase: 10-data-manager-downloads-verification
    provides: "10-01..10-03's full queue surface (state machine, channel resolution, engine, reconcile gate, zenodo lane) and 10-04/10-05's screen + app spine + selection integration — the surfaces this plan sweeps and verifies"
provides:
  - The degradation contract proven at both tiers — CLI absent via a nowhere-pointing explicit path (cli_unavailable, no entry, byte-identical file), corrupt-load diagnostic surfaced as a screen status line (session memory), registry-unknown entries tolerated end-to-end
  - The exhaustive state-machine transition table (5 states x 4 mutators, 20 parametrized rows) + the run_task terminal leg (done / exit-N failed / mismatch with both numbers) — no illegal transition silently coerces
  - SC2 proven end-to-end at three tiers: service (persist -> crash -> load downgrade -> claim -> .msc-skip fast path -> reconcile -> done), app (boot_resume kicks exactly once on pending, never without, never twice), screen (the real Backend rehydrates a mid-download seed and renders the restart note)
  - The SC1-5 goal-backward verification checklist — every roadmap criterion mapped to plans/tasks/exact green test names (zero evidence-less rows)
  - The documented GB10 live-smoke procedure (maintainer-executed by design, never CI)
affects: [Phase 11 launch gate (presence reflects live reconcile truth; the degradation paths are honest), the maintainer GB10 smoke]
actuals:
  tokens: 11565      # chars/4 over the realized diff (2e10f12..d543163)
  tasks: 3
  commits: 4         # MEASURED: git rev-list --count 2e10f12..d543163 (2 RED test + 2 GREEN feat, TDD; the docs commits follow this frontmatter, the 10-05 convention)
plan_head_before: 2e10f128798fc600d81f0039c624ee495590cd70
plan_head_after: d5431632d2383b4c9cb36b2b01fcaedb9b5c6531
tech-stack:
  added: []
  patterns:
    - "Availability gate at the consumer, purity at the resolver: resolve_modelscope_cli keeps the pinned verbatim-explicit contract while _resolve_cli refuses a nowhere-pointing path at enqueue/run_task — the honest cli_unavailable state instead of a spawn of a nonexistent binary"
    - "Session-memory diagnostics: load() returns the corrupt diagnostic exactly once (the file is quarantined), last_load_diagnostic() remembers it for the process lifetime so every later snapshot reload still surfaces it"
    - "Active-key guard on the restart downgrade: a reload mid-flight (the Backend's load) can never re-queue the entry the driver is currently executing — the boot-time downgrade is for interrupted restarts only"
    - "Probe-through-the-queue: the real service's probe_zenodo routes its zenodo_fetch seam, making the real adapter's probe offline-injectable exactly like the Pilot fakes"
key-files:
  created: []
  modified:
    - tui/services/download_queue.py
    - tui/screens/data_manager.py
    - tests/tui/test_services_download_queue.py
    - tests/tui/test_pilot_data_manager.py
key-decisions:
  - "The plan's action line (CLI absence via constructor override, 'no PATH games') contradicted the 10-01-pinned verbatim-explicit resolve contract; resolved by gating at the consumers (enqueue/run_task) instead of changing the resolver — the plan's own 'fix surgically what the tests expose' path"
  - "The corrupt diagnostic needed session memory: load() returns it once, but the app-level boot resume discards that return and the screen mounts later — the remembered value is the only way the status line survives reloads (never silent loss)"
  - "DataManagerBackend.missing_snapshot now rehydrates through tolerant load() first — the single seam that makes the screen deterministic without the boot race (in production the boot resume has usually loaded; the read is idempotent), with the active-key guard making it safe mid-download"
  - "The transition table's downloading rows reach their state via claim_next, never via seeding — a seeded downloading entry downgrades to pending at load (D-06 by design), so the owning-edge discipline is baked into the table itself"
  - "The screen rehydration proof asserts the restart-note SEGMENT in the task cell plus the FULL note in the drill-down — the landed 10-04 in-cell truncation contract for an 11-char key, not a re-litigation of it"
requirements-completed: [DATA-01, DATA-02, DATA-03, DATA-04]
coverage:
  - id: H1
    description: "The three degradation states (CLI absent, corrupt file, unknown key) proven at BOTH tiers; no path crashes, blocks, or silently loses state"
    requirement: DATA-01
    verification:
      - kind: unit
        ref: "tests/tui/test_services_download_queue.py (test_enqueue_cli_absent_via_nonexistent_explicit_path, test_run_task_nonexistent_explicit_cli_fails_cli_unavailable, test_corrupt_load_diagnostic_remembered_for_the_session, test_unknown_registry_key_entry_tolerated_end_to_end)"
        status: pass
      - kind: integration
        ref: "tests/tui/test_pilot_data_manager.py (test_cli_unavailable_enqueue_never_adds_a_row_screen_usable, test_load_diagnostic_surfaces_as_status_line, test_unknown_channel_queue_row_renders_state_intact)"
        status: pass
  - id: H2
    description: "The state machine exhaustively pinned; boot resume fires exactly when it should, never twice; the interrupted row's visible note Pilot-proven over the real Backend"
    requirement: DATA-02
    verification:
      - kind: unit
        ref: "tests/tui/test_services_download_queue.py (test_state_machine_transition_table_exhaustive [20 rows], test_run_task_terminal_transitions_from_downloading [3 rows], test_restart_resume_end_to_end_service_tier)"
        status: pass
      - kind: integration
        ref: "tests/tui/test_pilot_data_manager.py (test_boot_resume_rehydrates_and_kicks_once, test_boot_resume_without_pending_never_kicks, test_second_boot_resume_while_busy_starts_no_second_worker, test_data_manager_rehydrates_real_backend_seeded_downloading)"
        status: pass
  - id: H3
    description: "Full phase gates green with counts recorded; the four emptiness cross-checks pass; the SC1-5 checklist exists with zero evidence-less rows; the live smoke documented"
    requirement: DATA-04
    verification:
      - kind: integration
        ref: "make test (pytest 1171 = 1135 wave-5 baseline + 36 new; node 18/18, exit 0); make lint (ruff All checks passed); make typecheck (ty All checks passed); git diff 71b05c4..HEAD --stat -- pipeline/ uv.lock pyproject.toml = EMPTY; --name-only over the official registries, the four committed audit artifacts (incl. ./DATA.md), and dnallm-mark/ script/ scripts/ = EMPTY"
        status: pass
duration: 41min
completed: 2026-10-13
status: complete
---

# Phase 10 Plan 06: Degradation Sweep + Restart E2E + Phase Verification Summary

**One-liner:** The phase's hardening close — the three degradation states (CLI absent via a nowhere-pointing explicit path, corrupt-load diagnostic, registry-unknown entries) proven at both tiers with surgical fixes where the sweep exposed defects, the exhaustive 20-row state-machine transition table plus the run_task terminal leg, SC2's restart story proven end-to-end at service/app/screen tiers (including the real-Backend rehydration over a pinned state root), and the SC1-5 goal-backward checklist mapping every roadmap criterion to exact green test names — full gates green over a phase diff that touches only `tui/` and `tests/`.

## What Was Built

### Task 1 — Degradation + corrupt-state + unknown-key edge sweep

**Service tier.** The CLI availability gate (`_resolve_cli`): `resolve_modelscope_cli` keeps its pinned 10-01 contract (an explicit `cli_path` returns verbatim — a pure resolution function), while `enqueue`/`run_task` now refuse a resolved path that points nowhere — an explicit pointer to nowhere IS the probed-unavailable state (the honest `cli_unavailable` outcome / failed event, zero spawn attempts), and a refused enqueue never creates or rewrites the queue file (byte-identical before/after, pinned on both an absent and a populated file). The corrupt-load diagnostic is now remembered for the session (`last_load_diagnostic`): `load()` returns it exactly once (the file is quarantined on that read), but the screen's later snapshot reloads still surface it. The restart downgrade gained the active-key guard — a reload mid-flight (the screen's snapshot worker) can never re-queue the entry the driver is currently executing. Registry-evolution tolerance pinned end-to-end: an entry whose key vanished from the registry loads, survives `entries()`, never breaks `missing_datasets`/`enqueue` (D-08 idempotence wins), resolves to the unknown channel, and fails honestly at run time with the other entries untouched.

**Screen tier.** `MissingSnapshot.load_diagnostic` + a hidden-by-default `#dl-load-diagnostic` status line under the title bar (verbatim diagnostic, warn style, `display=False` on the healthy path — zero layout cost on the 80x24 budget); `DataManagerBackend.missing_snapshot` now rehydrates the shared queue through tolerant `load()` first and surfaces the remembered diagnostic. Pilot proofs: the cli_unavailable enqueue toasts without adding a row while the screen stays fully usable; the diagnostic renders as a visible status line with both panes live; the unknown-channel queue row renders state-intact with the drill-down naming `channel: unknown (unknown_key)`.

### Task 2 — Restart rehydration end-to-end + the exhaustive transition table

**Service tier.** The exhaustive `(state x mutator)` table — 20 parametrized rows over {pending, downloading, done, failed, mismatch} x {claim_next, retry, cancel, enqueue}: every legal edge applies through its owning mutator; every illegal edge is a no-op with a falsy return and a byte-identical queue file. The downloading rows reach their state via `claim_next` (a seeded downloading entry downgrades at load — D-06), baking the owning-edge discipline into the table. The run_task terminal leg parametrized: pass -> done, exit-7 -> failed, mismatching verdict -> mismatch carrying `Train_mismatch_declared=10_measured=3`. The SC2 capstone: persist mid-download -> crash -> `load()` downgrade (pending + interrupted, persisted) -> claim -> the channel's own resume fast path (exit 0 + success marker over the already-complete tree — the .msc skip) -> landing check on the existing tree -> reconcile pass -> done. Plus `probe_zenodo()` on the service (routes the `zenodo_fetch` seam) — the real adapter's probe is now offline-injectable; no queue lane can reach the wire by construction.

**App tier.** `FakeQueueService` gained a once-only `load_seed` (the boot read); three proofs over the landed 10-04 spine: boot resume with one rehydrated pending entry kicks exactly once (generation 1, the entry runs to done); zero pending (empty seed / terminal-only) never kicks; a second boot-resume while the driver is mid-claim is a guarded no-op (generation stays 1, exactly one worker runs the task).

**Screen tier.** The D-06 visible-recovery contract over the REAL `DataManagerBackend` + real `DownloadQueueService` + a pinned state root: a state file seeded mid-download rehydrates at mount and the row renders the pending glyph with the restart-note segment (in-cell truncation honored; the full note pinned in the drill-down), the queue never kicks (the test app is inert), and the Zenodo probe provably rode the fetch seam (the recording opener saw the frozen URL — offline by construction).

### Task 3 — Phase gates + the SC1-5 goal-backward verification checklist

All gates green and recorded (below); the four phase-scoped emptiness cross-checks pass (the plan-checker W2 correction applied: `git diff 71b05c4..HEAD` against the phase base, not the useless working-tree diff — pipeline/ + uv.lock + pyproject.toml EMPTY, official registries EMPTY, the four committed audit artifacts EMPTY, dnallm-mark/ + script/ + scripts/ EMPTY); the whole-phase manifest touches exactly `tui/` + `tests/` + `.planning/`. The SC1-5 checklist and the GB10 live-smoke procedure follow.

## Performance

- **Duration:** ~41 min (2026-10-12T17:29Z -> 18:10Z)
- **Tasks:** 3/3
- **Files modified:** 4 (all planned; `tui/app.py` from Task 2's file list deliberately untouched — see deviations)

## Task Commits

Each TDD task ran RED -> GREEN with separate commits:

1. **Task 1: degradation sweep** — `29759b1` (test, 4 RED — the nonexistent-path enqueue currently *succeeds*, the diagnostic accessor/status line absent; 3 born-green pins) / `089d01f` (feat)
2. **Task 2: transition table + restart e2e** — `04a8e8c` (test — the probe-seam rows RED: `probe_zenodo` absent, the screen probe not seam-routed; the boot-resume trio and the table born-green over the landed semantics) / `d543163` (feat, incl. the str(None) fix)

## Verification Evidence

- `uv run --group dev --group tui pytest tests/tui/test_services_download_queue.py tests/tui/test_pilot_data_manager.py tests/tui/test_pilot_nav_shell.py -q` — **202 passed** (Task 2's verify command).
- `make test` — **exit 0**: pytest **1171 passed** (1135 wave-5 baseline + 36 new: 7 Task-1 + 29 Task-2), node lane **18/18, fail 0**.
- `make lint` — ruff **All checks passed**. `make typecheck` — ty **All checks passed** (zero ty:ignore, unchanged).
- **Forbidden-surface gates (phase-scoped, W2-corrected):**
  - `git diff 71b05c4..HEAD --stat -- pipeline/ uv.lock pyproject.toml` — **EMPTY** (zero pipeline source changes this phase, zero dependency changes).
  - `git diff 71b05c4..HEAD --name-only -- pipeline/models_info.json pipeline/datasets_info.json` — **EMPTY** (R-01 zero-registry-change).
  - `git diff 71b05c4..HEAD --name-only -- dnallm-mark/data/n_audit.json dnallm-mark/data/n_audit.csv pipeline/eval_subsets.json DATA.md` — **EMPTY** (no automatic path ever ran a default-outputs audit; the working tree is clean).
  - `git diff 71b05c4..HEAD --name-only -- dnallm-mark/ script/ scripts/` — **EMPTY**.
  - The whole-phase file manifest (`git diff 71b05c4..HEAD --name-only`): exactly `tui/**` (8 files), `tests/tui/**` (7 files incl. 2 fixtures), `.planning/**` — nothing else.
- CI network-free: every Zenodo touch is a seam-injected opener (the real adapter's probe now provably routes the `zenodo_fetch` seam); no test lane reaches zenodo.org or modelscope.

## The SC1-5 Goal-Backward Verification Checklist

Every roadmap Phase 10 success criterion mapped to its implementing plans/tasks and the exact green test names at commit time (`tests/tui/…`; all 1171 pass under `make test`). Zero evidence-less rows.

### SC1 — One-click download via the registry `download_url`; presence flips on landing (selection + env check)

| Slice | Plan/Task | Evidence (exact test names, all green) |
|---|---|---|
| Registry URL is the only channel authority (R-01 primary-else-alternate, R-02 census, argv composition, repo-id allowlist) | 10-01 T1/T2 | `test_r02_census_46_downloadable_4_disabled_over_committed_registry`, `test_r01_gue_primary_google_drive_resolves_via_alternates`, `test_r01_modelscope_primary_ignores_alternates`, `test_shape_a_argv_list_absolute_exact_flag_order`, `test_shape_b_argv_whole_repo_local_dir_no_include`, `test_shape_c_argv_subtree_include_plus_rename_pair`, `test_malformed_repo_id_degrades_never_reaches_argv` (test_services_download_queue.py) |
| The engine executes the CLI (LIST argv, spawn discipline, landing gate, shape-C rename) | 10-01 T3 | `test_spawn_pins_list_argv_env_passthrough_pipes_session`, `test_exit_zero_with_success_marker_but_no_files_fails_landing`, `test_shape_c_rename_source_present_target_absent`, `test_nonzero_exit_fails_with_code_and_log` |
| done = landed AND reconcile pass (the flip's gate); only pass keys enter the overlay | 10-02 T1/T2 | `test_run_task_done_populates_entry_reconcile`, `test_merge_presence_flips_missing_to_present_with_measured_ints`, `test_reconciled_rows_feeds_merge_presence_end_to_end` |
| The operator surface: d enqueues, the driver runs, the reconciled key leaves the missing list | 10-04 T2/T3 | `test_d_enqueues_missing_cursor_with_all_outcome_toasts`, `test_driver_e2e_rows_toast_and_missing_refresh` (test_pilot_data_manager.py) |
| The selection-table flip (snapshot + live, mismatch never flips) + the env route | 10-05 T1/T2 | `test_d_enqueues_a_missing_row_through_the_shared_seam_and_kicks`, `test_overlay_flips_missing_presence_to_present_and_back`, `test_mismatch_and_failed_entries_never_flip_presence`, `test_live_flip_through_the_app_event_forward` (test_pilot_selection_custom.py); `test_env_route_hint_renders_and_digit3_is_the_one_path` (test_pilot_data_manager.py) |

**Verdict: PROVEN.** Both halves of the flip chain (seeded-state and live-event) run end-to-end over the real merged snapshot; the d action's outcome contract is identical on both screens by construction (same constants).

### SC2 — The queue persists across TUI exit/crash and resumes where it stopped

| Slice | Plan/Task | Evidence |
|---|---|---|
| XDG persistence, schema, every-transition-writes, atomic rail | 10-01 T1 | `test_enqueue_persists_schema_one_entries_shape`, `test_mutator_round_trip_byte_consistent` |
| Restart downgrade (downloading -> pending + interrupted, persisted) + corrupt quarantine | 10-01 T1 | `test_restart_downgrades_downloading_to_pending_interrupted`, `test_corrupt_file_moved_aside_with_diagnostic_then_usable` |
| The channel's own resume machinery (killpg cancel retains partials; the re-invoke resumes) | 10-01 T3 | `test_cancel_mid_run_terminates_process_group_real_subprocess` |
| **The end-to-end chain at the service tier: persist -> crash -> reboot -> rehydrate -> resume (.msc skip) -> done** | 10-06 T2 | `test_restart_resume_end_to_end_service_tier` |
| Boot resume kicks exactly once on pending work, never without, never twice; the busy guard | 10-04 T1 + 10-06 T2 | `test_boot_is_inert_driver_never_autostarts_never_hangs`, `test_busy_guard_two_rapid_kicks_start_exactly_one_worker` (10-04); `test_boot_resume_rehydrates_and_kicks_once`, `test_boot_resume_without_pending_never_kicks`, `test_second_boot_resume_while_busy_starts_no_second_worker` (10-06) |
| The visible recovery note over the REAL Backend + real service + pinned state root | 10-06 T2 | `test_data_manager_rehydrates_real_backend_seeded_downloading` |

**Verdict: PROVEN.** The exhaustive transition table (`test_state_machine_transition_table_exhaustive`, 20 rows) additionally pins that no illegal transition silently coerces.

### SC3 — Every landed download reconciles row counts against n_audit; mismatches prominent, never silently accepted

| Slice | Plan/Task | Evidence |
|---|---|---|
| The audit subprocess leg (temp staging, four output flags, empty-overlay env, gauntlet verdict semantics) | 10-02 T1 | `test_reconcile_argv_pins_all_output_flags_at_temp_paths`, `test_reconcile_env_exactly_one_override_pinned_to_empty_dir`, `test_reconcile_real_subprocess_pass_over_fixture_csvs`, `test_reconcile_real_subprocess_mismatch_names_numbers_no_deletion` |
| done gated on pass; mismatch a first-class state carrying both numbers; nothing deleted | 10-02 T1 | `test_run_task_reconcile_mismatch_lands_mismatch_state`, `test_reconcile_verdict_mismatch_names_split_and_both_numbers` |
| The committed baseline is read-only to every automatic path (anti-clobber + the g semantics) | 10-02 T3 | `test_committed_artifacts_byte_unchanged_across_real_reconcile_run`, `test_no_automatic_path_ever_constructs_a_no_flag_audit_argv`, `test_reaudit_argv_exactly_interpreter_and_script_no_flags` |
| Mismatch banners under the queue title + sort-to-top; the reconcile-cell vocabulary | 10-04 T2 | `test_mismatch_banner_block_and_sort_to_top`, `test_reconcile_cells_four_vocabularies` |
| Mismatch never flips presence (the exclusion proof) | 10-05 T2 + 10-06 T2 | `test_mismatch_and_failed_entries_never_flip_presence` (test_pilot_selection_custom.py); `test_run_task_terminal_transitions_from_downloading[mismatch_verdict-…]` (10-06) |

**Verdict: PROVEN.**

### SC4 — The Zenodo bulk bundle (record 19135551, once public) reachable as an alternate whole-package entry

| Slice | Plan/Task | Evidence |
|---|---|---|
| The four-state probe (frozen URL, GET-only, 404 = the live-today not_public; activation is the answer flipping, zero code change) | 10-03 T1 | `test_probe_404_maps_not_public_the_live_today_state`, `test_probe_200_maps_public_and_passes_the_seam_kwargs`, `test_probe_accepts_no_url_or_shape_parameter` (test_services_zenodo_bundle.py) |
| The guarded bundle driver + zenodo-kind queue integration (offline E2E to done through the REAL extract + REAL reconcile subprocess; zip-slip; mismatch no-deletion; nothing-landed) | 10-03 T2 | `test_run_task_zenodo_bundle_offline_end_to_end_done`, `test_run_task_zenodo_zip_slip_member_skipped_run_still_lands`, `test_run_task_zenodo_mismatch_lands_mismatch_state_no_deletion`, `test_run_task_zenodo_not_public_fails_record_not_public`, `test_enqueue_zenodo_appends_without_any_cli` (test_services_download_queue.py) |
| The screen surface: the four-state Zenodo line, z public-only enqueue (never silent otherwise), the bundle row label | 10-04 T2 | `test_zenodo_line_four_states`, `test_z_enqueues_only_when_public_never_silent_otherwise`, `test_bundle_row_renders_the_task_name` |
| The real adapter's probe rides the service fetch seam (activation needs zero code) | 10-06 T2 | `test_probe_zenodo_routes_through_the_service_fetch_seam` |

**Verdict: PROVEN** (the not-public state is the live truth — record 19135551 is unregistered today; activation is the probe answer flipping).

### SC5 — Subprocess/thread-worker discipline (the console never freezes); zero credentials stored or echoed

| Slice | Plan/Task | Evidence |
|---|---|---|
| Subprocess discipline: LIST argv, owned Popen, process-group cancel, never in-process download | 10-01 T3 | `test_spawn_pins_list_argv_env_passthrough_pipes_session`, `test_cancel_mid_run_terminates_process_group_real_subprocess` |
| The persisted schema carries zero credential surface (exact field-set equality) | 10-01 T1 | `test_persisted_entries_carry_no_credential_fields` |
| The driver/worker spine: exclusive driver, no-hang drain, responsiveness under a blocked task, boot inertness | 10-04 T1/T3 | `test_boot_is_inert_driver_never_autostarts_never_hangs`, `test_kick_on_empty_queue_exits_and_wait_for_complete_returns`, `test_blocked_task_never_freezes_the_console`, `test_worker_exits_on_drain_and_restarts_on_next_kick` |
| The g re-audit and every service I/O leg stay inside workers | 10-04 T2 | `test_g_reruns_reaudit_in_worker_ui_stays_responsive` |
| Credentials remain the CLI's own business; nothing imports modelscope; the CLI-absent degradation is first-class | 10-01 T1 + 10-06 T1 | `test_service_module_never_imports_modelscope`; `test_enqueue_cli_absent_via_nonexistent_explicit_path`, `test_run_task_nonexistent_explicit_cli_fails_cli_unavailable`, `test_cli_unavailable_enqueue_never_adds_a_row_screen_usable` |

**Verdict: PROVEN.** The recorded T-10-06-01 acceptance (unbounded download runtime; operator cancel the bounded escape) is recorded for the maintainer below.

## The GB10 Live-Smoke Procedure (maintainer-executed — never CI, by design)

The research validation architecture: the offline lanes prove the seams; one live run on the GB10 host proves the real CLI's behavior against them. Procedure:

1. **Launch:** `make tui` on the GB10 host (the modelscope console script on PATH, SDK token already in `~/.modelscope` — the TUI never touches either beyond passing `dict(os.environ)` through).
2. **Route:** from the env screen (or the selection screen), press `3` — the data-manager screen mounts with the missing list computed over the committed n_audit (7 missing GUE keys on the current baseline).
3. **Enqueue:** cursor to `GUE__emp_H3` in the missing list (shape A, small — the suggested first target), press `d`. Expected: the enqueued toast, the queue row appears (pending -> downloading with the indeterminate tick, then live percents as the CLI's stderr parses).
4. **Observe the chain:** progress streams into the row; on exit 0 the landing gate checks the three split CSVs under `pipeline/datasets/GUE/emp_H3`; the reconcile subprocess runs; pass -> the QUEUE_FLIP_TOAST fires, the row turns done, the key leaves the missing list; press `2` — the selection table's presence cell for the key now reads present (the merged snapshot). A mismatch instead lands the mismatch state + banner (nothing deleted) — press `g` to re-audit if expected.
5. **The g audit-diff check (the four-artifact proof):** press `g` on a mismatch row (or run `python script/audit_n_frequencies.py` from the repo root). `git status` must show EXACTLY four modified artifacts — `dnallm-mark/data/n_audit.json`, `dnallm-mark/data/n_audit.csv`, `pipeline/eval_subsets.json`, `DATA.md` — nothing else; review the diff and commit it as the new baseline (R-03).
6. **Interrupt/resume check (optional):** mid-download, quit the TUI (or kill it), relaunch `make tui` — the boot resume re-queues the interrupted entry (the row shows the restart note), the channel's own `.msc` skip makes the re-invoke fast, and the row completes.
7. **Record outcomes** (progress parse quality, landing, reconcile, the flip, the four-artifact diff) against this procedure in the maintainer's notes; any deviation from the offline-pinned behavior is a defect against the corresponding test above.

Accepted-by-design note (T-10-06-01): a legitimate multi-GB transfer has no artificial timeout; the operator's `x` cancel (SIGTERM -> SIGKILL on the process group) is the bounded escape, real-subprocess-proven in 10-01.

## Deviations from Plan

**1. [Rule 1 - design conflict, resolved surgically] the CLI-absent test vehicle**
- **Found during:** Task 1 RED — the plan's action line ("the CLI absence via the constructor cli_path override to a nonexistent path — no PATH games needed") is impossible against the 10-01-pinned contract that `resolve_modelscope_cli` returns an explicit path VERBATIM (`test_cli_probe_explicit_arg_wins`).
- **Fix:** kept the resolver pure; added the availability gate at the consumers (`_resolve_cli` used by `enqueue`/`run_task`) — the nonexistent explicit path now yields the honest `cli_unavailable` instead of enqueueing a task that would spawn a nonexistent binary. Both new tests pin it; the pinned 10-01 test stays green unmodified. **Commit:** `089d01f`.

**2. [Rule 1 - self-inflicted, fixed in-lane] the pre-existing absent-CLI engine fixture**
- **Found during:** Task 1 GREEN — `test_cli_absent_at_run_time_fails_without_spawning` enqueued through a deliberately nonexistent `cli=` override, which the new gate correctly refuses; the override was dead weight (the test nulls `_cli_path` immediately after).
- **Fix:** the test now enqueues through the existing fake CLI, then stages the run-time absence. Same proof, honest staging. **Commit:** `089d01f`.

**3. [Rule 1 - bug, caught by the Task-2 test] `str(None)` in the Backend diagnostic read**
- **Found during:** Task 2 RED — the Task-1 Backend's `str(diagnostic_getter())` rendered the truthy string `"None"` as the status line over every healthy real-Backend snapshot.
- **Fix:** stringify only a non-None value. **Commit:** `d543163`.

**4. [Task 2 test-authoring, self-corrected before RED commit] two fixture defects**
- The transition table's downloading rows initially seeded the state directly — a seeded downloading entry downgrades to pending at load (D-06 by design); the rows now reach downloading via its owning edge (`claim_next`), which is itself the discipline the table exists to pin.
- The screen rehydration test initially asserted the FULL restart note in the task cell; the landed 10-04 truncation contract clips its tail for an 11-char key (full note in the drill-down) — the assertions now honor that contract exactly.

**5. [Rule 2 - hardening, in-plan] the active-key guard + the Backend load**
- The plan's screen-tier Task-2 proof ("mount the data manager through the real Backend over the pinned state root -> the row renders") requires the Backend to rehydrate through `load()`; a naive load() mid-download would downgrade the in-flight entry (a double-execution hazard). The guard (skip the downgrade for keys with a live process) landed inside Task 1's GREEN as the prerequisite, with the whole-screen proof in Task 2.

**6. [W4 - manifest note] `tui/app.py` listed in Task 2's files but untouched**
- All three app-tier proofs (kick-once, no-kick-without-pending, no-second-worker-while-busy) passed over the landed 10-04 `boot_resume_queue` + busy guard — no defect surfaced, so no app.py edit was needed. The frontmatter's `files_modified` omission of app.py (plan-checker W4) is therefore moot.

**7. [Rule 3 - CI-network-free] the service `probe_zenodo` method**
- Mounting the screen over the REAL Backend would have fired a real GET to zenodo.org (the Backend's probe-through-the-queue found no method on the real service and fell through to the wire). Added the thin delegate through the `zenodo_fetch` seam — the whole queue surface is now offline-injectable by construction. **Commit:** `d543163`.

---

**Total deviations:** 7 documented (2 Rule-1 code fixes, 1 Rule-1 caught bug, 1 test-authoring batch, 1 Rule-2 hardening, 1 manifest note, 1 Rule-3 seam)
**Impact on plan:** No scope creep — every change inside the four planned files; all gates green.

## Issues Encountered

None blocking. `gsd_run` was unavailable as a shell command but the node CLI (`node ~/.claude/gsd-core/bin/gsd-tools.cjs`) served every state handler.

## Known Stubs

None. Every surface this plan touched is wired end-to-end; the not-public Zenodo state remains the live truth (record 19135551 unregistered; activation is the probe answer flipping, zero code change — D-12's design). The GB10 live smoke is a documented maintainer procedure by the plan's own architecture (offline lanes prove the seams), not a stub.

## Threat Flags

None — no security-relevant surface beyond the plan's threat model. All seven register dispositions verified: T-10-SC1/SC2/SC3/SC5 mitigated by the checklist rows above (each cites green evidence); T-10-SC4 mitigated (10-03 lanes + the seam-routing pin); T-10-06-01 accepted and recorded in the live-smoke block; T-10-SC (package installs) — `git diff 71b05c4..HEAD -- uv.lock pyproject.toml` EMPTY across the whole phase.

## Next Phase Readiness

- **Phase 11 (launch gate):** presence now reflects live reconcile truth everywhere (selection + env route through the merged view); the degradation paths (CLI absent, corrupt state, unknown keys) are honest first-class states; the driver/worker idioms (per-worker groups, generation tagging, busy guard, boot resume) are proven patterns to reuse.
- **The maintainer's GB10 smoke and the future Zenodo activation need zero further code** — the procedure above is the only outstanding manual step.

## Self-Check: PASSED

All five touched files exist on disk (the four planned code/test files + this SUMMARY); all four plan commits are ancestors of HEAD (`29759b1`, `089d01f`, `04a8e8c`, `d543163`); `commits: 4` measured from the persisted ledger (`2e10f12..d543163`); full gates green (1171 pytest + node 18/18, ruff, ty); all four phase-scoped forbidden-surface diffs EMPTY.
