---
phase: 08-tui-foundation-env-check-selection
plan: 08
subsystem: tui (selection/env-check seams, pipeline env_smoke kernels) — gap closure
tags: [tui, gap-closure, cr-01, wr-01, registry-tolerance, env-smoke, work-hardening, sel-01, env-01]
requires:
  phase: ["08-07", "08-04"]
provides:
  - "tui/services/registries.py — isinstance-guarded canonical projections (_project_model_entry/_project_dataset_entry): a non-dict card value (loader-accepted input) projects as the empty card with the original value verbatim — chain 1 closed at the root"
  - "tui/screens/selection.py _load_entries — the widened except tuple (OSError, SystemExit, json.JSONDecodeError, UnicodeDecodeError): a corrupt OFFICIAL registry degrades to the documented ([], path) load-error state; both routing call sites (load_selection_data, preset_menu) inherit the seam — chain 2 closed"
  - "pipeline/env_smoke.py — _read_registry fail-closed helper in BOTH directory kernels (named ok=False FAIL line in the torch-gate wording shape on OSError/JSONDecodeError/UnicodeDecodeError; non-dict/path-less entries count as fail-closed missing); healthy-path bytes unchanged, S1-S4 goldens green unmodified"
  - "tui/screens/env_check.py run_full_check — WR-01 guards inside the existing @work shape (per-kernel degrade + kernels()-enumeration degrade through ENV_KERNEL_DEGRADED, same persist+complete tail) + exit_on_error=False"
  - "tests/tui/test_work_site_hardening.py — the AST structural never-exit pin (exit_on_error=False OR internal broad except at every @work site, >=20-site non-vacuity floor, file:line offender messages)"
affects:
  - tui/services/registries.py
  - tui/services/selection.py
  - tui/screens/selection.py
  - tui/screens/env_check.py
  - tui/strings.py
  - pipeline/env_smoke.py
  - tui/app.py
  - tui/screens/about.py
  - tui/screens/data_manager.py
  - tui/screens/monitor.py
  - tui/screens/wizard.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_pilot_env_check.py
  - tests/test_env_smoke_bytes.py
  - tests/tui/test_work_site_hardening.py
actuals:
  tokens: 11183   # chars/4 over the realized code diff (44730 chars, tui/+pipeline/+tests/, 22ca261..514721d)
  tasks: 3
  commits: 6      # measured: git rev-list --count 22ca261..514721d (2 test-RED + 2 fix-GREEN + 1 feat pin+kwarg sweep + 1 docs ledger typo); the SUMMARY/docs commit follows
plan_head_before: 22ca261ccd280c95805b06519bc8ea1d828a9d7d
plan_head_after: 514721dcf17249b62d14646e37ca0e335caef17b
tech-stack:
  added: []        # zero new dependencies; textual stays pinned 8.2.8; exit_on_error is textual's own decorator kwarg
  patterns:
    - "fail-closed degraded CheckResult in the torch-gate wording shape (FAIL: read registry {path} — {Type}: {msg}) — an unreadable registry is a named FAIL and a non-zero E2' exit, never a traceback"
    - "the never-exit dichotomy pinned structurally: every @work site carries exit_on_error=False OR an internal broad except (Exception/BaseException/bare); specific-tuple handlers deliberately do NOT qualify"
    - "empty-card projection for loader-accepted non-dict card values — key visible, blank filter axes, size_m 0.0, original value verbatim (never mutated, never dropped)"
key-files:
  created:
    - tests/tui/test_work_site_hardening.py
    - .planning/tdd-evidence/08-08-task1-red.json
    - .planning/tdd-evidence/08-08-task2-red.json
    - .planning/tdd-evidence/08-08-task3-red.json
  modified:
    - tui/services/registries.py
    - tui/services/selection.py
    - tui/screens/selection.py
    - tui/screens/env_check.py
    - tui/strings.py
    - pipeline/env_smoke.py
    - tui/app.py
    - tui/screens/about.py
    - tui/screens/data_manager.py
    - tui/screens/monitor.py
    - tui/screens/wizard.py
    - tests/tui/test_pilot_selection.py
    - tests/tui/test_pilot_env_check.py
    - tests/test_env_smoke_bytes.py
