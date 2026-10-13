---
phase: 12-multi-gpu-orchestration-console-hardening
plan: "04"
subsystem: pipeline
tags: [multi-gpu, merge, sha256, manifest-union, decision-doc, ddp-vs-sharding]

requires:
  - phase: 12-multi-gpu-orchestration-console-hardening (12-01)
    provides: pipeline/run_sweep_shard.py launch mode + worker_root()/worker_log_path() (the ONE naming authority --merge imports) + the tier-1 suite this plan extends
  - phase: 12-multi-gpu-orchestration-console-hardening (12-02)
    provides: script/gen_progress.py + the frozen sweep.json contract the runbook's mirror step cites
provides:
  - "run_sweep_shard.py --merge mode — allowlist copy + SHA256-verify + manifest/failures union with output_dir rewrite + lane-equality refusal (MGPU-02 artifact half, D-09)"
  - "--include-checkpoints escape hatch (A2) and the MERGE_ALLOWLIST scope constant"
  - "the merge tier-1 suite (17 new tests; 39 total in tests/test_sweep_shard.py) incl. consumer equivalence over the real export_runs walk and worker immutability"
  - "docs/multi-gpu.md — the D-04 sharding-vs-DDP decision matrix, CLI runbook, killpg/Ctrl-C semantics, E2' trust boundary, D-05 machine roles, and the 9-step other-machine smoke procedure (MGPU-03)"
  - "README one-line link to docs/multi-gpu.md"
affects: [12-05, phase-12-verification, gsd-verify-work, multi-gpu-smoke-executor (maintainer, other machine)]

actuals:
  tokens: 19994   # chars/4 over the realized diff (git diff 6de1afc..HEAD = 79976 chars)
  tasks: 3
  commits: 4      # MEASURED: git rev-list --count 6de1afc..HEAD

tech-stack:
  added: []        # stdlib only: hashlib + shutil; zero pyproject/uv.lock change (verified empty diff)
  patterns:
    - "copy + SHA256-verify merge (hash, copy, re-hash, compare per file; any mismatch refuses before the merged manifests land — a partial corrupt merge never becomes a sweep root)"
    - "boundary-guarded prefix swap for output_dir rewriting (w0 is a raw string prefix of w01 — the swap only fires on exact or /-boundary matches)"
    - "lane signature = every cell key outside the identity projection {model,task,seed,status,output_dir}, compared as canonical-JSON value sets across worker manifests"

key-files:
  created:
    - docs/multi-gpu.md
    - .planning/phases/12-multi-gpu-orchestration-console-hardening/evidence/12-04-task1-red.json
  modified:
    - pipeline/run_sweep_shard.py
    - tests/test_sweep_shard.py
    - README.md

key-decisions:
  - "Lane equality compares every cell key outside the identity projection (canonical-JSON value sets) — this catches peft/config_variant/num_train_epochs/subset_file/effective_batch_size/cache_dir exactly as recorded via sweep_flags, and any lane key a future driver merges into cells the same way"
  - "Known limitation, documented: run_sweep manifests do not record peft/curve at sweep level (peft lives in run_record.json; curve lives in output_dir shape), so a REAL lora-worker-vs-base-worker merge is not machine-detectable from the manifests alone — the runbook's lane-match warning (the D-08 re-run row carries the same hazard) is the guard; the fixture-level peft refusal proves the check fires whenever the flag IS recorded"
  - "The corruption unit test simulates a corrupt copy by pre-writing a tampered destination under a neutered copyfile (a plain overwrite would repair the tamper and verify green — the only honest way to make _copy_verified observe post-copy divergence)"
  - "Task 2's suite landed green-on-first-run by design: the plan's Task-1 action row front-loads RED ('write Task 2's failing tests first for the equality-refusal and the rewrite'); non-vacuity proven by three throwaway mutation probes (allowlist shrink / verify-disabled / rewrite-disabled each turn the suite red)"
  - "docs/multi-gpu.md normalizes the Area-10 draft's inconsistent root spellings onto the frozen {root}-mgpu-w{i} pattern (the draft mixed ./finetuned-smoke-mgpu and finetuned-smoke-mgpu-w0, which the real naming would render finetuned-smoke-mgpu-mgpu-w0)"

patterns-established:
  - "RED evidence via interface skeleton (the 12-01 precedent, second application): flags parse + seams raise NotImplementedError so the behavior rows fail on missing behavior, never on collection/import"
  - "Consumer-equivalence testing: import the REAL consumer (export_runs.load_run_records / sweep_monitor.full_scan) in the tier-1 suite and assert the merged root reads as the exact union — no mock walk"

