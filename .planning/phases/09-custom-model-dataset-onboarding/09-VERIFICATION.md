---
phase: 09-custom-model-dataset-onboarding
verified: 2026-10-14T14:47:03Z
status: gaps_found
score: 4/5 must-haves verified
covered_files: [".planning/phases/09-custom-model-dataset-onboarding/09-01-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-01-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-02-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-02-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-03-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-03-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-04-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-04-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-05-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-05-SUMMARY.md", ".planning/phases/09-custom-model-dataset-onboarding/09-06-PLAN.md", ".planning/phases/09-custom-model-dataset-onboarding/09-06-SUMMARY.md", "pipeline/registry_loader.py", "schemas/custom_registry.json", "tests/test_registry_loader.py", "tests/tui/test_pilot_env_check.py", "tests/tui/test_pilot_nav_shell.py", "tests/tui/test_pilot_selection.py", "tests/tui/test_pilot_selection_custom.py", "tests/tui/test_pilot_wizard.py", "tests/tui/test_services_about.py", "tests/tui/test_services_custom_entries.py", "tests/tui/test_services_custom_validation.py", "tests/tui/test_services_gauntlet.py", "tui/app.py", "tui/screens/about.py", "tui/screens/env_check.py", "tui/screens/selection.py", "tui/screens/wizard.py", "tui/services/about.py", "tui/services/custom_entries.py", "tui/services/custom_validation.py", "tui/services/gauntlet.py", "tui/strings.py", "tui/styles.tcss"]
covered_digest: "v3:sha256:803a627fbdbde206d3bd1d5be29a01c8d2c6b2d725c3be4699a9a09a9084bdf4"
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions:
    - "SC5 dataset half (CUST-06): the 2026-10-14 maintainer slot split (quick-261014-mlc) removed the dataset enable/disable console surface and the per-row dataset custom marker — no console path reaches custom_entries.set_enabled('datasets', ...) and landed custom datasets render as rows nowhere; models half fully intact"
gaps:
  - truth: "SC5: landed custom entries carry a visible custom marker in both lists and can be individually enabled/disabled (dataset half of the truth)"
    status: partial
    reason: "The maintainer's locked 2026-10-14 slot-split ruling (quick-261014-mlc, .planning/.continue-here.md decisions_made) removed the interactive dataset table: slot 3's pane lists official registry keys only, and the e toggle became models-constant. Dataset custom entries have NO console enable/disable surface (the MLC SUMMARY maintainer-facing item 3 flagged exactly this: 'the wizard's undo covers the just-landed case only. Flagged, not built') and NO per-row marker anywhere; only the slot-2 status-line count segment (自定义 {models}/{datasets}) still exposes their existence. No override is recorded and no later phase or backlog item (milestone ends at Phase 12; backlog 999.1 is validation fool-proofing, a different scope) restores the surface — so the SC5 wording fails at HEAD for datasets. Export (slot-3 wizard o), the service-tier set_enabled + loader-skip, and the aggregate count remain intact and test-pinned."
    artifacts:
      - path: "tui/screens/selection.py"
        issue: "action_toggle_enabled (line ~1744) calls set_enabled with the constant kind 'models'; no other set_enabled call site exists under tui/"
      - path: "tui/screens/data_manager.py"
        issue: "slot-3 pane rows are official-only ('one PresenceRow per official registry key'); binding set is d/r/x/a/v/w/enter/g/z — no e, no custom rows, no badge"
    missing:
      - "A console enable/disable surface for dataset customs (e.g. e on slot 3's pane rows), OR a maintainer-accepted override in this file's frontmatter (see the override suggestion in the report body)"
      - "A per-row custom marker for dataset entries on slot 3 (◇ badge or 自定义 cell), OR an explicit ruling that the slot-2 count segment is the accepted dataset marker"
