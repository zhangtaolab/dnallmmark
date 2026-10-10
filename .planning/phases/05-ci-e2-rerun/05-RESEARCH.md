# Phase 5: CI & Three-Seed Full Re-Run (E2') - Research

**Researched:** 2026-10-10
**Domain:** Statistical aggregation upgrade + GitHub Actions CI + dataset N-audit/eval-subset tooling + E2' launch-readiness (code-only) + data-v2 migration gate
**Confidence:** HIGH (repo facts live-verified at HEAD; external CI facts MEDIUM, see Sources)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**CI golden tests (REV-06/F9)**
- **Q1:** Smoke = CANNED GOLDEN REPLAY: committed micro run_record + checkpoint artifacts; CI runs export→aggregate→schema full-chain assertions over them. No real training in CI (dnallm/GPU prohibited by CI feasibility constraint).
- **Q2:** The other three test classes (metric-key parity, species-table spot checks, aggregation units) reuse the existing pytest suite via a `ci` marker lane.
- **Q3:** Platform: GitHub Actions ubuntu runner, PR-required, README badge.
- **Q4:** Hard <15-minute budget (current suite ~8s + node ~8s — ample headroom for the chain replay).

**Aggregation upgrade (REV-04/F6)**
- **Q1:** CI intervals use the SAME SOURCE as the vendored `aggregate_seeds` (n<3 → t-interval 95%, n≥3 → bootstrap 2000, seed=42) — one statistical vocabulary everywhere.
- **Q2:** Difficulty weight v1 = uniform (1/num_tasks) z-score weighting — no hand-tuned difficulty table.
- **Q3:** Permutation tests: 10,000 shuffles, BH-corrected (FDR 0.05), pairwise model comparisons (scipy.stats or equivalent).
- **Q4:** Public leaderboard DEFAULT VIEW switches to z-score×difficulty-weighted; raw-rank stays one click away. (Public-facing number change — maintainer-accepted.)

**N audit + eval subsets (REV-07/F7)**
- **Q1:** Unified eval N = min(per-model current sample count) per task, integer — all models evaluate identical sample counts (fairness directly provable).
- **Q2:** N/non-ACGT frequency tables published as DATA.md appendix + downloadable CSV/JSON artifact (47 tasks × train/dev/test).
- **Q3:** Pipeline interface: run_finetune accepts `--subset_file` (JSON task→ID list); absent = full evaluation.

**data-v2 migration gate (DATA-01/02/03/06)**
- **Q1:** Same gate shape as data-v1: E2' completes → pre-generated categorized diff inventory → MAINTAINER SIGN-OFF → data-v2 tag + SHA256 manifest. Never auto-tagged.
- **Q2:** CHANGELOG.md with per-version sections: date + data_version + change-category counts + link to the diff inventory.
- **Q3:** Before/after comparison-JSON snapshots both archived (pre-E2' current + post-E2' new).

**E2' execution (pre-decided — ROADMAP carries the full framework)**
- Dual gate (DNALLM stable release + PIPE-02 env smoke on GB10) + EXPLICIT maintainer authorization; failure recovery = sweep failure-manifest re-run; window degradation = priority order (E2E pair → arena representatives → rest) with honest n_seeds; scope = ALL 62 unified-registry models.

### Claude's Discretion
None — all sixteen grey-area answers were maintainer-accepted recommendations.

### Deferred Ideas (OUT OF SCOPE)
- E2' LAUNCH itself — behind the dual gate + maintainer trigger (this phase lands its tooling and the pipeline readiness).
- IA³ lane — suite-support-gated, Phase 6 priority list.
</user_constraints>

<phase_requirements>
## Phase Requirements

Phase-5-mapped requirement IDs (ROADMAP traceability): TEST-04, TEST-05, TEST-07, DATA-01, DATA-02, DATA-03, DATA-06, REV-04, REV-06, REV-07, REV-09. The objective's eight named IDs map as follows (TEST-04/05/07 are subsumed into the CI work per ROADMAP SC-2: "subsumes TEST-04/05: lint + matrix + frontend checks + drift detection").

