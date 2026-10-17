# Phase 7: Pipeline-Side Enablement - Pattern Map

**Mapped:** 2026-10-11
**Files analyzed:** 13 (new + modified + deleted)
**Analogs found:** 13 / 13 (all analogs verified git-tracked via `git ls-files`)

> RESEARCH.md already contains verbatim, line-anchored excerpts for most of this
> phase (it is unusually concrete). This file adds the file classification and
> the per-file analog assignments the planner consumes; where RESEARCH quotes
> code, PATTERNS points at the same anchors rather than duplicating them.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `pipeline/flops_counter.py` (NEW) | service/utility (GPU-lane module) | transform (calibration pass) | `pipeline/dnallmmark_pipeline.py:43-708` (the class being ported — the analog IS the source) | exact (port source) |
| `pipeline/artifact_loader.py` (NEW) | utility | file-I/O | `run_sweep._read_operator_json` (`pipeline/run_sweep.py:524-541`) — opposite contract, same parsing surface | role-match |
| `pipeline/registry_loader.py` (NEW) | utility | file-I/O + merge | `run_sweep.enumerate_matrix` registry loads (`pipeline/run_sweep.py:367-371`) + `script/run_migration_inventory.py:93-98` (importlib file-path load) | role-match |
| `pipeline/run_finetune.py` (MOD) | service (GPU pipeline) | batch | itself — calibration slot between `:1423`/`:1425-1429`, write in `local_rank == 0` success block `:1482-1507`, registry loads `:672-679` | exact (self-anchors) |
| `pipeline/run_sweep.py` (MOD) | controller (CLI) | request-response (argv) | its own `build_argv` `:810-857`, `launch_subprocess` `:860-876`, `_manifest_payload` `:978-992` | exact (self-anchors) |
| `script/audit_n_frequencies.py` (MOD) | controller (CLI) | batch | its own `main()` `:596-601` | exact |
| `schemas/flops_report.json` (NEW) | config (contract) | — | `schemas/n_audit.json` (strict draft-2020-12, `additionalProperties: false`, optional-section `if/then`) | exact (pattern-match) |
| `tests/test_flops_counter.py` (NEW) | test | — | `tests/test_run_finetune_contracts.py:743-783` (stub/exec discipline) + RESEARCH Pattern 1 harness shape | role-match |
| `tests/test_artifact_loader.py` (NEW) | test | — | `tests/test_sweep.py` helper style (`write_registry`/`tmp_path`) | role-match |
| `tests/test_registry_loader.py` (NEW) | test | — | `tests/test_sweep.py:115-140` (`write_registry`/`make_registry`) + RESEARCH Pattern 3 test shape | exact (fixture reuse) |
| `tests/test_sweep.py` (MOD) | test | — | its own `flag_value`/`run_cli` harness `:143-154` + argv tests `:491-522`, `:1479-1506` | exact |
| `tests/test_run_finetune_contracts.py` (MOD) | test | — | its own `LEGACY_PIPELINE` reads `:394/:491/:559/:622/:666` (re-pin sites) | exact |
| `pipeline/dnallmmark_pipeline.py` (DELETE) + `Makefile` (MOD, lint list `:125-126`) | — | — | — | — |

## Pattern Assignments

### `pipeline/flops_counter.py` (service/utility, calibration transform)

**Analog (port source):** `pipeline/dnallmmark_pipeline.py` — `FlopsCounter` class `:43-64`, `_register_hooks` if/elif dispatch chain `:66-187`, hook closure factories `:189-668`, `save_to_json` report schema `:690-705`, calibration call pattern `:1072-1157`. RESEARCH.md "Pattern 1" quotes the load-bearing excerpts verbatim (dispatch classname lists, report keys, calibration forward). Port hook bodies and dispatch ORDER verbatim; the single structural change is the lazy torch seam:

```python
# Lazy torch seam (RESEARCH Pattern 1 item 2) — do NOT `import torch` at module top
def _torch_nn():
    import torch.nn as nn
    return nn
```

Tests monkeypatch `flops_counter._torch_nn` with a stub module (plain classes `Linear`, `Conv1d`, `Conv2d`, `MultiheadAttention`, `Embedding`, `LayerNorm`, `SiLU`, `GELU`, `ReLU`). Hook closures are duck-typed (`.shape`, `.numel()`, `.out_features`, `.name_or_path`) — see RESEARCH Pattern 1 items 1-3. Add uncovered accounting (module constant threshold, recommended 0.05) and a hardware-section builder reading `metrics.get("train_runtime")`, the `max_mem` computation from `run_finetune.py:1533-1538`, and `torch.cuda.get_device_name()`.

### `pipeline/artifact_loader.py` (utility, tolerant file-I/O)

**Analog (parsing surface, inverted contract):** `pipeline/run_sweep.py:524-541`:

