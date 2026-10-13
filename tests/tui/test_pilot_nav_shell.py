"""
Tier-2 Pilot suite for the navigation shell (Phase 9, 09-03, D-13..D-16).

Pins the two chrome bars on the base screens against the REAL
``DnallmMarkTui`` with constructor-injected deterministic fakes (no real
kernel, no real registry read — the D-03 discipline):

- the top menu bar: six slots with the RATIFIED verbatim resource-noun
  names, digit-prefixed, the active slot carrying the ◆ prefix (glyph +
  bold + accent triple channel), placeholder 5 dim with the
  未开放 suffix (slots 3/4 are REAL since 10-04/11-06), and the whole
  slot set fitting within 80 columns at
  80x24 (the fixed-vocabulary overflow edge);
- placeholder activation is never silent: digit 5 fires the
  Phase-naming toast and never switches screens; digits 1/2/4/6 switch
  to the live screens (slot 4 = the run-config screen, 11-06; slot 6 =
  the About screen) with the ◆ tracking the
  active slot;
- the bottom bar: the left segment renders the active screen's command
  keycaps in binding-declaration order (the ``_binding_row`` source the
  help modal uses) clipped at the available width with a trailing … at
  80 columns on the selection screen — and the ? help modal still lists
  the COMPLETE map (the discoverability backstop);
- digit navigation scope (Interaction #1): digits are plain per-screen
  bindings — a focused Input consumes digit keystrokes first (typing 1
  into the selection filter types 1, never switches screens).

Task 3 extends this module with the migration assertions (env s
retirement reflection, matrix no-bars, below-minimum guard interplay,
about wrap, i18n greps).
"""

import re
from pathlib import Path

from rich.text import Text
from textual.widgets import Input, Static

import tui.screens.about as about_screen_module
import tui.screens.nav as nav_module
from tui.app import DnallmMarkTui, HelpModal
from tui.screens.about import AboutScreen
from tui.screens.data_manager import DataManagerScreen
from tui.screens.env_check import EnvCheckScreen
from tui.screens.nav import BottomBar, TopMenuBar
from tui.screens.run_config import PickerEntries, RunConfigScreen
from tui.screens.selection import PresetMenu, SelectionData, SelectionScreen
from tui.services import registries as registries_service
from tui.services import selection as selection_service
from tui.services.download_queue import merge_presence
from tui.services.run_config import PreviewResult, RunSpec
from tui.strings import (
    APP_HELP_ROW,
    ENV_DETAIL_LABEL,
    ENV_REFRESH_LABEL,
    NAV_LABEL_ABOUT,
    NAV_LABEL_DATA,
    NAV_LABEL_ENV,
    NAV_LABEL_MONITOR,
    NAV_LABEL_RUN_CONFIG,
    NAV_LABEL_SELECTION,
)

# Module files for the i18n grep gates (Task 3 extension).
_NAV_MODULE_FILE = Path(nav_module.__file__)
_ABOUT_SCREEN_FILE = Path(about_screen_module.__file__)


# =====================================================================
# Deterministic fakes (D-03: no real kernel / registry read)
# =====================================================================

class _EnvCacheHitFake:
    """The minimal env-check service fake (same-day cache hit)."""

    def cached_results(self):
        from env_smoke import CheckResult

        from tui.strings import ENV_KERNEL_LABELS
        return ("2026-10-11 09:30", tuple(
            CheckResult(name=k, ok=True, lines=(f"PASS: {k}",))
            for k in ENV_KERNEL_LABELS
        ))

    def kernels(self):
        raise AssertionError("a cache-hit boot must never spawn the worker")

    def persist(self, results):
        raise AssertionError("a cache-hit boot must never persist")


