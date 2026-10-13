# Multi-GPU Sweep Orchestration

This document is the single decision record for running the DNALLM-Mark
sweep on more than one GPU (D-04, requirement MGPU-03): **when to shard
models across GPUs vs when DDP is the right tool**, the CLI runbook for
the orchestrator (`pipeline/run_sweep_shard.py`), and the bounded smoke
procedure that validates a multi-GPU machine. Every command is
copy-paste; every claim names the code that implements it.

The orchestration CLI is deliberately the ONLY multi-GPU entry: the TUI
composes single sweeps (D-01), `run_sweep.py` and `run_finetune.py` are
byte-untouched by the orchestration work (their argv surfaces are frozen
by the tier-1 suite and the TUI composer), and the orchestrator composes
ordinary `run_sweep.py` invocations — one per GPU — under frozen sibling
output roots.

## The decision: model sharding vs DDP

| | **Model sharding** (this repo, today) | **DDP / torch-run** (future) |
|---|---|---|
| What accelerates | Multi-model sweeps: the 62-model benchmark matrix is embarrassingly parallel — every (model × task × seed) cell is an independent fine-tune | A single large model: one cell's batch split across GPUs |
| Code coupling | Zero. Each worker is an ordinary `run_sweep.py --models <shard> --output-root <worker root>` invocation; nothing inside the pipeline knows sharding exists | Real. `run_finetune.py` already carries the scaffolding — `num_gpus = int(os.environ.get("WORLD_SIZE", "1"))` (`pipeline/run_finetune.py:1357`) and `local_rank = int(os.environ.get("LOCAL_RANK", "0"))` (`:1542`) — but data-splitting launch orchestration (a torch-run wrapper that shards the dataset and sets the rank env) is **deferred out of this milestone by decision** (12-CONTEXT deferred list: DDP 实装 → 决策文档落地即交付，实装非本里程碑) |
| Coverage | Every model in the registry, custom entries included (customs shard with weight 0.0 when their `size (M)` is unusable) | Would apply per-cell to any single model, including the frontier models |
| Cost / honest limits | Per-model load imbalance: shards are weighted by the registry's `size (M)` only (assumption A1 — every worker runs the same task set, so model size dominates the differential; per-task dataset variance is ignored) | Splitting one cell's data changes the effective batch/step math and adds a distributed-launch failure surface; none of it is exercised by the current pipeline |
| Concurrency guarantee | Disjointness by construction: each worker writes only under its own `{root}-mgpu-w{i}` root, so no path is ever shared; `trainer_state.json` marker-skip is the only resume guard needed (D-06) | Requires a distributed process group; out of scope here |

**适用场景 (when to use which):**

- 62-model sweep throughput, benchmark production, any multi-model run →
  **model sharding** (this phase's deliverable).
- Single-model frontier scaling (one very large model, one task) →
  **DDP, future work**. The child's `WORLD_SIZE`/`LOCAL_RANK` scaffolding
  is the seam a future torch-run wrapper would drive; until that wrapper
  exists, a single large model runs on one GPU under the ordinary sweep.

The matrix above closes the DDP question by *deciding* it: sharding is
the supported multi-GPU mode of this milestone; DDP implementation is
deferred with the seam documented, not silently missing.

## CLI runbook

All commands run from the repository root. Frozen naming (one authority,
`run_sweep_shard.worker_root()`): worker i writes under
`{output-root}-mgpu-w{i}` with its tee log at
`{output-root}-mgpu-w{i}.log` — sibling roots are a hard invariant (two
workers on one root would collide last-writer-wins over the root-level
`sweep_manifest.json` / `sweep_failures.json`).

### 1. Launch — dry-run first, always

```bash
# (a) Dry-run: enumerate the shards, write ONLY the per-worker planned
#     manifests — no GPU, no subprocess; verify the partition first
python pipeline/run_sweep_shard.py --dry-run --workers 2 \
    --models plant-dnabert-6mer,GENERanno-eukaryote-0.5b-base \
    --tasks GUE__emp_H3 --seeds 42,43,44 --num_train_epochs 1 \
    --output-root ./pipeline/finetuned

# (b) Real launch: same command minus --dry-run; one run_sweep.py worker
#     per GPU, CUDA_VISIBLE_DEVICES pinned per worker (default 0..N-1,
#     override with --gpus "0,1" — operator-owned strings, arity-checked)
python pipeline/run_sweep_shard.py --workers 2 \
    --models plant-dnabert-6mer,GENERanno-eukaryote-0.5b-base \
    --tasks GUE__emp_H3 --seeds 42,43,44 --num_train_epochs 1 \
    --output-root ./pipeline/finetuned
```

The orchestrator owns five launch flags (`--workers`, `--gpus`,
`--models`, `--output-root`, `--dry-run`); every other token
(`--tasks`, `--seeds`, `--peft`, `--num_train_epochs`,
`--registry-dir`, ...) passes through VERBATIM to every worker —
`run_sweep.py` stays the single owner of sweep-flag validation. Models
are LPT-sharded by the registry's `size (M)` (largest first, least-loaded
worker next). The orchestrator waits for ALL workers and exits 0 iff
every worker exited 0, printing a per-worker verdict table.

