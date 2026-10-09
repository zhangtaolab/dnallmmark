---
phase: 02-data-contracts-test-harness
verified: 2026-10-09T04:35:53Z
status: human_needed
score: 31/31 must-haves verified
covered_files: [".gitignore", ".planning/phases/02-data-contracts-test-harness/02-01-PLAN.md", ".planning/phases/02-data-contracts-test-harness/02-01-SUMMARY.md", ".planning/phases/02-data-contracts-test-harness/02-02-PLAN.md", ".planning/phases/02-data-contracts-test-harness/02-02-SUMMARY.md", ".planning/phases/02-data-contracts-test-harness/02-03-PLAN.md", ".planning/phases/02-data-contracts-test-harness/02-03-SUMMARY.md", "Makefile", "README.md", "pyproject.toml", "schemas/model_performance.json", "schemas/models_comparison.json", "schemas/task_performance.json", "schemas/tasks_index.json", "tests/conftest.py", "tests/fixtures/golden/models_comparison.json", "tests/fixtures/golden/models_comparison_animal.json", "tests/fixtures/golden/models_comparison_microbe.json", "tests/fixtures/golden/models_comparison_plant.json", "tests/fixtures/golden/tasks.json", "tests/fixtures/synthetic_models/fake-alpha_performance.json", "tests/fixtures/synthetic_models/fake-beta_performance.json", "tests/fixtures/synthetic_models/fake-gamma_performance.json", "tests/js/generate-tasks-index.test.js", "tests/test_aggregation.py", "tests/test_determinism.py", "tests/test_golden.py", "tests/test_known_defects.py", "tests/test_pivot.py", "tests/test_schemas.py", "uv.lock"]
covered_digest: "v3:sha256:34a1f6cd5693213c62f0a0f2ac7d2112145a7c6adb473b925e23ba754968c0bd"
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Confirm REL-04 probe-accounting disposition: plans 02-01's unclassified probe row for REL-04 was left without an authored truth beyond the zero-diff criterion (make data == committed tree byte-for-byte). A human should confirm no additional REL-04 edge criterion is required (e.g. exit-status semantics, partial-failure modes of the recipe lines)."
    expected: "Human accepts the zero-diff criterion as sufficient for REL-04's single-command guarantee, or names an additional defensible criterion for a follow-up plan."
    why_human: "The planner explicitly flagged this row 'for human review at phase verification' (02-01 probe_accounting) — it is a sufficiency judgment about spec-less probe coverage, not an observable codebase fact. All observable REL-04 behavior was verified programmatically (make data zero-diff, exit 0)."
  - test: "Confirm TEST-02 probe-accounting disposition: plan 02-02's unclassified probe row for TEST-02 was left without an authored truth beyond the approx/pinning criteria (pytest.approx on every float, OMP/OPENBLAS/MKL/NUMEXPR/VECLIB pinned to 1, pin asserted at test time). A human should confirm no additional stability criterion is required (e.g. repeated-run flake bounds beyond the single full-suite run performed)."
    expected: "Human accepts the approx + pinning + lane-segregation criteria as sufficient for TEST-02's stability-by-construction guarantee, or names an additional defensible criterion for a follow-up plan."
    why_human: "The planner explicitly flagged this row 'for human review at phase verification' (02-02 probe_accounting) — sufficiency judgment about spec-less probe coverage. The observable criteria all passed (thread-pin assertion in suite, approx used throughout, 132+133 item runs green, slow lane segregated)."
---

# Phase 2: Data Contracts & Test Harness Verification Report

**Phase Goal:** The data chain is guarded by executable contracts and a stable CPU-only test harness — schemas, unit tests, golden files, determinism regression, and a single-command Makefile — locked before any correctness fix moves the numbers
**Verified:** 2026-10-09T04:35:53Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

All 31 must-have truths (5 roadmap success criteria + 26 plan truths across 02-01/02-02/02-03) verified — every behavior-dependent truth has passing behavioral test evidence from this verification run. Two planner-flagged probe-accounting assumptions (sufficiency judgments, not codebase facts) route to human review, producing `human_needed` per the Step 9 tree.

### Observable Truths

