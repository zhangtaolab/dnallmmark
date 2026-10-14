---
phase: 07
review: 07-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "Schema-valid custom entries crash `run_finetune.py` with uncaught `KeyError` — required-field sets are inconsistent across the overlay chain"
  - id: WR-01
    severity: warning
    disposition: open
    title: "The 5 repo-ID fixes in `models_info.json` were not propagated — the committed display data (and the public Models page) still carries the stale IDs"
  - id: WR-02
    severity: warning
    disposition: open
    title: "Empty-string CLI values for the new directory flags crash or silently degenerate — inconsistent with both `output_dir`'s handling and `directories_config`'s own drop-empty policy"
  - id: IN-01
    severity: info
    disposition: open
    title: "Stale \"62/50\" official-entry count in the schema `$comment` (registry is 59 since 261014-ir9)"
  - id: IN-02
    severity: info
    disposition: open
    title: "Duplicated `gpu_memory_override = args.gpu_memory` assignment (pre-existing at diff_base)"
  - id: IN-03
    severity: info
    disposition: open
    title: "Pre-existing registry data inconsistencies in fields adjacent to this change (flagged for the maintainer since the registry was just edited)"
open: 6
total: 6
recorded: 2026-10-14T11:18:42.472Z
---

# Phase 07: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | open | - |
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
