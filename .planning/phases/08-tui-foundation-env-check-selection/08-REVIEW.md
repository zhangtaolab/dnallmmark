---
phase: 08-tui-foundation-env-check-selection
reviewed: 2026-10-11T16:25:25Z
depth: standard
files_reviewed: 34
files_reviewed_list:
  - Makefile
  - pipeline/env_smoke.py
  - pyproject.toml
  - schemas/run_template.json
  - tests/test_env_smoke_bytes.py
  - tests/tui/conftest.py
  - tests/tui/test_import_lock.py
  - tests/tui/test_pilot_boot.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_matrix.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_services_env_check.py
  - tests/tui/test_services_env_gate.py
  - tests/tui/test_services_quick_check.py
  - tests/tui/test_services_registries.py
  - tests/tui/test_services_selection.py
  - tests/tui/test_services_settings.py
  - tests/tui/test_services_templates.py
  - tui/__init__.py
  - tui/__main__.py
  - tui/app.py
  - tui/screens/__init__.py
  - tui/screens/env_check.py
  - tui/screens/matrix.py
  - tui/screens/selection.py
  - tui/services/__init__.py
  - tui/services/env_check.py
  - tui/services/env_gate.py
  - tui/services/quick_check.py
  - tui/services/registries.py
  - tui/services/selection.py
  - tui/services/settings.py
  - tui/services/templates.py
  - tui/strings.py
  - tui/styles.tcss
findings:
  critical: 3
  warning: 5
  info: 6
  total: 14
status: issues_found
---

# Phase 8 (TUI foundation — env check + selection): Code Review Report

**Reviewed:** 2026-10-11T16:25:25Z
**Depth:** standard
**Files Reviewed:** 34
**Status:** issues_found

## Summary

Standard-depth adversarial review of the full Phase 8 TUI slice (34 files: the
`tui/` package, its tier-1/tier-2 test suites, the `env_smoke.py` D-02
structured-return refactor, the `[tui]` dependency wiring, the Makefile lanes,
and the D-07 run-template schema). All 170 phase tests pass and the ruff gate
is clean — but the passing suite has coverage holes, and probing them with
headless Textual Pilot reproductions confirmed **three console-crashing
defects** in untested paths, plus a permanently-stuck-screen state, a
worker-message race, and several contract inconsistencies.

The phase's load-bearing invariants were verified and **hold**:

- **Services textual-free**: no `textual` import (static or dynamic) anywhere
  under `tui/services/` (grep + AST verified; `tests/tui/test_import_lock.py`
  enforces the static form — see IN-01 for the dynamic-import gap).
- **env_smoke byte contract**: `main()` remains the sole renderer
  (`_emit`/`print_ecosystem_diagnostics` are its helpers only); the golden
  byte suite pins three full-stdout scenarios and passes; the refactor's
  behavior matches the pre-refactor module (verified against `3214460~1`).
- **Dependency lanes**: `uv.lock` group membership verified — `data` =
  evaluate/numpy/pandas/scipy, `gpu` = torch/transformers,
  `tui` = jsonschema/platformdirs/textual exactly; textual-dev/textual-serve
  appear in no committed group; default-groups = ["data"], so data/gpu lanes
  never install textual.
- **CI byte-untouched**: `.github/workflows/ci.yml` last changed in Phase 5
  (`fb419f6`); it invokes everything through the Makefile, whose `test`,
  `test-fast`, `ci`, `lint`, and `typecheck` targets all now carry
  `--group tui` — so `tests/tui` collection works with zero workflow edits.
- **Schema one-way contract**: `schemas/run_template.json` is strict
  draft-2020-12, `additionalProperties: false` at the single object level,
  `schema_version` const 1, exactly the ratified field set.
- **XDG split + atomic writes**: `DNALLMMARK_TUI_STATE_DIR`/`_CONFIG_DIR`
  whole-dir overrides (empty = unset) resolve independently through
  platformdirs; all persistence sites write tmp + `os.replace`.
- **I18N single home**: Chinese literals exist only in `tui/strings.py`
  (grep-enforced per screen module + the registries service).

The three BLOCKERs are all in the 08-06/08-07 presentation layer, each
reproduced headlessly against the real `DnallmMarkTui`.

