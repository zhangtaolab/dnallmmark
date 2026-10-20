# Requirements: DNALLM-Mark v1.3 多 GPU 编排与验证

**Defined:** 2026-10-20
**Core Value:** Every number on the public leaderboard is correct and reproducible from code that external reviewers can trust. (v1.3 extension: multi-GPU throughput without sacrificing one-cell-one-GPU honesty or a single published number.)

## v1.3 Requirements

Requirements for milestone v1.3. Each maps to roadmap phases (Traceability below).

### MGPU — 动态调度与编排

- [ ] **MGPU-01**: Orchestrator dispatches (model×dataset×seed) cells as a work queue — idle GPU workers pull the next cell; each cell runs entirely on exactly one GPU (never split across GPUs); enumeration is deterministic and dry-run-provable
- [ ] **MGPU-02**: Cell output paths are worker-independent (one root, ordinary cell subpaths) with an exactly-once O_EXCL claim ledger; killing a worker mid-cell and relaunching re-dispatches that cell to exactly-once completion (test-pinned)
- [ ] **MGPU-03**: Live orchestrator run view — a terminal progress table AND a single-writer atomic `dispatch_state.json` (queue depth, per-worker in-flight cell, failures, timestamps) consumable by the TUI and `gen_progress.py`
- [ ] **MGPU-04**: Cross-worker failure re-run — one command re-runs the union of failed cells across workers with full lane context (peft/variant/epochs) recorded at claim time, fixing the v1.2 lane-blindness limitation
- [ ] **MGPU-05**: Post-merge verify + cleanup helper — verifies the merged root (export dry-run + manifest count check), then removes worker roots behind an explicit confirmation gate (replaces the manual `rm -rf` recipe)
- [ ] **MGPU-06**: Legacy static model-sharding mode coexists behind the same CLI with explicit mode declaration; `--merge` refuses mixed-mode roots loudly; dispatch-mode roots need no merge (documented)

### VAL — 双卡验证（本机 2×5090）

- [ ] **VAL-01**: The `docs/multi-gpu.md` N=2 smoke procedure executes successfully on the local 2× RTX 5090 box (WINDOWS #21 closed); the D-05 machine-role decision is revised in-doc (本机 = 双卡验证机)
- [ ] **VAL-02**: 5% sub-datasets are pre-materialized as first-class dataset directories — deterministic seed-governed STRATIFIED sampling per split, measured row counts carried in a dedicated subset registry/config file, separate output roots; subset runs and real runs never share a registry, config, or output root
- [ ] **VAL-03**: A small real sweep (≈2-4 models × 2-3 datasets × 3 seeds, 1 epoch, 5% subsets) completes on both GPUs through dynamic dispatch → merge/data-chain consumption end-to-end with real training
- [ ] **VAL-04**: `docs/multi-gpu.md` and related runbooks are updated to dispatch mode with every command copy-pasteable (including the subset-generation step)

### TUI — 控制台多 GPU 界面

- [ ] **TUI-01**: A textual-free nvidia-smi read-only probe service (CSV query mode, frozen dataclass rows, honest 未安装 degradation when absent) feeds a G GPU-lanes display on the monitor cadence
- [ ] **TUI-02**: Slot-4 run config launches multi-GPU runs (workers/gpus params, dispatch-plan preview) through the UNCHANGED gate chain (env gate → problems → confirm → E2' typed-phrase when full-scope); the single-GPU serial gate is revised to multi-GPU-aware semantics, never bypassed
- [ ] **TUI-03**: Slot-5 monitor consumes `dispatch_state.json` (queue depth, in-flight cells) alongside existing scanner sources; multi-GPU runs render natively
- [ ] **TUI-04**: Snapshot goldens for changed screens regenerate under the D-03 maintainer-review discipline (uncommitted until reviewed)

### WEB — 多种子 Error Bar

- [ ] **WEB-01**: Aggregation emits additive-optional `mean`/`std`/`n_seeds` fields per model×dataset — absent fields produce byte-identical JSON (zero-drift gate proves additivity); METHODOLOGY.md documents the display-only semantics (std definition fixed once)
- [ ] **WEB-02**: FLOPs-vs-rank scatter gains error-bar whiskers via a vendored inline Chart.js plugin (`afterDatasetsDraw`, no new CDN dependency); the task bar chart uses native floating bars + whiskers; tooltips gain ±std
- [ ] **WEB-03**: Node-lane tests cover the plugin's value→pixel math as a pure function and the additive schema fields (fixtures generated, not hand-written)

## v2 Requirements

Deferred. Tracked but not in current roadmap.

### WEB (deferred)

- **WEB-D01**: ±std column in leaderboard/task tables (charts-only per 2026-10-20 scoping)
- **WEB-D02**: CI-95 / IQR error-bar selector and asymmetric whisker styling (vendored plugin extension or the ratified sgratzl fallback)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| DDP / torch-run 实装 | Maintainer ruling 2026-10-20 (不做 DDP), re-affirming v1.2 D-04; the `WORLD_SIZE`/`LOCAL_RANK` seam stays documented-only |
| Cost-prediction load balancing | Maintainer rejected estimation (不做单一任务的负载); dynamic dispatch makes estimation unnecessary |
| Cloud / remote / multi-node orchestration | Single-box scope; no backend hosting constraint unchanged |
| Error-aware ranking (re-ranking by confidence bounds) | Display-only error bars — ranking math untouched (Core Value; zero-drift gate) |
| Full E2' three-seed re-run | Stays maintainer dual-gated; v1.3 validates the machinery with bounded runs |
| pynvml / NVML Python bindings | One read-only CSV probe doesn't justify an ABI-coupled dependency |
| New Chart.js CDN script by default | sgratzl plugin is ratified-fallback only; repo pins Chart.js 4.4.0 UMD today |
| Patching the DNALLM suite repo locally | Suite repo is read-only; upstream defects discovered during v1.3 get filed as upstream issues + documented workarounds here (maintainer 2026-10-20: 可以提 issue) |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MGPU-01 | TBD | Pending |
| MGPU-02 | TBD | Pending |
| MGPU-03 | TBD | Pending |
| MGPU-04 | TBD | Pending |
| MGPU-05 | TBD | Pending |
| MGPU-06 | TBD | Pending |
| VAL-01 | TBD | Pending |
| VAL-02 | TBD | Pending |
| VAL-03 | TBD | Pending |
| VAL-04 | TBD | Pending |
| TUI-01 | TBD | Pending |
| TUI-02 | TBD | Pending |
| TUI-03 | TBD | Pending |
| TUI-04 | TBD | Pending |
| WEB-01 | TBD | Pending |
| WEB-02 | TBD | Pending |
| WEB-03 | TBD | Pending |

**Coverage:**
- v1.3 requirements: 17 total
- Mapped to phases: 0
- Unmapped: 17 ⚠️ (filled by roadmap creation, next step)

---
*Requirements defined: 2026-10-20*
*Last updated: 2026-10-20 after initial definition (scoping: mode coexistence + charts-only error bars; DNALLM issue-channel constraint added same day)*
