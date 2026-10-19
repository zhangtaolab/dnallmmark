---
phase: 09-custom-model-dataset-onboarding
plan: 09-01
subsystem: tui/services custom onboarding (non-visual service tier)
tags: [custom-registry, validation, collect-all, metric-registry, import-export, json-schema]
requires:
  - "Phase 8 settings rails (settings.config_dir + atomic_write, D-04/T-08-03)"
  - "Phase 7 registry overlay seam (registry_loader, CUST-05/D-06..D-08)"
  - "Phase 8 jsonschema + committed-schema discipline (schemas/run_template.json, D-07)"
provides:
  - "custom_entries: the ONLY custom-registry write seam (read/land/undo/set_enabled/read_import_candidates/export_registry)"
  - "custom_validation: D-05 collect-all validator (full CUST-03 matrix) + METRIC_REGISTRY (28, parity-locked) + validate_import_document"
  - "schemas/custom_registry.json: the committed entry-shape contract for imported/exported files"
  - "WIZ_PROBLEM_* / WIZM_/WIZD_ strings block: validation copy + field labels for the 09-04/09-05 wizard screens"
affects:
  - "tui/strings.py (additive WIZ_ block; no existing constant touched)"
actuals:
  tokens: 28235
  tasks: 3
  commits: 6
plan_head_before: 7413567aefe2f27a57c5372d5daad992d1231012
plan_head_after: 501002145f152d63d4a96541fbf2eb7d8eb739c2
tech-stack:
  added: []  # zero new packages (T-09-SC: jsonschema/platformdirs Phase 8-locked)
  patterns:
    - "fourth _validate_filters-discipline collect-all instance (field-definition ordered, one-defect-one-problem)"
    - "frozen twin constant + tier-1 parity test (METRIC_REGISTRY vs SUITE_CANONICAL; runtime import impossible)"
    - "audit-kernel CSV parse mirror (utf-8 csv.reader, header membership, malformed-row skip) with the authoritative measurement left to the 09-02 subprocess"
key-files:
  created:
    - tui/services/custom_entries.py
    - tui/services/custom_validation.py
    - schemas/custom_registry.json
    - tests/tui/test_services_custom_entries.py
    - tests/tui/test_services_custom_validation.py
    - tests/tui/test_services_custom_validation_import.py
  modified:
    - tui/strings.py
key-decisions:
  - "Store = single write seam: land/undo/set_enabled all route through settings.atomic_write; land relativizes absolute paths (Pitfall 4), stamps Model_name/Dataset_name = key (Pitfall 6/11), coerces Train/Dev/Test ints with bool excluded; the wizard's key form field is dropped from landed entries"
  - "METRIC_REGISTRY = frozen 28-name SUITE_CANONICAL twin in tui/services/custom_validation, parity-locked by a tier-1 test that imports export_runs via the tests/conftest.py sys.path; the service module never imports it (AST import lock)"
  - "One-defect-one-problem collect-all: numeric checks skip absent/empty values (the required check owns them); enum checks skip empty injected vocabularies (partially-built sources never fail candidates); split int-strict check runs even when the dataset dir does not resolve"
  - "Declared Train/Dev/Test derive from split counting (the wizard never collects them): present int declarations must equal the well-formed row counts; absent declarations are legal and derived at composition"
  - "schemas/custom_registry.json = per-ENTRY contract under the run_template discipline: plain {key: entry} file top level (NO envelope — the loader merges every top-level key), optional per-entry schema_version const 1, kind-appropriate custom-only fields (quirks model-only, label_column dataset-only), required = the wizard-required subset, field types probed from the official registries"
  - "Export = byte-verbatim shutil.copyfile of the user-owned file (hash-pinned); empty/absent/unreadable registry yields the (False, diagnostic) empty-state signal creating nothing at the destination"
patterns-established:
  - "ValidationSources dataclass = the D-05 injection seam (official keys, existing customs, metric registry, fs root, observed vocabularies) — the 09-04/09-05 screens construct it from registry_loader + custom_entries + METRIC_REGISTRY"
  - "Import gate = tolerant read (custom_entries.read_import_candidates, file order preserved) + strict collect-all validation (custom_validation.validate_import_document) — nothing merges on any problem; the 09-05 sequential gauntlet consumes candidates in file order"
