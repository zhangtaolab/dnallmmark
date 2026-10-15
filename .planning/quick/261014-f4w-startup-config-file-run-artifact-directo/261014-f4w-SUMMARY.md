---
phase: quick-261014-f4w
plan: 01
subsystem: pipeline + tui
tags: [startup-config, directories-json, log-dir, directory-picker, storage-overview, textual]
requires:
  - "261014-c2l: the --model_root/--dataset_root underscore family + RunSpec storage roots (the family this plan extends)"
  - "261014-dcl: the run-config-aware env directory kernels + the seeded load_state consumer seam"
provides:
  - "pipeline/directories_config.py — the ONE shared stdlib-only directories.json loader (strict fail-loud + tolerant display twin + effective() precedence merge, flag > file key > default)"
  - "--log_dir end-to-end: run_sweep WR-05 refusal + D-15 resolution + manifest recording + the pinned argv tail --cache_dir/--model_root/--dataset_root/--log_dir -> run_finetune's effective error-log site"
  - "TUI file-awareness: load_state seeds DEFAULTS from directories.json (one seam for env kernels, slot-4 prefill, slot-1 overview)"
  - "save_directory_defaults: the atomic TUI write of the five-key document (same-root pinned against the pipeline read)"
  - "the ctrl+o DirPickerModal (core DirectoryTree, directories only) and the slot-1 five-row storage overview"
affects:
  - pipeline/run_sweep.py (startup read merges the file; --output-root argparse default flips to None with ./finetuned as the effective fallback)
  - pipeline/run_finetune.py (module-top cache-env file branch; effective() unpacks for model_root/dataset_root/output_dir/log_dir; the ./logs site derives from the effective log dir)
  - tests/conftest.py (the autouse DNALLMMARK_TUI_CONFIG_DIR machine-independence pin)
tech-stack:
  added: []
  patterns:
    - "ADD-ALONGSIDE override merging (one effective() seam, default literals stay at consumers — the 261014-c2l discipline)"
    - "textual 8.2.8 probe-pinned seams: filter_paths method for directories-only trees; prevent_default() to win MRO-dispatched private handlers; ctrl+o falls through a focused Input; rich Text spans cannot carry $tokens on the Static path (theme-resolved at render, the nav.py precedent)"
key-files:
  created:
    - pipeline/directories_config.py
    - tests/test_directories_config.py
  modified:
    - pipeline/run_sweep.py
    - pipeline/run_finetune.py
    - tests/conftest.py
    - tests/test_sweep.py
    - tests/test_run_finetune_contracts.py
    - tests/tui/test_snapshots.py
    - tui/services/run_config.py
    - tui/screens/run_config.py
    - tui/screens/env_check.py
    - tui/strings.py
    - tui/styles.tcss
    - tests/tui/test_services_run_config.py
    - tests/tui/test_services_env_check.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_pilot_env_check.py
    - tests/tui/test_strings_phase11.py
    - "tests/tui/test_pilot_{boot,data_manager,matrix,monitor,nav_shell,selection,selection_custom,wizard}.py (env fakes gain storage_rows)"
    - tests/tui/__snapshots__/run_config.svg
    - tests/tui/__snapshots__/env_check.svg
decisions:
  - "F4W-01 precedence implemented ONCE (directories_config.effective) with default literals left at consumers — absent everywhere stays byte-identical (existing default-path tests green unmodified)"
  - "The DEFAULT output_root literal doubles as the unset signal on the SAVE side (an all-defaults save writes five empty strings and loads back as {} — the restore path is 'clear the inputs and save'); the seeding fills output_root only at the DEFAULT literal, the documented str-typed conflation"
  - "The run_finetune module-top cache branch uses the STRICT load (a malformed file aborts the child); the TUI load_state seeding uses the tolerant twin (display degrades, self-heals on the next save)"
  - "Picker enter semantics: collapsed nodes descend, expanded nodes select — implemented by overriding _on_tree_node_selected WITHOUT super plus prevent_default() (probe-pinned: textual dispatches private handlers per MRO class, so the base handler otherwise double-fires and closes the modal on the first enter); auto_expand=False stays as a redundant guard"
metrics:
  duration: 92 min
  completed: 2026-10-14T05:26:02Z
status: complete
actuals:
  tokens: 123567   # chars/4 over the realized diff 28b455a..bc8f36b (SVG goldens included)
  tasks: 3
  commits: 3        # MEASURED: git rev-list --count 28b455a..HEAD
plan_head_before: 28b455a0abf75caea82c7e5e176375561d3f50af
plan_head_after: bc8f36b1766da10b29e3f1c6fc9983bcfc866f94
---

# Phase quick-261014-f4w Plan 01: startup config file + run-artifact directories Summary

