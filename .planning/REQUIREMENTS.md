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
- [x] **REL-04**: Single-command data-regeneration chain (`make data` or equivalent) replacing the undocumented 3-step CWD-sensitive procedure
- [x] **REL-05**: Secret hygiene settled per maintainer decision (2026-10-08 discuss) — the Zenodo record-19135551 preview link + token at `README.md:116` is the intentional dataset-sharing mechanism (record-scoped, read-only) and stays as-is; a full-history secret scan confirms no OTHER secrets exist beyond this known-intentional link

### Correctness Fixes

- [x] **FIX-01**: Every page renders without errors — `renderNavbar()` null-container crash fixed; verified on ALL pages, not just the 3 known-broken ones
- [x] **FIX-02**: Species-as-dataset grouping bug fixed (`pipeline/dnallmmark_pipeline.py:1229`), with a failing test written first
- [x] **FIX-03**: Submission flow repaired — `submit.html` created, orphaned `js/submit.js` wired to the current data schema, reachable from navigation
- [x] **FIX-04**: Sink-side escaping at DOM-build sites the fixes touch (bounded to touched code, not a full security hardening pass)
- [x] **FIX-05**: All three data generators produce deterministic output (sorted directory iteration + `sort_keys` JSON writing) — prerequisite for every diff-based check

### Test Infrastructure

- [x] **TEST-01**: Unit tests for the data-script pure functions (rank/MinMax/z-score/robust aggregation, pivot logic) using synthetic fixtures, CPU-only
- [x] **TEST-02**: Float-tolerance policy and thread pinning fixed at scaffold time (`pytest.approx` tolerances; `OMP/OPENBLAS/MKL_NUM_THREADS=1` in conftest)
- [x] **TEST-03**: Golden-file tests over synthetic fixture trees plus a determinism regression test
- [x] **TEST-04**: GitHub Actions CI (lint + test matrix on Python 3.12/3.13 plus a Node job; actions SHA-pinned) with README badge
- [x] **TEST-05**: Frontend static checks in CI (ESLint flat config + html-validate + `node --check`)
- [x] **TEST-06**: JSON Schema contract validation — 4 schemas (model_performance, task_performance, models_comparison, tasks_index) enforced over every committed JSON in CI
- [x] **TEST-07**: CI drift-detection job — regenerate derived data and `git diff --exit-code`, making stale derived files a build failure

### Data & Records

