---
phase: 19-tui-run-config-full-params
plan: "01"
subsystem: pipeline-passthrough
tags: [advanced-params, arg-family, dispatch-lane, passthrough, trainingconfig, table-driven]

requires:
  - phase: quick-261023-abu
    provides: the batch_size 9-surface passthrough precedent (8ea81fa) this plan generalizes table-driven
  - phase: 13-dynamic-dispatch-core
    provides: lane_values/claim JSONs/_RERUN_LANE_TOKENS + the 14-03 absent-parity replay design
provides:
  - "run_sweep.ADVANCED_TRAIN_FLAGS — the frozen 18-row NamedTuple param table (flag, kind, lo, hi, choices, default_display); THE shared advanced-param vocabulary for dispatch_core and (19-02) tui/services/run_config.py via their existing run_sweep imports"
  - "run_sweep.build_argv / launch_subprocess / run_matrix advanced: Mapping | None kwarg; the advanced argv block (alphabetical table order, immediately after --batch_size, before --cache_dir — PD-19-2)"
  - "run_sweep.advanced_flag_problems / collect_advanced — the table-driven guard + present-only collection helpers (single definition, consumed by dispatch_core's mirror)"
  - "sweep_flags['advanced'] nested manifest key (PD-19-7, only-when-non-empty)"
  - "dispatch_core: lane_values['advanced'] (ordinary + rerun tolerant per-entry), context['advanced'] + build_argv threading, dry-run mirror, ADVANCED_LANE_TOKENS derived into _RERUN_LANE_TOKENS (drift-proof)"
  - "run_finetune: the 18 argparse flags (local registration tuple; bool str-to-bool, json json.loads + dict-shape argv-boundary ValueError) + the PD-19-4 configs['finetune'] mutation loop (after variant reload + num_train_epochs override, before the default_grad_accum snapshot)"
affects:
  - "19-02 TUI run-config service/screen (consumes ADVANCED_TRAIN_FLAGS; pins the same PD-19-2 block position element-for-element)"
  - "19-03 driver + goldens"
  - "claim-lane replay consumers (14-03 MGPU-04 re-run) — advanced dicts replay verbatim"

actuals:
  tokens: 19943   # chars/4 over the realized 6-file diff (79771 chars)
  tasks: 3
  commits: 3      # measured: git rev-list --count c28c8cb..HEAD

plan_head_before: c28c8cb4b06b55a510d37382df1dfeefe3151c64
plan_head_after: bd545d0bde91e05d366180a1f333992bb5394008

tech-stack:
  added: []
  patterns:
    - "one frozen table (NamedTuple rows) driving argparse registration, guards, collection, argv block, lane mirrors, and DERIVED rerun tokens — drift structurally impossible (PD-19-6)"
    - "whole-family-as-one-dict lane key (PD-19-7): absent key = absent family = zero argv elements; lane homogeneity compares the dict as ONE value"
    - "tolerant per-entry replay filtered to table flags (unknown keys in a claim's advanced dict are dropped, never echoed verbatim from disk — T-19-02)"

key-files:
  created: []
  modified:
    - pipeline/run_sweep.py
    - pipeline/dispatch_core.py
    - pipeline/run_finetune.py
    - tests/test_sweep.py
    - tests/test_dispatch_core.py
    - tests/test_run_finetune_contracts.py

key-decisions:
  - "Table rows store DASHED flag literals ('--learning_rate') so the argparse target, the argv element, and the grep-gate literal are one string; field/lane keys derive by dash-strip (learning_rate — matches the existing undashed lane-key convention)"
  - "bool rides STRING choices ('true'/'false') at the run_sweep/dispatch layers; only the child converts (its _str_to_bool type callable) — one conversion point, the authoritative child"
  - "advanced_flag_problems/collect_advanced live in run_sweep and are called by dispatch_core's mirror (one definition, zero drift — the existing run_sweep._validate_* cross-module precedent)"
  - "lane_values['advanced'] and sweep_flags['advanced'] are written ONLY when non-empty — a no-flag launch records claims/manifests byte-identical to the pre-19 shape, and the 14-03 absent==None homogeneity projection stays consistent"
  - "Task 3 needed ZERO dispatch_core engine changes — the Task-1 mechanisms are loops over the table and scaled to 18 rows as designed (the derivation pin proves it)"
  - "cadence re-apply (deviation-recorded Rule-1): operator-threaded logging/eval/save_steps override the per-dataset derived cadence after its computation; absent flags keep the derived cadence byte-identical"