requirements-completed: [MGPU-02, MGPU-03]   # declared by 12-05 too — the shared-ID gate holds REQUIREMENTS.md open until 12-05 lands

coverage:
  - id: D1
    description: "The --merge mode — collect-all validation (missing root/manifest, stray passthrough, lane inequality), MERGE_ALLOWLIST copy with frac_*/ recursion, --include-checkpoints hatch, per-file SHA256 verify refusing before the manifests land, union manifest/failures with output_dir rewrite, matrix union, deterministic JSON writes"
    requirement: MGPU-02
    verification:
      - kind: unit
        ref: "tests/test_sweep_shard.py#test_merge_happy_path_copies_allowlist_and_rewrites .. test_merge_refuses_stray_passthrough + ruff pipeline/run_sweep_shard.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "The merge suite — corruption red-on-tamper (unit + merge level), consumer equivalence over the real export_runs walk and the scanner's manifest branch, idempotent byte-stable re-merge, worker-root byte/mtime immutability across default and hatch merges; mutation-probed non-vacuous"
    requirement: MGPU-02
    verification:
      - kind: unit
        ref: "tests/test_sweep_shard.py#test_copy_verified_unit_detects_corruption, test_merged_root_is_consumer_equivalent, test_merge_is_idempotent_byte_stable, test_merge_leaves_worker_roots_immutable (39/39 module; 1569 pytest total)"
        status: pass
    human_judgment: false
  - id: D3
    description: "docs/multi-gpu.md — the D-04 decision matrix with the run_finetune :1357/:1542 scaffolding citations and the deferred-DDP decision, 适用场景 guidance, the full CLI runbook (launch/killpg/isolated re-run/merge/mirror), the D-05 machine-role note verbatim, the honest E2'-vs-CLI boundary, the A1 override note, and the 9-step other-machine smoke procedure + the README link"
    requirement: MGPU-03
    verification:
      - kind: unit
        ref: "topic grep (decision/CUDA_VISIBLE_DEVICES/from-failures/merge/gen_progress/kill/smoke all present) + README multi-gpu link"
        status: pass
    human_judgment: true
    rationale: "The grep proves every required topic is present, not that the doc is adequate as the D-04 decision record or that its commands are right for the maintainer's machines — and the 9-step procedure is executed by the maintainer on ANOTHER machine (D-05), so its real-world correctness lands only when that run is recorded (WINDOWS.md entry #21 tracks it)"

duration: 28min
completed: 2026-10-13
status: complete
plan_head_before: 6de1afcb22b9cb64e7c8f800f089df611ab193ec
plan_head_after: 22a490df93e4b0583be665b420e3c686903292ee
---

# Phase 12 Plan 04: Merge Mode + Multi-GPU Decision Doc Summary

**`--merge` in `pipeline/run_sweep_shard.py` unions N frozen worker roots into one SHA256-verified consumer root the existing data chain reads unchanged (allowlist copy, lane-equality refusal, output_dir rewrite, consumer-equivalence-proven), plus `docs/multi-gpu.md` — the D-04 sharding-vs-DDP decision matrix, the full CLI runbook, and the 9-step other-machine smoke procedure — with the README one-liner**

## Performance

- **Duration:** ~28 min
- **Started:** 2026-10-13T13:09:18Z
- **Completed:** 2026-10-13T13:37:05Z
- **Tasks:** 3 (2 TDD)
- **Files modified:** 5 (code+tests+docs+evidence)

## Accomplishments

