---
phase: 12-multi-gpu-orchestration-console-hardening
plan: "01"
subsystem: pipeline
tags: [multi-gpu, orchestration, cli, lpt, subprocess]
requires:
  - "run_sweep.py frozen argv surface (Phase 3/11)"
  - "sweep_launcher._spawn discipline (Phase 10/11)"
  - "registry_loader overlay seam (Phase 7)"
provides:
  - "pipeline/run_sweep_shard.py launch mode (MGPU-01/SC1)"
  - "worker_root()/worker_log_path() — the frozen {root}-mgpu-w{i} naming authority 12-04's --merge imports"
  - "lpt_shard() pure function (disjoint/cover/deterministic)"
  - "tests/test_sweep_shard.py tier-1 suite (22 tests)"
  - "PHASE12_MODULES Makefile lint guard (covers 12-02's script/gen_progress.py on arrival)"
affects:
  - "12-02 (gen_progress.py joins lint automatically — NO Makefile edit needed)"
  - "12-04 (--merge imports worker_root; docs/multi-gpu.md cites this CLI)"
tech-stack:
  added: []
  patterns:
    - "sweep_launcher._spawn kwargs copied VERBATIM + exactly one CUDA_VISIBLE_DEVICES env key"
    - "parse_known_args passthrough remainder forwarded verbatim per worker"
    - "collect-all fail-fast validation (the _validate_filters discipline)"
    - "injectable spawner seam (the :475 idiom) for CPU-only testing"
key-files:
  created:
    - pipeline/run_sweep_shard.py
    - tests/test_sweep_shard.py
  modified:
    - Makefile
decisions:
  - "D-07 landed as the NEW entry; run_sweep.py/run_finetune.py byte-untouched (verified: 0-line diff over the plan range)"
  - "passthrough --registry-dir is READ (not owned) for the validation join so orchestrator and workers see the same registry view"
  - "test helpers (make_registry/run_cli/flag_value) locally copied, not cross-imported — run_cli needs the spawner parameter anyway; make_registry gained size (M) values for pinned LPT expectations"
  - "frozen-root collision guard is defense-in-depth by construction (the frozen naming cannot self-collide); proven wired via a pinned colliding naming fn"
metrics:
  duration: "29m"
  completed: "2026-10-13"
estimate:
  tokens: 62000
actuals:
  tokens: 14487   # chars/4 over the realized diff (git diff 41453ce..c732fbb)
  tasks: 2
  commits: 2      # MEASURED: git rev-list --count 41453ce..HEAD
plan_head_before: 41453ceffa4548f19de8087d89b0de1be174a50c
plan_head_after: c732fbbe2cdc863658e5f4844af171e2264fa7bf
status: complete
---

# Phase 12 Plan 01: Multi-GPU Sweep Orchestrator Launch Mode Summary

One-liner: stdlib-only `pipeline/run_sweep_shard.py` — collect-all validated LPT model sharding x N ordinary `run_sweep.py` workers, each pinned to one GPU via `CUDA_VISIBLE_DEVICES` under frozen sibling roots `{root}-mgpu-w{i}` with sibling tee logs and an honest aggregated verdict; CPU-proven end-to-end by 22 tier-1 tests including a real two-worker dry-run subprocess chain.

## What Was Built

### pipeline/run_sweep_shard.py (NEW, 505 lines, stdlib-only)

