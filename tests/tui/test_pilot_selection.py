"""
Tier-2 Pilot suite for the selection screen (Phase 8, 08-07; SEL-01..04).

Pins the selection surface end-to-end against the REAL ``DnallmMarkTui``
with constructor-injected deterministic fakes (RESEARCH Pattern 7; the
``SelectionServiceProtocol`` seam — no registry file, priorities file, or
template file is ever touched by a faked run; the env screen boots on a
same-day cache-hit fake so no kernel executes either, D-03):

- boot: the model table renders the mark/model/type/species/size/presence
  columns over three synthetic models, rows keyed on the registry keys;
  ``m`` toggles to the dataset table (its column set) and back; BOTH mark
  sets persist independently across the toggles (SEL-01);
- the spacebar mark-set: the mark column cell updates in place via the
  dedicated-column mechanism, the shared set gains/loses the registry
  key, and the status line renders the zero-one-many readout;
- the k9s filter: the Input rebuilds visible rows through the 08-05
  grammar (the fake delegates parse/apply to the real pure functions over
  fake entries), the (N/total) readout is live, marks survive a
  rebuilt-then-cleared filter, the no-match row renders the documented
  copy, unknown axes warn while valid terms still apply, and esc clears
  + refocuses;
- presets (p): REPLACING semantics — tier-1 marks pair models AND tasks,
  a ghost-name preset warns loudly listing the skipped keys, customs
  apply from the menu, the empty-customs entry renders, toasts fire, and
  the worker's async modal push never opens over the min-size guard
  (WR-06);
- templates (x): a failed import renders the numbered collect-all
  problem list and applies NOTHING; a valid import replaces the marks;
  export/tier-convert write through the service with toasts;
- the save flow (s): the overwrite confirm works both ways (Enter
  overwrites via the service, Esc cancels — nothing saved);
- presence cells (SEL-04): exact thousands-separated counts, the missing
  word, the exact 0 boundary, the unknown gap-filler, and the
  n_audit-absent column copy;
- enter: the row-detail modal renders every card field, long values
  never elided;
- the registry-failure empty state names the path and the app stays
  alive; the loading row covers the read seam (a gated fake, never a
  sleep);
- the real ``SelectionBackend`` (sync tests): the committed registries
  load 62/50 with presence from the committed n_audit, registry failures
  degrade to the error state, the preset menu derives over the committed
  priorities with customs under a tmp config root, and template
  import/export round-trips through the strict D-07 schema.

Pilot discipline (08-RESEARCH Pattern 7 / Pitfall 7): ``await
pilot.pause()`` before every assertion; worker completion is awaited via
``app.workers.wait_for_complete()``; the loading-state fake gates on a
``threading.Event`` — deterministic, never a timed sleep.
"""

import json
import re
import threading
from pathlib import Path

import pytest
from env_smoke import CheckResult
from rich.text import Text
from textual.keys import _character_to_key
from textual.widgets import DataTable, RichLog, Static

import tui.screens.about as about_screen_module
import tui.screens.selection as selection_screen_module
import tui.screens.wizard as wizard_screen_module
from tui.app import DnallmMarkTui, HelpModal, MinSizeScreen
from tui.screens.selection import (
    ConfirmModal,
    PathInputModal,
    PresetMenu,
    PresetModal,
    PresetOption,
    RowDetailModal,
    SelectionBackend,
    SelectionData,
    SelectionScreen,
    TemplateImport,
    TemplateMenuModal,
)
from tui.services import registries as registries_service
from tui.services import run_config as run_config_service
from tui.services import selection as selection_service
from tui.services.registries import (
    PRESENCE_MISSING,
    PRESENCE_PRESENT,
    Presence,
)
from tui.strings import (
    APP_HELP_LABEL,
    APP_HELP_ROW,
    APP_QUIT_LABEL,
    ENV_KERNEL_LABELS,
    SEL_COL_CATEGORY,
    SEL_COL_MARK,
    SEL_COL_METRIC,
    SEL_COL_MODEL,
    SEL_COL_PRESENCE,
    SEL_COL_SIZE,
    SEL_COL_SPECIES,
    SEL_COL_TASK,
    SEL_COL_TYPE,
    SEL_ENQUEUE_LABEL,
    SEL_FILTER_COUNT,
    SEL_FILTER_KEY_LABEL,
    SEL_FILTER_NO_MATCH,
    SEL_FILTER_UNKNOWN_AXIS,
    SEL_LOADING_ROW,
    SEL_MARK_LABEL,
    SEL_MATRIX_LABEL,
    SEL_MODEL_PRESENCE_MISSING,
    SEL_MODEL_PRESENCE_PRESENT,
    SEL_N_AUDIT_MISSING,
    SEL_PRESENCE_MISSING,
    SEL_PRESENCE_PRESENT,
    SEL_PRESENCE_UNKNOWN,
    SEL_PRESET_ALL,
    SEL_PRESET_APPLIED,
    SEL_PRESET_LABEL,
    SEL_PRESET_NO_CUSTOMS,
    SEL_PRESET_OVERWRITE_CONFIRM,
    SEL_PRESET_SAVE_FAILED,
    SEL_PRESET_SAVED,
    SEL_PRESET_TIER_1,
    SEL_PRESET_TIER_2,
    SEL_PRESET_UNKNOWN_KEYS,
    SEL_REGISTRY_LOAD_FAILED,
    SEL_SAVE_PRESET_LABEL,
    SEL_STATUS_LINE,
    SEL_SWITCH_LABEL,
    SEL_TEMPLATE_EXPORTED,
    SEL_TEMPLATE_IMPORTED,
    SEL_TEMPLATE_LABEL,
    SEL_TEMPLATE_PROBLEM_LINE,
    SEL_TEMPLATE_PROBLEMS,
    SEL_TEMPLATE_WRITE_FAILED,
    SEL_TOGGLE_LABEL,
    SEL_WIZARD_LABEL,
)

_SCREEN_MODULE_FILE = Path(selection_screen_module.__file__)

# 09-06 i18n close-out: the zero-Chinese grep lock extends to the two
# Phase 9 screen modules (wizard/about) — the scanned module list, the
# assertion itself unchanged.
_GREP_LOCK_MODULES = (
    _SCREEN_MODULE_FILE,
    Path(wizard_screen_module.__file__),
    Path(about_screen_module.__file__),
)

# =====================================================================
# Synthetic registry fixtures (three models, two datasets, mixed presence)
# =====================================================================

_KEY_MODEL_A = "plant-dnamamba-6mer"
_KEY_MODEL_B = "plant-dnabert-6mer"
_KEY_MODEL_C = "PlantHelixSeek"
_TASK_A = "PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation"
_TASK_B = "GUE__emp_H3"

# A card value far than any column — the row-detail never-elide case.
_LONG_CARD_VALUE = "x" * 120

_MODEL_COLUMNS_KEYS = ("mark", "key", "type", "species", "size", "presence")
_DATASET_COLUMNS_KEYS = (
    "mark", "key", "category", "type", "metric", "presence",
)


