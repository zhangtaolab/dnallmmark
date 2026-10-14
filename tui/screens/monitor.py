"""
monitor — the slot-5 monitor screen (Phase 11, 11-07; menu slot 5).

The operator's monitoring surface over the 11-04 pure scanner: the
discovered-sweeps pane (three D-03 states, progress + ETA per D-17), the
per-(model, task) cell table with seed columns and the five glyph states
(incl. the ⊘ resume provenance), the stats line, the [f] failures modal
with the gated from-failures re-run (D-11), the [t] tee log tail
(D-10/MON-04), the [a] manual-root attach, and the [r] immediate rescan.

Contract (locked decisions):

- PRESENTATION ONLY (the ``tui/screens/`` tier contract): the screen
  derives NOTHING from the artifact tree itself — every scan, stat,
  failure list, and tail read goes through the injected
  ``MonitorServiceProtocol`` (the plan's rendering prohibition). The
  screen owns only cadence, focus, and rendering.
- D-09 cadence: ``set_interval(2s)`` dispatches the frontier worker and
  ``set_interval(60s)`` the full-scan worker — a tick NEVER scans
  inline; each tick bumps its run id, dispatches an
  ``@work(exclusive=True, thread=True, group=...)`` worker in its OWN
  group (the data_manager group-discipline note: exclusivity cancels by
  (node, group), so the two cadences must never share one), and posts a
  run-id-tagged message whose handler drops superseded posts (WR-02).
- Honesty over motion (the phase-10 progress rule): unknown totals,
  pending ETAs, absent elapsed, and the no-tee log state are DESIGNED
  renderings via the frozen MON_ constants — never fabricated numbers
  and never errors.
- WR-06: every async modal push checks ``app.below_minimum_grid``.

I18N-01: zero Chinese literals in this module — every operator-facing
string renders through ``tui/strings.py`` constants (grep-enforced);
roots, model/task keys, record fields, argv, and paths stay data,
verbatim.
"""

import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Protocol

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen, Screen
from textual.widgets import DataTable, Footer, Label, RichLog

from tui.screens.nav import BottomBar, TopMenuBar
from tui.screens.selection import ConfirmModal, PathInputModal
from tui.services import run_config as run_config_svc
from tui.services import sweep_launcher as sweep_launcher_module
from tui.services import sweep_monitor
from tui.services.sweep_monitor import (
    CELL_COMPLETED,
    CELL_FAILED,
    CELL_QUEUED,
    CELL_RUNNING,
    CELL_SKIPPED,
    ETA_PENDING,
    ETA_POINT,
    ETA_RANGE,
    SWEEP_ARTIFACTS_ONLY,
    SWEEP_FINISHED,
    SWEEP_RUNNING,
    format_eta,
    format_hms,
)
from tui.strings import (
    APP_MODAL_BACK_LABEL,
    CFG_VALUE_ABSENT,
    ENV_DETAIL_LABEL,
    LNC_LAUNCH_FAILED_TOAST,
    MON_ATTACH_INVALID_TOAST,
    MON_ATTACH_LABEL,
    MON_ATTACH_PLACEHOLDER,
    MON_ATTACH_TITLE,
    MON_ATTACHED_TOAST,
    MON_CELLS_EMPTY,
    MON_CELLS_TITLE,
    MON_COL_ETA,
    MON_COL_MODEL,
    MON_COL_PROGRESS,
    MON_COL_ROOT,
    MON_COL_SCALE,
    MON_COL_SEED,
    MON_COL_TASK,
    MON_DISCOVERED_EMPTY,
    MON_DISCOVERED_TITLE,
    MON_ETA_PENDING,
    MON_ETA_RANGE,
    MON_ETA_UNKNOWN,
    MON_FAILURE_ROW,
    MON_FAILURES_EMPTY,
    MON_FAILURES_TITLE,
    MON_FRACTION_LINE,
    MON_LOG_TEE_LINE,
    MON_LOG_TITLE,
    MON_LOG_UNAVAILABLE,
    MON_RERUN_CONFIRM,
    MON_RERUN_LABEL,
    MON_RERUN_TOAST,
    MON_RESCAN_LABEL,
    MON_RESCAN_TOAST,
    MON_RESUME_NOTE,
    MON_RESUME_NOTE_SHORT,
    MON_SCAN_NOTE,
    MON_SCREEN_TITLE,
    MON_STATE_ARTIFACTS_SWEEP,
    MON_STATE_DONE,
    MON_STATE_FAILED,
    MON_STATE_FINISHED_SWEEP,
    MON_STATE_QUEUED,
    MON_STATE_RUNNING,
    MON_STATE_RUNNING_SWEEP,
    MON_STATE_SKIPPED,
    MON_STATS_LINE,
    MON_STATS_LINE_NO_CURRENT,
    MON_STATS_LINE_UNKNOWN_TOTAL,
    MON_TOTAL_UNKNOWN,
    NAV_LABEL_ABOUT,
    NAV_LABEL_DATA,
    NAV_LABEL_ENV,
    NAV_LABEL_MONITOR,
    NAV_LABEL_RUN_CONFIG,
    NAV_LABEL_SELECTION,
)

if TYPE_CHECKING:
    from textual import getters

    from tui.app import DnallmMarkTui

#: The 80-col width threshold (the UI-SPEC responsive rules: the scale
#: column drops and the stats line drops the current segment below).
_NARROW_WIDTH = 100

#: The cadence intervals (D-09): 2s frontier + 60s full. Injectable so
#: Pilot tests drive the tick callbacks directly (never real sleeps).
FRONTIER_INTERVAL_SECONDS = 2.0
FULL_INTERVAL_SECONDS = 60.0

_STYLE_DIM = "$text-muted"
_STYLE_RUNNING = "dim"
_STYLE_DONE = "$success"
_STYLE_FAILED = "$error"
_STYLE_SKIPPED = "dim"

#: Keycap labels for the [f]/[t] bindings, projected from their landed
#: modal-title constants (the 11-06 keycap-budget precedent: no
#: standalone 4-CJK-char constants exist in the frozen inventory and
#: additions are tripwire-locked; the projection adds zero copy).
_FAILURES_KEYCAP = MON_FAILURES_TITLE.split(" (")[0]
_LOG_KEYCAP = MON_LOG_TITLE.split(" — {")[0]

#: The discovered-sweep state cell vocabulary (machine state -> the
#: glyph-first copy + its style channel).
_SWEEP_STATE_CELLS: "dict[str, tuple[str, str]]" = {
    SWEEP_RUNNING: (MON_STATE_RUNNING_SWEEP, _STYLE_RUNNING),
    SWEEP_FINISHED: (MON_STATE_FINISHED_SWEEP, _STYLE_DIM),
    SWEEP_ARTIFACTS_ONLY: (MON_STATE_ARTIFACTS_SWEEP, _STYLE_DIM),
}

#: The per-seed cell-state vocabulary (machine state -> copy + style).
_CELL_STATE_CELLS: "dict[str, tuple[str, str]]" = {
    CELL_COMPLETED: (MON_STATE_DONE, _STYLE_DONE),
    CELL_FAILED: (MON_STATE_FAILED, _STYLE_FAILED),
    CELL_SKIPPED: (MON_STATE_SKIPPED, _STYLE_SKIPPED),
    CELL_RUNNING: (MON_STATE_RUNNING, _STYLE_RUNNING),
    CELL_QUEUED: (MON_STATE_QUEUED, _STYLE_DIM),
}


