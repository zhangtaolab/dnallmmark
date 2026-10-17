# Phase 7: Pipeline-Side Enablement (FlopsCounter Port, argv Threading & Registry Overlay) - Research

**Researched:** 2026-10-11
**Domain:** Brownfield pipeline instrumentation + CLI threading + registry overlay (Python 3.13, stdlib-first; torch only GPU-side)
**Confidence:** HIGH (every load-bearing claim verified by direct file inspection this session; no external packages introduced)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**FLOPs 启用与输出契约（PIPE-01）**
- **D-01:** FlopsCounter **always-on** —— 每个 run 自动挂钩并写报告，与旧管线行为一致，无额外旗标面（不设 `--flops`/`--no-flops`）。
- **D-02:** 输出走**独立 `flops_report.json`**，沿用 legacy 文件名与 schema（逐层明细 + `save_to_json` 外推总训练 FLOPs），落在每个 run 输出目录；**不动 `run_record.json` 现有测试契约**。
- **D-03:** **uncovered 架构层响亮报告**：钩子分派未命中的层归为 uncovered 并在报告中显式列出；uncovered 占比超阈值时控制台 WARNING。宁可噪声不可静默少计（正确性品牌纪律）。
- **D-04:** 移植完成后**删除 `pipeline/dnallmmark_pipeline.py`**（Phase 3 已废弃，git 历史即参考）。删除前需检查仓库内残留引用（docs/测试/注释）。
- **D-05（维护者 2026-10-11 中途补充）:** flops_report.json 新增 **hardware/runtime 节**：`gpu_device`（如 5090 / RTX6000 / 4090 / 5090D / 4090D，取 `torch.cuda.get_device_name()` 实报字符串，不做枚举映射）、`train_time`（训练时长）、`max_mem_gb`（显存峰值，现有 print 改落盘）。仅管线侧捕获；前端展示记 Deferred。— **Reversibility:** costly — flops_report schema 对外发布后，hardware 节字段名成为下游（monitor/排行榜）依赖契约。

**Overlay 激活机制（CUST-05）**
- **D-06:** **自动探测**：`~/.config/dnallmmark/custom_models.json` / `custom_datasets.json` 存在即加载；缺失 = 逐字节今日行为。不设显式开关旗标。
- **D-07:** 路径解析：默认 platformdirs（`~/.config/dnallmmark/`）；提供 **`DNALLMMARK_CUSTOM_REGISTRY_DIR` 单一 env var** 覆盖整个目录（测试注入 tmp_path + 非标准 home 环境）。
- **D-08:** **共享 loader 模块**（如 `pipeline/registry_loader.py`）：合并视图 + 官方键冲突 fail-fast（清晰报错）。run_finetune 模块级加载（`:674-679`）改走它但**导入时序不变**；run_sweep 三处（`:368/:474/:514`）与 audit（`script/audit_n_frequencies.py:599`）全部改走它（D-10 单源先例）。
- **D-09:** **不动 `script/export_runs.py`**（已核实运行时不加载注册表，只读 run artifacts；自定义条目经 run 自然流入导出）。Phase 7 overlay 触点 = run_sweep ×3 + run_finetune ×1（两文件一次加载）+ audit ×1。

**argv 透传语义（PIPE-02）**
- **D-10（open Q7 裁决）:** auto-GA = **乘积语义**：`GA = max(1, effective_batch // bs_new)`，与现有 `run_finetune.py --effective_batch_size`（`:167/:1300-1310`）完全一致；`bs_new` 为动态缩放后的实际 per-device batch。**不是**"覆盖全训练集"语义（N//batch 的 N 指有效批量目标值，非训练行数）。
- **D-11:** sweep 层旗标**沿用下划线名 `--effective_batch_size`**（与仓库 `--target_model`/`--train_fraction` 风格一致，零别名映射）。
- **D-12:** **裸旗标=16、缺席=不改**：argparse `nargs='?'` `const=16`；完全缺席 = 不透传给子进程 = 逐字节今日行为（YAML GA 生效）。"默认 16" 由此落地。
- **D-13:** `sweep_manifest.json` cell **在场才记**：四旗标在场时增记对应字段（如 `effective_batch_size: 16`）；缺席时字段不出现，保持字节确定性（现有 manifest 字节确定性测试不动）。
- **D-14:** `--subset_file` 在 **sweep 层预校验**：启动前校验（键在注册表内、结构合法），问题一次性全列出后 exit 非零（与 unknown-filter fail-fast 纪律一致）；不是放给子进程逐 cell 报错。
- **D-15:** `--cache_dir` / `--subset_file` sweep 层**先转绝对路径再透传**（与 `--output_dir` 绝对路径纪律一致；子进程 cwd 钉在 pipeline/）。
- **D-16:** `--num_train_epochs` 优先级**确认现有语义**：旗标覆盖 config（`run_finetune.py:950` 已文档化）；sweep 纯透传不重复裁决。

**容错 loader 契约（PIPE-03）**
- **D-17:** **解析级容错**：覆盖 OSError（缺失/不可读）、`json.JSONDecodeError`、空文件；结构有效但缺字段的 JSON **不算损坏**（键级检查归调用方）。
- **D-18:** **无状态 + 哨兵**：loader 损坏时返回 None（或抛特定异常），调用方保留自己的 last-known-good；loader 不内置缓存（可测性、多进程安全）。
- **D-19:** 落点 **`pipeline/artifact_loader.py`**（纯函数、零重依赖）；Phase 8 `tui/services/` import 它（依赖方向 tui→pipeline，与研究结论一致）。
- **D-20:** Phase 7 loader **仅覆盖 flops_report.json 读取**（契约测试锁定）；run_sweep 现有两处容错读取（`:537-540`/`:1107-1109`）**不动**（surgical 纪律，WR-11 测试已锁）；Phase 11 monitor 接入时再评估替换。

**验证深度（含纪律变更）**
- **D-21（维护者 2026-10-11 裁定）:** **code-only 限制取消，现在可以用 GPU** —— 有界 GPU 运行/smoke 作为普通计划步骤无需中途再授权；**E2' 全量三种子 sweep 仍维护者双门**；CI 仍无 GPU/dnallm。长期记忆已更新。
- **D-22:** Phase 7 含 **GB10 FLOPs smoke**：单常规架构模型（BERT 系最小最快）×1 任务×1 种子×1 epoch；exotic 架构（Mamba/Hyena/evo2 等）靠 CPU stub 单测锁分派逻辑。
- **D-23:** smoke 过门判定 = **发射+合理性**：flops_report.json 成功落盘、主层钩子命中、uncovered 低于阈值、FLOPs 数量级 sane（与参数量×token 数粗估同阶）；**无 legacy 逐位对账**（架构/配置链已漂移，对账含义有限）。
- **D-24:** **executor 执行** smoke（本机即 GB10，[gpu] venv + dnallm 1.2.1 已就绪并经 Phase 6 四次 smoke 验证）；计划里显式标注 GPU 步骤。

**smoke 产物与 schema 契约**
- **D-25:** smoke 为**计划内步骤**（命令+预期输出写进 PLAN，执行后贴实录留证）；不做常驻 make 目标。
- **D-26:** 测试用**合成 flops_report fixture**（CPU 确定性生成）；真跑产物**不入库**（机器相关），计划执行记录贴关键字段摘要。
- **D-27:** `flops_report.json` 上**严格 JSON Schema**（`schemas/flops_report.json`，与 Phase 2 既有 schema 纪律对齐）+ 顶层 **`schema_version: 1` 字段留演进余地 + 合成 fixture 校验测试；hardware 节为可选节。— **Reversibility:** one-way — schema 一旦发布即为对外契约（v1 字段名与结构被 monitor/排行榜消费）。

### Claude's Discretion
- FlopsCounter 新模块的具体文件名与内部结构（前提：torch 延迟导入/stub 可测、run_finetune 集成点最小侵入）
- registry_loader / artifact_loader 的函数签名与异常类型设计
- uncovered 阈值的具体数值（建议从 legacy 行为推导，给 planner 留白）
- D-04 删除旧文件时对残留引用的清理范围（docs/注释同步更新）
- smoke 具体选哪个注册表模型（"最小可跑 + 分钟级"原则）

### Deferred Ideas (OUT OF SCOPE)
- **榜单/前端展示训练平台（GPU 型号）列与训练时间列** —— 展示层工作，牵动 leaderboard schema/goldens/前端多页面，超出 Phase 7 边界；未来单独安排（届时 flops_report/数据链的 hardware 数据已就位）

