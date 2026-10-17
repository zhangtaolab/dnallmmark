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
  load 59/50 with presence from the committed n_audit, registry failures
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
    APP_LANGUAGE_TOGGLE_LABEL,
    APP_QUIT_LABEL,
    ENV_KERNEL_LABELS,
    SEL_COL_COMPAT,
    SEL_COL_DOWNLOAD,
    SEL_COL_MARK,
    SEL_COL_MODEL,
    SEL_COL_SIZE,
    SEL_COL_SPECIES,
    SEL_COL_TYPE,
    SEL_COMPAT_ADAPTED,
    SEL_COMPAT_CUSTOM,
    SEL_COMPAT_UNADAPTED,
    SEL_FILTER_COUNT_POOLED,
    SEL_FILTER_KEY_LABEL,
    SEL_FILTER_NO_MATCH,
    SEL_FILTER_UNKNOWN_AXIS,
    SEL_LOADING_ROW,
    SEL_MARK_LABEL,
    SEL_MATRIX_LABEL,
    SEL_MODEL_DL_MANUAL,
    SEL_MODEL_DOWNLOAD_LABEL,
    SEL_MODEL_PRESENCE_MISSING,
    SEL_MODEL_PRESENCE_PRESENT,
    SEL_POOL_ADAPTED,
    SEL_POOL_ALL,
    SEL_POOL_TOGGLE_LABEL,
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
_KEY_MODEL_D = "GENA-LM-yeast"
_TASK_A = "PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation"
_TASK_B = "GUE__emp_H3"

# A card value far than any column — the row-detail never-elide case.
_LONG_CARD_VALUE = "x" * 120

_MODEL_COLUMNS_KEYS = (
    "mark", "key", "type", "species", "size", "compat", "download",
)


