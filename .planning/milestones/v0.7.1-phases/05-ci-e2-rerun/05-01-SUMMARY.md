---
phase: 05-ci-e2-rerun
plan: 01
subsystem: infra
tags: [github-actions, ci, pytest-markers, golden-replay, eslint, html-validate, drift-detection, sha-pinning]

# Dependency graph
requires:
  - phase: 04-correctness-methodology-core
    provides: deterministic data chain (make data byte-identical no-op), schemas + goldens the replay asserts against, 236-test green suite
provides:
  - .github/workflows/ci.yml — the repo's first CI workflow (lint/typecheck, test matrix, JS/HTML static checks, data drift job; all actions SHA-pinned; every job timeout-minutes: 14)
  - tests/fixtures/e2_replay/ + tests/test_ci_replay.py — committed canned golden replay (3 models x 1 task x 3 seeds) proving export -> schema, aggregate -> schema, byte-stability end-to-end under pytest
  - pinned `ci` pytest marker lane + `make ci` (reuses metric-key parity, species spot checks, aggregation units — zero duplicated tests)
  - eslint.config.mjs + .htmlvalidate.json — manifest-free static-check configs for exact-pin npx invocation
  - TEST-07 drift gate: `make data && git diff --exit-code -- dnallm-mark/data/` (green on the committed tree)
affects: [05-ci-e2-rerun (05-02 F6 migration lands under drift protection; 05-04 extends the replay), future public release]

# Actuals (#2632) — measured from the plan ledger (base 5d084c9)
actuals:
  tokens: 12040   # chars/4 over the realized diff (48161 chars) — plan estimate 50000
  tasks: 3        # Task 1 + Task 2 (checkpoint, maintainer-approved) + Task 3
  commits: 2      # MEASURED: git rev-list --count 5d084c9..HEAD (c1b4b24, d546e30)
plan_head_before: 5d084c90c2b4ece8afee49754ff12bc7a8fab5d
plan_head_after: d546e30c4a897edaaeb2c5dcb0e45db2cbc4034f

# Tech tracking
tech-stack:
  added: []        # nothing installed into the repo — CI pulls at run time:
                   # eslint@10.12.0 + html-validate@11.16.2 via exact-version npx (no package.json, no lockfile)
  patterns:
    - "SHA-pinned actions (40-char commit SHA + '# vX.Y.Z' comment) resolved from official repos at execution time, never from third-party listings"
    - "Canned golden replay: ephemeral test-tree builders transcribed into committed fixtures so CI proves the chain without any training"
    - "Manifest-free static checks: exact-version npx pins with dependency-free flat configs (inlined globals, no @eslint/js import)"

key-files:
  created:
    - .github/workflows/ci.yml
    - eslint.config.mjs
    - .htmlvalidate.json
    - tests/test_ci_replay.py
    - tests/fixtures/e2_replay/   # 30-file tree: 3 models x 1 task x 3 seeds + config + registry slices
    - .planning/phases/05-ci-e2-rerun/05-USER-SETUP.md
  modified:
    - Makefile                    # `ci` lane + header note
    - pyproject.toml              # `ci` marker registration
    - tests/test_aggregation.py   # module-level ci pytestmark (aggregation units)
    - tests/test_export_runs.py   # ci pytestmark (metric-key parity)
    - tests/test_known_defects.py # ci pytestmark (species spot checks)
    - .gitignore                  # fixture-negation fix
    - README.md                   # CI badge
    - dnallm-mark/js/task.js      # Object.entries -> Object.keys (lint-blocking unused binding)

key-decisions:
  - "Action SHAs resolved this session from the official repos (git ls-remote + GitHub API, both reporting type:commit): checkout v7.0.1 3d3c42e5, setup-uv v10.3.0 1c37ad07, setup-node v7.1.0 949feb24 — setup-uv had drifted past the research doc's v8.x listing, confirming A2"
  - "eslint config tunes no-unused-vars to documented repo idioms instead of editing six files: varsIgnorePattern '^app$' (page-controller singleton instantiation), caughtErrors 'none' (catch-and-continue error strategy), args 'none'"
  - "html-validate rule set is the structural core only (close-order, no-dup-id, no-dup-attr, element-permitted-content/parent, element-name); rule name is no-dup-id in 11.x — 'duplicate-id' does not exist"
  - "Test matrix = 3.13 required + 3.14 continue-on-error probe (TEST-04's literal 3.12 text superseded by requires-python >= 3.13, D-07 — plan-instructed deviation)"
  - "Task 2 gate disposition (recorded verbatim): maintainer reply `approved` — eslint@10.12.0 + html-validate@11.16.2 blessed with the exact-pin npx-no-package.json form"