key-decisions:
  - "Chain 1 fixed at the projection root, not by filtering: non-dict card values STAY in the entry list as the empty card (key visible, blank axes, value verbatim) — the honest degraded row; the loader's merge of non-dict entries stays exactly as pinned (fail-loud SystemExit contract untouched for pipeline consumers)"
  - "Chain 2 fixed at the one seam both call sites route through: widening _load_entries' tuple (not per-callsite guards) means load_selection_data AND preset_menu inherit the corrupt-JSON degrade with zero further changes"
  - "[Rule 1 deviation] tui/services/selection.py model_presence gained a companion isinstance(card, dict) guard — REQUIRED for the plan's own chain-1 truth: load_selection_data calls model_presence over the merged entries, and a non-dict card previously crashed the presence pass (UNKNOWN = no usable Model_path, the documented branch)"
  - "env_smoke per-entry guards count broken shapes as MISSING (cannot-verify = fail-closed), not as skip — the gate's own philosophy (a registry that cannot be verified is a named failure, and main() stays the only renderer, D-02)"
  - "The env screen's two WR-01 guards live INSIDE the existing exclusive worker shape (D-03: all kernel execution stays in the thread worker); degraded results ride the same CheckItemDone/persist/CheckRunComplete tail so D-05 partial-failure-persists-whole semantics stay uniform"
  - "The AST pin is the authority over the 24-site ledger snapshot: any future @work site it flags must carry the kwarg or the internal guard; the 13 kwarg rows are documented site-by-site in the plan (11 flagged by the pin + app.py run_download_queue per its explicit ledger row — its narrow inner except only guards the pending-scan, not run_task)"
  - "ENV_KERNEL_DEGRADED ('FAIL: kernel raised {error}') is the ONE new strings constant — English technical wording in the env_smoke detail-line vocabulary (data, D-02), FAIL-prefixed so _summary_of's existing strip derives the summary cell with zero render-path changes"
metrics:
  duration: 47 min
  completed: 2026-10-14
status: complete
---

# Phase 08 Plan 08: Gap closure — tolerant-loading crash chains (CR-01 chains 1+2, WR-01, the @work never-exit net) Summary

**One-liner:** The two reproduced registry-input crash chains and the WR-01 broken-checkout boot crash now degrade through their real seams (empty-card rows, SEL_REGISTRY_LOAD_FAILED state rows, named fail-closed env_smoke FAIL lines, degraded env rows) with a structural AST pin holding exit_on_error=False or an internal broad except at every @work site — no worker exception can exit the console through textual 8.2.8's default handler.

