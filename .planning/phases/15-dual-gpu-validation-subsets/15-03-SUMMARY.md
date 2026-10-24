---
phase: 15-dual-gpu-validation-subsets
plan: 3
subsystem: multi-gpu-dispatch-validation
tags: [dispatch, subsets, real-sweep, val-03, windows-45-closed, fresh-root-rerun]
requires:
  - "15-01 smoke green (finetuned-smoke-r2 done 2/2) + 15-02 generator + 15-04 run_record writer + 15-05 producer fix (option A)"
provides:
  - "REAL 5% subsets materialized for exactly the two sweep tasks with research-table-exact stratification (emp_H3 test 37/37 per the 15-02 Rule-1 correction) + proven registry isolation"
  - "12-cell dual-GPU dispatch sweep GREEN on the FRESH evidence-of-record root pipeline/finetuned-sweep-r2 (done 12/12, 0 skipped, both GPUs, subset-scale steps) with eval_f1 in ALL 12 final_metrics + run_records — the 15-05 producer fix proven live"
  - "Zero-modification consumption proof over that root: real export (subset-registry flags) -> tmp-tree summarize emitting NON-EMPTY models_comparison.json + models_comparison_animal.json (5mC Category Multiple->Animals) + models_comparison_microbe.json (emp_H3 Category Microbe); five JSONs archived as committed phase artifacts"
  - "D15-15 real-artifact pytest checks repointed to the r2 root + a new eval-key pin (suite 27 green; CI-safe skip-if-absent); VAL-03 complete; WINDOWS #45 closed; PROJECT.md small-sweep row done"
affects:
  - "Phase 18 DOCS-01 (docs describe the ruled option-A producer behavior + the r2 re-run as the executed evidence)"
  - "Phase 15 is now fully plan-complete (15-01/02/03/04/05 all landed)"
tech-stack:
  added: []
  patterns:
    - "Halt-at-consumption discipline (D15-04) + fresh-root re-run after a producer fix: the superseded root stays on disk as evidence, the re-run proves the fix end-to-end, and permanent pytest pins move to the evidence-of-record root"
key-files:
  created:
    - .planning/phases/15-dual-gpu-validation-subsets/artifacts/models_comparison.json
    - .planning/phases/15-dual-gpu-validation-subsets/artifacts/models_comparison_animal.json
    - .planning/phases/15-dual-gpu-validation-subsets/artifacts/models_comparison_microbe.json
    - .planning/phases/15-dual-gpu-validation-subsets/artifacts/plant-dnabert-6mer_performance.json
    - .planning/phases/15-dual-gpu-validation-subsets/artifacts/plant-dnamamba-6mer_performance.json
    - .planning/phases/15-dual-gpu-validation-subsets/15-03-SUMMARY.md
  modified:
    - .gitignore
    - tests/test_subset_datasets.py
    - .planning/PROJECT.md
    - .planning/REQUIREMENTS.md
    - .planning/WINDOWS.md
decisions:
  - "Fresh-root re-run on pipeline/finetuned-sweep-r2 (the 15-05 pinned handoff): the original finetuned-sweep root is preserved SUPERSEDED evidence (eval-less final_metrics; never archived) — its trainer_state markers would resume-skip all 12 cells; adjacency .gitignore entry landed (f20dcc7) before the run created the root"
  - "Eval gate asserted BEFORE the chain (per the handoff): eval_f1 numeric in ALL 12 r2 final_metrics AND mirrored into run_record.metrics via the verbatim-copy seam — the halt condition (empty score slots) is gone at both the producer and the child-record layer"
  - "Consumption proven at CONTENT level, not just emission: animal avg_raw == the 5mC f1 mean and microbe avg_raw == the emp_H3 f1 mean per model (dataset-Category grouping, samples=1 each), global samples=2 with ranks 1/2; the tmp tree's models_comparison_plant.json is byte-identical to the committed copy — provably the stale cp artifact, NOT archived"
  - "D15-15 pins repointed to the r2 evidence-of-record root + new test_real_sweep_final_metrics_carry_eval_keys pin (the WINDOWS #45 fix asserted on real run artifacts); suite 27 green"
  - "WINDOWS #45 closed via the CLI fixed verb (open 9->8, fixed 30->31) with the full resolution naming 15-05 + this green re-run; VAL-03 and the PROJECT.md small-sweep row closed in the same Task-3 commit"
