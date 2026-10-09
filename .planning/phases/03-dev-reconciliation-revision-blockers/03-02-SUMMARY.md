---
phase: 03-dev-reconciliation-revision-blockers
plan: "02"
subsystem: pipeline
tags: [registry-unification, D-10, dev-splits, F1, REV-01, refusal-guard, contract-test, tdd]

requires:
  - phase: 03-dev-reconciliation-revision-blockers
    provides: "03-01 merged tree: run_finetune.py + dual .txt/.json registries in-tree; D-03 pivoted AUD-01 lock on datasets_info Category"
  - phase: 02-data-contracts-test-harness
    provides: "test harness (conftest sys.path contract, xfail lock pattern, make test lanes)"
provides:
  - Single-source JSON registries (models 62 / datasets 50), both .txt retired, guarded by tests/test_registry_unification.py
  - run_finetune.py json read site (json.load + dict .items()) + REFUSED refusal guard before model load
  - script/make_dev_splits.py (deterministic stratified splitter, --check verifier) + 18 carved dev splits + registry Train/Dev on-disk counts
  - Two-layer EVAL-01 enforcement: suite-side opt-in test-eval contract + driver-side fail-fast + config purity
affects: [03-03 (PlantHelixSeek card removes one name from the card-absent enumeration; F2 edits land on the guarded run_finetune.py), 03-04 (ruff census baseline re-anchored at 16 unchanged findings; extends test_run_finetune_contracts.py), Phase 4 (card fields for the 18 txt-only models), Phase 5]

actuals:
  tokens: 42717   # 170866 diff chars / 4 over plan_head_before..HEAD; bulk = whole-file re-sorted registries (2,928+/1,090-)
  tasks: 3
  commits: 6      # measured: git rev-list --count 9e6d2cc..HEAD
plan_head_before: 9e6d2cc9e2eb8e6030d3f95c9e685a771eb5e761
plan_head_after: 883eafb1787e530a94bc4628f18e8db06a88ad1e

tech-stack:
  added: []       # numpy already in the data group; no new dependencies (stdlib csv + numpy only)
  patterns:
    - "TDD RED/GREEN per feature: failing tests against the intended API first (8c38723, 47fd10b), implementation to green (39146d2, a26c574)"
    - "Single-source registry contract test: git ls-files pathspec assertion + entry-count/field-completeness/card-absent-enumeration pins"
    - "Registry/disk count agreement verifier (--check): Train/Dev/Test counts vs on-disk CSV rows, unlocatable dirs WARNING-excluded"
    - "Source-contract tests over unimportable pipeline files: index-precedence assertions on read-as-text source (guard before model load)"

key-files:
  created:
    - tests/test_convert_registry.py
    - tests/test_registry_unification.py
    - tests/test_dev_splits.py
    - tests/test_run_finetune_contracts.py
    - script/make_dev_splits.py
  modified:
    - script/convert_registry.py        # --rename-name + --derive-operational + name-column-lands-as-field
    - pipeline/models_info.json         # unified: 44 -> 62 entries (sort_keys whole-file re-sort, expected)
    - pipeline/datasets_info.json       # unified 50 + Index/Category; later 18x Train/Dev + 5 count corrections
    - pipeline/run_finetune.py          # json read site + REFUSED guard
    - tests/test_known_defects.py       # D-03 Category source retargeted to the unified json
    - README.md                         # 3 stale .txt registry mentions retargeted to .json
  deleted:
    - pipeline/models_info.txt          # D-10 retirement (same commit as read site + D-03 retarget)
    - pipeline/datasets_info.txt

key-decisions:
  - "Name-column-lands-as-field: the converter's --to-json merge now writes the name cell (Model_name/Dataset_name) as a field on every merged entry — required for both key == name-field contracts and the dict read site (model_row[\"Model_name\"] would KeyError otherwise); pinned by test + pinned in the stock-merge suite"
  - "Registry counts are disk-authoritative: 5 pre-existing registry count defects corrected (4 Train + 4 Test header-inclusive counts on Deep4mC x3/iPro-WAEL; BEND Dev/Test transposed vs disk) — the plan's key_links contract (registry Train must equal on-disk rows or num_train_data math is wrong) fixes the direction"
  - "--check verifies Train/Dev/Test counts vs disk (the plan's 'registry counts vs on-disk CSV row counts' read on all count fields); 7 unlocatable GUE dirs (partial extraction, not double-nesting) WARNING-excluded per the documented E2E-gate deferral"
  - "REFUSED guard placed after the three selection filters, immediately before task-config mutation and the model load: it fires only for datasets that would actually run (a Dev-less registry entry cannot block an unrelated --target_dataset run) while still preceding load_model_and_tokenizer( and data_dict"
  - "make_dev_splits is header-driven (sequence,label AND name,sequence,label layouts both occur across the 18) and resolves Dataset_path pipeline-relative, exactly like run_finetune's base_dir + Dataset_path"

