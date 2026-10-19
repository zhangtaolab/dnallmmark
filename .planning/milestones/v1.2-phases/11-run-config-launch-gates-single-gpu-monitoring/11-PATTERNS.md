# Phase 11: Run Config, Launch Gates & Single-GPU Monitoring - Pattern Map

**Mapped:** 2026-10-13
**Files analyzed:** 14 (11 NEW, 3 EDIT)
**Analogs found:** 14 / 14 (11 with strong in-repo analogs; 4 sub-areas have no analog and are covered by research sections, listed per-file)

All analog paths are git-TRACKED (verified via `git ls-files`). No gitignored mirror paths.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `tui/services/run_config.py` | service | request-response (pure compose/preview/gate) | `tui/services/download_queue.py` (service idioms) + `tui/services/selection.py` (XDG mark sets) | exact (role+discipline) |
| `tui/services/sweep_launcher.py` | service | subprocess / streaming-tee | `tui/services/download_queue.py:698-712, 870-876` (`_default_spawner` / `_signal_group`) | exact |
| `tui/services/sweep_monitor.py` | service | batch (artifact-tree scan) | `tui/services/download_queue.py` tolerant loaders + `tui/screens/data_manager.py` reload-worker discipline | role-match (no scanner exists) |
| `tui/screens/run_config.py` | component | request-response | `tui/screens/selection.py` (pickers/filter/`m`) + `tui/screens/data_manager.py` (screen frame) | exact |
| `tui/screens/monitor.py` | component | event-driven (worker messages) | `tui/screens/data_manager.py` (two stacked regions + run-id workers) | exact |
| `tui/strings.py` | config (constants) | — | existing `DL_*`/`QUEUE_*` blocks in `tui/strings.py` | exact |
| `tui/screens/nav.py` | route | — | existing `NavSlot(1..3,6)` entries, `nav.py:82-88` | exact |
| `tui/app.py` | component (composition root) | event-driven | existing `build_data_manager_screen` (`app.py:342-349`) + `q` binding (`app.py:251`) | exact |
| `pipeline/run_sweep.py` | utility (CLI driver) | batch | its own `--peft` machinery (`run_sweep.py:330-343, 1046`) | exact |
| `tests/tui/test_services_run_config.py` | test | — | `tests/tui/test_services_download_queue.py` | exact |
| `tests/tui/test_services_sweep_monitor.py` | test | — | `tests/tui/test_services_download_queue.py` (fake-tree style: `tests/fixtures/e2_replay/finetuned/` is the tree-layout seed) | exact |
| `tests/tui/test_pilot_run_config.py` | test | — | `tests/tui/test_pilot_data_manager.py` (constructor-injected fakes) | exact |
| `tests/tui/test_pilot_monitor.py` | test | — | `tests/tui/test_pilot_data_manager.py` | exact |
| `tests/test_sweep.py` | test (EDIT) | — | its own `flag_value` idiom (`tests/test_sweep.py:175`) + `test_launch_subprocess_builds_argv_list_with_pinned_cwd` (line 515) | exact |

## Pattern Assignments

### `tui/services/run_config.py` (service, request-response)

**Analogs:** `tui/services/download_queue.py` (module skeleton, spawner seam, XDG persistence) + `tui/services/selection.py` (mark-set persistence) + `tui/services/quick_check.py`/`env_gate.py` (frozen consumed face)

**Imports pattern** (copy `download_queue.py:104-114`): stdlib-only + `import signal` etc. + `from tui.services import settings` + zero textual imports (the ast import-lock test `tests/tui/test_import_lock.py` is glob-based and extends automatically). Add `import run_sweep` — D-05 same-source; the sys.path root already exists (`tui/__main__.py:5-18`, `tests/conftest.py:44`); live-probed 0.012s, zero torch.

**Module docstring pattern**: copy `download_queue.py:26-104` shape — numbered decision citations (D-0x) in the docstring, persistence path named, tolerance policy stated.

