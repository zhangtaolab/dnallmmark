"""
app.py — ``DnallmMarkTui``, the console's composition root (Phase 8, 08-02).

Minimal by design: the app wires the title and the stylesheet, and nothing
else. Screen registration, key bindings, and service wiring land with the
08-03 tracer (the boot path through screen, service, and the pipeline seam);
every later Phase 8-12 plan adds screens and services onto this root — no
business logic ever lands here (binding constraint 5: TUI orchestrates,
never computes).
"""

from textual.app import App

from tui.strings import APP_TITLE


class DnallmMarkTui(App):
    """DNALLM-Mark operator console — composition root (Phase 8 skeleton)."""

    # I18N-01: operator-facing copy lives ONLY in tui/strings.py; screens
    # reference constants, never inline copy.
    TITLE = APP_TITLE

    # tui/styles.tcss — semantic Textual theme tokens only (08-UI-SPEC
    # Color contract; no hardcoded hex outside the optional theme site).
    CSS_PATH = "styles.tcss"