patterns-established:
  - "Converter-driven registry ingest with exact-count aborts (62/50 maintainer-verified arithmetic) — no inline conversion code anywhere"
  - "Count-guard-then-carve with deterministic re-runs: interrupted splits self-heal because the same seed regenerates identical bytes over the same original rows"

requirements-completed: [REV-01]

coverage:
  - id: D1
    description: "D-10 single-source unification: converter-driven .txt ingest into both .json registries (62 models / 50 datasets), .txt retirement, run_finetune.py json read site, D-03 Category retarget in the same commit"
    requirement: REV-01
    verification:
      - kind: unit
        ref: "pytest tests/test_convert_registry.py tests/test_registry_unification.py -q -> 12 passed"
        status: pass
      - kind: other
        ref: "test -z \"$(git ls-files -- 'pipeline/*.txt' 'pipeline/*.csv')\" -> NO_TABULAR_REGISTRIES"
        status: pass
      - kind: other
        ref: "python -c assert over both registries -> 'registries unified: 62 models / 50 datasets' (plan one-liner corrected: d.values() -> d.items() typo)"
        status: pass
      - kind: other
        ref: "grep -c read_table pipeline/run_finetune.py -> 0; py_compile -> COMPILES; ruff census 16 == 16 baseline (no new finding)"
        status: pass
      - kind: unit
        ref: "pytest tests/test_known_defects.py -q --runxfail -> exit 1, retargeted AUD-01 lock fails on the athaliana defect (non-vacuous), WR-02/WR-03 [nan][inf][-inf] present; normal mode 1 passed + 5 xfailed"
        status: pass
    human_judgment: false
  - id: D2
    description: "Converter D-10 extensions (--rename-name, --derive-operational) TDD'd: RED tests first, implementation to green, stock c3843d7 behavior pinned"
    requirement: REV-01
    verification:
      - kind: unit
        ref: "tests/test_convert_registry.py -> 9 passed (RED run first: 7 extension tests failed on planned assertions, 2 pins green)"
        status: pass
      - kind: other
        ref: "ruff check script/convert_registry.py tests/test_convert_registry.py -> clean"
        status: pass
    human_judgment: false
  - id: D3
    description: "script/make_dev_splits.py + tests: deterministic stratified carving (seed=42, max(1, n_c//10), rare-class policy, order preservation), count guard, idempotency, registry write discipline, --check verifier"
    requirement: REV-01
    verification:
      - kind: unit
        ref: "tests/test_dev_splits.py -> 13 passed (RED run first: 13/13 failed at the target API)"
        status: pass
      - kind: other
        ref: "real run: 18/18 split, 0 skipped, 0 failed; registry diff proven to touch exactly the 18 tasks' Train/Dev"
        status: pass
    human_judgment: false
  - id: D4
    description: "Executed splits + registry on-disk counts + REFUSED refusal guard before model load + config purity (allow_test_as_eval in neither YAML) + source-contract tests"
    requirement: REV-01
    verification:
      - kind: other
        ref: "make_dev_splits.py --check -> exit 0, 'OK: registry/disk agreement for 43 task(s)', 7 GUE dirs WARNING-excluded"
        status: pass
      - kind: other
        ref: "python -c assert -> 'json 50/50 Dev>0'; 18 dev.csv at Dataset_path locations (57 on disk; 14 extras in non-registry dirs)"
        status: pass
      - kind: unit
        ref: "pytest tests/test_run_finetune_contracts.py -> 2 passed (guard precedes load_model_and_tokenizer( and data_dict = {}; config purity)"
        status: pass
      - kind: unit
        ref: "make test -> 163 passed + 5 xfailed + node lane 2 pass"
        status: pass
    human_judgment: false

duration: 19 min
completed: 2026-10-10
status: complete
---

