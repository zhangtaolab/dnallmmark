---
phase: 05-ci-e2-rerun
reviewed: 2026-10-10T00:00:00Z
depth: deep
files_reviewed: 37
files_reviewed_list:
  - script/summarize_comparison.py
  - script/permutation_tests.py
  - script/audit_n_frequencies.py
  - script/run_migration_inventory.py
  - script/export_runs.py
  - pipeline/run_sweep.py
  - pipeline/run_finetune.py
  - pipeline/env_smoke.py
  - pipeline/sweep_priorities.json
  - schemas/models_comparison.json
  - schemas/permutation_tests.json
  - schemas/data_manifest.json
  - schemas/n_audit.json
  - dnallm-mark/js/main.js
  - dnallm-mark/js/config.js
  - dnallm-mark/js/data.js
  - dnallm-mark/js/task.js
  - .github/workflows/ci.yml
  - eslint.config.mjs
  - .htmlvalidate.json
  - Makefile
  - CHANGELOG.md
  - DATA.md
  - README.md
  - .gitignore
  - pyproject.toml
  - tests/test_aggregation.py
  - tests/test_permutation.py
  - tests/test_sweep.py
  - tests/test_audit_n.py
  - tests/test_run_finetune_contracts.py
  - tests/test_migration_inventory.py
  - tests/test_ci_replay.py
  - tests/test_export_runs.py
  - tests/test_schemas.py
  - tests/test_known_defects.py
  - tests/js/main-view-toggle.test.js
findings:
  critical: 0
  warning: 3
  info: 4
  total: 7
status: issues_found
---

# Phase 05: Code Review Report

**Reviewed:** 2026-10-10 (commits 5d084c9..HEAD, 20 execution commits across plans 05-01..05-04)
**Depth:** deep (per-file + cross-file: scipy-suite ground-truth reads, DNALLM suite seam verification, independent drift/inventory rerun, artifact-level statistical assertions, gate reruns)
**Files Reviewed:** 37 production files (+ the committed artifacts they emit, inspected as evidence)
**Status:** issues_found — 0 critical, 3 warnings, 4 info

## Summary

Phase 05 holds up under adversarial review. The two highest-risk surfaces — the
F6 statistics (tie rule, weighted score, permutation family) and the two data
migrations (3c40de3 single-commit F6 migration, dfb9a80 D-18 alias rename) — were
verified independently, not just read:

