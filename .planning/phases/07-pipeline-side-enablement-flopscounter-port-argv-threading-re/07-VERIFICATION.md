---
phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
verified: 2026-10-14T00:00:00Z
status: passed
score: 14/14 must-haves verified
covered_files: [".claude/CLAUDE.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-01-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-01-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-02-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-02-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-03-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-03-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-04-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-04-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-05-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-05-SUMMARY.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-06-PLAN.md", ".planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-06-SUMMARY.md", "AUDIT.md", "Makefile", "README.md", "docs/TUI-REQUIREMENTS.md", "pipeline/artifact_loader.py", "pipeline/flops_counter.py", "pipeline/registry_loader.py", "pipeline/run_finetune.py", "pipeline/run_sweep.py", "schemas/flops_report.json", "script/audit_n_frequencies.py", "script/export_runs.py", "tests/test_artifact_loader.py", "tests/test_flops_counter.py", "tests/test_known_defects.py", "tests/test_registry_loader.py", "tests/test_run_finetune_contracts.py", "tests/test_sweep.py"]
covered_digest: "v3:sha256:bf92f37cbab2cfa4f473d0d899ae30834047866ae4f3a7a54f04c4458f8c8468"
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
**Verified:** 2026-10-14
**Status:** passed
**Re-verification:** Yes — #4682 stale-fingerprint route (fifth pass over this phase). The 2026-10-13 pass (passed 14/14 at HEAD `8b92766`) went stale because Phase 12's close-out touched two covered files: `Makefile` (+28/-4, phase-12 lint-lane + snapshot-update target additions) and `README.md` (+4/-1, multi-gpu doc link) — the ONLY covered-file changes since; all pipeline code byte-identical. This pass verified the delta against Phase 7's gate/Makefile contracts, re-ran the six phase-7 test suites, re-checked the live overlay/tolerant-loader contracts, and recomputed the covered-input fingerprint.

## Re-verification (stale refresh, HEAD def16a5, 2026-10-14)

### Staleness diagnosis (commit-anchored, verified this pass)

Anchor: the commit lineage of the 2026-10-13 passed verification (tree at HEAD `8b92766`). `git diff --stat 8b92766..HEAD` over the covered set:

- **`Makefile`** — +28/-4. Hunk-audited in full below; every hunk is Phase 12's sanctioned scope (12-01 `PHASE12_MODULES` existence-guard lint expansion, 12-03 `snapshot-update` maintainer-only golden-regeneration target + `.PHONY` line, comment updates). Zero changes to the PHASE7_MODULES definition, its wildcard-existence idiom, or its position in the lint recipe.
- **`README.md`** — +4/-1. One prose change: adds a `docs/multi-gpu.md` link sentence to the existing docs-links paragraph. Zero changes to any pipeline/sweep/registry documentation claims verified in prior passes.
- **All 17 other covered implementation files + `AUDIT.md` + `.claude/CLAUDE.md` + `docs/TUI-REQUIREMENTS.md`:** empty diff — byte-identical (`flops_counter.py`, `registry_loader.py`, `artifact_loader.py`, `run_finetune.py`, `run_sweep.py`, `schemas/flops_report.json`, all six test files, both script files).
- Working-tree check: `git diff -- Makefile README.md` is empty — no uncommitted changes to either file (the working tree's only uncommitted content is untracked helixgen/multi-species WIP data, outside the covered set and outside phase-7 scope).

### Delta contract analysis vs the Phase 7 must-haves

Hunk-audited read of the full delta against Truth 14 (SC5 gate contract) and the whole 14-truth contract:

1. **`PHASE7_MODULES` untouched and still wired.** Line 161 (`Makefile`) is byte-identical to the prior pass: `PHASE7_MODULES := $(foreach s,pipeline/flops_counter.py pipeline/registry_loader.py pipeline/artifact_loader.py,$(if $(wildcard $(s)),$(s)))`. The lint recipe (line 176) still expands `$(PHASE7_MODULES)`; the delta only APPENDS `$(PHASE12_MODULES)` after `$(PHASE8_TUI)`, following the established existence-guard idiom. Dry-run verified this pass: `make -n lint` expands the literal three-file sequence `pipeline/flops_counter.py pipeline/registry_loader.py pipeline/artifact_loader.py` (PHASE7-EXPANSION-OK).
2. **`snapshot-update` target is additive and CI-inert.** New maintainer-only target running the golden regeneration through `uv run --group dev --group tui python tests/tui/test_snapshots.py --regenerate`; a comment block explicitly pins it as NEVER a CI lane. It touches no existing lane (`test`, `test-fast`, `ci`, `lint`, `typecheck` recipes byte-unchanged — only the lint line gains the appended `$(PHASE12_MODULES)` token).
3. **README delta is documentation-only.** The added sentence links `docs/multi-gpu.md` (Phase 12's D-04 decision record). No README content verified by prior passes (pipeline CLI documentation, FLOPs reference of record) is modified.
4. **No gate-lane GPU/dnallm exposure introduced.** The appended PHASE12_MODULES list is `pipeline/run_sweep_shard.py` + `script/gen_progress.py` (both stdlib/CPU-side per Phase 12's own verification); the ruff lane remains `--group dev`; no covered gate gains a GPU or dnallm dependency.

### Re-verified verdicts (all 14 truths)

| Must-have | Verdict | Basis this pass |
|---|---|---|
| T1-T5 (four flags: threading, bare-EBS=16, abs-resolution, D-14 pre-validation, only-when-present manifest) | ✓ VERIFIED | `pipeline/run_sweep.py` + `tests/test_sweep.py` byte-identical since the passed pass (empty git diff this round); suite green in this verifier's run |
| T6-T9, T13 (FlopsCounter port, dispatch order, always-on calibration, GPU emission, v1 schema) | ✓ VERIFIED | FLOPs chain (`flops_counter.py`, `run_finetune.py`, `schemas/flops_report.json`) byte-identical (empty diff); live torch-free CPU import re-checked this pass; suite green |
| T10 (tolerant loader) | ✓ VERIFIED | `artifact_loader.py` byte-identical; live 4-case contract re-check passed this pass |
| T11 (registry overlay: byte-identical-when-absent, collision fail-fast, fail-loud, five load sites) | ✓ VERIFIED | `registry_loader.py` byte-identical (zero commits since the 2026-10-12 pass); live byte-identity re-check passed this pass (62 keys, equal order, 0 official `enabled` fields); 24-test suite green |
| T12 (legacy deleted, zero references, parity literals) | ✓ VERIFIED | Re-checked: `pipeline/dnallmmark_pipeline.py` absent; `grep -rn dnallmmark_pipeline pipeline/ script/ tests/ Makefile schemas/` → 0 lines |
| T14 (lint/typecheck/test gates, GPU-free/dnallm-free) | ✓ VERIFIED | Delta fully hunk-audited: PHASE7_MODULES definition and lint-recipe inclusion byte-unchanged; `make -n lint` expansion re-proven; phase-7 suites re-run green; no gate lane touched by the delta |

### Spot-checks (executed by this verifier at HEAD def16a5)

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_flops_counter.py tests/test_registry_loader.py tests/test_sweep.py tests/test_artifact_loader.py tests/test_run_finetune_contracts.py tests/test_known_defects.py -q` | **276 passed, 2 skipped in 1.38s** (skips = the two conditional root-user permission-bit guards — environmental, not taken on this host) |
| `git diff 8b92766..HEAD` over the other 17 covered impl files + 3 covered docs | empty (byte-identical) |
| Live overlay byte-identity (empty `DNALLMMARK_CUSTOM_REGISTRY_DIR`) | equal dict AND equal key order (n=62); 0 official entries with `enabled` |
| Live tolerant-loader 4-case | valid→dict; empty/truncated-UTF8/missing→None |
| `make -n lint` PHASE7 expansion | `pipeline/flops_counter.py pipeline/registry_loader.py pipeline/artifact_loader.py` present (PHASE7-EXPANSION-OK) |
| Legacy absence + zero references | absent / 0 lines |
| Debt markers (`TBD\|FIXME\|XXX`) over `Makefile` + `README.md` | 0 hits |

**Advisory (new-scope, unevidenced):** none — the only covered-file delta was hunk-audited in full, is the sanctioned Phase 12 scope (TEST-01 snapshot lane + 12-01 lint expansion), and introduces no new-scope concern against Phase 7 contracts.

**Fresh fingerprint (verbatim from `verification.fingerprint`):** `v3:sha256:bf92f37cbab2cfa4f473d0d899ae30834047866ae4f3a7a54f04c4458f8c8468` over the same 19 implementation files + 4 docs + auto-added PLAN/SUMMARY set (frontmatter `covered_files` is the command's verbatim output).

**Verdict: PASSED — 14/14 must-haves hold at HEAD def16a5.** Zero regressions; the staleness was exactly the sanctioned Phase 12 Makefile/README delta, and the Phase 7 contracts (four flags, argv parity, byte-identical-when-absent overlay, tolerant loader, FLOPs chain, gate lanes) all verified against the current tree.

---

## Goal Achievement

### Observable Truths

Must-haves carried forward verbatim from the prior pass (re-verification reuses Step 0 must-haves — same 14-truth contract). Truths 10, 11, 12, 14 received live re-execution this pass; the rest quick-regression checked (covered files byte-unchanged since the passed pass + suites green in this verifier's run).

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `run_sweep.py` accepts `--subset_file`, `--effective_batch_size`, `--num_train_epochs`, `--cache_dir` (underscore-only) and threads each as separate LIST elements in child argv only when present; byte-identical when absent (SC1 / PIPE-02 / D-11/D-13) | ✓ VERIFIED | `pipeline/run_sweep.py` + `tests/test_sweep.py` byte-identical since the passed pass (empty git diff 8b92766..HEAD); suite green in this verifier's 276-test run |
| 2 | Bare `--effective_batch_size` yields 16; valued yields int; absent contributes zero argv elements so child YAML GA governs (D-12) | ✓ VERIFIED | File byte-unchanged; tests green in this verifier's run |
| 3 | `--subset_file` / `--cache_dir` resolved to absolute paths at sweep layer before threading (D-15); GA arithmetic stays child-side, integer-only pass-through (D-10/D-16) | ✓ VERIFIED | File byte-unchanged; tests green |
| 4 | `--subset_file` pre-validated collect-all at sweep start (every problem listed, before any cell enumerates) (D-14) | ✓ VERIFIED | File byte-unchanged; tests green |
| 5 | Manifest cells record flag fields ONLY when present; run_record.json field set untouched (D-13 / D-02 spirit) | ✓ VERIFIED | File byte-unchanged; tests green |
| 6 | FlopsCounter's 20+ architecture dispatch ported with formulas verbatim, CPU-importable and stub-testable with no torch at module top, no GPU, no dnallm (SC2 / PIPE-01) | ✓ VERIFIED | `pipeline/flops_counter.py` byte-unchanged; live re-check this pass: `import flops_counter` succeeds CPU-side with `'torch' not in sys.modules` (cpu-import-ok / torch-free-ok); 49 stub tests green |
| 7 | Dispatch order preserved: a Linear inside a borzoi-path model takes the Linear hook, not the borzoi branch | ✓ VERIFIED | File byte-unchanged; `test_linear_wins_over_borzoi_branch` green in this verifier's run |
| 8 | Every run_finetune execution calibrates FLOPs always-on (no flag), hooks removed BEFORE the DNATrainer ctor, single post-success flops_report.json write ordered final_metrics → flops_report → trainer_state marker inside the local_rank==0 guard, hardware captured verbatim (D-01/D-02/D-05, WR-13) | ✓ VERIFIED | `pipeline/run_finetune.py` byte-unchanged; contract tests green in this verifier's run |
| 9 | A real bounded GPU run emits flops_report.json: schema_version 1, attention + Linear hook keys, uncovered within threshold, hardware populated with the real device string, magnitude ratio in [0.05, 1.0] (SC2 runtime / D-22/D-23) | ✓ VERIFIED | GB10 smoke evidence stands (07-06; artifacts re-examined at prior passes); FLOPs chain byte-unchanged since — this pass's git audit over the covered set shows zero commits to `flops_counter.py`/`run_finetune.py`/`schemas/flops_report.json`; see Warning W2 on evidence recency |
| 10 | Tolerant loader contract: `load_json_artifact` returns parsed doc for valid files, None for missing/unreadable/truncated/empty; valid-but-key-missing returned, not rejected (SC3 / PIPE-03 / D-17/D-18/D-19) | ✓ VERIFIED | `pipeline/artifact_loader.py` byte-unchanged; live 4-case re-check this pass — missing/empty/truncated-UTF8 → None, valid → parsed dict returned; 9 tests green |
| 11 | Registry overlay seam: custom entries merge over official registries, collision fails fast naming key + BOTH paths, malformed custom fails loud, byte-identical when absent, official files never written, all five load sites rewired (SC4 / CUST-05 / D-06/D-07/D-08) | ✓ VERIFIED | `pipeline/registry_loader.py` byte-unchanged since the 2026-10-12 pass; live byte-identity re-check this pass (empty overlay → `load_models_registry("pipeline")` equals official with identical key order, n=62; 0 official entries carry `enabled`); 24-test suite green (2 root-guard skips environmental) |
| 12 | Legacy file deleted with zero live-code references; five parity expectations re-pinned as sha-documented verbatim literals; archives untouched (D-04) | ✓ VERIFIED | Re-executed this pass: `test ! -e pipeline/dnallmmark_pipeline.py` → absent; grep over `pipeline/ script/ tests/ Makefile schemas/` → 0 lines; contract tests green |
| 13 | flops_report.json v1 schema published, strictly additive over legacy writer keys, schema_version const 1, optional hardware (D-27/D-02/D-03/D-05) | ✓ VERIFIED | `schemas/flops_report.json` byte-unchanged; round-trip test green in this verifier's run |
| 14 | `make lint` + `make typecheck` cover the changed files; full test lane green; zero GPU/dnallm in any gate (SC5) | ✓ VERIFIED | **Delta-focused re-verification:** `PHASE7_MODULES` definition byte-unchanged (Makefile:161); lint recipe still expands it — `make -n lint` re-proven this pass (PHASE7-EXPANSION-OK); the delta only appends `$(PHASE12_MODULES)` (CPU-side modules per Phase 12's own verification) and an inert maintainer-only `snapshot-update` target; phase-7 suites re-run green (276 passed); no gate lane gains GPU/dnallm exposure |

**Score:** 14/14 truths verified (0 present, behavior-unverified)

### Advisory (New Scope, Unevidenced)

Re-verification ran (stale-fingerprint route); this section is recorded per the #3304 evidence-gate contract.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | None — no new-scope findings. The only covered-file delta (`Makefile` +28/-4, `README.md` +4/-1) was hunk-audited in full: Phase 12's sanctioned lint-lane expansion and doc link; the PHASE7 gate contract was re-proven by dry-run expansion and the green 276-test phase-7 run. | — | — |

### Required Artifacts

All Phase 7 artifacts byte-unchanged since the prior pass except `Makefile` (Phase 12's +28/-4 lint-lane/snapshot additions — delta-audited above) and `README.md` (+4/-1 doc link — documentation-only). `gsd-tools verify artifacts` returns `total: 0` for these plans (plain string lists, not `{path, provides}` objects) — artifact status below is from direct inspection, same as prior passes.

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pipeline/flops_counter.py` | FlopsCounter port: lazy torch seams, 20+ dispatch, uncovered accounting, save_to_json + v1 additions, count_split_tokens, build_hardware_section, calibration_forward | ✓ VERIFIED | Byte-unchanged since prior pass; live torch-free import re-checked; imported by run_finetune — WIRED |
| `pipeline/artifact_loader.py` | Tolerant load_json_artifact (D-17/D-18/D-19) | ✓ VERIFIED | Byte-unchanged; live 4-case contract re-check passed |
| `pipeline/registry_loader.py` | Overlay seam: custom_registry_dir, load_models_registry, load_datasets_registry (D-09 enabled-skip, CR-01 UnicodeDecodeError) | ✓ VERIFIED | Byte-unchanged; live byte-identity re-proven; wired at all five load sites |
| `schemas/flops_report.json` | v1 strict contract (D-27) | ✓ VERIFIED | Byte-unchanged; round-trip test green |
| `tests/test_flops_counter.py` | Stub-nn harness, per-family arithmetic, schema pins, dispatch order, calibration chain | ✓ VERIFIED | Byte-unchanged; green |
| `tests/test_artifact_loader.py` | Tolerant-read contract cases | ✓ VERIFIED | Byte-unchanged; green |
| `tests/test_registry_loader.py` | Overlay merge/collision/malformed/resolution/byte-identity + run_finetune source-contract | ✓ VERIFIED | Byte-unchanged; 24 tests green (2 environmental root-guard skips) |
| `tests/test_sweep.py` | argv parity, pre-validation, manifest-field, byte-identity extensions | ✓ VERIFIED | Byte-unchanged; green |
| `tests/test_run_finetune_contracts.py` | Calibration-slot / write-ordering / rank-guard contracts + re-pinned parity literals | ✓ VERIFIED | Byte-unchanged; green |
| `Makefile` | Gate lanes: PHASE7_MODULES lint expansion, test lanes | ✓ VERIFIED | Delta-audited: PHASE7_MODULES definition + lint inclusion byte-unchanged; `make -n lint` re-proven; only Phase 12 appends added |
| `README.md` | Project documentation | ✓ VERIFIED | Delta-audited: documentation-only multi-gpu link addition; no pipeline-claim changes |
| `pipeline/dnallmmark_pipeline.py` | DELETED (D-04) | ✓ VERIFIED (absence) | Re-checked this pass: not on disk, zero live references |

### Key Link Verification

Wiring re-confirmed this pass via byte-identity of the wired files (empty git diff over the full covered implementation set) plus the green suites.

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| run_finetune calibration slot | flops_counter.FlopsCounter / build_hardware_section | sibling import | ✓ WIRED | `run_finetune.py` byte-unchanged; contract tests green |
| run_finetune / run_sweep / audit registry loads | registry_loader | module import / importlib | ✓ WIRED | `registry_loader.py` byte-unchanged; 24-test suite green |
| FlopsCounter.save_to_json output | schemas/flops_report.json | round-trip test with Draft202012Validator | ✓ WIRED | Round-trip test green; schema byte-unchanged |
| sweep argv | run_finetune child flags | four sanctioned flags | ✓ WIRED | `run_sweep.py` byte-unchanged; suite green |
| Makefile lint | PHASE7_MODULES | wildcard existence guard | ✓ WIRED | Definition byte-unchanged; `make -n lint` expansion re-proven this pass |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| flops_report.json (written) | report dict | FlopsCounter accumulators from real forward hooks | ✓ | Real GB10 report evidence stands (chain byte-unchanged since) |
| manifest flag fields | sweep_flags | argparse → main() resolution → _manifest_payload | ✓ | run_sweep byte-unchanged |
| registry merged dict | registry | official JSON file + optional custom JSON file | ✓ | Live byte-identity re-check passed this pass |

### Behavioral Spot-Checks

All executed by this verifier at HEAD `def16a5`.

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Phase-7 test suites (6 files) | `.venv/bin/python -m pytest tests/test_flops_counter.py tests/test_registry_loader.py tests/test_sweep.py tests/test_artifact_loader.py tests/test_run_finetune_contracts.py tests/test_known_defects.py -q` | 276 passed, 2 skipped in 1.38s | ✓ PASS |
| Torch-free CPU import | `python -I` — import flops_counter, registry_loader, artifact_loader + `'torch' not in sys.modules` | cpu-import-ok / torch-free-ok | ✓ PASS |
| Overlay byte-identity when absent | live: empty `DNALLMMARK_CUSTOM_REGISTRY_DIR` → `load_models_registry("pipeline")` vs official JSON | equal dict AND equal key order (n=62); 0 official entries with `enabled` | ✓ PASS |
| Tolerant loader 4-case regression | live: valid/empty/truncated-UTF8/missing | valid→dict; others→None | ✓ PASS |
| Lint recipe PHASE7 expansion | `make -n lint` | three-file PHASE7 sequence present | ✓ PASS |
| Legacy absence + zero references | `test ! -e` + grep | absent / 0 lines | ✓ PASS |

### Probe Execution

Not applicable — phase declares no `scripts/*/tests/probe-*.sh` probes; the runtime proof is plan 07-06's GB10 smoke whose evidence stands with the FLOPs chain byte-unchanged (this pass's git audit).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PIPE-01 | 07-01, 07-04, 07-05, 07-06 | FlopsCounter 20+ architecture port into run_finetune.py | ✓ SATISFIED | Truths 6-9, 12, 13 — FLOPs chain byte-unchanged; suites green |
| PIPE-02 | 07-03, 07-06 | run_sweep argv passthrough of the four flags | ✓ SATISFIED | Truths 1-5 — files byte-unchanged; suite green |
| PIPE-03 | 07-01 | Tolerant loader JSON contract shared with the future monitor | ✓ SATISFIED | Truth 10 — live 4-case re-check passed |
| CUST-05 | 07-02 | Registry overlay: collision fail-fast, byte-identical when absent, existing tests zero-modification | ✓ SATISFIED | Truth 11 — byte-identity live-proven; 24-test suite green |

Orphan check: REQUIREMENTS.md maps exactly 4 IDs to Phase 7 (CUST-05, PIPE-01, PIPE-02, PIPE-03), all marked Complete; all four are claimed by plans and satisfied. No orphans. REQUIREMENTS.md itself is outside the covered set and unchanged by the delta.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | Zero TBD/FIXME/XXX markers in `Makefile` and `README.md` (re-scanned this pass); the other 17 covered files stand clean from prior scans (byte-unchanged) | - | - |

**Warnings (non-blocking, carried forward from the prior pass — still applicable):**

| # | Finding | Severity | Impact |
|---|---------|----------|--------|
| W1 | ROADMAP SC4's consumer list names **export** among the overlay consumers, but `script/export_runs.py` was deliberately NOT rewired (locked decision D-09 scope). Re-checked this pass: `export_runs.py` byte-unchanged since Phase 7 and still joins registries via explicit `--models-info`/`--datasets-info` CLI paths. Documented-by-decision deviation, non-blocking. | ⚠️ Warning | Remains a documented-by-decision deviation |
| W2 | GPU emission evidence (Truth 9) predates Phases 8-12; the FLOPs chain has zero commits since the smoke and this pass's git audit confirms byte-identity — but strictly, the exact current tree state has not itself been GPU-run. | ℹ️ Info | Acceptable: zero FLOPs-chain code changed since the smoke; a future bounded smoke under E2' will re-prove the tree |
| W3 | Review-disposition Info findings IN-01..IN-05 remain open by maintainer scope decision (`07-REVIEW-DISPOSITION.md`); relevant files byte-unchanged. | ℹ️ Info | Non-blocking; documentation/cleanup-tier, out of the CR+WR fix scope the maintainer chose |

### Human Verification Required

N/A — Infrastructure/foundation phase (pipeline tooling, no user-facing elements). All acceptance criteria verified programmatically: six phase-7 suites green (276 passed), live behavioral contracts re-run (torch-free import, overlay byte-identity, tolerant-loader 4-case), gate expansion re-proven by dry-run, delta hunk-audited in full. No ⚠️ PRESENT_BEHAVIOR_UNVERIFIED truths, no abstained non-inferable truths.

### Re-Verification Record

- **Route:** #4682 stale fingerprint (third stale-fingerprint re-run over this phase; prior pass `passed` 14/14 at 2026-10-13T09:26:11Z / HEAD `8b92766`).
- **Staleness diagnosis confirmed:** `git diff --stat 8b92766..HEAD` over the covered set → only `Makefile` (+28/-4) and `README.md` (+4/-1) changed — Phase 12's sanctioned close-out additions; all pipeline code and tests byte-identical. Working tree adds no uncommitted Makefile/README changes.
- **Delta contract analysis:** every hunk audited — PHASE7_MODULES definition and lint inclusion byte-unchanged (dry-run expansion re-proven), `snapshot-update` is an additive maintainer-only target touching no existing lane, README change is a documentation-only link. No Phase 7 contract impacted.
- **Regression check:** all 14 truths quick-checked (covered files byte-unchanged + symbol/wiring greps + green suites); Truths 10/11/12/14 live re-executed. Zero regressions.
- **Fingerprint recomputed** over the current tree via `verification.fingerprint`; `covered_digest` in the frontmatter is the command's verbatim output (`v3:sha256:bf92f37c...c8468`).

### Gaps Summary

No gaps. The stale fingerprint was diagnosed (Makefile +28/-4, README +4/-1 — Phase 12's sanctioned delta), the delta hunk-audited against every Phase 7 assertion (PHASE7 gate expansion re-proven, no pipeline contract touched), all 14 must-have truths verified against the current tree, six phase-7 suites re-run green (276 passed, 2 environmental skips), live overlay/tolerant-loader contracts re-executed, all 4 requirement IDs satisfied with no orphans, zero debt markers, and the covered-input fingerprint regenerated at the current tree state.

---

_Verified: 2026-10-14 (stale refresh at HEAD def16a5; prior pass 2026-10-13T09:26:11Z at HEAD 8b92766)_
_Verifier: Claude (gsd-verifier)_