# Phase 03 Plan 02: D-10 Registry Unification, F1 Dev Splits, EVAL-01 Refusal Guard Summary

**Single-source JSON registries (62 models / 50 datasets) built by the extended converter with the .txt duals retired in the same commit as the json read site and the D-03 Category retarget; all 18 Dev-empty tasks carry deterministic stratified dev splits with the registry reconciled to disk; run_finetune.py hard-refuses Dev-less datasets before model load under the suite's EVAL-01 contract**

## Performance

- **Duration:** 19 min (execution; excludes planning)
- **Started:** 2026-10-09T16:36:28Z
- **Completed:** 2026-10-10 (UTC boundary crossed during execution)
- **Tasks:** 3/3 (Tasks 1 and 2 TDD: RED -> GREEN)
- **Commits:** 6 (2 RED test, 4 feat) — measured `git rev-list --count 9e6d2cc..HEAD`
- **Files:** 13 (5 created, 6 modified, 2 deleted)

## Accomplishments

- **Task 1 — D-10 unification (3 commits).** Converter extensions TDD'd first: RED `8c38723` (7 extension tests failing on planned assertions — KeyError on the fields to add, duplicate-key set mismatch, DID-NOT-RAISE — while the 2 stock-behavior pins stayed green), GREEN `39146d2` (`--rename-name` merge-key+cell rewrite with collision abort, `--derive-operational` card-to-operational derivation, name-column-lands-as-field). Unification executed through the converter `54b4413`: models `18 added + 38 merged + 6 derived = 62` (the maintainer-verified arithmetic, exact), datasets `0 added + 50 merged + 3 renamed = 50` (the 3 bare `gene_exp.*` names normalized to the `Source__task` form, zero duplicate keys). `run_finetune.py` read site flipped to `json.load` + dict `.items()` with every field key unchanged, orphaned pandas import removed, both argparse help strings updated; ruff census 16 findings before == 16 after (no new finding; D-08 population untouched for 03-04). Both `.txt` registries `git rm`'d in the SAME commit as the read-site change and the D-03 retarget (`_load_category_map` now reads Category from the unified json; lock proven non-vacuous under `--runxfail`, companion green). `tests/test_registry_unification.py` pins the single-source contract: no tabular registry tracked, 62/50 counts, operational completeness, card keys on exactly 44 entries with the card-absent set equal to the enumerated 18 txt-only names, key == name field everywhere, zero bare gene_exp keys.
- **Task 2 — split generator (2 commits).** RED `47fd10b` (13 tests + skeleton; all 13 fail at the target API), GREEN `a26c574`: `script/make_dev_splits.py` — `carve_stratified_dev` implements `max(1, n_c // 10)` for `n_c >= 2` (1-row classes stay in train), one `np.random.default_rng(42)` per task, classes in sorted label order, outputs preserve original row order (byte-stable); header-driven CSV handling covers both real layouts (`sequence,label` and `name,sequence,label`); count guard (SystemExit naming task + both numbers, zero writes); idempotent skip; Dev-registered-but-dev.csv-missing loud skip (never re-carves); malformed rows TaskSkip all-or-nothing; registry writes mirror the converter serialization exactly. stdlib csv + numpy only, repo-relative paths (REL-04), policy formula + Zenodo recovery note in the docstring.
- **Task 3 — executed splits + guard (1 commit, `883eafb`).** The generator carved all 18 Dev-empty tasks (seed=42; dev sizes 234-17083 rows, exactly the per-class formula), registry Train/Dev updated to on-disk counts with the diff proven to touch exactly the 18 tasks' Train/Dev. The REFUSED guard landed at the dataset-iteration top (after the selection filters, before task-config mutation and the model load): SystemExit naming the dataset, stating the suite's EVAL-01 contract (`dnallm/finetune/trainer.py` L568-605 @ 483a35c — test eval only when `finetune.allow_test_as_eval` is explicitly true, default False; hard ValueError on a missing eval split under `load_best_model_at_end`/early stopping), pointing to `script/make_dev_splits.py`. `tests/test_run_finetune_contracts.py` proves guard-precedes-`load_model_and_tokenizer(`-and-`data_dict` by source-index comparison (the open-paren match distinguishes the call from the module-top import) and config purity (`allow_test_as_eval` in neither YAML). `make_dev_splits.py --check` exits 0 with full Train/Dev/Test registry/disk agreement for all 43 locatable tasks.

