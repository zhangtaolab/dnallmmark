---
phase: 15-dual-gpu-validation-subsets
plan: 1
subsystem: multi-gpu-dispatch-validation
tags: [dispatch, smoke, gpu, val-01, halted]
requires:
  - "Phase 13/14 frozen dispatch CLI (run_sweep_shard --mode dispatch, dispatch_core)"
provides:
  - "Executed 2-cell N=2 dispatch smoke evidence (both GPUs produced cells, dispatch_state done 2/2)"
  - "HALT record: dispatch roots carry no run_record.json (Phase 13 A3) — D15-02 consumption criterion unmeetable without modifying frozen dispatch code; remediation decision pending"
affects:
  - "15-03-PLAN.md (same false premise in its key_links: dispatch children are NOT run_sweep.py invocations)"
  - "Phase 18 DOCS-01 dispatch-first docs rewrite (blocked on the same producer-side gap)"
tech-stack:
  added: []
  patterns:
    - "D15-04 stop discipline executed: criteria failure -> preserve evidence, halt Task 3, never document an unproven procedure"
key-files:
  created:
    - .planning/phases/15-dual-gpu-validation-subsets/15-01-SUMMARY.md
  modified: []
decisions:
  - "Rule 4 + D15-04 halt: dispatch-root run_record.json gap is an architectural decision (frozen dispatch code), not an executor auto-fix"
metrics:
  duration: 17 min
  completed: 2026-10-20
  tasks: 2 of 3 (Task 3 halted per D15-04)
  commits: 0
  plan_head_before: 2626010e8dfcfa610606b740dc23b20e8704c986
  plan_head_after: 2626010e8dfcfa610606b740dc23b20e8704c986
status: halted
actuals:
  tokens: 9000   # chars/4 over the files actually changed (this SUMMARY + STATE/WINDOWS rows)
  tasks: 2       # tasks completed (Task 1 tracer + Task 2 run executed; verify partially green)
  commits: 0     # zero tracked-file task commits; the only commit is the halted-plan docs commit after this file
---

# Phase 15 Plan 1: N=2 Dispatch Smoke + Docs/Ledger Closure Summary

**One-liner:** The 2-cell dispatch smoke ran REAL training on both RTX 5090s and every engine-level criterion passed (dispatch_state "done" 2/2, both GPUs produced cell artifacts, ledger claims completed) — but the plan HALTED before docs closure because dispatch roots carry no run_record.json (Phase 13 decision A3), making the D15-02 consumption criterion ("[Dry-run] 2 run record(s)") unmeetable without modifying frozen dispatch code, which this plan's own prohibition forbids.

## Status: HALTED (D15-04 stop discipline — Rule 4 architectural decision required)

