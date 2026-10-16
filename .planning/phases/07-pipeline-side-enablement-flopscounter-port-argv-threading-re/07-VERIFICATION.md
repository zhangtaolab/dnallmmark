---
phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
verified: 2026-10-15T23:59:53Z
status: passed
score: 14/14 must-haves verified
covered_files: [".claude/CLAUDE.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-01-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-01-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-02-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-02-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-03-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-03-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-04-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-04-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-05-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-05-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-06-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-06-SUMMARY.md", "AUDIT.md", "Makefile", "README.md", "docs/TUI-REQUIREMENTS.md", "pipeline/artifact_loader.py", "pipeline/flops_counter.py", "pipeline/registry_loader.py", "pipeline/run_finetune.py", "pipeline/run_sweep.py", "schemas/flops_report.json", "script/audit_n_frequencies.py", "script/export_runs.py", "tests/test_artifact_loader.py", "tests/test_flops_counter.py", "tests/test_known_defects.py", "tests/test_registry_loader.py", "tests/test_run_finetune_contracts.py", "tests/test_sweep.py"]
covered_digest: "v3:sha256:24dc141744a9aed0a01e626404b14783889d62ac10ce2662c8812fff20c3105d"
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
**Verified:** 2026-10-15T23:59:53Z
**Status:** passed
**Re-verification:** Yes — stale-fingerprint refresh (fifth stale-fingerprint re-run over this phase). The 2026-10-14T11:28:53Z pass (passed 14/14 at HEAD `075a621`) went stale because three covered files changed since: `Makefile` (261015-pex lint append), `README.md` (docs refresh b89e87c + pex TUI/demo sections), `script/audit_n_frequencies.py` (line-number comment refresh b89e87c). This pass diff-audited that delta in full, re-verified every must-have against the current tree at HEAD `18838c0` (live re-execution of the loader/overlay/import/lint/legacy contracts plus one green run of the six phase-7 suites), reconfirmed the open CR-01 finding's sites unchanged, and recomputed the covered-input fingerprint.

## Re-verification (stale refresh, HEAD 18838c0, 2026-10-15/16)

### Staleness diagnosis (commit-anchored, verified this pass)

`git diff --stat 075a621..HEAD` over the covered set — exactly **3 files**:

- **`Makefile` (+5/-1):** adds the `QUICK_PEX_DEMO` existence-guarded variable (`scripts/demo/record_tui_demo.py`) and appends `$(QUICK_PEX_DEMO)` to the `lint` recipe — the same lint-only idiom as `QUICK_L6H_SCRIPTS`. `PHASE7_MODULES` definition and position byte-untouched; no gate lane gains GPU/dnallm execution (the script is linted, never CI-run).
- **`README.md` (+35/-2):** documentation only — Python/Node lane count badges (389→1743 / 18→26), a ModelScope-first registry/download section, an operator-console (TUI) section, repo-tree and doc-index additions. No pipeline-contract claim weakened; no Phase 7 surface touched.
- **`script/audit_n_frequencies.py` (12 lines):** comment/docstring line-number refresh (`:1418-1425` → `:1494-1503`) pointing at `run_finetune.py`'s `validate_sequences` call and `models_no_char_n` conditional — verified ACCURATE against the current file this pass (`validate_sequences` at `:1502`, the conditional at `:1494-1499`). Behavior unchanged.

**Byte-identical (empty diff) since the prior pass:** `pipeline/flops_counter.py`, `pipeline/registry_loader.py`, `pipeline/artifact_loader.py`, `pipeline/run_finetune.py`, `pipeline/run_sweep.py`, `schemas/flops_report.json`, all six phase-7 test files, `.claude/CLAUDE.md`, `AUDIT.md`, `docs/TUI-REQUIREMENTS.md`, `script/export_runs.py` — the entire FLOPs chain core, the overlay seam, both pipeline drivers, and the whole phase-7 test surface.

**Uncovered since the prior pass (reviewed for spillover, none into Phase 7 surfaces):** the 261015 quick-task series (ehc/c4j/h8i/pex — TUI i18n, launch gates, single-GPU guard, demo recording), the golden-SVG refresh, and the 261016-a4f fail-closed fixes (`f64e764`/`7217ca1` over `pipeline/env_smoke.py`, `tui/screens/env_check.py`, their tests) — all outside the Phase 7 covered set; the a4f fixes address scoped-review findings WR-01..WR-04/IN-01 in env-smoke/TUI files, none of which are Phase 7 artifacts.

