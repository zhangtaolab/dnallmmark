# Roadmap: DNALLM-Mark

## Milestones

- ✅ **v0.7.1 Release Hardening** - Phases 1-6 (shipped 2026-10-11)
- ✅ **v1.2 TUI任务** - Phases 7-12 (shipped 2026-10-19)
- ⏳ **v1.3 多 GPU 编排与验证** - Phases 13-18 (started 2026-10-20)

## Phases

### ⏳ v1.3 多 GPU 编排与验证 (Phases 13-18) — ACTIVE

**Defined:** 2026-10-20 · **Requirements:** 20 (`.planning/REQUIREMENTS.md`) · **Research:** `.planning/research/SUMMARY.md` · **Core:** cell-level dynamic dispatch, one cell = one GPU, no DDP

**Binding constraints (carried + new):** E2' full sweep stays maintainer dual-gated; every GPU execution (smoke, sweep) is maintainer-authorized, code-first; CI stays GPU/dnallm-free AND N>1-free (fake-children + injected seams only); DNALLM suite repo read-only — upstream defects get upstream issues, never local patches; TUI orchestrates, never computes; Linux-only platform; surgical fixes; leaderboard numbers move only through zero-drift-proven additive changes; legacy static-shard mode coexists (2026-10-20 ruling); 5% subsets pre-materialized with a dedicated config, never mixed with real runs.

#### Phase 13: 动态调度核心

**Goal**: The orchestrator dispatches (model×dataset×seed) cells as a work queue over per-GPU workers with worker-independent cell outputs, an exactly-once claim ledger, and resume semantics proven under mid-cell kill — legacy static sharding coexists behind explicit mode declaration
**Requirements**: MGPU-01, MGPU-02, MGPU-06
**Plans**: 2/2 plans complete

Plans:
**Wave 1**
- [x] 13-01-PLAN.md — Dispatch tracer: --mode routing + engine (queue, O_EXCL ledger/lock, worker loops) + SC2 kill-proven resume (MGPU-01, MGPU-02) — complete 2026-10-20 (78 tests: 29 dispatch + 49 static tripwire; lint/typecheck green)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 13-02-PLAN.md — Dry-run plan artifact + SC1 goldens, evidence-based merge refusal, static byte-identity pins, Makefile lint line, full gates (MGPU-01, MGPU-06) — complete 2026-10-20 (90 tests: 12 new + 78 tripwire; lint/typecheck green; node 26/26; ci.yml hash-pinned; full-gate pre-existing failures logged in deferred-items.md)

**Success criteria**:
1. Dry-run enumeration is deterministic and byte-identical across runs; the planned cell set matches static-mode enumeration for identical inputs
2. Fake-children kill test: a worker killed mid-cell, orchestrator relaunched → every cell completes exactly once (no duplicates, no orphans) — the P1 acceptance test
3. Cell artifacts land at worker-independent paths; double-claim is structurally refused (O_EXCL ledger)
4. Legacy static-shard launch behaves byte-identically behind its declared mode; `--merge` refuses mixed-mode roots with a named error
5. Full CPU gates green (pytest/ruff/ty, node lanes); zero CI changes; zero N>1 assumptions in any test

#### Phase 14: 编排运行视图与失败恢复

**Goal**: Running multi-GPU sweeps are observable (terminal table + machine-readable state file) and recoverable (cross-worker failure re-run with lane context; post-merge verify + confirm-gated cleanup)
**Requirements**: MGPU-03, MGPU-04, MGPU-05
**Plans**: 3/3 plans complete

Plans:
**Wave 1**
- [x] 14-01-PLAN.md — Frozen dispatch-state v2 consumer schema (schemas/dispatch_state.json) + live plain-line terminal table at the _write_state choke point (MGPU-03) — complete 2026-10-20 (66 dispatch tests: 13 new over the 53 baseline; 115 combined with the static tripwire; lint/typecheck green; ci.yml hash-pinned; pty+pipe flush lanes live-proven)
- [x] 14-02-PLAN.md — export_runs.py --dry-run seam + `--cleanup` sibling mode: dual verification then typed-phrase-gated worker-root removal (MGPU-05) — complete 2026-10-20

