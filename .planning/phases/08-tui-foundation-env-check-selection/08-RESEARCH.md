# Phase 8: TUI Foundation (Env Check & Selection) - Research

**Researched:** 2026-10-11
**Domain:** Textual TUI foundation over existing Python pipeline seams (env_smoke kernel refactor, k9s-style selection, XDG persistence, two-tier test harness)
**Confidence:** HIGH (repo facts verified by direct file reads this session; Textual/platformdirs API facts fetched from official docs + PyPI registry today; UI-shape recommendations MEDIUM where they rest on design judgment)

## Summary

Phase 8 builds the `tui/` package from zero while refactoring exactly one pipeline file (`pipeline/env_smoke.py`, D-02). The heavy architectural lifting was already done at milestone level (`.planning/research/SUMMARY.md`, `ARCHITECTURE.md`, `STACK.md`, all 2026-10-11, HIGH confidence): a thin read-plan-launch-observe shell with a textual-free `tui/services/` layer, subprocess/pure-import seams into `pipeline/`, XDG config persistence, and a two-tier test harness (tier-1 headless services, tier-2 Pilot with injected fakes). This phase research verified every in-repo seam the plan will touch and pinned the Textual 8.2 API facts the two visible surfaces need.

Three verified facts dominate implementation risk. First, **Textual's DataTable has no built-in multi-select** — a k9s mark-set must be built as app state keyed on stable `RowKey`s (kernels for this are documented and simple, but it is custom code, not a widget flag) [VERIFIED: textual.textualize.io/widgets/data_table/]. Second, **the env_smoke refactor is contract-pinned from three sides at once**: the PASS:/FAIL: stdout bytes (E2' greppable contract), the exit code, and — easily missed — three source-grep tests in `tests/test_run_finetune_contracts.py:1593-1657` that assert literal strings and literal wiring (`results.append(check_peft())` inside `main()`, version labels in the docstring) which D-02 says stay untouched. Third, **`pipeline/` is a sys.path root, not a package** (no `__init__.py`), so `tui/services` importing `env_smoke`/`registry_loader`/`artifact_loader` requires a bootstrap sys.path insert mirroring `tests/conftest.py` — both at TUI runtime and in tests.

The stack delta is verified current and tiny: textual 8.2.8 (unchanged since 2026-06-30; `>=8.2,<9` still resolves to it), platformdirs 4.13.0 (4.12.4 already present in the repo venv as a jupyter-core/wandb transitive — `user_state_dir('dnallmmark')` empirically returns `/home/forrest/.local/state/dnallmmark`, exactly the D-04 layout), pytest-asyncio 1.4.0 (dev group; requires `pytest<10,>=8.4`, repo has 9.1.1).

**Primary recommendation:** Land the non-retrofittable spine first in one wave (pyproject `[tui]` group + ty/ruff/Makefile/CI wiring + `tui/` skeleton with sys.path bootstrap + the 5-line services-textual-free import test), then the env_smoke structured-return refactor with a byte-stability golden test, then the two screens (env-check panel with thread-worker kernels; selection tables with mark-set state machine) — Pilot tests against constructor-injected fakes throughout.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** 批准 textual-the-library 进 CPU CI 测试通道（library yes, display/GPU runtime no）：现有 CI test job 的 `uv sync` 增加安装 `[tui]` 组（textual + platformdirs），Pilot 测试以 headless driver 运行（无显示、无 GPU、无 dnallm）；零新增 CI job；data/gpu lane 永不见 textual。— reversible
- **D-02:** 结构化返回重构：将 `pipeline/env_smoke.py` 各检查内核（`check_numpy`/`check_version_pins`/`check_dnallm`/`check_peft`/`check_cuda`/`check_dataset_dirs`/`check_matmul`）重构为返回结构化结果（名称/状态/详情），`main()` 的 PASS:/FAIL: 打印行与退出码契约逐字节保持（E2' 双门的 greppable 契约，现有测试锁定不动）。TUI 服务层 import 内核（tui→pipeline 依赖方向），绝不子进程解析 stdout、绝不在 TUI 重写检查。— costly
- **D-03:** 检查执行绝不阻塞事件循环：全量检查在 worker thread（`@work(thread=True)`）运行，逐项结果异步回填面板；同日缓存命中时即时呈现。GPU 触碰内核（CUDA/matmul）只在真机（GB10）上实际执行；CI 服务测试用注入 fake，不跑真内核。
- **D-04:** state 与 config 分离（platformdirs 双根）：环境检查结果（含时间戳、逐项状态）→ XDG state dir（Linux `~/.local/state/dnallmmark/env_check.json`）；用户保存的预设/模板/会话选择/设置 → `~/.config/dnallmmark/`。测试经 env-var 注入临时目录（沿用 `DNALLMMARK_CUSTOM_REGISTRY_DIR` 整目录覆盖先例；TUI 侧具体变量名 planner 定）。— reversible
- **D-05:** 缓存语义：同日 = 日历日比较（"上次检查"日期可见）；手动刷新动作强制全量重检；部分失败也整体持久化（逐项状态带 FAIL 详情），下次启动直接呈现失败项。快检（ENV-04）不落盘为"全量结果"——它是启动前的轻量子集重验，结果即算即用。
- **D-06:** 预设从 `pipeline/sweep_priorities.json` 派生（单一来源，零硬编码重复）：tier-1 E2E 对、tier-2 arena 代表由服务层读该文件派生；"全部" = overlay 合并注册表（`pipeline/registry_loader.py`）全量；"自定义保存" = 用户 XDG 文件。选择集以注册表键名为稳定 row_key。— reversible
- **D-07:** 模板走 schemas/ 严格 JSON Schema 纪律：运行配置模板（模型×任务×种子×PEFT×变体×GA 完整参数集）定义 `schemas/` 下 schema + 顶层 `schema_version` 字段；导入时 jsonschema 校验、失败一次性全列问题（fail-fast 全列纪律）；`sweep_priorities.json` tier 互转作为服务层纯函数。Phase 11 run-config 屏消费同一 schema。— one-way
- **D-08:** 在场列读已提交产物，TUI 零计算：每行 ✓ 在场 / ✗ 缺失 + 行数来自 `dnallm-mark/data/n_audit.json`；刷新走 audit 重跑（CLI 先例，Phase 10 数据管理器接管面板化）。启动时的活体目录检查用 env_smoke `check_dataset_dirs` 内核（D-02），浏览行的静态来源是 n_audit.json。缺数据项路由数据管理（Phase 8 呈现指引，面板本体 Phase 10）。— reversible
- **D-09:** 门判定现在落地，阻断钩子 Phase 11 接线：Phase 8 交付 env-gate 判定服务（纯逻辑：哪些 FAIL 关键、何为可启动）+ 面板可见呈现 + 快检内核（launch-required 子集轻量重验，服务化）。实际阻断与快检调用点在 Phase 11 启动屏接线。— reversible
- **D-10:** registry_loader 不做 platformdirs 整合：保持 Phase 7 手写 env>XDG>home stdlib 解析器不动；TUI settings 服务直接用 platformdirs。整合记 Deferred。— reversible

### Claude's Discretion

- `tui/` 包内部结构（`app.py` 组合根、`screens/`、`services/`、constants/strings 模块命名——research 建议的骨架为准）
- 选择屏具体 UI 形态（模型/数据集独立浏览的实现：单屏切换 vs tab；矩阵辅助视图入口）——k9s 心智模型为准（type-to-filter、空格标记、键盘优先）
- env-check 面板异步填充 UX（逐项 spinner、详情下钻呈现）
- i18n constants 模块具体结构与文案键组织
- TUI 侧测试 env-var 的具体变量名与 settings 服务 API 形状
- Pilot（tier-2）测试的具体断言集与 fake 注入形态
- tier 预设派生函数与模板互转函数的签名
- 实现期建议加载 `tui-design` skill（终端 UI 打磨规范）——执行 agent 的实现质量工具，非架构约束

