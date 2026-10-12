"""
about — the About screen (Phase 9, 09-03, D-13 slot 6).

The read-only info screen behind top-menu slot 6: five fixed rows
(software / data / milestone / dependencies / repository, rendered from
the ABOUT_ROW_* strings constants) whose values derive through the
injected ``AboutServiceProtocol`` seam — every value wraps, never
elides; absent dependencies render the absent-dependency constant dim;
the screen composes fully on any machine (the partial-tolerance edge —
T-09-08 absorbs every probe failure into a neutral value upstream).

Contract (locked decisions):

- Read-only (the D-13 read-only info screen): the ONLY bindings are the nav digits
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

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Label, Static

from tui.screens.nav import BottomBar, TopMenuBar
from tui.services import about as about_service
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

# Dim style for absent-dependency values (rich `dim` — a Textual
# `$token` cannot style a rich Text span on the Static render path,
# probe-pinned 8.2.8; the word itself is the NO_COLOR meaning-carrier).
_STYLE_DIM = "dim"


class AboutServiceProtocol(Protocol):
    """The about-derivation surface the screen consumes (the seam)."""

    def derive_about_data(self) -> AboutData:
        """One complete about snapshot; never raises (T-09-08)."""


class AboutBackend:
    """The real about service adapter — thin delegation over 09-03.

    Every semantic stays in ``tui/services/about`` (the tested service);
    this adapter only presents the module function as the object seam the
    screen's constructor injection consumes (the 08-06 EnvCheckBackend
    pattern).
    """

    def derive_about_data(self) -> AboutData:
        """Delegate to the tested service module."""
        return about_service.derive_about_data()


class AboutScreen(Screen):
    """The read-only About screen: five fixed rows over tolerant probes."""

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
        yield TopMenuBar()
        with Vertical(id="about-box"):
            yield Label(ABOUT_TITLE, id="about-title")
            for row_id, row_label in self._rows():
                with Horizontal(classes="about-row"):
                    yield Label(row_label, classes="about-label")
                    yield Static("", id=f"about-value-{row_id}",
                                 classes="about-value")
        yield BottomBar()

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
        """Render the five values from the loaded snapshot.

        Values wrap, never elide (the wrapping value column); absent
        dependencies render the absent-dependency constant dim inside the
        deps row; a missing sha renders the bare version.
        """
        data = message.data
        self._set_value("software", self._software_value(data))
        self._set_value("data", self._data_value(data))
        self._set_value("milestone", ABOUT_MILESTONE_STAGE)
        self._set_value("deps", self._deps_value(data))
        self._set_value("repo", data.repo_url)

    # ----- value composition (label-safe data -> renderable content) -----

    def _set_value(self, row_id: str, content) -> None:
        """Write one row's value column (str or rich Text)."""
        self.query_one(f"#about-value-{row_id}", Static).update(content)

    @staticmethod
    def _software_value(data: AboutData) -> str:
        """Software row: the version, with the git sha appended when resolved."""
        if data.git_sha:
            return ABOUT_VALUE_SOFTWARE_WITH_SHA.format(
                version=data.software_version, sha=data.git_sha)
        return data.software_version

    @staticmethod
    def _data_value(data: AboutData) -> str:
        """Data row: official-only counts + custom counts + the n_audit signal."""
        audit = (
            ABOUT_N_AUDIT_PRESENT if data.n_audit_present
            else ABOUT_N_AUDIT_ABSENT
        )
        return ABOUT_VALUE_DATA.format(
            om=data.official_counts.models,
            od=data.official_counts.datasets,
            cm=data.custom_counts[0],
            cd=data.custom_counts[1],
            audit=audit,
        )

    @staticmethod
    def _deps_value(data: AboutData) -> Text:
        """Deps row: per-package version lines; absent renders the
        absent-dependency constant dim.

        The joiner is the halfwidth middle dot with spaces (the mockup
        format); package names and versions stay English verbatim.
        """
        segments: list[Text] = []
        for position, (package, version) in enumerate(data.deps.items()):
            if position:
                segments.append(Text(" · "))
            segments.append(Text(f"{package} "))
            if version is None:
                segments.append(Text(ABOUT_DEP_ABSENT, style=_STYLE_DIM))
            else:
                segments.append(Text(version))
        return Text.assemble(*segments)
