---
phase: 09-custom-model-dataset-onboarding
verified: 2026-10-16T07:09:36Z
status: passed
score: 5/5 must-haves verified (1 dataset-half truth overridden by maintainer acceptance 2026-10-14)
overrides_applied: 1
overrides:
  - must_have: "SC5: landed custom entries carry a visible custom marker in both lists and can be individually enabled/disabled (dataset half)"
    reason: "Maintainer's locked 2026-10-14 slot-split ruling (slot 2 = models only, slot 3 = datasets only); dataset enable/disable surface and per-row marker consciously removed, flagged in 261014-mlc-SUMMARY maintainer-facing item 3; service-tier capability and export retained"
    accepted_by: "Tao Zhang"
    accepted_at: "2026-10-14T14:50:00Z"
    acceptance_channel: "interactive ruling during 2026-10-14 verification-refresh session (option: 接受 override)"
covered_files: [".planning/phases/09-custom-model-dataset-onboarding/09-01-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-01-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-02-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-02-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-03-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-03-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-04-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-04-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-05-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-05-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-06-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-06-SUMMARY.md", "pipeline/registry_loader.py", "schemas/custom_registry.json", "tests/test_registry_loader.py", "tests/tui/test_pilot_env_check.py", "tests/tui/test_pilot_nav_shell.py", "tests/tui/test_pilot_selection.py", "tests/tui/test_pilot_selection_custom.py", "tests/tui/test_pilot_wizard.py", "tests/tui/test_services_about.py", "tests/tui/test_services_custom_entries.py", "tests/tui/test_services_custom_validation.py", "tests/tui/test_services_gauntlet.py", "tui/app.py", "tui/screens/about.py", "tui/screens/env_check.py", "tui/screens/selection.py", "tui/screens/wizard.py", "tui/services/about.py", "tui/services/custom_entries.py", "tui/services/custom_validation.py", "tui/services/gauntlet.py", "tui/strings.py", "tui/styles.tcss"]
covered_digest: "v3:sha256:8f81bbd71badc980a1f29dfafe84013b42e30b6380a45499f3eb872df1124222"
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions: []
advisory:
  - finding: "WR-01: ExitModal renders the attached sweep's progress counts under the launcher root's name (tui/app.py)"
    category: other
    reason: "Post-phase-9 surface (Phase-12 D-06 exit modal + monitor attach); no phase-9 SC covers the exit modal; open in 09-REVIEW-DISPOSITION.md — fix belongs to that queue, not this phase. Note: the 11-08 WR-05 multi-root rework reshaped this modal (ExitModal class still at app.py:165; every live root named; done/total dropped in the multi-root form) but the 09 disposition row remains open until triaged there"
    evidence_status: "deterministic: code-traced in 09-REVIEW.md; modal present at app.py:165-199 this pass (HEAD 3040add)"
  - finding: "WR-02: slot-1 storage overview runs load_state() + Path.exists() stats synchronously on the event loop (tui/screens/env_check.py storage_rows) — the D-03 worker-discipline class"
    category: other
    reason: "The storage-overview feature is quick-261014-f4w scope riding a phase-9 covered file; no phase-9 SC covers env-check I/O discipline; open in the disposition queue. The a4f fail-closed rework of env_check.py did not change the storage-overview delegation pattern"
    evidence_status: "deterministic: storage_rows → run_config_service.storage_overview() delegation read this pass (env_check.py:172-178)"
  - finding: "WR-03: _manual_landing_path reads run-config state on the event loop inside the d handler (tui/screens/selection.py) — same D-03 class, delta-introduced"
    category: other
    reason: "The d model-download lane is quick-261014-mlc scope; no phase-9 SC covers the download lane; open in the disposition queue"
    evidence_status: "deterministic: _manual_landing_path at selection.py:1891, called synchronously in the d handler at :1946 this pass"
  - finding: "CR-01 (standing, from Phase 7): schemas/custom_registry.json declares Mean_token_length/Model_name (model_entry) and length (dataset_entry) OPTIONAL while pipeline/run_finetune.py hard-indexes them (lines 1008, 1021, 1322) and pipeline/registry_loader.py injects no defaults — a custom entry omitting them can pass schema + wizard validation + the gauntlet and KeyError at first training step"
    category: architectural
    reason: "Assessed against the phase-9 must-haves with direct evidence: SC3's enumerated contract (required/type/enum/collisions/path/splits/rows/label-column/metric — the checks the validator KNOWS about) is complete and collect-all; field-completeness-vs-pipeline-hard-index is not an enumerated phase-9 check, and the gauntlet (dry-run + audit, as SC4 defines it) cannot exercise the training loop. The schema's optionality is the shared phase-7/9 contract; the defect is a cross-phase seam already deterministically reproduced and adjudicated a non-falsifying Warning in the Phase-7 verification and queued for a /gsd-quick schema-side fix. Not a phase-9 gap; tracked there. Schema byte-stable across the entire delta — seam unchanged at 3040add."
    evidence_status: "deterministic: schema required-arrays re-parsed this pass (model_entry requires only Model_path/size (M)/type/Tokenizer; dataset_entry omits length); run_finetune.py:1008/1021/1322 hard-index confirmed; registry_loader has no defaulting for these fields"
  - finding: "IN-01: six dead SEL_ constants remain in tui/strings.py after the slot split — post-ehc-rewrite the dead set is SEL_COL_TASK, SEL_COL_CATEGORY, SEL_COL_METRIC, SEL_COL_PRESENCE, SEL_PRESENCE_PRESENT, SEL_PRESENCE_MISSING (the old slot-3 dataset-table column labels)"
    category: other
    reason: "Cosmetic dead code; zero functional impact; open in the disposition queue. The ehc bilingual strings rewrite did not remove them (grep-verified zero consumers outside strings.py this pass)"
    evidence_status: "deterministic: cross-file consumer grep zero this pass"
  - finding: "IN-02: tests pin committed-data counts (59/60 officials, index 36) in tests/tui/test_pilot_selection_custom.py — break on any compat-map data refresh"
    category: other
    reason: "Tests pass at HEAD (59/50 is current); the risk is future data commits turning CI red for a non-defect, contrary to the repo's R-03 pin-structure-not-counts rule; open in the disposition queue"
    evidence_status: "deterministic: assertions read this pass (:589 == 60, :593 == 59, :904 index 36); tests green in the given 1808-run and in this pass's named-test runs"
  - finding: "IN-03: stale 'seven kernel ids' comment at tests/tui/test_pilot_env_check.py:92 (it is eight since 261014-dcl)"
    category: other
    reason: "Comment-only staleness; open in the disposition queue"
    evidence_status: "deterministic: read this pass; kernel count is 8"
