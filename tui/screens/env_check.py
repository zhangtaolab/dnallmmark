"""
env_check — the env-check screen (Phase 8, 08-06; ENV-01..04 presentation).

The visible half of the startup environment check: a seven-row DataTable
keyed on the stable kernel ids in ``main()`` kernel order, filled
row-by-row as kernel results arrive, plus the last-check line (ENV-02),
the advisory gate verdict + missing-data routing block (ENV-03, D-09),
and the verbatim drill-down modal.

Contract (locked decisions):

- Presentation only (the ``tui/screens/`` tier contract): every business
  semantic lives in ``tui/services/`` — ``env_check`` owns
  orchestration/persistence/cache, ``env_gate`` owns the verdict
  judgment; this screen renders service results and posts user intent.
- D-03 (the ONLY execution site): the full check runs in ONE exclusive
  ``@work(exclusive=True, thread=True)`` worker. Kernel results cross
  the worker-thread -> event-loop boundary exclusively via
  ``post_message`` of a nested custom ``Message``; no kernel call ever
  executes inside a message handler or any event-loop context (the
  T-08-07 mitigation — the Pilot suite proves the UI stays responsive
  with a deliberately blocked kernel).
- D-05 (cache semantics): ``on_mount`` consults the injected service's
  same-day cache first; a hit renders every row in its final state
  instantly and spawns ZERO kernels; the refresh key is the ONLY path
  that re-runs kernels (partial-failure cache hits render FAIL rows —
  by-design honesty, not an error state).
- D-02 (verbatim drill-down): the modal shows the kernel's own detail
  lines byte-for-byte (the byte-stable env_smoke contract text) in a
  wrapping, scrolling RichLog — never elided; Chinese chrome only wraps
  them (title, footer).
- D-09 (advisory verdict): the verdict block renders the
  ``tui.services.env_gate`` judgment; the launch BLOCK is Phase 11
  wiring — the persisted state file is never treated as gate authority.
- I18N-01: zero Chinese literals in this module — every operator-facing
  string renders through ``tui/strings.py`` constants (grep-enforced);
  kernel ids, column keys, and file paths stay English verbatim.
- ModalScreen for the drill-down: app-level bindings (q/?) do not fire
  while the modal is on top (08-RESEARCH Pitfall 11).
"""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import ClassVar, Protocol

from env_smoke import CheckResult  # top-level module (pipeline/ sys.path root, D-02)
from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen, Screen
from textual.widgets import DataTable, Footer, Header, Label, RichLog, Static
from textual.worker import get_current_worker

from tui.services import env_check, env_gate
from tui.strings import (
    APP_MODAL_BACK_LABEL,
    ENV_COL_ITEM,
    ENV_COL_STATE,
    ENV_COL_SUMMARY,
    ENV_DETAIL_LABEL,
    ENV_DETAIL_TITLE,
    ENV_KERNEL_LABELS,
    ENV_LAST_CHECK_LINE,
    ENV_REFRESH_LABEL,
    ENV_ROUTE_MISSING_DATASETS,
    ENV_SCREEN_TITLE,
    ENV_STATE_CHECKING,
    ENV_STATE_FAIL,
    ENV_STATE_PASS,
    ENV_STATE_PENDING,
    ENV_VERDICT_CRITICAL_FAIL,
    ENV_VERDICT_PASS,
    SEL_OPEN_LABEL,
)

# State-cell styles: semantic theme tokens only (08-UI-SPEC Color —
# hardcoded hex is forbidden outside the optional theme site). DataTable
# cells are not DOM nodes, so per-cell color rides on rich Text styles
# referencing the SAME theme variables; the glyph is the meaning-carrier
# under NO_COLOR, color is the redundant second channel (glyph+color
# redundancy rule).
_STYLE_DIM = "$text-muted"      # Secondary role: pending/checking rows
_STYLE_PASS = "bold $success"   # Emphasis + Success roles
_STYLE_FAIL = "bold $error"     # Emphasis + Destructive roles