metrics:
  duration: 40 min of 15-03 work across two sessions (20 min halted session + ~20 min continuation); the 22-min 15-05 gap-closure interlude is attributed to 15-05
  completed: 2026-10-21
  tasks: 3 of 3
  commits: 6      # 15-03-attributed: 44e421c + fa04cb6 + 012e526 (halt session) + f20dcc7 + 02c5f83 + this docs commit
  plan_head_before: 157610338849af8fe2bd53cedf322490d9bff5dd
status: complete
actuals:
  tokens: 16500   # chars/4 over the realized 15-03-attributed diffs (~9K halt-session + ~7.5K continuation incl. the five archived artifacts + this SUMMARY) vs estimate 15000
  tasks: 3
  commits: 6      # 15-03-attributed (halt 3 + continuation 3); raw ledger-to-HEAD count is 9 — the extra 4 are 15-05's own commits, attributed to 15-05's ledger
---

# Phase 15 Plan 3: Small Real Sweep Summary — COMPLETE (halt + option-A fix + fresh-root resume)

**One-liner:** The full VAL-03 arc landed across three sessions: REAL 5% subsets (research-table-exact, isolation-proven) and a first 12-cell dual-GPU sweep green but halted at the consumption proof on the WINDOWS #45 producer gap (run_finetune discarded trainer.evaluate(), so the export emitted empty score slots and summarize emitted `{}` with zero species files); the maintainer ruled option A, 15-05 landed the flat-additive eval merge plus the animal/microbe archive-list correction; this continuation re-ran the sweep on the FRESH root `pipeline/finetuned-sweep-r2` (272 s, done 12/12, 0 skipped, both GPUs, eval_f1 in ALL 12 final_metrics and run_records) and drove the zero-modification export→summarize chain to NON-EMPTY models_comparison + _animal + _microbe outputs — five JSONs archived as phase artifacts, VAL-03 complete, WINDOWS #45 closed.

## Status: COMPLETE (3/3 tasks; Task 3 finished by the post-15-05 continuation)

The plan originally HALTED at Task 3 (D15-04 discipline) when the real consumption
chain exposed the eval-metrics seam gap. That halt, the maintainer's option-A
ruling, and the producer fix (plan 15-05) are part of this plan's story; the
continuation session (2026-10-21) re-ran the sweep on a fresh root and completed
Task 3's consumption/archive/closure criteria exactly as the 15-05 handoff pinned.

## What Was Executed

### Task 1 — Sweep assets + REAL subset generation + isolation proof + gitignore — COMPLETE (halt session, commit 44e421c)

- Preconditions asserted read-only (both smoke roots terminal done 2/2); D15-14
  preflight green (dnallm editable, 2 CUDA devices, GPUs idle).
- Assets: `zhangtaolab/plant-dnamamba-6mer` (66 s, config.json flat) and GUE
  `emp_H3` (3 s, rows 11971/1497/1497 == registry exactly).
- REAL 5% subsets generated via `script/make_subset_datasets.py`:
  5mC **105/11/117** (53/52, 6/5, 59/58); emp_H3 **598/74/74** (291/307, 36/38,
  **37/37 test** — the 15-02 Rule-1 largest-remainder correction, see Deviations).
- Isolation (D15-07): official + custom registry sha256 byte-unchanged
  before/after; path assertions green (subset roots != official/custom/
  directories.json output_root).
- `.gitignore` gained `pipeline/finetuned-sweep/`; empty custom-registry dir
  prepared for the child pin.

### Task 2 — first 12-cell dispatch sweep — COMPLETE, then SUPERSEDED (halt session; no tracked files)

Dry-run manifest asserted (12 planned cells, per-cell dataset_root == subset
root, orchestrator_mode dispatch). REAL RUN into `pipeline/finetuned-sweep`:
**270 s**, run_id `04f12add…`, dispatch_state **done 12/12 / failed 0 /
skipped 0**, all 12 cell dirs carrying the four artifacts, exactly 12 ledger
claims all lane-pinned to `/pipeline/datasets-smoke`, workers w0 gpu=0 (8
cells) + w1 gpu=1 (4 cells), subset-scale steps (5mC `max_steps=27` ==
ceil(105/4); emp_H3 `150` == ceil(598/4)), plant-dnamamba-6mer trained cleanly
(no Pitfall-8 swap). Mid-run observation evidence + a 24-hash SHA pack saved.
**Supersession note:** this root's final_metrics are eval-less by construction
of the pre-fix producer — it stays on disk as preserved evidence and is NEVER
archived (the 15-05 handoff ruling).

