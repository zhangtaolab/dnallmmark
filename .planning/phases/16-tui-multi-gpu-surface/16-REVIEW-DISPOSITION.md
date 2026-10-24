---
phase: 16
review: 16-REVIEW.md
titles: json
findings:
  - id: IN-01
    severity: info
    disposition: open
    title: "`_parse_gpu_indices` accepts non-canonical integer tokens (carried, iteration 1)"
  - id: IN-02
    severity: info
    disposition: open
    title: "GPU list sorts lexicographically at >= 10 GPUs (carried, iteration 1)"
  - id: IN-03
    severity: info
    disposition: open
    title: "every probe failure mode renders the \"nvidia-smi not installed\" copy (carried, design-pinned)"
  - id: IN-04
    severity: info
    disposition: open
    title: "clearing the workers/GPUs field keeps the last-valid spec value, not the placeholder's promised default (carried, iteration 1)"
  - id: IN-05
    severity: info
    disposition: open
    title: "stale `LNC_GATE_DISPATCH_LINE` comment still asserts the retired WR-03 semantics (NEW this iteration)"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "`_demand_cache` is never invalidated — stale per-root GPU demand after kill/detach/prune + relaunch"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "`DISPATCH_STALE_SECONDS = 60.0` is far below the writer's actual write cadence"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "\"all detected GPUs\" claim contradicts the child CLI — the empty `--gpus` default resolves to `0..workers-1`"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "A malformed-but-fresh dispatch view renders the STALE copy with a self-contradictory age"
  - id: WR-05
    severity: warning
    disposition: fixed
    title: "The probe timeout is not fully bounded — `subprocess.run`'s post-kill `wait()` can hang the worker on a D-state nvidia-smi"
open: 5
total: 10
recorded: 2026-10-21T07:35:09.193Z
---

# Phase 16: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| WR-01 | warning | fixed | 16-REVIEW-FIX.md (not in the current review) |
| WR-02 | warning | fixed | 16-REVIEW-FIX.md (not in the current review) |
| WR-03 | warning | fixed | 16-REVIEW-FIX.md (not in the current review) |
| WR-04 | warning | fixed | 16-REVIEW-FIX.md (not in the current review) |
| WR-05 | warning | fixed | 16-REVIEW-FIX.md (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
