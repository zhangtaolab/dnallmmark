---
phase: 09-custom-model-dataset-onboarding
verified: 2026-10-17T07:50:05Z
status: passed
score: 5/5 must-haves verified (1 dataset-half truth overridden by maintainer acceptance 2026-10-14)
covered_files: [".planning/phases/09-custom-model-dataset-onboarding/09-01-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-01-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-02-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-02-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-03-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-03-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-04-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-04-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-05-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-05-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-06-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-06-SUMMARY.md", "pipeline/registry_loader.py", "schemas/custom_registry.json", "tests/test_registry_loader.py", "tests/tui/test_pilot_env_check.py", "tests/tui/test_pilot_nav_shell.py", "tests/tui/test_pilot_selection.py", "tests/tui/test_pilot_selection_custom.py", "tests/tui/test_pilot_wizard.py", "tests/tui/test_services_about.py", "tests/tui/test_services_custom_entries.py", "tests/tui/test_services_custom_validation.py", "tests/tui/test_services_gauntlet.py", "tui/app.py", "tui/screens/about.py", "tui/screens/env_check.py", "tui/screens/selection.py", "tui/screens/wizard.py", "tui/services/about.py", "tui/services/custom_entries.py", "tui/services/custom_validation.py", "tui/services/gauntlet.py", "tui/strings.py", "tui/styles.tcss"]
covered_digest: "v3:sha256:23e1c517c1a54e86031220eb626ca852d98297936d481f02b0682eece0bbd9f2"
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions: []
overrides_applied: 1
overrides:
  - must_have: "SC5: landed custom entries carry a visible custom marker in both lists and can be individually enabled/disabled (dataset half)"
    reason: "Maintainer's locked 2026-10-14 slot-split ruling (slot 2 = models only, slot 3 = datasets only); dataset enable/disable surface and per-row marker consciously removed, flagged in 261014-mlc-SUMMARY maintainer-facing item 3; service-tier capability and export retained"
    accepted_by: "Tao Zhang"
    accepted_at: "2026-10-14T14:50:00Z"
    acceptance_channel: "interactive ruling during 2026-10-14 verification-refresh session (option: 接受 override)"
