---
phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
plan: 01
subsystem: pipeline
tags: [flops, torch, json-schema, calibration, cpu-testing, jsonschema]

# Dependency graph
requires:
  - phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
    provides: locked decisions D-01..D-27 (07-CONTEXT.md) and the legacy FlopsCounter source (dnallmmark_pipeline.py:43-720)
provides:
  - pipeline/flops_counter.py — CPU-importable FlopsCounter (20+ architecture dispatch, verbatim formulas, lazy torch seams, uncovered accounting, hardware builder, calibration_forward)
  - schemas/flops_report.json — the ratified v1 contract (D-27, one-way; schema_version 1, uncovered_layers, optional hardware)
  - pipeline/artifact_loader.py — load_json_artifact tolerant-read contract for the Phase 11 monitor and Phase 8 tui/services (PIPE-03)
  - Makefile PHASE7_MODULES existence-guarded lint list (auto-covers registry_loader.py when 07-02 lands)
affects: [07-02 registry overlay, 07-04 run_finetune integration, 07-05 legacy deletion + parity re-pins, 07-06 GB10 smoke, phase-08 tui/services, phase-11 monitor]

# Actuals (#2632) — same estimateTokens scale as the plan's estimate (chars/4
# over the realized diff base..HEAD, planning artifacts included).
actuals:
  tokens: 25000
  tasks: 3
  commits: 5

tech-stack:
  added: []  # zero external packages (T-07-SC: stdlib + existing pinned deps only)
  patterns:
    - "lazy torch seam (_torch_nn/_torch, never module-top) making GPU-side modules CPU-importable and stub-testable"
    - "stub-nn harness: plain classes + fire() closure invocation replacing torch forward hooks in tests"
    - "existence-guarded Makefile lint list (PHASE7_MODULES) so sibling plans join coverage without Makefile edits"

key-files:
  created:
    - pipeline/flops_counter.py
    - pipeline/artifact_loader.py
    - schemas/flops_report.json
    - tests/test_flops_counter.py
    - tests/test_artifact_loader.py
  modified:
    - Makefile

key-decisions:
  - "flops_report.json v1 published exactly as derived (publish-as-derived, maintainer decision at the Task-1 blocking-human checkpoint, 2026-10-11) — field names are now immutable downstream contract (D-27)"
  - "layer_details / total_flops_exact values typed number rather than integer: the verbatim HyenaFilter FFT formula emits fractional FLOPs (math.log2), and an integer map would reject legitimate writer output; integers validate identically, no ratified field name changed"
  - "three legacy-verbatim blind excepts kept with per-line `# noqa: BLE001` (the run_finetune D-08 precedent): ModernBERT layer-index parse, calibration retry trigger, calibration print-and-continue"

patterns-established:
  - "Lazy-seam port: GPU-only dependencies resolve through monkeypatchable accessors so the dev/CI lane imports and unit-tests pipeline modules"
  - "Duck-typed stub modules reproduce torch dispatch (isinstance + classname strings + name_or_path gating) without torch"

requirements-completed: [PIPE-03]  # PIPE-01 shared with 07-04/05/06 — completes when those plans finish (shared-ID gate)

