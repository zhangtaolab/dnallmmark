---
phase: 08-tui-foundation-env-check-selection
verified: 2026-10-14T17:45:49Z
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
  - dnallm-mark/data/n_audit.json
  - pipeline/env_smoke.py
  - tests/test_env_smoke_bytes.py
  - tests/tui/test_card_site_hardening.py
  - tests/tui/test_pilot_boot.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_matrix.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_services_registries.py
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
  - tui/strings.py
  - tui/styles.tcss
covered_digest: "v3:sha256:b5b816bda166ae0beb9e519656ccfd5e7c144e4472f41e8b9f1b9c8bca7fdb05"
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
    reason: "Implements the plan's own per-function wording exactly; the residual is covered behaviorally — the w Pilot regression test exercises BOTH comprehensions (re-run green this pass, inside the 38-passed selection lane). A per-node guard check would close it; not a must-have breach. Carried forward unchanged (test_card_site_hardening.py byte-unchanged since the machine-proven pass)."
    evidence_status: "none provided — mutation-evidenced in the fourth pass's report; unchanged this pass"
  - finding: "WR-02: degraded dnallm_compat map renders a silent blank models table on slot 2 (no degraded-state row when the default pool yields zero entries)"
    category: architectural
    reason: "quick-261014-mlc scope (post-phase); tracked open in 08-REVIEW-DISPOSITION.md. selection.py + data_manager.py byte-unchanged since d9b96b5 — finding unchanged this pass. (Distinct from the phase-11 monitor WR-02 label.)"
    evidence_status: "none provided"
  - finding: "WR-03: new synchronous event-loop file reads (_render_storage, _submit_save→custom_names) contradict the module's own D-03 read-seam discipline"
    category: architectural
    reason: "quick tasks 261014-f4w/mlc scope (post-phase); bounded local-file stalls, not a Phase 8 must-have breach; tracked open in the disposition. Files byte-unchanged since d9b96b5 — unchanged this pass. (Distinct from the phase-11 monitor WR-03 label.)"
    evidence_status: "none provided"
  - finding: "IN-01..IN-04: dead strings constants after the slot split; matrix Header() chrome inconsistency; missing is_valid_coordinate guard in EnvCheckScreen.action_show_detail (present in SelectionScreen.action_show_detail); degenerate filter tokens (=x, type=)"
    category: other
    reason: "Info-level, post-phase scope, tracked open in 08-REVIEW-DISPOSITION.md; none breaches a Phase 8 must-have. matrix.py + env_check.py byte-unchanged since d9b96b5 — unchanged this pass."
    evidence_status: "none provided"
---

# Phase 8: TUI Foundation (Env Check & Selection) Verification Report

**Phase Goal:** The console exists and is trustworthy at rest — `make tui` opens a Textual app whose startup shows a persisted full environment-check panel, and operators build model×dataset selections k9s-style with presets, templates, and presence columns — with every non-retrofittable decision (textual-free services layer, `[tui]` dependency group, Pilot test harness, tolerant artifact loader, constants-module i18n convention) landed so later phases add screens, not architecture
**Verified:** 2026-10-14T17:45:49Z
**Status:** passed
**Re-verification:** Yes — fifth pass (second stale-refresh tonight), at HEAD 646bcd5. The fourth pass verified 6/6 at d9b96b5; since then, later phases' gap closures (11-08) touched three files in this phase's covered set. This pass established the exact delta, re-confirmed all six truths at HEAD (live service executions + named tests + Pilot lanes), re-executed both round-2 crash chains via the 08-09 named tests, re-ran both AST pins, and ran the full suite once against the updated box baseline.

## Stale-Refresh Delta Analysis (why this pass exists)

`git diff d9b96b5..HEAD` over the covered tree — **only 3 of 26 covered implementation files changed**, all phase-11-scope:

