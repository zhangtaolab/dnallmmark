---
phase: 08-tui-foundation-env-check-selection
verified: 2026-10-13T07:45:00Z
status: gaps_found
score: 4/5 must-haves verified
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
  - tui/__main__.py
  - tui/app.py
  - tui/screens/selection.py
  - tui/strings.py
  - tui/styles.tcss
covered_digest: "v3:sha256:99686fda7819f8937e3406d39b6101dff3a5aedd340ccdf71f1370b98fddba5c"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining:
    - "SC5 Pilot-green invariant: 8 tui tests red at HEAD (3 in Phase 8 covered files) — the R-03 baseline refresh (2f7211d, 50/50 present) invalidated content pins written against the pre-refresh baseline (7 missing GUE keys); the tests were not updated with the refresh"
  regressions:
    - "tests/tui red count 0 -> 8 at 2f7211d (627 passed at bfe65e1 pre-refresh -> 619 passed + 8 failed at HEAD 26280d5); all 8 are baseline-content pins, zero mechanism regressions (presence mechanism live-verified 50/50 present at HEAD)"
deferred:
  - truth: "Critical FAILs block entry into the launch flow (ENV-03) and the quick-check re-validates before each task launch (ENV-04) — the launch-flow wiring itself"
    addressed_in: "Phase 11"
    evidence: "Phase 11 Success Criterion 2: 'The launch gate is terraform-style: env_smoke preflight blocks on FAIL with the reason, preview precedes explicit confirmation...' — the D-09 recorded decision (08-CONTEXT) lands the pure judgment (env_gate.gate_verdict, unchanged since initial verification) and quick-check service NOW and defers the blocking hook to the Phase 11 launch screen. Carried forward unchanged."
gaps:
  - truth: "SC5 foundation-invariant clause: 'Pilot tests green CPU-side in CI'"
    status: failed
    reason: "The maintainer's R-03 baseline refresh (commit 2f7211d, 50/50 present, 0 missing) invalidated test pins on the pre-refresh baseline content (exactly 7 missing GUE keys); the refresh commit updated the four data artifacts but no test. 8 tui tests are red at HEAD; 3 of them live in Phase 8 covered files. The presence MECHANISM is not regressed (live-verified below) — the pins are stale against deliberately-changed committed data."
    artifacts:
      - path: "tests/tui/test_pilot_selection.py"
        issue: "test_backend_loads_the_committed_registries_and_presence (:1341-1361) asserts PRESENCE_MISSING in statuses and 'exactly the 7 missing GUE tasks' — fails with statuses == {'present'} against the refreshed baseline"
      - path: "tests/tui/test_services_registries.py"
        issue: "test_load_n_audit_reads_the_real_committed_artifact (:247-257) asserts GUE__EPI_GM12878 status MISSING; test_every_registry_dataset_key_maps_to_a_definite_presence (:260-272) asserts statuses == {PRESENCE_PRESENT, PRESENCE_MISSING} — both fail against 50/50"
    missing:
      - "Update the three Phase 8 baseline-content pins to the refreshed committed baseline — or (preferred) stop pinning transient baseline content: derive expectations from the committed files without asserting a non-empty missing set, or pin against a fixture-frozen baseline"
      - "Fix the same root cause in the five Phase 10-file tests reddened by the refresh: test_pilot_selection_custom.py overlay-flip trio (needs a committed-missing key to flip; _committed_missing_dataset_keys() now empty) and test_services_download_queue.py test_enqueue_all_missing_enqueues_downloadable_missing_only + test_missing_datasets_computed_over_committed_registry_and_n_audit (both assert non-empty missing)"
      - "Re-run uv run --group dev --group tui pytest tests/tui -q to 0 failed (pre-refresh bar: 627 passed)"
---

# Phase 8: TUI Foundation (Env Check & Selection) Verification Report

