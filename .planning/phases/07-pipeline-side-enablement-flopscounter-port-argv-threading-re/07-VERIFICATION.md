---
phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
verified: 2026-10-12T11:51:07Z
status: passed
score: 14/14 must-haves verified
covered_files: [".claude/CLAUDE.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-01-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-01-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-02-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-02-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-03-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-03-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-04-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-04-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-05-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-05-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-06-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-06-SUMMARY.md", "AUDIT.md", "Makefile", "README.md", "docs/TUI-REQUIREMENTS.md", "pipeline/artifact_loader.py", "pipeline/flops_counter.py", "pipeline/registry_loader.py", "pipeline/run_finetune.py", "pipeline/run_sweep.py", "schemas/flops_report.json", "script/audit_n_frequencies.py", "script/export_runs.py", "tests/test_artifact_loader.py", "tests/test_flops_counter.py", "tests/test_known_defects.py", "tests/test_registry_loader.py", "tests/test_run_finetune_contracts.py", "tests/test_sweep.py"]
covered_digest: "v3:sha256:de2a334ff108268c663643227ad39fcc35af810406ab75cf594d758a36568d7d"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 14/14
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 7: Pipeline-Side Enablement (FlopsCounter Port, argv Threading & Registry Overlay) Verification Report

**Phase Goal:** The pipeline can be fully driven, measured, and extended by an external operator tool — FlopsCounter's 20+ architecture forward-hook FLOPs instrumentation ported from the deprecated `dnallmmark_pipeline.py` into `run_finetune.py`, the four sanctioned `run_sweep.py` argv flags threaded through with CLI parity, the official+custom registry overlay seam (user-maintained custom entries load on top of official registries; byte-identical when absent), and the tolerant JSON loader contract that FLOPs output and the future monitor share
**Verified:** 2026-10-12T11:51:07Z
**Status:** passed
**Re-verification:** Yes — #4682 stale-fingerprint route (third pass over this phase). Prior VERIFICATION.md (2026-10-11T13:56:57Z, passed 14/14, zero gaps) went stale again because Phase 9's commits touched a covered file: `pipeline/registry_loader.py` (the D-09 enabled-skip and CR-01 UnicodeDecodeError additions — the sanctioned additive changes) plus `tests/test_registry_loader.py` (append-only test coverage). This pass verified the delta against Phase 7's overlay/tolerant-loader contracts, re-executed the quality gates on the current tree, and recomputed the covered-input fingerprint.

## What Changed Since the Prior Pass (staleness diagnosis, verified)

File-level git audit (`git log --since=2026-10-11T13:56:57Z`) over all 19 covered implementation files at current HEAD `b69d07b`:

- **`pipeline/registry_loader.py`** — 2 commits (`78ab7ca` feat(09-02) D-09 loader-level enabled:false skip; `ad7213a` fix(09) CR-01 non-UTF-8 custom registry reads → fail-loud SystemExit). Diff vs prior-verified tree: **+38/-2**, hunk-audited below.
- **`tests/test_registry_loader.py`** — 2 commits (`9afcd27` RED additive D-09 tests; part of `ad7213a`). Diff vs prior-verified tree: **+198/-0 — purely append-only**; the 15 pre-existing Phase 7 test functions are byte-untouched (verified: the diff contains zero deletions, and the only pre-existing-test edit visible in the wider history — the WR-04 root-guard on `test_unreadable_custom_file_fails_loud_naming_file` — predates the prior verification, which already recorded it as present).
- **All 17 other covered implementation files** (Makefile included): **zero commits since the prior verification**. The staleness is exactly the two files above.
- `pyproject.toml` (not in the covered set) gained only `jsonschema>=4.26.0` under the `[tui]` group (`dafcf94`, Phase 8 selection screen) — dev-group gate lanes unaffected.

### Delta Contract Analysis (the focus of this pass)

The two registry_loader.py changes audited against the Phase 7 contracts (CUST-05 / D-06/D-08, T-07-04):

