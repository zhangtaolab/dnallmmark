---
phase: 15
review: 15-REVIEW.md
titles: json
findings:
  - id: IN-01
    severity: info
    disposition: open
    title: "(carried) Subset-consuming workflow still undocumented outside `.planning/` — generator \"See also\" mis-points"
  - id: IN-03
    severity: info
    disposition: open
    title: "(carried, remainder) Line-anchored citations in docs/multi-gpu.md are correct today but fragile"
  - id: IN-04
    severity: info
    disposition: open
    title: "(carried) Success banner printed before the all-refused error exit"
  - id: IN-05
    severity: info
    disposition: open
    title: "(carried, pre-existing) Duplicate `gpu_memory_override` assignment"
  - id: IN-06
    severity: info
    disposition: open
    title: "(new this iteration, hardening — not re-opening WR-02) CR-02's existence-only check still trusts a stale v1 metrics file for failures OUTSIDE the evaluate window"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "A failed `trainer.evaluate()` yields a falsely-completed dispatch cell with no eval keys"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "`csv.Error` is uncaught in `read_csv_rows` — an oversized-field CSV crashes the whole generator run"
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "Subset generator has no `--output-root` / `--dataset-root` isolation guard — equal roots silently destroy the real benchmark datasets"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "`write_cell_run_record` WR-11 branch misses `UnicodeDecodeError` — a non-UTF-8 corrupt `final_metrics.json` yields a record-less cell with the claim rewritten failed"
open: 5
total: 9
recorded: 2026-10-21T01:35:08.002Z
---

# Phase 15: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| IN-01 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| IN-06 | info | open | - |
| WR-02 | warning | fixed | 15-REVIEW-FIX.md (not in the current review) |
| WR-03 | warning | fixed | 15-REVIEW-FIX.md (not in the current review) |
| CR-01 | critical | fixed | 15-REVIEW-FIX.iter2.md (not in the current review) |
| WR-01 | warning | fixed | 15-REVIEW-FIX.iter2.md (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
