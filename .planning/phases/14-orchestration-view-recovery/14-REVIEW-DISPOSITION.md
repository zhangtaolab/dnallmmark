---
phase: 14
review: 14-REVIEW.md
titles: json
findings:
  - id: IN-01
    severity: info
    disposition: open
    title: "Archive-filename \"injective\" claim is probabilistic (8-hex-char run_id prefix) — CARRIED"
  - id: IN-02
    severity: info
    disposition: open
    title: "Re-run genealogy silently degrades if the canonical claim vanishes between scan and claim — CARRIED"
  - id: IN-03
    severity: info
    disposition: open
    title: "Cleanup echoes only the last stdout line of the export dry-run — CARRIED"
  - id: IN-04
    severity: info
    disposition: open
    title: "`_validate_rerun_passthrough` accepts a flag-shaped `--registry-dir` value where the mirrored argparse path refuses — NEW (minor)"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "Launch-time state-publish failures leak the dispatcher lock and crash with a raw traceback"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "`--rerun-failed` silently drops corrupt / integrity-failing failed claims from the re-run feed"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "The re-run branch skips the startup validation family — a stale replayed lane burns one child per cell"
open: 4
total: 7
recorded: 2026-10-20T12:52:25.766Z
---

# Phase 14: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| WR-01 | warning | fixed | 14-REVIEW-FIX.md (not in the current review) |
| WR-02 | warning | fixed | 14-REVIEW-FIX.md (not in the current review) |
| WR-03 | warning | fixed | 14-REVIEW-FIX.md (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
