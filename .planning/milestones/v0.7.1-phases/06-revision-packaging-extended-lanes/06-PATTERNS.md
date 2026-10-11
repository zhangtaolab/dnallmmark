# Phase 6: Revision Packaging & Extended Lanes - Pattern Map

**Mapped:** 2026-10-11
**Files analyzed:** 13 surfaces (new + modified, incl. greenfield scripts/docs)
**Analogs found:** 12 / 13 (1 partial-greenfield: docs/ architecture — DATA.md/README conventions exist, no docs/ dir)

> All analog paths are git-tracked repo source (verified via `git ls-files`
> at HEAD 66cee65; none live under a gitignored mirror). Suite-side anchors
> (`/home/forrest/Github/DNALLM/...`) are read-only reference targets at tag
> `v1.2.1` — they are REUSE targets, never edit targets.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `pipeline/run_finetune.py` (EDIT — `--peft`, `--frozen-probe`/config-variant, `--train_fraction`, trainable-params persistence) | service (pipeline) | batch | itself; the `--subset_file` seam (flag + pure validator `validate_subset_file` + injectable application between load and validate) | exact |
| `pipeline/finetune_config.yaml` (+ `finetune_config_with_head.yaml`, + new probe/curve variant YAMLs) | config | — | itself; `special_models` reload seam at `run_finetune.py:630-632` | exact |
| `pipeline/run_sweep.py` (EDIT — `--peft`/`--curve` matrix expansion, record fields) | service (sweep driver) | batch | itself; `--priority-file` tier composition (`load_priority_tiers` :383 / `apply_priority_order` :479) + `_validate_filters` :290 | exact |
| `script/export_runs.py` (EDIT — tolerant `seed_result.json` reader) | service (exporter) | batch/transform | itself; `LEGACY_DATASET_METRIC` tolerance :384-412 + `load_run_records` :420-450 | exact |
| `script/zero_shot_vep.py` (NEW — registry batch VEP driver) | service | batch | `script/audit_n_frequencies.py` (registry enumeration + missing/excluded-row disclosure) + `script/export_runs.py` (module banner + REPO_ROOT argparse) | role-match |
| `script/build_provenance.py` (NEW — provenance emitter) | service | batch/transform | `script/audit_n_frequencies.py` (emission trio: DATA.md appendix + CSV + JSON) | role-match |
| `script/convert_registry.py` (EDIT — provenance columns in KIND_PRESETS) | utility | file-I/O | itself; `KIND_PRESETS["datasets"]["columns"]` :84-112 | exact |
| `pipeline/datasets_info.json` (EDIT — ~6 provenance columns) | config (registry) | — | itself; D-10 single-source discipline | exact |
| `script/freeze_snapshot.py` (wire only) + `Makefile` `snapshot:` lane | config | file-I/O | itself (tested primitive, `freeze_snapshot()` :52-103); `baseline/data-v1.sha256` line convention; Makefile lane style | exact |
| `script/doi_swap.py` (NEW — README + .gitleaks.toml same-commit swap) | utility | file-I/O | `script/run_migration_inventory.py` (thin REPO_ROOT orchestrator, `--write-manifest` convention) | role-match |
| `dnallm-mark/js/data.js` (EDIT — delete `recalculateComparison` :232) | component (data layer) | — | prior dead-code removals (04-05 `get_task_performance.py` deletion + pivot assertions folded into exporter tests); node-test proof `tests/js/data-escape.test.js:16` | role-match |
| `pipeline/env_smoke.py` (EDIT — peft check + 1.2.1 labels + sanction amendment) | utility (gate check) | check→exit | itself; checks 1-6 PASS/FAIL structure (env_smoke.py:368-404) | exact |
| Frontier/VEP/provenance schemas (`schemas/frontier.json` etc.) + `tests/test_schemas.py` buckets + `tests/test_frontier.py` | test/contract | batch | `schemas/permutation_tests.json` ($comment disclosure style) + `SCHEMA_FILES` bucket `tests/test_schemas.py:25-58` + `tests/test_export_runs.py::_build_fixture_tree` | exact |
| `docs/METHODOLOGY.md`, `docs/ONBOARDING.md`, README reproduction section | docs | — | `DATA.md` generated-appendix conventions (:3-7 header stamp, :41-53 missing-row disclosure); README badge/Quick-Start sections; CI-replay proof `tests/test_ci_replay.py` | role-match (no docs/ dir yet) |

## Pattern Assignments