One-liner: a shared stdlib-only `directories.json` startup config (flag > file key > default, byte-identical when absent), a `--log_dir` flag threaded run_sweep -> run_finetune's error-log site, TUI file-default seeding + the atomic save seam, a core-DirectoryTree directory picker (ctrl+o), and the slot-1 five-dir storage overview.

## What Was Built

### Task 1 — the shared loader + bare-CLI startup reads + --log_dir end-to-end (tracer)

- `pipeline/directories_config.py` (stdlib json/os/pathlib only): `config_dir()` resolves DNALLMMARK_TUI_CONFIG_DIR (whole-dir, empty=unset) > XDG_CONFIG_HOME/dnallmmark > ~/.config/dnallmmark — the settings.py conventions hand-rolled (D-10 coexistence; platformdirs stays out of the pipeline); `load_directories()` is strict (a present-but-malformed file raises SystemExit naming the path — the T-07-04 fail-loud precedent), `load_directories_tolerant()` is the display twin ({} on any failure), `effective(cli_value, key)` implements the precedence merge; `DIRECTORY_KEYS` is the frozen five-key order every consumer shares.
- `run_sweep`: `--log_dir` joins the underscore family verbatim (empty refusal WR-05 twin, D-15 absolute resolution, sweep_flags manifest recording, the pinned child-argv tail now `--cache_dir/--model_root/--dataset_root/--log_dir`); `main()` reads the file at ONE startup point and computes effective values (`--output-root` argparse default flipped to None with `./finetuned` as the documented fallback, the same `Path(...).resolve()` line over the effective value).
- `run_finetune` (read as source text by tests, never imported): `import directories_config` precedes the cache-env block, which gains the file branch (strict load) between the argv pre-scan and the HF_HOME default; `--log_dir` declared; the `__main__` unpack merges `effective()` for model_root/dataset_root/output_dir/log_dir; the `./logs/` makedirs/open pair became the `log_base` effective form (absent everywhere produces the identical directory and path string).
- `tests/conftest.py`: an autouse `DNALLMMARK_TUI_CONFIG_DIR` pin over `tmp_path_factory` (NEVER the per-test tmp_path — the first draft used tmp_path and broke the exact-listing atomic-write lanes; see deviations) + the same pin in `tests/tui/test_snapshots.py`'s script-mode bootstrap.
- New tier-1 loader suite (23 tests) + sweep family/startup-file lanes + run_finetune source contracts; the machine-independence property proven by running the sweep suite with an ambient planted config env var (137 green).

### Task 2 — RunSpec.log_dir + seeding + the atomic save seam (service tier, TDD)

