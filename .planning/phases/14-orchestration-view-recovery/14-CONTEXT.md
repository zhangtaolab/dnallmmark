---
phase: 14-orchestration-view-recovery
title: 编排运行视图与失败恢复 (Orchestration View & Failure Recovery)
status: approved
created: 2026-10-20
---

# Phase 14: 编排运行视图与失败恢复 - Context

**Gathered:** 2026-10-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Running multi-GPU sweeps become observable and recoverable: the Phase 13 dispatch
state file gains its frozen consumer contract and a live terminal table; failed cells
re-run through ONE command with full lane context (fixing the v1.2 lane-blindness
limitation); and the post-merge verify + cleanup helper replaces the manual rm -rf
runbook step. GPU validation (N=2 smoke) stays in Phase 15; TUI consumption in Phase 16.

</domain>

<decisions>
## Implementation Decisions

### Live Run View (MGPU-03)
- **D14-01:** The state file is Phase 13's `{root}/dispatch_state.json` EXTENDED (single-writer, atomic) — no second file; Phase 14 freezes the consumer schema (queue depth, per-worker in-flight cell, failures, timestamps)
- **D14-02:** Terminal table = plain-line renderer (stdlib prints) inside dispatch_core.py or a thin sibling, rendering per-worker rows on every state write — no timer loop, no TUI library
- **D14-03:** Render cadence = on each state write (claim/finalize/event); pty/capsys tests assert row content after scripted events
- **D14-04:** Schema frozen and parseable by a consumer test BEFORE Phase 16 (TUI) touches it; `script/gen_progress.py` mirror updated in the same commit as any schema change

### Failure Re-Run (MGPU-04)
- **D14-05:** Re-run surface = `--from-failures`-style flag on dispatch mode itself (one command re-runs the union of failed cells), reusing the CR-01 filter machinery landed in Phase 13
- **D14-06:** Lane flags (peft/config_variant/num_train_epochs/subset_file/effective_batch_size/cache_dir) recorded at claim time are replayed verbatim on re-run — the 12-04 lane-blindness fix, fixture-proven
- **D14-07:** Failure-union semantics: ledger `state: failed` cells across ALL prior runs on the root form the re-run set; re-runs create FRESH O_EXCL claims carrying a `rerun_of` link to the original — old claims are never mutated (audit trail preserved)
- **D14-08:** Heterogeneous lane signatures among failed cells refuse loudly, naming the differing flag per cell (mirrors the merge lane-equality refusal discipline)

### Post-Merge Verify + Cleanup (MGPU-05)
- **D14-09:** Helper shape = `run_sweep_shard.py --cleanup --workers N --output-root R` sibling mode: verify THEN offer removal behind an explicit confirmation gate
- **D14-10:** Verification = `script/export_runs.py` dry-run over the merged root + manifest cell-count equality vs the union of worker manifests — both green before removal is offered
- **D14-11:** Removal gate = explicit typed confirmation (interactive `--yes` typed phrase or non-interactive refusal); refusal paths tested; static-merge roots only — dispatch roots get a named "needs no cleanup" error (one root by construction)
- **D14-12:** Scope: static-mode worker roots only

### Testing & CI Shape
- **D14-13:** Table assertions via capsys/pty lane over scripted fake-child event sequences (worker/cell/state strings per step); no full-screen golden snapshots
- **D14-14:** State-schema consumer test parses dispatch_state.json against a frozen schema definition committed with any field change
- **D14-15:** Re-run fixture = two-worker fake run with injected failures on BOTH workers → one re-run → exactly the failed cells re-claimed with original lane flags, healthy cells untouched
- **D14-16:** Full CPU lanes stay green (pytest/ruff/ty + node); static mode byte-identical; zero CI changes; stdlib-headless held; fake children + injected seams only

### Claude's Discretion
- Exact table column set/format (worker id, cell key, state, elapsed) provided the frozen-schema and capsys assertions cover it
- Whether the renderer lives in dispatch_core.py or a thin sibling module (follow Phase 13's compose-as-sibling ergonomics)
- The `rerun_of` link's exact JSON shape inside the claim payload

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pipeline/dispatch_core.py` (Phase 13): single-writer atomic `_write_state`/`_atomic_write_json`, claim ledger with lane flags at claim time, per-GPU worker loops, `--from-failures` filter machinery (CR-01 fix: `run_sweep.load_failure_pairs` + base_model_name join), containment + accounting assertion, exit-0-no-metrics fail-safe
- `pipeline/run_sweep_shard.py`: mode routing in `main()`, `run_merge` (SHA256-verify copy, MERGE_ALLOWLIST, lane-equality refusal with per-flag diagnostics — the refusal-shape precedent for D14-08/D14-11), collect-all `sys.exit(f"[Error] ...")` idiom
- `pipeline/run_sweep.py`: `load_failure_pairs`, `--from-failures` semantics (frozen contract, referenced not modified)
- `script/export_runs.py`: dry-run seam for merged-root verification; `script/gen_progress.py`: progress JSON generator (worker-roots warning precedent)
- `tests/test_dispatch_core.py` (53 tests): fake-spawner idioms, per-cell scripted children, spy children, ENOSPC injection, SC2 kill test — the harness this phase extends

### Established Patterns
- O_EXCL create-or-refuse structural guards; atomic single-writer JSON writes; evidence-based (never shape-inferred) mode detection
- Collect-all problem reporting; per-worker tee logs; mutation-proven regression pins (the review loop's discipline)
- Stdlib-headless: no torch/dnallm at module top; CI never assumes N>1 devices

### Integration Points
- `dispatch_state.json` gains frozen consumer fields — consumed by the terminal renderer (this phase), TUI slot 5 (Phase 16), gen_progress mirror
- Failure ledger (`state: failed` claims + lane flags) is the MGPU-04 re-run feed
- `--cleanup` joins `--merge` as a sibling mode in run_sweep_shard main()

</code_context>

<specifics>
- Research `.planning/research/ARCHITECTURE.md` §A (state file) + §B (failure re-run + cleanup) is the design backbone
- Phase 13 SUMMARYs document the ledger/state/naming contract this phase builds on (claim naming = percent-encoding + sha256[:12])
- Binding constraints: TUI orchestrates never computes (the renderer here is pipeline-side CLI output, not TUI); leaderboard numbers move only through zero-drift-proven additive changes; surgical fixes only

</specifics>

<deferred>
- TUI slot-5 consumption + G GPU-lanes display → Phase 16 (TUI-03/TUI-01)
- Real-GPU exercise of the view/re-run on 2×5090 → Phase 15 (VAL-03 small real sweep uses this machinery end-to-end)
- `gen_progress.py` web-mirror enhancements beyond keeping it parsing → follow Web phase scope

</deferred>
