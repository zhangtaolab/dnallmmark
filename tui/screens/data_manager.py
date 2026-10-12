"""
data_manager — the slot-3 数据管理 screen (Phase 10, 10-04;
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
- D-15: the bottom bar is d 入队 / r 重试 / x 取消 / a 全部入队 /
  enter 详情 (declaration order) + the constant ``?`` ``q`` right
  segment; ``g`` (re-audit, mismatch rows) and ``z`` (Zenodo) are
  show=False bindings (auto-defaults 7 and the D-12 entry).
- D-07/D-09: mismatch entries render one prominent banner row each
  directly under the queue title AND sort to the top of the queue table
  (with failed rows); presence never flips on mismatch (the service's
  done gate owns that upstream, D-11).
- D-03: the drill-down renders data, never translated, never elided —
  the full key, the registry ``download_url`` (the only download
  authority, D-01/SC1), the composed LIST argv, the reconcile numbers,
  and the verbatim CLI/audit log lines through the Backend read seam.
- WR-06: every async chrome push (drill-down, cancel confirm) checks
  ``app.below_minimum_grid`` first — no modal may open over the guard.
- I18N-01: zero Chinese literals in this module — every operator-facing
  string renders through ``tui/strings.py`` constants (grep-enforced);
  dataset keys, URLs, argv, machine codes, and file paths stay English
  verbatim (data, never copy).
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Protocol

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Label

from tui.screens.nav import BottomBar, TopMenuBar
from tui.services import download_queue, registries, settings, zenodo_bundle
from tui.services.download_queue import (
    EnqueueOutcome,
    MissingInfo,
    QueueEntry,
    ReauditOutcome,
)
from tui.strings import (
    DL_CANCEL_LABEL,
    DL_ENQUEUE_ALL_LABEL,
    DL_ENQUEUE_LABEL,
    DL_MISSING_COL_KEY,
    DL_MISSING_COL_ROWS,
    DL_MISSING_TITLE,
    DL_RETRY_LABEL,
    DL_SCREEN_TITLE,
    DL_ZENODO_KEY_LABEL,
    DL_ZENODO_PROBING,
    ENV_DETAIL_LABEL,
    NAV_LABEL_ABOUT,
    NAV_LABEL_DATA,
    NAV_LABEL_ENV,
    NAV_LABEL_MONITOR,
    NAV_LABEL_RUN_CONFIG,
    NAV_LABEL_SELECTION,
    QUEUE_COL_PROGRESS,
    QUEUE_COL_RECONCILE,
    QUEUE_COL_STATE,
    QUEUE_COL_TASK,
    QUEUE_REAUDIT_LABEL,
    QUEUE_TITLE,
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


@dataclass(frozen=True)
class MissingSnapshot:
    """The missing-list read result (pure service data; the screen renders).

    Attributes:
        rows: one ``MissingInfo`` per missing official key (registry order).
        total: the audited dataset count (the committed n_audit view).
        present: the present count over the same view.
    """

    rows: "tuple[MissingInfo, ...]"
    total: int
    present: int

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
                (``missing_datasets``/``entries``/``enqueue``/
                ``enqueue_all_missing``/``enqueue_zenodo``/``retry``/
                ``cancel``/``reaudit_baseline``/``resolve_channel``, with
                ``probe_zenodo`` optional via the getattr guard).
        """
        self._queue: Any = (queue if queue is not None
                            else download_queue.DownloadQueueService())

    def missing_snapshot(self) -> MissingSnapshot:
        """The missing rows + the presence summary (the registries view).

        The presence counts derive from the committed n_audit view
        through the unchanged ``registries.presence_for`` (the same
        loop shape ``SelectionBackend.load_selection_data`` runs); an
        absent n_audit yields zero rows and a zero denominator — the
        missing set is unknowable, not "everything" (the service rule).
        """
        rows = self._queue.missing_datasets()
        audit = registries.load_n_audit()
        if audit is None:
            return MissingSnapshot(
                rows=tuple(rows), total=0, present=0)
        present = sum(
            1 for key in audit
            if registries.presence_for(key, audit).status
            == registries.PRESENCE_PRESENT
        )
        return MissingSnapshot(
            rows=tuple(rows), total=len(audit), present=present)

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
        injected fakes stay deterministic), else the real frozen-URL GET."""
        queue_probe = getattr(self._queue, "probe_zenodo", None)
        if queue_probe is not None:
            return str(queue_probe())
        return zenodo_bundle.probe_zenodo_public()

    def channel_detail(self, key: str) -> ChannelDetail:
        """The drill-down channel data (registry authority + LIST argv)."""
        if key == download_queue.ZENODO_BUNDLE_KEY:
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

    def __init__(self,
                 data_service: "DataManagerServiceProtocol | None" = None,
                 **kwargs):
        super().__init__(**kwargs)
        self._service: DataManagerServiceProtocol = (
            data_service if data_service is not None
            else DataManagerBackend()
        )

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
        """Build the two empty tables and focus the missing list."""
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
