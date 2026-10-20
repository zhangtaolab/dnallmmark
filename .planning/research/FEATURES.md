# Features Research

**Domain:** Multi-GPU sweep orchestration, TUI operator console, leaderboard visualization
**Researched:** 2026-10-20
**Confidence:** HIGH (behavioral norms from orchestrator/leaderboard ecosystems; v1.3 scope from maintainer rulings recorded 2026-10-20)

## Feature Categories

### 1. Dynamic Multi-GPU Dispatch (orchestrator)

**Table stakes** (any work-queue orchestrator has these):
- Cell-granular work queue: (model×dataset×seed) cells enumerated once, dispatched to idle GPU workers — the benchmark matrix is embarrassingly parallel (59 models × 50 datasets × 3 seeds)
- Per-worker GPU pinning (`CUDA_VISIBLE_DEVICES`) — already exists from static sharding
- Exactly-one-owner guarantee: a cell runs on exactly one GPU at any moment; never split across GPUs (maintainer: 不要用一个任务在多块卡上跑)
- Crash isolation: one worker's cell failure never kills siblings; failed cells recorded for re-run
- Resume safety: completed cells never re-run (today via `trainer_state.json` marker-skip — semantics must survive dynamic assignment)
- Deterministic enumeration: same inputs → same cell set (dry-run parity, byte-determinism discipline)

**Differentiators** (what makes this repo's version good):
- Live orchestrator-level aggregate view: per-worker/per-GPU progress, in-flight cell, failures — terminal table AND a machine-readable state file the TUI/web mirror consume (maintainer-selected)
- Cross-worker failure re-run: one command re-runs the union of failed cells across workers with lane flags threaded (overturns v1.2's deliberate no-convenience-flag decision — maintainer-selected)
- Merge-then-verify-then-clean helper: post-merge artifact verification + explicit cleanup of worker roots (today: manual `rm -rf` recipe in docs)
- Zero-dependency, single-process dispatcher: no daemon, no ports, no coordination service

**Anti-features:**
- DDP / torch-run data-splitting (decided out — v1.2 D-04 re-affirmed)
- Cost-prediction load balancing (maintainer explicitly rejected estimation; dynamic dispatch makes it unnecessary)
- Cloud/remote orchestration, multi-node (single-box scope)

### 2. N=2 Validation (smoke + small real sweep)

**Table stakes:**
- The 9-step N=2 smoke procedure from `docs/multi-gpu.md`, executed on the local 2×5090 (closes WINDOWS #21; revises D-05)
- A small real sweep exercising dispatch→merge→data-chain end-to-end with real training

**Differentiators:**
- Pre-materialized 5% sub-datasets: deterministic, **stratified** subsets of the real datasets as first-class dataset directories (maintainer: 小数据集需要提前生产), with **their own config/registry** carrying their own row counts (与真实数据使用不同的配置文件 — never mixed)
- Honest reconciliation: subset entries carry measured counts so n_audit-style checks stay meaningful

**Anti-features:**
- Runtime-only subsetting for the validation sweep (rejected — pre-materialized artifacts are the point)
- Full E2' re-run in v1.3 (stays maintainer dual-gated, out of this milestone)

### 3. TUI Multi-GPU Surface

**Table stakes:**
- Multi-GPU launch from slot 4 (workers/gpus), respecting the existing gate chain (env gate → problems → confirm → E2' typed phrase when applicable); single-GPU serial gate (261015-ehc) revised rather than bypassed
- Monitor renders multi-GPU runs natively (partially exists: mgpu-w sibling grouping from 261018-kvj)

**Differentiators:**
- G GPU-lanes display: per-GPU utilization/memory/temperature lanes (nvidia-smi read-only probe; v1.2 deferred item whose stated trigger is exactly this milestone)
- Live consumption of the orchestrator state file (dispatch queue depth, per-worker in-flight cell)

**Anti-features:**
- TUI-side re-implementation of dispatch logic (TUI orchestrates, never computes — binding constraint)
- GPU control actions (no kill/reset of GPUs; read-only probe)

### 4. Web Multi-Seed Error Bars

**Table stakes:**
- Mean±std (or CI) rendered for multi-seed results wherever the point estimate is shown
- Zero methodology drift: ranking/normalization math untouched; existing numbers byte-identical when error fields are absent (zero-drift gate stays green)

**Differentiators:**
- Scatter chart (FLOPs-vs-rank): vertical/horizontal whiskers via vendored inline plugin
- Task bar chart: native floating bars; error-bar whiskers via the same plugin
- Per-dataset metric tables gain a ±std column where space allows

**Anti-features:**
- New CDN dependency by default (vendored plugin; sgratzl plugin only as ratified fallback)
- Changing aggregation/ranking semantics to "error-aware" versions (display-only)

## Complexity Notes

| Feature | Complexity | Dependencies |
|---------|-----------|--------------|
| Dynamic dispatch core + resume redesign | High | None (rework of run_sweep_shard internals; output-root/resume semantics is the risk) |
| Orchestrator live view | Medium | Depends on dispatch core (state file written by dispatcher) |
| Failure re-run + cleanup helper | Low-Medium | Depends on dispatch core (failure ledger) |
| 5% subset generator + separate config | Medium | None (deterministic stratified sampling; registry schema reuse) |
| N=2 smoke + small sweep | Medium (GPU time) | Dispatch core; subset generator |
| TUI launch + monitor + G lanes | Medium | Dispatch core state file; nvidia-smi probe |
| Web error bars | Medium | Aggregation std emission + JSON schema (additive) + Chart.js plugin |

## Sources

- Repo: `docs/multi-gpu.md` (Phase 12 decision record), `.planning/PROJECT.md` v1.3 Current Milestone + Key Decisions (maintainer rulings 2026-10-20)
- Externals: sgratzl/chartjs-chart-error-bars (Chart.js 3/4 error-bar chart types), HandsOnDataViz Chart.js error-bars template (custom `afterDatasetsDraw` idiom)
