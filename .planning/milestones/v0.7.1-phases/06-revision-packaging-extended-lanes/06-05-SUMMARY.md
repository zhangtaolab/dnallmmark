---
phase: 06-revision-packaging-extended-lanes
plan: 05
subsystem: pipeline-adapter
tags: [frozen-probe, config-variant, learning-curves, train-fraction, run-sweep, curve-points, gb10-smoke]
requires:
  - "06-02's alias seam + --num_train_epochs knob + trainable_params_pct persistence (the probe smoke's proof channel)"
  - "06-01's installed GPU env (dnallm 1.2.1, peft 0.21.2, torch 2.11.0+cu130, plant-dnabert-6mer in pipeline/models/)"
provides:
  - "run_finetune --config-variant {head,probe,curve} (default None): VARIANT_CONFIGS-mapped YAML reload at the exact special_models slot (before the D-11 snapshot; special_models auto-reload stays the byte-identical default override)"
  - "pipeline/finetune_config_probe.yaml: the with_head block with head mlp, frozen true, hidden_dims [512] (suite fields only — configs.py:14-17 / model.py:101-103 @ v1.2.1)"
  - "module-level PROBE_INELIGIBLE (deeplearning four + special_models pair + gpn/omnidna dedicated-loader members, one provenance comment each) + an argv-boundary guard refusing probe on special-loader models with a disclosing [Error]"
  - "{model}+probe alias default (probe variant only; head/curve do not alias; explicit --save_model_name wins)"
  - "run_finetune --train_fraction (float, (0,1] bounds, seed-governed shuffle-then-select on the TRAIN split only, frac-under-seed output nesting, fraction-scaled step cadence)"
  - "run_sweep --curve (collect-all fraction validation, 4-tuple cell expansion, frac-under-seed layout, LIST argv, run_record train_fraction field) + pipeline/finetune_config_curve.yaml (eval/save 100, logging 50)"
  - "run_sweep.extract_curve_points(trainer_state): pure offline reader of (step, eval-metrics) points from log_history"
affects:
  - "E2' (curve cells and probe runs enumerable/executable via the lane mechanisms; real runs stay maintainer-gated)"
  - "the frontier machinery (06-02): probe cells carry trainable_params_pct through the same final_metrics channel; build_frontier's method derivation already strips +probe"
tech-stack:
  added: []
  patterns:
    - "config-variant reload generalizing the special_models in-loop slot (additive; default pinned verbatim by contract)"
    - "enforced scope boundary as a module-level quirk list + argv-boundary fail-fast (the ineligibility guard)"
    - "4-tuple cell normalization in run_matrix with an additively-extended executor kwarg (train_fraction=None)"
key-files:
  created:
    - pipeline/finetune_config_probe.yaml
    - pipeline/finetune_config_curve.yaml
  modified:
    - pipeline/run_finetune.py
    - pipeline/run_sweep.py
    - tests/test_run_finetune_contracts.py
    - tests/test_sweep.py
decisions:
  - "VARIANT_CONFIGS maps head to the existing finetune_config_with_head.yaml (no finetune_config_head.yaml is authored): 'variant head is the explicit form of today's implicit special_models behavior' — the naming pattern ./finetune_config_<variant>.yaml applies to the two files this plan creates"
  - "variant reload sits BEFORE the special_models branch, so special models keep their own overriding reload under any variant (evo2/megaDNA never lose their required head config)"
  - "probe guard resolves the explicit --target_model or the full registry when absent — a whole-registry probe run hits the same special-loader boundary"
  - "dedicated special-loader family members derived by substring cross-reference against the suite handlers @ v1.2.1: gpn-brassicales + Omni-DNA-700M join the quirk lists' eight (the evo1 family has no registry members)"
  - "fraction-scaled step cadence (num_train_data rescale) added as Rule-2 critical functionality: without it a 0.25 cell's dynamic logging/eval/save cadence uses the full registry count and lands 4x sparser curve points"
  - "executor seam extended additively: executor(model, task, seed, output_root, train_fraction=None) — fake-executor provability of frac cells requires the fraction; the 4-arg injectable form holds for non-curve cells"
  - "--config-variant deliberately NOT forwarded through run_sweep (documented standalone composition — run_finetune --config-variant probe --train_fraction f nests {model}+probe/.../frac_{f}/ identically); half-wiring rejected"