**Load-balancing override (A1 honesty note):** the shard weights are a
static size proxy. When you know better (a small model on a huge
dataset outcosts a big model on a tiny one), rebalance manually: run the
orchestrator twice with hand-picked `--models` subsets, or run one
`run_sweep.py` per GPU directly with your own split — `--models` is the
manual override, and per-worker roots keep the runs mergeable either
way.

### 2. Watch the workers (zero new screens, D-01)

Each worker is an independent output root, so the TUI's monitor (slot 5)
renders N rows natively: `make tui`, then `[a]`-attach each worker root
once (`pipeline/finetuned-mgpu-w0`, `pipeline/finetuned-mgpu-w1`, ... —
persisted across sessions). Enter on a row switches to that worker's
per-worker progress/ETA view.

### 3. Stopping workers — the killpg recipe (Ctrl-C semantics)

Workers are spawned with `start_new_session=True`: each worker is its
own process group, so **Ctrl-C on the orchestrator does NOT kill the
workers** (by design — they are resume-safe via the per-cell
`trainer_state.json` marker; an accidental terminal close must not burn
GPU-hours). To stop ONE worker, signal its whole process group so its
`run_finetune.py` children die with it:

```bash
kill -TERM -$(ps -o pgid= -p <worker pid> | tr -d ' ')
```

(The TUI's exit prompt cannot kill CLI-launched workers either — its
registry only holds processes the TUI itself spawned.)

### 4. Isolated failure re-run (D-08 — one line, per worker)

A failed worker's cells are re-run over ITS root only; healthy workers'
roots are never touched. The command is an ordinary `run_sweep.py`
invocation of the `--from-failures` filter — there is deliberately NO
orchestrator convenience flag for this (the command is already one line,
and a wrapper would add argv surface for nothing):

```bash
python pipeline/run_sweep.py \
    --from-failures pipeline/finetuned-mgpu-w1/sweep_failures.json \
    --output-root pipeline/finetuned-mgpu-w1 \
    --seeds 42,43,44 --num_train_epochs 1
# ...plus the SAME lane flags as the original launch
```

**The lane must match the original sweep** (`--peft`,
`--config-variant`, `--num_train_epochs`, ...): re-running a lora
worker's failures without `--peft lora` enumerates the BASE cells — a
different experiment, not a recovery. Completed cells inside the re-run
are skipped by the seed-scoped marker, so the re-run attempts exactly
the failed cells.

### 5. Merge (D-09 — copy + SHA256-verify, never a link, never a move)

After all workers finish, union their frozen roots into ONE consumer
root that `script/export_runs.py`, the monitor, and the web mirror all
read unchanged:

```bash
python pipeline/run_sweep_shard.py --merge --workers 2 \
    --output-root ./pipeline/finetuned
```

- Copies each cell's **data artifacts** (`run_record.json`,
  `final_metrics.json`, `trainer_state.json`, `seed_result.json`,
  `flops_report.json`, plus `frac_*/` children for curve cells) with
  per-file SHA256 verification (hash, copy, re-hash, compare); ANY
  mismatch refuses the whole merge before the merged manifests land.
- Excludes `checkpoint-*/` and `runs/` by default (resume state; nobody
  re-runs the merged root). Escape hatch: `--include-checkpoints`.
- Writes the union `sweep_manifest.json` / `sweep_failures.json` with
  every `output_dir` rewritten onto the merged root, and refuses if the
  workers' lane flags differ (a lora worker merged with a base worker is
  a different experiment than either).
- **Never mutates a worker root and never deletes anything.** Cleanup is
  an explicit maintainer step: after verifying the merged root (export a
  model from it, check the manifest), delete the worker roots and logs:
  `rm -rf pipeline/finetuned-mgpu-w{0,1}{,.log}`

### 6. Web mirror (offline regeneration, never both roots)

```bash
uv run --group tui --group dev python script/gen_progress.py \
    pipeline/finetuned-mgpu-w0 pipeline/finetuned-mgpu-w1 \
    --output dnallm-mark/data/progress/sweep.json
# live view: every worker root -> N sweeps in the page's selector

uv run --group tui --group dev python script/gen_progress.py \
    pipeline/finetuned \
    --output dnallm-mark/data/progress/sweep.json
# post-run view: the MERGED root alone -> 1 sweep
```

**Never pass worker roots AND their merged root together** — every cell
would appear twice (double-counted sweeps in the selector view).

## Machine roles (D-05, verbatim)

