---
phase: 08-tui-foundation-env-check-selection
verified: 2026-10-16T06:52:14Z
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
covered_digest: "v3:sha256:4f15a85b8036a27b96341d999959601997a2c9dfa637a61c72e996126b72cba4"
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
    reason: "Implements the plan's own per-function wording exactly; the residual is covered behaviorally — the w Pilot regression test exercises BOTH comprehensions (re-run green this pass inside the 4-named-test run). test_card_site_hardening.py byte-unchanged since the mutation-proven pass (absent from the 646bcd5..HEAD delta)."
    evidence_status: "none provided — mutation-evidenced in the fourth pass's report; unchanged this pass"
  - finding: "WR-02 (08-scope label): degraded dnallm_compat map renders a silent blank models table on slot 2 (no degraded-state row when the default pool yields zero entries)"
    category: architectural
    reason: "CARRIED WITH CAVEAT: selection.py and data_manager.py both changed heavily since d9b96b5/646bcd5 (quick-261015-c4j slot rework + hhx i18n), so the old byte-unchanged premise no longer holds; no deterministic evidence either way this pass (no failing test, no reproducible defect). The scoped 601aa51 review examined the c4j+ehc delta and its own WR-02 finding was FIXED in 190d1c4. Post-phase scope, review-tracked."
    evidence_status: "none provided"
  - finding: "WR-03 (08-scope label): new synchronous event-loop file reads (_render_storage, _submit_save→custom_names) contradict the module's own D-03 read-seam discipline"
    category: architectural
    reason: "CARRIED WITH CAVEAT: same file-change caveat as the WR-02 row (c4j/hhx touched the surfaces); bounded local-file stalls, not a Phase 8 must-have breach; review-tracked open. (Distinct from the phase-11 monitor WR-03 label, whose hhx namesake was FIXED.)"
    evidence_status: "none provided"
  - finding: "Info-level residuals: env screen action_show_detail still lacks the is_valid_coordinate guard its selection-screen twins carry (confirmed literally present-shaped at env_check.py:749-753 this pass); matrix Header() chrome inconsistency; IN-04 degenerate filter tokens (=x, type=) — open in 08-REVIEW-DISPOSITION.md; NAV_PLACEHOLDER_* constants documented as zero-consumer (nav.py:74)"
    category: other
    reason: "Info-level, post-phase scope, review-tracked (disposition ledger: 7/8 findings FIXED in quick-261016-hhx, IN-04 open); none breaches a Phase 8 must-have."
    evidence_status: "none provided"
---

# Phase 8: TUI Foundation (Env Check & Selection) Verification Report

**Phase Goal:** The console exists and is trustworthy at rest — `make tui` opens a Textual app whose startup shows a persisted full environment-check panel, and operators build model×dataset selections k9s-style with presets, templates, and presence columns — with every non-retrofittable decision (textual-free services layer, `[tui]` dependency group, Pilot test harness, tolerant artifact loader, constants-module i18n convention) landed so later phases add screens, not architecture
**Verified:** 2026-10-16T06:52:14Z
**Status:** passed
**Re-verification:** Yes — sixth pass (third stale-refresh), at HEAD 1e29efc. The fifth pass verified 6/6 at 646bcd5 and committed as b328d07; 42 commits since touched the covered surface heavily: the c4j three-screen slot rework, the ehc bilingual-registry conversion (strings.py rewritten around a `_t(zh, en)` registry with live `set_language`, EHC-1 maintainer ruling default-English), the D-03-approved SVG golden refresh (d5cb44b — the xfail markers dropped, goldens committed), the a4f env_smoke/env-screen fail-closed fixes (f64e764/7217ca1), and the hhx render-time i18n fix wave (f9528e3/190d1c4/723e046, closing the scoped-review CR-01). This pass re-verified every truth against the CURRENT tree with the verifier's own executions: 232 tests green across seven targeted lanes, two AST pins, four live service checks, and the full prohibition set.