metrics:
  duration: "15 min"
  completed: "2026-10-11"
estimate_provenance: "plan estimate: 45000 tokens / 2 tasks"
actuals:
  tokens: 24596    # chars/4 over git diff ab88923..HEAD (98384 chars)
  tasks: 2
  commits: 4       # MEASURED: git rev-list --count ab88923..HEAD
plan_head_before: ab889233d6221580e9618b8e9130795d230c78dd
plan_head_after: 7d850a51ca086c5cb9de80a9750bce680b992d6f
status: complete
coverage:
  - deliverable: "--config-variant mechanism (reload slot, registry mapping, default preservation)"
    verification:
      - kind: tests
        ref: "tests/test_run_finetune_contracts.py#test_config_variant_flag_declared_with_choices_and_none_default,test_variant_config_registry_maps_choices_to_real_files,test_variant_reload_occupies_the_special_models_slot_before_snapshot,test_per_dataset_head_config_task_type_assignment_untouched"
        status: pass
    human_judgment: false
  - deliverable: "probe ineligibility guard (enforced scope boundary)"
    verification:
      - kind: tests
        ref: "tests/test_run_finetune_contracts.py#test_probe_ineligible_list_covers_special_loader_families_with_provenance,test_probe_ineligibility_guard_fails_fast_before_model_loop"
        status: pass
    human_judgment: false
  - deliverable: "frozen probe YAML + +probe alias"
    verification:
      - kind: tests
        ref: "tests/test_run_finetune_contracts.py#test_probe_yaml_carries_the_frozen_mlp_head_block,test_probe_alias_defaults_only_for_the_probe_variant,test_peft_none_save_name_is_exactly_the_base_name"
        status: pass
      - kind: command
        ref: "grep gates: 'frozen: true' + head: \"mlp\" present in pipeline/finetune_config_probe.yaml"
        status: pass
    human_judgment: false
  - deliverable: "bounded 1-epoch probe smoke (frozen-backbone proof)"
    verification:
      - kind: command
        ref: "GB10 smoke: finetuned/plant-dnabert-6mer+probe/iDNA_ABF_datasets__5mC/seed_9527/final_metrics.json carries trainable_params 395778 / total_params 89591298 / trainable_params_pct 0.441759 in (0,5]"
        status: pass
    human_judgment: false
  - deliverable: "run_finetune --train_fraction (validator, seam, nesting, cadence)"
    verification:
      - kind: tests
        ref: "tests/test_run_finetune_contracts.py#test_train_fraction_flag_shape_and_seed_governed_semantics,test_train_fraction_validator_rejects_out_of_bounds,test_train_fraction_fail_fast_at_argv_boundary,test_apply_train_fraction_train_only_seed_governed,test_apply_train_fraction_absent_flag_is_noop,test_train_fraction_seam_sits_between_load_and_validate,test_frac_segment_nests_under_seed_in_default_outdir,test_fraction_scales_step_cadence_num_train_data"
        status: pass
    human_judgment: false
  - deliverable: "run_sweep --curve expansion (layout, argv, record, determinism, peft composition)"
    verification:
      - kind: tests
        ref: "tests/test_sweep.py#test_curve_flag_declared_in_parse_args,test_parse_curve_fractions_valid_sorted_deduped,test_curve_validation_collects_all_problems_together,test_curve_validation_refuses_empty_elements_and_empty_lists,test_enumerate_matrix_expands_fraction_cells_sorted,test_curve_composes_with_peft_enumeration,test_curve_dry_run_manifest_lists_frac_cells_nested_under_seed,test_build_argv_appends_train_fraction_as_list_element,test_new_record_train_fraction_field,test_run_matrix_curve_cell_record_and_frac_scoped_resume,test_default_executor_receives_train_fraction"
        status: pass
    human_judgment: false
  - deliverable: "curve YAML + extract_curve_points reader"
    verification:
      - kind: tests
        ref: "tests/test_run_finetune_contracts.py#test_curve_yaml_tightens_checkpoint_cadence_suite_fields_only + tests/test_sweep.py#test_extract_curve_points_sorts_and_filters_log_history,test_extract_curve_points_empty_or_absent_history,test_extract_curve_points_skips_unusable_entries"
        status: pass
      - kind: command
        ref: "grep gates: eval_steps: 100 + logging_steps: 50 in pipeline/finetune_config_curve.yaml; make data drift gate porcelain-empty"
        status: pass
    human_judgment: false
