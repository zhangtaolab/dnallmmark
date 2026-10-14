---
phase: 09-custom-model-dataset-onboarding
verified: 2026-10-14T17:42:19Z
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
covered_digest: "v3:sha256:d6dc044b38c13761af7e7725bcade01d5bd5d3bc4a14a5c17c6ed7c1b9b8187e"
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions: []
advisory:
  - finding: "WR-01: ExitModal renders the attached sweep's progress counts under the launcher root's name (tui/app.py)"
    category: other
    reason: "Post-phase-9 surface (Phase-12 D-06 exit modal + monitor attach); no phase-9 SC covers the exit modal; open in 09-REVIEW-DISPOSITION.md — fix belongs to that queue, not this phase. Note: the 11-08 WR-05 multi-root rework (7e5af59) reshaped this modal (every live root named; done/total dropped in the multi-root form) but the 09 disposition row remains open until triaged there"
    evidence_status: "deterministic: code-traced in 09-REVIEW.md (delta review be62a5a); modal rework read this pass (app.py:179-230)"
  - finding: "WR-02: slot-1 storage overview runs load_state() + five Path.exists() stats synchronously on the event loop (tui/screens/env_check.py:613-648) — the D-03 worker-discipline class"
    category: other
    reason: "The storage-overview feature is quick-261014-f4w scope riding a phase-9 covered file; no phase-9 SC covers env-check I/O discipline; open in the disposition queue"
    evidence_status: "deterministic: code-traced in 09-REVIEW.md; env_check.py byte-stable since be595a3 (diff 0)"
  - finding: "WR-03: _manual_landing_path reads run-config state on the event loop inside the d handler (tui/screens/selection.py) — same D-03 class, delta-introduced"
    category: other
    reason: "The d model-download lane is quick-261014-mlc scope; no phase-9 SC covers the download lane; open in the disposition queue"
    evidence_status: "deterministic: code-traced in 09-REVIEW.md; selection.py byte-stable since be595a3 (diff 0)"
  - finding: "CR-01 (standing, from Phase 7): schemas/custom_registry.json declares Mean_token_length/Model_name (model_entry) and length (dataset_entry) OPTIONAL while pipeline/run_finetune.py hard-indexes them (lines 1008, 1021, 1322) and pipeline/registry_loader.py injects no defaults — a custom entry omitting them can pass schema + wizard validation + the gauntlet and KeyError at first training step"
    category: architectural
    reason: "Assessed against the phase-9 must-haves with direct evidence: SC3's enumerated contract (required/type/enum/collisions/path/splits/rows/label-column/metric — the checks the validator KNOWS about) is complete and collect-all; field-completeness-vs-pipeline-hard-index is not an enumerated phase-9 check, and the gauntlet (dry-run + audit, as SC4 defines it) cannot exercise the training loop. The schema's optionality is the shared phase-7/9 contract; the defect is a cross-phase seam already deterministically reproduced and adjudicated a non-falsifying Warning in the Phase-7 verification and queued for a /gsd-quick schema-side fix. Not a phase-9 gap; tracked there. Schema byte-stable since 517f821 — seam unchanged at dd16ad6."
    evidence_status: "deterministic: schema required-arrays parsed this pass (model_entry requires only Model_path/size (M)/type/Tokenizer; dataset_entry omits length); run_finetune.py:1008/1021/1322 hard-index confirmed; registry_loader has no defaulting for these fields"
  - finding: "IN-01: six dead SEL_ constants + stale dataset-table comments in tui/strings.py after the slot split"
    category: other
    reason: "Cosmetic dead code with misleading comments; zero functional impact; open in the disposition queue. strings.py's dd16ad6 delta (LNC_EXIT_MESSAGE_MULTI, MON_RERUN_* amendments) touches none of them"
    evidence_status: "deterministic: grep-verified zero consumers in 09-REVIEW.md; delta diff read this pass"
  - finding: "IN-02: tests pin committed-data counts (36 adapted) in tests/tui/test_pilot_selection.py and test_pilot_selection_custom.py — break on any compat-map data refresh"
    category: other
    reason: "Tests pass at HEAD (36 is current); the risk is future data commits turning CI red for a non-defect, contrary to the repo's R-03 pin-structure-not-counts rule; open in the disposition queue"
    evidence_status: "deterministic: assertions read this pass; 285/285 phase tests green at dd16ad6"
  - finding: "IN-03: stale 'seven kernel ids' comment at tests/tui/test_pilot_env_check.py:90 (it is eight since 261014-dcl)"
    category: other
    reason: "Comment-only staleness; open in the disposition queue"
    evidence_status: "deterministic: read this pass"
