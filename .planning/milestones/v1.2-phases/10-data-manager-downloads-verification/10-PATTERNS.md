# Phase 10: Data Manager (Downloads & Verification) - Pattern Map

**Mapped:** 2026-10-12
**Files analyzed:** 10 (5 new, 5 modified)
**Analogs found:** 10 / 10

All analog paths below are git-TRACKED repo source (verified: `tui/`, `tests/tui/`, `script/` are tracked trees on branch `autorun`).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `tui/services/download_queue.py` (NEW) | service | event-driven (subprocess orchestration) + CRUD (XDG state file) | `tui/services/gauntlet.py` (subprocess legs) + `tui/services/custom_entries.py` (XDG-root read/write seam) | exact (two-part composite) |
| `tui/screens/data_manager.py` (NEW) | component (Textual Screen) | event-driven (worker messages → row updates) | `tui/screens/env_check.py` (worker + per-row fill + drill-down) + `tui/screens/selection.py` (column geometry, state rows, modals) | exact |
| `tui/screens/nav.py` (EDIT) | route/config (nav slots) | — | itself; slot-3 placeholder → real (mirror of how slot routing reads `NAV_SLOTS`) | exact |
| `tui/screens/selection.py` (EDIT) | component | event-driven | itself; `w`/`e` binding family → add `d` enqueue binding | exact |
| `tui/screens/env_check.py` (EDIT) | component | — | itself; route line amendment | exact |
| `tui/app.py` (EDIT) | config (composition root) | — | itself; `action_nav` slot routing + `build_selection_screen` factory | exact |
| `tui/strings.py` (EDIT) | config (i18n) | — | itself; `GAUNTLET_*` block as the newest prefix-group precedent | exact |
| `tests/tui/test_services_download_queue.py` (NEW) | test | — | `tests/tui/test_services_gauntlet.py` (fake-runner + real-subprocess lanes) | exact |
| `tests/tui/test_pilot_data_manager.py` (NEW) | test | — | `tests/tui/test_pilot_selection_custom.py` (real app + injected fakes) | exact |
| stderr fixture files (NEW, `tests/tui/` data) | test fixture | — | the verbatim captures in 10-RESEARCH §Output streams | no in-repo analog (seed from research) |

## Pattern Assignments

### `tui/services/download_queue.py` (service; NEW — the core file)

**Analogs:** `tui/services/gauntlet.py` (subprocess discipline, ~70%), `tui/services/custom_entries.py` (XDG-root persistence seam, ~30%)

