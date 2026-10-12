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

import json
from pathlib import Path
from typing import ClassVar

import registry_loader
from env_smoke import CheckResult
from rich.text import Text
from textual.binding import Binding, BindingType
from textual.screen import ModalScreen
from textual.widgets import DataTable, Input, Static

from tui.app import DnallmMarkTui, QueueEventMessage
from tui.screens.nav import NAV_SLOTS
from tui.screens.selection import (
    PresetMenu,
    PresetModal,
    PresetOption,
    SelectionBackend,
    SelectionData,
    SelectionScreen,
)
from tui.screens.wizard import WizardModal
from tui.services import custom_entries
from tui.services import registries as registries_service
from tui.services import selection as selection_service
from tui.services.download_queue import EnqueueOutcome, QueueEvent
from tui.services.gauntlet import (
    LEG_AUDIT,
    LEG_DRY_RUN,
    GauntletItem,
)
from tui.services.registries import (
    PRESENCE_MISSING,
    PRESENCE_PRESENT,
    Presence,
)
from tui.strings import (
    DL_DISABLED_TOAST,
    DL_UNKNOWN_TOAST,
    ENV_KERNEL_LABELS,
    QUEUE_FLIP_TOAST,
    QUEUE_PERSIST_FAILED_TOAST,
    QUEUE_TOAST_ALREADY_QUEUED,
    QUEUE_TOAST_ENQUEUED,
    SEL_COUNT_CUSTOM_SEGMENT,
    SEL_CUSTOM_BADGE,
    SEL_DISABLED_MARK_WARNING,
    SEL_DISABLED_SUFFIX,
    SEL_ENQUEUE_LABEL,
    SEL_ENQUEUE_PRESENT_TOAST,
    SEL_MATRIX_LABEL,
    SEL_PRESENCE_MISSING,
    SEL_PRESENCE_PRESENT,
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


async def _open_selection(pilot, app, custom_fake=None, queue_fake=None):
    """Push the selection screen (the custom + queue seams injected) and
    settle."""
    app.push_screen(SelectionScreen(
        selection_service=app._selection_service,
        marked_models=app._marked_models,
        marked_tasks=app._marked_tasks,
        custom_service=custom_fake,
        queue_service=queue_fake,
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


def _pin_state_root(monkeypatch, tmp_path):
    """Pin the XDG state root to the tmp dir (the 10-05 discipline: the
    state-root pin joins the config-root pin — the queue seam's state
    reads/writes can never reach the operator's real home)."""
    state_root = tmp_path / "state"
    state_root.mkdir()
    monkeypatch.setenv("DNALLMMARK_TUI_STATE_DIR", str(state_root))
    return state_root


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
        # "data_manager" joined at 10-04 (the slot-3 promotion)
        slot.target in ("env_check", "selection", "data_manager",
                        "about", None)
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
        # the accent span carries the resolved live-theme accent (rich
        # spans cannot hold $token styles — probe-pinned, the nav-bar
        # precedent); the disabled spans use rich's native dim
        assert enabled_cell.spans[0].style == (
            f"bold {app.current_theme.accent}")
        assert any(span.style == "dim" for span in disabled_cell.spans)

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


# =====================================================================
# Task 3 — the full integration loop (w -> gauntlet -> land -> badge ->
# count -> e -> disabled-visible + loader-excluded; both kinds)
# =====================================================================

class _AllPassGauntlet:
    """The fake gauntlet: every leg returns an ok item (the full loop
    never spawns a subprocess — the real service carries its own 09-02
    tier-1 suite; this fake conforms to the panel's per-leg calls)."""

    def __init__(self):
        self.calls = []

    def dry_run_precheck(self, kind, key, entry, run_id):
        self.calls.append((LEG_DRY_RUN, kind, key))
        return GauntletItem(
            run_id=run_id, kind=kind, leg=LEG_DRY_RUN, name=key, ok=True,
            details=("planned_cells=1",), raw_output="planned 1 cell",
        )

    def audit_reconciliation(self, key, entry, declared_splits, run_id):
        self.calls.append((LEG_AUDIT, "datasets", key))
        return GauntletItem(
            run_id=run_id, kind="datasets", leg=LEG_AUDIT, name=key,
            ok=True, details=("train_rows=8",), raw_output="audit ok",
        )


class _LoopCustomService:
    """The full-loop custom service: the REAL 09-01 store over the
    pinned tmp roots (read/toggle/land/undo) with the wizard composed
    from the fake-clean validator + the all-pass gauntlet — one
    operator story over one user-owned file."""

    def __init__(self, gauntlet):
        self.gauntlet = gauntlet
        self.refreshes = 0

    def read_entries(self, kind):
        return custom_entries.read_entries(kind)

    def set_enabled(self, kind, key, enabled):
        return custom_entries.set_enabled(kind, key, enabled)

    def build_wizard(self, kind, prefill, on_changed):
        def _land(entry_kind, key, entry):
            result = custom_entries.land(entry_kind, key, entry)
            self.refreshes += 1
            if on_changed is not None:
                on_changed()
            return result

        return WizardModal(
            kind=kind,
            validator=lambda values: [],
            prefill=prefill,
            gauntlet_service=self.gauntlet,
            land=_land,
            undo=custom_entries.undo,
        )


async def _type_wizard_field(pilot, wizard, wid, text):
    """Focus one wizard Input and type through real key events."""
    inp = wizard.query_one(f"#wiz-{wid}", Input)
    inp.focus()
    await pilot.pause()
    await pilot.press(*list(text))
    await pilot.pause()


async def _submit_wizard(pilot, app, wizard):
    """Advance to step 4, submit, and settle the gauntlet worker."""
    for _ in range(3):
        wizard.set_focus(None)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
    wizard.set_focus(None)
    await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()
    await pilot.pause()


async def test_full_loop_models_wizard_lands_badges_counts_and_disables(
        monkeypatch, tmp_path):
    """The CUST story over one user-owned file: w -> fill -> validation
    pass -> gauntlet all-pass -> land -> dismiss -> the badge + the
    count segment appear; e -> the suffix + the real-loader exclusion
    while the table keeps the row (ROADMAP criteria 1/2/4/5 in one
    executable story)."""
    _pin_roots(monkeypatch, tmp_path)
    official = Path(registry_loader.__file__).parent / "models_info.json"
    before = official.read_bytes()
    gauntlet = _AllPassGauntlet()
    custom = _LoopCustomService(gauntlet)
    app = _app(SelectionBackend())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app, custom)
        screen = app.screen
        table = screen.query_one(DataTable)
        # the zero-customs Phase 8 look over the committed registries
        assert _status_line(screen) == SEL_STATUS_LINE.format(
            n=0, models_total=62, m=0, tasks_total=50,
        )

        await pilot.press("w")
        await pilot.pause()
        wizard = app.screen
        assert isinstance(wizard, WizardModal)
        await _type_wizard_field(pilot, wizard, "key", "loop-model-lm")
        await _type_wizard_field(pilot, wizard, "model-path",
                                 "models/loop-lm")
        await _submit_wizard(pilot, app, wizard)
        # the gauntlet ran dry-run and the real store landed the entry
        assert gauntlet.calls == [(LEG_DRY_RUN, "models", "loop-model-lm")]
        landed, _error = custom_entries.read_entries("models")
        assert "loop-model-lm" in landed
        assert custom.refreshes == 1
        # dismiss (a land clears the form: esc returns, esc dismisses)
        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SelectionScreen)
        await app.workers.wait_for_complete()
        await pilot.pause()

        # the refreshed table: the badge on the new row + the count line
        keys = _row_keys(table)
        assert keys.index("loop-model-lm") == 62  # appended after official
        assert _row(table, 62)[1] == f"{SEL_CUSTOM_BADGE} loop-model-lm"
        assert _status_line(screen) == (
            SEL_STATUS_LINE.format(
                n=0, models_total=63, m=0, tasks_total=50,
            ) + " · " + SEL_COUNT_CUSTOM_SEGMENT.format(
                official_models=62, official_datasets=50,
                custom_models=1, custom_datasets=0,
            )
        )

        # e: the disable keeps the row visible with the suffix while the
        # REAL loader drops it, and the count still counts it
        table.move_cursor(row=62)
        await pilot.pause()
        await pilot.press("e")
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert SEL_TOGGLE_DISABLED_TOAST.format(
            key="loop-model-lm") in _toasts(app)
        assert _row(table, 62)[1] == (
            f"{SEL_CUSTOM_BADGE} loop-model-lm{SEL_DISABLED_SUFFIX}")
        assert "loop-model-lm" not in (
            registry_loader.load_models_registry())
        assert SEL_COUNT_CUSTOM_SEGMENT.format(
            official_models=62, official_datasets=50,
            custom_models=1, custom_datasets=0,
        ) in _status_line(screen)

        assert official.read_bytes() == before  # zero official writes


async def test_full_loop_datasets_wizard_runs_both_legs_and_disables(
        monkeypatch, tmp_path):
    """The dataset-kind loop once: both gauntlet legs run (dry-run +
    audit), the landed entry badges the dataset table with the 自定义
    count, and e disables with the loader exclusion."""
    _pin_roots(monkeypatch, tmp_path)
    official = Path(registry_loader.__file__).parent / (
        "datasets_info.json")
    before = official.read_bytes()
    gauntlet = _AllPassGauntlet()
    custom = _LoopCustomService(gauntlet)
    app = _app(SelectionBackend())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app, custom)
        screen = app.screen
        table = screen.query_one(DataTable)
        await pilot.press("m")  # the datasets table routes the kind
        await pilot.pause()

        await pilot.press("w")
        await pilot.pause()
        wizard = app.screen
        assert isinstance(wizard, WizardModal)
        await _type_wizard_field(pilot, wizard, "key", "loop-ds")
        await _type_wizard_field(pilot, wizard, "dataset-path",
                                 "datasets/loop-ds")
        await _submit_wizard(pilot, app, wizard)
        # BOTH legs ran for the dataset kind, dry-run first
        assert [call[0] for call in gauntlet.calls] == [
            LEG_DRY_RUN, LEG_AUDIT]
        landed, _error = custom_entries.read_entries("datasets")
        assert "loop-ds" in landed
        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SelectionScreen)
        await app.workers.wait_for_complete()
        await pilot.pause()

        keys = _row_keys(table)
        assert keys.index("loop-ds") == 50  # appended after official
        assert _row(table, 50)[1] == f"{SEL_CUSTOM_BADGE} loop-ds"
        assert _status_line(screen) == (
            SEL_STATUS_LINE.format(
                n=0, models_total=62, m=0, tasks_total=51,
            ) + " · " + SEL_COUNT_CUSTOM_SEGMENT.format(
                official_models=62, official_datasets=50,
                custom_models=0, custom_datasets=1,
            )
        )

        table.move_cursor(row=50)
        await pilot.pause()
        await pilot.press("e")
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert SEL_TOGGLE_DISABLED_TOAST.format(key="loop-ds") in _toasts(
            app)
        assert _row(table, 50)[1] == (
            f"{SEL_CUSTOM_BADGE} loop-ds{SEL_DISABLED_SUFFIX}")
        assert "loop-ds" not in registry_loader.load_datasets_registry()

        assert official.read_bytes() == before  # zero official writes


