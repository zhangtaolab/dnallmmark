---
phase: 15-dual-gpu-validation-subsets
verified: 2026-10-21T01:43:41Z
status: passed
score: 7/7 must-haves verified
covered_files:
  - .gitignore
  - .planning/PROJECT.md
  - .planning/REQUIREMENTS.md
  - .planning/WINDOWS.md
  - .planning/phases/15-dual-gpu-validation-subsets/15-01-PLAN.md
  - .planning/phases/15-dual-gpu-validation-subsets/15-01-SUMMARY.md
  - .planning/phases/15-dual-gpu-validation-subsets/15-02-PLAN.md
  - .planning/phases/15-dual-gpu-validation-subsets/15-02-SUMMARY.md
  - .planning/phases/15-dual-gpu-validation-subsets/15-03-PLAN.md
  - .planning/phases/15-dual-gpu-validation-subsets/15-03-SUMMARY.md
  - .planning/phases/15-dual-gpu-validation-subsets/15-04-PLAN.md
  - .planning/phases/15-dual-gpu-validation-subsets/15-04-SUMMARY.md
  - .planning/phases/15-dual-gpu-validation-subsets/15-05-PLAN.md
  - .planning/phases/15-dual-gpu-validation-subsets/15-05-SUMMARY.md
  - .planning/phases/15-dual-gpu-validation-subsets/artifacts/models_comparison.json
  - .planning/phases/15-dual-gpu-validation-subsets/artifacts/models_comparison_animal.json
  - .planning/phases/15-dual-gpu-validation-subsets/artifacts/models_comparison_microbe.json
  - .planning/phases/15-dual-gpu-validation-subsets/artifacts/plant-dnabert-6mer_performance.json
  - .planning/phases/15-dual-gpu-validation-subsets/artifacts/plant-dnamamba-6mer_performance.json
  - Makefile
  - docs/multi-gpu.md
  - pipeline/dispatch_core.py
  - pipeline/run_finetune.py
  - script/make_subset_datasets.py
  - tests/fixtures/subset_fixture/dev.csv
  - tests/fixtures/subset_fixture/test.csv
  - tests/fixtures/subset_fixture/train.csv
  - tests/test_dispatch_core.py
  - tests/test_run_finetune_contracts.py
  - tests/test_subset_datasets.py
