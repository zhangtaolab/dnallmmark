---
phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
reviewed: 2026-10-14T11:14:13Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - Makefile
  - pipeline/run_finetune.py
  - pipeline/registry_loader.py
  - pipeline/models_info.json
  - schemas/custom_registry.json
  - tests/test_run_finetune_contracts.py
  - tests/test_registry_loader.py
  - tests/test_registry_unification.py
  - tests/test_model_registry.py
findings:
  critical: 1
  warning: 2
  info: 3
  total: 6
status: issues_found
incremental: true
diff_base: 67027b29ccd49aadbd8bbe57285cfc97d25086a1
---

# Phase 07: Code Review Report (Incremental)

**Reviewed:** 2026-10-14T11:14:13Z
**Depth:** standard (incremental re-review over `67027b2..HEAD`)
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Incremental review of the Phase 07 deliverable surface after later phases (08-12)
and quick tasks (261014-c2l, 261014-f4w, 261014-ir9, 261014-l6h, 09-01/09-02)
modified it: `run_finetune.py` gained the `directories_config` startup merge
(`--model_root`/`--dataset_root`/`--log_dir`/cache-dir file branch),
`registry_loader.py` gained the D-09 `enabled:false` skip and the CR-01
`UnicodeDecodeError` catch, `models_info.json` got 5 repo-ID fixes and the
62→59 Chaoba removal, and `schemas/custom_registry.json` landed as the custom
entry contract.

