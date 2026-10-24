# Stack Research

**Domain:** Multi-GPU benchmark orchestration + static leaderboard visualization (brownfield, v1.3)
**Researched:** 2026-10-20
**Confidence:** HIGH (repo-internal facts probe-verified across v1.2; external Chart.js facts web-verified 2026-10-20)

## Recommended Stack

### Core Technologies

**Verdict: ZERO new runtime dependencies.** Every v1.3 capability lands with what the repo already pins. This is a constraint-driven result, not an omission — see rationale per capability below.

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python stdlib (`subprocess`, `queue`/pipes, `json`, `pathlib`) | 3.11+/3.13 | Dynamic-dispatch orchestrator core | `run_sweep_shard.py` is already stdlib-only headless-importable (Phase 12 contract); a single-dispatcher process with an in-memory work queue + `Popen` workers needs nothing else. The repo's own download-queue driver (Phase 10) is the proven precedent |
| Chart.js (existing CDN pin) | 4.4.0 UMD | Error-bar rendering | Native floating bars (`[min, max]` data) cover the task bar chart with **zero code additions to the library surface**; scatter error bars via a vendored inline `afterDatasetsDraw` plugin (~40 lines) using `chart.scales.{x,y}.getPixelForValue()` — the established zero-dependency pattern (HandsOnDataViz template idiom, Chart.js 4 API) |
| `nvidia-smi` (subprocess, read-only) | driver-bundled | G GPU-lanes probe | `nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits` — machine-readable, no parsing of human layout; absent binary degrades to the repo's honest 未安装 verdict pattern (env_smoke precedent). No Python binding (pynvml/NVML adds a dep + ABI surface for one read-only probe) |
| Vendored statistics (`tui`-free `script/` layer) | existing `aggregate_seeds` @483a35c | Multi-seed mean±std for error bars | Already computes per-seed statistics artifacts; std propagation is an extension of the single existing owner (IN-03 single-authority discipline), not a new statistics package |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `chartjs-chart-error-bars` (sgratzl) | 4.x-compatible | Full error-bar/boxplot chart types (bar/line/scatter/polarArea) | **Fallback only** — if v1.3+ needs whisker styling, asymmetric CI, or boxplots beyond the custom plugin. Adds a second CDN script (repo pins Chart.js 4.4.0 UMD only today; the progress page pins zero CDN structurally), so default remains the vendored inline plugin. MIT, actively maintained (renamed from `chartjs-plugin-error-bars`) |
| pytest + node:test (existing lanes) | pinned | Dispatch/resume/error-bar regression tests | Existing fake-executor (run_sweep dry-run) + byte-determinism + SVG-golden lanes cover all new surfaces; no new harness |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `pexpect` pty lane (existing) | Orchestrator live-view e2e | The 261018-08g permanent pty lane is the template for terminal-table assertions without new deps |
| `make snapshot-update` (existing, maintainer-only) | Regenerate monitor/config SVG goldens after G-lanes/multi-GPU UI lands | D-03 review discipline unchanged — regenerate uncommitted, maintainer reviews |

## Installation

Nothing to install. CI stays GPU-free and N>1-free (carried constraint); `uv sync` surface unchanged; no CDN additions unless the sgratzl fallback is later ratified (which would then need the v0.7.1-style package-legitimacy gate: provenance + pinned version, like textual 8.2.8 in 08-02).

## Integration Points

- Orchestrator: `pipeline/run_sweep_shard.py` (sole owner of dispatch; `run_sweep.py`/`run_finetune.py` argv surfaces stay frozen)
- Sub-dataset generator: new offline script under `script/` (deterministic, stratified; separate registry/config file per maintainer ruling)
- Error bars: `script/summarize_comparison.py` (emit mean±std alongside existing aggregates), `dnallm-mark/data/*.json` schema (additive optional fields), `dnallm-mark/js/{main,task}.js` (vendored plugin + floating bars)
- GPU lanes: TUI services layer (textual-free) + slot-5/monitor surfaces

## What NOT to Add

- **pynvml / NVML bindings** — one read-only probe doesn't justify an ABI-coupled dep; CSV mode of nvidia-smi is stable across drivers
- **Any work-queue framework** (celery/dask/joblib) — violates the stdlib-headless orchestrator contract and the no-backend hosting constraint
- **torch-run / DDP tooling** — explicitly out of scope by maintainer decision (不做 DDP)
- **A second Chart.js CDN script by default** — see fallback row above
