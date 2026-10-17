---
phase: 08-tui-foundation-env-check-selection
plan: 03
subsystem: tui (env-check shell screen + first pipeline-seam service)
tags: [tui, tracer, pilot-tests, env-check-shell, registry-seam, import-lock, env-01, i18n-01]
requires:
  phase: []
provides: []
provides:
  - "tui.services.registries.load_registry_counts() -> RegistryCounts(models, datasets) — the first service on the tui→pipeline seam, proven with the real committed registries (62, 50); 08-04 expands this module to entry lists/filter axes"
  - "tui/screens/env_check.py — the env-check shell screen: seven fixed pending rows in main() kernel order, keyed on the stable kernel ids, rendered entirely through strings constants (filled with async kernel results by 08-06)"
  - "tui/app.py screen registration (SCREENS) + opening screen (get_default_screen) + app-level q binding — the boot path make tui runs and the Pilot lane boots headlessly"
  - "tests/tui/test_import_lock.py — the services-textual-free absence lock (ast walk over every Import/ImportFrom node, non-vacuous glob assertion): the foundation invariant is locked from the first services module"
  - "The tier-1/tier-2 test style-setters for the rest of Phase 8: test_services_registries.py (real-data seam test) and test_pilot_boot.py (Pilot boot test, 120x40, pause-before-assert, q-exit assertion)"
affects:
  - tui/app.py
  - tui/strings.py
  - tui/screens/env_check.py
  - tui/services/registries.py
  - Makefile
  - tests/tui/
actuals:
  tokens: 4815      # chars/4 over the realized diff (19260 chars) — vs estimate 9000
  tasks: 1          # the tracer task (single-task plan by design)
  commits: 1        # measured: git rev-list --count 34eabec..HEAD
plan_head_before: 34eabec1ad81e81b4782dda3630fe7effb899adb
plan_head_after: 6b78026c0c6e9b168aa6573d85f30c38c3fbd02d
tech-stack:
  added: []         # zero new packages — the [tui] group landed in 08-02; this plan consumes it
  patterns:
    - "ClassVar annotations mirroring the framework base for mutable class attributes (App.BINDINGS / App.SCREEN declarations copied verbatim from textual/app.py) — ruff RUF012 satisfied by truthful typing, not noqa suppression"
    - "Pilot boot-test shape: run_test(size=(120, 40)) → await pilot.pause() → isinstance(app.screen, ...) → row_count + get_row_at(index) order assertions + get_row(key) keyed assertion → press q → return_code == 0 (timing proven by a pre-implementation probe)"
    - "absence lock over a directory: ast.walk every Import/ImportFrom node in tui/services/*.py with a non-vacuous glob assertion (Phase 7 absence-lock discipline applied to the services tier)"
key-files:
  created:
    - tui/screens/env_check.py
    - tui/services/registries.py
    - tests/tui/test_services_registries.py
    - tests/tui/test_pilot_boot.py
    - tests/tui/test_import_lock.py
  modified:
    - tui/app.py
    - tui/strings.py
    - Makefile
key-decisions:
  - "RUF012 resolved by mirroring the App base ClassVar annotations verbatim (BINDINGS: ClassVar[list[BindingType]], SCREENS: ClassVar[dict[str, Callable[[], Screen[Any]]]]) — these are framework-read class constants; annotation is truthful, suppression was rejected"
  - "Makefile test-fast + ci gain --group tui (Rule 3): pytest imports every collected module BEFORE -m filtering, so the first textual-importing test file would break both documented local lanes on a fresh dev-only venv — every pytest lane now carries textual-the-library (the D-01 posture), data/gpu lanes still never see textual"
  - "RegistryCounts NamedTuple: named fields for call-site readability, compares equal to the plain tuple (62, 50); the seam test pins the seam + real data with the custom overlay pinned empty (the tests/test_registry_loader.py machine-independence discipline), while overlay MERGE semantics stay pinned in tests/test_registry_loader.py"
  - "env_check.py is zero-Chinese including docstrings and comments — keeps the I18N-01 grep-ability property absolute (no Chinese characters anywhere in the tui tree outside tui/strings.py)"
  - "The plan-text acceptance criterion naming 'uv run --group dev --group tui python -m tui' as the make tui recipe is a plan slip resolved in favor of the 08-02-locked Pitfall-10 recipe (uv run --group tui --group gpu python -m tui, no dev group, gpu required on GB10); the load-bearing half of the criterion — the boot test exercises the same DnallmMarkTui class headlessly — holds and is proven"
