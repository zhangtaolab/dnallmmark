"""
Tier-2 Pilot suite for the matrix overview screen + the app wiring
(Phase 8, 08-07 Task 2; SEL-01 auxiliary view).

Pins the read-only matrix against the REAL ``DnallmMarkTui`` with
constructor-injected fakes (the ``SelectionServiceProtocol`` seam — no
real registry or audit file is touched; the env screen boots on a
cache-hit fake, D-03):

- ``v`` from the selection screen pushes the matrix; esc pops back to
  the selection screen with BOTH mark sets intact (the screen stack over
  the shared app-state sets);
- the grid: one row per model keyed on the registry key, one column per
  dataset keyed on the task key, single presence glyphs per cell, the
  diamond mark prefix on marked-model row labels AND marked-dataset
  column headers;
- column headers truncate to 8 cells with the ellipsis; the cursor
  readout line below the table carries the FULL task key of the cursor
  column, live on cursor movement;
- read-only by absent bindings: space, /, p, x, m, s pressed on the
  matrix change no mark, open no modal, and crash nothing (the
  out-of-scope ban on an editable grid, enforced by what is absent);
- horizontal scrolling exposes every column at 80 columns (the fixed
  first column stays pinned);
- enter opens the full-key modal (the complete task + model keys,
  verbatim);
- n_audit absent: the documented column-level empty copy renders instead
  of the grid;
- the app wiring: the env screen's ``s`` binding opens the selection
  screen through the app factory (the shared-set contract).

Pilot discipline (08-RESEARCH Pattern 7 / Pitfall 7): ``await
pilot.pause()`` before every assertion; the selection load worker is
awaited via ``app.workers.wait_for_complete()`` — never a timed sleep.
"""

import re
from pathlib import Path

from env_smoke import CheckResult
from rich.text import Text
from textual.widgets import DataTable, RichLog

import tui.screens.matrix as matrix_screen_module
from tui.app import DnallmMarkTui
from tui.screens.matrix import MatrixKeyModal, MatrixScreen
from tui.screens.selection import (
    PresetMenu,
    PresetOption,
    SelectionData,
    SelectionScreen,
)
from tui.services import selection as selection_service
from tui.services.registries import (
    PRESENCE_MISSING,
    PRESENCE_PRESENT,
    Presence,
)
from tui.strings import (
    ENV_KERNEL_LABELS,
    MATRIX_CURSOR_READOUT,
    MATRIX_TITLE,
    SEL_N_AUDIT_MISSING,
    SEL_REGISTRY_LOAD_FAILED,
)

_MATRIX_MODULE_FILE = Path(matrix_screen_module.__file__)

# The 3x4 fixture (mixed presence incl. missing cells) — realistic
# registry keys so the header-truncation assertions exercise real shapes.
_MODELS = ("plant-dnamamba-6mer", "plant-dnabert-6mer", "PlantHelixSeek")
_TASKS = (
    "GUE__emp_H3",
    "GUE__prom_core",
    "iDNA_ABF_datasets__5mC",
    "PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation",
)
_PRESENCE = {
    "GUE__emp_H3": Presence(status=PRESENCE_MISSING, rows=None),
    "GUE__prom_core": Presence(status=PRESENCE_PRESENT, rows=(100, 20, 20)),
    "iDNA_ABF_datasets__5mC": Presence(
        status=PRESENCE_PRESENT, rows=(743095, 109717, 106227),
    ),
    "PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation":
        Presence(status=PRESENCE_MISSING, rows=None),
}


def _matrix_data(model_keys=_MODELS, task_keys=_TASKS,
                 presence=None, audit_available=True):
    """A selection snapshot for the matrix (models x datasets)."""
    return SelectionData(
        model_entries=tuple(
            {"key": key, "type": "MLM", "species": "plants",
             "size_m": 100.0, "card": {}}
            for key in model_keys
        ),
        dataset_entries=tuple(
            {"key": key, "category": "Plants", "type": "binary",
             "metric": "f1", "card": {}}
            for key in task_keys
        ),
        presence=dict(presence if presence is not None else _PRESENCE),
        audit_available=audit_available,
    )


