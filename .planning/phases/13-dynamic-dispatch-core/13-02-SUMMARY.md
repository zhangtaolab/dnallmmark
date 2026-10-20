---
phase: 13-dynamic-dispatch-core
plan: 02
subsystem: infra
tags: [multi-gpu, dispatch, dry-run, golden-manifest, merge-refusal, mode-coexistence, evidence-based]

# Dependency graph
requires:
  - phase: 12-mgpu-static-orchestration
    provides: pipeline/run_sweep_shard.py merge mode + MERGE_ALLOWLIST + the injectable main(spawner, clock) seam, run_sweep dry-run projection (_manifest_payload/_write_json/cell_dir_for)
  - phase: 13-dynamic-dispatch-core plan 01
    provides: pipeline/dispatch_core.py engine (enumeration+validation+lock+ledger), the --mode {static,dispatch} surface, the dispatch_state.json/dispatch_ledger frozen artifacts, the 78-test dispatch+shard suite
provides:
  - "pipeline/dispatch_core.py run_dispatch --dry-run branch: the manifest-shaped plan artifact (static projection verbatim + orchestrator_mode:'dispatch' sweep-flags marker) writing ONLY {root}/sweep_manifest.json"
  - "pipeline/run_sweep_shard.py run_merge evidence-based refusal: _root_has_dispatch_evidence (dispatch_state.json / dispatch_ledger / manifest orchestrator_mode marker) + the named 'dispatch root {path} needs no merge' problem before any copy"
  - "Makefile PHASE13_MODULES existence-guard lint slot for pipeline/dispatch_core.py (Makefile-only; ci.yml byte-identical)"
  - "SC1 closed: dispatch enumeration dry-run-provable (byte-identical goldens + static-union equality); SC4 closed: static byte-identity pins + mixed-mode merge refusal"
affects: [phase-14 MGPU-03/04/05 (state-file rendering, failure re-run over ledger lane flags, verify/cleanup), phase-15 VAL (N=2 smoke), docs/multi-gpu.md Phase 18 DOCS-01 (dispatch-roots-need-no-merge wording)]

# Actuals (#2632) — pairs with the plan's estimate to calibrate future estimates.
# Same estimateTokens scale (chars/4 over the realized diff), never a harness token count.
actuals:
  tokens: 9343   # chars/4 over the 37,375-char diff fea5d8d..e8dfb24 (estimate was 19000)
  tasks: 2
  commits: 2      # MEASURED: git rev-list --count fea5d8d..HEAD

plan_head_before: fea5d8db43bd1f9e926b0f21030271c4574d4f4a
plan_head_after: e8dfb24796265f4747fa3f47fffed50404b0e3ee

# Tech tracking
tech-stack:
  added: []        # zero-dependency plan — Python stdlib + sibling imports only
  patterns:
    - "One manifest shape across modes: the dispatch dry-run projects through run_sweep._manifest_payload/_write_json verbatim (the static dry-run projection, run_sweep.py:1909-1946) — the SC1 union-equality comparison exists BECAUSE both modes share the projection"
    - "Evidence-based mode detection (D13-07): run-recorded markers only (dispatch_state.json, dispatch_ledger dir, the orchestrator_mode manifest cell marker) — never directory-shape inference"
    - "Makefile existence-guard lint extension (PHASE12_MODULES idiom) — new modules join the fixed-findings gate without touching ci.yml"
    - "Lazy dispatch_core import inside run_sweep_shard helpers (the 09-06/main() cycle-breaking precedent) so the evidence helper can reuse the frozen naming constants"

key-files:
  created: []
  modified:
    - pipeline/dispatch_core.py
    - pipeline/run_sweep_shard.py
    - tests/test_dispatch_core.py
    - Makefile

