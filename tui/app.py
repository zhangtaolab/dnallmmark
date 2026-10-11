"""
app.py — ``DnallmMarkTui``, the console's composition root (Phase 8, 08-02;
screen wiring 08-03).

Composition root ONLY: the app wires the title, the stylesheet, the
screen registry, and the app-level bindings — nothing else. Every later
Phase 8-12 plan adds screens and services onto this root; no business
logic ever lands here (binding constraint 5: TUI orchestrates, never
computes).

08-03 tracer wiring — the boot path ``make tui`` runs and the Pilot boot
test exercises headlessly:

- the env-check shell screen is registered by name and set as the
  opening screen (08-UI-SPEC: the app opens on env check);
- the app-level ``q`` binding quits from anywhere (08-UI-SPEC Keyboard
  contract — the operator-facing label is copy, so it lives in
  ``tui/strings.py``, I18N-01).
"""

from collections.abc import Callable
from typing import Any, ClassVar

from textual.app import App
from textual.binding import Binding, BindingType
from textual.screen import Screen

from tui.screens.env_check import EnvCheckScreen
from tui.strings import APP_QUIT_LABEL, APP_TITLE


class DnallmMarkTui(App):
    """DNALLM-Mark operator console — composition root."""

    # I18N-01: operator-facing copy lives ONLY in tui/strings.py; screens
    # reference constants, never inline copy.
    TITLE = APP_TITLE

    # tui/styles.tcss — semantic Textual theme tokens only (08-UI-SPEC
    # Color contract; no hardcoded hex outside the optional theme site).
    CSS_PATH = "styles.tcss"

    # App-level binding: q quits from any screen. Unhandled keys bubble
    # widget → screen → app, so a focused DataTable does not swallow q.
    # The ClassVar annotations mirror the App base declarations verbatim
    # (textual/app.py: BINDINGS: ClassVar[list[BindingType]],
    # SCREENS: ClassVar[dict[str, Callable[[], Screen[Any]]]]) — these
    # are framework-read class constants (ruff RUF012).
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", APP_QUIT_LABEL),
    ]

    # Screen registry (key-switched full screens, 08-UI-SPEC Auto-Selected
    # Default #4): 08-03 lands the first screen; the selection/matrix
    # screens join here in later Phase 8 plans. Classes instantiate
    # lazily on first name access.
    SCREENS: ClassVar[dict[str, Callable[[], Screen[Any]]]] = {
        "env_check": EnvCheckScreen,
    }

    def get_default_screen(self) -> EnvCheckScreen:
        """Open the console on the env-check screen.

        The opening screen is the 08-03 shell (seven pending rows); the
        08-06 screen build fills it with kernel results.
        """
        return EnvCheckScreen()