- **Task 1 — the `--merge` mode** (`pipeline/run_sweep_shard.py`, +510/-19): collect-all validation (workers<1, non-empty passthrough — merge takes no sweep flags, dry-run+merge conflict, missing worker root, worker root without a manifest, malformed manifest/failures, cell output_dir outside its worker root, lane-flag inequality with per-root per-flag diagnostic) → allowlist copy with `frac_*/` recursion → per-file SHA256 verify (any mismatch refuses BEFORE the merged manifests land) → union manifest + failures with `output_dir` prefix-rewritten onto the merged root → matrix.models/tasks/seeds unioned with `output_root` = merged root → deterministic JSON writes (the run_sweep `_write_json` discipline, mirrored locally). `--models` moved from argparse-required to validation-layer launch-mode-required so merge mode takes none. Pure seams: `MERGE_ALLOWLIST`, `_copy_verified`, `_rewrite_output_dir` (boundary-guarded — `...-mgpu-w0` is a raw string prefix of `...-mgpu-w01`), `_lane_signature`. The merge never mutates a worker root and never deletes anything (D-08; cleanup is the runbook step).
- **Task 2 — the merge suite** (+362 tests): the two-worker fixture pair (curve cell + `frac_0.5` child, stray `checkpoint-500/`+`runs/`, planned-but-never-run cell, missing-flops_report cells), happy path (byte-identical copies at exact relative paths, strays absent by default / present under the hatch, never-run cell counted with its rewritten entry, per-cell suffix-preserved rewrite, matrix+failures union, console counts 15/8 + 5 cells/1 failure), corruption red (unit `_copy_verified` + merge-level monkeypatched corrupting copy refusing with manifests NOT written), missing-root/missing-manifest/passthrough refusals, **consumer equivalence over the real `export_runs.load_run_records` walk** (merged key set == worker union) + `sweep_monitor.full_scan` manifest branch (finished, 4 done / 5 total), idempotent byte-stable re-merge, and worker-root byte/mtime immutability across both a default and a hatch merge.
- **Task 3 — `docs/multi-gpu.md` (NEW, 247 lines) + README one-liner**: the two-column decision matrix (sharding: multi-model throughput, embarrassingly parallel cells, zero code coupling, every model incl. customs; DDP: single-large-model acceleration — the `run_finetune.py:1357/:1542` WORLD_SIZE/LOCAL_RANK scaffolding cited, data-splitting orchestration deferred BY DECISION per 12-CONTEXT) + 适用场景 guidance; the CLI runbook (launch with `--dry-run` first, slot-5 per-worker view, the killpg recipe + Ctrl-C detach semantics, the D-08 one-line isolated `--from-failures` re-run with the lane-match warning, the D-09 merge with the checkpoints hatch + post-merge cleanup, the exact gen_progress mirror command with the never-both-roots warning); the A1 size-proxy honesty note + `--models` manual override; the D-05 machine-role note verbatim; the honest E2'-vs-CLI trust boundary (Pitfall 7); and the 9-step N=2 other-machine smoke procedure (below). README gains the link beside METHODOLOGY/ONBOARDING.

## Task Commits

1. **Task 1 RED — merge lane-equality + rewrite tranche** - `eda9153` (test; includes the interface skeleton, the 12-01 precedent)
2. **Task 1 GREEN — the --merge mode** - `e6e1328` (feat)
3. **Task 2 — the full merge suite** - `278a21e` (test)
4. **Task 3 — the decision doc + README link** - `22a490d` (docs)

**Plan metadata:** (this commit)

## Verification