---

# Phase 06 Plan 05: Frozen probes + learning curves Summary

**One-liner:** The frozen-probe and learning-curve lanes are mechanism-complete: `--config-variant {head,probe,curve}` reloads its YAML at the exact special_models slot for any generic-path model with an enforced special-loader scope guard (PROBE_INELIGIBLE, provenance-commented), `run_finetune --train_fraction` subsets the TRAIN split via seed-governed shuffle-then-select with frac-under-seed output nesting and fraction-scaled cadence, `run_sweep --curve` expands fraction cells byte-deterministically (LIST argv + train_fraction record field + the no-sibling layout lock), and the tightened curve YAML + pure `extract_curve_points` reader close the offline harvesting loop — GPU-proven by a 1-epoch probe smoke reporting trainable_params_pct 0.441759 (head-only, backbone frozen).

## What Was Built

### Task 1 — --config-variant mechanism + probe YAML + guard + alias (commit 006c912)

**The flag + reload.** `--config-variant` (choices head/probe/curve, default None) joined the argparse seam. Inside the model loop, immediately after the per-model base reload and BEFORE the special_models membership branch, a guarded `configs = load_config(VARIANT_CONFIGS[config_variant])` generalizes the evo2/megaDNA reload to ANY model. The module-level `VARIANT_CONFIGS` maps `head → ./finetune_config_with_head.yaml` (the explicit form of today's implicit behavior — no separate head YAML exists or is needed), `probe → ./finetune_config_probe.yaml`, `curve → ./finetune_config_curve.yaml`. The special_models branch below is untouched and still overrides for its members under any variant (evo2/megaDNA never lose their required head config), and the D-11 grad_accum snapshot still sits after every reload — pinned by the evolved placement contract tests.

**The scope boundary.** A module-level `PROBE_INELIGIBLE` list (8 names, one provenance comment each) backs an argv-boundary guard: `--config-variant probe` resolves its target set (explicit `--target_model` or the full registry) and refuses any ineligible hit with an `[Error]` naming the model(s), the special-loader reason, and the suite anchors (model.py:1169-1228 dispatch → model.py:600-615 generic head routing → configs.py:14-17/model.py:101-103 the frozen field and freeze loop these loaders never reach). Membership derived by substring cross-reference against the suite's handler name lists @ v1.2.1: the deeplearning_models four (enformer/space/borzoi/flashzoi loaders), the special_models pair (evo2/megaDNA own-head branches), plus `gpn-brassicales` and `Omni-DNA-700M` — the two registry members of the remaining dedicated families (the evo1 family has no registry members).

**The probe YAML + alias.** `pipeline/finetune_config_probe.yaml` = the with_head block with `head: "mlp"`, `frozen: true`, `hidden_dims: [512]` — key surface exactly with_head's plus the suite's `frozen`, with a header comment citing configs.py:14-17 and model.py:101-103. The save-name chain gained a fourth branch: `elif config_variant == "probe": model_save_name = f"{model_name}+probe"` — after the peft alias, before the base-name else; explicit `--save_model_name` still wins; head/curve never alias.

**The bounded GB10 smoke (the ONLY sanctioned execution this plan).** From `pipeline/`, exit 0:

```bash
uv run --group gpu python run_finetune.py --target_model plant-dnabert-6mer \
    --target_dataset iDNA_ABF_datasets__5mC --config-variant probe \
    --num_train_epochs 1
```

`iDNA_ABF_datasets__5mC` is the n_audit picker's smallest locally-present task (Train=2110 — the same cell 06-02's LoRA smoke used). Key output lines verbatim:

```text
[2026-10-11 08:21:39] Loading model: plant-dnabert-6mer
[2026-10-11 08:21:42] Index: iDNA_ABF_datasets__5mC, Dataset: iDNA_ABF_datasets__5mC
Tokenizer type: 6mer. Infer max token length: 8
Training the model using 0.358945369720459 GB memory.
```

528 train steps in 20.75s; 0.36 GB peak memory; zero `[Error]`/`Error` lines in the full log (`/tmp/06-05-smoke-probe.log`). The `+probe` cell's `final_metrics.json` (full file, verbatim):

```json
{
    "train_runtime": 20.7514,
    "train_samples_per_second": 101.68,
    "train_steps_per_second": 25.444,
    "total_flos": 8714371233600.0,
    "train_loss": 2.834926215085116,
    "epoch": 1.0,
    "trainable_params": 395778,
    "total_params": 89591298,
    "trainable_params_pct": 0.441759
}
```

Acceptance: **trainable_params_pct = 0.441759 in (0, 5]** (asserted programmatically — a full-backbone run would report ~100) — head-only training proving the frozen backbone through the 06-02 persistence channel. The `trainer_state.json` resume marker landed inside the `+probe` cell (WR-13 ordering); the base-name dir `finetuned/plant-dnabert-6mer/` still contains only 06-01's dry-run shell (the probe run never touched the base name).

### Task 2 — learning curves (commits 66c1846, 6014e3c, 7d850a5)

**`--train_fraction` (66c1846).** Float flag (default None) + pure `validate_train_fraction` ((0, 1] bounds; fail-fast `[Error] invalid --train_fraction` at the argv boundary before the model loop) + the `apply_train_fraction` seam at the exact `--subset_file` slot (between `DNADataset.load_local_data` and `validate_sequences`): `train.shuffle(seed=seed).select(range(int(n * fraction)))` — TRAIN SPLIT ONLY (dev/test never touched; the eval-invariance guarantee asserted by the stub-split test), seed-governed per research A5 with plain first-N explicitly documented as NOT the semantics in the flag help. The output composition appends `frac_{train_fraction}/` UNDER the seed dir before the resume check, so `trainer_state.json` markers are (model, task, seed, fraction)-scoped and fraction runs never collide with full runs. The dynamic logging/eval/save step calculation now consumes the fraction-scaled train count (guarded; absent fraction = registry count, byte-identical).

**`--curve` expansion (6014e3c).** `run_sweep --curve "0.25,0.5,1.0"`: `parse_curve_fractions` validates collect-all (empty elements, non-numeric tokens, and bounds violations ALL listed in one exit; duplicates collapse; sorted ascending), then `enumerate_matrix(fractions=...)` expands each (model, task, seed) cell into sorted (model, task, seed, fraction) 4-tuples — `None` keeps the exact 3-tuple default enumeration. `cell_dir_for` nests `frac_{f}` under `seed_{s}` in every path (the no-sibling T-06-15 invariant, regression-locked by the manifest-walk test); `build_argv` appends `--train_fraction <f>` as LIST elements (composing with the peft alias argv); `_new_record` gains `train_fraction` (float for curve cells, null otherwise); `run_matrix` normalizes both cell arities and threads the fraction through the additively-extended executor kwarg (`executor(model, task, seed, output_root, train_fraction=None)`); the default executor path composes the fraction into the real argv (captured, never executed). Dry-run manifests enumerate frac cells byte-deterministically in sorted fraction order. `--curve` composes with `--peft` (alias cells expand across fractions). `pipeline/finetune_config_curve.yaml`: the base block with eval_steps/save_steps 100, logging_steps 50 — suite-owned TrainingArguments fields only, key surface identical to the base config. `--config-variant` is deliberately NOT forwarded through the sweep (standalone composition documented in the module docstring; half-wiring rejected).

