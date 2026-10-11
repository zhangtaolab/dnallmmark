---
phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
verified: 2026-10-11T13:56:57Z
status: passed
score: 14/14 must-haves verified
covered_files: [".claude/CLAUDE.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-01-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-01-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-02-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-02-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-03-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-03-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-04-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-04-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-05-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-05-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-06-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-06-SUMMARY.md", "AUDIT.md", "Makefile", "README.md", "docs/TUI-REQUIREMENTS.md", "pipeline/artifact_loader.py", "pipeline/flops_counter.py", "pipeline/registry_loader.py", "pipeline/run_finetune.py", "pipeline/run_sweep.py", "schemas/flops_report.json", "script/audit_n_frequencies.py", "script/export_runs.py", "tests/test_artifact_loader.py", "tests/test_flops_counter.py", "tests/test_known_defects.py", "tests/test_registry_loader.py", "tests/test_run_finetune_contracts.py", "tests/test_sweep.py"]
covered_digest: "v3:sha256:a998bf8dc5e0ed4e342f841241164a984c2e47cc12010f95e1f13e617e6766fc"
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
**Verified:** 2026-10-11T13:56:57Z
**Status:** passed
**Re-verification:** Yes — #4682 stale-fingerprint route. Prior VERIFICATION.md (2026-10-11T08:27:07Z, passed 14/14, zero gaps) went stale because one covered file (`Makefile`) changed AFTER the verifier ran. This pass re-verified the phase goal against the CURRENT tree and recomputed the covered-input fingerprint.

## What Changed Since the Prior Pass (staleness diagnosis, verified)

File-level git audit of all 19 covered implementation files against the prior `verified:` timestamp:

