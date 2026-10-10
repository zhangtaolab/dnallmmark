---
phase: 06-revision-packaging-extended-lanes
plan: 02
subsystem: pipeline-adapter
tags: [peft, lora, ia3, adapter-aliases, trainable-params, run-sweep, frontier, schema, gb10-smoke]
requires:
  - "06-01's --peft tracer + installed GPU env (dnallm 1.2.1, peft 0.21.2, torch 2.11.0+cu130, plant-dnabert-6mer in pipeline/models/)"
  - "the F2 run-record contract (run_sweep run_record.json / run_finetune final_metrics.json)"
provides:
  - "adapter-run name isolation: --peft lora|ia3 without --save_model_name defaults to {model}+lora/+ia3 (separate output dir AND trainer_state.json marker; explicit flag wins; registry lookup stays base)"
  - "--num_train_epochs (int, default None) config override — the bounded-smoke knob (plan-check blocker fix)"
  - "trainable_params / total_params / trainable_params_pct persisted into final_metrics.json for EVERY mode (the frontier producer gap closed)"
  - "run_sweep --peft {none,lora,ia3}: alias cell enumeration, LIST argv (--target_model base + --save_model_name alias + --peft mode), run_record peft field"
  - "script/build_frontier.py + schemas/frontier.json + generator-produced tests/fixtures/frontier/frontier_sample.json (cost-accuracy frontier machinery; real numbers land post-E2')"
  - "GPU-proven alias+persistence path: 1-epoch LoRA smoke, pct 0.331253 in (0,5], base dir untouched"
affects:
  - "06-05 (frozen probes ride the alias/variant seams: +probe suffix already forward-compatible in the frontier method derivation)"
  - "06-03 (VEP/curve lanes compose on the verified adaptation + this plan's sweep-threading discipline)"
  - "E2' (adapter sweep cells now enumerable via run_sweep --peft; frontier rows derive the moment real runs exist)"
tech-stack:
  added: []
  patterns:
    - "alias isolation via save_model_name defaults + suffix-stripping joins (D-18 discipline)"
    - "post-ctor pure-arithmetic persistence complementing suite-owned printing (never re-implementing _guard_trainable_ratio)"
    - "frontier generator importing the exporter's single reader + metric authorities (load_run_records / resolve_dataset_metric / resolve_metric_key)"
key-files:
  created:
    - script/build_frontier.py
    - schemas/frontier.json
    - tests/test_frontier.py
    - tests/fixtures/frontier/frontier_sample.json
  modified:
    - pipeline/run_finetune.py
    - pipeline/run_sweep.py
    - tests/test_run_finetune_contracts.py
    - tests/test_sweep.py
decisions:
  - "frontier rows are one-per-COMPLETED-run-record (per-seed granularity): every column traces to 'the record' singular; the score_delta none-counterpart is the per-(base_model, task) MEAN over none-method seeds"
  - "method=none rows carry score_delta null + a reference note (delta is defined for adapter rows only); only total_flos is hard-required — timestamp/pct/score gaps are null+disclosed (skip-as-data)"
  - "build_frontier's default output dir derives {input-root}/frontier (a sibling, D-16 pattern) — never dnallm-mark/data; publication + SCHEMA_FILES bucket + DATA.md link all gated on real post-E2' numbers (resolved OQ)"
  - "the default sweep executor binds peft via functools.partial(launch_subprocess, peft=...) — the injectable 4-arg executor seam is unchanged"
  - "REV-05 NOT marked complete: 06-05 is the final carrier (frozen probes + response-letter packaging)"
metrics:
  duration: "~23 minutes"
  completed: "2026-10-11"
estimate_provenance: "plan estimate: 65000 tokens / 3 tasks"
actuals:
  tokens: 22574    # chars/4 over git diff f4bc1e9..HEAD (90296 chars)
  tasks: 3
  commits: 4       # MEASURED: git rev-list --count f4bc1e9..HEAD
