---
phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
plan: 04
subsystem: pipeline
tags: [flops, calibration, torch-hooks, wr-13, source-contract-tests, hardware-section]

# Dependency graph
requires:
  - phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
    provides: pipeline/flops_counter.py (FlopsCounter, count_split_tokens, calibration_forward, build_hardware_section, save_to_json with schema_version/uncovered_layers/hardware — 07-01)
  - phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
    provides: run_finetune module-level registry loads through registry_loader with exec-extract spans byte-stable (07-02)
provides:
  - run_finetune.py FLOPs integration — the always-on pre-training calibration slot (hooks registered, ONE no_grad forward, hooks removed BEFORE the DNATrainer ctor) and the single post-success flops_report.json write (WR-13-ordered, hardware section)
  - Four new source-contract tests locking calibration position, hook lifetime, write ordering, and rank guarding
affects: [07-05 legacy deletion + parity re-pins, 07-06 GB10 smoke (GPU emission proof), phase-11 monitor (reads flops_report.json), phase-08 tui/services]

# Actuals (#2632) — same estimateTokens scale as the plan's estimate (chars/4
# over the realized diff base..HEAD, planning artifacts included).
actuals:
  tokens: 7000
  tasks: 2
  commits: 3

tech-stack:
  added: []  # zero external packages (T-07-SC vacuous)
  patterns:
    - "loop-local stash across the train boundary: flops_counter/current_tokens/total_tokens stay alive from the calibration slot to the rank-0 success block — no module globals, no new run_finetune functions (Pitfall 1)"
    - "write-time hardware capture: max_mem_gb read inside the success block BEFORE trainer.evaluate() so the peak scopes to training, not post-block flow"

key-files:
  created: []
  modified:
    - pipeline/run_finetune.py
    - tests/test_run_finetune_contracts.py

key-decisions:
  - "build_hardware_section joins the sibling import in Task 2's commit, not Task 1's — ruff F401 (unused import) would fail the Task-1 atomic lint gate; the plan's end state is identical, only the commit boundary moved (commit-hygiene sequencing)"
  - "max_mem_gb computed at write time inside the rank-0 success block (per plan), which is BEFORE trainer.evaluate() — the value therefore scopes to the training peak, arguably stricter than D-05's wording; the later print-only max_mem read at :1648+ is untouched"
  - "rank-guard membership proven textually via indentation depth (save_to_json line deeper than the `if local_rank == 0:` guard) plus a statement_index-anchored trainer.evaluate() upper bound — plain src.find matched the new block's own comment text, so the file's line-anchored helper was used (established idiom)"

patterns-established:
  - "Calibration-slot shape for any future pre-train instrumentation: count AFTER fraction apply, construct unconditionally, single no_grad forward via flops_counter.calibration_forward, remove_hooks in BOTH branches, stash loop-locals for the post-success write"
  - "Three-artifact WR-13 chain: final_metrics.json < flops_report.json < trainer_state marker copy, contract-tested by source-order index comparison"

requirements-completed: [PIPE-01]  # shared with 07-01/05/06 — completes only when those plans finish (shared-ID gate; 07-05/07-06 summaries still absent)

coverage:
  - id: D1
    description: "Always-on FLOPs calibration slot (D-01): FlopsCounter constructed unconditionally inside the dataset loop after the target_length adjustment and before reset_peak_memory_stats, after apply_train_fraction; single no_grad train[0] forward via the legacy-ported calibration_forward; remove_hooks in both branches, source position before the DNATrainer ctor"
    requirement: PIPE-01
    verification:
      - kind: unit
        ref: "tests/test_run_finetune_contracts.py#test_calibration_hooks_removed_before_trainer_construction, test_calibration_slot_between_encode_and_memory_reset"
        status: pass
      - kind: other
        ref: "uv run --group dev python pipeline/run_finetune.py --help -> usage printed, exit 0 (module-level health with the sibling import)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Post-success flops_report.json write (D-02/D-05): single write inside the local_rank == 0 block, source order final_metrics < flops_report < trainer_state marker (WR-13/T-07-07), hardware section with gpu_device verbatim / train_time from train_runtime / max_mem_gb from the peak-memory counter"
    requirement: PIPE-01
    verification:
      - kind: unit
        ref: "tests/test_run_finetune_contracts.py#test_final_metrics_then_flops_report_then_resume_marker, test_flops_report_write_rank_guarded"
        status: pass
    human_judgment: false
  - id: D3
    description: "Contract non-disturbance: run_record.json surfaces and the final_metrics.json payload keys gain nothing from FLOPs work (D-02); exec-extract spans :276-517 byte-stable; every pre-existing contract test passes unmodified"
    requirement: PIPE-01
    verification:
      - kind: other
        ref: "git diff 5d559f4..44de6e3: hunks only at the import block and :1536+ (success block); zero metrics.update payload-key changes; test-file diff is one pure-addition hunk"
        status: pass
      - kind: other
        ref: "make test-fast -> 549 passed, 1 deselected (zero regressions); make lint + make typecheck exit 0"
        status: pass
    human_judgment: false

