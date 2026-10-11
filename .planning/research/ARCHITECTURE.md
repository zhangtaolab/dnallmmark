# Architecture Research

**Domain:** Textual TUI console layered onto an existing subprocess-based sweep orchestration platform (brownfield integration — v1.2 TUI任务)
**Researched:** 2026-10-11
**Confidence:** HIGH for repo facts (verified by direct inspection of `pipeline/run_sweep.py`, `pipeline/run_finetune.py`, `pipeline/env_smoke.py`, `pyproject.toml`, `tests/conftest.py`, `docs/TUI-REQUIREMENTS.md` at autorun HEAD) and for Textual API facts (official textualize.io docs fetched 2026-10-11); MEDIUM for Textual version status and ModelScope CLI flag details (secondary sources)

## Standard Architecture

The TUI does **not** become part of the sweep. It is a **read-plan-launch-observe shell** around an execution model that already exists and must not change: `run_sweep.py` enumerates the matrix and spawns one `run_finetune.py` subprocess per cell; all durable state lands on the filesystem (per-cell `run_record.json`, resume markers, end-of-run manifests). The TUI's job is to make that filesystem state visible and the launch safe — nothing more.

Three facts from the existing code anchor every design decision below:

1. **The filesystem is the progress API.** `run_matrix()` writes `run_record.json` per cell *inside* the loop (`run_sweep.py:1144-1154`), but `sweep_manifest.json` and `sweep_failures.json` only *after* the loop (`run_sweep.py:1163-1169`). `run_sweep.py` prints almost nothing per cell. So live cell status lives exclusively in per-cell `run_record.json` files as they appear — the manifests are post-run audit artifacts, not live feeds.
2. **Child logs flow through run_sweep's stdout.** `launch_subprocess()` uses `subprocess.run(argv, cwd=PIPELINE_DIR, check=True)` with **no capture** (`run_sweep.py:872-876`) — every `run_finetune.py` child inherits run_sweep's stdout/stderr. A TUI that pipes run_sweep's stdout therefore receives the interleaved live training logs for free, with zero pipeline changes.
3. **Planning functions are pure and importable.** `enumerate_matrix`, `apply_priority_order`, `cell_dir_for`, `parse_curve_fractions`, `load_priority_tiers`, `load_failure_pairs` are stdlib-only, read-only, side-effect-free (`run_sweep.py:333-812`) — already imported headless by `tests/test_sweep.py` via the conftest `sys.path` seam (`tests/conftest.py`). The TUI can compute the exact planned cell list for preview **without launching anything**, guaranteed in parity with the subprocess because it is the same code.