## Critical Issues

### CR-01: Pressing `?` on the selection screen crashes the console (Rich MarkupError from the `[/]` keycap)

**File:** `tui/app.py:84` (with `tui/app.py:246-273`, `tui/strings.py:40`, trigger binding `tui/screens/selection.py:796-798`)
**Issue:** `HelpModal.compose` renders each help row as
`Static(APP_HELP_ROW.format(key=key, label=label))` where
`APP_HELP_ROW = "[{key}] {label}"`. The selection screen's filter binding
declares `key_display="/"`, so its row is the literal string `"[/] 过滤"` —
Rich parses `[/]` as an auto-closing markup tag with nothing to close and
raises `MarkupError`, which kills the whole console during layout. Confirmed
by headless Pilot repro (`?` on the selection screen →
`MarkupError: auto closing tag ('[/]') has nothing to close`). The env-screen
help test passes only because that screen has no `/` binding. Two further
defects in the same row construction: (a) `_binding_rows` does not filter
`show=False` bindings, so the selection screen's hidden `enter`/`escape`
bindings are listed; (b) `_binding_row` returns a row for bindings with no
description, so the 2-arg escape binding yields `("escape", None)` —
`"[escape] None"` operator-facing copy.
**Fix:** Render the rows as `rich.text.Text` (bypasses markup), and filter
hidden/description-less bindings:

```python
# tui/app.py
from rich.text import Text

def _binding_rows(self) -> "list[tuple[str, str]]":
    rows = [row for row in map(_binding_row, self.BINDINGS)
            if row is not None]
    rows.extend(row for row
                in map(_binding_row, getattr(self.screen, "BINDINGS", []))
                if row is not None)
    return rows

def _binding_row(binding: BindingType) -> "tuple[str, str] | None":
    if isinstance(binding, Binding):
        if not binding.show or not binding.description:
            return None  # hidden bindings never help-render (Footer contract)
        return (binding.key_display or binding.key, binding.description)
    if len(binding) >= 3 and binding[2]:
        return (binding[0], binding[2])
    return None

# HelpModal.compose — a Text content object is never markup-parsed:
yield Static(Text(APP_HELP_ROW.format(key=key, label=label)))
```

Add a Pilot test opening `?` on the selection screen (the current help test
covers only the env screen).

### CR-02: Template export / preset save to an unwritable or invalid path crashes the console (unhandled OSError)

**File:** `tui/screens/selection.py:1209-1231` (`_submit_export`/`_submit_tiers`), `tui/screens/selection.py:1289-1299` (`_do_save`), root write path `tui/services/settings.py:90-107`
**Issue:** The path-input modal contract is "problems render in-modal, the
modal stays open" — but the submit handlers catch only `ValueError` (the
empty-selection refusal). `atomic_write` performs
`target.parent.mkdir(parents=True, exist_ok=True)` + `write_text` +
`os.replace`, any of which raises `OSError` for operator-plausible paths:
a parent that is a file (`/dev/null/x.json`), a read-only location, a
directory target, a full disk. Confirmed by headless Pilot repro: with a
model and a task marked, exporting to `/dev/null/x.json` crashes the whole
console with `FileExistsError: [Errno 17] File exists: '/dev/null'`.
`_do_save` has no try/except at all (a read-only `~/.config` crashes the
save flow the same way). This contradicts the module's own fail-closed modal
contract and the everywhere-else "degrade, never crash" discipline.
**Fix:** Catch `OSError` alongside `ValueError` in all three write paths and
surface it as modal problems (or a warning toast for save):

```python
def _submit_export(self, path: str) -> "Sequence[tuple[str, str]] | None":
    try:
        self._service.export_template(
            path, sorted(self._marked_models), sorted(self._marked_tasks),
        )
    except ValueError as exc:
        return ((path, str(exc)),)
    except OSError as exc:  # unwritable/invalid operator path — fail closed
        return ((path, f"export failed: {type(exc).__name__}: {exc}"),)
    self.app.notify(SEL_TEMPLATE_EXPORTED.format(path=path))
    return None
```

Apply the same `except OSError` to `_submit_tiers`, and wrap `_do_save`'s
`save_preset` call with a warning notification on `OSError`.