def _default_data():
    """The standard snapshot: 3 models, 2 datasets, mixed presence."""
    return SelectionData(
        model_entries=(
            {
                "key": _KEY_MODEL_A, "type": "MLM", "species": "plants",
                "size_m": 396.0,
                "card": {
                    "type": "MLM", "species": "plants", "size (M)": 396,
                    "Tokenizer": "6mer", "Mean_token_length": 6,
                    "description": _LONG_CARD_VALUE,
                },
            },
            {
                "key": _KEY_MODEL_B, "type": "MLM", "species": "plants",
                "size_m": 86.0,
                "card": {"type": "MLM", "species": "plants",
                         "size (M)": 86, "Tokenizer": "6mer"},
            },
            {
                "key": _KEY_MODEL_C, "type": "DL", "species": "plants",
                "size_m": 151.0,
                "card": {"type": "DL", "species": "plants",
                         "size (M)": 151},
            },
        ),
        dataset_entries=(
            {
                "key": _TASK_A, "category": "Plants", "type": "binary",
                "metric": "f1",
                "card": {"Category": "Plants", "type": "binary",
                         "metric": "f1"},
            },
            {
                "key": _TASK_B, "category": "Animals", "type": "binary",
                "metric": "f1",
                "card": {"Category": "Animals", "type": "binary",
                         "metric": "f1"},
            },
        ),
        presence={
            _TASK_A: Presence(
                status=PRESENCE_PRESENT, rows=(743095, 109717, 106227),
            ),
            _TASK_B: Presence(status=PRESENCE_MISSING, rows=None),
        },
        # DCL-02 (261014-dcl): the models-column live presence — one of
        # each status (A downloaded, B not, C unknown — its card carries
        # no Model_path).
        model_presence={
            _KEY_MODEL_A: selection_service.MODEL_PRESENCE_PRESENT,
            _KEY_MODEL_B: selection_service.MODEL_PRESENCE_MISSING,
            _KEY_MODEL_C: selection_service.MODEL_PRESENCE_UNKNOWN,
        },
    )


def _default_presets():
    """The standard menu: tier-1 pairs, a ghost-name tier-2, all."""
    return (
        PresetOption(
            id="tier-1", kind="derived", name=None,
            models=(_KEY_MODEL_A, _KEY_MODEL_C), tasks=(_TASK_A,),
        ),
        PresetOption(
            id="tier-2", kind="derived", name=None,
            models=("GENERanno-eukaryote-0.5b-base",), tasks=(),
            unknown_keys=("GENERanno-eukaryote-0.5b-base",),
        ),
        PresetOption(
            id="all", kind="derived", name=None,
            models=(_KEY_MODEL_A, _KEY_MODEL_B, _KEY_MODEL_C),
            tasks=(_TASK_A, _TASK_B),
        ),
    )


