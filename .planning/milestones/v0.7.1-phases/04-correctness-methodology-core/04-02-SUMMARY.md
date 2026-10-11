---
phase: 04-correctness-methodology-core
plan: 02
subsystem: data-chain
tags: [unified-exporter, vendored-statistics, scipy, evaluate, metric-key-mapping, d-12-join, freeze-snapshot, jsonschema]

# Dependency graph
requires:
  - phase: 04-correctness-methodology-core
    provides: maintainer-confirmed datasets_info Category + MAJORITY_ARENA twin in summarize_comparison (04-01); D-15 dependency-unification decision (04-CONTEXT, commit 83d86ba)
provides:
  - Vendored, parity-tested aggregate_seeds @483a35c in script/export_runs.py (character-identical to the suite source, mechanically diff-proven) + its module constants — the reviewer-facing statistics authority
  - The IN-03 single-owner metric-key mapping table (SUITE_CANONICAL 28 names / CANONICAL_TO_EXPORT 11 / UNMAPPED 17 / PIPELINE_KEYS 3), total over the vendored surface and equal to the UNCHANGED task_performance metricBlock set — key-parity tested in both directions
  - The F2 run-record exporter core: reader (sorted walk, failed/skipped contribute nothing, missing-total_flos actionable hard error), D-12 parametersBlock join (vram_probe overrides + YAML base + trainer_state steps), dual output (schema-valid task_performance-compatible files + per-seed statistics artifacts), byte-stable by construction
  - script/freeze_snapshot.py — parameterized tar + SHA256 manifest primitive (data-v1 line convention + commit header), tested, invocation intentionally unwired (Phase 6)
  - D-15 landed: scipy>=1.15.2 + evaluate>=0.4.6 in the [data] group (same dependency commit, uv.lock re-resolved) + the evaluate golden-case cross-check harness (pearsonr/spearmanr vs independently derived expected values)
  - Lint scope grown to script/export_runs.py + script/freeze_snapshot.py (D-08 discipline)