key-decisions:
  - "Dry-run branch position frozen: AFTER enumeration/priority AND after the zero-cell refusal, BEFORE the lock — an empty enumeration refuses identically dry or real (the WR-07 family holds on the planning path too); 13-01's named dry-run refusal is thereby superseded exactly as it staged"
  - "orchestrator_mode:'dispatch' rides the sweep_flags **flags merge into every planned cell (the A7 dry-run-root evidence); real dispatch runs carry dispatch_state.json instead — the merge refusal reads BOTH"
  - "sweep_flags mirrored from run_sweep.main present-keys-only construction verbatim (subset_file/effective_batch_size/num_train_epochs/cache_dir/model_root/dataset_root/log_dir/config_variant); peft does NOT join — it rides the ALIAS identities, only config_variant joins among the two lane axes"
  - "Merge refusal wording pinned: 'dispatch root {path} needs no merge — dispatch mode writes ONE shared root (MGPU-06)' — appended to the collect-all problems list for the base root AND each existing worker root, BEFORE any copy"
  - "_root_has_dispatch_evidence fail-open direction: absent/unreadable manifest carries no marker — absence of every marker IS the static world (T-13-08 accept); a root carrying any marker IS a dispatch root by definition"
  - "PHASE13_MODULES is a Makefile-only extension; the scratch-run F401 probe (unused import -> ruff flags -> revert -> re-clean) proves the slot actually gates pipeline/dispatch_core.py"

patterns-established:
  - "SC1 golden discipline: byte-identity via copy-aside + sha256 between consecutive dry-runs; cross-mode equality over (model, task, seed[, fraction]) identity tuples ONLY — never absolute output_dir paths (worker roots vs the shared root differ by design)"
  - "Tee-log byte-identity comparison normalizes the BASE-ROOT NAME out of the filename (the log is a sibling of the root, so its name embeds it by design) — the argv/kwargs normalization idiom extended to on-disk artifacts"

requirements-completed: [MGPU-01, MGPU-06]

# Coverage metadata (#1602) — one entry per shipped deliverable.
coverage:
  - id: D1
    description: "Dispatch dry-run plan artifact (SC1): writes ONLY {root}/sweep_manifest.json with the static projection shape (matrix sorted unions + status 'planned' cells at cell_dir_for paths) plus orchestrator_mode 'dispatch' merged into every cell; byte-identical across runs; identity set equals the static per-worker dry-run union; priority reorder permutes the queue without changing the set; peft rides alias identities while config_variant joins every cell"
    requirement: MGPU-01
    verification:
      - kind: unit
        ref: tests/test_dispatch_core.py#test_dispatch_dry_run_writes_only_plan_manifest
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_dispatch_dry_run_is_byte_identical_across_runs
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_dispatch_dry_run_identity_set_equals_static_union
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_dispatch_dry_run_priority_reorders_planned_cells
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_dispatch_dry_run_peft_alias_and_variant_flag_shapes
        status: pass
    human_judgment: false
  - id: D2
    description: "Evidence-based merge refusal (MGPU-06 / T-13-06): the helper reads ONLY the three run-recorded markers; the refusal fires in run_merge's collect-all stage for the base root or any existing worker root, BEFORE any copy, with the named problem; static no-evidence merge behavior untouched (control)"
    requirement: MGPU-06
    verification:
      - kind: unit
        ref: tests/test_dispatch_core.py#test_root_has_dispatch_evidence_marker_matrix
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_merge_refuses_dispatch_state_evidence_at_base
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_merge_refuses_worker_root_ledger_evidence
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_merge_refuses_dry_run_marker_only_evidence
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_merge_happy_path_control_without_evidence
        status: pass
    human_judgment: false
  - id: D3
    description: "Static byte-identity + combo refusal adjacency (SC4): explicit --mode static produces the identical captured argv (worker roots included), spawn kwargs, and tee-log names as the default launch; --mode dispatch + --merge refuses with the 13-01 named problem before any root write"
    requirement: MGPU-06
    verification:
      - kind: unit
        ref: tests/test_dispatch_core.py#test_static_mode_explicit_pins_argv_roots_and_logs
        status: pass
      - kind: unit
        ref: tests/test_dispatch_core.py#test_dispatch_merge_combo_refusal_reasserted
        status: pass
      - kind: unit
        ref: tests/test_sweep_shard.py (the 49-test static suite passed UNMODIFIED — the byte-identity tripwire)
        status: pass
    human_judgment: false
  - id: D4
    description: "Makefile PHASE13_MODULES lint slot: pipeline/dispatch_core.py joins the fixed-findings list via the existence-guard idiom; ci.yml byte-identical (blob-hash pinned)"
    requirement: MGPU-06
    verification:
      - kind: gate
        ref: "make lint — expanded file list includes pipeline/dispatch_core.py; scratch-run F401 probe ('import xml.sax' -> 'F401 xml.sax imported but unused', exit 2) then reverted and re-run clean"
        status: pass
      - kind: gate
        ref: "test \"$(git hash-object .github/workflows/ci.yml)\" = 33d2252eb594e0faecece9e8015a332d8d6479ef — equal at both task commits"
        status: pass
    human_judgment: false