patterns-established:
  - "tracer-first plan shape proven: one committed path (dependency group → entry point → bootstrap → screen → service → pipeline seam) with the tier invariant (import lock) landing in the same commit as the first module it governs"
  - "the Pilot boot test is the boot-path contract: any future change to the opening screen, screen registration, bindings, or row composition reddens this one test"
  - "pilot.quit timing: press(\"q\") + await pilot.pause() → is_running False and return_code 0 inside the run_test block (empirically probed before the test was written — no flaky assertion patterns)"
requirements-completed: [ENV-01, I18N-01]
coverage:
  - id: D1
    description: "Phase tracer — the app boots headless (Pilot, 120x40) on the env-check shell screen rendering the seven fixed pending-state rows in main() kernel order from strings constants, quits cleanly on q; the first service crosses the tui→pipeline seam returning the real overlay-merged registry counts (62, 50) by importing pipeline/registry_loader; the services-textual-free import lock is green and non-vacuous"
    requirement: ENV-01
    verification:
      - kind: unit
        ref: "uv run --group dev --group tui pytest tests/tui -q → 3 passed (seam counts + Pilot boot + import lock)"
        status: pass
      - kind: unit
        ref: "tests/tui/test_services_registries.py: load_registry_counts() == (62, 50) against the real committed registries (custom overlay pinned empty via DNALLMMARK_CUSTOM_REGISTRY_DIR — machine-independent, no fakes on the path)"
        status: pass
      - kind: unit
        ref: "tests/tui/test_pilot_boot.py: run_test(size=(120,40)) → isinstance(app.screen, EnvCheckScreen); row_count == 7; get_row_at(index) == [ENV_STATE_PENDING, label] for each ENV_KERNEL_LABELS entry in order; get_row(kernel_id) keyed on the stable kernel id; press q → app.return_code == 0"
        status: pass
      - kind: unit
        ref: "tests/tui/test_import_lock.py: ast walk of tui/services/*.py → zero textual imports (top-level or nested); non-vacuous (glob-found file count asserted >= 1)"
        status: pass
      - kind: other
        ref: "make lint exit 0 — the lint command line carries tui/screens/env_check.py + tui/services/registries.py (PHASE8_TUI wildcard, zero Makefile lint edits)"
        status: pass
      - kind: other
        ref: "make typecheck exit 0 ('All checks passed!')"
        status: pass
      - kind: other
        ref: "entry smoke: import tui.__main__ → entry-import-ok; make -n tui → 'uv run --group tui --group gpu python -m tui'; the boot test boots the same DnallmMarkTui class that entry point runs"
        status: pass
      - kind: other
        ref: "regression hygiene: make test-fast → 563 passed, 1 deselected (560 pre-existing + 3 new; zero regressions); make ci → 77 passed"
        status: pass
    human_judgment: false
    rationale: "Every criterion is mechanically checked (test exits, headless Pilot assertions over real data, ast walk, lint/typecheck exits, command expansion) — no visual or judgment-based criterion exists for this deliverable."
  - id: D2
    description: "I18N-01 seam exercised — the shell renders only through tui/strings.py constants (APP_QUIT_LABEL, ENV_STATE_PENDING, ENV_COL_STATE/ITEM, ENV_KERNEL_LABELS, all UI-SPEC Copywriting Contract verbatim); tui/screens/env_check.py and tui/app.py carry zero Chinese literals anywhere (docstrings and comments included)"
    requirement: I18N-01
    verification:
      - kind: other
        ref: "grep -P '[\\x{4e00}-\\x{9fff}]' over tui/screens/env_check.py tui/app.py → zero matches (zero-Chinese-ok)"
        status: pass
      - kind: unit
        ref: "Pilot test asserts every row == [ENV_STATE_PENDING, ENV_KERNEL_LABELS[kernel_id]] — strings constants are the render vocabulary, and the strings values match the UI-SPEC Copywriting rows verbatim (landed 08-02, extended here with the pending-state + column-header + quit-label rows)"
        status: pass
    human_judgment: false
    rationale: "Both checks are mechanical greps/assertions over committed text; no visual judgment involved."
duration: 15 min
completed: 2026-10-11T12:00:00Z
status: complete
---

# Phase 08 Plan 03: TUI Tracer — Env-Check Shell over the Pipeline Seam Summary

Ran the phase tracer: the console boots headless on an env-check shell screen (seven fixed pending rows, main() kernel order, stable kernel-id row keys) and the first textual-free service crosses the tui→pipeline seam returning the real registry counts (62, 50) from pipeline/registry_loader — the whole stack proven on one committed path with the services import lock green.

## Performance

- **Duration:** 15 min (2026-10-11T11:44:53Z – 11:59:55Z)
- **Tasks completed:** 1 / 1 (the tracer task; single-task plan by design)
- **Files changed:** 8 (5 created, 3 modified; +363/−12 lines)
- **Commits:** 1 production commit (measured from the persisted plan ledger)
- **Estimate calibration:** 4815 actual tokens vs 9000 estimated (54% — the low-confidence estimate overestimated the tracer slice; the skeleton it built on was already complete)

