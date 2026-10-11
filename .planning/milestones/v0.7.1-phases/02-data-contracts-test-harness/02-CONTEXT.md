# Phase 2: Data Contracts & Test Harness - Context

**Gathered:** 2026-10-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Executable contracts over the data chain plus a stable CPU-only test harness, locked BEFORE any correctness fix moves a number: four JSON Schemas (model_performance, task_performance, models_comparison, tasks_index), unit tests over the data-script pure functions, golden-file tests, a determinism regression, and a single-command Makefile (`make data` / `make test` / `make lint`). CI wiring (TEST-04/05/07) and post-fix recomputation (DATA-*) are Phase 5 — this phase builds the contracts and tests that CI will later enforce. No correctness-fix code changes land here except the two zero-risk micro-fixes itemized in D-08; behavior-changing fixes stay test-first (xfail) until Phase 4.

</domain>

<decisions>
## Implementation Decisions

### Schema strictness
- **D-01:** All four schemas are FULLY STRICT — `additionalProperties: false` plus every field required. Any shape drift fails validation; adding a field anywhere requires a schema change first (forced versioning, reviewer-friendly). — **Reversibility:** costly — once published, loosening a strict schema breaks the contract's meaning for every consumer that started relying on drift-detection; tightening later is cheap but loosening reads as a regression.
- **D-02:** `metric` / primary-metric fields use a CLOSED ENUM of metric names extracted from the current 50 datasets (f1, accuracy, mcc, auprc, …). New datasets with new metrics require a schema update; typos fail immediately. Self-check: a unit test asserts the enum ≡ the set of metric values actually present in committed data, so enum and data cannot silently diverge.

### Known-failing test mechanism
- **D-03:** The species-as-dataset bug (AUD-01-P0) is captured as `xfail(strict=True)`: the test asserts the CORRECT behavior (a dataset entry's `species` must be the arena category Animals/Plants/Microbe, never the model's organism). Today it fails → xfail. `strict=True` means an unexpected XPASS fails the suite, forcing the Phase 4 fixer to explicitly remove the marker and confirm the fix — a fix can never land silently. The same mechanism is used for WR-02/WR-03 (D-07).

