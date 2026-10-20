---
phase: 15-dual-gpu-validation-subsets
title: 双卡验证与子数据集 (N=2 Smoke & Small Real Sweep)
status: approved
created: 2026-10-20
---

# Phase 15: 双卡验证与子数据集 - Context

**Gathered:** 2026-10-20
**Status:** Ready for planning

<domain>
## Phase Boundary

The dispatch orchestrator is proven on the local 2× RTX 5090 box: the
docs/multi-gpu.md N=2 smoke procedure executes for real (WINDOWS #21 closed,
D-05 revised 本机=双卡验证机), 5% stratified subsets are pre-materialized as
first-class dataset directories under a dedicated config, and a small real
sweep (≈2 models × 2 datasets × 3 seeds, 1 epoch) runs both GPUs end-to-end
through dynamic dispatch → export/data-chain consumption without modification.

**Maintainer authorization (2026-10-20, option A):** ALL GPU executions in this
phase are pre-authorized by the user — smoke + small real sweep. Executors run
real training subprocesses inside plan tasks.

</domain>

<decisions>
## Implementation Decisions

### N=2 Smoke Procedure (VAL-01)
- **D15-01:** docs/multi-gpu.md rewritten as the dispatch-mode procedure: dual workers × `--gpus 0,1`, ONE smallest real model×dataset pair from the registries, 1 epoch, real child processes end-to-end
- **D15-02:** Pass criteria: both GPUs produced cell artifacts + dispatch_state.json terminal status "done" + merged-root consumption dry-run passes + the executed procedure is what the docs now say (procedure/doc identity)
- **D15-03:** D-05 revision lands in docs/multi-gpu.md (本机=双卡验证机; the old 开发本机/验证他机 split is retired); WINDOWS #21 closed with evidence links
- **D15-04:** Smoke failure = stop immediately: preserve dispatch_state + tee logs as phase artifacts, route to debug flow; never proceed into VAL-03 with a broken core

### Subset Generator (VAL-02)
- **D15-05:** New offline script `script/make_subset_datasets.py`: reads real dataset dirs → deterministic STRATIFIED 5% sample per split (label-stratified for classification; seed-governed) → writes subset dataset directories + a dedicated subset registry file carrying MEASURED row counts
- **D15-06:** Sampling semantics: per-split independent stratified 5%; splits with <20 rows take min(5%, full) with the actual fraction recorded; run-twice byte-identity is test-pinned
- **D15-07:** Isolation: subset registry/config/output roots are triple-isolated from official AND user-custom registries (e.g. output under `pipeline/finetuned-smoke/`); an assertion proves zero intersection; subset entries are a third registry class, never written into official or custom files
- **D15-08:** Coverage: subsets generated only for the small-sweep's chosen 2-3 datasets (+1 small classification fixture dataset for the stratification unit test)

### Small Real Sweep (VAL-03)
- **D15-09:** Scale: 2 models × 2 datasets × 3 seeds, 1 epoch — small models (plant-dnabert-6mer class) so the sweep finishes in hours; satisfies the ≈2-4×2-3×3 requirement at its lower bound
- **D15-10:** Run mode: Phase 13/14 dynamic dispatch `--mode dispatch --workers 2 --gpus 0,1`, ONE shared root, NO merge needed (MGPU-06); live view + state file observed during the run
- **D15-11:** Consumption proof: the shared root feeds `script/export_runs.py` (real run, not dry-run) → task_performance → summarize_comparison chain with ZERO chain modifications; produced JSONs archived as phase artifacts
- **D15-12:** All artifacts under /root/autodl-tmp per the disk-capacity policy (model caches already routed; subset dirs and output roots inside the gitignored pipeline/ areas)

### Execution & Gates
- **D15-13:** Executors run real GPU training inside plan tasks (pre-authorized); every run prints its plan (models/datasets/seeds/GPUs/expected outputs) before launching
- **D15-14:** dnallm environment preflight per the standing rule: verify the editable install before any GPU run (`pip show dnallm`); reinstall if a uv sync dropped it
- **D15-15:** Full CPU lanes stay green; GPU-outcome assertions (artifacts exist, measured row counts, terminal state) land in pytest as fake-independent checks reading REAL produced artifacts where the box allows; CI stays zero-GPU (assert on fixture-generated artifacts, not live GPUs)
- **D15-16:** Every real GPU run's command, duration, and artifact SHAs are recorded in the SUMMARY; defects found mid-run go through the normal fix flow

### Claude's Discretion
- Exact model/dataset selection for smoke + sweep (smallest-by-size from registries, subject to availability on disk)
- The subset registry file's exact name/location (pipeline/ gitignored area) provided isolation assertions cover it
- Splitting smoke vs sweep across plans/waves

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pipeline/run_sweep_shard.py`: `--mode dispatch --workers N --gpus G1,G2` + shared-root semantics; `--dry-run` plan artifact; `--cleanup`; `--rerun-failed`
- `pipeline/dispatch_core.py`: the full engine (v2 state + live renderer, ledger + archive genealogy, lane replay)
- `script/export_runs.py`: `--dry-run` seam (14-02) + real export; data chain (task_performance → summarize_comparison) unchanged
- `run_sweep.py --train_fraction` shuffle-then-select precedent; custom_registry per-entry count fields as the subset-registry schema precedent
- `pipeline/models_info.json` / `datasets_info.json` registries; `run_sweep.load_priority_tiers` size data for smallest-pair selection
- docs/multi-gpu.md: the v1.2 static-shard runbook (§5 manual rm -rf recipe now replaced by --cleanup)

### Established Patterns
- Deterministic seed-governed sampling with run-twice byte-identity pins (test_determinism.py precedent)
- Registry isolation fail-fast (custom overlay precedent — subset registry follows the same discipline)
- Real-GPU artifacts asserted via pytest fixtures over produced directories (Phase 11 bounded-smoke precedent)

### Integration Points
- Smoke + sweep run through the Phase 13/14 dispatch CLI verbatim — this phase must NOT modify pipeline dispatch code except for defects found (normal fix flow)
- Subset datasets feed run_sweep via the existing registry-dir override seam
- docs/multi-gpu.md + WINDOWS.md are first-class deliverables (procedure identity + ledger closure)

</code_context>

<specifics>
- Research `.planning/research/ARCHITECTURE.md` §C is the subset-generator design backbone
- Binding constraints: E2' full sweep stays dual-gated (this phase's small sweep is authorized); subsets pre-materialized, never mixed with real runs; DNALLM suite repo read-only; zero CI GPU
- 2× RTX 5090 (32GB each) confirmed idle at phase start (2026-10-20)

</specifics>

<deferred>
- TUI multi-GPU surface → Phase 16
- Web error bars → Phase 17
- Docs rewrite beyond multi-gpu.md/README touchpoints → Phase 18

</deferred>
