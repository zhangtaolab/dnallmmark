---
phase: 11-run-config-launch-gates-single-gpu-monitoring
plan: 01
subsystem: pipeline
tags: [run-sweep, config-variant, aliasing, argv-parity, peft-machinery]

requires:
  - phase: 07-03
    provides: the PIPE-02 pass-through argv-parity test idioms (flag_value, _capturing_launcher) reused here
provides:
  - run_sweep --config-variant head|probe|curve via the --peft ALIASING machinery (alias enumeration + explicit --save_model_name + --config-variant twin, driver as single naming authority)
  - HEAD_KEEP_BASE_NAMES frozen pair (evo2_1b_base, megaDNA_updated) with a read-source parity tripwire against run_finetune.py
  - variant x peft collect-all refusal at sweep start (all 3 variants x lora/ia3, driver-side front line over the child's probe x peft backstop)
  - run_record.json config_variant field (default "none") + manifest config_variant cell merge via sweep_flags when the flag is present
  - variant-aware base_model_name / --from-failures base-name join
affects: [11-02 run_config service (imports enumerate_matrix/build_argv CPU-side), 11-03+ launch/monitor plans, CFG-01 variant control]

actuals:
  tokens: 12266   # chars/4 over the realized diff (49063 chars, 2 files)
  tasks: 2
  commits: 2
plan_head_before: 9d820a8ebc9f9633700bd6f41f99a2312d504b66
plan_head_after: 52fd7a677cf41fb308fe9e01ac29cfc538cdc088

tech-stack:
  added: []   # zero new dependencies (stdlib-only module unchanged)
  patterns:
    - "peft-aliasing reuse: a second alias axis (config_variant) threaded through enumerate/base_model_name/build_argv/launch/_new_record/run_matrix/main as a pure suffix-suffix twin of the --peft machinery"
    - "read-source-never-import parity tripwire extended to a frozen NAME PAIR (regex over run_finetune.py source; torch at its module top forbids import)"

key-files:
  created: []
  modified:
    - pipeline/run_sweep.py
    - tests/test_sweep.py

key-decisions:
  - "D-18 errata implemented literally: ALIASING, never pass-through — enumerate_matrix emits {model}+{variant} cells and build_argv threads --target_model <base> + explicit --save_model_name <alias> + --config-variant <v>, so the child's explicit-save-name-wins branch (run_finetune.py:1198-1213) can never diverge from the dir cell_dir_for records (the retrain-forever trap)"
  - "run_matrix's default-executor partial binds config_variant EXPLICITLY and filters the config_variant key out of the sweep_flags splat: main() records a present variant in sweep_flags for the manifest merge (D-13), while the explicit param stays the single argv authority — no duplicate-kwarg collision"
  - "head on the frozen pair keeps the BASE save name (alias == base) while --config-variant head still threads — verbatim the child's own exemption"
  - "run_record gains config_variant unconditionally (default 'none', the peft-field precedent); the MANIFEST carries the key only when the flag is present (sweep_flags mechanism, D-13)"

patterns-established:
  - "Second alias axis on the peft machinery: alias-rule closure order peft -> probe/curve -> head(exception) -> base; suffix strips compose in base_model_name (axes disjoint by the collect-all refusal)"

requirements-completed: [CFG-01, LNC-02]

coverage:
  - id: D1
    description: "--config-variant aliasing machinery in run_sweep.py (enumeration, argv twin, records, manifest, refusal, from-failures join)"
    requirement: CFG-01
    verification:
      - kind: unit
        ref: "tests/test_sweep.py::test_enumerate_matrix_emits_alias_cells_under_config_variant (and 19 sibling tests, 20 total)"
        status: pass
  - id: D2
    description: "Frozen-pair parity tripwire: HEAD_KEEP_BASE_NAMES == the tuple extracted from run_finetune.py source text (never imported)"
    requirement: CFG-01
    verification:
      - kind: unit
        ref: "tests/test_sweep.py::test_head_keep_base_names_pinned_against_run_finetune_source"
        status: pass
  - id: D3
    description: "Variant x peft composition refused driver-side, collect-all, all 3 variants x both peft modes, both flags named"
    requirement: LNC-02
    verification:
      - kind: unit
        ref: "tests/test_sweep.py::test_cli_config_variant_refuses_peft_collect_all[probe-lora..curve-ia3] (6 parametrized cases)"
        status: pass
      - kind: other
        ref: "CLI: python pipeline/run_sweep.py --config-variant probe --peft lora ... -> exit 1, message names both flags"
        status: pass

---

# Phase 11 Plan 01: --config-variant Aliasing in run_sweep Summary

Landed the D-18 `--config-variant head|probe|curve` threading in `pipeline/run_sweep.py` by reusing the proven `--peft` aliasing machinery (NOT a pass-through), pinned by a 20-test argv-parity suite in `tests/test_sweep.py`.

## What Was Built

### Task 1 — the aliasing machinery (commit 647741c)

- `HEAD_KEEP_BASE_NAMES = ("evo2_1b_base", "megaDNA_updated")` — verbatim from run_finetune.py:1207-1209 (the child exempts the pair from the +head alias; their with-head config IS their base config).
- argparse `--config-variant` (choices head/probe/curve, default None) after the `--cache_dir` block, help mirroring the `--peft` alias documentation.
- `enumerate_matrix(..., config_variant="none")`: `cell_model` closure adds the variant rule AFTER the peft branch — probe/curve → `{model}+{variant}`, head → `{model}+head` except the frozen pair; registry iteration and `--models` join stay on BASE names; sorting after the alias mapping stays deterministic; composes with `fractions` (alias 4-tuples).
- `base_model_name(model, peft="none", config_variant="none")`: variant suffix strip after the peft strip (no-op on the frozen pair / absent suffix).
- `build_argv(..., config_variant="none")`: `elif config_variant != "none": argv += ["--save_model_name", str(model), "--config-variant", config_variant]` — and `--target_model` carries `base_model_name(model, peft, config_variant)`. The explicit save name makes the DRIVER the single naming authority over the child's identical self-aliasing branch.
- `launch_subprocess` / `_new_record` / `run_matrix` thread the param; `run_matrix`'s default-executor partial binds `config_variant` explicitly and filters it out of the `sweep_flags` splat (a present flag is recorded in sweep_flags for the manifest merge — no duplicate-kwarg collision); all three failure-appends derive `base_model` variant-aware.
- `main()`: collect-all refusal when `args.config_variant is not None and args.peft != "none"` (message names both flags, child's probe×peft refusal cited as backstop); `config_variant = args.config_variant or "none"`; threaded into the enumerate call, the from-failures filter, and the run_matrix call; `sweep_flags["config_variant"]` set only when present.
- Module docstring: the "Config variants compose STANDALONE" note replaced by the D-18 landing note; run_record schema doc gains `config_variant`.

### Task 2 — the parity suite (commit 52fd7a6)

20 tests, every assertion style copied from existing idioms (make_registry / run_cli / flag_value / _capturing_launcher / _failures_manifest / _manifest_cells / fake-executor run_matrix):

- Alias enumeration (probe/curve/head sorted tuples; base-name filter join; frozen pair keeps base; fraction composition).
- argv parity: `--save_model_name == {base}+{variant}`, `--config-variant == variant`, `--target_model == base`, LIST of str, cwd pinned; head-on-frozen-pair save name == base while the variant threads.
- Absent parity: `config_variant="none"` argv byte-identical; no manifest cell key; record field "none".
- Alias cell dirs in the dry-run manifest (`{root}/{model}+probe/{task}/seed_{seed}/`).
- Record field inside the alias dir; failure entries carry `base_model` beside the alias; default-executor argv threads the twin.
- Manifest merge (dry-run + fake-executor run) when present.
- Composition refusal: 6 parametrized cases (probe/head/curve × lora/ia3), both flags named, no output written.
- Frozen-pair read-source parity (regex over run_finetune.py text — never imported, torch at its module top).
- from-failures under variant; base_model_name unit strips.

## Verification Evidence

- `uv run --group dev --group tui pytest tests/test_sweep.py -q` → **121 passed** (101 pre-existing + 20 new).
- `uv run --group dev --group tui pytest tests/ -q -k "sweep or run_finetune_contracts"` → **186 passed**.
- `make test` → **1217 passed** (baseline 1197 + 20 new) + node:test JS lane 18/18 — green.
- `make lint` (ruff) → All checks passed.
- `make typecheck` (ty) → All checks passed.
- Import purity (D-05, live probe): `python -I` + `import run_sweep` leaves torch/dnallm/transformers ABSENT from sys.modules; full 62×50×3 enumeration still ~0.002s.
- TDD discipline: suite written first and confirmed RED (20 failures: unexpected kwarg / missing attribute / unrecognized flag), then machinery landed → GREEN.
- Manual dry-run spot evidence (`--config-variant probe --dry-run` over the make_registry fixture):
  `[Dry-run] 2 planned cell(s) over 2 model(s) x 1 task(s) x 1 seed(s); manifest: /tmp/sw-variant-spot/out/sweep_manifest.json`
  manifest `matrix.models == ['model-a+probe', 'model-b+probe']`, cells carry `config_variant: 'probe'`, outdir `.../model-a+probe/task-x/seed_42`.
- Refusal spot evidence: `--config-variant probe --peft lora` → `[Error] --config-variant probe refuses --peft lora: ...` exit 1.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Record-correctness] Reverted the premature CFG-01/LNC-02 requirement completion marks**
- **Found during:** State updates (post-summary)
- **Issue:** The `requirements mark-complete` protocol verb checked off CFG-01 and LNC-02 in REQUIREMENTS.md, but both are PHASE-level requirements shared across plans 11-01/02/05/06/07 (verified in each plan's frontmatter). Plan 1 of 7 delivered only the pipeline-side enabler (the variant control's execution path / the argv LIST discipline); the slot-4 parameter pane (CFG-01) and the launch-service kill/detach/cancel lifecycle (LNC-02) land in later plans. Leaving the marks would write a false "Complete" traceability row for UI/service work that does not exist yet.
- **Fix:** Reverted the two checkboxes and the two traceability-table rows to their prior Pending state (surgical text revert; the tool has no unmark verb). The integration plan (11-06) and final plans carry the same requirement IDs and will mark them when the full requirement text is actually satisfied.
- **Files modified:** .planning/REQUIREMENTS.md
- **Commit:** this plan's docs commit

### Implementation Notes (within the plan's own discretion)

- The default-executor partial in `run_matrix` filters the `config_variant` key out of the `sweep_flags` splat before binding the param explicitly (the plan threads the param into the partial AND records a present flag in sweep_flags; without the filter the two channels would collide as duplicate kwargs). Pinned by `test_default_executor_receives_config_variant`.
- Commit boundary: Task 1 = machinery (`pipeline/run_sweep.py`), Task 2 = suite (`tests/test_sweep.py`) — the TDD RED→GREEN cycle ran across both before either commit (the plan sanctions the ordering; each commit is independently green).

## What 11-02 Can Now Assume

`tui/services/run_config.py` may `import run_sweep` (stdlib-only, headless) and compose a variant sweep as plain flags — `--config-variant head|probe|curve` aliases enumeration, argv, records, and manifests exactly like `--peft`; preview counting via `enumerate_matrix(..., config_variant=v)` and argv display via `build_argv(..., config_variant=v)` are correct by construction, and a variant×peft composition fails fast at sweep start with both flags named (mirror it as a preview problem; the child's PROBE_INELIGIBLE refusal remains child-side, read-source only).

## Self-Check: PASSED

- pipeline/run_sweep.py — FOUND
- tests/test_sweep.py — FOUND
- 647741c ancestor of HEAD — FOUND
- 52fd7a6 ancestor of HEAD — FOUND
- Deletion check: neither commit deletes tracked files
- Untracked scan: only the pre-existing `.planning/.gsd-allow-shrink` (present at spawn; not this plan's artifact)
- Ledger: commits measured 2 (`9d820a8..52fd7a6`), no uncommitted code changes