def _glyph_of(copy: str) -> str:
    """The glyph token of one glyph-first constant (glyph + word)."""
    return copy.split(" ", 1)[0]


def _eta_field(eta: Any) -> str:
    """The stats-line ETA field: the numeric forms render without the
    leading ≈ (the frozen line constant carries its own ≈); the pending
    and none degradations render their designed constants (the caller
    drops the line's stray ≈ for them — never a double marker)."""
    if eta.mode == ETA_PENDING:
        return MON_ETA_PENDING
    if eta.mode == ETA_RANGE:
        return MON_ETA_RANGE.format(
            lo=format_eta(eta.lo_seconds).lstrip("≈"),
            hi=format_eta(eta.hi_seconds).lstrip("≈"))
    if eta.mode == ETA_POINT:
        return format_eta(eta.point_seconds).lstrip("≈")
    return MON_ETA_UNKNOWN


def _stats_line(stats: Any, narrow: bool) -> str:
    """The MON-02/D-17 stats line over one SweepStats (all variants)."""
    elapsed = (
        format_hms(stats.elapsed_seconds)
        if stats.elapsed_seconds is not None else MON_ETA_UNKNOWN)
    if stats.total is None:
        return MON_STATS_LINE_UNKNOWN_TOTAL.format(
            done=stats.done, elapsed=elapsed)
    eta_field = _eta_field(stats.eta)
    if narrow or stats.current is None:
        line = MON_STATS_LINE_NO_CURRENT.format(
            done=stats.done, total=stats.total,
            elapsed=elapsed, eta=eta_field)
    else:
        line = MON_STATS_LINE.format(
            done=stats.done, total=stats.total,
            model=stats.current.model, task=stats.current.task,
            seed=stats.current.seed, elapsed=elapsed, eta=eta_field)
    if eta_field in (MON_ETA_PENDING, MON_ETA_UNKNOWN):
        # the degradation copy never rides the ≈ prefix
        line = line.replace("≈" + eta_field, eta_field)
    return line


def _progress_cell(summary: Any) -> Text:
    """The discovered-row progress cell: the phase-10 grammar verbatim
    (``{done}/{total}`` + the 10-cell bar on running rows; the bar is
    additive, never fabricated; unknown totals render the designed
    copy)."""
    if summary.total is None:
        return Text(MON_TOTAL_UNKNOWN, style=_STYLE_DIM)
    fraction = Text(f"{summary.done}/{summary.total}")
    if summary.state != SWEEP_RUNNING:
        return fraction
    filled = max(0, min(10, round(summary.done / summary.total * 10)))
    return Text.assemble(
        fraction, Text(" "), Text("█" * filled),
        Text("·" * (10 - filled), style=_STYLE_RUNNING))


def _discovered_eta_cell(summary: Any, stats: Any | None) -> Text:
    """The discovered-row ETA cell: running rows render the D-17 ETA
    (point/range/pending); finished and prior-artifacts rows render the
    absent marker."""
    if summary.state != SWEEP_RUNNING or stats is None:
        return Text(MON_ETA_UNKNOWN, style=_STYLE_DIM)
    eta = stats.eta
    if eta.mode == ETA_PENDING:
        return Text(MON_ETA_PENDING, style=_STYLE_DIM)
    if eta.mode == ETA_RANGE:
        return Text("≈" + MON_ETA_RANGE.format(
            lo=format_eta(eta.lo_seconds).lstrip("≈"),
            hi=format_eta(eta.hi_seconds).lstrip("≈")))
    if eta.mode == ETA_POINT:
        return Text(format_eta(eta.point_seconds))
    return Text(MON_ETA_UNKNOWN, style=_STYLE_DIM)


def _seed_cell(seed: Any, wide: bool) -> Text:
    """One seed column cell: the glyph (+ word where the cell is wide);
    a curve seed renders the folded glyph + the fraction mini-counts; an
    unrecognized record status renders verbatim (honest)."""
    copy, style = _CELL_STATE_CELLS.get(
        seed.state, (seed.state, _STYLE_DIM))
    if seed.fraction_states is not None:
        done = sum(
            1 for _name, state in seed.fraction_states
            if state in (CELL_COMPLETED, CELL_SKIPPED))
        return Text(
            f"{_glyph_of(copy)} {done}/{len(seed.fraction_states)}",
            style=style)
    if wide:
        return Text(copy, style=style)
    return Text(_glyph_of(copy), style=style)


# =====================================================================
# Service Protocols + the real Backend (the constructor-injection seam)
# =====================================================================


class MonitorServiceProtocol(Protocol):
    """The monitor-service surface the screen consumes (11-04 + the
    launcher's live-root/tee seams, adapted).

    The real ``MonitorBackend`` and the tier-2 Pilot fakes both conform
    structurally — no artifact-tree read ever executes in a faked Pilot
    run (the plan's rendering prohibition).
    """

    def full_scan(self, prev_watermarks: "dict | None" = None) -> Any:
        """The 60s full scan: roots -> ScanResult (D-03)."""

    def frontier_scan(self, root) -> Any:
        """The 2s light pass over one root (D-09)."""

    def cells_view(self, root) -> Any:
        """The per-(model, task) cell rows with per-seed states."""

    def stats(self, root, expected_total: "int | None" = None,
              fallback_start: "float | None" = None) -> Any:
        """The stats line data (MON-02/D-17); the launch-injection
        seams thread the TUI-launched plan."""

    def sweep_scale(self, root) -> "tuple[int, int, int] | None":
        """The manifest scale ({models}x{tasks}x{seeds}), None unknown."""

    def resume_count(self, root) -> int:
        """Cells skipped this run by the resume marker (MON-05)."""

    def failures_view(self, root) -> Any:
        """The failure list (live records / the end-of-sweep file)."""

    def rerun_lane(self, root) -> "tuple[str, str]":
        """The (peft, config_variant) lane the [r] re-run must carry
        (WR-01 — recovered from the source sweep's own artifacts)."""

    def cell_record(self, root, model: str, task: str,
                    seed: int) -> "dict | None":
        """One cell's run_record fields verbatim (None when absent) —
        the detail modal's data source."""

    def read_log_tail(self, path,
                      max_lines: int = 200,
                      max_bytes: int = 65536) -> Any:
        """The bounded tail (None = no/unreadable log)."""

    def is_sweep_root(self, path) -> bool:
        """The [a] attach-validation predicate (D-03)."""

    def add_manual_root(self, path) -> bool:
        """Persist a validated manual root (refuses invalid)."""


class MonitorLauncherProtocol(Protocol):
    """The launcher surface the monitor screen consumes ([r] re-run)."""

    def env_preflight(self, kernels: Any = None) -> Any:
        """The D-08 preflight (the re-run re-enters the same gate)."""

    def launch_from_failures(self, failures_path, seeds, output_root,
                             peft: str = "none",
                             config_variant: str = "none",
                             phrase: "str | None" = None) -> Any:
        """The D-11 from-failures launch through the shared pipeline
        (CR-01-gated: an E2'-class effective matrix refuses at the
        phrase stage until the typed phrase is threaded)."""

    def phrase_matches(self, typed: str, output_root: str) -> bool:
        """The exact-match E2' phrase verdict (the re-prompt's live
        indicator — the widget holds no matching logic)."""

    def live_sweeps(self) -> tuple:
        """The live roots (the attach-alive signal)."""

    def tee_path_for(self, root) -> "str | None":
        """One live root's tee path (None = CLI-launched)."""