### Delta contract analysis vs the Phase 7 must-haves

1. **Four-flag threading (T1-T5) untouched** — `run_sweep.py` byte-identical; the flags, `const=16` bare-EBS, abs-resolution, collect-all pre-validation, and only-when-present manifest discipline all stand (re-grepped + suite green this pass).
2. **FLOPs chain byte-identical** — calibration slot, hook lifetime (`remove_hooks` before the DNATrainer ctor, both branches), WR-13 write ordering, `local_rank == 0` guard, and verbatim hardware capture re-read directly in `run_finetune.py` this pass; contracts tests green.
3. **Registry overlay seam byte-identical** — all load sites still go through `registry_loader`; live byte-identity re-proven at the current registry (59 models / 50 datasets).
4. **No gate-lane GPU/dnallm exposure** — the only Makefile change is a lint-only append; `make -n lint` still expands the three PHASE7 modules.
5. **CR-01 (open critical carried finding) sites unchanged** — `run_finetune.py:1008` `model_row["Model_name"]` and `:1021` `model_row["Mean_token_length"]` re-confirmed present and unguarded; the prior pass's full adjudication (real defect, NOT a Phase 7 must-have breach — every enumerated Truth 11 / SC4 / CUST-05 clause holds; ownership is the Phase 9 custom-registry schema/wizard seam plus pre-Phase-7 consumer indexing, provenance `c6b3137`) carries unchanged. Disposition ledger (`07-REVIEW-DISPOSITION.md`) records it `open`.

### Re-verified verdicts (all 14 truths)

| Must-have | Verdict | Basis this pass |
|---|---|---|
| T1-T5 (four flags: threading, bare-EBS=16, abs-resolution, D-14 pre-validation, only-when-present manifest) | ✓ VERIFIED | `run_sweep.py` byte-identical since prior pass; registration (`:433/:444/:458/:468`, `nargs='?' const=16`), `build_argv` (`:1139`) only-when-present contract, resolution (`:1805/:1809`), and `_validate_subset_file` (`:794`) re-grepped; 302-test run green |
| T6-T9, T13 (FlopsCounter port, dispatch order, always-on calibration, GPU emission, v1 schema) | ✓ VERIFIED | `flops_counter.py` + `schemas/flops_report.json` byte-identical; live torch-free CPU import re-checked; calibration/write spans re-read directly in `run_finetune.py` (`:1537-1562`, `:1643-1690`); GB10 smoke evidence stands (07-06, ratio 0.332, `NVIDIA GB10` verbatim); contracts tests green |
| T10 (tolerant loader) | ✓ VERIFIED | `artifact_loader.py` byte-identical; live 4-case re-check passed this pass (valid→dict; empty/truncated-UTF8/missing→None) |
| T11 (registry overlay: byte-identical-when-absent, collision fail-fast, fail-loud, load sites) | ✓ VERIFIED | `registry_loader.py` byte-identical; live byte-identity re-check (models 59 equal + equal key order, datasets 50 equal + equal key order, 0 official `enabled`); all load sites grep-verified (`run_sweep` :579/:580/:688/:689/:766/:767/:1721/:1868, `run_finetune` :744/:747, audit :622); 24-test suite green. Carries open CR-01 (Warning W4) — every seam clause holds |
| T12 (legacy deleted, zero references) | ✓ VERIFIED | Re-executed this pass: legacy absent on disk; `grep -rn dnallmmark_pipeline pipeline/ script/ tests/ Makefile schemas/` → 0 lines |
| T14 (lint/typecheck/test gates, GPU-free/dnallm-free) | ✓ VERIFIED | `make -n lint` re-proven — the three PHASE7 modules still expand; the only recipe change is the lint-only `QUICK_PEX_DEMO` append; phase-7 suites 302 green this pass; fresh full-suite evidence (minutes old, same tree): 1798 passed at the documented 7F machine baseline, node 26/26, ruff + ty green |

### Spot-checks (executed by this verifier at HEAD 18838c0)