Roadmap success criteria (the phase contract):

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| R1 | `make data` regenerates all derived files in one command from repo root; `make test` / `make lint` run the full local suite | ✓ VERIFIED | Behavioral: `make data` exit 0 with `git status --porcelain -- dnallm-mark/data/` EMPTY (zero-diff); `make test` exit 0 (133 passed + 5 xfailed pytest; node:test 2 pass); `make lint` exit 0 ("All checks passed!") |
| R2 | Unit tests over synthetic fixtures exercise rank/MinMax/z-score/robust aggregation and the pivot, CPU-only and passing; species bug captured as known-failing test | ✓ VERIFIED | `make test` green: test_aggregation.py (30 items incl. exact-tie ranks 1/1/3 scores 2/2/0, one-step boundary probe, constant/empty cases), test_pivot.py (3 items, chdir-driven); species bug = `test_producer_writes_dataset_species_not_model_organism` xfail(strict=True) — 5 xfailed confirmed, `--runxfail` probe shows it failing on the real `model_row` vs `row` assertion |
| R3 | Every committed leaderboard JSON validates against one of the four schemas | ✓ VERIFIED | 94 files counted on disk (42 model_performance + 47 task_performance + 4 models_comparison + 1 tasks.json); 94 parametrized items in the 132-passed run; injected-drift probes fail with additionalProperties (bogus info key) and enum (F1-casing) errors |
| R4 | Golden tests pass over synthetic tree; determinism regression re-runs chain expecting byte-identical output | ✓ VERIFIED | test_golden.py 3 items green via `from compare import walk` (zero diffs); `pytest -m slow` → 1 passed (0.57s): chain x2 byte-identical AND byte-identical to committed tree, trailing porcelain guard in test (tests/test_determinism.py:215-223) |
| R5 | Suite stable by construction — pytest.approx tolerances + thread pinning in conftest | ✓ VERIFIED | conftest.py pins all 5 env vars via setdefault before test-module imports; `test_thread_pinning_is_active_at_test_time` (tests/test_aggregation.py:309-313) asserts OMP/OPENBLAS/MKL == '1' at test time and passed; pytest.approx present and used throughout test_aggregation/test_pivot |

Plan 02-01 truths (9): 94-file zero-error validation ✓; fully-strict schemas (draft 2020-12, $id, additionalProperties:false at every level — read + probe-verified) ✓; closed enums + D-02 self-check (test_metric_enum_matches_committed_data green) ✓; missing-value anyOf convention (probe: numeric 0 passes; null, "0", "N/A" all fail; batch_size "" passes) ✓; empty-map-validates / missing-key-fails (probe: empty performance object and count-0 tasks.json validate; deleted `info` fails) ✓; key-order-insensitivity (probe: fully reversed key order validates) ✓; make data zero-diff ✓; uv lanes (`uv lock --check` exit 0; pytest/jsonschema/ruff resolve and run via `--group dev`) ✓; conftest 5-var pinning ✓.

