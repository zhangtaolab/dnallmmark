"""
Tier-2 Pilot suite for the selection screen's custom-entry surface
(Phase 9, 09-06; CUST-06 + the CUST-01/02 entry point, D-09/D-10/D-12/D-14).

Pins the w/e binding family end-to-end against the REAL ``DnallmMarkTui``
with constructor-injected deterministic fakes (the Phase 8 discipline;
the new seams are optional ``SelectionScreen`` constructor injections
whose defaults are the real services — existing Phase 8 fake injections
run unchanged):

- w (D-14): opens the wizard for the ACTIVE table's kind (models table
  -> model wizard; datasets table -> dataset wizard); the cursor row
  prefills from that entry when it is a landed custom entry (the D-12
  re-record aid — the management read supplies the entry); every other
  cursor state opens a blank form; the top menu carries no wizard item
  (the wizard is an action, not a screen);
- e (D-09): flips the cursor custom entry's enabled through the injected
  store seam (the atomic set_enabled write) with the toast pair (the
  disable wording carries the loader-level note); an official cursor row
  is a no-op with the honest toast, never silent; the table refreshes
  after every successful write;
- loader-skip visibility (tier-1-grade): after a disable, the REAL
  ``registry_loader`` (tmp-pinned env) no longer contains the key while
  the real ``SelectionBackend`` snapshot still renders it — the disabled
  entry stays visible for management (Pitfall 7: the management second
  read adds back what the overlay-merged view hides);
- the bottom bar's left segment renders [w]接入 and [e]停用 in binding
  declaration order BEFORE the auxiliary actions (the 09-UI-SPEC
  migration table).

Pilot discipline (inherited): ``await pilot.pause()`` before every
assertion; env pinning sets BOTH ``DNALLMMARK_TUI_CONFIG_DIR`` and
``DNALLMMARK_CUSTOM_REGISTRY_DIR`` to the SAME tmp root (the 09-01 tracer
discipline — the real home config is never read, official registries
never written).
"""

from pathlib import Path
from typing import ClassVar

import registry_loader
from env_smoke import CheckResult
from rich.text import Text
from textual.binding import Binding, BindingType
from textual.screen import ModalScreen
from textual.widgets import DataTable, Static

from tui.app import DnallmMarkTui
from tui.screens.nav import NAV_SLOTS
from tui.screens.selection import (
    PresetMenu,
    PresetModal,
    PresetOption,
    SelectionBackend,
    SelectionData,
    SelectionScreen,
)
from tui.services import custom_entries
from tui.services import selection as selection_service
from tui.services.registries import PRESENCE_PRESENT, Presence
from tui.strings import (
    ENV_KERNEL_LABELS,
    SEL_COUNT_CUSTOM_SEGMENT,
    SEL_CUSTOM_BADGE,
    SEL_DISABLED_MARK_WARNING,
    SEL_DISABLED_SUFFIX,
    SEL_MATRIX_LABEL,
    SEL_PRESET_UNKNOWN_KEYS,
    SEL_STATUS_LINE,
    SEL_TOGGLE_DISABLED_TOAST,
    SEL_TOGGLE_ENABLED_TOAST,
    SEL_TOGGLE_LABEL,
    SEL_TOGGLE_OFFICIAL_NOOP,
    SEL_WIZARD_LABEL,
)

# =====================================================================
# Synthetic fixtures (official + landed custom rows, mixed enable state)
# =====================================================================

_KEY_OFFICIAL_MODEL = "plant-dnabert-6mer"
_KEY_CUSTOM_MODEL = "my-custom-dna-lm"
_KEY_OFFICIAL_TASK = "GUE__emp_H3"
_KEY_CUSTOM_TASK = "my-custom-ds"

_CUSTOM_MODEL_ENTRY = {
    "Model_path": "models/my-custom-dna-lm",
    "Model_name": _KEY_CUSTOM_MODEL,
    "type": "MLM",
    "species": "plants",
    "size (M)": 88,
}
_CUSTOM_DATASET_ENTRY = {
    "Dataset_path": "datasets/my-custom-ds",
    "Dataset_name": _KEY_CUSTOM_TASK,
    "Category": "Plants",
    "type": "binary",
    "metric": "f1",
}