| Command | Result | Status |
|---|---|---|
| `.venv/bin/python -m pytest tests/test_flops_counter.py tests/test_registry_loader.py tests/test_sweep.py tests/test_artifact_loader.py tests/test_run_finetune_contracts.py tests/test_known_defects.py -q` | **302 passed in 0.76s** | ✓ PASS |
| `python -I` torch-free import (`flops_counter`, `registry_loader`, `artifact_loader`) | cpu-import-ok / torch-free-ok | ✓ PASS |
| Live overlay byte-identity (empty `DNALLMMARK_CUSTOM_REGISTRY_DIR`) | models: equal dict AND equal key order (n=59); datasets: equal (n=50); 0 official entries with `enabled` | ✓ PASS |
| Live tolerant-loader 4-case | valid→dict; empty/truncated-UTF8/missing→None | ✓ PASS |
| `make -n lint` PHASE7 expansion | all three phase-7 modules present in the expansion | ✓ PASS |
| Legacy absence + zero references | absent / 0 lines | ✓ PASS |
| Audit-script line refs vs `run_finetune.py` | `validate_sequences` at :1502, `models_no_char_n` conditional at :1494-1499 — refreshed refs accurate | ✓ PASS |
| Debt markers (`TBD\|FIXME\|XXX`) over the 3 changed covered files | 0 hits | ✓ PASS |
| CR-01 hard-index sites | `:1008` / `:1021` unchanged (carried open per disposition ledger) | ✓ CONFIRMED UNCHANGED |

