---
phase: quick-261014-c2l
plan: 01
subsystem: pipeline
tags: [run_finetune, run_sweep, storage-roots, tui, run-config, argv-parity]

requires:
  - phase: 07-03 / 11-01 / 11-02
    provides: the --cache_dir-style pass-through flag family (build_argv/launch_subprocess/sweep_flags seams) and the slot-4 RunSpec/compose_argv/DirPlan service the roots thread through
provides:
  - pipeline --model_root/--dataset_root flags (run_finetune resolution override + run_sweep pass-through threading, manifest recording, WR-05 empty refusal)
  - RunSpec.model_root + live default-None dataset_root (D-19 retired) with the legacy "./datasets" tolerant-load mapping
  - slot-4 screen #cfg-input-model-root row + prompt-hint pair + regenerated run_config.svg golden
affects: [run_sweep_shard passthrough, TUI launch gate, sweep manifest consumers]

actuals:
  tokens: 48245   # chars/4 over the realized diff (192,979 chars incl. the regenerated SVG; code-only diff is 62,056 chars ~ 15,514)
  tasks: 3
  commits: 3       # measured: git rev-list --count 9f9404a..HEAD
plan_head_before: 9f9404a
plan_head_after: 451782d

tech-stack:
  added: []         # zero new dependencies anywhere (T-c2l-SC)
  patterns:
    - "override-aware base with byte-identical None branch: base = base_dir if flag is None else flag.rstrip(os.sep) + os.sep (absent-flag expressions stay byte-identical string concatenations)"
    - "retired-default tolerant-load migration: LEGACY_DATASET_ROOT_DEFAULT maps the exact pre-change literal to unset — no schema_version bump, byte-identical launches"
    - "pinned argv tail order shared by run_sweep.build_argv and run_config.compose_argv: --cache_dir, --model_root, --dataset_root"

key-files:
  created: []
  modified:
    - pipeline/run_finetune.py
    - pipeline/run_sweep.py
    - tui/services/run_config.py
    - tui/screens/run_config.py
    - tui/strings.py
    - tests/test_sweep.py
    - tests/test_run_finetune_contracts.py
    - tests/tui/test_services_run_config.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_strings_phase11.py
    - tests/tui/__snapshots__/run_config.svg

key-decisions:
  - "Flag spelling UNDERSCORE everywhere (the plan's objective pre-decided the description's hyphen slip); flags join the --subset_file/--cache_dir underscore pass-through family"
  - "ADD-ALONGSIDE, not promote: script-dir (base_dir) resolution stays the default; rstrip+sep normalization applies ONLY to the flag form so exactly one separator joins root and registry value"
  - "D-19 retirement shape: RunSpec.dataset_root default flips to None and DEFAULT_DATASET_ROOT renames LEGACY_DATASET_ROOT_DEFAULT consumed only by the tolerant-load migration (pre-change './datasets' state files launch byte-identically)"
  - "Manifest records present roots in every cell via sweep_flags (T-c2l-02 mitigation): a storage-root override changes WHICH weights/files a cell consumed — provenance worth recording"

requirements-completed: [C2L-01, C2L-02, C2L-03]

