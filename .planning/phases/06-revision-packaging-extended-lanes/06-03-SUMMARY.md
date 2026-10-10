---
phase: 06-revision-packaging-extended-lanes
plan: 03
subsystem: vep-lane
tags: [zero-shot-vep, clinvar, registry-driver, lazy-import, sanity-checks, gb10-smoke, rev-08]
requires:
  - "dnallm 1.2.1 in .venv (tag-archive install, 06-01) + [gpu] groups + peft 0.21.2"
  - "pipeline/models/plant-dnabert-6mer (06-01 fetch)"
provides:
  - "script/zero_shot_vep.py — the registry batch VEP driver (62-row enumeration, injectable scorer seam, sanity + RC channels, dual emission)"
  - "schemas/vep_zero_shot.json — the strict row contract with the full convention/cohort/sanity disclosure"
  - "tests/fixtures/vep_zero_shot/ — our own synthetic ClinVar-shaped cohort + reference + chain-produced expectation fixture"
  - "tests/test_zero_shot_vep.py — 19 stub-scorer CPU tests incl. the import-boundary source contract"
  - "real-kernel GB10 evidence: both smoke rows schema-valid with surfaced skip fractions, sanity verdicts, and the CLM RC control"
affects:
  - "06-04 (Makefile lint-list extension picks up script/zero_shot_vep.py)"
  - "06-05 (response-letter packaging cites this plan's smoke verdicts incl. the honest sanity FAILs)"
tech-stack:
  added: []
  patterns:
    - "lazy suite-kernel import behind an injectable per-model scorer seam (CPU tests drive real enumeration/emission with a stub double)"
    - "codon-translation consequence classification as a synthetic-cohort-scoped sanity convention (disclosed; real cohorts need transcript annotation)"
key-files:
  created:
    - script/zero_shot_vep.py
    - schemas/vep_zero_shot.json
    - tests/test_zero_shot_vep.py
    - tests/fixtures/vep_zero_shot/cohort.vcf
    - tests/fixtures/vep_zero_shot/reference.json
    - tests/fixtures/vep_zero_shot/expected_stub_rows.json
  modified: []
decisions:
  - "sanity classes derive from frame-0 +strand codon translation of the synthetic contig instead of a parallel annotation file — derived, not asserted (a test pins every fixture variant's hand-derived class); disclosed as synthetic-cohort-scoped in the schema $comment"
  - "model source resolution lives INSIDE the default scorer (GPU-path concern): the registry's one unfetchable CLM row (PlantDNAMamba2-BPE — Model_path absent locally, hf/modelscope columns empty) surfaces as a loud evaluation-failed row at GPU time, keeping the enumeration split purely type-driven (50/12) as the acceptance demands"
  - "--models keeps all 62 rows: non-selected MLM/CLM rows carry a not-selected reason (skip-as-data universal); DL/EMPTY reasons take precedence"
  - "RC control = a second full evaluate_vcf pass over the reverse-complemented cohort (RC VCF sidecar derived from the input stem under --output-dir); asymmetry = |auroc_forward - auroc_rc|"
  - "registry hygiene flagged for the maintainer: Tokenizer column 6mer (6 rows) vs 6-mer (1 row) normalized at read time, registry never rewritten"
  - "REV-08 NOT marked complete: it spans 06-01/02/03/05; the final carrier (06-05) owns the mark (06-01 precedent)"
metrics:
  duration: "12 min"
  completed: "2026-10-11"
estimate_provenance: "plan estimate: 55000 tokens / 3 tasks"
actuals:
  tokens: 19868    # chars/4 over git diff 539813b..HEAD (79471 chars)
  tasks: 3
  commits: 2       # MEASURED: git rev-list --count 539813b..HEAD
