---
phase: 02-data-contracts-test-harness
verified: 2026-10-09T05:30:10Z
status: passed
score: 31/31 must-haves verified
covered_files: [".gitignore", ".planning/phases/02-data-contracts-test-harness/02-01-PLAN.md", ".planning/phases/02-data-contracts-test-harness/02-01-SUMMARY.md", ".planning/phases/02-data-contracts-test-harness/02-02-PLAN.md", ".planning/phases/02-data-contracts-test-harness/02-02-SUMMARY.md", ".planning/phases/02-data-contracts-test-harness/02-03-PLAN.md", ".planning/phases/02-data-contracts-test-harness/02-03-SUMMARY.md", "Makefile", "README.md", "pyproject.toml", "schemas/model_performance.json", "schemas/models_comparison.json", "schemas/task_performance.json", "schemas/tasks_index.json", "tests/conftest.py", "tests/fixtures/golden/models_comparison.json", "tests/fixtures/golden/models_comparison_animal.json", "tests/fixtures/golden/models_comparison_microbe.json", "tests/fixtures/golden/models_comparison_plant.json", "tests/fixtures/golden/tasks.json", "tests/fixtures/synthetic_models/fake-alpha_performance.json", "tests/fixtures/synthetic_models/fake-beta_performance.json", "tests/fixtures/synthetic_models/fake-gamma_performance.json", "tests/js/generate-tasks-index.test.js", "tests/test_aggregation.py", "tests/test_determinism.py", "tests/test_golden.py", "tests/test_known_defects.py", "tests/test_pivot.py", "tests/test_schemas.py", "uv.lock"]
covered_digest: "v3:sha256:6e2ecef52cbeaa86aeb9dd8362a922fe4a3051a1df5ae789e5815846a017e4db"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 31/31
  gaps_closed:
    - "Prior report went STALE (not failed): review-fix rounds 1 (106ad13..b99a02d: WR-01..05, IN-02, IN-04) and 2 (86fdc8a..e642600: WR-06, WR-07, IN-05) changed covered files after it was written — all fix-round changes re-verified against the current tree in this run"
    - "REL-04 probe-accounting sufficiency — CONFIRMED PASS by maintainer in 02-UAT.md (2/2, session complete)"
    - "TEST-02 probe-accounting sufficiency — CONFIRMED PASS by maintainer in 02-UAT.md (2/2, session complete)"
  gaps_remaining: []
  regressions: []
---

# Phase 2: Data Contracts & Test Harness Verification Report

**Phase Goal:** The data chain is guarded by executable contracts and a stable CPU-only test harness — schemas, unit tests, golden files, determinism regression, and a single-command Makefile — locked before any correctness fix moves the numbers
**Verified:** 2026-10-09T05:30:10Z
**Status:** passed
**Re-verification:** Yes — final re-verification after two review-fix rounds made the prior (31/31, human_needed) report stale; both prior human items are settled by 02-UAT.md

## Goal Achievement

All 31 must-have truths (5 roadmap success criteria + 26 plan truths across 02-01/02-02/02-03) verified against the CURRENT tree, every behavior-dependent truth with behavioral evidence executed in this verification run. The two prior probe-accounting sufficiency items were confirmed PASS by the maintainer in 02-UAT.md (2/2 passed, session complete) and are not re-raised; no new un-verifiable judgments surfaced from the fix rounds. Suite is now 136 passed + 5 xfailed (pytest) + 2 passed (node:test).

### Observable Truths