# Metrics
duration: 8 min
completed: 2026-10-11
status: complete
plan_head_before: 5d559f41b8568f9f0037fce63b8fd4caac30d201
plan_head_after: 44de6e3  # last production commit; the docs close-out commit follows this SUMMARY
---

# Phase 7 Plan 04: run_finetune FLOPs Integration (Calibration Slot + Post-Success Write) Summary

**PIPE-01's integration half: every run_finetune execution now calibrates FLOPs pre-training via an unconditional FlopsCounter slot (hooks dead before the DNATrainer exists) and writes a schema-versioned flops_report.json with the D-05 hardware section between final_metrics and the resume marker — locked by 4 new source-contract tests, 549-test fast lane green, zero existing-test churn**

## Performance

- **Duration:** 8 min (2026-10-11T07:19:58Z → 07:28:12Z)
- **Tasks:** 2/2
- **Files:** 2 modified (pipeline/run_finetune.py, tests/test_run_finetune_contracts.py)
- **Commits:** 2 production (measured `git rev-list --count 5d559f4..HEAD` at SUMMARY time; the docs close-out follows)

## Accomplishments

- **The calibration slot is live** (run_finetune.py :1434-1478, inside the
  dataset loop): `count_split_tokens` over the (fraction-scaled) train split →
  unconditional `FlopsCounter(model, include_norm=True, include_act=True,
  include_embed=True)` (D-01: no flag exists — contract-tested) → the legacy
  train[0] no_grad forward chain via `calibration_forward` (evo2-backbone /
  bf16-autocast / plain branches, single attention_mask retry,
  print-and-continue on double failure — Pitfall 8: nothing more) →
  `remove_hooks()` in BOTH the populated and empty-train branches, always
  before `trainer = DNATrainer(`. `flops_counter` / `current_tokens` /
  `total_tokens` stay alive as loop-locals for the post-success write.
- **The post-success write is live** (:1536-1598, inside the rank-0 block):
  `flops_counter.save_to_json(num_tokens=current_tokens,
  all_tokens=total_tokens, filepath=os.path.join(outdir,
  "flops_report.json"), hardware=build_hardware_section(gpu_device,
  train_time, max_mem_gb))` — a single write, so a failed cell emits no report
  (research Open Q4 disposition). Hardware: `train_time =
  metrics.get("train_runtime")` (None-tolerant, A1); `max_mem_gb` from the
  peak-memory counter under the NPU_AVAILABLE/cuda guards at write time —
  before `trainer.evaluate()`, scoping it to the training peak; `gpu_device`
  verbatim from `torch.cuda.get_device_name()`, no enum normalization
  (5090D/4090D pass through; None on NPU/CPU).
- **WR-13 extended to three artifacts**: the success-block comment now names
  the chain final_metrics FIRST → flops_report SECOND → marker LAST, and the
  ordering is contract-tested (T-07-07 closed: a kill can never leave a
  permanently-done cell missing its FLOPs report).
- **Four new source-contract tests** in the file's read-text-and-assert-order
  idiom: hook-removal-before-trainer, slot position between
  encode/target_length-adjust and memory reset (+ the no-flops-flag always-on
  pin), final→flops→marker ordering (+ hardware wiring + comment naming), and
  rank-guard block membership. All 64 contracts tests green; the full fast
  lane 549 passed / 1 deselected; `make lint` and `make typecheck` exit 0.

## Task Commits

Each task was committed atomically:

1. **Task 1: Always-on calibration slot before the trainer (D-01)** —
   `ef35071` (feat)
2. **Task 2: Post-success flops_report write with hardware section,
   WR-13-ordered** — `44de6e3` (feat)
3. **Plan metadata close-out** — this SUMMARY + STATE/ROADMAP/REQUIREMENTS

## Files Created/Modified

- `pipeline/run_finetune.py` — module-top sibling import from flops_counter;
  the calibration slot between the target_length adjustment and
  reset_peak_memory_stats; the rank-0 flops_report write between
  final_metrics and the marker copy; WR-13 comment naming the third artifact
- `tests/test_run_finetune_contracts.py` — 4 new tests under a
  "FLOPs enablement (PIPE-01 integration, 07-04)" section banner

## Decisions Made

- `build_hardware_section` joined the import in Task 2's commit (ruff F401
  would fail Task 1's atomic lint gate with an unused import) — end state
  exactly per plan, only the commit boundary moved.