# Metrics
duration: 46min
completed: 2026-10-20
status: complete
---

# Phase 13 Plan 02: 动态调度核心 (Dynamic Dispatch Core) Summary

**Mode coexistence + dry-run provability: dispatch `--dry-run` plans through run_sweep's own manifest projection (byte-identical goldens, static-union equality), `--merge` refuses dispatch-evidence roots by name before any copy, static mode pinned byte-identical behind `--mode static`, and the engine joins the lint gate via a Makefile-only PHASE13 slot — zero CI changes**

## Performance

- **Duration:** 46 min (04:37–05:23 UTC; ~32 min of it the full `make test` lane)
- **Tasks:** 2/2
- **Files modified:** 4 (0 created; +660/−9 lines)

## Accomplishments
- `pipeline/dispatch_core.py` — the dry-run branch of `run_dispatch`: 13-01's named dry-run refusal removed and replaced by the planning artifact; branches after enumeration/priority + the zero-cell refusal and before the lock; builds matrix + planned_records EXACTLY as the static dry-run does (`status: "planned"`, `output_dir` via `run_sweep.cell_dir_for`) and writes via `run_sweep._write_json(root/MANIFEST_NAME, run_sweep._manifest_payload(...))`; the sweep_flags dict mirrors `run_sweep.main`'s present-keys-only construction verbatim PLUS `"orchestrator_mode": "dispatch"`; prints the static `[Dry-run]` planned-count line prefixed `[Dispatch]`; returns with NO lock, NO state file, NO claims, NO tees, NO spawns (module + `run_dispatch` docstrings updated to the new protocol shape)
- `pipeline/run_sweep_shard.py` — `_root_has_dispatch_evidence(path)` (lazy `dispatch_core` import, the cycle precedent): True iff `dispatch_state.json` is a file OR `dispatch_ledger/` is a dir OR `sweep_manifest.json` parses with any cell carrying `orchestrator_mode == "dispatch"` (absent/unreadable/non-object/cells-not-a-list = no marker); `_dispatch_merge_refusal(path)` builds the pinned wording; `run_merge` appends the problem for the base root and each existing worker root in the collect-all stage, before `if problems: sys.exit(...)` — `MERGE_ALLOWLIST`, the copy pass, and all no-evidence static behavior untouched; `run_merge` docstring extended
- `Makefile` — `PHASE13_MODULES := $(foreach s,pipeline/dispatch_core.py,$(if $(wildcard $(s)),$(s)))` beside PHASE12_MODULES with a section-style comment; `$(PHASE13_MODULES)` appended to the lint target's file list; nothing else changed, ci.yml untouched
- `tests/test_dispatch_core.py` — 12 new tests (5 SC1 dry-run + 7 mode-coexistence): writes-only-manifest + the full no-side-effects set, copy-aside sha256 byte-identity, static-union identity equality over LPT shards, priority reorder with set-stability, peft-alias/probe-variant flag shapes, the evidence-marker matrix, mixed-mode refusals (base state file / worker ledger / dry-run-marker-only), the static argv/worker-root/tee-log byte-identity pin, the combo-refusal re-assertion, and the merge happy-path control