_IMPORT_BAD = TemplateImport(
    ok=False,
    problems=(
        ("/models", "'models' is a required property"),
        ("/seeds/0", "42.5 is not of type 'integer'"),
    ),
)
_IMPORT_GOOD = TemplateImport(
    ok=True, models=(_KEY_MODEL_B,), tasks=(_TASK_B,),
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


class FakeSelectionService:
    """Deterministic selection-service fake (the injection seam's fake side).

    ``parse_filter``/``apply_filter`` delegate to the REAL 08-05 pure
    functions — the screen's filter wiring is exercised over the genuine
    grammar with fake entries (the plan's "apply_filter (fake entries)").
    Everything else is canned: fixed data snapshot, fixed preset menu
    (customs appended sorted by name), path-keyed import outcomes, and
    call recorders for the export/save flows.
    """

    def __init__(self, data=None, presets=None, customs=None,
                 load_error=None, import_results=None, load_gate=None):
        self.data = data if data is not None else _default_data()
        self.presets = tuple(presets) if presets else _default_presets()
        self.customs = dict(customs) if customs else {}
        self.load_error = load_error
        self.import_results = dict(import_results) if import_results else {
            "bad-template.json": _IMPORT_BAD,
            "good-template.json": _IMPORT_GOOD,
        }
        self.load_gate = load_gate
        self.load_calls = 0
        self.export_calls = []
        self.tiers_calls = []
        self.save_calls = []

    def load_selection_data(self):
        self.load_calls += 1
        if self.load_gate is not None:
            self.load_gate.wait(timeout=10)  # deterministic gate, no sleep
        return self.data

    def preset_menu(self):
        options = list(self.presets)
        options.extend(
            PresetOption(
                id=f"custom:{name}", kind="custom", name=name,
                models=tuple(value["models"]),
                tasks=tuple(value["tasks"]),
            )
            for name, value in sorted(self.customs.items())
        )
        return PresetMenu(options=tuple(options), load_error=self.load_error)

    def custom_names(self):
        return tuple(sorted(self.customs))

    def save_preset(self, name, models, tasks):
        self.save_calls.append((name, sorted(models), sorted(tasks)))
        self.customs[name] = {"models": sorted(models), "tasks": sorted(tasks)}

    def parse_filter(self, query):
        return selection_service.parse_filter_query(query)

    def apply_filter(self, entries, parsed):
        return selection_service.apply_filter(entries, parsed.terms)

    def import_template(self, path):
        return self.import_results.get(path, TemplateImport(
            ok=False,
            problems=((path, f"template file not found: {path}"),),
        ))

    def export_template(self, path, models, tasks):
        self.export_calls.append((path, sorted(models), sorted(tasks)))

    def export_tiers(self, path, models, tasks):
        self.tiers_calls.append((path, sorted(models), sorted(tasks)))


# =====================================================================
# Helpers
# =====================================================================

def _cell(value):
    """Plain text of a DataTable cell (cells carry rich Text styles)."""
    return value.plain if isinstance(value, Text) else str(value)


def _row(table, index):
    """A row's cell texts as plain strings."""
    return [_cell(cell) for cell in table.get_row_at(index)]


def _row_keys(table):
    """The stable row keys, in row order (the registry-key contract)."""
    return [str(key.value) for key in table.rows]


def _headers(table, column_keys):
    """The rendered column-header labels for the given column keys."""
    return [str(table.columns[key].label) for key in column_keys]


def _label_text(screen, selector):
    """The current text of a Label/Static (status line, warning, etc.)."""
    content = screen.query_one(selector).content
    return content.plain if isinstance(content, Text) else str(content)


def _toast_messages(app):
    """The active notification messages (the toast assertions)."""
    return [notification.message for notification in app._notifications]


def _app(fake):
    """The real app with the cache-hit env fake + the selection fake."""
    return DnallmMarkTui(
        env_check_service=_EnvCacheHitFake(),
        selection_service=fake,
    )


async def _open_selection(pilot, app):
    """Push the selection screen and deterministically await its load."""
    app.push_screen(app.build_selection_screen())
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()


async def _type(pilot, text):
    """Type text into the focused Input, one key per character.

    Each character goes through textual's own character->key mapping
    (``.`` is the ``full_stop`` key, ``/`` the ``slash`` key, ...) —
    exactly what a physical keypress produces.
    """
    for character in text:
        await pilot.press(_character_to_key(character))
    await pilot.pause()


# =====================================================================
# Pilot tests — boot, mark-set, table toggle (SEL-01)
# =====================================================================

async def test_boot_columns_toggle_and_marks_persist_independently():
    """Boot renders the model columns; m toggles; both mark sets persist."""
    app = _app(FakeSelectionService())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        assert isinstance(screen, SelectionScreen)
        # the shared-set contract: the screen reads the app's live sets
        assert screen.marked_models is app._marked_models
        assert screen.marked_tasks is app._marked_tasks

        table = screen.query_one(DataTable)
        assert table.row_count == 3
        assert _headers(table, _MODEL_COLUMNS_KEYS) == [
            SEL_COL_MARK, SEL_COL_MODEL, SEL_COL_TYPE, SEL_COL_SPECIES,
            SEL_COL_SIZE, SEL_COL_PRESENCE,
        ]
        # rows keyed on the registry keys, registry order (stable keys)
        assert _row_keys(table) == [_KEY_MODEL_A, _KEY_MODEL_B, _KEY_MODEL_C]
        # card-field columns render; the model presence cell renders the
        # LIVE per-model download state (DCL-02 — decided in the service
        # over the effective model root; the fixture marks A present)
        assert _row(table, 0)[:5] == [
            "", _KEY_MODEL_A, "MLM", "plants", "396",
        ]
        assert _row(table, 0)[5] == SEL_MODEL_PRESENCE_PRESENT
        assert _row(table, 1)[5] == SEL_MODEL_PRESENCE_MISSING
        assert _row(table, 2)[5] == SEL_PRESENCE_UNKNOWN

        # space marks the cursor row (the mark column updates in place)
        await pilot.press("space")
        await pilot.pause()
        assert screen.marked_models == {_KEY_MODEL_A}
        assert _row(table, 0)[0] == "✓"

        # m toggles to the dataset table: its column set + its rows
        await pilot.press("m")
        await pilot.pause()
        assert _headers(table, _DATASET_COLUMNS_KEYS) == [
            SEL_COL_MARK, SEL_COL_TASK, SEL_COL_CATEGORY, SEL_COL_TYPE,
            SEL_COL_METRIC, SEL_COL_PRESENCE,
        ]
        assert _row_keys(table) == [_TASK_A, _TASK_B]
        # the dataset presence cell carries the fake's exact counts
        # (formatting happens only in the screen)
        assert _row(table, 0)[5] == SEL_PRESENCE_PRESENT.format(
            train="743,095", dev="109,717", test="106,227",
        )
        assert _row(table, 1)[5] == SEL_PRESENCE_MISSING

        # the dataset mark set is INDEPENDENT (models still marked)
        await pilot.press("space")
        await pilot.pause()
        assert screen.marked_tasks == {_TASK_A}
        assert screen.marked_models == {_KEY_MODEL_A}

        # m back: the model marks survived the round trip
        await pilot.press("m")
        await pilot.pause()
        assert _row_keys(table) == [
            _KEY_MODEL_A, _KEY_MODEL_B, _KEY_MODEL_C,
        ]
        assert screen.marked_models == {_KEY_MODEL_A}
        assert screen.marked_tasks == {_TASK_A}
        assert _row(table, 0)[0] == "✓"


async def test_spacebar_mark_toggle_and_status_line_zero_one_many():
    """space toggles the cursor row; the status readout covers 0/1/many."""
    app = _app(FakeSelectionService())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        table = screen.query_one(DataTable)

        # zero
        assert _label_text(screen, "#selection-status") == (
            SEL_STATUS_LINE.format(
                n=0, models_total=3, m=0, tasks_total=2,
            )
        )
        # one
        await pilot.press("space")
        await pilot.pause()
        assert screen.marked_models == {_KEY_MODEL_A}
        assert _label_text(screen, "#selection-status") == (
            SEL_STATUS_LINE.format(
                n=1, models_total=3, m=0, tasks_total=2,
            )
        )
        # many
        await pilot.press("down")
        await pilot.press("space")
        await pilot.pause()
        assert screen.marked_models == {_KEY_MODEL_A, _KEY_MODEL_B}
        assert _label_text(screen, "#selection-status") == (
            SEL_STATUS_LINE.format(
                n=2, models_total=3, m=0, tasks_total=2,
            )
        )
        # space again unmarks (the toggle is symmetric)
        await pilot.press("space")
        await pilot.pause()
        assert screen.marked_models == {_KEY_MODEL_A}
        assert _row(table, 1)[0] == ""


# =====================================================================
# Pilot tests — the k9s filter (SEL-01)
# =====================================================================

async def test_filter_rebuilds_rows_and_marks_survive_the_round_trip():
    """A rebuilt-then-cleared filter leaves marks intact; esc refocuses."""
    app = _app(FakeSelectionService())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        table = screen.query_one(DataTable)

        # mark first, then filter — the mark must survive the rebuild
        await pilot.press("space")
        await pilot.pause()
        assert screen.marked_models == {_KEY_MODEL_A}

        await pilot.press("slash")
        await pilot.pause()
        await _type(pilot, "mlm")
        assert _row_keys(table) == [_KEY_MODEL_A, _KEY_MODEL_B]
        assert _label_text(screen, "#selection-filter-count") == (
            SEL_FILTER_COUNT.format(n=2, total=3)
        )
        # the marked row carries its mark through the rebuild
        assert _row(table, 0)[0] == "✓"

        # narrowing further keeps the mark set untouched
        await _type(pilot, " dnabert")
        assert _row_keys(table) == [_KEY_MODEL_B]
        assert screen.marked_models == {_KEY_MODEL_A}

        # esc clears the filter and refocuses the table
        await pilot.press("escape")
        await pilot.pause()
        assert screen.query_one("#selection-filter").value == ""
        assert _row_keys(table) == [
            _KEY_MODEL_A, _KEY_MODEL_B, _KEY_MODEL_C,
        ]
        assert screen.marked_models == {_KEY_MODEL_A}
        assert _row(table, 0)[0] == "✓"
        # the table is focused again: space marks through the table cursor
        await pilot.press("space")
        await pilot.pause()
        assert screen.marked_models == set()  # cursor back on row 0 (marked)


async def test_filter_no_match_renders_the_documented_row():
    """Zero matches render the no-match row with the Esc hint — never a
    blank table."""
    app = _app(FakeSelectionService())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        table = screen.query_one(DataTable)

        await pilot.press("slash")
        await pilot.pause()
        await _type(pilot, "zzz-no-match")
        assert table.row_count == 1
        assert _row(table, 0)[1] == SEL_FILTER_NO_MATCH.format(total=3)
        assert _label_text(screen, "#selection-filter-count") == (
            SEL_FILTER_COUNT.format(n=0, total=3)
        )
        # the no-match row is never a mark target
        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("space")
        await pilot.pause()
        assert screen.marked_models == {_KEY_MODEL_A}


async def test_filter_unknown_axis_warns_while_valid_terms_still_apply():
    """An unknown axis renders the warning line; valid terms still filter."""
    app = _app(FakeSelectionService())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        table = screen.query_one(DataTable)

        await pilot.press("slash")
        await pilot.pause()
        await _type(pilot, "bogus=1 mlm")
        # the valid term still applied
        assert _row_keys(table) == [_KEY_MODEL_A, _KEY_MODEL_B]
        # the warning line names the axis and the known-axis vocabulary
        assert _label_text(screen, "#selection-filter-warning") == (
            SEL_FILTER_UNKNOWN_AXIS.format(
                axis="bogus", axes="category, metric, size, species, type",
            )
        )
        # clearing the query clears the warning
        await pilot.press("escape")
        await pilot.pause()
        assert _label_text(screen, "#selection-filter-warning") == ""


# =====================================================================
# Pilot tests — presets (SEL-02)
# =====================================================================

async def test_preset_modal_replaces_both_mark_sets_with_toast():
    """tier-1 REPLACES both mark sets (pair models AND tasks) + toast."""
    app = _app(FakeSelectionService())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        table = screen.query_one(DataTable)

        # pre-existing marks must be REPLACED, not merged
        await pilot.press("down")
        await pilot.press("space")
        await pilot.pause()
        assert screen.marked_models == {_KEY_MODEL_B}

        await pilot.press("p")
        await app.workers.wait_for_complete()  # the menu read is a worker (WR-04)
        await pilot.pause()
        assert isinstance(app.screen, PresetModal)
        modal = app.screen
        # the empty-customs entry renders with the save-flow hint
        assert str(
            modal.query_one("#preset-no-customs", Static).content
        ) == SEL_PRESET_NO_CUSTOMS
        preset_list = modal.query_one("#preset-list")
        prompts = [str(option.prompt) for option in preset_list.options]
        assert prompts == [
            SEL_PRESET_TIER_1, SEL_PRESET_TIER_2, SEL_PRESET_ALL,
        ]

        # enter applies the highlighted tier-1 preset and closes
        await pilot.press("enter")
        await pilot.pause()
        assert not isinstance(app.screen, PresetModal)
        assert screen.marked_models == {_KEY_MODEL_A, _KEY_MODEL_C}
        assert screen.marked_tasks == {_TASK_A}
        # the mark column re-rendered for the new sets
        assert _row(table, 0)[0] == "✓"
        assert _row(table, 1)[0] == ""
        assert _row(table, 2)[0] == "✓"
        # the success toast fired with the preset label and both counts
        assert SEL_PRESET_APPLIED.format(
            preset=SEL_PRESET_TIER_1, n=2, m=1,
        ) in _toast_messages(app)
        # the status line reflects the applied preset
        assert _label_text(screen, "#selection-status") == (
            SEL_STATUS_LINE.format(
                n=2, models_total=3, m=1, tasks_total=2,
            )
        )


async def test_preset_unknown_keys_warn_loudly_and_skip():
    """A ghost-name preset warns listing the skipped keys; marks replace."""
    app = _app(FakeSelectionService())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen

        await pilot.press("space")
        await pilot.pause()
        assert screen.marked_models == {_KEY_MODEL_A}

        # tier-2 (one down) carries only the ghost model name
        await pilot.press("p")
        await app.workers.wait_for_complete()  # the menu read is a worker (WR-04)
        await pilot.pause()
        await pilot.press("down")
        await pilot.press("enter")
        await pilot.pause()
        assert not isinstance(app.screen, PresetModal)
        # every tier-2 key was unknown -> skipped: the model set is empty
        assert screen.marked_models == set()
        assert SEL_PRESET_UNKNOWN_KEYS.format(
            n=1, keys="GENERanno-eukaryote-0.5b-base",
        ) in _toast_messages(app)


async def test_custom_preset_applies_from_the_menu():
    """A saved custom preset restores both sets as saved."""
    fake = FakeSelectionService(customs={
        "my-preset": {"models": [_KEY_MODEL_B], "tasks": [_TASK_B]},
    })
    app = _app(fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen

        await pilot.press("p")
        await app.workers.wait_for_complete()  # the menu read is a worker (WR-04)
        await pilot.pause()
        modal = app.screen
        # no empty-customs entry when customs exist; the custom is last
        assert not list(modal.query("#preset-no-customs"))
        prompts = [
            str(option.prompt)
            for option in modal.query_one("#preset-list").options
        ]
        assert prompts[-1] == "my-preset"

        # three downs to the custom, enter applies it
        await pilot.press("down")
        await pilot.press("down")
        await pilot.press("down")
        await pilot.press("enter")
        await pilot.pause()
        assert screen.marked_models == {_KEY_MODEL_B}
        assert screen.marked_tasks == {_TASK_B}
        assert SEL_PRESET_APPLIED.format(
            preset="my-preset", n=1, m=1,
        ) in _toast_messages(app)


async def test_preset_menu_load_runs_off_the_event_loop():
    """WR-04/T-08-07: the preset-menu read (both registries, the
    priorities file, presets.json) runs in the worker, never on the
    event loop — a blocked menu load leaves the UI responsive and the
    modal opens only after the read completes."""
    gate = threading.Event()

    class _GatedMenuFake(FakeSelectionService):
        """preset_menu blocks until the gate opens (a cold cache or a
        network-mounted home, deterministically — never a timed sleep)."""

        def preset_menu(self):
            gate.wait(timeout=10)
            return super().preset_menu()

    app = _app(_GatedMenuFake())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        table = screen.query_one(DataTable)

        await pilot.press("p")
        await pilot.pause()
        # the menu read is in flight in the worker: no modal yet, and
        # the event loop keeps processing keys (the m toggle renders —
        # the T-08-07 responsiveness proof)
        assert not isinstance(app.screen, PresetModal), (
            "the modal must wait for the worker's menu"
        )
        await pilot.press("m")
        await pilot.pause()
        assert _row_keys(table) == [_TASK_A, _TASK_B], (
            "the UI must stay responsive while the menu loads"
        )

        # the read completes -> the modal opens over the loaded menu
        gate.set()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, PresetModal)


async def test_preset_modal_never_opens_over_the_min_size_guard():
    """WR-06: the WR-04 worker's async PresetMenuLoaded push never opens
    the PresetModal over the min-size guard. The message can arrive while
    the guard is the active screen (this screen sits beneath it, pump
    still running), and a modal pushed over the guard strands it at full
    size on grow (the pop fires only when the guard IS the top screen) —
    so the message is dropped below the grid; the operator re-presses p
    after growing back (the same degraded behavior action_help has)."""
    gate = threading.Event()

    class _GatedMenuFake(FakeSelectionService):
        """preset_menu blocks until the gate opens (deterministic — the
        exact T-08-07 slow read the WR-04 worker exists for: the read is
        still in flight when the terminal shrinks)."""

        def preset_menu(self):
            gate.wait(timeout=10)
            return super().preset_menu()

    app = _app(_GatedMenuFake())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)

        # p at full size: the menu read starts in the worker
        await pilot.press("p")
        await pilot.pause()
        assert not isinstance(app.screen, PresetModal)

        # shrink below the grid while the read is in flight: the guard
        # swaps in (the selection screen sits beneath, pump still running)
        await pilot.resize_terminal(60, 20)
        await pilot.pause()
        assert isinstance(app.screen, MinSizeScreen)

        # the read completes while the guard is up: the message is
        # dropped — no chrome over the guard
        gate.set()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, MinSizeScreen), (
            "no chrome may open over the min-size guard"
        )
        assert not any(
            isinstance(screen, PresetModal) for screen in app.screen_stack
        ), "the preset modal must never land over the min-size guard"

        # growing back restores the selection screen — never the stranded
        # guard at full size
        await pilot.resize_terminal(120, 40)
        await pilot.pause()
        assert isinstance(app.screen, SelectionScreen), (
            "the console must never be stranded on the min-size screen "
            "at full size"
        )
        assert app._min_size_screen is None

        # p works again once above the minimum (the operator re-press)
        await pilot.press("p")
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, PresetModal)


