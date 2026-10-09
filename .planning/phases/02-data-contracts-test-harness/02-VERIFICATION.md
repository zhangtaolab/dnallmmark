---
phase: 02-data-contracts-test-harness
verified: 2026-10-09T21:03:35Z
status: passed
score: 31/31 must-haves verified
covered_files: [".gitignore", ".planning/phases/02-data-contracts-test-harness/02-01-PLAN.md", ".planning/phases/02-data-contracts-test-harness/02-01-SUMMARY.md", ".planning/phases/02-data-contracts-test-harness/02-02-PLAN.md", ".planning/phases/02-data-contracts-test-harness/02-02-SUMMARY.md", ".planning/phases/02-data-contracts-test-harness/02-03-PLAN.md", ".planning/phases/02-data-contracts-test-harness/02-03-SUMMARY.md", "Makefile", "README.md", "pipeline/datasets_info.json", "pyproject.toml", "schemas/model_performance.json", "schemas/models_comparison.json", "schemas/task_performance.json", "schemas/tasks_index.json", "tests/conftest.py", "tests/fixtures/export_chain/defect_species_performance.json", "tests/fixtures/golden/models_comparison.json", "tests/fixtures/golden/models_comparison_animal.json", "tests/fixtures/golden/models_comparison_microbe.json", "tests/fixtures/golden/models_comparison_plant.json", "tests/fixtures/golden/tasks.json", "tests/fixtures/synthetic_models/fake-alpha_performance.json", "tests/fixtures/synthetic_models/fake-beta_performance.json", "tests/fixtures/synthetic_models/fake-gamma_performance.json", "tests/js/generate-tasks-index.test.js", "tests/test_aggregation.py", "tests/test_determinism.py", "tests/test_golden.py", "tests/test_known_defects.py", "tests/test_pivot.py", "tests/test_schemas.py", "uv.lock"]
covered_digest: "v3:sha256:3913fea90f0f6af7809e5dfc4337482a2dfe34621d1520778ac1d3c9e31581e0"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 31/31
  gaps_closed:
    - "STALE-REFRESH, not a failure: the prior report (2026-10-09T05:30:10Z, 31/31 passed) went stale after Phase 3 changed files in its covered set (dev-branch merge 41bf49e, D-10 registry unification to JSON with .txt retirement, deprecated-pipeline banner, README rewrite, pyproject [pipeline]->[gpu] + ty wiring, Makefile typecheck/lint widening, new Phase-3 tests, D-03 pivot of the AUD-01 lock) — every must-have re-verified against the CURRENT tree at HEAD 28ba056 in this run; fresh fingerprint computed"
  gaps_remaining: []
  regressions: []
---

# Phase 2: Data Contracts & Test Harness Verification Report

**Phase Goal:** The data chain is guarded by executable contracts and a stable CPU-only test harness — schemas, unit tests, golden files, determinism regression, and a single-command Makefile — locked before any correctness fix moves the numbers
**Verified:** 2026-10-09T21:03:35Z
**Status:** passed
**Re-verification:** Yes — STALE-REFRESH re-verification: prior report passed 31/31 but its fingerprint went stale after Phase 3 (dev-branch merge, registry unification, D-03 lock pivot, toolchain wiring) changed files in its covered set. Every must-have re-proven at HEAD `28ba056` on `autorun`; suite now 193 passed + 5 xfailed (pytest) + 2 passed (node lane).

## Goal Achievement

All 31 must-have truths (5 roadmap success criteria + 26 plan truths across 02-01/02-02/02-03) re-verified against the CURRENT tree at HEAD `28ba056`, every behavior-dependent truth re-proven with behavioral evidence executed in this verification run. Two shape-supersessions from Phase 3 are recorded below with decision IDs — superseded-by-design, never failed: the AUD-01 lock's anchoring mechanism (D-03) and its Category-source registry format (D-10 interlock). No Phase-2 truth asserted `.txt` registry presence (grep over all three plans: zero `.txt` references), so the D-10 unification superseded no Phase-2 truth directly — only the lock's internal Category source, which was retargeted in the same commit as the `.txt` retirement and is verified live here.