advisory:
  - finding: "WR-01 (09 review): ExitModal renders the attached sweep's progress counts under the launcher root's name (tui/app.py)"
    category: other
    reason: "Post-phase-9 surface (Phase-12 D-06 exit modal + monitor attach); no phase-9 SC covers the exit modal; open in 09-REVIEW-DISPOSITION.md — fix belongs to that queue, not this phase. The klw batch's 08-review WR-03 fix (attached_extra joining the multi form, app.py this delta) reshapes the modal further: a CLI-launched attached running root now joins the multi-root naming form; the disposition row remains open until triaged there"
    evidence_status: "deterministic: code-traced in 09-REVIEW.md; app.py +134/-12 delta this round read hunk-by-hunk (kill worker, ExitKillsDone, multi-form join, ctrl+c Input delegation — none touches the phase-9 nav-shell or registry surfaces)"
  - finding: "WR-02 (09 review): slot-1 storage overview runs load_state() + Path.exists() stats synchronously on the event loop (tui/screens/env_check.py storage_rows) — the D-03 worker-discipline class"
    category: other
    reason: "The storage-overview feature is quick-261014-f4w scope riding a phase-9 covered file; no phase-9 SC covers env-check I/O discipline; open in the disposition queue. The klw batch's env_check.py delta (+10, 08-review IN-03) adds only the synchronous _check_in_flight set in action_refresh — storage_rows untouched"
    evidence_status: "deterministic: env_check.py delta read this pass (single hunk, action_refresh flag only); storage_rows delegation unchanged"
  - finding: "WR-03 (09 review): _manual_landing_path reads run-config state on the event loop inside the d handler (tui/screens/selection.py) — same D-03 class"
    category: other
    reason: "The d model-download lane is quick-261014-mlc scope; no phase-9 SC covers the download lane; open in the disposition queue"
    evidence_status: "deterministic: selection.py delta this round read in full — only apply_queue_progress changed (the 08-review IN-01 store-ordering fix); _manual_landing_path untouched"
  - finding: "CR-01 (09 review, status changed this round): schemas/custom_registry.json optional-fields vs pipeline hard-index seam — the model-loop consumer sites are NOW FIXED by 6e331d3 (07-CR-01): Model_name falls back to the registry key (run_finetune.py:1015) and Mean_token_length to 1 (:1035), AST-pinned by test_minimal_custom_entry_reads_are_guarded (green this pass); disposition ledger records CR-01 fixed. Residual sibling sites (dataset-side length at :1336, Train/Dev/Test reads) remain unguarded — explicitly adjudicated maintainer-ruled W4 in the Phase-7 round-3 verification (855202e), not a phase-9 or phase-7 must-have breach: the crash class requires minimal hand-written entries; wizard-landed entries stamp every field (Pitfall 6/11)"
    category: architectural
    reason: "The schema/loader pair is byte-stable across this delta (zero-byte diff re-verified); the fix landed pipeline-side in the Phase-7 covered set with its own AST contract test; the phase-9 gauntlet/schema/wizard path is unchanged. Residual tracked in the Phase-7 lane (07-REVIEW-DISPOSITION W4) and cross-referenced here so nothing is silently dropped"
    evidence_status: "deterministic: run_finetune.py delta read hunk-by-hunk this pass; named pin test run green this pass; Phase-7 round-3 residual adjudication read"
  - finding: "IN-01 (09 review): six dead SEL_ constants remain in tui/strings.py — SEL_COL_TASK, SEL_COL_CATEGORY, SEL_COL_METRIC, SEL_COL_PRESENCE, SEL_PRESENCE_PRESENT, SEL_PRESENCE_MISSING (the old slot-3 dataset-table column labels). NOTE: distinct from the 08-review IN-01 (apply_queue_progress) the klw batch fixed — strings.py is byte-identical this delta, so these stay dead"
    category: other
    reason: "Cosmetic dead code; zero functional impact; open in the disposition queue. Cross-file consumer grep re-run this pass: 0 consumers outside strings.py for all six"
    evidence_status: "deterministic: cross-file consumer grep zero this pass; strings.py zero-byte diff since round-2"
  - finding: "IN-02 (09 review): tests pin committed-data counts (59/60 officials, index 38) in tests/tui/test_pilot_selection_custom.py — break on any compat-map data refresh"
    category: other
    reason: "The class persists: assertions re-read this pass (:589 == 60, :593 == 59, :904 index 38); tests are green at HEAD (full-suite 1F/1867P known-good, the single failure machine-local); the risk remains that a future data commit turns CI red for a non-defect, contrary to the repo's R-03 pin-structure-not-counts rule; open in the disposition queue"
    evidence_status: "deterministic: assertions read this pass; this round's additive test (dataset-kind tick) does not touch the pins"
  - finding: "IN-03 (09 review): stale 'seven kernel ids' comment at tests/tui/test_pilot_env_check.py:92 (it is eight since 261014-dcl)"
    category: other
    reason: "Comment-only staleness; open in the disposition queue; the klw batch's +40 to this file (08-review IN-03 flag test) did not fix it"
    evidence_status: "deterministic: read this pass; kernel count is 8"
  - finding: "DNR-27 (standing): WizardModal's all-six bindings render show=False (wizard.py:564-576) — the dnr 27-modal audit flags it NEEDS-MAINTAINER-RULING on keycap-visibility grounds"
    category: other
    reason: "A discoverability finding, not a semantic change: wizard.py is byte-stable across this delta (zero-byte diff verified this pass; the binding set is exactly what the 09-04/09-05 plans built and what the phase-9 SCs verified); the cancel/advance affordances live in the step-view copy by design. The ruling request is recorded in the 261017-dnr quick summary and awaits the maintainer; no phase-9 SC covers footer keycap visibility"
    evidence_status: "deterministic: wizard.py zero-byte diff since round-2; dnr audit row 27 carried"
behavior_unverified: 0
---

# Phase 9: Custom Model & Dataset Onboarding (自定义接入向导) Verification Report

