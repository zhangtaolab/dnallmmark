# Roadmap: DNALLM-Mark

## Overview

This is a hardening milestone over an existing, working platform — not a build. A verification layer is wrapped around the three subsystems (GPU pipeline, offline data chain, static leaderboard site) in the one order that keeps every leaderboard number attributable: audit the codebase and freeze the pre-fix baseline; lock the data contract with schemas and a CPU-only test harness; adapt the GPU pipeline to the dnallm dev branch and prove the adaptation with a real run; land the known correctness fixes surgically under test evidence; recompute the leaderboard under full CI protection with a changelogged, tagged number migration; and finish with the provenance, methodology, and onboarding documentation external reviewers need to trust and extend the platform. Done right, the public leaderboard carries numbers that are correct, reproducible, and defensible under external scrutiny.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Audit & Release Foundations** - Findings report over all three subsystems, pre-fix baseline frozen (`data-v1`), LICENSE + pinned manifests, deterministic generators, secret-hygiene decision applied (intentional Zenodo preview link kept; scan confirms no other secrets)
- [ ] **Phase 2: Data Contracts & Test Harness** - Four JSON Schemas, CPU-only unit/golden/determinism tests over the data chain, and a single-command Makefile — locked before any number moves
- [ ] **Phase 3: Pipeline Adaptation to dnallm Dev** - Pipeline adapted to dnallm dev (v0.7.1), GPU environment reproducibly buildable on the GB10 machine, one end-to-end fine-tune run emitting schema-valid output
- [ ] **Phase 4: Correctness Fixes** - Every page renders (navbar fix), species-grouping fixed test-first in the adapted pipeline, submission flow restored, escaping at touched DOM-build sites
- [ ] **Phase 5: CI & Verified Data Migration** - GitHub Actions CI (lint, test matrix, frontend checks, drift detection) plus post-fix recomputation with a changelogged, tagged before/after record
- [ ] **Phase 6: Release Packaging & Provenance** - README reproducibility commands, 50-dataset provenance table + downloadable manifest, aggregation-methodology docs, validated onboarding guides

## Phase Details

### Phase 1: Audit & Release Foundations

**Goal**: The repo is safe for public visibility and every future number change is attributable — all three subsystems audited with evidence, the pre-fix state frozen, and the reproducibility substrate (license, pinned dependencies, deterministic generators) in place
**Depends on**: Nothing (first phase)
**Requirements**: AUDIT-01, AUDIT-02, REL-01, REL-02, REL-05, FIX-05
**Success Criteria** (what must be TRUE):
  1. A findings report covers pipeline, data scripts, and frontend, with every finding severity-graded and backed by `file:line` evidence plus a recommended fix
  2. The pre-fix state is recoverable and diffable — a `data-v1` git tag and golden baseline outputs of the current data chain exist — before any result-affecting fix lands
  3. Running the data-regeneration chain twice from a clean checkout produces byte-identical derived JSON
  4. A fresh contributor can install the CPU-only data-chain dependencies from version-pinned manifests (`pandas>=2.2,<3.0`), with GPU pipeline dependencies isolated in a separate group CI never installs
  5. The repo is publishable: a LICENSE file exists with data licensing declared separately, and the secret-hygiene decision (2026-10-08) is applied — the intentional Zenodo record-19135551 preview link at `README.md:116` stays as-is while a full-history secret scan confirms no OTHER secrets exist beyond that known-intentional link

**Plans**: 1/3 plans executed
Plans:
**Wave 1**
- [x] 01-01-PLAN.md — Freeze data-v1 baseline (comparator + SHA256 manifest + tag) and pin the data-chain environment (pyproject/uv.lock/requirements + pin validation)

**Wave 2** *(blocked on Wave 1 completion)*
- [ ] 01-02-PLAN.md — Three-subsystem systematic audit with parallel review agents and verified, severity-graded findings published as AUDIT.md

**Wave 3** *(blocked on Wave 2 completion)*
- [ ] 01-03-PLAN.md — FIX-05 deterministic generators + one-time attributed data migration, LICENSE + data terms, gitleaks full-history scan with narrow allowlist

### Phase 2: Data Contracts & Test Harness

**Goal**: The data chain is guarded by executable contracts and a stable CPU-only test harness — schemas, unit tests, golden files, determinism regression, and a single-command Makefile — locked before any correctness fix moves the numbers
**Depends on**: Phase 1
**Requirements**: REL-04, TEST-01, TEST-02, TEST-03, TEST-06
**Success Criteria** (what must be TRUE):
  1. `make data` regenerates all derived leaderboard files in one command from repo root — no undocumented CWD-sensitive steps — and `make test` / `make lint` run the full local suite
  2. Unit tests over synthetic fixtures exercise rank/MinMax/z-score/robust aggregation and the model-to-task pivot logic, CPU-only and passing; the species-as-dataset bug is captured as a known-failing test that the Phase 4 fix must turn green
  3. Every committed leaderboard JSON validates against one of the four JSON Schemas (model_performance, task_performance, models_comparison, tasks_index), so a malformed or shape-drifted derived file fails the suite
  4. Golden-file tests pass over a synthetic fixture tree, and a determinism regression test re-runs the chain expecting byte-identical output
  5. The suite is stable by construction — float assertions carry explicit tolerances (`pytest.approx`) and thread counts are pinned in conftest — so repeated local runs do not flake