| File | Delta | Phase-8 impact |
| ---- | ----- | -------------- |
| `tui/app.py` | WR-05: `ExitModal` takes `roots` (str normalizes to 1-tuple), kill/detach act on ALL live roots; `action_quit` multi-root branch via `LNC_EXIT_MESSAGE_MULTI` | None on the 6 truths: `get_default_screen() → EnvCheckScreen` (:438-440) intact; boot lane green; i18n gate 0 |
| `tui/screens/monitor.py` | CR-01 attach resolve() + WR-02/WR-03 rerun-seed derivation (`derive_rerun_seeds`) | Phase-11 screen (slot 5); no 08 truth reads it; covered-set membership is fingerprint-only |
| `tui/strings.py` | +`LNC_EXIT_MESSAGE_MULTI`, +`MON_RERUN_NO_SEEDS`, `MON_RERUN_CONFIRM` amended in place | Phase-11 string families only; zero 08-family constants touched (`ENV_LAST_CHECK_LINE` byte-identical); the single-home i18n lock still holds (0 CJK outside strings.py) |

**Everything else is byte-unchanged since the machine-proven fourth pass** (0 diff lines): `selection.py` (all three guards), `env_check.py`, `matrix.py`, `wizard.py`, all five 08 services, `styles.tcss`, `__main__.py`, all seven 08 test files, `env_smoke.py`, `registry_loader.py`, `n_audit.json`, `Makefile`, `pyproject.toml`, `uv.lock`. The guards therefore cannot have regressed in place; this pass confirmed them at HEAD by direct read and by re-execution.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | SC1: `make tui` opens the console; startup runs the full environment check reusing env_smoke kernels; per-item ✓/✗ status with drill-down | ✓ VERIFIED | Makefile recipe unchanged (0 diff since d9b96b5); `get_default_screen() → EnvCheckScreen` survived the WR-05 app.py delta (app.py:438-440); live `len(ENV_KERNEL_LABELS) == 8`; boot + env-check Pilot lanes green this pass (67 passed across boot/env-check/matrix/registries) |
| 2 | SC2: Check results persist with visible 上次检查 date; same-day restarts read the cache; manual refresh re-checks | ✓ VERIFIED | `ENV_LAST_CHECK_LINE = "上次检查: {checked_at}"` byte-identical (strings.py:94 — the strings delta touched only MON_/LNC_ families); `Binding("r", "refresh", ENV_REFRESH_LABEL)` (env_check.py:324); env-check lane green in the suite run |
| 3 | SC3: Critical FAILs visibly block with reason; missing-dataset routes to data management; quick-check re-validates launch-required subset | ✓ VERIFIED | Live at HEAD (`PYTHONPATH` over real services): CRITICAL {cuda, dnallm, matmul, numpy, peft, version_pins} ∩ ROUTING {model_dirs, dataset_dirs} = ∅; `QUICK_CHECK_KERNEL_IDS` 7 ids ⊂ the 8 kernel labels; env_gate.py + quick_check.py byte-unchanged; Phase-11 deferral stays CLOSED |
| 4 | SC4: Model/dataset lists first-class selectable; k9s filter; spacebar marks on stable row_keys; presets; read-only matrix auxiliary view | ✓ VERIFIED | Live real `SelectionBackend().load_selection_data()`: 59 models / 50 datasets, both load errors None; full selection Pilot lane 38 passed this pass; matrix lane green |
| 5 | SC5: Presence columns; templates round-trip as validated JSON with sweep_priorities tier interop; Chinese-primary i18n via constants module; foundation invariants (services textual-free, `[tui]` isolation, Pilot green CPU-side) | ✓ VERIFIED | Live: presence map 50 entries + `model_presence` 59 entries (4 present / 55 missing — real filesystem state flowing, not static); presets tier-1 (2) / tier-2 (3) / all (59 models, 50 tasks) + saved custom `d1`, `load_error` None, zero unknown keys; templates lane 26 passed; 0 textual imports across tui/services/ (23 raw grep hits are all comments); 0 CJK outside strings.py in tui/ including the changed app.py/monitor.py; `[tui]` group exact (textual>=8.2,<9 + platformdirs + jsonschema; 8.2.8 installed; pyproject/uv.lock unchanged); ruff + ty green |
| 6 | Goal-derived foundation invariant: tolerant artifact loading landed such that loader-accepted registry inputs degrade — the console never exits on them | ✓ VERIFIED | selection.py byte-unchanged since the machine-proven pass; all three guards confirmed by direct read at HEAD (build_wizard :718-733 walrus dict-narrowing in BOTH comprehensions; `_open_detail` :2169 `card if isinstance(card, dict) else {}`; `_manual_landing_path` :1774 `isinstance(card, dict)` ternary); both crash chains re-executed this pass via the four named 08-09 tests through the REAL app + REAL backend (4 passed); AST card-site pin + 08-08 work-site pin green (3 passed) |

