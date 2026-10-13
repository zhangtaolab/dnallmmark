---
phase: 12-multi-gpu-orchestration-console-hardening
fixed_at: 2026-10-13T14:57:13Z
review_path: 12-REVIEW.md
iteration: 1
findings_in_scope: 8
fixed: 8
skipped: 0
status: all_fixed
---

# Phase 12: Code Review Fix Report

**Fixed at:** 2026-10-13T14:57:13Z
**Source review:** `.planning/phases/12-multi-gpu-orchestration-console-hardening/12-REVIEW.md`
**Iteration:** 1
**Scope:** WR-01..WR-08 only (the three IN- items stay open per dispatch; not touched)

**Summary:**
- Findings in scope: 8
- Fixed: 8
- Skipped: 0

Every fix followed RED-then-GREEN TDD (a failing test naming the defect
committed conceptually with its fix, one atomic commit per finding) and
module-suite-only iteration per the maintainer speed directive
(`tests/test_sweep_shard.py`, `tests/tui/test_pilot_run_config.py`).

## Fixed Issues

### WR-01: `--gpus` is int-validated although documented as verbatim "operator-owned strings, ARITY-validated only"

**Files modified:** `pipeline/run_sweep_shard.py`, `tests/test_sweep_shard.py`
**Commit:** d8c54a8
**Applied fix:** `_parse_gpus` now keeps each stripped token as a verbatim
operator-owned string — the only malformed token is an EMPTY element (the
arity check is unchanged); the default assignment builds `"0".."N-1"`
strings and the spawn env forwards `gpus[i]` directly (no `str()` at the
spawn site). Code aligned to the documented contract (UUID / MIG ids now
forward verbatim, D-05). RED→GREEN:
`test_gpus_non_numeric_tokens_forward_verbatim` pins a
`MIG-GPU-…/1/0` token; the malformed-refusal case in
`test_gpus_problems_refuse_collect_all` became the empty-element case
(`"0,zero"` is now a legal operator string).

### WR-02: Frozen worker-log path opened `"w"` — a resume relaunch destroys the previous run's diagnostic log