**Phase Goal:** Operators can bring their own model and dataset into the benchmark entirely from the console, with official registries provably untouched — guided wizards collect the full entry into user-owned custom registries, fool-proofing validation collects every field problem in one fail-fast report before anything is written, and an entry lands only after passing the real gauntlet (dry-run precheck + audit reconciliation) with entry-level rollback when anything fails
**Verified:** 2026-10-17T07:50:05Z (micro re-verification at HEAD `6bb768f`)
**Status:** passed
**Re-verification:** Yes — fifth refresh since the 2026-10-13 initial pass. Refresh 1 (c700a41) found the SC5 dataset-half gap; maintainer override accepted 2026-10-14T14:50Z. Refresh 2 (646bcd5) covered the phases-10/11 delta. Refresh 3 (3040add) covered the hhx/c4j/ehc/a4f delta. Refresh 4 (round-2, tree 0672992, committed 46b898a) covered the live-feedback quicks + eea data-chain + compat v1.3. This micro refresh covers 46b898a..6bb768f = the quick-261017-klw fix batch only (commits 06d2679, 0d02e18, 6e331d3 + docs). The phase-9 cores — tui/services/custom_entries.py, custom_validation.py, gauntlet.py, tui/screens/wizard.py, tui/screens/data_manager.py, pipeline/registry_loader.py, schemas/custom_registry.json, tui/strings.py, tui/styles.tcss, about.py (both), and 8 of the 11 covered test files — are byte-stable across the entire delta (zero-byte diff verified this pass). The delta's covered-set footprint is 5 files from the klw TUI commits: tui/app.py (+134/−12, exit-channel: WR-02/WR-03-of-08 kill worker + attached-root multi-form + ctrl+c Input delegation), tui/screens/selection.py (+12/−1, IN-01-of-08 apply_queue_progress store-ordering fix), tui/screens/env_check.py (+10, IN-03-of-08 synchronous in-flight flag), and two additive covered tests pinning those fixes. No hunk touches any phase-9 SC surface. pipeline/models_info.json and datasets_info.json are byte-identical across the delta. All five SCs re-verified against the current on-disk state; 3 named behavioral tests re-run green this pass. Zero regressions.

**Delta-scope note (brief correction):** the refresh brief characterized the covered-set delta as "selection.py change ONLY". The verifiable delta is larger — 5 covered files — because the brief counted only the 08-review IN-01 selection.py fix and omitted the 06d2679 app.py exit-channel commit and the env_check/test additions from the same klw batch. Every extra hunk was read and adjudicated this pass (none touches a phase-9 SC surface); the conclusion is unchanged, but the report records the true delta.

## Goal Achievement

### Observable Truths

Merged must-haves: the five ROADMAP Success Criteria (the contract), cross-checked against the six PLAN frontmatter truth blocks. Every plan truth maps into one of the five SCs.

