---
phase: 17
review: 17-REVIEW.md
titles: json
findings:
  - id: IN-01
    severity: info
    disposition: skipped
    title: "METRIC_MAP diverges from the exporter's legacy metric table (MSE/MAE uppercase)"
  - id: IN-02
    severity: info
    disposition: skipped
    title: "Trio recording is independent of the raw-score presence gate"
  - id: IN-03
    severity: info
    disposition: skipped
    title: "Floating bars can extend below the metric's natural domain (mean < std)"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "Error-bar plugin's vertical-bar branch draws wrong geometry (latent)"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "Scatter whiskers mix units — tooltip label invites misreading"
open: 0
total: 5
recorded: 2026-10-21T12:40:28.728Z
---

# Phase 17: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| IN-01 | info | skipped | 17-REVIEW-FIX.md |
| IN-02 | info | skipped | 17-REVIEW-FIX.md |
| IN-03 | info | skipped | 17-REVIEW-FIX.md |
| WR-01 | warning | fixed | 17-REVIEW-FIX.md (not in the current review) |
| WR-02 | warning | fixed | 17-REVIEW-FIX.md (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