### Advisory-findings disposition (from Phase 1 review)
- **D-04:** WR-02 (compare.py treats equal-value bool/int cross-type pairs as identical — live risk over the 47 pinned files carrying bf16/fp16 booleans) and WR-03 (non-finite metric values pass the presence gate and NaN-poison a whole task's normalization) become xfail(strict) tests THIS phase — defect semantics locked test-first, fixed in Phase 4. No production-code change in Phase 2.
- **D-05:** Routing of the remaining five: WR-01 (gitleaks allowlist is record-scoped, not token-scoped) → Phase 5, fix when CI wires gitleaks (pin the token's header+payload prefix in the allowlist regex); IN-01 (compare.py labels pure-int diffs FLOAT_BIG) → Phase 4, when the comparator is next modified; IN-02 (index generator raw-crashes on missing task_performance/ dir) → milestone backlog.
- **D-06:** These dispositions are recorded in the phase 01 disposition ledger; the planner should treat D-04/D-05 as scope input, not re-derive routing.
- **D-07:** (folded into D-03/D-04 — species bug + WR-02 + WR-03 all use xfail(strict=True).)
- **D-08:** Two zero-risk micro-fixes land in-phase alongside the harness (no code semantics, no numbers touched): IN-03 — README "Output fields" list gains `avg_PFLOPs`; IN-04 — `.gitignore` gains `.planning/tmp/`.

### Test data surface
- **D-09:** Golden-file tests run over a SYNTHETIC fixture tree (hand-crafted minimal model set, ~3-5 fake models × several datasets, engineered to cover exact ties, missing/empty metric values, boundary shapes) — fast, stable, decoupled from real-data drift. — **Reversibility:** reversible.
- **D-10:** The determinism regression runs over the REAL committed tree: run the full chain twice, assert byte-identical outputs, and assert regeneration == committed tree (the zero-diff check behaviorally proven during Phase 1 UAT). ~40s per chain run; local-run acceptable, CI wiring deferred to Phase 5 TEST-07. — **Reversibility:** reversible.

### Claude's Discretion
- Schemas live in `schemas/` (four files, JSON Schema draft 2020-12, with `$id`).
- Tests live in `tests/` (pytest); pytest config and the dev dependency group go into the existing `pyproject.toml` (PEP 735 group, consistent with the Phase 1 substrate).
- `make data` / `make test` / `make lint` invoke through `uv run` (no activation step), replacing the CWD-sensitive 3-step procedure (REL-04). `make data` must work from repo root.
- The JS index generator gets a minimal `node:test` unit suite (it is part of the data chain; the real-tree determinism test also exercises it end-to-end).
- Thread pinning (`OMP/OPENBLAS/MKL_NUM_THREADS=1`) and `pytest.approx` tolerances live in `conftest.py` per TEST-02.
- xfail markers carry the finding ID in the reason string (e.g. `reason="AUD-01-P0 species-as-dataset — Phase 4 fix"`).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 1 baseline & contracts (this phase builds on them)
- `baseline/PIN-VALIDATION.md` — D-05/D-06 pin-validation evidence; the diff-inventory vocabulary (FLOAT_ULP / FLOAT_BIG / exact-tie) the new tests must be consistent with
- `baseline/compare.py` — the order-insensitive comparator and its `--summary-json` machine contract; WR-02/IN-01 target file
- `AUDIT.md` — findings AUD-01..AUD-24; AUD-01 (species-as-dataset) is the xfail test's subject; severity rubric P0/P1/P2
- `.planning/phases/01-audit-release-foundations/01-REVIEW-DISPOSITION.md` — the 7 open advisory findings and their D-04/D-05 routing
- `.planning/phases/01-audit-release-foundations/01-CONTEXT.md` — D-05..D-10 decisions (env pins, D-06 differences-investigated standard, token visibility)

### Data contracts source of truth
- `script/summarize_comparison.py` — aggregation math under test (rank/MinMax/z-score/robust), `metric_key_map` at :295-305; WR-03 target file
- `script/get_task_performance.py` — model→task pivot logic under test
- `scripts/generate-tasks-index.js` — index generator; IN-02 target (backlog)
- `dnallm-mark/data/model_performance/` (42 files), `dnallm-mark/data/task_performance/` (47), `dnallm-mark/data/models_comparison*.json` (4), `dnallm-mark/data/tasks.json` — the real committed instances the four schemas must validate
- `pipeline/dnallmmark_pipeline.py:1195-1265` — the producer-side output contract the model_performance schema encodes

### Requirements
- `.planning/REQUIREMENTS.md` — REL-04, TEST-01, TEST-02, TEST-03, TEST-06 (Phase 2 scope); TEST-04/05/07 + DATA-01/02/06 explicitly Phase 5

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `baseline/compare.py` — canonical JSON value comparator with diff-class vocabulary; the golden/determinism tests should REUSE it rather than re-implement comparison
- `pyproject.toml` + `uv.lock` + `.python-version` (3.13) — the Phase 1 substrate; add the test/dev group here, no new dependency manifests
- `.venv` (uv-managed, pandas 2.3.3 / numpy 2.5.3) — the run environment `make` targets invoke via `uv run`
- Phase 1 UAT session's manual regeneration procedure (this session, 2026-10-09) — the behavioral precedent D-10 automates: chain run from `dnallm-mark/data/` with venv python, `git status` zero-diff assertion

### Established Patterns
- Data scripts are CWD-sensitive today (`run from dnallm-mark/data/`); D-11's `make data` must encapsulate that, not rewrite the scripts' path resolution (surgical-fix discipline)
- Missing metric values are empty strings `""`, never null/0 — synthetic fixtures and schema `type` choices must encode this
- Exact-tie groups exist (six documented in AUDIT.md's migration record); synthetic fixtures should include a tie pair so rank-ordering logic is covered deterministically

### Integration Points
- `make data` wraps the three-script chain (get_task_performance → summarize_comparison → generate-tasks-index)
- Schema validation runs over every committed JSON in the suite (TEST-06's local form; CI enforcement is Phase 5)
- The species xfail test imports/asserts against `pipeline/dnallmmark_pipeline.py`'s output contract OR a captured fixture of producer output — planner decides the least-coupled form

</code_context>

<specifics>
## Specific Ideas

- Maintainer's consistent preference across this discussion: maximum strictness for contracts (all-strict schemas, closed enums) — when the planner faces a strictness trade-off not covered by an explicit decision, err strict.
- The xfail(strict=True) pattern is the house style for known defects: defect semantics locked as failing tests, fixes forced to remove markers explicitly.

</specifics>

<deferred>
## Deferred Ideas

- WR-01 gitleaks token-prefix pinning — Phase 5 (with CI gitleaks wiring)
- IN-01 comparator diff-label accuracy (pure-int → FLOAT_BIG) — Phase 4 (next comparator modification)
- IN-02 index-generator missing-dir crash robustness — milestone backlog
- CI enforcement of schemas/determinism (TEST-04/05/07), post-fix recomputation + changelog (DATA-01/02/06) — Phase 5

</deferred>

---

*Phase: 2-Data Contracts & Test Harness*
*Context gathered: 2026-10-09*
