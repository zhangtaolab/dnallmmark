---
phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
plan: 06
subsystem: pipeline
tags: [flops, gb10-smoke, dry-run, pipe-02, d-23-emission-sanity, evidence-record]

# Dependency graph
requires:
  - phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
    provides: pipeline/flops_counter.py + schemas/flops_report.json (07-01) — the writer and the contract this smoke validates
  - phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
    provides: run_sweep four-flag pass-through with manifest present-only recording (07-03) — the surface the live dry-run exercises
  - phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
    provides: run_finetune FLOPs integration — calibration slot + post-success write, WR-13-ordered (07-04)
provides:
  - PIPE-01's runtime half proven on the real GB10 — a bounded default-mode run emits a schema-valid, hook-covered, hardware-tagged, magnitude-sane flops_report.json (D-22/D-23 closed)
  - PIPE-02 proven on a live sweep invocation — the four threaded flags record exactly the present flags in every manifest cell, absent flags leave no keys (D-13)
  - The phase's runtime evidence record — executed commands, wall times, exit statuses, console tail, report key fields, and the magnitude ratio, all pasted verbatim (D-25)
affects: [phase-07 verification, E2' (bounded-smoke discipline precedent), phase-11 monitor (consumes flops_report.json), phase-08 tui]

# Actuals (#2632) — same estimateTokens scale as the plan's estimate (chars/4
# over the realized diff; this plan changes only this SUMMARY — no source files).
actuals:
  tokens: 4451
  tasks: 3
  commits: 0       # production commits — a pure verification plan (no source changes, no committed artifacts, D-26); the docs close-out commit follows this SUMMARY

tech-stack:
  added: []  # zero installs this phase (T-07-SC vacuous — uv only toggled one venv entry switching --group dev/--group gpu, no network installs)
  patterns:
    - "evidence-not-artifacts smoke recording: machine-specific run products stay gitignored under pipeline/finetuned/; the committed record is the SUMMARY's pasted key fields (D-25/D-26)"

key-files:
  created:
    - .planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-06-SUMMARY.md
  modified: []

key-decisions:
  - "Dry-run used the valued --effective_batch_size 16 form for explicitness (per plan); bare-flag equivalence (nargs='?' const=16, D-12) is already unit-locked by 07-03 and was not re-run — surgical scope"
  - "The calibration UserWarning at flops_counter.py:885 (torch.tensor on a tensor) is the legacy-verbatim calibration-forward behavior ported by 07-01 — expected console noise, not a defect"
  - "No per-task commits exist by design: every task's declared output IS this SUMMARY (the plan's artifacts section names no source symbols); the docs close-out commit carries the plan"

patterns-established:
  - "Bounded-smoke evidence shape for future GPU verification tasks: command + wall time + exit status + console tail + pasted report key fields + mechanical assertion output, never the artifacts themselves"

requirements-completed: [PIPE-01, PIPE-02]

coverage:
  - id: D1
    description: "PIPE-02 proven on a live CPU-side sweep invocation: --dry-run with --num_train_epochs 1 --effective_batch_size 16 records both flags in the manifest cell and omits subset_file/cache_dir keys (D-13)"
    requirement: PIPE-02
    verification:
      - kind: other
        ref: "command: DNALLMMARK_CUSTOM_REGISTRY_DIR=<empty tmp> uv run --group dev python pipeline/run_sweep.py --dry-run --models plant-dnabert-6mer --tasks iDNA_ABF_datasets__5mC --seeds 42 --output-root <tmp>/sweep-out --num_train_epochs 1 --effective_batch_size 16 -> '[Dry-run] 1 planned cell(s) over 1 model(s) x 1 task(s) x 1 seed(s)' + 'dry-run-flags-ok' (inline json assertion over cells[0]), exit 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "GB10 bounded FLOPs smoke (D-21/D-22/D-24): 1 model x 1 task x 1 seed x 1 epoch, default mode, exits 0 at minutes scale with flops_report.json emitted into the cell dir alongside final_metrics.json before the trainer_state marker"
    requirement: PIPE-01
    verification:
      - kind: other
        ref: "command: (cd pipeline) uv run --group gpu python run_finetune.py --target_model plant-dnabert-6mer --target_dataset iDNA_ABF_datasets__5mC --num_train_epochs 1 -> exit 0, wall 77 s; test -f .../seed_9527/flops_report.json -> report-present; zero 'Error finetuning dataset'/'Error encoding dataset' lines"
        status: pass
    human_judgment: false
  - id: D3
    description: "All six D-23 emission+sanity criteria pass on the real artifacts: parse+schema_version 1, BertSelfAttention (.matmul_core) and non-attention Linear hook keys present, uncovered_layers empty, hardware populated (gpu_device 'NVIDIA GB10' verbatim, train_time 65.0438, max_mem_gb 1.5587), Draft202012 schema validation, ratio 0.332 in [0.05, 1.0]"
    requirement: PIPE-01
    verification:
      - kind: other
        ref: "command: uv run --group dev python -c '<six-assertion script>' -> 'smoke-criteria-ok ratio=0.332 gpu=NVIDIA GB10'"
        status: pass
    human_judgment: false

# Metrics
duration: 5 min
completed: 2026-10-11
status: complete
plan_head_before: 26400c34c17fa2bc006395fda133b3a27bbbd9f3
plan_head_after: 26400c3  # unchanged — zero production commits (docs-only plan); the docs close-out commit follows this SUMMARY
---

# Phase 7 Plan 06: GB10 FLOPs Smoke & Live PIPE-02 Dry-Run Summary

**Bounded GB10 smoke (plant-dnabert-6mer × iDNA_ABF_datasets__5mC, 1 epoch, default mode, 77 s wall) emitted a schema-valid flops_report.json with all six D-23 criteria green — ratio 0.332 vs HF's total_flos (the ~1/3 fwd-only expectation), gpu_device "NVIDIA GB10" verbatim, uncovered_layers empty — and a live CPU dry-run proved PIPE-02's four-flag surface records exactly the present flags and nothing else**

## Performance

- **Duration:** ~5 min (2026-10-11T07:47:22Z → 07:52:00Z)
- **Tasks:** 3/3
- **Files:** 1 created (this SUMMARY) — zero source changes, zero committed run artifacts (D-26)
- **Production commits:** 0 (measured `git rev-list --count 26400c3..HEAD` = 0 — a pure verification plan; every task's output IS this evidence record)

## Accomplishments

- **PIPE-02 proven on a live invocation (Task 1):** a CPU-side `run_sweep.py --dry-run` with `--num_train_epochs 1 --effective_batch_size 16` planned exactly 1 cell (1 model × 1 task × 1 seed) and recorded both flags in the manifest cell while leaving `subset_file`/`cache_dir` keys absent (D-13) — the threading the 07-03 unit tests promise, demonstrated end-to-end on a real CLI call with the custom-registry env pinned to an empty temp dir (machine-independence, Pitfall 3).
- **The GB10 bounded smoke ran green (Task 2, D-21/D-22/D-24):** default mode (peft none, fresh base-name cell), 1 epoch, exit 0, **77 s wall** (train_runtime 65.04 s; the 06-02 LoRA precedent was 42.4 s), peak memory 1.5587 GB (vs LoRA's 0.53 GB — full-parameter training), eval_f1 0.9667 after 1 epoch. `flops_report.json` landed in the cell dir alongside `final_metrics.json`, before the `trainer_state.json` marker copy (WR-13).
- **All six D-23 criteria passed mechanically (Task 3):** parse + schema_version 1; 12 `.matmul_core` (BertSelfAttention) + 39 non-attention Linear/LayerNorm keys among 111 layer_details entries; `uncovered_layers == []` (the conventional Bert is fully covered — strict criterion met, nothing surfaced); hardware populated with the real platform string; Draft202012 validation against `schemas/flops_report.json` clean; **ratio = 0.3316** — almost exactly the mechanical ~1/3 expectation for a fwd-only extrapolation against HF's fwd+bwd `total_flos` (research A7).

## Task Execution Record (the phase evidence, D-25)

### Task 1 — CPU-side sweep dry-run (PIPE-02 live proof)

Command (from repo root; temp root outside the repo, cleaned up after):

```bash
TMP=$(mktemp -d) && mkdir -p "$TMP/empty-custom"
DNALLMMARK_CUSTOM_REGISTRY_DIR="$TMP/empty-custom" uv run --group dev \
  python pipeline/run_sweep.py --dry-run \
  --models plant-dnabert-6mer --tasks iDNA_ABF_datasets__5mC --seeds 42 \
  --output-root "$TMP/sweep-out" \
  --num_train_epochs 1 --effective_batch_size 16
```

Observed output (exit 0):

```text
[Dry-run] 1 planned cell(s) over 1 model(s) x 1 task(s) x 1 seed(s); manifest: /tmp/tmp.1tikZxLlp3/sweep-out/sweep_manifest.json
dry-run-flags-ok
```

The manifest cell, verbatim (the inline assertion checked `num_train_epochs == 1`, `effective_batch_size == 16`, and `'subset_file' not in c and 'cache_dir' not in c` — all passed):

```json
{
    "effective_batch_size": 16,
    "model": "plant-dnabert-6mer",
    "num_train_epochs": 1,
    "output_dir": "/tmp/tmp.1tikZxLlp3/sweep-out/plant-dnabert-6mer/iDNA_ABF_datasets__5mC/seed_42",
    "seed": 42,
    "status": "planned",
    "task": "iDNA_ABF_datasets__5mC"
}
```

No GPU touched (run_sweep is stdlib-only; the dry-run path only enumerates and writes the manifest). Temp root removed afterward; `git status` clean of run artifacts.

### Task 2 — GB10 bounded FLOPs smoke (GPU step, D-24)

**Preconditions verified (all read-only, all met):** `torch.cuda.is_available() == True` and `torch.cuda.get_device_name() == "NVIDIA GB10"` in the gpu-group venv; dnallm 1.2.1 importable; `pipeline/models/plant-dnabert-6mer` on disk; `pipeline/datasets/iDNA_ABF_datasets/5mC/{train,dev,test}.csv` present; the base-name cell dir `pipeline/finetuned/plant-dnabert-6mer/iDNA_ABF_datasets__5mC/seed_9527` did not exist (fresh train — no resume marker to remove).

Command (cwd `pipeline/`, exit 0, **wall 77 s**):

```bash
uv run --group gpu python run_finetune.py --target_model plant-dnabert-6mer \
    --target_dataset iDNA_ABF_datasets__5mC --num_train_epochs 1
```

Key console lines (full log kept at `/tmp/07-06-smoke.log`):

```text
Detected GPU memory: 121.62 GB
[2026-10-11 15:49:36] Loading model: plant-dnabert-6mer
[transformers] BertForSequenceClassification LOAD REPORT from: .../pipeline/models/plant-dnabert-6mer
Base batch size: 1 | Dynamic starting batch size: 1 for max_len 8
World size (num_gpus): 1
[2026-10-11 15:49:39] Index: iDNA_ABF_datasets__5mC, Dataset: iDNA_ABF_datasets__5mC
Tokenizer type: 6mer. Infer max token length: 8
pipeline/flops_counter.py:885: UserWarning: To copy construct from a tensor, ... (torch.tensor(batch_sample["input_ids"]).unsqueeze(0).to(device))
{'loss': '2.897', 'grad_norm': '16.54', 'learning_rate': '1.962e-05', 'epoch': '0.09858'}
```

Console tail (last lines after de-CR of the tqdm stream):

```text
{'eval_loss': '0.2518', 'eval_accuracy': '0.9658', 'eval_precision': '0.9431', 'eval_recall': '0.9915', 'eval_f1': '0.9667', 'eval_mcc': '0.9329', 'eval_AUROC': '0.9722', 'eval_AUPRC': '0.9608', ...}
100%|██████████| 528/528 [01:07<00:00,  7.78it/s]
Writing model shards: 100%|██████████| 1/1 [00:00<00:00,  5.55it/s]
100%|██████████| 234/234 [00:01<00:00, 227.56it/s]
Training the model using 1.5587153434753418 GB memory.
Recorded initial max memory: 1.5587153434753418 GB
```

Zero occurrences of "Error finetuning dataset" / "Error encoding dataset". Cell dir listing after the run: `checkpoint-520`, `checkpoint-528`, `config.json`, **`final_metrics.json`**, **`flops_report.json`**, `model.safetensors`, `runs/`, `tokenizer_config.json`, **`trainer_state.json`** (the resume marker), `training_args.bin`, `vocab.txt`. The `flops_counter.py:885` UserWarning is the calibration forward's legacy-verbatim `torch.tensor` call — expected, matches the ported pattern.

### Task 3 — D-23 six-criteria assertion over the real artifacts

Assertion command: the plan's `<verify>` script (`uv run --group dev python -c ...` over the cell's `flops_report.json` + `final_metrics.json`, validated against `schemas/flops_report.json` with `jsonschema.Draft202012Validator`). Observed:

```text
smoke-criteria-ok ratio=0.332 gpu=NVIDIA GB10
```

| # | D-23 criterion | Result |
|---|----------------|--------|
| 1 | Report parses; `schema_version == 1` | **PASS** (1) |
| 2 | `layer_details` has `.matmul_core` keys (BertSelfAttention hook) AND non-attention Linear keys | **PASS** (12 `.matmul_core` keys, e.g. `bert.encoder.layer.0.attention.self.matmul_core`; 39 non-attention keys, e.g. `bert.encoder.layer.0.intermediate.dense`; 111 entries total) |
| 3 | `uncovered_layers` empty or share < 0.05 | **PASS** — `uncovered_layers == []` (fully covered conventional Bert; no WARNING printed) |
| 4 | Hardware: non-empty `gpu_device`, positive `train_time`, positive `max_mem_gb` | **PASS** (`gpu_device: "NVIDIA GB10"` verbatim, `train_time: 65.0438`, `max_mem_gb: 1.5587153434753418`) |
| 5 | Validates against `schemas/flops_report.json` (Draft202012) | **PASS** (no ValidationError) |
| 6 | `0.05 <= total_flops_all_tokens / total_flos <= 1.0` | **PASS** — **ratio 0.3316** (2.876e12 / 8.674e12) |

Report top-level fields, verbatim:

```json
{
    "schema_version": 1,
    "num_tokens": 8,
    "all_tokens": 16880,
    "num_params": 89197058,
    "total_flops_G": 1.363110912,
    "total_flops_exact": 1363110912,
    "total_flops_per_token": 170388864.0,
    "total_flops_all_tokens": 2876164024320.0,
    "computation_size_ratio": 1.9102520623494106,
    "config": {"include_act": true, "include_embed": true, "include_norm": true},
    "hardware": {"gpu_device": "NVIDIA GB10", "max_mem_gb": 1.5587153434753418, "train_time": 65.0438},
    "uncovered_layers": []
}
```

Magnitude anchor: `final_metrics.json` `total_flos = 8674442606400.0` (HF's fwd+bwd counter over the 528 actual steps; the 06-02 LoRA anchor for this same cell was 8.704e12 — consistent). `num_tokens: 8` is the calibration sample's sequence length (6mer tokenizer, max_len 8); `all_tokens: 16880` = 2110 train samples × 8 tokens exactly; the extrapolation `1.363e9 × 16880 / 8 = 2.876e12` checks out.

## Task Commits

None by design — every task's declared `<files>` is this SUMMARY, and the plan's artifacts section names no source symbols ("No source symbols; no committed run artifacts", D-26). The docs close-out commit following this file is the plan's single commit.

## Files Created/Modified

- `.planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-06-SUMMARY.md` — this evidence record (the plan's only artifact)

## Decisions Made

- The dry-run used the valued `--effective_batch_size 16` form (plan's explicitness note); bare-flag equivalence is D-12 unit-locked territory from 07-03 and was not re-run.
- The calibration `UserWarning` (`flops_counter.py:885`) is recorded as expected legacy-verbatim behavior rather than "fixed" — silencing it would deviate from the 07-01 verbatim port.
- `uv run --group dev` ↔ `--group gpu` toggles exactly one local venv entry per switch (sub-millisecond, no network) — recorded as venv group-switching, satisfying T-07-SC's zero-installs posture.

## Deviations from Plan

None - plan executed exactly as written.

## Prohibition Verification (flagged items)

- **Bounded shape held:** the executed smoke command names exactly one model (`plant-dnabert-6mer`), one task (`iDNA_ABF_datasets__5mC`), default seed 9527 (no `--seed`), one epoch (`--num_train_epochs 1`), default mode (no `--peft`). No sweep-scale execution — E2' remains maintainer dual-gated (binding constraint 1, D-21/D-22).
- **Real run artifacts never committed:** `git check-ignore` confirms `pipeline/finetuned/` is ignored (`.gitignore:101`); `git status` shows no staged finetuned artifacts; the evidence is the pasted fields above (D-26).
- **No legacy bit-for-bit reconciliation attempted:** the criteria table lists only emission/sanity checks (D-23 waives reconciliation).

## Flagged Assumption Resolution (research A4)

Confirmed: the smoke pair was available exactly as flagged — `plant-dnabert-6mer` (89M, Bert arch) on disk, `iDNA_ABF_datasets__5mC` (Train=2110) locally present, base-name cell without a resume marker. The fallback (another locally-present small pair) was not needed. Default-mode full-parameter cost landed at minutes scale as predicted (77 s wall).

## Issues Encountered

None.

## Authentication Gates

None — no external services.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 7 is complete: all six plans have summaries. PIPE-01's runtime half (this smoke) and PIPE-02's live proof close ROADMAP success criteria 2; the D-22/D-23 gates are closed with committed evidence.
- The bounded-smoke evidence shape established here (command + wall + tail + pasted fields + mechanical assertion) is the template for Phase 11's bounded smoke and any future GPU verification step.
- Phase 8 (TUI foundation) can proceed; flops_report.json reads go through `pipeline/artifact_loader.py` (07-01, D-19/D-20).

## Self-Check: PASSED

- This SUMMARY exists on disk at the plan directory (the plan's only declared artifact)
- Task-1 verify: `[Dry-run] 1 planned cell(s)...` + `dry-run-flags-ok`, exit 0 (re-observed above)
- Task-2 verify: `SMOKE_EXIT=0 SMOKE_WALL=77s` + `report-present`, zero failure-signature lines
- Task-3 verify: `smoke-criteria-ok ratio=0.332 gpu=NVIDIA GB10` (all six assertions + schema validation green)
- `git status` clean of run artifacts; `pipeline/finetuned/` confirmed gitignored; measured production commits from ledger base 26400c3 = 0 (docs-only plan — legitimate per the zero-code-changes rule)

---
*Phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re*
*Completed: 2026-10-11*
