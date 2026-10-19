---
phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
plan: 03
subsystem: pipeline
tags: [cli, argv, sweep, subprocess, manifest, pass-through, tdd]

# Dependency graph
requires:
  - phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
    provides: the registry overlay seam (registry_loader) — the D-14 subset pre-validation joins against the same overlay-merged datasets registry view the matrix enumeration uses
provides:
  - run_sweep CLI flags --subset_file / --effective_batch_size (bare=16) / --num_train_epochs / --cache_dir — PIPE-02, the exact surface the Phase 11 TUI run-config screen drives
  - Sweep-owned collect-all --subset_file pre-validation (_validate_subset_file, D-14) — a bad map aborts at startup with every problem listed, never after model loads burn
  - Manifest only-when-present flag recording (D-13) with byte determinism locked; run_record.json contract untouched
affects: [07-06 GB10 smoke (dry-run with flags), phase-11 TUI run-config screen, phase-08 tui services]

# Actuals (#2632) — same estimateTokens scale as the plan's estimate
# (chars/4 over the realized diff base..HEAD, planning artifacts included).
actuals:
  tokens: 12707
  tasks: 3
  commits: 7

tech-stack:
  added: []  # zero external packages (T-07-SC; stdlib argparse/json/pathlib only)
  patterns:
    - "Pass-through flag threading: parse -> collect-all sanity + abs-path resolution in main() -> sweep_flags dict of ONLY present flags -> partial-bound default executor -> two-element LIST argv appends; absent flag = zero argv elements and zero manifest keys"
    - "Sweep-owned shallow validation as defense-in-depth: the child's validator stays authoritative; the sweep mirrors only the checks whose failure would burn a model load (structure, registry membership, int-list) — never a shared import (stdlib-only headless import discipline)"

key-files:
  created: []
  modified:
    - pipeline/run_sweep.py
    - tests/test_sweep.py

key-decisions:
  - "Bool exclusion in the sweep's int-list check mirrors the child validator: a JSON true is an int subclass in Python but not a row ID, and without the exclusion it would pass sweep validation and surface only child-side after a model load burns — the exact burn D-14 exists to prevent"
  - "Dry-run manifest path now routes through _manifest_payload (was an inline dict write): both paths project identically so present flags record the same way planned and executed; the no-flag payload is byte-identical to the old inline form"
  - "Unreadable/not-JSON subset files are COLLECTED (not immediate exits) in _validate_subset_file: one problems list, one non-zero exit naming everything — the parse_curve_fractions discipline applied uniformly"

patterns-established:
  - "Only-when-present recording: a present-flag dict merged with ** into each manifest cell; absent = no keys = byte-identical artifacts (D-13); run records never gain configuration fields (D-02 spirit)"
  - "D-15 abs-path resolution at the sweep layer BEFORE threading, because the child cwd is pinned to pipeline/ — every new path-bearing sweep flag must resolve in main(), not in the child"

requirements-completed: [PIPE-02]

