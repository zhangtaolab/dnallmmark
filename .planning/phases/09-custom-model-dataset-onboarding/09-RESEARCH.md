# Phase 9: Custom Model & Dataset Onboarding (自定义接入向导) - Research

**Researched:** 2026-10-12
**Domain:** Textual 8.2.8 modal-wizard TUI + staged-overlay subprocess gauntlet over the Phase 7 registry seam
**Confidence:** HIGH (every load-bearing mechanic probed live against the pinned code; all in-repo values quoted from source)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (D-01..D-16 — research these, not alternatives)

- **D-01:** 多步模态向导(3-4 步,每步一组字段,enter 下一步 / esc 取消),复用 Phase 8 ModalScreen 模式
- **D-02:** 模型 quirk 清单(safetensors/fp32/特殊头)记录于条目字段 + 校验警示;执行侧 quirk→CLI 旗标映射是 Phase 11 run-config 的职责(管线硬编码 quirk 表不可扩——约束 6;TUI never-computes)
- **D-03:** 类型感知控件:枚举字段用 SelectionList(物种/架构/Task_type/主指标——指标名从度量注册表取),路径用 Input + 存在性即时校验,数字字段类型校验
- **D-04:** 本相位引入导航壳(详见 D-13..16)
- **D-05:** collect-all 校验为服务层纯函数(tier-1 可测,数据源注入)——一次全列,不逐字段打断
- **D-06:** dry-run 预检 = 子进程 `run_sweep.py --dry-run`(overlay 自动生效,subset=新条目)——CLI parity 正面运用;CPU 纯规划零训练,无需 GPU 授权
- **D-07:** audit 对账 = 子进程调 audit 脚本内核(新数据集行数/非 ACGT/子集存活)——复用既有实现,TUI 零计算
- **D-08:** **gauntlet 全过才落盘**——失败=条目从未写入,天然零回滚风险;成功后另有会话内 undo 撤销刚落盘条目
- **D-09:** loader 级真停用:自定义条目带 `enabled` 字段,`registry_loader` 跳过 `enabled:false`(加性改动——官方条目无此字段,缺席仍逐字节一致,现有测试零改动)
- **D-10:** custom 标记 = 列内徽标(颜色+字形双通道)+ 计数行区分(官方 62/50 · 自定义 N/M)
- **D-11:** 导出 = custom 注册表文件本身复制到操作者指定路径;导入 = 向导内"从文件导入"入口(校验后合并,冲突一次性列出)
- **D-12:** 本相位条目只增不编辑(编辑 = 删除 + 重录,完整编辑表单留后续相位)
- **D-13:** 顶部主菜单(资源名词命名):`1环境检查 2模型·数据集 3数据管理 4运行配置 5任务监控 6关于`——3/4/5 占位显示"未开放"(按相应相位实装),**`6关于` 本相位实装**(版本信息屏:软件版本/数据版本/milestone 阶段/依赖版本等只读信息)
- **D-14:** 向导从列表屏 `w` 键进入(选中行预填该列表上下文);菜单无向导项(向导是动作不是屏)
- **D-15:** 底部子菜单:左段当前屏上下文命令(现 Footer 键帽迁移),右段恒定 `?` `q`
- **D-16:** 低于 80×24 时 min-size 守卫全屏接管,顶/底菜单隐藏(现状不变);菜单栏各占 1 行计入内容区预算

### Claude's Discretion (research options, recommend)

- 向导步序划分(模型向导与数据集向导各自 3-4 步怎么分组)— UI-SPEC Auto-Default #2 settled: 4 steps each
- enabled 字段的确切 schema 位置与默认值语义(缺席 = 启用)
- 徽标字形/颜色的具体选择 — UI-SPEC settled: `◇` + bold + `$accent`
- 关于屏的具体信息条目集合与布局 — UI-SPEC Auto-Default #13 settled
- gauntlet 结果的呈现形态(逐项 ✓/✗ 面板)— UI-SPEC settled
- dry-run/audit 子进程的超时与输出解析容错(artifact_loader 容错契约复用)

### Deferred Ideas (OUT OF SCOPE — ignore completely)

- quirk → CLI 旗标映射(执行侧)→ Phase 11 run-config
- 条目完整编辑表单(本相位只增不编辑)→ 后续相位
- export_runs.py 改走 overlay(Phase 7 验证器 W1 建议)→ Phase 11 数据流或单独小任务
- 自定义条目的启用/停用批量操作 → 后续(按需)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CUST-01 | 模型向导 → `~/.config/dnallmmark/custom_models.json`,官方零写入,quirk 可选勾选 | Official 16-field model schema quoted verbatim (below); wizard field mapping; registry_loader write target verified |
| CUST-02 | 数据集向导 → `custom_datasets.json`,不动官方 | Official 17-field dataset schema quoted verbatim; Train/Dataset_name pipeline contracts probed |
| CUST-03 | 防呆检测:字段级 collect-all(必填/类型/枚举/键冲突官方+既有自定义/路径存在/split 可解析/行数>0/标签列/指标名在度量注册表) | Metric registry = SUITE_CANONICAL (28 names, verified); CSV header/rows checks per audit kernel semantics; key-collision sources enumerated |
| CUST-04 | 错误检测:dry-run 预检 + audit 对账;失败醒目报告 + 条目级撤销 | Full subprocess gauntlet mechanics probed live (dry-run exit codes + manifest shape; audit n_audit.json shape + pass criteria) |
| CUST-06 | custom 标记、可停用、导出分享 | D-09 loader-skip landing point identified; management-view second read path required (pitfall); export = file copy |
</phase_requirements>

## Summary

Phase 9 is the first TUI feature that **writes user-owned state through a verified gauntlet of real subprocesses**. Three mechanisms carry the phase: (1) a multi-step `ModalScreen` wizard whose shape, controls, and key-consumption semantics are all verified against the pinned textual 8.2.8 in `.venv` — most importantly a Pilot-proved fact that a focused `Input` consumes printable digit keys before any binding fires, so per-base-screen digit navigation and wizard text entry cannot conflict; (2) the staged-overlay gauntlet, probed live end-to-end: `run_sweep.py --dry-run` under `DNALLMMARK_CUSTOM_REGISTRY_DIR=<temp overlay>` enumerates a candidate model/dataset and writes a `sweep_manifest.json` whose planned cells are the pass signal (exit 0 alone is NOT sufficient — verified that filters/Train/Dataset_name failures exit 1 with collect-all `[Error]` messages); (3) the audit reconciliation, probed live: `script/audit_n_frequencies.py` run against a candidate-only temp registry emits an `n_audit.json` whose `missing`/`unified_eval_n`/per-split `rows` fields are the pass criteria, with two hard-pitfall findings — its DEFAULT output paths clobber committed repo artifacts (`dnallm-mark/data/n_audit.json`, `pipeline/eval_subsets.json`, `DATA.md`), and without the env override it merges the operator's REAL custom dir.