covered_digest: "v3:sha256:f40c8e2af656f0a82ec79ea83d3bd2bfefa6f66b667bcc86579735c7f60f83a3"
behavior_unverified: 0
overrides_applied: 0
unverified_prohibition_flags: # 17 judgment-tier prohibitions auto-judged HELD (ADR-550 autonomous mode, consistent with Phases 13/14) — non-authoritative LLM-judge verdicts with cited evidence, NOT human-test items; human review recommended
  - plan: "15-01"
    prohibition: "The smoke must not modify any pipeline dispatch/training code — the Phase 13/14 CLI runs VERBATIM; defects route through the normal fix flow (D15-04, D15-16), never in-phase redesign"
    verdict_held_evidence: "15-01's own commits touched only docs/multi-gpu.md, .planning ledgers, .gitignore (5295cbd docs-only). run_finetune.py/dispatch_core.py changes came from the maintainer-ruled gap-closure plans 15-04 (Option 1, commits 9c22787/8c5e8b9) and 15-05 (option A, f1af8d6/1d17145) plus the sanctioned code-review loop (227a34a/2becdb4/bbdac40) — exactly the normal-fix-flow routing the prohibition itself names"
  - plan: "15-01"
    prohibition: "The smoke must not write into dnallm-mark/data/ or any real (non-smoke) output root — explicit --output-root/--log_dir only, roots distinct from the directories.json values"
    verdict_held_evidence: "git status --porcelain -- dnallm-mark/data/ empty (re-checked this pass); smoke root pipeline/finetuned-smoke-r2 is distinct from the directories.json output_root /root/autodl-tmp/dnallmmark-data/finetuned; doc command carries explicit absolute --output-root/--log_dir (docs/multi-gpu.md:248-252)"
  - plan: "15-01"
    prohibition: "The docs rewrite must not describe any command that was not executed (procedure/doc identity, D15-02)"
    verdict_held_evidence: "The documented argv (finetuned-smoke-r2 root, seeds 42,43, 1 epoch) matches the on-disk dispatch_state.json (run_id 7759c2cc0536…, started 2026-10-20T15:20:00Z, done 2/2) and the tee log /root/autodl-tmp/phase15-evidence/smoke-dispatch-r2.log; the doc's consumption step re-executed by this verifier reproduced the doc's exact output line ([Dry-run] 2 run record(s) across 1 model(s) / 1 task(s), exit 0)"
  - plan: "15-02"
    prohibition: "The generator must never write into official pipeline/{models,datasets}_info.json or user custom registry files — subsets are a third registry class, isolated by discipline and by hash assertions (D15-07)"
    verdict_held_evidence: "git porcelain over pipeline/models_info.json + pipeline/datasets_info.json empty; tests/test_subset_datasets.py carries an autouse official+custom sha256 pin across every suite run (suite re-run this pass: 29 passed); generator refuses --registry-dir resolving onto official/custom (path-based refusal); CR-01 guard additionally refuses --output-root == --dataset-root (script/make_subset_datasets.py:270-272)"
  - plan: "15-02"
    prohibition: "The generator must not alter official registry keys or Dataset_path values in the subset registry (the child-resolution seam depends on them verbatim)"
    verdict_held_evidence: "pipeline/registry-smoke/datasets_info.json read this pass: Dataset_path values verbatim official (datasets/iDNA_ABF_datasets/5mC, datasets/GUE/emp_H3); only Train/Dev/Test replaced by measured counts + subset provenance {generator, seed, fraction, actual_fraction, source_counts}"
  - plan: "15-02"
    prohibition: "The generator must not emit a 0-row split CSV (a 0-row dev/test split breaks DNADataset; the floor-of-1 rule exists to prevent it)"
    verdict_held_evidence: "k = max(1, int(n × fraction)) capped at n literal present in source+docstring (3 occurrences); floor-rule test (12/19/20 → k=1, never 0, capped at n, fraction 1.0 → n) inside the 29-passed suite"
  - plan: "15-03"
    prohibition: "The sweep must not train on full datasets while the registry/manifest claims subset counts — silent wrong numbers on the consumption path (Pitfall 1)"
    verdict_held_evidence: "All three tripwires re-checked on disk: max_steps 27 (5mC, = ceil(105/4)) and 150 (emp_H3, = ceil(598/4)) in all 12 trainer_state.json — never full-split 528/3000; exactly 12 ledger claims, every lane dataset_root endswith /pipeline/datasets-smoke; dry-run manifest assertion recorded in 15-03-SUMMARY"
  - plan: "15-03"
    prohibition: "The consumption proof must not modify export_runs.py, summarize_comparison.py, or any data-chain code (D15-11 zero chain modification)"
    verdict_held_evidence: "git status --porcelain -- script/ empty at HEAD (re-checked this pass); .github/workflows/ci.yml blob hash 33d2252eb594e0faecece9e8015a332d8d6479ef matches the pre-phase pin (byte-identical)"
  - plan: "15-03"
    prohibition: "The consumption proof must not write into the committed dnallm-mark/data/ tree — tmp-tree idiom only"
    verdict_held_evidence: "git status --porcelain -- dnallm-mark/data/ empty; consumption outputs live under /root/autodl-tmp/phase15-evidence/consumption-r2/ (tmp tree) + the committed phase artifacts dir only"
  - plan: "15-03"
    prohibition: "Mid-run defects must not be fixed by in-phase redesign of the dispatch engine — normal fix flow with evidence preserved (D15-04/D15-16)"
    verdict_held_evidence: "The WINDOWS #45 halt followed D15-04 stop discipline (halt commit 012e526, evidence preserved, superseded root never archived); remediation went through the maintainer option-A ruling and gap-closure plan 15-05, then a fresh-root re-run — no in-run redesign"
  - plan: "15-04"
    prohibition: "No engine behavior changes beyond the record write: claim state semantics, the CR-02 existence check, the relaunch skip filter, dispatch_state writes, spawn kwargs, the dry-run branch, and static mode stay byte-compatible (the shard byte-identity tripwire must stay green)"
    verdict_held_evidence: "15-04-SUMMARY records 305 passed (98 prior dispatch + 7 new contract tests + sweep + shard suites incl. the byte-identity tripwire); this pass re-ran 5 named record-contract tests (shape parity, no-overwrite refusal, stale-failed replacement, export dry-run visibility, WR-02 eval-failure) — all PASS; skipped cells gain no record pinned by test_dispatch_skipped_cell_gains_no_record (suite green)"
  - plan: "15-04"
    prohibition: "run_sweep.py and run_finetune.py must NOT be modified — the fix reuses run_sweep's builder and constants; the schema authority stays frozen"
    verdict_held_evidence: "15-04's own diff touched only pipeline/dispatch_core.py + tests + 15-03-PLAN.md (commits 9c22787/8c5e8b9; porcelain empty over both frozen files at 15-04 time). run_finetune.py was later modified only by the separately-ruled 15-05 unfreeze and the code-review WR-02 fix — outside this prohibition's scope"
  - plan: "15-04"
    prohibition: "No new schema file, no new dependency, no GPU, no real children in tests; the dispatch test module stays stdlib+jsonschema pure (export_runs is invoked as a sys.executable subprocess — D14-10)"
    verdict_held_evidence: "No new files under schemas/; generator/dispatch changes import nothing beyond stdlib (script/make_subset_datasets.py imports: argparse/csv/json/os/random/pathlib); export dry-run visibility test runs export_runs.py as a subprocess (re-run this pass: PASS in 0.75 s, CPU-only)"
  - plan: "15-05"
    prohibition: "No changes to script/export_runs.py, script/summarize_comparison.py, pipeline/run_sweep.py, pipeline/run_sweep_shard.py, pipeline/dispatch_core.py — producer-side ONLY (D15-11 holds)"
    verdict_held_evidence: "git porcelain over script/ + pipeline/run_sweep.py + pipeline/run_sweep_shard.py + pipeline/dispatch_core.py empty at HEAD; dispatch_core.py's Phase-15 hunks belong to 15-04 and the WR-01 review fix (2becdb4), not to 15-05's commits (f1af8d6/1d17145 touched run_finetune.py, tests, 15-03-PLAN.md only)"
  - plan: "15-05"
    prohibition: "No argv/parse_args surface changes (no new flags, no help-text edits — add_argument count pinned at 27)"
    verdict_held_evidence: "grep -c add_argument pipeline/run_finetune.py == 27 (re-counted this pass); 15-05 SUMMARY records diff legs 0/0 on add_argument lines"
  - plan: "15-05"
    prohibition: "No weakening or removal of existing contract pins — the one edited locator keeps its ordering assertion verbatim, and the four WR-13/D-05/trainable-params order pins must pass without edits"
    verdict_held_evidence: "test_flops_report_write_rank_guarded still asserts flops_idx < evaluate_idx (locator re-spelled to the captured call per plan); the new pin test_eval_results_merged_additively_into_final_metrics re-run this pass: PASS; 15-05 SUMMARY records the contracts suite 76 green with exactly one locator edit"
  - plan: "15-05"
    prohibition: "No sweep re-run in THIS plan — the 15-03 continuation owns the re-run (fresh root pipeline/finetuned-sweep-r2), consumption, archive, and the VAL-03 marks; WINDOWS #45 stays open until that continuation greens"
    verdict_held_evidence: "15-05's commits (f1af8d6, 1d17145) contain no sweep-run changes; the re-run landed with the 15-03 continuation (f20dcc7 gitignore + 02c5f83 consumption/closure, after 1d17145); WINDOWS #45 closed only in that continuation (2026-10-21T00:21:36Z)"