Task 3 (docs/multi-gpu.md rewrite + WINDOWS #21 + PROJECT.md D-05 closure) was NOT
executed: "never document an unproven procedure". The docs rewrite includes the
export_runs.py consumption step as part of the procedure; that step cannot pass today.
WINDOWS #21 stays **open**; PROJECT.md D-05 row stays **Pending**.

## What Was Executed

### Task 1 — D15-14 preflight + smoke-pair acquisition (tracer) — COMPLETE

- dnallm editable verified: `pip show dnallm` → `Editable project location:
  /root/autodl-tmp/Github/DNALLM` (v1.3.2) — no reinstall needed.
- CUDA verified: `torch.cuda.is_available() == True`, `device_count == 2`.
- Model acquired (62 s wall): `.venv/bin/modelscope download --model
  zhangtaolab/plant-dnabert-6mer --local_dir
  /root/autodl-tmp/dnallmmark-data/models/plant-dnabert-6mer` — config.json lands
  DIRECTLY in the model dir (flat `Model_path` contract).
- Dataset acquired (2 s wall): `.venv/bin/modelscope download --dataset
  forrestzhang/iDNA_ABF_datasets --local_dir
  /root/autodl-tmp/dnallmmark-data/datasets/iDNA_ABF_datasets --include "5mC/*"
  --exclude "*.DS_Store"` — row counts EXACTLY match the registry: train 2110 /
  dev 234 / test 2344 (T-15-01 declared-vs-measured reconciliation green).
- Tracer feedback gate re-run: verify green end-to-end.

### Task 2 — 2-cell dispatch smoke — EXECUTED; criteria 1-2 PASS, criterion 3 FAIL

Executed command (verbatim, from the repo root):

```bash
.venv/bin/python pipeline/run_sweep_shard.py --mode dispatch --workers 2 --gpus 0,1 \
  --models plant-dnabert-6mer --tasks iDNA_ABF_datasets__5mC --seeds 42,43 \
  --num_train_epochs 1 \
  --output-root "$(pwd)/pipeline/finetuned-smoke" \
  --log_dir "$(pwd)/pipeline/finetuned-smoke/logs"
```

- Wall duration: **157 s** (2026-10-20T13:59:43Z → 14:02:20Z, exit 0).
- Tee (live view, D15-10): `/root/autodl-tmp/phase15-evidence/smoke-dispatch.log`
  (final table: `status=done queue=0 done=2/2 failed=0 skipped=0`; verdicts
  `worker 0: cells=1 completed=1 gpu=0`, `worker 1: cells=1 completed=1 gpu=1`).

**D15-02 criterion 1 — both GPUs produced cell artifacts: PASS.**
- `workers[]`: w0 gpu=0 completed 1/1; w1 gpu=1 completed 1/1; failures [].
- Ledger claims `plant-dnabert-6mer--iDNA_ABF_datasets__5mC--seed{42,43}-*.json`
  both `state: completed`, one per GPU token.

**D15-02 criterion 2 — dispatch_state.json terminal "done": PASS.**
- run_id `aff2faa39a6c433188f1fbb9c75f0275`; status `done`; counts
  `{completed: 2, failed: 0, skipped: 0, total: 2}`; queue_depth 0.

**Per-cell artifacts:** both `seed_42/` and `seed_43/` contain
`final_metrics.json`, `flops_report.json`, `trainer_state.json` (+ checkpoints,
config, model.safetensors, runs/). **`run_record.json` is ABSENT from both cells —
the root cause of the halt (below).**

**D15-02 criterion 3 — consumption dry-run reporting "2 run record(s)": FAIL.**
`export_runs.py --dry-run --input-root pipeline/finetuned-smoke` exits 0 but prints
`[Dry-run] 0 run record(s) across 0 model(s) / 0 task(s)` — `load_run_records`
(script/export_runs.py:498-534) walks
`{root}/{model}/{task}/seed_{n}/run_record.json` and skips any cell without one.

**Isolation assertions (T-15-02): PASS** — smoke output root
`pipeline/finetuned-smoke` differs from the directories.json `output_root`
(`/root/autodl-tmp/dnallmmark-data/finetuned`); explicit `--output-root`/`--log_dir`
were passed (absolute, `"$(pwd)/"`-prefixed); no writes into `dnallm-mark/data/`
(git status clean over it).

### D15-16 evidence record (SHA256)

| Artifact | SHA256 |
|---|---|
| seed_42/final_metrics.json | `7c7e07fa3422e688afab22e9ef5a12dbad0827f90625e78bdad1e234e0a204f7` |
| seed_42/flops_report.json | `782da96e3d62fe83982562c228dc3957b585fb64decc665c9def026e2d86beaf` |
| seed_43/final_metrics.json | `51dc57d66507f8cdc45e8c8416dd92f4802b2cd129f2807103314ba6d69c349b` |
| seed_43/flops_report.json | `69cde0371f93e2bfd81ff6d8093ff4010b02390a47127f505d54535fa46210b0` |
| dispatch_state.json | `43419723af1bbadc99c37f3d6c94d510c096478de225280169125dffe234c072` |

Preserved evidence (never deleted): `pipeline/finetuned-smoke/` (dispatch_state.json,
dispatch_ledger/, both cell trees — gitignored runtime root, intact) and
`/root/autodl-tmp/phase15-evidence/` (smoke-dispatch.log tee, dispatch_state.final.json
copy, timing epochs).

## Root Cause Analysis (why criterion 3 cannot pass today)

The plan's premise — that dispatch cells carry `run_record.json` — is false for the
frozen Phase 13/14 CLI:

1. `run_record.json` is written ONLY by the run_sweep driver
   (`pipeline/run_sweep.py:21` "written by THIS driver", `RECORD_NAME` at :314).
2. In dispatch mode the children are `run_finetune.py` invoked DIRECTLY —
   `pipeline/dispatch_core.py:1941-1942`: "NO run_sweep.main runs in dispatch mode —
   the children are run_finetune.py directly." run_finetune.py writes
   final_metrics/flops_report/trainer_state, never run_record.
3. This is not an accident but the locked Phase 13 decision A3
   (13-01-PLAN.md:121-124): "Phase 13 dispatch roots carry child artifacts + the
   ledger + dispatch_state.json but NOT sweep_manifest.json/run_record.json ...
   exporters see a manifest-less root ... the documented Phase 14/15 handoff."
   Phase 14 never landed that handoff (14-02's --dry-run seam verifies MERGED
   STATIC roots only).
4. Phase 15's plans were written on the false premise: 15-RESEARCH.md's architecture
   diagram lists `run_record.json` per dispatch cell, and 15-03-PLAN.md key_links
   states "the dispatch children are run_sweep.py invocations that write it per
   cell" — contradicted by dispatch_core.py:1942. The gap was unobservable in
   dry-runs (dry-run writes only `sweep_manifest.json` with "planned" records, and
   no real dispatch run had ever executed — zero GPU assets existed on this box
   before Task 1).

## Deviations from Plan

### 1. [Rule 4 - Architectural] D15-04 halt: consumption criterion requires modifying frozen dispatch code

- **Found during:** Task 2 verification (criterion 3).
- **Issue:** dispatch roots carry no `run_record.json` (Phase 13 A3), so
  `export_runs.py` counts 0 records and the D15-02 consumption criterion fails.
- **Why not auto-fixed (Rules 1-3):** teaching dispatch_core to write run_record
  per cell is new functionality in a frozen, 93+-test-pinned engine (payload
  composition from final_metrics + claim-time lane records, WR-12 no-overwrite
  semantics, ordering vs the trainer_state marker) — a structural change with
  cross-plan impact (15-03's entire consumption proof depends on it). The plan's
  prohibition is explicit: "The smoke must not modify any pipeline dispatch/training
  code — the Phase 13/14 CLI runs VERBATIM; defects route through the normal fix
  flow (D15-04, D15-16), never in-phase redesign."
- **Action taken:** D15-04 stop discipline — evidence preserved, Task 3 halted,
  failure recorded here, remediation routed to the maintainer (options below).
- **Files modified:** none (pipeline untouched; `git status` shows zero
  source-file changes from this plan).

### Remediation options (maintainer decision required)

| Option | Description | Impact |
|---|---|---|
| **1 (recommended)** | Planned fix (debug flow / mini-plan): dispatch_core writes `run_record.json` per completed cell at finalize — reusing run_sweep's own record builder (`run_sweep.py:1356` build-skeleton, "never re-implemented" discipline), lane flags from the claim-time records (D14-06), WR-12 no-overwrite. Supersedes A3 exactly where A3 said the handoff would land. | ~1 focused plan (code + dispatch-suite tests + A3 decision supersession); unblocks 15-01 criterion 3 (fresh 2-min smoke re-run after the fix) AND 15-03 wholesale; keeps D15-11 "zero chain modification" intact (producer side only) |
| 2 | Offline adapter script synthesizing run_records from final_metrics + ledger claims post-run | Adds a NEW producer fabricating the pipeline's own attestation — provenance/reviewer-trust concern; new unplanned script; weaker than 1 |
| 3 | Run the small sweep in STATIC mode (workers are run_sweep.py → native run_records) | Contradicts D15-10 (dispatch is the locked run mode) and the milestone's core deliverable; only viable as an explicit maintainer scope change |

**Consequence for 15-03:** its Task-2/Task-3 verifiers and key_links inherit the
same false premise; whichever option is chosen must land BEFORE 15-03 executes.

## Auth Gates

None.

## Known Stubs

None. (No code was written by this plan; no stubs introduced.)

## Threat Flags

None — no new security-relevant surface beyond the plan's threat model. T-15-01
(official-channel downloads + row-count reconciliation) and T-15-02 (root
isolation, explicit roots, committed data untouched) mitigations both verified
green above.

## Self-Check: PARTIAL (halted plan)

- Evidence files: pipeline/finetuned-smoke/dispatch_state.json FOUND;
  /root/autodl-tmp/phase15-evidence/smoke-dispatch.log FOUND; both cell trees FOUND.
- Task commits: 0 expected (Tasks 1-2 touch only gitignored/untracked runtime
  areas) — 0 present, consistent.
- Task 3 artifacts deliberately ABSENT (halt): docs/multi-gpu.md unchanged,
  WINDOWS #21 open, PROJECT.md D-05 Pending — verified below in Self-Check output.

Self-Check run output (2026-10-20): all 8 evidence artifacts FOUND; retired phrase
count in docs/multi-gpu.md == 1 (unchanged); WINDOWS #21 open; PROJECT.md D-05
Pending; `git status` over pipeline/ script/ docs/ dnallm-mark/ == 0 lines (zero
source changes — prohibition 1 honored); commit ledger
`gsd-plan-head-before-15-01` = 2626010, task commits since base = 0 (expected:
Tasks 1-2 are gitignored runtime areas). Self-Check PASSED for the halted scope.