- **Module docstring** (run_sweep depth): invocation + cwd contract; frozen `{root}-mgpu-w{i}` naming + `.log` siblings; the three-line disjointness proof (Pitfall 1: root-level manifests are why shared roots are FORBIDDEN); marker-skip as the only guard / disjointness as the static guarantee (D-06); the killpg recipe (`kill -TERM -$(ps -o pgid= -p <pid> | tr -d ' ')`); Ctrl-C leaves workers running by design (A4); task/seed validation surfaces inside each worker and lands in the verdict table; the E2' boundary pointer to docs/multi-gpu.md (12-04); English help throughout (D-10).
- **`worker_root(base, i)` / `worker_log_path(base, i)`** — the ONE naming authority (12-04's `--merge` imports them).
- **`lpt_shard(models, workers, sizes)`** — pure LPT: size desc (name-asc tie-break) -> least accumulated load (lowest index tie-break); `_coerce_size` sends missing/None/non-numeric `size (M)` to 0.0.
- **`parse_args` via `parse_known_args`** — five orchestrator-owned flags (`--workers/--gpus/--models/--output-root/--dry-run`); every unrecognized token is the verbatim passthrough tail (run_sweep stays the single flag owner — D-07's argv-surface-minimization answer).
- **`main(spawner=None)`** — collect-all refusal (workers<1, gpus malformed/arity, empty `--models` value, unknown names vs registry, workers>models empty-shard refusal naming both counts, frozen-root collision), then shard -> spawn all -> wait all -> verdict table -> exit 0 iff all workers 0, else `SystemExit(1)`.
- **Worker spawn** — `sweep_launcher._spawn` kwargs VERBATIM (`start_new_session=True`, `cwd=str(run_sweep.PIPELINE_DIR)`, `env={**os.environ, PYTHONUNBUFFERED: "1", ...}`, `stdout=tee`, `stderr=STDOUT`) plus exactly ONE added key `CUDA_VISIBLE_DEVICES: str(gpu_i)`; argv always a LIST (T-03-10); tee handles held for child lifetime with the SIM115 rationale inlined.

### tests/test_sweep_shard.py (NEW, 22 tests)

LPT properties (disjoint+cover, determinism, both tie-breaks pinned, 0.0-weight coercion, workers=1 and workers==len(models) degenerates); frozen naming pin; fake-spawner argv+kwargs proofs (LIST argv, shard csv per worker, frozen `--output-root`, verbatim passthrough, `--dry-run` iff requested, sessions/cwd/env incl. `--gpus "2,5"` override and duplicate-token arity-only forwarding, tee-handle stdout); all six collect-all refusals; collision refusal (pinned colliding naming fn — guard is wired and fires BEFORE spawn); aggregation honesty (all-0 -> exit 0; [1,0] -> SystemExit 1 + table; failed-cell count from fixture `sweep_failures.json`; wait-all death isolation); the in-process dry-run disjointness proof (pairwise-disjoint identities, union == unsharded matrix, `matrix.models == shard`); the live official-registry partition (2/4 workers over 62 models); and the REAL two-worker subprocess chain (real Popen, real `run_sweep.py --dry-run` children, frozen-root manifests disjoint, both tee logs non-empty, main returns 0).

### Makefile

`PHASE12_MODULES` existence-guard variable (the `PHASE7_MODULES` idiom) covering BOTH `pipeline/run_sweep_shard.py` AND `script/gen_progress.py` — 12-02's generator joins lint coverage automatically when it lands, with NO later Makefile edit. Appended to the lint recipe; header comment updated.

## Verification

- Module suites during TDD: 15 -> 22 tests green; ruff clean on both new files from the first GREEN run.
- **Full gate ONCE at plan end** (SPEED DIRECTIVE): `make test && make lint && make typecheck` -> exit 0, **1523 passed** (baseline 1501 + 22 new), lint "All checks passed!", ty "All checks passed!".
- Hard constraint verified: `git diff --stat 41453ce..HEAD -- pipeline/run_sweep.py pipeline/run_finetune.py pyproject.toml uv.lock tui/strings.py` is EMPTY — the frozen argv surface, dependency manifests, and TUI strings are byte-untouched; pipeline/ gained exactly one file.
- Verbatim verdict-table stdout (the scripted-returncode scenario, exit 1 path):

```text
[Worker 0] gpu=0 models=1 root=/tmp/tmpxivr7uoj/finetuned-mgpu-w0 log=/tmp/tmpxivr7uoj/finetuned-mgpu-w0.log
[Worker 1] gpu=1 models=1 root=/tmp/tmpxivr7uoj/finetuned-mgpu-w1 log=/tmp/tmpxivr7uoj/finetuned-mgpu-w1.log
Worker verdicts:
  worker 0: exit=1 failed=3 root=/tmp/tmpxivr7uoj/finetuned-mgpu-w0 log=/tmp/tmpxivr7uoj/finetuned-mgpu-w0.log
  worker 1: exit=0 failed=- root=/tmp/tmpxivr7uoj/finetuned-mgpu-w1 log=/tmp/tmpxivr7uoj/finetuned-mgpu-w1.log
1/2 worker(s) failed — isolation holds: a dead worker never touched its siblings (independent sessions + disjoint roots); re-run one worker's failed cells with run_sweep.py --from-failures <worker root>/sweep_failures.json --output-root <worker root> [same lane flags as this launch]
(SystemExit: 1)
```

- Real-subprocess chain evidence: worker 0's tee log captured the genuine child line `[Dry-run] 1 planned cell(s) over 1 model(s) x 1 task(s) x 1 seed(s); manifest: .../finetuned-mgpu-w0/sweep_manifest.json`.

## TDD Cycle (both tasks tdd="true")

- **RED**: tests written first; initial run failed at collection (module absent), then against an interface skeleton (docstring + signatures + NotImplementedError) all 15 stage-1 tests failed on the planned behaviors — behavior-level RED, module importing cleanly (no syntax/fixture faults).
- **GREEN**: two stage-1 test bugs fixed on the way (a sizes-dict key mismatch in the tie-break test; the passthrough expectation missing the verbatim `--registry-dir` tokens) — test-expectation corrections, not implementation changes; implementation landed unchanged from the behavior rows.
- **REFACTOR**: none needed — the module was written to the row order (docstring -> naming fn -> lpt_shard -> parse_args -> validation -> argv/spawn -> aggregation) and needed no cleanup after GREEN.

## Deviations from Plan

None requiring Rules 1-4 (no bugs found, no blockers). Executor-owned details exercised per the plan's action row, recorded here:

- **Test helpers locally copied** (not cross-imported from test_sweep.py) — the plan offered the choice; `run_cli` needs the `spawner=` parameter anyway, and `make_registry` gained `size (M)` values (100/50/10) so CLI-driven LPT tests pin the expected `[[model-a], [model-b, model-c]]` partition.
- **Passthrough `--registry-dir` is scanned for the validation join** (`_registry_dir_from_passthrough`, both `X` and `=X` forms) while still forwarding verbatim — the orchestrator's unknown-name check must see the SAME registry view the workers will use (fixture/custom registries), which the five owned flags alone cannot express.
- **Collision refusal proven via a pinned colliding naming fn** — with the frozen naming function, worker roots cannot self-collide (the suffix always appends), so the guard is defense-in-depth against a future naming change; the test monkeypatches `worker_root` to alias the base root and proves the guard is wired and refuses BEFORE any spawn.

## Threat Mitigations Landed

| Threat | Mitigation | Proof |
|--------|------------|-------|
| T-12-01-01 root collision | frozen sibling roots + collision refusal in collect-all | `test_frozen_root_collision_refuses_collect_all` |
| T-12-01-02 argv injection | argv always a LIST of str, never a shell string | fake-spawner LIST/type assertions |
| T-12-01-03 env leakage | explicit env copy + exactly one CUDA key, per-index asserted incl. `--gpus "2,5"` | kwargs env assertions |
| T-12-01-04 lying exit | wait-all + verdict table + exit 0 iff all-0 | aggregation tests (scripted returncodes) |
| T-12-01-05 no-op workers | models>=workers collect-all refusal naming both counts | `test_workers_exceeding_model_count_refuses` |

## Known Stubs

None. No placeholder data, no unimplemented paths, no skipped tests, no unrun `<verify>` steps (the full gate ran once, green).

## What 12-02 / 12-04 Can Now Assume

- **12-02** does NOT touch the Makefile: `script/gen_progress.py` is already in `PHASE12_MODULES`, so lint coverage joins automatically the moment the file lands.
- **12-04** imports `run_sweep_shard.worker_root` / `worker_log_path` for `--merge` (one naming authority, already test-pinned), cites this CLI in `docs/multi-gpu.md`, and can rely on: `main(spawner=...)` seam, the frozen `sweep_manifest.json`-per-worker-root layout the merge will union, and the tier-1 suite as the regression net for any refactor of the launch path.

## Self-Check: PASSED

Files found: pipeline/run_sweep_shard.py, tests/test_sweep_shard.py, Makefile, 12-01-SUMMARY.md. Commits 683f2ff (Task 1) and c732fbb (Task 2) are ancestors of HEAD. Measured commit count 2 matches the ledger.