requirements-completed: ["TUI19-full-params", "P19-R2", "P19-R5"]

coverage:
  - id: D1
    description: "ADVANCED_TRAIN_FLAGS frozen 18-row table + the run_sweep family (argparse registration loop, collect-all bounds/json guards, nested manifest key, build_argv/launch_subprocess/run_matrix threading with the PD-19-2 alphabetical block)"
    requirement: "P19-R2"
    verification:
      - kind: unit
        ref: "tests/test_sweep.py#test_advanced_train_flags_row_matches_locked_table (18-row parametrize) + test_advanced_train_flags_table_is_exactly_the_locked_18 + test_build_argv_full_advanced_block_exact_alphabetical_order + test_cli_manifest_records_advanced_only_when_present"
        status: pass
      - kind: other
        ref: "real --dry-run with --learning_rate 0.0001 into a mktemp root; manifest cell asserted advanced.learning_rate == 1e-4 (tracer gate re-run)"
        status: pass
    human_judgment: false
  - id: D2
    description: "dispatch_core nested advanced family — ordinary + rerun lane_values (tolerant per-entry replay), worker context + build_argv threading, dry-run sweep_flags mirror, ADVANCED_LANE_TOKENS derived into _RERUN_LANE_TOKENS"
    requirement: "P19-R2"
    verification:
      - kind: unit
        ref: "tests/test_dispatch_core.py#test_rerun_replays_full_advanced_dict_verbatim + test_rerun_replays_partial_advanced_dict_partially + test_rerun_pre_change_claim_replays_advanced_absent + test_rerun_refuses_heterogeneous_advanced_lanes + test_rerun_token_family_derived_equals_the_18_table_flags + test_dispatch_dry_run_advanced_parity_with_run_sweep_dry_run"
        status: pass
    human_judgment: false
  - id: D3
    description: "run_finetune 18-flag argparse family (local tuple; bool str-to-bool, json dict-shape argv-boundary ValueError) + the PD-19-4 mutation loop placed between the num_train_epochs override and the default_grad_accum snapshot (threaded GA = snapshot base)"
    requirement: "P19-R2"
    verification:
      - kind: unit
        ref: "tests/test_run_finetune_contracts.py#test_advanced_family_parity_with_run_sweep_table + test_advanced_family_absent_from_extra_args_env_seam + test_advanced_train_flag_registered_and_mutation_slot_pinned"
        status: pass
    human_judgment: false
  - id: D4
    description: "Absent-parity guarantees — no advanced flag anywhere means zero argv elements, zero manifest keys, zero claim lane keys (byte-identical to HEAD); the tui defaults 10-element base argv lock stays green unmodified"
    requirement: "P19-R5"
    verification:
      - kind: unit
        ref: "tests/test_sweep.py#test_build_argv_absent_advanced_adds_zero_elements + tests/test_dispatch_core.py#test_dispatch_no_advanced_launch_records_no_advanced_lane_key + tests/tui/test_services_run_config.py#test_compose_argv_defaults_exactly_ten_base_elements (unmodified, green)"
        status: pass
    human_judgment: false

duration: 34 min
completed: 2026-10-23
status: complete
---

# Phase 19 Plan 01: Pipeline leg — ADVANCED_TRAIN_FLAGS + the 18 advanced params through run_sweep → dispatch_core → run_finetune Summary

**One frozen 18-row param table now drives the whole advanced chain: argparse families + bounds/json guards at both CLI layers, one nested "advanced" dict riding lanes/claims/manifests/worker context with proven absent parity and verbatim rerun replay, and a PD-19-4-placed configs["finetune"] mutation loop that makes threaded gradient_accumulation_steps the snapshot base.**

## Performance

