---
phase: 08-tui-foundation-env-check-selection
verified: 2026-10-17T07:51:50Z
status: passed
score: 6/6 must-haves verified
covered_files:
  - .planning/phases/08-tui-foundation-env-check-selection/08-01-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-01-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-02-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-02-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-03-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-03-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-04-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-04-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-05-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-05-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-06-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-06-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-07-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-07-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-08-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-08-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-09-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-09-SUMMARY.md
  - Makefile
  - dnallm-mark/data/n_audit.json
  - pipeline/env_smoke.py
  - pipeline/registry_loader.py
  - pyproject.toml
  - schemas/run_template.json
  - tests/test_env_smoke_bytes.py
  - tests/tui/conftest.py
  - tests/tui/test_card_site_hardening.py
  - tests/tui/test_import_lock.py
  - tests/tui/test_language_rederivation.py
  - tests/tui/test_pilot_boot.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_matrix.py
  - tests/tui/test_pilot_run_config.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_pilot_selection_custom.py
  - tests/tui/test_services_registries.py
  - tests/tui/test_services_selection.py
  - tests/tui/test_services_templates.py
  - tests/tui/test_strings_phase11.py
  - tests/tui/test_work_site_hardening.py
  - tui/__main__.py
  - tui/app.py
  - tui/screens/about.py
  - tui/screens/data_manager.py
  - tui/screens/env_check.py
  - tui/screens/matrix.py
  - tui/screens/monitor.py
  - tui/screens/run_config.py
  - tui/screens/selection.py
  - tui/screens/wizard.py
  - tui/services/env_check.py
  - tui/services/env_gate.py
  - tui/services/quick_check.py
  - tui/services/registries.py
  - tui/services/selection.py
  - tui/services/settings.py
  - tui/services/templates.py
  - tui/strings.py
  - tui/styles.tcss
  - uv.lock
covered_digest: "v3:sha256:a66c4d36dc2c99816ff2729b5481b8a2c401801bd91f50ca3a67b66034900497"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 6/6
  gaps_closed: []
  gaps_remaining: []
  regressions: []
deferred:
  - truth: "Critical FAILs block entry into the launch flow (ENV-03) and the quick-check re-validates before each task launch (ENV-04) — the launch-flow wiring itself"
    addressed_in: "Phase 11"
    evidence: "CLOSED by its successor: Phase 11 landed the env preflight + E2' typed gate (e63a08d) and the launch gate screen — Phase 11 verification passed (round 3 at 6bb768f). Kept as the historical deferral record."
advisory:
  - finding: "Pin guard-granularity: the card-site pin's guard-presence check is per-FUNCTION — stripping ONE of build_wizard's two comprehension guards leaves the sibling's isinstance in the function and the pin stays green"
    category: other
    reason: "Implements the plan's own per-function wording exactly; residual covered behaviorally — the w Pilot regression test exercises BOTH comprehensions (re-run green this pass). tests/tui/test_card_site_hardening.py byte-unchanged through this delta (zero-diff confirmed)."
    evidence_status: "none provided — mutation-evidenced in a prior pass's report; unchanged this pass"
  - finding: "WR-02 (08-scope label, pre-feedback-round): degraded dnallm_compat map renders a silent blank models table on slot 2 (no degraded-state row when the default pool yields zero entries)"
    category: architectural
    reason: "CARRIED: pipeline/dnallm_compat.json untouched by the klw delta; no deterministic evidence either way (no failing test, no reproducible defect). Post-phase scope, review-tracked. Distinct from the feedback-round WR-02 (kill channel), which is now FIXED."
    evidence_status: "none provided"
  - finding: "WR-03 (08-scope label, pre-feedback-round): synchronous event-loop file reads (_render_storage, _submit_save→custom_names) contradict the module's own D-03 read-seam discipline"
    category: architectural
    reason: "CARRIED: the klw selection.py delta (+13 lines) touches only apply_queue_progress ordering — the read seams are untouched; bounded local-file stalls, not a Phase 8 must-have breach; review-tracked open. Distinct from the feedback-round WR-03 (mixed roots), which is now FIXED."
    evidence_status: "none provided"
  - finding: "Info-level residuals: env screen action_show_detail still lacks the is_valid_coordinate guard its selection-screen twins carry (re-confirmed at env_check.py:759-763 this pass); IN-04 degenerate filter tokens open in the disposition ledger; NAV_PLACEHOLDER_* constants zero-consumer"
    category: other
    reason: "Info-level, post-phase scope, review-tracked. IN-01/IN-02/IN-03 (the ledger's other open info items) are now FIXED and adjudicated below — the residual set shrank to these three."
    evidence_status: "none provided"
  - finding: "klw Maintainer Items (new this delta, deliberately not fixed): wizard keycap step-aware-visibility ruling pending (carried from dnr); run_finetune sibling hard-index sites :849/:1077/:1322 raise the same KeyError class for schema-legal minimal entries on their code paths (07-scope, recorded in the klw SUMMARY)"
    category: other
    reason: "Explicitly recorded as NOT changed per the batch's non-goals; maintainer-ruled future batch. Phase-7 pipeline scope (07-CR-01 covered only the two model-loop reads); no Phase 8 must-have breach."
    evidence_status: "none provided"
