"""
matrix — the read-only matrix overview screen (Phase 8, 08-07; SEL-01
auxiliary view).

The auxiliary density view: one row per model, one column per dataset,
single presence glyphs per cell, the diamond mark prefixes on both axes,
and the full task key of the cursor column in a readout line below the
table (long-text resolution — the 68-char registry keys never fit a
column header).

Contract (locked decisions):

- READ-ONLY BY ABSENT BINDINGS (the REQUIREMENTS out-of-scope ban on an
  editable grid): the screen defines exactly its navigation bindings —
  esc pops back to the selection screen, enter opens the full-key modal
  — and NO mark/filter/preset binding exists. Read-only is enforced by
  what is absent, not by convention (plan prohibition).
- Render-only (T-08-08 mitigation): every glyph traces to the 08-04
  presence data in the injected ``SelectionData`` snapshot or to the
  shared mark sets — nothing is computed here (binding constraint 5).
- Marks flow from the SAME live shared sets the selection screen reads
  (constructor-injected by the pushing screen); the diamond prefixes
  render from them at composition time.
- Column headers truncate to 8 cells with the ellipsis (Rich's own
  measurement); the full key renders in the cursor readout line and in
  the enter modal — never elided there.
- The first column (the model keys) is fixed — it stays visible while
  the 50 dataset columns scroll horizontally.
- n_audit absent: the documented column-level empty copy renders INSTEAD
  of the grid (presence is the matrix's entire payload — without it the
  view has nothing honest to show). A failed models-registry read degrades
  the same way (CR-03): the selection screen's survivable degraded state
  must survive HERE too — a rowless grid would crash the cursor readout
  on mount (``coordinate_to_cell_key`` RAISES for invalid coordinates, it
  never returns None), so the documented load-failure copy renders
  instead and the grid is never composed.
- I18N-01: zero Chinese literals in this module — copy renders through
  ``tui/strings.py`` constants; registry keys stay English verbatim.
"""

from typing import TYPE_CHECKING, ClassVar

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.coordinate import Coordinate
from textual.screen import ModalScreen, Screen
from textual.widgets import DataTable, Footer, Header, Label, RichLog, Static

from tui.services.registries import (
    PRESENCE_MISSING,
    PRESENCE_PRESENT,
)
from tui.strings import (
    APP_MODAL_BACK_LABEL,
    ENV_DETAIL_LABEL,
    MATRIX_CURSOR_READOUT,
    MATRIX_SCROLL_HINT,
    MATRIX_TITLE,
    SEL_COL_MODEL,
    SEL_N_AUDIT_MISSING,
    SEL_REGISTRY_LOAD_FAILED,
)

if TYPE_CHECKING:
    # The selection snapshot type — annotations only (the runtime data
    # arrives structurally through the constructor; a runtime import
    # here would be circular: selection imports this screen for the v
    # binding's push).
    from tui.screens.selection import SelectionData


# ===== Geometry =====

#: The fixed model-key column width (the row labels; the first column is
#: pinned so it stays visible while the dataset columns h-scroll).
_MODEL_COLUMN_W = 24

#: Every dataset column: 8 display cells (headers truncate to 8 with the
#: ellipsis; cells are single glyphs).
_TASK_COLUMN_W = 8

#: The model column's DataTable column key (the addressing scheme).
_COL_MODEL = "model"

# Per-cell rich Text styles: semantic theme tokens only (the 08-06/08-07
# idiom — the glyph is the meaning-carrier under NO_COLOR).
_STYLE_DIM = "$text-muted"
_STYLE_PASS = "$success"
_STYLE_FAIL = "bold $error"

#: The diamond mark prefix (08-UI-SPEC Screen 3: marked models/datasets).
_MARK_PREFIX = "◆ "


def _header_text(task_key: str, marked: bool) -> Text:
    """One column header: the diamond prefix when marked, truncated to
    8 cells with the ellipsis (Rich's own width measurement)."""
    text = Text(_MARK_PREFIX + task_key if marked else task_key)
    text.truncate(_TASK_COLUMN_W, overflow="ellipsis", pad=False)
    return text


def _row_label(model_key: str, marked: bool) -> Text:
    """One row label: the diamond prefix when marked, truncated to the
    fixed model-column width."""
    text = Text(_MARK_PREFIX + model_key if marked else model_key)
    text.truncate(_MODEL_COLUMN_W, overflow="ellipsis", pad=False)
    return text


def _presence_glyph(data: "SelectionData", task_key: str) -> Text:
    """One cell glyph from the 08-04 presence data — render only."""
    presence = data.presence.get(task_key)
    if presence is not None and presence.status == PRESENCE_PRESENT:
        return Text("✓", style=_STYLE_PASS)
    if presence is not None and presence.status == PRESENCE_MISSING:
        return Text("✗", style=_STYLE_FAIL)
    return Text("◌", style=_STYLE_DIM)