# DataTable column keys (English technical ids, I18N-01): the labels come
# from strings constants; the keys are the update_cell addressing scheme.
_COL_STATE = "state"
_COL_SUMMARY = "summary"


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
    """The real env-check service adapter — thin delegation glue over 08-04.

    Every semantic stays in ``tui/services/env_check`` (the tested
    service): this adapter only reshapes the module-function API into the
    object seam the screen's constructor injection consumes — the cache
    answer as a ``(checked_at, results)`` pair with items rebuilt into
    ``CheckResult`` values, the kernel sequence as-is, and persistence
    returning the display string for the last-check line (one moment
    derives both the persisted file and the rendered line).
    """

    def __init__(self, state_path: Path | str | None = None):
        """Adapt the 08-04 service over a state-file location.

        Args:
            state_path: the env-check state file; None means the D-04
                default (``settings.state_dir() / env_check.json``).
        """
        self._state_path = (
            Path(state_path) if state_path is not None
            else env_check.default_state_path()
        )

    def cached_results(self) -> "tuple[str, tuple[CheckResult, ...]] | None":
        """The same-day cache answer: (checked_at, results) or None.

        Delegates to ``env_check.load_cached`` + ``is_same_local_day``
        (the tolerant None sentinel and the local calendar-day basis are
        the service's contract); rebuilds every persisted item dict back
        into a ``CheckResult`` so the render path treats cached and live
        results identically. Any structural surprise reads as a miss —
        degrade, never crash.
        """
        state = env_check.load_cached(self._state_path)
        if not isinstance(state, dict):
            return None
        if not env_check.is_same_local_day(state):
            return None
        checked_at = state.get("checked_at")
        items = state.get("items")
        if not isinstance(checked_at, str) or not isinstance(items, list):
            return None
        results = []
        for item in items:
            if not isinstance(item, dict):
                return None
            name = item.get("name")
            ok = item.get("ok")
            lines = item.get("lines")
            if not isinstance(name, str) or not isinstance(ok, bool):
                return None
            if not isinstance(lines, list):
                return None
            if not all(isinstance(line, str) for line in lines):
                return None
            results.append(CheckResult(name=name, ok=ok, lines=tuple(lines)))
        return checked_at, tuple(results)

    def kernels(self) -> "dict[str, Callable[[], CheckResult]]":
        """The shared 08-04 kernel sequence (main() order, import-only)."""
        return env_check.default_kernels()

    def persist(self, results: "list[CheckResult]") -> str:
        """Persist through the service; return the persisted display string."""
        # One moment derives BOTH the persisted checked_at and the rendered
        # last-check line — they can never disagree (ENV-02).
        now = datetime.now().astimezone()  # aware local (the 08-04 idiom)
        env_check.persist(self._state_path, results, now=now)
        return now.strftime(env_check.CHECKED_AT_FORMAT)


