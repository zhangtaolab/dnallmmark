---
phase: 09-custom-model-dataset-onboarding
plan: 09-02
subsystem: tui/services gauntlet orchestration + pipeline registry_loader (the one pipeline change)
tags: [gauntlet, dry-run-precheck, audit-reconciliation, subprocess, enabled-skip, custom-registry]
requires:
  - "09-01 custom_entries store (existing-custom read seam + KIND vocabulary + land discipline)"
  - "Phase 7 registry overlay seam (registry_loader, DNALLMMARK_CUSTOM_REGISTRY_DIR whole-dir override)"
  - "Phase 7 run_sweep --dry-run pure-planning path + sweep_manifest.json contract (D-06 mechanism)"
  - "script/audit_n_frequencies.py kernels + --registry-dir/--datasets-root/output flags (D-07 kernel reuse)"
  - "Phase 8 settings.atomic_write + artifact_loader None-sentinel tolerant reads"
provides:
  - "GauntletService.dry_run_precheck: the D-06 leg — staged overlay (existing customs + candidate forced enabled:true), LIST argv, artifact-based verdict (planned cells naming the candidate)"
  - "GauntletService.audit_reconciliation: the D-07 leg — candidate-only temp registry with absolutized Dataset_path, all-temp output flags, declared-vs-measured reconciliation from parsed n_audit.json"
  - "GauntletService.reconcile(kind, ...): the kind-aware 09-05 panel entry point (models 1 leg, datasets 2 legs, one run_id)"
  - "GauntletItem (run_id/kind/leg/name/ok/details/raw_output): the WR-02 tag-and-drop data contract the 09-05 gauntlet panel renders from GAUNTLET_* strings"
  - "D-09 loader-level enabled:false skip in registry_loader._load_registry (the phase's only pipeline change)"
affects:
  - "every registry consumer (run_sweep/run_finetune/audit/export) now skips enabled:false custom entries"
  - "09-03/09-05 screens consume reconcile + GauntletItem; 09-06 management view must read past the skip via custom_entries.read_entries (Pitfall 7, already landed)"
actuals:
  tokens: 17965
  tasks: 3
  commits: 6
plan_head_before: fcce0cd9f9f382bd2cc3e5cb4d1d41ece78d480e
plan_head_after: bf4b630e23429bc97b6a91048b9cfed8bfcafa8c
tech-stack:
  added: []  # zero new packages (T-09-SC: both subprocess targets are in-repo stdlib scripts)
  patterns:
    - "injectable subprocess runner seam (fakes record argv/env/timeout; real lane proves the leg end-to-end CPU-only)"
    - "verdict-from-parsed-artifacts, never exit codes alone (manifest planned cells / n_audit fields)"
    - "double isolation for the audit leg (candidate-only registry dir + empty overlay env dir)"
key-files:
  created:
    - tui/services/gauntlet.py
    - tests/tui/test_services_gauntlet.py
  modified:
    - pipeline/registry_loader.py
    - tests/test_registry_loader.py
key-decisions:
  - "D-09 filter = skip iff isinstance(entry, dict) and entry.get('enabled') is False: the isinstance guard preserves the pre-D-09 merge of non-object entry values (an entry with no dict shape has no enabled field — an AttributeError there would be a new crash on formerly accepted input); skip sits after the collision loop so disabled shadow attempts still fail fast"
  - "Counterpart resolution is read-time deterministic, never hardcoded: first official datasets key in file order with truthy Train (model candidates) / first official models key (dataset candidates), read DIRECTLY from the official files so overlay state can never leak a custom key into the counterpart slot"
  - "Corrupt existing-custom registry = failed gauntlet item launching nothing (silently dropping existing customs from staging would let a dry-run pass while the real pipeline fail-louds on the same file)"
  - "Detail tokens are data (planned_cells=N, train_rows=N, unified_eval_n=N, Train_mismatch_declared=N_measured=M) — zero copy in the service, zero f-strings (the plan's shell/string-interpolation grep gate pins the module)"
  - "audit leg absolutizes the landed pipeline-relative Dataset_path via pathlib resolve against pipeline/ (Pitfall 3) and pins DNALLMMARK_CUSTOM_REGISTRY_DIR to an EMPTY temp dir (Pitfall 2) — the operator's real custom dir is never merged into the audit registry view"
  - "reconcile runs both legs sequentially regardless of dry-run outcome — landing-after-all-pass is the caller's act through custom_entries.land (D-08); the gauntlet itself never writes user state"
