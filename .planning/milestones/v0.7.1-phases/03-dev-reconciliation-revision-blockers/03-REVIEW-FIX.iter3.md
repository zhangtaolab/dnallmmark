---
phase: 03-dev-reconciliation-revision-blockers
fixed_at: 2026-10-10T02:18:46+08:00
review_path: .planning/phases/03-dev-reconciliation-revision-blockers/03-REVIEW.md
iteration: 2
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 03: Code Review Fix Report

**Fixed at:** 2026-10-10
**Source review:** `.planning/phases/03-dev-reconciliation-revision-blockers/03-REVIEW.md` (iteration 2)
**Iteration:** 2 (this report is the cumulative final fix report; iteration-1 dispositions are carried forward below)
**Scope:** critical_warning per config, further narrowed by the maintainer directive to this iteration's in-scope set: **WR-11, WR-12, WR-13** (all empirically demonstrated by the reviewer against the real `run_sweep.run_matrix` / `run_finetune.py` write ordering)

**Summary:**
- Findings in scope: 3 (all Warning)
- Fixed: 3
- Skipped: 0
- Out of scope, documented open: IN-01..IN-08 (critical_warning scope excludes Info; left for Phase 4 routing)
- Deferred/locked honored, untouched: WR-03/WR-04 (Phase-4 quirk parity), WR-09 (false premise, resolved), the three `xfail(strict=True)` locks in `tests/test_known_defects.py`

All three fixes are in the sweep/finetune interplay and each ships with a regression test pinning the corrected behavior.

## Fixed Issues

### WR-11: Corrupt/truncated final_metrics.json aborts the entire sweep instead of recording a failed cell

**Files modified:** `pipeline/run_sweep.py`, `tests/test_sweep.py`
**Commit:** `062f72e`
**Applied fix:** The metrics read in `run_matrix`'s success branch is now guarded: a `final_metrics.json` that is present but not valid JSON — reachable because `run_finetune.py` writes it inside its D-08 blind-except scope, so a mid-write death (e.g. disk full) leaves a truncated file with the child still exiting 0 — is recorded as a **failed** cell (error text naming the corruption, entry in `sweep_failures.json`) and the sweep **continues**, instead of an uncaught `JSONDecodeError` escaping the `(SubprocessError, OSError)` boundary and aborting every remaining cell with no manifest ever written. `record["status"]` is now set to `"completed"` only after a successful parse. An `OSError` from the read itself still propagates to the existing outer boundary (recorded failed) — unchanged. The module docstring's "Failure boundary" section and the `run_matrix` docstring now enumerate the corrupt-file case explicitly (child-data corruption, not a driver bug). New test `test_run_matrix_corrupt_metrics_file_fails_cell_not_sweep` pins: seed-42 cell with truncated JSON → failed + failures entry; seed-43 cell → completed; manifest written with `["failed", "completed"]` (pre-fix this test dies with `JSONDecodeError` before any manifest exists).

### WR-12: Resume skip overwrites a completed cell's run_record.json, destroying its provenance

**Files modified:** `pipeline/run_sweep.py`, `tests/test_sweep.py`
**Commit:** `43acfa8`
**Applied fix:** The per-cell `run_record.json` write is no longer unconditional: a **skipped** cell never overwrites an existing record. The on-disk record of the run that actually trained (or failed) the cell — status, verbatim metrics, `git_commit`, `started_at`/`finished_at` — is the only provenance linking the cell's outcome to the run that produced it ("recorded once at observation time, never regenerated", per the module docstring); this run's skipped view is reported by `sweep_manifest.json` only. A skipped cell with **no** record yet (e.g. a standalone `run_finetune.py` invocation left the marker but no record) still gets a fresh one — pinned by the pre-existing `test_run_matrix_resume_marker_is_seed_scoped`, which stays green. This also stops the WR-13 compounding effect: a cell recorded `failed` in run 1 keeps its failure record after later sweeps skip it. Docstrings updated (module runtime-observation section + `run_matrix`). New test `test_resume_never_overwrites_existing_run_record` runs two `run_matrix` passes over the same root (fake executor writes metrics + marker on run 1; a never-invoke executor on run 2) and asserts the on-disk record is byte-identical to run 1's completed record while the manifest reports `skipped`.

### WR-13: Resume marker written before final_metrics.json — a kill in the window permanently marks an incomplete cell as done

