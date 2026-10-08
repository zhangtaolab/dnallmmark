# Requirements: DNALLM-Mark — Public-Release Hardening

**Defined:** 2026-10-08
**Core Value:** Every number on the public leaderboard is correct and reproducible from code that external reviewers can trust.

## v1 Requirements

Requirements for the hardening release. Each maps to roadmap phases.

### Systematic Audit

- [x] **AUDIT-01**: Severity-graded findings report covering all three subsystems (pipeline, data scripts, frontend), every finding with `file:line` evidence and a recommended fix
- [x] **AUDIT-02**: Pre-fix baseline captured — golden outputs of the current data chain plus a `data-v1` git tag — before any result-affecting fix lands, so number changes are attributable

### Release Foundations

- [x] **REL-01**: LICENSE file present (explicit code license; data licensing declared separately)
- [x] **REL-02**: Dependency manifests for the offline/data chain, version-pinned (`pandas>=2.2,<3.0`); GPU pipeline dependencies in a separate group that CI never installs
- [ ] **REL-03**: README reproducibility section — literal copy-pasteable commands from repo root (install → data → aggregate → serve)
- [ ] **REL-04**: Single-command data-regeneration chain (`make data` or equivalent) replacing the undocumented 3-step CWD-sensitive procedure
- [x] **REL-05**: Secret hygiene settled per maintainer decision (2026-10-08 discuss) — the Zenodo record-19135551 preview link + token at `README.md:116` is the intentional dataset-sharing mechanism (record-scoped, read-only) and stays as-is; a full-history secret scan confirms no OTHER secrets exist beyond this known-intentional link

### Correctness Fixes

- [ ] **FIX-01**: Every page renders without errors — `renderNavbar()` null-container crash fixed; verified on ALL pages, not just the 3 known-broken ones
- [ ] **FIX-02**: Species-as-dataset grouping bug fixed (`pipeline/dnallmmark_pipeline.py:1229`), with a failing test written first
- [ ] **FIX-03**: Submission flow repaired — `submit.html` created, orphaned `js/submit.js` wired to the current data schema, reachable from navigation
- [ ] **FIX-04**: Sink-side escaping at DOM-build sites the fixes touch (bounded to touched code, not a full security hardening pass)
- [x] **FIX-05**: All three data generators produce deterministic output (sorted directory iteration + `sort_keys` JSON writing) — prerequisite for every diff-based check

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

### Pipeline & Environment (dnallm dev)

- [ ] **PIPE-01**: Pipeline code adapted to dnallm dev branch (v0.7.1, local clone `/home/forrest/Github/DNALLM` @ `c99fa9d`) — API/config-schema deltas resolved; imports and dry-run pass
- [ ] **PIPE-02**: Local GPU pipeline environment reproducibly buildable (uv/venv on the NVIDIA GB10 aarch64 machine; dnallm installed from the local git dev clone; torch/transformers pinned per dnallm 0.7.1 bounds) with documented setup commands
- [ ] **PIPE-03**: Small end-to-end validation — at least one model×dataset fine-tune run completes against dnallm dev and produces a structurally valid `{model}_performance.json`

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
| Full benchmark re-run against dnallm dev | Extensive GPU time; adaptation validated with one model×dataset pair (PIPE-03) |
| Actually adding new models/datasets this milestone | Mechanism only (EXT-01/02); new entries require GPU runs and arrive later |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUDIT-01 | Phase 1 | Complete |
| AUDIT-02 | Phase 1 | Complete |
| REL-01 | Phase 1 | Complete |
| REL-02 | Phase 1 | Complete |
| REL-05 | Phase 1 | Complete |
| FIX-05 | Phase 1 | Complete |
| REL-04 | Phase 2 | Pending |
| TEST-01 | Phase 2 | Pending |
| TEST-02 | Phase 2 | Pending |
| TEST-03 | Phase 2 | Pending |
| TEST-06 | Phase 2 | Pending |
| PIPE-01 | Phase 3 | Pending |
| PIPE-02 | Phase 3 | Pending |
| PIPE-03 | Phase 3 | Pending |
| FIX-01 | Phase 4 | Pending |
| FIX-02 | Phase 4 | Pending |
| FIX-03 | Phase 4 | Pending |
| FIX-04 | Phase 4 | Pending |
| TEST-04 | Phase 5 | Pending |
| TEST-05 | Phase 5 | Pending |
| TEST-07 | Phase 5 | Pending |
| DATA-01 | Phase 5 | Pending |
| DATA-02 | Phase 5 | Pending |
| DATA-03 | Phase 5 | Pending |
| DATA-06 | Phase 5 | Pending |
| REL-03 | Phase 6 | Pending |
| DATA-04 | Phase 6 | Pending |
| DATA-05 | Phase 6 | Pending |
| DATA-07 | Phase 6 | Pending |
| EXT-01 | Phase 6 | Pending |
| EXT-02 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 31 total (30 defined + REL-05 added at roadmap creation)
- Mapped to phases: 31
- Unmapped: 0 ✓

**Phase mapping notes:**
- FIX-02 (species fix) maps to Phase 4, but its failing test is scaffolded in Phase 2 per the dependency ordering — test before fix
- PIPE-01..03 (dnallm dev adaptation) form Phase 3: Phase 2's model_performance schema defines PIPE-03's "structurally valid", and the Phase 4 species fix lands in the already-adapted pipeline so `dnallmmark_pipeline.py` is not touched twice
- DATA-03 maps to Phase 5 where `data-v2` completes the pair; the pre-fix `data-v1` tag is created in Phase 1 under AUDIT-02
- DATA-07 (methodology docs + dead-logic removal) is kept whole in Phase 6; the dead `recalculateComparison()` is uncalled and affects no number
- TEST-06 schemas/contract tests are created in Phase 2 (before fixes move numbers); CI enforcement activates when Phase 5 lands CI

---
*Requirements defined: 2026-10-08*
*Last updated: 2026-10-08 after roadmap creation (REL-05 added for token revocation; traceability filled — 31/31 mapped; PIPE-01..03 mapped to Phase 3)*
