"""
app.py — ``DnallmMarkTui``, the console's composition root (Phase 8, 08-02
skeleton; 08-03 tracer wiring; 08-06 full root).

Composition root ONLY: the app wires the title, the stylesheet, the
screen registry, the app-level bindings, the service injection seam, the
help modal, and the min-size guard — nothing else. Zero check/mark/
filter logic ever lands here (binding constraint 5: TUI orchestrates,
never computes); every later Phase 8-12 plan adds screens and services
onto this root.

08-06 wiring:

- Service injection: the constructor accepts an optional
  ``env_check_service`` override (the ``EnvCheckServiceProtocol`` seam —
  tier-2 Pilot tests inject deterministic fakes so no real kernel, GPU
  or otherwise, ever executes in CI, D-03); None means the real service.
- App-level bindings (08-UI-SPEC Keyboard map): ``q`` quits from any
  screen; ``?`` opens the help modal listing every active binding with
  its Chinese label from ``tui/strings.py`` (I18N-01).
- Min-size guard (08-UI-SPEC Terminal Contract): below 80x24 the app
  renders ONLY the min-size message with the current dimensions — a
  dedicated screen swapped in on mount/resize and popped when the
  terminal grows back; nothing else is visible while it is on top.

08-07 wiring:

- The selection seam: ``selection_service`` (the same Protocol-injection
  pattern) plus the shared app-state mark sets — every selection/matrix
  screen is built through ``build_selection_screen`` so the sets are the
  same live instances (SEL-01 persistence).
"""

from collections.abc import Callable
from typing import Any, ClassVar

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Footer, Static

from tui.screens.env_check import EnvCheckScreen, EnvCheckServiceProtocol
from tui.screens.selection import (
    SelectionScreen,
    SelectionServiceProtocol,
)
from tui.strings import (
    APP_HELP_LABEL,
    APP_HELP_ROW,
    APP_HELP_TITLE,
    APP_MIN_SIZE_MESSAGE,
    APP_MODAL_BACK_LABEL,
    APP_QUIT_LABEL,
    APP_TITLE,
)

# 08-UI-SPEC Terminal Contract: the minimum grid. Below this, only the
# min-size message renders (re-checked on every resize).
MIN_WIDTH = 80
MIN_HEIGHT = 24