**Score:** 6/6 truths verified (0 present, behavior-unverified)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | ENV-03/ENV-04 launch-flow wiring (historical record) | Phase 11 | CLOSED by Phase 11: env preflight + E2' typed gate landed (e63a08d), Phase 11 verification passed. Kept for the audit trail |

### Advisory (New Scope, Unevidenced)

Carried forward unchanged from the fourth pass (files underlying each finding are byte-unchanged since d9b96b5, so the findings cannot have moved). No new-scope findings this pass.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | Pin guard-granularity: guard-presence is checked per-FUNCTION, so one-of-two guard deletion inside build_wizard escapes the pin alone | other | Plan implements its own per-function wording; the w Pilot regression test (re-run green this pass in the 38-passed lane) exercises both comprehensions, so the behavioral layer covers the residual |
| 2 | WR-02 (08-scope label): degraded compat map renders a silent blank models table on slot 2 | architectural | mlc-scope; review-tracked open; selection.py/data_manager.py unchanged this delta |
| 3 | WR-03 (08-scope label): synchronous event-loop file reads contradict the pinned D-03 read-seam discipline | architectural | f4w/mlc-scope; bounded stall; review-tracked open; files unchanged this delta |
| 4 | IN-01..IN-04: dead constants, matrix Header chrome, missing coordinate guard in env detail action, degenerate filter tokens | other | info-level, later scope; matrix.py/env_check.py unchanged this delta |

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `tui/screens/selection.py` | slot-2 models screen + the three extraction-site guards | ✓ VERIFIED | Byte-unchanged since d9b96b5 (0 diff lines); guards read directly at HEAD; four named behavior tests re-run green |
| `tests/tui/test_pilot_selection.py` | w/enter/d real-app Pilot trio + the unit pin | ✓ VERIFIED | 4 named tests green; full lane 38 passed this pass |
| `tests/tui/test_card_site_hardening.py` | the card-extraction family pin | ✓ VERIFIED | Green this pass; file byte-unchanged since the mutation-proven pass |
| `pipeline/env_smoke.py` | structured kernels; fail-closed registry reads | ✓ VERIFIED | Byte-unchanged since d9b96b5; goldens green in the suite |
| `tui/services/registries.py` | entries + presence + compat; isinstance-guarded projections | ✓ VERIFIED | Byte-unchanged; live 59/50 through the real seam |
| `tui/services/selection.py` | filter/presets/presence; model_presence guard | ✓ VERIFIED | Byte-unchanged; live presets derivation correct (tier-1/tier-2/all + custom, zero unknowns) |
| `tests/tui/test_work_site_hardening.py` | the 08-08 @work never-exit AST pin | ✓ VERIFIED | Green this pass (3 passed with the card pin); byte-unchanged |
| `tui/app.py` / `tui/strings.py` / `pyproject.toml [tui]` | composition root / i18n single home / textual isolation | ✓ VERIFIED | app.py changed ONLY by phase-11 WR-05 (exit-modal multi-root) — default screen + boot verified at HEAD; strings.py gained only phase-11 constants, 0 CJK outside it; group contents exact, textual 8.2.8 |
| `pipeline/registry_loader.py` | fail-loud contract BYTE-UNMODIFIED (prohibition) | ✓ VERIFIED | `git diff 0559c40..HEAD` over the file: 0 lines |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `make tui` | `tui.app` | recipe → `python -m tui` | ✓ WIRED | Recipe unchanged; boot Pilot green this pass |
| app startup | EnvCheckScreen | `get_default_screen()` | ✓ WIRED | app.py:438-440 intact through the WR-05 delta |
| `w` keypress | WizardModal | build_wizard guarded vocabularies | ✓ WIRED | Named Pilot tests green at HEAD; guards read directly |
| `enter` on degraded row | card-less RowDetailModal | _open_detail isinstance narrowing | ✓ WIRED | Named Pilot test green at HEAD |
| `d` on degraded row | silent no-op | UNKNOWN-presence branch + hardened _manual_landing_path | ✓ WIRED | Named tests green at HEAD |
| AST family pin | every card extraction site in tui/ | scanner + allowlist + guard-presence | ✓ WIRED | Pin green over the current tree |
| Services layer | textual | must NOT import | ✓ WIRED (negative) | 0 actual imports (23 raw hits are comments) |
| Presence column | committed n_audit | load → presence map | ✓ WIRED | Live: 50-entry presence map + 59-entry model_presence with real 4/55 split |
| i18n copy | constants module | strings.py only | ✓ WIRED (negative) | 0 CJK outside strings.py across tui/ incl. the changed files |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| model list | `load_model_entries()` | overlay-merged registry | Yes — live 59, load_error None | ✓ FLOWING |
| dataset list | `load_dataset_entries()` | committed registry | Yes — live 50, load_error None | ✓ FLOWING |
| presence | `presence` / `model_presence` | filesystem + n_audit + queue reconcile | Yes — live 50 + 59 entries, real 4-present/55-missing split | ✓ FLOWING |
| presets | `preset_menu()` | pipeline/sweep_priorities.json | Yes — tier-1(2)/tier-2(3)/all(59,50) + custom d1, zero unknown keys | ✓ FLOWING |
| env gate | `CRITICAL`/`ROUTING`/`QUICK_CHECK_KERNEL_IDS` | env_gate + quick_check over env_smoke kernels | Yes — live disjointness + 7⊂8 subset | ✓ FLOWING |

