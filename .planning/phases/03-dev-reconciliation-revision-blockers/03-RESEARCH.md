# Phase 3: Dev-Branch Reconciliation & P0 Revision Blockers - Research

**Researched:** 2026-10-09
**Domain:** Git branch reconciliation + Python GPU-training pipeline revision (seed isolation, dev splits, sweep runner) + uv/ty toolchain wiring
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** `git merge origin/dev` into autorun with per-path conflict policy: `dnallm-mark/data/**` and `baseline/` resolve to HEAD (our contract-validated deterministic data + data-v1 baseline discipline); `pipeline/**`, `dnallm-mark/js/**`, `dnallm-mark/index.html`, README take the dev side (new pipeline + new frontend); `script/**`/`scripts/**`/`pyproject.toml`/`.gitignore` reviewed file-by-file (our determinism fixes vs dev state). — **Reversibility:** costly — the merge commit is the fork's convergence point; redoing it means rewriting history after planning artifacts reference it.
- **D-02:** Merge acceptance = `make test` green on the merged tree with ZERO changes to Phase 2 assets beyond documented necessity (schema bucket counts 42/47/4/1 and the enum≡data self-checks must hold unchanged; if dev's script-side state conflicts with our determinism fixes, OUR fixes win — they are the tested behavior).
- **D-03:** The AUD-01-P0 xfail lock PIVOTS from the pipeline-source AST anchor to an EXPORT-CHAIN CONTRACT assertion: every dataset entry's `species` in a result/performance JSON must equal the dataset's arena category (Animals/Plants/Microbe from datasets_info), never a model organism. Fixture-injectable (no pipeline import, no model run); stays xfail(strict=True) until Phase 4's F3② dataset-side species table lands; the unmarked companion (findable/unique/species-key) is replaced by a companion asserting the contract shape exists in the fixture. The old pipeline anchor test is retired with the deprecation (F10), documented in the same commit.
- **D-04:** Merge takes dev's `js/main.js` (79-line diff) + `index.html`, THEN a targeted review of exactly that diff runs in-phase (against our Phase 1 frontend-audit file:line baseline for the same file) before Phase 4 frontend work begins — findings route to Phase 4's list.
- **D-05:** PIPE-02 (GPU env build) and PIPE-03 (two-model E2E) are DEFERRED until the DNALLM suite stabilizes. What still lands as code: the `pyproject [gpu]` dependency-group definition (versions per the verified combo torch 2.11.0+cu130 / transformers 5.17.0 / dnallm from local clone — NOT installed), and PlantHelixSeek's models_info entry (metadata from its model card — serves AUD-05 groundwork). Dataset double-nesting normalization defers with the E2E (only needed before runs). — **Reversibility:** reversible.
- **D-06:** E2' (Phase 5 three-seed re-run) stays gated: F1 → F2 → E2'; with model runs deferred, Phase 5's F6/F9/F7 code work may proceed independently of E2' timing.

### Claude's Discretion
- Merge mechanics (single merge commit vs. path-checkout steps) and conflict resolution order; a merge-conflict inventory table lands in the plan's acceptance evidence.
- run_finetune.py reading pass during reconciliation: no behavioral edits (that is F1/F2's job), but a correctness read of the G1/G2 claims at L516/L584-598 vs actual code is cheap and de-risks F2's fix.
- Datasets double-nesting: normalization command documented (not executed) for the future E2E gate.

### Deferred Ideas (OUT OF SCOPE)
- PIPE-02 GPU env BUILD + PIPE-03 two-model E2E — until DNALLM suite stabilizes (D-05); models do not run this phase
- Dataset double-nesting normalization — with the E2E gate (command documented, not executed)
- E2' three-seed full re-run — Phase 5, gated on F1/F2 (+ suite stability)
- WR-01(P1) gitleaks token-pinning, IN-01(P1) comparator label — Phases 4/5 as recorded
- Suite-side work (IA³, from_scratch) — lives in the DNALLM repo, not here
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REV-01 (F1) | Dev-split generation for the 18 Dev-empty tasks (stratified 10% from train, seed=42, datasets_info Dev columns updated) + checkpoint selection refuses silent test fallback | The exact 18 tasks enumerated (identical on HEAD and dev); CSV format `sequence,label` verified on disk; the silent fallback located in `dnallm/finetune/trainer.py:234-241` (suite-side, read-only — the refusal guard must live in `run_finetune.py`); both registries (`.json` + `.txt`) must be updated; sklearn/numpy split options analyzed |
| REV-02 (F2) | Multi-seed sweep — seed-isolated output dirs fixing G1 (resume never skips a different seed), sweep runner (model×task×seed) with per-run records and failure manifest; VRAM-probe state semantics documented per seed | G1 confirmed at `run_finetune.py:516-517` (seed-agnostic `trainer_state.json` skip; outdir has no seed component at L512); a NEW G2-class config leak found (grad_accum mutation persists across datasets, L584-598); run_record schema proposal aligned with Phase 4 REV-03 exporter needs; dry-run mode design makes the runner testable CPU-side under D-05 |
| REV-10 (F10) | Old pipeline deprecation header + README names `run_finetune.py` as benchmark entry point | Old pipeline has no module docstring (starts `import os`); README names `dnallmmark_pipeline.py` at L154 (usage) and L318 (structure tree); D-03 anchor retirement couples to this commit |
| PIPE-02 (metadata-only part) | `pyproject [gpu]` group definition lands as code, NOT installed | Existing `[pipeline]` group conflicts with the named `[gpu]` deliverable; torch cu130 pinning pattern verified against uv docs (`[[tool.uv.index]]` explicit + `[tool.uv.sources]`); dnallm bounds `torch>=2.4.0,<2.12` / `transformers>=4.49.0,<6` verified from the local clone — combo fits |
| PIPE-03 (metadata-only part) | PlantHelixSeek's models_info entry lands as metadata (AUD-05 groundwork) | Registry entry shape verified from dev's CrossDNA entries (11 keys); TWO registries exist — `models_info.json` (metadata) and `models_info.txt` (what `run_finetune.py` actually reads); model-card source for the entry's fields is an open input |
</phase_requirements>

## Summary

Phase 3's merge is far more mechanical than the planning context assumed — and one of its assumptions is inverted. The real merge-base of autorun and `origin/dev` is **bf98dff** (not a44d310): main already merged dev at bf98dff via PR #5 (a44d310), and autorun forked after that. Since bf98dff, dev added exactly two commits (808d61e CrossDNA, c6b3137 run_finetune.py) touching **only 5 pipeline files + 57 data files**. A `git merge-tree --write-tree HEAD origin/dev` dry-run yields **exactly 51 content conflicts, all inside `dnallm-mark/data/`** (47 task_performance + 4 models_comparison — precisely the both-sides-modified set). Zero conflicts in pipeline/, js/, README, script/, scripts/, pyproject, .gitignore, tests/, schemas/, Makefile — the D-01 "file-by-file review" bucket is **empty** because dev changed none of those paths. The frontend corollary: dev's js/main.js "79-line diff" is **already in our tree** — it is autorun's own commit 8d99daf (log10/linear scatter toggle), reverse-viewed through the a44d310 diff. D-04's "take dev's js" resolves to "keep ours" mechanically; its targeted review reviews commit 8d99daf against the Phase 1 audit baseline.

The P0 code work is well-scoped by direct code reading. **G1 confirmed:** `run_finetune.py:512` builds `{root}/{model}/{dataset}/` with no seed component and `:516-517` skips on `trainer_state.json` existence — seed 2 silently skips after seed 1. **G2-class NEW finding:** `configs["finetune"].gradient_accumulation_steps` is mutated in place (L593/L598) and re-read at L584 on the next dataset — a per-task setting leaks across the dataset loop (the old pipeline's "batch config leak" defect class, reborn). **F1's silent test fallback is suite-side:** `dnallm/finetune/trainer.py:234-241` picks `test` as eval set when no dev split exists — under the read-only constraint on the DNALLM clone, the refusal guard must land in `run_finetune.py` (our repo). The **18 Dev-empty tasks** are enumerated identically in both registries (16 binary + 2 multiclass; the `.txt` encodes them as `Dev=0` with CRLF line endings). ty wiring is empirically solved: with `environment.extra-paths=["script","baseline"]` mirroring the conftest sys.path contract and `replace-imports-with-any` for GPU-only imports, **ty 0.0.85 reports zero diagnostics on the entire tree** — `make typecheck` can gate from day one with no suppression backlog.

**Primary recommendation:** Execute the merge as: `git merge --no-commit origin/dev` → resolve the 51 data conflicts with `git checkout --ours` → `git rm` dev's 6 added data files (3 CrossDNA performance JSONs, `models_comparison_human.json`, 2 gene_exp task files — required to hold the 42/47/4/1 bucket pins) → verify `git diff <pre-merge-HEAD> HEAD -- dnallm-mark/data` is empty and `make test` green (136 passed + 5 xfailed baseline confirmed). Then land F1/F2/F10 as surgical edits to the merged `run_finetune.py`, the D-03 pivot as a fixture-injectable contract test, `[gpu]` replacing the `[pipeline]` group, and ty in the dev group with a `typecheck` Makefile target.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Branch reconciliation (merge, conflict policy) | VCS (git) | — | Content-level decisions only; no runtime component |
| Benchmark training execution (run_finetune.py) | Offline pipeline (GPU workstation) | — | Single synchronous process per run; outside CI forever (GB10 aarch64, local dnallm clone) |
| Dev-split generation (F1) | Offline data prep (CPU, pandas) | — | CSV carving on local dataset files; runs this phase (data prep ≠ model run) |
| Sweep orchestration (F2 runner) | Offline pipeline driver | — | Subprocess driver over run_finetune.py; needs dry-run mode to be CI/CPU-testable |
| Run records / failure manifest | Offline artifacts → Phase 4 exporter input | — | Written by pipeline, consumed by REV-03; schema coordinated now |
| Contract tests (schemas, xfail locks) | Test harness (pytest, CPU) | — | The merge-acceptance instrument; fixture-injectable, never imports torch/dnallm |
| Derived leaderboard data | Static files (committed) | — | Regenerated only via `make data`; merge policy keeps HEAD bytes |
| Type/lint toolchain (ruff + ty) | Dev toolchain (uv-managed) | CI (Phase 5) | `uv run --group dev` invocation pattern already established |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| ty | 0.0.85 | Python type checker (Astral, Rust) | Maintainer directive; empirically zero-diagnostics baseline on this tree; beta — pin via uv.lock [VERIFIED: PyPI registry, uploaded 2026-10-06] |
| ruff | 0.16.10 | Linter (already wired, Phase 2) | Current latest on PyPI matches the pyproject floor `ruff>=0.16.10` [VERIFIED: PyPI registry] |
| uv | 0.12.23 | Env/lock manager | Already the project's carrier; `--group dev` invocation is the established Makefile pattern [VERIFIED: local `uv --version`] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| scikit-learn | 1.9.1 | `train_test_split(stratify=..., random_state=42)` for F1 dev splits | If maintainer prefers the battle-tested stratified sampler over a ~20-line numpy hand-roll (see Don't Hand-Roll) |
| numpy | (pinned in uv.lock) | Fallback stratified sampler; already in `data` group | Deterministic per-class permutation sampling if sklearn is declined |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| scikit-learn stratified split | numpy hand-rolled per-class sampler | Hand-roll avoids a new `data`-group dep (scipy chain) and makes the rounding/rare-class policy explicit and testable; sklearn hides remainder-allocation details but is battle-tested — planner/maintainer decision |
| mypy / pyright | ty | Maintainer directive names ty; ty is 10-100x faster and uv-native; beta status is the cost |

**Installation:**
```bash
uv add --dev "ty>=0.0.85"          # lands in [dependency-groups].dev next to ruff
# scikit-learn only if chosen:
uv add --group data "scikit-learn>=1.9"
uv lock                             # after the [gpu] group edit — tracked uv.lock stays in sync
```

**Version verification (this session, PyPI registry):** ty 0.0.85 (2026-10-06, requires-python >=3.8, repo github.com/astral-sh/ty); ruff 0.16.10 (2026-10-01); scikit-learn 1.9.1 (2026-09-10, requires-python >=3.11).

## Package Legitimacy Audit

| Package | Registry | Age (latest release) | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| ty | PyPI | 2026-10-06 (project pre-1.0 since 2025) | seam signal null | github.com/astral-sh/ty | SUS (too-new heuristic) | Approved — maintainer-directed; Astral-official (docs.astral.sh/ty); beta caveat below |
| ruff | PyPI | 2026-10-01 | seam signal null | docs.astral.sh/ruff | SUS (too-new heuristic) | Already in use since Phase 2 — heuristic false positive; no action |
| scikit-learn | PyPI | 2026-09-10 | seam signal null | seam reported none | SUS (too-new heuristic) | Flagged — planner adds checkpoint:human-verify before adding to `data` group (optional dep; numpy fallback exists) |

**Packages removed due to SLOP verdict:** none.
**Packages flagged as suspicious [SUS]:** scikit-learn (optional — only if the sklearn split route is chosen). ty and ruff carry SUS verdicts solely because the seam's download signal is null in this environment and its too-new heuristic keys off the latest release date; both are Astral-official tools with maintainer directive behind them. **ty operational caveat (real):** ty is pre-1.0 and "does not yet have a stable API; breaking changes, including changes to diagnostics, may occur between any two versions" [CITED: github.com/astral-sh/ty] — exactness must come from uv.lock, and version bumps must be deliberate.

## Architecture Patterns

### System Architecture Diagram

```
                         MERGE (one-time, costly to redo)
  autorun HEAD ──────────┐
  (Phase 1/2 assets:     │  git merge origin/dev
   schemas/ tests/       ├──────────────────► MERGED TREE ──► make test green (gate)
   Makefile baseline/    │   data/** → HEAD (51 conflicts --ours;
   data-v1 discipline)   │   6 dev-added data files git rm'd;
  origin/dev @ c6b3137 ──┘   pipeline/** (5 files) → dev side
                          F10: deprecate dnallmmark_pipeline.py; README → run_finetune.py;
                          D-03: AST lock retired, export-chain contract lock pivoted in

  F1 (CPU, this phase)                    F2 (code this phase; runs deferred by D-05)
  ┌──────────────────────┐                ┌────────────────────────────────────┐
  │ datasets_info(.json  │ enumerate 18   │ sweep runner (model×task×seed)     │
  │ +.txt) ──► split     │ Dev-empty      │   --dry-run: matrix + records only │
  │ generator (seed=42,  │ tasks          │   real mode: subprocess per run    │
  │ stratified 10%)      │                │     cwd=pipeline/ (config is       │
  │   ▼                  │                │     CWD-relative!)                 │
  │ dev.csv per task +   │                │   ▼ per {model}/{task}/seed_{seed}/│
  │ Train/Dev counts in  │                │   trainer_state.json (per-seed     │
  │ BOTH registries      │                │   resume marker) + final_metrics   │
  │ + refusal guard in   │                │     + run_record.json (REV-03 feed)│
  │ run_finetune.py      │                │   + sweep manifest / failures.json │
  └──────────────────────┘                └────────────────────────────────────┘

  Toolchain: [dependency-groups] dev += ty; Makefile += typecheck;
             [pipeline] group → [gpu] (torch==2.11.0 cu130-index-sourced,
             transformers==5.17.0, NOT installed; CI never installs it)
```

### Merge Conflict Inventory (the D-01 application, empirically derived)

Merge-base: `bf98dff` (`git merge-base HEAD origin/dev`). Dry-run: `git merge-tree --write-tree HEAD origin/dev` (git 2.43).

| Path group | Dev-side change since bf98dff | Conflict? | D-01 policy → resolution |
|---|---|---|---|
| `dnallm-mark/data/task_performance/*.json` (47) + `models_comparison{,_animal,_plant,_microbe}.json` (4) | regenerated (CrossDNA included, non-deterministic writer) | **YES — all 51 content conflicts are exactly these** | data/** → HEAD: `git checkout --ours` |
| `dnallm-mark/data/model_performance/CrossDNA_{8.1M,71.6M,519M}_performance.json` | ADDED (3 files) | no (clean addition) | data/** → HEAD ⇒ **`git rm`** (else model_performance bucket = 45 ≠ pinned 42) |
| `dnallm-mark/data/models_comparison_human.json` | ADDED | no | **`git rm`** (comparison bucket = 5 ≠ pinned 4; "human" arena also outside the fixed all/animal/plant/microbe taxonomy) |
| `dnallm-mark/data/task_performance/plant-genomic-benchmark__gene_exp.{arabidopsis_thaliana,oryza_sativa}_task_performance.json` | ADDED (2 files) | no | **`git rm`** (task bucket = 49 ≠ pinned 47) |
| `pipeline/run_finetune.py` | NEW, 737 lines | no | pipeline/** → dev: take as-is |
| `pipeline/models_info.json` | +41/−5 (CrossDNA entries; 44 models total) | no | take dev (PlantHelixSeek entry added on top in-phase) |
| `pipeline/dnallmmark_pipeline.py` | 11 lines: metric-key renames + CrossDNA fp32 list | no | take dev (deprecation header added on top in-phase, F10) |
| `pipeline/datasets_info.txt`, `pipeline/models_info.txt` | NEW (TSV registries the new pipeline reads) | no | take dev |
| `dnallm-mark/js/main.js`, `index.html`, `css/charts.css` | **dev changed NOTHING since bf98dff** | no | Stays ours. The "79-line dev diff" from planning docs is a44d310-relative — those changes predate the fork and are already in our tree; the only js delta vs dev is OUR commit 8d99daf (log10/linear toggle) |
| `README.md`, `script/**`, `scripts/**`, `pyproject.toml`, `.gitignore`, `tests/`, `schemas/`, `Makefile`, `baseline/`, `.planning/**` | dev changed NOTHING | no | D-01's file-by-file review bucket is **EMPTY** — no dev-side state to weigh against our determinism fixes |

[VERIFIED: `git merge-tree --write-tree` + `git diff --name-only bf98dff..HEAD` / `bf98dff..origin/dev` cross-computation, this session]

**Post-merge acceptance evidence (per D-02 + Claude's discretion):**
1. `git diff <pre-merge-HEAD> HEAD -- dnallm-mark/data` → must be **empty** (data tree byte-identical to data-v1 discipline).
2. `make test` → 136 passed + 5 xfailed + node 2 passed (pre-merge baseline re-confirmed green this session in 1.4s). The bucket pins and enum self-checks mechanically enforce the data tree:
```python
EXPECTED_BUCKET_SIZES = {
    "model_performance": 42,
    "task_performance": 47,
    "models_comparison": 4,
    "tasks_index": 1,
}
```
[VERIFIED: tests/test_schemas.py:100-105]
3. The merge-conflict inventory table above lands in the plan/commit message.

**D-04 correction (important):** dev's js/main.js does not arrive via this merge — there is nothing to "take from dev." The targeted review reviews **commit 8d99daf** (our log10/linear scatter X-axis toggle, +58/−19 lines in js/main.js with +6 index.html and +16 charts.css) against the Phase 1 frontend-audit baseline; findings route to Phase 4's list, exactly as D-04 intended. The review's object changes; the review still happens.

### Recommended Project Structure (additions this phase)

```
pipeline/
├── run_finetune.py        # merged from dev; F1 guard + F2 seed-isolation edits land here
├── run_sweep.py           # NEW (F2): model×task×seed matrix driver, --dry-run mode, run records
├── datasets_info.txt      # merged from dev; Dev column updates (F1); CRLF endings preserved
├── datasets_info.json     # ours (dev unchanged); Dev/Train column updates (F1)
├── models_info.json       # merged from dev (44); + PlantHelixSeek entry (PIPE-03 metadata)
├── models_info.txt        # merged from dev; + PlantHelixSeek row (recommended, see OQ-5)
├── dnallmmark_pipeline.py # dev side + deprecation header (F10)
script/
└── make_dev_splits.py     # NEW (F1): stratified 10% dev-split generator (seed=42)
tests/
├── test_known_defects.py  # D-03 pivot: AST lock retired, export-chain contract lock added
└── test_dev_splits.py     # NEW: split determinism + stratification + rare-class policy
```

### Pattern 1: Seed-Isolated Output Dirs (F2/G1 fix)
**What:** Insert the seed into the output-dir layout so the resume marker becomes seed-scoped.
**When to use:** The single surgical change at the outdir construction site.
**Example (current code, verbatim):**
```python
            # Source: pipeline/run_finetune.py @ origin/dev c6b3137, lines 510-517
            save_root = output_dir if output_dir else "./finetuned"
            model_save_name = save_model_name if save_model_name else model_name
            outdir = f"{save_root}/{model_save_name}/{dataset_name}/"
            os.makedirs(outdir, exist_ok=True)
            configs["finetune"].output_dir = outdir

            if os.path.exists(outdir + "trainer_state.json"):
                continue
```
Change L512 to `f"{save_root}/{model_save_name}/{dataset_name}/seed_{seed}/"` — the L516-517 skip then resumes per (model, task, seed) and G1 is dead (resume never skips a different seed). `seed` is already in scope (`args.seed`, L334). Note `set_seed(seed)` runs once at L375 before the loops — correct for a per-invocation seed; the sweep runner varies it per invocation.

### Pattern 2: run_record.json (F2 writes; REV-03 Phase 4 consumes)
**What:** Per-run record inside each `seed_{seed}/` dir, carrying **suite-native** metric keys.
**When to use:** Any run the sweep runner drives (including dry-run mocks for tests).
**Why suite-native keys:** REV-03's deliverable is an *explicit* suite-registry↔export-key mapping layer with key-parity tests — pre-mapping in F2 would duplicate that layer and defeat its design. The key drift is real and already visible: dev renamed the old pipeline's reads from `eval_auroc`→`eval_AUROC`, `eval_pearson_r`→`eval_pearsonr` etc. [VERIFIED: git diff bf98dff..origin/dev -- pipeline/dnallmmark_pipeline.py].
**Proposed shape (deterministic per Phase 2 discipline — `sort_keys=True, indent=4, ensure_ascii=False`):**
```json
{
  "model": "plant-dnamamba-6mer",
  "task": "PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation",
  "seed": 42,
  "status": "completed",            // completed | failed | skipped
  "output_dir": "finetuned/plant-dnamamba-6mer/PlantCAD2.../seed_42",
  "metrics": { /* verbatim final_metrics.json keys, untranslated */ },
  "vram_probe": { "gpu_mem_total": 0.0, "init_max_mem": 0.0, "batch_size": 0,
                  "gradient_accumulation_steps": 0 },   // REV-02 "VRAM-probe state semantics documented per seed"
  "git_commit": "<repo HEAD at launch>",
  "started_at": "...", "finished_at": "...",
  "error": null                      // failure-manifest entry when status=failed
}
```
Timestamps in run records are runtime observations (never regenerated, never diffed) — distinct from the no-live-clock rule for regenerated data-chain outputs (Phase 1 learning). Sweep-level `sweep_manifest.json` holds the matrix definition + per-run statuses, iterated in `sorted()` order.

### Pattern 3: D-03 Export-Chain Contract Lock (fixture-injectable)
**What:** Replace the AST anchor lock with an assertion over a *fixture* result JSON.
**When to use:** Same commit as the F10 retirement of the old anchor (D-03 requires same-commit documentation).
**Design requirements (all load-bearing):**
1. Contract: for every dataset entry, `entry["dataset"]["species"]` must equal the dataset's arena category — drawn from `datasets_info` `Category` column, whose verbatim value set is `{Animals (20), Plants (15), Microbe (13), Multiple (2)}` [VERIFIED: origin/dev pipeline/datasets_info.txt via git show + awk]. The **2 "Multiple" tasks (`iDNA_ABF_datasets__5mC`, `iDNA_ABF_datasets__6mA`)** need an explicit contract decision (see OQ-1).
2. The fixture MUST contain a defect-bearing entry (e.g. `species="athaliana"` or `"human+mouse"` — real model-card values from HEAD's models_info.json distribution: `plants(14), human(9), multi-species(5), human+mouse(4), microbiome(2), eukaryote, prokaryote, brassicales, bacteriophage, virus, athaliana, vertebrate` [VERIFIED: HEAD pipeline/models_info.json via git show]) so the `xfail(strict=True)` lock fails on its defect assertion today — a lock that passes vacuously is a false lock (Phase 2 learning: probe with `--runxfail`).
3. Unmarked companion (outside the marker): asserts the fixture's contract *shape* exists — dataset entries present, `species` key present per entry — so a fixture edit that deletes the defect cannot silently vacate the lock. This adapts the existing companion pattern [VERIFIED: tests/test_known_defects.py:93-127].
4. No pipeline import, no model run — the test never leaves `tests/` + fixtures (mirrors why the AST lock avoided import: torch/dnallm at module level, tests/test_known_defects.py:52-55).

### Pattern 4: F1 Dev-Split Generator
**What:** CPU-only script carving stratified 10% dev splits from train.csv for the 18 Dev-empty tasks.
**Inputs verified this session:**
- The 18 tasks (identical in `datasets_info.json` on HEAD and dev — Dev falsy in JSON, `Dev=0` in TSV):

| # | Task | Train | type |
|---|------|-------|------|
| 1 | Deep4mC_datasets__C.elegans_4mC | 84927 | binary |
| 2 | Deep4mC_datasets__D.melanogaster_4mC | 126467 | binary |
| 3 | Deep4mC_datasets__E.coli_4mC | 8682 | binary |
| 4 | Genomic_Benchmarks__coding | 75000 | binary |
| 5 | Genomic_Benchmarks__human_vs_worm | 75000 | binary |
| 6 | Genomic_Benchmarks__regulatory_region_type | 150000 | multiclass |
| 7 | NT_downstream_tasks__H3K27ac | 30000 | binary |
| 8 | NT_downstream_tasks__H3K27me3 | 30000 | binary |
| 9 | NT_downstream_tasks__H3K4me2 | 30000 | binary |
| 10 | NT_downstream_tasks__H3K9me3 | 27438 | binary |
| 11 | NT_downstream_tasks__enhancers | 30000 | binary |
| 12 | NT_downstream_tasks__splice_sites_acceptors | 30000 | binary |
| 13 | NT_downstream_tasks__splice_sites_all | 30000 | multiclass |
| 14 | NT_downstream_tasks__splice_sites_donors | 30000 | binary |
| 15 | iDNA_ABF_datasets__5mC | 2344 | binary |
| 16 | iDNA_ABF_datasets__6mA | 18336 | binary |
| 17 | iPro-WAEL_datasets__Promoter_R_capsulatus | 7407 | binary |
| 18 | plant-genomic-benchmark__poly_a.arabidopsis_thaliana | 170835 | binary |

[VERIFIED: pipeline/datasets_info.json on HEAD and origin/dev via git show — Dev-empty sets are byte-identical across both refs]
- CSV contract: header `sequence,label` (verified by reading `pipeline/datasets/Deep4mC_datasets/E.coli_4mC/train.csv` header; same layout as `DNADataset.load_local_data(..., seq_col="sequence", label_col="label", ...)` at run_finetune.py:611-617).
- On-disk datasets exist locally under `pipeline/datasets/` (spot-verified: Deep4mC tasks carry only train.csv+test.csv — no dev.csv — confirming the split is genuinely missing on disk).
**Both registries must be updated:** `datasets_info.txt` (what run_finetune.py reads via `pd.read_table` at L316 — note **CRLF line endings**, preserve them) AND `datasets_info.json` (the old pipeline's registry; still the metadata source for the committed performance JSONs' dataset sub-dict). Train counts reduce by the carved dev rows — update `Train` too, since run_finetune.py computes logging/eval steps from `num_train_data = int(row["Train"])` (L582). The committed data tree is NOT regenerated this phase (no runs) — registry/dataset-sub-dict divergence until data-v2 is expected and should be documented.
**Refusal guard (F1 part 2):** in run_finetune.py, when `row["Dev"]` is falsy, hard-refuse (loud error) instead of proceeding — because the suite silently evals on test:
```python
        # Source: /home/forrest/Github/DNALLM/dnallm/finetune/trainer.py:234-241 (READ-ONLY clone)
        eval_key = [x for x in self.data_split if x not in ["train", "test"]]
        if eval_key:
            eval_dataset = self.datasets.dataset[eval_key[0]]
        elif "test" in self.data_split:
            eval_dataset = self.datasets.dataset["test"]
        else:
            eval_dataset = None
            self.training_args.eval_strategy = "no"