**`extract_curve_points` (7d850a5).** Pure module-level reader: from a trainer_state structure's `log_history`, the (step, eval-metrics) points — only entries carrying `eval_` keys, non-eval keys excluded, sorted by step, non-dict entries and step-less eval entries skipped, absent/empty history → `[]`. Total over trainer_state shapes; synthetic-fixture tested (out-of-order, eval-less, empty).

## Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 | 006c912 | feat(06-05): config-variant mechanism + probe YAML + ineligibility guard |
| 2 | 66c1846 | feat(06-05): train-fraction flag |
| 2 | 6014e3c | feat(06-05): sweep curve expansion |
| 2 | 7d850a5 | feat(06-05): curve points reader |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Fraction-scaled step cadence**
- **Found during:** Task 2 implementation design
- **Issue:** run_finetune unconditionally overrides the YAML's logging/eval/save steps with `num_train_data * epoch // (eff_batch * 10)` using the REGISTRY Train count — a 0.25-fraction cell runs a quarter of the steps, so the computed cadence would land 4x fewer eval/save points than intended, defeating the curve lane's dense-checkpoint purpose (and leaving the tightened curve YAML values inert in the sweep path).
- **Fix:** a guarded `num_train_data = int(num_train_data * train_fraction)` between the registry read and the step calculation; absent fraction keeps the registry count (byte-identical default), and f=1.0 rescales to the same integer.
- **Files modified:** pipeline/run_finetune.py
- **Commit:** 66c1846

### Interpretations (no plan contract changed)

**2. VARIANT_CONFIGS maps `head` to the existing with_head file.** The plan's "./finetune_config_<variant>.yaml" naming pattern applies to the two YAMLs it authors (probe/curve); a literal `finetune_config_head.yaml` is never created, so the mapping `head → ./finetune_config_with_head.yaml` is what makes "variant head is the explicit form of today's implicit special_models behavior" literally true (same file, any model). Contract-tested.

**3. Variant reload BEFORE the special_models branch.** Keeps the special_models override last for its members — evo2/megaDNA never lose their required head config under any variant (the alternative order would reset head to "mlp" for them). The plan's "unchanged default" prohibition is satisfied either way; this ordering is the conservative one.

**4. The ineligible set's family derivation.** The plan names "the dedicated special-loader families from suite model.py:1169-1228"; their REGISTRY membership was derived by substring cross-reference against each handler's name list at v1.2.1 (enformer/space/borzoi+flashzoi = the deeplearning four; evo2/megadna = the special_models pair; gpn → gpn-brassicales; omnidna → Omni-DNA-700M; evo1 has no registry members). 8 total, each with its one-line provenance comment.