plan_head_before: 539813b0b4ac28535f265b00377b929b86efa61b
plan_head_after: 527167599b3b160810b38137d612f1100372d47d
status: complete
coverage:
  - deliverable: "driver core — lazy kernel seam, enumeration, exclusions, sanity, RC, dual emission"
    verification:
      - kind: command
        ref: "uv run --group dev python -c 'import zero_shot_vep' (cpu-import-ok); ruff check script/zero_shot_vep.py clean; ty check clean; --help usage OK"
        status: pass
      - kind: tests
        ref: "tests/test_zero_shot_vep.py#test_source_contract_no_module_level_gpu_imports,test_full_registry_enumeration_counts,test_synthetic_slice_rows_and_exclusion_reasons,test_missing_type_column_yields_empty_exclusion,test_models_filter_discloses_not_selected,test_evaluated_row_carries_suite_accounting,test_scorer_failure_is_a_loud_row_level_exclusion"
        status: pass
    human_judgment: false
  - deliverable: "sanity layer (synonym-vs-nonsense medians + bidirectional pass flag)"
    verification:
      - kind: tests
        ref: "tests/test_zero_shot_vep.py#test_genetic_code_spot_checks,test_revcomp,test_fixture_variant_classifications,test_fixture_label_class_coherence,test_sanity_flag_true_and_flips_with_stub_ordering"
        status: pass
    human_judgment: false
  - deliverable: "rc_control CLM-only with real asymmetry arithmetic"
    verification:
      - kind: tests
        ref: "tests/test_zero_shot_vep.py#test_rc_control_clm_only_with_asymmetry"
        status: pass
    human_judgment: false
  - deliverable: "schema + fixtures + determinism + publication gate"
    verification:
      - kind: tests
        ref: "tests/test_zero_shot_vep.py#test_two_runs_emit_byte_identical_artifacts,test_emission_validates_schema,test_committed_fixture_validates_schema,test_committed_fixture_is_chain_product,test_reference_fixture_is_a_plain_chromosome_mapping,test_no_committed_data_artifact"
        status: pass
      - kind: command
        ref: "make test (368 passed + node lane), make lint, make typecheck; make data no-op + dnallm-mark/data/vep_zero_shot.json absent"
        status: pass
    human_judgment: false
  - deliverable: "bounded GB10 smoke — real kernels, one MLM + one CLM over the synthetic cohort"
    verification:
      - kind: command
        ref: "smoke-shape-ok assertion block (paradigms, auroc/auprc in [0,1], rc null/non-null, skip_fraction < 1, sanity present) + emitted JSON validates schemas/vep_zero_shot.json with 0 errors + suite repo porcelain empty"
        status: pass
    human_judgment: false
---

# Phase 06 Plan 03: Zero-shot VEP registry batch driver Summary

**One-liner:** Registry batch driver over the suite's tested VEP kernels (lazy `dnallm.inference.vep` import behind an injectable scorer seam) emitting always-62 disclosure rows with synonym-vs-nonsense sanity and a CLM-only reverse-complement control — CPU-proven through a 19-test stub suite plus a real-kernel GB10 smoke whose honest sanity verdicts are FAILs, recorded as findings.

## What Was Built

### Task 1 — the driver core (commit ff922c5)

`script/zero_shot_vep.py` per the audit_n_frequencies/export_runs conventions (module banner: Purpose / Direction-of-truth / Usage; `REPO_ROOT = Path(__file__).resolve().parents[1]`; argparse `--registry/--vcf/--reference/--output-dir/--models`):

