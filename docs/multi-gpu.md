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
| What accelerates | Multi-model sweeps: the 59-model benchmark matrix is embarrassingly parallel — every (model × task × seed) cell is an independent fine-tune | A single large model: one cell's batch split across GPUs |
| Code coupling | Zero. Each worker is an ordinary `run_sweep.py --models <shard> --output-root <worker root>` invocation; nothing inside the pipeline knows sharding exists | Real. `run_finetune.py` already carries the scaffolding — `num_gpus = int(os.environ.get("WORLD_SIZE", "1"))` (`pipeline/run_finetune.py:1450`) and `local_rank = int(os.environ.get("LOCAL_RANK", "0"))` (`:1635`) — but data-splitting launch orchestration (a torch-run wrapper that shards the dataset and sets the rank env) is **deferred out of this milestone by decision** (12-CONTEXT deferred list: DDP 实装 → 决策文档落地即交付，实装非本里程碑) |
| Coverage | Every model in the registry, custom entries included (customs shard with weight 0.0 when their `size (M)` is unusable) | Would apply per-cell to any single model, including the frontier models |
| Cost / honest limits | Per-model load imbalance: shards are weighted by the registry's `size (M)` only (assumption A1 — every worker runs the same task set, so model size dominates the differential; per-task dataset variance is ignored) | Splitting one cell's data changes the effective batch/step math and adds a distributed-launch failure surface; none of it is exercised by the current pipeline |
| Concurrency guarantee | Disjointness by construction: each worker writes only under its own `{root}-mgpu-w{i}` root, so no path is ever shared; `trainer_state.json` marker-skip is the only resume guard needed (D-06) | Requires a distributed process group; out of scope here |

**适用场景 (when to use which):**

