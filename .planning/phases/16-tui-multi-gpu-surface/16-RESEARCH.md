# Phase 16: TUI 多 GPU 界面 (TUI Multi-GPU Surface) - Research

**Researched:** 2026-10-21
**Domain:** Textual TUI surface extension over existing services — gpu_probe/dispatch_state readers, slot-4 multi-GPU launch through the unchanged gate chain, G GPU-lanes panel, snapshot goldens
**Confidence:** HIGH (every seam read from live code this session with line citations; nvidia-smi probe argv verified live on the 2×5090 validation box; milestone ARCHITECTURE.md §D provides the design backbone — NOT re-derived here)

## Summary

Phase 16 wires the operator console into the multi-GPU machinery Phases 13–15
proved on the CLI. Three surfaces, all extensions of EXISTING screens: (1) a
textual-free `gpu_probe` service (nvidia-smi CSV → frozen dataclass rows,
honest 未安装 degradation) feeding a standing G GPU-lanes panel on the slot-5
monitor; (2) a `dispatch_state` reader service joining the slot-5 scanner's
data sources (queue depth + per-worker in-flight rows, 60s stale marking);
(3) slot-4 run-config gaining workers/GPUs fields that compose
`run_sweep_shard.py --mode dispatch` argv through the byte-pinned gate chain,
with the EHC-3 single-GPU stage-0 predicate replaced by multi-GPU capacity
arithmetic. Goldens for the changed screens regenerate uncommitted under the
D-03 discipline.

The codebase is unusually well-prepared for this phase: every pattern the
phase needs already exists as a named, test-pinned precedent — the
`EnvCheckServiceProtocol` injection seam, the `_default_spawner` Popen
discipline, the `_tick_frontier`/`mon-frontier` cadence, the `_card_content`
one-builder seam, the `_t()` bilingual registry with its bidirectional
inventory tripwire, the `#dl-queue-region` border-top separator TCSS pattern,
and the fallback-lane snapshot machinery. The plan's job is assembling these
precedents, not inventing new mechanics.

The riskiest findings for the planner: (a) `_tick_frontier` early-returns
when no live roots exist (`tui/screens/monitor.py:2302-2303`) — the GPU probe
must dispatch independent of live runs or the panel dies on an idle machine;
(b) the in-place amendment of `LNC_SINGLE_GPU_BLOCKED` changes its format
signature, forcing a lockstep edit across 5 code sites + 3 test sites; (c)
the pty lane's byte-silence pin (`test_pty_driver.py:478`) asserts ZERO
terminal bytes over 5.5s on the REAL app — the G panel's content-signature
gate must be airtight because the probe reads real, fluctuating hardware on
the dev box; (d) the working-tree goldens are CLEAN (#35/#39/#42 were
committed 2026-10-19), so Phase 16 opens a NEW D-03 review batch — the
UI-SPEC's "joins that same review batch" describes the discipline, not an
open dirty tree.

**Primary recommendation:** Land in the order services-first (gpu_probe →
dispatch_state reader → RunSpec/composer/predicate extensions, each with
unit tests via injected seams), then screens (G panel → dispatch rows →
slot-4 fields + confirm line), then the gate-order test extensions, and
goldens LAST (`make snapshot-update`, uncommitted). The gate chain's stage
ORDER and VEHICLE stay byte-identical; only the predicate inside
`single_gpu_launch_blocked` changes semantics.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

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

### Deferred Ideas (OUT OF SCOPE)
- Web error bars → Phase 17
- Docs for the TUI surface (TUI-DEMO.md precedent) → Phase 18 (DOCS-03)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description (REQUIREMENTS.md) | Research Support |
|----|-------------------------------|------------------|
| TUI-01 | A textual-free nvidia-smi read-only probe service (CSV query mode, frozen dataclass rows, honest 未安装 degradation when absent) feeds a G GPU-lanes display on the monitor cadence | New `tui/services/gpu_probe.py` following the env_check service shape; probe argv verified live (returns `0, 0, 2, 32607, 29` per GPU on this box); G panel mounts between `#mon-content` and `BottomBar()` in `MonitorScreen.compose` (monitor.py:2095-2107); own `mon-gpu` worker group; TCSS follows the `#dl-queue-region` separator + `#env-detail-log` max-height precedents |
| TUI-02 | Slot-4 run config launches multi-GPU runs (workers/gpus params, dispatch-plan preview) through the UNCHANGED gate chain; the single-GPU serial gate is revised to multi-GPU-aware semantics, never bypassed | RunSpec additive fields + `parse_params` mirrors + new dispatch composer over the frozen shard CLI; stage-0 predicate replaced inside `single_gpu_launch_blocked` (sweep_launcher.py:827-846) — call sites at sweep_launcher.py:898, 1050 and the screen pre-checks (run_config.py:2049-2058, monitor.py:4679-4688, 4949-4958) keep position/vehicle; gate-order tests at test_services_sweep_launcher.py:1372/1399/1448 + test_pilot_run_config.py:1015/1047 extend |
| TUI-03 | Slot-5 monitor consumes `dispatch_state.json` (queue depth, in-flight cells) alongside existing scanner sources; multi-GPU runs render natively | New `tui/services/dispatch_state.py` tolerant reader over the frozen v2 schema (verified: `schemas/dispatch_state.json`); dispatch block inserts via the ONE `_card_content` seam (monitor.py:3385-3434); reader rides the frontier worker pass; 60s stale constant in the reader (the `STALE_GRACE_SECONDS = 600` precedent, sweep_monitor.py:127) |
| TUI-04 | Snapshot goldens for changed screens regenerate under the D-03 maintainer-review discipline (uncommitted until reviewed) | Fallback-lane machinery verified (test_snapshots.py:751 `_golden_app` constructor injection, `_frozen_mon_clock`:722); `make snapshot-update` is the only regen path (Makefile:132-133); working tree currently CLEAN — a NEW D-03 batch opens |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| GPU probing (subprocess nvidia-smi CSV) | tui/services (gpu_probe.py) | — | Services own I/O; textual-free so CPU lanes import it; the screen owns only cadence + rendering |
| GPU-lanes rendering + 2s cadence | tui/screens/monitor.py | services (data) | Screens own cadence/focus/render ("the scanner's declaration" — the service is a pure callable, D16-03) |
| dispatch_state.json reading | tui/services (dispatch_state.py) | — | Tolerant JSON→dataclass reader; textual-free; testable with fixture files, zero dispatch_core import needed |
| Dispatch-row rendering | tui/screens/monitor.py `_card_content` | dispatch_state reader | The ONE content-builder seam keeps ListItem/cursor identity (the f0x law) |
| workers/gpus params + validation mirrors | tui/services/run_config.py | screens/run_config.py (fields) | Machine problems live service-side (collect-all vocabulary); screens render copy only |
| Dispatch argv composition | tui/services/run_config.py | — | The composer is mechanical; the shard CLI stays the single validation authority |
| Capacity predicate (stage-0 replacement) | tui/services/sweep_launcher.py | run_config.py service (spec fields) | The gate is structural in the SERVICE (screens re-check via tolerant getattr; the service stage-0 is the backstop) |
| Confirm-face dispatch-plan line | sweep_launcher.gate_confirm_data (GateSummary) | run_config.py screen modals | Numbers arrive service-side (TUI orchestrates, never computes); cells = the same fresh enumeration |
| Copy (18 constants + 1 amendment) | tui/strings.py | — | D16-15 single home; `_t()` registry + inventory tripwires |
| Goldens | tests/tui/test_snapshots.py | — | Fallback lane; `make snapshot-update` only; D-03 uncommitted discipline |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| textual | 8.2.8 (uv.lock-pinned, `>=8.2,<9` [tui] group) | The TUI framework — unchanged | Verified in the repo venv this session: `textual 8.2.8`, Python 3.13.14 [VERIFIED: live venv probe] |
| stdlib subprocess | Python 3.13 | gpu_probe nvidia-smi call | D16-14 stdlib-only; the `_default_spawner` discipline precedent |
| stdlib json/dataclasses | Python 3.13 | dispatch_state reader | The artifact_loader/env_check precedent |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `tui.services.artifact_loader` (pipeline/ top-level module) | existing | `load_json_artifact` None-sentinel tolerant JSON read | The dispatch_state reader's absent/damaged → None contract (the env_check.py:95 precedent) |
| `tui.services.settings` | existing | `state_dir()` (tee logs), atomic_write | Already the persistence root; unchanged this phase |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| nvidia-smi CSV subprocess | pynvml | REJECTED in REQUIREMENTS (out of scope); pynvml adds a dep + NVIDIA driver binding; D16-01 pins CSV mode |
| Dry-run subprocess for queue preview | `run_config.preview()` same-source enumeration | UI-SPEC auto-default #7 pins preview() (same-source zero-copy, no subprocess in the gate path); the dry-run IS available (`--dry-run` writes only sweep_manifest.json) but adds a spawn per gate-open — rejected |