patterns-established:
  - "Negative-probe discipline for lint configs: every green static-check lane is proven non-vacuous by feeding it a known-defective input (dup-ID HTML; dup-key + undefined-global JS) and observing rejection"
  - "CI lanes are Makefile entry points (make lint/typecheck/test/data) — the workflow invokes exactly what local development runs"

requirements-completed: [REV-06, TEST-04, TEST-05, TEST-07]

# Coverage metadata (#1602)
coverage:
  - id: D1
    description: "Canned golden replay: committed 3x1x3 run-record fixture + test_ci_replay.py proving export_runs -> task_performance schema validity, seed_stats n_seeds=3 t-interval (method 't', two-float ci95), and byte-stability across two runs for both the export and the aggregate half"
    requirement: REV-06
    verification:
      - kind: integration
        ref: "uv run --group dev pytest -m ci (tests/test_ci_replay.py) — 63 passed in the ci lane"
        status: pass
      - kind: integration
        ref: "make test — full suite 236 passed + 0 xfailed (replay inside the full suite)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Pinned `ci` pytest marker lane: marker registered in pyproject.toml, module pytestmarks added to the three reused test classes, `make ci` lane in the Makefile"
    requirement: REV-06
    verification:
      - kind: unit
        ref: "make ci — 63 passed; pytest -m ci --collect-only selects exactly test_ci_replay/test_aggregation/test_export_runs/test_known_defects (proven at Task 1)"
        status: pass
    human_judgment: false
  - id: D3
    description: ".github/workflows/ci.yml: four jobs (lint-typecheck, test matrix 3.13-required + 3.14-probe, static-js, drift), every action 40-char-SHA-pinned with version comments, permissions: contents: read, push(main)+pull_request only, timeout-minutes: 14 on every job"
    requirement: TEST-04
    verification:
      - kind: other
        ref: "pyyaml safe_load over the workflow (YAML parses); grep proves zero mutable @vN tags and 4/4 jobs carry timeout-minutes: 14"
        status: pass
      - kind: other
        ref: "every lane's command sequence run locally at repo root: make lint, make typecheck, make test, node --test, node --check x11, make data + git diff --exit-code"
        status: pass
    human_judgment: true
    rationale: "The workflow's first execution on a real GitHub runner happens on the maintainer's next push — runner-side behavior (action SHAs resolving, uv sync on the runner, badge going green, <15-min wall clock) is not locally provable before that push"
  - id: D4
    description: "Frontend static checks: eslint.config.mjs (ESLint 10 flat config, browser/CDN globals inlined, zero npm imports) + .htmlvalidate.json (structural rules over exactly the six real shells) + node --check over dnallm-mark/js/ and scripts/"
    requirement: TEST-05
    verification:
      - kind: other
        ref: "npx --yes eslint@10.12.0 --config eslint.config.mjs \"dnallm-mark/js/*.js\" — exit 0"
        status: pass
      - kind: other
        ref: "npx --yes html-validate@11.16.2 --config .htmlvalidate.json <six shells> — exit 0"
        status: pass
      - kind: other
        ref: "negative probes: dup-ID HTML and dup-key/undef-global JS are both rejected by the pinned tools under the committed configs"
        status: pass
    human_judgment: false
  - id: D5
    description: "Data drift gate (TEST-07): drift job runs `make data` then `git diff --exit-code -- dnallm-mark/data/`; the committed tree is a verified regeneration no-op"
    requirement: TEST-07
    verification:
      - kind: integration
        ref: "make data && git status --porcelain -- dnallm-mark/data/ -> empty; git diff --exit-code -- dnallm-mark/data/ -> exit 0 (the exact CI step, run locally)"
        status: pass
    human_judgment: false
  - id: D6
    description: "README carries the ci.yml workflow status badge (zhangtaolab/dnallmmark slug)"
    requirement: TEST-04
    verification:
      - kind: other
        ref: "grep 'actions/workflows/ci.yml/badge.svg' README.md — markdown link present at line 5"
        status: pass
    human_judgment: false

# Metrics
duration: 74min
completed: 2026-10-10
status: complete
---

# Phase 5 Plan 1: CI golden-test harness Summary

**Canned golden replay fixture + pinned ci marker lane + SHA-pinned GitHub Actions workflow (lint/typecheck, 3.13+3.14 test matrix, eslint/html-validate static checks, zero-drift data gate) with every lane proven locally before commit**

## Performance