- [x] **DATA-01**: Leaderboard data recomputed after correctness fixes, with a before/after comparison artifact *(complete — co-declared by 05-02 and 05-04; with 05-04's SUMMARY present both declarers are done: 05-02's F6 migration and 05-04's D-18 alias migration each carry a full baseline inventory attributing every before/after diff)*
- [x] **DATA-02**: CHANGELOG.md records each result-affecting fix with date, per lm-evaluation-harness convention; `data_version` stamped into regenerated JSON
- [x] **DATA-03**: Git tags for data versions (pre-fix `data-v1`, post-fix `data-v2`) *(complete as PREPARATION — `data-v1` tagged (Phase 1); the data-v2 gate tooling (run_migration_inventory.py + --write-manifest SHA256 convention) is rehearsed on the D-18 mini-migration; the `data-v2` tag itself is created ONLY by the maintainer after E2' sign-off, never by an agent)*
- [ ] **DATA-04**: Provenance table for all 50 datasets (DATA.md: source, citation, license, preprocessing, download URL) — download URLs default to ModelScope, other sources as alternates
- [ ] **DATA-05**: Downloadable data manifest file (CSV/JSON) with full dataset metadata and direct links — ModelScope links by default, alternates included
- [x] **DATA-06**: Leaderboard page footer shows data-generation date/version stamp
- [ ] **DATA-07**: Aggregation-methodology documentation (rank vs MinMax vs z-score vs robust) and removal of the divergent dead logic in `js/data.js:recalculateComparison()`

### Extensibility Mechanisms

- [ ] **EXT-01**: New-model onboarding process documented and validated end-to-end (register in `models_info.json` → pipeline quirks → run → copy performance JSON → regenerate → appears on leaderboard)
- [ ] **EXT-02**: New-dataset onboarding process documented and validated end-to-end (register in `datasets_info.json` → metric mapping → run → regenerate)

### Pipeline & Environment (dnallm dev)

- [x] **PIPE-01**: ~~Pipeline code adapted to dnallm dev branch~~ — **absorbed by the dev-branch rewrite** (`pipeline/run_finetune.py` @ dev `c6b3137`, 2026-10-09): the rewritten pipeline already targets dnallm dev; remaining adaptation work (branch reconciliation, Phase 2 asset survival, anchor migration) lives in REV-01..REV-10 and Phase 3's success criteria
- [x] **PIPE-02**: Local GPU pipeline environment reproducibly buildable (uv/venv on the NVIDIA GB10 aarch64 machine; dnallm installed from the local git dev clone; torch/transformers pinned per dnallm 0.7.1 bounds) with documented setup commands

**Revision requirements (F1–F10, per the 2026-10-09 code-review & feature plan against dev@c6b3137; F-numbers are the canonical reference)**:
- [x] **REV-01** (F1, P0): Dev-split generation for the 18 Dev-empty tasks (stratified 10% from train, seed=42, datasets_info Dev columns updated) + checkpoint selection refuses silent test fallback
- [x] **REV-02** (F2, P0): Multi-seed sweep — seed-isolated output dirs fixing G1 (resume never skips a different seed), sweep runner (model×task×seed) with per-run records and failure manifest; VRAM-probe state semantics documented per seed
- [x] **REV-03** (F3, P0): Unified exporter + result snapshot — metric-key mapping layer (suite registry ↔ export keys, key-parity unit-tested), dataset species from a human-verified metadata table (never model cards), per-seed detail + mean±SD/bootstrap-CI aggregates; freeze_snapshot (tar + SHA-256 + frozen commit hash)
- [x] **REV-04** (F6, P1): Aggregation upgrade — CI-overlap tie rules, raw-rank + z-score×difficulty-weight dual views, permutation tests (10k, BH-corrected); CpG case renders as tie
- [ ] **REV-05** (F4, P1): Adaptation lanes — LoRA (suite built-in, CLI-exposed), IA³ (after suite-side support), frozen probes (embedding cache + logistic/MLP); cost-accuracy frontier table
- [x] **REV-06** (F9, P1): CI golden tests — smoke (tiny model × 1k × 1 epoch incl. export), key parity, species spot checks, aggregation units; CPU, <15 min, PR-required
- [x] **REV-07** (F7, P1): N-frequency audit (47 tasks × splits) + unified eval-subset ID lists accepted by the pipeline
- [ ] **REV-08** (F5+F8, P1/P2): Zero-shot VEP lane (CLM/MLM scoring, ClinVar/AraGWAS, baselines + sanity checks) and, window permitting, from-scratch baselines + learning curves (label-fraction sweeps)
- [x] **REV-09** (E2' 执行面, P0 依赖): Three-seed full re-run (E2') executes only after REV-01/REV-02 gates — critical path F1→F2→E2'
- [x] **REV-10** (F10, P0): Old pipeline (`dnallmmark_pipeline.py`) deprecation header + README names `run_finetune.py` as the benchmark entry point
- [x] **PIPE-03**: Small end-to-end validation on the NEW pipeline (`run_finetune.py`) — plant-dnamamba-6mer and PlantHelixSeek (models_info entry added in-phase) each fine-tune on PlantCAD2__cross_species_leaf_on_off_translation and produce a `{model}_performance.json` valid against the Phase 2 schema

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
| REL-04 | Phase 2 | Complete |
| TEST-01 | Phase 2 | Complete |
| TEST-02 | Phase 2 | Complete |
| TEST-03 | Phase 2 | Complete |
| TEST-06 | Phase 2 | Complete |
| PIPE-01 | — (absorbed by dev rewrite) | Absorbed |
| PIPE-02 | Phase 3 | Complete |
| PIPE-03 | Phase 3 | Complete |
| REV-01 | Phase 3 | Complete |
| REV-02 | Phase 3 | Complete |
| REV-03 | Phase 4, Phase 6 | Complete |
| REV-04 | Phase 5 | Complete |
| REV-05 | Phase 6 | Pending |
| REV-06 | Phase 5 | Complete |
| REV-07 | Phase 5 | Complete |
| REV-08 | Phase 6 | Pending |
| REV-09 | Phase 5 | Complete |
| REV-10 | Phase 3 | Complete |
| FIX-01 | Phase 4 | Complete |
| FIX-02 | Phase 4 | Complete |
| FIX-03 | Phase 4 | Complete |
| FIX-04 | Phase 4 | Complete |
| TEST-04 | Phase 5 | Complete |
| TEST-05 | Phase 5 | Complete |
| TEST-07 | Phase 5 | Complete |
| DATA-01 | Phase 5 | Complete |
| DATA-02 | Phase 5 | Complete |
| DATA-03 | Phase 5 | Complete |
| DATA-06 | Phase 5 | Complete |
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
- PIPE-01 absorbed by the dev-branch rewrite (run_finetune.py @ dev c6b3137); PIPE-02/03 + REV-01/02/10 form Phase 3 (reconciliation + P0 blockers). Phase 2's model_performance schema defines PIPE-03 validity. REV-03's dataset-side species table is the AUD-01-P0 fix vehicle in Phase 4. Revision critical path: REV-01 → REV-02 → E2' (REV-09); E2' must not start before REV-02 (seed overwrite)
- DATA-03 maps to Phase 5 where `data-v2` completes the pair; the pre-fix `data-v1` tag is created in Phase 1 under AUDIT-02
- DATA-07 (methodology docs + dead-logic removal) is kept whole in Phase 6; the dead `recalculateComparison()` is uncalled and affects no number
- TEST-06 schemas/contract tests are created in Phase 2 (before fixes move numbers); CI enforcement activates when Phase 5 lands CI

---
*Requirements defined: 2026-10-08*
*Last updated: 2026-10-09 after revision-plan integration (REV-01..10 added from the F1-F10 manuscript-revision plan; PIPE-01 absorbed by dev rewrite; phases 3-6 restructured; critical path F1→F2→E2' recorded)*