**Installation:** None. Zero new dependencies (D16-14: stdlib + existing deps
only; UI-SPEC Registry Safety: "gpu_probe is stdlib `subprocess` only; the
dispatch_state reader is stdlib `json` only").

## Package Legitimacy Audit

No external packages are installed this phase. Nothing to audit. Existing
pins (textual 8.2.8, platformdirs) were legitimacy-approved at 08-02
(maintainer delegation on record, STATE.md) and are untouched.

## Architecture Patterns

### System Architecture Diagram

```text
 slot-4 运行配置 (tui/screens/run_config.py — EXISTING)
   params pane: [.. effective_batch_size row :1304-1308]
              → NEW 多 GPU 调度 section (workers / GPUs fields + hint)
              → [CFG_DIRS_TITLE :1309]
                │ _compose_spec (:1639) → RunSpec{workers:int=1, gpus:tuple|None}
                │ parse_params mirrors: workers_invalid / gpus_invalid /
                │                       workers_exceeds_gpus  (collect-all)
                ▼
   GATE CHAIN (position/vehicle byte-pinned; ONLY stage-0 predicate replaced)
   [enter :1983] → fresh enumeration (cfg-gate-enum worker)
     → ProblemsModal (parse+preview problems, incl. the 3 new mirrors)
     → CR-02 live-root refusal (:2036)
     → CAPACITY STAGE (:2042-2058 — was EHC-3, now multi-GPU arithmetic)
     → env preflight (cfg-gate-env) → EnvBlockModal
     → confirm face: E2PhraseModal (full scope, phrase gate UNTOUCHED)
                   / _GateConfirmModal + NEW LNC_GATE_DISPATCH_LINE
     → launch (cfg-gate-launch) → sweep_launcher.launch_spec (:848)
        stage 0: single_gpu_launch_blocked → REPLACED predicate (:898)
        stage 1: preview problems → stage 2: official keys → stage 3: phrase
        → _spawn(run_sweep_shard.py --mode dispatch argv, tee, registry)
                │
                ▼  (dispatch_state.json written by pipeline/dispatch_core.py)
 slot-5 任务监控 (tui/screens/monitor.py — EXISTING)
   _run_frontier (mon-frontier, 2s): per live root + NEW dispatch_state read
     → running card: strip → NEW dispatch line + worker rows + stale row
       (via _card_content :3385, the ONE builder seam) → matrix/tree
   _tick_frontier fires → NEW mon-gpu worker (independent of live roots!)
     → gpu_probe.py: nvidia-smi CSV → GpuRow[] | absent
     → #mon-gpu panel (NEW section under #mon-content, both tabs)
   goldens: run_config / monitor_empty / monitor_running REGENERATE
          + run_config_confirm NEW  (uncommitted, D-03)
```

### Recommended Project Structure

```text
tui/
├── services/
│   ├── gpu_probe.py        # NEW — nvidia-smi CSV probe (textual-free)
│   └── dispatch_state.py   # NEW — frozen-v2 tolerant reader (textual-free)
├── screens/
│   ├── monitor.py          # EDIT — #mon-gpu panel, dispatch rows, mon-gpu worker
│   └── run_config.py       # EDIT — mgpu params section, capacity stage, confirm line
├── strings.py              # EDIT — +18 constants, LNC_SINGLE_GPU_BLOCKED amended
└── styles.tcss             # EDIT — #mon-gpu block ONLY (slot-4: zero new TCSS)
tests/tui/
├── test_services_gpu_probe.py        # NEW — injected runner fakes
├── test_services_dispatch_state.py   # NEW — fixture files incl. damaged/absent
├── test_services_sweep_launcher.py   # EXTEND — capacity family (:1372/:1399/:1448)
├── test_services_run_config.py       # EXTEND — parse/persist/compose-dispatch pins
├── test_pilot_run_config.py          # EXTEND — gate-order multi-GPU (:1015/:1047)
├── test_pilot_monitor.py             # EXTEND — G panel + dispatch rows + refusals
├── test_strings_phase11.py           # EXTEND — EXPECTED_* inventory tuples
└── __snapshots__/                    # 3 REGENERATED + run_config_confirm.svg NEW
```

### Pattern 1: The injectable-subprocess service (gpu_probe)
**What:** A textual-free service module whose OS seam (Popen/run) is
constructor/parameter-injectable; CI injects canned stdout/exit codes.
**When to use:** gpu_probe. The exact precedent is
`sweep_launcher._default_spawner` (sweep_launcher.py:335-351 — "the injectable
Popen seam... a pure forward to `subprocess.Popen`") plus the
`SweepLauncher.__init__(spawner=None, ...)` shape (:687-694).
**Example:**
```python
# Source: tui/services/sweep_launcher.py:335-351 (the seam being copied)
def _default_spawner(argv, **kwargs):
    return subprocess.Popen(argv, **kwargs)
# gpu_probe's shape: an injectable RUNNER returning (returncode, stdout) —
# tests inject `lambda argv, timeout: (0, "0, 0, 2, 32607, 29\n1, 0, 2, 32607, 28\n")`
# or (1, "") / raise FileNotFoundError / raise TimeoutExpired — the four
# degradation modes (D16-02), each asserting the SAME absent result.
```

### Pattern 2: The tolerant reader with a None sentinel (dispatch_state)
**What:** Absent file / damaged JSON → None, never a crash; the screen renders
last-known-good through its content gate.
**When to use:** dispatch_state.py. The precedent is
`env_check.load_cached` → `artifact_loader.load_json_artifact(path)` —
"missing, unreadable, empty, truncated, or not valid JSON (the
artifact_loader None sentinel — a cache miss, never a crash)"
[VERIFIED: tui/services/env_check.py:81-95].
**Example:**
```python
# Source: schemas/dispatch_state.json:31 (status enum — render VERBATIM, never translated)
"status": { "enum": ["running", "done", "incomplete"] },
# Reader exposes: DispatchStateView(run_id, status, started_at, updated_at,
#   counts{total,completed,failed,skipped}, queue_depth,
#   workers[{index,gpu,in_flight,cells,completed,failed}], failures[],
#   state_mtime)  — frozen-schema superset, missing-field tolerant (CONTEXT discretion)
```

### Pattern 3: The exclusive per-group cadence worker
**What:** `set_interval` ticks only dispatch `@work(exclusive=True,
thread=True, group=...)` workers; run-id-tagged messages; per-worker GROUPS
are mandatory.
**When to use:** the mon-gpu probe worker. Verified precedents:
`@work(exclusive=True, thread=True, group="mon-frontier", exit_on_error=False)`
(monitor.py:2307-2308) and `group="mon-full"` (:2254). STATE.md 10-04 lesson:
"per-worker @work groups are mandatory for concurrent exclusive workers —
textual exclusivity cancels by (node, group), so the mount pair sharing the
default group silently cancelled each other".

### Pattern 4: The content-signature render gate (the rze law)
**What:** Every rendered region keeps a signature sentinel; a steady tick over
unchanged data performs ZERO widget writes; `on_mount` resets sentinels; the
pass is suppressed while a modal is stacked.
**When to use:** the G panel AND the dispatch rows. Verified:
`_render_all`'s early return `if self.app.screen is not self: return  # a
modal or the min-size guard is stacked above` (monitor.py:2935-2936); the
sentinel-reset block `self._tabs_sig = None ... self._cards_sig = None ...`
(:2129-2141, "the render gates MUST reset here or the unchanged sentinels
would gate away the updates"); the tabs gate `sig = (running_count,
history_count, self._active_tab); if sig == self._tabs_sig: return`
(:2978-2981).

### Pattern 5: The one shared content builder (cursor identity)
**What:** ONE builder defines a card's lines for BOTH the rebuild path and the
in-place update path, so ListItem/cursor identity survives.
**When to use:** the dispatch block. Verified: `_card_content`
(monitor.py:3385-3434) is "the ONE content definition shared by BOTH render
paths — the rebuild path (`_card_widget`'s ListItem construction) and the
in-place path (the existing Labels' content update) — so the two can never
drift". The dispatch rows join `lines` here as `.mon-card-resume`-family
`(classes, Text)` pairs.

### Pattern 6: In-place string amendment (constant NAME unchanged)
**What:** Amend a constant's WORDING in place, keeping the name — tests that
reference the name survive; format-field changes ride the same lockstep edit.
**When to use:** `LNC_SINGLE_GPU_BLOCKED` (strings.py:1557-1563). The
precedent named by the UI-SPEC: MON_RERUN_CONFIRM (261015-ehc family). NOTE:
the current constant formats ONLY `{roots}`; the amended copy adds
`{workers}`/`{n}` — see Pitfall 2 for the lockstep surface.

### Pattern 7: Collect-all validation mirrors (driver-authoritative)
**What:** The screen/service mirrors the CLI's validation as cheap machine
problems; the CLI stays authoritative.
**When to use:** workers/gpus fields. Verified precedent: `parse_params`
"the sys.exit-ing run_sweep validators are never called — the bounds are
mirrored here" (tui/services/run_config.py:336-338); codes like
`PROBLEM_SEEDS_INVALID = "seeds_invalid"` (:163-166) rendered through
`_problem_line` (tui/screens/run_config.py:393-415).

### Anti-Patterns to Avoid
- **Probing only when runs are live:** `_tick_frontier` early-returns on
  `if not self._live: return` (monitor.py:2302-2303). GPU state is
  machine-level (both tabs, D16-05) — the probe dispatch must fire regardless
  of live roots (own dispatch site before the guard, or its own timer).
- **Client-side reconciliation of dispatch counts:** the reader NEVER
  recomputes queue depth or fixes inconsistent counts; a broken snapshot
  invariant renders the stale/malformed marker (UI-SPEC B rule 6). "TUI
  orchestrates, never computes" (AST/import pins).
- **Hardcoded hex or new spacing tokens in the G panel:** theme tokens +
  the documented separator/row/scroll-bound exceptions only (styles.tcss
  contract, lines 8-27).
- **Scattered literals:** any operator-facing copy outside `tui/strings.py`
  fails the CJK lock AND the bidirectional inventory tripwire.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tolerant JSON read | try/except json.load chains | `artifact_loader.load_json_artifact` (the None sentinel) | The env_check precedent; one tolerance contract, already test-pinned |
| Detached launch + tee + registry | New spawn logic | `SweepLauncher._spawn` / `launch_spec` seams unchanged | The composer only changes the ARGV; D-06/D-10 discipline (O_EXCL tee, killpg, PYTHONUNBUFFERED) is load-bearing and frozen |
| Queue-depth computation | UI-side cell counting | `run_config.preview()` same-source enumeration (`cells_count`) | UI-SPEC auto-default #7; `gate_confirm_data` already recomputes it fresh (sweep_launcher.py:462) |
| GPU count truth | nvidia-smi parsing for capacity | `effective_gpu_count()` (WORLD_SIZE > torch > 0) — UNCHANGED | sweep_launcher.py:175-210; count-0 machines unrestricted (the EHC-3 letter, kept by UI-SPEC C.4) |
| Stale semantics | Per-screen thresholds | One pinned module constant in the READER (60s), documented-tunable | D16-08 + UI-SPEC D; the `STALE_GRACE_SECONDS = 600.0` precedent (sweep_monitor.py:127) |
| Live-evidence discovery | /proc walks in the predicate | The launcher REGISTRY (`live_sweeps()`) only | `probe_cli_sweeps` is "DISPLAY-ONLY evidence... it never gates a launch, a kill, or an exit" [VERIFIED: sweep_launcher.py:545-547] — gating on /proc would change that contract |

**Key insight:** Every deceptively complex piece (atomic state writes,
claim ledgers, worker loops, resume markers) already lives in
`pipeline/dispatch_core.py` — the TUI only READS its state file and COMPOSES
its argv. The reader and the composer are deliberately thin; complexity on
this side of the seam would duplicate frozen pipeline contracts.

## Common Pitfalls

### Pitfall 1: The frontier tick's empty-registry early return starves the G panel
**What goes wrong:** Riding the probe dispatch inside `_tick_frontier` means
no probe ever fires on an idle machine (no live roots).
**Why it happens:** `_tick_frontier` begins `if not self._live: return`
[VERIFIED: tui/screens/monitor.py:2302-2303 — `"""The 2s tick: dispatch ONE
frontier worker..."""` over `if not self._live:`].
**How to avoid:** Dispatch the gpu worker from a site that fires
unconditionally on the 2s cadence — either a dedicated
`set_interval(self._frontier_interval, self._tick_gpu)` stopped/re-armed in
`on_mount`/`on_unmount` beside the existing pair (:2145-2151, :2193-2197 —
the idempotent-mount discipline), or at the TOP of `_tick_frontier` before
the guard. The worker itself is its own exclusive group.
**Warning signs:** G panel shows first-paint skeleton forever on a machine
with zero runs; pty test of the idle monitor never sees lane rows.

### Pitfall 2: The LNC_SINGLE_GPU_BLOCKED amendment ripples through 8+ sites
**What goes wrong:** The constant currently formats ONLY `{roots}`
[VERIFIED: tui/strings.py:1557-1563, zh `"⚠ 单卡机器上已有训练任务在运行（{roots}）—
请等待完成、经退出门终止，或换一个结果目录"`]. The amended copy adds
`{workers}` and `{n}` (UI-SPEC Copywriting table). Every `.format(roots=...)`
call site must change in the same commit or the render raises KeyError.
**Why it happens:** In-place amendment changes the placeholder SET, not just
wording.
**How to avoid:** Lockstep-edit all sites, verified by grep this session:
  - `tui/screens/run_config.py:414` (`_problem_line` → `format(roots=detail)`)
  - `tui/screens/monitor.py:4685`, `:4852`, `:4955` (three refusal renders)
  - `tests/tui/test_pilot_run_config.py:1038` (`format(roots="/repo/finetuned-live")`)
  - `tests/tui/test_pilot_monitor.py:3522`, `:5223`
  The problem-tuple detail threading (currently `", ".join(blocked)` — plain
  roots) must carry the counts too (e.g. the detail becomes a structured
  value or the screen composes the params). Planner owns the exact shape.
**Warning signs:** KeyError: 'workers' at gate-refusal render; the pilot
gate tests red on the copy assertion.

### Pitfall 3: The zero-arg tolerant-getattr call sites constrain the predicate signature
**What goes wrong:** The replacement predicate needs requested-workers
context, but three pre-check sites call it with ZERO arguments through a
tolerant getattr: `blocked_getter = getattr(self._launcher,
"single_gpu_launch_blocked", None); blocked = (blocked_getter() if
blocked_getter is not None else None)` [VERIFIED: monitor.py:4679-4682 and
:4949-4952; the facade twin at tui/screens/run_config.py:383-390; the slot-4
gate at tui/screens/run_config.py:2049-2052].
**Why it happens:** EHC-3's predicate was context-free (count==1 AND live).
Multi-GPU capacity is not: Σ live demand + requested workers vs capacity.
**How to avoid:** Defaulted parameters keep every existing zero-arg call
valid — e.g. `def launch_blocked(self, requested_workers: int = 1,
dispatch: bool = False)` — where the monitor [r]/[e] paths (plain run_sweep
re-runs, 1 GPU, non-dispatch) and the facade pass through unchanged, and the
slot-4 path threads the spec's workers. Keep the OLD name or rename with the
fakes updated — `test_gate_fakes_without_the_single_gpu_seam_never_block`
(test_pilot_run_config.py:1047) deletes the method off a fake class and pins
that a seam-less launcher NEVER blocks; that tolerance must survive verbatim.
**Warning signs:** TypeError on the monitor re-run path; the 1047 test red.

### Pitfall 4: Registry-only capacity arithmetic (the honest boundary)
**What goes wrong:** Expecting the capacity stage to see CLI-launched live
sweeps. It cannot — `single_gpu_launch_blocked` reads `self.live_sweeps()`,
the TUI-owned registry; CLI-launched processes are visible only via
`probe_cli_sweeps`, which is pinned DISPLAY-ONLY: "it never gates a launch, a
kill, or an exit" [VERIFIED: sweep_launcher.py:545-547].
**Why it happens:** The monitor shows CLI runs as live cards (via /proc
evidence) — operators will assume the gate sees them too.
**How to avoid:** Accept and document the boundary (same as EHC-3 today): the
capacity stage counts REGISTRY entries only. Per-entry demand derives from
the stored `LiveSweep.argv` [VERIFIED: sweep_launcher.py:229-232 — `argv:
tuple[str, ...]` "the launch argv, verbatim"] — a `run_sweep_shard.py ...
--mode dispatch --workers N` entry demands N GPUs; a plain `run_sweep.py`
entry demands 1. The argv-parsing precedent is the launcher's own
`_plan_cache`/`live_sweep_plans` (built per-argv, sweep_launcher.py:701-705).
Do NOT widen the predicate to /proc without a maintainer ruling.
**Warning signs:** A test asserting refusal over a probed-but-unregistered
sweep; scope creep into T-uwr-01's contract.

### Pitfall 5: The pty byte-silence pin vs a real, fluctuating probe
**What goes wrong:** `test_monitor_quiet_cadence_is_byte_silent`
(tests/tui/test_pty_driver.py:478-507) drives the REAL app over a real pty
and asserts `child.before == drained` — ZERO terminal bytes across 2+
frontier ticks (5.5s). Once the G panel probes real nvidia-smi on the 2s
cadence, any genuine hardware fluctuation (a 1°C temperature drift, a
utilization blip) is LEGITIMATELY-changed data that writes bytes and fails
the pin on the dev box (CI has no nvidia-smi → stable absent state).
**Why it happens:** The pin predates any hardware-sourced render region.
**How to avoid:** (1) The G-panel signature must cover the FULL formatted row
text (probe-state + row count + per-row values) so UNCHANGED readings write
zero — mandatory regardless (UI-SPEC A rule 7). (2) Quantized display (int
percent, int MiB, int °C) already damps noise; idle 5090s read stably
(`0, 0, 2, 32607, 29` / `28` this session). (3) If flakiness appears, the
planner-owned fallback is a test-scoped probe override (e.g. an env var the
pty spawner sets forcing the absent state) — weigh it against adding an env
surface; the UI-SPEC does not sanction an operator-facing toggle.
**Warning signs:** Intermittent `the quiet cadence wrote N new bytes`
failures that only reproduce on the GPU box.

### Pitfall 6: The dispatch block breaking card cursor identity
**What goes wrong:** Dispatch rows rendered through a separate widget path
(not `_card_content`) drift from the in-place update path — cursor jumps,
structure rebuilds every tick.
**Why it happens:** The card has TWO render paths that share exactly one
builder; a third path violates the f0x law.
**How to avoid:** Dispatch lines join `_card_content`'s `lines` list
[VERIFIED: monitor.py:3414-3434 — strip first, resume note, then
matrix/tree]. The per-card structure signature (`_cards_signature`,
:2587) must gain the dispatch structure legs (has-block, worker count,
stale flag) so a worker-count CHANGE rebuilds while value-only changes ride
`_refresh_card_labels` (:3693 — "update ONLY the existing ListItem's Label
children in DOM order").
**Warning signs:** Cursor resets on the Running tab while a dispatch run
renders; full ListItem rebuild every 2s tick (flicker).

### Pitfall 7: gpus field semantics — the TUI mirror is deliberately NARROWER than the CLI
**What goes wrong:** Copying the CLI's verbatim-string --gpus contract into
the field validation, or vice versa expecting UUID support.
**Why it happens:** The shard CLI accepts "a decimal index, a GPU UUID, or a
MIG instance id... ARITY-validated only" [VERIFIED:
pipeline/run_sweep_shard.py:364-368, :484-494]; the TUI field pins
comma-separated non-negative INDICES (`0,1`) per UI-SPEC C.3
(`CFG_GPUS_INVALID_PROBLEM`). A UUID typed into the TUI is refused by the
mirror though the CLI would accept it.
**How to avoid:** Ship the documented asymmetry: the mirror is a cheap
pre-filter, the CLI authoritative (Pattern 7); the problem copy names the
accepted grammar. Arity (len(gpus) == workers) is the CLI's own
`--gpus arity mismatch` refusal (dispatch_core.py:2034-2038) — mirrored as
`workers_exceeds_gpus` when a typed list is SHORTER than workers.
**Warning signs:** Tests asserting UUID acceptance in the TUI field; or
weakening the CLI-side arity.

### Pitfall 8: Persisting a guessed GPU list
**What goes wrong:** Resolving `gpus=None` (all-detected) to a concrete list
at save/preview time and persisting it — a stale machine's list silently
pins a future launch.
**Why it happens:** It's tempting to make state files self-describing.
**How to avoid:** `gpus` persists as the tuple or None; resolution happens
at LAUNCH time only (UI-SPEC C.2: "None = all detected, resolved at LAUNCH
time, never persisted as a guessed value"). The defaults spec composes argv
WITHOUT the `--gpus` element (present-only parity, D-12 discipline —
`compose_argv`'s "An ABSENT flag contributes ZERO elements"
[VERIFIED: tui/services/run_config.py:1106-1108]). The preview renders
`GPUs all(2)` from the live detected count, explicitly a preview.
**Warning signs:** A saved state file containing a gpus list the operator
never typed.

### Pitfall 9: Golden regeneration discipline (the batch is NEW, not joined)
**What goes wrong:** Assuming the tree already carries uncommitted goldens
from #35/#39/#42 and stacking Phase-16 regens "onto" them.
**Why it happens:** The UI-SPEC says "this phase's regeneration joins that
same review batch" — but the ledger shows #35/#39/#42 status `fixed` and the
working tree is CLEAN this session [VERIFIED: `git status --short
tests/tui/__snapshots__/` empty; commits `b84afc0` "land monitor goldens...
maintainer-approved 2026-10-19" and `2bdcbad` "land D-03 goldens"].
**How to avoid:** Regenerate the four goldens (run_config, run_config_confirm
NEW, monitor_empty, monitor_running) via `make snapshot-update` (the ONLY
regen path, Makefile:132-133: `$(UV) run --group dev --group tui python
tests/tui/test_snapshots.py --regenerate`), leave UNCOMMITTED, open the new
WINDOWS deviation row naming the D-03 handoff. The committed tree will fail
the four golden tests until review lands — the documented #39 pattern.
**Warning signs:** Committing regenerated SVGs in the phase's code commits;
regenerating untouched screens' goldens (D16-13 forbids it).

### Pitfall 10: GPU-row fabrication in tests (CI zero-GPU)
**What goes wrong:** Any test lane invoking real nvidia-smi — flaky on CI
(binary absent, but PRESENT on the dev box → different bytes).
**Why it happens:** The real service's default runner is the subprocess.
**How to avoid:** Every gpu_probe unit test injects the runner; every golden
fabricates `GpuRow` dataclasses (frozen dataclasses are "trivially fakeable"
— UI-SPEC Goldens) through the constructor seam that joins
`MonitorScreen.__init__` / `_golden_app` (test_snapshots.py:751-764's
constructor-injection shape). The import lock (test_import_lock.py) covers
the new services automatically by glob [VERIFIED:
test_import_lock.py:41-46 — `files = sorted(SERVICES_DIR.glob("*.py"))`].
**Warning signs:** `subprocess` reaching nvidia-smi in any collected test; a
golden that renders different bytes on GPU vs GPU-less machines.

## Code Examples

### gpu_probe probe argv (verified live on the validation box, 2026-10-21)
```text
# Source: live probe this session (AutoDL 2×RTX 5090 box) + UI-SPEC D16-01
$ nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits
0, 0, 2, 32607, 29
1, 0, 2, 32607, 28
# → GpuRow(index=0, utilization_pct=0, memory_used_mib=2, memory_total_mib=32607, temperature_c=29)
# Exit 0; /usr/bin/nvidia-smi present. [VERIFIED: live probe]
```

### The stage-0 predicate being replaced (current EHC-3 semantics)
```python
# Source: tui/services/sweep_launcher.py:827-846 (VERIFIED, read this session)
def single_gpu_launch_blocked(self):
    """The EHC-3 single-GPU serialization predicate.

    True-blocking (returns the live roots) exactly when the
    EFFECTIVE GPU count is 1 AND at least one sweep is live in the
    registry: on a single-GPU machine a second concurrent sweep
    would contend for the one GPU. Count >= 2 (multi-GPU) and
    count 0 (torch/CUDA unavailable — the ruling's letter)
    are unrestricted; an idle registry is unrestricted.
    """
    count = (self._gpu_count if self._gpu_count is not None
             else effective_gpu_count())
    if count != 1:
        return None
    live = self.live_sweeps()
    return live if live else None
```
The service refusal ORDER stays byte-identical — `launch_spec` stage 0 fires
BEFORE the preview recompute (:898-902); `launch_from_failures` repeats the
same stage-0 (:1050). Only the predicate body changes.

### The gate chain's screen-side capacity stage slot (position byte-pinned)
```python
# Source: tui/screens/run_config.py:2042-2058 (VERIFIED) — the stage the
# multi-GPU predicate replaces, sitting AFTER the CR-02 live-root refusal
# (:2036-2041) and BEFORE the env preflight dispatch (:2059-2060).
# EHC-3 (261015-ehc ruling 3): the single-GPU serialization
# pre-check — beside the CR-02 live-root stage, BEFORE any env
# preflight or confirm: ...
blocked_getter = getattr(
    self._launcher, "single_gpu_launch_blocked", None)
blocked = (blocked_getter()
           if blocked_getter is not None else None)
if blocked:
    self._gate_active = False
    if not self.app.below_minimum_grid:
        self.push_screen(ProblemsModal(
            (("single_gpu_busy", ", ".join(blocked)),)))
    return
```

### The dispatch composer's frozen CLI surface (verified against the shard parser)
```python
# Source: pipeline/run_sweep_shard.py:351-410 + dispatch_core.py:2030-2085 (VERIFIED)
# Orchestrator-owned: --workers (int>=1), --gpus (comma ids, ARITY==workers),
#                     --models (REQUIRED in dispatch mode), --output-root,
#                     --mode {static,dispatch}, --dry-run, --merge/--cleanup/--yes/--rerun-failed
# Everything else = passthrough to run_sweep workers VERBATIM
#                   (--seeds REQUIRED by dispatch's remainder re-parse, --tasks,
#                    --peft, --config-variant, --curve, --subset_file, ...)
# Dispatch-mode specifics: --cleanup x dispatch refused (:1594-1599);
# --merge x dispatch refused (:1524); the "workers exceeds model count"
# refusal (:1678) is STATIC-mode-only — it sits after the dispatch return.
# compose shape (plan owns exact spelling/order; UI contract pins present-only):
 = [sys.executable, str(RUN_SWEEP_SHARD_SCRIPT),
        "--mode", "dispatch",
        "--workers", str(spec.workers),          # or present-only when 1 — plan-owned
        # "--gpus", "0,1",                      # PRESENT-ONLY (D-12 parity)
        "--models", ",".join(spec.models),
        "--output-root", _abs_against_repo_root(spec.output_root),
        "--tasks", ",".join(spec.tasks),         # + the pinned sweep-flag tail
        "--seeds", ",".join(str(s) for s in spec.seeds), ...]
```

### The dispatch_state snapshot invariant (the reader's honesty check)
```text
# Source: schemas/dispatch_state.json:4 $comment (VERIFIED, quoted verbatim)
"SNAPSHOT INVARIANT — holds at every observed write by construction:
counts.completed + counts.failed + counts.skipped + queue_depth +
(number of workers whose in_flight is non-null) == counts.total.
queue_depth is DERIVED (total - completed - failed - skipped -
active_workers), never len(pending)"
# Reader fields (all VERIFIED against the schema lines 39-123):
#   counts: {total, completed, failed, skipped}  — required integers >= 0
#   workers[]: {index, gpu:str, in_flight: cellKey|null, cells, completed, failed}
#   in_flight cellKey: {model:str, task:str, seed:int, fraction:number|null}
#   failures[]: {model, task, seed, fraction, finished_at}
#   top-level required: schema_version(2), mode("dispatch"), run_id, status,
#     started_at, updated_at, counts, queue_depth, workers, failures
#     (additionalProperties: false at every level)
```

### The G panel's TCSS pattern (existing precedents to copy verbatim)
```css
/* Source: tui/styles.tcss:337-339 (#dl-queue-region) and :102-104
   (#env-detail-log) — VERIFIED patterns this session */
#dl-queue-region {
    /* ... */
    border-top: solid $border;  /* 1-cell border exception — separator */
}
#env-detail-log {
    height: auto;
    max-height: 20;             /* scroll bound (not a spacing token) */
}
/* #mon-gpu block = separator + height:1 row tokens + padding: 0 2 status
   exception + height:auto; max-height:8 lane bound; theme tokens only;
   one comment block naming Phase 16. ZERO new TCSS for slot-4. */
```

### The strings insertion shapes
```python
# Source: tui/strings.py:68-90 (VERIFIED) — every new constant follows:
CONST = _t("CONST", "<zh>", "<en>")   # module-level typed assignment; the
# TypeVar keeps ty seeing the literal type; language-neutral values pass the
# same value twice (MON_GPU_ROW / MON_DISPATCH_WORKER_BUSY are identical
# zh/en data-forward rows per the UI-SPEC table).
# Block ends read this session: LNC_ block through ~:1600 (exit-confirm
# family), MON_ block ends at MON_FRACTION_LINE (:1942, file is 1943 lines).
# The 18 names + the amended LNC_SINGLE_GPU_BLOCKED extend
# test_strings_phase11.py's EXPECTED_CFG_/LNC_/MON_ CONSTANTS tuples
# (bidirectional — an unregistered new name FAILS the inventory).
```

## State of the Art

Not applicable — no external ecosystem movement this phase (frozen repo-local
stack: textual 8.2.8 pinned; the milestone research already covers the
design). The only externally-facing fact re-verified this session: the
nvidia-smi CSV query mode works as specified on current drivers (probe run
above).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The dispatch composer forwards `--tasks` in the passthrough family (tasks is NOT orchestrator-owned; only --models is) | Code Examples / composer | argv pin wrong; mitigated by the frozen shard parser read (parse_known_args remainder) — verify exact tail order at plan time against `run_sweep.build_argv` |
| A2 | `--workers 1` renders explicitly in the composed argv (the field carries a live value "1") rather than present-only omission | Code Examples | Either reading satisfies the CLI (default 1); plan owns the pin — if omitted, the [p] preview shows fewer elements |
| A3 | Idle-GPU probe values are stable enough for the pty byte-silence window on this hardware (0% util / fixed MiB / ±0°C over 5.5s observed) | Pitfall 5 | Intermittent dev-box flake; fallback options documented (signature gate is mandatory anyway) |
| A4 | The dispatch block and the existing resume-note interleave as strip → resume note → dispatch block (both `.mon-card-resume` family) | Surface B | Cosmetic ordering only; UI-SPEC pins "under the summary strip, above the matrix" — either interleave satisfies it |
| A5 | `run_config_confirm.svg` golden drives the `_GateConfirmModal` with a deterministic spec fixture (the D16-13 "config preview+confirm" wording maps to a NEW golden id alongside the existing 9) | Goldens | If the maintainer intended regenerating an existing confirm face instead, the delta is one test id |

All other claims in this research are `[VERIFIED: <path:lines>]` against
files read this session, or direct quotes from the ratified CONTEXT/UI-SPEC.

## Open Questions (RESOLVED — planner rulings: Q1(a) registry-only capacity arithmetic in 16-03; Q2(a) always-full panel + Q3(a) every-frontier-tick in 16-01; Q4 mandatory signature gate + escalation path in 16-01 Task 2)

1. **Multi-GPU capacity predicate** (UI-SPEC Open Q1 — recommendation (a))
   - What we know: stage position/vehicle/copy pinned; sanctioned shape N→N;
     the registry holds `LiveSweep.argv` per entry; `effective_gpu_count()`
     unchanged; /proc evidence is display-only.
   - What's unclear: the exact demand accounting for a live STATIC shard
     entry (a static `--workers 2` launch also holds 2 GPUs — does it count
     as 2?) and whether count-0 machines admit ANY dispatch launch
     unconditionally (the EHC-3 letter says unrestricted — carried over).
   - Recommendation: adopt (a) literally: refuse iff
     `Σ(live registry demand) + requested_workers > effective_gpu_count()`
     where demand = parsed `--workers` for shard argv (both modes), else 1
     for plain run_sweep argv; any live non-dispatch holder on a count-1
     machine is subsumed by the arithmetic (1 + 1 > 1). Zero-arg call sites
     read demand-only (requested=1). Extend the 1372/1399/1448 family with:
     within-capacity dispatch admits; over-capacity refuses naming roots +
     counts; static-demand counts; count-0 admits.

2. **G panel at the 80×24 floor** (UI-SPEC Open Q2 — recommendation (a))
   - What we know: 3-row cost (header + 2 lanes) at the floor; cards scroll;
     the min-size guard suppresses repaints beneath.
   - Recommendation: always-full panel (a). No threshold logic to test, no
     golden variance; revisit only on UAT crowding reports.

3. **G-panel cadence sharing** (UI-SPEC Open Q3 — recommendation (a))
   - What we know: D16-03 pins the 2s frontier class with ~2s per-call
     timeout; a read-only CSV query is cheap; Pitfall 1 forces an
     unconditional dispatch site anyway.
   - Recommendation: every frontier tick (2s) via the dedicated `mon-gpu`
     worker. If the maintainer prefers 4s, the mechanism is identical —
     tick every 2nd frontier pass; make it a one-line constant.

4. **Discovered this session — the pty byte-silence exposure** (Pitfall 5)
   - What we know: the pin asserts byte-identity over the REAL app on real
     hardware; the G panel is the first hardware-sourced region.
   - Recommendation: land the airtight signature gate; run the pty lane on
     the idle box; if flaky, escalate the env-override option to the
     maintainer rather than silently weakening the pin (D16-14: zero
     weakening).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| nvidia-smi | gpu_probe (runtime only — never in tests) | ✓ (dev box) | `/usr/bin/nvidia-smi`, exit 0, 2 GPUs | Honest 未安装 degradation (D16-02) — the designed CI state |
| Python (repo venv) | all lanes | ✓ | 3.13.14 | — |
| textual | screens/goldens | ✓ | 8.2.8 (uv.lock) | — |
| uv | snapshot-update / lanes | ✓ | per repo bootstrap | — |
| GitHub Actions GPU | — | ✗ (by design) | — | Injected seams + fabricated fixtures (D16-14); zero-GPU is a binding constraint, not a gap |

**Missing dependencies with no fallback:** none.

**Missing dependencies with fallback:** CI lacks nvidia-smi — the absent
state IS a first-class render (MON_GPU_ABSENT); the monitor_empty golden may
legitimately fixture either the absent shape or fabricated rows (UI-SPEC
goldens table allows both; pick one and pin it).

## Security Domain

`security_enforcement: true`, ASVS level 1 (config). This phase adds no
network surface, no auth, no crypto. Applicable categories:

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (local console app) |
| V3 Session Management | no | — |
| V4 Access Control | no | — (no privilege change; the gate chain is the existing control) |
| V5 Input Validation | yes | Field mirrors are collect-all server-of-truth-validated (the shard CLI re-validates everything — defense in depth); JSON readers are stdlib `json` only, shape-tolerant, never `eval` |
| V6 Cryptography | no | — |
| V12 File Handling | yes (local) | Reads are read-only + tolerant (None sentinel); writes ride existing `settings.atomic_write`; the launcher writes only through the frozen `_spawn` seams |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Command injection via probe argv | Tampering | The nvidia-smi argv is a FIXED list of literals — no operator input reaches the subprocess (list argv, never `shell=True`; the `_default_spawner` discipline). Workers/gpus FIELD values never compose into the probe |
| Malicious/half-written dispatch_state.json | Tampering | stdlib `json` parse → typed dataclasses with per-field tolerance; malformed values render verbatim or degrade to the stale marker — never executed, never reconciled; a damaged file reads None (block absent) |
| nvidia-smi output spoofing/partial parse | Spoofing | Strict per-field `int()` coercion; ONE malformed line degrades the WHOLE probe to absent (never partial rows); fixed units from the query — no runtime unit parsing |
| Launch-gate bypass via screen state | Elevation | The service `launch_spec` re-proves every stage FRESH (preview, keys, phrase, capacity) — no widget path reaches `_spawn` for a refused spec (T-11-03); the screen pre-checks are UX, the service is the boundary |
| Registry-key confusion (root basis) | Tampering | The spawn key rides `rc.resolve_dirs(spec).output_root_abs` (the REPO_ROOT basis) — carry this discipline into the dispatch composer unchanged [VERIFIED: sweep_launcher.py:875-883] |

## Sources

### Primary (HIGH confidence — read from live code this session)
- `tui/services/sweep_launcher.py` — effective_gpu_count (:175-210), single_gpu_launch_blocked (:827-846), launch_spec refusal order (:848-921), launch_from_failures stage-0 (:1050-1052), _spawn/O_EXCL tee (:709-823), GateSummary/GateRefusal (:277-327), gate_confirm_data (:444-486), LiveSweep.argv (:229-232), probe_cli_sweeps display-only (:540-560)
- `tui/services/run_config.py` — RunSpec (:184-249), problem codes/param keys (:158-177), parse_params (:329-387), _persist_payload (:453-479), _spec_from_doc (:560-624), load_state/SCHEMA_VERSION=1 (:663-692), preview (:878-924), compose_argv present-only tail (:1095-1164)
- `tui/screens/run_config.py` — LauncherBackend facade (:310-390), _problem_line (:393-415), E2PhraseModal compose (:704-758), _GateConfirmModal (:861-907), params pane compose / EBS row / DIRS title (:1232-1310), _compose_spec (:1639-1668), gate chain (:1983-2197), EHC-3 slot (:2042-2058)
- `tui/screens/monitor.py` — _strip_bar (:527-558), MonitorSession (:1598-1652), compose (:2077-2107), on_mount cadence+sentinels (:2109-2181), mon-full/mon-frontier workers (:2254-2330), _render_all modal suppression (:2924-2945), tabs gate (:2965-2998), _cards_signature (:2587), _card_content (:3385-3434), _refresh_card_labels (:3693), EHC-3 sites (:4673-4688, :4846-4854, :4946-4958)
- `tui/services/env_check.py` — the injectable-kernel service pattern + artifact_loader None sentinel (:81-95, :126-238)
- `tui/services/sweep_monitor.py` — STALE_GRACE_SECONDS=600.0 (:127), scanner dataclasses (:186-353), full_scan/frontier_scan (:572-735)
- `tui/strings.py` — `_t` (:68-90), LNC_SINGLE_GPU_BLOCKED (:1557-1563), block layout (CFG 53 / LNC 23 / MON 79 constants)
- `tui/styles.tcss` — token contract (:8-27), separator/border-top patterns (:64-65, :337-339, :404-406), max-height scroll bounds (:102-104, :220-225)
- `schemas/dispatch_state.json` — frozen v2, all fields + snapshot invariant (full read)
- `pipeline/run_sweep_shard.py` — CLI surface (:321-481), dispatch routing (:1619-1627), static validations (:1628-1693)
- `pipeline/dispatch_core.py` — run_dispatch validation (:1982-2091), state/ledger names (:134-165)
- `tests/tui/` — test_import_lock.py (AST glob :41-46), test_snapshots.py (fallback lane, `_golden_app` :751-764, `_frozen_mon_clock` :722-748, corpus table), test_strings_phase11.py (bidirectional inventory), test_pilot_run_config.py (:1015-1071), test_pilot_monitor.py, test_services_sweep_launcher.py (:1292-1357, :1372-1448), test_pty_driver.py (:478-507)
- `Makefile` — snapshot-update (:132-133)
- Live probes this session: nvidia-smi CSV query (2 GPUs, exit 0); venv `textual 8.2.8` / Python 3.13.14; `git status tests/tui/__snapshots__/` clean; WINDOWS.md #35/#39/#42 = fixed

### Secondary (MEDIUM confidence — ratified planning artifacts)
- `.planning/phases/16-tui-multi-gpu-surface/16-CONTEXT.md` (D16-01..D16-15)
- `.planning/phases/16-tui-multi-gpu-surface/16-UI-SPEC.md` (approved design contract; open questions 1-3)
- `.planning/research/ARCHITECTURE.md` §D (design backbone, HIGH per its own header)
- `.planning/STATE.md` (10-04 worker-group lesson, 08-06 protocol seam, 12-03 golden fallback lane, textual 8.2.8 probe pins)

### Tertiary (LOW confidence)
- None. No `[ASSUMED]` external claims remain; see Assumptions Log A1-A5 for plan-owned pins.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — nothing new; every version verified in the repo venv
- Architecture: HIGH — every mount point, seam, and pattern cited to lines read this session; the milestone research agrees
- Pitfalls: HIGH — each verified against the exact code (the early-return guard, the zero-arg getattr sites, the byte-silence pin, the clean golden tree)

**Research date:** 2026-10-21
**Valid until:** 2026-11-21 (repo-local frozen stack; re-verify only if textual or the shard CLI move before planning lands)
