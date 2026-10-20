# Architecture Research

**Domain:** How v1.3's four capability groups integrate with the existing DNALLM-Mark architecture
**Researched:** 2026-10-20
**Confidence:** HIGH (all integration points named against live code; probe-verified during v1.2)

## Existing Architecture (DO NOT re-research; integration targets)

- **Orchestrator**: `pipeline/run_sweep_shard.py` — 5 owned flags + verbatim passthrough; LPT shard by registry `size (M)`; frozen sibling roots `{root}-mgpu-w{i}`; per-worker `CUDA_VISIBLE_DEVICES`; `start_new_session=True` process groups; per-launch tee logs; `--merge` (SHA256-verify copy, MERGE_ALLOWLIST, lane-equality refusal, output_dir prefix rewrite)
- **Sweep driver**: `pipeline/run_sweep.py` — cell enumeration (model×task×seed, alias cells for peft), `--from-failures`, priority tiers, manifest recording (D-13 present-flags-only), fake-executor dry-run proof lane
- **Child**: `pipeline/run_finetune.py` — `trainer_state.json` resume marker per cell; argv surface frozen by tier-1 suite; `WORLD_SIZE`/`LOCAL_RANK` scaffolding (DDP seam, stays dormant)
- **TUI**: `tui/app.py` + `tui/screens/*` over textual-free `tui/services/*`; slot 4 run-config + terraform-style launch gates (env gate → problems → confirm → E2' typed-phrase); slot 5 monitor (Running/History tabs, mgpu-w sibling grouping, matrix/tree/wide); single-GPU serial gate refuses stage-0 on both launch paths; snapshot SVG goldens (D-03 maintainer review)
- **Data chain**: `script/export_runs.py` → `task_performance/` → `script/summarize_comparison.py` → `models_comparison*.json` → static pages; `script/gen_progress.py` → `data/progress/sweep.json`; vendored `aggregate_seeds` (per-seed statistics artifacts)
- **Web**: `dnallm-mark/js/main.js` scatter (FLOPs vs rank), `js/task.js` bar chart; Chart.js 4.4.0 UMD CDN pin; chart destroy-before-render discipline; no build step (hard constraint)
- **Registries**: official `pipeline/{models,datasets}_info.json` + user custom overlay (`~/.config/dnallmmark/custom_*.json`, `DNALLMMARK_CUSTOM_REGISTRY_DIR` whole-dir override); n_audit reconciliation

## New Components and Integration Points

### A. Dynamic dispatch core (rework inside `run_sweep_shard.py`)

- **Single dispatcher process owns an in-memory cell queue.** Workers = persistent `run_sweep.py`-class loops? NO — key design decision: each *worker* is a long-lived process that executes cells one at a time via the existing child path. Two viable shapes (plan-phase decides, both stdlib):
  1. **Dispatcher spawns one `run_finetune.py`-equivalent child per cell** (worker = thin loop: claim cell → spawn child with cell argv + CUDA pin → wait → record → claim next). Maximal reuse of the frozen child argv surface; per-cell exit codes are the failure ledger.
  2. **Dispatcher keeps spawning per-cell `run_sweep.py --models M --tasks T --seeds S` single-cell invocations.** Zero new child-facing code, but pays sweep-startup cost per cell and bends run_sweep's multi-cell contract.
  - Shape 1 is the recommended integration: the orchestrator already owns worker processes; the child argv surface stays untouched (frozen contract honored); run_sweep stays the single-sweep authority.
- **Output roots — the load-bearing redesign.** Today: worker-scoped frozen roots. Under dispatch, cell output must be **cell-stable, worker-independent** so resume/merge never depend on which GPU ran the cell. Recommended: keep ONE `{root}` with the ordinary per-cell subpaths (`{root}/{model}/{dataset}/seed{k}` — the existing layout run_sweep already produces), plus a small per-cell **claim ledger** (O_EXCL claim file, the tee O_EXCL precedent) making double-dispatch structurally impossible. `--merge` then degenerates for dispatch-mode runs (one root already) but must keep working for legacy static-shard roots — both modes coexist behind the same CLI.
- **Resume**: `trainer_state.json` marker-skip remains authoritative at the child level; the dispatcher additionally skips ledger-completed cells. A partially-trained cell (crashed mid-run, no marker) is simply re-dispatched.
- **State file** (`{root}/dispatch_state.json`, single-writer = dispatcher, atomic write via the settings.atomic_write idiom): queue remaining/done/failed, per-worker in-flight cell + last event, per-GPU assignment, timestamps. Consumed by: orchestrator terminal table, TUI (read-only), `gen_progress.py` mirror.

### B. Failure re-run + cleanup

- `--from-failures`-style union re-run: dispatcher-mode failure ledger → one relaunch enumerating exactly failed cells (reuse the existing failure-file contract shape; thread lane flags — the 12-04 lane-match limitation gets fixed here by recording lane flags in the dispatch ledger)
- Post-merge verify + cleanup helper: export-dry-run over merged root + manifest count check, then explicit (confirm-gated) worker-root removal — the manual `rm -rf` recipe from docs/multi-gpu.md §5 becomes a command

### C. 5% subset generator + separate config

- New offline script (`script/make_subset_datasets.py`-class): reads real dataset dirs → deterministic **stratified** sample (seed-governed, the `--train_fraction` shuffle-then-select precedent extended to preserve class balance for classification tasks) → writes subset dataset directories + a **subset registry file** with **measured row counts** (the custom_registry per-entry count fields are the schema precedent — subset entries are a third registry class, NOT written into official or user-custom files)
- Sweep runs against the subset registry via the existing registry-dir override seam; output root separate (e.g. `pipeline/finetuned-smoke/`) so real and subset artifacts never mix

### D. TUI multi-GPU surface

- Services: `gpu_probe.py` (textual-free, subprocess nvidia-smi → frozen dataclass rows, honest degradation) + `dispatch_state.py` reader (JSON → dataclasses); both CPU-testable with injectable seams (EnvCheckServiceProtocol pattern)
- Slot 4: workers/gpus params join RunSpec; preview shows dispatch plan (queue depth); gate chain unchanged (E2' typed phrase when full-scope; the single-GPU serial gate's stage-0 refusal is *replaced* by multi-GPU-aware semantics: N GPUs → N concurrent cells is the sanctioned shape)
- Slot 5: dispatch state joins the scanner's data sources (Running tab gains queue/in-flight rows); G GPU-lanes panel reads gpu_probe on the monitor cadence (2s frontier class)
- Goldens: monitor/config SVGs regenerate (D-03 uncommitted discipline)

### E. Web error bars

- `summarize_comparison.py`: emit per-model per-dataset `mean`, `std`, `n_seeds` alongside existing aggregate fields (additive optional keys; absent → byte-identical output → zero-drift gate green)
- JSON schemas: optional fields with documented semantics (std = population std over seeds; document ddof choice once, in METHODOLOGY.md appendix per the inventoried-migration discipline — display-only, no methodology version bump)
- `js/`: vendored `errorBarsPlugin` (~40 lines, `afterDatasetsDraw`, `getPixelForValue`) applied to the scatter; bar chart uses floating bars for the range + plugin whiskers; tooltip gains ±std line; CSS via existing tokens
- Node lane: generator fixture → JSON → plugin math assertions (pure function: value±std → pixel geometry) without a browser

## Suggested Build Order (dependency-driven)

1. **Dispatch core + resume/ledger redesign** (A) — everything else consumes its state file; riskiest piece first, CPU-provable with fake children
2. **Orchestrator live view + failure re-run + cleanup** (A state file + B) — pure consumers of A
3. **N=2 smoke** (validation gate for A+B on the real 2×5090; closes WINDOWS #21) — before TUI so UI work rides a proven core
4. **Subset generator + small real sweep → merge → data chain** (C) — proves the full benchmark loop
5. **TUI surface** (D) — launch params, monitor integration, G lanes; goldens last
6. **Web error bars** (E) — independent of D, needs only C's artifacts for real data; could parallel 5 in a separate phase

## Data Flow Changes

- New artifacts: `dispatch_state.json` (live), dispatch failure ledger, subset dataset dirs + subset registry, `mean/std/n_seeds` keys in comparison JSONs
- Unchanged: per-cell artifacts contract (run_record/final_metrics/trainer_state/seed_result/flops_report), arena taxonomy, hosting model (static files), CI lanes
