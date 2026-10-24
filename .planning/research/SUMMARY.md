# Project Research Summary

**Milestone:** v1.3 多 GPU 编排与验证
**Researched:** 2026-10-20
**Method:** inline orchestrator-generated (spawn tooling unavailable this session); repo facts from live code + v1.2 planning record; external facts web-verified where marked

## Key Findings

### Stack: zero new dependencies
- Dynamic dispatch is a **single-dispatcher + Popen workers** stdlib design; `run_sweep_shard.py`'s stdlib-headless contract survives intact. The Phase 10 download-queue driver is the in-repo precedent.
- Error bars: **vendored ~40-line inline Chart.js plugin** (`afterDatasetsDraw` + `getPixelForValue`) + native floating bars; [chartjs-chart-error-bars](https://github.com/sgratzl/chartjs-chart-error-bars) (sgratzl, Chart.js 3/4-ready, MIT) is the ratified-fallback only — it would add a second CDN script against the repo's pin discipline.
- GPU lanes: `nvidia-smi --format=csv,noheader,nounits` read-only subprocess probe; **no pynvml**. Honest 未安装 degradation; CI never needs a GPU.

### Features: four capability groups, one dependency spine
- **Dispatch core is the spine** — live view, failure re-run, TUI monitoring all consume its state file; error bars are independent (ride the data chain).
- Table stakes per group cataloged in FEATURES.md; anti-features locked by maintainer rulings: no DDP, no cost-prediction balancing, no cloud orchestration, no error-aware ranking.

### Architecture: the load-bearing decision is output-root ownership
- Cells need **worker-independent stable paths** (one root, ordinary cell subpaths) + an **O_EXCL claim ledger**; child-level `trainer_state.json` marker-skip stays authoritative. This single decision defuses the top three pitfalls (double-run, blocked resume, merge drift).
- Dispatch mode and legacy static-shard mode **coexist behind one CLI**, declared explicitly; merge refuses mixed modes (dispatch roots need no merge at all).
- Subset datasets = third registry class (not official, not user-custom) with **measured** row counts; stratified sampling mandatory.
- Build order: dispatch core → view/recovery → N=2 smoke → subsets + small sweep → TUI → web error bars.

### Pitfalls: 10 cataloged, all structurally prevented
- Highest risk: **P1** resume-marker ownership (HIGH/HIGH), **P3** lane-blind failure re-run (HIGH/MEDIUM), **P4** unstratified subsets (HIGH/MEDIUM), **P6** error bars moving published numbers (MEDIUM/**CRITICAL** — Core Value).
- Two first-class acceptance criteria recommended: kill-mid-cell → exactly-once re-dispatch test; additive-only JSON emission proven by the zero-drift gate.

## Implications for Roadmap

1. **Dispatch core must be its own early phase** (Ph 13): everything except web error bars depends on it; it carries the riskiest redesign (roots/ledger/resume).
2. **N=2 smoke gates the TUI phase** (proven core before UI rides it — mirrors v1.2's 单卡→多卡 sequencing discipline); it closes WINDOWS #21 and lands the D-05 revision.
3. **Subset generator + small real sweep** is one phase (generator without the sweep is unproven; the sweep without the generator has no bounded data budget).
4. **TUI surface** (launch + monitor + G lanes) as its own phase; goldens regenerate under D-03 review discipline.
5. **Web error bars** as the final phase — independent spine, real artifacts available from the sweep phase, display-only discipline enforced by the zero-drift gate.
6. Cross-cutting: fake-children test lanes keep CI N>1-free (structural, all phases); Linux-only rule blocks any cross-platform shim.

## Sources

- Repo: `docs/multi-gpu.md`; `.planning/PROJECT.md` (v1.3 Current Milestone + Key Decisions, maintainer rulings 2026-10-20); `.planning/MILESTONES.md` v1.2 record; `pipeline/run_sweep_shard.py` + Phase 12 planning record
- External (web-verified 2026-10-20): [sgratzl/chartjs-chart-error-bars](https://github.com/sgratzl/chartjs-chart-error-bars) (Chart.js 3/4 error-bar chart types, MIT); [HandsOnDataViz — Error Bars with Chart.js](https://handsondataviz.org/chartjs-error-bars.html) (custom `afterDatasetsDraw` plugin pattern); Chart.js 4 floating-bar data semantics
