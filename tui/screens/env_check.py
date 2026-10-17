"""
env_check — the env-check screen (Phase 8, 08-06; ENV-01..04 presentation).

The visible half of the startup environment check: an eight-row DataTable
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
from textual.widgets import DataTable, Footer, Label, RichLog, Static
from textual.worker import get_current_worker

from tui import strings as S
from tui.screens.nav import BottomBar, TopMenuBar
from tui.services import env_check, env_gate
from tui.services import run_config as run_config_service

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

    def storage_rows(self) -> tuple:
        """The five effective storage dirs + existence flags (F4W-04,
        261014-f4w) — read-only display data derived from the same
        seeded load_state seam the directory kernels read roots
        through."""


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
        # Coverage guard (261014-dcl): a same-day state file whose items
        # cover anything short of the FULL kernel-id set is a cache MISS
        # — a pre-change seven-item file re-runs once and persists eight,
        # instead of stranding the new model_dirs row pending forever.
        if {result.name for result in results} != set(S.ENV_KERNEL_LABELS):
            return None
        return checked_at, tuple(results)

    def kernels(self) -> "dict[str, Callable[[], CheckResult]]":
        """The shared 08-04 kernel sequence (main() order, import-only)."""
        return env_check.default_kernels()

    def storage_rows(self) -> tuple:
        """The storage overview over the run-config service (F4W-04):
        thin delegation — the seeding/defaulting semantics live in the
        tested tier (``storage_overview`` over the seed-applied
        ``load_state``)."""
        return run_config_service.storage_overview()

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
        Binding("escape", "dismiss", S.APP_MODAL_BACK_LABEL),
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
        box.border_title = S.ENV_DETAIL_TITLE.format(
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


def _missing_count(result: CheckResult | None) -> int:
    """Count the missing entries from one directory kernel's lines.

    Reads the byte-stable contract shape BOTH directory kernels share
    (261014-dcl): every missing dir is one ``  - name`` listing line
    (the double-nested note is appended to the same line, never a line
    of its own) — counting the prefix is counting the kernel's own list.
    """
    if result is None:
        return 0
    return sum(1 for line in result.lines if line.startswith("  - "))


def _route_line(result: CheckResult, template: str) -> str:
    """The verdict-route line for one FAILED directory kernel (WR-04,
    261016-a4f).

    With listing lines (``  - name`` entries) the count is knowable
    and the count-based ``ENV_ROUTE_MISSING_*`` template renders
    exactly as before (byte-identical healthy behavior). With NONE —
    the registry read-failure / degraded shapes, where a count is
    UNKNOWABLE — the kernel's own first FAIL line renders VERBATIM
    (the same byte-stable data the row summary and drill-down show; no
    glyph prefix, no translation — kernel lines are data): a failed
    kernel must never claim ``0 dirs missing``. The empty-lines
    fallback is defensive only (unreachable for the directory kernels
    today — render, never crash).

    Args:
        result: the failed directory kernel's result.
        template: the count-based route template for that kernel.

    Returns:
        The rendered route line.
    """
    count = _missing_count(result)
    if count > 0:
        return template.format(n=count)
    if result.lines:
        return result.lines[0]
    return template.format(n=0)


def _degraded_result(kernel_id: str, exc: Exception) -> CheckResult:
    """One degraded kernel result for an exception inside the check run.

    WR-01 (08-08): a raising kernel (or a failing ``kernels()``
    enumeration — exactly the broken-checkout state this screen exists
    to diagnose) becomes ONE named ok=False result carrying the
    ``ENV_KERNEL_DEGRADED`` line (exception type + message). The FAIL:
    prefix lets ``_summary_of``'s strip derive the summary cell exactly
    the way every real kernel line already does, and the row renders the
    fail glyph — the console stays alive and the run persists whole
    (D-05).

    IN-01 (261016-a4f): the annotation is ``Exception``, matching both
    ``except Exception`` call sites — KeyboardInterrupt/SystemExit
    deliberately NEVER reach it (they must propagate).
    """
    return CheckResult(
        name=kernel_id,
        ok=False,
        lines=(S.ENV_KERNEL_DEGRADED.format(
            error=f"{type(exc).__name__}: {exc}"),),
    )


class EnvCheckScreen(Screen):
    """The env-check screen: eight rows, async fill, verdict, drill-down."""

    # D-13 slot 1 (the top-menu active-slot marker the nav bar reads).
    NAV_SLOT: ClassVar[int] = 1

    # The ClassVar annotation mirrors the App base declaration verbatim
    # (the 08-03 RUF012 resolution) — framework-read class constant.
    # The 08-07 s binding (open selection) was RETIRED by the 09-03
    # nav-shell migration: menu slot 2 supersedes it — one navigation
    # path per target (the UI-SPEC migration table), and the ? help
    # modal auto-reflects the removal (its rows derive from these
    # declarations).
    # The nav digits (09-03) are PLAIN per-screen bindings routed to the
    # app's ``nav`` action — never priority (Pattern 2: priority fires
    # before a focused Input and breaks typing); show=False keeps them
    # out of the bottom-bar/help surfaces (the top bar carries the
    # digit labels).
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("r", "refresh", S.ENV_REFRESH_LABEL),
        Binding("enter", "show_detail", S.ENV_DETAIL_LABEL),
        Binding("1", "app.nav(1)", S.NAV_LABEL_ENV, show=False),
        Binding("2", "app.nav(2)", S.NAV_LABEL_SELECTION, show=False),
        Binding("3", "app.nav(3)", S.NAV_LABEL_DATA, show=False),
        Binding("4", "app.nav(4)", S.NAV_LABEL_RUN_CONFIG, show=False),
        Binding("5", "app.nav(5)", S.NAV_LABEL_MONITOR, show=False),
        Binding("6", "app.nav(6)", S.NAV_LABEL_ABOUT, show=False),
    ]

    class CheckItemChecking(Message):
        """One kernel is starting (worker thread -> event loop, D-03).

        Carries the run id it belongs to — the handlers drop messages
        from a superseded run (WR-02).
        """

        def __init__(self, kernel_id: str, run_id: int) -> None:
            self.kernel_id = kernel_id
            self.run_id = run_id
            super().__init__()

    class CheckItemDone(Message):
        """One kernel finished; carries its CheckResult (D-03).

        Carries the run id it belongs to — the handlers drop messages
        from a superseded run: a cancelled worker's OS thread can still
        finish its in-flight kernel and post AFTER the new run's
        messages, and a stale landing last would overwrite the fresh
        result (WR-02).
        """

        def __init__(self, result: CheckResult, run_id: int) -> None:
            self.result = result
            self.run_id = run_id
            super().__init__()

    class CheckRunComplete(Message):
        """The whole run finished (persisted); carries the outcome (D-03).

        Carries the run id it belongs to — dropped when superseded
        (WR-02). WR-03 (261016-a4f): ``persist_error`` stays None on
        the healthy path (the default — every pre-existing construction
        site is untouched) and carries ``"{type}: {exc}"`` when the
        persist tail itself failed, so the completion handler renders
        the degraded last-check line instead of the plain one.
        """

        def __init__(self, checked_at: str,
                     results: "tuple[CheckResult, ...]",
                     run_id: int,
                     persist_error: "str | None" = None) -> None:
            self.checked_at = checked_at
            self.results = results
            self.run_id = run_id
            self.persist_error = persist_error
            super().__init__()

    def __init__(self, env_check_service: EnvCheckServiceProtocol | None = None,
                 **kwargs):
        super().__init__(**kwargs)
        self._service: EnvCheckServiceProtocol = (
            env_check_service if env_check_service is not None
            else EnvCheckBackend()
        )
        self._results: dict[str, CheckResult] = {}
        # The current run's id (WR-02): incremented on every refresh so a
        # cancelled run's late messages — its OS thread cannot be
        # interrupted — are recognized as stale and dropped.
        self._run_id = 0
        # WR-03 (quick-261016-hhx, the 08 review): the remount guards.
        # ``_check_in_flight`` marks a run the worker is executing (set
        # at run entry, cleared ONLY by the accepted completion — a
        # stale-dropped completion belongs to a superseding run that set
        # the flag itself); ``_last_outcome`` caches the last rendered
        # (checked_at, results, persist_error) triple so a remount
        # re-renders the outcome instead of re-deriving it. Together
        # they make on_mount population-only on EVERY re-mount: the L
        # toggle mid-run restarts zero kernels and resets nothing.
        self._check_in_flight = False
        self._last_outcome: tuple[str, tuple[CheckResult, ...], str | None] | None = None

    def compose(self) -> ComposeResult:
        """The screen frame: nav bars, title bar, kernel table, verdict.

        The 09-03 migration retired the Textual Header/Footer (the two
        shell bars own those rows now — row-neutral, D-16).
        """
        yield TopMenuBar()
        with Horizontal(id="env-title-bar"):
            yield Label(S.ENV_SCREEN_TITLE, id="env-screen-title")
            yield Label("", id="env-last-check")
        yield DataTable(id="env-kernels")
        yield Vertical(id="env-verdict")
        yield Vertical(id="env-storage")
        yield BottomBar()

    def on_mount(self) -> None:
        """Build the eight fixed rows, then cache-hit-or-worker (D-05).

        ``ENV_KERNEL_LABELS`` is defined in main() kernel order (the
        08-02 strings contract), so iteration order IS the row-order
        contract; the dict keys double as the stable DataTable row keys.
        A same-day cache hit renders every row in its FINAL state and
        starts zero kernels; a miss starts the one exclusive worker.

        WR-03 (quick-261016-hhx): the tail is population-only on
        RE-MOUNT — with results already on the instance they re-apply
        (plus the cached outcome); with a run in flight the freshly
        built pending rows stand and the worker keeps posting onto them;
        only a FIRST mount consults the cache / starts the worker. A
        remount therefore never restarts kernels the operator never
        asked to re-run (the L toggle's re-render path).
        """
        table = self.query_one("#env-kernels", DataTable)
        table.cursor_type = "row"   # 08-UI-SPEC DataTable usage contract
        table.zebra_stripes = True  # same
        table.add_columns(
            (S.ENV_COL_STATE, _COL_STATE),
            (S.ENV_COL_ITEM, "item"),
            (S.ENV_COL_SUMMARY, _COL_SUMMARY),
        )
        for kernel_id, label in S.ENV_KERNEL_LABELS.items():
            table.add_row(
                Text(S.ENV_STATE_PENDING, style=_STYLE_DIM),
                label,
                "",
                key=kernel_id,
            )
        table.focus()

        if self._results:
            # WR-03: a re-mount over landed results — re-apply them
            # (partial results re-apply fine: the in-flight worker's
            # run-id-tagged messages keep landing on the rebuilt rows)
            # and re-render the cached outcome when one exists.
            for result in self._results.values():
                self._apply_result_to_table(result)
            if self._last_outcome is not None:
                checked_at, results, persist_error = self._last_outcome
                self._render_check_outcome(
                    checked_at, results, persist_error=persist_error)
        elif self._check_in_flight:
            # WR-03: a run is executing — leave the freshly built
            # pending rows alone (no cache consult, no run_full_check:
            # the operator asked for a re-render, never for GPU work)
            pass
        else:
            cached = self._service.cached_results()
            if cached is not None:
                checked_at, results = cached
                for result in results:
                    self._results[result.name] = result
                    self._apply_result_to_table(result)
                self._render_check_outcome(checked_at, results)
                self._last_outcome = (checked_at, results, None)
            else:
                self.run_full_check()
        self._render_storage()

    # ===== The exclusive thread worker (D-03: the ONLY kernel execution site) =====

    @work(exclusive=True, thread=True, exit_on_error=False)
    def run_full_check(self) -> None:
        """Run every kernel in the worker thread, posting one message per step.

        A plain ``def`` (an OS thread, never the event loop): each kernel
        call blocks here, not the UI. Per kernel: post the checking state,
        run, post the result; per run: persist through the service (file
        I/O stays off the event loop too), then post the completion. The
        cancellation poll between kernels honors exclusive=True's cancel
        of a still-running previous refresh (threads cannot be
        interrupted). Every message carries the run id captured at start;
        the handlers drop messages whose id no longer matches
        ``self._run_id`` — the cancelled run's OS thread can finish its
        in-flight kernel and post AFTER the new run's messages, and a
        stale landing last would overwrite the fresh result (WR-02).

        WR-01 (08-08) never-exit guards, both inside the existing worker
        shape: (a) a raising kernel becomes the degraded ok=False result
        for its own row and the loop continues to the next kernel; (b) a
        failing ``kernels()`` enumeration degrades EVERY
        ``ENV_KERNEL_LABELS`` row — either way the run routes through
        the same persist + completion tail (D-05 partial-failure
        persists whole), and the decorator's ``exit_on_error=False`` is
        the residual net (textual 8.2.8's default exits the console).
        WR-03 (261016-a4f) closes the THIRD raise site: the persist
        call itself is guarded too — a raising persist (e.g. a
        read-only state dir) posts ONE degraded completion instead of
        stranding the run, so ALL three raise sites route through the
        persist + completion tail.
        """
        worker = get_current_worker()
        run_id = self._run_id  # the run this worker serves (WR-02)
        self._check_in_flight = True  # the WR-03 remount guard
        results: list[CheckResult] = []
        try:
            kernels = self._service.kernels().items()
        except Exception as exc:  # noqa: BLE001 — the WR-01 enumeration guard
            for kernel_id in S.ENV_KERNEL_LABELS:
                degraded = _degraded_result(kernel_id, exc)
                results.append(degraded)
                self.post_message(self.CheckItemDone(degraded, run_id))
        else:
            for kernel_id, kernel in kernels:
                if worker.is_cancelled:
                    return
                self.post_message(self.CheckItemChecking(kernel_id, run_id))
                try:
                    result = kernel()
                except Exception as exc:  # noqa: BLE001 — WR-01 per-kernel
                    result = _degraded_result(kernel_id, exc)
                results.append(result)
                self.post_message(self.CheckItemDone(result, run_id))
        if worker.is_cancelled:
            # a newer run superseded this one mid-flight — never persist
            # stale results over the fresh run's state (the same WR-02
            # race, on the persisted side)
            return
        # WR-03 (261016-a4f): the persist tail is the THIRD raise site
        # — guard it in the same WR-01 idiom, so a read-only state dir
        # still reaches a completion render instead of stranding the
        # run (rows final, no verdict, no last-check line, the error
        # silently swallowed by the worker machinery).
        try:
            checked_at = self._service.persist(results)
        except Exception as exc:  # noqa: BLE001 — the WR-03 tail guard
            # Nothing was written: the display timestamp is computed
            # HERE on the same basis the real backend's persist derives
            # its own from (the 08-04 aware-local idiom) — it labels
            # the attempt moment, never a persisted state.
            attempt_at = datetime.now().astimezone().strftime(
                env_check.CHECKED_AT_FORMAT)
            self.post_message(self.CheckRunComplete(
                attempt_at,
                tuple(results),
                run_id,
                persist_error=f"{type(exc).__name__}: {exc}",
            ))
            return
        self.post_message(
            self.CheckRunComplete(checked_at, tuple(results), run_id)
        )

    # ===== Message handlers (event-loop side: row mutation only, never kernels) =====

    def on_env_check_screen_check_item_checking(
            self, message: CheckItemChecking) -> None:
        """Flip the in-flight row to the checking state (inline fill)."""
        if message.run_id != self._run_id:
            return  # a newer exclusive run superseded this one (WR-02)
        if message.kernel_id not in S.ENV_KERNEL_LABELS:
            return
        table = self.query_one("#env-kernels", DataTable)
        table.update_cell(
            message.kernel_id, _COL_STATE,
            Text(S.ENV_STATE_CHECKING, style=_STYLE_DIM),
        )

    def on_env_check_screen_check_item_done(
            self, message: CheckItemDone) -> None:
        """Record the result and flip its row to the final glyph + summary."""
        if message.run_id != self._run_id:
            return  # a newer exclusive run superseded this result (WR-02)
        self._results[message.result.name] = message.result
        self._apply_result_to_table(message.result)

    def on_env_check_screen_check_run_complete(
            self, message: CheckRunComplete) -> None:
        """Render the last-check line + the verdict block (ENV-02/ENV-03)."""
        if message.run_id != self._run_id:
            return  # a newer exclusive run superseded this outcome (WR-02)
        # WR-03: only the ACCEPTED completion clears the in-flight flag
        # and caches the outcome — a stale-dropped completion belongs to
        # a superseding run that set the flag itself.
        self._check_in_flight = False
        self._last_outcome = (
            message.checked_at, message.results, message.persist_error)
        self._render_check_outcome(
            message.checked_at, message.results,
            persist_error=message.persist_error)

    # ===== Rendering (pure UI state mutation over service results) =====

    def _apply_result_to_table(self, result: CheckResult) -> None:
        """One result -> its row's state glyph and summary cells."""
        if result.name not in S.ENV_KERNEL_LABELS:
            return  # forward tolerance: unknown kernel ids never crash rows
        table = self.query_one("#env-kernels", DataTable)
        glyph = S.ENV_STATE_PASS if result.ok else S.ENV_STATE_FAIL
        style = _STYLE_PASS if result.ok else _STYLE_FAIL
        table.update_cell(result.name, _COL_STATE, Text(glyph, style=style))
        table.update_cell(result.name, _COL_SUMMARY, _summary_of(result))

    def _render_check_outcome(self, checked_at: str,
                              results: "tuple[CheckResult, ...]",
                              persist_error: "str | None" = None) -> None:
        """The last-check line + the advisory verdict/routing block (D-09).

        WR-03 (261016-a4f): ``persist_error`` None (the default — the
        on_mount cache-hit call site and every healthy run) renders the
        plain ``ENV_LAST_CHECK_LINE`` byte-identically; a persist
        failure renders ``ENV_LAST_CHECK_DEGRADED`` — a bare timestamp
        would promise a persisted same-day cache that does not exist.
        """
        if persist_error is None:
            self.query_one("#env-last-check", Label).update(
                S.ENV_LAST_CHECK_LINE.format(checked_at=checked_at)
            )
        else:
            self.query_one("#env-last-check", Label).update(
                S.ENV_LAST_CHECK_DEGRADED.format(
                    checked_at=checked_at, error=persist_error)
            )
        verdict = env_gate.gate_verdict(results)
        box = self.query_one("#env-verdict", Vertical)
        box.remove_children()
        if verdict.can_launch:
            box.mount(Static(S.ENV_VERDICT_PASS, classes="verdict-pass"))
        else:
            failing = [
                result.name for result in results
                if not result.ok and result.name in env_gate.CRITICAL
            ]
            box.mount(Static(
                S.ENV_VERDICT_CRITICAL_FAIL.format(
                    kernel_names=", ".join(failing)),
                classes="verdict-fail",
            ))
        # Per-KERNEL routing lines (261014-dcl) — never the
        # route_to_data bool alone: a model_dirs failure must not
        # fabricate a zero-count datasets line (and vice versa). Each
        # directory kernel renders its own copy only when THAT kernel
        # itself failed. WR-04 (261016-a4f): the lines route through
        # _route_line — a failed kernel with NO listing lines (the
        # registry read-failure / degraded shapes) renders its own
        # first FAIL line verbatim, never a fabricated zero-count
        # route.
        model_dirs = next(
            (result for result in results if result.name == "model_dirs"),
            None,
        )
        if model_dirs is not None and not model_dirs.ok:
            box.mount(Static(
                _route_line(model_dirs, S.ENV_ROUTE_MISSING_MODELS),
                classes="verdict-route",
            ))
        dataset_dirs = next(
            (result for result in results if result.name == "dataset_dirs"),
            None,
        )
        if dataset_dirs is not None and not dataset_dirs.ok:
            box.mount(Static(
                _route_line(dataset_dirs, S.ENV_ROUTE_MISSING_DATASETS),
                classes="verdict-route",
            ))

    # ===== Actions (user intent) =====

    def action_refresh(self) -> None:
        """The refresh key: reset every row to pending and re-run (D-05).

        The ONLY path that re-runs kernels after a cache hit; rows reset
        synchronously, the outcome slots clear, and the exclusive worker
        restarts (cancelling any still-running previous run). The
        storage section re-renders too (F4W-04): a slot-4 dir change
        reflects here after [r] or a console restart — the documented
        staleness boundary.
        """
        table = self.query_one("#env-kernels", DataTable)
        for kernel_id in S.ENV_KERNEL_LABELS:
            table.update_cell(
                kernel_id, _COL_STATE,
                Text(S.ENV_STATE_PENDING, style=_STYLE_DIM),
            )
            table.update_cell(kernel_id, _COL_SUMMARY, "")
        self._results.clear()
        self.query_one("#env-verdict", Vertical).remove_children()
        self.query_one("#env-last-check", Label).update("")
        self._render_storage()
        self._run_id += 1  # a new run: the old one's messages now drop (WR-02)
        # IN-03 (08 review, fix batch 261017-klw): the remount guard must
        # hold from DISPATCH, not from the worker thread's first line —
        # an L-toggle remount landing between this dispatch and the
        # worker body's own set would otherwise see the flag still
        # False, consult the same-day cache, and render the stale
        # pre-refresh outcome (the app's kick_download_queue busy-flag
        # discipline: set synchronously on the event loop, before the
        # worker is spawned). The worker-body set stays as the belt for
        # the mount-path dispatch (on_mount's run_full_check call).
        self._check_in_flight = True
        self.run_full_check()

    def _render_storage(self) -> None:
        """The slot-1 storage overview (F4W-04, 261014-f4w): five
        read-only rows — the ENV_STORAGE_LABELS label, the absolute
        path verbatim (data), and the ✓/✗ existence glyph over the
        $success/$error styles (the glyph-is-the-meaning-carrier rule)
        — plus the footer note routing edits to slot 4. Derived
        entirely from the injected service's ``storage_rows()`` (the
        same seeded load_state seam the directory kernels read roots
        through); a wrong-key row renders its key verbatim, never
        crashes (forward tolerance, the _apply_result_to_table
        precedent). Rendered at mount and re-rendered by [r]: a
        slot-4 dir change reflects after a refresh or a console
        restart — the staleness boundary.
        """
        box = self.query_one("#env-storage", Vertical)
        box.remove_children()
        box.mount(Static(S.ENV_STORAGE_TITLE, classes="env-storage-title"))
        # rich Text SPANS cannot carry Textual $token styles on the
        # Static render path (probe-pinned on 8.2.8, the nav.py
        # precedent): resolve the live theme's success/error at render —
        # the theme's own values, never a hardcoded hex — and render the
        # footer note rich-native dim (the migrated-label treatment).
        ok_color = self.app.current_theme.success
        bad_color = self.app.current_theme.error
        for row in self._service.storage_rows():
            label = S.ENV_STORAGE_LABELS.get(row.key, row.key)
            exists = bool(row.exists)
            glyph = S.ENV_STATE_PASS if exists else S.ENV_STATE_FAIL
            color = ok_color if exists else bad_color
            box.mount(Static(Text.assemble(
                Text(f"{glyph} ", style=f"bold {color}"),
                Text(f"{label}  "),
                Text(str(row.path)),
            ), classes="env-storage-row"))
        box.mount(Static(Text(S.ENV_STORAGE_NOTE, style="dim"),
                         classes="env-storage-note"))

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
        label = S.ENV_KERNEL_LABELS.get(kernel_id, kernel_id)
        self.app.push_screen(
            EnvDetailModal(kernel_id, label, result.lines)
        )
