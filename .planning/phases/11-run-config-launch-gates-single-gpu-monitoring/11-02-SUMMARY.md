---
phase: 11-run-config-launch-gates-single-gpu-monitoring
plan: 02
subsystem: tui-services
tags: [run-config, same-source-preview, e2x-gate, typed-phrase, probe-ineligible, argv-composition, cfg, lnc]

requires:
  - phase: 11-01
    provides: run_sweep's config_variant-aware enumerate_matrix/base_model_name signatures + the variant×peft sweep-start refusal this service mirrors as preview problems
  - phase: 08-04
    provides: settings.state_dir + atomic_write (run_config.json XDG persistence)
  - phase: 11-05
    provides: the CFG_/LNC_ copy blocks (the future screen renders; this service stays zero-textual)
provides:
  - tui/services/run_config.py — the slot-4 composition service: RunSpec frozen model (CFG-01 full params), parse_params collect-all machine problems, validate_composition (empty_selection / variant_peft / probe_ineligible), run_config.json XDG persistence (tolerant whole-default load), resolve_dirs DirPlan (D-14 display-repo-relative + argv-absolute), same-source preview via the IMPORTED run_sweep.enumerate_matrix (D-05, cells VERBATIM), load_probe_ineligible read-source extraction (Pitfall 7), official_keys overlay-free fail-closed key sets, is_full_e2x superset predicate (D-02/O4), expected_phrase/phrase_matches exact-match check (D-07), compose_argv + compose_from_failures_argv (D-12 absent parity, D-11)
  - the machine problem vocabulary (7 codes) + DirPlan/PreviewResult/OfficialKeys frozen dataclasses as the 11-06 screen's data contract