behavior_unverified: 0
---

# Phase 9: Custom Model & Dataset Onboarding (自定义接入向导) Verification Report

**Phase Goal:** Operators can bring their own model and dataset into the benchmark entirely from the console, with official registries provably untouched — guided wizards collect the full entry into user-owned custom registries, fool-proofing validation collects every field problem in one fail-fast report before anything is written, and an entry lands only after passing the real gauntlet (dry-run precheck + audit reconciliation) with entry-level rollback when anything fails
**Verified:** 2026-10-16T07:09:36Z (stale-refresh re-verification at HEAD `3040add`)
**Status:** passed
**Re-verification:** Yes — third refresh since the 2026-10-13 pass. Refresh 1 (c700a41) found the SC5 dataset-half gap; maintainer override accepted 2026-10-14T14:50Z. Refresh 2 (646bcd5) covered the phases-10/11 delta. This refresh was triggered by the 646bcd5..3040add delta touching eleven covered files via quick-261015-c4j (slot rework), quick-261015-ehc (bilingual strings registry), quick-261016-a4f (env_check fail-closed), quick-261016-hhx (render-time i18n re-derivation incl. the wizard's module-level KINDS freeze removal), plus the pex/demo and golden-refresh commits. The phase-9 service cores (custom_entries.py, custom_validation.py, gauntlet.py, registry_loader.py, custom_registry.json) are byte-stable across the entire delta (absent from `git diff --stat 646bcd5..HEAD`); the TUI surface files moved but every phase-9 SC surface was re-verified against the current on-disk state with named behavioral tests re-run this pass. Zero regressions found.

## Goal Achievement

### Observable Truths

Merged must-haves: the five ROADMAP Success Criteria (the contract), cross-checked against the six PLAN frontmatter truth blocks. Every plan truth maps into one of the five SCs.

| # | Truth | Status | Evidence (current codebase, 3040add) |
| --- | ------- | ---------- | -------------- |
| 1 | SC1: one action from the model list opens the custom-model wizard; a validated submission lands in `~/.config/dnallmmark/custom_models.json` and the model appears via the overlay; `pipeline/models_info.json` never written | ✓ VERIFIED | Slot-2 `w` (tui/screens/selection.py:1312 `Binding("w", "open_wizard")`) → `action_open_wizard` (:1838) → `CustomOnboardingBackend.build_wizard(kind="models", prefill, on_changed)` (:1857-1861); the backend (:603-738) composes the REAL services — validator over real `ValidationSources` from live registry reads (:684-704), `land`/`undo`/`import`/`export` seams bound to `custom_entries_service` (:706-737). Landing writes through `settings.atomic_write` → `custom_registry_path` → `custom_models.json` (custom_entries.py:209 land, KIND map :89-90). Official registries: both files git-clean at 3040add, counts 59 models / 50 datasets, zero TUI write paths (every models_info/datasets_info reference in tui/ is a path constant, load, or docstring — audited file-by-file this pass). Behavioral, re-run green this pass: `test_full_loop_models_wizard_lands_badges_counts_and_disables` (1 passed, 3.74s — asserts `official.read_bytes() == before`) |
| 2 | SC2: same for datasets from the dataset list — landing in `~/.config/dnallmmark/custom_datasets.json`, `pipeline/datasets_info.json` never written | ✓ VERIFIED | Slot-3 `w` (tui/screens/data_manager.py:563) → `action_open_wizard` (:1274) → `service.build_wizard(kind="datasets", ...)` (:1291-1292) → same store → `custom_datasets.json`. Behavioral, re-run green this pass: `test_w_opens_the_dataset_wizard_and_reload_wires_through` (1 passed). Overlay visibility holds at the registry tier (custom dataset keys merge into `SelectionData.dataset_entries` → marks/matrix/status); the per-row presentation is the overridden SC5 dataset half. Official zero-touch shares Truth 1's evidence |
| 3 | SC3: submission blocked until validation passes; collect-all fail-fast one-pass report (required/type/enum/collisions vs official AND custom/path existence/split parseability/rows>0/label column/metric-in-registry), every problem itemized | ✓ VERIFIED | `tui/services/custom_validation.py` byte-stable across the delta: `validate_model_candidate`/`validate_dataset_candidate` (:193/:237) collect `(field_key, message)` pairs; `METRIC_REGISTRY` (:91) parity-locked to `SUITE_CANONICAL`. The wizard's submit gate survives the hhx i18n re-derivation intact: `_submit` (wizard.py:957-979) runs the injected validator, problems render as the numbered collect-all report via `_write_report` (:981-990) and NOTHING is applied; a clean pass alone enters the gauntlet phase. The re-derivation itself (module-level KINDS freeze removed; `_kind_spec`/`_model_steps`/`_dataset_steps`/`_quirk_fields` read `S.*` at CALL time, wizard.py:186-292) is behaviorally pinned. Behavioral, re-run green this pass: `test_three_simultaneous_defects_yield_three_ordered_problems` + `test_metric_registry_parity_with_suite_canonical` (2 passed) and `test_kind_spec_reads_active_language` (1 passed — the CR-01 hhx pin: a freshly built kind spec reads the ACTIVE language) |
| 4 | SC4: after submission the automatic gauntlet runs (dry-run precheck + audit reconciliation); any failure reported prominently, failed entry never lands, entry-level revert, no half-written state | ✓ VERIFIED | `tui/services/gauntlet.py` byte-stable across the delta: dry-run leg invokes `run_sweep.py --dry-run` as LIST argv with staged overlay env (:251), audit leg stages candidate-only registry with absolute `Dataset_path` and parses `n_audit.json`; the real subprocess seam is `subprocess.run(argv, check=False, **kwargs)` (:161) with the injectable runner seam. The wizard lands only on all-✓: `on_wizard_modal_gauntlet_entry_done` (wizard.py:1263-1311) — `if message.ok:` → the injected land seam (the panel's ONLY write call site); any ✗ renders the failure banner and nothing lands; stale-run drops prevent an abandoned run from backfilling (:1272). Session undo: `action_undo_landed` (:1396-1412) → injected undo seam. Behavioral, re-run green this pass: `test_real_subprocess_dry_run_passes_for_synthetic_model_candidate` + `test_committed_audit_artifacts_byte_unchanged_across_real_gauntlet` (each 1 passed — the Pitfall-1 committed-artifact byte-unchanged gate over a real audit subprocess) |
| 5 | SC5: landed customs carry a visible marker distinct from official in both lists, individually enable/disable, export as the share unit; official registries and existing test suite stay green and untouched | ✓ PASSED (override) | **Models half fully intact and re-verified on the current tree**: `◇` badge (selection.py:1035/:1038), `（已停用）` suffix (:1040), `e` toggle (selection.py:1313 binding → `action_toggle_enabled` :1863-1887 → `set_enabled` through the store's atomic seam, honest official-row no-op toast), count segment (`_update_status_line` :1693-1717, official/custom split, zero-customs byte-identical Phase-8 line), loader-skip (registry_loader.py:160-169, `entry.get("enabled") is False`). Wizard `o`/`f` export/import bindings intact (wizard.py:571-572 → :1504/:1525). **Dataset half overridden**: the maintainer's locked 2026-10-14 slot-split ruling consciously removed the dataset enable/disable console surface and per-row marker (service-tier `set_enabled` + loader-skip for both kinds, export, and the aggregate count segment all remain, test-pinned) — see the frontmatter `overrides` block, accepted by Tao Zhang 2026-10-14T14:50:00Z, carried verbatim. Official registries green and untouched (Truth 1); suite green (given 1808-passed baseline + this pass's named tests) |

**Score:** 5/5 truths verified (4 direct + 1 maintainer override; 0 present-but-behavior-unverified — every behavior-dependent truth (land-only-on-all-✓, undo rollback, loader-skip, collect-all ordering, render-time i18n re-derivation) has a passing behavioral test, re-run individually this pass)

### Required Artifacts

All artifacts from the six PLANs exist and are substantive at 3040add. The plans use plain-string artifact lists (`verify.artifacts` does not parse them), so levels were verified manually: exists ✓, substantive ✓ (no stubs; TBD/FIXME/XXX grep zero across all covered implementation files this pass), wired ✓ (below).

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| tui/services/custom_entries.py | store: read/land/undo/set_enabled/import/export | ✓ VERIFIED | byte-stable across the delta (absent from 646bcd5..3040add); read_entries :172, land :209, undo :246, set_enabled :269, read_import_candidates :296, export_registry :339 — all through settings.atomic_write |
| tui/services/custom_validation.py | collect-all validator + METRIC_REGISTRY | ✓ VERIFIED | byte-stable; validators :193/:237, METRIC_REGISTRY :91 |
| schemas/custom_registry.json | entry-shape schema for imports | ✓ VERIFIED | byte-stable; carries the CR-01 optional-fields seam (advisory #4) |
| tui/services/gauntlet.py | two-leg subprocess gauntlet | ✓ VERIFIED | byte-stable; real `subprocess.run` seam :161 |
| pipeline/registry_loader.py | D-09 enabled:false skip | ✓ VERIFIED | :160-169 skip intact (collision loop precedes the skip) |
| tui/screens/wizard.py | 4-step modal + report + gauntlet panel + import/export | ✓ VERIFIED | moved by hhx (389 delta lines: call-time i18n re-derivation, CR-01) — the full SC3/SC4 flow re-verified this pass: `_submit` :957-979, `_write_report` :981-990, land-only-on-all-✓ :1263-1311, undo :1396-1412, `f`/`o` :571-572/:1504/:1525; Pilot suite 42/42 green this pass (109s) |
| tui/screens/selection.py | w entry, badge, e toggle, count, prefill | ✓ VERIFIED | moved by c4j/ehc (530 delta lines: slot rework + bilingual registry) — all models-side surfaces re-verified at current line numbers (w :1312/:1838, e :1313/:1863, badge :1035-1040, count :1693-1717, prefill :1849-1856, CustomOnboardingBackend.build_wizard :633-738) |
| tui/screens/data_manager.py | slot-3 dataset wizard entry | ✓ VERIFIED | `w` :563 → :1274 → kind="datasets" :1291-1292; dataset-wizard seam test green this pass |
| tui/app.py | 09-03 nav shell host | ✓ VERIFIED | delta = multi-root ExitModal rework + demo/i18n follow-ups; zero official-registry write paths; nav-shell tests green in the given suite |
| tui/screens/about.py, tui/services/about.py, env_check.py, strings.py, styles.tcss | 09-03 nav shell + about + i18n | ✓ VERIFIED | about/env_check/styles moved by the a4f/ehc/pex quicks (fail-closed + bilingual registry + demo surfaces — reviewed and dispositioned fixed in 07/08-REVIEW); strings.py now the `_t()` bilingual registry read at access time with the full WIZ_* family intact (WIZM/WIZD_STEPS :805-820, field labels :667-738, quirk trio :822-826, problem lines :657-661) |
| 11 phase test files (incl. test_language_rederivation.py pinning the wizard) | behavioral evidence | ✓ VERIFIED | all exist; suite green at the given 1808-passed baseline with exactly the pinned 7F membership; 7 named phase tests + the 42-test wizard Pilot suite re-run green this pass |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| slot-2 `w` | model wizard | `action_open_wizard` → `build_wizard(kind="models")` over real services | ✓ WIRED | selection.py:1312 → :1838 → :1857-1861 → backend :633-738; full-loop Pilot green this pass |
| slot-3 `w` | dataset wizard | `data_manager.action_open_wizard` → `build_wizard(kind="datasets")` | ✓ WIRED | data_manager.py:563 → :1274 → :1291-1292; seam test green this pass |
| wizard all-✓ | custom_entries.land | injected land seam → atomic write → overlay-visible | ✓ WIRED | wizard.py:1263-1311 (the panel's only write call site); full-loop test green |
| gauntlet service | run_sweep.py --dry-run / audit | LIST argv subprocess + pinned env → artifact parse | ✓ WIRED | gauntlet.py:161 real subprocess seam; both real-subprocess tests green this pass |
| registry_loader enabled-skip | every registry consumer | `entry.get("enabled") is False` (:160-169) | ✓ WIRED | loader-skip test green in the given suite; skip logic read this pass |
| slot-2 `e` | custom_entries.set_enabled | atomic seam → next load skips | ✓ WIRED (models — the overridden scope) | selection.py:1313 → :1863-1887 → store :269; disable/re-enable/no-op Pilot tests green in the given suite |
| wizard `o`/`f` | export_registry / import+per-entry gauntlet | kind-bound seams from build_wizard | ✓ WIRED | wizard.py:571-572/:1504/:1525; backend seams :730-737 |
| wizard labels | active language | `S.*` read at CALL time (`_kind_spec`/`_model_steps`/`_dataset_steps`/`_quirk_fields`) | ✓ WIRED | wizard.py:186-292; `test_kind_spec_reads_active_language` green this pass |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| selection custom_status | overlay merge + management read | registry_loader + custom_entries.read_entries | ✓ | ✓ FLOWING |
| gauntlet verdicts | parsed artifacts | sweep_manifest.json / n_audit.json from real subprocesses | ✓ | ✓ FLOWING (real-subprocess tests green this pass) |
| wizard report | problems list | validate_*_candidate over injected ValidationSources | ✓ | ✓ FLOWING |
| wizard labels/steps | S.* constants | strings.py `_t()` bilingual registry read at access time | ✓ | ✓ FLOWING (no import-time language freeze — CR-01 pin green) |

No static returns, hardcoded verdicts, or mock-fed renders on production paths.

### Behavioral Spot-Checks

Full suite NOT re-run this pass (fresh recorded evidence: 1808 passed at exactly the pinned 7F baseline membership, incl. 10 new i18n/fail-closed tests; node 26/26; ruff+ty green; 9 golden SVGs unmodified). Single named tests + one bounded suite re-run directly this pass:

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full-loop models wizard (land → badge → counts → disable; official untouched) | `.venv/bin/python -m pytest tests/tui/test_pilot_selection_custom.py::test_full_loop_models_wizard_lands_badges_counts_and_disables -q` | **1 passed in 3.74s** | ✓ PASS |
| Wizard render-time i18n re-derivation (hhx CR-01 pin) | `.venv/bin/python -m pytest tests/tui/test_language_rederivation.py::test_kind_spec_reads_active_language -q` | **1 passed in 0.11s** | ✓ PASS |
| Slot-3 dataset wizard seam | `.venv/bin/python -m pytest tests/tui/test_pilot_data_manager.py::test_w_opens_the_dataset_wizard_and_reload_wires_through -q` | **1 passed** | ✓ PASS |
| Collect-all discipline (3 simultaneous defects → 3 ordered problems) | `... test_services_custom_validation.py::test_three_simultaneous_defects_yield_three_ordered_problems -q` | **1 passed** | ✓ PASS |
| METRIC_REGISTRY = SUITE_CANONICAL parity | `... test_services_custom_validation.py::test_metric_registry_parity_with_suite_canonical -q` | **1 passed** | ✓ PASS |
| Real-subprocess dry-run gauntlet leg | `... test_services_gauntlet.py::test_real_subprocess_dry_run_passes_for_synthetic_model_candidate -q` | **1 passed** | ✓ PASS |
| Committed-artifact byte-unchanged across a real audit gauntlet | `... test_services_gauntlet.py::test_committed_audit_artifacts_byte_unchanged_across_real_gauntlet -v` | **1 passed** | ✓ PASS |
| Wizard Pilot suite (changed wizard.py, full flow) | `.venv/bin/python -m pytest tests/tui/test_pilot_wizard.py -q` | **42 passed in 109.07s** | ✓ PASS |
| Official registries untouched | `git status` clean on both files; write-path audit over tui/ (every models_info/datasets_info reference is a constant/load/docstring); counts 59/50 | clean | ✓ PASS |

### Probe Execution

No `probe-*.sh` scripts declared or present; not a probe-based phase. N/A.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| CUST-01 | 09-01, 09-03, 09-04, 09-05, 09-06 | model wizard → custom registry, official untouched, quirk checklist | ✓ SATISFIED | Truth 1 |
| CUST-02 | 09-01, 09-03, 09-04, 09-05, 09-06 | dataset wizard → custom registry | ✓ SATISFIED | Truth 2 |
| CUST-03 | 09-01, 09-04 | collect-all fail-fast field validation | ✓ SATISFIED | Truth 3 |
| CUST-04 | 09-02, 09-05 | gauntlet dry-run + audit, entry-level rollback | ✓ SATISFIED | Truth 4 |
| CUST-06 | 09-01, 09-02, 09-06 | badge / enable/disable / export share unit | ✓ SATISFIED (models full; dataset marker/toggle surface under the maintainer override — service tier + export retained) | Truth 5 |

No orphaned requirements: REQUIREMENTS.md maps exactly CUST-01/02/03/04/06 to Phase 9 (all marked Complete; CUST-05 = Phase 7). The union of the six plans' `requirements:` frontmatter is exactly {CUST-01, CUST-02, CUST-03, CUST-04, CUST-06} — no ID unmapped, no plan claims a Phase-7 ID.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | Zero TBD/FIXME/XXX across all covered implementation files this pass (incl. all delta files); the "placeholder" grep hits in wizard.py/selection.py are Input-widget hint parameters (`placeholder=`), legitimate UI affordances, not stubs | — | none |

### Human Verification Required

None. The original items were closed by the recorded UAT (09-UAT.md, status passed, 2026-10-12: live console wizard loop driven in the real app; cross-machine share-unit round trip via pinned XDG roots), the removed dataset e-toggle/marker surface is settled by the maintainer's recorded override (a decision, not a re-test), and this refresh introduced no behavior-unverified truths: every behavior-dependent truth (land-only-on-all-✓, undo rollback, loader-skip, collect-all ordering, render-time i18n re-derivation) has a passing behavioral test re-run this pass.

### Gaps Summary

No gaps. All five SCs hold at 3040add: four verified directly — the phase-9 service cores are byte-stable across the entire 646bcd5..3040add delta, and the moved TUI surfaces (wizard.py i18n re-derivation, selection.py slot rework + bilingual registry) were re-verified line-by-line with 7 named behavioral tests plus the 42-test wizard Pilot suite re-run green this pass — and the SC5 dataset half stands under the maintainer override carried verbatim in the frontmatter. Official registries are provably untouched (git-clean, 59/50, zero TUI write paths, byte-unchanged assertion in the green full-loop test). The seven advisory findings (WR-01..03, IN-01..03, CR-01 cross-phase schema seam) remain real, evidenced, and non-blocking: six are disposition-open in 09-REVIEW-DISPOSITION.md (6 open / 11 total recorded there), and CR-01's seam was re-confirmed deterministically this pass (schema required-arrays vs run_finetune.py:1008/1021/1322 hard-index) with its schema-side fix still queued — none breaches a phase-9 SC. The delta on the stale set was itself code-reviewed (08-REVIEW.md superset diff base 2341f1c + 07-REVIEW.md for the env_check cluster) with all findings dispositioned fixed via quicks a4f + hhx.

---

_Verified: 2026-10-16T07:09:36Z_
_Verifier: Claude (gsd-verifier)_
