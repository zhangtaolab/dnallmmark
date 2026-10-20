---
phase: 14-orchestration-view-recovery
fixed_at: 2026-10-20T12:33:27Z
review_path: .planning/phases/14-orchestration-view-recovery/14-REVIEW.md
iteration: 1
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 14: Code Review Fix Report

**Fixed at:** 2026-10-20T12:33:27Z
**Source review:** .planning/phases/14-orchestration-view-recovery/14-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope (critical_warning): 3 (WR-01, WR-02, WR-03)
- Fixed: 3
- Skipped: 0
- Out of scope per fix_scope (Info, recorded below): 3 (IN-01, IN-02, IN-03)

**Binding constraints honored:** only `pipeline/dispatch_core.py` and
`tests/test_dispatch_core.py` changed (verified per-commit via
`git show --stat`); `run_sweep.py` / `run_finetune.py` untouched;
`run_sweep_shard.py` untouched (no deviation needed); static mode
byte-identity pins (`test_mode_static_explicit_matches_default`,
`test_static_mode_explicit_pins_argv_roots_and_logs`) pass unchanged;
stdlib-headless imports unchanged; fake children only; **no push** —
local commits only on `autorun`.

## Fixed Issues

### WR-01: Launch-time state-publish failures leak the dispatcher lock and crash with a raw traceback

**Files modified:** `pipeline/dispatch_core.py`, `tests/test_dispatch_core.py`
**Commit:** `1a984b4`
**Applied fix:** Followed the fix_hint's per-publish guard mechanism,
factored into one helper rather than three copies: new
`_publish_state_pre_drain(context, lock_path)` wraps `_publish_state`,
and on `OSError` releases the lock then `sys.exit`s with the designed
diagnostic (`[Error] writing dispatch state failed: {exc} — no children
spawned; the dispatcher lock is released` — the tee-open refusal's
shape). All three pre-drain call sites in `_launch_and_drain` route
through it: the mode-evidence write, the post-skip-filter write, and
the nothing-to-do branch's terminal `done` publish. (The alternative in
the hint — one `finally` around the whole pre-drain block — was not
used because the drain section already owns a release `finally`, and a
second one would double-release on the normal path.)
**Regression test:**
`test_launch_state_publish_failure_releases_lock_exits_cleanly`
(parametrized over all three publish sites) using the suite's
`_flaky_finalize` idiom — `_publish_fails_on_call` monkeypatches
`dispatch_core._publish_state` with `OSError(28, "No space left on
device")`. Asserts the diagnostic names the error, no children spawn,
and `dispatcher.lock` does not survive. Red/green proven: 3/3 FAIL
against pre-fix source (raw OSError, leaked lock), 3/3 PASS post-fix.

### WR-02: `--rerun-failed` silently drops corrupt / integrity-failing failed claims from the re-run feed

**Files modified:** `pipeline/dispatch_core.py`, `tests/test_dispatch_core.py`
**Commit:** `528a165`
**Applied fix:** Followed the fix_hint's return-shape option:
`_scan_failed_claims` now returns `(qualified, excluded)` where each
excluded entry is `"{name} ({reason})"` — reasons:
`unreadable/unparseable`, `payload is not an object`, and
`state failed but the stored cell key is unusable or disagrees with the
filename`. `_run_rerun_failed` prints the `[Rerun] [Skip] N unusable
claim(s) excluded ...` line naming every dropped file, and when
`qualified` is empty but exclusions occurred, the zero-failed verdict
distinguishes the realities ("holds 0 usable failed claim(s) (N
excluded as unusable, named above)") instead of the plain "holds no
failed claims" wording (which stays for clean ledgers, exit 0
unchanged). Trust direction unchanged: excluded claims are never
re-queued.
**Regression test:**
`test_rerun_names_excluded_unusable_claims_never_silently_drops` — one
ledger mixing a usable failed claim with all three exclusion classes
(every fixture under a real `claim_filename`): asserts the `[Skip]`
line names all three files with their reasons, exactly the usable cell
re-runs, only one genealogy archive exists (excluded cells never
re-queued); then a second root holding ONLY unusable claims asserts the
distinguished verdict (and that the plain wording is absent), exit 0,
nothing spawned. Red/green proven: FAIL pre-fix, PASS post-fix.

