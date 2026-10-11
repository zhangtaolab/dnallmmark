---
phase: 03-dev-reconciliation-revision-blockers
plan: "04"
subsystem: pipeline
tags: [seed-isolation, G1, D-07, D-11, D-08, REV-02, sweep-runner, dry-run, fake-executor, tdd, ruff]

requires:
  - phase: 03-dev-reconciliation-revision-blockers
    provides: "03-02 unified 62/50 JSON registries (D-10 single source) + read-site flip + REFUSED guard + test harness; 03-03 [gpu] group + ty toolchain (make typecheck)"
provides:
  - Seed-isolated output layout {root}/{model}/{task}/seed_{seed}/ with a per-seed trainer_state.json resume marker (G1 dead — resume never skips a different seed)
  - Leak-free config: per-model base-config reload (D-11 — head_config cannot cross models) + per-dataset grad_accum reset to the per-model YAML default (D-07)
  - pipeline/run_sweep.py (model x task x seed matrix driver: registry-derived enumeration, --dry-run, injectable executor, run_record/sweep_manifest/sweep_failures writers)
  - run_finetune.py ruff-clean under full strictness (16 findings resolved; 3 justified per-line noqa at the designed blind-except isolation sites) + widened make lint gate
affects: [Phase 4 (REV-03 exporter consumes run_record.json's suite-native metric keys verbatim), Phase 5 (E2' three-seed re-run drives the sweep; typecheck+lint gates widened), E2E gate when runs resume]

actuals:
  tokens: 20535   # 82141 diff chars / 4 over plan_head_before..HEAD (estimate was 30000)
  tasks: 3
  commits: 5      # measured: git rev-list --count d48eaba..HEAD
plan_head_before: d48eaba526e0809d21ff9ca2faf2425fec03f137
plan_head_after: 1d14a0726bf3e91e2afe92d141e1b25d8aca0ea7

tech-stack:
  added: []       # stdlib-only runner; no new dependencies
  patterns:
    - "Injectable-executor seam for GPU-adjacent drivers: real mode proven CPU-side via a fake executor; --dry-run is the only sanctioned execution (D-05)"
    - "Source-contract tests with regex word-boundary anchors (a naive substring find matched the snapshot inside default_grad_accum — (?<![\\w]) anchors the adjustment read)"
    - "Lint-clean broad-failure capture: (subprocess.SubprocessError, OSError) at the executor seam instead of a blind except — D-08's noqa prohibition holds with zero suppression"

key-files:
  created:
    - pipeline/run_sweep.py
    - tests/test_sweep.py
  modified:
    - pipeline/run_finetune.py           # seed_{seed}/ outdir (G1) + in-loop base reload (D-11) + grad_accum reset (D-07) + 16 ruff fixes (D-08)
    - tests/test_run_finetune_contracts.py # +3 source-contract tests (5 total)
    - tests/conftest.py                  # sys.path contract += pipeline/ (run_sweep import root)
    - pyproject.toml                     # [tool.ty.environment] extra-paths += pipeline
    - Makefile                           # lint scope widened to the explicit Phase-3 file list + decision comment

key-decisions:
  - "run_sweep failure capture is (subprocess.SubprocessError, OSError), not except Exception: D-08 forbids noqa outside run_finetune.py's three sanctioned sites and the widened lint scope must exit clean, so the failure boundary is the launch seam's real failure modes (CalledProcessError from check=True, spawn OSErrors); driver/executor bugs abort the sweep loudly instead of being recorded across thousands of cells — probed empirically that ruff BLE001 fires even on underscore-named exception bindings"
  - "F401 torch_npu fixed via importlib.import_module (NOT import removal): the bare import's registration side effect is what makes torch.npu exist on Ascend hardware; importlib keeps the side effect while eliminating the unused name"
  - "SIM115 fixed by wrapping the model-loop body in a with-open block (354 lines re-indented mechanically, 2 redundant explicit closes dropped): break/continue semantics preserved because the with encloses the dataset loop — the file stays open across a model's datasets exactly as before"
  - "Harness wiring (conftest sys.path + ty extra-paths += pipeline/) landed with the RED commit: without it the tests fail at collection (invalid RED) and ty cannot resolve the run_sweep import — the same contract conftest already establishes for script/ and baseline/"
  - "vram_probe records null per seed (null-when-unknown): run_finetune.py prints VRAM numbers without persisting them, so the runner documents WHERE they will land rather than inventing data (REV-02 semantics)"