# =====================================================================
# Task 1 — the d binding (10-05, D-14: presence-✗ rows enqueue into the
# shared queue; one vocabulary with the data-manager screen's d)
# =====================================================================

_KEY_MISSING_DATASET = "GUE__fake_missing"
_KEY_PRESENT_DATASET = "GUE__fake_present"


def _d_fixture_data():
    """The d-binding fixture: datasets = one missing + one present; one
    model row (the models-view no-op proof)."""
    return SelectionData(
        model_entries=(
            {
                "key": _KEY_OFFICIAL_MODEL, "type": "MLM",
                "species": "plants", "size_m": 86.0,
                "card": {"type": "MLM"},
            },
        ),
        dataset_entries=(
            {
                "key": _KEY_MISSING_DATASET, "category": "Animals",
                "type": "binary", "metric": "f1",
                "card": {"Category": "Animals", "type": "binary",
                         "metric": "f1"},
            },
            {
                "key": _KEY_PRESENT_DATASET, "category": "Animals",
                "type": "binary", "metric": "f1",
                "card": {"Category": "Animals", "type": "binary",
                         "metric": "f1"},
            },
        ),
        presence={
            _KEY_MISSING_DATASET: Presence(
                status=PRESENCE_MISSING, rows=None),
            _KEY_PRESENT_DATASET: Presence(
                status=PRESENCE_PRESENT, rows=(100, 20, 20)),
        },
    )