patterns-established:
  - "GauntletItem + injectable runner = the tier-1 subprocess-orchestration shape later phases (data-manager downloads, run-config smoke) reuse"
  - "_invoke absorbing timeout/crash into (proc, failure-details) tuples — no exception ever crosses a service boundary into a panel worker"
requirements-completed: [CUST-04, CUST-06]
coverage:
  - id: D09-SKIP
    description: "Loader-level true disable: literal-JSON-false-only skip (absent/true/null/0/'false' load), collision fail-fast still fires for disabled entries, official keys keep file order then custom file order, absent-overlay byte-identity untouched (15 pre-existing tests green unmodified, test file additions-only)"
    requirement: CUST-06
    verification:
      - kind: automated
        ref: "tests/test_registry_loader.py (23 tests: 8 additive enabled-skip; git diff 0 deleted lines)"
        status: pass
      - kind: automated
        ref: "test $(grep -c '^def test_' tests/test_registry_loader.py) -ge 22 -> 23"
        status: pass
    human_judgment: false
    rationale: ""
  - id: CUST04-GAUNTLET
    description: "Dry-run precheck (D-06) + audit reconciliation (D-07) as real subprocesses with injectable runner: argv LIST discipline (sys.executable + absolute scripts), env = os.environ + exactly one override, staging existing+candidate forced enabled:true, candidate-only audit registry with absolutized Dataset_path, verdicts from parsed artifacts (exit-0-but-absent is a FAIL), timeout/crash absorbed as failed items, kind-gated reconcile under one run_id"
    requirement: CUST-04
    verification:
      - kind: automated
        ref: "tests/tui/test_services_gauntlet.py (29 tests: fake-runner matrix + real-subprocess dry-run pass)"
        status: pass
      - kind: automated
        ref: "grep shell/os.system/f-string/join gate over tui/services/gauntlet.py -> zero matches"
        status: pass
    human_judgment: false
    rationale: ""
  - id: PITFALL1-REGRESSION
    description: "Committed audit artifacts provably clobber-safe: n_audit.json, n_audit.csv, eval_subsets.json, DATA.md sha256-identical across a REAL audit-gauntlet run over a tmp CSV dataset (all five audit flags overridden to temp; fails if any default output path ever fires)"
    requirement: CUST-04 (Pitfall 1 / T-09-04)
    verification:
      - kind: automated
        ref: "tests/tui/test_services_gauntlet.py::test_committed_audit_artifacts_byte_unchanged_across_real_gauntlet"
        status: pass
    human_judgment: false
    rationale: ""
duration: 19 min
completed: 2026-10-12
status: complete
---

# Phase 09 Plan 02: Onboarding Gauntlet (dry-run precheck + audit reconciliation + D-09 skip) Summary

The CUST-04 error-detection gauntlet as textual-free orchestration over two real stdlib subprocesses — run_sweep.py --dry-run precheck over a staged overlay (existing customs + candidate forced enabled) and audit_n_frequencies.py reconciliation over a candidate-only temp registry with absolutized paths and all-temp outputs — plus the phase's single pipeline change: the D-09 loader skip where only the literal JSON false disables a custom entry (absence = enabled, byte-identity preserved, existing tests untouched).

## Performance

- 3/3 tasks, 6 commits (3 RED + 3 GREEN), ~19 min (estimate 29000 tokens / 3 tasks; actual ~17965 tokens over a 71.9k-char diff — estimate 61% high, the tightest implementation of the phase so far)
- Tests: tests/test_registry_loader.py 15 -> 23 (additions only, 0 deleted lines); tests/tui/test_services_gauntlet.py 29 new (fake-runner matrix + 2 real-subprocess lanes, both sub-second CPU); full tests/tui = 288 green; make lint + make typecheck zero findings (gauntlet.py joined the PHASE8_TUI glob and ty src-include automatically, zero Makefile edits)

## Accomplishments

