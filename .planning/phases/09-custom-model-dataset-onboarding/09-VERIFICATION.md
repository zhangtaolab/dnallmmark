---
phase: 09-custom-model-dataset-onboarding
verified: 2026-10-12T11:13:37Z
status: human_needed
score: 5/5 must-haves verified
covered_files: [".planning/phases/09-custom-model-dataset-onboarding/09-01-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-01-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-02-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-02-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-03-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-03-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-04-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-04-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-05-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-05-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-06-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-06-SUMMARY.md", "pipeline/registry_loader.py", "schemas/custom_registry.json", "tests/test_registry_loader.py", "tests/tui/test_pilot_env_check.py", "tests/tui/test_pilot_nav_shell.py", "tests/tui/test_pilot_selection.py", "tests/tui/test_pilot_selection_custom.py", "tests/tui/test_pilot_wizard.py", "tests/tui/test_services_about.py", "tests/tui/test_services_custom_entries.py", "tests/tui/test_services_custom_validation.py", "tests/tui/test_services_gauntlet.py", "tui/app.py", "tui/screens/about.py", "tui/screens/env_check.py", "tui/screens/selection.py", "tui/screens/wizard.py", "tui/services/about.py", "tui/services/custom_entries.py", "tui/services/custom_validation.py", "tui/services/gauntlet.py", "tui/strings.py", "tui/styles.tcss"]
covered_digest: "v3:sha256:f5d773e8159c72dd37f459157385f6530b35f5097490a4a1c9ce4e4a66678b8d"
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
| Full phase test surface (10 files: services, gauntlet, registry loader, Pilot wizard/selection/nav/env/about) | `.venv/bin/pytest tests/tui/test_services_custom_entries.py tests/tui/test_services_custom_validation.py tests/tui/test_services_gauntlet.py tests/test_registry_loader.py tests/tui/test_pilot_wizard.py tests/tui/test_pilot_selection_custom.py tests/tui/test_services_about.py tests/tui/test_pilot_nav_shell.py tests/tui/test_pilot_env_check.py tests/tui/test_pilot_selection.py -q` | 260 passed in 147.76s | ✓ PASS |
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