**Fresh full-tree gate evidence (recorded by the orchestrator minutes before this pass, source unchanged since — not re-run per the refresh brief):** full pytest 1798 passed at exactly the pinned 7F baseline (`test_determinism` 1, `test_schemas` 5, `test_services_run_config` 1 — all pre-existing, documented in WINDOWS #22), including the 3 new fail-closed tests from `f64e764`/`7217ca1`; node suite 26/26; ruff + ty green; 9 TUI golden SVGs green unmodified.

**Fresh fingerprint (verbatim from `verification.fingerprint`):** `v3:sha256:24dc141744a9aed0a01e626404b14783889d62ac10ce2662c8812fff20c3105d` over the same covered set as the prior pass (frontmatter `covered_files` is the command's verbatim output).

---

## Goal Achievement

### Observable Truths

Must-haves carried forward verbatim from the prior pass (the 14-truth contract derived from ROADMAP SC1-SC5 plus the six PLANs' must_haves; unchanged because the plans did not change).

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `run_sweep.py` accepts `--subset_file`, `--effective_batch_size`, `--num_train_epochs`, `--cache_dir` (underscore-only) and threads each as separate LIST elements in child argv only when present; byte-identical when absent (SC1 / PIPE-02 / D-11/D-13) | ✓ VERIFIED | File byte-identical since prior verified pass; registrations re-grepped (:433/:444/:458/:468, underscore-only); suite green (302 passed) |
| 2 | Bare `--effective_batch_size` yields 16; valued yields int; absent contributes zero argv elements so child YAML GA governs (D-12) | ✓ VERIFIED | `nargs='?' const=16 type=int default=None` re-read this pass; tests green |
| 3 | `--subset_file` / `--cache_dir` resolved to absolute paths at sweep layer before threading (D-15); GA arithmetic stays child-side, integer-only pass-through (D-10/D-16) | ✓ VERIFIED | Resolution sites (:1805/:1809) re-grepped; `build_argv` docstring + body confirm no GA arithmetic; tests green |
| 4 | `--subset_file` pre-validated collect-all at sweep start (every problem listed, before any cell enumerates) (D-14) | ✓ VERIFIED | `_validate_subset_file` (:794) + collect-all zone (:1862-1868) intact; tests green |
| 5 | Manifest cells record flag fields ONLY when present; run_record.json field set untouched (D-13 / D-02 spirit) | ✓ VERIFIED | `sweep_flags` only-when-present discipline (:1735, :1825-1826, `_manifest_payload` :1390) intact; tests green |
| 6 | FlopsCounter's 20+ architecture dispatch ported with formulas verbatim, CPU-importable and stub-testable with no torch at module top, no GPU, no dnallm (SC2 / PIPE-01) | ✓ VERIFIED | `flops_counter.py` byte-identical; live re-check: import succeeds CPU-side with `'torch' not in sys.modules`; 49 stub tests green |
| 7 | Dispatch order preserved: a Linear inside a borzoi-path model takes the Linear hook, not the borzoi branch | ✓ VERIFIED | File byte-unchanged; `test_linear_wins_over_borzoi_branch` green in this verifier's run |
| 8 | Every run_finetune execution calibrates FLOPs always-on (no flag), hooks removed BEFORE the DNATrainer ctor, single post-success flops_report.json write ordered final_metrics → flops_report → trainer_state marker inside the local_rank==0 guard, hardware captured verbatim (D-01/D-02/D-05, WR-13) | ✓ VERIFIED | Calibration block (:1537-1562) and write block (:1643-1690) re-read directly this pass — always-on, `remove_hooks` in both branches before the trainer, final_metrics → `save_to_json` → `shutil.copy` marker ordering, `local_rank == 0` guard, `torch.cuda.get_device_name()` verbatim; contract tests green |
| 9 | A real bounded GPU run emits flops_report.json: schema_version 1, attention + Linear hook keys, uncovered within threshold, hardware populated with the real device string, magnitude ratio in [0.05, 1.0] (SC2 runtime / D-22/D-23) | ✓ VERIFIED | GB10 smoke evidence stands (07-06-SUMMARY: ratio 0.3316, `gpu_device "NVIDIA GB10"` verbatim, uncovered_layers empty, Draft202012-valid); FLOPs chain core byte-identical since the smoke and the run_finetune delta since is disjoint from the emission spans; see Warning W2 on evidence recency |
| 10 | Tolerant loader contract: `load_json_artifact` returns parsed doc for valid files, None for missing/unreadable/truncated/empty; valid-but-key-missing returned, not rejected (SC3 / PIPE-03 / D-17/D-18/D-19) | ✓ VERIFIED | `artifact_loader.py` byte-identical; live 4-case re-check this pass — missing/empty/truncated-UTF8 → None, valid → parsed dict; 9 tests green |
| 11 | Registry overlay seam: custom entries merge over official registries, collision fails fast naming key + BOTH paths, malformed custom fails loud, byte-identical when absent, official files never written, all load sites rewired (SC4 / CUST-05 / D-06/D-07/D-08) | ✓ VERIFIED | `registry_loader.py` byte-identical; live byte-identity at the current 59/50 registry (equal dicts, equal key order, 0 official `enabled`); all load sites grep-verified this pass; 24-test suite green. Open finding CR-01 lives in the consumer/schema interplay OUTSIDE these clauses — see Warning W4 |
| 12 | Legacy file deleted with zero live-code references; five parity expectations re-pinned as sha-documented verbatim literals; archives untouched (D-04) | ✓ VERIFIED | Re-executed this pass: legacy absent; grep over `pipeline/ script/ tests/ Makefile schemas/` → 0 lines; contract tests green |
| 13 | flops_report.json v1 schema published, strictly additive over legacy writer keys, schema_version const 1, optional hardware (D-27/D-02/D-03/D-05) | ✓ VERIFIED | `schemas/flops_report.json` byte-identical; round-trip test green in this verifier's run |
| 14 | `make lint` + `make typecheck` cover the changed files; full test lane green; zero GPU/dnallm in any gate (SC5) | ✓ VERIFIED | `make -n lint` re-proven (three-file PHASE7 expansion intact; only the lint-only `QUICK_PEX_DEMO` append added since); typecheck recipe byte-unchanged CPU-side; phase-7 suites 302 green this pass; full-suite failures are the documented 7F machine baseline, none in phase-7 files |

**Score:** 14/14 truths verified (0 present, behavior-unverified)

### Advisory (New Scope, Unevidenced)

Re-verification ran (stale-fingerprint route); this section is recorded per the #3304 evidence-gate contract.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | None — no new-scope Step 7 finding arose this pass; the covered-set delta is lint-append + docs + comment refresh, all audited above. The one open critical item (CR-01) is a carried review finding, not a new-scope discovery, and is reported at full prominence as Warning W4. | — | — |

### Required Artifacts

`gsd-tools verify artifacts` treats these plans' plain string artifact lists as `total: 0` — artifact status is from direct inspection, same as prior passes.

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pipeline/flops_counter.py` | FlopsCounter port: lazy torch seams, 20+ dispatch, uncovered accounting, save_to_json + v1 additions, count_split_tokens, build_hardware_section, calibration_forward | ✓ VERIFIED | Byte-identical since prior pass; live torch-free import re-checked; imported by run_finetune (:58-61) — WIRED |
| `pipeline/artifact_loader.py` | Tolerant load_json_artifact (D-17/D-18/D-19) | ✓ VERIFIED | Byte-identical; live 4-case contract re-check passed |
| `pipeline/registry_loader.py` | Overlay seam: custom_registry_dir, load_models_registry, load_datasets_registry | ✓ VERIFIED | Byte-identical; live byte-identity re-proven at n=59/50; wired at every registry load site (grep-verified) |
| `schemas/flops_report.json` | v1 strict contract (D-27) | ✓ VERIFIED | Byte-identical; round-trip test green |
| `tests/test_flops_counter.py` | Stub-nn harness, per-family arithmetic, schema pins, dispatch order, calibration chain | ✓ VERIFIED | Byte-identical; green |
| `tests/test_artifact_loader.py` | Tolerant-read contract cases | ✓ VERIFIED | Byte-identical; green |
| `tests/test_registry_loader.py` | Overlay merge/collision/malformed/resolution/byte-identity + run_finetune source-contract | ✓ VERIFIED | Byte-identical; green |
| `tests/test_sweep.py` | argv parity, pre-validation, manifest-field, byte-identity extensions | ✓ VERIFIED | Byte-identical since prior pass; green |
| `tests/test_run_finetune_contracts.py` | Calibration-slot / write-ordering / rank-guard contracts + re-pinned parity literals | ✓ VERIFIED | Byte-identical since prior pass; green |
| `Makefile` | Gate lanes: PHASE7_MODULES lint expansion, test lanes | ✓ VERIFIED | Delta-audited: PHASE7_MODULES definition + inclusion byte-unchanged; only the lint-only `$(QUICK_PEX_DEMO)` append |
| `README.md` | Project documentation | ✓ VERIFIED | Delta-audited: documentation additions only (badges, ModelScope/registry section, TUI section); no pipeline-claim changes |
| `script/audit_n_frequencies.py` | N-frequency audit wired through registry_loader | ✓ VERIFIED | Delta-audited: line-number comment refresh only, verified accurate against current run_finetune.py; registry load still via `_REGISTRY_LOADER` (:98-100, :622) |
| `pipeline/dnallmmark_pipeline.py` | DELETED (D-04) | ✓ VERIFIED (absence) | Re-checked this pass: not on disk, zero live references |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| run_finetune calibration slot | flops_counter.FlopsCounter / build_hardware_section / calibration_forward / count_split_tokens | sibling import (:58-61) + calibration block (:1537-1562) | ✓ WIRED | Re-read directly this pass; contract tests green |
| run_finetune / run_sweep / audit registry loads | registry_loader | module import / importlib | ✓ WIRED | All load sites grep-verified this pass (`run_sweep` :579/:580/:688/:689/:766/:767/:1721/:1868, `run_finetune` :744/:747, audit :622); 24-test suite green |
| FlopsCounter.save_to_json output | schemas/flops_report.json | round-trip test with Draft202012Validator | ✓ WIRED | Round-trip test green; schema byte-unchanged |
| sweep argv | run_finetune child flags | four sanctioned flags | ✓ WIRED | Four-flag block byte-unchanged; suite green |
| Makefile lint | PHASE7_MODULES | wildcard existence guard | ✓ WIRED | Definition byte-unchanged; `make -n lint` expansion re-proven |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| flops_report.json (written) | report dict | FlopsCounter accumulators from real forward hooks | ✓ | Real GB10 report evidence stands (chain byte-unchanged; delta disjoint) |
| manifest flag fields | sweep_flags | argparse / directories.json → main() resolution → _manifest_payload | ✓ | run_sweep byte-unchanged; tests green |
| registry merged dict | registry | official JSON file + optional custom JSON file | ✓ | Live byte-identity re-check passed this pass (59/50) |

### Behavioral Spot-Checks

All executed by this verifier at HEAD `18838c0` (see the re-verification section's spot-check table). Full-suite and node/lint/typecheck evidence comes from the orchestrator's fresh run minutes before this pass on the identical tree (not re-run per the refresh brief).

### Probe Execution

Not applicable — phase declares no `scripts/*/tests/probe-*.sh` probes; the runtime proof is plan 07-06's GB10 smoke whose evidence stands with the FLOPs chain byte-unchanged since.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PIPE-01 | 07-01, 07-04, 07-05, 07-06 | FlopsCounter 20+ architecture port into run_finetune.py | ✓ SATISFIED | Truths 6-9, 12, 13 — FLOPs chain byte-unchanged; 302 tests green |
| PIPE-02 | 07-03, 07-06 | run_sweep argv passthrough of the four flags | ✓ SATISFIED | Truths 1-5 — four-flag threading intact; suite green |
| PIPE-03 | 07-01 | Tolerant loader JSON contract shared with the future monitor | ✓ SATISFIED | Truth 10 — live 4-case re-check passed |
| CUST-05 | 07-02 | Registry overlay: collision fail-fast, byte-identical when absent, existing tests zero-modification | ✓ SATISFIED | Truth 11 — byte-identity live-proven at 59/50; 24-test suite green; every enumerated clause holds (CR-01 assessed outside these clauses — W4) |

Orphan check: REQUIREMENTS.md maps exactly 4 IDs to Phase 7 (CUST-05, PIPE-01, PIPE-02, PIPE-03), all marked Complete; all four are claimed by plans and satisfied. No orphans.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| tests/test_sweep.py | PIPE-02 | all | 0 | no | Value (argv-shape literals, byte-identity) | OK |
| tests/test_flops_counter.py | PIPE-01 | all | 0 | no | Value (per-family arithmetic, schema pins, dispatch order) | OK |
| tests/test_registry_loader.py | CUST-05 | all | 0 | no | Value (collision message, merge equality) | OK |
| tests/test_artifact_loader.py | PIPE-03 | all | 0 | no | Value (4-case returns) | OK |
| tests/test_run_finetune_contracts.py | PIPE-01 | all | 0 | no | Value (source-order contracts, parity literals with source-commit provenance) | OK |

Skip-marker scan (`pytest.mark.skip` / `unittest.skip` / `xfail`) over all six files: 0 hits. No disabled tests on requirements; no circular expected-value generation (parity literals are transcribed from git history with sha-documented provenance, the D-04 discipline).

### Decision Coverage

`check.decision-coverage-verify`: 27/27 trackable CONTEXT.md decisions honored by shipped artifacts; 0 not honored. (Non-blocking gate — recorded per #2492.)

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | Zero TBD/FIXME/XXX and zero TODO/HACK/PLACEHOLDER markers across the 3 changed covered files (re-scanned this pass); the byte-identical 16 stand clean from prior scans | - | - |

### Human Verification Required

N/A — Infrastructure/foundation phase (pipeline tooling, no user-facing elements). All acceptance criteria verified programmatically: six phase-7 suites green (302 passed), live behavioral contracts re-run (torch-free import, overlay byte-identity, tolerant-loader 4-case, lint expansion, legacy absence), the covered-set delta audited in full against the 14-truth contract, and fresh full-tree gate evidence (1798 passed / node 26/26 / ruff+ty green) recorded on the identical tree minutes before this pass. No ⚠️ PRESENT_BEHAVIOR_UNVERIFIED truths, no abstained non-inferable truths.

### Warnings (open items — none blocking a must-have)

| # | Finding | Severity | Impact |
|---|---------|----------|--------|
| W1 | ROADMAP SC4 / CUST-05's consumer list names **export** among the overlay consumers, but `script/export_runs.py` was deliberately NOT rewired (locked decision D-09 scope; verified it loads no registries at runtime — custom entries flow into exports through run records). File byte-identical since the prior pass. Documented-by-decision deviation, non-blocking. | ⚠️ Warning | Remains a documented-by-decision deviation |
| W2 | GPU emission evidence (Truth 9) predates Phases 8-12 and the 261015/261016 series; the FLOPs chain core is byte-identical since the smoke and this pass's audit shows every covered delta disjoint from the calibration/write spans — but strictly, the exact current tree state has not itself been GPU-run. | ℹ️ Info | Acceptable: a future bounded smoke under E2' will re-prove the tree |
| W3 | Review-disposition state updated this pass (`07-REVIEW-DISPOSITION.md`, open 8→3): the scoped incremental review of the only post-review source delta (16e21b5, `pipeline/env_smoke.py` — outside Phase 7's covered set) landed its five findings as FIXED — WR-01/WR-02 in `f64e764`, WR-03/WR-04/IN-01 in `7217ca1`, with 3 new fail-closed tests in the green full-suite run. The three remaining `open` rows are carried rows from the superseded full review: CR-01 (W4 below), IN-02 (duplicated `gpu_memory_override` assignment, pre-existing), IN-03 (pre-existing registry data inconsistencies). The prior pass's W3 items (stale repo-IDs, empty-string flag handling, stale schema `$comment`) are subsumed: the repo-ID/schema-comment items were fixed by intervening quick tasks and the ledger's live rows; the 261014 directory-flag empty-string concern is superseded by the scoped review's disposition. | ⚠️ Warning | Open carried rows await maintainer triage; none falsifies a Phase 7 must-have |
| W4 | **CR-01 (critical, disposition open — unchanged since the prior pass).** A minimal custom model entry carrying exactly the schema-required subset (`Model_path`, `size (M)`, `type`, `Tokenizer` per `schemas/custom_registry.json`) is schema-VALID, merges cleanly through the Phase 7 `registry_loader` seam, and then crashes the pipeline consumer: `run_finetune.py:1008` `model_row["Model_name"]` and `:1021` `model_row["Mean_token_length"]` are unguarded hard indexes (dataset-side siblings likewise) — both sites re-confirmed unchanged this pass (file byte-identical since the prior pass, which deterministically reproduced the `KeyError`s). **Why this is NOT a Phase 7 must-have breach:** every enumerated Truth 11 / SC4 / CUST-05 clause (merge, collision fail-fast naming key + both paths, malformed-JSON fail-loud, byte-identical-when-absent, official-files-never-written, load sites) was live-verified this pass and holds — the crash requires an entry that is *well-formed* JSON; the fail-loud clause covers malformed files only. The defect is a field-completeness mismatch between the **Phase 9** custom-registry schema/wizard contract and `run_finetune.py`'s hard indexing (provenance `c6b3137`, pre-Phase-7; not a regression). Fix belongs at the Phase 9 schema/wizard seam (or defense-in-depth in `registry_loader._load_registry`). Recommend fixing before the TUI wizard is used in anger; tracked `open` in `07-REVIEW-DISPOSITION.md`. | ⚠️ Warning (open critical review finding) | Does not block Phase 7's passed verdict; blocks real-world custom-entry usage until triaged |

### Re-Verification Record

- **Route:** stale fingerprint (fifth stale-fingerprint re-run over this phase; prior pass `passed` 14/14 at 2026-10-14T11:28:53Z / HEAD `075a621`).
- **Staleness diagnosis confirmed:** `git diff --stat 075a621..HEAD` over the covered set → exactly 3 files (Makefile lint append; README docs; audit-script comment line-number refresh); 16 covered files byte-identical including the whole FLOPs chain core, the overlay seam, both pipeline drivers, and all six test files.
- **Delta contract analysis:** every hunk audited against the 14-truth contract — four-flag threading, GA pass-through, manifest discipline, calibration/write spans, PHASE7 gate expansion all intact; no gate lane gains GPU/dnallm exposure.
- **Regression check:** all 14 truths verified against the current tree (live re-execution for the loader/overlay/legacy/gate/import contracts; direct source re-read of the calibration and write-ordering spans; green 302-test run). Zero regressions.
- **Review gate:** satisfied — scoped incremental review committed (`07-REVIEW.md`), five findings fixed in `f64e764`/`7217ca1` (all in env-smoke/TUI files outside the Phase 7 covered set), disposition ledger records them `fixed` with 3 carried-open rows (`07-REVIEW-DISPOSITION.md`).
- **Fingerprint recomputed** over the current tree via `verification.fingerprint`; `covered_digest` in the frontmatter is the command's verbatim output (`v3:sha256:24dc1417...c3105d`).

### Gaps Summary

No gaps. The stale fingerprint was diagnosed (Makefile lint append + README docs + audit-script comment refresh since `075a621`), the delta hunk-audited against every Phase 7 assertion (all intact), all 14 must-have truths verified against the current tree at HEAD `18838c0`, the six phase-7 suites re-run green (302 passed), live overlay/tolerant-loader/torch-free-import/lint/legacy contracts re-executed, all 4 requirement IDs satisfied with no orphans, 27/27 decisions honored, zero debt markers on changed files, fresh full-tree gate evidence (1798 passed / node 26/26 / ruff + ty green at the documented baseline) recorded on the identical tree, and the covered-input fingerprint regenerated. The open critical review finding CR-01 is unchanged (sites byte-identical), previously reproduced, and adjudicated: owned by the Phase 9 custom-registry schema/wizard seam plus pre-Phase-7 consumer indexing — no Phase 7 clause breaches; carried as Warning W4 for maintainer triage alongside carried info rows IN-02/IN-03.

---

_Verified: 2026-10-15T23:59:53Z (stale refresh at HEAD 18838c0; prior pass 2026-10-14T11:28:53Z at HEAD 075a621)_
_Verifier: Claude (gsd-verifier)_