**Files modified:** `pipeline/run_finetune.py`, `tests/test_run_finetune_contracts.py`
**Commit:** `dbabb8b`
**Applied fix:** In the `local_rank == 0` success block of the training loop, the write order is swapped: `final_metrics.json` is written **first**, and the `trainer_state.json` completion marker is copied **last** — the marker (read by `run_finetune.py`'s own resume check and `run_sweep.py`'s skip check) must be the final act of a successful cell, so a process death between the two writes (OOM killer, SIGKILL, power loss; Ctrl-C's `KeyboardInterrupt` also lands here since `except Exception` does not catch it) leaves a cell with **no** marker, which the next sweep re-runs — never a permanently done-with-no-metrics cell. A why-comment records the ordering contract at the site. New source-contract test `test_final_metrics_written_before_resume_marker` pins that the metrics write precedes the marker copy (same read-source-never-import pattern as the file's other contracts; `run_finetune.py` cannot be imported CPU-side).

## Out of Scope (documented open)

- **IN-01..IN-08** — all Info-tier; excluded by `fix_scope: critical_warning` and the maintainer directive. IN-06 is a documented maintainer decision (D-08/AUDIT.md, Phase-6 retirement tracked); the others (IN-01 duplicated assignment, IN-02 split_task reuse, IN-03 --target_dataset stripping, IN-04 to_csv test coverage, IN-05 README labels, IN-07 CR-02 error wording, IN-08 lint scope) remain open for Phase 4 routing.
- **Deferred/locked (binding, untouched):** WR-03/WR-04 (Phase-4 quirk parity surface), the three `xfail(strict=True)` known-defect locks (AUD-01 species, comparator bool/int, non-finite `get_float`), WR-09 (false premise, stands resolved).

## Prior Round: Iteration 1 (carried forward)

Iteration 1 (source review of the same 19 files): 12 in scope, 9 fixed, 3 skipped. All 9 were verified correct+complete by the iteration-2 re-review. Full detail preserved in `03-REVIEW-FIX.iter2.md`.

| Finding | Disposition | Commit |
|---|---|---|
| CR-01 fp32-only model handling | fixed | `7c703a7` |
| CR-02 exit-0-no-metrics = failed | fixed | `9932727` |
| WR-01 grad_accum snapshot ordering | fixed | `725782b` |
| WR-02 dataset-dir presence guard | fixed | `8cd586d` |
| WR-05 make_dev_splits docstring narrowing | fixed | `db46c4e` |
| WR-06 always write sweep_failures.json | fixed | `52b0b3a` |
| WR-07 filter validation, non-zero exit | fixed | `0352311` (+ style follow-up `a00ae96`) |
| WR-08 README CWD / run_sweep docs | fixed | `af12068` |
| WR-10 mem_ratio passed to estimator | fixed | `f820423` |
| WR-03 ACGT-only alphabet | skipped: deferred to Phase 4 (maintainer-sanctioned) | — |
| WR-04 unported quirk registries | skipped: deferred to Phase 4 (maintainer-sanctioned) | — |
| WR-09 deprecation banner premise | skipped: false premise (git history contradicts it) | — |

## Verification

**Where the gates ran:** per-fix verification (ast syntax check + targeted pytest per touched test file + ruff over the touched files) ran inside the isolated worktree (`.claude/worktrees/rf-03-*`) using the main checkout's `.venv` interpreters (`ty` required `--python .venv/bin/python` there); the full suite was also run in the worktree pre-merge, and the **authoritative** gate run below ran in the **main checkout** after the three fix commits were fast-forwarded onto `autorun` — the numbers are reproducible from the tree as merged (`dbabb8b`).

- `make test` — pytest: **186 passed + 5 xfailed** (iteration-1 baseline 183 + 5, plus the 3 new tests added by WR-11/WR-12/WR-13); node lane: **2 pass / 0 fail**
- `make lint` (ruff over tests/ + the Phase-3-authored files) — **All checks passed**
- `make typecheck` (ty) — **All checks passed**

CODE-ONLY honored: no model runs, no GPU work, no installs (uv auto-sync was a no-op; no dependency files touched). `/home/forrest/Github/DNALLM` was never written to (read-only). The `xfail(strict=True)` locks were not touched.

## Commit Index (this iteration)

| Commit | Finding | Subject |
|---|---|---|
| `062f72e` | WR-11 | fail the cell on a corrupt final_metrics.json instead of aborting the sweep |
| `43acfa8` | WR-12 | never overwrite an existing run_record.json for a skipped cell |
| `dbabb8b` | WR-13 | write final_metrics.json before the trainer_state.json resume marker |

---

_Fixed: 2026-10-10_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 2_
