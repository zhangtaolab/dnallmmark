"""
monitor — the slot-5 monitor screen (Phase 11, 11-07; menu slot 5).

The operator's monitoring surface over the 11-04 pure scanner: the
discovered-sweeps pane (three D-03 states, progress + ETA per D-17),
the model×dataset ENTRIES table (C4J-3, 261015-c4j — one row per
(model, task) with the folded completion state + done/total seed
counts and the training-progress cell parsed from the running seed's
newest checkpoint trainer_state; per-seed/fraction detail stays in the
enter drill-down), the stats line, the [f] failures modal with the
gated from-failures re-run (D-11), the [t] tee log tail (D-10/MON-04),
the [a] manual-root attach, and the [r] immediate rescan.

Contract (locked decisions):

- PRESENTATION ONLY (the ``tui/screens/`` tier contract): the screen
  derives NOTHING from the artifact tree itself — every scan, stat,
  failure list, entry fold, and progress parse goes through the
  injected ``MonitorServiceProtocol`` (the plan's rendering
  prohibition). The screen owns only cadence, focus, and rendering.
- D-09 cadence: ``set_interval(2s)`` dispatches the frontier worker and
  ``set_interval(60s)`` the full-scan worker — a tick NEVER scans
  inline; each tick bumps its run id, dispatches an
  ``@work(exclusive=True, thread=True, group=...)`` worker in its OWN
  group (the data_manager group-discipline note: exclusivity cancels by
  (node, group), so the two cadences must never share one), and posts a
  run-id-tagged message whose handler drops superseded posts (WR-02).
  C4J-3: the frontier/full workers additionally refresh the attached
  root's ``entries_progress`` (inside the SAME exclusive worker, never
  the event loop; a fake service without the method reads {} — the
  tolerant getattr seam).
- Honesty over motion (the phase-10 progress rule): unknown totals,
  pending ETAs, absent elapsed, the no-tee log state, and a running
  entry whose checkpoint parses nothing are DESIGNED renderings via
  the frozen MON_ constants — never fabricated numbers and never
  errors.
- WR-06: every async modal push checks ``app.below_minimum_grid``.

I18N-01: zero Chinese literals in this module — every operator-facing
string renders through ``tui/strings.py`` constants (grep-enforced);
roots, model/task keys, record fields, argv, and paths stay data,
verbatim.
"""

import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Protocol

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen, Screen
from textual.widgets import DataTable, Footer, Label, RichLog, Static

