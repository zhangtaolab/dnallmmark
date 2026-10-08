---
phase: 01
review: 01-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "Live Zenodo preview JWT committed in public README — residual risk untracked"
  - id: WR-02
    severity: warning
    disposition: open
    title: "README says Python 3.11+ while the repo pins >=3.13"
  - id: WR-03
    severity: warning
    disposition: open
    title: "`baseline/compare.py` diff ordering is nondeterministic across processes"
  - id: WR-04
    severity: warning
    disposition: open
    title: "`baseline/compare.py` cannot detect int↔float type drift and false-positives on NaN"
  - id: WR-05
    severity: warning
    disposition: open
    title: "`sum_PFLOPs`/`avg_PFLOPs` include FLOPs from tasks the model is not ranked on"
  - id: WR-06
    severity: warning
    disposition: open
    title: "Dataset species labels contradict the datasets' own identity (fungi → Animals, human cell line → Microbe)"
  - id: WR-07
    severity: warning
    disposition: open
    title: "Documented output filenames are plural; the generator writes singular (AUD-19 persists in reviewed files)"
  - id: WR-08
    severity: warning
    disposition: open
    title: "gitleaks allowlist path regex is unanchored — broader than the documented intent"
  - id: WR-09
    severity: warning
    disposition: open
    title: "README's data-regeneration docs omit the third generator entirely"
  - id: IN-01
    severity: info
    disposition: open
    title: "Dead counter variable"
  - id: IN-02
    severity: info
    disposition: open
    title: "Metric-presence check is narrower than `get_float`'s missing-value semantics"
  - id: IN-03
    severity: info
    disposition: open
    title: "No per-file error handling in the index generator"
  - id: IN-04
    severity: info
    disposition: open
    title: "Double spaces in generated task display names"
  - id: IN-05
    severity: info
    disposition: open
    title: "`top8_count` missing from README's documented output fields"
  - id: IN-06
    severity: info
    disposition: open
    title: "`.gitignore` carries upstream-dnallm rules for paths that do not exist here"
open: 15
total: 15
recorded: 2026-10-08T15:12:20.399Z
---

# Phase 01: Code Review Disposition

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
| WR-09 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| IN-06 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved.
