# Phase 12: Multi-GPU Orchestration & Console Hardening - Research

**Researched:** 2026-10-13
**Domain:** Multi-process sweep orchestration (CLI), static-artifact merge, offline web-mirror generation, Textual snapshot goldens, TUI focus hardening
**Confidence:** HIGH (every load-bearing claim live-probed against the working tree or a throwaway venv on this host)

## Summary

Phase 12 scales the validated single-GPU sweep loop out to N workers and ships the
milestone's release extras. The architecture is already N-capable at every seam the
phase touches: `run_sweep.py` accepts `--models <shard> --output-root <worker-root>`
verbatim (no code change needed per worker), `sweep_monitor`'s discovery list renders
any number of roots by design, and the marker-skip (`trainer_state.json`) resume
discipline is per-cell-dir. What is missing is (a) one CLI entry that partitions the
model registry into disjoint shards and launches N isolated `run_sweep.py` workers
with per-worker `CUDA_VISIBLE_DEVICES` and per-worker output roots, (b) a merge tool
that unions the per-worker artifact trees into one root the existing data chain
(`script/export_runs.py`) reads unchanged, (c) the offline `gen_progress.py`
generator that serializes the pure scanner's dataclasses into the frozen web data
contract, (d) the Textual SVG goldens corpus, and (e) the single sanctioned TUI fix
(the slot-4 modal focus trap).

Two decisions the dispatch asked research to DECIDE are decided here with live
evidence. **D-07:** a NEW entry `pipeline/run_sweep_shard.py` — extending
`run_sweep.py` with orchestration flags would widen the frozen argv surface that the
tier-1 suite and the TUI composer pin, for zero benefit; the orchestrator composes
ordinary `run_sweep.py` argv per worker. **D-09:** merge lives in the same new entry
as a `--merge` mode (one naming authority for the frozen worker-root pattern
`{root}-mgpu-w{i}`) and is a **copy + SHA256-verify of the data artifacts**
(`run_record.json`, `final_metrics.json`, `trainer_state.json`, `seed_result.json`,
`flops_report.json`) — NOT checkpoints/runs — plus a cell-union manifest merge with
`output_dir` rewritten to the merged root. **The snapshot plugin verdict
(UI-SPEC OQ3) is resolved AGAINST the plugin:** `pytest-textual-snapshot` 1.1.0
pins `syrupy==4.8.0`, which caps `pytest<9`, while the repo's committed dev floor is
`pytest>=9.1.1` — a resolver-level conflict (error pasted below), with no upstream
fix released. The zero-dep fallback (`export_screenshot()` + string-compare goldens)
is proven live: byte-deterministic SVG across app instances, red-on-drift, 3 tests in
0.44 s. The golden corpus, naming, and CI semantics are identical either way, exactly
as the UI-SPEC pre-designed.

The focus-trap fix seam (delta B) is now fully characterized: under textual 8.2.8 a
modal dismiss restores focus to the **pre-modal focused widget** (live-probed — the
trap is "focus was on a params Input before the modal opened", not "focus is lost"),
`ScreenResume` fires on modal pop only through the private `_on_screen_resume`
(not a stable public hook), and `Screen.action_dismiss` routes through
`self.dismiss()` — so ONE override of `dismiss()` in a shared modal base class in
`run_config.py` covers every escape-binding AND every explicit `dismiss()` call site.
The fix pattern (explicit `#cfg-picker` refocus) was probe-verified end-to-end:
digit nav fires with picker focus, is eaten by an Input.

**Primary recommendation:** Build `pipeline/run_sweep_shard.py` (launch + `--merge`
modes, LPT size-weighted static model sharding, Popen `start_new_session` per worker,
`{root}-mgpu-w{i}` naming), `script/gen_progress.py` over the pure scanner, the
fallback-goldens corpus in `tests/tui/test_snapshots.py`, the delta-B focus fix via a
shared `dismiss()` override, `docs/multi-gpu.md` (decision matrix + the other-machine
N=2 smoke procedure), and the web page per the frozen UI-SPEC — zero new runtime
dependencies, zero pyproject/uv.lock changes.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (D-01..D-12, verbatim from 12-CONTEXT.md)

