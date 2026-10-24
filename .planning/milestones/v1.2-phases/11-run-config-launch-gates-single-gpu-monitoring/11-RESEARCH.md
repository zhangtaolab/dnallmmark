# Phase 11: Run Config, Launch Gates & Single-GPU Monitoring - Research

**Researched:** 2026-10-13
**Domain:** Same-source sweep planning via `pipeline/run_sweep.py` pure functions, detached subprocess launch + tee, sweep-artifact monitoring (run_record/manifest/failures trees), E2' maintainer gate, D-18 `--config-variant` threading (Textual TUI service layer)
**Confidence:** HIGH (every load-bearing claim live-probed this session against the repo venv Python 3.13, the real registries, the real on-disk model/dataset trees, the real GB10 artifacts, and the pipeline/TUI source; two live sweep-driver runs — one `--dry-run`, one fake-executor `run_matrix` — captured verbatim)

## Summary

Phase 11 closes the operator loop by composing three proven seams: (1) the
**pure planning functions of `run_sweep.py` imported CPU-side** — live-probed:
`import run_sweep` costs 0.012s with ZERO torch/dnallm in `sys.modules`, and a
full 62×50×3 `enumerate_matrix` call costs 0.002s returning 9300 cells, so the
D-05 same-source preview and the D-02 E2' verdict are both trivially cheap and
need **zero pipeline refactor** (the `tui/__main__.py` bootstrap already puts
`REPO_ROOT/pipeline` on `sys.path`; `tui/services/registries.py` already
imports `pipeline/registry_loader` the same way); (2) the **phase-10 Popen
discipline** (`start_new_session`, LIST argv, `os.killpg` cancel, injectable
`_default_spawner` seam) reused verbatim for the detached `run_sweep.py`
launch; and (3) the **phase-8 frozen env-gate face**
(`quick_check.run_quick_check` + `env_gate.gate_verdict`) consumed unchanged.