requirements-completed: [CUST-01, CUST-02, CUST-03, CUST-06]
coverage:
  - id: TRAC-01
    description: "Tracer: land a synthetic candidate into a tmp config+overlay dir -> registry_loader.load_models_registry()/load_datasets_registry() see it merged over the official 62/50; undo returns to official-only"
    requirement: CUST-01/CUST-02 (the write->overlay-load substrate)
    verification:
      - kind: automated
        ref: "tests/tui/test_services_custom_entries.py::test_tracer_land_then_overlay_load_then_undo"
        status: pass
      - kind: automated
        ref: "uv run --group dev --group tui pytest tests/tui -q (259 passed)"
        status: pass
    human_judgment: false
    rationale: ""
  - id: CUST03-MATRIX
    description: "Full nine-check collect-all matrix (required/name-format, numerics with bool exclusion, enums incl. metric registry, collisions official+custom, path existence under injected fs root, split parseability/row-count/label-column, declared==counted) in field-definition order; never raises on untrusted input; non-UTF-8 CSVs yield problem lines"
    requirement: CUST-03
    verification:
      - kind: automated
        ref: "tests/tui/test_services_custom_validation.py (43 tests: enum/path/split/encoding/copy-lock matrix)"
        status: pass
      - kind: automated
        ref: "tests/tui/test_services_custom_validation.py::test_metric_registry_parity_with_suite_canonical (== SUITE_CANONICAL, len 28)"
        status: pass
    human_judgment: false
    rationale: ""
  - id: CUST06-SERVICES
    description: "Service tier of marking/disable/export: set_enabled writes the literal JSON boolean (absence = enabled); read_entries is the management-view direct read (disabled entries stay visible); export_registry is the byte-verbatim share unit; import is fail-closed collect-all over schemas/custom_registry.json"
    requirement: CUST-06
    verification:
      - kind: automated
        ref: "tests/tui/test_services_custom_entries.py (enabled/undo/atomic-write/hash-pinned official files)"
        status: pass
      - kind: automated
        ref: "tests/tui/test_services_custom_validation_import.py (22 tests: schema contract, both collision kinds one pass, file order, byte-identical export, empty-state)"
        status: pass
      - kind: automated
        ref: "uv run --group dev python -c schema check (schema-valid True)"
        status: pass
    human_judgment: false
    rationale: ""
  - id: BINDING-11
    description: "Official registries provably untouched across every write path (hash-pinned across land/undo/toggle; git-clean)"
    requirement: CUST-01/CUST-02 binding constraint 11
    verification:
      - kind: automated
        ref: "tests/tui/test_services_custom_entries.py::test_official_registries_hash_unchanged_across_all_writes"
        status: pass
    human_judgment: false
    rationale: ""
duration: 47 min
completed: 2026-10-12
status: complete
---

# Phase 09 Plan 01: Custom Onboarding Service Tier Summary

Non-visual custom-onboarding foundation: the user-owned registry store (land/undo/toggle/import-candidates/export through one atomic write seam), the D-05 collect-all field validator covering the full CUST-03 nine-check matrix with a 28-name SUITE_CANONICAL-parity metric registry, and the committed per-entry JSON schema governing imported files — proven end-to-end headless by the tracer (a landed candidate is visible through the Phase 7 overlay seam: 63/51 merged, undo returns 62/50).

## Performance

- 3/3 tasks, 6 commits, ~47 min (estimate: 32000 tokens / 3 tasks; actual ~28235 tokens — estimate 13% high, within confidence)
- Tests: 82 new tier-1 tests across three lanes; full tests/tui = 259 green (all Phase 8 suites untouched); make lint + make typecheck zero findings/diagnostics (zero Makefile edits — the PHASE8_TUI wildcard and ty src-include picked up every new file)

## Accomplishments

- **Task 1 (tracer, 2ba1c3c):** the custom-registry store + validator skeleton with the write -> overlay-load seam proven headless before any UI exists — a synthetic model+dataset candidate landed under a tmp `DNALLMMARK_TUI_CONFIG_DIR` that is also `DNALLMMARK_CUSTOM_REGISTRY_DIR` is seen by `registry_loader.load_models_registry()/load_datasets_registry()` (63/51 over the official 62/50); undo returns official-only. Tracer feedback gate re-ran the verify end-to-end (auto mode) — green, expanded.
- **Task 2 (TDD, 4b941f7 + 8f93103):** the full CUST-03 collect-all matrix — enums (Category/type/model type/injected species+tokenizer vocabularies/metric registry), path existence under the injected fs root (absolute as-is, relative vs root), split-file checks mirroring the audit kernel's exact CSV discipline (utf-8 csv.reader, header sequence+label membership, malformed-row skip, row count > 0, declared == counted), non-UTF-8 tolerance, CJK label columns — plus METRIC_REGISTRY (frozen 28 names) parity-locked to `export_runs.SUITE_CANONICAL`, and all problem copy moved into `tui/strings.py` (zero inline CJK in the service, source-scan locked).
- **Task 3 (TDD, 9b5b488 + 517f821):** `schemas/custom_registry.json` (strict draft 2020-12 entry-shape contract: plain {key: entry} top level, pipeline-relative path rule in $comment, wizard-required subsets, Category/type enums, custom-only enabled/quirks/label_column, inert optional Index + per-entry schema_version const 1), `validate_import_document` (per-entry jsonschema collect-all + both collision families in file order), `read_import_candidates` (tolerant file-ordered read), `export_registry` (byte-verbatim copy; empty-state signal creates nothing).

## Task Commits