class _SelectionFake:
    """The minimal selection-service fake (empty data, real grammar)."""

    def load_selection_data(self):
        return SelectionData()

    def preset_menu(self):
        return PresetMenu(options=(), load_error=None)

    def custom_names(self):
        return ()

    def save_preset(self, name, models, tasks):
        raise AssertionError("the nav-shell tests never save presets")

    def parse_filter(self, query):
        return selection_service.parse_filter_query(query)

    def apply_filter(self, entries, parsed):
        return selection_service.apply_filter(entries, parsed.terms)

    def import_template(self, path):
        raise AssertionError("the nav-shell tests never import templates")

    def export_template(self, path, models, tasks):
        raise AssertionError("the nav-shell tests never export templates")

    def export_tiers(self, path, models, tasks):
        raise AssertionError("the nav-shell tests never export tiers")


class _QueueDriverFake:
    """The minimal download-queue fake (10-04): the driver surface only —
    an empty inert queue plus the two read legs the slot-3 screen mount
    needs; ``run_task`` can never legitimately run here."""

    def load(self):
        return None

    def entries(self):
        return ()

    def claim_next(self):
        return None

    def missing_datasets(self):
        return ()

    def merged_audit_tasks(self):
        # CR-01: the real Backend's presence-summary seam — delegate to
        # the same pure rule (empty queue -> the committed view alone)
        return merge_presence(registries_service.load_n_audit(), {})

    def probe_zenodo(self):
        return "not_public"

    def run_task(self, *args, **kwargs):
        raise AssertionError("the nav-shell tests never run queue tasks")


class _RunConfigShellFake:
    """The minimal run-config service fake (11-06): empty registries,
    the default spec, the real pure grammar legs — the slot-4 screen
    mounts deterministically without a registry read or XDG write."""

    def picker_entries(self):
        return PickerEntries()

    def load_state(self):
        return RunSpec(models=(), tasks=())

    def save_state(self, spec):
        del spec

    def preview(self, spec):
        return PreviewResult(
            models_count=len(spec.models), tasks_count=len(spec.tasks),
            seeds_count=len(spec.seeds), fractions_count=None,
            cells_count=0, cells=(),
            problems=(("empty_selection", None),))

    def parse_params(self, raw):
        from tui.services import run_config as run_config_module

        return run_config_module.parse_params(raw)

    def resolve_dirs(self, spec):
        from tui.services import run_config as run_config_module

        return run_config_module.resolve_dirs(spec)

    def probe_ineligible(self):
        return frozenset()

    def path_state(self, value):
        return "unset" if not value else "missing"

    def parse_filter(self, query):
        return selection_service.parse_filter_query(query)

    def apply_filter(self, entries, parsed):
        return selection_service.apply_filter(entries, parsed.terms)

    def compose_argv(self, spec):
        raise AssertionError("the nav-shell tests never compose argv")

    def expected_phrase(self, output_root):
        return Path(output_root).name

    def phrase_matches(self, typed, output_root):
        return typed == self.expected_phrase(output_root)


class _LauncherShellFake:
    """The minimal launcher fake (11-06): no live sweeps, no launches."""

    def env_preflight(self, kernels=None):
        from tui.services.sweep_launcher import EnvPreflight

        return EnvPreflight(
            can_launch=True, reasons=(), failed_kernels=())

    def gate_confirm_data(self, spec):
        raise AssertionError("the nav-shell tests never gate")

    def launch_spec(self, spec, phrase=None):
        raise AssertionError("the nav-shell tests never launch")

    def kill_sweep(self, root):
        raise AssertionError("the nav-shell tests never kill")

    def detach(self, root):
        raise AssertionError("the nav-shell tests never detach")

    def live_sweeps(self):
        return ()

    def tee_path_for(self, root):
        return None


class _MonitorShellFake:
    """The minimal monitor-service fake (11-07): an empty scan — the
    slot-5 screen mounts deterministically with no artifact read."""

    def full_scan(self, prev_watermarks=None):
        from tui.services.sweep_monitor import ScanResult

        return ScanResult(sweeps=(), watermarks={})

    def frontier_scan(self, root):
        from tui.services.sweep_monitor import FrontierSnapshot

        return FrontierSnapshot(
            root=Path(str(root)), state="artifacts_only",
            newest_mtime=None, newest_cell=None, cell_states={})

    def cells_view(self, root):
        return ()

    def stats(self, root, expected_total=None, fallback_start=None):
        from tui.services.sweep_monitor import EtaEstimate, SweepStats

        return SweepStats(
            done=0, total=None, current=None, elapsed_seconds=None,
            eta=EtaEstimate("none", None, None, None))

    def sweep_scale(self, root):
        return None

    def resume_count(self, root):
        return 0

    def failures_view(self, root):
        return ()

    def read_log_tail(self, path, max_lines=200, max_bytes=65536):
        return None

    def is_sweep_root(self, path):
        return False

    def add_manual_root(self, path):
        raise AssertionError("the nav-shell tests never attach roots")