# =====================================================================
# Pilot tests — templates (SEL-03)
# =====================================================================

async def test_template_import_failure_lists_problems_and_applies_nothing():
    """A failed import renders the numbered problem list; NOTHING applies."""
    app = _app(FakeSelectionService())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen

        await pilot.press("space")
        await pilot.pause()
        assert screen.marked_models == {_KEY_MODEL_A}

        await pilot.press("x")
        await pilot.pause()
        assert isinstance(app.screen, TemplateMenuModal)
        await pilot.press("enter")  # the import entry
        await pilot.pause()
        assert isinstance(app.screen, PathInputModal)

        await _type(pilot, "bad-template.json")
        await pilot.press("enter")
        await pilot.pause()
        # the modal STAYS OPEN with the numbered collect-all list
        assert isinstance(app.screen, PathInputModal)
        content = str(app.screen.query_one("#path-problems", Static).content)
        assert content.startswith(SEL_TEMPLATE_PROBLEMS.format(n=2))
        assert SEL_TEMPLATE_PROBLEM_LINE.format(
            n=1, location="/models",
            message="'models' is a required property",
        ) in content
        assert SEL_TEMPLATE_PROBLEM_LINE.format(
            n=2, location="/seeds/0",
            message="42.5 is not of type 'integer'",
        ) in content
        # nothing was applied — the pre-import marks are untouched
        assert screen.marked_models == {_KEY_MODEL_A}
        assert screen.marked_tasks == set()
        # esc closes the modal; the app stays alive
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SelectionScreen)