### CR-03: Matrix screen crashes on mount (CellDoesNotExist) in the registry-degraded state it is supposed to survive

**File:** `tui/screens/matrix.py:213-238` (crash site `222-231`), dead guards `tui/screens/selection.py:1064-1066` and `tui/screens/matrix.py:225-226`
**Issue:** When the models registry read fails, `SelectionBackend`
deliberately degrades (`model_entries=()`, `models_load_error` set) and the
selection screen's Pilot test pins "the app stays alive". But `v` in that
state pushes `MatrixScreen` with zero model rows; `on_mount` then sets
`cursor_coordinate = Coordinate(0, 1)` (dataset entries are healthy) and
calls `_update_readout()` → `_current_task_key()` →
`table.coordinate_to_cell_key(...)`, which **raises**
`CellDoesNotExist: No cell exists at Coordinate(row=0, column=1)` on the
rowless table (verified against the installed textual 8.2.8: the method
raises for invalid coordinates, it never returns None). Confirmed by
headless Pilot repro. The `if cell_key is None` guards in
`selection.py:1065` and `matrix.py:225-226` are dead code — they guard a
return value the API never produces — so nothing catches the raise.
**Fix:** Validate the coordinate before conversion, and skip the grid when
there are no model rows:

```python
# tui/screens/matrix.py
def _current_task_key(self) -> "str | None":
    table = self.query_one("#matrix-table", DataTable)
    if not table.is_valid_coordinate(table.cursor_coordinate):
        return None  # empty grid — no cell under the cursor
    cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
    ...

# on_mount: compose the documented empty copy instead of a rowless grid
if not self._data.model_entries:
    yield Static(SEL_REGISTRY_LOAD_FAILED.format(...), id="matrix-empty")
    return
```

Replace the dead `cell_key is None` guards in `selection.py:1064-1066` with
the same `is_valid_coordinate` check (the guard exists for exactly this
crash class and does nothing).

## Warnings

### WR-01: Min-size guard pops the wrong screen — console permanently stuck on MinSizeScreen at full size

**File:** `tui/app.py:213-238` (restore branch 236-238)
**Issue:** Below 80x24 the guard pushes `MinSizeScreen`. App-level bindings
still fire while it is active (it is a plain `Screen` with no bindings), so
`?` pushes `HelpModal` **on top of** the guard. Growing back then runs
`self.pop_screen()` — which pops the TOP screen (the modal), not the guard —
and sets `_min_size_screen = None`. Confirmed by headless Pilot repro:
after shrink(60x20) → `?` → grow(120x40), the active screen is still
`MinSizeScreen` showing "终端过小（需 ≥ 80x24，当前 60x20）" at full size.
The state is permanent: further shrink/grow cycles push/pop fresh guards and
never remove the stale one; only `q` (quit) escapes.
**Fix:** Suppress chrome below the minimum and only pop the guard when it is
the active screen:

```python
def action_help(self) -> None:
    if self._min_size_screen is not None:
        return  # below the minimum grid: no chrome over the guard
    self.push_screen(HelpModal(self._binding_rows()))

# _apply_min_size_guard restore branch:
elif guard is not None:
    self._min_size_screen = None
    if self.screen is guard:
        self.pop_screen()
```

### WR-02: Env-check refresh race — a cancelled worker's last CheckItemDone can overwrite the fresh run's result

**File:** `tui/screens/env_check.py:349-370`
**Issue:** `run_full_check` is `@work(exclusive=True, thread=True)`; on
refresh, the previous worker is cancelled and a new one starts immediately,
but the old OS thread finishes its in-flight kernel and posts its
`CheckItemDone` **after** the new worker may have posted the same kernel's
fresh result. The `is_cancelled` poll only runs between kernels. When the
stale message lands last, `on_env_check_screen_check_item_done` overwrites
the row glyph, the summary cell, and `self._results[kernel]` with the old
value — so the final table row and the drill-down source disagree with the
`CheckRunComplete` verdict/persisted state (which correctly carry the new
run). The Pilot refresh test gates the first run to completion first, so the
interleave is never exercised.
**Fix:** Tag messages with a monotonically increasing run id and drop stale
ones in the handlers:

```python
class CheckItemDone(Message):
    def __init__(self, result: CheckResult, run_id: int) -> None:
        self.result = result
        self.run_id = run_id
        super().__init__()

# worker: capture self._run_counter at start; increment in action_refresh.
# handler:
def on_env_check_screen_check_item_done(self, message: CheckItemDone) -> None:
    if message.run_id != self._run_id:
        return  # a newer exclusive run superseded this result
    ...
```

### WR-03: Tier-grammar mismatch — derive_presets rejects task-omitting tier-1 specs that run_sweep and the templates service both accept

**File:** `tui/services/selection.py:206-218` vs `pipeline/run_sweep.py:767-783` and `tui/services/templates.py:296-320`
**Issue:** `run_sweep.load_priority_tiers` documents and accepts a
`{model, task}` spec that omits `task` ("covering the model's every task"),
and this same phase's `templates.tiers_to_template` handles
`task is not None` for exactly that grammar. But `derive_presets` requires
`isinstance(entry.get("task"), str)` — a tier-1 spec omitting `task` makes
the ENTIRE priorities file "damaged": empty presets plus a load error in the
preset modal. A maintainer editing `pipeline/sweep_priorities.json` in the
pipeline's own grammar would silently lose the whole TUI preset menu. The
committed file currently satisfies the strict shape, so nothing fails today.
**Fix:** Accept an omitted `task` in tier-1 pairs (matching the pipeline
grammar) — treat `entry.get("task")` as `None` contributing the model only,
or at minimum validate `task is None or isinstance(task, str)` and derive
the same way `tiers_to_template` does.

### WR-04: preset_menu runs two full registry reads + the priorities/customs files synchronously on the event loop

**File:** `tui/screens/selection.py:1112-1125` (handler) over `tui/screens/selection.py:325-355` (backend)
**Issue:** The module contract states the registry read runs in ONE
exclusive `@work(thread=True)` worker ("D-03: the only registry-read site"),
and `load_selection_data` honors it. But `action_apply_preset` calls
`self._service.preset_menu()` directly in the key handler — which re-reads
BOTH registries (`_load_entries` x2), the priorities file, and presets.json
on the event loop. Same class: `custom_names()` in `_submit_save`, and the
import/export file I/O in the modal submit handlers. On a cold cache or a
network-mounted home this stalls the UI — precisely what T-08-07 (the
responsiveness requirement this phase added) exists to prevent.
**Fix:** Either cache the loaded registry keys from the `DataLoaded` worker
snapshot and build the preset menu over them (the snapshot is already on the
screen), or move `preset_menu()` into the existing exclusive-worker pattern
with a posted message.

### WR-05: Machine-dependent tests — four registries tests and the 62/50 backend assertions omit the custom-overlay pin the module's own docstring mandates