class EnvDetailModal(ModalScreen):
    """The drill-down modal: one kernel's own detail lines, verbatim.

    ModalScreen (not a plain Screen) so app-level bindings do not fire
    while the detail is open (Pitfall 11). The RichLog wraps and scrolls
    — the byte-stable env_smoke lines are never elided (D-02).
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, kernel_id: str, label: str,
                 lines: "tuple[str, ...] | list[str]", **kwargs):
        super().__init__(**kwargs)
        self.kernel_id = kernel_id
        self._label = label
        self.detail_lines = tuple(lines)

    def compose(self) -> ComposeResult:
        # The footer lives INSIDE the bordered box (the 08-UI-SPEC modal
        # mockup: the esc-back hint at the box bottom).
        with Vertical(id="env-detail-box"):
            yield RichLog(wrap=True, id="env-detail-log")
            yield Footer()

    def on_mount(self) -> None:
        box = self.query_one("#env-detail-box", Vertical)
        box.border_title = ENV_DETAIL_TITLE.format(
            kernel_id=self.kernel_id, label=self._label
        )
        log = self.query_one("#env-detail-log", RichLog)
        for line in self.detail_lines:
            log.write(line)


def _summary_of(result: CheckResult) -> str:
    """The summary cell: the kernel's own first detail line, prefix-stripped.

    The kernel's English wording is data (the byte-stable contract), so
    the summary is derived, never re-worded; the PASS:/FAIL: prefix is
    redundant with the state glyph. Empty for line-less results (the
    torch-unavailable cuda/matmul placeholders).
    """
    if not result.lines:
        return ""
    first = result.lines[0]
    if first.startswith("PASS: "):
        return first[len("PASS: "):]
    if first.startswith("FAIL: "):
        return first[len("FAIL: "):]
    return first


def _missing_dataset_count(result: CheckResult | None) -> int:
    """Count the missing dataset dirs from the dataset_dirs kernel's lines.

    Reads the byte-stable contract shape: every missing dir is one
    ``  - name`` listing line (the double-nested note is appended to the
    same line, never a line of its own) — counting the prefix is counting
    the kernel's own list.
    """
    if result is None:
        return 0
    return sum(1 for line in result.lines if line.startswith("  - "))


class EnvCheckScreen(Screen):
    """The env-check screen: seven rows, async fill, verdict, drill-down."""

    # The ClassVar annotation mirrors the App base declaration verbatim
    # (the 08-03 RUF012 resolution) — framework-read class constant.
    # The s binding (08-07, 08-UI-SPEC Keyboard map) opens the selection
    # screen; the action targets the app's screen factory via the
    # qualified ``app.open_selection`` action name (the shared mark sets
    # live on the composition root).
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("r", "refresh", ENV_REFRESH_LABEL),
        Binding("enter", "show_detail", ENV_DETAIL_LABEL),
        Binding("s", "app.open_selection", SEL_OPEN_LABEL),
    ]

    class CheckItemChecking(Message):
        """One kernel is starting (worker thread -> event loop, D-03)."""

        def __init__(self, kernel_id: str) -> None:
            self.kernel_id = kernel_id
            super().__init__()

    class CheckItemDone(Message):
        """One kernel finished; carries its CheckResult (D-03)."""

        def __init__(self, result: CheckResult) -> None:
            self.result = result
            super().__init__()

    class CheckRunComplete(Message):
        """The whole run finished (persisted); carries the outcome (D-03)."""

        def __init__(self, checked_at: str,
                     results: "tuple[CheckResult, ...]") -> None:
            self.checked_at = checked_at
            self.results = results
            super().__init__()

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
        """Build the seven fixed rows, then cache-hit-or-worker (D-05).

        ``ENV_KERNEL_LABELS`` is defined in main() kernel order (the
        08-02 strings contract), so iteration order IS the row-order
        contract; the dict keys double as the stable DataTable row keys.
        A same-day cache hit renders every row in its FINAL state and
        starts zero kernels; a miss starts the one exclusive worker.
        """
        table = self.query_one("#env-kernels", DataTable)
        table.cursor_type = "row"   # 08-UI-SPEC DataTable usage contract
        table.zebra_stripes = True  # same
        table.add_columns(
            (ENV_COL_STATE, _COL_STATE),
            (ENV_COL_ITEM, "item"),
            (ENV_COL_SUMMARY, _COL_SUMMARY),
        )
        for kernel_id, label in ENV_KERNEL_LABELS.items():
            table.add_row(
                Text(ENV_STATE_PENDING, style=_STYLE_DIM),
                label,
                "",
                key=kernel_id,
            )
        table.focus()

        cached = self._service.cached_results()
        if cached is not None:
            checked_at, results = cached
            for result in results:
                self._results[result.name] = result
                self._apply_result_to_table(result)
            self._render_check_outcome(checked_at, results)
        else:
            self.run_full_check()

    # ===== The exclusive thread worker (D-03: the ONLY kernel execution site) =====

    @work(exclusive=True, thread=True)
    def run_full_check(self) -> None:
        """Run every kernel in the worker thread, posting one message per step.

        A plain ``def`` (an OS thread, never the event loop): each kernel
        call blocks here, not the UI. Per kernel: post the checking state,
        run, post the result; per run: persist through the service (file
        I/O stays off the event loop too), then post the completion. The
        cancellation poll between kernels honors exclusive=True's cancel
        of a still-running previous refresh (threads cannot be interrupted).
        """
        worker = get_current_worker()
        results: list[CheckResult] = []
        for kernel_id, kernel in self._service.kernels().items():
            if worker.is_cancelled:
                return
            self.post_message(self.CheckItemChecking(kernel_id))
            result = kernel()
            results.append(result)
            self.post_message(self.CheckItemDone(result))
        checked_at = self._service.persist(results)
        self.post_message(self.CheckRunComplete(checked_at, tuple(results)))

    # ===== Message handlers (event-loop side: row mutation only, never kernels) =====

    def on_env_check_screen_check_item_checking(
            self, message: CheckItemChecking) -> None:
        """Flip the in-flight row to the checking state (inline fill)."""
        if message.kernel_id not in ENV_KERNEL_LABELS:
            return
        table = self.query_one("#env-kernels", DataTable)
        table.update_cell(
            message.kernel_id, _COL_STATE,
            Text(ENV_STATE_CHECKING, style=_STYLE_DIM),
        )

    def on_env_check_screen_check_item_done(
            self, message: CheckItemDone) -> None:
        """Record the result and flip its row to the final glyph + summary."""
        self._results[message.result.name] = message.result
        self._apply_result_to_table(message.result)

    def on_env_check_screen_check_run_complete(
            self, message: CheckRunComplete) -> None:
        """Render the last-check line + the verdict block (ENV-02/ENV-03)."""
        self._render_check_outcome(message.checked_at, message.results)

    # ===== Rendering (pure UI state mutation over service results) =====

    def _apply_result_to_table(self, result: CheckResult) -> None:
        """One result -> its row's state glyph and summary cells."""
        if result.name not in ENV_KERNEL_LABELS:
            return  # forward tolerance: unknown kernel ids never crash rows
        table = self.query_one("#env-kernels", DataTable)
        glyph = ENV_STATE_PASS if result.ok else ENV_STATE_FAIL
        style = _STYLE_PASS if result.ok else _STYLE_FAIL
        table.update_cell(result.name, _COL_STATE, Text(glyph, style=style))
        table.update_cell(result.name, _COL_SUMMARY, _summary_of(result))

    def _render_check_outcome(self, checked_at: str,
                              results: "tuple[CheckResult, ...]") -> None:
        """The last-check line + the advisory verdict/routing block (D-09)."""
        self.query_one("#env-last-check", Label).update(
            ENV_LAST_CHECK_LINE.format(checked_at=checked_at)
        )
        verdict = env_gate.gate_verdict(results)
        box = self.query_one("#env-verdict", Vertical)
        box.remove_children()
        if verdict.can_launch:
            box.mount(Static(ENV_VERDICT_PASS, classes="verdict-pass"))
        else:
            failing = [
                result.name for result in results
                if not result.ok and result.name in env_gate.CRITICAL
            ]
            box.mount(Static(
                ENV_VERDICT_CRITICAL_FAIL.format(
                    kernel_names=", ".join(failing)),
                classes="verdict-fail",
            ))
        # the single ROUTING kernel id (env_gate.ROUTING) — its copy is
        # dataset-specific per the Copywriting Contract
        dataset_dirs = next(
            (result for result in results if result.name == "dataset_dirs"),
            None,
        )
        if verdict.route_to_data and dataset_dirs is not None:
            box.mount(Static(
                ENV_ROUTE_MISSING_DATASETS.format(
                    n=_missing_dataset_count(dataset_dirs)),
                classes="verdict-route",
            ))

    # ===== Actions (user intent) =====

    def action_refresh(self) -> None:
        """The refresh key: reset every row to pending and re-run (D-05).

        The ONLY path that re-runs kernels after a cache hit; rows reset
        synchronously, the outcome slots clear, and the exclusive worker
        restarts (cancelling any still-running previous run).
        """
        table = self.query_one("#env-kernels", DataTable)
        for kernel_id in ENV_KERNEL_LABELS:
            table.update_cell(
                kernel_id, _COL_STATE,
                Text(ENV_STATE_PENDING, style=_STYLE_DIM),
            )
            table.update_cell(kernel_id, _COL_SUMMARY, "")
        self._results.clear()
        self.query_one("#env-verdict", Vertical).remove_children()
        self.query_one("#env-last-check", Label).update("")
        self.run_full_check()

    def action_show_detail(self) -> None:
        """The enter key (table unfocused): drill into the cursor row."""
        table = self.query_one("#env-kernels", DataTable)
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        self._open_detail(str(row_key.value))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """The enter key on the focused table (its native select event)."""
        self._open_detail(str(event.row_key.value))

    def _open_detail(self, kernel_id: str) -> None:
        """Open the drill-down modal for a checked kernel's verbatim lines."""
        result = self._results.get(kernel_id)
        if result is None:
            return  # pending/unchecked rows have no detail yet — no-op
        label = ENV_KERNEL_LABELS.get(kernel_id, kernel_id)
        self.app.push_screen(
            EnvDetailModal(kernel_id, label, result.lines)
        )
