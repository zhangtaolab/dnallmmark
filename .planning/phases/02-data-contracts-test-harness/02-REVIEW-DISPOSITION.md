---
phase: 02
review: 02-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "AUD-01 lock's `pytest.fail` honesty guard is swallowed by its own `xfail` marker"
  - id: WR-02
    severity: warning
    disposition: open
    title: "Makefile hardcodes `~/.local/bin/uv` — all targets break wherever uv lives elsewhere"
  - id: WR-03
    severity: warning
    disposition: open
    title: "Schema-validation buckets built from glob with no non-emptiness guard — silent vacuous pass"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "Determinism run-to-run check masks a \"run 2 wrote fewer files\" flake"
  - id: WR-05
    severity: warning
    disposition: open
    title: "Thread-pinning pin uses `setdefault` while the test hard-asserts `\"1\"` — suite goes red on machines that preset thread vars"
  - id: IN-01
    severity: info
    disposition: open
    title: "Generator fallback values violate the tasks_index closed enums the same phase asserts"
  - id: IN-02
    severity: info
    disposition: open
    title: "Closed enums duplicated across three schema files; self-check covers only one"
  - id: IN-03
    severity: info
    disposition: open
    title: "`METRIC_KEY_MAP` in test_aggregation is a manual mirror of a production local"
  - id: IN-04
    severity: info
    disposition: open
    title: "`node` is an undeclared hard dependency of `make test-fast` with a raw traceback on absence"
open: 7
total: 9
recorded: 2026-10-09T05:00:49.681Z
---

# Phase 02: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | 02-REVIEW-FIX.md |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| WR-04 | warning | fixed | 02-REVIEW-FIX.md |
| WR-05 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