coverage:
  - id: D1
    description: "FlopsCounter CPU-importable port: dispatch head + tail, verbatim hook formulas, lazy torch seam"
    requirement: PIPE-01
    verification:
      - kind: unit
        ref: "tests/test_flops_counter.py#test_linear_hook_counts_2NTIF, test_mha_hook_sums_projection_and_attention, test_conv1d_and_conv2d_hooks, test_layer_details_overwrite_while_total_accumulates"
        status: pass
      - kind: other
        ref: "uv run --group dev python -c \"import sys; sys.path.insert(0, 'pipeline'); import flops_counter, artifact_loader; print('cpu-import-ok')\""
        status: pass
    human_judgment: false
  - id: D2
    description: "Full 20+ architecture dispatch port with legacy-verbatim order and formulas, plus calibration_forward"
    requirement: PIPE-01
    verification:
      - kind: unit
        ref: "tests/test_flops_counter.py#test_mamba_ssm_hook_arithmetic, test_mamba2_ssd_hook_arithmetic, test_hyena_filter_hook_fft_terms, test_bigbird_sparse_hook_arithmetic, test_gqa_hook_windowed_for_flash_variant, test_flash_attn_hook_windowed_for_attention2, test_hf_conv1d_hook_arithmetic, test_linear_wins_over_borzoi_branch, test_calibration_forward_attention_mask_retry"
        status: pass
    human_judgment: false
  - id: D3
    description: "schemas/flops_report.json v1 published exactly as ratified at the Task-1 checkpoint (D-27 one-way contract)"
    requirement: PIPE-01
    verification:
      - kind: unit
        ref: "tests/test_flops_counter.py#test_round_trip_stub_calibration_schema_and_loadback, test_schema_version_is_pinned_to_1, test_schema_rejects_unknown_top_level_field, test_schema_hardware_section_contract, test_schema_accepts_fractional_layer_flops"
        status: pass
    human_judgment: false
  - id: D4
    description: "Uncovered-layer accounting with 0.05 parameter-share threshold and console WARNING (D-03)"
    requirement: PIPE-01
    verification:
      - kind: unit
        ref: "tests/test_flops_counter.py#test_param_owning_undispatched_module_is_uncovered, test_disabled_optional_branch_lands_in_uncovered, test_uncovered_share_warning_prints"
        status: pass
    human_judgment: false
  - id: D5
    description: "Tolerant artifact loader load_json_artifact: None sentinel for missing/empty/truncated/unreadable, valid-but-key-missing returned (PIPE-03, D-17/D-18/D-19)"
    requirement: PIPE-03
    verification:
      - kind: unit
        ref: "tests/test_artifact_loader.py#test_missing_file_returns_none, test_empty_file_returns_none, test_truncated_json_returns_none, test_unreadable_permissions_return_none, test_valid_json_without_expected_keys_is_returned, test_loader_is_stateless_across_calls"
        status: pass
    human_judgment: false
  - id: D6
    description: "Makefile lint coverage for the new modules via PHASE7_MODULES wildcard (registry_loader.py joins automatically in 07-02)"
    verification:
      - kind: other
        ref: "make lint — exit 0 with pipeline/flops_counter.py + pipeline/artifact_loader.py in the ruff file list"
        status: pass
    human_judgment: false

# Metrics
duration: 13 min
completed: 2026-10-11
status: complete
plan_head_before: 35469ff41b3bfa672b8cf2fe9e455318657cb05b
plan_head_after: f8fa845  # last production commit; the docs close-out commit follows this SUMMARY
---

# Phase 7 Plan 01: FLOPs Report Chain (FlopsCounter Port, Schema, Tolerant Loader) Summary

**CPU-provable FLOPs chain end-to-end: a torch-free-importable FlopsCounter port (20+ architecture hooks, verbatim formulas), the ratified flops_report.json v1 schema, and the tolerant loader contract — 57 stub tests, zero GPU, zero new dependencies**

## Performance

- **Duration:** 13 min (2026-10-11T06:30:05Z → ~06:48Z)
- **Tasks:** 3/3 (1 checkpoint resolved by continuation decision, 1 TDD tracer, 1 expansion)
- **Files:** 6 code files (5 created, 1 modified) + this SUMMARY
- **Commits:** 5 (measured `git rev-list --count 35469ff..HEAD`)

## Task 1 Decision Record (checkpoint:decision, gate=blocking-human)

**Decision:** `publish-as-derived` — publish the `flops_report.json` v1 schema
EXACTLY as derived from the locked decisions. No field-name amendments.