class _QueueFake:
    """The enqueue-seam fake (the FakeEnvCheckService idiom): scripted
    ``EnqueueOutcome`` per key (default enqueued), every call recorded —
    no real registry read, no state write, no CLI probe."""

    def __init__(self, outcomes=None):
        self.outcomes = dict(outcomes or {})
        self.enqueue_calls = []

    def enqueue(self, key):
        self.enqueue_calls.append(key)
        outcome = self.outcomes.get(key)
        if outcome is not None:
            return outcome
        return EnqueueOutcome(action="enqueued", key=key)


async def test_d_enqueues_a_missing_row_through_the_shared_seam_and_kicks(
        monkeypatch, tmp_path):
    """d on a presence-✗ datasets row enqueues the cursor's key through
    the SAME shared-queue seam the data-manager screen uses (recorded
    key), fires the app-level kick, and toasts the enqueued copy — the
    table stays mounted (enqueuing never navigates away)."""
    _pin_state_root(monkeypatch, tmp_path)
    queue = _QueueFake()
    kicks = []
    monkeypatch.setattr(
        DnallmMarkTui, "kick_download_queue",
        lambda self: kicks.append(True),
    )
    app = _app(_SelectionFake(data=_d_fixture_data()))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app, queue_fake=queue)
        screen = app.screen
        table = screen.query_one(DataTable)
        await pilot.press("m")  # the datasets table
        await pilot.pause()
        table.move_cursor(row=0)  # the missing row
        await pilot.pause()

        await pilot.press("d")
        await pilot.pause()
        assert queue.enqueue_calls == [_KEY_MISSING_DATASET], (
            "d must enqueue the cursor's dataset key through the seam"
        )
        assert QUEUE_TOAST_ENQUEUED.format(
            key=_KEY_MISSING_DATASET) in _toasts(app)
        assert kicks == [True], "the enqueued outcome must kick the driver"
        assert app.screen is screen, "enqueuing never navigates away"

        # a second d on the same row -> the already-queued toast, no
        # second kick (the D-08 idempotence surfaced, never silent)
        queue.outcomes[_KEY_MISSING_DATASET] = EnqueueOutcome(
            action="already_queued", key=_KEY_MISSING_DATASET)
        await pilot.press("d")
        await pilot.pause()
        assert queue.enqueue_calls == [_KEY_MISSING_DATASET] * 2
        assert QUEUE_TOAST_ALREADY_QUEUED.format(
            key=_KEY_MISSING_DATASET) in _toasts(app)
        assert kicks == [True], "already_queued never kicks"