- `max_mem_gb` is read at write time inside the success block, which precedes
  `trainer.evaluate()` — the captured peak therefore covers training only
  (the later print-only `max_mem` at :1648+ still runs after evaluate and is
  untouched; the two values can legitimately differ by evaluate's
  allocation).
- Rank-guard membership is proven by indentation depth + a
  `statement_index`-anchored `trainer.evaluate()` upper bound, because plain
  `src.find("trainer.evaluate()")` matched the new block's own comment text.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Task-1 commit would fail the lint gate on an unused import**
- **Found during:** Task 1 (verification)
- **Issue:** the plan's Task-1 action imports `build_hardware_section` at
  module top, but its only use is Task 2's write — ruff F401 fails
  `make lint` on the Task-1 atomic commit.
- **Fix:** Task 1 imports only what it uses (`FlopsCounter,
  calibration_forward, count_split_tokens`); Task 2's commit expands the
  import to include `build_hardware_section` alongside its use.
- **Files modified:** pipeline/run_finetune.py
- **Verification:** `make lint` exit 0 at both commits; final import block
  matches the plan's end state.
- **Committed in:** `ef35071` / `44de6e3`

**2. [Rule 1 - Bug] Rank-guard test matched comment text instead of the call**
- **Found during:** Task 2 (first test run — 1 failed)
- **Issue:** `src.find("trainer.evaluate()")` matched the phrase inside the
  new flops-write block's own comments (which precede the write), inverting
  the ordering assertion.
- **Fix:** the bound now uses the file's established `statement_index`
  helper (line-anchored), which exists precisely so commented-out or
  string-embedded copies never satisfy a contract.
- **Files modified:** tests/test_run_finetune_contracts.py
- **Verification:** 64/64 green.
- **Committed in:** `44de6e3`

---

**Total deviations:** 2 auto-fixed (1 Rule-3 blocking, 1 Rule-1 bug)
**Impact on plan:** Both are commit-boundary/test-authoring hygiene; the
implemented end state matches the plan exactly. No scope creep.

## Prohibition Verification (flagged items)

- **Calibration forward does not widen beyond the legacy pattern** — the slot
  region (:1434-1478) contains no `.eval()`, no dtype moves, no `.to()`
  beyond what `calibration_forward` (07-01's verbatim port) performs, no
  weight init, no extra retry layers; verified by grep over the slot region
  plus the pre-existing
  `test_calibration_forward_attention_mask_retry` in tests/test_flops_counter.py.
- **flops_report never written after the marker copy** —
  `test_final_metrics_then_flops_report_then_resume_marker` asserts
  final_metrics < flops_report < marker in source order.
- **run_record.json / final_metrics.json payload untouched (D-02)** — the
  plan-range diff shows zero `metrics.update` key changes and no
  `_new_record`-equivalent edits; `test_trainable_params_persisted_into_final_metrics_for_every_mode`
  and the run_sweep contract tests pass unmodified (fast lane 549 green).

## Flagged Assumption Carried Forward (research A5)

The flops write is `local_rank == 0`-guarded like the final_metrics write
(legacy wrote unguarded — single-GPU in practice); no multi-rank verification
is possible this phase. Worst case under torchrun without the guard would be
duplicate identical writes; with it, non-zero ranks simply skip. Flagged for
phase verification review; the guard is contract-tested.

## Issues Encountered

None beyond the deviations above. GPU emission proof (report lands, hooks
hit, magnitude sane per D-23) is plan 07-06's smoke — explicitly out of
scope here because run_finetune is GPU-lane only.

## Authentication Gates

None — no external services.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- 07-05 (legacy deletion + parity re-pins): run_finetune now carries the
  live FLOPs chain; the 5 LEGACY_PIPELINE parity sites in this test file
  re-pin as literals when dnallmmark_pipeline.py is deleted.
- 07-06 (GB10 smoke): the recommended cell (plant-dnabert-6mer ×
  iDNA_ABF_datasets__5mC, base name, 1 epoch) now produces
  flops_report.json with schema_version 1, uncovered_layers, and the
  hardware section; D-23 magnitude anchor applies.
- Phase 11 monitor / Phase 8 tui: read the reports through
  pipeline/artifact_loader.py (07-01).

---
*Phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re*
*Completed: 2026-10-11*

## Self-Check: PASSED

- All key files exist on disk (2 modified + this SUMMARY)
- Both production commits are ancestors of HEAD (`ef35071`, `44de6e3`);
  measured `git rev-list --count` from the plan ledger base 5d559f4 = 2
  production commits (+1 docs close-out immediately following, = the
  frontmatter's 3)
- Plan-level verification re-run green: contracts 64/64,
  `run_finetune.py --help` exit 0, `make lint` exit 0, `make typecheck`
  exit 0, full fast lane 549 passed / 1 deselected (zero regressions)
