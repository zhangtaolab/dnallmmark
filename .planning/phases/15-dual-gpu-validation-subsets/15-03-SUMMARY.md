---
phase: 15-dual-gpu-validation-subsets
plan: 3
subsystem: multi-gpu-dispatch-validation
tags: [dispatch, subsets, real-sweep, val-03, halted-at-consumption]
requires:
  - "15-01 smoke green (finetuned-smoke-r2 done 2/2) + 15-02 generator + 15-04 run_record writer"
provides:
  - "REAL 5% subsets materialized for exactly the two sweep tasks with research-table-exact stratification (emp_H3 test 37/37 per the 15-02 Rule-1 correction) + proven registry isolation"
  - "12-cell dual-GPU dispatch sweep GREEN on one shared root: status done 12/12, 0 skipped, all claims lane-pinned to the subset root, subset-scale step counts (Pitfall 1's three tripwires all green)"
  - "D15-15 real-artifact pytest checks (5 skip-if-absent pins; suite 26 green; CI-safe)"
  - "HALT EVIDENCE: the producer->consumer eval-metrics seam gap (run_finetune discards trainer.evaluate(); WINDOWS #45) + the arena-grouping premise error blocking Task 3's emission/archive criteria"
affects:
  - "VAL-03 completion blocked pending remediation ruling (the 15-01->15-04 precedent pattern)"
  - "Phase 18 DOCS-01 (docs will describe the ruled remediation, not the blocked path)"
tech-stack:
  added: []
  patterns:
    - "Halt-at-consumption discipline (D15-04): when a plan premise fails at the seam, preserve all runtime evidence, land the independent green parts, record WINDOWS, route the architectural decision to the maintainer"
key-files:
  created:
    - .planning/phases/15-dual-gpu-validation-subsets/15-03-SUMMARY.md
  modified:
    - .gitignore
    - tests/test_subset_datasets.py
decisions:
  - "Task 3 HALTED at the consumption-proof criterion per D15-04 discipline: eval metrics never persist into final_metrics.json (run_finetune.py:1706 bare trainer.evaluate() discard, faithful port since c6b3137) so the real export emits empty score slots and summarize's aggregate_models returns {} — every species file (incl. the plan-required plant) is skipped by the if species_comparison: guard"
  - "Independent plan-premise error: the arena chain groups by DATASET Category (5mC Multiple->Animals, emp_H3 Microbe), not model species — models_comparison_plant.json is unproducible from this dataset pair even with real scores; the archived-artifact list needs replan"
  - "The D15-15 real-artifact checks landed independently of the blocked criterion (they pin Task-1/Task-2 outcomes; 26-test suite green; CI-safe skip-if-absent)"
metrics:
  duration: 20 min
  completed: 2026-10-20
  tasks: 2 of 3 (Task 3 landed its independent D15-15 leg; consumption criterion blocked)
  commits: 2      # task commits (44e421c + fa04cb6); MEASURED ledger-to-HEAD incl. this docs commit = 3
  plan_head_before: 157610338849af8fe2bd53cedf322490d9bff5dd
status: blocked
actuals:
  tokens: 9000    # chars/4 over the realized diffs (.gitignore +6, tests +82, this SUMMARY)
  tasks: 2        # fully complete (Tasks 1-2); Task 3 partial (blocked leg documented)
  commits: 2      # MEASURED: git rev-list --count 1576103..HEAD (excludes this docs commit)
---

# Phase 15 Plan 3: Small Real Sweep Summary — HALTED at Task 3 (consumption seam gap)

**One-liner:** Tasks 1-2 are fully green — REAL 5% subsets with research-table-exact stratification, then a 12-cell dual-GPU dispatch sweep (270 s, 12/12, 0 skipped, subset-scale steps, both GPUs) — but Task 3 halted at the consumption proof on a pre-existing producer gap: run_finetune discards `trainer.evaluate()` results, so no eval scores ever reach `final_metrics.json`/`run_record.json`, the real export emits empty score slots, and `summarize_comparison` emits an empty `models_comparison.json` while skipping every species file; an independent plan-premise error (arena files group by DATASET Category — Animals/Microbe, never Plants for this pair) means the plant artifact is unproducible even after a producer fix. Ruled remediation required (the 15-01 → 15-04 precedent); D15-15 real-artifact checks landed independently.

## Status: BLOCKED at Task 3 (Tasks 1-2 complete; Task 3's D15-15 leg landed)

## What Was Executed

### Task 1 — Sweep assets + REAL subset generation + isolation proof + gitignore — COMPLETE (commit 44e421c)

