---
phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
verified: 2026-10-14T11:28:53Z
status: passed
score: 14/14 must-haves verified
covered_files: [".claude/CLAUDE.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-01-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-01-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-02-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-02-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-03-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-03-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-04-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-04-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-05-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-05-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-06-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-06-SUMMARY.md", "AUDIT.md", "Makefile", "README.md", "docs/TUI-REQUIREMENTS.md", "pipeline/artifact_loader.py", "pipeline/flops_counter.py", "pipeline/registry_loader.py", "pipeline/run_finetune.py", "pipeline/run_sweep.py", "schemas/flops_report.json", "script/audit_n_frequencies.py", "script/export_runs.py", "tests/test_artifact_loader.py", "tests/test_flops_counter.py", "tests/test_known_defects.py", "tests/test_registry_loader.py", "tests/test_run_finetune_contracts.py", "tests/test_sweep.py"]
covered_digest: "v3:sha256:888330253a0e5c06c3e36d32b6795a0e4e98b19ef07d354264f83500716f837d"
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
**Verified:** 2026-10-14T11:28:53Z
**Status:** passed
**Re-verification:** Yes — #4682 stale-fingerprint route (fourth stale-fingerprint re-run over this phase). The 2026-10-14T00:00:00Z pass (passed 14/14 at HEAD `43d3544`) went stale because the 261014 quick-task series (c2l, f4w, ir9, l6h, mlc) plus the incremental Phase 7 code review touched covered files: `run_sweep.py` (+225), `run_finetune.py` (+93), `tests/test_sweep.py` (+416), `tests/test_run_finetune_contracts.py` (+266), `Makefile` (+7), `README.md` (+18), `script/audit_n_frequencies.py` (12), `script/export_runs.py` (5), `AUDIT.md` (4), `docs/TUI-REVIEW.md` not in set; `docs/TUI-REQUIREMENTS.md` (4). This pass hunk-audited the full delta, re-ran the six phase-7 suites, re-executed the live overlay/tolerant-loader/import/lint contracts, assessed the open critical review finding CR-01 against the must-haves (see Warnings), and recomputed the covered-input fingerprint at HEAD `075a621`.

## Re-verification (stale refresh, HEAD 075a621, 2026-10-14)

### Staleness diagnosis (commit-anchored, verified this pass)

`git diff --stat 43d3544..HEAD` over the covered set:

- **261014-c2l + 261014-f4w (sibling flag family + startup config):** `run_sweep.py` +225 — adds `--model_root`/`--dataset_root`/`--log_dir` as pass-through family members following the exact 07-03 discipline (only-when-present LIST argv append, D-15 abs-resolution, WR-05 empty-refusal, D-13 only-when-present manifest keys) plus the `directories.json` startup read (`pipeline/directories_config`, flag > file > built-in default); `run_finetune.py` +93 — the matching child flags, the `directories_config.effective()` merge, storage-root base resolution, and the effective log dir (all absent-everywhere branches documented and tested byte-identical). `--output-root` argparse default moved `./finetuned` → None with an explicit `file_dirs.get("output_root") or "./finetuned"` fallback — bare resolution unchanged.
- **Test extensions:** `tests/test_sweep.py` +416, `tests/test_run_finetune_contracts.py` +266 — new tests for the above (suite grew 276 → 302, all green).
- **`Makefile` +7:** lint lane APPENDS `$(QUICK_L6H_SCRIPTS)` (`script/audit_dnallm_compat.py` — linted, never CI-executed); `PHASE7_MODULES` definition and position untouched.
- **Comment/doc-only:** `script/audit_n_frequencies.py` (line-number references :832→:1418), `script/export_runs.py` (62/62 → 59/59 comment), `README.md` (+18), `AUDIT.md` (4 annotation lines), `docs/TUI-REQUIREMENTS.md` (2 annotation lines).
- **Byte-identical (empty diff):** `pipeline/flops_counter.py`, `pipeline/registry_loader.py`, `pipeline/artifact_loader.py`, `schemas/flops_report.json`, `tests/test_flops_counter.py`, `tests/test_registry_loader.py`, `tests/test_artifact_loader.py`, `tests/test_known_defects.py`, `.claude/CLAUDE.md`.
- **Uncovered but relevant:** `pipeline/models_info.json` 62 → 59 entries (261014-ir9 Chaoba removal) — registry content change; the byte-identity contract is relative to the official file, so it is unaffected (live re-check this pass at n=59).