class _MonitorLauncherShellFake:
    """The minimal monitor launcher fake (11-07): no live sweeps."""

    def env_preflight(self, kernels=None):
        raise AssertionError("the nav-shell tests never gate a re-run")

    def launch_from_failures(self, failures_path, seeds, output_root,
                             peft="none", config_variant="none"):
        raise AssertionError("the nav-shell tests never re-run")

    def live_sweeps(self):
        return ()

    def tee_path_for(self, root):
        return None


def _pin_config_roots(monkeypatch, tmp_path):
    """Pin the config roots at tmp_path (the real home is never read)."""
    config = tmp_path / "config"
    config.mkdir(exist_ok=True)
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(config))
    monkeypatch.setenv(
        "DNALLMMARK_CUSTOM_REGISTRY_DIR", str(tmp_path / "custom-empty"))


def _app():
    """The real app with cache-hit env fake + the empty fakes."""
    return DnallmMarkTui(
        env_check_service=_EnvCacheHitFake(),
        selection_service=_SelectionFake(),
        download_queue_service=_QueueDriverFake(),
        run_config_service=_RunConfigShellFake(),
        launcher_service=_LauncherShellFake(),
        monitor_service=_MonitorShellFake(),
        monitor_launcher=_MonitorLauncherShellFake(),
    )


def _plain(content) -> str:
    """Plain text of a Static's content (cells may carry rich Text)."""
    return content.plain if isinstance(content, Text) else str(content)


def _slot_texts(screen):
    """The top bar's slot contents as plain strings, slot order."""
    bars = list(screen.query(TopMenuBar))
    assert bars, "the top menu bar must render on the base screen"
    return [_plain(child.content) for child in bars[0].children]


def _slot_widgets(screen):
    """The top bar's slot widgets (class assertions), slot order."""
    return list(screen.query_one(TopMenuBar).children)


def _toast_messages(app):
    """The active notification messages (the toast assertions)."""
    return [notification.message for notification in app._notifications]


async def _open_selection(pilot, app):
    """Push the selection screen and deterministically await its load."""
    app.push_screen(app.build_selection_screen())
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()


# =====================================================================
# The top menu bar (D-13)
# =====================================================================

async def test_top_bar_six_verbatim_slots_fit_80_triple_channel():
    """Six slots, verbatim names, ◆+bold+accent active, fit at 80x24."""
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, EnvCheckScreen)
        texts = _slot_texts(app.screen)
        widgets = _slot_widgets(app.screen)

        # six slots, the ratified verbatim resource-noun names, digit-first;
        # slot 3 is REAL since 10-04, slot 4 since 11-06, and slot 5
        # since 11-07 (no suffix anywhere — every slot is real)
        assert len(texts) == 6, "the bar carries exactly six slots"
        assert texts[0] == f"◆ 1{NAV_LABEL_ENV}", (
            "the ACTIVE slot carries the ◆ prefix (glyph channel)"
        )
        assert texts[1] == f" 2{NAV_LABEL_SELECTION}"
        assert texts[2] == f" 3{NAV_LABEL_DATA}"
        assert texts[3] == f" 4{NAV_LABEL_RUN_CONFIG}", (
            "slot 4 is REAL since 11-06 — no placeholder suffix"
        )
        assert texts[4] == f" 5{NAV_LABEL_MONITOR}", (
            "slot 5 is REAL since 11-07 — no placeholder suffix"
        )
        assert texts[5] == f" 6{NAV_LABEL_ABOUT}"

        # triple channel: the active slot carries the active class
        # (bold + $accent via styles.tcss — color+weight after the glyph)
        assert widgets[0].has_class("nav-slot-active"), (
            "the active slot must render bold + accent (color/weight channel)"
        )
        # no placeholder classes remain anywhere (every slot is real)
        for widget in widgets:
            assert not widget.has_class("nav-slot-placeholder"), (
                "no slot renders the placeholder class after 11-07"
            )
        assert not widgets[3].has_class("nav-slot-placeholder"), (
            "the promoted slot 4 must not render the placeholder class"
        )
        assert not widgets[4].has_class("nav-slot-placeholder"), (
            "the promoted slot 5 must not render the placeholder class"
        )

        # the fixed vocabulary fits within 80 columns at 80x24
        bar = app.screen.query_one(TopMenuBar)
        total = sum(child.content.cell_len for child in bar.children)
        assert total <= 80, (
            f"the six-slot vocabulary must fit 80 columns (is {total})"
        )
        last_edge = (bar.children[-1].region.x
                     + bar.children[-1].region.width)
        assert last_edge <= 80, "no slot may overflow the 80-col grid"