- **Duration:** 34 min (07:04–07:39 UTC)
- **Started:** 2026-10-23T07:04:38Z
- **Completed:** 2026-10-23T07:39:06Z
- **Tasks:** 3/3
- **Files modified:** 6 (exactly the plan's files_modified)

## Accomplishments

- `run_sweep.ADVANCED_TRAIN_FLAGS`: the locked 18-row NamedTuple table (kinds/bounds inclusive sanity mirrors, live-probed 12-scheduler + 3-strategy vocabularies, base-YAML default_display) + one argparse registration loop, the table-driven `advanced_flag_problems`/`collect_advanced` helpers, `sweep_flags["advanced"]` only-when-non-empty, and the `advanced` kwarg on `build_argv`/`launch_subprocess`/`run_matrix` (bound explicitly, splat-filtered like `config_variant`).
- `dispatch_core`: `_RERUN_LANE_TOKENS` extended with the DERIVED `ADVANCED_LANE_TOKENS` (drift structurally impossible), the mirror guard + collection via the same run_sweep helpers, the nested lane key on ordinary + rerun paths (tolerant per-entry, filtered to table flags), `context["advanced"]` + the worker `build_argv` threading, and the dry-run mirror — all engine loops from the tracer, zero further engine changes in Task 3.
- `run_finetune`: the local 18-row registration tuple (bool = exact `true`/`false` type callable, json = `json.loads` + dict-shape `ValueError` at the argv boundary before the model loop), present-only collection, and the mutation loop at the locked slot (after the variant reload + `num_train_epochs` override, BEFORE the `default_grad_accum` snapshot — threaded GA becomes the snapshot base; bf16 documented as correctly-overridden by the fp32-only quirk block; warmup_ratio pinned OFF the extra_args env seam).
- Verification: 401 passing across the three pipeline suites (sweep 180, dispatch 141, contracts 80 — all pre-existing tests green unmodified); ruff + ty clean on all three pipeline files; the real `--dry-run` manifest carries `advanced.learning_rate == 1e-4`; zero diff to `run_sweep_shard.py`; the tui 10-element base argv lock green unmodified; the in-flight FHS sweep untouched (dry-run roots were `mktemp -d`, no GPU processes).

## Task Commits

Each task was committed atomically:

1. **Task 1: Tracer — table + learning_rate end-to-end** — `8f9a8d7` (feat) — tracer verified end-to-end (341 passed at the gate + the real dry-run manifest assertion), then expansion
2. **Task 2: Fill the table to 18 params + parity pins** — `31734e3` (feat)
3. **Task 3: dispatch full family — replay matrix + derived tokens** — `bd545d0` (feat, test-only: the Task-1 engine mechanisms scaled with the table)

## Files Created/Modified

- `pipeline/run_sweep.py` — the frozen table + spec NamedTuple, argparse loop, guard/collect helpers, advanced kwarg threading, PD-19-2 block, module-docstring family note
- `pipeline/dispatch_core.py` — derived rerun tokens, mirror guard/collection, nested lane key ×2, worker context, dry-run mirror, docstring lane lists
- `pipeline/run_finetune.py` — local tuple (18 rows), parse loop (bool/json kinds), collection + json boundary ValueError, PD-19-4 mutation loop, cadence re-apply
- `tests/test_sweep.py` — 38 advanced-family tests (locked-table pins, per-kind parses, refusals, full-18 element-for-element block, manifest parity); `extract_finetune_parse_args` widened
- `tests/test_dispatch_core.py` — 29 family tests (replay matrix, heterogeneous refusal, derived-token pin, 18-token refusal parametrize, dry-run parity)
- `tests/test_run_finetune_contracts.py` — registration + placement source-order pin, table parity, env-seam absence

## Decisions Made

- Dashed flag literals in both tables (`"--learning_rate"`): the argparse target, argv element, and the plan's grep gates are one string; lane/field keys derive by dash-strip (undashed, matching the existing lane-key convention).
- run_sweep's bool row keeps STRING choices; only the child converts to a real bool (one authoritative conversion point).
- The guard/collection helpers live in run_sweep and are imported by dispatch_core's mirror (one definition — the existing `run_sweep._validate_*` cross-module precedent), instead of hand-duplicating the mirror as the pre-19 flags did.
- Lane/manifest nested key only-when-non-empty (keeps claim JSONs byte-identical when unused AND keeps the 14-03 absent==None homogeneity projection consistent).
- Task 3 required no dispatch_core engine edits — confirmation, not new code, which is exactly what PD-19-6 derivation was for.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Cadence flags re-applied after the per-dataset derived cadence**
- **Found during:** Task 2
- **Issue:** the plan locks the whole mutation loop at the model-level slot, but run_finetune's per-dataset step calc (`step = num_train_data * epoch // (bs_new * grad_accum * num_gpus * 10)`) unconditionally OVERWRITES `logging_steps`/`eval_steps`/`save_steps` — a threaded `--logging_steps`/`--eval_steps`/`--save_steps` would have been a silently-dead no-op flag (the silent-no-op hazard this project's WR-07 family exists to prevent).
- **Fix:** after the derived-cadence writes, a guarded re-apply loop restores any operator-threaded cadence value (operator-explicit > derived — the same flag > file > default precedence every other knob uses). Absent flags keep the derived cadence byte-identical. The plan's locked model-level loop is unchanged and the placement pins still hold; this is an additional consumer of the collected dict, commented in place.
- **Files modified:** pipeline/run_finetune.py
- **Verification:** source pin (`advanced` cadence re-apply block present); default-path byte-parity covered by every pre-existing cadence test passing unmodified.
- **Committed in:** 31734e3 (Task 2 commit)

