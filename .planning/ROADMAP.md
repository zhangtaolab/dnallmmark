# Roadmap: DNALLM-Mark

## Milestones

- ✅ **v0.7.1 Release Hardening** - Phases 1-6 (shipped 2026-10-11)
- 🚧 **v1.2 TUI任务** - Phases 7-12 (in progress)

## Overview

v1.2 builds the operator-facing terminal console on top of the hardened v0.7.1 platform: a pure-Python Textual TUI that lets one operator, working over SSH on the GB10 machine, select from the 62-model × 50-dataset matrix, bring their own models and datasets in through guided wizards, close dataset gaps, configure and safely launch sweeps, and monitor/recover multi-day GPU runs — without changing any existing pipeline contract and without losing CLI parity. The journey: pipeline-side enablement first (FlopsCounter port, the four sanctioned argv flags, and the official+custom registry overlay seam — TUI-independent, feeds E2' FLOPs correctness and makes user-maintained custom entries loadable everywhere); then the TUI foundation carrying every non-retrofittable decision (startup env-check panel, k9s-style selection, textual-free services layer, test harness); then custom model/dataset onboarding — wizards writing user-owned registries over the overlay, with collect-all fool-proofing and a dry-run/audit gauntlet that never lets a failed entry land; then the data manager, so env presence FAILs are diagnosable before launch; then the complete run-config → gated launch → single-GPU monitoring loop, proven by a maintainer-authorized bounded smoke; and finally multi-GPU orchestration, hard-gated on single-GPU validation, with the read-only web mirror and snapshot goldens closing the console out.

## Phases

**Phase Numbering:**
- Integer phases (7, 8, 9): Planned milestone work — numbering continues from v0.7.1 (Phase 6); it never restarts at 1
- Decimal phases (7.1, 7.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 7: Pipeline-Side Enablement (FlopsCounter Port, argv Threading & Registry Overlay)** - The four sanctioned `run_sweep.py` flags land CLI-first with argv-parity tests; FlopsCounter (20+ architecture hooks) ports from the legacy pipeline into `run_finetune.py`; the official+custom registry overlay seam lands byte-identical-when-absent; the shared tolerant JSON loader contract is pinned
- [x] **Phase 8: TUI Foundation (Env Check & Selection)** - `make tui` opens the console with a persisted startup environment-check panel and k9s-style filter/mark-set selection over first-class model and dataset lists, with presets, templates, and presence columns — carrying all non-retrofittable architecture decisions
- [x] **Phase 9: Custom Model & Dataset Onboarding (自定义接入向导)** - Guided wizards land custom models/datasets in user-owned registries over the Phase-7 overlay — collect-all fail-fast field validation, dry-run + audit gauntlet, entry-level rollback; official registries are never written
- [x] **Phase 10: Data Manager (Downloads & Verification)** - One-click ModelScope download with a persistent resumable queue and n_audit row-count reconciliation, so missing datasets are closable in-session before launch
- [x] **Phase 11: Run Config, Launch Gates & Single-GPU Monitoring** - Full run-config surface with same-source dry-run preview, terraform-style launch gates (E2' stays maintainer-authorized), detached `run_sweep.py` execution, and the poll-and-attach monitor with failure re-run — proven by a bounded GB10 smoke
- [ ] **Phase 12: Multi-GPU Orchestration & Console Hardening** - CLI-invocable static model sharding × CUDA_VISIBLE_DEVICES with per-worker views, artifact merge, and the DDP-vs-sharding decision, plus the static read-only web mirror and maintainer-verified snapshot goldens — hard-gated on Phase 11 validation

## Phase Details

<details>
<summary>✅ v0.7.1 Release Hardening (Phases 1-6) — SHIPPED 2026-10-11</summary>

*(Full accomplishment record: `.planning/MILESTONES.md`. Per-plan execution history: git log + archived phase directories.)*

#### Phase 1: Audit & Release Foundations

**Goal**: Repo safe for public visibility and every future number change attributable — all three subsystems audited with evidence, pre-fix state frozen, reproducibility substrate in place
**Requirements**: AUDIT-01, AUDIT-02, REL-01, REL-02, REL-05, FIX-05
**Plans**: 3/3 complete (01-01 data-v1 baseline freeze + pinned data-chain env · 01-02 three-subsystem audit → AUDIT.md, 24 severity-graded findings · 01-03 deterministic generators + one-time 52-file migration + LICENSE + gitleaks full-history scan)
**Completed**: 2026-10-09

#### Phase 2: Data Contracts & Test Harness

**Goal**: Data chain guarded by executable contracts and a stable CPU-only test harness, locked before any correctness fix moves the numbers
**Requirements**: REL-04, TEST-01, TEST-02, TEST-03, TEST-06
**Plans**: 3/3 complete (02-01 four fully-strict JSON Schemas + 94-file validation + Makefile entry points · 02-02 synthetic fixture tree + aggregation/pivot unit tests + node:test lane · 02-03 real-tree determinism regression + three xfail(strict=True) defect locks)
**Completed**: 2026-10-09

#### Phase 3: Dev-Branch Reconciliation & P0 Revision Blockers

**Goal**: dev-branch run_finetune.py rewrite reconciled with the audited lineage (Phase 1/2 assets survive), revision P0 blockers landed (dev splits, seed-isolated sweep, old-pipeline retirement)
**Requirements**: PIPE-02, PIPE-03, REV-01, REV-02, REV-10
**Plans**: 4/4 complete (03-01 D-01 merge + old-pipeline deprecation + species-lock pivot · 02-02→03-02 registry unification + F1 dev splits · 03-03 [gpu] exact-pin group + ty wiring + card fill · 03-04 run_sweep.py matrix driver + G1/D-07/D-11 fixes)
**Completed**: 2026-10-10

#### Phase 4: Correctness & Methodology Core

**Goal**: Every confirmed correctness bug fixed surgically with test evidence — species grouping via dataset-side metadata, unified exporter with explicit metric-key mapping — and every page works
**Requirements**: FIX-01, FIX-02, FIX-03, FIX-04, REV-03
**Plans**: 5/5 complete (04-01 species fix + xfail unmarks + 42/42 swap inventory · 04-03 frontend restoration (6 pages, 48/48 Playwright) · 04-04 quirk parity ports + 62/62 cards · 04-02 unified exporter + vendored aggregate_seeds · 04-05 pivot retirement + IN-03 single metric-key authority)
**Completed**: 2026-10-10

#### Phase 5: CI & Three-Seed Full Re-Run (E2')

**Goal**: Aggregation methodology upgraded before numbers publish, CI proves repo health end-to-end, E2' readiness landed code-only behind the maintainer dual gate
**Requirements**: TEST-04, TEST-05, TEST-07, DATA-01, DATA-02, DATA-03, DATA-06, REV-04, REV-06, REV-07, REV-09
**Plans**: 4/4 complete (05-01 SHA-pinned 4-job CI workflow · 05-02 F6 aggregation migration as one atomic commit (zero existing numbers moved) · 05-03 N-frequency audit + unified eval subsets + --subset_file seam · 05-04 E2' readiness: sweep priority tiers, --from-failures, env_smoke gate, alias normalization)
**Completed**: 2026-10-10

#### Phase 6: Revision Packaging & Extended Lanes

**Goal**: External reviewers can understand, trust, reproduce, and extend the platform; extension lanes (PEFT, zero-shot VEP, probes, curves) delivered as far as the revision window allowed
**Requirements**: REL-03, DATA-04, DATA-05, DATA-07, EXT-01, EXT-02, REV-03, REV-05, REV-08
**Plans**: 5/5 complete (06-01 dnallm v1.2.1 adaptation + sanctioned GB10 env_smoke/peft smokes · 06-02 PEFT lane + frontier machinery · 06-03 zero-shot VEP registry driver · 06-04 provenance chain + snapshots + docs trio + doi_swap prepared · 06-05 frozen probes + learning curves)
**Completed**: 2026-10-11

</details>

### v1.2 TUI任务 — Milestone Goal & Binding Constraints

**Milestone Goal:** Operators drive the benchmark platform confidently from one terminal console — select, bring their own models and datasets, fetch data, configure, gate, launch, monitor, recover — while every number stays correct, reproducible, and CLI-reachable.

**Binding Constraints** (load-bearing for every phase in this milestone):

1. **E2' stays maintainer dual-gate.** The TUI may launch bounded runs and present the full-sweep confirmation gate, but the full three-seed E2' re-run is always explicitly maintainer-authorized. No pipeline execution of any kind — including Phase 11's bounded smoke — without explicit maintainer authorization; this milestone is code-first.
2. **CI stays GPU-free and dnallm-free.** All TUI/service tests run CPU-side with injectable seams. `textual`-the-library is allowed in a CPU test lane (Phase 8 discuss item to ratify: library yes, display/GPU runtime no); zero new CI jobs.
3. **DNALLM sibling repo is strictly read-only** (`/home/forrest/Github/DNALLM` @ v1.2.1) — issue channel only, never written.
4. **CLI parity is a rule, not a nicety.** Every TUI capability exists as a CLI capability and stays CI-exercised; orchestration must never become TUI-only; E2' authorization records the exact CLI command, never a persisted TUI state.
5. **TUI orchestrates, never computes.** No client-side re-implementation of benchmark semantics — the TUI reads artifacts and drives existing implementations (pure-function import or subprocess), and shows the actual argv it will exec.
6. **Surgical pipeline surface.** The only pipeline modifications are the four sanctioned argv flags (`--subset_file`, `--effective_batch_size`, `--num_train_epochs`, `--cache_dir`), the FlopsCounter port, and the official+custom registry overlay seam (CUST-05; maintainer refinement 2026-10-11 — custom entries live in user-owned files, never written into `pipeline/{models,datasets}_info.json`); no opportunistic refactors.
7. **Static hosting model unchanged.** WEB-01's progress mirror is generated static files — no backend, no API — consistent with the vanilla no-build web constraint.
8. **Multi-GPU is hard-gated** on Phase 11 single-GPU validation (maintainer sequencing: 单卡开发成功再开发多卡).
9. **Quality gates:** ruff AND ty cover all new code from Phase 7 onward (`make lint` / `make typecheck`).
10. **Stack addition is surgical:** Textual (`>=8.2,<9`) + platformdirs via a new `[tui]` uv group; textual-dev/textual-serve never in committed groups; data/gpu lanes never see textual.
11. **Custom/official registry separation is absolute** (maintainer refinement 2026-10-11: 自定义的不与官方放在一起，免得冲突): custom onboarding writes only user-owned registries (`~/.config/dnallmmark/custom_models.json` / `custom_datasets.json`); official registry files are project-maintained and never written by any custom flow; the overlay fails fast on custom-key collision with official keys; absent custom files mean byte-identical behavior and untouched existing tests.

**Phase structure rationale** (granularity: coarse): 6 phases is the natural floor, not padding — multi-GPU cannot merge into the single-GPU phase (maintainer hard gate), the data manager cannot merge into launch (env presence FAILs must be diagnosable first), and pipeline-side enablement stays separate so its verification is never coupled to TUI work. The custom-entries revision (maintainer, 2026-10-11) splits along the exact seam the maintainer drew: the pipeline-side registry overlay (CUST-05) joined Phase 7 — it touches the same run_sweep/run_finetune files, carries the same byte-identical-when-absent discipline as argv parity, and must land before any wizard consumes it — while the wizard surface (CUST-01..04, CUST-06) is a dedicated Phase 9 directly after the selection foundation it builds on and marks: five requirements with a distinct safety story (collect-all fail-fast validation + dry-run/audit gauntlet + entry-level rollback) that would have blurred both verification stories if folded into Phase 8 (14 requirements) and is phase-sized the same way DATA and PIPE are. Downstream renumbering (old 9→10, 10→11, 11→12) is free — zero plans existed. Folded from the research sketch: the small argv-threading lane joined Phase 7; WEB-01/TEST-01 attached to Phase 12.

### Phase 7: Pipeline-Side Enablement (FlopsCounter Port, argv Threading & Registry Overlay)

**Goal**: The pipeline can be fully driven, measured, and extended by an external operator tool — FlopsCounter's 20+ architecture forward-hook FLOPs instrumentation ported from the deprecated `dnallmmark_pipeline.py` into `run_finetune.py`, the four sanctioned `run_sweep.py` argv flags threaded through with CLI parity, the official+custom registry overlay seam (user-maintained custom entries load on top of official registries; byte-identical when absent), and the tolerant JSON loader contract that FLOPs output and the future monitor share
**Depends on**: Nothing (first phase of v1.2; pipeline-side and TUI-independent — verification is deliberately NOT coupled to any TUI phase)
**Requirements**: PIPE-01, PIPE-02, PIPE-03, CUST-05
**Success Criteria** (what must be TRUE):
  1. `run_sweep.py` accepts `--subset_file`, `--effective_batch_size` (auto-GA: GA = max(1, N//batch_size), default 16), `--num_train_epochs`, and `--cache_dir`, threads them into the child argv, and produces byte-identical behavior when the flags are absent — proven by argv-shape assertions in the existing sweep test harness
  2. A run through `run_finetune.py` emits FLOPs accounting equivalent to the legacy pipeline: hook dispatch over the 20+ carried architectures (HF attention variants, GQA, BigBird, windowed attention, Hyena, Mamba/Mamba2, Caduceus, Borzoi/Enformer, megaDNA, …) proven by CPU-side unit tests over stub torch modules — no GPU and no dnallm import required to test
  3. FLOPs/report JSON is read through the shared tolerant-loader contract: truncated or partially-written files are skipped with last-known-good retained instead of crashing — contract test-pinned for reuse by the Phase 11 monitor
  4. The registry consumers (`run_sweep.py`, `run_finetune.py`, audit, export) load official registries with an optional custom overlay from user-owned files (`~/.config/dnallmmark/custom_models.json` / `custom_datasets.json`): a custom key colliding with an official key fails fast with a clear error, and with no custom files present behavior is byte-identical to today — existing registry/sweep tests pass unmodified, proven CPU-side in the existing harness (official `pipeline/{models,datasets}_info.json` are never written by any custom flow)
  5. `make lint` + `make typecheck` cover the changed files and CI stays green with zero GPU/dnallm dependency; every new flag works headless (scripts stay first-class)

**Plans**: 6/6 plans complete
Plans:
**Wave 1**
- [x] 07-01-PLAN.md — FLOPs report chain on CPU: flops_counter module (lazy-torch port, uncovered accounting), artifact_loader tolerant contract, schemas/flops_report.json (D-27 one-way checkpoint), Makefile lint coverage
- [x] 07-02-PLAN.md — registry overlay (CUST-05): registry_loader with collision fail-fast + env/XDG path resolution, five load sites rewired, absent = byte-identical

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 07-03-PLAN.md — run_sweep four-flag argv threading (PIPE-02): registration, abs-path resolution, collect-all subset pre-validation, only-when-present manifest fields, argv parity tests
- [x] 07-04-PLAN.md — run_finetune FlopsCounter integration (PIPE-01): always-on calibration slot before the trainer, post-success flops_report write WR-13-ordered with hardware section

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 07-05-PLAN.md — legacy deletion (D-04): re-pin 5 parity tests as literals, delete dnallmmark_pipeline.py, purge stale references, full lint/typecheck/test gates
- [x] 07-06-PLAN.md — GB10 bounded FLOPs smoke (D-21..D-26): CPU dry-run flag proof, GPU emission, D-23 sanity criteria, evidence in SUMMARY

### Phase 8: TUI Foundation (Env Check & Selection)

**Goal**: The console exists and is trustworthy at rest — `make tui` opens a Textual app whose startup shows a persisted full environment-check panel, and operators build model×dataset selections k9s-style with presets, templates, and presence columns — with every non-retrofittable decision (textual-free services layer, `[tui]` dependency group, Pilot test harness, tolerant artifact loader, constants-module i18n convention) landed so later phases add screens, not architecture
**Depends on**: Phase 7 (tolerant-loader JSON contract reused by `tui/services/`)
**Requirements**: ENV-01, ENV-02, ENV-03, ENV-04, SEL-01, SEL-02, SEL-03, SEL-04, I18N-01
**Success Criteria** (what must be TRUE):
  1. `make tui` (uv `--group tui`, `python -m tui`) opens the console over SSH/tmux on GB10; startup runs the full environment check (reusing env_smoke kernels: version pins, dnallm import, CUDA, dataset directories, numpy>=2, peft) and presents per-item ✓/✗ status with drill-down detail
  2. Check results persist with a visible check date ("上次检查: YYYY-MM-DD HH:MM"); same-day restarts read the cache without re-running, and a manual refresh action re-checks on demand
  3. Critical FAILs (no GPU / missing dependency) visibly block entry into the launch flow with the reason shown; missing-dataset items route the operator toward data management; a lightweight quick-check re-validates the launch-required subset before each task launch
  4. The model list and dataset list are first-class selectable surfaces — browsed independently with key card fields as columns (62 models / 50 datasets); operators filter them k9s-style (arena/type/species/scale), spacebar-mark rows into a stable row_key selection set, apply presets (tier-1 E2E pair, tier-2 arena representatives, all, saved customs), and consult a read-only matrix overview as an auxiliary view — never an editable grid
  5. Every row shows local data presence (✓ present / ✗ missing + n_audit row count) and run-config templates round-trip as validated JSON with `sweep_priorities.json` tier interop; all operator-facing copy is Chinese-primary through the constants module with technical terms in English — and the foundation invariants hold (services layer imports zero textual symbols by test, `[tui]` group keeps textual out of data/gpu lanes, Pilot tests green CPU-side in CI)

**Plans**: 7/7 complete + 2 gap-closure plans (08-08 + 08-09, verification Truth 6)
Plans:
**Wave 1**
- [x] 08-01-PLAN.md — env_smoke D-02 structured-return refactor (ENV-01 substrate): golden byte-characterization suite + kernels-return-CheckResult + renderer main(), E2' contract byte-stable
- [x] 08-02-PLAN.md — foundation spine (D-01): [tui] group + make tui + tui/ skeleton + test-harness conftest; textual-free services discipline declared; CI lane unchanged

**Wave 2** *(blocked on 08-02)*
- [x] 08-03-PLAN.md — phase tracer: console boots on the env-check shell over the registry seam (load_registry_counts 62/50); services-textual-free import-lock test + tier-1/tier-2 test lanes

**Wave 3** *(blocked on 08-01 + 08-03)*
- [x] 08-04-PLAN.md — env/registry services (D-04/05/08/09/10): XDG state/config split, env-check orchestration + same-day cache, env-gate judgment + quick-check subset, registry entries + n_audit presence

**Wave 4** *(blocked on 08-04)*
- [x] 08-05-PLAN.md — selection/template services (D-06/D-07, one-way checkpoint): strict run_template schema + collect-all validation + sweep_priorities tier interop, preset derivation, custom presets, filter grammar
- [x] 08-06-PLAN.md — env-check screen + composition root + i18n strings (ENV-01..04 presentation, I18N-01): thread-worker async fill, 上次检查 cache line, advisory gate verdict, verbatim drill-down, min-size/no-color guards

**Wave 5** *(blocked on 08-05 + 08-06)*
- [x] 08-07-PLAN.md — selection + matrix screens (SEL-01..04, I18N-01): k9s filter + mark-set on stable row keys, preset/template modals, presence columns, read-only matrix overview, 80-col backstop Pilot tests

**Wave 6** *(gap closure — blocked on 08-07)*
- [x] 08-08-PLAN.md — tolerant-loading gap closure (Truth 6 / CR-01 + WR-01): isinstance guards in both registries projections + widened _load_entries tuple, fail-closed env_smoke directory kernels + guarded env-screen worker, exit_on_error never-exit net with per-site ledger + AST pin, both seam regression tests

**Wave 7** *(round-2 gap closure — blocked on 08-08)*
- [x] 08-09-PLAN.md — screen-side card-read family closure (Truth 6 residual, second gaps_found): isinstance guards at the w vocabularies + enter drill-down + _manual_landing_path hardening, w/enter/d real-app Pilot regression tests, card-extraction AST family pin

**UI hint**: yes

### Phase 9: Custom Model & Dataset Onboarding (自定义接入向导)

**Goal**: Operators can bring their own model and dataset into the benchmark entirely from the console, with official registries provably untouched — guided wizards collect the full entry into user-owned custom registries, fool-proofing validation collects every field problem in one fail-fast report before anything is written, and an entry lands only after passing the real gauntlet (dry-run precheck + audit reconciliation) with entry-level rollback when anything fails
**Depends on**: Phase 7 (registry overlay seam — custom entries become visible to sweep planning, audit, and export), Phase 8 (selection list surfaces provide the wizard entry points and the custom markers; services skeleton; constants-module i18n)
**Requirements**: CUST-01, CUST-02, CUST-03, CUST-04, CUST-06
**Success Criteria** (what must be TRUE):
  1. From the model list, one action opens the custom-model wizard — guided collection of the model card (name/architecture/tokenizer/species/scale/HF+ModelScope URLs/local path) with the quirk checklist (safetensors/fp32/special heads…) as optional checkboxes — and a validated submission lands in the user-owned custom registry (`~/.config/dnallmmark/custom_models.json`), after which the model appears in the model list via the overlay; `pipeline/models_info.json` is never written
  2. The same exists for datasets from the dataset list — key name/path/train-dev-test files/label column/primary metric/Task_type/provenance columns — landing in `~/.config/dnallmmark/custom_datasets.json` with `pipeline/datasets_info.json` never written
  3. Submission is blocked until validation passes, and validation is collect-all fail-fast (the `_validate_filters` discipline): required/type/enum checks, key collisions against official AND existing custom entries, path existence, split-file parseability, row count > 0, label-column validity, and metric-in-registry are checked in one pass with every problem listed item-by-step — never one error at a time
  4. After submission the automatic error detection runs — dry-run precheck plus audit reconciliation (row counts / non-ACGT / subset survival); any failure is reported prominently and the failed entry never lands: the custom registry reverts cleanly at entry level (official files zero-risk), leaving no half-written state that could trip the registry chain's abort-on-wrong-count discipline
  5. Landed custom entries carry a visible custom marker in both lists (distinct from the official 62/50), can be individually enabled/disabled, and export as the shareable unit (the custom registry file itself); the official registries and the existing test suite stay green and untouched

**Plans**: 6/6 plans complete
Plans:
**Wave 1**
- [x] 09-01-PLAN.md — custom-entry services core (CUST-01/02/03/06 tier): store (land/undo/toggle/import/export) + collect-all validator + schemas/custom_registry.json; tracer proves write → overlay-load end-to-end

**Wave 2** *(blocked on 09-01)*
- [x] 09-02-PLAN.md — gauntlet service (CUST-04): dry-run + audit subprocess legs with artifact-based pass criteria + the D-09 enabled:false skip (the one pipeline change) + the committed-artifact byte-unchanged regression
- [x] 09-03-PLAN.md — navigation shell (D-04/D-13..16): top menu + bottom bar + digit nav + Header/Footer migration + the 关于 screen (slot 6)

**Wave 3** *(blocked on 09-01 + 09-03)*
- [x] 09-04-PLAN.md — wizard modal family, collection half (CUST-01/02 UI + CUST-03 report): 4-step forms, type-aware controls, value preservation, collect-all report view, 80×24 long-text backstop

**Wave 4** *(blocked on 09-02 + 09-04)*
- [x] 09-05-PLAN.md — wizard writing half (CUST-04 UI + D-08/D-11): async gauntlet panel (land-only-on-all-✓), session undo, per-entry import gauntlet, export

**Wave 5** *(blocked on 09-03 + 09-05)*
- [x] 09-06-PLAN.md — selection integration (CUST-06 + D-09/10/12/14): w entry with prefill, e toggle, ◇ badge + （已停用）visibility, count segment, disabled-mark block, full-loop test + phase gates

**UI hint**: yes

### Phase 10: Data Manager (Downloads & Verification)

**Goal**: Dataset gaps are closable in-session before launch — one-click ModelScope download driven by the registry's authoritative `download_url`, a persistent resumable queue, and row-count reconciliation against n_audit — so an env-check presence FAIL is always diagnosable and fixable from the console
**Depends on**: Phase 8 (presence view, settings/services skeleton)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04
**Success Criteria** (what must be TRUE):
  1. From a missing-dataset row, one action downloads via the ModelScope channel with the registry `download_url` as the only authority; on landing, presence flips to ✓ in the selection table and the environment check
  2. The download queue persists across TUI exit/crash and resumes where it stopped after restart
  3. Every landed download reconciles row counts against the n_audit baseline, with mismatches reported prominently rather than silently accepted
  4. The Zenodo bulk bundle (record 19135551, once public) is reachable as an alternate whole-package entry
  5. Downloads run under subprocess/thread-worker discipline (the console never freezes) and no credentials are stored or echoed in logs or queue state

**Plans**: 7/7 planned
Plans:
**Wave 1**
- [x] 10-01-PLAN.md — queue service core (DATA-01/02 substrate): XDG-persisted five-state queue, R-01 channel resolution + R-02 shape table (46/4 census), CLI probe, Popen engine with progress parse, landing check, shape-C rename, killpg cancel

**Wave 2** *(blocked on 10-01)*
- [x] 10-02-PLAN.md — reconcile kernel (DATA-03): audit subprocess leg (temp staging, absolute Dataset_path, artifact verdicts), done-gate + mismatch, presence overlay merge, `g` re-audit (R-03 default outputs) + byte-unchanged regression

**Wave 3** *(blocked on 10-02)*
- [x] 10-03-PLAN.md — Zenodo probe + bundle driver (DATA-04): 4-state GET probe, guarded download/extract, zenodo-kind queue integration, the full DL_/QUEUE_ string block + ENV_ROUTE amendment

**Wave 4** *(blocked on 10-03)*
- [x] 10-04-PLAN.md — data-manager screen (slot 3): two-pane layout, five-state glyphs, progress cells, mismatch banners, drill-down, Zenodo line, d/r/x/a/enter/g/z; app-level driver worker + boot resume; nav promotion

**Wave 5** *(blocked on 10-04)*
- [x] 10-05-PLAN.md — cross-screen integration (D-14/D-11): selection `d` enqueue on presence-✗ rows, presence overlay in the selection snapshot + live flip, env route hint proof

**Wave 6**
- [x] 10-06-PLAN.md — hardening + phase-goal verification: CLI-absent/corrupt/unknown-key/restart edge sweep, exhaustive transition table, full gates, SC1-5 goal-backward checklist + GB10 live-smoke procedure

**Wave 7** *(gap closure — blocked on 10-06)*
- [x] 10-07-PLAN.md — CR-01 gap closure (SC1 env-check conjunct, DATA-01): reroute `_datasets_base` through the run-config chain (`resolve_dirs(load_state()).dataset_root_abs`, the `_models_base` twin) + the three-configuration landing/consumption agreement regression matrix

**UI hint**: yes

### Phase 11: Run Config, Launch Gates & Single-GPU Monitoring

**Goal**: The operator's core loop is closed and safe — compose a complete run spec, preview it from the same pure planning functions execution uses, pass the env + confirmation gates, launch `run_sweep.py` as a detached subprocess, and monitor/recover the sweep from the same console — proven end-to-end by a maintainer-authorized bounded smoke on GB10, with E2' provably still maintainer-gated
**Depends on**: Phase 10 (data readiness), Phase 7 (argv flags + FLOPs-correct runs)
**Requirements**: CFG-01, CFG-02, CFG-03, LNC-01, LNC-02, LNC-03, MON-01, MON-02, MON-03, MON-04, MON-05
**Success Criteria** (what must be TRUE):
  1. The run-config screen exposes the full parameter set — seeds (default 42,43,44), PEFT mode with alias preview, config-variant head/probe/curve with PROBE_INELIGIBLE hints, learning-curve tiers, fairness-subset toggle, epochs/batch overrides, auto-GA via `--effective_batch_size` — plus separated project/storage directories (repo-relative defaults; absolute paths passed on explicit override) and a dry-run preview computed by importing the same pure planning functions execution uses, showing enumerated cell counts
  2. The launch gate is terraform-style: env_smoke preflight blocks on FAIL with the reason, preview precedes explicit confirmation, and the full E2' three-seed sweep additionally requires a typed confirmation phrase — the TUI presents the gate but cannot bypass maintainer authorization
  3. Execution is always a `run_sweep.py` subprocess (LIST argv + PYTHONUNBUFFERED=1 + start_new_session detachment); on TUI exit the operator chooses kill/detach/cancel, and a detached sweep is resume-safe to re-attach to later
  4. The monitor dashboard shows cell-level state (queued/running/done/failed/skipped, seed-adjacent) via 2s frontier + 60s full tolerant scans, progress stats (done/total, current cell, elapsed), attach mode for externally (CLI) launched sweeps, a live failure list with confirmation-gated `--from-failures` re-run, bounded log tailing with tee-to-disk persistence, and resume recognition from `trainer_state.json` markers
  5. A maintainer-authorized bounded smoke (1 model × 1 task × 1 seed, 1 epoch) runs launch → monitor → failure-re-run end-to-end on GB10 while the E2' full-sweep gate demonstrably blocks; every capability remains reachable headless via CLI

**Plans**: 8/8 plans complete (7 complete + gap closure 11-08)
Plans:
- [x] 11-01-PLAN.md — run_sweep `--config-variant` via the peft ALIASING machinery (D-18; not pass-through), argv-parity + frozen-pair read-source tests
- [x] 11-02-PLAN.md — run_config service: XDG-persisted own pickers state, full params model, dirs, same-source preview (imported enumerate_matrix), E2' verdict + typed phrase, PROBE_INELIGIBLE extraction
- [x] 11-03-PLAN.md — sweep_launcher service: spawner seam + detached Popen/tee (D-10 single root), env preflight over the frozen face, structural E2' phrase gate, kill/detach registry, from-failures launch
- [x] 11-04-PLAN.md — sweep_monitor service: three-state discovery, tolerant record readers, cell states + resume, D-17 elapsed/median-ETA math, live failures, bounded log tail
- [x] 11-05-PLAN.md — CFG_/LNC_/MON_ strings verbatim + bidirectional tripwire + ENV_VERDICT amendment + the 7→9 spec-prose correction
- [x] 11-06-PLAN.md — slot-4 运行配置 screen: pickers/params/dirs/preview line, [p] modal, the 启动门 modals (env-block, confirm, E2' typed phrase), ExitModal + q intercept, nav promotion
- [x] 11-07-PLAN.md — slot-5 任务监控 screen: discovery/attach, cell table, stats/ETA line, [f]/[t]/[a]/[r], D-13 auto-nav, degradation sweep, SC1-5 checklist + the GB10 bounded smoke procedure
- [x] 11-08-PLAN.md — gap closure (11-VERIFICATION): CR-01 attach-path resolution + WR-01 REPO_ROOT registry basis + WR-02/03 re-run seed derivation + honest confirm + WR-04 O_EXCL tee + WR-05 multi-root exit modal

**UI hint**: yes

### Phase 12: Multi-GPU Orchestration & Console Hardening

**Goal**: With single-GPU validated, throughput scales out — CLI-invocable static model sharding × CUDA_VISIBLE_DEVICES with per-worker monitoring, artifact merge, and isolated failure re-run, plus the documented DDP-vs-sharding applicability decision — and the console ships its release extras: a static read-only web progress mirror and maintainer-verified snapshot goldens pinning the canonical screens
**Depends on**: Phase 11 (HARD GATE — single-GPU validation complete; maintainer sequencing: 单卡开发成功再开发多卡)
**Requirements**: MGPU-01, MGPU-02, MGPU-03, WEB-01, TEST-01
**Success Criteria** (what must be TRUE):
  1. Multi-worker orchestration is invokable from the CLI (not TUI-only): N workers over disjoint static model shards with `CUDA_VISIBLE_DEVICES` isolation, marker-skip as the only concurrency guard
  2. The operator sees per-worker monitoring views, artifacts merge across workers, and a failed worker's shard re-runs in isolation without touching healthy workers
  3. The DDP (torch-run data splitting) vs model-sharding applicability decision is documented and landed — single-large-model acceleration vs multi-model throughput
  4. A read-only web progress mirror generated from sweep artifacts lets the team follow progress in a browser — static files only, no backend (static-hosting constraint holds)
  5. Canonical screens are pinned by Textual snapshot SVG goldens reviewed and committed by the maintainer, failing CI CPU-side on visual regression

**Plans**: 5/5 plans executed
Plans:

**Wave 1** *(parallel)*
- [x] 12-01-PLAN.md — run_sweep_shard.py launch mode (D-07 new entry): collect-all validation, LPT size-weighted sharding (pure fn + property tests), verbatim-launcher spawn + CUDA_VISIBLE_DEVICES per worker, frozen `{root}-mgpu-w{i}` sibling roots/logs, aggregated exit verdict; Makefile lint guard
- [x] 12-02-PLAN.md — web mirror (D-02): script/gen_progress.py over the pure scanner (frozen data contract, newest_mtime dropped, byte-stable), progress.html/js/css + DataAPI.loadProgress + NAV_LINKS, JS-lane extension, golden-JSON generator tests

**Wave 2** *(blocked on wave 1)*
- [x] 12-03-PLAN.md — TEST-01 goldens (fallback lane, zero pyproject changes): export_screenshot string-compare harness, 8-SVG corpus, determinism + sensitivity, make snapshot-update + D-03 review gate; PLUS delta B — the one dismiss() override focus fix (10 paths, B1-B5 Pilot proof)
- [x] 12-04-PLAN.md — `--merge` mode (D-09: allowlist copy + SHA256 verify, manifest union + output_dir rewrite, lane-flag equality) + consumer-equivalence tests; docs/multi-gpu.md (D-04 decision matrix + runbook + 9-step other-machine procedure, D-05) + README link

**Wave 3** *(blocked on wave 2)*
- [x] 12-05-PLAN.md — phase close: delta A N-root Pilot proof (zero monitor code), D-08 isolation re-run test, N=1 degenerate local smoke, SC1-5 ledger with named tests, WINDOWS.md unrun-verify entry for the maintainer's other-machine N=2 smoke

**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 7 → 8 → 9 → 10 → 11 → 12
Phase 12 is hard-gated on Phase 11's single-GPU validation (maintainer sequencing).

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 7. Pipeline-Side Enablement (FlopsCounter Port, argv Threading & Registry Overlay) | v1.2 | 6/6 | Complete    | 2026-10-11 |
| 8. TUI Foundation (Env Check & Selection) | v1.2 | 9/9 | Complete    | 2026-10-12 |
| 9. Custom Model & Dataset Onboarding | v1.2 | 6/6 | Complete    | 2026-10-12 |
| 10. Data Manager (Downloads & Verification) | v1.2 | 7/7 | Complete    | 2026-10-13 |
| 11. Run Config, Launch Gates & Single-GPU Monitoring | v1.2 | 8/8 | Complete    | 2026-10-13 |
| 12. Multi-GPU Orchestration & Console Hardening | v1.2 | 5/5 | In Progress | - |

---
*v0.7.1 (Phases 1-6) shipped 2026-10-11 — collapsed above; full record in `.planning/MILESTONES.md`.*
*v1.2 TUI任务 roadmap created 2026-10-11 — 5 phases, 32/32 requirements mapped; revised 2026-10-11 per maintainer custom-entries adjustment — 6 phases (7-12), 38/38 requirements mapped.*

## Backlog

### Phase 999.1: 自定义模型/数据集防呆（fool-proofing）增强 (BACKLOG)

**Goal:** Custom-model/dataset entries gain layered fool-proofing — today the file-based path has only JSON-validity + official-key-collision checks (registry_loader fail-loud SystemExit) while the wizard validates path existence; the gap is the file lane and launch-time enforcement.
**Requirements:** TBD — candidate scope from the 2026-10-14 manual-verification session: (1) load-time path-existence preflight for custom entries, errors naming entry + path instead of a bare SystemExit; (2) field completeness/type validation with per-field actionable messages (against the models_info.json card schema: Model_path/Model_name/size/tokenizer etc.); (3) consistency checks (same path under multiple names, size (M) vs Model_size mismatch); (4) TUI side — broken/pathless custom entries marked red with a problems list on the selection screen, launch gate refuses runs containing broken entries; (5) optional custom-registry lint/doctor subcommand.
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd-review-backlog when ready)