- **Precondition asserted read-only:** both smoke roots terminal (`finetuned-smoke` and `finetuned-smoke-r2` `dispatch_state.json` status `done`, 2/2). D15-14 preflight: dnallm editable 1.3.2 @ `/root/autodl-tmp/Github/DNALLM`, `torch.cuda` 2 devices, both GPUs 0% util.
- **Assets acquired (modelscope, official/verified channels):**
  - `zhangtaolab/plant-dnamamba-6mer` → `/root/autodl-tmp/dnallmmark-data/models/plant-dnamamba-6mer` — **66 s**, config.json FLAT in the model dir (12 files, safetensors+bin ~747 MB).
  - `dataset lgq12697/GUE --include "emp_H3/*"` → `datasets/GUE/emp_H3` — **3 s**, rows **11971/1497/1497 == registry EXACTLY** (T-15-01).
- **REAL subsets generated (0 s, D15-05/D15-08 scope — only the two sweep tasks):**
  `.venv/bin/python script/make_subset_datasets.py --dataset-root /root/autodl-tmp/dnallmmark-data --output-root $(pwd)/pipeline/datasets-smoke --registry-dir $(pwd)/pipeline/registry-smoke --models plant-dnabert-6mer,plant-dnamamba-6mer --tasks iDNA_ABF_datasets__5mC,GUE__emp_H3 --fraction 0.05 --seed 42`
  Measured: 5mC **105/11/117** (53/52, 6/5, 59/58); emp_H3 **598/74/74** (291/307, 36/38, **37/37 test** — the 15-02 Rule-1 correction; see Deviations 1). Subset registry `Train/Dev/Test` == on-disk rows; `Dataset_path` official-relative verbatim.
- **Isolation proven (D15-07):** sha256 of `pipeline/{models,datasets}_info.json` + `custom_models.json` (custom_datasets.json absent) **byte-unchanged** before/after (`registry-hash-{before,after}.txt`); path assertions green — datasets-smoke ≠ real datasets root, finetuned-sweep ≠ directories.json `output_root` (`/root/autodl-tmp/dnallmmark-data/finetuned`), registry-smoke ≠ `pipeline/` ≠ custom dir.
- **Gitignore:** `pipeline/finetuned-sweep/` added adjacent to the 15-02 entries (baseline 0 → 1), with the adjacency rationale in the comment.
- **Subset registry sha256 (D15-16):** models `7a463bd5…f49cac`, datasets `497d09f7…0b9267`.
- **Empty custom dir prepared:** `/root/autodl-tmp/phase15-evidence/empty-custom/` for Task 2's `DNALLMMARK_CUSTOM_REGISTRY_DIR` pin.

### Task 2 — 12-cell dispatch sweep on both GPUs — COMPLETE (no tracked files; evidence preserved)

Run plan printed first (D15-13). **Dry-run** into the throwaway root (`sweep-dryrun-root`): `[Dry-run] [Dispatch] 12 planned cell(s)`; manifest asserts green — 12 cells, per-cell `dataset_root` == the subset root, `model_root` == the real model root, `orchestrator_mode: "dispatch"` (Pitfall 1 tripwire 1).

**REAL RUN** (identical argv minus `--dry-run`, `--output-root $(pwd)/pipeline/finetuned-sweep`, `DNALLMMARK_CUSTOM_REGISTRY_DIR=empty-custom`, `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`, tee → `phase15-evidence/sweep-dispatch.log`):

- **Wall: 270 s** (2026-10-20T15:52:55Z → 15:57:25Z, exit 0). run_id `04f12add9015456bb9710de982c43dc3`.
- **Terminal state:** `dispatch_state.json` status **done**, counts **completed 12 / total 12 / failed 0 / skipped 0** — the adjacency edge holds: the smoke roots' trainer_state markers for the identical cell key never skipped a sweep cell.
- **Per-cell artifacts:** all 12 cell dirs carry `final_metrics.json`, `flops_report.json`, `trainer_state.json`, `run_record.json` (the 15-04 writer proven on a real multi-model sweep).
- **Ledger:** exactly 12 claims; every claim's lane `dataset_root` endswith `/pipeline/datasets-smoke` (tripwire 2). Workers: w0 gpu=0 **8 cells**, w1 gpu=1 **4 cells** — both GPUs produced cells.
- **Step-count sanity (tripwire 3):** 5mC cells `max_steps=27` == ceil(105/4); emp_H3 cells `max_steps=150` == ceil(598/4) — subset-scale, never the full-split 528/2993. No full-data training signature.
- **plant-dnamamba-6mer:** trained cleanly on both tasks (Pitfall 8 contingency NOT needed — no model swap).
- **Mid-run observation evidence (D15-10):** `dispatch_state.midrun-sweep.json` (status running, 6/12, both workers in-flight on separate GPUs) + `sweep-table-snapshot.midrun.txt` (live plain-line table) + GPU util snapshot.
- **D15-16 SHA256 pack:** `phase15-evidence/sweep-sha256.txt` — dispatch_state + all 12 cells' final_metrics + flops_report (24 hashes; spot-check table below; full file is the evidence of record).