| ID | Description | Research Support |
|----|-------------|------------------|
| REV-04 (F6) | Aggregation upgrade — CI-overlap tie rules, raw-rank + z-score×difficulty-weight dual views, permutation tests (10k, BH-corrected); CpG case renders as tie | Current aggregation surface mapped (`calculate_dataset_stats`/`aggregate_models`); schema is closed (`additionalProperties: false`) so the dual-view fields require a same-commit schema extension; scipy 1.18.1 `permutation_test` + `false_discovery_control` verified importable in the pinned venv; CpG span 0.0021039 confirmed in committed data |
| REV-06 (F9) | CI golden tests — smoke incl. export, key parity, species spot checks, aggregation units; CPU, <15 min, PR-required | No `.github/` exists today (new workflow); repo has no package.json (node lane = `node --test` + npx-invoked static checks); marker-lane mechanics documented; budget analysis shows ~2-4 min wall-clock worst case |
| REV-07 (F7) | N-frequency audit (47 tasks × splits) + unified eval-subset ID lists accepted by the pipeline | On-disk state audited this session: 43/50 dataset dirs present (7 GUE dirs missing), test-row counts match registry exactly; suite `validate_sequences` row-drop semantics and its own "unified-subset prefiltering is a pipeline-side concern (dnallmmark)" note; `--subset_file` integration point identified (HF `select` on the loaded DatasetDict — no suite change needed) |
| REV-09 (E2') | Three-seed full re-run executes only after gates — THIS PHASE LANDS CODE/TOOLING ONLY | run_sweep gaps mapped (priority ordering, failure-manifest re-run flow); PIPE-02 env smoke script surface defined; data-v2 gate tooling inventory (compare.py `--summary-json`, freeze_snapshot primitive, SHA256 convention); THE DATA-CHAIN BRIDGE GAP found (see Open Question 1) |
| DATA-01 | Leaderboard recomputed with before/after artifact | `baseline/compare.py --summary-json` is the machine-readable diff contract; snapshot mechanics via tested-but-unwired `freeze_snapshot.py` |
| DATA-02 | CHANGELOG.md + data_version stamped into regenerated JSON | `tasks.json` already carries a free-string `version` field ("1.0.0") — but models_comparison schema has no version home (closed root map); stamp placement is a design decision |
| DATA-03 | Git tags data-v1 + data-v2 | `data-v1` tag exists; data-v2 = maintainer sign-off then tag + SHA256 manifest mirroring `baseline/data-v1.sha256` convention |
| DATA-06 | Leaderboard footer shows data-generation date/version stamp | `js/main.js:367` currently renders a LIVE CLOCK (`new Date().toLocaleDateString`) — must be replaced by the stamped version, not merely augmented |
</phase_requirements>

## Summary

Phase 5 is four code-only deliverables plus migration readiness. (1) The F6 aggregation upgrade changes `script/summarize_comparison.py` (tie rule inside per-task scoring; a new weighted-view aggregate field) and `dnallm-mark/js/main.js` (view toggle, weighted default) — and because `schemas/models_comparison.json` is fully closed (`additionalProperties: false` over a fixed 15-key performance block) and four committed goldens pin the current output byte-for-byte, the field addition, schema extension, regeneration, and golden re-chain must land as ONE migration commit in the Phase-1/Phase-4 discipline (compare.py inventory → commit). (2) CI is greenfield (no `.github/` exists): one workflow, SHA-pinned actions, uv-managed Python, plain `node --test` plus npx-invoked ESLint 10 / html-validate 11 static checks, a committed canned-replay fixture (micro run_record tree incl. `trainer_state.json`, since the exporter's parametersBlock join reads `global_step` from it), and a drift job (`make data` + `git diff --exit-code`) that only goes green after the F6 regeneration is committed. (3) The N audit is a new stdlib/numpy script reading on-disk CSVs — 43 of 50 registry tasks have data on disk (7 GUE dirs are missing pending the documented E2E-gate re-extraction), all present test-row counts match the registry exactly, and the DNALLM suite itself anticipates the unified-subset feature in its `validate_sequences` docstring. `--subset_file` integrates cleanly after `DNADataset.load_local_data` via the wrapped HF Dataset's `.select(ids)` — zero suite modification (the suite repo is strictly read-only). (4) E2' readiness = priority ordering + failure-manifest re-run in `run_sweep.py` (mostly free: the seed-scoped resume marker already re-attempts exactly the failed cells), a never-executed env-smoke script, CHANGELOG skeleton, and the data-v2 gate tooling.

**The single most important finding:** the E2' data chain has a **bridge gap**. `export_runs.py` produces task-centric `task_performance/` files from run records, but `summarize_comparison.py` — the only producer of `models_comparison*.json` — still reads the model-centric `model_performance/{alias}_performance.json` directory, and nobody regenerates those per-model files from run records. The submit page and the finetuning page both consume the per-model contract. The planner must decide the bridge (Open Question 1) before any E2' chain code is written.

**Secondary critical finding:** the CONTEXT F6-Q1 parenthetical ("n<3 → t-interval 95%, n≥3 → bootstrap 2000") does not match the vendored `aggregate_seeds` it defers to. The vendored semantics are `n<3 → ci95 null, method "none"`; `3 <= n < 10 → t-interval`; `n >= 10 → bootstrap`. The BINDING decision is "SAME SOURCE as the vendored aggregate_seeds" — so E2' 3-seed data gets **t-intervals (df=2)**, never bootstrap. Implement by calling the vendored function/constants, never by re-implementing the parenthetical.

**Primary recommendation:** land in waves — (W1) CI skeleton + canned golden replay + marker lane (pure addition, no data movement); (W2) F6 aggregation upgrade + schema/goldens/data single-commit migration + frontend view toggle; (W3) N audit + subset_file + DATA.md appendix; (W4) E2' readiness tooling (priority ordering, failure re-run, env smoke, CHANGELOG, snapshot/migration scripts) + the data-chain bridge decision. E2' launch itself stays behind the maintainer dual gate throughout.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Tie rule + dual-view aggregation math | Offline data scripts (`script/summarize_comparison.py`) | — | All normalization/ranking already lives there; CPU-only, testable |
| CI intervals for tie rule | Offline (`script/export_runs.py` vendored `aggregate_seeds`) | — | Decision Q1: ONE statistical vocabulary — call the vendored function, do not fork it |
| Permutation tests | Offline data scripts (new module or summarize extension) | CI asserts canned outputs | scipy CPU-only; 10k shuffles × pairs is minutes-scale, run at regeneration not page-render |
| View toggle / weighted default | Browser (`js/main.js` + `js/config.js`) | Static data (new fields in models_comparison*.json) | Rendering concern; the weighted score is precomputed offline, never recomputed client-side (dead `recalculateComparison` lesson, DATA-07) |
| CI golden replay | GitHub Actions runner | pytest fixtures | Committed micro run_record tree; export→aggregate→schema assertions |
| Drift detection | GitHub Actions runner | Makefile `make data` | Regenerate + `git diff --exit-code` over `dnallm-mark/data/` |
| N audit + subset generation | Offline data scripts (new) | Pipeline registries (`datasets_info.json`) | Reads on-disk CSVs; writes DATA.md appendix + CSV/JSON artifact + subset ID lists |
| Subset application at eval | GPU pipeline (`run_finetune.py --subset_file`) | — | After `DNADataset.load_local_data`, HF `.select()` on the test split; code lands this phase, executes only at E2' |
| E2' sweep ordering/failure re-run | GPU pipeline (`run_sweep.py`) | — | Priority tiers + failures-manifest filter; tested via fake executor (D-05 discipline) |
| data-v2 migration gate | Offline + git | Maintainer sign-off | compare.py inventory → sign-off → tag + SHA256 manifest; never automated |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| scipy | 1.18.1 (pinned via uv.lock; floor `>=1.15.2` in `[data]`) | `stats.permutation_test` (10k shuffles), `stats.false_discovery_control` (BH), `stats.t.ppf` (already used by vendored stats) | Already a data-group dependency (D-15); both APIs verified importable in the repo venv this session |
| pytest | 9.1.1 | `ci` marker lane + new golden-replay tests | Existing harness; markers already registered in pyproject |
| uv | 0.13.0 (local); setup-uv action v8.x in CI | Environment sync from uv.lock | Existing repo convention (`UV ?= uv`, `uv run --group …` in Makefile) |
| Node.js | v26.10.0 local; ≥18 in CI | `node --test tests/js/`, `node --check`, tasks.json generator | Zero-dep node:test lane already exists |

### Supporting (CI-only, npx-invoked — NEVER installed into the repo)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| eslint | 10.12.0 via `npx --yes eslint@10.12.0` | Frontend static checks (TEST-05) | CI + optional local; flat config `eslint.config.mjs` (no package.json needed) |
| html-validate | 11.16.2 via `npx --yes html-validate@11.16.2` | HTML validation of the 6 real shells | CI-only; skip dev mockups (`task-mockup.html`, `test.html`, `verify-chart.html`) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| eslint via npx | A dev-only package.json + npm ci | Violates the repo's no-npm state and adds a lockfile surface; npx with exact-version pins keeps the repo manifest-free [ASSUMED: exact-pin npx is the maintainer-acceptable form — confirm at planning] |
| scipy BH (`false_discovery_control`) | statsmodels multipletests | statsmodels is a new dependency for one function scipy already provides; rejected |
| GitHub-hosted ubuntu runner | Self-hosted aarch64 | GB10 stays pipeline-only; CI scope is CPU stdlib/numpy/pandas by hard constraint |

**Installation:** None. This phase installs NO new packages into any group. CI pulls pinned tools at run time (uv from setup-uv; node from setup-node; eslint/html-validate via exact-version npx). Any pyproject/uv.lock edit therefore requires the same-commit `uv lock` + `requirements.txt` re-export discipline — expected to be unnecessary here.

**Version verification (run this session):** `npm view eslint version` → 10.12.0; `npm view html-validate version` → 11.16.2; neither has a postinstall script. scipy/pytest/ruff/ty/pytest versions confirmed from the live `.venv` (scipy 1.18.1, pytest 9.1.1, ruff 0.16.10, ty 0.0.85).

## Package Legitimacy Audit

> Gate run via `gsd-tools query package-legitimacy check --ecosystem npm eslint html-validate`. No Python packages are added this phase.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| eslint | npm | latest release 2026-10-02 (project since 2013) | 161.6M/wk | github.com/eslint/eslint | SUS ("too-new" latest release) | Approved with warning — canonical tool, huge download base, no postinstall; pin exact version `eslint@10.12.0` |
| html-validate | npm | latest release 2026-10-04 (project since 2018) | 512K/wk | gitlab.com/html-validate/html-validate | SUS ("too-new" latest release) | Approved with warning — pin exact version `html-validate@11.16.2` |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** eslint, html-validate — both flagged ONLY because their latest releases are days old (the heuristic fires on publish recency, not project legitimacy). `eslint` [WARNING: flagged as suspicious — verify before using.] `html-validate` [WARNING: flagged as suspicious — verify before using.] Planner: pin exact versions (above) and add a `checkpoint:human-verify` before the CI job that first npx-fetches them; exact-version npx pins make later releases inert.

## Architecture Patterns

### System Architecture Diagram

```
                       ┌─────────────────────────── CI (new, .github/workflows/ci.yml) ───────────────────────────┐
                       │  PR + push → ubuntu runner (SHA-pinned actions)                                          │
                       │                                                                                         │
  repo + uv.lock ──────┼─► setup-uv ─► uv sync --group dev ─► ruff (make lint) ─► ty (make typecheck)            │
                       │                                        └► pytest  (full suite, ~8s; `ci` marker lane)  │
                       │                                        └► GOLDEN REPLAY: committed micro run_record tree │
                       │                                              → export_runs → aggregate → jsonschema      │
  node (setup-node) ───┼─► node --test tests/js/ ─► node --check per JS file ─► npx eslint@10.12.0 ─► npx html-validate │
                       │                                                                                         │
  repo tree ───────────┼─► DRIFT: make data → git diff --exit-code -- dnallm-mark/data/  (green only AFTER the     │
                       │        F6 regeneration commit lands)                                                   │
                       └─────────────────────────────────────────────────────────────────────────────────────────┘

  OFFLINE regeneration (maintainer, CPU):

  model_performance/*.json (42 committed) ──► summarize_comparison.py ──► models_comparison{,_animal,_plant,_microbe}.json
   (F6: + tie rule, + weighted-view fields)      │                                (schema-extended, goldens re-chained,
                                                 │                                 DEFAULT VIEW = weighted)
                                                 └─► permutation tests (10k, BH) ──► reported artifact

  E2' CHAIN (code lands now; execution behind maintainer dual gate):

  run_sweep.py (priority tiers + failures re-run) ──► {model}/{task}/seed_{n}/ run_record.json
                                                            │
                              export_runs.py (vendored aggregate_seeds: n=3 → t-interval) 
                                                            │
                                     task_performance/*.json + seed_stats/*.json
                                                            │
                                     ??? BRIDGE GAP ???  ──────────────► summarize_comparison.py
                                     (Open Question 1)                    └─► models_comparison* → migration gate
                                                                              (compare.py inventory → sign-off
                                                                               → data-v2 tag + SHA256 manifest)

  N AUDIT (offline, reads pipeline/datasets/ CSVs):
  datasets_info.json + on-disk CSVs ──► audit script ──► DATA.md appendix + CSV/JSON artifact
                                        └─► subset ID lists (JSON task→IDs) ──► run_finetune.py --subset_file (E2')
```

### Recommended Project Structure (additions only)

```
.github/
└── workflows/
    └── ci.yml                    # the single workflow: lint+typecheck, pytest+replay, node lane, drift job
CHANGELOG.md                      # per-version sections: date + data_version + category counts + inventory link
DATA.md                           # exists? NO — new file; N/non-ACGT appendix lands here (DATA-04 provenance table is Phase 6)
eslint.config.mjs                 # flat config; .mjs avoids the no-package.json ESM ambiguity; browser globals inlined
.htmlvalidate.json                # html-validate config; scope to the 6 real shells
script/
├── audit_n_frequencies.py        # NEW: N/non-ACGT census + subset-ID-list generation (new)
├── run_migration_inventory.py    # NEW or extension: pre-generated categorized diff inventory for the data-v2 gate
│                                 #   (candidate: extend baseline/compare.py usage instead — see Open Question 6)
pipeline/
├── run_sweep.py                  # EDIT: priority ordering + failures-manifest re-run filter
├── run_finetune.py               # EDIT: --subset_file (select on test split after DNADataset.load_local_data)
└── env_smoke.py                  # NEW: PIPE-02 dual-gate smoke (torch/dnallm import + CUDA visible + version pins; NEVER run by agents)
tests/
├── fixtures/
│   └── e2_replay/                # NEW: committed micro run_record tree (2-3 models × 1-2 tasks × 3 seeds,
│                                 #     incl. trainer_state.json + final_metrics.json + run_record.json + config slice)
├── test_ci_replay.py             # NEW: export→aggregate→schema chain assertions over the committed fixture
└── test_audit_n.py               # NEW: N-audit unit tests over synthetic CSV fixtures
```

### Pattern 1: CI statistical vocabulary — call the vendored function, never re-implement
**What:** The tie rule needs per-model-per-task 95% CIs. The only sanctioned source is the vendored `aggregate_seeds` in `script/export_runs.py`.
**When to use:** Everywhere a CI appears (tie rule, reviewer stats). One vocabulary.
**Example — the vendored n-guards [VERIFIED: script/export_runs.py:122-130, verbatim]:**
```python
SMALL_N_CI_CHOICES = ("t-interval", "omit")
CI_MIN_SEEDS = 3
BOOTSTRAP_MIN_SEEDS = 10
```
and the branch semantics [VERIFIED: script/export_runs.py:183-207, condensed]: `n < CI_MIN_SEEDS` → `out["ci95"] = None; out["method"] = "none"`; `n < BOOTSTRAP_MIN_SEEDS and small_n_ci == "t-interval"` → Student-t interval via `stats.t.ppf(0.975, n - 1)`; `n >= BOOTSTRAP_MIN_SEEDS` → seeded percentile bootstrap. **E2' has n=3 seeds → t-interval (df=2), NOT bootstrap.** The CONTEXT Q1 parenthetical ("n<3 → t-interval, n≥3 → bootstrap") contradicts this — the vendored code is the decision's named source and wins; importing `aggregate_seeds` (and its constants) from `export_runs` keeps it provably one vocabulary (`tests/test_vendored_stats.py` already pins the semantics).

### Pattern 2: Tie rule inside the existing per-task scoring
**What:** CI-overlap ⇒ tied rank applies at per-task ranking in `calculate_dataset_stats` / the aggregation that consumes it.
**When to use:** When per-model per-task CIs exist (E2' 3-seed data; canned replay fixtures now).
**Current seam [VERIFIED: script/summarize_comparison.py:192-195, verbatim]:**
```python
ranks = pd.Series(scores).rank(ascending=False, method='min').values
# Convert ranks to competitive points: rank 1 earns N-1, last earns 0.
task_rank_scores = N - ranks
```
`method='min'` already makes EXACT ties share rank; the CI-overlap rule widens "tie" from exact-equality to interval overlap. Design notes for the planner: (a) with n=3 t-intervals on near-saturated metrics (the CpG case: top-10 span 0.0021), the rule will tie large groups — the CpG assertion is an E2'-outcome testable now with a canned 3-seed fixture replicating those AUPRC values; (b) pre-E2' committed data is single-run (no CI source) — the rule lands as code + fixture-tested and is vacuous on the pre-E2' regeneration unless the planner gates it on CI presence; (c) overlapping-CI rank assignment should use competition-style min-rank over tie-groups (the `method='min'` convention) so `task_rank_score = N - rank` stays coherent.

### Pattern 3: Weighted dual view — precomputed offline, selected client-side
**What:** New per-model aggregate field(s) for the z-score×uniform-difficulty view; `js/main.js` gains a view toggle with weighted as DEFAULT.
**Current consumer surfaces [VERIFIED: js/main.js:14-15 (`currentSort: 'rank_score'` default), :236 (`y: model.performance?.rank_score || 0` scatter axis), :388 (`data-sort="rank_score"` column), js/config.js:27-31 (FILTER_OPTIONS button pattern)]:**
The toggle follows the existing FILTER_OPTIONS/x-scale-toggle idiom: `this.state.currentView` ('weighted' | 'rank'), buttons in `leaderboard-controls`, on switch → re-sort (`filterAndSortModels` with a view-derived sort field) → `renderScatterChart` (y-axis reads the active view's field) → `renderLeaderboard`. Uniform difficulty weight = `1/num_tasks` per task (CONTEXT Q2): weighted = `Σ_tasks z_task / N_tasks_in_view`; models absent from a task contribute nothing (same no-imputation convention as `rank_score` today [VERIFIED: summarize_comparison.py:291-294 comment "Tasks where the model did not run are implicitly zero"]). SCHEMA: `schemas/models_comparison.json` performance block is `additionalProperties: false` with a fixed 15-key required set [VERIFIED: schemas/models_comparison.json:35-54] — new fields require extending required+properties in the SAME commit as the data and the re-chained goldens (Phase-2 SC-6 discipline; goldens are chain-produced, never hand-edited [VERIFIED: tests/test_golden.py:17 "goldens are never hand-edited to match chain output"]).

### Pattern 4: Canned golden replay fixture (REV-06 Q1)
**What:** A COMMITTED micro run-record tree replayed through export→aggregate→schema in CI.
**Model:** `tests/test_export_runs.py` already builds ephemeral trees via `_write_run_record` / `_build_fixture_tree` [VERIFIED: tests/test_export_runs.py:89,196-228] — the replay fixture is the same shape, but committed under `tests/fixtures/e2_replay/` with: `run_record.json` (status completed; metrics with `total_flos` — its absence is a hard error [VERIFIED: export_runs.py:478-484]), `trainer_state.json` (the D-12 parametersBlock join reads `global_step` from it [VERIFIED: export_runs.py:540-543]), `final_metrics.json`, a `finetune_config.yaml` slice (the join source [VERIFIED: export_runs.py:585-598]), and registry slices. CI assertions: exporter output validates against `schemas/task_performance.json`; `seed_stats` carry n_seeds=3 t-intervals; byte-stability across two runs; downstream aggregation over the exported files produces the tie behavior (a deliberately-overlapping fixture pair ties). 3 seeds × 2-3 models × 1-2 tasks keeps the whole chain well under a second of compute.

### Pattern 5: `--subset_file` via HF `select` — no suite modification
**What:** `run_finetune.py` accepts a JSON `{task_name: [row IDs]}` and restricts the TEST split to those rows.
**Integration point [VERIFIED: pipeline/run_finetune.py:795-801 — the `DNADataset.load_local_data(data_dict, …)` call builds `data_dict` with train/dev/test CSV paths at :667-676]**: after `load_local_data`, the wrapped object is a HF `DatasetDict` at `dataset.dataset` [VERIFIED: /home/forrest/Github/DNALLM/dnallm/datahandling/data.py:50-97 — `self.dataset = ds`; `load_local_data` with a dict returns a `DatasetDict`]. Apply `dataset.dataset["test"] = dataset.dataset["test"].select(ids)` (HF datasets `select` — the same primitive the suite's own `sampling()` uses [VERIFIED: data.py:1108-1145]). The suite anticipates this feature: its `validate_sequences` docstring says "unified-subset prefiltering is a pipeline-side concern (dnallmmark), not a dnallm API" [VERIFIED: data.py:859-910]. Apply the subset BEFORE `validate_sequences` so the audited IDs are the actually-evaluated rows. Absent flag = full evaluation (exact current behavior).
**Design constraints:** (a) IDs must be CSV row indices (stable given committed CSV order — no re-sorting upstream); (b) the audit-generated subsets must be the rows that pass ALL models' filters — strict-charset models (`models_no_char_n`, "ACGTacgt|") drop whole rows containing N [VERIFIED: data.py:875-880 "a single out-of-charset character discards the entire row" + the cross-model warning], and `validate_sequences(minl=0, maxl=10010, …)` [VERIFIED: run_finetune.py:837-839] also drops over-length rows — so the common-subset computation must mirror `check_sequence` semantics (charset `ACGTacgt|`, maxl 10010) or the "identical sample counts" guarantee silently breaks; (c) document whether train/dev are also subset (decision says EVAL subsets — test only; dev stays full for checkpoint selection).

### Pattern 6: E2' sweep readiness — priority tiers + failure re-run
**What:** `run_sweep.py` gains deterministic priority ordering and a failures-manifest re-run path.
**Current ordering [VERIFIED: pipeline/run_sweep.py:439 `for model, task, seed in sorted(cells)`]** — plain lexicographic. Priority mechanism (recommended): a `--priority-file` JSON of ordered tiers, each a list of `(model, task)` specs or bare model names; `enumerate_matrix` composes `cells.sort(key=priority_rank)` with the existing sorted() order as the stable fallback (deterministic when the file is absent — backward compatible). Tier 1 per the pre-decided order = the PIPE-03 E2E pair all-seeds: `plant-dnamamba-6mer` + `PlantHelixSeek` on `PlantCAD2__cross_species_leaf_on_off_translation` [VERIFIED: REQUIREMENTS.md:72]. Tier 2 "arena representatives" is UNDEFINED in any repo artifact — the priority file is maintainer-curated (see Open Question 4). Honest n_seeds is already structural: the exporter discloses `n_seeds` per metric and `aggregate_seeds` never emits a vacuous CI below 3 seeds.
**Failure-manifest re-run is nearly free:** `sweep_failures.json` is written on EVERY run (empty when clean — WR-06) [VERIFIED: run_sweep.py:533-538], and a failed cell has NO `trainer_state.json` (the marker is copied only on success, WR-13 ordering [VERIFIED: run_finetune.py:899-910]) — so simply re-running the same sweep command already re-attempts exactly the failed cells (completed cells are `skipped`). A `--from-failures <path>` filter (enumerate only cells present in a failures manifest) is a thin, fake-executor-testable addition that avoids re-enumerating 9,300 cells (62×50×3) and guards against typo'd manual `--models/--tasks` re-runs.

### Pattern 7: data-v2 migration gate (mirror data-v1)
**What:** E2' completes → pre-generated categorized diff inventory → maintainer sign-off → tag + SHA256 manifest.
**Reusable, verified pieces:** `baseline/compare.py --summary-json` emits the complete untruncated machine-readable diff inventory (`{committed, regen, total, counts, diffs}` with `len(diffs) == total == sum(counts.values())`) [VERIFIED: baseline/compare.py:34-42]; `baseline/data-v1.sha256` fixes the manifest line convention (`<sha256>  <path>`, two spaces) [VERIFIED: freeze_snapshot.py:6-10]; `script/freeze_snapshot.py` is the TESTED but UNWIRED snapshot primitive (tar + SHA256 + commit hash; Phase 6 owns invocation policy) [VERIFIED: freeze_snapshot.py:11-15]; the `data-v1` tag exists (git tag -l → `data-v1`) [VERIFIED this session]. Before/after snapshots (CONTEXT Q3): freeze the current committed comparison files pre-E2' (cheap, can land this phase as an archived snapshot under `baseline/snapshots/` — confirm location with maintainer), then the post-E2' set after regeneration. CHANGELOG.md sections: `## [data-v2] - <date>` + data_version + change-category counts (reusing compare.py's diff-class vocabulary: FLOAT_BIG/INT/VALUE/MISSING_IN_REGEN/EXTRA_IN_REGEN/…) + link to the inventory artifact.

### Pattern 8: PIPE-02 env smoke as a checkable gate
**What:** A small script the MAINTAINER runs on the GB10 machine as the second half of the E2' dual gate; agents write it, never run it.
**Concrete surface (all checkable, exit-code contract):** import torch and assert the pinned `torch.__version__` matches the `[gpu]` group pin (`torch==2.11.0`, `transformers==5.17.0` [VERIFIED: pyproject.toml:33-36]); `import dnallm` resolves (installed from the local dev clone per PIPE-02); `torch.cuda.is_available()` and `torch.cuda.device_count() >= 1` with device name/memory printed; optional single-tensor matmul to prove executability. Print PASS/FAIL lines and exit nonzero on any failure. It runs only on the GPU box, so the ty `replace-imports-with-any` config [VERIFIED: pyproject.toml:64] keeps the CPU-side typecheck green; ruff scope must include it.

### Anti-Patterns to Avoid
- **Re-implementing the CI/t-interval math for the tie rule:** forks the statistical vocabulary the decision explicitly unifies; import `aggregate_seeds` instead.
- **Computing the weighted view client-side:** the dead `recalculateComparison()` in `js/data.js` is the cautionary tale (DATA-07, Phase 6 removes it) — precompute offline, render only.
- **Editing goldens by hand to match new output:** goldens are chain-produced [VERIFIED: tests/test_golden.py:17]; regenerate via the chain in the migration commit.
- **Shipping the CI drift job before the F6 regeneration commit:** `make data` must be a byte-identical no-op on the committed tree or the drift job reds forever; sequence the migration commit before enabling the job (or before merging the workflow).
- **Subsetting only the eval split while the audit counts filtered rows differently:** the audit's common-subset semantics MUST mirror `check_sequence` (charset + maxl) or per-model counts diverge again.
- **Auto-tagging data-v2:** the gate is maintainer sign-off by decision; scripts may PREPARE the tag (inventory + manifest) but never create it.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Permutation test engine | Custom shuffle/p-value loop | `scipy.stats.permutation_test` | Exact-test edge cases, `permutation_type` semantics, vectorization; verified importable at scipy 1.18.1 |
| BH/FDR correction | Manual Benjamini-Hochberg procedure | `scipy.stats.false_discovery_control(ps, method="bh")` | Off-by-one p-value ordering bugs; method audited upstream |
| CI intervals (tie rule source) | New t/bootstrap code | Vendored `aggregate_seeds` import | Decision Q1; semantics already parity-tested vs the suite |
| JSON diff vocabulary | New comparator | `baseline/compare.py` (+ INT/BOOL_CROSS labels) | Already the migration-gate contract; extending beats replacing |
| SHA256 manifest format | New format | `baseline/data-v1.sha256` line convention (+ `freeze_snapshot`) | Tamper-evidence continuity across data versions |
| HF dataset row selection | Custom CSV rewriting | `datasets.Dataset.select(ids)` | Keeps arrow-format semantics identical to the suite's own `sampling()` |
| Actions version pinning | `@v4`-style mutable tags | full 40-char SHA + `# vX.Y.Z` comment | tj-actions CVE-2025-30066 tag-rewrite class of attack [CITED: starsling.dev/best-practices/github-actions/pin-action-shas.md] |

**Key insight:** this phase's risk is statistical-vocabulary drift and data-contract drift, not missing tooling — nearly every primitive (CI math, comparator, snapshot, manifest, selection) already exists in-repo or in scipy; the work is wiring, schemas, and gates.

## Runtime State Inventory

> Included because this is a data-migration phase (data-v1 → F6 regeneration → data-v2). Canonical question: after all code lands, what state still carries the old form?

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data (committed derived JSON) | 4 `models_comparison*.json` (42 models each), 47 `task_performance/*.json`, `tasks.json` (version "1.0.0", count 47), 42 `model_performance/*.json` — verified counts this session | F6 regeneration moves comparison values/fields (one migration commit, inventoried via compare.py); task files move only at E2' |
| Stored data (goldens) | `tests/fixtures/golden/` — 4 comparison goldens + tasks.json golden | Re-chain in the F6 migration commit (chain-produced, never hand-edited) |
| Live service config | None — static site, no backend | None — verified by architecture (CLAUDE.md hosting model) |
| OS-registered state | None | None — no schedulers/daemons introduced |
| Secrets/env vars | None new; Zenodo preview link settled (REL-05) | None |
| Build artifacts | `.venv`, `uv.lock`, `requirements.txt` (re-exported after D-15); no new deps this phase expected | None unless deps change — then same-commit `uv lock` + re-export |
| Git tags | `data-v1` exists [VERIFIED: `git tag -l`] | `data-v2` created only at the maintainer gate after E2' |
| Datasets on disk (E2' blockers) | 43/50 registry task dirs present with ALL splits; test-row counts match registry EXACTLY (0 mismatches); 7 GUE dirs missing (`GUE__EPI_GM12878`, `GUE__fungi_species_20`, `GUE__human_tf_0`, `GUE__mouse_1`, `GUE__mouse_4`, `GUE__virus_covid`, `GUE__virus_species_40`) [VERIFIED: on-disk audit this session] | Re-extract + flatten the 7 GUE archives (the documented E2E-gate double-nesting quirk) BEFORE E2' and before the N audit covers them; audit script must skip-with-warning meanwhile |
| Model-registry vs committed results | 42 committed `model_performance` files; 21 of 62 registry models have no committed results (first-time runs at E2'); **`plant-dnamamba2-BPE` has a committed result file but is NOT in the 62-key registry** [VERIFIED: set-diff this session] | Decide its fate at the bridge design (Open Question 1): register it, or it drops out of the E2'-chain leaderboard |

## Common Pitfalls

### Pitfall 1: The CONTEXT CI-paraphrase vs the vendored n-guards
**What goes wrong:** Implementing "n<3 → t-interval, n≥3 → bootstrap" literally produces intervals the vendored stats never emit, and the CpG tie test built on wrong intervals.
**Why it happens:** The CONTEXT Q1 parenthetical mis-paraphrases `aggregate_seeds` (actual: n<3 → none; 3≤n<10 → t; n≥10 → bootstrap).
**How to avoid:** Import and call `aggregate_seeds`; write the CpG fixture test against the function's actual output for n=3 (t, df=2).
**Warning signs:** A tie-rule test that passes with fabricated intervals; any bootstrap call path reachable at n=3.

### Pitfall 2: Schema/goldens/data three-way skew
**What goes wrong:** New performance fields land in code but the closed schema rejects the regenerated files (or CI schema-validation reds), or goldens red, or the data tree is committed without the field.
**Why it happens:** `schemas/models_comparison.json` is `additionalProperties: false` with 15 required keys; goldens are byte-value-pinned; TEST-06 validates every committed JSON in the suite.
**How to avoid:** One migration commit: code + schema extension + regenerated 4 comparisons + re-chained goldens (and schema self-check tests updated per Phase-2 SC-6 same-commit discipline).
**Warning signs:** `make test` failures isolated to test_golden/test_schemas after a summarize edit.

### Pitfall 3: Drift job reds on merge
**What goes wrong:** TEST-07 (`make data && git diff --exit-code`) fails on the F6 merge because the committed tree wasn't regenerated with the new aggregation.
**How to avoid:** Sequence: F6 migration commit (data moves) → then the workflow file (or at least the drift job) merges. The pre-F6 state is a verified no-op (Phase 4 verifier ran `make data` → 0 dirty lines).
**Warning signs:** CI red only on the drift job immediately after an aggregation change.

### Pitfall 4: Subset IDs that don't survive the filters
**What goes wrong:** Audited "identical N" per task still yields different per-model evaluated counts because `validate_sequences` drops N-containing rows for strict-charset models and >10010bp rows for everyone.
**How to avoid:** The audit's common-subset computation mirrors `check_sequence` semantics exactly (charset `ACGTacgt|` + `|` pair separator, minl 0, maxl 10010); assert per-task that the emitted ID list contains only rows passing the common filter.
**Warning signs:** A task where subset size < N because filtered rows were sampled first.

### Pitfall 5: npx supply-chain drift in CI
**What goes wrong:** `npx --yes eslint` (no version) pulls a different major mid-milestone; or a compromised fresh release is auto-pulled (both tools flagged SUS solely for days-old releases).
**How to avoid:** Exact-version pins (`eslint@10.12.0`, `html-validate@11.16.2`) + the checkpoint:human-verify before first CI run; Dependabot-style review when bumping.
**Warning signs:** CI static-check behavior changing without a repo change.

### Pitfall 6: TEST-04's stale "3.12/3.13" matrix text
**What goes wrong:** A 3.12 CI job fails instantly — `requires-python = ">=3.13"` [VERIFIED: pyproject.toml:7] refuses the environment.
**Why it happens:** TEST-04 was written before the D-07 Python-floor decision.
**How to avoid:** Matrix = 3.13 (the floor, matching `.python-version` 3.13 and `[tool.ty.environment] python-version = "3.13"`); optionally add 3.14 as a forward-compat probe. Record the deviation from TEST-04's literal text.
**Warning signs:** `uv sync` error "requires-python" in a 3.12 job.

### Pitfall 7: Permutation-test cost blowup
**What goes wrong:** 10,000 shuffles × 861 model pairs (42 models) × 47 tasks ≈ 400M statistic evaluations if implemented naively per-task-per-pair.
**How to avoid:** Use `vectorized=True` + `batch` in `permutation_test`; restrict the pairwise family to ONE axis (per-task averaged score or the aggregate view) and disclose the family size with the BH correction; run offline at regeneration, never in page render. Decide the axis explicitly (Open Question 5).
**Warning signs:** Regeneration taking hours; CI replay timing out (keep the canned fixture tiny — 2-3 models).

### Pitfall 8: The 7 missing GUE datasets discovered late
**What goes wrong:** E2' launch or the N audit hits missing dataset dirs mid-run (the pipeline skips with a log line — silent coverage loss).
**How to avoid:** The env-smoke/launch-readiness checklist verifies all 50 registry Dataset_paths exist on disk (and the double-nesting is flattened) before the maintainer pulls the trigger; the N audit reports missing dirs explicitly.
**Warning signs:** `Dataset dir not found … skipping` lines in pipeline logs; N-audit rows with empty counts.

## Code Examples

### Permutation test + BH (verified against the pinned scipy 1.18.1 this session)
```python
# [VERIFIED: .venv live probe, scipy 1.18.1] signatures as inspected:
# scipy.stats.permutation_test(data, statistic, *, permutation_type='independent',
#     vectorized=None, n_resamples=9999, batch=None, alternative='two-sided',
#     axis=0, rng=None, random_state=None)
# scipy.stats.false_discovery_control(ps, *, axis=0, method='bh')  # 'bh' is Benjamini-Hochberg
from scipy import stats

def mean_diff(x, y, axis=-1):
    return x.mean(axis=axis) - y.mean(axis=axis)

res = stats.permutation_test(
    (model_a_scores, model_b_scores), mean_diff,
    permutation_type="samples",      # swap score vectors between the two models
    n_resamples=10_000,              # CONTEXT Q3: 10,000 shuffles
    vectorized=True, batch=100, alternative="two-sided",
    rng=42,                          # or random_state=42 — seed for reproducible p-values
)
adjusted = stats.false_discovery_control(p_values, method="bh")  # FDR 0.05 threshold
```

### Subset application in run_finetune.py (integration point)
```python
# after: dataset = DNADataset.load_local_data(data_dict, ...)   [VERIFIED: run_finetune.py:795-801]
# before: dataset.validate_sequences(...)                        [VERIFIED: run_finetune.py:837-839]
if subset_ids is not None and "test" in dataset.dataset:
    dataset.dataset["test"] = dataset.dataset["test"].select(subset_ids)
```

### pytest marker registration + lane selection
```toml
# pyproject.toml [tool.pytest.ini_options] — extend the existing markers list
# [VERIFIED: pyproject.toml:78-80 currently registers only "slow"]
markers = [
    "slow: long-running real-tree regression tests; excluded by make test-fast",
    "ci: pinned CI lane — metric-key parity, species spot checks, aggregation units, golden replay",
]
```
```bash
uv run --group dev pytest -m ci          # the pinned lane
uv run --group dev pytest -m "not slow"  # everything except the ~80s real-tree lane (budget allows full suite in CI: ~8s)
```

### Workflow badge (README)
```markdown
<!-- [CITED: docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/adding-a-workflow-status-badge] -->
[![CI](https://github.com/zhangtaolab/dnallmmark/actions/workflows/ci.yml/badge.svg)](https://github.com/zhangtaolab/dnallmmark/actions/workflows/ci.yml)
```
Repo slug `zhangtaolab/dnallmmark` [VERIFIED: `$id` fields in schemas/*.json, e.g. schemas/tasks_index.json].

### Workflow skeleton (SHA-pinning posture)
```yaml
# .github/workflows/ci.yml — actions pinned by full SHA with version comments
# [CITED: starsling.dev/best-practices/github-actions/pin-action-shas.md; SHAs must be
#  re-resolved from the official repos at authoring time — the listing below is illustrative]
- uses: actions/checkout@<full-sha>  # v7.0.0
- uses: astral-sh/setup-uv@<full-sha>  # v8.x — cache auto-enabled on GH runners since v5.0.0
- uses: actions/setup-node@<full-sha>  # v6.x — node-version: 22 or 24
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `env: { browser: true }` (eslintrc) | flat config `languageOptions.globals` | ESLint 9+ (flat default), ESLint 10 current | The new `eslint.config.mjs` must inline browser globals (`window`, `document`, `Chart`, `XLSX`, `console`, `localStorage`) — importing the `globals` package would need npm deps [CITED: eslint.org/docs/use/configure/migration-guide] |
| Mutable action tags (`@v4`) | Full-SHA pinning + `# vX.Y.Z` comment | Mainstream since tj-actions CVE-2025-30066 (2026-07 listings show checkout v7.0.0 / setup-node v6.5.0) | TEST-04's "actions SHA-pinned" clause is now table stakes; Dependabot updates pinned actions via the version comment |
| `random_state=` scipy kwarg | `rng=` preferred (random_state legacy) | scipy ≥1.15 | Either works at 1.18.1; pick one and pin it in tests for reproducible p-values |

**Deprecated/outdated:**
- TEST-04's literal "Python 3.12/3.13" matrix — superseded by `requires-python = ">=3.13"` (Pitfall 6).
- ROADMAP SC-2's "smoke run (tiny model × 1k samples × 1 epoch incl. export)" literal training-in-CI phrasing — superseded by CONTEXT Q1's canned golden replay (no real training in CI; the maintainer accepted the later, stricter form).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Exact-version npx pins (`eslint@10.12.0`, `html-validate@11.16.2`) are acceptable without a package.json | Standard Stack / Pitfall 5 | If the maintainer prefers a dev-only package.json, the manifest-free convention changes (repo currently has no package.json by design) |
| A2 | Specific action SHAs (checkout v7.0.0, setup-node v6.5.0, setup-uv v8.3.2) as listed by third-party trackers | Code Examples | SHAs are time-sensitive third-party listings; MUST be re-resolved from official repos at execution (impostor-commit hazard). Wrong SHA = broken or unverified workflow |
| A3 | `data_version` stamp home = `tasks.json` `version` field (currently "1.0.0") or CHANGELOG registry, not models_comparison (whose closed root map has no version slot) | DATA-02 | Wrong home = schema surgery or a stamp that doesn't regenerate with the artifacts it versions; maintainer should confirm |
| A4 | Eval subsets apply to the TEST split only (train/dev full) | Pattern 5 | If dev is also subset, checkpoint selection changes and comparability with historical single-run numbers shifts |
| A5 | The pre-E2' F6 regeneration (default-view switch on current single-run data) is committed this phase and recorded in CHANGELOG without an intermediate git tag; `data-v2` tags only after E2' | Summary / Open Question 3 | If the maintainer wants an intermediate tag (e.g. data-v1.1), the tagging tooling runs twice; no code impact |
| A6 | Priority ordering lands as a `--priority-file` (maintainer-curated JSON tiers) rather than CLI flags | Pattern 6 | If CLI-form is preferred, tier 2's "arena representatives" list becomes a long flag value; mechanism equivalent |
| A7 | `plant-dnamamba2-BPE` (committed results, absent from the 62-key registry) drops out of the E2'-chain leaderboard unless registered | Runtime State Inventory | If it must survive, it needs a registry entry (a 62→63 invariant change requiring maintainer sign-off, analogous to the space≡SPACE decision) |

## Open Questions

1. **The E2' data-chain bridge (BLOCKING design decision)**
   - What we know: `export_runs.py` emits task-centric `task_performance/` + `seed_stats/` from run records; `summarize_comparison.py` (the only `models_comparison*` producer) reads the model-centric `model_performance/{alias}_performance.json` directory [VERIFIED: summarize_comparison.py:333 `input_dir = 'model_performance'`]; nothing regenerates per-model files from run records; the submit page validates uploads as per-model `{info, performance}` files and the finetuning page loads `DataAPI.loadAllModelPerformance()` [VERIFIED: js/finetuning.js:51].
   - What's unclear: the bridge. Option A — `summarize_comparison.py` gains a task-centric input mode reading `task_performance/` (all required inputs exist there: 7-key card subset derivable from the 11-key card, raw metric via `info.metric`, FLOPs in metricBlock); keeps run-records→comparisons pure but leaves `model_performance/` frozen and the submit/finetuning pages on the old contract. Option B — a per-model emitter writes `model_performance/` from run records (preserves both pages + the submission contract) but partially resurrects the "per-model master-JSON assembly" export_runs claims to have replaced [VERIFIED: export_runs.py docstring line 5-7]. Option C — both views emitted by export_runs (task + model), one reader each.
   - Recommendation: decide WITH the maintainer early (it shapes the canned-replay fixture and the E2' runbook); Option A is the smallest-change path for the leaderboard; Option B/C preserve the contributor-facing contract. Also decide `plant-dnamamba2-BPE`'s fate here (A7).

2. **Where does `data_version` live (DATA-02) and what feeds the footer (DATA-06)?**
   - What we know: `tasks.json` has a free-string `version` ("1.0.0") [VERIFIED: schemas/tasks_index.json `version: {type: string}`]; `models_comparison` schema has no version slot; `js/main.js:367` currently stamps "Updated:" with a LIVE CLOCK.
   - Recommendation: bump `tasks.json.version` to the data_version at each regeneration + CHANGELOG as the human registry + footer reads the stamped value (never `new Date()`). If comparisons can move without task files moving (F6 pre-E2'), a tiny `data/manifest.json` (version + generated-from commit) may be cleaner — maintainer call.

3. **Does the pre-E2' F6 regeneration get an intermediate git tag?**
   - SC-1 only demands F6-before-E2'-publication; DATA-03 defines data-v2 as the post-E2' pair to data-v1. Recommendation: changelog entry + version bump, tag only at data-v2 (A5).

4. **Who are the "arena representatives" in tier 2 of the degradation order?**
   - No repo artifact names them. Recommendation: the priority file ships with tier 1 (the PIPE-03 E2E pair, verifiable) and a maintainer-curated tier 2 the planner surfaces as a `checkpoint:human-verify` (never invented by the agent).

5. **Permutation-test axis and family definition (CONTEXT Q3 says "pairwise model comparisons" without naming the score axis).**
   - Options: (a) per-task pairwise on the primary metric with BH across the task×pair family (large family, expensive); (b) pairwise on the aggregate view (rank_score / weighted) with score-vector-permutation across tasks (`permutation_type="samples"` shuffling per-task scores between the two models) — one family of C(42,2)=861 tests pre-E2', C(62,2)=1891 post-E2'. Recommendation: (b) for the leaderboard headline + optional (a) spot checks; document the family with the BH disclosure.

6. **New inventory script vs extending `baseline/compare.py` for the categorized data-v2 inventory.**
   - compare.py is per-file pair; a migration inventory wants a tree-level summary with category counts per file. A thin orchestrator looping compare.py `--summary-json` over the file set (the plan-01-03 pattern) likely suffices — no comparator edits.

7. **Does the golden replay chain include the BRIDGE aggregation (Open Question 1's output) or stop at task_performance?**
   - SC-2's chain is "export→aggregate→schema" — "aggregate" implies models_comparison. If the bridge is Option A (task-centric summarize), the replay covers it end-to-end; if Option B, the replay covers the per-model emitter too. Decide with Q1.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (venv) | data chain, tests | ✓ | 3.13.16 | — |
| uv | env sync, CI parity | ✓ | 0.13.0 (aarch64) | setup-uv installs its own in CI |
| Node | JS lane, tasks.json generator, `make data` | ✓ | v26.10.0 | — |
| git | tags, drift job | ✓ | 2.43.0 | — |
| ruff / ty / pytest | lint + typecheck + test gates | ✓ | 0.16.10 / 0.0.85 / 9.1.1 | — |
| scipy | permutation tests, FDR, t-intervals | ✓ | 1.18.1 (uv.lock) | — |
| numpy / pandas | aggregation | ✓ | per uv.lock (2.5.3 / 2.3.3 per Phase-1 pins) | — |
| On-disk datasets (43/50) | N audit, E2' | ◐ partial | 7 GUE dirs MISSING | audit skips-with-warning; E2' blocked on re-extraction (Pitfall 8) |
| GPU / dnallm / torch | E2' execution | ✗ (by design — never run by agents) | — | PIPE-02 env smoke + maintainer dual gate |
| Network (CI) | npx eslint/html-validate, uv sync | CI-only | — | — |

**Missing dependencies with no fallback:** none blocking this phase's code-only deliverables.
**Missing dependencies with fallback:** 7 GUE dataset dirs (audit marks unavailable rows; E2' launch checklist gates on re-extraction).

## Validation Architecture

> `workflow.nyquist_validation` is explicitly `false` in `.planning/config.json` — section skipped.

## Security Domain

> `security_enforcement: true`, ASVS level 1, block_on high. Phase surface: CI pipeline, offline scripts reading untrusted CSVs, a new pipeline CLI flag.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth surface (static site + CI) |
| V3 Session Management | no | None |
| V4 Access Control | no (CI-adjacent) | Workflow permissions: set `permissions: contents: read` at workflow top; PRs from forks never get secrets (default) |
| V5 Input Validation | yes | `--subset_file` JSON validated: known task keys (registry join), integer IDs in range (fail fast, mirror `_validate_filters` WR-07 discipline); N-audit treats CSVs as UNTRUSTED DATA (malformed rows skipped per the repo's `[Skip]` convention; never `eval`; run readers with bounded parsing) |
| V6 Cryptography | no | SHA256 manifests use hashlib (already the convention); never hand-roll |
| V14 Config | yes | CI: SHA-pinned actions (Pitfall 5/A2), exact-version npx pins, no secrets required by any job |

### Known Threat Patterns for static-site + CI + dataset tooling

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Action tag rewrite supply-chain (tj-actions class) | Tampering/Elevation | Full-SHA pins + version comments; minimal `permissions` |
| npx fetching a compromised fresh release | Tampering | Exact-version pins + human checkpoint (both tools flagged SUS on release recency) |
| Malicious dataset CSV (Zenodo-sourced, untrusted) | Tampering | Parse-only readers, per-row skip, no dynamic execution; downloads quarantined outside the repo tree |
| Subset file with path-like "task" keys / huge IDs | DoS/Tampering | Registry-key validation + integer range checks before any filesystem or select call |
| p-value/CI fabrication via unseeded RNG | Repudiation | Seeded everywhere (`rng=42`, bootstrap_seed=42) — reproducibility IS the integrity control |

## Sources

### Primary (HIGH confidence — repo, live-verified this session)
- `script/summarize_comparison.py` — aggregation surface (lines 158-220 stats, 246-326 aggregate, 329-467 main)
- `script/export_runs.py` — vendored `aggregate_se` (122-210), mapping tables, reader, D-12 join, emitter
- `pipeline/run_sweep.py` / `pipeline/run_finetune.py` — sweep semantics, subset integration point, validate_sequences call site
- `/home/forrest/Github/DNALLM/dnallm/datahandling/data.py` (READ-ONLY) — `load_local_data`, `validate_sequences` (859-910), `sampling` (1108-1145)
- `schemas/models_comparison.json`, `schemas/tasks_index.json` — closed contracts
- `.venv` live probes — scipy 1.18.1 `permutation_test`/`false_discovery_control` signatures; on-disk dataset audit (43/50, counts exact); CpG top-10 span 0.0021039; tool versions
- `baseline/compare.py`, `baseline/data-v1.sha256` convention, `script/freeze_snapshot.py`, `Makefile`, `pyproject.toml`, `tests/*` (golden/aggregation/export/sweep patterns)

### Secondary (MEDIUM confidence)
- [astral-sh/setup-uv action.yml (v7.6.0/v8.3.2)](https://github.com/astral-sh/setup-uv/blob/v7.6.0/action.yml) — version-file/caching inputs; v5.0.0+ auto-cache on GH runners
- [starsling.dev SHA-pinning guide](https://starsling.dev/best-practices/github-actions/pin-action-shas.md) — checkout v7.0.0 / setup-node v6.5.0 SHAs (third-party listing — re-resolve at execution)
- [cosai-oasis ADR-024 pinning posture](https://github.com/cosai-oasis/secure-ai-tooling/blob/main/docs/adr/024-github-actions-pinning-posture.md) — SHA-only policy, Dependabot comment format
- [eslint discussion #17021](https://github.com/eslint/eslint/discussions/17021) — flat config without package.json (`.mjs` workaround)
- [ESLint migration guide](https://eslint.org/docs/next/use/configure/migration-guide) — `env.browser` → `languageOptions.globals`
- [GitHub docs: workflow status badge](https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/adding-a-workflow-status-badge) — badge URL template (fetched this session)

### Tertiary (LOW confidence)
- None used for recommendations; A2's third-party SHAs are explicitly flagged for re-resolution

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new installed packages; all existing pins live-verified
- Architecture (repo seams): HIGH — every integration point opened and read this session; the bridge gap is a verified fact, not speculation
- CI specifics: MEDIUM — versions/posture from web sources; workflow shape follows repo conventions and will be exercised at execution
- Pitfalls: HIGH — each grounded in a verified repo fact or a live probe

**Research date:** 2026-10-10
**Valid until:** 2026-11-09 (repo facts stable at HEAD 89d374b+; CI action versions drift faster — re-resolve SHAs at plan execution)
