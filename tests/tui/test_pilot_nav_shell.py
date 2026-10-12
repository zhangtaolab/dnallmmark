"""
Tier-2 Pilot suite for the navigation shell (Phase 9, 09-03, D-13..D-16).

Pins the two chrome bars on the base screens against the REAL
``DnallmMarkTui`` with constructor-injected deterministic fakes (no real
kernel, no real registry read — the D-03 discipline):

- the top menu bar: six slots with the RATIFIED verbatim resource-noun
  names, digit-prefixed, the active slot carrying the ◆ prefix (glyph +
  bold + accent triple channel), placeholders 3/4/5 dim with the
  未开放 suffix, and the whole slot set fitting within 80 columns at
  80x24 (the fixed-vocabulary overflow edge);
- placeholder activation is never silent: digits 3/4/5 fire the
  Phase-naming toast and never switch screens; digits 1/2/6 switch to
  the live screens (slot 6 = the About screen) with the ◆ tracking the
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
from textual.widgets import DataTable, Input, Static

import tui.screens.about as about_screen_module
import tui.screens.nav as nav_module
from tui.app import DnallmMarkTui, HelpModal, MinSizeScreen
from tui.screens.about import AboutScreen
from tui.screens.env_check import EnvCheckScreen
from tui.screens.nav import BottomBar, TopMenuBar
from tui.screens.selection import SelectionScreen
from tui.screens.selection import PresetMenu, SelectionData
from tui.services import selection as selection_service
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
    NAV_PLACEHOLDER_SUFFIX,
    NAV_PLACEHOLDER_TOAST,
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

    def parse_filter(self, query):
        return selection_service.parse_filter_query(query)

    def apply_filter(self, entries, parsed):
        return selection_service.apply_filter(entries, parsed.terms)


def _pin_config_roots(monkeypatch, tmp_path):
    """Pin the config roots at tmp_path (the real home is never read)."""
    config = tmp_path / "config"
    config.mkdir(exist_ok=True)
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(config))
    monkeypatch.setenv(
        "DNALLMMARK_CUSTOM_REGISTRY_DIR", str(tmp_path / "custom-empty"))


def _app():
    """The real app with cache-hit env fake + the empty selection fake."""
    return DnallmMarkTui(
        env_check_service=_EnvCacheHitFake(),
        selection_service=_SelectionFake(),
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

        # six slots, the ratified verbatim resource-noun names, digit-first
        assert len(texts) == 6, "the bar carries exactly six slots"
        assert texts[0] == f"◆ 1{NAV_LABEL_ENV}", (
            "the ACTIVE slot carries the ◆ prefix (glyph channel)"
        )
        assert texts[1] == f" 2{NAV_LABEL_SELECTION}"
        assert texts[2] == f" 3{NAV_LABEL_DATA}{NAV_PLACEHOLDER_SUFFIX}"
        assert texts[3] == f" 4{NAV_LABEL_RUN_CONFIG}{NAV_PLACEHOLDER_SUFFIX}"
        assert texts[4] == f" 5{NAV_LABEL_MONITOR}{NAV_PLACEHOLDER_SUFFIX}"
        assert texts[5] == f" 6{NAV_LABEL_ABOUT}"

        # triple channel: the active slot carries the active class
        # (bold + $accent via styles.tcss — color+weight after the glyph)
        assert widgets[0].has_class("nav-slot-active"), (
            "the active slot must render bold + accent (color/weight channel)"
        )
        # placeholders render dim (the muted class) — never dead-looking
        for placeholder in widgets[2:5]:
            assert placeholder.has_class("nav-slot-placeholder"), (
                "placeholder slots render dim with the suffix"
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
        assert _slot_texts(app.screen)[1] == f"◆ 2{NAV_LABEL_SELECTION}"

        await pilot.press("6")
        await pilot.pause()
        assert isinstance(app.screen, AboutScreen), (
            "digit 6 must switch to the About screen (slot 6)"
        )
        assert _slot_texts(app.screen)[5] == f"◆ 6{NAV_LABEL_ABOUT}"

        await pilot.press("1")
        await pilot.pause()
        assert isinstance(app.screen, EnvCheckScreen), (
            "digit 1 must switch back to the env-check screen"
        )
        assert _slot_texts(app.screen)[0] == f"◆ 1{NAV_LABEL_ENV}"


async def test_placeholder_digits_fire_phase_toast_never_switch():
    """3/4/5 are never silent: the phase toast fires, the screen holds."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        for digit, phase in (("3", 10), ("4", 11), ("5", 12)):
            await pilot.press(digit)
            await pilot.pause()
            assert NAV_PLACEHOLDER_TOAST.format(n=phase) in (
                _toast_messages(app)), (
                f"digit {digit} must toast the delivering phase {phase}"
            )
            assert isinstance(app.screen, EnvCheckScreen), (
                f"digit {digit} must never switch screens"
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
