---
phase: 05-ci-e2-rerun
recorded: 2026-10-10T20:56:28+08:00
source: [05-REVIEW.md, 05-REVIEW-FIX.md]
iterations: 1
total_findings: 7
fixed: 4
skipped: 0
open: 3
status: reconciled
---

# Phase 05 — Review Disposition Ledger

Single fix pass (no --auto loop), MAIN tree. Fix commits 87d10b3..d87c0b6 on
autorun. Final suite: 310 passed (Python; baseline 307 + 3 review-fix tests) +
node lane 15; make lint / make typecheck clean; make data no-op after the
WR-01 regeneration commit (drift gate green).

| ID | Severity | Finding | Disposition | Evidence |
|----|----------|---------|-------------|----------|
| WR-01 | warning (medium) | permutation artifact info.axis did not disclose paired-test semantics | fixed | 87d10b3 (axis reworded; artifact regenerated via make data — 1-line info change, 861 pair rows byte-identical; drift no-op proven post-commit) |
| WR-02 | warning (low, latent) | priority/failure files accept Train-falsy task names (vs _validate_filters discipline) | fixed | d41a7db (_load_registry_key_sets returns Train-falsy set; both validators append named problem; +2 tests over the fixture's Train=0 task-y) |
| WR-03 | warning (low, latent) | --subset_file validates registry KEYS but applies via Dataset_name | fixed | 39b2021 (validation-time cross-check, named problem + non-zero [Error] exit; + synthetic-divergence test; real-registry no-op verified over all 50 rows) |
| IN-01 | info | tie-rule boundary semantics under mixed interval presence | info-open (documented) | REVIEW — per-plan intentional behavior, pinned by test_ci_map_none_and_missing_entries_reproduce_exact_tie_output; recorded so the E2' ci_map wiring review treats it as intentional. E2'-time consideration, no code change now. |
| IN-02 | info | audit ID space assumes HF row order equals CSV file order | info-open | REVIEW — belt-and-braces `len(dataset.dataset["test"]) == audit rows` assert belongs at the E2' seam (apply_eval_subset consumer), not in this phase's scope; deferred to the E2' wiring review. |
| IN-03 | info | CI eslint lane could go vacuously green on a glob/config drift | info-open | REVIEW — hardening gap, not a current defect; `--max-warnings 0` on the pinned eslint invocation is a CI-config change outside this run's surgical-fix scope. Non-vacuousness is execution-proven today (05-01 negative probes). |
| IN-04 | info | stale legacy usage line in summarize_comparison.py docstring | fixed | d87c0b6 (docstring usage block now points at repo-root `make data`, keeping the CWD-sensitivity note — the orchestrator-sanctioned documentation one-liner inside a phase-5-touched file) |

Notes:
- Disposition directive honored exactly: all three warnings FIX; info
  findings recorded open except IN-04 (trivial documentation one-liner fully
  inside `script/summarize_comparison.py`, a phase-5-touched file).
- CHANGELOG untouched for WR-01: the [1.1.0] methodology bullet already
  discloses "paired permutation test (`permutation_type='samples'`)" — the
  fix brought the artifact up to the existing disclosure; the workflow's
  convention requires no duplicate line for a disclosure rewording that
  moves no number.
- No critical findings existed in the review (0 critical / 3 warning / 4
  info).
