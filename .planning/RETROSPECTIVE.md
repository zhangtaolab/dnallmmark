# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.2 — TUI任务

**Shipped:** 2026-10-19
**Phases:** 6 (7-12) | **Plans:** 41 | **Quick tasks:** 30+ (2026-10-14 → 2026-10-20 tail)

### What Was Built
- Pipeline-side enablement ahead of any UI: FlopsCounter ported (20+ architecture hooks, CPU-provable via stub torch modules, `flops_report.json` v1 schema), the four sanctioned sweep flags threaded with byte-identical-when-absent argv parity, and the official+custom registry overlay (collision fail-fast, byte-identical when absent)
- The TUI console end-to-end over a textual-free services layer: persisted env-check panel, k9s-style selection with presets/templates/presence, custom model/dataset wizards behind a collect-all validator + dry-run/audit gauntlet + entry-level rollback, a persistent resumable ModelScope/Zenodo download queue with n_audit row-count reconciliation, run config with same-source dry-run preview and terraform-style launch gates (E2' typed-phrase boundary held), and the slot-5 monitor through many maintainer-driven redesigns (two-tab Running/History, tree mode, planned-cell union, stale-progress guard)
- Multi-GPU orchestration as a new composing entry (`run_sweep_shard.py`: LPT sharding × CUDA_VISIBLE_DEVICES, frozen sibling roots, SHA256-verified `--merge`, lane-equality refusal) plus the sharding-vs-DDP decision matrix (`docs/multi-gpu.md`), a static read-only web progress mirror, and an 8-SVG snapshot-golden corpus
- A CI-safe pty driver lane (pexpect, zero new runtime deps) proving real-process behavior Pilot cannot see — the long-term defense established during the soak-test round

### What Worked
- Hard-gated sequencing (单卡开发成功再开发多卡): Phase 12 composed cleanly on frozen Phase 11 seams with near-zero monitor code changes — the compose-don't-modify rule over the frozen argv surface paid for itself
- Gap-closure waves: every verifier `gaps_found` round became a numbered plan (08-08/08-09, 10-07, 11-08) instead of ad-hoc patching — findings converted to tests in one hop
- The quick-task loop for maintainer-reported bugs: root-cause + fix + real-scenario pin in one batch (e.g. 261020-blt's one-model-render bug traced to driver mkdir-on-reach), each landing with the full gate run
- Structural pins over instance fixes: the exit_on_error AST net, the card-extraction allowlist, the strings bidirectional tripwire — each closed a bug *family*, not a bug

### What Was Inefficient
- The exit-key saga took four quick-task rounds (v0z → cdr → mad, 2026-10-16 → 10-17) to reach the maintainer's final F10 ruling; an explicit keybinding ruling at Phase 8 discuss time would have saved two rounds
- Verify-staleness cascade: covered-file digests re-stale phases on every later commit, forcing repeated verifier dispatches through the quick-task tail — accepted as override at close (2026-10-19, gates green)
- Monitor goldens regenerated-uncommitted accumulated across redesigns (WINDOWS #35/#39/#42) behind a single pending D-03 maintainer review — the review gate became a batch bottleneck
- Test baseline churn: later quick tasks moved the suite baseline (2F/1919P drift), recorded as a deferred item rather than re-baselined deliberately

### Patterns Established
- Services layer imports zero textual symbols (import-lock test); screens are thin — mandatory for any future TUI screen
- XDG state/config split for every piece of persisted TUI state; user-owned custom registries never touch official files
- Shared tolerant-loader JSON contract between pipeline and TUI readers (truncated file → last-known-good, never a crash)
- Constants-module Chinese-primary i18n with drift tripwires; verbatim-string landing plans
- New entry over frozen argv: when an interface is frozen by a tier-1 suite, add a composing tool (run_sweep_shard) instead of editing the frozen file
- pty/pexpect repro recipes (fake-probe sweep spawner) for live-process bugs — keep the recipe in the plan doc

### Key Lessons
1. Land the non-retrofittable decisions first (Phase 8's declared purpose) — every later phase added screens, not architecture; zero architectural rework across 41 plans
2. AST structural pins are the cheapest way to make "never again" enforceable — instance fixes rot, allowlists don't
3. Real-process evidence beats framework test rigs: the pty lane caught the cached-MonitorScreen dead-5 and stale-progress families that Pilot structurally cannot
4. Freeze argv/file surfaces early and let the tier-1 suite guard them; composition then becomes the only extension path, which is exactly what multi-GPU needed

### Cost Observations
- Model mix / session counts: not tracked per-milestone (no telemetry) — start recording if cost becomes a concern
- Notable: the full CPU suite grew from ~550 (v0.7.1) to ~2000 tests and still runs ≈9 min; every quick task closed with the complete gate run (ruff + ty + pytest + node + goldens), which kept the tail batches cheap to review

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v0.7.1 | ~2 weeks | 6 | Audit-first discipline: freeze baseline → contracts → surgical fixes → CI → packaging |
| v1.2 | 2026-10-11 → 10-19 | 6 | Wave-parallel execution + verifier gap-closure loops + quick-task tail for maintainer feedback |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v0.7.1 | ~550 + node lane | data chain + registries pinned | none (stdlib/numpy/pandas only) |
| v1.2 | ~2000 + node lane + pty lane | + tui/ services + argv/flops contracts + goldens | textual+platformdirs ([tui] group), pexpect ([dev]) |