### WR-03: The re-run branch skips the startup validation family — a stale replayed lane burns one child per cell

**Files modified:** `pipeline/dispatch_core.py`, `tests/test_dispatch_core.py`
**Commit:** `1680ae2`
**Applied fix:** Followed the fix_hint verbatim in mechanism and
placement: in `_run_rerun_failed`, immediately after the agreed lane is
resolved and BEFORE the archive pre-check and any launch, the replayed
lane's `subset_file` (the claim-time resolved absolute path) is
validated through `run_sweep._validate_subset_file` against the current
overlay-merged registry view, and `run_sweep._validate_dataset_name_alignment`
runs over the same view (loaded once, shared by both — the ordinary
path loads it twice; loading once is equivalent and cheaper).
Docstring protocol + Raises updated to name the step.
**Regression test:**
`test_rerun_validates_startup_family_before_any_launch` — (A) a failed
claim whose lane replays a subset map that no longer exists refuses
with `_validate_subset_file`'s named `cannot read` problem, zero
spawns, no state file (the burned-children hazard pinned); (B) control:
a valid replayed map threads through — one spawn, `--subset_file` on
the child argv verbatim; (C) a registry whose `Dataset_name` diverged
from its key since the original run refuses via the alignment check,
zero spawns. Red/green proven: FAIL pre-fix, PASS post-fix.

## Out of Scope (Info — recorded, not fixed)

Per fix_scope `critical_warning` and the iteration-1 instructions,
IN-01/02/03 are out of scope this round:

- **IN-01** (`pipeline/dispatch_core.py:429-445`,
  `_archive_filename`): archive-name "injective" docstring claim is
  probabilistic (~2^-32 run_id prefix collision; failure mode already
  refuses loudly via `O_EXCL`). Candidate: soften docstring or key on
  full run_id.
- **IN-02** (`pipeline/dispatch_core.py:946-967`, `_spawn_worker`
  `_TAG_RERUN` branch): genealogy silently degrades to a fresh claim
  if the canonical failed claim vanishes between scan and claim (no
  EEXIST). Candidate: loud refusal or diagnostic on the no-collision
  re-run claim path.
- **IN-03** (`pipeline/run_sweep_shard.py:1371-1373`, `run_cleanup`
  leg A): cleanup echoes only the last stdout line of the export
  dry-run. Candidate: echo full captured stdout, or pin the one-line
  contract with a comment. (Note: fixing this would touch
  `run_sweep_shard.py`, outside this iteration's file scope.)

## Verification

| Lane | Where it ran | Result |
|------|--------------|--------|
| `.venv/bin/python -m pytest tests/test_dispatch_core.py tests/test_sweep_shard.py -q` | isolated worktree (main repo's `.venv`), pre-merge; re-run after all 3 fixes | **160 passed** |
| `ruff check pipeline/dispatch_core.py tests/test_dispatch_core.py` | isolated worktree, pre-merge | **All checks passed** |
| `make lint` | main checkout, post-fast-forward (merged `autorun` @ `1680ae2`) | **All checks passed** |
| `make typecheck` (`ty check`) | main checkout, post-fast-forward | **All checks passed** |

Worktree note: `ruff format --check` reports both files as
format-divergent, but that divergence pre-dates this iteration (the
base commit `34ffd31` versions diverge identically) and `make lint`
gates on `ruff check` only. A `ty check` run from inside the worktree
resolved a foreign interpreter (no worktree `.venv`) and was discarded
as environment noise; the authoritative `make typecheck` ran in the
main checkout. Each fix was additionally red/green-proven: its new
test fails against the pre-fix source (via `git stash` of the source
file) and passes after.

---

_Fixed: 2026-10-20T12:33:27Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
