---
phase: 06-revision-packaging-extended-lanes
fixed_at: 2026-10-11T01:21:37Z
review_path: .planning/phases/06-revision-packaging-extended-lanes/06-REVIEW.md
review_commit: ab3540f
iteration: 1
findings_in_scope: 14
fixed: 14
skipped: 0
status: all_fixed
---

# Phase 06: Code Review Fix Report

**Fixed at:** 2026-10-11T01:21:37Z
**Source review:** `.planning/phases/06-revision-packaging-extended-lanes/06-REVIEW.md` (commit ab3540f)
**Iteration:** 1
**Mode:** sequential, MAIN tree, ISOLATION=none (per the invoking directive; `workflow.use_worktrees` bypassed by explicit orchestrator instruction)

**Summary:**
- Findings in scope: 14 (1 high + 4 medium + 9 low — the actionable tiers)
- Fixed: 14 (each an atomic `{type}(06-review): ...` commit, no co-author lines)
- Skipped: 0
- Info findings (2): INFO-01, INFO-02 — info-open by the disposition directive, recorded in `06-REVIEW-DISPOSITION.md` (all 16 findings covered there)

**Where verification ran:** the MAIN checkout (`/home/forrest/Github/dnallmmark`, branch `autorun`) — every gate below is reproducible from this tree as committed.

## Fixed Issues

### HI-01: PROBE_INELIGIBLE omits the registry's `SPACE` row