## Stale-Refresh Delta Analysis (why this pass exists)

`git diff 646bcd5..HEAD --stat` over the covered tree — the changed implementation surface and its Phase-8 truth impact:

| File cluster | Delta | Phase-8 impact |
| ------------ | ----- | -------------- |
| `tui/strings.py` (+1738 lines churn) | ehc bilingual registry rewrite + hhx fixes | I18N-01 substance SHIFTED by maintainer ruling EHC-1 (2026-10-15): bilingual registry, DEFAULT EN, live L toggle; single-home lock re-verified (0 CJK outside strings.py) and re-derivation behavior re-pinned by the NEW tests/tui/test_language_rederivation.py |
| `tui/screens/env_check.py` (+267) | a4f guarded persist tail + honest unreadable-registry routing + hhx render-time strings | Truths 1/2 wiring re-verified live: worker `@work(exclusive=True, thread=True, exit_on_error=False)`, post_message protocol, `r` refresh binding, ENV_LAST_CHECK_LINE/DEGRADED render path |
| `pipeline/env_smoke.py` + `tests/test_env_smoke_bytes.py` | a4f WR-01/WR-02 fail-closed registry reads (non-dict top level, empty Model_path) | Truth 6 / SC1 substrate: guards confirmed at :463/:472/:520/:588; healthy-path goldens green (suite evidence + my bytes-lane spot runs) |
| `tui/screens/selection.py` (+530) | c4j slot rework + hhx i18n | Truths 4/5/6 re-verified: the three extraction guards enforced by the green card-site AST pin; render-time `S.*` reads (selection.py:865 comment documents the L-toggle invariant) |
| `tui/app.py` (+242), `tui/__main__.py`, `tui/styles.tcss`, screens (about/data_manager/matrix/monitor/nav/run_config/wizard), services (download_queue/settings/sweep_*) | c4j/ehc/hhx waves | Default-screen wiring re-verified (`get_default_screen() → EnvCheckScreen`, app.py:507-509); matrix read-only re-verified; later-phase surfaces ride the same Phase-8 architecture (services textual-free across all 17 modules) |
| `Makefile` (+5), `pyproject.toml` (+8), `uv.lock` (+181) | modelscope data-group entry + demo lanes + [tui] jsonschema (08-07 handoff) | Truth 5 invariants re-verified: `make tui` recipe intact, [tui] group exact, CI textual-free, textual 8.2.8 |
| `tests/tui/__snapshots__/*.svg` | d5cb44b: D-03-approved golden refresh, xfail markers dropped | Resolves the 08-08/08-09 prohibition's own pending condition (maintainer review) — goldens now committed and green; zh-pin byte-identical through the hhx fix by design |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | SC1: `make tui` opens the console; startup runs the full environment check reusing env_smoke kernels; per-item ✓/✗ status with drill-down | ✓ VERIFIED | Makefile:209-210 recipe (`uv run --group tui --group gpu python -m tui`); `get_default_screen() → EnvCheckScreen(env_check_service=...)` (app.py:507-509, read at HEAD); services import env_smoke kernels top-level (`import env_smoke`, D-02 — no subprocess); live `len(ENV_KERNEL_LABELS) == 8`; worker + post_message + enter-drill-down wired (env_check.py:491-589, :749-761); boot/env-check/matrix Pilot lanes 51 passed this pass (verifier-executed); live env_smoke CLI: exit 1 honest (missing model dirs — real machine state, 14/60 downloaded) with the SMOKE RESULT trailer |
| 2 | SC2: Check results persist with visible 上次检查 date; same-day restarts read the cache; manual refresh re-checks | ✓ VERIFIED | `ENV_LAST_CHECK_LINE` zh value `"上次检查: {checked_at}"` (strings.py:244-245, halfwidth colon); `Binding("r", "refresh", S.ENV_REFRESH_LABEL)` (env_check.py:329) with `action_refresh` resetting rows and re-running (:688-710); services `load_cached` / `is_same_local_day` / `run_full_check` / `persist` present (env_check.py services :81/:98/:126/:241); on_mount same-day path runs zero kernels (:426-486); the a4f WR-03 guarded persist tail renders `ENV_LAST_CHECK_DEGRADED` on persist failure (:630-641); env-check Pilot lane green this pass |
| 3 | SC3: Critical FAILs visibly block with reason; missing-dataset routes to data management; quick-check re-validates the launch-required subset | ✓ VERIFIED | Live this pass (verifier-executed over the real modules): CRITICAL {cuda, dnallm, matmul, numpy, peft, version_pins} ∩ ROUTING {dataset_dirs, model_dirs} = ∅ (disjoint=True); `QUICK_CHECK_KERNEL_IDS` = 7 ids ⊂ the 8 kernel labels (subset=True, matmul excluded); screen consumes `env_gate.gate_verdict(results)` for the verdict block (env_check.py:643); quick-check never persists (service contract). Phase-11 launch-flow wiring landed (e63a08d) — the historical deferral stays CLOSED |
| 4 | SC4: Model/dataset lists first-class selectable; k9s filter; spacebar marks on stable row_keys; presets; read-only matrix auxiliary view | ✓ VERIFIED | Live this pass: real `SelectionBackend().load_selection_data()` → 60 models / 50 datasets, both load errors None; full selection Pilot lane 38 tests green (verifier-executed); matrix screen defines ONLY escape/enter bindings (matrix.py:150-151 — no mark/filter/preset; read-only by absent bindings holds at HEAD); matrix lane green |
| 5 | SC5: Presence columns; templates round-trip as validated JSON with sweep_priorities tier interop; i18n through the constants module; foundation invariants (services textual-free, `[tui]` isolation, Pilot green CPU-side) | ✓ VERIFIED | Live this pass: presence map 50 entries + model_presence 60 entries (14 present / 60 — real filesystem state flowing, not static); preset_menu: tier-1 (2 models/1 task), tier-2 (3/0), all (59/50) + 3 saved customs, zero unknown keys, load_error None; tier-1 services lanes 121 passed in 0.22s (templates/selection/env_gate/quick_check/registries/env_check/settings — verifier-executed); 0 textual imports across all 17 tui/services modules (verifier's AST scan); 0 CJK outside tui/strings.py across tui/ (grep gate); [tui] group exact (textual>=8.2,<9 + platformdirs>=3.6,<5 + jsonschema per the 08-07 handoff; textual 8.2.8 installed; textual-dev/serve absent from committed groups; CI workflow textual-free); i18n CURRENT substance (EHC-1 + hhx CR-01): bilingual `_t(zh, en)` registry, DEFAULT EN, live `set_language` rebind through globals(), every screen reads `S.*` fresh at render time, render-time re-derivation pinned by tests/tui/test_language_rederivation.py (4 tests green, verifier-executed: AST no-frozen-capture pin + positive control + L-toggle Pilot pin + kind-spec active-language pin); zh-pin SVG goldens byte-identical through the fix (9 goldens green in the verifier's test_snapshots run, snapshots directory clean after) |
| 6 | Goal-derived foundation invariant: tolerant artifact loading landed such that loader-accepted registry inputs degrade — the console never exits on them | ✓ VERIFIED | The four named 08-09 crash-chain tests green this pass (verifier-executed: w-survives/enter-degraded-row/d-degraded-row/manual_landing_path — 4 passed in 2.73s through the REAL app + REAL backend); card-site AST pin + work-site @work never-exit pin green this pass (3 tests, verifier-executed — every card extraction site in the 4-function allowlist, each guard-carrying, ≥4-node floor, positive control); env_smoke fail-closed directory kernels confirmed at HEAD (:463 except-tuple, :472 non-dict top level, :520/:588 dict-guarded path reads — the a4f WR-01/WR-02 fixes) |

