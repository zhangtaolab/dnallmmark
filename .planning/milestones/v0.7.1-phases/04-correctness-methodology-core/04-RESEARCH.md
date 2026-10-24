# Phase 4: Correctness & Methodology Core - Research

**Researched:** 2026-10-10
**Domain:** Data-chain correctness fixes (species grouping, unified exporter) + static-site frontend restoration + pipeline quirk-parity carryovers
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Species metadata table (F3②/AUD-01)**
- **Q1:** The human-verified species table IS `pipeline/datasets_info.json`'s `Category` column (merged in during Phase 3's D-10 unification; 50 rows Animals/Plants/Microbe). No second source of truth.
- **Q2:** Verification procedure: the maintainer personally reviews all 50 Category rows against a generated review list; the confirmed list is committed as the human-verified evidence.
- **Q3:** The Phase 2 species xfail lock (D-03 pivoted export-chain contract) is UNMARKED in the SAME commit as the fix lands (fix + unmark + aggregation-diff inventory, three-in-one — SC-1 literal). The findability/uniqueness/species-key companion stays.
- **Q4:** "Multiple"-origin datasets (e.g. iDNA_ABF 5mC/6mA cross-species) classify into their majority-species arena per the Phase 3 research recommendation; the review list annotates their multiple origin.