coverage:
  - id: D1
    description: "Pipeline override flags end-to-end: run_finetune resolves registry Model_path/Dataset_path under --model_root/--dataset_root when present and under its own script dir byte-identically when absent; run_sweep refuses empty values, resolves absolute, threads into every child argv and records in every manifest cell when present, zero argv elements/keys when absent"
    requirement: C2L-01
    verification:
      - kind: unit
        ref: "tests/test_sweep.py#test_cli_resolves_storage_roots_to_absolute_paths, #test_manifest_records_resolved_storage_roots, #test_build_argv_threads_storage_roots_as_list_elements, #test_cli_empty_model_root_value_aborts, #test_cli_whitespace_dataset_root_value_aborts, #test_sweep_flags_default_to_none_in_parse_args, #test_build_argv_absent_flags_add_zero_elements, #test_dry_run_manifest_absent_flags_add_no_keys"
        status: pass
      - kind: unit
        ref: "tests/test_run_finetune_contracts.py#test_storage_root_flags_declared_in_parse_args, #test_storage_root_unpack_precedes_model_loop, #test_override_aware_bases_rewire_both_resolution_sites"
        status: pass
    human_judgment: false
  - id: D2
    description: "RunSpec model_root field + live dataset_root threading in the run-config service: compose_argv threads both present-only absolute in the pinned tail order; persistence round-trips the new key; a pre-change persisted './datasets' state file loads as unset and launches byte-identically; defaults spec still composes exactly 10 base elements"
    requirement: C2L-02
    verification:
      - kind: unit
        ref: "tests/tui/test_services_run_config.py#test_runspec_defaults, #test_compose_argv_full_spec_element_for_element, #test_compose_argv_defaults_exactly_ten_base_elements, #test_compose_argv_threads_both_storage_roots_when_set, #test_persistence_round_trip_full_spec, #test_legacy_dataset_root_default_loads_as_unset, #test_legacy_custom_dataset_root_loads_through_live, #test_importing_service_leaves_gpu_stack_absent"
        status: pass
    human_judgment: false
  - id: D3
    description: "Run-config screen model-root input: renders with label + prompt hint, populates from and persists into the spec, drives the advisory path state, and threads --model_root; dataset-root input defaults empty with its prompt hint; strings inventory lock green; the only regenerated golden is run_config.svg, committed with the change"
    requirement: C2L-03
    verification:
      - kind: automated_ui
        ref: "tests/tui/test_pilot_run_config.py#test_params_defaults_render, #test_params_input_values_render_in_export, #test_model_root_input_threads_absolute_flag_into_argv"
        status: pass
      - kind: unit
        ref: "tests/tui/test_strings_phase11.py#test_cfg_lnc_mon_string_inventory_defined, #test_cfg_lnc_mon_inventory_complete_no_unlisted_constants"
        status: pass
      - kind: automated_ui
        ref: "tests/tui/test_snapshots.py#test_run_config_golden (make snapshot-update; git status over __snapshots__/ shows ONLY run_config.svg)"
        status: pass
    human_judgment: false

duration: 28min
completed: 2026-10-14
status: complete
---

# Quick Task 261014-c2l: Custom model/dataset storage directories Summary

**--model_root/--dataset_root storage-root overrides across run_finetune (verbatim registry-path resolution), run_sweep (absolute pass-through threading + manifest provenance), and the slot-4 TUI (live dataset_root, new model_root field, prompt-hint defaults, regenerated golden) — byte-identical when absent**

## Performance

- **Duration:** 28 min (00:51:56Z → 01:20:02Z; gate re-runs after)
- **Started:** 2026-10-14T00:51:56Z
- **Completed:** 2026-10-14T01:20:02Z
- **Tasks:** 3
- **Files modified:** 11

## Accomplishments
- Pipeline flags end-to-end: run_finetune resolves registry Model_path/Dataset_path under the flagged root verbatim (`--model_root /root/autodl-tmp` + `models/Chaoba` → `/root/autodl-tmp/models/Chaoba`) with byte-identical base_dir resolution when absent (grep spot check: `base_dir + model_row` gone; `base_dir if model_root is None` on the None branch)
- run_sweep pass-through family: WR-05 empty refusal twins, D-15 absolute resolution, pinned child-argv tail `--cache_dir, --model_root, --dataset_root`, present roots recorded in EVERY manifest cell (T-c2l-02 mitigation), zero argv elements / zero manifest keys when absent; run_sweep_shard needed no changes (unknown tokens pass through verbatim)
- Service: RunSpec.model_root added, dataset_root default None (D-19 retired), LEGACY_DATASET_ROOT_DEFAULT tolerant mapping keeps pre-change `./datasets` state files launching byte-identically (no schema_version bump), compose_argv/DirPlan/resolve_dirs/persistence all threaded
- Screen: #cfg-input-model-root row mirroring the dataset-root row exactly, dataset-root input defaults empty with the "—（默认 pipeline/）" prompt hints, advisory path states wired, run_config.svg the only regenerated golden (committed with its cause)

