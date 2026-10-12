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

10-04 wiring (the D-02/SC5 execution spine):

- The queue seam: the constructor accepts ``download_queue_service``
  (the driver-surface Protocol; None builds the real
  ``DownloadQueueService``). The app owns ONE shared instance — the
  driver worker, the data-manager screen, and (in 10-05) the
  selection/env screens all mutate the same queue.
- The driver worker: ONE exclusive ``@work(exclusive=True, thread=True)``
  loop over ``claim_next -> run_task -> post QueueEventMessage`` that
  RETURNS when no pending entry remains — ``wait_for_complete`` can
  never hang. ``kick_download_queue`` is guarded by a deterministic busy
  flag (set synchronously in kick, cleared in the worker finally) so a
  second enqueue never cancels an in-flight download (T-10-04-02).
- Boot resume (D-06): ``boot_resume_queue`` (service.load + kick iff
  pending entries exist) is scheduled ONLY by ``tui/__main__.main`` —
  never by ``App.on_mount``; test-constructed apps stay provably inert
  (T-10-04-03).
"""

from collections.abc import Callable
from threading import Lock
from typing import Any, ClassVar, Protocol

from rich.text import Text
from textual import events, work
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Vertical
from textual.message import Message
from textual.screen import ModalScreen, Screen
from textual.widgets import Footer, Static
from textual.worker import get_current_worker

from tui.screens.about import AboutScreen
from tui.screens.data_manager import DataManagerBackend, DataManagerScreen
from tui.screens.env_check import EnvCheckScreen, EnvCheckServiceProtocol
from tui.screens.nav import NAV_SLOT_BY_INDEX, binding_row
from tui.screens.selection import (
    SelectionQueueBackend,
    SelectionScreen,
    SelectionServiceProtocol,
)
from tui.services.download_queue import (
    DownloadQueueService,
    QueueEntry,
    QueueEvent,
)
from tui.strings import (
    APP_HELP_LABEL,
    APP_HELP_ROW,
    APP_HELP_TITLE,
    APP_MIN_SIZE_MESSAGE,
    APP_MODAL_BACK_LABEL,
    APP_QUIT_LABEL,
    APP_TITLE,
    NAV_PLACEHOLDER_TOAST,
    QUEUE_FLIP_TOAST,
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
                # A rich Text content object is never markup-parsed — the
                # keycap renders as literal text. Key displays may be
                # markup-reserved characters (the selection screen's "/"
                # filter keycap parsed as a broken auto-closing tag and
                # crashed the console — the row must stay literal).
                yield Static(Text(APP_HELP_ROW.format(key=key, label=label)))
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


class QueueDriverProtocol(Protocol):
    """The driver-surface queue Protocol the app consumes (10-04).

    The structural seam the tier-2 Pilot fakes conform to: the app only
    ever drives the queue (load/claim/run) — the screen-facing surface
    (snapshot reads, enqueue toasts, drill-down seams) lives behind
    ``DataManagerServiceProtocol`` in ``tui/screens/data_manager``.
    """

    def load(self) -> "str | None":
        """Tolerantly load the persisted queue state (D-06)."""

    def entries(self) -> "list[QueueEntry]":
        """The immutable entry snapshots, in file order."""

    def claim_next(self) -> "QueueEntry | None":
        """Claim the head pending entry (None when the queue is idle)."""

    def run_task(self, key: str, run_id: str,
                 progress_cb: Callable[[str, "int | None"], None] | None
                 = None) -> QueueEvent:
        """Execute one claimed task; NEVER raises (the service boundary)."""


class QueueEventMessage(Message):
    """One completed queue task (driver worker thread -> event loop).

    Carries the driver generation it belongs to (WR-02) — the handler
    drops posts from a superseded generation. Behind the kick busy-guard
    two drivers can never overlap, so the drop path guards only the
    teardown-time exclusive cancellation.
    """

    def __init__(self, event: QueueEvent, generation: int) -> None:
        self.event = event
        self.generation = generation
        super().__init__()


class QueueProgressMessage(Message):
    """One live progress tick (driver worker thread -> event loop).

    Throttled to integer-percent changes at BOTH layers (the service's
    parser dedupes within a task; the driver dedupes across posts);
    percent None is the indeterminate contract (the screen renders the
    indeterminate glyph, never a fabricated number).
    """

    def __init__(self, key: str, percent: "int | None",
                 generation: int) -> None:
        self.key = key
        self.percent = percent
        self.generation = generation
        super().__init__()


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
    # The about screen (09-03, D-13 slot 6) is STATELESS — it joins the
    # zero-arg registry as permitted (the only live state it touches is
    # the derived snapshot inside one worker run).
    # Classes instantiate lazily on first name access; name-based access
    # builds the default (real) service — the injected-service path is
    # get_default_screen below.
    SCREENS: ClassVar[dict[str, Callable[[], Screen[Any]]]] = {
        "env_check": EnvCheckScreen,
        "about": AboutScreen,
    }

    def __init__(self, env_check_service: EnvCheckServiceProtocol | None = None,
                 selection_service: SelectionServiceProtocol | None = None,
                 download_queue_service: QueueDriverProtocol | None = None):
        """Compose the console with injectable services.

        Args:
            env_check_service: optional service override for the env-check
                screen (the tier-2 Pilot seam — tests inject deterministic
                fakes so no real kernel executes in CI, D-03). None means
                the real service (EnvCheckBackend over the 08-04 module).
            selection_service: optional service override for the selection
                screen (the same seam pattern, 08-07). None means the real
                service (SelectionBackend over the 08-04/08-05 modules).
            download_queue_service: optional override for the shared
                download-queue service (the 10-04 seam — the driver loop
                AND the data-manager screen run over this ONE instance).
                None means the real ``DownloadQueueService``.
        """
        super().__init__()
        self._env_check_service = env_check_service
        self._selection_service = selection_service
        self._download_queue: QueueDriverProtocol = (
            download_queue_service if download_queue_service is not None
            else DownloadQueueService()
        )
        # The driver state (T-10-04-02): the busy flag is set
        # SYNCHRONOUSLY in kick and cleared in the worker's drain exit,
        # so two rapid enqueues can never start (and exclusive-cancel) a
        # second driver while a download is in flight. The generation
        # tags every driver post (WR-02). The lock makes the flag's
        # check-and-set (kick) atomic against the drain-side
        # release-and-recheck (WR-02's lost-wakeup guard).
        self._queue_busy = False
        self._queue_generation = 0
        self._queue_busy_lock = Lock()
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
        """Build the selection screen over the shared mark sets + queue.

        The screen factory (08-07): the injected-or-real service plus the
        SAME live mark-set instances every selection/matrix screen
        shares — constructed here, never through a zero-arg SCREENS slot
        (a slot-built screen would carry fresh sets and silently lose
        the SEL-01 persistence guarantee). 10-05 (D-14): the factory
        also bridges the app-level SHARED queue instance into the
        screen's enqueue seam (the SelectionQueueBackend two-Protocol
        bridge — the build_data_manager_screen rationale), so the
        selection screen's ``d``, the data-manager screen, and the
        driver all mutate ONE queue.
        """
        return SelectionScreen(
            selection_service=self._selection_service,
            marked_models=self._marked_models,
            marked_tasks=self._marked_tasks,
            queue_service=SelectionQueueBackend(self._download_queue),
        )

    def build_data_manager_screen(self) -> DataManagerScreen:
        """Build the data-manager screen over the SHARED queue service.

        The 10-04 factory (the build_selection_screen rationale): the
        screen's Backend adapter wraps the SAME app-level queue instance
        the driver worker drives, so an enqueue from the screen, a boot
        resume, and a driver event all mutate one queue — a zero-arg
        SCREENS slot would build a second service and silently fork the
        state.
        """
        return DataManagerScreen(
            data_service=DataManagerBackend(self._download_queue))

    # ===== Digit navigation (D-13, 09-03) =====

    async def action_nav(self, slot: int) -> None:
        """Route one top-menu digit press (the nav bars only render).

        Live slots switch the screen (switch_screen replaces the top of
        the stack — the depth never grows under digit navigation);
        placeholder slots are NEVER silent: the toast names the
        delivering phase (D-13). A press targeting the screen already
        active is a no-op (no redundant rebuild, no worker restart).
        """
        target = NAV_SLOT_BY_INDEX.get(slot)
        if target is None:
            return
        if target.phase is not None:
            self.notify(NAV_PLACEHOLDER_TOAST.format(n=target.phase))
            return
        current = self.screen
        if target.target == "env_check":
            if isinstance(current, EnvCheckScreen):
                return
            await self.switch_screen(self.get_default_screen())
        elif target.target == "selection":
            if isinstance(current, SelectionScreen):
                return
            await self.switch_screen(self.build_selection_screen())
        elif target.target == "data_manager":
            if isinstance(current, DataManagerScreen):
                return
            await self.switch_screen(self.build_data_manager_screen())
        elif target.target == "about":
            if isinstance(current, AboutScreen):
                return
            # the stateless zero-arg SCREENS slot (D-13; the injected
            # service path does not exist for about — tests pin env roots)
            await self.switch_screen("about")

    # ===== The download-queue execution spine (10-04, D-02/SC5) =====

    def kick_download_queue(self) -> None:
        """Start the driver iff it is idle (the T-10-04-02 busy guard).

        The check-and-set runs under the busy lock (WR-02) — atomic
        against the worker's drain-side release-and-recheck, so a kick
        racing the drain either sees the flag released and starts the
        next driver itself, or is a guarded no-op while the SAME worker
        absorbs the entry it was racing. The flag is set SYNCHRONOUSLY
        here — before any await — so two rapid enqueues (or an enqueue
        racing boot resume) can never both reach ``run_download_queue``:
        an exclusive restart would CANCEL the in-flight download's
        worker thread mid-task. The worker's drain exit clears the flag
        under the same lock exactly when the queue has drained
        (``claim_next`` returned None and no pending entry exists), so
        a later enqueue restarts it.
        """
        with self._queue_busy_lock:
            if self._queue_busy:
                return
            self._queue_busy = True
            self._queue_generation += 1
        self.run_download_queue()

    @work(exclusive=True, thread=True)
    def run_download_queue(self) -> None:
        """Drive the serial queue until it drains (never on the loop).

        One claim -> one task -> one event post, repeated; RETURNS when
        ``claim_next`` finds no pending entry — ``wait_for_complete`` can
        therefore never hang on an idle queue. All subprocess/HTTP I/O
        lives inside the service's ``run_task`` (D-02: spawn/reap/parse
        in this OS thread, never in-process, never on the event loop —
        SC5). Progress crosses as a second message throttled to
        integer-percent changes; every post carries the driver
        generation (WR-02).
        """
        worker = get_current_worker()
        generation = self._queue_generation
        last_percent: dict[str, int | None] = {}

        def on_progress(key: str, percent: "int | None") -> None:
            # throttle: the service dedupes within a task; this dedupes
            # the post itself across tasks/retries of the same key
            if percent is not None and last_percent.get(key) == percent:
                return
            last_percent[key] = percent
            self.post_message(
                QueueProgressMessage(key, percent, generation))

        try:
            while True:
                if worker.is_cancelled:
                    return
                entry = self._download_queue.claim_next()
                if entry is None:
                    # WR-02 (the lost-wakeup guard): an enqueue+kick that
                    # lands between this drain scan and the busy-flag
                    # release sees the flag still set and is a guarded
                    # no-op — the entry would strand with no driver. The
                    # release-and-recheck below is ATOMIC against kick's
                    # check-and-set (the shared lock): if the pending
                    # entry is already visible HERE, this SAME worker
                    # keeps driving it (no restart, no second driver —
                    # D-04 serial stays guaranteed); if not, the flag is
                    # released and any concurrent kick starts the next
                    # driver itself.
                    with self._queue_busy_lock:
                        if self._queue_generation != generation:
                            return  # a successor owns the flag
                        pending = False
                        try:
                            pending = any(
                                item.state == "pending"
                                for item
                                in self._download_queue.entries())
                        except Exception:  # noqa: BLE001 — never raise here
                            pending = False
                        if pending:
                            continue    # keep driving THIS worker
                        self._queue_busy = False
                    return  # drained — the no-hang contract
                if worker.is_cancelled:
                    return
                # the claim tick: one indeterminate post flips the row
                # to its downloading state before any percent parses
                # (unparsed CLI output may never fire a real tick)
                self.post_message(
                    QueueProgressMessage(entry.key, None, generation))
                event = self._download_queue.run_task(
                    entry.key,
                    f"driver-{generation}-{entry.key}",
                    progress_cb=on_progress,
                )
                self.post_message(QueueEventMessage(event, generation))
        finally:
            with self._queue_busy_lock:
                if self._queue_generation == generation:
                    self._queue_busy = False
                # a superseded generation owns the flag now — never
                # clear a successor's guard (the release-and-recheck
                # below is the only drain-side clear)

    def boot_resume_queue(self) -> None:
        """D-06 boot resume: load the persisted queue; kick iff work
        is pending (a restart with queued work resumes automatically).

        Scheduled ONLY by ``tui/__main__.main`` via ``call_later`` —
        never by ``App.on_mount``: test-constructed apps stay provably
        inert (T-10-04-03 — no real download can ever start from a Pilot
        test), while the operator's console resumes on boot.
        """
        self._download_queue.load()
        if any(entry.state == "pending"
               for entry in self._download_queue.entries()):
            self.kick_download_queue()

    def on_queue_event_message(self, message: QueueEventMessage) -> None:
        """One task finished: flip-toast on done, forward to the screen.

        The done state IS the reconcile pass (the service's done gate,
        D-09), so done is exactly the D-11 presence-flip moment — the
        app-level QUEUE_FLIP_TOAST fires here. The forward reaches the
        current screen's ``apply_queue_event`` when the attribute exists
        (the data-manager screen consumes it now; the selection screen
        joins in 10-05 through the same forward).
        """
        if message.generation != self._queue_generation:
            return  # a superseded driver's late post (WR-02)
        event = message.event
        if event.state == "done":
            self.notify(QUEUE_FLIP_TOAST.format(key=event.key))
        apply_event = getattr(self.screen, "apply_queue_event", None)
        if apply_event is not None:
            apply_event(event)

    def on_queue_progress_message(self, message: QueueProgressMessage) -> None:
        """One live progress tick: forward to the screen's row updater."""
        if message.generation != self._queue_generation:
            return  # a superseded driver's late post (WR-02)
        apply_progress = getattr(
            self.screen, "apply_queue_progress", None)
        if apply_progress is not None:
            apply_progress(message.key, message.percent)

    # ===== Min-size guard (08-UI-SPEC Terminal Contract) =====

    def on_mount(self) -> None:
        """Check the grid once at mount (resize events re-check live)."""
        # textual 8.2.8 probe-pinned fact (09-03): the boot screen is
        # appended to the stack WITHOUT push bookkeeping, so switching
        # away from it (switch_screen/pop_screen's _pop_result_callback)
        # raises IndexError on the empty callback list. Register the one
        # missing result-callback entry here so digit navigation can
        # switch away from the opening screen.
        self.screen._push_result_callback(self.screen, None)
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
        trip — the pop restores the exact stack. The pop itself only
        fires when the guard IS the active screen: popping the top screen
        unconditionally would remove a modal that legitimately sits
        beneath the guard and strand the guard itself (WR-01).
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
            if self.screen is guard:
                self.pop_screen()

    @property
    def below_minimum_grid(self) -> bool:
        """True while the min-size guard screen is up (no chrome may open).

        The guard state every ASYNC chrome push must check (WR-06): a
        message-handler push can fire while the guard is the active
        screen (the screen beneath keeps pumping), and a modal pushed
        over the guard strands it at full size on grow — the restore pop
        fires only when the guard IS the top screen (WR-01).
        """
        return self._min_size_screen is not None

    # ===== Actions (app-level) =====

    def action_help(self) -> None:
        """The ``?`` key: the help modal over the current screen.

        Suppressed below the minimum grid: no chrome may open over the
        guard (a modal pushed there would be popped instead of the guard
        on grow, stranding the console on the min-size screen at full
        size — WR-01).
        """
        if self.below_minimum_grid:
            return  # below the minimum grid: no chrome over the guard
        self.push_screen(HelpModal(self._binding_rows()))

    def _binding_rows(self) -> "list[tuple[str, str]]":
        """Every active binding as (display key, Chinese label) rows.

        App bindings first, then the active screen's — the help surface
        always reflects the live key map (k9s-style contextual help).
        The descriptions are the strings-module constants wired into the
        BINDINGS declarations — no copy is redefined here (I18N-01).
        The row projection itself is ``tui.screens.nav.binding_row``
        (moved there in 09-03 so the nav bars and the help modal share
        the ONE key-map source).
        """
        rows = [row for row in map(binding_row, self.BINDINGS)
                if row is not None]
        rows.extend(row for row
                    in map(binding_row, getattr(self.screen, "BINDINGS", []))
                    if row is not None)
        return rows