- **Decided by:** maintainer, 2026-10-11 13:46 CST (authoritative user decision
  delivered to the continuation executor; recorded before Task 2 started, per
  the checkpoint's completion criteria).
- **Ratified contract (D-02/D-03/D-05/D-27):** required legacy keys
  (`num_tokens`, `all_tokens`, `num_params`, `total_flops_G`,
  `total_flops_exact`, `total_flops_per_token`, `total_flops_all_tokens`,
  `computation_size_ratio`, closed `config`, open `layer_details`) +
  `uncovered_layers` (closed `{name, classname}` items, D-03) + optional
  `hardware` (`gpu_device` verbatim-string-or-null, `train_time`,
  `max_mem_gb`, D-05) + `schema_version` const 1 (D-27); draft-2020-12,
  `$id` under the repo raw.githubusercontent convention,
  `additionalProperties: false` on every closed object.
- **Consequence:** v1 field names are immutable downstream contract; Task 2
  published `schemas/flops_report.json` to this shape exactly.

## Accomplishments

- **FlopsCounter ported CPU-side** (`pipeline/flops_counter.py`): the full
  `_register_hooks` if/elif chain in exact legacy order — four torch.nn
  isinstance branches, the HF self-attn / flash / GQA / Mamba-SSM / Mamba2-SSD
  classname lists, the Caduceus singletons, the five string-compare
  singletons (incl. the legacy-sic `"ModernBertAttention"`), and the three
  model_path-gated branches (megadna, enformer|space, borzoi|flashzoi) placed
  AFTER every classname branch — with all ~24 hook closure factories verbatim
  (duck-typed reads intact). torch resolves only through the lazy
  `_torch_nn`/`_torch` seams, never at module top.
- **The one-way schema contract is live** (`schemas/flops_report.json`):
  ratified v1 shape, additive-only over the legacy writer, optional hardware
  section, synthetic-fixture + round-trip validation tests.
- **The tolerant loader contract is pinned** (`pipeline/artifact_loader.py`):
  read-then-decode parse-level tolerance returning the None sentinel;
  stdlib `json` + `pathlib` only; stateless (D-17/D-18/D-19). Phase 11
  monitor and Phase 8 `tui/services` import this.
- **Uncovered accounting (D-03)**: registration-time `uncovered_layers` list,
  `uncovered_param_share()` by named-parameters prefix matching, 0.05
  threshold WARNING at save time.
- **`calibration_forward`** ports the legacy no_grad single-sample chain
  (evo2 backbone case, bf16 autocast branch, plain branch, attention_mask
  retry, print-and-continue) for plan 07-04 to call before the DNATrainer
  construction.
- **Lint coverage future-proofed**: `PHASE7_MODULES` existence-guarded
  wildcard — `pipeline/registry_loader.py` joins `make lint` automatically
  when sibling plan 07-02 creates it; no later plan edits the Makefile.

## Task Commits

Each task was committed atomically (Task 2 as a TDD RED→GREEN pair):

1. **Task 1: checkpoint decision recorded** — `4d2d563` (docs)
2. **Task 2 RED: failing tests + import-only skeletons** — `22e1e9c` (test;
   22 target tests failing on planned assertions, 7 trivial-direction passes)
3. **Task 2 GREEN: chain implementation** — `7af37af` (feat; 29/29 green)
   — REFACTOR skipped: no cleanup exists that would not violate the
   verbatim-port discipline
4. **Task 3: full 20+ dispatch port + calibration_forward** — `f8fa845`
   (feat; 57/57 green)
5. **Plan metadata close-out** — this SUMMARY + STATE/ROADMAP/REQUIREMENTS

Tracer feedback gate (auto mode, `_auto_chain_active: true`): all three
Task-2 `<verify>` commands re-run end-to-end green before expansion
(`⚡ Tracer verified end-to-end — expanding`).

## Files Created/Modified

- `pipeline/flops_counter.py` — FlopsCounter port (lazy seams, full dispatch, uncovered accounting, save_to_json + schema_version/hardware, count_split_tokens, build_hardware_section, calibration_forward)
- `schemas/flops_report.json` — ratified v1 strict contract (D-27)
- `pipeline/artifact_loader.py` — `load_json_artifact` (PIPE-03)
- `tests/test_flops_counter.py` — 48 stub tests (harness, arithmetic, schema pins, dispatch order, lifecycle, calibration chain)
- `tests/test_artifact_loader.py` — 9 tolerant-read contract tests
- `Makefile` — PHASE7_MODULES lint list

## Decisions Made

- Task-1 checkpoint resolved `publish-as-derived` (see the Decision Record above).
- `layer_details` / `total_flops_exact` schema value type `number` (not
  `integer`): the verbatim HyenaFilter FFT formula emits fractional FLOPs, so
  an integer map would reject legitimate writer output — the plan's own
  key_link ("every key the writer emits is schema-valid") forced the wider
  type. Field names/structure unchanged; integers validate identically.
- Three legacy blind excepts kept verbatim with per-line `# noqa: BLE001`
  (run_finetune D-08 precedent) rather than narrowing catches the legacy
  never had.
- `run_finetune.py`, `run_sweep.py`, and its two tolerant-read sites
  untouched, exactly per D-20 and the plan's success criteria.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Schema integer map would reject fractional Hyena FLOPs**
- **Found during:** Task 2 (GREEN, schema authoring)
- **Issue:** the derived contract text said `layer_details` maps to integers,
  but the verbatim HyenaFilter formula (`math.log2` terms) yields fractional
  FLOPs — a strict integer map makes the schema reject reports the writer
  legitimately emits.
- **Fix:** `layer_details` values and `total_flops_exact` typed `number`
  (superset; integers validate identically); `$comment` documents why;
  `test_schema_accepts_fractional_layer_flops` and the Hyena report-validation
  test pin it.
- **Files modified:** schemas/flops_report.json, tests/test_flops_counter.py
- **Verification:** schema tests + Hyena round-trip validation pass
- **Committed in:** `7af37af` (test landed in RED `22e1e9c`)

**2. [Rule 1 - Bug] computation_size_ratio crashed on num_tokens=None**
- **Found during:** Task 2 (GREEN)
- **Issue:** legacy guarded only `total_params > 0`, so `num_tokens=None`
  (a schema-representable state — the ratio is nullable) raised
  `TypeError: None / int`.
- **Fix:** guard extended to `per_token_flops is not None and total_params > 0`.
- **Files modified:** pipeline/flops_counter.py
- **Verification:** `test_save_without_tokens_writes_null_extrapolations`
- **Committed in:** `7af37af`

**3. [Rule 1 - Bug] _hf_conv1d_hook bound the shape tuple to `b` for 3-dim inputs**
- **Found during:** Task 3 (per-family test run)
- **Issue:** the legacy ternary (`x.shape if x.dim() == 3 else (*x.shape, 1)[0]`)
  assigned the whole shape TUPLE to `b` in the 3-dim case — the normal
  hidden-states shape — so the hook raised inside the calibration forward,
  which the legacy try/except silently swallowed as under-counted FLOPs for
  Conv1D (GPT-2-style) models.
- **Fix:** 3-dim path reads `(x.shape[0], x.shape[1], x.shape[-1])` like every
  sibling hook; the 2-dim path is preserved exactly; in-code comment documents
  the divergence.
- **Files modified:** pipeline/flops_counter.py
- **Verification:** `test_hf_conv1d_hook_arithmetic` (3-dim input)
- **Committed in:** `f8fa845`

**4. [Rule 2 - Missing Critical] artifact_loader missed truncated-UTF-8 files**
- **Found during:** Task 2 (GREEN)
- **Issue:** a file truncated mid-multibyte character raises
  `UnicodeDecodeError` (a ValueError, not OSError/JSONDecodeError) at read
  time — still a truncated artifact, but it would crash the loader.
- **Fix:** read-side catch extended to `(OSError, UnicodeDecodeError)` → None.
- **Files modified:** pipeline/artifact_loader.py
- **Verification:** `test_truncated_utf8_sequence_returns_none`
- **Committed in:** `7af37af`

---

**Total deviations:** 4 auto-fixed (3 Rule-1 bugs, 1 Rule-2 missing error handling)
**Impact on plan:** All four were required for the writer/schema/loader to be
self-consistent; none touched the ratified field names or re-derived any
formula beyond repairing a destructuring bug. No scope creep.

## Issues Encountered

None beyond the deviations above. Ruff's 0.16 default profile surfaced 8
findings on first run (import sorting, `yield from`, `check=False`,
parenthesized concatenation, unused `math`/`model_path` in the Task-2 scope,
BLE001 on the legacy blind excepts) — all resolved inline; `make lint` green.

## TDD Note (Task 2)

Plan type is `execute` with one `tdd="true"` tracer task; the RED/GREEN gate
sequence was executed as `test(07-01)` → `feat(07-01)` commits with the RED
run captured before implementation (22 target-test assertion failures; the 7
passes are the trivial None-direction loader cases plus the import contract).
REFACTOR produced no commit — no behavior-neutral cleanup existed.

## Authentication Gates

None — no external services.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- 07-02 can create `pipeline/registry_loader.py` and inherits lint coverage
  automatically via the PHASE7_MODULES wildcard.
- 07-04 integrates the chain into `run_finetune.py`: calibration slot between
  the encode block and `reset_peak_memory_stats`, single post-success write
  ordered `final_metrics.json` → `flops_report.json` → `trainer_state.json`
  marker (WR-13), `build_hardware_section` fed from
  `torch.cuda.get_device_name()` / `train_runtime` / the `max_mem` read.
- 07-05 deletes `pipeline/dnallmmark_pipeline.py` and re-pins the 5 parity
  test sites as literals.
- 07-06 runs the GB10 smoke; the D-23 magnitude anchor
  (`total_flops_all_tokens` vs HF `total_flos`) applies to the schema-valid
  report this plan's writer emits.

---
*Phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re*
*Completed: 2026-10-11*

## Self-Check: PASSED

- All 6 key files exist on disk (5 created + Makefile modified + this SUMMARY)
- All 5 commits are ancestors of or equal to HEAD (`4d2d563`, `22e1e9c`,
  `7af37af`, `f8fa845`, and the docs close-out at HEAD); measured
  `git rev-list --count` from the plan ledger base = 5, matching frontmatter
- `gsd_run check evaluation-scope --plan 07-01 --commits-only` resolves with
  commits on this branch
- Plan-level verification re-run green: pytest 57/57, cpu-import-ok,
  `make lint` exit 0, `make typecheck` exit 0, full fast lane 507 passed /
  1 deselected (no regressions)
