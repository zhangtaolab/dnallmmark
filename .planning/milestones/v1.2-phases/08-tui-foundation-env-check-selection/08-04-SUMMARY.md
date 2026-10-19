---
phase: 08-tui-foundation-env-check-selection
plan: 04
subsystem: tui/services (env/registry services layer)
tags: [tui, services, xdg, env-check, env-gate, quick-check, registries, n-audit, d-04, d-05, d-08, d-09, d-10, env-02, env-03, env-04, sel-04]
requires:
  phase: []
provides: []
provides:
  - "tui.services.settings — state_dir()/config_dir() (D-04 XDG split via platformdirs, whole-dir env overrides DNALLMMARK_TUI_STATE_DIR/_CONFIG_DIR, empty value = unset) + atomic_write (tmp + os.replace, parents on demand)"
  - "tui.services.env_check — load_cached (artifact_loader None sentinel), is_same_local_day (LOCAL calendar basis, Pitfall 8), persist (schema_version 1 + checked_at local naive + checked_at_iso UTC + whole items incl. FAIL lines), run_full_check(kernels=None, state_path=None, now=None), default_kernels() (the imported env_smoke main()-order sequence with the torch-gate two-False fallback — the shared seam for quick_check and the 08-06 worker)"
  - "tui.services.env_gate — CRITICAL/ROUTING disjoint kernel-id sets covering all seven ids, frozen GateVerdict(can_launch, reasons, route_to_data), gate_verdict() pure judgment (Phase 11 wires the blocking hook, D-09)"
  - "tui.services.quick_check — QUICK_CHECK_KERNEL_IDS (exactly six ids, matmul excluded, main() order), run_quick_check(kernels=None) computed on demand, zero persistence (D-05)"
  - "tui.services.registries — load_model_entries()/load_dataset_entries() canonical entries ({key,type,species,size_m,card} / {key,category,type,metric,card}), MODEL_CARD_* canonical casing constants, load_n_audit() (tolerant, __file__-relative), presence_for() pure presence data; load_registry_counts() retained over the entry loaders"
  - "The canonical entry-key vocabulary (models species/type/size_m; datasets category/type/metric) consumed by 08-05 filters and 08-07 table columns"
affects:
  - tui/services/settings.py
  - tui/services/env_check.py
  - tui/services/env_gate.py
  - tui/services/quick_check.py
  - tui/services/registries.py
  - tests/tui/test_services_settings.py
  - tests/tui/test_services_env_check.py
  - tests/tui/test_services_env_gate.py
  - tests/tui/test_services_quick_check.py
  - tests/tui/test_services_registries.py
actuals:
  tokens: 33768     # chars/4 over the realized diff (135075 chars: 75075 code + 60000 embedded JUnit RED-evidence reports); code-only ≈ 18768 vs estimate 17000
  tasks: 3
  commits: 7        # measured: git rev-list --count 671dbe3..HEAD (3 test + 3 feat + 1 refactor)
plan_head_before: 671dbe3b31cb01b2451a7ca5744025af0e7391b7
plan_head_after: 25a4d617ccf6772da128986d338b2a1acf3054d6
tech-stack:
  added: []         # zero new packages — consumes the 08-02 [tui] group (platformdirs) and pipeline seams
  patterns:
    - "None-returning RED skeletons committed with the failing tests (07-02 precedent): the target test executes and fails on the planned assertion, never a collection error"
    - "monkeypatch-the-pipeline-module seam for default-sequence tests: setattr on env_smoke kernel attributes + sys.modules torch injection (None halt sentinel = torch-missing, fake ModuleType = torch-present) — the real kernel BODIES never execute in CI (D-03)"
    - "lint-clean naive-local datetime idiom: chained datetime.now().astimezone() (run_finetune.py:691 precedent), date.fromisoformat for date parsing, single justified-noqa _local() fixture helper"
    - "canonical casing constants over divergent card twins: MODEL_CARD_* constants declare the one field every consumer reads; the card dict preserves both twins verbatim"
key-files:
  created:
    - tui/services/settings.py
    - tui/services/env_check.py
    - tui/services/env_gate.py
    - tui/services/quick_check.py
    - tests/tui/test_services_settings.py
    - tests/tui/test_services_env_check.py
    - tests/tui/test_services_env_gate.py
    - tests/tui/test_services_quick_check.py
    - .planning/tdd-evidence/08-04-task1-red.json
    - .planning/tdd-evidence/08-04-task2-red.json
    - .planning/tdd-evidence/08-04-task3-red.json
  modified:
    - tui/services/registries.py
    - tests/tui/test_services_registries.py