**Core persistence pattern** (copy `download_queue.py:470-477, 1174-1205`):
```python
path = settings.state_dir() / QUEUE_FILE_NAME   # -> state_dir()/logs/ for tee (D-10)
...
settings.atomic_write(state_path, json.dumps(...))   # settings.py:90-107
```
Slot-4 selection/params/dirs persist exactly like the queue entries: frozen dataclasses (`@dataclass(frozen=True)`, `download_queue.py:512-531` `QueueEntry`/`EnqueueOutcome` shape) — the run spec, preview result, and E2' verdict should each be a frozen dataclass ("DATA, never screen copy").

**Gate steps 1-3 pattern**: gate is a service-tier pure pipeline; env step calls the frozen face verbatim — `quick_check.run_quick_check(kernels=None)` (injectable kernel sequence) and `env_gate.gate_verdict(results) -> GateVerdict(can_launch, reasons, route_to_data)` (`tui/services/env_gate.py:63-66`, `quick_check.py:7-9` docstrings pre-announce Phase 11). E2' predicate + typed-phrase exact-match are pure functions here (D-07); official key sets via direct `json.load` of `pipeline/models_info.json` / `datasets_info.json` (overlay-free — Pitfall 5), NOT via registries.

**PROBE_INELIGIBLE extraction — no import analog, but an exact test-file pattern analog**: `tests/test_run_finetune_contracts.py:8-12` read-source-never-import (run_finetune module-top imports torch). Copy the regex helper sketch in 11-RESEARCH.md "Code Examples" (`load_probe_ineligible`). Never duplicate the 9 names in strings.py; pin with a parity test against the real file.

**Differs from analog**: no queue/claim loop; no subprocess here (that is sweep_launcher).

### `tui/services/sweep_launcher.py` (service, subprocess/streaming)

**Analogs:** `tui/services/download_queue.py:698-712` (spawner seam), `:870-876` (`_signal_group`), `:849-867` (`_pump` — the tee read-side shape)

**Spawner seam — copy verbatim** (`download_queue.py:698-712`):
```python
def _default_spawner(argv, **kwargs):
    return subprocess.Popen(argv, **kwargs)
```
Launcher passes fixed kwargs: `start_new_session=True, cwd=<pipeline/>, env={**os.environ, "PYTHONUNBUFFERED": "1"}, stdout=tee_file, stderr=subprocess.STDOUT` (PYTHONUNBUFFERED is load-bearing — Pitfall 4).

**Kill path — copy verbatim** (`download_queue.py:870-876`):
```python
def _signal_group(proc, sig):
    os.killpg(os.getpgid(proc.pid), sig)
```
(SIGTERM then SIGKILL escalation; the `cancel()` flow at `download_queue.py:1367-1407` shows the removed/signalled/noop outcome vocabulary — reuse for ExitModal kill/detach/cancel.)

**Tee target**: `settings.state_dir() / "logs" / f"sweep_{ts}_{rootname}.log"` — single XDG root (D-10); atomic writes not needed for append-style tee, but the dir joins the same family.

**Live-sweep registry**: a small dict of live Popen handles keyed by output root — no direct analog; model on the queue's claimed-entry state (`download_queue.py` claim/run_task bookkeeping, `:1408-1498`).

**No-analog piece — tee pump**: `download_queue._pump` (`:849-867`) reads PIPE chunks for progress parsing; the sweep tee instead writes the child's stdout directly to the file (no pump thread needed) and the monitor tails the file. Substitute: 11-RESEARCH.md § Research Area 7 (launch mechanics + stdout shape, live-captured dry-run line for the fixture seed).

### `tui/services/sweep_monitor.py` (service, batch scan)

**Analogs:** tolerant-JSON discipline from `download_queue.py` (`artifact_loader` tolerant reads, `pipeline/artifact_loader.py` per CLAUDE.md) + worker/run-id message discipline from `tui/screens/data_manager.py:544-575, 679-694`

**Constants import — copy verbatim seam**: `from run_sweep import MANIFEST_NAME, FAILURES_NAME, RECORD_NAME, RESUME_MARKER, METRICS_NAME, base_model_name` (defined `pipeline/run_sweep.py:252-256`) — never re-type the strings.