### Superseded-by-Design (recorded with decision IDs — not gaps, not failures)

| Superseded surface | Decision | What replaced it | Current-tree evidence (this run) |
|--------------------|----------|------------------|----------------------------------|
| 02-03 truth 3's plan-literal lock SHAPE: AUD-01-P0 locked "via an AST source-contract check of pipeline/dnallmmark_pipeline.py"; 02-03 key link `test_known_defects.py -> pipeline/dnallmmark_pipeline.py via ast.parse` | **D-03** (Phase 3 Wave 1, with F10 deprecation + D-10 interlock) | Export-chain contract: `test_aud01_species_matches_dataset_arena_category` asserts every dataset entry's `species` equals the dataset's `Category` in the unified `pipeline/datasets_info.json`, over the repo-authored fixture `tests/fixtures/export_chain/defect_species_performance.json`; unmarked companion `test_aud01_contract_fixture_has_expected_shape` keeps the lock honest (WR-01 discipline); pipeline modules still never imported (JSON/text reads only) | Lock present with `xfail(strict=True)` (tests/test_known_defects.py:134); `--runxfail` exit 1 with the lock FAILING on the defect entry — `plant-genomic-benchmark__poly_a.arabidopsis_thaliana: dataset.species 'athaliana' is a model organism, not an arena category` — non-vacuous; companion passes unmarked; module docstring documents the D-03 pivot |
| The lock's Category source: retired `pipeline/datasets_info.txt` | **D-10** (Phase 3 registry unification, same-commit interlock with D-03) | `_load_category_map()` reads Category from the unified `pipeline/datasets_info.json` (50 entries) | Join verified live — the lock resolves every fixture dataset name to a Category row and fails on the value comparison (not on a broken join); companion asserts the join keys hold |

The truth's core intent — species-as-dataset bug captured as a known-failing test with strict semantics that a Phase 4 fix must turn green — HOLDS in the current tree in the pivoted shape; only the anchoring mechanism is superseded (score counts it VERIFIED with the supersession recorded).

**Info note (honest-verifier observation, not a flag):** the fixture is the sole carrier of the defect instance — the union of `dataset.species` values across all 42 committed real files is exactly `{Animals, Microbe, Plants}` (no `athaliana` in the production tree). This is the declared D-03 contract shape: the lock pins the export contract for future producers, the companion guards fixture integrity, and Phase 4's fix commit must update the fixture and remove the marker together (house rule documented in the module docstring and pinned by the companion's red-on-shape-loss behavior).

### Observable Truths

Roadmap success criteria (the phase contract):

