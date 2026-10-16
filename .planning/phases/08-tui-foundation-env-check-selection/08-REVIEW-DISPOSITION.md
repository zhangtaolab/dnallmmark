---
phase: 08
review: 08-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "The L language toggle / persisted-zh boot renders a mixed-language UI — module-frozen copy never re-resolves"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "`translate_value` en→zh collisions — the documented well-definedness invariant is false in one direction, and the wizard's `b` label is already mistranslated"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "`enqueue_zenodo` ignores persist failure — the WR-04 rollback/`persist_failed` contract is missing on the bundle lane (pre-delta, verified also at 2341f1c)"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "Pressing L while an env check is in flight restarts the whole kernel run from zero"
  - id: IN-01
    severity: info
    disposition: fixed
    title: "`data_manager.apply_queue_progress` stores live percent/speed for KIND_MODEL keys before the ignore check — and `apply_queue_event` never pops them"
  - id: IN-02
    severity: info
    disposition: fixed
    title: "The persisted-language filename is duplicated as an inline literal"
  - id: IN-03
    severity: info
    disposition: fixed
    title: "Slot-3's present-row enqueue toast reuses a slot-2 (SEL_) constant"
  - id: IN-04
    severity: info
    disposition: open
    title: "Filter grammar accepts degenerate tokens that render oddly"
open: 1
total: 8
recorded: 2026-10-16T04:35:44.750Z
fixed: 2026-10-16 (quick-261016-hhx)
---

# Phase 08: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | fixed | f9528e3 (quick-261016-hhx Task 1) |
| WR-01 | warning | fixed | 190d1c4 (quick-261016-hhx Task 2) |
| WR-02 | warning | fixed | 190d1c4 (quick-261016-hhx Task 2) |
| WR-03 | warning | fixed | 190d1c4 (quick-261016-hhx Task 2) |
| IN-01 | info | fixed | 190d1c4 (quick-261016-hhx Task 2) |
| IN-02 | info | fixed | 190d1c4 (quick-261016-hhx Task 2) |
| IN-03 | info | fixed | 190d1c4 (quick-261016-hhx Task 2) |
| IN-04 | info | open | - (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`,
`deferred`.