class MonitorBackend:
    """The real monitor adapter: delegation glue over the 11-04 scanner
    with the app-owned launcher's live roots injected into every scan
    (the Popen-alive running signal), plus the manifest scale read.

    The semantics stay in the tested ``sweep_monitor`` service; this
    adapter owns only the launcher seam (live roots + tee path) and the
    scale projection over the manifest cells.
    """

    def __init__(self, launcher: Any = None):
        self._launcher = launcher

    def _live_roots(self) -> tuple:
        if self._launcher is None:
            return ()
        return tuple(self._launcher.live_sweeps())

    def full_scan(self, prev_watermarks: "dict | None" = None) -> Any:
        return sweep_monitor.full_scan(
            live_roots=self._live_roots(),
            prev_watermarks=prev_watermarks)

    def frontier_scan(self, root) -> Any:
        return sweep_monitor.frontier_scan(
            root, live_roots=self._live_roots())

    def cells_view(self, root) -> Any:
        return sweep_monitor.cells_view(root)

    def stats(self, root, expected_total: "int | None" = None,
              fallback_start: "float | None" = None) -> Any:
        return sweep_monitor.stats(
            root, expected_total=expected_total,
            fallback_start=fallback_start)

    def sweep_scale(self, root) -> "tuple[int, int, int] | None":
        """The manifest's {models} x {tasks} x {seeds} (None when no
        readable manifest — the honest unknown, never a derived guess
        over discovered artifacts)."""
        manifest = sweep_monitor.load_manifest(
            Path(root) / sweep_monitor.MANIFEST_NAME)
        if not isinstance(manifest, dict):
            return None
        cells = manifest.get("cells")
        if not isinstance(cells, list) or not cells:
            return None
        models: set[str] = set()
        tasks: set[str] = set()
        seeds: set[int] = set()
        for cell in cells:
            if not isinstance(cell, dict):
                continue
            if isinstance(cell.get("model"), str):
                models.add(cell["model"])
            if isinstance(cell.get("task"), str):
                tasks.add(cell["task"])
            if isinstance(cell.get("seed"), int):
                seeds.add(cell["seed"])
        if not models or not tasks or not seeds:
            return None
        return (len(models), len(tasks), len(seeds))

    def resume_count(self, root) -> int:
        return sweep_monitor.resume_count(root)

    def failures_view(self, root) -> Any:
        return sweep_monitor.failures_view(root)

    def rerun_lane(self, root) -> "tuple[str, str]":
        """WR-01: the source sweep's lane, recovered from its artifacts
        (the worker-side read for the [r] re-run)."""
        return sweep_monitor.rerun_lane(root)

    def cell_record(self, root, model: str, task: str,
                    seed: int) -> "dict | None":
        """The seed dir's run_record via the tolerant reader (the
        last-known-good contract; None when absent)."""
        return sweep_monitor.load_record(
            Path(root) / model / task / f"seed_{seed}"
            / sweep_monitor.RECORD_NAME)

    def read_log_tail(self, path,
                      max_lines: int = 200,
                      max_bytes: int = 65536) -> Any:
        return sweep_monitor.read_log_tail(
            path, max_lines=max_lines, max_bytes=max_bytes)

    def is_sweep_root(self, path) -> bool:
        return sweep_monitor.is_sweep_root(path)

    def add_manual_root(self, path) -> bool:
        return sweep_monitor.add_manual_root(path)

    # ----- the launcher face (the [r] re-run seam; the real path
    # receives the app-owned shared launcher, whose methods these
    # delegate to — the adapter satisfies BOTH protocols) -----

    def env_preflight(self, kernels=None) -> Any:
        return sweep_launcher_module.env_preflight(kernels)

    def launch_from_failures(self, failures_path, seeds, output_root,
                             peft="none", config_variant="none",
                             phrase=None) -> Any:
        if self._launcher is None:
            return None
        return self._launcher.launch_from_failures(
            failures_path, seeds, output_root,
            peft=peft, config_variant=config_variant, phrase=phrase)

    def phrase_matches(self, typed, output_root) -> bool:
        """The exact-match verdict over the REAL service tier (the
        E2' re-prompt's live indicator — run_config owns the check,
        never the widget)."""
        return run_config_svc.phrase_matches(typed, output_root)

    def live_sweeps(self) -> tuple:
        return self._live_roots()

    def tee_path_for(self, root) -> "str | None":
        if self._launcher is None:
            return None
        return self._launcher.tee_path_for(root)


# =====================================================================
# Modals ([f] failures + drill, [t] log tail, cell detail)
# =====================================================================


class FailureDetailModal(ModalScreen):
    """The [f] enter drill-down: the verbatim error string, wrapped,
    never elided (data discipline)."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, title: str, error: str, **kwargs):
        super().__init__(**kwargs)
        self._title = title
        self._error = error

    def compose(self) -> ComposeResult:
        with Vertical(id="mon-faildetail-box", classes="modal-box"):
            yield RichLog(wrap=True, id="mon-faildetail-log")
            yield Footer()

    def on_mount(self) -> None:
        box = self.query_one("#mon-faildetail-box", Vertical)
        box.border_title = self._title
        log = self.query_one("#mon-faildetail-log", RichLog)
        log.write(self._error)


class FailuresModal(ModalScreen):
    """The [f] failures modal: one row per failure, enter drills the
    verbatim error, and the destructive re-run sits behind its own
    confirm (the only destructive key on this screen)."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "drill_cursor", show=False),
        Binding("r", "rerun_failures", MON_RERUN_LABEL),
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, root: str, failures: tuple,
                 monitor: "MonitorScreen", **kwargs):
        super().__init__(**kwargs)
        self._root = root
        self._failures = tuple(failures)
        # the owning monitor screen (a modal's ``self.screen`` is the
        # modal itself — the parent must be passed, never looked up)
        self._monitor = monitor

    def compose(self) -> ComposeResult:
        with Vertical(id="mon-failures-box", classes="modal-box"):
            yield DataTable(id="mon-failures-table")
            yield Footer()

    def on_mount(self) -> None:
        box = self.query_one("#mon-failures-box", Vertical)
        box.border_title = MON_FAILURES_TITLE.format(n=len(self._failures))
        table = self.query_one("#mon-failures-table", DataTable)
        table.cursor_type = "row"
        table.add_column(MON_FAILURE_ROW.format(
            model="model", task="task", seed="seed"), key="model")
        if not self._failures:
            table.add_row(MON_FAILURES_EMPTY, key="__empty__")
        else:
            for index, failure in enumerate(self._failures):
                table.add_row(MON_FAILURE_ROW.format(
                    model=failure.model, task=failure.task,
                    seed=failure.seed), key=f"failure-{index}")
        table.focus()

    def on_data_table_row_selected(
            self, event: DataTable.RowSelected) -> None:
        """enter on the focused table (its native select event — the
        table consumes the key, the modal binding never fires)."""
        self.action_drill_cursor()

    def action_drill_cursor(self) -> None:
        """enter: the selected failure's verbatim error (never elided)."""
        if not self._failures:
            return
        table = self.query_one("#mon-failures-table", DataTable)
        row = table.coordinate_to_cell_key(
            table.cursor_coordinate)[0].value
        try:
            index = int(str(row).rsplit("-", 1)[1])
            failure = self._failures[index]
        except (ValueError, IndexError):
            return
        self.app.push_screen(FailureDetailModal(
            MON_FAILURE_ROW.format(model=failure.model, task=failure.task,
                                   seed=failure.seed),
            failure.error))

    def action_rerun_failures(self) -> None:
        """[r]: the independent re-run confirm (never unconfirmed —
        this is a real GPU spend), routed through the monitor screen."""
        if not self._failures:
            return
        self.dismiss()
        self._monitor.request_rerun(self._root, len(self._failures))


