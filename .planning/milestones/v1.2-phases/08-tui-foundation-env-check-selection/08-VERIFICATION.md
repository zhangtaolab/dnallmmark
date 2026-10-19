---
phase: 08-tui-foundation-env-check-selection
verified: 2026-10-19T12:17:28Z
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
covered_digest: "v3:sha256:5e8dc7e0d408bf68f1ce231deed2da372f5841a7983e7bdbb001a0b7517b7113"
fingerprint_head: 578356793c632c05412982c497019a8054891409
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
    evidence: "CLOSED by its successor: Phase 11 landed the env preflight + E2' typed gate (e63a08d) and the launch gate screen — Phase 11 verification passed. Kept as the historical deferral record."
advisory:
  - finding: "Pin guard-granularity: the card-site pin's guard-presence check is per-FUNCTION — stripping ONE of build_wizard's two comprehension guards leaves the sibling's isinstance in the function and the pin stays green"
    category: other
    reason: "CARRIED unchanged: test_card_site_hardening.py byte-identical through this delta (absent from git diff 6bb768f..HEAD); residual covered behaviorally; wizard.py byte-unchanged."
    evidence_status: "none provided — unchanged this pass"
  - finding: "WR-02 (08-scope label): degraded dnallm_compat map renders a silent blank models table on slot 2 (no degraded-state row when the default pool yields zero entries)"
    category: architectural
    reason: "CARRIED: pipeline/dnallm_compat.json and tui/services/registries.py byte-unchanged this delta; live backend still returns 60/60 with load_error None on this box; post-phase scope, review-tracked."
    evidence_status: "none provided"
  - finding: "WR-03 (08-scope label): synchronous event-loop file reads (_render_storage, _submit_save→custom_names) contradict the module's own D-03 read-seam discipline"
    category: architectural
    reason: "CARRIED: the only selection.py delta this window is the 9-line 08g uppercase Y/N keycap twins in LaunchConfirmModal — the read seams are untouched; bounded local-file stalls; review-tracked open."
    evidence_status: "none provided"
  - finding: "Info-level residuals: env screen action_show_detail still lacks the is_valid_coordinate guard its selection-screen twins carry (env_check.py byte-unchanged this delta, so still true); IN-04 degenerate filter tokens open in the disposition ledger. The third prior sub-item (NAV_PLACEHOLDER_* zero-consumer) is RESOLVED — the nav shell now consumes NAV_PLACEHOLDER_SUFFIX (tui/screens/nav.py:191) and NAV_PLACEHOLDER_TOAST (tui/app.py:838); a stale 'ZERO consumers' comment survives at nav.py:74 (info-level, non-covered file)"
    category: other
    reason: "Info-level, post-phase scope, review-tracked; no Phase 8 must-have breach."
    evidence_status: "none provided"
  - finding: "klw Maintainer Items (carried): wizard keycap step-aware-visibility ruling pending; run_finetune sibling hard-index sites :849/:1077/:1322 raise the same KeyError class for schema-legal minimal entries on their code paths (07-scope, recorded in the klw SUMMARY)"
    category: other
    reason: "Explicitly recorded as NOT changed per the batch's non-goals; maintainer-ruled future batch. pipeline/run_finetune.py untouched in this window; no Phase 8 must-have breach."
    evidence_status: "none provided"
---

# Phase 8: TUI Foundation (Env Check & Selection) Verification Report