def _custom_data(model_enabled=True, task_enabled=True):
    """The standard custom snapshot: 1 official + 1 custom per table."""
    return SelectionData(
        model_entries=(
            {
                "key": _KEY_OFFICIAL_MODEL, "type": "MLM",
                "species": "plants", "size_m": 86.0,
                "card": {"type": "MLM", "species": "plants",
                         "size (M)": 86},
            },
            {
                "key": _KEY_CUSTOM_MODEL, "type": "MLM",
                "species": "plants", "size_m": 88.0,
                "card": _CUSTOM_MODEL_ENTRY,
            },
        ),
        dataset_entries=(
            {
                "key": _KEY_OFFICIAL_TASK, "category": "Animals",
                "type": "binary", "metric": "f1",
                "card": {"Category": "Animals", "type": "binary",
                         "metric": "f1"},
            },
            {
                "key": _KEY_CUSTOM_TASK, "category": "Plants",
                "type": "binary", "metric": "f1",
                "card": _CUSTOM_DATASET_ENTRY,
            },
        ),
        presence={
            _KEY_OFFICIAL_TASK: Presence(
                status=PRESENCE_PRESENT, rows=(100, 20, 20),
            ),
        },
        custom_status={
            _KEY_CUSTOM_MODEL: {"custom": True, "enabled": model_enabled},
            _KEY_CUSTOM_TASK: {"custom": True, "enabled": task_enabled},
        },
    )


_KEY_DISABLED_MODEL = "my-other-lm"


def _landed_fixture_data():
    """The D-10 presentation fixture: models = official + enabled custom +
    DISABLED custom; datasets = official + enabled custom — the one table
    state carrying badge, suffix, counts, mark-block, and preset loud-skip
    in a single snapshot."""
    return SelectionData(
        model_entries=(
            {
                "key": _KEY_OFFICIAL_MODEL, "type": "MLM",
                "species": "plants", "size_m": 86.0,
                "card": {"type": "MLM", "species": "plants",
                         "size (M)": 86},
            },
            {
                "key": _KEY_CUSTOM_MODEL, "type": "MLM",
                "species": "plants", "size_m": 88.0,
                "card": dict(_CUSTOM_MODEL_ENTRY),
            },
            {
                "key": _KEY_DISABLED_MODEL, "type": "CLM",
                "species": "human", "size_m": 310.0,
                "card": {"type": "CLM", "species": "human",
                         "size (M)": 310, "enabled": False},
            },
        ),
        dataset_entries=(
            {
                "key": _KEY_OFFICIAL_TASK, "category": "Animals",
                "type": "binary", "metric": "f1",
                "card": {"Category": "Animals", "type": "binary",
                         "metric": "f1"},
            },
            {
                "key": _KEY_CUSTOM_TASK, "category": "Plants",
                "type": "binary", "metric": "f1",
                "card": dict(_CUSTOM_DATASET_ENTRY),
            },
        ),
        presence={},
        custom_status={
            _KEY_CUSTOM_MODEL: {"custom": True, "enabled": True},
            _KEY_DISABLED_MODEL: {"custom": True, "enabled": False},
            _KEY_CUSTOM_TASK: {"custom": True, "enabled": True},
        },
    )