coverage:
  - id: D1
    description: "Four flags threaded CLI -> child argv with parity: parse_args registration (underscore names only, D-11), bare --effective_batch_size=16 / valued=int / absent=None (D-12), two-element LIST appends in build_argv/launch_subprocess, collect-all startup sanity (>=1 batch/epochs, non-empty subset path), D-15 absolute-path resolution, run_matrix partial binding; zero GA arithmetic in the sweep"
    requirement: PIPE-02
    verification:
      - kind: unit
        ref: "tests/test_sweep.py#test_sweep_flags_default_to_none_in_parse_args, test_effective_batch_size_bare_valued_absent_parse, test_build_argv_threads_four_flags_as_list_elements, test_build_argv_absent_flags_add_zero_elements, test_cli_bare_effective_batch_size_threads_16_into_child_argv, test_cli_resolves_subset_and_cache_dir_to_absolute_paths, test_cli_zero_flag_values_abort_naming_flag_and_value, test_cli_flag_sanity_is_collect_all, test_cli_empty_subset_file_value_aborts"
        status: pass
      - kind: other
        ref: "uv run --group dev python -c build_argv parity check -> argv-parity-ok (present threads '16', absent adds none of the four flags)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Sweep-owned collect-all --subset_file pre-validation (D-14): unknown registry keys, unreadable paths, non-object top level, and non-int-list values each abort non-zero naming the offender; multiple problems list TOGETHER in one exit; validation runs before any cell enumerates (fake executor never invoked); child validate_subset_file stays authoritative, never imported"
    requirement: PIPE-02
    verification:
      - kind: unit
        ref: "tests/test_sweep.py#test_subset_file_unknown_dataset_key_aborts_naming_key, test_subset_file_unreadable_path_aborts_naming_path, test_subset_file_non_object_top_level_aborts, test_subset_file_collects_all_value_problems_together, test_valid_subset_file_passes_validation_and_threads_to_child_argv, test_subset_validation_runs_before_any_cell_enumerates"
        status: pass
      - kind: other
        ref: "real negative e2e: uv run python pipeline/run_sweep.py --dry-run --subset_file <ghost-key file> -> '[Error] --subset_file task keys not in datasets registry: [GHOST__task]', exit 1, no output root"
        status: pass
    human_judgment: false
  - id: D3
    description: "Manifest only-when-present recording (D-13) + byte-determinism lock: present flags join every cell with the five base keys unchanged; absent flags add no keys (byte-identical, the :206 test unmodified and green); paths record as resolved absolute strings; run_record.json carries none of the four keys even when present; dry-run and real paths record identically; two same-flag dry-runs byte-identical"
    requirement: PIPE-02
    verification:
      - kind: unit
        ref: "tests/test_sweep.py#test_dry_run_manifest_records_present_flags, test_dry_run_manifest_absent_flags_add_no_keys, test_manifest_records_resolved_absolute_paths, test_run_record_untouched_by_sweep_flags, test_dry_run_with_flags_is_byte_deterministic, test_dry_run_manifest_is_byte_deterministic (pre-existing, unmodified)"
        status: pass
      - kind: other
        ref: "uv run --group dev python -c _manifest_payload field check -> manifest-fields-ok; real dry-run e2e with all four flags -> cells carry effective_batch_size 16, num_train_epochs 1, subset_file/cache_dir absolute"
        status: pass
    human_judgment: false

# Metrics
duration: 12 min
completed: 2026-10-11
status: complete
plan_head_before: a3dfd98c7885ccd5e99c2422b02d62a4e3ec7409
---

# Phase 7 Plan 03: Sweep argv Threading (PIPE-02) Summary

**Four pass-through sweep flags (--subset_file / --effective_batch_size bare=16 / --num_train_epochs / --cache_dir) threaded CLI -> child argv as two-element LIST appends with collect-all startup validation, absolute-path discipline, and only-when-present manifest recording — byte-identical argv/manifests/records when absent, 23 new tests, zero run_finetune.py changes**

## Performance

- **Duration:** 12 min (2026-10-11T07:04:52Z → 07:16:26Z)
- **Tasks:** 3/3 (each TDD RED→GREEN)
- **Files:** 2 code files modified (0 created) + 3 RED-evidence records + this SUMMARY
- **Commits:** 7 (measured `git rev-list --count a3dfd98..HEAD`)

## Accomplishments

- **All four flags thread with CLI parity (PIPE-02)**: parse_args
  registers exactly the four underscore names (D-11, zero alias
  mapping); `--effective_batch_size` uses `nargs='?' const=16`
  (D-12: bare = 16, valued = int, absent = None → zero argv elements,
  the child's YAML gradient-accumulation governs); each present flag
  appends two LIST elements in build_argv/launch_subprocess (the
  peft/train_fraction append idiom); run_matrix binds them into the
  default executor via `functools.partial(launch_subprocess, peft=...,
  **(sweep_flags or {}))`.
- **No GA arithmetic anywhere in the sweep**: `grep bs_new/
  required_grad_accum` hits only docstring/help prose documenting the
  CHILD-side `max(1, N // bs_new)` semantics (D-10/D-16 pure
  pass-through); the integer floor division lives at
  run_finetune.py:1305-1315, untouched.
- **D-15 abs-path discipline**: main() resolves `--subset_file` /
  `--cache_dir` against the sweep's CWD BEFORE threading (the
  --output-root precedent) — the child cwd is pinned to pipeline/, so
  relatives would misresolve.