**Wave 2** *(blocked on Wave 1 file overlap: dispatch_core.py + run_sweep_shard.py)*
- [x] 14-03-PLAN.md — Ledger-driven cross-worker failure re-run: `--rerun-failed` with claim-time lane replay, archive+rerun_of genealogy, heterogeneous-lane refusal (MGPU-04) — complete 2026-10-20 (93 dispatch tests: 27 new over the 66 baseline; D14-15 e2e proves one command re-runs exactly the failed cells with byte-identical lane argv; 155 dispatch+shard combined; lint/typecheck/node green; ci.yml hash-pinned)

**Success criteria**:
1. `dispatch_state.json` (single-writer, atomic) carries queue depth, per-worker in-flight cells, failures, timestamps; schema frozen and parseable by a consumer test
2. The terminal progress table renders live per-worker state during a fake-children run (pty-lane assertable)
3. Injected failures across two workers → ONE re-run command re-runs exactly the failed cells with the original lane flags (peft lane preserved — 12-04 lane-blindness fixed, fixture-proven)
4. Verify+cleanup helper: verifies the merged root (export dry-run + manifest counts) before offering worker-root removal behind an explicit confirmation; refusal paths tested

#### Phase 15: 双卡验证与子数据集 (N=2 Smoke & Small Real Sweep)