def _official_only_data():
    """The zero-customs snapshot (custom_status defaults to {})."""
    return SelectionData(
        model_entries=(
            {
                "key": _KEY_OFFICIAL_MODEL, "type": "MLM",
                "species": "plants", "size_m": 86.0,
                "card": {"type": "MLM"},
            },
            {
                "key": "plant-dnamamba-6mer", "type": "MLM",
                "species": "plants", "size_m": 396.0,
                "card": {"type": "MLM"},
            },
        ),
        dataset_entries=(
            {
                "key": _KEY_OFFICIAL_TASK, "category": "Animals",
                "type": "binary", "metric": "f1",
                "card": {"Category": "Animals"},
            },
        ),
        presence={},
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


class _SelectionFake:
    """Deterministic selection-service fake (the Phase 8 shape): the real
    08-05 grammar over synthetic entries, a mutable ``data`` snapshot the
    tests flip between presses, a load counter for refresh proofs, and
    injectable preset options for the loud-skip cases."""

    def __init__(self, data=None, presets=()):
        self.data = data if data is not None else _custom_data()
        self.presets = tuple(presets)
        self.load_calls = 0

    def load_selection_data(self):
        self.load_calls += 1
        return self.data

    def preset_menu(self):
        return PresetMenu(options=self.presets)

    def custom_names(self):
        return ()

    def save_preset(self, name, models, tasks):
        raise AssertionError("not under test")

    def parse_filter(self, query):
        return selection_service.parse_filter_query(query)

    def apply_filter(self, entries, parsed):
        return selection_service.apply_filter(entries, parsed.terms)

    def import_template(self, path):
        raise AssertionError("not under test")

    def export_template(self, path, models, tasks):
        raise AssertionError("not under test")

    def export_tiers(self, path, models, tasks):
        raise AssertionError("not under test")


class _StubWizard(ModalScreen):
    """The fake build_wizard product: a dismissible marker modal."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", "back"),
    ]

    def compose(self):
        yield Static("stub-wizard")


class _CustomServiceFake:
    """The custom-onboarding service fake: records the w push args and
    every set_enabled call (the atomic-seam proof); read_entries serves
    the management view from a dict."""

    def __init__(self, entries=None):
        self.entries = entries if entries is not None else {
            "models": {_KEY_CUSTOM_MODEL: dict(_CUSTOM_MODEL_ENTRY)},
            "datasets": {_KEY_CUSTOM_TASK: dict(_CUSTOM_DATASET_ENTRY)},
        }
        self.built = []
        self.enabled_calls = []

    def read_entries(self, kind):
        return dict(self.entries.get(kind, {})), None

    def set_enabled(self, kind, key, enabled):
        self.enabled_calls.append((kind, key, enabled))
        return True

    def build_wizard(self, kind, prefill, on_changed):
        self.built.append((kind, prefill, on_changed))
        return _StubWizard()


# =====================================================================
# Helpers
# =====================================================================


def _row_keys(table):
    return [str(key.value) for key in table.rows]


def _row(table, index):
    """A row's cell texts as plain strings (the Phase 8 idiom)."""
    return [
        cell.plain if isinstance(cell, Text) else str(cell)
        for cell in table.get_row_at(index)
    ]


def _status_line(screen):
    """The status-line Label's plain text (badge/count assertions)."""
    content = screen.query_one("#selection-status").content
    return content.plain if isinstance(content, Text) else str(content)


def _toasts(app):
    return [notification.message for notification in app._notifications]


def _app(selection_fake):
    """The real app over the cache-hit env fake + the selection fake."""
    return DnallmMarkTui(
        env_check_service=_EnvCacheHitFake(),
        selection_service=selection_fake,
    )


async def _open_selection(pilot, app, custom_fake=None):
    """Push the selection screen (the custom seam injected) and settle."""
    app.push_screen(SelectionScreen(
        selection_service=app._selection_service,
        marked_models=app._marked_models,
        marked_tasks=app._marked_tasks,
        custom_service=custom_fake,
    ))
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()


def _pin_roots(monkeypatch, tmp_path):
    """Pin BOTH env roots to one tmp dir (the 09-01 tracer discipline)."""
    root = tmp_path / "dnallmmark"
    root.mkdir()
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(root))
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(root))
    return root


# =====================================================================
# Task 1 — the w binding (D-14: kind routing + the D-12 prefill)
# =====================================================================

async def test_w_routes_by_active_table_and_prefills_from_the_custom_row():
    """w opens the wizard for the active table's kind: the models table
    routes models (blank from an official cursor, prefilled from a custom
    cursor); the datasets table routes datasets with the same rule."""
    custom = _CustomServiceFake()
    app = _app(_SelectionFake())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app, custom)
        screen = app.screen
        table = screen.query_one(DataTable)

        # official cursor row -> blank form for the models kind
        await pilot.press("w")
        await pilot.pause()
        assert isinstance(app.screen, _StubWizard)
        assert custom.built[0][:2] == ("models", None)
        await pilot.press("escape")
        await pilot.pause()

        # custom cursor row -> the entry prefills (D-12 re-record aid)
        table.move_cursor(row=1)
        await pilot.pause()
        await pilot.press("w")
        await pilot.pause()
        kind, prefill, _on_changed = custom.built[-1]
        assert kind == "models"
        assert prefill == {_KEY_CUSTOM_MODEL: _CUSTOM_MODEL_ENTRY}
        await pilot.press("escape")
        await pilot.pause()

        # the datasets table routes the dataset kind (custom row prefill)
        await pilot.press("m")
        await pilot.pause()
        table.move_cursor(row=1)
        await pilot.pause()
        await pilot.press("w")
        await pilot.pause()
        kind, prefill, _on_changed = custom.built[-1]
        assert kind == "datasets"
        assert prefill == {_KEY_CUSTOM_TASK: _CUSTOM_DATASET_ENTRY}


