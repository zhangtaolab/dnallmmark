# Phase 5: User Setup Required

**Generated:** 2026-10-10
**Phase:** 05-ci-e2-rerun (plan 05-01 — CI golden-test harness)
**Status:** Incomplete

Complete these items for the CI gate to function as REV-06 intends ("PR-required"). Claude automated everything possible (workflow, configs, badge, local lane proofs); these items require maintainer access to the GitHub repository settings.

## Environment Variables

None required — the workflow references no secrets (by design: top-level `permissions: contents: read`, no `secrets.*` anywhere in `.github/workflows/ci.yml`).

## Account Setup

None required — the repository already exists under the `zhangtaolab` org.

## Dashboard Configuration

- [ ] **Make the ci.yml checks required before merging**
  - Location: GitHub repo Settings -> Branches -> Branch protection rules (rule for the default branch, `main`)
  - Set to: Enable "Require status checks to pass before merging" and select the checks from the `ci.yml` workflow:
    - `Lint + typecheck (ruff / ty)`
    - `Test (Python 3.13)` (the required floor leg — do NOT make the 3.14 probe leg required; it is `continue-on-error` by design)
    - `Static JS/HTML checks`
    - `Data drift (make data must be a byte-identical no-op)`
  - Notes:
    - A status check only becomes selectable in this UI **after it has run at least once** — push (or open a PR touching `.github/workflows/ci.yml`) first, then configure branch protection.
    - The 3.14 matrix leg reports as non-blocking (yellow/continue-on-error); requiring `Test (Python 3.13)` covers the required leg.
    - The 7 GUE dataset dirs and all GPU work stay outside CI by design; nothing here needs self-hosted runners.

## Verification

After completing setup, verify with:

```bash
# 1. Badge is live and green (after the first run of the workflow on main)
#    open https://github.com/zhangtaolab/dnallmmark — the CI badge near the README title

# 2. Checks appear as required on a new PR (open any draft PR; the four ci.yml
#    checks must be listed as required, with 3.14 shown as non-blocking)

# 3. Locally, the lanes the workflow runs (already proven at commit d546e30):
make lint && make typecheck && make ci
make data && git diff --exit-code -- dnallm-mark/data/ && echo "no drift"
```

Expected results:
- Badge renders green after the first workflow run completes under 15 minutes per job (`timeout-minutes: 14` enforces it).
- Merging a PR with a red ci.yml check is blocked by branch protection.

---

**Once all items complete:** Mark status as "Complete" at top of file.