| Artifact | SHA256 (first 16) |
|---|---|
| dispatch_state.json | `34bff2b8bb282dca` |
| plant-dnabert-6mer/5mC/seed_42 final_metrics | `a2761514547137df` |
| plant-dnabert-6mer/5mC/seed_42 flops_report | `a7d39ba2e1f2708d` |
| plant-dnamamba-6mer/GUE/seed_42 final_metrics | (see sweep-sha256.txt) |

Task 2 declares no tracked files (sweep artifacts are gitignored runtime; worker dispatch logs match the pre-existing `*.log` pattern) — no commit, per the plan's own `<files>` contract.

### Task 3 — Consumption chain — BLOCKED at the emission/archive criterion (D15-11)

**What ran green (zero chain modifications, committed data untouched):**

1. **Real export (not dry-run)** from the sweep root with the exporter's OWN flags pointed at the subset registry: exit 0, emitted **2 `{model}_performance.json` + 2 `{task}_task_performance.json`** into `/root/autodl-tmp/phase15-evidence/consumption/`. Dataset blocks are TRUTHFUL subset blocks (train 105 / dev 11 / test 117 from the subset registry); FLOPs and runtime are real numbers.
2. **Summarize over the tmp data tree** (copytree idiom, CWD = tmp tree): exit 0, `models_comparison.json` + `manifest.json` regenerated IN THE TMP TREE.
3. **Read-only proofs:** `git status --porcelain` over `dnallm-mark/data/` EMPTY and over `script/` EMPTY — the D15-11 zero-chain-modification and committed-data-untouched prohibitions held.
4. **D15-15 real-artifact pytest checks LANDED** (commit fa04cb6): 5 skip-if-absent pins (smoke roots done 2/2; sweep root done 12/12 skipped 0 — the adjacency edge; subset rows == registry per task). Suite 26 passed; `make lint` + `make typecheck` + node 26/26 + ci.yml hash pin all green; dnallm editable intact after the `uv run` gates.

**What failed (the halt):**

- `models_comparison.json` regenerated as **`{}` (2 bytes)** and **`models_comparison_plant.json` was NOT emitted** — the tmp tree's plant/animal/microbe files are byte-identical copies of the committed files (plain `cp -r` copies; sizes equal committed), NOT products of this sweep. Archiving them as phase artifacts would fabricate evidence.

**Root cause 1 — producer seam gap (WINDOWS #45, architectural):** `pipeline/run_finetune.py:1706` calls bare `trainer.evaluate()` and **discards the result** (faithful port; unchanged since first commit c6b3137). Eval scores survive only inside `checkpoint-*/trainer_state.json` `log_history` (verified present: `eval_f1: 0.714…` in the 5mC seed_42 cell). `export_runs`'s documented contract reads `final_metrics.json` keys verbatim (plus the suite's `seed_result.json` adoption — our subprocesses never write it). Measured uniformity: **0/12 sweep cells and 0/2 smoke cells carry any eval score metric** in `run_record.metrics`. With all score slots `""`, `aggregate_models` returns `{}` and `summarize_comparison`'s `if species_comparison:` guard skips every species file (only the unconditional global write fires).

**Root cause 2 — arena premise error (plan-side):** the plan requires the plant file because "both models are plants". The arena chain groups by **DATASET Category** (the D-10 registry authority), not model species: `iDNA_ABF_datasets__5mC` is `Multiple` → resolved to **Animals**; `GUE__emp_H3` is **Microbe**. Even with real scores, this dataset pair emits `models_comparison_animal.json` + `models_comparison_microbe.json` — **never `_plant.json`**.

**Why this is a halt, not an auto-fix (Rule 4):** every remediation shape touches a frozen, test-pinned contract —
- **Option A:** merge `trainer.evaluate()` results into `final_metrics` in run_finetune — reorders the WR-13 artifact chain and/or pollutes the D-05 training-peak memory scoping (evaluate allocates before the flops_report hardware read);
- **Option B:** harvest `trainer_state.log_history` at record-write time (dispatch_core writer / `run_sweep._new_record` — the schema authority 15-04 just froze);
- **Option C:** exporter-side adoption of trainer_state log_history — **prohibited outright** by this plan's D15-11 zero-chain-modification.
Plus the sweep's `final_metrics.json` content would change semantics post-fix (re-run needed for truthful artifacts), and the archive list must be replanned (animal/microbe vs plant). Choosing among these is a maintainer decision — the same situation class that halted 15-01 and was resolved by plan 15-04.

**Evidence preserved:** `phase15-evidence/consumption/` (task_performance/, seed_stats/, model_performance/, data/ tmp tree), `consumption-export.log`, `consumption-summarize.log` (full console output + the `{}` file content + species-file mtime/size proof they are cp copies), the intact sweep root, and this record.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Stale expectation] Plan verify pinned emp_H3 test as 36/38**
- **Found during:** Task 1 verify
- **Issue:** the plan's inline expectation tuple for the emp_H3 test split repeats the research table's inconsistent allocation; the pinned largest-remainder rule yields **37/37** (quotas 36.68/37.32 → label 0 takes the extra row), exactly as 15-02's SUMMARY documented and the orchestrator's required-reading note flagged.
- **Fix:** re-ran the verify leg with `test: (74, (37, 37))`; all row counts and the other five splits matched unchanged. The generator itself needed no change.
- **Files modified:** none (verify-command-side correction only)
- **Commit:** n/a (evidence: this record + 15-02-SUMMARY deviation 1)

