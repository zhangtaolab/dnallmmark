---
phase: 16-tui-multi-gpu-surface
fixed_at: 2026-10-21T07:21:22Z
review_path: .planning/phases/16-tui-multi-gpu-surface/16-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 16: Code Review Fix Report

**Fixed at:** 2026-10-21T07:21:22Z
**Source review:** .planning/phases/16-tui-multi-gpu-surface/16-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope (critical_warning): 5 (WR-01..WR-05)
- Fixed: 5
- Skipped: 0
- Out of scope per iteration-1 directive: 4 Info items (IN-01..IN-04),
  recorded below as skipped-info

**Binding constraints honored:** frozen files untouched
(`pipeline/dispatch_core.py`, `pipeline/run_sweep_shard.py`,
`pipeline/run_sweep.py`, `pipeline/run_finetune.py` — zero edits);
services stay textual-free (the gpu_probe logger is stdlib `logging`,
the tier's first and only diagnostic); screens stay thin (every new
number/copy arrives service- or strings-side); all copy via
`tui/strings.py` with the bidirectional inventory tripwires updated
lockstep; nothing pushed.

## Fixed Issues

### WR-01: `_demand_cache` is never invalidated — stale per-root GPU demand after kill/detach/prune + relaunch

**Files modified:** `tui/services/sweep_launcher.py`, `tests/tui/test_services_sweep_launcher.py`
**Commit:** 960435f
**Applied fix:** The smaller mechanism (invalidation), not the
`(root, argv)` re-key: the per-root demand-cache entry is evicted at
EVERY registry mutation — `kill_sweep`, `detach`, the `live_sweeps()`
dead-entry prune, `_spawn`'s dead-entry reclaim, and the `_spawn`
claim itself (the claim-time pop alone covers the reclaim path and
guards against a future drop site missing its eviction; the drop-site
pops also bound cache growth). Docstrings/comments updated (argv is
immutable PER ENTRY, never per ROOT). Three regression tests
reproduce the reviewer's poisoning scenario: the over-refusal
direction (kill 2-worker, relaunch `--workers 1`, request 1 → must
admit), the over-admission direction (kill 1-worker, relaunch
`--workers 2`, request 1 → must refuse), and a per-site eviction pin
(detach / prune / dead-entry reclaim). All three were verified to
FAIL against the pre-fix source (stash-probe) before committing.

### WR-02: `DISPATCH_STALE_SECONDS = 60.0` is far below the writer's actual write cadence

**Files modified:** `tui/services/dispatch_state.py`, `tui/strings.py`, `tui/screens/monitor.py`, `tests/tui/test_services_dispatch_state.py`, `tests/tui/test_pilot_monitor.py`
**Commit:** a8c4965
**Applied fix — option (b), with rationale.** The semantic option (a)
(terminal status `done`/`incomplete` → never stale; `running` →
stale-after-grace) was investigated first per the fix directive, and
REJECTED on the pinned-test escape hatch: `tests/tui/
test_services_dispatch_state.py` section 5 ("staleness (D16-08, the
pinned 60s threshold)") pins BOTH the constant value AND the
unconditional-mtime behavior at a running status, and D16-08 is
listed in the module's "Contract (locked decisions)" block whose own
tunability clause sanctions RAISING the value ("MAINTAINER-TUNABLE …
raise it for slow quiescent phases") but not re-shaping the
projection. Shipped: `DISPATCH_STALE_SECONDS = 3600.0` — cell scale,
documented against the writer's real cadence (transitions only:
pre-drain/claim/finalize/containment/terminal; no heartbeat; the
longest quiet window on a healthy run is one claim-to-finalize cell,
minutes-to-hours). The docstring also states option (b)'s known
residual: a terminal file is never rewritten, so its age eventually
crosses the grace and the marker renders on long-finished runs
(cosmetic; last-known-good rows stay verbatim) — the truthful fix for
that residual is the maintainer-ruling territory the reviewer's
dispatcher-heartbeat alternative lives in. Lockstep: `MON_DISPATCH_STALE`
now interpolates `{grace}` instead of hardcoding "60s" (zh `≥ {grace}s`),
the screen formats it from `dispatch_state.DISPATCH_STALE_SECONDS`
(still a pure constant read — the screen computes nothing), and the
unit pin was rescaled (age 3700 → stale, age 120 → FRESH, constant ==
3600.0) with the false-positive case pinned as the fresh leg.