key-decisions:
  - "numpy is CRITICAL (ENV-03): the plan action text's five-id CRITICAL list omitted numpy, but the behavior bullet's 'union covers all seven kernel ids' + the RESEARCH sketch + the 'matmul is critical' acceptance pin the six-id set {version_pins, dnallm, peft, cuda, matmul, numpy} — a numpy FAIL must block launch (the data chain's hard numpy>=2 floor); resolved as a plan-text slip in favor of the seven-coverage contract"
  - "default_kernels() exposed as the shared id->callable sequence (insertion order = main() order): run_full_check, quick_check's subset filter, and the 08-06 worker all consume ONE sequence definition; the torch-import gate is applied per cuda/matmul wrapper (observable pair identical to main()'s single gate)"
  - "run_full_check grew state_path/now parameters (plan artifacts said 'kernels=None, ...'): tests and 08-06 need explicit persistence targets and deterministic moments; None defaults keep the D-04 state-root location"
  - "Canonical casing: Tokenizer (not tokenizer), Mean_token_length (not mean_token_len), size (M) (not the Model_size '400M' string twin) — the committed cards' twin values genuinely diverge (prokbert-mini: Mean_token_length 6 vs mean_token_len 1), so the constants are load-bearing, declared once in registries.py"
  - "presence_for returns a frozen Presence(status, rows) with a four-value vocabulary (present/missing/unknown/unavailable); 'unavailable' is the column-level sentinel for absent/unreadable n_audit; bool excluded from 'integer' rows (the D-14 discipline); a present flag with undeterminable splits degrades to unknown, never crashes"
  - "is_same_local_day/persist default moment is an aware LOCAL datetime via the chained-astimezone idiom — behavior-identical to the naive form for all three consumers (strftime, date(), UTC instant) while satisfying the repo's DTZ-clean ruff gate; injected naive now values still read as local wall-clock time (Pitfall 8 contract)"
patterns-established:
  - "the services-tier TDD shape: RED commit = failing tests + None-skeleton signatures + validated JUnit evidence record under .planning/tdd-evidence/; GREEN commit = full implementation with contract docstring"
  - "sys.modules torch injection (None = missing, ModuleType = present) as the deterministic GPU-seam test technique — real kernels never execute CPU-side"