**Discovery predicate — no analog**: manifest presence ⇒ finished; Popen alive or mtime churn ⇒ running; neither ⇒ artifacts-only third state (Pitfall 3, O2). Substitute: 11-RESEARCH.md § Research Area 4 (write-timing verified in source: manifest `run_sweep.py:1403`, failures `:1405-1410`, record `:1394`; mkdir-before-executor `:1315`; skip check `:1310-1313`).

**ETA math — no analog**: rolling median of completed-cell durations (skipped excluded) × remaining; per-model else global; `估算中…` degradation. Substitute: 11-RESEARCH.md § Research Area 4 "Elapsed + ETA inputs" + D-17; pure functions, tier-1 testable against fake trees.

**Live failures — no analog (anti-pattern guard)**: derive from `run_record.json` with `status=="failed"` while running (sweep_failures.json lands only at END). Substitute: 11-RESEARCH.md § Research Area 4 (verbatim record schema captured) + O3.

**Fixture seed**: `tests/fixtures/e2_replay/finetuned/**` already exists as a tracked fake tree with `run_record.json`/`trainer_state.json` per seed — clone this layout in tmp_path for monitor tests.

### `tui/screens/run_config.py` (component, request-response)

**Analogs:** `tui/screens/selection.py` (pickers) + `tui/screens/data_manager.py` (screen frame + worker discipline)

**Picker pattern — copy** from `selection.py`: SelectionList with `m` flip, `/` filter Input with right-aligned `({n}/{total})` count, `parse_filter`/`apply_filter` delegation through a Protocol backend (`selection.py:291-341` `SelectionServiceProtocol` + `SelectionBackend`). Reuse the interaction grammar, NOT slot-2's state (D-01).

**Modal reuse — copy verbatim**: `PathInputModal` (`selection.py:1059`), `ConfirmModal` (`selection.py:1109`), `RowDetailModal` (`selection.py:1138`); data_manager imports ConfirmModal cross-screen at `data_manager.py:71`.

**Screen frame — copy** `data_manager.py:596-640` (`compose`: TopMenuBar → title bar → regions → BottomBar; `on_mount`: DataTable build with column keys/widths/cursor_type/zebra_stripes then focus). Params pane rows = label+value height-1 rows inside a VerticalScroll.

**Worker discipline — copy** `data_manager.py:679-694`: run-id bump + `@work(exclusive=True, thread=True, group=...)` + `post_message` + handler drops superseded run ids (WR-02). The preview line recompute uses this on every selection/param change; the gate recomputes independently.

**Differs**: two-column layout (picker | params) instead of two stacked regions — new, per UI-SPEC mockups.

### `tui/screens/monitor.py` (component, event-driven)

**Analog:** `tui/screens/data_manager.py` — exact structural match

**Two stacked regions — copy** `data_manager.py:596-628` compose (fixed-height upper region + flex lower, full-width rule, right-aligned note on the title row — the Zenodo line at `:610-613` is the cadence-note precedent for `扫描: 前沿 2s · 全扫 60s`).

**Worker messages — copy** the `SnapshotLoaded`/`ZenodoProbed`/`ReauditDone` Message classes (`data_manager.py:544-573`) and the run-id-supersede guard (`:690-694`) for the 2s frontier / 60s full scans.

**No-analog piece — periodic cadence**: data_manager reloads are event-driven; NO `set_interval`/timer exists anywhere in `tui/` (grep-verified). The 2s/60s timers are new — use Textual's `set_interval` on the screen, each tick dispatching the existing worker+run-id pattern (never scanning on the event loop). Substitute for analog: UI-SPEC "Scanning discipline" + 11-RESEARCH.md Area 4.

**Tables**: DataTable with stable row keys (the `update_cell`/filter-rebuild idiom, `selection.py:21` docstring) — row key `{model}__{task}` per UI-SPEC.

### `tui/strings.py` (EDIT — constants)

**Analog:** the `DL_*`/`QUEUE_*` blocks; the full constant list is already enumerated verbatim in 11-UI-SPEC.md `## Copywriting Contract` (CFG_ 30+ / LNC_ 13 / MON_ 30) — copy that table directly. Plus one value amendment: `ENV_VERDICT_CRITICAL_FAIL` (one-line diff, UI-SPEC Existing-Surface Amendments).

### `tui/screens/nav.py` (EDIT — route)