### Delta contract analysis vs the Phase 7 must-haves

1. **The four sanctioned flags (T1-T5) are untouched and still first in the family.** `build_argv` still appends `--subset_file`/`--effective_batch_size`/`--num_train_epochs`/`--cache_dir` only when present; the new storage tail (`--model_root`, `--dataset_root`, `--log_dir`) appends AFTER them. Abs-path resolution (`subset_file_abs`, `cache_dir_abs`) and collect-all subset pre-validation survive; `cache_dir` now falls back to the `directories.json` key before None (additive documented feature — absent-flag-plus-no-file keeps zero argv elements, byte-identical). `sweep_flags` still records only present keys.
2. **The FLOPs chain core is byte-identical** and the `run_finetune.py` delta does not touch the calibration slot, hook lifetime, or the write-ordering block — the 07-04 contracts (`remove_hooks` before DNATrainer ctor, final_metrics → flops_report → marker ordering, local_rank==0 guard) are test-pinned and green in this verifier's 302-test run.
3. **No gate-lane GPU/dnallm exposure.** The only Makefile change appends a stdlib lint-only script; `typecheck` (`uv run --group dev --group tui ty check`) and `test` recipes are byte-unchanged.
4. **CR-01 (open critical review finding) assessed in full — see Warnings.** Deterministically reproduced this pass; does not falsify any enumerated Truth 11 / SC4 / CUST-05 clause; ownership is the Phase 9 custom-registry schema/wizard surface plus pre-Phase-7 consumer indexing (provenance commit `c6b3137`).

### Re-verified verdicts (all 14 truths)

| Must-have | Verdict | Basis this pass |
|---|---|---|
| T1-T5 (four flags: threading, bare-EBS=16, abs-resolution, D-14 pre-validation, only-when-present manifest) | ✓ VERIFIED | `run_sweep.py` delta hunk-audited — four-flag threading intact and unchanged; suite green in this verifier's run (302 passed) |
| T6-T9, T13 (FlopsCounter port, dispatch order, always-on calibration, GPU emission, v1 schema) | ✓ VERIFIED | `flops_counter.py` + `schemas/flops_report.json` byte-identical (empty diff); live torch-free CPU import re-checked; `run_finetune.py` delta does not touch the calibration/write spans; contracts tests green |
| T10 (tolerant loader) | ✓ VERIFIED | `artifact_loader.py` byte-identical; live 4-case contract re-check passed this pass |
| T11 (registry overlay: byte-identical-when-absent, collision fail-fast, fail-loud, load sites) | ✓ VERIFIED | `registry_loader.py` byte-identical; live byte-identity re-check at the post-Choba registry (59 models / 50 datasets, equal key order, 0 official `enabled` fields); all load sites still via `registry_loader`; 24-test suite green. **Carries open finding CR-01 (Warning W4) — seam clauses all hold; see Warnings** |
| T12 (legacy deleted, zero references) | ✓ VERIFIED | Re-executed: `test ! -e pipeline/dnallmmark_pipeline.py` → absent; grep over `pipeline/ script/ tests/ Makefile schemas/` → 0 lines |
| T14 (lint/typecheck/test gates, GPU-free/dnallm-free) | ✓ VERIFIED | `make -n lint` PHASE7 expansion re-proven (PHASE7-EXPANSION-OK); typecheck recipe byte-unchanged CPU-side; phase-7 suites 302 green; the 7 full-suite failures are the documented machine baseline (5 schema/determinism pins + 1 storage_overview machine-state) — none in phase-7 covered test files |