## Accomplishments

- **The tracer path, wired end-to-end:** `tui/app.py` registers the env-check screen (`SCREENS`), opens on it (`get_default_screen`), and carries the app-level `q` quit binding; `tui/screens/env_check.py` composes a DataTable whose `on_mount` adds the seven fixed pending rows — one per kernel id in main() order (`version_pins, dnallm, peft, cuda, matmul, numpy, dataset_dirs`), each row keyed on its stable kernel id (the 08-06 update seam) and rendering `ENV_STATE_PENDING` + the kernel label from `tui/strings.py`; `tui/services/registries.py` is the first services module — `load_registry_counts()` imports `registry_loader` as a top-level module (pipeline/ sys.path root) and returns `RegistryCounts(62, 50)` from the real overlay-merged loaders, zero re-implementation, zero textual import.
- **The tier invariant locked from the first module:** `tests/tui/test_import_lock.py` ast-walks every `Import`/`ImportFrom` node in `tui/services/*.py` (top-level or nested) and asserts the glob found at least one file — the services-textual-free contract declared in 08-02's `tui/services/__init__.py` is now enforced, not just documented.
- **Both test lanes proven CPU-side:** tier-1 seam test asserts the real counts (custom overlay pinned empty for machine independence — the `tests/test_registry_loader.py` discipline); tier-2 Pilot boot test boots the real `DnallmMarkTui` at 120x40, asserts the opening screen, exactly 7 pending rows in order and keyed, and a clean `q` exit (return code 0 — the quit-timing was probed empirically before the test was written).
- **Tracer feedback gate (auto mode):** after the task commit, the full `<verify>` chain was re-run end-to-end — pytest tests/tui 3 passed, make lint 0, make typecheck 0 — `⚡ Tracer verified end-to-end — expanding`. The skeleton is proven; the phase's remaining plans expand onto it.
- **Proof, not inspection:** all three plan verify commands green post-commit; entry smoke (`import tui.__main__`, `make -n tui`) confirms the boot test exercises the exact class the entry point runs; regression hygiene — `make test-fast` 563 passed (+3 new, zero regressions), `make ci` 77 passed.

## Task Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 — tracer: env-check shell + registry seam + import lock (feat) | `6b78026` | feat(08-03): tracer — console boots on env-check shell over the pipeline seam |
| plan metadata (docs) | (this commit) | docs(08-03): complete TUI tracer plan |

## Files Created/Modified

- **Created:** `tui/screens/env_check.py` (env-check shell screen — DataTable, seven pending rows, kernel-id row keys, zero Chinese literals), `tui/services/registries.py` (first service: `load_registry_counts()` delegating to `registry_loader`), `tests/tui/test_services_registries.py` (tier-1 seam test), `tests/tui/test_pilot_boot.py` (tier-2 Pilot boot test), `tests/tui/test_import_lock.py` (services-textual-free absence lock)
- **Modified:** `tui/app.py` (screen registration + opening screen + q binding, ClassVar annotations), `tui/strings.py` (+`APP_QUIT_LABEL`, +`ENV_STATE_PENDING`, +`ENV_COL_STATE`/`ENV_COL_ITEM`), `Makefile` (test-fast + ci gain `--group tui`)

## Decisions Made

- **ClassVar annotations mirror the App base (RUF012):** ruff flagged `BINDINGS` and `SCREENS` as mutable class-attribute defaults. Annotated with the base class declarations verbatim (`BINDINGS: ClassVar[list[BindingType]]`, `SCREENS: ClassVar[dict[str, Callable[[], Screen[Any]]]]` — textual/app.py:393,454) — truthful (framework-read class constants), keeps real typing, no noqa.
- **`--group tui` extended to test-fast and ci (Rule 3):** the first textual-importing test files would break `make test-fast` and `make ci` on any fresh dev-only venv (pytest imports every collected module before `-m` filtering). Both recipes now match the `test:` recipe's D-01 posture; CI (which runs only lint/typecheck/test) was never affected, and the data/gpu lanes still never see textual.
- **`RegistryCounts` NamedTuple:** named fields for call-site readability; compares equal to the plain `(62, 50)` tuple. The seam test pins the seam + the real committed data; overlay merge semantics remain pinned where they belong (`tests/test_registry_loader.py`).
- **Zero-Chinese discipline extends to docstrings/comments:** `tui/screens/env_check.py` and `tui/app.py` contain no Chinese characters at all, keeping the I18N-01 grep-ability property absolute (any Chinese anywhere in the tui tree outside `tui/strings.py` is a violation).
- **make tui recipe discrepancy resolved toward the locked decision:** the plan's acceptance criterion cites `uv run --group dev --group tui python -m tui`, but the 08-02-locked recipe is `uv run --group tui --group gpu python -m tui` (Pitfall 10: gpu required on GB10; no dev group). The recipe was NOT changed — the criterion's load-bearing half (boot test exercises the same app class) is satisfied and proven.