**Score:** 6/6 truths verified (0 present, behavior-unverified)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | ENV-03/ENV-04 launch-flow wiring (historical record) | Phase 11 | CLOSED by Phase 11: env preflight + E2' typed gate landed (e63a08d), Phase 11 verification passed. Kept for the audit trail |

### Advisory (New Scope, Unevidenced)

Carried forward from the fifth pass. Two rows (WR-02/WR-03 08-scope) lost their byte-unchanged premise — their files changed in the c4j/hhx waves — and were re-examined this pass: no deterministic evidence either way (no failing test, no reproducible defect command), so they remain advisory per the #3304 evidence gate and do not block. No NEW advisories this pass.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | Pin guard-granularity: guard-presence is checked per-FUNCTION, so one-of-two guard deletion inside build_wizard escapes the pin alone | other | Plan implements its own per-function wording; the w Pilot regression test (re-run green this pass) exercises both comprehensions, so the behavioral layer covers the residual; pin file byte-unchanged |
| 2 | WR-02 (08-scope label): degraded compat map renders a silent blank models table on slot 2 | architectural | post-phase scope, review-tracked; files changed since the finding was recorded, no deterministic evidence this pass |
| 3 | WR-03 (08-scope label): synchronous event-loop file reads contradict the pinned D-03 read-seam discipline | architectural | post-phase scope, bounded stall, review-tracked; files changed since, no deterministic evidence this pass |
| 4 | Info-level residuals: env action_show_detail coordinate guard absent (:749-753), matrix Header chrome, IN-04 degenerate filter tokens (open in disposition), NAV_PLACEHOLDER_* dead constants | other | info-level, review-tracked (disposition: 7/8 FIXED in hhx, IN-04 open); no must-have breach |

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `tui/screens/selection.py` | slot-2 models screen + the three extraction-site guards | ✓ VERIFIED | Changed by c4j/hhx since the machine-proven pass; guards re-proven structurally (card-site AST pin green) + behaviorally (4 named tests green) this pass |
| `tests/tui/test_pilot_selection.py` | w/enter/d real-app Pilot trio + the unit pin | ✓ VERIFIED | 38 tests collected, full lane green this pass; the four named tests green |
| `tests/tui/test_card_site_hardening.py` | the card-extraction family pin | ✓ VERIFIED | Green this pass; byte-unchanged since the mutation-proven pass |
| `pipeline/env_smoke.py` | structured kernels; fail-closed registry reads | ✓ VERIFIED | a4f guards confirmed by direct read (:463/:472/:520/:588); goldens green in the suite evidence |
| `tui/services/registries.py` | entries + presence + compat; isinstance-guarded projections | ✓ VERIFIED | Live 60/50 through the real seam, load errors None |
| `tui/services/selection.py` | filter/presets/presence; model_presence guard | ✓ VERIFIED | Live presets derivation correct (tier-1/tier-2/all + 3 customs, zero unknowns) |
| `tests/tui/test_work_site_hardening.py` | the 08-08 @work never-exit AST pin | ✓ VERIFIED | Green this pass; exit_on_error=False confirmed on the env worker at HEAD |
| `tui/app.py` / `tui/strings.py` / `pyproject.toml [tui]` | composition root / i18n single home / textual isolation | ✓ VERIFIED | Default screen intact at :507-509 through the c4j/hhx deltas; strings.py now the bilingual registry — still the single CJK home; group contents exact, textual 8.2.8 |
| `tests/tui/test_language_rederivation.py` (NEW this delta) | render-time i18n re-derivation pins (hhx CR-01) | ✓ VERIFIED | 4 tests green this pass; the I18N-01 behavioral evidence for the CURRENT architecture |
| `pipeline/registry_loader.py` | fail-loud contract BYTE-UNMODIFIED (prohibition) | ✓ VERIFIED | `git diff 0559c40..HEAD` over the file: 0 lines |