async def test_d_on_a_present_row_is_a_noop_with_the_honest_toast(
        monkeypatch, tmp_path):
    """d on a present row never reaches the service — the present toast
    fires and nothing enqueues (never silent, never duplicate work)."""
    _pin_state_root(monkeypatch, tmp_path)
    queue = _QueueFake()
    kicks = []
    monkeypatch.setattr(
        DnallmMarkTui, "kick_download_queue",
        lambda self: kicks.append(True),
    )
    app = _app(_SelectionFake(data=_d_fixture_data()))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app, queue_fake=queue)
        table = app.screen.query_one(DataTable)
        await pilot.press("m")
        await pilot.pause()
        table.move_cursor(row=1)  # the present row
        await pilot.pause()

        await pilot.press("d")
        await pilot.pause()
        assert SEL_ENQUEUE_PRESENT_TOAST in _toasts(app)
        assert queue.enqueue_calls == []
        assert kicks == []


async def test_d_on_a_shape_d_row_renders_the_disabled_reason_toast(
        monkeypatch, tmp_path):
    """A disabled (shape-D) channel outcome renders the SAME disabled
    toast the data-manager screen renders, carrying the key — always
    diagnosable (R-02); never a kick."""
    _pin_state_root(monkeypatch, tmp_path)
    queue = _QueueFake(outcomes={
        _KEY_MISSING_DATASET: EnqueueOutcome(
            action="disabled", key=_KEY_MISSING_DATASET,
            reason_code="shape_d_layout",
            source_url="https://www.modelscope.cn/datasets/x/y"),
    })
    kicks = []
    monkeypatch.setattr(
        DnallmMarkTui, "kick_download_queue",
        lambda self: kicks.append(True),
    )
    app = _app(_SelectionFake(data=_d_fixture_data()))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app, queue_fake=queue)
        table = app.screen.query_one(DataTable)
        await pilot.press("m")
        await pilot.pause()
        table.move_cursor(row=0)
        await pilot.pause()

        await pilot.press("d")
        await pilot.pause()
        assert DL_DISABLED_TOAST.format(
            key=_KEY_MISSING_DATASET) in _toasts(app)
        assert queue.enqueue_calls == [_KEY_MISSING_DATASET]
        assert kicks == []