- **D-14 collect-all subset pre-validation** (`_validate_subset_file`,
  ~60 lines with docstring): readable-JSON / object / registry-key /
  int-list checks against the same overlay-merged registry view the
  matrix joins on (registry_loader, post 07-02); every problem lists in
  ONE non-zero exit; runs pre-enumeration (fake executor never invoked);
  the child's `validate_subset_file` stays authoritative — defense in
  depth, deliberately NOT a shared import (sweep stays stdlib-only and
  headless-importable; torch never enters CI).
- **D-13 manifest recording**: `_manifest_payload(matrix, records,
  sweep_flags=None)` merges present flags into every cell; the dry-run
  path now routes through it too, so planned and executed cells record
  identically; `_new_record` untouched (run_record.json keeps its exact
  field set even with flags present — D-02 spirit, Open Q3).
- **Byte-identity locked**: test_sweep.py 96 passed with ZERO
  pre-existing-test modifications (`git diff` over the plan range =
  495 insertions, 0 deletions); full fast lane 545 passed /
  1 deselected; `make lint` + `make typecheck` clean; `git diff
  pipeline/run_finetune.py` empty (zero child changes — all four child
  flags already existed at :138/:167/:188/:211).
- **Real-invocation e2e (CPU)**: a `--dry-run` over the real registries
  with all four flags records `effective_batch_size: 16` (bare flag),
  `num_train_epochs: 1`, and both absolute paths in the manifest cells;
  a ghost-key subset file aborts with exit 1 and no output root.

## Task Commits

Each task was a TDD RED→GREEN pair:

1. **Task 1 RED: argv-parity tests** — `181fd28` (test; 9 fail / 1
   absent-parity pass; RED_EVIDENCE_OK)
2. **Task 1 GREEN: four flags threaded** — `49b706a` (feat)
3. **Task 2 RED: collect-all subset tests** — `5799cbe` (test;
   DID-NOT-RAISE; RED_EVIDENCE_OK)
4. **Task 2 GREEN: _validate_subset_file + main() wiring** — `040351e`
   (feat)
5. **Task 3 RED: manifest only-when-present tests** — `cccc979` (test;
   KeyError on the missing field; RED_EVIDENCE_OK)
6. **Task 3 GREEN: _manifest_payload merge + dry-run routing** —
   `fbe9062` (feat)
7. **Bool-exclusion coverage + RED evidence records** — `793c17e` (test)
8. **Plan metadata close-out** — this SUMMARY + STATE/ROADMAP/REQUIREMENTS

REFACTOR: skipped per task — no behavior-neutral cleanup existed after
any GREEN (implementations follow the existing idioms directly).

## TDD Note (all three tasks)

RED evidence persisted at `.planning/tdd-evidence/07-03-task{1,2,3}-red.json`,
each validated `gsd_run check tdd-red-evidence` → **RED_EVIDENCE_OK**
(`target_test_failed`, junit via pytest `--junitxml`):
- Task 1 target failed as `TypeError: build_argv() got an unexpected
  keyword argument 'subset_file'` — the planned API surface absent.
- Task 2 target failed as `Failed: DID NOT RAISE` — the dry-run ran to
  completion and wrote a manifest, precisely the hazard D-14 prevents.
- Task 3 target failed as `KeyError: 'effective_batch_size'` — the
  manifest cell lacked the planned field.
Each record carries a semantic assessment; every named target executed
and failed on the planned behavior, not on collection/fixture faults.

## Files Created/Modified

- `pipeline/run_sweep.py` — four parse_args flags; build_argv /
  launch_subprocess kwargs; run_matrix sweep_flags; main() sanity +
  resolution + validation zone; _validate_subset_file;
  _manifest_payload merge + dry-run routing; module-docstring section
- `tests/test_sweep.py` — 23 new tests across three suites (argv
  parity, subset pre-validation, manifest recording); zero
  pre-existing-test modifications

## Decisions Made

