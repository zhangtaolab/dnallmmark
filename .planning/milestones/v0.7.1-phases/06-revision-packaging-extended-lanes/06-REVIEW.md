---
phase: 06-revision-packaging-extended-lanes
reviewed: 2026-10-11T00:00:00Z
depth: deep
files_reviewed: 38
files_reviewed_list:
  - pipeline/run_finetune.py
  - pipeline/run_sweep.py
  - pipeline/env_smoke.py
  - pipeline/finetune_config.yaml
  - pipeline/finetune_config_with_head.yaml
  - pipeline/finetune_config_probe.yaml
  - pipeline/finetune_config_curve.yaml
  - pipeline/datasets_info.json
  - pipeline/models_info.json
  - script/export_runs.py
  - script/zero_shot_vep.py
  - script/build_frontier.py
  - script/build_provenance.py
  - script/convert_registry.py
  - script/doi_swap.py
  - script/freeze_snapshot.py
  - schemas/frontier.json
  - schemas/provenance.json
  - schemas/vep_zero_shot.json
  - schemas/task_performance.json
  - schemas/model_performance.json
  - dnallm-mark/js/data.js
  - dnallm-mark/js/config.js
  - dnallm-mark/data/provenance.json
  - dnallm-mark/data/provenance.csv
  - baseline/snapshots/snapshot-991804613c4874bfa3f32d318340b5d7b4118ffe.sha256
  - docs/METHODOLOGY.md
  - docs/ONBOARDING.md
  - DATA.md
  - README.md
  - Makefile
  - .gitignore
  - tests/test_run_finetune_contracts.py
  - tests/test_sweep.py
  - tests/test_frontier.py
  - tests/test_zero_shot_vep.py
  - tests/test_build_provenance.py
  - tests/test_doi_swap.py
  - tests/test_convert_registry.py
  - tests/test_export_runs.py
  - tests/test_schemas.py
  - tests/js/data-api.test.js
  - tests/js/main-view-toggle.test.js
findings:
  critical: 1
  high: 1
  medium: 4
  warning: 13
  low: 9
  info: 2
  total: 16
status: issues_found
---

# Phase 06: Code Review Report

**Reviewed:** 2026-10-11 (commits 83bdbaf..ea83def, 32 execution commits across plans 06-01..06-05)
**Depth:** deep (per-file + cross-file: DNALLM suite v1.2.1 tag reads for every cited seam, registry↔suite dispatch cross-derivation, empirical reproductions of three defects, gate reruns: 324 targeted pytest, `make lint`, `ty check`, node lane 18/18, `make data` drift no-op)
**Files Reviewed:** 38 source/config/schema/doc files (+ committed artifacts and fixtures inspected as evidence; fixture data files not reviewed as code, per scope)
**Status:** issues_found — 1 high (blocker-tier), 4 medium, 9 low, 2 info

## Summary

Phase 06 is largely solid: the seed_result reader matches the actual v1.2.1
suite writer shape exactly; the trainable-params persistence, epochs-override
seam, frac-under-seed nesting, and tolerant-reader precedence are all as
documented; the VEP driver's lazy-import boundary is clean (zero module-level
dnallm/torch/peft in script/ or tests/), its 62-row census (32 MLM / 18 CLM /
5 DL / 7 empty) and genetic code check out, and the RC round-trip tokens
("Pathogenic"/"Benign"/"criteria_provided") all satisfy the suite whitelists;
the snapshot lane re-verifies with the literal `sha256sum -c` one-liner; the
dead `recalculateComparison` removal is complete with no orphaned callees;
`make data` is a verified no-op on the committed tree; data_version stays
1.1.0; no new tags; CI surface untouched; ruff/ty/pytest/node all green.

Four defects survive adversarial scrutiny, one of them exactly in the area
most likely to hide a real defect:

1. **PROBE_INELIGIBLE is incomplete — the registry's uppercase `SPACE` row
   dispatches to the suite's dedicated space loader but is not in the list**
   (HIGH, CONFIRMED against the v1.2.1 tag and by guard simulation). The
   pinning contract test hard-codes the same 8-member set, so it cannot catch
   the omission.
2. **`--from-failures` cannot recover a `--peft` sweep**: the failures
   manifest records ALIAS model names, which the validator rejects as
   not-in-registry (MEDIUM, CONFIRMED empirically).
3. **The env_smoke 1.2.1 relabel is factually wrong on the datasets cap**
   (claims `datasets<=3.2.0`; the v1.2.1 pyproject declares `datasets<=5.1.0`)
   in three places, in a commit whose stated purpose was verified relabeling
   (MEDIUM, CONFIRMED against the tag's pyproject).
4. **The reviewer-facing provenance correction path is broken as documented**:
   "edit `data/provenance.csv`, ingest via `convert_registry.py --to-json
   --merge-existing`" aborts — the CSV's name column is `dataset`, the
   datasets preset requires `Dataset_name`, and the new required-header gate
   demands all 21 preset columns the 7-column projection lacks (MEDIUM,
   CONFIRMED empirically).

The two specifically-adjudicated areas:

- **Frontier score_delta semantics: SOUND.** The none-counterpart reference is
  the per-`(base_model, task)` mean over completed none-method seeds; adapter
  rows carry `score - mean`, none rows carry null + a reference note, missing
  counterparts carry null + disclosure — coherent, tested
  (tests/test_frontier.py:232-235), and direction-uniform because every
  registry primary metric (f1 37, mcc 6, spearmanr 3, r2 3, AUPRC 1) is
  higher-is-better. The one latent hazard is not in the delta math but in the
  alias-default gap (MED-04 below): a config-variant run that lands under a
  BASE model name is classified `method=none` and would pollute the reference
  mean.
- **PROBE_INELIGIBLE completeness: INCOMPLETE** (see HI-01) — 9 registry
  models dispatch to a special loader at v1.2.1; the list covers 8.

Documented deviations in the five SUMMARYs were accepted and are not
re-reported (notably the `--peft_dry_run` trailing "max() iterable argument is
empty" console line, disclosed in 06-01-SUMMARY as observed-and-accepted).

## High (blocker-tier)

### HI-01: PROBE_INELIGIBLE omits the registry's `SPACE` row — probe guard passes, suite trains unfrozen under a `+probe` dir

**File:** `pipeline/run_finetune.py:452-461` (list), `:697-714` (guard)
**Issue:** CONFIRMED. The registry (`pipeline/models_info.json`) carries TWO
distinct rows, `SPACE` (Model_path `models/SPACE`) and `space`
(`models/space`). The suite dispatches on substring matches over the full
local path (dnallm/models/special/space.py:10 `space_models = ["SPACE"]` via
model.py:1207-1215): the uppercase row is claimed by the NATIVE list member
(`"SPACE" in ".../models/SPACE"`, case-sensitive), the lowercase row by the
`extra` self-append (`"space" in path.lower()`). Both therefore bypass the
generic `head_config` routing (model.py:600-615), so `task.head_config.frozen`
(configs.py:14-17; freeze loop model.py:101-103) never applies to either. The
guard, however, checks exact-name membership:

```python
PROBE_INELIGIBLE = [
    "enformer-official-rough",  # enformer dedicated loader ...
    "space",                    # SPACE dedicated loader ...
    ...
]
...
ineligible_hits = sorted(
    name for name in probe_targets if name in PROBE_INELIGIBLE
)
```

`"SPACE" not in PROBE_INELIGIBLE`, so `run_finetune --config-variant probe
--target_model SPACE` passes the guard (verified by simulation: guard passes,
registry row exists), the suite loads SPACE through
`SpaceForSequenceClassification`, the backbone is never frozen, and the run
silently trains a full unfrozen model under `finetuned/SPACE+probe/...` with
`trainable_params_pct ≈ 100` — precisely the integrity failure the guard
exists to prevent, reachable in targeted AND whole-registry mode. The contract
test `test_probe_ineligible_list_covers_special_loader_families_with_provenance`
(tests/test_run_finetune_contracts.py:1651-1683) pins the exact same 8-member
set, and its `deeplearning_models ⊆ members` cross-check passes vacuously
because the pre-existing `deeplearning_models` list also spells only
lowercase `space` — nothing in the suite can catch this.

**Failure scenario:** a future whole-registry probe lane (the REV-05 response
letter's frozen-probe table) runs SPACE unfrozen; its row is published as a
"frozen probe" result. Silent wrong science on the public leaderboard.

**Fix:** add the uppercase row (and derive, don't pin):

```python
PROBE_INELIGIBLE = [
    "enformer-official-rough",
    "SPACE",   # uppercase registry row: native space_models member "SPACE"
    "space",   # lowercase registry row: claimed via the extra self-append
    "borzoi-replicate-0", "flashzoi-replicate-0",
    "evo2_1b_base", "megaDNA_updated",
    "gpn-brassicales", "Omni-DNA-700M",
]
```

and update the pinning test to derive the expected set from the registry ×
suite dispatch (or at minimum assert `{"SPACE", "space"} <= set(members)`).

## Medium

### MED-01: `--from-failures` cannot recover a `--peft` sweep — alias model names recorded, then rejected as not-in-registry

**File:** `pipeline/run_sweep.py:1073-1079` (writer), `:714-723` (validator)
**Issue:** CONFIRMED empirically. Under `--peft lora`, cells enumerate under
the alias (`{base}+lora`), and every failures entry records that alias:

```python
failures.append({
    "model": model,   # the ALIAS under --peft (cell[0])
    ...
})
```

but `load_failure_pairs` validates against registry KEYS (base names):

```python
if model not in known_models:
    problems.append(
        f"--from-failures model not in registry: {model!r} (entry {idx})"
    )
```

Feeding a peft sweep's own `sweep_failures.json` back (with or without
`--peft`) exits non-zero: `[Error] --from-failures model not in registry:
'plant-dnabert-6mer+lora' (entry 0)` (reproduced). The module docstring
advertises this exact workflow ("re-enumerates exactly the failed (model,
task) pairs named in the manifest"); no test covers from-failures × peft.

**Fix:** in `load_failure_pairs`, strip a known alias suffix before
validation and re-key the pair to the base name (mirroring `build_argv`'s
`model.removesuffix(f"+{peft}")`), or record BOTH `model` (alias) and
`base_model` in failure entries and validate/join on `base_model`.

### MED-02: env_smoke 1.2.1 relabel is factually wrong — v1.2.1 caps `datasets<=5.1.0`, not `<=3.2.0`

**File:** `pipeline/env_smoke.py:49` (check-6 docstring), `:203`
(diagnostics docstring), `:223` (INFO print line)
**Issue:** CONFIRMED against the tag: `git show v1.2.1:pyproject.toml` line
31 declares `"datasets<=5.1.0"`. All three relabeled sites say:

```python
"(dnallm 1.2.1 caps datasets<=3.2.0, no pyarrow pin — dnallm's "
```

The `3.2.0` figure is the retired 0.8.x-era cap the relabel commit (1298eef)
was supposed to replace; the diagnostics docstring even claims "verified
read-only against the v1.2.1 pyproject". The neighboring claims ARE correct
(`numpy>=2.0.0` at pyproject:48, `peft>=0.14.0` at :52, no pyarrow
constraint, trainer.py:58 hard-imports peft). A maintainer reading smoke
output on GB10 is misinformed about resolution constraints.

**Fix:** replace `datasets<=3.2.0` with `datasets<=5.1.0` at all three sites.

### MED-03: The documented provenance correction path aborts — provenance.csv cannot be ingested by convert_registry

**File:** `script/build_provenance.py:82-84` (BEGIN_MARKER text), `:175-176`
(appendix body), `:14-18` (docstring); `schemas/provenance.json:5`
($comment); `DATA.md:110,123` (committed generated appendix)
**Issue:** CONFIRMED empirically. Three shipped surfaces instruct the
maintainer/reviewer:

```
correct values in dnallm-mark/data/provenance.csv, ingest via
script/convert_registry.py --to-json --merge-existing, then re-run `make data`
```

but the ingest dies at the first gate:

```
[Error] Header of dnallm-mark/data/provenance.csv lacks name column
'Dataset_name' (found: ['dataset', 'source', 'citation', 'license',
'preprocessing', 'download_url', 'download_url_alternates'])
```

and even with a header rename it would die at the new required-header gate
(06-04's own hardening) demanding all 21 datasets-preset columns the 7-column
projection lacks. The 06-04 SUMMARY records the maintainer accepting the
provenance state on the understanding that "corrections may come anytime
later via provenance.csv + convert_registry --to-json --merge-existing" —
that promise does not work. (ONBOARDING's flow via the FULL registry CSV does
work; the broken instruction is the provenance.csv-specific one.)

**Fix:** pick one — (a) make `build_provenance` emit the CSV with the
ingest-compatible header (`Dataset_name` + all 21 preset columns, provenance
columns carrying the corrections), or (b) add a `--kind provenance` slice
preset (name column `dataset`, six required columns, merge-only) and name
THAT in the marker/appendix/$comment text; then regenerate DATA.md.

### MED-04: Alias-default gaps — peft×probe composition and fraction-less curve/head variants collide with existing output dirs and the resume marker

**File:** `pipeline/run_finetune.py:1075-1082` (save-name resolution),
`:1092-1098` (marker skip)
**Issue:** CONFIRMED by code order. The alias chain is:

```python
if save_model_name:
    model_save_name = save_model_name
elif peft_mode != "none":
    model_save_name = f"{model_name}+{peft_mode}"
elif config_variant == "probe":
    model_save_name = f"{model_name}+probe"
else:
    model_save_name = model_name
```

(a) `--peft lora --config-variant probe` (both flags are independently
legal, nothing refuses the combination) silently drops the `+probe` alias
and writes into `{model}+lora/` — colliding with a plain LoRA cell. Since
completion is signaled by `trainer_state.json` in that dir
(`if os.path.exists(outdir + "trainer_state.json"): continue`), whichever
run finished first silently skips the other: two semantically different runs
(frozen-head+LoRA vs plain LoRA) share a directory and a record chain, and
the frontier would classify both as `method=lora` off the same suffix.
(b) `--config-variant curve` or `head` WITHOUT `--train_fraction` also
falls to the base name (curve deliberately does not alias; head's alias IS
the base name): a curve-cadence or custom-head run then lands in
`{model}/{task}/seed_{s}/`, where an existing full run's marker silently
skips it — or it completes first and the later REAL base run silently skips,
making the leaderboard's "full run" actually a variant-config run. In
frontier terms such a record is classified `method=none` and pollutes the
score_delta reference mean (see verdict above). The documented compositions
all pair a variant with a fraction (frac nesting provides the isolation),
but no guard enforces that.

**Fix:** compose aliases (`f"{model_name}+{peft_mode}+probe"` when both
apply, or refuse the combination fail-fast at the argv boundary), and either
alias curve runs (`{model}+curve`) or refuse `--config-variant curve`
without `--train_fraction` (and `head` for non-special models) with a
disclosing `[Error]`, matching the probe-guard discipline.

## Low

### LOW-01: ONBOARDING's metric enum omits `r2` — the registry itself uses it for 3 tasks

**File:** `docs/ONBOARDING.md:111-113`
**Issue:** CONFIRMED: the doc says the metric "must be one of the schema's
closed enum: `f1`, `mcc`, `spearmanr`, `AUPRC`", but
`pipeline/datasets_info.json` declares `r2` for the three
`plant-genomic-benchmark__gene_exp.*` tasks (pre-existing divergence between
the D-10 registry and the schema enums — the committed performance JSONs
carry only the 4 enum values). A maintainer following the checklist for a
regression dataset would wrongly conclude `r2` is not allowed.
**Fix:** list `r2` with a note about the registry↔schema divergence, or
resolve the divergence itself.

### LOW-02: README `make data` expected-output block shows a line order that never occurs

**File:** `README.md` (Reproducing the Leaderboard, step 2 expected output)
**Issue:** CONFIRMED: the block places `🎉 All statistical comparisons
generated successfully!` after the provenance lines, but that line is
`script/summarize_comparison.py:619`'s final print and summarize runs FIRST
in the chain (Makefile order: summarize → permutation → provenance → tasks
index). The section's premise is "Each step shows its expected output, so a
failed step is immediately visible" — wrong-order output misattributes
steps. **Fix:** reorder the block to actual execution order.

### LOW-03: RC sidecar name is fixed `cohort.rc.vcf`, not the "input VCF stem" the docstring claims; multi-model runs overwrite it

**File:** `script/zero_shot_vep.py:582` vs `:485-487` (docstring)
**Issue:** CONFIRMED: `_rc_control` writes `output_dir / "cohort.rc.vcf"`
(literal), while `_build_rc_cohort`'s docstring and the module summary claim
the sidecar is "derived from the INPUT VCF stem under the output dir". In a
62-model batch every CLM model's RC pass overwrites the same file (scoring
is synchronous, so reported numbers are unaffected; the on-disk sidecar after
a run is the last model's, under a generic name). **Fix:** either name it
`f"{vcf_stem}.rc.vcf"` per model or fix the docstring; per-model naming also
makes the sidecar auditable.

### LOW-04: `--models` typos in zero_shot_vep are silent

**File:** `script/zero_shot_vep.py:895-901`
**Issue:** an unknown `--models` name matches no registry key, producing 62
`not selected` rows and exit 0 — diverging from the repo's own fail-fast
filter discipline (run_sweep WR-07/T-05-09 refuses unknown filter names). A
partial typo in a multi-model list is invisible in the artifact.
**Fix:** validate the filter against registry keys and exit non-zero listing
unknown names (skip-as-data can keep the not-selected rows for known names).

### LOW-05: build_provenance marker handling misses the END-without-BEGIN and multi-marker states

**File:** `script/build_provenance.py:226-241`
**Issue:** BEGIN-without-END aborts (good), but END-without-BEGIN silently
falls to the append branch (leaving the stray END marker mid-file plus a new
block), and with two marker pairs `text.index` takes the first BEGIN and the
first END anywhere, garbling on `end < begin`. Only reachable via manual
corruption of DATA.md, but the feature's whole contract is marker safety.
**Fix:** also abort when `END_MARKER in text and BEGIN_MARKER not in text`,
and when either marker occurs more than once.

### LOW-06: "Preprocessing (uniform across all N datasets)" asserted from rows[0] without checking uniformity

**File:** `script/build_provenance.py:160,179-180`
**Issue:** the appendix prints `rows[0]["preprocessing"]` under a uniformity
claim. It holds today (1 distinct value across all 50 rows, verified), but a
future CSV correction introducing a second value would make the appendix
silently assert a falsehood. **Fix:** abort (or disclose per-row) when
`len({r["preprocessing"] for r in rows}) > 1`.

### LOW-07: frontier `_primary_score` collision precedence differs from the exporter's

**File:** `script/build_frontier.py:174-179` vs `script/export_runs.py:599-607`
**Issue:** preference (would be a defect only under key collisions): the
frontier takes the FIRST sorted metric key resolving to the slot; the
exporter's `_collect_cell_values` lets the LAST insertion-order key win the
same slot. Reachable once the new seed_result merge coexists two spellings of
one metric in a record's metrics (e.g. run_record `AUROC` + suite
`eval_AUROC`). **Fix:** share one collision rule (e.g. both prefer the
run-record-produced key) or assert single-key-per-slot.

### LOW-08: `apply_train_fraction` can select zero rows on small tasks

**File:** `pipeline/run_finetune.py:426-428`
**Issue:** `int(n * fraction)` is 0 for small n × tiny f (e.g. n=40, f=0.01)
→ empty train split → crash deep in the suite (recorded as a failed cell)
instead of an argv-boundary refusal. `validate_train_fraction` only bounds
f. **Fix:** after computing the selection size (or at validation time when
the registry Train count is known), refuse with a disclosing error when the
kept-row count would be 0.

### LOW-09: doi_swap's "both-or-neither at the filesystem level" overclaims

**File:** `script/doi_swap.py:220-241`
**Issue:** atomicity holds for PATTERN failures (both rewrites computed
before any write) but not for I/O failure between the two `write_text`
calls; the docstring says "a partial application is impossible by
construction". Two-line window, maintainer-run, low impact — but the claim
should be accurate. **Fix:** write to temp files and rename both, or soften
the docstring to pattern-level atomicity.

## Info

### INFO-01: New blind `except Exception` with `# noqa: BLE001` in script/zero_shot_vep.py

**File:** `script/zero_shot_vep.py:715`
**Issue:** run_sweep.py's failure-boundary docstring states "no blind
`except Exception` is introduced: D-08 forbids noqa outside run_finetune.py's
three designed isolation sites", yet the new VEP driver adds a fourth
noqa'd blind except (row-level isolation). It is disclosed, prints to
stderr, and records the failure as the row's `excluded_reason` — consistent
with the skip-as-data design the plan documents — but the D-08 boundary
statement and the code now disagree about the policy's scope. Preference:
either amend the D-08 statement or scope this except more narrowly over time.

### INFO-02: dry-run cosmetic error line — documented, not re-reported

The `--peft_dry_run` path's trailing "[Error] finetuning ... max() iterable
argument is empty" (run_finetune.py:1379-1381 glob-max on an empty
checkpoint set after the suite's validate-and-exit) is observed, disclosed,
and accepted in 06-01-SUMMARY ("behavior is correct as-is"); per review
scope it is not counted as a finding. If touched for other reasons, skipping
the completion-glob block under dry-run remains the cheap cosmetic fix the
SUMMARY itself noted.

## Verification evidence

- Suite cross-reads at tag v1.2.1 (read-only, `/home/forrest/Github/DNALLM`,
  `git status --porcelain` clean): trainer ctor/train dry-run branches;
  model.py special-loader dispatch + all native family lists; configs.py
  HeadConfig.frozen; sweep.py seed_result writer; vep.py record/label
  semantics and whitelist tokens; pyproject dependency strings.
- Registry×suite dispatch derivation (scripted): 9 registry models claimed by
  a special loader; PROBE_INELIGIBLE covers 8 — the omission is HI-01.
- Empirical reproductions: from-failures alias rejection (MED-01);
  provenance.csv ingest abort (MED-03); probe-guard pass on `SPACE` (HI-01);
  `sha256sum -c` in baseline/snapshots (all 58 files OK).
- Gates: `make lint` clean; `ty check` clean; node lane 18/18; targeted
  pytest (phase-6 files) 324 passed; `make data` + `git status --porcelain
  dnallm-mark/data/ DATA.md` → empty (drift invariant holds).
- The 17 ruff findings under a broad `ruff check tests/ script/ pipeline/`
  are all in the deprecated `pipeline/dnallmmark_pipeline.py`, which is
  deliberately outside the lint gate (pre-existing, unchanged this phase).

---

_Reviewed: 2026-10-11_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_

## REVIEW COMPLETE
