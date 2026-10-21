---
phase: 16-tui-multi-gpu-surface
title: TUI 多 GPU 界面 (TUI Multi-GPU Surface)
status: approved
created: 2026-10-21
---

# Phase 16: TUI 多 GPU 界面 - Context

**Gathered:** 2026-10-21
**Status:** Ready for planning

<domain>
## Phase Boundary

The operator console launches and watches multi-GPU runs natively: a
textual-free read-only gpu_probe service feeds a G GPU-lanes display on the
monitor cadence; slot-4 run config launches multi-GPU dispatch through the
UNCHANGED gate chain (env gate → problems → confirm → E2' typed phrase when
full-scope), with the single-GPU serial gate revised to multi-GPU-aware
semantics; slot-5 consumes dispatch_state.json (frozen Phase 14 schema)
alongside existing scanner sources. Snapshot goldens for changed screens
regenerate uncommitted under the D-03 maintainer-review discipline.

</domain>

<decisions>
## Implementation Decisions

### gpu_probe Service (TUI-01)
- **D16-01:** Probe = `nvidia-smi --query-gpu=... --format=csv,noheader,nounits` subprocess CSV → frozen dataclass rows (index, utilization, memory_used, memory_total, temperature; fixed units) — pynvml explicitly out of scope
- **D16-02:** Honest degradation: missing binary / non-zero exit → explicit 未安装 empty-state row; never raises into the console, never fabricates data; unit-tested via injected seam (EnvCheckServiceProtocol pattern)
- **D16-03:** Cadence rides the existing monitor refresh (2s frontier class) with a short per-call timeout (~2s) so the UI never blocks; no resident poller thread
- **D16-04:** Rows sorted by index; N=0 renders an explicit empty state

### G Lanes Panel + Slot-5 (TUI-01/03)
- **D16-05:** G panel = a new section on the existing monitor screen (Running/History tab structure untouched) rendering probe rows
- **D16-06:** New `tui/services/dispatch_state.py` reader service (JSON → dataclasses, tolerant read, Phase 14 frozen schema) joins the slot-5 scanner data sources; Running tab gains queue-depth/in-flight rows
- **D16-07:** Worker-guard discipline: services import zero textual (import-lock test extended to the new service); screens stay thin
- **D16-08:** Stale marking: dispatch_state mtime beyond a threshold (~60s) renders a stale marker instead of silently presenting old data

### Slot-4 Multi-GPU Launch (TUI-02)
- **D16-09:** RunSpec gains workers/gpus fields (defaults 1/all-detected); the composer builds `run_sweep_shard.py --mode dispatch` argv
- **D16-10:** Gate chain UNCHANGED: env gate → problems → confirm → E2' typed phrase for full-scope; the single-GPU serial gate's stage-0 refusal is replaced by multi-GPU-aware semantics (N GPUs → N concurrent cells is the sanctioned shape) — no gate weakened, gate-order tests extended
- **D16-11:** Confirm screen shows a dispatch-plan preview (queue depth — dry-run projection or enumeration table)
- **D16-12:** E2' boundary unchanged: full-scope sweeps still require the typed phrase; subset/smoke scopes route through the existing problems gate

### Goldens & Gates (TUI-04)
- **D16-13:** Snapshot goldens regenerate for CHANGED screens only (config preview+confirm, monitor incl. G lanes + dispatch rows), UNCOMMITTED pending D-03 maintainer review; unchanged screens' goldens untouched
- **D16-14:** Existing gate-order tests extended for multi-GPU semantics with zero weakening; all service unit tests via injected seams; full CPU lanes green; stdlib+existing-deps only
- **D16-15:** Copy strings centralized per the existing i18n convention (tui/strings.py) — no scattered literals in screens

### Claude's Discretion
- Exact G-panel column set/format provided stale/empty states are covered
- dispatch_state reader's internal dataclass field set (frozen-schema superset allowed, missing-field tolerance required)
- How the queue preview computes depth (dry-run subprocess vs enumeration from the registry) provided it is honest about being a preview

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tui/services/sweep_monitor.py`: scanner data-source pattern, tolerant reads, three-state discovery — dispatch_state.py follows it
- `tui/services/sweep_launcher.py`: detached subprocess + tee + killpg, O_EXCL discipline (reused for the dispatch composer)
- `tui/services/env_check.py` + the EnvCheckServiceProtocol injection seam (gpu_probe's test pattern)
- `tui/screens/` slot 4 run-config + terraform-style gates (env gate → problems → confirm → E2'); single-GPU serial gate refusal lives on both launch paths
- `tui/strings.py` i18n convention; snapshot golden machinery (D-03 discipline)
- `schemas/dispatch_state.json` (frozen v2) + `pipeline/run_sweep_shard.py --dry-run` plan artifact

### Established Patterns
- Services textual-free (import-lock test); screens thin; worker guard never crashes the console
- TUI orchestrates, never computes — no client-side re-implementation of benchmark semantics (AST/import pins)

### Integration Points
- gpu_probe → monitor cadence; dispatch_state reader → slot-5 scanner; RunSpec workers/gpus → dispatch composer → run_sweep_shard argv
- Goldens under the existing snapshot test lane (CPU-only, no GPU assumed — gpu_probe tests inject; golden fixtures fabricate rows)

</code_context>

<specifics>
- Research `.planning/research/ARCHITECTURE.md` §D is the design backbone
- Binding constraints: TUI orchestrates never computes; CI zero-GPU (probe tests inject seams only); goldens uncommitted until reviewed; Linux-only; no new deps
- The dispatch CLI runs verbatim — defects route through the normal fix flow

</specifics>

<deferred>
- Web error bars → Phase 17
- Docs for the TUI surface (TUI-DEMO.md precedent) → Phase 18 (DOCS-03)

</deferred>
