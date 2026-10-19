---
phase: 08-tui-foundation-env-check-selection
plan: 05
subsystem: tui/services (templates + selection services, run-template schema)
tags: [tui, services, templates, selection, presets, filter-grammar, schema, one-way-contract, d-06, d-07, sel-02, sel-03]
requires:
  phase: []
provides: []
provides:
  - "schemas/run_template.json — the D-07 one-way strict contract (draft 2020-12, additionalProperties false, schema_version const 1, required schema_version/models/tasks each minItems 1 uniqueItems, seeds/peft/config_variant enums with defaults, optional curve_fractions/subset_file/effective_batch_size(min 1)/num_train_epochs(>0)/cache_dir; $comment records the ratification provenance and the GA semantics) — the SAME schema the Phase 11 run-config screen consumes"
  - "tui.services.templates — validate_template (collect-ALL (json_pointer, message) problems, pointer-ordered, untrusted-input safe), export_selection_template (defaults materialized, dedupe first-occurrence, valid-by-construction, empty-selection and unknown-param refusal), load_template_file (tolerant existence diagnostics), template_to_tiers/tiers_to_template (membership-preserving pure interop over the run_sweep --priority-file grammar)"
  - "tui.services.selection — derive_presets (tier-1 pairs -> models AND tasks, tier-2 names -> models only, all -> passed registry keys verbatim; unknown-key loud surfacing; damaged file -> empty presets + load-error signal), save_custom_preset/load_custom_presets (presets.json {schema_version 1, presets name -> {models, tasks}} under the config root, atomic, tolerant, sorted), parse_filter_query/apply_filter (AND terms over the five-axis vocabulary species/type/size->size_m/category/metric, case-insensitive, order-preserving, unknown-axis diagnostics) — zero imports from tui.services.registries (decoupled by design)"
affects:
  - schemas/run_template.json
  - tui/services/templates.py
  - tui/services/selection.py
  - tests/tui/test_services_templates.py
  - tests/tui/test_services_selection.py
actuals:
  tokens: 30917     # chars/4 over the realized diff (123669 chars: 79873 code+tests+schema + 43796 embedded JUnit RED-evidence reports); code-only ≈ 19968 vs estimate 15000 (133%)
  tasks: 2          # Task 2 + Task 3 (Task 1 was the D-07 ratification checkpoint — decision only, resolved by the maintainer before this continuation)
  commits: 4        # measured: git rev-list --count de3cbc2..HEAD (2 test + 2 feat, one full TDD cycle per task)
plan_head_before: de3cbc25bfd06c91942f4310082454753e1ca730
plan_head_after: 059673760053b89c5dda3f3916fe9ab771ec7dcb
tech-stack:
  added: []         # zero new packages — jsonschema (dev group, Phase 2) is the only new import surface
  patterns:
    - "named JSON-shape predicates (_is_json_object/_is_json_list/_is_json_string) at data-validation raise sites — the TRY004-clean idiom preserving the ValueError-for-data-shape discipline (export_runs.py: ValueError for parse/shape, TypeError for wrong-typed arguments) with zero noqa"
    - "D-06-faithful test discipline: real-file tests derive every expectation from the file/registries as data, and the no-hardcoding scans read the tier names from the committed file — tier edits break zero code AND zero tests"
    - "valid-by-construction builders: export validates its own output before returning, so a shareable one-way artifact can never be emitted invalid"
key-files:
  created:
    - schemas/run_template.json
    - tui/services/templates.py
    - tui/services/selection.py
    - tests/tui/test_services_templates.py
    - tests/tui/test_services_selection.py
    - .planning/tdd-evidence/08-05-task2-red.json
    - .planning/tdd-evidence/08-05-task3-red.json
  modified: []
