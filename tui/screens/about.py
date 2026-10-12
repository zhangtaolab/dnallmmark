"""
about — the 关于 screen (Phase 9, 09-03, D-13 slot 6).

The read-only info screen behind top-menu slot 6: five fixed rows
(软件版本 / 数据版本 / 里程碑阶段 / 依赖版本 / 仓库地址) whose values
derive through the injected ``AboutServiceProtocol`` seam — every value
wraps, never elides; absent dependencies render the 未安装 constant dim;
the screen composes fully on any machine (the partial-tolerance edge —
T-09-08 absorbs every probe failure into a neutral value upstream).

Contract (locked decisions):

- Read-only (D-13 只读信息屏): the ONLY bindings are the nav digits
  (plain per-screen declarations — a focused Input elsewhere consumes
  digit keystrokes first, Pattern 2) plus the app-level ``?`` / ``q``.
  No action keys, no refresh.
- Stateless: this screen MAY join the zero-arg ``SCREENS`` registry
  (unlike selection, which keeps its live-mark-set factory discipline).
- Protocol injection (the env-check screen pattern): the constructor
  accepts an ``about_service`` override; the real ``AboutBackend`` below
  is thin delegation glue over the tested ``tui/services/about`` module
  and tier-2 Pilot fakes conform structurally.
- D-03 (the read seam): the derivation runs in an exclusive
  ``@work(exclusive=True, thread=True)`` worker — the git subprocess and
  the file reads never run on the event loop; the result crosses the
  thread boundary only via ``post_message``.
- I18N-01: zero Chinese literals in this module — every operator-facing
  string renders through ``tui/strings.py`` constants (grep-enforced);
  package names, versions, and the URL stay English verbatim.
"""

from typing import ClassVar, Protocol

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Label, Static

from tui.services.about import AboutData
from tui.strings import (
    ABOUT_DEP_ABSENT,
    ABOUT_MILESTONE_STAGE,
    ABOUT_N_AUDIT_ABSENT,
    ABOUT_N_AUDIT_PRESENT,
    ABOUT_ROW_DATA,
    ABOUT_ROW_DEPS,
    ABOUT_ROW_MILESTONE,
    ABOUT_ROW_REPO,
    ABOUT_ROW_SOFTWARE,
    ABOUT_TITLE,
    ABOUT_VALUE_DATA,
    ABOUT_VALUE_SOFTWARE_WITH_SHA,
    NAV_LABEL_ABOUT,
    NAV_LABEL_DATA,
    NAV_LABEL_ENV,
    NAV_LABEL_MONITOR,
    NAV_LABEL_RUN_CONFIG,
    NAV_LABEL_SELECTION,
)

# Dim style for absent-dependency values (theme token — the 未安装 state
# renders secondary; the word itself is the NO_COLOR meaning-carrier).
_STYLE_DIM = "$text-muted"


class AboutServiceProtocol(Protocol):
    """The about-derivation surface the screen consumes (the seam)."""

    def derive_about_data(self) -> AboutData:
        """One complete about snapshot; never raises (T-09-08)."""


class AboutBackend:
    """The real about service adapter — thin delegation over 09-03."""

    def derive_about_data(self) -> AboutData:
        """Delegate to the tested service module."""
        raise NotImplementedError  # GREEN lands the delegation


class AboutScreen(Screen):
    """The read-only 关于 screen: five fixed rows over tolerant probes."""

    # D-13 slot 6 (the top-menu active-slot marker the nav bar reads).
    NAV_SLOT: ClassVar[int] = 6

    # The nav digits — PLAIN per-screen bindings, never priority (a
    # priority binding would fire before a focused Input and break
    # typing, Pattern 2); show=False keeps them out of the bottom-bar
    # left segment and the help modal (the top bar itself carries the
    # digit labels — listing them twice would duplicate the menu).
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("1", "app.nav(1)", NAV_LABEL_ENV, show=False),
        Binding("2", "app.nav(2)", NAV_LABEL_SELECTION, show=False),
        Binding("3", "app.nav(3)", NAV_LABEL_DATA, show=False),
        Binding("4", "app.nav(4)", NAV_LABEL_RUN_CONFIG, show=False),
        Binding("5", "app.nav(5)", NAV_LABEL_MONITOR, show=False),
        Binding("6", "app.nav(6)", NAV_LABEL_ABOUT, show=False),
    ]

    class AboutLoaded(Message):
        """The derivation worker finished; carries the snapshot (D-03)."""

        def __init__(self, data: AboutData) -> None:
            self.data = data
            super().__init__()

    def __init__(self, about_service: AboutServiceProtocol | None = None,
                 **kwargs):
        super().__init__(**kwargs)
        self._service: AboutServiceProtocol = (
            about_service if about_service is not None
            else AboutBackend()
        )

    def compose(self) -> ComposeResult:
        """The five fixed rows: 8-cell CJK label + wrapping value column."""
        with Vertical(id="about-box"):
            yield Label(ABOUT_TITLE, id="about-title")
            for row_id, row_label in self._rows():
                with Horizontal(classes="about-row"):
                    yield Label(row_label, classes="about-label")
                    yield Static("", id=f"about-value-{row_id}",
                                 classes="about-value")

    @staticmethod
    def _rows() -> "tuple[tuple[str, str], ...]":
        """The five (row id, label) pairs in D-13 row order."""
        return (
            ("software", ABOUT_ROW_SOFTWARE),
            ("data", ABOUT_ROW_DATA),
            ("milestone", ABOUT_ROW_MILESTONE),
            ("deps", ABOUT_ROW_DEPS),
            ("repo", ABOUT_ROW_REPO),
        )

    def on_mount(self) -> None:
        """Start the one exclusive derivation worker (D-03)."""
        self._load_data()

    @work(exclusive=True, thread=True)
    def _load_data(self) -> None:
        """Derive the snapshot off the event loop; post it back."""
        data = self._service.derive_about_data()
        self.post_message(self.AboutLoaded(data))

    def on_about_screen_about_loaded(self, message: AboutLoaded) -> None:
        """Render the five values from the loaded snapshot."""
        raise NotImplementedError  # GREEN lands the row rendering