- **Task 1 (TDD, 9afcd27 + 78ab7ca):** the D-09 enabled skip in `pipeline/registry_loader.py` — `registry.update` over the dict comprehension filtering `isinstance(entry, dict) and entry.get("enabled") is False`, placed after the untouched collision loop; module docstring contract extended with the D-09 clause; diff confined to `_load_registry` + docstring (30 insertions, 1 deletion). Eight additive tests pin every behavior row: literal-false-only skip against the string/0/null sentinels, enabled-true and absent-field both load, disabled collision still fails fast, official-file-order then custom-file-order key sequence (a disabled key skipped mid-file without disturbing order), no-custom-file order identity, and the non-dict-entry merge preserved.
- **Task 2 (TDD, 4809aa3 + fed61f3):** `tui/services/gauntlet.py` — GauntletItem dataclass (run_id/kind/leg/name/ok/details/raw_output) + GauntletService with an injectable runner seam; the D-06 dry-run leg stages existing customs + candidate (forced `enabled: true`) through `settings.atomic_write` into a temp overlay, resolves the official counterpart at read time (first Train-truthy task / first model key, read directly from the official files), invokes `[sys.executable, absolute run_sweep.py, --dry-run, ...]` as a LIST under `os.environ` + exactly one env override, and derives the verdict from the parsed `sweep_manifest.json` (planned cells naming the candidate) — exit-0-but-absent is a FAIL (Pitfall 5), a corrupt existing-custom registry surfaces as a failed item launching nothing, timeout/crash never cross the service boundary.
- **Task 3 (TDD, d58fb4a + bf4b630):** the D-07 audit leg — candidate-only temp `datasets_info.json` with the landed pipeline-relative `Dataset_path` re-absolutized (Pitfall 3), all five audit flags (`--registry-dir/--datasets-root/--data-dir/--subsets-out/--data-md`) pointed at temp paths (Pitfall 1), env override pinned to an EMPTY temp dir (Pitfall 2), own 300s timeout; the verdict parses the temp `n_audit.json` (missing false, three splits rows > 0, `unified_eval_n` > 0, declared Train/Dev/Test == measured rows — mismatches name the split and both counts) with the non-ACGT census and survivor counts riding the details as data; `reconcile(kind, ...)` gates models to dry-run only and runs datasets through both legs sequentially under one run_id.

## Task Commits

| Task | Commit | Type |
|------|--------|------|
| 1 — RED: additive enabled-skip tests | 9afcd27 | test(09-02) |
| 1 — GREEN: D-09 loader skip | 78ab7ca | feat(09-02) |
| 2 — RED: skeleton + dry-run leg suite | 4809aa3 | test(09-02) |
| 2 — GREEN: dry-run precheck leg | fed61f3 | feat(09-02) |
| 3 — RED: audit-leg suite + Pitfall-1 gate | d58fb4a | test(09-02) |
| 3 — GREEN: audit reconciliation + reconcile | bf4b630 | feat(09-02) |

## Files Created/Modified

Created: `tui/services/gauntlet.py`, `tests/tui/test_services_gauntlet.py`. Modified: `pipeline/registry_loader.py` (the one pipeline change — D-09 skip + docstring), `tests/test_registry_loader.py` (additions only).

## Decisions Made

See key-decisions in frontmatter. Highlights: the isinstance-guarded literal-false sentinel; read-time deterministic counterpart resolution from the official files; corrupt-custom-registry = failed item (never silent staging); zero f-strings/copy in the service (grep-gate-pinned); reconcile runs both legs unconditionally with landing left to the caller (D-08).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `_default_runner` double-passed `capture_output`/`text`**
- **Found during:** Task 2 GREEN (first real-subprocess run)
- **Issue:** the default runner forwarded the service's kwargs AND re-passed `capture_output=True, text=True` itself — `subprocess.run() got multiple values for keyword argument`.
- **Fix:** the default is now a pure forward (`subprocess.run(argv, check=False, **kwargs)`); the flags have one source (the service call, the same kwargs the fakes record).
- **Files modified:** `tui/services/gauntlet.py`
- **Commit:** fed61f3 (fixed inside the GREEN commit, before any commit landed the bug)

**2. [Rule 2 - Missing-critical] `entry.get()` would crash on non-object custom entries**
- **Found during:** Task 1 implementation
- **Issue:** the plan's literal filter `entry.get("enabled") is not False` raises AttributeError on a non-dict entry value that the pre-D-09 `registry.update(custom)` merged as-is — a new crash on formerly accepted input.
- **Fix:** the skip inspects `enabled` only on dict entries (`isinstance(entry, dict) and entry.get("enabled") is False`); pinned by `test_non_dict_custom_entry_still_merges_after_skip_filter`.
- **Files modified:** `pipeline/registry_loader.py`
- **Commit:** 78ab7ca

