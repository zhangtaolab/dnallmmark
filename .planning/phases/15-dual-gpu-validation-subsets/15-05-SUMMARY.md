---
phase: 15-dual-gpu-validation-subsets
plan: 5
subsystem: multi-gpu-dispatch-validation
tags: [gap-closure, windows-45, producer-fix, eval-metrics, option-a, contracts]
requires:
  - "15-03 halt evidence (Tasks 1-2 green, WINDOWS #45 recorded, arena premise error documented)"
  - "2026-10-21 maintainer option-A ruling (producer-side merge; deliberate narrow unfreeze of pipeline/run_finetune.py)"
provides:
  - "Producer side of WINDOWS #45 CLOSED: run_finetune captures trainer.evaluate() and persists it FLAT-ADDITIVE into final_metrics.json under the exact eval_* spellings the unmodified export/summarize chain resolves (eval_f1 -> metric_block f1 -> performance.f1 -> raw_score)"
  - "Tier-1 contract pins extended update-not-weakened: the captured-call locator + test_eval_results_merged_additively_into_final_metrics (flops < evaluate < merged re-write < marker copy + the literal additive merge expression) + module-docstring contract line"
  - "15-03-PLAN.md corrected to the true arena outputs (models_comparison_animal.json + models_comparison_microbe.json, zero plant remnants) ready for the 15-03 continuation's archive step"
affects:
  - "The 15-03 continuation (sweep re-run on pipeline/finetuned-sweep-r2 + consumption + archive + VAL-03 marks) — this plan's SUMMARY carries its pinned handoff"
  - "Phase 18 DOCS-01 (docs will describe the ruled option-A producer behavior)"
tech-stack:
  added: []
  patterns:
    - "Producer-side seam fix honoring D15-11: when a reader contract already resolves the needed key spellings, fix the producer and pin both frozen invariants (D-05 hardware-read scoping, WR-13 marker-last) with static-source ordering tests rather than touching the chain"
key-files:
  created:
    - .planning/phases/15-dual-gpu-validation-subsets/15-05-SUMMARY.md
  modified:
    - pipeline/run_finetune.py
    - tests/test_run_finetune_contracts.py
    - .planning/phases/15-dual-gpu-validation-subsets/15-03-PLAN.md
decisions:
  - "Option A implemented exactly as ruled (2026-10-21): eval_results = trainer.evaluate() stays OUTSIDE the rank guard (all ranks evaluate — DDP semantics preserved); the second rank-0 block merges merged = {**eval_results, **metrics} (training keys win every collision — 'epoch' keeps its training value, trainable_params_pct survives) and re-writes final_metrics.json; the trainer_state marker copy moved AFTER that re-write as the cell's final write (WR-13 stronger than the pre-fix code, where the discarded evaluate already ran after the marker)"
  - "Resulting pinned write order: final_metrics(v1) < flops write < evaluate < merged re-write < marker copy — the D-05 hardware reads (train_time/max_mem_gb/gpu_device) stay before evaluate so max_mem_gb still measures the training peak; a kill anywhere before the marker leaves no marker (re-run on resume); a failed evaluate hits the D-08 except-continue with no marker (also a re-run, never a falsely-done cell)"
  - "Tier-1 tests updated, NOT weakened: exactly ONE existing pin edited (test_flops_report_write_rank_guarded's locator statement_index now spells the captured call; its ordering assertion and everything else verbatim); the four pre-existing WR-13/D-05/trainable-params pins pass WITHOUT edits (76-suite green); one NEW pin (test_eval_results_merged_additively_into_final_metrics) asserts the full ordering + the additive merge literal + the second merged-dump write"
  - "15-03-PLAN.md's archive list corrected at all six baseline sites to animal/microbe (arena files group by DATASET Category per D-10 + MAJORITY_ARENA Multiple->Animals; emp_H3 Category Microbe) — plant count 0, animal 6, microbe 6, 'five archived JSONs', halt SUMMARY byte-untouched"
metrics:
  duration: 22 min
  completed: 2026-10-21
  tasks: 2 of 2
  commits: 2      # MEASURED: git rev-list --count f7a75b4..HEAD (task commits f1af8d6 + 1d17145; excludes this docs commit)
  plan_head_before: f7a75b445ae41fa8f959788cd73484bd7b505ca4
  plan_head_after: 1d171451a4cf8ac0154b6a4ba3d3bf0e30c0de42
status: complete
gap_closure: true
actuals:
  tokens: 7800    # chars/4 over the FULL realized ledger-to-HEAD diff (31309 chars: run_finetune +37, tests +103, 15-03-PLAN +11/-8, this SUMMARY, STATE/ROADMAP churn) vs estimate 15000
  tasks: 2
  commits: 2      # MEASURED: git rev-list --count f7a75b4..HEAD at SUMMARY-write time (task commits; the docs commit followed, total 3)