- **Lazy kernel seam**: `from dnallm.inference.vep import evaluate_vcf` (plus `TaskConfig` / `load_model_and_tokenizer`) lives ONLY inside `_suite_scorer` — the module imports cleanly in the torch-free dev env (executed proof: the test module imports it). Model loading follows the suite CLI's own idiom (dnallm/cli/vep.py @ v1.2.1): paradigm → task type `generation`/`mask` → `TaskConfig` → `load_model_and_tokenizer(source=...)`, the pairing the suite's paradigm-architecture guard then verifies. A GPU-path model cache lets the RC pass reuse the loaded backbone.
- **Enumeration**: every `models_info` entry exactly once, sorted; `type` column drives paradigm (MLM 32 → mlm, CLM 18 → clm); DL 5 + EMPTY 7 (and any unknown/missing type defensively) become excluded-with-reason rows — 62 rows ALWAYS. `--models` selects what gets EVALUATED; non-selected rows carry a not-selected reason (never dropped).
- **Sanity layer**: median paradigm delta over the cohort's synonymous vs nonsense variants (classification by frame-0 +strand codon translation from contig offset 0 — a disclosed synthetic-cohort convention); `pass = nonsense_median < synonymous_median` under alt-minus-ref; null when either median is missing.
- **RC control** (CLM rows only): the forward records + reference are transformed into a reverse-complemented cohort VCF (sidecar path derived from the input stem under `--output-dir`, never from record fields) and re-scored through the same seam; reports `auroc_forward`, `auroc_rc`, `asymmetry = |fwd - rc|`. Null on MLM rows.
- **Emission**: deterministic dual `vep_zero_shot.json` (indent 4, sort_keys, no clock) + `vep_zero_shot.csv` (fixed 12-column order; nested objects as sorted compact JSON cells). Registry `6mer`/`6-mer` Tokenizer spelling normalized at read time (data-hygiene note in the banner; registry never rewritten); context-window policy bucketed on the normalized type (all at the suite default 200 today — the single documented place to tighten post-E2').
- **Row-level failure isolation**: any per-model exception (paradigm guard, model load, cohort contract) becomes that model's `excluded_reason = "evaluation failed: ..."` row plus a loud stderr line; siblings continue.

### Task 2 — schema + fixtures + the CPU suite (commit 5271675, TDD: RED run confirmed on missing fixtures first)

- `schemas/vep_zero_shot.json`: strict draft-2020-12, every field typed, `additionalProperties: false` throughout; the `$comment` discloses the conventions (alt-minus-ref, deleterious negative, AUROC/AUPRC over `-delta`), the D-17 cohort rules (SNVs only; strict P/LP vs B/LB whitelist; ≥1 review star; VUS/conflicting excluded), the sanity codon-frame convention, RC CLM-only semantics, and the evaluation-failure semantics. Two ENFORCED conditionals: an `excluded_reason` string ⇒ null metric fields; `paradigm: mlm` ⇒ null `rc_control`.
- `tests/fixtures/vep_zero_shot/cohort.vcf` + `reference.json`: authored fresh by hand (suite fixtures were read-only SHAPE references only — never copied). The chrV contig is codon-designed (14 codons, frame 0) so every variant's class is hand-derivable: 5 nonsense (P/LP-labeled) + 4 synonymous (Benign-labeled) SNVs, missense rows, one 4-ALT row exercising `alt_number=4` handling (one alt length-changing → the skip channel), plus VUS / no-star / non-SNV exclusion rows.
- `expected_stub_rows.json`: CHAIN-PRODUCED by running the driver with the stub over the slice + fixtures (byte-copied; the chain-product test re-proves it).
- `tests/test_zero_shot_vep.py`: 19 tests — source-contract AST walk (no module-level dnallm/torch/peft/allel import AND the lazy `dnallm.inference.vep` import exists inside a function), genetic-code/revcomp spot checks, per-variant hand-derived classification table, label↔class coherence, 62/50/32/18/5/7 full-registry counts, DL/EMPTY/missing-type/not-selected exclusion discipline, suite-accounting surfacing (12/1/1÷13), sanity flip in both polarities, rc CLM-only with real asymmetry, scorer-failure row isolation, byte determinism, schema validation (slice emission + full-registry emission + committed fixture), chain-product equality, publication gate.
- The stub double parses ONLY this repo's committed trusted fixture VCF (the product path's untrusted-data discipline is untouched — the suite's scikit-allel reader does all real cohort parsing) and mirrors the suite's convention-filter order and accounting vocabulary; its AUROC is a pairwise Mann-Whitney with AUPRC as a documented placeholder (the product path's metrics come from the suite metric registry).

### Task 3 — bounded GB10 smoke (evidence-only: no production delta; fetched model is gitignored, smoke artifacts live in /tmp)

(a) Fetched `plant-dnagpt-BPE` (the registry's CLM row; GPT2LMHeadModel, model_type gpt2) from `zhangtaolab/plant-dnagpt-BPE` into a fresh `pipeline/models/plant-dnagpt-BPE/` (11 files, model.safetensors 368MB) — the second and final sanctioned fetch of this lane. (b) Ran the driver over the committed synthetic cohort with the REAL kernels, restricted to the two models. (c) All smoke-contract assertions passed: both rows evaluated, auroc/auprc in [0,1], skip fractions < 1, rc_control null on the MLM row and populated on the CLM row, sanity fields present, emitted JSON validates the schema with 0 errors. (d) **Honest findings: BOTH models FAIL the synthetic-cohort sanity bar** (below) — recorded, not tuned away; the cohort was authored for hand-derivable classes, not for passing. (e) Suite repo porcelain empty at every checkpoint.

## Verbatim Evidence

### The GB10 smoke (uv run --group gpu python script/zero_shot_vep.py --vcf tests/fixtures/vep_zero_shot/cohort.vcf --reference tests/fixtures/vep_zero_shot/reference.json --models plant-dnabert-6mer,plant-dnagpt-BPE --output-dir /tmp/06-03-vep-smoke) — exit 0

```text
[zero_shot_vep] plant-dnabert-6mer: paradigm=mlm evaluated=12 skipped=1 skip_fraction=0.0769 auroc=0.4571 auprc=0.5923 sanity_pass=false
[zero_shot_vep] plant-dnagpt-BPE: paradigm=clm evaluated=6 skipped=7 skip_fraction=0.5385 auroc=0.3333 auprc=0.6333 sanity_pass=false
[zero_shot_vep] 62 rows (2 evaluated, 60 excluded-with-reason) -> /tmp/06-03-vep-smoke/vep_zero_shot.json
```

Full per-model rows (from the schema-valid emission; `/tmp/06-03-vep-smoke/vep_zero_shot.json`):

```text
plant-dnabert-6mer (mlm, 6mer):  evaluated=12 skipped=1 skip_fraction=0.0769
  auroc=0.4571  auprc=0.5923
  sanity: synonymous_median=-0.2024  nonsense_median=-0.0864  pass=false
  rc_control: null
plant-dnagpt-BPE (clm, BPE):     evaluated=6 skipped=7 skip_fraction=0.5385
  auroc=0.3333  auprc=0.6333
  sanity: synonymous_median=-0.5369  nonsense_median=-0.1246  pass=false
  rc_control: auroc_forward=0.3333  auroc_rc=0.6667  asymmetry=0.3333
```

Both rows share the suite's convention block verbatim (rows_read=13; exclusion_counts {non_snv_clnvc:1, unlabeled_clnsig:1, below_star_floor:1}; labels `['Likely_pathogenic', 'Pathogenic']=1 vs ['Benign', 'Likely_benign']=0`). The RC sidecar `cohort.rc.vcf` round-trips all 13 forward records.

### Honest-FAIL findings (the plan's provision (d), verbatim verdicts)

1. **plant-dnabert-6mer fails the synonym-vs-nonsense expectation**: nonsense median (-0.0864) is LESS deleterious than the synonymous median (-0.2024) on this synthetic cohort; AUROC 0.4571 sits below the random floor's discriminating side.
2. **plant-dnagpt-BPE fails it too** (nonsense -0.1246 vs synonymous -0.5369) with AUROC 0.3333 — and its BPE tokenizer skips 7/13 records as multi-slot token differences (skip_fraction 0.5385), the k-mer/multi-token alignment cost the same-slot rule discloses as data.
3. **RC strand asymmetry is real on the CLM**: the reverse-complemented cohort scores HIGHER (0.6667) than forward (0.3333), asymmetry 0.3333 — exactly the causal-strand phenomenon the control exists to disclose (PlantCAD2/evo literature).

Interpretation for the response letter (06-05): a 42bp synthetic contig with 9 classifiable variants is far below the cohort scale these models discriminate on; the machinery's job was to REPORT verdicts honestly, and a recorded sanity FAIL on a tiny synthetic cohort is compliant behavior — masking one would not be. Real-cohort verdicts wait for post-E2' runs over ClinVar-scale data (the publication gate stays closed).

## Commits

| Task | Commit | Subject |
| --- | ------ | ------- |
| 1 | ff922c5 | feat(06-03): zero-shot VEP registry batch driver — lazy kernel seam, 62-row enumeration, sanity + RC control, dual emission |
| 2 | 5271675 | test(06-03): VEP schema + synthetic cohort fixtures + stub-scorer CPU suite |
| 3 | (none — evidence-only) | smoke artifacts in /tmp, fetched model gitignored; evidence recorded here |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] scorer-seam altitude: source resolution ran before the seam, breaking the type-driven 50/12 split**
- **Found during:** Task 1 acceptance scratch run (49/13 instead of 50/12)
- **Issue:** `_resolve_model_source` executed in `build_rows` before calling the scorer, so the registry's one unfetchable CLM row (`PlantDNAMamba2-BPE`: `Model_path` directory absent AND empty huggingface/modelscope columns) became an enumeration-time exclusion under the stub — the split was registry-content-driven, not type-driven.
- **Fix:** moved source resolution INSIDE `_suite_scorer` (a GPU-path concern); `ScoringRequest` now carries the registry row. Enumeration marks a row evaluated iff type ∈ {MLM, CLM}; unfetchable models surface at GPU time as loud `evaluation failed:` rows — the correct contract.
- **Files modified:** script/zero_shot_vep.py
- **Commit:** ff922c5 (folded in before the Task 1 commit)

### Interpretations (no plan contract changed)

**2. Sanity classes are DERIVED by codon translation, not carried in a parallel annotation file.** The plan requires "median delta over the cohort's synonymous vs nonsense variants" without pinning the class source. A fourth fixture file (or an envelope reference.json) would assert classes; deriving them (frame 0, +strand, contig offset 0) makes them checkable from first principles — a test pins every fixture variant's hand-derived class, and no VCF re-parsing enters the driver (the suite result records + the mapping are enough). Disclosed as synthetic-cohort-scoped in the schema `$comment`; real-cohort consequence classes require transcript annotation (post-E2' work).

**3. `--models` emits all 62 rows** (non-selected → not-selected reason) rather than filtering emission — the plan's "the output always carries 62 rows" truth read universally; the smoke's verify block picks the two models from the full row set either way.

**4. Task-3 commit is evidence-only.** The plan's `<files>` for Task 3 lists `script/zero_shot_vep.py`, but the smoke required no code change (all gates passed first run). The fetched model is gitignored by design and smoke outputs live in `/tmp` per the verify block — there is no production delta to commit; the evidence lands in this SUMMARY (atomic close-out: production commits → SUMMARY).

**5. TDD scope per task followed the plan's own file ownership:** Task 1's `tdd` flag targets a script whose test module belongs to Task 2 (the plan's Task 2 action says "write tests FIRST"); Task 2 executed the literal RED→GREEN cycle (RED confirmed on missing fixtures), and Task 1's acceptance criteria were validated by a scratch stub run before commit.

## Verification Results

- `uv run --group dev python -c "import zero_shot_vep"`: cpu-import-ok
- `ruff check script/zero_shot_vep.py`: clean (4 initial findings fixed: 3× ISC004 parenthesized concatenation, 1× TRY004 ValueError→TypeError per the 06-01 house convention)
- `ty check`: All checks passed (no widened suppressions, no config change)
- `python script/zero_shot_vep.py --help`: usage text, exit 0
- `pytest tests/test_zero_shot_vep.py -v`: **19 passed**
- `make test`: **368 passed** (was 349; +19) + node lane green
- `make lint` / `make typecheck`: clean
- `make data` + porcelain on dnallm-mark/data/: no-op; `dnallm-mark/data/vep_zero_shot.json` absent (publication gate holds)
- Task 3 verify block 1 (smoke-shape-ok): PASS; emitted JSON validates `schemas/vep_zero_shot.json` with 0 errors
- Task 3 verify block 2 (suite repo porcelain empty + no committed artifact): PASS
- Final suite-repo state: `git -C /home/forrest/Github/DNALLM status --porcelain` EMPTY; venv-installed dnallm byte-identical to the suite working tree (`sha256` match, which matches tag v1.2.1 content per 06-01's empty-diff verification)

## Test Coverage

All 19 tests in `tests/test_zero_shot_vep.py` enumerated: source contract (AST module-level import ban + lazy seam presence), genetic code + revcomp primitives, fixture classification table + label/class coherence, full-registry counts (62/50/32/18/5/7) + uniqueness, slice rows + DL/EMPTY reasons + 6-mer normalization, missing-type exclusion, `--models` disclosure, suite accounting (evaluated/skipped/skip_fraction/metrics/9-key convention), sanity both polarities, rc CLM-only + sidecar, scorer-failure row isolation, byte determinism (JSON + CSV), schema validation ×3 (slice, full registry, committed fixture), chain-product equality, plain-mapping reference, publication gate (no artifact + no SCHEMA_FILES registration). GPU-side proof is the executed smoke itself — by design never in `make test`/CI.

## Known Stubs

None. (The stub scorer is a test double inside the test module, not a product stub; the driver's product path is the real suite kernels.)

## Self-Check: PASSED

All six created files exist on disk; both commits (ff922c5, 5271675) verified as ancestors of HEAD; commits measured at 2 via `git rev-list --count 539813b..HEAD` (matches the frontmatter `actuals.commits`); Task 3 evidence artifacts verified present under /tmp/06-03-vep-smoke and the suite repo porcelain-empty.