async def test_w_passes_a_refresh_callback_into_the_wizard_composition():
    """The land-completion callback reaches build_wizard (the badge/count
    refresh seam) — a callable, not None."""
    custom = _CustomServiceFake()
    app = _app(_SelectionFake())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app, custom)
        await pilot.press("w")
        await pilot.pause()
        _kind, _prefill, on_changed = custom.built[-1]
        assert callable(on_changed)


# =====================================================================
# Task 1 — the e binding (D-09: the atomic toggle + honest toasts)
# =====================================================================

async def test_e_disables_a_custom_row_through_the_store_seam():
    """e on an ENABLED custom row writes enabled=False through the
    injected atomic seam with the disable toast (the loader-level note)
    and refreshes the data."""
    custom = _CustomServiceFake()
    fake = _SelectionFake()
    app = _app(fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app, custom)
        screen = app.screen
        table = screen.query_one(DataTable)
        table.move_cursor(row=1)  # the custom model row
        await pilot.pause()

        loads_before = fake.load_calls
        await pilot.press("e")
        await pilot.pause()
        assert custom.enabled_calls == [("models", _KEY_CUSTOM_MODEL, False)]
        assert SEL_TOGGLE_DISABLED_TOAST.format(key=_KEY_CUSTOM_MODEL) in (
            _toasts(app))
        assert fake.load_calls > loads_before  # the refresh fired


async def test_e_re_enables_a_disabled_custom_row():
    """e on a DISABLED custom row writes enabled=True with the enable
    toast — the toggle is reversible in both directions."""
    custom = _CustomServiceFake()
    fake = _SelectionFake(data=_custom_data(model_enabled=False))
    app = _app(fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app, custom)
        table = app.screen.query_one(DataTable)
        table.move_cursor(row=1)  # the disabled custom model row
        await pilot.pause()

        await pilot.press("e")
        await pilot.pause()
        assert custom.enabled_calls == [("models", _KEY_CUSTOM_MODEL, True)]
        assert SEL_TOGGLE_ENABLED_TOAST.format(key=_KEY_CUSTOM_MODEL) in (
            _toasts(app))


async def test_e_on_an_official_row_is_a_noop_with_the_honest_toast():
    """e on an official row changes nothing and posts the no-op toast —
    never silent, never a store call."""
    custom = _CustomServiceFake()
    fake = _SelectionFake()
    app = _app(fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app, custom)
        table = app.screen.query_one(DataTable)
        table.move_cursor(row=0)  # the official model row
        await pilot.pause()
        loads_before = fake.load_calls

        await pilot.press("e")
        await pilot.pause()
        assert custom.enabled_calls == []
        assert fake.load_calls == loads_before
        assert SEL_TOGGLE_OFFICIAL_NOOP in _toasts(app)


# =====================================================================
# Task 1 — loader-skip visibility (tier-1-grade, real seams on tmp roots)
# =====================================================================