Roadmap success criteria (the phase contract):

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| R1 | `make data` regenerates all derived files in one command from repo root; `make test` / `make lint` run the full local suite | ✓ VERIFIED | Behavioral: `make data` exit 0 with `git status --porcelain -- dnallm-mark/data/` EMPTY (zero-diff); `make test` exit 0 (136 passed + 5 xfailed pytest; node:test 2 pass 0 fail); `make lint` exit 0 ("All checks passed!") |
| R2 | Unit tests over synthetic fixtures exercise rank/MinMax/z-score/robust aggregation and the pivot, CPU-only and passing; species bug captured as known-failing test | ✓ VERIFIED | `make test` green: test_aggregation.py 30 items (exact-tie ranks 1/1/3 scores 2/2/0, one-step boundary 1/2/3, constant/empty cases), test_pivot.py 3 items chdir-driven; species bug = `test_producer_writes_dataset_species_not_model_organism` xfail(strict=True) — 5 xfailed confirmed, `--runxfail` probe (exit 1) shows 5 FAILED on defect assertions (model_row vs row, walk silence, non-finite get_float), no import/collection errors |
| R3 | Every committed leaderboard JSON validates against one of the four schemas | ✓ VERIFIED | 94 files counted on disk (42 model_performance + 47 task_performance + 4 models_comparison + 1 tasks.json); 94 parametrized items inside the 136-passed run; WR-03-review bucket-count canary (tests/test_schemas.py:100-127) pins 42/47/4/1 so a vanished glob fails loudly; injected-drift probes re-run this session: bogus info key → additionalProperties error, F1-casing → enum error |
| R4 | Golden tests pass over synthetic tree; determinism regression re-runs chain expecting byte-identical output | ✓ VERIFIED | test_golden.py 3 items green via `from compare import walk` (zero diffs, FLOAT_ULP included); `pytest -m slow` → 1 passed (0.57s): chain x2 byte-identical AND byte-identical to committed tree; WR-04 hardening present (tests/test_determinism.py:125-130 stale-output removal per run + :177-202 file-set exactness) |
| R5 | Suite stable by construction — pytest.approx tolerances + thread pinning in conftest | ✓ VERIFIED | conftest.py pins all 5 env vars at module top (now FORCE-assigned per WR-05 fix, tests/conftest.py:28-35); `test_thread_pinning_is_active_at_test_time` asserts '1' at test time and passed; pytest.approx present (19 usages test_aggregation, 4 test_pivot); hostile-env spot-check this session: `OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 pytest tests/test_aggregation.py` → 30 passed (the WR-05 force-assign fix proven live) |

Plan 02-01 truths (9): 94-file zero-error validation ✓ (bucket canary green); fully-strict schemas (draft 2020-12, $id, additionalProperties:false at every level — probe-verified P1) ✓; closed enums + D-02 self-check (metric/species/type closed enums; original metric self-check plus the IN-02-widened cross-schema enum check `test_dataset_enums_match_committed_data_across_all_schemas` green, incl. the models_comparison open-string boundary assert) ✓; missing-value anyOf convention (probe P3: numeric 0 passes; null, "0", "N/A" all fail; batch_size "" passes) ✓; empty-map-validates / missing-key-fails (probe P4) ✓; key-order-insensitivity (probe P5: fully reversed key order validates) ✓; make data zero-diff ✓; uv lanes (`uv lock --check` exit 0 "Resolved 69 packages"; test/test-fast/lint all run through `uv run --group dev`; pytest/jsonschema/ruff resolve and run) ✓ — note UV is now `UV ?= uv` (WR-02 review fix: PATH lookup with overridable default instead of hardcoded `~/.local/bin/uv`), the "no activation step through uv" contract unchanged; conftest 5-var pinning ✓ — mechanism changed from setdefault to force-assign (WR-05 review fix, strictly stronger: overrides hostile preset envs), still module-top before any test-module numpy import.