## Task Commits

Each task was committed atomically:

1. **Task 1: Dispatch dry-run plan artifact + SC1 golden tests** - `a10cef1` (feat)
2. **Task 2: Merge refusal (evidence-based) + static byte-identity pins + Makefile lint line + full gates** - `e8dfb24` (feat)

**Plan metadata:** (this commit — docs: complete plan)

## Verification Evidence
- `.venv/bin/python -m pytest tests/test_dispatch_core.py tests/test_sweep_shard.py -q` → **90 passed** (78 pre-existing + 12 new; the 49-test shard suite passed UNMODIFIED — the static byte-identity tripwire)
- `make lint` → "All checks passed!" — the expanded ruff file list now includes `pipeline/dispatch_core.py`; **scratch-run probe**: a deliberate unused import (`import xml.sax`) made `make lint` fail with `F401 xml.sax imported but unused` (exit 2), then the probe was reverted and lint re-ran clean (the slot provably gates the module)
- `make typecheck` → "All checks passed!" (ty covers pipeline/ incl. the new branch + helper)
- ci.yml zero-change pin → `git hash-object .github/workflows/ci.yml` = `33d2252eb594e0faecece9e8015a332d8d6479ef` (equals the plan-time baseline; `git diff fea5d8d..HEAD -- pipeline/run_sweep.py pipeline/run_finetune.py tests/test_sweep_shard.py .github/workflows/ci.yml` is EMPTY — every frozen surface byte-untouched)
- `make test` (full CPU suite, run after both commits) → pytest lane: **`7 failed, 2030 passed, 3 skipped in 1945.18s`**. ALL 7 failures are pre-existing/environmental and provably outside this plan's blast radius (none import or exercise any file this plan changed):
  - 6 × the documented root-user chmod artifacts — persist-failure simulations via `state.chmod(0o500)` are ineffective when pytest runs as root on this box (`tests/tui/test_services_download_queue.py` ×5, `tests/tui/test_pilot_data_manager.py` ×1 — the user-memory environmental note)
  - 1 × `tests/tui/test_services_about.py::test_derive_about_data_default_root_is_the_repo_pyproject` pins `software_version == "1.2.0"` while `pyproject.toml` is `1.3.0` — stale since the v1.3 bump (commit `9a39bde`, verified an ancestor of the plan base `fea5d8d`, so it fails with or without this plan)
  - Both items are logged in `.planning/phases/13-dynamic-dispatch-core/deferred-items.md`; the recorded baseline-count drift (2F/1919P at 261018-kvj → 7F/2030P observed) is noted there for the maintainer. Re-baselining is deliberately NOT done by an executor (the 261018-kvj precedent)
  - node lane: pytest's non-zero exit stopped `make` before it, so it was run directly → `node --test tests/js/*.test.js`: **26 pass / 0 fail**

## Files Created/Modified
- `pipeline/dispatch_core.py` - the `run_dispatch` `--dry-run` branch (+91 lines incl. docstring updates; the 13-01 refusal block removed)
- `pipeline/run_sweep_shard.py` - `_root_has_dispatch_evidence` + `_dispatch_merge_refusal` + the run_merge collect-all insertion (+83 lines; docstring extended)
- `tests/test_dispatch_core.py` - 12 new tests + helpers (`_read_manifest`, `_manifest_identities`, `_write_static_worker`) (+486 lines)
- `Makefile` - PHASE13_MODULES variable + lint-list append (+9 lines)

