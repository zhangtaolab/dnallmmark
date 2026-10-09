---
phase: 01
review: 01-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "Live Zenodo preview JWT committed in public README — residual risk untracked"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "README says Python 3.11+ while the repo pins >=3.13"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "`baseline/compare.py` diff ordering is nondeterministic across processes"
  - id: IN-01
    severity: info
    disposition: fixed
    title: "Dead counter variable"
  - id: IN-02
    severity: info
    disposition: fixed
    title: "Metric-presence check is narrower than `get_float`'s missing-value semantics"
  - id: IN-03
    severity: info
    disposition: fixed
    title: "No per-file error handling in the index generator"
  - id: IN-04
    severity: info
    disposition: fixed
    title: "Double spaces in generated task display names"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "`baseline/compare.py` cannot detect int↔float type drift and false-positives on NaN"
  - id: WR-05
    severity: warning
    disposition: skipped
    title: "`sum_PFLOPs`/`avg_PFLOPs` include FLOPs from tasks the model is not ranked on"
  - id: WR-06
    severity: warning
    disposition: skipped
    title: "Dataset species labels contradict the datasets' own identity (fungi → Animals, human cell line → Microbe)"
  - id: WR-07
    severity: warning
    disposition: fixed
    title: "Documented output filenames are plural; the generator writes singular (AUD-19)"
  - id: WR-08
    severity: warning
    disposition: fixed
    title: "gitleaks allowlist path regex is unanchored — broader than the documented intent"
  - id: WR-09
    severity: warning
    disposition: fixed
    title: "README's data-regeneration docs omit the third generator entirely"
  - id: IN-05
    severity: info
    disposition: fixed
    title: "`top8_count` missing from README's documented output fields"
  - id: IN-06
    severity: info
    disposition: fixed
    title: "`.gitignore` carries upstream-dnallm rules for paths that do not exist here"
open: 0
total: 15
recorded: 2026-10-09T00:42:04.402Z
---

# Phase 01: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | 01-REVIEW-FIX.md (not in the current review) |
| WR-02 | warning | fixed | 01-REVIEW-FIX.md (not in the current review) |
| WR-03 | warning | fixed | 01-REVIEW-FIX.md (not in the current review) |
| IN-01 | info | fixed | 01-REVIEW-FIX.md (not in the current review) |
| IN-02 | info | fixed | 01-REVIEW-FIX.md (not in the current review) |
| IN-03 | info | fixed | 01-REVIEW-FIX.md (not in the current review) |
| IN-04 | info | fixed | 01-REVIEW-FIX.md (not in the current review) |
| WR-04 | warning | fixed | 01-REVIEW-FIX.md (not in the current review) |
| WR-05 | warning | skipped | 01-REVIEW-FIX.md (not in the current review) |
| WR-06 | warning | skipped | 01-REVIEW-FIX.md (not in the current review) |
| WR-07 | warning | fixed | 01-REVIEW-FIX.md (not in the current review) |
| WR-08 | warning | fixed | 01-REVIEW-FIX.md (not in the current review) |
| WR-09 | warning | fixed | 01-REVIEW-FIX.md (not in the current review) |
| IN-05 | info | fixed | 01-REVIEW-FIX.md (not in the current review) |
| IN-06 | info | fixed | 01-REVIEW-FIX.md (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
