# Requirements: DNALLM-Mark — Public-Release Hardening

**Defined:** 2026-10-08
**Core Value:** Every number on the public leaderboard is correct and reproducible from code that external reviewers can trust.

## v1 Requirements

Requirements for the hardening release. Each maps to roadmap phases.

### Systematic Audit

- [ ] **AUDIT-01**: Severity-graded findings report covering all three subsystems (pipeline, data scripts, frontend), every finding with `file:line` evidence and a recommended fix
- [ ] **AUDIT-02**: Pre-fix baseline captured — golden outputs of the current data chain plus a `data-v1` git tag — before any result-affecting fix lands, so number changes are attributable

### Release Foundations

- [ ] **REL-01**: LICENSE file present (explicit code license; data licensing declared separately)
- [ ] **REL-02**: Dependency manifests for the offline/data chain, version-pinned (`pandas>=2.2,<3.0`); GPU pipeline dependencies in a separate group that CI never installs
- [ ] **REL-03**: README reproducibility section — literal copy-pasteable commands from repo root (install → data → aggregate → serve)
- [ ] **REL-04**: Single-command data-regeneration chain (`make data` or equivalent) replacing the undocumented 3-step CWD-sensitive procedure

### Correctness Fixes

- [ ] **FIX-01**: Every page renders without errors — `renderNavbar()` null-container crash fixed; verified on ALL pages, not just the 3 known-broken ones
- [ ] **FIX-02**: Species-as-dataset grouping bug fixed (`pipeline/dnallmmark_pipeline.py:1229`), with a failing test written first
- [ ] **FIX-03**: Submission flow repaired — `submit.html` created, orphaned `js/submit.js` wired to the current data schema, reachable from navigation
- [ ] **FIX-04**: Sink-side escaping at DOM-build sites the fixes touch (bounded to touched code, not a full security hardening pass)
- [ ] **FIX-05**: All three data generators produce deterministic output (sorted directory iteration + `sort_keys` JSON writing) — prerequisite for every diff-based check

### Test Infrastructure

- [ ] **TEST-01**: Unit tests for the data-script pure functions (rank/MinMax/z-score/robust aggregation, pivot logic) using synthetic fixtures, CPU-only
- [ ] **TEST-02**: Float-tolerance policy and thread pinning fixed at scaffold time (`pytest.approx` tolerances; `OMP/OPENBLAS/MKL_NUM_THREADS=1` in conftest)
- [ ] **TEST-03**: Golden-file tests over synthetic fixture trees plus a determinism regression test
- [ ] **TEST-04**: GitHub Actions CI (lint + test matrix on Python 3.12/3.13 plus a Node job; actions SHA-pinned) with README badge
- [ ] **TEST-05**: Frontend static checks in CI (ESLint flat config + html-validate + `node --check`)
- [ ] **TEST-06**: JSON Schema contract validation — 4 schemas (model_performance, task_performance, models_comparison, tasks_index) enforced over every committed JSON in CI
- [ ] **TEST-07**: CI drift-detection job — regenerate derived data and `git diff --exit-code`, making stale derived files a build failure

### Data & Records

- [ ] **DATA-01**: Leaderboard data recomputed after correctness fixes, with a before/after comparison artifact
- [ ] **DATA-02**: CHANGELOG.md records each result-affecting fix with date, per lm-evaluation-harness convention; `data_version` stamped into regenerated JSON
- [ ] **DATA-03**: Git tags for data versions (pre-fix `data-v1`, post-fix `data-v2`)
- [ ] **DATA-04**: Provenance table for all 50 datasets (DATA.md: source, citation, license, preprocessing, download URL) — download URLs default to ModelScope, other sources as alternates
- [ ] **DATA-05**: Downloadable data manifest file (CSV/JSON) with full dataset metadata and direct links — ModelScope links by default, alternates included
- [ ] **DATA-06**: Leaderboard page footer shows data-generation date/version stamp
- [ ] **DATA-07**: Aggregation-methodology documentation (rank vs MinMax vs z-score vs robust) and removal of the divergent dead logic in `js/data.js:recalculateComparison()`

### Extensibility Mechanisms

- [ ] **EXT-01**: New-model onboarding process documented and validated end-to-end (register in `models_info.json` → pipeline quirks → run → copy performance JSON → regenerate → appears on leaderboard)
- [ ] **EXT-02**: New-dataset onboarding process documented and validated end-to-end (register in `datasets_info.json` → metric mapping → run → regenerate)

## v2 Requirements

Deferred to post-release. Tracked, not in current roadmap.

### Citation & Archival

- **CITE-01**: BibTeX citation block in README
- **CITE-02**: CITATION.cff and Zenodo DOI on first tagged release

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Deep security hardening (CSP, SRI on CDN scripts) | Descoped by prioritization; only token revocation is release-blocking |
| Frontend E2E tests (Playwright) | Regression prevention scoped to data scripts + CI by decision |
| Automated evaluation/submission server | Violates static-site constraint; unbounded GPU cost and maintenance |
| Maintainer re-run verification of submitted results | Unbounded GPU cost per submission |
| Git history rewrite to purge leaked token | Post-revocation it protects nothing; breaks SHAs/forks |
| Full Datasheets for all 50 datasets | Weeks of work on murky licenses; provenance table suffices |
| Framework migration / bundler / pipeline rewrite | Hard constraint: vanilla no-build MPA; surgical fixes only |
| Actually adding new models/datasets this milestone | Mechanism only (EXT-01/02); new entries require GPU runs and arrive later |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| (to be filled by roadmap) | | |

**Coverage:**
- v1 requirements: 27 total
- Mapped to phases: 0
- Unmapped: 27 ⚠️ (roadmap pending)

---
*Requirements defined: 2026-10-08*
*Last updated: 2026-10-08 after initial definition (ModelScope-default download links applied per user adjustment)*