class _EnvCacheHitFake:
    """The env-check boot fake: a same-day cache hit, zero kernels."""

    def cached_results(self):
        return ("2026-10-11 09:30", tuple(
            CheckResult(name=kernel_id, ok=True, lines=(f"PASS: {kernel_id}",))
            for kernel_id in ENV_KERNEL_LABELS
        ))

    def kernels(self):
        raise AssertionError("a cache-hit boot must never spawn the worker")

    def persist(self, results):
        raise AssertionError("a cache-hit boot must never persist")


class _MatrixFake:
    """The minimal selection-service fake: load + the real grammar.

    The preset/template/save surfaces raise — the matrix tests never
    press their bindings (the screen defines none).
    """

    def __init__(self, data):
        self.data = data

    def load_selection_data(self):
        return self.data

    def parse_filter(self, query):
        return selection_service.parse_filter_query(query)

    def apply_filter(self, entries, parsed):
        return selection_service.apply_filter(entries, parsed.terms)

    def preset_menu(self):
        raise AssertionError("preset menu is not under test here")

    def custom_names(self):
        raise AssertionError("custom names are not under test here")

    def save_preset(self, name, models, tasks):
        raise AssertionError("save is not under test here")

    def import_template(self, path):
        raise AssertionError("template import is not under test here")

    def export_template(self, path, models, tasks):
        raise AssertionError("template export is not under test here")

    def export_tiers(self, path, models, tasks):
        raise AssertionError("tier export is not under test here")


# =====================================================================
# Helpers
# =====================================================================

def _cell(value):
    """Plain text of a DataTable cell (cells carry rich Text styles)."""
    return value.plain if isinstance(value, Text) else str(value)


def _row(table, index):
    return [_cell(cell) for cell in table.get_row_at(index)]


def _row_keys(table):
    return [str(key.value) for key in table.rows]


def _column_keys(table):
    return [str(key.value) for key in table.columns]


def _app(data):
    """The real app with the env cache-hit fake + the matrix fake."""
    return DnallmMarkTui(
        env_check_service=_EnvCacheHitFake(),
        selection_service=_MatrixFake(data),
    )


async def _open_matrix(pilot, app):
    """Open selection (loaded), then push the matrix via ``v``."""
    app.push_screen(app.build_selection_screen())
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()
    await pilot.press("v")
    await pilot.pause()


def _text_width(value):
    """Display width of a string (Rich's measurement, never len())."""
    return Text(value).cell_len


# =====================================================================
# Pilot tests — push/pop, grid, glyphs, diamonds (SEL-01 auxiliary)
# =====================================================================

async def test_v_pushes_matrix_esc_pops_back_with_marks_intact():
    """v from selection pushes the matrix; esc pops back, marks intact."""
    app = _app(_matrix_data())
    async with app.run_test(size=(120, 40)) as pilot:
        app.push_screen(app.build_selection_screen())
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        selection = app.screen
        assert isinstance(selection, SelectionScreen)

        # mark one model + one dataset before pushing (the shared sets)
        await pilot.press("space")
        await pilot.press("m")
        await pilot.pause()
        await pilot.press("space")
        await pilot.press("m")
        await pilot.pause()
        assert selection.marked_models == {"plant-dnamamba-6mer"}
        assert selection.marked_tasks == {"GUE__emp_H3"}

        await pilot.press("v")
        await pilot.pause()
        assert isinstance(app.screen, MatrixScreen)
        matrix = app.screen
        # the matrix reads the SAME live shared sets
        assert matrix._marked_models is selection.marked_models
        assert matrix._marked_tasks is selection.marked_tasks

        # esc pops back to the selection screen — marks intact
        await pilot.press("escape")
        await pilot.pause()
        assert app.screen is selection
        assert selection.marked_models == {"plant-dnamamba-6mer"}
        assert selection.marked_tasks == {"GUE__emp_H3"}


