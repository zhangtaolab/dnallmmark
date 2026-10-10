# Phase 05: CI & Three-Seed Full Re-Run (E2') — UAT Record

**Date:** 2026-10-10
**Result:** ✅ PASSED

## Gate

Interactive UAT presented to the maintainer after VERIFICATION PASSED (05-VERIFICATION.md, d2877b0, 24/24 must-haves, fingerprint `v3:sha256:53047219266e2d8b7076ef72bc899efc2fa257ea1a7555ac47e5e517c0d037b4`).

**Maintainer response:** "All good — continue"

## Items covered

1. **05-02 Task 3 visual localhost check** (WINDOWS #11) — leaderboard default Weighted view, one-click Raw Rank toggle (table re-sort + scatter y-axis relabel), stamped footer (date + data v1.1.0, no today's-date behavior). Mechanical seams pinned by tests/js/main-view-toggle.test.js (node lane 15/15); browser-level confirmation accepted by the maintainer.
2. **Phase 5 overall acceptance** — 4/4 plans (05-01 CI harness, 05-02 F6 aggregation migration, 05-03 N-audit + eval subsets, 05-04 E2' readiness), review/fix convergence (0 critical / 3 warnings fixed / 4 info dispositioned), 25 commits, all gates green (make test 310 + node 15, lint, typecheck, drift no-op).

## Deferred to maintainer (not UAT blockers — recorded in 05-USER-SETUP.md and WINDOWS)

- First real GitHub-runner execution of ci.yml + branch protection setup (WINDOWS #10)
- E2' launch: env_smoke on GB10 + explicit go, sweep execution, first real --subset_file consumption, data-v2 tag (WINDOWS #12 — dual-gate maintainer action)
