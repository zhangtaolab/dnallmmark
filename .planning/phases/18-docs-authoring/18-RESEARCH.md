# Phase 18: 文档撰写 (Documentation) - Research

**Researched:** 2026-10-22
**Domain:** Technical-documentation rewrite (dispatch-mode runbooks) + self-contained static HTML test-results report
**Confidence:** HIGH (entirely in-repo survey; every claim carries a path:line citation from this session)

## Summary

Phase 18 is a pure documentation-and-artifact phase with one code-adjacent edit
(the `ABOUT_MILESTONE_STAGE` string). The doc targets split into two states:
`docs/multi-gpu.md` is HALF-rewritten (the Phase-15 dispatch smoke section at
lines 217-309 is executed-reality and must be extended, not touched), while its
lines 1-215 still frame STATIC sharding as the default procedure — dispatch
surface (`--mode dispatch`, `--rerun-failed`) appears only inside the smoke
section, and the 5% subset workflow is entirely absent from every doc.
`README.md`, `docs/ONBOARDING.md`, and `docs/GETTING-STARTED.md` contain **zero
dispatch/subset-dataset content** and no stale-static passages beyond two
static-framed descriptors (README:122-123 and the docs-index entry README:574,
which still says "sharding vs DDP decisions and the runbook"). A previously
unsurveyed staleness finding: **`docs/TUI-GUIDE.md:193-204` now contradicts
shipped Phase-16 reality** ("the TUI composes single sweeps only", "zero new
screens") — TUI-02/TUI-03 shipped TUI-launched dispatch runs, G lanes, and
dispatch rows.

The report (D18-05..08) has a complete, ratified design contract in
`18-UI-SPEC.md` (structure, tokens, badge vocabulary, figure contract, print
stylesheet, zero-external-request grep gate). Its evidence corpus is fully
inventoried below with exact paths and the key numbers: five verification
scores (13→23/23, 14→28/28, 15→7/7, 16→41/41, 17→16/16), sweep 272 s / 12
cells / run_id `4e74c92d…` (15-03-SUMMARY:145-146), smoke r2 155 s
(smoke-r2-timing.txt), and the two gap-closure stories (15-04 run_record,
15-05 eval merge). One evidence-pairing hazard was found: the smoke run_id
`aff2faa3…` lives in `dispatch_state.final.json` (the r1 archive) while the
155 s timing belongs to the r2 run whose archived state
(`dispatch_state.final-r2.json`) carries run_id `7759c2cc…` — the executor
must pair run_id and timing from the SAME archived artifact, never from
memory. Version surfaces are already consistent at 1.3.0 (pyproject.toml:5,
uv.lock:562-563) — D18-04's only edit is the milestone string at
`tui/strings.py:1047-1052` ("v1.3.0 开发中" → delivered scope), which is
test-safe because the pin at `tests/tui/test_pilot_nav_shell.py:892` asserts
symbol equality (`== ABOUT_MILESTONE_STAGE`), not a literal.

**Primary recommendation:** Structure the phase as (1) multi-gpu.md
dispatch-first restructure that PRESERVES the executed smoke section verbatim
and re-homes the static runbook under explicit `--mode static`, (2) three
additive doc edits + one TUI-GUIDE correction, (3) the one-line strings.py
milestone rewrite, (4) report generation as a copy-numbers-from-artifacts task
per the ratified 18-UI-SPEC, with committed-golden SVG copies under
`docs/report-assets/` (PENDING-REVIEW-badged for the WINDOWS #50 four) and the
pty live capture attempted only as a stretch task with the UI-SPEC's honest
degradation path as the sanctioned fallback.

<user_constraints>
## User Constraints (from 18-CONTEXT.md)

### Locked Decisions
- **D18-01:** docs/multi-gpu.md rewritten for dispatch mode — every command copy-pasteable (incl. subset generation); the N=2 smoke procedure matches the EXECUTED Phase-15 reality (the r2 evidence); legacy static-shard mode documented as coexisting (--mode static, merge/cleanup semantics)
- **D18-02:** README + ONBOARDING/GETTING-STARTED gain the multi-GPU dispatch section + the 5% subset workflow (generate → configure → run → consume); zero stale static-sharding-only instructions remain
- **D18-03:** TUI multi-GPU usage documented (multi-GPU launch, monitoring, G lanes) in the TUI-DEMO.md precedent shape, verified against shipped screens (the Phase-16 UI-SPEC is the source of truth)
- **D18-04:** Version surfaces consistent at 1.3.0 (pyproject, uv.lock, TUI about milestone stage) — verify-only unless drift found; the about-screen milestone-stage row is rewritten to the DELIVERED v1.3 scope
- **D18-05:** Comprehensive HTML report (self-contained, offline-viewable: inline CSS, relative/absolute asset links) at `baseline/v1.3-test-report.html` (or docs/ — planner picks) covering ALL SIX phases: goal, what shipped, test evidence, the two gap-closures (15-04 run_record, 15-05 eval merge), GPU run evidence (smoke 155s/2 cells, sweep 272s/12 cells, dispatch_state done 12/12), review-loop outcomes
- **D18-06:** Screenshots/SVG embedded: (a) Phase-17 browser pixel-verification PNGs at /root/autodl-tmp/phase17-preview/; (b) TUI SVG goldens (monitor w/ G lanes + dispatch rows, run_config w/ 多GPU section, confirm golden) as committed report assets, PLUS at least one REAL pty execution capture if feasible; analysis text per image
- **D18-07:** Test-suite summary table: per-lane counts (pytest 2236-passed / 6 environmental, node 44/44, pty byte-silence, tier-1 contracts, determinism/vendored unmodified) + known environmental exclusions (root-chmod class, HF-egress note)
- **D18-08:** The report is a committed DOCUMENT artifact linked from README or docs index — not a CI job; regeneration manual per static-file philosophy

### Claude's Discretion
- Report structure/sections order; asset directory layout (e.g. docs/report-assets/ vs baseline/)
- Whether TUI "execution" captures come from the SVG golden machinery re-run vs the existing committed goldens (uncommitted #50 batch may be referenced — planner notes the dependency)

### Deferred Ideas (OUT OF SCOPE)
- Post-milestone full leaderboard regeneration with multi-seed data (maintainer decision)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DOCS-01 | multi-gpu.md + related runbooks rewritten dispatch-first, copy-pasteable, smoke matches executed Phase-15 reality, static mode coexists | Target survey §T1 (exact stale/current line map); executed-command corpus §Code Examples; shard CLI surface verified at pipeline/run_sweep_shard.py:352-469 |
| DOCS-02 | README + ONBOARDING/GETTING-STARTED gain dispatch + 5% subset workflow; zero stale static-only instructions | Target survey §T2/T3 (insertion points + the two static-framed descriptors); subset generator CLI verified at script/make_subset_datasets.py:140-175 |
| DOCS-03 | TUI multi-GPU usage in TUI-DEMO.md precedent shape, verified against shipped screens | Target survey §T4 (TUI-DEMO section anatomy + re-record machinery + the TUI-GUIDE:193-204 contradiction); 16-UI-SPEC vocabulary at lines 77-79 |
| DOCS-04 | Version surfaces 1.3.0 consistent; about milestone row → delivered v1.3 scope | Version survey §T5 (pyproject/uv.lock already 1.3.0; strings.py:1047-1052 is the only edit; test pin is symbol-based) |
| D18-05..08 | Milestone test-results HTML report | 18-UI-SPEC ratified contract + evidence corpus inventory §T7 + asset conventions §T8 + pty feasibility §T9 |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Dispatch/subset runbook accuracy | Docs (markdown) | Pipeline CLI (source of truth) | Commands must be copied from executed evidence; pipeline/run_sweep_shard.py argv surface is the authority |
| TUI multi-GPU usage doc | Docs (TUI-DEMO precedent) | tui/ screens + 16-UI-SPEC | "Verified against shipped screens" — 16-UI-SPEC is the ratified vocabulary source |
| Version consistency | Build metadata (pyproject/uv.lock) | TUI about screen (strings.py) | Verify-only except the one static milestone constant |
| Test-results report | Static site family (docs/) | Offline evidence corpus | Committed static artifact per D18-08; zero runtime, zero CI |
| Report images | docs/report-assets/ (new) | tests/tui/__snapshots__ + /root/autodl-tmp evidence | Committed copies of goldens/PNGs; sources stay where they are |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| none | — | This phase installs NOTHING | Vanilla markdown + one static HTML file with inline CSS (18-UI-SPEC: tool = none, zero CDN, zero JS) |

No packages are installed, removed, or upgraded by this phase. Chart.js/SheetJS
CDN pins are untouched (site-only concerns). **Installation: nothing.**

## Package Legitimacy Audit

Not applicable — no external packages. (No registry lookups were needed; no
`npm`/`pip`/`cargo` installs appear in any task this phase.)

## Survey of Deliverable Targets (live state, line-cited)

### T1. docs/multi-gpu.md — 309 lines, last touched by commits 5295cbd + 55c8788 (Phase 15)

**Current and correct (DO NOT rewrite — extend only):**
- § "The dispatch-mode N=2 smoke procedure (executed on this machine)" — lines 217-309. Written FROM the executed r2 commands (D15-02 procedure/doc identity): env exports (`HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`), the `--mode dispatch --workers 2 --gpus 0,1` launch with explicit absolute `--output-root`/`--log_dir` (lines 246-253), the live dispatcher output block (258-268), terminal-state assertion one-liners (280-283), consumption dry-run (290-292), dispatch-root boundary rules (294-299), isolation assertion (301-304).
- § "Machine roles" lines 190-204 (D-05 revised 本机=双卡验证机 — current).
- § 5 Merge/cleanup lines 134-171 — already Phase-14-current (`--cleanup` typed-phrase, dispatch roots refuse both).
- § "The E2' trust boundary" lines 206-215 — current philosophy.

**Stale for DOCS-01 (static-framed as default):**
- Intro lines 1-15: presents static sharding as THE runbook; no mention of two modes. The smoke section's own last-line caveat (added Phase 15) says the dispatch-first pass "is Phase 18, DOCS-01" — that caveat gets removed when the restructure lands.
- § "The decision: model sharding vs DDP" lines 17-38: table frames the choice as sharding-vs-DDP; post-Phase-13 the primary axis is dispatch-vs-static, with DDP still deferred. Needs reframing, not deletion (MGPU-06 coexistence; DDP ruling stays).
- § 1 Launch lines 51-85: dry-run + real launch commands WITHOUT `--mode` (implicit static). Must become the explicit `--mode static` variant; the dispatch variant gets its own copy-paste block (generalized from the executed smoke/sweep argv).
- § 2 Watch the workers lines 87-93: N worker roots + `[a]`-attach per root — static-only. Post-Phase-16 the TUI ALSO renders dispatch natively (G lanes + dispatch rows from one shared root) — must be updated to cover both.
- § 4 Isolated failure re-run lines 111-131: static `--from-failures` per-worker recipe. Phase 14's cross-worker `--rerun-failed` (dispatch) is mentioned only inside the smoke section (line 296) — needs promotion to a first-class subsection alongside the static recipe.
- § 3 killpg recipe lines 95-109: still valid for both modes (workers are `start_new_session=True` children either way) — verify wording, likely keep as-is.
- **Absent entirely:** the 5% subset workflow (generate via `script/make_subset_datasets.py` → configure → run through dispatch → consume). Required by D18-01 ("incl. subset generation"). The executed facts: output under `pipeline/datasets-smoke`, registry `pipeline/registry-smoke`, fraction=0.05 seed=42, measured rows 105/11/117 (source 2110/234/2344) and 598/74/74 (source 11971/1497/1497) — `[VERIFIED: /root/autodl-tmp/phase15-evidence/subset-generation.log:1-3]`.

### T2. README.md — 583 lines

- No dispatch/subset-dataset content anywhere (grep hits are unrelated: multi-label, multi-species, `--gpu_memory`).
- Two static-framed descriptors to refresh: line 122-123 ("running the sweep across multiple GPUs is documented in docs/multi-gpu.md" — the pointer is fine, the target changed) and the docs-index entry line 574: "**[multi-gpu.md](docs/multi-gpu.md)**: Multi-GPU sweep orchestration — sharding vs DDP decisions and the runbook" → should read dispatch-first.
- Insertion points: the "🔁 Reproducing the Leaderboard" section (starts ~line 113) is where a dispatch/subset subsection naturally slots (after the single-GPU sweep steps); the docs index (lines 564-583) gains the report link (D18-08) — index format is one bullet per doc, bold title + colon + one-line description.
- GETTING-STARTED pointer list line 154 (`- [multi-gpu.md](multi-gpu.md) — multi-GPU sweep orchestration`) — same descriptor refresh.

### T3. docs/ONBOARDING.md (217) + docs/GETTING-STARTED.md (156)

- ONBOARDING: § 5 "Validate the sweep matrix with a dry run" (lines 69-86) uses `--tasks <name1,name2>` — that is TASK-subsetting, a different concept from the 5% subset DATASETS; the new section must disambiguate explicitly or readers will conflate them. § 6 "GPU runs (maintainer…)" lines 88-90 is the natural home for a dispatch pointer + the 5% subset workflow summary (generate → configure → run → consume per D18-02). No stale-static prose found beyond the multi-gpu.md dependency itself.
- GETTING-STARTED: explicitly CPU-only-scoped ("Everything here runs on a CPU-only machine", line 4); multi-GPU stays a pointer (line 154 deeper-docs list) — do NOT inline GPU workflow here; just keep the descriptor accurate. This satisfies "zero stale" without bloating the on-ramp.

### T4. docs/TUI-DEMO.md (209) — the precedent shape + docs/TUI-GUIDE.md (243)

TUI-DEMO anatomy (the shape D18-03 mandates): 10 numbered sections, one per
console capability. Each section = (1) bilingual GIF table `| English | 中文 |`
embedding `demo/gifs/{scene}-{en,zh}.gif`, (2) prose of what happens live,
(3) a Key/Action table, (4) cross-link to the TUI-GUIDE.md anchor, (5) an
honest italic "*What actually happened:*" note. Re-record machinery:
`scripts/demo/record.sh SCENE LANG [SPEED]`, scenes listed by
`scripts/demo/record_tui_demo.py --list-scenes` (ten today — NO multi-GPU
scene exists), requires asciinema + agg on PATH and, for launch scenes, REAL
GPU training (documented at lines 189-209). **Implication:** recording a new
multi-GPU GIF section = new scene-driver code + a real dual-GPU run — a
code+GPU change disproportionate to a docs phase; the precedent's own honesty
discipline supports a prose section (shape items 2-5) referencing the shipped
screens/goldens with an explicit "GIF re-record queued" note. Planner decides;
see Open Questions Q1.

Phase-16 surfaces to document (vocabulary `[VERIFIED:
.planning/phases/16-tui-multi-gpu-surface/16-UI-SPEC.md:77-79]`): "G GPU-lanes
panel (slot-5)" — per-GPU lane rows (index / utilization bar+% / memory
used-total / temperature) on the 2s cadence, honest 未安装 + N=0 empty states;
"Dispatch rows (slot-5 Running tab)" — dispatch line (queue depth, status) +
per-worker in-flight rows from `dispatch_state.json` v2, stale-marked >60s;
"Slot-4 multi-GPU launch" — workers/GPUs fields → dispatch argv
(`run_sweep_shard.py --mode dispatch --workers N --gpus …`, D16-09),
dispatch-plan preview line on the confirm face, multi-GPU-aware gate chain
unchanged in order.

**Staleness finding (NEW, survey-discovered):** `docs/TUI-GUIDE.md:193-204`
states "Multi-GPU runs are CLI-orchestrated … the TUI composes single sweeps
only", "the monitor renders N workers natively with zero new screens", and
describes only static worker-root attaching. Phase 16 shipped TUI-launched
dispatch (TUI-02) and G lanes/dispatch rows (TUI-01/03) — these lines now
contradict shipped screens and violate the spirit of D18-03 ("verified
against shipped screens") and D18-02 ("zero stale"). Recommend one corrective
task; flag for planner confirmation (see Open Questions Q2).

### T5. Version surfaces (D18-04)

- `pyproject.toml:5` → `version = "1.3.0"` `[VERIFIED]`; `uv.lock:562-563` → `name = "dnallmmark"` / `version = "1.3.0"` `[VERIFIED]` — consistent; verify-only, NO bump needed.
- The single edit: `tui/strings.py:1047-1052` — `ABOUT_MILESTONE_STAGE = _t("ABOUT_MILESTONE_STAGE", "v1.3.0 开发中 — 多 GPU 编排与验证（Phase 13-18）：动态调度/运行视图/失败恢复/双卡验证/TUI 多卡界面/error bar/文档", "v1.3.0 in development — multi-GPU orchestration & validation (Phases 13-18): …")` — rewrite 开发中/in-development to delivered scope (both languages, one `_t()` call).
- Test safety `[VERIFIED: tests/tui/test_pilot_nav_shell.py:892]`: `assert _about_value(screen, "milestone") == ABOUT_MILESTONE_STAGE` — symbol equality via import; a content change keeps this green with zero test edits. No literal-string pin found (`grep "开发中" tests/` → none). No about-screen SVG golden exists (snapshot dir has env_check, selection_*, data_manager*, run_config*, monitor_*, wizard — no about.svg), so no golden churn.

### T6. Dispatch/subset CLI surface (the copy-paste authority)

`pipeline/run_sweep_shard.py` flags `[VERIFIED: pipeline/run_sweep_shard.py:352-469]`:
`--workers`, `--gpus`, `--models`, `--dry-run`, `--mode`, `--merge`,
`--cleanup` (typed-phrase `--yes <abs resolved root>`), `--rerun-failed`
(dispatch-only: "needs NEITHER --models NOR --seeds"). Lane flags
(`--tasks --seeds --peft --num_train_epochs --registry-dir --dataset-root` …)
pass through VERBATIM to workers.

`script/make_subset_datasets.py` `[VERIFIED: script/make_subset_datasets.py:140-175]`
— required: `--dataset-root` (REAL datasets root), `--output-root` (subset
datasets root, never a real-run root), `--registry-dir` (subset registry
OUTPUT dir — refused if it equals/contains `pipeline/` or the custom registry
dir, D15-07), `--models`, `--tasks`; optional `--fraction` (default 0.05),
`--seed` (default 42). Semantics: per-split independent stratified sampling,
`k = max(1, int(n*fraction))` floor-of-1, largest-remainder class allocation,
run-twice byte-identical (docstring lines 1-40).

### T7. Report evidence corpus (exact paths + key numbers)

**Verification scores** `[VERIFIED: .planning/phases/1[3-7]-*/1[3-7]-VERIFICATION.md]`
(all `status: passed`):
| Phase | Score |
|---|---|
| 13 dynamic-dispatch-core | 23/23 |
| 14 orchestration-view-recovery | 28/28 |
| 15 dual-gpu-validation-subsets | 7/7 |
| 16 tui-multi-gpu-surface | 41/41 |
| 17 web-multiseed-error-bars | 16/16 |

**Suite/lane counts:** pytest full suite **2236 passed / 6 documented
environmental root-chmod failures** — recorded in the Phase-17 SUMMARY and
quoted at `17-VERIFICATION.md:121` (which also notes the suite needs the
machine's academic proxy for one evaluate-touching lane — cite-or-rerun
decision, see Open Questions Q4). Node lane **44/44** `[VERIFIED:
17-VERIFICATION.md:69]` (`node --test tests/js/*.test.js`, includes
`tests/js/error-bars.test.js`, 18 cases). Other D18-07 lane rows (pty
byte-silence, tier-1 contract pins, determinism, vendored-stats unmodified)
come from the suite's named gates — executor pastes real gate output at
generation time (18-UI-SPEC lane-table contract).

**GPU runs:**
- Smoke r2: **155 s, exit 0, 2 cells** `[VERIFIED: /root/autodl-tmp/phase15-evidence/smoke-r2-timing.txt:1-2]` (`START 2026-10-20T15:20:00Z / END …15:22:35Z … DURATION 155s`). Archived terminal state `dispatch_state.final-r2.json` carries run_id `7759c2cc05364ebdacd2c6a5fa614bac`; `dispatch_state.final.json` (r1) carries `aff2faa39a6c433188f1fbb9c75f0275`. **Pairing hazard:** 155 s belongs to r2; do NOT print run_id `aff2faa3…` beside the 155 s number unless the archived artifact itself pairs them — read the run_id from the SAME dispatch_state file whose timing you cite.
- Sweep r2: **272 s (2026-10-21T00:11:11Z→00:15:43Z), exit 0, dispatch done 12/12, 0 failed, 0 skipped, both GPUs, run_id `4e74c92d27944db9a20488cb374719a4`** `[VERIFIED: 15-03-SUMMARY.md:55,145-147]`. Fresh root `pipeline/finetuned-sweep-r2`; models plant-dnabert-6mer + plant-dnamamba-6mer × iDNA_ABF_datasets__5mC + GUE__emp_H3 × seeds 42/43/44, 1 epoch, 5% subsets (REQUIREMENTS.md VAL-03 row). Live-view sample lines available in `/root/autodl-tmp/phase15-evidence/sweep-dispatch-r2.log:1-15`.

**Gap-closure stories (D18-05 callouts):** 15-04 (dispatch_core writes
`run_record.json` at claim finalize — run_sweep record shape, WR-12 no
overwrite; context in multi-gpu.md:275-277) and 15-05 (the WINDOWS #45
producer gap: `run_finetune` discarded `trainer.evaluate()`, export emitted
empty score slots, summarize emitted `{}`; fix = flat-additive eval merge +
animal/microbe archive-list correction; full arc in 15-03-SUMMARY.md:55 and
15-04/15-05 SUMMARY/PLAN files).

**Review-loop outcomes:** every phase dir has REVIEW.md + REVIEW.iter2(/3) +
REVIEW-FIX* + REVIEW-DISPOSITION.md (13: 3 iters; 14: 2; 15: 3; 16: 2; 17:
2) — the report cites the disposition files as the review-loop evidence.

**Images:**
- Phase-17 browser verification PNGs `[VERIFIED: ls /root/autodl-tmp/phase17-preview/]`: `shot-scatter.png`, `shot-scatter-tooltip.png`, `shot-bars.png`, `shot-bars2.png`, `shot-bars3.png`, `shot-bars-tooltip.png`, plus `geometry.json` / `bars-geo.json` (pixel-geometry evidence) and the rendered `site/` copy.
- TUI goldens `tests/tui/__snapshots__/` — 10 files. **WINDOWS #50 batch = exactly 4** `[VERIFIED: git status]`: modified `monitor_empty.svg`, `monitor_running.svg`, `run_config.svg` + untracked `run_config_confirm.svg` — the D-03 uncommitted-until-reviewed batch. Report embeds copies under report-assets with PENDING-REVIEW badges (18-UI-SPEC figure contract); the golden lane files themselves stay uncommitted.
- Phase-15 evidence pack `/root/autodl-tmp/phase15-evidence/` (41 files): dispatch snapshots (final/final-r2/midrun-sweep/midrun-sweep-r2), sha256 packs, timing files, subset-generation.log, registry hashes, sweep table snapshots, consumption logs.
- 15-03 archived consumption JSONs `[VERIFIED: ls .planning/phases/15-dual-gpu-validation-subsets/artifacts/]`: models_comparison.json, _animal, _microbe, plant-dnabert-6mer_performance.json, plant-dnamamba-6mer_performance.json.

### T8. Asset conventions (committed binaries precedent)

`docs/demo/` is the repo's only committed-binary-asset pattern:
`docs/demo/gifs/*.gif` (2 committed), `docs/demo/casts/*.cast` (20
committed asciinema casts), `docs/demo/RECORDED.md`. `docs/report-assets/`
(18-UI-SPEC recommended) is NEW but follows the same docs-relative
committed-binary precedent. No docs image convention exists outside demo/.
SVG goldens are generated via `App.run_test(size=(120,40))` +
`App.export_screenshot()` (SVG) — rasterizing via cairosvg is explicitly
REJECTED in the golden harness docstring `[VERIFIED:
tests/tui/test_snapshots.py:19-23]`; the report therefore embeds SVGs
directly (natural 1480×1024, renders ~74% scale in the 1100px column per
18-UI-SPEC).

### T9. pty real-execution capture feasibility (D18-06 "if feasible")

`tests/tui/test_pty_driver.py` exists as the permanent real-pty regression
lane — it spawns the REAL app under a pty and asserts render behavior
(docstring lines 1-30 document findings invisible to Pilot). It does NOT
currently emit image artifacts, and the repo has NO ANSI→SVG/PNG renderer
(any such converter would be new tooling — and the snapshot harness
deliberately avoids rasterization). Feasibility verdict: **a pty-driven
monitor-screen capture with a live dispatch root is buildable (drive the app
to slot 5 with an attached dispatch root from sweep-dispatch-r2 evidence or a
fresh tiny run) but requires new conversion tooling not in the repo** —
MEDIUM-LOW feasibility, discretionary effort. The ratified fallback is the
18-UI-SPEC honest-degradation path: `PENDING-REVIEW` badge + "Capture not
available at publication" copy with a named ticket — NEVER a fabricated
placeholder. Alternative real-execution flavor without new rendering code:
asciinema+agg GIF via the demo machinery — but that needs a new scene driver
(same objection as T4). Recommendation: goldens-as-assets primary; pty
capture as an explicitly-optional stretch task with time-boxed effort.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TUI screen images | ANSI→SVG/PNG converter | Existing SVG goldens (`export_screenshot` machinery) + copies in report-assets | Rasterization is explicitly rejected by the golden harness; goldens already show G lanes + dispatch rows |
| Report styling | CSS framework / build step | Single inline `<style>` with mirrored tokens per 18-UI-SPEC | Zero-CDN/zero-JS hard constraint; token mapping table already enumerated |
| Evidence numbers | Recomputed/simplified counts | Paste from real gate output / archived artifacts at generation time | 18-UI-SPEC every-number-is-real rule; the run_id pairing hazard shows why |
| Link/asset validation | New checker script | grep one-liners (zero-external-request gate: no `<script src=`, no `@import`, no `url(http`, no external font links) | The 12-02 zero-CDN-pin precedent; single grep, no tooling to maintain |

**Key insight:** every tempting "small utility" in this phase (renderer,
checker, generator) already has a ratified manual or grep-based equivalent —
the phase's value is accuracy and honesty, not tooling.

## Runtime State Inventory

> Docs phase — no rename/migration — but stateful items bound to this phase:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Uncommitted goldens (OS-adjacent working tree) |  files: `monitor_empty.svg` `monitor_running.svg` `run_config.svg` (modified) + `run_config_confirm.svg` (untracked) — the WINDOWS #50 D-03 batch | Stay uncommitted (binding constraint); report embeds COPIES under docs/report-assets/ badged PENDING-REVIEW |
| Out-of-repo evidence | `/root/autodl-tmp/phase15-evidence/` (41 files), `/root/autodl-tmp/phase17-preview/` (6 PNGs + geo JSONs + site copy) | Copy selected assets INTO the repo at report generation; originals untouched |
| Version metadata | pyproject.toml:5 = 1.3.0; uv.lock:562-563 = 1.3.0 — consistent | Verify-only (no drift found this session) |
| Milestone string | tui/strings.py:1047-1052 "开发中/in development" | One edit → delivered scope; test pin is symbol-based (safe) |
| Live runtime roots | `pipeline/finetuned-sweep-r2`, `pipeline/finetuned-smoke-r2` etc. — gitignored by design | None (docs reference paths only; no rerun required) |
| Secrets/env vars | None — docs cite `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` (non-secret offline vars) | None |

## Common Pitfalls

### Pitfall 1: Transcribing evidence numbers from memory or from the wrong artifact
**What goes wrong:** run_id/timing/duration mispairing — concretely: the
objective's own pairing (smoke 155 s + run_id aff2faa3) mixes the r2 timing
(smoke-r2-timing.txt) with the r1 run_id (dispatch_state.final.json); r2's
archived state says `7759c2cc…`.
**How to avoid:** every GPU-evidence number in the report is read from ONE
named artifact file at generation time and the artifact path is cited beside
it; the plan's verification step greps the report for each number's source
path.
**Warning signs:** a run_id appearing without its source file path.

### Pitfall 2: Rewriting the executed smoke section
**What goes wrong:** touching multi-gpu.md lines 217-309 prose/commands breaks
the D15-02 procedure/doc identity (the section IS the executed record).
**How to avoid:** restructure AROUND it (move/relabel sections, add the
dispatch-first lead-in), never edit its command blocks; diff check that the
smoke code fences are byte-identical pre/post.
**Warning signs:** any diff hunk inside the smoke section's ``` fences.

### Pitfall 3: Deleting static mode instead of co-documenting it
**What goes wrong:** MGPU-06 requires `--mode static` documented as
coexisting (merge/cleanup semantics are static-only); a dispatch-only rewrite
would orphan the merge/cleanup sections and violate D18-01.
**How to avoid:** two clearly-labeled mode tracks; static sections gain
explicit `--mode static` in their commands; dispatch sections own the shared
`--rerun-failed` story; a short "which mode when" lead table.

### Pitfall 4: Conflating task-subsetting with 5% subset datasets
**What goes wrong:** ONBOARDING.md:86 already uses "--tasks <name1,name2> to
validate a subset" — a DIFFERENT concept from VAL-02 subset DATASETS; naive
editing creates a doc that teaches the wrong thing.
**How to avoid:** name the distinction explicitly in every new subset
section ("task filter" vs "5% stratified subset datasets via
make_subset_datasets.py").

### Pitfall 5: Embedding unreviewed goldens without the badge
**What goes wrong:** committing copies of the WINDOWS #50 four presents
unreviewed goldens as ratified — violates the D-03 discipline and 18-UI-SPEC.
**How to avoid:** every figure whose source is in the #50 batch carries the
`◌ PENDING-REVIEW` badge in its caption (the UI-SPEC partial-state
resolution); verification greps captions.

### Pitfall 6: Scope creep into GIF recording or CI
**What goes wrong:** adding a multi-GPU demo scene (code + GPU run) or any CI
job for the report — both out of bounds (surgical-fix discipline; D18-08
zero CI).
**How to avoid:** TUI-DEMO section uses shipped-screen references + honest
queued-note; report regeneration documented as a manual command in the
footer stamp.

### Pitfall 7: Documentation language drift
**What goes wrong:** multi-gpu.md mixes an English static body with a
Chinese-heavy smoke section (existing convention); new sections written in
the wrong language for their file (README/docs body = English per Phase-12
i18n ruling; TUI-DEMO = bilingual tables; zh verbatim inside TUI figures).
**How to avoid:** match each file's existing dominant language; the report
body is English with zh verbatim in figures (18-UI-SPEC Auto-Default #2).

### Pitfall 8: Missing the TUI-GUIDE contradiction
**What goes wrong:** shipping DOCS-03 while TUI-GUIDE.md:193-204 still says
"the TUI composes single sweeps only" — the docs family self-contradicts.
**How to avoid:** one corrective task updates those lines to the Phase-16
reality (slot-4 multi-GPU launch, slot-5 G lanes/dispatch rows) with
cross-links to the new TUI-DEMO section.

## Code Examples

### Dispatch launch (executed reality — generalize, don't retype)
```bash
# Source: docs/multi-gpu.md:246-253 (the executed r2 smoke, verbatim today)
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
.venv/bin/python pipeline/run_sweep_shard.py --mode dispatch --workers 2 --gpus 0,1 \
    --models plant-dnabert-6mer --tasks iDNA_ABF_datasets__5mC --seeds 42,43 \
    --num_train_epochs 1 \
    --output-root "$(pwd)/pipeline/finetuned-smoke-r2" \
    --log_dir "$(pwd)/pipeline/finetuned-smoke-r2/logs"
```

### Subset generation (flag surface; executed rows for the expected-output block)
```bash
# Source flags: script/make_subset_datasets.py:140-175 (verified this session)
python script/make_subset_datasets.py \
    --dataset-root <REAL datasets root> \
    --output-root pipeline/datasets-smoke \
    --registry-dir pipeline/registry-smoke \
    --models plant-dnabert-6mer,plant-dnamamba-6mer \
    --tasks iDNA_ABF_datasets__5mC,GUE__emp_H3 \
    --fraction 0.05 --seed 42
# Executed output [VERIFIED: /root/autodl-tmp/phase15-evidence/subset-generation.log:1-3]:
#   ✅ iDNA_ABF_datasets__5mC: train 105 / dev 11 / test 117 rows (source 2110/234/2344)
#   ✅ GUE__emp_H3: train 598 / dev 74 / test 74 rows (source 11971/1497/1497)
#   ✅ 2 subset dataset(s) written under …/pipeline/datasets-smoke (fraction=0.05, seed=42); registry: …/pipeline/registry-smoke
```
(The executor pulls the FULL executed command line incl. exact argv spelling
from the 15-02-SUMMARY / subset-generation.log before publishing — the above
flag set is verified, the exact executed invocation should be pasted.)

### Terminal-state assertion + consumption dry-run (executed, multi-gpu.md:280-292)
```bash
.venv/bin/python -c "import json; s = json.load(open('pipeline/finetuned-smoke-r2/dispatch_state.json')); assert s['status'] == 'done', s['status']; assert s['counts']['completed'] == s['counts']['total'] == 2, s['counts']"
.venv/bin/python script/export_runs.py --dry-run --input-root pipeline/finetuned-smoke-r2
# → [Dry-run] 2 run record(s) across 1 model(s) / 1 task(s) under pipeline/finetuned-smoke-r2
```

### Report badge vocabulary (18-UI-SPEC — the report's core signal system)
`✓ PASS` (#2F7D0F) · `⚠ ENVIRONMENTAL-EXCLUDED` (#8C6300, reason mandatory) ·
`◌ PENDING-REVIEW` (#0E6EDC) · `✗ FAILED` (#A61D24, disposition mandatory) —
glyph + UPPERCASE word + color, never color-only; one legend row under the
summary table.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | TUI-DEMO multi-GPU section can follow the precedent shape (prose/tables/honest note) without new GIFs, deferring recording | T4 / OQ1 | If maintainer expects GIFs, a scene-driver task (code+GPU) must be added — confirm in plan review |
| A2 | TUI-GUIDE.md:193-204 correction is in scope under DOCS-03's "verified against shipped screens" | T4 / OQ2 | If ruled out-of-scope, docs family ships self-contradictory; cheap either way |
| A3 | 2236/6 may be cited from the recorded Phase-17 artifact if a fresh full-suite run is impractical (academic-proxy dependency) | T7 / OQ4 | Report shows a stale count if the suite grew since; fresh run preferred |
| A4 | The pty live capture is optional-with-fallback (MEDIUM-LOW feasibility; new conversion tooling required) | T9 | None — UI-SPEC honest-degradation path is pre-ratified |
| A5 | Report home = docs/v1.3-test-report.html + docs/report-assets/ (18-UI-SPEC Auto-Default #1; planner may pick baseline/) | T8 | None — either home satisfies D18-05; link placement adjusts |
| A6 | `--rerun-failed` full usage details (ledger feed, archive genealogy) beyond run_sweep_shard.py:462-469 flag help are in 14-CONTEXT/SUMMARYs and will be quoted at doc-write time | T6 | Minor doc-accuracy risk; executor reads 14 artifacts before writing |

All other claims in this research were verified this session against the
cited repo files/artifacts (in-repo provenance; no external sources were
consulted — no packages, no external APIs, no web claims).

## Open Questions

1. **TUI-DEMO: GIFs or prose section?**
   - What we know: precedent sections embed bilingual GIFs; the record.sh scene list has NO multi-GPU scene; recording needs new driver code + real dual-GPU run.
   - Recommendation: prose section in precedent shape + golden references + explicit "GIF re-record queued" note; recording deferred post-milestone.
2. **TUI-GUIDE.md:193-204 correction in scope?**
   - What we know: lines contradict shipped Phase-16 screens; D18-02/03 zero-stale spirit argues yes; requirement text names only TUI-DEMO/README/ONBOARDING.
   - Recommendation: include as a small DOCS-03 task (~10 lines edited); confirm at plan review.
3. **Report home: docs/ vs baseline/?**
   - 18-UI-SPEC recommends docs/v1.3-test-report.html + docs/report-assets/ (public family, README index link); D18-05 allows baseline/. Planner picks; docs/ recommended.
4. **Fresh full-suite run at report generation, or cite the recorded 2236/6?**
   - 17-VERIFICATION.md:121 notes the suite needs the machine's academic proxy for one lane. If runnable, run `make test` and paste fresh counts (with date); else cite the recorded artifact + its date. Either way the lane table states which.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Evidence pack /root/autodl-tmp/phase15-evidence/ | report GPU evidence | ✓ (41 files) | — | none needed |
| /root/autodl-tmp/phase17-preview/ PNGs | report figures | ✓ (6 PNGs + geo JSONs) | — | none needed |
| pytest suite (machine + academic proxy) | optional fresh lane counts | ✓ (ran during 13-17) | — | cite recorded 2236/6 (OQ4) |
| node --test | node lane count | ✓ (44/44 at 17-VERIFICATION) | — | cite recorded |
| asciinema + agg | GIF re-recording | not probed | — | not needed if Q1 = prose section |
| Static file server | report local preview | ✓ (start-server.sh pattern) | — | open file:// works for the report (relative assets, no modules) |

**Missing dependencies with no fallback:** none — the phase has no blocking
external dependency.

## Security Domain

`security_enforcement: true` (ASVS level 1, block on high) — but this phase
ships **no runtime code**:

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2/V3/V4 Auth/Session/Access | no | no runtime, no users, no inputs |
| V5 Input Validation | no inputs | the report is a static document; zero form controls (18-UI-SPEC) |
| V6 Cryptography | no | none used |
| Supply chain (adjacent) | yes (docs discipline) | zero-external-request structural gate: committed HTML contains no `<script src=`, no `@import`, no `url(http`, no external font links — enforced by grep task (18-UI-SPEC Registry Safety) |

Threat note: the only injection-adjacent surface is pasting evidence text
(log lines, JSON) into HTML — escape `<`/`&` when embedding dispatch_state
excerpts and log lines inside `<pre>`; task-level check.

## Sources

### Primary (HIGH confidence — all in-repo, read this session)
- `.planning/phases/18-docs-authoring/18-CONTEXT.md`, `18-UI-SPEC.md` — decisions + ratified report contract
- `docs/multi-gpu.md` (full read), `README.md` (targeted), `docs/ONBOARDING.md` / `GETTING-STARTED.md` / `TUI-DEMO.md` / `TUI-GUIDE.md` (grep + targeted reads)
- `pyproject.toml:5`, `uv.lock:562-563`, `tui/strings.py:1040-1058`, `tests/tui/test_pilot_nav_shell.py:892`
- `pipeline/run_sweep_shard.py:352-469`, `script/make_subset_datasets.py:1-40,140-175`
- `.planning/phases/1[3-7]-*/1[3-7]-VERIFICATION.md` (scores), `15-03-SUMMARY.md`, `17-VERIFICATION.md:69,121`
- `/root/autodl-tmp/phase15-evidence/` (listings + timing/log/state heads), `/root/autodl-tmp/phase17-preview/` (listing)
- `tests/tui/__snapshots__/` git status, `tests/tui/test_pty_driver.py:1-30`, `tests/tui/test_snapshots.py:19-23`
- `.planning/config.json:24,48-50` (nyquist_validation: false → Validation Architecture section omitted; security_enforcement: true)

No web/Context7 sources were consulted — the phase is entirely in-repo
documentation with zero external packages.

## Metadata

**Confidence breakdown:**
- Doc-target staleness map: HIGH — every claim read this session with line cites
- Evidence corpus: HIGH — paths and numbers verified against artifacts; the one mispairing (155 s × aff2faa3) caught and documented
- pty capture feasibility: MEDIUM — harness verified to exist; image-emission capability confirmed absent (new tooling required)
- TUI-DEMO/GIF decision: LOW-MEDIUM assumption (A1) — flagged for plan review

**Research date:** 2026-10-22
**Valid until:** 2026-11-05 (stable — docs-phase facts anchored to committed/evidenced state; goldens state may shift if maintainer reviews WINDOWS #50 first)