class MatrixKeyModal(ModalScreen):
    """The enter drill-down: the FULL task key of the cursor column.

    The full registry keys render verbatim (wrapping, never elided) with
    their English technical labels — data, not copy (I18N-01).
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, model_key: str, task_key: str, **kwargs):
        super().__init__(**kwargs)
        self.model_key = model_key
        self.task_key = task_key

    def compose(self) -> ComposeResult:
        with Vertical(id="matrix-key-box", classes="modal-box"):
            yield RichLog(wrap=True, id="matrix-key-log")
            yield Footer()

    def on_mount(self) -> None:
        box = self.query_one("#matrix-key-box", Vertical)
        box.border_title = self.model_key
        log = self.query_one("#matrix-key-log", RichLog)
        log.write(f"task: {self.task_key}")
        log.write(f"model: {self.model_key}")


class MatrixScreen(Screen):
    """The read-only 59x50 presence matrix (SEL-01 auxiliary view)."""

    # READ-ONLY BY ABSENT BINDINGS: exactly the navigation pair — esc
    # pops back to selection, enter opens the full-key modal. No mark,
    # filter, or preset binding exists here (the out-of-scope ban).
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "close", APP_MODAL_BACK_LABEL),
        Binding("enter", "show_key", ENV_DETAIL_LABEL, show=False),
    ]

    def __init__(self, data: "SelectionData",
                 marked_models: "set[str] | None" = None,
                 marked_tasks: "set[str] | None" = None, **kwargs):
        super().__init__(**kwargs)
        self._data = data
        self._marked_models: set[str] = (
            marked_models if marked_models is not None else set()
        )
        self._marked_tasks: set[str] = (
            marked_tasks if marked_tasks is not None else set()
        )

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="matrix-title-bar"):
            yield Label(
                MATRIX_TITLE.format(
                    models=len(self._data.model_entries),
                    datasets=len(self._data.dataset_entries),
                ),
                id="matrix-screen-title",
            )
            yield Label(MATRIX_SCROLL_HINT, id="matrix-scroll-hint")
        if not self._data.audit_available:
            # n_audit absent: the documented column-level empty copy IS
            # the body — presence is the matrix's entire payload, and a
            # grid of unknown glyphs would hide the actual state
            yield Static(SEL_N_AUDIT_MISSING, id="matrix-empty")
            return
        if self._data.models_load_error is not None:
            # a failed models-registry read (the selection screen's own
            # survivable degraded state): the documented load-failure
            # copy IS the body — a rowless grid would crash the cursor
            # readout on mount (CellDoesNotExist) in exactly the state
            # this screen must survive (CR-03)
            yield Static(
                SEL_REGISTRY_LOAD_FAILED.format(
                    registry_path=self._data.models_load_error,
                ),
                id="matrix-empty",
            )
            return
        yield DataTable(id="matrix-table")
        yield Label("", id="matrix-readout")

    @property
    def _grid_composed(self) -> bool:
        """True when the grid composed (neither empty state holds)."""
        return (
            self._data.audit_available
            and self._data.models_load_error is None
        )

    def on_mount(self) -> None:
        """Compose the grid: fixed model column, one glyph column per
        dataset, diamond prefixes from the live shared mark sets."""
        if not self._grid_composed:
            return  # an empty state composed instead of the grid
        table = self.query_one("#matrix-table", DataTable)
        table.cursor_type = "cell"
        table.zebra_stripes = True
        table.fixed_columns = 1
        table.add_column(SEL_COL_MODEL, key=_COL_MODEL, width=_MODEL_COLUMN_W)
        for task_entry in self._data.dataset_entries:
            task_key = task_entry["key"]
            table.add_column(
                _header_text(task_key, task_key in self._marked_tasks),
                key=task_key, width=_TASK_COLUMN_W,
            )
        for model_entry in self._data.model_entries:
            model_key = model_entry["key"]
            cells = [_row_label(model_key, model_key in self._marked_models)]
            cells.extend(
                _presence_glyph(self._data, task_entry["key"])
                for task_entry in self._data.dataset_entries
            )
            table.add_row(*cells, key=model_key)
        # the cursor starts on the FIRST dataset column — the readout is
        # immediately meaningful (column 0 is the model column); only a
        # grid with model rows can carry a cursor at all
        if self._data.dataset_entries and self._data.model_entries:
            table.cursor_coordinate = Coordinate(0, 1)
        self._update_readout()
        table.focus()

    # ----- the cursor readout -----

    def _current_task_key(self) -> "str | None":
        """The dataset key under the cursor column, else None."""
        table = self.query_one("#matrix-table", DataTable)
        if not table.is_valid_coordinate(table.cursor_coordinate):
            # no cell under the cursor (a rowless grid, or any invalid
            # coordinate) — coordinate_to_cell_key RAISES for invalid
            # coordinates, it never returns None (CR-03)
            return None
        cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        column_key = str(cell_key[1].value)
        if column_key in self._task_key_set:
            return column_key
        return None

    def _update_readout(self) -> None:
        """The cursor readout line: the FULL task key under the cursor."""
        task_key = self._current_task_key() or ""
        self.query_one("#matrix-readout", Label).update(
            MATRIX_CURSOR_READOUT.format(task_key=task_key)
        )

    @property
    def _task_key_set(self) -> frozenset[str]:
        """The dataset keys (the column-key vocabulary)."""
        return frozenset(
            entry["key"] for entry in self._data.dataset_entries
        )

    # ----- actions (the read-only navigation pair) -----

    def action_close(self) -> None:
        """esc: pop back to the selection screen (never quits the app)."""
        self.app.pop_screen()

    def action_show_key(self) -> None:
        """enter (table unfocused): the full-key modal for the cursor.

        A no-op on the empty states — no grid composed, so there is no
        cursor cell to show (querying the absent table would crash).
        """
        if not self._grid_composed:
            return  # an empty state composed instead of the grid
        task_key = self._current_task_key()
        if task_key is None:
            return
        table = self.query_one("#matrix-table", DataTable)
        cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        model_key = str(cell_key[0].value)
        self.app.push_screen(MatrixKeyModal(
            model_key=model_key, task_key=task_key,
        ))

    def on_data_table_cell_highlighted(
            self, event: DataTable.CellHighlighted) -> None:
        """Cursor movement keeps the readout live."""
        self._update_readout()

    def on_data_table_cell_selected(
            self, event: DataTable.CellSelected) -> None:
        """enter on the focused table (its native select event)."""
        self.action_show_key()