### Key Link Verification

Verified manually (the plans' must_haves use string-shaped lists that predate the verify.key-links verb's dict shape — the verb returns 0/0 for all nine plans, so wiring was checked by direct read and execution instead).

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `make tui` | `tui.app` | recipe → `uv run --group tui --group gpu python -m tui` | ✓ WIRED | Makefile:209-210; boot Pilot green this pass |
| app startup | EnvCheckScreen | `get_default_screen()` | ✓ WIRED | app.py:507-509 at HEAD |
| `w` keypress | WizardModal | build_wizard guarded vocabularies | ✓ WIRED | Named Pilot test green at HEAD; AST pin enforces the guards |
| `enter` on degraded row | card-less RowDetailModal | _open_detail isinstance narrowing | ✓ WIRED | Named Pilot test green at HEAD |
| `d` on degraded row | silent no-op | UNKNOWN-presence branch + hardened _manual_landing_path | ✓ WIRED | Named tests green at HEAD |
| AST family pin | every card extraction site in tui/ | scanner + allowlist + guard-presence | ✓ WIRED | Pin green over the current tree (verifier-executed) |
| Services layer | textual | must NOT import | ✓ WIRED (negative) | 0 imports across 17 services modules (verifier's AST scan; raw textual hits are docstrings/a probe tuple) |
| Presence column | committed n_audit | load → presence map | ✓ WIRED | Live: 50-entry presence map + 60-entry model_presence with real 14/60 split |
| i18n copy | constants module | strings.py only | ✓ WIRED (negative) | 0 CJK outside strings.py across tui/ (py + tcss) including all delta files |
| L language toggle | live re-derivation | set_language → globals() rebind → render-time S.* reads | ✓ WIRED | Toggle Pilot pin green; all ten screens read `from tui import strings as S` with attribute access |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| model list | `load_model_entries()` | overlay-merged registry | Yes — live 60, load_error None | ✓ FLOWING |
| dataset list | `load_dataset_entries()` | committed registry | Yes — live 50, load_error None | ✓ FLOWING |
| presence | `presence` / `model_presence` | filesystem + n_audit + queue reconcile | Yes — live 50 + 60 entries, real 14-present/60 split | ✓ FLOWING |
| presets | `preset_menu()` | pipeline/sweep_priorities.json + config-root customs | Yes — tier-1(2/1)/tier-2(3/0)/all(59/50) + 3 customs, zero unknown keys | ✓ FLOWING |
| env gate | `CRITICAL`/`ROUTING`/`QUICK_CHECK_KERNEL_IDS` | env_gate + quick_check over env_smoke kernels | Yes — live disjointness + 7⊂8 subset | ✓ FLOWING |
| env check rows | `run_full_check()` | imported env_smoke kernels (main() order) | Yes — live CLI run exit-1 honest with trailer (real missing-model-dirs state) | ✓ FLOWING |

### Behavioral Spot-Checks

All executed by this verifier at HEAD 1e29efc (fresh, this pass). Full-suite evidence (1808 passed at the pinned 7F baseline membership, node --test 26/26, make lint + make typecheck green) was provided by the dispatching context on this exact tree — working tree clean, no commits since — and was NOT re-run per instruction.

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| i18n re-derivation lane + both AST pins | `pytest tests/tui/test_language_rederivation.py tests/tui/test_card_site_hardening.py tests/tui/test_work_site_hardening.py -q` | 7 passed in 0.84s | ✓ PASS |
| Crash chains w/enter/d + unit pin (08-09) | `pytest tests/tui/test_pilot_selection.py -k "survives_non_dict_card or degraded_row or manual_landing_path_returns_none"` | 4 passed in 2.73s | ✓ PASS |
| Tier-1 services lanes (templates/selection/gate/quick-check/registries/env-check/settings) | `pytest tests/tui/test_services_{templates,selection,env_gate,quick_check,registries,env_check,settings}.py -q` | 121 passed in 0.22s | ✓ PASS |
| Boot / env-check / matrix Pilot lanes | `pytest tests/tui/test_pilot_boot.py tests/tui/test_pilot_env_check.py tests/tui/test_pilot_matrix.py -q` | 51 passed in 11.49s | ✓ PASS |
| Full selection Pilot lane + SVG goldens | `pytest tests/tui/test_pilot_selection.py tests/tui/test_snapshots.py -q` | 49 passed in 31.02s; snapshots dir clean after | ✓ PASS |
| Live T3 gates | `uv run --group dev --group tui python` over real env_gate/quick_check/strings | disjoint=True; 7 ids ⊂ 8 labels; default lang en | ✓ PASS |
| Live selection backend | `SelectionBackend().load_selection_data()` + `preset_menu()` | 60/50, errors None, presence 50 + model_presence 60 (14/60), presets correct + 3 customs | ✓ PASS |
| Live env_smoke CLI | `uv run --group dev python pipeline/env_smoke.py` | exit 1, trailer present (honest missing-model-dirs FAIL; all 50 dataset dirs PASS) | ✓ PASS |
| Services textual-import lock | verifier AST scan over tui/services/*.py | 17 files, 0 textual imports | ✓ PASS |
| CJK single-home | `grep -rlPn "[\x{4e00}-\x{9fff}]" tui/` | only tui/strings.py (py + tcss) | ✓ PASS |
| Loader prohibition | `git diff 0559c40..HEAD -- pipeline/registry_loader.py` | 0 lines | ✓ PASS |
| Snapshots prohibition (resolved) | `git status --short -- tests/tui/__snapshots__/` + d5cb44b | clean; D-03-approved golden refresh committed (the prohibition's pending condition satisfied) | ✓ PASS |
| CI isolation | `grep textual .github/workflows/ci.yml`; [tui] group; installed version | 0 hits; group exact (textual/platformdirs/jsonschema); textual 8.2.8; textual-dev/serve absent | ✓ PASS |
| Debt markers | TBD/FIXME/XXX over tui/, pipeline/env_smoke.py, tests/tui/ | 0 (PLACEHOLDER hits are the named Input-placeholder copy constants + nav zero-consumer note) | ✓ PASS |

### Probe Execution

No probes declared for this phase — not applicable.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| ENV-01 | 08-01, 08-03, 08-04, 08-06, 08-08 | Startup full env check, per-item ✓/✗ + detail | ✓ SATISFIED | Truth 1 (8 kernel rows, drill-down, live CLI) |
| ENV-02 | 08-04, 08-06 | Persisted results + check date + refresh; same-day cache | ✓ SATISFIED | Truth 2 (上次检查 line, r binding, cache semantics, guarded persist tail) |
| ENV-03 | 08-04, 08-06 | Critical FAIL blocks launch flow; missing data routes to data management | ✓ SATISFIED | Truth 3; Phase-11 wiring landed (deferral closed) |
| ENV-04 | 08-04, 08-06 | Quick-check re-validation of launch-required subset | ✓ SATISFIED | Truth 3 (7-id subset ⊂ 8 kernels, live) |
| SEL-01 | 08-07, 08-08, 08-09 | Browsable lists, k9s filter + mark sets, read-only matrix | ✓ SATISFIED | Truth 4 (60/50 live; 38-test lane; matrix bindings read-only) |
| SEL-02 | 08-05, 08-07 | Presets: tier-1 pair, tier-2 representatives, all, saved customs | ✓ SATISFIED | Truth 4/5 (live: 3 derived + 3 customs, zero unknowns, load_error None) |
| SEL-03 | 08-05, 08-07 | Template import/export with validation; sweep_priorities tier interop | ✓ SATISFIED | Truth 5 (templates lane green in the 121; presets flowing from sweep_priorities.json) |
| SEL-04 | 08-04, 08-07 | Per-row local data presence (✓/✗ + n_audit rows) | ✓ SATISFIED | Truth 5 (presence maps flowing live, 14/60 real split) |
| I18N-01 | 08-02, 08-03, 08-06, 08-07 | Chinese-primary copy via constants module, technical terms English | ✓ SATISFIED | Verified against the CURRENT substance per the maintainer's EHC-1 ruling (2026-10-15) + hhx CR-01 fix layer: bilingual registry with FULL zh copy (terminology-table governed), DEFAULT EN, live L toggle with render-time re-derivation (4-test lane green this pass); the constants-module convention itself unchanged — 0 CJK outside strings.py, technical terms English in both languages. The default-language shift (zh-primary → en-default, zh one keypress away) is the documented maintainer ruling encoded in the strings.py contract, not a regression |

All 9 phase-mapped requirement IDs accounted for; REQUIREMENTS.md traceability lists exactly these for Phase 8, all Complete; no orphaned IDs.

### Decision Coverage

`check.decision-coverage-verify`: 10/10 trackable CONTEXT.md decisions honored by shipped artifacts (`not_honored: []`).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none blocking) | — | No TBD/FIXME/XXX anywhere in the covered tree; PLACEHOLDER grep hits are the named Input-placeholder copy constants (S.*_PLACEHOLDER) and the nav zero-consumer annotation | — | — |

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| tests/tui/test_language_rederivation.py | I18N-01 | 4 | 0 | 0 | Behavioral (AST structural + L-toggle Pilot post-state + positive control) | Sound — the hhx fix's dedicated pin |
| tests/tui/test_pilot_selection.py | SEL-01..04, Truth 6 | 38 | 0 | 0 | Behavioral (real-app Pilot, real backend, overlay injection) | Sound |
| tests/tui/test_card_site_hardening.py + test_work_site_hardening.py | Truth 6 | 3 | 0 | 0 | Structural (AST pins, non-vacuity floors, positive controls) | Sound |
| tests/tui/test_pilot_boot/env_check/matrix.py | ENV-01/02, SC1 | 51 | 0 | 0 | Behavioral (Pilot) | Sound |
| tests/tui/test_services_*.py (7 lanes) | ENV-02..04, SEL-02..04 | 121 | 0 | 0 | Value/behavioral (real registries, injected fakes per D-03) | Sound — no disabled tests, no circular generation (goldens regenerated only by the maintainer-only Makefile script) |

### Human Verification Required

None. Every truth is machine-evidenced by this verifier's own executions this pass (232 tests across seven lanes, two AST pins, four live service gates, live CLI run). The i18n behavior specifically — previously the riskiest unexercised seam — now carries the render-time re-derivation Pilot pin this pass ran green.

### Gaps Summary

No gaps. The stale-refresh trigger was the widest yet: 42 commits (c4j slot rework, ehc bilingual conversion, D-03 golden refresh, a4f fail-closed fixes, hhx render-time i18n) rewrote large parts of the covered surface after the machine-proven fifth pass — strings.py alone churned ~1700 lines. At HEAD 1e29efc this verifier re-established every truth with fresh evidence: the default screen and worker protocol survive the env-screen rework; the T3 gates are live-disjoint with the quick-check subset intact; the real backend yields 60/50 with flowing presence (real 14/60 machine state) and correct preset derivation; all three tolerant-loading crash chains re-executed green through the real app; both structural AST pins pass; the services layer is textual-free across all 17 modules (now including the later-phase services that grew onto the Phase 8 architecture — screens added, not architecture); the i18n single-home lock holds at zero CJK outside strings.py, and the language subsystem's current substance (bilingual registry, default en per EHC-1, live L toggle re-deriving at render time) is pinned by the new re-derivation lane this pass ran green; every prohibition holds (loader byte-unmodified, CI textual-free, [tui] exact at textual 8.2.8, textual-dev/serve absent, snapshots resolved by the D-03-approved refresh). The code-review gate for the delta is dispositioned (7/8 fixed, IN-04 open info). Phase 8 remains 6/6: the console is trustworthy at rest, and later phases are still adding screens, not architecture.

---

_Verified: 2026-10-16T06:52:14Z (sixth pass, third stale-refresh, at HEAD 1e29efc)_
_Verifier: Claude (gsd-verifier)_