None — discussion stayed within phase scope (除上条维护者补充的展示侧延伸)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PIPE-01 | FlopsCounter 移植：旧 dnallmmark_pipeline.py 的 20+ 架构前向钩子移植到 run_finetune.py（早于监控阶段；喂 E2' FLOPs 正确性与排行榜效率轴） | Legacy class fully mapped (`:43-708`), calibration-pass call pattern mapped (`:1072-1157`), target integration slot identified (`run_finetune.py` between `:1423` and `:1425`), CPU-stub test mechanism designed (Pattern 1) |
| PIPE-02 | run_sweep argv 透传四项：--subset_file、--effective_batch_size（auto-GA：GA=max(1, N//batch_size)，默认 16）、--num_train_epochs、--cache_dir | All four child flags verified present on run_finetune.py; build_argv LIST-append precedent verified; GA semantics verified verbatim at `run_finetune.py:1302-1311`; test harness shape mapped (`flag_value`/`run_cli`/argv assertions) |
| PIPE-03 | FlopsCounter 与监控共用容错 loader 的 JSON 输出契约 | Tolerant-read precedents located (`run_sweep.py:535-541`, `:1105-1130`, both untouched per D-20); loader contract + test design in Pattern 4 |
| CUST-05 | 注册表叠加层（overlay）：管线工具在官方注册表之上加载自定义 overlay（冲突 fail-fast）；无自定义文件时行为逐字节一致 | All 5 load sites verified with exact line ranges; no-overlay baseline verified live (`~/.config/dnallmmark` absent); collision + byte-identity test design in Pattern 3 |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

From `/home/forrest/Github/dnallmmark/.claude/CLAUDE.md` (checked into the codebase) and long-term memory:

- **GSD workflow enforcement** — no direct repo edits outside a GSD workflow (this research runs inside one).
- **Fix discipline** — surgical fixes only; no opportunistic refactors that widen review surface. Directly reinforces D-09/D-20 (untouched surfaces stay untouched).
- **Tech stack** — Python 3.13 / vanilla JS; no architecture changes for public release.
- **CI feasibility** — GitHub Actions must not require GPU or the external `dnallm` package; test scope limited to stdlib/numpy/pandas scripts and static checks. [VERIFIED: .github/workflows/ci.yml:34-74 — `make lint`, `make typecheck`, `make test`, no GPU runner]
- **DNALLM sibling repo strictly read-only** (`/home/forrest/Github/DNALLM` @ v1.2.1) — memory `dnallmmark-dnallm-repo-off-limits.md`.
- **ruff + ty gates mandatory from Phase 7 on** — memory `dnallmmark-ruff-ty-required.md`; `make lint` / `make typecheck` [VERIFIED: Makefile:125-135].
- **NO pipeline runs without GSD execution context** — but D-21 lifts code-only for *planned, bounded* GPU smokes; E2' full sweep stays maintainer dual-gate (memory `dnallmmark-no-pipeline-runs.md`, amended by D-21).
- **Bilingual comments acceptable** — match the surrounding file (EN/中文).
- **JS conventions** — irrelevant this phase (no JS changes).

## Summary

Phase 7 is a pure brownfield integration phase over four already-hardened files (`run_finetune.py`, `run_sweep.py`, `audit_n_frequencies.py`, the deprecated `dnallmmark_pipeline.py`). Every decision is already locked in 07-CONTEXT.md (D-01..D-27); the research job was to convert those decisions into exact, line-anchored mechanics. Three discoveries dominate the plan shape:

**First, the legacy FLOPs measurement is a pre-training calibration pass, not training-time instrumentation.** [VERIFIED: pipeline/dnallmmark_pipeline.py:1072-1157] The legacy pipeline registers hooks, runs ONE `torch.no_grad()` forward on a single train sample (with an evo2-backbone special case, a bf16-autocast branch, and an attention_mask fallback), calls `remove_hooks()` immediately, then extrapolates: `per_token = total_flops / seq_len_of_sample`, `all_tokens_estimate = total_flops * train_tokens / seq_len`. Hooks therefore never live during `DNATrainer` training — which answers the "how to count without breaking DDP/PEFT" question structurally: replicate the calibration slot in `run_finetune.py` (between the encode block ending at `:1419` and `reset_peak_memory_stats` at `:1425-1429`, i.e., before the `DNATrainer` ctor at `:1444`), and the training path is untouched. The D-05 hardware section (`train_time`, `max_mem_gb`, `gpu_device`) is the only part that must be captured post-training — `max_mem` already exists as a print-only variable at `:1533-1539`, `train_runtime` already flows back in `trainer.train()`'s metrics dict (proven in the 06-02 smoke: `"train_runtime": 42.416`), and `torch.cuda.get_device_name` is verified present in the installed torch 2.11.0+cu130.

**Second, `run_finetune.py` is never imported in tests — it is read as source text** [VERIFIED: tests/test_run_finetune_contracts.py:5-9], and two test helpers regex-extract function spans from its source (`def validate_subset_file` → `def set_seed`, `def validate_train_fraction` → `def set_seed`) and `exec()` them. This constrains the port: the new FlopsCounter must live in a **new module** (`pipeline/flops_counter.py` recommended) with **lazy/injectable `torch.nn`** so it CAN be imported CPU-side with stub modules (a strictly stronger test than source-text assertions), and any new pure functions added to `run_finetune.py` must NOT be inserted into the `:276-517` exec-extract span. It also settles the D-14 sweep-side pre-validation question: `run_sweep.py` is stdlib-only and imported headless by tests, so it cannot import `run_finetune.validate_subset_file`; a slim sweep-owned collect-all validator (~25 lines, the `_validate_filters`/`parse_curve_fractions` discipline) is the surgical answer (see Open Questions Q2).

**Third, the overlay has a dependency seam the decisions imply but don't spell out:** D-07 defaults to platformdirs' path, but platformdirs is NOT declared in any CPU-side group — it is only a transitive of `jupyter_core`/`setuptools`/`wandb` in the GPU lane [VERIFIED via importlib.metadata this session] — while ROADMAP binding constraint 10 places platformdirs in the future `[tui]` group (Phase 8). Importing it from `pipeline/registry_loader.py` in Phase 7 would crash the CI dev lane. A ~4-line hand-rolled resolver (`DNALLMMARK_CUSTOM_REGISTRY_DIR` > `XDG_CONFIG_HOME` > `~/.config`, joined with `dnallmmark/`) gives the identical Linux path with zero new dependencies; Phase 8 may consolidate onto platformdirs behind it.

The GB10 smoke is de-risked by the Phase 6 precedent: `plant-dnabert-6mer` (89M, Bert arch, on disk at `pipeline/models/plant-dnabert-6mer`) × `iDNA_ABF_datasets__5mC` (Train=2110, smallest locally-present task) ran 1 epoch LoRA in 42.4s / 0.53 GB on this exact machine and venv [VERIFIED: 06-02-SUMMARY.md verbatim command + output]. The base-name cell (`plant-dnabert-6mer/iDNA_ABF_datasets__5mC/seed_9527`) has NO resume marker today (only `+lora` and `+probe` aliases do) [VERIFIED: filesystem], so a default-mode run trains fresh. A pleasant sanity anchor exists for free: HF Trainer already persists `total_flos` (fwd+bwd) in `final_metrics.json` — the FlopsCounter estimate (fwd-only, epoch-scaled) should land in the same order of magnitude (≈⅓ of it), giving D-23's "FLOPs 数量级 sane" check a mechanical formula.

**Primary recommendation:** Build in this order — (1) `pipeline/flops_counter.py` (lazy-torch port + uncovered accounting + hardware section builder) with CPU stub tests, (2) `pipeline/artifact_loader.py` + `schemas/flops_report.json` + synthetic-fixture contract tests, (3) `pipeline/registry_loader.py` + 5-site rewiring + overlay/collision/byte-identity tests, (4) run_sweep four-flag threading + argv-parity/manifest tests, (5) run_finetune integration (calibration slot + post-train write) + contracts-test extensions, (6) delete `pipeline/dnallmmark_pipeline.py` with reference cleanup (5 test parity sites re-pinned as literals; README/AUDIT/docs/`.claude/CLAUDE.md` mentions updated), (7) GB10 smoke as a planned GPU task, (8) full `make lint` + `make typecheck` + `make test` gate.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| FLOPs hook dispatch + calibration forward | Pipeline process (`pipeline/flops_counter.py` + `run_finetune.py` calibration slot) | — | Must run in-process on the live torch model before `DNATrainer` wraps it; hooks are process-local state [VERIFIED: dnallmmark_pipeline.py:1072-1142] |
| FLOPs extrapolation + report write | Pipeline process (post-train, rank-0-guarded) | — | `train_time`/`max_mem_gb` exist only after `trainer.train()` returns; write joins the final_metrics block so the WR-13 marker-last discipline holds [VERIFIED: run_finetune.py:1495-1507] |
| argv composition for child flags | Sweep driver (`run_sweep.build_argv`) | — | Single LIST-authority for the child argv; the TUI/CLI never bypasses it [VERIFIED: run_sweep.py:810-857] |
| Subset pre-validation (fail-fast) | Sweep driver (`run_sweep.main` pre-enumeration) | run_finetune `validate_subset_file` (authoritative re-check per cell) | Sweep must abort before ANY cell spawns; child re-validates because it is the authority [VERIFIED discipline: run_sweep.py:1218-1237] |
| Registry official+custom merge | Shared loader (`pipeline/registry_loader.py`) | — | 5 load sites across 3 files must not diverge (D-08 single-source precedent) |
| Custom-dir resolution | Shared loader (env var > XDG > `~/.config`) | platformdirs (Phase 8, `[tui]` group) | CPU lanes cannot import platformdirs today [VERIFIED: not a dep of any dev/data group package] |
| Tolerant JSON reads | Shared loader (`pipeline/artifact_loader.py`) | Phase 11 monitor (consumer), Phase 8 `tui/services` (consumer) | Parsing-level tolerance is consumer-agnostic; statefulness (last-known-good) stays with callers (D-18) |
| Schema pinning | `schemas/flops_report.json` + jsonschema (dev group) | — | Phase 2 discipline: draft-2020-12, `additionalProperties: false` on closed objects [VERIFIED: schemas/n_audit.json pattern] |
| Smoke execution | GB10 host, executor-run planned task | CI never | D-21/D-24; CI stays GPU-free [VERIFIED: ci.yml] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (`json`, `argparse`, `pathlib`, `os`, `sys`, `math`) | 3.13 | Everything new CPU-side: registry_loader, artifact_loader, sweep flags, tests | Repo discipline: `run_sweep.py` is stdlib-only and headless-imported by tests [VERIFIED: run_sweep.py:213-222, tests/conftest.py:41-44] |
| torch (GPU lane only) | 2.11.0+cu130 | FlopsCounter hooks, calibration forward, `get_device_name`/`max_memory_allocated` | Already pinned in `[gpu]` group, never CI-installed [VERIFIED: pyproject.toml gpu group + .venv dist-info] |
| jsonschema (dev group) | >=4.26.0 | flops_report schema validation in tests | Existing Phase 2 lane [VERIFIED: pyproject.toml dev group; tests/test_schemas.py:20] |
| pytest (dev group) | >=9.1.1 | All new tests | Existing harness; conftest already puts `pipeline/` on sys.path [VERIFIED: tests/conftest.py:44] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ruff | >=0.16.10 | `make lint` over the new files (must be ADDED to the Makefile lint list) | Every commit; default rule set (E4/E7/E9/F) — function-level imports pass |
| ty | >=0.0.85 | `make typecheck` — `pipeline/` already in `[tool.ty.src].include`, so new files are covered automatically | Every commit; `torch.**` already in `replace-imports-with-any` [VERIFIED: pyproject.toml] |
| platformdirs | (NOT this phase) | Custom-dir resolution | Phase 8 `[tui]` group per ROADMAP constraint 10 — see Open Questions Q1 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New `pipeline/flops_counter.py` module | Inlining FlopsCounter into `run_finetune.py` | Inline keeps one file but forfeits CPU-side import (module-level torch) and forces more source-text tests — rejected; the new module gets real unit tests over stubs |
| Hand-rolled XDG resolver in registry_loader | platformdirs import | platformdirs absent from dev/data groups (transitive only of GPU-lane jupyter_core/setuptools/wandb) [VERIFIED: importlib.metadata scan] — importing it would crash CI; declaring it now violates the surgical-stack constraint |
| Sweep-owned slim subset validator | Extracting `validate_subset_file` into a shared module | Shared module breaks the exec-extract regex tests (`def validate_subset_file` must remain in run_finetune source) [VERIFIED: test_run_finetune_contracts.py:749-751] — extraction costs test churn for zero behavioral gain (child re-validates authoritatively) |
| Post-success single flops_report write | Legacy-style pre-training write + post-train amend | Two writes risk a torn intermediate file; failed cells leaving no report is consistent with "no metrics, no marker" cell semantics — recommended single write (planner confirms) |

**Installation:**
```bash
# Nothing new. Existing gates only:
uv sync                        # data group (CPU)
uv run --group dev pytest      # test lane
uv run --group gpu python pipeline/env_smoke.py   # GPU lane (smoke preflight, proven Phase 6)
```

**Version verification:** No new packages introduced this phase, so no registry lookups were needed. torch/dnallm/peft/transformers verified live in `.venv` (dnallm 1.2.1, torch 2.11.0+cu130, peft 0.21.2, transformers 5.17.0) [VERIFIED: dist-info directories, 2026-10-11].

## Package Legitimacy Audit

> This phase installs **zero** external packages — the gate is vacuous. torch APIs used (`torch.cuda.get_device_name`, `torch.cuda.max_memory_allocated`, `torch.autocast`, `register_forward_hook`) were verified against the *installed* runtime (`.venv` torch 2.11.0+cu130), which is the authoritative source for this environment [VERIFIED: live attribute check, `hasattr` all True, `torch.cuda.is_available()` True].

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| (none — stdlib + existing pinned deps only) | — | — | — | — | — | — |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```text
                        OPERATOR / (future TUI, Phase 8+)
                              │ CLI argv (LIST)
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ pipeline/run_sweep.py  (stdlib-only; CPU-testable)                      │
│                                                                         │
│  parse_args ──► NEW --subset_file ──► sweep-side pre-validation         │
│                 NEW --effective_batch_size (nargs='?' const=16)         │
│                 NEW --num_train_epochs   NEW --cache_dir                │
│                       │ abs-path resolution (D-15, output_root rule)    │
│                       ▼                                                 │
│  registry loads ×3 ──► pipeline/registry_loader.py  ◄── NEW MODULE      │
│      (:368/:474/:514)   official{models,datasets}_info.json             │
│                         + optional custom overlay                       │
│                         (~/.config/dnallmmark/custom_*.json or          │
│                          $DNALLMMARK_CUSTOM_REGISTRY_DIR)               │
│                         collision w/ official key ──► fail fast         │
│                       │                                                 │
│                       ▼                                                 │
│  build_argv(:810) ── append-only LIST elements when flag PRESENT:       │
│      ["--subset_file", abs] ["--effective_batch_size", N]               │
│      ["--num_train_epochs", N] ["--cache_dir", abs]                     │
│      absent flag ──► ZERO extra elements (byte-identical argv)          │
│                       │                                                 │
│  run_matrix ──► subprocess.run(argv, cwd=PIPELINE_DIR, check=True)      │
│                       │            manifest cells record flags          │
│                       │            only-when-present (D-13)             │
└───────────────────────┼─────────────────────────────────────────────────┘
                        ▼  ONE PER CELL
┌─────────────────────────────────────────────────────────────────────────┐
│ pipeline/run_finetune.py  (torch+dnallm; GPU lane only)                 │
│                                                                         │
│  module level: registry loads (:674-679) ──► registry_loader (same      │
│      overlay seam; import-time behavior unchanged, D-08)                │
│                                                                         │
│  per (model, dataset):                                                  │
│    load model (:1060) → quirks → outdir/resume-check (:1201)            │
│    → batch/GA (:1302-1311, --effective_batch_size product semantics)    │
│    → DNADataset load → subset/fraction apply → encode (:1386-1418)      │
│                                                                         │
│    ══ NEW CALIBRATION SLOT (between :1423 and :1429) ══                 │
│    count train tokens ──► FlopsCounter(model, norm/act/embed=True)      │
│    ONE no_grad forward on train[0] (evo2 backbone case / bf16 autocast  │
│    / attention_mask fallback) ──► remove_hooks() ──► stash counts       │
│                                                                         │
│    DNATrainer ctor (:1444) ──► trainer.train() (:1481)                  │
│                                                                         │
│    ══ NEW POST-SUCCESS WRITE (rank-0, alongside final_metrics,          │
│       BEFORE the trainer_state.json marker copy — WR-13 marker-last) ══ │
│    flops_report.json = legacy schema + schema_version: 1                │
│                      + hardware{gpu_device, train_time, max_mem_gb}     │
│                                                                         │
│    pipeline/flops_counter.py  ◄── NEW MODULE (lazy torch.nn / DI)       │
│      20+ architecture dispatch (verbatim classname lists + order)       │
│      closure-factory hooks · save_to_json extrapolation                 │
│      NEW: uncovered-module accounting + threshold WARNING (D-03)        │
└───────────────────────┬─────────────────────────────────────────────────┘
                        │ flops_report.json (per cell dir)
                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ pipeline/artifact_loader.py ◄── NEW MODULE (pure, stateless)            │
│   load flops_report.json tolerantly: OSError / JSONDecodeError /        │
│   empty file ──► None sentinel; caller keeps last-known-good (D-17/18)  │
│   CONSUMERS: Phase 7 contract tests · Phase 11 monitor · Phase 8 tui/   │
└─────────────────────────────────────────────────────────────────────────┘
   Also rewired: script/audit_n_frequencies.py:599-601 datasets load ──►
   registry_loader (overlay seam, 5th touchpoint). export_runs.py UNTOUCHED
   (D-09). CI: make lint/typecheck/test — zero GPU/dnallm (constraint 2).
```

### Recommended Project Structure

```text
pipeline/
├── flops_counter.py      # NEW — FlopsCounter port (lazy torch.nn / DI),
│                         #   count_split_tokens, calibration-forward helper,
│                         #   uncovered accounting, report builder (+hardware)
├── registry_loader.py    # NEW — official+custom overlay: path resolution
│                         #   (env var > XDG > ~/.config), merge, collision
│                         #   fail-fast, load_models/load_datasets functions
├── artifact_loader.py    # NEW — tolerant JSON read (pure, stateless)
├── run_finetune.py       # EDITED — calibration slot + post-success write +
│                         #   registry loads routed through registry_loader
├── run_sweep.py          # EDITED — 4 flags, pre-validation, abs paths,
│                         #   argv append, manifest only-when-present fields,
│                         #   3 registry loads via registry_loader
├── (dnallmmark_pipeline.py  # DELETED at phase end — D-04)
script/
├── audit_n_frequencies.py # EDITED — 1 datasets load via registry_loader
schemas/
├── flops_report.json      # NEW — strict draft-2020-12 schema, schema_version 1
tests/
├── test_flops_counter.py   # NEW — stub-torch dispatch/unit tests (CPU)
├── test_registry_overlay.py # NEW — overlay/collision/byte-identity (CPU)
├── test_artifact_loader.py # NEW — tolerant-read contract (truncated/empty/missing)
├── test_sweep.py           # EXTENDED — 4-flag argv parity + manifest fields
├── test_run_finetune_contracts.py # EXTENDED — calibration-slot + write-order
│                           #   contracts; 5 legacy-parity sites re-pinned as
│                           #   literals when the legacy file is deleted
└── fixtures/…              # synthetic flops_report fixture (deterministic)
Makefile                    # EDITED — lint list += the 3 new pipeline modules
```

Naming follows repo convention: lowercase snake_case top-level modules in `pipeline/` (a sys.path root, not a package — same import mechanics as `run_sweep` today) [VERIFIED: tests/conftest.py:44; pyproject `[tool.ty.environment] extra-paths`].

### Pattern 1: FlopsCounter port — lazy torch, calibration slot, stub-testable dispatch

**What:** Port `FlopsCounter` (`dnallmmark_pipeline.py:43-708`) verbatim into `pipeline/flops_counter.py` with one structural change: `torch.nn` is resolved lazily/optionally so the module imports CPU-side without torch.

**When to use:** Always for this port (CONTEXT discretion clause: "torch 延迟导入/stub 可测").

**Mechanics (all line-verified this session):**

1. **Dispatch order is load-bearing.** `_register_hooks` is one if/elif chain [VERIFIED: dnallmmark_pipeline.py:66-187]: `nn.Linear` → `nn.Conv1d` → `nn.Conv2d` → `nn.MultiheadAttention` → classname lists (`BertSelfAttention`… → `Conv1D` → `BertUnpadSelfAttention` → flash list → `ModernBertAttention` → GQA list → `BigBirdAttention` → `HyenaFilter` → `MambaMixer`/`JambaMambaMixer` → `Mamba2Mixer` → `Mamba` → `Mamba2`) → **model_path-gated branches** (`"megadna" in model_path`, `"enformer" in model_path or "space" in model_path`, `"borzoi" in model_path or "flashzoi" in model_path`) → optional Embedding/Norm/Activation. Port the chain order EXACTLY — the model_path branches sit AFTER all classname branches, so a `Linear` inside a borzoi model hits the Linear hook first. The verbatim classname lists:

   - HF self-attn: `["BertSelfAttention", "JambaAttention", "MistralAttention", "MistralSdpaAttention", "RoPEBertSdpaAttention", "OLMoSequentialBlock", "GPT2Attention", "EsmSelfAttention", "MegatronBertSelfAttention"]`
   - Flash: `["MistralFlashAttention", "MistralFlashAttention2", "FlashAttentionBlock"]`
   - GQA: `["LlamaAttention", "GemmaAttention", "GemmaFlashAttention2", "GemmaSdpaAttention"]`
   - Mamba SSM: `["MambaMixer", "JambaMambaMixer"]`; Mamba2 SSD: `["Mamba2Mixer"]`; Caduceus: `["Mamba"]`; Caduceus2: `["Mamba2"]`
   - Singletons: `Conv1D`, `BertUnpadSelfAttention`, `ModernBERTAttention`(sic — the string compared is `"ModernBertAttention"`), `BigBirdAttention`, `HyenaFilter`
   - `model_path = getattr(self.model, "name_or_path", "").lower()` (:69)

   [VERIFIED: dnallmmark_pipeline.py:80-187, quoted verbatim above]

2. **Lazy torch seam (recommended form):** resolve `nn` inside `_register_hooks` via a module-level accessor the tests can monkeypatch, e.g. `def _torch_nn(): import torch.nn as nn; return nn` — or constructor injection `FlopsCounter(model, nn_module=None)` defaulting to the lazy import. Both keep the isinstance dispatch verbatim; tests pass a stub module object exposing `Linear`, `Conv1d`, `Conv2d`, `MultiheadAttention`, `Embedding`, `LayerNorm`, `SiLU`, `GELU`, `ReLU` as plain classes. Ruff's default rule set does not flag function-level imports; ty already replaces `torch.**` with Any [VERIFIED: pyproject.toml `[tool.ty.analysis]`]. Do NOT import torch at module top — that would recreate the read-source-never-import limitation.

3. **Hook bodies need only duck-typed attributes.** Closures read `inputs[0].shape` / `.numel()`, `module.out_features`, `module.kernel_size`, `module.groups`, `module.batch_first`, `module.all_head_size`, `module.config`, `module.q_proj.out_features`, `module.conv1d.*`, `cu_seqlens` arithmetic (`seq_lens**2).sum().item()`), and `self.model.config` (caduceus paths) [VERIFIED: :189-668]. A ~40-line stub harness (Shape namedtuple-ish, stub modules, hook handles with `.remove()`) exercises every hook deterministically — no GPU, no dnallm (success criterion 2).

4. **Calibration call pattern (port verbatim):**
   ```python
   # Source: pipeline/dnallmmark_pipeline.py:1075-1154 (legacy call site, read 2026-10-11)
   total_tokens, samples = count_split_tokens(dataset.dataset.get("train", []))
   device = next(model.parameters()).device ...
   flops_counter = FlopsCounter(
       model, include_norm=True, include_act=True, include_embed=True
   )
   # single-sample forward under no_grad:
   #   if "evo" in model_name.lower() and hasattr(model, "backbone"):
   #       _ = model.backbone.model(inputs_embeds or input_ids)
   #   elif configs["finetune"].bf16:
   #       with torch.autocast(device.type, dtype=torch.bfloat16): _ = model(...)
   #   else: _ = model(...)
   # fallback retry with attention_mask=torch.ones_like(input_ids)
   flops_counter.remove_hooks()
   current_tokens = input_ids.shape[-1] if input_ids is not None else (inputs_embeds.shape[1] if inputs_embeds is not None else 0)
   flops_counter.save_to_json(num_tokens=current_tokens, all_tokens=total_tokens, filepath=os.path.join(outdir, "flops_report.json"))
   ```
   Placement in `run_finetune.py`: after the encode try/except ends (`:1418`, the `print(f"Tokenizer type…")` line) and after the `deeplearning_models` target_length adjustment (`:1422-1423`), before `reset_peak_memory_stats` (`:1425-1429`). Counting AFTER `apply_train_fraction` (`:1361`) means curve cells automatically extrapolate from the fraction-scaled token count — correct per-cell FLOPs for the curve lane.

5. **Report schema (legacy verbatim + additions):**
   ```python
   # Source: pipeline/dnallmmark_pipeline.py:690-705 (verbatim keys)
   report = {
       "num_tokens": num_tokens, "all_tokens": all_tokens,
       "num_params": self.total_params,
       "total_flops_G": self.total_flops / 1e9,
       "total_flops_exact": self.total_flops,
       "total_flops_per_token": per_token_flops,
       "total_flops_all_tokens": all_tokens_flops,
       "computation_size_ratio": computation_size_ratio,
       "config": {"include_norm": ..., "include_act": ..., "include_embed": ...},
       "layer_details": self.layer_flops,
   }
   ```
   Phase 7 additions: top-level `"schema_version": 1` (D-27) and optional `"hardware": {"gpu_device": str|None, "train_time": float|None, "max_mem_gb": float|None}` (D-05). Note `layer_details` values are the LAST forward's per-layer flops (the dict is overwritten per pass) while `total_flops` accumulates — legacy behavior, keep it [VERIFIED: e.g. `:198` `self.layer_flops[name] = flops` vs `:197` `+=`].

6. **Post-success write point:** the hardware fields exist only after training, so `save_to_json`'s file write belongs in the `local_rank == 0` success block — after the `final_metrics.json` write (`:1495-1506`) and BEFORE the `trainer_state.json` marker copy (`:1507`), preserving the WR-13 marker-is-final-act kill-window discipline [VERIFIED: test_final_metrics_written_before_resume_marker pins this ordering]. Under torchrun, guard the write with the same `local_rank == 0` check already used there (legacy wrote unguarded — single-GPU in practice; the guard is cheap insurance against N ranks writing one file). Values: `train_time = metrics.get("train_runtime")` (proven key), `max_mem_gb` = the existing `max_mem` computation (`:1533-1538` — note it is currently computed AFTER the success block; either hoist the read or compute at write time), `gpu_device = torch.cuda.get_device_name() if torch.cuda.is_available() else None` (NPU path: leave None — CUDA-only capture this phase; `get_device_name` verified present in installed torch).

7. **Uncovered accounting (D-03, new):** at registration time, record every named module that (a) directly owns parameters and (b) matched no dispatch branch and is not a pure container. After the calibration forward, compute `uncovered_param_share = uncovered_params / total_params` (parameters under no hooked module's subtree, derivable by `named_parameters()` prefix matching against hooked module names). Report `uncovered_layers: [{name, classname}, …]` in the JSON and print a WARNING when the share exceeds the threshold. Legacy has NO threshold to derive from — with `include_norm/act/embed=True` a BERT model is fully covered (Linear+Embedding+LayerNorm+BertSelfAttention), so any sane threshold is unreachable for conventional architectures; **recommend 0.05 (5% param share)** as the default, surfaced as a module constant the planner/executor can tune (CONTEXT leaves the value to planner discretion).

**Example (test-shape, the stub harness):**
```python
# tests/test_flops_counter.py — CPU-side, no torch import required
import flops_counter  # conftest puts pipeline/ on sys.path

def _stub_nn(): ...          # plain classes: Linear(out_features=…), Conv1d, …
def _stub_model(modules): ...  # named_modules(), name_or_path, config, parameters()

def test_linear_hook_counts_2NTIF(monkeypatch):
    nn = _stub_nn()
    monkeypatch.setattr(flops_counter, "_torch_nn", lambda: nn)
    counter = flops_counter.FlopsCounter(_stub_model([("mlp.0", nn.Linear(8, 16))]),
                                         include_norm=True, include_act=True, include_embed=True)
    counter.fire("mlp.0", batch=2, tokens=5, in_feat=8)   # tiny test seam or direct closure call
    assert counter.layer_flops["mlp.0"] == 2 * 2 * 5 * 8 * 16   # 2·N·T·F_in·F_out
    assert counter.uncovered_param_share() == 0.0
```
(Exact fire-mechanism is implementer's choice — either call the returned closure directly with `(module, inputs, outputs)` triples, or have stub `register_forward_hook` record closures for manual invocation. Direct closure invocation is the least-magic option.)

### Pattern 2: argv threading — append-only LIST elements, absent = byte-identical

**What:** Four new sweep flags, each appending separate LIST elements to the child argv only when present, exactly as `--peft`/`--train_fraction` already do [VERIFIED: run_sweep.py:853-857].

**When to use:** every new flag.

**Verified mechanics:**
- `build_argv(model, task, seed, output_root, peft="none", train_fraction=None)` returns `[sys.executable, str(RUN_FINETUNE), "--target_model", …, "--output_dir", …]` + conditional appends [VERIFIED: :844-857]. New kwargs (`subset_file=None, effective_batch_size=None, num_train_epochs=None, cache_dir=None`) each append `["--flag", str(value)]` when not None. `launch_subprocess` and `run_matrix`'s `functools.partial` executor binding thread them through [VERIFIED: :1049-1052, :860-876].
- `--effective_batch_size`: `parser.add_argument("--effective_batch_size", nargs="?", const=16, type=int, default=None)` — bare flag → 16, valued → int, absent → None (no argv elements). NOTE: REQUIREMENTS.md PIPE-02 writes the hyphenated form `--effective-batch`, but D-11 locks the underscore name with zero alias mapping — CONTEXT wins.
- Auto-GA is the CHILD's existing logic — the sweep does NOT compute GA [VERIFIED verbatim, run_finetune.py:1302-1311]:
  ```python
  if effective_batch_size is not None:
      if bs_new >= effective_batch_size:
          required_grad_accum = 1
      else:
          required_grad_accum = max(1, effective_batch_size // bs_new)
  ```
  This is exactly D-10's `GA = max(1, N // bs_new)` product semantics; the sweep is pure pass-through (D-16 discipline).
- `--num_train_epochs`: child override already documented "flag overrides config" at the `:949-958` block; sweep passes `str(int)`.
- `--subset_file` / `--cache_dir`: resolve `Path(args.subset_file).resolve()` / `Path(args.cache_dir).resolve()` in `main()` before threading (D-15; the `--output-root` precedent is `Path(args.output_root).resolve()` at `:1179`). The child's `_peek_cache_dir` reads `--cache_dir` from raw argv BEFORE argparse [VERIFIED: run_finetune.py:5-18] — threading works with no child change.
- **Pre-validation (D-14):** a sweep-owned validator run in `main()` after `_validate_filters` (the fail-fast zone at `:1218-1237`), loading the (overlay-merged) datasets registry it already has and checking: file readable JSON (`_read_operator_json` precedent, :524-541), top-level object, every key in the datasets registry, every value a list of ints within `[0, Test)`. Collect ALL problems → `sys.exit(f"[Error] --subset_file …")`. Do NOT import `validate_subset_file` from run_finetune (torch-blocking; see Open Questions Q2).
- **Manifest only-when-present (D-13):** `_manifest_payload` projects a fixed key set from records [VERIFIED: :978-992]. Thread a `sweep_flags` dict (only keys whose flag was present) into `run_matrix` and merge into each manifest cell; `_write_json` already uses `sort_keys=True` so key order stays deterministic [VERIFIED: :899-903]. Absent flags → no keys → byte-identical manifests (the `test_dry_run_manifest_is_byte_deterministic` and `test_peft_none_default_is_byte_identical_to_today` tests stay green unmodified [VERIFIED: tests/test_sweep.py:206, :1418]).

**Test shape (follows the proven harness):**
```python
# Source: pattern of tests/test_sweep.py:491-522 and :1479-1506 (existing, verbatim idioms)
argv = run_sweep.build_argv("model-a", "task-x", 42, "/tmp/root",
                            effective_batch_size=16)
assert flag_value(argv, "--effective_batch_size") == "16"
argv_none = run_sweep.build_argv("model-a", "task-x", 42, "/tmp/root")
assert "--effective_batch_size" not in argv_none
assert "--subset_file" not in argv_none and "--num_train_epochs" not in argv_none \
       and "--cache_dir" not in argv_none
```
Plus `run_cli(monkeypatch, ["--effective_batch_size", …])` bare-flag → const-16 CLI tests, and an abs-path assertion (`flag_value(argv, "--subset_file").startswith("/")`).

### Pattern 3: registry overlay — one loader, five sites, collision fail-fast, absent = byte-identical

**What:** `pipeline/registry_loader.py` exposing e.g. `load_models_registry(registry_dir) -> dict` and `load_datasets_registry(registry_dir) -> dict`: read the official file with plain `open`/`json.load` (missing official file raises exactly as today — import-time behavior unchanged, D-08), then optionally merge custom entries.

**Verified load sites to rewire:**

| Site | Current code | Notes |
|------|--------------|-------|
| `run_sweep.enumerate_matrix` | `run_sweep.py:367-371` — opens both registries from `registry_dir` param | tests call with tmp_path registries |
| `run_sweep._validate_filters` | `run_sweep.py:473-477` — same | |
| `run_sweep._load_registry_key_sets` | `run_sweep.py:513-517` — same | |
| `run_finetune` module level | `run_finetune.py:672-679` — `base_dir + "datasets_info.json"` / `"models_info.json"` | must stay module-level, same exceptions |
| `audit main` | `script/audit_n_frequencies.py:599-601` — `args.registry_dir / "datasets_info.json"` | datasets only |

**Mechanics:**
- **Path resolution (recommended):** `DNALLMMARK_CUSTOM_REGISTRY_DIR` env var (whole-directory override, D-07) → else `Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "dnallmmark"`. Identical result to platformdirs on Linux. Verified TODAY the default dir does not exist on this host and the env var is unset — the no-overlay byte-identity baseline is live [VERIFIED: filesystem check 2026-10-11].
- **Merge semantics:** custom file absent → return official dict object as-is (byte-identical). Custom present → validate it is a JSON object, then for each custom key: if key already in official → fail fast (`sys.exit`/raise with a message naming the key and BOTH file paths — D-08 "清晰报错"); else add. Malformed custom JSON → fail fast with the file named (never silently ignored — the "宁可噪声" discipline).
- **Cross-root import for audit:** `script/` files cannot `import registry_loader` standalone (sys.path[0] = `script/`). Use the repo's established file-path loader [VERIFIED precedent: script/run_migration_inventory.py:95-101 uses `importlib.util.spec_from_file_location` for baseline/compare.py] targeting `REPO_ROOT / "pipeline" / "registry_loader.py"`, or a 2-line `sys.path.insert`. The importlib form is the documented precedent.
- **Determinism caveat for tests:** the overlay auto-detection is environment-sensitive. New Phase 7 overlay tests MUST pin `DNALLMMARK_CUSTOM_REGISTRY_DIR` (monkeypatch env → empty tmp dir for absent-case, populated tmp dir for merge-case) so they are machine-independent. Existing tests pass unmodified on CI (no custom files there) — but note for the future: once real custom files exist on the maintainer's machine (Phase 9+), locally-run sweep tests that use tmp registries would see the local overlay. Cheap future-proofing (planner's call): the loader applies the overlay only when reading the DEFAULT pipeline registry dir vs. any `--registry-dir`… or accept uniform application and document the local-run caveat. Uniform application is the simpler, decision-text-faithful reading of D-06.
- **run_finetune import-time contract:** today a missing official registry crashes the import (`open` raises inside module top-level). The loader must reproduce that (do not catch OSError on the OFFICIAL file) — "导入时序不变" means same order, same failure modes, same resulting dicts.

**Test shape:**
```python
def test_overlay_absent_is_byte_identical(tmp_path, monkeypatch):
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(tmp_path / "empty"))
    official = write_registry(tmp_path / "reg", models={...}, datasets={...})
    merged = registry_loader.load_models_registry(tmp_path / "reg")
    assert merged == json.loads((tmp_path / "reg" / "models_info.json").read_text())

def test_custom_key_colliding_with_official_fails_fast(tmp_path, monkeypatch):
    ... custom file with an existing official key ...
    with pytest.raises(SystemExit):        # or the loader's specific error type
        registry_loader.load_models_registry(...)
```

### Pattern 4: tolerant artifact loader — parsing-level tolerance, stateless, sentinel

**What:** `pipeline/artifact_loader.py` with a pure function, e.g. `load_json_artifact(path) -> dict | list | None`, catching `OSError` (missing/unreadable), `json.JSONDecodeError` (truncated/partial), and the empty-file case (`json.loads("")` raises `JSONDecodeError`, so one except covers it — but an explicit read-then-decode makes the empty case nameable if a distinct sentinel/error is desired). Structurally-valid-but-key-missing JSON is NOT corruption (D-17) — the loader returns it; key checks belong to callers.

**Precedents (both stay untouched, D-20):**
- `run_sweep._read_operator_json` (:524-541): catches `OSError` + `json.JSONDecodeError` → `sys.exit` (operator-input fail-fast — a DIFFERENT contract, do not imitate the exit).
- `run_matrix`'s WR-11 inline read (:1105-1130): corrupt metrics → cell failed, sweep continues (consumer-side last-known-good analogue).

**Phase 7 consumer:** contract tests only (valid → dict; truncated → None; empty → None; missing → None; unreadable-perms → None). The Phase 11 monitor and Phase 8 `tui/services/` import this module later (D-19 dependency direction tui→pipeline). Keep the module dependency-free (stdlib `json` + `pathlib` only) so every lane can import it.

### Pattern 5: strict schema + synthetic fixture (Phase 2 discipline applied to a non-committed artifact)

**What:** `schemas/flops_report.json` (draft-2020-12, `$id` under the repo's raw.githubusercontent convention, `$comment` documenting the contract) + a deterministically-generated synthetic fixture validated in tests.

**Verified pattern source** [schemas/n_audit.json: draft-2020-12, `"additionalProperties": false`, all-required, conditional `if/then` for optional sections; tests/test_schemas.py:20 uses `Draft202012Validator`].

**flops_report schema shape (planner refines):**
- Required: `schema_version` (const 1), `num_tokens`, `all_tokens`, `num_params`, `total_flops_G` (number), `total_flops_exact` (integer), `total_flops_per_token`, `total_flops_all_tokens`, `computation_size_ratio` (number or null — null when `num_tokens` is None), `config` (closed object, three booleans), `layer_details` (object with integer values — `additionalProperties: {"type": "integer"}`; keys are layer names, cannot be a closed set), plus D-03's `uncovered_layers` list.
- Optional: `hardware` (`gpu_device` string|null, `train_time` number|null, `max_mem_gb` number|null) — optional section per D-27.
- Unlike committed-data schemas, flops_report is machine-specific and NOT committed (D-26) — it does NOT join the `test_schemas.py` committed-file bucket map; its validation test builds the fixture in-test (deterministic synthetic generation) and validates against the schema.

### Anti-Patterns to Avoid

- **Importing torch at module top of `flops_counter.py`** — recreates the read-source-never-import limitation and makes the dispatch untestable CPU-side. Lazy accessor or constructor injection only.
- **Inserting new functions into `run_finetune.py`'s `:276-517` span** — the exec-extract regexes (`def validate_subset_file` → `def set_seed`, `def validate_train_fraction` → `def set_seed`) sweep everything in between [VERIFIED: test_run_finetune_contracts.py:743-783]. New helpers go after `set_seed` (`:517`) or in the new module.
- **Keeping hooks alive during training** — DDP/PEFT/gradient-checkpointing interactions, double counting under gradient accumulation, and hook overhead across thousands of steps. The legacy calibration-pass design exists precisely to avoid this; replicate it.
- **Writing flops_report.json after the trainer_state.json marker copy** — violates WR-13 (marker must be the final act; a kill between marker and report would mark a cell done with missing FLOPs) [VERIFIED: test_final_metrics_written_before_resume_marker].
- **Validating `--subset_file` per cell instead of once at sweep start** — a bad file would burn model-load time on cell 1 of N before dying (D-14 explicitly rejects per-cell errors).
- **Letting the overlay mutate or write official registry files** — constraint 11: official files are never written by any custom flow; the loader is read-only over both.
- **Registering the four flags with hyphenated aliases** — D-11: zero alias mapping; underscore names only.
- **Deleting `dnallmmark_pipeline.py` without re-pinning the 5 parity tests** — `tests/test_run_finetune_contracts.py` reads `LEGACY_PIPELINE` at :394/:491/:559/:622/:666; deletion without inlining the expected values as literals (documented as transcribed from the deleted file) turns the suite red.
- **Absolute-path laziness on threaded flags** — child cwd is pinned to `pipeline/`; a relative `--subset_file`/`--cache_dir` resolves against the wrong root (D-15).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| FLOPs formulas per architecture | Re-derive attention/SSM/FFT FLOPs math | Port the 20+ verified hook bodies verbatim from `:189-668` | The formulas encode non-obvious decisions (flash-attn `4·b·s·w·d` window, Hyena's 5-term FFT sum, Caduceus fused-projection terms); re-deriving invites silent divergence from every historical leaderboard number |
| JSON parsing tolerance | Ad-hoc try/except at each read site | `pipeline/artifact_loader.py` single contract | Three copies of tolerance logic (run_sweep ×2 today + monitor later) drift; D-19 exists to prevent exactly this |
| Registry merge + collision rules | Per-site overlay loops | `pipeline/registry_loader.py` | Five sites × hand-rolled merge = five divergence chances; collision fail-fast must be identical everywhere |
| Argv construction | f-string/shell composition | The existing LIST `build_argv` append pattern | T-03-10 (no shell) + byte-identity testing both depend on the LIST form |
| XDG path resolution | Full platformdirs adoption now | 4-line env>XDG>home resolver in registry_loader | platformdirs is absent from dev/data groups (verified) and reserved for `[tui]` in Phase 8 (constraint 10) |

**Key insight:** this phase's entire risk profile is *divergence from proven behavior* — every "don't hand-roll" is really "don't re-derive what the repo already proved."

## Runtime State Inventory

> This phase is not a rename/refactor phase, but D-04 deletes a file, so the deletion-adjacent runtime state is inventoried.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no database/store keys reference `dnallmmark_pipeline` (grepped: only docs/tests/comments/planning archives) [VERIFIED: repo-wide grep 2026-10-11] | none |
| Live service config | None — no external services consume the legacy module | none |
| OS-registered state | None | none |
| Secrets/env vars | None — no secret or env var names derive from the deleted module name | none |
| Build artifacts | `pipeline/__pycache__/dnallmmark_pipeline.cpython-{313,314}.pyc` exist (untracked bytecode) [VERIFIED: filesystem] | Harmless (Python will not import source-less .pyc from `__pycache__`); optionally delete for cleanliness in the same task |
| In-repo references to the deleted file | LIVE CODE: `tests/test_run_finetune_contracts.py` (LEGACY_PIPELINE const :159; reads at :394/:491/:559/:622/:666), comment in `script/export_runs.py:286`; DOCS: `README.md:474`, `AUDIT.md`, `docs/TUI-REQUIREMENTS.md`, `.claude/CLAUDE.md` (31 mentions — includes the now-false "retained read-only, never deleted" claims); PLANNING ARCHIVES under `.planning/milestones/` (historical records — do NOT edit) | Tests: re-pin the 5 parity expectations as inline literals; comments/docs: refresh or drop stale mentions; `.claude/CLAUDE.md`: update the architecture sections that describe the legacy file as the FLOPs reference (it moves to `flops_counter.py`) |

## Common Pitfalls

### Pitfall 1: The exec-extract test span breaks silently
**What goes wrong:** Adding a helper function between `validate_subset_file`/`validate_train_fraction` and `set_seed` in `run_finetune.py` changes what the regex-extracted source contains; if the helper imports anything not in the exec namespace (`{"json": json, "Path": Path}` / `{}`), the extracted-functions tests crash with NameError at exec time.
**Why it happens:** The tests exec a regex span, not an imported module [VERIFIED: test_run_finetune_contracts.py:757-758 `exec(match.group(0), namespace)`].
**How to avoid:** New run_finetune helpers go after `set_seed` (`:517`) or into the new modules. If the calibration block must call a helper, the helper lives in `flops_counter.py`.
**Warning signs:** `NameError` in `test_run_finetune_contracts.py` subset/fraction tests.

### Pitfall 2: platformdirs import crashes the CI dev lane
**What goes wrong:** `registry_loader.py` does `import platformdirs` (per D-07's wording) → locally fine (GPU-lane transitive present) → CI `make test`/`make lint` red because the dev/data resolution has no platformdirs.
**Why it happens:** platformdirs is only required by `jupyter_core`/`setuptools`/`wandb` — GPU-lane neighbors [VERIFIED: importlib.metadata scan this session]; `uv tree --group dev` shows no platformdirs.
**How to avoid:** Hand-rolled resolver (env var > XDG_CONFIG_HOME > `~/.config`, joined with `dnallmmark/`). If platformdirs is adopted later, it lands with the `[tui]` group (Phase 8) behind the same seam.
**Warning signs:** `ModuleNotFoundError: No module named 'platformdirs'` in CI.

### Pitfall 3: Overlay makes machine-dependent test outcomes
**What goes wrong:** Once real custom files exist in `~/.config/dnallmmark/`, every test that loads registries through the loader on THAT machine sees merged registries — `make test` locally diverges from CI.
**Why it happens:** D-06's auto-detection is environment-global; tmp_path registries don't opt out.
**How to avoid:** All NEW overlay-aware tests pin `DNALLMMARK_CUSTOM_REGISTRY_DIR` via monkeypatch. Document the local-run caveat; if it bites in Phase 9, the loader can scope overlay application (planner/Phase 9 decision — uniform application is the D-06-faithful default).
**Warning signs:** Registry-count assertions failing only on machines with custom files.

### Pitfall 4: flops_report written after the resume marker (WR-13 regression)
**What goes wrong:** Post-training write lands after `shutil.copy(... trainer_state.json ...)`; a kill between them leaves a permanently-"done" cell with no FLOPs report.
**How to avoid:** Write order in the success block: `final_metrics.json` → `flops_report.json` → marker copy. Extend the WR-13 contracts test to include the flops write.
**Warning signs:** The ordering test failing; smoke artifact missing after an interrupted run.

### Pitfall 5: nargs='?' flag spelling and CLI foot-guns
**What goes wrong:** `--effective_batch_size 0` or negative values thread into the child and produce `required_grad_accum` quirks; `--subset_file` given an empty string; `--num_train_epochs 0`.
**Why it happens:** argparse accepts them; the child's own guards are partial (effective_batch_size has no positivity check today [VERIFIED: :1302-1311 has none]).
**How to avoid:** Sweep-side collect-all validation mirroring `parse_curve_fractions`: `effective_batch_size >= 1`, `num_train_epochs >= 1`, non-empty resolved subset path. Fail fast naming the flag and value (WR-14 style).
**Warning signs:** Smoke/sweep running with nonsense batch math.

### Pitfall 6: make lint doesn't cover the new modules
**What goes wrong:** New files pass CI's lint job by luck of not being in the file list — then a later broadening flags them with pre-existing findings.
**Why it happens:** `make lint` checks an explicit file list [VERIFIED: Makefile:125-126].
**How to avoid:** Add `pipeline/flops_counter.py pipeline/registry_loader.py pipeline/artifact_loader.py` to the lint list in the same commit that creates them. (`make typecheck` needs nothing — `[tool.ty.src].include` already covers `pipeline/` [VERIFIED: pyproject.toml].)

### Pitfall 7: Deleting the legacy file orphans its stale bytecode + stale claims
**What goes wrong:** `.pyc` files linger; `.claude/CLAUDE.md` and README keep asserting the file is "retained read-only, never deleted" — future agents re-cite a deleted file.
**How to avoid:** One deletion task includes: file removal, `__pycache__` cleanup (optional), the 5 test re-pins, export_runs.py:286 comment refresh, README/AUDIT/docs/`.claude/CLAUDE.md` mention updates. Planning archives stay untouched (historical records).

### Pitfall 8: Calibration forward changes RNG/model state
**What goes wrong:** The single no_grad forward could, on exotic models, mutate buffers (e.g., positional caches) and alter training.
**Why it happens:** Legacy accepted this risk (fallback path exists); the port must not widen it.
**How to avoid:** Port the try/except fallback chain verbatim (primary → attention_mask retry → print-and-continue on double failure, `:1105-1140`). Do not add weight init, `model.eval()` switches, or dtype moves beyond the legacy pattern.
**Warning signs:** Smoke metrics diverging wildly from the 06-02 baseline on the same cell.

## Code Examples

### Legacy calibration block (the port's source of truth)
```python
# Source: pipeline/dnallmmark_pipeline.py:1075-1090, 1142-1153 (verbatim excerpts, read 2026-10-11)
total_tokens, samples = count_split_tokens(dataset.dataset.get("train", []))
flops_counter = FlopsCounter(
    model, include_norm=True, include_act=True, include_embed=True
)
...
                try:
                    with torch.no_grad():
                        if "evo" in model_name.lower() and hasattr(model, "backbone"):
                            _ = model.backbone.model(...)
                        elif configs["finetune"].bf16:
                            with torch.autocast(device.type, dtype=torch.bfloat16):
                                _ = model(...)
                        else:
                            _ = model(...)
                except Exception:
                    # retry once with attention_mask=torch.ones_like(input_ids)
                    ...
                flops_counter.remove_hooks()
                current_tokens = (
                    input_ids.shape[-1] if input_ids is not None
                    else (inputs_embeds.shape[1] if inputs_embeds is not None else 0)
                )
                out_stats = os.path.join(outdir, "flops_report.json")
                flops_counter.save_to_json(
                    num_tokens=current_tokens, all_tokens=total_tokens, filepath=out_stats)
```

### GA semantics the sweep threads into (child, existing, verbatim)
```python
# Source: pipeline/run_finetune.py:1301-1311 (verbatim)
                # In case memory insufficient or effective_batch_size is specified
                if effective_batch_size is not None:
                    # Adjust gradient_accumulation to achieve target effective batch size
                    if bs_new >= effective_batch_size:
                        # batch_size already large enough, no need for gradient accumulation
                        required_grad_accum = 1
                    else:
                        required_grad_accum = max(1, effective_batch_size // bs_new)
                    configs["finetune"].gradient_accumulation_steps = required_grad_accum
```

### The proven GB10 smoke command (Phase 6 precedent — Phase 7 adapts)
```bash
# Source: .planning/milestones/v0.7.1-phases/06-revision-packaging-extended-lanes/06-02-SUMMARY.md
# (from pipeline/, exit 0, 42.4s / 0.53 GB for the LoRA variant)
cd /home/forrest/Github/dnallmmark/pipeline
uv run --group gpu python run_finetune.py --target_model plant-dnabert-6mer \
    --target_dataset iDNA_ABF_datasets__5mC --peft lora --num_train_epochs 1
# Phase 7 FLOPs smoke (recommended shape — default peft=none, fresh base-name cell):
uv run --group gpu python run_finetune.py --target_model plant-dnabert-6mer \
    --target_dataset iDNA_ABF_datasets__5mC --num_train_epochs 1
# Sweep-driven alternative (additionally exercises PIPE-02 threading end-to-end):
uv run --group gpu python pipeline/run_sweep.py --models plant-dnabert-6mer \
    --tasks iDNA_ABF_datasets__5mC --seeds 42 --output-root <abs-outdir> \
    --num_train_epochs 1
```

### Smoke pass-criteria mechanics (D-23, all mechanically checkable)
```bash
REPORT=<outdir>/plant-dnabert-6mer/iDNA_ABF_datasets__5mC/seed_9527/flops_report.json
python - "$REPORT" <<'EOF'   # after the run:
# 1. report lands and parses; schema_version == 1
# 2. main-layer hooks hit: layer_details has keys ending ".matmul_core"
#    (BertSelfAttention → f"{name}.matmul_core") AND bare Linear layer keys
# 3. uncovered: uncovered_layers == [] (BERT fully covered) or share < threshold
# 4. magnitude sanity vs HF's own counter in final_metrics.json:
#    r = total_flops_all_tokens / total_flos   (HF = fwd+bwd over actual steps)
#    expect 0.05 <= r <= 1.0  (fwd-only extrapolation ≈ 1/3 of HF's fwd+bwd;
#    the 06-02 smoke's total_flos was 8.704e12 for this exact cell)
EOF
```

## State of the Art

Not applicable — no external ecosystem movement informs this phase (no new libraries, no API migrations). The only version-sensitive facts (torch 2.11 API surface) were verified against the installed runtime, which is the deployment target.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `trainer.train()` metrics always carry `train_runtime` on success (observed once, 06-02 smoke; treated as stable HF Trainer API) | Pattern 1 item 6 | `train_time` lands null; schema tolerates null — low risk, smoke would reveal |
| A2 | `torch.cuda.get_device_name()` returns market-specific strings (5090D/4090D) verbatim — untested on this host (GB10 reports its own name); no normalization per D-05 | Pattern 1 item 6 | None functionally (string passthrough) |
| A3 | Hand-rolled XDG resolver is acceptable for D-07 ("默认 platformdirs" read as "platformdirs' default path") | Pattern 3, Pitfall 2 | If maintainer insists on the library, it must be declared in the data group — one-line change either way |
| A4 | `plant-dnabert-6mer` + `iDNA_ABF_datasets__5mC` remain present/smallest at execution time (verified on disk today) | Smoke | Pick another locally-present pair (21 dataset dirs exist) |
| A5 | Rank-0-only flops_report write is correct under torchrun (legacy wrote unguarded; no multi-rank verification possible this phase) | Pattern 1 item 6 | Duplicate writes at worst (same content) — low |
| A6 | Uncovered metric = parameter-share under unhooked subtrees, threshold 0.05 — a design recommendation, not legacy-derived (legacy had no uncovered concept) | Pattern 1 item 7 | Threshold may fire noisily on some architecture → tune value, mechanism unchanged |
| A7 | HF `total_flos` is a usable magnitude anchor (fwd+bwd semantics) for D-23 sanity | Smoke criteria | Widen the ratio window; criterion is order-of-magnitude anyway |
| A8 | `bf16` branch of the calibration uses `configs["finetune"].bf16` as in legacy; run_finetune's fp32-quirk override (`:1114-1116`) lands before the calibration slot so the branch sees the corrected flag | Pattern 1 item 4 | If ordering differs, fp32-only models calibrate under autocast — port must verify override precedes slot (it does: quirk block `:1114` < slot `~:1424`) |

## Open Questions (RESOLVED)

All six were closed during Phase 7 planning (2026-10-11); each disposition names the adopting plan. Original notes retained for provenance.

1. **platformdirs now vs. Phase 8 (A3)**
   - What we know: D-07 names platformdirs; constraint 10 reserves it for `[tui]`; dev/data groups lack it (verified).
   - What's unclear: whether the maintainer reads D-07 as mandating the library in Phase 7.
   - Recommendation: hand-rolled resolver now, identical Linux path, one-line swap later. Flag at plan review.
   - **RESOLVED — adopted by 07-02 Task 1:** hand-rolled resolver (env var > XDG_CONFIG_HOME > ~/.config, joined with dnallmmark), documented in-plan as a visible refinement of D-07; platformdirs consolidation stays a Phase 8 one-line swap behind the same seam.

2. **Sweep-side subset pre-validation: slim reimplementation vs. shared extraction**
   - What we know: run_sweep cannot import run_finetune (torch); extracting `validate_subset_file` to a shared module breaks the exec-extract regex tests unless those tests are rewritten.
   - What's unclear: appetite for test churn vs. strict DRY.
   - Recommendation: sweep-owned ~25-line collect-all validator (the `_validate_filters` shape), child remains authoritative. Double validation is deliberate defense-in-depth, matching D-14's "pre-validate, then child enforces".
   - **RESOLVED — adopted by 07-03 Task 2:** `_validate_subset_file(path, datasets_info)`, the sweep-owned collect-all validator; the child's `validate_subset_file` stays authoritative — no shared import.

3. **Manifest flag-fields placement (record vs. manifest projection)**
   - What we know: D-13 says manifest cells record present-flags; `_manifest_payload` projects fixed keys from records; `run_record.json` is not to be disturbed (D-02 spirit).
   - Recommendation: thread a `flags` dict into `run_matrix`/`_manifest_payload` and merge into manifest cells only — run_record.json stays byte-identical even when flags are present.
   - **RESOLVED — adopted by 07-03 Task 3:** present-flags dict merged into `_manifest_payload` cells only; `_new_record` untouched, so run_record.json keeps its exact field set even when flags are present.

4. **flops_report write timing for failed cells**
   - What we know: legacy wrote the report pre-training (exists even if training fails); recommended design writes post-success only.
   - Recommendation: post-success single write (failed cells produce no artifacts, consistent with final_metrics semantics). Confirm at plan review — the alternative (calibration-time partial write, post-train amend) doubles write logic.
   - **RESOLVED — adopted by 07-04 Task 2:** single post-success write inside the local_rank == 0 success block, ordered final_metrics.json < flops_report.json < trainer_state.json marker (WR-13); a failed cell emits no report.

5. **Smoke driven via run_finetune directly vs. via run_sweep**
   - What we know: both shapes proven viable; direct = Phase 6 precedent (lowest risk); sweep-driven additionally proves PIPE-02 threading on GPU.
   - Recommendation: sweep-driven if a single smoke is desired for both proofs; direct if smoke risk must be minimal. Either satisfies D-22..D-25.
   - **RESOLVED — split across 07-06 Tasks 1-2:** Task 1 proves the sweep-driven surface with a CPU-side dry-run (flags thread + manifest recording, no GPU), Task 2 runs the GPU smoke direct through run_finetune.py (Phase 6 precedent shape) — both shapes proven at their lowest-risk lanes; D-22..D-25 satisfied.

6. **Overlay scope under non-default `--registry-dir`**
   - What we know: D-06 text implies uniform application; tests use tmp registries.
   - Recommendation: uniform application + env-var pinning in new tests (Pitfall 3); revisit only if Phase 9 wizards need isolation semantics.
   - **RESOLVED — adopted by 07-02 as a flagged assumption:** overlay applies uniformly regardless of registry_dir (the D-06-faithful reading); all new tests pin DNALLMMARK_CUSTOM_REGISTRY_DIR; revisit trigger remains "Phase 9 wizards need isolation semantics".

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| GPU (CUDA) | FlopsCounter smoke (D-22..D-24) | ✓ (`torch.cuda.is_available()` True) | GB10 / torch 2.11.0+cu130 | — |
| dnallm | run_finetune import at smoke time | ✓ | 1.2.1 [VERIFIED: dist-info] | — |
| peft / transformers | smoke (PEFT lanes optional) | ✓ | 0.21.2 / 5.17.0 | smoke uses peft=none — peft not strictly required |
| uv | all gates + smoke | ✓ | 0.12.23 (per CLAUDE.md runtime notes) | — |
| `plant-dnabert-6mer` weights | smoke model | ✓ | `pipeline/models/plant-dnabert-6mer` on disk | `plant-dnagpt-BPE` (also on disk) |
| `iDNA_ABF_datasets/5mC` split | smoke task | ✓ | on disk (21 dataset dirs present) | any locally-present small task |
| ruff / ty / pytest / jsonschema | lint+typecheck+test gates | ✓ | dev group per uv.lock | — |
| platformdirs | (NOT required — see Q1) | installed-but-undeclared | 4.12.4 (transitive, GPU lane) | hand-rolled resolver |
| node | JS test lane (`make test`) | ✓ | per CI setup | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** platformdirs (fallback: hand-rolled XDG resolver — recommended default).

## Validation Architecture

> `workflow.nyquist_validation` is explicitly `false` in `.planning/config.json` — section skipped per config.

Existing suite facts the planner should still know: `make test` = full pytest (`tests/`, conftest sys.path = script+baseline+pipeline) + node JS lane; `make test-fast` = `-m "not slow"`; `make ci` = `-m ci` pinned lane. New Phase 7 tests are plain pytest functions in `tests/` — no framework additions.

## Security Domain

> `security_enforcement` enabled (level 1, block on high) per `.planning/config.json`.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (local CLI tools, no auth surface added) |
| V3 Session Management | no | — |
| V4 Access Control | no | — (operator-local execution; no privilege changes) |
| V5 Input Validation | yes | stdlib `json.loads` for all new operator-supplied files (subset_file, custom registries); collect-all fail-fast validators; NO `eval`/`exec` in production code (the exec-extract pattern exists only in tests, sanctioned `# noqa: S102`) |
| V6 Cryptography | no | — |
| V12 File Handling | yes | Custom/official registry reads are read-only; official files never written by custom flows (constraint 11 — integrity of the published registry); flops_report written into the run's own outdir only |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious/typo'd `--subset_file` path reading arbitrary files | Information disclosure | File is parsed as JSON and only task-key/int-list structure is used; contents never executed; errors name the path (existing `_read_operator_json` precedent) |
| Custom registry injection (someone plants `~/.config/dnallmmark/custom_models.json`) | Tampering | Loader treats it as untrusted data: structure-validated, collision-failed, never written back; effect is limited to adding training targets the operator's own user account could add anyway (same trust domain as CLI args) |
| `DNALLMMARK_CUSTOM_REGISTRY_DIR` env-var abuse | Tampering | Operator-controlled env, same trust level as PATH/argv; tests pin it via monkeypatch; no privilege boundary crossed |
| argv injection via registry values | Elevation | LIST argv, never shell (T-03-10); `subprocess.run(list, shell=False)` [VERIFIED: run_sweep.py:872-876] |
| Prompt-injection via fetched/model content | — | N/A this phase: no network fetches, no LLM consumption of untrusted text in the new code paths |

## Sources

### Primary (HIGH confidence)
- Direct inspection 2026-10-11 (autorun HEAD 8f225b9): `pipeline/dnallmmark_pipeline.py` (FlopsCounter :43-708; calibration :1072-1157; report schema :690-705; dispatch lists :66-187), `pipeline/run_finetune.py` (all anchors cited inline), `pipeline/run_sweep.py` (build_argv :810-857; loads :367/:473/:513; tolerant reads :524-541/:1105-1130; run_matrix/main), `script/audit_n_frequencies.py` (:82-101, :561-617), `script/run_migration_inventory.py` (:91-101 importlib precedent), `tests/conftest.py`, `tests/test_sweep.py` (harness helpers :115-154; argv/byte-identity tests :206/:491/:1418/:1479), `tests/test_run_finetune_contracts.py` (:1-100 docstring, LEGACY_PIPELINE :159, reads :394-666, exec-extract :743-783), `tests/test_schemas.py`, `schemas/n_audit.json`, `Makefile` (:125-135), `pyproject.toml`, `.github/workflows/ci.yml`, `pipeline/models_info.json` / `datasets_info.json` (registry entries quoted), filesystem state (models on disk, finetuned markers, `~/.config/dnallmmark` absent, `__pycache__` contents)
- Live `.venv` verification 2026-10-11: torch 2.11.0+cu130 (`get_device_name`/`max_memory_allocated` present, CUDA available), dnallm 1.2.1, peft 0.21.2, transformers 5.17.0, platformdirs 4.12.4 (undeclared transitive — required only by jupyter_core/setuptools/wandb; absent from `uv tree --group dev`)
- Phase 6 smoke evidence: `.planning/milestones/v0.7.1-phases/06-revision-packaging-extended-lanes/06-02-SUMMARY.md` (verbatim command, timings, final_metrics payload incl. `train_runtime`/`total_flos`)

### Secondary (MEDIUM confidence)
- `.planning/research/SUMMARY.md` + `ARCHITECTURE.md` (2026-10-11 milestone research, HIGH per their own audit — treated as prior art, re-verified where load-bearing)

### Tertiary (LOW confidence)
- None relied upon.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; all APIs verified against the installed runtime
- Architecture: HIGH — every integration point line-verified this session; test harness shapes read directly
- Pitfalls: HIGH — each pitfall grounded in a specific verified mechanism (exec-extract spans, dependency groups, write ordering, lint file list)

**Research date:** 2026-10-11
**Valid until:** 2026-11-11 (stable; repo-internal facts drift only with new commits — re-anchor line numbers if run_finetune.py/run_sweep.py change before planning)