requirements-completed: [ENV-01, ENV-02, ENV-03, ENV-04, SEL-04]
coverage:
  - id: D1
    description: "ENV-01 service half — run_full_check executes the imported env_smoke kernels in main() order (never a child process, never stdout parsing) and returns their CheckResult list; the torch-gate appends the two ok=False empty-lines placeholders when torch cannot import"
    requirement: ENV-01
    verification:
      - kind: unit
        ref: "tests/tui/test_services_env_check.py::test_run_full_check_default_sequence_mirrors_main_order — monkeypatched env_smoke kernels + fake torch module: order == the seven ids, torch module passed through to cuda/matmul, persisted under the injected state path"
        status: pass
      - kind: unit
        ref: "tests/tui/test_services_env_check.py::test_default_sequence_torch_gate_appends_two_false_results — sys.modules torch=None halt sentinel: cuda/matmul == CheckResult(ok=False, lines=())"
        status: pass
      - kind: unit
        ref: "tests/tui/test_services_env_check.py::test_service_never_subprocesses_or_parses_env_smoke_stdout — source grep: no 'subprocess', no 'check_output'"
        status: pass
    human_judgment: false
    rationale: "All criteria are mechanically checked (test exits, recorded order lists, source grep)."
  - id: D2
    description: "ENV-02 cache + persistence — same-local-calendar-day restart is a cache hit (zero kernels), yesterday is a miss, corrupt/missing state is a None-sentinel cache miss without raising; persist writes schema_version 1 + checked_at local naive + checked_at_iso + whole items (partial failures included); persisting twice leaves one valid file with no tmp residue (atomic tmp+os.replace)"
    requirement: ENV-02
    verification:
      - kind: unit
        ref: "tests/tui/test_services_settings.py (8 tests) — D-04 root resolution per root, whole-dir env overrides beating platformdirs, empty value = unset, delegation-to-platformdirs pinned via module-attribute spies, atomic_write parents + zero residue"
        status: pass
      - kind: unit
        ref: "tests/tui/test_services_env_check.py cache/persistence tests — same-day hit, yesterday miss, corrupt/missing None, schema+both timestamps, idempotent double persist, partial failure persists whole, injected kernels in order + persist-once (counted via monkeypatched persist)"
        status: pass
      - kind: other
        ref: "verify gate: grep -rn 'json.load(' tui/services/ | grep -v artifact_loader exits 1 — every JSON read goes through the tolerant loader"
        status: pass
    human_judgment: false
    rationale: "Cache semantics, tolerance, and atomicity are all machine-verified (test exits + the plan's own grep gate)."
  - id: D3
    description: "ENV-03 env-gate judgment — gate_verdict over CheckResults classifies FAILs against disjoint CRITICAL/ROUTING sets; zero failures -> can_launch; critical FAIL blocks with its detail lines in main() kernel order; dataset_dirs FAIL routes to data without blocking; both together produce both signals; unknown kernel ids ignored"
    requirement: ENV-03
    verification:
      - kind: unit
        ref: "tests/tui/test_services_env_gate.py (8 tests) — every behavior bullet incl. the both-failures case, kernel-order reasons, disjoint-set/coverage assertions, frozen verdict"
        status: pass
    human_judgment: false
    rationale: "Pure-function behavior, fully pinned by test assertions."
  - id: D4
    description: "ENV-04 quick check — revalidates exactly the six non-matmul kernel ids (QUICK_CHECK_KERNEL_IDS, main() order) through the shared env_check sequence, injectable for CI fakes, computed on demand with zero persistence"
    requirement: ENV-04
    verification:
      - kind: unit
        ref: "tests/tui/test_services_quick_check.py (4 tests) — six ids/no matmul, injected order, default = env_check sequence filtered (monkeypatched), nothing written to the state dir"
        status: pass
    human_judgment: false
    rationale: "Subset membership, ordering, and no-persistence are mechanical assertions."
  - id: D5
    description: "SEL-04 presence data — canonical registry entries (62 models {key,type,species,size_m,card} / 50 datasets {key,category,type,metric,card}) through the overlay-merged loaders; presence_for pure data (present with exact integer train/dev/test rows, missing flag beats counts, unknown on registry/audit drift, column-unavailable sentinel on absent audit); n_audit read tolerantly via artifact_loader with an __file__-relative path; counts consistent with entry lists"
    requirement: SEL-04
    verification:
      - kind: unit
        ref: "tests/tui/test_services_registries.py (18 tests: 17 new + 08-03's count test kept green) — canonical keys, raw values with empty-string absents, size_m == float(card['size (M)']), casing-twin constants, all four presence cases, real committed artifact (50 tasks, BEND present (743095,109717,106227), GUE missing), all 50 registry keys definite, corrupt/missing audit -> None, zero Chinese"
        status: pass
      - kind: other
        ref: "git diff clean for pipeline/registry_loader.py and dnallm-mark/data/n_audit.json (D-10 / committed artifact untouched)"
        status: pass
      - kind: other
        ref: "make lint exit 0; make typecheck exit 0 (Task 3 verify gates)"
        status: pass
    human_judgment: false
    rationale: "Entry shapes, presence mapping, tolerance, and file immutability are all mechanically checked."
duration: 32 min
completed: 2026-10-11T12:40:49Z
status: complete
---

# Phase 08 Plan 04: Env/Registry Services Layer Summary

Landed the entire non-visual half of the console as five textual-free services: the D-04 XDG state/config split with atomic writes, env-check orchestration with same-local-day cache semantics over the imported env_smoke kernels, the pure D-09 gate judgment and six-kernel quick-check subset, and the canonical registry entry view with exact n_audit presence data — every piece tier-1 tested headless with injected fakes.

## Performance

- **Duration:** 32 min (12:08:47Z – 12:40:49Z, 2026-10-11)
- **Tasks completed:** 3 / 3 (each a full TDD RED-GREEN cycle)
- **Files changed:** 13 (11 created, 2 modified; +1847/−19 lines)
- **Commits:** 7 (measured from the persisted plan ledger: 3 test + 3 feat + 1 refactor)
- **Estimate calibration:** code-only diff ≈ 18768 tokens vs 17000 estimated (110% — the low-confidence estimate was close); full realized diff including the three embedded JUnit RED-evidence reports is 33768 tokens

## Accomplishments