- **Duration:** 74 min (plan-start 2026-10-10T08:46:36Z -> 2026-10-10T10:00:56Z; spans the Task-2 maintainer checkpoint wait)
- **Started:** 2026-10-10T08:46:36Z
- **Completed:** 2026-10-10T10:00:56Z
- **Tasks:** 3/3 (Task 1 tracer fixture+lane; Task 2 blocking-human package-legitimacy gate — approved; Task 3 workflow+configs+badge)
- **Files modified:** 42 (30 fixture tree files + 12 source/config/doc files)

## Accomplishments

- Committed canned golden replay (`tests/fixtures/e2_replay/`, 3 models x 1 task x 3 seeds incl. trainer_state.json/final_metrics.json/config + registry slices; models A/B carry near-identical AUPRC per-seed values reproducing the CpG top-10 overlap input for 05-02) with `tests/test_ci_replay.py` asserting schema validity + n_seeds=3 t-intervals + byte-stability on both halves — the phase's chain proven end-to-end under pytest with zero training
- Pinned `ci` marker lane (pyproject registration, pytestmarks on the three reused test classes, `make ci`) — 63 tests, no duplication
- `.github/workflows/ci.yml`: the repo's first CI workflow — four jobs, every `uses:` pinned by full 40-char commit SHA resolved from the official repos this session (checkout v7.0.1 / setup-uv v10.3.0 / setup-node v7.1.0), `permissions: contents: read`, no fork-triggering variant, `timeout-minutes: 14` everywhere (REV-06 Q4 as enforced fact)
- Manifest-free static-check configs (`eslint.config.mjs`, `.htmlvalidate.json`) + README CI badge; both pinned npx invocations green locally and proven non-vacuous by negative probes
- TEST-07 drift gate proven green on the untouched tree (byte-identical `make data` no-op) — the guard exists BEFORE 05-02 moves any public number

## Task Commits

Each task was committed atomically:

1. **Task 1: Canned golden replay fixture + pinned ci marker lane** - `c1b4b24` (test) — 37 files; prior-executor commit, fresh-checkout proven; make ci = 63 passed, full suite 236 + node lane 8, `uv lock --check` clean
2. **Task 2: Package-legitimacy gate (checkpoint:human-verify, blocking-human)** - no commit (gate) — maintainer reply `approved` (see Gate Resolutions)
3. **Task 3: CI workflow + static-check configs + README badge** - `d546e30` (feat)

**Plan metadata:** see final docs commit below.

## Gate Resolutions (Checkpoints)

- **Task 2 — package-legitimacy gate (blocking-human), RESOLVED:** The CI static-check lane fetches exactly two npm packages at run time via exact-version pins with no package.json and no lockfile (research A1). Both were flagged [SUS] by the legitimacy gate solely on publish recency, so per policy they were never auto-approvable. **Maintainer disposition, recorded verbatim: `approved`** — eslint@10.12.0 + html-validate@11.16.2 blessed with the exact-pin npx-no-package.json form (also recorded in the Task-3 commit message). The two pinned npx invocations during Task 3 were the first fetches of these tools.

## Files Created/Modified

