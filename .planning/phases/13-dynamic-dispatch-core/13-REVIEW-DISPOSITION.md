---
phase: 13
review: 13-REVIEW.md
titles: json
findings:
  - id: IN-01
    severity: info
    disposition: open
    title: "`_atomic_write_json` tmp path follows a planted symlink (carried, iteration 1)"
  - id: IN-02
    severity: info
    disposition: open
    title: "tee-log stamp has 1-second resolution — a sub-second relaunch truncates the prior crash log (carried, iteration 1)"
  - id: IN-03
    severity: info
    disposition: open
    title: "terminal state writes happen after the lock is released — a fast relaunch's fresh state can be briefly clobbered (carried, iteration 2)"
  - id: IN-04
    severity: info
    disposition: open
    title: "a failed CR-03 pid-persist write abandons an already-spawned child without waiting it (carried, iteration 2)"
  - id: IN-05
    severity: info
    disposition: open
    title: "a non-integer `--seeds` token crashes with a raw ValueError traceback instead of a named collect-all refusal (new observation, defer to owner)"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "containment re-finalizes an already-truthful claim as `failed` when only the state write fails"
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "`--from-failures` is silently ignored in dispatch mode"
  - id: CR-02
    severity: critical
    disposition: fixed
    title: "dispatcher lock create-to-write window defeats the singleton guarantee"
  - id: CR-03
    severity: critical
    disposition: fixed
    title: "child pid is never persisted while the child runs"
  - id: CR-04
    severity: critical
    disposition: fixed
    title: "worker-thread exception silently drops the queue; run reports `done` and exits 0"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "dispatch skips `run_sweep.main`'s startup `--subset_file` map validation"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "parseable lock with an out-of-range `pid` crashes with uncaught OverflowError"
open: 5
total: 12
recorded: 2026-10-20T06:23:55.993Z
---

# Phase 13: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| WR-03 | warning | fixed | 13-REVIEW-FIX.md (not in the current review) |
| CR-01 | critical | fixed | 13-REVIEW-FIX.iter2.md (not in the current review) |
| CR-02 | critical | fixed | 13-REVIEW-FIX.iter2.md (not in the current review) |
| CR-03 | critical | fixed | 13-REVIEW-FIX.iter2.md (not in the current review) |
| CR-04 | critical | fixed | 13-REVIEW-FIX.iter2.md (not in the current review) |
| WR-01 | warning | fixed | 13-REVIEW-FIX.iter2.md (not in the current review) |
| WR-02 | warning | fixed | 13-REVIEW-FIX.iter2.md (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
