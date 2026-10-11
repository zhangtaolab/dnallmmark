# DNALLM-Mark

## What This Is

DNALLM-Mark is a DNA language-model benchmark platform: a PyTorch fine-tuning pipeline that evaluates 62 DNA LLMs across 50 datasets (three-seed protocol, PEFT/VEP/curve lanes), offline Python/Node scripts that aggregate results with vendored statistics, and a static multi-page leaderboard website — hardened and release-reviewed in v0.7.1 (audit, contracts, CI, methodology migration, provenance, snapshots). The current milestone **v1.2 TUI任务** builds the operator-facing terminal console: model×dataset selection with data presence/download, run configuration, single-GPU launch with task monitoring, and multi-GPU orchestration after single-GPU validation.

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
- ✓ Systematic tri-subsystem review producing a severity-graded, fully-reproduced findings report — `AUDIT.md`, 24 findings (2 P0 / 12 P1 / 10 P2) — Phase 1
- ✓ Reproducibility substrate: `data-v1` frozen baseline (tag + SHA256 manifest + `baseline/compare.py`), pinned dependencies (pyproject/uv.lock, pandas 2.3.3 / numpy 2.5.3), deterministic data generators with one-time fully-attributed 52-file migration — Phase 1
- ✓ Pre-release hygiene: secret-hygiene decision recorded (Zenodo preview link intentional, D-08), full-history gitleaks scan clean, MIT LICENSE landed with holder "zhangtaolab and DNALLM-Mark contributors" (maintainer-confirmed 2026-10-09) — Phase 1
- ✓ **v0.7.1 shipped (6 phases / 24 plans / 68 tasks, 2026-10-11)**: dev-branch reconciliation to `run_finetune.py`/`run_sweep.py` (seed protocol, priority tiers, failure re-run, `--subset_file` fairness, PEFT/variant/curve flags), correctness core (species fix, dual registries, unified exporter, vendored statistics), CI (SHA-pinned 4-job workflow, first real-runner green), F6 methodology migration (weighted dual view, 861-pair permutation artifact, CHANGELOG/manifest), N-audit + provenance (ModelScope 50/50, maintainer-reviewed), snapshots, METHODOLOGY/ONBOARDING/README reproduction, docs trio, doi_swap prepared — full record in `.planning/MILESTONES.md` and `reviewer-response/REPORT.md` (untracked)

### Active

- [ ] TUI console: model×dataset selection matrix (filters, preset groups, template import/export)
- [ ] Data management panel: presence audit view, ModelScope fetch + row-count verification, persistent download queue
- [ ] Run configuration surface: seeds/PEFT/variant/curve/subset/epochs + auto-GA (`--effective-batch`) + project/storage directory settings
- [ ] Single-GPU launch with env_smoke gate, dry-run preview, E2' authorization boundary
- [ ] Task monitoring: cell dashboard, failure re-run, log tailing, resume states
- [ ] FlopsCounter port (20+ architecture hooks) from the legacy pipeline to `run_finetune.py`
- [ ] Multi-GPU orchestration (model sharding × CUDA_VISIBLE_DEVICES; DDP layer) — gated on single-GPU validation

### Out of Scope

- Deep security hardening (CSP, SRI on CDN scripts) — correctness/maintainability prioritized this milestone; only token revocation is required pre-release
- Frontend E2E/smoke tests (Playwright-level) — regression prevention scoped to data scripts + CI by decision
- New benchmark entries (actually adding new models/datasets) — mechanism only this milestone (EXT-01/02); hardening, not expansion
- Full benchmark re-run against dnallm dev — needs extensive GPU time; this milestone validates adaptation with one model×dataset pair
- Pipeline rewrite/modularization — fixes stay surgical, minimal diff
- Framework migration (React/Vue/bundler) — vanilla no-build MPA is a hard constraint

## Context