Plan 02-02 truths (9): aggregation pure-function coverage ✓; exact-tie + constant-score zero-branch semantics (tests/test_aggregation.py:141-163 — rank 1/1/3, score 2/2/0, one-step-off 1/2/3) ✓; missing-metric presence gating (gamma excluded from ranking, samples reflects it; pivot keeps gamma with f1 == "" at tests/test_pivot.py:81-99) ✓; get_float boundary pinning (nan/inf/-inf pass-through as plain assertions — the WR-03 carrier) ✓; approx-everywhere + thread-pin assertion ✓; pivot under monkeypatch.chdir with verbatim info mirroring and `/`+`\` sanitization ✓; golden chain via compare.walk zero-diff ✓; node:test JS suite (2 pass: displayName collapse + defensive fallbacks; malformed-JSON [Skip]) ✓; make test runs pytest + node --test tests/js/ ✓.

Plan 02-03 truths (8): real-tree determinism (chain x2 + committed-equal, slow-marked) ✓; slow-lane segregation (`-m slow` → 1 passed; `-m "not slow"` → 1 deselected) ✓; AUD-01-P0 AST lock ✓; WR-02 comparator lock ✓; WR-03 parametrized lock (nan/inf/-inf) ✓; strict=True + finding-ID + "Phase 4 fix" in every reason (3 markers, lines 54/121/146) ✓; combined run green (make test: 133 passed + 5 xfailed, 0 failed) ✓; locks fail for the right reason (`--runxfail` → 5 FAILED on defect assertions, e.g. `assert -inf is None ... get_float('-inf', default=None)` — no import/collection errors) ✓.

**Score:** 31/31 truths verified (0 present, behavior-unverified)

### Required Artifacts

gsd-tools `verify.artifacts`: 02-01 → 11/11 passed; 02-02 → 8/8 passed; 02-03 → 2/2 passed. All 21 declared artifacts exist, are substantive (no "Only N lines"/"Missing pattern" issues), and are wired (imported and exercised by the green suite). No MISSING, STUB, or ORPHANED artifacts.

### Key Link Verification

gsd-tools `verify.key-links`: 02-01 → 4/4 verified; 02-02 → 4/5 (one PARTIAL); 02-03 → 4/4 verified.

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| tests/test_aggregation.py | script/summarize_comparison.py | pattern `import summarize_comparison` | ✓ WIRED (functional) | Tool reports PARTIAL (literal pattern not found) — the module actually uses `from summarize_comparison import (...)` (tests/test_aggregation.py:31), a direct import through conftest's sys.path root; proven functional by 30 passing items exercising get_float/calculate_dataset_stats/to_singular_species/aggregate_models. Literal-pattern artifact, not a wiring gap. |
| (all other 12 links) | | | ✓ WIRED | "Pattern found in source" — pyproject→uv.lock (jsonschema in both), Makefile→scripts (`cd $(DATA_DIR) && $(UV) run` present), test_schemas→schemas (iter_errors), conftest→script/+baseline/ (sys.path.insert), test_golden→baseline/compare.py (`from compare import walk`), test_golden→fixtures (monkeypatch.chdir), JS test→generator (copyFileSync), Makefile→tests/js (`node --test tests/js/`), determinism→model_performance/ (copytree), known-defects→pipeline (ast.parse, never import), known-defects→compare.py (`from compare import walk`), Makefile→determinism (`not slow`) |

### Data-Flow Trace (Level 4)

Not a data-rendering phase — but the chain contract holds: `make data` regenerates every derived file from `dnallm-mark/data/model_performance/` inputs through the real scripts (get_task_performance.py, summarize_comparison.py, generate-tasks-index.js per Makefile recipe) and the output equals the committed tree byte-for-byte (zero-diff proven). The determinism test independently proves the same data flow under subprocess isolation. ✓ FLOWING.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| make test-fast | `make test-fast` | 132 passed, 1 deselected, 5 xfailed, 0.76s, exit 0 | ✓ PASS |
| make test (full) | `make test` | 133 passed + 5 xfailed (pytest); node:test 2 pass 0 fail; exit 0 | ✓ PASS |
| make lint | `make lint` | "All checks passed!", exit 0 | ✓ PASS |
| make data zero-diff (REL-04) | `make data` then `git status --porcelain -- dnallm-mark/data/` | exit 0; porcelain output empty | ✓ PASS |
| uv lock sync | `~/.local/bin/uv lock --check` | "Resolved 69 packages in 1ms", exit 0 | ✓ PASS |
| Defect locks genuine (false-lock guard) | `pytest tests/test_known_defects.py --runxfail -q` | exit 1; 5 FAILED all on defect assertions (no import/collection errors) | ✓ PASS |
| Slow lane included | `pytest tests/test_determinism.py -m slow -q` | 1 passed in 0.57s | ✓ PASS |
| Slow lane excluded | `pytest tests/test_determinism.py -m "not slow" -q` | 1 deselected | ✓ PASS |
| Strictness: unknown key rejected | Draft202012Validator probe (bogus info key) | additionalProperties error | ✓ PASS |
| Strictness: enum casing rejected | tasks_index probe (metric "F1") | enum error | ✓ PASS |
| Missing-value convention | probes: 0 / batch_size "" pass; null, "0", "N/A" fail | all as specified | ✓ PASS |
| Empty-map + missing-key edges | probes: empty performance object, count-0 tasks.json validate; deleted info fails | all as specified | ✓ PASS |
| Key-order insensitivity | probe: fully reversed key order validates | validates | ✓ PASS |
| D-08 micro-fixes | `grep avg_PFLOPs README.md` (line 259); `grep -c '^\.planning/tmp/$' .gitignore` = 1; `git check-ignore .planning/tmp/` | all present | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` files exist or are declared by the plans. The plans' probe discipline is discharged through the behavioral spot-checks above (drift probes, --runxfail, lane segregation) — all executed in this verification, all PASS.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| REL-04 | 02-01 | Single-command data-regeneration chain replacing undocumented 3-step CWD-sensitive procedure | ✓ SATISFIED | `make data` from repo root, zero-diff proven behaviorally |
| TEST-01 | 02-02 | Unit tests for data-script pure functions (aggregation, pivot) + JS generator, synthetic fixtures, CPU-only | ✓ SATISFIED | 30 aggregation + 3 pivot items + 2 node:test items green; CPU-only (no torch/dnallm imports anywhere in tests/) |
| TEST-02 | 02-01, 02-02, 02-03 | Float-tolerance policy + thread pinning at scaffold time | ✓ SATISFIED | pytest.approx throughout; conftest pins 5 vars; pin asserted at test time; slow lane segregated |
| TEST-03 | 02-02, 02-03 | Golden-file tests over synthetic tree + determinism regression | ✓ SATISFIED | 5 golden files + walk()-compared zero-diff test; real-tree determinism 1 passed |
| TEST-06 | 02-01 | 4 JSON Schemas enforced over every committed JSON | ✓ SATISFIED | 94/94 files validate; drift probes fail; enum self-check green (CI activation is Phase 5 per REQUIREMENTS.md note) |

