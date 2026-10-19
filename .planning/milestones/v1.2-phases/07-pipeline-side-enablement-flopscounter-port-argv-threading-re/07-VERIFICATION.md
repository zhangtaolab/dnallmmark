---
phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
verified: 2026-10-17T07:40:16Z
status: passed
score: 14/14 must-haves verified
covered_files: [".claude/CLAUDE.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-01-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-01-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-02-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-02-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-03-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-03-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-04-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-04-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-05-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-05-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-06-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-06-SUMMARY.md", "AUDIT.md", "Makefile", "README.md", "docs/TUI-REQUIREMENTS.md", "pipeline/artifact_loader.py", "pipeline/flops_counter.py", "pipeline/registry_loader.py", "pipeline/run_finetune.py", "pipeline/run_sweep.py", "schemas/flops_report.json", "script/audit_n_frequencies.py", "script/export_runs.py", "tests/test_artifact_loader.py", "tests/test_flops_counter.py", "tests/test_known_defects.py", "tests/test_registry_loader.py", "tests/test_run_finetune_contracts.py", "tests/test_sweep.py"]
covered_digest: "v3:sha256:be9828f579234f9ffa1f309c9a979cad05065c1c0d703f32c1885c2d6b75127d"
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

**Phase Goal:** The pipeline can be fully driven, measured, and extended by an external operator tool — FlopsCounter's 20+ architecture forward-hook FLOPs instrumentation ported from the deprecated `dnallmmark_pipeline.py` into `run_finetune.py`, the four sanctioned `run_sweep.py` argv flags threaded through with per-cell artifact emission, and a registry-overlay loader so operator-side model/dataset metadata extends the committed registries without editing them
**Verified:** 2026-10-17T07:40:16Z
**Status:** passed
**Re-verification:** Yes — third refresh (micro). The round-2 pass (2026-10-17T04:48:42Z, `passed` 14/14, run at code HEAD `e41f9e6`, committed as `2212ee8`) went stale because its covered set changed once since: quick-task 261017-klw commit `6e331d3` — the 07-CR-01 disposition fix (guarded model-loop reads in `run_finetune.py` + a new AST source-contract test). This pass verified that delta directly against the current tree at HEAD `1cb8512`, re-checked the standing must-haves, adjudicated the CR-01 residual state explicitly, and recomputed the covered-input fingerprint.

## Re-verification (micro refresh, HEAD 1cb8512, 2026-10-17)

### Staleness diagnosis (commit-anchored, verified this pass)

`git diff --stat e41f9e6..HEAD` over the covered set — exactly **2 files**, both from commit `6e331d3` (fix(pipeline): guarded model-loop reads for minimal custom entries, 07-CR-01):

- **`pipeline/run_finetune.py` (+16/-2):** the two model-loop registry reads became guarded `.get` calls with adjudicated defaults — `model_name = model_row.get("Model_name", ix)` (the registry key is the fallback, exactly what `custom_entries.land()` stamps, so wizard-landed entries never hit it and `--target_model` filtering keeps working over the key for minimal hand-written entries) and `mean_token_len = model_row.get("Mean_token_length", 1)` (the no-compression floor; the sole consumer `max_length = int(data_length / mean_token_len) + 2` degrades to `data_length + 2`, over-long never truncating, still bounded by the max_token_len cap and the models_with_limited_length clamp). `Model_path` and `Tokenizer` stay hard-indexed (schema-REQUIRED). Plus 12 lines of explanatory comments.
- **`tests/test_run_finetune_contracts.py` (+139):** one new AST source-contract test (`test_minimal_custom_entry_reads_are_guarded`, read-source-never-import pattern) pinning (a) both guarded `.get` shapes with exactly those defaults inside the `for ix, model_row in models_info.items():` loop, (b) the negative — no bare `model_row[...]` subscript on `Model_name`/`Mean_token_length` anywhere in the module, and (c) the boundary — `Model_path`/`Tokenizer` must STAY hard-indexed (their absence is a malformed entry that must fail loudly).

