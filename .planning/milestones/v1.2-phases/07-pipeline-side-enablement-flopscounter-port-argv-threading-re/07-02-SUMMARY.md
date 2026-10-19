---
phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
plan: 02
subsystem: pipeline
tags: [registry, overlay, json, custom-entries, xdg, cli]

# Dependency graph
requires:
  - phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
    provides: locked decisions D-01..D-27 (07-CONTEXT.md), the five verified registry load sites, and the Makefile PHASE7_MODULES lint wildcard (07-01 — registry_loader.py joined lint coverage automatically on creation)
provides:
  - pipeline/registry_loader.py — the single official+custom registry overlay seam (custom_registry_dir, load_models_registry, load_datasets_registry)
  - All five registry load sites (run_sweep x3, run_finetune module level x1, audit x1) reading through the merged view — the seam Phase 9 wizards (CUST-01..04, CUST-06) write into
  - tests/test_registry_loader.py — 15 contract tests locking merge, collision fail-fast, fail-loud malformed handling, D-07 resolution order, absent byte-identity, and the run_finetune rewiring source-contract
affects: [07-03 sweep argv threading, 07-04 run_finetune integration, 07-05 legacy deletion, 07-06 GB10 smoke, phase-09 wizards CUST-01..04/CUST-06, phase-08 tui/services, phase-12 monitor]

# Actuals (#2632) — same estimateTokens scale as the plan's estimate (chars/4
# over the realized diff base..HEAD, planning artifacts included).
actuals:
  tokens: 8077
  tasks: 3
  commits: 4

tech-stack:
  added: []  # zero external packages (T-07-SC; stdlib json/os/pathlib only)
  patterns:
    - "overlay seam: official dict object returned as-is when the custom file is absent — identity is object-identity, not just value-equality (byte-identical-when-absent)"
    - "SystemExit-as-builtin: fail-loud errors raise SystemExit directly, keeping the module's import surface at exactly json/os/pathlib"
    - "cross-root importlib.util.spec_from_file_location loader for script/ -> pipeline/ module reuse (run_migration_inventory.py precedent, second consumer)"

key-files:
  created:
    - pipeline/registry_loader.py
    - tests/test_registry_loader.py
  modified:
    - pipeline/run_sweep.py
    - pipeline/run_finetune.py
    - script/audit_n_frequencies.py

key-decisions:
  - "D-07 env-var semantics resolved as WHOLE-DIRECTORY override: DNALLMMARK_CUSTOM_REGISTRY_DIR is used as-is (no dnallmmark suffix appended); the suffix join applies to the XDG_CONFIG_HOME and ~/.config bases only — the must_haves truth ('overrides the entire custom directory'), the original D-07 text (覆盖整个目录), and RESEARCH Pattern 3 ('whole-directory override') all agree; the behavior bullet's 'each joined with dnallmmark' is that same statement's compressed shorthand"
  - "platformdirs refinement recorded (per plan instruction): the hand-rolled env>XDG>home resolver exists because platformdirs is absent from every CPU-side group (GPU-lane transitive only, RESEARCH Pitfall 2) and ROADMAP binding constraint 10 reserves it for Phase 8 [tui]; it yields the identical Linux path and Phase 8 may consolidate behind this same seam"
  - "raise SystemExit(...) instead of sys.exit(...): SystemExit is a builtin, so the module imports exactly json/os/pathlib (the plan's acceptance criterion) while keeping the identical exit semantics"

patterns-established:
  - "Overlay-on-absent identity: absent custom file returns the freshly-loaded official dict untouched; present custom file validates then merges add-only keys with collision fail-fast naming key + both paths"
  - "Env-pinned overlay tests: every test that exercises the loader pins DNALLMMARK_CUSTOM_REGISTRY_DIR via monkeypatch (machine-independent outcomes, Pitfall 3)"

requirements-completed: [CUST-05]

