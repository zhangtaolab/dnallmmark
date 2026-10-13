---
phase: 12
review: 12-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "`--gpus` is int-validated although documented as verbatim \"operator-owned strings, ARITY-validated only\""
  - id: WR-02
    severity: warning
    disposition: open
    title: "Frozen worker-log path opened `\"w\"` — a resume relaunch destroys the previous run's diagnostic log"
  - id: WR-03
    severity: warning
    disposition: open
    title: "Re-merge over a previously-merged root with a changed worker set leaves stale cell files that downstream consumers will export"
  - id: WR-04
    severity: warning
    disposition: open
    title: "Unhandled `OSError` from `shutil.copyfile`/`mkdir` bypasses the designed merge-refusal message"
  - id: WR-05
    severity: warning
    disposition: open
    title: "Lane-equality comparison canonicalizes Python sets via `json.dumps(..., default=str)` — hash-order-fragile"
  - id: WR-06
    severity: warning
    disposition: open
    title: "`--models` is silently ignored in merge mode"
  - id: WR-07
    severity: warning
    disposition: open
    title: "A marked-then-disabled custom model is stuck in the run spec — rendered unmarked, counted, launched, and impossible to unmark from the picker"
  - id: WR-08
    severity: warning
    disposition: open
    title: "Operator-facing copy composed in the screen module with CJK punctuation — bypasses the I18N-01 grep lock"
  - id: IN-01
    severity: info
    disposition: open
    title: "Dead constant `PROGRESS.LEGEND`"
  - id: IN-02
    severity: info
    disposition: open
    title: "Seed column header interpolated unescaped"
  - id: IN-03
    severity: info
    disposition: open
    title: "Zenodo bearer preview token in the public README (pre-existing, documented)"
open: 11
total: 11
recorded: 2026-10-13T14:22:22.916Z
---

# Phase 12: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| WR-04 | warning | open | - |
| WR-05 | warning | open | - |
| WR-06 | warning | open | - |
| WR-07 | warning | open | - |
| WR-08 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