**Byte-identical (empty diff) since the round-2 pass:** the other 29 covered files — `pipeline/flops_counter.py`, `pipeline/registry_loader.py`, `pipeline/artifact_loader.py`, `pipeline/run_sweep.py`, `schemas/flops_report.json`, the other five phase-7 test files, `Makefile`, `.claude/CLAUDE.md`, `AUDIT.md`, `README.md`, `docs/TUI-REQUIREMENTS.md`, `script/audit_n_frequencies.py`, `script/export_runs.py` — the entire FLOPs chain core, the overlay seam, the sweep driver, and the phase-7 test surface. Verified via `git diff --stat e41f9e6..HEAD -- <covered set>` (2 files only).

### Delta contract analysis vs the Phase 7 must-haves

1. **Four-flag threading (Truths 1-5) untouched** — `run_sweep.py` byte-identical; registrations re-read this pass (`:433` subset_file, `:444-446` effective_batch_size with `nargs="?" const=16`, `:458` num_train_epochs, `:468` cache_dir) and the LIST appends (`:1242-1248`).
2. **FLOPs chain intact, line-shifted only** — the fix lands ~500 lines upstream of the calibration span; all spans re-read directly this pass at their shifted positions: calibration block (`:1563` FlopsCounter ctor, `:1568` calibration_forward, `remove_hooks` in both branches `:1571/:1573`), write ordering (`:1638` `local_rank == 0` guard → `:1697` save_to_json → `:1705` marker copy, WR-13 last), hardware verbatim `torch.cuda.get_device_name()` (`:1693`). The ordering/lifetime contract tests green in this pass's run.
3. **Registry overlay seam untouched — and its consumer interplay IMPROVED** — `registry_loader.py` byte-identical; live torch-free import + overlay load re-checked this pass (59 models / 50 datasets). The CR-01 model-loop KeyError class (the prior W4 critical finding) is now closed at the two sites two prior verifiers adjudicated as this phase's seam ownership.
4. **No gate-lane GPU/dnallm exposure** — `Makefile` byte-identical; `make -n lint` still expands all three PHASE7 modules.
5. **Official-registry behavior byte-identical** — every official row carries both `Model_name` and `Mean_token_length`, so the `.get` defaults are dead code over official registries; the change only alters behavior for schema-legal minimal custom entries (crash → correct fallback), which is precisely the fix's intent.

### CR-01 residual state (explicit adjudication, per the refresh brief)