### Spot-checks (executed by this verifier at HEAD 075a621)

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_flops_counter.py tests/test_registry_loader.py tests/test_sweep.py tests/test_artifact_loader.py tests/test_run_finetune_contracts.py tests/test_known_defects.py -q` | **302 passed in 0.78s** (suite grew from 276 via the 261014 flag-family test extensions) |
| `python -I` torch-free import (`flops_counter`, `registry_loader`, `artifact_loader`) | cpu-import-ok / torch-free-ok |
| Live overlay byte-identity (empty `DNALLMMARK_CUSTOM_REGISTRY_DIR`) | models: equal dict AND equal key order (n=59, post-Choba); datasets: equal (n=50); 0 official entries with `enabled` |
| Live tolerant-loader 4-case | valid→dict; empty/truncated-UTF8/missing→None |
| `make -n lint` PHASE7 expansion | `pipeline/flops_counter.py pipeline/registry_loader.py pipeline/artifact_loader.py` present (PHASE7-EXPANSION-OK); only `$(QUICK_L6H_SCRIPTS)` appended since the prior pass |
| Legacy absence + zero references | absent / 0 lines |
| Debt markers (`TBD\|FIXME\|XXX`) over all 10 changed covered files | 0 hits |
| CR-01 reproduction (see Warnings W4) | schema-valid minimal entry merges through the seam → `KeyError: 'Model_name'` / `KeyError: 'Mean_token_length'` at the exact run_finetune index sites |

**Fresh fingerprint (verbatim from `verification.fingerprint`):** `v3:sha256:888330253a0e5c06c3e36d32b6795a0e4e98b19ef07d354264f83500716f837d` over 19 implementation files + 4 docs + the auto-added PLAN/SUMMARY set (frontmatter `covered_files` is the command's verbatim output).

**Verdict: PASSED — 14/14 must-haves hold at HEAD 075a621.** Zero regressions in the phase-7 contract; the staleness was the sanctioned 261014 quick-task delta plus the incremental review artifacts, none of which weakens a Phase 7 clause. One open critical review finding (CR-01) was reproduced and assessed in full — it is a real, evidenced defect in the CURRENT overlay chain's end-to-end robustness but does not breach any enumerated Phase 7 must-have (analysis below); it is reported as Warning W4 for maintainer triage, not silently absorbed.

---

## Goal Achievement

### Observable Truths

Must-haves carried forward verbatim from the prior pass (re-verification reuses Step 0 must-haves — same 14-truth contract). Truths 10, 11, 12, 14 received live re-execution this pass; T1-T5 delta-audited in full (run_sweep.py changed since the prior pass); the FLOPs chain byte-checked.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `run_sweep.py` accepts `--subset_file`, `--effective_batch_size`, `--num_train_epochs`, `--cache_dir` (underscore-only) and threads each as separate LIST elements in child argv only when present; byte-identical when absent (SC1 / PIPE-02 / D-11/D-13) | ✓ VERIFIED | Delta hunk-audited: four-flag `build_argv` append block unchanged, new 261014 flags append after; suite green (302 passed) |
| 2 | Bare `--effective_batch_size` yields 16; valued yields int; absent contributes zero argv elements so child YAML GA governs (D-12) | ✓ VERIFIED | `parse_args` EBS definition unchanged in the delta; tests green |
| 3 | `--subset_file` / `--cache_dir` resolved to absolute paths at sweep layer before threading (D-15); GA arithmetic stays child-side, integer-only pass-through (D-10/D-16) | ✓ VERIFIED | Resolution block present (`cache_dir_arg` adds a directories.json fallback before None — additive; absent-everywhere = byte-identical); no GA arithmetic added; tests green |
| 4 | `--subset_file` pre-validated collect-all at sweep start (every problem listed, before any cell enumerates) (D-14) | ✓ VERIFIED | Pre-validation zone intact (:1862-1868 via registry_loader); tests green |
| 5 | Manifest cells record flag fields ONLY when present; run_record.json field set untouched (D-13 / D-02 spirit) | ✓ VERIFIED | `sweep_flags` only-when-present discipline preserved for the four flags (new flags follow it); tests green |
| 6 | FlopsCounter's 20+ architecture dispatch ported with formulas verbatim, CPU-importable and stub-testable with no torch at module top, no GPU, no dnallm (SC2 / PIPE-01) | ✓ VERIFIED | `flops_counter.py` byte-identical (empty diff); live re-check: import succeeds CPU-side with `'torch' not in sys.modules`; 49 stub tests green |
| 7 | Dispatch order preserved: a Linear inside a borzoi-path model takes the Linear hook, not the borzoi branch | ✓ VERIFIED | File byte-unchanged; `test_linear_wins_over_borzoi_branch` green in this verifier's run |
| 8 | Every run_finetune execution calibrates FLOPs always-on (no flag), hooks removed BEFORE the DNATrainer ctor, single post-success flops_report.json write ordered final_metrics → flops_report → trainer_state marker inside the local_rank==0 guard, hardware captured verbatim (D-01/D-02/D-05, WR-13) | ✓ VERIFIED | `run_finetune.py` delta does not touch the calibration slot, hook lifetime, or write block (hunk-audited); contract tests green in this verifier's run |
| 9 | A real bounded GPU run emits flops_report.json: schema_version 1, attention + Linear hook keys, uncovered within threshold, hardware populated with the real device string, magnitude ratio in [0.05, 1.0] (SC2 runtime / D-22/D-23) | ✓ VERIFIED | GB10 smoke evidence stands (07-06; artifacts re-examined at prior passes); FLOPs chain core byte-identical since and the run_finetune delta is disjoint from the emission spans; see Warning W2 on evidence recency |
| 10 | Tolerant loader contract: `load_json_artifact` returns parsed doc for valid files, None for missing/unreadable/truncated/empty; valid-but-key-missing returned, not rejected (SC3 / PIPE-03 / D-17/D-18/D-19) | ✓ VERIFIED | `artifact_loader.py` byte-identical; live 4-case re-check this pass — missing/empty/truncated-UTF8 → None, valid → parsed dict; 9 tests green |
| 11 | Registry overlay seam: custom entries merge over official registries, collision fails fast naming key + BOTH paths, malformed custom fails loud, byte-identical when absent, official files never written, all five load sites rewired (SC4 / CUST-05 / D-06/D-07/D-08) | ✓ VERIFIED | `registry_loader.py` byte-identical; live byte-identity at the current 59/50 registry (equal dicts, equal key order, 0 official `enabled`); all registry loads in run_sweep/run_finetune/audit go through `registry_loader` (grep-verified this pass); 24-test suite green. Open finding CR-01 lives in the consumer/schema interplay OUTSIDE these clauses — see Warning W4 |
| 12 | Legacy file deleted with zero live-code references; five parity expectations re-pinned as sha-documented verbatim literals; archives untouched (D-04) | ✓ VERIFIED | Re-executed this pass: legacy absent; `grep -rn dnallmmark_pipeline pipeline/ script/ tests/ Makefile schemas/` → 0 lines; contract tests green |
| 13 | flops_report.json v1 schema published, strictly additive over legacy writer keys, schema_version const 1, optional hardware (D-27/D-02/D-03/D-05) | ✓ VERIFIED | `schemas/flops_report.json` byte-identical; round-trip test green in this verifier's run |
| 14 | `make lint` + `make typecheck` cover the changed files; full test lane green; zero GPU/dnallm in any gate (SC5) | ✓ VERIFIED | `make -n lint` re-proven (PHASE7_MODULES expansion intact; only the lint-only `QUICK_L6H_SCRIPTS` append added); typecheck recipe byte-unchanged (`--group dev --group tui`, CPU-side); phase-7 suites 302 green; full-suite failures are the documented machine baseline, none in phase-7 files |

**Score:** 14/14 truths verified (0 present, behavior-unverified)

### Advisory (New Scope, Unevidenced)

Re-verification ran (stale-fingerprint route); this section is recorded per the #3304 evidence-gate contract.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | None — every new-scope concern found this pass carries deterministic evidence (CR-01 reproduced; see Warnings W4) and was assessed against the must-haves in the open. | — | — |

### Required Artifacts

`gsd-tools verify artifacts` returns `total: 0` for these plans (plain string lists, not `{path, provides}` objects) — artifact status is from direct inspection, same as prior passes.

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pipeline/flops_counter.py` | FlopsCounter port: lazy torch seams, 20+ dispatch, uncovered accounting, save_to_json + v1 additions, count_split_tokens, build_hardware_section, calibration_forward | ✓ VERIFIED | Byte-identical since prior pass; live torch-free import re-checked; imported by run_finetune — WIRED |
| `pipeline/artifact_loader.py` | Tolerant load_json_artifact (D-17/D-18/D-19) | ✓ VERIFIED | Byte-identical; live 4-case contract re-check passed |
| `pipeline/registry_loader.py` | Overlay seam: custom_registry_dir, load_models_registry, load_datasets_registry (D-09 enabled-skip, UnicodeDecodeError sibling catch) | ✓ VERIFIED | Byte-identical; live byte-identity re-proven at n=59; wired at every registry load site (grep-verified) |
| `schemas/flops_report.json` | v1 strict contract (D-27) | ✓ VERIFIED | Byte-identical; round-trip test green |
| `tests/test_flops_counter.py` | Stub-nn harness, per-family arithmetic, schema pins, dispatch order, calibration chain | ✓ VERIFIED | Byte-identical; green |
| `tests/test_artifact_loader.py` | Tolerant-read contract cases | ✓ VERIFIED | Byte-identical; green |
| `tests/test_registry_loader.py` | Overlay merge/collision/malformed/resolution/byte-identity + run_finetune source-contract | ✓ VERIFIED | Byte-identical; green |
| `tests/test_sweep.py` | argv parity, pre-validation, manifest-field, byte-identity extensions | ✓ VERIFIED | Extended +416 lines by 261014-c2l/f4w (sanctioned family extensions); green |
| `tests/test_run_finetune_contracts.py` | Calibration-slot / write-ordering / rank-guard contracts + re-pinned parity literals | ✓ VERIFIED | Extended +266 lines by 261014-c2l/f4w; green |
| `Makefile` | Gate lanes: PHASE7_MODULES lint expansion, test lanes | ✓ VERIFIED | Delta-audited: PHASE7_MODULES definition + lint inclusion byte-unchanged; only `$(QUICK_L6H_SCRIPTS)` appended |
| `README.md` | Project documentation | ✓ VERIFIED | Delta-audited: +18 documentation lines (261014 quick-task docs); no pipeline-claim changes verified by prior passes |
| `pipeline/dnallmmark_pipeline.py` | DELETED (D-04) | ✓ VERIFIED (absence) | Re-checked this pass: not on disk, zero live references |

