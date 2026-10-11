"""
selection — the selection screen (Phase 8, 08-07; SEL-01..04 presentation).

The operator's daily surface: model/dataset tables browsed one at a time
(the ``m`` toggle), k9s-style type-to-filter over the 08-05 grammar,
spacebar marks into stable app-state sets (one set per list, both alive
while either table is visible), the preset/template modals over the 08-05
services, and the SEL-04 presence column from the 08-04 n_audit data.

Contract (locked decisions):

- Presentation only (the ``tui/screens/`` tier contract): filtering,
  preset derivation, template validation, and presence all live in
  ``tui/services/`` — this screen wires injected service calls to widgets
  and formats their results (binding constraint 5: TUI orchestrates,
  never computes).
- SEL-01 (mark-set mechanism): marks live in SHARED app-state sets keyed
  on registry keys, never inside the DataTable (08-RESEARCH Pitfall 1 —
  DataTable has no multi-select). Spacebar toggles the cursor row's
  membership and updates the dedicated mark column in place via
  ``update_cell``; filter rebuilds (``clear`` + re-``add_row`` with the
  same keys) and the ``m`` table switch can never lose them. Both sets
  are constructor-injected by the composition root so the matrix screen
  (08-07 Task 2) reads the same live sets.
- SEL-01 (filter): the Input drives the injected parse/apply pair; the
  unknown-axis diagnostics render as the dim warning line while valid
  terms still apply; the (N/total) readout is live; esc clears and
  refocuses the table.
- SEL-02 (presets, replacing semantics): applying a preset REPLACES the
  relevant mark set(s) — tier-1 marks pair models AND tasks, tier-2
  models only, all marks every registry key in both lists, customs
  restore both sets as saved. Keys absent from the current registry are
  skipped with the loud warning; the menu order is tier-1, tier-2, all,
  customs sorted by name.
- SEL-03 (templates, fail-closed): import validates collect-all through
  the injected service — a failed import renders the numbered problem
  list and applies NOTHING; a successful import replaces the marks.
- SEL-04 (presence): cells render the 08-04 ``Presence`` values — present
  = pass glyph + thousands-separated exact counts (formatting happens
  only here), missing = the missing word, unknown = the gap-filler copy,
  and the n_audit-absent column state renders the documented copy. The
  ``missing`` flag decision is the service's (tier-1 tested); the screen
  never re-derives it.
- D-03 (the read seam): the registry/n_audit load runs in ONE exclusive
  ``@work(exclusive=True, thread=True)`` worker — the single loading row
  covers the seam; results cross the thread boundary only via
  ``post_message``.
- I18N-01: zero Chinese literals in this module — every operator-facing
  string renders through ``tui/strings.py`` constants (grep-enforced);
  registry keys, filter axes, and JSON pointers stay English verbatim.
- ModalScreen for every modal surface (presets, templates, path/name
  input, confirms, row detail): app/screen bindings do not fire while a
  modal is on top (Pitfall 11).
"""

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any, ClassVar, Protocol

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    RichLog,
    SelectionList,
    Static,
)
from textual.widgets.selection_list import Selection

from tui.services import selection as selection_service
from tui.services.registries import (
    PRESENCE_MISSING,
    PRESENCE_PRESENT,
    Presence,
)
from tui.strings import (
    APP_MODAL_BACK_LABEL,
    ENV_DETAIL_LABEL,
    SEL_COL_CATEGORY,
    SEL_COL_MARK,
    SEL_COL_METRIC,
    SEL_COL_MODEL,
    SEL_COL_PRESENCE,
    SEL_COL_SIZE,
    SEL_COL_SPECIES,
    SEL_COL_TASK,
    SEL_COL_TYPE,
    SEL_FILTER_COUNT,
    SEL_FILTER_KEY_LABEL,
    SEL_FILTER_LABEL,
    SEL_FILTER_PLACEHOLDER,
    SEL_LOADING_ROW,
    SEL_MARK_LABEL,
    SEL_MATRIX_LABEL,
    SEL_N_AUDIT_MISSING,
    SEL_PRESENCE_MISSING,
    SEL_PRESENCE_PRESENT,
    SEL_PRESENCE_UNKNOWN,
    SEL_PRESET_ALL,
    SEL_PRESET_LABEL,
    SEL_PRESET_NO_CUSTOMS,
    SEL_PRESET_TIER_1,
    SEL_PRESET_TIER_2,
    SEL_PRESET_TITLE,
    SEL_SAVE_PRESET_LABEL,
    SEL_SCREEN_TITLE_MODELS,
    SEL_SWITCH_LABEL,
    SEL_TEMPLATE_LABEL,
    SEL_TEMPLATE_MENU_EXPORT,
    SEL_TEMPLATE_MENU_IMPORT,
    SEL_TEMPLATE_MENU_TIERS,
    SEL_TEMPLATE_PROBLEM_LINE,
    SEL_TEMPLATE_PROBLEMS,
    SEL_TEMPLATE_TITLE,
)

