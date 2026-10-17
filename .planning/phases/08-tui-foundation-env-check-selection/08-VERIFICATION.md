---
phase: 08-tui-foundation-env-check-selection
verified: 2026-10-17T04:58:05Z
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
  - tests/tui/test_pilot_selection.py
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
covered_digest: "v3:sha256:951520d5b0083190bf151685fcc3de7834609ca209d6a4392599da00a662be72"
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
    reason: "Implements the plan's own per-function wording exactly; the residual is covered behaviorally — the w Pilot regression test exercises BOTH comprehensions (re-run green this pass). tests/tui/test_card_site_hardening.py absent from the 1e29efc..HEAD delta (byte-unchanged since the mutation-proven pass)."
    evidence_status: "none provided — mutation-evidenced in the fourth pass's report; unchanged this pass"
  - finding: "WR-02 (08-scope label): degraded dnallm_compat map renders a silent blank models table on slot 2 (no degraded-state row when the default pool yields zero entries)"
    category: architectural
    reason: "CARRIED WITH CAVEAT: pipeline/dnallm_compat.json changed again this delta (dnallm v1.3 audit adoption, 2478cfc — PlantHelixSeek + FungiHelixSeek); no deterministic evidence either way this pass (no failing test, no reproducible defect). Distinct from the feedback-round WR-02 below. Post-phase scope, review-tracked."
    evidence_status: "none provided"
  - finding: "WR-03 (08-scope label): synchronous event-loop file reads (_render_storage, _submit_save→custom_names) contradict the module's own D-03 read-seam discipline"
    category: architectural
    reason: "CARRIED WITH CAVEAT: selection.py changed again this delta (poa +66); bounded local-file stalls, not a Phase 8 must-have breach; review-tracked open. Distinct from the feedback-round WR-03 below."
    evidence_status: "none provided"
  - finding: "Feedback-round review WR-01 (cdr): the ctrl+c any-focus intercept silently kills the focused-Input copy binding on every base screen"
    category: architectural
    reason: "NEW this delta (261017-cdr quick, reviewed at diff base 601aa51 — 08-REVIEW.md 0C/3W/3I). UX-polish defect in a post-phase exit affordance; open in 08-REVIEW-DISPOSITION.md; no Phase 8 must-have covers copy-in-input."
    evidence_status: "none provided"
  - finding: "Feedback-round review WR-02: ExitModal [k] runs kill_sweep serially on the event loop — up to kill_grace × N roots of frozen UI"
    category: architectural
    reason: "NEW this delta (vxr slot-5 k kill-confirm surface). Review-tracked open in the disposition ledger; bounded UI-freeze risk in a post-phase kill affordance, not a Phase 8 truth."
    evidence_status: "none provided"
  - finding: "Feedback-round review WR-03: mixed live-root exit drops the attached CLI-launched sweep from the ExitModal"
    category: architectural
    reason: "NEW this delta (v0z/cdr exit-chain surface). Review-tracked open; an exit-edge gap in post-phase affordances, not a Phase 8 truth."
    evidence_status: "none provided"
  - finding: "Info-level residuals: env screen action_show_detail still lacks the is_valid_coordinate guard its selection-screen twins carry (confirmed present-shaped at env_check.py:749-753 this pass); IN-01..IN-04 open in 08-REVIEW-DISPOSITION.md (IN-04 degenerate filter tokens carried from the hhx round); NAV_PLACEHOLDER_* constants documented as zero-consumer"
    category: other
    reason: "Info-level, post-phase scope, review-tracked (disposition ledger: CR-01 fixed in hhx/f9528e3; IN-01..04 + the three feedback-round warnings open); none breaches a Phase 8 must-have."
    evidence_status: "none provided"
---

# Phase 8: TUI Foundation (Env Check & Selection) Verification Report