advisory:
  - finding: "WR-01: ExitModal renders the attached sweep's progress counts under the launcher root's name (tui/app.py:835-849)"
    category: other
    reason: "Post-phase-9 surface (Phase-12 D-06 exit modal + monitor attach); no phase-9 SC covers the exit modal; open in 09-REVIEW-DISPOSITION.md — fix belongs to that queue, not this phase"
    evidence_status: "deterministic: code-traced in 09-REVIEW.md (delta review be62a5a)"
  - finding: "WR-02: slot-1 storage overview runs load_state() + five Path.exists() stats synchronously on the event loop (tui/screens/env_check.py:613-648) — the D-03 worker-discipline class"
    category: other
    reason: "The storage-overview feature is quick-261014-f4w scope riding a phase-9 covered file; no phase-9 SC covers env-check I/O discipline; open in the disposition queue"
    evidence_status: "deterministic: code-traced in 09-REVIEW.md"
  - finding: "WR-03: _manual_landing_path reads run-config state on the event loop inside the d handler (tui/screens/selection.py:1777-1781) — same D-03 class, delta-introduced"
    category: other
    reason: "The d model-download lane is quick-261014-mlc scope; no phase-9 SC covers the download lane; open in the disposition queue"
    evidence_status: "deterministic: code-traced in 09-REVIEW.md"
  - finding: "CR-01 (standing, from Phase 7): schemas/custom_registry.json declares Mean_token_length/Model_name (model_entry) and length (dataset_entry) OPTIONAL while pipeline/run_finetune.py hard-indexes them (lines 1008, 1021, 1322) and pipeline/registry_loader.py injects no defaults — a custom entry omitting them can pass schema + wizard validation + the gauntlet and KeyError at first training step"
    category: architectural
    reason: "Assessed against the phase-9 must-haves this pass with direct evidence: SC3's enumerated contract (required/type/enum/collisions/path/splits/rows/label-column/metric — the checks the validator KNOWS about) is complete and collect-all; field-completeness-vs-pipeline-hard-index is not an enumerated phase-9 check, and the gauntlet (dry-run + audit, as SC4 defines it) cannot exercise the training loop. The schema's optionality is the shared phase-7/9 contract; the defect is a cross-phase seam already deterministically reproduced and adjudicated a non-falsifying Warning in the Phase-7 verification (original + 2026-10-14 re-run, which names this phase's schema/wizard surface as ownership) and queued for a /gsd-quick schema-side fix. Not a phase-9 gap; tracked there."
    evidence_status: "deterministic: schema required-arrays parsed this pass; run_finetune.py:1008/1021/1322 hard-index confirmed; registry_loader has no defaulting for these fields"
  - finding: "IN-01: six dead SEL_ constants + stale dataset-table comments in tui/strings.py:218-240 after the slot split"
    category: other
    reason: "Cosmetic dead code with misleading comments; zero functional impact; open in the disposition queue"
    evidence_status: "deterministic: grep-verified zero consumers in 09-REVIEW.md"
  - finding: "IN-02: tests pin committed-data counts (36 adapted) in tests/tui/test_pilot_selection.py:1451-1455 and test_pilot_selection_custom.py:895 — break on any compat-map data refresh"
    category: other
    reason: "Tests pass at HEAD (36 is current); the risk is future data commits turning CI red for a non-defect, contrary to the repo's R-03 pin-structure-not-counts rule; open in the disposition queue"
    evidence_status: "deterministic: assertions read this pass; 285/285 phase tests green at be62a5a"
  - finding: "IN-03: stale 'seven kernel ids' comment at tests/tui/test_pilot_env_check.py:90 (it is eight since 261014-dcl)"
    category: other
    reason: "Comment-only staleness; open in the disposition queue"
    evidence_status: "deterministic: read this pass"
behavior_unverified: 0
---

# Phase 9: Custom Model & Dataset Onboarding (自定义接入向导) Verification Report