- **Permutation semantics (the flagged interpretation question): resolved as
  ACCEPTED, not a defect.** scipy 1.18.1's own documentation (read from the
  pinned install) confirms `permutation_type='samples'` IS the paired-sample
  permutation type ("observations are assigned to different samples but remain
  paired with the same observations from other samples ... appropriate for
  paired sample hypothesis tests such as ... the paired t-test") — exactly what
  `script/permutation_tests.py`'s docstring claims. The three binding plan
  statements literally mandate the parameter; the paired null (per-task
  difference sign-flip, task as blocking factor over per-task-normalized
  zscores) is the statistically appropriate test for "is model A systematically
  better than B across tasks"; and the tests' exact hand-computed values
  (p = 2/8 = 0.25 at the 2^3 exact floor; BH 0.375/0.375/1.0) are the correct
  paired-test values — independently recomputed by this review. The committed
  artifact verifies: 861 = C(42,2) sorted-unique pairs, 657 significant, all
  `p_adj >= p_value` (BH monotone), 0 excluded. The actionable residue is
  WR-01 (medium): the artifact's own `info` block does not carry the paired
  disclosure — see below.
- **Migration integrity verified from artifacts, not prose:** an independent
  scratch regeneration at HEAD (`run_migration_inventory.py` into /tmp)
  reports **0 changed / 0 new / 7 identical / 0 diffs** — the drift-green
  claim is true at HEAD. D-18's attribution logic is sound: the ULP-scale
  `sum_zscore`/`weighted_score` movement is the real, explainable consequence
  of the renamed file sorting at a different `os.listdir` position (different
  float summation order in per-task mean/std), and ranks/rank_score/Top-K are
  order-invariant — "scores untouched" is accurate. The tier-2 curation basis
  was re-derived from the committed data: animal leader 0.799
  (GENERanno-eukaryote-0.5b-base), plant leader excluding the tier-1 pair 1.000
  (PlantCAD2-Small-l24-d0768), microbe excluding tier-1 1.056 (Omni-DNA-700M)
  — the maintainer's stated basis matches the committed numbers exactly.
- **Sweep driver:** tier-rank composition `(tier_idx, entry specificity)` over
  the `sorted()` fallback is correct (fallback rank `(len(tiers), 0)` strictly
  outranks every tier rank), stability preserves seed adjacency, and the
  degradation-order fake-executor test genuinely proves the full tier-1 →
  tier-2 → fallback order through `run_matrix`. `--from-failures` exact-pair
  re-enumeration and the clean-manifest explicit zero-cell run behave as
  claimed.
- **--subset_file:** `validate_subset_file` is a real collect-all-problems
  validator (bool-as-non-int correctly rejected before the int check; `[0, Test)`
  range); the select seam sits between `load_local_data` and
  `validate_sequences` exactly as claimed, and the seam is the suite's own
  mutation idiom (verified against the read-only DNALLM checkout: the suite's
  `sampling()` does `dataset[dt] = dataset[dt].select(...)` on the same
  DatasetDict, and `check_sequence` at the pinned revision matches the audit's
  `_survives` mirroring verbatim — length window and `set(seq.upper())`
  membership). Absent flag = no-op path. `pipeline/eval_subsets.json` verified:
  43 tasks, 582,927 IDs, every ID in range and sorted, zero problems.
- **Audit script:** parse-only under untrusted-data discipline (no eval/exec,
  per-row `[Skip]` with the row index consumed so ID space stays file-aligned,
  csv.Error/UnicodeDecodeError/OSError each downgrade a split to a WARNING,
  never a crash).
- **env_smoke.py:** pins parsed from pyproject (never duplicated), PASS/FAIL +
  exit-1 contract, 50-dir check names missing dirs with the double-nesting
  note; grep confirms nothing in the repo imports or executes it (only the
  Makefile lint scope names it). The BLE001 noqa sites (three, at :207/:232/:380
  — the 05-04 SUMMARY said "two"; count drift only) are each justified by the
  gate's FAIL-not-traceback contract; no suppression widening elsewhere.
- **Frontend:** weighted default, view-derived sort/scatter/column/footer all
  read `performance.weighted_score` — zero client-side aggregation math found;
  `loadDataManifest` failure hides the stamp (null-guard verified in code and
  pinned by node tests); no `toLocaleDateString` remains.
- **CI:** all three actions full-40-char-SHA-pinned with version comments;
  `timeout-minutes: 14` on 4/4 jobs; `permissions: contents: read`; no
  `pull_request_target`; all six HTML shells referenced by html-validate exist
  on disk (including `submit.html`); 3.13-required + 3.14-probe matrix matches
  the documented deviation.
- **Cross-cutting:** no committed run artifacts outside `tests/fixtures/`
  (`git ls-files` over finetuned/final_metrics/trainer_state/run_record/
  sweep_manifest/sweep_failures: only fixture paths); no pipeline execution
  anywhere in the phase; the DNALLM sibling repo's tracked files are unmodified
  (only pre-existing untracked `.planning/` dirs, absent from this phase's
  commits); `make lint` scope files and the pinned eslint invocation re-run
  green at HEAD; the six phase-05 test modules re-run green (190 passed).

The 3 warnings are disclosure/robustness gaps, not incorrect shipped numbers:
every number on the leaderboard today regenerates byte-identically.

## Warnings

### WR-01: Published permutation artifact does not disclose the paired-test semantics (severity: medium)

**File:** `script/permutation_tests.py:192` (emitted into `dnallm-mark/data/permutation_tests.json` `info.axis`)
**Issue:** The artifact's self-contained methodology block records `axis: "per-task zscore, aggregate view (score-vector permutation across tasks)"` — but the computed test is the **paired** permutation test (scipy `permutation_type='samples'`: per-task difference signs flipped under the null; verified against the pinned scipy 1.18.1 documentation). "Score-vector permutation across tasks" reads closest to a between-task shuffle of score vectors — i.e. an independent-samples null, which is a different test with different p-values. The info block carries seed/n_resamples/batch/FDR but not the test type, so a reviewer reproducing from the artifact alone cannot reconstruct the computation. The paired semantics ARE correctly disclosed in `CHANGELOG.md:60` ("paired permutation test (`permutation_type='samples'`)") and in the module docstring — this finding is strictly about the machine-readable, site-downloadable evidence artifact.
**Failure scenario:** An external reviewer downloads `permutation_tests.json`, replicates the pipeline from the disclosed fields under the independent-sample assumption, obtains different p-values (they would — the nulls differ), and files a reproducibility/methodology complaint against the benchmark — precisely the trust failure this milestone exists to prevent.
**Fix:** Reword the `axis` constant in `build_artifact` (schema-compatible — `axis` is a free string, `additionalProperties: false` only forbids *new* keys) to name the semantics, e.g. `"per-task zscore, aggregate view; paired permutation test (scipy permutation_type='samples') — per-task difference signs flipped under the null"`, then regenerate the artifact in a small documented commit (it is a drift-gated derived file). Do not add a `permutation_type` info key without extending `schemas/permutation_tests.json` in the same commit.

### WR-02: --priority-file/--from-failures accept non-trainable task names — inconsistent with the _validate_filters discipline (severity: low, latent)

**File:** `pipeline/run_sweep.py:451` (`load_priority_tiers`), `pipeline/run_sweep.py:555` (`load_failure_pairs`), vs `pipeline/run_sweep.py:319-331` (`_validate_filters`)
**Issue:** `_validate_filters` deliberately refuses `--tasks` names whose registry row has falsy `Train` ("the matrix can never run them, so enumerating them away silently is also a no-op"). Both operator-JSON validators instead join against the FULL registry key sets (`_load_registry_key_sets` returns `set(datasets_info)`), so a priority entry naming a Train-falsy task passes validation and is then silently inert — its cells never enumerate, and the maintainer believes a cell is prioritized that will never run.
**Failure scenario:** A future registry revision adds an eval-only task; a tier-2 curation names it; validation passes; launch-day degradation order silently omits it with no error and no warning.
**Current exposure:** zero — all 50 registry tasks are Train-truthy today (verified), so this is latent. CONFIRMED inconsistency, latent-only impact.
**Fix:** In both validators, either build the known-task set from truthy-Train rows only, or append a problem (`"task has no train split (Train is falsy): ..."`) when an entry names such a task — one small change each, mirroring `_validate_filters`.

### WR-03: --subset_file joins two different key spaces (registry key vs Dataset_name) (severity: low, latent)

**File:** `pipeline/run_finetune.py:234-236` (validates against `datasets_info` keys) vs `pipeline/run_finetune.py:281-287` (`apply_eval_subset` joins on `dataset_name`) and `pipeline/run_finetune.py:623` (`dataset_name = row["Dataset_name"]`)
**Issue:** The validator accepts subset keys that are registry KEYS; the apply seam looks them up by `Dataset_name`. These coincide for all 50 rows today (verified: zero mismatches), but they are independent fields — if any future registry row sets `Dataset_name != key`, that task's subset silently no-ops: the model evaluates the FULL test split while the operator believes the unified-N fairness subset is applied. The failure is silent in exactly the direction the flag exists to guard (identical cross-model sample counts), and the sweep would complete "successfully" with incomparable numbers.
**Failure scenario:** Registry edit introduces `Dataset_name` divergence on one task; E2' runs consume `eval_subsets.json`; the affected task's strict-charset/tolerant divergence reappears unnoticed; published per-task sample counts differ across models on that task.
**Fix:** Join on the registry key at the seam (pass the loop's `idx`/key into `apply_eval_subset`), or add a one-time fail-fast assertion in `validate_subset_file` that `datasets_info[task]["Dataset_name"] == task` for every subset key — the same fail-loudly discipline as the rest of the flag.

## Info

### IN-01: Tie-rule boundary semantics under mixed interval presence — verified per-plan, recorded for the E2' wiring review

**File:** `script/summarize_comparison.py:239-264`
**Issue:** Not a defect: with intervals present for models A (rank 1) and C (rank 3) but absent for B (rank 2, score between them), an A~C overlap gives A and C the component-min rank 1 while B keeps rank 2 — the worst-scoring model C then earns MORE `task_rank_score` than the better-scoring B. This exactly matches the plan's binding behavior ("models without interval entry keep pure score ranking") and is pinned by `test_ci_map_none_and_missing_entries_reproduce_exact_tie_output`. It can only arise mid-migration (E2' gives every model a 3-seed interval). Recorded here so the E2' ci_map wiring review treats it as intentional, not emergent.
**Fix:** None required; optionally a one-line comment at the `component_min` loop noting the mixed-map boundary case.

### IN-02: Audit ID space assumes HF row order equals CSV file order

**File:** `script/audit_n_frequencies.py:49-50`, `:213-235`
**Issue:** Emitted subset IDs are CSV data-row indices; the consumer applies them via HF `Dataset.select`. The suite loads CSVs through HF `load_dataset`, which preserves order for well-formed CSVs, and the audit correctly consumes an index for malformed rows (`row_index += 1` precedes the skip), but a row that HF's loader silently drops (e.g. a blank line handled differently by the CSV backends) would shift the index space. No such rows exist in the 43 audited tasks (582,927 IDs validated against registry Test counts).
**Fix (optional belt-and-braces at E2'):** assert `len(dataset.dataset["test"]) == audit rows` before `select` at the seam, failing the cell loudly on any divergence.

### IN-03: CI eslint lane could go vacuously green on a glob/config drift

**File:** `.github/workflows/ci.yml:98`, `eslint.config.mjs:22`
**Issue:** The config's `files: ['dnallm-mark/js/*.js']` matches the CLI glob today, and non-vacuousness was proven by execution-time negative probes (05-01). But a future cwd or pattern drift that makes CLI files match no config object produces ignored-file warnings, not errors — exit 0, lane green, nothing checked. Not a current defect; a hardening gap.
**Fix:** Add `--max-warnings 0` to the pinned eslint invocation so any ignored-file warning fails the lane.

### IN-04: Stale legacy usage line in summarize_comparison.py docstring

**File:** `script/summarize_comparison.py:74-77`
**Issue:** The module docstring still documents the pre-Makefile invocation (`cd dnallm-mark/data && python ../../script/summarize_comparison.py`); the canonical regeneration path since 05-02 is `make data` (which also runs the permutation engine and index generator the old two-step omits). Doc drift only — running the documented two-step alone still works but leaves the derived tree stale relative to the full chain.
**Fix:** Update the usage block to `make data` (repo root), keeping the CWD note for historical context if desired.

---

## Verification Evidence (independent, this review)

1. scipy 1.18.1 `permutation_type` semantics read from the pinned install's own docstring (paired/pairings/independent taxonomy) — the implementation's documented interpretation is factually correct.
2. Hand-recomputed the 3-task exact p-values (2/8 = 0.25 floor; BH step-up → 0.375/0.375/1.0) — match `tests/test_permutation.py`.
3. Scratch migration inventory rerun at HEAD: `0 changed / 0 new / 7 identical — 0 diffs` (drift-green independently confirmed on all 7 derived files).
4. Committed artifact assertions: 861 pairs / 657 significant / sorted-unique / BH-monotone; eval_subsets 43 tasks / 582,927 IDs / zero range or sort problems; `weighted_score` present in all 4 comparison files (42 models each).
5. Tier-2 curation basis re-derived from committed weighted_score arena leaders excluding the tier-1 pair — matches the recorded gate disposition exactly.
6. Suite ground truth (read-only DNALLM checkout): `sampling()`'s `select` mutation idiom and `check_sequence`'s `set(seq.upper())` membership + length window — the audit's filter mirroring and the subset seam are the suite's own semantics, not approximations.
7. Gates rerun at HEAD: pinned `eslint@10.12.0` exit 0; `ruff check` over the seven phase-05 pipeline/script files clean; `pytest` over the six phase-05 test modules: 190 passed.
8. Hygiene: no committed run artifacts outside `tests/fixtures/`; nothing imports/executes `env_smoke.py`; DNALLM tracked tree unmodified.

## Documented deviations NOT re-reported (verified accurate)

- 3.13+3.14 matrix supersession of TEST-04's literal 3.12 text (05-01 #3) — consistent with `requires-python >= 3.13`.
- `permutation_type="samples"` kept per three binding plan statements (05-02 "Documented Interpretations") — endorsed by this review (see Summary); WR-01 covers only the artifact disclosure.
- Inventory executed before tree movement; extraction refactor to `load_model_inputs`; scipy `axis=-1` fix; single-common-task exclusion; D-18 icase glob substitution; shorthand→registry-key task name; ULP/positional-churn attribution; env_smoke numpy gate extension; RED-phase argparse-exit note; stale docstring updates in 6598e45. Each checked against the code — none is factually wrong.

_Reviewed: 2026-10-10_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