**Analog:** `nav.py:82-88`. Copy the real-slot shape `NavSlot(4, NAV_LABEL_RUN_CONFIG, "run_config", None)` / `NavSlot(5, NAV_LABEL_MONITOR, "monitor", None)` replacing the two placeholder tuples. NOTE: slot 5's current placeholder carries `12` with a "delivered by Phase 12" annotation — stale per D-16; the promotion edit removes it (11-RESEARCH "Deprecated/outdated").

### `tui/app.py` (EDIT — composition root)

**Analogs:** `app.py:267` SCREENS registry, `:342-349` `build_data_manager_screen` (service constructed ONCE in the factory, never a zero-arg SCREENS slot — the anti-fork comment at `:345-349` is the load-bearing rationale to copy), `:417` `@work(exclusive=True, thread=True)` driver worker.

**`q` intercept**: the existing binding `Binding("q", "quit", APP_QUIT_LABEL)` (`app.py:251`) gains an `action_quit` override: live sweep ⇒ push ExitModal, else default quit. No analog for the override — small new code; the ExitModal itself is a ConfirmModal-family ModalScreen.

### `pipeline/run_sweep.py` (EDIT — `--config-variant` via ALIASING)

**Analogs — its own machinery, copy exactly:**
- argparse: insert after the `--cache_dir` block (`run_sweep.py:393-401`); the `--peft` argument at `:330-343` is the shape (choices, help naming the alias rule).
- `enumerate_matrix` alias rule: mirror the peft alias (`{model}+lora` style) — probe/curve ⇒ `{model}+{variant}`, head ⇒ `{model}+head` EXCEPT frozen pair `("evo2_1b_base", "megaDNA_updated")` (keeps base; verbatim at `run_finetune.py:1206-1207`).
- `build_argv`: copy the peft line `argv += ["--save_model_name", str(model), "--peft", peft]` (`run_sweep.py:1046`) as `argv += ["--save_model_name", str(model), "--config-variant", variant]`.
- `run_record.json` gains `config_variant` field — precedent: the `peft` field (`run_sweep.py:1151-1161`, `_new_record`).
- Pin the head frozen-pair with a read-source parity test (pattern below).

**CRITICAL — do NOT pass through** (Pitfall 1): the child self-aliases its save name (`run_finetune.py:1194-1209`); a pure pass-through mis-records every cell and retrains forever.

### Test modules

**`tests/test_sweep.py` (EDIT)** — copy the `flag_value(argv, flag)` helper idiom (`:175`) and `test_launch_subprocess_builds_argv_list_with_pinned_cwd` (`:515`, monkeypatched `subprocess.run`, LIST-ness + per-flag asserts; absent flag ⇒ zero elements). New suite: variant alias present + `--save_model_name` + `--config-variant` in argv; absent ⇒ byte-identical argv; alias cell dirs; head×frozen-pair ⇒ base name.

**`tests/tui/test_run_finetune_contracts.py`** — the read-source-never-import pattern (`:8-12` header states the torch rationale; `exec(match.group(0), namespace)` for pure fragments at `:771, 851, 871`). Copy for: (a) PROBE_INELIGIBLE parity (9 names), (b) the head frozen-pair parity.

**`tests/tui/test_services_run_config.py` / `test_services_sweep_monitor.py` (NEW)** — analog `tests/tui/test_services_download_queue.py` (fake spawner/runner recording kwargs; tmp_path state; import-purity assertions).

**`tests/tui/test_pilot_run_config.py` / `test_pilot_monitor.py` (NEW)** — analog `tests/tui/test_pilot_data_manager.py` (constructor-injected deterministic fakes via the Protocol backends; Pilot at 120×40 and 80×24).