patterns-established:
  - "Two-sided layout contract via fake executors: the fake writes final_metrics.json to the layout it expects, run_matrix reads from ITS computed cell dir — disagreement fails the test, pinning {root}/{model}/{task}/seed_{seed}/ on both sides of the seam"
  - "Deterministic manifests + runtime observations kept separate: sweep_manifest.json holds only matrix + statuses (byte-identical across runs); timestamps/git_commit live in run_record.json only"

requirements-completed: [REV-02]

coverage:
  - id: D1
    description: "Task 1: seed-isolated outdir segment seed_{seed}/ with the resume check seed-scoped (G1), per-model base-config reload inside the model loop before the custom-head override (D-11, exactly-once load, pre-loop gone), default_grad_accum snapshot + per-dataset reset before the adjustment read (D-07) — all pinned by source-contract tests"
    requirement: REV-02
    verification:
      - kind: unit
        ref: "pytest tests/test_run_finetune_contracts.py -q -> 5 passed (>= 4 gate: guard + purity + 3 new contracts)"
        status: pass
      - kind: other
        ref: "grep -c 'seed_{seed}' pipeline/run_finetune.py -> 1; python -m py_compile -> COMPILES"
        status: pass
      - kind: unit
        ref: "make test -> 171 passed + 5 xfailed + node lane 2 pass at Task-1 commit time (178 after Task 2)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Task 2 (TDD RED->GREEN): pipeline/run_sweep.py — registry-derived sorted enumeration (models_info keys x truthy-Train datasets), --dry-run writing ONLY the planned manifest, byte-deterministic serialization, run_record with verbatim suite-native metrics + vram_probe nulls, seed-scoped skip-on-resume, failures manifest, argv-list subprocess with cwd pinned to pipeline/ (never shell)"
    requirement: REV-02
    verification:
      - kind: unit
        ref: "tests/test_sweep.py -> 7 passed covering every behavior bullet (RED first: 7/7 failed at the target API, NotImplementedError, zero collection errors)"
        status: pass
      - kind: other
        ref: "dry-run CLI smoke over the real registries (plant-dnamamba-6mer x GUE__emp_H3 x seeds 42,43): manifest created, grep -c seed_4 -> 2, tmp root cleaned up"
        status: pass
      - kind: unit
        ref: "make test -> 178 passed + 5 xfailed + node lane 2 pass; make typecheck -> All checks passed!"
        status: pass
    human_judgment: false
  - id: D3
    description: "Task 3: D-08 — all 16 fresh-enumerated ruff findings in run_finetune.py resolved (13 genuine fixes + 3 justified per-line noqa at the BLE001 isolation sites preserving break/continue), zero config-level suppression, make lint widened to tests/ + script/make_dev_splits.py + pipeline/run_finetune.py + pipeline/run_sweep.py with the Phase 3 scope-decision comment"
    requirement: REV-02
    verification:
      - kind: other
        ref: "ruff check tests/ script/make_dev_splits.py pipeline/run_finetune.py pipeline/run_sweep.py -> All checks passed (rc=0)"
        status: pass
      - kind: other
        ref: "make lint -> rc=0; grep -c 'tool.ruff' pyproject.toml -> 0; grep -c noqa pipeline/run_finetune.py -> 3 (break x1, continue x2 control flow verified intact)"
        status: pass
      - kind: other
        ref: "make typecheck -> All checks passed! (zero diagnostics after line-moving fixes)"
        status: pass
      - kind: unit
        ref: "pytest tests/test_run_finetune_contracts.py tests/test_sweep.py -q -> 12 passed; make test -> 178 passed + 5 xfailed + node lane 2"
        status: pass
    human_judgment: false

duration: 16 min
completed: 2026-10-10
status: complete
---

# Phase 03 Plan 04: Seed-Isolated Sweep Runner + D-07/D-11 Config Leaks + D-08 Ruff Remediation Summary