```
With train+test only, `eval_key` is empty and `eval_dataset = test` → `metric_for_best_model` checkpoint selection optimizes on test. The DNALLM repo is under parallel maintainer revision and is READ-ONLY for us — the guard lands in OUR file (run_finetune.py), before `data_dict` construction (L520-529).

### Pattern 5: [gpu] Dependency Group (PIPE-02 metadata-only)
**What:** Replace the existing `[pipeline]` group with the named `[gpu]` deliverable (two overlapping GPU groups is drift; REL-02 wants exactly one CI-never-installed GPU group).
**Current state [VERIFIED: pyproject.toml:23-28]:**
```toml
pipeline = [
    # GPU-only, NEVER installed in CI (REL-02). dnallm itself is deliberately absent —
    # it is installed from the local dev clone in Phase 3 (PIPE-02).
    "torch>=2.0",
    "transformers>=4.0",
]
```
**Target pattern (uv + PyTorch cu130, per official uv docs [CITED: docs.astral.sh/uv/guides/integration/pytorch]):**
```toml
[dependency-groups]
gpu = [
    # GPU-only, NEVER installed in CI (REL-02). Definition lands Phase 3; the BUILD
    # is deferred (D-05). dnallm stays deliberately absent — installed from the local
    # dev clone when runs resume (../DNALLM, branch `revision`).
    "torch==2.11.0",
    "transformers==5.17.0",
]

