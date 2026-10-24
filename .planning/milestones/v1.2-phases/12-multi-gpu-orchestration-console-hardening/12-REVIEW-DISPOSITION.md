---
phase: 12
review: 12-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "Blanket strict-xfail opens an unbounded golden-drift detection gap until the maintainer snapshot-update lands"
  - id: WR-02
    severity: warning
    disposition: open
    title: "`pipeline/directories_config.py` (new production module) is missing from the `make lint` lane"
  - id: IN-01
    severity: info
    disposition: open
    title: "Pre-ir9 \"62\" fixture strings survive in out-of-scope TUI test fakes"
  - id: IN-02
    severity: info
    disposition: open
    title: "docs/multi-gpu.md cleanup bullet renders two rm commands as one joined line"
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
  - id: IN-03
    severity: info
    disposition: open
    title: "Zenodo bearer preview token in the public README (pre-existing, documented)"
  - id: IN-04
    severity: info
    disposition: open
    title: "WR-07 sanitizer is kind-blind — a cross-kind key collision would drop a valid mark of the other kind"
open: 6
total: 12
recorded: 2026-10-14T17:28:21.418Z
---

# Phase 12: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| WR-03 | warning | fixed | 12-REVIEW-FIX.md (not in the current review) |
| WR-04 | warning | fixed | 12-REVIEW-FIX.md (not in the current review) |
| WR-05 | warning | fixed | 12-REVIEW-FIX.md (not in the current review) |
| WR-06 | warning | fixed | 12-REVIEW-FIX.md (not in the current review) |
| WR-07 | warning | fixed | 12-REVIEW-FIX.md (not in the current review) |
| WR-08 | warning | fixed | 12-REVIEW-FIX.md (not in the current review) |
| IN-03 | info | open | - (not in the current review) |
| IN-04 | info | open | iteration-2 delta re-review (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