## Task Commits

1. **Task 1 (RED):** converter extension tests — `8c38723` (test)
2. **Task 1 (GREEN):** `--rename-name` + `--derive-operational` — `39146d2` (feat)
3. **Task 1:** unification + read site + .txt retirement + D-03 retarget + contract test — `54b4413` (feat)
4. **Task 2 (RED):** split-generator tests + skeleton — `47fd10b` (test)
5. **Task 2 (GREEN):** split generator implementation — `a26c574` (feat)
6. **Task 3:** 18 splits + registry corrections + REFUSED guard + contract tests — `883eafb` (feat)

**Plan metadata:** this SUMMARY + STATE/ROADMAP/REQUIREMENTS commit (see below).

## Files Created/Modified

- `script/convert_registry.py` — D-10 extensions + name-column-lands-as-field merge contract
- `script/make_dev_splits.py` — NEW: stratified dev-split generator + `--check` verifier
- `tests/test_convert_registry.py` — NEW: 9 tests (extensions + stock pins)
- `tests/test_registry_unification.py` — NEW: 3 single-source contract tests
- `tests/test_dev_splits.py` — NEW: 13 behavior tests
- `tests/test_run_finetune_contracts.py` — NEW: 2 source-contract tests
- `pipeline/models_info.json` — unified 62-entry registry (sort_keys whole-file re-sort; 44 -> 62)
- `pipeline/datasets_info.json` — unified 50-entry registry + 18 Train/Dev updates + 5 count corrections
- `pipeline/run_finetune.py` — json read site + REFUSED guard (the only edits this plan; seed/grad_accum/head-config belong to 03-04)
- `tests/test_known_defects.py` — D-03 Category source retarget
- `README.md` — 3 registry mentions retargeted to .json
- `pipeline/models_info.txt`, `pipeline/datasets_info.txt` — DELETED
- `pipeline/datasets/**/dev.csv` + rewritten `train.csv` — 18 tasks, gitignored, regenerable

## Decisions Made