**Phase Goal:** Operators can bring their own model and dataset into the benchmark entirely from the console, with official registries provably untouched — guided wizards collect the full entry into user-owned custom registries, fool-proofing validation collects every field problem in one fail-fast report before anything is written, and an entry lands only after passing the real gauntlet (dry-run precheck + audit reconciliation) with entry-level rollback when anything fails
**Verified:** 2026-10-14T14:47:03Z (stale-refresh re-verification at HEAD `be62a5a`)
**Status:** gaps_found
**Re-verification:** Yes — stale-fingerprint refresh. The 2026-10-13 pass (5/5) went stale because phases 10-12, quick tasks 261014-l6h/mlc/dcl/c2l/f4w/ir9, and the 08-08/08-09 gap-closure rounds modified covered files (selection.py reshaped to the models-only MLC-02 surface + card guards; app.py download-queue spine + exit modal; env_check.py storage overview + worker guards; gauntlet.py decode policy; ir9 registry 62→59 data change; test files extended).

## Goal Achievement

### Observable Truths

Merged must-haves: the five ROADMAP Success Criteria (the contract), cross-checked against the six PLAN frontmatter truth blocks. Every plan truth maps into one of the five SCs.

| # | Truth | Status | Evidence (current codebase) |
| --- | ------- | ---------- | -------------- |
| 1 | SC1: one action from the model list opens the custom-model wizard; a validated submission lands in `~/.config/dnallmmark/custom_models.json` and the model appears via the overlay; `pipeline/models_info.json` never written | ✓ VERIFIED | `action_open_wizard` (tui/screens/selection.py:1704, `w` binding :1279) → `build_wizard(kind="models", prefill, on_changed)` (:681) composing the REAL services: validators over real `ValidationSources` built from live registry reads, `land`/`undo`/`import`/`export` seams bound to `custom_entries_service` (:705-786). MLC-02 STRENGTHENED model visibility: customs are always in the default pool (outside the adapted-filter ruling), carry the `◇` badge (:1030-1035), the `自定义` compat cell, and the count segment (`_update_status_line`, :1572-1593). Landing writes through `settings.atomic_write` → `custom_registry_path` → `custom_models.json` (custom_entries.py:209, :431). Official registries: zero TUI write paths (grep over tui/ for write/dump to models_info|datasets_info: none), working tree clean, last commits are maintainer data edits (ir9 confidential-series removal 62→59, l6h URL fills). Tests: `test_full_loop_models_wizard_lands_badges_counts_and_disables` (asserts `official.read_bytes() == before`) and the tracer test pass in the 285-test run below. The 08-09 card guards (type-tolerant walrus vocab reads, :721-733) harden the composition, no behavior change to required fields |
| 2 | SC2: same for datasets from the dataset list — landing in `~/.config/dnallmmark/custom_datasets.json`, `pipeline/datasets_info.json` never written | ✓ VERIFIED | The dataset wizard moved WITH the dataset list in the 2026-10-14 slot split: slot 3's `w` (tui/screens/data_manager.py:597 binding → `action_open_wizard` :1253) → the SAME real composition (`CustomOnboardingBackend.build_wizard(kind="datasets", ...)`, :1270-1274, lazy import per the 09-06 cycle-break pattern) → same store → `custom_datasets.json`. Wizard-suite dataset-kind behavior stays pinned (`_dataset_wizard` helper + dataset-kind gauntlet legs in tests/tui/test_pilot_wizard.py; slot-3 w seam pinned by `test_w_opens_the_dataset_wizard_and_reload_wires_through`). Official zero-touch shares Truth 1's evidence. Overlay visibility holds at the registry tier (custom dataset keys merge into `SelectionData.dataset_entries` → marks/matrix/status); the per-row PRESENTATION of that visibility is the SC5 finding below |
| 3 | SC3: submission blocked until validation passes; collect-all fail-fast one-pass report (required/type/enum/collisions vs official AND custom/path existence/split parseability/rows>0/label column/metric-in-registry), every problem itemized | ✓ VERIFIED | `tui/services/custom_validation.py` is byte-stable since the phase-9 review fixes (last commit b0e2812, 2026-10-12 — untouched by the entire phases-10-12 delta): `validate_model_candidate`/`validate_dataset_candidate` (:193/:237) collect `(field_key, message)` pairs through the `_check_*` family; `METRIC_REGISTRY` parity-locked to `SUITE_CANONICAL`; collision check covers official + existing custom keys. The only delta at the seam is the 08-09 type-tolerant vocabulary reads inside `build_wizard` (hardening — which fields are required lives in the untouched validator). Collect-all discipline re-proven green this pass: `test_three_simultaneous_defects_yield_three_ordered_problems`, `test_dataset_collect_all_spans_all_required_fields`, `test_problems_follow_field_definition_order_not_dict_order`, `test_metric_registry_parity_with_suite_canonical` — all in the 285. Wizard renders the numbered report and hands off only on clean pass (`_phase` state machine, wizard.py unchanged since d6f2a2c's exit_on_error hardening) |
| 4 | SC4: after submission the automatic gauntlet runs (dry-run precheck + audit reconciliation); any failure reported prominently, failed entry never lands, entry-level revert, no half-written state | ✓ VERIFIED | `tui/services/gauntlet.py` (599 lines): dry-run leg invokes `run_sweep.py --dry-run` as LIST argv with staged overlay env; audit leg stages candidate-only registry with absolute `Dataset_path`, all-temp outputs; pass parsed from `sweep_manifest.json` / `n_audit.json`; timeouts yield failed items verbatim. The only delta since the passing verification is the decode `errors="replace"` policy (46ddd37, a review follow-up making corrupt-output handling robust — both legs remain REAL subprocesses). Gauntlet imports only `read_entries` (read-only store seam); the wizard lands through injected `land`/`undo` seams only after all-✓; per-entry import rollback covered. Real-subprocess evidence re-run green this pass: `test_real_subprocess_dry_run_passes_for_synthetic_model_candidate`, `test_committed_audit_artifacts_byte_unchanged_across_real_gauntlet`, timeout tests, dataset-kind gauntlet legs — all in the 285 |
| 5 | SC5: landed customs carry a visible marker distinct from official in both lists, individually enable/disable, export as the share unit; official registries and existing test suite stay green and untouched | ✗ FAILED (partial — dataset half) | **Models half fully intact**: `◇` badge + `（已停用）` suffix (:1030-1035), `e` toggle → `custom_entries_service.set_enabled` (:1739-1756), count segment, loader-skip (`registry_loader.py:166` `entry.get("enabled") is False`, official entries unaffected). **Dataset half breached by the 2026-10-14 maintainer slot split** (quick-261014-mlc, executing the maintainer's locked ruling recorded in `.planning/.continue-here.md` decisions_made): (a) the interactive dataset table is gone — slot 3's pane rows are official-only ("one PresenceRow per official registry key"), so a landed custom dataset renders as a row NOWHERE (no per-row marker; matrix screen has none either); (b) `e` is now models-constant — `action_toggle_enabled` calls `set_enabled("models", ...)` (:1744) and it is the ONLY call site under tui/; slot 3's bindings (d/r/x/a/v/w/enter/g/z) have no e — dataset customs have NO console enable/disable surface. The MLC-03 plan scoped it out explicitly ("e stays OFF this screen … flagged in the SUMMARY, not built here") and the MLC SUMMARY maintainer-facing item 3 flagged it ("dataset custom entries have NO enable/disable surface anywhere in the console"). What survives for datasets: export (slot-3 wizard binds `export_registry("datasets", dest)`), the aggregate count segment (`自定义 {m}/{d}`), the service-tier `set_enabled` + loader-skip (test-pinned for both kinds), and `（已停用）`-aware management reads. No override is recorded in this file and no later phase (milestone ends at Phase 12) or backlog item (999.1 = validation fool-proofing, different scope) restores the surface — the SC5 wording therefore fails at HEAD for datasets. **This looks intentional** — see the override suggestion below |

**Score:** 4/5 truths verified (0 present-but-behavior-unverified — the prior cross-machine share-unit item was closed by the recorded UAT, 09-UAT.md, passed 2026-10-12: machine-B pinned-root import ran the real gauntlet and landed)

### Override Suggested (SC5 dataset half — maintainer decision requested)

The SC5 dataset-half breach is the documented consequence of the maintainer's OWN locked 2026-10-14 slot-split ruling, deliberately flagged in the 261014-mlc SUMMARY rather than slipped in. It is not executor drift. If the maintainer accepts the reduced surface (count-segment-only dataset marker, no dataset e-toggle; the wizard's undo covers just-landed entries), add to this file's frontmatter:

```yaml
overrides:
  - must_have: "SC5: landed custom entries carry a visible custom marker in both lists and can be individually enabled/disabled (dataset half)"
    reason: "Maintainer's locked 2026-10-14 slot-split ruling (slot 2 = models only, slot 3 = datasets only); dataset enable/disable surface and per-row marker consciously removed, flagged in 261014-mlc-SUMMARY maintainer-facing item 3; service-tier capability and export retained"
    accepted_by: "Tao Zhang"
    accepted_at: "{ISO timestamp}"
```

Otherwise `/gsd-plan-phase --gaps` will plan the restore (e.g., an `e` + badge lane on slot 3's pane rows).

### Advisory (New Scope, Unevidenced as Phase-9 Gaps)

All seven findings below are real and evidenced, but none breaches a phase-9 SC — six are post-phase surfaces riding covered files (phases 10-12 / quick tasks, disposition-open in 09-REVIEW-DISPOSITION.md), and CR-01 is the standing cross-phase seam already adjudicated at Phase 7. Details in frontmatter `advisory:`.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | WR-01 ExitModal counts/name mixing (app.py:835-849) | other | Phase-12 D-06 surface; no phase-9 SC covers it |
| 2 | WR-02 storage_overview event-loop reads (env_check.py:613-648) | other | quick-261014-f4w surface; D-03 class; disposition-open |
| 3 | WR-03 `_manual_landing_path` event-loop read (selection.py:1777) | other | quick-261014-mlc d-lane; D-03 class; disposition-open |
| 4 | CR-01 schema-optional vs run_finetune hard-index (run_finetune.py:1008/1021/1322) | architectural | Cross-phase seam; SC3's enumerated contract complete; Phase-7-adjudicated Warning, /gsd-quick fix queued |
| 5 | IN-01 dead SEL_ constants (strings.py:218-240) | other | Cosmetic; disposition-open |
| 6 | IN-02 data-pinned test counts (36 adapted) | other | Green at HEAD; future-refresh fragility; disposition-open |
| 7 | IN-03 stale "seven kernel ids" comment | other | Comment-only; disposition-open |

### Required Artifacts

All artifacts from the six PLANs exist and are substantive at HEAD. Manual levels (the plans use plain-string artifact lists `verify.artifacts` does not parse): exists ✓, substantive ✓ (no stubs, no debt markers — TBD/FIXME/XXX grep zero across all covered files), wired ✓ (below).

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| tui/services/custom_entries.py | store: read/land/undo/set_enabled/import/export | ✓ VERIFIED | 432 lines, byte-stable since phase 9 (9d6bd75); all six ops + atomic write seam |
| tui/services/custom_validation.py | collect-all validator + METRIC_REGISTRY | ✓ VERIFIED | 616 lines, byte-stable since phase 9 (b0e2812) |
| schemas/custom_registry.json | entry-shape schema for imports | ✓ VERIFIED | 71 lines, byte-stable since 517f821; carries the CR-01 optional-fields seam (advisory #4) |
| tui/services/gauntlet.py | two-leg subprocess gauntlet | ✓ VERIFIED | 599 lines; only delta = decode `errors="replace"` (46ddd37, review follow-up) |
| pipeline/registry_loader.py | D-09 enabled:false skip | ✓ VERIFIED | :166 skip intact; byte-identical-when-absent contract re-proven by the 24-test loader suite in the 285 |
| tui/screens/wizard.py | 4-step modal + report + gauntlet panel + import/export | ✓ VERIFIED | 1702 lines; delta = exit_on_error hardening only (d6f2a2c) |
| tui/screens/selection.py | w entry, badge, e toggle, count, prefill | ✓ VERIFIED (models scope) | 2179 lines after MLC-02 rework; models-side w/badge/e/count intact; dataset-side surface loss = the SC5 gap |
| tui/app.py, about.py screens/services, env_check.py, strings.py, styles.tcss | 09-03 nav shell + about + i18n | ✓ VERIFIED | all six nav slots live (nav.py NAV_SLOTS); zero-Chinese-literals lock green; deltas are later-phase surfaces (advisory) |
| 10 phase test files | behavioral evidence | ✓ VERIFIED | 285 tests, all passing (153.97s) — grew from 260 with later-phase additions |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| slot-2 `w` | model wizard | `action_open_wizard` → `build_wizard(kind="models")` over real services | ✓ WIRED | selection.py:1704-1729; full-loop Pilot green |
| slot-3 `w` | dataset wizard | `data_manager.action_open_wizard` → `build_wizard(kind="datasets")` | ✓ WIRED | data_manager.py:1253-1274 (lazy CustomOnboardingBackend); seam + wizard-suite dataset-kind pins green |
| wizard all-✓ | custom_entries.land | injected land seam → atomic write → overlay-visible | ✓ WIRED | tracer + full-loop tests green in the 285 |
| gauntlet service | run_sweep.py --dry-run / audit | LIST argv subprocess + pinned env → artifact parse | ✓ WIRED | real-subprocess tests green |
| registry_loader enabled-skip | every registry consumer | `entry.get("enabled") is False` (:166) | ✓ WIRED | loader-skip tests green |
| slot-2 `e` | custom_entries.set_enabled | atomic seam → next load skips | ✓ WIRED (models only) | **no dataset path — the SC5 gap** |
| wizard `o`/`f` | export_registry / import+per-entry gauntlet | kind-bound seams from build_wizard | ✓ WIRED | both kinds reachable (slot-2 wizard = models, slot-3 = datasets) |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| selection custom_status | overlay merge + management read | registry_loader + custom_entries.read_entries | ✓ | ✓ FLOWING |
| gauntlet verdicts | parsed artifacts | sweep_manifest.json / n_audit.json from real subprocesses | ✓ | ✓ FLOWING |
| wizard report | problems list | validate_*_candidate over injected ValidationSources | ✓ | ✓ FLOWING |
| slot-3 pane rows | presence_rows | official registry only (by design post-split) | ✓ | ✓ FLOWING (customs excluded — SC5 gap, not a data disconnect) |

No static returns, hardcoded verdicts, or mock-fed renders on production paths.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full phase test surface (10 files) | `.venv/bin/python -m pytest tests/tui/test_services_custom_entries.py tests/tui/test_services_custom_validation.py tests/tui/test_services_gauntlet.py tests/test_registry_loader.py tests/tui/test_pilot_wizard.py tests/tui/test_pilot_selection_custom.py tests/tui/test_services_about.py tests/tui/test_pilot_nav_shell.py tests/tui/test_pilot_env_check.py tests/tui/test_pilot_selection.py -q` | **285 passed in 153.97s** (this pass, HEAD be62a5a) | ✓ PASS |
| Real-subprocess gauntlet legs + committed-artifact byte-unchanged | named tests within the above | passed | ✓ PASS |
| Full-loop models wizard (land → badge → counts → disable) | `test_full_loop_models_wizard_lands_badges_counts_and_disables` | passed | ✓ PASS |
| METRIC_REGISTRY = SUITE_CANONICAL parity | `test_metric_registry_parity_with_suite_canonical` | passed | ✓ PASS |
| Official registries untouched | `git status` clean on both files; TUI write-path grep zero; counts 59/50 (post-ir9 maintainer data edit) | clean | ✓ PASS |
| Full-suite baseline (given, not re-run — GPU smoke running in background) | 7 failed / 1731 passed / 9 xfailed | 6 documented (5 test_schemas + 1 test_determinism) + 1 machine-state (storage_overview vs pipeline/logs) + 9 strict-xfail goldens — none in phase-9 covered files; phase-9 files proven green directly above | ✓ PASS modulo documented baseline |

### Probe Execution

No `probe-*.sh` scripts declared or present; not a probe-based phase. N/A.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| CUST-01 | 09-01, 09-03, 09-04, 09-06 | model wizard → custom registry, official untouched, quirk checklist | ✓ SATISFIED | Truth 1 |
| CUST-02 | 09-01, 09-03, 09-04, 09-06 | dataset wizard → custom registry | ✓ SATISFIED | Truth 2 |
| CUST-03 | 09-01, 09-04 | collect-all fail-fast field validation | ✓ SATISFIED | Truth 3 |
| CUST-04 | 09-02, 09-05 | gauntlet dry-run + audit, entry-level rollback | ✓ SATISFIED | Truth 4 |
| CUST-06 | 09-01, 09-02, 09-06 | badge / enable/disable / export share unit | ✗ PARTIAL — BLOCKED by the SC5 gap (dataset enable/disable + per-row marker absent) | Truth 5 |

No orphaned requirements: REQUIREMENTS.md maps exactly CUST-01/02/03/04/06 to Phase 9 (CUST-05 = Phase 7).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | Zero TBD/FIXME/XXX across all 13 covered implementation files; PLACEHOLDER hits are legitimate Input-widget hint constants; NAV_PLACEHOLDER_TOAST is a self-annotated zero-consumer D-13 leftover (all six slots live) | — | none |

### Human Verification Required

None newly raised. The two prior items were closed by the recorded UAT (09-UAT.md, status passed, 2026-10-12): the live console wizard loop was driven in the real app (collect-all report, gauntlet, land, undo, toggle all verified live), and the cross-machine share-unit round trip was executed via pinned XDG roots (machine-A export → machine-B import → real gauntlet PASS → land → e-toggle loader-skip). The UAT predates the slot split; the wizard core it exercised is unchanged (byte-stable modulo exit-modal hardening), and the one UAT flow the split removed (dataset e toggle) is exactly the SC5 gap above — it needs a maintainer decision, not a re-test.

### Gaps Summary

One gap. SC5's dataset half fails at HEAD: the maintainer's locked 2026-10-14 slot split removed the dataset enable/disable console surface (the only `set_enabled` call site is models-constant; slot 3 has no `e`) and the per-row dataset custom marker (slot 3's pane rows are official-only). The loss was deliberately scoped out and flagged to the maintainer in the 261014-mlc SUMMARY (maintainer-facing item 3) — but no override is recorded here and no later phase or backlog item restores it, so the roadmap contract wording fails. Export, the aggregate count marker, the service-tier toggle, and the loader-skip all remain intact and test-pinned; models-side SC5 is fully intact. Everything else the phase built is verified green at HEAD: 285/285 phase tests (real-subprocess gauntlet legs, byte-unchanged committed artifacts, full-loop wizard, loader-skip, collect-all discipline), official registries provably untouched, and the validator/gauntlet cores byte-stable through the entire phases-10-12 delta. The seven review findings (WR-01..03, IN-01..03, CR-01) are real but advisory to this phase — six are post-phase surfaces with disposition-open status, and CR-01 is the Phase-7-adjudicated cross-phase seam (evidence re-confirmed this pass: schema optional `Model_name`/`Mean_token_length`/`length` vs `run_finetune.py:1008/1021/1322` hard-index, no loader defaults) queued for the schema-side /gsd-quick fix.

---

_Verified: 2026-10-14T14:47:03Z_
_Verifier: Claude (gsd-verifier)_