coverage:
  - id: D1
    description: "registry_loader module: D-07 path resolution (env whole-dir override > XDG > ~/.config, suffixed dnallmmark on the two bases), add-only merge, collision fail-fast naming key + both file paths, fail-loud malformed/non-object custom files, uncaught OSError on missing official files"
    requirement: CUST-05
    verification:
      - kind: unit
        ref: "tests/test_registry_loader.py#test_absent_overlay_models_returns_official_dict_verbatim, test_absent_overlay_datasets_returns_official_dict_verbatim, test_custom_models_key_merges_over_official, test_custom_datasets_key_merges_over_official, test_custom_models_key_colliding_with_official_fails_fast, test_custom_datasets_key_colliding_with_official_fails_fast, test_malformed_custom_models_json_fails_loud_naming_file, test_custom_datasets_top_level_not_object_fails_loud_naming_file, test_unreadable_custom_file_fails_loud_naming_file, test_custom_registry_dir_env_var_wins, test_custom_registry_dir_xdg_config_home, test_custom_registry_dir_defaults_to_config_home, test_missing_official_models_file_raises_oserror, test_missing_official_datasets_file_raises_oserror"
        status: pass
      - kind: other
        ref: "uv run --group dev python -c \"import sys; sys.path.insert(0, 'pipeline'); import registry_loader; print(registry_loader.custom_registry_dir())\" -> /home/forrest/.config/dnallmmark"
        status: pass
    human_judgment: false
  - id: D2
    description: "run_sweep's three registry loads (enumerate_matrix / _validate_filters / _load_registry_key_sets) and audit_n_frequencies' main() datasets load rewired through the overlay seam, signatures and --registry-dir semantics unchanged, tolerant-read sites and export_runs.py untouched"
    requirement: CUST-05
    verification:
      - kind: unit
        ref: "uv run --group dev pytest tests/test_sweep.py tests/test_audit_n.py tests/test_registry_loader.py -q -> 99 passed (zero existing-test modifications)"
        status: pass
      - kind: other
        ref: "uv run --group dev python -c \"import sys; sys.path.insert(0, 'pipeline'); import run_sweep; print('sweep-import-ok')\" -> sweep-import-ok"
        status: pass
    human_judgment: false
  - id: D3
    description: "run_finetune module-level loads routed through registry_loader at the exact former position and order with the crash-on-missing import-time contract preserved; exec-extract spans :276-517 byte-unchanged; source-contract test pins the rewiring from source text"
    requirement: CUST-05
    verification:
      - kind: unit
        ref: "uv run --group dev pytest tests/test_run_finetune_contracts.py tests/test_registry_loader.py -q -> 75 passed, zero NameError; tests/test_registry_loader.py#test_run_finetune_module_level_loads_route_through_registry_loader"
        status: pass
      - kind: other
        ref: "uv run --group dev python pipeline/run_finetune.py --help -> usage printed, exit 0 (module-level loads succeed with no custom files present)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Overlay end-to-end semantics proven on the CLI surface: empty overlay dry-run manifest byte-identical to env-unset (today's behavior) at the same output root; a custom model key enumerates into the matrix; a colliding key aborts the sweep naming key + both file paths"
    requirement: CUST-05
    verification:
      - kind: other
        ref: "cmp manifest(empty DNALLMMARK_CUSTOM_REGISTRY_DIR) manifest(env unset) -> identical; dry-run with merge-custom -> cells for m1/m2/m-custom; dry-run with collide-custom -> exit 1, error names 'm1' + custom_models.json + models_info.json"
        status: pass
    human_judgment: false

# Metrics
duration: 11 min
completed: 2026-10-11
status: complete
plan_head_before: f65a6ac96035c952337660920b671ce16cb01400
plan_head_after: 439e871  # last production commit; the docs close-out commit follows this SUMMARY
---

# Phase 7 Plan 02: Registry Overlay (CUST-05) Summary

**Official+custom registry overlay seam: one stdlib-only loader merges user-owned custom_{models,datasets}.json over the official registries with collision fail-fast and fail-loud malformed handling, rewired into all five load sites (run_sweep x3, run_finetune x1, audit x1) — byte-identical when absent, 15 new contract tests, zero existing-test churn**

## Performance

- **Duration:** 11 min (2026-10-11T06:48:47Z → ~07:00Z)
- **Tasks:** 3/3 (Task 1 TDD RED→GREEN, Tasks 2-3 rewiring)
- **Files:** 5 code files (2 created, 3 modified) + this SUMMARY
- **Commits:** 4 (measured `git rev-list --count f65a6ac..HEAD`)

## Accomplishments

- **The overlay seam exists** (`pipeline/registry_loader.py`):
  `custom_registry_dir()` resolves `DNALLMMARK_CUSTOM_REGISTRY_DIR`
  (whole-directory override) > `XDG_CONFIG_HOME` > `~/.config`, the two
  bases joined with `dnallmmark` — hand-rolled, platformdirs deliberately
  absent (it is a GPU-lane transitive only; Phase 8's [tui] group may
  consolidate behind this seam). `load_models_registry` /
  `load_datasets_registry` read the official file with plain
  open+json.load and NO OSError catching (the run_finetune import-time
  contract), then merge the custom overlay add-only: absent → the
  official dict object returned untouched (byte-identical, D-06);
  collision → SystemExit naming the key AND both file paths (D-08);
  malformed/non-object/unreadable custom → SystemExit naming the file
  (T-07-04, 宁可噪声).
