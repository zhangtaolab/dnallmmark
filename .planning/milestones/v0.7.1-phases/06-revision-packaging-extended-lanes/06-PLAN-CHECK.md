# Phase 06 Plan Check — 2026-10-11

Checker: goal-backward pre-execution verification. Inputs: ROADMAP Phase 6 (goal, SC-1..SC-7, 9 requirement IDs), 06-CONTEXT.md (binding decisions), 06-RESEARCH.md, 06-PATTERNS.md, 06-01..06-05-PLAN.md, plus live code facts (DNALLM v1.2.1 pyproject, run_finetune.py flag surface, env_smoke.py, js/data.js).

## Coverage (SC → plan/task)

| SC | Discharged by | Status |
|----|----------------|--------|
| SC-1 fresh-clone reproduction | 06-04 T3 (README literal section + CI-replay tie) | Covered |
| SC-2 provenance rows + manifest | 06-04 T2 (+T4 review gate) | Covered |
| SC-3 snapshot | 06-04 T2 (make snapshot, manifest-derived hash, .sha256 committed / .tar ignored) | Covered |
| SC-4 methodology + dead logic | 06-04 T1 (removal first commit) + T3 (METHODOLOGY.md) | Covered |
| SC-5 onboarding | 06-04 T3 (docs/ONBOARDING.md, dry-run-validatable) | Covered |
| SC-6 lanes | 06-01 (tracer+gate), 06-02 (LoRA/IA³+frontier), 06-03 (VEP), 06-05 (probes+curves) — mechanisms + tests per CONTEXT Area 1; runs correctly deferred | Covered |
| SC-7 DOI swap | 06-04 T3 doi_swap.py prepared-not-executed; CONTEXT Area 4 explicitly assigns execution to the maintainer (record 19135551 is 404) | Covered (no deferred-action-claimed-complete: the plan's must_have states "prepared, not executed" and backstop-verifies the preview link still present) |

Requirements: REL-03, DATA-04, DATA-05, DATA-07, EXT-01, EXT-02, REV-03 → 06-04; REV-05 → 06-01/02/05; REV-08 → 06-01/03/05. All 9 frontmatter-declared. No requirement left unclaimed.

## Contradiction checks (performed, not credited)

- **File disjointness 06-02/03/04**: verified from frontmatter `files_modified` — the three sets share zero files (02: run_finetune/run_sweep/sweep+contract tests/frontier set; 03: vep driver/schema/tests/fixtures; 04: js+registry+provenance+snapshot+docs+Makefile). Shared files (run_finetune, run_sweep, both test files) occur only between 06-02 and 06-05, which is exactly why 06-05 sits in wave 3 with depends_on 06-02. Disjointness claim holds.
- **Standing constraints**: ruff+ty gated in every plan (direct invocation in wave-2 plans — see risk c); CI GPU-free preserved (lazy-import seam + AST contract test in 06-03; no smoke enters make test/CI anywhere); DNALLM read-only enforced by tag-archive install (no editable install — egg-info rationale correct), porcelain asserts in 06-01 T3 and 06-03 T3; no tags, no data_version bump, drift-proxy verifies present in 01/02/03/05; E2' gating respected (all lane data artifacts publication-gated with absence asserts).
- **Deferred ideas**: no plan implements lane RUNS, E2', data-v2 tag, the reviewer-response report, or first CI execution. The bounded smokes are explicitly sanctioned bounded plan tasks (06-01 amends the env_smoke sanction docstring to record exactly this boundary), not the deferred lane runs.

## Risk-item dispositions

**a. Smoke heaviness — ACCEPT.** 06-01 T3 (install + env_smoke + 2 dry-runs), 06-02 T1 (1-epoch LoRA), 06-03 T3 (2-model VEP), 06-05 T1 (1-epoch probe) are all bounded: named 100M backbones only, smallest-local-task pickers, verbatim-output SUMMARY evidence, explicit "never in make test/CI" prohibitions, honest-FAIL provisions (06-03 T3(d): a real model failing the sanity bar is recorded, not tuned away — correct). One caveat: the real 1-epoch trainings in 06-02/06-05 go beyond dry-run; the 06-01-amended sanction text ("bounded plan TASKS on this GB10 host") covers them, and the executor should confirm the amended docstring wording is broad enough when landing 06-01. Note only.

**b. 06-04 size — ACCEPT with note.** 4 tasks / 21 files / 75k tokens is the heaviest plan and over the usual file target. The natural cut exists (T2 provenance+snapshot vs T3 docs+doi, zero shared files except the Makefile lint-list line) but is not required: T1 is tiny, T4 is a checkpoint, confidence is high, and splitting would put the lint-list consolidation and the docs in different plans without reducing risk. If execution context pressure appears, split at the T2/T3 boundary.

**c. Makefile lint-list consolidation — MOSTLY HOLDS, one gap.** Verified each wave-2 plan gates ruff by direct invocation: 06-02 T3 (`uv run --group dev ruff check script/build_frontier.py && ty check`), 06-03 T1 (`ruff check script/zero_shot_vep.py && ty check`). So every gate holds even if 06-04 has not run. Gap: 06-04 runs in wave 2 in PARALLEL with 06-02/06-03, and its existence-guarded lint-list addition (`only if the file exists on disk at execution time`) can therefore permanently omit `script/build_frontier.py` and/or `script/zero_shot_vep.py` — nothing later re-adds them, so `make lint` would silently not cover those scripts. WARNING below.

**d. SCHEMA_FILES deferral — CONSISTENT.** 06-02 and 06-03 each commit the schema FILE + generator-produced fixtures and validate them inside their own test modules; only the tests/test_schemas.py SCHEMA_FILES bucket (which validates committed dnallm-mark/data artifacts) waits for the first real data file. The one-commit schema+data discipline is preserved where data exists (06-04 provenance registers its bucket with its artifact in one commit). No violation.

**e. pyarrow relabel — VERIFIED CORRECT.** Read /home/forrest/Github/DNALLM/pyproject.toml @ 1.2.1: `datasets<=3.2.0` is present, `numpy>=2.0.0` floor present, and there is NO direct pyarrow pin in [project].dependencies — the `pyarrow>=15,<26` attribution in env_smoke.py (lines 33-41, 135, 195) is a 0.8.0-era claim. 06-01 T1 explicitly instructs: "re-verify the pyarrow claim against the v1.2.1 pins and drop or correct it if the row changed" — the plan anticipates exactly this outcome. Accept.

**f. VEP honest-FAIL provision — ACCEPT.** 06-03 T3(d) records a real-model sanity failure as an honest finding without cohort tuning or schema weakening; the stub flip test proves the sanity logic is real. Compliant.

## Checkpoint correctness

06-04 Task 4 is `checkpoint:human-verify` with a blocking gate, an explicit resume-signal ("reviewed" or CSV corrections), and a defined post-review re-ingest/commit path — matches the CONTEXT Area 2 binding decision. The "review unavailable → Unspecified-default stands, surfaced at phase verification" escape is honest (Unspecified is publication-safe) but means the checkpoint can effectively self-resolve; acceptable given the escape is disclosed, not silent. Plan is `autonomous: false` — consistent.

## Issues

### BLOCKER

**1. [executability] Every evidence-producing verify command must be runnable as written**
- Plans: 06-02 (Task 1), 06-05 (Task 1)
- Evidence: both smoke verify commands invoke `run_finetune.py --num_train_epochs 1`, but run_finetune.py's argparse surface (verified live: flags are --target_model, --target_dataset, --batch_size, --max_token_len, --remove_pt, --remove_checkpoints, --category, --task_index, --auto_batch_size, --gradient_checkpointing, --ddp_find_unused_parameters, --cache_dir, --seed, --gpu_memory, --mem_ratio, --effective_batch_size, --output_dir, --save_model_name, --subset_file) has NO --num_train_epochs flag; epochs come from the YAML (num_train_epochs: 3). Both bounded smokes would fail at argument parsing before any training — the alias/persistence/probe-freeze evidence could not be produced as written. Neither plan's action adds the flag.
- Example fix (non-binding): have each plan's task add a `--num_train_epochs` CLI override (mirroring the existing flag shape) in the same task, or run the 1-epoch smoke through a variant config / explicitly-passed config mechanism that the plan already defines.

### WARNING

**2. [dependency_correctness] The existence-guarded lint-list can permanently omit parallel-wave scripts**
- Plan: 06-04 (Task 2, Commit D)
- Evidence: 06-04 adds script/build_frontier.py and script/zero_shot_vep.py to the Makefile lint list "only if the file exists on disk at execution time", but 06-04 executes in wave 2 alongside 06-02/06-03, which create those files. If 06-04 runs first, the guard excludes them and no later task re-adds them — `make lint` silently loses coverage of two new scripts.
- Example fix (non-binding): schedule the lint-list consolidation after wave 2 (small follow-up in 06-05 or a phase-verify step), or have 06-02/06-03's final tasks assert their script appears in `make lint` scope once 06-04 lands.

**3. [scope_sanity] 06-04 is the heaviest plan (4 tasks, 21 files, 75k tokens)**
- Plan: 06-04
- Evidence: file count well above the 5-8 target; docs + provenance + snapshot + dead-code + doi_swap in one plan.
- Example fix (non-binding): optional split at the T2/T3 boundary (provenance+snapshot vs docs+doi_swap); acceptable as-is given high confidence and the tiny T1/checkpoint T4.

### INFO

**4. [task_completeness]** 06-02 T1's smoke verify pipes `tail -5` and then separately `find`s the metrics file — the pass/fail coupling between the training run and the file assertion is loose (a failed run leaves a stale dir absent, so it still fails correctly; fine, just noisy). No action required.

**5. [dependency_correctness]** 06-01 T1 verify greps `grep -c "0\.8\.0" pipeline/env_smoke.py` expecting zero; the current file legitimately contains the string inside the claims being relabeled, so the check is correct post-edit but would fail pre-edit — intended. No action.

## Verdicts per plan

| Plan | Verdict |
|------|---------|
| 06-01 | PASS — gating plan, real execution evidence, read-only boundary enforced, pyarrow relabel correctly anticipated |
| 06-02 | PASS-with-notes — BLOCKER 1 (smoke flag) must be fixed; otherwise full REV-05 LoRA/IA³+frontier mechanism with publication gate |
| 06-03 | PASS — 62-row totality, lazy-import CI boundary, stub-seam CPU proof, honest-FAIL smoke, schema+fixtures committed |
| 06-04 | PASS-with-notes — WARNING 2 (lint-list race) and 3 (size); SC-1..SC-5, SC-7 discharged; checkpoint correct |
| 06-05 | PASS-with-notes — BLOCKER 1 (smoke flag) must be fixed; nesting invariant and scope guard well designed |

## Overall

**ISSUES FOUND — 1 blocker, 2 warnings, 2 info.** The plan set is goal-complete (all 7 SCs and all 9 requirements discharged with evidence-producing verifies, no scope reduction of any CONTEXT decision, no deferred idea implemented). Fix blocker 1 (the two `--num_train_epochs` smoke invocations) before executing 06-02/06-05; address warning 2 (lint-list wave race) before or during wave 2. 06-01 and 06-03 are executable as written.