- `RunSpec.log_dir: str | None = None`; persistence round-trips it; `DirPlan` gains the display/argv twins; `compose_argv` appends `--log_dir` after `--dataset_root` (the tail now matches `run_sweep.build_argv` element-for-element).
- `seed_directory_defaults` (pure) + `load_state()` applies it over `load_directories_tolerant()`: the file seeds DEFAULTS, session state overrides; output_root fills only at the DEFAULT literal. Every load_state consumer (env kernels' root kwargs, slot-4 prefill, slot-1 overview) is file-aware through the one seam.
- `save_directory_defaults(spec, config_path=None) -> Path`: the five-key schema-1 document (resolved-absolute values, "" for unset) through `settings.atomic_write` under `settings.config_dir()/directories.json` — the same-root agreement with `directories_config.config_path()` is test-pinned from both sides.
- `storage_overview()` + `StorageRow`: five DIRECTORY_KEYS-ordered rows with the real-consumer display defaults (pipeline dir for both roots, pipeline/logs, REPO_ROOT/cache) and plain exists stats.

### Task 3 — slot-4 row/save/picker + slot-1 overview (screens + strings + goldens)

- strings: the eight planned CFG_ names + the ENV_STORAGE_* block, all in the bidirectional IN-09 inventory.
- `directory_picker_root(value)`: stripped value -> nearest existing ancestor -> REPO_ROOT (Path.home() last resort documented as unreachable while REPO_ROOT exists), tier-1 tested.
- run_config screen: the log-dir row (label/placeholder/advisory) after the cache row + the dim restore-defaults hint; `[s]` (focus outside an Input) writes the defaults file and toasts the written path (synchronous by design — one deliberate keypress, one atomic two-syscall write; docstring states why the preview worker's rationale does not apply); `ctrl+o` opens `DirPickerModal` only over the five dir inputs (any other focus is a silent no-op; the binding-choice rationale comment records the probe: ctrl+o falls through a focused Input on 8.2.8, a bare letter would type).
- `_DirsOnlyTree` (DirectoryTree subclass): `filter_paths` drops files (probe-pinned mechanism on 8.2.8); enter descends collapsed nodes and selects expanded ones; `[f]` selects the cursor row; both paths funnel into ONE fill-and-close that sets the ORIGIN input's value (firing Input.Changed -> the unchanged preview/persist validation path — no bypass, proven by the persisted state file) and restores focus; esc cancels untouched.
- env_check screen: the read-only storage section (five rows, glyph-first with theme-resolved span colors, path verbatim, the 修改目录请到 4 运行配置 footer), rendered at mount and re-rendered by `[r]`; every env-check/run-config service fake across 14 test files gained `storage_rows`/`save_directory_defaults`.
- Goldens: `run_config.svg` + `env_check.svg` regenerated (the plan-pinned exactly-two expectation), plus `wizard.svg` collateral drift committed per D-03 (recorded in WINDOWS.md).

## Evidence

- `make lint` green; `make typecheck` green.
- Per-task lanes: Task 1 (233 passed), Task 2 (159 passed incl. import lock), Task 3 (245 passed).
- Full `make test`: **exactly the 10 documented pre-existing failures** (5 schemas + 1 determinism stale pins after data commit 9e803ca, 4 root-user chmod persist-failure sims — see the c2l deferred-items.md), 1677 passed, 3 skipped; node lane 26/26 green.
- Acceptance probe (CPU): with `DNALLMMARK_TUI_CONFIG_DIR` at a tmp dir holding all five keys, a bare `run_sweep.py --dry-run` threads the five file values resolved absolute into every manifest cell; with an empty config dir and no flags the manifest carries exactly the five base cell keys (the c2l proof style).
- Machine-independence: the sweep suite green under an ambient `DNALLMMARK_TUI_CONFIG_DIR` pointing at a planted directories.json (the autouse pin wins); the snapshot lane passed 3 consecutive runs after regeneration.
- SVG drift over the whole plan: run_config.svg + env_check.svg (pinned) + wizard.svg (collateral flake, WINDOWS #24).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The conftest autouse pin initially polluted per-test tmp_path**
- **Found during:** Task 1 (full-suite gate)
- **Issue:** The autouse fixture created its pin directory inside pytest's per-test `tmp_path`, breaking the exact-listing assertions (`test_persist_twice_leaves_single_valid_file_no_tmp_residue`, `test_run_quick_check_never_persists`, `test_export_with_zero_customs_toasts_writes_nothing`).
- **Fix:** The pin now uses `tmp_path_factory` (a directory OUTSIDE the per-test tmp_path); docstring records why.
- **Files modified:** tests/conftest.py
- **Commit:** b0644d5

**2. [Rule 2 - Missing functionality] The save-failure toast constant**
- **Found during:** Task 3
- **Issue:** The plan requires the [s] failure to "surface as the error toast (the WR-03 surface)" but its strings list names no failure constant; reusing LNC_LAUNCH_FAILED_TOAST ("launch failed") would be wrong copy.
- **Fix:** Added `CFG_SAVE_DEFAULTS_FAILED_TOAST` ("✗ 保存默认目录失败: {error}") and registered it in the bidirectional IN-09 inventory (nine new CFG_ names total).
- **Files modified:** tui/strings.py, tests/tui/test_strings_phase11.py
- **Commit:** bc8f36b

**3. [Rule 3 - Blocking] Probe-pinned textual 8.2.8 seams the plan's wording had to reconcile with**
- **Found during:** Task 3 development
- **Issue/fixes:** (a) the directories-only mechanism is the `filter_paths` METHOD (no `filter_directories` on 8.2.8); (b) enter fires BOTH the name-based handler per MRO class AND the @on toggle — the override needs `prevent_default()` (without it the modal closed on the first enter; the probe-pinned MRO double-fire lesson); (c) rich Text spans cannot carry `$success`/`$error` on the Static render path (MissingStyle) — the storage glyphs resolve `app.current_theme.success/.error` at render (the nav.py precedent), the footer note uses rich-native dim.
- **Files modified:** tui/screens/run_config.py, tui/screens/env_check.py
- **Commit:** bc8f36b

### Sanctioned amendments of predecessor test literals (source-text pins this plan replaces by design)

- `test_storage_root_unpack_precedes_model_loop` (c2l) now asserts the `directories_config.effective(...)` unpack form; `test_build_argv_threads_storage_roots_as_list_elements` and the absent-flags parametrize extended with `--log_dir`; `test_params_input_values_render_in_export` placeholder count 2 -> 3 (the new log-dir hint). All additive extensions of surfaces this plan explicitly changes; the byte-identity-when-absent lanes stayed green unmodified.

## Known Stubs

None — every surface renders real data (the storage overview stats the real filesystem; the picker browses the real filesystem; no placeholder values flow to any UI render).

## Threat Flags

None — no security-relevant surface beyond the plan's threat_model (T-f4w-01..05 all accepted/mitigated as registered; zero package installs landed).

## Self-Check: PASSED

All key files exist on disk; all three task commits (b0644d5, 18bad38, bc8f36b) are ancestors of HEAD; the measured commit count (3) matches the frontmatter.