### System Overview

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                    TUI PRESENTATION LAYER (new — textual)                  │
│  Screens: Selection · DataManager · RunConfig · Monitor · Modal gates      │
│  (App = composition root only; reactive dashboard state; Pilot-testable)   │
├────────────────────────────────────────────────────────────────────────────┤
│                    TUI SERVICE LAYER (new — NO textual imports)            │
│  registries · sweep_plan · launcher · monitor · downloads ·                │
│  settings · templates · env_gate                                           │
│  (pure Python + stdlib + run_sweep imports; constructor-injected fakes;    │
│   unit-tested headless like tests/test_sweep.py)                           │
├───────────────┬─────────────────────────────┬──────────────────────────────┤
│  PROCESS      │        PROCESS SEAM         │  CONFIG STATE (new)          │
│  BOUNDARY     │  asyncio.create_subprocess_ │  ~/.config/dnallmmark/       │
│               │  exec(argv LIST, cwd, env,  │    settings.json             │
│  run_sweep.py │  start_new_session=True)    │    templates/*.json          │
│  env_smoke.py │  stdout streamed → log tail │    downloads.json (queue)    │
│  modelscope   │  terminate() / detach       │  (XDG; injectable root path) │
│  audit_n_freq │                              │                              │
├───────────────┴─────────────────────────────┴──────────────────────────────┤
│                EXISTING PIPELINE (UNCHANGED CONTRACTS)                     │
│  run_sweep.py → run_finetune.py subprocess per cell (argv LIST, cwd=pwd)   │
├────────────────────────────────────────────────────────────────────────────┤
│                FILESYSTEM — THE INTEGRATION BUS (existing)                 │
│  {output_root}/{model}/{task}/seed_{s}/[frac_{f}/]                         │
│    run_record.json (per cell, as-finished) · trainer_state.json (marker)   │
│    final_metrics.json · sweep_manifest.json + sweep_failures.json (at end) │
│  pipeline/{models_info,datasets_info}.json · n_audit.json ·                │
│  eval_subsets.json · sweep_priorities.json · pipeline/datasets/            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `tui/app.py` | Composition root: build services, own shared reactives, MODES wiring, key bindings | Textual `App` — no business logic |
| `screens/selection.py` | 62×50 matrix view, filters (arena/type/species/size), preset groups, presence column | `DataTable` with row keys = model names, `update_cell` for status |
| `screens/data_manager.py` | Presence audit view, download queue UI, row-count reconciliation | `DataTable` + queue `ListView` |
| `screens/run_config.py` | Seeds/PEFT/variant/curve/subset/epochs/effective-batch form, dry-run preview, directory settings | Input/Select/Toggle widgets → `RunSpec` dataclass |
| `screens/monitor.py` | Cell dashboard, progress counts, failure list, log tail, resume states | `DataTable` + `RichLog` + reactive counters |
| `screens/modals.py` | E2' full-sweep confirm gate, exit-with-running-sweep prompt | `ModalScreen[bool]` + `dismiss()` |
| `services/sweep_plan.py` | Wrap `run_sweep` pure functions: enumerate, priority tiers, planned-cell preview, argv construction for display | thin import wrapper (stdlib-only) |
| `services/launcher.py` | Spawn/track run_sweep (and env_smoke) subprocesses; stream stdout; terminate or detach on exit | async `@work` worker + `asyncio.create_subprocess_exec` |
| `services/monitor.py` | Poll output_root frontier; derive per-cell + aggregate state from run_record/marker files | pure functions + `set_interval` tick |
| `services/downloads.py` | Persistent queue state machine; drive `modelscope` CLI per dataset; verify post-download | subprocess + JSON queue file |
| `services/settings.py` | Load/save XDG config; project-root vs storage-root resolution | stdlib json + injectable base path |
| `services/templates.py` | Run-config template import/export/validation (shareable JSON) | schema-validated (jsonschema, dev group) |
| `services/env_gate.py` | Run `env_smoke.py`, parse `PASS:`/`FAIL:` lines, block launch on FAIL | subprocess + line parsing |

## Recommended Project Structure

Follows repo convention: `script/`, `pipeline/`, `baseline/` are sys.path roots, not installable packages (`pyproject.toml` `package = false`; `tests/conftest.py` inserts `pipeline/`). The TUI is the same shape — a directory importable from repo root, run via `python -m tui`:

```text
tui/
├── __init__.py
├── __main__.py            # entry: python -m tui  (resolves REPO_ROOT itself)
├── app.py                 # DnallmMarkTui(App) — composition root ONLY
├── styles.tcss            # Textual CSS (single file to start)
├── screens/
│   ├── __init__.py
│   ├── selection.py       # model×dataset matrix (MODES["select"])
│   ├── data_manager.py    # presence + downloads (MODES["data"])
│   ├── run_config.py      # run parameters + preview (MODES["run"])
│   ├── monitor.py         # sweep dashboard (MODES["monitor"])
│   └── modals.py          # ModalScreen gates (E2', exit, from-failures confirm)
├── services/              # ZERO textual imports (typing-only if ever needed)
│   ├── __init__.py
│   ├── registries.py      # models_info/datasets_info/n_audit/eval_subsets readers
│   ├── sweep_plan.py      # wraps run_sweep pure functions + preview argv
│   ├── launcher.py        # SweepProcess: spawn/stream/terminate/detach
│   ├── monitor.py         # filesystem state derivation (frontier scan)
│   ├── settings.py        # XDG settings + directory resolution
│   ├── templates.py       # run-config template IO + validation
│   ├── downloads.py       # queue state machine + modelscope CLI driver
│   └── env_gate.py        # env_smoke runner + PASS/FAIL parser
└── events.py              # frozen dataclass ServiceEvent union (services → app)
tests/tui/                 # tier 1: headless service tests (no textual)
                          # tier 2: Pilot tests (textual, fake services injected)
```

### Structure Rationale

- **`services/` textual-free is the load-bearing rule.** It is what makes CI-side unit testing possible without the TUI runtime, mirrors the existing `tests/test_sweep.py` fake-executor discipline (D-05), and keeps ty/ruff coverage uniform. Enforce with an import-linter-style test: `assert no module in tui/services imports textual` (a 5-line test — no new dependency).
- **`screens/` get everything through constructor injection.** `MonitorScreen(monitor=FakeMonitor())` is what makes Pilot tests deterministic and fast; screens never construct services themselves — `app.py` does.
- **`python -m tui` (not a script path)** avoids the CWD-sensitivity trap that the two legacy `script/` tools document (`summarize_comparison.py` must run from `dnallm-mark/data/`). `__main__.py` resolves REPO_ROOT from `__file__` and never trusts CWD.

## Architectural Patterns

### Pattern 1: Subprocess launch + in-process import of pure planning functions (dual-use)

**What:** Execution always goes through `python pipeline/run_sweep.py <argv LIST>` as a subprocess. Planning/preview imports the same module's pure functions.

**When to use:** Always for this codebase.

**Trade-offs:** Subprocess gives crash isolation (TUI hang/death never kills a multi-day sweep), clean cancel semantics (`Process.terminate()`), the identical argv a maintainer would type by hand (the TUI-REQUIREMENTS "same entry as smoke→E2'" requirement), and a natural multi-GPU generalization (N subprocesses). Cost: no in-memory progress callbacks — solved by Pattern 2. Importing `run_matrix` in-process instead would block Textual's event loop for hours, entangle TUI crashes with sweep fate, conflict with SIGINT handling, and fork GPU-adjacent state into the console process — rejected.

**Example:**
```python
# services/sweep_plan.py — preview WITHOUT launching (parity by construction)
import run_sweep  # pure import; conftest-proven pattern (tests/conftest.py)

def preview_cells(spec: RunSpec) -> list[Cell]:
    cells = run_sweep.enumerate_matrix(
        spec.models, spec.tasks, spec.seeds, REPO_ROOT / "pipeline",
        peft=spec.peft, fractions=spec.curve_fractions)
    if spec.priority_tiers:
        cells = run_sweep.apply_priority_order(cells, spec.priority_tiers)
    return cells  # count, order, and planned dirs for the preview pane

# services/launcher.py — execution ALWAYS a subprocess
argv = [sys.executable, str(REPO_ROOT / "pipeline" / "run_sweep.py"),
        "--models", ",".join(spec.models), "--tasks", ",".join(spec.tasks),
        "--seeds", ",".join(map(str, spec.seeds)),
        "--output-root", str(spec.output_root), ...]
proc = await asyncio.create_subprocess_exec(
    *argv, cwd=REPO_ROOT, stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.STDOUT, start_new_session=True,
    env={**os.environ, "PYTHONUNBUFFERED": "1",
         "CUDA_VISIBLE_DEVICES": spec.gpu})
```

**Details that matter (repo-verified):**
- `PYTHONUNBUFFERED=1` is mandatory — piped Python children are block-buffered otherwise; the log tail would lag by kilobytes.
- `start_new_session=True` detaches the sweep from the TUI's session: it survives TUI exit (detach) and ignores terminal-originated SIGHUP, while the retained `Process` object still allows explicit `terminate()`.
- argv is built as a LIST, never a shell string — same T-03-10 discipline run_sweep itself follows.
- `--registry-dir` exists on run_sweep if the TUI ever reads non-default registries; `--output-root` is resolved absolute by run_sweep itself.

### Pattern 2: Filesystem-as-API monitoring — poll the frontier, stream stdout only for logs

**What:** The monitor derives state by stat-reading the output tree against the planned cell list; the subprocess stdout stream feeds only the log-tail pane.

**When to use:** Any long-running child whose durable state is on disk — exactly this repo.

**Trade-offs:** Polling is deterministic, Pilot-testable (fixture trees in `tmp_path`, injectable interval), correct over SSH/network mounts, and works for sweeps the TUI did **not** launch (attach to any output_root — even a CLI-started sweep — because state is read from disk, not from a process handle). Cost: a tick interval; bounded below.

**Repo-grounded signal map:**

| Signal | File | Written | Meaning |
|--------|------|---------|---------|
| Cell finished (any status) | `run_record.json` in cell dir | per cell, inside loop (`run_sweep.py:1144`) | status: completed/failed/skipped + metrics + timings |
| Cell in-flight | cell dir exists, no `run_record.json` | dir created just before executor (`run_sweep.py:1075`) | current cell |
| Cell trained (resume marker) | `trainer_state.json` | by run_finetune | skip-on-resume eligibility |
| Training produced metrics | `final_metrics.json` | by run_finetune | CR-02 failure signal when missing |
| Sweep over | `sweep_manifest.json`, `sweep_failures.json` | AFTER loop (`run_sweep.py:1163-1169`) | authoritative final report only |

**Refresh cadence under Textual's asyncio loop:** one `set_interval` timer at **2 s** (setting, not constant) driving an async callback. Cost control at 9,300 cells (62×50×3 full sweep): per tick, stat only the **frontier** — the first K unresolved cells in planned order plus a periodic full rescan (every ~60 s and on process exit) to absorb out-of-order completion (priority tiers reorder execution). A full planned-order rescan is ~9,300 `stat` calls ≈ 10 ms — harmless, but the frontier scan keeps the common tick at microseconds. Pause the timer on `ScreenSuspend` when the monitor screen is hidden. Log lines are NOT polled — they arrive event-driven via `async for line in proc.stdout` in the launcher's async worker; the launcher forwards them to the app via a thread-safe post (worker → reactive update).

**Do not** use Textual filesystem-watch APIs: no watcher API is documented in current Textual (only `watch_css` for CSS hot-reload); `set_interval` polling is the documented, testable mechanism (LOW-confidence leads on watcher APIs were not verifiable — treat as unavailable).

### Pattern 3: Headless services with injectable seams

**What:** Every service is a plain class taking its collaborators and an event sink through the constructor; screens take services through the constructor; only `app.py` wires real implementations.

**When to use:** Any Textual app that must be CI-tested — here mandated by "TUI tests CPU-side with injectable seams" (PROJECT.md Constraints).

**Trade-offs:** Slightly more wiring code; buys the two-tier test strategy that keeps CI GPU/dnallm-free and lets service logic run under plain pytest without textual installed.

**Example:**
```python
# tests/tui/test_monitor.py — tier 1, no textual, CI-safe
def test_frontier_derives_in_flight_cell(tmp_path):
    root = make_fixture_tree(tmp_path, cells=[("m1", "t1", 42, "completed")],
                             planned=[("m1", "t1", 42), ("m1", "t1", 43)])
    state = MonitorService(root, planned=...).scan()
    assert state.counts == {"completed": 1, "pending": 1}
    assert state.current_cell == ("m1", "t1", 43)

# tests/tui/test_pilot_monitor.py — tier 2, textual, fake service
async def test_monitor_renders_records():
    app = DnallmMarkTui(monitor=FakeMonitor(fixed_state))
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.query_one("#counts", Static).content # ...
```

Tier 2 runs under pytest-asyncio (`asyncio_mode = "auto"` per Textual's documented integration) with textual from a new `tui` uv group — CPU-only, satisfying the GPU/dnallm-free CI constraint. The unchecked requirement "CI 不引入 GPU/TUI 运行时" should be resolved at discuss: recommendation is to run tier-2 in CI as a separate job (`uv run --group tui pytest tests/tui -m pilot`) because textual is a small pure-Python install and Pilot tests are the only automated UI regression net; the strict-local-only fallback is a pytest marker if the team prefers.

### Pattern 4: XDG config state — user-local, never repo-local

**What:** All TUI persistent state lives under `$XDG_CONFIG_HOME/dnallmmark/` (default `~/.config/dnallmmark/`), path resolved by a hand-rolled ~10-line helper with an injectable override for tests.

**Schema:**
```jsonc
// ~/.config/dnallmmark/settings.json  (written atomically: tmp+rename)
{
  "settings_version": 1,
  "project_root": "/home/forrest/Github/dnallmmark",   // repo location: registries, scripts
  "storage": {
    "output_root": null,     // null = repo default ./finetuned (resolved absolute at launch)
    "cache_dir": null        // null = run_finetune default
  },
  "monitor": {"poll_seconds": 2.0},
  "defaults": {"seeds": [42, 43, 44], "peft": "none", "effective_batch": 16}
}

// ~/.config/dnallmmark/templates/<name>.json — the shareable run template
{
  "template_version": 1,
  "name": "tier1-e2e-smoke",
  "models": ["plant-dnamamba-6mer"], "tasks": ["GUE__emp_H3"],
  "seeds": [42], "peft": "none", "curve": null, "config_variant": null,
  "subset_file": true, "effective_batch": 16, "num_train_epochs": 1,
  "priority_tiers": [["plant-dnamamba-6mer"], ["GENERanno-eukaryote-0.5b-base"]]
}
```

**Rationale:** operator state is per-machine, so repo-local is wrong (would dirty the checkout and leak machine paths into git); hand-rolled XDG resolution avoids adding `platformdirs` for ~10 lines, consistent with the repo's minimal-dependency discipline. Templates are user-local between sessions but **import/export to arbitrary paths** as shareable artifacts (the requirement), validated against a JSON Schema committed under `schemas/` — reusing the repo's existing schema-validation pattern (jsonschema already in the dev group). `priority_tiers` mirrors `sweep_priorities.json`'s tier structure so a template converts to a `--priority-file` by writing the tiers array verbatim; the TUI writes that temp file under its config dir (never into the repo).

### Pattern 5: Download manager — CLI subprocess + persisted queue state machine

**What:** One `modelscope download --dataset <ns/name> --local_dir <dst>` subprocess at a time, driven by a JSON queue file that survives restarts.

**When to use:** The repo has already validated the CLI channel at 50/50 coverage (TUI-REQUIREMENTS §2); the CLI is an external prerequisite checked with `shutil.which("modelscope")` at startup — the TUI itself adds **no** modelscope dependency.

**Trade-offs vs alternatives:** SDK-in-thread couples a heavy import tree and a hung transfer to the TUI process, and can't be killed without killing the thread; raw-HTTP async re-implements auth/resume that the CLI already handles. The CLI subprocess gets crash isolation, trivial kill/restart, and resume for free (re-running the command continues partial downloads; flag details MEDIUM confidence — verified behavior should be confirmed in phase). Keep the raw HTTP API (`/api/v1/datasets/{ns}/{name}/repo?FilePath=...`) as the documented fallback channel, not a second implementation.

**Queue file** (`~/.config/dnallmmark/downloads.json`): entries `{task, ns_name, local_dir, status: pending|running|done|failed, attempts, last_error, verified: bool}` — rewritten atomically on every transition; on TUI start, `running` entries reset to `pending` (resume = re-enqueue; the CLI's own resume makes re-download cheap). Destination dirs come from `datasets_info.json` `Dataset_path` joined to the project root — datasets must land exactly where `run_finetune.py:973` expects (`base_dir + Dataset_path`). Post-download **verification** reuses `script/audit_n_frequencies.py` (the authoritative row-count tool) as a subprocess, then reloads `n_audit.json` — reuse, not re-implementation; a light pre-check (dir exists, expected file count) gates the full audit. Mind the documented double-nesting zip gotcha (run_sweep module docstring "FUTURE E2E note"): a freshly unzipped suite extracts as `suite-name/suite-name/...` and must be flattened before `Dataset_path` resolves — the verifier should detect and report this specifically.

### Pattern 6: Directory settings — pass-through today, threading gaps inventoried explicitly

**What:** The TUI resolves every path absolute and passes it via existing script flags; it never changes script assumptions (the requirement's own rule: 需统一传参而非改脚本假设).

**Support matrix (repo-verified):**

| Setting | Flag that carries it | Status |
|---------|---------------------|--------|
| Output root | `run_sweep --output-root` (resolved absolute internally) | supported today |
| Registry dir | `run_sweep --registry-dir` | supported today (run_finetune still reads its own dir — fine, TUI reads registries itself) |
| Model cache | `run_finetune --cache_dir` | **not threaded through run_sweep argv** |
| Datasets root | none — `run_finetune.py:672-673,973` hard-joins `base_dir + Dataset_path` | **not redirectable without pipeline change — out of scope; datasets live under the repo checkout** |
| Models root | none — `run_finetune.py:922` `base_dir + Model_path` | same — repo checkout |

Consequence: the "project directory / storage directory" split is realized as **project_root** (where the repo lives — basis for registries, scripts, and by default datasets/models) plus **storage.output_root** (fully supported) and **storage.cache_dir** (needs one small threading addition). Redirecting datasets/models outside the repo would violate the no-contract-change constraint and is documented as out of scope for v1.2.

**Sanctioned small run_sweep threading additions** (each follows the established append-as-separate-LIST-elements pattern in `build_argv`, byte-identical when absent, argv-shape asserted in `tests/test_sweep.py` — the same pattern `--peft`/`--train_fraction` already established):

| Addition | Status in repo docs | Size |
|----------|--------------------|------|
| `--subset_file` pass-through | already inventoried as "the one known pre-launch gap" (PROJECT.md Context) | ~15 lines |
| `--effective-batch` → child `--effective_batch_size` | PROJECT.md Key Decision (auto-GA, GA=max(1, N//batch), default 16) — Pending | small |
| `--num_train_epochs` pass-through | run_finetune flag exists (`run_finetune.py:210`); TUI "1-epoch smoke fast path" needs it for sweeps | small |
| `--cache_dir` pass-through | run_finetune flag exists (`run_finetune.py:137`) | small, optional |

These are the ONLY pipeline-file modifications the TUI milestone needs on `run_sweep.py`, and they extend its contract additively — the TUI never bypasses run_sweep to reach run_finetune directly for sweeps.

## Data Flow

### Launch Flow (single GPU)

```text
[RunConfig screen] -- RunSpec dataclass -->
[env_gate] -- subprocess env_smoke.py, parse PASS:/FAIL: -- FAIL? --> modal, BLOCK launch
[E2' gate] -- is_full_e2e_sweep(preview) ? ModalScreen[bool] typed confirm --> abort | continue
[launcher] -- asyncio.create_subprocess_exec(run_sweep argv LIST,
              cwd=REPO_ROOT, PYTHONUNBUFFERED=1, CUDA_VISIBLE_DEVICES=<dev>,
              start_new_session=True) --> Process handle
[App] switch_mode("monitor")
```

### Monitoring Flow

```text
set_interval(2s) → [monitor.scan(output_root, planned_cells)]
   frontier stats: run_record.json (status) · trainer_state.json (marker)
   final_metrics.json presence · periodic full rescan (60s)
        ↓ frozen ServiceEvent
[App reactives] --data_bind--> [counts/progress widgets]
                    └--> [DataTable rows: update_cell(row_key, "status", ...)]
[launcher worker] async-for line in proc.stdout → [RichLog tail pane]
process exit → read sweep_manifest.json + sweep_failures.json → final report
     failures present → [from-failures re-run] button pre-fills RunSpec
         (--from-failures <path> — flag already exists, run_sweep.py:293)
```

### Download Flow

```text
[DataManager screen] presence = n_audit.json × datasets_info.json (missing flags)
[enqueue missing] → downloads.json (atomic write) → worker: one modelscope CLI
   subprocess at a time → stdout stream → progress line → on exit:
[verify] audit_n_frequencies.py subprocess → reload n_audit.json →
   row-count mismatch? mark entry failed with diff shown; nesting issue? named hint
```

## Anti-Patterns

### Anti-Pattern 1: Importing run_matrix to drive the sweep in-process

**What people do:** `import run_sweep; run_sweep.run_matrix(...)` inside a Textual thread worker to get "real" callbacks.
**Why it's wrong:** hours-long synchronous loop in the console process; TUI crash kills a multi-day sweep; no clean cancel; SIGINT/Ctrl-C semantics fight between Textual and the child; breaks "TUI launch = same entrypoint as CLI".
**Do this instead:** subprocess launch (Pattern 1); import ONLY the pure planning functions.

### Anti-Pattern 2: Treating manifests as live progress

**What people do:** poll `sweep_failures.json`/`sweep_manifest.json` mtime for the dashboard.
**Why it's wrong:** both are written once, AFTER the loop (`run_sweep.py:1163-1169`) — the dashboard would show nothing for days, then everything.
**Do this instead:** per-cell `run_record.json` as it appears; manifests are the final report read on process exit.

### Anti-Pattern 3: Dry-run against the real output root for preview

**What people do:** run `run_sweep.py --dry-run --output-root ./finetuned` to count cells.
**Why it's wrong:** dry-run writes `sweep_manifest.json` into that root — clobbering a previous real run's authoritative manifest (contradictory audit artifacts, the exact WR-06 class of hazard the driver was hardened against).
**Do this instead:** import `enumerate_matrix`/`apply_priority_order` for preview (no disk writes at all).

### Anti-Pattern 4: Parsing child log text as state

**What people do:** regex the training stdout for "epoch 3" to compute progress.
**Why it's wrong:** log format belongs to dnallm/HF Trainer and changes upstream; tqdm `\r` progress spam pollutes parsing; the durable truth is already on disk.
**Do this instead:** logs are for the human tail pane (RichLog handles `\r`); state comes from files. Also expect HF Trainer progress-bar spam in the tail — filter or tolerate, never parse.

### Anti-Pattern 5: Re-implementing enumeration/aggregation in the TUI

**What people do:** a fresh "models × tasks × seeds" counter in `tui/` "because it's easy".
**Why it's wrong:** drifts from run_sweep semantics (peft aliasing, curve expansion, priority composition) — the preview would lie about the real run.
**Do this instead:** wrap `run_sweep` functions (Pattern 1); drift is impossible by construction.

### Anti-Pattern 6: Business logic inside screens/App

**What people do:** cell-state derivation, template validation, queue transitions written as widget methods.
**Why it's wrong:** untestable without textual; Pilot tests become the only tests; CI story collapses.
**Do this instead:** services own logic; screens render (Pattern 3); add the import-linter test pinning `tui/services` textual-free.

### Anti-Pattern 7: Killing the sweep on TUI exit by default

**What people do:** nothing — app exit cancels workers, orphaned child dies with the session.
**Why it's wrong:** a sanctioned multi-day E2'-adjacent sweep should not die because the operator closed the console; conversely silently leaking GPU processes is worse.
**Do this instead:** exit prompt when a sweep is live: `[K]ill (terminate group) / [D]etach (default for launched sweeps — resume-safe by marker design) / [C]ancel exit`. `start_new_session=True` makes both explicit choices, and re-attach works later because monitoring reads the filesystem.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| `run_sweep.py` | subprocess (argv LIST) for execution; module import for planning | contracts frozen; additive flag threading per Pattern 6 table |
| `run_finetune.py` | never called directly by the TUI for sweeps; contract untouched | FlopsCounter port into it is pipeline-side work, not TUI |
| `env_smoke.py` | subprocess before first launch; parse greppable `PASS:`/`FAIL:` lines + exit code | blocks launch on FAIL with reasons shown |
| `modelscope` CLI | subprocess per queued dataset; `shutil.which` prerequisite check | token already at `~/.modelscope`; resume on re-run (confirm in phase) |
| `script/audit_n_frequencies.py` | subprocess for post-download verification | authoritative row counts; output `n_audit.json` re-read |
| Textual ≥8,<9 | new `tui` uv group; ty src include + ruff as usual | Python 3.13 supported (6.3.0+); expect major-bump deprecation churn |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| screens ↔ services | constructor injection; services emit frozen `ServiceEvent`s consumed by App workers | fakes in tests; no service imports textual |
| TUI ↔ pipeline scripts | process seam + filesystem bus | TUI never writes into `pipeline/` outputs; only reads registries/artifacts |
| TUI ↔ config | `~/.config/dnallmmark/` JSON, atomic writes, injectable root | never repo-local; templates import/export via file paths |
| launcher ↔ monitor | independent: launcher owns the Process; monitor owns the tree | monitor works with zero processes (attach to CLI-launched sweep); log tail available only for TUI-launched sweeps (stdout pipe) |
| TUI ↔ multi-GPU (P4) | launcher generalizes to N `SweepProcess`es, each `CUDA_VISIBLE_DEVICES=<dev>` + disjoint `--models` shard | static sharding (deterministic, resume markers stay per-shard authoritative); dynamic work-stealing rejected — two workers could claim one cell, and run_sweep's marker-skip is the only concurrency guard |

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Smoke (1 model × 1 task × 1 seed) | nothing — monitor tick 2 s, frontier scan trivial |
| Full sweep (62×50×3 ≈ 9,300 cells, days) | frontier scan + 60 s full rescan (full rescan ≈ 10 ms of stats); RichLog capped (e.g. `max_lines=10_000`); DataTable shows aggregates + windowed detail, not 9,300 rows at once |
| Multi-GPU (P4, N GPUs) | N run_sweep subprocesses with static model shards; per-shard monitors (same service, N instances); merge view = read-only scan of the shared output_root (run_sweep's own layout makes shard outputs disjoint by model dir); DDP (torchrun) is a separate per-cell axis — decide explicitly in P4 (requirements cross-check: sharding for E2' throughput, DDP for single 1B+ model acceleration; `--ddp_find_unused_parameters` already exists in run_finetune) |
| Downloads (50 datasets, multi-GB) | serial queue by design (storage & bandwidth on one box); persistence + re-enqueue on start; verification decoupled from transfer |

### Scaling Priorities

1. **First bottleneck: monitor scan cost at full-sweep scale** — solved by frontier-first scanning (Pattern 2); revisit only if a tick exceeds ~50 ms.
2. **Second: log volume** — cap RichLog; never persist full logs in the TUI (per-cell stdout is not captured to disk by run_sweep — a TUI-side log file would be the only copy; if persistence is wanted, tee the stream to a TUI-managed file under the config dir, documented as TUI-owned, never alongside pipeline audit artifacts).

## Recommended Build Order (feeds ROADMAP phase structure)

Dependency-ordered; each phase's gate named:

1. **WP-A (pipeline-side, parallel track, EARLY — maintainer directive: 落地于 P3 前): FlopsCounter port** from `dnallmmark_pipeline.py` into `run_finetune.py` (20+ architecture hooks). Independent of every TUI phase; benefits E2' FLOPs correctness and the leaderboard efficiency axis regardless of TUI fate. Not TUI work — do not couple its verification to TUI phases.
2. **P1 — TUI foundation:** `tui/` package skeleton, `services/settings.py` + `services/registries.py`, selection matrix screen with n_audit presence column, Pilot harness (tier-1 + tier-2 tests, CI decision), pyproject `tui` group + ty/ruff wiring, `make tui`. Gate: matrix renders 62×50 with filters; CI green without GPU/dnallm.
3. **P2 — Data manager:** `services/downloads.py` queue + modelscope CLI driver + verification via audit script; queue persistence + resume. Depends only on P1 (registries/settings). Gate: one real missing dataset round-trips download → verify → presence flips.
4. **P2.5 (small, lands with P2 or P3) — run_sweep argv threading:** `--subset_file`, `--effective-batch`, `--num_train_epochs` (+optional `--cache_dir`), argv-shape tests in `tests/test_sweep.py`. Must land **before** the RunConfig screen ships its full surface; independent of screens so it can start any time after P1 scaffolding exists.
5. **P3 — Run config + single-GPU launch + monitoring:** RunSpec form + dry-run preview (imported enumeration), env_smoke gate, E2' confirm modal, `services/launcher.py`, monitor screen. Depends on P1 (screens/services) + P2.5 (flags exist) + WP-A only in the sense that FLOPs-correct runs want it landed first (maintainer sequencing: FlopsCounter before P3). Gate: bounded smoke (1 model × 1 task × 1 seed, 1 epoch) launched, monitored, failure re-run exercised end-to-end on GB10; E2' gate provably blocks full sweeps.
6. **P4 — Multi-GPU orchestration (HARD-GATED on P3 single-GPU validation — maintainer: 单卡开发成功再开发多卡):** static model sharding × `CUDA_VISIBLE_DEVICES`, N `SweepProcess`es, per-worker health + isolation re-run, merged dashboard; explicit DDP-vs-sharding decision documented. Gate: 2-GPU sharded bounded run; worker kill isolates and re-runs.

Ordering rationale in one line each: WP-A is early because it is pipeline-critical-path and TUI-independent; settings/registries before everything because every screen consumes them; downloads before launch because env_smoke itself checks dataset presence (a FAIL there is undiagnosable without the manager); flag-threading before RunConfig because the form cannot promise flags that do not exist; monitoring lands with launch (same phase) because the launcher's stdout stream and the monitor's filesystem scan are one screen; multi-GPU last because it is N copies of the launcher plus shard math — cheap only after single-GPU is proven.

## Sources

- Repo (HIGH, direct inspection 2026-10-11): `pipeline/run_sweep.py` (esp. `launch_subprocess` :872, `run_matrix` :995-1170, `build_argv` :810, argparse :231-330), `pipeline/run_finetune.py` (argparse :57-265, `base_dir` :672-673, :922, :973), `pipeline/env_smoke.py` (PASS/FAIL contract), `pyproject.toml` (groups/ty/pytest), `tests/conftest.py` (sys.path seam), `docs/TUI-REQUIREMENTS.md`, `.planning/PROJECT.md`
- Official Textual docs, fetched 2026-10-11 (HIGH): guide/workers, guide/screens, guide/testing, guide/reactivity, widgets/data_table, api/timer
- Textual version status (MEDIUM): libregistry/Debian/Buildroot trackers via search — 8.2.x current, Python 3.13 supported since 6.3.0
- ModelScope CLI (MEDIUM for flags, HIGH for channel availability via in-repo validation): TUI-REQUIREMENTS §2 + third-party CLI guides
- Textual filesystem-watch APIs: LOW/inconclusive — correctly treated as unavailable

---
*Architecture research for: Textual TUI integration over the DNALLM-Mark subprocess sweep architecture (v1.2)*
*Researched: 2026-10-11*