| Task | Commit | Type |
|------|--------|------|
| 1 — tracer store + validator skeleton + overlay seam | 2ba1c3c | feat(09-01) |
| 2 — RED: full CUST-03 matrix tests | 4b941f7 | test(09-01) |
| 2 — GREEN: matrix + METRIC_REGISTRY + strings | 8f93103 | feat(09-01) |
| 3 — RED: import/export tier tests | 9b5b488 | test(09-01) |
| 3 — GREEN: schema + import validate-before-merge + export | 517f821 | feat(09-01) |
| 3 — ty-clean test fixtures (typecheck gate) | 5010021 | fix(09-01) |

## Files Created/Modified

Created: `tui/services/custom_entries.py`, `tui/services/custom_validation.py`, `schemas/custom_registry.json`, `tests/tui/test_services_custom_entries.py`, `tests/tui/test_services_custom_validation.py`, `tests/tui/test_services_custom_validation_import.py`. Modified: `tui/strings.py` (additive WIZ_ block).

## Decisions Made

See key-decisions in frontmatter. Highlights: the single-write-seam store design; the frozen-twin + parity-test metric custody (no runtime import); one-defect-one-problem collect-all semantics; derived (never wizard-collected) Train/Dev/Test declarations; the per-entry schema contract with kind-appropriate custom-only fields.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Double-reported field defects in the numeric checks**
- **Found during:** Task 1 verify (first pytest run)
- **Issue:** an empty/None required-numeric value yielded BOTH a required problem and a numeric problem for the same field.
- **Fix:** numeric checks skip values the required check owns (`_is_absent`) — one field defect yields one problem.
- **Files modified:** `tui/services/custom_validation.py`
- **Commit:** 2ba1c3c (fixed before the tracer commit)

**2. [Rule 3 - Blocker] ty failures in test fixtures (make typecheck gate)**
- **Found during:** plan-level verification
- **Issue:** `ValidationSources(**base)` dict-unpacking builders and bare `node.lineno` on `ast.AST` tripped ty's invalid-argument-type/unresolved-attribute (7 diagnostics).
- **Fix:** explicit keyword construction with module-level vocabulary constants; `getattr(node, 'lineno', '?')`.
- **Files modified:** both validation test files
- **Commit:** 5010021

**3. [Process - RED evidence format]** The gate's report parser accepts TAP/JUnit/Swift/unittest — plain pytest `-q` text is "Unsupported report format". Re-captured both RED records with pytest's built-in `--junitxml` (zero new dependencies). The plan's verify command `python -c "... '$defs' in s"` needed single-quote shell quoting (`$defs` expands under double quotes); run correctly it prints `schema-valid True`. Neither changed planned behavior.

## Issues Encountered

None beyond the deviations above. No auth gates, no checkpoints (fully autonomous plan; tracer feedback gate passed in auto mode).

## TDD Gate Compliance

Both tdd tasks followed RED -> GREEN with persisted, gate-validated evidence (INVALID_RED guarded):

- **Task 2 RED** (`RED_EVIDENCE_OK`, target `test_metric_registry_parity_with_suite_canonical`): 21 fail / 22 pass — every failing test a planned matrix assertion; the 22 passing confirmed fixtures sound. Records: `.planning/tmp/09-01-task2-red.json` (gitignored path, evidence re-verifiable via `gsd-tools check tdd-red-evidence`).
- **Task 3 RED** (`RED_EVIDENCE_OK`, target `test_schema_file_is_valid_draft_2020_12`): 22 fail / 0 pass — an entirely new module's intentional RED.
- Both GREEN phases ran the FULL suite (not just the target test) before their feat commits; no test was weakened to pass.

## Known Stubs

None — every function is wired and tested; no TODO/FIXME/placeholder markers in the new files.

## User Setup Required

None. The user-owned `~/.config/dnallmmark/custom_{models,datasets}.json` files are created at runtime by `land()` — never committed, nothing for the operator to pre-create.

## Next Phase Readiness

- 09-02 (gauntlet) consumes: `custom_entries.read_entries` (existing-custom staging), `custom_validation.METRIC_REGISTRY`/`ValidationSources`, and lands through `custom_entries.land` after its subprocess gates pass; the D-09 `enabled:false` loader skip lands there.
- 09-04/09-05 (wizard screens) consume: `validate_model_candidate`/`validate_dataset_candidate` (problems -> numbered report lines via `WIZ_PROBLEMS_HEADER`/`WIZ_PROBLEM_LINE`/`WIZM_/WIZD_FIELD_LABELS`), `read_import_candidates` + `validate_import_document` (the f-key import flow), `export_registry` (o-key), `set_enabled`/`undo` (e/u keys).
- Success criteria all confirmed: headless validate->land->read-back( incl. disabled)->overlay-visible chain; metric enum parity-locked at 28; import fail-closed collect-all + byte-verbatim export; official registries hash-pinned untouched.

## Self-Check: PASSED

All 6 task commits are ancestors of HEAD (2ba1c3c, 4b941f7, 8f93103, 9b5b488, 517f821, 5010021); all 7 artifact files exist on disk; measured commits from the persisted ledger (`gsd-plan-head-before-09-01`) = 6, matching `actuals.commits`; official registries git-clean.