### Deferred Ideas (OUT OF SCOPE)

- **目录设置**（项目根与存储根分离配置、显式覆盖时 TUI 传参给下游脚本）→ Phase 11 run-config/设置面；Phase 8 settings 服务设计不预设死路径假设
- **registry_loader platformdirs 整合**（STATE 遗留开放项）→ D-10 裁定不做；除非维护者提出否则永久搁置
- **前端展示训练平台（GPU 型号）列**（Phase 7 延续）→ 展示层工作，未来单独安排
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ENV-01 | TUI 启动即运行完整环境检查（复用 env_smoke 内核），逐项 ✓/✗ + 详情 | D-02 structured-return refactor surface fully mapped (env_smoke.py:174-448); D-03 thread-worker + post_message pattern verified against official docs |
| ENV-02 | 结果持久化 + 检查日期显示 + 刷新动作 + 同日读缓存 | platformdirs `user_state_dir` empirically verified → `~/.local/state/dnallmmark/env_check.json`; calendar-day comparison semantics defined (D-05) |
| ENV-03 | 关键 FAIL 阻止进入启动流程；缺数据项引导数据管理 | D-09 env-gate pure-logic service + visible presentation; blocking hook deferred to Phase 11 by decision |
| ENV-04 | 每次启动任务前的快检（轻量子集重验） | Quick-check kernel service shape defined (D-09: computed on demand, not persisted as full result) |
| SEL-01 | 模型/数据集独立浏览 + k9s 式过滤 + 空格标记 + 稳定 row_key + 只读矩阵辅助视图 | DataTable API verified (stable row keys via `add_row(key=...)`, `cursor_type="row"`, `sort()`); **no built-in multi-select** — mark-set is app state; registry filter fields enumerated (species/type/size; Category/type/metric) |
| SEL-02 | 预设一键选择（tier-1/tier-2/全部/自定义保存） | `sweep_priorities.json` two-tier shape verified (pair dicts / model-name strings); derivation via registry overlay keys (D-06) |
| SEL-03 | 模板 JSON 导入/导出 + 校验 + sweep_priorities tier 互转 | schemas/ strict-schema + schema_version + synthetic-fixture precedent verified (schemas/flops_report.json); jsonschema already in dev group |
| SEL-04 | 每行本地数据状态（✓/✗ + n_audit 行数） | `n_audit.json` shape fully verified (50 tasks, `missing` flag, per-split `rows`); live check stays in env_smoke `check_dataset_dirs` (D-08) |
| I18N-01 | 中文为主界面文案（constants 模块，术语保留英文） | Constants-module convention defined; exact operator string "上次检查: YYYY-MM-DD HH:MM" is requirement-verbatim |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **GSD workflow enforcement:** all edits through GSD entry points — this phase is planned work via `/gsd-plan-phase` / `/gsd-execute-phase`, satisfied by the phase workflow itself
- **Fix discipline:** surgical fixes only; Phase 8's pipeline touch is exactly the env_smoke kernel refactor (D-02) — zero other pipeline contract files (binding constraint 6)
- **Static-only hosting** (web side) — not touched by this phase
- **CI feasibility:** no GPU, no dnallm, no new CI jobs (binding constraints 1-2); textual-the-library allowed in CPU test lane per ratified D-01
- **Python conventions:** module docstrings with contract statements, Google-style `Args:/Returns:`, `# =====` section banners, bilingual EN/zh comments acceptable
- **Memory directives:** ruff AND ty gates from Phase 3 on and must cover all new `tui/` code; DNALLM sibling repo read-only; GPU smoke allowed as bounded plan tasks on this GB10 host (env_smoke docstring records the sanction), CI stays GPU-free

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Env-check execution (7 kernels) | TUI services layer (imports `pipeline/env_smoke` kernels, runs in `@work(thread=True)` worker) | pipeline module (kernel logic, structured returns) | D-02/D-03: kernels are the single implementation; TUI never re-implements or subprocess-parses |
| Env-check rendering (✓/✗ panel, drill-down, date line) | Textual screen (`screens/`) | — | presentation only; receives results via custom `Message` posted from the worker |
| Env-check persistence | TUI services (platformdirs state dir) | — | D-04: `~/.local/state/dnallmmark/env_check.json`; atomic write |
| Env-gate judgment (critical vs routing) | TUI services (pure function over check results) | — | D-09: pure logic now, Phase 11 wires the block |
| Selection browsing/filtering | Textual screen (DataTable) | TUI services (registry view) | widget renders; filtering is a pure function over the registry list |
| Mark-set state (spacebar, stable row_keys) | Textual screen + app state | — | no DataTable multi-select exists; state keyed on registry keys (D-06) |
| Presets (tier-1/tier-2/all/custom) | TUI services (derive from `sweep_priorities.json` + overlay registry) | user XDG files (saved customs) | single source of truth, zero hardcoding (D-06) |
| Template import/export/validation | TUI services (pure functions) | `schemas/` (strict JSON Schema, D-07 one-way contract) | schema is the cross-phase contract Phase 11 consumes |
| Presence column | TUI services (read `n_audit.json`) | filesystem (live dir check in env_smoke kernel) | D-08: static artifact read, TUI computes nothing |
| i18n copy | `tui` constants module | — | single home for Chinese-primary strings |
| CLI parity for env check | `pipeline/env_smoke.py` CLI (existing, byte-stable) | — | the CLI face already exists and is the E2' gate; TUI adds no new execution path |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| textual | 8.2.8 (`>=8.2,<9`) | TUI framework: App/Screen/DataTable/workers/Pilot | [VERIFIED: PyPI JSON API, fetched 2026-10-11] version 8.2.8, uploaded 2026-06-30 — no newer release exists; `requires_python <4.0,>=3.9` (repo floor 3.13, CI 3.14 probe both fine); pure-Python wheel, deps are `markdown-it-py`, `mdit-py-plugins`, `platformdirs<5,>=3.6.0`, `pygments`, `rich>=14.2.0` (rich/pygments/markdown-it-py already in uv.lock transitively per milestone STACK research) |
| platformdirs | 4.13.0 (`>=3.6,<5`) | XDG config/state dir resolution | [VERIFIED: PyPI JSON API] 4.13.0 uploaded 2026-10-11; `requires_python >=3.11` (repo 3.13 OK). Already present in repo venv at 4.12.4 (transitive of jupyter-core + wandb — `uv pip show` verified); declared in `[tui]` to stop transitive-luck imports. **Empirically verified:** `user_state_dir('dnallmmark')` → `/home/forrest/.local/state/dnallmmark`; `user_config_dir('dnallmmark')` → `/home/forrest/.config/dnallmmark` — exactly the D-04 split |
| pytest-asyncio | 1.4.0 (`>=1.4,<2`, **dev group**) | runs `App.run_test()` Pilot tests under pytest 9.1.1 | [VERIFIED: PyPI JSON API] 1.4.0 uploaded 2026-05-26; `requires_dist` includes `pytest<10,>=8.4` — compatible with repo `pytest>=9.1.1`; `asyncio_mode = "auto"` documented by Textual's testing guide [CITED: textual.textualize.io/guide/testing/] |
| jsonschema | already in dev (`>=4.26.0`) | template import validation (D-07) | [VERIFIED: pyproject.toml:19-29 — dev group lists `"jsonschema>=4.26.0"`] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| textual-dev | 1.8.0 | `textual run --dev` hot-reload devtools | **Never in a committed group** (constraint 10); on demand via `uv run --group tui --with textual-dev==1.8.0 …` [CITED: .planning/research/STACK.md] |
| pytest-textual-snapshot | — | SVG golden snapshots | **NOT this phase** — TEST-01 (Phase 12) owns snapshot goldens; Phase 8 Pilot tests are behavioral assertions only |

