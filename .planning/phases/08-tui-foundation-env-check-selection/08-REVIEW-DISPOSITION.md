---
phase: 08
review: 08-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "The L language toggle / persisted-zh boot renders a mixed-language UI — module-frozen copy never re-resolves"
  - id: WR-01
    severity: warning
    disposition: open
    title: "`translate_value` en→zh collisions — the documented well-definedness invariant is false in one direction, and the wizard's `b` label is already mistranslated"
  - id: WR-02
    severity: warning
    disposition: open
    title: "`enqueue_zenodo` ignores persist failure — the WR-04 rollback/`persist_failed` contract is missing on the bundle lane (pre-delta, verified also at 2341f1c)"
  - id: WR-03
    severity: warning
    disposition: open
    title: "Pressing L while an env check is in flight restarts the whole kernel run from zero"
  - id: IN-01
    severity: info
    disposition: open
    title: "`data_manager.apply_queue_progress` stores live percent/speed for KIND_MODEL keys before the ignore check — and `apply_queue_event` never pops them"
  - id: IN-02
    severity: info
    disposition: open
    title: "The persisted-language filename is duplicated as an inline literal"
  - id: IN-03
    severity: info
    disposition: open
    title: "Slot-3's present-row enqueue toast reuses a slot-2 (SEL_) constant"
  - id: IN-04
    severity: info
    disposition: open
    title: "Filter grammar accepts degenerate tokens that render oddly"
open: 8
total: 8
recorded: 2026-10-16T04:35:44.750Z
---

# Phase 08: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | open | - |
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
