---
phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
reviewed: 2026-10-11T08:04:43Z
depth: standard
files_reviewed: 19
files_reviewed_list:
  - .claude/CLAUDE.md
  - AUDIT.md
  - docs/TUI-REQUIREMENTS.md
  - Makefile
  - pipeline/artifact_loader.py
  - pipeline/flops_counter.py
  - pipeline/registry_loader.py
  - pipeline/run_finetune.py
  - pipeline/run_sweep.py
  - README.md
  - schemas/flops_report.json
  - script/audit_n_frequencies.py
  - script/export_runs.py
  - tests/test_artifact_loader.py
  - tests/test_flops_counter.py
  - tests/test_known_defects.py
  - tests/test_registry_loader.py
  - tests/test_run_finetune_contracts.py
  - tests/test_sweep.py
findings:
  critical: 1
  warning: 6
  info: 5
  total: 12
status: issues_found
---

# Phase 7: Code Review Report

**Reviewed:** 2026-10-11T08:04:43Z
**Depth:** standard
**Files Reviewed:** 19 (scoped to the phase's diff `be1f02d..HEAD`; full-file reads, plus behavioral verification of suspect paths in a sandbox)
**Status:** issues_found

## Summary

Phase 7 ported `FlopsCounter` into `pipeline/flops_counter.py` behind a lazy `torch.nn` seam, added the overlay `registry_loader.py` and tolerant `artifact_loader.py`, threaded four argv flags through `run_sweep.py`, integrated the always-on FLOPs calibration + post-success `flops_report.json` write into `run_finetune.py`, and re-pinned the legacy parity literals after deleting the legacy monolith. The port discipline itself holds up well: the dispatch order and hook formulas are internally consistent and pinned by tests; `run_sweep.py` stays stdlib-only; the absent-flag byte-identity paths are real (verified by reading every `if ... is not None` branch); the WR-13 write order (final_metrics → flops_report → marker) is correctly ordered and contract-tested; the D-04 re-pinned `LEGACY_*` literals in `tests/test_run_finetune_contracts.py` were cross-checked against the active source lists and match modulo the documented name map.

However, the review found one verified crash-path defect in the phase's core deliverable (the FLOPs write divides by a zero token count that `run_finetune.py` itself can produce), a verified fail-fast bypass in the new sweep-side subset pre-validation (JSON `null` passes), a silent full-evaluation fallback for empty subset entries (which the audit script can emit), an unpinned-env test-reliability regression in `tests/test_sweep.py` introduced by the 07-02 registry-loader rewiring, and several smaller robustness/consistency gaps. No security findings: no eval/exec, subprocess argv-list discipline held everywhere, and the README token is the documented intentional Zenodo link (AUDIT.md D-08).

Two findings were behaviorally reproduced in a sandbox before grading (CR-01, WR-01); the rest are static traces over the exact cited lines.

## Critical Issues

### CR-01: `save_to_json` crashes on `num_tokens=0` — cell ends "completed" without marker or FLOPs report and is silently retrained by every sweep

**File:** `pipeline/flops_counter.py:753-755` (division), `pipeline/run_finetune.py:1466-1468` (produces the 0), `pipeline/run_finetune.py:1591-1598` (unconditional post-success call)
**Issue:** `save_to_json` guards the extrapolation against `num_tokens is None` (the docstring at `flops_counter.py:761-763` explicitly documents fixing the legacy `None` crash) but not against `num_tokens == 0`:

```python
per_token_flops = (
    self.total_flops / num_tokens if num_tokens is not None else None
)
```

`run_finetune.py` itself produces `current_tokens = 0` in the calibration slot's else-branch (train split empty after load/filter, or `train[0]` carrying neither `input_ids` nor `inputs_embeds` — note `validate_sequences(minl=0, ...)` admits zero-length sequences), and then calls `flops_counter.save_to_json(num_tokens=current_tokens, ...)` unconditionally in the success block. Verified in a sandbox: `ZeroDivisionError: division by zero`.

Because of the WR-13 ordering, `final_metrics.json` is already written when the exception fires, the `trainer_state.json` marker is NOT copied, and the designed blind-except swallows the error. Downstream consequence: `run_sweep.py`'s CR-02 rule (executor exit 0 + `final_metrics.json` present = **completed**) records the cell completed, but with no resume marker every subsequent sweep silently **retrains** it (GPU-days of waste), and the "completed" cell never carries the `flops_report.json` this phase exists to produce. This is exactly the permanently-inconsistent-cell class T-07-07/WR-13 were built to prevent — the flops write joined the kill-window chain but brought its own crash window.
**Fix:** In `pipeline/flops_counter.py`, treat a non-positive token count as "extrapolation unavailable" (the same semantics as `None`):

```python
per_token_flops = (
    self.total_flops / num_tokens
    if num_tokens is not None and num_tokens > 0
    else None
)
all_tokens_flops = (
    self.total_flops * all_tokens / num_tokens
    if all_tokens is not None and num_tokens is not None and num_tokens > 0
    else None
)
```

(The schema already allows `num_tokens: 0` with null extrapolations, so no schema change is needed. Optionally also log loudly at the call site when `current_tokens == 0` on a non-empty train split — a zero-token calibration sample means the FLOPs number is meaningless even when it does not crash.)

## Warnings

### WR-01: `run_sweep._validate_subset_file` bypassed by a JSON `null` top level — collect-all startup contract violated

**File:** `pipeline/run_sweep.py:636-666` (specifically line 643)
**Issue:** The validator uses `loaded = None` as its own unreadable-file sentinel and then guards with `if loaded is not None and not isinstance(loaded, dict):` — so a subset file whose content is the JSON literal `null` parses to `None`, collides with the sentinel, and **passes sweep-start validation with zero problems** (verified in a sandbox; `false`, `0`, and `""` are all correctly refused — only `null` collides). The docstring's contract ("A bad subset map must abort the sweep at STARTUP with every problem listed together — never per-cell") is violated: the file is threaded to every child, each child's authoritative validator rejects it, and the sweep degrades to N per-cell `CalledProcessError` failures instead of one startup abort.
**Fix:** Use a distinct sentinel:

```python
_LOADED = object()
loaded = _LOADED
try:
    with open(path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
except (OSError, json.JSONDecodeError) as exc:
    problems.append(f"cannot read {path}: {exc}")
if loaded is not _LOADED and not isinstance(loaded, dict):
    ...
```

(or simply always append a problem when the load failed and drop the sentinel entirely, as the child's `validate_subset_file` effectively does).

### WR-02: An empty subset-ID list silently means FULL test-split evaluation — and the audit can emit exactly that

**File:** `pipeline/run_finetune.py:386-392` (`apply_eval_subset`), `pipeline/run_finetune.py:348-364` (validator accepts it), `script/audit_n_frequencies.py:309-315` (producer)
**Issue:** `apply_eval_subset` short-circuits on `if not ids: return`, so a task mapped to `[]` is treated identically to "no entry" — the FULL test split is evaluated while the operator believes the unified-N fairness subset is applied. The child validator raises no problem for an empty list. Meanwhile `audit_n_frequencies.py` computes `unified = min(strict_survivors, n_tolerant_survivors)` and emits `subsets[name] = sorted(test_strict_ids)[:unified]` whenever a test split is readable — a task where no test row passes the strict ACGT filter yields `unified_eval_n: 0` and an **empty-list entry** in `pipeline/eval_subsets.json`. That is precisely the "silently no-op an evaluation" class this codebase refuses loudly everywhere else (the Dataset_name-divergence guard in the same validator exists for exactly this reason). Cross-model test-row comparability — the feature's whole point — breaks silently for such a task.
**Fix:** In `run_finetune.validate_subset_file`, refuse empty ID lists by name (e.g. `f"{task}: empty ID list — an empty subset cannot mean full evaluation; remove the key or investigate the audit's unified_eval_n=0"`), and/or make `apply_eval_subset` treat `[]` as `select([])` rather than a no-op. At minimum, `audit_n_frequencies.py` should omit tasks with `unified == 0` from `eval_subsets.json` and warn, instead of emitting a key that silently disables the subset.

### WR-03: `tests/test_sweep.py` registry paths are unpinned against the custom-overlay env — machine-dependent failures once a real overlay exists

**File:** `tests/test_sweep.py:157-171, 653-677, 761-777` (and every `run_cli`/`enumerate_matrix` test); cross-ref `pipeline/registry_loader.py:57-81`
**Issue:** 07-02 rewired `run_sweep.enumerate_matrix` / `_validate_filters` / `_load_registry_key_sets` through `registry_loader`, which applies the user-owned overlay from `DNALLMMARK_CUSTOM_REGISTRY_DIR` > `XDG_CONFIG_HOME` > `~/.config/dnallmmark`. `tests/test_sweep.py` pins **neither** variable (verified by grep across `tests/` — only `test_registry_loader.py` pins them), and `tests/conftest.py` has no autouse pin either. `tests/test_registry_loader.py:26-29` documents the exact hazard: "once real custom files exist on a machine, an unpinned test would see the local overlay and diverge from CI." On the maintainer's machine — the moment the custom-registry feature this phase shipped is actually used — the frozen-order tests (`test_default_enumeration_order_is_frozen_without_priority_file` asserts the exact 12-cell list; `test_cli_absent_filters_keep_full_matrix_semantics`, `test_dry_run_writes_only_the_planned_manifest`, …) enumerate extra custom models and fail, making `make test` red locally while CI stays green.
**Fix:** Add an autouse fixture in `tests/test_sweep.py` (or `tests/conftest.py`) pointing `DNALLMMARK_CUSTOM_REGISTRY_DIR` at an empty `tmp_path`-style directory for every test that loads registries — the `pin_custom_dir` idiom from `test_registry_loader.py:56-64`, applied at module/conftest scope.

### WR-04: `test_registry_loader.py` unreadable-file test lacks the running-as-root skip guard its sibling has

**File:** `tests/test_registry_loader.py:220-235`
**Issue:** `test_unreadable_custom_file_fails_loud_naming_file` chmods the custom registry to `0o000` and expects `SystemExit`. `tests/test_artifact_loader.py:44-53` demonstrates the correct idiom for the same technique — `if os.access(path, os.R_OK): pytest.skip("permission bits not enforced (running as root)")` — because root ignores mode bits. `test_registry_loader.py` omits the guard: under a root CI container the `open()` succeeds, the JSON parses, the overlay merges, no `SystemExit` is raised, and the test fails spuriously (reliability defect in a test file, flagged per the test-reliability exception).
**Fix:** Mirror the sibling guard:

```python
custom_path.chmod(0o000)
if os.access(custom_path, os.R_OK):
    pytest.skip("permission bits not enforced (running as root)")
```

### WR-05: `--cache_dir ""` silently resolves to the current directory and is threaded to every child

**File:** `pipeline/run_sweep.py:1440-1454`
**Issue:** The flag-sanity block refuses a provided-but-empty `--subset_file` (line 1440-1444, with its own test), but `--cache_dir` gets no equivalent guard: `Path("").resolve()` is the CWD (verified: `'/tmp/gsd-review-check'` in the sandbox; a whitespace value resolves to a `' '`-suffixed path). An empty `--cache_dir` therefore threads `--cache_dir <repo root>` to every child, which sets `HF_HOME`/`MS_CACHE_HOME` to the repository root in the child's argv pre-scan (`run_finetune.py:22-31`) — caches start landing in the repo with no error and no warning. Same operator-error class as the guarded `--subset_file` case (WR-14/Pitfall 5); the asymmetry looks like an oversight in the same commit.
**Fix:** Add the twin check to the collect-all block:

```python
if args.cache_dir is not None and not args.cache_dir.strip():
    flag_problems.append(
        f"--cache_dir {args.cache_dir!r} is empty — refusing to "
        "thread a pathless flag"
    )
```

### WR-06: Registry-key vs `Dataset_name` divergence desynchronizes `run_sweep` cell dirs from `run_finetune` output dirs — guarded only for subset-file tasks

**File:** `pipeline/run_sweep.py:900-910` (`cell_dir_for` keyed by registry task key) vs `pipeline/run_finetune.py:985, 1200` (outdir built from `row["Dataset_name"]`)
**Issue:** `run_sweep` enumerates and checks `final_metrics.json`/resume markers under `{root}/{model}/{registry-key}/...`, while `run_finetune` writes under `{save_root}/{model}/{row["Dataset_name"]}/...`. The divergence is refused loudly only inside `validate_subset_file` (`run_finetune.py:329-347`, "a divergent row would silently no-op that task's subset") and only for tasks present in a `--subset_file`. For any other divergent row, every cell of that task trains successfully in the `Dataset_name` dir while the sweep records it **failed** ("executor exited 0 but final_metrics.json is missing") and re-attempts it forever — a misleading failure manifest and unbounded retraining. All 50 registry rows coincide today (the subset validator's comment says so), but the sweep-path coincidence is enforced nowhere, and the overlay loader this phase added makes user-authored custom dataset rows a new source of divergence.
**Fix:** Either join the sweep on `Dataset_name` (`enumerate_matrix` emitting `entry["Dataset_name"]` as the task component), or add a one-time startup assertion over the merged datasets registry that every key equals its `Dataset_name`, refusing loudly with the offending rows named.

## Info

### IN-01: Unused `samples` from `count_split_tokens`

**File:** `pipeline/run_finetune.py:1454`
**Issue:** `total_tokens, samples = count_split_tokens(...)` — `samples` is never read (the legacy report carried a sample count; the new `flops_report.json` does not). Tuple-unpack targets escape F841, so ruff stays silent.
**Fix:** `total_tokens, _ = count_split_tokens(...)` or drop the second element at the call site.

### IN-02: Duplicated `gpu_memory_override` assignment

**File:** `pipeline/run_finetune.py:708-709`
**Issue:** `gpu_memory_override = args.gpu_memory` appears twice back-to-back (pre-existing, inside a phase-edited file).
**Fix:** Delete one line.

### IN-03: README CLI surface outgrew its documentation — including this phase's four threaded flags

**File:** `README.md:284-289` (sweep section), `README.md:291-324` (run_finetune args listing)
**Issue:** The `run_sweep.py` section documents only `--seeds/--output-root/--dry-run`; the four flags this phase threaded (`--subset_file`, `--effective_batch_size` with its bare-flag-means-16 behavior, `--num_train_epochs`, `--cache_dir`) are undocumented, as are `--peft`, `--config-variant`, `--train_fraction`, `--priority-file`, `--from-failures`, and `--curve`. The TUI requirements doc positions these flags as the future TUI's CLI-first contract, so the README is the operator's only reference.
**Fix:** Extend the sweep section with the flag table (or a pointer to `--help`), noting the bare-`--effective_batch_size`=16 default and the absolute-path resolution of the two path flags.

### IN-04: `.claude/CLAUDE.md` claims "Python 3.11+ required (per README.md badge)" — the README badge is 3.13+

**File:** `.claude/CLAUDE.md:36`
**Issue:** The regenerated stack section attributes the 3.11+ floor to the README badge, which actually reads "Python 3.13+" (`README.md:4`; the 3.13 pin is the data toolchain per `.python-version`). The pipeline-side 3.11+ floor may be correct, but the cited evidence is wrong.
**Fix:** Reword to "Python 3.11+ for the GPU pipeline; the data toolchain is pinned to 3.13 (see `.python-version`)" and drop the badge attribution.

### IN-05: CPU-run `max_mem_gb` records `0.0`, contradicting `build_hardware_section`'s "records nulls rather than lying" contract

**File:** `pipeline/run_finetune.py:1584-1585` vs `pipeline/flops_counter.py:822-824`
**Issue:** `build_hardware_section`'s docstring states each field "is nullable so a CPU-only or NPU run records nulls rather than lying", but the CPU branch hard-codes `max_mem_gb = 0.0` — nothing was measured on a CPU run, so 0.0 is a fabricated reading, not a null. (NPU runs read a real counter; `gpu_device`/`train_time` already follow the null contract.)
**Fix:** Use `max_mem_gb = None` in the `else` branch (schema allows null).

---

_Reviewed: 2026-10-11T08:04:43Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