affects: [11-03 sweep_launcher (consumes compose_argv verbatim + re-proves phrase_matches before spawn), 11-06 run-config screen (renders PreviewResult/problems/DirPlan; persists via save_state/load_state), 11-07 (E2' modal renders is_full_e2x + diagnostic)]

actuals:
  tokens: 20804   # chars/4 over the realized diff (83216 chars, 2 files)
  tasks: 3
  commits: 6      # measured: git rev-list --count eb75be4..HEAD
plan_head_before: eb75be4c5ff2a9c76fdfa2b72b8df7ae8d1a812f
plan_head_after: 8fe61a2a125e00a5607b58d6dc836801dc434a3a

tech-stack:
  added: []   # stdlib + the existing run_sweep/settings seams only; zero packages installed
  patterns:
    - "same-source service: module-level `import run_sweep` (stdlib-only, headless — D-05); zero enumeration logic copied, cells returned VERBATIM"
    - "read-source-never-import extended into the services tier (PROBE_INELIGIBLE regex extraction; torch at run_finetune's module top)"
    - "fail-closed authorization reference: OfficialKeys carries empty sets TOGETHER with its diagnostic — the predicate can never satisfy itself by vacuity"

key-files:
  created:
    - tui/services/run_config.py
    - tests/tui/test_services_run_config.py
  modified: []

key-decisions:
  - "preview guards the empty selection itself: run_sweep's filters are falsy-semantics (None and [] both mean no-filter), so an empty selection fed straight into enumerate_matrix would silently enumerate the FULL 9300-cell registry — the preview refuses with zero cells + the empty_selection problem (the WR-07 hazard the driver refuses at its own start, mirrored)"
  - "the import-purity probe runs in a fresh `python -I` subprocess: the GB10 dev host's venv holds torch, and the suite process may legitimately carry it by the time the test runs (the env-check kernels import it) — an in-process assert proved nothing about this module"
  - "load_state is whole-default on ANY shape deviation (field-level partial preservation was rejected: a partially-misread spec is worse than an honest reset — the plan's 'missing/corrupt/shape-drift returns the DEFAULT spec' read taken literally)"
  - "official tasks = datasets_info keys with truthy Train only (all 50 today): an untrainable entry can never appear in the matrix, so including it in the reference would make E2' unreachable"
  - "fractions_count is an axis-mode property of the spec (None when the curve lane is off), while models/tasks/seeds counts derive from the enumerated cells (the honest registry intersection — an unknown selection name counts zero)"
  - "requirements CFG-02/CFG-03/LNC-03 left Pending (the 11-01 discipline): this plan delivers their service-tier foundation; the requirement texts describe the screen-visible surface landing in 11-06/11-07"

patterns-established:
  - "empty-falsy-filter guard on every enumeration pass-through (None means all; [] must mean none)"
  - "exact-equality service-tier checks with zero normalization (phrase_matches: no strip/case-fold/prefix)"

requirements-completed: []   # CFG-02/CFG-03/LNC-03 deferred to the screen/launcher plans (see key-decisions)

coverage:
  - id: D1
    description: "RunSpec + params validation + XDG persistence + dirs (Task 1)"
    requirement: CFG-01
    verification:
      - kind: unit
        ref: "tests/tui/test_services_run_config.py (lane 1: 54 tests — defaults, normalization, parse_params codes, composition refusals, persistence round-trip + 10 drift shapes, DirPlan D-14)"
        status: pass
  - id: D2
    description: "Same-source preview + PROBE_INELIGIBLE + E2' + typed phrase (Task 2)"
    requirement: CFG-03
    verification:
      - kind: unit
        ref: "tests/tui/test_services_run_config.py (lane 2: 45 tests — 9-name real-file parity, 2×3×3=18 verbatim cells re-derived through run_sweep, curve 4-tuples, alias cells, overlay-free behavioral pin, fail-closed diagnostics, superset predicate, exact-match phrase)"
        status: pass
  - id: D3
    description: "run_sweep argv composition + absent parity + from-failures (Task 3)"
    requirement: LNC-02
    verification:
      - kind: unit
        ref: "tests/tui/test_services_run_config.py (lane 3: 16 tests — 10-element defaults pin, element-for-element full argv, 7 absent flags, REPO_ROOT-absolute resolution, defensive raise, from-failures shape)"
        status: pass
      - kind: other
        ref: "make test 1379 passed (baseline 1264 + 115) + JS lane; make lint + make typecheck clean"
        status: pass
  - id: D4
    description: "Threat mitigations T-11-02-01..05 (overlay-free keys, fail-closed diagnostics, service-tier phrase, probe parity, tolerant load)"
    requirement: LNC-03
    verification:
      - kind: unit
        ref: "test_official_keys_is_overlay_free / test_official_keys_missing_file_fail_closed / test_is_full_e2x_diagnostic_never_true / test_probe_ineligible_real_file_pinned_to_nine_names / test_load_state_*"
        status: pass

---

# Phase 11 Plan 02: Run Config Service Summary

Landed `tui/services/run_config.py` — the pure brain under the slot-4 screen and the launch gate: XDG-persisted own selection (D-01), the full params model with collect-all machine problems (CFG-01), dirs separation (CFG-02/D-14/D-19), the same-source dry-run preview through the IMPORTED `run_sweep.enumerate_matrix` (CFG-03/D-05), the E2' verdict + exact-match typed phrase (D-02/D-07, LNC-03's structural boundary), the 9-name PROBE_INELIGIBLE read-source extraction (Pitfall 7), and run_sweep argv composition with D-12 absent parity — proven by a 115-test tier-1 suite (TDD RED→GREEN per task, 6 commits).

## What Was Built

### Task 1 — RunSpec + validation + persistence + dirs (commits 016487d RED, 235e40d GREEN)

- Module skeleton in the download_queue idiom: numbered-decision docstring (D-01/D-05/D-07/D-14/D-19 + the O4 superset rationale recorded verbatim), persistence path + tolerance policy declared, zero textual (both tier locks extend automatically by glob).
- `RunSpec` frozen dataclass: sorted-dedup models/tasks/seeds/fractions, seeds default (42, 43, 44), peft/config_variant vocabularies (run_sweep's choices), curve/subset/epochs/EBS, `output_root="./finetuned"`, `dataset_root="./datasets"` (presence/docs only — D-19), `cache_dir=None`.
- `parse_params(raw)`: the four numeric fields parse with run_sweep's own bounds mirrored (never its sys.exit validators) — seeds int-list (dedupe-sort), curve (0,1] (collapse-sort), epochs/EBS int ≥ 1 — each failure one machine problem `("seeds_invalid"|"curve_invalid"|"epochs_invalid"|"ebs_invalid", raw)`; invalid fields contribute no partial.
- `validate_composition(spec, probe_ineligible)`: `("empty_selection", None)`, `("variant_peft", f"{v}+{p}")` for all 3 variants × both adapter modes (the 11-01 driver refusal mirrored), one `("probe_ineligible", model)` per selected frozen name under variant=probe.
- `save_state`/`load_state` over `settings.state_dir()/run_config.json` (schema_version 1, atomic_write): missing/corrupt/schema-drift/any-field-shape-drift → the WHOLE default spec, never raises (10 drift shapes pinned).
- `resolve_dirs` → `DirPlan`: display forms verbatim (repo-relative defaults), argv forms absolute against REPO_ROOT (`REPO_ROOT / value` join — absolute inputs pass through); nonexistent output root advisory-only.

### Task 2 — same-source preview + probe extraction + E2' + phrase (commits 2ca1c1d RED, 9dd98cf GREEN)

- `load_probe_ineligible(source_text)`: regex over the `PROBE_INELIGIBLE = [...]` literal + string-literal scan (the read-source-never-import pattern); `probe_ineligible()` reads the real 9-name frozen list; parity-pinned (both space spellings, evo2/megaDNA, gpn-brassicales, Omni-DNA-700M).
- `preview(spec, registry_dir=None)` → `PreviewResult`: cells are the imported `enumerate_matrix` output VERBATIM with peft/config_variant/fractions threaded (alias cells appear as 11-01's machinery emits them); counts derive from the cells (fractions_count is the spec's axis-mode); problems = the Task-1 composition codes over the REAL frozen names; empty selection previews zero cells (the falsy-filter guard — see Deviations).
- `official_keys(registry_dir=None)` → `OfficialKeys`: direct `json.load` of models_info.json + datasets_info.json (overlay-free — a custom-registry env var provably never joins), tasks trainable-only; any unreadable/shape-invalid file → EMPTY sets + a diagnostic naming the paths.
- `is_full_e2x(spec, official)`: base names (via `run_sweep.base_model_name` strip) ⊇ official ∧ tasks ⊇ official ∧ seeds ≥ 3; a diagnostic-bearing reference NEVER returns True (fail-closed); superset escalation pinned (official ∪ customs still gates — O4).
- `expected_phrase`/`phrase_matches`: exact string equality on `Path(output_root).resolve().name` — no strip/case-fold/prefix, service tier.

### Task 3 — argv composition + full gates (commits 622e2b1 RED, 8fe61a2 GREEN)

- `compose_argv(spec)`: `[sys.executable, run_sweep.py, --models, --tasks, --seeds, --output-root(abs)]` (10 base elements) then present-only pairs in the pinned order `--peft, --config-variant, --curve, --subset_file, --num_train_epochs, --effective_batch_size, --cache_dir`; absent flags contribute ZERO elements; path values absolute before threading; defensive ValueError on empty selection. The full-present argv is pinned element-for-element.
- `compose_from_failures_argv(failures_path, seeds, output_root, peft, config_variant, extra)`: the [r] re-run path (D-11) — resolved failures path, present-only alias pairs, caller `extra` tail; never the full matrix by construction (documented — never subject to the E2' typed gate).
- Gates: `make test` **1379 passed** (baseline 1264 + 115) + node:test JS lane green; `make lint` All checks passed; `make typecheck` All checks passed (transcript).

## Verification Evidence

- `uv run --group dev --group tui pytest tests/tui/test_services_run_config.py -q` → **115 passed** (54 + 45 + 16 across the three lanes).
- `make test` → **1379 passed** + JS 18/18 — green (first run exposed the purity-test shape bug; final run clean).
- `make lint` (ruff) → All checks passed. `make typecheck` (ty) → All checks passed.
- Services locks: `test_import_lock` (textual-free) + `test_services_about` CJK scan extend over the new module automatically — green.
- TDD discipline: each task's suite landed RED first (collection error / 45 failures / 16 failures), then GREEN — 3× RED+GREEN commit pairs.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Correctness] Preview guards the empty selection against run_sweep's falsy-filter semantics**
- **Found during:** Task 2 GREEN run (`test_preview_problems_empty_selection`)
- **Issue:** `enumerate_matrix` treats an empty models/tasks filter as "no filter" (falsy) — an empty selection fed straight in enumerated the FULL registry (558 cells in the test), silently previewing a full sweep the operator did not select (the WR-07 hazard class the driver refuses at its own start).
- **Fix:** `preview` short-circuits an empty selection to zero cells + the `empty_selection` problem (comment cites the falsy-filter semantics).
- **Files modified:** tui/services/run_config.py
- **Commit:** 9dd98cf

**2. [Rule 1 - Test bug] Import-purity probe moved to a fresh `python -I` subprocess**
- **Found during:** Task 3 full-gate `make test` run
- **Issue:** The in-process `assert "torch" not in sys.modules` passed standalone but failed in the full suite — the GB10 dev host's venv has torch installed and earlier suite modules (env-check kernels) legitimately load it; the assertion proved nothing about THIS module's imports.
- **Fix:** The probe now spawns `sys.executable -I -c` with both import roots, asserting torch/dnallm/transformers absent AND `run_sweep` present in the fresh interpreter (the live-probe discipline, deterministic regardless of suite order).
- **Files modified:** tests/tui/test_services_run_config.py
- **Commit:** 8fe61a2

**3. [Rule 1 - Gate fixes] ruff PLW1510/B017/FURB167 + ty read-only frozen dataclass**
- **Found during:** Task 3 `make lint` / `make typecheck`
- **Fix:** explicit `check=False` on the probe subprocess; `FrozenInstanceError` + the 08-01 `setattr`/noqa-B010 precedent for the frozen-mutation test; `re.DOTALL` for the extraction regex.
- **Files modified:** tests/tui/test_services_run_config.py, tui/services/run_config.py
- **Commit:** 8fe61a2

### Implementation Notes (within the plan's own discretion)

- `load_state` is whole-default on ANY field drift (not per-field salvage) — the plan's "returns the DEFAULT spec ... on missing/corrupt/shape-drift" read taken literally; 10 drift shapes pinned including out-of-vocabulary enums and out-of-bounds numerics.
- The full-present argv pin uses a spec with both alias axes set (peft + variant) purely to exercise the element ORDER in one assertion; the composer is mechanical — composition validation and run_sweep's own start-time refusal own rejecting that combo (layering documented in the test).
- `requirements-completed` stays empty: CFG-02/CFG-03/LNC-03 describe screen-visible surface landing in 11-06/11-07 (the 11-01 premature-mark discipline; CFG-01's copy surface was already marked by 11-05's copy contract — not re-litigated here).

## Threat Flags

None — every register entry landed as planned: T-11-02-01 (overlay-free direct json.load, behaviorally pinned), T-11-02-02 (fail-closed diagnostic, vacuity-proof), T-11-02-03 (pure service functions), T-11-02-04 (read-source parity tripwire), T-11-02-05 (tolerant load), T-11-02-06 accepted (preview ~0.002s), SC vacuous (zero installs).

## What 11-03 Can Now Assume

`sweep_launcher` consumes `compose_argv(spec)` / `compose_from_failures_argv(...)` VERBATIM as its LIST argv (element order pinned; every path already absolute, so its pinned cwd cannot diverge), re-proves the gate with `is_full_e2x(spec, official_keys())` + `phrase_matches(typed, output_root)` before spawn (both pure functions, spawner-refusal-proof), and blocks on any `PreviewResult.problems` code or `OfficialKeys.diagnostic` — the machine vocabulary (`PROBLEM_*`, `PEFT_MODES`, `CONFIG_VARIANTS`, `RUN_SWEEP_SCRIPT`, `DEFAULT_REGISTRY_DIR`) is exported for exactly that composition.

## Self-Check: PASSED

- tui/services/run_config.py — FOUND
- tests/tui/test_services_run_config.py — FOUND
- 016487d, 235e40d, 2ca1c1d, 9dd98cf, 622e2b1, 8fe61a2 — all ancestors of HEAD
- Deletion check: no tracked files deleted by any plan commit
- Untracked scan: only the pre-existing `.planning/.gsd-allow-shrink` (present at spawn)
- Ledger: commits measured 6 (`eb75be4..8fe61a2`), no uncommitted code changes