async def test_d_on_the_models_view_is_a_silent_noop(
        monkeypatch, tmp_path):
    """The models table never enqueues (models are not n_audit subjects
    — Phase 8 truth): d returns before any service call, silently."""
    _pin_state_root(monkeypatch, tmp_path)
    queue = _QueueFake()
    app = _app(_SelectionFake(data=_d_fixture_data()))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app, queue_fake=queue)
        table = app.screen.query_one(DataTable)
        # the models view is the mount default; cursor row 0 is a model
        table.move_cursor(row=0)
        await pilot.pause()

        await pilot.press("d")
        await pilot.pause()
        assert queue.enqueue_calls == []
        assert _toasts(app) == [], "the models view stays silent"


async def test_d_persist_failed_outcome_toasts_never_silent(
        monkeypatch, tmp_path):
    """WR-04 on the selection screen: the persist_failed outcome renders
    the same honest never-wrote toast the data-manager screen renders —
    one vocabulary, never silent, never a kick."""
    _pin_state_root(monkeypatch, tmp_path)
    queue = _QueueFake(outcomes={
        _KEY_MISSING_DATASET: EnqueueOutcome(
            action="persist_failed", key=_KEY_MISSING_DATASET),
    })
    kicks = []
    monkeypatch.setattr(
        DnallmMarkTui, "kick_download_queue",
        lambda self: kicks.append(True),
    )
    app = _app(_SelectionFake(data=_d_fixture_data()))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app, queue_fake=queue)
        table = app.screen.query_one(DataTable)
        await pilot.press("m")
        await pilot.pause()
        table.move_cursor(row=0)
        await pilot.pause()

        await pilot.press("d")
        await pilot.pause()
        assert QUEUE_PERSIST_FAILED_TOAST.format(
            key=_KEY_MISSING_DATASET) in _toasts(app)
        assert queue.enqueue_calls == [_KEY_MISSING_DATASET]
        assert kicks == [], "a refused enqueue never kicks"


async def test_d_unknown_outcome_toasts_the_reason_not_mirror_layout(
        monkeypatch, tmp_path):
    """WR-06 on the selection screen: an unknown-channel outcome (e.g.
    a transient registry-read failure) renders the neutral
    channel-unavailable toast naming the machine reason — never the
    shape-D mirror-layout copy that would send the diagnosis the wrong
    way."""
    _pin_state_root(monkeypatch, tmp_path)
    queue = _QueueFake(outcomes={
        _KEY_MISSING_DATASET: EnqueueOutcome(
            action="unknown", key=_KEY_MISSING_DATASET,
            reason_code="registry_unreadable"),
    })
    kicks = []
    monkeypatch.setattr(
        DnallmMarkTui, "kick_download_queue",
        lambda self: kicks.append(True),
    )
    app = _app(_SelectionFake(data=_d_fixture_data()))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app, queue_fake=queue)
        table = app.screen.query_one(DataTable)
        await pilot.press("m")
        await pilot.pause()
        table.move_cursor(row=0)
        await pilot.pause()

        await pilot.press("d")
        await pilot.pause()
        assert DL_UNKNOWN_TOAST.format(
            key=_KEY_MISSING_DATASET,
            reason="registry_unreadable") in _toasts(app)
        assert DL_DISABLED_TOAST.format(
            key=_KEY_MISSING_DATASET) not in _toasts(app)
        assert kicks == []