- **`Makefile`** — the ONLY covered file modified (commits `ef56567`, `6b78026`: Phase 8's `[tui]` dependency/tooling spine + tracer). Diff audited hunk-by-hunk: purely additive — a new `tui` launch target, a `PHASE8_TUI` directory glob appended AFTER `$(PHASE7_MODULES)` in the lint invocation, `--group tui` added to the test/test-fast/ci/typecheck lanes, and comment-header updates. The `PHASE7_MODULES` definition line and its position in the lint recipe are byte-unchanged.
- **All 18 other covered implementation files** (`pipeline/flops_counter.py`, `pipeline/artifact_loader.py`, `pipeline/registry_loader.py`, `pipeline/run_finetune.py`, `pipeline/run_sweep.py`, `schemas/flops_report.json`, both `script/` files, all six test files, `.claude/CLAUDE.md`, `README.md`, `AUDIT.md`, `docs/TUI-REQUIREMENTS.md`): **zero commits since the prior verification** — Phase 7's code is untouched.
- Phase 8's 08-01 refactored `pipeline/env_smoke.py` (structured-return), but `env_smoke.py` is a Phase 5 file and is NOT in Phase 7's covered set; it sits in the lint list unchanged and does not participate in the FLOPs/argv/overlay/loader chains.

Because the only in-scope change is the Makefile, all 14 truths received a quick regression check (existence + sanity + green suite) and Truth 14 (the gates) received full re-execution on the current tree.

**Verification basis (all executed by this verifier against current HEAD `1697b0c`):** `make lint` exit 0 (all three PHASE7 modules observed in the ruff expansion, `$(PHASE8_TUI)` appended after them), `make typecheck` exit 0 (with Phase 8's `--group tui`), `make test-fast` **669 passed / 1 deselected / 0 failed**, `node --test tests/js/*.test.js` **18 pass / 0 fail**; live CPU torch-free import, live argv-parity / manifest-fields / tolerant-loader / overlay-byte-identity checks; re-validation of the on-disk GB10 smoke artifacts against the current-tree schema; symbol/wiring greps over every integration point; anti-pattern scan over all covered files.

## Goal Achievement

### Observable Truths

Must-haves merged from ROADMAP success criteria (1-5) plus the six PLAN frontmatter truth blocks, deduplicated — same 14-truth contract as the prior pass (re-verification reuses Step 0 must-haves verbatim).

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `run_sweep.py` accepts `--subset_file`, `--effective_batch_size`, `--num_train_epochs`, `--cache_dir` (underscore-only) and threads each as separate LIST elements in child argv only when present; byte-identical when absent (SC1 / PIPE-02 / D-11/D-13) | ✓ VERIFIED | `pipeline/run_sweep.py:358-401` (four registrations, underscore names only), `:1048-1058` (two-element argv appends), `:1522-1530` (sweep_flags only-when-present) — file unchanged since prior pass; live check `build_argv(..., effective_batch_size=16)` → `'16'` follows flag, all four flags thread their values, absent → none of the four strings (`argv-parity-ok`); `test_build_argv_threads_four_flags_as_list_elements`, `test_build_argv_absent_flags_add_zero_elements`, `test_dry_run_manifest_is_byte_deterministic` enumerated and green in this verifier's 669-test run |
| 2 | Bare `--effective_batch_size` yields 16; valued yields int; absent contributes zero argv elements so child YAML GA governs (D-12) | ✓ VERIFIED | `run_sweep.py:369-381`: `nargs="?", const=16, type=int, default=None`; `test_effective_batch_size_bare_valued_absent_parse` enumerated and green |
| 3 | `--subset_file` / `--cache_dir` resolved to absolute paths at sweep layer before threading (D-15); GA arithmetic stays child-side, integer-only pass-through (D-10/D-16) | ✓ VERIFIED | `run_sweep.py:1515-1519` (`Path(...).resolve()` before sweep_flags build), `:1495-1513` (WR-05 empty-value guards, present in tree); `bs_new` / `max(1, N // ...)` appear only in docstring/help prose (:49/:199/:378/:1008) — no GA computation executes in the sweep |
| 4 | `--subset_file` pre-validated collect-all at sweep start (every problem listed, before any cell enumerates) (D-14) | ✓ VERIFIED | `_validate_subset_file` at `run_sweep.py:649-713`, called at `:1537-1540` pre-enumeration against the overlay-merged registry view; `test_subset_file_collects_all_value_problems_together` enumerated and green |
| 5 | Manifest cells record flag fields ONLY when present; run_record.json field set untouched (D-13 / D-02 spirit) | ✓ VERIFIED | `_manifest_payload(matrix, records, sweep_flags=None)` at `run_sweep.py:1184-1208`; live check: present flag → `effective_batch_size: 16` in cell, absent → exactly the five base keys `{model, task, seed, status, output_dir}` (`manifest-fields-ok`); `test_run_record_untouched_by_sweep_flags` enumerated and green |
| 6 | FlopsCounter's 20+ architecture dispatch ported with formulas verbatim, CPU-importable and stub-testable with no torch at module top, no GPU, no dnallm (SC2 / PIPE-01) | ✓ VERIFIED | `pipeline/flops_counter.py` (937 lines, unchanged since prior pass which diffed hook bodies byte-identical vs `git show 1b74037e` legacy): module-top imports are `json`/`math`/`pathlib` only; torch resolves via `_torch_nn()` (:40) / `_torch()` (:850) lazy seams; live `cpu-import-ok` + `torch-free-ok` (`'torch' not in sys.modules` after import) in the dev lane; 49 stub tests green in the 669 run |
| 7 | Dispatch order preserved: a Linear inside a borzoi-path model takes the Linear hook, not the borzoi branch | ✓ VERIFIED | File unchanged since prior pass (branch order diffed identical vs legacy then); `test_linear_wins_over_borzoi_branch` enumerated and green now |
| 8 | Every run_finetune execution calibrates FLOPs always-on (no flag), hooks removed BEFORE the DNATrainer ctor, single post-success flops_report.json write ordered final_metrics → flops_report → trainer_state marker inside the local_rank==0 guard, hardware captured verbatim (D-01/D-02/D-05, WR-13) | ✓ VERIFIED | `run_finetune.py:1455-1494` (unconditional FlopsCounter ctor; `remove_hooks()` in both branches at :1478/:1480, before the trainer-init block), `:1604-1612` (`save_to_json` with `build_hardware_section(gpu_device, train_time, max_mem_gb)`; `gpu_device` verbatim from `torch.cuda.get_device_name()`; `shutil.copy(... trainer_state.json ...)` follows) — file unchanged since prior pass; all four contract tests (`test_calibration_hooks_removed_before_trainer_construction`, `test_final_metrics_then_flops_report_then_resume_marker`, `test_flops_report_write_rank_guarded`, `test_calibration_slot_between_encode_and_memory_reset`) enumerated and green |
| 9 | A real bounded GPU run emits flops_report.json: schema_version 1, attention + Linear hook keys, uncovered within threshold, hardware populated with the real device string, magnitude ratio in [0.05, 1.0] (SC2 runtime / D-22/D-23) | ✓ VERIFIED | Artifacts on disk at `pipeline/finetuned/plant-dnabert-6mer/iDNA_ABF_datasets__5mC/seed_9527/` (uncommitted, gitignored — D-26 holds): re-read this pass — `schema_version: 1`, `gpu_device: "NVIDIA GB10"`, `train_time: 65.0438`, `max_mem_gb: 1.5587`, `uncovered_layers: []`, ratio `2876164024320.0 / 8674442606400.0 = 0.3316` ∈ [0.05, 1.0], 13 top-level keys matching the 07-06 SUMMARY verbatim; **Draft202012 validation against the CURRENT-tree `schemas/flops_report.json`: 0 errors**. The smoke predates Phase 8's commits, but Phase 8 touched no Phase 7 pipeline file in the FLOPs chain (only `env_smoke.py`, outside the chain and the covered set) |
| 10 | Tolerant loader contract: `load_json_artifact` returns parsed doc for valid files, None for missing/unreadable/truncated/empty; valid-but-key-missing returned, not rejected (SC3 / PIPE-03 / D-17/D-18/D-19) | ✓ VERIFIED | `pipeline/artifact_loader.py` (45 lines, stdlib-only, unchanged); live 4-case check this pass — missing/empty/truncated-UTF8 → None, thin-valid `{}` → returned (`tolerant-loader-ok`); 9 tests green incl. `test_truncated_utf8_sequence_returns_none` and the round-trip pin `test_round_trip_stub_calibration_schema_and_loadback`. Production consumers are Phase 8 tui / Phase 11 monitor by design (D-19/D-20) — the contract is the deliverable and is test-pinned; Phase 8's `tui/services/` now exists and consumes this seam as planned |
| 11 | Registry overlay seam: custom entries merge over official registries, collision fails fast naming key + BOTH paths, malformed custom fails loud, byte-identical when absent, official files never written, all five load sites rewired (SC4 / CUST-05 / D-06/D-07/D-08) | ✓ VERIFIED | `pipeline/registry_loader.py` (172 lines, unchanged): read-only `"r"` opens only (:105/:111); live check this pass — empty pinned overlay dir → `load_models_registry() == json.loads(official)` (`absent-overlay-byte-identical-ok`); five sites re-confirmed by grep: run_sweep import :247 + loads :440/:441, :543/:544, :621/:622 (three load contexts) + `:1470`/`:1539`, run_finetune :42/:702/:705, audit via importlib `script/audit_n_frequencies.py:98-100`; 15 tests green. See Warning W1 on SC4's "export" consumer listing |
| 12 | Legacy file deleted with zero live-code references; five parity expectations re-pinned as sha-documented verbatim literals; archives untouched (D-04) | ✓ VERIFIED | `test ! -e pipeline/dnallmmark_pipeline.py` → absent; `grep -rn dnallmmark_pipeline pipeline/ script/ tests/ Makefile schemas/` → 0 lines; `git log --since=<prior verified ts> -- .planning/milestones/` → 0 commits (archives still untouched); re-pinned contracts suite green in the 669 run |
| 13 | flops_report.json v1 schema published, strictly additive over legacy writer keys, schema_version const 1, optional hardware (D-27/D-02/D-03/D-05) | ✓ VERIFIED | `schemas/flops_report.json` (107 lines, unchanged since prior pass which proved additivity by direct diff vs the legacy writer's report dict from `git show 1b74037e`); real GB10 report re-validated against this exact file: 0 errors; `test_round_trip_stub_calibration_schema_and_loadback` green; CR-01 guard confirmed in `save_to_json` (`num_tokens is not None and num_tokens > 0`, `flops_counter.py:756-771`) |
| 14 | `make lint` + `make typecheck` cover the changed files; full test lane green; zero GPU/dnallm in any gate (SC5) | ✓ VERIFIED | **Re-executed on the CURRENT (Phase-8-modified) Makefile:** `make lint` exit 0 — the ruff expansion observed listing `pipeline/flops_counter.py pipeline/registry_loader.py pipeline/artifact_loader.py` (PHASE7_MODULES intact) with `$(PHASE8_TUI)` files appended after; `make typecheck` exit 0 (now `--group dev --group tui ty check`); `make test-fast` 669 passed / 1 deselected (pytest lane, includes all six Phase 7 test files — 249 tests collected among them); `node --test tests/js/*.test.js` 18 pass / 0 fail. Phase 8's Makefile additions are lane-widening only and preserve every Phase 7 gate; the lanes remain GPU-free and dnallm-free |

**Score:** 14/14 truths verified (0 present, behavior-unverified)

### Advisory (New Scope, Unevidenced)

Re-verification ran (stale-fingerprint route); this section is recorded per the #3304 evidence-gate contract.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | None — no new-scope findings. The only covered file modified since the prior pass (Makefile) was fully re-verified with green gates; no unevidenced new-scope concern was raised. | — | — |

### Decision Coverage

Gate output (`check.decision-coverage-verify`, re-run this pass): 27/27 trackable CONTEXT.md decisions honored by shipped artifacts, 0 not honored, non-blocking.

### Required Artifacts

All Phase 7 artifacts unchanged since the prior pass except Makefile (additive Phase 8 lane changes, re-verified above). `gsd-tools verify artifacts` returns `total: 0` for these plans — the tool expects `{path, provides}` object entries while these plans declare plain string lists — so artifact status below is from direct inspection (existence + substantiveness + wiring), same as the prior pass.

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pipeline/flops_counter.py` | FlopsCounter port: lazy torch seams, 20+ dispatch, uncovered accounting, save_to_json + v1 additions, count_split_tokens, build_hardware_section, calibration_forward | ✓ VERIFIED | 937 lines; all symbols present; module-top torch-free (live-checked); imported by run_finetune (:48-51) — WIRED |
| `pipeline/artifact_loader.py` | Tolerant load_json_artifact (D-17/D-18/D-19) | ✓ VERIFIED | 45 lines, stdlib-only, stateless; contract pinned by 9 tests + round-trip; consumers are Phase 8/11 by design (D-19) — contract-pinned, not orphaned |
| `pipeline/registry_loader.py` | Overlay seam: custom_registry_dir, load_models_registry, load_datasets_registry | ✓ VERIFIED | 172 lines; collision fail-fast + fail-loud malformed; read-only opens only; imported by run_sweep, run_finetune, audit (importlib) — WIRED at all five sites |
| `schemas/flops_report.json` | v1 strict contract (D-27) | ✓ VERIFIED | 107 lines; validates the real GB10 report (0 errors this pass); additive-only over legacy keys proven by prior-pass diff |
| `tests/test_flops_counter.py` | Stub-nn harness, per-family arithmetic, schema pins, dispatch order, calibration chain | ✓ VERIFIED | 1114 lines; green in this verifier's run |
| `tests/test_artifact_loader.py` | Tolerant-read contract cases | ✓ VERIFIED | 88 lines; green |
| `tests/test_registry_loader.py` | Overlay merge/collision/malformed/resolution/byte-identity + run_finetune source-contract | ✓ VERIFIED | 343 lines; green |
| `tests/test_sweep.py` | argv parity, pre-validation, manifest-field, byte-identity extensions | ✓ VERIFIED | 2588 lines; green (96+ tests incl. the four-flag extensions) |
| `tests/test_run_finetune_contracts.py` | Calibration-slot / write-ordering / rank-guard contracts + re-pinned parity literals | ✓ VERIFIED | 2647 lines; green (64 contract tests) |
| `pipeline/dnallmmark_pipeline.py` | DELETED (D-04) | ✓ VERIFIED (absence) | Not on disk; git history retains at 1b74037e; zero live references |

### Key Link Verification

`gsd-tools verify key-links` likewise parses zero links from these plans' prose-style `key_links` entries; wiring below is from direct source inspection.

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| run_finetune calibration slot | flops_counter.FlopsCounter / count_split_tokens / calibration_forward / build_hardware_section | sibling import at `run_finetune.py:48-51`, calls at :1467/:1470/:1475/:1604/:1608 | ✓ WIRED | Import + all four symbols used at the integration points (re-read this pass) |
| run_finetune / run_sweep / audit registry loads | registry_loader | module import (run_sweep :247; run_finetune :42) / importlib spec_from_file_location (audit :98-100) | ✓ WIRED | Five sites re-confirmed by grep; `run_finetune --help` and headless `import run_sweep` green this pass |
| FlopsCounter.save_to_json output | schemas/flops_report.json | round-trip test with Draft202012Validator | ✓ WIRED | `test_round_trip_stub_calibration_schema_and_loadback` green; real GB10 report validates against current schema (0 errors) |
| save_to_json writes | artifact_loader.load_json_artifact | round-trip read-back | ✓ WIRED | Same round-trip test returns the identical dict |
| sweep argv | run_finetune child flags | `--cache_dir`, `--effective_batch_size`, `--subset_file`, `--num_train_epochs` (pre-existing child flags, zero child changes needed for threading) | ✓ WIRED | Child flags confirmed present; GA arithmetic child-side |
| Makefile lint | PHASE7_MODULES | wildcard existence guard | ✓ WIRED | `Makefile` PHASE7_MODULES definition byte-unchanged; all three modules observed in this verifier's ruff expansion; Phase 8's `$(PHASE8_TUI)` appended after — coverage widened, not narrowed |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| flops_report.json (written) | report dict | FlopsCounter accumulators from real forward hooks | ✓ | Real GB10 report on disk (re-read this pass) with hardware from `torch.cuda.get_device_name()` / train_runtime / peak-memory counter |
| manifest flag fields | sweep_flags | argparse → main() resolution → _manifest_payload | ✓ | Live-checked this pass: present flags merge into cells, absent add no keys |
| registry merged dict | registry | official JSON file + optional custom JSON file | ✓ | Live byte-identity check vs `json.loads(official)` this pass; merge exercised by tests |

### Behavioral Spot-Checks

All executed by this verifier against current HEAD `1697b0c`.

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Torch-free CPU import of the three modules | `uv run --group dev python -c "sys.path.insert(0,'pipeline'); import flops_counter, artifact_loader, registry_loader"` + `'torch' not in sys.modules` | cpu-import-ok / torch-free-ok | ✓ PASS |
| argv parity (present threads values, absent adds none) | direct `build_argv` assertions over all four flags | argv-parity-ok | ✓ PASS |
| Manifest only-when-present fields | direct `_manifest_payload` assertions | manifest-fields-ok | ✓ PASS |
| Tolerant loader None-sentinel + thin-JSON return | direct `load_json_artifact` 4-case check (missing/empty/truncated-UTF8/thin-valid) | tolerant-loader-ok | ✓ PASS |
| Overlay byte-identity when absent | `load_models_registry` vs `json.loads(official)` with empty pinned overlay dir | absent-overlay-byte-identical-ok | ✓ PASS |
| Full quality gates on the CURRENT Makefile | `make lint` / `make typecheck` / `make test-fast` / `node --test tests/js/*.test.js` | exit 0 / exit 0 / 669 passed 1 deselected / 18 pass 0 fail | ✓ PASS |
| GB10 smoke evidence re-validated on current tree | jsonschema Draft202012 validation of on-disk report + field reads | 0 schema errors; schema_version 1; NVIDIA GB10; ratio 0.3316; uncovered [] | ✓ PASS |
| Headless pipeline health | `import run_sweep`; `run_finetune.py --help` | sweep-import-ok / usage printed exit 0 | ✓ PASS |

### Probe Execution

Not applicable — phase declares no `scripts/*/tests/probe-*.sh` probes; the runtime proof is plan 07-06's GB10 smoke whose artifacts this verifier independently re-examined on disk and re-validated against the current-tree schema (Truth 9).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PIPE-01 | 07-01, 07-04, 07-05, 07-06 | FlopsCounter 20+ architecture port into run_finetune.py | ✓ SATISFIED | Truths 6, 7, 8, 9, 12, 13 |
| PIPE-02 | 07-03, 07-06 | run_sweep argv passthrough of the four flags | ✓ SATISFIED | Truths 1-5 (+ 07-06's live dry-run evidence; unit tests green this pass) |
| PIPE-03 | 07-01 | Tolerant loader JSON contract shared with the future monitor | ✓ SATISFIED | Truth 10 |
| CUST-05 | 07-02 | Registry overlay: collision fail-fast, byte-identical when absent | ✓ SATISFIED | Truth 11 (see Warning W1 on the SC4 "export" consumer listing — locked decision D-09 scope) |

Orphan check: REQUIREMENTS.md maps exactly 4 IDs to Phase 7 (CUST-05, PIPE-01, PIPE-02, PIPE-03); all four are claimed by plans and satisfied. No orphans.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| tests/test_flops_counter.py | PIPE-01/03 | 49 | 0 | 0 | Value (arithmetic equals, dict equality, schema validation) | OK |
| tests/test_artifact_loader.py | PIPE-03 | 9 | 0 (conditional root-guard, not taken — verifier uid 1001) | 0 | Value (None-vs-dict discrimination) | OK |
| tests/test_registry_loader.py | CUST-05 | 15 | 0 (conditional root-guard, not taken) | 0 | Value (dict equality, SystemExit message content) | OK |
| tests/test_sweep.py | PIPE-02 | extended | 0 | 0 | Value/Behavioral (argv element-by-element, manifest field presence/absence) | OK |
| tests/test_run_finetune_contracts.py | PIPE-01 | extended (+4 FLOPs contracts) | 0 | 0 | Behavioral (source-order index comparisons, rank-guard membership) | OK |

249 tests collected across the Phase 7 test files this pass, all green within the 669-passed fast lane. Key named tests enumerated and confirmed present (calibration-hook-removal, write-ordering, rank-guard, argv-parity, byte-determinism, borzoi-dispatch-order, round-trip). No disabled tests on requirements (WR-04 root guards are conditional, not taken). No circular patterns — the legacy file in git history (1b74037e) remains the independent oracle; expected-value provenance for the magnitude anchor is external (HF `total_flos`).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | Zero TBD/FIXME/XXX and zero TODO/HACK/PLACEHOLDER markers across all covered files including the Phase-8-modified Makefile (re-scanned this pass) | - | - |

**Warnings (non-blocking, carried forward from the prior pass — both still accurate against the current tree):**

| # | Finding | Severity | Impact |
|---|---------|----------|--------|
| W1 | ROADMAP SC4's consumer list names **export** among the overlay consumers, but `script/export_runs.py` was deliberately NOT rewired (locked decision D-09, user-selected at the discuss checkpoint). export_runs.py joins registries at runtime via explicit `--models-info`/`--datasets-info` CLI paths and would hard-fail on a custom-entry run exported with default paths rather than flowing through. The practical SC4 assertions (collision fail-fast, byte-identity when absent, tests unmodified, official files never written) all verify; the goal statement does not list export; no custom entries exist until Phase 9; escape hatch exists (`--models-info` with any registry file). | ⚠️ Warning | Surface to Phase 9 (CUST wizards): wire export through registry_loader or document the manual merged-file step |
| W2 | GPU emission evidence (Truth 9) was produced before HEAD; the intervening commits are Phase 8's, which touched no Phase 7 pipeline file in the FLOPs chain (env_smoke.py is outside it), and the on-disk report re-validates against the current-tree schema — but strictly, the exact current tree state has not itself been GPU-run. | ℹ️ Info | Acceptable: zero FLOPs-chain code changed since the smoke; a future bounded smoke under E2' will re-prove the tree |
| W3 | Review-disposition Info findings IN-01..IN-05 (unused `samples` var, duplicate gpu_memory_override assignment, README CLI docs missing the four sweep flags, CLAUDE.md 3.11+ vs README 3.13+ badge, CPU-run max_mem_gb 0.0 vs docstring) remain open by maintainer scope decision (2026-10-11 16:10 CST, `07-REVIEW-DISPOSITION.md`). | ℹ️ Info | Non-blocking; documentation/cleanup-tier, out of the CR+WR fix scope the maintainer chose |

### Human Verification Required

N/A — Infrastructure/foundation phase (pipeline tooling, no user-facing elements). All acceptance criteria are verifiable programmatically and were verified programmatically this pass: gates re-executed on the current tree (lint / typecheck / 669-test fast lane / 18-test JS lane), behavioral invariants covered by named tests that ran green in this verifier's test run, live behavioral checks re-run (argv parity, manifest fields, tolerant loader, overlay byte-identity, torch-free import), and runtime behavior evidenced by the real GB10 artifacts re-examined on disk and re-validated against the current-tree schema. No ⚠️ PRESENT_BEHAVIOR_UNVERIFIED truths, no abstained non-inferable truths.

### Re-Verification Record

- **Route:** #4682 stale fingerprint (prior pass `passed` 14/14; covered file `Makefile` changed after the verifier ran — Phase 8's dependency-lane additions, not Phase 7 semantic changes).
- **Staleness diagnosis confirmed:** `git log --since=2026-10-11T08:27:07Z` over all 19 covered implementation files → only `Makefile` modified (2 commits, additive); Phase 7's code is byte-unchanged since the prior pass.
- **Regression check:** all 14 truths quick-checked (existence + symbol sanity + wiring greps), full gates re-executed green on the current tree, live behavioral spot-checks re-run, GB10 artifacts re-validated against the current schema. Zero regressions.
- **Fingerprint recomputed** over the current tree via `verification.fingerprint` with the phase's implementation files (PLAN/SUMMARY files auto-added by the command); `covered_digest` in the frontmatter is the command's verbatim output.

### Gaps Summary

No gaps. The stale fingerprint was diagnosed (Makefile-only change, Phase 8's additive lane work), all 14 merged must-have truths re-verified against the current tree, the changed-file gate (Truth 14) fully re-executed (lint exit 0 with PHASE7 modules in the expansion, typecheck exit 0, 669-test fast lane green, JS lane 18/18), all 4 requirement IDs satisfied with no orphans, 27/27 decisions honored, zero debt markers, and the covered-input fingerprint regenerated at the current tree state. The three warnings are informational (W1 → Phase 9 follow-up; W2/W3 → evidence-recency and maintainer-scoped Info findings).

---

_Verified: 2026-10-11T13:56:57Z_
_Verifier: Claude (gsd-verifier)_
