# Roadmap: DNALLM-Mark

## Milestones

- ✅ **v0.7.1 Release Hardening** - Phases 1-6 (shipped 2026-10-11)
- ✅ **v1.2 TUI任务** - Phases 7-12 (shipped 2026-10-19)

## Phases

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

<details>
<summary>✅ v1.2 TUI任务 (Phases 7-12) — SHIPPED 2026-10-19</summary>

*(Full accomplishment record: `.planning/MILESTONES.md`. Per-plan execution history: git log + `.planning/milestones/v1.2-phases/`.)*

- [x] Phase 7: Pipeline-Side Enablement (FlopsCounter Port, argv Threading & Registry Overlay) — 6/6 plans, completed 2026-10-11
- [x] Phase 8: TUI Foundation (Env Check & Selection) — 9/9 plans (7 + 2 gap-closure), completed 2026-10-12
- [x] Phase 9: Custom Model & Dataset Onboarding (自定义接入向导) — 6/6 plans, completed 2026-10-12
- [x] Phase 10: Data Manager (Downloads & Verification) — 7/7 plans, completed 2026-10-13
- [x] Phase 11: Run Config, Launch Gates & Single-GPU Monitoring — 8/8 plans (7 + gap closure), completed 2026-10-13
- [x] Phase 12: Multi-GPU Orchestration & Console Hardening — 5/5 plans, completed 2026-10-16

</details>

---
*v0.7.1 (Phases 1-6) shipped 2026-10-11 · v1.2 TUI任务 (Phases 7-12, 41 plans, 62 tasks) shipped 2026-10-19 — full records in `.planning/MILESTONES.md` and `.planning/milestones/`. Next milestone starts with `/gsd-new-milestone`.*

## Backlog

### Phase 999.1: 自定义模型/数据集防呆（fool-proofing）增强 (BACKLOG)

**Goal:** Custom-model/dataset entries gain layered fool-proofing — today the file-based path has only JSON-validity + official-key-collision checks (registry_loader fail-loud SystemExit) while the wizard validates path existence; the gap is the file lane and launch-time enforcement.
**Requirements:** TBD — candidate scope from the 2026-10-14 manual-verification session: (1) load-time path-existence preflight for custom entries, errors naming entry + path instead of a bare SystemExit; (2) field completeness/type validation with per-field actionable messages (against the models_info.json card schema: Model_path/Model_name/size/tokenizer etc.); (3) consistency checks (same path under multiple names, size (M) vs Model_size mismatch); (4) TUI side — broken/pathless custom entries marked red with a problems list on the selection screen, launch gate refuses runs containing broken entries; (5) optional custom-registry lint/doctor subcommand.
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd-review-backlog when ready)