1. **D-09 enabled skip** (`registry.update()` → dict comprehension filtering `isinstance(entry, dict) and entry.get("enabled") is False`, at `pipeline/registry_loader.py:161-168`):
   - **Byte-identity when absent (D-06) untouched** — the absent-custom early return (`:119-120`, `if not custom_path.is_file(): return registry`) fires BEFORE any skip logic exists on that path; the official dict object is returned as-is. Live-checked this pass: empty overlay dir → `load_models_registry() == json.loads(official)` with identical key order (62 entries), and 0 of 62 official entries carry an `enabled` field (the invariant the skip relies on).
   - **Collision fail-fast (D-08) still first** — the collision loop (`:143-150`) runs over ALL custom keys BEFORE the skip comprehension, so a disabled shadow attempt still exits naming key + both paths. Live-checked: custom `{"official-model": {..., "enabled": false}}` → SystemExit "collides".
   - **Literal-False-only semantics** — `is False` identity check: absent, `true`, `0`, `"false"`, JSON `null` all LOAD; only the bool `False` disables. Live-checked as a 7-entry matrix. The `isinstance` guard preserves pre-D-09 merge-as-is behavior for non-object entry values (no new crash on formerly accepted input).
   - **CUST-05's "existing tests zero-modification" clause holds** — pre-existing tests byte-unchanged (+198/-0) and all 15 green.
2. **CR-01 UnicodeDecodeError** (`:132`, except tuple widened to `(OSError, json.JSONDecodeError, UnicodeDecodeError)`): fail-loud SystemExit message path unchanged — a ValueError sibling that previously escaped as a raw traceback now takes the same T-07-04 fail-loud path as every other unreadable custom file. Live-checked: GBK-encoded custom file → SystemExit naming the file (not a raw UnicodeDecodeError).

Both changes sit ONLY on the custom-file-present path and are the sanctioned Phase 9 additive scope (D-09 loader-level disable). No other behavior of the seam changed; the five load sites (run_sweep x3, run_finetune module level, audit importlib) share the seam unchanged.

**Verification basis (all executed by this verifier against current HEAD `b69d07b`):** `make lint` exit 0 (PHASE7 modules in the ruff expansion), `make typecheck` exit 0, `make test-fast` **953 passed / 1 deselected / 0 failed** (163s, includes the 24-test registry_loader suite = 15 pre-existing + 9 Phase 9 additions), dedicated `pytest tests/test_registry_loader.py` **24 passed**; live CPU torch-free import; live 14-point contract check (byte-identity, enabled-skip matrix, key ordering, collision-before-skip, non-UTF-8 fail-loud, malformed fail-loud, tolerant-loader 4-case re-check); symbol/wiring greps over every integration point; anti-pattern scan over both changed files; decision-coverage gate re-run.

## Goal Achievement

### Observable Truths