The fix (commit `6e331d3`) guards **only the model-loop sites** — `run_finetune.py:1015` and `:1035` in the current tree (the finding's `:1008`/`:1021`, shifted +14 by the fix's comments), now `.get`-guarded, AST-pinned by `test_minimal_custom_entry_reads_are_guarded` (green this pass). **Three sibling hard-index sites remain open by maintainer ruling** (klw SUMMARY Maintainer Items #2, "recorded, deliberately NOT fixed — outside the ruling's seven"), all re-confirmed present and unguarded in the current tree this pass:

- `:849` — the probe-variant guard's enumeration `[row["Model_name"] for row in models_info.values()]` (a minimal entry under `--config-variant probe` without `--target_model` crashes before the refusal check);
- `:1091` — the dataset loop's `row["Dataset_name"]` (schema-OPTIONAL for custom datasets the same way `Model_name` is for models);
- `:1336` — `data_length = row["length"]` (the dataset row's `length` field).

These belong to a future maintainer-ruled batch (same guarded-read pattern + AST pin; the dataset side needs its own defaults adjudicated). The phase-local ledger `07-REVIEW-DISPOSITION.md` still records CR-01 `open` — factually accurate as titled ("required-field sets are inconsistent across the overlay chain"), since the sibling sites genuinely still raise the same KeyError class. **Not a Phase 7 must-have breach** (unchanged adjudication): every enumerated Truth 11 / SC4 / CUST-05 clause — merge, collision fail-fast naming key + both paths, malformed-JSON fail-loud, byte-identical-when-absent, official-files-never-written, load sites — holds; the crash class requires *well-formed* JSON entries, which the fail-loud clause does not cover.

### Re-verified verdicts (all 14 truths)

| Must-have | Verdict | Basis this pass |
|---|---|---|
| T1-T5 (four flags: threading, bare-EBS=16, abs-resolution, D-14 pre-validation, only-when-present manifest) | ✓ VERIFIED | `run_sweep.py` byte-identical; registrations (`:433/:444-446/:458/:468`) and LIST appends (`:1242-1248`) re-read this pass; green in the 303-test run |
| T6-T9, T13 (FlopsCounter port, dispatch order, always-on calibration, GPU emission, v1 schema) | ✓ VERIFIED | `flops_counter.py` + `schemas/flops_report.json` byte-identical; live torch-free CPU import re-checked (`'torch' not in sys.modules`); calibration and write spans re-read directly at shifted positions in `run_finetune.py`; GB10 smoke evidence stands; contract tests green |
| T10 (tolerant loader) | ✓ VERIFIED | `artifact_loader.py` byte-identical; green in this pass's run |
| T11 (registry overlay: byte-identical-when-absent, collision fail-fast, fail-loud, merge, resolution, load sites) | ✓ VERIFIED | `registry_loader.py` byte-identical; live import + overlay load re-checked (59/50); load sites before the diff hunk unshifted (`run_finetune` :744/:747); 24-test suite green. **CR-01 model-loop consumer sites now FIXED** (see residual adjudication) |
| T12 (legacy deleted, zero references) | ✓ VERIFIED | Re-executed this pass: legacy absent on disk; `grep -rn dnallmmark_pipeline pipeline/ script/ tests/ Makefile schemas/` → 0 lines |
| T14 (lint/typecheck/test gates, GPU-free/dnallm-free) | ✓ VERIFIED | `make -n lint` re-proven — all three PHASE7 modules expand; phase-7 suites 303 green this pass; known-good full-tree gates on this exact HEAD recorded by the orchestrator (full suite 1F/1867P with the sole failure the machine-local `test_services_run_config` member; node 26/26; ruff + ty green; goldens untouched) |

### Spot-checks (executed by this verifier at HEAD 1cb8512)

| Command | Result | Status |
|---|---|---|
| `.venv/bin/python -m pytest tests/test_flops_counter.py tests/test_registry_loader.py tests/test_sweep.py tests/test_artifact_loader.py tests/test_run_finetune_contracts.py tests/test_known_defects.py -q` | **303 passed in 0.76s** (prior 302 + the new AST guard test) | ✓ PASS |
| `.venv/bin/python -m pytest tests/test_run_finetune_contracts.py::test_minimal_custom_entry_reads_are_guarded -q` (single named test — the 07-CR-01 fix's behavioral pin) | **1 passed** | ✓ PASS |
| `.venv/bin/python -I` torch-free import (`flops_counter`, `registry_loader`, `artifact_loader` + symbol presence + live overlay load) | torch-free-ok; 59 models / 50 datasets through the overlay seam | ✓ PASS |
| Guarded reads in source | `:1015` `model_row.get("Model_name", ix)`; `:1035` `model_row.get("Mean_token_length", 1)`; `Model_path` (`:1026`) / `Tokenizer` (`:1027`) hard-indexed | ✓ PASS |
| Sibling hard-index residual sites | `:849` / `:1091` / `:1336` unguarded — exactly as recorded in the klw maintainer ruling | ✓ CONFIRMED (recorded residual) |
| Four-flag registrations + LIST appends | `:433/:444-446/:458/:468`; `:1242-1248`; `nargs="?" const=16` | ✓ PASS |
| FLOPs calibration/write spans (shifted) | ctor `:1563`, `remove_hooks` `:1571/:1573`, `local_rank==0` `:1638` → `save_to_json` `:1697` → marker copy `:1705`, `get_device_name()` `:1693` | ✓ PASS |
| `make -n lint` PHASE7 expansion | all three phase-7 modules present | ✓ PASS |
| Legacy absence + zero references | absent / 0 lines | ✓ PASS |
| Debt markers (`TBD\|FIXME\|XXX`) over the 2 changed covered files | 0 hits | ✓ PASS |

**Known-good full-tree gates on this exact HEAD (1cb8512), recorded by the orchestrator — not re-run per the refresh brief:** full pytest 1867 passed / 1 failed (`tests/tui/test_services_run_config.py::test_storage_overview_defaults_mirror_real_consumers` — machine-local `pipeline/logs` state; fresh-checkout green; the documented 1F baseline membership, 1867 = prior 1858 + klw's 9 new tests all green), node suite 26/26, ruff + ty green, snapshot goldens untouched.

**Fresh fingerprint (verbatim from `verification.fingerprint`):** `v3:sha256:be9828f579234f9ffa1f309c9a979cad05065c1c0d703f32c1885c2d6b75127d` over the same 31-entry covered set as the prior pass (frontmatter `covered_files` is the command's verbatim output).

---

## Goal Achievement

### Observable Truths

Must-haves carried forward verbatim from the prior pass (the 14-truth contract derived from ROADMAP SC1-SC5 plus the six PLANs' must_haves; unchanged because the plans did not change).

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `run_sweep.py` accepts `--subset_file`, `--effective_batch_size`, `--num_train_epochs`, `--cache_dir` (underscore-only) and threads each as separate LIST elements in child argv only when present; byte-identical when absent (SC1 / PIPE-02 / D-11/D-13) | ✓ VERIFIED | `run_sweep.py` byte-identical since the round-2 pass; registrations + LIST appends re-read this pass (:433/:444-446/:458/:468, :1242-1248); suite green (303 passed); zero hyphen aliases |
| 2 | Bare `--effective_batch_size` yields 16; valued yields int; absent contributes zero argv elements so child YAML GA governs (D-12) | ✓ VERIFIED | `nargs="?" const=16 type=int default=None` re-read this pass; tests green in the 303 |
| 3 | `--subset_file` / `--cache_dir` resolved to absolute paths at sweep layer before threading (D-15); GA arithmetic stays child-side, integer-only pass-through (D-10/D-16) | ✓ VERIFIED | File byte-unchanged; only docstring/help prose mentions `max(1, N // bs_new)`; tests green |
| 4 | `--subset_file` pre-validated collect-all at sweep start (every problem listed, before any cell enumerates) (D-14) | ✓ VERIFIED | File byte-unchanged; `_validate_subset_file` + call site intact; tests green |
| 5 | Manifest cells record flag fields ONLY when present; run_record.json field set untouched (D-13 / D-02 spirit) | ✓ VERIFIED | File byte-unchanged; present-only `sweep_flags` construction intact; tests green |
| 6 | FlopsCounter's 20+ architecture dispatch ported with formulas verbatim, CPU-importable and stub-testable with no torch at module top, no GPU, no dnallm (SC2 / PIPE-01) | ✓ VERIFIED | `flops_counter.py` byte-identical; live re-check this pass: import succeeds CPU-side with `'torch' not in sys.modules`; stub tests green (in the 303) |
| 7 | Dispatch order preserved: a Linear inside a borzoi-path model takes the Linear hook, not the borzoi branch | ✓ VERIFIED | File byte-unchanged; `test_linear_wins_over_borzoi_branch` green in this verifier's run |
| 8 | Every run_finetune execution calibrates FLOPs always-on (no flag), hooks removed BEFORE the DNATrainer ctor, single post-success flops_report.json write ordered final_metrics → flops_report → trainer_state marker inside the local_rank==0 guard, hardware captured verbatim (D-01/D-02/D-05, WR-13) | ✓ VERIFIED | Spans re-read directly this pass at their +14-shifted positions — calibration (ctor :1563, `remove_hooks` both branches :1571/:1573, before the DNATrainer ctor), write ordering (:1638 guard → :1697 `save_to_json` → :1705 marker copy), `torch.cuda.get_device_name()` verbatim (:1693); the klw delta is confined to the model loop ~500 lines upstream and cannot touch these spans; the four ordering/lifetime contract tests green in this verifier's run (303) |
| 9 | A real bounded GPU run emits flops_report.json: schema_version 1, attention + Linear hook keys, uncovered within threshold, hardware populated with the real device string, magnitude ratio in [0.05, 1.0] (SC2 runtime / D-22/D-23) | ✓ VERIFIED | GB10 smoke evidence stands (07-06-SUMMARY: ratio 0.3316, `gpu_device "NVIDIA GB10"` verbatim, uncovered_layers empty); FLOPs chain core byte-identical since the smoke; the klw delta (guarded registry reads upstream of calibration, dead code over official registries) is disjoint from the emission spans; see Warning W2 on evidence recency |
| 10 | Tolerant loader contract: `load_json_artifact` returns parsed doc for valid files, None for missing/unreadable/truncated/empty; valid-but-key-missing returned, not rejected (SC3 / PIPE-03 / D-17/D-18/D-19) | ✓ VERIFIED | `artifact_loader.py` byte-identical; 9 tests green in this pass's run |
| 11 | Registry overlay seam: custom entries merge over official registries, collision fails fast naming key + BOTH paths, malformed custom fails loud, byte-identical when absent, official files never written, all load sites rewired (SC4 / CUST-05 / D-06/D-07/D-08) | ✓ VERIFIED | `registry_loader.py` byte-identical; live overlay load re-checked this pass (59/50); load sites grep-verified (pre-hunk sites unshifted); 24-test suite green. **CR-01 status improved: the model-loop consumer sites (the prior W4 crash class) are now FIXED and AST-pinned** — see the residual adjudication for the three maintainer-ruled sibling sites |
| 12 | Legacy file deleted with zero live-code references; five parity expectations re-pinned as sha-documented verbatim literals; archives untouched (D-04) | ✓ VERIFIED | Re-executed this pass: legacy absent; grep over `pipeline/ script/ tests/ Makefile schemas/` → 0 lines; contract tests green |
| 13 | flops_report.json v1 schema published, strictly additive over legacy writer keys, schema_version const 1, optional hardware (D-27/D-02/D-03/D-05) | ✓ VERIFIED | `schemas/flops_report.json` byte-identical; round-trip test green in this verifier's run |
| 14 | `make lint` + `make typecheck` cover the changed files; full test lane green; zero GPU/dnallm in any gate (SC5) | ✓ VERIFIED | `make -n lint` re-proven (three-file PHASE7 expansion); phase-7 suites 303 green this pass; full-tree gates known-good on this exact HEAD (1F/1867P machine-local baseline, node 26/26, ruff + ty green, goldens untouched) |

**Score:** 14/14 truths verified (0 present, behavior-unverified)

### Advisory (New Scope, Unevidenced)

Re-verification ran (stale-fingerprint route); this section is recorded per the #3304 evidence-gate contract.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | None — no new-scope Step 7 finding arose this pass; the covered-set delta is the single audited 07-CR-01 fix commit (`6e331d3`, 2 files, every hunk analyzed above). The CR-01 residual sibling sites are a maintainer-recorded carried item, not a new-scope discovery, and are reported at full prominence as Warning W4. | — | — |

### Required Artifacts

`gsd-tools verify artifacts` treats these plans' plain string artifact lists as `total: 0` — artifact status is from direct inspection, same as prior passes.

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pipeline/flops_counter.py` | FlopsCounter port: lazy torch seams, 20+ dispatch, uncovered accounting, save_to_json + v1 additions, count_split_tokens, build_hardware_section, calibration_forward | ✓ VERIFIED | Byte-identical since round-2; live torch-free import re-checked; imported by run_finetune (:58-61) — WIRED |
| `pipeline/artifact_loader.py` | Tolerant load_json_artifact (D-17/D-18/D-19) | ✓ VERIFIED | Byte-identical; green in the 303 |
| `pipeline/registry_loader.py` | Overlay seam: custom_registry_dir, load_models_registry, load_datasets_registry | ✓ VERIFIED | Byte-identical; live load re-checked at n=59/50; wired at every registry load site |
| `pipeline/run_finetune.py` | Calibration slot + write-ordering integration + guarded registry reads (07-CR-01 fix) | ✓ VERIFIED | Delta-audited in full this pass: only the two model-loop reads changed (guarded `.get`), FLOPs spans re-read intact; AST contract test pins the new shape; green in the 303 |
| `schemas/flops_report.json` | v1 strict contract (D-27) | ✓ VERIFIED | Byte-identical; round-trip test green |
| `tests/test_flops_counter.py` | Stub-nn harness, per-family arithmetic, schema pins, dispatch order, calibration chain | ✓ VERIFIED | Byte-identical; green |
| `tests/test_artifact_loader.py` | Tolerant-read contract cases | ✓ VERIFIED | Byte-identical; green |
| `tests/test_registry_loader.py` | Overlay merge/collision/malformed/resolution/byte-identity + run_finetune source-contract | ✓ VERIFIED | Byte-identical; green |
| `tests/test_sweep.py` | argv parity, pre-validation, manifest-field, byte-identity extensions | ✓ VERIFIED | Byte-identical; green |
| `tests/test_run_finetune_contracts.py` | Calibration-slot / write-ordering / rank-guard contracts + re-pinned parity literals + 07-CR-01 AST guard pin | ✓ VERIFIED | +139 lines this refresh (the new AST test, substantive: pins guarded shapes, the negative, and the hard-index boundary); 74 tests collected, all green |
| `Makefile` | Gate lanes: PHASE7_MODULES lint expansion, test lanes | ✓ VERIFIED | Byte-identical; expansion re-proven |
| `README.md` | Project documentation | ✓ VERIFIED | Byte-identical since round-2 |
| `script/audit_n_frequencies.py` | N-frequency audit wired through registry_loader | ✓ VERIFIED | Byte-identical |
| `pipeline/dnallmmark_pipeline.py` | DELETED (D-04) | ✓ VERIFIED (absence) | Re-checked this pass: not on disk, zero live references |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| run_finetune calibration slot | flops_counter.FlopsCounter / build_hardware_section / calibration_forward / count_split_tokens | sibling import (:58-61) + calibration block (:1553-1573) | ✓ WIRED | Re-read directly this pass; contract tests green |
| run_finetune / run_sweep / audit registry loads | registry_loader | module import / importlib | ✓ WIRED | `run_sweep` :579/:580/:688/:689/:766/:767/:1721/:1868 (byte-identical file), `run_finetune` :744/:747 (pre-hunk, unshifted), audit :622; 24-test suite green |
| FlopsCounter.save_to_json output | schemas/flops_report.json | round-trip test with Draft202012Validator | ✓ WIRED | Round-trip test green; schema byte-unchanged |
| sweep argv | run_finetune child flags | four sanctioned flags | ✓ WIRED | Four-flag block byte-unchanged; registrations re-read this pass |
| Makefile lint | PHASE7_MODULES | wildcard existence guard | ✓ WIRED | Definition byte-unchanged; `make -n lint` expansion re-proven |
| minimal custom model entry → model loop | guarded `.get` reads (:1015/:1035) | AST source-contract test | ✓ WIRED | `test_minimal_custom_entry_reads_are_guarded` green this pass — the fix is pinned, not just present |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| flops_report.json (written) | report dict | FlopsCounter accumulators from real forward hooks | ✓ | Real GB10 report evidence stands (chain byte-unchanged; delta disjoint) |
| manifest flag fields | sweep_flags | argparse / directories.json → main() resolution → _manifest_payload | ✓ | run_sweep byte-unchanged |
| registry merged dict | registry | official JSON file + optional custom JSON file | ✓ | Live load re-checked this pass (59/50) |
| model-loop registry reads | model_name / mean_token_len | `model_row.get(field, adjudicated default)` | ✓ | Defaults are registry key / no-compression floor 1 — real fallback semantics, dead code over official registries, correct behavior for minimal customs (AST-pinned) |

### Behavioral Spot-Checks

Executed by this verifier at HEAD `1cb8512` (see the re-verification section's spot-check table). Full-suite and node/lint/typecheck evidence is the orchestrator's known-good record on this exact HEAD (not re-run per the refresh brief).

### Probe Execution

Not applicable — phase declares no `scripts/*/tests/probe-*.sh` probes; the runtime proof is plan 07-06's GB10 smoke whose evidence stands with the FLOPs chain byte-unchanged since.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PIPE-01 | 07-01, 07-04, 07-05, 07-06 | FlopsCounter 20+ architecture port into run_finetune.py | ✓ SATISFIED | Truths 6-9, 12, 13 — FLOPs chain byte-unchanged, spans re-read intact; 303 tests green |
| PIPE-02 | 07-03, 07-06 | run_sweep argv passthrough of the four flags | ✓ SATISFIED | Truths 1-5 — four-flag threading intact (registrations re-read); tests green |
| PIPE-03 | 07-01 | Tolerant loader JSON contract shared with the future monitor | ✓ SATISFIED | Truth 10 — loader byte-identical; tests green |
| CUST-05 | 07-02 | Registry overlay: collision fail-fast, byte-identical when absent, existing tests zero-modification | ✓ SATISFIED | Truth 11 — every enumerated clause holds; live overlay load re-checked (59/50); 24-test suite green; the CR-01 model-loop consumer crash class is now FIXED (guarded reads + AST pin), improving the real-world custom-entry path this requirement exists for |

Orphan check: REQUIREMENTS.md maps exactly 4 IDs to Phase 7 (CUST-05 :28, PIPE-01 :60, PIPE-02 :61, PIPE-03 :62), all marked Complete (matrix :105/:122-124); all four are claimed by plans and satisfied. No orphans.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| tests/test_sweep.py | PIPE-02 | all | 0 | no | Value (argv-shape literals, byte-identity) | OK |
| tests/test_flops_counter.py | PIPE-01 | all | 0 | no | Value (per-family arithmetic, schema pins, dispatch order) | OK |
| tests/test_registry_loader.py | CUST-05 | all | 0 | no | Value (collision message, merge equality) | OK |
| tests/test_artifact_loader.py | PIPE-03 | all | 0 | no | Value (4-case returns) | OK |
| tests/test_run_finetune_contracts.py | PIPE-01 | all | 0 | no | Value (source-order contracts, parity literals with source-commit provenance; new AST structural pin asserts shapes + negative + boundary — not circular) | OK |

Skip-marker scan: 0 hits across the six files (303 green). No disabled tests on requirements; the new AST test is substantive (three-way assertion: guarded shapes with exact defaults, module-wide negative on bare subscripts, hard-index boundary for the schema-REQUIRED pair).

### Decision Coverage

Non-blocking gate. The prior pass recorded 27/27 trackable CONTEXT.md decisions honored; `07-CONTEXT.md` is unchanged since (outside the covered delta), so that figure stands. (Note: the `check.decision-coverage-verify` query skips on this phase's numbered-filename layout — `07-CONTEXT.md` vs the tool's expected `CONTEXT.md` — reported as skipped, blocking: false; figure carried from the prior verified pass over the identical file.)

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | Zero TBD/FIXME/XXX markers in the 2 changed covered files (`pipeline/run_finetune.py`, `tests/test_run_finetune_contracts.py`, re-scanned this pass); the byte-identical 29 stand clean from prior scans | - | - |

### Human Verification Required

N/A — Infrastructure/foundation phase (pipeline tooling, no user-facing elements). All acceptance criteria verified programmatically: six phase-7 suites green (303 passed), the 07-CR-01 fix verified directly (guarded reads in source + named AST contract test green), sibling residual sites confirmed against the maintainer ruling record, live torch-free import + overlay load, four-flag registrations, FLOPs spans, lint expansion, and legacy absence re-checked, and known-good full-tree gates (1F/1867P machine-local baseline / node 26/26 / ruff+ty green / goldens untouched) recorded on the identical HEAD. No ⚠️ PRESENT_BEHAVIOR_UNVERIFIED truths, no abstained non-inferable truths.

### Warnings (open items — none blocking a must-have)

| # | Finding | Severity | Impact |
|---|---------|----------|--------|
| W1 | ROADMAP SC4 / CUST-05's consumer list names **export** among the overlay consumers, but `script/export_runs.py` was deliberately NOT rewired (locked decision D-09 scope; verified it loads no registries at runtime — custom entries flow into exports through run records). File byte-identical. Documented-by-decision deviation, non-blocking. | ⚠️ Warning | Remains a documented-by-decision deviation |
| W2 | GPU emission evidence (Truth 9) predates Phases 8-12 and the 261015-261017 series; the FLOPs chain core is byte-identical since the smoke and the klw delta is confined to model-loop registry reads upstream of calibration (dead code over official registries) — but strictly, the exact current tree state has not itself been GPU-run. | ℹ️ Info | Acceptable: a future bounded smoke under E2' will re-prove the tree |
| W3 | Review-disposition ledger state re-checked this pass (`07-REVIEW-DISPOSITION.md`): WR-01..WR-04 / IN-01 remain `fixed`; IN-02 (duplicated `gpu_memory_override` assignment, pre-existing) and IN-03 (pre-existing registry data inconsistencies) remain `open`. CR-01's ledger row also remains `open` — accurate as titled, because the finding spans the whole overlay-chain field-set inconsistency, of which the model-loop half is now fixed and the sibling half remains (W4). | ⚠️ Warning | Open carried rows await maintainer triage; none falsifies a Phase 7 must-have |
| W4 | **CR-01 — model-loop half FIXED this refresh; sibling half remains open by maintainer ruling.** The two sites two prior verifiers adjudicated as this phase's seam ownership (`run_finetune.py` model-loop `Model_name` / `Mean_token_length` reads, formerly :1008/:1021) are now guarded `.get` reads with adjudicated defaults (registry-key fallback; no-compression floor 1) and pinned by a new AST source-contract test (`test_minimal_custom_entry_reads_are_guarded`, green; commit `6e331d3`). **Residual:** three sibling hard-index sites will still raise the same KeyError class for schema-legal minimal entries when their code paths run — `:849` probe-variant enumeration `row["Model_name"]` (minimal entry + `--config-variant probe` without `--target_model`), `:1091` dataset-loop `row["Dataset_name"]`, `:1336` `data_length = row["length"]` — all re-confirmed unguarded this pass. These are recorded, deliberately NOT fixed, outside the fix batch's ruling (klw SUMMARY Maintainer Items #2: "belong to a future maintainer-ruled batch; the dataset side needs its own defaults adjudicated"). **Still not a Phase 7 must-have breach** (unchanged adjudication): every Truth 11 / SC4 / CUST-05 clause holds; the crash class requires well-formed JSON the fail-loud clause does not cover. | ⚠️ Warning (maintainer-ruled residual) | Does not block Phase 7's passed verdict; sibling sites block real-world minimal custom DATASET entries and the probe-variant path until the future batch |

### Re-Verification Record

- **Route:** stale fingerprint (third refresh over this phase; prior pass `passed` 14/14 at 2026-10-17T04:48:42Z, code HEAD `e41f9e6`, committed `2212ee8`).
- **Staleness diagnosis confirmed:** `git diff --stat e41f9e6..HEAD` over the covered set → exactly 2 files, both from the 07-CR-01 fix commit `6e331d3` (`pipeline/run_finetune.py` +16/-2 guarded model-loop reads; `tests/test_run_finetune_contracts.py` +139 AST contract test); the other 29 covered files byte-identical.
- **Delta contract analysis:** every hunk audited against the 14-truth contract — the fix is confined to the model loop ~500 lines upstream of the FLOPs calibration/write spans (re-read intact at shifted positions), the `.get` defaults are dead code over official registries (behavior byte-identical), and the change closes the exact crash class prior passes carried as W4.
- **Regression check:** all 14 truths verified against the current tree (six phase-7 suites 303 green; named AST guard test green; live torch-free import + overlay load; four-flag registrations; FLOPs spans; lint expansion; legacy absence; zero debt markers). Zero regressions.
- **CR-01 residual adjudication:** model-loop sites FIXED + AST-pinned; sibling sites `:849`/`:1091`/`:1336` confirmed open per the maintainer ruling recorded in the klw SUMMARY; ledger row remains `open` (accurate as titled). Detailed under W4.
- **Fingerprint recomputed** over the current tree via `verification.fingerprint`; `covered_digest` in the frontmatter is the command's verbatim output (`v3:sha256:be9828f5...5127d`).

### Gaps Summary

No gaps. The stale fingerprint was diagnosed (the single 07-CR-01 fix commit `6e331d3`, 2 covered files; the remaining 29 byte-identical), the delta audited in full against every Phase 7 assertion (all intact; the FLOPs spans only line-shifted, re-read directly), all 14 must-have truths verified against the current tree at HEAD `1cb8512`, the six phase-7 suites re-run green (303 passed, including the new AST guard pin), live overlay/torch-free-import/lint/legacy/registration contracts re-checked, all 4 requirement IDs satisfied with no orphans, zero debt markers on changed files, known-good full-tree gate evidence (1F/1867P machine-local baseline / node 26/26 / ruff + ty green / goldens untouched) recorded on the identical HEAD, and the covered-input fingerprint regenerated. The 07-CR-01 finding's model-loop half — carried as W4 through two prior passes — is now fixed and contract-pinned; its sibling half (three hard-index sites) remains open by explicit maintainer ruling, recorded for a future batch, and adjudicated as no Phase 7 must-have breach.

---

_Verified: 2026-10-17T07:40:16Z (third refresh at HEAD 1cb8512; prior pass 2026-10-17T04:48:42Z at code HEAD e41f9e6, committed 2212ee8)_
_Verifier: Claude (gsd-verifier)_