## Task Commits

Each task was committed atomically:

1. **Task 1: Pipeline override flags end-to-end (tracer)** - `5074408` (feat)
2. **Task 2: RunSpec model_root + live dataset_root threading** - `153c6cf` (feat)
3. **Task 3: Screen model-root input + strings + golden** - `451782d` (feat)

## Files Created/Modified
- `pipeline/run_finetune.py` - both flags in parse_args; override-aware model_base/dataset_base (None branch keeps base_dir verbatim; flag branch rstrip+sep); both resolution sites rewired
- `pipeline/run_sweep.py` - flags in parse_args; WR-05 empty twins; absolute resolution; sweep_flags threading + manifest recording; build_argv/launch_subprocess keyword params in the pinned tail order; module docstring family paragraph
- `tui/services/run_config.py` - RunSpec fields + docstrings; compose_argv tail; DirPlan projections; persistence key; legacy migration; D-14/D-19 contract block updated
- `tui/screens/run_config.py` - model-root row + advisory; dataset-root empty default + hint; populate/compose/dir-states/advisory seams
- `tui/strings.py` - CFG_FIELD_MODEL_ROOT, CFG_MODEL_ROOT_DEFAULT, CFG_DATASET_ROOT_DEFAULT (all registered in the IN-09 inventory)
- `tests/test_sweep.py`, `tests/test_run_finetune_contracts.py`, `tests/tui/test_services_run_config.py`, `tests/tui/test_pilot_run_config.py`, `tests/tui/test_strings_phase11.py` - the same-change test lanes
- `tests/tui/__snapshots__/run_config.svg` - regenerated (the only golden drift)

## Decisions Made
- Followed the plan's pre-decided items verbatim: underscore spelling, verbatim join semantics, ADD-ALONGSIDE override, legacy-mapping shape, pinned tail order shared with build_argv
- The Pilot interaction test uses the persisted-spec path over the REAL `run_config_service.compose_argv` (the established fake's compose_argv is display-only — the plan's "else" branch)
- The export-SVG presence assert pins the prompt hints by their stable "—（默认" prefix (the SVG encodes the inner space as `&#160;`, so the contiguous constant never appears) plus the retired `./datasets` absence and the new label presence

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `make test` shows 10 failures — ALL pre-existing at the base commit 9f9404a (verified in a temporary worktree, identical failures): 5 schema/determinism pins stale after the helixgen data commit 9bc68e1, and 5 persist-failure-simulation tests ineffective when pytest runs as root (root bypasses chmod read-only). Out of scope per the scope boundary; logged to `deferred-items.md` in this directory. Everything this plan touches is green; the node lane matches baseline (26 pass).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Models/datasets can live outside the system disk: `python pipeline/run_sweep.py ... --model_root /root/autodl-tmp --dataset_root /root/autodl-tmp` (recorded in every manifest cell), or via the slot-4 目录 section inputs
- Pre-existing data-side failures (deferred-items.md) need the data owner's reconciliation before the next full `make test` gate can read green end-to-end

## Self-Check: PASSED

- All 11 modified artifacts exist on disk (SUMMARY, deferred-items, the 5 production files, the 5 test files incl. the regenerated golden)
- All 3 task commits (5074408, 153c6cf, 451782d) verified as ancestors of HEAD; `git rev-list --count 9f9404a..HEAD` == 3 (measured, matches `commits:` in frontmatter)
- `status: complete` present in frontmatter
- Working tree carries only uncommitted orchestrator-owned docs (SUMMARY.md, deferred-items.md, STATE.md, WINDOWS.md)

---
*Quick task: 261014-c2l*
*Completed: 2026-10-14*