**Plans**: TBD

### Phase 3: Pipeline Adaptation to dnallm Dev

**Goal**: The fine-tuning pipeline runs against the dnallm dev branch — code adapted, GPU environment reproducibly buildable on the local machine, and proven by a real end-to-end run whose output passes the data contract
**Depends on**: Phase 2
**Requirements**: PIPE-01, PIPE-02, PIPE-03
**Success Criteria** (what must be TRUE):
  1. The pipeline's imports resolve and a dry-run completes against the dnallm dev clone (v0.7.1 @ `c99fa9d`, `/home/forrest/Github/DNALLM`) with all API/config-schema deltas resolved
  2. A maintainer can rebuild the GPU pipeline environment from documented commands on the NVIDIA GB10 aarch64 machine (uv/venv; dnallm installed from the local dev clone; torch/transformers pinned per dnallm 0.7.1 bounds)
  3. At least one model×dataset fine-tune completes end-to-end against dnallm dev and produces a `{model}_performance.json` that validates against the Phase 2 model_performance schema

**Plans**: TBD

### Phase 4: Correctness Fixes

**Goal**: Every page works and every confirmed correctness bug is fixed surgically — one fix per review unit, each backed by test evidence, with only fix-explained deltas in the diff
**Depends on**: Phase 3
**Requirements**: FIX-01, FIX-02, FIX-03, FIX-04
**Success Criteria** (what must be TRUE):
  1. A visitor can load every page (main leaderboard, task benchmark, finetuning, models, datasets) with no console errors, working navigation, and fully rendered content — verified on ALL pages, not just the three known-broken ones
  2. A user can complete the submission flow: `submit.html` is reachable from navigation, validates a submission client-side, and generates correct PR instructions against the current data schema
  3. The species-as-dataset grouping fix is in — landed in the dnallm-dev-adapted pipeline — its Phase 2 failing test now passes, and the aggregation diff shows only changes the fix explains
  4. DOM-build sites touched by these fixes escape rendered content, so a hostile string in any performance JSON displays as inert text, not markup

**Plans**: TBD
**UI hint**: yes

### Phase 5: CI & Verified Data Migration

**Goal**: CI proves repo health end-to-end, and the leaderboard numbers are recomputed under that protection with an attributable, changelogged, tagged migration from pre-fix to post-fix data
**Depends on**: Phase 4
**Requirements**: TEST-04, TEST-05, TEST-07, DATA-01, DATA-02, DATA-03, DATA-06
**Success Criteria** (what must be TRUE):
  1. Every push and PR runs GitHub Actions CI — lint plus the test matrix on Python 3.12/3.13 and a Node job, SHA-pinned actions, least-privilege permissions — green on main, with a README badge
  2. Frontend regressions block merges: ESLint (flat config), html-validate, and `node --check` all run in CI
  3. Stale derived data is a build failure: a PR that changes source data without regenerating derived files fails the drift-detection job, which names the stale files
  4. Leaderboard data is recomputed after the fixes; a before/after comparison artifact records which numbers moved and why, CHANGELOG.md documents each result-affecting fix with dates, and `data_version` is stamped into the regenerated JSON
  5. Both data-version tags (`data-v1`, `data-v2`) exist, and a visitor can see the data-generation date/version in the leaderboard footer

**Plans**: TBD
**UI hint**: yes

### Phase 6: Release Packaging & Provenance

**Goal**: External reviewers can understand, trust, reproduce, and extend the platform — dataset provenance for all 50 datasets, aggregation-methodology docs, validated onboarding guides, and copy-paste reproducibility instructions
**Depends on**: Phase 5
**Requirements**: REL-03, DATA-04, DATA-05, DATA-07, EXT-01, EXT-02
**Success Criteria** (what must be TRUE):
  1. A reviewer can reproduce the leaderboard from a fresh clone using only literal copy-pasteable README commands (install → data → aggregate → serve)
  2. Each of the 50 datasets has a provenance row in DATA.md — source, citation, license, preprocessing, and a ModelScope-default download URL with alternates
  3. Anyone can download a data manifest (CSV/JSON) carrying full dataset metadata and direct links (ModelScope defaults, alternates included)
  4. The four aggregation methods (rank / MinMax / z-score / robust) are documented in one place, and the divergent dead logic in `js/data.js:recalculateComparison()` is gone, leaving a single authoritative implementation
  5. A maintainer can onboard a new model or dataset by following the documented process end-to-end through to "appears on the leaderboard" (mechanism validated, no new GPU runs required)

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Audit & Release Foundations | 1/3 | In Progress | - |
| 2. Data Contracts & Test Harness | 0/TBD | Not started | - |
| 3. Pipeline Adaptation to dnallm Dev | 0/TBD | Not started | - |
| 4. Correctness Fixes | 0/TBD | Not started | - |
| 5. CI & Verified Data Migration | 0/TBD | Not started | - |
| 6. Release Packaging & Provenance | 0/TBD | Not started | - |