The pipeline surface is exactly one additive change (D-09): `registry_loader._load_registry` skips entries whose `enabled` is explicitly `False` after the collision check. Everything else is TUI-side. The custom registry schema mirrors the official entries field-for-field (both quoted verbatim below) plus `enabled` and custom-only fields the pipeline provably ignores (it reads only named keys). Two schema facts bind hard: the custom file's top level MUST stay a plain `{key: entry}` map (a `schema_version` envelope key would be merged as a registry entry and collide-fail), and custom `Model_path`/`Dataset_path` MUST be relative to `pipeline/` because `run_finetune.py` resolves them by STRING CONCATENATION (`base_dir + row[...]`) — absolute paths break the trainer while working in the audit.

**Primary recommendation:** Build three new textual-free services (custom-registry store + validation collect-all, gauntlet orchestrator with injectable subprocess runner, about-screen data) plus one wizard modal family and the nav-shell bars on the existing composition root; stage the gauntlet as `existing-custom + candidate` in a temp overlay for dry-run and a candidate-only temp registry-dir with ABSOLUTE `Dataset_path` for audit; treat the manifest's planned cells and `n_audit.json` fields (not exit codes alone) as the pass signals; add one real-subprocess tier-1 integration test for each gauntlet leg (both are stdlib-only, CPU, sub-second — proven by the probes).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Wizard form collection, step flow, value preservation | TUI screens (ModalScreen) | — | Presentation-only; services receive plain dicts |
| Collect-all field validation (CUST-03) | TUI services (pure function, injected data sources) | — | D-05: tier-1 testable, zero textual (import-lock) |
| Key-collision checks (official + existing custom) | TUI services over `registry_loader` + direct custom-file read | pipeline registry_loader (already fail-fast on load) | Loader collision check exists; wizard must pre-check to produce collect-all output |
| Dry-run precheck (CUST-04) | pipeline `run_sweep.py` as subprocess | TUI services orchestrate (argv, env, temp dirs, result parse) | D-06 CLI parity; TUI never computes |
| Audit reconciliation (CUST-04) | `script/audit_n_frequencies.py` as subprocess | TUI services orchestrate | D-07 reuse; kernels stay in the audit script |
| Custom registry persistence (land/undo/toggle) | TUI services (XDG config root, atomic write) | — | D-04 settings.py seam; write ONLY after all-✓ gauntlet |
| `enabled:false` skip (D-09) | pipeline `registry_loader` | — | The ONE pipeline change; loader-level true disable |
| Custom-entry management view (disabled rows visible) | TUI services (direct read of user-owned file) | — | Post-D-09 the merged view hides disabled rows; the table needs a second read path |
| Import/export | TUI services (file copy + validate-before-merge) | — | D-11; the file IS the share unit |
| Nav shell (top menu / bottom bar) | TUI screens (base screens) + composition root | — | Row-neutral replacement for Header/Footer |
| About screen values | TUI services (tolerant probes) | — | Read-only derivations, no computation |
| Benchmark semantics (rows/non-ACGT/subset survival) | pipeline/audit script ONLY | — | Binding constraint 5: TUI orchestrates, never computes |

## Standard Stack

### Core (all already installed and locked — ZERO new packages this phase)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| textual | 8.2.8 (pinned `>=8.2,<9`, `[tui]` group) | ModalScreen wizard family, nav-shell bars, Pilot tests | Phase 8 landed; verified in `.venv` this session |
| platformdirs | 4.13.0 (`>=3.6,<5`) | XDG config root for custom registries (same root as presets.json) | settings.py D-04 seam |
| jsonschema | 4.26.0 (`>=4.26.0`) | optional: validate imported registry files against a committed schema | templates.py precedent (run_template.json discipline) |
| pytest / pytest-asyncio | 9.1.1 / 1.4.0 (`asyncio_mode=auto`) | tier-1 + tier-2 lanes | existing config, zero edits |
| Python stdlib (subprocess, tempfile, csv, json, os/pathlib) | 3.13 | gauntlet subprocesses, temp staging | run_sweep + audit are stdlib-only — proven importable/runnable CPU-only |

**Installation:** none — `uv sync --group dev --group tui` already provides everything. No `[tui]`/`[dev]`/`[pipeline]` group changes. (Memory rule: `uv sync` for tui must stay `--inexact` on the GB10 host.)

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Single ModalScreen + internal step state | One ModalScreen per step (pushed stack) | Rejected: cross-screen value preservation and back-nav become manual message plumbing; a single screen with `self._step` + re-compose is the repo-consistent, Pilot-testable shape (Phase 8 modal family precedent) |
| Subprocess `run_sweep.py --dry-run` | Import `enumerate_matrix` in-process | Rejected by D-06 (CLI parity) AND practically: importing run_sweep is fine (stdlib-only) but would re-implement the CLI's validation surface; subprocess exercises the real operator path |
| Subprocess audit script with temp registry-dir | Import `audit_task` kernel in-process | D-07 says subprocess; in-process import would also put script/ on the TUI runtime sys.path (bootstrap only adds repo root + pipeline/). The CLI accepts `--registry-dir`/`--datasets-root`/output flags exactly for this |
| jsonschema for the custom-registry entry shape | Hand-rolled structural checks | Either acceptable; the templates.py precedent uses jsonschema with a committed schema + collect-all problem listing. Recommend jsonschema for the IMPORT path (untrusted file), hand-rolled field checks for the wizard path (field-level messages with Chinese labels must come from strings.py anyway) |

## Package Legitimacy Audit

> No new packages are installed this phase. All dependencies were approved at 08-02 (verdict lines in 08-02-SUMMARY.md) and re-verified in `.venv` this session: textual 8.2.8, platformdirs 4.13.0, jsonschema 4.26.0, pytest 9.1.1, pytest-asyncio 1.4.0.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| (none new) | — | — | — | — | — | Approved at Phase 8; nothing to audit |

**Packages removed due to [SLOP]:** none. **Packages flagged [SUS]:** none.

## Architecture Patterns

### System Architecture Diagram