Recorded in frontmatter `key-decisions` (name-column contract, disk-authoritative counts, --check scope, guard placement, header-driven CSV handling).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Data defect] 4 registry Train counts included the CSV header line**
- **Found during:** Task 3 pre-run verification (A4 discharge)
- **Issue:** Deep4mC x3 + iPro-WAEL registry Train = `wc -l` of train.csv (data rows + header): 84927/84926, 126467/126466, 8682/8681, 7407/7406. The count guard correctly refused to carve.
- **Fix:** Pre-corrected the 4 Train values before the run (disk authoritative per the plan's key_links contract: counts must match on-disk rows or num_train_data math is wrong); the generator then passed the guard honestly for all 18.
- **Verification:** 4-line diff shown before carving; guard green post-correction
- **Committed in:** 883eafb

**2. [Rule 1 - Data defect] BEND__CpG_methylation registry Dev/Test transposed vs disk**
- **Found during:** Task 3 `--check` run (the first full registry/disk audit)
- **Issue:** registry Dev=106227/Test=109717, disk dev.csv=109717/test.csv=106227 — the dev-side registry author swapped the two counts.
- **Fix:** Corrected to the on-disk values (Dev 109717, Test 106227).
- **Verification:** `--check` agreement for BEND post-correction
- **Committed in:** 883eafb

**3. [Rule 1 - Data defect] 4 registry Test counts included the CSV header line**
- **Found during:** Task 3 full-registry count audit (prompted by finding 2)
- **Issue:** Same header-counting origin as finding 1, on the Test column (Deep4mC x3, iPro-WAEL: reg = disk + 1).
- **Fix:** Corrected the 4 Test values to on-disk counts.
- **Verification:** `--check` exit 0 across all 43 locatable tasks
- **Committed in:** 883eafb

**4. [Rule 2 - Verifier completeness] `--check` extended to verify Test counts**
- **Found during:** Task 3
- **Issue:** The plan's `--check` spec says "registry counts vs on-disk CSV row counts" (plural, general); the Train/Dev-only implementation would have silently passed the 4 stale Test counts (finding 3) that the audit exposed.
- **Fix:** `run_check` verifies Train/Dev/Test counts + dev.csv presence + dev/train header equality per locatable entry; unit test extended with a Test-mismatch case.
- **Files modified:** script/make_dev_splits.py, tests/test_dev_splits.py
- **Committed in:** 883eafb

**5. [Rule 3 - Blocking] make_dev_splits dataset-root path bug**
- **Found during:** Task 3 real run (first execution aborted)
- **Issue:** `DATASETS_ROOT = pipeline/datasets` double-prefixed the path — Dataset_path values already carry the `datasets/` prefix and resolve against `pipeline/` exactly as run_finetune.py does (`base_dir + Dataset_path`).
- **Fix:** `PIPELINE_ROOT = REPO_ROOT / "pipeline"`; docstring path contract corrected; tests unaffected (they inject roots).
- **Committed in:** 883eafb

**6. [Rule 3 - Documentation] README .txt registry references**
- **Found during:** Task 1
- **Issue:** README named `datasets_info.txt`/`models_info.txt` in 3 places (L171/L189/L192 — the 03-01 deviation had just retargeted them TO .txt for the then-current read site); deleting the files would leave the README naming nonexistent files.
- **Fix:** Retargeted to the .json registries in the retirement commit.
- **Committed in:** 54b4413

**7. [Plan-command fix] Task 1 verify one-liner typo**
- **Found during:** Task 1 verification
- **Issue:** The plan's assert one-liner reads `for k,e in d.values()` where it needs `d.items()` — the genexpr unpacks entry dicts and ValueErrors regardless of registry state.
- **Fix:** Ran the corrected assertion (`d.items()`); semantics unchanged, assertion passes. Documented here rather than editing the plan.

**8. [TDD mechanics] Task 2 RED commit includes a skeleton module**
- **Found during:** Task 2
- **Issue:** tests/test_dev_splits.py imports `make_dev_splits`, which did not exist — a test-only RED commit would fail at collection (invalid RED, zero tests discovered).
- **Fix:** The RED commit carries a NotImplementedError skeleton so all 13 tests collect and fail at the target API; behavior lands in the GREEN commit.

---

**Total deviations:** 8 auto-fixed (3 data defects corrected with disk as authority, 1 verifier extension, 1 path bug, 1 README truth fix, 1 plan-command typo, 1 TDD mechanics note)
**Impact on plan:** The registry-diff acceptance criterion ("ONLY the 18 tasks' Train/Dev values changing") holds for the split updates themselves but not literally across the whole diff — the 5 count corrections (findings 1-3) change Train/Dev/Test values on 5 additional pre-existing tasks. This is the plan's own verifier doing its job: the first full registry/disk audit exposed stale dev-side registry data, and the disk-authoritative direction is fixed by the plan's key_links contract. Every correction is enumerated above with before/after values. No review surface widened beyond registry count values; no behavioral code beyond the plan's named edits.

## Issues Encountered

None beyond the deviations above (all resolved in-flight).

## Authentication Gates

None — fully offline work. No model runs, no GPU work, no installs, no writes under /home/forrest/Github/DNALLM (read-only suite references only).

## User Setup Required

None.

## Known Stubs

None — no stub patterns introduced. (The 18 txt-only models' absent card fields are the plan's own flagged D-10 gap, explicitly enumerated in tests/test_registry_unification.py, not a stub.)

## Next Phase Readiness

- 03-03 (F2/PIPE-02 metadata) should remove PlantHelixSeek from the card-absent enumeration when D-09 fills its card (the test's error message names this exact maintenance step).
- 03-04's ruff baseline re-anchors here: 16 findings on run_finetune.py, unchanged by this plan's edits (read site + guard introduced none); D-08 fixes them all.
- 03-04 extends tests/test_run_finetune_contracts.py (the plan's artifacts note says so).
- The 7 unlocatable GUE dirs (partial extraction of GUE.zip — not double-nesting) are WARNING-excluded by `--check`; dataset-dir normalization stays deferred to the E2E gate per D-05.
- Registry correction follow-up for Phase 4 data regeneration: the leaderboard's committed dataset sub-dicts still carry pre-unification counts — expected divergence until data-v2, per the research note.

## Self-Check: PASSED

All 5 created files exist on disk; all 6 task commits (8c38723, 39146d2, 54b4413, 47fd10b, a26c574, 883eafb) verified as ancestors of HEAD; both .txt registries verified absent from git ls-files; TDD gate pattern present (test(03-02) RED + feat(03-02) GREEN for both TDD tasks).

---
*Phase: 03-dev-reconciliation-revision-blockers*
*Completed: 2026-10-10*