- **Bool exclusion in the int-list check** (mirrors the child's
  `isinstance(row_id, bool) or not isinstance(row_id, int)`): a JSON
  `true` is an int subclass but not a row ID; without the exclusion it
  would pass sweep validation and die child-side after a model load
  burns — the exact burn D-14 exists to prevent. Pinned by the
  collect-all test fixture (`[0, "x", True]`).
- **Dry-run manifest routed through `_manifest_payload`** (was an
  inline `{"matrix": ..., "cells": planned_records}` write): one
  projection path for planned and executed cells; no-flag output is
  byte-identical to the old inline form (sort_keys discipline).
- **Unreadable/not-JSON subset problems are collected, not immediate
  exits** — one problems list, one exit naming everything (the plan's
  "collected rather than immediately exiting" reading of the
  _read_operator_json precedent).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Bool IDs would pass the sweep's int-list check**
- **Found during:** Task 2 (GREEN, validator edge coverage)
- **Issue:** "values lists of ints" read naively (`isinstance(x, int)`)
  accepts JSON `true`/`false` (bool is an int subclass) — the sweep-side
  validator would pass them and the failure would surface only
  child-side after a model load burns.
- **Fix:** explicit bool exclusion, mirroring the child validator.
- **Files modified:** pipeline/run_sweep.py, tests/test_sweep.py
- **Verification:** collect-all test fixture `[0, "x", True]` asserts
  `True` is named as a non-integer ID
- **Committed in:** `040351e` (code), `793c17e` (test pin)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** One validator edge tightened to match the child's
authoritative rule and D-14's burn-prevention purpose. No scope creep —
no new behavior, surface, or dependency.

## Prohibition Verification (flagged items)

- **No hyphenated flag aliases (D-11)** — grep for
  `effective-batch|subset-file|num-train-epochs|cache-dir` in
  run_sweep.py: zero matches; parse_args registers exactly the four
  underscore names.
- **No gradient-accumulation arithmetic in the sweep (D-10/D-16)** — the
  only `bs_new`/`required_grad_accum` mentions are docstring/help PROSE
  documenting child-side semantics; no floor division or GA computation
  executes in run_sweep.py.
- **run_finetune.py unmodified** — `git diff` over the plan range shows
  zero run_finetune.py changes; all four child flags pre-existed.

## Issues Encountered

- The Task 2 RED test over-specified one error-message assertion
  (`"not-a-list" in message` asserted the fixture's string VALUE rather
  than the type descriptor the child-validator message style produces).
  Corrected in GREEN to `"value is str" in message` — the planned
  behavior (both problems named in one exit) was never in question.
- `gsd_run` is not on this executor's PATH; invoked via
  `bash ~/.claude/gsd-core/bin/gsd_run` (same as 07-02).

## Authentication Gates

None — no external services.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- 07-04 (run_finetune integration) is unblocked; this plan changed
  nothing child-side.
- 07-06 (GB10 smoke) can prove the flags end-to-end on a real
  invocation; the CPU dry-run e2e here already demonstrates manifest
  recording with all four flags.
- Phase 11's TUI run-config screen now has its complete CLI-first
  surface: seeds/PEFT/variant/curve/subset/epochs/auto-GA
  (--effective_batch_size) + cache directory, all with argv-shape
  proofs in the existing sweep test harness.

---
*Phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re*
*Completed: 2026-10-11*

## Self-Check: PASSED

- All key files exist on disk (2 modified code files + 3 RED-evidence
  records + this SUMMARY)
- All 7 commits are ancestors of HEAD (`181fd28`, `49b706a`, `5799cbe`,
  `040351e`, `cccc979`, `fbe9062`, `793c17e`); measured
  `git rev-list --count` from the plan ledger base a3dfd98 = 7, matching
  frontmatter
- `gsd_run check evaluation-scope --plan 07-03 --commits-only` resolves
  with commits on this branch
- Plan-level verification re-run green: full plan gate 96 passed
  (test_sweep.py), full fast lane 545 passed / 1 deselected,
  `make lint` exit 0, `make typecheck` exit 0; both direct python -c
  parity checks green (argv-parity-ok, manifest-fields-ok); real
  dry-run e2e (four flags present + ghost-key negative) green; zero
  pre-existing-test modifications confirmed by `git diff` over the plan
  range (495 insertions, 0 deletions)
