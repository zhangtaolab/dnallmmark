# Phase 15: 双卡验证与子数据集 (N=2 Smoke & Small Real Sweep) - Research

**Researched:** 2026-10-20
**Domain:** Dual-GPU dispatch validation, 5% stratified subset generation, real sweep → data-chain consumption
**Confidence:** HIGH (every load-bearing claim verified against live code, on-disk state, or a real probe this session)

## Summary

This box (AutoDL, 2× RTX 5090, returned to 2026-10-20) is the milestone's N=2 validation
machine — but it currently holds **zero benchmark assets**: no model weights anywhere
(HF/ModelScope caches empty, `pipeline/models/` and `pipeline/datasets/` do not exist, the
configured roots `/root/autodl-tmp/dnallmmark-data/{models,datasets}` are empty directories).
Phase 15 therefore needs an explicit **data-acquisition step** before any GPU run: 2 models
(~714 MB + ~750 MB) and 2 dataset tasks via the modelscope CLI. I verified the full download
path live: `modelscope download --dataset forrestzhang/iDNA_ABF_datasets --local_dir <root>
--include "5mC/*"` lands `train/dev/test.csv` whose row counts match the registry EXACTLY
(2110/234/2344), and `--model zhangtaolab/plant-dnabert-6mer --local_dir <dir>` lands a FLAT
model dir (config.json directly in the dir — the `Model_path` contract). All candidate repos
return HTTP 200 from this box.

The single most load-bearing architectural fact: **the child (`run_finetune.py`) always loads
the OFFICIAL registries** (`registry_loader.load_datasets_registry()` / `load_models_registry()`
at `pipeline/run_finetune.py:744,747` — no registry-dir argument, no `--registry-dir` child
flag exists in `build_argv`). `--registry-dir` steers only the SWEEP layer (enumeration,
validation, manifest). Consequently subset datasets MUST be materialized at the
**official-relative `Dataset_path`** under an overridden `--dataset_root`, and the subset
registry must keep **official keys with unchanged `Dataset_path`** (only `Train/Dev/Test`
become measured counts). I proved this exact command shape with a real CPU dispatch dry-run
against a subset-registry fixture: 12 planned cells, per-cell `dataset_root`/`model_root`/
`orchestrator_mode: dispatch` recorded in the manifest — the isolation evidence trail.

**Primary recommendation:** Smoke = plant-dnabert-6mer × iDNA_ABF_datasets__5mC × seeds
42,43 @ 1 epoch (2 cells — D15-02 requires BOTH GPUs to produce cell artifacts, which one
cell can never do). Sweep = plant-dnabert-6mer + plant-dnamamba-6mer × {5mC, GUE__emp_H3}
5% subsets × seeds 42,43,44 @ 1 epoch (12 cells, one dispatch shared root). Consumption =
real `export_runs.py` with `--datasets-info <subset registry>` into temp outputs, then
`summarize_comparison.py` over a tmp data tree (the `test_determinism.py` copytree idiom).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
Copied verbatim from `.planning/phases/15-dual-gpu-validation-subsets/15-CONTEXT.md` `<decisions>`:

- **D15-01:** docs/multi-gpu.md rewritten as the dispatch-mode procedure: dual workers × `--gpus 0,1`, ONE smallest real model×dataset pair from the registries, 1 epoch, real child processes end-to-end
- **D15-02:** Pass criteria: both GPUs produced cell artifacts + dispatch_state.json terminal status "done" + merged-root consumption dry-run passes + the executed procedure is what the docs now say (procedure/doc identity)
- **D15-03:** D-05 revision lands in docs/multi-gpu.md (本机=双卡验证机; the old 开发本机/验证他机 split is retired); WINDOWS #21 closed with evidence links
- **D15-04:** Smoke failure = stop immediately: preserve dispatch_state + tee logs as phase artifacts, route to debug flow; never proceed into VAL-03 with a broken core
- **D15-05:** New offline script `script/make_subset_datasets.py`: reads real dataset dirs → deterministic STRATIFIED 5% sample per split (label-stratified for classification; seed-governed) → writes subset dataset directories + a dedicated subset registry file carrying MEASURED row counts
- **D15-06:** Sampling semantics: per-split independent stratified 5%; splits with <20 rows take min(5%, full) with the actual fraction recorded; run-twice byte-identity is test-pinned
- **D15-07:** Isolation: subset registry/config/output roots are triple-isolated from official AND user-custom registries (e.g. output under `pipeline/finetuned-smoke/`); an assertion proves zero intersection; subset entries are a third registry class, never written into official or custom files
- **D15-08:** Coverage: subsets generated only for the small-sweep's chosen 2-3 datasets (+1 small classification fixture dataset for the stratification unit test)
- **D15-09:** Scale: 2 models × 2 datasets × 3 seeds, 1 epoch — small models (plant-dnabert-6mer class) so the sweep finishes in hours; satisfies the ≈2-4×2-3×3 requirement at its lower bound
- **D15-10:** Run mode: Phase 13/14 dynamic dispatch `--mode dispatch --workers 2 --gpus 0,1`, ONE shared root, NO merge needed (MGPU-06); live view + state file observed during the run
- **D15-11:** Consumption proof: the shared root feeds `script/export_runs.py` (real run, not dry-run) → task_performance → summarize_comparison chain with ZERO chain modifications; produced JSONs archived as phase artifacts
- **D15-12:** All artifacts under /root/autodl-tmp per the disk-capacity policy (model caches already routed; subset dirs and output roots inside the gitignored pipeline/ areas)
- **D15-13:** Executors run real GPU training inside plan tasks (pre-authorized); every run prints its plan (models/datasets/seeds/GPUs/expected outputs) before launching
- **D15-14:** dnallm environment preflight per the standing rule: verify the editable install before any GPU run (`pip show dnallm`); reinstall if a uv sync dropped it
- **D15-15:** Full CPU lanes stay green; GPU-outcome assertions (artifacts exist, measured row counts, terminal state) land in pytest as fake-independent checks reading REAL produced artifacts where the box allows; CI stays zero-GPU (assert on fixture-generated artifacts, not live GPUs)
- **D15-16:** Every real GPU run's command, duration, and artifact SHAs are recorded in the SUMMARY; defects found mid-run go through the normal fix flow

Maintainer authorization (2026-10-20, option A): ALL GPU executions in this phase are
pre-authorized — smoke + small real sweep, inside plan tasks.