**Files modified:** `pipeline/run_sweep_shard.py`, `tests/test_sweep_shard.py`, `docs/multi-gpu.md`
**Commit:** caa8f67
**Applied fix:** The launcher's per-launch timestamped-log idiom, as the
dispatch directed: `worker_log_path(base, i, timestamp)` returns
`{base}-mgpu-w{i}-{stamp}.log` (`WORKER_LOG_TIMESTAMP_FORMAT` copies the
launcher's `%Y%m%d_%H%M%S`), `main()` gains the launcher's injectable
`clock` seam, ONE stamp per launch names every worker log, and the
verdict table reports the log THIS launch teed into. `docs/multi-gpu.md`
runbook lines + the `--output-root` help text aligned; cleanup globs
become `-mgpu-w{0,1}-*.log`. RED→GREEN:
`test_resume_relaunch_never_truncates_prior_worker_log` pins the crash
evidence surviving a relaunch verbatim; the frozen-naming, argv-kwargs,
verdict-table, and both real-subprocess tests re-pin stamped paths with
deterministic clocks.

### WR-03: Re-merge over a previously-merged root with a changed worker set leaves stale cell files that downstream consumers will export

**Files modified:** `pipeline/run_sweep_shard.py`, `tests/test_sweep_shard.py`
**Commit:** 4c20d42
**Applied fix:** Refusal, not reconciliation (minimal safe fix per
dispatch): before the copy pass, the merge enumerates the merged root's
existing `MERGE_ALLOWLIST`-named files and refuses with a precise
diagnostic (count + up to 5 paths + the remedy) when any is not covered
by this merge's copy plan — the worker set changed and the stale cells
would leak into exported data because the exporter walks the file tree,
not the manifest. Identical worker sets stay idempotent (every
pre-existing allowlisted file IS in the plan; guard passes silently).
RED→GREEN: `test_remerge_with_changed_worker_set_refuses_on_stale_cells`
(manifest byte-unchanged after the refusal) + the positive control
`test_remerge_unchanged_worker_set_stays_idempotent_under_stale_guard`;
the existing byte-stable idempotency test keeps holding.

### WR-04: Unhandled `OSError` from `shutil.copyfile`/`mkdir` bypasses the designed merge-refusal message

**Files modified:** `pipeline/run_sweep_shard.py`, `tests/test_sweep_shard.py`
**Commit:** 0addc67
**Applied fix:** In `_copy_verified`, the `dst.parent.mkdir` +
`shutil.copyfile` pair is wrapped; an `OSError` (ENOSPC / EACCES /
read-only destination) converts to the mismatch path (`False`), landing
in the designed `[Error] … merge refused, merged manifests NOT written`
collect-all diagnostic instead of a raw traceback. RED→GREEN: unit test
pins `_copy_verified → False` on a raising copy; merge-level test pins
the designed diagnostic + no merged manifests on a `PermissionError` copy.

### WR-05: Lane-equality comparison canonicalizes Python sets via `json.dumps(..., default=str)` — hash-order-fragile

**Files modified:** `pipeline/run_sweep_shard.py`, `tests/test_sweep_shard.py`
**Commit:** 471656b
**Applied fix:** New `_canonical_lane_value`: sets/frozensets canonicalize
through `sorted()` before `json.dumps` (the old inline form serialized
`str(set)`, whose element order is the internal iteration order —
PYTHONHASHSEED-dependent across processes, insertion-history-dependent
even in one — so identical lanes could be falsely refused); everything
else keeps the sorted-keys form (`None → "null"` stays deterministic).
The lane-equality comparison in `run_merge` uses it. RED→GREEN:
`_ReversedIterSet` (a deterministic reversed-iteration stand-in for the
hash-order fragility) pins equal-content sets canonicalizing identically
plus the exact sorted-JSON canonical form; the existing unequal-lane
refusals keep holding. Classified "fixed: requires human verification"
semantics NOT needed — the property is pure-function pinned.

### WR-06: `--models` is silently ignored in merge mode

**Files modified:** `pipeline/run_sweep_shard.py`, `tests/test_sweep_shard.py`
**Commit:** 59fafaf
**Applied fix:** `run_merge`'s validation block refuses a provided
`--models` with the module's own collect-all pattern
(`--merge takes no --models (the worker manifests are the merge's source
of truth)`); the docstring's refusal list updated. RED→GREEN:
`test_merge_refuses_models_flag` pins the refusal, its message, and that
no merged manifest lands.

### WR-07: A marked-then-disabled custom model is stuck in the run spec — rendered unmarked, counted, launched, and impossible to unmark from the picker

**Files modified:** `tui/screens/run_config.py`, `tests/tui/test_pilot_run_config.py`
**Commit:** e788acb
**Applied fix:** Sanitize at load (the review's primary option):
`_sanitize_disabled_custom_marks` runs in `on_run_config_screen_loaded`
right after the entries land and drops disabled customs from BOTH spec
axes (`models` and `tasks` — `custom_status` covers dataset customs
too), so the spec agrees with the rendered marks; the first
preview-worker save persists the sanitized spec (the XDG state
self-heals). The render-side `and not is_disabled` suppression stays as
defense-in-depth. RED→GREEN: Pilot test pins the sanitized spec, the
status-line counts (render == spec), and the persisted saves over a
fixture with a disabled custom model AND a disabled custom dataset. No
SVG golden drift (the full `make test` snapshot suite passed — no
`make snapshot-update` needed).

### WR-08: Operator-facing copy composed in the screen module with CJK punctuation — bypasses the I18N-01 grep lock

**Files modified:** `tui/strings.py`, `tui/screens/run_config.py`, `tests/tui/test_pilot_run_config.py`, `tests/tui/test_strings_phase11.py`
**Commits:** ae303de (+ follow-ups 5a6855e lint alignment, 3bb2926 inventory registration)
**Applied fix:** The OFF-with-path copy shape moved wholly into
`tui/strings.py` (`CFG_SUBSET_OFF_WITH_PATH = "关（{path}）"`), the screen
renders it via `.format(path=path)` and the now-unused `CFG_SUBSET_OFF`
import leaves the screen module. The I18N grep lock in the Pilot suite
was extended to the CJK punctuation + fullwidth-form ranges
(`[一-鿿　-〿＀-￯]`, U+3000–U+303F + U+FF00–U+FFEF) so this class cannot
recur — the extended lock was the RED (it caught the two U+FF08/U+FF09
literals), green after the move. Lock scope: extended ONLY in this
suite's lock over `run_config.py` (the finding's module) — extending the
other suites' locks was not in scope. The phase-11 string inventory's
bidirectional lock required registering the new constant
(`3bb2926`). `test_params_defaults_render` now pins the exact constant
shape. I18N lock green.

## Skipped Issues

None — all 8 in-scope findings were fixed.

## Verification

- Per-fix: module suites only during iteration (maintainer speed
  directive) — `tests/test_sweep_shard.py` 41→49 tests green after each
  fix; `tests/tui/test_pilot_run_config.py` 47→48 green after each TUI
  fix.
- Final gate ONCE, run in the MAIN CHECKOUT (this fixer ran sequentially
  on the main working tree per the dispatch; no worktree, so the numbers
  are reproducible from the tree as-is): `make test` 1581 passed
  (0 failed; incl. the snapshot SVG goldens — no drift);
  `make lint` all checks passed (after the DTZ001/RUF100 follow-up
  5a6855e); `make typecheck` (ty) all checks passed.
- Standing constraint held: zero `pyproject.toml` / `uv.lock` /
  `requirements.txt` changes (verified in the final commit's diff
  scope).

---

_Fixed: 2026-10-13T14:57:13Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
