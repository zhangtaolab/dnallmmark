---
phase: 08
review: 08-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "Loader-contract registry input crashes the entire console (tolerant seam incomplete + `exit_on_error=True`)"
  - id: WR-01
    severity: warning
    disposition: open
    title: "env_smoke directory kernels raise on missing/malformed registry — console crash at boot, violating the gate's own never-traceback contract"
  - id: WR-02
    severity: warning
    disposition: open
    title: "Degraded compat map renders a silent blank models table on slot 2"
  - id: WR-03
    severity: warning
    disposition: open
    title: "New synchronous event-loop file reads contradict the pinned D-03/WR-04 read-seam discipline"
  - id: IN-01
    severity: info
    disposition: open
    title: "Dead strings constants after the 2026-10-14 slot split"
  - id: IN-02
    severity: info
    disposition: open
    title: "Matrix screen still composes a Textual `Header()` after the nav-shell migration"
  - id: IN-03
    severity: info
    disposition: open
    title: "`EnvCheckScreen.action_show_detail` lacks the `is_valid_coordinate` guard its sibling screens carry"
  - id: IN-04
    severity: info
    disposition: open
    title: "Filter grammar accepts degenerate tokens that render oddly"
open: 8
total: 8
recorded: 2026-10-14T11:53:21.528Z
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
| IN-04 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
