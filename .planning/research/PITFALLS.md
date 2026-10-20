# Pitfalls Research

**Domain:** Adding dynamic dispatch, TUI multi-GPU surface, and error bars to the existing platform
**Researched:** 2026-10-20
**Confidence:** HIGH for structural pitfalls (they follow from the architecture); MEDIUM for external-tool specifics noted inline

## Pitfalls (ordered by expected phase)

### P1. Resume-marker / output-root ownership under dynamic dispatch — **probability HIGH if naive, impact HIGH**
**The trap:** today `trainer_state.json` lives under a worker-owned frozen root (`{root}-mgpu-w{i}`). If v1.3 keeps worker-scoped cell paths, a cell crashed by worker A either (a) never re-runs because its half-written state sits in A's root while the queue thinks it's pending elsewhere, or (b) runs twice. Workers change identity across relaunches under dispatch.
**Prevention:** cell-stable output paths independent of worker identity (one root, ordinary cell subpaths) + an O_EXCL claim ledger for double-dispatch impossibility; child-level marker-skip stays authoritative for completion. **Phase:** dispatch core (first phase). Test: kill a fake child mid-cell on "worker 0", relaunch, assert exactly-once completion.

### P2. Merge semantics drift — probability MEDIUM, impact HIGH
**The trap:** `--merge` assumes frozen sibling roots and rewrites `output_dir` prefixes; dispatch-mode runs have no per-worker roots. Silently merging a dispatch root with legacy roots double-counts cells (the gen_progress §6 never-both-roots warning is the existing smell).
**Prevention:** dispatch mode and legacy static-shard mode are *declared* (root layout / ledger presence), merge refuses mixed modes loudly; dispatch roots need no merge (document, don't special-case). **Phase:** dispatch core.

### P3. Lane-flag blindness in cross-worker failure re-run — probability HIGH, impact MEDIUM
**The trap:** v1.2's known limitation (12-04): sweep manifests don't record peft/curve, so a lora worker's failures re-run as BASE cells — "a different experiment, not a recovery". A cross-worker re-run helper inherits this bug amplified.
**Prevention:** the dispatch ledger records the full lane context at claim time; the re-run helper enumerates from the ledger, never from a bare failure list. **Phase:** failure recovery.

### P4. Unstratified 5% subsets break classification tasks — probability HIGH, impact MEDIUM
**The trap:** random 5% of a multi-class dataset can empty minority classes in dev/test (metrics become undefined/NaN) and never reconciles against declared counts (n_audit mismatches the subset's honest size).
**Prevention:** stratified sampling per split (class-preserving); subset registry carries **measured** row counts and its own Train/Dev/Test truths; a small-batch sanity check per task type before the sweep. **Phase:** subset generator.

### P5. nvidia-smi probe brittleness — probability MEDIUM, impact LOW
**The trap:** parsing human-formatted output breaks across driver versions; utilization values like "0 %" vs "0"; MIG mode changes device enumeration; binary absent on CPU boxes/CI (which is **every** CI lane).
**Prevention:** `--format=csv,noheader,nounits` query mode only; read-only + graceful 未安装 degradation (env_smoke precedent); probe result is a frozen dataclass, screen renders state-then-DOM; never a hard gate. CI never runs the probe against real GPUs (injectable seam). **Phase:** TUI G lanes.

### P6. Error bars that move the numbers — probability MEDIUM, impact **CRITICAL** (Core Value)
**The trap:** any change to aggregation output that alters existing bytes breaks the zero-drift gate and the published-numbers trust contract; "error-aware ranking" ideas (e.g., re-ranking by lower confidence bound) would silently change leaderboard order.
**Prevention:** std emission is **additive-optional** (absent fields → byte-identical JSON); ranking math untouched; zero-drift gate extended to prove additivity; METHODOLOGY.md documents the display-only semantics. **Phase:** web error bars.

### P7. Chart.js error-bar implementation traps — probability MEDIUM, impact LOW
**The trap:** scatter has no native error bars; floating bars only work on bar charts; a plugin that draws during animation glitches; tooltips/hover points drift from whiskers; forgetting `chart.destroy()` before re-render (existing discipline) leaks canvases.
**Prevention:** vendored inline `afterDatasetsDraw` plugin with `getPixelForValue()` (Chart.js 4 API, HandsOnDataViz idiom) + `animation: false` or draw-on-complete; single shared plugin instance; node:test asserts pixel math as a pure function. Probe-pin Chart.js 4.4.0 behavior in a real browser check once (the 48/48 Playwright precedent from Phase 4 exists if needed). **Phase:** web error bars.

### P8. TUI bypassing gates for multi-GPU — probability MEDIUM, impact HIGH (trust)
**The trap:** slot-4's single-GPU serial gate (261015-ehc stage-0 refusal) exists to stop accidental parallel single-box launches; wiring multi-GPU launch could accidentally weaken E2' typed-phrase/full-scope gates or the y-confirmation launch gate.
**Prevention:** multi-GPU launch reuses the *same* gate chain objects (env gate, problems, confirm, E2' exact-phrase) with only the worker/GPU params added; gate-order tests extended; the CLI-vs-TUI trust boundary (docs/multi-gpu.md Pitfall 7) is NOT projected onto CLI. **Phase:** TUI.

### P9. Test environments assuming N>1 — probability MEDIUM, impact MEDIUM
**The trap:** dispatch code tested as if 2+ GPUs exist; CI (and any CPU box) has none; tests that shell out to nvidia-smi or require CUDA devices rot CI.
**Prevention:** all dispatch tests via fake children (run_sweep fake-executor precedent) + injected probe seams; the only real N>2 execution is the maintainer-authorized smoke on the 2×5090 box (D-05 revision). **Phase:** all phases (structural).

### P10. State-file write contention — probability LOW, impact MEDIUM
**The trap:** if every worker writes `dispatch_state.json`, interleaved partial writes corrupt the one file TUI/web read.
**Prevention:** single-writer rule — only the dispatcher process writes (atomic tmp+rename); workers report via pipe/stdout events. **Phase:** dispatch core.

### P11. Windows/macOS paths — ruled out entirely (Linux-only platform rule 2026-10-20); do not add compatibility shims anywhere in the new code.

## Warning Signs (detect early)

- A cell path containing a worker index after the dispatch rework → P1 live
- `--merge` output_dir rewriting on a dispatch root → P2 live
- Subset registry reusing the real registry's declared counts → P4 live
- Any existing comparison JSON byte change without new keys → P6 live
- `nvidia-smi` output parsed line-by-line without csv mode → P5 live

## Prevention Summary

Every pitfall above maps to a structural mechanism (ledger, mode declaration, stratified sampler, additive schema, csv-mode probe, shared gate objects, fake children) — none relies on reviewer vigilance alone. The phase plan should place P1's kill-and-relaunch test and P6's additivity gate as first-class acceptance criteria.