## Decisions Made
- Dry-run branch position: after the zero-cell refusal, before the lock — an empty enumeration refuses identically dry or real (never a silent empty plan manifest, never a full-registry fallback)
- `orchestrator_mode: "dispatch"` rides the sweep_flags merge (A7): every planned cell carries it; it is the ONE marker a dry-run root ever has, and the merge refusal reads it
- The evidence helper uses the lazy `dispatch_core` import so the frozen naming constants (`DISPATCH_STATE_NAME`, `LEDGER_DIR_NAME`) keep ONE authority (the constants stay pinned by the 13-01 naming tests)
- Static byte-identity comparison normalizes the base-root name out of tee-log filenames (the log is a sibling of the root by design — raw-name comparison across two launch dirs was the one auto-fixed defect, see Deviations)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test fixture] Static byte-identity log-name comparison needed root-name normalization**
- **Found during:** Task 2 (first verification pass — 1 failed, 89 passed)
- **Issue:** The new byte-identity test compared tee-log FILENAMES raw across two launches, but the tee log is a SIBLING of the base root so its filename embeds the base-root name (`finetuned-default-...` vs `finetuned-explicit-...`) — the launches necessarily use different roots, so raw names can never be equal.
- **Fix:** Compare `log.name.replace(base_name, "ROOT")` on both sides (the same normalization the argv/kwargs comparison already applies); assertion documents why the name embeds the root. Test-only change; zero production impact.
- **Files modified:** tests/test_dispatch_core.py
- **Verification:** 90 passed on re-run
- **Committed in:** e8dfb24 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1, test-only)
**Impact on plan:** None on scope — the plan's byte-identity contract is now pinned correctly.

## Issues Encountered
- `make test` pytest lane reports 7 pre-existing/environmental failures (root-chmod ×6, stale version pin ×1) — all proven to predate the plan base and unrelated to the diff; logged to `deferred-items.md`, NOT fixed (scope boundary). Everything this plan owns is green: 90/90 targeted, lint, typecheck, node 26/26.

## User Setup Required
None - no external service configuration required.

## Known Stubs
None - every code path is real; no placeholder/TODO/fixtures left behind.

## Threat Flags
None - no security-relevant surface beyond the plan's threat model. The T-13-06 mitigation (merge refusal before any copy) and T-13-07 mitigation (`status: "planned"` never-terminal + no run_record.json on dry-run roots) landed exactly as registered.

## Next Phase Readiness
- Phase 14 (MGPU-03/04/05) consumes the ledger lane flags + `dispatch_state.json` counts unchanged; its verify/cleanup tooling can treat `orchestrator_mode` manifest cells as planned-not-executed (the scanner's never-terminal semantics already hold)
- Phase 15's N=2 real-GPU smoke can add `--dry-run` pre-flight checks to the dispatch launch runbook (the plan artifact now exists)
- docs/multi-gpu.md (Phase 18 DOCS-01) documents the dispatch-roots-need-no-merge wording already enforced by the refusal
- Deferred (deferred-items.md): the stale v1.2.0 about-version pin and the baseline-count drift are maintainer-owned

## Self-Check: PASSED

- pipeline/dispatch_core.py — FOUND (modified, committed a10cef1/e8dfb24)
- pipeline/run_sweep_shard.py — FOUND (modified, committed e8dfb24)
- tests/test_dispatch_core.py — FOUND (modified, committed a10cef1/e8dfb24)
- Makefile — FOUND (modified, committed e8dfb24)
- .planning/phases/13-dynamic-dispatch-core/13-02-SUMMARY.md — FOUND
- Task 1 commit a10cef1 — FOUND (ancestor of HEAD)
- Task 2 commit e8dfb24 — FOUND (ancestor of HEAD)
- commits measured from the ledger: `git rev-list --count fea5d8d..HEAD` = 2 (matches `actuals.commits`)

---
*Phase: 13-dynamic-dispatch-core*
*Completed: 2026-10-20*