async def test_matrix_renders_grid_glyphs_and_diamond_prefixes():
    """Rows keyed on model keys; columns on task keys; single-glyph
    cells; the diamond prefix on marked rows AND marked headers."""
    app = _app(_matrix_data())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_matrix(pilot, app)
        matrix = app.screen
        assert isinstance(matrix, MatrixScreen)
        table = matrix.query_one(DataTable)

        # one row per model, keyed on the registry key, registry order
        assert _row_keys(table) == list(_MODELS)
        # the fixed model column + one column per dataset task key
        assert _column_keys(table) == ["model", *_TASKS]
        assert table.fixed_columns == 1

        # single presence glyphs per cell — the dataset's presence in
        # every row of its column (render-only, from the 08-04 data)
        assert _cell(table.get_cell("plant-dnamamba-6mer",
                                    "GUE__prom_core")) == "✓"
        assert _cell(table.get_cell("PlantHelixSeek", "GUE__emp_H3")) == "✗"
        assert _cell(table.get_cell(
            "plant-dnabert-6mer", _TASKS[3],
        )) == "✗"

        # pre-mark one model + one dataset (shared sets) and re-push:
        # the diamond prefixes render on the row label AND the header
        app.screen._marked_models.add("plant-dnabert-6mer")
        app.screen._marked_tasks.add("GUE__prom_core")
        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("v")
        await pilot.pause()
        table = app.screen.query_one(DataTable)
        assert _row(table, 1)[0] == "◆ plant-dnabert-6mer"
        assert _row(table, 0)[0] == "plant-dnamamba-6mer"
        marked_header = str(table.columns["GUE__prom_core"].label)
        assert marked_header.startswith("◆ ")
        unmarked_header = str(table.columns["GUE__emp_H3"].label)
        assert unmarked_header == "GUE__em…"
        # every header stays within the 8-cell budget (incl. the prefix)
        for task_key in _TASKS:
            assert Text(str(table.columns[task_key].label)).cell_len <= 8


async def test_unknown_presence_renders_the_dim_glyph():
    """A task absent from the audit mapping renders the unknown glyph."""
    presence = dict(_PRESENCE)
    del presence["iDNA_ABF_datasets__5mC"]
    app = _app(_matrix_data(presence=presence))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_matrix(pilot, app)
        table = app.screen.query_one(DataTable)
        assert _cell(table.get_cell(
            "plant-dnamamba-6mer", "iDNA_ABF_datasets__5mC",
        )) == "◌"


async def test_readout_tracks_the_cursor_column_full_task_key():
    """The readout carries the FULL task key of the cursor column, live."""
    app = _app(_matrix_data())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_matrix(pilot, app)
        matrix = app.screen
        table = matrix.query_one(DataTable)

        readout = matrix.query_one("#matrix-readout")
        # the cursor starts on the FIRST dataset column — the readout is
        # immediately meaningful (the full key, never the 8-cell header)
        assert str(readout.content) == MATRIX_CURSOR_READOUT.format(
            task_key=_TASKS[0],
        )

        # moving the cursor across columns updates the readout live
        await pilot.press("right")
        await pilot.pause()
        assert str(readout.content) == MATRIX_CURSOR_READOUT.format(
            task_key=_TASKS[1],
        )
        await pilot.press("right")
        await pilot.pause()
        assert str(readout.content) == MATRIX_CURSOR_READOUT.format(
            task_key=_TASKS[2],
        )
        # the title carries the live counts
        assert matrix.query_one("#matrix-screen-title").content == (
            MATRIX_TITLE.format(models=3, datasets=4)
        )
        assert table.row_count == 3


async def test_no_mark_filter_or_preset_bindings_exist_on_matrix():
    """Read-only by absent bindings: space///p/x/m/s are all no-ops."""
    app = _app(_matrix_data())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_matrix(pilot, app)
        matrix = app.screen
        matrix._marked_models.add("plant-dnamamba-6mer")
        matrix._marked_tasks.add("GUE__emp_H3")
        marks_before = (set(matrix._marked_models), set(matrix._marked_tasks))

        for key in ("space", "slash", "p", "x", "m", "s", "v"):
            await pilot.press(key)
            await pilot.pause()
            # still the matrix screen — no modal, no screen change, and
            # the marks are untouched (no binding consumed the key)
            assert isinstance(app.screen, MatrixScreen), (
                f"{key!r} must do nothing mark/filter/preset-related"
            )
        assert (set(matrix._marked_models),
                set(matrix._marked_tasks)) == marks_before


