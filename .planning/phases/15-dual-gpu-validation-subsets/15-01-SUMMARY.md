---
phase: 15-dual-gpu-validation-subsets
plan: 1
subsystem: multi-gpu-dispatch-validation
tags: [dispatch, smoke, gpu, val-01, resumed-after-15-04]
requires:
  - "Phase 13/14 frozen dispatch CLI (run_sweep_shard --mode dispatch, dispatch_core)"
provides:
  - "Executed 2-cell N=2 dispatch smoke evidence, ALL D15-02 criteria green incl. consumption dry-run ([Dry-run] 2 run record(s)) on the 15-04-fixed engine"
  - "docs/multi-gpu.md dispatch-mode N=2 procedure (copy-paste of the executed argv/outputs, procedure/doc identity) + revised machine roles 本机=双卡验证机 (D15-03)"
  - "WINDOWS #21 closed with evidence; WINDOWS #44 (the halt's own deviation row) closed; PROJECT.md D-05 row done; VAL-01 complete in REQUIREMENTS.md"
affects:
  - "15-03-PLAN.md (premises already corrected by 15-04; its consumption proof now rests on the executed criterion-3 evidence here)"
  - "Phase 18 DOCS-01 (the full dispatch-first rewrite builds on this landed D15-01/D15-03 surface)"
tech-stack:
  added: []
  patterns:
    - "Fresh-root re-run discipline: preserved halt evidence root + suffixed re-run root (finetuned-smoke*/ gitignore family) so trainer_state marker-skip can never mask a regression"
key-files:
  created:
    - .planning/phases/15-dual-gpu-validation-subsets/15-01-SUMMARY.md
  modified:
    - docs/multi-gpu.md
    - .planning/WINDOWS.md
    - .planning/PROJECT.md
    - .gitignore
decisions:
  - "Fresh root (pipeline/finetuned-smoke-r2) for the continuation re-run: the halted run's root is preserved evidence and its cells would skip on trainer_state markers — a re-run must re-execute real training to prove the run_record writer"
  - "WINDOWS #44 closed alongside #21: the halt's own deviation row is resolved by 15-04 (Option 1 ruling) + this re-run; leaving it open would falsely block ship"
metrics:
  duration: 47 min total (17 min halted session + ~30 min continuation)
  completed: 2026-10-20
  tasks: 3 of 3
  commits: 4
  plan_head_before: 2626010e8dfcfa610606b740dc23b20e8704c986
  plan_head_after: 5295cbd364488be0f8195b3878717d6292a72b84
status: complete
actuals:
  tokens: 16000   # chars/4 over the plan's realized diffs (halt SUMMARY ~9K + continuation docs/ledger/SUMMARY)
  tasks: 3        # tasks completed across both sessions
  commits: 4      # 15-01-attributed: 117fe2d (halt record) + 0c6c865 + 5295cbd + final docs commit
---

# Phase 15 Plan 1: N=2 Dispatch Smoke + Docs/Ledger Closure Summary

**One-liner:** The dispatch-mode N=2 smoke ran REAL 1-epoch training on both RTX 5090s twice — the first attempt halted at the run_record.json gap (all engine criteria green, consumption criterion unmeetable), 15-04 landed the producer-side fix, and the continuation's fresh-root re-run passed ALL FOUR D15-02 criteria including "[Dry-run] 2 run record(s)", after which docs/multi-gpu.md was rewritten as the executed dispatch procedure (本机=双卡验证机), WINDOWS #21/#44 closed, PROJECT.md D-05 done, and VAL-01 completed.

## Status: COMPLETE (3/3 tasks, resumed after 15-04)

The plan originally HALTED at Task 3 (D15-04 stop discipline) when the first
smoke revealed dispatch roots carry no run_record.json (Phase 13 decision A3's
deferred handoff never landed). The maintainer ruled remediation Option 1;
plan 15-04 landed it (commits 9c22787/8c5e8b9). This continuation re-ran the
smoke on a FRESH root and completed Task 3. The halt record is preserved
below as part of the story — it is why the executed procedure in the docs
uses `finetuned-smoke-r2`.

## What Was Executed

### Task 1 — D15-14 preflight + smoke-pair acquisition (tracer) — COMPLETE (halted session)

- dnallm editable verified: `pip show dnallm` → `Editable project location:
  /root/autodl-tmp/Github/DNALLM` (v1.3.2) — no reinstall needed.