```text
                    选择屏 (selection.py)
   w ──────────────►│ wizard entry (cursor row key → type + prefill)
   e ──────────────►│ enable/disable toggle (custom rows only)
                    │ ◇ badge / （已停用）suffix / count line
                    └────────────┬──────────────────────────────┐
                                 ▼                              ▼
                    ┌──────────────────────┐        ┌────────────────────────┐
                    │ Wizard ModalScreen   │        │ services/custom_*.py   │
                    │ 4 steps, Input/      │ submit │ (textual-free, tier-1) │
                    │ SelectionList/       ├───────►│ 1. collect-all validate │
                    │ Checkbox, live path  │        │    (official keys,      │
                    │ checks, b/esc/enter  │        │    existing custom file,│
                    └──────────┬───────────┘        │    SUITE_CANONICAL-28, │
                               │ problems           │    fs via injected root)│
                               ▼                    └───────────┬────────────┘
                    ┌──────────────────────┐  pass              │
                    │ Validation report    ├────────────────────┤
                    │ (collect-all, esc    │                    ▼
                    │ returns, values kept)│        ┌────────────────────────┐
                    └──────────────────────┘        │ Gauntlet orchestrator   │
                                                    │ (thread worker, run-id  │
                                                    │  tags, injectable       │
                                                    │  subprocess runner)     │
                                                    └───┬───────────────┬────┘
                     env: DNALLMMARK_CUSTOM_REGISTRY_DIR=<temp staging dir>
                     (existing custom + candidate, enabled true)│   │
                                                        ▼       ▼
              ┌─────────────────────────────┐  ┌──────────────────────────────┐
              │ subprocess run_sweep.py     │  │ subprocess audit_n_frequen-  │
              │ --dry-run --models/--tasks  │  │ cies.py --registry-dir <temp │
              │ <candidate> --seeds 42      │  │ candidate-only> --data-dir   │
              │ --output-root <temp>        │  │ <temp> (ALL outputs temp)    │
              └──────────┬──────────────────┘  └──────────┬───────────────────┘
                         ▼                                ▼
              pass = exit 0 AND manifest      pass = n_audit.json: missing=false,
              cells[] contains the            3 splits rows>0, unified_eval_n>0,
              candidate key (status planned)  declared Train/Dev/Test == measured
                         │                                │
                         └───────────────┬────────────────┘
                                         ▼ all ✓
                    ┌──────────────────────────────────────────────┐
                    │ LAND: atomic write custom_models.json /      │
                    │ custom_datasets.json under XDG config root   │
                    │ (official pipeline/*.json NEVER written)     │
                    │ [u] session undo removes the just-landed key │
                    └──────────────────────────────────────────────┘
                                         │
                                         ▼ next pipeline load
                    registry_loader: official + custom merge,
                    collision fail-fast, NEW: skip enabled===false
```

### Recommended Project Structure

```text
tui/
├── app.py                      # + 关于屏 wiring, nav-shell mount points, digit-nav actions, w/e helpers
├── strings.py                  # + NAV_*, ABOUT_*, WIZ_*, WIZM_*, WIZD_*, GAUNTLET_*, SEL_* additions
├── styles.tcss                 # + menu-bar / wizard / gauntlet classes (theme tokens only)
├── screens/
│   ├── selection.py            # + w/e bindings, ◇ badge cells, count segment, import/export hooks
│   ├── about.py                # NEW 关于屏 (slot 6, read-only, zero-arg SCREENS slot OK)
│   └── wizard.py               # NEW the modal family: wizard + validation report + gauntlet panel
│                               #   (or wizard.py + gauntlet.py split at planner's discretion)
└── services/
    ├── custom_entries.py       # NEW store: read/land/undo/toggle custom registries; management view
    ├── custom_validation.py    # NEW collect-all pure validator (D-05) + import validate-before-merge
    ├── gauntlet.py             # NEW orchestration: staging dirs, argv/env, result parsing, timeouts
    └── about.py                # NEW 关于屏 derivations (version/counts/deps tolerant probes)
pipeline/
└── registry_loader.py          # THE ONE PIPELINE CHANGE: skip enabled===false (D-09)
schemas/
└── custom_registry.json        # NEW (optional but recommended): entry-shape contract for import
tests/
├── test_registry_loader.py     # + enabled-skip tests (additive; existing tests untouched)
└── tui/
    ├── test_services_custom_entries.py    # NEW tier-1
    ├── test_services_custom_validation.py # NEW tier-1 (incl. real-subprocess gauntlet legs)
    ├── test_services_gauntlet.py          # NEW tier-1 (fake runner argv assertions + real legs)
    ├── test_services_about.py             # NEW tier-1
    ├── test_pilot_wizard.py               # NEW tier-2 (step flow, preservation, esc-confirm)
    ├── test_pilot_nav_shell.py            # NEW tier-2 (digits, bars, placeholders, guard)
    └── test_pilot_selection_custom.py     # NEW tier-2 (badge, counts, e toggle, w entry)
```

### Pattern 1: The wizard = ONE ModalScreen with step state

**What:** A single `ModalScreen` subclass holds `self._values: dict[str, str]` and `self._step: int`; compose()/re-compose renders the active step's fields, pre-filling from `_values`. `enter` advances (last step: submit), `b` goes back, `esc` confirms-cancel only when any value is entered.

**When to use:** exactly here (D-01). Precedent: the Phase 8 modal family (`PresetModal`/`ConfirmModal`/`RowDetailModal`/`PathInputModal` at `tui/screens/selection.py:612-805`).

**Verified control facts (textual 8.2.8, read from the installed package this session):**

```python
# Input consumes printable keys BEFORE bindings — Pilot-proved on 8.2.8:
#   focused Input + pilot.press("1","3") → Input.value == "13", ZERO bindings fired
#   set_focus(None) + press("1") → screen binding fires
# Source: textual/widgets/input.py Input._on_key:
#   if event.is_printable: event.stop(); ...; event.prevent_default()
#
# SelectionList (multi-toggle by default) — single-pick enforced in the screen:
from textual.widgets.selection_list import Selection
# Selection(prompt, value, initial_state=False, id=None, disabled=False)
# events: on_selection_list_selection_toggled(event) → event.selection.value
# APIs: select(sel) / deselect(sel) / deselect_all() / selected -> list[values]
#
# Checkbox: Checkbox(label, value=False, *, id=None, ...)  # quirk checklist
# Input.Changed fires per keystroke → live path-check Static updates
```

```python
# Single-pick enforcement (the UI-SPEC Interaction #6 contract):
def on_selection_list_selection_toggled(self, event) -> None:
    if event.selection.value not in self._picked:          # newly picked
        for prev in list(self._picked):
            self.query_one(f"#{field_id}", SelectionList).deselect(
                next(s for s in self._options if s.value == prev))
        self._picked = {event.selection.value}
```

### Pattern 2: Digit navigation — per-base-screen bindings, never priority

**What:** digits `1`-`6` declared in each base screen's `BINDINGS` (env_check, selection, about). Two verified facts make this safe:

1. **A focused `Input` eats digits** (Pilot-proved, above) — typing `1` in the wizard or in the selection `/` filter types `1`; navigation never hijacks.
2. **`Binding(priority=True)` must NOT be used** — priority bindings are "checked prior to the bindings of the focused widget" `[CITED: textual.textualize.io/guide/input]`, i.e. they would fire EVEN when an Input is focused and break typing. Plain per-screen bindings + ModalScreen isolation (base bindings never fire under a modal — the Phase 8 Pitfall 11 pattern) yield exactly the UI-SPEC Interaction #1 behavior.