async def test_template_import_success_applies_marks_with_toast():
    """A valid import replaces the marks and fires the toast."""
    app = _app(FakeSelectionService())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen

        await pilot.press("x")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await _type(pilot, "good-template.json")
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, SelectionScreen)
        assert screen.marked_models == {_KEY_MODEL_B}
        assert screen.marked_tasks == {_TASK_B}
        assert SEL_TEMPLATE_IMPORTED.format(n=1, m=1) in _toast_messages(app)


async def test_template_export_and_tiers_write_through_the_service():
    """Export and tier-convert write the marked sets to the given paths."""
    app = _app(FakeSelectionService())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        fake: FakeSelectionService = app._selection_service

        # mark one model and one task (both sets flow into the export)
        await pilot.press("space")
        await pilot.press("m")
        await pilot.pause()
        await pilot.press("space")
        await pilot.press("m")
        await pilot.pause()
        assert screen.marked_models == {_KEY_MODEL_A}
        assert screen.marked_tasks == {_TASK_A}

        # export (menu entry 2)
        await pilot.press("x")
        await pilot.pause()
        await pilot.press("down")
        await pilot.press("enter")
        await pilot.pause()
        await _type(pilot, "exported.json")
        await pilot.press("enter")
        await pilot.pause()
        assert fake.export_calls == [
            ("exported.json", [_KEY_MODEL_A], [_TASK_A]),
        ]
        assert SEL_TEMPLATE_EXPORTED.format(path="exported.json") in (
            _toast_messages(app)
        )

        # tier conversion (menu entry 3)
        await pilot.press("x")
        await pilot.pause()
        await pilot.press("down")
        await pilot.press("down")
        await pilot.press("enter")
        await pilot.pause()
        await _type(pilot, "tiers.json")
        await pilot.press("enter")
        await pilot.pause()
        assert fake.tiers_calls == [
            ("tiers.json", [_KEY_MODEL_A], [_TASK_A]),
        ]
        assert SEL_TEMPLATE_EXPORTED.format(path="tiers.json") in (
            _toast_messages(app)
        )


async def test_export_to_an_unwritable_path_fails_closed_in_the_modal():
    """CR-02: an OSError export path (e.g. a parent that is a file)
    renders as in-modal problems and the app stays alive — the console
    never crashes on an operator-plausible path."""
    class _UnwritableExportFake(FakeSelectionService):
        """Exports raise like the real backend's atomic_write on an
        unwritable operator path (the review's /dev/null/x.json repro)."""

        def export_template(self, path, models, tasks):
            raise FileExistsError(17, "File exists", "/dev/null")

        def export_tiers(self, path, models, tasks):
            raise FileExistsError(17, "File exists", "/dev/null")

    fake = _UnwritableExportFake()
    app = _app(fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        await pilot.press("space")  # a marked model: a non-empty selection
        await pilot.pause()

        # export (menu entry 2) to the unwritable path
        await pilot.press("x")
        await pilot.pause()
        await pilot.press("down")
        await pilot.press("enter")
        await pilot.pause()
        await _type(pilot, "/dev/null/x.json")
        await pilot.press("enter")
        await pilot.pause()
        # the modal STAYS OPEN with the numbered problem — fail closed,
        # nothing written, the app never crashed
        assert isinstance(app.screen, PathInputModal)
        content = str(app.screen.query_one("#path-problems", Static).content)
        assert content.startswith(SEL_TEMPLATE_PROBLEMS.format(n=1))
        assert SEL_TEMPLATE_PROBLEM_LINE.format(
            n=1, location="/dev/null/x.json",
            message=SEL_TEMPLATE_WRITE_FAILED.format(
                error="FileExistsError: [Errno 17] File exists: '/dev/null'",
            ),
        ) in content
        # esc closes the modal; the app stays alive and responds
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SelectionScreen)
        await pilot.press("m")
        await pilot.pause()
        assert _row_keys(screen.query_one(DataTable)) == [_TASK_A, _TASK_B]

        # the tier conversion degrades the same way (menu entry 3)
        await pilot.press("x")
        await pilot.pause()
        await pilot.press("down")
        await pilot.press("down")
        await pilot.press("enter")
        await pilot.pause()
        await _type(pilot, "/dev/null/t.json")
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, PathInputModal)
        assert str(
            app.screen.query_one("#path-problems", Static).content
        ).startswith(SEL_TEMPLATE_PROBLEMS.format(n=1))


async def test_save_preset_to_an_unwritable_root_warns_and_stays_alive():
    """CR-02: an OSError from the save path degrades to a warning toast —
    the save flow never crashes the console."""
    class _UnwritableSaveFake(FakeSelectionService):
        """save_preset raises like the real atomic_write on a read-only
        config root."""

        def save_preset(self, name, models, tasks):
            raise PermissionError(13, "Permission denied", "/root/.config")

    fake = _UnwritableSaveFake()
    app = _app(fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        await pilot.press("space")
        await pilot.pause()
        await pilot.press("s")
        await pilot.pause()
        await _type(pilot, "mine")
        await pilot.press("enter")
        await pilot.pause()
        # the input modal dismissed; the warning toast fired; app alive
        assert isinstance(app.screen, SelectionScreen)
        assert SEL_PRESET_SAVE_FAILED.format(
            error="PermissionError: [Errno 13] Permission denied: "
                  "'/root/.config'",
        ) in _toast_messages(app)
        # the app stays alive: the table still responds
        await pilot.press("m")
        await pilot.pause()
        assert _row_keys(screen.query_one(DataTable)) == [_TASK_A, _TASK_B]


async def test_save_preset_overwrite_confirm_works_both_ways():
    """s: an existing name confirms; Enter overwrites via the service,
    Esc cancels with nothing saved."""
    fake = FakeSelectionService(customs={
        "existing": {"models": [_KEY_MODEL_C], "tasks": []},
    })
    app = _app(fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen

        await pilot.press("space")
        await pilot.pause()
        assert screen.marked_models == {_KEY_MODEL_A}

        # --- Esc cancels: nothing saved ---
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, PathInputModal)
        await _type(pilot, "existing")
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmModal)
        confirm = app.screen
        assert str(confirm.query_one(Static).content) == (
            SEL_PRESET_OVERWRITE_CONFIRM.format(name="existing")
        )
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SelectionScreen)
        assert fake.save_calls == []

        # --- Enter overwrites via the service ---
        await pilot.press("s")
        await pilot.pause()
        await _type(pilot, "existing")
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmModal)
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, SelectionScreen)
        assert fake.save_calls == [
            ("existing", [_KEY_MODEL_A], []),
        ]
        assert SEL_PRESET_SAVED.format(
            name="existing", n=1, m=0,
        ) in _toast_messages(app)

        # a NEW name saves without any confirm
        await pilot.press("s")
        await pilot.pause()
        await _type(pilot, "fresh")
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, SelectionScreen)
        assert fake.save_calls[-1] == ("fresh", [_KEY_MODEL_A], [])


