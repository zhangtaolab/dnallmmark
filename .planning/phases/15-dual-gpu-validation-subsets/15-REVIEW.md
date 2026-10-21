---
phase: 15-dual-gpu-validation-subsets
reviewed: 2026-10-21T00:39:46Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - pipeline/run_finetune.py
  - pipeline/dispatch_core.py
  - script/make_subset_datasets.py
  - tests/test_subset_datasets.py
  - tests/test_run_finetune_contracts.py
  - tests/test_dispatch_core.py
  - docs/multi-gpu.md
  - Makefile
findings:
  critical: 1
  warning: 1
  info: 4
  total: 6
status: issues_found
---

# Phase 15: Code Review Report

**Reviewed:** 2026-10-21T00:39:46Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Reviewed the Phase 15 surface: the deterministic stratified subset generator
(`script/make_subset_datasets.py`), the 15-04 run_record producer
(`dispatch_core.write_cell_run_record` + call-site ordering), the 15-05
evaluate-merge producer fix (`run_finetune.py`), the three test suites, the
`docs/multi-gpu.md` dispatch-mode rewrite, and the Makefile lint wiring.

Overall assessment: the three code changes are well-engineered and their
invariants hold under adversarial checking. The evaluate merge is verifiably
additive-only with training keys winning collisions
(`merged = {**eval_results, **metrics}` at `pipeline/run_finetune.py:1729`),
`trainer.evaluate()` stays OUTSIDE the rank guard exactly as the prior
discarded-call discipline did (all ranks evaluate; writes rank-0 only), the
trainer_state marker copy remains the final write, and the argv surface is
untouched (27 `add_argument` calls confirmed). The generator is stdlib-only
at module top and — verified empirically in this review by running it twice
under `PYTHONHASHSEED=1` and `PYTHONHASHSEED=424242` — byte-deterministic
across hash seeds (all dict/set iteration feeding row selection goes through
`sorted(...)`; the `picked` set is always returned as `sorted(picked)`).
Largest-remainder stratification was re-derived by hand (57 rows / 4 classes
/ k=11 → 3/3/3/2) and matches. The dispatch run_record writer is ordered
after the CR-02 check and before `finalize_claim`, flows refusals through the
CR-04 containment with `accounted=False`, and its shape parity is asserted
against a REAL `run_matrix` run in tests. `pipeline/run_sweep.py` is
diff-empty against the base (frozen, verified), `.github/workflows/ci.yml`
blob hash matches the `33d2252eb594e0faecece9e8015a332d8d6479ef` pin, and
all 209 tests in the three suites pass locally (27 + 106 + 76; the D15-15
real-artifact tests ran, not skipped, on this box — runtime evidence the
15-05 fix produced `eval_f1` in all 12 real sweep cells).

Two defects are confirmed, both by execution rather than reading alone:

1. **CR-01 (Critical, data loss):** the subset generator enforces the D15-07
   isolation rule for `--registry-dir` only. Passing the same root as
   `--dataset-root` and `--output-root` makes the generator silently
   OVERWRITE the real benchmark dataset CSVs with 5% subsets — confirmed
   empirically in this review (40-row real CSVs replaced by 2-row subsets,
   exit 0). The generator's own docstring states the output root is "never a
   real-run root" (`script/make_subset_datasets.py:143`), but nothing
   enforces it — the exact asymmetry D15-07 closed for registries.
2. **WR-01 (Warning):** `write_cell_run_record`'s WR-11 corrupt-metrics
   branch catches only `json.JSONDecodeError`; a non-UTF-8 (or unreadable)
   `final_metrics.json` escapes it — confirmed empirically
   (`UnicodeDecodeError` propagates, NO run_record.json lands, and the CR-04
   containment rewrites the CLAIM failed), contradicting the docstring's
   "the claim STAYS completed ... the RECORD reports the honest failure"
   semantics and re-creating the record-less-cell shape 15-04 exists to
   eliminate. The sibling existing-record check at
   `pipeline/dispatch_core.py:1327` already catches all three flavors
   (`OSError`, `JSONDecodeError`, `UnicodeDecodeError`), showing the intended
   tolerance set.

The remaining findings are documentation-accuracy issues (IN-01..IN-04),
including one operational-semantics mismatch worth a maintainer's attention:
the dispatch no-overwrite predicate is documented as "the run_sweep.py:1614
parity" but run_sweep actually overwrites completed records on a
marker-deleted retrain, where dispatch refuses — recoverable, tested, and
loud, but not what "parity" implies (IN-02).