# ===== Service data shapes (the injection contract's vocabulary) =====


@dataclass(frozen=True)
class SelectionData:
    """One loaded snapshot of the registries + presence (pure data).

    Attributes:
        model_entries: canonical 08-04 model entries (registry order).
        dataset_entries: canonical 08-04 dataset entries.
        presence: registry key -> 08-04 ``Presence`` (the real backend
            fills dataset keys from n_audit; keys absent here render the
            unknown cell).
        audit_available: False when n_audit.json is missing/corrupt —
            every presence cell then renders the documented copy.
        models_load_error: the registry path when the models read failed
            (the tolerant-loader None result), else None.
        datasets_load_error: the datasets-read failure path, else None.
    """

    model_entries: tuple[dict, ...] = ()
    dataset_entries: tuple[dict, ...] = ()
    presence: dict[str, Presence] = field(default_factory=dict)
    audit_available: bool = True
    models_load_error: "str | None" = None
    datasets_load_error: "str | None" = None


@dataclass(frozen=True)
class PresetOption:
    """One preset-menu entry — pure data; the screen applies it.

    Attributes:
        id: ``tier-1`` | ``tier-2`` | ``all`` | ``custom:<name>``.
        kind: ``derived`` | ``custom`` (labels map on the id/kind).
        name: the custom preset's name (None for the derived built-ins).
        models: model registry keys to mark, derivation order.
        tasks: task registry keys to mark (``()`` for tier-2).
        unknown_keys: members absent from the current registries — the
            loud-surfacing channel (never silently dropped).
    """

    id: str
    kind: str
    name: "str | None"
    models: tuple[str, ...] = ()
    tasks: tuple[str, ...] = ()
    unknown_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class PresetMenu:
    """The derived preset menu plus the damaged-priorities signal."""

    options: tuple[PresetOption, ...] = ()
    load_error: "str | None" = None


@dataclass(frozen=True)
class TemplateImport:
    """A template-import outcome — collect-all, fail-closed.

    Attributes:
        ok: True only when the file parsed AND validated — the caller
            applies marks only then.
        problems: every problem as ``(location, message)`` — the JSON
            pointer for validation problems, the path for load failures.
        models: the template's model keys (valid imports only).
        tasks: the template's task keys (valid imports only).
    """

    ok: bool = False
    problems: tuple[tuple[str, str], ...] = ()
    models: tuple[str, ...] = ()
    tasks: tuple[str, ...] = ()


class SelectionServiceProtocol(Protocol):
    """The selection-service surface the screen consumes.

    The constructor-injection seam (the 08-06 pattern): the screen
    depends on this protocol, not on any concrete service — the real
    ``SelectionBackend`` (delegation glue over the 08-04/08-05 service
    modules) and the tier-2 Pilot fakes both conform structurally, so no
    registry file, priorities file, or template file is ever touched by
    a faked Pilot run.
    """

    def load_selection_data(self) -> SelectionData:
        """The registries + presence snapshot (the worker-read seam)."""

    def preset_menu(self) -> PresetMenu:
        """The preset menu: tier-1, tier-2, all, then customs sorted."""

    def custom_names(self) -> tuple[str, ...]:
        """The saved custom-preset names (the overwrite check)."""

    def save_preset(self, name: str, models: Iterable[str],
                    tasks: Iterable[str]) -> None:
        """Persist a custom preset under the config root."""

    def parse_filter(self, query: str) -> Any:
        """Parse a filter query (the 08-05 ParsedFilter shape)."""

    def apply_filter(self, entries: Sequence[dict], parsed: Any) -> list[dict]:
        """Apply parsed terms to entries (pure, order-preserving)."""

    def import_template(self, path: str) -> TemplateImport:
        """Read + collect-all validate one template file (fail-closed)."""

    def export_template(self, path: str, models: Iterable[str],
                        tasks: Iterable[str]) -> None:
        """Export the selection as a run template to the path."""

    def export_tiers(self, path: str, models: Iterable[str],
                     tasks: Iterable[str]) -> None:
        """Export the selection as a sweep_priorities tier list."""


