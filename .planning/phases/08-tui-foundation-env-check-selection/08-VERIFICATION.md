---
phase: 08-tui-foundation-env-check-selection
verified: 2026-10-11T18:11:11Z
status: passed
score: 5/5 must-haves verified
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
  - Makefile
  - pipeline/env_smoke.py
  - pyproject.toml
  - schemas/run_template.json
  - tests/test_env_smoke_bytes.py
  - tests/tui/conftest.py
  - tests/tui/test_import_lock.py
  - tests/tui/test_pilot_boot.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_matrix.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_services_env_check.py
  - tests/tui/test_services_env_gate.py
  - tests/tui/test_services_quick_check.py
  - tests/tui/test_services_registries.py
  - tests/tui/test_services_selection.py
  - tests/tui/test_services_settings.py
  - tests/tui/test_services_templates.py
  - tui/__init__.py
  - tui/__main__.py
  - tui/app.py
  - tui/screens/__init__.py
  - tui/screens/env_check.py
  - tui/screens/matrix.py
  - tui/screens/selection.py
  - tui/services/__init__.py
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
covered_digest: "v3:sha256:fad6ccbcae1c016fdf471ce49a59265420d7d3c5e16d5ad537c91893ab437d2f"
behavior_unverified: 0
overrides_applied: 0
deferred:
  - truth: "Critical FAILs block entry into the launch flow (ENV-03) and the quick-check re-validates before each task launch (ENV-04) — the launch-flow wiring itself"
    addressed_in: "Phase 11"
    evidence: "Phase 11 Success Criterion 2: 'The launch gate is terraform-style: env_smoke preflight blocks on FAIL with the reason, preview precedes explicit confirmation...' — the D-09 recorded decision (08-CONTEXT) lands the pure judgment (env_gate.gate_verdict) and quick-check service NOW (verified below) and defers the blocking hook to the Phase 11 launch screen, which consumes the same pure judgment"
human_verification:
  - test: "Run `make tui` interactively on the GB10 host over SSH/tmux at 120x40; watch startup run the REAL environment check (CUDA/matmul kernels on the GPU), then exercise r (refresh), enter (drill-down), s (selection), and q (quit)"
    expected: "Console opens on the env-check panel; rows fill pending→checking→✓/✗ inline as real kernels complete; the 上次检查 line shows the persisted date; drill-down shows kernel detail lines verbatim; refresh re-runs all kernels; q restores terminal state cleanly"
    why_human: "D-03 keeps real kernels out of CI by design — every Pilot test injects fakes; the real-kernel composition (torch import → CUDA probe → matmul) executes only on the GB10 display runtime; real-time row-by-row fill in an actual terminal cannot be observed headlessly"
  - test: "Check CJK glyph and box-drawing legibility on the operator's actual terminal (SSH client + tmux on GB10), including the ✓/✗/◌ glyphs, the pending/checking row states, and the Chinese labels"
    expected: "All row-state glyphs and Chinese copy render legibly with correct double-width alignment; the glyph-first redundancy keeps states distinguishable under NO_COLOR"
    why_human: "Planner-flagged assumption A2 (08-RESEARCH): glyph rendering on exotic terminals lacking CJK/box-drawing font coverage is assumed adequate and was explicitly ruled out of CI-verification scope by the UI-SPEC resolution note — font coverage is a property of the operator's terminal, not the codebase"
---

# Phase 8: TUI Foundation (Env Check & Selection) Verification Report

**Phase Goal:** The console exists and is trustworthy at rest — `make tui` opens a Textual app whose startup shows a persisted full environment-check panel, and operators build model×dataset selections k9s-style with presets, templates, and presence columns — with every non-retrofittable decision (textual-free services layer, `[tui]` dependency group, Pilot test harness, tolerant artifact loader, constants-module i18n convention) landed so later phases add screens, not architecture
**Verified:** 2026-10-11T18:11:11Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