**3. [Rule 3 - Blocker] ruff 0.16 expanded defaults vs the plan's no-f-string grep gate**
- **Found during:** Task 2 lint gate
- **Issue:** the plan's verify gate greps `gauntlet.py` for ` f"` (any indented f-string matches) while ruff 0.16's default rule set (UP032) demands f-strings over `.format()` — the two cannot coexist via `.format()`.
- **Fix:** detail tokens use string concatenation (`"planned_cells=" + str(n)` — satisfies UP032's target and the grep gate), `Callable` imported from `collections.abc` (UP035), explicit `check=False` (PLW1510), and one `# noqa: BLE001` with the repo-precedent justification comment on the service-boundary catch. The plan's grep gate still passes with zero matches.
- **Files modified:** `tui/services/gauntlet.py`, `tests/tui/test_services_gauntlet.py`
- **Commits:** fed61f3, bf4b630

Otherwise the plan executed exactly as written.

## Issues Encountered

None beyond the deviations above. No auth gates, no checkpoints (fully autonomous plan).

Requirements-marking note: the shared-ID gate (`requirements ready-ids`, #2388 discipline) correctly reports CUST-04/CUST-06 as NOT ready — sibling plans 09-05/09-06 still declare them without SUMMARYs. REQUIREMENTS.md checkboxes therefore stay Pending until the phase's last sibling plan completes (same state 09-01 left CUST-01..03 in); the plan-level completion evidence lives in the coverage section above.

## TDD Gate Compliance

All three tdd-marked tasks followed RED -> GREEN with persisted, gate-validated evidence (INVALID_RED guarded):

- **Task 1 RED** (`RED_EVIDENCE_OK`, target `test_disabled_custom_model_entry_is_skipped`): 4 fail / 19 pass — the four disabled-skip assertions failed against the unconditional `registry.update(custom)`; all 15 pre-existing tests plus the four behavior-preserving new tests passed. Record: `.planning/tdd-evidence/09-02-task1-red.json`.
- **Task 2 RED** (`RED_EVIDENCE_OK`, target `test_pass_yields_ok_item_with_planned_cell_count_and_stdout`): 16 fail / 2 pass — every leg-behavior test failed on the NotImplementedError skeleton; the two module-hygiene scans passed on the skeleton as expected. Record: `.planning/tdd-evidence/09-02-task2-red.json`.
- **Task 3 RED** (`RED_EVIDENCE_OK`, target `test_audit_pass_yields_ok_item_with_reconciliation_detail`): 11 fail / 18 pass — all audit/reconcile tests failed on the stubs; the Task 2 suite stayed green. Record: `.planning/tdd-evidence/09-02-task3-red.json`.
- Both GREEN phases ran the FULL suite (not just the target test) before their feat commits; no test was weakened to pass.

## Known Stubs

None — every function is wired and tested; no TODO/FIXME/placeholder markers in the new files; the RED-phase NotImplementedError stubs were all replaced by their GREEN implementations.

## User Setup Required

None. The gauntlet runs entirely in temp directories; the user-owned custom registries are only ever read (existing-custom staging) and written exclusively by `custom_entries.land` in a later plan after all-pass.

## Next Phase Readiness

- 09-03/09-05 (wizard screens + gauntlet panel) consume: `reconcile(kind, candidate_key, entry, run_id, declared_splits=...)` on a thread worker, render `GauntletItem` from GAUNTLET_* strings (details are data tokens; `raw_output` is the drill-down), and drop stale `run_id`s (WR-02).
- 09-06 (management view) reads past the D-09 skip through `custom_entries.read_entries` (already landed in 09-01 — Pitfall 7 closed by construction).
- Success criteria confirmed: artifact-based pass criteria from real tooling; failures never land state (the gauntlet writes nothing outside its TemporaryDirectorys); disabled entries vanish from every registry consumer's view while official behavior stays byte-identical and existing tests untouched; the committed audit artifacts are provably clobber-safe.

## Self-Check: PASSED

All 6 task commits are ancestors of HEAD (9afcd27, 78ab7ca, 4809aa3, fed61f3, d58fb4a, bf4b630); all 4 plan files exist on disk; measured commits from the persisted ledger (`gsd-plan-head-before-09-02`) = 6, matching `actuals.commits`; official registries and committed audit artifacts git-clean.
