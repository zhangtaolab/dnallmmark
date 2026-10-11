---
status: complete
phase: 05-ci-e2-rerun
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md, 05-04-SUMMARY.md, 05-VERIFICATION.md]
started: 2026-10-10T21:24:00+08:00
updated: 2026-10-10T21:24:00+08:00
---

## Current Test

number: 2
name: Phase 5 overall acceptance
expected: |
  All four plans accepted; verification PASSED (24/24); review/fix converged
awaiting: resolved

## Tests

### 1. Visual localhost check — weighted default view, one-click toggle, stamped footer (05-02 Task 3, WINDOWS #11)
expected: |
  bash start-server.sh → http://localhost:8080 opens the leaderboard on the
  Weighted view by default; one click on Raw Rank re-sorts the table and
  relabels the scatter y-axis; footer shows the stamped date + data v1.1.0
  with no today's-date behavior. Mechanical seams pinned by
  tests/js/main-view-toggle.test.js (node lane 15/15).
result: passed
reported: "All good — continue"

### 2. Phase 5 overall acceptance (4 plans + review/fix convergence + gates)
expected: |
  05-01 CI harness, 05-02 F6 aggregation migration, 05-03 N-audit + eval
  subsets, 05-04 E2' readiness all complete; 0 critical review findings,
  3 warnings fixed with tests, 4 info dispositioned; make test 310 + node 15,
  lint/typecheck clean, drift no-op.
result: passed
reported: "All good — continue"