**Strings tripwire — MUST extend** (D-12): the bidirectional inventory lock lives in `tests/tui/test_services_download_queue.py:3163-3240` — `EXPECTED_DL_CONSTANTS`/`EXPECTED_QUEUE_CONSTANTS` tuples, `test_dl_and_queue_string_inventory_defined` (every name exists, non-empty) and `test_dl_queue_inventory_complete_no_unlisted_constants` (every defined DL_/QUEUE_ constant is listed). Add `EXPECTED_CFG_/LNC_/MON_` tuples + both test directions (either in that file's pattern or a sibling; plan decides location, pattern is fixed). The services CJK scan at `tests/tui/test_services_about.py:314-335` extends automatically by glob.

### UI-checker FLAG fixes (plan-level TODO anchors)

1. **OQ table staleness — PROBE_INELIGIBLE count**: 11-UI-SPEC line ~211 says "7 names"; the frozen list has **9** (`run_finetune.py:527-537`). Copy `CFG_VARIANT_PROBE_HINT` uses dynamic `{models}` so only spec prose is wrong — note the correction at plan review; the extraction helper + parity test prevent drift going forward.
2. **Enter-key pin on slot 4** (UI-SPEC Keyboard table): `enter` on the picker / no-field-focused opens the 启动门; Inputs consume their own Enter — typing never launches. Pin with a Pilot assertion in `test_pilot_run_config.py`.

## Shared Patterns

### Subprocess discipline (spawner seam + killpg)
**Source:** `tui/services/download_queue.py:698-712` (`_default_spawner`), `:870-876` (`_signal_group`), `:1367-1407` (cancel outcomes)
**Apply to:** `sweep_launcher.py`, ExitModal kill path, every test fake spawner. LIST argv always; `start_new_session=True`; PYTHONUNBUFFERED=1.

### Worker/run-id message discipline
**Source:** `tui/screens/data_manager.py:544-575` (Message classes), `:587` (run ids), `:660-694` (`@work(exclusive=True, thread=True, group=...)` + superseded-post drop)
**Apply to:** run_config preview worker, monitor 2s/60s scans, gate enumeration step.

### XDG persistence + atomic writes
**Source:** `tui/services/settings.py:48` (`state_dir`), `:90-107` (`atomic_write`)
**Apply to:** slot-4 selection/params/dirs, manual monitor roots, tee logs dir (`state_dir()/logs/`, D-10 single root).

### Protocol backend + constructor injection
**Source:** `tui/screens/data_manager.py:250-306` (`DataManagerServiceProtocol` + `DataManagerBackend`), `selection.py:291-358`
**Apply to:** both new screens (Pilot fakes inject the Protocol, never the real service).

### Read-source-never-import (pipeline torch modules)
**Source:** `tests/test_run_finetune_contracts.py:8-12`
**Apply to:** PROBE_INELIGIBLE extraction, head frozen-pair parity test. NEVER `import run_finetune` in tui/ or tests.

### Strings single home + bidirectional inventory lock
**Source:** `tui/strings.py` + `tests/tui/test_services_download_queue.py:3163-3240`
**Apply to:** all CFG_/LNC_/MON_ constants (D-12).

## No Analog Found

| Piece | Owning File | Substitute |
|-------|-------------|------------|
| E2' verdict computation (62×50×≥3 official-only ⊇ predicate + typed-phrase) | `run_config.py` | 11-RESEARCH § Research Area 5 (live-costed; sketch in Code Examples) |
| ETA rolling-median math + variance range | `sweep_monitor.py` | 11-RESEARCH § Research Area 4 "Elapsed + ETA inputs" + D-17; O4 threshold plan-owned |
| Manifest/churn discovery scan (3rd artifacts-only state) | `sweep_monitor.py` | 11-RESEARCH § Research Area 4 (write-timing source-verified); O2 |
| Periodic timer cadence (set_interval) | `monitor.py` | No timer anywhere in `tui/` (grep-verified); wrap the data_manager worker/run-id pattern in Textual `set_interval` |
| Tee-to-file launch (stdout=tee_file) | `sweep_launcher.py` | 11-RESEARCH § Research Area 7; `_pump` (`download_queue.py:849-867`) is the read-side relative only |
| run_sweep dry-run stdout fixture seed | `tests/tui/fixtures/` | Live-captured verbatim in 11-RESEARCH § Research Area 7 (the `[Dry-run] 1 planned cell(s)...` line) |

## Metadata

**Analog search scope:** `tui/`, `tui/services/`, `tui/screens/`, `tests/tui/`, `tests/`, `pipeline/`
**Tracked-source gate:** all named analogs verified non-empty under `git ls-files`
**Pattern extraction date:** 2026-10-13