### 1. `pipeline/run_finetune.py` — peft / probe / train-fraction passthroughs

**Analog:** itself — the `--subset_file` seam is the exact shape for every new flag.

**Flag + pure-validator + injectable-application seam** (`pipeline/run_finetune.py:188, 201-258, 493-509, 943`, condensed discipline):
```python
# parse_args() block (:188):
"--subset_file", ...                       # new: --peft {none,lora,ia3}, --frozen-probe, --train_fraction
# pure module-level validator (:201-258):
def validate_subset_file(subset_path, datasets_info): ...
# driver load + fail-fast (:503-509): collect problems -> sys.exit("[Error] ...")
# application at the dataset seam (:943): "identical code path" when absent
```
Copy this three-stage shape verbatim for `--peft` (choices `[none,lora,ia3]`), `--train_fraction` (float validation: >0, <=1, parse "0.25,0.5" only on the sweep side), and the config-variant reload (generalize the `special_models` → with_head reload at `:630-632` into a `--config-variant` that swaps the YAML for ANY model).

**Ctor passthrough** (`pipeline/run_finetune.py:1027-1032` — the DNATrainer call site):
```python
trainer = DNATrainer(
```
gains `use_lora=(peft_mode == "lora")` here; `configs["finetune"].use_ia3 = True` set in the same per-dataset mutation block that already sets quirk fields (pattern: `configs["finetune"].save_safetensors = False` at `:784-786`). Quirk-list config blocks live at `:552-602` (extend the stale `@ revision 483a35c` inline citations there to v1.2.1 in plan 1).

**Alias isolation** (`pipeline/run_finetune.py:181, 794-800`): reuse `--save_model_name` → `{model}+lora|+ia3|+probe` gives separate output dirs AND separate `trainer_state.json` resume markers with zero layout-code changes. **Trainable-params persistence** (the one frontier producer gap): after ctor, `sum(p.numel() for p in trainer.model.parameters() if p.requires_grad)` → `final_metrics.json` (written at `:1051-1053`).

**CPU proof pattern:** `tests/test_run_finetune_contracts.py:6-10` — "read as SOURCE TEXT and never imported" (ast/regex on the file). Pin: kwarg present at ctor site, `use_ia3` set before ctor, `lora:` section present in the YAML, variant-reload placement. GPU smoke (sanctioned): `finetune.peft_dry_run` validate-and-exit (suite trainer.py:335-344, 451-461) — no training, minutes not hours.

---

### 2. `pipeline/finetune_config*.yaml` — lora:/ia3:/frozen sections

**Analog:** itself + `finetune_config_with_head.yaml` (the existing head_config-carrying variant). Section field surfaces are suite-owned (dnallm configs.py:400-423 LoraConfig, :436-478 Ia3Config, :14-17 `frozen`) — do NOT invent fields. `lora:` section MUST exist whenever `use_lora=True` (suite trainer.py:421 indexes `config["lora"]` directly → KeyError otherwise; `ia3:` is optional). Frozen probe = `finetune_config_with_head.yaml`'s head_config block with `head: "mlp"`, `frozen: true`, small `hidden_dims` (suite model.py:101-103 executes the freeze).

---

### 3. `pipeline/run_sweep.py` — `--curve` / `--peft` matrix extension

**Analog:** itself — the `--priority-file`/`--from-failures` discipline.

**Tier composition over sorted() fallback** (`pipeline/run_sweep.py:479-480` + `:439`): `apply_priority_order(cells, tiers)` stable-reorders over the `sorted(cells)` enumeration — `--curve` fraction expansion and `--peft` variant expansion compose into `enumerate_matrix` (:251) the same way: enumerate base cells, then expand per-fraction/per-variant, keeping `sorted()` determinism (manifests must be byte-stable).

**Collect-all-problems validation** (`_validate_filters`, `pipeline/run_sweep.py:290-335`; `load_priority_tiers` :383-478): every new flag's file/list input validates fail-fast listing ALL problems with `sys.exit("[Error] --curve ...")` — fraction bounds, peft choice legality, registry-join key checks.

**Record + argv** — `build_argv` (:595-616) is LIST-not-string (T-03-10); add `peft` (default `"none"`) and `train_fraction` fields to the run_record written at `:663-682`. **Layout rule (critical):** frac dirs NEST under seed — `{root}/{model}/{task}/seed_{seed}/frac_{f}/` — never sibling (breaks the `trainer_state.json` resume marker and the exporter walk `export_runs.py:438-450`). **Tests:** fake-executor discipline `tests/test_sweep.py` (`run_matrix(cells, output_root, executor=None)` seam, run_sweep.py:702-744).