### Key Link Verification

Wiring re-confirmed this pass: FLOPs chain byte-identity + grep over the two changed drivers + green suites.

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| run_finetune calibration slot | flops_counter.FlopsCounter / build_hardware_section | sibling import | ✓ WIRED | Delta disjoint from calibration spans; contract tests green |
| run_finetune / run_sweep / audit registry loads | registry_loader | module import / importlib | ✓ WIRED | All load sites grep-verified this pass (`run_sweep` :579/:688/:766/:1721/:1868, `run_finetune` :744/:747, audit :98-100); 24-test suite green |
| FlopsCounter.save_to_json output | schemas/flops_report.json | round-trip test with Draft202012Validator | ✓ WIRED | Round-trip test green; schema byte-unchanged |
| sweep argv | run_finetune child flags | four sanctioned flags | ✓ WIRED | Four-flag block unchanged in the delta; suite green |
| Makefile lint | PHASE7_MODULES | wildcard existence guard | ✓ WIRED | Definition byte-unchanged; `make -n lint` expansion re-proven |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| flops_report.json (written) | report dict | FlopsCounter accumulators from real forward hooks | ✓ | Real GB10 report evidence stands (chain byte-unchanged; run_finetune delta disjoint) |
| manifest flag fields | sweep_flags | argparse / directories.json → main() resolution → _manifest_payload | ✓ | run_sweep delta hunk-audited; tests green |
| registry merged dict | registry | official JSON file + optional custom JSON file | ✓ | Live byte-identity re-check passed this pass (59/50) |