**Installation (pyproject delta — the full surgical change):**

```toml
[dependency-groups]
# ... existing data / dev / gpu unchanged ...
tui = [
    "textual>=8.2,<9",
    "platformdirs>=3.6,<5",
]
# dev group gains exactly one line: "pytest-asyncio>=1.4,<2"

[tool.pytest.ini_options]
asyncio_mode = "auto"   # async def TUI tests need no decorator; sync tests unaffected

# [tool.ty.src] include gains "tui"; [tool.ty.environment] extra-paths gains "tui"
```

[VERIFIED: pyproject.toml:10-36 current groups are exactly `data`/`dev`/`gpu` — no `tui` yet; pyproject.toml:59-72 `extra-paths = ["script", "baseline", "pipeline"]` and `include = ["script", "baseline", "tests", "scripts", "pipeline"]` — neither lists `tui`; pyproject.toml:74-86 `[tool.pytest.ini_options]` carries only `testpaths` + `markers` — no `asyncio_mode` yet]

**ty note:** textual ships `py.typed` (verified at tag v8.2.8 by milestone research) → **no** `replace-imports-with-any` entry needed for textual; the existing list (`torch.**`, `dnallm.**`, `transformers.**`, `peft.**`, `datasets.**`, `torch_npu.**`, `evaluate.**` [VERIFIED: pyproject.toml:64]) is untouched.

**Version verification:** textual 8.2.8 (2026-06-30), platformdirs 4.13.0 (2026-10-11), pytest-asyncio 1.4.0 (2026-05-26) — all confirmed today via `pypi.org/pypi/<pkg>/json`.

## Package Legitimacy Audit

Ran `gsd-tools query package-legitimacy check --ecosystem pypi textual platformdirs pytest-asyncio`:

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| textual | PyPI | 8+ yrs (first release 2018 era; current release 2026-06-30) | unknown (seam could not read PyPI stats) | github.com/Textualize/textual | SUS | Approved with flag |
| platformdirs | PyPI | ~5 yrs (4.13.0 released 2026-10-11, i.e. today) | unknown | github.com/tox-dev/platformdirs | SUS | Approved with flag |
| pytest-asyncio | PyPI | ~8 yrs (1.4.0 2026-05-26) | unknown | github.com/pytest-dev/pytest-asyncio | SUS | Approved with flag |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** `textual`, `platformdirs`, `pytest-asyncio` [WARNING: flagged as suspicious — verify before using.] — **context:** all three verdicts derive from the seam's null `weeklyDownloads` signal (its PyPI stats source returned no data), not from any negative finding; all three resolve on the PyPI registry with canonical maintainer repos (Textualize/tox-dev/pytest-dev), and textual/platformdirs were already registry+source-verified in the maintainer-visible milestone research (`.planning/research/STACK.md`, 2026-10-11). The planner should still add a `checkpoint:human-verify` before the `[tui]` group commit per protocol. No postinstall-script class applies (PyPI sdists/wheels; no npm-style lifecycle scripts).

*Per the provenance rule, package facts above are registry-verified; the names themselves come from official Textual documentation (textual is documented at textual.textualize.io, platformdirs at platformdirs.readthedocs.io) and the ratified CONTEXT/milestone decisions, so they are treated as legitimate pending the human-verify checkpoint.*

## Architecture Patterns

### System Architecture Diagram

