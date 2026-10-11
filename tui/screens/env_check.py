"""
env_check — the env-check screen (Phase 8, 08-06; ENV-01..04 presentation).

RED SKELETON (TDD 08-06 Task 1): the layout shell — seven fixed rows in
main() kernel order over the three-column table, the title bar with the
last-check slot, the verdict block container — with every 08-06 behavior
absent on purpose: no cache consultation, no thread worker, no per-row
fill, no verdict rendering, no drill-down, no refresh. The failing tier-2
Pilot suite (tests/tui/test_pilot_env_check.py) pins the missing behavior;
the GREEN commit fills this shell in place.

Contract (lands with the GREEN implementation):

- Presentation only (the tui/screens/ tier contract): business semantics
  live in tui/services/ (env_check orchestration/persistence, env_gate
  judgment); this screen renders and posts user intent.
- D-03: the full check runs in ONE exclusive ``@work(thread=True)`` worker;
  kernel results cross to the UI exclusively via ``post_message`` of a
  custom Message — no kernel call ever executes inside a message handler.
- D-05: on_mount consults the injected service's same-day cache; a hit
  renders instantly and starts zero kernels; the refresh key is the only
  path that re-runs kernels.
- I18N-01: zero Chinese literals in this module — every operator-facing
  string renders through tui/strings.py constants (grep-enforced).
"""

from collections.abc import Callable
from typing import ClassVar, Protocol

from env_smoke import CheckResult  # top-level module (pipeline/ sys.path root, D-02)
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import DataTable, Footer, Header, Label, Static

from tui.strings import (
    ENV_COL_ITEM,
    ENV_COL_STATE,
    ENV_COL_SUMMARY,
    ENV_DETAIL_LABEL,
    ENV_KERNEL_LABELS,
    ENV_REFRESH_LABEL,
    ENV_SCREEN_TITLE,
    ENV_STATE_PENDING,
)

# State-cell styles: semantic theme tokens only (08-UI-SPEC Color) — the
# glyph is the meaning-carrier under NO_COLOR; color is the redundant
# second channel (glyph+color redundancy rule).
_STYLE_DIM = "$text-muted"


class EnvCheckServiceProtocol(Protocol):
    """The env-check service surface the screen consumes.

    The constructor-injection seam (08-06): the screen depends on this
    protocol, not on any concrete service — the real ``EnvCheckBackend``
    (08-04 delegation glue) and the tier-2 Pilot fakes both conform
    structurally, so no real kernel ever executes in CI (D-03).
    """

    def cached_results(self) -> "tuple[str, tuple[CheckResult, ...]] | None":
        """Same-day cache check: (checked_at, results) on a hit, None on a miss."""

    def kernels(self) -> "dict[str, Callable[[], CheckResult]]":
        """The kernel sequence: kernel id -> zero-arg callable, main() order."""

    def persist(self, results: "list[CheckResult]") -> str:
        """Persist the whole result list; return the persisted checked_at display string."""


class EnvCheckBackend:
    """RED SKELETON — the real env-check service adapter (08-04 glue).

    GREEN fills: cached_results/kernels/persist delegation over
    ``tui.services.env_check``.
    """

    def __init__(self, state_path=None):
        self._state_path = state_path

    def cached_results(self) -> "tuple[str, tuple[CheckResult, ...]] | None":
        """RED skeleton: behavior absent (None — always a cache miss)."""
        return None

    def kernels(self) -> "dict[str, Callable[[], CheckResult]]":
        """RED skeleton: behavior absent (empty sequence — zero kernels)."""
        return {}

    def persist(self, results: "list[CheckResult]") -> str:
        """RED skeleton: behavior absent (empty display string)."""
        return ""


class EnvDetailModal(ModalScreen):
    """RED SKELETON — the drill-down modal (verbatim kernel detail lines)."""

    def __init__(self, kernel_id: str, label: str, lines, **kwargs):
        super().__init__(**kwargs)
        self.kernel_id = kernel_id
        self._label = label
        self.detail_lines = tuple(lines)

    def compose(self) -> ComposeResult:
        yield Static(self.kernel_id)


class EnvCheckScreen(Screen):
    """Env-check screen: seven fixed rows in main() kernel order (08-06)."""

    # The ClassVar annotation mirrors the App base declaration verbatim
    # (the 08-03 RUF012 resolution) — framework-read class constant.
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("r", "refresh", ENV_REFRESH_LABEL),
        Binding("enter", "show_detail", ENV_DETAIL_LABEL),
    ]

    def __init__(self, env_check_service: EnvCheckServiceProtocol | None = None,
                 **kwargs):
        super().__init__(**kwargs)
        self._service: EnvCheckServiceProtocol = (
            env_check_service if env_check_service is not None
            else EnvCheckBackend()
        )
        self._results: dict[str, CheckResult] = {}

    def compose(self) -> ComposeResult:
        """The screen frame: header, title bar, kernel table, verdict slot."""
        yield Header()
        with Horizontal(id="env-title-bar"):
            yield Label(ENV_SCREEN_TITLE, id="env-screen-title")
            yield Label("", id="env-last-check")
        yield DataTable(id="env-kernels")
        yield Vertical(id="env-verdict")
        yield Footer()

    def on_mount(self) -> None:
        """Compose the seven fixed pending rows in main() kernel order.

        ``ENV_KERNEL_LABELS`` is defined in main() kernel order (the
        08-02 strings contract), so iteration order IS the row-order
        contract; the dict keys double as the stable DataTable row keys.
        """
        table = self.query_one("#env-kernels", DataTable)
        table.cursor_type = "row"   # 08-UI-SPEC DataTable usage contract
        table.zebra_stripes = True  # same
        table.add_columns(
            (ENV_COL_STATE, "state"),
            (ENV_COL_ITEM, "item"),
            (ENV_COL_SUMMARY, "summary"),
        )
        for kernel_id, label in ENV_KERNEL_LABELS.items():
            table.add_row(
                Text(ENV_STATE_PENDING, style=_STYLE_DIM),
                label,
                "",
                key=kernel_id,
            )
        table.focus()

    def action_refresh(self) -> None:
        """RED skeleton: refresh behavior lands with the worker (GREEN)."""

    def action_show_detail(self) -> None:
        """RED skeleton: drill-down behavior lands with the modal (GREEN)."""
