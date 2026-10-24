---
phase: 09-custom-model-dataset-onboarding
verified: 2026-10-19T12:13:51Z
status: passed
score: 5/5 must-haves verified (1 dataset-half truth overridden by maintainer acceptance 2026-10-14)
covered_files: [".planning/phases/09-custom-model-dataset-onboarding/09-01-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-01-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-02-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-02-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-03-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-03-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-04-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-04-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-05-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-05-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-06-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-06-SUMMARY.md", "pipeline/registry_loader.py", "schemas/custom_registry.json", "tests/test_registry_loader.py", "tests/tui/test_pilot_env_check.py", "tests/tui/test_pilot_nav_shell.py", "tests/tui/test_pilot_selection.py", "tests/tui/test_pilot_selection_custom.py", "tests/tui/test_pilot_wizard.py", "tests/tui/test_services_about.py", "tests/tui/test_services_custom_entries.py", "tests/tui/test_services_custom_validation.py", "tests/tui/test_services_gauntlet.py", "tui/app.py", "tui/screens/about.py", "tui/screens/data_manager.py", "tui/screens/env_check.py", "tui/screens/selection.py", "tui/screens/wizard.py", "tui/services/about.py", "tui/services/custom_entries.py", "tui/services/custom_validation.py", "tui/services/gauntlet.py", "tui/strings.py", "tui/styles.tcss"]
covered_digest: "v3:sha256:d0f98c9f2816d6d2f34da60a806c698a652e253e72f58bfd1f68125090903f44"
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
    reason: "Post-phase-9 surface (Phase-12 D-06 exit modal + monitor attach); no phase-9 SC covers the exit modal; open in 09-REVIEW-DISPOSITION.md. app.py was reshaped again across this delta (F10 exit ruling 261017-mad, f1/f2 help keys, monitor tabbed redesign, [e] resume / [d] delete history actions) without a naming fix; the disposition row stays open in that queue"
    evidence_status: "deterministic: app.py delta hunks surveyed this pass (@@-map over the +275/-x diff); every hunk is exit-key/help-row/monitor-nav scope; zero official-registry write paths re-audited"
  - finding: "WR-02 (09 review): slot-1 storage overview runs load_state() + Path.exists() stats synchronously on the event loop (tui/screens/env_check.py storage_rows) — the D-03 worker-discipline class"
    category: other
    reason: "The storage-overview feature is quick-261014-f4w scope riding a phase-9 covered file; no phase-9 SC covers env-check I/O discipline; open in the disposition queue. tui/screens/env_check.py is byte-stable across this entire delta (zero-byte diff re-verified this pass); only its Pilot test changed (help-row additions)"
    evidence_status: "deterministic: env_check.py absent from the 6bb768f..5783567 changed-file list; test delta read (help rows only)"
  - finding: "WR-03 (09 review): _manual_landing_path reads run-config state on the event loop inside the d handler (tui/screens/selection.py) — same D-03 class"
    category: other
    reason: "The d model-download lane is quick-261014-mlc scope; no phase-9 SC covers the download lane; open in the disposition queue. selection.py's delta this round is confined to LaunchConfirmModal's uppercase Y/N twin bindings (261018-08g SOAK-2/F3, +9 lines at :1261-1266) — _manual_landing_path untouched at :1953"
    evidence_status: "deterministic: selection.py delta read in full this pass (single hunk, LaunchConfirmModal only); site re-anchored at :1953"
  - finding: "CR-01 (09 review): schemas/custom_registry.json optional-fields vs pipeline hard-index seam — model-loop consumer sites fixed by 6e331d3 (07-CR-01) with the AST pin test_minimal_custom_entry_reads_are_guarded re-run GREEN this pass; residual sibling sites (dataset-side length, Train/Dev/Test reads) remain maintainer-ruled W4 in the Phase-7 round-3 lane"
    category: architectural
    reason: "The schema/loader pair is byte-stable across this delta (zero-byte diff re-verified); pipeline/run_finetune.py unchanged across this delta; the phase-9 gauntlet/schema/wizard path is unchanged. Residual tracked in the Phase-7 lane (07-REVIEW-DISPOSITION W4)"
    evidence_status: "deterministic: run_finetune.py absent from the delta changed-file list; named pin re-run green this pass (27-test batch)"
  - finding: "IN-01 (09 review): six dead SEL_ constants remain in tui/strings.py — SEL_COL_TASK, SEL_COL_CATEGORY, SEL_COL_METRIC, SEL_COL_PRESENCE, SEL_PRESENCE_PRESENT, SEL_PRESENCE_MISSING (the old slot-3 dataset-table column labels). strings.py gained +175/−68 this delta (exit-key copy, ABOUT_MILESTONE_STAGE reword, MON_* tabbed redesign) without touching them"
    category: other
    reason: "Cosmetic dead code; zero functional impact; open in the disposition queue. Cross-file consumer grep re-run this pass: 0 consumers outside strings.py for all six (constants verified present at :462-475)"
    evidence_status: "deterministic: cross-file consumer grep zero this pass; strings.py delta grepped for SEL_/WIZ/GAUNTLET/CUSTOM mutations — zero hits"
  - finding: "IN-02 (09 review): tests pin committed-data counts (59/60 officials, index 38) in tests/tui/test_pilot_selection_custom.py — break on any compat-map data refresh"
    category: other
    reason: "The class persists: test file byte-stable across this delta (absent from changed-file list); the full-loop pin re-run GREEN this pass (index 38 current); registries at 59 models / 50 datasets byte-identical; the R-03 pin-structure-not-counts risk remains open in the disposition queue"
    evidence_status: "deterministic: full-loop test green this pass; registry counts re-read (59/50)"
  - finding: "IN-03 (09 review): stale 'seven kernel ids' comment at tests/tui/test_pilot_env_check.py:92 (it is eight since 261014-dcl)"
    category: other
    reason: "Comment-only staleness; open in the disposition queue; this delta's +20 to the file (f10/f1/f2 help-row expectations) did not fix it — the comment still reads 'seven' at :92 this pass"
    evidence_status: "deterministic: re-read this pass; comment unchanged"
  - finding: "DNR-27 (standing): WizardModal's all-six bindings render show=False (wizard.py) — the dnr 27-modal audit flags it NEEDS-MAINTAINER-RULING on keycap-visibility grounds"
    category: other
    reason: "A discoverability finding, not a semantic change: wizard.py is byte-stable across this delta (zero-byte diff verified this pass); the binding set is exactly what the 09-04/09-05 plans built; the cancel/advance affordances live in the step-view copy by design. The ruling request remains with the maintainer; no phase-9 SC covers footer keycap visibility"
    evidence_status: "deterministic: wizard.py zero-byte diff since round-2; dnr audit row 27 carried"
