---
phase: 10
review: 10-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "Dataset landing base resolves through a different chain than the sweep/env-check root — downloads can land where the configured run does not read"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "A failed KIND_MODEL download flips the selection 下载 column to 已下载 — presence is dir-existence while the done gate requires config.json"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "The slot-3 drill-down renders \"channel: unknown (unknown_key)\" for healthy KIND_MODEL queue rows — channel_detail only resolves the dataset registry"
  - id: IN-01
    severity: info
    disposition: fixed
    title: "`z` during the probe-in-flight window renders the \"not yet public\" toast as fact"
  - id: IN-02
    severity: info
    disposition: fixed
    title: "`ABOUT_MILESTONE_STAGE` is stale — names phase 9 as the current phase on the About screen"
open: 4
total: 5
recorded: 2026-10-14T15:20:38.683Z
---

# Phase 10: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | fixed | - |
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