key-decisions:
  - "D-07 ratified verbatim 2026-10-11 (maintainer verdict: ratify — field set frozen as proposed); the field set, GA semantics, and file names are a published one-way contract from this landing"
  - "template_to_tiers emits ONE tier of explicit cross-product pairs (models-major) — a bare model name in the priorities grammar covers the model's EVERY task, which would cover unselected tasks too; tiers_to_template is registry-blind and refuses names-only tiers files (a template's minItems-1 tasks field would have nothing to carry)"
  - "Filter grammar: axis names are the strict lowercase five-axis vocabulary (species/type/size for models — size maps to the canonical size_m field; category/type/metric for datasets); values and bare substrings match case-insensitively (the k9s type-to-filter feel, size=86 matches size_m 86.0); unknown-axis tokens drop from the applied terms into diagnostics"
  - "derive_presets validates the strict committed two-tier shape (exactly two tiers, string pairs / string names) — any drift is a loud load error with empty presets, never an exception and never a silent partial derivation"
  - "Custom presets store sorted-unique lists (the same selection always produces the same file bytes); load is tolerant per T-08-06 with an unknown-schema_version whole-file guard and per-preset skip"
  - "export_selection_template validates its own output before returning (Rule 2) — an export can never emit a template another operator's import would reject"
  - "jsonschema imports at module top level in templates.py (every lane importing the module today — test/typecheck — carries it via the dev group); the make tui display lane does not yet import the module, and 08-07 must add jsonschema to the [tui] group when the selection screen wires template import"
patterns-established:
  - "the tier interop membership contract: both composition directions (tiers -> template -> tiers, template -> tiers -> template) preserve model and task MEMBERSHIP exactly — pinned by a round-trip test over the committed priorities shape"
  - "decoupled-by-design service modules: selection.py takes entries and registry keys as parameters (AST-level no-import test locks the registries decoupling), so the grammar stays pure and synthetic-fixture testable"
requirements-completed: [SEL-02, SEL-03]
coverage:
  - id: D1
    description: "SEL-03 templates — strict D-07 schema (draft 2020-12, additionalProperties false, schema_version const 1, full ratified field set with $comment GA semantics); collect-all validation (every simultaneous problem listed once, pointer-ordered, untrusted shapes yield problems not crashes); export valid-by-construction with defaults and empty-selection refusal; tier interop round-trips preserving membership exactly over the committed priorities shape"
    requirement: SEL-03
    verification:
      - kind: unit
        ref: "tests/tui/test_services_templates.py (26 tests) — schema self-check via Draft202012Validator.check_schema, the one-way field-set pin, $comment provenance/GA pin, multi-violation collect-all (>=5 problems, pointer-ordered, every location present), seeds-default case, bool-not-integer seed, export defaults/full/dedupe/empty/unknown-param/invalid-param, interop round-trip + cross-product + names-only refusal + malformed-entry ValueErrors, committed-file interop, tolerant load diagnostics"
        status: pass
      - kind: other
        ref: "plan verify gate: uv run --group dev python -c '...Draft202012Validator.check_schema(s)...' prints schema-ok; exit 0"
        status: pass
    human_judgment: false
    rationale: "Schema validity, field-set equality, collect-all behavior, and round-trip membership are all mechanically pinned by test assertions and the plan's own verify commands."
  - id: D2
    description: "SEL-02 selection — presets derive from pipeline/sweep_priorities.json at read time (tier-1 pairs -> models AND tasks, tier-2 names -> models only, all -> the passed registry keys); derivation order deterministic (file order, menu order tier-1/tier-2/all); unknown keys surfaced loudly, never silently dropped; damaged file -> empty presets + load signal, never an exception; custom presets round-trip atomically under the XDG config root with sorted names and an empty mapping on missing root; pure filter grammar (substring + axis=value AND terms, order-preserving, empty result is a plain list)"
    requirement: SEL-02
    verification:
      - kind: unit
        ref: "tests/tui/test_services_selection.py (30 tests) — every derivation bullet incl. the ghost-name unknown-key case and the real committed file (data-derived expectations), customs round-trip/overwrite/missing-root/corrupt/unknown-schema/malformed-entry/sorted-names, parse/apply grammar (AND, order, case-insensitivity, size->size_m, absent-kind axes, empty edges), decoupling scans (no registries import, no state-root reference, no bare json.load, no hardcoded tier names)"
        status: pass
      - kind: other
        ref: "make lint exit 0; make typecheck exit 0 (Task 3 verify gates); pipeline/ and dnallm-mark/ byte-untouched vs plan base (write-boundary prohibition); grep for real tier names under tui/ finds zero hits outside test data reads"
        status: pass
    human_judgment: false
    rationale: "Derivation, persistence, tolerance, and grammar semantics are fully machine-verified; the write boundary is verified by git diff."