**Unified exporter (REV-03/F3① + IN-03)**
- **Q1:** Aggregation = VENDORED copy of dnallm.finetune.sweep's pure numpy/scipy statistics function (source-annotated revision@483a35c) + a parity test pinning behavior to that revision. No direct import (dnallm/__init__ pulls torch — breaks the CPU-only torch-free dev discipline). Revisit when the suite offers a torch-free import path.
- **Q2:** New script `script/export_runs.py`: reads F2-layout run_record.json → applies the explicit metric-key mapping → emits task_performance-compatible shape (Phase 2 schemas unchanged; frontend untouched). `get_task_performance.py`'s input side retires per SC-2.
- **Q3:** The exporter OWNS the single metric-key mapping table; `summarize_comparison.py`'s METRIC_KEY_MAP mirror is DELETED (IN-03 resolved by removal, not by co-existence); key-parity unit tests enumerate suite-registry ↔ export-enum both directions; new keys join the closed enum with the data≡enum self-check updated in the same commit (SC-6).
- **Q4:** freeze_snapshot (tar + SHA256 + frozen commit hash) lands as a tested function this phase; the actual freeze invocation waits for Phase 6 packaging (data still moves at E2').

**Frontend restoration (FIX-01..04)**
- **Q1:** renderNavbar fix covers the 5 REAL pages (index/task/finetuning/models/datasets); mockup/test dev artifacts stay out (project convention).
- **Q2:** submit.html is created as the 6th real page: js/submit.js rewired to the current schema, added to CONFIG.NAV_LINKS, client-side validation + PR-instruction generator per the Phase 1 audit description.
- **Q3:** A shared escapeHTML util (js/data.js) applied ONLY at DOM-build sites this phase touches (navbar/submit/task renderers) — bounded to touched code, no global hardening pass.
- **Q4:** "Every page renders, zero console errors" is verified by LIVE Playwright MCP browser passes per page (console capture as evidence) plus UAT records; static checks alone are insufficient.

**Phase-3 carryovers**
- **Q1:** WR-03/WR-04 quirk-parity ports land IN FULL (ACGT alphabet option, models_with_limited_length, safetensors membership fix, length-tier rounding) with a parity contract test against the legacy pipeline's registries.
- **Q2:** All 17 card-less models get full 11-key cards this phase (pure metadata, no GPU; same discipline as PlantHelixSeek; card-absent enumeration goes to zero — contract test asserts 62/62 complete cards).
- **Q3:** IN-01 comparator label fix lands inside the SC-1 aggregation-diff inventory tooling (one tool surface, two items).
- **Q4:** README exporter sentence + IN-08 (convert_registry.py joins make lint scope) bundled as one hygiene commit, ruff-zero self-evidenced.

### Claude's Discretion
None — all sixteen grey-area answers were maintainer-accepted recommendations.

### Deferred Ideas (OUT OF SCOPE)
- Direct import of the suite's aggregation function — until dnallm offers a torch-free import path (vendor now, revisit later).
- Actual freeze_snapshot invocation — Phase 6 packaging.
- Global innerHTML escaping hardening — bounded to touched sites this phase (full pass is out of scope by design).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description (from REQUIREMENTS.md) | Research Support |
|----|------------------------------------|------------------|
| FIX-01 | Every page renders without errors — `renderNavbar()` null-container crash fixed; verified on ALL pages, not just the 3 known-broken ones | Crash mechanism fully mapped (see Frontend Restoration); AUD-10 nesting misread is the second render-blocking defect; Playwright verification path confirmed |
| FIX-02 | Species-as-dataset grouping bug fixed (`pipeline/dnallmmark_pipeline.py:1229`), with a failing test written first | Producer defect site verified verbatim (:1248); lock shape + fixture + unmark sequence mapped; aggregation diff PREVIEWED with exact expected classes |
| FIX-03 | Submission flow repaired — `submit.html` created, orphaned `js/submit.js` wired to the current data schema, reachable from navigation | submit.js validateJSON misread confirmed; NAV_LINKS already carries Submit; schema shape captured for rewiring |
| FIX-04 | Sink-side escaping at DOM-build sites the fixes touch (bounded to touched code, not a full security hardening pass) | escapeHTML placement (js/data.js) + bounded site list (navbar/submit/task renderers) enumerated |
| REV-03 | Unified exporter + result snapshot — metric-key mapping layer (suite registry ↔ export keys, key-parity unit-tested), dataset species from a human-verified metadata table (never model cards), per-seed detail + mean±SD/bootstrap-CI aggregates; freeze_snapshot (tar + SHA-256 + frozen commit hash) | Suite aggregate_seeds signature/body captured @483a35c; run_record schema captured; suite metric-registry 28-name surface captured; scipy dependency gap discovered; parametersBlock gap discovered |
</phase_requirements>

## Summary

Phase 4 fixes every confirmed correctness defect in one phase across three layers. The **species fix** (FIX-02) is now a consumer-side switch in `script/summarize_comparison.py` (group by `pipeline/datasets_info.json` Category instead of the producer's `dataset.species` string) plus a producer-side rule in the new exporter — no GPU, no pipeline run. A live preview run of the Category-based grouping against the 42 committed model files shows the exact aggregation diff the fix will produce: `models_comparison.json` (total) and `models_comparison_plant.json` regenerate **byte-identical**; `models_comparison_animal.json` and `models_comparison_microbe.json` change **all 42 entries each** via exactly one membership swap per file (GUE__EPI_GM12878 moves microbe→animal, GUE__fungi_species_20 moves animal→microbe; both arenas keep their dataset count — 22 animal, 13 microbe — because the two moves cancel). The iDNA_ABF Multiple→Animals majority mapping produces **no net change** (today's committed value is already Animals). This preview IS the pre-documented diff inventory the SC-1 gate needs.

The **unified exporter** (REV-03) has a clean vendoring target: `dnallm/finetune/sweep.py::aggregate_seeds` at suite revision 483a35c is a pure `numpy`/`scipy` function (no torch anywhere in the module) with an exact signature and n-guard semantics captured below. Two design gaps surfaced that the planner must resolve: (1) **scipy is not in the dev/data environment** — the vendored function imports `scipy.stats`, so scipy joins a dependency group same-commit (the suite itself pins `scipy>=1.15.2`); (2) **run_record.json cannot populate the task_performance schema's required `parametersBlock`** (batch_size/epochs/lr/…) — the record carries only metrics + null-when-unknown vram_probe fields, so the exporter must join finetune config and/or the schema needs a conscious decision. The **frontend restoration** is precisely bounded: no HTML page defines `.navbar-container` (grep 0 across all 8 pages), finetuning/models/datasets crash on the first render call inside setup()'s try/catch, index/task simply have no navbar, and submit.js's validateJSON iterates the wrong nesting level so it rejects every real file.

**Primary recommendation:** Land the species fix as a summarize_comparison consumer-side switch with hard-fail on unregistered datasets, regenerate + inventory the 4 comparison files (2 byte-identical, 2 fully-explained), unmark the lock + fix the fixture in the same commit; build export_runs.py dual-input (run_record fixture path + legacy model_performance path) around a vendored `aggregate_seeds` with scipy added to the data group; fix the navbar by giving all 5 real pages a `.navbar-container` div and one shared render path, then fix AUD-10's nesting misreads before Playwright-verifying zero console errors per page.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Dataset→arena grouping authority | Data Aggregation (`script/summarize_comparison.py`) | Data Production (exporter writes Category into emitted files) | Grouping is a consumer-side read of the human-verified registry; producer only mirrors it forward |
| Species value in result JSONs | Data Production (`script/export_runs.py` + future pipeline) | — | The D-03 lock asserts export-chain output; the exporter is the new producer of that output |
| Metric-key mapping (suite↔export) | Data Production (`script/export_runs.py` OWNS the table) | Data Aggregation (imports it; METRIC_KEY_MAP deleted) | One owner per CONTEXT Q3; summarize imports rather than mirrors |
| Per-seed statistics (mean/SD/CI) | Data Production (vendored `aggregate_seeds` in script/) | — | Suite-revision-pinned vendored copy; parity-tested |
| Navbar rendering | Static Site (HTML shells + page JS) | — | Container div per page + one renderer; no framework allowed |
| Submission validation | Browser (`js/submit.js` client-side) | Static Site (schema doc as contract) | Static-hosting constraint: no server validation possible |
| Output encoding (escaping) | Browser (`js/data.js` util) | — | Sink-side at DOM-build sites; bounded to touched code |
| Quirk registries parity | Data Production (`pipeline/run_finetune.py`) | Tests (parity contract vs legacy lists) | Registries are runtime behavior switches in the training driver |
| Model-card metadata | Data Production (`pipeline/models_info.json`) | Tests (62/62 completeness assertion) | Pure registry data; no code path |
| Comparator label taxonomy | Verification tooling (`baseline/compare.py`) | Tests | The aggregation-diff inventory consumes its vocabulary |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | 2.5.3 (uv.lock) | Aggregation math, vendored statistics | Already pinned [VERIFIED: pyproject.toml:13 + uv env probe] |
| pandas | 2.3.3 (uv.lock) | `calculate_dataset_stats` ranking | Already pinned [VERIFIED: pyproject.toml:12] |
| scipy | **NEW** — add `>=1.15.2` (suite-matching floor; latest 1.18.1 installs clean) | Vendored `aggregate_seeds` t-interval (`stats.t.ppf`) | The suite pins `scipy>=1.15.2` at pyproject.toml:59 [VERIFIED: /home/forrest/Github/DNALLM/pyproject.toml:59, read-only]; NOT currently in our dev/data env (import fails live) — must be added same-commit as the vendored copy |
| pytest | 9.1.1 | Test harness (xfail strict locks live on it) | Existing [VERIFIED: uv env probe] |
| jsonschema | 4.26.0 | Schema validation of exporter output | Existing [VERIFIED: uv env probe] |
| ruff | >=0.16.10 | Lint gate (scope grows this phase) | Existing [VERIFIED: pyproject.toml:21] |
| ty | >=0.0.85 | Type gate (maintainer directive, Phase 3 on) | Existing; `make typecheck` must stay zero-diagnostics |
| Node.js | v26.10.0 | JS test lane (`node --test`) | Existing [VERIFIED: env probe] |
| Playwright | CLI 1.64.0 (`npx playwright --version`); `playwright@claude-plugins-official` plugin previously used | LIVE page verification with console capture (CONTEXT Q4) | Available in environment [VERIFIED: env probe + ~/.claude.json plugin usage record] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python stdlib `tarfile`/`hashlib`/`subprocess` | 3.13 | freeze_snapshot (tar + SHA256 + commit hash) | Tested function this phase; invocation deferred to Phase 6 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Vendored `aggregate_seeds` + scipy dep | Direct `from dnallm.finetune.sweep import aggregate_seeds` | LOCKED OUT by CONTEXT Q1 (dnallm/__init__ pulls torch) |
| Hand-computed t-quantile table (no scipy) | scipy | Violates parity intent; hand-rolling a quantile function is exactly a don't-hand-roll — rejected |
| Chart/templating libraries for submit.html | — | LOCKED OUT by project constraint (vanilla no-build MPA) |

**Installation:**
```bash
# scipy joins the data group (exporter runtime dep) — uv.lock re-resolved same commit
uv add --group data "scipy>=1.15.2"
```

**Version verification:** pytest 9.1.1 / numpy 2.5.3 / pandas 2.3.3 / jsonschema 4.26.0 confirmed live via `uv run python -c "import …"` this session; scipy 1.18.1 confirmed installable via `uv run --with scipy` probe (registry-resolved, no network incident).

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| scipy | PyPI | First release 2001 (25 yrs); latest 1.18.1 published 2026-08-21 | checker signal null (PyPI probe returned no download count) | checker signal null (repo field not populated by probe); canonical repo github.com/scipy/scipy | **SUS** (reasons: unknown-downloads, no-repository — both are *signal absence* in the checker's PyPI probe, not negative evidence) | Flagged — planner adds checkpoint:human-verify before the uv add. Mitigating evidence: the DNALLM suite itself declares `scipy>=1.15.2` (pyproject.toml:59, read-only verified at both HEAD and 483a35c), scipy is a NumFOCUS-governed foundational package, and the vendored function's scipy usage (`stats.t.ppf`) was read directly from the suite source this session. |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** scipy — checkpoint:human-verify before install (see mitigating evidence above; the SUS verdict is an artifact of null metadata signals, and the dependency is suite-pinned).

No other external packages are introduced this phase: everything else is stdlib + already-pinned project dependencies.

## Architecture Patterns

### System Architecture Diagram

```
                    OFFLINE DATA CHAIN (CPU, no GPU, no dnallm)
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  [E2' future]  finetuned/{model}/{task}/seed_{seed}/run_record.json      │
│                     │  (metrics = final_metrics.json VERBATIM,           │
│                     │   suite-native keys e.g. eval_AUROC)               │
│                     ▼                                                    │
│  script/export_runs.py  ◄─── pipeline/datasets_info.json (Category,      │
│     │  1. map metric keys        metric col; species=Category rule)      │
│     │  2. join model cards ◄─── pipeline/models_info.json                │
│     │  3. vendored aggregate_seeds (per-seed detail + mean±SD/CI)        │
│     ▼                                                                    │
│  dnallm-mark/data/task_performance/{ds}_task_performance.json            │
│     (schema-validated; frontend UNTOUCHED)                               │
│                                                                          │
│  [today]  dnallm-mark/data/model_performance/*.json (42 committed)       │
│                     │                                                    │
│                     ▼                                                    │
│  script/summarize_comparison.py                                          │
│     │  FIX-02: species := datasets_info[ds].Category                     │
│     │        (Multiple → majority arena; hard-fail unregistered ds)      │
│     │  metric keys: imports exporter's mapping (METRIC_KEY_MAP deleted)  │
│     ▼                                                                    │
│  models_comparison{,_animal,_plant,_microbe}.json                        │
│     │  diff-inventoried: total+plant byte-identical,                     │
│     │  animal+microbe 42/42 changed via 1 membership swap each           │
│     ▼                                                                    │
│  baseline/compare.py (--summary-json)  ◄── IN-01: int diffs get an       │
│     │                                    honest label, not FLOAT_BIG     │
│     ▼                                                                    │
│  aggregation-diff inventory (SC-1 gate: only fix-explained changes)      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

                    STATIC SITE (browser, no build step)
┌──────────────────────────────────────────────────────────────────────────┐
│  6 HTML pages ── each gains .navbar-container ──► one shared renderNavbar │
│     index/task/finetuning/models/datasets + NEW submit.html              │
│         │                            │                                   │
│         ▼                            ▼                                   │
│  js/{page}.js  ── FIX-01 crash gone; AUD-10 nesting reads fixed          │
│         │                                                                │
│         ▼                                                                │
│  js/data.js: DataAPI + escapeHTML util (FIX-04, bounded sites)           │
│         │                                                                │
│         ▼                                                                │
│  Playwright MCP live pass per page ──► zero console errors (evidence)    │
└──────────────────────────────────────────────────────────────────────────┘

                    PIPELINE QUIRKS (code-only, never executed)
┌──────────────────────────────────────────────────────────────────────────┐
│  pipeline/run_finetune.py: 4 quirk ports + parity contract test vs       │
│  legacy dnallmmark_pipeline.py registries (union for safetensors,        │
│  registry-name forms for renamed/dropped models)                         │
└──────────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure
```
script/
├── export_runs.py        # NEW — unified exporter (REV-03/F3①)
├── summarize_comparison.py  # EDIT — Category grouping, imports mapping, get_float fix
├── get_task_performance.py  # input side retires (see Open Question 6 for disposition)
├── convert_registry.py      # joins make lint scope (IN-08)
baseline/
├── compare.py            # EDIT — IN-01 int label; WR-02 bool/int report
pipeline/
├── run_finetune.py       # EDIT — 4 quirk ports
├── models_info.json      # EDIT — 17 card fills (62/62 complete)
dnallm-mark/
├── submit.html           # NEW — 6th real page
├── {index,task,finetuning,models,datasets}.html  # EDIT — .navbar-container div
└── js/
    ├── data.js           # EDIT — escapeHTML util + aggregateSpecies caller level
    ├── submit.js         # EDIT — validateJSON rewiring
    ├── finetuning.js / datasets.js / models.js  # EDIT — nesting reads (AUD-10)
    └── task.js           # EDIT — bounded escaping at touched renderers
tests/
├── test_known_defects.py     # EDIT — fixture fix + AUD-01 unmark; WR-02/WR-03 unmarks
├── test_aggregation.py       # EDIT — get_float pins flip to isfinite semantics
├── test_export_runs.py       # NEW — mapping parity + exporter output contracts
├── test_vendored_stats.py    # NEW — aggregate_seeds parity @483a35c
├── test_run_finetune_contracts.py  # EDIT — quirk-parity extension
└── test_registry_unification.py    # EDIT — card-absent enumeration → 62/62
```

### Pattern 1: The species fix — consumer-side switch with hard-fail join

**What:** `summarize_comparison.py`'s grouping source changes from the result-JSON `dataset.species` field to a `datasets_info.json` Category lookup. The current mechanism, verbatim [VERIFIED: script/summarize_comparison.py:335-339, 389-412]:

```python
species = str(ds_meta.get("species", "Unknown")).strip()
# ...
if species:
    dataset_species_map[dataset_name] = species
```

and grouping/filename emission:

```python
species_groups = {}
for ds_name, sp in dataset_species_map.items():
    if sp not in species_groups:
        species_groups[sp] = []
    species_groups[sp].append(ds_name)
# ...
singular_species = to_singular_species(species)
safe_species_name = singular_species.replace("/", "_").replace("\\", "_").lower()
out_file = f'models_comparison_{safe_species_name}.json'
```

**The fix joins exactly like the lock's `_load_category_map` does** [VERIFIED: tests/test_known_defects.py:79-91]: `{name: entry["Category"] for name, entry in registry.items()}` — plain key lookup on `Source__task`-form names, no normalization. The join must **hard-fail** (not fall back to the file value) when a dataset has no registry row: a silent fallback would re-create the class of defect being fixed. All 47 datasets present in the committed model files have registry rows (verified by join this session — zero misses).

**Multiple→arena mapping** (CONTEXT Q4): `Category == "Multiple"` maps to the majority-species arena. For the 2 Multiple datasets (iDNA_ABF__5mC/6mA) the majority arena is **Animals** [ASSUMED — inferred from cross-species composition and from the committed files already carrying "Animals"; the maintainer review list (Q2) confirms per-row]. Mapping Multiple→Animals produces **zero net diff** vs today (previewed live).

**When to use:** the fix regenerates all 4 comparison files in the same commit as the lock unmark and the diff inventory (SC-1 three-in-one).

**Aggregation-diff inventory (previewed live this session over the 42 committed files):**

| File | Expected diff | Explanation |
|------|--------------|-------------|
| `models_comparison.json` | **byte-identical** (preview: 0/42 entries changed) | Total aggregation never reads species |
| `models_comparison_plant.json` | **byte-identical** (0/42) | Plant membership identical under both sources (15 registry-Plants = 15 file-Plants) |
| `models_comparison_animal.json` | **42/42 entries changed** | Membership swap: GUE__fungi_species_20 leaves (file=Animals → registry=Microbe), GUE__EPI_GM12878 enters (file=Microbe → registry=Animals); iDNA_ABF×2 stay (Multiple→Animals = today's value). 22 datasets before AND after |
| `models_comparison_microbe.json` | **42/42 entries changed** | Inverse swap (EPI_GM12878 leaves, fungi_species_20 enters); 13 datasets before AND after |

Every per-model numeric change (rank_score, sum_minmax/zscore/robust, avg_*, top*_count, samples, sum/avg_PFLOPs) must be arithmetically attributable to removing one dataset's contribution and adding the other's; the final `rank` field may shift for models whose own totals are unchanged, purely from reordering. No model is added to or dropped from any file (all 42 models have results on both swapped datasets — verified: no ADDED/DROPPED in preview). Integer diffs (rank, samples, top-K) are exactly why the IN-01 label fix rides in the same tooling: without it they all report as FLOAT_BIG.

**The 50 Category rows for the maintainer review list (Area 1 Q2 deliverable)** — dumped verbatim from `pipeline/datasets_info.json` this session [VERIFIED: live read]:

```
Category counts: Animals 20, Plants 15, Microbe 13, Multiple 2

Animals (20): BEND__CpG_methylation, Deep4mC_datasets__C.elegans_4mC,
  Deep4mC_datasets__D.melanogaster_4mC, GUE__EPI_GM12878, GUE__human_tf_0,
  GUE__mouse_1, GUE__mouse_4, GUE__prom_300_all, GUE__prom_core_all,
  Genomic_Benchmarks__coding, Genomic_Benchmarks__human_vs_worm,
  Genomic_Benchmarks__regulatory_region_type, NT_downstream_tasks__H3K27ac,
  NT_downstream_tasks__H3K27me3, NT_downstream_tasks__H3K4me2,
  NT_downstream_tasks__H3K9me3, NT_downstream_tasks__enhancers,
  NT_downstream_tasks__splice_sites_acceptors,
  NT_downstream_tasks__splice_sites_all, NT_downstream_tasks__splice_sites_donors
Plants (15): PDLLMs_datasets__plant-multi-species-{H3K27ac,H3K27me3,H3K4me3,
  core-promoters,lncRNAs,open-chromatin,sequence-conservation},
  PlantCAD2_fine_tuning_tasks__cross_species_leaf_absolute_translation,
  PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation,
  plant-genomic-benchmark__gene_exp.{arabidopsis_thaliana,oryza_sativa,zea_mays},
  plant-genomic-benchmark__poly_a.arabidopsis_thaliana,
  plant-genomic-benchmark__promoter_strength.leaf,
  plant-genomic-benchmark__terminator_strength.leaf
Microbe (13): Deep4mC_datasets__E.coli_4mC, GUE__emp_{H3,H3K14ac,H3K36me3,
  H3K4me1,H3K79me3,H3K9ac,H4,H4ac}, GUE__fungi_species_20, GUE__virus_covid,
  GUE__virus_species_40, iPro-WAEL_datasets__Promoter_R_capsulatus
Multiple (2): iDNA_ABF_datasets__5mC, iDNA_ABF_datasets__6mA  ← annotate
  multiple origin on the review list; classify into majority arena (Animals)
```

Only 2 rows conflict with the committed file values (EPI_GM12878, fungi_species_20) — those two ARE the fix's diff. 3 registry datasets have no results in the committed files (47 file datasets ⊂ 50 registry rows) — they are invisible to the aggregation and need no review-list action beyond presence.

### Pattern 2: The lock unmark — exact current shape and same-commit mechanics

The lock and companion, verbatim contract [VERIFIED: tests/test_known_defects.py:99-164]:

- **Companion (unmarked, stays forever):** `test_aud01_contract_fixture_has_expected_shape` — asserts the fixture is a result-JSON with ≥2 dataset entries, each carrying a `dataset` sub-dict with a `species` key, each name resolvable to a Category row. Goes RED if the fixture loses its contract shape (WR-01: the xfail marker swallows every failure inside the lock body, so only an unmarked companion can catch a fixture edit that deletes the defect).
- **Lock (xfail strict, reason "AUD-01-P0 species-as-dataset — Phase 4 fix"):** `test_aud01_species_matches_dataset_arena_category` — asserts every fixture entry's `dataset.species` ∈ `VALID_SPECIES = frozenset({"Animals", "Plants", "Microbe", "Multiple"})` AND `== category_map[name]`.
- **Fixture:** `tests/fixtures/export_chain/defect_species_performance.json` — the SOLE defect carrier; its `plant-genomic-benchmark__poly_a.arabidopsis_thaliana` entry carries `species="athaliana"` while the dataset's Category is Plants. `--runxfail` proves the lock fails on this entry today (non-vacuous, re-proven at Phase 3 verification).

**Same-commit sequence (SC-1 literal):** (1) land the summarize_comparison fix; (2) update the fixture's defect entry to `species="Plants"` (deliberate, flagged in the plan — the companion forces deliberateness); (3) remove the `xfail` marker from the lock (it now XPASSes; strict=True would FAIL the suite if the marker stayed); (4) regenerate the 4 comparison files; (5) commit the diff inventory alongside. The lock becomes a permanent green contract test; the companion keeps guarding fixture integrity.

**Note on VALID_SPECIES vs task_performance schema:** the lock's legal set includes `"Multiple"` (frozenset above, verbatim) but `schemas/task_performance.json`'s datasetBlock species enum is `["Animals", "Plants", "Microbe"]` only [VERIFIED: schemas/task_performance.json:34]. These coexist fine because the exporter applies the Multiple→majority mapping before emission — but the exporter test must assert emitted species ∈ the schema enum (never the raw "Multiple"), or schema validation catches it. Both committed iDNA_ABF task files carry "Animals" today (verified live).

### Pattern 3: The unified exporter — vendoring target, dual input, mapping layer

**Vendoring target** [VERIFIED: `git show 483a35c:dnallm/finetune/sweep.py` read-only; file identical at suite HEAD (diff 483a35c..HEAD empty for both sweep.py and metric_registry.py)]:

```python
def aggregate_seeds(
    values: Sequence[float],
    *,
    n_bootstrap: int,
    bootstrap_seed: int,
    small_n_ci: str,          # "t-interval" | "omit"
) -> dict[str, Any]:
```

Returns the statistics block with EXACTLY these keys: `{"n_seeds": int, "mean": float, "sd": float|None, "ci95": [float, float]|None, "method": str}`. n-guard semantics verbatim from source:
- `n < 3` → `ci95=None, method="none"` (D-14: never vacuous)
- `3 <= n < 10`, `small_n_ci="t-interval"` → Student-t interval, `method="t"` (`sem = std(ddof=1)/sqrt(n)`, `tcrit = stats.t.ppf(0.975, n-1)`)
- `3 <= n < 10`, `small_n_ci="omit"` → `ci95=None, method="omitted"`
- `n >= 10` → seeded percentile bootstrap (`np.random.default_rng(bootstrap_seed)`, `rng.integers(0, n, size=(n_bootstrap, n))`, `np.percentile(means, [2.5, 97.5])`), `method="bootstrap-percentile"`

`sd` is `None` at n=1 (ddof=1 undefined); `ValueError` on non-flat/empty input or bad `small_n_ci`. Module-level constants to vendor with it: `SMALL_N_CI_CHOICES = ("t-interval", "omit")`, `CI_MIN_SEEDS = 3`, `BOOTSTRAP_MIN_SEEDS = 10`. The only imports are `numpy` and `scipy.stats` — no torch anywhere in the module. The parity test pins: n-guard boundaries (2/3/9/10), t-interval values against `scipy.stats.t` recomputation, bootstrap determinism (same seed → identical interval), the ValueError cases.

**Input side — run_record.json schema (F2 contract)** [VERIFIED: pipeline/run_sweep.py:23-37 docstring schema]:

```python
{
    "model": "...", "task": "...", "seed": 42,
    "status": "completed" | "failed" | "skipped",
    "output_dir": ".../seed_42",
    "metrics": { ... },          # final_metrics.json keys VERBATIM, suite-native
    "vram_probe": {"gpu_mem_total": null, "init_max_mem": null,
                   "batch_size": null, "gradient_accumulation_steps": null},
    "git_commit": "<repo HEAD at launch>",
    "started_at": "...", "finished_at": "...",
    "error": null
}
```

Test-side metric key convention [VERIFIED: tests/test_sweep.py:68-72]: `SUITE_NATIVE_METRICS = {"eval_AUROC": 0.9123, "eval_pearsonr": 0.5, "eval_loss": 0.234}` — the fixture metric set the exporter's run-record path should reuse. Layout: `{output_root}/{model}/{task}/seed_{seed}/run_record.json`.

**Dual-input design (run records do not exist until E2'):** the exporter's run-record path is exercised over synthetic run-record fixtures (fake tree + `SUITE_NATIVE_METRICS`-style payloads). Whether it ALSO carries a legacy `model_performance/` input path is a planner decision (see Open Question 6) — the locked text retires `get_task_performance.py`'s input side, and the 47 committed task files remain the live frontend data until E2' regenerates them.

**The suite metric-registry key surface (the mapping must cover this)** [VERIFIED: `git show 483a35c:dnallm/tasks/metric_registry.py`, `_RAW_REGISTRY` table read verbatim]. 28 canonical names:

```
accuracy, precision, recall, f1, f1_micro, f1_weighted, f1_samples,
precision_micro, precision_weighted, precision_samples,
recall_micro, recall_weighted, recall_samples,
mcc, matthews_correlation, AUROC, AUPRC, AUROC_ovr, AUROC_ovo,
TPR, TNR, FPR, FNR, mse, mae, r2, pearsonr, spearmanr
```

Every canonical name also resolves its `eval_`-prefixed alias (`eval_AUROC`, `eval_auroc`, …); historical aliases `eval_pearson_r`/`eval_spearman_r` also resolve (one-directional — aliases are never emitted). Registry API: `canonical_name(name)`, `registered_names()`, `resolve(name)`, `validate_emission(keys)`. The module is import-light (no torch/sklearn at module level) but lives under the `dnallm` package whose `__init__` pulls torch — hence no direct import (CONTEXT Q1).

**Mapping layer shape** — three sub-maps the single table needs:

1. **Alias resolution** (suite-alias → suite-canonical): strip/resolve `eval_`-prefixed keys exactly as the registry does (`eval_AUROC` → `AUROC`).
2. **Canonical → export slot**: `AUROC→auroc`, `AUPRC→auprc`, `pearsonr→pearson_r`, `spearmanr→spearman_r`, `mse→mse`, `r2→r2`, `f1→f1`, `mcc→mcc`, `accuracy→accuracy`, `precision→precision`, `recall→recall`, `loss←eval_loss`, `runtime←train_runtime` [the last two are pipeline-produced keys, not registry metrics]. The legacy producer's hardcoded precedent, verbatim [VERIFIED: pipeline/dnallmmark_pipeline.py:1273-1285]: `"auroc": test_results.get("eval_AUROC", "")`, `"pearson_r": test_results.get("eval_pearsonr", "")`, `"spearman_r": test_results.get("eval_spearmanr", "")`, … — the new table formalizes exactly this legacy semantics.
3. **Unmapped canonicals** (`f1_micro/weighted/samples`, `precision_*`/`recall_*` variants, `matthews_correlation`, `AUROC_ovr/ovo`, `TPR/TNR/FPR/FNR`, `mae`): either join the metricBlock closed enum per SC-6 (schema + data≡enum self-check updated same commit) or map to `""`. Planner decision — default: map to `""` now (matches the 14-key contract's "missing = empty string" convention), extend the enum only when a task actually emits them.

**Key-parity tests both directions:** (a) every suite canonical (vendored 28-name list, source-annotated @483a35c) either maps to an export slot or is explicitly declared unmapped — no silent drops; (b) every export metricBlock key traces to a suite key or is declared pipeline-produced (FLOPs, runtime, loss). The vendored name list is the parity oracle (importing the live registry is impossible CPU-side; see Don't Hand-Roll for the enumeration-mechanism options).

**Output shape:** task_performance-compatible per schemas/task_performance.json — `info` = 8-key datasetBlock (dev/labels/length/metric/species/test/train/type; metric enum `["f1","mcc","spearmanr","AUPRC"]`, species enum `["Animals","Plants","Microbe"]`), `performance` = open map of model alias → `{model: modelCard(11 keys), parameters: parametersBlock(9 keys), performance: metricBlock(14 keys)}` [VERIFIED: schemas/task_performance.json:15-143]. The exporter joins `models_info.json` for the modelCard and `datasets_info.json` for the datasetBlock. The **parametersBlock gap** (9 required training-param keys that run_record.json does not carry) is Open Question 5.

### Pattern 4: Frontend restoration — crash mechanism and fix order

**Crash mechanism (FIX-01)** [VERIFIED: live grep + code reads this session]:

- NO HTML page defines `.navbar-container` — grep count 0 across all 8 HTML files (5 real + 3 dev artifacts).
- `finetuning.js` / `models.js` / `datasets.js`: `renderNavbar()` is the FIRST render call in `setup()` → `document.querySelector('.navbar-container').innerHTML = ...` throws `TypeError: Cannot set properties of null` → caught by setup()'s try/catch → `console.error('Failed to load data:', error)` → NOTHING after renders. These are the 3 known-broken pages (AUD-09, browser-verified in Phase 1).
- `main.js` / `task.js`: NO renderNavbar call at all — index and task pages render fully but have NO navigation (the audit's "verified on ALL pages, not just the 3 known-broken ones" is exactly this: the other 2 pages lack nav without crashing).
- `js/submit.js` also queries `.navbar-container` (line 39-53 region) — orphaned; no host page exists.

**Fix:** add a `.navbar-container` div to the 5 real pages' HTML shells (matching the existing empty-container pattern: `.hero-container`, `.leaderboard-container`, etc.), give main.js/task.js a navbar render call, keep the per-page renderNavbar implementations pointed at the now-existing container (or share one renderer — planner choice; the audit suggested "remove the calls (static navbars already exist) or extract one shared navbar renderer", but CONTEXT Q1 locks "renderNavbar fix covers the 5 REAL pages", i.e. the dynamic navbar is kept). NAV_LINKS already contains `{ name: 'Submit', url: '/submit.html' }` [VERIFIED: js/config.js:56] — the dead link becomes live when submit.html lands; no config change needed beyond confirming the entry.

**AUD-10 nesting misreads must land WITH the crash fix** (rendering order): four consumers iterate the ROOT `{info, performance}` document instead of its `performance` dict [VERIFIED: AUDIT.md AUD-10 row, file:line evidence]. Sites: `js/finetuning.js:129-132`, `js/datasets.js:46-47`, `js/data.js:132-142` (`aggregateSpecies` — callers pass the wrong level), `js/submit.js:184-195`. On finetuning/datasets this is currently MASKED by the AUD-09 crash — unmasking the crash without fixing the nesting yields pages that render garbage rows named "info"/"performance". Both must land before the Playwright zero-console-error pass means anything.

**submit.js rewiring (FIX-03):** current `validateJSON` iterates `Object.entries(parsed)` at the ROOT and rejects any value without `dataset`/`performance` siblings — so a real `{model}_performance.json` fails with `Dataset "info" missing required fields (dataset, performance)` [VERIFIED: js/submit.js:171-206, verbatim read]. Rewire to the Phase 2 model_performance schema shape: top level must be `{info, performance}`; each `performance.{dataset}` entry must carry `dataset`/`parameters`/`performance` sub-dicts; client-side checks mirror the schema's required keys (full JSON-Schema-in-the-browser is NOT needed — a structural check plus the PR instruction stays vanilla-JS and light). submit.html follows the datasets.html shell pattern (empty containers + module script tag + CSS links).

**Bounded escaping (FIX-04):** add `escapeHTML(str)` to `js/data.js` (beside `getColorForModel`/`normalizeToArena` helpers). Apply ONLY at DOM-build sites this phase touches: navbar renderer (CONFIG.APP_NAME + link names are static today but the util goes in as the pattern), submit page renderers (user-entered model name, submitter name, email — the highest-risk interpolations per AUD-14), and task-page renderers this phase edits. grep confirms ZERO escaping helpers exist anywhere in js/ today [VERIFIED: AUD-14 evidence]. No global pass (locked).

**Playwright verification (CONTEXT Q4):** per page — start `bash start-server.sh` (python3 http.server on :8080 from dnallm-mark/), navigate `http://localhost:8080/{page}.html`, assert (a) zero console errors after load settles, (b) expected containers non-empty (navbar present on all 6, leaderboard/table/chart per page), (c) navigation links resolve (no 404s, submit.html reachable from every page). Evidence = console capture + DOM assertions recorded per page. Playwright plugin (previously used) + CLI 1.64.0 both available; Phase 1 precedent used headless-chromium DOM dumps via the CLI.

### Pattern 5: Quirk-parity ports — exact deltas and the name-drift trap

Legacy registries (inside `if __name__ == "__main__":`, lines 1322-1361) vs current `run_finetune.py` (lines 380-403) [VERIFIED: both files read this session]:

| Registry | Legacy (dnallmmark_pipeline.py) | Current (run_finetune.py) | Port action |
|----------|--------------------------------|---------------------------|-------------|
| `model_not_use_safetensors` | 10 entries incl. `plant-dnamamba-6mer`, NO `PlantGFM` | 10 entries incl. `PlantGFM`, NO `plant-dnamamba-6mer` | **Union fix**: both `plant-dnamamba-6mer` AND `PlantGFM` present (11 total) |
| `models_only_support_fp32` | 4 entries (Jamba-DNA-v1-114M-hg38, CrossDNA 8.1M/71.6M/519M) | identical (CR-01, already ported + contract-tested) | none — parity test extends the existing `test_fp32_only_models_forced_to_full_precision` pattern |
| `deeplearning_models` | 4 entries (enformer-official-rough, space, borzoi-replicate-0, flashzoi-replicate-0) | identical list present | verify usage sites port with it (legacy uses: fix_token_len exemption :998, encode branch :978, :1160) |
| `models_no_char_n` (WR-03 ACGT alphabet) | `deeplearning_models + [PlantCAD2-Small-l24-d0768, PlantCAD2-Medium-l48-d1024, PlantCAD2-Large-l48-d1536, prokbert-mini, prokbert-mini-c, prokbert-mini-long, MutBERT, MutBERT-Multi, megaDNA_updated]`; legacy :1055 `"ACGTacgt|" if model_name in models_no_char_n else "ACGTNacgtn|"` | **ABSENT** — run_finetune.py:732 hardcodes `dataset.validate_sequences(minl=0, maxl=10010, valid_chars="ACGTacgt|")` for ALL models | Introduce the list + conditional: models NOT in the list get `"ACGTNacgtn|"` (N-allowing), list members get `"ACGTacgt|"` |
| `models_with_limited_length` | `{"prokbert-mini": 1027, "plant-dnabert-6mer": 512}` — defined but **NEVER USED** in legacy (grep: definition at :1351 only; AUD-15 called it dead config) | absent | Port **functional**: apply the per-model max_length cap at the max_length-determination block (run_finetune ~:628) — wiring what legacy declared but never wired |
| length-tier rounding (WR-04) | `determine_batch_size(max_length, batch_size)` at :791-811: tiers `<=512: full, <=1024: //2, <=2048: //4, <=4096: //8, <=8192: //16, <=16384: //32, else 1`, each `max(1, batch_size // N)`; called at :1002 before setting per_device batch sizes, with grad_accum scaling `max(1, batch_size // dynamic_batch_size)` | **ABSENT** — current has VRAM-probe `estimate_batch_size` (:210-230) and `estimate_batch_size_by_model_params` (:231-307), no length-tier initial cap | Port the tier table as the INITIAL batch cap by sequence length (composable with the VRAM estimator), preserving the `max(1, …)` floor and the grad_accum compensation |

**Name-drift trap (verified live):** legacy list entries do NOT all exist in the unified 62-entry registry — `PlantCAD2-Large-l48-d1536` → registry renamed to `PlantCAD2-Large`; `prokbert-mini-c`, `probert-mini-long`, `MutBERT` → NOT in registry (dropped at unification; registry carries `prokbert`, `prokbert-mini`, `MutBERT-Multi`). The ported lists must use CURRENT registry name forms and omit dead names; the parity contract test compares against the legacy lists **modulo the documented rename/drop mapping** (blind copy equality would fail or, worse, resurrect dead names). The existing parity pattern to extend [VERIFIED: tests/test_run_finetune_contracts.py:237-255]: regex-extract the list from both sources, assert membership — extend with the rename map.

### Pattern 6: The remaining xfail locks (WR-02, WR-03) and same-commit pin flips

Both locks carry "Phase 4 fix" reasons and Phase 2/3 docs route them to Phase 4 (see Open Question 2 for scope confirmation):

- **WR-02** (`test_compare_reports_equal_value_bool_int_cross_type`): `baseline/compare.py`'s walk() BOOL branch reports only `if a != b` — `True` vs `1` compares equal and stays silent [VERIFIED: baseline/compare.py:88-92]. Fix: report when types differ (`isinstance(a, bool) != isinstance(b, bool)`) even at equal value. Live risk per the lock: the 47 pinned task files carry bf16/fp16 booleans.
- **WR-03** (`test_nonfinite_metric_excluded_from_ranking`, 3 params nan/inf/-inf): `summarize_comparison.get_float` passes non-finite floats through [VERIFIED: script/summarize_comparison.py:91-96]. Fix: after `float(val)`, `if not math.isfinite(result): return default`. **Same-commit obligation:** `tests/test_aggregation.py` pins TODAY's pass-through as plain assertions and its module docstring says so verbatim [VERIFIED: tests/test_aggregation.py:15-18] — those pins flip to isfinite semantics in the same commit, and the lock's 3 markers come off.

### Anti-Patterns to Avoid
- **Blind legacy-copy parity:** porting quirk lists verbatim resurrects dead model names (MutBERT, prokbert-mini-c/-long) and misses the PlantCAD2-Large rename — parity is modulo the documented name mapping.
- **Fallback joins:** a species lookup that silently falls back to the file value on a registry miss re-creates the defect class — hard-fail instead.
- **Unmark-without-fixture-fix / fixture-fix-without-unmark:** strict xfail fails the suite on XPASS, and the companion fails if the fixture loses shape — the three-part commit is enforced by the tests themselves.
- **Emitter leaking "Multiple":** the raw Category value must never reach task_performance output (schema enum rejects it); map to majority arena at the exporter.
- **numpy scalar reprs in diffs:** regenerated values serialize as plain floats (np.float64 subclasses float; json.dump handles it — Phase 1 proved byte-determinism), but diff-tooling reprs can mislead during analysis; compare serialized bytes for the byte-identity claims.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Seed aggregation with CI n-guard | Custom mean/SD/bootstrap | Vendored `aggregate_seeds` @483a35c | Reviewer-facing statistics must match the suite exactly; the n-guard (no CI below 3 seeds, t 3-9, bootstrap ≥10) is a published contract (D-14/SEED-01) |
| Student-t quantile | t-table interpolation / custom ppf | `scipy.stats.t.ppf` | Numerical correctness; the suite uses scipy — parity requires it |
| JSON contract validation | Hand-rolled shape checks in Python | `jsonschema` (already in dev group) | The 4 Phase 2 schemas exist; the exporter output must validate against them |
| Alias/canonical metric resolution | Ad-hoc string munging | The explicit mapping table keyed on the VENDORED 28-name registry surface | The registry's resolution rules (case-sensitive, one-directional aliases) are subtle; the table + parity tests encode them once |
| Metric-enum drift | Manual enum edits | SC-6 data≡enum self-check (extend `test_schemas.py` pattern) | `test_metric_enum_matches_committed_data` already proves the pattern [VERIFIED: tests/test_schemas.py:130-153] |

**Key insight:** every statistics/contract primitive this phase needs already exists in the repo or the suite at a pinned revision — the phase is wiring and vendoring, not invention.

## Runtime State Inventory

Not a rename/refactor/migration phase in the graph-state sense, but data regeneration occurs. Applicable categories:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data (committed derived JSON) | 4 `models_comparison*.json` regenerate; 2 byte-identical, 2 changed 42/42 (previewed) | Aggregation-diff inventory in the fix commit (SC-1) |
| Stored data (committed task files) | 2 committed task_performance files carry species values that differ from Category (EPI_GM12878=Microbe→Animals, fungi_species_20=Animals→Microbe) | Open Question 4 — regenerate now (own diff inventory) or leave until E2' |
| Live service config | None — static site, no backend | — |
| OS-registered state | None | — |
| Secrets/env vars | None touched | — |
| Build artifacts | None — no installs beyond scipy (uv.lock re-resolve, definition-only) | — |

## Common Pitfalls

### Pitfall 1: The strict-xfail unmark ordering
**What goes wrong:** fixing the defect without touching the marker makes the suite FAIL (strict XPASS); fixing the fixture without the code fix makes the lock lie green.
**Why:** `xfail(strict=True)` is designed exactly to force the same-commit discipline.
**How to avoid:** one commit = code fix + fixture correction + marker removal + regenerated data + inventory (SC-1's three-in-one, literally).
**Warning signs:** CI red with XPASS errors; companion test red after a fixture edit.

### Pitfall 2: The masked-defect unmasking order (AUD-09 → AUD-10)
**What goes wrong:** fixing only the navbar crash reveals garbage rows ("info"/"performance" as dataset names, N/A metrics) on finetuning/datasets pages — "every page renders" becomes true while "every page works" is false.
**Why:** AUD-10's nesting misreads sit downstream of the crash in setup() and were never observable.
**How to avoid:** land AUD-10's four site fixes in the same plan as the navbar fix, before the Playwright pass.
**Warning signs:** Playwright zero-console-error pass succeeds while tables render two nonsense rows.

### Pitfall 3: CWD-relative scripts
**What goes wrong:** `summarize_comparison.py` and `get_task_performance.py` read `model_performance/` against CWD — running from repo root writes outputs to the wrong place.
**Why:** historical design (documented in CLAUDE.md; Phase 2's REL-04 `make data` chains this correctly).
**How to avoid:** regenerate via the established chain (make data / from `dnallm-mark/data/`); the exporter should be repo-root-runnable with explicit paths (match `baseline/compare.py`'s explicit-path convention) — planner decides whether export_runs.py breaks the CWD convention deliberately (documented) or follows it.
**Warning signs:** outputs appearing outside `dnallm-mark/data/`.

### Pitfall 4: The scipy surprise
**What goes wrong:** vendoring `aggregate_seeds` without adding scipy → ImportError at first test run (scipy is NOT in the dev/data env — import fails live today).
**Why:** the function's only non-numpy import is `scipy.stats`; nobody noticed because the suite was never imported CPU-side.
**How to avoid:** `uv add --group data "scipy>=1.15.2"` in the same commit as the vendored copy (suite-matching floor), uv.lock re-resolved; legitimacy-check SUS verdict is signal-absence (null downloads/repo in the probe) — checkpoint:human-verify per protocol.
**Warning signs:** first `make test` after vendoring fails on ModuleNotFoundError.

### Pitfall 5: The parametersBlock gap
**What goes wrong:** the exporter emits task_performance-shaped files that FAIL schema validation — `parametersBlock` requires 9 training-param keys (`batch_size, bf16, epochs, fp16, gradient_accumulation_steps, learning_rate, lr_scheduler_type, steps, warmup`) that run_record.json simply does not carry.
**Why:** the F2 record contract captured metrics + provenance, not training args (vram_probe holds those keys as nulls by design).
**How to avoid:** decide the join explicitly (Open Question 5) BEFORE writing the emitter; whichever source is chosen, the exporter test must validate output against the real schema.
**Warning signs:** schema validation failing only on parameters keys.

### Pitfall 6: Lint-scope debt on every touched file
**What goes wrong:** Phase 4 edits `summarize_comparison.py`, `baseline/compare.py`, new `export_runs.py` — none are in `make lint` scope today (`tests/ script/make_dev_splits.py pipeline/run_finetune.py pipeline/run_sweep.py`) [VERIFIED: Makefile:68].
**Why:** Phase 3's D-08 discipline widened scope to every file it touched; Phase 4 must do the same or new findings hide outside the gate.
**How to avoid:** lint scope grows to include convert_registry.py (IN-08, locked) + every script Phase 4 touches; ruff-zero is self-evidenced by the gate passing.
**Warning signs:** ruff findings appearing only when someone runs ruff manually on script/.

### Pitfall 7: Mixed-casing metric enums
**What goes wrong:** the task_performance `info.metric` enum is `["f1", "mcc", "spearmanr", "AUPRC"]` — data-surveyed, NOT normalized (three lowercase suite-canonical forms + one uppercase).
**Why:** Phase 2 surveyed committed data verbatim (the tasks.json metric-casing history from Phase 1 research).
**How to avoid:** the exporter maps the datasets_info `metric` column through the same mapping table when emitting info.metric; do not "normalize" the enum casing — the frontend and self-checks pin it, and SC-6 requires same-commit enum+data updates for any change.
**Warning signs:** schema enum failures on regenerated info blocks.

### Pitfall 8: Dual navbar sources drift
**What goes wrong:** five pages each keep their own renderNavbar copy (finetuning/models/datasets/submit have inline copies today) — the Submit link or active-state logic drifts per page.
**Why:** copy-paste page-controller pattern with no shared renderer.
**How to avoid:** one shared renderNavbar (config-driven, active-state from pathname) used by all 6 pages; the CONTEXT locks "the 5 REAL pages" for the fix — sharing the renderer is the natural implementation.
**Warning signs:** navbar renders differently across pages in the Playwright pass.

## Code Examples

### The species switch (summarize_comparison.py edit site)
```python
# Source: derived from tests/test_known_defects.py:79-91 (_load_category_map — same join)
# and script/summarize_comparison.py:335-339 (the site being replaced)
REGISTRY = REPO_ROOT / "pipeline" / "datasets_info.json"
MAJORITY_ARENA = {"Multiple": "Animals"}   # CONTEXT Q4; review-list annotated

def load_arena_map():
    """{Dataset_name: arena} — Category with Multiple resolved to majority arena."""
    with REGISTRY.open("r", encoding="utf-8") as fh:
        registry = json.load(fh)
    return {
        name: MAJORITY_ARENA.get(entry["Category"], entry["Category"])
        for name, entry in registry.items()
    }

# in the dataset loop — replaces species = str(ds_meta.get("species", ...)):
arena = arena_map[dataset_name]   # KeyError = unregistered dataset = hard fail,
                                  # never a silent fallback
dataset_species_map[dataset_name] = arena
```

### The mapping table skeleton (script/export_runs.py)
```python
# Source: suite registry surface verbatim from
# git show 483a35c:dnallm/tasks/metric_registry.py (_RAW_REGISTRY), and the
# legacy producer precedent at pipeline/dnallmmark_pipeline.py:1273-1285.

# Suite canonical names @483a35c (vendored surface for key-parity tests):
SUITE_CANONICAL = frozenset({
    "accuracy", "precision", "recall", "f1", "f1_micro", "f1_weighted",
    "f1_samples", "precision_micro", "precision_weighted", "precision_samples",
    "recall_micro", "recall_weighted", "recall_samples", "mcc",
    "matthews_correlation", "AUROC", "AUPRC", "AUROC_ovr", "AUROC_ovo",
    "TPR", "TNR", "FPR", "FNR", "mse", "mae", "r2", "pearsonr", "spearmanr",
})

# canonical -> export metricBlock slot; unmapped canonicals emit ""
CANONICAL_TO_EXPORT = {
    "accuracy": "accuracy", "precision": "precision", "recall": "recall",
    "f1": "f1", "mcc": "mcc", "AUROC": "auroc", "AUPRC": "auprc",
    "mse": "mse", "r2": "r2", "pearsonr": "pearson_r", "spearmanr": "spearman_r",
}
# pipeline-produced (non-registry) keys with export slots:
PIPELINE_KEYS = {"eval_loss": "loss", "train_runtime": "runtime", "FLOPs": "FLOPs"}
```

### escapeHTML util (js/data.js)
```javascript
// Bounded application: navbar / submit / task renderers this phase touches ONLY.
escapeHTML(str) {
  if (typeof str !== 'string') return str;
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
},
```

### Quirk-parity contract test extension (extends tests/test_run_finetune_contracts.py:237-255 pattern)
```python
# Legacy -> registry rename/drop mapping the parity test applies before comparing
LEGACY_NAME_MAP = {
    "PlantCAD2-Large-l48-d1536": "PlantCAD2-Large",   # renamed at unification
    # dropped at unification — must NOT be ported:
    # "prokbert-mini-c", "prokbert-mini-long", "MutBERT"
}
def test_safetensors_membership_is_legacy_union():
    active = members(active_src, "model_not_use_safetensors")
    legacy = members(legacy_src, "model_not_use_safetensors")
    # union: legacy had plant-dnamamba-6mer (current dropped it);
    # current added PlantGFM (legacy lacked it) — both must be present
    assert set(active) == (set(legacy) | {"PlantGFM"})
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Per-model `{model}_performance.json` assembled by the training pipeline | Per-cell `run_record.json` (F2) + separate offline exporter | Phase 3 (REV-02) | Producer no longer assembles leaderboards; export is a pure function of records + registries |
| Species from producer string (model organism) | Category column of unified datasets_info.json | Phase 3 D-10 unification → Phase 4 consumes it | Human-verified single source; committed-data regeneration now safe |
| Suite metrics read ad-hoc (`test_results.get("eval_AUROC", "")`) | Frozen suite metric registry (28 canonicals, one-directional aliases) | Suite revision 483a35c (metric_registry.py NEW) Mapping layer has a definitive key surface to pin against |
| `metric_key_map` local in summarize main() + mirror in tests | Exporter-owned single table; mirror deleted | This phase (IN-03) | One authority; parity tests both directions |

**Deprecated/outdated:**
- `pipeline/dnallmmark_pipeline.py` — deprecated (F10), retained read-only as the behavioral reference for quirk parity; never executed.
- `script/get_task_performance.py`'s input side — retires per SC-2/CONTEXT Q2 (see Open Question 6 for the file's disposition: the pivot logic's output side is the schema the exporter must match).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | iDNA_ABF 5mC/6mA majority-species arena is **Animals** (basis: committed files already say Animals; cross-species composition) | Species fix / Q4 mapping | Wrong arena → 2 datasets move arenas → animal/microbe diffs grow beyond the previewed inventory; the maintainer review list (Q2) is the designed catch — confirm before regenerating |
| A2 | Under `load_best_model_at_end: True` + `eval_strategy: "steps"`, HF Trainer (transformers 5.17.0) merges eval metrics into `train()`'s return, so real `final_metrics.json` will carry `eval_*` task metrics | Exporter input | If not, run records at E2' lack task metrics and the exporter has nothing to map; mitigation: `run_finetune.py:804` `trainer.evaluate()` return is discarded today — capture it if needed (code-only edit, but touches run_finetune — planner gates it) |
| A3 | The vendored 28-name registry list is the parity oracle (live registry import impossible CPU-side) | Mapping layer | If the suite registry changes before E2', parity is against a stale surface — mitigated by source-annotation @483a35c and the suite's own frozen-surface design; revisit at E2' |
| A4 | WR-02 (comparator bool/int) and WR-03 (get_float non-finite) are Phase 4 scope (lock reasons say "Phase 4 fix"; Phase 2/3 docs route them here) though the 16 CONTEXT answers don't name them | Locks | If descoped, their markers stay (suite stays green as xfail) — no breakage, but the locks' "Phase 4 fix" promise reads stale; planner confirms with maintainer |
| A5 | `space` (card-absent, `<500M`) and `SPACE` (complete card, 589M) are distinct models (both in registry with different operational data) — verified structurally, semantics assumed | Card fills | If they are duplicates, a 62-entry invariant breaks mid-fill; contract test catches immediately |
| A6 | Unmapped suite canonicals (f1_micro, AUROC_ovr, TPR…) map to `""` (14-key contract unchanged) rather than extending the metricBlock enum this phase | Mapping layer | If a Phase 4 test task actually emits one, SC-6 enum extension lands instead — both paths are designed; no schema breakage either way |
| A7 | scipy's SUS verdict is a probe-signal artifact (null downloads/repo), not evidence of risk — suite-pinned, 25-year-old NumFOCUS package | Package audit | None practically; checkpoint:human-verify satisfies the protocol |

## Open Questions (RESOLVED — all 7 dispositioned at planning time)

> Resolution map (recorded 2026-10-10 after checker verification): OQ1→D-12 (parametersBlock = config-YAML join, schema unchanged) · OQ2→D-13 (WR-02/WR-03 fixed+unmarked in 04-01) · OQ3→D-14 (AUD-11/12 include-with-flexibility) · OQ4→04-05 Task (2-file species correction + tasks.json, ordered after pivot retirement) · OQ5→04-01 Task 3 (IN-01 label) · OQ6→04-05 (get_task_performance.py deleted, assertions folded) · OQ7→04-02 (freeze_snapshot path parameterized).

1. **Exporter parametersBlock sourcing (blocking design decision)**
   - What we know: task_performance schema requires 9 training-param keys; run_record.json carries none (vram_probe holds 4 of them as nulls by design).
   - What's unclear: join from `finetune_config.yaml` + sweep manifest? extend run_record at the producer (touches run_finetune/run_sweep — code-only, allowed)? relax the schema?
   - Recommendation: source from the config YAML + per-cell provenance noted in the exporter docstring, and validate output against the UNCHANGED schema (schema relaxation would ripple to the 47 committed files). Flag for maintainer sign-off in the plan.

2. **WR-02/WR-03 scope confirmation**
   - What we know: both locks say "Phase 4 fix"; Phase 2 REVIEW-FIX deferred them "to Phase 4 together with the WR-03(P1)/IN-01(P1) comparator work"; the 16 CONTEXT answers don't mention them.
   - What's unclear: whether the maintainer intends them inside this phase's budget.
   - Recommendation: include both (small, fully mapped fixes with same-commit pin flips — Pattern 6); confirm at plan review.

3. **AUD-11 (sort state) / AUD-12 (listener loss) scope**
   - What we know: audit routed both to "Phase 4 scope"; they are interaction defects (static-verified-only), not render blockers; CONTEXT Q4's verification is render+console focused.
   - What's unclear: whether "every page works" includes sorting/modal interactions.
   - Recommendation: include as a bounded interaction-fix plan item IF the Playwright pass can assert them cheaply (click sort header → order changes); otherwise explicitly descope with maintainer sign-off (they are P1 audit findings — silent descoping risks a Phase 5 surprise).

4. **Do the 2 committed task_performance info.species values get corrected now?**
   - What we know: EPI_GM12878 (Microbe→Animals) and fungi_species_20 (Animals→Microbe) in committed task files conflict with Category; the task page displays info.species.
   - What's unclear: regenerate those 2 files now (own diff inventory, schema-valid, task page immediately correct) vs leave until E2'.
   - Recommendation: regenerate now with a 2-file inventory — it is the same class of fix as the comparison files and leaves no known-wrong committed data.

5. **IN-01 label taxonomy choice**
   - What we know: pure-int diffs currently land in FLOAT_BIG (or FLOAT_ULP); the species diff will emit many int diffs (rank, samples, top-K).
   - What's unclear: exact new label name (`INT`? fold into `VALUE`?) and whether `--summary-json` consumers (plan gates) need updating.
   - Recommendation: add a distinct `INT` label branch for `int`-vs-`int` pairs (both sides int, values differ); update the docstring vocabulary table same-commit; check `PIN-VALIDATION.md`/gate tooling for label dependencies.

6. **get_task_performance.py disposition after its input side retires**
   - What we know: CONTEXT Q2 retires its input side; the file also carries the pivot semantics (output shape) that test_pivot.py pins (11/9/14 key shape).
   - What's unclear: delete the script + retire test_pivot.py's coverage into exporter tests, or keep as a legacy no-op/documented retiree.
   - Recommendation: delete `script/get_task_performance.py` and fold pivot-shape assertions into test_export_runs.py (the exporter OWNs the shape now); the deprecated-pipeline precedent (F10) applies only to files kept as behavioral references — the pivot's reference role transfers to the schema.

7. **freeze_snapshot surface**
   - What we know: tar + SHA256 + frozen commit hash, tested function, invocation deferred to Phase 6; prior art is `baseline/data-v1.sha256`.
   - What's unclear: which paths it freezes (derived data only? + registries?) and where the artifact lands.
   - Recommendation: parameterize (paths + output dir), freeze `dnallm-mark/data/` derived files by default, hash manifest format matching baseline/data-v1.sha256 convention; pure-function test over a fixture tree.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | all Python work | ✓ | present on PATH | — |
| Python (venv) | scripts/tests | ✓ | 3.13 ([tool.ty] python 3.13) | — |
| numpy / pandas / jsonschema / pytest | data chain + tests | ✓ | 2.5.3 / 2.3.3 / 4.26.0 / 9.1.1 | — |
| scipy | vendored aggregate_seeds | **✗ (not installed)** | — | **None — must add** (`uv add --group data "scipy>=1.15.2"`); probe confirms 1.18.1 resolves |
| Node.js | JS test lane | ✓ | v26.10.0 | — |
| Playwright | FIX-01 live verification | ✓ | CLI 1.64.0; playwright plugin previously used | CLI headless script if MCP unavailable |
| python3 http.server | local serving (start-server.sh) | ✓ | stdlib | npx http-server |
| torch / dnallm | NOTHING this phase (by design) | ✗ (provably absent — D-05 discipline holds) | — | vendoring avoids the need |
| DNALLM repo (/home/forrest/Github/DNALLM) | read-only suite reference @483a35c | ✓ | HEAD 283b14a; 483a35c ancestor; sweep.py/metric_registry.py identical at both | — |

**Missing dependencies with no fallback:** none once scipy is added (planner sequences the uv add before/with the vendored copy).

**Missing dependencies with fallback:** none.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | static site, no auth surface |
| V3 Session Management | no | no sessions |
| V4 Access Control | no | no privileged operations client-side |
| V5 Input Validation | yes | submit.js client-side structural validation of uploaded JSON against the documented schema (FileReader + JSON.parse + shape checks; no eval, no dynamic code); exporter validates inputs against registries/schemas before emission |
| V6 Cryptography | no | SHA256 in freeze_snapshot is integrity, not cryptography-for-security (hashlib stdlib — never hand-roll an algorithm) |

### Known Threat Patterns for static-site + data-PR pipeline

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Stored XSS via merged data PR (model/dataset names interpolated into innerHTML — AUD-14) | Tampering/Elevation | FIX-04 escapeHTML at DOM-build sites this phase touches (bounded per CONTEXT Q3); full hardening explicitly deferred |
| Hostile submit-file content rendered in preview (submit.js interpolates user-entered name/email) | Tampering | escapeHTML on every user-entered string rendered by submit page (in bounded scope — highest-risk site) |
| Path traversal via submitted filenames | Tampering | submit.js already sanitizes branch names (`replace(/[^a-zA-Z0-9_-]/g, '-')` — verified); keep |
| Registry-key injection into sweep/export paths | Tampering | run_sweep argv-list subprocess discipline (T-03-10, landed Phase 3); exporter uses registry keys as dict lookups only, writes under parameterized output dir with the existing `/`→`_` filename sanitization |

## Sources

### Primary (HIGH confidence — read this session)
- `script/summarize_comparison.py` (full read) — species mechanism :335-339/:389-412, metric_key_map :295-305, get_float :91-96
- `tests/test_known_defects.py` (full read) — lock + companion + fixture contract :69-204
- `pipeline/run_sweep.py:1-140` — run_record.json schema verbatim
- `tests/test_sweep.py:66-72,189-205` — SUITE_NATIVE_METRICS fixture contract
- `pipeline/dnallmmark_pipeline.py` — producer defect :1248 verbatim, legacy metric mapping :1273-1285, quirk registries :1322-1361, determine_batch_size :791-811
- `pipeline/run_finetune.py` — current registries :380-403, validate_sequences :732, final_metrics write :787-804
- `git show 483a35c:dnallm/finetune/sweep.py` (read-only) — aggregate_seeds full body, constants, statistics block spec
- `git show 483a35c:dnallm/tasks/metric_registry.py` (read-only) — _RAW_REGISTRY 28 canonical names, alias rules, API
- `git show 483a35c:dnallm/finetune/trainer.py` (read-only) — train() return, evaluate(split) result-JSON contract
- `dnallm/finetune/trainer.py` + `pyproject.toml` at suite HEAD (read-only) — scipy>=1.15.2 pin, files unchanged 483a35c..HEAD
- `schemas/task_performance.json` (full read) — datasetBlock/modelCard/parametersBlock/metricBlock enums and required keys
- `tests/test_registry_unification.py` — TXT_ONLY_MODELS 17-name enumeration verbatim, CARD_KEYS
- `tests/test_run_finetune_contracts.py:237-255` — parity contract test pattern
- `baseline/compare.py:70-115` — walk() branches, FLOAT_BIG/BOOL/TYPE semantics (IN-01/WR-02 sites)
- `dnallm-mark/js/{config,main,task,finetuning,models,datasets,submit}.js` + 8 HTML files — navbar audit (grep 0), setup() order, validateJSON misread
- `pipeline/datasets_info.json` (live JSON reads) — 50 Category rows dumped; `pipeline/models_info.json` — card-absent survey, Model_size forms
- Live aggregation-diff preview (this session, /tmp sandbox over the 42 committed files via uv env)
- `AUDIT.md` — AUD-01/09/10/11/12/13/14/15/17 rows with file:line evidence
- `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md` (Phase 4 SC 1-6), Phase 3 `03-VERIFICATION.md`, `03-REVIEW-DISPOSITION.md`, Phase 2 `02-REVIEW-FIX.md` (IN-03 deferral), Phase 1 `01-REVIEW-DISPOSITION.md` (IN-01)
- `Makefile:67-68` (lint scope), `pyproject.toml` (dep groups), `tests/conftest.py` (thread pinning), `tests/test_aggregation.py:15-18` (WR-03 pin docstring)

### Secondary (MEDIUM confidence)
- Playwright plugin availability (~/.claude.json usage record — proves prior use, not current-session wiring)

### Tertiary (LOW confidence)
- None — no web research was needed; every claim traces to in-repo or suite-revision reads

## Metadata

**Confidence breakdown:**
- Species fix design: HIGH — mechanism, lock shape, and diff classes all verified live (preview run)
- Exporter design: HIGH on inputs (suite function + registry + record contract read verbatim); MEDIUM on the parametersBlock resolution (open design decision)
- Frontend: HIGH — every crash/misread site read directly; interaction defects (AUD-11/12) static-verified-only per audit
- Carryovers: HIGH — legacy/current registry deltas diffed name-by-name live

**Research date:** 2026-10-10
**Valid until:** 2026-11-09 (stable repo-internal facts; the suite-revision pin 483a35c is immutable by construction)