async def test_digits_switch_live_screens_and_track_active_slot(
        monkeypatch, tmp_path):
    """1/2/6 switch to the live screens; ◆ tracks the active slot."""
    _pin_config_roots(monkeypatch, tmp_path)
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.press("2")
        await pilot.pause()
        assert isinstance(app.screen, SelectionScreen), (
            "digit 2 must switch to the selection screen"
        )
        # non-first slots carry their single-space separator before the
        # diamond prefix — strip compares the slot content itself
        assert _slot_texts(app.screen)[1].strip() == (
            f"◆ 2{NAV_LABEL_SELECTION}")

        await pilot.press("6")
        await pilot.pause()
        assert isinstance(app.screen, AboutScreen), (
            "digit 6 must switch to the About screen (slot 6)"
        )
        assert _slot_texts(app.screen)[5].strip() == f"◆ 6{NAV_LABEL_ABOUT}"

        await pilot.press("1")
        await pilot.pause()
        assert isinstance(app.screen, EnvCheckScreen), (
            "digit 1 must switch back to the env-check screen"
        )
        assert _slot_texts(app.screen)[0] == f"◆ 1{NAV_LABEL_ENV}"


async def test_placeholder_digits_fire_phase_toast_never_switch():
    """No placeholder slots remain: digits 3/4/5 all switch to their
    real screens with zero placeholder artifacts (slot 5 promoted by
    11-07); the phase toast vocabulary retires with the last
    placeholder."""
    from tui.screens.monitor import MonitorScreen

    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        # slot 5 (11-07): the real monitor screen, no phase toast
        await pilot.press("5")
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, MonitorScreen), (
            "digit 5 must switch to the real monitor screen"
        )
        assert not _toast_messages(app), (
            "slot 5 must never fire the placeholder phase toast"
        )
        await pilot.press("4")
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, RunConfigScreen), (
            "digit 4 must switch to the real run-config screen"
        )

        # slot 3 (10-04): the real data-manager screen, no phase toast
        await pilot.press("3")
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, DataManagerScreen), (
            "digit 3 must switch to the real data-manager screen"
        )


# =====================================================================
# The bottom submenu bar (D-15)
# =====================================================================

def _bar_segments(screen):
    """The bottom bar's (left, right) Static pair."""
    bars = list(screen.query(BottomBar))
    assert bars, "the bottom bar must render on the base screen"
    left = bars[0].query_one("#nav-left-keycaps", Static)
    right = bars[0].query_one("#nav-right-keycaps", Static)
    return left, right


