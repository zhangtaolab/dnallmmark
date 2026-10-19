---
phase: 10-data-manager-downloads-verification
plan: "07"
subsystem: testing
tags: [tui, download-queue, run-config, tdd, gap-closure, cr-01]

requires:
  - phase: 10-data-manager-downloads-verification
    provides: the download queue, the run-config service chain, and the env-check dataset_dirs kernel whose landing/consumption agreement this plan restores
provides:
  - the CR-01 reroute — the queue's dataset landing base resolves through resolve_dirs(load_state()).dataset_root_abs (the _models_base twin), identical to every consumption side
  - three _cr01 agreement regression tests pinning the verifier's three-configuration repro matrix
  - the module state-root hermeticity pin in the queue test autouse fixture
affects: [phase-10 re-verification (DATA-01 unblocked), download-queue landing legs, slot-4 configured-root operators]

actuals:
  tokens: 2941
  tasks: 1
  commits: 2
plan_head_before: b14339b5df8387d1756966cc51d77cb6d9450c3a
plan_head_after: 45d321167371ef23dbec159b5ea31200be125ffb

tech-stack:
  added: []
  patterns:
    - "landing/consumption agreement via ONE shared chain — the helper-funnel reroute precedent (a second application of _models_base's twin treatment, now covering every dataset landing leg at once)"

key-files:
  created: []
  modified:
    - tui/services/download_queue.py
    - tests/tui/test_services_download_queue.py

key-decisions:
  - "CR-01 fix shape: _datasets_base keeps the constructor-param tier first, then reads run_config.resolve_dirs(run_config.load_state()).dataset_root_abs per call (never memoized — a live slot-4 edit must steer the next landing), falling back to repo pipeline/ unchanged; the directories.json file tier survives INSIDE the chain via load_state's seed_directory_defaults (session state overrides file defaults)"
  - "Hermeticity: the module autouse fixture now pins BOTH roots (config + state) — after the reroute every _datasets_base() call reads settings.state_dir()/run_config.json and the maintainer box carries a live one; explicit in-test pin_state_dir calls still override"

patterns-established:
  - "Agreement-matrix regression tests: pin landing-base == consumption-base through the real run_config services (state written via the service's own save_state, never hand-composed JSON) across the divergence repro configurations"

requirements-completed: [DATA-01]

coverage:
  - id: D1
    description: "The queue's dataset landing base agrees with the consumption base (env-check dataset_dirs kernel + compose_argv --dataset_root) across spec-without-file, relative-file-value, and the aligned default — the three _cr01 agreement tests through the real run_config services"
    requirement: DATA-01
    verification:
      - kind: unit
        ref: "tests/tui/test_services_download_queue.py::test_datasets_base_agrees_with_consumption_spec_without_file_cr01"
        status: pass
      - kind: unit
        ref: "tests/tui/test_services_download_queue.py::test_datasets_base_agrees_with_consumption_relative_file_value_cr01"
        status: pass
      - kind: unit
        ref: "tests/tui/test_services_download_queue.py::test_datasets_base_agrees_with_consumption_default_control_cr01"
        status: pass
    human_judgment: false
  - id: D2
    description: "L6H-03 semantics survive the reroute — the four existing pins green and byte-unmodified; queue module lane fully green (195 passed)"
    requirement: DATA-01
    verification:
      - kind: unit
        ref: "tests/tui/test_services_download_queue.py full module lane — 195 passed in 0.70s (four L6H-03 pins included, git-diff-proven byte-unmodified)"
        status: pass
    human_judgment: false

duration: 9min
completed: 2026-10-14
status: complete
---

# Phase 10 Plan 07: CR-01 Gap Closure (datasets_base run-config reroute) Summary

**Rerouted the download queue's dataset landing base through the same run-config chain every consumption side reads (the `_models_base` twin), closing the SC1 env-check conjunct: downloads now land exactly where the env kernel and the launched sweep read them, under every configuration.**

## Performance

- **Duration:** ~9 min (15:41–15:50 UTC, code + gates; full-suite run included)
- **Commits:** 2 (RED `b6e019e`, GREEN `45d3211`)

## TDD Evidence

### RED (commit b6e019e)

The three `_cr01` agreement tests added to the L6H-03 section; the module autouse fixture extended with the state-root pin in the same change. Modes 1 and 2 failed under the pre-reroute code — exactly the verifier's reproduced divergence:

```text
tests/tui/test_services_download_queue.py::test_datasets_base_agrees_with_consumption_spec_without_file_cr01
E   AssertionError: assert PosixPath('/home/forrest/Github/dnallmmark/pipeline') == PosixPath('/tmp/pytest-of-forrest/pytest-482/test_datasets_base_agrees_with0/sweep-data')

tests/tui/test_services_download_queue.py::test_datasets_base_agrees_with_consumption_relative_file_value_cr01
E   AssertionError: assert PosixPath('/tmp/pytest-of-forrest/pytest-481/test_datasets_base_agrees_with1/rel-ds') == PosixPath('/home/forrest/Github/dnallmmark/rel-ds')
```