- **Task 1 — settings + env_check (ENV-01/ENV-02, D-04/D-05):** `state_dir()`/`config_dir()` resolve the two XDG roots separately through platformdirs, each behind its whole-dir env override (empty value = unset, the registry_loader idiom mirrored with the pipeline original untouched — D-10); `atomic_write` does tmp-sibling + os.replace with parent mkdir on demand (T-08-03). `env_check` reads state through artifact_loader's None sentinel (torn/corrupt/missing = cache miss, never a crash), compares LOCAL calendar days (Pitfall 8 basis documented in the docstring, both timestamp forms persisted from one instant), persists partial failures whole, and runs the imported env_smoke kernel sequence in main() order — kernels imported, never subprocessed (D-02), with the torch-import gate's two-False fallback reproduced exactly.
- **Task 2 — env_gate + quick_check (ENV-03/ENV-04, D-09):** frozen `GateVerdict(can_launch, reasons, route_to_data)` over disjoint CRITICAL/ROUTING sets covering all seven kernel ids (numpy resolved into CRITICAL — see Decisions); reasons collect failing kernels' lines in main() order; unknown future kernel ids ignored deterministically. `quick_check` revalidates exactly the six non-matmul ids through the shared `default_kernels()` sequence, injectable, never persisted.
- **Task 3 — registries expansion (SEL-04, D-08):** canonical entry lists through the overlay-merged Phase 7 loaders (62/50, counts now implemented over the entry loaders so they can never disagree); the casing twins resolved once via `MODEL_CARD_*` constants (the committed cards' twin values genuinely diverge); `load_n_audit()` tolerant read with an `__file__`-relative path; `presence_for()` returns pure data — present with exact integer (train, dev, test) rows, missing flag beats any counts, unknown on registry/audit drift, column-unavailable sentinel when the audit itself is absent. pipeline/registry_loader.py and dnallm-mark/data/n_audit.json untouched.
- **Proof, not inspection:** all three RED cycles validated `RED_EVIDENCE_OK` by the gate tool before each GREEN; tests/tui 53 passed; make lint + make typecheck clean; make test-fast 613 passed (563 prior + 50 new, zero regressions); make ci 77 passed; the services-textual-free import lock green and non-vacuous over the now-five-module services tier.

## Task Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 RED — settings/env_check tests | `32b3544` | test(08-04): add failing tests for settings + env-check services |
| 1 GREEN — implementation | `c102f55` | feat(08-04): implement settings (XDG split) + env-check orchestration |
| 2 RED — env_gate/quick_check tests | `3f3ba42` | test(08-04): add failing tests for env-gate judgment + quick-check subset |
| 2 GREEN — implementation | `68e8028` | feat(08-04): implement env-gate judgment + quick-check subset |
| 3 RED — registries expansion tests | `8e9bdd4` | test(08-04): add failing tests for registry entry view + n_audit presence |
| 3 GREEN — implementation | `c065f95` | feat(08-04): implement registry entry view + n_audit presence |
| lint fold-in (see Deviations 3) | `25a4d61` | refactor(08-04): fold env_check datetime handling into the lint-clean idiom |
| plan metadata (docs) | (this commit) | docs(08-04): complete env/registry services plan |

## Files Created/Modified

- **Created:** `tui/services/settings.py`, `tui/services/env_check.py`, `tui/services/env_gate.py`, `tui/services/quick_check.py`, `tests/tui/test_services_settings.py`, `tests/tui/test_services_env_check.py`, `tests/tui/test_services_env_gate.py`, `tests/tui/test_services_quick_check.py`, plus the three `.planning/tdd-evidence/08-04-task{1,2,3}-red.json` records
- **Modified:** `tui/services/registries.py` (entry view + presence expansion over the retained counts), `tests/tui/test_services_registries.py` (08-03's count test kept verbatim + 17 new tests)

## Decisions Made

- **numpy is CRITICAL:** the plan action text listed five CRITICAL ids (no numpy), but the behavior bullet ("their union ... covers all seven kernel ids"), the RESEARCH sketch, and the acceptance criteria ("matmul is critical", disjoint sets) together pin the six-id set — with numpy in neither set, a numpy FAIL could never block launch, which is wrong for the data chain's hard `numpy>=2` floor. Treated as a plan-text slip; the seven-coverage contract wins.
- **`default_kernels()` as the shared sequence seam:** one dict {kernel id -> zero-arg callable} in main() insertion order serves run_full_check, quick_check's subset filter, and (08-06) the worker posting one message per kernel. The torch gate is applied inside the cuda/matmul wrappers — the observable pair is identical to main()'s single gate (import failure deterministically produces both placeholders).
- **`run_full_check(kernels=None, state_path=None, now=None)`:** the plan's "..." resolved with explicit persistence-target and moment parameters (tests and 08-06 need them); None defaults preserve the D-04 state-root location and current-moment behavior.
- **Canonical casing constants are load-bearing:** the committed model cards carry `Tokenizer`/`tokenizer` and `Mean_token_length`/`mean_token_len` twins whose values genuinely diverge (prokbert-mini: 6 vs 1), and `size (M)`/`Model_size` naming twins — `MODEL_CARD_*` declares the one field each consumer reads while `card` preserves both twins verbatim.
- **Aware-local default moment:** `datetime.now().astimezone()` (the chained idiom run_finetune.py:691 already uses) replaces the bare naive `datetime.now()` — behavior-identical for all three consumers while satisfying the repo's DTZ-clean ruff gate; naive injected `now` values still read as local wall-clock time (Pitfall 8).
- **Presence vocabulary:** four statuses (`present`/`missing`/`unknown`/`unavailable`) as plain string constants + a frozen `Presence` dataclass; `unavailable` is column-level (audit absent), `unknown` covers registry/audit drift AND undeterminable splits (degrade, never crash); bool excluded from "integer" rows (D-14 discipline).

## Deviations from Plan

**1. [Rule 1 - test-side bugs] Task 1 GREEN-phase test corrections**
- **Found during:** Task 1 GREEN run
- **Issue:** Two RED-phase test defects surfaced once the implementation existed: the recording cuda/matmul fakes didn't append to the shared order list (so the main()-order assertion under-recorded), and the service docstring's word "subprocesses" tripped the test's own no-child-process source grep.
- **Fix:** Recording fakes now append to the shared list (helper takes `order` explicitly); docstring reworded to "never runs env_smoke as a child process". Service code unchanged by the first fix.
- **Files modified:** tests/tui/test_services_env_check.py, tui/services/env_check.py (docstring only)
- **Verification:** 21 tests green; grep gate clean.
- **Commit:** `c102f55`

**2. [Rule 1 - wrong spot literal] Task 3 BEND type assertion**
- **Found during:** Task 3 GREEN run
- **Issue:** The raw-values spot check asserted BEND__CpG_methylation `type == "binary"`; the committed card says `multilabel` (labels: 7). The service was passing the raw value correctly — the test literal was wrong.
- **Fix:** Assertion corrected to the committed value.
- **Files modified:** tests/tui/test_services_registries.py
- **Commit:** `c065f95`

**3. [Rule 1 - process] env_check lint fixes missed from the Task 2 staging**
- **Found during:** plan-level verification (git status)
- **Issue:** The DTZ/UP datetime fixes to `tui/services/env_check.py` were made during Task 2's lint-compliance pass but the file was not in that commit's `git add` list — the changes sat uncommitted while the gates had been verified against them.
- **Fix:** Committed as a dedicated `refactor(08-04)` commit with the full explanation; all gates re-run green afterward (53 tui tests, lint, typecheck, full 613-test fast suite).
- **Files modified:** tui/services/env_check.py
- **Commit:** `25a4d61`

**4. [Rule 3 - tooling] ruff DTZ/UP/B010 + ty findings on the new modules**
- **Found during:** Task 2/3 verify gates (make lint / make typecheck)
- **Issue:** The repo's effective ruff set flags naive-datetime construction (DTZ001/DTZ005/DTZ007), the timezone.utc spelling (UP017), constant-attr setattr (B010), and import grouping (I001); ty flags both direct assignment and setattr on frozen dataclass properties depending on form.
- **Fix:** All resolved via repo precedents — the chained-astimezone idiom, `date.fromisoformat`, the UTC alias, a single justified-noqa `_local()` test helper, `setattr` + justified `# noqa: B010` for the frozen-verdict mutation test (the 08-01 inverse-conflict pattern), and correct first-party import grouping.
- **Files modified:** tui/services/env_check.py, tui/services/env_gate.py, tests/tui/test_services_env_check.py, tests/tui/test_services_env_gate.py, tests/tui/test_services_registries.py
- **Verification:** make lint + make typecheck exit 0; all suites green.
- **Commits:** `68e8028`, `c065f95`, `25a4d61`

**Total deviations:** 4 auto-fixed (2 Rule 1 test/code corrections, 1 Rule 1 process fix, 1 Rule 3 tooling pass).
**Impact:** None on the plan's contracts — every D-number truth is implemented as specified; the D-02/D-03/D-10 prohibitions verified untouched.

## TDD Gate Compliance

All three tasks carried `tdd="true"` and completed full RED-GREEN cycles with gate-validated evidence:

| Task | RED commit | RED evidence | GREEN commit |
|------|-----------|--------------|--------------|
| 1 | `32b3544` | `RED_EVIDENCE_OK` (21 tests, 18 failed, 0 errors; target `test_same_day_state_is_a_cache_hit`) | `c102f55` |
| 2 | `3f3ba42` | `RED_EVIDENCE_OK` (12 tests, 12 failed, 0 errors; target `test_critical_fail_blocks_launch_with_its_detail_lines`) | `68e8028` |
| 3 | `8e9bdd4` | `RED_EVIDENCE_OK` (18 tests, 16 failed, 0 errors; target `test_presence_present_returns_exact_integer_rows`) | `c065f95` |

RED method: None-returning skeletons committed with the failing tests (the 07-02 precedent), so every target test executed and failed on its planned assertion — no collection, import, or fixture faults (JUnit `errors=0` in all three records). The trivially-green tests against skeletons (None-expecting cache-miss cases, source greps over the skeleton, the frozen-type check) are noted in each record's semantic assessment. One REFACTOR-class commit (`25a4d61`, the lint fold-in) exists with tests still green; its staging omission from Task 2 is documented as Deviation 3. Gate commits verified: 3 `test(08-04):` + 3 `feat(08-04):` present in git log.

## Issues Encountered

None beyond the deviations above. No auth gates, no package installs (the [tui] group landed in 08-02; platformdirs was already locked), no pre-commit hook cycles. The GB10 host's real torch never executed in any test — the torch seam is fully controlled by sys.modules injection.

## User Setup Required

None.

## Known Stubs

None — no placeholder patterns in the delivered files; the designed sentinels (None cache-miss, empty-lines torch placeholders, PRESENCE_UNAVAILABLE) are specified behavior with tests, not stubs.

## Next Phase Readiness

- **08-05 (selection services):** the canonical entry vocabulary (`species`/`type`/`size_m`, `category`/`type`/`metric`) and the `MODEL_CARD_*` constants are the declared filter-axis contract; presets derive from `pipeline/sweep_priorities.json` per D-06 with registry keys as row_keys.
- **08-06 (env screen build):** `default_kernels()` is the worker's iteration seam (one message per kernel), `load_cached` + `is_same_local_day` compose the on_mount cache check (same-day hit -> render cached items, zero kernels), `persist` is called by `run_full_check`, and the stable kernel-id row keys the 08-03 shell already renders are exactly `CheckResult.name` values.
- **08-07 (selection screen):** `presence_for` returns pure data — the screen maps the four statuses to glyphs/copy from `tui/strings.py` and formats the exact integer rows.
- **Phase 11 (launch):** `gate_verdict` and `run_quick_check` are the ready-made pure judgments the launch gate wires; per D-09 the persisted env-check state is never a gate input (quick-check computes fresh).
- **Every pytest lane already carries the tui group** (08-03), so the 50 new tests ride `make test`/`test-fast`/`ci` with zero Makefile edits; the PHASE8_TUI lint wildcard picked up all four new service modules automatically.

## Self-Check: PASSED

- All 4 new service modules + 4 new test files — FOUND (committed across `32b3544`/`c102f55`/`3f3ba42`/`68e8028`/`8e9bdd4`/`c065f95`)
- Modified registries pair — FOUND in `8e9bdd4`/`c065f95`
- 3 tdd-evidence records — FOUND, all `RED_EVIDENCE_OK`-validated
- Task commits verified as ancestors of HEAD: `32b3544`, `c102f55`, `3f3ba42`, `68e8028`, `8e9bdd4`, `c065f95`, `25a4d61`
- Commit count measured from the persisted ledger: 7 production commits (`git rev-list --count 671dbe3..HEAD`)
- TDD gate: 3 `test(08-04):` + 3 `feat(08-04):` commits present (git log grep validated)
- Gates at plan close: tests/tui 53 passed; make lint 0; make typecheck 0; make test-fast 613 passed; make ci 77 passed; json.load gate clean; registry_loader/n_audit/env_smoke unmodified
