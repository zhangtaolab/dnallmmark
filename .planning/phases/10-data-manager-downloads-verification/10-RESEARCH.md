# Phase 10: Data Manager (Downloads & Verification) - Research

**Researched:** 2026-10-12
**Domain:** ModelScope CLI download channel, persistent queue state machine, n_audit row-count reconciliation, Zenodo public-record probe (Textual TUI service layer)
**Confidence:** HIGH (all critical claims live-probed this session against modelscope 1.34.0 in the repo venv, the real ModelScope hub, the real Zenodo API, and the repo source)

## Summary

Phase 10 turns menu slot 3 into a real data-manager screen by composing three
subprocess channels under the established services-tier discipline: the
`modelscope` CLI (download), `script/audit_n_frequencies.py` (reconcile), and a
stdlib HTTP GET (Zenodo probe). The STATE.md blocker ("ModelScope CLI
flag/progress-parsing specifics are MEDIUM confidence") is now **resolved by live
probe**: modelscope 1.34.0 is installed in the repo venv, its console script is
`.venv/bin/modelscope`, the dataset invocation is
`modelscope download --dataset <ns/repo> --local_dir <dir> [--include "pat/*"]`,
completed files are skipped on re-run via a `.msc` index written into
`--local_dir`, interrupted partials byte-resume via HTTP Range headers, SIGTERM
yields exit 143 with partials retained, progress rides stderr as tqdm lines while
stdout carries two clean parseable markers (`Downloading Dataset to directory:
{dir}` and `Successfully Downloaded from dataset {repo}.`). `python -m
modelscope` does NOT work (no `__main__`), so the worker must invoke the console
script — and modelscope is deliberately in NO uv group (manually installed,
survives only via the Phase 8 `--inexact` sync discipline), so the TUI must probe
for the CLI, exactly as the approved UI-SPEC already assumes.

The biggest discovery is structural: **the 15 ModelScope dataset repos are
heterogeneous** (live-probed file trees). Only 38/50 registry keys map cleanly
onto "repo task-subdir → registry Dataset_path task component" (shape A);
5 keys sit in single-task repos with CSVs at the repo root (shape B — different
`--local_dir` target, still one-click); 3 keys (plant-multi-species-histone)
land under repo subtree names that differ from the registry dir name (shape C —
needs a post-landing rename); and 4 keys (Genomic_Benchmarks ×3 parquet-upstream
layout, open-chromatin full/mini layout) are **not one-click landable at all**
without preprocessing. Additionally, D-01's "download_url 为唯一权威" collides
with committed reality: only 18/50 `download_url` values point at ModelScope —
the other 32 keep their ModelScope mirror in the `download_url_alternates`
field (every entry has it; union = 50/50, matching PROJECT.md's zhangtaolab 9 /
lgq12697 34 / forrestzhang 7). Both findings need a maintainer ruling recorded
at plan review: which URL field(s) the channel reads, and what happens for the
7 shape-C/D keys (post-move vs disabled-with-explanation).

Third seam, resolved: **presence cannot flip from the committed n_audit.json
alone** — `tui/services/registries.py` reads the committed
`dnallm-mark/data/n_audit.json`, which still says `missing: true` for a freshly
downloaded dataset. The flip path is an in-memory overlay: the queue service
publishes reconcile-pass keys + measured rows, and the presence snapshot builder
merges committed-n_audit ⊕ queue-reconcile results (a pure function, tier-1
testable). The env-check `dataset_dirs` kernel is a disk scan
(`pipeline/env_smoke.py:390-413`), so it flips naturally once the dir exists.
The committed baseline itself is only refreshed by the `g` re-audit action,
which runs the audit script with its DEFAULT outputs (writes the 4 repo
artifacts, including git-tracked `n_audit.json`) — a maintainer
data-regeneration act that must stay explicit.

**Primary recommendation:** Build `tui/services/download_queue.py` (state
machine + argv composer + progress parser + reconcile driver + Zenodo probe,
zero textual, injectable seams) over `settings.state_dir()/atomic_write`
persistence, a single exclusive `@work(thread=True)` worker spawning
`Popen(LIST argv)` with `start_new_session` and `os.killpg` cancel, a
per-key→(repo, include-pattern, local_dir, optional rename) mapping table in
code (data about external repos), and a pure `presence_overlay` merge consumed
by the selection/env screens. Gate shape-C/D keys and the URL-field question
behind a plan-review maintainer checkpoint.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
Copied verbatim from `.planning/phases/10-data-manager-downloads-verification/10-CONTEXT.md` `<decisions>`:

- **D-01:** `modelscope` CLI 子进程通道(CLI parity;进度/失败输出可解析;凭据由 CLI 自取 `~/.modelscope`,TUI 零接触零存储零回显——SC5)
- **D-02:** 队列服务 + 每任务独立子进程;worker 线程(@work(thread=True))只管 spawn/收割/解析,绝不进程内下载(D-03 纪律延续)
- **D-03:** 队列屏逐项进度行(解析 CLI 进度输出);失败项 verbatim 日志下钻(env-check 同款模式)
- **D-04:** 串行队列(单任务执行,磁盘/带宽友好,对账有序)
- **D-05:** 队列状态入 XDG state dir(`~/.local/state/dnallmmark/download_queue.json`,与 env_check 状态同根——Phase 8 D-04 先例;`DNALLMMARK_TUI_STATE_DIR` 注入)
- **D-06:** 通道自身续传 + 任务级状态机;TUI 重启后 pending+failed 自动重排(downloading 视为中断转 pending)
- **D-07:** 落地但对账 mismatch:醒目报告、不自动删除(操作者决定;audit 重跑可刷新);"重新审计"动作刷新 n_audit 基线
- **D-08:** 队列条目 = 数据集键级(每缺失数据集一任务,对账同粒度)
- **D-09:** 落地后自动对账:audit 行数内核子进程(Phase 9 gauntlet 同款纪律:LIST argv、临时输出、制品判据);结果进队列行 + mismatch 横幅
- **D-10:** 已提交 `dnallm-mark/data/n_audit.json` 为基线;屏内"重新审计"动作刷新基线(audit 脚本子进程)
- **D-11:** 对账 pass → selection 屏 presence ✗→✓ + env-check 数据集目录项同步(重读 n_audit 服务;SC1 后半)
- **D-12:** Zenodo 整包入口:记录 19135551 公开探测(URL HEAD/GET 检查);**未公开时按钮禁用 + 说明文案**;公开后激活为整包下载(单任务入队)
- **D-13:** 菜单槽 3(数据管理)变实屏:顶部缺失数据集清单(n_audit missing 集,可入队)+ 队列表(任务/状态/进度/行数对账列)
- **D-14:** 入队入口:selection 屏 presence ✗ 行 `d` 键;env-check FAIL 数据项路由跳槽 3(ENV-03 路由本相位落地)
- **D-15:** 底部子菜单:`d` 入队 / `r` 重试 / `x` 取消 / `a` 全部缺失入队 / `enter` 详情(verbatim 日志);右段恒定 `?` `q`
- **D-16:** 09-UI-SPEC 继承演进(同 Phase 9 模式);ui-researcher 加载 `tui-design` skill

### Claude's Discretion (from CONTEXT.md)
- 队列文件 schema 具体形状(schema_version + 任务数组字段命名)
- CLI 进度输出的具体解析正则(以实测为准——研究阶段探针)
- 缺失清单与队列表的布局比例、列宽
- 公开探测的缓存时长与失败文案
- 取消语义细节(杀子进程 vs 等待落地后丢弃)
- audit 对账内核的复用形态(Phase 9 GauntletService 的 audit 腿 vs 直接子进程)

### Deferred Ideas (OUT OF SCOPE)
- N 并发下载(本相位串行)→ 按需后续
- 下载带宽限速/镜像选择 → 后续按需
- 模型权重下载(本相位仅数据集)→ Phase 11+ 若需要
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | 缺失数据集一键下载（ModelScope 通道，注册表 download_url 为唯一权威） | Live-probed CLI surface (§ModelScope CLI), repo-shape mapping table (§Repo Heterogeneity), URL-field discrepancy + checkpoint (Open Question Q1) |
| DATA-02 | 下载队列持久化 + 断点续传（崩溃/重启后续跑） | Channel-level resume proven live (.msc skip + Range partials); queue schema + restart semantics (§Queue Persistence) |
| DATA-03 | 下载落地后行数对账（n_audit 基准）；不一致醒目报告 | GauntletService.audit_reconciliation reuse shape (§Reconcile Kernel), verdict criteria verbatim, presence-overlay flip chain (§Presence Flip Chain) |
| DATA-04 | Zenodo 整包（record 19135551 公开后）作为备选整体入口 | Live API probe: GET /api/records/19135551 → 404 not-registered (§Zenodo Probe); probe-state machine maps to UI-SPEC |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Queue state machine + persistence | TUI service (`tui/services/download_queue.py`, new) | XDG state dir (settings) | Pure orchestration state, zero textual, tier-1 testable; settings already owns atomic writes [VERIFIED: tui/services/settings.py:44,90-107] |
| modelscope argv composition | TUI service | — | Orchestration, not benchmark semantics: repo/include/local_dir come from registry fields + a code-owned repo-shape table |
| Download execution | modelscope CLI subprocess | worker thread spawn/reap/parse | D-01/D-02: never in-process; CLI owns credentials (~/.modelscope), resume, integrity |
| Row-count measurement + verdict semantics | `script/audit_n_frequencies.py` subprocess | service parses artifacts only | Binding constraint 5 (TUI orchestrates, never computes); Phase 9 gauntlet precedent [VERIFIED: tui/services/gauntlet.py:296-455] |
| Presence status derivation | `tui/services/registries.presence_for` (pure) | queue reconcile overlay merge | Presence is already a pure function over audit tasks dict; the overlay is data composition, not recomputation [VERIFIED: tui/services/registries.py:208-261] |
| Env-check dataset presence | `pipeline/env_smoke.check_dataset_dirs` disk scan | — | Flips naturally when the dir lands; no new env work needed [VERIFIED: pipeline/env_smoke.py:390-413] |
| Zenodo public probe | TUI service (stdlib urllib) | — | One GET, no credentials, session-memory only (UI-SPEC auto-default #6) |
| Progress rendering / toasts / drill-down | screens (`tui/screens/data_manager.py`, selection/env amendments) | strings.py `DL_`/`QUEUE_` | Screens render, never compute; i18n single home |
| n_audit baseline refresh (`g`) | audit script subprocess with default outputs | — | D-10: the script's own write path; TUI never computes counts nor hand-writes the baseline |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| textual | 8.2.8 (uv.lock-pinned) | TUI framework | Phase 8-locked; UI-SPEC enumerates 42 widgets from the installed package |
| platformdirs | 4.13.0 | XDG state/config roots | Phase 8-locked; `settings.state_dir()` already wraps it |
| Python stdlib `subprocess` | 3.13 | Popen spawn, killpg cancel, non-blocking stderr read | The gauntlet/env-check discipline; no new deps |
| Python stdlib `urllib.request` | 3.13 | Zenodo probe | services-tier has no HTTP dep; requests belongs to modelscope only |
| **modelscope CLI** | **1.34.0, installed in repo venv, NOT in any uv group** | The download channel (external subprocess only) | D-01: never a Python dependency of the TUI; probe before use [VERIFIED: `.venv/bin/modelscope` exists; `importlib.metadata.version('modelscope')` → `1.34.0`; no `modelscope` hit in pyproject.toml/uv.lock] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest (+pytest-asyncio 1.4.0, asyncio_mode=auto) | existing | tier-1 service tests + tier-2 Pilot | All CPU lanes; real-subprocess tests follow test_services_gauntlet.py |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| modelscope CLI subprocess | SDK `snapshot_download` in-process | Rejected by D-01 (never-in-process discipline; credentials zero-touch; CLI parity) |
| os.killpg + start_new_session | psutil process-tree walk | psutil is a new dependency for one kill; stdlib suffices (modelscope uses threads, not child processes — single OS process) [VERIFIED: snapshot_download.py thread_executor; ps aux during live download showed one process] |
| Parsing stderr tqdm percent | Only stdout markers + indeterminate render | UI-SPEC auto-default #3 already makes indeterminate honest; parsing best-effort percent is additive, never load-bearing |

**Installation:** NONE. Phase 10 adds zero dependencies (UI-SPEC Registry Safety: "New dependency surface in Phase 10: none"). modelscope stays a manually-installed venv extra behind the `uv sync --inexact` discipline [VERIFIED: STATE.md Phase 08 decision "uv sync for the tui group must use --inexact"].

## Package Legitimacy Audit

No packages are installed by this phase. modelscope is invoked as an external
CLI and deliberately never joins a uv group; its absence is a probed error
state (UI-SPEC: `✗ modelscope CLI 不可用 — 请先安装 (pip install modelscope)`).

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| modelscope (CLI only, external) | PyPI (1.34.0 confirmed in venv) | mature | high | github.com/modelscope/modelscope | OK (not installed as a dependency) | External channel — probe, never import |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## ModelScope CLI — Live-Probed Facts (STATE.md blocker resolved)

All quotes below are verbatim captures from this session (2026-10-12, modelscope
1.34.0, repo venv Python 3.13, credentials from `~/.modelscope` auto-picked —
the CLI needed no `--token` flag for these public repos).

### Invocation shape

```
modelscope download --dataset <namespace/repo> --local_dir <dir> [--include "<glob>/*"] [--exclude ...] [--revision R] [--max-workers N]
```

[VERIFIED: `.venv/bin/modelscope download --help` — flags captured verbatim:
`--model MODEL | --dataset DATASET`, `--repo-type {model,dataset}`,
`--token TOKEN`, `--revision REVISION`, `--cache_dir CACHE_DIR`,
`--local_dir LOCAL_DIR`, `--include [INCLUDE ...]`, `--exclude [EXCLUDE ...]`,
`--max-workers MAX_WORKERS`, positional `repo_id` + `files`]

- **`python -m modelscope` DOES NOT WORK** [VERIFIED: live probe —
  `/home/forrest/Github/dnallmmark/.venv/bin/python -m modelscope download ...`
  → `No module named modelscope.__main__; 'modelscope' is a package and cannot be directly executed`].
  The worker must invoke the console script. Resolution order:
  `Path(sys.executable).parent / "modelscope"` (the venv layout this console
  runs under), fallback `shutil.which("modelscope")`; absence → the probed
  unavailable state.
- `--local_dir` makes `--cache_dir` inert: files land at
  `local_dir/<repo-relative-path>` [VERIFIED: modelscope/hub/utils/caching.py:346-348 —
  `cache_full_path = os.path.join(self.cache_root_location, cache_key['Path'])`
  with cache root = local_dir in local_dir mode; and live probe: repo `lgq12697/GUE`
  file `emp_H3/train.csv` landed at `<local_dir>/emp_H3/train.csv`].
- `--include` patterns are `fnmatch` over the repo-relative `Path` and are the
  scoping mechanism [VERIFIED: modelscope/hub/snapshot_download.py:516-528].

### Output streams (the parse contract)

- **stdout** carries two clean markers, one line each:
  - Start: `Downloading Dataset to directory: {dir}`
  - Success: `Successfully Downloaded from dataset {repo_id}.`
  [VERIFIED: live probe stdout capture, verbatim]
- **stderr** carries: (1) a first-line noise warning
  `UserWarning: pkg_resources is deprecated as an API...` (plus
  `import pkg_resources` on line 2) — skip it; (2) tqdm progress with ANSI
  cursor-up escapes (`[A`) because files download in parallel
  (`--max-workers`, default 8):
  - File-level: `Processing 4 items:  25%|██▌       | 1.00/4.00 [00:00<00:01, 2.17it/s]`
  - Per-file bytes: `Downloading [emp_H3/dev.csv]:   0%|          | 0.00/737k [00:00<?, ?B/s]`
    … `Downloading [emp_H3/.DS_Store]: 100%|██████████| 6.00k/6.00k [00:00<00:00, 13.4kB/s]`
  [VERIFIED: live probe stderr capture, verbatim]
- Recommended best-effort percent regex (worker-owned, indeterminate fallback per
  UI-SPEC #3): match `Downloading \[([^\]]+)\]:\s+(\d+)%` for per-file percent
  and `Processing (\d+) items:\s+(\d+)%` for the file-count roll-up; strip ANSI
  (`\x1b\[[0-9;]*[A-Za-z]`) and split on `\r` first. The byte totals
  (`737k`) are tqdm-humanized — parse percent, not bytes. This regex is
  plan-owned discretion refined by this probe; recording it satisfies the
  CONTEXT discretion item.

### Exit codes, resume, cancel (live-probed)

- Success: exit `0` + the stdout success marker.
- **Resume on re-run**: a second identical invocation exits 0 with the success
  marker and ZERO `Downloading [` lines — complete files skip via the `.msc`
  pickle index written inside `--local_dir` [VERIFIED: live re-run probe +
  modelscope/hub/snapshot_download.py:550-556 `if cache.exists(repo_file): ... skip downloading`].
  So D-06 channel resume = the worker simply re-invokes the CLI.
- **Interrupted partials**: in-flight bytes live under
  `local_dir/._____temp/` (`TEMPORARY_FOLDER_NAME = '._____temp'`
  [VERIFIED: modelscope/hub/constants.py:40]); the parallel path resumes part
  files with HTTP Range headers [VERIFIED: modelscope/hub/file_download.py:415-447
  `if os.path.exists(part_file_name): # download partial, continue download`].
- **SIGTERM**: main process exits with shell code 143 (128+SIGTERM); completed
  files remain in place; partials remain under `._____temp` and resume on the
  next run [VERIFIED: live kill probe — partial tree retained
  `<dir>/<task>/dev.csv` for finished small files + `._____temp/<task>/` partials].
- modelscope downloads with threads (ThreadPoolExecutor), **one OS process** —
  `Popen.terminate()` reaches the whole channel. Spawn with
  `start_new_session=True` and cancel via `os.killpg(os.getpgid(pid), SIGTERM)`
  (stdlib; no psutil) so a future CLI version spawning children is covered.
  Live-probe lesson: killing a *wrapper* PID orphans the downloader (my test
  artifact left the real process running) — the TUI must own the Popen handle
  directly, never through a shell.

### Local-dir side effects (document, don't fight)

`--local_dir` receives `.msc` (pickle cache index) and `.mv` metadata files, and
`--include "<task>/*"` still admits junk like `.DS_Store` (probed: it landed).
Harmless: `check_dataset_dirs` tests only directory existence
[VERIFIED: pipeline/env_smoke.py:404-413], and the audit reads only
`train/dev/test.csv` per task. Optional hygiene: `--exclude "*.DS_Store"` /
`"*.gitattributes"`.

## Registry → Channel Mapping (live-probed repo census)

Every registry entry carries BOTH fields [VERIFIED: pipeline/datasets_info.json —
all 50 entries have non-empty `download_url` AND `download_url_alternates`]:

- `download_url`: primary provenance URL — 18/50 point at modelscope.cn, 17 at
  one shared Google Drive file (all GUE), 14 at huggingface.co, 1 at sid.erda.dk
- `download_url_alternates`: the ModelScope mirror for the other 32/50
  (e.g. GUE__EPI_GM12878: `"download_url_alternates": "https://www.modelscope.cn/datasets/lgq12697/GUE"`,
  primary `"download_url": "https://drive.google.com/file/d/1uOrwlf07qGQuruXqGXWMpPn8avBoW7T-/view"`)

Union coverage: **50/50 ModelScope-reachable**, exactly PROJECT.md's
"zhangtaolab 9 / lgq12697 34 / forrestzhang 7" key counts [VERIFIED: computed
over the committed registry + confirmed against `.planning/PROJECT.md:52`].
Repo id derivation: `urlparse(url).path.split('/datasets/')[-1].strip('/')`.

### Repo heterogeneity (HubApi file-tree census, all 15 repos)

| Shape | Repos (keys) | Mapping rule |
|-------|--------------|--------------|
| A — task subdir at repo root == registry task component | lgq12697/GUE (17), lgq12697/nucleotide_transformer_downstream_tasks (8), lgq12697/plant-genomic-benchmark (6), forrestzhang/Deep4mC_datasets (3), forrestzhang/iDNA_ABF_datasets (2), forrestzhang/iPro-WAEL_datasets (1), forrestzhang/BEND (1) — 38 keys | `--local_dir pipeline/datasets/<Group> --include "<task>/*"` where Group = `Dataset_path.split('/')[1]`, task = last component |
| B — CSVs at repo root | zhangtaolab/cross_species_leaf_absolute_translation, ...leaf_on_off_translation, ...core-promoters, ...lncRNAs, ...sequence-conservation (5 keys) | `--local_dir pipeline/datasets/<Group>/<task>` (whole repo; `--exclude` junk) |
| C — subtree name ≠ registry dir name | zhangtaolab/plant-multi-species-histone-modifications (3 keys: repo trees `H3K27ac`/`H3K27me3`/`H3K4me3`, registry wants `plant-multi-species-H3K27ac` dirs) | Needs post-landing rename `<Group>/<suffix>` → `<Group>/plant-multi-species-<suffix>` (queue post-landing step) |
| D — upstream mirror layout, NOT one-click | lgq12697/Genomic_Benchmarks (3 keys — parquet demo dirs, no registry-named subtrees), zhangtaolab/plant-multi-species-open-chromatin (1 key — `full_datasets`/`mini_datasets`) | No clean argv; render disabled-with-explanation (drill-down shows download_url) |

[VERIFIED: live HubApi `get_dataset_files` census over all 15 repos this
session; local expected layout cross-checked on disk — every group dir holds
`<task>/{train,dev,test}.csv` plus a group `.zip` (the Zenodo bundle unpack)]

**Design consequence:** argv composition cannot be derived from registry fields
alone. Ship a small code-owned mapping table (per-repo or per-key:
`{repo_id, shape}` with shape A/B/C/D rules above — 15 rows, or per-key for the
8 shape C/D exceptions). This is external-repo data, not user config; hardcoding
in the service (constants at module top, like gauntlet's
`_AUDIT_SPLIT_ORDER`) matches the codebase idiom. Shape-D keys: `d` on them
yields the disabled toast + drill-down explanation (the "always diagnosable"
goal — presence FAIL still tells the operator exactly why and where the URL is).

**Shared-repo note:** GUE's 17 keys share one repo. Key-granular tasks (D-08)
that sequentially invoke the same repo+local_dir are cheap — after the first
task, completed files skip via `.msc`. No dedupe machinery needed for
correctness; per-key `--include "<task>/*"` scopes each invocation. [VERIFIED:
re-run skip behavior]

## Architecture Patterns

### System Architecture Diagram

```text
 [selection screen ✗ row: d]   [data-manager missing list: d/a]   [env-check FAIL route → slot 3]
        │ enqueue(key)                  │                                  │ (nav digit 3, hint only)
        └───────────────┬───────────────┴──────────────────────────────────┘
                        ▼
          DownloadQueueService (tui/services/download_queue.py — zero textual)
          ├─ load(): XDG state download_queue.json (atomic_write; downloading→pending)
          ├─ enqueue/enqueue_all/retry/cancel → state transitions + persist
          ├─ single exclusive worker (@work(thread=True)) claims head pending
          │     ├─ compose argv: console-script path + --dataset <repo> --local_dir …
          │     │    (repo from download_url ⊕ download_url_alternates; shape table)
          │     ├─ Popen(LIST argv, start_new_session=True, stdout/stderr=PIPE)
          │     │    stderr → percent parser (best-effort; ⠋ … fallback)
          │     │    cancel: os.killpg(SIGTERM) → state=failed/cancelled-partials
          │     ├─ exit 0 → RECONCILE LEG (audit subprocess, gauntlet discipline):
          │     │    temp candidate-only registry {key: entry-with-ABSOLUTE-Dataset_path}
          │     │    → parse temp n_audit.json → verdict (declared==measured etc.)
          │     │    → pass: state=done (+measured rows) | fail: state=mismatch
          │     └─ shape-C post-landing rename before reconcile
          ├─ Zenodo probe (mount-time worker): GET /api/records/19135551
          │     200→public | 404→not public | else/timeout→probe failed (session memory)
          └─ publishes events (run-id tagged, WR-02) → data_manager screen rows
                        │
                        ▼ presence flip (D-11): pure overlay merge
   committed n_audit.json (registries.load_n_audit) ⊕ queue reconcile-done keys
                        │                                  │
                        ▼                                  ▼
        selection presence column ✗→✓          env-check dataset items (disk-scan
   (snapshot rebuild on the service event)      kernel flips naturally; same-day
                                                cache refresh on next visit)
   [g on mismatch row] → full audit subprocess (default outputs) → refreshed
                         committed n_audit baseline (maintainer data-regeneration)
```

### Recommended Project Structure

```text
tui/
├── services/
│   └── download_queue.py      # NEW: queue state machine, argv composer, progress
│                              # parser, reconcile driver (reuses gauntlet shape),
│                              # Zenodo probe, presence-overlay pure merge
├── screens/
│   ├── data_manager.py        # NEW: slot-3 screen (missing list + queue table +
│   │                          # banners + drill-down + z/g bindings)
│   ├── nav.py                 # EDIT: NAV_SLOTS slot 3 placeholder → real
│   ├── selection.py           # EDIT: datasets table `d` binding (missing rows)
│   └── env_check.py           # EDIT: ENV_ROUTE line gains [3] keycap hint
├── strings.py                 # EDIT: DL_* / QUEUE_* groups + ENV_ROUTE amendment
└── app.py                     # EDIT: screen registration/composition root
tests/tui/
├── test_services_download_queue.py   # tier-1: state machine, restart, parser
│                                     # fixtures, reconcile via real audit subprocess
└── test_pilot_data_manager.py        # tier-2: screen over fake queue service
```

### Pattern 1: Queue task lifecycle (D-02/D-06 state machine)

**What:** Five states `pending → downloading → (reconciling) → done | failed | mismatch`, persisted after every transition.
**When to use:** Every queue mutation.

```python
# Skeleton — field names are plan discretion; states are D-02 verbatim
QUEUE_STATES = ("pending", "downloading", "done", "failed", "mismatch")
SCHEMA_VERSION = 1
# entry: {"key", "state", "attempts", "enqueued_at", "started_at",
#         "finished_at", "last_percent", "raw_output_path",
#         "reconcile": {"baseline": {...Train,Dev,Test}, "measured": {...}, "verdict"}}
# NO credential fields ever (UI-SPEC interaction semantic #4)
# load(): entries persisted as "downloading" → "pending" (D-06 中断转 pending)
```

Persistence via the existing seam [VERIFIED: tui/services/settings.py:44
`STATE_DIR_ENV = "DNALLMMARK_TUI_STATE_DIR"`; settings.py:90-91 `def atomic_write(path, text): """Atomically write ... (tmp sibling + os.replace)`] — `download_queue.json` in the same state root as env_check state (D-05).

### Pattern 2: Reconcile leg = GauntletService.audit_reconciliation shape, official-key variant

**What:** Per-key reconcile reuses the Phase 9 audit-leg invocation verbatim: candidate-only temp registry, ABSOLUTE `Dataset_path`, all output flags temp, env pinned to an empty overlay.
**When to use:** after every landed download (D-09 automatic), and for `r` retry.

```python
argv = [sys.executable,
        str(repo_root / "script" / "audit_n_frequencies.py"),
        "--registry-dir", str(registry_dir),      # temp: {key: entry} only
        "--datasets-root", str(empty_temp),       # inert: absolute path replaces
        "--data-dir", str(audit_out),
        "--subsets-out", str(audit_out / "eval_subsets.json"),
        "--data-md", str(audit_out / "DATA.md")]
env[CUSTOM_DIR_ENV] = str(empty_overlay)
```

[VERIFIED: tui/services/gauntlet.py:348-356 — this exact argv/env shape; the
absolute-Dataset_path inertness rationale at gauntlet.py:335-343 ("Pitfall 3")]
Verdict = parsed `n_audit.json` `tasks.{key}` record: `missing` false, all three
splits rows > 0, `unified_eval_n` > 0, declared `Train`/`Dev`/`Test` ==
measured per split [VERIFIED: gauntlet.py:390-455 `_audit_verdict` pass
criteria quoted in its docstring: "``missing`` false; train/dev/test each
present with rows > 0; ``unified_eval_n`` > 0 ... declared ``Train``/``Dev``/
``Test`` ints equal the measured rows per split"]. For official keys the
declared side comes from the registry entry's `Train`/`Dev`/`Test` ints
[VERIFIED: present on entries, e.g. GUE__EPI_GM12878 `"Train": 10000, "Dev": 2000, "Test": 2000`].

**Reuse form (CONTEXT discretion):** direct subprocess inside the new queue
service (mirroring the gauntlet shape) is recommended over importing
GauntletService — the gauntlet's staging carries candidate/custom semantics
(enabled:true injection, existing-custom merge) that official-key reconcile
does not need; a thin re-implementation of the ~30-line staging + verdict
parse keeps both honest. Alternatively extract the audit leg into a shared
private helper both services import — planner's call.

### Pattern 3: Presence overlay (the D-11 flip chain — resolved seam)

`presence_for` is pure over an `audit_tasks` dict [VERIFIED:
tui/services/registries.py:208-261 — signature `def presence_for(task_key, audit_tasks)`],
and `load_n_audit()` reads only the committed file [VERIFIED: registries.py:77
`N_AUDIT_PATH = REPO_ROOT / "dnallm-mark" / "data" / "n_audit.json"`]. A fresh
download does NOT touch that file, so the flip needs one pure merge:

```python
def merge_presence(audit_tasks, reconcile_results):
    """reconcile_results: {key: (train, dev, test)} for done+pass entries.
    Returns a tasks-like dict view where reconciled keys read missing=False
    with measured splits — presence_for then works unchanged."""
```

The selection snapshot worker (which already builds
`presence = {key: presence_for(...)}` [VERIFIED: tui/screens/selection.py:380-391])
and the env-check dataset view consume the merged view. Env-check's kernel is a
disk existence scan and flips without any overlay the moment the dir lands
[VERIFIED: pipeline/env_smoke.py:404-413 — `expected.is_dir()` per Dataset_path].

### Pattern 4: Single exclusive worker, run-id tagged events

D-02/D-04: one `@work(thread=True)` worker loop (the 08-06 exclusive-worker
idiom: "kernel() exists exactly once in the screen, inside the exclusive
@work(thread=True) worker" [VERIFIED: STATE.md Phase 08 08-06 decision record]).
Worker = claim head `pending` → spawn → stream-parse → reap → reconcile →
persist → post per-item messages with run-id tags (WR-02 tag-and-drop;
GauntletItem.run_id is the precedent [VERIFIED: gauntlet.py:122-144]). No
double-spawn: `d`/`a` only mutate queue state + persist; the worker
self-advances (UI-SPEC semantic #2 "the queue advances itself, no manual start key").

### Anti-Patterns to Avoid

- **Importing modelscope from the service** — breaks D-01, the services-tier
  CPU-lane importability, and the CI story (modelscope is not in uv.lock).
- **Shell-string argv or wrapping the CLI in `bash -c`** — LIST argv only
  (binding constraint 5; my orphan probe is the cautionary tale).
- **Rewriting committed n_audit.json on reconcile-pass** — the baseline is
  git-tracked maintainer data; only the explicit `g` re-audit (script default
  outputs) refreshes it.
- **Fabricating a percent when stderr doesn't parse** — `⠋ …` indeterminate is
  contract (UI-SPEC #3).
- **Persisting probe state or credentials** — session-memory probe
  (auto-default #6); zero credential fields in the queue schema (SC5).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Resumable downloads | Byte-range resume logic | modelscope CLI's own (.msc skip + ._____temp Range resume) [VERIFIED live] | Proven this session; D-06 makes the channel own it |
| File integrity | Hash verification | modelscope's built-in digest check (file_download.py: `file_integrity_validation`) | Channel-owned |
| Row counting / filter semantics | Any CSV counting in the TUI | audit script subprocess | Binding constraint 5; kernels are the audit's alone [VERIFIED: gauntlet.py docstring "the kernels ... are the audit script's alone"] |
| Atomic JSON state writes | Locking schemes | `settings.atomic_write` | Existing seam [VERIFIED: settings.py:90-107] |
| Process-tree termination | psutil dependency | `start_new_session=True` + `os.killpg` | stdlib; single-process channel today, future-proof |
| Presence status mapping | New status vocabulary | `registries.presence_for` + overlay merge | The 08-04 four-status vocabulary is the contract |

**Key insight:** every piece of "download engineering" (resume, integrity,
progress, credentials, retries) already exists inside the CLI; the TUI's whole
job is argv composition, state bookkeeping, output parsing, and verdict
presentation — exactly the orchestrates-never-computes line.

## Common Pitfalls

### Pitfall 1: Killing the wrong PID orphans the downloader
**What goes wrong:** SIGTERM to a wrapper/parent leaves the python downloader running, still writing into the target dir.
**Why:** compound shells / double-spawn hide the real PID (observed live this session).
**How to avoid:** `Popen(argv, start_new_session=True)` directly from the worker; cancel = `os.killpg(os.getpgid(proc.pid), signal.SIGTERM)`; reap with `proc.wait(timeout)` then SIGKILL escalation.
**Warning signs:** queue says cancelled but disk keeps growing.

### Pitfall 2: stderr parsing assumes clean lines
**What goes wrong:** tqdm emits `\r` updates, ANSI `[A` escapes, and interleaved parallel lines; a naive `readline()` loop garbles.
**Why:** parallel max-workers render stacked bars on one stream.
**How to avoid:** read stderr as bytes (`stderr=PIPE`, non-blocking or a reader thread), split on `\r` AND `\n`, strip ANSI `\x1b\[[0-9;]*[A-Za-z]`, regex per-file percent; never block the worker on stdout (stdout is tiny — poll both or use `communicate` after a reader thread drains stderr).
**Warning signs:** percent jumping or stuck at 0 while bytes flow.

### Pitfall 3: Assuming one repo layout (the 50/50 trap)
**What goes wrong:** a uniform `--local_dir <group> --include "<task>/*"` silently lands nothing for shape B/C/D keys (0 filtered files still exits 0 with the success marker — the CLI reports success for an empty filtered set).
**Why:** repos are independent mirrors with three generations of layout (live census above).
**How to avoid:** the shape table + a post-landing existence check: after exit 0, verify `pipeline/datasets/<G>/<t>/{train,dev,test}.csv` all exist BEFORE reconcile; missing → failed with a verbatim diagnostic (this also catches empty-include).
**Warning signs:** done-with-zero-bytes tasks.

### Pitfall 4: n_audit baseline vs live presence drift confusion
**What goes wrong:** reconcile passes but selection still shows ✗ (committed file unchanged), or the committed baseline is silently rewritten.
**Why:** two sources of truth (committed baseline, live disk).
**How to avoid:** the overlay merge (Pattern 3) for the flip; the committed file changes ONLY via the explicit `g` re-audit; drill-down always states which source it shows.
**Warning signs:** presence disagrees with disk after a download.

### Pitfall 5: The pkg_resources warning pollutes failure logs
**What goes wrong:** every stderr capture starts with the deprecation UserWarning; naive "first error line" presentation shows noise.
**Why:** modelscope 1.34.0 still imports pkg_resources at CLI boot.
**How to avoid:** store verbatim (D-03) but skip the known first two stderr lines when scanning for real errors; the drill-down shows everything.
**Warning signs:** operators trained to ignore the top of logs.

### Pitfall 6: `g` re-audit writes four repo files, not one
**What goes wrong:** refreshing "the n_audit baseline" via the audit script's default outputs also rewrites `n_audit.csv`, `pipeline/eval_subsets.json`, and `DATA.md`.
**Why:** the script's four-artifact contract [VERIFIED: script/audit_n_frequencies.py module docstring artifacts 1-4].
**How to avoid:** ship `g` as the documented maintainer command semantics (defaults, verbatim — the same command ENV_ROUTE already prints: `python script/audit_n_frequencies.py` [VERIFIED: tui/strings.py:99-101]); the confirm copy should name that it refreshes the audit artifacts; leave the git diff to the maintainer. Alternative (temp outputs + atomic replace of n_audit.json only) desynchronizes the four artifacts — recommend against.

### Pitfall 7: Zenodo HEAD hangs
**What goes wrong:** probing `HEAD https://zenodo.org/records/19135551` times out (000 at 30s, live) while the API GET answers instantly.
**Why:** the records CDN doesn't answer HEAD from this network.
**How to avoid:** probe with `GET https://zenodo.org/api/records/19135551` (stdlib urllib, ~15s timeout): 200 → public; 404 → not public (live today: body `{"status": 404, "message": "The persistent identifier is not registered."}`); anything else/exception → probe-failed.

## Code Examples

### Zenodo probe (service-tier, stdlib, session-memory)

```python
# Source: live-probed behavior 2026-10-12 (see Pitfall 7); stdlib only
import json, urllib.request, urllib.error

ZENODO_API_URL = "https://zenodo.org/api/records/19135551"
PROBE_PUBLIC, PROBE_NOT_PUBLIC, PROBE_FAILED = "public", "not_public", "failed"

def probe_zenodo_public(timeout=15.0):
    """One GET; returns a probe-state string (pure data, screens render)."""
    try:
        with urllib.request.urlopen(ZENODO_API_URL, timeout=timeout) as resp:
            return PROBE_PUBLIC if resp.status == 200 else PROBE_FAILED
    except urllib.error.HTTPError as exc:
        return PROBE_NOT_PUBLIC if exc.code == 404 else PROBE_FAILED
    except Exception:                     # noqa: BLE001 — service boundary
        return PROBE_FAILED
```

### Progress parse (best-effort; UI-SPEC #3 fallback carries the contract)

```python
# Source: verbatim stderr capture analysis (ModelScope CLI section)
import re
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
FILE_PCT_RE = re.compile(r"Downloading \[([^\]]+)\]:\s+(\d+)%")
ITEMS_PCT_RE = re.compile(r"Processing (\d+) items:\s+(\d+)%")

def parse_progress(chunk: str):
    """Latest per-file percent + file-count percent from one stderr chunk."""
    clean = ANSI_RE.sub("", chunk.replace("\r", "\n"))
    files = FILE_PCT_RE.findall(clean)
    items = ITEMS_PCT_RE.findall(clean)
    return (dict(files) if files else {},
            int(items[-1][1]) if items else None)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Registry `download_url` treated as the sole channel authority (CONTEXT D-01 wording) | Live census: modelscope mirror lives in `download_url_alternates` for 32/50 | Probed 2026-10-12 | Channel must read primary-else-alternate (or maintainer re-points the registry) — Open Question Q1 |
| STATE.md: "ModelScope CLI flag/progress-parsing specifics are MEDIUM confidence" | Fully live-probed (flags, streams, exit codes, resume, cancel) | This research | Blocker closed; planning can proceed on VERIFIED facts |
| Phase 9 reconcile = custom candidates only | Official-key reconcile = same subprocess shape, declared side from registry Train/Dev/Test | This research | Pattern 2 |

**Deprecated/outdated:** `python -m modelscope` invocation path (no `__main__` — never worked); HEAD-based Zenodo probing (times out).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | modelscope repo layouts (shape table) remain stable through phase execution | Repo Heterogeneity | A repo restructure breaks landing; post-landing existence check (Pitfall 3) converts silent breakage into a failed row with diagnostics — low risk |
| A2 | `Path(sys.executable).parent / "modelscope"` is the right CLI resolution for the console's venv | CLI Facts | Fallback `shutil.which` covers PATH installs; worst case = unavailable-state on an unusual install (probed error state exists) |
| A3 | Per-file tqdm percent appears promptly enough on slow links to be worth parsing (vs `⠋ …` only) | Output streams | Cosmetic only — indeterminate fallback is the contract carrier |
| A4 | Zenodo 404 "not registered" remains the not-public signal until the record publishes (vs a later "restricted" 403 state) | Zenodo | A restricted-published record could 403; mapping treats it as probe-failed (disabled + explanation) — safe degradation, verify at activation time |
| A5 | The `g` re-audit runs the audit script with default outputs (writing the 4 repo artifacts) as the maintainer-blessed semantics | Pitfall 6 | If maintainer wants temp+replace instead, one task changes; recommend confirm at plan review (Q3) |

## Open Questions

1. **URL authority for the channel (D-01 wording vs committed data)**
   - What we know: `download_url` is modelscope for 18/50; the modelscope mirror is in `download_url_alternates` for the other 32; union = 50/50.
   - What's unclear: does "download_url 为唯一权威" mean (a) primary-if-modelscope-else-alternate (recommended — zero registry changes), or (b) the maintainer re-points `download_url` at modelscope for all 50 (a committed-data change, likely out of phase scope)?
   - Recommendation: implement (a); record the maintainer ruling at plan review. [checkpoint:human-verify]
2. **Shape-C rename + shape-D disabled set**
   - What we know: 3 histone keys need `H3K27ac` → `plant-multi-species-H3K27ac` rename; 4 keys (Genomic_Benchmarks ×3, open-chromatin) are not one-click.
   - What's unclear: maintainer preference — post-landing rename owned by the queue worker (recommended), vs registry-side fix, vs disabling all 7.
   - Recommendation: rename in-worker for shape C; disabled-with-explanation for shape D; the drill-down always shows download_url. [checkpoint:human-verify]
3. **`g` re-audit write semantics** — default-outputs (4 artifacts, recommended) vs temp+atomic-replace of n_audit.json only. See A5.
4. **Reconcile-leg reuse form** — direct subprocess in download_queue.py (recommended) vs shared extraction from GauntletService. Planner discretion (CONTEXT lists it).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| modelscope CLI | DATA-01/02 download channel | ✓ (repo venv) | 1.34.0 | Probed unavailable state (toast + disabled enqueue) — CI never has it, by design |
| `~/.modelscope` credentials | Private repos (public repos need none — live probes ran token-free) | ✓ | — | CLI-owned; TUI zero-touch |
| Network to modelscope.cn | downloads + repo census | ✓ (live probes) | — | Failed state + verbatim log; retry `r` |
| Network to zenodo.org (API GET) | DATA-04 probe | ✓ (API answers; HTML HEAD times out) | — | probe-failed state (disabled + 稍后重试) |
| Python 3.13 venv (uv, repo-local) | console runtime | ✓ | 3.13 | — |
| textual / platformdirs / jsonschema | existing TUI | ✓ | 8.2.8 / 4.13.0 / 4.26+ (uv.lock) | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none missing; modelscope absence is an expected, designed-for state on CI machines.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio 1.4.0 (asyncio_mode=auto), existing Makefile lanes |
| Config file | `pyproject.toml` / existing pytest config (none new) |
| Quick run command | `uv run --group tui --group dev pytest tests/tui -x -q` |
| Full suite command | `make test` (CI parity: `make ci`) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | argv composition per shape table; CLI-absent probe state | unit | `pytest tests/tui/test_services_download_queue.py -x -q` | ❌ Wave 0 |
| DATA-01 | progress parser over RECORDED stderr fixtures (clean, ANSI, interrupted, pkg_resources-noise) | unit | same file | ❌ Wave 0 |
| DATA-02 | state machine transitions + atomic persistence + restart (downloading→pending) | unit | same file | ❌ Wave 0 |
| DATA-02 | cancel: killpg path with a fake long-running subprocess (sleep script) | unit (real subprocess) | same file | ❌ Wave 0 |
| DATA-03 | reconcile verdict via REAL audit subprocess on fixture CSVs (the test_services_gauntlet.py precedent — CPU, sub-second) + declared-vs-measured mismatch paths | integration | same file (+ reuse gauntlet fixtures) | ❌ Wave 0 |
| DATA-03 | presence overlay merge flips presence_for result | unit | same file | ❌ Wave 0 |
| DATA-04 | Zenodo probe state machine with mocked urlopen (200/404/HTTPError-other/timeout) | unit | same file | ❌ Wave 0 |
| SC1/SC5 | screen renders queue rows/banner/drill-down over a fake queue service; selection `d` binding; env route hint | Pilot (tier-2) | `pytest tests/tui/test_pilot_data_manager.py -x -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run --group tui --group dev pytest tests/tui -x -q`
- **Per wave merge:** `make test` + `make lint typecheck` (ruff + ty gates, `--group tui` per Rule 3)
- **Phase gate:** full suite green + live-CLI manual smoke on the GB10 machine (documented, not CI)

### Wave 0 Gaps
- [ ] `tests/tui/test_services_download_queue.py` — queue/reconcile/probe (REQ-DATA-01..04)
- [ ] `tests/tui/test_pilot_data_manager.py` — screen + integration bindings
- [ ] Recorded stderr fixture files (from this research's verbatim captures — seed them in-repo)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (token handled entirely inside modelscope CLI against ~/.modelscope) | CLI-owned; TUI zero-touch (D-01/SC5) |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | Registry-derived argv values pass through LIST argv (no shell); URL fields parsed with urlparse, never interpolated into commands; probe URL is a module constant |
| V6 Cryptography | no | Channel-owned integrity (SHA-256 digest validation inside modelscope) |
| V12 File Handling | yes | Downloads land only under `pipeline/datasets/` paths derived from registry `Dataset_path` (validated components); temp staging via `tempfile.TemporaryDirectory`; atomic writes via settings seam |

### Known Threat Patterns for {stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious registry value injecting CLI args (e.g. a `--token`-shaped repo id) | Tampering/Elevation | LIST argv (values can never become flags via shell parsing), repo-id regex allowlist (`^[\w.-]+/[\w.-]+$`), URL parsed not executed |
| Untrusted dataset content | Tampering | Parse-only consumption downstream (audit T-05-07 discipline); TUI never evaluates content; reconcile counts rows only |
| Credential leakage into logs/state | Information Disclosure | Zero credential fields in queue schema; raw CLI output verbatim but the CLI itself never echoes tokens (live-verified output contains none) |
| Partial-file poisoning after cancel | Tampering | Channel-owned: `._____temp` partials never considered final; post-landing existence check + audit verdict gate presence |
| Zenodo probe SSRF-ish misuse | — | Probe URL is a frozen module constant (no user input reaches it) |

## Sources

### Primary (HIGH confidence)
- Live probes this session (venv modelscope 1.34.0): `--help` output verbatim; real download of `lgq12697/GUE` include-filtered into temp local_dir; re-run skip; SIGTERM cancel + partial retention; orphan-PID observation; `python -m modelscope` failure
- Live HubApi census of all 15 modelscope dataset repos (file trees) + committed `pipeline/datasets_info.json` field analysis (download_url × download_url_alternates × Dataset_path)
- Live Zenodo API GET (404 not-registered body) + HEAD timeout
- Repo source read this session: `tui/services/gauntlet.py` (full), `tui/services/registries.py` (full), `tui/services/settings.py` (grep-verified seams), `tui/screens/nav.py` / `env_check.py` / `selection.py` (integration points), `script/audit_n_frequencies.py` (docstring + argparse + main), `pipeline/env_smoke.py` `check_dataset_dirs`, `tui/strings.py` ENV_ROUTE line
- modelscope 1.34.0 source in venv: cli/download.py, hub/snapshot_download.py, hub/file_download.py, hub/utils/caching.py, hub/constants.py

### Secondary (MEDIUM confidence)
- `.planning/PROJECT.md:52` (ModelScope 50/50 coverage claim — cross-verified against the registry census)
- Phase 8/9 decision records in `.planning/STATE.md` (worker idiom, --inexact sync, XDG seams)

### Tertiary (LOW confidence)
- None — no training-data-only claims load-bearing in this research

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new deps; all existing seams read from source this session
- CLI/通道 facts: HIGH — every claim live-probed with verbatim captures (STATE.md MEDIUM blocker closed)
- Architecture: HIGH — three prior phases of service/screen patterns to compose; all integration points read from source
- Pitfalls: HIGH — observed live or read from source; A1/A4/A5 carry residual risk explicitly

**Research date:** 2026-10-12
**Valid until:** 2026-11-12 (stable repo; modelscope repo layouts are the one moving target — A1)