### Behavioral Spot-Checks

All executed by this verifier at HEAD `075a621`.

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Phase-7 test suites (6 files) | `.venv/bin/python -m pytest tests/test_flops_counter.py tests/test_registry_loader.py tests/test_sweep.py tests/test_artifact_loader.py tests/test_run_finetune_contracts.py tests/test_known_defects.py -q` | 302 passed in 0.78s | ✓ PASS |
| Torch-free CPU import | `python -I` — import flops_counter, registry_loader, artifact_loader + `'torch' not in sys.modules` | cpu-import-ok / torch-free-ok | ✓ PASS |
| Overlay byte-identity when absent | live: empty `DNALLMMARK_CUSTOM_REGISTRY_DIR` → load_models/datasets_registry vs official JSON | equal dicts AND equal key order (59/50); 0 official entries with `enabled` | ✓ PASS |
| Tolerant loader 4-case regression | live: valid/empty/truncated-UTF8/missing | valid→dict; others→None | ✓ PASS |
| Lint recipe PHASE7 expansion | `make -n lint` | three-file PHASE7 sequence present | ✓ PASS |
| Legacy absence + zero references | `test ! -e` + grep | absent / 0 lines | ✓ PASS |
| CR-01 seam-level reproduction | live: schema-valid minimal custom model entry → registry_loader merge → the exact run_finetune index expressions | entry schema-VALID, merges cleanly, then `KeyError: 'Model_name'` (:1008) and `KeyError: 'Mean_token_length'` (:1021) | ✓ REPRODUCED (defect confirmed — see Warning W4; not a must-have breach) |