- CUDA verified: `torch.cuda.is_available() == True`, `device_count == 2`.
- Model acquired (62 s wall): `.venv/bin/modelscope download --model
  zhangtaolab/plant-dnabert-6mer --local_dir
  /root/autodl-tmp/dnallmmark-data/models/plant-dnabert-6mer` — config.json
  lands DIRECTLY in the model dir (flat `Model_path` contract).
- Dataset acquired (2 s wall): `.venv/bin/modelscope download --dataset
  forrestzhang/iDNA_ABF_datasets --local_dir
  /root/autodl-tmp/dnallmmark-data/datasets/iDNA_ABF_datasets --include
  "5mC/*" --exclude "*.DS_Store"` — row counts EXACTLY match the registry:
  train 2110 / dev 234 / test 2344 (T-15-01 declared-vs-measured green).
- Re-verified at continuation start (D15-14 standing rule): dnallm editable
  present, both GPUs 0% utilization, assets intact.

### Task 2 — 2-cell dispatch smoke — COMPLETE (two executions; final run all-green)

**Execution A (halted session, root `pipeline/finetuned-smoke`):** 157 s
wall, exit 0. D15-02 criteria 1-2 PASS (both GPUs produced cells;
dispatch_state "done" 2/2) but criterion 3 FAILed — dispatch roots carried
no `run_record.json` (Phase 13 A3), so `export_runs.py --dry-run` reported
0 records. D15-04 stop discipline: Task 3 halted, evidence preserved
(`pipeline/finetuned-smoke/` intact + `/root/autodl-tmp/phase15-evidence/
smoke-dispatch.log`), WINDOWS #44 recorded, remediation routed to the
maintainer. Root-cause analysis and the three remediation options live in
git history (halt commit 117fe2d) and 15-04-SUMMARY.

**Execution B (this continuation, root `pipeline/finetuned-smoke-r2`, FRESH
so the trainer_state marker-skip cannot mask the re-run):** run plan printed
first (D15-13), then executed verbatim from the repo root:

```bash
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
.venv/bin/python pipeline/run_sweep_shard.py --mode dispatch --workers 2 --gpus 0,1 \
    --models plant-dnabert-6mer --tasks iDNA_ABF_datasets__5mC --seeds 42,43 \
    --num_train_epochs 1 \
    --output-root "$(pwd)/pipeline/finetuned-smoke-r2" \
    --log_dir "$(pwd)/pipeline/finetuned-smoke-r2/logs"
```

- Wall duration: **155 s** (2026-10-20T15:20:00Z → 15:22:35Z, exit 0).
- Tee: `/root/autodl-tmp/phase15-evidence/smoke-dispatch-r2.log` — final
  table `status=done queue=0 done=2/2 failed=0 skipped=0`; verdicts
  `worker 0: cells=1 completed=1 gpu=0`, `worker 1: cells=1 completed=1
  gpu=1`; live view showed `w0 gpu=0: .../seed_42` and `w1 gpu=1:
  .../seed_43` in flight simultaneously.
- run_id `7759c2cc05364ebdacd2c6a5fa614bac`.

**D15-02 pass criteria — ALL FOUR PASS on execution B:**

1. **Both GPUs produced cell artifacts: PASS** — workers[] `{index:0,
   gpu:"0", cells:1, completed:1}` and `{index:1, gpu:"1", cells:1,
   completed:1}`; ledger claims seed42→gpu 0, seed43→gpu 1.
2. **dispatch_state.json terminal "done": PASS** — status `done`; counts
   `{completed: 2, failed: 0, skipped: 0, total: 2}`; queue_depth 0.
3. **Consumption dry-run: PASS** — `export_runs.py --dry-run --input-root
   pipeline/finetuned-smoke-r2` exits 0 printing `[Dry-run] 2 run record(s)
   across 1 model(s) / 1 task(s)` — the criterion the halt was about,
   now green on a REAL GPU run through the 15-04 writer (both cells carry
   `run_record.json`, status completed, metrics loaded verbatim from
   final_metrics.json).
4. **Procedure/doc identity: PASS** — docs/multi-gpu.md now carries the
   executed argv + copy-paste key output lines (Task 3 below).

Per-cell artifacts: both `seed_42/` and `seed_43/` contain
`final_metrics.json`, `flops_report.json`, `trainer_state.json`, AND
`run_record.json`. Isolation (T-15-02) PASS: smoke root
`pipeline/finetuned-smoke-r2` ≠ directories.json `output_root`
(`/root/autodl-tmp/dnallmmark-data/finetuned`); explicit absolute
`--output-root`/`--log_dir` passed; `git status` over `dnallm-mark/data/`
and over `pipeline/`+`script/` sources = 0 lines (committed data and
frozen sources untouched).