**File:** `tests/tui/test_services_registries.py:131-158, 250-258`; `tests/tui/test_pilot_selection.py:1052-1074`
**Issue:** The module docstring pins the discipline ("the custom overlay dir
is pinned to a fresh empty tmp dir, so the assertions pin the COMMITTED
official registries — 62/50 — regardless of any local
`~/.config/dnallmmark/custom_{models,datasets}.json` a machine may carry"),
and the count/entry-shape tests honor it. But
`test_model_entries_carry_raw_values_with_empty_string_absents` (62-length
implicit via entry lookup, plus the `"" in {e["type"]...}` sweep),
`test_dataset_entries_carry_raw_values`,
`test_size_m_is_the_numeric_card_field_as_float`,
`test_every_registry_dataset_key_maps_to_a_definite_presence` (a custom
dataset key yields PRESENCE_UNKNOWN, breaking
`statuses == {PRESENT, MISSING}`), and the Pilot
`test_backend_loads_the_committed_registries_and_presence`
(`len(...) == 62` / `== 50`) all read the overlay-merged registries with NO
`DNALLMMARK_CUSTOM_REGISTRY_DIR` pin. Any machine carrying the documented
Phase 7 user overlay fails these tests — a test-reliability defect.
**Fix:** Apply the same three-line pin used by the sibling tests
(`monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(empty_overlay))`)
to each of the five tests.

## Info

### IN-01: The import-lock test cannot detect dynamic textual imports

**File:** `tests/tui/test_import_lock.py:28-41`
**Issue:** The lock walks `ast.Import`/`ast.ImportFrom` nodes only.
`importlib.import_module("textual")` or `__import__("textual")` inside a
services module would pass it. Grep confirms no services module currently
uses any dynamic import (the invariant holds today); this is a hardening gap
in the lock, not a live violation.
**Fix:** Extend the AST walk to flag `ast.Call` nodes whose func is
`__import__` or an `import_module` attribute, with the first argument the
constant `"textual"` (or any non-literal first argument, conservatively).

### IN-02: Matrix cursor readout renders an empty task key on the fixed model column

**File:** `tui/screens/matrix.py:222-238`
**Issue:** Moving the cursor left onto the fixed model column (column 0)
makes `_current_task_key()` return None (the column key `"model"` is not a
task key) and the readout renders `"光标: "` — a dangling label with no
value. Cosmetic, but the readout's contract is "the FULL task key of the
cursor column".
**Fix:** When the cursor column is the model column, render a distinct
string (e.g. the cursor row's model key) instead of an empty format field.

### IN-03: check_dataset_dirs crashes with a traceback on a malformed registry entry (pre-existing)

**File:** `pipeline/env_smoke.py:404-417`
**Issue:** `datasets_info[name]["Dataset_path"]` raises KeyError for an
entry missing that key, and the `open(DATASETS_INFO_PATH)` raises OSError if
unreadable — the gate dies with a traceback instead of a named FAIL line,
unlike every import-failure path (`import_or_fail`) and unlike
`read_gpu_pins`'s loud-fail on its own config. Verified pre-existing
(identical code at `3214460~1` — the byte-stable refactor preserved it), and
the committed registry is well-formed; exit is still non-zero so the E2'
dual gate still blocks. Listed because the file is in this phase's scope and
its own docstring posture is "report, never traceback".
**Fix:** Wrap the registry read in try/except and return a
`CheckResult(ok=False, ...)` naming the problem, mirroring `read_gpu_pins`.

### IN-04: atomic_write uses a fixed `.tmp` sibling name

**File:** `tui/services/settings.py:105-107`
**Issue:** Two concurrently running console instances sharing a state/config
root write the same `target.name + ".tmp"` path; a writer's tmp content can
be silently replaced by the other instance before its `os.replace`, so one
write is lost (the file is never torn — always one complete content — so
this is last-writer-wins, not corruption). Single-operator usage makes this
unlikely, but the XDG roots are shared by construction.
**Fix:** Use a unique tmp name
(`target.with_name(f"{target.name}.{os.getpid()}.tmp")` or
`tempfile.mkstemp` in the target's directory).

### IN-05: Pilot tests reach into private textual APIs

**File:** `tests/tui/test_pilot_selection.py:59, 340`
**Issue:** `from textual.keys import _character_to_key` and
`app._notifications` are underscore-private. The `textual>=8.2,<9` pin
bounds the exposure, but a patch release renaming either breaks the tier-2
lane with an import/attribute error rather than a test failure.
**Fix:** Prefer public equivalents where available (`pilot.press` already
accepts printable characters; notifications can be asserted via the
`app.notify` return/`Notifications` API), or isolate the private imports
behind a small helper with a version comment.

### IN-06: Operator-facing diagnostic copy authored in the services layer, outside tui/strings.py

**File:** `tui/services/selection.py:191, 235-236`
**Issue:** `derive_presets`'s load-error sentences
("sweep_priorities unreadable or not valid JSON: ...",
"sweep_priorities damaged at ...") render verbatim as the preset modal's
first line (`PresetModal` → `Static(self._load_error)`) — operator-facing
English sentences living outside the I18N single home. The grep gate only
checks for Chinese literals, so it passes; the single-home rule ("screens
reference these constants, never inline copy") is technically violated.
**Fix:** Return a structured error (path + problem list) from the service
and format the modal line from a `SEL_*` constant, or explicitly document
load diagnostics as "data, not copy" like the env_smoke detail lines.

---

_Reviewed: 2026-10-11T16:25:25Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