### Behavioral Spot-Checks

All executed by this verifier at HEAD 646bcd5.

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| **Crash chain A (`w` on degraded card)** + chain B (`enter`) + `d` + unit | `pytest tests/tui/test_pilot_selection.py -k "survives_non_dict_card or degraded_row or manual_landing_path_returns_none"` | 4 passed | ✓ PASS |
| Card-site AST pin + 08-08 work-site pin | `pytest tests/tui/test_card_site_hardening.py tests/tui/test_work_site_hardening.py -q` | 3 passed | ✓ PASS |
| Boot / env-check / matrix / registries lanes | `pytest tests/tui/test_pilot_boot.py tests/tui/test_pilot_env_check.py tests/tui/test_pilot_matrix.py tests/tui/test_services_registries.py -q` | 67 passed | ✓ PASS |
| Full selection Pilot lane | `pytest tests/tui/test_pilot_selection.py -q` | 38 passed | ✓ PASS |
| Templates lane | `pytest tests/tui/test_services_templates.py -q` | 26 passed | ✓ PASS |
| Live T3 gates | `PYTHONPATH` `python -c` over real env_gate/quick_check/strings | disjoint=True; quick-check 7 ids ⊂ 8 kernels | ✓ PASS |
| Live selection backend | `SelectionBackend().load_selection_data()` | 59/50, load errors None, presence 50 + model_presence 59 (4/55), presets correct, custom d1 | ✓ PASS |
| **Full suite (once)** | `uv run --group dev --group tui pytest -q` | **7 failed / 1743 passed / 9 xfailed** — exactly the updated box baseline (same 7: 6 documented data/schema + 1 machine-state storage-overview; 1743 = 1731 + 12 tests added by phases 10-11 delta); zero new failures | ✓ PASS |
| Lint + typecheck | `make lint` / `make typecheck` | All checks passed (both) | ✓ PASS |
| Loader prohibition | `git diff 0559c40..HEAD -- pipeline/registry_loader.py` | 0 lines | ✓ PASS |
| Snapshots prohibition | `git status --short -- tests/tui/__snapshots__/` | clean | ✓ PASS |
| Architecture greps | textual imports in services / CJK outside strings / [tui] group | 0 / 0 / exact (textual 8.2.8) | ✓ PASS |
| Debt markers | TBD/FIXME/XXX/TODO/HACK over the changed + core covered files | 0 (strings.py PLACEHOLDER hits are the 7 named Input-placeholder constants, as documented) | ✓ PASS |
| Covered-set delta | `git diff d9b96b5..HEAD --stat` over covered tree | Only app.py / monitor.py / strings.py, all phase-11 scope; all 08-core files 0 diff | ✓ PASS (no 08-surface change) |