The matrix view (pushed plain Screen hides everything beneath) and all modals never see digit nav — verified mechanics: the existing min-size guard uses the same plain-Screen push to hide all chrome (`tui/app.py:223-248`).

### Pattern 3: The staged-overlay dry-run gauntlet (probed live, exit codes + manifest verified)

```python
# VERIFIED PROBE (2026-10-12, this session, temp dirs):
#   overlay/custom_models.json = {candidate entry with all 16 official fields + enabled: true}
#   env DNALLMMARK_CUSTOM_REGISTRY_DIR=/tmp/.../overlay
#   python pipeline/run_sweep.py --dry-run --models my-custom-dna-lm \
#         --tasks GUE__emp_H3 --seeds 42 --output-root /tmp/.../out
# → exit 0, stdout "[Dry-run] 1 planned cell(s) over 1 model(s) x 1 task(s) x 1 seed(s)"
# → out/sweep_manifest.json cells[0] = {model: "my-custom-dna-lm", task, seed, status: "planned", output_dir}
# → dry-run writes ONLY sweep_manifest.json (no failures manifest, no cell dirs)
#
# FAILURE PATHS (all exit 1 with collect-all [Error] messages on stdout):
#   overlay env var NOT propagated → "[Error] --models names not in registry: ['my-custom-dna-lm']"
#   candidate dataset with Train: 0 → "[Error] --tasks with no train split (Train is falsy): [...]"
#   Dataset_name != key          → _validate_dataset_name_alignment collect-all refusal
```

**Staging rules (the load-bearing details):**
- The overlay dir must contain `custom_models.json` = **existing user custom entries + candidate** (the env var replaces the WHOLE dir — a candidate-only file would drop existing customs from the merged view; collision validation upstream guarantees the merge is collision-free).
- The candidate stages with `enabled` absent or `true` — after D-09 lands, an `enabled: false` staged entry would be skipped by the loader and the dry-run would fail "not in registry" (correct: you cannot gauntlet a disabled entry; at gauntlet time it is always enabled).
- Model gauntlet: `--models <candidate_key> --tasks <one official Train-truthy task>`. Dataset gauntlet: `--models <one official model> --tasks <candidate_key>`.
- **Pass = exit 0 AND the parsed manifest's `cells[]` contains the candidate key with `status: "planned"`** — exit 0 alone is insufficient in principle (a filter that intersects to zero still exits 0 with a manifest), though the fail-fast validators make the realistic miss paths exit 1.
- The subprocess needs no `--registry-dir` (official registries default to pipeline/); argv is a LIST, `sys.executable`, script path absolute — the repo subprocess discipline.

### Pattern 4: The audit reconciliation subprocess (probed live, output shape verified)

```python
# VERIFIED PROBE (candidate-only temp registry + ABSOLUTE Dataset_path + temp outputs):
#   python script/audit_n_frequencies.py \
#     --registry-dir <tmp>/regdir          # contains ONLY {candidate: entry}
#     --datasets-root <any>                # inert when Dataset_path is absolute (pathlib join)
#     --data-dir <tmp>/audit-out --subsets-out <tmp>/audit-out/eval_subsets.json \
#     --data-md <tmp>/audit-out/DATA.md
#   env DNALLMMARK_CUSTOM_REGISTRY_DIR=<empty tmp dir>   # MANDATORY isolation (see Pitfall 2)
# → exit 0 ALWAYS (even missing rows); n_audit.json is the verdict:
#   tasks.<key>.missing == False, unified_eval_n == 3,
#   splits.train/dev/test = {rows, non_acgt_chars, strict_survivors, n_tolerant_survivors, ...}
# → eval_subsets.json: {"my-custom-ds": [0,1,2]}  (the subset-survival evidence)
```

**Pass criteria derivable from the verified output:** `missing == false`; all three splits present with `rows > 0`; `unified_eval_n > 0` (subset survival — a 0 emits NO eval-subset entry by design); and the **row-count reconciliation**: the wizard-collected declared `Train`/`Dev`/`Test` ints must equal the measured `rows` per split (对账 = declared vs measured). The non-ACGT census is reported data (drill-down), not a failure condition — official datasets carry non-ACGT rows by design.

### Pattern 5: registry_loader D-09 skip (the one pipeline change)

```python
# Landing point: pipeline/registry_loader.py _load_registry, AFTER the collision
# loop, BEFORE registry.update(custom) — skip only EXPLICIT false:
#     registry.update(
#         {key: entry for key, entry in custom.items()
#          if entry.get("enabled") is not False}     # absent/true → loaded
#     )
# Why `is not False` and not `not entry.get(...)`: an absent field (None) must
# load (official entries lack the field — D-09 缺席=启用); only the JSON literal
# false disables. bool is a subclass of int — no numeric edge here, but the
# sentinel must be the literal False, matching the "explicit false only" lock.
```

Official entries carry no `enabled` field `[VERIFIED: pipeline/registry_loader.py:124-133 — the merge is `registry.update(custom)` with no field inspection today]`, so with the skip in place the absent-field path executes the same `update` over the same content — byte-identical behavior, existing `test_registry_loader.py` untouched (verified test names at `tests/test_registry_loader.py:89-304` include the absent-overlay verbatim tests).

### Pattern 6: Nav shell + Footer migration