## Narrative Findings (AI reviewer)

### Critical Issues

### CR-01: Subset generator has no `--output-root` / `--dataset-root` isolation guard — equal roots silently destroy the real benchmark datasets

**File:** `script/make_subset_datasets.py:490,494-503` (writes); guard exists only at `:203-238` (`ensure_registry_isolation`, `--registry-dir` only)
**Issue:** `generate_subset_task` writes subset CSVs to
`Path(output_root) / official_entry["Dataset_path"] / f"{split}.csv"`. When
`--output-root` resolves to the same directory as `--dataset-root`, that
path IS the real dataset path, and every real `train/dev/test.csv` is
replaced by its 5% subset. Confirmed empirically during this review: a
40-row-per-split real tree passed with identical `--dataset-root` and
`--output-root` came back as 3-line files (header + 2 rows), exit 0, success
banner printed. The declared-vs-measured count guard cannot catch it — all
reads complete before the writes within each task. The datasets are
gitignored Zenodo/modelscope downloads (the repo's core input corpus), so
the loss is expensive to repair. The generator already resolves and refuses
the analogous collision for `--registry-dir` (official-dir
equals/contains, custom-dir equality, D15-07) and its docstring claims
"`--output-root` ... (never a real-run root)" — the invariant is stated but
not enforced. A single mis-set shell variable in the documented two-root
invocation (`--dataset-root <real> --output-root <subset>`) is enough.
**Fix:** extend the isolation refusal to the dataset tree — after
`ensure_registry_isolation(args.registry_dir)`, resolve both roots and
refuse equality before any file is opened (resolve() also covers symlink
aliases; equality is the exact collision condition since both sides join
the same `Dataset_path`):

```python
def ensure_output_isolation(dataset_root, output_root):
    """Refuse a subset output root that IS the real dataset root (D15-07)."""
    resolved_out = Path(output_root).expanduser().resolve()
    resolved_in = Path(dataset_root).expanduser().resolve()
    if resolved_out == resolved_in:
        raise SystemExit(
            f"[Error] --output-root {resolved_out} equals --dataset-root "
            f"{resolved_in} — the subset would overwrite the REAL dataset "
            "CSVs; subsets must land under a dedicated root (D15-07)"
        )
```

Call it in `main()` next to `ensure_registry_isolation`, and pin it with a
refusal test alongside `test_registry_dir_refusals`.

### Warnings

### WR-01: `write_cell_run_record` WR-11 branch misses `UnicodeDecodeError` — a non-UTF-8 corrupt `final_metrics.json` yields a record-less cell with the claim rewritten failed, contradicting the documented semantics

**File:** `pipeline/dispatch_core.py:1295-1308`
**Issue:** The corrupt-metrics handler is
`except json.JSONDecodeError as exc:` over
`json.load(handle)` on a UTF-8 text handle. A file with invalid UTF-8 bytes
raises `UnicodeDecodeError` (a `ValueError`, not a `JSONDecodeError`), which
escapes the handler. Empirically confirmed during this review: calling
`write_cell_run_record` with a completed payload and a
`final_metrics.json` containing an invalid continuation byte raises
`UnicodeDecodeError`, no `run_record.json` is written, and the exception
lands in the CR-04 containment — so the CLAIM is rewritten
`failed` with a dispatcher-side error. That contradicts the function's own
documented contract ("a corrupt/unparseable `final_metrics.json` on a
completed claim flips the RECORD to failed ... while the CLAIM STAYS
completed") and re-creates the invisible/record-less failed-cell shape the
15-04 gap fix set out to eliminate (still loud: counts.failed, exit 1,
re-runnable via `--rerun-failed`). Honest scope note: `run_finetune.py`
dumps metrics with `ensure_ascii=True` (default), so its own mid-write
truncations produce valid-UTF-8 prefixes that DO hit the handled
`JSONDecodeError` path; the unhandled flavor needs a non-UTF-8 or unreadable
file from another writer (manual edit, external tool, FS corruption). The
sibling existing-record check at `:1327` already catches
`(OSError, json.JSONDecodeError, UnicodeDecodeError)`, so the intended
tolerance set exists in this very function. (An `OSError` on the open has
the same escape shape; folding it in is defensible since existence was just
verified by CR-02 — keeping it propagating is also acceptable if the
containment path is preferred, but then the docstring should say so.)
**Fix:**

```python
        try:
            with open(cell_dir / run_sweep.METRICS_NAME, "r",
                      encoding="utf-8") as handle:
                record["metrics"] = json.load(handle)
            record["status"] = "completed"
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            # WR-11 (the run_sweep.py:1570-1591 parity): ...
            record["status"] = "failed"
            record["error"] = (
                "final_metrics.json is corrupt/unreadable "
                f"({exc}); the child left a partial file")
```

### Info

### IN-01: Generator "See also" mis-points, and the subset-consuming workflow is undocumented outside `.planning/`

**File:** `script/make_subset_datasets.py:93-94`; `docs/multi-gpu.md:228-232`
**Issue:** The generator's docstring says `docs/multi-gpu.md` documents "the
dispatch-mode smoke procedure that consumes these subsets via
`--dataset_root`" — but the rewritten doc's smoke explicitly uses FULL data
("全量 2110/234/2344 行——冒烟不依赖任何子集机制", `docs/multi-gpu.md:232`),
and no file under `docs/` mentions `make_subset_datasets`,
`pipeline/datasets-smoke/`, or `pipeline/registry-smoke/` (grepped). The
subset-consuming 12-cell sweep procedure exists only in phase artifacts.
For a public-release milestone this re-creates the repo's own documented
anti-pattern ("data regeneration is implicit tribal knowledge"), and it
amplifies CR-01 by leaving the safe two-root invocation outside the docs
tree.
**Fix:** Either point the "See also" at the actual phase artifact, or add a
short "subset smoke" subsection to `docs/multi-gpu.md` carrying the real
generator + dispatch commands (distinct `--dataset-root` / `--output-root` /
`--registry-dir`), ideally alongside the CR-01 guard.

### IN-02: "run_sweep.py:1614 parity" claim for the no-overwrite predicate is inaccurate — run_sweep OVERWRITES completed records on retrained cells; dispatch refuses

**File:** `pipeline/dispatch_core.py:1258-1267` (docstring), compare `pipeline/run_sweep.py:1614-1615`
**Issue:** run_sweep's write predicate is
`if record["status"] != "skipped" or not record_path.exists(): _write_json(...)`
— for any cell it actually RUNS (marker absent), it overwrites whatever
record is there, COMPLETED included. Dispatch instead raises
`FileExistsError` for a parseable completed record. The refusal itself is
deliberate, named, and pinned by
`test_dispatch_refuses_to_overwrite_completed_record`; but calling it "the
run_sweep.py:1614 parity" misdescribes the frozen engine's behavior, and
the operational difference is real: the marker-delete-forced retrain flow
that works under `run_matrix` (delete `trainer_state.json`, re-run) can
NEVER complete under dispatch until `run_record.json` is also removed
manually — the operator discovers this only through the failed-claim error
text. That is a defensible strictness, but it should be documented as a
divergence, not a parity.
**Fix:** Reword the docstring (and the `FileExistsError` message's
"(WR-12, the run_sweep.py:1614 parity)" tag) to "deliberately stricter than
run_sweep.py:1614, which overwrites records for retrained cells" and note
the manual record-removal step required to force a retrain through
dispatch.

### IN-03: Stale line citations in docs/multi-gpu.md after this phase's edits

**File:** `docs/multi-gpu.md:22`
**Issue:** The DDP-seam table cites `pipeline/run_finetune.py:1436` for the
`WORLD_SIZE` read (actual line: 1450) and `:1621` for `LOCAL_RANK` (actual:
1635). The citations drifted as run_finetune.py changed shape over phases
(including 15-05's insertions above them).
**Fix:** Update to `:1450` and `:1635`, or switch to anchor-style citations
("the `WORLD_SIZE` read in the dataset loop") that survive edits.

### IN-04: Success banner printed before the all-refused error exit

**File:** `script/make_subset_datasets.py:571-577`
**Issue:** When every task is refused, `main()` first prints
"✅ 0 subset dataset(s) written under ... ; registry: ..." and only then
raises `SystemExit("[Error] N task(s) refused — see the [Skip] lines
above")". The success emoji + completed-registry phrasing followed by an
error is confusing operator output (the registry is NOT written when
`subset_entries` is empty).
**Fix:** Move the banner inside the `if subset_entries:` block (or gate it
on `not failed`) so a fully-refused run ends on the error line only.

---

_Reviewed: 2026-10-21T00:39:46Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
