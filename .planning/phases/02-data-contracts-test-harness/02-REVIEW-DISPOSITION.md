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
    disposition: fixed
    title: "Makefile hardcodes `~/.local/bin/uv` — all targets break wherever uv lives elsewhere"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "Schema-validation buckets built from glob with no non-emptiness guard — silent vacuous pass"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "Determinism run-to-run check masks a \"run 2 wrote fewer files\" flake"
  - id: WR-05
    severity: warning
    disposition: fixed
    title: "Thread-pinning pin uses `setdefault` while the test hard-asserts `\"1\"` — suite goes red on machines that preset thread vars"
  - id: IN-01
    severity: info
    disposition: deferred
    title: "Generator fallback values violate the tasks_index closed enums the same phase asserts"
  - id: IN-02
    severity: info
    disposition: fixed
    title: "Closed enums duplicated across three schema files; self-check covers only one"
  - id: IN-03
    severity: info
    disposition: deferred
    title: "`METRIC_KEY_MAP` in test_aggregation is a manual mirror of a production local"
  - id: IN-04
    severity: info
    disposition: fixed
    title: "`node` is an undeclared hard dependency of `make test-fast` with a raw traceback on absence"
open: 0
total: 9
recorded: 2026-10-09T05:00:49.681Z
---

# Phase 02: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | 02-REVIEW-FIX.md |
| WR-02 | warning | fixed | 02-REVIEW-FIX.md |
| WR-03 | warning | fixed | 02-REVIEW-FIX.md |
| WR-04 | warning | fixed | 02-REVIEW-FIX.md |
| WR-05 | warning | fixed | 02-REVIEW-FIX.md |
| IN-01 | info | deferred | deferred to Phase 4/5: fix requires generator change (D-04 forbids production edits this phase); documented in 02-REVIEW-FIX.md |
| IN-02 | info | fixed | 02-REVIEW-FIX.md |
| IN-03 | info | deferred | deferred to Phase 4: fix requires extracting METRIC_KEY_MAP from summarize_comparison.main() (D-04); documented in 02-REVIEW-FIX.md |
| IN-04 | info | fixed | 02-REVIEW-FIX.md |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