**Phase Goal:** The console exists and is trustworthy at rest — `make tui` opens a Textual app whose startup shows a persisted full environment-check panel, and operators build model×dataset selections k9s-style with presets, templates, and presence columns — with every non-retrofittable decision (textual-free services layer, `[tui]` dependency group, Pilot test harness, tolerant artifact loader, constants-module i18n convention) landed so later phases add screens, not architecture
**Verified:** 2026-10-17T04:58:05Z
**Status:** passed
**Re-verification:** Yes — seventh pass (fourth stale-refresh), at HEAD 2212ee8. The sixth pass verified 6/6 at 1e29efc; 42 commits since touched the covered surface: the maintainer live-feedback quicks (poa picker anchor/contrast + launch-confirmation pair-list/Y/N/hint/启动确认 terminology, v0z quit-confirm chain on every exit path, vxr entry ETA + slot-5 k kill-confirm, cdr ctrl+c any-focus exit + P9 guard + bold Y/N, dnr confirm-family Y/N prominence + ExitModal keycaps), eea (pexpect into the dev group + data-chain regen — no tui/ code), the dnallm v1.3 compat adoption (2478cfc), and the D-03 golden SVG landing (f2a772a). This pass re-verified every truth against the CURRENT tree with the verifier's own executions: 250 tests green across five targeted lanes, two AST pins, live service gates over the real backend, and the full prohibition set. The feedback-round delta itself was separately code-reviewed (08-REVIEW.md at base 601aa51, 0C/3W/3I; disposition ledger records all open).

## Stale-Refresh Delta Analysis (why this pass exists)

`git diff 1e29efc..HEAD --stat` over the covered tree:

| File cluster | Delta | Phase-8 impact |
| ------------ | ----- | -------------- |
| `tui/app.py` (+241) | v0z quit-confirm chain, cdr ctrl+c any-focus exit + P9 guard, dnr keycaps | Truth 1 wiring re-verified live: `get_default_screen() → EnvCheckScreen` intact (app.py:636-638); QuitConfirmModal y-only confirm wired to `S.LNC_EXIT_CONFIRM` (:1111); boot Pilot lane re-run green (51) — the exit rework is covered by the updated boot tests |
| `tui/strings.py` (+152) | cdr/dnr confirm-family + keycap constants, poa launch-confirmation terminology | I18N-01 substance re-verified: bilingual `_t(zh, en)` registry intact, DEFAULT EN (EHC-1), keycap constants (LNC_EXIT_CONFIRM family, MON_KILL_CONFIRM) defined AND consumed (app.py:288-289/1111, monitor.py:564/1519, selection.py:1249); injectivity tripwires green in the 25-lane |
| `tui/screens/selection.py` (+66), `tui/screens/run_config.py`, `tui/screens/monitor.py` | poa slot-4 picker anchor/contrast + launch confirmation; vxr entry ETA + k kill-confirm (post-phase surfaces) | Truths 4/5/6 re-verified: selection Pilot lane 38 green; card-site AST pin green; crash chains re-run green |
| `tui/services/{run_config,sweep_launcher,sweep_monitor}.py` | vxr ETA/kill-confirm service tails | Services layer still textual-free across all 17 modules (verifier AST scan) — later-phase services keep riding the Phase 8 architecture |
| `tui/styles.tcss` (+27) | dnr keycap/bold styles | No copy impact; CJK single-home grep re-run clean |
| `pyproject.toml` (+9) | eea: `pexpect>=4.9` into the DEV group (the demo scene driver's static-import root cause) | [tui] group untouched and exact; CI lanes unaffected (pexpect rides dev) |
| `pipeline/dnallm_compat.json` (+22), `schemas/`, data chain | dnallm v1.3 audit adoption (PlantHelixSeek + FungiHelixSeek) + eea regen | Truth 5 live state shifted honestly: model_presence now 16 present / 60 (was 14 — two helix models now on disk); registries/presets flowing live, load errors None |
| `tests/tui/__snapshots__/{monitor_empty,monitor_running,run_config}.svg` | f2a772a: D-03-approved golden refresh landed | 9 goldens green this pass (snapshots lane inside the 49); directory clean after |
| `tests/tui/test_pilot_{boot,env_check,matrix,selection}.py`, `test_strings_phase11.py` | quick-matched test updates | All re-run green this pass |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | SC1: `make tui` opens the console; startup runs the full environment check reusing env_smoke kernels; per-item ✓/✗ status with drill-down | ✓ VERIFIED | Makefile:209-210 recipe (`uv run --group tui --group gpu python -m tui`); `get_default_screen() → EnvCheckScreen(env_check_service=...)` (app.py:636-638, read at HEAD); services import env_smoke kernels top-level (D-02 — no subprocess); live `len(ENV_KERNEL_LABELS) == 8` in main() order (version_pins, dnallm, peft, cuda, matmul, numpy, model_dirs, dataset_dirs); worker `@work(exclusive=True, thread=True, exit_on_error=False)` + post_message protocol + enter-drill-down wired (env_check.py:491-589, :749-757); boot/env-check/matrix Pilot lanes 51 passed this pass (verifier-executed); env_smoke bytes goldens green in the 25-lane; live env_smoke CLI: exit 1 honest with the SMOKE RESULT trailer (real machine state — 6 failed groups, all 50 dataset dirs PASS) |
| 2 | SC2: Check results persist with visible 上次检查 date; same-day restarts read the cache; manual refresh re-checks | ✓ VERIFIED | `ENV_LAST_CHECK_LINE` zh value `"上次检查: {checked_at}"` (strings.py:266-268, halfwidth colon, bilingual via `_t`); `Binding("r", "refresh", S.ENV_REFRESH_LABEL)` (env_check.py:329) with `action_refresh` (:688); services `load_cached` / `is_same_local_day` / `run_full_check` / `persist` present (services/env_check.py:81/:98/:126/:241); on_mount same-day path renders final states and starts zero kernels (documented contract :426-440); the guarded persist tail renders `ENV_LAST_CHECK_DEGRADED` on persist failure (:628-645); env-check Pilot lane green this pass |
| 3 | SC3: Critical FAILs visibly block with reason; missing-dataset routes to data management; quick-check re-validates the launch-required subset | ✓ VERIFIED | Live this pass (verifier-executed over the real modules): CRITICAL {cuda, dnallm, matmul, numpy, peft, version_pins} ∩ ROUTING {dataset_dirs, model_dirs} = ∅ (disjoint=True); `QUICK_CHECK_KERNEL_IDS` = 7 ids ⊂ the 8 kernel labels (subset=True, matmul excluded); screen consumes `env_gate.gate_verdict(results)` for the verdict block (env_check.py:643); quick-check never persists (service contract). Phase-11 launch-flow wiring landed (e63a08d) — the historical deferral stays CLOSED |
| 4 | SC4: Model/dataset lists first-class selectable; k9s filter; spacebar marks on stable row_keys; presets; read-only matrix auxiliary view | ✓ VERIFIED | Live this pass: real `SelectionBackend().load_selection_data()` → 60 models / 50 datasets, both load errors None; full selection Pilot lane green (38 selection tests inside the 49-test run, verifier-executed); spacebar `toggle_mark` + in-place `update_cell` mark column (selection.py:1345, :1822, :1851); matrix screen defines ONLY escape/enter bindings (matrix.py:150-151 — read-only by absent bindings holds at HEAD); the 08-07 `m`-toggle shape was superseded post-phase by the maintainer-directed c4j slot-2/slot-3 split (slot 2 models, slot 3 datasets) — both lists remain first-class browsable surfaces with the active-table kind switch (selection.py:638), which strengthens the SEL-01 substance |
| 5 | SC5: Presence columns; templates round-trip as validated JSON with sweep_priorities tier interop; i18n through the constants module; foundation invariants (services textual-free, `[tui]` isolation, Pilot green CPU-side) | ✓ VERIFIED | Live this pass: presence map 50 entries + model_presence 60 entries (16 present / 60 — real filesystem state flowing through the dnallm v1.3 + eea shifts, not static); preset_menu: tier-1 (2 models/1 task), tier-2 (3/0), all (59/50) + 3 saved customs (d1, demo-walkthrough, probe-preset), load_error None; tier-1 services lanes 121 passed in 0.12s (templates/selection/env_gate/quick_check/registries/env_check/settings — verifier-executed); 0 textual imports across all 17 tui/services modules (verifier's AST scan); 0 CJK outside tui/strings.py across tui/ (grep gate); [tui] group exact (textual>=8.2,<9 + platformdirs>=3.6,<5 + jsonschema>=4.26.0 per the 08-07 handoff; textual 8.2.8 installed; textual-dev/serve appear only in the never-enter comments; CI workflow 0 textual hits; `make test` = `--group dev --group tui` per D-01); i18n CURRENT cumulative substance (EHC-1 + hhx + cdr/dnr): bilingual `_t(zh, en)` registry, DEFAULT EN, live `set_language` rebind through globals(), cdr/dnr confirm-modal keycap constants defined and consumed, bidirectional injectivity tripwires + render-time re-derivation pins green (inside the 25-lane this pass); 9 golden SVGs green (snapshots lane), directory clean after |
| 6 | Goal-derived foundation invariant: tolerant artifact loading landed such that loader-accepted registry inputs degrade — the console never exits on them | ✓ VERIFIED | The four named 08-09 crash-chain tests green this pass (verifier-executed: w-survives/enter-degraded-row/d-degraded-row/manual_landing_path — 4 passed in 2.74s through the REAL app + REAL backend); card-site AST pin + work-site @work never-exit pin green this pass; env_smoke fail-closed guards unchanged (env_smoke.py absent from the 1e29efc..HEAD delta; bytes goldens green in the 25-lane); `git diff 0559c40..HEAD -- pipeline/registry_loader.py`: 0 lines (prohibition holds) |

**Score:** 6/6 truths verified (0 present, behavior-unverified)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | ENV-03/ENV-04 launch-flow wiring (historical record) | Phase 11 | CLOSED by Phase 11: env preflight + E2' typed gate landed (e63a08d), Phase 11 verification passed. Kept for the audit trail |

### Advisory (New Scope, Unevidenced)

Carried forward from the sixth pass (rows 1-3, 7) plus the three NEW feedback-round review warnings (rows 4-6) — the entire quick delta was code-reviewed at diff base 601aa51 (08-REVIEW.md, 0C/3W/3I) and every warning is disposition-open; none has deterministic evidence (no failing test, no reproducible defect command) and none breaches a Phase 8 must-have, so all stay advisory per the #3304 evidence gate.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | Pin guard-granularity: guard-presence is checked per-FUNCTION, so one-of-two guard deletion inside build_wizard escapes the pin alone | other | Plan implements its own per-function wording; the w Pilot regression test (re-run green this pass) exercises both comprehensions; pin file byte-unchanged through this delta |
| 2 | WR-02 (08-scope label): degraded compat map renders a silent blank models table on slot 2 | architectural | post-phase scope, review-tracked; dnallm_compat.json changed again this delta (v1.3 adoption), no deterministic evidence this pass |
| 3 | WR-03 (08-scope label): synchronous event-loop file reads contradict the pinned D-03 read-seam discipline | architectural | post-phase scope, bounded stall, review-tracked; selection.py changed again (poa), no deterministic evidence this pass |
| 4 | Feedback-round WR-01: ctrl+c intercept kills the focused-Input copy binding on base screens | architectural | NEW (cdr quick); UX defect in a post-phase exit affordance; disposition-open; no Phase 8 truth covers copy-in-input |
| 5 | Feedback-round WR-02: ExitModal [k] kill_sweep runs serially on the event loop | architectural | NEW (vxr kill surface); bounded UI-freeze risk; disposition-open; not a Phase 8 truth |
| 6 | Feedback-round WR-03: mixed live-root exit drops the attached CLI-launched sweep from ExitModal | architectural | NEW (v0z/cdr exit chain); exit-edge gap; disposition-open; not a Phase 8 truth |
| 7 | Info-level residuals: env action_show_detail coordinate guard absent (:749-753, confirmed this pass), IN-01..04 open in the disposition ledger, NAV_PLACEHOLDER_* dead constants | other | info-level, review-tracked; no must-have breach |

### Required Artifacts

All 37 implementation artifacts in the covered set exist and are substantive (existence sweep this pass; strings.py 1823 lines, app.py 1252, selection.py 2365). The plans' must_haves use string-shaped lists that predate the verify.artifacts/verify.key-links verbs' dict shape (the verbs return "invalid"/0-input for this plan generation), so Levels 1-4 were verified by direct read, execution, and the live gates below.

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `pipeline/env_smoke.py` | structured kernels; fail-closed registry reads; byte-stable CLI | ✓ VERIFIED | Absent from the 1e29efc..HEAD delta (unchanged); bytes goldens green in the 25-lane; live CLI exit-1 honest with trailer |
| `tui/screens/env_check.py` | env-check screen: worker, persist line, refresh, verdict | ✓ VERIFIED | Read at HEAD: worker :491, r binding :329, persist tail :628-645, gate_verdict :643; Pilot lane green |
| `tui/screens/selection.py` | slot-2 selection screen + the three extraction-site guards | ✓ VERIFIED | Guards re-proven structurally (card-site AST pin green) + behaviorally (4 named tests green) through the poa delta |
| `tui/screens/matrix.py` | read-only matrix overview | ✓ VERIFIED | Only escape/enter bindings (:150-151); matrix lane green |
| `tui/services/*` (17 modules) | textual-free services layer | ✓ VERIFIED | AST scan: 0 textual imports across all 17; import-lock test green in the 25-lane |
| `tui/strings.py` | i18n single home: bilingual registry + keycaps | ✓ VERIFIED | Only CJK-bearing file in tui/; keycap constants consumed at 4+ sites; injectivity + re-derivation lanes green |
| `tui/app.py` / `tui/__main__.py` | composition root + sys.path bootstrap | ✓ VERIFIED | Default screen :636-638; REPO_ROOT from `__file__`; exit chain (v0z/cdr) wired and boot-tested |
| `pyproject.toml` | [tui] group exact; dev-group pexpect (eea) | ✓ VERIFIED | [tui] = textual/platformdirs/jsonschema (:71-79); pexpect>=4.9 in dev (:50) — documented demo-driver root cause, no ty masking |
| `Makefile` | `make tui` + `make test` lanes | ✓ VERIFIED | :209-210 tui recipe; :101-103 test = dev+tui (D-01) |
| `tests/tui/test_pilot_selection.py` | w/enter/d real-app Pilot trio + unit pin | ✓ VERIFIED | 38 tests green in the 49-lane; four named tests green individually |
| `tests/tui/test_card_site_hardening.py` + `test_work_site_hardening.py` + `test_import_lock.py` + `test_language_rederivation.py` + `test_strings_phase11.py` + `tests/test_env_smoke_bytes.py` | structural/behavioral pins | ✓ VERIFIED | 25-lane green this pass (0.99s) |
| `pipeline/registry_loader.py` | fail-loud contract BYTE-UNMODIFIED (prohibition) | ✓ VERIFIED | `git diff 0559c40..HEAD` over the file: 0 lines |

### Key Link Verification

Verified manually (string-shaped plan lists predate the verbs' dict shape — see Required Artifacts note).

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `make tui` | `tui.app` | recipe → `uv run --group tui --group gpu python -m tui` | ✓ WIRED | Makefile:209-210; boot Pilot green this pass |
| app startup | EnvCheckScreen | `get_default_screen()` | ✓ WIRED | app.py:636-638 at HEAD, through the v0z/cdr exit rework |
| env worker | UI rows | `@work(thread=True)` + post_message | ✓ WIRED | env_check.py:491-589; env-check Pilot lane green |
| `r` keypress | full re-check | `action_refresh` | ✓ WIRED | env_check.py:329/:688 |
| spacebar | mark set | `toggle_mark` → `update_cell` on stable row keys | ✓ WIRED | selection.py:1345/:1822/:1851; selection lane green |
| SelectionBackend | registries services | `load_selection_data` → isinstance-guarded projections | ✓ WIRED | Live 60/50, errors None |
| presence column | committed n_audit + filesystem | presence / model_presence maps | ✓ WIRED | Live 50 + 60 entries, real 16/60 split |
| presets | `sweep_priorities.json` + config-root customs | `preset_menu()` | ✓ WIRED | Live: 3 derived + 3 customs, zero unknowns, load_error None |
| Services layer | textual | must NOT import | ✓ WIRED (negative) | 0 imports across 17 modules (AST scan + lock test) |
| i18n copy | constants module | strings.py only | ✓ WIRED (negative) | 0 CJK outside strings.py across tui/ (py + tcss) |
| confirm keycaps (cdr/dnr) | app/monitor/selection modals | `S.LNC_EXIT_CONFIRM*` / `S.MON_KILL_CONFIRM` | ✓ WIRED | app.py:288-289/:1111, monitor.py:564/:1519, selection.py:1249 |
| L language toggle | live re-derivation | `set_language` → globals() rebind → render-time `S.*` | ✓ WIRED | Toggle Pilot pin green in the 25-lane |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| model list | `model_entries` | overlay-merged registry | Yes — live 60, load_error None | ✓ FLOWING |
| dataset list | `dataset_entries` | committed registry | Yes — live 50, load_error None | ✓ FLOWING |
| presence | `presence` / `model_presence` | filesystem + n_audit + queue reconcile | Yes — live 50 + 60 entries, real 16-present/60 split (moved 14→16 with the v1.3/eea machine state — live, not static) | ✓ FLOWING |
| presets | `preset_menu()` | pipeline/sweep_priorities.json + config-root customs | Yes — tier-1(2/1)/tier-2(3/0)/all(59/50) + 3 customs, zero unknown keys | ✓ FLOWING |
| env gate | `CRITICAL`/`ROUTING`/`QUICK_CHECK_KERNEL_IDS` | env_gate + quick_check over env_smoke kernels | Yes — live disjointness + 7⊂8 subset | ✓ FLOWING |
| env check rows | `run_full_check()` | imported env_smoke kernels (main() order) | Yes — live CLI run exit-1 honest with trailer | ✓ FLOWING |

### Behavioral Spot-Checks

All executed by this verifier at HEAD 2212ee8 (fresh, this pass; working tree clean except .planning state files). Full-suite evidence (1 failed / 1858 passed — the single machine-local member; node 26/26; ruff + ty green; CI four lanes green, PR #7 run 38997386977; make data idempotent) was provided by the dispatching context on this exact tree and was NOT re-run per instruction.

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| i18n re-derivation + both AST pins + import lock + injectivity tripwires + env_smoke bytes | `pytest tests/tui/test_language_rederivation.py tests/tui/test_card_site_hardening.py tests/tui/test_work_site_hardening.py tests/tui/test_import_lock.py tests/tui/test_strings_phase11.py tests/test_env_smoke_bytes.py -q` | 25 passed in 0.99s | ✓ PASS |
| Crash chains w/enter/d + unit pin (08-09) | `pytest tests/tui/test_pilot_selection.py::<4 exact names>` | 4 passed in 2.74s | ✓ PASS |
| Tier-1 services lanes (templates/selection/gate/quick-check/registries/env-check/settings) | `pytest tests/tui/test_services_{...}.py -q` | 121 passed in 0.12s | ✓ PASS |
| Boot / env-check / matrix Pilot lanes (exit-rework-covered) | `pytest tests/tui/test_pilot_{boot,env_check,matrix}.py -q` | 51 passed in 12.04s | ✓ PASS |
| Full selection Pilot lane + SVG goldens | `pytest tests/tui/test_pilot_selection.py tests/tui/test_snapshots.py -q` | 49 passed in 31.33s; snapshots dir clean after | ✓ PASS |
| Live T3 gates | `uv run --group dev --group tui python` over real env_gate/quick_check/strings | disjoint=True; 7 ids ⊂ 8 labels; kernel order correct | ✓ PASS |
| Live selection backend + presets | `SelectionBackend().load_selection_data()` + `preset_menu()` | 60/50, errors None, presence 50 + model_presence 60 (16/60), presets correct + 3 customs | ✓ PASS |
| Live env_smoke CLI | `uv run --group dev python pipeline/env_smoke.py` | exit 1, trailer present (honest 6-group FAIL; all 50 dataset dirs PASS) | ✓ PASS |
| Services textual-import lock | verifier AST scan over tui/services/*.py | 17 files, 0 textual imports | ✓ PASS |
| CJK single-home | `grep -rlPn "[\x{4e00}-\x{9fff}]" tui/` | only tui/strings.py | ✓ PASS |
| Loader prohibition | `git diff 0559c40..HEAD -- pipeline/registry_loader.py` | 0 lines | ✓ PASS |
| CI isolation + [tui] exactness | grep ci.yml / pyproject / installed version | CI 0 textual hits; [tui] exact (textual 8.2.8, platformdirs, jsonschema); textual-dev/serve comment-only; uv.lock 0 | ✓ PASS |
| Debt markers | TBD/FIXME/XXX/TODO over tui/, pipeline/env_smoke.py, tests/tui/ | 0 hits | ✓ PASS |

### Probe Execution

No probes declared for this phase — not applicable.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| ENV-01 | 08-01, 08-03, 08-04, 08-06, 08-08 | Startup full env check, per-item ✓/✗ + detail | ✓ SATISFIED | Truth 1 (8 kernel rows in main() order, drill-down, live CLI, bytes goldens) |
| ENV-02 | 08-04, 08-06 | Persisted results + check date + refresh; same-day cache | ✓ SATISFIED | Truth 2 (上次检查 line, r binding, cache semantics, guarded persist tail) |
| ENV-03 | 08-04, 08-06 | Critical FAIL blocks launch flow; missing data routes to data management | ✓ SATISFIED | Truth 3; Phase-11 wiring landed (deferral closed) |
| ENV-04 | 08-04, 08-06 | Quick-check re-validation of launch-required subset | ✓ SATISFIED | Truth 3 (7-id subset ⊂ 8 kernels, live) |
| SEL-01 | 08-07, 08-08, 08-09 | Browsable lists, k9s filter + mark sets, read-only matrix | ✓ SATISFIED | Truth 4 (60/50 live; 38-test lane; matrix read-only by absent bindings; slot-2/3 split preserves and strengthens both-lists-first-class) |
| SEL-02 | 08-05, 08-07 | Presets: tier-1 pair, tier-2 representatives, all, saved customs | ✓ SATISFIED | Truth 4/5 (live: 3 derived + 3 customs, zero unknowns, load_error None) |
| SEL-03 | 08-05, 08-07 | Template import/export with validation; sweep_priorities tier interop | ✓ SATISFIED | Truth 5 (templates lane green in the 121; presets flowing from sweep_priorities.json) |
| SEL-04 | 08-04, 08-07 | Per-row local data presence (✓/✗ + n_audit rows) | ✓ SATISFIED | Truth 5 (presence maps flowing live, real 16/60 split; n_audit.json byte-unchanged this delta) |
| I18N-01 | 08-02, 08-03, 08-06, 08-07 | Chinese-primary copy via constants module, technical terms English | ✓ SATISFIED | Verified against the CURRENT cumulative substance per the maintainer's EHC-1 ruling + hhx CR-01 fix + cdr/dnr keycap layer: bilingual registry with FULL zh copy (terminology-table governed), DEFAULT EN, live L toggle with render-time re-derivation, confirm-modal keycaps bilingual and consumed; constants-module convention unchanged — 0 CJK outside strings.py, technical terms English in both languages; injectivity tripwires + re-derivation pins green this pass. The default-language shift (zh-primary → en-default, zh one keypress away) is the documented maintainer ruling encoded in the strings.py contract, not a regression |

All 9 phase-mapped requirement IDs accounted for; REQUIREMENTS.md traceability lists exactly these for Phase 8, all Complete; no orphaned IDs.

### Decision Coverage

08-CONTEXT.md's `<decisions>` block records the non-retrofittable decisions (D-01 CI textual lane, D-02 kernel reuse, D-04 XDG split, D-05 cache idempotency, D-06 presets, D-07 template schema, D-08 presence, D-09 gate/quick-check, D-10 [tui] group); the `check.decision-coverage-verify` verb skipped this pass (argument-shape), so the five goal-named decisions were verified directly: textual-free services layer (17 modules, 0 imports, lock test), `[tui]` dependency group (pyproject :71-79 exact), Pilot test harness (five lanes green this pass), tolerant artifact loader (registry_loader byte-unmodified + crash chains green), constants-module copy discipline (strings.py single CJK home). Later phases added screens, not architecture — the invariant holds.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none blocking) | — | No TBD/FIXME/XXX/TODO anywhere in the covered tree | — | — |

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| tests/tui/test_language_rederivation.py | I18N-01 | 4+ | 0 | 0 | Behavioral (AST structural + L-toggle Pilot + positive control) | Sound |
| tests/tui/test_strings_phase11.py | I18N-01 | injectivity tripwires | 0 | 0 | Value (bidirectional key↔copy) | Sound — updated for the cdr/dnr constants |
| tests/tui/test_pilot_selection.py | SEL-01..04, Truth 6 | 38 | 0 | 0 | Behavioral (real-app Pilot, real backend, overlay injection) | Sound |
| tests/tui/test_card_site_hardening.py + test_work_site_hardening.py + test_import_lock.py | Truth 6, foundation | structural | 0 | 0 | Structural (AST pins, non-vacuity floors, positive controls) | Sound — byte-unchanged this delta |
| tests/tui/test_pilot_boot/env_check/matrix.py | ENV-01/02, SC1 | 51 | 0 | 0 | Behavioral (Pilot; boot lane covers the v0z/cdr exit chain) | Sound |
| tests/tui/test_services_*.py (7 lanes) | ENV-02..04, SEL-02..04 | 121 | 0 | 0 | Value/behavioral (real registries, injected fakes per D-03) | Sound — no disabled tests, goldens regenerated only by the maintainer-only Makefile script |

### Human Verification Required

None. Every truth is machine-evidenced by this verifier's own executions this pass (250 tests across five lanes, two AST pins, live service gates over the real backend, live CLI run). The exit-chain rework (v0z/cdr) and keycap layer (dnr) — the riskiest new seams in this delta — are covered by the boot Pilot lane and the strings injectivity + re-derivation lanes, all re-run green this pass.

### Gaps Summary

No gaps. The fourth stale-refresh trigger was the maintainer live-feedback round: six quicks (poa/v0z/vxr/cdr/dnr/eea) plus the dnallm v1.3 compat adoption and the D-03 golden landing rewrote the exit chain, confirm-family copy, and monitor/run-config surfaces after the sixth pass — app.py alone churned +241 lines. At HEAD 2212ee8 this verifier re-established every truth with fresh evidence: the default screen and worker protocol survive the exit rework; the T3 gates are live-disjoint with the quick-check subset intact; the real backend yields 60/50 with flowing presence (the split honestly moved 14→16 present with the v1.3/eea machine state) and correct preset derivation; all three tolerant-loading crash chains re-executed green through the real app; both structural AST pins pass; the services layer remains textual-free across all 17 modules; the i18n single-home lock holds at zero CJK outside strings.py with the current substance (bilingual registry, default en per EHC-1, live L toggle, cdr/dnr keycaps consumed) pinned green; every prohibition holds (loader byte-unmodified, CI textual-free, [tui] exact at textual 8.2.8, textual-dev/serve comment-only, snapshots clean). The feedback-round delta carries its own scoped review (0C/3W/3I, all disposition-open) — recorded as advisories here, none breaching a Phase 8 must-have. Phase 8 remains 6/6: the console is trustworthy at rest, and later phases are still adding screens, not architecture.

---

_Verified: 2026-10-17T04:58:05Z (seventh pass, fourth stale-refresh, at HEAD 2212ee8)_
_Verifier: Claude (gsd-verifier)_