**2. [Rule 3 - Blocking] Plan's summarize command sequence omitted `mkdir` after `rm -rf`**
- **Found during:** Task 3 Step 2
- **Issue:** `rm -rf .../data/model_performance` followed by `cp *.json .../data/model_performance/` fails (plain cp needs an existing target dir); the first summarize attempt then hit the script's lenient missing-input path (prints `Error: Could not find input directory` and **returns exit 0** — pre-existing script idiom) — a silent no-op that would have passed an inattentive rc check.
- **Fix:** inserted `mkdir -p .../data/model_performance` between the rm and cp, rebuilt the tmp tree fresh, re-ran. Both attempts' console output preserved in evidence logs.
- **Files modified:** none (command-sequence-side fix only; zero chain modifications held)

**3. [Rule 1 - Lint/type] Gate failures in the new test code**
- **Found during:** Task 3 gates
- **Issue:** ruff SIM115 (bare `open`) and a ty unsupported-`/` diagnostic (union-typed dict value) in the new real-artifact pins.
- **Fix:** context-manager read + restructured `SUBSET_EXPECT` as typed triples threaded through the parametrize signature. All gates re-run green.
- **Files modified:** tests/test_subset_datasets.py
- **Commit:** fa04cb6

### Halt (Rule 4 — maintainer decision required)

**4. Eval-metrics producer/consumer seam gap + arena premise error — Task 3's consumption criterion unmeetable as written.** Full analysis above; WINDOWS #45 recorded (kind `unmet-truth`). Remediation options A/B/C prepared for a ruling; VAL-03 stays open; the PROJECT.md small-sweep row stays Pending (marking it done would overstate — the subset materialization itself IS landed, but VAL-03's end-to-end consumption is not).

## Auth Gates

None (modelscope downloads used the box's pre-authenticated channel; no credentials touched).

## Known Stubs

None — no stub code was written. (The empty `{}` models_comparison.json is a runtime artifact of the seam gap, preserved as halt evidence under phase15-evidence/, NOT archived as a phase artifact.)

## Threat Flags

None beyond the plan's threat model. T-15-05 (silent full-data training): all three tripwires verified green (manifest per-cell dataset_root, 12/12 ledger lanes, subset-scale step counts). T-15-06 (consumption writing committed data): porcelain empty over `dnallm-mark/data/` at every step; outputs confined to tmp/evidence dirs. T-15-SC: zero installs (downloads via the locked modelscope CLI only; `.venv/bin/python` used directly for chain commands; dnallm editable verified intact after every `uv run` gate).

## Self-Check: PARTIAL (halt state verified)

- Files FOUND: `.gitignore` (entry present, count 1), `tests/test_subset_datasets.py` (26 tests green), this SUMMARY.
- Commits FOUND and ancestors of HEAD: 44e421c (Task 1), fa04cb6 (Task 3 D15-15 leg), dd5b1e7 (this docs commit); ledger `gsd-plan-head-before-15-03` = 157610338849af8fe2bd53cedf322490d9bff5dd, measured 3.
- Runtime evidence FOUND: `pipeline/finetuned-sweep/dispatch_state.json` (done 12/12 skipped 0), 12 cell trees with all four artifacts, dry-run manifest, tee log, mid-run snapshots, 24-hash SHA pack, consumption tree + logs.
- Blocked items (NOT done, by design of the halt): archived artifacts dir, PROJECT row closure, ROADMAP/REQUIREMENTS VAL-03 marks, state.advance-plan.
- No push performed (v1.3 local-commits-only policy held).
