---
phase: 09-custom-model-dataset-onboarding
verified: 2026-10-13T00:18:15Z
status: passed
score: 5/5 must-haves verified
covered_files: [".planning/phases/09-custom-model-dataset-onboarding/09-01-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-01-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-02-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-02-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-03-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-03-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-04-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-04-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-05-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-05-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-06-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-06-SUMMARY.md", "pipeline/registry_loader.py", "schemas/custom_registry.json", "tests/test_registry_loader.py", "tests/tui/test_pilot_env_check.py", "tests/tui/test_pilot_nav_shell.py", "tests/tui/test_pilot_selection.py", "tests/tui/test_pilot_selection_custom.py", "tests/tui/test_pilot_wizard.py", "tests/tui/test_services_about.py", "tests/tui/test_services_custom_entries.py", "tests/tui/test_services_custom_validation.py", "tests/tui/test_services_gauntlet.py", "tui/app.py", "tui/screens/about.py", "tui/screens/env_check.py", "tui/screens/selection.py", "tui/screens/wizard.py", "tui/services/about.py", "tui/services/custom_entries.py", "tui/services/custom_validation.py", "tui/services/gauntlet.py", "tui/strings.py", "tui/styles.tcss"]
covered_digest: "v3:sha256:a3d9fe54c5faad43a602a04cc43a7615023776ebb6313fc656382f69ceb0b122"
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions: []
advisory:
  - finding: "Three phase-10 10-05 overlay-flip tests red at HEAD (introduced by phase-10 commit f417862, stale-dated by phase-10 baseline refresh 2f7211d)"
    category: other
    reason: "Out of phase-9 scope (DATA-phase presence semantics; the tests postdate phase-9 verification): their fixture helper _committed_missing_dataset_keys() asserts the committed n_audit carries missing keys, but the R-03 maintainer-ruled refresh made it 50/50 present. Resolution belongs to a phase-10 follow-up: stage a missing-key fixture instead of reading the committed baseline's missing set."
    evidence_status: "deterministic: named tests fail at HEAD 26280d5 (AssertionError: the committed baseline must carry missing keys); direct parse of dnallm-mark/data/n_audit.json: 50 records, 0 missing; RESOLVED at 84b0fcf (420411e fixture-staged pins) — re-run 3 passed"
behavior_unverified: 1
behavior_unverified_items:
  - truth: "CUST-06 share unit is consumable cross-machine/cross-version (an exported custom registry file lands on another operator's machine through the same import + gauntlet path)"
    test: "On a second machine (or a second config root), export a custom registry via o, transfer the file, import it via f, and run the per-entry gauntlet"
    expected: "The imported entry passes its own gauntlet and lands; keys, relative paths, and metric names resolve identically on the receiving machine"
    why_human: "Cross-machine file sharing and cross-version schema drift are not CI-verifiable; the planner explicitly flagged this edge as open for UAT (09-06 PLAN FLAGGED PLANNER ASSUMPTION) — no code path is blocked on it"
human_verification:
  - test: "Cross-machine share-unit round trip: export a custom registry on machine A (o flow), transfer the file, import (f flow) on machine B, watch the per-entry gauntlet run"
    expected: "Entry passes its own gauntlet and lands on machine B; no conflict or schema surprise"
    why_human: "Real cross-machine/cross-version consumption of the share unit is outside CI reach; flagged by the planner for UAT"
  - test: "Interactive wizard loop in a live console: w from the model and dataset tables, walk all four steps each, submit with several broken fields, fix them, watch the gauntlet panel, land, undo, toggle e"
    expected: "Collect-all report lists every problem numbered; values survive report/gauntlet dismiss; all-✓ lands with toast; u undo removes exactly the just-landed key; e toggle flips enabled with the loader-skip visible"
    why_human: "Live console feel (toasts, focus flow, dim/bold rendering at 80x24) is human-judged; Pilot tests cover the interactions programmatically but not the operator experience"
---

# Phase 9: Custom Model & Dataset Onboarding (自定义接入向导) Verification Report