### Probe Execution

No probes declared for this phase — not applicable.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| ENV-01 | 08-01, 08-03, 08-04, 08-06, 08-08 | Startup full env check, per-item ✓/✗ + detail | ✓ SATISFIED | Truth 1 |
| ENV-02 | 08-04, 08-06 | Persisted results + check date + refresh; same-day cache | ✓ SATISFIED | Truth 2 |
| ENV-03 | 08-04, 08-06 | Critical FAIL blocks launch flow; missing data routes to data management | ✓ SATISFIED | Truth 3; Phase-11 wiring landed (deferral closed) |
| ENV-04 | 08-04, 08-06 | Quick-check re-validation of launch-required subset | ✓ SATISFIED | Truth 3 (7-id subset) |
| SEL-01 | 08-07, 08-08, 08-09 | Browsable lists, k9s filter + mark sets, read-only matrix | ✓ SATISFIED | Truth 4; degraded-card paths still guarded (Truth 6 re-run) |
| SEL-02 | 08-05, 08-07 | Presets: tier-1 pair, tier-2 representatives, all, saved customs | ✓ SATISFIED | Truth 4 (live: 3 derived + custom d1, load_error None, zero unknowns) |
| SEL-03 | 08-05, 08-07 | Template import/export with validation; sweep_priorities tier interop | ✓ SATISFIED | Truth 5 (templates lane 26 passed; presets flowing from sweep_priorities.json) |
| SEL-04 | 08-04, 08-07 | Per-row local data presence (✓/✗ + n_audit rows) | ✓ SATISFIED | Truth 5 (presence maps flowing live) |
| I18N-01 | 08-02, 08-03, 08-06, 08-07 | Chinese-primary copy via constants module, technical terms English | ✓ SATISFIED | 0 CJK outside strings.py at HEAD incl. the delta files |

### Decision Coverage

`check.decision-coverage-verify`: 10/10 trackable CONTEXT.md decisions honored by shipped artifacts (`not_honored: []`).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | — | No stubs, no unreferenced debt markers, no unwired seams found this pass | — | — |

### Human Verification Required

None. Every truth is machine-evidenced by this verifier's own executions this pass (live service reads, named crash-chain tests, Pilot lanes, full suite at the box baseline). The prior pass's A/B pre-fix controls established that those named tests exercise the real crash paths; the underlying implementation and tests are byte-unchanged since.

### Gaps Summary

No gaps. The stale-refresh trigger was precisely bounded: only `tui/app.py` (phase-11 WR-05 exit-modal multi-root), `tui/screens/monitor.py` (phase-11 rerun hardening), and `tui/strings.py` (three phase-11-family constants) changed inside the covered set since the machine-proven pass at d9b96b5 — every 08-core file (selection.py with all three guards, env_check.py, the five services, styles, all seven 08 test files, env_smoke, registry_loader, n_audit, Makefile, pyproject, uv.lock) is byte-unchanged. At HEAD 646bcd5 this verifier re-confirmed all six truths with fresh executions: the default screen survives the app.py delta, the i18n lock holds at zero CJK outside strings.py including the changed files, the T3 gates are live-disjoint with the quick-check subset intact, the real backend still yields 59/50 with flowing presence and correct presets, both crash chains re-executed green through the named Pilot tests, both AST pins pass, ruff and ty are green, all three prohibitions hold (loader byte-unmodified, snapshots clean, textual isolation exact at 8.2.8), and the full suite sits exactly at the updated box baseline — 7 failed / 1743 passed / 9 xfailed, zero new failures (the +12 passing tests are phases 10-11 additions). The four carried-forward advisories are unchanged by construction (their files did not move). Phase 8 remains 6/6: the console is trustworthy at rest, and later phases are still adding screens, not architecture.

---

_Verified: 2026-10-14T17:45:49Z (fifth pass, second stale-refresh tonight, at HEAD 646bcd5)_
_Verifier: Claude (gsd-verifier)_
