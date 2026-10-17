---
phase: 08
review: 08-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "The ctrl+c intercept silently kills the focused-Input copy binding on every base screen"
  - id: WR-02
    severity: warning
    disposition: open
    title: "ExitModal `[k]` runs `kill_sweep` serially on the event loop — up to kill_grace × N roots of frozen UI"
  - id: WR-03
    severity: warning
    disposition: open
    title: "Mixed live-root exit drops the attached CLI-launched sweep from the ExitModal"
  - id: IN-01
    severity: info
    disposition: open
    title: "`selection.apply_queue_progress` still stores before the kind guard — the asymmetric twin of this round's IN-01 slot-3 fix"
  - id: IN-02
    severity: info
    disposition: open
    title: "`GateWorkerError` staleness filter collides across the `_gate_stage_id` / `_gate_launch_id` number spaces"
  - id: IN-03
    severity: info
    disposition: open
    title: "env_check remount can transiently render the stale pre-refresh cache outcome"
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "The L language toggle / persisted-zh boot renders a mixed-language UI — module-frozen copy never re-resolves"
  - id: IN-04
    severity: info
    disposition: open
    title: "Filter grammar accepts degenerate tokens that render oddly"
open: 7
total: 8
recorded: 2026-10-17T04:43:05.046Z
---

# Phase 08: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | fixed in 06d2679 (klw): ctrl+c delegates to Input copy on selection |
| WR-02 | warning | fixed | fixed in 06d2679 (klw): kill-and-exit off-loop @work worker |
| WR-03 | warning | fixed | fixed in 06d2679 (klw): mixed roots join the multi-root ExitModal |
| IN-01 | info | fixed | fixed in 0d02e18 (klw): store below the kind guard |
| IN-02 | info | fixed | fixed in 0d02e18 (klw): scope-tagged single-counter staleness filter |
| IN-03 | info | fixed | fixed in 0d02e18 (klw): _check_in_flight set synchronously |
| CR-01 | critical | fixed | f9528e3 (quick-261016-hhx Task 1) (not in the current review) |
| IN-04 | info | open | - (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