## Deviations from Plan

**1. [Rule 1 - lint finding] RUF012 mutable class-attribute defaults in tui/app.py**
- **Found during:** Task 1 (verify command 2, first run)
- **Issue:** The Textual-idiom `BINDINGS = [...]` / `SCREENS = {...}` class attributes trigger ruff RUF012 (mutable default value for class attribute).
- **Fix:** Annotated both with the App base class's own ClassVar declarations, imported `BindingType`/`Screen`/`Callable`/`Any` accordingly — framework-read class constants, truthfully typed; no noqa suppression.
- **Files modified:** tui/app.py
- **Verification:** make lint exit 0; make typecheck exit 0 (annotations resolve against real textual types).
- **Commit:** `6b78026`

**2. [Rule 3 - blocking issue] Makefile test-fast + ci would fail collection on fresh dev-only venvs**
- **Found during:** Task 1 (post-verify regression hygiene — `make test-fast`)
- **Issue:** This plan lands the first textual-importing test modules (`tests/tui/test_pilot_boot.py` imports `textual.widgets`). `make test-fast` and `make ci` run pytest with `--group dev` only, and pytest imports every collected module BEFORE applying `-m` filters — on a fresh clone with a fresh venv (no textual; it lives only in the [tui] group), both documented local lanes would die with a ModuleNotFoundError collection error. CI is unaffected (it runs lint/typecheck/test, all of which carry `--group tui`).
- **Fix:** Added `--group tui` to both recipes with dated comments — the exact D-01 pattern already sanctioned for `test:`; no workflow edits, no new jobs, data/gpu lanes untouched.
- **Files modified:** Makefile
- **Verification:** make test-fast → 563 passed, 1 deselected; make ci → 77 passed; make test (CI lane) unchanged and green.
- **Commit:** `6b78026`

**Total deviations:** 2 auto-fixed (1 Rule 1, 1 Rule 3).
**Impact:** None on the plan's contract — all verify commands green after each fix; the tracer's one-path scope (no worker, no kernel imports, no second screen) is untouched.

## Issues Encountered

- The plan-text acceptance criterion 4 names `uv run --group dev --group tui python -m tui` as "the make tui recipe path" — the actual locked recipe is `uv run --group tui --group gpu python -m tui` (08-02, Pitfall 10). Treated as a plan-text slip (the plan predates the final recipe shape and carried `confidence: low`): the recipe was left at the locked form, and the criterion's substance — the boot test exercises the same app class the entry point runs — was verified explicitly (entry smoke + `make -n tui`).
- Nothing else. No auth gates, no package installs, no pre-commit hook cycles (the commit landed first try).

## User Setup Required

None. (`make tui` on the GB10 host now opens the console on the env-check shell — seven pending rows; the kernel fill lands with 08-04/08-06.)

## Known Stubs

None — the pending-only shell is the designed tracer shape per the plan (explicitly "this shell is filled by 08-06"), not a stub: every element this plan promises (screen, service, seam, lock, boot path) exists and is gate-covered. No placeholder text, no unwired data sources.

## Next Phase Readiness

- **08-04 (env services):** the services tier pattern is set — module-docstring contract block, top-level pipeline imports, tier-1 test style; the import lock already guards the tier; `CheckResult` kernel ids are the established row vocabulary.
- **08-06 (env screen build):** `on_mount` is the fill seam and the stable kernel-id row keys are proven (the boot test asserts them) — the worker's `update_cell` path has its targets; the summary column, verdict block, and footer chrome extend the shell without restructuring it.
- **The Pilot lane is proven on a real async test** (auto mode, 120x40, pause-before-assert, exit-code assertion) — every later screen test copies this shape.
- **Every pytest make lane is now tui-capable** (test / test-fast / ci), so later plans adding tests/tui modules need zero Makefile edits.

## Self-Check: PASSED

- All 5 created files — FOUND (committed in `6b78026`): tui/screens/env_check.py, tui/services/registries.py, tests/tui/test_services_registries.py, tests/tui/test_pilot_boot.py, tests/tui/test_import_lock.py
- All 3 modified files — FOUND in `6b78026`: tui/app.py, tui/strings.py, Makefile
- Task commit verified as ancestor of HEAD: `6b78026`
- Commit count measured from the persisted ledger: 1 production commit (`git rev-list --count 34eabec..6b78026`)
- Tracer feedback gate: all three verify commands green post-commit (auto mode — `⚡ Tracer verified end-to-end — expanding`)
