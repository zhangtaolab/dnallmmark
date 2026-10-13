---
phase: 12
review: 12-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "`--gpus` is int-validated although documented as verbatim \"operator-owned strings, ARITY-validated only\""
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "Frozen worker-log path opened `\"w\"` — a resume relaunch destroys the previous run's diagnostic log"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "Re-merge over a previously-merged root with a changed worker set leaves stale cell files that downstream consumers will export"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "Unhandled `OSError` from `shutil.copyfile`/`mkdir` bypasses the designed merge-refusal message"
  - id: WR-05
    severity: warning
    disposition: fixed
    title: "Lane-equality comparison canonicalizes Python sets via `json.dumps(..., default=str)` — hash-order-fragile"
  - id: WR-06
    severity: warning
    disposition: fixed
    title: "`--models` is silently ignored in merge mode"
  - id: WR-07
    severity: warning
    disposition: fixed
    title: "A marked-then-disabled custom model is stuck in the run spec — rendered unmarked, counted, launched, and impossible to unmark from the picker"
  - id: WR-08
    severity: warning
    disposition: fixed
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
  - id: IN-04
    severity: info
    disposition: open
    title: "WR-07 sanitizer is kind-blind — a cross-kind key collision would drop a valid mark of the other kind"
open: 4
fixed: 8
total: 12
recorded: 2026-10-13T14:22:22.916Z
updated: 2026-10-13T14:57:13Z
---

# Phase 12: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | 12-REVIEW-FIX.md |
| WR-02 | warning | fixed | 12-REVIEW-FIX.md |
| WR-03 | warning | fixed | 12-REVIEW-FIX.md |
| WR-04 | warning | fixed | 12-REVIEW-FIX.md |
| WR-05 | warning | fixed | 12-REVIEW-FIX.md |
| WR-06 | warning | fixed | 12-REVIEW-FIX.md |
| WR-07 | warning | fixed | 12-REVIEW-FIX.md |
| WR-08 | warning | fixed | 12-REVIEW-FIX.md |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | iteration-2 delta re-review |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