async def test_bottom_bar_env_keycaps_and_constant_right_segment():
    """The env keycaps render [r]/[enter] (no s); the right pair is constant."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        left, right = _bar_segments(app.screen)
        left_plain = _plain(left.content)
        assert f"[r]{ENV_REFRESH_LABEL}" in left_plain
        assert f"[enter]{ENV_DETAIL_LABEL}" in left_plain
        assert _plain(right.content) == "[?]帮助 [q]退出"


async def test_bottom_bar_clips_at_80_help_modal_stays_complete():
    """The clip policy: declaration order + trailing … at 80 columns; the
    ? help modal still lists EVERY shown binding (the backstop)."""
    from textual.binding import Binding as BindingType

    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        await _open_selection(pilot, app)
        screen = app.screen
        left, _ = _bar_segments(screen)
        plain = _plain(left.content)
        assert plain.endswith("…"), (
            "the 9-keycap left segment must clip with a trailing ellipsis"
        )
        # declaration order: the primary keycaps render, the least-primary
        # (the trailing [v] keycap) is what the clip drops
        assert "[v]" not in plain, "the clip drops the tail keycaps first"

        # the discoverability backstop: the ? modal lists the COMPLETE map
        await pilot.press("question_mark")
        await pilot.pause()
        assert isinstance(app.screen, HelpModal)
        expected = {}
        for binding in (*app.BINDINGS, *screen.BINDINGS):
            if isinstance(binding, BindingType) and binding.show:
                key = binding.key_display or binding.key
                expected[key] = binding.description
        rows = [str(static.content) for static in app.screen.query(Static)]
        for key, label in expected.items():
            assert APP_HELP_ROW.format(key=key, label=label) in rows, (
                f"the help modal must keep listing [{key}] {label}"
            )
        await pilot.press("escape")
        await pilot.pause()

        # at the 120x40 design grid the full left map renders (no clip)
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        left, _ = _bar_segments(app.screen)
        assert not _plain(left.content).endswith("…"), (
            "the full keycap map renders at the design grid"
        )


# =====================================================================
# Digit navigation scope (Interaction #1 — Input eats digits)
# =====================================================================

async def test_focused_input_eats_digits_no_screen_switch():
    """A focused Input consumes digit keystrokes first (Pilot-proven):
    typing 1 into the selection filter types 1 — the screen never
    switches; once the Input is no longer focused the digit navigates."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        await pilot.press("slash")  # focus the filter Input
        await pilot.pause()
        filter_input = app.screen.query_one("#selection-filter", Input)
        assert app.focused is filter_input

        await pilot.press("1")
        await pilot.pause()
        assert filter_input.value == "1", (
            "the focused Input must consume the digit keystroke"
        )
        assert isinstance(app.screen, SelectionScreen), (
            "typing a digit into the filter must never switch screens"
        )

        # esc clears the filter and refocuses the table — now the digit
        # navigates (the plain binding fires once nothing consumes it)
        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("1")
        await pilot.pause()
        assert isinstance(app.screen, EnvCheckScreen)


async def test_no_priority_digit_binding_exists_anywhere():
    """The prohibition, grep-pinned: no Binding(priority=True) anywhere
    under tui/ — a priority binding would fire before a focused Input
    and break typing (the verified textual semantics)."""
    tui_dir = Path(nav_module.__file__).parents[1]
    offenders = []
    for py in sorted(tui_dir.rglob("*.py")):
        source = py.read_text(encoding="utf-8")
        if re.search(r"priority\s*=\s*True", source):
            offenders.append(py.name)
    assert not offenders, f"priority bindings are prohibited: {offenders}"


# =====================================================================
# Task 3 — the Header/Footer migration, reflection, and guard interplay
# =====================================================================

async def test_env_help_modal_reflects_the_s_removal():
    """The checker note: after the env s binding retires (superseded by
    menu slot 2), the ? help modal lists NO s row — its rows derive from
    the same BINDINGS declarations, so the removal auto-reflects."""
    from tui.strings import APP_HELP_LABEL, APP_QUIT_LABEL

    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.press("question_mark")
        await pilot.pause()
        assert isinstance(app.screen, HelpModal)
        rows = [str(static.content) for static in app.screen.query(Static)]
        # the live map after the migration: q, ?, r, enter — and NO s
        assert rows == [
            APP_HELP_ROW.format(key="q", label=APP_QUIT_LABEL),
            APP_HELP_ROW.format(key="?", label=APP_HELP_LABEL),
            APP_HELP_ROW.format(key="r", label=ENV_REFRESH_LABEL),
            APP_HELP_ROW.format(key="enter", label=ENV_DETAIL_LABEL),
        ], "the help rows must auto-reflect the retired s binding"
        assert not any(row.startswith("[s]") for row in rows)