class HelpModal(ModalScreen):
    """The ``?`` help modal: every active binding, Chinese labels.

    ModalScreen so app/screen bindings do not fire while it is open
    (Pitfall 11); the rows arrive pre-built from the app (the binding
    descriptions ARE the strings-module copy — no copy lives here).
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, rows: "list[tuple[str, str]]", **kwargs):
        super().__init__(**kwargs)
        self._rows = list(rows)

    def compose(self) -> ComposeResult:
        with Vertical(id="help-box"):
            for key, label in self._rows:
                yield Static(APP_HELP_ROW.format(key=key, label=label))
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#help-box", Vertical).border_title = APP_HELP_TITLE


class MinSizeScreen(Screen):
    """The below-minimum terminal state: ONLY the min-size message.

    A plain Screen (not a ModalScreen) so the screen beneath is not
    rendered at all — the message with the current dimensions is the
    entire visible surface (08-UI-SPEC Terminal Contract).
    """

    def __init__(self, width: int, height: int, **kwargs):
        super().__init__(**kwargs)
        self._width = width
        self._height = height

    def compose(self) -> ComposeResult:
        yield Static(self._message(), id="min-size-message")

    def _message(self) -> str:
        return APP_MIN_SIZE_MESSAGE.format(w=self._width, h=self._height)

    def update_dimensions(self, width: int, height: int) -> None:
        """Keep the displayed dimensions current on further below-min resizes."""
        self._width = width
        self._height = height
        self.query_one("#min-size-message", Static).update(self._message())


class DnallmMarkTui(App):
    """DNALLM-Mark operator console — composition root."""

    # I18N-01: operator-facing copy lives ONLY in tui/strings.py; screens
    # reference constants, never inline copy.
    TITLE = APP_TITLE

    # tui/styles.tcss — semantic Textual theme tokens only (08-UI-SPEC
    # Color contract; no hardcoded hex — the optional brand theme is
    # deliberately not landed, default theme tokens satisfy the contract).
    CSS_PATH = "styles.tcss"

    # App-level bindings: q quits from any screen (unhandled keys bubble
    # widget -> screen -> app, so a focused DataTable does not swallow q);
    # ? opens the help modal. The ClassVar annotations mirror the App base
    # declarations verbatim (the 08-03 RUF012 resolution) — framework-read
    # class constants.
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", APP_QUIT_LABEL),
        Binding("question_mark", "help", APP_HELP_LABEL, key_display="?"),
    ]

    # Screen registry (key-switched full screens, 08-UI-SPEC Auto-Selected
    # Default #4): the env-check screen is the opening screen. The
    # selection/matrix screens (08-07) deliberately do NOT join this
    # zero-arg registry: they share the live app-state mark sets, so they
    # are built through build_selection_screen / the pushing screen —
    # a slot-built screen would carry fresh sets and silently lose marks.
    # Classes instantiate lazily on first name access; name-based access
    # builds the default (real) service — the injected-service path is
    # get_default_screen below.
    SCREENS: ClassVar[dict[str, Callable[[], Screen[Any]]]] = {
        "env_check": EnvCheckScreen,
    }

    def __init__(self, env_check_service: EnvCheckServiceProtocol | None = None,
                 selection_service: SelectionServiceProtocol | None = None):
        """Compose the console with injectable services.

        Args:
            env_check_service: optional service override for the env-check
                screen (the tier-2 Pilot seam — tests inject deterministic
                fakes so no real kernel executes in CI, D-03). None means
                the real service (EnvCheckBackend over the 08-04 module).
            selection_service: optional service override for the selection
                screen (the same seam pattern, 08-07). None means the real
                service (SelectionBackend over the 08-04/08-05 modules).
        """
        super().__init__()
        self._env_check_service = env_check_service
        self._selection_service = selection_service
        # The shared app-state mark sets (SEL-01): marks live HERE, never
        # inside a DataTable — the selection screen and the matrix screen
        # read the same live sets, so filter rebuilds, table switches,
        # and screen pushes can never lose them.
        self._marked_models: set[str] = set()
        self._marked_tasks: set[str] = set()
        # The active min-size guard screen (None = terminal at/above the
        # minimum grid).
        self._min_size_screen: MinSizeScreen | None = None

    def get_default_screen(self) -> EnvCheckScreen:
        """Open the console on the env-check screen (with the wired service)."""
        return EnvCheckScreen(env_check_service=self._env_check_service)

    def build_selection_screen(self) -> SelectionScreen:
        """Build the selection screen over the shared mark sets.

        The screen factory (08-07): the injected-or-real service plus the
        SAME live mark-set instances every selection/matrix screen
        shares — constructed here, never through a zero-arg SCREENS slot
        (a slot-built screen would carry fresh sets and silently lose
        the SEL-01 persistence guarantee).
        """
        return SelectionScreen(
            selection_service=self._selection_service,
            marked_models=self._marked_models,
            marked_tasks=self._marked_tasks,
        )

    # ===== Min-size guard (08-UI-SPEC Terminal Contract) =====

    def on_mount(self) -> None:
        """Check the grid once at mount (resize events re-check live)."""
        if self.size.width and self.size.height:
            self._apply_min_size_guard(self.size.width, self.size.height)

    def on_resize(self, event: events.Resize) -> None:
        """Re-evaluate the guard on every resize (shrink AND grow)."""
        self._apply_min_size_guard(event.size.width, event.size.height)

    def _apply_min_size_guard(self, width: int, height: int) -> None:
        """Below 80x24, swap in the min-size screen; at/above, restore.

        The guard screen is pushed as a plain Screen, so while it is on
        top NOTHING else renders (the message is the whole surface); a
        modal beneath it (e.g. an open drill-down) survives the round
        trip — the pop restores the exact stack.
        """
        below = width < MIN_WIDTH or height < MIN_HEIGHT
        guard = self._min_size_screen
        if below:
            if guard is None:
                guard = MinSizeScreen(width, height)
                self._min_size_screen = guard
                self.push_screen(guard)
            else:
                # still below the minimum, different dimensions — keep
                # the displayed width/height current
                guard.update_dimensions(width, height)
        elif guard is not None:
            self._min_size_screen = None
            self.pop_screen()

    # ===== Actions (app-level) =====

    def action_help(self) -> None:
        """The ``?`` key: the help modal over the current screen."""
        self.push_screen(HelpModal(self._binding_rows()))

    def _binding_rows(self) -> "list[tuple[str, str]]":
        """Every active binding as (display key, Chinese label) rows.

        App bindings first, then the active screen's — the help surface
        always reflects the live key map (k9s-style contextual help).
        The descriptions are the strings-module constants wired into the
        BINDINGS declarations — no copy is redefined here (I18N-01).
        """
        rows = [row for row in map(_binding_row, self.BINDINGS)
                if row is not None]
        rows.extend(row for row
                    in map(_binding_row, getattr(self.screen, "BINDINGS", []))
                    if row is not None)
        return rows


def _binding_row(binding: BindingType) -> "tuple[str, str] | None":
    """One binding declaration -> its (display key, label) help row.

    Handles both BINDINGS forms: ``Binding`` objects (key_display shown
    when set) and the tuple shorthands ``(key, action[, description])``
    (the 2-tuple carries no footer label — no help row for it).
    """
    if isinstance(binding, Binding):
        return (binding.key_display or binding.key, binding.description)
    if len(binding) >= 3 and binding[2]:
        return (binding[0], binding[2])
    return None
