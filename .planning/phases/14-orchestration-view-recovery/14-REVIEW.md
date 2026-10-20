---
phase: 14-orchestration-view-recovery
reviewed: 2026-10-20T12:51:03Z
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
  warning: 0
  info: 4
  total: 4
status: issues_found
---

# Phase 14: Code Review Report (Re-review, iteration 2)

**Reviewed:** 2026-10-20T12:51:03Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found (0 Critical, 0 Warning; 3 carried Info + 1 new Info)

## Summary

Post-fix re-review of the Phase 14 surface (MGPU-03/04/05) at standard depth.
All three iteration-1 Warnings were re-traced against their fix commits
(1a984b4, 528a165, 1680ae2): **all three fixes hold**, and the fixes
introduced **no new Critical or Warning issues**. The three known Info items
(IN-01/IN-02/IN-03, recorded as skipped in REVIEW-FIX.md) are still present
and carried as Info per instruction; one new minor Info (IN-04) is recorded.

Test evidence (executed in this review, `.venv`):

- `tests/test_dispatch_core.py` — 98 passed
- `tests/test_sweep_shard.py` — 62 passed
- `tests/tui/test_services_about.py` — 21 passed
- `tests/test_export_runs.py` — 28 passed, 1 deselected
  (`test_d15_evaluate_cross_validates_suite_mapped_metric_conventions` —
  network-gated on `evaluate.load()`; unchanged from before the diff base,
  outside the changed hunks; blocked in this sandbox, not a code signal)

## Fix Verification (iteration 1 → iteration 2)

### WR-01 — pre-drain state publishes guarded; lock release guaranteed — VERIFIED FIXED

