# Roadmap: DNALLM-Mark

## Overview

This is a hardening milestone over an existing, working platform — not a build. A verification layer is wrapped around the three subsystems (GPU pipeline, offline data chain, static leaderboard site) in the one order that keeps every leaderboard number attributable: audit the codebase and freeze the pre-fix baseline; lock the data contract with schemas and a CPU-only test harness; adapt the GPU pipeline to the dnallm dev branch and prove the adaptation with a real run; land the known correctness fixes surgically under test evidence; recompute the leaderboard under full CI protection with a changelogged, tagged number migration; and finish with the provenance, methodology, and onboarding documentation external reviewers need to trust and extend the platform. Done right, the public leaderboard carries numbers that are correct, reproducible, and defensible under external scrutiny.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Audit & Release Foundations** - Findings report over all three subsystems, pre-fix baseline frozen (`data-v1`), LICENSE + pinned manifests, deterministic generators, secret-hygiene decision applied (intentional Zenodo preview link kept; scan confirms no other secrets) (completed 2026-10-09)
- [x] **Phase 2: Data Contracts & Test Harness** - Four JSON Schemas, CPU-only unit/golden/determinism tests over the data chain, and a single-command Makefile — locked before any number moves (completed 2026-10-09)
- [x] **Phase 3: Dev-Branch Reconciliation & P0 Revision Blockers** - dev@c6b3137 (run_finetune.py rewrite) merged with Phase 1/2 assets intact; dev splits (F1), seed-isolated sweep (F2/G1), old-pipeline retirement (F10); GPU env + two-model E2E on the new pipeline (completed 2026-10-10)
- [x] **Phase 4: Correctness & Methodology Core** - Species fix via dataset-side metadata (F3②), unified exporter with metric-key mapping + run_record (F3), IN-03 lands; every page renders, submission restored, escaping at touched sites (completed 2026-10-10)
- [x] **Phase 5: CI & Three-Seed Full Re-Run (E2')** - Aggregation upgrade first (F6: tie/CI-overlap, difficulty normalization, permutation tests), CI golden tests (F9), N audit + eval subsets (F7), then E2' 3-seed full re-run with changelogged tagged migration (completed 2026-10-10)
- [ ] **Phase 6: Revision Packaging & Extended Lanes** - Provenance table + reproducibility docs + snapshot/Zenodo SI (F3); revision-window permitting: LoRA/IA³/probes (F4), zero-shot VEP (F5), learning curves (F8); remainder to response-letter future work

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

**Plans**: 3/3 plans complete
Plans:
**Wave 1**
- [x] 01-01-PLAN.md — Freeze data-v1 baseline (comparator + SHA256 manifest + tag) and pin the data-chain environment (pyproject/uv.lock/requirements + pin validation)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 01-02-PLAN.md — Three-subsystem systematic audit with parallel review agents and verified, severity-graded findings published as AUDIT.md

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 01-03-PLAN.md — FIX-05 deterministic generators + one-time attributed data migration, LICENSE + data terms, gitleaks full-history scan with narrow allowlist

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

**Plans**: 3/3 plans complete planned
Plans:
**Wave 1**
- [x] 02-01-PLAN.md — Four fully-strict JSON Schemas + 94-file schema validation suite + dev group/Makefile entry points (make data/test/test-fast/lint) + D-08 micro-fixes; make data proven zero-diff (REL-04, TEST-06, TEST-02)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 02-02-PLAN.md — Synthetic fixture tree (tie/missing-metric/regression/species-group edges) + aggregation/pivot unit tests + golden files via compare.walk + node:test JS suite; make test runs Python+JS (TEST-01, TEST-02, TEST-03)
- [x] 02-03-PLAN.md — Real-tree determinism regression (chain ×2 byte-identical + regeneration == committed, slow-marked) + xfail(strict=True) locks for AUD-01-P0/WR-02/WR-03; full make test green (TEST-03, TEST-02)

### Phase 3: Dev-Branch Reconciliation & P0 Revision Blockers

**Goal**: The dev-branch pipeline rewrite (run_finetune.py @ dev c6b3137) is reconciled with the audited main lineage — Phase 1/2 contracts and tests survive the merge — and the manuscript-revision P0 blockers (dev splits, seed-isolated sweep, old-pipeline retirement) land, proven by a two-model end-to-end run on the new pipeline
**Depends on**: Phase 2
**Requirements**: PIPE-02, PIPE-03, REV-01, REV-02, REV-10
**Success Criteria** (what must be TRUE):
  1. dev@c6b3137 is merged into the audited lineage (or the audited lineage rebased onto it) with zero loss of Phase 1/2 assets: all four schemas, the full test suite, the Makefile, and the data-v1 baseline discipline survive; `make test` is green on the merged tree
  2. The Phase 2 species xfail lock's AST anchor is migrated to the new pipeline/export chain (or the lock re-anchored with the same strict semantics), and the anchor companion still guards findability+uniqueness+species-key
  3. `pipeline/dnallmmark_pipeline.py` carries a deprecation header pointing to `run_finetune.py` (REV-10/F10); README names run_finetune.py as the benchmark entry point
  4. All 47 tasks have train/dev/test splits (REV-01/F1): the 18 Dev-empty tasks get stratified 10% dev splits (seed=42, reproducible), datasets_info Dev columns updated, and checkpoint selection refuses to silently fall back to test
  5. Multi-seed execution is real (REV-02/F2, fixes G1): output dirs are seed-isolated (`{model}/{task}/seed_{seed}/`), resume never skips a different seed, and a sweep runner drives model×task×seed matrices with per-run records and a failure manifest
  6. [DEFERRED 2026-10-09 — no model runs until the DNALLM suite stabilizes] The GPU pipeline environment is reproducibly buildable (PIPE-02): dedicated uv venv on the GB10 machine, dnallm@0.7.1 from the local clone, torch/transformers pinned to the verified combination (2.11.0+cu130 / 5.17.0), locked in pyproject `[gpu]` group + uv.lock, documented rebuild commands. THIS PHASE lands only the pyproject `[gpu]` group definition as code (no install)
  7. [DEFERRED 2026-10-09 — with PIPE-02, until model runs resume] Two end-to-end runs complete on the new pipeline (PIPE-03): plant-dnamamba-6mer and PlantHelixSeek each fine-tune on PlantCAD2__cross_species_leaf_on_off_translation and produce `{model}_performance.json` validating against the Phase 2 schema. THIS PHASE lands PlantHelixSeek's models_info entry as metadata only (AUD-05 groundwork)

**Plans**: 4/4 plans complete planned
Plans:
**Wave 1**
- [x] 03-01-PLAN.md — D-01 merge of origin/dev@c6b3137 (51 data conflicts to HEAD, 6 dev-added data files removed) + F10 old-pipeline deprecation/README entry-point rename + D-03 species-lock pivot to the export-chain contract + D-04 frontend diff review of commit 8d99daf (REV-10)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 03-02-PLAN.md — D-10 registry unification to single-source JSON (convert_registry.py ingest + tested extensions, run_finetune.py json read site, both .txt registries retired, D-03 Category retarget, single-source contract test) + F1 dev splits: make_dev_splits.py carving the 18 Dev-empty tasks, unified registry updated, run_finetune.py refusal guard + source-contract tests (REV-01)

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 03-03-PLAN.md — [pipeline]→[gpu] pyproject group (torch==2.11.0 cu130, transformers==5.17.0, definition only per D-05) + ty toolchain wiring + make typecheck + PlantHelixSeek card fill in the unified 62-entry registry from the D-09 ModelScope card (PIPE-02, PIPE-03)

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 03-04-PLAN.md — F2/G1 seed-isolated output dirs + D-11 per-model base-config reload (cross-model head-config leak) + D-07 grad_accum per-dataset reset in run_finetune.py + pipeline/run_sweep.py matrix driver over the unified json registries (--dry-run, run_record/failure/manifest, suite-native metric keys) + D-08 ruff findings fixed fresh + widened make lint (REV-02)

**Decisions carried from the 2026-10-09 discussion**: dedicated new uv venv (not DNALLM/.venv reuse); pyproject `[gpu]` dependency-group + uv.lock as the lock carrier; E2E pair = the two maintainer-named models × PlantCAD2__on_off; on-disk datasets are double-nested from unzip and get normalized during setup.

### Phase 4: Correctness & Methodology Core

**Goal**: Every confirmed correctness bug is fixed surgically with test evidence — species grouping via dataset-side metadata, a unified exporter with an explicit metric-key mapping, key-name parity tested — and every page works
**Depends on**: Phase 3
**Requirements**: FIX-01, FIX-02, FIX-03, FIX-04, REV-03
**Success Criteria** (what must be TRUE):
  1. Dataset species comes from a human-verified dataset metadata table (REV-03/F3②), never from the model card; the Phase 2 species xfail lock turns green in the same commit as the fix, and the aggregation diff shows only changes the fix explains
  2. The unified exporter (REV-03/F3①) replaces get_task_performance.py's input side: it reads per-run records, applies an explicit suite-registry↔export-key mapping layer with key-parity unit tests, and emits per-seed detail plus aggregated (mean±SD, bootstrap 95% CI) tables; IN-03 (METRIC_KEY_MAP mirror) is resolved here
  3. A visitor can load every page (main leaderboard, task benchmark, finetuning, models, datasets) with no console errors, working navigation, and fully rendered content — verified on ALL pages
  4. A user can complete the submission flow: submit.html reachable, client-side validation working, PR instructions correct against the current data schema
  5. DOM-build sites touched by these fixes escape rendered content, so a hostile string in any performance JSON displays as inert text
  6. Phase 2 schemas/tests are updated for the new export shape (any new metric keys join the closed enum WITH the data≡enum self-check updated in the same commit)

**Plans**: 5/5 plans complete planned
**UI hint**: yes
Plans:
**Wave 1**
- [x] 04-01-PLAN.md — TRACER: species fix end-to-end — maintainer Category-review gate → summarize Comparison-join grouping (hard-fail, Multiple→majority) → regeneration + previewed diff inventory (2 byte-identical / 2 swapped membership 42/42, counts 22/13) → AUD-01 lock unmark three-in-one; WR-03 get_float isfinite + WR-02 bool/int + IN-01 INT label with same-commit unmarks (D-13) (FIX-02, REV-03)
- [x] 04-03-PLAN.md — Frontend restoration — shared escaped navbar on all 6 shells (AUD-09 + the 2 nav-less pages), AUD-10 nesting ×4, AUD-11 sort state + AUD-12 delegation (D-14), AUD-20 dropdown, submit.html + schema-current submit.js (FIX-03), bounded escapeHTML (FIX-04), LIVE Playwright zero-console-error pass per page (FIX-01, FIX-03, FIX-04)
- [x] 04-04-PLAN.md — Carryovers — 4 quirk-parity ports in run_finetune.py (ACGT alphabet, limited-length wiring, safetensors union, length-tier rounding) with rename-map parity tests; 17 card fills → 62/62 complete cards (REV-03)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 04-02-PLAN.md — Unified exporter core — scipy behind a blocking-human legitimacy gate, vendored aggregate_seeds @483a35c with parity tests, exporter-owned 28-name metric-key mapping (key-parity both directions), run-record reader + registry joins, D-12 parametersBlock config-YAML join, dual output (schema-valid task_performance-compatible + per-seed stats artifact), freeze_snapshot tested + unwired (REV-03)

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 04-05-PLAN.md — Chain retirement + IN-03 + hygiene — get_task_performance.py deleted with pivot assertions folded into exporter tests, golden/determinism re-scoped (task files become committed inputs), OQ4 2-file species correction + tasks.json inventory, summarize's metric-key mirror deleted (exporter table imported, legacy alias surface owned), IN-08 lint scope + README exporter sentence (REV-03, FIX-02)

### Phase 5: CI & Three-Seed Full Re-Run (E2')

**Decisions carried (2026-10-10 pre-decision)**: E2' launch = dual gate (DNALLM stable release + PIPE-02 env smoke on GB10) with EXPLICIT maintainer authorization (agent never auto-launches); failure recovery = sweep failure-manifest driven re-run of failed cells only; window degradation = priority order (E2E pair all-seeds first, then arena representatives, then the rest as window allows) with honest n_seeds disclosure (suite statistics contract; n<3 → ci95=null/t-interval), never silent omission; E2' scope = ALL 62 unified-registry models (the 18 without prior results are first-time runs, comparability noted in the response letter). Small/medium grey areas (CI smoke shape, aggregation statistics details, N-audit subset rule, data-v2 migration gate) deferred to this phase's discuss.

**Goal**: Aggregation methodology is upgraded BEFORE numbers publish (tie rules, difficulty normalization, permutation tests), CI proves repo health end-to-end, and the leaderboard is recomputed under three seeds with an attributable, changelogged, tagged migration
**Depends on**: Phase 4
**Requirements**: TEST-04, TEST-05, TEST-07, DATA-01, DATA-02, DATA-03, DATA-06, REV-04, REV-06, REV-07, REV-09
**Success Criteria** (what must be TRUE):
  1. Aggregation upgrade (REV-06/F6) lands before E2' numbers are published: within-task 95% CI overlap ⇒ tied rank; raw-rank and z-score×difficulty-weighted dual views; permutation tests (10,000 shuffles, BH-corrected) reported; the CpG top-10 case (span 0.0021, distinct ranks) renders as a tie under the new rule
  2. CI golden tests (REV-09/F9): smoke run (tiny model × 1k samples × 1 epoch incl. export), metric-key parity, species-table spot checks, aggregation unit tests — CPU runner, <15 min, PR-required, badge in README (subsumes TEST-04/05: lint + matrix + frontend checks + drift detection)
  3. N-frequency audit + unified eval subsets (REV-07/F7): 47 tasks × train/dev/test N/non-ACGT tables published; eval-subset ID lists accepted by the pipeline; all models evaluate identical sample counts per task
  4. E2' three-seed full re-run executes via the sweep runner only after F1/F2 gates (critical path note); DATA-01/02/03/06 land: recomputed leaderboard, before/after artifact, CHANGELOG with dates, data_version stamped, both data tags (data-v1, data-v2) exist, footer shows the generation date/version

**Plans**: 4/4 plans complete planned
**UI hint**: yes
Plans:
**Wave 1**
- [x] 05-01-PLAN.md — CI golden harness: canned replay fixture + pinned `ci` marker lane + SHA-pinned workflow (lint/typecheck/test matrix/JS static checks/drift, 14-min budget) + eslint/html-validate configs + README badge, package-legitimacy blocking checkpoint (REV-06, TEST-04, TEST-05, TEST-07)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 05-02-PLAN.md — F6 aggregation upgrade as ONE migration commit: vendored-stats tie rule + weighted dual view + permutation tests (10k/BH, 861-pair family) + schema extensions + regenerated comparisons + re-chained goldens + migration inventory + CHANGELOG/manifest (data_version 1.1.0) + weighted-default frontend view toggle + stamped footer (REV-04, DATA-01, DATA-02, DATA-06)

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 05-03-PLAN.md — N-frequency audit: 50-task census (43 present / 7 GUE missing-with-warning) published as DATA.md appendix + CSV/JSON artifacts + unified eval-subset ID lists + run_finetune --subset_file fail-fast test-split seam (REV-07)

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 05-04-PLAN.md — E2' readiness (code only): D-16 bridge (export_runs emits BOTH views; full-chain CI replay), D-18 alias normalization (plant-dnamamba2-BPE → PlantDNAMamba2-BPE, inventoried), sweep priority tiers + --from-failures re-run, never-executed env_smoke gate, tier-2 maintainer curation checkpoint, data-v2 gate tooling rehearsal (REV-09, DATA-01, DATA-03)

### Phase 6: Revision Packaging & Extended Lanes

**Decisions carried (2026-10-10 pre-decision)**: Extended-lane priority = LoRA → zero-shot VEP → frozen probes → learning curves → IA3 (suite-support-gated last); lanes open only after E2' core completes, each independently cuttable (completed lanes reported, incomplete → response-letter future work with reasons); cost-accuracy frontier table built from whatever completed. Post-milestone deliverable (maintainer directive 2026-10-10): a gitignored reviewer-response report generated from code at milestone close, answering F1-F10/G1-G7 point-by-point — never committed to the repo.

**Goal**: External reviewers can understand, trust, reproduce, and extend the platform — provenance, methodology docs, validated onboarding, result snapshots for SI/Zenodo — with the revision-window extension lanes (PEFT, zero-shot VEP, learning curves) delivered as far as the window allows and the remainder explicitly deferred to the response letter
**Depends on**: Phase 5
**Requirements**: REL-03, DATA-04, DATA-05, DATA-07, EXT-01, EXT-02, REV-03, REV-05, REV-08
**Success Criteria** (what must be TRUE):
  1. A reviewer can reproduce the leaderboard from a fresh clone using only literal copy-pasteable README commands (install → data → aggregate → serve)
  2. Each dataset has a provenance row in DATA.md — source, citation, license, preprocessing, ModelScope-default download URL with alternates; a downloadable manifest (CSV/JSON) carries full metadata and direct links
  3. A results snapshot (REV-03: tar + SHA-256 manifest + frozen commit hash) supports SI/Zenodo deposition and can be re-verified from its manifest
  4. The four aggregation methods (plus the F6 dual views) are documented in one place; the divergent dead logic in js/data.js:recalculateComparison() is gone
  5. A maintainer can onboard a new model or dataset end-to-end by following the documented process (mechanism validated, no new GPU runs required)
  6. Revision-window lanes, in priority order: LoRA/IA³/frozen probes (REV-05/F4) with a cost-accuracy frontier table; zero-shot VEP lane (REV-08/F5) with CLM/MLM scoring and sanity checks; learning curves (part of REV-08's P2 tail) — whatever does not fit lands in the response letter as future work with the mechanism documented
  7. The intentional Zenodo preview-token link in README.md is replaced with the published record DOI/URL once record 19135551 is public, with the .gitleaks.toml allowlist rule updated in the same commit (WR-01 follow-up)

**Plans**: 2/5 plans executed planned
Plans:
**Wave 1**
- [x] 06-01-PLAN.md — dnallm 1.2.1 adaptation verification (gating): quirk re-verification vs tag v1.2.1 + citation refresh, --peft tracer wiring (flag + lora:/ia3: YAML + use_lora ctor kwarg + use_ia3), env_smoke peft check + 1.2.1 relabel + smoke-sanction docstring amendment, seed_result.json tolerant reader, and the sanctioned GB10 install + env_smoke EXECUTION + peft_dry_run smoke (REV-05, REV-08)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 06-02-PLAN.md — PEFT lane: adapter-run aliases (+lora/+ia3) + trainable_params_pct persistence + run_sweep --peft threading + cost-accuracy frontier machinery (schema + synthetic fixtures committed; data artifact gated on real post-E2' numbers) + bounded 1-epoch smoke (REV-05)
- [ ] 06-03-PLAN.md — zero-shot VEP registry driver over the suite kernels (paradigm filtering MLM 32 / CLM 18, DL 5 + EMPTY 7 excluded-with-reason, synonym/nonsense + RC sanity checks, dual CSV+JSON + schema + fixtures, bounded two-model GB10 smoke) (REV-08)
- [ ] 06-04-PLAN.md — packaging: recalculateComparison dead-code removal as the FIRST dedicated commit, provenance columns + convert_registry round-trip + build_provenance + dual artifact + DATA.md appendix + maintainer-review checkpoint, freeze_snapshot wiring (manifest-derived hash, .sha256 committed / .tar gitignored under baseline/snapshots/), docs/METHODOLOGY.md + docs/ONBOARDING.md + README literal reproduction section, doi_swap.py prepared not executed (REL-03, DATA-04, DATA-05, DATA-07, EXT-01, EXT-02, REV-03)

**Wave 3** *(blocked on 06-02 completion — 06-05 shares the run_finetune/run_sweep surfaces with 06-02)*
- [ ] 06-05-PLAN.md — frozen probes (--config-variant mechanism + finetune_config_probe.yaml with head_config.frozen + special-loader scope guard + frozen-backbone 1-epoch smoke) + learning curves (--train_fraction + run_sweep --curve with frac-under-seed nesting + tightened curve YAML + extract_curve_points reader) (REV-05, REV-08)

**Revision-work-package map**: F1→E1'-1 · F2→E1'+E2' prerequisite · F3→E1'-2/3+Ed-5 · F4→E3' · F5→E5 · F6→E8 · F7→E1'-⑤/E7 · F8→E6' (P2) · F9→E10 · F10→E1'-4. **Critical path: F1 → F2 (G1) → E2' full re-run; E2' must NOT start before F2 is done (seeds would overwrite each other).**

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Audit & Release Foundations | 3/3 | Complete    | 2026-10-09 |
| 2. Data Contracts & Test Harness | 3/3 | Complete    | 2026-10-09 |
| 3. Pipeline Adaptation to dnallm Dev | 4/4 | Complete    | 2026-10-10 |
| 4. Correctness Fixes | 5/5 | Complete    | 2026-10-10 |
| 5. CI & Verified Data Migration | 4/4 | Complete    | 2026-10-10 |
| 6. Release Packaging & Provenance | 2/5 | In Progress | - |