### Probe Execution

Not applicable — phase declares no `scripts/*/tests/probe-*.sh` probes; the runtime proof is plan 07-06's GB10 smoke whose evidence stands with the FLOPs chain byte-unchanged and the run_finetune delta disjoint from the emission spans (this pass's git audit).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PIPE-01 | 07-01, 07-04, 07-05, 07-06 | FlopsCounter 20+ architecture port into run_finetune.py | ✓ SATISFIED | Truths 6-9, 12, 13 — FLOPs chain byte-unchanged, run_finetune delta disjoint; 302 tests green |
| PIPE-02 | 07-03, 07-06 | run_sweep argv passthrough of the four flags | ✓ SATISFIED | Truths 1-5 — four-flag threading intact through the 261014 delta; suite green |
| PIPE-03 | 07-01 | Tolerant loader JSON contract shared with the future monitor | ✓ SATISFIED | Truth 10 — live 4-case re-check passed |
| CUST-05 | 07-02 | Registry overlay: collision fail-fast, byte-identical when absent, existing tests zero-modification | ✓ SATISFIED | Truth 11 — byte-identity live-proven at 59/50; 24-test suite green; every enumerated clause holds (CR-01 assessed outside these clauses — W4) |

Orphan check: REQUIREMENTS.md maps exactly 4 IDs to Phase 7 (CUST-05, PIPE-01, PIPE-02, PIPE-03), all marked Complete; all four are claimed by plans and satisfied. No orphans.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| tests/test_sweep.py | PIPE-02 | all | 0 | no | Value (argv-shape literals, byte-identity) | OK |
| tests/test_flops_counter.py | PIPE-01 | all | 0 | no | Value (per-family arithmetic, schema pins, dispatch order) | OK |
| tests/test_registry_loader.py | CUST-05 | all | 0 (root-guard skips not hit this host at 43d3544; none observed in this run) | no | Value (collision message, merge equality) | OK |
| tests/test_artifact_loader.py | PIPE-03 | all | 0 | no | Value (4-case returns) | OK |
| tests/test_run_finetune_contracts.py | PIPE-01 | all | 0 | no | Value (source-order contracts, parity literals with source-commit provenance) | OK |

