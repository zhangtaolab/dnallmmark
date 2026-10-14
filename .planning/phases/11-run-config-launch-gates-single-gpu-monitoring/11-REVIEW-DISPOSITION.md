---
phase: 11
review: 11-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "`[a]` attach stores the raw operator path — `~`/relative attaches silently monitor nothing"
  - id: WR-01
    severity: warning
    disposition: open
    title: "SweepLauncher registry key resolves against the TUI process CWD, contradicting the service tier's any-CWD contract (D-14)"
  - id: WR-02
    severity: warning
    disposition: open
    title: "`[r]` re-run seed fan-out falls back to a silent `[42]` when the cell table is empty — a different experiment than the one confirmed"
  - id: WR-03
    severity: warning
    disposition: open
    title: "The re-run confirm names entry-count `n`, but the launch enumerates pairs × the sweep's full seed set — the confirmed GPU spend can be understated ~3x"
  - id: WR-04
    severity: warning
    disposition: open
    title: "Tee log filename uses second-resolution timestamp + basename only — two same-basename roots launched in the same second truncate each other's logs"
  - id: WR-05
    severity: warning
    disposition: open
    title: "The exit modal handles only one live sweep — `[k] 终止后退出` exits with the others still running"
  - id: IN-01
    severity: info
    disposition: open
    title: "`LNC_E2_WARNING` hardcodes the registry counts (59 × 50 × 8850) — copy drifts when the registries evolve"
  - id: IN-02
    severity: info
    disposition: open
    title: "Stale placeholder comment over the NAV block"
  - id: IN-03
    severity: info
    disposition: open
    title: "`cells_view`'s `expected_seeds` parameter is dead in production"
  - id: IN-04
    severity: info
    disposition: open
    title: "Cell-detail modal never reads curve-cell records"
  - id: IN-05
    severity: info
    disposition: open
    title: "Cell-row key `f\"{model}__{task}\"` is collision-prone for keys containing `__`"
open: 11
total: 11
recorded: 2026-10-14T16:12:41.467Z
---

# Phase 11: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | open | - |
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| WR-04 | warning | open | - |
| WR-05 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