class LogTailModal(ModalScreen):
    """The [t] log-tail modal: the bounded RichLog tail of the tee file
    refreshed on the 2s cadence while open; the dim tee line names the
    file (D-10). No tee (a CLI-launched sweep) renders the designed
    unavailable state and schedules NO refresh — never a fabricated
    empty log."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, root: str, tee_path: "str | None", tail_reader,
                 interval: float = FRONTIER_INTERVAL_SECONDS, **kwargs):
        super().__init__(**kwargs)
        self._root = root
        self._tee_path = tee_path
        self._tail_reader = tail_reader
        self._interval = interval
        self._timer = None
        self._refresh_run_id = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="mon-log-box", classes="modal-box"):
            yield RichLog(wrap=True, id="mon-log-tail", max_lines=200)
            yield Label("", id="mon-log-tee-line")
            yield Footer()

    def on_mount(self) -> None:
        box = self.query_one("#mon-log-box", Vertical)
        box.border_title = MON_LOG_TITLE.format(root=self._root)
        if self._tee_path is None:
            log = self.query_one("#mon-log-tail", RichLog)
            log.write(MON_LOG_UNAVAILABLE)
            return  # CLI-launched: no refresh is ever scheduled
        self.query_one("#mon-log-tee-line", Label).update(Text(
            MON_LOG_TEE_LINE.format(path=self._tee_path),
            style=_STYLE_DIM))
        self._refresh_tick()
        self._timer = self.set_interval(self._interval, self._refresh_tick)

    def on_unmount(self) -> None:
        """esc: the tail stops with the modal (no zombie timer)."""
        if self._timer is not None:
            self._timer.stop()

    @work(exclusive=True, thread=True, group="mon-logtail")
    def _refresh_tick(self) -> None:
        """One cadence refresh: the tail read stays off the event loop
        (WR-03-wrapped: a raised read skips this tick — the modal keeps
        its last-good lines, the next tick retries)."""
        if self._tee_path is None:
            return
        try:
            lines = self._tail_reader(self._tee_path)
        except Exception:  # noqa: BLE001 — tolerant refresh
            return
        self._refresh_run_id += 1
        self.post_message(self.TailRead(lines, self._refresh_run_id))

    class TailRead(Message):
        """One tail read arrived (worker thread -> loop)."""

        def __init__(self, lines, run_id: int) -> None:
            self.lines = lines
            self.run_id = run_id
            super().__init__()

    def on_log_tail_modal_tail_read(self, message: TailRead) -> None:
        if message.run_id != self._refresh_run_id:
            return
        log = self.query_one("#mon-log-tail", RichLog)
        log.clear()
        for line in message.lines or ():
            log.write(line)


class CellDetailModal(ModalScreen):
    """The cell-detail drill-down (the RowDetailModal family): full
    model/task keys, every seed's state, per-fraction lines — data,
    never translated, never elided."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, model: str, task: str, row: Any,
                 records: "dict[int, dict] | None" = None, **kwargs):
        super().__init__(**kwargs)
        self._model = model
        # NOTE: ``_task`` is MessagePump's own internal attribute (the
        # pump's asyncio task — clobbered on mount); the field is named
        # ``_task_key`` so the row identity survives.
        self._task_key = task
        self._row = row
        self._records = records or {}

    def compose(self) -> ComposeResult:
        with Vertical(id="mon-celldetail-box", classes="modal-box"):
            yield RichLog(wrap=True, id="mon-celldetail-log")
            yield Footer()

    def on_mount(self) -> None:
        box = self.query_one("#mon-celldetail-box", Vertical)
        box.border_title = f"{self._model} × {self._task_key}"
        log = self.query_one("#mon-celldetail-log", RichLog)
        for seed in self._row.seeds:
            copy, _style = _CELL_STATE_CELLS.get(
                seed.state, (seed.state, _STYLE_DIM))
            log.write(f"{MON_COL_SEED.format(seed=seed.seed)}: {copy}")
            for name, state in seed.fraction_states or ():
                frac_copy, _frac_style = _CELL_STATE_CELLS.get(
                    state, (state, _STYLE_DIM))
                fraction = (name.removeprefix("frac_"))
                log.write("  " + MON_FRACTION_LINE.format(
                    fraction=fraction, state=frac_copy))
            record = self._records.get(seed.seed)
            if record:
                # the run_record fields verbatim (data discipline)
                for field_name, value in record.items():
                    log.write(f"  {field_name}: {value}")


def _set_table_rows(table: DataTable, columns, rows) -> None:
    """WR-05 (phase-11 review): diff-preserving row update — the
    ``PickerList.set_rows`` precedent (tui/screens/run_config.py)
    carried to DataTable.

    Textual 8.2.8's ``DataTable.clear()`` resets ``cursor_coordinate``
    to (0,0) and zeroes scroll, so the clear+rebuild the cadence
    handlers used on every 2s tick made keyboard navigation snap back
    to row 0 continuously — and an ``[enter]`` pressed after a tick
    landed mid-reset, acting on ROW 0 (attaching the wrong sweep root,
    opening the wrong cell detail out of a 2950-row table). Here
    columns rebuild ONLY when their key set changes (the narrow
    toggle, a new seed column); known rows update in place via
    ``update_cell``, new rows append, vanished rows drop; the cursor
    is re-pinned to its ROW KEY (identity, not coordinate) with
    ``scroll=False`` so the operator's view never jumps.

    Args:
        table: the target DataTable.
        columns: ``[(label, key), ...]`` in display order.
        rows: ``{row_key: [cell, ...]}`` in display order (each cell
            list parallel to ``columns``).
    """
    wanted = [key for _label, key in columns]
    current = [str(key.value) for key in table.columns]
    if current != wanted:
        table.clear(columns=True)
        for label, key in columns:
            table.add_column(label, key=key)
    cursor_key = None
    try:
        cursor_key = str(table.coordinate_to_cell_key(
            table.cursor_coordinate)[0].value)
    except Exception:  # noqa: BLE001 — an empty table has no cell key
        cursor_key = None
    existing = {str(key.value) for key in table.rows}
    for row_key in existing - set(rows):
        table.remove_row(row_key)
    for row_key, cells in rows.items():
        if row_key in existing:
            for column_key, value in zip(wanted, cells, strict=True):
                table.update_cell(row_key, column_key, value)
        else:
            table.add_row(*cells, key=row_key)
    if cursor_key is not None and cursor_key in rows:
        try:
            table.move_cursor(
                row=table.get_row_index(cursor_key),
                animate=False, scroll=False)
        except Exception:  # noqa: BLE001 — the row vanished
            return  # mid-diff: the cursor simply stays where it is


# =====================================================================
# The screen
# =====================================================================