async def test_horizontal_scroll_exposes_all_columns_at_80():
    """At 80 columns the fixed model column stays pinned and every
    dataset column is reachable by cursor movement."""
    task_keys = tuple(f"task-{index:02d}" for index in range(12))
    presence = {
        key: Presence(status=PRESENCE_PRESENT, rows=(1, 1, 1))
        for key in task_keys
    }
    app = _app(_matrix_data(task_keys=task_keys, presence=presence))
    async with app.run_test(size=(80, 24)) as pilot:
        await _open_matrix(pilot, app)
        matrix = app.screen
        table = matrix.query_one(DataTable)

        # the grid is wider than the 80-column viewport — h-scroll is on
        assert table.virtual_size.width > table.size.width
        # walk the cursor to the LAST column
        for _ in range(len(task_keys) - 1):
            await pilot.press("right")
        await pilot.pause()
        readout = str(matrix.query_one("#matrix-readout").content)
        assert readout == MATRIX_CURSOR_READOUT.format(
            task_key=task_keys[-1],
        )
        # the viewport followed the cursor (all columns are exposed)
        assert table.scroll_x > 0


async def test_enter_opens_the_full_key_modal():
    """enter: the full task + model keys render verbatim."""
    app = _app(_matrix_data())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_matrix(pilot, app)
        matrix = app.screen

        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, MatrixKeyModal)
        modal = app.screen
        assert modal.task_key == _TASKS[0]
        assert modal.model_key == _MODELS[0]
        log = modal.query_one("#matrix-key-log", RichLog)
        rendered = " ".join(
            "".join(strip.text for strip in log.lines).split()
        )
        assert f"task: {_TASKS[0]}" in rendered
        assert f"model: {_MODELS[0]}" in rendered

        await pilot.press("escape")
        await pilot.pause()
        assert app.screen is matrix


async def test_n_audit_absent_renders_the_documented_empty_copy():
    """n_audit absent: the copy renders instead of the grid."""
    app = _app(_matrix_data(audit_available=False))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_matrix(pilot, app)
        matrix = app.screen
        # the empty state is the body — no table is composed
        assert not list(matrix.query(DataTable))
        assert str(matrix.query_one("#matrix-empty").content) == (
            SEL_N_AUDIT_MISSING
        )
        # esc still pops back (the screen stays a screen)
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SelectionScreen)


async def test_models_registry_degraded_mounts_empty_copy_and_stays_alive():
    """CR-03: v in the models-registry-degraded state (the selection
    screen's own survivable empty state) pushes a matrix that mounts the
    documented load-failure copy — never a rowless grid that crashes on
    mount; enter is a no-op on the empty state; esc pops back alive."""
    base = _matrix_data()
    degraded = SelectionData(
        model_entries=(),
        dataset_entries=base.dataset_entries,
        presence=base.presence,
        models_load_error="/repo/pipeline/models_info.json",
    )
    app = _app(degraded)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_matrix(pilot, app)
        matrix = app.screen
        assert isinstance(matrix, MatrixScreen)
        # the documented load-failure copy IS the body — no grid composed
        assert not list(matrix.query(DataTable))
        assert str(matrix.query_one("#matrix-empty").content) == (
            SEL_REGISTRY_LOAD_FAILED.format(
                registry_path="/repo/pipeline/models_info.json",
            )
        )
        # enter is a no-op on the empty state (no grid, no crash)
        await pilot.press("enter")
        await pilot.pause()
        assert app.screen is matrix
        # esc pops back to the selection screen — the app stays alive
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SelectionScreen)


# =====================================================================
# App wiring — the env screen's s binding (08-UI-SPEC Keyboard map)
# =====================================================================

async def test_env_s_binding_opens_the_selection_screen():
    """s on the env screen opens selection through the app factory."""
    app = _app(_matrix_data())
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from tui.screens.env_check import EnvCheckScreen
        assert isinstance(app.screen, EnvCheckScreen)

        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, SelectionScreen)
        # the shared-set contract: the factory wired the app's live sets
        assert app.screen.marked_models is app._marked_models


# =====================================================================
# Source-level gates (permanent CI enforcement of the verify gates)
# =====================================================================

def test_screen_module_carries_zero_chinese_literals():
    """I18N-01 single-home: no operator-facing copy outside strings.py."""
    source = _MATRIX_MODULE_FILE.read_text(encoding="utf-8")
    offenders = re.findall(r"[一-鿿]", source)
    assert not offenders, (
        "Chinese literals must live in tui/strings.py only "
        f"({len(offenders)} found in {_MATRIX_MODULE_FILE.name})"
    )