# =====================================================================
# Pilot tests — the ? help modal over the selection screen (app chrome)
# =====================================================================

async def test_help_modal_opens_on_the_selection_screen():
    """? over the selection screen renders every shown binding row —
    including the ``/`` keycap (a literal Rich would otherwise parse as
    a broken auto-closing markup tag, CR-01) — and never lists the
    hidden enter/escape bindings."""
    app = _app(FakeSelectionService())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        await pilot.press("question_mark")
        await pilot.pause()
        assert isinstance(app.screen, HelpModal), (
            "? must open the help modal over the selection screen "
            "without a markup crash"
        )
        modal = app.screen
        rows = [str(static.content) for static in modal.query(Static)]
        # app rows first, then the screen's shown bindings in declaration
        # order; the / keycap renders as literal text (the row is a rich
        # Text content object, never markup-parsed) and the hidden
        # enter/escape rows never list. The w/e rows joined at 09-06
        # (after the mark/preset bindings, before the auxiliary actions —
        # the migration table's declaration order; the modal auto-reflects
        # the declared surface, the 09-03 chrome-pin-update class). The
        # d row joined at 10-05 (between e and v — D-14's enqueue key).
        assert rows == [
            APP_HELP_ROW.format(key="q", label=APP_QUIT_LABEL),
            APP_HELP_ROW.format(key="?", label=APP_HELP_LABEL),
            APP_HELP_ROW.format(key="space", label=SEL_MARK_LABEL),
            APP_HELP_ROW.format(key="m", label=SEL_SWITCH_LABEL),
            APP_HELP_ROW.format(key="p", label=SEL_PRESET_LABEL),
            APP_HELP_ROW.format(key="x", label=SEL_TEMPLATE_LABEL),
            APP_HELP_ROW.format(key="s", label=SEL_SAVE_PRESET_LABEL),
            APP_HELP_ROW.format(key="/", label=SEL_FILTER_KEY_LABEL),
            APP_HELP_ROW.format(key="w", label=SEL_WIZARD_LABEL),
            APP_HELP_ROW.format(key="e", label=SEL_TOGGLE_LABEL),
            APP_HELP_ROW.format(key="d", label=SEL_ENQUEUE_LABEL),
            APP_HELP_ROW.format(key="v", label=SEL_MATRIX_LABEL),
        ]
        # esc closes back to the selection screen
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SelectionScreen)


# =====================================================================
# Pilot tests — presence cells (SEL-04)
# =====================================================================

async def test_presence_cell_formats_pin_the_contract():
    """Present counts / missing word / exact 0 / unknown / n_audit-absent."""
    data = SelectionData(
        model_entries=_default_data().model_entries,
        dataset_entries=(
            {"key": "task-present-big", "category": "Plants",
             "type": "binary", "metric": "f1", "card": {}},
            {"key": "task-present-zero", "category": "Plants",
             "type": "binary", "metric": "f1", "card": {}},
            {"key": "task-missing", "category": "Plants",
             "type": "binary", "metric": "f1", "card": {}},
            {"key": "task-unknown", "category": "Plants",
             "type": "binary", "metric": "f1", "card": {}},
        ),
        presence={
            "task-present-big": Presence(
                status=PRESENCE_PRESENT, rows=(743095, 109717, 106227),
            ),
            # a present task with a zero-row split shows the exact 0
            "task-present-zero": Presence(
                status=PRESENCE_PRESENT, rows=(0, 5, 3),
            ),
            # the missing flag alone decides missing (service-side; the
            # screen renders what it is fed — no coercion)
            "task-missing": Presence(status=PRESENCE_MISSING, rows=None),
        },
    )
    app = _app(FakeSelectionService(data=data))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        table = screen.query_one(DataTable)

        await pilot.press("m")
        await pilot.pause()
        assert _row(table, 0)[5] == SEL_PRESENCE_PRESENT.format(
            train="743,095", dev="109,717", test="106,227",
        )
        assert _row(table, 1)[5] == SEL_PRESENCE_PRESENT.format(
            train="0", dev="5", test="3",
        )
        assert _row(table, 2)[5] == SEL_PRESENCE_MISSING
        # a key absent from the audit renders the unknown copy
        assert _row(table, 3)[5] == SEL_PRESENCE_UNKNOWN


async def test_presence_column_renders_n_audit_missing_copy():
    """n_audit absent: every presence cell renders the documented copy."""
    data = SelectionData(
        model_entries=_default_data().model_entries,
        dataset_entries=_default_data().dataset_entries,
        presence={},
        audit_available=False,
    )
    app = _app(FakeSelectionService(data=data))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        table = screen.query_one(DataTable)

        await pilot.press("m")
        await pilot.pause()
        for index in range(table.row_count):
            assert _row(table, index)[5] == SEL_N_AUDIT_MISSING
        # the model view is filesystem-driven, NOT n_audit-driven
        # (DCL-02): with no model_presence filled the cells render the
        # shared unknown copy — never the dataset column's n_audit state
        await pilot.press("m")
        await pilot.pause()
        assert _row(table, 0)[5] == SEL_PRESENCE_UNKNOWN


# =====================================================================
# Pilot tests — row detail, registry failure, loading state
# =====================================================================

async def test_enter_opens_row_detail_with_full_card_fields():
    """enter opens the modal; every card field renders, never elided."""
    app = _app(FakeSelectionService())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)

        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, RowDetailModal)
        modal = app.screen
        assert modal.entry_key == _KEY_MODEL_A
        assert modal.query_one("#row-detail-box").border_title == (
            _KEY_MODEL_A
        )
        # every card field rendered, in order — whitespace-normalized
        # containment proves wrapping dropped nothing (wrap, not elide)
        log = modal.query_one("#row-detail-log", RichLog)
        rendered = " ".join(
            "".join(strip.text for strip in log.lines).split()
        )
        card = _default_data().model_entries[0]["card"]
        for field_name, value in card.items():
            needle = f"{field_name}: {value}"
            assert needle in rendered, (
                f"row detail must render {needle!r} verbatim"
            )


async def test_registry_failure_renders_error_state_and_app_stays_alive():
    """A registry-load failure renders the documented row naming the
    path; the other table and the app stay alive."""
    data = SelectionData(
        model_entries=(),
        dataset_entries=_default_data().dataset_entries,
        presence=_default_data().presence,
        models_load_error="/repo/pipeline/models_info.json",
    )
    app = _app(FakeSelectionService(data=data))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        table = screen.query_one(DataTable)

        assert table.row_count == 1
        assert _row(table, 0)[1] == SEL_REGISTRY_LOAD_FAILED.format(
            registry_path="/repo/pipeline/models_info.json",
        )
        # the status line renders zero totals for the failed registry
        assert _label_text(screen, "#selection-status") == (
            SEL_STATUS_LINE.format(
                n=0, models_total=0, m=0, tasks_total=2,
            )
        )
        # the app stays alive: m toggles to the healthy dataset table
        await pilot.press("m")
        await pilot.pause()
        assert _row_keys(table) == [_TASK_A, _TASK_B]
        await pilot.press("m")
        await pilot.pause()
        assert _row(table, 0)[1] == SEL_REGISTRY_LOAD_FAILED.format(
            registry_path="/repo/pipeline/models_info.json",
        )