> 机器分工：多 GPU 开发在本机、**验证在他机**——MGPU 冒烟写成他机执行程序文档（E2' 同模式）；本机仅 fake-executor/干跑枚举不相交性/单卡 CUDA_VISIBLE_DEVICES 语义证明；CI 与 GB10 不假设 N>1 设备。

Multi-GPU *development* happens on the local dev machine (CPU-side test
suites, dry-run disjointness proofs, single-GPU `CUDA_VISIBLE_DEVICES`
semantics). Multi-GPU *validation* runs on the other machine, as the
procedure below documents. CI and the local GB10 assume nothing about
N>1 devices — there is no multi-GPU CI lane and there will not be one.

## The E2' trust boundary, stated honestly (Pitfall 7)

The full-E2' typed-phrase gate is a **TUI-composed-path structural
feature** — it exists because the TUI's launch pipeline composes and
inspects the sweep before spawning it. The CLI has no such gate today,
by design: `run_sweep.py` is, and `run_sweep_shard.py` remains, **the
maintainer trust surface** — an operator at a shell typing a command is
trusted the same way an operator typing `git push` is. Do not project
E2' expectations onto the CLI, and do not add gate code to it; the
bounded smoke procedure below uses small explicit combos anyway.

## The 9-step N=2 multi-GPU smoke procedure

**Maintainer-executed, on the OTHER machine (D-05). Bounded: 2 models ×
1 task × 1 seed × 1 epoch ≈ minutes. Never CI, never GB10.** Record all
output in the phase VERIFICATION/UAT artifact.

He机多 GPU 冒烟（maintainer-executed，N=2，有界：2 模型 × 1 任务 × 1 种子 × 1 epoch；非 CI）：

```text
 0. 前置：目标机已装 dnallm/torch/cuda（uv run --group tui --group gpu 可启动）；数据集已就位
    （与 11 的 D-04 冒烟挑选同一最小组合：iDNA_ABF_datasets__5mC，2110/234/2344 行）。
 1. 干跑枚举不相交性（无 GPU）：
      python pipeline/run_sweep_shard.py --dry-run --workers 2 \
        --models plant-dnabert-6mer,<second-smallest-local-model> \
        --tasks iDNA_ABF_datasets__5mC --seeds 42 --num_train_epochs 1 \
        --output-root ./pipeline/finetuned-smoke
    → 检查两个 worker manifest（pipeline/finetuned-smoke-mgpu-w0/-w1）：
      模型集不相交、并集 == 请求集。（已知边界：dry-run 写入的 planned manifest 会让
      scanner 先 classify 该根 finished——真实启动后同根复写即正常。）
 2. 启动：同一命令去掉 --dry-run → 2 个 run_sweep 进程，CUDA_VISIBLE_DEVICES=0/1，
    每个 worker 1 个模型；tee 日志 {root}-mgpu-w{0,1}.log。
 3. TUI 视图：make tui → 槽 5 [a] 附加两个 worker 根（各一次，持久化）→ 发现列表 2 行
    （finetuned-smoke-mgpu-w0/-w1），Enter 切换视图，进度/ETA 独立（D-01/SC2 操作面证明）。
 4. 隔离证明：等待或促使一个 worker 的 cell 失败（或直接观察两 worker 完成时间差）→
    确认另一 worker 不受影响继续；orchestrator 退出码聚合表列出两 worker verdict。
 5. 失败重跑（仅 w1 根被写；w0 根 mtime 不变——touch 前后比对）：
      python pipeline/run_sweep.py \
        --from-failures pipeline/finetuned-smoke-mgpu-w1/sweep_failures.json \
        --output-root pipeline/finetuned-smoke-mgpu-w1 \
        --seeds 42 --num_train_epochs 1
    → marker-skip：已完成的 cell 显示 skipped，不重训（lane 与原 launch 一致）。
 6. 合并（数据工件复制 + SHA256 校验输出；合并 manifest cells = 两 worker 之和）：
      python pipeline/run_sweep_shard.py --merge --workers 2 \
        --output-root ./pipeline/finetuned-smoke
 7. 镜像（先两 worker 根看 2 sweeps，再合并根单独再生一次对比 1 sweep；绝不同时传两类根）：
      uv run --group tui --group dev python script/gen_progress.py \
        pipeline/finetuned-smoke-mgpu-w0 pipeline/finetuned-smoke-mgpu-w1 \
        --output dnallm-mark/data/progress/sweep.json
    → 本地静态服务（dnallm-mark/ 下 python3 -m http.server 8080）查看 progress.html。
 8. 数据链冒烟（合并根可导出，与 worker 分别导出的并集一致）：
      uv run --group data python script/export_runs.py \
        --input-root pipeline/finetuned-smoke ...
 9. 清理：确认合并根校验通过后删除 worker 根与日志
    （rm -rf pipeline/finetuned-smoke-mgpu-w{0,1}{,.log}）；记录全部输出到相位 VERIFICATION。
```

Every numbered step is a human-check with expected output; a step whose
output does not match is a finding, not a rerun-and-hope.
