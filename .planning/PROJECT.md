# DNALLM-Mark

## What This Is

DNALLM-Mark is a DNA language-model benchmark platform: a PyTorch fine-tuning pipeline that evaluates 41 DNA LLMs across 50 datasets (with custom FLOPs instrumentation), offline Python/Node scripts that aggregate results, and a static multi-page leaderboard website. The current milestone is a **systematic review and hardening pass** over the existing codebase to prepare it for public release: audit all three subsystems, fix confirmed issues, and add regression prevention (data-script tests + CI).

## Core Value

Every number on the public leaderboard is correct and reproducible from code that external reviewers can trust.

## Requirements

### Validated

<!-- Inferred from existing code (brownfield init, map dated 2026-10-08). -->

- ✓ Fine-tuning pipeline: model×dataset training loop delegated to dnallm, per-architecture FLOPs measurement, master performance JSON output (`pipeline/dnallmmark_pipeline.py`)
- ✓ Main leaderboard page: FLOPs-vs-rank scatter chart, sortable table, arena switching (all/animal/plant/microbe) (`dnallm-mark/js/main.js`)
- ✓ Task benchmark page: per-task model rankings, metric dropdown, two-tier caching with retry/preload (`dnallm-mark/js/task.js`, `js/task-loader.js`)
- ✓ Fine-tuning results, models catalog, and datasets catalog pages (`dnallm-mark/js/finetuning.js`, `js/models.js`, `js/datasets.js`)
- ✓ Offline data chain: model-centric → task-centric pivot, multi-method score aggregation (rank/MinMax/z-score/robust), task index generation (`script/get_task_performance.py`, `script/summarize_comparison.py`, `scripts/generate-tasks-index.js`)
- ✓ Client-side submission validation + PR instruction generator (`dnallm-mark/js/submit.js` — implemented but orphaned; `submit.html` missing)

### Active

- [ ] Systematic review of pipeline, data scripts, and frontend producing a severity-graded findings report
- [ ] Fix confirmed correctness bugs (3 pages dead-on-load from `renderNavbar()`, species-as-dataset grouping at `dnallmmark_pipeline.py:1229`, orphaned submit flow)
- [ ] Close maintainability gaps (dependency manifests, documented/detectable data-regeneration chain)
- [ ] Unit tests for the data-processing scripts (`script/`)
- [ ] GitHub Actions CI running the test suite
- [ ] Recompute leaderboard data after fixes, with before/after comparison notes
- [ ] Pre-release hygiene: revoke leaked Zenodo token (`README.md:116`), decide on LICENSE
- [ ] Adapt pipeline to dnallm dev branch (v0.7.1): resolve API/config-schema deltas, imports and dry-run pass
- [ ] Build reproducible local GPU pipeline environment (uv/venv; dnallm from git dev; pinned torch/transformers)
- [ ] Small end-to-end validation: at least one model×dataset fine-tune run against dnallm dev produces a valid performance JSON

### Out of Scope

- Deep security hardening (CSP, SRI on CDN scripts) — correctness/maintainability prioritized this milestone; only token revocation is required pre-release
- Frontend E2E/smoke tests (Playwright-level) — regression prevention scoped to data scripts + CI by decision
- New benchmark entries (actually adding new models/datasets) — mechanism only this milestone (EXT-01/02); hardening, not expansion
- Full benchmark re-run against dnallm dev — needs extensive GPU time; this milestone validates adaptation with one model×dataset pair
- Pipeline rewrite/modularization — fixes stay surgical, minimal diff
- Framework migration (React/Vue/bundler) — vanilla no-build MPA is a hard constraint

## Context

- Brownfield repo mapped 2026-10-08 at commit `a44d310` (7 docs in `.planning/codebase/`)
- Known findings from the map (input to the review, not its conclusion):
  - Leaked Zenodo token in `README.md:116` — needs manual revocation, cannot be fixed by code
  - `finetuning.js` / `models.js` / `datasets.js` / `submit.js` abort rendering in `setup()` because `renderNavbar()` targets a nonexistent `.navbar-container` — 3 production pages render partially or not at all
  - `submit.html` missing while `js/submit.js` (300 lines) and its nav link exist — submission feature unreachable
  - Species-as-dataset bug: `dnallmmark_pipeline.py:1229` treats species as a dataset key
  - Unescaped `innerHTML` rendering — stored-XSS risk if any performance JSON carries hostile strings
  - Duplicate, divergent aggregation logic in `js/data.js:recalculateComparison()` (uncalled, returns placeholders) vs the authoritative `script/summarize_comparison.py`
  - No tests, no `requirements.txt`/`pyproject.toml`, no CI, no LICENSE
- Repo: `https://github.com/zhangtaolab/dnallmmark` — target is public release; code must withstand external scrutiny (paper/community use)
- Upstream DNALLM framework moved: dev branch at v0.7.1 (local clone `/home/forrest/Github/DNALLM`, commit `c99fa9d`, 2026-10-08). The pipeline was written against an older dnallm and must be adapted. Local machine is an NVIDIA GB10 (Grace Blackwell, aarch64, CUDA) — the pipeline environment builds here
- Data regeneration is a manual 3-step chain run from `dnallm-mark/data/` (`get_task_performance.py` → `summarize_comparison.py` → `generate-tasks-index.js`), documented only in README — stale derived files are undetectable today
- `.planning/` is currently gitignored (`.gitignore:90`)

## Constraints

- **Tech stack**: Keep vanilla ES-module JS (no build step, no framework) and Python — public release must not change the architecture
- **Hosting model**: Static files only — no backend or API may be introduced
- **Reproducibility**: Fixes may change aggregated numbers (e.g. species-grouping fix); recomputation is allowed and expected, each change documented with before/after comparison
- **CI feasibility**: GitHub Actions must not require GPU or the external `dnallm` package — test scope limited to stdlib/numpy/pandas scripts and static checks
- **Fix discipline**: Surgical fixes only; no opportunistic refactors that widen review surface

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Milestone = report + fixes + regression prevention | Public release means the audit itself must land in the code, not a drawer | — Pending |
| Regression prevention = data-script unit tests + GitHub Actions CI | Highest value per cost; pipeline needs GPU, frontend tests deferred | — Pending |
| Allow data recomputation after fixes, documented with comparisons | Correctness over number stability — the species fix intentionally changes aggregates | — Pending |
| Priority: correctness first, maintainability second; security limited to token revocation | User prioritization for this milestone | — Pending |
| Adapt to dnallm dev (v0.7.1) with local GPU env + one-pair validation; full benchmark re-run deferred | Upstream moved; local GB10 machine + local DNALLM clone make adaptation verifiable now | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-08 after initialization*