behavior_unverified: 0
---

# Phase 9: Custom Model & Dataset Onboarding (自定义接入向导) Verification Report

**Phase Goal:** Operators can bring their own model and dataset into the benchmark entirely from the console, with official registries provably untouched — guided wizards collect the full entry into user-owned custom registries, fool-proofing validation collects every field problem in one fail-fast report before anything is written, and an entry lands only after passing the real gauntlet (dry-run precheck + audit reconciliation) with entry-level rollback when anything fails
**Verified:** 2026-10-19T12:13:51Z (stale refresh at HEAD `5783567`)
**Status:** passed
**Re-verification:** Yes — sixth refresh since the 2026-10-13 initial pass. Refresh 1 (c700a41) found the SC5 dataset-half gap; maintainer override accepted 2026-10-14T14:50Z. Refresh 2 (646bcd5) covered the phases-10/11 delta. Refresh 3 (3040add) covered the hhx/c4j/ehc/a4f delta. Refresh 4 (round-2, tree 0672992, committed 46b898a) covered the live-feedback quicks + eea data-chain + compat v1.3. Refresh 5 (6bb768f) covered the quick-261017-klw fix batch. This refresh covers `6bb768f..5783567` = 46 commits of slot-5 monitor quicks (261017-uwr/mad, 261018-08g/kvj/rze/toe, 261019-f0x/n0w/o8e/pe0) plus the D-03/#42 golden landings. The phase-9 cores — tui/services/custom_entries.py, custom_validation.py, gauntlet.py, tui/screens/wizard.py, data_manager.py, tui/screens/env_check.py, tui/screens/about.py, tui/services/about.py, pipeline/registry_loader.py, schemas/custom_registry.json, pipeline/run_finetune.py, pipeline/models_info.json, pipeline/datasets_info.json, and 7 of the 11 covered test files — are byte-stable across the entire delta (zero-byte diff verified this pass). The delta's covered-set footprint is 8 files: tui/app.py (+275, exit-key F10 ruling + f1/f2 help keys + monitor nav), tui/screens/selection.py (+9, LaunchConfirmModal uppercase Y/N twins only), tui/strings.py (+175/−68, exit/monitor/about copy — zero SEL_/WIZ/GAUNTLET/CUSTOM constant mutations), tui/styles.tcss (monitor master-detail block replaced by the tabbed redesign — zero wizard/custom style lines), and 4 covered test files updated for the help-row/version-pin changes. No hunk touches a phase-9 SC surface. All five SCs re-verified against the current on-disk state; the full wizard/custom evidence lane (175 tests) plus the named pins plus all remaining covered test files re-run green this pass. Zero regressions.