affects: [04-05 mirror deletion (METRIC_KEY_MAP) + task-file species correction, E2' regeneration (the exporter is its designed input path), Phase 6 freeze invocation, D-15 scikit-learn extension decision]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
# Same estimateTokens scale (chars/4 over the realized diff), never a harness token count.
actuals:
  tokens: 85261     # 341,044 diff chars / 4 over base 83d86ba..HEAD — dominated by uv.lock (265,547 chars, evaluate's transitive closure); authored code/test diff alone is 75,497 chars (~18,874 tokens)
  tasks: 3
  commits: 2        # MEASURED: git rev-list --count 83d86ba..HEAD at SUMMARY time
plan_head_before: 83d86baf7bb69e50bf1977505415b2e294c38f96
plan_head_after: 5b111d7de27637d149aeeaedbc9f21b45b0a9e97

# Tech tracking
tech-stack:
  added:
    - "scipy>=1.15.2 ([data] group, D-15 statistics layer — suite-matching floor; vendored aggregate_seeds t-interval)"
    - "evaluate>=0.4.6 ([data] group, D-15 metrics layer — HF evaluate cross-validation; pyyaml arrives transitively via huggingface-hub)"
  patterns:
    - "Vendor-with-provenance verified mechanically: the vendored section is diff-checked character-for-character against git show 483a35c:..., with parity tests recomputing t-values from scipy.stats.t independently"
    - "Total metric-key mapping with explicit UNMAPPED: no silent drops in either direction; unmapped canonicals emit \"\" in metricBlock but stay disclosed in the statistics artifact under their canonical names"
    - "D-12 config-YAML join: parameters sourced at export time (vram_probe overrides when non-null, YAML base otherwise, trainer_state global_step with max_steps>0-only fallback); run_record contract untouched"
    - "Documented skip contract for Trainer bookkeeping keys (train_loss/epoch/eval_runtime/*_per_second) — not leaderboard metrics, skipped by resolve_metric_key returning None"
    - "evaluate as a verification layer, not the number source: suite-side metrics stay authoritative; golden-case cross-check tolerance-asserts against independently derived expected values"

key-files:
  created:
    - script/export_runs.py
    - script/freeze_snapshot.py
    - tests/test_vendored_stats.py
    - tests/test_export_runs.py
    - tests/test_freeze_snapshot.py
  modified:
    - pyproject.toml   # [data] += scipy/evaluate (D-15); [tool.ty] replace-imports-with-any += evaluate.**
    - uv.lock          # re-resolved same dependency commit
    - Makefile         # lint scope += export_runs.py + freeze_snapshot.py
    - tests/conftest.py # import-roots comment names the two new modules

key-decisions:
  - "D-15 operative adaptation: evaluate's accuracy/f1/mcc metric modules import scikit-learn (not installed, outside the sanctioned scipy+evaluate pair) — the golden-case cross-check covers the scipy-backed evaluate modules pearsonr + spearmanr (both suite-mapped slots); extending to count metrics requires a maintainer-approved scikit-learn addition (noted in WINDOWS.md, not built)"
  - "evaluate's pearsonr buffers inputs through its Arrow metric pipeline and perturbs the last digits at a characterized ~3.3e-9 scale (its spearmanr is bit-exact) — cross-check tolerances set to abs=1e-8 (pearson) / 1e-9 (spearman), still orders below any real convention drift (O(1e-2))"
  - "The vendored aggregate_seeds is character-identical to the suite source (mechanically diff-proven at RED, GREEN and final HEAD); one docstring line-wrap transcription drift was caught and fixed by the diff before commit"
  - "steps/vram_probe provenance rule: the FIRST completed seed in sorted order anchors the parametersBlock join (per-cell training params are config-derived and seed-invariant) — documented in load_parameters_block"
  - "PyYAML used transitively (evaluate -> huggingface-hub -> pyyaml 6.0.3) for the D-12 YAML join rather than adding a new direct dependency (the hard constraint sanctions only the scipy+evaluate uv add)"
  - "ty replace-imports-with-any += evaluate.** (sanctioned per continuation hard constraints): evaluate's partial py.typed annotations make ty misread EvaluationModule.compute as an unbound union member; behavior is pinned by the D-15 cross-check test, not types"
  - "TDD under the plan's explicit one-commit task boundary (type: execute, not type: tdd): tests were written first and RED captured (9 AttributeErrors on the absent vendored names; 11 on the absent exporter/freeze surface) before GREEN within each task's single commit — the plan's 'One commit' instruction overrode the reference's test/feat commit split, as pyproject+uv.lock+script+test must land atomically (Pitfall 4)"

patterns-established:
  - "Golden-case cross-validation of metric conventions against a standard implementation (evaluate) with independently derived expected values and drift-scale tolerances"
  - "Dual-output exporter: leaderboard view (schema-validated aggregate means) + reviewer view (per-seed detail + vendored statistics with per-metric n_seeds disclosure)"

requirements-completed: [REV-03]

coverage:
  - id: D1
    description: "D-15 dependency unification: scipy>=1.15.2 + evaluate>=0.4.6 join the [data] group in the same dependency commit (maintainer Option C), uv.lock re-resolved, uv lock --check green"
    verification:
      - kind: command
        ref: "~/.local/bin/uv lock --check (Resolved 88 packages, OK) + dev-env probe import scipy, numpy, evaluate, yaml -> 1.18.1 / 0.4.6 / 6.0.3"
        status: pass
      - kind: command
        ref: "commit 0189d4c carries pyproject.toml + uv.lock together with the vendored copy (same-commit discipline, Pitfall 4)"
        status: pass
    human_judgment: true
    rationale: "Package legitimacy was human-verified before dispatch: the blocking-human scipy gate was resolved by the maintainer as D-15 Option C (recorded in 04-CONTEXT.md, commit 83d86ba). The automated probes prove the install; the legitimacy judgment itself is the completed human decision."
  - id: D2
    description: "Vendored aggregate_seeds @483a35c: verbatim copy + SMALL_N_CI_CHOICES/CI_MIN_SEEDS/BOOTSTRAP_MIN_SEEDS with source annotation; parity proven by 9 tests (n-guards 2/3/9/10, omit policy, t-interval recomputation, bootstrap determinism, n=1, ValueErrors, constants) and a mechanical character-for-character diff against git show 483a35c"
    verification:
      - kind: unit
        ref: "tests/test_vendored_stats.py (9 PASSED)"
        status: pass
      - kind: command
        ref: "verbatim diff of the vendored section vs the suite source at final HEAD — VERBATIM OK"
        status: pass
    human_judgment: false
  - id: D3
    description: "IN-03 single-owner mapping table: SUITE_CANONICAL (28 @483a35c), alias rules mirroring the suite registry one-directionally (incl. historical eval_pearson_r/eval_spearman_r/eval_auroc/eval_auprc), CANONICAL_TO_EXPORT (11), UNMAPPED (17 deliberate), PIPELINE_KEYS (3) — total over the surface, equal to the UNCHANGED schema metricBlock set, parity green both directions"
    verification:
      - kind: unit
        ref: "tests/test_export_runs.py#test_suite_canonical_surface_is_the_28_name_vendored_set, #test_key_parity_suite_to_export_no_silent_drops, #test_key_parity_export_to_suite_every_key_traces, #test_alias_resolution_mirrors_suite_registry_one_directionally"
        status: pass
      - kind: command
        ref: "plan verify: len(SUITE_CANONICAL)==28, AUROC/mae members, set(CANONICAL_TO_EXPORT)|set(UNMAPPED)==SUITE_CANONICAL — MAPPING TOTAL OK"
        status: pass
    human_judgment: false
  - id: D4
    description: "Run-record reader + hard edges: sorted F2-layout walk, failed/skipped records contribute nothing, completed record missing total_flos raises an actionable error naming the record path, unregistered dataset/model raise KeyError (never a fallback join), 1-seed cell emits sd/ci95 None with method none"
    verification:
      - kind: unit
        ref: "tests/test_export_runs.py#test_hard_edges_missing_flops_unregistered_one_seed, #test_one_seed_cell_emits_degenerate_statistics, #test_end_to_end_emission_validates_against_unchanged_schema (failed-sibling exclusion)"
        status: pass
    human_judgment: false
  - id: D5
    description: "D-12 parametersBlock join: batch_size from a non-null vram_probe override (149) and grad_accum from a null probe falling back to YAML; epochs/lr/scheduler/warmup/bf16/fp16 from the YAML; steps from trainer_state.json global_step (max_steps>0-only fallback, else hard error); run_record contract NOT extended"
    verification:
      - kind: unit
        ref: "tests/test_export_runs.py#test_end_to_end_emission_validates_against_unchanged_schema (EXPECTED_PARAMS_A override path + EXPECTED_PARAMS_B fallback path, both pinned)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Dual output: task_performance-compatible files validating against the UNCHANGED schema (jsonschema), species always the majority arena (Multiple never reaches output; parity with summarize_comparison.MAJORITY_ARENA pinned), metric casing verbatim, per-seed statistics artifact with n_seeds/sd/ci95(t)/method per metric (unmapped canonicals disclosed), byte-stable across runs"
    verification:
      - kind: unit
        ref: "tests/test_export_runs.py#test_end_to_end_emission_validates_against_unchanged_schema (jsonschema.validate + species + t-interval block + TPR disclosure), #test_majority_arena_parity_with_summarize_comparison, #test_export_is_byte_stable_across_runs"
        status: pass
    human_judgment: false
  - id: D7
    description: "freeze_snapshot: parameterized function (paths + output dir + commit hash) writing a tar + SHA256 manifest in the data-v1.sha256 line convention with the commit recorded on the header; tested over a fixture tree; invocation intentionally unwired (Phase 6)"
    verification:
      - kind: unit
        ref: "tests/test_freeze_snapshot.py#test_freeze_snapshot_writes_tar_and_manifest (manifest format, hash recomputation, tar round-trip)"
        status: pass
      - kind: command
        ref: "no Makefile target or caller wires freeze_snapshot (grep: only the module, its test, and doc cross-references mention it)"
        status: pass
    human_judgment: false
  - id: D8
    description: "D-15 integration: evaluate golden-case cross-check over suite-mapped metrics — evaluate's pearsonr/spearmanr vs independently derived expected values (covariance/rank formulas written in the test), tolerance-asserted; sklearn-backed evaluate metrics documented as out of the sanctioned dependency set (extension needs maintainer-approved scikit-learn)"
    verification:
      - kind: unit
        ref: "tests/test_export_runs.py#test_d15_evaluate_cross_validates_suite_mapped_metric_conventions (PASSED; tolerances 1e-8/1e-9 with the ~3.3e-9 Arrow-pipeline perturbation characterized in-line)"
        status: pass
    human_judgment: false

# Metrics
duration: 19 min
completed: 2026-10-10
status: complete
---

# Phase 4 Plan 02: Unified Exporter Summary

**Vendored suite statistics (aggregate_seeds @483a35c, character-identical + parity-tested), the IN-03 single-owner metric-key mapping (28-name total surface, both-direction parity), an F2 run-record exporter with the D-12 config join emitting schema-valid task_performance files + per-seed statistics artifacts byte-stably, a tested freeze_snapshot primitive, and the D-15 scipy+evaluate dependency unification with a golden-case cross-validation harness**

## Performance

- **Duration:** 19 min
- **Started:** 2026-10-10T05:02:45Z
- **Completed:** 2026-10-10T05:22:14Z
- **Tasks:** 3/3 (Task 1 gate resolved pre-dispatch)
- **Files:** 9 (5 created, 4 modified)

## Accomplishments

- **D-15 dependency unification landed (Task 1 gate → Task 2 commit):** the scipy blocking-human package-legitimacy gate was resolved by the maintainer as **Option C** (recorded in 04-CONTEXT.md, commit 83d86ba) — `scipy>=1.15.2` (statistics layer) and `evaluate>=0.4.6` (metrics layer) joined the `[data]` group in the SAME dependency commit (0189d4c) with uv.lock re-resolved; `uv lock --check` green; dev-env import probe green (scipy 1.18.1, evaluate 0.4.6, pyyaml 6.0.3 transitively).
- **Vendored statistics frozen:** `script/export_runs.py` carries `aggregate_seeds` + `SMALL_N_CI_CHOICES`/`CI_MIN_SEEDS`/`BOOTSTRAP_MIN_SEEDS` in a clearly-delimited, source-annotated section (@483a35c, copy date 2026-10-10) — mechanically diff-proven character-identical to `git show 483a35c:dnallm/finetune/sweep.py`; 9 parity tests pin the n-guards (2/3/9/10), the omit policy, t-interval values recomputed independently from `scipy.stats.t`, bootstrap seed determinism, the n=1 degenerate block, the ValueError cases, and the constant values. Zero dnallm imports anywhere in `script/` (CONTEXT exporter-Q1 holds).
- **The IN-03 mapping table exists and is total:** `SUITE_CANONICAL` (28 names), the suite-mirroring alias table (one-directional), `CANONICAL_TO_EXPORT` (11), `UNMAPPED` (17 deliberate "" emissions per A6), `PIPELINE_KEYS` (`eval_loss`→loss, `train_runtime`→runtime, `total_flos`→FLOPs). Parity is tested in BOTH directions; the 14-key export surface equals the UNCHANGED schema metricBlock requirement set (test-asserted). Trainer bookkeeping keys are a documented skip contract, not silent drops.
- **The exporter core:** sorted F2-layout reader; failed/skipped records contribute nothing; a completed record missing `total_flos` is an actionable hard error naming the record path; unregistered dataset/model abort with KeyError (no fallback joins); the D-12 parametersBlock join sources batch/grad-accum from vram_probe overrides when non-null else the YAML, the six config values from the YAML, and steps from `trainer_state.json` `global_step` (YAML `max_steps` only when > 0, else hard error); dual output = schema-valid task files (Multiple→majority arena before emission, metric casing verbatim, `/`+`\` filename sanitization) + per-seed statistics artifacts (vendored aggregate per metric, n_seeds disclosed, unmapped canonicals kept under their canonical names); byte-stable by construction (sorted iteration, sort_keys, no clock) and pinned by test.
- **freeze_snapshot:** parameterized `freeze_snapshot(paths, output_dir, commit_hash)` producing a tar + SHA256 manifest in the `baseline/data-v1.sha256` line convention plus the commit-hash header; tested over a fixture tree; invocation intentionally unwired (Phase 6 packaging owns it).
- **D-15 integration:** `tests/test_export_runs.py` carries the golden-case cross-check — evaluate's pearsonr/spearmanr vs independently derived expected values (covariance / rank formulas written in the test), tolerance-asserted (1e-8/1e-9 with the characterized ~3.3e-9 evaluate Arrow-pipeline perturbation documented in-line). sklearn-backed evaluate metrics (accuracy/f1/mcc) cannot load without scikit-learn — outside the sanctioned pair — so coverage is noted for a maintainer decision, not silently widened (WINDOWS.md entry recorded).
- **Gates:** suite 226 passed + 0 xfailed (baseline 206 → +20 new), node lane 5; `make lint` + `make typecheck` zero-diagnostics over the widened scope; zero committed-data changes (`git status --porcelain dnallm-mark/data/ baseline/` empty).

## Task Commits

Each task was committed atomically (TDD test-first discipline exercised inside each single commit — see TDD note below):

1. **Task 1 (checkpoint:human-verify, gate resolved pre-dispatch):** maintainer chose D-15 Option C at the scipy package-legitimacy gate (04-CONTEXT.md, commit 83d86ba); the approved install + lock re-resolve landed in the Task-2 dependency commit per the plan's design. No separate commit.
2. **Task 2: scipy+evaluate data deps + vendored aggregate_seeds + parity tests** — `0189d4c` (feat)
3. **Task 3: exporter core (mapping, reader, D-12 join, dual emitter) + freeze_snapshot + contract tests** — `5b111d7` (feat)

**Plan metadata:** (docs commit follows this SUMMARY)

## Files Created/Modified

- `script/export_runs.py` — module docstring (Purpose/Behavior/Direction of truth/Provenance incl. D-15 dependency provenance + single-writer concurrency note), verbatim vendored section @483a35c, mapping table, `resolve_metric_key`, `load_run_records`, `load_parameters_block` (D-12), registry joins, dual-output emitter (`export_runs_tree`), repo-root-runnable argparse CLI
- `script/freeze_snapshot.py` — `freeze_snapshot` + `_sha256_file` + CLI (unwired)
- `tests/test_vendored_stats.py` — 9 parity tests (RED captured: 9 AttributeErrors on the absent vendored names)
- `tests/test_export_runs.py` — 10 contract tests: mapping parity both directions, alias rules, arena parity with summarize_comparison, end-to-end jsonschema validation, D-12 both paths, hard edges, 1-seed degenerate stats, byte-stability, D-15 evaluate cross-check (RED captured: 11 failures on the absent surface)
- `tests/test_freeze_snapshot.py` — manifest format + hash recomputation + tar round-trip
- `pyproject.toml` — `[data]` += scipy/evaluate (D-15 annotated); `[tool.ty]` replace-imports-with-any += `evaluate.**` (annotated)
- `uv.lock` — re-resolved (evaluate's transitive closure: datasets/pyarrow/huggingface-hub/pyyaml/requests/... 88 packages total)
- `Makefile` — lint scope += export_runs.py + freeze_snapshot.py (header + scope list + comment)
- `tests/conftest.py` — import-roots comment names the two new script modules

## TDD Note

Both `tdd="true"` tasks were executed test-first with captured RED inside the plan's explicit one-commit task boundary (the plan is `type: execute`, not `type: tdd`, and mandates "One commit: pyproject + uv.lock + script + test + Makefile" — the dependency and the vendored copy that needs it must land atomically per Pitfall 4). RED evidence: Task 2 — 9 target tests failed on `AttributeError: module 'export_runs' has no attribute ...` with the module importing cleanly; Task 3 — 11 target tests failed on the absent mapping/emitter/freeze surface. Both went GREEN before their single commits; no refactor commits were needed (the GREEN implementations landed in final form).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking dependency scope] D-15 evaluate cross-check covers pearsonr/spearmanr, not accuracy/f1/auroc**
- **Found during:** Task 3 (evaluate probe)
- **Issue:** The continuation guidance's illustrative list ("accuracy/f1/auroc") is not loadable with the sanctioned dependency set: evaluate's accuracy/f1/matthews_correlation modules import scikit-learn at compute time (`ModuleNotFoundError: No module named 'sklearn'` live), and scikit-learn is outside the sanctioned `uv add --group data "scipy>=1.15.2" "evaluate"` pair — adding it would be a new package-legitimacy question the blocking-human gate exists for.
- **Fix:** The cross-check covers the scipy-backed evaluate modules `pearsonr` and `spearmanr` — both suite canonicals AND mapped export slots (`pearson_r`, `spearman_r`), satisfying D-15's operative semantics (suite-mapped values vs `evaluate.load(...)`, tolerance-asserted) without widening the dependency set. A `roc_auc` evaluate module does not exist canonically. Extension to count metrics is recorded in WINDOWS.md as a maintainer decision.
- **Files modified:** tests/test_export_runs.py (test docstring documents the scope)
- **Verification:** test_d15_evaluate_cross_validates_suite_mapped_metric_conventions PASSED; dependency set unchanged beyond the sanctioned pair.
- **Committed in:** 5b111d7

**2. [Rule 1 - External-tool characterization] evaluate pearsonr tolerance calibrated to its Arrow-pipeline perturbation**
- **Found during:** Task 3 (first D-15 test run)
- **Issue:** evaluate's pearsonr wraps `scipy.stats.pearsonr` but buffers inputs through its Arrow metric pipeline, perturbing the result at a characterized ~3.3e-9 scale (its spearmanr is bit-exact) — the initially drafted 1e-9 tolerance false-failed.
- **Fix:** Tolerances set to abs=1e-8 (pearson) / 1e-9 (spearman) with the perturbation scale and the drift-scale argument (wrong formulas err at O(1e-2)) documented in the test.
- **Files modified:** tests/test_export_runs.py
- **Verification:** D-15 test PASSED deterministically across repeated suite runs.
- **Committed in:** 5b111d7

**3. [Rule 3 - Type-gate allowance applied] ty replace-imports-with-any += evaluate.**
- **Found during:** Task 3 (`make typecheck`)
- **Issue:** evaluate's partial py.typed annotations make ty misread `EvaluationModule.compute` as an unbound union member (missing-argument/not-subscriptable diagnostics on the D-15 test).
- **Fix:** Added `evaluate.**` to `[tool.ty.analysis] replace-imports-with-any` with an explanatory comment — explicitly sanctioned by the continuation hard constraints ("If evaluate/scipy need ty replace-imports-with-any entries, add them per the [tool.ty] config pattern"); evaluate's behavior is pinned by the cross-check test, not by types.
- **Files modified:** pyproject.toml
- **Verification:** make typecheck zero-diagnostics.
- **Committed in:** 5b111d7

---

**Total deviations:** 3 auto-fixed (dependency scope, tolerance calibration, ty allowance)
**Impact on plan:** None on the plan's truths — all acceptance criteria green; the D-15 metrics-layer semantics land with the sanctioned dependency pair and a documented extension path.

## Issues Encountered

None beyond the deviations above. The r2 metric-enum gap and the A2 final_metrics key-presence question remain flagged-assumption territory by design (fixtures pin the input contract; the exporter's actionable hard errors are the designed E2' discovery mechanism).

## User Setup Required

None - no external service configuration required.

## Authentication Gates

None encountered at runtime. The plan's Task 1 blocking-human scipy package-legitimacy gate was resolved by the maintainer BEFORE this continuation dispatch (Option C — D-15 dependency unification, recorded in 04-CONTEXT.md at commit 83d86ba); this executor performed the approved install + lock re-resolve in the Task-2 dependency commit as the plan directed.

## Next Phase Readiness

- Ready for 04-05: `summarize_comparison.py`'s METRIC_KEY_MAP mirror can now be deleted in favor of `export_runs`' table (IN-03 by removal); the exporter's output shape is the schema the pivot-retirement assertions fold into; the 2 committed task-file species corrections (EPI_GM12878, fungi_species_20) remain routed there.
- E2' path: the exporter is the designed input path for real run records; its CLI is repo-root-runnable (`uv run --group data python script/export_runs.py`); fixture-proven only until real records exist (A2 flagged assumption).
- Suite baseline moved: 226 passed + 0 xfailed + node lane 5 (was 215 after Task 2, 206 before this plan).
- Maintainer follow-up recorded: D-15 count-metric coverage (scikit-learn addition) — WINDOWS.md.

## Self-Check: PASSED

- Files verified on disk: script/export_runs.py, script/freeze_snapshot.py, tests/test_vendored_stats.py, tests/test_export_runs.py, tests/test_freeze_snapshot.py — all FOUND
- Commits verified as ancestors of HEAD: 0189d4c, 5b111d7 — FOUND
- Commits measured from ledger base 83d86ba: 2 (matches per-task commits)
- All plan acceptance criteria re-run post-commit: PASS (vendored section verbatim at final HEAD; mapping total; parity green both directions; schema validation, hard edges, byte-stability, freeze all green; make test/lint/typecheck + uv lock --check green; zero dnallm imports; zero committed-data changes)
- Vendored aggregate_seeds diff vs `git show 483a35c:dnallm/finetune/sweep.py`: VERBATIM OK at final HEAD

---
*Phase: 04-correctness-methodology-core*
*Completed: 2026-10-10*