behavior_unverified: 0
---

# Phase 9: Custom Model & Dataset Onboarding (自定义接入向导) Verification Report

**Phase Goal:** Operators can bring their own model and dataset into the benchmark entirely from the console, with official registries provably untouched — guided wizards collect the full entry into user-owned custom registries, fool-proofing validation collects every field problem in one fail-fast report before anything is written, and an entry lands only after passing the real gauntlet (dry-run precheck + audit reconciliation) with entry-level rollback when anything fails
**Verified:** 2026-10-14T17:42:19Z (convergence stale-refresh re-verification at HEAD `dd16ad6`)
**Status:** passed
**Re-verification:** Yes — second refresh since the 2026-10-13 pass. Refresh 1 (be62a5a, 2026-10-14T14:47Z) found the SC5 dataset-half gap; the maintainer accepted the override at 14:50Z (be595a3, status passed). This refresh was triggered by the phases-10/11 delta be595a3..dd16ad6 touching two covered files: `tui/app.py` (WR-05 multi-root ExitModal + the CJK-free docstring fix, 7e5af59/320cb97 — Phase-11 exit-modal surface, no phase-9 SC) and `tui/strings.py` (LNC_EXIT_MESSAGE_MULTI + MON_RERUN_* copy amendments — Phase-11 monitor/exit copy, no WIZ_/SEL_ phase-9 strings touched). All eight phase-9 core files are byte-stable across the delta (diff 0): custom_entries.py, custom_validation.py, gauntlet.py, wizard.py, registry_loader.py, custom_registry.json, selection.py, data_manager.py. Zero regressions found.

## Goal Achievement

### Observable Truths

Merged must-haves: the five ROADMAP Success Criteria (the contract), cross-checked against the six PLAN frontmatter truth blocks. Every plan truth maps into one of the five SCs.