from tui import strings as S
from tui.screens.nav import BottomBar, TopMenuBar
from tui.screens.selection import (
    ConfirmModal,
    LaunchConfirmModal,
    PathInputModal,
)
from tui.services import run_config as run_config_svc
from tui.services import sweep_launcher as sweep_launcher_module
from tui.services import sweep_monitor
from tui.services.sweep_monitor import (
    CELL_COMPLETED,
    CELL_FAILED,
    CELL_INTERRUPTED,
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

#: The entries list's non-running progress cell — a table symbol / data
#: word (not operator copy — the data_manager module's _DASH precedent).
_DASH = "—"

#: Keycap labels for the [f]/[t] bindings (CR-01, quick-261016-hhx — the
#: 08 review): the dedicated MON_FAILURES_KEYCAP / MON_LOG_KEYCAP
#: registry constants replace the old ``split()``-substring projections
#: of the modal-title constants — byte-equal values in BOTH languages,
#: but now registry entries themselves, so ``remap_binding_descriptions``
#: can translate them on the L toggle (a split() substring never
#: byte-matched any registry value and stayed frozen in the boot
#: language forever).

def _sweep_state_cells() -> "dict[str, tuple[str, str]]":
    """The discovered-sweep state cell vocabulary (machine state -> the
    glyph-first copy + its style channel), re-derived at CALL time
    (CR-01, quick-261016-hhx — the state words follow the live
    language)."""
    return {
        SWEEP_RUNNING: (S.MON_STATE_RUNNING_SWEEP, _STYLE_RUNNING),
        SWEEP_FINISHED: (S.MON_STATE_FINISHED_SWEEP, _STYLE_DIM),
        SWEEP_ARTIFACTS_ONLY: (S.MON_STATE_ARTIFACTS_SWEEP, _STYLE_DIM),
    }


def _cell_state_cells() -> "dict[str, tuple[str, str]]":
    """The per-seed cell-state vocabulary (machine state -> copy +
    style), re-derived at CALL time (CR-01 — same rule). The
    interrupted leg (261017-uwr, UWR-1) rides the muted channel —
    honest history, no failure semantics."""
    return {
        CELL_COMPLETED: (S.MON_STATE_DONE, _STYLE_DONE),
        CELL_FAILED: (S.MON_STATE_FAILED, _STYLE_FAILED),
        CELL_SKIPPED: (S.MON_STATE_SKIPPED, _STYLE_SKIPPED),
        CELL_RUNNING: (S.MON_STATE_RUNNING, _STYLE_RUNNING),
        CELL_QUEUED: (S.MON_STATE_QUEUED, _STYLE_DIM),
        CELL_INTERRUPTED: (S.MON_STATE_INTERRUPTED, _STYLE_DIM),
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
        return S.MON_ETA_PENDING
    if eta.mode == ETA_RANGE:
        return S.MON_ETA_RANGE.format(
            lo=format_eta(eta.lo_seconds).lstrip("≈"),
            hi=format_eta(eta.hi_seconds).lstrip("≈"))
    if eta.mode == ETA_POINT:
        return format_eta(eta.point_seconds).lstrip("≈")
    return S.MON_ETA_UNKNOWN


def _stats_line(stats: Any, narrow: bool) -> str:
    """The MON-02/D-17 stats line over one SweepStats (all variants)."""
    elapsed = (
        format_hms(stats.elapsed_seconds)
        if stats.elapsed_seconds is not None else S.MON_ETA_UNKNOWN)
    if stats.total is None:
        return S.MON_STATS_LINE_UNKNOWN_TOTAL.format(
            done=stats.done, elapsed=elapsed)
    eta_field = _eta_field(stats.eta)
    if narrow or stats.current is None:
        line = S.MON_STATS_LINE_NO_CURRENT.format(
            done=stats.done, total=stats.total,
            elapsed=elapsed, eta=eta_field)
    else:
        line = S.MON_STATS_LINE.format(
            done=stats.done, total=stats.total,
            model=stats.current.model, task=stats.current.task,
            seed=stats.current.seed, elapsed=elapsed, eta=eta_field)
    if eta_field in (S.MON_ETA_PENDING, S.MON_ETA_UNKNOWN):
        # the degradation copy never rides the ≈ prefix
        line = line.replace("≈" + eta_field, eta_field)
    return line


def _progress_cell(summary: Any) -> Text:
    """The discovered-row progress cell: the phase-10 grammar verbatim
    (``{done}/{total}`` + the 10-cell bar on running rows; the bar is
    additive, never fabricated; unknown totals render the designed
    copy)."""
    if summary.total is None:
        return Text(S.MON_TOTAL_UNKNOWN, style=_STYLE_DIM)
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
        return Text(S.MON_ETA_UNKNOWN, style=_STYLE_DIM)
    eta = stats.eta
    if eta.mode == ETA_PENDING:
        return Text(S.MON_ETA_PENDING, style=_STYLE_DIM)
    if eta.mode == ETA_RANGE:
        return Text("≈" + S.MON_ETA_RANGE.format(
            lo=format_eta(eta.lo_seconds).lstrip("≈"),
            hi=format_eta(eta.hi_seconds).lstrip("≈")))
    if eta.mode == ETA_POINT:
        return Text(format_eta(eta.point_seconds))
    return Text(S.MON_ETA_UNKNOWN, style=_STYLE_DIM)


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

    def _registry_live_roots(self) -> tuple:
        """The launcher REGISTRY's live roots alone — the kill-face
        basis (261017-uwr UWR-2: a probed CLI sweep is display-live
        but never handle-killable, so [k]'s predicate NEVER widens to
        the probe union)."""
        if self._launcher is None:
            return ()
        return tuple(self._launcher.live_sweeps())

    def _live_evidence(self) -> "tuple[tuple, dict]":
        """The live-sweep evidence union (261017-uwr, UWR-2): the
        launcher REGISTRY's live roots plus the /proc-probed CLI roots,
        with each root's planned pair matrix. Tolerant at the seam (the
        entries_progress precedent): a launcher without
        ``live_sweep_matrices`` (every pre-existing fake) degrades to
        ``live_sweeps()`` alone with NO per-root matrices; a raising
        call degrades the same way — the previous render stands."""
        live_roots = self._registry_live_roots()
        if self._launcher is None:
            return live_roots, {}
        matrices_getter = getattr(
            self._launcher, "live_sweep_matrices", None)
        if matrices_getter is None:
            return live_roots, {}
        try:
            matrices = dict(matrices_getter() or {})
        except Exception:  # noqa: BLE001 — the tolerant-reader promise
            return live_roots, {}
        merged = tuple(dict.fromkeys(live_roots + tuple(matrices)))
        return merged, matrices

    def _live_pairs_for(self, root, matrices: dict):
        """The root's live-pair evidence: a strict miss (the root
        absent from the evidence dict) reads the EMPTY set — the
        dead-root case, every non-terminal cell derives interrupted."""
        root_key = str(Path(root).expanduser().resolve())
        return matrices.get(root_key, frozenset())

    def full_scan(self, prev_watermarks: "dict | None" = None) -> Any:
        live_roots, _matrices = self._live_evidence()
        return sweep_monitor.full_scan(
            live_roots=live_roots,
            prev_watermarks=prev_watermarks)

    def frontier_scan(self, root) -> Any:
        live_roots, matrices = self._live_evidence()
        return sweep_monitor.frontier_scan(
            root, live_roots=live_roots,
            live_pairs=self._live_pairs_for(root, matrices))

    def cells_view(self, root) -> Any:
        _live_roots, matrices = self._live_evidence()
        return sweep_monitor.cells_view(
            root, live_pairs=self._live_pairs_for(root, matrices))

    def entries_progress(self, root) -> Any:
        """C4J-3's backend leg: the attached root's progress map over
        the live-evidence-threaded derivation (Rule 2, 261017-uwr — the
        adapter had NO entries_progress delegation, so the REAL screen
        read {} through the tolerant getattr seam and the progress
        column was dead in production while every Pilot fake carried
        it; the delegation lands here with the evidence threading)."""
        _live_roots, matrices = self._live_evidence()
        return sweep_monitor.entries_progress(
            root, live_pairs=self._live_pairs_for(root, matrices))

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
        """The registry-only kill face (261017-uwr UWR-2 pin): [k]'s
        gate reads the LAUNCHER REGISTRY alone — a probed CLI sweep is
        display-live but never handle-killable."""
        return self._registry_live_roots()

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
        Binding("escape", "dismiss", S.APP_MODAL_BACK_LABEL),
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
        Binding("r", "rerun_failures", S.MON_RERUN_LABEL),
        Binding("escape", "dismiss", S.APP_MODAL_BACK_LABEL),
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
        box.border_title = S.MON_FAILURES_TITLE.format(n=len(self._failures))
        table = self.query_one("#mon-failures-table", DataTable)
        table.cursor_type = "row"
        table.add_column(S.MON_FAILURE_ROW.format(
            model="model", task="task", seed="seed"), key="model")
        if not self._failures:
            table.add_row(S.MON_FAILURES_EMPTY, key="__empty__")
        else:
            for index, failure in enumerate(self._failures):
                table.add_row(S.MON_FAILURE_ROW.format(
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
            S.MON_FAILURE_ROW.format(model=failure.model, task=failure.task,
                                   seed=failure.seed),
            failure.error))

    def action_rerun_failures(self) -> None:
        """[r]: the independent re-run confirm (never unconfirmed —
        this is a real GPU spend), routed through the monitor screen.
        WR-02/WR-03: the failure ROWS thread into the confirm — they
        are the seed-derivation source and the pairs-count basis, so
        the confirmed estimate names exactly what the launch will
        enumerate."""
        if not self._failures:
            return
        self.dismiss()
        self._monitor.request_rerun(self._root, tuple(self._failures))


class KillConfirmModal(ConfirmModal):
    """The 261016-vxr [k] kill confirm: ``y`` is the ONLY key that
    stops the training, ``n``/``esc`` cancel, and ``enter`` is
    STRUCTURALLY inert — bound to a documented no-op (the
    LaunchConfirmModal EHC-2 idiom: a stray double-enter can never
    SIGTERM a live sweep).

    This modal NEVER exits the console: stopping a training task and
    quitting the console are distinct operator acts — y dismisses and
    fires the ``on_confirm`` callback (the screen's off-loop kill
    worker), nothing else.

    The 261017-dnr prominence ruling (DNR-2): the message's [Y]/[N]
    tokens render bold and the y/n bindings carry show=True with
    bilingual keycaps — visibility only; y stays the ONLY key that
    stops a training, enter lands on the documented no-op, n/esc
    cancel (vxr semantics untouched).
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        # DNR-2 (261017-dnr): the answer keys are VISIBLE — y/n carry
        # show=True with bilingual keycaps. Exact-identical-pair reuse
        # (the WIZ_BACK precedent): MON_KILL_KEYCAP (the Kill word) is
        # exactly what y does; LNC_EXIT_CONFIRM_NO (the Cancel pair) is
        # exactly what n does — zero new constants. enter stays
        # show=False — the inert no-op is never advertised (EHC-2: y the
        # ONLY key that stops a training, keys/actions byte-unchanged).
        Binding("y", "confirm_kill", S.MON_KILL_KEYCAP, show=True),
        Binding("n", "dismiss", S.LNC_EXIT_CONFIRM_NO, show=True),
        # escape inherited from ConfirmModal
    ]

    def __init__(self, message: str, root: str,
                 on_confirm: "Callable[[], None]", **kwargs):
        super().__init__(message, on_confirm, **kwargs)
        self._root = root

    def compose(self) -> ComposeResult:
        # DNR-2 (261017-dnr): the message's [Y]/[y]/[N]/[n] tokens render
        # BOLD via the Rich Text API (the 261017-cdr QuitConfirmModal
        # pattern — Text content is never markup-parsed; 'bold' is a
        # Rich core style, no $token MissingStyle hazard). highlight_words
        # mutates the Text IN PLACE and returns the count (cdr-probed
        # rich text.py:639 -> int) — never chained, two-step only. The
        # layout mirrors ConfirmModal.compose EXACTLY — same
        # #confirm-box Vertical (on_mount queries it for the border
        # title) with the message Static FIRST (the tests query the
        # first Static) — then the Footer that renders the new keycaps.
        message = Text(self._message)
        message.highlight_words(("[Y]", "[y]", "[N]", "[n]"), style="bold")
        with Vertical(id="confirm-box", classes="modal-box"):
            yield Static(message)
            yield Footer()

    def on_mount(self) -> None:
        box = self.query_one("#confirm-box", Vertical)
        box.border_title = S.MON_KILL_TITLE.format(root=self._root)

    def action_confirm(self) -> None:
        """Enter is deliberately inert on the kill confirm (EHC-2
        extended to the kill surface by 261016-vxr: only ``y`` stops a
        training; the message copy names the [Y] keycap)."""
        # documented no-op: the inherited enter binding lands here

    def action_confirm_kill(self) -> None:
        """``y`` — the one key that confirms the kill."""
        self.dismiss()
        self._on_confirm()


class LogTailModal(ModalScreen):
    """The [t] log-tail modal: the bounded RichLog tail of the tee file
    refreshed on the 2s cadence while open; the dim tee line names the
    file (D-10). No tee (a CLI-launched sweep) renders the designed
    unavailable state and schedules NO refresh — never a fabricated
    empty log."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", S.APP_MODAL_BACK_LABEL),
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
        box.border_title = S.MON_LOG_TITLE.format(root=self._root)
        if self._tee_path is None:
            log = self.query_one("#mon-log-tail", RichLog)
            log.write(S.MON_LOG_UNAVAILABLE)
            return  # CLI-launched: no refresh is ever scheduled
        self.query_one("#mon-log-tee-line", Label).update(Text(
            S.MON_LOG_TEE_LINE.format(path=self._tee_path),
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
        Binding("escape", "dismiss", S.APP_MODAL_BACK_LABEL),
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
            copy, _style = _cell_state_cells().get(
                seed.state, (seed.state, _STYLE_DIM))
            log.write(f"{S.MON_COL_SEED.format(seed=seed.seed)}: {copy}")
            for name, state in seed.fraction_states or ():
                frac_copy, _frac_style = _cell_state_cells().get(
                    state, (state, _STYLE_DIM))
                fraction = (name.removeprefix("frac_"))
                log.write("  " + S.MON_FRACTION_LINE.format(
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

    261017-uwr (UWR-4): when the desired row-key ORDER differs from
    the table's current order (a fold flip moving a running row to the
    top), the moved rows are removed and re-added in the desired
    order — Textual's DataTable has no move-row API — and the same
    cursor-key re-pin below preserves the operator's row identity
    across the reorder. An unchanged order takes the in-place update
    path: zero added churn on steady ticks.

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
    current_order = [str(key.value) for key in table.rows]
    if current_order != list(rows):
        # order drift: rebuild the surviving rows in the desired order
        # (remove + re-add — no move-row API); the cursor re-pin below
        # restores the operator's row identity.
        for row_key in current_order:
            table.remove_row(row_key)
        for row_key, cells in rows.items():
            table.add_row(*cells, key=row_key)
    else:
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


def derive_rerun_seeds(failures, cell_rows) -> "tuple[int, ...]":
    """WR-02 (phase-11 stale-refresh review): the [r] re-run's seed
    fan-out derives from the FAILURE ROWS themselves — the sorted
    distinct ``FailureRow.seed`` values first, falling back to the
    sorted distinct cell-row seed values, else ``()`` (empty = refuse
    loudly, never a fixed default).

    ONE pure derivation shared by BOTH consumers — the confirm-side
    estimate (``request_rerun``) and the launch worker
    (``_run_rerun_launch``) — so the confirmed GPU spend and the
    executed GPU spend can never drift apart (WR-03).

    Args:
        failures: the failure rows (``FailureRow`` sequence; the
            ``.seed`` field is authoritative — it names the experiment
            that actually failed).
        cell_rows: the screen's merged cell rows (``{key: CellRow}``;
            the fallback when no failure rows carry seeds).

    Returns:
        tuple[int, ...]: the sorted distinct seeds; empty when nothing
        is derivable.
    """
    seeds = {row.seed for row in failures or ()}
    if not seeds:
        seeds = {
            cell_seed.seed
            for row in (cell_rows or {}).values()
            for cell_seed in row.seeds
        }
    return tuple(sorted(seeds))


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
        Binding("enter", "row_action", S.ENV_DETAIL_LABEL),
        Binding("f", "show_failures", S.MON_FAILURES_KEYCAP),
        Binding("t", "show_log_tail", S.MON_LOG_KEYCAP),
        Binding("a", "attach_path", S.MON_ATTACH_LABEL),
        Binding("r", "rescan", S.MON_RESCAN_LABEL),
        # 261016-vxr (VXR-2): stop the attached training through the
        # launcher's kill channel — y-only confirm, console stays up
        Binding("k", "kill_running", S.MON_KILL_KEYCAP),
        Binding("1", "app.nav(1)", S.NAV_LABEL_ENV, show=False),
        Binding("2", "app.nav(2)", S.NAV_LABEL_SELECTION, show=False),
        Binding("3", "app.nav(3)", S.NAV_LABEL_DATA, show=False),
        Binding("4", "app.nav(4)", S.NAV_LABEL_RUN_CONFIG, show=False),
        Binding("5", "app.nav(5)", S.NAV_LABEL_MONITOR, show=False),
        Binding("6", "app.nav(6)", S.NAV_LABEL_ABOUT, show=False),
    ]

    class FullScanned(Message):
        """The 60s full scan arrived (worker thread -> loop; WR-02)."""

        def __init__(self, result: Any, root_stats: dict,
                     cells: Any, resume: int, run_id: int,
                     progress: "dict | None" = None) -> None:
            self.result = result
            self.root_stats = root_stats
            self.cells = cells
            self.resume = resume
            self.run_id = run_id
            # C4J-3: the attached root's first entries-progress read
            # (None when nothing was attached)
            self.progress = progress
            super().__init__()

    class FrontierScanned(Message):
        """The 2s frontier pass arrived (worker thread -> loop; WR-02)."""

        def __init__(self, snapshot: Any, stats: Any,
                     run_id: int, progress: "dict | None" = None) -> None:
            self.snapshot = snapshot
            self.stats = stats
            self.run_id = run_id
            # C4J-3: the attached root's refreshed entries progress
            self.progress = progress
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

    class KillFinished(Message):
        """The kill outcome arrived (worker thread -> loop; 261016-vxr,
        VXR-2). The console NEVER exits on this path — the handler only
        renders the outcome toast."""

        def __init__(self, outcome: str, root: str, run_id: int) -> None:
            self.outcome = outcome
            self.root = root
            self.run_id = run_id
            super().__init__()

    class KillFailed(Message):
        """The kill worker RAISED (WR-03): surfaced as the MON_KILL_
        FAILED error toast — a confirmed kill that dies is never a
        silent no-op."""

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
        # C4J-3 (261015-c4j): the attached root's entries progress —
        # {(model, task): CellProgress} refreshed by the frontier/full
        # workers; empty when nothing runs or nothing parses
        self._cell_progress: dict[tuple[str, str], Any] = {}
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
        # 261016-vxr (VXR-2): the kill worker's stage id (the WR-02
        # idiom — a superseded kill's late outcome toast drops)
        self._kill_stage_id = 0
        self._pending_rescan = False
        self._frontier_timer = None
        self._full_timer = None
        self._narrow = False

    # ===== compose / mount =====

    def compose(self) -> ComposeResult:
        """The screen frame: nav bars, the title bar (the cadence note
        right-aligned — standing chrome, D-09), the one-row context
        header (261017-uwr, UWR-3 — the attached root + its fold
        counts; empty while unattached, the stats-line precedent), the
        discovered region (fixed height), the cell region (flex, the
        resume note on its title row), the 1-row stats line, the
        bottom bar."""
        yield TopMenuBar()
        with Horizontal(id="mon-title-bar"):
            yield Label(S.MON_SCREEN_TITLE, id="mon-screen-title")
            yield Label(S.MON_SCAN_NOTE, id="mon-scan-note")
        yield Label("", id="mon-context-header")
        with Vertical(id="mon-discovered-region"):
            with Horizontal(id="mon-discovered-title-row"):
                yield Label(S.MON_DISCOVERED_TITLE.format(n=0),
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
        """Build the tables, focus the discovered list, arm the cadence.

        261015-ehc (EHC-1): the mount body is IDEMPOTENT — the L language
        toggle re-invokes it after a recompose (the app's _rerender_screen
        mechanism), so the cadence timers stop BEFORE re-arming (a bare
        second set_interval would orphan the first pair firing forever).
        """
        for timer in (self._frontier_timer, self._full_timer):
            if timer is not None:
                timer.stop()
                if timer is self._frontier_timer:
                    self._frontier_timer = None
                else:
                    self._full_timer = None
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

    def _entries_progress_of(self, root: str) -> dict:
        """The attached root's entries progress through the TOLERANT
        service seam (C4J-3): a fake without ``entries_progress`` (every
        pre-C4J injected service) reads {} — the entries render their
        honest indeterminate, never a crash."""
        progress_getter = getattr(
            self._service, "entries_progress", None)
        if progress_getter is None:
            return {}
        try:
            return dict(progress_getter(root) or {})
        except Exception:  # noqa: BLE001 — the tolerant-reader promise
            return {}

    @work(exclusive=True, thread=True, group="mon-full")
    def _run_full_scan(self, run_id: int) -> None:
        """The full scan + the per-running-root stats + the attached
        rows — all off the event loop (T-11-07-01/04). C4J-3: the
        attached root's FIRST entries-progress read rides the same
        worker (the cadence never scans inline)."""
        try:
            result = self._service.full_scan(self._watermarks or None)
            root_stats: dict[str, Any] = {}
            for summary in result.sweeps:
                if summary.state == SWEEP_RUNNING:
                    root_stats[str(summary.root)] = self._stats_of(
                        str(summary.root))
            cells: Any = ()
            resume = 0
            progress: dict | None = None
            if self._attached_root is not None:
                cells = self._service.cells_view(self._attached_root)
                resume = self._service.resume_count(self._attached_root)
                progress = self._entries_progress_of(
                    str(self._attached_root))
        except Exception:  # noqa: BLE001 — the tolerant-reader promise:
            # the previous render stands (last-known-good), never a crash
            return
        self.post_message(self.FullScanned(
            result, root_stats, cells, resume, run_id, progress))

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
        continuously, D-17) + the entries-progress refresh (C4J-3) —
        all off the event loop."""
        try:
            snapshot = self._service.frontier_scan(root)
            stats = self._stats_of(root)
            progress = self._entries_progress_of(root)
        except Exception:  # noqa: BLE001 — same tolerant promise
            return
        self.post_message(self.FrontierScanned(
            snapshot, stats, run_id, progress))

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
            self._cell_progress = {}
            self._resume_count = 0
            self._ever_discovered.discard(attached_key)
        elif attached_key is not None:
            self._cell_rows = self._merge_cell_rows(
                self._cell_rows, message.cells)
            self._resume_count = message.resume
            if message.progress is not None:
                self._cell_progress = message.progress
            stats = message.root_stats.get(attached_key)
            if stats is not None:
                self._last_stats = stats
        self._render_discovered()
        self._render_cells()
        self._render_stats_line()
        if self._pending_rescan:
            self._pending_rescan = False
            self.app.notify(S.MON_RESCAN_TOAST.format(
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
        if message.progress is not None:
            self._cell_progress = message.progress
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
        # CR-01 note: this pre-resolution is now a documented NO-OP for
        # correctness (attach() owns the expanduser().resolve() contract)
        # — kept so the key computation stays locally explicit.
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

        CR-01 (phase-11 stale-refresh review): the root is stored
        EXPANDED and RESOLVED — ``Path(str(root)).expanduser().resolve()``
        — the exact semantics the ``[a]`` validation layer
        (``add_manual_root``) already applied internally, so validation
        and attach agree on ONE path basis: a ``~`` -spelled operator
        path that VALIDATES also MONITORS. Every reader — cells_view /
        stats / failures_view / cell_record via the service, the ◆
        marker's discovered-table key comparison, attached_running_counts,
        the frontier target — sees the resolved root, never the literal
        spelling. An already-absolute resolved key (the discovered
        table's enter, note_launch) passes through as identity.

        Safe before mount (the D-13 hook may attach while another
        screen is active): the state lands now, the refresh worker runs
        on the next mount kick or tick."""
        self._attached_root = Path(str(root)).expanduser().resolve()
        self._cell_rows = {}
        self._cell_progress = {}
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
                else S.CFG_VALUE_ABSENT)
        total = (str(stats.total)
                 if stats is not None and stats.total is not None
                 else S.CFG_VALUE_ABSENT)
        return (summary_state == SWEEP_RUNNING, str(root), done, total)

    def request_rerun(self, root: str, failures: tuple) -> None:
        """The [f] modal's r path: the independent LaunchConfirmModal
        naming the PLANNED-CELL estimate — ``len(distinct (model, task)
        pairs) x len(seeds)`` over the ONE shared ``derive_rerun_seeds``
        derivation (WR-03: the confirmed GPU spend is the executed GPU
        spend, never an understated entry count) — then the re-run
        through the same pipeline as slot 4 (env preflight included —
        T-11-07-03). Since 261015-ehc (EHC-2) the confirm is a
        LAUNCH confirm: ``y`` starts, ``esc`` cancels, ``enter`` lands
        on the documented no-op (a re-run spends GPU — the same
        misfire-proof key the slot-4 gate carries)."""
        if self.app.below_minimum_grid:
            return
        # EHC-3 (261015-ehc ruling 3): pre-check the single-GPU
        # serialization guard BEFORE pushing the confirm (the tolerant
        # getattr seam — a fake without the method never blocks, the
        # 11-03 precedent; the service's own stage-0 guard is the
        # structural backstop) — y is never reached on a busy
        # single-GPU machine.
        blocked_getter = getattr(
            self._launcher, "single_gpu_launch_blocked", None)
        blocked = (blocked_getter()
                   if blocked_getter is not None else None)
        if blocked:
            self.app.notify(
                S.LNC_SINGLE_GPU_BLOCKED.format(
                    roots=", ".join(blocked)),
                severity="error")
            return
        seeds = derive_rerun_seeds(failures, self._cell_rows)
        pairs = len({(row.model, row.task) for row in failures or ()})
        self.app.push_screen(LaunchConfirmModal(
            message=S.MON_RERUN_CONFIRM.format(
                pairs=pairs,
                seeds=", ".join(str(seed) for seed in seeds),
                n=pairs * len(seeds)),
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
            S.LNC_LAUNCH_FAILED_TOAST.format(error=message.error),
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
        an E2'-class effective matrix and this screen re-prompts).

        WR-02: the seed fan-out re-derives through the ONE shared
        ``derive_rerun_seeds`` over this worker's OWN
        ``failures_view(root)`` re-read (the authoritative rows, read
        off the event loop) with the cell rows as fallback — when
        NOTHING is derivable the pipeline REFUSES LOUDLY
        (``RerunFailed`` -> the error toast; the launcher is never
        consulted) and the silent ``[42]`` default is gone. The E2'
        re-prompt path re-invokes this worker and re-derives
        identically."""
        try:
            failures = self._service.failures_view(root)
            seeds = derive_rerun_seeds(failures, self._cell_rows)
            if not seeds:
                self.post_message(self.RerunFailed(
                    S.MON_RERUN_NO_SEEDS, root, run_id))
                return
            failures_path = str(Path(root) / sweep_monitor.FAILURES_NAME)
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
            # the D-07 escalation, never a silent no-op); the EHC-3
            # single-GPU stage renders its bilingual copy naming the
            # running root(s); any other problems refusal
            # (official-keys / unevaluatable manifest) surfaces as the
            # launch-failed toast naming the problems verbatim.
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
            if any(code == sweep_launcher_module.PROBLEM_SINGLE_GPU
                   for code, _value in outcome.problems):
                roots = "; ".join(
                    str(value) for code, value in outcome.problems
                    if code == sweep_launcher_module.PROBLEM_SINGLE_GPU)
                self.app.notify(
                    S.LNC_SINGLE_GPU_BLOCKED.format(roots=roots),
                    severity="error")
                return
            detail = "; ".join(
                f"{code}: {value}" for code, value in outcome.problems)
            self.app.notify(
                S.LNC_LAUNCH_FAILED_TOAST.format(error=detail),
                severity="error")
            return
        if getattr(outcome, "spawned", False):
            cells = self._expected_totals.get(message.root)
            self.app.notify(S.MON_RERUN_TOAST.format(
                cells=(str(cells) if cells is not None
                       else S.MON_ETA_UNKNOWN),
                root=Path(message.root).name))
            self.note_launch(message.root, 0)
            return
        self.app.notify(
            S.LNC_LAUNCH_FAILED_TOAST.format(
                error=getattr(outcome, "error", None) or ""),
            severity="error")

    # ===== the [k] kill channel (261016-vxr, VXR-2) =====

    def action_kill_running(self) -> None:
        """[k]: stop the attached training through the launcher's kill
        channel — behind its OWN y-only confirm (enter structurally
        inert, EHC-2); the console NEVER exits on this path (stopping a
        training task and quitting the console are distinct operator
        acts). Degradations: below the minimum grid nothing opens
        (WR-06); no attached root is silent (the [f]/[t] precedent); an
        attached root NOT in ``live_sweeps()`` (CLI-launched or already
        dead) refuses BEFORE the confirm with MON_KILL_UNAVAILABLE —
        never a confirm the channel cannot execute."""
        if self.app.below_minimum_grid:
            return
        root = self._attached_root
        if root is None:
            return
        root_key = str(root)
        if root_key not in self._launcher.live_sweeps():
            self.app.notify(
                S.MON_KILL_UNAVAILABLE.format(root=root_key))
            return
        # EHC-3 (261015-ehc ruling 3): the single-GPU serialization
        # guard is deliberately NOT consulted here — kill is the
        # REMEDY on a busy single-GPU machine, not a launch.
        self.app.push_screen(KillConfirmModal(
            message=S.MON_KILL_CONFIRM,
            root=root_key,
            on_confirm=lambda: self._kill_confirmed(root_key)))

    def _kill_confirmed(self, root: str) -> None:
        """y landed on the kill confirm: bump the kill stage id (the
        WR-02 idiom — a superseded kill's late outcome toast drops) and
        dispatch the off-loop kill worker."""
        self._kill_stage_id += 1
        self._run_kill(root, self._kill_stage_id)

    @work(exclusive=True, thread=True, group="mon-kill",
          exit_on_error=False)
    def _run_kill(self, root: str, run_id: int) -> None:
        """The kill through the TOLERANT getattr seam (261016-vxr): a
        launcher face without ``kill_sweep`` (every pre-existing fake —
        the Protocol deliberately does NOT declare it, so no fake is
        ever ty-flagged) reads the noop outcome, exactly the
        entries_progress / single_gpu_launch_blocked precedent.
        ``kill_sweep`` blocks up to the kill grace polling the process
        group — NEVER on the event loop. WR-03: an exception posts
        KillFailed, never a silent post-confirm no-op."""
        kill_getter = getattr(self._launcher, "kill_sweep", None)
        try:
            outcome = (kill_getter(root) if kill_getter is not None
                       else sweep_launcher_module.OUTCOME_NOOP)
        except Exception as exc:  # noqa: BLE001 — WR-03
            self.post_message(self.KillFailed(
                str(exc) or repr(exc), root, run_id))
            return
        self.post_message(self.KillFinished(outcome, root, run_id))

    def on_monitor_screen_kill_finished(
            self, message: KillFinished) -> None:
        """The kill outcome toast — the console stays up (this handler
        never exits anything; the sweep's own scanner state refreshes
        on the next cadence tick)."""
        if message.run_id != self._kill_stage_id:
            return  # a superseded kill's late post (WR-02)
        if message.outcome == sweep_launcher_module.OUTCOME_SIGNALLED:
            self.app.notify(S.MON_KILL_TOAST.format(root=message.root))
        elif (message.outcome
                == sweep_launcher_module.OUTCOME_ALREADY_DEAD):
            self.app.notify(
                S.MON_KILL_TOAST_DEAD.format(root=message.root))
        else:  # noop: the channel no longer knows the root
            self.app.notify(
                S.MON_KILL_UNAVAILABLE.format(root=message.root))

    def on_monitor_screen_kill_failed(self, message: KillFailed) -> None:
        """WR-03: the kill worker raised — the error toast names it."""
        if message.run_id != self._kill_stage_id:
            return
        self.app.notify(
            S.MON_KILL_FAILED.format(error=message.error),
            severity="error")

    # ===== rendering (event-loop side only) =====

    def _discovered_columns(self) -> "list[tuple[str, str]]":
        """The discovered (label, key) columns; the scale column drops
        below the width threshold (the UI-SPEC responsive rule)."""
        columns = [("", "state"), (S.MON_COL_ROOT, "root")]
        if not self._narrow:
            columns.append((S.MON_COL_SCALE, "scale"))
        columns.append((S.MON_COL_PROGRESS, "progress"))
        columns.append((S.MON_COL_ETA, "eta"))
        return columns

    def _render_discovered(self) -> None:
        """Diff the discovered table to the last scan (WR-05: the
        cursor row identity survives every cadence rebuild)."""
        if not self.is_running:
            return
        table = self.query_one("#mon-discovered", DataTable)
        sweeps = self._scan.sweeps if self._scan is not None else ()
        title = self.query_one("#mon-discovered-title", Label)
        title.update(S.MON_DISCOVERED_TITLE.format(n=len(sweeps)))
        rows: dict[str, list] = {}
        if not sweeps:
            row: list = [S.MON_DISCOVERED_EMPTY]
            row.extend([""] * (3 if self._narrow else 4))
            rows["__empty__"] = row
        else:
            attached_key = (str(self._attached_root)
                            if self._attached_root is not None else None)
            for summary in sweeps:
                root_key = str(summary.root)
                copy, style = _sweep_state_cells().get(
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
                        if scale else S.MON_ETA_UNKNOWN))
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
        """Diff the ENTRIES table to the merged rows (C4J-3,
        261015-c4j): one row per (model, task) with the folded state
        word + the done/total seed counts and the training-progress
        cell — per-seed/fraction detail stays in the enter drill-down
        (WR-05: the cursor row identity survives every cadence rebuild).

        261017-uwr (UWR-4): the rows sort by fold GROUP — running rows
        on top (freshest ``newest_mtime`` first, mtime-None last), then
        the unfinished non-running rows (failed / interrupted / queued
        / unrecognized, key ASC), completed rows sink (key ASC) — the
        live row is always visible at the top of the table, dead
        history never hides it.

        The screen derives NOTHING: the fold and the progress both come
        from the service (``sweep_monitor.entry_fold`` /
        ``entries_progress``) — this composes their outputs only, and
        the context header's counts reuse the SAME per-row fold results
        (each row folds exactly once per render pass, no double
        derivation).
        """
        if not self.is_running:
            return
        table = self.query_one("#mon-cells", DataTable)
        self._render_cells_title()
        rows_map = self._cell_rows
        if self._attached_root is None or not rows_map:
            _set_table_rows(
                table,
                [(S.MON_COL_MODEL, "model"), (S.MON_COL_TASK, "task"),
                 (S.MON_COL_STATE, "state"), (S.MON_COL_PROGRESS, "progress")],
                {"__empty__": [S.MON_CELLS_EMPTY, "", "", ""]})
            self._render_context_header()
            return
        columns = [(S.MON_COL_MODEL, "model"), (S.MON_COL_TASK, "task"),
                   (S.MON_COL_STATE, "state"),
                   (S.MON_COL_PROGRESS, "progress")]
        key_width = max(8, self.size.width // 3 - 2)
        folds = {key: sweep_monitor.entry_fold(row)
                 for key, row in rows_map.items()}

        def _row_sort_key(key: str) -> tuple:
            fold_state = folds[key].state
            if fold_state == CELL_RUNNING:
                # freshest activity first; a missing mtime sorts last
                return (0, -(rows_map[key].newest_mtime or 0.0), key)
            if fold_state == CELL_COMPLETED:
                return (2, 0.0, key)
            return (1, 0.0, key)

        running = done = interrupted = 0
        rows: dict[str, list] = {}
        for key in sorted(rows_map, key=_row_sort_key):
            row = rows_map[key]
            fold = folds[key]
            if fold.state == CELL_RUNNING:
                running += 1
            elif fold.state == CELL_COMPLETED:
                done += 1
            elif fold.state == CELL_INTERRUPTED:
                interrupted += 1
            model_cell = Text(row.model)
            model_cell.truncate(key_width, overflow="ellipsis", pad=False)
            task_cell = Text(row.task)
            task_cell.truncate(key_width, overflow="ellipsis", pad=False)
            rows[key] = [
                model_cell,
                task_cell,
                self._entry_state_cell(fold),
                self._entry_progress_cell(
                    fold, self._cell_progress.get((row.model, row.task))),
            ]
        _set_table_rows(table, columns, rows)
        self._render_context_header(running, done, interrupted)

    def _render_context_header(self, running: int = 0, done: int = 0,
                               interrupted: int = 0) -> None:
        """The one-row context header (261017-uwr, UWR-3): the ATTACHED
        root's name, the total entry count, and the three fold-family
        counts — the single line that answers 「these rows come from
        WHERE?」at a glance. Unattached renders the empty string (the
        stats-line precedent); attached-with-zero-rows renders the
        line with n=0 and zero counts (honest, never blank-when-
        attached). ``no_wrap`` so a long line can never push the
        layout. The counts arrive from ``_render_cells``'s single fold
        pass (render-side composition only — the screen derives
        nothing from the artifact tree)."""
        if not self.is_running:
            return
        header = self.query_one("#mon-context-header", Label)
        if self._attached_root is None:
            header.update("")
            return
        header.update(Text(S.MON_CONTEXT_HEADER.format(
            root=self._attached_root.name,
            n=len(self._cell_rows),
            running=running, done=done, interrupted=interrupted),
            no_wrap=True))

    def _entry_state_cell(self, fold: Any) -> Text:
        """The entries state cell: the folded state's glyph word from the
        existing MON_STATE_* vocabulary plus the done/total seed counts
        as data. The narrow grid drops the word — the glyph + counts
        carry the meaning (the seed-cell degradation precedent)."""
        copy, style = _cell_state_cells().get(
            fold.state, (fold.state, _STYLE_DIM))
        counts = S.MON_ENTRY_SEED_COUNTS.format(
            done=fold.done, total=fold.total)
        if self._narrow:
            return Text(f"{_glyph_of(copy)} {counts}", style=style)
        return Text(f"{copy} {counts}", style=style)

    def _entry_progress_cell(self, fold: Any, progress: Any) -> Text:
        """The entries progress cell: steps/max + the integer percent + the
        10-cell bar on RUNNING rows with parseable progress (the
        data_manager progress grammar — the bar's filled cells carry
        the live theme accent); the honest indeterminate constant on
        running rows without progress (never a fabricated number); the
        dim dash on non-running rows. The narrow grid drops the bar.

        261016-vxr (VXR-1): a derivable checkpoint-pair eta appends the
        ``format_eta`` segment after the text/bar (data, CJK-free);
        eta None appends the dim dash — the honest underivable. Zero
        new operator copy (format_eta is data; _DASH is the existing
        table symbol)."""
        if fold.state != CELL_RUNNING:
            return Text(_DASH, style=_STYLE_SKIPPED)
        if progress is None or progress.percent is None:
            return Text(S.MON_PROGRESS_INDETERMINATE,
                        style=_STYLE_RUNNING)
        text = S.MON_PROGRESS_STEPS.format(
            step=progress.step, max=progress.max_steps,
            percent=progress.percent)
        eta_segment = (
            Text(format_eta(progress.eta_seconds))
            if progress.eta_seconds is not None
            else Text(_DASH, style=_STYLE_SKIPPED))
        if self._narrow:
            # the narrow form keeps the steps text + eta, drops the bar
            return Text.assemble(
                Text(text, style=_STYLE_RUNNING),
                Text(" "),
                eta_segment,
            )
        filled = max(0, min(10, round(progress.percent / 10)))
        accent = str(self.app.current_theme.accent)
        return Text.assemble(
            Text(text, style=_STYLE_RUNNING),
            Text(" "),
            Text("█" * filled, style=accent),
            Text("·" * (10 - filled), style=_STYLE_RUNNING),
            Text(" "),
            eta_segment,
        )

    def _render_cells_title(self) -> None:
        """The cells title + the standing resume note (MON-05)."""
        if not self.is_running:
            return
        title = self.query_one("#mon-cells-title", Label)
        if self._attached_root is None:
            title.update("")
        else:
            title.update(S.MON_CELLS_TITLE.format(
                root=self._attached_root.name))
        note = self.query_one("#mon-resume-note", Label)
        if self._resume_count > 0:
            note_copy = (S.MON_RESUME_NOTE_SHORT if self._narrow
                         else S.MON_RESUME_NOTE)
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
            self.app.notify(S.MON_ATTACHED_TOAST.format(
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
                    self.app.notify(S.MON_ATTACHED_TOAST.format(
                        root=Path(path).name))
                return None
            return (("path", S.MON_ATTACH_INVALID_TOAST.format(path=path)),)

        self.app.push_screen(PathInputModal(
            S.MON_ATTACH_TITLE, S.MON_ATTACH_PLACEHOLDER, on_submit))

    def action_rescan(self) -> None:
        """[r]: an immediate full rescan outside the 60s cadence; the
        toast (with the count) lands when the scan does."""
        self._pending_rescan = True
        self._tick_full()