**Phase Goal:** Operators can bring their own model and dataset into the benchmark entirely from the console, with official registries provably untouched — guided wizards collect the full entry into user-owned custom registries, fool-proofing validation collects every field problem in one fail-fast report before anything is written, and an entry lands only after passing the real gauntlet (dry-run precheck + audit reconciliation) with entry-level rollback when anything fails
**Verified:** 2026-10-12T11:13:37Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

Merged must-haves: the five ROADMAP Success Criteria (the contract), cross-checked against the six PLAN frontmatter truth blocks (09-01 services, 09-02 gauntlet + D-09, 09-03 nav shell, 09-04 wizard collection, 09-05 wizard writing, 09-06 selection integration). Every plan truth maps into one of the five SCs below.

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | SC1: one action from the model list opens the custom-model wizard; a validated submission lands in `~/.config/dnallmmark/custom_models.json` and the model appears via the overlay; `pipeline/models_info.json` never written | ✓ VERIFIED | `tui/screens/selection.py` composes the real wizard over real services (`_compose_wizard`, lines ~535-630); `WizardModal` (tui/screens/wizard.py:543) with `on_valid` handoff; `custom_entries.land` (custom_entries.py:209) writes through `settings.atomic_write` to `custom_registry_path(kind)` → `custom_models.json`; tracer test `test_tracer_land_then_overlay_load_then_undo` (test_services_custom_entries.py:139) proves land → `registry_loader.load_models_registry` visibility end-to-end; full-loop Pilot `test_full_loop_models_wizard_lands_badges_counts_and_disables` passes over tmp roots. Official registries: zero write paths in tui/ (grep), git-clean, last touched Phase 4/6 commits |
| 2 | SC2: same for datasets → `~/.config/dnallmmark/custom_datasets.json`, `pipeline/datasets_info.json` never written | ✓ VERIFIED | Same store with `KIND_DATASETS`; `KIND_FILE_NAMES` in gauntlet/entries seams; `test_full_loop_datasets_wizard_runs_both_legs_and_disables` (dataset candidate runs both gauntlet legs) passes; dataset landing path and official-file zero-touch share the SC1 evidence |
| 3 | SC3: submission blocked until validation passes; collect-all fail-fast one-pass report (required/type/enum/collisions vs official AND custom/path existence/split parseability/rows>0/label column/metric-in-registry), every problem itemized | ✓ VERIFIED | `validate_model_candidate`/`validate_dataset_candidate` (custom_validation.py:193,237) collect `(field_key, message)` pairs through `_check_key/_check_required/_check_numeric/_check_enum/_check_path_exists/_check_split_fields/_count_well_formed_rows`; collision check covers official + existing custom keys; `METRIC_REGISTRY` frozenset parity-locked to `SUITE_CANONICAL` by `test_metric_registry_parity_with_suite_canonical` (:583); collect-all behavior proven by `test_three_simultaneous_defects_yield_three_ordered_problems`, `test_dataset_collect_all_spans_all_required_fields`, `test_problems_follow_field_definition_order_not_dict_order` (:208-238); wizard renders the numbered report view and hands off only on clean pass (wizard.py `_phase` form/report/gauntlet state machine) |
| 4 | SC4: after submission the automatic gauntlet runs (dry-run precheck + audit reconciliation); any failure reported prominently, failed entry never lands, entry-level revert, no half-written state | ✓ VERIFIED | `tui/services/gauntlet.py`: dry-run leg invokes `run_sweep.py --dry-run` as LIST argv with staged overlay env (`DNALLMMARK_CUSTOM_REGISTRY_DIR` pinned to temp), pass = exit 0 AND parsed `sweep_manifest.json` cells contain candidate with status planned; audit leg stages candidate-only registry with absolute `Dataset_path`, all-temp outputs, empty custom-dir pin, pass parsed from `n_audit.json` (missing false, splits rows>0, `unified_eval_n > 0`, declared-vs-measured reconciliation); timeouts (60s/300s) yield failed items verbatim; TemporaryDirectory cleanup. Real-subprocess evidence: `test_real_subprocess_dry_run_passes_for_synthetic_model_candidate`, timeout tests, and `test_committed_audit_artifacts_byte_unchanged_across_real_gauntlet` (Pitfall 1 hash-pin) all pass. Gauntlet imports only `read_entries` from the store (read-only seam — landing is the caller's act); wizard lands through injected `land`/`undo` seams only after all-✓; per-entry import rollback covered in wizard Pilot suite. 09-02 prohibition "no pipeline surface beyond the enabled-skip" spot-checked: `registry_loader.py` gained the skip only |
| 5 | SC5: landed customs carry a visible marker distinct from official 62/50 in both lists, individually enable/disable, export as the share unit; official registries and existing test suite stay green and untouched | ✓ VERIFIED | `SelectionData.custom_status` (selection.py:216) composes overlay-merged view + management `read_entries` read (disabled stay visible with （已停用）); `◇` badge render class (:841); `e` toggle through `custom_entries.set_enabled` (atomic) with loader-skip proof `test_disabled_entry_stays_in_the_table_while_the_real_loader_skips_it` (:503); `registry_loader.py:166` `entry.get("enabled") is False` skip (absent = enabled, official entries unaffected — pre-existing tests unmodified); count segment 官方/自定义 in title bar; `export_registry` byte-identical copy (custom_entries.py:339); phase test run: **260 passed** across the 10 phase test files; reported full gate 954 + JS 18 |

**Score:** 5/5 truths verified (1 present, behavior-unverified: the cross-machine share-unit consumption edge — see Human Verification)

### Required Artifacts

All 21 artifacts from the six PLANs exist and are substantive (verify.artifacts query returned 0/0 — the plans use plain-string artifact lists the tool does not parse; existence + substance verified manually via wc -l, 15,831 total lines). Levels: exists ✓, substantive ✓ (no stubs found), wired ✓ (see key links).

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| tui/services/custom_entries.py | store: read/land/undo/set_enabled/import/export | ✓ VERIFIED | 432 lines; all six operations + `_normalize_entry` (relpath, name stamps, int splits) present |
| tui/services/custom_validation.py | collect-all validator + METRIC_REGISTRY | ✓ VERIFIED | 616 lines; both validators, ValidationSources, import validator, parity-locked registry |
| schemas/custom_registry.json | entry-shape schema for imports | ✓ VERIFIED | 71 lines; wired to `load_import_schema()` (custom_validation.py:486) |
| tui/services/gauntlet.py | two-leg subprocess gauntlet | ✓ VERIFIED | 593 lines; both legs, artifact-parsed criteria, timeouts, run_id |
| pipeline/registry_loader.py | D-09 enabled:false skip (the one pipeline change) | ✓ VERIFIED | line 166; official-absent byte-identity preserved |
| tui/screens/wizard.py | 4-step modal family + report + gauntlet panel + import/export | ✓ VERIFIED | 1702 lines; StepSpec/KindSpec, `_phase` state machine, gauntlet rows, seams |
| tui/screens/selection.py | w entry, badge, e toggle, count, prefill | ✓ VERIFIED | 1888 lines; custom_status backend + `_compose_wizard` real wiring |
| tui/app.py, tui/screens/about.py, tui/services/about.py, env_check.py, strings.py, styles.tcss | 09-03 nav shell + about + i18n | ✓ VERIFIED | top menu/bottom bar/about per 09-03 truths; zero-Chinese-literals grep tests pass |
| 10 test files (services + Pilot) | behavioral evidence | ✓ VERIFIED | 260 tests, all passing (147.8s) |

### Key Link Verification

| From | To | Via | Status |
| ---- | -- | --- | ------ |
| wizard submit | custom_validation | validators → numbered report view → on_valid on clean pass | ✓ WIRED (wizard.py `_phase` branches; Pilot suite passes) |
| all-✓ handler | custom_entries.land | injected land seam → atomic write → overlay-visible | ✓ WIRED (selection `_compose_wizard` injects real `custom_entries_service` functions; tracer test) |
| gauntlet service | run_sweep.py --dry-run / audit_n_frequencies.py | LIST argv subprocess + pinned env → artifact_loader parse | ✓ WIRED (real-subprocess tests pass) |
| registry_loader enabled-skip | every registry consumer + 09-06 management read | `entry.get("enabled") is False` | ✓ WIRED (loader-skip visibility test passes) |
| selection e action | custom_entries.set_enabled | atomic seam → next load skips | ✓ WIRED |
| about counts / selection count segment | registries + custom_entries reads | two-view composition | ✓ WIRED |
| gauntlet staging | custom_entries | `read_entries` only (read-only import) | ✓ WIRED (prohibition held) |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| selection custom_status | overlay merge + management read | registry_loader + custom_entries.read_entries | ✓ | ✓ FLOWING |
| gauntlet verdicts | parsed artifacts | sweep_manifest.json / n_audit.json from real subprocesses | ✓ | ✓ FLOWING |
| wizard report | problems list | validate_*_candidate over injected ValidationSources | ✓ | ✓ FLOWING |
| about 数据版本 row | official/custom counts + n_audit presence | registries + custom_entries services | ✓ | ✓ FLOWING |

No static returns, hardcoded verdicts, or mock-fed renders found on the production paths (fakes are test-only injections, real composition in `selection._compose_wizard`).

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full phase test surface (10 files: services, gauntlet, registry loader, Pilot wizard/selection/nav/env/about) | `.venv/bin/pytest tests/tui/test_services_custom_entries.py tests/tui/test_services_custom_validation.py tests/tui/test_services_gauntlet.py tests/test_registry_loader.py tests/tui/test_pilot_wizard.py tests/tui/test_pilot_selection_custom.py tests/tui/test_services_about.py tests/tui/test_pilot_nav_shell.py tests/tui/test_pilot_env_check.py tests/tui/test_pilot_selection.py -q` | 260 passed in 147.76s *(run at the phase-9 verification commit, 2026-10-12, pre-phase-10)* **[amended 2026-10-13]** — not reproducible at re-verification HEAD `26280d5`: the R-03 baseline refresh (2f7211d) had reddened 3 baseline-content pins in `test_pilot_selection.py` (Phase-8 lane, 08-VERIFICATION.md @767ce3e) and the 3 phase-10 overlay-flip tests in `test_pilot_selection_custom.py`; the phase-9 must-have tests stayed green (see Re-verification). All 6 reds are green again at `84b0fcf` (post-420411e) | ✓ PASS at verification time (amended — see note) |
| Real-subprocess gauntlet legs + committed-artifact byte-unchanged regression | included above (named tests enumerated: `test_real_subprocess_dry_run_passes_for_synthetic_model_candidate`, `test_committed_audit_artifacts_byte_unchanged_across_real_gauntlet`) | passed | ✓ PASS |
| Full CUST story loop (wizard → validate → gauntlet → land → badge/count → disable) | `test_full_loop_models_wizard_lands_badges_counts_and_disables`, `test_full_loop_datasets_wizard_runs_both_legs_and_disables` | passed | ✓ PASS |
| METRIC_REGISTRY = SUITE_CANONICAL parity | `test_metric_registry_parity_with_suite_canonical` | passed | ✓ PASS |

### Probe Execution

No `probe-*.sh` scripts declared by the plans or present under `scripts/`; not a probe-based phase — behavioral spot-checks above carry the evidence. N/A.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| CUST-01 | 09-01, 09-03, 09-04, 09-06 | model wizard → custom registry, official untouched, quirk checklist | ✓ SATISFIED | Truth 1 |
| CUST-02 | 09-01, 09-03, 09-04, 09-06 | dataset wizard → custom registry | ✓ SATISFIED | Truth 2 |
| CUST-03 | 09-01, 09-04 | collect-all fail-fast field validation | ✓ SATISFIED | Truth 3 |
| CUST-04 | 09-02, 09-05 | gauntlet dry-run + audit, entry-level rollback | ✓ SATISFIED | Truth 4 |
| CUST-06 | 09-01, 09-02, 09-06 | badge / enable/disable / export share unit | ✓ SATISFIED (share-unit cross-machine consumption edge → UAT) | Truth 5 + behavior_unverified_items |

No orphaned requirements: REQUIREMENTS.md maps exactly CUST-01/02/03/04/06 to Phase 9 (CUST-05 belongs to Phase 7). All five accounted for across plans.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | none — no TBD/FIXME/XXX markers in any of the 11 implementation files; no stub returns on production paths | — | — |

Official registries `pipeline/models_info.json` / `pipeline/datasets_info.json`: working tree clean, no Phase 9 commits touch them (last modified by Phase 4/6 commits). The cardinal prohibition held.

### Human Verification Required

### 1. Cross-machine share-unit round trip (CUST-06 flagged planner assumption)

**Test:** Export a custom registry on machine A (o flow), transfer the file, import it (f flow) on machine B, watch the per-entry gauntlet run.
**Expected:** The imported entry passes its own gauntlet and lands; keys, relative paths, and metric names resolve identically.
**Why human:** Cross-machine/cross-version consumption of the share unit is not CI-verifiable; the planner explicitly surfaced this edge (09-06 FLAGGED PLANNER ASSUMPTION) rather than silently resolving it.

### 2. Live console wizard loop

**Test:** In a live console: w from both tables, walk all four steps per kind, submit with several broken fields, fix them, watch the gauntlet panel, land, undo (u), toggle e.
**Expected:** Numbered collect-all report; values preserved across report/gauntlet dismiss; all-✓ lands with toast; undo removes exactly the just-landed key; e toggle flips enabled with the loader-skip visible in the table.
**Why human:** Operator-experience qualities (toasts, focus flow, 80×24 legibility of the live console) are human-judged; Pilot tests cover the interactions programmatically.

### Gaps Summary

No gaps. All five ROADMAP Success Criteria are verified against the codebase with passing behavioral evidence (260 phase tests, including real-subprocess gauntlet legs, the committed-artifact byte-unchanged regression, the loader-skip visibility proof, and the full-loop integration Pilots). All prohibitions held: official registries untouched (git evidence + code grep), gauntlet read-only over the store, wizard writes only through the store's atomic seam, no pipeline surface change beyond the D-09 enabled-skip. The status is human_needed solely for the two UAT items above — the planner-flagged CUST-06 cross-machine share-unit edge and the live console experience — neither of which blocks any code path.

---

_Verified: 2026-10-12T11:13:37Z_
_Verifier: Claude (gsd-verifier)_

---

## Re-verification (stale refresh, HEAD 26280d5, 2026-10-13)

**Route:** #4682 narrow-delta stale refresh. The previous PASS (2026-10-12T11:13:37Z) plus UAT (09-UAT.md, 2/2 passed live) went stale after 83 phase-10 commits. Goal-backward re-verified at HEAD `26280d5cf48d65a47205eac05530b572f67fdc35` (branch autorun; working tree clean over every phase-9 surface).

### Delta since previous verification (phase-9 surfaces touched by phase 10)

| Surface | Delta | Phase-9 impact |
| ------- | ----- | -------------- |
| `tui/services/gauntlet.py` (+ its test) | 46ddd37: `_invoke` passes `errors="replace"` alongside `text=True` (1 kwarg + 6 comment lines) | none — hardening twin of download_queue's WR-05 fix; kwargs-pin regression `test_runner_decode_policy_pins_errors_replace` is present (asserts `kwargs["errors"] == "replace"`, KeyError-RED before the line) and passing |
| `tui/screens/selection.py` | phase-10 10-05 + review-fix commits: `d` enqueue Binding inserted between the `e` pair and `v` (D-14, comment-documented); additive `SelectionQueueBackend` adapter (:559); presence overlay in `load_selection_data` (`merge_presence(committed_audit, reconciled_rows())` feeding only `presence`/`audit_available`); `apply_queue_event` (done event -> `_load_data()` re-run) | none — the 09-06 custom composition is context-unchanged: overlay-merged UNION management read, `custom_status` build (:393-411), `_compose_wizard` land/undo seams (:620-712), `w`/`e`/`v` bindings, `action_toggle_enabled` -> `set_enabled` (:1649-1664), `_key_cell` badge render; no delta hunk touches the custom/badge/toggle/wizard paths |
| `tui/app.py` | `build_selection_screen` additionally injects `queue_service=SelectionQueueBackend(self._download_queue)`; queue event forwards past modals | none — additive constructor kwarg; `selection_service` + shared mark-set injection unchanged |
| `tui/strings.py` | +121 constants (DL_/QUEUE_ block); the 4 removed lines amend the phase-10 `ENV_ROUTE_MISSING_DATASETS` env-route string, not any phase-9 constant | none |
| `dnallm-mark/data/n_audit.json` (2f7211d) | committed baseline refreshed to 50/50 present (R-03 maintainer ruling) | none for the wizard/gauntlet/custom surfaces — presence columns only; but it stale-dated three phase-10 tests (cross-phase warning below) |
| `pipeline/registry_loader.py`, `pipeline/models_info.json`, `pipeline/datasets_info.json`, `tui/screens/wizard.py`, `tui/services/custom_entries.py`, `tui/services/custom_validation.py`, `schemas/custom_registry.json` | zero commits since 2026-10-12T11:13:37Z; `git status` clean | untouched — D-09 skip, official-registry prohibition, wizard modal (`u` undo :601, `f`/`o` import/export :597-598), store, and validator all byte-stable |

Phase-10 additions to `tests/tui/test_pilot_selection_custom.py` are additive test functions (10 new, 0 phase-9 tests deleted or weakened; the 5 changed non-test lines are the `_open_selection` helper gaining the `queue_service` injection and the nav-slot whitelist gaining `data_manager`).

### Per-must-have still-holds verdicts

| # | Truth (SC) | Verdict at HEAD | Evidence |
| - | ---------- | --------------- | -------- |
| 1 | SC1 model wizard -> `custom_models.json` over the overlay; `models_info.json` never written | STILL HOLDS | `w`->`open_wizard` Binding (:1197); `_compose_wizard` land/undo seams intact; `test_full_loop_models_wizard_lands_badges_counts_and_disables` PASS; `test_tracer_land_then_overlay_load_then_undo` PASS; `pipeline/models_info.json` zero commits since prior verification |
| 2 | SC2 dataset twin -> `custom_datasets.json`; `datasets_info.json` never written | STILL HOLDS | `test_full_loop_datasets_wizard_runs_both_legs_and_disables` PASS; `pipeline/datasets_info.json` zero commits |
| 3 | SC3 collect-all fail-fast validation | STILL HOLDS | `custom_validation.py` byte-stable; its 43-test suite green incl. `test_metric_registry_parity_with_suite_canonical` |
| 4 | SC4 gauntlet (dry-run + audit), entry-level rollback, no half-written state | STILL HOLDS | gauntlet suite 32/32 green incl. the real-subprocess legs and the committed-artifact byte-unchanged regression; the 46ddd37 decode fix hardens `_invoke` only and carries its own kwargs-pin regression (green); wizard session-undo `u` binding in an untouched file |
| 5 | SC5 badge / e toggle / export share unit; official registries + existing suite green | STILL HOLDS | `test_disabled_entry_stays_in_the_table_while_the_real_loader_skips_it` PASS; badge + toggle + `registry_loader.py` enabled-skip untouched; all phase-9 must-have tests run green (178/181 spot-run green; the 3 red are phase-10's — and `test_pilot_selection.py`, outside the spot set, carried 3 Phase-8 baseline pins red at `26280d5`, Phase-8 lane 767ce3e; both sets green at `84b0fcf` — see warning) |

### Spot runs at HEAD

- `.venv/bin/pytest tests/tui/test_services_gauntlet.py tests/tui/test_services_custom_entries.py tests/tui/test_pilot_selection_custom.py tests/tui/test_pilot_wizard.py tests/test_registry_loader.py -q` -> **135 passed, 3 failed** (119.76s)
- `.venv/bin/pytest tests/tui/test_services_custom_validation.py -q` -> **43 passed**
- Named must-have tests, single `-k "full_loop or disabled_entry_stays or tracer_land or decode_policy"` run -> **5 passed**
- Per-file: gauntlet 32/32 - custom_entries 17/17 - pilot_selection_custom 20/23 - pilot_wizard 42/42 - registry_loader 24/24 - custom_validation 43/43 = **178/181 green**
- Scope note *(added 2026-10-13)*: `tests/tui/test_pilot_selection.py` (the Phase-8 SEL suite inside the phase-9 evidence set) was NOT in this spot set; at `26280d5` it carried 3 baseline-content pins red from the R-03 refresh — documented in the Phase-8 re-verification (767ce3e), never phase-9 evidence. Re-runs at `84b0fcf` (post-420411e): the overlay trio **3 passed** (1.14s) and `test_pilot_selection.py` **31 passed** (22.69s); full `pytest tests/tui -q` reported **627 passed, 0 failed** at `84b0fcf`.

### Digest-refresh re-run (84b0fcf code state, 2026-10-13T00:18Z)

Full covered surface re-run to refresh the attested digest (coordinator-directed): all 10 covered test files in one invocation —
`.venv/bin/pytest tests/tui/test_services_custom_entries.py tests/tui/test_services_custom_validation.py tests/tui/test_services_gauntlet.py tests/test_registry_loader.py tests/tui/test_pilot_wizard.py tests/tui/test_pilot_selection_custom.py tests/tui/test_services_about.py tests/tui/test_pilot_nav_shell.py tests/tui/test_pilot_env_check.py tests/tui/test_pilot_selection.py -q`
-> **271 passed, 0 failed** (150.03s; the original 260 + the 11 phase-10-added tests now inside covered files). Named must-have lane
`-k "full_loop or disabled_entry_stays or tracer_land or decode_policy or metric_registry_parity"` -> **6 passed**. 420411e's fixture-staged
pins are part of the covered state this digest attests.

**Cross-phase warning (phase-10 scope, NOT a phase-9 gap):** the 3 red tests — `test_overlay_flips_missing_presence_to_present_and_back`, `test_mismatch_and_failed_entries_never_flip_presence`, `test_live_flip_through_the_app_event_forward` — were introduced by phase-10 commit f417862 and stale-dated by phase-10's own baseline refresh 2f7211d: their fixture helper `_committed_missing_dataset_keys()` asserts the committed n_audit carries missing keys, and the R-03 refresh made it 50 records / 0 missing (verified by direct parse). Deterministic root cause, no phase-9 surface involved; the fix (stage a missing-key fixture instead of reading the committed baseline) belongs to a phase-10 follow-up. Any "full suite green at HEAD" claim predating 2f7211d is stale — these three are red at `26280d5`.
**Resolution (2026-10-13, `84b0fcf`):** closed by 420411e (fixture-staged n_audit / refresh-stable pins, 8 tests) and 84b0fcf (DATA.md provenance appendix restored after the R-03 refresh). Re-run at `84b0fcf`: the trio passes (3 passed, 1.14s); `test_pilot_selection.py` 31/31 (22.69s); full `pytest tests/tui -q` 627 passed / 0 failed. The advisory is discharged.

### Fingerprint refresh

`covered_files` unchanged (the same 35-file phase-9 surface — the earlier "36" in this section was a count typo; recomputed via `gsd-tools verification fingerprint`):

`covered_digest: "v3:sha256:a3d9fe54c5faad43a602a04cc43a7615023776ebb6313fc656382f69ceb0b122"` *(refreshed 2026-10-13T00:18Z over the 84b0fcf code state; supersedes the 26280d5-pinned `v3:sha256:95a3dfb5...` digest, which attested the pre-420411e surface and is preserved in git history at commit d97ccc7)*

420411e's fixture-staged pins in `tests/tui/test_pilot_selection.py` and `tests/tui/test_pilot_selection_custom.py` are now part of the covered state this digest attests — correct: they pin phase-9-adjacent behavior, and the digest-refresh re-run above proves the entire covered surface green at that state (271/271).

**Verdict: passed.** All five SCs still hold at HEAD; the two UAT items remain discharged (09-UAT.md, 2/2, 2026-10-12); no regression on any phase-9 must-have; the one finding is a phase-10 test-baseline staleness recorded in `advisory:`.

---

_Re-verified: 2026-10-13T00:18:15Z (local 2026-10-13; digest refreshed over the 84b0fcf code state)_
_Verifier: Claude (gsd-verifier, #4682 stale-refresh route)_