**Fix:** `_publish_state_pre_drain` (`pipeline/dispatch_core.py:886-915`)
catches `OSError`, calls `release_dispatcher_lock`, then `sys.exit`s with the
tee-shaped diagnostic ("no children spawned; the dispatcher lock is
released").

**Exception-window trace (every path between `acquire_dispatcher_lock`
(:1632) and the drain's `try/finally` (:1741-1775)):**

1. Lock acquire → mode-evidence publish (:1705): pure dict/Path building;
   `gpus[i]` indexing (:1664) is arity-validated pre-lock
   (`run_dispatch` :1874-1878 / `_run_rerun_failed` :1887). No I/O.
2. Mode-evidence publish: **guarded**.
3. Publish #1 → post-skip-filter publish (:1720): the `relaunch_decision`
   loop is read-only and tolerant (`marker.exists()` never raises;
   `read_claim` catches `OSError/JSONDecodeError/UnicodeDecodeError`). No
   writes.
4. Post-skip-filter publish: **guarded**.
5. Nothing-to-do branch (:1726-1738): guarded terminal "done" publish, then
   the explicit release. On failure the guard releases and exits (the
   explicit release is never reached — no double-release concern; release is
   idempotent regardless, tolerating a missing file).
6. Tee opens (`mkdir` + `open`) inside the inner `try/except OSError` →
   `sys.exit` (:1754) → unwinds through the OUTER `finally` (:1769-1775):
   opened tees closed, lock released. The message's "lock is released" claim
   is accurate.
7. Residual (pre-existing, by design, NOT a leak introduced here):
   `acquire_dispatcher_lock`'s own create-to-write window (:688) — a failed
   payload write after a successful `O_EXCL` create leaves a fresh empty
   lock; the CR-02 grace window (:175, :648-660) refuses reclaim for 5s then
   self-heals. Documented contract.

Guard-scope check: `_publish_state` raises `OSError` only in practice —
`_atomic_write_json` failures are `OSError`; `_render_state` swallows its own
output failures (`BrokenPipeError/OSError/ValueError`, :828-833); the dict
keys it reads are writer-set. `_publish_state_pre_drain` catching `OSError`
therefore covers the guard's stated failure class.

Test pin: `test_launch_state_publish_failure_releases_lock_exits_cleanly`
(parametrized over publish sites 1/2/3, drained and not) — passes; asserts
lock gone, zero children, designed message.

### WR-02 — excluded unusable claims named; never re-queued, never silently dropped — VERIFIED FIXED

**Fix:** `_scan_failed_claims` (`pipeline/dispatch_core.py:1309-1358`)
returns `(qualified, excluded)`; every exclusion class appends a
`"{name} ({reason})"` diagnostic (unreadable/unparseable; payload not an
object; state-failed with unusable/identity-disagreeing cell key).

**Trace:**

- **Never re-queued:** `pending` is built solely from `qualified`
  (:1579-1586); excluded files never enter the feed, and the worker's
  genealogy step never touches them — the e2e test pins the archive holds
  exactly one file (the usable cell's original) when three unusable claims
  sit in the same ledger.
- **Never silently dropped:** `[Rerun] [Skip] N unusable claim(s) excluded
  from the re-run feed: …` prints at :1453-1456 with every name+reason; the
  zero-qualified verdict distinguishes "the ledger holds 0 usable failed
  claim(s) (N excluded as unusable, named above)" from "the ledger holds no
  failed claims" (:1462-1474), both exit 0.
- The marker-skip of a qualified cell (D-06 adjacency) is accounted, not
  silent: it lands in `counts.skipped` in the run's state file and verdict.
- Sole call site updated (return-shape change); no other callers (verified by
  grep; the scan is engine-internal).

Test pin: `test_rerun_names_excluded_unusable_claims_never_silently_drops`
(all three exclusion classes + only-unusable ledger verdict) — passes.

### WR-03 — replayed-lane startup validation before any child spawns — VERIFIED FIXED

**Fix:** `pipeline/dispatch_core.py:1514-1530` — after the heterogeneous-lane
refusal and BEFORE the archive-collision pre-check, the pending build, and
`_launch_and_drain`: `_validate_subset_file(replayed_subset,
registry_loader.load_datasets_registry(registry_dir))` when the agreed lane
carries a `subset_file`, plus `_validate_dataset_name_alignment` over the
same view.

**Trace:**

- **Ordering:** `_launch_and_drain` is the only child-spawning machinery
  (lock, state file, tees, worker threads all live inside it, :1627+). The
  validation precedes it — and therefore precedes lock acquisition, the
  `dispatch_state.json` write, and every spawn. Tests assert `calls == []`
  and `not (base / DISPATCH_STATE_NAME).exists()`.
- **Lane-uniformity:** the preceding D14-08 homogeneity check projects every
  qualified claim's lane onto the union key set, so `agreed_lane.get(
  "subset_file")` is uniform across the replay set; `is not None` preserves
  the Pitfall-4 absent-parity (a lane lacking the key, or recording `None`,
  replays with zero argv elements and skips the map validation — correct).
- **View consistency:** the same `registry_dir` view the T-14-07 registry
  join used — consistency, not a fidelity break (documented in-code).
- Refusal loudness confirmed against the validators: a deleted map exits
  `"[Error] cannot read --subset_file file …"`; a diverged `Dataset_name`
  row exits naming the rows (both re-verified in `run_sweep.py:666-748,
  794-826`).

Test pin: `test_rerun_validates_startup_family_before_any_launch` (legs A:
deleted map / B: valid-map control threads to argv / C: divergent registry) —
passes.

### No new Critical/Warning from the fixes

- WR-01 diff: adds one helper + rewrites three call sites; no behavior change
  on the success path; no new call graph edges.
- WR-02 diff: return-shape change with the single call site updated; the
  exclusion strings are static non-empty diagnostics.
- WR-03 diff: two validator calls inserted between existing refusals; both
  are stdlib, read-only, and already exercised on the ordinary path.
- Full phase suites re-run green (counts above); the frozen-contract,
  stdlib-headless, O_EXCL/genealogy, deletion-gate, and static-mode
  byte-identity invariants from iteration 1 were spot-re-verified unchanged
  (`_root_has_dispatch_evidence` markers, `run_cleanup` leg structure,
  `_canonical_lane_value`, MERGE_ALLOWLIST, spawn kwargs).

## Info

### IN-01: Archive-filename "injective" claim is probabilistic (8-hex-char run_id prefix) — CARRIED

**File:** `pipeline/dispatch_core.py:429-445` (`_archive_filename`)
**Issue:** Still present, unchanged. The name keys on `original_run[:8]`
(32 bits of a uuid4 hex); a prefix collision between two attempts of the
same cell maps to one archive name. The failure mode is safe (`O_EXCL`
refuses loudly — append-only protected, never an overwrite), but the
docstring's "injective across attempts" is overstated. **Fix:** soften the
docstring or key on the full run_id. (Known item; recorded as skipped in
REVIEW-FIX.md.)

### IN-02: Re-run genealogy silently degrades if the canonical claim vanishes between scan and claim — CARRIED

**File:** `pipeline/dispatch_core.py:966-999` (`_spawn_worker`, `_TAG_RERUN`
branch)
**Issue:** Still present, unchanged. Genealogy (archive + `rerun_of`) fires
only on the `claim_cell` EEXIST; if the canonical failed-claim file is
deleted between `_scan_failed_claims` and the worker's claim step, the
re-run proceeds as a fresh claim with no link and no archive — the audit
trail loses the attempt without a diagnostic (the EEXIST-with-unusable-
original path refuses loudly; this path has no equivalent). **Fix:** when
`claim_cell` succeeds for a `_TAG_RERUN` cell, fail the cell loudly or emit
a genealogy-loss diagnostic. (Known item; recorded as skipped in
REVIEW-FIX.md.)

### IN-03: Cleanup echoes only the last stdout line of the export dry-run — CARRIED

**File:** `pipeline/run_sweep_shard.py:1371-1373` (`run_cleanup`, leg A)
**Issue:** Still present, unchanged. `dry_lines[-1]` surfaces only the final
stdout line; multi-line future output would be dropped from the operator
echo (full output is only visible on failure via the captured tail).
**Fix:** echo the full captured stdout or pin the one-line contract behind a
comment. (Known item; recorded as skipped in REVIEW-FIX.md.)

### IN-04: `_validate_rerun_passthrough` accepts a flag-shaped `--registry-dir` value where the mirrored argparse path refuses — NEW (minor)

**File:** `pipeline/dispatch_core.py:1268-1283` (`_validate_rerun_passthrough`)
**Issue:** For a remainder like `["--registry-dir", "--bogus"]`, the scanner
consumes `"--bogus"` as the registry-dir VALUE and appends no problem —
diverging from the argparse semantics the module otherwise mirrors
(`parse_sweep_remainder` over the same tokens exits 2 with "expected one
argument"). The failure stays loud downstream (the bogus dir has no official
registry, so `_load_registry`'s uncaught `OSError` tracebacks — the same
shape the ordinary path produces for any nonexistent registry dir), so this
is a strictness/consistency gap in a validator whose purpose is collect-all
refusals, not an incorrect-accept of a runnable configuration. Note
orchestrator-owned flags (`--workers`, `--merge`, …) are consumed by the
shard parser before the remainder forms, so the shape requires an
UNRECOGNIZED flag-shaped token after `--registry-dir`.
**Fix:** treat a next token starting with `--` as a missing value (append
the "requires a value" problem) instead of consuming it.

---

_Reviewed: 2026-10-20T12:51:03Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
_Iteration: 2 (post-fix re-review of WR-01/WR-02/WR-03; all verified fixed)_
