---
phase: 08-tui-foundation-env-check-selection
verified: 2026-10-13T09:26:11Z
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
  - dnallm-mark/data/n_audit.json
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_services_registries.py
  - tui/__main__.py
  - tui/app.py
  - tui/screens/selection.py
  - tui/strings.py
  - tui/styles.tcss
covered_digest: "v3:sha256:def2d45254cbbae8897ad3225e9a728468eae3b7970c8c5e758604f8b809095e"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions: []
deferred:
  - truth: "Critical FAILs block entry into the launch flow (ENV-03) and the quick-check re-validates before each task launch (ENV-04) — the launch-flow wiring itself"
    addressed_in: "Phase 11"
    evidence: "Phase 11 Success Criterion 2: 'The launch gate is terraform-style: env_smoke preflight blocks on FAIL with the reason, preview precedes explicit confirmation...' — the D-09 recorded decision (08-CONTEXT) lands the pure judgment (env_gate.gate_verdict, unchanged since initial verification) and quick-check service NOW and defers the blocking hook to the Phase 11 launch screen. Carried forward unchanged. [2026-10-13 stale-refresh note: Phase 11 has SINCE landed this wiring — the env preflight + E2' typed gate (d8e63ed) and the launch gate screen, verified passed at c50abe4/UAT 64ad9e3. The deferral is closed by its successor phase; Truth 3's full intent now holds end-to-end at HEAD.]"
---

# Phase 8: TUI Foundation (Env Check & Selection) Verification Report

**Phase Goal:** The console exists and is trustworthy at rest — `make tui` opens a Textual app whose startup shows a persisted full environment-check panel, and operators build model×dataset selections k9s-style with presets, templates, and presence columns — with every non-retrofittable decision (textual-free services layer, `[tui]` dependency group, Pilot test harness, tolerant artifact loader, constants-module i18n convention) landed so later phases add screens, not architecture
**Verified:** 2026-10-13T09:26:11Z
**Status:** passed
**Re-verification:** Yes — #4682 stale-fingerprint route. The 2026-10-13T08:40Z gap-closure pass (passed 5/5, code `84b0fcf`) went stale because Phase 11's slot-4/5 promotions and copy blocks landed in three covered files: `tui/app.py`, `tui/strings.py`, `tui/styles.tcss` (six commits, `b113627`..`47dd63f`). This pass verified the delta against Phase 8's truths and architecture invariants at HEAD, spot-ran the Pilot suites, and recomputed the fingerprint. Full verdict record in the `## Re-verification (stale refresh, HEAD 8b92766, 2026-10-13)` section below; the gap-closure report body follows unchanged as the prior-pass record.

## Re-verification (stale refresh, HEAD 8b92766, 2026-10-13)

### Staleness diagnosis (commit-anchored, verified this pass)

Anchor: `91cdd63` (the commit that wrote the 2026-10-13T08:40Z passed verification, over code `84b0fcf`). `git diff --stat 91cdd63..HEAD` over the 8 covered implementation files:

- **`tui/app.py`** — +213/-3 across 3 commits: `0b5984b` (11-06 slot-4 run-config screen + promotion), `67d1274` (11-06 gate-clean typecheck), `e6da784` (11-07 slot-5 monitor screen + promotion).
- **`tui/strings.py`** — +232/-2 across 3 commits: `b113627` (CFG_/LNC_/MON_ copy blocks), `7e9fba7` (ENV_VERDICT present-tense amendment — the Phase-11-blocked note replaced now that the gate landed), `47dd63f` (WR-07 E2' typed gate fail-closed copy).
- **`tui/styles.tcss`** — +259/-0 (new-screen styles: run-config, monitor, modals; zero deletions).
- **All 5 other covered files byte-identical**: `tui/screens/selection.py`, `tui/__main__.py`, `tests/tui/test_pilot_selection.py`, `tests/tui/test_services_registries.py`, `dnallm-mark/data/n_audit.json` — zero commits since the anchor.

Truth-relevant files OUTSIDE the covered set, audited additionally this pass: `tui/screens/env_check.py` **byte-unchanged since the anchor** (zero commits — the entire SC1/SC2 surface: boot screen, 上次检查 cache line, refresh binding); `tui/services/env_gate.py`, `quick_check.py`, `templates.py`, `selection.py`, `registries.py` **byte-unchanged**; `tui/screens/nav.py` changed additively (slot-4 `0b5984b`, slot-5 `e6da784` promotions); `tui/services/` gained Phase 11 modules (run_config, sweep_launcher, sweep_monitor + WR/CR fixes) — invariants re-checked over the grown tree below.

### Delta contract analysis vs the Phase 8 must-haves

1. **SC1 boots on env-check — holds.** `get_default_screen() → EnvCheckScreen` (`tui/app.py:422` at HEAD); `tui/screens/env_check.py` byte-unchanged; `make tui` recipe and `tui/__main__.py` bootstrap byte-unchanged.
2. **SC2 上次检查 cache — holds.** `ENV_LAST_CHECK_LINE = "上次检查: {checked_at}"` (`tui/strings.py:84`, untouched by the delta); `Binding("r", "refresh", ENV_REFRESH_LABEL)` (`env_check.py:279`) and `action_refresh` (`:509`) byte-unchanged; same-day cache service byte-unchanged.
3. **SC3 gate — holds, and the deferral CLOSED.** `env_gate.py`/`quick_check.py` byte-identical; the ENV_VERDICT copy amendment (`7e9fba7`) only retires the "阻断接线于 Phase 11" future-tense note — the blocking wiring it announced has now LANDED in Phase 11 (env preflight + E2' typed gate `d8e63ed`; Phase 11 verification passed at `c50abe4`, UAT at `64ad9e3`). The prior `deferred:` item is closed by its successor phase (frontmatter annotation added).
4. **SC4 selection — holds.** `tui/screens/selection.py` byte-unchanged (all Phase 8 bindings: space/m/p/x/s/slash/v + digits intact by byte-identity); nav digit-2 → `"selection"` unchanged (`nav.py:87`); the slot-4/5 promotions are ADDITIVE rows — `NAV_SLOTS` now six real targets (`env_check`, `selection`, `data_manager`, `run_config`, `monitor`, `about`), and `test_pilot_nav_shell.py`'s placeholder-behavior tests were REPLACED by real-screen assertions (`test_placeholder_digits_fire_phase_toast_never_switch` now asserts digits 3/4/5 switch to their real screens with zero placeholder toasts — a strengthening, not a weakening). `app.py`'s `action_quit` q-intercept (`:817`) pushes the ExitModal only when a live sweep exists; at rest q exits directly (Phase 8 behavior preserved).
5. **SC5 presence/templates/i18n/invariants — hold at HEAD.** Presence chain byte-unchanged end-to-end (`n_audit.json`, `registries.py`, `selection.py`); the 62/50 assertions green (`len(model_entries) == 62`, `len(dataset_entries) == 50`, `tests/tui/test_pilot_selection.py:1348-1349`); template schema + service byte-unchanged. Invariants re-executed over the GROWN tree (including all new Phase 11 services):
   - services zero-textual: `grep textual` over `tui/services/` → **0 imports** (18 service modules incl. run_config/sweep_launcher/sweep_monitor)
   - i18n single home: CJK grep over `tui/screens/` + `tui/app.py` + `tui/services/` + `tui/__main__.py` → **0 hits** (all new copy in `strings.py` CFG_/LNC_/MON_ blocks)
   - `[tui]` isolation: pyproject `tui = [textual>=8.2,<9, platformdirs, jsonschema]` — textual absent from data/dev/gpu groups
   - XDG split: `settings.py` state (`~/.local/state/dnallmmark`) vs config (`~/.config/dnallmmark`) via platformdirs — unchanged; Phase 11's `run_config.save_state` routes through the SAME `settings.atomic_write` (tmp + `os.replace`) — the new code follows the Phase 8 atomic-write discipline
   - Pilot green CPU-side: spot-run below

### Spot-checks (executed by this verifier at HEAD 8b92766)

| Command | Result |
|---|---|
| `uv run --group dev --group tui pytest tests/tui/test_pilot_env_check.py tests/tui/test_pilot_selection.py tests/tui/test_pilot_nav_shell.py -q` | **69 passed in 29.24s, 0 failed** |
| `git diff 91cdd63..HEAD` over `selection.py`/`__main__.py`/`n_audit.json`/`test_pilot_selection.py`/`test_services_registries.py`/`env_check.py`/`env_gate.py`/`quick_check.py`/`templates.py` | empty (byte-identical) |
| Debt markers (`TBD|FIXME|XXX`) over the delta (`app.py`, `strings.py`, `styles.tcss`, `nav.py`, `test_pilot_nav_shell.py`) | 0 hits |

**Advisory (new-scope, unevidenced):** none — the covered-file delta is the sanctioned Phase 11 slot-4/5 promotion scope, diff-audited additive, with green Pilot suites and invariants re-proven over the grown tree.

**Fresh fingerprint (verbatim from `verification.fingerprint`):** `v3:sha256:def2d45254cbbae8897ad3225e9a728468eae3b7970c8c5e758604f8b809095e` over the same 8 implementation files + auto-added PLAN/SUMMARY set (frontmatter `covered_files` is the command's verbatim output).

**Verdict: PASSED — 5/5 must-haves hold at HEAD 8b92766.** Zero regressions; the architecture remains "later phases add screens, not architecture" — Phase 11 added its screens exactly through the seams Phase 8 landed (injectable services, factories, strings module, atomic-write settings).

---

## Prior-pass record (2026-10-13T08:40Z gap-closure, code 84b0fcf — kept as the verification history)

**Phase Goal:** The console exists and is trustworthy at rest — `make tui` opens a Textual app whose startup shows a persisted full environment-check panel, and operators build model×dataset selections k9s-style with presets, templates, and presence columns — with every non-retrofittable decision (textual-free services layer, `[tui]` dependency group, Pilot test harness, tolerant artifact loader, constants-module i18n convention) landed so later phases add screens, not architecture
**Verified:** 2026-10-13T08:40:00Z
**Status:** passed
**Re-verification:** Yes — gap-closure re-run after 420411e fixed the 8 baseline-refresh-stale test pins (the sole gap of the 2026-10-13T07:45Z gaps_found report)

## Re-Verification Scope (gap closed, HEAD 84b0fcf, 2026-10-13)

This report supersedes the 2026-10-13T07:45:00Z gaps_found report (4/5 at 26280d5). That report's sole gap — the SC5 "Pilot tests green CPU-side" invariant, broken because the R-03 baseline refresh (2f7211d, 43/50 → 50/50 present) invalidated 8 baseline-content test pins — is closed by:

- **420411e** `fix(10): baseline-refresh-stable test pins (8 tests, R-03 follow-up)` — the 4 test files holding the 8 red tests, zero production changes. Two rules: (a) flip/overlay/missing lanes STAGE their own fixture n_audit over real registry keys via the existing `N_AUDIT_PATH` monkeypatch seam (`_stage_missing_dataset_keys()`; the enqueue lane additionally stages a shape-D missing key); (b) committed-artifact lanes assert refresh-stable truths (well-formed schema for every record, audit key set == registry key set, definite presence for every key) instead of the old missing-count content.
- **84b0fcf** `data(10): restore the provenance DATA.md appendix after the R-03 refresh` — an R-03 side effect now handled: the audit script's default outputs had rewritten the repo-root DATA.md wholesale at 2f7211d, dropping the hand-maintained provenance appendix; this commit restores it (+84 lines, DATA.md only — documentation, no test or code surface).

(HEAD d97ccc7 sits atop 84b0fcf with a docs-only Phase 9 annotation commit; code is identical — `84b0fcf..d97ccc7` touches only `.planning/…/09-VERIFICATION.md`. All evidence below ran at that code state.)

### Gap-Closure Test-Quality Audit (the 8 changed tests)

Verified the fixture-staging approach does NOT weaken what the tests prove — read in full at 420411e:

| Test | Old pin | New pin | Verdict |
| ---- | ------- | ------- | ------- |
| `test_pilot_selection.py::test_backend_loads_the_committed_registries_and_presence` (08-07) | "exactly the 7 missing GUE tasks" | 62/50 counts + full key coverage + definite statuses (`<= {PRESENT, MISSING}`) over the REAL committed artifact | ✓ NOT WEAKENED — same real-backend seam, same registry/audit reads; only the transient content pin dropped (mixed-state coverage moved to the staged lanes) |
| `test_services_registries.py::test_load_n_audit_reads_the_real_committed_artifact` (08-04) | 2-key spot check (BEND present w/ exact rows; GUE__EPI_GM12878 missing) | FULL-artifact schema check: every record has str key + bool `missing`; every present record yields three positive int rows through the real `presence_for` | ✓ STRONGER — all 50 records validated vs 2; schema is the refresh-stable truth the services consume |
| `test_services_registries.py::test_every_registry_dataset_key_maps_to_a_definite_presence` (08-04) | `statuses == {PRESENT, MISSING}` | NEW `set(tasks) == registry_keys` lockstep invariant + definite-presence subset | ✓ STRONGER — the audit↔registry key lockstep is a new drift-catcher across future refreshes |
| `test_pilot_selection_custom.py` overlay-flip trio (10-05) | missing targets derived from the committed baseline | `_stage_missing_dataset_keys()` stages missing keys over REAL registry keys; same mechanism exercised (D-11 flip on done, revert on overlay removal, mismatch/failed never flip, live flip through the app forward) | ✓ NOT WEAKENED — identical mechanism under test; the fixture makes the mixed state deterministic instead of maintainer-refreshable |
| `test_services_download_queue.py::test_enqueue_all_missing_enqueues_downloadable_missing_only` | derived from baseline (all shape A at the time) | stages 2 downloadable + 1 shape-D missing; asserts count == 2 (downloadable only), shape-D skipped, second call no-op | ✓ STRONGER — the disabled/shape-D-skip half was never exercised before |
| `test_services_download_queue.py::test_missing_datasets_computed_over_committed_registry_and_n_audit` | computed from the two committed files + non-empty assertion | same computed cross-check over the staged view, `rows == expected == staged_missing` | ✓ PRESERVED — the derive-don't-hardcode discipline kept; determinism added |

The exit bar set by the prior report — "re-run tui lane to 0 failed (bar: 627 passed)" — is met by this verifier's own execution, not by claim: **`pytest tests/tui -q` → 627 passed in 168.16s, 0 failed** (619 + the 8 fixed).

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | SC1: `make tui` opens the console; startup runs the full env check reusing env_smoke kernels; per-item ✓/✗ status with drill-down | ✓ VERIFIED | `get_default_screen()` → EnvCheckScreen (app.py:317); `make tui` recipe + `python -m tui` bootstrap unchanged; boot/env-check Pilot suites green in the 627; env_check screen byte-identical since b69d07b |
| 2 | SC2: Check results persist with visible 上次检查 date; same-day restarts read the cache; manual refresh re-checks | ✓ VERIFIED | `ENV_LAST_CHECK_LINE.format` :477, `Binding("r", "refresh")` :279, `action_refresh` :509 — all byte-identical since b69d07b; cache tests green in the 627 |
| 3 | SC3: Critical FAILs visibly block with reason; missing-dataset routes to data management; quick-check re-validates launch-required subset | ✓ VERIFIED | `env_gate.py` + `quick_check.py` byte-identical since b69d07b; ENV_ROUTE string now routes to the real `[3]` data-management panel; launch-flow blocking hook = D-09 Phase-11 deferral (carried) |
| 4 | SC4: Model/dataset lists are first-class selectable surfaces; k9s filter; spacebar marks on stable row_keys; presets; read-only matrix auxiliary view | ✓ VERIFIED | All Phase 8 bindings at HEAD (selection.py:1186-1205: space/m/p/x/s/slash/v + digit routing); digit-2 routing unchanged (nav.py:84); 62 models / 50 datasets live-read; matrix + nav-shell suites green in the 627 |
| 5 | SC5: Presence columns (✓/✗ + n_audit rows); templates round-trip as validated JSON with sweep_priorities tier interop; Chinese-primary i18n through constants module; foundation invariants (services textual-free, `[tui]` isolation, Pilot tests green CPU-side) | ✓ VERIFIED | Presence live-verified at HEAD: 50/50 present, 0 missing, 0 unknown, exact row tuples flowing from the refreshed committed baseline through unchanged `presence_for`; templates schema byte-frozen since 098fc48; i18n grep 0; services 0 textual imports; `[tui]` group intact; **Pilot-green invariant restored: 627 passed / 0 failed** — the formerly-red backend/registries lanes named-run green (`3 passed in 0.12s`) |

**Score:** 5/5 truths verified (0 present, behavior-unverified)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | ENV-03/ENV-04 launch-flow wiring: the env-gate verdict blocking entry into the launch flow, and the quick-check invoked before each task launch | Phase 11 | Phase 11 SC2 (terraform-style gate). D-09 (08-CONTEXT) records the boundary: judgment landed in Phase 8 (`gate_verdict` + `quick_check` services, both byte-identical at HEAD), hook is Phase 11 additive wiring. Carried forward unchanged |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `make tui` | `tui.app` | `uv run --group tui --group gpu python -m tui` → bootstrap → `DnallmMarkTui` | ✓ WIRED | Recipe unchanged; boot Pilot test green in the 627 |
| Nav digit 2 | `SelectionScreen` | `NavSlot(2, NAV_LABEL_SELECTION, "selection")` → app routing | ✓ WIRED | nav.py:84; nav-bar boot test green |
| `tui/screens/env_check.py` | `pipeline/env_smoke` | imported kernels returning CheckResult | ✓ WIRED | Byte-identical; test-pinned, green |
| Services layer | textual | (must NOT import) | ✓ WIRED (negative) | 0 imports incl. Phase 10 service additions |
| `tui/strings.py` | all screens | constants import; no inline CJK | ✓ WIRED | grep gate 0 across screens + app.py |
| Presence column | committed n_audit | `load_selection_data` → `merge_presence(load_n_audit(), reconciled_rows())` → `presence_for` | ✓ WIRED | Live-run: 50/50 present with exact row counts — FLOWING |

### Data-Flow Trace (Level 4)

Unchanged from the prior report: the presence view reads the committed n_audit overlaid with the queue's reconcile-pass rows (pure tolerant read), mapped by the unchanged `presence_for`. Live-executed at HEAD: 50 datasets → 50 PRESENCE_PRESENT with exact integer row tuples, 0 missing, 0 unknown; one live reconcile row merged without altering the outcome. ✓ FLOWING.

### Behavioral Spot-Checks

All commands run by this verifier at the gap-closure HEAD (code 84b0fcf; d97ccc7 atop is docs-only).

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| **Gap exit bar — full tui lane** | `uv run --group dev --group tui pytest tests/tui -q` | **627 passed in 168.16s, 0 failed** | ✓ PASS |
| The 3 formerly-red Phase 8 tests, named | `pytest tests/tui/test_pilot_selection.py::test_backend_loads_the_committed_registries_and_presence tests/tui/test_services_registries.py::test_load_n_audit_reads_the_real_committed_artifact tests/tui/test_services_registries.py::test_every_registry_dataset_key_maps_to_a_definite_presence -q` | 3 passed in 0.12s | ✓ PASS |
| Presence flow over refreshed baseline (real services, no display) | `python3 -I` driving `registries` + `download_queue.merge_presence` + `presence_for` | 50/50 present, 0 missing, 0 unknown; 62 models | ✓ PASS |
| i18n single-home gate | CJK grep over `tui/screens/*.py` + `tui/app.py` | 0 hits | ✓ PASS |
| Services textual-free | textual-import grep over `tui/services/` | 0 imports | ✓ PASS |
| Byte-freeze invariants | `git diff 098fc48..HEAD -- pipeline/env_smoke.py schemas/run_template.json .github/workflows/` | empty | ✓ PASS |
| Gap-closure commit scope | `git show --stat 420411e` / `84b0fcf` | 4 test files only / DATA.md only | ✓ CONFIRMED (zero production changes) |
| Debt markers | `TBD\|FIXME\|XXX` grep over the changed test files | 0 hits | ✓ PASS |

### Probe Execution

No probes declared for this phase — not applicable (unchanged).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| ENV-01 | 08-01, 08-03, 08-04, 08-06 | Startup full env check, per-item ✓/✗ + detail | ✓ SATISFIED | Truth 1 |
| ENV-02 | 08-04, 08-06 | Persisted results + check date + refresh; same-day cache | ✓ SATISFIED | Truth 2 |
| ENV-03 | 08-04, 08-06 | Critical FAIL blocks launch flow; missing data routes to data management | ✓ SATISFIED | Truth 3; ENV_ROUTE now targets the real panel |
| ENV-04 | 08-04, 08-06 | Quick-check re-validation of launch-required subset | ✓ SATISFIED | Truth 3; Phase-11 wiring (deferred) |
| SEL-01 | 08-07 | Browsable model/dataset lists (62/50), k9s filter + mark sets, read-only matrix | ✓ SATISFIED | Truth 4; 62/50 live-verified |
| SEL-02 | 08-05, 08-07 | Presets: tier-1 pair, tier-2 representatives, all, saved customs | ✓ SATISFIED | Truth 4 |
| SEL-03 | 08-05, 08-07 | Template import/export with validation; sweep_priorities tier interop | ✓ SATISFIED | Schema byte-frozen; service byte-identical |
| SEL-04 | 08-04, 08-07 | Per-row local data presence (✓/✗ + n_audit rows) | ✓ SATISFIED | Truth 5 — mechanism live-verified AND test-pinned (refresh-stable pins at 420411e) |
| I18N-01 | 08-02, 08-03, 08-06, 08-07 | Chinese-primary copy via constants module, technical terms English | ✓ SATISFIED | grep gate 0 |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | — | No debt markers or stubs in the gap-closure delta (4 test files, no production changes) | — | — |

### Human Verification Required

None outstanding. Prior UAT items passed 2/2 (2026-10-12); the gap was machine-evidenced and is now machine-closed.

### Gaps Summary

No gaps. The single gap of the 2026-10-13T07:45Z report (SC5's Pilot-green invariant, broken by the R-03 baseline refresh reddening 8 content pins) is closed at 420411e with zero production changes: the flip/overlay/missing lanes now stage their own fixture n_audit over real registry keys (same mechanism, deterministic mixed state — the enqueue lane actually gains the shape-D-skip half it never exercised), and the committed-artifact lanes assert refresh-stable truths (full-artifact schema, audit↔registry key lockstep, definite presence) — two of them strictly stronger than the old pins. The exit bar (tui lane to 0 failed, 627 passed) is met by this verifier's own run. The R-03 DATA.md side effect (provenance appendix clobbered by the audit script's default outputs at 2f7211d) is separately handled by 84b0fcf. All five Phase 8 success criteria hold at HEAD; every non-retrofittable architecture decision is intact; later phases still add screens, not architecture. Fingerprint regenerated: `v3:sha256:83d76ddc56f08d13a3c7ac3f372d6fad45f011e359a5d34f4b0fb0b02201ed21`.

---

_Verified: 2026-10-13T09:26:11Z (stale refresh at HEAD 8b92766; prior pass 2026-10-13T08:40:00Z)_
_Verifier: Claude (gsd-verifier)_