class SelectionBackend:
    """The real selection service — delegation glue over 08-04/08-05.

    Every semantic stays in the tested service modules; this adapter only
    reshapes them into the object seam the screen's constructor injection
    consumes. The registry read is wrapped tolerantly AT THIS SEAM (the
    advisory-UI survivability rule): a missing official registry file or
    a malformed custom overlay degrades to the documented load-error
    state naming the path — the app stays alive (registry_loader's own
    fail-loud contract is untouched for pipeline consumers).
    """

    def __init__(self, config_dir: "str | None" = None,
                 priorities_path: "str | None" = None):
        """Adapt the services over injectable roots (tests point at tmp).

        Args:
            config_dir: the XDG config root; None means the 08-04 default.
            priorities_path: the sweep_priorities file; None means the
                committed pipeline file.
        """
        self._config_dir = config_dir
        self._priorities_path = priorities_path

    # ----- the seam methods (behavior lands in GREEN) -----

    def load_selection_data(self) -> SelectionData:
        """The registries + presence snapshot."""
        return SelectionData()

    def preset_menu(self) -> PresetMenu:
        """The derived preset menu."""
        return PresetMenu()

    def custom_names(self) -> tuple[str, ...]:
        """The saved custom-preset names."""
        return ()

    def save_preset(self, name: str, models: Iterable[str],
                    tasks: Iterable[str]) -> None:
        """Persist a custom preset."""

    def parse_filter(self, query: str) -> Any:
        """Parse a filter query (the pure 08-05 grammar)."""
        return selection_service.parse_filter_query(query)

    def apply_filter(self, entries: Sequence[dict], parsed: Any) -> list[dict]:
        """Apply parsed terms to entries."""
        return selection_service.apply_filter(entries, parsed.terms)

    def import_template(self, path: str) -> TemplateImport:
        """Read + validate one template file (collect-all)."""
        return TemplateImport()

    def export_template(self, path: str, models: Iterable[str],
                        tasks: Iterable[str]) -> None:
        """Export the selection as a run template."""

    def export_tiers(self, path: str, models: Iterable[str],
                     tasks: Iterable[str]) -> None:
        """Export the selection as a tier list."""


# ===== Column geometry (the 80-column budget, 08-UI-SPEC Screen 2) =====
#
# DataTable columns render with 1 cell of padding on each side (the
# textual default ``cell_padding``) and the vertical scrollbar consumes 2
# more cells once rows exceed the height — so a six-column view fits the
# 80-column minimum exactly when the width sum is 66:
# 66 + 12 (padding) + 2 (scrollbar) == 80. Wider content truncates with
# the ellipsis; full values always render in the enter row-detail modal.

_MODELS_VIEW = "models"
_DATASETS_VIEW = "datasets"

_COL_MARK = "mark"
_COL_KEY = "key"
_COL_PRESENCE_KEY = "presence"

#: (column key, header constant, width) — the column keys are the
#: update_cell addressing scheme (English technical ids, I18N-01).
_MODEL_COLUMNS: tuple[tuple[str, str, int], ...] = (
    (_COL_MARK, SEL_COL_MARK, 2),
    (_COL_KEY, SEL_COL_MODEL, 25),
    ("type", SEL_COL_TYPE, 4),
    ("species", SEL_COL_SPECIES, 8),
    ("size", SEL_COL_SIZE, 7),
    (_COL_PRESENCE_KEY, SEL_COL_PRESENCE, 20),
)

_DATASET_COLUMNS: tuple[tuple[str, str, int], ...] = (
    (_COL_MARK, SEL_COL_MARK, 2),
    (_COL_KEY, SEL_COL_TASK, 20),
    ("category", SEL_COL_CATEGORY, 8),
    ("type", SEL_COL_TYPE, 10),
    ("metric", SEL_COL_METRIC, 8),
    (_COL_PRESENCE_KEY, SEL_COL_PRESENCE, 18),
)

# Row keys for the non-registry state rows (never mark/filter targets).
_LOADING_ROW_KEY = "_loading"

# Per-cell rich Text styles: semantic theme tokens only (the 08-06
# idiom — the glyph carries meaning under NO_COLOR, color is the
# redundant channel).
_STYLE_DIM = "$text-muted"
_STYLE_MARK = "bold $accent"
_STYLE_PRESENCE_PASS = "$success"
_STYLE_PRESENCE_FAIL = "bold $error"
_STYLE_PRESENCE_UNKNOWN = "$text-muted"