| # | Truth | Status | Evidence (current codebase, 6bb768f) |
| --- | ------- | ---------- | -------------- |
| 1 | SC1: one action from the model list opens the custom-model wizard; a validated submission lands in `~/.config/dnallmmark/custom_models.json` and the model appears via the overlay; `pipeline/models_info.json` never written | ✓ VERIFIED | Slot-2 `w` (tui/screens/selection.py:1358 `Binding("w", "open_wizard")`) → `action_open_wizard` (:1891, models-kind constant per the slot split, cursor-custom prefill) → `CustomOnboardingBackend` (:603, `build_wizard` over the REAL services — validator over live registry reads, land/undo/import/export seams bound to custom_entries_service). Landing writes through `settings.atomic_write` → `custom_models.json` (custom_entries.py:209 land). Official registries: models_info.json and datasets_info.json byte-identical across 46b898a..6bb768f (zero-byte diff verified this pass), counts 59 models / 50 datasets, zero TUI write paths (every models_info/datasets_info reference in tui/ is a constant, load, or docstring — write-pattern grep 0 hits, re-audited this pass). Behavioral, re-run green this pass: `test_full_loop_models_wizard_lands_badges_counts_and_disables` (2-test batch passed in 3.83s — asserts official bytes unchanged, badge/count/disable/loader-drop). selection.py's delta (apply_queue_progress only) sits in the download-queue surface, below and apart from every SC1 seam |
| 2 | SC2: same for datasets from the dataset list — landing in `~/.config/dnallmmark/custom_datasets.json`, `pipeline/datasets_info.json` never written | ✓ VERIFIED | data_manager.py byte-stable across the delta (zero-byte diff): slot-3 `w` → `action_open_wizard` → `build_wizard(kind="datasets")` → same store → `custom_datasets.json`. Overlay visibility holds at the registry tier; the per-row presentation is the overridden SC5 dataset half. Official zero-touch shares Truth 1's byte-diff evidence. Dataset-side behavioral pin stands in the known-good full suite at this HEAD (full 1F/1867P, the single failure machine-local) |
| 3 | SC3: submission blocked until validation passes; collect-all fail-fast one-pass report (required/type/enum/collisions vs official AND custom/path existence/split parseability/rows>0/label column/metric-in-registry), every problem itemized | ✓ VERIFIED | `tui/services/custom_validation.py` and `tui/screens/wizard.py` both byte-stable across the delta (zero-byte diff): `validate_model_candidate`/`validate_dataset_candidate` collect `(field_key, message)` pairs in field-definition order; `METRIC_REGISTRY` parity-locked to `SUITE_CANONICAL`; wizard `_submit` runs the injected validator, `_write_report` renders the numbered collect-all report and NOTHING is applied; a clean pass alone enters the gauntlet phase. Collect-all discipline and METRIC_REGISTRY parity pins stand green in the known-good suite; the call-time i18n re-derivation pin likewise |
| 4 | SC4: after submission the automatic gauntlet runs (dry-run precheck + audit reconciliation); any failure reported prominently, failed entry never lands, entry-level revert, no half-written state | ✓ VERIFIED | `tui/services/gauntlet.py` and the wizard's land-only-on-all-✓ handler both byte-stable across the delta (zero-byte diff): dry-run leg invokes `run_sweep.py --dry-run` as LIST argv with staged overlay env; audit leg stages candidate-only registry and parses `n_audit.json`; the wizard lands only on `if message.ok:` through the injected land seam (the panel's ONLY write call site); session undo intact. Real-subprocess pins stand green in the known-good suite at this HEAD. The run_finetune.py delta (07-CR-01 guarded reads) is downstream of the gauntlet and closes a crash class — it cannot weaken SC4 |
| 5 | SC5: landed customs carry a visible marker distinct from official in both lists, individually enable/disable, export as the share unit; official registries and existing test suite stay green and untouched | ✓ PASSED (override) | **Models half fully intact and re-verified on the current tree**: `◇` badge renders via `S.SEL_CUSTOM_BADGE` + `S.SEL_DISABLED_SUFFIX` in the custom-key cell (selection.py:1035-1040, re-read this pass at current line numbers); `e` toggle (selection.py:1359 binding → `action_toggle_enabled` :1916 → `set_enabled` custom_entries.py:269 through the store's atomic seam); count segment (`_update_status_line` :1746); loader-skip (registry_loader.py:160-169, byte-stable). Wizard `f`/`o` export/import seams intact (wizard.py byte-stable). Behavioral, re-run green this pass in the same 2-test batch (badge + suffix + count + loader-drop asserted). **Dataset half overridden**: the maintainer's locked 2026-10-14 slot-split ruling consciously removed the dataset enable/disable console surface and per-row marker (service-tier `set_enabled` + loader-skip for both kinds, export, and the aggregate count segment all remain, test-pinned) — see the frontmatter `overrides` block, accepted by Tao Zhang 2026-10-14T14:50:00Z, carried verbatim. Official registries byte-identical across the delta (Truth 1); suite green at the known-good baseline (full 1F/1867P at HEAD 6bb768f, the single failure a machine-local member; node 26/26; ruff+ty green; goldens green) plus this pass's named tests |

**Score:** 5/5 truths verified (4 direct + 1 maintainer override; 0 present-but-behavior-unverified — every behavior-dependent truth (land-only-on-all-✓, undo rollback, loader-skip, collect-all ordering, render-time i18n re-derivation) has a passing behavioral test; the SC1 full-loop pin was re-run individually this pass, the remainder stand green in the known-good full suite at this HEAD)

### Advisory (New Scope, Unevidenced)

Carried review findings, re-evidenced this pass (statuses in the frontmatter `advisory:` block). One material status change: CR-01's model-loop consumer sites are now FIXED (6e331d3, AST-pinned, pin test green this pass), with the residual sibling sites adjudicated maintainer-ruled W4 in the Phase-7 round-3 lane.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | WR-01 (09) ExitModal naming (app.py) | other | post-phase-9 surface; disposition-open; this delta's exit-channel rework reshapes the modal again without a naming fix |
| 2 | WR-02 (09) env_check storage_rows sync IO | other | quick-261014-f4w scope riding a covered file; no phase-9 SC; this delta's env_check hunk (in-flight flag) does not touch it |
| 3 | WR-03 (09) selection _manual_landing_path event-loop read | other | quick-261014-mlc scope; no phase-9 SC; selection.py delta read in full — untouched |
| 4 | CR-01 (09) schema-optional vs hard-index seam — model-loop sites FIXED this delta; residual dataset-side sites maintainer-ruled (Phase-7 W4) | architectural | crash class requires minimal hand-written entries; wizard lands stamp every field; schema/gauntlet path byte-stable |
| 5 | IN-01 (09) six dead SEL_ constants (strings.py) | other | cosmetic; 0 consumers re-verified; strings.py byte-identical (distinct from the 08-review IN-01 fixed this delta) |
| 6 | IN-02 (09) pinned data counts in tests | other | green at HEAD; R-03 class risk; disposition-open |
| 7 | IN-03 (09) stale "seven kernel ids" comment | other | comment-only; disposition-open |
| 8 | DNR-27 wizard keycap visibility ruling | other | discoverability finding on a byte-stable surface; awaits maintainer |

### Required Artifacts

All artifacts from the six PLANs exist and are substantive at 6bb768f. The plans use plain-string artifact lists (`verify.artifacts` does not parse them), so levels were verified manually: exists ✓, substantive ✓ (no stubs; TBD/FIXME/XXX grep zero across all covered implementation files including every delta file this pass), wired ✓ (below).

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| tui/services/custom_entries.py | store: read/land/undo/set_enabled/import/export | ✓ VERIFIED | byte-stable across the delta (zero-byte diff 46b898a..6bb768f); read_entries :172, land :209, undo :246, set_enabled :269, read_import_candidates :296, export_registry :339 — all through settings.atomic_write |
| tui/services/custom_validation.py | collect-all validator + METRIC_REGISTRY | ✓ VERIFIED | byte-stable; validators, METRIC_REGISTRY :91 |
| schemas/custom_registry.json | entry-shape schema for imports | ✓ VERIFIED | byte-stable; carries the CR-01 optional-fields seam (advisory #4 — consumer sites now guarded, residual Phase-7 W4) |
| tui/services/gauntlet.py | two-leg subprocess gauntlet | ✓ VERIFIED | byte-stable; real `subprocess.run` seam :161 |
| pipeline/registry_loader.py | D-09 enabled:false skip | ✓ VERIFIED | byte-stable; :160-169 skip intact (collision loop precedes the skip) |
| tui/screens/wizard.py | 4-step modal + report + gauntlet panel + import/export | ✓ VERIFIED | byte-stable across the entire delta; `_submit`, `_write_report`, land-only-on-all-✓, undo, `f`/`o` seams all as at round-2 |
| tui/screens/selection.py | w entry, badge, e toggle, count, prefill | ✓ VERIFIED | delta = apply_queue_progress store-ordering fix only (+12/−1, the 08-review IN-01 — download-queue hygiene below the (model, downloading) guard, RED-first tested); all models-side SC surfaces re-verified at current line numbers (w :1358, e :1359, action_open_wizard :1891 with prefill, action_toggle_enabled :1916, badge cell :1035-1040 via S.SEL_CUSTOM_BADGE, count :1746, CustomOnboardingBackend :603) |
| tui/screens/data_manager.py | slot-3 dataset wizard entry | ✓ VERIFIED | byte-stable; dataset-wizard seam stands green in the known-good suite |
| tui/app.py | 09-03 nav shell host | ✓ VERIFIED | delta = exit-channel only (kill worker + ExitKillsDone, attached-root multi-form join, ctrl+c Input-copy delegation — all Phase-12/08-review surfaces); zero official-registry write paths (re-audited this pass); nav-shell tests byte-stable and green in the known-good suite |
| tui/screens/about.py, tui/services/about.py, env_check.py, strings.py, styles.tcss | 09-03 nav shell + about + i18n | ✓ VERIFIED | about/strings/styles byte-stable this delta; env_check.py delta = the synchronous `_check_in_flight` set in `action_refresh` (+10, 08-review IN-03) — a refresh-discipline fix with its own new Pilot test; no phase-9 SC covers the env refresh path |
| 11 phase test files (incl. test_language_rederivation.py pinning the wizard) | behavioral evidence | ✓ VERIFIED | all exist; two covered test files gained additive pins this delta (dataset-kind tick residue; refresh in-flight flag) — both green; suite green at the known-good 1F/1867P baseline (machine-local member) |

### Key Link Verification

All links byte-anchored this pass: the service/wizard/data_manager/registry_loader ends are byte-identical to round-2 (zero-byte diff), and the selection-side seams were re-read at current line numbers.

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| slot-2 `w` | model wizard | `action_open_wizard` → `build_wizard(kind="models")` over real services | ✓ WIRED | selection.py:1358 → :1891 → backend :603; full-loop Pilot green this pass |
| slot-3 `w` | dataset wizard | `data_manager.action_open_wizard` → `build_wizard(kind="datasets")` | ✓ WIRED | data_manager.py byte-stable; seam test green in the known-good suite |
| wizard all-✓ | custom_entries.land | injected land seam → atomic write → overlay-visible | ✓ WIRED | wizard.py byte-stable; the panel's only write call site; full-loop test green this pass |
| gauntlet service | run_sweep.py --dry-run / audit | LIST argv subprocess + pinned env → artifact parse | ✓ WIRED | gauntlet.py byte-stable; real-subprocess pins green in the known-good suite |
| registry_loader enabled-skip | every registry consumer | `entry.get("enabled") is False` (:160-169) | ✓ WIRED | byte-stable; loader-drop asserted in the green full-loop test |
| slot-2 `e` | custom_entries.set_enabled | atomic seam → next load skips | ✓ WIRED (models — the overridden scope) | selection.py:1359 → :1916 → store :269; disable/suffix/loader-drop asserted in the green full-loop test |
| wizard `o`/`f` | export_registry / import+per-entry gauntlet | kind-bound seams from build_wizard | ✓ WIRED | wizard.py byte-stable; seams bound in the backend |
| wizard labels | active language | `S.*` read at CALL time (`_kind_spec`/`_model_steps`/`_dataset_steps`/`_quirk_fields`) | ✓ WIRED | wizard.py byte-stable; re-derivation pin green in the known-good suite |
| wizard cancel | ConfirmModal base | esc-confirm push | ✓ WIRED | wizard.py byte-stable; the app.py exit rework does not touch ConfirmModal |

### Data-Flow Trace (Level 4)

Unchanged from round-2 (all sources byte-stable); re-anchored where the delta touched a file.

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| selection custom_status | overlay merge + management read | registry_loader + custom_entries.read_entries | ✓ | ✓ FLOWING |
| gauntlet verdicts | parsed artifacts | sweep_manifest.json / n_audit.json from real subprocesses | ✓ | ✓ FLOWING |
| wizard report | problems list | validate_*_candidate over injected ValidationSources | ✓ | ✓ FLOWING |
| wizard labels/steps | S.* constants | strings.py `_t()` bilingual registry read at access time | ✓ | ✓ FLOWING |
| badge/count/toggle | S.SEL_CUSTOM_BADGE / SEL_DISABLED_SUFFIX / custom_status | strings.py + management read | ✓ | ✓ FLOWING (full-loop test asserts the rendered badge + suffix + count line — green this pass) |
| selection download-cell percent/speed | `_live_percents`/`_live_speeds` (delta site) | queue events via `apply_queue_progress` | ✓ | ✓ FLOWING (now stored only for passing (model, downloading) ticks — the delta's hygiene fix, pinned by the new test, green this pass) |

No static returns, hardcoded verdicts, or mock-fed renders on production paths.

### Behavioral Spot-Checks

Full suite NOT re-run this pass (given known-good gates at HEAD 6bb768f: full suite 1F/1867P with the single failure a machine-local member; node 26/26; ruff+ty green; goldens green). Named tests re-run directly this pass:

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Delta site: dataset-kind tick stores no live-dict residue (08-review IN-01 fix) | `.venv/bin/python -m pytest tests/tui/test_pilot_selection_custom.py::test_dataset_kind_tick_stores_no_live_dict_residue -q` (2-test batch) | **2 passed in 3.83s** (batch with the full-loop pin) | ✓ PASS |
| Full-loop models wizard (land → badge → counts → disable; official bytes unchanged; loader drops disabled) | `.venv/bin/python -m pytest tests/tui/test_pilot_selection_custom.py::test_full_loop_models_wizard_lands_badges_counts_and_disables -q` (batch) | **passed** (same batch; index pin 38 current) | ✓ PASS |
| CR-01 guarded-reads pin (run_finetune model-loop sites — the advisory's fix) | `.venv/bin/python -m pytest tests/test_run_finetune_contracts.py::test_minimal_custom_entry_reads_are_guarded -q` | **1 passed in 0.02s** | ✓ PASS |
| Official registries untouched | `git diff 46b898a..6bb768f -- pipeline/models_info.json pipeline/datasets_info.json` → zero-byte; write-path audit over tui/ (0 write-pattern hits); counts 59/50 | clean | ✓ PASS |

### Probe Execution

No `probe-*.sh` scripts declared or present; not a probe-based phase. N/A.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| CUST-01 | 09-01, 09-03, 09-04, 09-05, 09-06 | model wizard → custom registry, official untouched, quirk checklist | ✓ SATISFIED | Truth 1 |
| CUST-02 | 09-01, 09-03, 09-04, 09-05, 09-06 | dataset wizard → custom registry | ✓ SATISFIED | Truth 2 |
| CUST-03 | 09-01, 09-04 | collect-all fail-fast field validation | ✓ SATISFIED | Truth 3 |
| CUST-04 | 09-02, 09-05 | gauntlet dry-run + audit, entry-level rollback | ✓ SATISFIED | Truth 4 |
| CUST-06 | 09-01, 09-02, 09-06 | badge / enable-disable / export share unit | ✓ SATISFIED (models full; dataset marker/toggle surface under the maintainer override — service tier + export retained) | Truth 5 |

No orphaned requirements: REQUIREMENTS.md maps exactly CUST-01/02/03/04/06 to Phase 9 (all marked Complete; CUST-05 = Phase 7). The union of the six plans' `requirements:` frontmatter re-read this pass is exactly {CUST-01, CUST-02, CUST-03, CUST-04, CUST-06} — no ID unmapped, no plan claims a Phase-7 ID.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | Zero TBD/FIXME/XXX across all covered implementation files this pass (incl. all five delta files: app.py, env_check.py, selection.py, and the two covered test files) | — | none |

### Human Verification Required

None. The original items were closed by the recorded UAT (09-UAT.md, status passed, 2026-10-12: live console wizard loop driven in the real app; cross-machine share-unit round trip via pinned XDG roots), the removed dataset e-toggle/marker surface is settled by the maintainer's recorded override (a decision, not a re-test), and this refresh introduced no behavior-unverified truths: every behavior-dependent truth (land-only-on-all-✓, undo rollback, loader-skip, collect-all ordering, render-time i18n re-derivation) has a passing behavioral test — the SC1 full-loop pin re-run this pass, the remainder standing green in the known-good full suite at this exact HEAD. The dnr audit's WizardModal keycap-visibility question (advisory #8) is a maintainer aesthetic ruling on a byte-stable surface, not a re-test of a phase-9 SC.

### Gaps Summary

No gaps. All five SCs hold at 6bb768f: the phase-9 cores (custom_entries.py, custom_validation.py, gauntlet.py, wizard.py, data_manager.py, registry_loader.py, custom_registry.json, strings.py, styles.tcss, about) are byte-stable across the entire 46b898a..6bb768f delta (zero-byte diff verified this pass), and the delta's five covered-file changes were read hunk-by-hunk and adjudicated: selection.py's apply_queue_progress store-ordering fix (download-queue hygiene, its own new RED-first pin — green), env_check.py's synchronous in-flight flag (refresh discipline, its own new pin), app.py's exit-channel rework (Phase-12/08-review surfaces), and two additive covered tests — none touches a phase-9 SC seam. The official registries are byte-identical across the delta — the strongest form of "provably untouched". The SC5 dataset half stands under the maintainer override carried verbatim in the frontmatter. The eight advisory findings (WR-01..03, IN-01..03, the CR-01 seam — materially improved this delta: model-loop sites fixed and AST-pinned, residual dataset-side sites adjudicated maintainer-ruled W4 in the Phase-7 round-3 lane — and the DNR-27 wizard-keycap-visibility ruling request) remain real, evidenced, and non-blocking: six are disposition-open in 09-REVIEW-DISPOSITION.md, CR-01's residual is tracked in the Phase-7 lane, and DNR-27 awaits the maintainer ruling recorded in the 261017-dnr quick summary — none breaches a phase-9 SC. The klw delta on the codebase was itself code-reviewed before landing (the quick's fix batch, RED-first discipline per its summary).

---

_Verified: 2026-10-17T07:50:05Z_
_Verifier: Claude (gsd-verifier)_
