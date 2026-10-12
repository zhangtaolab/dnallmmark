"""
data_manager — the slot-3 data-manager screen (Phase 10, 10-04;
D-13/D-14/D-15 + the D-12 Zenodo entry surface).

The operator's window onto everything 10-01..10-03 built: the
missing-datasets list (the n_audit missing set, the d/a target), the
persistent download queue (five-state rows with live progress cells and
the reconcile column), the mismatch banners (D-07/D-09), the Zenodo
whole-package line (D-12), and the verbatim drill-down (D-03).

Contract (locked decisions):

- PRESENTATION ONLY (the screens-tier contract): channel resolution,
  verdicts, presence, and missing-set derivation all live in
  ``tui/services/download_queue`` + ``zenodo_bundle``; this screen
  renders service results and posts user intent. The one adapter here
  (``DataManagerBackend``) is delegation glue over those services — the
  same shape as ``EnvCheckBackend``/``SelectionBackend``.
- D-02/SC5: every service I/O leg (snapshot reads, the Zenodo probe, the
  ``g`` re-audit) runs inside an exclusive ``@work(exclusive=True,
  thread=True)`` worker; results cross the worker-thread -> event-loop
  boundary exclusively via ``post_message`` of a run-id-tagged nested
  ``Message`` (WR-02 — handlers drop stale ids); the console never
  freezes. The DOWNLOAD loop itself is the app-level driver worker
  (``tui/app.py``) — never started by this screen, only kicked.
- Persisted-state-as-truth (T-10-04-01): the app-forwarded queue events
  are applied by RE-READING the entry from the service and re-rendering
  its row — a late or duplicated event can therefore never overwrite a
  newer state; the row always shows the queue's own current truth.
- D-15: the bottom bar is d enqueue / r retry / x cancel / a
  enqueue-all / enter detail (declaration order) + the constant ``?``
  ``q`` right segment; ``g`` (re-audit, mismatch rows) and ``z``
  (Zenodo) are show=False bindings (auto-defaults 7 and the D-12
  entry).
- D-07/D-09: mismatch entries render one prominent banner row each
  directly under the queue title AND sort to the top of the queue table
  (with failed rows); presence never flips on mismatch (the service's
  done gate owns that upstream, D-11). Banners render only where the
  reconcile payload carries the declared/measured numbers (dataset
  granularity — the contract's {n}/{m} fields); a mismatched BUNDLE row
  sorts to the top and carries its per-key map in the drill-down (no
  number pair exists for the whole-package lane).
- D-03: the drill-down renders data, never translated, never elided —
  the full key, the registry ``download_url`` (the only download
  authority, D-01/SC1), the composed LIST argv, the reconcile numbers,
  and the verbatim CLI/audit log lines through the Backend read seam.
- WR-06: every async chrome push (drill-down, cancel confirm) checks
  ``app.below_minimum_grid`` first — no modal may open over the guard.
- I18N-01: zero Chinese literals in this module — every operator-facing
  string renders through ``tui/strings.py`` constants (grep-enforced);
  dataset keys, URLs, argv, machine codes, and file paths stay English
  verbatim (data, never copy). The ``—`` table dash and the probe-error
  placeholder below are table symbols / data words, not copy.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar, Protocol

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen, Screen
from textual.widgets import DataTable, Footer, Label, RichLog, Static

from tui.screens.nav import BottomBar, TopMenuBar
from tui.screens.selection import ConfirmModal
from tui.services import download_queue, registries, settings, zenodo_bundle
from tui.services.download_queue import (
    KIND_ZENODO_BUNDLE,
    ZENODO_BUNDLE_KEY,
    EnqueueOutcome,
    MissingInfo,
    QueueEntry,
    QueueEvent,
    ReauditOutcome,
)
from tui.strings import (
    APP_MODAL_BACK_LABEL,
    DL_BUNDLE_TASK_NAME,
    DL_CANCEL_LABEL,
    DL_DISABLED_TOAST,
    DL_UNKNOWN_TOAST,
    DL_ENQUEUE_ALL_LABEL,
    DL_ENQUEUE_LABEL,
    DL_MISSING_COL_KEY,
    DL_MISSING_COL_ROWS,
    DL_MISSING_EMPTY,
    DL_MISSING_TITLE,
    DL_PRESENCE_SUMMARY,
    DL_RETRY_LABEL,
    DL_SCREEN_TITLE,
    DL_ZENODO_DISABLED_TOAST,
    DL_ZENODO_FAILED,
    DL_ZENODO_KEY_LABEL,
    DL_ZENODO_NOT_PUBLIC,
    DL_ZENODO_PROBING,
    DL_ZENODO_PUBLIC,
    ENV_DETAIL_LABEL,
    NAV_LABEL_ABOUT,
    NAV_LABEL_DATA,
    NAV_LABEL_ENV,
    NAV_LABEL_MONITOR,
    NAV_LABEL_RUN_CONFIG,
    NAV_LABEL_SELECTION,
    QUEUE_BANNER_MISMATCH,
    QUEUE_CANCEL_NOOP,
    QUEUE_CLI_UNAVAILABLE,
    QUEUE_PERSIST_FAILED_TOAST,
    QUEUE_COL_PROGRESS,
    QUEUE_COL_RECONCILE,
    QUEUE_COL_STATE,
    QUEUE_COL_TASK,
    QUEUE_CONFIRM_CANCEL_DOWNLOADING,
    QUEUE_CONFIRM_CANCEL_PENDING,
    QUEUE_EMPTY,
    QUEUE_PROGRESS_INDETERMINATE,
    QUEUE_REAUDIT_LABEL,
    QUEUE_RECONCILE_MISMATCH,
    QUEUE_RECONCILE_PASS,
    QUEUE_RECONCILE_RUNNING,
    QUEUE_RESTART_NOTE,
    QUEUE_RETRY_NOOP,
    QUEUE_STATE_DONE,
    QUEUE_STATE_DOWNLOADING,
    QUEUE_STATE_FAILED,
    QUEUE_STATE_MISMATCH,
    QUEUE_STATE_PENDING,
    QUEUE_TITLE,
    QUEUE_TOAST_ALREADY_QUEUED,
    QUEUE_TOAST_ENQUEUED,
    QUEUE_TOAST_ENQUEUED_ALL,
)

if TYPE_CHECKING:
    from textual import getters

    from tui.app import DnallmMarkTui


# ===== Column geometry (10-UI-SPEC auto-default 2) =====
#
# The queue table's pinned widths keep the D-15 four-column budget inside
# 80 cells: the task column carries the 68-char-key truncation lesson
# (full key always in the enter detail), the progress column fits the
# contract composition exactly — a right-aligned 4-cell percent + one
# space + the 10-cell bar (15 content cells + the DataTable's 2-cell
# default padding = 17; textual column widths are TOTAL width including
# padding, probe-pinned on 8.2.8). The reconcile column takes the rest.

_TASK_W = 33
_STATE_W = 10
_PROGRESS_W = 17

#: The DataTable's default per-side cell padding (content = width - 2).
_CONTENT_PAD = 2

#: (column key, header constant, width) — the column keys are the
#: update_cell addressing scheme (English technical ids, I18N-01).
_QUEUE_COLUMNS: tuple[tuple[str, str, int], ...] = (
    ("task", QUEUE_COL_TASK, _TASK_W),
    ("state", QUEUE_COL_STATE, _STATE_W),
    ("progress", QUEUE_COL_PROGRESS, _PROGRESS_W),
    ("reconcile", QUEUE_COL_RECONCILE, 0),  # 0 = the flex remainder
)

_MISSING_COLUMNS: tuple[tuple[str, str, int], ...] = (
    ("key", DL_MISSING_COL_KEY, _TASK_W),
    ("rows", DL_MISSING_COL_ROWS, 0),
)

# Row keys for the non-entry state rows (never action targets).
_MISSING_EMPTY_ROW_KEY = "_missing-empty"
_QUEUE_EMPTY_ROW_KEY = "_queue-empty"

# Table symbols / data words (not operator copy — see the module header).
_DASH = "—"
_PROBE_ERROR_DETAIL = "unknown"  # the probe API answers a bare state

# Per-cell rich Text styles: semantic theme tokens only (the glyph is
# the meaning-carrier under NO_COLOR; color is the redundant channel).
_STYLE_MUTED = "$text-muted"
_STYLE_RUNNING = "dim"
_STYLE_DONE = "bold $success"
_STYLE_FAIL = "bold $error"
_STYLE_WARN = "$warning"
#: The five queue states -> (copy constant, style).
_STATE_CELLS = {
    "pending": (QUEUE_STATE_PENDING, _STYLE_MUTED),
    "downloading": (QUEUE_STATE_DOWNLOADING, _STYLE_RUNNING),
    "done": (QUEUE_STATE_DONE, _STYLE_DONE),
    "failed": (QUEUE_STATE_FAILED, _STYLE_FAIL),
    "mismatch": (QUEUE_STATE_MISMATCH, _STYLE_WARN),
}


@dataclass(frozen=True)
class MissingSnapshot:
    """The missing-list read result (pure service data; the screen renders).

    Attributes:
        rows: one ``MissingInfo`` per missing official key (registry order).
        total: the audited dataset count (the committed n_audit view).
        present: the present count over the same view.
        load_diagnostic: the queue file's corrupt-load diagnostic when
            the last load quarantined a state file (None on every
            healthy session) — rendered verbatim as the status line
            (data, never copy); remembered for the session by the
            service so reloads keep surfacing it (10-06).
    """

    rows: "tuple[MissingInfo, ...]"
    total: int
    present: int
    load_diagnostic: "str | None" = None

    @property
    def missing(self) -> int:
        """The missing count (the rows themselves)."""
        return len(self.rows)


@dataclass(frozen=True)
class ChannelDetail:
    """One key's drill-down channel data (D-03; pure data, never copy).

    Attributes:
        key: the dataset registry key (or the Zenodo bundle key).
        source_url: the winning registry URL (the only download
            authority, D-01/R-01) — None when the channel never resolved.
        argv: the composed LIST argv (data, space-joined in the detail);
            None when no argv is ever composed (degraded channels, the
            CLI-absent machine, or the bundle lane's stdlib-HTTP path).
        channel: the disposition vocabulary (``downloadable`` /
            ``disabled`` / ``unknown``).
        reason_code: the machine reason for degraded channels.
    """

    key: str
    source_url: "str | None"
    argv: "tuple[str, ...] | None"
    channel: str
    reason_code: "str | None"


class DataManagerServiceProtocol(Protocol):
    """The data-manager service surface the screen consumes.

    The constructor-injection seam (the EnvCheckServiceProtocol shape):
    the real ``DataManagerBackend`` and the tier-2 Pilot fakes both
    conform structurally — no real registry read, network probe, or
    subprocess ever executes in CI (D-03).
    """

    def missing_snapshot(self) -> MissingSnapshot:
        """The missing rows + the presence summary numbers."""

    def entries(self) -> "tuple[QueueEntry, ...]":
        """The queue entries, in file order."""

    def enqueue(self, key: str) -> EnqueueOutcome:
        """Idempotently enqueue one dataset key."""

    def enqueue_all(self) -> int:
        """Enqueue every missing downloadable key; return the new count."""

    def enqueue_zenodo(self) -> EnqueueOutcome:
        """Idempotently enqueue the Zenodo whole-package bundle."""

    def retry(self, key: str) -> bool:
        """Re-queue one failed/mismatch entry (False on other states)."""

    def cancel(self, key: str) -> str:
        """Cancel one entry: removed / signalled / noop."""

    def reaudit(self, run_id: str) -> ReauditOutcome:
        """The explicit g re-audit (D-10/R-03 default outputs)."""

    def probe_zenodo(self) -> str:
        """The D-12 publication probe: public / not_public / failed."""

    def channel_detail(self, key: str) -> ChannelDetail:
        """The drill-down channel data for one key."""

    def read_log(self, key: str) -> "tuple[str, ...]":
        """The verbatim log lines for one queue entry."""


class DataManagerBackend:
    """The real data-manager service adapter — thin delegation glue.

    Every semantic stays in the services (``download_queue`` owns the
    queue/channel/reaudit legs, ``zenodo_bundle`` owns the probe,
    ``registries`` owns the presence view): this adapter only composes
    service outputs into the Protocol shapes the screen consumes. The
    queue instance is the APP-level shared service (the driver worker
    and this screen mutate the same queue — the plan's one-instance
    wiring); a default-constructed backend builds its own real service
    for the never-injected path.
    """

    def __init__(self, queue: Any = None):
        """Adapt over one (shared) queue service instance.

        Args:
            queue: the app-level queue service (the shared instance the
                driver worker drives); None builds a fresh real
                ``DownloadQueueService``. Typed ``Any`` deliberately —
                this is the adapter boundary between the app's
                driver-surface Protocol (``QueueDriverProtocol``) and the
                screen's Protocol: the REAL service and the tier-2 fakes
                both satisfy the consumed surface structurally
                (``missing_datasets``/``merged_audit_tasks``/``entries``/
                ``enqueue``/``enqueue_all_missing``/``enqueue_zenodo``/
                ``retry``/``cancel``/``reaudit_baseline``/
                ``resolve_channel``, with ``probe_zenodo`` optional via
                the getattr guard).
        """
        self._queue: Any = (queue if queue is not None
                            else download_queue.DownloadQueueService())

    def missing_snapshot(self) -> MissingSnapshot:
        """The missing rows + the presence summary + the load state.

        Rehydrates the shared queue through its tolerant ``load()``
        FIRST (10-06: a screen mounted over a not-yet-loaded service —
        the test path, or any mount racing the boot resume — reads the
        persisted entries; in production the boot resume has usually
        loaded already and this is an idempotent no-op read), then
        derives BOTH surfaces from the D-11 MERGED view through the
        queue's own state path (CR-01: rows AND present/total move
        together — a reconcile-pass key leaves the missing list and
        counts present the moment its queue entry turns done); the
        denominator stays the committed view's audited count. An absent
        n_audit yields zero rows and a zero denominator — the missing
        set is unknowable, not "everything" (the service rule). The
        corrupt-load diagnostic rides the snapshot from the service's
        SESSION memory (``load()`` returns it exactly once; the
        remembered value survives this adapter's every reload).
        """
        self._queue.load()
        diagnostic_getter = getattr(
            self._queue, "last_load_diagnostic", None)
        diagnostic_value = (diagnostic_getter()
                            if diagnostic_getter is not None else None)
        diagnostic = (str(diagnostic_value)
                      if diagnostic_value is not None else None)
        rows = self._queue.missing_datasets()
        committed = registries.load_n_audit()
        if committed is None:
            return MissingSnapshot(
                rows=tuple(rows), total=0, present=0,
                load_diagnostic=diagnostic)
        merged = self._queue.merged_audit_tasks()
        present = sum(
            1 for key in merged
            if registries.presence_for(key, merged).status
            == registries.PRESENCE_PRESENT
        )
        return MissingSnapshot(
            rows=tuple(rows), total=len(committed), present=present,
            load_diagnostic=diagnostic)

    def entries(self) -> "tuple[QueueEntry, ...]":
        """The shared queue's entries (file order)."""
        return tuple(self._queue.entries())

    def enqueue(self, key: str) -> EnqueueOutcome:
        """Delegate the idempotent enqueue."""
        return self._queue.enqueue(key)

    def enqueue_all(self) -> int:
        """Delegate the enqueue-all-missing sweep."""
        return self._queue.enqueue_all_missing()

    def enqueue_zenodo(self) -> EnqueueOutcome:
        """Delegate the D-12 bundle enqueue (CLI-free)."""
        return self._queue.enqueue_zenodo()

    def retry(self, key: str) -> bool:
        """Delegate the failed/mismatch re-queue."""
        return self._queue.retry(key)

    def cancel(self, key: str) -> str:
        """Delegate the cancel (remove / signal / noop)."""
        return self._queue.cancel(key)

    def reaudit(self, run_id: str) -> ReauditOutcome:
        """Delegate the explicit baseline re-audit (R-03 default outputs)."""
        return self._queue.reaudit_baseline(run_id)

    def probe_zenodo(self) -> str:
        """The D-12 probe — through the queue when it carries one (the
        real service's ``probe_zenodo`` routes its ``zenodo_fetch``
        seam, and the Pilot fakes stay deterministic), else the real
        frozen-URL GET (queues without the method)."""
        queue_probe = getattr(self._queue, "probe_zenodo", None)
        if queue_probe is not None:
            return str(queue_probe())
        return zenodo_bundle.probe_zenodo_public()

    def channel_detail(self, key: str) -> ChannelDetail:
        """The drill-down channel data (registry authority + LIST argv)."""
        if key == ZENODO_BUNDLE_KEY:
            return ChannelDetail(
                key=key, source_url=zenodo_bundle.ZENODO_API_URL,
                argv=None, channel="downloadable", reason_code=None)
        spec = self._queue.resolve_channel(key)
        if spec is None:
            return ChannelDetail(
                key=key, source_url=None, argv=None, channel="unknown",
                reason_code="unknown_key")
        argv = None
        if spec.reason_code is None:
            cli = download_queue.resolve_modelscope_cli()
            if cli is not None:
                composed = download_queue.compose_download_argv(spec, cli)
                argv = tuple(composed) if composed else None
        return ChannelDetail(
            key=key, source_url=spec.source_url, argv=argv,
            channel=download_queue.channel_state(spec),
            reason_code=spec.reason_code)

    def read_log(self, key: str) -> "tuple[str, ...]":
        """The verbatim drill-down log lines (empty when none exist)."""
        entry = next((item for item in self._queue.entries()
                      if item.key == key), None)
        if entry is None or not entry.log_path:
            return ()
        path = settings.state_dir() / entry.log_path
        try:
            return tuple(path.read_text(encoding="utf-8").splitlines())
        except OSError:
            return ()


def _truncate(text: Text, width: int) -> Text:
    """Ellipsis-truncate one rich Text in place (Rich's measurement)."""
    text.truncate(width, overflow="ellipsis", pad=False)
    return text


def _cell(value: object, width: int, style: "str | None" = None) -> Text:
    """One DataTable cell: plain text, ellipsis-truncated to the width."""
    return _truncate(
        Text(str(value), style=style) if style else Text(str(value)),
        width,
    )


def _int_sum(values: object) -> int:
    """Sum the non-bool int values of a mapping (defensive, 0 on junk)."""
    if not isinstance(values, dict):
        return 0
    return sum(value for value in values.values()
               if isinstance(value, int) and not isinstance(value, bool))


def _sorted_entries(entries: "tuple[QueueEntry, ...]"
                    ) -> "tuple[QueueEntry, ...]":
    """Mismatch and failed rows first (stable file order within groups)."""
    return tuple(sorted(
        entries,
        key=lambda entry: 0 if entry.state in ("mismatch", "failed") else 1,
    ))


class QueueDetailModal(ModalScreen):
    """The drill-down modal: the row's own data, verbatim (D-03).

    A wrapping, scrolling RichLog renders the composed data lines — the
    full key, the registry URL, the LIST argv, the reconcile numbers,
    the machine problems, and the verbatim CLI/audit log; long values
    wrap, nothing is ever elided.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, entry_key: str,
                 lines: "tuple[str, ...]", **kwargs):
        super().__init__(**kwargs)
        self.entry_key = entry_key
        self.detail_lines = tuple(lines)

    def compose(self) -> ComposeResult:
        with Vertical(id="dl-detail-box", classes="modal-box"):
            yield RichLog(wrap=True, id="dl-detail-log")
            yield Footer()

    def on_mount(self) -> None:
        box = self.query_one("#dl-detail-box", Vertical)
        box.border_title = self.entry_key
        log = self.query_one("#dl-detail-log", RichLog)
        for line in self.detail_lines:
            log.write(line)


class DataManagerScreen(Screen):
    """The data-manager screen: two panes over the shared queue service."""

    # D-13 slot 3 (the top-menu active-slot marker the nav bar reads).
    NAV_SLOT: ClassVar[int] = 3

    if TYPE_CHECKING:
        # Narrows MessagePump's ``App[object]`` to the composition root
        # (the selection-screen idiom — no runtime import of tui.app).
        app = getters.app(DnallmMarkTui)

    # The D-15 bottom-bar vocabulary in declaration order (d/r/x/a/enter
    # visible; the clip policy drops least-primary first), then the
    # show=False pair: g (re-audit, mismatch rows — auto-default 7) and
    # z (the D-12 Zenodo entry). The nav digits are plain per-screen
    # bindings routed to the app's nav action (never priority, Pattern 2).
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("d", "enqueue_cursor", DL_ENQUEUE_LABEL),
        Binding("r", "retry_cursor", DL_RETRY_LABEL),
        Binding("x", "cancel_cursor", DL_CANCEL_LABEL),
        Binding("a", "enqueue_all", DL_ENQUEUE_ALL_LABEL),
        Binding("enter", "show_detail", ENV_DETAIL_LABEL),
        Binding("g", "reaudit_cursor", QUEUE_REAUDIT_LABEL, show=False),
        Binding("z", "zenodo_bundle", DL_ZENODO_KEY_LABEL, show=False),
        Binding("1", "app.nav(1)", NAV_LABEL_ENV, show=False),
        Binding("2", "app.nav(2)", NAV_LABEL_SELECTION, show=False),
        Binding("3", "app.nav(3)", NAV_LABEL_DATA, show=False),
        Binding("4", "app.nav(4)", NAV_LABEL_RUN_CONFIG, show=False),
        Binding("5", "app.nav(5)", NAV_LABEL_MONITOR, show=False),
        Binding("6", "app.nav(6)", NAV_LABEL_ABOUT, show=False),
    ]

    class SnapshotLoaded(Message):
        """The mount/reload snapshot arrived (worker thread -> loop).

        Carries the run id — handlers drop superseded reloads (WR-02).
        """

        def __init__(self, snapshot: MissingSnapshot,
                     entries: "tuple[QueueEntry, ...]",
                     run_id: int) -> None:
            self.snapshot = snapshot
            self.entries = entries
            self.run_id = run_id
            super().__init__()

    class ZenodoProbed(Message):
        """The D-12 probe answered (worker thread -> loop; WR-02)."""

        def __init__(self, state: str, probed_at: str,
                     run_id: int) -> None:
            self.state = state
            self.probed_at = probed_at
            self.run_id = run_id
            super().__init__()

    class ReauditDone(Message):
        """The g re-audit finished (worker thread -> loop; WR-02)."""

        def __init__(self, run_id: int) -> None:
            self.run_id = run_id
            super().__init__()

    def __init__(self,
                 data_service: "DataManagerServiceProtocol | None" = None,
                 **kwargs):
        super().__init__(**kwargs)
        self._service: DataManagerServiceProtocol = (
            data_service if data_service is not None
            else DataManagerBackend()
        )
        self._snapshot: MissingSnapshot | None = None
        self._queue_entries: tuple[QueueEntry, ...] = ()
        # Live percents streamed from the driver (None = indeterminate).
        self._live_percents: dict[str, int | None] = {}
        # The per-worker run ids (WR-02): bumped on every reload so a
        # superseded worker's late post drops.
        self._snapshot_run_id = 0
        self._probe_run_id = 0
        self._reaudit_run_id = 0
        # The Zenodo line state (None = probing, the compose default).
        self._zenodo_state: str | None = None
        self._zenodo_probed_at = ""

    def compose(self) -> ComposeResult:
        """The screen frame: nav bars, title bar, the two stacked regions.

        The missing region is fixed-height (title + header + ~3 rows,
        auto-default 1); the queue region takes the flex remainder; the
        full-width rule separates them (the existing treatment — borders
        stay reserved for modals). The Zenodo line lives right-aligned
        in the missing-section title row (D-12).
        """
        yield TopMenuBar()
        with Horizontal(id="dl-title-bar"):
            yield Label(DL_SCREEN_TITLE, id="dl-screen-title")
            yield Label("", id="dl-presence-summary")
        # The corrupt-load status line (10-06): hidden by default (zero
        # layout cost on the healthy path — the 80x24 budget keeps its
        # geometry), shown verbatim when the snapshot carries the
        # session's quarantine diagnostic.
        diagnostic_line = Label("", id="dl-load-diagnostic")
        diagnostic_line.display = False
        yield diagnostic_line
        with Vertical(id="dl-missing-region"):
            with Horizontal(id="dl-missing-title-row"):
                yield Label(
                    DL_MISSING_TITLE.format(n=0), id="dl-missing-title")
                yield Label(DL_ZENODO_PROBING, id="dl-zenodo-line")
            yield DataTable(id="dl-missing")
        with Vertical(id="dl-queue-region"):
            yield Label(QUEUE_TITLE.format(n=0), id="dl-queue-title")
            yield Vertical(id="dl-queue-banners")
            yield DataTable(id="dl-queue")
        yield BottomBar()

    def on_mount(self) -> None:
        """Build the two tables, focus the missing list, start the reads."""
        for table_id, columns in (("#dl-missing", _MISSING_COLUMNS),
                                  ("#dl-queue", _QUEUE_COLUMNS)):
            table = self.query_one(table_id, DataTable)
            table.cursor_type = "row"
            table.zebra_stripes = True
            for column_key, header, width in columns:
                if width:
                    table.add_column(header, key=column_key, width=width)
                else:
                    table.add_column(header, key=column_key)
        self.query_one("#dl-missing", DataTable).focus()
        self._load_snapshot()
        self._probe_zenodo()

    # ===== The exclusive read workers (D-03/D-12/SC5) =====
    #
    # Each worker carries its OWN group: textual exclusivity cancels by
    # (node, group), so a shared "default" group would make the mount
    # pair (snapshot + probe) cancel each other — the probe's start
    # kills the just-started snapshot thread (probe-pinned on 8.2.8;
    # the env/selection screens never hit this only because their
    # workers never overlap).

    @work(exclusive=True, thread=True, group="dl-snapshot")
    def _load_snapshot(self) -> None:
        """Read the missing snapshot + queue entries off the event loop."""
        run_id = self._snapshot_run_id  # the run this worker serves (WR-02)
        snapshot = self._service.missing_snapshot()
        entries = self._service.entries()
        self.post_message(
            self.SnapshotLoaded(snapshot, entries, run_id))

    @work(exclusive=True, thread=True, group="dl-probe")
    def _probe_zenodo(self) -> None:
        """The D-12 publication probe (session-memory; auto-default 6)."""
        run_id = self._probe_run_id
        state = self._service.probe_zenodo()
        # aware local (the _now_iso idiom) — the HH:MM is a wall-clock
        probed_at = datetime.now().astimezone().strftime("%H:%M")
        self.post_message(self.ZenodoProbed(state, probed_at, run_id))

    @work(exclusive=True, thread=True, group="dl-reaudit")
    def _run_reaudit(self) -> None:
        """The explicit g re-audit — the audit subprocess stays inside
        the worker (R-03: default outputs, the maintainer's review)."""
        run_id = self._reaudit_run_id
        self._service.reaudit(f"reaudit-{run_id}")
        self.post_message(self.ReauditDone(run_id))

    def _reload_snapshot(self) -> None:
        """Bump the run id and reload both panes through the worker."""
        self._snapshot_run_id += 1
        self._load_snapshot()

    # ===== Message handlers (event-loop side: render only) =====

    def on_data_manager_screen_snapshot_loaded(
            self, message: SnapshotLoaded) -> None:
        """Both panes compose from the snapshot (the loading clears)."""
        if message.run_id != self._snapshot_run_id:
            return  # a superseded reload's late post (WR-02)
        self._snapshot = message.snapshot
        self._queue_entries = message.entries
        self._render_presence_summary()
        self._render_load_diagnostic()
        self._render_missing()
        self._render_queue()

    def on_data_manager_screen_zenodo_probed(
            self, message: ZenodoProbed) -> None:
        """The Zenodo line flips to its terminal probe state (D-12)."""
        if message.run_id != self._probe_run_id:
            return  # a superseded probe's late post (WR-02)
        self._zenodo_state = message.state
        self._zenodo_probed_at = message.probed_at
        self._render_zenodo_line()

    def on_data_manager_screen_reaudit_done(
            self, message: ReauditDone) -> None:
        """The re-audit finished: refresh both panes (the refreshed
        baseline re-derives the missing set and the presence view)."""
        if message.run_id != self._reaudit_run_id:
            return  # a superseded re-audit's late post (WR-02)
        self._reload_snapshot()

    # ===== The app-forwarded queue events (persisted-state-as-truth) =====

    def apply_queue_event(self, event: QueueEvent) -> None:
        """One completed task: refresh its row from the queue's truth.

        Re-reads the entries (never trusts the event payload for row
        state — T-10-04-01) and re-renders the table + banners; a done
        event additionally reloads the missing list (the D-11 flip
        moment: the reconciled key left the missing set).
        """
        entries = self._service.entries()
        self._queue_entries = tuple(entries)
        self._live_percents.pop(event.key, None)
        self._render_queue()
        if event.state == "done":
            self._reload_snapshot()

    def apply_queue_progress(self, key: str,
                             percent: "int | None") -> None:
        """One live tick: update the running row's cells in place.

        Re-reads the entry from the service (persisted-state-as-truth,
        T-10-04-01): the cached copy predates the claim, so the FIRST
        tick (the driver's indeterminate claim post) is what flips the
        row from pending to its downloading state. None percent is the
        indeterminate contract — never a fabricated number.
        """
        self._live_percents[key] = percent
        entries = self._service.entries()
        entry = next((item for item in entries if item.key == key), None)
        if entry is None or entry.state != "downloading":
            return
        self._queue_entries = tuple(entries)
        table = self.query_one("#dl-queue", DataTable)
        try:
            table.update_cell(key, "state", self._state_cell(entry))
            table.update_cell(key, "progress", self._progress_cell(entry))
            table.update_cell(key, "reconcile",
                              self._reconcile_cell(entry))
        except Exception:  # noqa: BLE001 — a vanished row mid-rebuild
            return  # the next full render owns the row

    # ===== Rendering (pure UI state mutation over service results) =====

    def _render_presence_summary(self) -> None:
        """The title-line presence summary (blank when n_audit absent)."""
        snapshot = self._snapshot
        if snapshot is None or snapshot.total == 0:
            self.query_one("#dl-presence-summary", Label).update("")
            return
        self.query_one("#dl-presence-summary", Label).update(
            DL_PRESENCE_SUMMARY.format(
                present=snapshot.present, total=snapshot.total,
                missing=snapshot.missing))

    def _render_load_diagnostic(self) -> None:
        """The corrupt-load status line (10-06): the service's verbatim
        quarantine diagnostic when the session carries one, hidden on
        the healthy path — the degradation is surfaced, never a crash,
        never silent loss."""
        line = self.query_one("#dl-load-diagnostic", Label)
        diagnostic = (self._snapshot.load_diagnostic
                      if self._snapshot is not None else None)
        if diagnostic is None:
            line.display = False
            return
        line.update(Text(diagnostic, style=_STYLE_WARN))
        line.display = True

    def _render_missing(self) -> None:
        """The missing pane: one row per MissingInfo, the happy zero."""
        table = self.query_one("#dl-missing", DataTable)
        table.clear()
        snapshot = self._snapshot
        if snapshot is None:
            return  # pre-snapshot emptiness (one worker hop)
        self.query_one("#dl-missing-title", Label).update(
            DL_MISSING_TITLE.format(n=snapshot.missing))
        if not snapshot.rows:
            if snapshot.total:
                # the happy zero (DATA-03's goal state)
                table.add_row(
                    Text(DL_MISSING_EMPTY.format(total=snapshot.total),
                         style=_STYLE_DONE),
                    "", key=_MISSING_EMPTY_ROW_KEY)
            return
        for row in snapshot.rows:
            key_cell = _truncate(Text.assemble(
                Text("✗ ", style=_STYLE_FAIL), Text(row.key),
            ), _TASK_W - _CONTENT_PAD)
            table.add_row(
                key_cell,
                Text(f"{row.declared_total:,}", justify="right"),
                key=row.key)

    def _render_queue(self) -> None:
        """The queue pane: five-state rows, banners, the empty state."""
        table = self.query_one("#dl-queue", DataTable)
        table.clear()
        entries = self._queue_entries
        self.query_one("#dl-queue-title", Label).update(
            QUEUE_TITLE.format(n=len(entries)))
        self._render_banners()
        if not entries:
            table.add_row(
                Text(QUEUE_EMPTY, style=_STYLE_MUTED),
                "", "", "", key=_QUEUE_EMPTY_ROW_KEY)
            return
        for entry in _sorted_entries(entries):
            table.add_row(
                self._task_cell(entry),
                self._state_cell(entry),
                self._progress_cell(entry),
                self._reconcile_cell(entry),
                key=entry.key)

    def _render_banners(self) -> None:
        """One prominent banner per number-carrying mismatch (D-07)."""
        box = self.query_one("#dl-queue-banners", Vertical)
        box.remove_children()
        for entry in self._queue_entries:
            if entry.state != "mismatch":
                continue
            reconcile = entry.reconcile if isinstance(
                entry.reconcile, dict) else {}
            declared = reconcile.get("declared")
            measured = reconcile.get("measured")
            if not (isinstance(declared, dict)
                    and isinstance(measured, dict)):
                continue  # the bundle lane carries per_key, not numbers
            box.mount(Static(
                Text(QUEUE_BANNER_MISMATCH.format(
                    key=entry.key, n=_int_sum(declared),
                    m=_int_sum(measured)),
                    style=_STYLE_WARN),
                classes="queue-banner-mismatch"))

    def _render_zenodo_line(self) -> None:
        """The Zenodo line's four-state render (D-12)."""
        line = self.query_one("#dl-zenodo-line", Label)
        state = self._zenodo_state
        if state is None:
            line.update(Text(DL_ZENODO_PROBING, style=_STYLE_MUTED))
        elif state == zenodo_bundle.PROBE_PUBLIC:
            line.update(Text(DL_ZENODO_PUBLIC, style=_STYLE_DONE))
        elif state == zenodo_bundle.PROBE_NOT_PUBLIC:
            # {HH:MM} is not a legal str.format field (the colon parses
            # as a format spec) — the placeholder fills via replace
            line.update(Text(
                DL_ZENODO_NOT_PUBLIC.replace(
                    "{HH:MM}", self._zenodo_probed_at),
                style=_STYLE_MUTED))
        else:
            line.update(Text(
                DL_ZENODO_FAILED.format(error=_PROBE_ERROR_DETAIL),
                style=_STYLE_WARN))

    def _task_cell(self, entry: QueueEntry) -> Text:
        """The task cell: the key (bundle label for the bundle row) with
        the dim restart note appended on recovered rows (the disabled-
        suffix append idiom — truncation may clip it for long keys; the
        full note rides the drill-down)."""
        display = (DL_BUNDLE_TASK_NAME
                   if entry.kind == KIND_ZENODO_BUNDLE else entry.key)
        segments: list[Text] = [Text(display)]
        if entry.interrupted:
            segments.append(
                Text(" " + QUEUE_RESTART_NOTE, style=_STYLE_RUNNING))
        return _truncate(Text.assemble(*segments),
                         _TASK_W - _CONTENT_PAD)

    @staticmethod
    def _state_cell(entry: QueueEntry) -> Text:
        """The state cell: the glyph-first copy + its style vocabulary."""
        copy, style = _STATE_CELLS.get(
            entry.state, (entry.state, _STYLE_MUTED))
        return Text(copy, style=style)

    def _progress_cell(self, entry: QueueEntry) -> Text:
        """The progress cell (D-03/auto-default 3: never a fabricated
        percent; the bar's filled cells carry the live theme accent —
        the probe-pinned span limitation)."""
        percent = self._live_percents.get(
            entry.key, entry.last_percent)
        if entry.state == "downloading":
            if percent is None:
                return Text(QUEUE_PROGRESS_INDETERMINATE,
                            style=_STYLE_RUNNING)
            filled = max(0, min(10, round(percent / 10)))
            accent = str(self.app.current_theme.accent)
            return Text.assemble(
                Text(f"{percent:>3}%", style=_STYLE_RUNNING),
                Text(" "),
                Text("█" * filled, style=accent),
                Text("·" * (10 - filled), style=_STYLE_RUNNING),
            )
        if entry.state in ("done", "mismatch"):
            return Text("100%", style=_STYLE_RUNNING)
        if entry.state == "failed":
            if percent is None:
                return Text(_DASH, style=_STYLE_RUNNING)
            return Text(f"{percent}%", style=_STYLE_RUNNING)
        return Text(_DASH, style=_STYLE_RUNNING)

    def _reconcile_cell(self, entry: QueueEntry) -> Text:
        """The reconcile cell: pass / running / mismatch / dash."""
        if entry.kind == KIND_ZENODO_BUNDLE:
            # the bundle lane's per-key verdict map rides the drill-down
            # (no declared/measured pair exists for the whole package)
            return Text(_DASH, style=_STYLE_RUNNING)
        reconcile = entry.reconcile if isinstance(
            entry.reconcile, dict) else {}
        measured = reconcile.get("measured")
        if entry.state == "done" and isinstance(measured, dict):
            return Text(
                QUEUE_RECONCILE_PASS.format(n=_int_sum(measured)),
                style=_STYLE_DONE)
        if entry.state == "downloading":
            percent = self._live_percents.get(
                entry.key, entry.last_percent)
            if percent == 100:
                # the post-landing transient (auto-default 14)
                return Text(QUEUE_RECONCILE_RUNNING,
                            style=_STYLE_RUNNING)
        if entry.state == "mismatch":
            declared = reconcile.get("declared")
            if isinstance(declared, dict) and isinstance(measured, dict):
                return Text(
                    QUEUE_RECONCILE_MISMATCH.format(
                        n=_int_sum(declared), m=_int_sum(measured)),
                    style=_STYLE_WARN)
        return Text(_DASH, style=_STYLE_RUNNING)

    # ===== Actions (user intent; toasts are never silent) =====

    def _cursor_row_key(self, table_id: str) -> "str | None":
        """The cursor row's key (None on state rows / empty tables)."""
        table = self.query_one(table_id, DataTable)
        if not table.is_valid_coordinate(table.cursor_coordinate):
            return None  # coordinate_to_cell_key RAISES on invalid (CR-03)
        return str(table.coordinate_to_cell_key(
            table.cursor_coordinate)[0].value)

    def _missing_cursor_key(self) -> "str | None":
        """The missing-table cursor key (state rows never act)."""
        key = self._cursor_row_key("#dl-missing")
        if key is None or self._snapshot is None:
            return None
        return key if any(row.key == key
                          for row in self._snapshot.rows) else None

    def _queue_cursor_entry(self) -> "QueueEntry | None":
        """The queue-table cursor entry (state rows never act)."""
        key = self._cursor_row_key("#dl-queue")
        if key is None:
            return None
        return next((entry for entry in self._queue_entries
                     if entry.key == key), None)

    def _toast_enqueue_outcome(self, outcome: EnqueueOutcome) -> bool:
        """Render one enqueue outcome; True iff the kick should follow."""
        if outcome.action == "enqueued":
            self.app.notify(
                QUEUE_TOAST_ENQUEUED.format(key=outcome.key))
            return True
        if outcome.action == "already_queued":
            self.app.notify(
                QUEUE_TOAST_ALREADY_QUEUED.format(key=outcome.key))
        elif outcome.action == "disabled":
            self.app.notify(
                DL_DISABLED_TOAST.format(key=outcome.key),
                severity="warning")
        elif outcome.action == "unknown":
            self.app.notify(
                DL_UNKNOWN_TOAST.format(
                    key=outcome.key,
                    reason=outcome.reason_code or "unknown"),
                severity="warning")
        elif outcome.action == "cli_unavailable":
            self.app.notify(QUEUE_CLI_UNAVAILABLE, severity="error")
        elif outcome.action == "persist_failed":
            self.app.notify(
                QUEUE_PERSIST_FAILED_TOAST.format(key=outcome.key),
                severity="error")
        return False

    def action_enqueue_cursor(self) -> None:
        """d: enqueue the missing-table cursor row's dataset key."""
        key = self._missing_cursor_key()
        if key is None:
            return  # state rows / no rows: silent (the selection rule)
        outcome = self._service.enqueue(key)
        if self._toast_enqueue_outcome(outcome):
            self.app.kick_download_queue()
            self._reload_snapshot()

    def action_enqueue_all(self) -> None:
        """a: enqueue every missing downloadable key (the count toast)."""
        count = self._service.enqueue_all()
        self.app.notify(QUEUE_TOAST_ENQUEUED_ALL.format(n=count))
        if count:
            self.app.kick_download_queue()
            self._reload_snapshot()

    def action_retry_cursor(self) -> None:
        """r: re-queue the queue cursor's failed/mismatch entry."""
        entry = self._queue_cursor_entry()
        if entry is None:
            return  # state rows: silent
        if entry.state not in ("failed", "mismatch"):
            self.app.notify(QUEUE_RETRY_NOOP)
            return
        if self._service.retry(entry.key):
            self.app.kick_download_queue()
            self._reload_snapshot()

    def action_cancel_cursor(self) -> None:
        """x: cancel the queue cursor's entry — ALWAYS behind the
        ConfirmModal (the destructive list; the copy names the resume
        retention for downloading rows, D-06)."""
        entry = self._queue_cursor_entry()
        if entry is None:
            return  # state rows: silent
        if entry.state == "pending":
            message = QUEUE_CONFIRM_CANCEL_PENDING.format(key=entry.key)
        elif entry.state == "downloading":
            message = QUEUE_CONFIRM_CANCEL_DOWNLOADING.format(
                key=entry.key)
        else:
            self.app.notify(QUEUE_CANCEL_NOOP)
            return
        if self.app.below_minimum_grid:
            return  # WR-06: no chrome over the guard
        key = entry.key
        self.app.push_screen(ConfirmModal(
            message, on_confirm=lambda: self._do_cancel(key)))

    def _do_cancel(self, key: str) -> None:
        """The confirmed cancel: through the seam, then reload."""
        self._service.cancel(key)
        self._reload_snapshot()

    def action_reaudit_cursor(self) -> None:
        """g: rerun the audit for the mismatch cursor row (D-10/R-03)
        in the exclusive worker — the audit subprocess never touches the
        event loop (SC5); the outcome refreshes both panes."""
        entry = self._queue_cursor_entry()
        if entry is None or entry.state != "mismatch":
            return  # the binding is live on mismatch rows only
        self._reaudit_run_id += 1
        self._run_reaudit()

    def action_zenodo_bundle(self) -> None:
        """z: enqueue the whole-package bundle when public; otherwise
        the never-silent explanatory toast (D-12)."""
        if self._zenodo_state != zenodo_bundle.PROBE_PUBLIC:
            self.app.notify(DL_ZENODO_DISABLED_TOAST)
            return
        outcome = self._service.enqueue_zenodo()
        if outcome.action == "enqueued":
            # the toast carries the operator-facing bundle label (the
            # queue identity is the raw record key — detail data)
            self.app.notify(
                QUEUE_TOAST_ENQUEUED.format(key=DL_BUNDLE_TASK_NAME))
            self.app.kick_download_queue()
            self._reload_snapshot()
        else:
            self.app.notify(
                QUEUE_TOAST_ALREADY_QUEUED.format(key=DL_BUNDLE_TASK_NAME))

    # ===== The drill-down (D-03: data, never translated, never elided) =====

    def action_show_detail(self) -> None:
        """enter (table unfocused edge): drill into the focused table."""
        self._open_detail_for_focused()

    def on_data_table_row_selected(self, event: DataTable.RowSelected
                                   ) -> None:
        """enter on the focused table: its native select event."""
        self._open_detail_for_focused()

    def _open_detail_for_focused(self) -> None:
        """Route enter to the focused table's cursor row detail."""
        queue_table = self.query_one("#dl-queue", DataTable)
        if self.focused is queue_table:
            entry = self._queue_cursor_entry()
            if entry is not None:
                self._open_detail(entry.key)
            return
        key = self._missing_cursor_key()
        if key is not None:
            self._open_detail(key)

    def _open_detail(self, key: str) -> None:
        """Compose and push the drill-down modal for one key."""
        if self.app.below_minimum_grid:
            return  # WR-06: no chrome over the guard
        detail = self._service.channel_detail(key)
        entry = next((item for item in self._queue_entries
                      if item.key == key), None)
        lines: list[str] = [f"key: {key}"]
        lines.append(
            "download_url: " + (detail.source_url or "-"))
        lines.append(
            "argv: " + (" ".join(detail.argv)
                        if detail.argv else "-"))
        if detail.reason_code:
            lines.append(f"channel: {detail.channel} ({detail.reason_code})")
        if entry is not None:
            lines.append(f"state: {entry.state}")
            lines.append(f"attempts: {entry.attempts}")
            if entry.last_percent is not None:
                lines.append(f"last_percent: {entry.last_percent}")
            if entry.interrupted:
                lines.append(QUEUE_RESTART_NOTE)
            if entry.problems:
                lines.append("problems: " + ", ".join(entry.problems))
            reconcile = entry.reconcile if isinstance(
                entry.reconcile, dict) else None
            if reconcile is not None:
                per_key = reconcile.get("per_key")
                if isinstance(per_key, dict):
                    for one_key, verdict in per_key.items():
                        lines.append(f"reconcile: {one_key}: {verdict}")
                else:
                    for field in ("verdict", "declared", "measured",
                                  "unified_eval_n"):
                        if field in reconcile:
                            lines.append(
                                f"reconcile: {field}: {reconcile[field]}")
        log_lines = self._service.read_log(key)
        if log_lines:
            lines.append("")
            lines.extend(log_lines)
        self.app.push_screen(QueueDetailModal(key, tuple(lines)))