async def test_bottom_bar_declares_d_between_e_and_v():
    """The bottom bar renders [d]入队 in binding-declaration order
    between [e]停用 and [v]矩阵 (the migration-table disposition)."""
    app = _app(_SelectionFake())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        bar = app.screen.query_one("#nav-left-keycaps", Static)
        content = bar.content
        text = content.plain if isinstance(content, Text) else str(content)
        assert f"[d]{SEL_ENQUEUE_LABEL}" in text
        assert text.index(f"[e]{SEL_TOGGLE_LABEL}") < text.index(
            f"[d]{SEL_ENQUEUE_LABEL}") < text.index(f"[v]{SEL_MATRIX_LABEL}")


# =====================================================================
# Task 2 — the D-11 presence overlay + the live flip (10-05; tier-1
# grade: the REAL backend over the committed baseline + tmp roots)
# =====================================================================

def _seed_queue_state(state_root, entries):
    """Write one queue state file (schema_version 1) under the tmp root."""
    (state_root / "download_queue.json").write_text(json.dumps({
        "schema_version": 1,
        "entries": entries,
    }, ensure_ascii=False), encoding="utf-8")


def _queue_state_entry(key, state, measured=None):
    """One canonical persisted entry (the service's _ENTRY_FIELDS shape)."""
    return {
        "key": key, "kind": "dataset", "state": state,
        "attempts": 1, "enqueued_at": "2026-10-12T10:00:00",
        "started_at": "2026-10-12T10:00:01", "finished_at": None,
        "last_percent": 100, "interrupted": False, "log_path": None,
        "problems": [],
        "reconcile": ({"verdict": "pass", "declared": None,
                       "measured": measured, "unified_eval_n": 1}
                      if measured is not None else None),
    }


def _stage_missing_dataset_keys(monkeypatch, tmp_path, count=1):
    """Stage a fixture n_audit marking the first ``count`` REAL registry
    dataset keys missing (the flip targets).

    The R-03 follow-up rule: the committed baseline is
    maintainer-refreshable (43/50 -> 50/50 landed as a data commit), so
    flip/overlay lanes NEVER derive missing-ness from it — they pin
    their own missing set through the same ``N_AUDIT_PATH`` seam the
    corrupt-file tests use, over real registry keys so the datasets
    table renders the rows. Every other key stages present. Returns the
    staged missing keys.
    """
    dataset_keys = sorted(
        entry["key"]
        for entry in registries_service.load_dataset_entries())
    assert len(dataset_keys) >= count, (
        "the committed registry must carry enough dataset keys"
    )
    staged = dataset_keys[:count]
    present = {"missing": False, "splits": {
        "train": {"rows": 1}, "dev": {"rows": 1}, "test": {"rows": 1}}}
    path = tmp_path / "n-audit-fixture" / "n_audit.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"tasks": {
        key: ({"missing": True} if key in staged else dict(present))
        for key in dataset_keys
    }}), encoding="utf-8")
    monkeypatch.setattr(registries_service, "N_AUDIT_PATH", path)
    return staged


def _dataset_presence_cell(table, key):
    """One dataset row's rendered presence cell (column 6 of 6)."""
    keys = _row_keys(table)
    assert key in keys, f"row {key} must render in the datasets table"
    cell = table.get_row_at(keys.index(key))[5]
    return cell.plain if isinstance(cell, Text) else str(cell)


async def _open_datasets_view(pilot, app, backend):
    """Mount selection over the REAL backend, switch to the datasets
    table, and settle the snapshot worker."""
    app.push_screen(SelectionScreen(
        selection_service=backend,
        marked_models=app._marked_models,
        marked_tasks=app._marked_tasks,
    ))
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()
    await pilot.press("m")
    await pilot.pause()
    return app.screen