No disabled tests on requirements; no circular expected-value generation (parity literals are transcribed from git history with sha-documented provenance, the D-04 discipline).

### Decision Coverage

`check.decision-coverage-verify`: 27/27 trackable CONTEXT.md decisions honored by shipped artifacts; 0 not honored. (Non-blocking gate — recorded per #2492.)

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | Zero TBD/FIXME/XXX and zero TODO/HACK/PLACEHOLDER markers across all 10 changed covered files (re-scanned this pass); the byte-identical 9 stand clean from prior scans | - | - |

### Human Verification Required

N/A — Infrastructure/foundation phase (pipeline tooling, no user-facing elements). All acceptance criteria verified programmatically: six phase-7 suites green (302 passed), live behavioral contracts re-run (torch-free import, overlay byte-identity, tolerant-loader 4-case, lint expansion, legacy absence), the covered-set delta hunk-audited in full, and CR-01 deterministically reproduced and assessed. No ⚠️ PRESENT_BEHAVIOR_UNVERIFIED truths, no abstained non-inferable truths.

### Warnings (open items — none blocking a must-have)

| # | Finding | Severity | Impact |
|---|---------|----------|--------|
| W1 | ROADMAP SC4's consumer list names **export** among the overlay consumers, but `script/export_runs.py` was deliberately NOT rewired (locked decision D-09 scope). Re-checked this pass: the 5-line delta since the prior pass is a comment-only 62→59 update; export still joins registries via explicit `--models-info`/`--datasets-info` CLI paths. Documented-by-decision deviation, non-blocking. | ⚠️ Warning | Remains a documented-by-decision deviation |
| W2 | GPU emission evidence (Truth 9) predates Phases 8-12 and the 261014 series; the FLOPs chain core is byte-identical since the smoke and this pass's audit shows the run_finetune delta disjoint from the calibration/write spans — but strictly, the exact current tree state has not itself been GPU-run. | ℹ️ Info | Acceptable: a future bounded smoke under E2' will re-prove the tree |
| W3 | Review-disposition Info/Warning findings WR-01, WR-02, IN-01..IN-03 remain open by maintainer scope decision (`07-REVIEW-DISPOSITION.md`, all disposition `open`): stale repo-IDs in `model_performance/` display data (WR-01), empty-string handling on the 261014 directory flags (WR-02 — new flags, outside the four Phase 7 flags which keep their WR-05 empty-refusal), stale 62/50 schema `$comment` (IN-01), duplicated `gpu_memory_override` assignment (IN-02, pre-existing), registry data inconsistencies (IN-03, pre-existing). | ⚠️ Warning | Open for maintainer triage; none falsifies a Phase 7 must-have |
| W4 | **CR-01 (critical, disposition open) — assessed in full this pass, deterministically reproduced.** A minimal custom model entry carrying exactly the schema-required subset (`Model_path`, `size (M)`, `type`, `Tokenizer` per `schemas/custom_registry.json`) is schema-VALID, merges cleanly through the Phase 7 `registry_loader` seam, and then crashes the pipeline consumer: `run_finetune.py:1008` `model_row["Model_name"]` and `:1021` `model_row["Mean_token_length"]` are unguarded hard indexes (same class at `:1077`/`:1322` for datasets), so the run aborts with a raw `KeyError` naming neither the custom file nor the entry. **Why this is NOT a Phase 7 must-have breach:** every enumerated Truth 11 / SC4 / CUST-05 clause (merge, collision fail-fast naming key + both paths, malformed-JSON fail-loud, byte-identical-when-absent, official-files-never-written, five load sites) was live-verified this pass and holds — the crash requires an entry that is *well-formed* JSON; the fail-loud clause covers malformed files only. The defect is a field-completeness mismatch between the **Phase 9** custom-registry schema/wizard contract (which declares `Mean_token_length`/`Model_name`/`Dataset_name`/`length` optional — `schemas/custom_registry.json` and `tui/services/custom_validation.py`, both outside Phase 7's scope and covered set) and `run_finetune.py`'s hard indexing, whose provenance is commit `c6b3137` (the original file import, predating Phase 7 entirely — verified via `git log -S`; the post-prior-pass 261014 delta did not touch these sites, so this is not a regression). Phase 7's seam was deliberately validation-free at merge time (validation deferred to the TUI import path). **Why reported at full prominence anyway:** it is a real, evidenced, open critical defect in the CURRENT overlay chain's end-to-end robustness — a wizard-landed minimal entry would abort a multi-day bare sweep with an undiagnosable traceback. Fix belongs at the Phase 9 schema/wizard seam (or defense-in-depth in `registry_loader._load_registry`, per the review's two options). Recommend a `/gsd-quick` fix before the TUI wizard is used in anger; tracked open in `07-REVIEW-DISPOSITION.md`. | ⚠️ Warning (open critical review finding) | Does not block Phase 7's passed verdict; blocks real-world custom-entry usage until triaged |

### Re-Verification Record

- **Route:** #4682 stale fingerprint (fourth stale-fingerprint re-run over this phase; prior pass `passed` 14/14 at 2026-10-14T00:00:00Z / HEAD `43d3544`).
- **Staleness diagnosis confirmed:** `git diff --stat 43d3544..HEAD` over the covered set → 10 files changed (261014-c2l/f4w sibling-flag family + startup config in run_sweep/run_finetune and their tests; Makefile lint append; comment/doc updates); 9 covered files byte-identical including the whole FLOPs chain core and `registry_loader.py`.
- **Delta contract analysis:** every hunk audited against the 14-truth contract — four-flag threading, GA pass-through, manifest discipline, calibration/write spans, PHASE7 gate expansion all intact; no gate lane gains GPU/dnallm exposure.
- **Regression check:** all 14 truths verified against the current tree (live re-execution for the loader/overlay/legacy/gate contracts; delta audit + green 302-test run for the rest). Zero regressions.
- **CR-01 (open critical review finding):** fact-checked against the code, deterministically reproduced at the seam level, provenance-traced (`c6b3137`, pre-Phase-7; not a regression), and adjudicated against every enumerated must-have clause — no clause falsified; reported as Warning W4 with the reproduction and fix-ownership analysis.
- **Fingerprint recomputed** over the current tree via `verification.fingerprint`; `covered_digest` in the frontmatter is the command's verbatim output (`v3:sha256:88833025...16f837d`).

### Gaps Summary

No gaps. The stale fingerprint was diagnosed (the 261014 quick-task series plus the incremental review artifacts), the delta hunk-audited against every Phase 7 assertion (four-flag threading, GA pass-through, calibration/write contracts, PHASE7 gate expansion — all intact), all 14 must-have truths verified against the current tree, six phase-7 suites re-run green (302 passed), live overlay/tolerant-loader/torch-free-import/lint contracts re-executed, all 4 requirement IDs satisfied with no orphans, 27/27 decisions honored, zero debt markers, and the covered-input fingerprint regenerated at HEAD `075a621`. The open critical review finding CR-01 was reproduced and adjudicated: real and evidenced, but owned by the Phase 9 custom-registry schema/wizard surface plus pre-Phase-7 consumer indexing — no Phase 7 clause breaches; carried as Warning W4 for maintainer triage.

---

_Verified: 2026-10-14T11:28:53Z (stale refresh at HEAD 075a621; prior pass 2026-10-14T00:00:00Z at HEAD 43d3544)_
_Verifier: Claude (gsd-verifier)_