class MonitorScreen(Screen):
    """The slot-5 monitor: discovered sweeps + cell table + stats line
    over the 11-04 scanner, with the D-09 worker cadence."""

    # D-13 slot 5 (the top-menu active-slot marker the nav bar reads).
    NAV_SLOT: ClassVar[int] = 5

    if TYPE_CHECKING:
        # Narrows MessagePump's ``App[object]`` to the composition root
        # (the selection-screen idiom — no runtime import of tui.app).
        app = getters.app(DnallmMarkTui)

    # The bottom-bar vocabulary in declaration order (the wireframe
    # order; the clip policy drops least-primary first). The nav digits
    # are plain per-screen bindings routed to the app's nav action
    # (never priority, Pattern 2).
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "row_action", ENV_DETAIL_LABEL),
        Binding("f", "show_failures", _FAILURES_KEYCAP),
        Binding("t", "show_log_tail", _LOG_KEYCAP),
        Binding("a", "attach_path", MON_ATTACH_LABEL),
        Binding("r", "rescan", MON_RESCAN_LABEL),
        Binding("1", "app.nav(1)", NAV_LABEL_ENV, show=False),
        Binding("2", "app.nav(2)", NAV_LABEL_SELECTION, show=False),
        Binding("3", "app.nav(3)", NAV_LABEL_DATA, show=False),
        Binding("4", "app.nav(4)", NAV_LABEL_RUN_CONFIG, show=False),
        Binding("5", "app.nav(5)", NAV_LABEL_MONITOR, show=False),
        Binding("6", "app.nav(6)", NAV_LABEL_ABOUT, show=False),
    ]

    class FullScanned(Message):
        """The 60s full scan arrived (worker thread -> loop; WR-02)."""

        def __init__(self, result: Any, root_stats: dict,
                     cells: Any, resume: int, run_id: int) -> None:
            self.result = result
            self.root_stats = root_stats
            self.cells = cells
            self.resume = resume
            self.run_id = run_id
            super().__init__()

    class FrontierScanned(Message):
        """The 2s frontier pass arrived (worker thread -> loop; WR-02)."""

        def __init__(self, snapshot: Any, stats: Any,
                     run_id: int) -> None:
            self.snapshot = snapshot
            self.stats = stats
            self.run_id = run_id
            super().__init__()

    class FailuresRead(Message):
        """The failure list arrived (worker thread -> loop)."""

        def __init__(self, root: str, failures) -> None:
            self.root = root
            self.failures = tuple(failures or ())
            super().__init__()

    class RerunPreflightDone(Message):
        """The re-run preflight verdict arrived (worker -> loop)."""

        def __init__(self, verdict, root: str, run_id: int) -> None:
            self.verdict = verdict
            self.root = root
            self.run_id = run_id
            super().__init__()

    class RerunFinished(Message):
        """The re-run launch outcome arrived (worker -> loop)."""

        def __init__(self, outcome, root: str, run_id: int) -> None:
            self.outcome = outcome
            self.root = root
            self.run_id = run_id
            super().__init__()

    class RerunFailed(Message):
        """A re-run worker RAISED (WR-03, phase-11 review): surfaced as
        the error toast — a confirm-then-crash re-run is never a silent
        no-op."""

        def __init__(self, error: str, root: str, run_id: int) -> None:
            self.error = error
            self.root = root
            self.run_id = run_id
            super().__init__()

    def __init__(self,
                 monitor_service: "MonitorServiceProtocol | None" = None,
                 launcher_service: "MonitorLauncherProtocol | None" = None,
                 frontier_interval: float = FRONTIER_INTERVAL_SECONDS,
                 full_interval: float = FULL_INTERVAL_SECONDS,
                 **kwargs):
        super().__init__(**kwargs)
        self._service: MonitorServiceProtocol = (
            monitor_service if monitor_service is not None
            else MonitorBackend())
        # the launcher seam defaults to the same backend adapter (the
        # real path receives the app-owned shared launcher)
        self._launcher: MonitorLauncherProtocol = (
            launcher_service if launcher_service is not None
            else MonitorBackend())
        self._frontier_interval = frontier_interval
        self._full_interval = full_interval
        # the scan state (event-loop side only; workers post into it)
        self._scan: Any = None
        self._watermarks: dict[str, float] = {}
        self._root_stats: dict[str, Any] = {}
        self._scales: dict[str, tuple[int, int, int] | None] = {}
        self._cell_rows: dict[str, Any] = {}
        self._ever_discovered: set[str] = set()
        self._resume_count = 0
        self._last_stats: Any = None
        # the attached sweep (None = the cells region's empty state)
        self._attached_root: Path | None = None
        # the D-13 launch injections (expected totals + fallback starts)
        self._expected_totals: dict[str, int] = {}
        self._fallback_starts: dict[str, float] = {}
        # per-worker run ids (WR-02): bumped on every kick so a
        # superseded worker's late post drops
        self._full_run_id = 0
        self._frontier_run_id = 0
        self._rerun_stage_id = 0
        self._pending_rescan = False
        self._frontier_timer = None
        self._full_timer = None
        self._narrow = False

    # ===== compose / mount =====

    def compose(self) -> ComposeResult:
        """The screen frame: nav bars, the title bar (the cadence note
        right-aligned — standing chrome, D-09), the discovered region
        (fixed height), the cell region (flex, the resume note on its
        title row), the 1-row stats line, the bottom bar."""
        yield TopMenuBar()
        with Horizontal(id="mon-title-bar"):
            yield Label(MON_SCREEN_TITLE, id="mon-screen-title")
            yield Label(MON_SCAN_NOTE, id="mon-scan-note")
        with Vertical(id="mon-discovered-region"):
            with Horizontal(id="mon-discovered-title-row"):
                yield Label(MON_DISCOVERED_TITLE.format(n=0),
                            id="mon-discovered-title")
            yield DataTable(id="mon-discovered")
        with Vertical(id="mon-cells-region"):
            with Horizontal(id="mon-cells-title-row"):
                yield Label("", id="mon-cells-title")
                yield Label("", id="mon-resume-note")
            yield DataTable(id="mon-cells")
        yield Label("", id="mon-stats-line")
        yield BottomBar()

    def on_mount(self) -> None:
        """Build the tables, focus the discovered list, arm the cadence."""
        discovered = self.query_one("#mon-discovered", DataTable)
        discovered.cursor_type = "row"
        discovered.zebra_stripes = True
        self._render_discovered()
        cells = self.query_one("#mon-cells", DataTable)
        cells.cursor_type = "row"
        cells.zebra_stripes = True
        self._render_cells()
        discovered.focus()
        # the D-09 cadence: every tick dispatches a worker (never an
        # inline scan); the mount kick covers the first full pass so
        # the screen never waits 60s for its first rows
        self._tick_full()
        self._frontier_timer = self.set_interval(
            self._frontier_interval, self._tick_frontier)
        self._full_timer = self.set_interval(
            self._full_interval, self._tick_full)

    def on_resize(self) -> None:
        """Re-derive the width mode (the 80-col column degradation)."""
        narrow = self.size.width < _NARROW_WIDTH
        if narrow != self._narrow:
            self._narrow = narrow
            self._render_discovered()
            self._render_cells()
            self._render_stats_line()

    def on_unmount(self) -> None:
        """The cadence stops with the screen (no zombie timers)."""
        for timer in (self._frontier_timer, self._full_timer):
            if timer is not None:
                timer.stop()

    # ===== the cadence workers (D-09 — SEPARATE groups) =====

    def _tick_full(self) -> None:
        """The 60s tick (+ the mount kick + [r]): dispatch the full
        scan worker (never an inline scan — T-11-07-01)."""
        self._full_run_id += 1
        self._run_full_scan(self._full_run_id)

    @work(exclusive=True, thread=True, group="mon-full")
    def _run_full_scan(self, run_id: int) -> None:
        """The full scan + the per-running-root stats + the attached
        rows — all off the event loop (T-11-07-01/04)."""
        try:
            result = self._service.full_scan(self._watermarks or None)
            root_stats: dict[str, Any] = {}
            for summary in result.sweeps:
                if summary.state == SWEEP_RUNNING:
                    root_stats[str(summary.root)] = self._stats_of(
                        str(summary.root))
            cells: Any = ()
            resume = 0
            if self._attached_root is not None:
                cells = self._service.cells_view(self._attached_root)
                resume = self._service.resume_count(self._attached_root)
        except Exception:  # noqa: BLE001 — the tolerant-reader promise:
            # the previous render stands (last-known-good), never a crash
            return
        self.post_message(self.FullScanned(
            result, root_stats, cells, resume, run_id))

    def _stats_of(self, root: str) -> Any:
        """One root's stats with the launch injections threaded."""
        return self._service.stats(
            root,
            expected_total=self._expected_totals.get(root),
            fallback_start=self._fallback_starts.get(root))

    def _tick_frontier(self) -> None:
        """The 2s tick: dispatch the frontier scan of the attached root
        (a no-op pass while nothing is attached — the cadence stays
        armed, the degradation-sweep contract)."""
        if self._attached_root is None:
            return
        self._frontier_run_id += 1
        self._run_frontier(str(self._attached_root),
                           self._frontier_run_id)

    @work(exclusive=True, thread=True, group="mon-frontier")
    def _run_frontier(self, root: str, run_id: int) -> None:
        """The light 2s pass + the stats refresh (elapsed accrues
        continuously, D-17) — off the event loop."""
        try:
            snapshot = self._service.frontier_scan(root)
            stats = self._stats_of(root)
        except Exception:  # noqa: BLE001 — same tolerant promise
            return
        self.post_message(self.FrontierScanned(snapshot, stats, run_id))

    # ===== message handlers (event-loop side: render only) =====

    def on_monitor_screen_full_scanned(self, message: FullScanned) -> None:
        """The discovered pane composes from the scan; the attached
        bindings rebind (or degrade honestly when the root vanished)."""
        if message.run_id != self._full_run_id:
            return  # a superseded scan's late post (WR-02)
        self._scan = message.result
        self._watermarks = dict(message.result.watermarks)
        self._root_stats.update(message.root_stats)
        for summary in message.result.sweeps:
            self._scales[str(summary.root)] = (
                self._service.sweep_scale(summary.root)
                if summary.state == SWEEP_FINISHED else None)
        attached_key = (str(self._attached_root)
                        if self._attached_root is not None else None)
        discovered_roots = {
            str(summary.root) for summary in message.result.sweeps}
        self._ever_discovered |= discovered_roots
        if (attached_key is not None
                and attached_key in self._ever_discovered
                and attached_key not in discovered_roots):
            # the attached root vanished from the scan (deleted mid-
            # monitor): degrade honestly — no stale marker, no crash.
            # A root the scan has NEVER listed survives (a just-attached
            # manual root awaits its first discovery pass).
            self._attached_root = None
            self._last_stats = None
            self._cell_rows = {}
            self._resume_count = 0
            self._ever_discovered.discard(attached_key)
        elif attached_key is not None:
            self._cell_rows = self._merge_cell_rows(
                self._cell_rows, message.cells)
            self._resume_count = message.resume
            stats = message.root_stats.get(attached_key)
            if stats is not None:
                self._last_stats = stats
        self._render_discovered()
        self._render_cells()
        self._render_stats_line()
        if self._pending_rescan:
            self._pending_rescan = False
            self.app.notify(MON_RESCAN_TOAST.format(
                n=len(message.result.sweeps)))

    def on_monitor_screen_frontier_scanned(
            self, message: FrontierScanned) -> None:
        """The cell states + stats refresh from the light pass; new
        (model, task) rows appear live (the driver mkdirs before the
        executor runs)."""
        if message.run_id != self._frontier_run_id:
            return
        if self._attached_root is None:
            return
        root_key = str(self._attached_root)
        self._root_stats[root_key] = message.stats
        self._last_stats = message.stats
        merged: dict[str, Any] = dict(self._cell_rows)
        for (model, task, seed), state in (
                message.snapshot.cell_states.items()):
            key = f"{model}__{task}"
            row = merged.get(key)
            if row is None:
                merged[key] = sweep_monitor.CellRow(
                    model=model, task=task,
                    seeds=(sweep_monitor.CellSeed(
                        seed=seed, state=state, fraction_states=None),))
                continue
            seeds = {cell_seed.seed: cell_seed for cell_seed in row.seeds}
            existing = seeds.get(seed)
            if existing is None or existing.state != state:
                seeds[seed] = sweep_monitor.CellSeed(
                    seed=seed, state=state, fraction_states=None)
                merged[key] = sweep_monitor.CellRow(
                    model=row.model, task=row.task,
                    seeds=tuple(seeds[number]
                                for number in sorted(seeds)))
        self._cell_rows = merged
        self._render_discovered()
        self._render_cells()
        self._render_stats_line()

    @staticmethod
    def _merge_cell_rows(current: dict, rows: Any) -> dict:
        """Fold a fresh cells_view into the table state: known rows
        take the fresh view wholesale; rows only the frontier saw are
        retained (the union keeps manifest-only queued rows)."""
        merged = dict(current)
        for row in rows or ():
            merged[f"{row.model}__{row.task}"] = row
        return merged

    # ===== the D-13 launch-injection seam =====

    def note_launch(self, root: str, cells: int) -> None:
        """Record a TUI-launched sweep's plan (the 11-04 stats seams):
        the expected total and the fallback start (the launch moment —
        superseded by the first record's started_at once it lands).

        WR-02 (phase-11 review): a note with ``cells == 0`` (the re-run
        flow, whose plan is unknown) CLEARS any stale expected total a
        prior launch at the same root left behind — the fresh run's own
        manifest (once it lands) or the honest unknown-total governs,
        never the prior sweep's number for the whole session."""
        root_key = str(Path(str(root)).resolve())
        if cells:
            self._expected_totals[root_key] = int(cells)
        else:
            self._expected_totals.pop(root_key, None)
        self._fallback_starts[root_key] = time.time()
        if self._attached_root is None:
            self.attach(root_key)

    def attach(self, root) -> None:
        """Attach one sweep root: the ◆ moves, the cell table / stats /
        failures / log bindings rebind, and the frontier target updates.

        Safe before mount (the D-13 hook may attach while another
        screen is active): the state lands now, the refresh worker runs
        on the next mount kick or tick."""
        self._attached_root = Path(str(root))
        self._cell_rows = {}
        self._last_stats = None
        self._resume_count = 0
        if self.is_running:
            self._tick_full()
            self._tick_frontier()

    def attached_running_counts(self) -> "tuple[bool, str, str, str]":
        """The ExitModal seam: the attached root's running verdict and
        its live done/total (absent markers when unknown — never a
        fabricated number)."""
        root = self._attached_root
        if root is None:
            return (False, "", "", "")
        summary_state = None
        if self._scan is not None:
            for summary in self._scan.sweeps:
                if str(summary.root) == str(root):
                    summary_state = summary.state
        stats = self._last_stats
        done = (str(stats.done) if stats is not None
                else CFG_VALUE_ABSENT)
        total = (str(stats.total)
                 if stats is not None and stats.total is not None
                 else CFG_VALUE_ABSENT)
        return (summary_state == SWEEP_RUNNING, str(root), done, total)

    def request_rerun(self, root: str, count: int) -> None:
        """The [f] modal's r path: the independent ConfirmModal, then
        the re-run through the same pipeline as slot 4 (env preflight
        included — T-11-07-03)."""
        if self.app.below_minimum_grid:
            return
        self.app.push_screen(ConfirmModal(
            message=MON_RERUN_CONFIRM.format(n=count),
            on_confirm=lambda: self._rerun_pipeline(root)))

    def _rerun_pipeline(self, root: str) -> None:
        """The gated re-run: env preflight first (the SAME gate), then
        the from-failures launch, then the toast + auto-attach."""
        self._rerun_stage_id += 1
        self._run_rerun_preflight(root, self._rerun_stage_id)

    @work(exclusive=True, thread=True, group="mon-rerun")
    def _run_rerun_preflight(self, root: str, run_id: int) -> None:
        """The D-08 preflight over the frozen face (worker; WR-03-
        wrapped: an exception surfaces, never a silent post-confirm
        no-op)."""
        try:
            verdict = self._launcher.env_preflight()
        except Exception as exc:  # noqa: BLE001 — WR-03
            self.post_message(self.RerunFailed(
                str(exc) or repr(exc), root, run_id))
            return
        self.post_message(
            self.RerunPreflightDone(verdict, root, run_id))

    def on_monitor_screen_rerun_failed(self, message: RerunFailed) -> None:
        """WR-03: the re-run pipeline's worker raised — surface the
        error toast (the operator confirmed a GPU spend; silence is the
        worst failure mode)."""
        if message.run_id != self._rerun_stage_id:
            return
        self.app.notify(
            LNC_LAUNCH_FAILED_TOAST.format(error=message.error),
            severity="error")

    def on_monitor_screen_rerun_preflight_done(
            self, message: RerunPreflightDone) -> None:
        if message.run_id != self._rerun_stage_id:
            return
        if not message.verdict.can_launch:
            if not self.app.below_minimum_grid:
                from tui.screens.run_config import EnvBlockModal

                self.app.push_screen(EnvBlockModal(
                    message.verdict.failed_kernels,
                    message.verdict.reasons))
            return
        self._run_rerun_launch(message.root, message.run_id)

    @work(exclusive=True, thread=True, group="mon-rerun")
    def _run_rerun_launch(self, root: str, run_id: int,
                          phrase: "str | None" = None) -> None:
        """The from-failures launch over the SAME seam (D-11): the
        re-run re-enters the sweep's own seeds at its own root, carrying
        the source sweep's OWN lane (WR-01 — the lane is recovered from
        the root's artifacts inside this worker, never defaulted, so a
        --peft/--config-variant sweep's failures re-run as that lane,
        not as base cells). CR-01: ``phrase`` threads the E2' re-prompt's
        answer (None on the first attempt — the service's gate refuses
        an E2'-class effective matrix and this screen re-prompts)."""
        seeds = sorted({
            cell_seed.seed
            for row in self._cell_rows.values()
            for cell_seed in row.seeds
        }) or [42]
        failures_path = str(Path(root) / sweep_monitor.FAILURES_NAME)
        try:
            peft, config_variant = self._service.rerun_lane(root)
            outcome = self._launcher.launch_from_failures(
                failures_path, seeds, root,
                peft=peft, config_variant=config_variant, phrase=phrase)
        except Exception as exc:  # noqa: BLE001 — WR-03: post-confirm
            # worker death surfaces, never a silent no-op launch
            self.post_message(self.RerunFailed(
                str(exc) or repr(exc), root, run_id))
            return
        self.post_message(self.RerunFinished(outcome, root, run_id))

    def on_monitor_screen_rerun_finished(
            self, message: RerunFinished) -> None:
        if message.run_id != self._rerun_stage_id:
            return
        outcome = message.outcome
        if isinstance(outcome, sweep_launcher_module.GateRefusal):
            # CR-01: the composed re-run path's own gate spoke. A
            # phrase-stage refusal re-prompts (the E2' typed phrase —
            # the D-07 escalation, never a silent no-op); a problems
            # refusal (official-keys / unevaluatable manifest) surfaces
            # as the launch-failed toast naming the problems verbatim.
            if outcome.stage == sweep_launcher_module.REFUSAL_STAGE_PHRASE:
                if self.app.below_minimum_grid:
                    return
                from tui.screens.run_config import E2PhraseModal

                root = message.root

                def on_phrase(typed_phrase: str) -> None:
                    # a plain closure (not the @work call inline): the
                    # modal's confirm callback returns None
                    self._run_rerun_launch(
                        root, self._rerun_stage_id, typed_phrase)

                self.app.push_screen(E2PhraseModal(
                    dirname=(outcome.expected
                             or run_config_svc.expected_phrase(root)),
                    matches=lambda typed: (
                        self._launcher.phrase_matches(typed, root)),
                    on_confirm=on_phrase,
                ))
                return
            detail = "; ".join(
                f"{code}: {value}" for code, value in outcome.problems)
            self.app.notify(
                LNC_LAUNCH_FAILED_TOAST.format(error=detail),
                severity="error")
            return
        if getattr(outcome, "spawned", False):
            cells = self._expected_totals.get(message.root)
            self.app.notify(MON_RERUN_TOAST.format(
                cells=(str(cells) if cells is not None
                       else MON_ETA_UNKNOWN),
                root=Path(message.root).name))
            self.note_launch(message.root, 0)
            return
        self.app.notify(
            LNC_LAUNCH_FAILED_TOAST.format(
                error=getattr(outcome, "error", None) or ""),
            severity="error")

    # ===== rendering (event-loop side only) =====

    def _discovered_columns(self) -> "list[tuple[str, str]]":
        """The discovered (label, key) columns; the scale column drops
        below the width threshold (the UI-SPEC responsive rule)."""
        columns = [("", "state"), (MON_COL_ROOT, "root")]
        if not self._narrow:
            columns.append((MON_COL_SCALE, "scale"))
        columns.append((MON_COL_PROGRESS, "progress"))
        columns.append((MON_COL_ETA, "eta"))
        return columns

    def _render_discovered(self) -> None:
        """Diff the discovered table to the last scan (WR-05: the
        cursor row identity survives every cadence rebuild)."""
        if not self.is_running:
            return
        table = self.query_one("#mon-discovered", DataTable)
        sweeps = self._scan.sweeps if self._scan is not None else ()
        title = self.query_one("#mon-discovered-title", Label)
        title.update(MON_DISCOVERED_TITLE.format(n=len(sweeps)))
        rows: dict[str, list] = {}
        if not sweeps:
            row: list = [MON_DISCOVERED_EMPTY]
            row.extend([""] * (3 if self._narrow else 4))
            rows["__empty__"] = row
        else:
            attached_key = (str(self._attached_root)
                            if self._attached_root is not None else None)
            for summary in sweeps:
                root_key = str(summary.root)
                copy, style = _SWEEP_STATE_CELLS.get(
                    summary.state, (summary.state, _STYLE_DIM))
                state_cell = Text(copy, style=style)
                attached = root_key == attached_key
                if attached and not self._narrow:
                    # the ◆ accent marker rides the state cell (amend. 13)
                    state_cell = Text.assemble(Text("◆ "), state_cell)
                row = [state_cell, Text(summary.root.name)]
                if not self._narrow:
                    scale = self._scales.get(root_key)
                    row.append(Text(
                        "×".join(str(part) for part in scale)
                        if scale else MON_ETA_UNKNOWN))
                row.append(_progress_cell(summary))
                eta_cell = _discovered_eta_cell(
                    summary, self._root_stats.get(root_key))
                if attached and self._narrow:
                    # the 80-col form carries the marker at the row end
                    eta_cell = Text.assemble(eta_cell, Text(" ◆"))
                row.append(eta_cell)
                rows[root_key] = row
        _set_table_rows(table, self._discovered_columns(), rows)

    def _render_cells(self) -> None:
        """Diff the cell table to the merged rows + seed columns (WR-05:
        the cursor row identity survives every cadence rebuild)."""
        if not self.is_running:
            return
        table = self.query_one("#mon-cells", DataTable)
        self._render_cells_title()
        rows_map = self._cell_rows
        if self._attached_root is None or not rows_map:
            _set_table_rows(
                table,
                [(MON_COL_MODEL, "model"), (MON_COL_TASK, "task"),
                 ("", "seed_0")],
                {"__empty__": [MON_CELLS_EMPTY, "", ""]})
            return
        seeds = sorted({
            cell_seed.seed
            for row in rows_map.values()
            for cell_seed in row.seeds})
        columns = [(MON_COL_MODEL, "model"), (MON_COL_TASK, "task")]
        columns.extend(
            (MON_COL_SEED.format(seed=seed), f"seed_{seed}")
            for seed in seeds)
        key_width = max(8, self.size.width // 3 - 2)
        rows: dict[str, list] = {}
        for key in sorted(rows_map):
            row = rows_map[key]
            model_cell = Text(row.model)
            model_cell.truncate(key_width, overflow="ellipsis", pad=False)
            task_cell = Text(row.task)
            task_cell.truncate(key_width, overflow="ellipsis", pad=False)
            cells = [model_cell, task_cell]
            seed_map = {cell_seed.seed: cell_seed for cell_seed
                        in row.seeds}
            for seed in seeds:
                cell_seed = seed_map.get(seed)
                if cell_seed is None:
                    cells.append(Text(_glyph_of(MON_STATE_QUEUED),
                                      style=_STYLE_DIM))
                else:
                    cells.append(
                        _seed_cell(cell_seed, wide=not self._narrow))
            rows[key] = cells
        _set_table_rows(table, columns, rows)

    def _render_cells_title(self) -> None:
        """The cells title + the standing resume note (MON-05)."""
        if not self.is_running:
            return
        title = self.query_one("#mon-cells-title", Label)
        if self._attached_root is None:
            title.update("")
        else:
            title.update(MON_CELLS_TITLE.format(
                root=self._attached_root.name))
        note = self.query_one("#mon-resume-note", Label)
        if self._resume_count > 0:
            note_copy = (MON_RESUME_NOTE_SHORT if self._narrow
                         else MON_RESUME_NOTE)
            note.update(Text(note_copy.format(n=self._resume_count),
                             style=_STYLE_SKIPPED))
        else:
            note.update("")

    def _render_stats_line(self) -> None:
        """The MON-02/D-17 stats line (all variants)."""
        if not self.is_running:
            return
        line = self.query_one("#mon-stats-line", Label)
        if self._attached_root is None or self._last_stats is None:
            line.update("")
            return
        line.update(_stats_line(self._last_stats, self._narrow))

    # ===== interactions =====

    def action_row_action(self) -> None:
        """[enter] with no focused table (the complementary chokepoint
        to the DataTable's own select event — the data_manager idiom)."""
        self._row_action_for_focused()

    def on_data_table_row_selected(
            self, event: DataTable.RowSelected) -> None:
        """enter on either table's native select event (mouse and key
        share this chokepoint)."""
        self._row_action_for_focused()

    def _row_action_for_focused(self) -> None:
        """Route enter by the focused table: attach on the discovered
        list (D-03), cell detail on the cells table."""
        focused = self.focused
        if not isinstance(focused, DataTable):
            return
        row_key = focused.coordinate_to_cell_key(
            focused.cursor_coordinate)[0].value
        if focused.id == "mon-discovered":
            if str(row_key) == "__empty__":
                return
            self.attach(row_key)
            self.app.notify(MON_ATTACHED_TOAST.format(
                root=Path(str(row_key)).name))
        elif focused.id == "mon-cells" and str(row_key) != "__empty__":
            detail_row = self._cell_rows.get(str(row_key))
            if detail_row is None or self.app.below_minimum_grid:
                return
            self._open_cell_detail(detail_row)

    @work(exclusive=True, thread=True, group="mon-detail", exit_on_error=False)
    def _open_cell_detail(self, row: Any) -> None:
        """Read the row's run records off the event loop, then push the
        detail modal (fields verbatim — data, never elided)."""
        root = str(self._attached_root) if self._attached_root else ""
        records: dict[int, dict] = {}
        for seed in row.seeds:
            record = self._service.cell_record(
                root, row.model, row.task, seed.seed)
            if record is not None:
                records[seed.seed] = record
        self.post_message(self.DetailReady(row, records))

    class DetailReady(Message):
        """The cell's records arrived (worker thread -> loop)."""

        def __init__(self, row: Any, records: dict) -> None:
            self.row = row
            self.records = records
            super().__init__()

    def on_monitor_screen_detail_ready(self, message: DetailReady) -> None:
        if self.app.below_minimum_grid:
            return
        self.app.push_screen(CellDetailModal(
            message.row.model, message.row.task, message.row,
            records=message.records))

    def action_show_failures(self) -> None:
        """[f]: the failures modal over the attached root."""
        if self.app.below_minimum_grid or self._attached_root is None:
            return
        self._open_failures(str(self._attached_root))

    @work(exclusive=True, thread=True, group="mon-failures", exit_on_error=False)
    def _open_failures(self, root: str) -> None:
        """Read the failure list off the event loop, then push."""
        failures = self._service.failures_view(root)
        self.post_message(self.FailuresRead(root, failures))

    def on_monitor_screen_failures_read(
            self, message: FailuresRead) -> None:
        if self.app.below_minimum_grid:
            return
        self.app.push_screen(FailuresModal(
            message.root, message.failures, self))

    def action_show_log_tail(self) -> None:
        """[t]: the log-tail modal over the attached root's tee."""
        if self.app.below_minimum_grid or self._attached_root is None:
            return
        root_key = str(self._attached_root)
        tee = self._launcher.tee_path_for(root_key)
        self.app.push_screen(LogTailModal(
            self._attached_root.name, tee,
            tail_reader=self._service.read_log_tail,
            interval=self._frontier_interval))

    def action_attach_path(self) -> None:
        """[a]: the manual-root path modal — validation via the service
        predicate; an invalid path keeps the modal open with the reason
        row (never silent, never attached)."""
        if self.app.below_minimum_grid:
            return

        def on_submit(path: str):
            if self._service.add_manual_root(path):
                self.attach(path)
                self._pending_rescan = True
                self._tick_full()
                if not self.app.below_minimum_grid:
                    self.app.notify(MON_ATTACHED_TOAST.format(
                        root=Path(path).name))
                return None
            return (("path", MON_ATTACH_INVALID_TOAST.format(path=path)),)

        self.app.push_screen(PathInputModal(
            MON_ATTACH_TITLE, MON_ATTACH_PLACEHOLDER, on_submit))

    def action_rescan(self) -> None:
        """[r]: an immediate full rescan outside the 60s cadence; the
        toast (with the count) lands when the scan does."""
        self._pending_rescan = True
        self._tick_full()