- Module lane during TDD: RED 6 failed / 22 green → GREEN 28/28 → suite 39/39; `ruff check pipeline/run_sweep_shard.py tests/test_sweep_shard.py` clean.
- **Full gate ONCE at plan end** (SPEED DIRECTIVE): `make test` → **1569 passed** pytest + node lane **26/26**; `make lint` → All checks passed; `make typecheck` → All checks passed.
- **Hard constraints verified:** `git diff --stat 6de1afc..HEAD -- pyproject.toml uv.lock pipeline/run_sweep.py pipeline/run_finetune.py tui/ Makefile` is EMPTY (zero dependency changes, run_sweep byte-untouched — the orchestrator's flag surface grew by exactly `--merge` and `--include-checkpoints`); the plan diff is exactly the 4 planned files + the evidence JSON.
- **SUMMARY spot evidence — merge console output over the fixture pair** (per-worker counts + union count):

```text
[Merge] worker 0: 15 file(s) copied + SHA256-verified from .../finetuned-mgpu-w0, 1 cell(s) with no files on disk
[Merge] worker 1: 8 file(s) copied + SHA256-verified from .../finetuned-mgpu-w1
[Merge] union: 5 cell(s) and 1 failure entry(ies) over 2 worker manifest(s) -> .../finetuned
[Merge] wrote .../finetuned/sweep_manifest.json and .../finetuned/sweep_failures.json
[Merge] worker roots left INTACT (re-runnable in isolation, D-08) — delete them manually only after verifying the merged root; never pass worker roots AND the merged root to gen_progress together (double-counted sweeps)
```

- **Consumer-equivalence assertion** (test green): `key_set(export_runs.load_run_records(merged)) == key_set(w0) | key_set(w1)` and `full_scan(roots=[merged])` → one sweep, `state == "finished"`, `total == 5`, `done == 4`.
- Task 3 topic grep green (decision / CUDA_VISIBLE_DEVICES / from-failures / merge / gen_progress / kill / smoke all present; README link at :122).

## TDD Cycle (Tasks 1-2 tdd="true")

- **Task 1 RED** (`evidence/12-04-task1-red.json`, classifier **RED_EVIDENCE_OK**): 6 tests against the interface skeleton — peft + num_train_epochs lane refusals, the 4 `_rewrite_output_dir` unit rows — all failing on planned behavior (module importing cleanly; the 12-01 skeleton precedent). Semantic assessment: failures are the absent merge behaviors, never collection/import/fixture faults.
- **Task 1 GREEN**: full implementation landed from the behavior rows; 6/6 tranche green + the 22 launch tests untouched-green; ruff clean. No test-side fixes needed.
- **Task 2 — green-on-first-run, investigated and documented**: the plan's Task-1 action row explicitly front-loads RED ("write Task 2's failing tests first for the equality-refusal and the rewrite (RED→GREEN)"), so the remaining suite pins landed behavior and passed immediately (39/39). Per the TDD reference's unexpected-green rule this was investigated rather than accepted blindly: **non-vacuity proven by three throwaway mutation probes** — (1) dropping `flops_report.json` from `MERGE_ALLOWLIST` → happy-path RED; (2) disabling the SHA compare in `_copy_verified` → both corruption tests RED; (3) disabling the output_dir rewrite → rewrite unit + happy-path RED. Probes run on scratch copies, never committed; no `12-04-task2-red.json` exists because no genuine failing run occurred and fabricating one is forbidden.
- **REFACTOR**: none — the module was written to the behavior-row order.

## Deviations from Plan

None requiring Rules 1-4 (no bugs found, no blockers, no scope creep). Executor-owned details, recorded:

- **Lane-equality surface**: compares every cell key outside the identity projection {model, task, seed, status, output_dir} as canonical-JSON value sets — operationally "every sweep_flags key except the sharded axis" exactly as the plan's behavior row defines, and it catches any future lane key recorded the same way (the peft fixture row proves the machinery). Known limitation documented in key-decisions: run_sweep manifests do not record peft/curve at sweep level, so a real lora-vs-base worker pair is invisible to the manifest comparison — the runbook's lane-match warning is the guard for that residual.
- **Corruption unit-test shape**: pre-tampered destination + neutered `copyfile` (a plain overwrite would repair the tamper and verify green — the plan's "simulate by pre-writing a tampered destination" only bites when the copy lands nothing).
- **Area-10 root spelling normalization** in the doc (the draft's `./finetuned-smoke-mgpu` base would produce double-`mgpu` worker roots under the frozen naming; normalized to `./pipeline/finetuned-smoke` → `finetuned-smoke-mgpu-w{0,1}`).
- **Validation additions beyond the listed rows**, all collect-all and consistent with the discipline: `--dry-run`+`--merge` conflict refusal, malformed failures-file refusal, cell output_dir outside its worker root refusal (validation-time, before any copy).

**Total deviations:** 0 auto-fixed. **Impact:** plan executed as written; the recorded details are design clarifications inside the plan's own latitude.

## Issues Encountered

None. (Two lint findings — I001 import order, RUF059 unused unpack — were caught and fixed inside Task 2 before its commit, normal iteration.)

## Known Stubs

None. No placeholder data, no skipped tests, no unrun `<verify>` steps (module lanes ran per task; the full gate ran once at plan end, green).

## Threat Mitigations Landed

| Threat | Mitigation | Proof |
|--------|------------|-------|
| T-12-04-01 artifact corruption during merge | per-file SHA256 source-vs-destination; any mismatch refuses before the merged manifests land | `test_copy_verified_unit_detects_corruption`, `test_merge_refuses_on_hash_mismatch_without_manifests` |
| T-12-04-02 unequal lane flags silently merged | lane-equality collect-all diagnostic listing per-root values per flag | `test_merge_refuses_unequal_peft_lane`, `test_merge_refuses_unequal_num_train_epochs_lane` |
| T-12-04-03 merged cells pointing at deleted worker roots | boundary-guarded output_dir prefix rewrite, manifest cells + failures | happy-path per-cell suffix assertions; the 4 `_rewrite_output_dir` unit rows incl. the sibling-prefix guard |
| T-12-04-04 checkpoint/resume pollution of the merged root | MERGE_ALLOWLIST default scope; strays absent; hatch opt-in | happy-path stray-absence assertions + `test_merge_include_checkpoints_hatch_copies_strays` |
| T-12-04-05 merge mutating worker roots | copy-only semantics; byte+mtime snapshot across default AND hatch merges | `test_merge_leaves_worker_roots_immutable` |
| T-12-04-SC package installs | zero packages (hashlib/shutil stdlib); empty pyproject/uv.lock diff | `git diff --stat` over the plan range |

## The 9-Step N=2 Multi-GPU Smoke Procedure (maintainer runbook — OTHER machine, D-05)

> Maintainer-executed on the multi-GPU validation machine, never CI, never GB10. Bounded: 2 models × 1 task × 1 seed × 1 epoch ≈ minutes. Full copy with commands and expected checks: `docs/multi-gpu.md` §"The 9-step N=2 multi-GPU smoke procedure". Record all output in the phase VERIFICATION/UAT artifact; **WINDOWS.md entry #21 tracks this pending run**.

0. 前置：目标机已装 dnallm/torch/cuda；数据集就位（iDNA_ABF_datasets__5mC）。
1. 干跑枚举不相交性（无 GPU）：`run_sweep_shard.py --dry-run --workers 2 --models plant-dnabert-6mer,<second-smallest> --tasks iDNA_ABF_datasets__5mC --seeds 42 --num_train_epochs 1 --output-root ./pipeline/finetuned-smoke` → 两 worker manifest 模型集不相交、并集 == 请求集。
2. 启动：同一命令去掉 `--dry-run` → 2 个 run_sweep 进程，CUDA_VISIBLE_DEVICES=0/1，每 worker 1 模型；tee 日志 `{root}-mgpu-w{0,1}.log`。
3. TUI 视图：`make tui` → 槽 5 `[a]` 附加两个 worker 根 → 发现列表 2 行，Enter 切换，进度/ETA 独立（D-01/SC2）。
4. 隔离证明：促使/等待一个 worker cell 失败 → 另一 worker 不受影响继续；orchestrator 聚合 verdict 表列出两 worker。
5. 失败重跑（仅 w1 根被写，w0 mtime 不变）：`run_sweep.py --from-failures pipeline/finetuned-smoke-mgpu-w1/sweep_failures.json --output-root pipeline/finetuned-smoke-mgpu-w1 --seeds 42 --num_train_epochs 1` → marker-skip：已完成 cell 显示 skipped（lane 与原 launch 一致）。
6. 合并：`run_sweep_shard.py --merge --workers 2 --output-root ./pipeline/finetuned-smoke` → SHA256 校验输出；合并 manifest cells = 两 worker 之和。
7. 镜像：`gen_progress.py` 先两 worker 根（2 sweeps）再合并根单独再生（1 sweeps）对比；绝不同时传两类根；`python3 -m http.server 8080` 查看 progress.html。
8. 数据链冒烟：`export_runs.py --input-root pipeline/finetuned-smoke ...` → 合并根可导出，与 worker 分别导出的并集一致。
9. 清理：确认合并根校验通过后 `rm -rf pipeline/finetuned-smoke-mgpu-w{0,1}{,.log}`；全部输出记录到相位 VERIFICATION。

## What 12-05 / Verification Can Now Assume

- **12-05** (MGPU-01/02/03 close-out + WEB-01/TEST-01 verification): both requirement IDs MGPU-02/MGPU-03 are co-declared — the shared-ID gate holds REQUIREMENTS.md open until 12-05's SUMMARY lands. The merge + doc deliverables are pinned by 39 tier-1 tests; the doc's topic coverage is grep-pinned; the maintainer smoke (WINDOWS #21) is the only open MGPU evidence item.
- The merged root is a first-class consumer root: `export_runs --input-root <merged>`, `sweep_monitor` attach, and `gen_progress <merged>` all verified against the merged shape.
- run_sweep.py stays untouched; the orchestrator's flag surface is now final for the milestone (`--workers/--gpus/--models/--output-root/--dry-run/--merge/--include-checkpoints`).

## Self-Check: PASSED

Files found: pipeline/run_sweep_shard.py, tests/test_sweep_shard.py, docs/multi-gpu.md, README.md, evidence/12-04-task1-red.json. Commits eda9153, e6e1328, 278a21e, 22a490d are ancestors of HEAD. Measured commit count 4 matches the ledger (6de1afc..HEAD).

---
*Phase: 12-multi-gpu-orchestration-console-hardening*
*Completed: 2026-10-13*