def _cell(value: object, width: int, style: "str | None" = None) -> Text:
    """One DataTable cell: plain text, ellipsis-truncated to the width.

    Rich's own width measurement does the truncating (never hand-rolled
    width math); short values pass through unchanged.
    """
    text = Text(str(value), style=style) if style else Text(str(value))
    text.truncate(width, overflow="ellipsis", pad=False)
    return text


def _presence_cell(data: SelectionData, key: str) -> Text:
    """One presence cell from the 08-04 data — render only.

    The four statuses map to the contract formats: present carries the
    thousands-separated exact counts, missing the missing word, unknown
    the gap-filler copy, and the n_audit-absent column state renders the
    documented copy in every cell (SEL-04 boundary: the service already
    decided missing-vs-present; the screen formats only).
    """
    if not data.audit_available:
        return Text(SEL_N_AUDIT_MISSING, style=_STYLE_PRESENCE_FAIL)
    presence = data.presence.get(key)
    if presence is None or presence.status not in (
        PRESENCE_PRESENT, PRESENCE_MISSING,
    ):
        return Text(SEL_PRESENCE_UNKNOWN, style=_STYLE_PRESENCE_UNKNOWN)
    if presence.status == PRESENCE_MISSING:
        return Text(SEL_PRESENCE_MISSING, style=_STYLE_PRESENCE_FAIL)
    train, dev, test = presence.rows or (0, 0, 0)
    return Text(
        SEL_PRESENCE_PRESENT.format(
            train=f"{train:,}", dev=f"{dev:,}", test=f"{test:,}",
        ),
        style=_STYLE_PRESENCE_PASS,
    )


def _preset_label(option: PresetOption) -> str:
    """The menu label for one preset option (derived ids map to copy)."""
    if option.kind == "custom":
        return option.name or option.id
    return {
        "tier-1": SEL_PRESET_TIER_1,
        "tier-2": SEL_PRESET_TIER_2,
        "all": SEL_PRESET_ALL,
    }.get(option.id, option.id)


# ===== Modals (ModalScreen — app/screen bindings blocked, Pitfall 11) =====