```python
def _read_operator_json(path, flag_name):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except OSError as exc:
        sys.exit(f"[Error] cannot read {flag_name} file {path}: {exc}")
    except json.JSONDecodeError as exc:
        sys.exit(f"[Error] {flag_name} file {path} is not valid JSON: {exc}")
```

Same `open`/`json.load` + `OSError`/`json.JSONDecodeError` catch surface, but return `None` sentinel instead of `sys.exit` (D-17/D-18). Stdlib `json` + `pathlib` only; stateless, no cache. The second precedent (`run_matrix` inline read `:1105-1130`, corrupt metrics → fail cell only) stays UNTOUCHED per D-20.

### `pipeline/registry_loader.py` (utility, registry merge)

**Analogs:**
1. Official-file load shape (must reproduce exactly, including crash-on-missing import-time behavior) — `pipeline/run_finetune.py:672-679`:
```python
base_dir = os.path.dirname(os.path.abspath(__file__)) + os.sep
with open(base_dir + "datasets_info.json", "r", encoding="utf-8") as _registry_file:
    datasets_info = json.load(_registry_file)
with open(base_dir + "models_info.json", "r", encoding="utf-8") as _registry_file:
    models_info = json.load(_registry_file)
```
and the `registry_dir`-parametrized form `pipeline/run_sweep.py:367-371` (three sites: `enumerate_matrix`, `_validate_filters` `:473-477`, `_load_registry_key_sets` `:513-517`), plus `script/audit_n_frequencies.py:599-601`.

2. Cross-root import for the audit script — `script/run_migration_inventory.py:93-98` (the established `importlib.util.spec_from_file_location` precedent; use it to load `pipeline/registry_loader.py` from `script/`).

Path resolution: `DNALLMMARK_CUSTOM_REGISTRY_DIR` > `XDG_CONFIG_HOME` > `~/.config`, joined with `dnallmmark/` — hand-rolled, NO platformdirs (Pitfall 2: absent from dev/data groups; CI crash). Merge: custom absent → return official dict as-is; custom key colliding with official → fail fast naming the key and BOTH paths (D-08).

### `pipeline/run_finetune.py` (MOD — calibration slot + post-success write)

Three anchors (verified this session):

**Calibration slot** — insert between `:1423` (`model.target_length` adjustment) and `:1425-1429` (`reset_peak_memory_stats`), before `DNATrainer` ctor at `:1444`. Port the legacy forward (no_grad, evo2-backbone case, bf16 autocast, attention_mask retry) verbatim from `dnallmmark_pipeline.py:1075-1157`.

**Post-success write** — inside `local_rank == 0` block (`:1482`), write `flops_report.json` AFTER the `final_metrics.json` write (`:1495-1506`) and BEFORE the `trainer_state.json` marker copy (`:1507`). The existing comment block at `:1486-1494` documents the WR-13 marker-last discipline — the new write must join that ordering and its contracts test.

**Registry rewiring** — replace `:672-679` with calls into `registry_loader`, keeping module-level timing and identical failure modes (missing official file still raises at import).

**CRITICAL constraint:** any new pure helper must NOT be added between `def validate_subset_file` and `def set_seed` or between `def validate_train_fraction` and `def set_seed` — `tests/test_run_finetune_contracts.py:743-783` regex-extracts and `exec()`s those spans:

```python
match = re.search(
    r"def validate_subset_file\(.*?\n(?=def set_seed)", src, re.DOTALL
)
...
exec(match.group(0), namespace)  # noqa: S102 - pure extracted fns
```

New helpers go after `set_seed` or in `flops_counter.py`.

### `pipeline/run_sweep.py` (MOD — four flags, pre-validation, manifest)

**build_argv append pattern** (`:844-857`) — new kwargs append exactly like `train_fraction`:
```python
if train_fraction is not None:
    argv += ["--train_fraction", str(train_fraction)]
```
Add `subset_file=None, effective_batch_size=None, num_train_epochs=None, cache_dir=None` kwargs to `build_argv` (`:810`), `launch_subprocess` (`:860`), and the `functools.partial` executor binding in `run_matrix`. Flag registration: `--effective_batch_size` with `nargs="?", const=16, type=int, default=None` (D-12); underscore names only (D-11).

**Collect-all fail-fast validator** — model on `_read_operator_json` (`:524-541`) + `parse_curve_fractions`/`load_priority_tiers` (`:544-617`, the `problems`-list-then-`sys.exit` discipline). Runs in `main()` after `_validate_filters` (`:1218-1237` zone). Do NOT import `run_finetune.validate_subset_file` (torch blocks headless import).

**Manifest only-when-present** — `_manifest_payload` (`:978-992`) projects a fixed key set; thread a present-flags dict and merge into cells only when keys exist. `_write_json` (`:899-903`) already uses `sort_keys=True`, keeping byte determinism. `_new_record` (`:945-975`) stays untouched (run_record.json contract, D-02 spirit).