[[tool.uv.index]]
name = "pytorch-cu130"
url = "https://download.pytorch.org/whl/cu130"
explicit = true

[tool.uv.sources]
torch = [
  { index = "pytorch-cu130", marker = "sys_platform == 'linux' or sys_platform == 'win32'" },
]
```
Exact pin `torch==2.11.0` + cu130 index resolves to the `2.11.0+cu130` local-version wheel. Bounds check against the local dnallm clone (0.7.1, branch `revision`): `torch>=2.4.0,<2.12` and `transformers>=4.49.0,<6` [VERIFIED: /home/forrest/Github/DNALLM/pyproject.toml:64-66 via read-only grep] — the verified combo fits both. After the edit, run `uv lock` (resolution-only, CPU-safe, no install) so the tracked uv.lock stays in sync. `default-groups = ["data"]` already prevents accidental gpu installs.

### Pattern 6: ty Wiring (maintainer directive)
**What:** ty joins ruff in the dev group; Makefile gains `typecheck`; config in pyproject.
**Empirically verified baseline (this session, `uvx ty@0.0.85`):**
- Default run over `script/ baseline/ tests/ scripts/`: **7 diagnostics, all `unresolved-import`** for `summarize_comparison` / `get_task_performance` / `compare` — the tests' sys.path-injection imports (conftest inserts `script/` and `baseline/` at tests/conftest.py:33-35).
- With `environment.extra-paths=["script","baseline"]`: **"All checks passed!"** — zero diagnostics.
- Adding `pipeline/` with `analysis.replace-imports-with-any=["torch.**","dnallm.**","transformers.**","peft.**","datasets.**"]`: **still zero errors.**
**Recommended config:**
```toml
[tool.ty.environment]
python-version = "3.13"                      # repo floor (requires-python >=3.13)
extra-paths = ["script", "baseline"]         # mirrors tests/conftest.py sys.path contract

