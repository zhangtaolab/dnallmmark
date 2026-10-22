---
phase: 18
review: 18-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "multi-gpu.md still carries the pre-review 60 s stale-grace value the phase corrected everywhere else"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "The report-assets honesty ledger table is split by a blank line — 5 of 7 assets render outside the table"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "TUI-DEMO now contradicts itself — the re-record section's collision guarantee is false under the Phase-16 semantics §11 documents"
  - id: IN-01
    severity: info
    disposition: skipped
    title: "README's example suite count is 493 tests behind the v1.3 baseline the report cites"
  - id: IN-02
    severity: info
    disposition: skipped
    title: "Absolute machine paths quoted in the multi-gpu.md subset evidence block"
open: 0
total: 5
recorded: 2026-10-22T08:05:47.993Z
---

# Phase 18: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | 18-REVIEW-FIX.md |
| WR-02 | warning | fixed | 18-REVIEW-FIX.md |
| WR-03 | warning | fixed | 18-REVIEW-FIX.md |
| IN-01 | info | skipped | 18-REVIEW-FIX.md |
| IN-02 | info | skipped | 18-REVIEW-FIX.md |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