**Abs-path resolution** — follow the `--output-root` precedent `Path(args.output_root).resolve()` at `:1179` for `--subset_file`/`--cache_dir` (child cwd pinned to `PIPELINE_DIR`, see `launch_subprocess` docstring `:864-866`).

### `schemas/flops_report.json` (NEW)

**Analog:** `schemas/n_audit.json` — draft-2020-12 `$schema`, `$id` under `https://raw.githubusercontent.com/zhangtaolab/dnallmmark/main/schemas/...`, explanatory `$comment`, `additionalProperties: false` on every closed object, open maps via `additionalProperties: {...}` (the `by_char` integer map at `:75-78` is the exact shape for `layer_details`), optional sections via `if/then` (`:37-56`; use for optional `hardware`). Required top-level keys = legacy report keys (RESEARCH Pattern 1 item 5) + `schema_version` const 1 + `uncovered_layers`; `layer_details` open integer map; `computation_size_ratio` number-or-null.

**Test consumer:** `tests/test_schemas.py` uses `Draft202012Validator` (`:19`) with a committed-file bucket map (`SCHEMA_FILES` `:25+`) — flops_report does NOT join that map (artifact never committed, D-26); its validation test builds a deterministic synthetic fixture in-test instead.

### Tests (NEW + MOD)

**Harness pattern:** `tests/test_sweep.py:115-154` — `write_registry(root, models, datasets)`, `make_registry(tmp_path)`, `run_cli(monkeypatch, argv)`, `flag_value(argv, flag)`. Reuse `write_registry` in `test_registry_loader.py`; reuse `run_cli`/`flag_value` for the four-flag argv parity and bare-flag `const=16` tests (existing shape: `:491-522` and `:1479-1506`).

**Stub-torch pattern:** RESEARCH Pattern 1 example (`monkeypatch.setattr(flops_counter, "_torch_nn", lambda: nn)`; direct closure invocation with `(module, inputs, outputs)` triples).

**Env pinning:** all overlay tests MUST `monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", ...)` (empty tmp dir for absent-case, populated for merge-case) so outcomes are machine-independent (Pitfall 3).

**Deletion re-pins:** `tests/test_run_finetune_contracts.py` reads `LEGACY_PIPELINE` at `:394/:491/:559/:622/:666` — inline those expected values as literals when `pipeline/dnallmmark_pipeline.py` is deleted (document as transcribed from the deleted file).

### `Makefile` (MOD)

Lint list at `:125-126` is an explicit file list — append `pipeline/flops_counter.py pipeline/registry_loader.py pipeline/artifact_loader.py` in the same commit that creates them. Typecheck needs nothing (`[tool.ty.src].include` already covers `pipeline/`).

## Shared Patterns

### Absent = byte-identical
**Source:** `build_argv` `:853-857` + `test_peft_none_default_is_byte_identical_to_today` (`tests/test_sweep.py:1418`)
**Apply to:** all four sweep flags, the registry overlay, manifest fields. Absent flag → zero argv elements → zero manifest keys → zero behavior change. Every new surface gets an absent-case parity test.

### Fail-fast, collect-all
**Source:** `parse_curve_fractions` / `load_priority_tiers` (`run_sweep.py:403-617`)
**Apply to:** subset pre-validation, overlay collision errors, flag sanity checks (`effective_batch_size >= 1`, `num_train_epochs >= 1`).

### Deterministic JSON write
**Source:** `_write_json` (`run_sweep.py:899-903`): `json.dump(payload, f, indent=4, ensure_ascii=False, sort_keys=True)`
**Apply to:** flops_report.json write.

### WR-13 marker-last ordering
**Source:** `run_finetune.py:1486-1507` comment + `test_final_metrics_written_before_resume_marker`
**Apply to:** flops_report write order: final_metrics → flops_report → marker copy; extend the contracts test.

### LIST argv, never shell
**Source:** `launch_subprocess` (`run_sweep.py:872-876`, `subprocess.run(list, cwd=PIPELINE_DIR, check=True)`)
**Apply to:** all new flag threading (T-03-10).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `pipeline/flops_counter.py` (uncovered accounting + hardware section) | service | transform | No precedent — legacy had no uncovered concept and no hardware capture. Design per RESEARCH Pattern 1 items 6-7 (threshold constant 0.05 recommended) |
| GB10 smoke task | — | — | Not a code file; use the Phase 6 proven command from `.planning/milestones/v0.7.1-phases/06-revision-packaging-extended-lanes/06-02-SUMMARY.md` and RESEARCH "Code Examples" |

Everything else has a direct, git-tracked analog.

## Metadata

**Analog search scope:** `pipeline/`, `script/`, `tests/`, `schemas/`, `Makefile` (all paths verified via `git ls-files`; no gitignored mirrors involved)
**Files scanned:** 12 analogs read (targeted ranges only)
**Pattern extraction date:** 2026-10-11
**Primary supplemental source:** `07-RESEARCH.md` (line-anchored verbatim excerpts — planner should read its Patterns 1-5 alongside this file)