The five ROADMAP success criteria are the goal-backward yardstick (Step 2a); the seven plans' must-haves were checked beneath each and are folded into the evidence column.

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | SC1: `make tui` (uv `--group tui`, `python -m tui`) opens the console; startup runs the full env check reusing env_smoke kernels; per-item ✓/✗ status with drill-down | ✓ VERIFIED | `make tui` recipe `uv run --group tui --group gpu python -m tui` (Makefile:181-182); `tui/__main__.py` bootstraps REPO_ROOT + pipeline/ from `__file__` (never CWD); app opens on `EnvCheckScreen` (`tui/app.py:184-186`); screen on_mount does cache-hit-or-worker, `@work(exclusive=True, thread=True)` is the sole kernel execution site, handlers mutate rows only (`tui/screens/env_check.py:371-435`); kernels are imported CheckResult consumers, never subprocessed (`tui/services/env_check.py:default_kernels` — live check confirmed main() order: version_pins, dnallm, peft, cuda, matmul, numpy, dataset_dirs); drill-down `EnvDetailModal` RichLog renders `result.lines` verbatim. Display-lane import proven with `--group tui` alone (textual 8.2.8, platformdirs 4.13.0, jsonschema, full tui tree). Pilot boot test (120x40, 7 rows, q quits) + full env-check Pilot suite pass headlessly. The interactive SSH/tmux/GB10 run with real GPU kernels routes to Human Verification (D-03 keeps real kernels out of CI by design) |
| 2 | SC2: Check results persist with visible check date (上次检查: YYYY-MM-DD HH:MM); same-day restarts read the cache without re-running; manual refresh re-checks on demand | ✓ VERIFIED | `persist()` writes schema_version 1, `checked_at` local naive `%Y-%m-%d %H:%M` + `checked_at_iso`, full items list, atomically (tmp+os.replace) under the D-04 state root (`tui/services/env_check.py:223-259`); `is_same_local_day` local-calendar comparison (Pitfall 8 basis documented); corrupt/torn file = None sentinel cache miss via artifact_loader; `ENV_LAST_CHECK_LINE = "上次检查: {checked_at}"` halfwidth colon per UI-SPEC Auto-Default 12 (`tui/strings.py:84`); `r` binding forces the worker path. Named test `test_same_day_state_is_a_cache_hit` (zero kernels on same-day hit) PASSED; cache-hit instant render and refresh re-run both Pilot-tested; `persist()` derives both the persisted timestamp and the rendered line from one moment (`EnvCheckBackend.persist`) |
| 3 | SC3: Critical FAILs visibly block the launch flow with the reason; missing-dataset items route toward data management; quick-check re-validates the launch-required subset | ✓ VERIFIED | `gate_verdict` pure judgment: CRITICAL (6 ids) and ROUTING (dataset_dirs) disjoint, union = exactly the 7 kernel ids (live check confirmed); zero failures → can_launch True; reasons in main() kernel order (`tui/services/env_gate.py`); the panel renders the advisory verdict — `ENV_VERDICT_CRITICAL_FAIL` names failing kernels with the Phase-11 note, `ENV_ROUTE_MISSING_DATASETS` routes to data management with the CLI audit command (`tui/strings.py:92-102`); quick-check service: `QUICK_CHECK_KERNEL_IDS` = 7 minus matmul, computed on demand, never persisted, injectable for CI fakes (`tui/services/quick_check.py`); Phase-11 quick-check strings staged (`ENV_QUICK_CHECK_PASS/FAIL`). The launch-flow blocking hook itself is the D-09 recorded decision, explicitly Phase 11 scope (see Deferred Items) |
| 4 | SC4: Model/dataset lists are first-class selectable surfaces (62/50) with card-field columns; k9s-style filter; spacebar marks on stable row_keys; presets (tier-1, tier-2, all, customs); read-only matrix auxiliary view | ✓ VERIFIED | Live check: `load_registry_counts()` == (62, 50) against the real committed registries; `SelectionScreen` with mark/model/type/species/size/presence and mark/task-key/category/type/metric/presence columns (`tui/screens/selection.py`); marks live in app-state sets passed by reference — never inside the DataTable — surviving filter rebuilds and table switches (dedicated Pilot test); filter grammar: substring + axis=value AND-terms, order-preserving, unknown-axis diagnostics (live check: `species=plant type=MLM` → 11 models; `category=Plants` → 15 datasets; the UI-SPEC Consideration-7 resolution maps SEL-01's arena axis onto species/category — the registry's own arena taxonomy, verified live); presets derived from `pipeline/sweep_priorities.json` at read time (live check: tier-1 = 2 models + 1 task, tier-2 = 3 models, all = 62/50, zero unknown keys; zero tier names hardcoded — grep clean); customs round-trip via presets.json under the XDG config root; matrix screen read-only by absent bindings — Pilot no-op test (space///p/x/m/s/v change nothing) PLUS a source-level gate (`test_screen_defines_its_read_only_navigation_bindings` greps the matrix module for forbidden binding vocabulary) — permanent CI enforcement of the out-of-scope ban |
| 5 | SC5: Presence columns (✓ present / ✗ missing + n_audit rows); templates round-trip as validated JSON with sweep_priorities tier interop; Chinese-primary i18n through the constants module; foundation invariants (services textual-free by test, `[tui]` group isolation, Pilot tests green CPU-side in CI) | ✓ VERIFIED | `presence_for` returns exact-integer (train, dev, test) rows, missing-flag authority, unknown + column-unavailable sentinels, no formatting in the service (`tui/services/registries.py:208-261`); `SEL_PRESENCE_PRESENT/MISSING` formats render in the screen (boundary edge Pilot-pinned: missing flag beats counts, present zero-row split shows exact 0); `schemas/run_template.json` is strict draft-2020-12, additionalProperties false at every level, schema_version const 1, GA formula in $comment, byte-frozen since 098fc48 (git diff empty); `validate_template` collect-all with JSON-pointer ordering (multi-violation test proves ≥5 problems in one call); `test_interop_round_trip_preserves_membership_exactly` PASSED; i18n: zero Chinese literals in `tui/screens/` + `tui/app.py` (grep gate exit 1), all copy in `tui/strings.py` (APP_/ENV_/SEL_/MATRIX_ blocks, technical terms English verbatim); services textual-free — AST import-lock test green (non-vacuous), zero textual import statements in `tui/services/` (live grep); `[tui]` group opt-in with `default-groups = ["data"]` — data/gpu lanes never install textual; no textual-dev/textual-serve anywhere in uv.lock; CI workflow byte-untouched (last modified Phase 5, fb419f6); Pilot tests green CPU-side: full `make test` = 738 Python passed + 18 JS passed, and CI's jobs run exactly `make lint` / `make typecheck` / `make test` |

**Score:** 5/5 truths verified (0 present, behavior-unverified)

### Deferred Items

Items not yet met but explicitly addressed in later milestone phases (Step 9b — conservative matching against Phase 11's goal/success criteria).

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | ENV-03/ENV-04 launch-flow wiring: the env-gate verdict actually blocking entry into the launch flow, and the quick-check service actually invoked before each task launch | Phase 11 | Phase 11 SC2: "The launch gate is terraform-style: env_smoke preflight blocks on FAIL with the reason, preview precedes explicit confirmation, and the full E2' three-seed sweep additionally requires a typed confirmation phrase." D-09 (08-CONTEXT) is the recorded decision that the judgment lands in Phase 8 (verified: `gate_verdict` + `quick_check` services + ENV_QUICK_CHECK strings) and the hook is Phase 11 wiring over the same pure functions. Not a gap — the phase goal's "non-retrofittable decisions landed" is satisfied; the hook is additive |

### Required Artifacts

All artifacts verified at all levels (exists → substantive → wired → data flows). Line counts from the working tree at HEAD (220c0bc).

| Artifact | Expected | Status | Details |
| -------- | --------- | ------ | ------- |
| `pipeline/env_smoke.py` | CheckResult frozen dataclass; 7 kernels return it; main() sole renderer; byte-stable CLI | ✓ VERIFIED | 539 lines; `CheckResult(name, ok, lines)` frozen dataclass at :83; all 7 kernels return it; `results.append(check_peft())` literal at :504; print only in main + its render helpers (_emit, print_ecosystem_diagnostics); byte-frozen through the fix loop (diff 098fc48..HEAD empty) |
| `tests/test_env_smoke_bytes.py` | Golden byte-characterization suite (S1/S2/S3, full-stdout equality + exit ints) | ✓ VERIFIED | 322 lines, 3 tests, docstring cites D-02 + E2' contract; 68 passed together with the untouched grep-lock trio |
| `tui/` package skeleton (`__init__`, `__main__`, `app`, `strings`, `styles.tcss`, `screens/__init__`, `services/__init__`) | 08-02 spine: bootstrap, strings home, contract docstrings | ✓ VERIFIED | All present and substantive; `__main__` resolves REPO_ROOT from `__file__` only; services `__init__` declares the textual-free contract |
| `tui/services/settings.py` | XDG state/config split (D-04), env overrides, atomic_write | ✓ VERIFIED | 107 lines; whole-dir overrides with empty=unset; tmp+os.replace; platformdirs resolution |
| `tui/services/env_check.py` | Orchestration + same-day cache (D-05), tolerant reads, both timestamps | ✓ VERIFIED | 259 lines; artifact_loader for every read; no bare json.load in services (grep gate exit 1); 15 tier-1 tests pass |
| `tui/services/env_gate.py` | Pure gate judgment (D-09): disjoint CRITICAL/ROUTING, frozen GateVerdict | ✓ VERIFIED | 111 lines; live check: disjoint, union = 7 kernel ids; no I/O |
| `tui/services/quick_check.py` | Launch-required subset (7 minus matmul), injectable, never persisted | ✓ VERIFIED | 69 lines; QUICK_CHECK_KERNEL_IDS verified live; no writes |
| `tui/services/registries.py` | Canonical entries + n_audit presence (D-08), counts retained | ✓ VERIFIED | 278 lines; 62/50 live; canonical MODEL_CARD_* casing constants documented; presence pure data |
| `schemas/run_template.json` | Strict one-way contract (D-07), GA semantics in $comment | ✓ VERIFIED | 68 lines; validates as draft 2020-12 (test-pinned); frozen since 098fc48 |
| `tui/services/templates.py` | Collect-all validation, export, tier interop pair | ✓ VERIFIED | 409 lines; interop round-trip named test passed |
| `tui/services/selection.py` | Presets derivation (D-06), customs, filter grammar; decoupled from registries | ✓ VERIFIED | 487 lines; no import of tui.services.registries (grep exit 1); live derivation check over the real priorities file |
| `tui/screens/env_check.py` | Full env panel: worker, cache line, verdict, drill-down, guards | ✓ VERIFIED | 523 lines; WR-02 run-id drops and WR-04 cancellation poll verified in source |
| `tui/screens/selection.py` | k9s selection surface: tables, filter, marks, preset/template modals, presence | ✓ VERIFIED | 1431 lines; all bindings present; fakes-only Pilot suite (25 tests) passes |
| `tui/screens/matrix.py` | Read-only matrix overview | ✓ VERIFIED | 310 lines; exactly esc/enter bindings; source-level forbidden-vocabulary gate |
| `tests/tui/` (13 modules) | tier-1 service suites + tier-2 Pilot suites + import lock | ✓ VERIFIED | 177 tests, all passing in 36s CPU-side; zero skipped/disabled |
| `Makefile` / `pyproject.toml` / `uv.lock` | [tui] group, make tui, lanes, asyncio_mode | ✓ VERIFIED | See truths 1 and 5; textual 8.2.8 / platformdirs 4.13.0 locked; jsonschema joined [tui] as the documented 08-07 Rule-3 deviation (08-05 handoff flag — display-lane import verified live) |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `make tui` | `tui.app` | `uv run --group tui --group gpu python -m tui` → `tui/__main__` sys.path bootstrap → `DnallmMarkTui` | ✓ WIRED | Recipe verified; import graph proven with `--group tui` alone (display-lane import-ok); the Pilot boot test exercises the same app class headlessly |
| `tui/screens/env_check.py` | `pipeline/env_smoke` | `EnvCheckBackend` → `tui.services.env_check.default_kernels()` → imported kernels returning CheckResult | ✓ WIRED | Import-only, never subprocess (test-pinned: `test_service_never_subprocesses_or_parses_env_smoke_stdout`); live kernel-order check matches main() |
| `tui/services/registries.py` | `pipeline/registry_loader` + `n_audit.json` | top-level module import over the pipeline/ sys.path root; artifact_loader tolerant read | ✓ WIRED | Live: 62/50 counts, presence data; registry_loader.py and n_audit.json untouched by the phase (git diff empty) |
| `schemas/run_template.json` | `tui/services/templates.py` | jsonschema Draft202012 collect-all validation | ✓ WIRED | Schema self-check test + multi-violation collect-all test pass; Phase 11 consumes the same schema (D-07) |
| `tui/services/selection.py` | `pipeline/sweep_priorities.json` + XDG config root | tolerant read at derive time; presets.json via settings.atomic_write | ✓ WIRED | Live derivation over the real file; customs round-trip tests via DNALLMMARK_TUI_CONFIG_DIR injection |
| `tui/app.py` | screens + services | constructor injection with real defaults; shared mark sets by reference | ✓ WIRED | `build_selection_screen` factory passes the same live set instances (SEL-01 persistence); Pilot tests inject fakes through the same seam |
| `tests/tui/conftest.py` | REPO_ROOT | sys.path insert | ✓ WIRED | 22 lines mirroring the root conftest contract; the whole tui suite collects and passes under plain pytest |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| env-check panel rows | CheckResult list | imported env_smoke kernels + persisted env_check.json state | Yes | ✓ FLOWING |
| 上次检查 line | checked_at | persisted state file (same moment as persist) | Yes | ✓ FLOWING |
| selection tables | model/dataset entries | `pipeline/registry_loader` overlay-merged registries | Yes (62/50 verified live) | ✓ FLOWING |
| presence cells | Presence status + rows | `dnallm-mark/data/n_audit.json` via artifact_loader | Yes | ✓ FLOWING |
| preset menu | Preset models/tasks | `pipeline/sweep_priorities.json` at read time | Yes (verified live) | ✓ FLOWING |
| matrix grid | presence per model×dataset | `presence_for` over load_n_audit | Yes | ✓ FLOWING |
| filter results | filtered entries | parse_filter_query/apply_filter over live entries | Yes (verified live) | ✓ FLOWING |

No static returns, hardcoded mock data, or HOLLOW props in any production path — fakes exist only in tests behind the constructor-injection seam.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Golden byte suite + grep-lock contract trio | `uv run --group dev pytest tests/test_env_smoke_bytes.py tests/test_run_finetune_contracts.py -q` | 68 passed | ✓ PASS |
| Whole tui suite (tier-1 + tier-2, headless) | `uv run --group dev --group tui pytest tests/tui -q` | 177 passed in 36.33s | ✓ PASS |
| Same-day cache hit runs zero kernels / tier interop round-trip / Pilot boot | 3 named tests | 3 passed | ✓ PASS |
| 80x24 longest-task-key backstop / 80-col footer backstop (plan-declared backstop truths) | 2 named tests | 2 passed | ✓ PASS |
| Full gate (Python slow lane + JS lane) | `make test` | 738 passed in 48.26s + node 18/18 | ✓ PASS |
| Registry counts against committed registries | `load_registry_counts()` | (62, 50) | ✓ PASS |
| Kernel order / quick-check subset / gate sets | live service introspection | main() order exact; subset = 7 minus matmul; CRITICAL∩ROUTING=∅, union=7 | ✓ PASS |
| Preset derivation from the real priorities file | `derive_presets(...)` | tier-1: 2 models+1 task; tier-2: 3 models; all: 62/50; 0 unknown | ✓ PASS |
| Filter grammar over real entries | `parse_filter_query('plant type=MLM')` / `category=Plants` | 11 plant MLM models; 15 Plants datasets | ✓ PASS |
| Display-lane import (`--group tui` alone, no dev) | `uv run --group tui python -c "import textual, jsonschema, tui.app, <all services>"` | display-lane-import-ok: textual 8.2.8, platformdirs 4.13.0 | ✓ PASS |

### Probe Execution

No probes declared for this phase — no `probe-*.sh` in PLAN/SUMMARY files and no `scripts/*/tests/probe-*.sh` conventions exist in this repo. Not applicable.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| ENV-01 | 08-01, 08-03, 08-04, 08-06 | Startup full env check, per-item ✓/✗ + detail | ✓ SATISFIED | Truth 1: kernels imported + structured CheckResult; panel renders per-row states; drill-down verbatim |
| ENV-02 | 08-04, 08-06 | Persisted results + check date + refresh; same-day cache | ✓ SATISFIED | Truth 2: both timestamps, local-day comparison, 上次检查 line, r refresh; named tests pass |
| ENV-03 | 08-04, 08-06 | Critical FAIL blocks launch flow; missing data routes to data management | ✓ SATISFIED | Truth 3: gate judgment + advisory verdict + routing line landed; the blocking hook is the D-09 Phase-11 boundary (deferred, not dropped) |
| ENV-04 | 08-04, 08-06 | Quick-check re-validation of launch-required subset | ✓ SATISFIED | Truth 3: quick_check service (6 ids, on-demand, injectable) + Phase-11 strings; invocation point is Phase-11 wiring (deferred) |
| SEL-01 | 08-07 | Browsable model/dataset lists (62/50), k9s filter + mark sets, read-only matrix | ✓ SATISFIED | Truth 4: live 62/50, mark sets on stable keys, matrix read-only enforced by test + source gate |
| SEL-02 | 08-05, 08-07 | Presets: tier-1 pair, tier-2 representatives, all, saved customs | ✓ SATISFIED | Truth 4: derivation from sweep_priorities.json (live), customs round-trip, replacing semantics Pilot-tested |
| SEL-03 | 08-05, 08-07 | Template import/export with validation; sweep_priorities tier interop | ✓ SATISFIED | Truth 5: strict schema, collect-all validation, interop round-trip test passed |
| SEL-04 | 08-04, 08-07 | Per-row local data presence (✓/✗ + n_audit rows) | ✓ SATISFIED | Truth 5: presence_for exact integers; boundary/adjacency/precision cases test-pinned |
| I18N-01 | 08-02, 08-03, 08-06, 08-07 | Chinese-primary copy via constants module, technical terms English | ✓ SATISFIED | Truth 5: strings.py single home, grep gates clean across the presentation layer |

No orphaned requirements: REQUIREMENTS.md maps exactly ENV-01..04, SEL-01..04, I18N-01 to Phase 8, and the union of plan `requirements` fields covers all 9. All 9 are marked Complete in REQUIREMENTS.md, consistent with the evidence above.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | — | No TBD/FIXME/XXX markers; no TODO/HACK beyond Textual `Input(placeholder=...)` API attributes (legitimate widget API, not stubs); no empty implementations; no console.log/print-only bodies; no skipped/disabled tests | — | — |

**Stub classification note:** every `placeholder` grep hit is the Textual `Input` widget's standard placeholder attribute or a docstring reference; every `return None` is the documented tolerant-loader sentinel with data-fetching callers. No value flows to user-visible output from a static source.

**Code-review residue (informational):** the phase's converged review loop (3 iterations, 9 findings fixed across 9 atomic commits, final re-review CLEAN 0C/0W) leaves 10 Info findings (IN-01..IN-10) open per the loop contract — full write-ups in 08-REVIEW.md, dispositions in 08-REVIEW-DISPOSITION.md. ℹ️ Info: recorded, out of fix scope, not blockers. Notable examples: IN-01 (AST import lock cannot see dynamic textual imports), IN-04 (atomic_write fixed .tmp sibling name), IN-07 (rapid double-p stacks two PresetModals via cancelled worker's late message).

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| tests/test_env_smoke_bytes.py | ENV-01 substrate | 3 | 0 | No (expected bytes are hardcoded literals recorded pre-refactor from the unmodified module — characterization by design, cross-checked by live before/after diff and the untouched source-grep trio) | Value (byte equality + exit ints) | OK |
| tests/tui/test_services_*.py (6) | ENV-01..04, SEL-02..04 | 60+ | 0 | No | Value/Behavioral | OK |
| tests/tui/test_pilot_*.py (4) | ENV-01..04, SEL-01..04, I18N-01 | 50+ | 0 | No | Behavioral (exact strings, counts, stack shapes, state transitions) | OK |
| tests/tui/test_import_lock.py | foundation invariant | 1 | 0 | No | Behavioral (AST walk, non-vacuous) | OK |

Disabled tests on requirements: 0. Circular patterns: 0. Insufficient assertions: 0.

### Decision Coverage

10/10 trackable CONTEXT.md decisions honored by shipped artifacts (gate output: `"All trackable CONTEXT.md decisions are honored by shipped artifacts."`). No status impact (warning-only gate).

### Human Verification Required

The automated evidence above covers everything verifiable headlessly. Two items genuinely require the operator/maintainer:

### 1. Interactive `make tui` session on GB10 over SSH/tmux

**Test:** Run `make tui` interactively on the GB10 host over SSH/tmux at 120x40; watch startup run the REAL environment check (CUDA/matmul kernels on the GPU), then exercise r (refresh), enter (drill-down), s (selection screen), and q (quit).
**Expected:** Console opens on the env-check panel; rows fill pending→checking→✓/✗ inline as real kernels complete; the 上次检查 line shows the persisted date; a same-day restart renders instantly from cache; drill-down shows kernel detail lines verbatim; refresh re-runs all kernels; q restores terminal state cleanly.
**Why human:** D-03 keeps real kernels out of CI by design — every Pilot test injects fakes; the real-kernel composition (torch import → CUDA probe → matmul) executes only on the GB10 display runtime; real-time row-by-row fill in an actual terminal cannot be observed headlessly.

### 2. CJK glyph legibility on the operator's real terminal

**Test:** Check CJK glyph and box-drawing legibility on the operator's actual terminal (SSH client + tmux on GB10), including the ✓/✗/◌ glyphs, the pending/checking row states, and the Chinese labels.
**Expected:** All row-state glyphs and Chinese copy render legibly with correct double-width alignment; the glyph-first redundancy keeps states distinguishable under NO_COLOR.
**Why human:** Planner-flagged assumption A2 (08-RESEARCH): glyph rendering on exotic terminals lacking CJK/box-drawing font coverage is assumed adequate and was explicitly ruled out of CI-verification scope by the UI-SPEC resolution note — font coverage is a property of the operator's terminal, not the codebase.

### Gaps Summary

No gaps. All five ROADMAP success criteria are verified against the codebase with direct evidence: every artifact exists, is substantive, is wired, and flows real data; all grep gates (i18n single home, services textual-free, no bare json.load, no hardcoded tier names) pass; the byte-freeze invariants (env_smoke CLI, run_template schema, CI workflow) hold at HEAD; the full gate is green (738 Python + 18 JS + lint/typecheck per the converged review). The phase goal's "non-retrofittable decisions landed" is satisfied — the textual-free services layer, [tui] group, Pilot harness, tolerant artifact loader, and constants-module i18n convention are all in place and locked by tests. The only items outstanding are the two human-verification runs above (by-design: real kernels and real terminals are outside CI's reach) and the Phase-11 launch-flow hook (a recorded D-09 deferral, not a Phase 8 deliverable).

---

_Verified: 2026-10-11T18:11:11Z_
_Verifier: Claude (gsd-verifier)_