- **D-01 (维护者裁定 A):** 每 worker 监控视图复用槽 5——worker=独立输出根,发现列表天然 N 行,Enter 附加即视图;TUI 零新编排屏;CLI 是唯一编排入口(MGPU-01/SC2)
- **D-02 (维护者裁定 A):** Web 镜像并入现有静态站:dnallm-mark/progress.html + js/progress.js + data/progress/sweep.json + script/gen_progress.py 生成器;零后端,静态托管约束不变(WEB-01/SC4)
- **D-03 (维护者裁定 A):** 快照金丝雀 6 屏各 1-2 张关键态(~8 张 SVG:env/selection×2/data_manager/run_config/monitor/wizard);维护者过目后提交;CI CPU 侧像素对比,漂移即红(TEST-01/SC5)
- **D-04 (维护者裁定 A):** DDP-vs-分片决策 → docs/multi-gpu.md(决策矩阵+适用场景+CLI 示例+机器分工注记)+ README 一行链接(MGPU-03/SC3)
- **D-05 (维护者 2026-10-13):** 机器分工:多 GPU 开发在本机、**验证在他机**——MGPU 冒烟写成他机执行程序文档(E2' 同模式);本机仅 fake-executor/干跑枚举不相交性/单卡 CUDA_VISIBLE_DEVICES 语义证明;CI 与 GB10 不假设 N>1 设备
- **D-06:** marker-skip(trainer_state)是唯一并发守卫(SC1 锁定;分片不相交性为静态保证,守卫为兜底)
- **D-07:** 分片 CLI 形态由研究定(pipeline/run_sweep_shard.py 新入口 vs run_sweep.py 子命令扩展);判据:argv 面最小化 + 与既有 --models 过滤语义协同
- **D-08:** 失败 worker 隔离重跑 = 该 worker 分片单独 --from-failures 重跑,不触碰健康 worker 的根(SC2)
- **D-09:** 产物合并 = 合并工具把 N worker 根并至单一根;model×task×seed 目录天然不相交,合并非移动而是链接/复制+校验(研究定形)
- **D-10:** TUI 字符串面近零(D-01 零新屏);Web 文案在 progress.html/js 内(遵循站点既有 i18n 惯例);分片 CLI 帮助文本遵循 run_sweep 既有英文惯例
- **D-11:** 快照稳定性:固定终端尺寸、冻结时钟/动态内容(固定夹具数据)、快照测试不依赖网络/GPU
- **D-12:** 相位 11 UAT 建议清单为加固候选池(焦点陷阱修复优先级最高);按"建议级"处置,非本相位硬门

### Deferred Ideas (OUT OF SCOPE)

- DDP 实装(torch-run 数据切分)→ 决策文档落地即交付,实装非本里程碑
- Web 镜像自动刷新(SSE/轮询)→ 静态约束下仅手动/CI 再生
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MGPU-01 | 按模型分片 × CUDA_VISIBLE_DEVICES 多 worker 静态编排(CLI 可调用的模式,非 TUI 专属) | Area 1 (D-07 new entry), Area 2 (LPT sharding), Area 3 (Popen semantics), Area 4 (disjointness proof + env passthrough verified) |
| MGPU-02 | 每 worker 监控视图 + 产物合并 + 失败 worker 隔离重跑 | Delta A (zero-code N-root rendering, verified), Area 5 (merge tool), Area 6 (per-root --from-failures, verified semantics) |
| MGPU-03 | DDP 与模型分片适用场景决策落地(单大模型加速 vs 多模型吞吐);硬依赖单卡验证通过 | Area 10 + D-04 doc skeleton; run_finetune's existing WORLD_SIZE/LOCAL_RANK scaffolding documented |
| WEB-01 | 只读 Web 进度镜像(静态产物,无后端) | Area 7 (gen_progress.py import chain verified), frozen data contract (UI-SPEC), scanner dataclasses quoted verbatim |
| TEST-01 | Textual 官方快照测试(SVG 金标准,维护者验证后提交) | Area 8 LIVE VERDICT: plugin resolver-blocked → fallback goldens proven deterministic (this is THE plan, per UI-SPEC OQ3 pre-design) |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Model sharding + N-worker orchestration | CLI / pipeline (`pipeline/run_sweep_shard.py`, NEW) | — | D-01: CLI is the ONLY orchestration entry; TUI composes single sweeps only. The orchestrator is stdlib-only + CPU-testable like `run_sweep.py` itself |
| GPU isolation per worker | Orchestrator env (`CUDA_VISIBLE_DEVICES={i}`) | torch runtime (native env consumer) | `run_finetune.py` never touches `CUDA_VISIBLE_DEVICES` (grep: zero hits repo-wide); torch honors it natively; env inherits through two subprocess hops (verified — Area 4) |
| Per-worker monitoring view | TUI slot 5 (EXISTING, zero code) | `[a]` attach persistence | D-01: worker = independent output root; `_render_discovered` renders `summary.root.name` for N roots by design (verified) |
| Artifact merge | CLI tool (`--merge` mode of the same entry) | — | Offline maintainer step; must make the merged root a valid `--input-root` for `export_runs.py` (verified walk layout) |
| Web progress mirror | Static site (`progress.html` + `js/progress.js`, NEW) | offline generator `script/gen_progress.py` | D-02: zero backend; page loads one static JSON |
| sweep.json generation | Offline generator (stdlib + scanner import) | `tui/services/sweep_monitor.py` (pure, textual-free) | The scanner is the single shape authority; generator serializes dataclasses verbatim (UI-SPEC frozen contract) |
| Snapshot goldens | Test tier (`tests/tui/test_snapshots.py`, NEW) | `App.export_screenshot()` (textual 8.2.8 built-in) | Fallback lane (plugin verdict); CPU-only, no network, frozen fixtures (D-11) |
| Focus-trap fix | TUI slot 4 (`tui/screens/run_config.py`) | — | Delta B: the ONE sanctioned production TUI change; dismiss-time refocus (Area 9) |
| DDP-vs-sharding decision | Docs (`docs/multi-gpu.md`, NEW) | README one-line link | D-04: documentation deliverable, no code |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pipeline/run_sweep.py` seams | working tree (post-11) | `enumerate_matrix` / `build_argv` / `--models` / `--from-failures` / `--dry-run` / RESUME_MARKER | The orchestrator REUSES these verbatim — it never re-implements enumeration (D-05 same-source discipline, the `run_config` service precedent) |
| `tui/services/sweep_monitor.py` | working tree (11-04) | three-state discovery, tolerant readers, cells/stats/ETA, `DEFAULT_OUTPUT_ROOTS` | gen_progress serializes ITS dataclasses; the TUI monitor screen is already N-root |
| textual | 8.2.8 (uv.lock, `>=8.2,<9`) | TUI runtime + `App.run_test` + `App.export_screenshot` (both import-verified) | Snapshot goldens use the BUILT-IN export; no plugin, no new dependency |
| vanilla ES-module site | working tree | `progress.html`/`js/progress.js`/`css/progress.css` per the frozen UI-SPEC | D-02 static-hosting constraint; zero CDN scripts on the new page |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `platformdirs` | 4.13.0 (`tui` group) | transitively required by `sweep_monitor` → `settings` import chain | any process importing the scanner (gen_progress included) — run under `--group tui` or an env carrying it |
| `hashlib` (stdlib) | — | SHA256 verify of merged copies | merge mode, always |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New `run_sweep_shard.py` entry | `run_sweep.py` flag extension | rejected (Area 1): widens the frozen argv surface pinned by tier-1 tests + TUI composer; regression risk to the single-sweep path for zero gain |
| Fallback string-compare goldens | `pytest-textual-snapshot` 1.1.0 | rejected (Area 8): resolver-level conflict with `pytest>=9.1.1` (syrupy==4.8.0 pins `pytest<9`); community `--no-deps` hacks violate the lockfile discipline |
| Copy + hash-verify merge | symlink farm | rejected (Area 5): symlinks break when worker roots are cleaned/moved and do not survive cross-host rsync; D-09 demands 校验 |
| LPT greedy bin-pack | round-robin on sorted names | round-robin is simpler but ignores the 8M→multi-B size spread (verified: all 62 models carry numeric `size (M)`); LPT is ~10 lines and strictly better makespan |

**Installation:** NONE. `uv sync` / existing groups unchanged. This phase lands ZERO
new dependencies — the plugin verdict removes the UI-SPEC's one candidate.

## Package Legitimacy Audit

> Required by protocol; this phase installs nothing, and the one audited candidate is REMOVED.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| pytest-textual-snapshot | PyPI | 1.1.0, 2025-01 (latest, verified via PyPI JSON API) | n/a | github.com/Textualize/pytest-textual-snapshot | OK (as a package) | **REMOVED from plan** — resolver conflict with repo's `pytest>=9.1.1` (evidence in Area 8) |

**Packages removed:** `pytest-textual-snapshot>=1.1,<2` (and transitives syrupy/jinja2 it would have dragged in) — removed by RESOLVER INCOMPATIBILITY, not by legitimacy doubt.
**Packages flagged as suspicious [SUS]:** none.
**Net pyproject/uv.lock change from this research's recommendations: ZERO** — better than the UI-SPEC's sanctioned one-line dev-group change, which is now unnecessary.

## Architecture Patterns

### System Architecture Diagram

```text
 OPERATOR (maintainer, CLI — D-01: the ONLY orchestration entry)
   │  python pipeline/run_sweep_shard.py --models A,B,C --tasks T1 --seeds 42,43 \
   │      --output-root ./finetuned --workers 2 [--gpus 0,1] [pass-through flags...]
   ▼
 run_sweep_shard.py  (NEW, stdlib-only, CPU-testable)
   │ 1. validate (collect-all): --workers/--gpus arity, registry names (reuses run_sweep validators)
   │ 2. shard = LPT partition of filtered BASE models over N workers by registry "size (M)"
   │    (disjoint by construction: each model → exactly one worker)
   │ 3. per worker i: root_i = {output-root}-mgpu-w{i}   ← FROZEN naming (fixture: finetuned-mgpu-w0)
   ▼                    ▼
 Popen(start_new_session=True, cwd=pipeline/, env={**os.environ,
   CUDA_VISIBLE_DEVICES="{gpu_i}", PYTHONUNBUFFERED:"1"}, stdout→tee sibling log)
   │                    │            (the sweep_launcher._spawn discipline, verbatim)
   ▼                    ▼
 run_sweep.py --models <shard_0> ... --output-root …-mgpu-w0     run_sweep.py --models <shard_1> ... --output-root …-mgpu-w1
   │ disjoint model sets ⇒ disjoint {root}/{model}/{task}/seed_N/ trees — NO shared file (Area 4)
   │ per-cell: run_finetune.py inherits env → torch sees only gpu_i
   ▼                    ▼
 …-mgpu-w0/sweep_manifest.json + sweep_failures.json             …-mgpu-w1/…   (root-level, per worker)
   │                    │
   ├── FAILURE (worker 1 died / cells failed): others continue (independent sessions);
   │   recovery = run_sweep.py --from-failures …-mgpu-w1/sweep_failures.json
   │                          --output-root …-mgpu-w1 --seeds 42,43   (Area 6: zero new code)
   ▼
 run_sweep_shard.py --merge (same entry, post-step)
   │ copy data artifacts per cell into {output-root} (merged), SHA256-verify each file,
   │ merge manifests (cells union, output_dir rewritten, matrix.models union)
   ▼
 {output-root}/  ← valid export_runs.py --input-root (verified walk: {root}/{model}/{task}/seed_{n}/run_record.json)
   │
   ├── script/gen_progress.py ROOT... --output dnallm-mark/data/progress/sweep.json
   │     (imports tui/services/sweep_monitor.py — textual-free by lock; serializes dataclasses verbatim)
   ▼
 dnallm-mark/progress.html + js/progress.js  (fetch-once static page, frozen UI-SPEC contract)

 TUI slot 5 (ZERO code): operator [a]-attaches …-mgpu-w0 / -w1 once → N discovered rows,
   Enter = per-worker view (delta A). Goldens: tests/tui/test_snapshots.py (8 SVGs, fallback lane)
```

### Recommended Project Structure (new/changed files — the complete list)

```
pipeline/run_sweep_shard.py     # NEW — orchestrator: launch + --merge modes (Areas 1-6)
docs/multi-gpu.md               # NEW — D-04 decision matrix + D-05 other-machine smoke procedure
script/gen_progress.py          # NEW — offline generator (Area 7)
dnallm-mark/progress.html       # NEW — page shell copies finetuning.html (frozen UI-SPEC)
dnallm-mark/js/progress.js      # NEW — ProgressPage controller
dnallm-mark/css/progress.css    # NEW — 5 state-glyph classes + stat-card grid (tokens only)
tui/screens/run_config.py       # EDIT — delta B focus fix ONLY (the single TUI production change)
tests/test_sweep_shard.py       # NEW — sharding/orchestration/merge units (tier-1)
tests/tui/test_snapshots.py     # NEW — 8 fallback goldens + __snapshots__/ SVGs
tests/tui/test_pilot_run_config.py  # EDIT — delta B Pilot tests (B1-B5)
tests/tui/test_gen_progress.py  # NEW — generator golden-JSON tests
dnallm-mark/js/config.js        # EDIT — NAV_LINKS += Progress (one line, UI-SPEC)
dnallm-mark/js/data.js          # EDIT — DataAPI.loadProgress() (UI-SPEC)
dnallm-mark/css/styles.css      # EDIT — @import progress.css (one line)
README.md                       # EDIT — one-line link to docs/multi-gpu.md (D-04)
Makefile                        # EDIT — snapshot-update maintainer target (fallback lane)
```

### Area 1 — D-07 CLI form: NEW entry `pipeline/run_sweep_shard.py` (RECOMMENDED, evidence-based)

**Criteria from D-07:** argv-surface minimization + coexistence with `--models` filter semantics.

**Evidence for a new entry:**

1. **The single-sweep argv surface is FROZEN and pinned.** `run_sweep.py` currently
   exposes 15 flags; the TUI's `run_config.compose_argv` pins the exact element order
   ("the element order is pinned by the tier-1 suite, here only" —
   `[VERIFIED: tui/services/run_config.py:973-1013]`), and the tier-1 suite pins argv
   shapes for every flag (`tests/test_sweep.py` argv-parity proofs). Adding
   `--workers/--gpus/--merge/--shard-*` to `run_sweep.py` widens that frozen surface
   and forces every pinned contract to re-prove itself — regression risk to the exact
   path Phase 11 validated, for zero capability gain.
2. **The orchestrator composes; it does not execute cells.** A worker IS an ordinary
   `run_sweep.py --models <shard> --output-root {root}-mgpu-w{i} ...` invocation —
   the existing `--models` filter is reused VERBATIM (the D-07 "coexistence" criterion
   satisfied by construction: shards are just `--models` values). Nothing inside
   `run_sweep.py` needs to know sharding exists.
3. **Testability parity.** A new stdlib-only module is CPU-testable exactly like
   `run_sweep.py` (fake spawner seam, dry-run manifests, fixture trees) and imports
   `enumerate_matrix`/validators from `run_sweep` as a sibling module — the same
   import mechanics `sweep_monitor` already uses
   (`import run_sweep  # top-level module (pipeline/ sys.path root)` —
   `[VERIFIED: tui/services/sweep_launcher.py:88]`).