- **All five load sites read the merged view**: run_sweep's
  `enumerate_matrix` / `_validate_filters` / `_load_registry_key_sets`
  (signatures unchanged, registry_dir param kept, overlay applies
  uniformly per the flagged D-06-faithful assumption); run_finetune's
  module-level loads at the exact former position and order; the audit
  script's main() via an importlib `spec_from_file_location` helper
  (the `run_migration_inventory.py` cross-root precedent).
- **Zero existing-test churn**: test_sweep, test_audit_n, and
  test_run_finetune_contracts pass UNMODIFIED (99 + 75 across the task
  gates; full fast lane 522 passed / 1 deselected — no regressions).
  `git diff` over the plan range touches no pre-existing test file and
  no `export_runs.py` line (D-09).
- **End-to-end semantics proven on the CLI**: same-output-root dry-run
  manifests are byte-identical between an empty pinned overlay dir and
  the unset env (== today's behavior on this machine, where
  `~/.config/dnallmmark` is absent); a custom model key enumerates into
  the sweep matrix; a colliding key aborts with the clear two-path error.

## Task Commits

Each task was committed atomically (Task 1 as a TDD RED→GREEN pair):

1. **Task 1 RED: 14 failing contract tests + import-only skeleton** —
   `25b239e` (test; all tests fail on planned assertions — equality,
   DID-NOT-RAISE, path inequality — no collection faults)
2. **Task 1 GREEN: overlay loader implementation** — `445724d` (feat;
   14/14 green) — REFACTOR skipped: no behavior-neutral cleanup exists
3. **Task 2: run_sweep x3 + audit x1 rewiring** — `ce0ef51` (feat)
4. **Task 3: run_finetune module-level rewiring + source-contract
   test** — `439e871` (feat)
5. **Plan metadata close-out** — this SUMMARY + STATE/ROADMAP/REQUIREMENTS

## TDD Note (Task 1)

RED evidence persisted at
`.planning/tdd-evidence/07-02-task1-red.json` and validated:
`gsd_run check tdd-red-evidence` → **RED_EVIDENCE_OK**
(`target_test_failed`, junit format — pytest's built-in `--junitxml`;
the first attempt with pytest `-q` text output was rejected as
`INVALID_RED/invalid_record`, unsupported format, so the planned target
test was re-run with the junit reporter per the tdd.md format contract).
Semantic assessment: exactly 1 test executed, it IS the named target
(`test_custom_models_key_merges_over_official`), and it failed inside
the planned merge-assertion logic because the behavior was absent.
GREEN minimal implementation made it pass; REFACTOR produced no commit.

## Files Created/Modified

- `pipeline/registry_loader.py` — the overlay seam (custom_registry_dir,
  load_models_registry, load_datasets_registry; read-only over both
  sides; no cache; stdlib json/os/pathlib only)
- `tests/test_registry_loader.py` — 15 contract tests (14 loader
  contracts + the run_finetune source-contract), every load test pins
  DNALLMMARK_CUSTOM_REGISTRY_DIR
- `pipeline/run_sweep.py` — three load sites + sibling import
- `pipeline/run_finetune.py` — module-level loads + sibling import
  (exec-extract spans untouched)
- `script/audit_n_frequencies.py` — importlib cross-root helper + main()
  datasets load

## Decisions Made

