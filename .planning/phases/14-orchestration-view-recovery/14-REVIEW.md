---
phase: 14-orchestration-view-recovery
reviewed: 2026-10-20T12:15:25Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - pipeline/dispatch_core.py
  - pipeline/run_sweep_shard.py
  - schemas/dispatch_state.json
  - script/export_runs.py
  - tests/test_dispatch_core.py
  - tests/test_export_runs.py
  - tests/test_sweep_shard.py
  - tests/tui/test_services_about.py
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 14: Code Review Report

**Reviewed:** 2026-10-20T12:15:25Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Reviewed the Phase 14 surface (MGPU-03/04/05): the `dispatch_state.json` v2
consumer contract + renderer (`dispatch_core.py`, `schemas/dispatch_state.json`),
the cleanup mode with its dual verification legs and typed-phrase gate
(`run_sweep_shard.py`, `export_runs.py --dry-run`), the ledger-driven
`--rerun-failed` with claim genealogy (`dispatch_core.py`), and the four test
files.

**Verified sound** (adversarially probed, no defects found):

- **Frozen contracts untouched** — `git diff d1713b2..HEAD` over
  `pipeline/run_sweep.py` / `pipeline/run_finetune.py` is empty; static-mode
  argv/kwargs remain byte-identical (pinned by
  `test_mode_static_explicit_matches_default` and
  `test_static_mode_explicit_pins_argv_roots_and_logs`).
- **Stdlib-headless** — neither `dispatch_core.py` nor `run_sweep_shard.py`
  imports numpy/yaml/scipy/torch at module top; `export_runs.py` is reached
  only via `sys.executable` subprocess (`_EXPORT_RUNS_SCRIPT` +
  `run_cleanup` leg A); `export_runs.main` gates `--dry-run` before any write.
- **Schema/writer agreement** — every key the writer emits
  (`_launch_and_drain`/`_publish_state`/`_spawn_worker`) satisfies
  `schemas/dispatch_state.json` (`additionalProperties: false` at all three
  levels, the `oneOf` null/object `cellKey`, `status` enum); the snapshot
  invariant holds at every write because `queue_depth` is derived and every
  mutating transition publishes under `state_lock` (the SC3-skip path mutates
  counts without publishing, but every *written* payload satisfies the
  identity and the terminal write corrects the counts).
- **Deletion gate** — removal is offered only after BOTH legs (export
  subprocess returncode + manifest cell-set equality), the target list is
  exactly `{root}-mgpu-w{i}` roots plus their `*.log` siblings (glob-escaped,
  never the merged root; symlinked dirs make `rmtree` refuse loudly), and the
  phrase is the *resolved* root string with EOF/mismatch/non-interactive all
  refusing. Dispatch roots refuse before any verification.