**Phase Goal:** The console exists and is trustworthy at rest — `make tui` opens a Textual app whose startup shows a persisted full environment-check panel, and operators build model×dataset selections k9s-style with presets, templates, and presence columns — with every non-retrofittable decision (textual-free services layer, `[tui]` dependency group, Pilot test harness, tolerant artifact loader, constants-module copy discipline) locked as ADRs
**Verified:** 2026-10-19T12:17:28Z
**Status:** passed
**Re-verification:** Yes — ninth pass (STALE REFRESH), at HEAD 578356793c632c05412982c497019a8054891409. The eighth pass verified 6/6 at HEAD 6bb768f (2026-10-17T07:51:50Z). The phase then went stale: quick tasks 261017-uwr → 261019-pe0 (plus mad, kvj, rze, toe, 08g, f0x, n0w, o8e, pe0, the golden-landing commits b84afc0/5783567, and the version bump) rebuilt slot-5 (`tui/screens/monitor.py` +4637 — B+D Running tab: strip/matrix/tree/wide modes, render gates, click=select) and added LauncherBackend delegations to `tui/screens/run_config.py` (+54), touching this phase's covered set. This pass re-ran the full Phase-8 evidence battery over the CURRENT tree — 455 tests across 7 invocations (all green, 0 failed) plus every static prohibition gate and both live service gates — and confirmed all six truths still hold. Full suite not run (dispatch instruction; the two documented environment notes are recorded below).

## Staleness Resolution (why the phase went stale and why the goal still holds)

`git diff 6bb768f..HEAD --stat` over the covered tree — the delta concentrates on Phase-11/12 surface riding inside Phase-8 covered files:

| File | Delta | Source quick tasks | Phase-8 impact — re-checked how |
| ---- | ----- | ------------------ | ------------------------------- |
| `tui/screens/monitor.py` (+4637) | slot-5 B+D Running tab rebuild: summary strip + matrix grid + group focus + [w] wide toggle + tree mode + render gates + click=select | uwr (context header/evidence threading), kvj (two-tab restructure), rze (five cadence render gates + sixth gate), toe ([d]/[e] history actions), f0x (B skeleton, D right pane, [w]), n0w (click=select, no-fill law), o8e (live-scope pair set), pe0 (tree state), 797b910/b84afc0/5783567 (fill kills + goldens) | Phase-11 substance; Phase-8 cross-tree invariants re-proven OVER it this pass: work-site @work never-exit pin (rglob over all of tui/, green — covers every new monitor @work site with zero pin edits), CJK single-home (0 hits outside strings.py), monitor Pilot lane 104 green, pty lane 13 green, goldens green |
| `tui/app.py` (+275) | mad (F10 any-focus exit, ctrl+c interception withdrawn → terminal-native semantics), 08g (F1 fresh MonitorScreen per nav, hoisted MonitorSession, f1/f2 help+language keys) | mad, 08g | Truth 1 wiring re-read at HEAD: `get_default_screen() → EnvCheckScreen(env_check_service=...)` intact (app.py:733-735); boot Pilot lane green (in the 81) |
| `tui/screens/run_config.py` (+54) | LauncherBackend delegations (62a5c61 `live_sweep_matrices` forward, 32be15d tee reattach) + 08g [m] hint | uwr-window, 08g | Phase-11 covered file; its Pilot lane re-run green this pass (in the 136) |
| `tui/screens/selection.py` (+9) | 08g F3: uppercase [Y]/[N] twins routing to the same actions, show=False | 08g | The filter/spacebar/preset/matrix surfaces untouched; selection-custom lane 45 green + full selection lane green (in the 81/136) |
| `tui/strings.py` (+249) | new constants-module entries for the slot-5/nav copy | f0x/n0w/o8e/pe0/toe/kvj | The constants-module discipline HELD under the heaviest copy growth since Phase 8: fresh grep — 0 CJK outside strings.py across tui/**.py and *.tcss; injectivity + rederivation + strings-phase11 pins green (in the 27; the pin file itself grew +161 to cover the new entries) |
| `tui/styles.tcss` (+151) + `tests/tui/__snapshots__/*` | slot-5 styles + monitor/run_config golden regeneration | f0x/n0w/pe0, b84afc0 | Snapshot goldens re-run green this pass (in the 94) — regenerated goldens are committed, not stale |
| `pyproject.toml` (2 lines) / `uv.lock` (2 lines) | version 0.7.1 → 1.2.0 only | effb5bf/0adac7a/565b338 | The `[tui]` group block re-read intact and byte-unchanged: textual>=8.2,<9 + platformdirs>=3.6,<5 + jsonschema>=4.26.0 (pyproject:71-79) |
| Test files: pilot_boot (+85), pilot_env_check (+20), pilot_selection (+14), pilot_run_config (+500), strings_phase11 (+161), monitor (+6314), pty_driver (+719 new), nav_shell, services_run_config, services_sweep_*, snapshots | later-phase lanes growing inside the shared harness | 08g → pe0 | All re-run green this pass (see Behavioral Spot-Checks) |
| **Zero-delta:** Makefile, n_audit.json, env_smoke.py, registry_loader.py, schemas/run_template.json, conftest.py, all six structural pin test files, pilot_selection_custom.py, pilot_matrix.py, env_check/matrix/wizard/data_manager/about screens, all seven Phase-8 services (env_check, env_gate, quick_check, registries, selection, settings, templates) | — | — | Confirmed by empty `git diff 6bb768f..HEAD` per file; every Phase-8 core surface is byte-identical to the eighth-pass-verified state. The only tui/services/ changes are the three Phase-11 modules (run_config, sweep_launcher, sweep_monitor) — not Phase-8 files |

**Why the goal holds:** the staleness was additive (a rebuilt slot-5 screen and launcher delegations inside shared files), not architectural. Every Phase-8 core surface — the env-check default screen and its service chain, the selection/matrix screens and their services, env_smoke kernels, the registries/overlay seam, the [tui] group, the make tui entry — is either byte-unchanged or verified green through its full behavioral lane on the current tree. The cross-tree invariants that the slot-5 rebuild could have breached (services purity, CJK single-home, @work never-exit, strings injectivity) were each re-proven directly over the new code this pass.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | SC1: `make tui` opens the console; startup runs the full environment check reusing env_smoke kernels; per-item ✓/✗ status with drill-down | ✓ VERIFIED | Makefile `tui` recipe unchanged (`uv run --group tui --group gpu python -m tui`, Makefile:209-210); `get_default_screen() → EnvCheckScreen(env_check_service=...)` intact through the mad/08g rework (app.py:733-735, read at HEAD); `pipeline/env_smoke.py` byte-unchanged since 6bb768f (0-line diff) with bytes goldens green in the 27; boot + env-check Pilot lanes green this pass (inside the 81) |
| 2 | SC2: Check results persist with visible 上次检查 date; same-day restarts read the cache; manual refresh re-checks | ✓ VERIFIED | `ENV_LAST_CHECK_LINE` registry entry live-read this pass: zh `"上次检查: {checked_at}"` / en `"Last check: {checked_at}"`; `r` binding + `action_refresh` + sync in-flight flag untouched (env_check.py byte-unchanged); env-check Pilot lane green in full (inside the 81) |
| 3 | SC3: Critical FAILs visibly block with reason; missing-dataset routes to data management; quick-check re-validates the launch-required subset | ✓ VERIFIED | Live this pass (verifier-executed over the real modules): CRITICAL {cuda, dnallm, matmul, numpy, peft, version_pins} ∩ ROUTING {model_dirs, dataset_dirs} = ∅ (disjoint=True); `QUICK_CHECK_KERNEL_IDS` = the same 7 ids as the eighth pass ({cuda, dataset_dirs, dnallm, model_dirs, numpy, peft, version_pins}, matmul excluded); env_gate.py + quick_check.py byte-unchanged. Phase-11 launch-flow wiring landed (e63a08d) — the historical deferral stays CLOSED |
| 4 | SC4: Model/dataset lists first-class selectable; k9s filter; spacebar marks on stable row_keys; presets; read-only matrix auxiliary view | ✓ VERIFIED | Live this pass: real `SelectionBackend().load_selection_data()` → 60 models / 50 datasets, both load errors None; `preset_menu()` live: tier-1 (plant-dnamamba-6mer + PlantHelixSeek), tier-2 (GENERanno-eukaryote-0.5b-base, PlantCAD2-Small-l24-d0768, Omni-DNA-700M), all (59 models × 50 tasks) + 3 customs (d1, demo-walkthrough, probe-preset), load_error None; selection-custom lane 45 green + full selection lane green (inside the 81/136); matrix.py byte-unchanged (read-only by absent bindings holds); the only selection.py delta is the 9-line 08g keycap twins — filter/mark/preset surfaces untouched |
| 5 | SC5: Presence columns; templates round-trip as validated JSON with sweep_priorities tier interop; i18n through the constants module; foundation invariants (services textual-free, `[tui]` isolation, Pilot green CPU-side) | ✓ VERIFIED | Live this pass: presence 50 entries + model_presence 60 entries (16 present / 44 missing — real filesystem state, matching the eighth pass); fresh AST scan: 0 textual imports across all 17 tui/services modules; fresh grep: 0 CJK outside tui/strings.py across tui/**.py and *.tcss — the +249-line strings growth from the slot-5 rebuild ALL went through the constants module, and the strings-phase11 pin file grew +161 lines to cover it; `[tui]` group exact and byte-unchanged (pyproject:71-79); import-lock + language-rederivation + strings-phase11 + snapshot-golden lanes green (inside the 27/94) |
| 6 | Goal-derived foundation invariant: tolerant artifact loading landed such that loader-accepted registry inputs degrade — the console never exits on them | ✓ VERIFIED | `git diff 0559c40..HEAD -- pipeline/registry_loader.py`: 0 lines (prohibition holds at the newer HEAD too); registry-failure / enter-drill-down / download-compat crash-chain tests green this pass (inside the 136 through the real app + real backend); card-site AST pin green; work-site @work never-exit pin green with ZERO pin edits — its rglob scan covers the rebuilt monitor.py's new @work sites (27 pins passed) |

**Score:** 6/6 truths verified (0 present, behavior-unverified)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | ENV-03/ENV-04 launch-flow wiring (historical record) | Phase 11 | CLOSED by Phase 11: env preflight + E2' typed gate landed (e63a08d), Phase 11 verification passed. Kept for the audit trail |

### Advisory (New Scope, Unevidenced)

Re-adjudicated this pass (re-verification ran, so the section is present). No NEW advisories: the slot-5 rebuild produced no unevidenced Phase-8 breach — every invariant it could have touched was re-proven with green tests this pass. Prior rows carry except where noted: row 4's NAV_PLACEHOLDER sub-item is RESOLVED (consumers now exist at nav.py:191 and app.py:838; a stale "ZERO consumers" comment survives at nav.py:74 — info-level, non-covered file). All rows stay advisory per the #3304 evidence gate (no deterministic evidence, no Phase-8 must-have breach).

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | Pin guard-granularity: guard-presence is checked per-FUNCTION, so one-of-two guard deletion inside build_wizard escapes the pin alone | other | pin file byte-unchanged through this delta; residual covered behaviorally by the w Pilot regression test (green in the 136) |
| 2 | WR-02 (08-scope label): degraded compat map renders a silent blank models table on slot 2 | architectural | dnallm_compat.json + registries service untouched this delta; live backend returns 60/60 errors None here; review-tracked, no deterministic evidence |
| 3 | WR-03 (08-scope label): synchronous event-loop file reads contradict the pinned D-03 read-seam discipline | architectural | selection.py delta touches only the LaunchConfirmModal keycaps; read seams unchanged; review-tracked |
| 4 | Info-level residuals: env action_show_detail coordinate guard absent (env_check.py byte-unchanged, still true); IN-04 degenerate filter tokens open; stale "ZERO consumers" comment at nav.py:74 | other | info-level, review-tracked; the NAV_PLACEHOLDER zero-consumer sub-item itself is now RESOLVED (consumers at nav.py:191 / app.py:838) |
| 5 | klw maintainer items: wizard keycap step-aware ruling pending; run_finetune sibling hard-indexes (:849/:1077/:1322) | other | deliberately not fixed per the batch's non-goals; run_finetune.py untouched this window; 07-scope, maintainer-ruled future batch |

### Required Artifacts

All implementation artifacts in the covered set exist and are substantive. Files changed since 6bb768f were verified at full depth this pass (diff read, behavioral lanes executed, cross-tree invariants re-proven); everything else is byte-identical to the eighth-pass-verified state (empty `git diff 6bb768f..HEAD` per file). The plans' must_haves use string-shaped lists that predate the verify.artifacts/verify.key-links verbs' dict shape, so Levels 1-4 were verified by direct read, execution, and the live gates.

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `tui/app.py` | composition root: default screen, exit chain | ✓ VERIFIED | Default-screen wiring read at HEAD (:733-735); boot lane green; F10-exit and withdrawn ctrl+c verified through their own +85 new boot tests (green) |
| `tui/screens/env_check.py` | env-check screen: worker, persist line, refresh, verdict | ✓ VERIFIED | Byte-unchanged since the eighth pass; full lane green (inside the 81) |
| `tui/screens/selection.py` | slot-2 selection screen + extraction-site guards | ✓ VERIFIED | Only delta = 08g keycap twins (read); card-site pin + crash chains + full custom lane green |
| `tui/screens/matrix.py` | read-only matrix auxiliary view | ✓ VERIFIED | Byte-unchanged; matrix Pilot lane green (inside the 81) |
| `tui/screens/monitor.py` | slot-5 (Phase-11 substance inside a covered file) | ✓ VERIFIED | Rebuilt B+D Running tab green under its own lane (104) + pty lane (13) + regenerated goldens (inside the 94); work-site pin covers its new @work sites |
| `tui/services/*` (17 modules) | textual-free services layer | ✓ VERIFIED | Fresh AST scan: 0 textual imports across all 17; the three changed services (run_config/sweep_launcher/sweep_monitor) are Phase-11 modules — also 0 textual imports |
| `tui/strings.py` | i18n single home | ✓ VERIFIED | +249 lines all through the constants module (0 CJK outside it); live registry read confirms the zh/en pair; pins green (grew +161 to cover new entries) |
| `pipeline/env_smoke.py` | structured kernels; fail-closed registry reads | ✓ VERIFIED | Byte-unchanged since 6bb768f; bytes goldens green (inside the 27) |
| `pipeline/registry_loader.py` | fail-loud contract BYTE-UNMODIFIED (prohibition) | ✓ VERIFIED | `git diff 0559c40..HEAD`: 0 lines — re-checked at the newer HEAD |
| `pyproject.toml` / `Makefile` / `uv.lock` | [tui] group exact; make tui recipe; lock | ✓ VERIFIED | Only delta = version string 0.7.1→1.2.0; `[tui]` block re-read intact (:71-79); Makefile recipe unchanged (:209-210) |
| Structural pin files (card-site, work-site, import-lock, rederivation, strings-phase11, env_smoke-bytes) | AST pins + tripwires | ✓ VERIFIED | 27 passed in 0.89s this pass (was 25 — strings pins grew with the new copy) |
| Pilot lanes (boot/env_check/selection/selection_custom/matrix/run_config/monitor) + pty driver | behavioral coverage over the changed screens | ✓ VERIFIED | 81 + 136 + 104 + 13 passed this pass |

### Key Link Verification

Verified manually (string-shaped plan lists predate the verbs' dict shape). Links whose files changed this delta were re-executed; the rest are byte-identical to the eighth-pass-verified state.

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `make tui` | `tui.app` | recipe → `uv run --group tui --group gpu python -m tui` | ✓ WIRED | Makefile unchanged; boot Pilot green |
| app startup | EnvCheckScreen | `get_default_screen()` | ✓ WIRED | app.py:733-735 at HEAD, through the mad/08g rework |
| `r` keypress | full re-check | `action_refresh` (+ synchronous in-flight flag) | ✓ WIRED | env_check.py byte-unchanged; sync-flag test green (inside the 81) |
| spacebar / SelectionBackend / presence / presets | mark set / registries / n_audit + filesystem / sweep_priorities + customs | unchanged seams | ✓ WIRED | Live this pass: 60/50 errors None, 16/60 present, presets tier-1(2)/tier-2(3)/all(59) + 3 customs, load_error None |
| Services layer | textual | must NOT import | ✓ WIRED (negative) | Fresh AST scan: 0 imports across 17 modules (incl. the three changed Phase-11 services) |
| i18n copy | constants module | strings.py only | ✓ WIRED (negative) | Fresh grep over tui/**.py + *.tcss: only strings.py carries CJK — held through the +249-line slot-5 copy growth |
| Loader prohibition | `pipeline/registry_loader.py` | must stay byte-unmodified since 0559c40 | ✓ WIRED (negative) | 0-line diff re-confirmed at HEAD 5783567 |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| model list | `model_entries` | overlay-merged registry | Yes — live 60, load_error None | ✓ FLOWING |
| dataset list | `dataset_entries` | committed registry | Yes — live 50, load_error None | ✓ FLOWING |
| presence | `presence` / `model_presence` | filesystem + n_audit + queue reconcile | Yes — live 50 + 60 entries, real 16-present/44-missing split | ✓ FLOWING |
| presets | `preset_menu()` | sweep_priorities.json + config-root customs | Yes — live tier-1(2)/tier-2(3)/all(59) + 3 customs, load_error None | ✓ FLOWING |
| env gate | CRITICAL/ROUTING/QUICK_CHECK_KERNEL_IDS | env_gate + quick_check over env_smoke kernels | Yes — live disjointness + same 7-id quick-check subset | ✓ FLOWING |

### Behavioral Spot-Checks

All executed by this verifier at HEAD 5783567 (fresh, this pass, via `.venv/bin/python -m pytest` — no `uv run`, no GPU, no state mutation beyond pytest's own tmpdirs). Full suite NOT run per dispatch instruction; the two documented environment notes are recorded beneath the table.

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Rebuilt slot-5 monitor (dispatch-mandated) | `.venv/bin/python -m pytest tests/tui/test_pilot_monitor.py -q` | `104 passed in 66.29s (0:01:06)` | ✓ PASS |
| pty driver lane (dispatch-mandated) | `.venv/bin/python -m pytest tests/tui/test_pty_driver.py -q` | `13 passed in 47.32s` — standalone run, NO timeout observed | ✓ PASS |
| Structural pins (work-site incl. the rebuilt monitor's new @work sites, card-site, import-lock, language-rederivation, strings-phase11, env_smoke bytes) | `.venv/bin/python -m pytest tests/tui/test_work_site_hardening.py tests/tui/test_card_site_hardening.py tests/tui/test_import_lock.py tests/tui/test_language_rederivation.py tests/tui/test_strings_phase11.py tests/test_env_smoke_bytes.py -q` | `27 passed in 0.89s` | ✓ PASS |
| Env-check + selection-custom + boot + matrix Pilot lanes | `.venv/bin/python -m pytest tests/tui/test_pilot_env_check.py tests/tui/test_pilot_selection_custom.py tests/tui/test_pilot_boot.py tests/tui/test_pilot_matrix.py -q` | `81 passed in 22.17s` | ✓ PASS |
| Selection (crash chains) + run_config (LauncherBackend delegations) Pilot lanes | `.venv/bin/python -m pytest tests/tui/test_pilot_selection.py tests/tui/test_pilot_run_config.py -q` | `136 passed in 90.57s (0:01:30)` (the two `exit-kill failed for /repo/a|b: OSError` lines are the expected per-root broad-guard log output of the raising-kill test, not failures) | ✓ PASS |
| Services registries/selection/templates + snapshot goldens | `.venv/bin/python -m pytest tests/tui/test_services_registries.py tests/tui/test_services_selection.py tests/tui/test_services_templates.py tests/tui/test_snapshots.py -q` | `94 passed in 6.36s` | ✓ PASS |
| Live T3 gates | `.venv/bin/python` over real env_gate/quick_check | disjoint=True; QUICK_CHECK = same 7 ids (matmul excluded) | ✓ PASS |
| Live selection backend + presets | `.venv/bin/python` `SelectionBackend().load_selection_data()` + `preset_menu()` | 60/50, errors None; presence 50 + model_presence 60 (16 present); presets tier-1(2)/tier-2(3)/all(59) + 3 customs (d1, demo-walkthrough, probe-preset), load_error None | ✓ PASS |
| ENV-02 persist line | live registry read of `ENV_LAST_CHECK_LINE` | zh `"上次检查: {checked_at}"` / en `"Last check: {checked_at}"` | ✓ PASS |
| Services textual-import lock | verifier AST scan over tui/services/*.py | 17 files, 0 textual imports | ✓ PASS |
| CJK single-home | `grep`-equivalent scan over tui/**.py + *.tcss | only tui/strings.py (0 hits elsewhere) | ✓ PASS |
| Loader prohibition | `git diff 0559c40..HEAD -- pipeline/registry_loader.py` | 0 lines | ✓ PASS |
| Zero-delta Phase-8 core surfaces | `git diff 6bb768f..HEAD --stat` per file | empty for Makefile, env_smoke.py, n_audit.json, schema, conftest, all 6 pin files, env_check/matrix/wizard/data_manager/about screens, all 7 Phase-8 services, pilot_selection_custom, pilot_matrix; pyproject delta = version string only | ✓ PASS |
| Debt markers | TBD/FIXME/XXX over all changed covered files (+ monitor/pty tests) | 0 unreferenced hits; TODO/HACK/PLACEHOLDER hits are only the known `S.*_PLACEHOLDER` Input-attribute constants and NAV_PLACEHOLDER_TOAST (app.py:838) | ✓ PASS |

**Environment notes (dispatch-provided, not re-triggered this pass):** (1) `test_storage_overview_defaults_mirror_real_consumers` (tests/tui/test_services_run_config.py — a Phase-11 services lane, NOT a Phase-8 covered lane) fails while `pipeline/logs` exists; documented collateral, out of Phase-8 scope, and not part of any Phase-8 truth's evidence chain. (2) The intermittent slot-4 pty TIMEOUT under heavy parallel load did not occur — the pty lane passed standalone in 47.32s.

### Probe Execution

No probes declared for this phase — not applicable.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| ENV-01 | 08-01, 08-03, 08-04, 08-06, 08-08 | Startup full env check, per-item ✓/✗ + detail | ✓ SATISFIED | Truth 1 (default screen intact at app.py:733-735; env_smoke + services byte-unchanged; boot + env-check lanes green) |
| ENV-02 | 08-04, 08-06 | Persisted results + check date + refresh; same-day cache | ✓ SATISFIED | Truth 2 (zh/en persist line live-read; env_check.py byte-unchanged) |
| ENV-03 | 08-04, 08-06 | Critical FAIL blocks launch flow; missing data routes to data management | ✓ SATISFIED | Truth 3 (live disjointness re-run); Phase-11 wiring landed (deferral closed) |
| ENV-04 | 08-04, 08-06 | Quick-check re-validation of launch-required subset | ✓ SATISFIED | Truth 3 (same 7-id subset live) |
| SEL-01 | 08-07, 08-08, 08-09 | Browsable lists, k9s filter + mark sets, read-only matrix | ✓ SATISFIED | Truth 4 (60/50 live; selection lanes green; matrix byte-unchanged) |
| SEL-02 | 08-05, 08-07 | Presets: tier-1 pair, tier-2 representatives, all, saved customs | ✓ SATISFIED | Truth 4/5 (live preset_menu: 3 derived + 3 customs, load_error None) |
| SEL-03 | 08-05, 08-07 | Template import/export with validation; sweep_priorities tier interop | ✓ SATISFIED | Truth 5 (templates service byte-unchanged; lane green) |
| SEL-04 | 08-04, 08-07 | Per-row local data presence (✓/✗ + n_audit rows) | ✓ SATISFIED | Truth 5 (presence maps flowing live, 16/60 split; n_audit.json byte-unchanged) |
| I18N-01 | 08-02, 08-03, 08-06, 08-07 | Chinese-primary copy via constants module, technical terms English | ✓ SATISFIED | Truth 5 (0 CJK outside strings.py through the +249-line copy growth; injectivity/rederivation/strings pins green) |

All 9 phase-mapped requirement IDs accounted for; no orphaned IDs.

### Decision Coverage

The five goal-named decisions re-confirmed this pass: textual-free services layer (17 modules, 0 imports — fresh AST scan; import-lock test green), `[tui]` dependency group (pyproject :71-79 exact, byte-unchanged through the version bump), Pilot test harness (seven lanes green this pass, 455 tests total), tolerant artifact loader (registry_loader byte-unmodified since 0559c40 + crash chains green through the real app), constants-module copy discipline (strings.py single CJK home through the largest copy growth since Phase 8, fresh grep). Later work is still adding screens, not architecture — the invariant held precisely where the slot-5 rebuild could have broken it.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none blocking) | — | No unreferenced TBD/FIXME/XXX in any changed covered file; TODO/HACK/PLACEHOLDER-pattern hits are pre-existing `placeholder=` Input attributes over constants-module strings and the now-consumed NAV_PLACEHOLDER_TOAST | — | — |
| tui/screens/nav.py | 74 | Stale comment claims NAV_PLACEHOLDER_* "retain ZERO consumers" while nav.py:191 and app.py:838 consume them | ℹ️ Info | Non-covered file (nav shell); comment staleness only, no behavior impact |

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| tests/tui/test_pilot_monitor.py (+6314 this delta) | Phase-11 slot-5 (attested for staleness) | 104 green this pass | 0 | 0 | Behavioral (real app; render-gate cadence assertions; pty-driven pins) | Sound — covers the rebuilt B+D Running tab |
| tests/tui/test_pty_driver.py (+719, new) | Phase-11 pty seam | 13 green this pass | 0 | 0 | Behavioral (real pty) | Sound |
| tests/tui/test_pilot_boot.py (+85) | Truth 1 + exit chain | green (inside the 81) | 0 | 0 | Behavioral (F10 exit, ctrl+c terminal-native) | Sound |
| tests/tui/test_pilot_selection.py / test_pilot_selection_custom.py | SEL-01..04, Truth 6 | green (inside the 81/136) | 0 | 0 | Behavioral (real app + backend; crash chains) | Sound |
| tests/tui/test_strings_phase11.py (+161) | I18N-01 | green (inside the 27) | 0 | 0 | Structural (injectivity/rederivation over the grown registry) | Sound — pins grew to cover the new slot-5 copy |

### Human Verification Required

None. Every truth is machine-evidenced by this verifier's own executions this pass (455 tests across seven targeted invocations, fresh AST/grep scans, live service gates over the real backend and real registries). The riskiest staleness seams — the rebuilt slot-5 monitor against the work-site @work pin and the CJK single-home gate, and the +249-line strings growth against the injectivity pins — all have passing behavioral/structural evidence on the current tree.

### Gaps Summary

No gaps. The stale-refresh trigger was the slot-5 rebuild riding inside Phase-8 covered files: quick tasks 261017-uwr → 261019-pe0 (uwr, mad, kvj, toe, rze, 08g, f0x, n0w, o8e, pe0 plus the golden-landing commits and the version bump) rewrote `tui/screens/monitor.py` (+4637), touched `tui/app.py` (+275), `tui/screens/run_config.py` (+54), `tui/screens/selection.py` (+9), `tui/strings.py` (+249), and `tui/styles.tcss` (+151) — every one of them Phase-11/12 substance inside shared files. The delta is additive, not architectural: every Phase-8 core surface (env-check screen/service chain, selection/matrix screens and services, env_smoke kernels, registry overlay seam, [tui] group, make tui entry, all pin files) is byte-identical to the eighth-pass-verified state except app.py, whose default-screen wiring survives read-at-HEAD and boot-lane-green. The cross-tree invariants the rebuild could have breached were each re-proven directly over the new code: services stay textual-free (17/17), all new copy flowed through the constants module (0 CJK outside strings.py, injectivity pins green and grown), the work-site @work never-exit pin covers the monitor's new sites with zero pin edits, the registry_loader prohibition holds at 0-line diff, and the live backend still yields 60/50 with flowing presence and correct presets while the T3 gates stay disjoint with the same 7-id quick-check subset. Phase 8 remains 6/6 at HEAD 5783567 — the console is trustworthy at rest, and later phases are still adding screens, not architecture.

---

_Verified: 2026-10-19T12:17:28Z (ninth pass, stale refresh, at HEAD 578356793c632c05412982c497019a8054891409)_
_Verifier: Claude (gsd-verifier)_