| # | Truth | Status | Evidence (current codebase, dd16ad6) |
| --- | ------- | ---------- | -------------- |
| 1 | SC1: one action from the model list opens the custom-model wizard; a validated submission lands in `~/.config/dnallmmark/custom_models.json` and the model appears via the overlay; `pipeline/models_info.json` never written | ✓ VERIFIED | Slot-2 `w` (tui/screens/selection.py:1279 `Binding("w", "open_wizard")`) → `action_open_wizard` (:1704) → `build_wizard(kind="models", prefill, on_changed)` (:1723-1726) composing the REAL services: validators over real `ValidationSources` from live registry reads, `land`/`undo`/`import`/`export` seams bound to `custom_entries_service`. selection.py byte-stable through the entire phases-10/11 delta (diff 0 vs be595a3). Landing writes through `settings.atomic_write` → `custom_registry_path` → `custom_models.json` (custom_entries.py:209/:431). Official registries: both files git-clean at dd16ad6, counts 59 models / 50 datasets (post-ir9 maintainer data edit), zero TUI write paths (grep over tui/ for writes to models_info/datasets_info: none). Behavioral: `test_full_loop_models_wizard_lands_badges_counts_and_disables` (asserts `official.read_bytes() == before`) green in the 285-test run below |
| 2 | SC2: same for datasets from the dataset list — landing in `~/.config/dnallmmark/custom_datasets.json`, `pipeline/datasets_info.json` never written | ✓ VERIFIED | Slot-3 `w` (tui/screens/data_manager.py:597 `Binding("w", "open_wizard")`) → `action_open_wizard` (:1253) → lazy `CustomOnboardingBackend` import (:1267-1269, the 09-06 cycle-break pattern) → `build_wizard(kind="datasets", prefill=None, on_changed=self._reload_snapshot)` (:1270-1273) → same store → `custom_datasets.json`. data_manager.py byte-stable since be595a3. Behavioral: `test_w_opens_the_dataset_wizard_and_reload_wires_through` (tests/tui/test_pilot_data_manager.py:2549) re-run green 1/1 at dd16ad6; wizard-suite dataset-kind legs green in the 285. Official zero-touch shares Truth 1's evidence. Overlay visibility holds at the registry tier (custom dataset keys merge into `SelectionData.dataset_entries` → marks/matrix/status); the per-row presentation is the overridden SC5 dataset half |
| 3 | SC3: submission blocked until validation passes; collect-all fail-fast one-pass report (required/type/enum/collisions vs official AND custom/path existence/split parseability/rows>0/label column/metric-in-registry), every problem itemized | ✓ VERIFIED | `tui/services/custom_validation.py` byte-stable since the phase-9 review fixes (last commit b0e2812; diff 0 vs be595a3): `validate_model_candidate`/`validate_dataset_candidate` (:193/:237) collect `(field_key, message)` pairs through the `_check_*` family; `METRIC_REGISTRY` parity-locked to `SUITE_CANONICAL`; collision check covers official + existing custom keys. Behavioral, green in this pass's 285: `test_three_simultaneous_defects_yield_three_ordered_problems`, `test_metric_registry_parity_with_suite_canonical`, dataset collect-all span and field-order pins. Wizard renders the numbered report and hands off only on clean pass (`_phase` state machine; wizard.py byte-stable since d6f2a2c) |
| 4 | SC4: after submission the automatic gauntlet runs (dry-run precheck + audit reconciliation); any failure reported prominently, failed entry never lands, entry-level revert, no half-written state | ✓ VERIFIED | `tui/services/gauntlet.py` byte-stable since the decode-policy follow-up (last commit 46ddd37; diff 0 vs be595a3): dry-run leg invokes `run_sweep.py --dry-run` as LIST argv with staged overlay env; audit leg stages candidate-only registry with absolute `Dataset_path`, all-temp outputs; pass parsed from `sweep_manifest.json` / `n_audit.json`; the real subprocess seam is `subprocess.run(argv, check=False, **kwargs)` (:161) with the injectable runner seam for tests. Gauntlet imports only `read_entries` (read-only store seam); the wizard lands through injected `land`/`undo` seams only after all-✓ (wizard.py :1286-1325 land-only-on-all-✓, :1417 undo); per-entry import rollback covered. Behavioral, green in this pass's 285: `test_real_subprocess_dry_run_passes_for_synthetic_model_candidate`, `test_committed_audit_artifacts_byte_unchanged_across_real_gauntlet`, timeout tests, dataset-kind gauntlet legs |
| 5 | SC5: landed customs carry a visible marker distinct from official in both lists, individually enable/disable, export as the share unit; official registries and existing test suite stay green and untouched | ✓ PASSED (override) | **Models half fully intact and re-confirmed byte-stable**: `◇` badge (SEL_CUSTOM_BADGE, strings.py:375 → selection.py:1030), `（已停用）` suffix (SEL_DISABLED_SUFFIX), `e` toggle (selection.py:1280 binding → `action_toggle_enabled` → `set_enabled("models", ...)` :1744), count segment (`_update_status_line` :1572-1593, official vs custom split), loader-skip (registry_loader.py:160-169, `entry.get("enabled") is False` — official entries unaffected). **Dataset half overridden**: the maintainer's locked 2026-10-14 slot-split ruling consciously removed the dataset enable/disable console surface and per-row marker (service-tier `set_enabled` + loader-skip for both kinds, export, and the aggregate count segment all remain, test-pinned) — see the frontmatter `overrides` block, accepted by Tao Zhang 2026-10-14T14:50:00Z, carried verbatim from be595a3. Official registries green and untouched (Truth 1); test suite green (285/285 below) |

**Score:** 5/5 truths verified (4 direct + 1 maintainer override; 0 present-but-behavior-unverified — the prior cross-machine share-unit item was closed by the recorded UAT, 09-UAT.md, passed 2026-10-12: machine-B pinned-root import ran the real gauntlet and landed)

### Required Artifacts