### Task 3 — docs/multi-gpu.md dispatch-mode rewrite + ledger closure — COMPLETE

1. **Smoke section**: the 9-step other-machine static-shard procedure
   replaced by the executed dispatch-mode N=2 procedure — `--mode dispatch
   --workers 2 --gpus 0,1`, pair plant-dnabert-6mer ×
   iDNA_ABF_datasets__5mC (full dataset), seeds 42,43 with the WHY-2-cells
   rationale (one cell idles worker 1; Pitfall 2), 1 epoch, explicit
   absolute roots with the child-cwd + directories.json rationale, the
   offline-env note, the dispatch_state terminal-status assertion, the 4
   per-cell artifacts, the `export_runs.py --dry-run` consumption step,
   and the no-merge/no-cleanup dispatch-root boundary (A6/MGPU-06) plus
   the fresh-root re-run note. Copy-paste of the actual argv and output.
2. **Machine roles (D15-03)**: 本机=双卡验证机 — the local 2×5090 box IS
   the validation machine; the old two-machine split retired; CI stays
   zero-GPU (D15-15 note).
3. **§5 cleanup tail**: manual `rm -rf` recipe replaced by the `--cleanup`
   command shape (typed phrase, verify-first) with the dispatch-roots-need-
   neither note.
4. **Scope guard held**: decision table, §1-§4 static runbook, E2' section
   byte-untouched (diff hunks confined to the three sanctioned regions) —
   the full dispatch-first rewrite is Phase 18 (DOCS-01).
5. **WINDOWS #21 closed** (unrun-verify → fixed) with the executed-smoke
   resolution + evidence links; **WINDOWS #44 closed** (the halt's own
   deviation row) naming the 15-04 fix + this green re-run. Ledger
   counts now open 8 / fixed 30, validated by `gsd-tools windows status`.
6. **PROJECT.md D-05 row**: "— Pending" → ✓ Landed with the revised-docs +
   executed-smoke resolution.
7. **REQUIREMENTS.md**: VAL-01 checkbox + traceability row → Complete with
   criterion evidence.

## Verification Evidence

- Task 2 automated verify (all legs): state assert `done` 2/2 PASS; 8×
  `test -f` per-cell artifacts PASS (incl. run_record.json both cells);
  `grep -F "[Dry-run] 2 run record(s) across 1 model(s) / 1 task(s)"` PASS.
- Task 3 automated verify (all legs): retired-phrase count 0;
  `双卡验证机` / `--mode dispatch` / `--seeds 42,43` present;
  `^| 21 |.*| fixed |` count 1; `D-05 machine-role revision.*Pending`
  count 0.
- Fresh root gitignored (`finetuned-smoke*/` matches; `git check-ignore`
  verified; zero untracked smoke noise in `git status`).
- No pipeline/script source modified by this plan (porcelain empty over
  `pipeline/` + `script/` beyond the sanctioned files).

## D15-16 evidence record (SHA256)

Execution A (halted; preserved under `pipeline/finetuned-smoke/`):

| Artifact | SHA256 |
|---|---|
| seed_42/final_metrics.json | `7c7e07fa3422e688afab22e9ef5a12dbad0827f90625e78bdad1e234e0a204f7` |
| seed_42/flops_report.json | `782da96e3d62fe83982562c228dc3957b585fb64decc665c9def026e2d86beaf` |
| seed_43/final_metrics.json | `51dc57d66507f8cdc45e8c8416dd92f4802b2cd129f2807103314ba6d69c349b` |
| seed_43/flops_report.json | `69cde0371f93e2bfd81ff6d8093ff4010b02390a47127f505d54535fa46210b0` |
| dispatch_state.json | `43419723af1bbadc99c37f3d6c94d510c096478de225280169125dffe234c072` |

Execution B (continuation; under `pipeline/finetuned-smoke-r2/`):