Mode 1 (spec-without-file): the base answered repo `pipeline/` while consumption answered the configured root. Mode 2 (relative file value, CWD != repo): the base answered `<CWD>/rel-ds` while consumption answered `REPO_ROOT/rel-ds`. The control (aligned default) passed before the fix, as the plan requires — it pins byte-identity, not divergence.

### GREEN (commit 45d3211)

The one-helper reroute in `tui/services/download_queue.py::_datasets_base` — the exact `_models_base` twin:

```python
if self._dataset_root is not None:
    return self._dataset_root
dirs = run_config.resolve_dirs(run_config.load_state())
if dirs.dataset_root_abs:
    return Path(dirs.dataset_root_abs)
return self._pipeline_dir
```

Supporting edits: constructor `dataset_root` docstring ("file tier > repo default" → "run-config tier > repo default"), section banner ("param > file > default" → "param > run-config > default"), docstring rewritten to the new precedence mirroring the `_models_base` rationale verbatim in spirit ("exactly the chain the env-check dataset_dirs kernel and compose_argv's --dataset_root consume, so download landing and the configured run can never disagree about the root"), the directories.json seeding explained WITHOUT naming the tolerant-loader function, and the now-unused `import directories_config` removed (its only consumer was the retired direct read).

### REFACTOR

None needed — the reroute is itself the minimal-shape fix; no cleanup remained after GREEN.

## Landing-Leg Coverage Proof

All six dataset landing legs already route through the single `_datasets_base()` helper, so the one reroute covers every leg at once (line numbers at the GREEN commit):

| Leg | Site |
|-----|------|
| Landing gate (`_landing_details` relative naming) | tui/services/download_queue.py:2121 |
| Shape-C rename | tui/services/download_queue.py:2150 |
| Zenodo extract target | tui/services/download_queue.py:2326 |
| Landed-keys scan | tui/services/download_queue.py:2397 |
| Reconcile staged `Dataset_path` absolutization | tui/services/download_queue.py:2465 |
| ChannelSpec `local_dir` derivation | tui/services/download_queue.py:2915 |

## Gates (all green)

| Gate | Result |
|------|--------|
| Queue module lane | `195 passed in 0.70s` (192 pre-existing + 3 new; the four L6H-03 pins included and byte-unmodified — every removed test-file line across both commits is an import/banner/fixture-docstring line, zero pin-body lines) |
| Structural gate 1 | `! grep "^import directories_config" tui/services/download_queue.py` → PASS |
| Structural gate 2 | `! grep "load_directories_tolerant" tui/services/download_queue.py` → PASS (docstring names no tolerant-read function; all file awareness flows through `load_state()`) |
| ruff | `make lint` — All checks passed |
| ty | `make typecheck` — All checks passed |
| Full suite | `7 failed, 1734 passed, 9 xfailed in 287.01s` — exactly the recorded box baseline (7/1731/9) + this plan's 3 new tests; the 7 failing IDs re-run in isolation and confirmed byte-identical to the recorded pre-existing set (test_determinism::test_chain_is_deterministic_and_matches_committed; test_schemas::test_committed_file_matches_schema[path29/30/31]; test_schemas::test_schema_bucket_counts_are_pinned; test_schemas::test_dataset_enums_match_committed_data_across_all_schemas; test_services_run_config::test_storage_overview_defaults_mirror_real_consumers) — none in tests/tui/test_services_download_queue.py |

## Deviations from Plan

None — plan executed exactly as written. No WR-01/WR-02/IN-01/IN-02 scope touched (all four remain disposition-open in 10-REVIEW-DISPOSITION.md for the maintainer's separate advisory fix queue); zero changes to strings.py, Pilot tests, snapshots, pipeline/, uv.lock, pyproject.toml; no new dependencies.

## Scope Verification

- The four L6H-03 pins (`test_file_dataset_root_redirects_spec_local_dir_and_gate_naming`, `test_constructor_dataset_root_beats_file_key`, `test_absent_param_and_file_keep_repo_pipeline_datasets_form`, `test_corrupt_directories_json_degrades_to_repo_default`) — green, byte-unmodified.
- The state-root hermeticity pin lives in the module autouse `_pin_directories_config` fixture (both `DNALLMMARK_TUI_CONFIG_DIR` and `DNALLMMARK_TUI_STATE_DIR` pinned to separate `tmp_path_factory` dirs); explicit in-test `pin_state_dir` calls override it and keep working.

## Self-Check: PASSED

- `tui/services/download_queue.py` — FOUND (modified, committed 45d3211)
- `tests/tui/test_services_download_queue.py` — FOUND (modified, committed b6e019e)
- `b6e019e` ancestor of HEAD — FOUND
- `45d3211` ancestor of HEAD — FOUND

## Notes for Re-verification

- SC1's env-check conjunct is mechanically restored: landing base == consumption base across the verifier's exact repro matrix (the three `_cr01` tests ARE the matrix, through the real `run_config` services).
- DATA-01 is unblocked for re-verification; the 10-VERIFICATION.md frontmatter `gaps:` entry can be retired on the next verification pass.
- The live GB10 smoke (ENV_ROUTE loop closure under a configured root) remains the human-verification item noted in 10-VERIFICATION.md — the env-check flip half is now meaningful under a CONFIGURED root too.