**5. Executor seam extended additively.** Fake-executor provability of frac cells (the plan's D-05 lineage) requires the fraction inside the executor: the call became `executor(model, task, seed, output_root, train_fraction=fraction)` — always passing the kwarg, with all existing test fakes updated to accept `train_fraction=None`. The 06-02 "4-arg seam unchanged" decision evolves additively for the new lane; non-curve cells behave identically.

**6. Per-commit micro-TDD cycles.** The plan's Task 2 prose says "write the tests FIRST across both files" then lists three commits; executing that literally would commit red intermediate states. Each commit instead carried its own RED→GREEN cycle (fraction tests → flag; curve tests → expansion+YAML; reader tests → reader), the atomic-commit + green-commit discipline — same final test surface (06-01 interpretation 3 precedent).

**7. One-commit window where VARIANT_CONFIGS referenced the not-yet-authored curve YAML** (between Task 1 and Task 2 commits): `--config-variant curve` would fail with a clear load_config file error in that window. Task 1's file-existence contract covered head+probe; Task 2's commit extended it to all three choices.

**8. The 06-02 save-name chain contract test evolved to the four-branch form** (the probe alias joins the chain after the peft elif) — extend-not-regress: the none-mode byte-identity, explicit-flag precedence, and peft-alias contracts are all still asserted, plus the probe branch. peft+probe combined runs (out of scope) keep the peft alias.

**Total deviations:** 1 auto-fixed (Rule 2) + 7 interpretations. **Impact:** none on default paths (all additions mode-guarded or additive; default-path byte-identity contract-pinned and suite-green).

## Verification Results

- `pytest tests/test_run_finetune_contracts.py tests/test_sweep.py -v`: **125 passed** (was 94 at baseline; +31 new tests: 8 Task-1 contracts, 8 fraction contracts, 14 sweep curve tests incl. the no-sibling lock, 1 curve-YAML contract)
- Probe YAML grep gates: `frozen: true` + `head: "mlp"` present; curve YAML grep gates: `eval_steps: 100` + `logging_steps: 50` + `save_steps: 100` present
- Bounded smoke: exit 0; `finetuned/plant-dnabert-6mer+probe/iDNA_ABF_datasets__5mC/seed_9527/final_metrics.json` present with `trainable_params_pct` **0.441759** in (0, 5] (asserted programmatically); `trainer_state.json` marker inside the +probe cell; base-name task dir untouched
- `make lint` / `make typecheck`: clean (no widened suppressions; no new files joined the lint list)
- `make test`: **431 passed** + JS lane 18 pass / 0 fail (was 400 + 18 at baseline)
- `make data` + porcelain on `dnallm-mark/data/`: **no-op** (drift gate green — the lane is execution-free and number-neutral)
- Suite repo: `git -C /home/forrest/Github/DNALLM status --porcelain` EMPTY at every checkpoint (read-only respected; all suite anchors read at tag v1.2.1)
- Working tree clean after all commits

## Test Coverage

- **Contracts (source-text, never imported):** the flag shape (choices/default-None); VARIANT_CONFIGS module-level mapping with real on-disk files for every choice; the variant reload's slot placement (after base reload, before the unchanged special_models branch, before the D-11 snapshot) with the special branch pinned verbatim; PROBE_INELIGIBLE membership (exact 8, superset of both quirk lists, registry-resolved, per-line provenance comments); the guard's fail-fast (before the model loop, [Error] message naming models + special-loader reason + suite anchors, target_model honored); the four-branch save-name chain (probe-only aliasing, no head/curve aliases anywhere); the probe YAML (frozen/mlp/[512], key surface = with_head + frozen, suite-anchor citations); the per-dataset head_config.task_type assignment variant-unconditioned; the fraction flag (float/None, A5 seed-governed + first-N-not semantics + train-only in the help); the pure validator bounds; the fail-fast wiring before the model loop; the fraction seam slot (load < apply < validate); the frac-under-seed nesting before the resume check; the fraction-scaled cadence placement; the curve YAML cadence + field-surface equality with the base.
- **Behavioral (exec-extracted pure fns):** apply_train_fraction on stub splits — shuffle called with the run seed, select exactly int(n*f) rows, train split only (dev/test zero calls — the eval-invariance guarantee), f=1.0 full keep, None no-op.
- **Sweep (imported, fake-executor discipline):** the collect-all curve validation (all three problem classes in one exit; empty elements; no-fraction refusal); 4-tuple expansion sorted with the 3-tuple default byte-identical; peft composition; the no-sibling manifest-walk lock (every frac_ directly under a seed_); dry-run byte determinism + sorted fraction order; argv LIST composition (fraction alone + peft+fraction); the train_fraction record field; the frac-scoped resume (frac_0.25 marker never skips frac_1.0) with the record written inside the frac dir; the default executor's fraction threading; extract_curve_points over synthetic fixtures (out-of-order sorted, eval-less skipped, non-eval keys excluded, empty/absent/None total, unusable entries skipped).
- GPU-side proof is the executed probe smoke itself — by design never in `make test`/CI.

## Known Stubs

None. (The lane mechanisms are complete; their real executions — curve sweeps, probe runs beyond the smoke — are post-E2' maintainer-gated actions by the plan's own boundary, not stubs.)

## Self-Check: PASSED

All six created/modified files exist on disk; all four commits (006c912, 66c1846, 6014e3c, 7d850a5) verified as ancestors of HEAD; commits measured at 4 via `git rev-list --count ab88923..HEAD`; 06-05-SUMMARY.md written to the phase directory.