- 59-model sweep throughput, benchmark production, any multi-model run →
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
`{output-root}-mgpu-w{i}-{launch-stamp}.log` — one log file per launch
(the launcher's tee idiom, WR-02: a resume relaunch never truncates the
prior launch's crash log). Sibling roots are a hard invariant (two
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
  an explicit, verified maintainer step — since Phase 14 (MGPU-05) the
  `--cleanup` command replaces the old manual `rm -rf` recipe: it
  re-verifies the merged root first (an `export_runs.py --dry-run`
  subprocess AND manifest cell-set equality against the worker
  manifests), then removes exactly the frozen worker roots
  `{output-root}-mgpu-w{0..N-1}` and their per-launch logs, behind an
  exact typed phrase (the resolved `--output-root` string, D14-11):
  ```bash
  python pipeline/run_sweep_shard.py --cleanup --workers 2 \
      --output-root ./pipeline/finetuned \
      --yes /abs/resolved/pipeline/finetuned
  ```
  **Dispatch roots need neither `--merge` nor `--cleanup`** — dispatch
  mode writes ONE shared root (MGPU-06); both commands refuse with a
  named error before touching anything (A6, D14-11/D14-12).

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

## Machine roles (D-05, revised 2026-10-20: 本机 = 双卡验证机)

> 机器分工（修订，D15-03）：**本机 = 双卡验证机**——AutoDL 2× RTX 5090
> 直接执行 N=2 调度冒烟与小规模真实 sweep；旧「开发本机 / 验证交给另一台
> 机器」的两机分工就此退役（该分工定于本机单卡时期）。CI 永远不假设 N>1
> 设备：多 GPU 证据来自本机实跑工件，CI 只对 fixture 生成的工件做断言
> （D15-15）。

Multi-GPU *development* and *validation* both happen on the local box
(CPU-side test suites plus real dispatch runs on the two 5090s — the
smoke procedure below was executed on this machine 2026-10-20; evidence
in `.planning/phases/15-dual-gpu-validation-subsets/15-01-SUMMARY.md`).
CI stays zero-GPU: there is no multi-GPU CI lane and there will not be
one — GPU-outcome assertions read real produced artifacts on this box
and fixture-generated artifacts in CI (D15-15).

## The E2' trust boundary, stated honestly (Pitfall 7)

The full-E2' typed-phrase gate is a **TUI-composed-path structural
feature** — it exists because the TUI's launch pipeline composes and
inspects the sweep before spawning it. The CLI has no such gate today,
by design: `run_sweep.py` is, and `run_sweep_shard.py` remains, **the
maintainer trust surface** — an operator at a shell typing a command is
trusted the same way an operator typing `git push` is. Do not project
E2' expectations onto the CLI, and do not add gate code to it; the
bounded smoke procedure below uses small explicit combos anyway.

## The dispatch-mode N=2 smoke procedure (executed on this machine)

**Executor-executed on the local 2× RTX 5090 box (D-05 revised: 本机=双卡验证机).
Bounded: 1 model × 1 task × 2 seeds × 1 epoch ≈ 2.5 min wall. Never CI.**
This section is written FROM the executed commands (D15-02
procedure/doc identity): every argv and output line below is a
copy-paste of the 2026-10-20 run. Dispatch mode (`--mode dispatch`,
Phase 13) is the primary multi-GPU mode; the static-shard runbook above
stays valid for the coexisting `--mode static` (the full dispatch-first
docs pass is Phase 18, DOCS-01).

为什么是 2 个 cell（种子 42,43）：D15-02 要求两块卡**各自**产出 cell
工件——1 模型 × 1 任务 × 1 种子 = 1 cell 会让 worker 1 拿到空队列直接退出，
"both GPUs produced cell artifacts" 不可判定（Pitfall 2）。组合选 registry
里最小且 Phase 11 有界冒烟已证明的配对：plant-dnabert-6mer ×
iDNA_ABF_datasets__5mC（全量 2110/234/2344 行——冒烟不依赖任何子集机制）。

**0. 前置（D15-14）：** dnallm editable 在位（`.venv/bin/python -m pip show
dnallm` 必须给出 `Editable project location: /root/autodl-tmp/Github/DNALLM`）；
`nvidia-smi` 两卡 0% 利用率；模型/数据集已就位（modelscope 官方通道下载，
`config.json` 直接落在模型目录、train/dev/test 行数与 registry 逐行核对
2110/234/2344——T-15-01）。

**1. 启动（ONE shared root；显式绝对 `--output-root`/`--log_dir`）：**
子进程 cwd 钉在 `pipeline/`，裸相对 root 会在 sweep 层与 child 层解析到不同
位置；显式 root 同时防止 `directories.json` 把真实 output_root/log_dir 播种
进冒烟（Pitfall 4）。本机 HF 不可达——资产全部本地，离线变量防止加载时
网络请求挂死：

```bash
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
.venv/bin/python pipeline/run_sweep_shard.py --mode dispatch --workers 2 --gpus 0,1 \
    --models plant-dnabert-6mer --tasks iDNA_ABF_datasets__5mC --seeds 42,43 \
    --num_train_epochs 1 \
    --output-root "$(pwd)/pipeline/finetuned-smoke-r2" \
    --log_dir "$(pwd)/pipeline/finetuned-smoke-r2/logs"
```

实跑关键输出（155 s wall，exit 0；dispatcher stdout 就是 live view，
status vocabulary running/done/incomplete——D15-10；日志路径缩写为 `...`）：

```text
[Dispatch] status=running queue=0 done=0/2 failed=0 skipped=0
  w0 gpu=0: plant-dnabert-6mer/iDNA_ABF_datasets__5mC/seed_42
  w1 gpu=1: plant-dnabert-6mer/iDNA_ABF_datasets__5mC/seed_43
...
Dispatch verdicts:
  worker 0: cells=1 completed=1 failed=0 gpu=0 log=.../finetuned-smoke-r2-dispatch-w0-20261020_232000.log
  worker 1: cells=1 completed=1 failed=0 gpu=1 log=.../finetuned-smoke-r2-dispatch-w1-20261020_232000.log
[Dispatch] status=done queue=0 done=2/2 failed=0 skipped=0
[Dispatch] 2/2 cell(s) completed, 0 failed, 0 skipped; state: .../finetuned-smoke-r2/dispatch_state.json
```

`w0 gpu=0: .../seed_42` 与 `w1 gpu=1: .../seed_43` 两行就是 D15-02
"both GPUs produced cell artifacts" 的 live 证据（ledger 里两个 claim 各自
记录 gpu token 0/1）。

**2. 终态判定：** `dispatch_state.json` 必须 `status == "done"` 且
`counts.completed == counts.total == 2`；两个 cell 目录各含 4 件工件
（`run_record.json` 由 dispatch_core 在 claim finalize 时写入——15-04 起，
run_sweep 记录形状、WR-12 不覆写）：

```bash
.venv/bin/python -c "import json; s = json.load(open('pipeline/finetuned-smoke-r2/dispatch_state.json')); assert s['status'] == 'done', s['status']; assert s['counts']['completed'] == s['counts']['total'] == 2, s['counts']"

for c in 42 43; do for f in final_metrics.json flops_report.json trainer_state.json run_record.json; do
  test -f "pipeline/finetuned-smoke-r2/plant-dnabert-6mer/iDNA_ABF_datasets__5mC/seed_${c}/${f}" || echo "MISSING seed_${c}/${f}"; done; done
```

**3. 消费 dry-run（D15-02 merged-root 判定的 dispatch 形态——shared root
即 merged root，无需 merge，MGPU-06）：**

```bash
.venv/bin/python script/export_runs.py --dry-run --input-root pipeline/finetuned-smoke-r2
# → [Dry-run] 2 run record(s) across 1 model(s) / 1 task(s) under pipeline/finetuned-smoke-r2
```

**4. Dispatch-root 边界（A6/MGPU-06）：** 不要传 `--merge` 或 `--cleanup`——
dispatch 模式只写一个共享根，两者都按设计拒绝（named error）。失败 cell 的
重跑走 `--rerun-failed`（Phase 14，账本 feed + archive genealogy）。复跑全量
冒烟请换一个新 root——已有 cell 的 `trainer_state.json` 标记会让 dispatch 按
恢复语义跳过它们（本节命令的 `-r2` 后缀正是这个原因；`finetuned-smoke*/`
整族已 gitignore）。

**5. 隔离断言（T-15-02）：** 冒烟 root 必须区别于 `directories.json` 的
`output_root`（真实根 `/root/autodl-tmp/dnallmmark-data/finetuned` ≠ 冒烟根
`pipeline/finetuned-smoke-r2`）；显式 `--output-root`/`--log_dir` 已在命令里
强制成立，committed `dnallm-mark/data/` 永远不是冒烟目标。

每一步的期望输出都是判定标准：输出不匹配就是 finding，不是
rerun-and-hope（D15-04：失败即停，保留 `dispatch_state.json` 与 tee 日志
作为相位工件，转入正常修复流程）。