Must-haves carried forward verbatim from the prior pass (re-verification reuses Step 0 must-haves — same 14-truth contract). Truths 10/11/14 received full re-execution against the current tree (the changed-file focus); the rest received quick regression checks (files byte-unchanged since a passed pass + symbol/wiring greps re-run this pass).

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `run_sweep.py` accepts `--subset_file`, `--effective_batch_size`, `--num_train_epochs`, `--cache_dir` (underscore-only) and threads each as separate LIST elements in child argv only when present; byte-identical when absent (SC1 / PIPE-02 / D-11/D-13) | ✓ VERIFIED | `pipeline/run_sweep.py` byte-unchanged since the prior pass (which live-checked `build_argv` threading + three green tests); grep re-confirmed this pass: 82 lines across the four flag names including registrations, argv appends, and sweep_flags handling; the four-flag test set green inside this verifier's 953-pass run |
| 2 | Bare `--effective_batch_size` yields 16; valued yields int; absent contributes zero argv elements so child YAML GA governs (D-12) | ✓ VERIFIED | File unchanged; `nargs="?", const=16, type=int, default=None` re-confirmed by grep; test green in the 953 run |
| 3 | `--subset_file` / `--cache_dir` resolved to absolute paths at sweep layer before threading (D-15); GA arithmetic stays child-side, integer-only pass-through (D-10/D-16) | ✓ VERIFIED | File unchanged since prior pass (Path.resolve pre-enumeration verified then); no GA computation present (prior-pass grep, file untouched) |
| 4 | `--subset_file` pre-validated collect-all at sweep start (every problem listed, before any cell enumerates) (D-14) | ✓ VERIFIED | File unchanged; `_validate_subset_file` present; collect-all test green in the 953 run |
| 5 | Manifest cells record flag fields ONLY when present; run_record.json field set untouched (D-13 / D-02 spirit) | ✓ VERIFIED | File unchanged; `_manifest_payload(matrix, records, sweep_flags=None)` present; test green in the 953 run |
| 6 | FlopsCounter's 20+ architecture dispatch ported with formulas verbatim, CPU-importable and stub-testable with no torch at module top, no GPU, no dnallm (SC2 / PIPE-01) | ✓ VERIFIED | `pipeline/flops_counter.py` byte-unchanged since prior pass; live re-check this pass: `import flops_counter` succeeds CPU-side with `'torch' not in sys.modules` (cpu-import-ok / torch-free-ok); 49 stub tests green in the 953 run |
| 7 | Dispatch order preserved: a Linear inside a borzoi-path model takes the Linear hook, not the borzoi branch | ✓ VERIFIED | File unchanged since prior pass (branch order diffed identical vs legacy `1b74037e` then); `test_linear_wins_over_borzoi_branch` green in this verifier's run |
| 8 | Every run_finetune execution calibrates FLOPs always-on (no flag), hooks removed BEFORE the DNATrainer ctor, single post-success flops_report.json write ordered final_metrics → flops_report → trainer_state marker inside the local_rank==0 guard, hardware captured verbatim (D-01/D-02/D-05, WR-13) | ✓ VERIFIED | `pipeline/run_finetune.py` byte-unchanged since prior pass; grep re-confirmed this pass: FlopsCounter ctor `:1470`, `remove_hooks()` both branches `:1478/:1480` before trainer init, `save_to_json` `:1604` with `build_hardware_section` `:1608`; all four contract tests green in the 953 run |
| 9 | A real bounded GPU run emits flops_report.json: schema_version 1, attention + Linear hook keys, uncovered within threshold, hardware populated with the real device string, magnitude ratio in [0.05, 1.0] (SC2 runtime / D-22/D-23) | ✓ VERIFIED | GB10 smoke artifacts on disk (uncommitted, gitignored — D-26) were re-examined and schema-re-validated by the prior pass against the byte-unchanged `schemas/flops_report.json`; zero FLOPs-chain commits exist since that pass (this pass's git audit: flops_counter.py, run_finetune.py, artifact_loader.py, schemas/ all unchanged) — see Warning W2 on evidence recency |
| 10 | Tolerant loader contract: `load_json_artifact` returns parsed doc for valid files, None for missing/unreadable/truncated/empty; valid-but-key-missing returned, not rejected (SC3 / PIPE-03 / D-17/D-18/D-19) | ✓ VERIFIED | `pipeline/artifact_loader.py` byte-unchanged; live 4-case re-check this pass — missing/empty/truncated-UTF8 → None, valid → parsed dict returned (`tolerant-*-ok`); 9 tests green in the 953 run. Phase 8's `tui/services/` consumes this seam as planned |
| 11 | Registry overlay seam: custom entries merge over official registries, collision fails fast naming key + BOTH paths, malformed custom fails loud, byte-identical when absent, official files never written, all five load sites rewired (SC4 / CUST-05 / D-06/D-07/D-08) | ✓ VERIFIED | **Full re-verification of the CHANGED file** (`pipeline/registry_loader.py`, +38/-2 since prior pass — Phase 9's D-09 enabled-skip + CR-01): read-only `"r"` opens only (`:117/:123`); live checks this pass — absent overlay → `load_models_registry() == json.loads(official)` with identical key order and 0 official entries carrying `enabled` (`absent-overlay-byte-identical-ok`); collision loop BEFORE the skip (live: disabled shadow → SystemExit `collides`); enabled matrix (literal False skipped; absent/true/0/"false"/null load; non-dict merges as-is); GBK custom → fail-loud SystemExit naming the file; malformed JSON → SystemExit; key order official-file-order then custom-file-order. Five load sites re-confirmed (run_sweep import + 3 load contexts + pre-validation; run_finetune module-level `:48-51`-adjacent import and loads — additionally source-pinned by the new `test_run_finetune_module_level_loads_route_through_registry_loader`; audit via importlib). `pytest tests/test_registry_loader.py`: **24 passed** (15 pre-existing unmodified + 9 Phase 9 additive). See Warning W1 on SC4's "export" consumer listing |
| 12 | Legacy file deleted with zero live-code references; five parity expectations re-pinned as sha-documented verbatim literals; archives untouched (D-04) | ✓ VERIFIED | Re-executed this pass: `test ! -e pipeline/dnallmmark_pipeline.py` → absent; `grep -rn dnallmmark_pipeline pipeline/ script/ tests/ Makefile schemas/` → 0 lines; archives untouched since prior pass (covered-set audit shows no `.planning/milestones/` churn); re-pinned contracts green in the 953 run |
| 13 | flops_report.json v1 schema published, strictly additive over legacy writer keys, schema_version const 1, optional hardware (D-27/D-02/D-03/D-05) | ✓ VERIFIED | `schemas/flops_report.json` byte-unchanged since prior pass (which proved additivity by direct diff vs the legacy writer and validated the real GB10 report 0-errors); CR-01 zero-token guard confirmed in `save_to_json` (flops_counter.py — unchanged); round-trip test green in the 953 run |
| 14 | `make lint` + `make typecheck` cover the changed files; full test lane green; zero GPU/dnallm in any gate (SC5) | ✓ VERIFIED | **Re-executed on the current tree (HEAD `b69d07b`):** `make lint` exit 0 — the ruff expansion observed listing `pipeline/flops_counter.py pipeline/registry_loader.py pipeline/artifact_loader.py` (PHASE7_MODULES intact) with Phase 8/9 `tui/` files appended; `make typecheck` exit 0 (`--group dev --group tui ty check`); `make test-fast` **953 passed / 1 deselected / 0 failed** in 163s (includes all six Phase 7 test files plus the 9 new registry tests). Makefile byte-unchanged since the prior pass verified it; pyproject's only change (jsonschema in `[tui]`) touches no gate lane used by Phase 7. Lanes remain GPU-free and dnallm-free |

**Score:** 14/14 truths verified (0 present, behavior-unverified)

### Advisory (New Scope, Unevidenced)

Re-verification ran (stale-fingerprint route); this section is recorded per the #3304 evidence-gate contract.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | None — no new-scope findings. The only covered file modified since the prior pass (`pipeline/registry_loader.py`) was fully re-verified with green gates, live contract checks, and its 24-test suite; no unevidenced new-scope concern was raised. | — | — |

### Decision Coverage

Gate output (`check.decision-coverage-verify`, re-run this pass): 27/27 trackable CONTEXT.md decisions honored by shipped artifacts, 0 not honored, non-blocking.

### Required Artifacts

All Phase 7 artifacts unchanged since the prior pass except `pipeline/registry_loader.py` (Phase 9's +38/-2 sanctioned additive changes — fully re-verified above) and `tests/test_registry_loader.py` (+198 append-only). `gsd-tools verify artifacts` returns `total: 0` for these plans (the tool expects `{path, provides}` object entries; these plans declare plain string lists) — artifact status below is from direct inspection (existence + substantiveness + wiring), same as the prior passes.

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pipeline/flops_counter.py` | FlopsCounter port: lazy torch seams, 20+ dispatch, uncovered accounting, save_to_json + v1 additions, count_split_tokens, build_hardware_section, calibration_forward | ✓ VERIFIED | Byte-unchanged since prior pass; live torch-free import re-checked; imported by run_finetune (`:48-51`) — WIRED |
| `pipeline/artifact_loader.py` | Tolerant load_json_artifact (D-17/D-18/D-19) | ✓ VERIFIED | Byte-unchanged; live 4-case contract re-check passed; consumed by Phase 8 tui services — contract-pinned, not orphaned |
| `pipeline/registry_loader.py` | Overlay seam: custom_registry_dir, load_models_registry, load_datasets_registry (+ Phase 9's D-09 enabled-skip, CR-01 UnicodeDecodeError) | ✓ VERIFIED | 209 lines (was 172); collision fail-fast + fail-loud malformed preserved and BEFORE the skip; read-only opens only; byte-identity when absent live-verified; imported by run_sweep, run_finetune, audit (importlib) — WIRED at all five sites; 24 tests green |
| `schemas/flops_report.json` | v1 strict contract (D-27) | ✓ VERIFIED | Byte-unchanged; validated the real GB10 report (prior pass, 0 errors) |
| `tests/test_flops_counter.py` | Stub-nn harness, per-family arithmetic, schema pins, dispatch order, calibration chain | ✓ VERIFIED | Byte-unchanged; green in this verifier's 953-test run |
| `tests/test_artifact_loader.py` | Tolerant-read contract cases | ✓ VERIFIED | Byte-unchanged; green |
| `tests/test_registry_loader.py` | Overlay merge/collision/malformed/resolution/byte-identity + run_finetune source-contract (+ Phase 9 additive enabled-skip/CR-01 coverage) | ✓ VERIFIED | 541 lines (was 343); +198/-0 — pre-existing tests unmodified; 24 tests green |
| `tests/test_sweep.py` | argv parity, pre-validation, manifest-field, byte-identity extensions | ✓ VERIFIED | Byte-unchanged; green in the 953 run |
| `tests/test_run_finetune_contracts.py` | Calibration-slot / write-ordering / rank-guard contracts + re-pinned parity literals | ✓ VERIFIED | Byte-unchanged; green in the 953 run |
| `pipeline/dnallmmark_pipeline.py` | DELETED (D-04) | ✓ VERIFIED (absence) | Re-checked this pass: not on disk, zero live references |

### Key Link Verification

`gsd-tools verify key-links` parses zero links from these plans' prose-style entries; wiring below is from direct source inspection (re-grepped this pass).

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| run_finetune calibration slot | flops_counter.FlopsCounter / build_hardware_section | sibling import `run_finetune.py:48-51`, calls at `:1470/:1604/:1608` | ✓ WIRED | Import + symbols re-confirmed by grep this pass |
| run_finetune / run_sweep / audit registry loads | registry_loader | module import (run_sweep; run_finetune) / importlib spec_from_file_location (audit) | ✓ WIRED | Five sites re-confirmed; run_finetune module-level routing now ALSO source-pinned by `test_run_finetune_module_level_loads_route_through_registry_loader` (green) |
| FlopsCounter.save_to_json output | schemas/flops_report.json | round-trip test with Draft202012Validator | ✓ WIRED | Round-trip test green in the 953 run; schema byte-unchanged |
| save_to_json writes | artifact_loader.load_json_artifact | round-trip read-back | ✓ WIRED | Round-trip test green |
| sweep argv | run_finetune child flags | `--cache_dir`, `--effective_batch_size`, `--subset_file`, `--num_train_epochs` | ✓ WIRED | run_sweep byte-unchanged; flag greps re-confirmed |
| Makefile lint | PHASE7_MODULES | wildcard existence guard | ✓ WIRED | Makefile byte-unchanged since prior pass verified it; all three modules observed in this verifier's ruff expansion this pass |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| flops_report.json (written) | report dict | FlopsCounter accumulators from real forward hooks | ✓ | Real GB10 report on disk (prior-pass re-read; FLOPs chain byte-unchanged since) |
| manifest flag fields | sweep_flags | argparse → main() resolution → _manifest_payload | ✓ | Live-checked by prior pass; run_sweep unchanged |
| registry merged dict | registry | official JSON file + optional custom JSON file | ✓ | Live byte-identity + enabled-skip matrix + key-order checks re-executed this pass |

### Behavioral Spot-Checks

All executed by this verifier against current HEAD `b69d07b` (focused on the delta; unchanged-truth evidence carried from the prior pass plus greps).

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Torch-free CPU import of the three modules | `uv run --group dev python -I` — import flops_counter, artifact_loader, registry_loader + `'torch' not in sys.modules` | cpu-import-ok / torch-free-ok | ✓ PASS |
| Overlay byte-identity when absent | live: empty pinned overlay dir → `load_models_registry(pipeline)` vs `json.loads(models_info.json)` | equal dict AND equal key order (n=62); 0 official entries with `enabled` | ✓ PASS |
| D-09 enabled-skip semantics matrix | live: 7-entry custom overlay (false/absent/true/0/"false"/null/non-dict) | only literal False skipped; others load; non-dict merged as-is | ✓ PASS |
| Collision fail-fast BEFORE skip | live: disabled custom entry shadowing official key | SystemExit "collides" naming key + both paths | ✓ PASS |
| CR-01 non-UTF-8 custom file | live: GBK-encoded custom_models.json | fail-loud SystemExit naming the file (no raw UnicodeDecodeError) | ✓ PASS |
| Malformed custom still fails loud | live: `{not json` | SystemExit raised | ✓ PASS |
| Key ordering | live: merged keys = official file order then custom file order (minus skipped) | exact order match | ✓ PASS |
| Tolerant loader 4-case regression | live: valid/empty/truncated-UTF8/missing | valid→dict; others→None | ✓ PASS |
| Changed-file test suite | `uv run --group dev pytest tests/test_registry_loader.py -q` | 24 passed in 0.06s | ✓ PASS |
| Full quality gates on current tree | `make lint` / `make typecheck` / `make test-fast` | exit 0 / exit 0 / 953 passed 1 deselected 0 failed | ✓ PASS |
| Legacy absence + zero references | `test ! -e pipeline/dnallmmark_pipeline.py` + grep | absent / 0 lines | ✓ PASS |

### Probe Execution

Not applicable — phase declares no `scripts/*/tests/probe-*.sh` probes; the runtime proof is plan 07-06's GB10 smoke whose artifacts the prior pass independently re-examined on disk and re-validated against the schema; the FLOPs chain is byte-unchanged since (this pass's git audit).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PIPE-01 | 07-01, 07-04, 07-05, 07-06 | FlopsCounter 20+ architecture port into run_finetune.py | ✓ SATISFIED | Truths 6, 7, 8, 9, 12, 13 — all FLOPs-chain files byte-unchanged since the passed prior pass; gates re-executed green |
| PIPE-02 | 07-03, 07-06 | run_sweep argv passthrough of the four flags | ✓ SATISFIED | Truths 1-5 — run_sweep byte-unchanged; test set green in the 953 run |
| PIPE-03 | 07-01 | Tolerant loader JSON contract shared with the future monitor | ✓ SATISFIED | Truth 10 — live 4-case re-check passed this pass; file unchanged |
| CUST-05 | 07-02 | Registry overlay: collision fail-fast, byte-identical when absent, existing tests zero-modification | ✓ SATISFIED | Truth 11 — full re-verification of the changed file: byte-identity live-proven, collision-before-skip live-proven, existing tests byte-unmodified (+198/-0) and green (see Warning W1 on the SC4 "export" consumer listing — locked decision D-09 scope) |

Orphan check: REQUIREMENTS.md maps exactly 4 IDs to Phase 7 (CUST-05, PIPE-01, PIPE-02, PIPE-03); all four are claimed by plans and satisfied. No orphans.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| tests/test_flops_counter.py | PIPE-01/03 | 49 | 0 | 0 | Value (arithmetic equals, dict equality, schema validation) | OK |
| tests/test_artifact_loader.py | PIPE-03 | 9 | 0 (conditional root-guard, not taken) | 0 | Value (None-vs-dict discrimination) | OK |
| tests/test_registry_loader.py | CUST-05 | 24 (15 pre-existing + 9 Phase 9 additive) | 0 (conditional root-guard, not taken) | 0 | Value (dict equality, key-order lists, SystemExit message content, enabled-matrix membership) | OK |
| tests/test_sweep.py | PIPE-02 | extended | 0 | 0 | Value/Behavioral (argv element-by-element, manifest field presence/absence) | OK |
| tests/test_run_finetune_contracts.py | PIPE-01 | extended | 0 | 0 | Behavioral (source-order index comparisons, rank-guard membership) | OK |

All five Phase 7 test files green within this verifier's 953-passed fast-lane run. The 9 Phase 9 additions are append-only coverage over the new enabled-skip/CR-01 semantics — the 15 pre-existing overlay tests are byte-unmodified and green (CUST-05's zero-modification clause holds). No disabled tests on requirements. No circular patterns — the legacy file in git history (`1b74037e`) remains the independent oracle; the magnitude anchor's provenance is external (HF `total_flos`).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | Zero TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER markers across both changed files (re-scanned this pass); prior pass's clean scan of the other 17 covered files stands (byte-unchanged) | - | - |

**Warnings (non-blocking, carried forward from the prior pass — re-checked against the current tree):**

| # | Finding | Severity | Impact |
|---|---------|----------|--------|
| W1 | ROADMAP SC4's consumer list names **export** among the overlay consumers, but `script/export_runs.py` was deliberately NOT rewired (locked decision D-09 scope, user-selected at the Phase 7 discuss checkpoint). Re-checked this pass: `export_runs.py` still has zero commits since Phase 7 and still joins registries via explicit `--models-info`/`--datasets-info` CLI paths. The practical SC4 assertions (collision fail-fast, byte-identity when absent, existing tests unmodified, official files never written) all verify; the goal statement does not list export; escape hatch exists (`--models-info` with any registry file). | ⚠️ Warning | Phase 9 completed without rewiring export; remains a documented-by-decision deviation, non-blocking |
| W2 | GPU emission evidence (Truth 9) was produced before Phase 8/9; the FLOPs chain (`flops_counter.py`, `run_finetune.py`, `artifact_loader.py`, `schemas/flops_report.json`) has zero commits since the smoke and since the prior verification (this pass's git audit), and the on-disk report re-validated against the schema at the prior pass — but strictly, the exact current tree state has not itself been GPU-run. | ℹ️ Info | Acceptable: zero FLOPs-chain code changed since the smoke; a future bounded smoke under E2' will re-prove the tree |
| W3 | Review-disposition Info findings IN-01..IN-05 (unused `samples` var, duplicate gpu_memory_override assignment, README CLI docs missing the four sweep flags, CLAUDE.md 3.11+ vs README 3.13+ badge, CPU-run max_mem_gb 0.0 vs docstring) remain open by maintainer scope decision (2026-10-11 16:10 CST, `07-REVIEW-DISPOSITION.md`); the relevant files are byte-unchanged since. | ℹ️ Info | Non-blocking; documentation/cleanup-tier, out of the CR+WR fix scope the maintainer chose |

### Human Verification Required

N/A — Infrastructure/foundation phase (pipeline tooling, no user-facing elements). All acceptance criteria are verifiable programmatically and were verified programmatically: gates re-executed on the current tree (lint exit 0 / typecheck exit 0 / 953-test fast lane green), the changed file's 24-test suite green, live behavioral checks re-run (overlay byte-identity, enabled-skip matrix, collision-before-skip, CR-01 non-UTF-8 fail-loud, malformed fail-loud, key ordering, tolerant-loader 4-case, torch-free import), and runtime behavior evidenced by the real GB10 artifacts re-examined on disk at the prior pass with the FLOPs chain byte-unchanged since. No ⚠️ PRESENT_BEHAVIOR_UNVERIFIED truths, no abstained non-inferable truths.

### Re-Verification Record

- **Route:** #4682 stale fingerprint (second stale-fingerprint re-run over this phase; prior pass `passed` 14/14 at 2026-10-11T13:56:57Z / HEAD `1697b0c`).
- **Staleness diagnosis confirmed:** `git log --since=2026-10-11T13:56:57Z` over all 19 covered implementation files → only `pipeline/registry_loader.py` (+38/-2, commits `78ab7ca`/`ad7213a`) and `tests/test_registry_loader.py` (+198/-0, `9afcd27`+) changed — Phase 9's sanctioned D-09 enabled-skip and CR-01 UnicodeDecodeError additions, the exact changes the <verification_context> flagged. Makefile and the other 17 covered files are byte-unchanged this round.
- **Delta contract analysis:** both changes verified additive and contract-preserving — byte-identity-when-absent untouched (early return precedes the skip; 0 official entries carry `enabled`), collision fail-fast still precedes the skip, literal-False-only disable semantics, fail-loud SystemExit widened (not altered) for non-UTF-8, pre-existing tests byte-unmodified and green.
- **Regression check:** all 14 truths quick-checked (existence + symbol sanity + wiring greps), Truth 11 fully re-verified live, Truth 14 gates fully re-executed (lint 0 / typecheck 0 / 953 passed), dedicated changed-file suite 24/24 green. Zero regressions.
- **Fingerprint recomputed** over the current tree via `verification.fingerprint` with the phase's 19 implementation files (PLAN/SUMMARY files auto-added by the command); `covered_digest` in the frontmatter is the command's verbatim output.

### Gaps Summary

No gaps. The stale fingerprint was diagnosed (registry_loader.py + test_registry_loader.py only — Phase 9's sanctioned additive D-09/CR-01 changes), the delta verified contract-preserving against every Phase 7 overlay/tolerant-loader assertion (byte-identity when absent live-proven, collision-before-skip live-proven, existing tests byte-unmodified, official files never written), all 14 merged must-have truths verified against the current tree, gates re-executed green (lint exit 0, typecheck exit 0, 953-test fast lane, 24/24 registry suite), all 4 requirement IDs satisfied with no orphans, 27/27 decisions honored, zero debt markers, and the covered-input fingerprint regenerated at the current tree state (`v3:sha256:de2a33...68d7d`). The three warnings are informational (W1 → documented-by-decision export deviation; W2/W3 → evidence-recency and maintainer-scoped Info findings).

---

_Verified: 2026-10-12T11:51:07Z_
_Verifier: Claude (gsd-verifier)_