- **Genealogy discipline** — `archive_superseded_claim` is `O_EXCL`
  (double-archive refuses loudly, pre-check + structural backstop); the
  canonical-slot replace is `tmp`+`os.replace` (the `.json.tmp` name never
  matches the ledger's `*.json` glob); `rerun_of` integrity is test-pinned
  (`test_rerun_failed_d14_15_two_worker_fixture`); heterogeneous lanes,
  forged registry models, and stale-claim replay parity all refuse or replay
  by design.
- **Composition** — `build_argv`/`cell_dir_for`/`base_model_name`/
  `_validate_filters` signatures and semantics in `dispatch_core` match
  `run_sweep` exactly; the flag-problems mirror (ebs/epochs/empty-path flags/
  variant×peft) is faithful to `run_sweep.main`'s collect-all.

No Critical findings. Three Warnings (robustness/observability gaps, each
with a concrete fix) and three Infos follow.

## Warnings

### WR-01: Launch-time state-publish failures leak the dispatcher lock and crash with a raw traceback

**File:** `pipeline/dispatch_core.py:1609-1635`
**Issue:** Inside `_launch_and_drain`, three `_publish_state(context)` calls
execute AFTER `acquire_dispatcher_lock` but BEFORE the `try/finally` that
guarantees `release_dispatcher_lock` (the mode-evidence write at line 1609,
the post-skip-filter write at line 1623, and the nothing-to-do path at lines
1633-1635 where the publish precedes the explicit release). An OSError from
any of them (ENOSPC/EACCES on the root — the same failure class the CR-04
containment was built for in workers) propagates as an unhandled traceback,
and `dispatcher.lock` is left on disk naming this run.

Contrast the sibling failure path: the tee-open refusal
(`run_sweep_shard`-style, lines 1656-1660) converts to a clean `sys.exit`
whose message explicitly states "the dispatcher lock is released", and the
`finally` (1672-1678) actually releases it. The launch-time publishes have no
such handling — an asymmetry inside the same function.

Self-healing exists (the crashed process dies, so the next launch reclaims
via the dead-pid probe; a pid-reuse false refusal is the safe direction), so
this is robustness, not data loss — but the module's own discipline is that
lock release is guaranteed on every exit path after acquisition.

**Fix:** Wrap the pre-drain publishes so an I/O failure releases the lock and
exits with the designed diagnostic:

```python
try:
    _publish_state(context)  # BEFORE any claim (mode evidence)
except OSError as exc:
    release_dispatcher_lock(lock_path)
    sys.exit(
        f"[Error] writing dispatch state failed: {exc} — no children "
        "spawned; the dispatcher lock is released"
    )
```

Apply the same guard to the line-1623 write and to the nothing-to-do publish
(moving the release into a `finally` around that block also works).

### WR-02: `--rerun-failed` silently drops corrupt / integrity-failing failed claims from the re-run feed

**File:** `pipeline/dispatch_core.py:1297-1311` (`_scan_failed_claims`)
**Issue:** The scan `continue`s without any diagnostic for: an unparseable
claim (1302-1303), a non-object payload (1304-1305), and — its own
integrity check — a claim whose stored cell key disagrees with its filename
(1309-1310). A failed cell whose claim is corrupt (disk fault, hand
tampering) therefore vanishes from the re-run set entirely: when it is the
only failed claim, `--rerun-failed` prints "no failed cells to re-run …
nothing spawned" and exits 0 — a green verdict that masks a never-re-run
failed cell, with nothing in the output naming the excluded file.

The tolerant-read contract ("corrupt claims contribute nothing and are never
trusted") is the right fail-safe direction, but silently. The relaunch path's
counterpart is test-pinned as "never a silent skip"
(`test_malformed_claims_requeue_never_crash_never_skip` — malformed claims
REQUEUE there), and the repo's own per-file convention is a named `[Skip]`
message (CLAUDE.md, `script/get_task_performance.py`). The recovery tool
whose entire job is completeness over the failed set should say what it
excluded.

**Fix:** Collect excluded files and name them (never re-queue them — trust
direction stays fail-safe):

```python
skipped = []
...
except (OSError, json.JSONDecodeError, UnicodeDecodeError):
    skipped.append(f"{path.name} (unreadable/unparseable)")
    continue
...
if skipped:
    print(f"[Rerun] [Skip] {len(skipped)} unusable claim(s) excluded from "
          f"the re-run feed: {'; '.join(sorted(skipped))}")
return qualified, skipped  # or print inside _scan_failed_claims
```

At minimum, when `qualified` is empty but exclusions occurred, the
"no failed cells to re-run" verdict should distinguish "ledger holds no
failed claims" from "ledger holds only unusable claims".

### WR-03: The re-run branch skips the startup validation family — a stale replayed lane burns one child per cell

**File:** `pipeline/dispatch_core.py:1387-1416` (`_run_rerun_failed`)
**Issue:** The ordinary dispatch path pre-validates the subset map ONCE at
startup (`run_sweep._validate_subset_file`, lines 1935-1938, citing WR-01:
"never one burned child launch per cell recorded as N cell failures") and
runs `_validate_dataset_name_alignment`. The re-run branch replays
`subset_file` (and the storage roots) verbatim from claim-time lanes but
performs neither check — it joins the registry (`_validate_filters`) and
proceeds straight to launch. If the subset map has been deleted or moved
since the original run, every re-run cell spawns a `run_finetune.py` child
that dies at its own per-cell validation, recording N failed claims and exit
1 — reintroducing exactly the burned-children hazard WR-01 was written to
prevent, on the recovery path where the operator is already chasing failures
(and re-running `--rerun-failed` repeats the burn loop, since the claims stay
failed).

The registry view is already the current one for the re-run (T-14-07 joins
failed cells' models against the current registry), so validating the
replayed subset map against the same view is consistent, not a fidelity
break.

**Fix:** In `_run_rerun_failed`, after resolving the agreed lane and before
`_launch_and_drain`, mirror the ordinary path:

```python
agreed = next(iter(signature_groups.values()))[0]
subset = agreed.get("subset_file")
if subset is not None:
    run_sweep._validate_subset_file(
        subset, registry_loader.load_datasets_registry(registry_dir))
run_sweep._validate_dataset_name_alignment(
    registry_loader.load_datasets_registry(registry_dir))
```

## Info

### IN-01: Archive-filename "injective" claim is probabilistic (8-hex-char run_id prefix)

**File:** `pipeline/dispatch_core.py:429-445` (`_archive_filename`)
**Issue:** The name is keyed by `original_run[:8]` — 32 bits of a uuid4 hex.
Two attempts of the same cell whose run_ids collide on the first 8 hex chars
(~2^-32 for the dispatcher's uuid4 ids; higher for hand-authored short
run_ids like the tests' `"phase13run"`) map to one archive name. The failure
mode is safe — the `O_EXCL` create raises `FileExistsError` and the re-run
refuses loudly, never an overwrite — but the docstring's "the name is
injective across attempts" is overstated; it is injective with overwhelming
probability. Fix: either soften the docstring ("injective except for a
~2^-32 run_id prefix collision, which refuses loudly") or key the archive on
the full run_id (the filename length is the only cost).

### IN-02: Re-run genealogy silently degrades if the canonical claim vanishes between scan and claim

**File:** `pipeline/dispatch_core.py:946-967` (`_spawn_worker`, `_TAG_RERUN` branch)
**Issue:** The genealogy step triggers only on `claim_cell` returning None
(EEXIST). If the canonical failed-claim file is deleted between
`_scan_failed_claims` and the worker's claim step (external mutation of the
ledger mid-run — out of the single-writer contract, but the scan/claim gap
is real wall-clock time), `claim_cell` succeeds and the cell runs as a fresh
claim with NO `rerun_of` link and no archive — the append-only audit trail
silently loses the attempt instead of refusing. The EEXIST branch's unusable
original raises loudly; the no-EEXIST branch has no equivalent guard. Fix:
in the `_TAG_RERUN` branch, when `claim_cell` SUCCEEDS (no collision), fail
the cell loudly ("the canonical failed claim disappeared mid-run — ledger
mutated under the dispatcher; refusing") or at minimum emit a diagnostic
naming the genealogy loss.

### IN-03: Cleanup echoes only the last stdout line of the export dry-run

**File:** `pipeline/run_sweep_shard.py:1371-1373` (`run_cleanup`, leg A)
**Issue:** `dry_lines[-1]` surfaces only the final line of the export
subprocess's stdout. Today the dry-run prints exactly one line so this is
fine, but any future multi-line output (warnings, per-model counts) is
dropped from the operator echo — the full output is only ever visible on
FAILURE (via the captured tail). Cosmetic/forward-compatibility: echo the
full captured stdout (it is already in hand) or at least keep the last-line
behavior behind a comment pinning the one-line contract.

---

_Reviewed: 2026-10-20T12:15:25Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