Plan 02-02 truths (9): aggregation pure-function coverage (get_float, calculate_dataset_stats x4 methods, to_singular_species, aggregate_models + pivot via main() under chdir) ✓; exact-tie + constant-score zero-branch semantics ✓ (tie 1/1/3 → 2/2/0; one-step 1/2/3; constant-guard case on binary-exact 0.5 with 0.7 companion per the recorded plan-correction deviation); missing-metric presence gating (gamma excluded from ranking, samples reflects it; pivot keeps gamma with f1 == "") ✓; get_float boundary pinning (nan/inf/-inf pass-through as plain assertions — WR-03 carrier) ✓; approx-everywhere + thread-pin assertion ✓; pivot under monkeypatch.chdir with verbatim info mirroring and `/`+`\` sanitization ✓; golden chain via compare.walk zero-diff ✓; node:test JS suite (2 pass: displayName collapse + defensive fallbacks; malformed-JSON [Skip]) ✓; make test runs pytest + node --test tests/js/ ✓ (exit 0, both lanes observed).

Plan 02-03 truths (8): real-tree determinism (chain x2 + committed-equal, slow-marked, 1 passed) ✓; slow-lane segregation (`-m slow` → 1 passed; `-m "not slow"` → 1 deselected) ✓; AUD-01-P0 AST lock ✓ (xfail green; --runxfail fails on the model_row-vs-row assertion; WR-01 unmarked companion `test_aud01_construction_site_anchor_is_findable_and_unique` + IN-05 species-key-presence assert both present and green — the honest-failure guard now lives OUTSIDE the marker where it can actually fail, per WR-01 fix); WR-02 comparator lock ✓ (walk(True,1,...) silent → xfail; runxfail fails on the diffs assertion); WR-03 parametrized lock ✓ (nan/inf/-inf; runxfail fails on `assert -inf is None ... get_float('-inf', default=None)`); strict=True + finding-ID + "Phase 4 fix" in every reason ✓ (3 markers at tests/test_known_defects.py:130/181/206, zero bare xfail suite-wide); combined run green ✓ (make test: 136 passed + 5 xfailed, 0 failed); locks fail for the right reason ✓ (--runxfail: 5 FAILED all on defect assertions, 1 passed companion, no import/collection errors; pipeline imported nowhere — only comments reference the path, AST-parsed as source).

**Score:** 31/31 truths verified (0 present, behavior-unverified)

### Sanctioned Deviations from Plan-Literal Wording (review-fix rounds, all disposition: fixed)

These change plan-literal mechanisms but preserve or strengthen each truth's observable outcome; all verified in the current tree:

| Change | Review finding | Truth impact |
|--------|---------------|--------------|
| conftest `setdefault` → force-assign `os.environ[_var] = "1"` | WR-05 | Pinning truth holds and is strictly stronger (hostile OMP=4 preset run green this session) |
| Makefile `~/.local/bin/uv` → `UV ?= uv` | WR-02 | uv-lane truth unchanged in substance (still `uv run --group dev`, no activation step; overridable) |
| AUD-01 honesty guard: `pytest.fail` inside lock → unmarked companion outside the marker (+ IN-05 species-key-presence) | WR-01, IN-05 | False-lock truth strengthened — anchor loss/key-loss now fails red outside the xfail swallow |
| `check-node` guard on `test` and `data` targets; `test_golden.py` module-level skipif without node; truthful message | IN-04, WR-06, WR-07 | make-test truth strengthened on node-less machines (this machine has node: 0 skips observed) |
| Bucket-count canary (42/47/4/1 pinned) in test_schemas.py | WR-03 (review) | 94-file validation truth strengthened against vacuous-glob shrink |
| Cross-schema enum self-check widened to species/type/metric x 3 schemas | IN-02 | D-02 truth strengthened — enum copies across schema files cannot drift apart |

### Required Artifacts

gsd-tools `verify.artifacts`: 02-01 → 11/11 passed; 02-02 → 8/8 passed; 02-03 → 2/2 passed (exit 0, all_passed each). All 21 declared artifacts exist, are substantive (no "Only N lines"/"Missing pattern" issues), and are wired (imported and exercised by the green suite). No MISSING, STUB, or ORPHANED artifacts.

### Key Link Verification

gsd-tools `verify.key-links`: 02-01 → 4/4 verified; 02-02 → 4/5 (one PARTIAL); 02-03 → 4/4 verified.

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| tests/test_aggregation.py | script/summarize_comparison.py | pattern `import summarize_comparison` | ✓ WIRED (functional) | Tool reports PARTIAL (literal pattern not found) — the module actually uses `from summarize_comparison import (...)` (tests/test_aggregation.py:31), a direct import through conftest's sys.path root; proven functional by 30 passing items exercising get_float/calculate_dataset_stats/to_singular_species/aggregate_models. Literal-pattern artifact, not a wiring gap. |
| (all other 12 links) | | | ✓ WIRED | "Pattern found in source" — pyproject→uv.lock (jsonschema in both), Makefile→scripts (`cd $(DATA_DIR) && $(UV) run` present), test_schemas→schemas (iter_errors), conftest→script/+baseline/ (sys.path.insert), test_golden→baseline/compare.py (`from compare import walk`), test_golden→fixtures (monkeypatch.chdir), JS test→generator (copyFileSync), Makefile→tests/js (`node --test tests/js/`), determinism→model_performance/ (copytree), known-defects→pipeline (ast.parse, never import), known-defects→compare.py (`from compare import walk`), Makefile→determinism (`not slow`) |

### Data-Flow Trace (Level 4)

Not a data-rendering phase — but the chain contract holds: `make data` regenerates every derived file from `dnallm-mark/data/model_performance/` inputs through the real scripts (get_task_performance.py, summarize_comparison.py, generate-tasks-index.js per Makefile recipe) and the output equals the committed tree byte-for-byte (porcelain empty after this session's run). The determinism test independently proves the same data flow under subprocess isolation with per-run output cleanup (WR-04). ✓ FLOWING.

### Behavioral Spot-Checks

All executed this session against the current tree:

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| make test (full, both lanes) | `make test` | 136 passed + 5 xfailed (pytest, 1.37s); node:test 2 pass 0 fail; exit 0 | ✓ PASS |
| make test-fast | `make test-fast` | 135 passed, 1 deselected, 5 xfailed, 0.78s, exit 0 | ✓ PASS |
| make lint | `make lint` | "All checks passed!", exit 0 | ✓ PASS |
| make data zero-diff (REL-04) | `make data` then porcelain over dnallm-mark/data/ | exit 0; 0 porcelain lines | ✓ PASS |
| uv lock sync | `uv lock --check` | "Resolved 69 packages in 0.61ms", exit 0 | ✓ PASS |
| Defect locks genuine (false-lock guard) | `pytest tests/test_known_defects.py --runxfail -q` | exit 1; 5 FAILED on defect assertions; 1 passed (unmarked companion, correct); no import/collection errors | ✓ PASS |
| Slow lane included | `pytest tests/test_determinism.py -m slow -q` | 1 passed in 0.57s | ✓ PASS |
| Slow lane excluded | `pytest tests/test_determinism.py -m "not slow" -q` | 1 deselected | ✓ PASS |
| Strictness: unknown key rejected | Draft202012Validator probe (bogus info key) | additionalProperties error | ✓ PASS |
| Strictness: enum casing rejected | tasks_index probe (metric "F1") | enum error | ✓ PASS |
| Missing-value convention | probes: 0 / batch_size "" pass; null, "0", "N/A" fail | all as specified | ✓ PASS |
| Empty-map + missing-key edges | probes: empty performance object validates; deleted info fails | as specified | ✓ PASS |
| Key-order insensitivity | probe: fully reversed key order validates | validates | ✓ PASS |
| WR-05 hostile-env pin override | `OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 pytest tests/test_aggregation.py -q` | 30 passed (force-assign overrides preset) | ✓ PASS |
| D-08 micro-fixes | `grep avg_PFLOPs README.md` (line 259); `.gitignore` line 101 `.planning/tmp/` | both present | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` files exist or are declared by the plans. The plans' probe discipline is discharged through the behavioral spot-checks above (drift probes, --runxfail, lane segregation, hostile-env pin) — all executed in this verification, all PASS.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| REL-04 | 02-01 | Single-command data-regeneration chain replacing undocumented 3-step CWD-sensitive procedure | ✓ SATISFIED | `make data` from repo root, zero-diff proven behaviorally; check-node guard makes node-less failure actionable (WR-07 fix) |
| TEST-01 | 02-02 | Unit tests for data-script pure functions (aggregation, pivot) + JS generator, synthetic fixtures, CPU-only | ✓ SATISFIED | 30 aggregation + 3 pivot items + 2 node:test items green; CPU-only (no torch/dnallm imports anywhere in tests/) |
| TEST-02 | 02-01, 02-02, 02-03 | Float-tolerance policy + thread pinning at scaffold time | ✓ SATISFIED | pytest.approx throughout; conftest force-pins 5 vars (WR-05); pin asserted at test time; hostile-env run green; slow lane segregated |
| TEST-03 | 02-02, 02-03 | Golden-file tests over synthetic tree + determinism regression | ✓ SATISFIED | 5 golden files + walk()-compared zero-diff test; real-tree determinism 1 passed; WR-04 flake-masking fix in place |
| TEST-06 | 02-01 | 4 JSON Schemas enforced over every committed JSON | ✓ SATISFIED | 94/94 files validate; drift probes fail; bucket-count canary; enum self-checks (metric + IN-02 cross-schema) green (CI activation is Phase 5 per REQUIREMENTS.md note) |