**2. [Rule 3 - Blocking] `extract_finetune_parse_args` exec namespace widened**
- **Found during:** Task 1
- **Issue:** run_finetune's `parse_args` became table-driven (module-level `ADVANCED_TRAIN_FLAGS` + `_str_to_bool` + `json`), so the existing exec-extraction seam in tests/test_sweep.py (`namespace = {"argparse": ..., "Path": ...}`) would NameError the moment the extracted function ran.
- **Fix:** the extraction regex now starts at the `ADVANCED_TRAIN_FLAGS = (` literal so the tuple + helper + `parse_args` extract together, with `json` added to the namespace.
- **Files modified:** tests/test_sweep.py
- **Verification:** `test_build_argv_subset_tail_parses_as_run_finetune_argv` green unmodified.
- **Committed in:** 8f9a8d7 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes keep the plan's locked placements intact and add no scope; without #1 three of the 18 flags would have been inert.

## Issues Encountered

- The plan's quoted suite baseline ("117 + 92 + 77 = 286") undercounts the actual HEAD suites (141 + 112 + 77 = 330 pre-change); the post-change totals are 180 + 141 + 80 = 401, all green, zero pre-existing tests weakened or modified (only the `extract_finetune_parse_args` helper internals and one added parametrize row touched existing test code, both additive).
- `mktemp -d` on this box resolves under `/root/autodl-tmp/tmp` (TMPDIR policy), so the plan's `/tmp/*/p19-tracer` glob needed the local tmp root added — assertion logic unchanged.
- WINDOWS ledger append of the #1 deviation failed on a PRE-EXISTING count mismatch (frontmatter 50 vs entries 49 — present before this plan; left untouched per the never-touch-dirt constraint). The deviation is fully documented here instead.

## Known Stubs

None — every chain hop is test-pinned end-to-end, and the real dry-run manifest assertion ran green.

## Auth Gates

None.

## Next Phase Readiness

- 19-02 can consume `run_sweep.ADVANCED_TRAIN_FLAGS` via the existing import (the table is the shared vocabulary — kinds/bounds/choices/default_display drive the TUI rows, parsers, dropdowns, and placeholders); the PD-19-2 block position and PD-19-7 nested-key semantics are pinned by this plan's tests for element-for-element mirroring in `compose_argv`/`compose_dispatch_argv`.
- EBS-vs-GA interplay (EBS recomputes GA and wins) and the variant-YAML default variance (Pitfall 3) are documented in code comments here and should surface in 19-02's hint copy.

## Self-Check: PASSED

All six modified files exist on disk; commits 8f9a8d7, 31734e3, bd545d0 verified as ancestors of HEAD (bd545d0); `git diff c28c8cb..HEAD --name-only` equals exactly the plan's files_modified; zero diff to pipeline/run_sweep_shard.py.

---
*Phase: 19-tui-run-config-full-params*
*Completed: 2026-10-23*