---

# Phase 15 Plan 5: WINDOWS #45 Producer Fix (option A) Summary

**One-liner:** run_finetune.py now captures `trainer.evaluate()` and merges it flat-additive into final_metrics.json (`merged = {**eval_results, **metrics}`, verbatim eval_* spellings) with the write order final_metrics(v1) < flops < evaluate < merged re-write < marker copy — D-05/WR-13 both preserved and newly pinned, argv byte-untouched (27 add_argument), zero chain changes — plus the 15-03 archive-list correction to the true arena outputs (animal/microbe, never plant).

## Status: COMPLETE (producer side only — WINDOWS #45 stays OPEN until the 15-03 continuation greens)

## What Was Executed

### Task 1 — Producer fix + tier-1 pin updates — COMPLETE (commit f1af8d6)

**Producer edit (confined to the :1636-1706 success block; nothing else in run_finetune.py touched):**

1. First final_metrics.json write kept VERBATIM (still carrying trainer.train() metrics + the trainable_params/total_params/trainable_params_pct update — the pre-existing pins key off this first occurrence).
2. flops_report block kept VERBATIM; the D-05 hardware reads (train_time from train_runtime, max_mem_gb from the peak-memory counter, gpu_device verbatim) precede the evaluate call, so max_mem_gb still measures the training peak; the pre-existing comment saying so stays true.
3. The trainer_state marker copy REMOVED from the end of the first rank-0 block.
4. The bare discarded `trainer.evaluate()` replaced by `eval_results = trainer.evaluate()` — still OUTSIDE the rank guard so ALL ranks evaluate (DDP semantics preserved).
5. New second rank-0 block, in the exact ruled order: `merged = {**eval_results, **metrics}` (additive-only, eval_results spread FIRST so existing training keys win every collision; FLAT and verbatim — no filtering, no renaming, no nesting), then the re-write `json.dump(merged, f, indent=4)`, then the marker copy as the block's and the cell's FINAL write. Merge comment cites WINDOWS #45 + the reader identity (run_record.metrics copies final_metrics verbatim via run_sweep :1446 + dispatch_core's write_cell_run_record; export_runs resolves eval_f1/eval_accuracy/... via _SUITE_ALIASES and eval_loss via PIPELINE_KEYS; bookkeeping like eval_runtime is harmlessly additive — resolve_metric_key returns None for it).
6. WR-13 ordering comment extended minimally: "Write final_metrics.json FIRST" and the flops_report.json mention untouched exactly where they were; one appended sentence names the post-evaluate merged re-write with the marker copy still last.

**Why both child types gain the fields with zero sweep/dispatch changes:** run_sweep (:1446) and dispatch_core's write_cell_run_record copy final_metrics.json keys VERBATIM into run_record.metrics, so static and dispatch children pick up the eval keys identically (the key_links seam honored — D15-11 zero chain modification).

**Tier-1 test updates (tests/test_run_finetune_contracts.py):**