class PresetModal(ModalScreen):
    """The preset picker: a SelectionList of the derived + custom presets.

    SelectionList per the UI-SPEC Auto-Selected Default #13; the operator
    highlights a preset and presses enter (a toggle-to-selected in the
    widget's own semantics) — the first toggle applies the preset and
    closes the modal. The empty-customs entry renders as a dim line with
    the save-flow hint.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, options: Sequence[PresetOption],
                 customs_empty: bool, load_error: "str | None",
                 on_apply: "Callable[[PresetOption], None]", **kwargs):
        super().__init__(**kwargs)
        self._options = tuple(options)
        self._customs_empty = customs_empty
        self._load_error = load_error
        self._on_apply = on_apply

    def compose(self) -> ComposeResult:
        with Vertical(id="preset-box", classes="modal-box"):
            if self._load_error:
                yield Static(self._load_error, id="preset-load-error")
            yield SelectionList(
                *(Selection(_preset_label(option), option)
                  for option in self._options),
                id="preset-list",
            )
            if self._customs_empty:
                yield Static(SEL_PRESET_NO_CUSTOMS, id="preset-no-customs")
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#preset-box", Vertical).border_title = (
            SEL_PRESET_TITLE
        )

    def on_selection_list_selection_toggled(
            self, event: SelectionList.SelectionToggled) -> None:
        """A toggle applies the toggled preset and closes (first toggle)."""
        self.dismiss()
        self._on_apply(event.selection.value)


class TemplateMenuModal(ModalScreen):
    """The template menu: import / export / tier-convert (ListView)."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, on_choice: "Callable[[str], None]", **kwargs):
        super().__init__(**kwargs)
        self._on_choice = on_choice

    def compose(self) -> ComposeResult:
        with Vertical(id="template-menu-box", classes="modal-box"):
            yield ListView(
                ListItem(Static(SEL_TEMPLATE_MENU_IMPORT), id="tpl-import"),
                ListItem(Static(SEL_TEMPLATE_MENU_EXPORT), id="tpl-export"),
                ListItem(Static(SEL_TEMPLATE_MENU_TIERS), id="tpl-tiers"),
                id="template-menu-list",
            )
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#template-menu-box", Vertical).border_title = (
            SEL_TEMPLATE_TITLE
        )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Route the chosen menu entry; the menu dismisses itself."""
        action = {
            "tpl-import": "import",
            "tpl-export": "export",
            "tpl-tiers": "tiers",
        }.get(str(event.item.id))
        self.dismiss()
        if action is not None:
            self._on_choice(action)


class PathInputModal(ModalScreen):
    """A titled path/name input modal with a fail-closed problem view.

    ``on_submit(path)`` returns None on success (the modal dismisses) or
    a problems sequence — the modal then renders the numbered collect-all
    list and stays open (nothing was applied; the operator escapes).
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, title: str, placeholder: str,
                 on_submit: "Callable[[str], Sequence[tuple[str, str]] | None]",
                 **kwargs):
        super().__init__(**kwargs)
        self._title = title
        self._placeholder = placeholder
        self._on_submit = on_submit

    def compose(self) -> ComposeResult:
        with Vertical(id="path-input-box", classes="modal-box"):
            yield Input(placeholder=self._placeholder, id="path-input")
            yield Static("", id="path-problems")
            yield Footer()

    def on_mount(self) -> None:
        box = self.query_one("#path-input-box", Vertical)
        box.border_title = self._title
        self.query_one("#path-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Submit the value; render the problems when the call fails."""
        value = event.value.strip()
        if not value:
            return
        problems = self._on_submit(value)
        if problems:
            lines = [SEL_TEMPLATE_PROBLEMS.format(n=len(problems))]
            lines.extend(
                SEL_TEMPLATE_PROBLEM_LINE.format(
                    n=index + 1, location=location, message=message,
                )
                for index, (location, message) in enumerate(problems)
            )
            self.query_one("#path-problems", Static).update("\n".join(lines))
        else:
            self.dismiss()


class ConfirmModal(ModalScreen):
    """An Enter/Esc confirm over one message (the destructive gates).

    The message copy carries the key hints (the Copywriting Contract's
    confirm wording); the bindings themselves stay out of the footer.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "confirm", show=False),
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, message: str,
                 on_confirm: "Callable[[], None]", **kwargs):
        super().__init__(**kwargs)
        self._message = message
        self._on_confirm = on_confirm

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-box", classes="modal-box"):
            yield Static(self._message)
            yield Footer()

    def action_confirm(self) -> None:
        """Enter confirms (the message carries the key hints)."""
        self.dismiss()
        self._on_confirm()


class RowDetailModal(ModalScreen):
    """The row-detail drill-down: every card field, never elided.

    A wrapping, scrolling RichLog (the 08-06 drill-down pattern) renders
    the card's own fields verbatim — long values wrap, they are never
    elided (the table's ellipsis truncation is display-only).
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, entry_key: str, card: dict, **kwargs):
        super().__init__(**kwargs)
        self.entry_key = entry_key
        self._card = card

    def compose(self) -> ComposeResult:
        with Vertical(id="row-detail-box", classes="modal-box"):
            yield RichLog(wrap=True, id="row-detail-log")
            yield Footer()

    def on_mount(self) -> None:
        box = self.query_one("#row-detail-box", Vertical)
        box.border_title = self.entry_key
        log = self.query_one("#row-detail-log", RichLog)
        for field_name, value in self._card.items():
            log.write(f"{field_name}: {value}")


# ===== The screen =====


class SelectionScreen(Screen):
    """The selection screen: tables, filter, mark-set, presets, presence."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("space", "toggle_mark", SEL_MARK_LABEL),
        Binding("m", "switch_list", SEL_SWITCH_LABEL),
        Binding("p", "apply_preset", SEL_PRESET_LABEL),
        Binding("x", "open_templates", SEL_TEMPLATE_LABEL),
        Binding("s", "save_preset", SEL_SAVE_PRESET_LABEL),
        Binding("slash", "focus_filter", SEL_FILTER_KEY_LABEL,
                key_display="/"),
        Binding("v", "open_matrix", SEL_MATRIX_LABEL),
        Binding("enter", "show_detail", ENV_DETAIL_LABEL, show=False),
        Binding("escape", "clear_filter", show=False),
    ]

    class DataLoaded(Message):
        """The worker finished reading the registries + presence (D-03)."""

        def __init__(self, data: SelectionData) -> None:
            self.data = data
            super().__init__()

    def __init__(self,
                 selection_service: "SelectionServiceProtocol | None" = None,
                 marked_models: "set[str] | None" = None,
                 marked_tasks: "set[str] | None" = None, **kwargs):
        super().__init__(**kwargs)
        self._service: SelectionServiceProtocol = (
            selection_service if selection_service is not None
            else SelectionBackend()
        )
        # The shared app-state mark sets (SEL-01: marks live OUTSIDE the
        # table; the composition root injects the same live sets the
        # matrix screen reads).
        self._marked_models: set[str] = (
            marked_models if marked_models is not None else set()
        )
        self._marked_tasks: set[str] = (
            marked_tasks if marked_tasks is not None else set()
        )
        self._data: SelectionData | None = None
        self._view = _MODELS_VIEW
        self._query = ""
        self._view_keys: frozenset[str] = frozenset()

    # ----- properties (the shared sets — Pilot assertions read these) -----

    @property
    def marked_models(self) -> "set[str]":
        """The live shared model mark set."""
        return self._marked_models

    @property
    def marked_tasks(self) -> "set[str]":
        """The live shared task mark set."""
        return self._marked_tasks

    # ----- layout -----

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="selection-title-bar"):
            yield Label(SEL_SCREEN_TITLE_MODELS, id="selection-screen-title")
            yield Label("", id="selection-status")
        with Horizontal(id="selection-filter-bar"):
            yield Label(SEL_FILTER_LABEL, id="selection-filter-label")
            yield Input(placeholder=SEL_FILTER_PLACEHOLDER,
                        id="selection-filter")
            yield Label(SEL_FILTER_COUNT.format(n=0, total=0),
                        id="selection-filter-count")
        yield Label("", id="selection-filter-warning")
        yield DataTable(id="selection-table")
        # compact + no palette hint: the 80-column footer budget (the
        # binding map is dense; ctrl+p keeps working, only the hint hides)
        yield Footer(compact=True, show_command_palette=False)

    def on_mount(self) -> None:
        """Compose the loading state, then the one exclusive read worker."""
        table = self.query_one("#selection-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        self._rebuild_rows()
        table.focus()
        self._update_status_line()
        self._load_data()

    # ----- the exclusive read worker (D-03: the only registry-read site) -----

    @work(exclusive=True, thread=True)
    def _load_data(self) -> None:
        """Read the registries + presence off the event loop."""
        data = self._service.load_selection_data()
        self.post_message(self.DataLoaded(data))

    def on_selection_screen_data_loaded(self, message: DataLoaded) -> None:
        """Rows compose from the loaded snapshot (the loading row clears)."""
        self._data = message.data
        self._apply_filter()
        self._update_status_line()

    # ----- row composition (state rows vs data rows) -----

    def _rebuild_rows(self) -> None:
        """Rebuild the visible table for the current state.

        Marks live in the shared sets — a rebuild can never lose them
        (Pitfall 1); rows re-add with the SAME registry keys.
        """
        table = self.query_one("#selection-table", DataTable)
        columns = (
            _MODEL_COLUMNS if self._view == _MODELS_VIEW
            else _DATASET_COLUMNS
        )
        table.clear(columns=True)
        for column_key, header, width in columns:
            table.add_column(header, key=column_key, width=width)
        self._add_state_or_data_rows(table, columns)

    def _add_state_or_data_rows(self, table: DataTable,
                                columns: tuple) -> None:
        """The loading row (pre-data; the read seam's visible state)."""
        table.add_row(
            "", Text(SEL_LOADING_ROW, style=_STYLE_DIM),
            key=_LOADING_ROW_KEY,
        )

    # ----- helpers (behavior lands in GREEN) -----

    def _apply_filter(self) -> None:
        """Parse + apply the current query; rebuild; update the readout."""

    def _update_status_line(self) -> None:
        """The zero-one-many marked-counts readout (top-right)."""

    # ----- actions (user intent) -----

    def action_toggle_mark(self) -> None:
        """space: toggle the cursor row's mark (the mark column updates)."""

    def action_switch_list(self) -> None:
        """m: toggle the model/dataset table (both mark sets persist)."""

    def action_focus_filter(self) -> None:
        """/: focus the filter Input (k9s type-to-filter)."""

    def action_clear_filter(self) -> None:
        """esc: clear the filter and refocus the table."""

    def action_apply_preset(self) -> None:
        """p: open the preset picker modal."""

    def action_open_templates(self) -> None:
        """x: open the template menu modal."""

    def action_save_preset(self) -> None:
        """s: save the current mark sets as a custom preset."""

    def action_open_matrix(self) -> None:
        """v: push the read-only matrix overview (08-07 Task 2)."""

    def action_show_detail(self) -> None:
        """enter (table unfocused): drill into the cursor row's card."""