plan_head_before: f4bc1e98b1df79b3cd6f0d627c1667b192ae8c37
plan_head_after: 872201259ce8f6a4c3093c8fb0ececb0ff98d715
status: complete
coverage:
  - deliverable: "adapter alias defaults + epochs override (run_finetune)"
    verification:
      - kind: tests
        ref: "tests/test_run_finetune_contracts.py#test_adapter_alias_defaults_when_peft_mode_active,test_explicit_save_model_name_wins_over_alias_default,test_registry_lookup_stays_on_base_model_name,test_peft_none_save_name_is_exactly_the_base_name,test_num_train_epochs_flag_overrides_config_only_when_given"
        status: pass
    human_judgment: false
  - deliverable: "trainable-params persistence into final_metrics (run_finetune)"
    verification:
      - kind: tests
        ref: "tests/test_run_finetune_contracts.py#test_trainable_params_persisted_into_final_metrics_for_every_mode"
        status: pass
      - kind: command
        ref: "GB10 smoke: final_metrics.json carries trainable_params 296450 / total_params 89493508 / trainable_params_pct 0.331253 in (0,5]"
        status: pass
    human_judgment: false
  - deliverable: "run_sweep --peft threading (alias cells, LIST argv, record field)"
    verification:
      - kind: tests
        ref: "tests/test_sweep.py#test_peft_none_default_is_byte_identical_to_today,test_enumerate_matrix_emits_alias_cells_under_peft,test_build_argv_targets_base_and_saves_alias_as_list_elements,test_run_matrix_writes_peft_record_inside_alias_cell_dir,test_alias_marker_does_not_skip_base_cell,test_dry_run_peft_manifest_lists_alias_cells_only"
        status: pass
    human_judgment: false
  - deliverable: "frontier machinery (generator + schema + fixture)"
    verification:
      - kind: tests
        ref: "tests/test_frontier.py#test_rows_derive_every_column_from_the_record_contracts,test_missing_total_flos_aborts_naming_the_record,test_emission_is_byte_deterministic,test_generator_emission_validates_against_the_schema,test_committed_fixture_is_generator_produced,test_no_committed_frontier_artifact_exists"
        status: pass
      - kind: command
        ref: "make data drift gate: dnallm-mark/data porcelain empty AND dnallm-mark/data/frontier.json absent"
        status: pass
    human_judgment: false
---

# Phase 06 Plan 02: LoRA/IA3 lane expansion — aliases, persistence, sweep threading, frontier machinery Summary