### Task 3 — first consumption attempt — HALTED at the emission/archive criterion (WINDOWS #45)

What ran green: real export (subset-registry flags, 2+2 files), tmp-tree
summarize, committed-data porcelain empty, D15-15 real-artifact pins landed
(commit fa04cb6; suite 26 green). What failed: `models_comparison.json`
regenerated as `{}` (2 bytes) and no species file was a product of the sweep.

- **Root cause 1 (producer seam gap, WINDOWS #45):** `run_finetune.py:1706`
  called bare `trainer.evaluate()` and discarded the result (faithful port
  since c6b3137) — eval scores survived only inside trainer_state
  `log_history`; with all exported score slots `""`, `aggregate_models`
  returned `{}` and every species write was skipped.
- **Root cause 2 (arena premise error, plan-side):** the plan required
  `models_comparison_plant.json` because "both models are plants", but the
  arena chain groups by DATASET Category (D-10): 5mC `Multiple` → Animals,
  emp_H3 → Microbe. The plant artifact is unproducible from this pair.
- **Rule 4 (architectural):** every remediation shape (producer merge /
  record-write harvest / exporter adoption) touched frozen, test-pinned
  contracts — routed to the maintainer (the 15-01 → 15-04 precedent). Halt
  recorded as commit 012e526; WINDOWS #45 opened (kind unmet-truth).

**Interlude — the ruling and the fix (plan 15-05, 2026-10-21):** the maintainer
ruled **option A** (producer-side merge, deliberate narrow unfreeze of
run_finetune.py). 15-05 landed `eval_results = trainer.evaluate()` captured
outside the rank guard + `merged = {**eval_results, **metrics}` flat-additive
re-write of final_metrics.json with the marker copy moved last (write order
final_metrics(v1) < flops < evaluate < merged re-write < marker copy; D-05/WR-13
preserved and newly pinned; argv untouched; contracts 76 + regression 306
green), and corrected this plan's archive list to the true arena outputs
(animal/microbe, six baseline sites). See 15-05-SUMMARY.md.

### Task 3 continuation — fresh-root re-run + consumption + archive + closure — COMPLETE (commits f20dcc7 + 02c5f83)

**Preflight (D15-14):** dnallm editable intact (1.3.2 @
/root/autodl-tmp/Github/DNALLM), both GPUs 0%, assets + subset registry
re-verified (105/11/117, 598/74/74). Run plan printed before launching
(D15-13). `.gitignore` gained the adjacent `pipeline/finetuned-sweep-r2/`
entry FIRST (commit f20dcc7) so the fresh root never leaves untracked noise.

**Dry-run** into the throwaway `sweep-dryrun-root-r2`: `[Dry-run] [Dispatch]
12 planned cell(s)`; manifest asserted — 12 cells, every per-cell
`dataset_root` == the subset root, `model_root` == the real model root,
`orchestrator_mode: "dispatch"`, seeds {42,43,44}.

**REAL RUN** (identical argv minus `--dry-run`, `--output-root
$(pwd)/pipeline/finetuned-sweep-r2`, `DNALLMMARK_CUSTOM_REGISTRY_DIR` pinned to
the empty dir, `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`, tee →
`phase15-evidence/sweep-dispatch-r2.log`):

- **Wall: 272 s** (2026-10-21T00:11:11Z → 00:15:43Z, exit 0). run_id
  `4e74c92d27944db9a20488cb374719a4`.
- **Terminal state:** dispatch_state **done**, counts **completed 12 / total
  12 / failed 0 / skipped 0** — the adjacency edge holds again on the fresh
  root (no cell skipped on any prior root's markers).
- **Per-cell artifacts:** all 12 cell dirs carry final_metrics.json,
  flops_report.json, trainer_state.json, run_record.json.
- **Ledger:** exactly 12 claims, every lane `dataset_root` ends with
  `/pipeline/datasets-smoke`; workers w0 gpu=0 (4 cells) + w1 gpu=1 (8 cells)
  — both GPUs produced cells (claim gpu tokens {0,1}).
- **Step-count sanity (Pitfall 1 tripwire 3):** 5mC cells `max_steps=27`,
  emp_H3 cells `max_steps=150` — subset-scale, never full-split.
- **THE EVAL GATE (asserted before the chain, per the handoff):**
  `eval_f1` present and numeric in **ALL 12** final_metrics (15 eval_* keys
  each; e.g. 5mC seed_42 `eval_f1=0.7143` — matching the score the halt found
  stranded in trainer_state log_history — and `eval_loss=0.7262`; emp_H3
  seed_42 `eval_f1=0.6970`), training keys preserved (`train_runtime`,
  `trainable_params_pct` — the additive merge), and the keys mirrored into
  every `run_record.metrics` through the verbatim-copy seam.
- **Mid-run observation (D15-10):** `dispatch_state.midrun-sweep-r2.json`
  (running 6/12, both workers in-flight on separate GPUs),
  `sweep-table-snapshot.midrun-r2.txt`, `gpu-snapshot.midrun-r2.txt`.
- **D15-16 SHA pack:** `phase15-evidence/sweep-r2-sha256.txt` (dispatch_state
  + 24 cell hashes; spot table below).

| Artifact | SHA256 (first 16) |
|---|---|
| dispatch_state.json (r2) | `4e2c59512cd68577` |
| plant-dnabert-6mer/5mC/seed_42 final_metrics | `e04fbf1e25a6fb9e` |
| plant-dnabert-6mer/5mC/seed_42 flops_report | `a741d5b7956715a2` |
| archived models_comparison.json | `3f2a31c01d2dfba6` |
| archived models_comparison_animal.json | `86aa7341a50456d2` |
| archived models_comparison_microbe.json | `b692b3d64ea497ea` |
| archived plant-dnabert-6mer_performance.json | `8b26e64e15b233c7` |
| archived plant-dnamamba-6mer_performance.json | `631e9e39bdd4e962` |

**Consumption proof (D15-11, zero chain modifications):**

1. **Real export** (not dry-run) from the r2 root with the exporter's OWN
   flags pointed at the subset registry (`.venv/bin/python` used directly —
   never `uv run`, the D15-14 footgun): exit 0, emitted **2
   {model}_performance.json + 2 {task}_task_performance.json** into
   `phase15-evidence/consumption-r2/`. Dataset blocks TRUTHFUL subset blocks
   (598/74/74 and 105/11/117); FLOPs/runtime real. **Every performance block
   carries a REAL numeric f1** (dnabert 0.5952/0.6906; dnamamba
   0.5861/0.6732) — the halt's empty-score condition is gone.
2. **Summarize over the tmp data tree** (copytree idiom with the halt
   session's `mkdir` fix; CWD = tmp tree): exit 0 with
   `✅ Species [Microbe] … (contains 1 dataset(s))` and
   `✅ Species [Animals] … (contains 1 dataset(s))` — and **no** Plants line,
   confirming the corrected arena premise (5mC Multiple→Animals, emp_H3→
   Microbe; grouping is by DATASET Category, never model species).
3. **Content-level assertions:** global `models_comparison.json` non-empty
   (both models, samples=2, ranks 1/2); `_animal.json` per-model `avg_raw`
   EXACTLY equals the 5mC f1 (e.g. 0.5952380952380952) with samples=1;
   `_microbe.json` `avg_raw` equals the emp_H3 f1 (0.6906149119559357) with
   samples=1; both differ from the committed copies (regenerated products,
   not stale copies). The tmp tree's `models_comparison_plant.json` is
   byte-identical to the committed file — provably the plain-cp stale
   artifact, NOT archived.
4. **Read-only proofs:** `git status --porcelain` EMPTY over
   `dnallm-mark/data/`, over `script/`, and over the four pipeline dispatch
   sources — D15-11 held end-to-end.

**Archive (D15-11/D15-16):** the five JSONs (models_comparison.json +
_animal + _microbe + both {model}_performance.json) copied into
`.planning/phases/15-dual-gpu-validation-subsets/artifacts/` and committed as
phase artifacts (the corrected archive list — zero plant remnants).

**D15-15 pytest updates (commit 02c5f83):** `SWEEP_ROOT` repointed to the
evidence-of-record `pipeline/finetuned-sweep-r2` (the old root is preserved
superseded evidence) + NEW `test_real_sweep_final_metrics_carry_eval_keys`
(skip-if-absent; asserts 12 final_metrics files, each with numeric eval_f1 —
the WINDOWS #45 fix pinned on real run artifacts). Suite **27 passed**.

**Gates (all green):** pytest subset suite 27; `make lint` + `make typecheck`
green; node 26/26; ci.yml hash pin `33d2252e…` matches; dnallm editable
re-verified intact after the `uv run` gates.

**Closure:** PROJECT.md "v1.3 small-sweep datasets" row — Pending → ✓ Landed
(citing the generator + isolation proofs + the executed sweep evidence);
REQUIREMENTS.md VAL-03 checkbox + traceability row → Complete with criterion
evidence; WINDOWS #45 → fixed via the ledger CLI (open 9→8, fixed 30→31) with
the full resolution naming 15-05 (f1af8d6/1d17145) + this green re-run; ROADMAP
15-03 checkbox marked.

## Deviations from Plan

### Carried from the halt session (part of the story)

**1. [Rule 1 - Stale expectation] Plan verify pinned emp_H3 test as 36/38** —
re-ran the verify leg with `test: (74, (37, 37))` (largest-remainder gives
label 0 the extra row; the 15-02 correction). Verify-command-side only.

**2. [Rule 3 - Blocking] Plan's summarize sequence omitted `mkdir` after
`rm -rf`** — inserted `mkdir -p …/data/model_performance`; the continuation
used the corrected sequence (first-attempt evidence preserved in the halt
logs).

**3. [Rule 1 - Lint/type] Gate failures in the new test code** — ruff SIM115
+ a ty diagnostic fixed (context-manager read, typed triples); commit fa04cb6.

**4. [Rule 4 → resolved out-of-plan] The halt itself** — the WINDOWS #45
producer/consumer seam gap + the arena premise error were architectural;
halted per D15-04, ruled option A by the maintainer, landed by 15-05, and
resolved by this continuation's green fresh-root re-run + consumption proof.
WINDOWS #45 is now closed.

### Continuation session

**None** — every continuation step ran green on first attempt (dry-run
manifest, 12/12 sweep, eval gate, export, summarize, archive, gates, ledger
closures). The two mid-verification KeyError aborts in this session's
throwaway inspection snippets (wrong dict-shape assumptions in the checker
scripts, not in product or test code) were fixed inline and never committed.

## Auth Gates

None (no credentials touched; the sweep ran fully offline per
HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE).

## Known Stubs

None — no stub code was written. The empty `{}` models_comparison.json of the
halt remains preserved halt evidence under phase15-evidence/consumption/
(runtime), never archived; the archived artifacts are the regenerated
non-empty products of the r2 sweep.

## Threat Flags

None beyond the plan's threat model. T-15-05 (silent full-data training): all
three tripwires green on the r2 run (manifest per-cell dataset_root, 12/12
ledger lanes on the subset root, subset-scale step counts 27/150). T-15-06
(consumption writing committed data): porcelain empty over `dnallm-mark/data/`
and `script/` at every step; outputs confined to tmp/evidence dirs + the
committed artifacts dir. T-15-SC: zero installs (`.venv/bin/python` used
directly for every chain command; dnallm editable verified intact before and
after the `uv run` gates).

## Self-Check: PASSED

- Archived artifacts FOUND: all five JSONs under
  `.planning/phases/15-dual-gpu-validation-subsets/artifacts/` (committed in
  02c5f83).
- Runtime evidence FOUND: `pipeline/finetuned-sweep-r2/dispatch_state.json`
  (done 12/12 skipped 0), 12 cell trees with all four artifacts (final_metrics
  eval-carrying), tee log, mid-run snapshots, SHA packs
  (sweep-r2-sha256.txt, artifacts-r2-sha256.txt), consumption-r2 tree + logs.
- Commits FOUND and ancestors of HEAD: 44e421c, fa04cb6, 012e526 (halt
  session), f20dcc7, 02c5f83 (continuation); ledger
  `gsd-plan-head-before-15-03` = 157610338849af8fe2bd53cedf322490d9bff5dd.
- Ledger state: WINDOWS #45 fixed (open 8 / fixed 31); REQUIREMENTS VAL-03
  complete; PROJECT small-sweep row done; ROADMAP 15-03 marked.
- No push performed (v1.3 local-commits-only policy held).