- **D-07 env var = whole-directory override** (no dnallmmark suffix on
  the env value): three authoritative sources agree (must_haves truth,
  D-07's 覆盖整个目录, RESEARCH "whole-directory override"); the plan's
  behavior-bullet shorthand "each joined with dnallmmark" describes the
  two config-home bases. Test
  `test_custom_registry_dir_env_var_wins` pins this reading.
- **platformdirs refinement** documented per the plan's explicit
  instruction: the resolver is hand-rolled because platformdirs is
  undeclared in every CPU-side group (importing it would crash CI) and
  reserved for Phase 8 [tui] by ROADMAP binding constraint 10.
- **`raise SystemExit(...)` over `sys.exit(...)`**: identical semantics,
  zero extra import — the module's import surface stays exactly
  json/os/pathlib as the acceptance criterion requires.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Unreadable custom file would crash with a raw traceback**
- **Found during:** Task 1 (GREEN, error-path coverage)
- **Issue:** the plan names malformed-JSON and non-object-top-level as
  SystemExit cases, but a present-but-unreadable custom file
  (permissions) would raise OSError with a traceback — loud, yes, but
  not the D-08 clear-error discipline every other custom-file failure
  follows.
- **Fix:** the custom-read except extended to `(OSError,
  json.JSONDecodeError)` → SystemExit naming the file.
- **Files modified:** pipeline/registry_loader.py,
  tests/test_registry_loader.py
- **Verification:** `test_unreadable_custom_file_fails_loud_naming_file`
  (chmod 0o000)
- **Committed in:** `445724d`

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** One error-path tightened to match the fail-loud
discipline the plan already mandates for the sibling cases. No scope
creep — no new behavior, surface, or dependency.

## Prohibition Verification (flagged items)

- **Official files never written** — registry_loader.py's only `open()`
  calls are mode `"r"` (two sites); no write/truncate anywhere.
- **Malformed custom never silently ignored** —
  `test_malformed_custom_models_json_fails_loud_naming_file` and the
  non-object variant expect SystemExit naming the file.
- **export_runs.py untouched** — `git diff --name-only` over
  f65a6ac..HEAD shows no export_runs.py change.
- **run_sweep tolerant-read sites untouched** — the run_sweep diff has
  exactly four hunks (import + three load sites); no hunk inside
  `_read_operator_json` (formerly :524-541) or the WR-11 inline read
  (formerly :1105-1130); the WR-11/T-05-09 tests stay green unmodified.

## Issues Encountered

- The first byte-identity `cmp` compared manifests written to two
  different `--output-root` dirs — the manifests record `output_dir`
  paths, so they differed at the path field. Re-run with the same
  output root: byte-identical. (Harness error in the sanity script, not
  a product issue.)
- `gsd_run` is not on this executor's PATH; invoked via
  `bash ~/.claude/gsd-core/bin/gsd_run` (launcher delegates to
  gsd-tools.cjs).

## Advisory Resolution (assumption-delta scan)

The registry identity model this plan establishes: **"the registry" is
the merged view returned by registry_loader** — the official file is
always the base; the custom overlay is optional-by-absence (D-06), never
a second registry callers must know about. The official files remain the
only written source (binding constraint 11). Entry provenance (a visible
custom marker) is deliberately NOT part of the merged dict and lands
with Phase 9's CUST-06. Callers keep consuming one dict — the
singular-to-plural seam closes inside the loader, not at the five call
sites. The flagged assumption (overlay applies uniformly even under a
non-default --registry-dir) is implemented as flagged: uniform, D-06-
faithful; revisit trigger remains "Phase 9 wizards need isolation
semantics".

## Authentication Gates

None — no external services.

## User Setup Required

None — no external service configuration required. (When Phase 9
wizards arrive, custom registries will live at
`~/.config/dnallmmark/custom_{models,datasets}.json`; today that
directory does not exist and behavior is byte-identical.)

## Next Phase Readiness

- 07-03 (PIPE-02 argv threading) proceeds on run_sweep — its registry
  loads now see the overlay; the D-14 subset pre-validation will join
  against the merged view for free.
- 07-04 (run_finetune integration) inherits the module-level loads
  already routed through the seam; the calibration slot and post-success
  write are unaffected by this plan.
- 07-05 (legacy deletion + parity re-pins) and 07-06 (GB10 smoke) are
  unblocked.
- Phase 9 wizards (CUST-01..04, CUST-06) write only user-owned custom
  files; every consumer already reads them through this seam.

---
*Phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re*
*Completed: 2026-10-11*

## Self-Check: PASSED

- All key files exist on disk (2 created + 3 modified + this SUMMARY)
- All 4 commits are ancestors of HEAD (`25b239e`, `445724d`, `ce0ef51`,
  `439e871`); measured `git rev-list --count` from the plan ledger base
  f65a6ac = 4, matching frontmatter
- `gsd_run check evaluation-scope --plan 07-02 --commits-only` resolves
  with 4 commits on this branch
- Plan-level verification re-run green: full plan gate 160 passed
  (test_registry_loader + test_sweep + test_audit_n +
  test_run_finetune_contracts), full fast lane 522 passed / 1 deselected,
  `make lint` exit 0, `make typecheck` exit 0; overlay e2e sanity
  (byte-identity / merge / collision) all green; zero pre-existing-test
  modifications confirmed by `git diff --name-only` over the plan range