Verified sound (no findings): the loader's D-09 sentinel semantics (`is not
False`, dict-guarded, collision-check-first) and its test coverage; the
`UnicodeDecodeError` fix (correctly a `ValueError` sibling, not a
`JSONDecodeError` subclass); the storage-root separator normalization and
byte-identical absent-flag branches; the strict-vs-tolerant
`directories_config` split; the Chaoba removal (no dangling references
anywhere in pipeline/script/tui/tests/js); the schema's property enumeration
(covers every official model and dataset field — a verbatim-mirrored official
row validates); the registry count/`key == Model_name` contract (59 entries,
verified); the Makefile extensions (`snapshot-update`'s script-mode entry
point exists with `--regenerate` handling and script-mode sys.path setup;
`.PHONY` covers all new targets; existence-guard lists are sound). All 105
tests in the four in-scope test files pass (`uv run --group dev pytest
tests/test_registry_loader.py tests/test_registry_unification.py
tests/test_model_registry.py tests/test_run_finetune_contracts.py -q`).

The one blocker is a contract mismatch between the shipped custom-registry
schema/wizard and the pipeline consumer: a fully schema-valid, wizard-landed
custom entry can omit fields `run_finetune.py` hard-indexes, crashing the run
with an uncaught `KeyError` that names neither the file nor the entry.

## Critical Issues

### CR-01: Schema-valid custom entries crash `run_finetune.py` with uncaught `KeyError` — required-field sets are inconsistent across the overlay chain

**File:** `schemas/custom_registry.json:9,43-46` + `pipeline/run_finetune.py:1021,1322,1008,1077` + `pipeline/registry_loader.py:161-168`
**Issue:** The custom-registry entry contract declares `required` as
`["Model_path", "size (M)", "type", "Tokenizer"]` (models) and
`["Dataset_path", "Category", "Train", "Dev", "Test", "labels", "type", "metric"]`
(datasets); `Mean_token_length` and `length` are explicitly optional numerics
("optional numerics may be absent"), and `Model_name`/`Dataset_name` are
optional (stamped only by the TUI `land()` path — hand-edited files, the
documented user-file contract per the schema `$comment`, never pass through
it). The TUI wizard validator mirrors this (`tui/services/custom_validation.py`
has no required check for `Mean_token_length`; its `_check_numeric(values,
"length", ...)` at :281 skips absent values and no `_check_required` backs it).
But `run_finetune.py` hard-indexes exactly those fields with no try/except and
no loader-side validation:

- `pipeline/run_finetune.py:1021` — `mean_token_len = model_row["Mean_token_length"]` (before the per-model error log even opens; kills the whole bare run at that model)
- `pipeline/run_finetune.py:1322` — `data_length = row["length"]` (after the GPU model load — a wasted load, then the whole run dies)
- `pipeline/run_finetune.py:1008` / `:1077` — `model_row["Model_name"]` / `row["Dataset_name"]` (hand-edit path)

`registry_loader._load_registry` merges custom entries with zero shape
validation (by design — validation lives only in the TUI import path), so a
minimal wizard-completed entry — the documented happy path ("required = the
wizard-required subset") — reaches the pipeline and aborts a multi-day bare
sweep with a raw `KeyError` traceback naming neither the custom file nor the
offending key. This directly contradicts the loader's own fail-loud contract
("a hard error naming the file") and the project's wrong-root/wrong-input
hazard discipline. Reproduction: land a model via the wizard filling only the
required four fields; run bare `python run_finetune.py` → `KeyError:
'Mean_token_length'` at line 1021, remaining models never run (completed cells
are marker-protected, but the sweep aborts).

**Fix:** Close the gap at one seam (or both):
1. In `schemas/custom_registry.json`, move the pipeline-consumed fields into
   `required`: models add `Model_name`, `Mean_token_length`; datasets add
   `Dataset_name`, `length` — and mirror in
   `tui/services/custom_validation.py` (`_check_required(values,
   "Mean_token_length", ...)` model-side; `_check_required(values, "length",
   ...)` dataset-side), or stamp them in `custom_entries.land()`.
2. Defense-in-depth in `pipeline/registry_loader.py::_load_registry`: after
   the collision loop, verify each merged custom entry carries the
   pipeline-consumed field set and `raise SystemExit` naming the custom file,
   the key, and the missing field — keeping the crash loud but diagnosable
   for hand-edited files:

```python
PIPELINE_REQUIRED = {
    "models": ("Model_name", "Model_path", "Tokenizer", "Mean_token_length"),
    "datasets": ("Dataset_name", "Dataset_path", "Train", "Dev", "Test",
                 "labels", "type", "metric", "length"),
}
```

## Warnings

### WR-01: The 5 repo-ID fixes in `models_info.json` were not propagated — the committed display data (and the public Models page) still carries the stale IDs

**File:** `pipeline/models_info.json:66,172,280,570,768` (fixed side) vs `dnallm-mark/data/model_performance/DNABERT-2-117M_performance.json:13` (+ 4 siblings, stale side)
**Issue:** The incremental fix corrected five repo IDs in the registry
(`DNABERT-2-117M` modelscope → `ZhejiangLab-LifeScience/...`, `GenomeOcean-500M`
huggingface → `pGenomeOcean/...`, `MutBERT-Multi` huggingface → `JadenLong/...`,
`agro-nucleotide-transformer-1b` and `hyenadna-large-1m-seqlen-hf` modelscope →
`ZhejiangLab-LifeScience/...`), but the hand-maintained
`dnallm-mark/data/model_performance/*_performance.json` info blocks and the
committed `task_performance/*.json` still carry the old IDs
(`lgq12697/DNABERT-2-117M`, `DOEJGI/GenomeOcean-500M`, `CompBioDSA/MutBERT`,
...). `dnallm-mark/js/models.js:59-60,122-123` renders `modelscope`/
`huggingface` links directly from `model_performance/`, so the public Models
page keeps publishing the stale/wrong repo links the registry fix was made to
correct — a recurrence of exactly the dual-source drift class D-10 exists to
prevent (registry is the declared single source of truth for these fields).
(`task_performance/` staleness is already deferred to E2' regeneration, but
`model_performance/` is the hand-maintained input and is not covered by that
deferral.)
**Fix:** Apply the same five corrections to the info blocks in
`dnallm-mark/data/model_performance/{DNABERT-2-117M,GenomeOcean-500M,MutBERT-Multi,agro-nucleotide-transformer-1b,hyenadna-large-1m-seqlen-hf}_performance.json`,
re-run `make data`, and record the before/after per the fix discipline.

### WR-02: Empty-string CLI values for the new directory flags crash or silently degenerate — inconsistent with both `output_dir`'s handling and `directories_config`'s own drop-empty policy

**File:** `pipeline/run_finetune.py:1029-1030,993-1000,772` + `pipeline/directories_config.py:227-229`
**Issue:** `directories_config.effective()` returns the CLI value when it
`is not None`, so `--log_dir ""` yields `log_base = ""` and
`os.makedirs("", exist_ok=True)` raises a bare `FileNotFoundError` at
`run_finetune.py:1030`; `--model_root ""` yields `model_base = "/"` and model
paths resolve to `/models/...`. Contrast `output_dir` at :772/:1277, which
uses truthiness (`save_root = output_dir if output_dir else "./finetuned"`)
and treats `""` as absent — and contrast `_parse_directories`, which
deliberately drops empty/whitespace values ("a whitespace-only or empty value
= the key is absent"). The CLI path bypasses the normalization the file path
enforces, and the three flags disagree with their sibling flag.
**Fix:** Normalize once in `directories_config.effective()` so an empty or
whitespace-only CLI value falls through to the file lookup, matching the
documented key-tolerance rule:

```python
if cli_value is not None and cli_value.strip():
    return cli_value
return load_directories(path).get(key)
```

## Info

### IN-01: Stale "62/50" official-entry count in the schema `$comment` (registry is 59 since 261014-ir9)

**File:** `schemas/custom_registry.json:4`
**Issue:** The `$comment` says "field types probed across all 62/50 official
entries"; the Chaoba removal (261014-ir9) took the models registry to 59 and
updated both test files, but this contract-file comment was missed. (The "62"
strings in `tests/tui/test_pilot_env_check.py:145,359,625` are fake-service
fixture text, not pins — harmless.)
**Fix:** Update the `$comment` to "59/50".

### IN-02: Duplicated `gpu_memory_override = args.gpu_memory` assignment (pre-existing at diff_base)

**File:** `pipeline/run_finetune.py:763-764`
**Issue:** The assignment appears twice back-to-back; the second is dead code.
Present already at `67027b2` (lines 721-722 there), so not introduced by the
incremental changes — but it sits in an in-scope file and is trivially removable.
**Fix:** Delete line 764.

### IN-03: Pre-existing registry data inconsistencies in fields adjacent to this change (flagged for the maintainer since the registry was just edited)

**File:** `pipeline/models_info.json:2-16,1028-1044`
**Issue:** (a) `CrossDNA_519M` carries `Model_size: "8.1M"` and `size (M): 8.1`
— identical to `CrossDNA_8.1M` and contradicting its own name (likely a
copy-paste; expected ~519). (b) `prokbert-mini` carries operational
`Mean_token_length: 6` while its card says `mean_token_len: 1` and
`tokenizer: "overlapped 6-mer"` — for overlapped k-mers the per-token bp is 1,
and the `models_with_limited_length` cap of 1027 is unreachable under a /6
division (only meaningful at ~1 bp/token), so either the operational value or
the cap rationale is wrong. Both predate `67027b2` (untouched by the
incremental diff); both feed the public Models page.
**Fix:** Maintainer-verify against the source model cards and correct
`CrossDNA_519M`'s size pair; reconcile `prokbert-mini`'s
`Mean_token_length` with the overlapped-tokenizer reality (and note that
changing it alters max_length resolution, so document before/after per the fix
discipline).

---

_Reviewed: 2026-10-14T11:14:13Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard (incremental over 67027b2..HEAD)_