**Staleness resolution:** the phase went stale because the monitor quick chain rebuilt shared surfaces (monitor.py +4637/−736, nav.py +26, app.py +275, strings.py, styles.tcss, run_config/launcher/monitor services, plus new pty-driver and boot/sweep test lanes). None of that churn reaches a phase-9 SC seam: the wizard/registry/validation/gauntlet cluster is byte-identical to the round-2-verified state, and every changed covered file was read hunk-by-hunk this pass and adjudicated below. The staleness is resolved by this report at HEAD 5783567.

## Goal Achievement

### Observable Truths

Merged must-haves: the five ROADMAP Success Criteria (the contract), cross-checked against the six PLAN frontmatter truth blocks. Every plan truth maps into one of the five SCs.

| # | Truth | Status | Evidence (current codebase, 5783567) |
| --- | ------- | ---------- | -------------- |
| 1 | SC1: one action from the model list opens the custom-model wizard; a validated submission lands in `~/.config/dnallmmark/custom_models.json` and the model appears via the overlay; `pipeline/models_info.json` never written | ✓ VERIFIED | Slot-2 `w` (selection.py:1367 `Binding("w", "open_wizard")`) → `action_open_wizard` (:1900) → `CustomOnboardingBackend` (:603, `build_wizard` :633 over the REAL services) — seams re-anchored at current line numbers this pass (shifted +9 by the LaunchConfirmModal insertion above them, content unchanged). Landing writes through `settings.atomic_write` → `custom_models.json`. Official registries: models_info.json and datasets_info.json byte-identical across 6bb768f..5783567 (zero-byte diff verified this pass), counts 59 models / 50 datasets re-read, zero official-path writes (the only two `DATASETS_INFO_NAME` write sites in tui/ — gauntlet.py:344 and download_queue.py:2565 — both stage into a tempfile `regdir`, re-read this pass; every other models_info/datasets_info reference in tui/ is a docstring, constant, or load). Behavioral, re-run green this pass: `test_full_loop_models_wizard_lands_badges_counts_and_disables` (in the 27-test pin batch) — asserts official bytes unchanged, badge/count/disable/loader-drop |
| 2 | SC2: same for datasets from the dataset list — landing in `~/.config/dnallmmark/custom_datasets.json`, `pipeline/datasets_info.json` never written | ✓ VERIFIED | data_manager.py byte-stable across the delta (absent from changed-file list): slot-3 `w` → `action_open_wizard` (:1274) → `build_wizard(kind="datasets")` (:1291) → same store → `custom_datasets.json`. Overlay visibility holds at the registry tier; the per-row presentation is the overridden SC5 dataset half. Official zero-touch shares Truth 1's byte-diff evidence. Dataset-side behavioral pins green in this pass's 175-test wizard/custom lane |
| 3 | SC3: submission blocked until validation passes; collect-all fail-fast one-pass report (required/type/enum/collisions vs official AND custom/path existence/split parseability/rows>0/label column/metric-in-registry), every problem itemized | ✓ VERIFIED | `tui/services/custom_validation.py` and `tui/screens/wizard.py` both byte-stable across the delta (zero-byte diff): `validate_model_candidate`/`validate_dataset_candidate` collect `(field_key, message)` pairs in field-definition order; `METRIC_REGISTRY` parity-locked to `SUITE_CANONICAL`; wizard `_submit` runs the injected validator, `_write_report` renders the numbered collect-all report and NOTHING is applied; a clean pass alone enters the gauntlet phase. Collect-all discipline and METRIC_REGISTRY parity pins green in this pass's lane (test_pilot_wizard.py + test_services_custom_validation.py all in the 175 + 128 green runs) |
| 4 | SC4: after submission the automatic gauntlet runs (dry-run precheck + audit reconciliation); any failure reported prominently, failed entry never lands, entry-level revert, no half-written state | ✓ VERIFIED | `tui/services/gauntlet.py` and the wizard's land-only-on-all-✓ handler both byte-stable across the delta (zero-byte diff): dry-run leg invokes `run_sweep.py --dry-run` as LIST argv with staged overlay env; audit leg stages candidate-only registry (the tempfile regdir write at :344, re-read this pass) and parses `n_audit.json`; the wizard lands only on `if message.ok:` through the injected land seam. Real-subprocess pins green this pass (test_services_gauntlet.py in the 128-test covered-file run). run_finetune.py unchanged across this delta — the 07-CR-01 guarded reads stand as landed |
| 5 | SC5: landed customs carry a visible marker distinct from official in both lists, individually enable/disable, export as the share unit; official registries and existing test suite stay green and untouched | ✓ PASSED (override) | **Models half fully intact and re-verified on the current tree**: `◇` badge renders via `S.SEL_CUSTOM_BADGE` + `S.SEL_DISABLED_SUFFIX` in the custom-key cell (selection.py:1035-1040, re-read this pass at current line numbers; both constants intact in strings.py at :661-662 with 11 consumer references); `e` toggle (selection.py binding → `action_toggle_enabled` :1925 → `set_enabled` in custom_entries.py:269, byte-stable); count segment (`_update_status_line` :1755); loader-skip (registry_loader.py:160-169, byte-stable, full test file green this pass). Wizard `f`/`o` export/import seams intact (wizard.py byte-stable). Behavioral, re-run green this pass (full-loop pin in the 27-test batch: badge + suffix + count + loader-drop asserted). **Dataset half overridden**: the maintainer's locked 2026-10-14 slot-split ruling consciously removed the dataset enable/disable console surface and per-row marker (service-tier `set_enabled` + loader-skip for both kinds, export, and the aggregate count segment all remain, test-pinned) — see the frontmatter `overrides` block, accepted by Tao Zhang 2026-10-14T14:50:00Z, carried verbatim. Official registries byte-identical across the delta (Truth 1); suite green across this pass's three runs (175 + 27 + 128 tests, zero failures, zero pty timeouts) |