async def test_loading_row_covers_the_read_seam():
    """The single loading row renders before the data composes (gated)."""
    gate = threading.Event()
    app = _app(FakeSelectionService(load_gate=gate))
    async with app.run_test(size=(120, 40)) as pilot:
        app.push_screen(app.build_selection_screen())
        await pilot.pause()
        screen = app.screen
        table = screen.query_one(DataTable)
        # the loading row is the whole table while the read is in flight
        for _ in range(100):
            await pilot.pause()
            if table.row_count == 1:
                break
        assert _row(table, 0)[1] == SEL_LOADING_ROW
        assert screen.marked_models == set()

        gate.set()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert _row_keys(table) == [
            _KEY_MODEL_A, _KEY_MODEL_B, _KEY_MODEL_C,
        ]


# =====================================================================
# Source-level i18n gate (permanent CI enforcement of the verify gate)
# =====================================================================

def test_screen_module_carries_zero_chinese_literals():
    """I18N-01 single-home: no operator-facing copy outside tui/strings.py."""
    for module_file in _GREP_LOCK_MODULES:
        source = module_file.read_text(encoding="utf-8")
        offenders = re.findall(r"[一-鿿]", source)
        assert not offenders, (
            "Chinese literals must live in tui/strings.py only "
            f"({len(offenders)} found in {module_file.name})"
        )


# =====================================================================
# The real backend adapter (sync — real 08-04/08-05 services, tmp roots)
# =====================================================================

def test_backend_loads_the_committed_registries_and_presence(
        monkeypatch, tmp_path):
    """The real seam: 62/50 entries, presence from the committed n_audit.
    Refresh-stable presence pins (the R-03 follow-up rule: the baseline
    is maintainer-refreshable — 43/50 -> 50/50 landed as a data commit —
    so the asserts cover structure and DEFINITE presence, never a
    specific missing count or key set)."""
    empty_overlay = tmp_path / "custom"
    empty_overlay.mkdir()
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(empty_overlay))
    data = SelectionBackend().load_selection_data()
    assert len(data.model_entries) == 62
    assert len(data.dataset_entries) == 50
    assert data.models_load_error is None
    assert data.datasets_load_error is None
    assert data.audit_available is True
    # every dataset key carries a presence entry, definite for all of
    # them (present or missing — whichever the current baseline says)
    assert set(data.presence) == {
        entry["key"] for entry in data.dataset_entries
    }
    statuses = {presence.status for presence in data.presence.values()}
    assert statuses <= {PRESENCE_PRESENT, PRESENCE_MISSING}
    assert statuses, "at least one dataset presence resolved"
    # DCL-02: model presence covers EVERY model key in the merged+
    # management view, statuses within the three-value vocabulary
    # (structure-only — CI machines differ in which models are on disk)
    assert set(data.model_presence) == {
        entry["key"] for entry in data.model_entries
    }
    assert set(data.model_presence.values()) <= {
        selection_service.MODEL_PRESENCE_PRESENT,
        selection_service.MODEL_PRESENCE_MISSING,
        selection_service.MODEL_PRESENCE_UNKNOWN,
    }
    assert data.model_presence, "at least one model presence resolved"


def test_backend_model_presence_all_missing_under_empty_configured_root(
        monkeypatch, tmp_path):
    """DCL-02 determinism: with DNALLMMARK_TUI_STATE_DIR pointed at a tmp
    state root holding a run_config.json whose model_root is an EMPTY
    tmp dir, every model reads MISSING — on any machine (the run-config
    threading; the committed pipeline models/ dir is never consulted)."""
    empty_root = tmp_path / "empty-model-root"
    empty_root.mkdir()
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setenv("DNALLMMARK_TUI_STATE_DIR", str(state))
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR",
                       str(tmp_path / "custom-overlay"))
    (tmp_path / "custom-overlay").mkdir()
    run_config_service.save_state(run_config_service.RunSpec(
        models=(), tasks=(), model_root=str(empty_root)))

    data = SelectionBackend().load_selection_data()

    assert len(data.model_entries) == 62
    assert set(data.model_presence.values()) == {
        selection_service.MODEL_PRESENCE_MISSING}, (
        "an empty configured root reads every model as missing"
    )


def test_backend_registry_failure_degrades_to_the_error_state(
        monkeypatch, tmp_path):
    """A failing registry read degrades to the error state, never raises."""
    def _raise():
        raise OSError("official registry file missing")

    monkeypatch.setattr(
        registries_service, "load_model_entries", _raise,
    )
    # pin the overlay empty: the healthy-side 50 below pins the COMMITTED
    # registry regardless of any local custom overlay (the WR-05 pin)
    empty_overlay = tmp_path / "custom"
    empty_overlay.mkdir()
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(empty_overlay))
    data = SelectionBackend().load_selection_data()
    assert data.model_entries == ()
    assert data.models_load_error is not None
    assert data.models_load_error.endswith("models_info.json")
    # the OTHER registry still loaded — the app stays alive
    assert len(data.dataset_entries) == 50


def test_backend_preset_menu_over_the_committed_priorities(tmp_path):
    """The menu derives tier-1/tier-2/all; customs round-trip sorted."""
    backend = SelectionBackend(config_dir=str(tmp_path))
    menu = backend.preset_menu()
    assert [option.id for option in menu.options] == [
        "tier-1", "tier-2", "all",
    ]
    assert menu.load_error is None
    tier_1 = menu.options[0]
    assert "plant-dnamamba-6mer" in tier_1.models
    # the committed tier names all exist in the registry — no unknowns
    assert tier_1.unknown_keys == ()
    assert menu.options[1].unknown_keys == ()
    assert menu.options[2].unknown_keys == ()
    assert backend.custom_names() == ()

    # save + reload: the custom joins the menu tail sorted by name
    backend.save_preset("mine", ["plant-dnabert-6mer"], ["GUE__emp_H3"])
    menu_after = backend.preset_menu()
    assert [option.id for option in menu_after.options] == [
        "tier-1", "tier-2", "all", "custom:mine",
    ]
    assert backend.custom_names() == ("mine",)


def test_backend_template_import_and_exports_round_trip(tmp_path):
    """Import validates collect-all; exports are valid by construction."""
    backend = SelectionBackend(config_dir=str(tmp_path))

    good = tmp_path / "good.json"
    good.write_text(json.dumps({
        "schema_version": 1,
        "models": ["plant-dnabert-6mer"],
        "tasks": ["GUE__emp_H3"],
        "seeds": [42], "peft": "none", "config_variant": "default",
    }), encoding="utf-8")
    outcome = backend.import_template(str(good))
    assert outcome.ok
    assert outcome.models == ("plant-dnabert-6mer",)
    assert outcome.tasks == ("GUE__emp_H3",)

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"schema_version": 1, "models": []}),
                   encoding="utf-8")
    outcome_bad = backend.import_template(str(bad))
    assert not outcome_bad.ok
    assert len(outcome_bad.problems) >= 2  # collect-all, never one at a time

    missing = backend.import_template(str(tmp_path / "nope.json"))
    assert not missing.ok
    assert missing.problems  # the load failure surfaces in the same shape

    # export writes a file the import accepts (valid by construction)
    out = tmp_path / "out.json"
    backend.export_template(
        str(out), ["plant-dnabert-6mer"], ["GUE__emp_H3"],
    )
    assert backend.import_template(str(out)).ok
    # the tier conversion writes the priorities cross-product shape
    tiers_path = tmp_path / "tiers.json"
    backend.export_tiers(
        str(tiers_path), ["plant-dnabert-6mer"], ["GUE__emp_H3"],
    )
    tiers = json.loads(tiers_path.read_text(encoding="utf-8"))
    assert tiers == [[
        {"model": "plant-dnabert-6mer", "task": "GUE__emp_H3"},
    ]]