Orphaned requirements: NONE — REQUIREMENTS.md maps exactly REL-04, TEST-01, TEST-02, TEST-03, TEST-06 to Phase 2; the three plans claim exactly those five IDs.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | No TBD/FIXME/XXX, no TODO/HACK/PLACEHOLDER, no placeholder phrasing, no empty returns in any of the 24 phase implementation files | - | Clean |

### Prohibitions (10 across 3 plans) — all hold observably

1. No production code modified (pipeline/, script/, scripts/, baseline/, dnallm-mark/): `git diff 4fd682b..HEAD -- script/ scripts/ baseline/ pipeline/ dnallm-mark/` is EMPTY, and working tree clean over those dirs — holds across both fix rounds too (fix commits touched only tests/, Makefile, planning docs).
2. Schemas never loosened: strictness probes live (additionalProperties + enum enforcement verified behaviorally this session).
3. Tests never write into committed data tree: porcelain over dnallm-mark/data/ empty after full `make test` AND after `make data`; determinism test self-asserts it (tests/test_determinism.py:226-235).
4. Synthetic never substitutes for real in assertions: unit tests assert hand-computed literal expectations; only the determinism test touches the real tree.
5. Goldens never hand-edited: test_golden.py proves goldens == chain output with zero diffs (FLOAT_ULP included).
6. No xfail without strict=True: suite-wide grep shows exactly 3 markers, all `@pytest.mark.xfail(strict=True,`; zero bare xfail.
7. Pipeline never imported: no actual import statement referencing dnallmmark_pipeline in test_known_defects.py (only comments/docstrings name the path); AST-parsed as source — proven by the passing lock + --runxfail failing on the species assertion, not an ImportError.
8. No production change to make locks pass: same empty git diff as (1).