**Score:** 5/5 truths verified (4 direct + 1 maintainer override; 0 present-but-behavior-unverified — every behavior-dependent truth (land-only-on-all-✓, undo rollback, loader-skip, collect-all ordering, render-time i18n re-derivation) has a passing behavioral test; the SC1 full-loop pin was re-run individually this pass, the remainder stood green in this pass's wizard/custom lane and covered-file runs)

### Advisory (New Scope, Unevidenced)

Carried review findings, re-evidenced this pass (statuses in the frontmatter `advisory:` block). No status changes: all eight remain disposition-open or maintainer-ruled, none breaches a phase-9 SC.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | WR-01 (09) ExitModal naming (app.py) | other | post-phase-9 surface; disposition-open; this delta's exit-key/monitor rework reshapes app.py again without a naming fix |
| 2 | WR-02 (09) env_check storage_rows sync IO | other | quick-261014-f4w scope riding a covered file; no phase-9 SC; env_check.py screen byte-stable this delta |
| 3 | WR-03 (09) selection _manual_landing_path event-loop read | other | quick-261014-mlc scope; no phase-9 SC; selection.py delta read in full — untouched (site at :1953) |
| 4 | CR-01 (09) schema-optional vs hard-index seam — model-loop sites fixed (6e331d3, pin re-run green this pass); residual dataset-side sites maintainer-ruled (Phase-7 W4) | architectural | crash class requires minimal hand-written entries; wizard lands stamp every field; schema/gauntlet path byte-stable; run_finetune.py unchanged this delta |
| 5 | IN-01 (09) six dead SEL_ constants (strings.py) | other | cosmetic; 0 consumers re-verified this pass; constants untouched by the +175/−68 strings delta |
| 6 | IN-02 (09) pinned data counts in tests | other | green at HEAD (full-loop pin re-run this pass, index 38 current); R-03 class risk; disposition-open |
| 7 | IN-03 (09) stale "seven kernel ids" comment | other | comment-only; still stale at :92 this pass; disposition-open |
| 8 | DNR-27 wizard keycap visibility ruling | other | discoverability finding on a byte-stable surface; awaits maintainer |

### Required Artifacts

All artifacts from the six PLANs exist and are substantive at 5783567. The plans use plain-string artifact lists (`verify.artifacts` does not parse them), so levels were verified manually: exists ✓, substantive ✓ (no stubs; TBD/FIXME/XXX grep zero across all of tui/ this pass), wired ✓ (below).

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| tui/services/custom_entries.py | store: read/land/undo/set_enabled/import/export | ✓ VERIFIED | byte-stable across the delta (zero-byte diff 6bb768f..5783567); read_entries :172, land :209, undo :246, set_enabled :269, read_import_candidates :296, export_registry :339 — all through settings.atomic_write; test file green this pass |
| tui/services/custom_validation.py | collect-all validator + METRIC_REGISTRY | ✓ VERIFIED | byte-stable; validators, METRIC_REGISTRY :91; test file green this pass |
| schemas/custom_registry.json | entry-shape schema for imports | ✓ VERIFIED | byte-stable; carries the CR-01 optional-fields seam (advisory #4) |
| tui/services/gauntlet.py | two-leg subprocess gauntlet | ✓ VERIFIED | byte-stable; real `subprocess.run` seam :161; staged-regdir audit write :344 re-read this pass; test file green this pass |
| pipeline/registry_loader.py | D-09 enabled:false skip | ✓ VERIFIED | byte-stable; :160-169 skip intact (collision loop precedes the skip); full test file green this pass (in the 27-test batch) |
| tui/screens/wizard.py | 4-step modal + report + gauntlet panel + import/export | ✓ VERIFIED | byte-stable across the entire delta; `_submit`, `_write_report`, land-only-on-all-✓, undo, `f`/`o` seams all as at round-2; test file green in this pass's lane |
| tui/screens/selection.py | w entry, badge, e toggle, count, prefill | ✓ VERIFIED | delta = LaunchConfirmModal uppercase Y/N twins only (+9, 261018-08g SOAK-2/F3 — the slot-4 gate / monitor re-run surface); all models-side SC surfaces re-verified at current line numbers (w :1367, action_open_wizard :1900 with prefill, action_toggle_enabled :1925, badge cell :1035-1040, count :1755, CustomOnboardingBackend :603) |
| tui/screens/data_manager.py | slot-3 dataset wizard entry | ✓ VERIFIED | byte-stable; wizard seam at :1274/:1291; seam tests green in this pass's lane |
| tui/app.py | 09-03 nav shell host | ✓ VERIFIED | delta = exit-key rework (261017-mad F10 primary exit, ctrl+c withdrawal to terminal semantics), f1/f2 any-focus help+language keys, monitor nav changes — all Phase-11/12/quick surfaces; zero official-registry write paths (re-audited this pass); nav-shell tests green this pass (in the 128-test covered-file run) |
| tui/screens/about.py, tui/services/about.py, env_check.py, strings.py, styles.tcss | 09-03 nav shell + about + i18n | ✓ VERIFIED | about.py both tiers + env_check.py screen byte-stable; strings.py delta touches zero SEL_/WIZ/GAUNTLET/CUSTOM constants (exit/monitor/about copy only); styles.tcss delta deletes only the retired monitor master-detail block (zero wizard/custom lines); about test's version pin follows the pyproject 1.2.0 bump — green this pass |
| 11 phase test files (incl. test_language_rederivation.py pinning the wizard) | behavioral evidence | ✓ VERIFIED | all exist; 7 byte-stable, 4 changed additively (help rows f10/f1/f2, typing-key predicate strengthening in nav_shell, about version pin 1.2.0); all green this pass across the three runs |

### Key Link Verification

All links re-anchored this pass: the service/wizard/data_manager/registry_loader ends are byte-identical to round-2 (zero-byte diff), and the selection-side seams were re-read at current line numbers (+9 shift from the LaunchConfirmModal hunk).

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| slot-2 `w` | model wizard | `action_open_wizard` → `build_wizard(kind="models")` over real services | ✓ WIRED | selection.py:1367 → :1900 → backend :603; full-loop Pilot green this pass |
| slot-3 `w` | dataset wizard | `data_manager.action_open_wizard` → `build_wizard(kind="datasets")` | ✓ WIRED | data_manager.py byte-stable (:1274/:1291); seam tests green in this pass's lane |
| wizard all-✓ | custom_entries.land | injected land seam → atomic write → overlay-visible | ✓ WIRED | wizard.py byte-stable; the panel's only write call site; full-loop test green this pass |
| gauntlet service | run_sweep.py --dry-run / audit | LIST argv subprocess + pinned env → artifact parse | ✓ WIRED | gauntlet.py byte-stable; real-subprocess pins green this pass |
| registry_loader enabled-skip | every registry consumer | `entry.get("enabled") is False` (:160-169) | ✓ WIRED | byte-stable; loader-drop asserted in the green full-loop test |
| slot-2 `e` | custom_entries.set_enabled | atomic seam → next load skips | ✓ WIRED (models — the overridden scope) | selection.py binding → :1925 → store :269; disable/suffix/loader-drop asserted in the green full-loop test |
| wizard `o`/`f` | export_registry / import+per-entry gauntlet | kind-bound seams from build_wizard | ✓ WIRED | wizard.py byte-stable; seams bound in the backend |
| wizard labels | active language | `S.*` read at CALL time (`_kind_spec`/`_model_steps`/`_dataset_steps`/`_quirk_fields`) | ✓ WIRED | wizard.py byte-stable; re-derivation pin green in this pass's lane |
| wizard cancel | ConfirmModal base | esc-confirm push | ✓ WIRED | wizard.py byte-stable; the app.py exit rework does not touch ConfirmModal |

### Data-Flow Trace (Level 4)

Unchanged from round-2 (all sources byte-stable); re-anchored where the delta touched a file.

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| selection custom_status | overlay merge + management read | registry_loader + custom_entries.read_entries | ✓ | ✓ FLOWING |
| gauntlet verdicts | parsed artifacts | sweep_manifest.json / n_audit.json from real subprocesses | ✓ | ✓ FLOWING |
| wizard report | problems list | validate_*_candidate over injected ValidationSources | ✓ | ✓ FLOWING |
| wizard labels/steps | S.* constants | strings.py `_t()` bilingual registry read at access time | ✓ | ✓ FLOWING (the strings.py delta does not touch any consumed wizard constant) |
| badge/count/toggle | S.SEL_CUSTOM_BADGE / SEL_DISABLED_SUFFIX / custom_status | strings.py + management read | ✓ | ✓ FLOWING (full-loop test asserts the rendered badge + suffix + count line — green this pass) |

No static returns, hardcoded verdicts, or mock-fed renders on production paths.

### Behavioral Spot-Checks

Full suite not re-run this pass (per the stale-refresh brief: run the phase's evidence lanes cheaply). Three targeted runs, all green, zero failures, zero pty timeouts (the documented slot-4 flake did not appear):

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Phase evidence lane: every wizard/custom-matched test in tests/tui | `.venv/bin/python -m pytest tests/tui -q -k "wizard or custom"` | **175 passed, 1101 deselected in 123.83s** | ✓ PASS |
| Full-loop models wizard + dataset-kind tick + CR-01 guarded reads + full registry_loader file (the report's named pins) | `.venv/bin/python -m pytest tests/tui/test_pilot_selection_custom.py::test_full_loop_models_wizard_lands_badges_counts_and_disables … ::test_dataset_kind_tick_stores_no_live_dict_residue tests/test_run_finetune_contracts.py::test_minimal_custom_entry_reads_are_guarded tests/test_registry_loader.py -q` | **27 passed in 3.78s** (batch; index pin 38 current) | ✓ PASS |
| Remaining covered test files incl. the two changed this delta (nav_shell, about) + gauntlet + custom_entries + custom_validation services | `.venv/bin/python -m pytest tests/tui/test_pilot_nav_shell.py tests/tui/test_services_gauntlet.py tests/tui/test_services_about.py tests/tui/test_services_custom_entries.py tests/tui/test_services_custom_validation.py -q` | **128 passed in 4.22s** | ✓ PASS |
| Official registries untouched | `git diff 6bb768f..5783567 -- pipeline/models_info.json pipeline/datasets_info.json` → zero-byte; write-path audit over tui/ (2 hits, both tempfile regdir staging); counts 59/50 | clean | ✓ PASS |

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

No orphaned requirements: REQUIREMENTS.md maps exactly CUST-01/02/03/04/06 to Phase 9 (all marked Complete; CUST-05 = Phase 7). The union of the six plans' `requirements:` frontmatter is exactly {CUST-01, CUST-02, CUST-03, CUST-04, CUST-06} — no ID unmapped, no plan claims a Phase-7 ID.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | Zero TBD/FIXME/XXX across all of tui/ this pass (incl. every delta file: app.py, selection.py, strings.py, styles.tcss, nav.py, monitor.py, sweep_launcher.py, sweep_monitor.py) | — | none |

### Human Verification Required

None. The original items were closed by the recorded UAT (09-UAT.md, status passed, 2026-10-12: live console wizard loop driven in the real app; cross-machine share-unit round trip via pinned XDG roots), the removed dataset e-toggle/marker surface is settled by the maintainer's recorded override (a decision, not a re-test), and this refresh introduced no behavior-unverified truths: every behavior-dependent truth (land-only-on-all-✓, undo rollback, loader-skip, collect-all ordering, render-time i18n re-derivation) has a passing behavioral test — the SC1 full-loop pin re-run individually this pass, the remainder standing green in this pass's wizard/custom lane and covered-file runs. The dnr audit's WizardModal keycap-visibility question (advisory #8) is a maintainer aesthetic ruling on a byte-stable surface, not a re-test of a phase-9 SC.

### Gaps Summary

No gaps. All five SCs hold at 5783567: the phase-9 cores (custom_entries.py, custom_validation.py, gauntlet.py, wizard.py, data_manager.py, env_check.py, about.py both tiers, registry_loader.py, custom_registry.json, run_finetune.py, both official registries, and 7 of the 11 covered test files) are byte-stable across the entire 6bb768f..5783567 delta (zero-byte diff verified this pass), and the delta's eight covered-file changes were read hunk-by-hunk and adjudicated: app.py's exit-key/F10/help-row/monitor-nav rework (Phase-11/12/quick surfaces), selection.py's LaunchConfirmModal Y/N twins (+9, slot-4 launch gate — below and apart from every SC1/SC5 seam), strings.py's exit/monitor/about copy churn (zero SEL_/WIZ/GAUNTLET/CUSTOM constant mutations), styles.tcss's monitor block replacement (zero wizard/custom lines), and four additive test updates (help rows, typing-key predicate strengthening, version pin 1.2.0) — none touches a phase-9 SC seam. The official registries are byte-identical across the delta and the write-path audit finds zero official-path writes — the strongest form of "provably untouched". The SC5 dataset half stands under the maintainer override carried verbatim in the frontmatter. The eight advisory findings remain real, evidenced, and non-blocking: six are disposition-open in 09-REVIEW-DISPOSITION.md, CR-01's residual is tracked in the Phase-7 lane (model-loop sites fixed with the AST pin re-run green this pass), and DNR-27 awaits the maintainer ruling — none breaches a phase-9 SC.

---

_Verified: 2026-10-19T12:13:51Z at HEAD 5783567_
_Verifier: Claude (gsd-verifier)_