- Retire `Header()` (`tui/screens/selection.py:891`) and `Footer(compact=True, show_command_palette=False)` (`:905`) on base screens; same for the env screen. Replace with 1-row `Horizontal`/`Static` bars (height-1, theme-token styles in styles.tcss).
- The bottom bar's left segment derives from the SAME source the help modal uses — `_binding_row(binding)` at `tui/app.py:292-309` maps each BINDINGS declaration to `(key_display or key, description)`. The migration is presentational; per-screen BINDINGS declarations stay authoritative, so the `?` help modal keeps reflecting the live map automatically (including the env `s` removal — the planner's UI-SPEC checker note).
- Overflow: render keycaps in binding-declaration order, clip at available width with trailing `…` (UI-SPEC Auto-Default #14).
- The 关于屏 has no shared mutable state → it MAY join the zero-arg `SCREENS` registry (`tui/app.py:154-156` currently `{"env_check": ...}`); the selection screen keeps its factory discipline (zero-arg slots remain forbidden for it — live mark sets).

### Anti-Patterns to Avoid

- **Do NOT write a top-level envelope into custom_models.json/custom_datasets.json** (no `{"schema_version": 1, "entries": {...}}`) — registry_loader merges EVERY top-level key as a registry entry `[VERIFIED: pipeline/registry_loader.py:124-132 — `for key in custom: if key in registry: raise`; `registry.update(custom)`]`; an envelope key would either collide or become a garbage entry. Schema discipline goes into a committed `schemas/custom_registry.json` describing the ENTRY shape, plus per-entry inert fields.
- **Do NOT store absolute paths in the landed `Model_path`/`Dataset_path`** — `run_finetune.py` resolves them by string concatenation `[VERIFIED: pipeline/run_finetune.py:948,999 — `model_path = base_dir + model_row["Model_path"]`; `dataset_path = base_dir + row["Dataset_path"]`; base_dir at :696 is the pipeline dir + os.sep]`. Absolute paths produce `pipeline//home/...` and break the trainer. Convert at land time via `os.path.relpath(abs, pipeline_dir)`.
- **Do NOT run the audit subprocess with default output flags** — defaults write `dnallm-mark/data/n_audit.json`, `dnallm-mark/data/n_audit.csv`, `pipeline/eval_subsets.json`, and regenerate `DATA.md` `[VERIFIED: script/audit_n_frequencies.py:603-615 — argparse defaults REPO_ROOT/dnallm-mark/data, REPO_ROOT/pipeline/eval_subsets.json, REPO_ROOT/DATA.md]` — clobbering committed artifacts.
- **Do NOT let the wizard wizard-compute benchmark semantics** (row counts, survivor counts) — the gauntlet subprocesses own all computation (binding constraint 5).
- **Do NOT use `Binding(priority=True)` for the digit keys** (verified semantics above — it would break Input typing).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|------|
| Registry load + overlay merge + collision fail-fast | A second loader | `pipeline/registry_loader.py` (`load_models_registry`/`load_datasets_registry`) | The single merge seam (D-08); a second implementation diverges from the pipeline's view |
| Row counts / non-ACGT / subset survival | CSV re-counting in services | subprocess `script/audit_n_frequencies.py` (D-07) | Filter semantics mirror the pipeline EXACTLY (strict/tolerant charsets, length window) — re-implementation would silently disagree |
| Matrix enumeration precheck | Re-implement filters | subprocess `run_sweep.py --dry-run` (D-06) | CLI parity; the dry-run path IS the pure-planning function |
| Metric registry | A new metric list constant home | tier-1 PARITY TEST against `SUITE_CANONICAL` (see below) | Single authority enforced by test; runtime import of export_runs is impossible from TUI (numpy top-level import + script/ not on the TUI bootstrap sys.path — verified `tui/__main__.py` inserts only REPO_ROOT and REPO_ROOT/pipeline) |
| XDG roots + atomic writes | New path/write code | `tui/services/settings.py` (`config_dir()`, `atomic_write`) | D-04 seam; tmp+os.replace tear-free |
| Tolerant JSON reads | bare `json.load` | `artifact_loader.load_json_artifact` (None sentinel) | The gauntlet/manifest/custom-file reads must never crash the console |
| Subprocess execution | shell strings | argv LIST + absolute script paths + explicit env | Repo discipline (T-03-10); registry values must never pass through a shell |

**Key insight:** the metric enum. `tui/services` cannot import `script/export_runs.py` at runtime (it imports numpy at module top and script/ is not on the TUI sys.path), but tier-1 tests CAN (`tests/conftest.py:43` puts script/ on sys.path; `test_export_runs.py:59` imports it). The established repo pattern (MODEL_CARD_* casing twins + parity tests) applies: a frozen `tui/services` constant (28 names, below) + a tier-1 test asserting equality with `export_runs.SUITE_CANONICAL` — the test lane enforces the single authority without a runtime import.

## Common Pitfalls

### Pitfall 1: Audit subprocess clobbers committed repo artifacts
**What goes wrong:** running `audit_n_frequencies.py` without overriding `--data-dir`/`--subsets-out`/`--data-md` overwrites `dnallm-mark/data/n_audit.json`, `n_audit.csv`, `pipeline/eval_subsets.json`, and regenerates `DATA.md` — committed files the leaderboard depends on.
**Why it happens:** the argparse defaults point at the repo's published artifact locations (the script's maintainer purpose).
**How to avoid:** the gauntlet service ALWAYS passes all four flags to temp paths. **Add a regression test asserting the repo files are byte-unchanged after a gauntlet run.**
**Warning signs:** `git status` shows DATA.md/n_audit.json modified after any gauntlet test/manual run.

### Pitfall 2: Audit subprocess merges the operator's REAL custom dir
**What goes wrong:** the audit loads registries through `registry_loader` (by design) — without `DNALLMMARK_CUSTOM_REGISTRY_DIR` set it merges whatever lives at `~/.config/dnallmmark/custom_datasets.json` (this machine already has a real `~/.config/dnallmmark/` with `presets.json` — the probe leaked it live).
**Why it happens:** whole-dir env override is the only isolation mechanism.
**How to avoid:** the gauntlet sets the env var to the staging temp dir for BOTH subprocess legs (dry-run and audit). For the audit leg, an EMPTY temp dir (the candidate is injected via `--registry-dir`, not the overlay) isolates fully.
**Warning signs:** audit output lists tasks the candidate run never asked for.

### Pitfall 3: The `datasets/` prefix + datasets-root arithmetic
**What goes wrong:** `resolve_dataset_dir` strips a literal `datasets/` prefix then joins to `--datasets-root` `[VERIFIED: script/audit_n_frequencies.py:133-149]`. A pipeline-relative custom path (`../../x`) joined to the DEFAULT root (`pipeline/datasets`, one level deeper than the concat base the rel was computed against) resolves one level wrong — my own probe failed exactly this way before switching to the absolute-path staging.
**How to avoid:** the audit gauntlet stages the candidate in its OWN temp registry with an ABSOLUTE `Dataset_path` (pathlib absolute-join replaces the root — verified); path-string resolution of the LANDED relative form is the dry-run + land-schema's job, not the audit's.
**Warning signs:** audit reports `missing: true` for a dataset whose CSVs demonstrably exist.

### Pitfall 4: Absolute paths in the landed registry rows break the trainer
**What goes wrong:** `run_finetune.py` does `base_dir + row["Dataset_path"]` STRING concat — an absolute path yields `pipeline//home/...`.
**How to avoid:** the wizard collects absolute paths (existence checks), the land service converts to `os.path.relpath(abs, pipeline_dir)`. The row detail/gauntlet drill-down shows the operator's absolute form; the registry carries the relative form. Document in the schema $comment.
**Warning signs:** any custom entry whose Model_path/Dataset_path starts with `/`.

### Pitfall 5: Trusting exit codes alone
**What goes wrong:** the audit script exits 0 even when every row is missing (missing rows are warnings by design — verified); a dry-run with filters that intersect to zero still exits 0 with a manifest.
**How to avoid:** parse the artifacts — manifest `cells[]` must contain the candidate key (status `planned`); n_audit `missing == false`, splits `rows > 0`, `unified_eval_n > 0`, declared == measured counts.
**Warning signs:** any gauntlet "pass" that never read its output artifact.