def test_backend_export_to_an_unwritable_path_raises_oserror():
    """CR-02 contract: an operator path whose parent is a file (/dev/null
    on POSIX) fails with OSError from the atomic write — the exact class
    the screen's submit handlers catch and surface in-modal."""
    backend = SelectionBackend()
    with pytest.raises(OSError):
        backend.export_template(
            "/dev/null/x.json", ["plant-dnabert-6mer"], ["GUE__emp_H3"],
        )
    with pytest.raises(OSError):
        backend.export_tiers(
            "/dev/null/x.json", ["plant-dnabert-6mer"], ["GUE__emp_H3"],
        )


def test_backend_parse_and_apply_delegate_to_the_service_grammar():
    """The delegation glue: parse/apply are the pure 08-05 functions."""
    backend = SelectionBackend()
    parsed = backend.parse_filter("type=mlm plant")
    assert backend.apply_filter(
        _default_data().model_entries, parsed,
    ) == [
        _default_data().model_entries[0],
        _default_data().model_entries[1],
    ]
    assert backend.parse_filter("bogus=1").diagnostics[0].axis == "bogus"


# =====================================================================
# Task 3 — the 80-column UI backstops (08-UI-SPEC UI Considerations)
# =====================================================================

#: The real longest registry task key (pipeline/datasets_info.json,
#: verified 2026-10-11): 68 chars — the backstop fixture's long key.
_LONGEST_TASK_KEY = (
    "PlantCAD2_fine_tuning_tasks__cross_species_leaf_absolute_translation"
)


async def test_backstop_longest_task_key_at_80x24():
    """Backstop (08-UI-SPEC UI Considerations, long-text; UAT geometry):
    at 80x24 the longest real registry task key causes no wrap-induced
    row-height change — every data row stays height 1 — and the key cell
    carries the FULL key; the over-budget table h-scrolls (the matrix
    precedent) and the presence column stays reachable by scrolling
    right."""
    task_keys = tuple(
        _LONGEST_TASK_KEY if index == 0 else f"GUE__task_{index}"
        for index in range(12)  # enough rows to force the v-scrollbar
    )
    data = SelectionData(
        model_entries=_default_data().model_entries,
        dataset_entries=tuple(
            {"key": key, "category": "Plants", "type": "binary",
             "metric": "f1", "card": {}}
            for key in task_keys
        ),
        presence={
            key: Presence(
                status=PRESENCE_PRESENT, rows=(743095, 109717, 106227),
            )
            for key in task_keys
        },
    )
    app = _app(FakeSelectionService(data=data))
    async with app.run_test(size=(80, 24)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        table = screen.query_one(DataTable)

        # the dataset table is the long-key surface
        await pilot.press("m")
        await pilot.pause()
        assert table.row_count == 12

        # no wrap-induced row-height change: every data row stays height 1
        # (the over-budget table clips + h-scrolls; it never wraps)
        heights = {row.height for row in table.rows.values()}
        assert heights == {1}, "long keys must never wrap a row taller"

        # the UAT geometry: the key column fits the longest real key
        # exactly (68) and the total budget (widths + per-column padding
        # + the scrollbar) is 128 — past 80, so the table h-scrolls
        widths = [
            table.columns[key].width for key in _DATASET_COLUMNS_KEYS
        ]
        assert table.columns["key"].width == 68
        assert sum(widths) + 2 * len(widths) + 2 == 128
        assert table.max_scroll_x > 0, (
            "the 128-wide table must h-scroll at the 80-column grid"
        )

        # the key cell carries the FULL key — no ellipsis (the DataTable
        # clips the display on narrow terminals; the full value stays in
        # the enter row detail)
        key_cell = _row(table, 0)[1]
        assert key_cell == _LONGEST_TASK_KEY
        assert Text(key_cell).cell_len == 68  # the dataset key-column budget

        # the viewport origin renders the key column header...
        from textual.geometry import Region
        strips = table.render_lines(
            Region(0, 0, table.size.width, min(table.size.height, 3)),
        )
        header = "".join(segment.text for segment in strips[0])
        assert SEL_COL_TASK in header

        # ...and the presence column stays reachable: scrolled to the
        # right end its header and glyphs render in the viewport
        table.scroll_to(x=table.max_scroll_x, animate=False)
        await pilot.pause()
        strips = table.render_lines(
            Region(0, 0, table.size.width, min(table.size.height, 3)),
        )
        header_right = "".join(segment.text for segment in strips[0])
        assert SEL_COL_PRESENCE in header_right
        first_data_row = "".join(segment.text for segment in strips[1])
        assert "✓" in first_data_row


async def test_backstop_longest_task_key_fits_in_full_at_160():
    """Regression (UAT feedback, 「部分数据集名称过长看不到全部」): on a
    normal wide terminal (160x40) the longest real registry task key
    renders IN FULL in its key cell — no ellipsis, the whole table fits
    without h-scroll — and the h-scroll geometry never disturbs the
    min-size guard (below 80x24 the guard still takes over)."""
    task_keys = tuple(
        _LONGEST_TASK_KEY if index == 0 else f"GUE__task_{index}"
        for index in range(12)  # enough rows to force the v-scrollbar
    )
    data = SelectionData(
        model_entries=_default_data().model_entries,
        dataset_entries=tuple(
            {"key": key, "category": "Plants", "type": "binary",
             "metric": "f1", "card": {}}
            for key in task_keys
        ),
        presence={
            key: Presence(
                status=PRESENCE_PRESENT, rows=(743095, 109717, 106227),
            )
            for key in task_keys
        },
    )
    app = _app(FakeSelectionService(data=data))
    async with app.run_test(size=(160, 40)) as pilot:
        await _open_selection(pilot, app)
        table = app.screen.query_one(DataTable)

        # the dataset table is the long-key surface
        await pilot.press("m")
        await pilot.pause()
        assert table.row_count == 12

        # the 128-wide table fits a 160-column terminal whole — no
        # h-scroll, and both edge columns render on-screen
        assert table.max_scroll_x == 0, (
            "the 128-wide table must fit a 160-column terminal"
        )
        from textual.geometry import Region
        strips = table.render_lines(
            Region(0, 0, table.size.width, min(table.size.height, 3)),
        )
        header = "".join(segment.text for segment in strips[0])
        assert SEL_COL_TASK in header
        assert SEL_COL_PRESENCE in header

        # the longest real key renders in full — no ellipsis
        key_cell = _row(table, 0)[1]
        assert key_cell == _LONGEST_TASK_KEY
        assert "…" not in key_cell
        assert Text(key_cell).cell_len == 68

        # the h-scroll geometry never disturbs the min-size guard:
        # shrink below the grid and the guard takes over; grow back and
        # the selection screen restores (the WR-06 semantics)
        await pilot.resize_terminal(60, 20)
        await pilot.pause()
        assert isinstance(app.screen, MinSizeScreen)
        await pilot.resize_terminal(160, 40)
        await pilot.pause()
        assert isinstance(app.screen, SelectionScreen)
        assert app._min_size_screen is None


# test_backstop_footer_renders_every_binding_label_at_80 was REMOVED by
# the 09-03 nav-shell migration: the selection screen no longer yields
# the Textual Footer (the bottom bar owns the keycap row). The successor
# assertions live in tests/tui/test_pilot_nav_shell.py — the 80-column
# clip-with-ellipsis policy and the ? help-modal completeness backstop
# (every shown binding listed, the CJK labels untruncated in the modal
# rows).