---

# Phase 8: TUI Foundation (Env Check & Selection) Verification Report

**Phase Goal:** The console exists and is trustworthy at rest — `make tui` opens a Textual app whose startup shows a persisted full environment-check panel, and operators build model×dataset selections k9s-style with presets, templates, and presence columns — with every non-retrofittable decision (textual-free services layer, `[tui]` dependency group, Pilot test harness, tolerant artifact loader, constants-module copy discipline) locked as ADRs
**Verified:** 2026-10-17T07:51:50Z
**Status:** passed
**Re-verification:** Yes — eighth pass (third post-closeout micro-refresh), at HEAD 6bb768f. The seventh pass verified 6/6 at tree 0672992 (committed as the round-2 refresh). The delta on this phase's covered set since = quick-261017-klw ONLY: the 08-review fix batch (WR-01/02/03 in 06d2679, IN-01/02/03 in 0d02e18) plus docs commits — `tui/app.py` (+134), `tui/screens/env_check.py` (+10), `tui/screens/selection.py` (+13), `tui/screens/run_config.py` (+50, phase-11 covered), and the three test files (+368). Zero delta on strings.py, styles.tcss, snapshots, env_smoke.py, registry_loader.py, Makefile, pyproject.toml, uv.lock, and every structural pin file (confirmed by empty `git diff 0672992..HEAD` over each). This pass verified the fix sites behaviorally (7 named tests), re-ran every structural/live gate over the changed files, and confirmed must-have standing. Full suite NOT re-run per dispatch instruction (known-good at this HEAD: 1F/1867P sole machine-local member, node 26/26, ruff+ty green, goldens green).

## Stale-Refresh Delta Analysis (why this pass exists)

`git diff 0672992..HEAD --stat` over the covered tree — only five implementation files changed, all from the klw fix batch:

| File | Delta | Phase-8 impact |
| ---- | ----- | -------------- |
| `tui/app.py` (+134) | WR-01 ctrl+c copy delegation, WR-02 exit-kill worker, WR-03 mixed-root MULTI form | Truth 1 wiring re-verified live: `get_default_screen() → EnvCheckScreen(env_check_service=...)` intact (app.py:666-668); boot Pilot lane 5 green; work-site hardening pin green with ZERO edits to the pin file (the new @work site carries exit_on_error=False AND an internal broad guard) |
| `tui/screens/env_check.py` (+10) | IN-03 synchronous `_check_in_flight` | Truths 1/2 untouched elsewhere: r binding, persist tail, worker protocol all outside the hunk; env-check Pilot lane green in full (17 tests inside the 62-lane) |
| `tui/screens/selection.py` (+13) | IN-01 store-below-guard ordering | Truths 4/5/6 re-verified: selection-custom lane green in full (45 tests inside the 62-lane), card-site AST pin green, the four named 08-09 crash chains green |
| `tui/screens/run_config.py` (+50) + `tests/tui/test_pilot_run_config.py` (+293) | IN-02 scope-tagged staleness filter + WR test evidence (phase-11 covered files; the WR-01/02/03 behavioral evidence lives here) | 7 named fix-site tests green this pass including all five WR/IN-02 tests from this file |
| `tui/strings.py`, `tui/styles.tcss`, `tests/tui/__snapshots__/`, `pipeline/env_smoke.py`, `pipeline/registry_loader.py`, `Makefile`, `pyproject.toml`, `uv.lock`, `schemas/`, all pin test files | 0 lines | Zero new strings, zero SVG interaction, prohibition files byte-unchanged — every prohibition re-confirmed trivially |