**Phase Goal:** The console exists and is trustworthy at rest — `make tui` opens a Textual app whose startup shows a persisted full environment-check panel, and operators build model×dataset selections k9s-style with presets, templates, and presence columns — with every non-retrofittable decision (textual-free services layer, `[tui]` dependency group, Pilot test harness, tolerant artifact loader, constants-module i18n convention) landed so later phases add screens, not architecture
**Verified:** 2026-10-13T07:45:00Z
**Status:** gaps_found
**Re-verification:** Yes — stale-fingerprint re-run (#4682) after Phase 10 landed changes in 6 covered files + the committed n_audit baseline

## Re-Verification Scope (2026-10-13, HEAD 26280d5)

This report supersedes the 2026-10-12T09:12:00Z verification (PASS 5/5 at b69d07b). Since b69d07b, 79 commits landed — the entire Phase 10 execution (download queue, data manager, presence overlay) plus the R-03 maintainer baseline refresh. Of the Phase 8 covered files, exactly 6 drifted (`git diff --name-only b69d07b..HEAD` over the covered set):

- `tui/app.py` (+342/−) — Phase 10 execution spine: queue seam (`download_queue_service` ctor param, one shared instance), exclusive driver worker with busy-flag/generation guard, boot-resume scheduling, `build_data_manager_screen()`, WR-03 screen-stack event forward
- `tui/screens/selection.py` (+169/−3) — `d` enqueue binding (D-14), `SelectionQueueBackend` two-Protocol bridge, presence overlay in `load_selection_data` (committed n_audit ⊕ `reconciled_rows` via `merge_presence`), `apply_queue_event` live-flip hook
- `tui/strings.py` (+139/−5) — DL_/QUEUE_ string block; ENV_ROUTE_MISSING_DATASETS note updated ("数据下载面板于 Phase 10 提供" → "[3] 前往数据管理" — the placeholder retired because the panel now exists); zero Phase 8 strings lost (deletions = 1 comment block + 1 string line)
- `tui/styles.tcss` (+72) — data-manager/queue styles
- `tui/__main__.py` (+10/−2) — schedules `boot_resume_queue` before `run()` (additive; test-constructed apps stay inert)
- `tests/tui/test_pilot_selection.py` (+5/−1) — help-modal row list gains the `d` row

Also load-bearing for SC5 and changed in the delta (not in the prior covered set): `dnallm-mark/data/n_audit.json` + `.csv` — the R-03 maintainer refresh (2f7211d) moved the committed baseline from 43/50 present (7 missing GUE keys) to **50/50 present, 0 missing**. This data change is what breaks the gap recorded below. All other covered files are byte-identical since b69d07b — including the entire services layer (`env_check/env_gate/quick_check/registries/selection/settings/templates.py`), `tui/screens/env_check.py`, `tui/screens/matrix.py`, `Makefile`, `pipeline/env_smoke.py`, `schemas/run_template.json`, `pyproject.toml`.

### Delta Analysis: Phase 10 vs the Phase 8 contracts

| Contract | Verdict | Evidence at HEAD (26280d5) |
| -------- | ------- | -------- |
| SC1 startup boots on the persisted env-check panel | ✓ HONORED | `tui/app.py:317` `get_default_screen()` → `EnvCheckScreen`; boot Pilot test green; `tui/screens/env_check.py` byte-identical since b69d07b (last touched Phase 9, covered then) |
| Terminal Contract min grid 80×24 | ✓ HONORED | `tui/app.py:97-98` `MIN_WIDTH=80`/`MIN_HEIGHT=24`; `MinSizeScreen` + `on_resize` guard intact (:132,:589-608) |
| Digit 2 routes to the SAME selection screen | ✓ HONORED | `tui/screens/nav.py:84` `NavSlot(2, NAV_LABEL_SELECTION, "selection", None)` unchanged; slot-3 promotion to `data_manager` (:85) is additive |
| k9s filter / spacebar marks / presets / templates / matrix | ✓ HONORED | `tui/screens/selection.py:1186-1205`: `space`→toggle_mark, `m`→switch_list, `p`→apply_preset, `x`→open_templates, `s`→save_preset, `slash`→focus_filter, `v`→open_matrix all present; `d` (enqueue) inserted between `e` and `v` — additive |
| Presence columns over the committed n_audit | ✓ HONORED (mechanism) | `load_selection_data` (:413-433): committed `load_n_audit()` ⊕ `reconciled_rows()` → `merge_presence` → unchanged `presence_for`; live-run at HEAD: 50 dataset entries, 50/50 present, 0 missing, 0 unknown (all-✓; zero missing is a legitimate state — truth flows from the committed baseline) |
| i18n single home | ✓ HONORED | CJK grep over `tui/screens/*.py` + `tui/app.py`: 0 hits; strings.py remains the sole home |
| Services textual-free | ✓ HONORED | textual-import grep over `tui/services/` (incl. Phase 10's `download_queue.py`, `zenodo_bundle.py`): 0 imports |
| `[tui]` group isolation + `make tui` | ✓ HONORED | `pyproject.toml:54-62` textual>=8.2,<9 + platformdirs + jsonschema; `Makefile:181-182` recipe unchanged |
| XDG state/config split + atomic writes | ✓ HONORED | `tui/services/settings.py` byte-identical (platformdirs roots + `atomic_write` tmp-sibling/`os.replace`) |
| Byte-frozen artifacts | ✓ UNTOUCHED | `git diff 098fc48..HEAD -- pipeline/env_smoke.py schemas/run_template.json .github/workflows/` empty |
| **Pilot tests green CPU-side (SC5 invariant clause)** | ✗ **BROKEN** | 8 tui tests red at HEAD (3 in Phase 8 covered files) — see Gaps Summary |

## Goal Achievement

### Observable Truths

The five ROADMAP success criteria remain the yardstick. Truths 1-4 re-confirmed at HEAD; Truth 5 fails on its Pilot-green invariant clause (mechanism sub-clauses verified).

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | SC1: `make tui` opens the console; startup runs the full env check reusing env_smoke kernels; per-item ✓/✗ status with drill-down | ✓ VERIFIED | `get_default_screen()` → EnvCheckScreen at HEAD; `make tui` recipe + `python -m tui` bootstrap unchanged (the `__main__` delta only schedules the Phase 10 boot-resume before `run()`); `test_pilot_boot.py` + `test_pilot_env_check.py` green in the spot-run; env_check screen byte-identical since b69d07b |
| 2 | SC2: Check results persist with visible 上次检查 date; same-day restarts read the cache; manual refresh re-checks | ✓ VERIFIED | `tui/screens/env_check.py` byte-identical since b69d07b: `ENV_LAST_CHECK_LINE.format` :477, `Binding("r", "refresh")` :279, `action_refresh` :509; `test_pilot_env_check.py` green in the spot-run |
| 3 | SC3: Critical FAILs visibly block with reason; missing-dataset routes to data management; quick-check re-validates launch-required subset | ✓ VERIFIED | `tui/services/env_gate.py` + `quick_check.py` byte-identical since b69d07b (`gate_verdict` :80, `run_quick_check` :52); the strings-only ENV_ROUTE amendment strengthens the routing copy (now points at the real `[3]` data-management panel instead of the retired Phase-10 placeholder note); launch-flow blocking hook remains the D-09 Phase-11 deferral |
| 4 | SC4: Model/dataset lists are first-class selectable surfaces; k9s filter; spacebar marks on stable row_keys; presets; read-only matrix auxiliary view | ✓ VERIFIED | All Phase 8 bindings present at HEAD (:1186-1205); digit-2 routing unchanged; live service read at HEAD: 62 model entries / 50 dataset entries; `test_pilot_matrix.py` + `test_pilot_nav_shell.py` fully green in the spot-run; `build_selection_screen()` seam preserved (extended additively with the shared-queue backend) |
| 5 | SC5: Presence columns (✓/✗ + n_audit rows); templates round-trip as validated JSON with sweep_priorities tier interop; Chinese-primary i18n through constants module; foundation invariants (services textual-free, `[tui]` isolation, **Pilot tests green CPU-side**) | ✗ FAILED | Mechanism sub-clauses ALL hold: presence live-verified 50/50 present / 0 missing / 0 unknown with exact row counts flowing from the refreshed committed baseline through the unchanged `presence_for`; templates schema byte-frozen since 098fc48; i18n grep 0; services 0 textual imports; `[tui]` group intact. But the **Pilot-green invariant is violated at HEAD**: 8 tui tests red — `test_pilot_selection.py::test_backend_loads_the_committed_registries_and_presence`, `test_services_registries.py::test_load_n_audit_reads_the_real_committed_artifact` + `::test_every_registry_dataset_key_maps_to_a_definite_presence` (Phase 8 covered files), plus 5 Phase 10-file tests — all pinning the pre-refresh baseline content (7 missing GUE keys) that R-03 (2f7211d) deliberately changed to 50/50 present without updating the pins |

**Score:** 4/5 truths verified (0 present, behavior-unverified; Truth 5 mechanism verified, invariant clause failed)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | ENV-03/ENV-04 launch-flow wiring: the env-gate verdict blocking entry into the launch flow, and the quick-check invoked before each task launch | Phase 11 | Phase 11 SC2 (terraform-style gate). D-09 (08-CONTEXT) records the boundary: judgment landed in Phase 8 (`gate_verdict` + `quick_check` services, both byte-identical at HEAD), hook is Phase 11 additive wiring. Carried forward unchanged |

### Advisory (New Scope, Unevidenced)

None — the single new finding (stale baseline pins) carries deterministic evidence (8 named tests run red by this verifier) and is recorded as a gap, not an advisory.

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `make tui` | `tui.app` | `uv run --group tui --group gpu python -m tui` → bootstrap → `DnallmMarkTui` | ✓ WIRED | Recipe unchanged; boot Pilot test green at HEAD |
| Nav digit 2 | `SelectionScreen` | `NavSlot(2, NAV_LABEL_SELECTION, "selection")` → app routing | ✓ WIRED | `tui/screens/nav.py:84`; nav-bar boot test green |
| `tui/screens/env_check.py` | `pipeline/env_smoke` | imported kernels returning CheckResult | ✓ WIRED | Byte-identical; test-pinned, green in spot-run |
| Services layer | textual | (must NOT import) | ✓ WIRED (negative) | 0 imports incl. Phase 10 service additions |
| `tui/strings.py` | all screens | constants import; no inline CJK | ✓ WIRED | grep gate 0 across screens + app.py |
| Presence column | committed n_audit | `load_selection_data` → `merge_presence(load_n_audit(), reconciled_rows())` → `presence_for` | ✓ WIRED | Live-run at HEAD: 50/50 present with exact (train,dev,test) row counts — data FLOWING from the refreshed committed baseline |

### Data-Flow Trace (Level 4)

The only production data path that changed hands is the presence view: `load_selection_data` now reads the committed n_audit AND overlays the queue's reconcile-pass rows (a pure tolerant read of the queue state file — no service instance, no write). `presence_for` (unchanged) maps the merged view. Live-executed at HEAD with the real services: 50 dataset entries → 50 PRESENCE_PRESENT with exact integer row tuples (e.g. BEND__CpG_methylation 743095/109717/106227), 0 missing, 0 unknown; one live reconcile row merged without altering the outcome. ✓ FLOWING — no static returns, no HOLLOW props.

### Behavioral Spot-Checks

All commands run at HEAD (26280d5) by this verifier.

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Phase 8 Pilot suites spot-run | `uv run --group dev --group tui pytest tests/tui/test_pilot_selection.py tests/tui/test_pilot_env_check.py tests/tui/test_pilot_boot.py tests/tui/test_pilot_matrix.py tests/tui/test_pilot_nav_shell.py -q` | **1 failed, 82 passed in 35.51s** | ✗ FAIL (the 1 = the baseline-pin test; see gap) |
| Full tui lane (run once) | `uv run --group dev --group tui pytest tests/tui -q` | **8 failed, 619 passed in 167.90s** | ✗ FAIL (all 8 = baseline-content pins; 619+8 = 627 = the pre-refresh green count) |
| Presence flow over refreshed baseline (real services, no display) | `python3 -I` driving `registries.load_dataset_entries/load_n_audit` + `download_queue.reconciled_rows/merge_presence` + `presence_for` | 50 datasets, 50/50 present, 0 missing, 0 unknown; 62 models | ✓ PASS |
| i18n single-home gate | CJK grep over `tui/screens/*.py` + `tui/app.py` | 0 hits | ✓ PASS |
| Services textual-free | textual-import grep over `tui/services/` | 0 imports | ✓ PASS |
| Byte-freeze invariants | `git diff 098fc48..HEAD -- pipeline/env_smoke.py schemas/run_template.json .github/workflows/` | empty | ✓ PASS |
| Covered-file drift scope | `git diff --name-only b69d07b..HEAD -- <covered set>` | exactly the 6 declared files | ✓ CONFIRMED |
| Debt markers in drifted files | `TBD\|FIXME\|XXX` grep over the 6 drifted files | 0 hits (PLACEHOLDER matches are input-placeholder string constants, present since Phase 8) | ✓ PASS |

**Note on the "full suite 1197 green at HEAD" claim in the re-verification request:** falsified by direct execution. The 627-green evidence in the Phase 10 verification (10-VERIFICATION.md:61) was captured at bfe65e1 — BEFORE the R-03 baseline refresh landed (2f7211d). The refresh reddened 8 tests; no commit after 2f7211d updates them, and the working tree is clean of any pending fix.

### Probe Execution

No probes declared for this phase — not applicable (unchanged).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| ENV-01 | 08-01, 08-03, 08-04, 08-06 | Startup full env check, per-item ✓/✗ + detail | ✓ SATISFIED | Truth 1 at HEAD; env-check screen byte-identical |
| ENV-02 | 08-04, 08-06 | Persisted results + check date + refresh; same-day cache | ✓ SATISFIED | Truth 2 at HEAD |
| ENV-03 | 08-04, 08-06 | Critical FAIL blocks launch flow; missing data routes to data management | ✓ SATISFIED | Truth 3 at HEAD — the ENV_ROUTE string amendment now routes to the real Phase 10 panel; blocking hook = D-09 Phase-11 deferral |
| ENV-04 | 08-04, 08-06 | Quick-check re-validation of launch-required subset | ✓ SATISFIED | Truth 3; quick_check.py byte-identical; invocation point = Phase-11 wiring (deferred) |
| SEL-01 | 08-07 | Browsable model/dataset lists (62/50), k9s filter + mark sets, read-only matrix | ✓ SATISFIED | Truth 4 at HEAD; 62/50 live-verified |
| SEL-02 | 08-05, 08-07 | Presets: tier-1 pair, tier-2 representatives, all, saved customs | ✓ SATISFIED | Truth 4; preset bindings + services unchanged |
| SEL-03 | 08-05, 08-07 | Template import/export with validation; sweep_priorities tier interop | ✓ SATISFIED | Schema byte-frozen; templates service byte-identical |
| SEL-04 | 08-04, 08-07 | Per-row local data presence (✓/✗ + n_audit rows) | ✓ SATISFIED (mechanism) | Presence live-verified 50/50 present over the refreshed baseline — the PIN TESTS are the failure, not the mechanism (see gap) |
| I18N-01 | 08-02, 08-03, 08-06, 08-07 | Chinese-primary copy via constants module, technical terms English | ✓ SATISFIED | grep gate 0 incl. Phase 10 screens |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | — | No debt markers or stubs introduced by the Phase 10 delta in the 6 drifted covered files | — | — |

### Human Verification Required

None new. The two prior human items passed UAT 2/2 on 2026-10-12. The one failure found this round is machine-evidenced (named failing tests with deterministic reproduction) and needs a code/test fix, not human judgment.

### Gaps Summary

One gap, one root cause. The R-03 maintainer baseline refresh (2f7211d) deliberately moved the committed n_audit from 43/50 present (7 missing GUE keys) to 50/50 present — a legitimate data state the re-verification request itself anticipated ("zero missing is a legitimate state"). But the refresh updated only the four data artifacts; eight tests that pin the OLD baseline content (asserting a non-empty missing set, "exactly the 7 missing GUE tasks", GUE__EPI_GM12878 missing) went red and were left red. Three of the eight live in Phase 8 covered files, and "Pilot tests green CPU-side in CI" is an explicit clause of Phase 8's Success Criterion 5 — so the Phase 8 verdict at HEAD cannot be `passed`.

Everything else the phase promised still holds at HEAD, most of it re-proven live: the console still boots on the persisted env-check panel (byte-identical screen, test-pinned), the 上次检查 cache line and refresh survive, the env-gate and quick-check judgments are unchanged, digit 2 still routes to the same k9s SelectionScreen with filter/mark/preset/template/matrix semantics intact (the `d` enqueue binding and presence overlay are additive Phase 10 features that preserve every Phase 8 binding and seam), presence columns still flow from the committed baseline — now rendering all-✓ 50/50 with exact row counts — and every non-retrofittable architecture decision holds (services 0 textual imports including Phase 10's additions, XDG split + atomic writes byte-identical, `[tui]` group isolated, i18n single home at 0 CJK literals, byte-frozen artifacts untouched).

The fix is narrow: update the three Phase 8 pins and the five Phase 10 pins to the refreshed baseline — preferably by deriving expectations from the committed files (as `test_missing_datasets_computed_over_committed_registry_and_n_audit` already does) or pinning a fixture-frozen baseline, instead of asserting the committed artifact carries missing tasks — then re-run the tui lane to 0 failed (pre-refresh bar: 627 passed). Fingerprint regenerated at HEAD: `v3:sha256:99686fda7819f8937e3406d39b6101dff3a5aedd340ccdf71f1370b98fddba5c` (now covering the drifted implementation files and the refreshed `dnallm-mark/data/n_audit.json`).

---

_Verified: 2026-10-13T07:45:00Z_
_Verifier: Claude (gsd-verifier)_