**Goal**: The dispatch orchestrator is proven on the local 2× RTX 5090 — the docs/multi-gpu.md N=2 smoke passes (WINDOWS #21 closed, D-05 revised) and a small real sweep over pre-materialized 5% stratified subsets runs both GPUs end-to-end through merge and the data chain
**Requirements**: VAL-01, VAL-02, VAL-03
**Plans**: 5/5 plans complete

Plans:
**Wave 1**
- [x] 15-01-PLAN.md — N=2 dispatch smoke on the local 2×5090 (smoke-pair acquisition via modelscope, 2-cell real dispatch run, D15-02 pass criteria + consumption dry-run) + docs/multi-gpu.md dispatch-mode rewrite, WINDOWS #21 closure, PROJECT.md D-05 row (VAL-01)
- [x] 15-02-PLAN.md — Subset generator `script/make_subset_datasets.py` (stdlib-only, stratified 5%, floor-of-1 small-split rule, subset registry with measured counts) + tests/test_subset_datasets.py byte-identity/isolation/fail-fast pins + .gitignore/Makefile entries (VAL-02)

**Wave 2** *(blocked on Wave 1: smoke must pass per D15-04; generator + test file from 15-02)*
- [x] 15-04-PLAN.md — GAP CLOSURE, executes immediately (no deps, before the 15-01 continuation and 15-03): dispatch_core writes run_record.json at claim finalize — run_sweep `_new_record` shape parity, WR-12 no-overwrite refusal, failed-cell/WR-11 records, CR-04 failure routing, export dry-run consumer visibility + 15-03 false-premise corrections (supersedes Phase 13 A3 at its deferred handoff; unblocks the 15-01 D15-02 consumption criterion) (VAL-01)
- [x] 15-05-PLAN.md — GAP CLOSURE (option A ruling 2026-10-21, WINDOWS #45): run_finetune captures trainer.evaluate() and merges it flat-additive into final_metrics.json (exact export-read eval_* spellings; D-05/WR-13 ordering preserved; argv untouched) + tier-1 pin update-not-weaken + 15-03 archive-list correction (animal/microbe) — producer side only; the sweep re-run is owned by the 15-03 continuation on the fresh root pipeline/finetuned-sweep-r2 (VAL-03) — complete 2026-10-21 (contracts 76 green incl. new eval-merge pin; dispatch/sweep regression 306 green unmodified; lint/typecheck green; ci.yml hash-pinned; chain porcelain empty; add_argument 27; WINDOWS #45 stays open pending the continuation)
- [x] 15-03-PLAN.md — Real subset generation (105/11/117 + 598/74/74) + 12-cell dual-GPU dispatch sweep (2 models × 2 subset tasks × 3 seeds, one shared root, 0 skipped) + zero-modification export→summarize consumption proof with archived phase artifacts + D15-15 real-artifact pytest checks (VAL-03) — complete 2026-10-21 across halt + 15-05 option-A fix + fresh-root resume: the r2 re-run (272 s, done 12/12, 0 skipped, both GPUs) carries eval_f1 in all 12 final_metrics; export→summarize emitted non-empty models_comparison + _animal (5mC) + _microbe (emp_H3); five JSONs archived; WINDOWS #45 closed; suite 27 green — Tasks 1-2 green; halted at Task 3 consumption (WINDOWS #45); the Task-3 continuation (sweep re-run on finetuned-sweep-r2 + consumption + archive + VAL-03 marks) executes after 15-05

**Success criteria**:
1. N=2 smoke procedure completes successfully on the local box; WINDOWS #21 closed; D-05 machine-role revision recorded (maintainer-authorized GPU run)
2. Subset generator: deterministic stratified 5% subsets with measured row counts in a dedicated subset registry/config; run-twice byte-identity; official/custom registries untouched
3. Small real sweep (≈2-4 models × 2-3 datasets × 3 seeds, 1 epoch) completes on both GPUs via dynamic dispatch; merged output consumed by the export/data chain without modification
4. Subset and real runs provably never share registry/config/output roots (asserted in the executed procedure)

#### Phase 16: TUI 多 GPU 界面

**Goal**: The operator console launches and watches multi-GPU runs natively — slot-4 multi-GPU launch through the unchanged gate chain, slot-5 consumption of dispatch state, and the deferred G GPU-lanes display over a read-only nvidia-smi probe
**Requirements**: TUI-01, TUI-02, TUI-03, TUI-04
**Plans**: 0
**Success criteria**:
1. `gpu_probe` service: csv-mode subprocess probe → frozen dataclass rows, textual-free, honest 未安装 degradation; unit-tested via injected seam (no GPU in CI)
2. G GPU-lanes panel renders per-GPU utilization/memory/temperature on the monitor cadence; absent binary never crashes the console (worker guard discipline)
3. Slot-4 multi-GPU launch (workers/gpus + dispatch preview) passes through env gate → problems → confirm → E2' typed-phrase unchanged; single-GPU serial gate replaced by multi-GPU-aware semantics; gate-order tests extended, none weakened
4. Slot-5 renders queue depth/in-flight cells from `dispatch_state.json`; changed-screen snapshot goldens regenerated uncommitted for D-03 review

#### Phase 17: Web 多种子 Error Bar

**Goal**: Multi-seed results display with error bars on the public pages — additive mean/std/n_seeds through the data chain, scatter whiskers via a vendored inline Chart.js plugin, floating-bar task charts — with zero drift in existing numbers
**Requirements**: WEB-01, WEB-02, WEB-03
**Plans**: 0
**Success criteria**:
1. Aggregation emits additive-optional `mean`/`std`/`n_seeds`; with the fields suppressed, output is byte-identical to pre-v1.3 (zero-drift gate extended and green); METHODOLOGY.md documents display-only semantics + std definition
2. Scatter (FLOPs vs rank) renders whiskers via the vendored `afterDatasetsDraw` plugin (zero new CDN scripts); task bar chart uses floating bars; tooltips gain ±std — verified against real sweep-derived artifacts
3. Node-lane tests cover plugin value→pixel math as a pure function and additive schema fields via generated fixtures

#### Phase 18: 文档撰写

**Goal**: v1.3's multi-GPU workflow is fully documented for operators and external reviewers — the dispatch-mode runbook, README/ONBOARDING multi-GPU + subset sections, TUI multi-GPU usage doc, and version-consistent v1.3.0 release documentation (TUI-DEMO.md / docs-trio precedents)
**Requirements**: DOCS-01, DOCS-02, DOCS-03, DOCS-04
**Plans**: 0
**Success criteria**:
1. `docs/multi-gpu.md` fully rewritten for dispatch mode — every command copy-pasteable, the N=2 smoke procedure matching the executed Phase 15 reality, D-05 revision recorded, legacy static-shard mode documented as coexisting
2. README + ONBOARDING/GETTING-STARTED carry the multi-GPU dispatch section and the 5% subset workflow (generate → configure → run → merge), with no stale static-sharding-only instructions anywhere
3. TUI multi-GPU usage documentation (launch, monitoring, G lanes) in the TUI-DEMO.md precedent shape, verified against the shipped screens
4. Version surfaces consistent at 1.3.0 (pyproject, uv.lock, TUI about screen) and the milestone-stage row describes the delivered v1.3 scope (rewritten from the in-development wording at ship time)

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