### WR-03: "all detected GPUs" claim contradicts the child CLI — the empty `--gpus` default resolves to `0..workers-1`

**Files modified:** `tui/services/sweep_launcher.py`, `tui/services/run_config.py`, `tui/screens/run_config.py`, `tui/strings.py`, `tests/tui/test_services_sweep_launcher.py`, `tests/tui/test_pilot_run_config.py`
**Commit:** e0f4523
**Applied fix:** Copy-only, NO child-side change (dispatch_core
frozen this phase). `GateSummary.gpus_display` for a `spec.gpus` of
None now renders `0..{workers-1}` — the child's OWN "Default GPU
assignment" (`if gpus is None: gpus = [str(i) for i in
range(workers)]`, dispatch_core.py:1796-1798) — replacing
`all({effective_gpu_count()})`; the derivation is from the spec's
workers alone, so no GPU detection happens at preview time.
`CFG_GPUS_DEFAULT` placeholder now reads "— (default: GPUs
0..workers-1)" / "—（默认: GPU 0..workers-1）" ("workers" = the
sibling field name, static placeholder). All three run_config
docstrings and the screen comments corrected; the gate test renamed
to `..._default_first_workers` (pins 0..0 at workers=1 and 0..3 at
workers=4), the fresh-recompute pin expects `0..1`, and the pilot
fabricated `gpus_display` values updated lockstep.

### WR-04: A malformed-but-fresh dispatch view renders the STALE copy with a self-contradictory age

**Files modified:** `tui/strings.py`, `tui/screens/monitor.py`, `tests/tui/test_strings_phase11.py`, `tests/tui/test_pilot_monitor.py`
**Commit:** aab7d69
**Applied fix:** The warning row's condition is split: `view.stale`
renders `MON_DISPATCH_STALE` (the age/grace statement), `view.malformed`
renders the NEW `MON_DISPATCH_MALFORMED` constant ("⚠ dispatch counts
inconsistent (snapshot invariant violated) — values shown verbatim" /
"⚠ 调度计数不一致（快照不变量被违反）— 数值按原样显示"; ⚠ glyph per the
NO_COLOR rule, registered in the bidirectional inventory lockstep).
Both flags render BOTH rows, stale first. The dispatch block's
STRUCTURE leg changed from a single bool to the WARNING-ROW COUNT
(`int(stale) + int(malformed)`) — a one-bool leg cannot distinguish
one warning row from two, so a flag flipping without a rebuild would
strand the row count. Fixture gap fixed: the pilot malformed view now
carries a FRESH age (`stale_age_s=5`), so a
malformation-borrows-the-staleness-copy regression renders a
self-contradictory claim and fails the pin; a new both-flags pilot
test pins the two-row order.

### WR-05: The probe timeout is not fully bounded — `subprocess.run`'s post-kill `wait()` can hang the worker on a D-state nvidia-smi

**Files modified:** `tui/services/gpu_probe.py`, `tests/tui/test_services_gpu_probe.py`
**Commit:** 258cb3d
**Applied fix:** `_default_runner` drops the raw `subprocess.run` for
`Popen` + `communicate(timeout=...)`; on TimeoutExpired it kills then
reaps with `wait(timeout=timeout)` — the SAME budget. A second
TimeoutExpired (an un-reapable D-state child: SIGKILL cannot
interrupt a driver ioctl) re-raises the ORIGINAL TimeoutExpired so
`probe()` degrades to the one absent outcome, and logs ONE warning on
the new module logger (the tier's first and only diagnostic; no
handler installed — every normal path stays silent). The killed
handle leaks — the documented trade-off (a rare zombie until the
driver recovers is strictly better than one stuck exclusive worker +
one zombie nvidia-smi per 2s tick). Regression tests: a wedge-shaped
fake Popen (kill lands, `wait()` reaps only under a finite timeout;
an unbounded wait trips a sentinel) pins the bounded reap + the
absent outcome + the warning; a reapable-after-kill variant pins that
a timed-out probe never rescues into data; a real-subprocess happy
path (sys.executable, never nvidia-smi — the download_queue
precedent) pins the seam contract. Verified to fail against the
pre-fix source.

## Skipped Issues

None — all five in-scope findings were fixed.

## Out of Scope (iteration-1 directive)

### IN-01: `_parse_gpu_indices` accepts non-canonical int()-parseable tokens

**File:** `tui/services/run_config.py:374-389`
**Reason:** skipped-info (Info tier excluded from iteration-1 fix scope)

### IN-02: GPU indices normalize with a STRING sort — non-numeric order at >= 10 GPUs

**File:** `tui/services/run_config.py:277-279`
**Reason:** skipped-info (Info tier excluded from iteration-1 fix scope)

### IN-03: nvidia-smi "[N/A]" sensor values degrade the whole panel to the "not installed" copy

**File:** `tui/services/gpu_probe.py:143-157`
**Reason:** skipped-info (Info tier excluded from iteration-1 fix scope)

### IN-04: The GPUs field placeholder says empty = "all detected GPUs", but a cleared field keeps the last valid list

**File:** `tui/screens/run_config.py:1768-1795`
**Reason:** skipped-info (Info tier excluded from iteration-1 fix scope).
Note: the WR-03 copy correction removed the inaccurate "all detected"
wording this finding partly rested on; the last-valid-governs
behavior itself is unchanged.

## Snapshot Goldens (D-03 pending batch)

The WR-03/WR-04 copy changes invalidated the 4 uncommitted D-03 SVGs
as predicted. All 10 goldens were regenerated via
`make snapshot-update` (uv, `tests/tui/test_snapshots.py
--regenerate`) against the fixed code and the suite is green
(12/12) in BOTH trees. Per the iteration directive the 4 D-03 SVGs
(`monitor_empty.svg`, `monitor_running.svg`, `run_config.svg`, and
the new `run_config_confirm.svg`) are kept UNCOMMITTED as the pending
WINDOWS #50 review batch — they were regenerated in the isolated
worktree, then copied into the main checkout after the fast-forward
and re-verified there; the maintainer reviews/commits them via the
D-03 batch flow. The committed tree still shows the 4 documented #50
golden reds until that batch lands.

## Verification

**Where the gates ran:** per-fix suites + `make lint` + `make
typecheck` ran in the ISOLATED WORKTREE (`.claude/worktrees/
rf-16-416445-1792565204`, branch `gsd-reviewfix/16-416445`,
fast-forwarded into `autorun` and removed afterwards); the final
snapshot-suite confirmation ran in the MAIN checkout after the
fast-forward. Worktree numbers are reproducible from the main
checkout at commit 258cb3d (same tree the fast-forward produced).

- Per-fix lanes (all green):
  - WR-01: `tests/tui/test_services_sweep_launcher.py` (83 passed;
    the 3 new regression tests stash-proven red pre-fix)
  - WR-02: `tests/tui/test_services_dispatch_state.py`,
    `tests/tui/test_strings_phase11.py` (23), and
    `tests/tui/test_pilot_monitor.py` (123)
  - WR-03: `tests/tui/test_services_sweep_launcher.py`,
    `tests/tui/test_services_run_config.py`,
    `tests/tui/test_strings_phase11.py`,
    `tests/tui/test_language_rederivation.py` (274), and
    `tests/tui/test_pilot_run_config.py` (108)
  - WR-04: `tests/tui/test_strings_phase11.py`,
    `tests/tui/test_language_rederivation.py` (16), and
    `tests/tui/test_pilot_monitor.py` (124)
  - WR-05: `tests/tui/test_services_gpu_probe.py` (16; regression
    stash-proven red pre-fix) and `tests/tui/test_import_lock.py`
- Lint: ruff over the full Makefile lint scope — All checks passed.
- Typecheck: `ty check` (uv, repo venv) — zero diagnostics (one
  diagnostic introduced by the first WR-05 test draft was fixed and
  folded into the WR-05 commit before the batch was declared green).
- Snapshots: pre-regen 4 failed / 8 passed (the documented #50
  committed-tree pattern); post-regen 12/12 in the worktree AND in
  the main checkout.
- Not run: the full `make test` battery (out of fixer scope; the
  verifier phase owns it).

**Human-verification flag:** none of the five fixes was classified as
a logic-error risk requiring manual semantic confirmation beyond the
pinned tests — WR-01/WR-05 carry stash-proven regression pins, and
WR-02's rejected-alternative rationale is recorded above for the
maintainer.

---

_Fixed: 2026-10-21T07:21:22Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