- `.github/workflows/ci.yml` - the single CI workflow (4 SHA-pinned jobs; every lane mirrors a Makefile entry point)
- `eslint.config.mjs` - ESLint 10 flat config; inlined browser/CDN globals; correctness-core rules; zero imports (manifest-free npx form)
- `.htmlvalidate.json` - html-validate 11 structural rules over the six real shells
- `tests/test_ci_replay.py` - export->schema, aggregate->schema, byte-stability assertions over the committed fixture
- `tests/fixtures/e2_replay/` - 30-file micro run-record tree (3 models x FakeCpG__methylation x 3 seeds)
- `Makefile` / `pyproject.toml` - `make ci` lane + `ci` marker registration
- `tests/test_aggregation.py`, `tests/test_export_runs.py`, `tests/test_known_defects.py` - module-level ci pytestmarks (existing pytestmark lists extended, nothing replaced)
- `.gitignore` - fixture-tree negation fix
- `README.md` - CI badge
- `dnallm-mark/js/task.js` - one-line Object.entries -> Object.keys (see Deviations #2)

## Decisions Made

- Action SHAs re-resolved at execution time (plan assumption A2 held: research listing was stale — setup-uv moved v8.x -> v10.3.0). Method: `git ls-remote` over the official repos + GitHub API `git/ref/tags` cross-check confirming each tag object is `type: commit` (lightweight tags, so the listed SHA is the commit itself).
- eslint `no-unused-vars` tuned to documented repo idioms (page-controller `const app = new X()` singleton; catch-and-continue bindings) rather than editing 6+ production files — keeps the fix surface surgical per the milestone constraint.
- html-validate 11.x rule name is `no-dup-id` (`duplicate-id` does not exist); final rule set is structural-only, per plan ("without style noise").
- `setup-node` (node 24) added to the `test` job beyond the plan's literal "setup-uv" — see Deviations #1.
- The YAML-parse verify ran through the repo venv (`uv run --group dev python -c "import yaml; ..."`): system python3 has no PyYAML and no network install was permitted (the venv's pyyaml 6.0.3 arrives via the locked data-group chain).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] setup-node added to the `test` CI job**
- **Found during:** Task 3 (workflow authoring)
- **Issue:** The plan describes the test job as "setup-uv, matrix ..., `make test`" — but `make test` hard-depends on node (Makefile `check-node` guard exits 1 without it; the recipe runs `node --test tests/js/`). Relying on the runner image's preinstalled node would be image-drift-fragile.
- **Fix:** Added `actions/setup-node` (node-version 24, same pin as static-js) to the test job.
- **Files modified:** .github/workflows/ci.yml
- **Verification:** `make test` proven locally (236 passed + node 8); the job's command surface is unchanged.
- **Committed in:** d546e30

**2. [Rule 1 - Bug] Unused destructured binding blocked the green eslint lane**
- **Found during:** Task 3 (first eslint run: 13 errors)
- **Issue:** `dnallm-mark/js/task.js:270` iterated `for (const [key, value] of Object.entries(firstModelPerf))` reading only `key`; the unused `value` binding is a genuine lint finding, not a documented idiom.
- **Fix:** `for (const key of Object.keys(firstModelPerf))` — identical iteration order and case-insensitive comparison, zero behavior change. (The other 12 findings were config-side: missing `FormData`/`alert` globals, plus the documented-idiom tunings recorded under Decisions.)
- **Files modified:** dnallm-mark/js/task.js
- **Verification:** eslint exit 0; `make test` green (node lane 8/8); `node --check` clean.
- **Committed in:** d546e30

**3. [Plan-acknowledged deviation] TEST-04 matrix text superseded (3.12 -> 3.13 + 3.14 probe)**
- **Found during:** Task 3 (per plan instruction: "TEST-04's literal 3.12 text is superseded, record the deviation")
- **Issue:** TEST-04's literal matrix text names 3.12/3.13; `requires-python = ">=3.13"` (D-07) makes a 3.12 leg unresolvable.
- **Fix:** Matrix = 3.13 (required floor leg) + 3.14 (`continue-on-error: true` forward-compat probe), per research Pitfall 6.
- **Files modified:** .github/workflows/ci.yml
- **Verification:** Workflow YAML validates; the 3.13 leg's exact command (`make test`) proven locally.
- **Committed in:** d546e30

---

**Total deviations:** 3 (1 blocking-issue fix, 1 bug fix, 1 plan-acknowledged requirement-text deviation)
**Impact on plan:** All three were necessary for a green, deterministic CI lane; no scope creep. The eslint tuning avoided touching six production files for a documented idiom.

## Issues Encountered

- html-validate rejected the config's `duplicate-id` rule name ("definition not found") — resolved by discovering the 11.x name `no-dup-id` from the pinned tool itself; final config passes all six shells and rejects a dup-ID probe.
- System `python3` (3.14.7) lacks PyYAML, so the plan's literal verify command cannot run there; the identical check ran through the repo venv (pyyaml 6.0.3, offline, no installs). No network fetches beyond the two sanctioned npx invocations + the plan-mandated action-SHA resolution (git ls-remote / GitHub API).

## User Setup Required

**External services require manual configuration.** See [05-USER-SETUP.md](./05-USER-SETUP.md) for:
- GitHub branch protection: make the four ci.yml checks required before merging (REV-06 "PR-required" clause). Note: checks become selectable only after the workflow's first run on the runner.

## Known Stubs

None — no stub patterns exist in any file created or modified by this plan.

## Next Phase Readiness

- 05-02 (F6 aggregation upgrade) can proceed: the drift gate is green on the untouched tree, so the F6 migration commit's data movement will be attributable and CI-visible from its first commit. The replay fixture's A/B near-identical AUPRC seeds are the deliberate input for 05-02's tie-rule test.
- The workflow's first real runner execution happens on the maintainer's next push (badge + branch-protection steps queued in 05-USER-SETUP.md; also recorded in the WINDOWS ledger as an unrun-verify so the ship gate sees it).

## Self-Check: PASSED

All 11 key files exist on disk (incl. the 30-file fixture tree); both task commits (c1b4b24, d546e30) are ancestors of HEAD; README badge present.

---
*Phase: 05-ci-e2-rerun*
*Completed: 2026-10-10*