### Pitfall 6: Zero-cell dry-run via missed Train/Dataset_name
**What goes wrong:** a custom dataset with `Train: 0` (or missing) is never enumerated — `_validate_filters` refuses it (verified exit 1), but only when the task is EXPLICITLY filtered; `Dataset_name != key` trips `_validate_dataset_name_alignment` (whole-registry check, verified in source at `pipeline/run_sweep.py:565-603`).
**How to avoid:** the wizard collect-all requires `Train` as a positive int and stamps `Dataset_name = key`; the schema marks both required.
**Warning signs:** gauntlet dry-run failures naming the candidate key.

### Pitfall 7: D-09 skip hides disabled rows from the management view
**What goes wrong:** after the skip lands, `tui/services/registries.load_*_entries` (which route through registry_loader) no longer see disabled entries — but UI-SPEC #10 requires disabled rows to stay VISIBLE with `（已停用）` ("you cannot re-enable what you cannot see").
**How to avoid:** a second read path in the custom-entries service: direct tolerant read of the user-owned custom file (including disabled), keyed against official keys for the badge/official-vs-custom distinction. The overlay-merged loaders remain the pipeline-visible view (used for counts of ENABLED customs in the sweep-visible sense; the count segment counts landed entries from the direct read — visible = counted).
**Warning signs:** disabled entries disappearing from the selection table after landing.

### Pitfall 8: Metric count is 28, not 27
**What goes wrong:** the UI-SPEC #12 text says "27 names" — the verified frozenset has **28**.
**How to avoid:** treat 28 as truth; the parity test pins it. `SUITE_CANONICAL` verbatim `[VERIFIED: script/export_runs.py:241-247]`: `"accuracy", "precision", "recall", "f1", "f1_micro", "f1_weighted", "f1_samples", "precision_micro", "precision_weighted", "precision_samples", "recall_micro", "recall_weighted", "recall_samples", "mcc", "matthews_correlation", "AUROC", "AUPRC", "AUROC_ovr", "AUROC_ovo", "TPR", "TNR", "FPR", "FNR", "mse", "mae", "r2", "pearsonr", "spearmanr"` (28 entries, counted programmatically this session). The committed registries use only 5 of these (`AUPRC, f1, mcc, r2, spearmanr` `[VERIFIED: observed dataset registry metric values]`) — the SelectionList offers all 28.