All artifacts from the six PLANs exist and are substantive at dd16ad6. Manual levels (the plans use plain-string artifact lists `verify.artifacts` does not parse): exists ✓, substantive ✓ (no stubs, no debt markers — TBD/FIXME/XXX grep zero across all covered implementation files this pass), wired ✓ (below).

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| tui/services/custom_entries.py | store: read/land/undo/set_enabled/import/export | ✓ VERIFIED | byte-stable since phase 9 (9d6bd75; diff 0 vs be595a3); all six ops + atomic write seam |
| tui/services/custom_validation.py | collect-all validator + METRIC_REGISTRY | ✓ VERIFIED | byte-stable since phase 9 (b0e2812; diff 0) |
| schemas/custom_registry.json | entry-shape schema for imports | ✓ VERIFIED | byte-stable since 517f821; carries the CR-01 optional-fields seam (advisory #4) |
| tui/services/gauntlet.py | two-leg subprocess gauntlet | ✓ VERIFIED | byte-stable since 46ddd37 (diff 0); real `subprocess.run` seam intact |
| pipeline/registry_loader.py | D-09 enabled:false skip | ✓ VERIFIED | :160-169 skip intact (diff 0); loader suite green in the 285 |
| tui/screens/wizard.py | 4-step modal + report + gauntlet panel + import/export | ✓ VERIFIED | byte-stable since d6f2a2c (diff 0) |
| tui/screens/selection.py | w entry, badge, e toggle, count, prefill | ✓ VERIFIED | byte-stable since 156e13d-era state (diff 0 vs be595a3); models-side w/badge/e/count intact |
| tui/screens/data_manager.py | slot-3 dataset wizard entry | ✓ VERIFIED | byte-stable (diff 0); `w` → kind="datasets" wired (:597, :1253-1273) |
| tui/app.py | 09-03 nav shell host | ✓ VERIFIED | delta = WR-05 multi-root ExitModal + CJK-free docstring only (Phase-11 surface); `test_app_module_carries_zero_chinese_literals` (env_check Pilot suite) green in the 285 — the i18n lock holds at dd16ad6 |
| tui/screens/about.py, tui/services/about.py, env_check.py, strings.py, styles.tcss | 09-03 nav shell + about + i18n | ✓ VERIFIED | about/env_check/styles byte-stable; strings.py delta = LNC_EXIT_MESSAGE_MULTI + MON_RERUN_* only (Phase-11 copy, no WIZ_/SEL_ strings touched); zero-Chinese-literals locks green |
| 10 phase test files | behavioral evidence | ✓ VERIFIED | 285 tests, all passing (152.60s) at dd16ad6 |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| slot-2 `w` | model wizard | `action_open_wizard` → `build_wizard(kind="models")` over real services | ✓ WIRED | selection.py:1279 → :1704 → :1723-1726; full-loop Pilot green in the 285 |
| slot-3 `w` | dataset wizard | `data_manager.action_open_wizard` → lazy `CustomOnboardingBackend` → `build_wizard(kind="datasets")` | ✓ WIRED | data_manager.py:597 → :1253-1273; `test_w_opens_the_dataset_wizard_and_reload_wires_through` green 1/1 this pass |
| wizard all-✓ | custom_entries.land | injected land seam → atomic write → overlay-visible | ✓ WIRED | wizard.py:1286-1325 land-only-on-all-✓; tracer + full-loop tests green in the 285 |
| gauntlet service | run_sweep.py --dry-run / audit | LIST argv subprocess + pinned env → artifact parse | ✓ WIRED | gauntlet.py:161 real subprocess seam; real-subprocess tests green in the 285 |
| registry_loader enabled-skip | every registry consumer | `entry.get("enabled") is False` (:160-169) | ✓ WIRED | loader-skip tests green in the 285 |
| slot-2 `e` | custom_entries.set_enabled | atomic seam → next load skips | ✓ WIRED (models — the overridden scope) | selection.py:1280 → :1744; dataset half under the maintainer override |
| wizard `o`/`f` | export_registry / import+per-entry gauntlet | kind-bound seams from build_wizard | ✓ WIRED | both kinds reachable (slot-2 wizard = models, slot-3 = datasets) |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| selection custom_status | overlay merge + management read | registry_loader + custom_entries.read_entries | ✓ | ✓ FLOWING |
| gauntlet verdicts | parsed artifacts | sweep_manifest.json / n_audit.json from real subprocesses | ✓ | ✓ FLOWING |
| wizard report | problems list | validate_*_candidate over injected ValidationSources | ✓ | ✓ FLOWING |
| slot-3 pane rows | presence_rows | official registry only (by design post-split) | ✓ | ✓ FLOWING (customs excluded by the overridden ruling, not a data disconnect) |

No static returns, hardcoded verdicts, or mock-fed renders on production paths.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full phase test surface (10 files) | `.venv/bin/python -m pytest tests/tui/test_services_custom_entries.py tests/tui/test_services_custom_validation.py tests/tui/test_services_gauntlet.py tests/test_registry_loader.py tests/tui/test_pilot_wizard.py tests/tui/test_pilot_selection_custom.py tests/tui/test_services_about.py tests/tui/test_pilot_nav_shell.py tests/tui/test_pilot_env_check.py tests/tui/test_pilot_selection.py -q` | **285 passed in 152.60s** (this pass, HEAD dd16ad6 — same count as refresh 1) | ✓ PASS |
| Slot-3 dataset wizard seam (single named test, outside the 10-file covered set) | `.venv/bin/python -m pytest tests/tui/test_pilot_data_manager.py::test_w_opens_the_dataset_wizard_and_reload_wires_through -q` | **1 passed in 0.50s** | ✓ PASS |
| Real-subprocess gauntlet legs + committed-artifact byte-unchanged | named tests within the 285 | passed | ✓ PASS |
| Full-loop models wizard (land → badge → counts → disable) | `test_full_loop_models_wizard_lands_badges_counts_and_disables` | passed | ✓ PASS |
| METRIC_REGISTRY = SUITE_CANONICAL parity | `test_metric_registry_parity_with_suite_canonical` | passed | ✓ PASS |
| app.py i18n lock at dd16ad6 (covered file touched by the delta) | `test_app_module_carries_zero_chinese_literals` (in the 285) | passed | ✓ PASS |
| Official registries untouched | `git status` clean on both files; TUI write-path grep zero; counts 59/50 | clean | ✓ PASS |
| Full-suite baseline (given, not re-run — background GPU smoke in flight; writes confined to pipeline/finetuned/smoke-2x2-261014 + pipeline/logs) | — | 7 failed / 1743 passed / 9 xfailed | ✓ PASS modulo documented baseline — same 7 documented failures as the ac26570 record (5 test_schemas + 1 test_determinism + 1 machine-state storage_overview-vs-pipeline/logs), none in phase-9 covered files, which are proven green directly above |

### Probe Execution

No `probe-*.sh` scripts declared or present; not a probe-based phase. N/A.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| CUST-01 | 09-01, 09-03, 09-04, 09-06 | model wizard → custom registry, official untouched, quirk checklist | ✓ SATISFIED | Truth 1 |
| CUST-02 | 09-01, 09-03, 09-04, 09-06 | dataset wizard → custom registry | ✓ SATISFIED | Truth 2 |
| CUST-03 | 09-01, 09-04 | collect-all fail-fast field validation | ✓ SATISFIED | Truth 3 |
| CUST-04 | 09-02, 09-05 | gauntlet dry-run + audit, entry-level rollback | ✓ SATISFIED | Truth 4 |
| CUST-06 | 09-01, 09-02, 09-06 | badge / enable/disable / export share unit | ✓ SATISFIED (models full; dataset marker/toggle surface under the maintainer override — service tier + export retained) | Truth 5 |

No orphaned requirements: REQUIREMENTS.md maps exactly CUST-01/02/03/04/06 to Phase 9 (CUST-05 = Phase 7).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | Zero TBD/FIXME/XXX across all covered implementation files this pass (incl. the delta files app.py, strings.py); prior PLACEHOLDER hits remain legitimate Input-widget hint constants and the self-annotated NAV_PLACEHOLDER_TOAST D-13 leftover (all six slots live) | — | none |

### Human Verification Required

None. The two original items were closed by the recorded UAT (09-UAT.md, status passed, 2026-10-12: live console wizard loop driven in the real app; cross-machine share-unit round trip via pinned XDG roots), and the one UAT flow the 2026-10-14 slot split removed (dataset e toggle / per-row marker) is settled by the maintainer's recorded override in the frontmatter — a decision, not a re-test. This refresh introduced no new behavior-unverified truths: every behavior-dependent truth (land-only-on-all-✓, undo rollback, loader-skip, collect-all ordering) has a passing behavioral test in the 285.

### Gaps Summary

No gaps. All five SCs hold at dd16ad6: four verified directly with byte-stable cores and a green 285-test phase surface (real-subprocess gauntlet legs, byte-unchanged committed artifacts, full-loop wizard, loader-skip, collect-all discipline, i18n locks including the delta-touched app.py), and the SC5 dataset half stands under the maintainer override carried verbatim in the frontmatter (service-tier set_enabled + loader-skip, export, and the aggregate count segment retained and test-pinned). Official registries are provably untouched (git-clean, 59/50, zero TUI write paths). The refresh's delta was confined to two covered files (app.py: Phase-11 WR-05 multi-root ExitModal + CJK docstring fix; strings.py: Phase-11 LNC/MON copy) — no phase-9 SC surface moved, and all eight phase-9 core files are byte-identical to the passed state be595a3. The seven advisory findings (WR-01..03, IN-01..03, CR-01 cross-phase schema seam) remain real, evidenced, and non-blocking: six are post-phase surfaces disposition-open in 09-REVIEW-DISPOSITION.md (6 open / 11 total recorded there), and CR-01's seam was re-confirmed deterministically this pass (schema required-arrays vs run_finetune.py:1008/1021/1322 hard-index) with its /gsd-quick schema-side fix still queued — none breaches a phase-9 SC.

---

_Verified: 2026-10-14T17:42:19Z_
_Verifier: Claude (gsd-verifier)_