### Claude's Discretion
- Exact model/dataset selection for smoke + sweep (smallest-by-size from registries, subject to availability on disk)
- The subset registry file's exact name/location (pipeline/ gitignored area) provided isolation assertions cover it
- Splitting smoke vs sweep across plans/waves

### Deferred Ideas (OUT OF SCOPE)
- TUI multi-GPU surface → Phase 16
- Web error bars → Phase 17
- Docs rewrite beyond multi-gpu.md/README touchpoints → Phase 18
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VAL-01 | docs/multi-gpu.md N=2 smoke executes on local 2×5090 (WINDOWS #21 closed); D-05 revised in-doc (本机=双卡验证机) | Dispatch CLI contract verified (`run_sweep_shard.py --mode dispatch --workers 2 --gpus 0,1`); smoke pair selected (plant-dnabert-6mer × 5mC, the Phase 11/12-proven pair); 2-cell (2-seed) requirement identified from D15-02; docs structure mapped (§"Machine roles (D-05)" line 179, §"9-step" line 200); WINDOWS #21 row located (`.planning/WINDOWS.md` id 21, status open) |
| VAL-02 | 5% sub-datasets pre-materialized as first-class dataset directories — deterministic seed-governed STRATIFIED per split, measured row counts in dedicated subset registry/config, separate output roots; never share registry/config/output root with real runs | Child-official-registry fact verified (the dataset_root-override mechanism); shuffle-then-select precedent read (`apply_train_fraction`, run_finetune.py:507-535); CSV format + label distributions measured (5mC balanced 1055/1055; emp_H3 5821/6150); 5% math computed (105/11/117 and 598/74/74); dispatch dry-run with subset registry fixture PASSED (12 cells, per-cell roots recorded) |
| VAL-03 | Small real sweep (≈2-4 models × 2-3 datasets × 3 seeds, 1 epoch, 5% subsets) completes on both GPUs through dynamic dispatch → merge/data-chain consumption end-to-end with real training | 2×2×3=12-cell plan dry-run-verified; export_runs real-run contract mapped (all flags, defaults, hard-fail joins); chain commands mapped (`make data`, summarize CWD contract, test_determinism tmp-tree idiom); dispatch terminal status vocabulary verified (`running/done/incomplete`, schemas/dispatch_state.json) |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Model/dataset acquisition (downloads) | Offline CLI (modelscope) | TUI data manager (manual alternative) | Executors run scripted `modelscope download` with the live-probed argv; TUI queue is the interactive equivalent, same channel resolution |
| Subset generation (5% stratified) | Offline script (`script/make_subset_datasets.py`) | — | Pure offline transform: real CSVs → subset CSVs + subset registry; stdlib-only, CI-testable |
| N=2 dispatch orchestration | Pipeline orchestrator (`run_sweep_shard.py --mode dispatch` → `dispatch_core.py`) | — | Frozen Phase 13/14 CLI runs VERBATIM; this phase executes it, never modifies it |
| Cell training | Child (`run_finetune.py` via dnallm) | GPU 0/1 (CUDA_VISIBLE_DEVICES per worker) | One cell = exactly one GPU; the child resolves registries/datasets/roots itself |
| Registry views | Sweep layer (`--registry-dir`) | Child layer (official registries + `--dataset_root`) | Two-layer registry reality: subset registry steers enumeration/validation; dataset_root override steers the child's data resolution |
| Data-chain consumption | Offline scripts (`export_runs.py` → `summarize_comparison.py`) | — | Real export over the shared dispatch root; committed `dnallm-mark/data/` is read-only to this phase |
| Docs/ledger closure | docs/multi-gpu.md + WINDOWS.md + PROJECT.md | — | Procedure/doc identity is a pass criterion (D15-02); #21 + D-05 row closures are file edits with evidence links |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| modelscope CLI | 1.40.2 (in `[data]` group, verified in venv) | Model + dataset downloads | The box-validated channel (261015-h8i; live-probed again this session) |
| dnallm (editable) | 1.3.2 from `../DNALLM` branch v1.3 | DNADataset/load_config/load_model_and_tokenizer/DNATrainer | The pipeline's suite dependency; editable install VERIFIED present right now |
| torch | 2.11.0+cu130 | Training + FLOPs hooks | `cuda_available True`, `device_count 2` verified in `.venv` |
| Python stdlib (csv/json/random/argparse) | 3.13.14 | The subset generator | Keep the generator stdlib-only → CI-safe, no new deps |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pandas/numpy/scipy (data group) | locked (uv.lock) | export_runs / summarize chain | Chain consumption runs via `uv run --group data` |
| Node 26 | v26.4.0 | `scripts/generate-tasks-index.js` (optional chain tail) | Only if the consumption proof extends to tasks.json |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| modelscope CLI (models) | TUI KIND_MODEL queue (`MODEL_DOWNLOAD_PROGRAM` via dnallm) | TUI path needs snapshot-nesting normalization; CLI `--local_dir` lands FLAT (verified) — prefer CLI for executor tasks |
| modelscope CLI (datasets) | TUI data-manager enqueue | Same argv underneath; CLI is scriptable and non-interactive |
| Google Drive URLs (GUE primary) | modelscope alternates (`lgq12697/GUE`) | GDrive is unreliable from CN boxes; the alternates are the working channel (verified live) |

**Installation:** none — no new packages. The venv already satisfies everything (`uv sync --group data --inexact` only if regenerating; remember dnallm reinstall rule).

## Package Legitimacy Audit

**No new packages are installed by this phase.** The generator is stdlib-only; downloads use
the already-pinned modelscope 1.40.2 (`[data]` group, box-validated floor per pyproject
comment); the chain uses locked data-group deps. Gate result: nothing to audit, nothing
flagged.

**Packages removed due to SLOP verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Ground Truth on Disk (read-only probes, 2026-10-20)

### What exists
| Item | State | Evidence |
|------|-------|----------|
| 2× RTX 5090 | idle, 32607 MiB each, 0% util | `nvidia-smi --query-gpu` this session |
| `/root/autodl-tmp` free space | 2.0 T available | `df -h` |
| `.venv` (repo) | Python 3.13.14, torch 2.11.0+cu130 CUDA working, modelscope 1.40.2 CLI on `.venv/bin/modelscope` | probed |
| dnallm editable | `pip show dnallm` → Editable project location `/root/autodl-tmp/Github/DNALLM`, v1.3.2; `from dnallm import DNADataset, ...` imports OK | probed |
| `~/.config/dnallmmark/directories.json` | `model_root`/`dataset_root` = `/root/autodl-tmp/dnallmmark-data`, `output_root` = `.../finetuned`, `log_dir` = `.../logs`, `cache_dir` = `/root/autodl-tmp/.cache/hf` | read |
| `~/.config/dnallmmark/custom_models.json` | user custom overlay exists (3 Chaoba private entries, 400M each, no modelscope id) | read |
| HF / ModelScope caches | `/root/autodl-tmp/.cache/hf` (evaluate/metrics/modules only, hub empty), ModelScope cache empty | listed |

### What does NOT exist (blockers for GPU runs until downloaded)
| Item | Consequence |
|------|-------------|
| ANY model weights | neither `pipeline/models/` nor `/root/autodl-tmp/dnallmmark-data/models/` exists as content — both empty/absent; no `*.safetensors`/`pytorch_model.bin` anywhere on either disk (exhaustive find) |
| ANY real dataset CSVs | no `train.csv` outside DNALLM's own `tests/test_data/` fixtures; `/root/autodl-tmp/dnallmmark-data/datasets/` is an empty dir |
| `/root/autodl-tmp/dnallmmark-data/finetuned/` | contains only a leftover Phase-14 dry-run `sweep_manifest.json` (1 planned CrossDNA_519M × GUE__emp_H3 cell, status "planned") — not a real run |

**Conclusion: the phase's first execution wave must download assets.** Probe artifacts
already landed in `/root/autodl-tmp/tmp/ms-probe/` (real 5mC + emp_H3 CSVs — row counts
match registry EXACTLY: 2110/234/2344 and 11971/1497/1497) and can be re-downloaded or
copied to the real roots; they are outside the repo and can be discarded freely.

### Smallest runnable pairs (all verified against registries + compat map)
Adapted (dnllm-adapted) models by size — from `pipeline/dnallm_compat.json` (field
`dnllm_adapted`, 38 of 59 adapted) joined with `pipeline/models_info.json`:

| Model | size (M) | channel / modelscope id | quirks (run_finetune lists) |
|-------|----------|--------------------------|------------------------------|
| hyenadna-large-1m-seqlen-hf | 7 | modelscope-slot `ZhejiangLab-LifeScience/hyenadna-large-1m-seqlen-hf` | model_not_use_safetensors |
| caduceus-ph_seqlen-131k_d_model-256_n_layer-16 | 8 | modelscope-mirror `lgq12697/caduceus-ph_seqlen-131k_d_model-256_n_layer-16` | model_not_use_safetensors |
| prokbert-mini | 21 | modelscope-mirror `lgq12697/prokbert-mini` | models_no_char_n; models_with_limited_length 1027 |
| plant-dnabert-6mer | 89 | modelscope-slot `zhangtaolab/plant-dnabert-6mer` | models_with_limited_length 512 — **Phase 11 bounded-smoke PROVEN (77 s/epoch, 1.56 GB peak on GB10; all six D-23 criteria green)** |
| plant-dnamamba-6mer | 94 | modelscope-slot `zhangtaolab/plant-dnamamba-6mer` | model_not_use_safetensors; download + 2×2 dry-run verified (261014-l6h); never real-trained through this pipeline |

Excluded despite small size: CrossDNA_8.1M (8.1 M) — `dnllm_adapted: false` AND fp32-only;
Shorkie_LM (13 M) — no modelscope id (HF-only).

Smallest datasets: `iDNA_ABF_datasets__5mC` (2110/234/2344 rows, 41 bp, binary f1, ModelScope
`forrestzhang/iDNA_ABF_datasets`), `GUE__virus_species_40` (4000/500/500, multiclass mcc),
`iPro-WAEL_datasets__Promoter_R_capsulatus` (6666/740/3175, binary f1),
`GUE__emp_H3` (11971/1497/1497, 500 bp, binary f1, ModelScope `lgq12697/GUE` alternate).
GUE's primary URL is Google Drive — use the `lgq12697/GUE` alternate (verified reachable).

### Recommended selections (Claude's discretion area, evidence-based)
| Run | Model(s) | Dataset(s) | Seeds | Cells | Rationale |
|-----|----------|-----------|-------|-------|-----------|
| Smoke (VAL-01) | plant-dnabert-6mer | iDNA_ABF_datasets__5mC (full — smallest real task) | 42,43 | 2 | The ONLY pair proven end-to-end through this pipeline (Phase 11 D-04 / docs precedent); 2 cells so BOTH GPUs produce artifacts (D15-02 — one pair × one seed = one cell would idle worker 1 and make the pass criterion unmeetable); full dataset keeps the smoke independent of VAL-02 machinery |
| Sweep (VAL-03) | plant-dnabert-6mer + plant-dnamamba-6mer | iDNA_ABF_datasets__5mC + GUE__emp_H3 (5% subsets) | 42,43,44 | 12 | D15-09 exact scale; BERT + Mamba exercises two FLOPs-counter dispatch families; both zhangtaolab slot-channel (proven downloads); same species group (plants) → `models_comparison_plant.json` exercises the arena chain |

Measured 5% math (from the real CSVs downloaded this session; `int(n*f)` per the
`apply_train_fraction` precedent):

| Split | n | labels | int(n×0.05) | stratified allocation (largest-remainder) |
|-------|---|--------|-------------|-------------------------------------------|
| 5mC train | 2110 | 1055/1055 balanced | 105 | 52/53 |
| 5mC dev | 234 | 117/117 | 11 | 5/6 |
| 5mC test | 2344 | 1172/1172 | 117 | 58/59 |
| emp_H3 train | 11971 | 5821/6150 (48.6/51.4) | 598 | 291/307 |
| emp_H3 dev | 1497 | 735/762 | 74 | 36/38 |
| emp_H3 test | 1497 | 742/755 | 74 | 36/38 |

### Environment preflight facts (D15-14)
- dnallm editable: **currently OK** (verified). Standing rule from project memory: after ANY
  `uv sync` (which prunes it — dnallm is deliberately absent from the lockfile), reinstall
  with `uv pip install -e ../DNALLM` from the repo root before any GPU run.
- pytest collection: 2113 tests collect cleanly (`uv run --group dev --group tui pytest
  --collect-only -q`). Known box baseline: ~1-2 environmental failures (root-user chmod
  simulations; WINDOWS #43 records 7 at Phase 13 incl. a stale about-pin since addressed) —
  expected, not regressions.
- v1.3 push policy (maintainer 2026-10-20): LOCAL COMMITS ONLY; push once at milestone close.

## Architecture Patterns

### System Architecture Diagram

```
                      ┌────────────────────────── Phase 15 execution flow ──────────────────────────┐
                      │                                                                          │
  modelscope.cn ──DL──► model_root/models/{plant-dnabert-6mer, plant-dnamamba-6mer}   (assets step) │
  modelscope.cn ──DL──► dataset_root/datasets/{iDNA_ABF_datasets/5mC, GUE/emp_H3}     (assets step) │
                      │                                                                          │
   real dataset CSVs ─► script/make_subset_datasets.py ──► subset dataset root                     │
                      │        (seed-governed stratified 5% per split)   ({subset_root}/datasets/  │
                      │                                          iDNA_ABF_datasets/5mC/…)        │
                      │                                        + subset registry dir               │
                      │                                          (models_info.json verbatim copies │
                      │                                           + datasets_info.json with        │
                      │                                           MEASURED Train/Dev/Test)         │
                      │                                                                          │
                      │  [VAL-01 smoke]  run_sweep_shard.py --mode dispatch --workers 2          │
                      │       --gpus 0,1 --models plant-dnabert-6mer --tasks 5mC                 │
                      │       --seeds 42,43 --num_train_epochs 1 --output-root finetuned-smoke   │
                      │            │  ONE shared root + dispatch_state.json + claim ledger       │
                      │            ▼                                                            │
                      │  [VAL-03 sweep]  same CLI + 2 models × 2 subset tasks × 3 seeds          │
                      │       + --registry-dir <subset registry> --dataset_root <subset_root>     │
                      │       + --model_root <real model root>  → 12 cells, both GPUs             │
                      │            │                                                            │
                      │            ▼  {root}/{model}/{task}/seed_{k}/ run_record.json +          │
                      │               final_metrics.json + flops_report.json + trainer_state      │
                      │            │                                                            │
                      │  [D15-11 consumption] export_runs.py --input-root <shared root>           │
                      │       --datasets-info <subset registry>/datasets_info.json                │
                      │       --output-dir/--stats-dir/--model-output-dir <TEMP evidence dir>     │
                      │            ▼  {model}_performance.json + {task}_task_performance.json    │
                      │  summarize_comparison.py (cwd = tmp data tree w/ model_performance/)      │
                      │            ▼  models_comparison{,_plant}.json  → archived phase artifacts │
                      └──────────────────────────────────────────────────────────────────────────┘
   committed dnallm-mark/data/  ──READ-ONLY (never written by this phase; tmp-tree idiom)──┘
```

### The registry two-layer reality (the phase's central design constraint)

```
SWEEP layer (run_sweep.py via --registry-dir):
  load_models_registry(registry_dir) / load_datasets_registry(registry_dir)
  → reads {subset registry dir}/models_info.json + datasets_info.json
  → --models/--tasks validation, enumeration, manifest cells, priority tiers
  → custom overlay from custom_registry_dir() STILL merges on top (add-only)

CHILD layer (run_finetune.py — NO registry-dir flag exists):
  datasets_info = registry_loader.load_datasets_registry()   # run_finetune.py:744 — ALWAYS official
  models_info   = registry_loader.load_models_registry()     # run_finetune.py:747 — ALWAYS official
  dataset_path  = dataset_base + row["Dataset_path"]          # :1092
  dataset_base  = --dataset_root flag > directories.json > pipeline/   # :998-999
```

**Therefore:** subset CSVs must live at the OFFICIAL relative `Dataset_path`
(`datasets/iDNA_ABF_datasets/5mC`) under an OVERRIDDEN `--dataset_root`; the subset registry
keeps official keys and official `Dataset_path` values, changing only `Train/Dev/Test` to
measured counts. The child then resolves the same relative path against the subset root and
trains on subset CSVs — with ZERO pipeline code changes (the binding constraint honored).
`--dataset_root`/`--model_root`/`--log_dir`/`--cache_dir` are run_sweep flags threaded
resolved-absolute to every child via `build_argv`'s pinned storage tail and recorded in every
manifest cell (the per-cell isolation evidence).

**Verified end-to-end** this session with a CPU dispatch dry-run over a subset-registry
fixture (2 models × 2 tasks × 3 seeds): exit 0, `[Dry-run] [Dispatch] 12 planned cell(s)`,
one shared-root `sweep_manifest.json`, per-cell
`dataset_root`/`model_root`/`orchestrator_mode: "dispatch"` recorded.

### Recommended artifact layout (D15-07 + D15-12: in-repo, gitignored, /root/autodl-tmp)

```
pipeline/
├── models/…                      # NOT here on this box — real models live at the
│                                 #   directories.json model_root (/root/autodl-tmp/dnallmmark-data/models)
├── datasets-smoke/               # NEW — subset dataset root (generator output; needs .gitignore entry)
│   └── datasets/{iDNA_ABF_datasets/5mC, GUE/emp_H3}/{train,dev,test}.csv
├── registry-smoke/               # NEW — subset registry dir (needs .gitignore entry)
│   ├── models_info.json          # the 2 selected model entries, verbatim copies
│   └── datasets_info.json        # the 2 dataset entries: official keys/paths + measured counts
├── finetuned-smoke/              # dispatch output root (already gitignored, .gitignore:122)
│   ├── sweep_manifest.json
│   ├── dispatch_state.json
│   ├── dispatch_ledger/
│   └── {model}/{task}/seed_{k}/…
└── logs-smoke/                   # NEW optional — --log_dir override (or reuse finetuned-smoke/logs)
```

. gitignore additions needed: `datasets-smoke/` and `registry-smoke/` (two lines, the
`finetuned-smoke/` precedent at `.gitignore:122`). Real dataset downloads land at
`/root/autodl-tmp/dnallmmark-data/datasets/…` (outside the repo, per directories.json).
Models are shared between real and subset runs (only `--model_root` pointing at the real
root) — models are not subsetted, so no model isolation is required beyond the output root.

### Isolation discipline (D15-07 → assertions)
1. Subset registry dir ∉ {`pipeline/` (official), `custom_registry_dir()`} — path inequality,
   asserted in the executed procedure and in pytest.
2. Official + custom registry files BYTE-UNCHANGED by generation: hash
   `pipeline/{models,datasets}_info.json` + `~/.config/dnallmmark/custom_{models,datasets}.json`
   before/after the generator run — strongest form (proves "never written into").
3. Subset dataset root ∩ real dataset root = ∅; smoke output root ∩ directories.json
   `output_root` = ∅ (assert the resolved paths differ).
4. During subset runs, pin `DNALLMMARK_CUSTOM_REGISTRY_DIR` to an empty dir so the child's
   registry view excludes user customs entirely (verified honored by the dry-run — the env
   is read by `registry_loader.custom_registry_dir()`, `pipeline/registry_loader.py:83-89`).
5. Pass `--log_dir <smoke logs>` explicitly: directories.json otherwise seeds the child error
   logs into the REAL log dir (observed in the dry-run manifest cell: `log_dir` =
   `/root/autodl-tmp/dnallmmark-data/logs` when the flag is absent).

### Pattern: the exact smoke/sweep command shapes (verified)

```bash
# Asset acquisition (executors, before any GPU run) — live-probed argv:
modelscope download --model zhangtaolab/plant-dnabert-6mer \
  --local_dir /root/autodl-tmp/dnallmmark-data/models/plant-dnabert-6mer
modelscope download --model zhangtaolab/plant-dnamamba-6mer \
  --local_dir /root/autodl-tmp/dnallmmark-data/models/plant-dnamamba-6mer
modelscope download --dataset forrestzhang/iDNA_ABF_datasets \
  --local_dir /root/autodl-tmp/dnallmmark-data/datasets/iDNA_ABF_datasets \
  --include "5mC/*" --exclude "*.DS_Store"
modelscope download --dataset lgq12697/GUE \
  --local_dir /root/autodl-tmp/dnallmmark-data/datasets/GUE \
  --include "emp_H3/*" --exclude "*.DS_Store"
# post-landing checks: config.json DIRECTLY in each model dir;
# {train,dev,test}.csv in each dataset task dir; row counts == registry.

# VAL-01 smoke (full small dataset, official registry — no subset machinery):
python pipeline/run_sweep_shard.py --mode dispatch --workers 2 --gpus 0,1 \
  --models plant-dnabert-6mer \
  --output-root /abs/path/pipeline/finetuned-smoke \
  --tasks iDNA_ABF_datasets__5mC --seeds 42,43 --num_train_epochs 1 \
  --log_dir /abs/path/pipeline/logs-smoke
# (paths absolute; the child cwd is pinned to pipeline/ and resolves against flags)

# VAL-03 sweep (subset registry + roots; DNALLMMARK_CUSTOM_REGISTRY_DIR=empty dir):
DNALLMMARK_CUSTOM_REGISTRY_DIR=/abs/empty-custom-dir \
python pipeline/run_sweep_shard.py --mode dispatch --workers 2 --gpus 0,1 \
  --models plant-dnabert-6mer,plant-dnamamba-6mer \
  --output-root /abs/path/pipeline/finetuned-smoke \
  --tasks iDNA_ABF_datasets__5mC,GUE__emp_H3 --seeds 42,43,44 \
  --num_train_epochs 1 \
  --registry-dir /abs/path/pipeline/registry-smoke \
  --model_root /root/autodl-tmp/dnallmmark-data \
  --dataset_root /abs/path/pipeline/datasets-smoke \
  --log_dir /abs/path/pipeline/logs-smoke
```

### Pattern: D15-11 consumption proof (zero chain modification)

```bash
# 1. Real export (NOT --dry-run) from the dispatch shared root, outputs into a TEMP
#    evidence dir — never dnallm-mark/data (committed data is read-only to this phase):
uv run --group data python script/export_runs.py \
  --input-root pipeline/finetuned-smoke \
  --models-info pipeline/registry-smoke/models_info.json \
  --datasets-info pipeline/registry-smoke/datasets_info.json \
  --output-dir <TMP>/task_performance --stats-dir <TMP>/seed_stats \
  --model-output-dir <TMP>/model_performance
# (--models-info/--datasets-info are the exporter's OWN documented flags — pointing them at
#  the subset registry gives truthful dataset blocks; NOT a chain modification)

# 2. summarize over a tmp data tree (the test_determinism.py copytree idiom):
cp -r dnallm-mark/data <TMP>/data && rm -rf <TMP>/data/model_performance
cp <TMP>/model_performance/*_performance.json <TMP>/data/model_performance/
cd <TMP>/data && uv run --group data python ../../script/summarize_comparison.py
# → models_comparison{,_plant}.json emitted in the tmp tree; archive as phase artifacts
```

### Anti-Patterns to Avoid
- **Relying on `--registry-dir` alone to point the child at subset data** — the child never
  reads it (run_finetune.py:744,747); without `--dataset_root` the sweep would silently train
  on FULL datasets while the manifest claims subset counts.
- **A 1-cell smoke** (one pair × one seed) — worker 1 idles; "both GPUs produced cell
  artifacts" (D15-02) becomes unmeasurable. Use 2 seeds.
- **Bare invocations without explicit roots** — directories.json seeds
  `output_root`/`log_dir` from the REAL roots (observed in the dry-run manifest). Always pass
  `--output-root` (orchestrator-owned) and `--log_dir` for smoke runs.
- **`--merge` or `--cleanup` on a dispatch root** — dispatch roots need neither (A6 refusal
  fires by design); MGPU-06.
- **Writing anything into `dnallm-mark/data/`** — committed published data; consumption
  outputs go to temp dirs (D-18 discipline).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cell enumeration/argv/manifest | custom sweep loop | `run_sweep_shard.py --mode dispatch` (verbatim) | Frozen Phase 13/14 CLI; binding constraint |
| Dataset/model downloads | wget/curl scripts | modelscope CLI (live-probed argv above) | Resume machinery, include scoping, verified channel |
| Post-run cleanup | `rm -rf` recipes | nothing (dispatch roots need no cleanup) / `--cleanup` only for static roots | MGPU-05/06 |
| Export/aggregation | custom JSON walker | `script/export_runs.py` + `script/summarize_comparison.py` | The D15-11 requirement IS "zero chain modifications" |
| Row-count verification | ad-hoc counting | declared-vs-measured comparison (the n_audit discipline; TUI D-09 precedent) | The generator's measured counts must equal on-disk CSV rows |

**Key insight:** every heavyweight mechanism this phase needs already exists and is
test-pinned; the ONLY new code is `script/make_subset_datasets.py` (+ tests + gitignore/docs
edits). Everything else is execution of existing CLIs.

## Common Pitfalls

### Pitfall 1: The child trains the FULL dataset despite the subset registry
**What goes wrong:** sweep enumerates against the subset registry (measured counts in the
manifest) while the child resolves `Dataset_path` from the OFFICIAL registry against the
default `dataset_base` → full-data training, wrong-by-5% numbers, no error raised.
**Why:** `--registry-dir` is a sweep-layer flag only; `run_finetune.py:744,747` load official
registries unconditionally; `build_argv` has no registry-dir element.
**How to avoid:** subset CSVs at official-relative `Dataset_path` under `--dataset_root`
override (the verified pattern); the sweep assertion step compares per-cell `dataset_root`
in the manifest against the subset root.
**Warning signs:** manifest `Train` counts ≠ what training logs show; epoch step counts
matching full-split sizes (2110 vs 105 steps at bs=1-equivalents).

### Pitfall 2: One-cell smoke proves only one GPU
**What goes wrong:** 1 model × 1 task × 1 seed = 1 cell; worker 1 finds an empty queue and
exits clean; the run "passes" without ever exercising GPU 1.
**How to avoid:** smoke = the pair × 2 seeds (42,43) = 2 cells minimum; assert BOTH
`workers[]` rows in `dispatch_state.json` show a completed in-flight history and both
expected cell dirs exist (the ledger claims record gpu tokens per worker).
**Warning signs:** `counts.total == 1`; only one `dispatch_ledger/` claim referencing one gpu.

### Pitfall 3: `uv sync` silently prunes dnallm
**What goes wrong:** any environment regen drops the editable dnallm; the first GPU cell
dies at `from dnallm import …` after GPU allocation.
**How to avoid:** D15-14 preflight before every GPU wave: `.venv/bin/python -m pip show
dnallm` must show `Editable project location: /root/autodl-tmp/Github/DNALLM`; if missing,
`uv pip install -e ../DNALLM`.
**Warning signs:** `pip show` Location without an Editable project location line.

### Pitfall 4: directories.json seeding leaks real-run paths into smoke runs
**What goes wrong:** absent `--log_dir`, child error logs land in the real log dir (verified:
the dry-run manifest cell carried `log_dir: /root/autodl-tmp/dnallmmark-data/logs`); absent
`--output-root`, a bare `run_sweep.py` would target the real `output_root`.
**How to avoid:** always pass explicit `--output-root` + `--log_dir` (+ `--model_root`/
`--dataset_root` for subset runs) in smoke/sweep commands; assert the smoke output root ≠
directories.json `output_root`.

### Pitfall 5: Subset dev/test splits rounding to zero rows
**What goes wrong:** a tiny split (n<20) at 5% yields `int(n*0.05)=0` rows; a 0-row dev CSV
either crashes the suite (Dev falsy check is registry-side, but a 0-row CSV breaks
DNADataset) or silently skips evaluation.
**Why:** D15-06's "<20 rows take min(5%, full)" needs a concrete floor.
**How to avoid:** per-split floor of 1 row (never 0, never >n); record
`actual_fraction = rows/n` in the subset registry (already the D15-06 requirement).
**Warning signs:** measured Dev == 0 in the subset registry; empty dev.csv.

### Pitfall 6: summarize_comparison CWD sensitivity
**What goes wrong:** running `summarize_comparison.py` from the repo root reads/writes the
wrong `model_performance/` — or worse, overwrites committed comparison JSONs if run inside
`dnallm-mark/data/` with real inputs.
**How to avoid:** always run it inside a tmp copy of the data tree (the test_determinism.py
idiom); never inside the committed `dnallm-mark/data/`.

### Pitfall 7: Model download nesting surprises
**What goes wrong:** `snapshot_download`-based paths (the TUI `MODEL_DOWNLOAD_PROGRAM`) land
weights under `models/<org>--<name>/snapshots/<rev>/…` nesting that violates the flat
`Model_path` contract unless normalized.
**How to avoid:** executor downloads use the modelscope CLI `--local_dir` form — verified to
land FLAT (config.json directly in the target dir). Note: repos carry BOTH
`model.safetensors` AND `pytorch_model.bin` (~2× bytes; plant-dnabert-6mer totals ~714 MB)
— acceptable, or `--include` per file if bandwidth matters.

### Pitfall 8: Second model (plant-dnamamba-6mer) has never real-trained through this pipeline
**What goes wrong:** a Mamba-specific loading/training defect surfaces mid-sweep and looks
like a dispatch failure.
**How to avoid:** D15-04 discipline applies per-run: preserve state + tee logs; defects go
through the normal fix flow (D15-16), never in-phase redesign. Contingency second models
(adapted, mirror channel, verified sizes): GROVER 87 M (BERT family), MutBERT-Multi 85 M,
PlantCaduceus_l24 43 M. The safetensors quirk for dnamamba is already handled
(`model_not_use_safetensors`, run_finetune.py:936).
**Warning signs:** cell fails at model load, not at data/training.

### Pitfall 9: Root-user test failures mistaken for regressions
**What goes wrong:** ~6 chmod-simulating TUI persist-failure tests fail because uid 0
bypasses permissions (documented environmental class; CI passes as non-root).
**How to avoid:** compare failures against the known baseline before diagnosing; record the
box baseline at wave start (WINDOWS #43 precedent).

### Pitfall 10: Procedure/doc identity drift (D15-02)
**What goes wrong:** the executed smoke commands differ from what docs/multi-gpu.md ends up
saying (e.g., doc shows 1 seed, execution used 2).
**How to avoid:** write the doc FROM the executed commands (copy-paste the actual argv +
key outputs into the doc/VERIFICATION); assert identity at verification time.

## Code Examples

### The stratified shuffle-then-select precedent (semantics to extend)
```python
# Source: pipeline/run_finetune.py:528-535 (read this session)
if fraction is None:
    return
if "train" in dataset_dict:
    train = dataset_dict["train"]
    n = len(train)
    dataset_dict["train"] = train.shuffle(seed=seed).select(
        range(int(n * fraction))
    )
```
The subset generator mirrors this discipline per split (train AND dev AND test — D15-06
"per-split independent"), adding label stratification: group row indices by the `label`
column, allocate per class by largest-remainder so the per-split total is exactly
`int(n * 0.05)` (floor 1 for n<20), select per class via `random.Random(seed)`-shuffled
indices, write rows in ORIGINAL FILE ORDER (deterministic, diff-friendly).

### CSV format (verified from the real downloaded datasets)
```text
# /root/autodl-tmp/tmp/ms-probe/datasets/iDNA_ABF_datasets/5mC/train.csv
sequence,label
GCGGCTGGGAGCAGAGTCTACGGGGCACCGAGAGGCAGGTG,1
```
Header `sequence,label` verbatim; labels are plain ints (binary 0/1 here). Write with
`csv.writer(f, lineterminator="\n")` + `newline=""` for byte-identity (no `\r\n` on any
platform, no trailing blank line).

### Terminal-state assertion vocabulary (verified)
```text
# Source: schemas/dispatch_state.json (status enum) + pipeline/dispatch_core.py:1730,1806
"status": {"enum": ["running", "done", "incomplete"]}
```
D15-02's "terminal status 'done'" == `dispatch_state.json` `status == "done"` with
`counts.completed == counts.total`. The state file lives at `{root}/dispatch_state.json`;
the dispatcher's stdout IS the live view (plain-line table, flush=True per write).

### Run-twice byte-identity idiom (test_determinism.py precedent)
```python
# Source: tests/test_determinism.py:154 (chain variant, read this session)
# generator variant: run make_subset_datasets.py twice into two tmp roots (subprocess,
# cwd-pinned), then compare every file byte-for-byte (hash walk over both trees) and
# against a second registry emission — pinned in tests/test_subset_datasets.py
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Static LPT model sharding (`{root}-mgpu-w{i}` sibling roots + `--merge`) | Dynamic dispatch (`--mode dispatch`, ONE shared root, claim ledger, no merge) | Phase 13 (MGPU-01/02/06) | Smoke/sweep use dispatch mode verbatim; merge/cleanup are NOT part of the flow |
| Manual `rm -rf` worker-root cleanup (docs §5 recipe) | `--cleanup` command (static roots only; dispatch roots refuse) | Phase 14 (MGPU-05) | docs/multi-gpu.md §5's tail note must be updated to the dispatch reality (D15-01 rewrite) |
| D-05: 开发本机/验证他机 (validation on the OTHER machine) | 本机 = 双卡验证机 (this 2×5090 box validates) | D15-03 (this phase) | docs "Machine roles (D-05, verbatim)" section (docs/multi-gpu.md:179-187) + the 9-step "OTHER machine" header (:200-206) rewritten; PROJECT.md:100 Pending row → done; WINDOWS #21 → fixed with evidence |
| Smoke procedure = 9-step static-shard, 2 models 1 seed 1 task | Dispatch-mode N=2 procedure, 1 pair × 2 seeds, real children | D15-01/D15-02 | The doc's §1-§6 runbook body largely survives (dispatch CLI documented in-module); the smoke section is replaced by the executed dispatch procedure |

**Deprecated/outdated in-doc items to retire this phase:** the "other machine" framing
(multi-gpu.md:180-187, 200-206), the static-only launch examples pointing at
`finetuned-smoke` worker roots (:211-245), the manual rm -rf recipe (:156-160 → point at
`--cleanup`/dispatch-no-cleanup). Full docs pass stays Phase 18 (DOCS-01/02).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Smoke wall time ≈ 1-3 min/cell on a 5090 (GB10 measured 77 s/epoch for the same pair; 5090 ≥ GB10) | Selections | Low — even 10× slower stays bounded |
| A2 | plant-dnamamba-6mer trains cleanly through dnallm on 5090/CUDA-13 (never real-trained in this repo; download+dry-run verified only) | Selections | A Mamba defect mid-sweep → normal fix flow; contingency models listed (Pitfall 8) |
| A3 | Sweep total ≈ under 1-2 h wall (12 cells × minutes each on 5% splits: 105/598 train rows) | Selections | Low — D15-09 budgets "hours" |
| A4 | D15-06 "<20 rows take min(5%, full)" means floor-of-1-row for 1≤n<20 with actual_fraction recorded (the wording is ambiguous; my reading keeps every split non-empty) | Pitfall 5 | A 0-row dev/test split breaks the child; planner should lock the exact rule |
| A5 | GUE repo task subdirs still match registry keys as of today (shape-A census from Phase 10; today's probe confirmed emp_H3 lands correctly, which re-verifies the one task we need) | Downloads | Low — only emp_H3 needed |
| A6 | modelscope model downloads remain reachable at execution time (200s today) | Downloads | Retry/resume is built into the CLI; worst case re-run the download task |
| A7 | The export's per-model view over 2 models feeds summarize cleanly in a tmp tree with only those files present (summarize reads any ≥1 `*_performance.json` dir; not executed end-to-end this session because no run records exist yet) | Consumption | Low — test_determinism proves the chain over arbitrary trees; flag toggles exist |

## Open Questions

1. **Exact D15-06 small-split rule** — see A4. Recommendation: `k = max(1, int(n * 0.05))`
   capped at n, `actual_fraction` recorded per split in the subset registry. Needs a
   plan-level decision line (it is arguably already locked; interpret charitably and pin in
   the generator's docstring + tests).
2. **Smoke on full 5mC vs 5% subset** — recommendation: FULL dataset (keeps VAL-01
   independent of VAL-02 machinery; 2110 rows is already minimal; the docs/Phase-11
   precedent used full). The alternative (subset smoke) would couple the two validations.
3. **Include a multiclass dataset in the REAL sweep?** — recommendation: NO (both sweep
   datasets binary; multiclass stratification is deterministically covered by the D15-08
   synthetic fixture test). Keeps the sweep bounded and the pair set proven.
4. **Subset registry extra provenance fields** (generator version/seed/fraction markers
   inside entries) — registry consumers ignore unknown keys (verified read pattern);
   recommendation: add a small `subset` provenance object per entry for auditability, but
   keep it optional vs. a sibling manifest file. Planner's call.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| 2× RTX 5090 (CUDA) | smoke + sweep training | ✓ (idle, 0% util) | driver 595.71.05 / torch cu130 sees 2 | — |
| dnallm editable | child training imports | ✓ verified | 1.3.2 @ ../DNALLM | reinstall rule (D15-14) |
| torch CUDA | training + FLOPs | ✓ | 2.11.0+cu130 | — |
| modelscope CLI + network | asset downloads | ✓ (live-probed, repos HTTP 200) | 1.40.2 | HF mirrors (registry `huggingface` ids) |
| /root/autodl-tmp disk | all artifacts | ✓ | 2.0 T free | — |
| uv | gates + chain | ✓ | 0.13.0 | — |
| node | chain tail (optional) | ✓ | v26.4.0 | — |
| pytest collection baseline | gates | ✓ 2113 collected | — | — |
| GPU-hour authorization | real runs | ✓ pre-authorized (CONTEXT option A) | — | — |

**Missing dependencies with no fallback:** none (models/datasets are missing BY STATE, not
by environment — acquisition is a planned task, channels verified working).

**Missing dependencies with fallback:** none.

## Security Domain

`security_enforcement: true`, ASVS level 1 (`.planning/config.json`). This phase adds one
offline stdlib script, downloads external data, and runs training — no network services, no
auth, no crypto, no secrets.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | none (no services introduced) |
| V3 Session Management | no | none |
| V4 Access Control | no | static-file/hosting model unchanged |
| V5 Input Validation | yes | The generator parses EXTERNAL CSVs (downloaded datasets = untrusted input): fail-fast on malformed CSV/header/label values (the script/ per-file skip-or-refuse discipline, `get_float`-style coercion precedent); never `eval`; `csv` module only |
| V6 Cryptography | no | none (SHA256 file hashes for evidence are stdlib `hashlib`, not a crypto control) |
| V12 File & Resources | yes | Generator writes ONLY under its explicit output root (test-pinned: no writes outside tmp fixture trees); downloads land in user-owned roots under /root/autodl-tmp (disk policy) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious/corrupt dataset CSV from mirror | Tampering | Declared-vs-measured row-count reconciliation (registry `Train/Dev/Test` vs on-disk rows — verified matching today); generator fails fast on malformed rows |
| Supply-chain weight files (model repos) | Tampering | Official-channel modelscope repos only (registry ids); the box-validated channel; no arbitrary URLs |
| Output-path confusion writing into committed data | Tampering | Explicit-root discipline (Pitfall 4/6); tmp-tree consumption; `dnallm-mark/data/` read-only assertion (test_determinism.py:3 precedent) |
| Registry cross-contamination (subset → official/custom) | Tampering | Triple isolation + hash-before/after assertions (D15-07; the custom-overlay fail-fast precedent) |

## Sources

### Primary (HIGH confidence — all verified this session by direct Read/probe)
- `pipeline/run_finetune.py` — :744,747 (child official-registry loads), :507-535 (`apply_train_fraction`), :930-980 (quirk lists), :985-1000 (root resolution), :1088-1160 (dataset loop, skip logic, Dev refusal), :1326-1332 (train/dev/test.csv paths)
- `pipeline/run_sweep.py` — :360-455 (flags incl. `--registry-dir`, `--subset_file`), :861-960 (`load_priority_tiers`), :1092 (`cell_dir_for`), :1139-1257 (`build_argv` full child argv contract)
- `pipeline/run_sweep_shard.py` — module docstring (dispatch/cleanup/rerun contracts), :400-480 (`--mode`/`--merge`/`--cleanup`/`--yes`/`--rerun-failed` definitions), :515+ (`_registry_dir_from_passthrough`)
- `pipeline/dispatch_core.py` — protocol order, usage example, :1730/:1806 (`state["status"] = "done"`)
- `schemas/dispatch_state.json` — status enum `running/done/incomplete`, snapshot invariant
- `pipeline/registry_loader.py` — :61-89 (`custom_registry_dir`, env override), :172-208 (`load_{models,datasets}_registry(registry_dir)` semantics)
- `script/export_runs.py` — docstring + :898-960 (full CLI contract incl. `--dry-run`, output defaults)
- `tui/services/download_queue.py` — :14-115 + :224-307 + :935-1010 (download argv shapes, shape tables, MODEL_DOWNLOAD_PROGRAM)
- `pipeline/{models,datasets}_info.json`, `pipeline/dnallm_compat.json`, `pipeline/sweep_priorities.json`, `pipeline/eval_subsets.json` — registry ground truth
- `docs/multi-gpu.md` (full read — structure, D-05 section :179, 9-step :200), `.planning/WINDOWS.md` (id 21 row), `.pl/PROJECT.md:100` (D-05 revision row Pending)
- `tests/test_determinism.py` (run-twice byte-identity idiom), `tests/test_dispatch_core.py` / `tests/test_sweep_shard.py` (test precedents), `tests/conftest.py`
- **Live probes:** nvidia-smi; `pip show dnallm`; torch cuda; exhaustive finds proving no weights/datasets on disk; real modelscope downloads (5mC + emp_H3, row counts verified); model config.json probe; HTTP 200s on all candidate repos; **CPU dispatch dry-run over a subset-registry fixture (exit 0, 12 cells, per-cell roots recorded)**
- `.planning/research/ARCHITECTURE.md` §C — the milestone subset-generator design (not re-derived, per instructions)

### Secondary (MEDIUM confidence)
- None needed — no external docs were required; all claims are in-repo or probe-verified.

### Tertiary (LOW confidence)
- None. (Training-time estimates are tagged [ASSUMED] in the Assumptions Log, not sourced.)

## Project Constraints (from CLAUDE.md)

Extracted directives the planner must honor (from `.claude/CLAUDE.md`, binding as locked decisions):
- **Surgical fixes only** — no opportunistic refactors that widen review surface; the dispatch CLI runs VERBATIM (defects → normal fix flow)
- **Tech stack unchanged** — vanilla ES-module JS + Python; static hosting only; no backend/API
- **Reproducibility** — every number change documented with before/after comparison; recomputation allowed and expected
- **CI feasibility** — GitHub Actions never requires GPU or the external `dnallm` package; tests limited to stdlib/numpy/pandas scripts and static checks
- **DNALLM repo read-only** — upstream defects get filed upstream + documented workarounds, never local patches
- **Disk policy** — all data/models/caches under /root/autodl-tmp, never / or /root
- **GSD workflow enforcement** — repo edits only through GSD commands/plan tasks
- **Commit discipline (project memory)** — plain commit messages, no Co-Authored-By trailers; v1.3 = LOCAL COMMITS ONLY, push deferred to milestone close
- Python `script/` conventions: module docstring with usage; Google-style docstrings; `main()` with `# ===== Configuration =====` block; `if __name__ == "__main__": main()`; defensive parsing; per-item skip-on-error loops; UTF-8 JSON `indent=4, ensure_ascii=False`

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — everything already installed and probed working; no new deps
- Architecture: HIGH — the load-bearing seam (child official-registry loads) is Read-verified AND the recommended command shape is dry-run-proven end-to-end
- Pitfalls: HIGH — each grounded in a Read line range or a live-probe observation; wall-time items are [ASSUMED] where noted
- Selections: HIGH on existence/reachability/compat; MEDIUM on plant-dnamamba-6mer real-training behavior (A2)

**Research date:** 2026-10-20
**Valid until:** 2026-11-20 (stable, in-repo grounded; the download-reachability facts are point-in-time and re-verified by the acquisition task itself)