**One-liner:** Adapter runs are now name-isolated end-to-end (`{model}+lora`/`+ia3` save-name defaults with separate resume markers, `--num_train_epochs` smoke knob, trainable-params persisted into final_metrics for every mode), run_sweep threads `--peft` through alias-cell enumeration + LIST argv + a record `peft` field, and the cost-accuracy frontier machinery (generator importing the exporter's reader/metric authorities, strict schema, generator-produced fixture) is in place — proven by a real 1-epoch GB10 LoRA smoke reporting trainable_params_pct 0.331253.

## What Was Built

### Task 1 — adapter aliases + epochs override + trainable-params persistence (2 commits)

**Commit 6748b92:** the save-name resolution at the outdir block became a three-branch chain — explicit `--save_model_name` > peft alias `f"{model_name}+{peft_mode}"` (only when `peft_mode != "none"`) > base name — so an adapter run with no explicit save name writes `{model}+lora/...` and gets a distinct `trainer_state.json` resume marker with ZERO layout-code changes; the registry lookup / target_model filtering / quirk lists all stay keyed on the base `model_name`; the none-mode outdir is byte-identical to today (the else branch is exactly `model_name`). In the same commit, `--num_train_epochs` (int, default None) landed as the plan-check blocker fix: a None-guarded `configs["finetune"].num_train_epochs = num_train_epochs` assignment placed AFTER the custom-head reload (so a with_head reload cannot clobber it) and BEFORE the epoch read that sizes logging/eval/save steps and the DNATrainer ctor — the bounded-smoke knob this plan's own verify and 06-05's probe smoke use.

**Commit 8c8e55c:** immediately after the DNATrainer ctor, `trainable_params` (sum of `p.numel()` filtered on `requires_grad`), `total_params` (unfiltered sum), and `trainable_params_pct` (`round(100.0 * trainable / max(total, 1), 6)` — the max guard mirrors the suite's `_guard_trainable_ratio` at trainer.py:285) are computed over `trainer.model.parameters()` — the CONSTRUCTED model, adapter-wrapped under peft (the suite assigns `self.model = get_peft_model(...)` in the ctor) — and merged into the metrics payload at the final_metrics.json write for EVERY mode including none (a full run reports 100.0). One comment records why run_finetune owns this: the suite prints but does not persist (trainer.py:248-288 @ v1.2.1); the frontier table needs the value in the record chain, and the sweep copies final_metrics verbatim into run_record.metrics.

### The bounded GB10 smoke (sanctioned; the ONLY execution this plan)

Command (from `pipeline/`, exit 0):

```bash
uv run --group gpu python run_finetune.py --target_model plant-dnabert-6mer \
    --target_dataset iDNA_ABF_datasets__5mC --peft lora --num_train_epochs 1
```

`iDNA_ABF_datasets__5mC` is the verify picker's `min(cand)` task (Train=2110, the smallest locally-present task). Key output lines verbatim:

```text
[2026-10-11 02:43:06] Loading model: plant-dnabert-6mer
[2026-10-11 02:43:09] Index: iDNA_ABF_datasets__5mC, Dataset: iDNA_ABF_datasets__5mC
[Info] LoRA preset 'Plant DNABERT' selected (matched by name marker 'plant-dnabert'): target_modules=['query', 'value']
[Info] Applying LoRA to the model...
trainable params: 296,450 || all params: 89,493,508 || trainable%: 0.3313
Training the model using 0.5345144271850586 GB memory.
```

528 train steps in 42.4s; 0.53 GB peak memory. `pipeline/finetuned/plant-dnabert-6mer+lora/iDNA_ABF_datasets__5mC/seed_9527/final_metrics.json` (the full file, verbatim):

```json
{
    "train_runtime": 42.416,
    "train_samples_per_second": 49.745,
    "train_steps_per_second": 12.448,
    "total_flos": 8704467062400.0,
    "train_loss": 2.8594008937026514,
    "epoch": 1.0,
    "trainable_params": 296450,
    "total_params": 89493508,
    "trainable_params_pct": 0.331253
}
```

Acceptance checks: **pct 0.331253 in (0, 5]** (PASS, asserted programmatically); the suite's own ctor print (`trainable%: 0.3313`) cross-validates the persisted value; the base-name dir `finetuned/plant-dnabert-6mer/iDNA_ABF_datasets__5mC/` does NOT exist (the adapter run never touched the base name — the only entry under the base dir is 06-01's dry-run `BEND__CpG_methylation` shell). Full log: `/tmp/06-02-smoke-lora.log`.

### Task 2 — run_sweep --peft threading (commit c5cad04)

`--peft {none,lora,ia3}` (default none) joined the argparse block. `enumerate_matrix` gained the `peft="none"` kwarg: registry iteration and the `--models` join stay on BASE names, the emitted cells carry the ALIAS (`{model}+{peft}`), and sorting happens after the mapping (determinism preserved). `build_argv` under peft targets `--target_model <base>` (suffix-stripped via `removesuffix(f"+{peft}")`) and appends `--save_model_name <alias>` + `--peft <mode>` as separate LIST elements; under none the argv is byte-identical to the pre-peft form. `_new_record` gained a `peft` field (string, default "none", sorted-key stable in the deterministic write). `run_matrix` binds the default executor with `functools.partial(launch_subprocess, peft=peft)` — the injectable 4-arg executor seam is untouched. The seed-dir layout and marker-skip logic are UNCHANGED (alias isolation comes entirely from the model-level dir name — proven by the alias-marker-never-skips-base-cell test). Dry-run manifests enumerate alias cells only, byte-deterministically.

### Task 3 — frontier table machinery (commit 8722012)

**script/build_frontier.py:** banner conventions (Purpose / Direction-of-truth / Usage; REPO_ROOT-relative argparse). Imports `load_run_records`, `resolve_dataset_metric`, `resolve_metric_key` from `export_runs` — the single reader + single metric authority; the module never walks the tree (`iterdir` absent, contract-tested). One row per COMPLETED run record: `model` (alias display), `base_model` (suffix-stripped — `+lora/+ia3/+probe`, probe for 06-05), `method` (suffix first, else the record `peft` field, else none), `wall_hours` (started_at→finished_at, wall-clock, 6dp, null+disclosed when missing/unparseable), `total_flos` (record metrics — a completed record missing it aborts naming the record path, mirroring the exporter), `trainable_params_pct` (null + disclosed "predates the 06-02 persistence" note for old records), `score` (the task's primary metric via the exporter surface — the synthetic fixture exercises the legacy `F1` translation), `score_delta` (method score minus the none-method MEAN per (base_model, task); null + disclosed with no counterpart; none rows are the reference), `notes` (every disclosure — skip-as-data, never silent drops). Dual emission `frontier.json` + `frontier.csv` (fixed column order, `\n` endings) + optional `--data-md` appendix mode (implemented + tested, NOT wired into DATA.md). Default output dir derives `{input-root}/frontier` — a SIBLING of the input root, never `dnallm-mark/data`.

**schemas/frontier.json:** strict draft-2020-12 (additionalProperties false, all fields required, closed method enum incl. probe); the `$comment` discloses derivation sources, the wall-clock-not-GPU-hours basis, the null/skip-as-data semantics, and that real numbers arrive post-E2'.

**tests/fixtures/frontier/frontier_sample.json:** produced by RUNNING the generator over the canonical synthetic tree (base+alias cells, a pre-persistence record, a missing-counterpart alias) via the test module's own builder — chain-produced only; `test_committed_fixture_is_generator_produced` byte-pins it to the generator (the regeneration path IS the test). NOTHING registered in `tests/test_schemas.py` SCHEMA_FILES — the bucket lands with the first real data file post-E2'.

## Commits

| Task | Commit | Subject |
|---|---|---|
| 1 | 6748b92 | feat(06-02): adapter alias defaults + epochs override |
| 1 | 8c8e55c | feat(06-02): trainable-params persistence into final_metrics |
| 2 | c5cad04 | feat(06-02): run_sweep --peft threading — alias cells, LIST argv, record field |
| 3 | 8722012 | feat(06-02): frontier table machinery — generator, schema, synthetic fixture |

## Deviations from Plan

None - plan executed exactly as written.

### Interpretations (no plan contract changed)

1. **Frontier row granularity is one-per-completed-run-record** (per-seed). The behavior rows say "the record" singular for wall_hours/total_flos/trainable_params_pct; the none-counterpart for score_delta is the per-(base_model, task) MEAN over none-method completed seeds — deterministic and stable under seed count changes.
2. **method=none rows carry score_delta null + a "reference" note.** The plan specifies null+disclosed only for the no-counterpart case; none-row semantics were Claude's discretion. A 0.0 self-delta would be trivially true noise — null with the disclosure is the honest form.
3. **Only total_flos is hard-required.** Missing/unparseable timestamps or a missing primary-metric value emit null + a disclosed note (skip-as-data), matching the plan's single mandated abort (missing-flos) without over-aborting on non-flos gaps.
4. **The committed fixture was regenerated once after test-file lint refactors** (lambda → def, import order) — the canonical tree's metric VALUES are identical, so the fixture bytes are unchanged; the byte-pin test re-verified equality after the refactor.
5. **Smoke executed in the background** (a ~3-minute run under the plan's generous-timeout guidance); all evidence captured from the completed run's log and on-disk artifacts.

## Verification Results

- `pytest tests/test_run_finetune_contracts.py -v`: 39 passed (was 34; +5 new: alias chain shape, explicit-flag precedence, base-name registry lookup, none-equivalence evolution, epochs override; +1 persistence = 6 new total vs 06-01's 33-peft-era set... net +5 from 34)
- `pytest tests/test_sweep.py -v`: 55 passed (+8 peft-threading tests)
- `pytest tests/test_frontier.py -v`: 12 passed (new file)
- `make test`: **349 passed** (+ node lane 15 pass / 0 fail) — was 324 at baseline
- `make lint` / `make typecheck`: clean; `ruff check script/build_frontier.py` direct: clean (the Makefile lint-list line lands in 06-04 per the file-disjoint wave rule)
- `make data` + porcelain on `dnallm-mark/data/`: no-op (drift gate green); `dnallm-mark/data/frontier.json` ABSENT (publication gate)
- Bounded smoke: exit 0, alias dir + final_metrics.json present, pct 0.331253 in (0,5] asserted, base-name task dir absent
- Suite repo: `git -C /home/forrest/Github/DNALLM status --porcelain` EMPTY at every checkpoint (read-only respected)
- Working tree clean after all commits

## Test Coverage

- **run_finetune contracts (source-text, never imported):** the three-branch save-name chain (explicit > alias > base) as one regex-pinned block resolving before the outdir f-string; explicit-flag adjacency to the peft elif; the target_model filter and the entire quirk-mutation region free of `model_save_name`; the none-mode else branch exactly `model_name`; every peft config mutation still mode-guarded; `--num_train_epochs` flag shape (int/None) + None-guarded assignment + placement (after with_head reload, before the epoch read and the ctor); the persistence arithmetic strictly between ctor and write, filtered+unfiltered sums over `trainer.model.parameters()`, 6dp rounding, the three merge keys at the write block, and NO `if peft_mode` guard between ctor and computation (none-mode universality).
- **run_sweep (imported, fake-executor discipline):** none-equivalence across enumeration/argv/record; alias enumeration with base-name join proof (an alias-typed filter finds nothing); argv composition in both modes with all flags separate LIST elements; launch-path argv capture (monkeypatched subprocess.run, never executed); the default executor's peft threading (incl. the _git_commit fake-stdout interaction); the peft record inside the alias cell dir; alias-marker never skips a base cell; dry-run manifest alias-only + byte-determinism.
- **frontier:** every column derivation over the canonical tree (incl. legacy F1→eval_f1 resolution, the delta mean, the two null classes); the missing-flos abort naming the record path; byte-determinism of both artifacts; schema validation of the emission AND the committed fixture; the fixture byte-pinned to the generator's output; the publication gate (no committed frontier.json, no DATA.md mention, sibling default output dir); probe + record-field method derivation; --data-md emission + determinism; the import-authority contract (`from export_runs import` the three names, no `iterdir`).
- GPU-side proof is the executed smoke itself — by design never in `make test`/CI.

## Known Stubs

None. (The `--data-md` appendix mode is implemented AND tested — its NON-wiring into DATA.md is the resolved-OQ publication gate, not a stub.)

## Self-Check: PASSED

All four commits verified as ancestors of HEAD (6748b92, 8c8e55c, c5cad04, 8722012); all eight created/modified files exist on disk; commits measured at 4 via `git rev-list --count f4bc1e9..HEAD`; 06-02-SUMMARY.md written to the phase directory.
