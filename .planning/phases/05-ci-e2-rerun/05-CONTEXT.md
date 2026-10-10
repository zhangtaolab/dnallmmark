# Phase 5: CI & Three-Seed Full Re-Run (E2') - Context

**Gathered:** 2026-10-10 (autonomous smart discuss, maintainer accepted all 4 areas)
**Status:** Ready for planning

<domain>
## Phase Boundary

Aggregation upgrade (F6: CI-overlap tie rules, dual views, permutation tests) lands BEFORE E2' numbers are published; CI golden tests (F9: canned-replay smoke + key parity + species spot checks + aggregation units — CPU, <15 min, PR-required, badge); N-frequency audit + unified eval subsets (F7); E2' three-seed full re-run executes via the sweep runner per the pre-decided authorization framework (ROADMAP Phase 5 decisions-carried block) — the CODE lands this phase, the E2' LAUNCH is a maintainer-pulled trigger (dual gate: DNALLM stable + PIPE-02 env smoke), never automatic; data-v2 migration gate (DATA-01/02/03/06) with changelogged tagged migration after E2'.

</domain>

<decisions>
## Implementation Decisions

### CI golden tests (REV-06/F9)
- **Q1:** Smoke = CANNED GOLDEN REPLAY: committed micro run_record + checkpoint artifacts; CI runs export→aggregate→schema full-chain assertions over them. No real training in CI (dnallm/GPU prohibited by CI feasibility constraint).
- **Q2:** The other three test classes (metric-key parity, species-table spot checks, aggregation units) reuse the existing pytest suite via a `ci` marker lane.
- **Q3:** Platform: GitHub Actions ubuntu runner, PR-required, README badge.
- **Q4:** Hard <15-minute budget (current suite ~8s + node ~8s — ample headroom for the chain replay).

### Aggregation upgrade (REV-04/F6)
- **Q1:** CI intervals use the SAME SOURCE as the vendored `aggregate_seeds` (n<3 → t-interval 95%, n≥3 → bootstrap 2000, seed=42) — one statistical vocabulary everywhere.
- **Q2:** Difficulty weight v1 = uniform (1/num_tasks) z-score weighting — no hand-tuned difficulty table.
- **Q3:** Permutation tests: 10,000 shuffles, BH-corrected (FDR 0.05), pairwise model comparisons (scipy.stats or equivalent).
- **Q4:** Public leaderboard DEFAULT VIEW switches to z-score×difficulty-weighted; raw-rank stays one click away. (Public-facing number change — maintainer-accepted.)

### N audit + eval subsets (REV-07/F7)
- **Q1:** Unified eval N = min(per-model current sample count) per task, integer — all models evaluate identical sample counts (fairness directly provable).
- **Q2:** N/non-ACGT frequency tables published as DATA.md appendix + downloadable CSV/JSON artifact (47 tasks × train/dev/test).
- **Q3:** Pipeline interface: run_finetune accepts `--subset_file` (JSON task→ID list); absent = full evaluation.

### data-v2 migration gate (DATA-01/02/03/06)
- **Q1:** Same gate shape as data-v1: E2' completes → pre-generated categorized diff inventory → MAINTAINER SIGN-OFF → data-v2 tag + SHA256 manifest. Never auto-tagged.
- **Q2:** CHANGELOG.md with per-version sections: date + data_version + change-category counts + link to the diff inventory.
- **Q3:** Before/after comparison-JSON snapshots both archived (pre-E2' current + post-E2' new).

### E2' execution (pre-decided — ROADMAP carries the full framework)
- Dual gate (DNALLM stable release + PIPE-02 env smoke on GB10) + EXPLICIT maintainer authorization; failure recovery = sweep failure-manifest re-run; window degradation = priority order (E2E pair → arena representatives → rest) with honest n_seeds; scope = ALL 62 unified-registry models.

### Planning-time decisions (2026-10-10, maintainer answers during Phase 5 research review)
- **D-16:** The E2' data-chain bridge = Option C: `export_runs.py` emits BOTH views from run records (task-centric `task_performance/` + per-model `model_performance/{alias}_performance.json`). One emitter, one reader per view; both the leaderboard chain and the submit/finetuning per-model contract stay live; the CI golden replay covers the chain end-to-end (export→both views→aggregate→schema).
- **D-17:** Research OQ package accepted: OQ2 `dnallm-mark/data/manifest.json` carries data_version + generated-from commit (footer reads it, replacing the live clock at js/main.js:367); OQ3 pre-E2' F6 regeneration = CHANGELOG entry + version bump only, git tag reserved for data-v2; OQ4 degradation tier-1 = the PIPE-03 E2E pair, tier-2 = maintainer-curated via checkpoint:human-verify at execution (never agent-invented); OQ5 permutation tests = pairwise on the aggregate view (score-vector permutation across tasks; C(42,2)=861 pre-E2' → C(62,2)=1891 post-E2' family, BH-disclosed; optional per-task spot checks); OQ6 data-v2 inventory = thin orchestrator looping `baseline/compare.py --summary-json` (comparator untouched); OQ7 replay depth = end-to-end per D-16.
- **D-18:** `plant-dnamamba2-BPE` alias normalization rides the bridge work: one key per model; the committed results file's alias aligns to the unified registry key (investigate the case-variant set-diff at execution; key==name contract governs).
- **F6 statistical semantics (binding, corrects the CONTEXT Q1 parenthetical):** the vendored `aggregate_seeds` is the SINGLE statistical source — its actual thresholds govern (n<3 → ci95 null/method "none"; 3≤n<10 → t-interval; n≥10 → bootstrap). E2' 3-seed data gets t-intervals (df=2), never bootstrap. Implement by calling the vendored function/constants.

### Claude's Discretion
None — all sixteen grey-area answers were maintainer-accepted recommendations.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `script/export_runs.py` (vendored aggregate_seeds, 28-name mapping, dual output — the aggregation upgrade builds ON this)
- `pipeline/run_sweep.py` (the E2' driver: --dry-run verified; failure manifest, priority ordering to add)
- Existing pytest suite (232 tests; `ci` marker lane to define) + node lane (8)
- `baseline/compare.py` diff vocabulary; data-v1 tag/manifest tooling as the data-v2 template

### Established Patterns
- Canned-golden replay mirrors the Phase-2 golden/determinism discipline
- Sign-off-then-tag mirrors the data-v1 gate
- CHANGELOG + categorized inventory mirrors the Phase-1 migration gate

### Integration Points
- `js/main.js` view toggle (weighted default); `dnallm-mark/data/models_comparison*.json` shape extension (per-view fields)
- `.github/workflows/ci.yml` (new); Makefile `ci` lane marker
- `pipeline/run_finetune.py --subset_file`; N-audit script reading datasets_info + on-disk CSVs

</code_context>

<specifics>
## Specific Ideas

- Maintainer preferences (consistent): maximum strictness, evidence-first, honest deferrals.
- The F6 landing BEFORE E2' publication is ordering-critical (ROADMAP SC-1).

</specifics>

<deferred>
## Deferred Ideas

- E2' LAUNCH itself — behind the dual gate + maintainer trigger (this phase lands its tooling and the pipeline readiness).
- IA³ lane — suite-support-gated, Phase 6 priority list.

</deferred>