[tool.ty.analysis]
replace-imports-with-any = ["torch.**", "dnallm.**", "transformers.**", "peft.**", "datasets.**"]
# GPU-side imports, never installed CPU-side; substitution keeps ty green without lying about types

[tool.ty.src]
include = ["script", "baseline", "tests", "scripts", "pipeline"]
```
**Makefile target (mirrors the established lint pattern [VERIFIED: Makefile:58-59]):**
```makefile
typecheck:
	$(UV) run --group dev ty check
```
Config keys verified against the official reference [CITED: docs.astral.sh/ty/reference/configuration/]: `[tool.ty.rules]` (rule → ignore/warn/error), `[[tool.ty.overrides]]` per-file globs (later overrides take precedence), `terminal.error-on-warning` (default true — exit 1 on warnings-only), `output-format` incl. `github`/`junit` for Phase 5 CI. ty officially supports checking code targeting Python 3.10+ [CITED: github.com/astral-sh/ty].

### Anti-Patterns to Avoid
- **Taking dev's 6 added data files in the merge** — they are clean additions (no conflict marks), so `git merge` includes them silently; the bucket-pin tests are the only thing that catches it, at test time instead of merge time. Resolve deliberately with `git rm` and prove with the empty-diff check.
- **Resolving the 51 data conflicts by hand-editing** — these are machine-generated JSONs; `git checkout --ours` + the empty-diff verification is the only sane resolution.
- **Pre-translating metric keys in run_record.json** — duplicates REV-03's mapping layer and moves key-parity risk into F2 where it has no tests.
- **Editing anything under /home/forrest/Github/DNALLM** — the clone is under parallel maintainer revision and strictly read-only for this project (coordinator constraint, 2026-10-09). Suite-side findings (the eval fallback) become notes + guards in OUR files.
- **Running `uv sync` with the gpu group** — D-05 forbids the install; `uv lock` (resolve-only) is the allowed operation.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Stratified sampling (F1) | Custom remainder-allocation loop | `sklearn.model_selection.train_test_split(stratify=, random_state=42)` OR a minimal per-class numpy sampler with explicit, tested rounding/rare-class policy | Remainder allocation and class-minimum edge cases are where hand-rolls silently break; sklearn is battle-tested but adds a dep to the `data` group (scipy chain) — planner/maintainer decision, numpy fallback documented |
| Type checking | ad-hoc mypy config | ty in dev group (pattern above) | Maintainer directive; empirically zero-baseline here |
| cu130 wheel pinning | `pip install torch==...+cu130` imperative installs | uv `[tool.uv.sources]` + explicit index (Pattern 5) | Declarative, lock-carried, marker-gated; CI never touches it |
| Merge-conflict resolution of generated JSON | Manual union edits | `git checkout --ours` + `git diff` empty proof | 51 machine-written files; manual edits are unauditable |

**Key insight:** This phase's risk is concentrated in *decisions about generated files* (data tree) and *one-line surgical edits* (outdir seed component; Dev guard) — both are places where hand-rolling anything larger multiplies review surface against the "surgical fixes only" constraint.

## Runtime State Inventory

> Phase includes a merge/migration — inventory completed across all 5 categories.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Committed derived data tree `dnallm-mark/data/**` (42+47+4+1 files, data-v1 discipline); NO databases, no external datastores | Merge policy keeps HEAD bytes; 6 dev-added files excluded; verified empty post-merge diff is the evidence |
| Live service config | None — static site, no backend/API (hosting model constraint); no dashboards/registrations reference branch state | None — verified by repo architecture (no service configs exist) |
| OS-registered state | None found in repo — no cron/systemd/pm2/launchd references anywhere in tracked files | None (nothing OS-registered by this repo; no rename of external identifiers occurs) |
| Secrets/env vars | `HF_HOME`/`MS_CACHE_HOME` set at runtime by run_finetune.py (L22-31, overridable via `--cache_dir`); Zenodo preview token = intentional (REL-05, settled Phase 1); no secrets affected by the merge | None — env names unchanged; `[gpu]` group adds no secrets |
| Build artifacts / installed packages | `.venv/` (uv-managed, python 3.13); tracked `uv.lock` goes stale the moment pyproject gains ty + `[gpu]` — every `uv run` would re-resolve | `uv lock` after the pyproject edit (same commit); `__pycache__` noise excluded by existing .gitignore |

**Nothing found in category:** explicitly none beyond the tabulated items — data category holds the only state that the merge touches.

## Common Pitfalls

### Pitfall 1: The merge is cleaner than planned for — over-thinking it introduces risk
**What goes wrong:** Plans built on the a44d310 conflict-surface map expect js/README/script/pyproject conflicts and frontend takeover work; the real merge-base is bf98dff and dev touched none of those.
**Why it happens:** `git diff a44d310..origin/dev` shows the world *as dev sees it from main's fork point*, inverting our own changes (8d99daf's 79 lines appear as dev's "diff").
**How to avoid:** Trust the merge-tree dry-run inventory above; verify post-merge with the empty-data-diff check + `make test`.
**Warning signs:** Anyone hand-resolving a js/main.js hunk in this merge — there is none to resolve.

### Pitfall 2: dev's clean data additions slip in (bucket pins catch it late)
**What goes wrong:** The 6 added data files arrive without conflict markers; `make test` fails later at `test_schema_bucket_counts_are_pinned` with "found 45 files, expected 42".
**Why it happens:** git treats additions on one side as clean merges.
**How to avoid:** `git rm` them during resolution; the empty-diff check makes it impossible to miss.

### Pitfall 3: CWD sensitivity, again — run_finetune.py is finetune_config-relative
**What goes wrong:** `configs = load_config("./finetune_config.yaml")` (L378), `./logs/` (L412) and default `./finetuned` (L510) resolve against CWD, while datasets/models registries are script-relative (`base_dir`, L315-319). Running from repo root breaks config load; running from pipeline/ works.
**Why it happens:** Same disease the data scripts had pre-REL-04, inherited into the rewrite.
**How to avoid:** The sweep runner (F2) must launch subprocesses with `cwd=pipeline/` and/or pass `--output_dir` absolutely; document the invocation contract. (Fixing the script's own path handling is a behavioral edit — outside the sanctioned reading pass; route as a finding.)
**Warning signs:** `FileNotFoundError: ./finetune_config.yaml` in any runner log.

### Pitfall 4: TSV registry CRLF endings
**What goes wrong:** The F1 registry update rewrites `datasets_info.txt` with LF endings; the diff explodes and downstream byte-comparisons shift.
**Why it happens:** The file has CRLF line endings [VERIFIED: `cat -A` shows `^M$` on every row].
**How to avoid:** Write updates preserving CRLF (or normalize deliberately in a standalone, flagged commit — never bundled).

### Pitfall 5: False-lock vacuity in the D-03 pivot
**What goes wrong:** The pivot fixture uses only healthy arena-category species values; the xfail lock passes vacuously... no — worse: an xfail(strict=True) lock whose body *passes* becomes an XPASS and FAILS the suite, forcing someone to delete the marker without the contract being real.
**Why it happens:** Committed data today already looks arena-like in spots (e.g. `species='Microbe'` for GUE emp_* datasets).
**How to avoid:** Fixture MUST contain a model-organism value (`"athaliana"`, `"human+mouse"`) per Pattern 3; probe with `pytest --runxfail` (Phase 2 learning) before landing.

### Pitfall 6: uv.lock drift after pyproject edits
**What goes wrong:** Adding ty + the `[gpu]` group without `uv lock` leaves the tracked lock stale; later `--frozen`/CI runs drift or fail.
**How to avoid:** `uv lock` in the same commit as the pyproject edit.

### Pitfall 7: ty version churn (pre-1.0)
**What goes wrong:** A casual `uv lock --upgrade` bumps ty across a breaking diagnostics change; `make typecheck` goes red for tool reasons.
**How to avoid:** Treat ty bumps as deliberate (like ruff); the lock pins exactness.

## Code Examples

### G1 site + seed fix (the whole defect in 6 lines)
```python
# Source: pipeline/run_finetune.py @ origin/dev c6b3137:510-517 (verbatim current code)
save_root = output_dir if output_dir else "./finetuned"
model_save_name = save_model_name if save_model_name else model_name
outdir = f"{save_root}/{model_save_name}/{dataset_name}/"   # ← no seed component (G1)
os.makedirs(outdir, exist_ok=True)
configs["finetune"].output_dir = outdir

if os.path.exists(outdir + "trainer_state.json"):           # ← seed-agnostic resume skip
    continue
```

### G2-class config leak (NEW finding — route to maintainer/F2)
```python
# Source: pipeline/run_finetune.py @ origin/dev c6b3137:584-598 (verbatim)
grad_accum = configs["finetune"].gradient_accumulation_steps   # re-reads MUTATED state
# In case memory insufficient or effective_batch_size is specified
if effective_batch_size is not None:
    ...
    configs["finetune"].gradient_accumulation_steps = required_grad_accum   # in-place mutation
    grad_accum = required_grad_accum
    print(...)
elif bs_new == 1 and grad_accum == 1:
    grad_accum = 4
    configs["finetune"].gradient_accumulation_steps = grad_accum            # in-place mutation
```
`configs["finetune"]` is loaded once per model (L378) and mutated per dataset; nothing resets `gradient_accumulation_steps` between datasets. If dataset A hits the `bs_new==1` branch (grad_accum→4), dataset B silently trains with grad_accum=4 regardless of its own batch size — the old pipeline's "batch config leak" defect class (AUDIT P0 #2) reborn in the rewrite. CONTEXT sanctions a correctness READ (no behavioral edits) — the fix decision belongs to the plan (it is sweep-correctness-adjacent: per-task config must not leak across a matrix run).

### The silent test-eval fallback (F1's adversary — suite-side, read-only)
See Pattern 4 quote: `/home/forrest/Github/DNALLM/dnallm/finetune/trainer.py:234-241`.

### Dev-split guard placement
```python
# Insert before the data_dict block at run_finetune.py:520-529 (which reads,
# verbatim: if row["Dev"]: val_path = dataset_path + "/dev.csv"; data_dict["dev"] = val_path)
if not row["Dev"]:
    raise SystemExit(
        f"[REFUSED] {dataset_name} has no dev split (datasets_info Dev=0); "
        "dnallm would select test as the eval set and checkpoint selection "
        "would optimize on test. Generate dev splits first (script/make_dev_splits.py)."
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pipeline = `dnallmmark_pipeline.py` (JSON registries, FLOPs hooks, monolith) | Pipeline = `run_finetune.py` (TSV registries, `--category`/`--task_index` filters, auto batch by model params, NPU support, effective_batch_size, gradient checkpointing) | dev c6b3137 (merged this phase) | Old pipeline deprecated (F10); NOTE: run_finetune.py has **no FLOPs instrumentation and no performance-JSON exporter** — both were old-pipeline features; the exporter gap is REV-03/Phase 4 scope, the FLOPs gap is beyond this milestone's requirements |
| AST-anchor xfail lock on pipeline source | Fixture-injectable export-chain contract lock | This phase (D-03) | Lock survives the old pipeline's deprecation; stays honest via the shape companion |
| `pipeline` dep group (torch>=2.0 loose) | `[gpu]` group, exact cu130-index-sourced pins, lock-carried | This phase (D-05) | REL-02 discipline preserved; CI never installs |
| ruff-only lint | ruff + ty (typecheck) | This phase (maintainer directive) | Zero-baseline empirically; gates from day one |

**Deprecated/outdated:**
- `pipeline/dnallmmark_pipeline.py` — deprecation header this phase (F10); README re-points to `run_finetune.py` (current README references at L154 usage + L318 structure tree [VERIFIED: README grep]).
- The `[pipeline]` pyproject group — superseded by `[gpu]` (recommendation; planner confirms).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `train_test_split(stratify=, random_state=42)` is deterministic for fixed input+version (uv.lock pins the version) | Pattern 4 / Don't Hand-Roll | Split irreproducibility across machines — mitigated by lock pinning; verify with a determinism test anyway |
| A2 | torch 2.11.0+cu130 wheels install on GB10 aarch64 | Pattern 5 | Build failure when runs resume — carried from CONTEXT's maintainer-verified combo, NOT re-verified here (no install allowed, D-05) |
| A3 | PlantHelixSeek model-card metadata is available to the maintainer for the entry fields | Phase Requirements / OQ-3 | Entry cannot land completely this phase — obtain the card (HF/ModelScope) before authoring |
| A4 | Registry Train counts match on-disk CSV row counts for the 18 tasks | Pattern 4 | Split script should verify counts itself and fail loudly on mismatch (cheap guard) — structure spot-checked, counts not |
| A5 | dev's models_info.txt rows cover exactly the 44 JSON entries (incl. paths/tokenizer types) | Pattern 4 / OQ-5 | PlantHelixSeek TXT row authoring needs a Model_path convention — verify at execution |
| A6 | "Multiple"-category tasks are the only Category semantics question for the D-03 contract | Pattern 3 / OQ-1 | Contract test would need rework if other categories appear in a future registry |
| A7 | ruff's broad default rule set in 0.16.10 (no config file exists — verified) will treat run_finetune.py's 16 findings consistently in CI later | Patterns / OQ-6 | Lint-scope decision needed; findings enumerated this session so the decision is informed |

## Open Questions

1. **"Multiple" category semantics in the D-03 contract** — `iDNA_ABF_datasets__5mC`/`6mA` carry `Category="Multiple"` (multi-species datasets). Must species equal the category *literally* (i.e. `"Multiple"` becomes a legal species value), or are these tasks excluded from the strict equality?
   - What we know: the 3-way arena taxonomy {Animals, Plants, Microbe} is the CLAUDE.md-fixed frontend contract; "Multiple" has no arena file.
   - Recommendation: contract test asserts species ∈ {Animals, Plants, Microbe, Multiple} AND species == Category for the fixture's datasets — keeps the lock strict while the Phase 4 species-table work resolves the real mapping.
2. **Fate of the `[pipeline]` group** — replace with `[gpu]` (recommended; one GPU group per REL-02) or keep both?
   - Recommendation: replace; the old group's loose bounds contradict the exact-pin discipline.
3. **PlantHelixSeek metadata source** — the entry's 11 fields (name, size (M), type, tokenizer, mean_token_len, architecture, series, context_len (bp), species, huggingface, modelscope) need the model card.
   - Recommendation: maintainer supplies the card or the HF/ModelScope ID at execution; entry shape follows the CrossDNA pattern verified above.
4. **grad_accum leak routing** — fix inside F2's sanctioned edits or record as a finding for Phase 4? It is per-task config correctness inside the sweep execution path (F2-adjacent) but not literally named by REV-02.
   - Recommendation: surface to maintainer at plan review; the fix is 2-3 lines (snapshot default grad_accum per model, or reset per dataset).
5. **PlantHelixSeek row in models_info.txt** — D-05 names "the models_info entry" (singular); run_finetune.py reads the TSV, the JSON is metadata-only. Landing both costs one line.
   - Recommendation: land both; the TXT row is required for the future E2E anyway.
6. **Lint scope for Phase-3-authored/edited files** — `make lint` is tests/-only (Phase 2 D-04 decision, ~21 deferred production findings). run_finetune.py carries 16 findings under ruff 0.16.10 defaults [VERIFIED: `ruff check --statistics` this session: 3 BLE001, 2 SIM102, 2 F541, 2 PLW1508, 2 I001, 1 each DTZ005/PLR0402/SIM115/FURB192/F401].
   - Recommendation: add Phase-3-authored files (script/make_dev_splits.py, pipeline/run_sweep.py, tests/*) to lint scope; leave merged dev code unlinted (matching the deferred-findings discipline); maintainer's strictness preference may override.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | All Makefile targets | ✓ | 0.12.23 (aarch64) | — |
| Python | Test/toolchain env | ✓ | 3.14.7 system; repo .venv 3.13 (floor >=3.13) | — |
| node | make test JS lane, make data | ✓ | 26.10.0 | — |
| ruff | make lint | ✓ | 0.16.10 (= PyPI latest) | — |
| ty | NEW make typecheck | ✓ (via uvx; 0.0.85 fetched this session) | 0.0.85 | — |
| pipeline/datasets/ CSVs | F1 split generation (this phase, CPU-only) | ✓ (spot-verified: Deep4mC, PlantCAD2 trees present) | — | — |
| DNALLM local clone | API-surface verification only (read-only) | ✓ (branch `revision`, 0.7.1) | — | Suite under parallel revision — do not touch |
| GPU / torch / dnallm install | NOT required (D-05: no model runs) | deliberately absent | — | Deferred with PIPE-02 build |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none applicable (GPU stack intentionally unbuilt this phase).

## Security Domain

> security_enforcement: true (level 1). Phase scope: offline scripts + config only; no network service, no user input path.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth surface (static site, offline scripts) |
| V3 Session Management | no | None |
| V4 Access Control | no | None this phase (no service) |
| V5 Input Validation | yes | Dataset CSVs are external data (Zenodo-sourced): the F1 split script must handle malformed rows/unknown labels defensively (per-file skip with loud report, mirroring `script/` conventions); JSON outputs validated by Phase 2 schemas |
| V6 Cryptography | no this phase | SHA-256 freeze_snapshot arrives with REV-03 (Phase 4) — never hand-roll then either |
| V14 Configuration | yes | The `[gpu]` group + explicit pytorch index is a supply-chain boundary: `explicit = true` confines the extra index to torch only (dependency-confusion mitigation); CI never installs the group (REL-02); ty/ruff are dev-group-only tools |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Dependency confusion via custom index | Tampering | `[[tool.uv.index]] explicit = true` + exact version pins + tracked uv.lock (Pattern 5) |
| Malformed/hostile dataset rows poisoning derived outputs | Tampering | Defensive CSV reads, loud skip-and-report, schema validation of outputs, deterministic regeneration |
| Toolchain supply chain (pre-1.0 ty) | Tampering | Exact pins via uv.lock; deliberate upgrades only |
| Untrusted-input in test fixtures (D-03 fixture) | Repudiation | Fixture is repo-authored test data; merge review covers it |

## Sources

### Primary (HIGH confidence)
- Git object inspection this session: `git merge-tree --write-tree HEAD origin/dev` (conflict inventory), `git diff bf98dff..origin/dev` (dev-side changes), `git show origin/dev:pipeline/run_finetune.py` (full 737-line read), `git show {HEAD,origin/dev}:pipeline/datasets_info.json` (18-task enumeration), `git show origin/dev:pipeline/{models_info.json,models_info.txt,datasets_info.txt}`, `git diff bf98dff..origin/dev -- pipeline/dnallmmark_pipeline.py`
- Local repo Reads: tests/test_known_defects.py, tests/test_schemas.py, Makefile, pyproject.toml, .planning/config, README grep, pipeline/datasets on-disk CSVs
- Local DNALLM clone (READ-ONLY): dnallm/finetune/trainer.py:234-241, dnallm/__init__.py exports, pyproject.toml bounds
- PyPI registry JSON: ty, ruff, scikit-learn (versions, upload dates, requires-python)
- Empirical runs this session: `uvx ty@0.0.85 check` (baseline), `make test` (136 passed + 5 xfailed + node 2 pass), `make lint` (green), `ruff check --statistics` on run_finetune.py (16 findings)

### Secondary (MEDIUM confidence)
- [CITED: docs.astral.sh/ty/reference/configuration/] — ty config schema, overrides, rule severities, output formats
- [CITED: docs.astral.sh/uv/guides/integration/pytorch/] — cu130 index/sources pinning pattern
- [CITED: github.com/astral-sh/ty] — beta status, breaking-change policy, Python 3.10+ target support

### Tertiary (LOW confidence)
- None — no training-data-only claims load-bearing in this research

## Metadata

**Confidence breakdown:**
- Merge surface: HIGH — empirically derived via merge-tree dry-run and both-sides diffs this session
- Pipeline code findings (G1, G2-class leak, fallback, CWD sensitivity): HIGH — full-file read of run_finetune.py + trainer.py with verbatim quotes
- F1 inputs (18 tasks, CSV contract, both registries): HIGH — enumerated from both refs; count-vs-CSV-row spot check remains (A4)
- ty wiring: HIGH — official docs + zero-diagnostics empirical run on this exact tree
- [gpu] group: HIGH on pattern (official docs) / A2 on the GB10 wheel claim (maintainer-carried)
- Stratified split implementation choice: MEDIUM — both options documented; decision open (OQ/A1)

**Research date:** 2026-10-09
**Valid until:** 2026-10-23 (merge surface is commit-pinned — stable while HEAD and origin/dev@c6b3137 do not move; ty version facts valid ~7 days given pre-1.0 cadence)