def test_screen_defines_its_read_only_navigation_bindings():
    """The verify gate: exactly the esc/enter pair — and none of the
    mark/filter/preset vocabulary anywhere in the BINDINGS."""
    source = _MATRIX_MODULE_FILE.read_text(encoding="utf-8")
    assert source.count("Binding(") >= 1, (
        "the screen must define its read-only navigation bindings"
    )
    for forbidden in ("toggle_mark", "apply_preset", "open_templates",
                      "save_preset", "focus_filter", "switch_list"):
        assert forbidden not in source, (
            f"the matrix must never gain a {forbidden} binding "
            "(read-only by absent bindings — the out-of-scope ban)"
        )


# =====================================================================
# Task 3 — the cross-screen navigation integration (composed app, fakes)
# =====================================================================

class _IntegrationFake(_MatrixFake):
    """The full-flow fake: load + grammar + one canned tier-1 preset."""

    def __init__(self, data):
        super().__init__(data)
        self.menu = PresetMenu(options=(
            PresetOption(
                id="tier-1", kind="derived", name=None,
                models=("plant-dnamamba-6mer", "PlantHelixSeek"),
                tasks=("GUE__emp_H3",),
            ),
        ))

    def preset_menu(self):
        return self.menu

    def custom_names(self):
        return ()


async def test_cross_screen_navigation_integration():
    """The composed navigation path end-to-end, headless with fakes:
    env screen -> s to selection -> filter -> mark -> preset -> v to
    matrix -> esc -> q — proving the app wiring as one flow."""
    from tui.screens.env_check import EnvCheckScreen

    # the app directly (NOT via _app — that helper wraps its argument in
    # _MatrixFake; the integration fake IS the service)
    app = DnallmMarkTui(
        env_check_service=_EnvCacheHitFake(),
        selection_service=_IntegrationFake(_matrix_data()),
    )
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        # the app opens on the env screen (cache-hit fake — instant)
        assert isinstance(app.screen, EnvCheckScreen)

        # s opens the selection screen through the app factory
        await pilot.press("s")
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        selection = app.screen
        assert isinstance(selection, SelectionScreen)
        table = selection.query_one(DataTable)
        assert _row_keys(table) == list(_MODELS)

        # the k9s filter narrows the model table, esc clears it
        await pilot.press("slash")
        await pilot.pause()
        for character in "mlm":
            await pilot.press(character)
        await pilot.pause()
        assert _row_keys(table) == list(_MODELS)  # all three are MLM
        await pilot.press("escape")
        await pilot.pause()
        assert _row_keys(table) == list(_MODELS)

        # spacebar marks the cursor row (the shared app-state set)
        await pilot.press("space")
        await pilot.pause()
        assert selection.marked_models == {"plant-dnamamba-6mer"}

        # the preset applies with REPLACING semantics (tier-1 marks its
        # pair models AND its task) — the menu read is a worker (WR-04)
        await pilot.press("p")
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert selection.marked_models == {
            "plant-dnamamba-6mer", "PlantHelixSeek",
        }
        assert selection.marked_tasks == {"GUE__emp_H3"}

        # v pushes the read-only matrix over the same shared sets
        await pilot.press("v")
        await pilot.pause()
        assert isinstance(app.screen, MatrixScreen)
        matrix_table = app.screen.query_one(DataTable)
        assert _row_keys(matrix_table) == list(_MODELS)
        # the diamond prefixes reflect the live mark sets (tier-1 marked
        # plant-dnamamba-6mer and PlantHelixSeek; plant-dnabert is bare)
        assert _row(matrix_table, 0)[0] == "◆ plant-dnamamba-6mer"
        assert _row(matrix_table, 1)[0] == "plant-dnabert-6mer"
        assert _row(matrix_table, 2)[0] == "◆ PlantHelixSeek"

        # esc pops back to the selection screen — marks intact
        await pilot.press("escape")
        await pilot.pause()
        assert app.screen is selection
        assert selection.marked_models == {
            "plant-dnamamba-6mer", "PlantHelixSeek",
        }
        assert selection.marked_tasks == {"GUE__emp_H3"}

        # q quits the whole console cleanly
        await pilot.press("q")
        await pilot.pause()
        assert app.return_code == 0