Closes the 08-VERIFICATION Truth-6 gap (CR-01, #3304-adjudicated; machine-evidenced at HEAD 0852b53) plus the WR-01 fold-in, so phase re-verification can pass 6/6.

## Tasks Completed

| # | Task | Commit | Outcome |
|---|------|--------|---------|
| 1 | Chains 1+2 — isinstance guards in registries projections + widened _load_entries tuple | RED 87c1458 / GREEN 39505dd | 3 regression tests through the real SelectionBackend seam; loader contract tests byte-unmodified and green |
| 2 | WR-01 — fail-closed env_smoke directory kernels + guarded env-screen worker | RED e65af73 / GREEN e762a42 | 4 degraded-input tests; S1-S4 byte goldens green unmodified (healthy-path stdout untouched) |
| 3 | @work never-exit net — exit_on_error=False ledger (12 remaining sites) + AST structural pin | d6f2a2c (+ docs 514721d) | pin found 24 sites, flagged 11 pre-sweep; 13 total kwarg sites incl. Task-2's env_check; zero worker-body restructuring |

## TDD Gate Compliance

`gsd_run check tdd-red-evidence` is UNAVAILABLE in this executor environment (gsd_run not installed, exit 127), so the machine classifier could not run; per the reference's error-handling path the RED records with real command/exit/output plus semantic assessments are committed at `.planning/tdd-evidence/08-08-task{1,2,3}-red.json` (the 08-07 precedent for in-repo evidence records).

- **Task 1 RED** (`uv run --group dev pytest tests/tui/test_pilot_selection.py -q -k "non_dict_custom_entry or corrupt_official"` → 3 failed): all three target tests failed on the reproduced crash chains themselves — `AttributeError: 'list' object has no attribute 'get'` at `tui/services/registries.py:139` (chain 1, the verifier's exact reproduction) and `json.JSONDecodeError` escaping `_load_entries` at `tui/screens/selection.py:805` and through `load_selection_data` (chain 2). VALID_RED: the behavior under test is "completes without raising"; each failure IS the crash being tested for absence. No fixture/load faults.
- **Task 1 GREEN:** `_project_model_entry`/`_project_dataset_entry` guards + the widened tuple + the model_presence companion guard (Rule-1 deviation, below). Verify lane `tests/tui/test_pilot_selection.py tests/test_registry_loader.py`: **58 passed** (55 baseline + 3 new), loader contract byte-unmodified.
- **Task 2 RED** (two commands, 2+2 failed): kernel tests failed with `JSONDecodeError` escaping the bare `open/json.load` and `AttributeError` at `env_smoke.py:460` (non-dict entry); Pilot tests failed with both `RuntimeError`s escaping the unguarded worker — exactly the WR-01 opening-screen death. The strings constant `ENV_KERNEL_DEGRADED` landed WITH the RED commit as a zero-consumer constant so the failures are behavioral, not import faults. VALID_RED.
- **Task 2 GREEN:** `_read_registry` fail-closed helper + per-entry guards; the two worker guards + `exit_on_error=False`. Verify lane `tests/test_env_smoke_bytes.py tests/tui/test_pilot_env_check.py`: **36 passed** (32 baseline + 4 new; S1-S4 byte goldens green unmodified). Two test-side assertion refinements during GREEN (the corrupt file's actual JSON message wording; the standard scenario's deliberate dataset_dirs FAIL expected alongside the degraded middle row) — test corrections, zero implementation impact.
- **Task 3 RED** (`uv run --group dev pytest tests/tui/test_work_site_hardening.py -q` → 1 failed): the pin's assertion listed exactly the 11 unguarded sites (floor assertion passed first: 24 sites found — non-vacuous). VALID_RED, with one granularity deviation: the RED run was executed against the pre-sweep tree, but the pin and the 12-kwarg sweep landed together in the atomic Task-3 commit d6f2a2c (execution order preserved the discipline; recorded in the evidence JSON).
- **REFACTOR:** none needed — no cleanup opportunities beyond what landed (the shared `_read_registry`/`_degraded_result`/`_project_*` helpers ARE the refactor-level dedup, landed with GREEN).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] model_presence card guard (file outside files_modified)**
- **Found during:** Task 1 GREEN — the required chain-1 test crashed one call deeper than the plan's named site.
- **Issue:** `load_selection_data()` calls `selection_service.model_presence(model_entries, ...)`; its `entry.get("card", {}).get("Model_path")` raised AttributeError on a non-dict card (a truthy list defeats the `or`-free `.get` chain). Without this guard the plan's own truth ("loads through SelectionBackend.load_selection_data() … the projection completes without raising") is unachievable.
- **Fix:** one isinstance(card, dict) guard in `tui/services/selection.py::model_presence` — a non-dict card maps to MODEL_PRESENCE_UNKNOWN (the documented no-usable-Model_path branch). Same root-cause family, one guard, zero behavior change for dict cards.
- **Files modified:** tui/services/selection.py
- **Commit:** 39505dd

**2. [Process] Task 3 commit granularity** — RED run captured pre-sweep but pin+sweep landed in one atomic commit (d6f2a2c) instead of separate RED/GREEN commits as in Tasks 1-2. Documented in `.planning/tdd-evidence/08-08-task3-red.json`.

**3. [Docs] Plan ledger prose typo** — line 169 said "14 decorator sites"; the ledger rows count 13 (12 in Task 3 + env_check in Task 2; verified: 13 `exit_on_error=False` decorators in the tree). Fixed in commit 514721d per the orchestrator's checker note.

**4. [Tooling] gsd_run unavailable** (exit 127) — the TDD red-evidence classifier and the state handler verbs ran manually: evidence records committed under `.planning/tdd-evidence/`, STATE.md updated by direct edit.

Otherwise the plan executed exactly as written (seam choice, guard shapes, ledger decisions, test names and assertions all per spec).

## Verification Evidence

| Check | Command | Result |
|-------|---------|--------|
| Task 1 lane | `uv run --group dev pytest tests/tui/test_pilot_selection.py tests/test_registry_loader.py -q` | 58 passed (was 55) |
| Task 2 lane | `uv run --group dev pytest tests/test_env_smoke_bytes.py tests/tui/test_pilot_env_check.py -q` | 36 passed (was 32; S1-S4 goldens unmodified) |
| Task 3 lane | `uv run --group dev pytest tests/tui/test_work_site_hardening.py -q` | 1 passed (pin green; 24 sites, 13 kwargs + 11 internal-guard rows) |
| Plan full lane | `uv run --group dev pytest tests/tui tests/test_registry_loader.py tests/test_env_smoke_bytes.py -q` | **1 failed / 1058 passed / 9 xfailed** — failure set == baseline exactly (the machine-state storage-overview test + the 9 strict-xfail SVG goldens) |
| Full suite | `uv run --group dev --group tui pytest -q` | **7 failed / 1725 passed / 9 xfailed** — exactly the locked box baseline (6 documented data/schema failures + 1 machine-state + 9 strict-xfail goldens); ZERO new failures |
| Lint | `make lint` | All checks passed |
| Typecheck | `make typecheck` (ty, dev+tui groups) | All checks passed |
| Verifier reproduction 1 (post-fix) | non-dict custom entry via `DNALLMMARK_CUSTOM_REGISTRY_DIR` → `load_model_entries()` | `CHAIN 1 DEGRADED: empty-card entry among 60 entries, no raise` (59 officials + the non-dict custom) |
| Verifier reproduction 2 (post-fix) | corrupt-official loader → `_load_entries(...)` | `CHAIN 2 DEGRADED: [] | error names: …/models_info.json` — the ([], path) state |
| Snapshots prohibition | `git status --short -- tests/tui/__snapshots__/` | clean (untouched; goldens pending maintainer D-03) |
| Prohibition: byte contract | S1/S2/S3 goldens + S4 | green byte-unmodified — only degraded-input branches were added to env_smoke |
| Prohibition: loader contract | tests/test_registry_loader.py | green byte-unmodified (incl. test_non_dict_custom_entry_still_merges_after_skip_filter) |
| Prohibition: @work protocol | diff at the 12 newly-kwarged sites | exactly one decorator argument each; zero worker-body changes beyond the Task-2 env screen guards |

## Known Stubs

None — no stubs, no skipped tests, no unrun verifies. All lanes and gates executed on this box.

## Deferred (recorded, not fixed — executor scope boundary)

Screen-side DIRECT card reads on user-action paths remain unguarded (same non-dict-card family, NOT on the plan's named seams): the wizard modal's observed vocabularies (`_build_wizard_modal`'s `entry["card"].get(...)`), `_manual_landing_path`'s `(entry.get("card") or {}).get("Model_path")`, and `RowDetailModal`'s `self._card.items()` (enter on a degraded row). Reached only by explicit w/d/enter action on a non-dict-card row; the load/projection path the gap's truths cover is closed. Logged to `deferred-items.md` in the phase directory.

## Gap Truths — closure status

- Chain 1: non-dict custom entry loads through `SelectionBackend.load_selection_data()` as the empty-card entry, projection completes without raising — **closed** (test_backend_non_dict_custom_entry_degrades_to_empty_card_never_raises).
- Chain 2: corrupt official registry degrades through `_load_entries` to ([], path); `SEL_REGISTRY_LOAD_FAILED` renders naming the path while the other registry stays healthy; preset_menu inherits — **closed** (test_load_entries_degrades_on_corrupt_official_json, test_backend_corrupt_official_registry_degrades_to_error_state).
- WR-01: env screen survives a broken checkout (raising kernel → one degraded fail row; failing kernels() → every row degrades; neither path exits the console) — **closed** (both Pilot tests, app alive at assert time).
- env_smoke directory kernels fail-closed with named ok=False CheckResults; healthy-path stdout byte-identical — **closed** (S1-S4 goldens green unmodified).
- Never-exit floor: every @work site in tui/ carries exit_on_error=False or an internal except-Exception handler, pinned by the AST structural test — **closed** (test_every_work_site_never_exits_the_console, 24 sites).

Phase 8 Truth 6 can flip to verified on re-verification.

## Self-Check: PASSED

All created/modified files exist on disk; all six commits (87c1458, 39505dd, e65af73, e762a42, d6f2a2c, 514721d) verified as ancestors of HEAD via `git merge-base --is-ancestor`.