### Review Disposition Context (advisory, not gaps)

- 02-REVIEW.md (convergence review): clean, 0 findings. Disposition ledger 02-REVIEW-DISPOSITION.md: 12 rows = 10 fixed + 2 deferred (IN-01 generator fallback enum tension; IN-03 METRIC_KEY_MAP manual mirror), both deferred to Phase 4/5 under the D-04 production-change prohibition with rationale recorded in 02-REVIEW-FIX.md — recorded dispositions, not open work.
- Known-defect behaviors (AUD-01-P0 species-as-dataset, WR-02 comparator silence, WR-03 get_float non-finite) are intentionally locked xfail — Phase 4 fixes them; the locks are the deliverable here, verified genuine via --runxfail.
- Prior human_verification items (REL-04 and TEST-02 probe-accounting sufficiency): CONFIRMED PASS by maintainer in 02-UAT.md (2/2 passed, session complete, updated 2026-10-09T05:01:33Z) — settled, not re-raised; no new un-verifiable judgments found in the fix-round changes.

### Human Verification Required

None. All observable behavior was verified programmatically in this run; the two prior sufficiency judgments are maintainer-settled (02-UAT.md).

### Gaps Summary

No gaps. All 31 truths verified with behavioral evidence from the current tree; all 21 artifacts exist, substantive, wired; 13/13 key links wired (one literal-pattern PARTIAL resolved functional); all 5 requirements satisfied; no orphaned requirements; all 10 prohibitions hold observably across the phase commits AND both fix rounds; all 11 task/fix commits valid; zero anti-pattern findings; fingerprint covers all 31 changed implementation/planning files (all paths verified on disk). Phase goal achieved: the data chain is guarded by executable contracts and a stable CPU-only test harness, locked before any correctness fix moves the numbers.

---

_Verified: 2026-10-09T05:30:10Z_
_Verifier: Claude (gsd-verifier)_