4. **E2' trust boundary is unchanged.** The E2' typed-phrase gate is a TUI-composed-path
   structural feature (`sweep_launcher.launch_spec`); the CLI `run_sweep.py` has NO such
   gate today — the CLI is the maintainer trust surface. The orchestrator inherits that
   same boundary (documented in `docs/multi-gpu.md`; the D-05 smoke procedure uses tiny
   combos anyway). No new gating code.

**Frozen naming (decides UI-SPEC OQ2):** worker root = `{output-root}-mgpu-w{i}`
(sibling of the base root). `Path(...).name` renders `finetuned-mgpu-w0` — the frozen
golden fixture name verbatim. With sibling naming, worker roots are NOT under
`DEFAULT_OUTPUT_ROOTS` (quoted below), so TUI discovery is **attach-only** (UI-SPEC
OQ2 option (c)): the operator `[a]`-attaches each worker root once (persisted in
`monitor_roots.json`), zero TUI code — D-01-clean. The runbook documents this as step
1 of every multi-GPU session.

### Area 2 — Sharding strategy: static by-model LPT (greedy descending) bin-pack

- **Disjointness by construction:** the partition assigns each BASE model name to
  exactly one worker; worker argv filters enumerate only that worker's models. Alias
  lanes (`--peft`/`--config-variant`) derive aliases as `f(base)+suffix` inside
  `enumerate_matrix`, so disjoint bases ⇒ disjoint alias sets ⇒ disjoint cell dirs —
  the alias machinery needs zero awareness of sharding
  (`[VERIFIED: pipeline/run_sweep.py:521-528` — `cell_model(model)` closure`]`).
- **Load weight:** every model carries a numeric `size (M)` — live-probed:
  62/62 models numeric, range sampled `('CrossDNA_519M', 8.1)` …
  `[VERIFIED: pipeline/models_info.json via live json read 2026-10-13]`.
- **Algorithm:** LPT (longest-processing-time-first) — sort models by `size (M)`
  descending (tie-break: registry-name ascending), repeatedly assign the next model
  to the worker with the least accumulated size (tie-break: lowest worker index).
  Deterministic, ~10 lines, no dependency. Round-robin over sorted names is the
  fallback-simple option but ignores the verified 8.1M→multi-hundred-M(+) spread;
  LPT dominates it on makespan at equal complexity. **Recommend LPT.**
