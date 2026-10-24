---
phase: 09
review: 09-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "ExitModal renders the attached sweep's progress counts under the launcher root's name"
  - id: WR-02
    severity: warning
    disposition: open
    title: "The slot-1 storage overview runs `load_state()` + five `Path.exists()` stats synchronously on the event loop — violating the module's own D-03 lock"
  - id: WR-03
    severity: warning
    disposition: open
    title: "`d`'s manual-placement toast path reads run-config state on the event loop (same D-03 class, delta-introduced)"
  - id: IN-01
    severity: info
    disposition: open
    title: "Dead SEL_ constants and stale dataset-table comments after the slot split"
  - id: IN-02
    severity: info
    disposition: open
    title: "Tests pin committed-data counts (36 adapted) that break on any compat-map data commit"
  - id: IN-03
    severity: info
    disposition: open
    title: "Stale \"seven kernel ids\" comment in the env-check Pilot suite"
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "Non-UTF-8 custom registry file raises uncaught UnicodeDecodeError (iteration 1)"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "Import/export file I/O runs on the event loop (iteration 1)"
  - id: WR-05
    severity: warning
    disposition: fixed
    title: "tui/services/about.py carries Chinese literals and no i18n lock covers it (iteration 1)"
  - id: WR-06
    severity: warning
    disposition: fixed
    title: "WR-02 absorption tuple misses UnicodeDecodeError — official-registry read can still raise across the gauntlet service boundary (iteration 2)"
  - id: WR-07
    severity: warning
    disposition: fixed
    title: "WR-04's Validated handler lacks the module's own liveness/generation discipline (iteration 2)"
open: 6
total: 11
recorded: 2026-10-14T14:36:12.369Z
---

# Phase 09: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| CR-01 | critical | fixed | 09-REVIEW-FIX.md (not in the current review) |
| WR-04 | warning | fixed | 09-REVIEW-FIX.md (not in the current review) |
| WR-05 | warning | fixed | 09-REVIEW-FIX.md (not in the current review) |
| WR-06 | warning | fixed | 09-REVIEW-FIX.md (not in the current review) |
| WR-07 | warning | fixed | 09-REVIEW-FIX.md (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