async def test_base_screens_retire_header_and_footer():
    """The migration: no base screen yields the retired Textual Header
    or Footer widgets (their rows belong to the two bars now; modals
    keep their own 1-row hints)."""
    from textual.widgets import Footer, Header

    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert not list(app.screen.query(Header)), (
            "the env screen must not yield a Header (the top bar owns it)"
        )
        assert not list(app.screen.query(Footer)), (
            "the env screen must not yield a Footer (the bottom bar owns it)"
        )
        await pilot.press("2")
        await pilot.pause()
        assert not list(app.screen.query(Header))
        assert not list(app.screen.query(Footer))
        await pilot.press("6")
        await pilot.pause()
        assert not list(app.screen.query(Header))
        assert not list(app.screen.query(Footer))


async def test_matrix_renders_without_bars_and_never_navigates_on_digits():
    """The matrix auxiliary view renders WITHOUT the shell bars and
    digits never navigate there (no digit bindings exist on it)."""
    from tui.screens.matrix import MatrixScreen

    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_selection(pilot, app)
        await pilot.press("v")
        await pilot.pause()
        assert isinstance(app.screen, MatrixScreen)
        assert not list(app.screen.query(TopMenuBar)), (
            "the matrix renders no menu bars (the migration table)"
        )
        assert not list(app.screen.query(BottomBar))
        # digits are dead on the matrix — the screen never switches
        for digit in ("1", "6"):
            await pilot.press(digit)
            await pilot.pause()
            assert isinstance(app.screen, MatrixScreen), (
                "digit navigation must never fire on the matrix view"
            )
        # esc still pops back to the selection screen (unchanged)
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SelectionScreen)


async def test_bars_hidden_below_minimum_grid_guard_takes_over():
    """D-16 interplay: below 80x24 the min-size guard is the whole
    surface (no bars render); growing back restores the screen WITH its
    bars — zero guard-code changes."""
    from tui.app import MinSizeScreen

    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert list(app.screen.query(TopMenuBar)), "bars render above minimum"

        await pilot.resize_terminal(60, 20)
        await pilot.pause()
        assert isinstance(app.screen, MinSizeScreen)
        assert not list(app.screen.query(TopMenuBar)), (
            "the guard screen renders NO bars (the message is the surface)"
        )
        assert not list(app.screen.query(BottomBar))

        await pilot.resize_terminal(120, 40)
        await pilot.pause()
        assert isinstance(app.screen, EnvCheckScreen)
        assert list(app.screen.query(TopMenuBar)), (
            "growing back restores the bars with the screen"
        )
        assert list(app.screen.query(BottomBar))


# =====================================================================
# Task 3 — the About screen over a fake service (rows, tolerance, wrap)
# =====================================================================

class _AboutFake:
    """Deterministic about-service fake (the injection seam's fake side)."""

    def __init__(self, data):
        self._data = data

    def derive_about_data(self):
        return self._data


def _about_data(**overrides):
    """A representative snapshot (torch absent — the CPU-lane case)."""
    from tui.services.about import AboutData
    from tui.services.registries import RegistryCounts

    fields = {
        "software_version": "0.7.1",
        "git_sha": "a8dba7c",
        "official_counts": RegistryCounts(62, 50),
        "custom_counts": (1, 0),
        "n_audit_present": True,
        "deps": {
            "textual": "8.2.8",
            "platformdirs": "4.13.0",
            "jsonschema": "4.26.0",
            "numpy": "2.5.3",
            "torch": None,
        },
    }
    fields.update(overrides)
    # explicit keyword construction (ty cannot type a dict **splat)
    return AboutData(
        software_version=fields["software_version"],
        git_sha=fields["git_sha"],
        official_counts=fields["official_counts"],
        custom_counts=fields["custom_counts"],
        n_audit_present=fields["n_audit_present"],
        deps=fields["deps"],
    )