### Pitfall 9: Wizard esc vs. modal esc
**What goes wrong:** the Phase 8 modals bind `escape → dismiss`; the wizard needs esc-cancel-CONFIRM when values exist (UI-SPEC destructive list) and validation-report/gauntlet esc must RETURN to the wizard with values intact (not dismiss it).
**How to avoid:** the wizard family is one ModalScreen whose esc handler branches on `self._phase` (form vs report vs gauntlet-result); the report/gauntlet are VIEWS inside the same modal (not separate pushed screens), so dismissal never destroys `self._values`. Only the explicit esc-confirm, a land, or a used undo clears the form (UI-SPEC Interaction #4).

### Pitfall 10: `e` toggle write path
**What goes wrong:** the `e` enable/disable toggle writes `enabled` in the user-owned file — this is one of the ONLY three sanctioned custom-registry writes (gauntlet-land, undo, toggle — UI-SPEC Interaction #3); wiring it through anything but the atomic-write service risks a torn file the loader then fail-louds on.
**How to avoid:** all three writes go through `custom_entries` service → `atomic_write`; toggle re-writes the whole file (read-modify-write of the small JSON — atomicity makes this safe).

### Pitfall 11: Dataset row-key fields the pipeline reads directly
**What goes wrong:** `run_finetune.py` reads `row["Dataset_name"]` with DIRECT key access (KeyError, not .get — verified at `pipeline/run_finetune.py:998`) — a custom entry omitting `Dataset_name` crashes the trainer mid-run.
**How to avoid:** the wizard/schema stamps `Dataset_name = key` and `Train/Dev/Test` as ints; collect-all validates presence + types; the dry-run gauntlet's `_validate_dataset_name_alignment` backstops.

## Code Examples

### The official registry field shapes (verbatim, for the custom-schema mirror)

`pipeline/models_info.json` — 62 entries, EVERY entry carries exactly these 16 fields `[VERIFIED: field-frequency probe over all 62 entries this session]`:

```json
{
 "Mean_token_length": 6,
 "Model_name": "plant-dnabert-6mer",
 "Model_path": "models/plant-dnabert-6mer",
 "Model_size": "100M",
 "Tokenizer": "6mer",
 "architecture": "Bert",
 "context_len (bp)": 2000,
 "huggingface": "zhangtaolab/plant-dnabert-6mer",
 "mean_token_len": 6,
 "modelscope": "zhangtaolab/plant-dnabert-6mer",
 "name": "PlantDNABERT-6mer",
 "series": "PDLLMs",
 "size (M)": 89,
 "species": "plants",
 "tokenizer": "6-mer",
 "type": "MLM"
}
```

Field types observed across all 62: `context_len (bp)` int-or-str; `size (M)` float-or-int; every other field str/int as above. Note the casing twins (`Tokenizer` "6mer" vs `tokenizer` "6-mer") — the TUI reads `Tokenizer` (MODEL_CARD_* discipline).

`pipeline/datasets_info.json` — 50 entries, EVERY entry carries exactly these 17 fields `[VERIFIED: field-frequency probe over all 50 entries]`:

```json
{
 "Category": "Plants",
 "Dataset_name": "BEND__CpG_methylation",
 "Dataset_path": "datasets/BEND/CpG_methylation",
 "Dev": 109717,
 "Index": 47,
 "Test": 106227,
 "Train": 743095,
 "citation": "Marin et al., ...",
 "download_url": "https://...",
 "download_url_alternates": "https://...",
 "labels": 7,
 "length": 512,
 "license": "Unspecified",
 "metric": "AUPRC",
 "preprocessing": "...",
 "source": "https://...",
 "type": "multilabel"
}
```

Enum vocabularies (verbatim observed values) `[VERIFIED: registry probes]`:
- `Category`: `Animals`, `Microbe`, `Multiple`, `Plants` (UI-SPEC adds none)
- `type` (dataset): `binary`, `multiclass`, `multilabel`, `regression` — NOTE the requirement wording "Task_type" maps to the registry field **`type`** (UI-SPEC Auto-Default #11)
- `metric`: registry uses 5 of the 28 SUITE_CANONICAL names
- model `type`: MLM/CLM/DL per the canonical entries service; model `species` free text (observed values include `plants`, `""`)
- model `tokenizer`: UI-SPEC lists `BPE / singlebase / one-hot / 6-mer / overlapped 6-mer` over observed values (SelectionList over the registry's observed values, sorted — D-03)

### The recommended custom-entry schema (planner-refinable)

```jsonc
// ~/.config/dnallmmark/custom_models.json — TOP LEVEL STAYS {key: entry}
{
  "my-custom-dna-lm": {
    // ... all 16 official model fields (the wizard fills; blanks = "") ...
    "enabled": true,                       // D-09: absent == enabled; ONLY literal false disables
    "quirks": {                            // D-02: recorded + warned; execution mapping = Phase 11
      "no_safetensors": false,             //   names mirror the pipeline quirk lists' semantics
      "fp32_only": false,                  //   (model_not_use_safetensors / models_only_support_fp32 /
      "special_head": false                //    special_models — verified list names in_finetune.py:879-930)
    }
    // schema provenance per run_template.json discipline: an inert
    // per-entry "schema_version": 1 is safe (the pipeline reads named keys only)
  }
}
```

Why extra fields are inert `[VERIFIED: the pipeline reads named keys only]`: `run_sweep.py` reads `Train`, `Dataset_name`; `run_finetune.py` reads `Model_path`, `Dataset_name`, `Dataset_path` (+ per-model quirk lists it MEMBERSHIP-TESTS by name — a custom model is in none of them, which is exactly the D-02 warning); `export_runs.py` joins specific card fields. No consumer iterates/validates entry keys — verified across all three consumers' source this session.

### The staged gauntlet invocation (service skeleton)

```python
def run_dry_run_gauntlet(self, kind, candidate_key, entry) -> GauntletItem:
    with tempfile.TemporaryDirectory(prefix="dnallmmark-gauntlet-") as tmp:
        staging = Path(tmp) / "overlay"
        staging.mkdir()
        # existing custom + candidate (validated collision-free upstream)
        merged = dict(self._store.read_raw(kind) or {})   # direct file read
        merged[candidate_key] = {**entry, "enabled": True}
        atomic_write(staging / f"custom_{kind}.json",
                     json.dumps(merged, indent=4, ensure_ascii=False))
        out = Path(tmp) / "out"
        argv = [sys.executable, str(REPO_ROOT / "pipeline" / "run_sweep.py"),
                "--dry-run",
                "--models" if kind == "models" else "--tasks", candidate_key,
                "--tasks" if kind == "models" else "--models",
                self._counterpart_key(kind),     # one official Train-truthy counterpart
                "--seeds", "42", "--output-root", str(out)]
        env = {**os.environ,
               "DNALLMMARK_CUSTOM_REGISTRY_DIR": str(staging)}
        proc = subprocess.run(argv, capture_output=True, text=True,
                              timeout=self._timeout, env=env)   # LIST argv, never shell
        if proc.returncode != 0:
            return GauntletItem.failed(proc.stdout + proc.stderr)  # verbatim lines
        manifest = artifact_loader.load_json_artifact(out / "sweep_manifest.json")
        cells = (manifest or {}).get("cells") or []
        planned = [c for c in cells
                   if isinstance(c, dict) and candidate_key in (c.get("model"), c.get("task"))]
        ok = bool(planned) and all(c.get("status") == "planned" for c in planned)
        return GauntletItem(ok, f"{len(planned)} cell(s) 计划成功", proc.stdout)
        # tmp cleanup: TemporaryDirectory context — nothing survives, repo untouched
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Footer/Header widgets on base screens | custom 1-row Static bars (D-13/D-15) | Phase 9 | row-neutral; binding declarations stay the single key-map source (`_binding_row` reuse) |
| per-cell `json.load` at 5 sites | registry_loader overlay seam | Phase 7 (landed) | the wizard consumes it; D-09 adds the enabled skip |
| no user-owned TUI state | XDG roots + atomic writes + env-injected tests | Phase 8 (landed) | custom registries land on the same rails as presets.json |
| metric custody loosely "metric_key_map in summarize_comparison" | `SUITE_CANONICAL` frozenset in export_runs.py (IN-03 single owner; the old map is gone — grep confirms only a $comment reference remains) | Phase 4 | the wizard's metric enum = SUITE_CANONICAL-28 via parity-tested constant |

**Deprecated/outdated:** `metric_key_map` in `summarize_comparison.py` no longer exists `[VERIFIED: grep across script/ finds only the custody-note comment in export_runs.py:381]` — 09-CONTEXT's canonical_refs row for it is stale; SUITE_CANONICAL is the authority (UI-SPEC #12 already says so).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The dry-run gauntlet's "one official counterpart" model/task can be a FIXED constant (e.g. a tier-1 key) | Gauntlet pattern | Low — any Train-truthy official task / any official model works; planner picks per-kind constants or first-sorted |
| A2 | Wizard numeric fields (`size (M)`, `context_len (bp)`, `labels`, `length`, `Train/Dev/Test`) stored as JSON numbers (int/float), matching official types | Custom schema | Low — collect-all type-checks; the field-type probe documented the official types |
| A3 | The `quirks` field names (`no_safetensors`/`fp32_only`/`special_head`) are free choices this phase (execution mapping is Phase 11) | Custom schema | None this phase — Phase 11 will bind or rename them |
| A4 | Gauntlet subprocess timeout: dry-run < a few seconds, audit bounded by CSV size (thread worker + timeout + cancel, per the 08-06 worker discipline) | Gauntlet | Low — the phase has Claude's-discretion ownership of timeout values |
| A5 | `modelscope`/`huggingface` URL format is free text (no URL syntax validation beyond non-empty) | Validation | Low — official values are org/repo strings, not full URLs; over-validating would reject official-shaped values |
| A6 | The audit gauntlet runs for IMPORTED dataset entries too (per-entry sequential, UI-SPEC #6) — same staged mechanics | Gauntlet | Low — already pinned by UI-SPEC Auto-Default #6 |

## Open Questions (RESOLVED 2026-10-12 — dispositions inline)

1. **Does the model-side gauntlet need more than the dry-run?**
   - What we know: UI-SPEC says model entry → `dry-run 预检` only; dataset entry → dry-run AND audit (there is no audit equivalent for models — n_audit is dataset-only, verified).
   - What's unclear: whether the model gauntlet should also probe the Model_path directory existence (the dry-run never touches paths).
   - Recommendation: collect-all already checks path existence (advisory live + authoritative submit); no extra gauntlet item. Match UI-SPEC exactly.
2. **Import gauntlet ordering when a file carries N entries**
   - What we know: UI-SPEC #6 — per imported entry, sequentially, same panel; failing entries revert individually.
   - Recommendation: validate file (schema + collisions, collect-all) → for each entry in file order: run gauntlet → land on all-✓ → next. A later-entry failure leaves earlier lands intact (entry-level semantics).
3. **Whether `Index` (dataset field) matters for customs**
   - What we know: official entries carry `Index` (an ordering int); no pipeline consumer reads it in run_sweep/run_finetune (verified reads).
   - Recommendation: stamp a neutral value (e.g. 9999) or omit; planner decides — the field is inert to every consumer verified.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 venv (`.venv`) | all lanes | ✓ | 3.13 | — |
| textual | wizard/screens/Pilot | ✓ | 8.2.8 | — |
| platformdirs / jsonschema | services | ✓ | 4.13.0 / 4.26.0 | — |
| uv | make lanes | ✓ | 0.12.23 (CLAUDE.md) | — |
| node ≥18 | make test JS lane | ✓ | present (Makefile guard) | — |
| GPU / dnallm / torch (CPU lanes) | NOT required this phase | torch present on GB10 host only | 2.11.0+cu130 | CI lanes never see it (constraint) |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none.

Note: the real `~/.config/dnallmmark/` exists on this machine with `presets.json` — every tier-1/tier-2 test MUST inject `DNALLMMARK_TUI_CONFIG_DIR`/`DNALLMMARK_CUSTOM_REGISTRY_DIR` at tmp_path (the whole-dir env override pattern; tests never touch the real home).

## Security Domain

`security_enforcement: true`, ASVS level 1, block_on high — assessed for this phase's surfaces:

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | local single-user TUI; no auth surface |
| V3 Session Management | no | — |
| V4 Access Control | yes (file-write authorization) | official registry files have NO write path (binding constraint 11 — verified: registry_loader is read-only over both sides); custom files written only via atomic_write under XDG root |
| V5 Input Validation | yes | wizard fields → collect-all validator; imported registry files are UNTRUSTED JSON (run_template.json T-08-04 discipline): jsonschema/structural validation before merge, never eval/exec, no dynamic interpretation of any string |
| V6 Cryptography | no | — |
| V8 Data Protection | partial | atomic writes (tear-free); temp staging dirs under `tempfile` auto-cleanup; no secrets |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious imported registry file (oversized/深嵌套 JSON, crafted keys) | Tampering/DoS | schema/structural validation only, size-bounded reads via artifact_loader tolerance; nothing evaluated; subprocess argv LIST so registry values never reach a shell (T-03-10) |
| Path traversal via wizard/import path fields | Tampering | paths are operator-entered for THEIR machine; the landed rows store pipeline-relative paths; export writes to operator-chosen path (same trust class as Phase 8 template export — established surface) |
| Committed-artifact clobber via gauntlet | Tampering | all audit outputs to temp (Pitfall 1) + byte-unchanged regression test |
| Cross-entry async result confusion (gauntlet) | Tampering (integrity of results) | run-id message tags (WR-02 pattern) — UI-SPEC Interaction #7 pins it |
| Env-var injection into subprocesses | Escalation | gauntlet constructs env explicitly ({**os.environ, one override}); no operator-controlled env content |

## Project Constraints (from CLAUDE.md)

- **ruff + ty gates are mandatory** (memory: lint AND typecheck from Phase 3/7 on) — `make lint` covers tui/ via the PHASE8_TUI glob (new Phase 9 files join automatically, zero Makefile edits); `make typecheck` needs `--group tui` (already in the recipe).
- **services layer stays textual-free** — `tests/tui/test_import_lock.py` AST-walks every `tui/services/*.py`; new services comply (import-lock test is non-vacuous and pattern-matched by glob).
- **i18n single home** — all new Chinese copy in `tui/strings.py` (NAV_/ABOUT_/WIZ_/WIZM_/WIZD_/GAUNTLET_/SEL_ prefixes per UI-SPEC); the zero-Chinese-literals grep tests extend to the new screen modules (`test_pilot_env_check.py:624`, `test_pilot_selection.py:1302` patterns).
- **fail-fast collect-all discipline** — fourth instance of the `_validate_filters` pattern; every problem listed, numbered, field-definition order.
- **DNALLM sibling repo is read-only** (memory) — not touched this phase.
- **GPU runs need no new authorization for bounded smoke** (memory, 2026-10-11) — but this phase needs NO GPU at all: dry-run + audit are CPU/stdlib (proven).
- **Branch workflow** (memory): autorun is the standing dev branch; commits land there.
- Test-file conventions: tier-1 `tests/tui/test_services_*.py` (sync, headless), tier-2 `tests/tui/test_pilot_*.py` (async, `asyncio_mode=auto`, `await pilot.pause()` before assertions, fake-injection via constructor seams).

## Sources

### Primary (HIGH confidence — probed/verified this session)

- `pipeline/registry_loader.py` (whole file) — overlay mechanics, env override, collision fail-fast, D-09 landing point
- `pipeline/run_sweep.py` (whole file) — dry-run path, `_validate_filters`/`_validate_dataset_name_alignment`/`_validate_subset_file`, manifest shape, argv discipline
- `script/audit_n_frequencies.py` (whole file) — kernels, CLI flags, default output paths, n_audit.json shape
- `pipeline/run_finetune.py:875-1010` — quirk lists (verbatim names), `base_dir + row[...]` string-concat path resolution, `row["Dataset_name"]` direct access
- `script/export_runs.py:241-247` — SUITE_CANONICAL verbatim (28 names, counted)
- `pipeline/models_info.json` / `pipeline/datasets_info.json` — full field-frequency + enum probes (all 62/50 entries)
- Live probes (temp dirs, this session): staged-overlay dry-run pass/fail ×3, audit subprocess pass/fail ×3 (incl. the default-output and real-overlay leak pitfalls), Pilot digit-vs-Input proof on textual 8.2.8
- textual 8.2.8 installed-package source: `Input._on_key`, `Binding.__init__` (priority flag), `SelectionList`/`Selection`/`Checkbox`/`DataTable` APIs, `getters.app`
- `tui/app.py`, `tui/services/{settings,registries}.py`, `tui/screens/selection.py` (modal family, bindings, cursor idiom, column widths), `tui/strings.py`, `tests/tui/*` (tier patterns, import lock, i18n locks), `Makefile`, `pyproject.toml`, `schemas/run_template.json`, `tests/conftest.py`

### Secondary (MEDIUM confidence)

- `[CITED: textual.textualize.io/guide/input]` — binding search order (focused widget upward), `priority=True` checked prior to focused widget (cross-check of the installed-source + Pilot findings)

### Tertiary (LOW confidence)

- None — no claim in this document rests on unverified training knowledge

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new packages; every pinned version re-verified in `.venv`
- Architecture: HIGH — every gauntlet mechanic probed live with exit codes and artifacts; wizard control semantics Pilot-proved on the exact installed version
- Pitfalls: HIGH — five of the eleven pitfalls were reproduced (not hypothesized) during the probes
- Schema: HIGH — both registry shapes quoted from full-population field probes; consumer reads verified in source

**Research date:** 2026-10-12
**Valid until:** 2026-11-12 (stable internal codebase; textual pinned `<9`)