| Artifact | SHA256 |
|---|---|
| seed_42/final_metrics.json | `996ee18937f20023432c4ef7555e47d1fe241e2a209f41a27b6e5132a3cf1b97` |
| seed_42/flops_report.json | `6c7f3350b58d08356c6580748f2c7e26c7945575d7c8c121677a53b0fc1accb4` |
| seed_42/run_record.json | `494a398a09f9e1102e282575dd12d750b6be644da1eb319bf49c2a593c27db59` |
| seed_43/final_metrics.json | `a373af0305126589e84f7db73482dfcb1686b441252ee4f8c71bacc4a977e321` |
| seed_43/flops_report.json | `277f3a9423740005d9302f76e3ba1e966b741bac548fc244eaa14f7f3a2ee2ac` |
| seed_43/run_record.json | `ae495d2c9ed11c3dd578e3d39104da2475e6393bba2c434981cc955fea871212` |
| dispatch_state.json | `8dce035846c084869c51582fb3728ba6805373d252be415a2f875c46eef64cfb` |

Evidence preserved: both smoke roots (gitignored runtime, intact),
`/root/autodl-tmp/phase15-evidence/` (smoke-dispatch.log,
smoke-dispatch-r2.log, dispatch_state.final.json,
dispatch_state.final-r2.json, timing files).

## Deviations from Plan

### 1. [Rule 4 → resolved out-of-plan] The halt itself (execution A, Task 2 criterion 3)

Dispatch roots carried no run_record.json (Phase 13 A3) — an architectural
gap, not an executor auto-fix. Halted per D15-04; maintainer ruled Option 1;
15-04 landed the writer (supersedes A3). Resolved: criterion 3 green on
execution B. Recorded as WINDOWS #44 (now fixed).

### 2. [Rule 3 - Blocking] Fresh root needs a gitignore family entry

- **Found during:** continuation Task 2 prep.
- **Issue:** the re-run requires a fresh root (the old root's trainer_state
  markers would skip both cells), but `pipeline/finetuned-smoke-r2/` matched
  no ignore pattern — the run would leave untracked runtime noise, violating
  the never-leave-generated-files-untracked discipline.
- **Fix:** generalize `.gitignore` `finetuned-smoke/` → `finetuned-smoke*/`
  (verified: 0 tracked files match, working tree clean of the family).
- **Files modified:** .gitignore
- **Commit:** 0c6c865

### 3. [Ledger hygiene] WINDOWS #44 closed alongside #21

Not named in the plan (the row did not exist when the plan was written —
the halt created it). Its remediation landed via 15-04 and is proven by
execution B; leaving it open would falsely block `/gsd-ship`. Closed with
a resolution naming the fix commits and the green criterion.
- **Commit:** 5295cbd

## Auth Gates

None.

## Known Stubs

None. (No code was written by this plan; the docs describe only executed
commands — procedure/doc identity verified.)

## Threat Flags

None — no new security-relevant surface beyond the plan's threat model.
T-15-01 (official-channel downloads + row-count reconciliation) verified in
Task 1; T-15-02 (root isolation, explicit roots, committed data untouched)
verified on BOTH executions; T-15-SC held (zero installs this plan).

## Edge Flag (carried from must_haves)

The smoke's edge behavior is covered only by the D15-02 pass-criteria
assertions recorded above (no unresolved edge probe was triggered — VAL-01
came back unclassified, no deterministic category); flagged as an
assumption for human review at verification.

## Self-Check: PASSED

- Created/modified files FOUND: docs/multi-gpu.md, .planning/WINDOWS.md,
  .planning/PROJECT.md, .gitignore, .planning/REQUIREMENTS.md,
  .planning/ROADMAP.md, this SUMMARY, STATE.md.
- Evidence FOUND: pipeline/finetuned-smoke-r2/dispatch_state.json (status
  done 2/2), both cell trees incl. run_record.json, tee log
  smoke-dispatch-r2.log, dispatch_state.final-r2.json evidence copy.
- Commits FOUND and ancestors of HEAD: 117fe2d (halt record),
  0c6c865 (gitignore), 5295cbd (Task 3); ledger
  gsd-plan-head-before-15-01 = 2626010.
- Commit-count measurement note: `git rev-list --count 2626010..HEAD` = 7
  at self-check time, of which 4 are plan 15-04's own commits
  (98d7279/9c22787/8c5e8b9/d160758 — attributed to 15-04's ledger,
  measured there as 2 task commits + plan docs). The 15-01-attributed
  count is 4: 117fe2d + 0c6c865 + 5295cbd + this SUMMARY's docs commit.
- Gates re-run at self-check: Task 3 identity gate PASS; consumption
  dry-run gate PASS ([Dry-run] 2 run record(s)).
- No push performed (v1.3 local-commits-only policy held).