Orphaned requirements: NONE — REQUIREMENTS.md maps exactly REL-04, TEST-01, TEST-02, TEST-03, TEST-06 to Phase 2; the three plans claim exactly those five IDs.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | No TBD/FIXME/XXX, no placeholder/stub markers, no empty implementations in any of the 25 phase files | - | Clean |

Prohibitions (10 across 3 plans, descriptor-less): all verified observably —
1. No production code modified (pipeline/, script/, scripts/, baseline/, dnallm-mark/): `git diff 4fd682b..HEAD -- script/ scripts/ baseline/ pipeline/ dnallm-mark/` is EMPTY (covers all three plans).
2. Schemas never loosened: created this phase at maximal strictness; strictness probes live (additionalProperties + enum enforcement verified behaviorally).
3. Tests never write into committed data tree: porcelain over dnallm-mark/data/ empty after full `make test`; determinism test self-asserts it (tests/test_determinism.py:215-223).
4. Synthetic never substitutes for real in assertions: unit tests assert hand-computed literal expectations (e.g. ranks 1/1/3 from {0.9, 0.9, 0.8}); only the determinism test touches the real tree.
5. Goldens never hand-edited: observable consequence holds — test_golden.py proves goldens == chain output with zero diffs (FLOAT_ULP included); chain-provenance itself is process-only but its protective effect is fully verified.
6. No xfail without strict=True: suite-wide grep shows exactly 3 markers, all `@pytest.mark.xfail(strict=True,` (tests/test_known_defects.py:54,121,146); zero bare xfail.
7. Pipeline never imported: grep of test_known_defects.py shows no dnallmmark_pipeline import; AST-parsed as source (verified by the passing lock + --runxfail failing on the species assertion, not an ImportError).
8. No production change to make locks pass: same empty git diff as (1).

### Advisory Context (not gaps, per verification brief)

- Code review 02-REVIEW.md (0 critical / 5 warning / 4 info; disposition ledger 02-REVIEW-DISPOSITION.md: 9 open) is advisory — findings do not gate this phase. Note the review's finding IDs (WR-01..05, IN-01..04) are distinct from the Phase 1 audit's defect IDs (AUD-01-P0, WR-02, WR-03) despite ID collisions.
- Known-defect behaviors (AUD-01-P0 species-as-dataset, audit WR-02 comparator silence, audit WR-03 get_float non-finite) are intentionally locked xfail — Phase 4 fixes them; the locks are the deliverable here, verified genuine via --runxfail.
- IN-01/IN-02/WR-01 routing to later phases is recorded in the plans/summaries.

### Human Verification Required

Two planner-flagged probe-accounting assumptions — sufficiency judgments explicitly routed here by the plans' `probe_accounting` sections. No codebase fact is in question (everything observable was verified programmatically).

### 1. REL-04 unclassified probe row (plan 02-01)

**Test:** Confirm the zero-diff criterion (make data == committed tree byte-for-byte) is sufficient coverage for REL-04's single-command guarantee; name any additional defensible edge criterion if one exists (e.g. recipe-line partial-failure semantics).
**Expected:** Human accepts sufficiency, or names an additional criterion for a follow-up plan.
**Why human:** The planner wrote "no defensible extra criterion beyond the zero-diff truth already authored; flagged for human review at phase verification" — a spec-less-coverage judgment, not observable in code.

### 2. TEST-02 unclassified probe row (plan 02-02)

**Test:** Confirm the approx + thread-pinning + lane-segregation criteria are sufficient coverage for TEST-02's stability-by-construction guarantee; name any additional defensible criterion if one exists (e.g. multi-repeat flake bounds).
**Expected:** Human accepts sufficiency, or names an additional criterion for a follow-up plan.
**Why human:** The planner wrote "no additional defensible criterion beyond the authored approx/pinning truths; flagged for human review at phase verification" — same spec-less-coverage judgment.

### Gaps Summary

No gaps. All 31 truths verified with behavioral evidence; all 21 artifacts exist, substantive, wired; 13/13 key links wired (one literal-pattern PARTIAL resolved functional); all 5 requirements satisfied; no orphaned requirements; all 10 prohibitions hold observably; all 8 task commits valid; zero anti-pattern findings. The `human_needed` status comes solely from the two planner-flagged probe-accounting sufficiency judgments, which are sign-off items rather than defects.

---

_Verified: 2026-10-09T04:35:53Z_
_Verifier: Claude (gsd-verifier)_