---

### 4. `script/export_runs.py` — tolerant `seed_result.json` reader

**Analog:** itself — two precedents in the same file.

**Tolerance precedent** (`script/export_runs.py:384-412`, condensed):
```python
LEGACY_DATASET_METRIC: dict[str, str] = { ... }
canonical = LEGACY_DATASET_METRIC.get(metric, metric)
```
**Landing point** — `load_run_records` (:420-450) walks `{model}/{task}/seed_{n}`; the reader (`_read_seed_result(seed_dir)`) checks `seed_result.json` presence there: absent → skip silently; present → merge `data["metrics"]`; **present-but-malformed → loud abort**, matching the run_record abort at `:426-427`. Suite writer shape (accept THIS, not the CONTEXT paraphrase): `{model_name, task_name, seed, timestamp, metrics}` (dnallm sweep.py:314-324). `_collect_cell_values` (:466+) consumes the merged evidence; `total_flos` stays hard-required (:494-499). Tests: extend `tests/test_export_runs.py::_write_run_record` fixtures with optional seed_result files (present/absent/malformed trio).

---

### 5. `script/zero_shot_vep.py` (NEW)

**Analogs:** `script/audit_n_frequencies.py` (structure) + `script/export_runs.py` (banner/CLI).

- **Module banner + REPO_ROOT argparse** (export_runs.py:76-96 docstring with Purpose/Direction-of-truth/Usage; `REPO_ROOT = Path(__file__).resolve().parents[1]` at :233).
- **Registry enumeration + excluded-with-reason rows** — audit_n_frequencies.py's missing-dataset disclosure (DATA.md:41-53 lists the 7 GUE rows) is the exact shape: 62 models iterated from `pipeline/models_info.json`, paradigm from the `type` column (MLM 32 / CLM 18), DL 5 + EMPTY 7 emitted as excluded-with-reason rows, never dropped.
- **Lazy kernel import (the hard rule):** `from dnallm.inference.vep import score_variant, evaluate_vcf` INSIDE the GPU run path only — module top stays torch-free or CI dies (Pitfall 2). Injectable scorer seam for CPU tests (stub scorer asserting the sanity-check expectations: nonsense < synonymous, RC control reporting).
- **Output:** `dnallm-mark/data/vep_zero_shot.{json,csv}` dual artifact + `schemas/vep_zero_shot.json` bucket + synthetic-fixture tests. Fixtures authored under `tests/fixtures/` (suite's `tests/inference/data/synthetic_variants.vcf` is a read-only SHAPE reference only). `evaluate_vcf` accepts a plain `Mapping[str, str]` reference — no FASTA needed for tests.

---

### 6. `script/convert_registry.py` + `pipeline/datasets_info.json` — provenance columns

**Analog:** itself. `KIND_PRESETS["datasets"]["columns"]` (`script/convert_registry.py:84-112`) is a plain list — append `source, citation, license, preprocessing, download_url, download_url_alternates` (planner's exact names). `--to-csv` emits missing as empty cell; `--to-json --merge-existing` round-trips. Extend the D-10 abort-on-wrong-count ingest validation family (existing tests: `tests/test_convert_registry.py`). JSON stays authoritative; the maintainer-editable surface is the CSV. Unknown values = literal `Unspecified`, never blank.

### 7. `script/build_provenance.py` (NEW) — emission trio

**Analog:** `script/audit_n_frequencies.py` — the exact trio: (1) generated DATA.md appendix table with the "GENERATED by ... do not edit by hand" stamp (DATA.md:3-7), (2) `data/provenance.json`, (3) `data/provenance.csv`. Reads the registry ONLY, deterministic (sorted iteration, `sort_keys`, no clock). Maintainer-review checkpoint gates publication (CONTEXT Q2 binding).

### 8. `script/freeze_snapshot.py` wiring + `Makefile` snapshot lane

**Analog:** itself (complete, tested — `freeze_snapshot()` at script/freeze_snapshot.py:52-103). Wiring: `snapshot:` Makefile target in the existing lane style (`$(UV) run --group data python script/freeze_snapshot.py --paths ... --output-dir baseline/snapshots --commit-hash ...`), extend `.PHONY`. **Hash derivation (Pitfall 5):** default `--commit-hash` = `manifest.json`'s committed `generated_from` (dnallm-mark/data/manifest.json carries `9918046...` + `data_version 1.1.0`) — NO `git rev-parse` in the data path; git only as a manual override. Commit the `.sha256` manifest, gitignore the `.tar` under `baseline/snapshots/` (mirrors `baseline/data-v1.sha256` committed). Line format is `sha256sum -c`-standard (two spaces). Add the frozen file list to the docstring's "intentionally unwired" note update (:12-15, :86-87).

### 9. `script/doi_swap.py` (NEW)

**Analog:** `script/run_migration_inventory.py` — thin REPO_ROOT-relative orchestrator, argparse with a `--write-manifest`-style action flag. Swap edits exactly two things in ONE commit (WR-01): README.md:117-123 (the HTML comment + tokenized Zenodo link) and the `.gitleaks.toml:19-35` rule block (rule + its allowlist). Refuse unless the target DOI is public (`--force` override for the maintainer); use `urllib.request` HEAD/GET check with a short timeout. Maintainer-executed, documented in phase docs.

### 10. `dnallm-mark/js/data.js` — remove `recalculateComparison`

**Analog:** the 04-05 dead-code deletion discipline (get_task_performance.py deleted with pivot assertions folded into exporter tests). Definition at `dnallm-mark/js/data.js:232-...`; zero callers confirmed (only comments at `js/config.js:37` and `tests/js/main-view-toggle.test.js:9` — update the config.js lesson comment, it cites the dead function). **Proof:** `tests/js/data-escape.test.js:16` already `require`s data.js — the module must keep loading; add an exported-surface assertion in the same early dedicated commit; `node --test tests/js/` lane (Makefile) is the gate. Sequencing: BEFORE METHODOLOGY.md lands (CONTEXT).

### 11. `pipeline/env_smoke.py` — peft check + relabel + sanction amendment

**Analog:** itself. Checks 1-6 PASS/FAIL greppable-line structure (env_smoke.py:368-404); pins parsed from pyproject, never duplicated (:32-37 area). Edits: (a) add a peft check (`import peft` + version print, same PASS/FAIL idiom); (b) relabel stale "dnallm 0.8.0" strings at :32-37, 41-43, 134-136, 182-188, 195-199, 212-215 → 1.2.1; (c) AMEND the docstring contract (:4-10, verbatim today: "Agents NEVER execute or import it — ``python3 -m py_compile`` is the only sanctioned agent-side proof") in the SAME adaptation commit to record the 2026-10-11 smoke sanction boundary (executed smoke now permitted as explicit plan TASKS on this GB10 host; E2' full sweep still dual-gated). Smoke executions are LOCAL plan tasks only — never in `make test`/CI.

### 12. Frontier-table machinery (+ VEP/provenance schema pattern shared)

**Analog:** `script/permutation_tests.py` + `schemas/permutation_tests.json` + `tests/test_schemas.py`.

- **Schema disclosure style** (`schemas/permutation_tests.json:4` `$comment`): fully-strict, methodology disclosed IN the schema (family size, coverage rule, seed, determinism statement) — `schemas/frontier.json` mirrors this for the frontier artifact.
- **Bucket wiring** (`tests/test_schemas.py:25-58`): add `"frontier": (REPO / "schemas" / "frontier.json", [DATA / "frontier.json"])` to `SCHEMA_FILES` (+ the file-count dict at :123) in the SAME commit as the first data (SC-6 three-way: schema + data + re-chained goldens).
- **Synthetic-fixture generation** (`tests/test_export_runs.py::_build_fixture_tree` / `_write_run_record` :89-235): the frontier generator is tested over a synthetic run-record tree with `+lora`/`+probe` alias cells; goldens chain-produced, never hand-edited (`tests/test_golden.py:29-32`).
- Frontier row derivations: `method` from run_record, `wall_hours` from started_at/finished_at (run_sweep.py:663-682), `total_flos` hard-required (export_runs.py:494-499), `trainable_params_pct` from the new run_finetune persistence (surface 1), `score_delta` = adapter-export vs full-export join on suffix-stripped base model (D-18 alias-normalization precedent, 05-04).

### 13. `docs/METHODOLOGY.md` + `docs/ONBOARDING.md` + README reproduction

**Analogs:** `DATA.md` (generated-doc header stamp :3-7, missing-row disclosure :41-53), README.md badge/Quick-Start sections (:100-111 server block — the reproduction section extends this backward with `uv sync` / `make data` / `make test` literal blocks + expected outputs per step, quoting the byte-stable drift-gate invariant), `tests/test_ci_replay.py` + `tests/fixtures/e2_replay/` (the fresh-clone proof style — "CI replays exactly this chain on every PR"). METHODOLOGY.md documents the four aggregation methods (all in `script/summarize_comparison.py`) + F6 dual views + tie rule + permutation tests; ONBOARDING.md is the EXT-01/02 checklist (registry edit → convert_registry round-trip → quirks if needed → audit → `run_sweep --dry-run`), every step dry-run-validatable. Sequencing: dead-code removal (10) lands FIRST.

## Shared Patterns

### Source-contract tests for GPU-importing pipeline files
**Source:** `tests/test_run_finetune_contracts.py:6-10`
**Apply to:** every run_finetune/run_sweep peft/probe/curve behavioral contract. Read source text, never import.

### Fail-fast collect-all-problems validation
**Source:** `pipeline/run_sweep.py:290-335` (`_validate_filters`), `:383-478` (`load_priority_tiers`)
**Apply to:** `--peft` choices, `--curve` fraction list, provenance CSV ingest (abort-on-wrong-count, D-10).

### Skip-as-data / excluded-with-reason disclosure rows
**Source:** `DATA.md:41-53` (7 missing GUE rows); suite `vep.py:57-79` (`VariantAlignment.skip_reason`)
**Apply to:** VEP DL/EMPTY model rows, `Unspecified` provenance, frontier cells with no counterpart run.

### Dual CSV+JSON artifacts + schema buckets (one commit)
**Source:** `dnallm-mark/data/n_audit.{json,csv}`; `tests/test_schemas.py:25-58`
**Apply to:** `frontier.*`, `vep_zero_shot.*`, `provenance.*` — schema bucket + data + re-chained goldens land together; generator stamps the DATA.md-style appendix.

### Alias names via save_model_name + suffix-stripping joins
**Source:** `pipeline/run_finetune.py:181, 794-800`; D-18 alias normalization (05-04)
**Apply to:** `+lora`/`+ia3`/`+probe` cells — separate dirs + resume markers; exporters strip the suffix for the metadata join, keep the alias for display.

### Deterministic emission (byte-stable, drift-gated)
**Source:** `script/export_runs.py:43-46` discipline; `make data` no-op invariant
**Apply to:** build_provenance, frontier, VEP artifacts, snapshot manifests (sorted, sort_keys, no live clock; frozen hash from committed manifest.json, never live git).

### Untrusted-data parse-only + argv LIST discipline
**Source:** `[Skip]` per-row convention; `build_argv` LIST form (run_sweep.py:595-616)
**Apply to:** provenance CSV ingest (no eval, neutral quoting), all new sweep flag composition (T-03-10).

### GPU-side isolation (CI stays torch/dnallm-free)
**Source:** `pyproject.toml` `replace-imports-with-any`; Makefile lint file list
**Apply to:** `zero_shot_vep.py` (lazy dnallm import inside GPU path only), env_smoke peft check; ADD every new script/pipeline file to the Makefile `lint` list. Smoke executions are LOCAL bounded plan tasks — never in CI.

## No Analog Found

| Surface | Role | Reason / Planner Action |
|---------|------|------------------------|
| `docs/` directory itself (METHODOLOGY.md, ONBOARDING.md) | docs | No docs/ dir or in-repo prose-doc convention exists — content structure is planner's discretion per CONTEXT ("doc section order"); only the DATA.md generated-appendix stamp and README link conventions apply. The reproduction section's command blocks are assembled from RESEARCH E3 (all commands verified working). |
| `finetune_config_probe.yaml` / curve YAML variant | config | Genuinely new file — closest structure is `finetune_config_with_head.yaml` (head_config block + `frozen: true` per suite configs.py:14-17); field surface is suite-owned, content per RESEARCH B/C1 recommendations. |
| Frontier `trainable_params_pct` producer | service | One genuinely new pipeline-side computation (param count after adapter attach) — no repo precedent; formula and persistence target (`final_metrics.json`) given in RESEARCH B. |

## Metadata

**Analog search scope:** `script/`, `pipeline/`, `tests/` (+ `tests/js/`), `schemas/`, `baseline/`, `dnallm-mark/{js,data}/`, `Makefile`, `pyproject.toml`, `README.md`, `.gitleaks.toml`, `DATA.md`; suite read-only refs at `/home/forrest/Github/DNALLM` @ v1.2.1
**Files scanned:** ~30
**Pattern extraction date:** 2026-10-11