| # | Truth | Status | Evidence (re-proven this run at HEAD 28ba056) |
|---|-------|--------|----------|
| R1 | `make data` regenerates all derived files in one command from repo root; `make test` / `make lint` run the full local suite | ✓ VERIFIED | Behavioral: `make data` exit 0 with `git status --porcelain -- dnallm-mark/data/` EMPTY (0 lines) — also proves Phase 3 held the data tree byte-identical post-merge; `make test` exit 0 (193 passed + 5 xfailed pytest; node:test 2 pass 0 fail); `make lint` exit 0 ("All checks passed!"); `make typecheck` (Phase-3 additive) also exit 0 |
| R2 | Unit tests over synthetic fixtures exercise rank/MinMax/z-score/robust aggregation and the pivot, CPU-only and passing; species bug captured as known-failing test | ✓ VERIFIED | `make test` green: test_aggregation.py + test_pivot.py items green within the 193; species bug = `test_aud01_species_matches_dataset_arena_category` xfail(strict=True) in pivoted D-03 shape — 5 xfailed confirmed; `--runxfail` probe: 5 FAILED on defect assertions (species lock on the athaliana entry, walk silence, non-finite get_float nan/inf/-inf), 1 passed (companion), no import/collection errors; zero torch/dnallm imports anywhere in tests/ (grep 0) |
| R3 | Every committed leaderboard JSON validates against one of the four schemas | ✓ VERIFIED | 94 files counted on disk (42 model_performance + 47 task_performance + 4 models_comparison + 1 tasks.json); verifier-run Draft202012Validator probe this session: 94/94 valid, 0 invalid; bucket-count canary (tests/test_schemas.py:101 pins 42/47/4/1) green inside the 193 |
| R4 | Golden tests pass over synthetic tree; determinism regression re-runs chain expecting byte-identical output | ✓ VERIFIED | test_golden.py green via `from compare import walk` (line 36) within the 193; `pytest -m slow` this session: 1 passed in 1.02s (chain x2 byte-identical AND byte-identical to committed tree); `-m "not slow"`: 1 deselected; porcelain over data tree 0 after the run |
| R5 | Suite stable by construction — pytest.approx tolerances + thread pinning in conftest | ✓ VERIFIED | conftest.py:29-36 force-assigns all 5 env vars at module top (WR-05 form; Phase 3's edit added only an additive `pipeline/` sys.path entry — pinning untouched); pin-assertion test green within the 193; hostile-env spot-check this session: `OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 pytest tests/test_aggregation.py` → 30 passed |

Plan 02-01 truths (9): 94-file zero-error validation ✓ (corpus probe 94/94 + canary green); fully-strict schemas (draft 2020-12, additionalProperties:false — probe P1a unknown-key REJECTED with validator=additionalProperties) ✓; closed enums + D-02 self-check (metric [f1, mcc, spearmanr, AUPRC], species [Animals, Plants, Microbe], type [binary, multiclass, regression, multilabel] — all three literal enums confirmed in schema source; `test_metric_enum_matches_committed_data` + IN-02 cross-schema `test_dataset_enums_match_committed_data_across_all_schemas` green in suite) ✓; missing-value anyOf convention (probe P3: numeric 0 VALIDATES; null REJECTED; "N/A" REJECTED) ✓; empty-map-validates / missing-key-fails (probe P4: empty performance object VALIDATES; deleted info REJECTED) ✓; key-order-insensitivity (probe P5: fully reversed key order VALIDATES) ✓; make data zero-diff ✓; uv lanes (`uv lock --check` exit 0, 71 packages resolved — grew from 69 with Phase 3's additive [gpu]/ty resolution; pytest/jsonschema/ruff all resolved in uv.lock; test/test-fast/lint run through `uv run --group dev`) ✓; conftest 5-var force-assign pinning at module top ✓.

Plan 02-02 truths (9): aggregation pure-function coverage (get_float, calculate_dataset_stats x4, to_singular_species, aggregate_models, pivot via main() under chdir — all green in suite) ✓; exact-tie + constant-score zero-branch semantics ✓; missing-metric presence gating ✓; get_float boundary pinning ✓; approx-everywhere + thread-pin assertion ✓; pivot under monkeypatch.chdir with info mirroring + sanitization ✓; golden chain via compare.walk zero-diff ✓; node:test JS suite (2 pass: displayName collapse + defensive fallbacks; malformed-JSON [Skip] — observed in this run's make test output) ✓; make test runs pytest + node --test tests/js/ ✓ (both lanes observed this run).

Plan 02-03 truths (8): real-tree determinism (chain x2 + committed-equal, slow-marked, 1 passed this run) ✓; slow-lane segregation (`-m slow` → 1 passed; `-m "not slow"` → 1 deselected; make test-fast → 192 passed + 1 deselected + 5 xfailed) ✓; AUD-01 lock ✓ VERIFIED **shape superseded by-design D-03** (export-chain contract, strict, non-vacuous — see Superseded table; plan-literal AST mechanism retired with F10 in the same commit, per Phase-3 verification truth 3); WR-02 comparator lock ✓ (walk(True,1,...) silent → xfail; runxfail fails on the diffs assertion); WR-03 parametrized lock ✓ (nan/inf/-inf; runxfail fails on `assert -inf is None ... get_float('-inf', default=None)` — observed verbatim this run); strict=True + finding-ID + "Phase 4 fix" in every reason ✓ (exactly 3 markers at tests/test_known_defects.py:134/167/192, all `strict=True`; zero bare xfail suite-wide); combined run green ✓ (make test: 193 passed + 5 xfailed, 0 failed); locks fail for the right reason ✓ (--runxfail: 5 FAILED all on defect assertions, 1 passed companion, no import/collection errors; pipeline imported nowhere — test_known_defects reads JSON/text only).

**Score:** 31/31 truths verified (0 present, behavior-unverified; 1 verified in D-03-superseded shape)

### Advisory (New Scope, Unevidenced)

Re-verification ran; no unevidenced new-scope findings.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| — | None | — | — |

### Required Artifacts

gsd-tools `verify.artifacts`: 02-01 → 11/11 passed (all_passed: true); 02-02 → 8/8 passed; 02-03 → 2/2 passed. All 21 declared artifacts exist, substantive (zero "Only N lines"/"Missing pattern" issues), and wired (exercised by the green 193-test suite). No MISSING, STUB, or ORPHANED artifacts. The pivoted lock's fixture (`tests/fixtures/export_chain/defect_species_performance.json`, 1687 bytes) is a Phase-3 addition inside a Phase-2 artifact's dependency set — present, substantive, and load-bearing (verified by the live join).

### Key Link Verification

gsd-tools `verify.key-links`: 02-01 → 4/4 verified; 02-02 → 4/5 (one literal-pattern PARTIAL); 02-03 → 3/4 (one SUPERSEDED by D-03).

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| tests/test_known_defects.py | pipeline/dnallmmark_pipeline.py | `ast.parse` | ◆ SUPERSEDED (D-03) | Plan-literal link retired with the F10 deprecation + D-03 pivot — tool reports "ast.parse not found" as expected. Replacement wiring VERIFIED in current tree: `_load_category_map()` joins `pipeline/datasets_info.json` (json.load, tests/test_known_defects.py:89-91) + the export-chain fixture (lines 70-73, 94-96); both live-proven by this run's --runxfail probe. Recorded superseded, not failed. |
| tests/test_aggregation.py | script/summarize_comparison.py | `import summarize_comparison` | ✓ WIRED (functional) | Tool reports PARTIAL (literal pattern miss) — module actually uses `from summarize_comparison import (...)` (tests/test_aggregation.py:31) through conftest's sys.path root; functional, proven by green items. Literal-pattern artifact, unchanged since the prior verification. |
| (all other 11 links) | | | ✓ WIRED | "Pattern found in source" — pyproject→uv.lock, Makefile→scripts, test_schemas→schemas, conftest→script/+baseline/, test_golden→compare.py, test_golden→fixtures, JS test→generator, Makefile→tests/js, determinism→model_performance/, known-defects→compare.py, Makefile→determinism. Phase 3's conftest edit added `pipeline/` as a THIRD sys.path root (additive; the script/+baseline/ contract intact). |

### Data-Flow Trace (Level 4)

`make data` this run regenerated every derived file from `dnallm-mark/data/model_performance/` through the real scripts (Makefile recipe: get_task_performance.py, summarize_comparison.py via `cd $(DATA_DIR) && $(UV) run --group data python`, then `node scripts/generate-tasks-index.js`) and output equals the committed tree byte-for-byte (porcelain 0) — the strongest cheap proof that Phase 3's merge held the data tree byte-identical. Bucket counts 42/47/4/1 re-counted on disk. Determinism test independently proves the same flow under subprocess isolation. ✓ FLOWING.

### Behavioral Spot-Checks

All executed this session at HEAD 28ba056:

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| make test (full, both lanes) | `make test` | 193 passed + 5 xfailed (pytest, 2.28s); node:test 2 pass 0 fail; exit 0 | ✓ PASS |
| make test-fast | `make test-fast` | 192 passed, 1 deselected, 5 xfailed, 1.15s, exit 0 | ✓ PASS |
| make lint | `make lint` | "All checks passed!", exit 0 | ✓ PASS |
| make typecheck (Phase-3 additive) | `make typecheck` | "All checks passed!", exit 0 | ✓ PASS |
| make data zero-diff (REL-04) | `make data` + porcelain over dnallm-mark/data/ | exit 0; 0 porcelain lines | ✓ PASS |
| uv lock sync | `uv lock --check` | "Resolved 71 packages in 1ms", exit 0 | ✓ PASS |
| Defect locks genuine (false-lock guard) | `pytest tests/test_known_defects.py --runxfail -q` | exit 1; 5 FAILED on defect assertions; 1 passed (companion); no import/collection errors | ✓ PASS |
| Species lock non-vacuity (D-03 pivot) | `pytest ...::test_aud01_species_matches_dataset_arena_category --runxfail -q` | exit 1; fails on `athaliana` defect entry: "dataset.species 'athaliana' is a model organism, not an arena category" | ✓ PASS |
| Slow lane included | `pytest tests/test_determinism.py -m slow -q` | 1 passed in 1.02s | ✓ PASS |
| Slow lane excluded | `pytest tests/test_determinism.py -m "not slow" -q` | 1 deselected | ✓ PASS |
| Full-corpus schema validation | verifier Draft202012Validator probe | 94/94 files valid, 0 invalid | ✓ PASS |
| Strictness: unknown key rejected | probe P1a (bogus info key) | REJECTED, validator=additionalProperties | ✓ PASS |
| Strictness: enum casing rejected | probe P2 (metric "F1" in tasks.json) | REJECTED (enum) | ✓ PASS |
| Missing-value convention | probes P3: 0 VALIDATES; null REJECTED; "N/A" REJECTED | as specified | ✓ PASS |
| Empty-map + missing-key edges | probes P4: empty performance VALIDATES; deleted info REJECTED | as specified | ✓ PASS |
| Key-order insensitivity | probe P5: fully reversed key order | VALIDATES | ✓ PASS |
| D-02 closed enums literal | schema source probe | metric/species/type enums exactly as pinned | ✓ PASS |
| WR-05 hostile-env pin override | `OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 pytest tests/test_aggregation.py -q` | 30 passed (force-assign overrides preset) | ✓ PASS |
| D-08 micro-fixes survive README rewrite | `grep avg_PFLOPs README.md` (line 285); `.gitignore` line 101 `.planning/tmp/` | both present | ✓ PASS |
| Bucket counts on disk | ls counts | 42 / 47 / 4 / 1 | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` files exist or are declared. The plans' probe discipline is discharged through the behavioral spot-checks above (schema drift probes, --runxfail, lane segregation, hostile-env pin, make-data zero-diff) — all executed in this verification, all PASS.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| REL-04 | 02-01 | Single-command data-regeneration chain | ✓ SATISFIED | `make data` zero-diff re-proven at HEAD 28ba056 |
| TEST-01 | 02-02 | Unit tests for pure functions + JS generator, synthetic fixtures, CPU-only | ✓ SATISFIED | aggregation/pivot/JS items green within 193; zero torch/dnallm imports in tests/ |
| TEST-02 | 02-01, 02-02, 02-03 | Float-tolerance policy + thread pinning at scaffold time | ✓ SATISFIED | approx throughout; conftest force-pins 5 vars (survived Phase 3's conftest edit); hostile-env run green; lanes segregated |
| TEST-03 | 02-02, 02-03 | Golden-file tests + determinism regression | ✓ SATISFIED | golden tests green in 193; slow determinism 1 passed this run |
| TEST-06 | 02-01 | 4 JSON Schemas enforced over every committed JSON | ✓ SATISFIED | 94/94 corpus probe valid; drift probes fail; canary + enum self-checks green (CI activation remains Phase 5 per REQUIREMENTS.md note) |

Orphaned requirements: NONE. REQUIREMENTS.md maps exactly REL-04, TEST-01, TEST-02, TEST-03, TEST-06 to Phase 2 — precisely the five IDs the three plans claim. Cross-check note on the verification directive's broader ID list: DATA-04/DATA-05/DATA-06 and TEST-04/TEST-05 are mapped by REQUIREMENTS.md to Phases 6/5 and Phase 5 respectively — later-phase scope (deferred there by design), never Phase 2 requirements; no orphans either way.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | Zero TBD/FIXME/XXX (blocker tier) and zero TODO/HACK/PLACEHOLDER across all 26 covered implementation files + pipeline/datasets_info.json | - | Clean |

### Prohibitions (10 across 3 plans) — all hold in the current tree

1. Production code never modified to make tests pass (phase-execution rule): historical range re-confirmed — `git diff 4fd682b..e642600 -- script/ scripts/ baseline/ pipeline/ dnallm-mark/` is EMPTY (e642600 = last Phase-2 commit). Phase 3's subsequent production changes are separate sanctioned phase work (D-05/D-08/D-10), not Phase-2 violations.
2. Schemas never loosened: strictness probes live (additionalProperties + enum enforcement re-verified behaviorally this run).
3. Tests never write into committed data tree: porcelain over dnallm-mark/data/ = 0 after full `make test`, after `make data`, and after the determinism lane.
4. Synthetic never substitutes for real in assertions: unit tests assert hand-computed expectations; only the determinism test touches the real tree.
5. Goldens never hand-edited: golden tests green in the 193 prove goldens == chain output.
6. No xfail without strict=True: exactly 3 markers (tests/test_known_defects.py:134/167/192), all `strict=True`; zero bare xfail suite-wide.
7. Pipeline never imported: zero `import`/`from` of dnallmmark_pipeline (and run_finetune) in tests/; zero torch/dnallm imports; the D-03-pivoted lock reads JSON/text only — proven by the lock failing on the species assertion, not an ImportError.
8. No production change to make locks pass: same empty historical diff; current gates green without any lock accommodation.

### Human Verification Required

None. All observable behavior re-verified programmatically in this run. The two prior sufficiency judgments (REL-04, TEST-02) remain maintainer-settled in 02-UAT.md (2/2 passed, session complete, 2026-10-09T05:01:33Z) — not re-raised; no new un-verifiable judgments surfaced by the Phase-3 changes.

### Gaps Summary

No gaps. All 31 truths re-verified with fresh behavioral evidence at HEAD 28ba056 — the suite now at 193 passed + 5 xfailed + node lane 2 (Phase 3's 57 additive tests on top of the Phase-2 corpus, zero Phase-2 tests removed or weakened); bucket counts 42/47/4/1 hold on disk and the data tree regenerates byte-identical, proving the merge held it unchanged; the metric closed-enumeration self-check, golden dual-run determinism, and WR-02/WR-03 xfail locks are live; `make test`/`test-fast`/`lint` still gate with `typecheck` as a Phase-3 additive; both Phase-3 shape-supersessions (D-03 lock pivot, D-10 Category-source retarget) are recorded above with decision IDs and their replacements verified live and non-vacuous. Fresh fingerprint computed over the current covered set. Phase goal achieved and stable under the Phase-3 tree.

---

_Verified: 2026-10-09T21:03:35Z_
_Verifier: Claude (gsd-verifier)_