**G1 seed-scoped resume, both cross-iteration config leaks (grad_accum per dataset, head_config per model), and the 16-finding ruff debt fixed in run_finetune.py; the model x task x seed sweep runner landed with dry-run + fake-executor proof and a widened lint gate — the E2' code prerequisites are in place with zero model runs (D-05/D-06 held)**

## Performance

- **Duration:** 16 min (execution; excludes planning)
- **Started:** 2026-10-09T17:12:32Z
- **Completed:** 2026-10-10 (UTC boundary crossed during execution)
- **Tasks:** 3/3 (Task 2 TDD: RED → GREEN)
- **Commits:** 5 (measured `git rev-list --count d48eaba..HEAD`)
- **Files:** 7 (2 created, 5 modified)

## Accomplishments

- **Task 1 — G1 + D-11 + D-07 (`75a6d10`).** The outdir construction gained `seed_{seed}/` so the untouched `trainer_state.json` existence check became seed-scoped (seed 43 runs after seed 42's marker exists in a sibling dir). The pre-loop `configs = load_config("./finetune_config.yaml")` was relocated to the top of the model loop body (unconditional, after the target_model filter), so the evo2_1b_base/megaDNA_updated with_head override — which REPLACES configs and never restores it — now applies on a fresh base and no head_config residue can reach the next model. `default_grad_accum` is snapshotted right after the per-model reload and restored at the top of each dataset iteration before the adjustment block reads `gradient_accumulation_steps`. Three new source-contract tests pin the behavior (5 total in the file, all green; guard + purity tests untouched).
- **Task 2 — sweep runner, TDD (`fa0f4ba` RED → `34b9805` GREEN).** RED: 7 contract tests + a NotImplementedError skeleton landed with the harness wiring (conftest sys.path + ty extra-paths += pipeline/) — 7/7 failed at the target API with zero collection errors. GREEN: `pipeline/run_sweep.py` — `enumerate_matrix` (sorted cells from the unified JSON registries: models_info.json keys x truthy-Train datasets_info.json entries, honoring comma filters), `run_matrix` with an injectable executor (seed-scoped skip on existing trainer_state.json, verbatim final_metrics.json keys into run_record.metrics, vram_probe null-when-unknown, failure capture at the (SubprocessError, OSError) seam → status failed + sweep_failures.json), `launch_subprocess` (argv LIST with --target_model/--target_dataset/--seed/--output_dir as separate elements, cwd pinned to pipeline/, check=True, never shell), `--dry-run` (writes ONLY sweep_manifest.json with planned cells — no subprocess, no cell dirs), sorted iteration + sort_keys serialization → byte-identical manifests. Module docstring documents the cwd contract, run_record schema, vram_probe null semantics, and the dataset double-nesting E2E note (documented, NOT executed, D-05). Dry-run CLI smoke passed over the real 62/50 registries.
- **Task 3 — D-08 (`1d14a07`, + lint-hygiene `7a91a6b`).** Fresh census at exactly 16 (Task 1/2 edits introduced none). 13 genuine fixes: import sort x2, `from torch import nn`, torch_npu via `importlib.import_module` (side-effect-preserving), `datetime.now().astimezone()` (tz-aware, same format), SIM102 collapses x2 (target_model filter, max_token_len clamp), SIM115 via a with-open context manager wrapping the model-loop body (354 lines re-indented, 2 redundant closes dropped, break/continue semantics preserved), str env-var defaults x2 (`"1"`/`"0"`), `max(all_steps)`, f-prefix drops x2. The 3 BLE001 sites keep blind excepts with per-line noqa + justification comments naming the isolation intent (model-load break / encode continue / train continue). `make lint` widened to tests/ + make_dev_splits.py + run_finetune.py + run_sweep.py with the Phase 3 scope-decision comment. Verified: ruff rc=0 over the widened scope, `make lint` green, 0 `[tool.ruff]` sections, exactly 3 noqa, `make typecheck` zero diagnostics, 12 contract/sweep tests green after the line moves, `make test` 178 + 5 xfailed + node 2.

## Task Commits

1. **Task 1:** G1 + D-11 + D-07 + 3 contract tests — `75a6d10` (feat)
2. **Task 2 (RED):** sweep contract tests + skeleton + harness wiring — `fa0f4ba` (test)
3. **Task 2 (GREEN):** run_sweep.py implementation to green — `34b9805` (feat)
4. **Lint hygiene:** import-order fix in contracts test (Task 1 self-finding) — `7a91a6b` (style)
5. **Task 3:** D-08 ruff remediation + widened make lint — `1d14a07` (fix)

**Plan metadata:** this SUMMARY + STATE/ROADMAP/REQUIREMENTS commit (see below).

## Files Created/Modified

- `pipeline/run_sweep.py` — NEW: matrix driver (enumerate_matrix / build_argv / launch_subprocess / run_matrix / main; CLI --models --tasks --seeds --output-root --registry-dir --dry-run)
- `tests/test_sweep.py` — NEW: 7 behavior tests (registry derivation, dry-run-only-manifest, byte determinism, verbatim metrics, failed+failures manifest, seed-scoped skip, argv/cwd contract)
- `pipeline/run_finetune.py` — seed_{seed}/ outdir, in-loop base reload, grad_accum snapshot/reset, 13 ruff fixes + 3 justified noqa, error_log context manager
- `tests/test_run_finetune_contracts.py` — 3 new source-contract tests (seed layout, per-model reload, grad_accum reset) + docstring
- `tests/conftest.py` — pipeline/ on sys.path (run_sweep import root)
- `pyproject.toml` — [tool.ty.environment] extra-paths += "pipeline"
- `Makefile` — lint scope widened + Phase 3 decision comment + header doc

## Decisions Made

Recorded in frontmatter `key-decisions` (failure-boundary tuple, torch_npu importlib, SIM115 wrap semantics, harness wiring placement, vram_probe nulls).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Harness wiring beyond the task file lists**
- **Found during:** Task 2 RED authoring
- **Issue:** `tests/test_sweep.py` imports `run_sweep`, but neither conftest's sys.path contract nor ty's extra-paths included `pipeline/` — tests would fail at collection (invalid RED) and `make typecheck` would flag the unresolved import once Task 3 widened nothing (typecheck already covers tests/).
- **Fix:** `tests/conftest.py` gained the `pipeline/` sys.path line (mirroring the existing script/ + baseline/ lines); `pyproject.toml` `[tool.ty.environment] extra-paths` gained `"pipeline"` (mirroring the same contract for ty). Both landed in the RED commit.
- **Files modified:** tests/conftest.py, pyproject.toml
- **Verification:** RED collected 7 tests (no collection errors); `make typecheck` All checks passed
- **Committed in:** fa0f4ba

**2. [Rule 3 - Design-forced] run_sweep failure capture is a specific-exception tuple, not `except Exception`**
- **Found during:** Task 2 design (pre-implementation)
- **Issue:** The plan's action text says "on exception record status failed" — but a blind `except Exception` in run_sweep.py is a BLE001 finding under the same ruff ruleset Task 3 widens the lint gate to, and the plan prohibits any noqa line outside run_finetune.py's three sanctioned sites. Probed empirically: ruff BLE001 fires even on underscore-named exception bindings, so there is no annotation-free escape.
- **Fix:** The failure boundary is `except (subprocess.SubprocessError, OSError)` — the launch seam's real failure modes (CalledProcessError from check=True; spawn OSErrors). Driver/executor bugs abort the sweep loudly instead of being recorded across thousands of cells. The failed-cell test fake raises `subprocess.CalledProcessError`, exactly what the default executor raises. Documented in the module docstring's "Failure boundary" section.
- **Files modified:** pipeline/run_sweep.py, tests/test_sweep.py
- **Verification:** ruff clean over the widened scope incl. run_sweep.py; 7/7 tests green
- **Committed in:** 34b9805

**3. [Rule 1 - Test bug] Disk-round-trip key-order assertion over-reached**
- **Found during:** Task 2 GREEN run
- **Issue:** The verbatim-metrics test asserted `list(disk["metrics"]) == list(SUITE_NATIVE_METRICS)` — but run_record.json is intentionally written with `sort_keys=True` (the plan's own determinism discipline), so the disk round-trip returns sorted keys while the in-memory record preserves source order.
- **Fix:** Asserts key-set identity (`sorted(...) == sorted(...)`) with a comment distinguishing the sorted serialized form from the no-renaming contract; dict-value equality assertions unchanged.
- **Files modified:** tests/test_sweep.py
- **Committed in:** 34b9805

**4. [Rule 1 - Lint] Task 1's import placement broke the existing make-lint scope**
- **Found during:** Task 2 lint preview
- **Issue:** Task 1 added `import re` below `from pathlib import Path` in tests/test_run_finetune_contracts.py — an I001 finding inside the already-linted tests/ scope (make lint was failing between commits).
- **Fix:** ruff --fix restored isort order; committed as its own style commit.
- **Files modified:** tests/test_run_finetune_contracts.py
- **Verification:** ruff check tests/ clean
- **Committed in:** 7a91a6b

**5. [TDD mechanics] RED commit carries harness wiring + skeleton**
- **Found during:** Task 2 RED authoring
- **Issue:** Same class as 03-02 deviation #8: a test-only commit fails at collection without the importable target.
- **Fix:** RED commit = tests + NotImplementedError skeleton + the wiring from deviation 1; all 7 tests collect and fail at the target API.

---

**Total deviations:** 5 auto-fixed (2 blocking harness/design-forced, 1 test bug, 1 lint self-finding, 1 TDD mechanics note)
**Impact on plan:** No review surface widened beyond the plan's named files plus the two one-line harness wirings the plan's own import contract requires. No behavior beyond the plan's sanctioned edits: run_finetune.py's control flow is byte-equivalent modulo the sanctioned fixes (verified by py_compile + 5 contract tests + control-flow grep of the 3 isolation sites), and the sweep runner was never launched in real mode.

## Issues Encountered

None beyond the deviations above (all resolved in-flight).

## Authentication Gates

None — fully offline work. No model runs, no GPU work, no installs (all commands ran from the existing uv.lock-pinned groups), no writes under /home/forrest/Github/DNALLM (read-only suite constraint honored; the suite was not even read this plan). run_sweep.py real mode never launched: only --dry-run (CLI smoke) and the injectable fake executor (unit tests) executed.

## User Setup Required

None.

## Known Stubs

None in the UI/data-path sense. Two deliberate, documented null/deferral contracts (not defects): `vram_probe` fields are null-when-unknown per seed (run_finetune.py prints VRAM without persisting it — documented in run_sweep.py's docstring per REV-02, keys reserve where the numbers land); run_sweep.py deliberately implements no statistics aggregation (suite `dnallm.finetune.sweep.run_seeds` adoption is the flagged REV-03/E2' planning decision — only the layout/record contract is guaranteed this phase).

## Next Phase Readiness

- Phase 4 (REV-03) consumes `run_record.json` as exporter input: metrics carry suite-native keys VERBATIM (e.g. `eval_AUROC`) — the suite-registry → export-key mapping layer with key-parity tests is REV-03's explicit deliverable; nothing here pre-maps it.
- E2' (Phase 5) drives the sweep for real: `uv sync --group gpu` + dnallm from the local clone, then run_sweep.py real mode (subprocess cwd pinned to pipeline/; layout contract matches the suite's `{out_root}/{model}/{task}/seed_{s}/` aggregator protocol at revision 483a35c).
- The flagged edge semantics (two concurrent sweeps over one root, a killed subprocess leaving a partial seed dir without trainer_state.json — accepted default: re-run; empty filter lists) are unclassified by design and flagged for the Phase 5 E2E gate review before the three-seed re-run.
- Dataset double-nesting flattening remains deferred to the E2E gate (documented in run_sweep.py's docstring, not executed — D-05).
- `make lint` now gates the four Phase-3 file paths; the ~21 pre-existing findings in the remaining script/, scripts/, baseline/ files stay deferred to Phase 4/5 routing (Makefile comment records the decision).

## Self-Check: PASSED

Both created files exist on disk (pipeline/run_sweep.py, tests/test_sweep.py); all 5 task commits (75a6d10, fa0f4ba, 34b9805, 7a91a6b, 1d14a07) verified as ancestors of HEAD; TDD gate pattern present (test(03-04) RED fa0f4ba precedes feat(03-04) GREEN 34b9805); final battery re-verified at plan_head_after: ruff widened-scope clean, make lint green, make typecheck zero diagnostics, make test 178 passed + 5 xfailed + node lane 2.

---
*Phase: 03-dev-reconciliation-revision-blockers*
*Completed: 2026-10-10*