Two discoveries change plan shape. First, **D-18's `--config-variant` threading
CANNOT be a pure PIPE-02-style pass-through**: `run_finetune.py` self-aliases
its save name under a variant (`{model}+probe` / `{model}+curve` / `{model}+head`
with the frozen evo2/megaDNA head exception) and writes its outputs under the
ALIAS dir, while the sweep driver keys `cell_dir_for` on the BASE name — a pure
pass-through would have every cell train successfully into `{root}/{model}+probe/...`
while the driver records it failed ("executor exited 0 but final_metrics.json
is missing") and re-attempts it forever. The correct shape is the **existing
`--peft` aliasing machinery** (cells enumerated under the alias, argv carrying
`--target_model <base>` + explicit `--save_model_name <alias>`), pinned by
argv-parity tests in the `tests/test_sweep.py` style. Second, the UI-SPEC's
PROBE_INELIGIBLE figure ("7 names") is stale: the frozen list in
`pipeline/run_finetune.py` has **9 names**, and because `run_finetune.py`
imports torch at module top the list is NOT importable CPU-side — the TUI must
read it as data via the established read-source-never-extract pattern (or a
small frozen extraction helper), never by import.

The D-04 smoke pick is decisive and evidence-backed: only **two** of the 62
models exist locally (`plant-dnabert-6mer` 89M, `plant-dnagpt-BPE` 92M), and
the smallest trainable task of all 50 is `iDNA_ABF_datasets__5mC`
(2110/234/2344 rows). This exact pair has a **prior real GB10 run in the tree**
— `final_metrics.json` records `train_runtime: 65.0438` seconds at 1 epoch with
`hardware: 'NVIDIA GB10'` in `flops_report.json` — so the SC5 smoke
(PEFT=none, variant=none, seed 42, 1 epoch) is a proven single-digit-minutes
cell, and seed 42 is untouched by the existing `seed_9527` resume markers
(seed-scoped markers never skip a different seed).

**Primary recommendation:** build three services (`run_config.py` compose +
preview + gate verdicts; `sweep_launcher.py` Popen/tee/exit lifecycle;
`sweep_monitor.py` discovery/scan/ETA), two screens (`run_config.py`,
`monitor.py`), a `run_sweep.py` `--config-variant` flag implemented via the
peft-aliasing pattern (NOT pass-through), and land the SC5 smoke as
plant-dnabert-6mer × iDNA_ABF_datasets__5mC × seed 42 × 1 epoch.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (D-01..D-19, copied verbatim)

- **D-01 (维护者裁定 B):** 槽 4 自带完整模型/数据集选择器,独立于槽 2 标记组合;选择状态 XDG 持久化;预览与启动只读本屏选择
- **D-02 (维护者裁定 A):** E2' 判定 = 干跑枚举比对全量(62 模型×50 数据集×3 种子);确认 = 完整输入本次输出目录名
- **D-03 (维护者裁定 A):** 监控附加 = 自动扫描默认输出根(finetuned/ 等,含 CLI 启动) + 手动输入输出路径
- **D-04 (维护者裁定 A):** SC5 冒烟选型由研究阶段实测定(最小模型×最小任务),写入计划供计划评审过目
- **D-05:** 干跑预览同源——导入 pipeline.run_sweep 纯规划函数(enumerate_matrix 等),绝不复制枚举逻辑;services 经 sys.path 根导入(pipeline/ 在路径),零 textual
- **D-06:** 执行恒为 run_sweep.py 子进程:LIST argv + PYTHONUNBUFFERED=1 + start_new_session 分离;TUI 退出三选 kill/detach/cancel,默认 detach;断点安全(trainer_state 标记天然恢复)
- **D-07:** E2' 三种子授权边界不可绕过:确认门在 TUI 呈现,但判定与短语校验使 UI 内部无法静默跳过(LNC-03)
- **D-08:** env_smoke 前置:FAIL 阻止启动并显示原因(消费相位 8 env_gate 冻结面,零改动)
- **D-09:** 监控节奏:2s 前沿扫描 + 60s 全扫;artifact-loader 容错(部分写跳拍,MON-01)
- **D-10:** 日志 tee 落盘:单一家 XDG logs 目录(与 state/config 一致);planner 可依实现细节微调但不得引入第二持久化根
- **D-11:** 失败重跑走 `--from-failures <sweep_failures.json>`,独立确认门;trainer_state.json 识别断点续跑(MON-03/05)
- **D-12:** 字符串前缀 CFG_/LNC_/MON_ 单一家 strings.py;CJK 锁与清单双向锁自动覆盖
- **D-13:** 槽 4→槽 5 启动后自动跳转:启动成功 toast + 自动导航监控屏(设计默认,计划评审确认)
- **D-14:** 项目/存储目录分离(CFG-02):输出根/数据集根/模型缓存三设置,默认仓库相对,显式覆盖传绝对路径
- **D-15:** 机器分工约束(维护者 2026-10-13):本机仅开发测试——冒烟上限 1-2 模型×3-4 数据集部分数据;全量 sweep 由其他机器执行,E2' 双重门控不变
- **D-16:** 9 相导航壳裁定延续:槽 4(运行配置)/槽 5(任务监控)本相位由占位变实屏;底栏左上下文命令右恒定 ? q
- **D-17 (维护者追加 2026-10-13):** 监控面板显示已用时 + 预估结束时间(ETA):已用时自 sweep 起点连续累计;ETA 依据已完成 cell 耗时的滚动中位数×剩余数(有分模型数据用分模型,否则全局),数据不足(<1 个完成 cell)诚实降级为"估算中…";显示带 ≈ 并在方差大时给出区间;出现在监控统计行与发现列表行
- **D-18 (2026-10-13):** 变体穿线:run_sweep 增加 `--config-variant` 直通旗标(PIPE-02 式增量管线改动,argv 奇偶校验钉死)——SC1 承诺变体控件全功能+执行恒为 run_sweep 的直接推论;UI-SPEC 开放问题 1 定案
- **D-19 (2026-10-13):** 数据集根混合方案:设置驱动 UI presence 检查+注册表侧绝对路径解析;本相位不加直通旗标(研究证实真实需要再议)——UI-SPEC 开放问题 2 定案;开放问题 3/4 归计划阶段(冒烟选型/ETA 方差常数)

### Requirements mapping (from CONTEXT `<requirements>`)

- CFG-01 全参数面 → 槽 4 参数区(种子 42/43/44 默认、PEFT+别名预览、变体 head/probe/curve+PROBE_INELIGIBLE、曲线档位、公平子集、epochs/batch、--effective_batch_size 自动 GA)
- CFG-02 目录分离 → D-14
- CFG-03 同源预览 → D-05,枚举 cell 数
- LNC-01/02/03 → D-06/07/08 + D-02
- MON-01..05 → 槽 5 看板 + D-03/09/10/11
- SC1-5 见 ROADMAP(逐字目标回溯锚)

### Phase boundary (from CONTEXT `<specifics>`)

- 相位边界:单 GPU 单 sweep;多 GPU 编排/分片属相位 12(hard gate:本相位验证通过)
- attach 模式对 CLI 启动 sweep 同效(D-03 扫描发现)
- 日志尾随 RichLog 有界;tee 落盘(D-10)

### Deferred Ideas (OUT OF SCOPE)

- 多 sweep 并行监控视图 → 相位 12 按需
- Web 进度镜像 → 相位 12 (WEB-01)
- 快照金丝雀 → 相位 12 (TEST-01)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CFG-01 | Full parameter surface (seeds/PEFT+alias/variant+PROBE_INELIGIBLE/curve tiers/fairness subset/epochs/batch/auto-GA) | run_sweep flag inventory + variant aliasing discovery (§ D-18); PROBE_INELIGIBLE 9-name data extraction seam (§ D-18) |
| CFG-02 | Project/storage dir separation, repo-relative defaults, absolute on override | run_sweep path-flag resolution precedent (D-15 absolute-before-threading); no dataset-root flag exists (D-19 hybrid confirmed) |
| CFG-03 | Same-source dry-run preview, enumerated cell counts | Live import probe: 0.012s import, 0.002s full enumeration, zero torch (§ D-05) |
| LNC-01 | Launch gate: env preflight blocking + terraform confirm + E2' typed phrase | env_gate/quick_check frozen signatures captured verbatim (§ Env Preflight); E2' predicate costed (§ E2') |
| LNC-02 | Execution always a run_sweep.py subprocess (LIST argv + PYTHONUNBUFFERED + start_new_session); exit kill/detach/cancel | Phase-10 Popen discipline reuse (§ Subprocess/tee/exit); resume-safety verified in source |
| LNC-03 | E2' full three-seed stays maintainer-authorized, TUI cannot bypass | Service-tier verdict + exact-match phrase check design (§ E2'); 9300-cell enumeration live cost |
| MON-01 | Cell-level states, seed-adjacent, 2s/60s scans, tolerant loader | run_record/manifest/failures schemas captured verbatim (§ Monitor Sources); in-flight churn signals observed in a real GB10 cell dir |
| MON-02 | Progress stats done/total/current/elapsed; attach for CLI-launched sweeps | Discovery predicate: manifest written only at sweep end (source-verified); stale-tree edge flagged (§ Monitor Sources) |
| MON-03 | Live failure list + gated `--from-failures` re-run | sweep_failures.json written only at END — live list must derive from run_records (§ Monitor Sources); failure schema verbatim |
| MON-04 | Bounded log tail + tee persistence | run_sweep stdout shape captured live (§ Subprocess/tee/exit); XDG logs root = state_dir()/logs |
| MON-05 | Resume recognition from trainer_state.json markers | RESUME_MARKER constant importable; skip logic + WR-12 no-overwrite read from source |
| SC1-5 | ROADMAP success criteria | SC5 smoke pick proposed with numbers (§ D-04 Smoke Pick); SC1 variant control enabled by the D-18 aliasing design |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Run-spec composition + XDG persistence | TUI service (`tui/services/run_config.py`, new) | `settings.state_dir()/atomic_write` | Pure state; D-01 rules slot-4-owned selection; settings already owns atomic writes [VERIFIED: tui/services/settings.py:44,90-107] |
| Dry-run preview / cell counting | imported `pipeline.run_sweep.enumerate_matrix` | `tui/services/run_config.py` wrapper | D-05 same-source; zero-copy; live-probed import cost 0.012s, zero torch [VERIFIED: live probe this session] |
| E2' verdict + typed-phrase check | TUI service (pure function) | official-only registry key sets | D-07: the boundary lives in the service tier, never a widget path |
| Env preflight | `tui/services/quick_check.py` + `env_gate.py` (frozen, zero-change) | — | Phase-8 frozen face; docstrings literally say "Phase 11 blocks on it" [VERIFIED: tui/services/env_gate.py:63-66, quick_check.py:7-9] |
| Sweep execution | `run_sweep.py` detached subprocess | `tui/services/sweep_launcher.py` spawn/tee/kill lifecycle | D-06: never in-process; phase-10 `_default_spawner`/`_signal_group` precedent [VERIFIED: tui/services/download_queue.py:698-712, 870-876] |
| Per-cell training | `run_finetune.py` (child of run_sweep) | — | Out of TUI scope entirely; GPU lane |
| Monitor discovery/scan/ETA | TUI service (`tui/services/sweep_monitor.py`, new) | tolerant JSON readers | D-03/D-09/D-17; pure over the artifact tree, tier-1 testable with fake trees |
| PROBE_INELIGIBLE data | `pipeline/run_finetune.py` source (read, never imported) | TUI service extraction helper | torch at module top makes import impossible CPU-side; read-source-never-import is the established pattern [VERIFIED: tests/test_run_finetune_contracts.py:8-12] |
| Rendering / gates / modals | screens (`tui/screens/run_config.py`, `monitor.py`, new) | strings.py CFG_/LNC_/MON_ | Screens render, never compute; zero constants exist today (grep-verified) |
| Nav promotion + quit intercept | `tui/screens/nav.py` slots 4/5, `tui/app.py` action_quit override | — | NAV_SLOTS placeholders at [VERIFIED: tui/screens/nav.py:82-88]; `q`→"quit" binding at [VERIFIED: tui/app.py:250-253] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| textual | 8.2.8 (uv.lock-pinned) | TUI framework | Phase 8-locked; UI-SPEC enumerates from the installed package; zero new deps this phase |
| platformdirs | 4.13.0 | XDG state/config roots | `settings.state_dir()` already wraps it; tee logs root joins the same family (D-10) |
| Python stdlib `subprocess` | 3.13 | Popen spawn, start_new_session, killpg | Phase-10 discipline; no psutil |
| `pipeline/run_sweep.py` (in-repo) | current (Phase-7 final) | Pure planning imports + the execution subprocess | D-05/D-06; stdlib-only, headless-importable [VERIFIED: live import probe] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest (+pytest-asyncio) | existing | tier-1 service tests + tier-2 Pilot | All CPU lanes; fake-executor + fake-tree fixtures |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Importing run_sweep planning functions | Re-implementing enumeration in the service | Rejected by D-05 (same-source or it does not exist); also unnecessary — import is clean |
| Importing PROBE_INELIGIBLE from run_finetune | — | IMPOSSIBLE CPU-side (module-top `import torch`); read-source extraction instead |
| Pure pass-through `--config-variant` (D-18 wording) | — | WRONG SHAPE — child self-aliases output dirs; must use the peft-aliasing pattern (§ D-18) |

**Installation:** NONE. Zero new dependencies (UI-SPEC Registry Safety: "New dependency surface in Phase 11: none").

## Package Legitimacy Audit

No packages are installed by this phase. No new external packages are imported;
`run_sweep.py` is in-repo. The audit is therefore vacuous.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| — (none installed) | — | — | — | — | — | — |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Research Area 1: D-04 Smoke Pick (SC5) — DECIDED with evidence

**Confidence: HIGH** (every number below read from disk or the registries this session)

### The local-model constraint (the deciding fact)

Only TWO of the 62 registry models exist on disk under `pipeline/models/`:

```
plant-dnabert-6mer    size (M): 89    Model_path: models/plant-dnabert-6mer
plant-dnagpt-BPE      size (M): 92    Model_path: models/plant-dnagpt-BPE
```

[VERIFIED: `ls pipeline/models/` + `pipeline/models_info.json` entries — fields
`"Model_path": "models/plant-dnabert-6mer"`, `"size (M)": 89` /
`"size (M)": 92`; registry total = 62 keys]. The committed tier-1 priority pair
(plant-dnamamba-6mer × PlantCAD2 cross_species_leaf_on_off_translation) is NOT
local — only other sweep machines hold those weights, so the pick must come
from the two local models.

### The smallest task

Ranked by total rows over all 50 trainable tasks (all 50 `datasets_info.json`
entries have truthy `Train` — verified: 50 entries, 50 truthy):

| rank | task | Train/Dev/Test | total | on disk |
|------|------|----------------|-------|---------|
| 1 | `iDNA_ABF_datasets__5mC` | 2110/234/2344 | 4688 | ✓ `pipeline/datasets/iDNA_ABF_datasets/5mC/{train,dev,test}.csv` |
| 2 | `GUE__virus_species_40` | 4000/500/500 | 5000 | ✓ |

[VERIFIED: computed over `pipeline/datasets_info.json` this session — 5mC row:
`{'Dataset_name': 'iDNA_ABF_datasets__5mC', 'Dataset_path': 'datasets/iDNA_ABF_datasets/5mC', 'Dev': 234, 'Test': 2344, 'Train': 2110, 'metric': 'f1'}`]
Dataset presence: `dnallm-mark/data/n_audit.json` reports **0 missing** (50/50),
5mC included (`"missing": false`, dev rows 234).

### THE PICK

**`plant-dnabert-6mer × iDNA_ABF_datasets__5mC`, seed 42, `--num_train_epochs 1`, PEFT none, variant none.**

- **Smallest local model** (89M < 92M) × **smallest trainable task** of all 50 (4688 total rows).
- **Runtime class: single-digit minutes.** This exact pair has a prior real run
  on THIS machine — `pipeline/finetuned/plant-dnabert-6mer/iDNA_ABF_datasets__5mC/seed_9527/final_metrics.json`
  records verbatim `"train_runtime": 65.0438` (1 epoch, 528 steps) and
  `flops_report.json` records `"hardware": {'gpu_device': 'NVIDIA GB10',
  'max_mem_gb': 1.5587153434753418, 'train_time': 65.0438}`; the cell-dir file
  mtimes span 15:49:40 → 15:50:48 (~68s). Add model load + FLOPs calibration +
  eval + artifact writes ⇒ ~2-3 minutes wall per cell on GB10.
- **Resume-marker interplay: none.** The existing marker is `seed_9527` and
  seed-scoped (a different seed never skips — run_sweep.py:1310-1313 skip check
  reads the per-seed `trainer_state.json`). Seed 42 runs clean even under the
  default root; the SC5 sweep will enumerate exactly one never-run cell.
- **PROBE_INELIGIBLE interplay: none.** `plant-dnabert-6mer` is not in the
  9-name frozen list; the smoke uses variant none regardless.
- **Smoke spec for the plan (D-15-compliant):** TUI-compose
  `--models plant-dnabert-6mer --tasks iDNA_ABF_datasets__5mC --seeds 42
  --num_train_epochs 1` (optionally a dedicated output root such as
  `./finetuned-smoke` if the plan wants the monitor discovery story isolated;
  both work — plan-owned).

Runner-up context (if the maintainer wants the failure-re-run leg exercised in
the same smoke): a second task (`GUE__virus_species_40`, +5000 rows ≈ +2-3 min)
or an intentional poison cell would exercise MON-03 end-to-end; D-15's bound
("1-2 模型×3-4 数据集部分数据") leaves room, but the minimal 1×1×1 pick above
is the recommendation.

## Research Area 2: The Pure-Planning Import Seam (D-05) — VERIFIED live, zero refactor

**Confidence: HIGH**

### Module-top imports (no torch anywhere in the chain)

[VERIFIED: pipeline/run_sweep.py:239-247 — verbatim:
`import argparse`, `import functools`, `import json`, `import subprocess`,
`import sys`, `from datetime import UTC, datetime`, `from pathlib import Path`,
`import registry_loader  # sibling module`]
`registry_loader.py` imports only `json`, `os`, `pathlib` [VERIFIED:
pipeline/registry_loader.py:53-55]. `run_sweep.py`'s own docstring pins the
contract: "this module stays stdlib-only and headless-importable".

### Live probe (repo venv, `python -I`, cwd=repo root)

```
sys.path.insert(0, 'pipeline'); import run_sweep
import run_sweep: 0.012s
torch loaded: False
dnallm loaded: False
```

Function shapes captured verbatim:

```
run_sweep.enumerate_matrix(['plant-dnabert-6mer'], ['GUE__emp_H3'], [42], 'pipeline')
  -> [('plant-dnabert-6mer', 'GUE__emp_H3', 42)]        # TUPLES, not dicts;
                                                        # 4-tuples under fractions
run_sweep.build_argv('plant-dnabert-6mer', 'GUE__emp_H3', 42, '/abs/finetuned')
  -> ['/home/forrest/Github/dnallmmark/.venv/bin/python',
      '/home/forrest/Github/dnallmmark/pipeline/run_finetune.py',
      '--target_model', 'plant-dnabert-6mer',
      '--target_dataset', 'GUE__emp_H3',
      '--seed', '42',
      '--output_dir', '/abs/finetuned']

run_sweep.build_argv('plant-dnabert-6mer+lora', ..., peft='lora',
                     subset_file='/abs/subset.json', effective_batch_size=16,
                     num_train_epochs=1, cache_dir='/abs/cache')
  -> [... '--save_model_name', 'plant-dnabert-6mer+lora', '--peft', 'lora',
      '--subset_file', '/abs/subset.json', '--effective_batch_size', '16',
      '--num_train_epochs', '1', '--cache_dir', '/abs/cache']

run_sweep.cell_dir_for('/root', 'm+t', 'T', 42, 0.25)
  -> '/root/m+t/T/seed_42/frac_0.25'
```

Cost of a full enumeration: **0.002s for 9300 cells** — the preview worker and
the gate's independent recompute are both effectively free.

### The sys.path seam already exists everywhere it is needed

- `tui/__main__.py` bootstraps `REPO_ROOT/pipeline` onto `sys.path` BEFORE any
  tui import [VERIFIED: tui/__main__.py:5-6,15-18 — "`pipeline/` is a sys.path
  root, not a package ... so `REPO_ROOT/pipeline` must be on sys.path before"].
- `tui/services/registries.py` already imports `pipeline/registry_loader` through
  it [VERIFIED: tui/services/registries.py:24-28, 111], and
  `tui/services/__init__.py` documents the one-directional contract.
- Tests: parent `tests/conftest.py:44` inserts `pipeline/` ("run_sweep
  (stdlib-only sweep driver)" — verbatim comment); `tests/tui/conftest.py`
  adds the repo root. Nothing new needed for tests either.
- The services-textual-free import lock [VERIFIED:
  tests/tui/test_import_lock.py — ast-walk over `tui/services/*.py`] covers the
  new modules automatically (glob-based).

**Conclusion: import-inside-function refactors are NOT needed.** A
`tui/services/*` module doing `import run_sweep` (module-level or
function-level) is CPU-safe today.

### Operator-input file formats (for the plan's parsing references)

- `load_failure_pairs(path, registry_dir)` → `set[tuple[str, str]]` of
  **(BASE model, task)** pairs; validated fail-fast; joins on `base_model`
  with legacy alias-suffix strip fallback [VERIFIED: pipeline/run_sweep.py:856-944].
- `sweep_failures.json` entry schema (live-captured verbatim from a real
  failing fake-executor run):
  ```json
  {
      "base_model": "plant-dnabert-6mer",
      "error": "CalledProcessError: Command '['fake']' returned non-zero exit status 3.",
      "model": "plant-dnabert-6mer",
      "output_dir": "/tmp/sw-fail/plant-dnabert-6mer/iDNA_ABF_datasets__5mC/seed_42",
      "seed": 42,
      "task": "iDNA_ABF_datasets__5mC"
  }
  ```
- `load_priority_tiers(path, registry_dir)` → `list[list[tuple[model, task|None]]]`;
  committed instance `pipeline/sweep_priorities.json` (verbatim):
  `[[{"model": "plant-dnamamba-6mer", "task": "PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation"}, {"model": "PlantHelixSeek", "task": "...same..."}], ["GENERanno-eukaryote-0.5b-base", "PlantCAD2-Small-l24-d0768", "Omni-DNA-700M"]]`.
  NOT surfaced in the TUI this phase (UI-SPEC auto-default #18).
- Importable name constants: `MANIFEST_NAME = "sweep_manifest.json"`,
  `FAILURES_NAME = "sweep_failures.json"`, `RECORD_NAME = "run_record.json"`,
  `RESUME_MARKER = "trainer_state.json"`, `METRICS_NAME = "final_metrics.json"`
  [VERIFIED: pipeline/run_sweep.py:252-256 — the monitor service should import
  these rather than re-typing the strings].

## Research Area 3: D-18 `--config-variant` Threading — the shape is ALIASING, not pass-through

**Confidence: HIGH** (evidence); the implementation shape recommendation is
plan-owned but strongly constrained by the evidence below.

### The child flag (exists, exact choices)

[VERIFIED: pipeline/run_finetune.py:239-242 — verbatim argparse:
`"--config-variant"`, `type=str`, `default=None`,
`choices=["head", "probe", "curve"]`]
[VERIFIED: pipeline/run_finetune.py:504-508 — verbatim:
`VARIANT_CONFIGS = {"head": "./finetune_config_with_head.yaml",
"probe": "./finetune_config_probe.yaml", "curve": "./finetune_config_curve.yaml"}`
loaded at the special_models reload slot (`configs = load_config(VARIANT_CONFIGS[config_variant])`, line 968)].

### THE CRITICAL DISCOVERY — the child self-aliases its output dir

[VERIFIED: pipeline/run_finetune.py:1194-1209 — verbatim naming chain:]

```python
save_root = output_dir if output_dir else "./finetuned"
if save_model_name:
    model_save_name = save_model_name
elif peft_mode != "none":
    model_save_name = f"{model_name}+{peft_mode}"
elif config_variant == "probe":
    model_save_name = f"{model_name}+probe"
elif config_variant == "curve":
    model_save_name = f"{model_name}+curve"
elif config_variant == "head" and model_name not in (
    "evo2_1b_base", "megaDNA_updated"
):
    model_save_name = f"{model_name}+head"
else:
    model_save_name = model_name
outdir = f"{save_root}/{model_save_name}/{dataset_name}/seed_{seed}/"
```

The prior smoke tree proves the alias layout on disk:
`pipeline/finetuned/plant-dnabert-6mer+probe/iDNA_ABF_datasets__5mC/seed_9527/`
and `.../plant-dnabert-6mer+lora/.../seed_9527/` both exist.

**Why a pure PIPE-02-style pass-through is wrong:** `run_sweep.build_argv`
threads `--output_dir {root}` and `cell_dir_for` keys records/markers on
`{root}/{model}/...` — the BASE name. Under a naive pass-through the child
writes `final_metrics.json` under `{root}/{model}+probe/...` while the driver
looks in `{root}/{model}/...`: every cell "succeeds" and is then recorded
**failed with "executor exited 0 but final_metrics.json is missing"** and
re-attempted forever (the CR-02 failure boundary). This is a retrain-forever
bug class, not a cosmetic one.

**Correct shape (mirrors the `--peft` machinery exactly, 06-02 precedent):**

1. argparse: add `--config-variant` (same choices) after the `--cache_dir`
   block [insertion point: pipeline/run_sweep.py:393-401].
2. `enumerate_matrix` gains the alias rule: cell model name becomes
   `{model}+{variant}` for probe/curve, `{model}+head` for head EXCEPT the
   frozen pair `("evo2_1b_base", "megaDNA_updated")` (keeps base — its
   with-head config IS its base config). Variant and peft never compose
   (child refuses probe×peft — see below), so the alias axes are disjoint.
3. `build_argv` appends `--config-variant <v>` AND threads an explicit
   `--save_model_name <alias>` — the child's "explicit --save_model_name
   always wins" branch (line 1190) then makes the DRIVER the single naming
   authority; the child's own aliasing never diverges.
4. `run_record.json` gains a `config_variant` field (the `peft`-field
   precedent, run_sweep.py:1151-1161); the alias identity keeps
   `trainer_state.json` resume isolation exactly like peft aliases.
5. The head-exception pair (2 names) is frozen in run_sweep with a parity
   test against the run_finetune source text (read-source-never-import — see
   PROBE_INELIGIBLE below for the pattern).

**Child-side refusals already implement the composition guards (zero driver
work needed):**

- probe × peft: [VERIFIED: pipeline/run_finetune.py:775-789 — fail-fast at the
  argv boundary, verbatim: `"[Error] --config-variant probe refuses --peft
  {peft_mode}: the frozen-probe lane trains a head on a frozen backbone ..."`]
- probe × PROBE_INELIGIBLE: [VERIFIED: pipeline/run_finetune.py:795-812 —
  fail-fast naming the models, BEFORE any model load]. A bad TUI composition
  therefore fails per-cell in seconds (no GPU burn), but the TUI should still
  mirror both refusals as preview problems (cheap composition-time prevention;
  the child stays authoritative).

### PROBE_INELIGIBLE — 9 names, not 7, and NOT importable

[VERIFIED: pipeline/run_finetune.py:527-537 — verbatim frozen list:]

```python
PROBE_INELIGIBLE = [
    "enformer-official-rough",  # enformer dedicated loader (suite special/enformer.py via model.py:1196-1204)
    "SPACE",                    # UPPERCASE registry row (models/SPACE): native space_models member "SPACE" claims it case-sensitively (suite special/space.py via model.py:1207-1215)
    "space",                    # lowercase registry row (models/space): claimed via the extra self-append ("space" in path.lower()) — the same dedicated loader (suite special/space.py via model.py:1207-1215)
    "borzoi-replicate-0",       # borzoi dedicated loader (suite special/borzoi.py via model.py:1218-1226)
    "flashzoi-replicate-0",     # borzoi-family flashzoi loader (suite special/borzoi.py via model.py:1218-1226)
    "evo2_1b_base",             # evo2 own-head branch (suite special/evo.py via model.py:1170-1172)
    "megaDNA_updated",          # megaDNA own-head branch (suite special/megadna.py via model.py:1183-1185)
    "gpn-brassicales",          # gpn special loader (suite special/gpn.py via model.py:1180)
    "Omni-DNA-700M",            # omnidna special loader (suite special/omnidna.py via model.py:1193)
]
```

- **The UI-SPEC's "7 names" is stale — flag at plan review** (the copy
  `CFG_VARIANT_PROBE_HINT` takes `{models}` dynamically so the string table is
  unaffected; only the count claim in the spec prose is wrong).
- **Import is impossible CPU-side:** run_finetune.py module-top imports
  `import torch` (line 43) and `from dnallm import ...` (line 64)
  [VERIFIED: pipeline/run_finetune.py:41-64]. The UI-SPEC's "imported from
  pipeline/run_finetune.py (data ...)" must be realized as **read-source
  extraction**: read the file text, regex/ast-extract the `PROBE_INELIGIBLE =`
  literal — the exact pattern `tests/test_run_finetune_contracts.py` uses
  ("read as SOURCE TEXT and never imported", with `exec(match.group(0),
  namespace)` for pure fragments) [VERIFIED:
  tests/test_run_finetune_contracts.py:8-12, 771, 851, 871]. A ~15-line
  service helper with a parity test against the frozen list is the honest
  seam; NEVER duplicate the names in strings.py (the spec's rule stands).

### argv-parity test template (D-18's "argv 奇偶校验钉死")

The PIPE-02 precedent in `tests/test_sweep.py`:
`test_launch_subprocess_builds_argv_list_with_pinned_cwd` (line 515) monkeypatches
`subprocess.run`, captures the argv, asserts LIST-ness + every flag via the
`flag_value(argv, flag)` helper (line 175: "Return the argv element immediately
following ``flag``"). The 07-03 pass-through suite extends the same idiom
(absent flag ⇒ zero elements, D-12 parity). The D-18 tests copy this shape:
alias present in argv + `--save_model_name` + cell dir under the alias + absent
variant ⇒ byte-identical argv; head × the frozen pair ⇒ base name.

## Research Area 4: Monitor Data Sources (MON-01/02/05, D-17)

**Confidence: HIGH** (schemas live-captured; churn signals observed in a real GB10 cell)

### run_record.json — schema (live-captured verbatim from a real fake-executor run)

Written by the driver at `{output_root}/{model}/{task}/seed_{seed}/run_record.json`
(+ `frac_{f}` nesting under curve). Verbatim completed record:

```json
{
    "error": null,
    "finished_at": "2026-10-13T00:47:23.018982+00:00",
    "git_commit": "77d4b86a257828557d0cf99bfcaae31b6b62db88",
    "metrics": { "eval_f1": 0.91 },
    "model": "plant-dnabert-6mer",
    "output_dir": "/tmp/sw-fake/plant-dnabert-6mer/iDNA_ABF_datasets__5mC/seed_42",
    "peft": "none",
    "seed": 42,
    "started_at": "2026-10-13T00:47:23.018801+00:00",
    "status": "completed",
    "task": "iDNA_ABF_datasets__5mC",
    "train_fraction": null,
    "vram_probe": {
        "batch_size": null,
        "gpu_mem_total": null,
        "gradient_accumulation_steps": null,
        "init_max_mem": null
    }
}
```

Field semantics [VERIFIED: pipeline/run_sweep.py:23-39 docstring + 1151-1181
`_new_record` + 1382-1394 write site]:
- `status` ∈ `"completed" | "failed" | "skipped"` (driver) / `"planned"`
  (dry-run manifest only).
- `metrics` = the cell's `final_metrics.json` VERBATIM (suite-native keys).
- `started_at`/`finished_at` ISO-8601 UTC — the D-17 elapsed/ETA inputs.
- `peft` marks the alias mode; the TUI should thread the same field for
  `config_variant` (D-18).
- **Timing: the record file is written only AFTER the cell finishes**
  (`_write_json(record_path, record)` at line 1394, after `finished_at` is
  set) — a RUNNING cell has NO run_record.json yet. WR-12: a skipped cell
  never overwrites an existing record.

### Output tree layout

```
{output_root}/
  sweep_manifest.json          # written ONLY at sweep END (line 1403) or dry-run
  sweep_failures.json          # written ONLY at sweep END (line 1410), always (WR-06)
  {model}[/+lora|/+ia3]/       # alias via base_model_name identity
    {task}/
      seed_{seed}/
        run_record.json        # post-cell (driver)
        trainer_state.json     # resume marker (child, final act — WR-13)
        final_metrics.json     # child, written BEFORE the marker (WR-13)
        flops_report.json      # child
        runs/                  # tensorboard dir — appears at cell START
        checkpoint-{step}/     # HF checkpoints — appear DURING training
        frac_{f}/...           # curve nesting
```

### How "running" is detectable

- **TUI-launched:** the owned Popen is alive (`poll() is None`) — the
  phase-10 discipline.
- **CLI-launched (mtime frontier):** between scans, (a) NEW seed dirs appear
  (the driver `cell_dir.mkdir(parents=True, exist_ok=True)` runs BEFORE the
  executor — line 1315), (b) `runs/` and `checkpoint-*/` dirs appear inside
  the current cell (observed in the real GB10 cell: `runs` at 15:49:40,
  `checkpoint-520` at 15:50:42, `checkpoint-528` at 15:50:45), (c) new
  run_record.json files land as cells complete. No single file updates
  continuously; the frontier = newest mtime/newest entries across the tree.
- **Finished:** `sweep_manifest.json` present at the root (written only after
  the loop — UI-SPEC auto-default #11 confirmed in source). Manifest cell
  shape (live verbatim): `{"model": ..., "output_dir": ..., "seed": 42,
  "status": "completed", "task": ...}` (+ present sweep_flags merged, D-13);
  dry-run manifests carry `"status": "planned"` — distinguishable.
- **The stale-tree edge (flag for plan):** `pipeline/finetuned` TODAY holds
  prior standalone-run artifacts with NO manifest and NO churn (the seed_9527
  tree). UI-SPEC #11's binary (manifest ⇒ finished / churn ⇒ running) leaves
  this state undefined. Recommend an explicit third rendering (artifacts-only
  row: 总数未知, no ●) or an age threshold — plan-owned refinement, listed in
  Open Questions.

### sweep_failures.json — write site + the live-list seam

[VERIFIED: pipeline/run_sweep.py:1405-1410 — `_write_json(output_root /
FAILURES_NAME, failures)` AFTER the cell loop, on every run, empty list when
clean (WR-06)]. Consequence: **for a RUNNING sweep the failures file does not
exist yet** (or is stale from a previous run at the same root). The live
failure list must derive from `run_record.json` files with
`"status": "failed"` (each lands as its cell fails); the `[f]` modal's
sweep_failures.json title is exact for finished sweeps and should present the
record-derived view while running (the entry shapes carry the same
model/task/seed/error identity). Flag for the plan (MON-03 wording says
"实时显示" — the records ARE the live source).

### Elapsed + ETA inputs (D-17)

- Elapsed: earliest `started_at` across the root's run_records ("—" before the
  first record lands — UI-SPEC stats contract).
- ETA: per-cell duration = `finished_at − started_at` wall-clock per completed
  record; rolling median (skipped records excluded — ~zero duration biases the
  median); per-model median where ≥1 cell of that model completed, global
  otherwise; honest `估算中…` before the first completion. All pure functions
  over the record scan — tier-1 testable with fake trees.

## Research Area 5: E2' Verdict Computation (D-02/D-07)

**Confidence: HIGH**

- **Cost (live):** `enumerate_matrix(None, None, [42,43,44], pipeline)` →
  9300 cells in **0.002s**. The gate's independent recompute is free; even
  doing it on every selection change (preview) is free.
- **"Full" definition (recommendation, matching the D-02 62×50×3 wording):**
  the enumeration covers ALL **official** models × ALL **official trainable**
  tasks × **≥3 seeds**. Official-only key sets = a direct `json.load` of
  `pipeline/models_info.json` (62 keys) and `pipeline/datasets_info.json`
  (50 keys, all truthy `Train` — both counts verified live) — NOT the
  `registry_loader` overlay view (which merges custom entries into the same
  enumeration). Custom-overlay keys selected ⇒ NEVER E2' (UI-SPEC
  auto-default #9). Compare on BASE names (strip aliases via
  `run_sweep.base_model_name`).
- **Predicate:** `models_base ⊇ official_62 AND tasks ⊇ official_50 AND
  len(seeds) >= 3` (an enumeration larger than official — overlay keys added —
  still satisfies ⊇; if the plan wants strict equality instead, that is a
  one-line tightening — flag at plan review. Recommendation: keep ⊇ so a
  custom+full mix still escalates to the typed gate; the phrase exists
  precisely because the run includes the full re-run).
- **Typed phrase:** the final path component of the operator-set output root
  (`Path(output_root).resolve().name`), typed in full; the exact-match check
  lives in the service tier (D-07) and gates the `[enter]确认` live state.

## Research Area 6: Env Preflight (D-08) — frozen face, zero change

**Confidence: HIGH**

- `tui/services/quick_check.py` — [VERIFIED verbatim:
  `QUICK_CHECK_KERNEL_IDS = ("version_pins", "dnallm", "peft", "cuda",
  "numpy", "dataset_dirs")`; `def run_quick_check(kernels=None) ->
  list[CheckResult]` — injectable kernel sequence (CI fakes), nothing
  persisted].
- `tui/services/env_gate.py` — [VERIFIED verbatim:
  `def gate_verdict(results: Sequence[CheckResult]) -> GateVerdict` returning
  the frozen dataclass:
  `GateVerdict(can_launch: bool, reasons: tuple[str, ...], route_to_data: bool)`
  — reasons are "the failing CRITICAL kernels' detail lines, in main() kernel
  order — exactly what the operator needs to read when launch is blocked"].
  The docstrings literally pre-announce this phase: "Phase 11's launch screen
  blocks on it" [env_gate.py:63-66] and "a launch pre-flight's (D-09 /
  ENV-04)" [quick_check.py:7-9].
- `CheckResult` fields [VERIFIED: pipeline/env_smoke.py:83-107]:
  `name (str)`, `ok (bool)`, `lines (tuple[str, ...])` — the env-block modal
  renders `reasons` verbatim in a bounded RichLog.
- **Zero-change confirmation:** both services need NO edits; the launch gate
  calls them exactly as the phase-8 tests already exercise them. The only
  env-screen change in the phase is the `ENV_VERDICT_CRITICAL_FAIL` value
  amendment (UI-SPEC Existing-Surface Amendments).

## Research Area 7: Subprocess / tee / exit (D-06/D-10)

**Confidence: HIGH**

### run_sweep stdout shape (live-captured verbatim — the tee/RichLog fixture seed)

Dry-run (real run, repo venv, PYTHONUNBUFFERED=1):

```
[Dry-run] 1 planned cell(s) over 1 model(s) x 1 task(s) x 1 seed(s); manifest: /tmp/sw-dry/sweep_manifest.json
```

Real run: `run_matrix` itself is SILENT per cell (the child's stdout/stderr
inherit the driver's — timestamped `print(f"[{current_time}] ...")` lines from
run_finetune); the driver prints only, verbatim [VERIFIED:
pipeline/run_sweep.py:1624-1630]:

```
Sweep finished: {n} cell(s) — {c} completed, {s} skipped, {f} failed; manifest: {output_root}/sweep_manifest.json
Failures recorded in: {output_root}/sweep_failures.json     # only when failed
```

plus, when `--from-failures` is used, a leading `[From-failures] ...` line
(lines 1560-1573). Tail-friendly: a continuous line stream — ideal for the
bounded RichLog tail over the tee file.

### Launch mechanics (locked by D-06/LNC-02, mechanics verified in source)

- `Popen(LIST argv, start_new_session=True, cwd=PIPELINE_DIR,
  env={**os.environ, "PYTHONUNBUFFERED": "1"}, stdout=tee_file,
  stderr=STDOUT)` — argv = `[sys.executable, str(REPO_ROOT/"pipeline"/"run_sweep.py"),
  "--models", ..., "--tasks", ..., "--seeds", ..., "--output-root", ...,
  "--dry-run-absent flags per D-12 parity]`. PYTHONUNBUFFERED=1 is load-bearing:
  with a pipe/file destination Python block-buffers stdout; the env var makes
  the tee see each line promptly.
- cwd pinned `pipeline/` (the driver itself resolves paths; pinning matches
  its documented "run from the repo root" contract and keeps relative
  `--output-root ./finetuned` resolving repo-relative — D-14's default).
- Spawner injection: copy the `_default_spawner(argv, **kwargs)` seam shape
  [VERIFIED: tui/services/download_queue.py:698-712].

### Tee target (D-10)

Single XDG logs root: `settings.state_dir()/logs/` (~/.local/state/dnallmmark/logs/
— the UI-SPEC auto-default #16 naming; REQUIREMENTS MON-04's older
"~/.config/dnallmmark/logs/ 或任务输出目录" wording is superseded by D-10's
"与 state/config 一致" ruling). Proposed filename (plan-owned):
`sweep_{YYYYmmdd_HHMMSS}_{rootname}.log` — one file per launch, `{rootname}`
= the output-root basename (the E2' phrase identity, making the log
self-describing). `MON-04`'s "或任务输出目录" alternative would violate D-10's
single-root rule — do not offer it.

### Exit semantics (D-06)

- **kill** = `os.killpg(os.getpgid(proc.pid), signal.SIGTERM)` with SIGKILL
  escalation — the `_signal_group` precedent [VERIFIED:
  tui/services/download_queue.py:870-876]. `start_new_session` at launch makes
  the whole child tree one process group (run_sweep → run_finetune children).
- **detach** = drop the handle (no wait, no kill). Resume-safe: the
  `trainer_state.json` marker makes re-attachment/resume exact —
  [VERIFIED: pipeline/run_sweep.py:1310-1313 — the per-seed marker skip; and
  run_finetune's own seed-scoped resume check]. A detached sweep keeps running
  as an orphaned session leader; the monitor re-discovers it via D-03 scanning
  (churn) and the manifest at end.
- **cancel** = close the modal, nothing happens.

## Research Area 8: Test Strategy

**Confidence: HIGH** (pattern-matched to the phase-10/8 layout read this session)

### Tier-1 (services, pure/fake — CI CPU)

- `tests/tui/test_services_run_config.py` — NEW. Analog:
  `test_services_download_queue.py`. Covers: import purity (importing the
  service leaves torch/dnallm absent — the live-probe assertion codified);
  preview counting via imported `enumerate_matrix` (tuple shapes, curve
  expansion, peft/variant aliasing); E2' verdict predicate (official 62×50×≥3;
  custom keys never trigger; alias stripping); typed-phrase exact-match in the
  service; PROBE_INELIGIBLE read-source extraction (against a fixture source
  AND the real file); argv composition for launch (LIST, PYTHONUNBUFFERED,
  cwd, tee path) with an injected fake spawner; gate ordering (enumeration →
  env preflight → confirm/E2'); XDG persistence round-trip.
- `tests/tui/test_services_sweep_monitor.py` — NEW. FakeSweepScanner over
  synthetic trees in tmp dirs: discovery predicate (manifest ⇒ finished,
  churn/Popen ⇒ running, stale artifacts edge); run_record tolerant parsing
  (truncated JSON skipped, last-known-good retained — the phase-10
  ROADMAP-binding tolerant-loader contract); done/total + ⊘ resume counting;
  ETA median/per-model/range/`估算中…` degradation; failure derivation from
  records while running; timer-based scans with injected cadence (no real
  sleeps).
- `tests/test_sweep.py` — EXTEND (pipeline side, D-18):
  `--config-variant` argv parity (alias + `--save_model_name` +
  `--config-variant` elements; absent ⇒ zero elements), alias cell dirs,
  run_record field, head frozen-pair exception parity vs the run_finetune
  source text, probe×peft composition surfaced (or documented child-side).

### Tier-2 (Pilot, real App + injected fakes)

- `tests/tui/test_pilot_run_config.py` — NEW. Analog:
  `test_pilot_data_manager.py` (constructor-injected deterministic fakes; no
  real kernel/subprocess). Screens render at 120×40 and 80×24; picker/params/
  dirs rows; preview line recompute on selection change; `[p]` modal argv
  verbatim; gate pipeline modals incl. the E2' typed input (mismatch→match
  indicator, enter live only on match); launch toast + auto-nav to slot 5.
- `tests/tui/test_pilot_monitor.py` — NEW. Discovered table + cell table over
  a fake monitor service; attach flow (`◆` moves); `[f]` failure modal +
  gated re-run routing through the same launch pipeline; `[t]` log tail over
  a fake tee file + the CLI-sweep unavailable state; `[r]` rescan toast;
  stats line variants (known/unknown total, `估算中…`); ExitModal
  kill/detach/cancel paths; `q`-intercept wiring at app level.

CI stays GPU/network-free: every subprocess is a fake spawner or a
`sleep`-shaped test double; the GB10 smoke is a **documented maintainer
procedure** (D-15 bounds; the SC5 1×1×1×1epoch pick from Area 1), not a CI
lane. The services-textual-free import lock auto-extends over the new
modules; the strings grep lock (no Chinese literals outside strings.py in
`tui/screens/`/`tui/app.py`) extends to the new screens (D-12).

## Architecture Patterns

### System Architecture Diagram

```text
 slot 4 运行配置 (RunConfigScreen, NEW)
   ├─ pickers (own state, XDG-persisted, D-01) ── params pane (CFG-01) ── dirs (CFG-02/D-14)
   ├─ preview worker (@work thread): service → import run_sweep.enumerate_matrix/build_argv
   │        (sys.path root import; 0.012s import / 0.002s full enumeration — live-probed)
   │        → preview line + [p] modal (argv verbatim, collect-all problems)
   └─ [enter] 启动门 (LaunchGateModal — service-tier pipeline, every step recomputed):
        1. same-source enumeration + collect-all problems   (blocked on problems)
        2. env preflight: quick_check.run_quick_check → env_gate.gate_verdict   (frozen face)
              FAIL ⇒ env-block modal (reasons verbatim) — launch blocked (D-08)
        3. non-E2' ⇒ ConfirmModal | E2' (models⊇62 ∧ tasks⊇50 ∧ seeds≥3, official-only
              key sets) ⇒ typed-phrase gate: exact match on output-root basename (D-02/D-07)
        4. sweep_launcher.py: Popen(LIST argv, start_new_session, cwd=pipeline/,
              PYTHONUNBUFFERED=1, stdout+stderr → tee file under state_dir()/logs/)  (D-06/D-10)
        5. toast + auto-nav slot 5, sweep attached (D-13)
                    │
                    ▼
 run_sweep.py subprocess (detached) ── run_fune.py per cell (GPU)
                    │  artifacts: {root}/{model}[+alias]/{task}/seed_{s}/
                    │    run_record.json (post-cell) · trainer_state.json (marker, final act)
                    │    final_metrics.json · flops_report.json · runs/ · checkpoint-*/
                    │    sweep_manifest.json + sweep_failures.json (sweep END only)
                    ▼
 slot 5 任务监控 (MonitorScreen, NEW)
   ├─ sweep_monitor.py discovery: default roots + XDG manual roots; 2s frontier /
   │    60s full @work(thread) scans, run-id-tagged messages (D-09)
   │    state: manifest ⇒ ○ 已结束 | Popen alive or artifact churn ⇒ ● 运行中
   ├─ attach (enter / [a] path input, validated) → cell table (row per model×task,
   │    seed columns, glyph states ⊘ skipped = resume marker) + resume note (MON-05)
   ├─ stats line: done/total · current · elapsed (earliest started_at) · ETA
   │    (median completed-cell duration × remaining, per-model else global, D-17)
   ├─ [f] failures: live from run_records (status=failed); finished ⇒ sweep_failures.json;
   │    [r] re-run → SAME launch pipeline, run_sweep --from-failures (D-11)
   └─ [t] log tail: RichLog over the tee file; CLI-launched ⇒ designed unavailable state
 App: q + live sweep ⇒ ExitModal (enter detach default / k killpg / esc) — D-06
```

### Recommended Project Structure

```text
tui/
├── services/
│   ├── run_config.py        # NEW: slot-4 state + XDG persistence, preview via imported
│   │                        # run_sweep functions, E2' verdict + phrase check, gate steps
│   ├── sweep_launcher.py    # NEW: Popen/tee/exit lifecycle (spawner-injectable),
│   │                        # live-sweep registry for the ExitModal   (or fold into
│   │                        # run_config.py if the planner prefers 2 services)
│   └── sweep_monitor.py     # NEW: discovery/attach, tolerant record/manifest readers,
│                            # progress/elapsed/ETA pure functions
├── screens/
│   ├── run_config.py        # NEW: slot-4 base screen
│   ├── monitor.py           # NEW: slot-5 base screen
│   └── nav.py               # EDIT: NavSlot(4/5) placeholders → real (screens "run_config"/"monitor")
├── strings.py               # EDIT: CFG_/LNC_/MON_ groups (zero exist today)
└── app.py                   # EDIT: screen registry + build_* + action_quit override
pipeline/
└── run_sweep.py             # EDIT: --config-variant (ALIASING pattern, § Area 3)
screens/env_check.py         # EDIT: ENV_VERDICT_CRITICAL_FAIL value amendment (one line)
tests/tui/                   # 4 new modules (§ Area 8)
tests/test_sweep.py          # EXTEND: variant argv-parity suite
```

### Pattern 1: Service imports pipeline modules through the existing sys.path root

**What:** `tui/services/run_config.py` does `import run_sweep` (module-level is
safe — zero torch in the chain); `tui/services/sweep_monitor.py` imports the
name constants (`MANIFEST_NAME`, `RESUME_MARKER`, ...) and `base_model_name`.
**When to use:** every preview/gate/recompute path (D-05).
**Why safe:** the `tui/__main__.py` bootstrap and both conftests already insert
the roots; the ast import lock keeps the services textual-free automatically.

### Pattern 2: Gate = service-tier pipeline, widgets never compute

**What:** the launch gate's four steps (enumeration → env → confirm/E2' →
spawn) live in the service; screens render modal states. The E2' predicate and
the exact-match phrase check are pure functions the modal cannot skip (D-07).
**When to use:** `[enter]` on slot 4 and the `[r]` from-failures re-run (same
pipeline; from-failures can never match the full matrix ⇒ no E2' by
construction).

### Pattern 3: Monitor = pure scanners over the artifact tree, tolerant readers

**What:** every scan runs in `@work(thread=True)` posting run-id-tagged
messages; JSON reads skip partially-written files with last-known-good
retained (the phase-10 ROADMAP-pinned tolerant-loader contract). Discovery
derives state from manifest presence + churn + the launcher's Popen registry —
never from a daemon.

### Anti-Patterns to Avoid

- **Pure pass-through `--config-variant`** — mis-recorded cells + retrain
  forever (§ Area 3). The flag must alias enumeration like `--peft`.
- **Importing anything from `run_finetune.py` in the TUI** — torch at module
  top; read-source extraction only.
- **Trusting the preview line at the gate** — the gate recomputes
  independently (UI-SPEC contract; staleness is a designed-out bug class).
- **Reading `sweep_failures.json` for a running sweep's live failure list** —
  the file lands only at sweep end (WR-06 write site); derive from
  run_records while running.
- **A second persistence root for tee logs** — D-10 forbids it;
  `state_dir()/logs/` is the single family.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cell enumeration / argv building | Copy enumerate/build_argv into the service | `import run_sweep` (D-05) | Import is clean (live-probed); copying creates the exact drift D-05 exists to prevent |
| E2' "full matrix" definition | Hardcoded 62/50 constants in logic | Official registry key sets loaded overlay-free | The registry is the single source; counts verified 62/50 today but the predicate reads them, not literals |
| Process-group termination | psutil tree walk | `start_new_session` + `os.killpg` | Phase-10 precedent, stdlib |
| Atomic state writes | Ad-hoc locking | `settings.atomic_write` | Existing seam [VERIFIED: tui/services/settings.py:90-107] |
| Registry presence views | New scan logic | `tui/services/registries.py` (delegates to registry_loader) | The D-08 single-source seam already serves the pickers |
| ETA math | Regression/extrapolation | rolling median × remaining (D-17 verbatim) | The decision fixes the method; variance ⇒ range display |

**Key insight:** every piece of sweep semantics (enumeration order, aliasing,
resume, failure boundary, manifests) already exists, tested, in
`run_sweep.py`; the TUI's whole job is composition, gate ordering, process
lifecycle, and artifact *reading* — the orchestrates-never-computes line.

## Common Pitfalls

### Pitfall 1: The variant pass-through trap (D-18)
**What goes wrong:** a `--config-variant` threaded like `--subset_file`
produces cells that train successfully into `{model}+probe/` dirs while the
driver records them failed and re-attempts forever.
**Why:** the child self-aliases `model_save_name` (run_finetune.py:1194-1209)
while `cell_dir_for` keys on the base name.
**How to avoid:** alias the enumeration (peft pattern) + explicit
`--save_model_name <alias>`; argv-parity tests pin it.
**Warning signs:** a variant sweep whose every cell reads "executor exited 0
but final_metrics.json is missing".

### Pitfall 2: Assuming run_record.json exists for the current cell
**What goes wrong:** the monitor shows no "running" cell because it only
watches records; or elapsed shows "—" for minutes.
**Why:** the record is written only post-cell; `started_at` is set at cell
start but persisted at cell end.
**How to avoid:** running-cell detection = newest seed dir (driver mkdirs
before the executor) + checkpoint/runs churn + the launcher's Popen registry;
elapsed falls back to the launcher's start time for TUI-launched sweeps.

### Pitfall 3: The stale finetuned tree renders as "running"
**What goes wrong:** the existing seed_9527 artifacts (no manifest, no churn)
show `● 运行中` forever.
**Why:** UI-SPEC #11's binary predicate has no third state.
**How to avoid:** define the artifacts-only state (no manifest + no churn +
no Popen): listed with `总数未知` and no ● glyph (or excluded); plan pins the
churn-age threshold.
**Warning signs:** a "running" sweep with zero new mtimes across scans.

### Pitfall 4: tee buffering hides progress
**What goes wrong:** the RichLog tail shows nothing for minutes.
**Why:** Python block-buffers stdout to a file/pipe.
**How to avoid:** `PYTHONUNBUFFERED=1` in the launch env (LNC-02's exact
wording is load-bearing, not decorative).

### Pitfall 5: E2' predicate over the overlay view
**What goes wrong:** custom entries silently join the enumeration via
registry_loader, and the verdict compares against a merged count.
**Why:** `enumerate_matrix` loads the overlay-merged registries.
**How to avoid:** official key sets loaded overlay-free (direct json.load of
the two official files); compare on base names; custom keys ⇒ never E2'.

### Pitfall 6: Head variant on the frozen pair aliases wrongly
**What goes wrong:** `evo2_1b_base` + variant head enumerated as
`evo2_1b_base+head` diverges from the child's base-name output.
**Why:** the child exempts the special pair from the +head alias (their
with-head config IS their base config).
**How to avoid:** mirror the exception in the driver's alias rule + pin with a
read-source parity test (the 2-name pair `("evo2_1b_base", "megaDNA_updated")`
is verbatim at run_finetune.py:1206-1207).

### Pitfall 7: Duplicated PROBE_INELIGIBLE names in strings.py
**What goes wrong:** the frozen list drifts from the pipeline source.
**Why:** the list lives in a torch-importing module and cannot be imported.
**How to avoid:** read-source extraction helper in the service + a parity test
against the real file; the UI-SPEC's "never duplicated in strings.py" rule
stands (also fix the stale "7 names" claim).

## Code Examples

### E2' verdict (service-tier pure function — sketch)

```python
# Source: shapes live-probed this session; official counts verified 62/50
def is_full_e2x(models_base: set[str], tasks: set[str], seeds: list[int],
                official_models: set[str], official_tasks: set[str]) -> bool:
    """D-02: full official models x full official tasks x >=3 seeds."""
    return (models_base >= official_models
            and tasks >= official_tasks
            and len(seeds) >= 3)
```

### PROBE_INELIGIBLE read-source extraction (the contracts-test pattern)

```python
# Source: tests/test_run_finetune_contracts.py:8-12 read-source-never-import;
# run_finetune.py imports torch at module top (line 43) — import is impossible.
import re

_PROBE_RE = re.compile(r"PROBE_INELIGIBLE\s*=\s*\[(.*?)\]", re.S)

def load_probe_ineligible(source_text: str) -> frozenset[str]:
    match = _PROBE_RE.search(source_text)
    if match is None:
        raise ValueError("PROBE_INELIGIBLE literal not found in source")
    names = re.findall(r'"([^"]+)"', match.group(1))
    return frozenset(names)   # 9 names today — verified 2026-10-13
```

### Launch spawner (phase-10 seam reuse)

```python
# Source: tui/services/download_queue.py:698-712 (_default_spawner) + D-06
def _default_spawner(argv, **kwargs):
    return subprocess.Popen(argv, start_new_session=True, **kwargs)

# launch: argv LIST, cwd pinned pipeline/, PYTHONUNBUFFERED=1, tee to XDG logs
env = {**os.environ, "PYTHONUNBUFFERED": "1"}
tee_path = settings.state_dir() / "logs" / f"sweep_{ts}_{rootname}.log"
proc = spawner([sys.executable, str(run_sweep_py), *flags],
               cwd=str(PIPELINE_DIR), env=env,
               stdout=tee_file, stderr=subprocess.STDOUT)
# kill path: os.killpg(os.getpgid(proc.pid), signal.SIGTERM)  (download_queue.py:870-876)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| run_sweep docstring: "Config variants compose STANDALONE, deliberately not forwarded here" (line 185-190) | D-18 (2026-10-13): thread `--config-variant` — as an ALIASING flag (peft pattern), because the child's save-name aliasing makes pass-through corrupt | This research | The docstring's "half-wiring is worse than documenting" concern is answered: full wiring = alias enumeration + explicit save name |
| UI-SPEC: PROBE_INELIGIBLE "data, 7 names" | The frozen list has 9 names (2 space spellings + gpn + omnidna added since) | Verified this session | Spec prose stale; dynamic `{models}` copy unaffected; flag at plan review |
| Monitor "sweep-level completion marker" assumed derivable-only | `sweep_manifest.json` written only at sweep END (line 1403) — a concrete marker exists | Verified this session | Discovery predicate is file-presence, not inference |
| REQUIREMENTS MON-04 tee target "~/.config/dnallmmark/logs/ 或任务输出目录" | D-10: single XDG logs root under the STATE family (`~/.local/state/dnallmmark/logs/`) | D-10 ruling 2026-10-13 | The config-root/输出目录 alternatives are superseded — do not implement them |

**Deprecated/outdated:** nav.py slot-5 placeholder annotation `NavSlot(5,
NAV_LABEL_MONITOR, None, 12)` still says "delivered by Phase 12" — D-16 rules
slot 5 real THIS phase; the promotion edit fixes the annotation.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The SC5 smoke's ~2-3 min/cell holds at seed 42 (the 65s evidence is seed 9527, same model×task×1epoch on the same GB10) | Smoke Pick | Variance is minutes-scale; even 3× is fine for a smoke |
| A2 | `--config-variant` record field named `config_variant` (mirroring the `peft` field) — field name is plan discretion | D-18 | Cosmetic; consumers are the phase's own monitor |
| A3 | Tee filename `sweep_{ts}_{rootname}.log` — explicitly plan-owned (UI-SPEC #16) | Subprocess/tee | Cosmetic |
| A4 | E2' predicate uses ⊇ (superset) rather than strict equality on official sets | E2' | If the maintainer wants strict equality, one-line tightening; listed as a plan-review checkpoint |
| A5 | The stale-tree third state (artifacts-only row) is the right resolution of UI-SPEC #11's gap | Monitor | A maintainer may prefer exclusion; rendering is plan-owned either way |
| A6 | Driver-authoritative aliasing via explicit `--save_model_name` (rather than relying on the child's identical self-aliasing) | D-18 | Both agree today; explicit is the single-authority design — if the planner drops the explicit flag, the parity test must pin the child's naming chain instead |

## Open Questions

1. **PROBE_INELIGIBLE count discrepancy (spec prose)**
   - What we know: the frozen list has 9 names (verified verbatim); UI-SPEC says 7.
   - What's unclear: nothing functional — the copy is dynamic.
   - Recommendation: note the correction at plan review; extraction helper + parity test make drift impossible going forward.
2. **Stale-artifact-tree rendering (UI-SPEC #11 gap)**
   - What we know: `pipeline/finetuned` today = standalone-run artifacts, no manifest, no churn.
   - What's unclear: maintainer preference — artifacts-only row with `总数未知`, or exclusion from discovery.
   - Recommendation: list it (honest, D-03 says discovery covers the default roots), no ● glyph; plan pins the churn-age threshold. [checkpoint:human-verify]
3. **Live failure-list source wording**
   - What we know: sweep_failures.json lands only at sweep END; run_records carry failures live.
   - What's unclear: whether the `[f]` modal title (which names sweep_failures.json) should re-word while running.
   - Recommendation: derive from records while running, keep the file-accurate title for finished sweeps; strings table already supports both. [checkpoint:human-verify]
4. **E2' ⊇ vs strict equality** — see A4. [checkpoint:human-verify]
5. **Service-module split** — 3 services (run_config/sweep_launcher/sweep_monitor) recommended; a 2-way split (launcher folded into run_config) is defensible. Planner's call; screens/tests map either way.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| GPU (GB10) + torch + dnallm + transformers | SC5 smoke (documented maintainer procedure, not CI) | ✓ (prior seed_9527 artifacts prove the lane) | torch per `[gpu]` pins | — (smoke is maintainer-run; CI never needs it) |
| Python 3.13 repo venv (uv) | TUI + services + tests | ✓ | 3.13 | — |
| textual / platformdirs / jsonschema | TUI | ✓ | 8.2.8 / 4.13.0 (uv.lock) | — |
| `pipeline/models/` local weights | any real launch from this host | ✓ only 2/62 (plant-dnabert-6mer, plant-dnagpt-BPE) | — | D-15: this host is dev/test; full sweeps run elsewhere — the pick uses a local model |
| Datasets on disk | smoke + env-check dataset_dirs | ✓ 50/50 (n_audit 0 missing) | — | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none (the 2-model limit is a D-15 constraint, not a gap).

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (no credentials anywhere in this phase; none stored, none echoed) |
| V3 Session Management | no | — |
| V4 Access Control | yes (LNC-03) | The E2' gate is an authorization boundary: verdict + exact-match phrase check live in the service tier; no widget path reaches launch without both (structural, not cosmetic) |
| V5 Input Validation | yes | Every operator input validates collect-all before use: seeds/curve fractions parse to typed values (run_sweep's own validators reused); unknown model/task names fail via `_validate_filters` at subprocess start; attach paths validated as sweep roots before persisting; E2' phrase compared by exact string equality |
| V6 Cryptography | no | — |
| V12 File Handling | yes | Tee + state writes via `settings.atomic_write`; tolerant readers never execute artifact content; outputs land only under operator-chosen roots (paths resolved absolute, D-14) or the XDG state root |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Argv injection via registry/model names | Tampering/Elevation | LIST argv throughout (values never become flags); the phase-10 discipline carried verbatim; run_sweep re-validates filters at start |
| UI-path bypass of the E2' gate | Elevation of privilege | Verdict + phrase check in the service tier (D-07); the gate recomputes independently of any widget state; from-failures cannot match the full matrix by construction |
| Malicious/corrupt artifact JSON | Tampering/Denial of service | Tolerant parse-only readers; partial writes skipped with last-known-good; no artifact content is ever executed or interpolated into argv |
| Log-file growth (tee) | Denial of service | One bounded file per launch under the XDG root; plan may add a size note; RichLog tail is bounded (max-height 20 family) |
| Stale failures manifest poisoning a re-run | Tampering | `--from-failures` validates every entry against the registries fail-fast (load_failure_pairs); WR-06 rewrite-on-every-run prevents stale lists surviving |

## Sources

### Primary (HIGH confidence)
- Live probes this session (repo venv Python 3.13): run_sweep import (0.012s, torch/dnallm absent from sys.modules), enumerate_matrix tiny + full (9300 cells, 0.002s), build_argv/cell_dir_for verbatim outputs, real `--dry-run` run (stdout + manifest verbatim), fake-executor `run_matrix` runs (run_record.json / sweep_failures.json / manifest-cell verbatim, clean + failing)
- On-disk census: `pipeline/models/` (exactly 2 local), `pipeline/datasets/iDNA_ABF_datasets/5mC` presence, `models_info.json` sizes, `datasets_info.json` row ranking, `dnallm-mark/data/n_audit.json` (0 missing), `pipeline/finetuned/**` prior GB10 artifacts (final_metrics 65.04s, flops_report hardware, mtimes), `pipeline/sweep_priorities.json`
- Repo source read this session: `pipeline/run_sweep.py` (full), `pipeline/run_finetune.py` (imports, --config-variant argparse, VARIANT_CONFIGS, PROBE_INELIGIBLE, probe guards, save-name aliasing block), `pipeline/registry_loader.py`, `pipeline/env_smoke.py` CheckResult, `tui/services/env_gate.py`, `tui/services/quick_check.py`, `tui/services/settings.py`, `tui/services/download_queue.py` (spawner/_signal_group), `tui/services/registries.py`, `tui/screens/nav.py`, `tui/app.py`, `tui/__main__.py`, `tests/test_sweep.py` (test inventory), `tests/test_run_finetune_contracts.py`, `tests/tui/conftest.py`, `tests/tui/test_import_lock.py`, `tests/tui/test_pilot_data_manager.py`
- `.planning/config.json` (nyquist_validation: false; security_enforcement: true, level 1)

### Secondary (MEDIUM confidence)
- `.planning/ROADMAP.md` Phase 11 SC1-5 + binding constraints; `.planning/REQUIREMENTS.md` CFG/LNC/MON rows; `11-CONTEXT.md` D-01..D-19; `11-UI-SPEC.md` (approved contract); phase-10 research (subprocess discipline, repo census context)

### Tertiary (LOW confidence)
- None — no training-data-only claims are load-bearing in this research

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new deps; all seams read from source + live import probe
- D-05 import seam: HIGH — live-probed with verbatim captures (the phase's foundational claim)
- D-18 variant design: HIGH evidence (child naming chain read verbatim); the aliasing recommendation is strongly constrained, field name/split are plan discretion (A2/A6)
- Monitor schemas: HIGH — live-captured artifacts + source-verified write timing; stale-tree predicate is a flagged design choice (A5)
- Smoke pick: HIGH — every number from disk/registries; runtime from a real prior GB10 run of the exact pair
- Pitfalls: HIGH — each observed live or read from source

**Research date:** 2026-10-13
**Valid until:** 2026-11-13 (stable repo; the only moving targets are the local model set and the frozen lists — both parity-tested in the proposed plan)

## Ready for Planning

Recommended new/edited files (services split = recommendation, planner may fold):

| File | Kind | Delivers |
|------|------|----------|
| `tui/services/run_config.py` | NEW service | Slot-4 state + XDG persistence; preview via imported `enumerate_matrix`/`build_argv`; E2' verdict + typed-phrase check (service-tier); gate steps 1-3; PROBE_INELIGIBLE read-source extraction; from-failures composition |
| `tui/services/sweep_launcher.py` | NEW service | Popen (LIST argv, start_new_session, cwd=pipeline/, PYTHONUNBUFFERED, tee→`state_dir()/logs/`); spawner-injectable; live-sweep registry; killpg/detach for ExitModal; `q`-intercept answer |
| `tui/services/sweep_monitor.py` | NEW service | Default+manual root discovery; manifest/churn/Popen state derivation; tolerant run_record/manifest/failures readers; done/total + ⊘ resume counting; elapsed + ETA (D-17 median) |
| `tui/screens/run_config.py` | NEW screen | Slot-4 base screen: pickers (`m` flip, `/` filter), params pane, dirs section, preview line, `[p]` modal, gate modals |
| `tui/screens/monitor.py` | NEW screen | Slot-5 base screen: discovered pane, cell table, stats line, `[f]`/`[t]`/`[a]`/`[r]` modals |
| `tui/strings.py` | EDIT | `CFG_*` / `LNC_*` / `MON_*` groups (grep-verified: zero exist today); `ENV_VERDICT_CRITICAL_FAIL` value amendment |
| `tui/screens/nav.py` | EDIT | `NavSlot(4, NAV_LABEL_RUN_CONFIG, "run_config", None)` + `NavSlot(5, NAV_LABEL_MONITOR, "monitor", None)`; placeholder suffix/toast lose all consumers |
| `tui/app.py` | EDIT | Screen registry entries + build hooks; `action_quit` override → ExitModal when a live sweep exists |
| `pipeline/run_sweep.py` | EDIT | `--config-variant` via the ALIASING pattern (enumerate alias + explicit `--save_model_name` + head frozen-pair exception + `config_variant` record field + manifest sweep_flag); argv-parity tests pin it |
| `tests/tui/test_services_run_config.py` | NEW | Tier-1 (Area 8) |
| `tests/tui/test_services_sweep_monitor.py` | NEW | Tier-1 (Area 8) |
| `tests/tui/test_pilot_run_config.py` | NEW | Tier-2 Pilot |
| `tests/tui/test_pilot_monitor.py` | NEW | Tier-2 Pilot |
| `tests/test_sweep.py` | EDIT | `--config-variant` argv-parity suite (flag_value/test_launch_subprocess idiom) |

**SC5 smoke (the D-04 deliverable, for plan review):**
`plant-dnabert-6mer × iDNA_ABF_datasets__5mC × seed 42 × 1 epoch × PEFT none × variant none`
— smallest local model (89M, one of only 2 on disk) × smallest trainable task
of all 50 (2110/234/2344 rows, present, n_audit clean) × the TUI-default seed
(untouched by the existing seed_9527 markers) — prior real GB10 run of this
exact pair: 65.04s training, ~2-3 min wall per cell. No PROBE_INELIGIBLE or
resume interactions. Optional second leg (runner-up `GUE__virus_species_40`,
+2-3 min) if the maintainer wants a multi-cell monitor/failure story inside
D-15's bound.

**Open questions surviving into planning:** O1-O5 above (O2/O3/O4 carry
checkpoint:human-verify at plan review; none block planning).