def test_disabled_entry_stays_in_the_table_while_the_real_loader_skips_it(
        monkeypatch, tmp_path):
    """After a disable the REAL registry_loader no longer contains the
    key while the REAL SelectionBackend snapshot still renders it — the
    two-view composition (overlay-merged + the management second read)
    keeps disabled entries visible for management, and the official
    registry files stay byte-identical (binding constraint 11)."""
    _pin_roots(monkeypatch, tmp_path)
    official_models = Path(registry_loader.__file__).parent / (
        "models_info.json")
    before = official_models.read_bytes()

    custom_entries.land("models", _KEY_CUSTOM_MODEL, {
        "Model_path": "models/my-custom-dna-lm",
        "type": "MLM", "size (M)": 88,
    })
    data = SelectionBackend().load_selection_data()
    keys = [entry["key"] for entry in data.model_entries]
    assert _KEY_CUSTOM_MODEL in keys
    assert data.custom_status[_KEY_CUSTOM_MODEL] == {
        "custom": True, "enabled": True,
    }
    assert _KEY_CUSTOM_MODEL in registry_loader.load_models_registry()

    # the atomic disable flips the loader view, never the table view
    assert custom_entries.set_enabled("models", _KEY_CUSTOM_MODEL, False)
    data_after = SelectionBackend().load_selection_data()
    keys_after = [entry["key"] for entry in data_after.model_entries]
    assert _KEY_CUSTOM_MODEL in keys_after  # the table still renders it
    assert len(keys_after) == 63  # 62 official + the disabled custom
    assert data_after.custom_status[_KEY_CUSTOM_MODEL]["enabled"] is False
    merged = registry_loader.load_models_registry()
    assert _KEY_CUSTOM_MODEL not in merged  # the loader-skip (D-09)
    assert len(merged) == 62

    assert official_models.read_bytes() == before  # zero official writes


# =====================================================================
# Task 1 — the chrome contracts (bottom bar order + no menu wizard item)
# =====================================================================

async def test_bottom_bar_declares_w_and_e_before_the_auxiliary_actions():
    """The left segment renders [w]接入 and [e]停用 in binding-declaration
    order BEFORE the auxiliary actions (the migration table disposition —
    at the 120x40 design grid every keycap renders, unclipped)."""
    app = _app(_SelectionFake())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        bar = app.screen.query_one("#nav-left-keycaps", Static)
        content = bar.content
        text = content.plain if isinstance(content, Text) else str(content)
        assert f"[w]{SEL_WIZARD_LABEL}" in text
        assert f"[e]{SEL_TOGGLE_LABEL}" in text
        assert f"[v]{SEL_MATRIX_LABEL}" in text
        assert text.index(f"[w]{SEL_WIZARD_LABEL}") < text.index(
            f"[v]{SEL_MATRIX_LABEL}")
        assert text.index(f"[e]{SEL_TOGGLE_LABEL}") < text.index(
            f"[v]{SEL_MATRIX_LABEL}")


def test_the_menu_carries_no_wizard_item():
    """D-14: the wizard is an action, not a screen — no top-menu slot
    targets it and no slot label carries the wizard wording."""
    assert all(
        slot.target in ("env_check", "selection", "about", None)
        for slot in NAV_SLOTS
    )
    assert all(SEL_WIZARD_LABEL not in slot.label for slot in NAV_SLOTS)


# =====================================================================
# Task 2 — the D-10 presentation contract (badge, suffix, counts, block)
# =====================================================================