def _default_data():
    """The standard snapshot: 4 models, 2 datasets, mixed presence.

    MLC-02 (261014-mlc): the compat fixture covers the pool semantics —
    A/B adapted (A downloaded, B the d-able missing row), C UNADAPTED
    (hidden by the default pool, revealed by t), D adapted with the
    no-Model_path unknown presence.
    """
    return SelectionData(
        model_entries=(
            {
                "key": _KEY_MODEL_A, "type": "MLM", "species": "plants",
                "size_m": 396.0,
                "card": {
                    "type": "MLM", "species": "plants", "size (M)": 396,
                    "Model_path": "models/plant-dnamamba-6mer",
                    "Tokenizer": "6mer", "Mean_token_length": 6,
                    "description": _LONG_CARD_VALUE,
                },
            },
            {
                "key": _KEY_MODEL_B, "type": "MLM", "species": "plants",
                "size_m": 86.0,
                "card": {"type": "MLM", "species": "plants",
                         "size (M)": 86, "Tokenizer": "6mer",
                         "Model_path": "models/plant-dnabert-6mer"},
            },
            {
                "key": _KEY_MODEL_C, "type": "DL", "species": "plants",
                "size_m": 151.0,
                "card": {"type": "DL", "species": "plants",
                         "size (M)": 151,
                         "Model_path": "models/PlantHelixSeek"},
            },
            {
                "key": _KEY_MODEL_D, "type": "DL", "species": "yeast",
                "size_m": 86.0,
                "card": {"type": "DL", "species": "yeast",
                         "size (M)": 86},
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
        # DCL-02 (261014-dcl): the models-column live presence — A
        # downloaded, B the d-able missing row, C missing (manual
        # placement — unadapted), D unknown (its card carries no
        # Model_path).
        model_presence={
            _KEY_MODEL_A: selection_service.MODEL_PRESENCE_PRESENT,
            _KEY_MODEL_B: selection_service.MODEL_PRESENCE_MISSING,
            _KEY_MODEL_C: selection_service.MODEL_PRESENCE_MISSING,
            _KEY_MODEL_D: selection_service.MODEL_PRESENCE_UNKNOWN,
        },
        # MLC-02 (261014-mlc): the committed dnallm compat verdict shape —
        # A/B/D adapted (the default pool), C unadapted (t reveals it).
        compat={
            _KEY_MODEL_A: {"dnllm_adapted": True,
                           "modelscope": "zhangtaolab/plant-dnamamba-6mer",
                           "channel": "modelscope-slot"},
            _KEY_MODEL_B: {"dnllm_adapted": True,
                           "modelscope": "zhangtaolab/plant-dnabert-6mer",
                           "channel": "modelscope-slot"},
            _KEY_MODEL_C: {"dnllm_adapted": False, "modelscope": None,
                           "channel": None},
            _KEY_MODEL_D: {"dnllm_adapted": True,
                           "modelscope": "lgq12697/gena-lm-bert-base-yeast",
                           "channel": "modelscope-mirror"},
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
            models=(_KEY_MODEL_A, _KEY_MODEL_B, _KEY_MODEL_C, _KEY_MODEL_D),
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

    def storage_rows(self):
        # F4W-04 (261014-f4w): frozen display rows — no filesystem scan.
        from tui.services.run_config import StorageRow

        return (
            StorageRow("model_root", "/golden/models", True),
            StorageRow("dataset_root", "/golden/datasets", False),
            StorageRow("output_root", "/golden/finetuned", True),
            StorageRow("log_dir", "/golden/logs", False),
            StorageRow("cache_dir", "/golden/cache", True),
        )

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

async def test_boot_models_only_columns_pool_and_marks_persist():
    """Boot renders the models-only 适配/下载 columns; the DEFAULT pool
    hides the unadapted official; t reveals it honestly marked; marks
    survive the pool round trip (MLC-02, the 2026-10-14 slot split)."""
    app = _app(FakeSelectionService())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        assert isinstance(screen, SelectionScreen)
        # the shared-set contract: the screen reads the app's live sets
        assert screen.marked_models is app._marked_models
        assert screen.marked_tasks is app._marked_tasks

        table = screen.query_one(DataTable)
        # the DEFAULT pool: adapted officials (C — unadapted — hidden)
        assert table.row_count == 3
        assert _headers(table, _MODEL_COLUMNS_KEYS) == [
            SEL_COL_MARK, SEL_COL_MODEL, SEL_COL_TYPE, SEL_COL_SPECIES,
            SEL_COL_SIZE, SEL_COL_COMPAT, SEL_COL_DOWNLOAD,
        ]
        assert _row_keys(table) == [_KEY_MODEL_A, _KEY_MODEL_B, _KEY_MODEL_D]
        # rows keyed on the registry keys, registry order (stable keys);
        # card-field columns render; the 适配 cells render the verdict,
        # the 下载 cells the honest four-state vocabulary (A downloaded,
        # B the d-able missing row, D unknown — no Model_path)
        assert _row(table, 0)[:5] == [
            "", _KEY_MODEL_A, "MLM", "plants", "396",
        ]
        assert _row(table, 0)[5] == SEL_COMPAT_ADAPTED
        assert _row(table, 0)[6] == SEL_MODEL_PRESENCE_PRESENT
        assert _row(table, 1)[5] == SEL_COMPAT_ADAPTED
        assert _row(table, 1)[6] == SEL_MODEL_PRESENCE_MISSING
        assert _row(table, 2)[5] == SEL_COMPAT_ADAPTED
        assert _row(table, 2)[6] == SEL_PRESENCE_UNKNOWN
        # the pool-mode filter-count segment is always legible
        assert _label_text(screen, "#selection-filter-count") == (
            SEL_FILTER_COUNT_POOLED.format(
                pool=SEL_POOL_ADAPTED, n=3, total=3))

        # space marks the cursor row (the mark column updates in place)
        await pilot.press("space")
        await pilot.pause()
        assert screen.marked_models == {_KEY_MODEL_A}
        assert _row(table, 0)[0] == "✓"

        # t reveals the ALL pool: the unadapted row is present, clearly
        # marked 未适配 with the honest manual-placement download cell —
        # never hidden data
        await pilot.press("t")
        await pilot.pause()
        assert _row_keys(table) == [
            _KEY_MODEL_A, _KEY_MODEL_B, _KEY_MODEL_C, _KEY_MODEL_D,
        ]
        assert _row(table, 2)[5] == SEL_COMPAT_UNADAPTED
        assert _row(table, 2)[6] == SEL_MODEL_DL_MANUAL
        assert _label_text(screen, "#selection-filter-count") == (
            SEL_FILTER_COUNT_POOLED.format(
                pool=SEL_POOL_ALL, n=4, total=4))
        # the mark survived the pool rebuild
        assert screen.marked_models == {_KEY_MODEL_A}
        assert _row(table, 0)[0] == "✓"

        # t back: the default pool, the mark still alive
        await pilot.press("t")
        await pilot.pause()
        assert _row_keys(table) == [_KEY_MODEL_A, _KEY_MODEL_B, _KEY_MODEL_D]
        assert screen.marked_models == {_KEY_MODEL_A}
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
                n=0, models_total=4, m=0, tasks_total=2,
            )
        )
        # one
        await pilot.press("space")
        await pilot.pause()
        assert screen.marked_models == {_KEY_MODEL_A}
        assert _label_text(screen, "#selection-status") == (
            SEL_STATUS_LINE.format(
                n=1, models_total=4, m=0, tasks_total=2,
            )
        )
        # many
        await pilot.press("down")
        await pilot.press("space")
        await pilot.pause()
        assert screen.marked_models == {_KEY_MODEL_A, _KEY_MODEL_B}
        assert _label_text(screen, "#selection-status") == (
            SEL_STATUS_LINE.format(
                n=2, models_total=4, m=0, tasks_total=2,
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
            SEL_FILTER_COUNT_POOLED.format(pool=SEL_POOL_ADAPTED, n=2, total=3)
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
            _KEY_MODEL_A, _KEY_MODEL_B, _KEY_MODEL_D,
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
            SEL_FILTER_COUNT_POOLED.format(pool=SEL_POOL_ADAPTED, n=0, total=3)
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
        # the mark column re-rendered for the new sets (C is marked but
        # lives OUTSIDE the default pool — its mark persists in the set,
        # the pool never filters the mark sets)
        assert _row(table, 0)[0] == "✓"
        assert _row(table, 1)[0] == ""
        assert _row(table, 2)[0] == ""
        # the success toast fired with the preset label and both counts
        assert SEL_PRESET_APPLIED.format(
            preset=SEL_PRESET_TIER_1, n=2, m=1,
        ) in _toast_messages(app)
        # the status line reflects the applied preset
        assert _label_text(screen, "#selection-status") == (
            SEL_STATUS_LINE.format(
                n=2, models_total=4, m=1, tasks_total=2,
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
        # the event loop keeps processing keys (the t pool toggle
        # renders — the T-08-07 responsiveness proof)
        assert not isinstance(app.screen, PresetModal), (
            "the modal must wait for the worker's menu"
        )
        await pilot.press("t")
        await pilot.pause()
        assert _row_keys(table) == [
            _KEY_MODEL_A, _KEY_MODEL_B, _KEY_MODEL_C, _KEY_MODEL_D,
        ], (
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

        # mark one model via spacebar; the TASK mark is seeded directly —
        # since the 2026-10-14 slot split slot 2 has no interactive
        # dataset table (task marks arrive via presets/templates; the
        # export flow itself is what this test pins)
        await pilot.press("space")
        await pilot.pause()
        app._marked_tasks.add(_TASK_A)
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
        await pilot.press("t")
        await pilot.pause()
        assert _row_keys(screen.query_one(DataTable)) == [
            _KEY_MODEL_A, _KEY_MODEL_B, _KEY_MODEL_C, _KEY_MODEL_D,
        ]

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
        await pilot.press("t")
        await pilot.pause()
        assert _row_keys(screen.query_one(DataTable)) == [
            _KEY_MODEL_A, _KEY_MODEL_B, _KEY_MODEL_C, _KEY_MODEL_D,
        ]


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
        # t pool toggle replaced the retired m table toggle at 261014-mlc
        # (the slot split — slot 2 is models only); the d row is the
        # MODEL download since the same split. The ctrl+q/ctrl+c rows
        # joined at 261016-v0z (after the app bindings: the declared
        # ctrl+q mirror + the ctrl+c row). 261017-mad: f10 is now the
        # any-focus PRIMARY exit (the declared priority binding per the
        # 2026-10-17 16:02 ruling) and its manual row lists FIRST among
        # the exit rows — and the 261016-vxr Q row stays RETIRED — Q is
        # a plain typing letter again.
        from tui.strings import (
            APP_CTRLC_LABEL,
            APP_CTRLQ_LABEL,
            APP_F10_LABEL,
        )

        assert rows == [
            APP_HELP_ROW.format(key="q", label=APP_QUIT_LABEL),
            APP_HELP_ROW.format(key="?", label=APP_HELP_LABEL),
            APP_HELP_ROW.format(key="L", label=APP_LANGUAGE_TOGGLE_LABEL),
            APP_HELP_ROW.format(key="f10", label=APP_F10_LABEL),
            APP_HELP_ROW.format(key="ctrl+q", label=APP_CTRLQ_LABEL),
            APP_HELP_ROW.format(key="ctrl+c", label=APP_CTRLC_LABEL),
            # 261018-08g (SOAK-4/F4): the f1/f2 any-focus manual rows
            APP_HELP_ROW.format(key="f1", label=APP_HELP_LABEL),
            APP_HELP_ROW.format(key="f2", label=APP_LANGUAGE_TOGGLE_LABEL),
            APP_HELP_ROW.format(key="space", label=SEL_MARK_LABEL),
            APP_HELP_ROW.format(key="t", label=SEL_POOL_TOGGLE_LABEL),
            APP_HELP_ROW.format(key="p", label=SEL_PRESET_LABEL),
            APP_HELP_ROW.format(key="x", label=SEL_TEMPLATE_LABEL),
            APP_HELP_ROW.format(key="s", label=SEL_SAVE_PRESET_LABEL),
            APP_HELP_ROW.format(key="/", label=SEL_FILTER_KEY_LABEL),
            APP_HELP_ROW.format(key="w", label=SEL_WIZARD_LABEL),
            APP_HELP_ROW.format(key="e", label=SEL_TOGGLE_LABEL),
            APP_HELP_ROW.format(key="d", label=SEL_MODEL_DOWNLOAD_LABEL),
            APP_HELP_ROW.format(key="v", label=SEL_MATRIX_LABEL),
        ]
        # esc closes back to the selection screen
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SelectionScreen)


# =====================================================================
# Pilot tests — the 适配/下载 cells (MLC-02)
# =====================================================================

async def test_download_and_compat_cell_states_pin_the_contract():
    """The four honest 下载 states and the three 适配 states render from
    presence + compat + custom_status exactly (MLC-02): 已下载 / 未下载
    (d-able, missing+adapted) / 手动放置 (missing unadapted-or-custom) /
    ◌ 未知 (no Model_path or drift); 已适配 / 未适配 / 自定义."""
    data = SelectionData(
        model_entries=(
            {"key": "m-present", "type": "MLM", "species": "plants",
             "size_m": 1.0, "card": {}},
            {"key": "m-dable", "type": "MLM", "species": "plants",
             "size_m": 2.0, "card": {"Model_path": "models/m-dable"}},
            {"key": "m-manual-official", "type": "DL", "species": "",
             "size_m": 3.0, "card": {"Model_path": "models/m-manual"}},
            {"key": "m-manual-custom", "type": "MLM", "species": "",
             "size_m": 4.0, "card": {"Model_path": "models/m-custom"}},
            {"key": "m-unknown", "type": "MLM", "species": "",
             "size_m": 5.0, "card": {}},
        ),
        model_presence={
            "m-present": selection_service.MODEL_PRESENCE_PRESENT,
            "m-dable": selection_service.MODEL_PRESENCE_MISSING,
            "m-manual-official": selection_service.MODEL_PRESENCE_MISSING,
            "m-manual-custom": selection_service.MODEL_PRESENCE_MISSING,
            "m-unknown": selection_service.MODEL_PRESENCE_UNKNOWN,
        },
        custom_status={"m-manual-custom": {"custom": True,
                                           "enabled": True}},
        compat={
            "m-present": {"dnllm_adapted": True},
            "m-dable": {"dnllm_adapted": True},
            "m-manual-official": {"dnllm_adapted": False},
            # the custom key is absent from the official compat map
            "m-unknown": {"dnllm_adapted": True},
        },
    )
    app = _app(FakeSelectionService(data=data))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        table = screen.query_one(DataTable)

        # t reveals every row (the unadapted official is default-hidden)
        await pilot.press("t")
        await pilot.pause()
        cells = {key: (_row(table, index)[5], _row(table, index)[6])
                 for index, key in enumerate(_row_keys(table))}
        assert cells["m-present"] == (
            SEL_COMPAT_ADAPTED, SEL_MODEL_PRESENCE_PRESENT)
        assert cells["m-dable"] == (
            SEL_COMPAT_ADAPTED, SEL_MODEL_PRESENCE_MISSING)
        assert cells["m-manual-official"] == (
            SEL_COMPAT_UNADAPTED, SEL_MODEL_DL_MANUAL)
        assert cells["m-manual-custom"] == (
            SEL_COMPAT_CUSTOM, SEL_MODEL_DL_MANUAL)
        assert cells["m-unknown"] == (
            SEL_COMPAT_ADAPTED, SEL_PRESENCE_UNKNOWN)


# test_presence_cell_formats_pin_the_contract and
# test_presence_column_renders_n_audit_missing_copy (the DATASET presence
# cells) were REMOVED by the 2026-10-14 slot split: slot 2 is models only
# — the dataset presence surface lives on slot 3 (the full-list 下载
# cells) and the matrix (the ◌/✓ glyph grid), both pinned in their own
# suites.


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
    path; the app stays alive (the pool toggle still re-renders)."""
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
        # the app stays alive: the pool toggle still re-renders the
        # error state (both pools read the same failed registry)
        await pilot.press("t")
        await pilot.pause()
        assert _row(table, 0)[1] == SEL_REGISTRY_LOAD_FAILED.format(
            registry_path="/repo/pipeline/models_info.json",
        )
        await pilot.press("t")
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
            _KEY_MODEL_A, _KEY_MODEL_B, _KEY_MODEL_D,
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
    """The real seam: 59/50 entries, presence from the committed n_audit.
    Refresh-stable presence pins (the R-03 follow-up rule: the baseline
    is maintainer-refreshable — 43/50 -> 50/50 landed as a data commit —
    so the asserts cover structure and DEFINITE presence, never a
    specific missing count or key set)."""
    empty_overlay = tmp_path / "custom"
    empty_overlay.mkdir()
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(empty_overlay))
    data = SelectionBackend().load_selection_data()
    assert len(data.model_entries) == 59
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
    # MLC-02 (261014-mlc): the compat verdict map rides the snapshot —
    # the committed 59-key artifact through the ONE loader (an empty map
    # is the degraded read; 38 adapted)
    assert data.compat, "the committed compat map loads through the seam"
    assert set(data.compat) == {
        entry["key"] for entry in data.model_entries
    }
    assert sum(
        1 for verdict in data.compat.values()
        if isinstance(verdict, dict)
        and verdict.get("dnllm_adapted") is True
    ) == 38


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

    assert len(data.model_entries) == 59
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


def test_backend_non_dict_custom_entry_degrades_to_empty_card_never_raises(
        monkeypatch, tmp_path):
    """CR-01 chain 1 (08-08): a non-dict entry in the user-owned
    custom_models.json — input the Phase 7 loader deliberately merges
    (pinned by tests/test_registry_loader.py::
    test_non_dict_custom_entry_still_merges_after_skip_filter) — loads
    through the REAL SelectionBackend.load_selection_data() seam as the
    empty-card entry: the key stays visible with blank filter axes and
    size_m 0.0, the card value verbatim, alongside the healthy custom
    and the committed officials; the call completes without raising
    (never an AttributeError exit of the console)."""
    overlay = tmp_path / "custom"
    overlay.mkdir()
    (overlay / "custom_models.json").write_text(
        json.dumps({
            "hand-edited-nondict": [1, 2],
            "healthy-custom": {
                "Model_name": "healthy-custom",
                "Model_path": "models/healthy/custom",
                "type": "MLM",
                "species": "plant",
                "size (M)": 86,
            },
        }),
        encoding="utf-8")
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(overlay))

    data = SelectionBackend().load_selection_data()

    assert data.models_load_error is None
    assert data.datasets_load_error is None
    by_key = {entry["key"]: entry for entry in data.model_entries}
    # the non-dict entry degrades to the empty card — never a drop, never
    # a mutation of the original value (the honest degraded row)
    degraded = by_key["hand-edited-nondict"]
    assert degraded["type"] == ""
    assert degraded["species"] == ""
    assert degraded["size_m"] == 0.0
    assert degraded["card"] == [1, 2]
    # the healthy custom entry projects its card fields normally
    healthy = by_key["healthy-custom"]
    assert healthy["type"] == "MLM"
    assert healthy["species"] == "plant"
    assert healthy["size_m"] == 86.0
    # the committed officials ride alongside (59 at HEAD post-ir9)
    assert len(data.model_entries) == 59 + 2
    assert len(data.dataset_entries) == 50


def test_load_entries_degrades_on_corrupt_official_json(tmp_path):
    """CR-01 chain 2 (08-08), proven at the seam function itself: a
    loader raising the corrupt-registry vocabulary — json.JSONDecodeError
    or UnicodeDecodeError, the loader's own malformed-input classes (a
    ValueError family that escaped the former (OSError, SystemExit)
    tuple) — degrades to the documented ([], path) load-error state,
    never raises."""
    registry_path = tmp_path / "models_info.json"

    def _corrupt_json():
        raise json.JSONDecodeError("Expecting value", "doc", 0)

    def _corrupt_encoding():
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

    entries, error = selection_screen_module._load_entries(
        _corrupt_json, registry_path)
    assert entries == []
    assert error == str(registry_path)

    entries, error = selection_screen_module._load_entries(
        _corrupt_encoding, registry_path)
    assert entries == []
    assert error == str(registry_path)


def test_backend_corrupt_official_registry_degrades_to_error_state(
        monkeypatch, tmp_path):
    """CR-01 chain 2 (08-08) through the real seam: a corrupt OFFICIAL
    models_info.json (json.JSONDecodeError from the loader) degrades to
    the SEL_REGISTRY_LOAD_FAILED load-error state naming the path while
    the OTHER registry stays healthy — the OSError twin's shape (the
    corrupt file is a broken checkout, not an app exit)."""
    def _corrupt():
        raise json.JSONDecodeError("Expecting value", "doc", 0)

    monkeypatch.setattr(
        registries_service, "load_model_entries", _corrupt,
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


# =====================================================================
# The round-2 screen-side card guards (08-09, the Truth-6 residual)
# =====================================================================

#: The degraded row's registry key (the 08-08 chain-1 overlay shape).
_DEGRADED_KEY = "hand-edited-nondict"


def _degraded_row_env(monkeypatch, tmp_path):
    """The 08-09 Pilot environment: a tmp overlay holding ONE loader-
    accepted non-dict card (the chain-1 fixture shape) plus a tmp TUI
    state root, so the REAL selection backend loads machine-independent
    registries through the env — the same injection the verifier's own
    reproductions used."""
    overlay = tmp_path / "custom"
    overlay.mkdir()
    (overlay / "custom_models.json").write_text(
        json.dumps({_DEGRADED_KEY: [1, 2]}),
        encoding="utf-8")
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(overlay))
    monkeypatch.setenv("DNALLMMARK_TUI_STATE_DIR", str(state))


async def test_w_press_survives_non_dict_card_and_opens_wizard(
        monkeypatch, tmp_path):
    """08-09 crash site 1 (the verifier's reproduction): ANY ``w`` press
    on the models screen — no row interaction, the DEFAULT cursor —
    raises ``AttributeError('list' object has no attribute 'get')`` out
    of ``build_wizard``'s observed-vocabularies comprehensions while a
    non-dict custom card is merged (selection.py:712), which textual
    8.2.8's ``App._handle_exception`` turns into a console EXIT. After
    the guard the wizard opens over the officials' vocabularies — the
    degraded card contributes no species/tokenizer entry, everything
    else intact."""
    _degraded_row_env(monkeypatch, tmp_path)
    # env fake only — the selection side stays REAL (the real backend
    # loads through the overlay env)
    app = DnallmMarkTui(env_check_service=_EnvCacheHitFake())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)

        await pilot.press("w")
        await pilot.pause()

        assert app._exception is None, (
            "a w press must never exit the console on a loader-accepted "
            f"non-dict card: {app._exception!r}"
        )
        # lazy import — the module's own wizard import is lazy (the
        # ConfirmModal cycle), so the test mirrors it
        from tui.screens.wizard import WizardModal

        assert isinstance(app.screen, WizardModal), (
            "the degraded-but-meaningful state: the wizard opens"
        )
        vocabularies = app.screen._vocabularies
        # the degraded card contributes no vocabulary entry; the
        # officials' vocabularies still populate
        assert vocabularies["species"], "official species populate"
        assert vocabularies["Tokenizer"], "official tokenizers populate"


async def _cursor_to_degraded_row(pilot, app):
    """The deterministic path onto the degraded row: ``t`` (the ALL
    pool — the row never carries a custom badge, because the management
    read skips non-dict entries, so the DEFAULT pool hides it), then the
    k9s filter narrowed to the row, then ``tab`` from the filter Input to
    the table (compose order: Input, warning Label, DataTable) so the
    cursor — row 0 of the one-row table — sits on it."""
    await pilot.press("t")
    await pilot.pause()
    await pilot.press("slash")
    await pilot.pause()
    await _type(pilot, "nondict")
    table = app.screen.query_one(DataTable)
    assert _row_keys(table) == [_DEGRADED_KEY]
    await pilot.press("tab")
    await pilot.pause()


async def test_enter_on_degraded_row_opens_cardless_detail_modal(
        monkeypatch, tmp_path):
    """08-09 crash site 2 (the verifier's reproduction): ``enter`` on the
    degraded row — visible in the ALL pool — defeats ``_open_detail``'s
    ``entry.get("card") or {}`` with the truthy non-dict card
    (selection.py:2144) and ``RowDetailModal.on_mount`` dies on
    ``self._card.items()`` (:1236, ``AttributeError('list' object has no
    attribute 'items')``) — a console EXIT on a plain drill-down the
    08-08 empty-card projection itself rendered reachable. After the
    guard the modal opens CARD-LESS: the border title carries the key,
    the detail log renders nothing — the drill-down twin of the row's
    blank type/species/size_m axes."""
    _degraded_row_env(monkeypatch, tmp_path)
    app = DnallmMarkTui(env_check_service=_EnvCacheHitFake())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)

        await _cursor_to_degraded_row(pilot, app)
        await pilot.press("enter")
        await pilot.pause()

        assert app._exception is None, (
            "enter on the degraded row must never exit the console: "
            f"{app._exception!r}"
        )
        assert isinstance(app.screen, RowDetailModal), (
            "the card-less drill-down opens over the degraded row"
        )
        modal = app.screen
        assert modal.entry_key == _DEGRADED_KEY
        assert modal._card == {}, (
            "only dicts reach the modal after the guard — the "
            "card-less state is {}, never the verbatim list"
        )
        assert modal.query_one("#row-detail-box").border_title == (
            _DEGRADED_KEY
        )
        log = modal.query_one("#row-detail-log", RichLog)
        assert not log.lines, "the card-less detail log renders nothing"


async def test_d_press_on_degraded_row_stays_silent_and_alive(
        monkeypatch, tmp_path):
    """08-09, the shield pin (passes pre-fix by design — the regression
    guard for the THIRD site's incidental survival): ``d`` on the
    degraded row stays silent-and-alive through the UNKNOWN-presence
    early return (the non-dict card carries no Model_path, so
    ``model_presence`` maps it UNKNOWN and the action returns before the
    card read). The UNKNOWN shield is incidental — one refactor from
    breaking — which is why ``_manual_landing_path`` is hardened
    independently (its direct unit pin below) and this test holds the
    Pilot-level behavior."""
    _degraded_row_env(monkeypatch, tmp_path)
    app = DnallmMarkTui(env_check_service=_EnvCacheHitFake())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen

        await _cursor_to_degraded_row(pilot, app)
        await pilot.press("d")
        await pilot.pause()

        assert app._exception is None, (
            f"d on the degraded row must stay alive: {app._exception!r}"
        )
        # no modal pushed (the UNKNOWN-presence silent branch) and the
        # selection screen still holds the focus
        assert app.screen is screen, "no modal over the silent branch"
        assert not _toast_messages(app), "the UNKNOWN branch is silent"
        assert app.focused is screen.query_one(DataTable), (
            "the table keeps the focus — the press is a no-op"
        )


def test_manual_landing_path_returns_none_for_non_dict_card():
    """08-09 hardening, the direct unit pin: ``_manual_landing_path``
    extracts the card through the ``model_presence`` idiom (bind, then
    ``.get(...) if isinstance(card, dict) else None``) — a non-dict card
    entry returns None and completes without raising. The former
    ``(entry.get("card") or {}).get("Model_path")`` idiom raised
    ``AttributeError`` on the truthy list (the ``or`` defeats), so this
    test is RED pre-fix alongside the two Pilot crash tests."""
    screen = SelectionScreen()
    screen._data = SelectionData(model_entries=(
        {"key": _DEGRADED_KEY, "type": "", "species": "",
         "size_m": 0.0, "card": [1, 2]},
    ))

    assert screen._manual_landing_path(_DEGRADED_KEY) is None


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

#: The real longest registry MODEL key (pipeline/models_info.json,
#: verified 2026-10-14): 46 chars — the backstop fixture's long key.
_LONGEST_MODEL_KEY = "caduceus-ph_seqlen-131k_d_model-256_n_layer-16"


async def test_backstop_longest_model_key_at_80x24():
    """Backstop (08-UI-SPEC UI Considerations, long-text; UAT geometry —
    reworked to the models-only surface at 261014-mlc): at 80x24 the
    longest real registry model key causes no wrap-induced row-height
    change — every data row stays height 1 — and the key cell carries
    the FULL key; the over-budget table h-scrolls (the matrix precedent)
    and the 下载 column stays reachable by scrolling right."""
    model_entries = tuple(
        {
            "key": (_LONGEST_MODEL_KEY if index == 0
                    else f"model-{index}"),
            "type": "MLM", "species": "plants", "size_m": 1.0,
            "card": {"Model_path": "models/x"},
        }
        for index in range(12)  # enough rows to force the v-scrollbar
    )
    data = SelectionData(
        model_entries=model_entries,
        compat={
            str(entry["key"]): {"dnllm_adapted": True}
            for entry in model_entries
        },
        model_presence={
            str(entry["key"]): selection_service.MODEL_PRESENCE_MISSING
            for entry in model_entries
        },
    )
    app = _app(FakeSelectionService(data=data))
    async with app.run_test(size=(80, 24)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        table = screen.query_one(DataTable)

        assert table.row_count == 12

        # no wrap-induced row-height change: every data row stays height 1
        # (the over-budget table clips + h-scrolls; it never wraps)
        heights = {row.height for row in table.rows.values()}
        assert heights == {1}, "long keys must never wrap a row taller"

        # the UAT geometry: the key column fits the longest real key
        # exactly (46) and the total budget (widths + per-column padding
        # + the scrollbar) is 119 — past 80, so the table h-scrolls
        # (C4J-1, 261015-c4j: the download column grew 10 -> 15 for the
        # live downloading word + the appended percent data word;
        # EHC-4, 261015-ehc: 15 -> 28 for the appended rate token —
        # measured with Rich over BOTH languages' widest honest
        # composition, never clipping live data)
        widths = [
            table.columns[key].width for key in _MODEL_COLUMNS_KEYS
        ]
        assert table.columns["key"].width == 46
        assert sum(widths) + 2 * len(widths) + 2 == 119
        assert table.max_scroll_x > 0, (
            "the 119-wide table must h-scroll at the 80-column grid"
        )

        # the key cell carries the FULL key — no ellipsis (the DataTable
        # clips the display on narrow terminals; the full value stays in
        # the enter row detail)
        key_cell = _row(table, 0)[1]
        assert key_cell == _LONGEST_MODEL_KEY
        assert Text(key_cell).cell_len == 46  # the model key-column budget

        # the viewport origin renders the key column header...
        from textual.geometry import Region
        strips = table.render_lines(
            Region(0, 0, table.size.width, min(table.size.height, 3)),
        )
        header = "".join(segment.text for segment in strips[0])
        assert SEL_COL_MODEL in header

        # ...and the 下载 column stays reachable: scrolled to the right
        # end its header and glyphs render in the viewport
        table.scroll_to(x=table.max_scroll_x, animate=False)
        await pilot.pause()
        strips = table.render_lines(
            Region(0, 0, table.size.width, min(table.size.height, 3)),
        )
        header_right = "".join(segment.text for segment in strips[0])
        assert SEL_COL_DOWNLOAD in header_right
        first_data_row = "".join(segment.text for segment in strips[1])
        assert "✗" in first_data_row


async def test_backstop_longest_model_key_fits_in_full_at_160():
    """Regression (UAT feedback, 「部分数据集名称过长看不到全部」 — reworked
    to the models-only surface at 261014-mlc): on a normal wide terminal
    (160x40) the longest real registry model key renders IN FULL in its
    key cell — no ellipsis, the whole table fits without h-scroll — and
    the h-scroll geometry never disturbs the min-size guard (below 80x24
    the guard still takes over)."""
    model_entries = tuple(
        {
            "key": (_LONGEST_MODEL_KEY if index == 0
                    else f"model-{index}"),
            "type": "MLM", "species": "plants", "size_m": 1.0,
            "card": {"Model_path": "models/x"},
        }
        for index in range(12)  # enough rows to force the v-scrollbar
    )
    data = SelectionData(
        model_entries=model_entries,
        compat={
            str(entry["key"]): {"dnllm_adapted": True}
            for entry in model_entries
        },
        model_presence={
            str(entry["key"]): selection_service.MODEL_PRESENCE_MISSING
            for entry in model_entries
        },
    )
    app = _app(FakeSelectionService(data=data))
    async with app.run_test(size=(160, 40)) as pilot:
        await _open_selection(pilot, app)
        table = app.screen.query_one(DataTable)

        assert table.row_count == 12

        # the 101-wide table fits a 160-column terminal whole — no
        # h-scroll, and both edge columns render on-screen
        assert table.max_scroll_x == 0, (
            "the 101-wide table must fit a 160-column terminal"
        )
        from textual.geometry import Region
        strips = table.render_lines(
            Region(0, 0, table.size.width, min(table.size.height, 3)),
        )
        header = "".join(segment.text for segment in strips[0])
        assert SEL_COL_MODEL in header
        assert SEL_COL_DOWNLOAD in header

        # the longest real key renders in full — no ellipsis
        key_cell = _row(table, 0)[1]
        assert key_cell == _LONGEST_MODEL_KEY
        assert "…" not in key_cell
        assert Text(key_cell).cell_len == 46

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