## 08-REVIEW Fix-Batch Adjudication (the dispatch question)

The working-tree disposition ledger (pending orchestrator commit) marks WR-01..03 + IN-01..03 fixed via klw. This verifier adjudicated each resolution against the reviewer's own fix sketch and a passing behavioral test — **all six RESOLVED**:

| Finding | Reviewer's fix sketch | Implementation at HEAD | Behavioral evidence (this pass) | Verdict |
| ------- | --------------------- | ---------------------- | ------------------------------- | ------- |
| WR-01 (ctrl+c kills Input copy) | Delegate when focused widget is an Input with non-empty selection | `on_event`: inside the existing non-modal guard, `if isinstance(focused, Input) and focused.selected_text: await super().on_event(event); return` (app.py:1204-1208). The reviewer's sketch named `.selection`, which does not exist in textual 8.2.8 — the implementation uses the real property `selected_text` (`_input.py:854`, verified in the installed venv), whose copy binding is `ctrl+c,super+c -> copy` (`_input.py:139`, verified). Empty selection / non-Input / modal keep today's routing | `test_ctrlc_copies_when_input_holds_a_real_selection` PASS (real key-press selection on 8.2.8) | RESOLVED |
| WR-02 (serial on-loop kill fan-out) | Dispatch through a one-shot thread worker; exit in completion handler | `ExitModal.action_kill_quit` → `request_kill_and_exit(roots)` → `@work(exclusive=True, thread=True, group="exit-kill", exit_on_error=False)` `_exit_kill_worker`: per-root broad guard (log + continue — every root attempted), `ExitKillsDone` posted UNCONDITIONALLY, `on_exit_kills_done` → `self.exit()` | `test_exit_k_raising_kill_still_attempts_every_root_and_exits` PASS (exercises the raising path — the stronger form; the per-root guard's log lines visible in test output) | RESOLVED |
| WR-03 (mixed roots drop attached CLI sweep) | Multi-root form with combined tuple (review supplied exact shape) | `attached_extra = attached_running and attached_root not in roots`; MULTI fires on `len(roots) > 1 or (roots and attached_extra)` with `combined = tuple(roots) + ((attached_root,) if attached_extra else ())` (app.py:1132-1143) — matches the sketch verbatim in intent | `test_mixed_roots_exit_names_and_kills_both_tui_and_attached` + `test_mixed_roots_exit_enter_detaches_both` PASS | RESOLVED |
| IN-01 (slot-2 live-dict residue) | Mirror slot-3 ordering: check first, store only for passing ticks | `_live_model_entries().get(key)` / state check moved ABOVE both stores; stores sit directly before the cell update (selection.py:1607-1621) | `test_dataset_kind_tick_stores_no_live_dict_residue` PASS | RESOLVED |
| IN-02 (gate id-space collision) | Tag the error with its counter; compare against that counter only | `GateWorkerError` carries `scope: str \| None` ('stage'/'launch'/None); filter compares scope 'launch' vs `_gate_launch_id`, everything else vs `_gate_stage_id` | `test_gate_worker_error_scope_tags_split_the_id_spaces` PASS | RESOLVED |
| IN-03 (remount stale-cache window) | Set `_check_in_flight = True` synchronously in action_refresh, kick_download_queue discipline | Flag set on the event loop immediately after `_run_id += 1`, BEFORE `run_full_check()` dispatch; worker-body set retained as mount-path belt (env_check.py:710-719) | `test_refresh_sets_in_flight_flag_synchronously` PASS | RESOLVED |

Remaining open in the ledger after this batch: IN-04 only (degenerate filter tokens, carried from the hhx round). CR-01 was fixed earlier (f9528e3). The three feedback-round advisories carried in the round-2 report (its advisory rows 4-6) are now RESOLVED and dropped from the advisory set.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | SC1: `make tui` opens the console; startup runs the full environment check reusing env_smoke kernels; per-item ✓/✗ status with drill-down | ✓ VERIFIED | Makefile `tui` recipe unchanged (`uv run --group tui --group gpu python -m tui`); `get_default_screen() → EnvCheckScreen(env_check_service=...)` intact through the WR-01..03 rework (app.py:666-668, read at HEAD); services import env_smoke kernels top-level (zero delta on tui/services/*); worker protocol + drill-down outside the IN-03 hunk; boot Pilot lane 5 passed this pass (verifier-executed); env_smoke.py byte-unchanged since round 2 (empty diff) with bytes goldens green in the 25-lane |
| 2 | SC2: Check results persist with visible 上次检查 date; same-day restarts read the cache; manual refresh re-checks | ✓ VERIFIED | `ENV_LAST_CHECK_LINE` registry entry live-read this pass: zh `"上次检查: {checked_at}"` / en `"Last check: {checked_at}"` (strings.py:266-268 — strings.py byte-unchanged this delta); `r` binding + `action_refresh` + persist tail unchanged (the IN-03 fix adds one synchronous flag set inside action_refresh before the dispatch — strengthens this truth's remount behavior, now test-pinned); env-check Pilot lane green in full inside the 62-lane |
| 3 | SC3: Critical FAILs visibly block with reason; missing-dataset routes to data management; quick-check re-validates the launch-required subset | ✓ VERIFIED | Live this pass (verifier-executed over the real modules): CRITICAL {cuda, dnallm, matmul, numpy, peft, version_pins} ∩ ROUTING {dataset_dirs, model_dirs} = ∅ (disjoint=True); `QUICK_CHECK_KERNEL_IDS` = 7 ids ⊂ the 8-kernel space (subset=True, matmul excluded); env_gate/quick_check services byte-unchanged this delta. Phase-11 launch-flow wiring landed (e63a08d) — the historical deferral stays CLOSED |
| 4 | SC4: Model/dataset lists first-class selectable; k9s filter; spacebar marks on stable row_keys; presets; read-only matrix auxiliary view | ✓ VERIFIED | Live this pass: real `SelectionBackend().load_selection_data()` → 60 models / 50 datasets, both load errors None; preset_menu options live: tier-1 (2 models), tier-2 (3), all (59) + 3 customs (d1, demo-walkthrough, probe-preset), load_error None; selection-custom Pilot lane 45 tests green in full (verifier-executed, includes the IN-01 residue pin and the existing in-place cell-update test); matrix.py byte-unchanged (read-only by absent bindings holds); spacebar `toggle_mark`/`update_cell` outside the IN-01 hunk |
| 5 | SC5: Presence columns; templates round-trip as validated JSON with sweep_priorities tier interop; i18n through the constants module; foundation invariants (services textual-free, `[tui]` isolation, Pilot green CPU-side) | ✓ VERIFIED | Live this pass: presence 50 entries + model_presence 60 entries (16 present — real filesystem state, unchanged from round 2); 0 textual imports across all 17 tui/services modules (verifier AST scan); 0 CJK outside tui/strings.py across tui/ (grep gate — critical this pass because app.py changed, and the new code adds zero string constants: scope tags and log lines are internal, confirmed zero-diff on strings.py); [tui] group exact and untouched (textual>=8.2,<9 + platformdirs + jsonschema, pyproject:71-79); templates/services lanes byte-unchanged (standing round-2 evidence: 121 tier-1 services tests); import-lock + language-rederivation + strings-phase11 lanes green in the 25-lane |
| 6 | Goal-derived foundation invariant: tolerant artifact loading landed such that loader-accepted registry inputs degrade — the console never exits on them | ✓ VERIFIED | The four named 08-09 crash-chain tests green this pass (verifier-executed through the REAL app + REAL backend, 4 passed in 2.70s — selection.py changed this delta, so re-run was mandatory); card-site AST pin green (selection.py's IN-01 hunk sits below the pinned extraction sites); work-site @work never-exit pin green with ZERO pin edits — the new exit-kill worker satisfies it structurally; `git diff 0559c40..HEAD -- pipeline/registry_loader.py`: 0 lines (prohibition holds) |

**Score:** 6/6 truths verified (0 present, behavior-unverified)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | ENV-03/ENV-04 launch-flow wiring (historical record) | Phase 11 | CLOSED by Phase 11: env preflight + E2' typed gate landed (e63a08d), Phase 11 verification passed (round 3 at 6bb768f). Kept for the audit trail |

### Advisory (New Scope, Unevidenced)

Carried forward in reduced form: the three feedback-round warnings (round-2 report rows 4-6) are now FIXED and adjudicated above — they leave the advisory set. Rows 1-3 carry unchanged; row 4 shrank (IN-01..03 resolved); row 5 is new (klw's own recorded maintainer items). None has deterministic evidence and none breaches a Phase 8 must-have, so all stay advisory per the #3304 evidence gate.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | Pin guard-granularity: guard-presence is checked per-FUNCTION, so one-of-two guard deletion inside build_wizard escapes the pin alone | other | Plan implements its own per-function wording; the w Pilot regression test (re-run green this pass) exercises both comprehensions; pin file byte-unchanged through this delta |
| 2 | WR-02 (08-scope label): degraded compat map renders a silent blank models table on slot 2 | architectural | post-phase scope, review-tracked; dnallm_compat.json untouched this delta, no deterministic evidence this pass |
| 3 | WR-03 (08-scope label): synchronous event-loop file reads contradict the pinned D-03 read-seam discipline | architectural | post-phase scope, bounded stall, review-tracked; the klw selection.py delta touches only apply_queue_progress — the read seams unchanged, no deterministic evidence this pass |
| 4 | Info-level residuals: env action_show_detail coordinate guard absent (:759-763, re-confirmed this pass), IN-04 degenerate filter tokens open, NAV_PLACEHOLDER_* dead constants | other | info-level, review-tracked; no must-have breach; the ledger's other info items (IN-01..03) are now fixed |
| 5 | klw maintainer items: wizard keycap step-aware ruling pending; run_finetune sibling hard-indexes (:849/:1077/:1322) for minimal custom entries | other | deliberately not fixed per the batch's non-goals; 07-scope pipeline items recorded in the klw SUMMARY; future maintainer-ruled batch |

### Required Artifacts

All implementation artifacts in the covered set exist and are substantive. The delta touched only app.py, env_check.py, selection.py, run_config.py, and three test files — each verified at full depth this pass (diff read, fix-site tests executed, regression lanes run); everything else is byte-identical to the round-2-verified state (empty `git diff 0672992..HEAD` per file). The plans' must_haves use string-shaped lists that predate the verify.artifacts/verify.key-links verbs' dict shape, so Levels 1-4 were verified by direct read, execution, and the live gates.

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `tui/app.py` | composition root: default screen, exit chain, ctrl+c intercept | ✓ VERIFIED | WR-01/02/03 sites read at HEAD (delegation :1204-1208, exit-kill worker :1221-1252, mixed-root form :1132-1143); boot lane + 7 fix tests + work-site pin green |
| `tui/screens/env_check.py` | env-check screen: worker, persist line, refresh, verdict | ✓ VERIFIED | IN-03 hunk read (:710-719); full lane green inside the 62 |
| `tui/screens/selection.py` | slot-2 selection screen + extraction-site guards | ✓ VERIFIED | IN-01 hunk read (:1607-1621); card-site pin + crash chains + full custom lane green |
| `tui/services/*` (17 modules) | textual-free services layer | ✓ VERIFIED | Zero delta since round 2 AND fresh AST scan: 0 textual imports across all 17 |
| `tui/strings.py` | i18n single home | ✓ VERIFIED | Byte-unchanged (empty diff) — zero new strings claim holds; live registry read confirms zh/en pair |
| `pipeline/env_smoke.py` | structured kernels; fail-closed registry reads | ✓ VERIFIED | Byte-unchanged since round 2; bytes goldens green in the 25-lane |
| `pipeline/registry_loader.py` | fail-loud contract BYTE-UNMODIFIED (prohibition) | ✓ VERIFIED | `git diff 0559c40..HEAD`: 0 lines — now inside the fingerprinted covered set |
| `pyproject.toml` / `Makefile` / `uv.lock` | [tui] group exact; make tui / make test lanes | ✓ VERIFIED | All byte-unchanged since round 2; [tui] block re-read (:71-79) |
| `tests/tui/test_pilot_{env_check,selection_custom}.py` | Pilot lanes over the changed screens + the two new RED-first tests | ✓ VERIFIED | 62 passed in 13.65s this pass |
| `tests/tui/test_pilot_run_config.py` | WR-01/02/03 + IN-02 behavioral evidence (phase-11 lane, attested here for the 08-REVIEW resolutions) | ✓ VERIFIED | 7 named tests green this pass; the two adapted CDR-2 tests (empty-selection form) included in the passing set |
| Structural pin files (card-site, work-site, import-lock, rederivation, strings-phase11, env_smoke-bytes) | AST pins + tripwires | ✓ VERIFIED | 25 passed in 0.88s this pass; work-site pin covers the NEW exit-kill worker with zero pin edits |

### Key Link Verification

Verified manually (string-shaped plan lists predate the verbs' dict shape). Only links whose files changed this delta were re-executed; the rest are byte-identical to the round-2-verified state.

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `make tui` | `tui.app` | recipe → `uv run --group tui --group gpu python -m tui` | ✓ WIRED | Makefile unchanged; boot Pilot green this pass |
| app startup | EnvCheckScreen | `get_default_screen()` | ✓ WIRED | app.py:666-668 at HEAD, through the WR rework |
| `r` keypress | full re-check | `action_refresh` (+ synchronous in-flight flag) | ✓ WIRED | IN-03 fix strengthens the remount path; sync-flag test green |
| ExitModal `[k]` | launcher kill fan-out | `request_kill_and_exit` → exit-kill worker → `ExitKillsDone` → `self.exit()` | ✓ WIRED | New chain read at HEAD; raising-kill + happy-path tests green |
| ctrl+c over selection-holding Input | Input copy binding | non-modal guard → `isinstance(focused, Input) and focused.selected_text` → `super().on_event` | ✓ WIRED | Real 8.2.8 property/binding verified in venv; delegation test green |
| spacebar / SelectionBackend / presence / presets | mark set / registries / n_audit + filesystem / sweep_priorities + customs | unchanged seams | ✓ WIRED | Live this pass: 60/50 errors None, 16/60 present, presets correct |
| Services layer | textual | must NOT import | ✓ WIRED (negative) | Fresh AST scan: 0 imports across 17 modules |
| i18n copy | constants module | strings.py only | ✓ WIRED (negative) | Fresh grep: only strings.py carries CJK |
| Loader prohibition | `pipeline/registry_loader.py` | must stay byte-unmodified since 0559c40 | ✓ WIRED (negative) | 0-line diff |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| model list | `model_entries` | overlay-merged registry | Yes — live 60, load_error None | ✓ FLOWING |
| dataset list | `dataset_entries` | committed registry | Yes — live 50, load_error None | ✓ FLOWING |
| presence | `presence` / `model_presence` | filesystem + n_audit + queue reconcile | Yes — live 50 + 60 entries, real 16-present split (marker values live-read: 'present'/'missing'/'unknown') | ✓ FLOWING |
| presets | `preset_menu()` | sweep_priorities.json + config-root customs | Yes — live tier-1(2)/tier-2(3)/all(59) + 3 customs, load_error None | ✓ FLOWING |
| env gate | CRITICAL/ROUTING/QUICK_CHECK_KERNEL_IDS | env_gate + quick_check over env_smoke kernels | Yes — live disjointness + 7⊂8 subset | ✓ FLOWING |
| exit kill fan-out | `ExitKillsDone` | exit-kill worker over launcher roots | Yes — exercised through the real app in the raising-kill test (log lines observed) | ✓ FLOWING |

### Behavioral Spot-Checks

All executed by this verifier at HEAD 6bb768f (fresh, this pass; working tree clean except .planning state). Full-suite evidence (1 failed / 1867 passed — the single machine-local member; node 26/26; ruff + ty green; goldens green) was provided by the dispatching context on this exact tree and NOT re-run per instruction.

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| The six 08-REVIEW fix sites (WR-01, WR-02, WR-03 ×2, IN-01, IN-02, IN-03) | `pytest <7 exact node ids across test_pilot_run_config/selection_custom/env_check>` | 7 passed in 3.06s | ✓ PASS |
| Structural pins over the changed files (work-site incl. new exit-kill @work site, card-site, import-lock, language-rederivation, strings-phase11, env_smoke bytes) | `pytest tests/tui/test_{work_site,card_site}_hardening.py tests/tui/test_import_lock.py tests/tui/test_language_rederivation.py tests/tui/test_strings_phase11.py tests/test_env_smoke_bytes.py -q` | 25 passed in 0.88s | ✓ PASS |
| Full env-check + selection-custom Pilot lanes (changed screens) | `pytest tests/tui/test_pilot_env_check.py tests/tui/test_pilot_selection_custom.py -q` | 62 passed in 13.65s | ✓ PASS |
| Boot Pilot lane (app.py exit chain through the WR rework) | `pytest tests/tui/test_pilot_boot.py -q` | 5 passed in 0.97s | ✓ PASS |
| The four named 08-09 crash chains (selection.py changed) | `pytest tests/tui/test_pilot_selection.py::<4 exact node ids>` | 4 passed in 2.70s | ✓ PASS |
| Live T3 gates | `uv run --group dev --group tui python` over real env_gate/quick_check | disjoint=True; 7 ids ⊂ 8-kernel space | ✓ PASS |
| Live selection backend + presets | `SelectionBackend().load_selection_data()` + `preset_menu()` | 60/50, errors None, presence 50 + model_presence 60 (16 present), presets tier-1(2)/tier-2(3)/all(59) + 3 customs, load_error None | ✓ PASS |
| textual 8.2.8 API reality for WR-01 | grep installed venv `_input.py` | `selected_text` property (:854), `ctrl+c,super+c -> copy` binding (:139) | ✓ PASS |
| Services textual-import lock | verifier AST scan over tui/services/*.py | 17 files, 0 textual imports | ✓ PASS |
| CJK single-home | `grep -rlPn "[\x{4e00}-\x{9fff}]" tui/` | only tui/strings.py | ✓ PASS |
| Loader prohibition | `git diff 0559c40..HEAD -- pipeline/registry_loader.py` | 0 lines | ✓ PASS |
| Zero-delta prohibitions (strings/styles/snapshots/env_smoke/Makefile/pyproject/uv.lock/pins) | `git diff 0672992..HEAD --stat` per file | empty | ✓ PASS |
| Debt markers | TBD/FIXME/XXX over the five changed implementation files + three test files | 0 hits | ✓ PASS |

### Probe Execution

No probes declared for this phase — not applicable.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| ENV-01 | 08-01, 08-03, 08-04, 08-06, 08-08 | Startup full env check, per-item ✓/✗ + detail | ✓ SATISFIED | Truth 1 (default screen intact through the WR rework; env_smoke + services byte-unchanged; boot + env-check lanes green) |
| ENV-02 | 08-04, 08-06 | Persisted results + check date + refresh; same-day cache | ✓ SATISFIED | Truth 2 (zh/en persist line live-read; IN-03 strengthens the refresh remount path, now test-pinned) |
| ENV-03 | 08-04, 08-06 | Critical FAIL blocks launch flow; missing data routes to data management | ✓ SATISFIED | Truth 3 (live disjointness re-run); Phase-11 wiring landed (deferral closed) |
| ENV-04 | 08-04, 08-06 | Quick-check re-validation of launch-required subset | ✓ SATISFIED | Truth 3 (7-id subset live) |
| SEL-01 | 08-07, 08-08, 08-09 | Browsable lists, k9s filter + mark sets, read-only matrix | ✓ SATISFIED | Truth 4 (60/50 live; selection-custom lane 45 green incl. the new IN-01 pin; matrix byte-unchanged) |
| SEL-02 | 08-05, 08-07 | Presets: tier-1 pair, tier-2 representatives, all, saved customs | ✓ SATISFIED | Truth 4/5 (live preset_menu: 3 derived + 3 customs, load_error None) |
| SEL-03 | 08-05, 08-07 | Template import/export with validation; sweep_priorities tier interop | ✓ SATISFIED | Truth 5 (templates service byte-unchanged; standing round-2 lane evidence) |
| SEL-04 | 08-04, 08-07 | Per-row local data presence (✓/✗ + n_audit rows) | ✓ SATISFIED | Truth 5 (presence maps flowing live, 16/60 split; n_audit.json byte-unchanged) |
| I18N-01 | 08-02, 08-03, 08-06, 08-07 | Chinese-primary copy via constants module, technical terms English | ✓ SATISFIED | strings.py byte-unchanged this delta (zero new strings confirmed by empty diff — the new WR/IN code adds zero user-facing constants); injectivity + re-derivation lanes green in the 25-lane; 0 CJK outside strings.py |

All 9 phase-mapped requirement IDs accounted for; REQUIREMENTS.md traceability lists exactly these for Phase 8, all Complete; no orphaned IDs.

### Decision Coverage

The five goal-named decisions re-confirmed this pass: textual-free services layer (17 modules, 0 imports — fresh AST scan; import-lock test green), `[tui]` dependency group (pyproject :71-79 exact, byte-unchanged), Pilot test harness (six lanes green this pass, 103 tests total), tolerant artifact loader (registry_loader byte-unmodified since 0559c40 + all four crash chains green), constants-module copy discipline (strings.py single CJK home, fresh grep). Later phases are still adding screens, not architecture — the invariant holds.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none blocking) | — | No TBD/FIXME/XXX anywhere in the five changed implementation files or three changed test files; the only TODO/HACK/PLACEHOLDER-pattern hits are pre-existing `placeholder=` Input attributes and the known NAV_PLACEHOLDER_TOAST | — | — |

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| tests/tui/test_pilot_env_check.py (+40) | ENV-01..04, IN-03 | full lane green (17) | 0 | 0 | Behavioral (recorder-based synchronous-flag pin; real app) | Sound — the new IN-03 test asserts flag state the instant action_refresh returns, before any worker runs |
| tests/tui/test_pilot_selection_custom.py (+35) | SEL-01..04, IN-01 | full lane green (45) | 0 | 0 | Behavioral (real app + backend; live-dict residue pin) | Sound — the IN-01 test asserts the dataset key never lands in either live dict |
| tests/tui/test_pilot_run_config.py (+293) | WR-01/02/03 + IN-02 evidence | 7 named green this pass | 0 | 0 | Behavioral (real key-press selection; raising-kill fan-out; mixed-root modal shape) | Sound — RED-first per the quick convention; the two adapted CDR-2 tests preserve every original assertion on the empty-selection form |
| Structural pin files (6) | Truth 6, foundation | 25 green | 0 | 0 | Structural (AST pins, non-vacuity floors) | Sound — work-site pin covers the NEW exit-kill worker with zero pin edits |

### Human Verification Required

None. Every truth is machine-evidenced by this verifier's own executions this pass (103 tests across six targeted invocations, fresh AST/grep scans, live service gates over the real backend). The riskiest new seams — the ctrl+c delegation (against the real 8.2.8 Input binding), the exit-kill worker's every-root-attempted guarantee (exercised on the raising path), and the mixed-root modal form — all have passing behavioral tests through the real app.

### Gaps Summary

No gaps. The third post-closeout micro-refresh trigger was the klw fix batch: the six 08-REVIEW findings (WR-01/02/03 exit-channel trio in app.py; IN-01/02/03 screen-hygiene trio) all landed RED-first with tests, and this pass adjudicated every resolution against the reviewer's own fix sketch with passing behavioral evidence — all six RESOLVED, the feedback-round advisories retired, and the disposition ledger's open set reduced to IN-04. The delta is otherwise surgical: zero new strings, zero SVG interaction, zero service-module changes, every prohibition file byte-unchanged. All six truths re-verified at HEAD 6bb768f (the three delta-touched screens with full behavioral lanes; the rest by zero-diff plus fresh structural/live gates): the default screen and worker protocol survive the exit rework, the T3 gates stay live-disjoint, the real backend still yields 60/50 with flowing presence and correct presets, the crash chains still pass through the real app, the services layer remains textual-free, and the i18n single-home lock holds. Phase 8 remains 6/6 — the console is trustworthy at rest, and later phases are still adding screens, not architecture.

---

_Verified: 2026-10-17T07:51:50Z (eighth pass, third post-closeout micro-refresh, at HEAD 6bb768f)_
_Verifier: Claude (gsd-verifier)_