async def test_overlay_flips_missing_presence_to_present_and_back(
        monkeypatch, tmp_path):
    """Tier-1-grade snapshot proof: a done entry with measured rows in
    the pinned state file flips the staged-missing key's cell to
    present WITH the measured counts (the D-11 flip); removing the
    state file returns the row to missing — the fixture n_audit view
    rules when no overlay exists. (The missing target is STAGED — the
    R-03 follow-up rule: the committed baseline is maintainer-
    refreshable and carries no missing keys today.)"""
    _pin_roots(monkeypatch, tmp_path)
    state_root = _pin_state_root(monkeypatch, tmp_path)
    (key,) = _stage_missing_dataset_keys(monkeypatch, tmp_path, count=1)
    _seed_queue_state(state_root, [
        _queue_state_entry(key, "done",
                           {"train": 12345, "dev": 678, "test": 90})])
    app = _app(SelectionBackend())
    async with app.run_test(size=(120, 40)) as pilot:
        screen = await _open_datasets_view(pilot, app, SelectionBackend())
        table = screen.query_one(DataTable)
        assert _dataset_presence_cell(table, key) == (
            SEL_PRESENCE_PRESENT.format(
                train="12,345", dev="678", test="90")), (
            "the reconciled key must render present with the "
            "thousands-separated measured counts"
        )

        # remove the state file -> the fixture n_audit view rules again
        (state_root / "download_queue.json").unlink()
        screen._load_data()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert _dataset_presence_cell(table, key) == SEL_PRESENCE_MISSING, (
            "with no overlay the staged n_audit view rules"
        )


async def test_mismatch_and_failed_entries_never_flip_presence(
        monkeypatch, tmp_path):
    """UI-SPEC semantic 6: only reconcile-PASS (done) entries belong in
    the overlay — mismatch and failed entries in the state file leave
    the staged-missing cells missing (the number would be wrong)."""
    _pin_roots(monkeypatch, tmp_path)
    state_root = _pin_state_root(monkeypatch, tmp_path)
    mismatch_key, failed_key = _stage_missing_dataset_keys(
        monkeypatch, tmp_path, count=2)
    _seed_queue_state(state_root, [
        _queue_state_entry(mismatch_key, "mismatch",
                           {"train": 1, "dev": 2, "test": 3}),
        _queue_state_entry(failed_key, "failed",
                           {"train": 4, "dev": 5, "test": 6}),
    ])
    app = _app(SelectionBackend())
    async with app.run_test(size=(120, 40)) as pilot:
        screen = await _open_datasets_view(pilot, app, SelectionBackend())
        table = screen.query_one(DataTable)
        assert _dataset_presence_cell(
            table, mismatch_key) == SEL_PRESENCE_MISSING
        assert _dataset_presence_cell(
            table, failed_key) == SEL_PRESENCE_MISSING


async def test_live_flip_through_the_app_event_forward(
        monkeypatch, tmp_path):
    """The D-11 live flip: a done QueueEvent forwarded by the app (the
    10-04 generic forward) reaches the MOUNTED selection screen's
    apply_queue_event, re-runs the snapshot worker, and the presence
    cell flips in place — the screen never remounts and the app-level
    flip toast fires. (Missing target staged per the R-03 follow-up
    rule — never derived from the refreshable committed baseline.)"""
    _pin_roots(monkeypatch, tmp_path)
    state_root = _pin_state_root(monkeypatch, tmp_path)
    (key,) = _stage_missing_dataset_keys(monkeypatch, tmp_path, count=1)
    app = _app(SelectionBackend())
    async with app.run_test(size=(120, 40)) as pilot:
        screen = await _open_datasets_view(pilot, app, SelectionBackend())
        table = screen.query_one(DataTable)
        assert _dataset_presence_cell(table, key) == SEL_PRESENCE_MISSING

        # the reconcile lands in the state file; the driver posts done
        _seed_queue_state(state_root, [
            _queue_state_entry(key, "done",
                               {"train": 500, "dev": 50, "test": 5})])
        event = QueueEvent(
            run_id="driver-1", key=key, kind="dataset", state="done",
            last_percent=100, problems=(), details=(), log_path=None)
        app.on_queue_event_message(
            QueueEventMessage(event, app._queue_generation))
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.pause()

        assert _dataset_presence_cell(table, key) == (
            SEL_PRESENCE_PRESENT.format(train="500", dev="50", test="5")), (
                "the done event must flip the presence cell live"
            )
        assert app.screen is screen, "the flip never remounts the screen"
        assert QUEUE_FLIP_TOAST.format(key=key) in _toasts(app)