**Files modified:** `pipeline/run_finetune.py`, `tests/test_run_finetune_contracts.py`
**Commit:** d894de4
**Applied fix:** Added `"SPACE"` (the uppercase registry row, `models/SPACE` — claimed by the suite's native `space_models = ["SPACE"]` member case-sensitively) beside the existing lowercase `"space"` (claimed via the `extra` self-append), each with a provenance comment naming the dispatch. The pinning test now (a) pins the 9-member set, (b) asserts both spellings against the registry, and (c) derives a **case-closure invariant from the registry itself**: any key group differing only by case must be all-in or all-out of the list (substring dispatch routes the group to the same special loader), so a future registry case-split cannot silently reopen the hole. A new guard-simulation test exec-extracts the list and runs the guard's exact membership expression over both spellings and every other special-loader family. Suite dispatch verified read-only at `v1.2.1` in `/home/forrest/Github/DNALLM` (`special/space.py` substring loop; `model.py:1207-1215` extra self-append).

### MED-01: `--from-failures` cannot recover a `--peft` sweep

**Files modified:** `pipeline/run_sweep.py`, `tests/test_sweep.py`
**Commit:** cb168cc
**Applied fix:** Every `sweep_failures.json` entry now records `"base_model"` (the registry name) beside the alias cell identity (`"model"`). `load_failure_pairs` validates and joins on base names — `base_model` when present, else a known-suffix (`+lora`/`+ia3`) strip of `model` mirroring `build_argv` (legacy alias-only manifests recover too; a name still unknown after the strip fails loudly). `main()`'s cell filter strips the re-run's `--peft` alias before matching, so feeding a peft sweep's own manifest back **with the same `--peft` mode re-enumerates exactly the failed alias cells across every requested seed**; without `--peft` it enumerates the base cells. The alias→base strip now lives in one helper (`base_model_name`) shared by `build_argv`, the three failure writers, and the filter. Tests pin: alias+base_model in the manifest, the exact re-enumeration, legacy-strip recovery + still-unknown refusal, and the non-string `base_model` guard.

### MED-02: env_smoke 1.2.1 relabel wrong on the datasets cap

**Files modified:** `pipeline/env_smoke.py`, `tests/test_run_finetune_contracts.py`
**Commit:** c2fa732
**Applied fix:** All three sites (check-6 docstring, diagnostics docstring, INFO print line) corrected from `datasets<=3.2.0` to `datasets<=5.1.0` — re-verified read-only against `git show v1.2.1:pyproject.toml` (`"datasets<=5.1.0"`; also reconfirmed `numpy>=2.0.0`, `peft>=0.14.0`, no pyarrow constraint). The pinning test now forbids the stale figure and asserts the corrected label. `env_smoke.py` was never imported/executed (py_compile only, per the phase constraints).

### MED-03: The documented provenance correction path aborts

**Files modified:** `script/convert_registry.py`, `script/build_provenance.py`, `schemas/provenance.json`, `DATA.md`, `tests/test_convert_registry.py`, `tests/test_build_provenance.py`
**Commit:** 360a28e
**Applied fix:** Canonical contract chosen: a dedicated **`--kind provenance` slice preset** — name column `dataset`, six required provenance columns, no numeric coercion, `merge_only` discipline (requires `--merge-existing`; refuses rows naming datasets absent from the merge registry, so a correction can never add a skeletal entry) — and the merged name lands under the registry's own `Dataset_name` field (D-10 `key == name field`), so no redundant `dataset` field pollutes entries. All four instruction sites (emitter docstring, BEGIN marker, appendix body, schema `$comment`) now name the working command; DATA.md regenerated through the emitter itself. DATA.md/schema wording was NOT bent to the broken behavior.

**The fixed documented round-trip (now works from the emitted provenance.csv as-is):**

1. Edit a cell in `dnallm-mark/data/provenance.csv` (the emitted 7-column CSV: `dataset` + the six provenance fields).
2. Ingest:
   ```
   python script/convert_registry.py --kind provenance --to-json \
       --input dnallm-mark/data/provenance.csv \
       --output pipeline/datasets_info.json \
       --merge-existing pipeline/datasets_info.json
   ```
   (expected output: `✅ ... : 0 entries added, 50 merged, 0 renamed, 0 derived, 50 total`)
3. Re-run `make data` — provenance.{json,csv} and the DATA.md appendix regenerate with the correction.

Empirically verified end-to-end on scratch copies before pinning: exactly the corrected entry changes, all other entries byte-identical, `Dataset_name == key` preserved, no `dataset` field added; the three refusal guards (partial header naming the 7-column set, missing `--merge-existing`, unknown dataset row) all exit 1 with named errors. Pinned by `test_documented_correction_round_trip_over_the_real_registry` (emit → edit → ingest via the exact CLI flag surface → no abort → re-emit carries the correction into every artifact).

### MED-04: Alias-default/resume-marker collision gaps

**Files modified:** `pipeline/run_finetune.py`, `tests/test_run_finetune_contracts.py`
**Commit:** 5be6627
**Applied fix:**
(a) `--config-variant probe` now **refuses** `--peft lora/ia3` at the argv boundary with a named `[Error]` (frozen-backbone probes vs adapters-on-frozen is a different experiment; the peft-first save-name chain would have silently dropped the `+probe` alias and collided with the plain adapter cell's dir and resume marker). The guard sits before the model loop and before the probe-ineligibility guard.
(b) Curve runs alias to `{model}+curve`, and `--config-variant head` aliases to `{model}+head` for GENERIC models only — a variant run no longer lands under the BASE name where a full run's `trainer_state.json` marker silently skips it (or vice versa, publishing a variant-config run as the full result and polluting the frontier's `method=none` reference mean). The special_models pair (`evo2_1b_base`, `megaDNA_updated`) is exempt from `+head`: their with-head config IS their base config, so an explicit head run on them keeps the base name (byte-identical to the implicit behavior). Default paths (peft=none, no variant, no fraction) remain byte-identical — the chain still ends at the bare base name. Residual, disclosed: `--peft` × curve/head without `--train_fraction` still resolves to the peft alias (the documented composition pairs variants with fractions, whose `frac_` nesting isolates them; the base-name collision the finding described is closed — noted in the disposition).

### LOW-01: ONBOARDING metric enum omits `r2`

**Files modified:** `docs/ONBOARDING.md`
**Commit:** 5020553
**Applied fix:** The checklist now lists `r2` with the registry↔schema divergence note (the three `plant-genomic-benchmark__gene_exp.*` tasks declare it; the committed performance JSONs and schema enums carry the four canonical values).

### LOW-02: README `make data` expected-output ordering

**Files modified:** `README.md`
**Commit:** 27f36c5
**Applied fix:** The 🎉 summarize-final line moved to directly after the manifest line — the block now matches the Makefile execution order (summarize → permutation → provenance → tasks index).

### LOW-03: RC sidecar fixed name overwritten per model

**Files modified:** `script/zero_shot_vep.py`, `tests/test_zero_shot_vep.py`
**Commit:** e329c77
**Applied fix:** The sidecar is now `{model}.rc.vcf` — one per model, auditable against its row; the false "derived from the input VCF stem" docstring claim replaced with the real naming rule. Scoring was already synchronous, so reported numbers are unchanged.

### LOW-04: `--models` typos silent in the VEP driver

**Files modified:** `script/zero_shot_vep.py`, `tests/test_zero_shot_vep.py`
**Commit:** 9e07c98
**Applied fix:** `run_zero_shot_vep` validates the filter against the registry keys and exits non-zero listing every unknown name (the run_sweep WR-07 discipline); known unselected names keep their skip-as-data not-selected rows.

### LOW-05: marker handling misses END-without-BEGIN and multi-marker states

**Files modified:** `script/build_provenance.py`, `tests/test_build_provenance.py`
**Commit:** 6247abb
**Applied fix:** `apply_data_md` aborts loudly on all four malformed states: BEGIN-without-END, END-without-BEGIN (previously fell through to append), more than one occurrence of either marker, and an END preceding its BEGIN (previously garbled slice math).

### LOW-06: "uniform preprocessing" asserted from rows[0] without checking

**Files modified:** `script/build_provenance.py`, `tests/test_build_provenance.py`
**Commit:** b4cb8c9
**Applied fix:** `render_block` aborts when the rows carry more than one distinct `preprocessing` value — the appendix can never silently assert the uniformity falsehood.

### LOW-07: frontier `_primary_score` collision precedence differs from the exporter's

**Files modified:** `script/build_frontier.py`, `tests/test_frontier.py`
**Commit:** 7bb887e
**Applied fix:** `_primary_score` now iterates insertion order and keeps the LAST finite key resolving to the slot — exactly `export_runs._collect_cell_values`' rule — so two spellings of one metric yield the same number on both surfaces. Pinned by a parity test running both resolvers over the same colliding metrics (single-key behavior identical).

### LOW-08: `apply_train_fraction` can select zero rows

**Files modified:** `pipeline/run_finetune.py`, `tests/test_run_finetune_contracts.py`
**Commit:** bf2cd39
**Applied fix:** New pure resolver `zero_selection_tasks(datasets_info, fraction, target_dataset)` derives the zero-selection set from the registry's on-disk `Train` counts (comma-separated target scoping matching the dataset loop; falsy-Train tasks out of scope); the `__main__` wiring exits with a disclosing `[Error]` naming every zeroed task before the model loop. Guarded on a given fraction — the default path is byte-identical. A regression assertion also confirms the real registry stays clean at the documented curve fractions (0.25/0.5/1.0).

### LOW-09: doi_swap "both-or-neither at the filesystem level" overclaims

**Files modified:** `script/doi_swap.py`
**Commit:** 7bfa5df
**Applied fix:** Wording scoped to the truth: both-or-neither at the PATTERN level (a missing pattern aborts before any write); an I/O failure between the two `write_text` calls can still leave the first file applied — loudly (a re-run aborts on the missing pattern). Wording fix chosen over temp-file+rename churn for the two-line, maintainer-run window.

## Verification evidence (final gates, MAIN checkout)

- `make test`: **451 passed** (431 baseline + 20 new tests from these fixes), node lane **18/18** — zero failures.
- `make lint` (ruff over tests/ + all phase-authored files): **All checks passed** — no new suppressions, no widened noqa.
- `make typecheck` (`ty check`): **All checks passed**.
- Drift gate: `make data` re-run → `git status --porcelain dnallm-mark/data/ DATA.md` empty (byte-stable no-op; DATA.md's regenerated instruction lines committed with MED-03).
- Hard constraints honored: `run_finetune` NEVER executed; `run_sweep` exercised only via its CPU-testable functions and `--dry-run` in tests; `env_smoke.py` never imported/executed (py_compile only); `/home/forrest/Github/DNALLM` touched read-only (`git show v1.2.1:...` verifications only); no tags, no installs; default paths regression-pinned byte-identical by the updated chain tests.
- Working tree clean after the final commit; no partial or uncommitted changes.

---

_Fixed: 2026-10-11T01:21:37Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
