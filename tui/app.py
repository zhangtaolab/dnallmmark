"""
app.py — ``DnallmMarkTui``, the console's composition root (Phase 8, 08-02;
screen wiring 08-03; service injection seam 08-06).

Composition root ONLY: the app wires the title, the stylesheet, the
screen registry, the app-level bindings, and the service injection seam —
nothing else. Every later Phase 8-12 plan adds screens and services onto
this root; no business logic ever lands here (binding constraint 5: TUI
orchestrates, never computes).

08-06 wiring — the injection seam every tier-2 Pilot test uses:

- the constructor accepts an optional ``env_check_service`` override
  defaulting to the REAL service (the ``EnvCheckBackend`` adapter over the
  08-04 module — None lets the screen build the same default itself);
- the env-check screen is created with the injected service so Pilot tests
  run the full app against deterministic fakes and no real kernel — GPU or
  otherwise — ever executes in CI (D-03).

08-03 tracer wiring — the boot path ``make tui`` runs and the Pilot boot
test exercises headlessly:

- the env-check screen is registered by name and set as the
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

from tui.screens.env_check import (
    EnvCheckScreen,
    EnvCheckServiceProtocol,
)
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
    # Default #4): the env-check screen is the opening screen; the
    # selection/matrix screens join here in 08-07 (the registry IS the
    # declared slot mechanism — do not create those screens early).
    # Classes instantiate lazily on first name access; name-based access
    # builds the default (real) service — the injected-service path is
    # get_default_screen below.
    SCREENS: ClassVar[dict[str, Callable[[], Screen[Any]]]] = {
        "env_check": EnvCheckScreen,
    }

    def __init__(self, env_check_service: EnvCheckServiceProtocol | None = None):
        """Compose the console with an injectable env-check service.

        Args:
            env_check_service: optional service override for the env-check
                screen (the tier-2 Pilot seam — tests inject deterministic
                fakes so no real kernel executes in CI, D-03). None means
                the real service (EnvCheckBackend over the 08-04 module).
        """
        super().__init__()
        self._env_check_service = env_check_service

    def get_default_screen(self) -> EnvCheckScreen:
        """Open the console on the env-check screen (with the wired service)."""
        return EnvCheckScreen(env_check_service=self._env_check_service)