- v0.7.1 closed and archived 2026-10-11 (`.planning/MILESTONES.md`); reviewer-response evidence base generated (gitignored)
- Upstream DNALLM on **main @ v1.2.1** (local clone `/home/forrest/Github/DNALLM`, STRICTLY READ-ONLY; peft native; metric registry stable; `aggregate_seeds` verified identical to our vendored copy)
- GB10 environment live: `[gpu]` group + dnallm 1.2.1 tag-extract + peft 0.21.2 + torch 2.11.0+cu130; four bounded smokes executed green (env_smoke, LoRA, probe, VEP)
- ModelScope dataset coverage 50/50 (zhangtaolab 9 / lgq12697 34 / forrestzhang 7); SDK token stored (`~/.modelscope`)
- Pre-revision data frozen immutably at `baseline/pre-revision-data/` (a44d310 tree + SHA-256) for E2' old-vs-new comparison — never overwritten
- `dnallmmark.org` serves from main (currently rolled back to a44d310 after a mixed deploy broke it; re-merge procedure documented)
- TUI requirements gathered in `docs/TUI-REQUIREMENTS.md` (team-supplemented + orchestrator cross-checked)
- Branch flow: **autorun = standing development branch**; dev/main sync only on explicit maintainer request
- E2' three-seed full re-run remains maintainer dual-gate; `--subset_file` sweep threading is the one known pre-launch gap (~15 lines)

## Constraints

- **Tech stack**: Vanilla ES-module JS frontend (no build step) unchanged; TUI = pure-Python pip-installable framework (Textual preferred — no build step, consistent with repo architecture)
- **E2' boundary**: TUI may launch bounded runs and present the full-sweep confirmation gate; the full three-seed sweep itself stays maintainer-authorized
- **CI feasibility**: GitHub Actions stays GPU/dnallm-free; TUI tests CPU-side with injectable seams
- **DNALLM read-only**: The suite repo is never written by this project (issue channel only)
- **Reproducibility**: Leaderboard numbers move only through the inventoried migration discipline (one-commit schema+data+goldens; drift gate green)
- **Fix discipline**: Surgical changes; no opportunistic refactors

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Milestone = report + fixes + regression prevention | Public release means the audit itself must land in the code, not a drawer | — Pending |
| Regression prevention = data-script unit tests + GitHub Actions CI | Highest value per cost; pipeline needs GPU, frontend tests deferred | — Pending |
| Allow data recomputation after fixes, documented with comparisons | Correctness over number stability — the species fix intentionally changes aggregates | — Pending |
| Priority: correctness first, maintainability second; security limited to token revocation | User prioritization for this milestone | — Pending |
| Adapt to dnallm dev (v0.7.1) with local GPU env + one-pair validation; full benchmark re-run deferred | Upstream moved; local GB10 machine + local DNALLM clone make adaptation verifiable now | — Pending |
| D-09 closed: LICENSE holder = "zhangtaolab and DNALLM-Mark contributors" | Maintainer override of the surfaced git-author assumption during Phase 1 UAT (2026-10-09); org handle matches the GitHub org | ✓ Applied (33b80ca) |
| D-06 accepted: six exact-tie-group census is the complete migration attribution | Maintainer UAT confirmation over independently re-derived evidence (4 flip/2 stable groups, exact rank_score ties both sides) | ✓ Confirmed |
| P0 rubric boundary: producer-side regeneration risks grade P0 even with committed data intact | "Risks corrupting published numbers on regeneration" reading accepted in UAT; steers Phase 4 scope (AUD-01..06) | ✓ Confirmed |
| Baseline form: annotated data-v1 tag + tracked SHA256 manifest + comparator, no golden copies | git stores exact bytes at the tag; 52 duplicated copies would rot | ✓ Landed (Phase 1) |
| v1.2 scope: FlopsCounter port included (early phase) | Feeds E2' FLOPs correctness + leaderboard efficiency axis; beneficiary beyond the TUI | — Pending (2026-10-11) |
| v1.2 scope: multi-GPU as final phase P4, hard-gated on single-GPU validation | Maintainer's stated sequencing: 单卡开发成功再开发多卡 | — Pending (2026-10-11) |
| v1.2 auto-GA policy: `--effective-batch` flag, GA=max(1, N//batch_size), default 16 | Team requirement (lgq12697 Q7) on top of existing dynamic batch sizing + D-07 reset | — Pending |

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
*Last updated: 2026-10-11 after v1.2 TUI任务 milestone start*