- (a) `test_flops_report_write_rank_guarded`: ONLY the locator changed — `statement_index(src, "trainer.evaluate()")` → `statement_index(src, "eval_results = trainer.evaluate()")` (statement_index is line-start-anchored, so the old spelling cannot match the captured call) with its failure message updated to name the captured form; `assert flops_idx < evaluate_idx` and everything else VERBATIM.
- (b) NEW `test_eval_results_merged_additively_into_final_metrics` (directly after the guard test, established static-source style): pins the captured call; the strict ordering flops write < evaluate < marker copy (D-05 + WR-13); the literal merge statement `merged = {**eval_results, **metrics}` (the additive-only order — the T-15-09 tamper pin) between evaluate and the marker; a SECOND `open(outdir + "final_metrics.json"` write after the merge that also precedes the marker copy and dumps the merged payload (`json.dump(merged` — second occurrence, the first being WR-13's v1 write). Docstring cites WINDOWS #45, the 2026-10-21 option-A ruling, and the chain identity (both sweep tasks declare metric "f1" — the load-bearing merged key is eval_f1, resolved by export to metric_block "f1" and read by summarize at performance["f1"]).
- (c) Module docstring's tier-1 list gained the matching contract line (evaluate-result merge, option A ruling, ordering + additive semantics).
- (d) READ-ONLY confirmation, zero edits: tests/test_dispatch_core.py fake-child fixtures already fabricate eval keys (`{"eval_loss": 0.5, "eval_accuracy": 0.9}` at :274/:468; `{"eval_loss": 0.5}` at :413/:2830) — the CR-02/WR-11/export-visibility tests remain honest unchanged, proven by the green unmodified regression suites.

**Gates (all green):** `tests/test_run_finetune_contracts.py` 76 passed; `tests/test_dispatch_core.py + test_sweep.py + test_sweep_shard.py` 306 passed (unchanged); `make lint` + `make typecheck` green; ci.yml hash pin `33d2252e…` matches; porcelain over script/ + run_sweep.py + run_sweep_shard.py + dispatch_core.py EMPTY; run_finetune.py add_argument diff legs 0/0 and the file still carries exactly 27 add_argument lines. dnallm editable re-verified intact after the `uv run` gates (1.3.3 @ /root/autodl-tmp/Github/DNALLM). `.venv/bin/python` used directly for every pytest lane.

### Task 2 — 15-03-PLAN.md archive-list correction — COMPLETE (commit 1d17145)

All six baseline plant-filename sites corrected (baseline 6 lines: 11, 29, 35, 160 ×2 spots, 162, 167 + the "four archived" count at 168):

1. Frontmatter files_modified: the single plant entry replaced by TWO entries (artifacts/models_comparison_animal.json + artifacts/models_comparison_microbe.json).
2. must_haves truth: "emitting models_comparison.json + models_comparison_animal.json + models_comparison_microbe.json in the TMP tree".
3. must_haves artifacts: the plant entry replaced by the real grouping pair (animal: "iDNA_ABF_datasets__5mC: Category Multiple resolved to Animals via MAJORITY_ARENA"; microbe: "GUE__emp_H3: Category Microbe) — arena files group by DATASET Category, not model species").
4. Task-3 action, both spots: the emission assertion now names the three-file set with the Category rationale (5mC Multiple→Animals, emp_H3→Microbe), and the cp sentence lists all three comparison JSONs.
5. Task-3 verify: the plant `test -f` became two `test -f` checks (animal + microbe).
6. Acceptance: "…+ models_comparison_animal.json + models_comparison_microbe.json" and "contains the five archived JSONs" (global + animal + microbe + the two model performance files).

Verify green: plant count 0 / animal 6 / microbe 6 / "five archived JSONs" 1 / "four archived" 0 / 15-03-SUMMARY.md porcelain EMPTY (the historical halt evidence stays byte-untouched). 15-03 Task 2's output-root line untouched (the re-run root pin lives below, not in 15-03).

## Continuation Handoff (15-03 Task-3 resumption — NOT this plan's work; the orchestrator-ruled pins, verbatim)

- **Sweep re-run root PINNED: `pipeline/finetuned-sweep-r2`** — FRESH: the existing `pipeline/finetuned-sweep` root carries trainer_state markers for all 12 cells, so the resume-safe skip semantics would skip every cell and leave the stale eval-less final_metrics in place. The continuation adds the matching `.gitignore` entry adjacent to the existing one.
- After the re-run: Task 3's consumption + archive asserting the CORRECTED list (models_comparison.json + models_comparison_animal.json + models_comparison_microbe.json + both {model}_performance.json — five archived JSONs), then the VAL-03 / PROJECT.md / ROADMAP marks.
- **WINDOWS #45 stays OPEN until that continuation greens** (this plan closed the producer side only — VAL-03 is NOT marked done here; no requirements marked complete).
- The 12 existing sweep cells under `pipeline/finetuned-sweep/` are SUPERSEDED evidence (eval-less final_metrics) — never archived as phase artifacts.

## Deviations from Plan

None — plan executed exactly as written. Both tasks' automated verifies green on first run; no auto-fixes needed (the only test-file changes are the plan-specified locator update, the new pin, and the docstring line).

## Auth Gates

None.

## Known Stubs

None — no stub code written; every pinned statement exists in live source.

## Threat Flags

None beyond the plan's threat model. T-15-09 (additive-only merge): pinned by the literal merge expression + the pre-existing trainable-params pin passing unmodified in the same gate run. T-15-10 (write ordering): pinned both ways by the new test + the unmodified pre-existing order pins. T-15-SC (package installs): zero installs — stdlib-only edit, no uv sync, `.venv/bin/python` used directly.

## Self-Check: PASSED

- Files FOUND: pipeline/run_finetune.py (captured evaluate + merge + reordered marker), tests/test_run_finetune_contracts.py (locator + new pin + docstring line), 15-03-PLAN.md (animal 6 / microbe 6 / plant 0).
- Commits FOUND and ancestors of HEAD: f1af8d6 (Task 1), 1d17145 (Task 2); ledger gsd-plan-head-before-15-05 = f7a75b445ae41fa8f959788cd73484bd7b505ca4, measured count 2.
- Suites: contracts 76 green; dispatch+sweep+sweep_shard 306 green; lint/typecheck green; ci.yml hash pinned; chain porcelain empty; add_argument 27.
- NOT done by design (owned by the 15-03 continuation): sweep re-run on finetuned-sweep-r2, consumption/archive, VAL-03 marks, WINDOWS #45 closure.
- No push performed (v1.3 local-commits-only policy held).
