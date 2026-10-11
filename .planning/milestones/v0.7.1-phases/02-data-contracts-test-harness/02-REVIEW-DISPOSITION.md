---
phase: 02
review: 02-REVIEW.md
titles: json
findings:
  - id: WR-06
    severity: warning
    disposition: fixed
    title: "check-node's remediation message points to a node-free lane that does not exist — `make test-fast` hard-requires node via `test_golden.py`"
  - id: WR-07
    severity: warning
    disposition: fixed
    title: "`make data` invokes node with no check-node guard — the raw exit-127 failure IN-04 fixed for `test` persists in the other node-dependent target"
  - id: IN-05
    severity: info
    disposition: fixed
    title: "AUD-01 companion guards findability and uniqueness but not key-presence — one silent-degradation path remains open"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "AUD-01 lock's `pytest.fail` honesty guard is swallowed by its own `xfail` marker"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "Makefile hardcodes `~/.local/bin/uv`"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "Schema-validation glob buckets have no non-emptiness guard"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "Determinism run-to-run check masks a \"run 2 wrote fewer files\" flake"
  - id: WR-05
    severity: warning
    disposition: fixed
    title: "Thread pin uses `setdefault` while the test hard-asserts \"1\""
  - id: IN-01
    severity: info
    disposition: deferred
    title: "Generator fallback values violate the tasks_index closed enums the same phase asserts"
  - id: IN-02
    severity: info
    disposition: fixed
    title: "Closed enums duplicated across schema files; self-check covers only one"
  - id: IN-03
    severity: info
    disposition: deferred
    title: "`METRIC_KEY_MAP` in test_aggregation is a manual mirror of a production local"
  - id: IN-04
    severity: info
    disposition: fixed
    title: "`node` is an undeclared hard dependency of the JS test lane"
open: 0
total: 12
recorded: 2026-10-09T05:09:37.646Z
---

# Phase 02: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-06 | warning | fixed | 02-REVIEW-FIX.md (round 2) |
| WR-07 | warning | fixed | 02-REVIEW-FIX.md (round 2) |
| IN-05 | info | fixed | 02-REVIEW-FIX.md (round 2) |
| WR-01 | warning | fixed | 02-REVIEW-FIX.md |
| WR-02 | warning | fixed | 02-REVIEW-FIX.md |
| WR-03 | warning | fixed | 02-REVIEW-FIX.md |
| WR-04 | warning | fixed | 02-REVIEW-FIX.md |
| WR-05 | warning | fixed | 02-REVIEW-FIX.md |
| IN-01 | info | deferred | deferred to Phase 4/5 (D-04 production-change prohibition; rationale in 02-REVIEW-FIX.md) |
| IN-02 | info | fixed | 02-REVIEW-FIX.md |
| IN-03 | info | deferred | deferred to Phase 4/5 (D-04 production-change prohibition; rationale in 02-REVIEW-FIX.md) |
| IN-04 | info | fixed | 02-REVIEW-FIX.md |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
