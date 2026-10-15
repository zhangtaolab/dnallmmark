---
phase: 07
review: 07-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "`_read_registry` still tracebacks on valid-JSON-but-non-dict registries — the fail-closed contract is incomplete"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "empty-string `Model_path` counts as PRESENT (false gate PASS) — asymmetric with the sibling kernel fixed in the same commit"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "`run_full_check` persist/completion tail is unguarded — a raising `persist` strands the run with no verdict and no last-check line"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "registry read-failure result renders a misleading \"0 dirs missing\" routing line"
  - id: IN-01
    severity: info
    disposition: fixed
    title: "`_degraded_result` annotation promises `BaseException` but both call sites catch `Exception` only"
  - id: CR-01
    severity: critical
    disposition: open
    title: "Schema-valid custom entries crash `run_finetune.py` with uncaught `KeyError` — required-field sets are inconsistent across the overlay chain"
  - id: IN-02
    severity: info
    disposition: open
    title: "Duplicated `gpu_memory_override = args.gpu_memory` assignment (pre-existing at diff_base)"
  - id: IN-03
    severity: info
    disposition: open
    title: "Pre-existing registry data inconsistencies in fields adjacent to this change (flagged for the maintainer since the registry was just edited)"
open: 3
total: 8
recorded: 2026-10-15T16:16:29.307Z
---

# Phase 07: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | f64e764 |
| WR-02 | warning | fixed | f64e764 |
| WR-03 | warning | fixed | 7217ca1 |
| WR-04 | warning | fixed | 7217ca1 |
| IN-01 | info | fixed | 7217ca1 |
| CR-01 | critical | open | - (not in the current review) |
| IN-02 | info | open | - (not in the current review) |
| IN-03 | info | open | - (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