async def test_landed_and_disabled_fixture_renders_the_full_custom_contract():
    """One table state carries every CUST-06 presentation truth: the ◇
    badge on both custom states (bold+accent enabled, dim + （已停用）
    disabled), official rows untouched (the adjacency edge), the count
    segment counting landed entries of BOTH states, the disabled-mark
    block, and the preset loud-skip over a disabled key."""
    preset = PresetOption(
        id="mine", kind="derived", name=None,
        models=(_KEY_OFFICIAL_MODEL, _KEY_DISABLED_MODEL), tasks=(),
    )
    fake = _SelectionFake(data=_landed_fixture_data(), presets=(preset,))
    app = _app(fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        table = screen.query_one(DataTable)

        # the badge renders in the key cell: enabled bold+accent, disabled
        # dim with the suffix, official rows carry neither (D-10)
        assert _row(table, 0)[1] == _KEY_OFFICIAL_MODEL
        assert _row(table, 1)[1] == f"{SEL_CUSTOM_BADGE} {_KEY_CUSTOM_MODEL}"
        assert _row(table, 2)[1] == (
            f"{SEL_CUSTOM_BADGE} {_KEY_DISABLED_MODEL}{SEL_DISABLED_SUFFIX}")
        official_cell = table.get_row_at(0)[1]
        enabled_cell = table.get_row_at(1)[1]
        disabled_cell = table.get_row_at(2)[1]
        assert official_cell.spans == []
        assert enabled_cell.spans[0].style == "bold $accent"
        assert any(
            span.style == "$text-muted" for span in disabled_cell.spans)

        # the count segment: 官方 1/1 · 自定义 2/1 — the disabled model
        # counts (visible = counted), appended dim after the Phase 8 line
        assert _status_line(screen) == (
            SEL_STATUS_LINE.format(n=0, models_total=3, m=0, tasks_total=2)
            + " · " + SEL_COUNT_CUSTOM_SEGMENT.format(
                official_models=1, official_datasets=1,
                custom_models=2, custom_datasets=1,
            )
        )

        # marking a DISABLED custom row is blocked with the warning toast
        # and the shared mark set is unchanged (T-09-13)
        table.move_cursor(row=2)
        await pilot.pause()
        await pilot.press("space")
        await pilot.pause()
        assert SEL_DISABLED_MARK_WARNING.format(
            key=_KEY_DISABLED_MODEL) in _toasts(app)
        assert screen.marked_models == set()
        assert _row(table, 2)[0] == ""

        # marking the ENABLED custom row still works (the block is
        # state-specific, never a blanket custom-mark ban)
        table.move_cursor(row=1)
        await pilot.pause()
        await pilot.press("space")
        await pilot.pause()
        assert screen.marked_models == {_KEY_CUSTOM_MODEL}

        # a preset referencing the disabled custom key rides the Phase 8
        # unknown-key loud skip: warned, skipped, never silently marked
        await pilot.press("p")
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, PresetModal)
        await pilot.press("enter")
        await pilot.pause()
        assert not isinstance(app.screen, PresetModal)
        assert screen.marked_models == {_KEY_OFFICIAL_MODEL}
        assert SEL_PRESET_UNKNOWN_KEYS.format(
            n=1, keys=_KEY_DISABLED_MODEL) in _toasts(app)

        # BOTH tables: m -> the dataset table carries the same badge
        await pilot.press("m")
        await pilot.pause()
        assert _row(table, 0)[1] == _KEY_OFFICIAL_TASK
        assert _row(table, 1)[1] == f"{SEL_CUSTOM_BADGE} {_KEY_CUSTOM_TASK}"


async def test_zero_customs_status_line_is_byte_identical_phase8():
    """The zero-one-many edge: zero customs omits the segment — the
    status line is EXACTLY the Phase 8 shape (byte-comparable)."""
    fake = _SelectionFake(data=_official_only_data())
    app = _app(fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        assert _status_line(screen) == SEL_STATUS_LINE.format(
            n=0, models_total=2, m=0, tasks_total=1,
        )


def test_the_real_backend_counts_disabled_customs_in_both_views(
        monkeypatch, tmp_path):
    """The real composition: a landed+disabled custom stays in the
    entries AND the custom-status map (counts include it) while the
    loader view drops it — the count truth is the management read."""
    _pin_roots(monkeypatch, tmp_path)
    custom_entries.land("models", _KEY_CUSTOM_MODEL, {
        "Model_path": "models/a", "type": "MLM", "size (M)": 1,
    })
    custom_entries.land("models", _KEY_DISABLED_MODEL, {
        "Model_path": "models/b", "type": "CLM", "size (M)": 2,
    })
    custom_entries.set_enabled("models", _KEY_DISABLED_MODEL, False)
    data = SelectionBackend().load_selection_data()
    keys = [entry["key"] for entry in data.model_entries]
    # both landed customs render (the disabled one appended after the
    # merged entries); both carry the custom-status truth
    assert keys.index(_KEY_CUSTOM_MODEL) < keys.index(_KEY_DISABLED_MODEL)
    assert data.custom_status[_KEY_DISABLED_MODEL] == {
        "custom": True, "enabled": False,
    }
    # the projection fields render (the canonical entry view shape)
    disabled_entry = next(
        entry for entry in data.model_entries
        if entry["key"] == _KEY_DISABLED_MODEL
    )
    assert disabled_entry["type"] == "CLM"
    assert disabled_entry["size_m"] == 2.0
    # the loader view drops exactly the disabled one
    merged = registry_loader.load_models_registry()
    assert _KEY_CUSTOM_MODEL in merged
    assert _KEY_DISABLED_MODEL not in merged