async def _open_about(pilot, app, data):
    app.push_screen(AboutScreen(about_service=_AboutFake(data)))
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()


def _about_value(screen, row_id) -> str:
    content = screen.query_one(f"#about-value-{row_id}", Static).content
    return content.plain if isinstance(content, Text) else str(content)


async def test_about_screen_renders_five_rows_with_tolerant_values():
    """Five fixed rows; absent deps render the constant; counts honest."""
    from tui.strings import (
        ABOUT_DEP_ABSENT,
        ABOUT_MILESTONE_STAGE,
        ABOUT_N_AUDIT_PRESENT,
        ABOUT_ROW_DATA,
        ABOUT_ROW_DEPS,
        ABOUT_ROW_MILESTONE,
        ABOUT_ROW_REPO,
        ABOUT_ROW_SOFTWARE,
        ABOUT_TITLE,
        ABOUT_VALUE_DATA,
        ABOUT_VALUE_SOFTWARE_WITH_SHA,
    )

    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await _open_about(pilot, app, _about_data())
        screen = app.screen
        assert isinstance(screen, AboutScreen)

        labels = [str(label.content) for label in screen.query(".about-label")]
        assert labels == [
            ABOUT_ROW_SOFTWARE, ABOUT_ROW_DATA, ABOUT_ROW_MILESTONE,
            ABOUT_ROW_DEPS, ABOUT_ROW_REPO,
        ]
        assert str(screen.query_one("#about-title").content) == ABOUT_TITLE

        assert _about_value(screen, "software") == (
            ABOUT_VALUE_SOFTWARE_WITH_SHA.format(
                version="0.7.1", sha="a8dba7c"))
        assert _about_value(screen, "data") == ABOUT_VALUE_DATA.format(
            om=62, od=50, cm=1, cd=0, audit=ABOUT_N_AUDIT_PRESENT)
        assert _about_value(screen, "milestone") == ABOUT_MILESTONE_STAGE
        deps = _about_value(screen, "deps")
        assert f"torch {ABOUT_DEP_ABSENT}" in deps, (
            "an absent package renders the constant (dim, per-package)"
        )
        assert "textual 8.2.8" in deps
        from tui.services.about import REPO_URL
        assert _about_value(screen, "repo") == REPO_URL


async def test_about_values_wrap_never_elide():
    """Long values wrap onto extra rows — nothing is ever elided (the
    wrapping value column contract; at 80 columns a long deps line
    exceeds the column budget)."""
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        data = _about_data(deps={
            "textual": "8.2.8",
            "platformdirs": "4.13.0",
            "jsonschema": "4.26.0",
            "numpy": "2.5.3",
            "torch": "2.11.0+cu130-with-a-very-long-local-version-string",
        })
        await _open_about(pilot, app, data)
        screen = app.screen
        value = screen.query_one("#about-value-deps", Static)
        plain = _about_value(screen, "deps")
        assert Text(plain).cell_len > 60, "the fixture value must be long"
        assert "…" not in plain, "values are never elided"
        assert value.size.height >= 2, (
            "a value longer than the column wraps onto extra rows"
        )


# =====================================================================
# Task 3 — i18n greps over the new screen modules
# =====================================================================

def test_nav_module_carries_zero_chinese_literals():
    """I18N-01 single home: no operator-facing copy in tui/screens/nav.py."""
    source = _NAV_MODULE_FILE.read_text(encoding="utf-8")
    offenders = re.findall(r"[一-鿿]", source)
    assert not offenders, (
        "Chinese literals must live in tui/strings.py only "
        f"({len(offenders)} found in {_NAV_MODULE_FILE.name})"
    )


def test_about_screen_module_carries_zero_chinese_literals():
    """I18N-01 single home: no operator-facing copy in the about screen."""
    source = _ABOUT_SCREEN_FILE.read_text(encoding="utf-8")
    offenders = re.findall(r"[一-鿿]", source)
    assert not offenders, (
        "Chinese literals must live in tui/strings.py only "
        f"({len(offenders)} found in {_ABOUT_SCREEN_FILE.name})"
    )