duration: 26 min
completed: 2026-10-11T13:38:00Z
status: complete
---

# Phase 08 Plan 05: Selection/Template Services + Run-Template Schema Summary

Landed the D-07 one-way run-template contract (strict draft-2020-12 schema with collect-all jsonschema validation and sweep_priorities tier interop) and the SEL-02 selection service (D-06-derived presets, XDG-persisted customs, and the pure five-axis filter grammar) — both textual-free, tier-1 tested, CLI-reachable importable functions.

## Performance

- **Duration:** 26 min (13:12:18Z – 13:38:00Z, 2026-10-11; continuation agent — Task 1's D-07 checkpoint was resolved by the maintainer before this run)
- **Tasks completed:** 2 / 2 executable tasks (each a full TDD RED-GREEN cycle; Task 1 was decision-only)
- **Files changed:** 7 (5 code/schema/test files created, 2 TDD evidence records; +1937 lines, 0 deletions)
- **Commits:** 4 (measured from the persisted plan ledger `de3cbc2..HEAD`: 2 test + 2 feat)
- **Estimate calibration:** code+tests+schema ≈ 19968 tokens vs 15000 estimated (133% — the low-confidence estimate undercounted the test surface, which is 52% of the code diff); full realized diff including the two embedded JUnit RED-evidence reports is 30917 tokens

## Accomplishments

- **Task 2 — strict schema + templates service (D-07, SEL-03):** `schemas/run_template.json` landed exactly as ratified — draft 2020-12, `$id` under the repo schemas URL, `additionalProperties: false`, `schema_version` const 1, required `schema_version`/`models`/`tasks` (minItems 1, uniqueItems), seeds/peft/config_variant enums with defaults, the five optional fields with their stated types and minimums, and a long `$comment` recording the ratification provenance and the GA semantics. `tui/services/templates.py` delivers collect-all validation (every problem as a `(json_pointer, message)` pair — RFC 6901 pointers built from `iter_errors`' absolute paths, sorted, untrusted-input safe), export that materializes defaults and validates its own output, tolerant file-load diagnostics, and the pure interop pair whose both composition directions preserve model/task membership exactly.
- **Task 3 — selection service (D-06, SEL-02):** `tui/services/selection.py` derives the preset menu from the single-source priorities file (tier-1 pairs marking models AND tasks, tier-2 names marking models only, all returning the passed registry keys verbatim), surfaces unknown keys per preset while still carrying them in membership (nothing silently dropped), degrades a damaged file to empty presets plus a load-error signal (strict two-tier shape validation, all problems in one message), persists customs as `presets.json` under the injected config root through the 08-04 atomic-write helper (sorted-unique storage, tolerant load), and implements the pure filter grammar — space-separated AND terms over the five canonical axes (`size` mapping to the `size_m` field), case-insensitive matching, registry-order-preserving results, unknown-axis diagnostics that never drop valid terms.
- **Proof, not inspection:** both RED cycles validated `RED_EVIDENCE_OK` by the gate tool before each GREEN; tests/tui 109 passed (53 prior + 56 new); make lint + make typecheck clean (zero noqa introduced); make test-fast 669 passed (613 prior + 56 new, zero regressions); make ci 77 passed; the services-textual-free import lock green over the now-seven-module services tier; pipeline/, dnallm-mark/, and sweep_priorities.json byte-untouched.

## D-07 Schema Ratification

**Verdict: RATIFY — the proposed field set is frozen as presented** (maintainer review 2026-10-11; response "继续" / proceed, recorded at the 08-05 Task-1 blocking-human checkpoint).

- **Field set (verbatim, as ratified):** `schema_version` (const 1); `models`/`tasks` (registry-key arrays, minItems 1, unique); `seeds` (integer array, default 42/43/44); `peft` (enum none/lora/ia3, default none); `config_variant` (enum default/head/probe/curve); `curve_fractions`/`subset_file`/`cache_dir` (optional strings/arrays); `effective_batch_size` (optional integer ≥ 1); `num_train_epochs` (optional positive number).
- **GA semantics in `$comment`:** GA = max(1, effective_batch // batch_size), maintainer default 16 (small-model batch 64 → GA 1) — TUI-REQUIREMENTS open question #7 maintainer wording, matching Phase 7 D-10 child-side semantics.
- **File names:** custom presets → `presets.json` under the XDG config root (~/.config/dnallmmark/, schema_version 1, presets: {name: {models, tasks}}); templates export to operator-chosen paths.
- **Strictness:** additionalProperties false at every object level, no field renames after landing — flops_report.json precedent ($schema draft 2020-12, $id under raw.githubusercontent.com/zhangtaolab/dnallmmark/main/schemas/, long $comment with D-number provenance).
- **ONE-WAY:** field names are now a published contract (templates are shared between operators; the Phase 11 run-config screen consumes the same schema).
- **Material record:** the ratified wording is embedded in the schema's `$comment` (schemas/run_template.json) and pinned byte-exactly by `test_schema_pins_the_ratified_field_set` + `test_schema_comment_records_provenance_and_ga_semantics` — the ratification is part of the artifact, not just this document.

## Task Commits

| Task | Commit | Subject |
|------|--------|---------|
| 2 RED — templates tests + skeleton | `472c5a4` | test(08-05): add failing tests for run-template schema + templates service |
| 2 GREEN — schema + implementation | `4146d15` | feat(08-05): implement strict run-template schema + templates service |
| 3 RED — selection tests + skeleton | `7523235` | test(08-05): add failing tests for selection service (presets/customs/filter) |
| 3 GREEN — implementation | `0596737` | feat(08-05): implement selection service (derived presets, customs, filter grammar) |
| plan metadata (docs) | (this commit) | docs(08-05): complete selection/template services plan |

## Files Created/Modified

- **Created:** `schemas/run_template.json`, `tui/services/templates.py`, `tui/services/selection.py`, `tests/tui/test_services_templates.py`, `tests/tui/test_services_selection.py`, plus the two `.planning/tdd-evidence/08-05-task{2,3}-red.json` records
- **Modified:** none outside the created set (pipeline/, dnallm-mark/, Makefile, pyproject.toml all byte-untouched; the PHASE8_TUI lint wildcard and the ty `include` list picked up both new service modules automatically, as designed in 08-02)

## Decisions Made

- **Tier interop encoding:** a template is a cross-product selection, so `template_to_tiers` emits one tier of explicit `{model, task}` pairs, models-major — the priorities grammar's bare model name means "every task of this model", which would cover the operator's UNSELECTED tasks too. `tiers_to_template` is registry-blind (the selection service owns registry comparison) and refuses a names-only tiers file with a ValueError naming the minItems-1 tasks constraint. Both composition directions preserve membership exactly (the pinned round-trip property).
- **Filter-grammar semantics (planner-discretion resolution):** axis names are the strict lowercase five-axis vocabulary (UI-SPEC keyboard contract; `size` is the operator-facing name of the canonical `size_m` field); axis values and bare substrings match as case-insensitive substrings — one uniform k9s-style rule that also makes `size=86` match `size_m` 86.0. Bare substrings match the key plus every canonical display field, never the verbatim `card`. An axis absent from an entry's kind (e.g. `category` over model entries) simply never matches.
- **derive_presets strictness:** exactly two tiers, tier-1 string pairs, tier-2 string names — any structural drift is a loud load error with EMPTY presets (no partial derivation, no exception). Tier EDITS (adding/removing entries) need zero code changes; structural changes surface loudly by design.
- **Custom preset storage:** sorted-unique lists (deterministic file bytes for the same selection), tolerant load (T-08-06: corrupt/unknown-schema/malformed entries degrade, never crash), names yielded sorted for the menu tail, config root only.
- **jsonschema import placement:** top-level in templates.py — every lane importing the module today (test/typecheck) carries jsonschema via the dev group; nothing in the make tui display lane imports it yet. See Next Phase Readiness.

## Deviations from Plan

**1. [Rule 2 - correctness] export validates its own output before returning**
- **Found during:** Task 2 GREEN (implementation)
- **Issue:** the plan pins "export produces a schema-valid document", but with unchecked param VALUES (e.g. `peft: "bogus"`) the builder could emit a document another operator's import would reject — a silent corruption path for a one-way shareable artifact.
- **Fix:** `export_selection_template` runs `validate_template` over the built document and raises ValueError with the collect-all problem list on any failure; a new test (`test_export_invalid_param_value_raises_listing_problems`) pins it.
- **Files modified:** tui/services/templates.py, tests/tui/test_services_templates.py
- **Commit:** `4146d15`

**2. [Rule 2 - robustness] per-preset tolerance in load_custom_presets pinned**
- **Found during:** Task 3 GREEN (implementation)
- **Issue:** the plan pins whole-file tolerance (missing/corrupt root -> empty mapping) but not the mixed-file case; a single malformed preset entry would otherwise be an unspecified crash-or-load choice.
- **Fix:** malformed individual presets are skipped while healthy ones load (T-08-06 accept posture); a new test (`test_load_custom_presets_skips_malformed_individual_presets`) pins it.
- **Files modified:** tui/services/selection.py, tests/tui/test_services_selection.py
- **Commit:** `0596737`

**3. [Rule 3 - tooling] TRY004 findings on data-shape ValueError raises**
- **Found during:** Task 2 verify gates (make lint)
- **Issue:** ruff 0.16's effective default set flags isinstance-then-ValueError (TRY004); six sites in templates.py. Switching to TypeError would be semantically wrong (these are JSON data-shape errors, the export_runs.py discipline) and would break the RED-pinned pytest.raises(ValueError) contract.
- **Fix:** named JSON-shape predicates (`_is_json_object`/`_is_json_list`/`_is_json_string`/`_is_string_list`) at every raise site — lint-clean, zero noqa, ValueError semantics preserved.
- **Files modified:** tui/services/templates.py
- **Commit:** `4146d15`

**4. [Rule 3 - tooling] I001 import ordering on the two Task 3 files**
- **Found during:** Task 3 verify gates (make lint)
- **Issue:** ruff isort wanted the two `from tui.services import ...` lines combined and a blank line before the settings import.
- **Fix:** `ruff check --fix` applied to exactly the two new files; all gates re-run green afterward.
- **Files modified:** tui/services/selection.py, tests/tui/test_services_selection.py
- **Commit:** `0596737`

**Total deviations:** 4 auto-fixed (2 Rule 2 correctness additions, 2 Rule 3 tooling passes).
**Impact:** none on the plan's contracts — every D-number truth and prohibition verified intact (write boundary, no hardcoding, collect-all, pure data).

## TDD Gate Compliance

Both executable tasks carried `tdd="true"` and completed full RED-GREEN cycles with gate-validated evidence:

| Task | RED commit | RED evidence | GREEN commit |
|------|-----------|--------------|--------------|
| 2 | `472c5a4` | RED_EVIDENCE_OK (25 tests, 23 failed, 0 errors; target `test_multi_violation_document_lists_every_problem_in_one_call`) | `4146d15` |
| 3 | `7523235` | RED_EVIDENCE_OK (29 tests, 25 failed, 0 errors; target `test_derive_presets_tier2_unknown_name_surfaced_exactly`) | `0596737` |

RED method: None-returning skeletons committed with the failing tests (the 07-02/08-04 precedent), so every target test executed and failed on its planned assertion — no collection, import, syntax, or fixture faults (JUnit `errors=0` in both records). The trivially-green tests against the skeletons (source/AST scans over the skeleton: 2 in Task 2, 4 in Task 3) are noted in each record's semantic assessment. No REFACTOR-phase commits — the Task 2 predicate restructure happened inside GREEN before its commit, and nothing warranted a post-GREEN refactor. Gate commits verified: 2 `test(08-05):` + 2 `feat(08-05):` present in git log.

## Issues Encountered

None beyond the deviations above. No auth gates, no package installs (jsonschema was already locked in the dev group since Phase 2), no pre-commit hook cycles, no checkpoints hit (Tasks 2-3 are type=auto; the D-07 gate was resolved before this run).

## User Setup Required

None. `~/.config/dnallmmark/presets.json` is created at runtime by the future 08-07 save flow, not committed (per the plan's artifact note).

## Known Stubs

None — no placeholder patterns in the delivered files; the designed sentinels (empty problem list = valid, `(None, message)` load diagnostics, empty-mapping customs, load-error signal) are specified behavior with tests, not stubs.

## Next Phase Readiness

- **08-06 (env screen build):** unaffected by this plan; consumes the 08-04 seams (`default_kernels`, `load_cached`/`is_same_local_day`, `persist`, `gate_verdict`).
- **08-07 (selection screen):** all seams are ready — `derive_presets(priorities_path, model_keys, task_keys)` for the preset menu (apply = replace marks with the preset's models/tasks, skipping keys with no table row and warning via `unknown_keys`; menu = tier-1, tier-2, all, then `load_custom_presets` sorted); `parse_filter_query`/`apply_filter` for the filter Input (render `diagnostics` as the `未知过滤轴` warning line; empty result = the documented `无匹配行` row); template import = `load_template_file` → `validate_template` (numbered collect-all list `1. {json_pointer}: {problem}`, apply NOTHING unless the list is empty) → marks; export = `export_selection_template` + `atomic_write` to the operator-chosen path; priorities export = `template_to_tiers`.
- **jsonschema [tui]-group gap (08-07 must resolve):** `tui/services/templates.py` imports jsonschema at module top level; the dev/CI test and typecheck lanes carry it (dev group), but the `make tui` display lane (`--group tui --group gpu`) does not yet — nothing imports the module there today. When 08-07 wires template import into the screen, add `jsonschema>=4.26.0` to the `[tui]` group (same locked version range as dev) or the console will ImportError at composition.
- **Phase 11 (run-config screen):** consumes `schemas/run_template.json` directly — the cross-phase D-07 contract; `effective_batch_size` GA semantics are recorded in the schema `$comment` and implemented child-side by run_finetune (Phase 7 D-10).
- **Lint/typecheck coverage:** the PHASE8_TUI wildcard and ty include list picked up both new service modules automatically — zero Makefile or pyproject edits this plan, exactly as the 08-02 design intended.

## Self-Check: PASSED

- All 5 code/schema/test files — FOUND (committed across `472c5a4`/`4146d15`/`7523235`/`0596737`)
- 2 tdd-evidence records — FOUND, both RED_EVIDENCE_OK-validated
- Task commits verified as ancestors of HEAD: `472c5a4`, `4146d15`, `7523235`, `0596737`
- Commit count measured from the persisted ledger: 4 production commits (`git rev-list --count de3cbc2..HEAD`)
- TDD gate: 2 `test(08-05):` + 2 `feat(08-05):` commits present (git log grep validated)
- Gates at plan close: tests/tui 109 passed; templates 26 + selection 30 green; schema-ok; make lint 0; make typecheck 0; make test-fast 669 passed; make ci 77 passed; pipeline/ + dnallm-mark/ diff-empty vs plan base