---

# Phase 15: Dual-GPU Validation & Subsets Verification Report

**Phase Goal:** The dispatch orchestrator is proven on the local 2× RTX 5090 — the docs/multi-gpu.md N=2 smoke passes (WINDOWS #21 closed, D-05 revised) and a small real sweep over pre-materialized 5% stratified subsets runs both GPUs end-to-end through merge and the data chain
**Verified:** 2026-10-21T01:43:41Z
**Status:** passed (complete with 17 flagged prohibitions — non-authoritative auto-judges, see `unverified_prohibition_flags`)
**Re-verification:** No — initial verification

## Goal Achievement

This is a GPU-validation phase; the goal IS real runtime behavior. The runtime evidence was verified directly on disk (state files, per-cell artifacts, tee'd dispatcher logs, SHA packs), and the consumption seams were **re-executed by this verifier** rather than trusted from SUMMARY claims. All evidence below was gathered this pass unless marked otherwise.

### Observable Truths

Consolidated from the 4 ROADMAP success criteria (the contract) + the five plans' must_haves (VAL-01: 15-01; VAL-02: 15-02; VAL-03: 15-03 + gap-closures 15-04/15-05).

| # | Truth | Status | Evidence |
| - | ----- | ------ | -------- |
| 1 | N=2 smoke executed REAL 1-epoch training on both local GPUs with all four D15-02 criteria green (VAL-01) | ✓ VERIFIED | `pipeline/finetuned-smoke-r2/dispatch_state.json`: status `done`, counts completed=total=2, failed=skipped=0, run_id 7759c2cc…, workers {gpu:"0", cells:1, completed:1} + {gpu:"1", cells:1, completed:1}; both cell dirs carry final_metrics.json + flops_report.json + trainer_state.json + run_record.json; tee log `smoke-dispatch-r2.log` ends `status=done … done=2/2`; consumption dry-run **re-run this pass**: `[Dry-run] 2 run record(s) across 1 model(s) / 1 task(s)` exit 0 |
| 2 | docs/multi-gpu.md carries the executed procedure; WINDOWS #21 closed; D-05 revised in-doc + PROJECT.md | ✓ VERIFIED | Doc contains `--mode dispatch` (2×), `--seeds 42,43` (4×), `双卡验证机` (3×), retired phrase `验证在他机` 0× (baseline 1); documented argv (:248-252, `finetuned-smoke-r2` root) matches the on-disk run; WINDOWS #21 + #44 rows carry `fixed` with evidence-bearing resolutions; PROJECT.md D-05 row `✓ Landed` (only remaining Pending is the deliberate DDP-not-implemented row) |
| 3 | Subset generator produces deterministic stratified 5% subsets with measured counts in a dedicated registry (VAL-02) | ✓ VERIFIED | `script/make_subset_datasets.py` 631 lines (min 200), stdlib-only imports (argparse/csv/json/os/random/pathlib — no numpy), D15-06 rule literal `max(1, int(n` present; on-disk subsets re-counted this pass: 5mC 105/11/117 with classes (53,52)/(6,5)/(59,58); emp_H3 598/74/74 with (291,307)/(36,38)/(37,37 — the 15-02 Rule-1 largest-remainder correction); subset registry Train/Dev/Test equal the CSV rows, official `Dataset_path` verbatim, `subset` provenance object present |
| 4 | Run-twice byte-identity + third-registry-class isolation (official/custom registries untouched) | ✓ VERIFIED | Suite **re-run this pass**: `pytest tests/test_subset_datasets.py -q` → **29 passed, 0 skipped** (byte-identity, stratification math, floor rule, ordering, registry fidelity, isolation sha256 pins, fail-fast, output containment); `git status --porcelain` over `pipeline/models_info.json` + `pipeline/datasets_info.json` + `dnallm-mark/data/` empty; CR-01 root-equality refusal in source (:270-272) |
| 5 | 12-cell dual-GPU dispatch sweep over the pre-materialized subsets: done 12/12, 0 skipped, subset-scale training, both GPUs (VAL-03) | ✓ VERIFIED | `pipeline/finetuned-sweep-r2/dispatch_state.json`: status `done`, completed=total=12, skipped=0, run_id 4e74c92d…, workers gpu 0 (4 cells) + gpu 1 (8 cells); all 12 cell dirs carry the 4 artifacts; **eval_f1 numeric in ALL 12 final_metrics (read this pass)** and mirrored into run_record.metrics (spot: 0.7142857142857143); max_steps 27/150 = subset scale (ceil(105/4), ceil(598/4)) — never full-split 528/3000; exactly 12 ledger claims, every lane `dataset_root` ends `/pipeline/datasets-smoke`, claim gpu tokens {0,1}; adjacency edge proven: identical cell key exists in the smoke root yet skipped==0 on the fresh sweep root |
| 6 | Zero-modification consumption: sweep root → export → summarize → non-empty global/animal/microbe JSONs, archived | ✓ VERIFIED | 5 archived JSONs under `artifacts/` non-empty; **content-level cross-check this pass**: animal avg_raw == 5mC f1 EXACTLY (0.5952380952380952 / 0.5860805860805861), microbe avg_raw == emp_H3 f1 EXACTLY (0.6906149119559357 / 0.6731980437862791), global samples=2 ranks 1/2 — dataset-Category grouping (5mC Multiple→Animals, emp_H3→Microbe) confirmed; dry-run over sweep root **re-run**: `[Dry-run] 12 run record(s) across 2 model(s) / 2 task(s)` exit 0; porcelain over `script/` empty; ci.yml hash 33d2252eb594e0faecece9e8015a332d8d6479ef matches pin |
| 7 | Gap closures wired and pinned: dispatch run_record writer (15-04) + producer eval merge (15-05) | ✓ VERIFIED | `write_cell_run_record` defined (dispatch_core.py:1211) and called at :1110 AFTER the CR-02 check / terminal-state assignment (:1097-1102), BEFORE `finalize_claim` (:1112) — read in source this pass; producer: `eval_results = trainer.evaluate()` (:1727, outside rank guard), `merged = {**eval_results, **metrics}` (:1748), ordering flops write (1701) < evaluate (1727) < merge (1748) < second final_metrics write (1749) < marker copy (1763), max_mem_gb read (1677) < evaluate (D-05); add_argument count 27; named tests **re-run this pass**: eval-merge ordering pin, shape parity, WR-12 no-overwrite refusal, stale-failed replacement, export dry-run visibility, WR-02 eval-failure delete — ALL PASS |

**Score:** 7/7 truths verified (0 present, behavior-unverified)

Truth 6 in 15-01's must_haves ("EDGE FLAG … flagged as an assumption for human review") is a meta-statement about coverage scope — verified as stated (all D15-02 pass criteria it names are green, and no deterministic edge category was triggered); the flag itself is carried as a review recommendation, not a gap.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `docs/multi-gpu.md` | executed dispatch-mode N=2 procedure + revised D-05 section | ✓ VERIFIED | All identity strings present, retired phrase 0, scope guard held (phase diff confined to the sanctioned regions per 15-01-SUMMARY; IN-03 citation refresh 55c8788) |
| `.planning/WINDOWS.md` | rows 21/44/45 fixed with evidence | ✓ VERIFIED | All three `fixed` with detailed resolutions; ledger 8 open / 31 fixed |
| `.planning/PROJECT.md` | D-05 + small-sweep rows done | ✓ VERIFIED | Both `✓ Landed` with evidence-bearing resolutions |
| `script/make_subset_datasets.py` | deterministic stratified generator (min 200 lines) | ✓ VERIFIED | 631 lines, stdlib-only, wired (produced the on-disk subset trees) |
| `tests/test_subset_datasets.py` | 9-behavior pin suite + D15-15 real-artifact checks (min 180 lines) | ✓ VERIFIED | 716 lines; 29 tests pass on this box (real-artifact checks RAN, not skipped); skipif only guards artifact absence for zero-GPU CI |
| `tests/fixtures/subset_fixture/{train,dev,test}.csv` | committed 3-class fixture | ✓ VERIFIED | Present, used by the multiclass stratification pin |
| `pipeline/dispatch_core.py` | finalize-time run_record writer | ✓ VERIFIED | Writer present + wired at the pinned insertion point; behavior pinned by named tests (run this pass) |
| `pipeline/run_finetune.py` | evaluate capture + additive merge + reordered writes | ✓ VERIFIED | All statements present at pinned order; argv byte-stable (27 add_argument) |
| `artifacts/models_comparison{,_animal,_microbe}.json` + 2 `{model}_performance.json` | archived consumption proof | ✓ VERIFIED | 5 files, non-empty, content-consistent with the real sweep f1s |
| `.gitignore` / `Makefile` | smoke/sweep root entries + lint slot | ✓ VERIFIED | `finetuned-smoke*/`, `pipeline/datasets-smoke/`, `pipeline/registry-smoke/`, `pipeline/finetuned-sweep/`, `pipeline/finetuned-sweep-r2/`; generator in lint list |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| Executed dispatch command | `dispatch_state.json` terminal state | `run_sweep_shard --mode dispatch` single-writer state | ✓ WIRED | Two real runs (2-cell, 12-cell) both terminal `done` with matching workers/counts; tee logs corroborate |
| Smoke/sweep roots | `export_runs.py` consumption | per-cell `run_record.json` walk | ✓ WIRED | **Re-executed**: 2 records/1 model/1 task and 12 records/2 models/2 tasks, both exit 0 |
| `run_finetune.py` evaluate capture | `run_record.metrics` → export → summarize f1 | verbatim `eval_*` key identity | ✓ WIRED | eval_f1 flows: final_metrics (12/12 numeric) → run_record (spot-verified) → archived performance.f1 → arena avg_raw (exact-value cross-check) |
| `dispatch_core._spawn_worker` | per-cell `run_record.json` | `write_cell_run_record` before `finalize_claim` | ✓ WIRED | Source-read at :1110-1112; parity/refusal/replacement tests PASS |
| Subset registry (`--registry-dir`) | subset CSVs (`--dataset_root`) | two-layer registry seam, official `Dataset_path` verbatim | ✓ WIRED | Registry paths verbatim; 12/12 ledger claims lane-pinned to the subset root; children trained subset-scale (max_steps 27/150) |
| Generator | official/custom registries | MUST NOT write (isolation) | ✓ WIRED (negative) | Porcelain clean + sha256 autouse pins + path refusals |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `artifacts/models_comparison_animal.json` | `avg_raw` | real 5mC eval_f1 from GPU sweep → export → summarize | Yes — equals archived performance f1 to full float precision | ✓ FLOWING |
| `artifacts/models_comparison_microbe.json` | `avg_raw` | real emp_H3 eval_f1 | Yes — exact match | ✓ FLOWING |
| `artifacts/{model}_performance.json` | `performance.f1` | run_record.metrics ← final_metrics.json | Yes — 4 real numeric f1s (0.5952/0.6906/0.5861/0.6732) | ✓ FLOWING |
| `pipeline/finetuned-sweep-r2/*` cell artifacts | metrics/flops/trainer_state | real GPU training (2× RTX 5090) | Yes — subset-scale steps, real flops reports | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| D15-02 criterion 3 (smoke consumption) | `export_runs.py --dry-run --input-root pipeline/finetuned-smoke-r2` | `[Dry-run] 2 run record(s) across 1 model(s) / 1 task(s)`, exit 0 | ✓ PASS |
| Sweep-root consumption | `export_runs.py --dry-run --input-root pipeline/finetuned-sweep-r2` | `[Dry-run] 12 run record(s) across 2 model(s) / 2 task(s)`, exit 0 | ✓ PASS |
| Subset suite incl. D15-15 real-artifact checks | `pytest tests/test_subset_datasets.py -q` | 29 passed in 1.11s (0 skipped) | ✓ PASS |
| Producer eval-merge ordering invariant (WINDOWS #45 fix) | `pytest tests/test_run_finetune_contracts.py::test_eval_results_merged_additively_into_final_metrics` | 1 passed | ✓ PASS |
| Record-writer shape parity (A3 supersession) | `pytest tests/test_dispatch_core.py::test_dispatch_writes_run_record_with_run_sweep_shape_parity` | 1 passed | ✓ PASS |
| WR-12 no-overwrite + failed-record replacement | `pytest …::test_dispatch_refuses_to_overwrite_completed_record …::test_dispatch_replaces_stale_failed_record` | 3 passed | ✓ PASS |
| Export dry-run consumer visibility (no phantom models) | `pytest …::test_dispatch_root_export_dry_run_visibility` | 1 passed | ✓ PASS |
| WR-02 evaluate-failure cleanup | `pytest …::test_dispatch_eval_failure_deletes_metrics_claim_failed_requeue` | 1 passed | ✓ PASS |

### Probe Execution

Not applicable — no `scripts/*/tests/probe-*.sh` declared by the plans; the phase's runnable checks are the pytest/CLI lanes above.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| VAL-01 | 15-01 (+15-04) | N=2 smoke executes on local 2×5090; WINDOWS #21 closed; D-05 revised | ✓ SATISFIED | Truths 1-2; REQUIREMENTS.md traceability row Complete with criterion evidence |
| VAL-02 | 15-02 | 5% subsets pre-materialized, deterministic stratified, dedicated registry, separate roots | ✓ SATISFIED | Truths 3-4; registry + provenance verified on disk |
| VAL-03 | 15-03 (+15-05) | Small real sweep on both GPUs through dispatch → data-chain consumption end-to-end | ✓ SATISFIED | Truths 5-7; five archived JSONs with content-level consistency |

Orphaned requirements: none — every Phase-15-mapped ID (VAL-01/02/03) is claimed by plans and verified. DOCS-01/DOCS-02 belong to Phase 18.

### Decision Coverage

`gsd-tools check.decision-coverage-verify`: **16/16 honored, 0 not honored** — "All trackable CONTEXT.md decisions are honored by shipped artifacts" (D15-01 … D15-16 each traceable to verified artifacts above).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none — debt-marker scan clean: 0 TBD/FIXME/XXX/TODO/HACK across all seven phase-modified code/doc files) | - | - | - | - |
| `.planning/phases/15-dual-gpu-validation-subsets/15-REVIEW-DISPOSITION.md` | - | 5 open info findings (IN-01/03/04/05 carried, IN-06 new hardening note) | ℹ️ Info | Tracked review debt, explicitly not goal failures; code-review loop closed 0 Critical / 0 Warning (4 fixes CR-01/WR-01/WR-02/WR-03 all verified present in source this pass) |
| `tests/test_export_runs.py` D-15 lane | - | pre-existing HF-endpoint hang on this box | ℹ️ Info | Environment (documented in deferred-items.md; HF_ENDPOINT workaround recorded); untouched by this phase |

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| ----------- | ---------- | ------ | ------- | -------- | --------------- | ------- |
| tests/test_subset_datasets.py | VAL-02/03 | 29 | 0 ran here (skipif guards CI-only absence) | No — fixtures hand-fabricated to the research math table (independent oracle); real-artifact checks read actual run outputs | Value (exact counts/classes/bytes) | OK |
| tests/test_dispatch_core.py (run_record contract set) | VAL-01/03 | re-ran 5 named | - | No — fake children + real run_sweep.run_matrix comparison oracle | Behavioral (field-by-field parity, exit codes, refusal semantics) | OK |
| tests/test_run_finetune_contracts.py | VAL-03 | re-ran 1 named | - | No — static-source ordering pins against the ruled invariant | Value (index ordering, literal merge expression) | OK |

Disabled tests on requirements: 0. Circular patterns: 0. Expected-value provenance for the archived JSONs: VALID (products of the real GPU sweep through the unmodified chain — cross-validated at exact-float level this pass).

### Human Verification Required

None as test items. This is a validation/infrastructure phase; the real-GPU behavior that constitutes the goal was verified directly against on-disk run artifacts and re-executed consumption seams.

**Flagged for human review (non-authoritative, ADR-550 autonomous mode — consistent with Phases 13/14):** the 17 judgment-tier `must_haves.prohibitions` across the five plans were auto-judged HELD with cited evidence (see `unverified_prohibition_flags` frontmatter). These verdicts are LLM-judge assessments, not human attestations; a maintainer spot-review of the frozen-surface claims (esp. 15-05's "no chain changes" and 15-04's "engine byte-compatibility beyond the record write") is recommended at the end-of-phase checkpoint. The 15-01 EDGE FLAG assumption (edge behavior covered only by the D15-02 pass criteria) is carried as the plan requested — all named criteria verified green.

### Gaps Summary

No gaps. All four ROADMAP success criteria verified against real runtime evidence: the N=2 smoke's terminal state and both-GPU artifact production re-read from disk; the consumption seams re-executed (exact expected output, exit 0); the 12-cell sweep's per-cell artifacts, eval keys, subset-scale step counts, and ledger lanes re-checked individually; the archived chain outputs cross-validated at exact-float level; the two gap-closure code changes (dispatch run_record writer, producer eval merge) confirmed wired at their pinned insertion/ordering points with named behavioral tests passing. The two mid-phase halts (WINDOWS #44/#45) followed the D15-04 stop discipline and were resolved through maintainer-ruled gap-closure plans — the ruled process, executed as designed. Working tree is clean over all frozen surfaces (pipeline/, script/, dnallm-mark/data/, ci.yml hash-pinned).

---

_Verified: 2026-10-21T01:43:41Z_
_Verifier: Claude (gsd-verifier)_