**Copy verbatim from gauntlet.py:**
- Module docstring shape (contract-decision header, ZERO-textual declaration) — `gauntlet.py:1-57`
- Import block: `import json, os, subprocess, sys, tempfile; from dataclasses import dataclass; from pathlib import Path` + `import artifact_loader` / `import registry_loader` as TOP-LEVEL modules (pipeline/ sys.path root — never `pipeline.xxx`) + `from tui.services import settings` — `gauntlet.py:59-78`
- `REPO_ROOT = Path(__file__).resolve().parents[2]` — `gauntlet.py:82`, `custom_entries.py:95`
- Frozen `@dataclass` result item with `run_id` field (WR-02 tag-and-drop) — `GauntletItem` at `gauntlet.py:120-144`. Name it e.g. `QueueEvent(key, state, last_percent, details, raw_output, run_id)`.
- `LEG_*`-style module constants + `_AUDIT_SPLIT_ORDER`-style shape-table constants at module top (the repo-shape census A/B/C/D as code-owned data, ~15 rows — RESEARCH recommends this idiom explicitly, `gauntlet.py:99-112`).
- The reconcile-leg invocation **shape** — `gauntlet.py:322-356` (candidate-only temp registry dir, ABSOLUTE `Dataset_path` via `(self._pipeline_dir / raw_path).resolve()` — the Pitfall-3 inertness rationale at `gauntlet.py:335-343` — every output flag to a temp path, `env[CUSTOM_DIR_ENV] = str(empty_overlay)`). Per RESEARCH Open Question 4, re-implement the ~30-line staging + verdict parse inside download_queue.py rather than importing GauntletService (planner's call).
- The `_audit_verdict` pass criteria — `gauntlet.py:390-455` verbatim semantics: `missing` false, three splits rows>0 (bool excluded), `unified_eval_n`>0, declared==measured. Declared side = registry entry `Train`/`Dev`/`Test` ints.
- The `_invoke` launch-failure absorption + timeout → failed-item (never an exception across the service boundary) — `gauntlet.py:531-559`
- Tempfile staging: `with tempfile.TemporaryDirectory(prefix="dnallmmark-...") as tmp:` — `gauntlet.py:239-242, 322-323`
- Injectable-runner seam: `def __init__(self, runner=None, ...)` + `Runner = Callable[..., Any]` type — `gauntlet.py:117, 147-161, 168-187`. The download leg needs a **Popen-shaped** seam (not `subprocess.run`) because cancel uses killpg; inject a `spawner(argv, env, start_new_session=True, stdout=PIPE, stderr=PIPE)` returning a Popen-like object.

**Copy verbatim from custom_entries.py / settings.py (persistence):**
- Queue state file = `settings.state_dir() / "download_queue.json"` — NOT a new env var; `settings.state_dir()` already honors `DNALLMMARK_TUI_STATE_DIR` (`settings.py:44, 48-66`). Do NOT copy `_env_aware_config_root` — the state root needs no extra override layer.
- Every write through `settings.atomic_write(path, json.dumps(doc, indent=4, ensure_ascii=False))` — `custom_entries.py:420-432` `_write_entries`, `settings.py:90-107`
- Tolerant read returning `(value, error_message)` tuples, absence-is-empty — `custom_entries.py:172-206` `read_entries`; also `artifact_loader.load_json_artifact`'s None sentinel (`gauntlet.py:274-275, 370-371`)
- `load()` downgrade rule: entries persisted `downloading` → `pending` (D-06), persisted after EVERY state transition (mirror `land`'s read-modify-write strictness on corrupt files: `custom_entries.py:239-243`).

**What differs:**
- `Popen(argv, start_new_session=True)` with `stdout=PIPE, stderr=PIPE`; cancel = `os.killpg(os.getpgid(proc.pid), signal.SIGTERM)` then wait + SIGKILL escalation (RESEARCH Pitfall 1). Never a shell, never a wrapper PID. `subprocess.run` (gauntlet's `_default_runner`) cannot cancel — hence the Popen seam.
- Console-script resolution: `Path(sys.executable).parent / "modelscope"` then `shutil.which("modelscope")`; absence = probed unavailable state, never an import.
- stderr streamed/parsed (ANSI strip + `Downloading \[...\]:\s+(\d+)%` / `Processing (\d+) items:` — regex in RESEARCH Code Examples); stdout carries the two clean markers.
- Post-landing existence check `pipeline/datasets/<G>/<t>/{train,dev,test}.csv` BEFORE reconcile (RESEARCH Pitfall 3); shape-C post-landing rename step; shape-D keys never enqueued (disabled data).
- Zenodo probe: stdlib `urllib.request` GET, probe-state constants, session-memory — RESEARCH Code Examples block is the reference implementation; frozen module-constant URL.
- Pure `merge_presence(audit_tasks, reconcile_results)` overlay function (RESEARCH Pattern 3) lives here — `presence_for` stays untouched and consumes the merged dict unchanged (`registries.py:208-261`).
- NO credential fields in the queue schema (SC5); schema carries `schema_version` + task array.

### `tui/screens/data_manager.py` (component; NEW — slot-3 screen)

**Analogs:** `tui/screens/env_check.py` (worker/messages/drill-down), `tui/screens/selection.py` (table geometry, modals, state rows)

**Copy verbatim from env_check.py:**
- Module docstring contract header + ZERO-service-logic declaration — `env_check.py:1-40`
- Protocol injection seam: `class DataManagerServiceProtocol(Protocol)` + real `Backend` adapter class + `__init__(service=None)` default-real — `env_check.py:102-143, 330-341`
- Exclusive `@work(exclusive=True, thread=True)` worker posting nested `Message` classes (`CheckItemChecking`/`CheckItemDone`/`CheckRunComplete` all carrying `run_id`) — `env_check.py:289-329`; worker body with `get_current_worker()`, `worker.is_cancelled` polls between steps — `env_check.py:395-429`
- Message handlers dropping stale `run_id` — `env_check.py:433-459`
- Per-row `table.update_cell(row_key, col_key, Text(glyph, style=...))` inline fill — `env_check.py:463-471`
- Screen frame: `yield TopMenuBar()` ... `yield BottomBar()`, `NAV_SLOT: ClassVar[int] = 3`, nav-digit bindings block — `env_check.py:278-287, 343-355`
- Verbatim drill-down `EnvDetailModal` (ModalScreen + `RichLog(wrap=True)` writing lines verbatim) — `env_check.py:193-226`
- Style constants `_STYLE_DIM/_STYLE_PASS/_STYLE_FAIL` + `"$text-muted"`/`"$success"` tokens — `env_check.py:92-94`

**Copy verbatim from selection.py:**
- Column-geometry block `_MODEL_COLUMNS: tuple[tuple[str, str, int], ...]` with per-column widths + `_cell`/`_truncate` helpers (`rich` Text measurement) — `selection.py:738-798`
- State-row mechanism (`_loading`/`_no_match` row keys + `_add_state_row`) — `selection.py:772-775, 1295-1300`
- `ConfirmModal` for `x` cancel — import from `tui.screens.selection` (wizard.py does exactly this: `from tui.screens.selection import ConfirmModal`, `wizard.py:108`)
- below_minimum_grid guard on any async chrome push — `selection.py:1601-1603` (`if self.app.below_minimum_grid: return`)
- `is_valid_coordinate(cursor_coordinate)` guard before `coordinate_to_cell_key` (it RAISES, never None) — `selection.py:1480-1489`
- Two stacked table regions → `textual.containers.Vertical`/`VerticalScroll` (UI-SPEC Component Inventory row for Containers)

**What differs:** two DataTables (missing upper fixed-height, queue lower flex) instead of one; progress-cell bar rendering (`█`×k + `·`×(10−k)) as in-cell rich Text; mismatch banner Statics under the queue title; `d/r/x/a/enter/g/z` binding set (D-15 + UI-SPEC keyboard map); Zenodo probe worker at mount posting a probe-state message.

### `tui/screens/nav.py` (EDIT)

**Analog:** itself. Change `NAV_SLOTS` slot 3 — `nav.py:81-88` — from `NavSlot(3, NAV_LABEL_DATA, None, 10)` to `NavSlot(3, NAV_LABEL_DATA, "data_manager", None)`. The placeholder suffix/toast path (`slot.phase is not None`, `nav.py:180-183`; app.py:224-225) then no longer fires for slot 3 — zero other nav changes (UI-SPEC 导航壳 amendment).

### `tui/screens/selection.py` (EDIT — `d` enqueue on presence-✗ rows)

**Analog:** itself — the `w`/`e` custom-entry action family is the exact precedent for adding one action binding + optional injected service seam.

- Append `Binding("d", "enqueue_dataset", SEL_ENQUEUE_LABEL)` after the w/e bindings in `BINDINGS` (`selection.py:1104-1108` — declaration order = bottom-bar order, the migration-table pattern)
- Optional constructor injection `queue_service=None` default-real, mirroring `custom_service` (`selection.py:1140-1156`)
- Cursor-key resolution via `_cursor_key()` + the presence lookup in `self._data.presence` (`selection.py:1480-1489, 812-836`); no-op-with-toast on present rows (`action_toggle_enabled`'s official-row toast, `selection.py:1541-1543`, is the shape)
- Presence-flip refresh = re-run the existing `_load_data()` exclusive worker after a reconcile-pass service event (`selection.py:1500-1503` `_on_custom_registry_changed`), with the presence snapshot built over the **merged** overlay view (RESEARCH Pattern 3) inside `SelectionBackend.load_selection_data` (`selection.py:379-387` — the `presence_for` loop is where `merge_presence` plugs in)

### `tui/screens/env_check.py` (EDIT — route hint)

**Analog:** itself. Amend `ENV_ROUTE_MISSING_DATASETS` rendering (`env_check.py:499-505`) to carry the `[3] 前往数据管理` keycap hint; the digit-3 nav binding already exists (`env_check.py:283`). No new binding (one navigation path per target).

### `tui/app.py` (EDIT — slot-3 registration)

**Analog:** itself — `action_nav` (`app.py:212-241`) and `build_selection_screen` (`app.py:195-208`).
- Add `DataManagerScreen` import; add routing branch in `action_nav` (env/selection branch shape, `app.py:228-235`)
- Screen factory vs zero-arg SCREENS registry decision: the data-manager screen holds live queue-service state → prefer a `build_data_manager_screen()` factory sharing one app-level queue-service instance (the `build_selection_screen` shared-sets rationale, `app.py:196-208`), or a single app-level `DownloadQueueService` injected into every builder (selection `d` and env routing need the same instance)
- Optional constructor injection `download_queue_service=None` mirroring `env_check_service` (`app.py:165-180`)

### `tui/strings.py` (EDIT — DL_ / QUEUE_ prefixes)

**Analog:** itself — the `GAUNTLET_*` block (Phase 9's latest prefix group) and the `ENV_ROUTE_MISSING_DATASETS` constant at `strings.py:99-101` (amend in place per UI-SPEC). Every copy row in the 10-UI-SPEC Copywriting Contract is verbatim source; constants stay module-level UPPER_SNAKE with `{placeholders}`. The grep lock (no Chinese literals outside strings.py in screens/app) extends automatically via existing tests.

### `tests/tui/test_services_download_queue.py` (NEW — tier-1)

**Analog:** `tests/tui/test_services_gauntlet.py` — copy its whole structure:
- Dual-lane docstring header (`test_services_gauntlet.py:1-36`)
- `FakeRunner`-style injectable seam recording `(argv, env, kwargs)` + configurable results (`test_services_gauntlet.py:74+`); argv-shape pins: LIST argv, absolute script paths, `os.environ` + exactly-one env override
- Real-subprocess lane for the reconcile leg (real `script/audit_n_frequencies.py` over fixture CSVs, CPU sub-second — the gauntlet precedent) and for cancel (a `sleep` script + killpg path)
- Env pinning helper `pin_config_dir`/state-dir pinning via `monkeypatch.setenv(settings.STATE_DIR_ENV, str(tmp_path))` (`test_services_gauntlet.py:47-53`)
- State-machine/restart tests: write queue JSON with `downloading` entry → `load()` returns `pending`; atomic-write round-trip
- Parser tests over recorded stderr fixture files (ANSI, `\r`, pkg_resources noise); Zenodo probe with mocked `urllib.request.urlopen` (200/404/other/timeout); overlay-merge unit tests asserting `presence_for` flips on merged input

### `tests/tui/test_pilot_data_manager.py` (NEW — tier-2)

**Analog:** `tests/tui/test_pilot_selection_custom.py` — copy its structure:
- Real `DnallmMarkTui` with constructor/`SelectionScreen`-style injected deterministic fakes (fake queue service conforming to the screen Protocol)
- `await pilot.pause()` before every assertion; `CJK_RE` if any copy assertions; slot-3 nav test (`NAV_SLOTS` import, `test_pilot_selection_custom.py:57-60`)
- Backstop tests from UI-SPEC: 68-char key renders in both tables; Zenodo line at 80 cols; selection `d` binding end-to-end; env route hint presence

## Shared Patterns

### Subprocess discipline (LIST argv + artifact verdicts)
**Source:** `tui/services/gauntlet.py:250-251, 348-356, 531-559` — apply to download leg, reconcile leg, and `g` re-audit. LIST argv, absolute paths, temp outputs, verdicts from parsed artifacts never exit codes alone, launch failures absorbed into failed items.

### Run-id message tagging (WR-02)
**Source:** `tui/services/gauntlet.py:120-144` (item side) + `tui/screens/env_check.py:289-329, 433-459` (handler drop side). Apply to every queue event crossing worker→event-loop.

### Atomic XDG state persistence
**Source:** `tui/services/settings.py:44, 48-107` (`state_dir`, `atomic_write`). One-line consumption: `settings.atomic_write(settings.state_dir() / "download_queue.json", json.dumps(...))`. Tests pin `DNALLMMARK_TUI_STATE_DIR` at tmp.

### Services-tier zero-textual lock
**Source:** `tests/tui/test_import_lock.py` (AST walk, any depth). New service module lands under the existing lock automatically — no lock changes needed; keep `download_queue.py` import-free of textual and of modelscope.

### Constructor-injection service seam
**Source:** `tui/screens/env_check.py:102-143` (Protocol + Backend + default-real) and `tui/screens/selection.py:1140-1156`. Every screen seam in this phase copies this shape.

### below_minimum_grid guard
**Source:** `tui/app.py:288-298` (property) + `tui/screens/selection.py:1601-1603` (usage). Apply to the data-manager screen's async modal pushes (drill-down, cancel confirm) and any Zenodo-driven chrome.

## No Analog Found

| File/Element | Role | Reason / Substitute |
|---|---|---|
| stderr progress-parser regexes | service util | No in-repo subprocess-output parsing exists. Use 10-RESEARCH §Code Examples regexes verbatim (live-probed) + seed fixture files from the research's verbatim captures |
| Zenodo HTTP probe | service util | No stdlib-HTTP precedent in tui/services. Use 10-RESEARCH probe-state implementation verbatim (4-state machine, mocked-urlopen tests) |
| Popen streaming + killpg cancel | service util | Gauntlet uses blocking `subprocess.run`. Combine gauntlet's argv/env discipline with RESEARCH Pitfall-1 mechanics (start_new_session, killpg, reader-thread stderr); no repo precedent for streaming — worker-owned, tier-1 tested with a sleep script |

## Metadata

**Analog search scope:** `tui/` (app, screens, services, strings), `tests/tui/`, `script/`, `pipeline/env_smoke.py` (verified via 10-RESEARCH)
**Files scanned:** 9 source files read in full/partial + 4 test modules
**Pattern extraction date:** 2026-10-12