- **Empty-shard edge:** if `#models < #workers`, later workers get empty shards —
  refuse at validation (collect-all: "--workers N exceeds the M filtered models;
  reduce workers") rather than spawn no-op workers that still write empty manifests
  into fresh roots (WR-07's silently-surprising-matrix hazard, new shape).
- **Sweep cost proxy honesty:** `size (M)` ignores per-task cost (dataset sizes vary);
  the shard cost is cells × per-cell-time where per-cell-time ~ model size × dataset
  size. Since EVERY worker runs the SAME task set (the shard axis is models only),
  task variance averages out across workers; model size is the dominant differential.
  Tagged [ASSUMED] (A1) — good enough for a static strategy; the runbook documents
  `--models` as the manual override when the operator knows better.

### Area 3 — Worker orchestration semantics: Popen `start_new_session` per worker

**Recommendation:** copy the `sweep_launcher._spawn` discipline VERBATIM (it is the
house-tested launch seam):

```python
proc = seam(
    list(argv),
    start_new_session=True,                 # each worker = its own process group
    cwd=str(PIPELINE_DIR),                  # run_sweep's documented cwd contract
    env={**os.environ,
         "PYTHONUNBUFFERED": "1",
         "CUDA_VISIBLE_DEVICES": str(gpu_i)},
    stdout=tee_handle,                      # per-worker sibling log
    stderr=subprocess.STDOUT,
)
```

`[VERIFIED: tui/services/sweep_launcher.py:477-484]` — the launcher's actual call is
`env={**os.environ, "PYTHONUNBUFFERED": "1"}` with `start_new_session=True`,
`cwd=str(PIPELINE_DIR)`, `stdout=tee_handle, stderr=subprocess.STDOUT`; the
orchestrator adds only the `CUDA_VISIBLE_DEVICES` key.

- **Parallel, not sequential:** spawn all N, then poll/wait all N. Sequential exec
  would defeat the phase's purpose.
- **Detach semantics:** workers survive orchestrator death BY DESIGN (separate
  sessions; resume-safe via the trainer_state marker — the same rationale as the
  launcher's `detach`). Ctrl-C on the orchestrator does NOT kill workers; the
  runbook documents the per-worker kill recipe
  (`kill -TERM -$(ps -o pgid= -p <pid> | tr -d ' ')` — the killpg discipline; the
  TUI exit modal canNOT kill CLI-launched workers: its registry only holds handles
  the TUI itself spawned — verified: `SweepLauncher._live` is instance state).
- **Worker logs:** one tee file per worker as a SIBLING of the worker root
  (`{root}-mgpu-w{i}.log`), NOT inside it (a log file inside the root is ignored by
  the scanner — only dirs are walked — but a sibling keeps the artifact tree pure)
  and NOT under the XDG state dir (that is the TUI's persistence root, D-10; the CLI
  must stay stateless). Self-describing, survives root cleanup decisions.
- **Failure isolation (SC2):** a worker exiting nonzero does NOT touch siblings —
  independent sessions, disjoint roots. The orchestrator waits for ALL workers,
  then aggregates: exit 0 iff every worker exited 0; else exit 1 printing a
  per-worker verdict table (exit code + root + log path + failed-cell count from
  that worker's `sweep_failures.json`).
- **GPU assignment:** `--gpus "0,1"` optional (default `0..N-1`); validation is
  arity-only (`len(gpus) == workers`), collect-all. The orchestrator NEVER probes
  nvidia-smi (stdlib purity + machine-agnostic + CPU-testable; D-05 says CI/GB10
  must not assume N>1).

### Area 4 — Marker-skip as the only concurrency guard (D-06): the disjointness proof

**Claim:** two `run_sweep.py` processes over DISJOINT model sets with PER-WORKER
output roots can never write the same file.

**Proof by construction (all quotes verified this session):**

1. Every write target derives from `cell_dir_for`:
   `cell = Path(output_root) / model / task / f"seed_{seed}"`
   `[VERIFIED: pipeline/run_sweep.py:1027]` — the first path segment after the root
   is the (alias) model name.
2. Worker i writes ONLY under `root_i = {base}-mgpu-w{i}`; `root_i != root_j` for
   `i != j` ⇒ **zero shared paths at any depth** — stronger than model-level
   disjointness.
3. Even the hypothetical weaker guarantee (same root, disjoint models) would NOT be
   safe: the manifest and failures file are ROOT-level, last-writer-wins —
   `_write_json(output_root / MANIFEST_NAME, ...)` and
   `_write_json(output_root / FAILURES_NAME, failures)`
   `[VERIFIED: pipeline/run_sweep.py:1525,1532]`. **This is exactly why per-worker
   roots are REQUIRED, not merely nice** (Pitfall 1).
4. The marker-skip guard remains the resume/兜底 mechanism, per-cell-dir:
   `if (cell_dir / RESUME_MARKER).exists(): record["status"] = "skipped"`
   with `RESUME_MARKER = "trainer_state.json"`
   `[VERIFIED: pipeline/run_sweep.py:1432-1435, 279]`.

**Env passthrough verification (the CUDA isolation chain):**
`run_sweep.launch_subprocess` spawns the child WITHOUT an `env=` kwarg —
`return subprocess.run(build_argv(...), cwd=PIPELINE_DIR, check=True,)`
`[VERIFIED: pipeline/run_sweep.py:1181-1187]` — so `run_finetune.py` inherits the
worker's environment verbatim. `run_finetune.py` itself only ever SETS cache env vars
(`os.environ["HF_HOME"] = _cache_dir` etc., lines 24-31) and reads `WORLD_SIZE` /
`LOCAL_RANK` / `GPU_MEMORY_GB`; a repo-wide grep for `CUDA_VISIBLE` returns ZERO hits
`[VERIFIED: grep over pipeline/, tui/, tests/ 2026-10-13]`. torch consumes
`CUDA_VISIBLE_DEVICES` natively at CUDA init. Chain: orchestrator env → run_sweep
(inherits, no env kwarg) → run_finetune (inherits) → torch sees exactly one GPU.
**Single-GPU degenerate probe (D-05 "本机 CUDA_VISIBLE_DEVICES 语义证明"):** on this
GB10 host (`nvidia-smi`: exactly one GPU, index 0, "NVIDIA GB10" — verified), a
N=1 orchestrator run with `CUDA_VISIBLE_DEVICES=0` is the degenerate-but-valid
semantic proof; N=2 validation is the other machine's procedure (Area 10).

**Test shape (the disjointness proof as an automated test):**
`tests/test_sweep_shard.py` — for each worker i, run `run_sweep.py --dry-run
--models <shard_i> --tasks <T> --seeds 42 --output-root {tmp}/w{i}` (dry-run writes
ONLY the manifest — `[VERIFIED: pipeline/run_sweep.py:104-108 docstring + 1726-1763]`),
parse the N manifests, assert: (a) pairwise-disjoint `output_dir` sets, (b) the union
equals the unsharded enumeration's `output_dir` set, (c) each manifest's
`matrix.models` equals its shard. CPU-only, deterministic, no GPU.

### Area 5 — Merge tool (D-09): `--merge` mode in the same entry; data-artifact copy + SHA256

**Form:** merge lives in `pipeline/run_sweep_shard.py` as a mode flag
(`--merge --output-root ./finetuned --workers 2` reads the frozen-named worker
roots; no launch). One entry = ONE naming authority — the `{root}-mgpu-w{i}`
function is defined once and shared by launch and merge, so the two can never
disagree about where worker artifacts live (the same single-source argument as
D-05 same-source). A separate merge script would duplicate the naming.

**Copy vs symlink: COPY + verify.** Symlinks break when worker roots are cleaned
(the runbook's post-merge step) and do not survive cross-host rsync/tar uniformly.
D-09 demands 校验: SHA256 each source file, copy, re-hash the destination, compare —
cheap relative to training cost. `[VERIFIED: hashlib stdlib only]`.

**What to copy (scope):** the DATA-ARTIFACT allowlist per cell dir —
`run_record.json`, `final_metrics.json`, `trainer_state.json` (the resume marker /
`global_step` source), `seed_result.json`, `flops_report.json`, plus `frac_*/`
recursion for curve cells. NOT `checkpoint-*/` and NOT `runs/` (tensorboard):
verified consumers read only the JSONs — `export_runs.py` walks
`{root}/{model}/{task}/seed_{n}/run_record.json`
(`_SEED_DIR_PATTERN = re.compile(r"^seed_(\d+)$")` —
`[VERIFIED: script/export_runs.py:340, 500-562]`) and reads `trainer_state.json`
(`global_step`) + `seed_result.json` from the seed dir; `total_flos` arrives INSIDE
the record's metrics (the exporter hard-fails on a completed record missing it —
`:593`), NOT from a separate flops file walk; the scanner's `is_sweep_root` checks
manifest/failures/record/marker/metrics/`runs` dir but a merged root is classified
by its merged manifest first-match. Checkpoints are resume-state for workers only;
nobody re-runs the merged root. At E2' scale (9300 cells) full-checkpoint copy is
disk-insane; artifact copy is megabytes per cell. **Recommend artifact-only with an
explicit allowlist constant + a `--include-checkpoints` escape hatch** (tagged
[ASSUMED] A2 — maintainer may want checkpoints preserved; plan review confirms).

**Manifest merge semantics:** per-worker `sweep_manifest.json` cells UNION into the
merged manifest; each merged cell's `output_dir` REWRITTEN from the worker root to
the merged root path (consumers and the monitor read `output_dir` strings; leaving
worker paths would point at roots the runbook deletes); `matrix.models` = union;
`matrix.output_root` = merged root; `matrix.tasks`/`seeds` = union. Flags
(`peft`/`config_variant`/pass-throughs merged per-cell by `_manifest_payload`) must
be EQUAL across worker manifests — a mismatch is a DIAGNOSTIC (collect-all listing
the differing flags per root), never a silent pick-first: a merge of a lora worker
and a base worker is a different experiment than either
(the `rerun_lane` WR-01 discipline's cousin). Failures file: union of per-worker
failure entries with `output_dir` rewritten. After merge, the merged root
classifies `finished` with full counts in the monitor AND gen_progress (manifest
present → first-match classification — `[VERIFIED: sweep_monitor.py full_scan,
manifest branch]`).

**Verification that the merged root reads identically:** `export_runs.py
--input-root <merged>` produces the same per-model outputs as per-worker exports
unioned — the walk keys on registry model names × `seed_(\d+)` dirs, both
preserved verbatim by the copy. Test: build two tiny fixture worker trees, merge,
run the real `collect_records`-equivalent walk (or `export_runs` with stub
registries) over the merged root, assert the record set == the union.

### Area 6 — Failure isolation re-run (D-08): per-worker `--from-failures`, ZERO new code

Verified flag semantics: `--from-failures <path>` re-enumerates exactly the failed
(model, task) pairs, across all requested seeds —
`cells = [cell for cell in cells if (base_model_name(...), cell[1]) in failure_pairs]`
`[VERIFIED: pipeline/run_sweep.py:1720-1724]`. The isolation re-run is an ordinary
invocation over ONE worker's root:

```
python pipeline/run_sweep.py \
    --from-failures pipeline/finetuned-mgpu-w1/sweep_failures.json \
    --output-root pipeline/finetuned-mgpu-w1 \
    --seeds 42,43 [same lane flags as the original launch]
```

Healthy workers' roots are untouched by construction (different output roots; the
driver writes nothing outside `output_root` — verified: every `_write_json` call
targets `cell_dir` or `output_root`). Completed cells inside the re-run are skipped
by the seed-scoped marker (verified Area 4), so the re-run attempts exactly the
failed cells. `--models` is NOT needed (the failures file scopes the pairs) and NOT
recommended (it would re-introduce a typo surface the flag exists to remove — the
manifest's own `base_model` fields are the join source, MED-01). The lane
(`--peft`/`--config-variant`) must match the original sweep — the runbook says so,
and the TUI's `rerun_lane` WR-01 recovery logic documents the same hazard
`[VERIFIED: tui/services/sweep_monitor.py:1152-1207]`. **Recommendation: document
the command in `docs/multi-gpu.md`; no orchestrator flag.** (An optional
`--rerun-failures {i}` convenience is possible but adds argv surface for a command
that is already one line — against the D-07 criterion.)

### Area 7 — `script/gen_progress.py`: generator over the pure scanner

- **Import chain (re-verified with the run_sweep dependency):**
  `sweep_monitor` imports `artifact_loader` (pipeline/) + `run_sweep` (pipeline/) +
  `tui.services.run_config` + `tui.services.settings` (repo root)
  `[VERIFIED: tui/services/sweep_monitor.py:50-62]`. Both `run_config` and `settings`
  are services-tier (zero textual — locked by `tests/tui/test_import_lock.py`, an
  ast-walk over every `tui/services/*.py` `[VERIFIED: test head read]`); `settings`
  imports `platformdirs` (tui group). Therefore the generator runs under any env
  carrying the tui group (`uv run --group tui --group dev python script/gen_progress.py`
  — the `make test` lane's env). The script bootstraps BOTH sys.path roots itself
  (the tests/conftest.py contract, inlined): repo root + `pipeline/`.
- **CLI surface (frozen in UI-SPEC):**
  `python script/gen_progress.py [ROOT ...] --output dnallm-mark/data/progress/sweep.json`;
  no positional args → `DEFAULT_OUTPUT_ROOTS` — quoted verbatim:
  `DEFAULT_OUTPUT_ROOTS: tuple[Path, ...] = (REPO_ROOT / "pipeline" / "finetuned", REPO_ROOT / "finetuned")`
  `[VERIFIED: tui/services/sweep_monitor.py:78-81]`.
- **Emission:** per root — `full_scan` classification (state/done/total via the
  manifest branch) + `stats()` (elapsed/ETA/current) + `cells_view(root)` (CellRow
  list) — all existing pure functions; `state_counts` derived in the same pass
  (UI-SPEC auto-default 12). `newest_mtime` is DELIBERATELY DROPPED from the JSON
  (checker recommendation, ratified in the UI-SPEC) — the field exists on
  `SweepSummary` (`newest_mtime: float | None` — `[VERIFIED: sweep_monitor.py:151]`)
  but is a churn signal, not team-facing data. `generated_at` = generator clock,
  ISO-8601 UTC; `json.dump(..., indent=4, ensure_ascii=False)` per house style
  (UI-SPEC; note the house `_write_json` also uses `sort_keys=True` — recommend it
  for byte-stable regeneration, the export_runs determinism discipline).
- **Machine vocabularies (verbatim quotes, the frozen data contract's source):**
  sweep states `SWEEP_FINISHED = "finished"`, `SWEEP_RUNNING = "running"`,
  `SWEEP_ARTIFACTS_ONLY = "artifacts_only"`; cell states `CELL_COMPLETED =
  "completed"`, `CELL_FAILED = "failed"`, `CELL_SKIPPED = "skipped"`,
  `CELL_RUNNING = "running"`, `CELL_QUEUED = "queued"`; ETA modes `"pending"`,
  `"point"`, `"range"`, `"none"` `[VERIFIED: tui/services/sweep_monitor.py:111-138]`.
  Dataclass fields: `SweepSummary(root, state, done, total, newest_mtime)`;
  `CellSeed(seed, state, fraction_states)`; `CellRow(model, task, seeds)`;
  `CurrentCell(model, task, seed)`; `EtaEstimate(mode, point_seconds, lo_seconds,
  hi_seconds)`; `SweepStats(done, total, current, elapsed_seconds, eta)`
  `[VERIFIED: sweep_monitor.py:143-235]`.
- **Multi-root (recommendation: YES, pass-through N):** the multi-worker live view
  passes every worker root (`gen_progress.py finetuned-mgpu-w0 finetuned-mgpu-w1`);
  the post-run view passes the MERGED root only. **Never both** — the same cells
  would appear twice (two sweeps in the JSON, double-counted in the selector view).
  The runbook states this; the generator does NOT dedupe (a sweep entry IS a root —
  the honest mirror of the TUI's N-row discovery).
- **Per-root tolerance (UI-SPEC):** a root with no artifacts → `[Skip]` console line,
  absent from the JSON (never a half-entry) — the scanner's degrade-never-crash
  contract already returns empty scans for such roots.

### Area 8 — Snapshot plugin LIVE VERDICT (decides the goldens lane): FALLBACK IS THE PLAN

**The probe chain (all on this host, 2026-10-13):**

1. **Resolver conflict (decisive).** In a throwaway venv,
   `uv pip install textual==8.2.8 pytest>=9.1.1 pytest-textual-snapshot>=1.1,<2`
   FAILS at resolution:
   > `error: No solution found when resolving dependencies`
   > `cause: Because syrupy==4.8.0 depends on pytest>=7.0.0,<9.0.0 and pytest-textual-snapshot>=1.1.0 depends on syrupy==4.8.0, we can conclude that pytest-textual-snapshot>=1.1.0 depends on pytest>=7.0.0,<9.0.0. And because you require pytest>=9.1.1 ...`

   The repo's committed dev floor is `"pytest>=9.1.1"`
   `[VERIFIED: pyproject.toml [dependency-groups] dev]`. PyPI JSON API confirms the
   plugin's latest is 1.1.0 with `requires_dist:
   ['pytest>=8.0.0', 'rich>=12.0.0', 'textual>=0.28.0', 'syrupy==4.8.0',
   'jinja2>=3.0.0']` — the syrupy pin is EXACT. syrupy 6.1.1 (latest) allows
   `pytest>=8` unbounded, but the plugin pins `syrupy==4.8.0` precisely, so the
   escape hatch does not exist. Community state: no upstream fix released;
   projects work around via `--no-deps` installs or staying on plugin 1.0.0
   (sources below) — both violate this repo's lockfile discipline. **The sanctioned
   dev-group addition from the UI-SPEC is REMOVED; zero pyproject change lands.**
2. **Plugin behavior under textual 8.2.8 (completeness — throwaway venv, pytest 8.4.2):**
   the plugin itself WORKS there (`snap_compare` runs, `--snapshot-update` generates,
   second run passes — verified in /tmp). So the blocker is purely the pytest pin,
   and a future plugin release relaxing it would work under textual 8.2.8. Revisit
   trigger for the docs: a pytest-textual-snapshot release depending on syrupy >=6.
3. **Fallback PROVEN (this is THE plan).** Under the repo-equivalent stack
   (textual 8.2.8 + pytest 9.1.1 + pytest-asyncio 1.4.0, throwaway venv):
   - `App.run_test(size=(120,40))` + `app.export_screenshot()` SVG is
     **byte-identical across two independent app instances** (determinism test PASSED);
   - string-compare against a committed `.svg` golden PASSES;
   - a changed app FAILS the compare (red-on-drift is non-vacuous);
   - 3 tests in **0.44 s** — CI-cheap.
   The SVG embeds only content + a CDN font URL reference (compare is string-equality;
   no network, no rasterization, no cairosvg — matching the UI-SPEC's "像素对比 at
   SVG fidelity" honesty note).

**Golden corpus consequences:** identical to the UI-SPEC's 8-SVG table (6 screens ×
key states) — naming `tests/tui/test_snapshots.py` + `tests/tui/__snapshots__/`
(plugin-default layout kept for familiarity), one test per golden id,
regeneration via a `make snapshot-update` target (a maintainer action, documented in
the module docstring — replacing `pytest --snapshot-update`, which no longer exists
in the fallback lane). CI compares only. D-11 rules unchanged (120×40, frozen clock
via injected `now=`/fixtures, no network/GPU).

### Area 9 — Focus-trap fix seam (delta B, D-12 #1): dismiss-time refocus via ONE shared `dismiss()` override

**Complete dismiss-site inventory (slot-4 reachable modals):**

| Modal | Class @ | escape binding | explicit `dismiss()` sites |
|-------|---------|----------------|---------------------------|
| Preview `[p]` | `PreviewModal` run_config.py:580 | :585 | — (inherited action) |
| Gate problems | `ProblemsModal` run_config.py:605 | :611 | — |
| Env-block | `EnvBlockModal` run_config.py:631 | :636 | — |
| E2' typed phrase | `E2PhraseModal` run_config.py:662 | :674 | :717 (`on_input_submitted`), :726 (`action_confirm_phrase`) |
| Choice RadioSet | `ChoiceModal` run_config.py:730 | :735 | :762 (`on_radio_set_changed`) |
| Confirm gate | `ConfirmModal` **selection.py:1109** (imported at run_config.py:71) | :1118 | :1134 (`action_confirm`) |

Push sites in the run-config screen: 1475, 1503, 1546, 1558, 1583, 1614, 1621, 1668,
1677 `[VERIFIED: grep + read of tui/screens/run_config.py]` — 9 push sites, 6 modal
classes, **10 distinct dismiss paths** (6 escape bindings + 4 explicit calls).

**Live-probed mechanics (textual 8.2.8, correct screen-stack construction):**

1. **The trap's root cause:** on modal dismiss, Textual restores focus to the
   PRE-MODAL focused widget — probe: params Input focused → modal pushed → modal's
   input focused → ESC → **focus back on the params Input**; then digit `3` is
   TYPED into the Input (nav binding never fires) — the UAT deadlock reproduced
   exactly. The bug is not "focus is lost"; it is "focus returns to wherever it
   was", and the gate pipeline's async worker (modal pushed from a message handler,
   not synchronously from the keypress) makes "wherever it was" frequently a
   params Input.
2. **The fix works:** explicit `picker.focus()` (the :1389 pattern — quoted:
   `if event.input.id == "cfg-filter":` / `self.query_one("#cfg-picker",
   PickerList).focus()` `[VERIFIED: run_config.py:1388-1389]`) takes focus (probe:
   `SelectionList#cfg-picker` focused), and with picker focus the digit `3` fires
   the app-level nav binding — deadlock gone. `PickerList` is a `SelectionList`
   subclass `[VERIFIED: run_config.py:460]`; plain `SelectionList.focus()` verified
   to take focus in isolation.
3. **ONE code site covers everything:** `Screen.action_dismiss` is literally
   `await self._flush_next_callbacks(); self.dismiss(result)` —
   `[VERIFIED: inspect.getsource(Screen.action_dismiss), textual 8.2.8]` — so the
   escape bindings ALL route through `self.dismiss()`, as do the 4 explicit call
   sites. A shared base class in run_config.py overriding `dismiss()` to
   (a) call `super().dismiss(result)` and (b) refocus `#cfg-picker` on the screen
   below (`self.app.screen_stack[-2]` at dismiss time, via `call_after_refresh`)
   patches all 10 paths in ONE helper. `ConfirmModal` lives in selection.py and is
   shared with other screens — do NOT edit it; give run_config a one-line local
   subclass (`class _GateConfirmModal(ConfirmModal)` inheriting the shared override)
   for its 1621 push site. This satisfies UI-SPEC B4 ("one shared helper in
   run_config.py") with zero selection.py changes.
4. **The resume-hook alternative is NOT viable:** `ScreenResume` fires on modal pop
   only through the PRIVATE `_on_screen_resume` (the public `on_screen_resume`
   handler did not fire — probed), and it also fires on initial screen push, so it
   cannot cleanly distinguish modal-pop from nav-return. Dismiss-time is the shape.

**Pilot test recipe (B1-B5, from the UI-SPEC, seam-verified):** boot slot 4 with
marks over the existing fake services → `p` + `esc` → assert `app.focused` is the
`PickerList` (`#cfg-picker`); open a choice modal (`enter` on a ChoiceRow) + `esc`
→ assert; gate `[enter]` → confirm/`esc` → assert; E2' modal `esc` → assert; then
press `3` and assert the data-manager screen is active. Deterministic fakes, no
sleeps (the `test_pilot_run_config.py` discipline).

### Area 10 — Multi-GPU smoke procedure (D-05: documented, OTHER machine, never CI/GB10)

Mirrors 11-07's GB10 recipe shape (numbered human-check, maintainer-executed,
recorded in VERIFICATION/UAT). Draft for `docs/multi-gpu.md`:

```text
他机多 GPU 冒烟(maintainer-executed,N=2,有界:2 模型 × 1 任务 × 1 种子 × 1 epoch;非 CI):
 0. 前置:目标机已装 dnallm/torch/cuda(uv run --group tui --group gpu 可启动);数据集已就位
    (与 11 的 D-04 冒烟挑选同一最小组合:iDNA_ABF_datasets__5mC,2110/234/2344 行)。
 1. 干跑枚举不相交性(无 GPU):python pipeline/run_sweep_shard.py --dry-run --workers 2 \
      --models plant-dnabert-6mer,<second-smallest-local-model> --tasks iDNA_ABF_datasets__5mC \
      --seeds 42 --num_train_epochs 1 --output-root ./finetuned-smoke-mgpu
    → 检查两个 worker manifest:模型集不相交、并集 == 请求集、根为 finetuned-smoke-mgpu-w0/-w1。
 2. 启动:同一命令去掉 --dry-run → 2 个 run_sweep 进程,CUDA_VISIBLE_DEVICES=0/1,
    每个 worker 1 个模型;tee 日志 {root}-mgpu-w{0,1}.log。
 3. TUI 视图:make tui → 槽 5 [a] 附加两个 worker 根(各一次,持久化)→ 发现列表 2 行
    (finetuned-smoke-mgpu-w0/-w1),Enter 切换视图,进度/ETA 独立(D-01/SC2 操作面证明)。
 4. 隔离证明:等待或促使一个 worker 的 cell 失败(或直接观察两 worker 完成时间差)→
    确认另一 worker 不受影响继续;orchestrator 退出码聚合表列出两 worker verdict。
 5. 失败重跑(python pipeline/run_sweep.py --from-failures <w1>/sweep_failures.json
    --output-root <w1 根> --seeds 42 --num_train_epochs 1)→ 仅 w1 根被写,w0 根 mtime 不变
    (touch 前后比对)。marker-skip:已完成的 cell 显示 skipped,不重训。
 6. 合并:python pipeline/run_sweep_shard.py --merge --workers 2 \
      --output-root ./finetuned-smoke-mgpu → 数据工件复制 + SHA256 校验输出;合并 manifest
    cells = 两 worker 之和。
 7. 镜像:uv run --group tui --group dev python script/gen_progress.py \
      pipeline/finetuned-smoke-mgpu-w0 pipeline/finetuned-smoke-mgpu-w1 \
      --output dnallm-mark/data/progress/sweep.json → 本地静态服务查看 progress.html
    (2 sweeps 选择器出现);再用合并根单独再生一次(1 sweep)对比。
 8. 数据链冒烟:uv run --group data python script/export_runs.py --input-root
    finetuned-smoke-mgpu … → 合并根可导出(与 worker 分别导出的并集一致)。
 9. 清理:确认合并根校验通过后删除 worker 根与日志;记录全部输出到相位 VERIFICATION。
```

(Bounded: 2 models × 1 task × 1 seed × 1 epoch ≈ minutes, the 11-UAT prior of
~65 s/cell for the smallest pair on GB10-class hardware — same-magnitude estimate.)

### D-04 decision-doc skeleton (MGPU-03)

`docs/multi-gpu.md` carries: (1) the matrix — model sharding (this phase: multi-model
throughput, embarrassingly parallel cells, zero code coupling, works for every model
incl. custom entries, cost = per-model load imbalance) vs DDP/torch-run
(single-large-model acceleration: one cell's batch split across GPUs; the child
ALREADY carries the scaffolding — `num_gpus = int(os.environ.get("WORLD_SIZE", "1"))`
and `local_rank = int(os.environ.get("LOCAL_RANK", "0"))`
`[VERIFIED: pipeline/run_finetune.py:1357, 1542]` — but data-splitting launch
orchestration is deferred by 12-CONTEXT); (2) 适用场景: 62-model sweeps → sharding;
single-model frontier scaling → DDP (future); (3) CLI examples (launch / re-run /
merge / mirror); (4) 机器分工注记 (D-05 verbatim); (5) the Area-10 procedure.
Plus the README one-line link (D-04).

### Anti-Patterns to Avoid

- **Two workers sharing ONE output root** — cell dirs would be disjoint but the
  root-level `sweep_manifest.json`/`sweep_failures.json` collide last-writer-wins
  (Area 4 proof item 3). Never alias worker roots onto one root.
- **Adding orchestration flags to `run_sweep.py`** — frozen argv surface, tier-1
  pinned contracts, zero gain (Area 1).
- **Symlink merge** — breaks on worker-root cleanup and cross-host copies (Area 5).
- **`--no-deps` plugin install** — the community workaround; violates the committed
  lockfile discipline and would pin pytest 8 silently under the floor (Area 8).
- **Passing worker roots AND the merged root to gen_progress** — double-counted
  sweeps (Area 7).
- **Killing the orchestrator expecting workers to die** — separate sessions by
  design; use the per-worker killpg recipe (Area 3).
- **Re-implementing enumeration/ETA/scan logic in the orchestrator or generator** —
  import `run_sweep` / `sweep_monitor` (D-05 same-source; the run_config precedent).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Matrix enumeration / argv building | a shard-specific enumerator | `run_sweep.enumerate_matrix` + the existing `--models` filter | alias lanes, curve fractions, priority order all live there; a copy would drift (retrain-forever class of bug) |
| Sweep state discovery / cell states / ETA | JSON walking in gen_progress | `sweep_monitor.full_scan` / `cells_view` / `stats` | the frozen web contract is DEFINED as these dataclasses; tolerant readers + degrade semantics come free |
| Subprocess launch discipline | a bespoke Popen wrapper | copy `sweep_launcher._spawn` kwargs verbatim | session/groups/env/tee semantics are phase-10/11-tested; the only delta is one env key |
| Concurrency guard | locks/claim files/ports | marker-skip (`trainer_state.json`) | D-06 LOCKED: it is the only guard; disjointness is static |
| SVG diff machinery | pixel/raster comparison | string equality on `export_screenshot()` output | probe-proven deterministic; cairosvg is NOT sanctioned (UI-SPEC) |
| Manifest validation | merge-side re-validation | `run_sweep` validators via import | collect-all fail-fast discipline, same source |

**Key insight:** every hard problem in this phase (enumeration, alias naming, resume,
scan tolerance, ETA math, launch isolation) was already solved once in phases 2-11;
the phase's job is composition, not invention. The two genuinely new algorithms — LPT
bin-pack (10 lines) and artifact-copy-merge (shutil + hashlib) — are the only new logic.

## Common Pitfalls

### Pitfall 1: The root-level manifest collision
**What goes wrong:** two run_sweep processes pointed at the SAME root with disjoint
`--models` shards silently corrupt each other's `sweep_manifest.json` /
`sweep_failures.json` (both written at sweep END, last-writer-wins) even though no
cell dir overlaps. **Why:** the manifests are root-scoped, not model-scoped
(`[VERIFIED: run_sweep.py:1525-1532]`). **Avoid:** per-worker roots are a HARD
invariant (`{root}-mgpu-w{i}`); the orchestrator refuses a worker root equal to the
base root or to another worker's. **Warning signs:** a merged/finished root whose
manifest cell count ≠ the sum of worker manifests.

### Pitfall 2: Focus fix at the wrong layer
**What goes wrong:** fixing the trap by re-binding digits globally or adding a
screen-resume hook — either re-shadows the nav shell or never fires (probe: public
`on_screen_resume` does not fire on modal pop; `_on_screen_resume` is private and
fires on initial push too). **Avoid:** the one-site `dismiss()` override (Area 9.3);
Textual restores PRE-modal focus, so only dismiss-time intervention changes the
landing. **Warning signs:** Pilot test asserting `app.focused` id after `esc`.

### Pitfall 3: gen_progress import failure under plain `python`
**What goes wrong:** `ModuleNotFoundError: run_sweep` (or `tui`) when the script is
run without the test harness's sys.path inserts — the script needs BOTH the repo
root and `pipeline/` (the tests/conftest.py + tests/tui/conftest.py contract,
inlined). **Avoid:** the script inserts both roots itself before importing the
scanner (house precedent: conftest comments state the two-root requirement
`[VERIFIED: tests/conftest.py:33-44, tests/tui/conftest.py:19-24]`). Also needs
`platformdirs` present (tui group) — document `uv run --group tui --group dev`.

### Pitfall 4: The plugin's `--snapshot-update` muscle memory
**What goes wrong:** in the fallback lane `pytest --snapshot-update` does nothing
(no plugin) — a maintainer regenerating goldens hits a silent no-op and ships stale
SVGs that then fail CI confusingly. **Avoid:** a `make snapshot-update` target that
runs the regeneration script explicitly; module docstring documents it as the ONLY
regeneration path. **Warning signs:** CI red on goldens right after an intentional
UI change with no update path run.

### Pitfall 5: Merged manifest pointing at deleted roots
**What goes wrong:** merging cells with their worker-root `output_dir` strings
verbatim, then the runbook's cleanup deletes worker roots — every merged cell's
`output_dir` dangles. **Avoid:** rewrite `output_dir` to the merged root during
merge (Area 5). **Warning signs:** monitor/[t] drill-downs on the merged root
resolving to nonexistent paths.

### Pitfall 6: Unequal worker lane flags discovered at merge time
**What goes wrong:** merging a `--peft lora` worker with a base worker produces a
manifest whose per-cell flags lie about half its cells. **Avoid:** merge validates
flag equality across worker manifests, collect-all diagnostic, refuses (Area 5).
**Warning signs:** the diagnostic listing differing flags per root.

### Pitfall 7: E2' expectations projected onto the CLI
**What goes wrong:** assuming the orchestrator needs an E2' typed-phrase gate.
The gate is a TUI-composed-path structural feature; the CLI (run_sweep today, the
orchestrator tomorrow) is the maintainer trust surface with NO gate — by design
(`[VERIFIED: run_sweep.py has no gate; sweep_launcher.launch_spec owns it]`).
**Avoid:** document the boundary in `docs/multi-gpu.md`; do not add gate code.

### Pitfall 8: dry-run manifests left behind as "sweeps"
**What goes wrong:** a `--dry-run` at a worker root writes `sweep_manifest.json`
with `planned` cells — the scanner classifies that root `finished` with 0 done
(the accepted full_scan edge, `[VERIFIED: sweep_monitor.py docstring "Known edge"]`);
a later REAL launch at the same root shows finished-until-end. **Avoid:** smoke
step 1 (dry-run) uses the SAME roots as the real launch deliberately to prove the
known-edge behavior, or dry-run into throwaway roots; runbook notes the edge.

## Code Examples

### The delta-B fix shape (one shared site; mechanics probe-verified, exact code plan-owned)

```python
# Source: probe-verified mechanics (textual8.2.8 inspect + Pilot probes), house pattern run_config.py:1389
class _PickerReturnModal(ModalScreen):
    """Slot-4 modal base: dismiss returns focus to #cfg-picker (delta B, B1/B4)."""
    def dismiss(self, result=None):          # Screen.action_dismiss + all explicit
        awaitable = super().dismiss(result)  # sites route through HERE (verified)
        below = self.app.screen_stack[-2] if len(self.app.screen_stack) > 1 else None
        if below is not None:
            try:
                picker = below.query_one("#cfg-picker", PickerList)
                picker.call_after_refresh(picker.focus)
            except Exception:  # wrong screen below (never on slot 4) — plain pop
                pass
        return awaitable
# PreviewModal / ProblemsModal / EnvBlockModal / E2PhraseModal / ChoiceModal
#   re-parent onto _PickerReturnModal; ConfirmModal gets a local subclass
#   (_GateConfirmModal) for its run_config push site — zero selection.py edits.
```

### The fallback golden test shape (probe-proven, 0.44s/3 tests)

```python
# Source: live probe /tmp/p12snap/test_fallback_golden.py (textual 8.2.8 + pytest 9.1.1)
async def _export(app_factory):
    app = app_factory()
    async with app.run_test(size=(120, 40)) as pilot:   # D-11: ONE size, the design grid
        await pilot.pause()
        return app.export_screenshot()                  # SVG string, byte-deterministic

def test_monitor_running_golden():
    svg = asyncio.run(_export(lambda: _golden_app("monitor_running")))  # fixture-injected fakes
    golden = (SNAP_DIR / "monitor_running.svg").read_text(encoding="utf-8")
    assert svg == golden          # red on ANY rendered drift; no plugin, no syrupy
```

### Sharding disjointness test shape (dry-run manifests, CPU-only)

```python
# Source: run_sweep --dry-run contract [VERIFIED: run_sweep.py:1726-1763]
def test_shards_are_disjoint_and_complete(tmp_path):
    shards = lpt_shard(["m1", "m2", "m3"], workers=2, sizes={"m1": 400, "m2": 8.1, "m3": 86})
    all_dirs = set()
    for i, shard in enumerate(shards):
        root = tmp_path / f"finetuned-mgpu-w{i}"
        run_sweep.main()  # via argv: --dry-run --models <shard> --tasks T --seeds 42 --output-root root
        cells = json.loads((root / "sweep_manifest.json").read_text())["cells"]
        dirs = {c["output_dir"] for c in cells}
        assert not (dirs & all_dirs)          # pairwise disjoint
        all_dirs |= dirs
    assert all_dirs == expected_full_enumeration_dirs  # union == whole matrix
```

### gen_progress sys.path bootstrap (house contract, inlined)

```python
# Source: tests/conftest.py:33-44 + tests/tui/conftest.py:19-24 [VERIFIED]
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))            # tui (package-qualified)
sys.path.insert(0, str(REPO_ROOT / "pipeline"))  # run_sweep, artifact_loader (top-level)
from tui.services import sweep_monitor        # textual-free by the import lock
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pytest-textual-snapshot 1.1.0 as the sanctioned goldens lane (UI-SPEC) | hand-rolled export_screenshot + string-compare goldens | this research, 2026-10-13 | zero new deps; corpus/naming/CI semantics unchanged; `make snapshot-update` replaces `pytest --snapshot-update` |
| syrupy 4.8.0 (`pytest<9`) | syrupy 6.x (`pytest>=8`, unbounded) | syrupy 6.0 (2025) | unusable here: the plugin pins `syrupy==4.8.0` exactly; revisit when a plugin release takes syrupy >=6 |

**Deprecated/outdated:** `pytest-textual-snapshot` 1.1.0 — not outdated as a tool
(works under pytest 8, verified), but BLOCKED for this repo by its exact syrupy pin
against the committed `pytest>=9.1.1` floor.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `size (M)` is an adequate static load proxy for LPT sharding (every worker runs the same task set; model size dominates per-cell cost) | Area 2 | imbalanced workers (slower wall-clock); `--models` manual override documented; low severity |
| A2 | Merge scope = data artifacts only (checkpoint-*/runs/ excluded) with a `--include-checkpoints` escape hatch | Area 5 | if a downstream consumer needs checkpoints from the merged root it breaks — none found (export_runs/monitor/gen_progress verified JSON-only); plan review confirms |
| A3 | Worker tee logs as siblings (`{root}-mgpu-w{i}.log`), not under the XDG state dir | Area 3 | cosmetic/differing maintainer preference; one-line change |
| A4 | Orchestrator Ctrl-C leaves workers running (documented; no signal handler) | Area 3 | operators might expect cascade kill; runbook covers the killpg recipe |
| A5 | `--merge` in the same entry (vs separate script) satisfies D-09 "合并工具" | Area 5 | if the maintainer reads D-09 as a separate tool, split is mechanical (same module, two entry points) |
| A6 | Fallback-lane snapshot dir named `__snapshots__/` (plugin-default layout) without the plugin | Area 8 | pure naming; one constant |

## Open Questions

1. **Navbar label `Progress` vs `进度`** (UI-SPEC OQ1, still the maintainer's one-word call)
   - What we know: site is verifiably English-primary; D-10 says follow site convention.
   - Recommendation stands: `Progress`.
2. **Merge scope confirmation (A2)** — data-artifact-only vs full copy including checkpoints.
   - Recommendation: artifact-only + escape hatch; confirm at plan review.
3. **sweep.json size at E2' scale** (UI-SPEC OQ4)
   - Recommendation stands: (a) no cap; static hosting already serves comparable JSON.
4. **Should the orchestrator expose `--rerun-failures {i}`?**
   - Recommendation: NO (Area 6 — the manual command is one line; argv-surface criterion); confirm at plan review.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | everything | ✓ | 3.13.16 (repo .venv) | — |
| uv | dependency mgmt | ✓ | 0.13.0 (note: CLAUDE.md cites committed 0.12.23 baseline) | — |
| textual | TUI + goldens | ✓ | 8.2.8 (repo .venv, uv.lock) | — |
| platformdirs | scanner import chain | ✓ | 4.13.0 | — |
| pytest | test lanes | ✓ | 9.1.1 (repo dev group) | — |
| GPU (this host) | D-05 local semantics probe | ✓ exactly 1 | NVIDIA GB10, index 0 (nvidia-smi verified) | N=1 degenerate only; N=2 = other machine (Area 10) |
| pytest-textual-snapshot | goldens (candidate) | ✗ BLOCKED | resolver refuses with repo pytest floor | fallback goldens (proven) — THE plan |
| GPU N≥2 host | MGPU smoke | ✗ (other machine, D-05) | — | documented procedure (Area 10) |

**Missing dependencies with fallback:** pytest-textual-snapshot (resolver conflict —
fallback adopted as the plan, zero-dep); N≥2 GPUs locally (D-05 routing to the other
machine's documented procedure).

## Security Domain

ASVS level 1 (`security_enforcement: true`, `security_asvs_level: 1`, `security_block_on: "high"`).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | no auth surface (offline tools + static site) |
| V3 Session Management | no | none |
| V4 Access Control | no | maintainer-local CLI; no multi-user surface |
| V5 Input Validation | yes | argv LISTs never shell strings (T-03-10 inherited — orchestrator copies the discipline); registry-name validation via run_sweep validators; merge path inputs are operator-supplied roots validated fail-fast; gen_progress tolerates malformed JSON via the scanner's None-sentinel readers |
| V6 Cryptography | incidental | SHA256 (hashlib) for merge verification — integrity, not secrecy; never hand-rolled crypto |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Shell injection via registry/model names | Tampering | argv LISTs, `shell` never used (inherited T-03-10; `subprocess.run(list, check=True)` verified) |
| Untrusted JSON → innerHTML XSS on progress.html | Tampering | data originates from the repo's own registries/artifacts (same trust level as every existing page rendering registry keys); the site pattern is `innerHTML` template literals — keep the site convention; no untrusted user input enters sweep.json (generator reads local artifacts only) |
| Env leakage across workers | Tampering/EoP | per-worker env is an explicit `{**os.environ, ...}` copy with ONE added key (the launcher discipline); no secrets are threaded |
| Artifact corruption during merge | Tampering | copy + SHA256 source-vs-destination verify per file (Area 5) |
| Path traversal in merge/generator | Tampering | roots are operator CLI args resolved via `Path.resolve()`; outputs stay under explicit destinations; no archive extraction |

## Sources

### Primary (HIGH confidence — live probes this session)
- Repo working tree (branch autorun @ e01c0fb): `pipeline/run_sweep.py`, `pipeline/run_finetune.py` (env/DDP scaffolding lines), `tui/services/sweep_monitor.py`, `tui/services/sweep_launcher.py`, `tui/services/run_config.py` (service), `tui/screens/run_config.py`, `tui/screens/selection.py` (ConfirmModal), `tui/screens/monitor.py`, `pipeline/models_info.json` (62/62 numeric `size (M)`), `script/export_runs.py`, `pyproject.toml`, `tests/conftest.py`, `tests/tui/conftest.py`, `tests/tui/test_pilot_monitor.py` (`_three_state_scan` fixture), `tests/tui/test_import_lock.py`
- Live textual 8.2.8 probes (repo .venv): modal-dismiss focus restore; ScreenResume non-firing public handler; `Screen.action_dismiss` → `dismiss()` routing (inspect); SelectionList focus takeover; digit-nav vs Input-eating; full trap→fix→nav chain
- Throwaway-venv probes (/tmp/p12snap): plugin resolver failure (error pasted verbatim); plugin smoke under pytest 8.4.2 (works); fallback goldens determinism/pass/drift-detect under pytest 9.1.1
- PyPI JSON API: pytest-textual-snapshot 1.1.0 requires_dist; syrupy 6.1.1 pytest bound
- nvidia-smi: single GB10 GPU (this host's D-05 role)

### Secondary (MEDIUM confidence)
- Community confirmation of the syrupy/pytest-9 conflict and workaround patterns — [Codeberg hypergumbo dev-install](https://codeberg.org/iterabloom/hypergumbo/src/branch/dev/scripts/dev-install), [hypergumbo fix commit](https://codeberg.org/iterabloom/hypergumbo/commit/4bc80cc54ab078a55eac677fe14252a7141674f5#1), [syrupy-project/syrupy](https://github.com/syrupy-project/syrupy), [syrupy on PyPI](https://pypi.org/project/syrupy/6.0.0/#files#1), [Textualize/textual poetry.lock](https://github.com/Textualize/textual/blob/55d1eac0b8531908718fda842ed92dc023dd7cea/poetry.lock#L34)

### Tertiary (LOW confidence)
- none — no claim in this document rests on unverified training knowledge alone

## Metadata

**Confidence breakdown:**
- Orchestration architecture (Areas 1-6): HIGH — every seam quote read from the working tree this session; disjointness proven by construction; env chain verified end-to-end (no env kwarg → inheritance; zero CUDA_VISIBLE_DEVICES writes repo-wide)
- Snapshot goldens (Area 8): HIGH — resolver conflict reproduced with pasted error; fallback proven deterministic + red-on-drift under the repo stack
- Focus fix (Area 9): HIGH — trap root cause, fix efficacy, and the one-site routing all probe-verified on textual 8.2.8; exact code shape plan-owned (B4)
- Web mirror (Area 7 + UI-SPEC): HIGH — data contract frozen from quoted dataclasses; import chain re-verified including platformdirs dependency
- Smoke procedure (Area 10): MEDIUM — drafted on verified components; execution is the other machine's, outcomes recorded later
- Load balance quality (A1): MEDIUM — proxy rationale is sound but unvalidated by a real N=2 run (impossible locally per D-05)

**Research date:** 2026-10-13
**Valid until:** 2026-11-13 (stable internal codebase; revisit sooner only if a pytest-textual-snapshot release changes the syrupy pin — the Area 8 revisit trigger)