```text
                    make tui  (uv run --group tui [--group gpu] python -m tui)
                                      │
┌─────────────────────────────────────▼──────────────────────────────────────┐
│ TUI PRESENTATION (textual — the ONLY tier allowed to import textual)       │
│  app.py (composition root: MODES, bindings, service wiring)                │
│  screens/env_check.py   ✓/✗ panel · 上次检查 date · refresh · drill-down   │
│  screens/selection.py   model table ⇄ dataset table · filter input ·       │
│                         spacebar mark-set · presets · matrix aux view      │
│  constants module       Chinese-primary strings (I18N-01)                  │
├────────────────────────────────────────────────────────────────────────────┤
│ TUI SERVICES (ZERO textual imports — locked by a 5-line import test)       │
│  env_check service ── runs kernels in @work(thread=True) worker ──┐        │
│  env_gate service (pure: critical vs routing)   │ posts custom    │        │
│  quick_check service (launch-required subset)   │ Message per     │        │
│  registries service ──► registry_loader         │ item result     │        │
│  selection/presets ───► sweep_priorities.json   └─────────────────► screen │
│  templates service ───► schemas/run_template.json (jsonschema)             │
│  settings service ────► platformdirs config/state roots                    │
├────────────────────────────────────────────────────────────────────────────┤
│ PIPELINE SEAMS (imported, never re-implemented; direction tui → pipeline)  │
│  env_smoke kernels (D-02 structured returns) · registry_loader (overlay)   │
│  artifact_loader (tolerant JSON reads)                                     │
├────────────────────────────────────────────────────────────────────────────┤
│ STATE & ARTIFACTS (filesystem — XDG user roots + repo artifacts)           │
│  ~/.local/state/dnallmmark/env_check.json (checked_at + per-item status)   │
│  ~/.config/dnallmmark/ (settings, saved presets, templates)                │
│  pipeline/{models_info,datasets_info}.json · sweep_priorities.json         │
│  dnallm-mark/data/n_audit.json (presence + row counts)                     │
└────────────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure

```text
tui/
├── __init__.py
├── __main__.py          # python -m tui entry; resolves REPO_ROOT from __file__,
│                        #   inserts REPO_ROOT/pipeline into sys.path (conftest mirror)
├── app.py               # DnallmMarkTui(App) — composition root ONLY
├── constants.py         # (or strings.py) Chinese-primary copy, EN technical terms
├── styles.tcss          # Textual CSS
├── screens/
│   ├── __init__.py
│   ├── env_check.py     # startup check panel (ENV-01..04 presentation)
│   ├── selection.py     # model/dataset tables + mark-set + presets (SEL-01..04)
│   └── matrix.py        # read-only 62×50 overview (auxiliary view)
├── services/            # ZERO textual imports (import test locks this)
│   ├── __init__.py
│   ├── env_check.py     # kernel orchestration + persistence + cache semantics
│   ├── env_gate.py      # pure critical/routing judgment (D-09)
│   ├── quick_check.py   # launch-required subset re-validation (ENV-04)
│   ├── registries.py    # overlay view + filter axes + card columns
│   ├── selection.py     # mark-set model + preset derivation (D-06) + tier interop
│   ├── templates.py     # template IO + jsonschema validation + sweep_priorities interop
│   └── settings.py      # platformdirs roots + env-var overrides (D-04)
└── events.py            # frozen dataclass messages (services → app) — optional
tests/tui/
├── test_services_*.py   # tier 1: headless, no textual, fakes for GPU kernels
└── test_pilot_*.py      # tier 2: App.run_test() Pilot, constructor-injected fakes
```

(Naming within the discretion grant; the load-bearing parts are: services textual-free, screens get services via constructor injection, `python -m tui` resolves paths from `__file__` never CWD.)

### Pattern 1: env_smoke structured-return refactor with byte-stable CLI (D-02)

**What:** each kernel returns a structured result (name / pass-fail / detail lines) while `main()` prints the exact bytes it prints today and returns the same exit code.

**Verified current kernel inventory** [VERIFIED: pipeline/env_smoke.py:174-448 — read in full this session]:

| Kernel | Line | Current signature | Returns |
|--------|------|-------------------|---------|
| `check_numpy` | :174 | `check_numpy(floor_major)` | `bool` |
| `check_version_pins` | :251 | `check_version_pins(pins)` | `bool` |
| `check_dnallm` | :279 | `check_dnallm()` | `bool` |
| `check_peft` | :288 | `check_peft()` | `bool` |
| `check_cuda` | :314 | `check_cuda(torch)` | `bool` |
| `check_dataset_dirs` | :341 | `check_dataset_dirs()` | `bool` |
| `check_matmul` | :386 | `check_matmul(torch)` | `bool` |
| `main` | :411 | `main()` | `0`/`1` via `raise SystemExit(main())` |

`main()`'s current results-list order (7 slots): `check_version_pins(pins)`, `check_dnallm()`, `check_peft()`, then torch-import gate → `check_cuda(torch)` + `check_matmul(torch)` (or two `False` appends + one extra FAIL line when torch is missing), then `check_numpy(read_numpy_floor_major(...))`, then `print_ecosystem_diagnostics()` (non-gating INFO line), then `check_dataset_dirs()`. Module-level imports are stdlib-only (`json`, `re`, `sys`, `tomllib`, `importlib`, `pathlib`) — so the module is CPU/CI-importable today and must stay so.

**Byte-stability obligations the plan must hold (quote-checkable output formats):**

- Header: `=== PIPE-02 env smoke ({REPO_ROOT.name} @ {REPO_ROOT}) ===`
- Per-check PASS/FAIL lines, e.g. `PASS: import {module_name} resolves ({origin})`, `FAIL: import {module_name} — {type(exc).__name__}: {exc}`, `PASS: {package} {installed} == pyproject [gpu] pin`, `PASS: CUDA available, {count} device(s)`, `PASS: device {idx}: {props.name}, {gib:.1f} GiB total memory`, `PASS: small-tensor matmul executed (sum == 512.0)`, `PASS: numpy {numpy.__version__} >= pyproject floor (major >= {floor_major}; dnallm 1.2.1 requires numpy>=2)`, `PASS: all {total} registry dataset dir(s) present on disk`, `FAIL: {len} of {total} registry dataset dir(s) missing on disk (the E2' launch gate):` followed by `  - {name}{note}` lines with the double-nested note, and the torch-missing line `FAIL: torch unavailable — CUDA + matmul checks not run`
- Non-gating INFO line placement (after numpy check, before dataset dirs)
- Trailer: `=== SMOKE RESULT: PASS (all checks green) ===` / `=== SMOKE RESULT: FAIL ({failed} check group(s) failed) ===`
- Exit code: `raise SystemExit(main())` → 0/1

**The three source-grep tests that must stay green, untouched** [VERIFIED: tests/test_run_finetune_contracts.py:1593-1657]:

1. `test_env_smoke_carries_zero_stale_version_labels` — asserts `"0.8.0" not in src`, `"1.2.1" in src`, `"pyarrow>=15,<26" not in src`, `"3.2.0" not in src`, `"datasets<=5.1.0" in src` over the whole file → **docstring/version labels must survive the refactor verbatim**.
2. `test_env_smoke_docstring_records_the_smoke_sanction` — first 4200 chars must contain `"2026-10-11"`, `"sanction"` (case-insensitive), `"bounded"` (ci), `"dual"`+`"gate"` (ci), and `"GPU-free"` → **keep the module docstring's sanction block intact and within the first 4200 chars** (watch docstring growth above it).
3. `test_env_smoke_peft_check_is_gating` — regex `^def check_peft\(\):` must exist; the 900 chars from that def must contain `"FAIL"`, `"PASS"`, `"__version__"`; and `re.search(r"^(\s*)results\.append\(check_peft\(\)\)", src, re.MULTILINE)` must match at a position AFTER `def main():` → **main() must retain the literal line `    results.append(check_peft())`** (or equivalent indentation) inside `main()` — the structured refactor cannot rename this wiring away without editing the test, and D-02 forbids editing it.

**Recommended refactor shape (discretion, not locked):**

```python
@dataclass(frozen=True)
class CheckResult:
    name: str          # stable kernel id, e.g. "cuda"
    ok: bool
    lines: tuple[str, ...]   # the EXACT PASS/FAIL lines this kernel prints today

def check_cuda(torch) -> CheckResult: ...   # kernels build lines, don't print

def main() -> int:
    ...
    results: list[CheckResult] = []
    results.append(check_version_pins(pins))
    results.append(check_dnallm())
    results.append(check_peft())          # literal wiring line — grep-locked
    ...
    for r in results:
        for line in r.lines:
            print(line)                   # or kernels keep ownership of echo order
    ...
```

Design tension to resolve in-plan: kernels-print-and-return (lowest byte risk, but TUI imports then echo to stdout — Textual captures `print`, polluting the console) vs kernels-return-lines-and-main-renders (clean for TUI, byte risk moves into the renderer). The renderer approach is the D-02 intent ("TUI 服务层 import 内核"); a golden byte-stability test (tier-1, monkeypatched `import_module` + `capsys`) must pin it. Note the torch-import gate and the torch-unavailable double-`False` append: the renderer must reproduce the `FAIL: torch unavailable — CUDA + matmul checks not run` line in that position.

### Pattern 2: Thread-worker kernel execution (D-03)

**What:** the env-check screen kicks one `@work(thread=True)` worker; each kernel result travels back via a custom `Message` (thread-safe) that updates the panel row-by-row.

[VERIFIED: textual.textualize.io/guide/workers/] — `@work(exclusive=True, thread=True)` on a regular `def`; decorating a non-async function without `thread=True` raises; `exclusive=True` cancels previous workers of that method; **`post_message` is thread-safe** ("a good idea to send custom messages and let the message handler update the state of the UI"); `call_from_thread(fn, ...)` marshals a single call to the event loop; never set reactives or call widget methods directly from the thread; threads cannot be interrupted — poll `get_current_worker().is_cancelled` between kernel calls; workers are tied to their DOM node and cancelled when the widget/screen goes away.

Import paths: `from textual.work import work` (module `textual.work`), `from textual.worker import Worker, get_current_worker` [CITED: textual.textualize.io/api/worker/]; custom message base `from textual.message import Message` [CITED: textual.textualize.io/api/message/] — define messages nested in the posting widget for namespacing (`on_<widget_snake>_<message_snake>` handlers) [CITED: textual.textualize.io/guide/events/].

```python
# screens/env_check.py — sketch
from textual.work import work

class EnvCheckScreen(Screen):
    class CheckItemDone(Message):
        def __init__(self, result: CheckResult) -> None:
            self.result = result
            super().__init__()

    def on_mount(self) -> None:
        self.run_full_check()

    @work(exclusive=True, thread=True)
    def run_full_check(self) -> None:          # plain def — OS thread
        for kernel in self.env_check_service.kernels():
            res = kernel()                     # blocking; GPU kernels run only on GB10
            self.post_message(self.CheckItemDone(res))

    def on_env_check_screen_check_item_done(self, message: CheckItemDone) -> None:
        self.update_row(message.result)        # event-loop side: safe
```

CI note (D-03): tier-1 service tests inject fake kernels (plain functions returning `CheckResult`s) — the GPU-touching real kernels never execute in CI; on the CPU dev box, torch absent → kernels return honest FAIL results, which is correct behavior, not an error.

### Pattern 3: k9s-style selection — DataTable + app-state mark-set

[VERIFIED: textual.textualize.io/widgets/data_table/] — `add_row(*cells, height=1, key=None, label=None)`: supply the registry key as `key` for a stable `RowKey` that survives sorting; `cursor_type` reactive `"row"` gives `RowHighlighted`/`RowSelected` on keyboard movement; `cursor_coordinate` + `coordinate_to_cell_key(...)` → the `row_key` under the cursor; `get_row(key)`/`get_cell(...)` read data back; `update_cell(row_key, column_key, value)` for in-place mark updates; `clear(columns=False)` for filter rebuilds; built-in `sort(columns..., key=fn, reverse=)`; `zebra_stripes = True`; `fixed_rows`/`fixed_columns` for pinned columns. **There is no built-in multi-select** — the mark-set is screen/app state:

```python
BINDINGS = [
    Binding("space", "toggle_mark", "标记"),
    Binding("m", "switch_list", "模型/数据集"),
    Binding("p", "apply_preset", "预设"),
]

def action_toggle_mark(self) -> None:
    row_key, _ = self.table.coordinate_to_cell_key(self.table.cursor_coordinate)
    name = str(row_key.value)                 # registry key — stable row_key (D-06)
    if name in self.marks:
        self.marks.discard(name)
    else:
        self.marks.add(name)
    self.table.update_cell(row_key, self.mark_col, "✓" if name in self.marks else "")
```

Type-to-filter = an `Input` widget above the table whose `Input.Changed` handler re-derives the visible rows (pure filter function in services) and rebuilds via `clear()` + `add_row(key=...)` — marks persist across rebuilds because they live in the set, not the table. Filter axes come straight from the registries [VERIFIED: registry probe this session — models: `species` ∈ {plants 19, human 12, '' 7, multi-species 5, human+mouse 5, fungi 4, microbiome 2, yeast/eukaryote/prokaryote/virus/athaliana/vertebrate/brassicalesacteriophage 1 each}, `type` ∈ {MLM 32, CLM 18, DL 5, '' 7}, `size (M)` range 7–1386; datasets: `Category` ∈ {Animals 20, Plants 15, Microbe 13, Multiple 2}, `type` ∈ {binary 37, multiclass 6, regression 6, multilabel 1}, `metric` ∈ {f1 37, mcc 6, spearmanr 3, r2 3, AUPRC 1}]. Note: model cards also carry duplicate-case twins (`Tokenizer` vs `tokenizer`, `Mean_token_length` vs `mean_token_len`) — pick one column source per field and stay consistent [VERIFIED: models_info.json keys list].

The read-only matrix auxiliary view is a third screen/pane rendering presence+selection density only — never editable (SEL-01 wording; REQUIREMENTS out-of-scope table bans the editable grid).

### Pattern 4: XDG persistence split (D-04/D-05)

```python
from platformdirs import user_config_dir, user_state_dir

STATE_FILE = Path(user_state_dir("dnallmmark")) / "env_check.json"   # → ~/.local/state/dnallmmark/env_check.json
CONFIG_DIR = Path(user_config_dir("dnallmmark"))                      # → ~/.config/dnallmmark
```

[VERIFIED: local execution against platformdirs 4.12.4 in the repo venv — `user_state_dir('dnallmmark')` = `/home/forrest/.local/state/dnallmmark`, `user_config_dir('dnallmmark')` = `/home/forrest/.config/dnallmmark`; signatures `(appname=None, appauthor=None, version=None, roaming=False, ensure_exists=False, ...)` per CITED: platformdirs.readthedocs.io/en/latest/api.html]

- **Cache semantics (D-05):** on startup read state file; if `checked_at` is the same calendar day → render immediately, do not re-run; a refresh action forces a full re-run; partial failures persist too (per-item status with FAIL detail). Quick-check (ENV-04) results are computed on demand and never persisted as the full result.
- **Atomic writes** (tmp + `os.replace`) — the settings/templates side follows the same discipline the milestone ARCHITECTURE prescribed.
- **Test injection:** env-var whole-dir overrides, following the verified Phase 7 precedent [VERIFIED: pipeline/registry_loader.py:75-81 — `override = os.environ.get("DNALLMMARK_CUSTOM_REGISTRY_DIR")` … `xdg = os.environ.get("XDG_CONFIG_HOME")` … `Path.home() / ".config" / "dnallmmark"`]. TUI-side variable names are planner discretion (see Open Questions).

### Pattern 5: presets derived, never hardcoded (D-06)

`sweep_priorities.json` shape [VERIFIED: pipeline/sweep_priorities.json:1-17, quoted]:

```json
[
    [
        {"model": "plant-dnamamba-6mer", "task": "PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation"},
        {"model": "PlantHelixSeek", "task": "PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation"}
    ],
    [
        "GENERanno-eukaryote-0.5b-base",
        "PlantCAD2-Small-l24-d0768",
        "Omni-DNA-700M"
    ]
]
```

Tier 1 = list of `{model, task}` pairs (E2E 对); tier 2 = list of model-name strings (arena representatives). The selection service reads this file and derives preset mark-sets **as registry keys**: tier-1 marks the pair's models (tasks already pinned per pair), tier-2 marks the three models, "全部" marks every key from the overlay-merged registry (`registry_loader.load_models_registry()` — which already resolves official + custom overlay with collision fail-fast [VERIFIED: pipeline/registry_loader.py:136-172]), custom saved presets live under the XDG config root. **The tier-2 model names are data, not code** — validation should confirm every preset name exists in the merged registry and surface unknown names loudly (tolerant of registry evolution without silent selection loss).

### Pattern 6: strict template schema + tier interop (D-07)

Follow the verified `schemas/` precedent [VERIFIED: schemas/flops_report.json:1-30 — draft 2020-12, `$id` under `raw.githubusercontent.com/zhangtaolab/dnallmmark/main/schemas/`, `additionalProperties: false`, `schema_version: {"const": 1}`]. A `schemas/run_template.json` defines the full parameter set (models × tasks × seeds × PEFT (none/lora/ia3) × config-variant (head/probe/curve) × curve fractions × subset toggle × `effective_batch` (GA semantics: `GA = max(1, N // batch_size)`, maintainer default 16) × epochs override). Import validates with `jsonschema` (dev group) and **collects every problem in one fail-fast list** — the repo's established `_validate_filters` discipline. The `sweep_priorities.json` interop is a pure function pair (template ⇄ tier list). GA field semantics per maintainer's own words [CITED: 08-CONTEXT.md specifics — 先定 16，小模型起始 batch size 超过 16（如 64）时 GA=1，即 Phase 7 D-10 的 `GA = max(1, effective_batch // bs_new)` 乘积语义]. **One-way contract:** once templates are shareable, field names are frozen — treat the schema landing as a checkpoint-worthy moment in-plan.

### Pattern 7: two-tier tests + the 5-line import lock

- **Tier 1 (headless, CI-safe, no textual):** pure-function tests over services — env-gate judgments, cache day-comparison, preset derivation against a fixture `sweep_priorities.json`, template validation (synthetic invalid fixtures listing all problems), n_audit presence mapping, settings path overrides via env vars. Import path mirror: `tests/conftest.py` currently inserts `script/`, `baseline/`, `pipeline/` [VERIFIED: tests/conftest.py:41-44] — **it does NOT insert the repo root**, so `import tui` needs one added line (`sys.path.insert(0, str(REPO_ROOT))`) or a `tests/tui/conftest.py`.
- **Tier 2 (Pilot):** [VERIFIED: textual.textualize.io/guide/testing/] `async with app.run_test(size=(120, 40)) as pilot:` — headless driver is the default (CI-safe, no terminal); `await pilot.press("space", "enter")`; `await pilot.click("#id")` (topmost widget wins, like a real user); **`await pilot.pause()` waits for all pending messages — required before asserting message-driven state**; tests must be `async def`; pytest + pytest-asyncio with `asyncio_mode = "auto"` is the documented integration. Fake services are constructor-injected into screens/app; never let a Pilot test import torch or touch the real XDG home.
- **Services-textual-free lock:** a tier-1 test that walks `tui/services/*.py` (AST or `sys.modules` scan) and asserts none imports `textual` — the Phase 7 "absence = byte-identical + import-test lock" discipline, ~5 lines.

```python
# tests/tui/test_pilot_selection.py — tier 2 sketch
async def test_spacebar_marks_row(tmp_path):
    app = DnallmMarkTui(registries=FakeRegistries(three_models()))
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.press("space")
        await pilot.pause()
        assert app.screen.marks == {"<first-registry-key>"}
```

### Anti-Patterns to Avoid

- **Parsing env_smoke stdout from the TUI** — D-02 forbids it outright; import kernels, read structured returns.
- **Blocking the event loop with kernel calls in message handlers** — CUDA init takes seconds; always the thread worker (D-03).
- **Editing the env_smoke grep-locked strings/wiring** — the three tests above fail loudly; they are the contract's tripwire.
- **Business logic in screens** — untestable without textual; services own it (Anti-Pattern 6 of milestone research).
- **Re-implementing presence/tier/registry logic in `tui/`** — read `n_audit.json`, derive from `sweep_priorities.json`, load through `registry_loader` (TUI orchestrates, never computes — constraint 5).
- **Making a preset a widget concern** — presets are service-derived mark-sets; the screen only applies them to the set + table.
- **Persisting env state under `~/.config/`** — state and config split is the D-04 decision; check results are state (regenerable), presets/templates are config (user-authored).
- **Hardcoding tier-2 model names into Python** — they live in `sweep_priorities.json`; the service derives (D-06 zero-duplication).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| XDG path resolution (config vs state vs cache) | Custom env>XDG>home resolver in tui | `platformdirs` `user_config_dir`/`user_state_dir` | empirical parity verified; D-10 keeps the *pipeline-side* hand-rolled resolver untouched — the TUI side uses the library |
| Environment check logic | Fresh check implementations in `tui/services` | import the refactored `env_smoke` kernels (D-02) | single implementation; TUI and CLI can never disagree about pass/fail |
| Registry view (official + custom overlay) | Direct `json.load` of `models_info.json` | `pipeline/registry_loader.load_models_registry/load_datasets_registry` | collision fail-fast + overlay semantics already locked by Phase 7 tests |
| Tolerant JSON reads (n_audit, templates at rest, state file) | Bare `json.load` with ad-hoc try/except | `pipeline/artifact_loader.load_json_artifact` (returns `None` sentinel) | D-19 seam; parse-level tolerance contract already test-pinned |
| Preset membership | Hardcoded tier lists | Derive from `sweep_priorities.json` | file is the single source; tier edits need zero code changes |
| Async test plumbing | Custom event-loop fixtures | `pytest-asyncio` `asyncio_mode = "auto"` | documented Textual integration; one pyproject line |
| Template validation | Hand-written field checks | `jsonschema` + strict `schemas/run_template.json` | repo precedent; declarative contract Phase 11 consumes |

**Key insight:** every hard problem in this phase already has a repo-owned or library-owned solution; the phase's real work is *wiring and rendering*, plus one disciplined refactor.

## Runtime State Inventory

> Phase includes a refactor (env_smoke D-02) and introduces new persistent state, so the inventory is included.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | **None today** — env_smoke persists nothing (pure checks + exit code; verified full read). NEW state file `~/.local/state/dnallmmark/env_check.json` is greenfield (no migration) | none (create-on-first-check) |
| Live service config | None — no service consumes env_smoke output besides the maintainer reading stdout | none |
| OS-registered state | None — no tasks/units/pm2 reference env_smoke or a TUI | none |
| Secrets/env vars | Existing: `DNALLMMARK_CUSTOM_REGISTRY_DIR`, `XDG_CONFIG_HOME` [VERIFIED: pipeline/registry_loader.py:75-81]. NEW Phase 8 vars (TUI state/config injection) are additive; no existing var is renamed | none — additive only |
| Build artifacts / installed packages | `uv.lock` must be regenerated when `[tui]` + dev-group pytest-asyncio land (`uv lock` then `uv sync`); `.venv` gains textual (+ pytest-asyncio in dev syncs); `pipeline/__pycache__` unaffected | one lockfile commit alongside pyproject |

## Common Pitfalls

### Pitfall 1: DataTable "multi-select" assumption
**What goes wrong:** planner assumes `DataTable` supports multi-row selection; it does not — one cursor only.
**Why:** verified against official docs this session.
**How to avoid:** mark-set lives in screen state keyed on registry keys; spacebar binding toggles membership and updates a dedicated mark column via `update_cell`. Keep marks OUT of the table so filter rebuilds can't lose them.
**Warning signs:** tests asserting on table-internal selection APIs that don't exist.

### Pitfall 2: env_smoke byte drift during refactor
**What goes wrong:** renderer reorders lines (INFO line placement, torch-unavailable slot, per-package loop order in `check_version_pins` — it iterates `sorted(pins)`), drops the trailing-newline-per-print semantics, or moves a FAIL line after the trailer.
**Why:** output is assembled interleaved with computation today.
**How to avoid:** golden test capturing `main()` output under monkeypatched `import_module` (fake torch/dnallm/peft/numpy modules with controlled `__version__`s) comparing byte-for-byte against a recorded expectation, for at least: all-pass, torch-missing, dataset-missing-with-double-nested cases.
**Warning signs:** any test that only checks line *presence*, not order/bytes.

### Pitfall 3: breaking the source-grep contract tests
**What goes wrong:** refactor renames `check_peft`, moves the `results.append(check_peft())` line out of `main()`, grows the module docstring past 4200 chars before the sanction keywords, or drops a version label.
**Why:** three tests in `tests/test_run_finetune_contracts.py:1593-1657` grep the source text (verified above).
**How to avoid:** run those three tests first after every env_smoke edit; keep the docstring's sanction block near the top; keep kernel names and the peft wiring literal.
**Warning signs:** "I modernized the docstring" — that's the failure mode.

### Pitfall 4: `import tui` failing under pytest
**What goes wrong:** tier-1/tier-2 tests `import tui` → ModuleNotFoundError because `tests/conftest.py` inserts only `script/`, `baseline/`, `pipeline/` and plain pytest does not add cwd.
**Why:** verified conftest contents.
**How to avoid:** add one `sys.path.insert(0, str(REPO_ROOT))` line (root conftest or `tests/tui/conftest.py`); same insert belongs in `tui/__main__.py` for `pipeline/` modules (`import env_smoke`, `import registry_loader`, `import artifact_loader`) since `pipeline/` has no `__init__.py` [VERIFIED this session].
**Warning signs:** `python -m pytest` green locally (cwd luck) but CI red.

### Pitfall 5: forgetting ty/ruff/Makefile/CI coverage for `tui/`
**What goes wrong:** code passes tests but `make lint`/`make typecheck` skip `tui/` — or conversely lint lists files that don't exist yet in an early plan.
**Why:** coverage is configured in three places: `[tool.ty.src] include` + `[tool.ty.environment] extra-paths` (pyproject) and the Makefile lint file list (explicit paths + `PHASE*_MODULES` existence-guard idiom) [VERIFIED: Makefile:124-131, pyproject.toml:59-72].
**How to avoid:** add `"tui"` to both ty lists; extend the Makefile lint list with a `PHASE8_TUI := $(foreach s,tui/__init__.py tui/__main__.py tui/app.py ..., $(if $(wildcard $(s)),$(s)))` existence-guard (exact file list planner's choice); CI needs **zero workflow edits** — `make test` recipe gains `--group tui` (the D-01 ratification).
**Warning signs:** CI lint job green while `tui/` was never checked.

### Pitfall 6: blocking prints leaking from kernels into the TUI
**What goes wrong:** if kernels keep printing (print-and-return refactor style), the TUI's stdout gets PASS/FAIL spam; Textual captures `print` but the console output is polluted.
**Why:** kernels print inline today.
**How to avoid:** prefer return-lines-and-render-in-main (Pattern 1); if kernels must keep printing, gate the echo behind a parameter the TUI sets False.
**Warning signs:** kernel signature unchanged after "refactor".

### Pitfall 7: pilot tests that race message-driven state
**What goes wrong:** asserting immediately after `pilot.press("space")` reads stale state.
**Why:** messages "may take a moment to bubble" (official testing guide).
**How to avoid:** `await pilot.pause()` before assertions; inject deterministic fake services so no real sleeps are ever needed.
**Warning signs:** `time.sleep` or `asyncio.sleep` in tests.

### Pitfall 8: same-day cache semantics ambiguity
**What goes wrong:** "same day" compared in UTC while the operator reads a local-time date (or vice versa) — restart at 07:59/08:00 local re-runs or fails to; clock/timezone choice undocumented.
**Why:** D-05 specifies calendar-day comparison but not the timezone basis.
**How to avoid:** store `checked_at` as local naive `YYYY-MM-DD HH:MM` + an ISO-8601 UTC timestamp; compare calendar days in **local time** (the displayed date is the operator's contract); document in the service docstring. (Open Question 2.)
**Warning signs:** state file storing only a unix epoch with no display basis.

### Pitfall 9: textual major-version drift
**What goes wrong:** a future `uv lock --upgrade` crosses textual 9.x with breaking changes (strict SemVer; majors are frequent and tiny but real).
**Why:** documented cadence — 8 majors since Dec 2024 [CITED: .planning/research/STACK.md].
**How to avoid:** the `>=8.2,<9` pin is already the locked decision; upgrades are deliberate `uv lock --upgrade-package textual` + CHANGELOG scan events.
**Warning signs:** dependabot-style automation (none configured — keep it that way).

### Pitfall 10: `make tui` without the gpu group on GB10
**What goes wrong:** `uv run --group tui python -m tui` on GB10 shows CUDA/matmul FAIL because torch isn't in the tui lane — honest but confusing for the operator.
**Why:** torch lives only in `[gpu]` (`torch==2.11.0`, `transformers==5.17.0` [VERIFIED: pyproject.toml:33-36]).
**How to avoid:** `make tui` recipe: `$(UV) run --group tui --group gpu python -m tui` (STACK recommendation); the FAIL-if-absent path is still correct behavior for CPU boxes. Note `uv run` does an inexact sync, so manually-installed `dnallm` (local clone, absent from all groups by design) survives [CITED: CLAUDE.md runtime section + Phase 7 practice].
**Warning signs:** env panel showing FAIL on a machine the operator knows is healthy.

### Pitfall 11: screen bindings leaking into drill-down/modal views
**What goes wrong:** app-level bindings (space/mark, filter focus) firing while a detail modal is open, double-handling keys.
**Why:** with a plain `Screen`, app bindings are always checked (official screens guide).
**How to avoid:** use `ModalScreen` for env-check detail drill-down and any confirm surface — it blocks app-level bindings while on top [VERIFIED: textual.textualize.io/guide/screens/].
**Warning signs:** space marking a row while reading a check's detail pane.

## Code Examples

### env_check.json state shape (D-04/D-05 — recommendation, planner-refinable)

```jsonc
// ~/.local/state/dnallmmark/env_check.json — atomic write (tmp + os.replace)
{
  "schema_version": 1,
  "checked_at": "2026-10-11 16:20",       // local naive — the displayed 上次检查 value
  "checked_at_iso": "2026-10-11T08:20:00+00:00",
  "items": [
    {"name": "version_pins", "ok": true,  "lines": ["PASS: torch 2.11.0 == pyproject [gpu] pin", "..."]},
    {"name": "cuda",         "ok": false, "lines": ["FAIL: torch.cuda.is_available() is False — no visible GPU"]}
  ]
}
```

Item `name` values mirror kernel ids (`version_pins`, `dnallm`, `peft`, `cuda`, `matmul`, `numpy`, `dataset_dirs` — the `main()` order verified above); `lines` carry the kernel's own detail text so drill-down shows exactly what the CLI would print.

### Env-gate pure judgment (D-09 — sketch)

```python
CRITICAL = {"version_pins", "dnallm", "peft", "numpy", "cuda", "matmul"}
ROUTING  = {"dataset_dirs"}            # missing data → data management (Phase 10 panel)

def gate_verdict(items: list[CheckResult]) -> GateVerdict:
    critical_failures = [r for r in items if not r.ok and r.name in CRITICAL]
    routing_failures  = [r for r in items if not r.ok and r.name in ROUTING]
    return GateVerdict(
        can_launch=not critical_failures,
        reasons=[line for r in critical_failures for line in r.lines],
        route_to_data=bool(routing_failures),
    )
```

### Presence column mapping (SEL-04 — data shape verified)

```python
audit = artifact_loader.load_json_artifact(REPO_ROOT / "dnallm-mark/data/n_audit.json") or {}
tasks = audit.get("tasks", {})     # task -> {"missing": bool, "splits": {train/dev/test: {"rows": int, ...}}, "unified_eval_n": int}
# row render: "✓ 743,095/109,717/106,227" (train/dev/test rows) or "✗ 缺失"
```

[VERIFIED: dnallm-mark/data/n_audit.json — top-level `{"tasks": …}` with 50 entries, 7 `missing: true` (all GUE); each split carries `rows`, `strict_survivors`, `n_tolerant_survivors`, `non_acgt_chars`, `rows_with_non_acgt`, `by_char`, `total_chars`; plus task-level `unified_eval_n`]

### pyproject + Makefile + CI wiring (verified current-state deltas)

```makefile
# Makefile additions (mirroring the PHASE7_MODULES existence-guard idiom at Makefile:124-129)
PHASE8_TUI := $(foreach s,$(wildcard tui/*.py tui/screens/*.py tui/services/*.py),$(s))
lint:
	$(UV) run --group dev ruff check ... $(PHASE7_MODULES) $(PHASE8_TUI)
test: check-node
	$(UV) run --group dev --group tui pytest        # D-01: textual rides the existing lane
	node --test tests/js/*.test.js
tui:
	$(UV) run --group tui --group gpu python -m tui
```

CI: **zero workflow edits** — the `test` job already runs `make test`; the group addition inside the recipe is the whole D-01 change. The `lint-typecheck` job picks up `tui/` through the ty config + lint list. The `drift` and `static-js` jobs are untouched.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SVG snapshot goldens as first TUI test line | Behavioral Pilot assertions; snapshots deferred to TEST-01 (Phase 12) | milestone decision | Phase 8 Pilot tests assert state, not pixels — no syrupy/jinja2 churn |
| `textual.run_test()` needing per-test `@pytest.mark.asyncio` | `asyncio_mode = "auto"` | pytest-asyncio current | one pyproject line; sync tests unaffected |
| hand-rolled XDG resolution (pipeline side, Phase 7) | platformdirs on the TUI side only (D-10) | Phase 8 | two resolvers coexist by design; consolidation permanently deferred |
| env checks = CLI-only, stdout bytes | structured returns + CLI rendering (D-02) | this phase | TUI and CLI share one kernel implementation |

**Deprecated/outdated to avoid:** any code written against a Textual filesystem-watcher API (none exists in 8.x — verified at milestone research; poll with timers instead, not needed for Phase 8's at-rest panel); `textual-dev`/`textual-serve` in committed groups (constraint 10).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `from textual.work import work` / `from textual.message import Message` are the correct import paths in 8.2.8 | Patterns 2 | trivial rename at implementation; API nav lists these modules [CITED, not executed] |
| A2 | ✓/✗ and Chinese glyphs render correctly over the operator's SSH/tmux (tmux 3.4 verified present; repo scripts already emit ✅ emoji) | Patterns 3 | garbled status marks on exotic terminals; mitigation is Textual's own rendering, no code risk |
| A3 | `asyncio_mode = "auto"` leaves the existing sync suite and `slow`/`ci` markers fully unaffected | Standard Stack | low — auto mode only touches `async def` tests; verify with one full `make test` run in Wave 0 |
| A4 | `uv run` (inexact sync default) preserves the manually-installed `dnallm` package on GB10 across `make tui` invocations | Pitfall 10 | env panel false-FAIL for the dnallm item; Phase 7 smoke practice supports this but it was not re-proven for `--group tui` this session |
| A5 | Unicode row-height: CJK strings in DataTable cells occupy 1 cell row (no double-height issues) | Patterns 3 | cosmetic only |
| A6 | The env-var override for TUI state/config test injection should be whole-directory, mirroring `DNALLMMARK_CUSTOM_REGISTRY_DIR` | Pattern 4 | low — naming is planner discretion; the whole-dir shape is the ratified precedent |

## Open Questions

1. **TUI env-var names for test injection (D-04 leaves naming to planner)**
   - What we know: Phase 7 precedent is one whole-dir override var (`DNALLMMARK_CUSTOM_REGISTRY_DIR`); D-04 splits state from config, so one var cannot cover both roots.
   - What's unclear: one var per root (`DNALLMMARK_TUI_STATE_DIR` + `DNALLMMARK_TUI_CONFIG_DIR`) vs a single app-home override.
   - Recommendation: two whole-dir vars mirroring the XDG split; tests point both at `tmp_path` subdirs; document in the settings service docstring.
2. **Timezone basis for the same-day cache comparison**
   - What we know: D-05 says calendar-day; the displayed string is the operator's local clock.
   - What's unclear: local vs UTC for the *comparison*.
   - Recommendation: compare in local time (display and comparison must agree); persist both local display string and ISO instant (Pitfall 8).
3. **CLI-parity surface for template/preset functions**
   - What we know: constraint 4 requires every TUI capability to exist as CLI capability, CI-exercised; env checking already has its CLI (`env_smoke.py` itself).
   - What's unclear: whether template validation/preset derivation need an operator-facing CLI command in Phase 8 or whether CI-exercised tier-1 tests + the JSON-file contract satisfy parity.
   - Recommendation: Phase 8 ships them as importable service functions exercised by tier-1 CI tests (parity = the capability is reachable without the TUI runtime); a thin `python -m tui --export-selection`-style CLI is a natural Phase 11 add-on when run-config materializes. Confirm with maintainer at plan review if in doubt.
4. **Pilot test lane marker**
   - What we know: D-01 ratified textual in the existing CI test lane, zero new jobs; `make test` gains `--group tui`.
   - What's unclear: whether tier-2 tests need a pytest marker (e.g. `pilot`) to allow local fast runs without textual installed.
   - Recommendation: no marker initially (suite is fast); add one only if Pilot runtime or a textual-less local lane becomes a real need.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (repo venv) | everything | ✓ | 3.13.16 | — |
| uv | group management, `make tui` | ✓ | 0.13.0 (aarch64) | — |
| textual | TUI runtime + tier-2 tests | ✗ (not yet installed — `[tui]` group lands this phase) | 8.2.8 on PyPI | none needed — install is a phase task |
| platformdirs | settings/env-state services | ✓ (transitive, 4.12.4 in venv) — declare in `[tui]` | 4.13.0 current | — |
| pytest-asyncio | tier-2 Pilot tests | ✗ (dev-group addition lands this phase) | 1.4.0 on PyPI | none needed |
| tmux | operator environment (success criterion 1) | ✓ | 3.4 | — |
| NVIDIA GB10 GPU | real CUDA/matmul kernels (D-03: real machine only) | ✓ (this host IS the GB10; `nvidia-smi` → NVIDIA GB10) | — | CI uses injected fakes — by design |
| node | `make test` JS lane (unchanged) | ✓ | v26.10.0 | — |
| GB10 CUDA stack (torch/dnallm in venv) | full env-check on real machine | ✓ (Phase 7 smoke proven on this host) | torch 2.11.0 / dnallm local clone | CPU boxes honestly show FAIL for cuda/matmul/dnallm |

**Missing dependencies with no fallback:** none — all gaps are phase deliverables (the `[tui]` group install itself).
**Missing dependencies with fallback:** none applicable.

## Security Domain

`security_enforcement: true`, ASVS level 1, block on high. This phase adds a local operator tool; no network surface, no auth, no secrets.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | local single-user TUI; no auth surface introduced |
| V3 Session Management | no | no sessions; XDG files are user-local (0600 default umask) |
| V4 Access Control | no | no privilege boundaries; writes confined to XDG user roots + repo read |
| V5 Input Validation | **yes** | template JSON import is untrusted file input → strict jsonschema validation (D-07) with collect-all failure listing; state file read via tolerant loader + schema_version guard |
| V6 Cryptography | no | no crypto |
| V12 File/Resource integrity (L1 spirit) | yes (light) | atomic writes (tmp + os.replace) for state/config; never write into `pipeline/` or repo registries from TUI flows |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious/corrupt template JSON (shared file, imported by operator) | Tampering | jsonschema strict validation before any use; unknown registry keys rejected loudly; no code execution from template content (pure data) |
| State-file tampering (`env_check.json` forged PASS) | Spoofing | low impact (advisory panel; the real launch gate re-runs `env_smoke` in Phase 11 — D-09 keeps quick-check computed fresh, never trusted from disk for gating) |
| Path traversal via env-var overrides / export paths | Elevation | paths are operator-local config, not attacker-facing; export writes only to operator-chosen paths via standard file dialogs/inputs; no shell strings anywhere (argv-list discipline already repo-wide) |
| Dependency confusion via new packages | Supply chain | `[tui]` sources stay on default PyPI (the cu130 explicit index is torch-only by config); legitimacy gate run; textual pin `<9` |

## Sources

### Primary (HIGH confidence)
- Repo inspection this session (full reads): `pipeline/env_smoke.py` (all 449 lines), `pipeline/registry_loader.py`, `pipeline/artifact_loader.py`, `pipeline/sweep_priorities.json`, `pyproject.toml`, `Makefile`, `tests/conftest.py`, `tests/test_run_finetune_contracts.py:1585-1680`, `schemas/flops_report.json` (head), `dnallm-mark/data/n_audit.json` + `pipeline/{models,datasets}_info.json` (programmatic shape probes), `.github/workflows/ci.yml`, `.planning/{ROADMAP,REQUIREMENTS,STATE,config}.md`, `08-CONTEXT.md`, `docs/TUI-REQUIREMENTS.md`
- PyPI JSON API (fetched 2026-10-11): textual 8.2.8, platformdirs 4.13.0, pytest-asyncio 1.4.0 (versions, upload dates, requires_python, requires_dist)
- Official Textual docs (fetched 2026-10-11): /widgets/data_table/, /guide/workers/, /guide/testing/, /guide/screens/, /guide/events/, /api/worker/, /api/message/
- Local execution: platformdirs 4.12.4 `user_state_dir`/`user_config_dir` path verification; environment probes (uv/node/python/tmux/nvidia-smi)

### Secondary (MEDIUM confidence)
- `.planning/research/SUMMARY.md`, `ARCHITECTURE.md`, `STACK.md` (milestone research, 2026-10-11, HIGH at source time — cited where I did not re-verify: rich-in-lock transitive claim, textual py.typed, #6668 tmux bug, major-cadence history)
- platformdirs API reference (readthedocs) — signatures; Linux path table page 404'd, paths verified empirically instead

### Tertiary (LOW confidence)
- None relied upon for plan-shaping claims

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified against PyPI today; platformdirs behavior executed locally; all config deltas read from the actual files
- Architecture: HIGH — every seam (env_smoke kernels, loaders, registries, Makefile/CI/ty wiring, test conftest) read in full this session; screen/service split carries the ratified CONTEXT decisions
- Pitfalls: HIGH for the repo-contract pitfalls (byte stability, grep tests, sys.path, config coverage — all verified); MEDIUM for Textual practice-level pitfalls (docs-verified API, unexecuted)

**Research date:** 2026-10-11
**Valid until:** 2026-11-10 (stack stable; textual has had no release since 2026-06-30 — re-check the registry if planning slips past the window)
