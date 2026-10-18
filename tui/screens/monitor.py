"""
monitor — the slot-5 monitor screen (Phase 11, 11-07; menu slot 5; the
261018-kvj two-tab redesign over the maintainer's 2026-10-18 15:01
contract).

The operator's monitoring surface is TWO TABS over the 11-04 scanner
service (presentation only — the service layer is byte-untouched):

- Running (the default landing, the zh copy names the tab): ONE
  CARD PER RUN — a run
  is one live handle (the launcher registry ∪ the /proc probe, threaded
  through ``full_scan`` as the uwr live-evidence pipeline). The card
  carries the run name, the manifest scale (model×task×seed, the
  honest unknown when nothing parses), the done/total 10-cell bar, the
  current-cell line (stats.current + the per-cell progress/ETA grammar),
  and — for multi-GPU orchestrator launches — the ``{root}-mgpu-w{i}``
  sibling worker roots render as WORKER ROWS INSIDE the same card (one
  launch = one card; the ``run_sweep_shard.worker_root`` naming is the
  grouping predicate).
- History (the second tab): completed/interrupted runs, newest
  activity first,
  enter drills the run's per-(model, task) cell snapshot; [f] opens
  that run's failures; the old master-detail dual table is DELETED (the
  tabs replace it — WINDOWS #40 closed by the redesign itself).

Execution-recorded design choices (probe decisions the plan left open):

- CARDS RENDER IN A ``ListView`` of ``ListItem`` cards (the
  selection.py template-menu precedent; probed against the
  VerticalScroll-of-focusable-Verticals alternative on textual 8.2.8):
  ListView owns cursor + enter (ItemSelected) natively, cards are few
  (live roots), and the rebuild-per-cadence re-pins the cursor by INDEX
  (clamped) — the WR-05 spirit for a list whose identity is positional.
- DUAL PRESENCE (a root that is live AND carries prior history — the
  same-root re-run workflow) derives from ``resume_count(root) > 0``:
  resume markers are exactly the on-disk evidence that a prior run's
  completed work sits under the root (a fresh first run has none; a
  from-failures re-run or a resume-restart has them). Such a root
  renders its live card on Running AND a History row carrying the
  the re-run-in-progress badge — surfaced with a badge rather
  than deduplicated away (the run-identity ruling).
- The History state glyphs reuse the CELL-state vocabulary (the
  done / interrupted glyph-words) — finished = the complete manifest, interrupted = the uwr
  prior-artifacts leg (the muted channel).

Contract (locked decisions that survive the redesign):

- PRESENTATION ONLY (the ``tui/screens/`` tier contract): the screen
  derives NOTHING from the artifact tree itself — every scan, stat,
  failure list, entry fold, and progress parse goes through the
  injected ``MonitorServiceProtocol``. The screen owns only cadence,
  focus, and rendering.
- D-09 cadence: ``set_interval(2s)`` dispatches ONE frontier worker
  that iterates EVERY live root (frontier_scan + stats +
  entries_progress per root, in the SAME exclusive ``mon-frontier``
  group) and ``set_interval(60s)`` the full-scan worker (``mon-full``)
  — a tick NEVER scans inline; each tick bumps its run id and posts a
  run-id-tagged message whose handler drops superseded posts (WR-02).
- Honesty over motion (the phase-10 progress rule): unknown totals,
  absent scales, a running entry whose checkpoint parses nothing, and
  the no-tee log state are DESIGNED renderings via the frozen MON_
  constants — never fabricated numbers and never errors. The #41
  optimistic first paint renders the tab skeleton + the scanning note
  ONLY (zero fabricated rows) until the first scan message lands.
- Graduation (261018-kvj Task 2): a root the screen OBSERVED running
  that reaches a terminal state between two on-screen scans fires the
  graduation toast and moves Running -> History on the next render.
  Screen-local by design: a finish while another screen is up
  graduates silently on the next visit (honest, no stale toast).
- 261018-rze (the five cadence render gates — the maintainer's
  2026-10-18 19:57 flicker report): a steady 2s tick over UNCHANGED
  data now performs ZERO widget writes. (a) the tab Labels update only
  when the (running, history, active-tab) signature changes, with
  ``layout=False`` (single-line fixed-height labels — the
  textual-blessed case); (b) the scan note updates only on the
  scanning state flip; (c) the card list rebuilds only when the
  STRUCTURE signature changes (roots identity/order, base_live,
  resume-note presence — never progress text) — a content-only change
  updates the existing card Labels in place over the ONE shared
  ``_card_content`` builder, so the operator's cursor identity and the
  ListItem objects survive every steady tick; (d) ``_focus_active``
  no-ops when the target already holds focus; (e) ``_render_all``
  early-returns while another screen is stacked above (a modal or the
  min-size guard) — the base surface never repaints beneath it. A
  sixth gate of the same family landed at execution time (a recorded
  deviation): the History rows' rendered-content signature gates the
  table diff pass, because textual 8.2.8's ``update_cell`` refreshes
  unconditionally and the hidden table's refreshes repainted the whole
  card region anyway. The gates reset in ``on_mount`` so the L-toggle
  recompose (fresh empty Labels) fully repaints in the active
  language.
- WR-06: every async modal push checks ``app.below_minimum_grid``.
- 261018-toe (the maintainer's 2026-10-18 21:21 slot-5 ruling): the
  History tab's row actions — [d] delete (a strong y-only
  DeleteConfirmModal naming the FULL root path and the training-item
  count; live roots structurally undeletable via the pre-modal refusal
  AND the worker-side re-check; the ``rm -rf`` runs in a
  ``mon-delete`` worker thread over the adapter-tier
  ``delete_root`` seam, followed by a full rescan) and [e] resume (the
  incomplete pairs derived off-loop, the honest LaunchConfirmModal, the
  SAME preflight/launch/E2' stages as [f]->[r] through
  ``launch_from_pairs``). The d/e footer keycaps render ONLY while the
  History tab is active (``_footer_pairs`` refreshes on mount + tab
  switch ONLY, never on the cadence — the Running-tab footer stays
  byte-identical so the uncommitted D-03 goldens hold).
- 261018-08g (SOAK-1/F1, PRESERVED EXACTLY): the app builds a FRESH
  MonitorScreen per navigation and injects the shared textual-free
  :class:`MonitorSession` — the fresh-screen-per-nav + session
  survival pair is load-bearing (the pty renav test pins it).

I18N-01: zero Chinese literals in this module — every operator-facing
string renders through ``tui/strings.py`` constants (grep-enforced);
roots, model/task keys, record fields, argv, and paths stay data,
verbatim.
"""

import shutil
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
from textual.widgets import (
    DataTable,
    Footer,
    Label,
    ListItem,
    ListView,
    RichLog,
    Static,
)

from tui import strings as S
from tui.screens.nav import BottomBar, TopMenuBar, binding_row
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
    SWEEP_ARTIFACTS_ONLY,
    SWEEP_FINISHED,
    SWEEP_RUNNING,
    format_eta,
)

if TYPE_CHECKING:
    from textual import getters

    from tui.app import DnallmMarkTui

#: The 80-col width threshold (the UI-SPEC responsive rules: the bars
#: drop, the state words drop to glyphs).
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

#: The multi-GPU sibling-worker marker (``run_sweep_shard.worker_root``
#: freezes ``{base}-mgpu-w{i}`` — one naming authority, 12-04 --merge).
_MGPU_MARKER = "-mgpu-w"


def _mgpu_base(root: str) -> str:
    """Strip the ``-mgpu-w{i}`` worker suffix (``finetuned-mgpu-w0`` ->
    ``finetuned``); a non-worker root passes through verbatim."""
    marker = root.rfind(_MGPU_MARKER)
    if marker == -1:
        return root
    digits = root[marker + len(_MGPU_MARKER):]
    if digits.isdigit():
        return root[:marker]
    return root


def _cell_state_cells() -> "dict[str, tuple[str, str]]":
    """The per-seed cell-state vocabulary (machine state -> copy +
    style), re-derived at CALL time (CR-01 — the state words follow the
    live language). The interrupted leg (261017-uwr, UWR-1) rides the
    muted channel — honest history, no failure semantics."""
    return {
        CELL_COMPLETED: (S.MON_STATE_DONE, _STYLE_DONE),
        CELL_FAILED: (S.MON_STATE_FAILED, _STYLE_FAILED),
        CELL_SKIPPED: (S.MON_STATE_SKIPPED, _STYLE_SKIPPED),
        CELL_RUNNING: (S.MON_STATE_RUNNING, _STYLE_RUNNING),
        CELL_QUEUED: (S.MON_STATE_QUEUED, _STYLE_DIM),
        CELL_INTERRUPTED: (S.MON_STATE_INTERRUPTED, _STYLE_DIM),
    }


def _history_state_cells() -> "dict[str, tuple[str, str]]":
    """The History row state vocabulary (261018-kvj): finished = the ✓
    word, interrupted (the uwr prior-artifacts leg) = the ⏸ word on the
    muted channel. A running root is never a plain History row — it is
    a Running CARD (dual presence adds the badged row, see the module
    docstring)."""
    return {
        SWEEP_FINISHED: (S.MON_STATE_DONE, _STYLE_DONE),
        SWEEP_ARTIFACTS_ONLY: (S.MON_STATE_INTERRUPTED, _STYLE_DIM),
    }


def _glyph_of(copy: str) -> str:
    """The glyph token of one glyph-first constant (glyph + word)."""
    return copy.split(" ", 1)[0]


def _progress_fraction(done, total, running: bool) -> Text:
    """The done/total progress grammar (the phase-10 grammar verbatim):
    ``{done}/{total}`` + the 10-cell bar on running values; the bar is
    additive, never fabricated; an unknown total renders the designed
    copy."""
    if total is None:
        return Text(S.MON_TOTAL_UNKNOWN, style="dim")
    fraction = Text(f"{done}/{total}")
    if not running:
        return fraction
    filled = max(0, min(10, round(done / total * 10)))
    return Text.assemble(
        fraction, Text(" "), Text("█" * filled),
        Text("·" * (10 - filled), style=_STYLE_RUNNING))


def _entry_state_cell(fold: Any, narrow: bool) -> Text:
    """The entry state cell: the folded state's glyph word from the
    MON_STATE_* vocabulary plus the done/total seed counts as data. The
    narrow grid drops the word — the glyph + counts carry the meaning
    (the seed-cell degradation precedent)."""
    copy, style = _cell_state_cells().get(
        fold.state, (fold.state, _STYLE_DIM))
    counts = S.MON_ENTRY_SEED_COUNTS.format(
        done=fold.done, total=fold.total)
    if narrow:
        return Text(f"{_glyph_of(copy)} {counts}", style=style)
    return Text(f"{copy} {counts}", style=style)


def _entry_progress_cell(fold: Any, progress: Any, narrow: bool,
                         accent: str) -> Text:
    """The entry progress cell: steps/max + the integer percent + the
    10-cell bar on RUNNING rows with parseable progress (the
    data_manager progress grammar — the bar's filled cells carry the
    live theme accent); the honest indeterminate constant on running
    rows without progress (never a fabricated number); the dim dash on
    non-running rows. The narrow grid drops the bar.

    261016-vxr (VXR-1): a derivable checkpoint-pair eta appends the
    ``format_eta`` segment after the text/bar (data, CJK-free); eta
    None appends the dim dash — the honest underivable. Zero new
    operator copy (format_eta is data; _DASH is the existing table
    symbol)."""
    if fold.state != CELL_RUNNING:
        return Text(_DASH, style=_STYLE_SKIPPED)
    if progress is None or progress.percent is None:
        return Text(S.MON_PROGRESS_INDETERMINATE, style=_STYLE_RUNNING)
    text = S.MON_PROGRESS_STEPS.format(
        step=progress.step, max=progress.max_steps,
        percent=progress.percent)
    eta_segment = (
        Text(format_eta(progress.eta_seconds))
        if progress.eta_seconds is not None
        else Text(_DASH, style=_STYLE_SKIPPED))
    if narrow:
        # the narrow form keeps the steps text + eta, drops the bar
        return Text.assemble(
            Text(text, style=_STYLE_RUNNING),
            Text(" "),
            eta_segment,
        )
    filled = max(0, min(10, round(progress.percent / 10)))
    return Text.assemble(
        Text(text, style=_STYLE_RUNNING),
        Text(" "),
        Text("█" * filled, style=accent),
        Text("·" * (10 - filled), style=_STYLE_RUNNING),
        Text(" "),
        eta_segment,
    )


def _current_cell_line(stats: Any, progress_map: "dict | None",
                       narrow: bool, accent: str) -> Text:
    """The running card's current-cell line (261018-kvj): stats.current
    names the (model, task, seed) and the per-cell progress rides the
    SAME grammar as _entry_progress_cell (steps/percent + bar + the
    checkpoint-pair eta); no current cell renders the designed absent
    marker — never a fabricated line."""
    if stats is None or stats.current is None:
        # rich-native dim: $token styles crash the Label render path
        return Text(S.MON_CARD_CURRENT_NONE, style="dim")
    current = stats.current
    head = S.MON_CARD_CURRENT.format(
        model=current.model, task=current.task, seed=current.seed)
    progress = (progress_map or {}).get((current.model, current.task))
    if progress is None or progress.percent is None:
        return Text(f"{head} {S.MON_PROGRESS_INDETERMINATE}",
                    style=_STYLE_RUNNING)
    tail = _entry_progress_cell(
        # a synthetic running fold: the progress cell grammar only reads
        # fold.state (running) — the counts come from the head line
        _RunningFold(), progress, narrow, accent)
    return Text.assemble(Text(head), Text(" "), tail)


class _RunningFold:
    """The synthetic always-running fold _current_cell_line feeds the
    progress grammar (the grammar reads ``.state`` only)."""

    state = CELL_RUNNING


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

    def delete_root(self, root) -> None:
        """261018-toe: rm -rf the root, tolerant of a missing dir
        (``ignore_errors``) — the adapter tier owns the mutation so the
        pure-scanner declaration in ``sweep_monitor`` stands (the plan's
        tier ruling). Reached through the tolerant getattr seam (the
        kill_sweep precedent: deliberately NOT declared in the Protocol
        so the pre-existing nav-shell/run-config monitor fakes are
        never ty-flagged; the real backend and the tier-2 Pilot fake
        both carry it)."""
        shutil.rmtree(Path(root).expanduser().resolve(),
                      ignore_errors=True)

    def remove_manual_root(self, path) -> bool:
        """261018-toe: the delete worker's manual-root hygiene leg —
        delegate to the scanner service's own tolerant removal. Reached
        through the tolerant getattr seam (the kill_sweep precedent:
        deliberately NOT declared in the Protocol so no fake is ever
        ty-flagged; every pre-existing fake simply skips the ride)."""
        return sweep_monitor.remove_manual_root(path)

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
# Modals ([f] failures + drill, [t] log tail, cell detail, run cells)
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
    verbatim error, and destructive re-run sits behind its own
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
        # 261018-08g (SOAK-2/F3): the UPPERCASE twins — the displayed
        # copy advertises [Y]/[N], and uppercase presses were inert
        # (the soak read the modal as a dead console). Twins route to
        # the SAME actions as the lowercase originals with show=False
        # (zero Footer/golden churn); y stays the ONLY family that
        # stops a training, uppercase included (EHC-2 preserved).
        Binding("Y", "confirm_kill", show=False),
        Binding("N", "dismiss", show=False),
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


class DeleteConfirmModal(ConfirmModal):
    """The 261018-toe [d] delete confirm: the KillConfirmModal contract
    matched EXACTLY — ``y`` (visible keycap) + ``Y`` (hidden twin) are
    the ONLY keys that confirm the ``rm -rf`` of a dead run's output
    root, ``n``/``N`` and ``esc`` cancel, and ``enter`` is STRUCTURALLY
    inert (a stray double-enter can never delete a run's artifacts).

    The message names the FULL root path and the training-item count
    (the honest scope of the deletion, derived off the event loop); the
    border title names the root. Live roots never reach this modal
    (screen-side refusal plus the worker-side re-check).
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        # The KillConfirmModal exact-pair reuse: MON_DELETE_KEYCAP (the
        # Delete word) is exactly what y does; LNC_EXIT_CONFIRM_NO (the
        # Cancel pair) is exactly what n does — zero new keycap pairs.
        # enter stays show=False — the inert no-op is never advertised.
        Binding("y", "confirm_delete", S.MON_DELETE_KEYCAP, show=True),
        Binding("n", "dismiss", S.LNC_EXIT_CONFIRM_NO, show=True),
        # the UPPERCASE twins (the SOAK-2/F3 idiom): same actions,
        # show=False — y stays the ONLY family that deletes.
        Binding("Y", "confirm_delete", show=False),
        Binding("N", "dismiss", show=False),
        # escape inherited from ConfirmModal
    ]

    def __init__(self, message: str, root: str,
                 on_confirm: "Callable[[], None]", **kwargs):
        super().__init__(message, on_confirm, **kwargs)
        self._root = root

    def compose(self) -> ComposeResult:
        # the KillConfirmModal layout mirror: the [Y]/[y]/[N]/[n] tokens
        # render BOLD via the Rich Text API (the cdr pattern — Text
        # content is never markup-parsed), same #confirm-box Vertical
        # with the message Static FIRST (on_mount + the tests query it).
        message = Text(self._message)
        message.highlight_words(("[Y]", "[y]", "[N]", "[n]"), style="bold")
        with Vertical(id="confirm-box", classes="modal-box"):
            yield Static(message)
            yield Footer()

    def on_mount(self) -> None:
        box = self.query_one("#confirm-box", Vertical)
        box.border_title = S.MON_DELETE_TITLE.format(root=self._root)

    def action_confirm(self) -> None:
        """Enter is deliberately inert on the delete confirm (EHC-2
        extended to the delete surface by 261018-toe: only ``y`` deletes;
        the message copy names the [Y] keycap)."""
        # documented no-op: the inherited enter binding lands here

    def action_confirm_delete(self) -> None:
        """``y`` — the one key that confirms the deletion."""
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

class RunCellsModal(ModalScreen):
    """The 261018-kvj per-run drill (enter on a running card or a
    History row): ONE read-once snapshot of the run's (model, task)
    cell rows with the folded state + progress grammar (the
    LogTailModal read-once precedent — live refresh stays on the
    running card; the drill is a snapshot). Enter again opens the
    existing CellDetailModal through the owning screen's record-read
    worker."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "drill_cursor", show=False),
        Binding("escape", "dismiss", S.APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, root: str, rows: "dict[str, Any]",
                 progress: "dict | None", monitor: "MonitorScreen",
                 **kwargs):
        super().__init__(**kwargs)
        self._root = root
        self._rows = dict(rows)
        self._progress = dict(progress or {})
        # the owning monitor screen (the FailuresModal parent-pass idiom)
        self._monitor = monitor

    def compose(self) -> ComposeResult:
        with Vertical(id="mon-runcells-box", classes="modal-box"):
            yield DataTable(id="mon-runcells-table")
            yield Footer()

    def on_mount(self) -> None:
        box = self.query_one("#mon-runcells-box", Vertical)
        box.border_title = S.MON_RUN_CELLS_TITLE.format(
            root=Path(self._root).name)
        table = self.query_one("#mon-runcells-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        narrow = self.app.size.width < _NARROW_WIDTH
        accent = str(self.app.current_theme.accent)
        key_width = max(8, self.app.size.width // 3 - 2)
        columns = [
            (S.MON_COL_MODEL, "model"), (S.MON_COL_TASK, "task"),
            (S.MON_COL_STATE, "state"),
            (S.MON_COL_PROGRESS, "progress")]
        rows: dict[str, list] = {}
        for key in _drill_row_order(self._rows):
            row = self._rows[key]
            fold = sweep_monitor.entry_fold(row)
            model_cell = Text(row.model)
            model_cell.truncate(key_width, overflow="ellipsis", pad=False)
            task_cell = Text(row.task)
            task_cell.truncate(key_width, overflow="ellipsis", pad=False)
            rows[key] = [
                model_cell, task_cell,
                _entry_state_cell(fold, narrow),
                _entry_progress_cell(
                    fold, self._progress.get((row.model, row.task)),
                    narrow, accent),
            ]
        _set_table_rows(table, columns, rows)
        table.focus()

    def on_data_table_row_selected(
            self, event: DataTable.RowSelected) -> None:
        self.action_drill_cursor()

    def action_drill_cursor(self) -> None:
        """enter: the selected row's full detail (records verbatim) via
        the owning screen's off-loop record reader."""
        table = self.query_one("#mon-runcells-table", DataTable)
        try:
            row_key = str(table.coordinate_to_cell_key(
                table.cursor_coordinate)[0].value)
        except Exception:  # noqa: BLE001 — an empty table
            return
        row = self._rows.get(row_key)
        if row is None:
            return
        self._monitor.open_cell_detail(self._root, row)


def _drill_row_order(rows: "dict[str, Any]") -> "list[str]":
    """The drill table's row order — the UWR-4 live-on-top grouping
    verbatim: running rows first (freshest ``newest_mtime`` first, a
    missing mtime last), then unfinished non-running rows (key ASC),
    completed rows sink."""
    def _sort_key(key: str) -> tuple:
        row = rows[key]
        fold = sweep_monitor.entry_fold(row)
        if fold.state == CELL_RUNNING:
            return (0, -(row.newest_mtime or 0.0), key)
        if fold.state == CELL_COMPLETED:
            return (2, 0.0, key)
        return (1, 0.0, key)

    return sorted(rows, key=_sort_key)


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
        cell_rows: the run's merged cell rows (``{key: CellRow}``; the
            fallback when no failure rows carry seeds).

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


# =====================================================================
# MonitorSession — the session state hoisted OFF the screen (261018-08g)
# =====================================================================


class MonitorSession:
    """The monitor's SESSION state, textual-free (261018-08g, SOAK-1/F1).

    Why this class exists: the screen used to carry this state as plain
    instance attributes, which was only safe because the app cached ONE
    MonitorScreen forever — and that cached-instance design is the root
    cause of the dead-5 freeze (textual 8.2.8 ``switch_screen`` ->
    ``_replace_screen`` awaits ``screen.remove()`` on the outgoing
    instance when navigating away; re-switching re-registers the REMOVED
    instance, which switches the stack but never repaints — real-pty
    probe-pinned, Pilot-blind, the 2026-10-18 soak report FINDING 1).
    The app now builds a FRESH MonitorScreen per navigation exactly like
    every other slot factory, and the cross-navigation state lives HERE
    — constructed once on the composition root and injected into every
    build (the SEL-01 marks-set precedent). Derived scan caches
    (_scan, watermarks, cell rows, timers, ...) deliberately stay
    screen-local: the mount kick rebuilds them, exactly like today's
    first visit after boot.

    261018-kvj: ``attached_root`` is RETIRED — the two-tab design has
    no attach concept (the tabs list every discovered run; [a] adds a
    manual root to the scan set). The surviving fields:

    Fields:
        expected_totals: the D-13 launch injections — the TUI-launched
            plan's cell count per resolved root key (the stats seam).
        fallback_starts: the launch moment per resolved root key (the
            11-04 stats seam; superseded by the first record's
            started_at once it lands).
        ever_discovered: every root any scan ever listed (the
            vanished-root degradation memory).

    ``note_launch`` seeds the stats seams only — the auto-attach-for-
    display leg is gone with the attach concept (WR-02 pops a stale
    expected total on a ``cells == 0`` re-run note, exactly as before).
    """

    def __init__(self) -> None:
        self.expected_totals: dict[str, int] = {}
        self.fallback_starts: dict[str, float] = {}
        self.ever_discovered: set[str] = set()

    def note_launch(self, root, cells: int) -> None:
        """Record a TUI-launched sweep's plan (see the class docstring —
        the stats seams only; a fresh screen's mount kick renders it)."""
        # CR-01 note: this pre-resolution is a documented NO-OP for
        # correctness (the service-side path basis owns the
        # expanduser().resolve() contract) — kept so the key computation
        # stays locally explicit.
        root_key = str(Path(str(root)).resolve())
        if cells:
            self.expected_totals[root_key] = int(cells)
        else:
            self.expected_totals.pop(root_key, None)
        self.fallback_starts[root_key] = time.time()

class _RunCard:
    """One running card's model (261018-kvj): the base identity plus
    its live roots (the base itself first when it is live, else the
    worker roots in w-index order — ``roots[0]`` is the ACTION ROOT
    every scoped key (k/t/f/enter) acts on)."""

    __slots__ = ("base", "roots")

    def __init__(self, base: str, roots: "list[str]") -> None:
        self.base = base
        self.roots = roots


class _RootRead:
    """The full-scan worker's per-live-root payload (off-loop reads,
    posted once per scan — the message carries plain data)."""

    __slots__ = ("cells", "progress", "resume", "scale", "stats")

    def __init__(self, stats, cells, progress, resume, scale) -> None:
        self.stats = stats
        self.cells = cells
        self.progress = progress
        self.resume = resume
        self.scale = scale


class MonitorScreen(Screen):
    """The slot-5 monitor, redesigned as TWO TABS (261018-kvj, the
    maintainer's 2026-10-18 15:01 contract):
    Running (the default landing — one card per live run, worker rows
    for multi-GPU sibling roots) and History (completed/interrupted runs,
    newest first, enter drills the per-run cells). The old master-
    detail dual table is DELETED.

    261018-08g (SOAK-1/F1): the screen is built FRESH per navigation
    (``build_monitor_screen``); the session state that must survive
    navigation lives on the injected :class:`MonitorSession` and the
    write-through properties below."""

    # D-13 slot 5 (the top-menu active-slot marker the nav bar reads).
    NAV_SLOT: ClassVar[int] = 5

    if TYPE_CHECKING:
        # Narrows MessagePump's ``App[object]`` to the composition root
        # (the selection-screen idiom — no runtime import of tui.app).
        app = getters.app(DnallmMarkTui)

    # The bottom-bar vocabulary in declaration order. The nav digits
    # are plain per-screen bindings routed to the app's nav action
    # (never priority, Pattern 2). 261018-kvj: left/right/tab switch
    # the tabs from EITHER tab's focused list — the tab/left/right keys
    # are non-printable, so DECLARED PRIORITY bindings pass the
    # consume-key filter over a focused widget (the 261017-mad f10
    # probe); screen-level priority never fires under a modal (the
    # active screen owns the chain), so the modal Inputs keep native
    # tab semantics. Only the tab key renders a Footer keycap.
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "row_action", S.ENV_DETAIL_LABEL),
        Binding("left", "switch_tab", show=False, priority=True),
        Binding("right", "switch_tab", show=False, priority=True),
        Binding("tab", "switch_tab", S.MON_TAB_SWITCH_KEYCAP,
                priority=True),
        # 261018-toe (the maintainer's 2026-10-18 21:21 ruling): the
        # HISTORY-TAB row actions — [d] delete a dead run's output root
        # (strong y-only confirm, worker-thread rm -rf, live roots
        # structurally undeletable) and [e] resume its incomplete items
        # (the honest confirm + the shared rerun pipeline). Both act on
        # the FOCUSED History row and stay silent everywhere else; the
        # footer keycaps render ONLY while the History tab is active
        # (see _footer_pairs — the Running-tab footer stays
        # byte-identical so the uncommitted D-03 goldens hold).
        # DEVIATION from the plan's "after the k row" placement
        # (recorded in the SUMMARY): the bottom bar's left segment is
        # 1fr (93 cells at the 120-col grid) and the D-15 clip drops
        # the LEAST-PRIMARY (trailing) keycaps first, so an
        # after-[k] declaration clipped exactly [d]/[e] away on the
        # History tab — contradicting the plan's own keycap-paint
        # must-have. Declared here (the History surface's primary
        # actions, ahead of the running-scoped keys) they paint; the
        # Running projection filters them and stays byte-identical.
        Binding("d", "delete_history", S.MON_DELETE_KEYCAP),
        Binding("e", "resume_history", S.MON_RESUME_KEYCAP),
        Binding("f", "show_failures", S.MON_FAILURES_KEYCAP),
        Binding("t", "show_log_tail", S.MON_LOG_KEYCAP),
        Binding("a", "attach_path", S.MON_ATTACH_LABEL),
        Binding("r", "rescan", S.MON_RESCAN_LABEL),
        # 261016-vxr (VXR-2): stop the focused running run through the
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
        """The 60s full scan arrived (worker thread -> loop; WR-02):
        the scan result plus each live root's per-root payload."""

        def __init__(self, result: Any, payload: "dict[str, _RootRead]",
                     run_id: int) -> None:
            self.result = result
            self.payload = payload
            self.run_id = run_id
            super().__init__()

    class FrontierScanned(Message):
        """The 2s frontier pass over EVERY live root arrived (worker
        thread -> loop; WR-02) — per-root snapshots/stats/progress."""

        def __init__(self, snapshots: dict, stats: dict, progress: dict,
                     run_id: int) -> None:
            self.snapshots = snapshots
            self.stats = stats
            self.progress = progress
            self.run_id = run_id
            super().__init__()

    class FailuresRead(Message):
        """The failure list arrived (worker thread -> loop)."""

        def __init__(self, root: str, failures) -> None:
            self.root = root
            self.failures = tuple(failures or ())
            super().__init__()

    class DrillReady(Message):
        """The run drill's read-once snapshot arrived (worker -> loop;
        261018-kvj — the LogTailModal read-once precedent)."""

        def __init__(self, root: str, cells: Any, progress: dict) -> None:
            self.root = root
            self.cells = cells
            self.progress = dict(progress or {})
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

    class DeleteReady(Message):
        """The delete confirm's training-item count arrived (worker ->
        loop; 261018-toe — the LogTailModal read-once precedent: one
        off-loop cells_view read feeds the modal's honest scope)."""

        def __init__(self, root: str, count: int) -> None:
            self.root = root
            self.count = count
            super().__init__()

    class DeleteFinished(Message):
        """The deletion outcome arrived (worker thread -> loop;
        261018-toe). Outcome vocabulary: ``"deleted"`` | ``"refused_live"``
        — machine strings the handler maps to the toasts."""

        def __init__(self, outcome: str, root: str, run_id: int) -> None:
            self.outcome = outcome
            self.root = root
            self.run_id = run_id
            super().__init__()

    class DeleteFailed(Message):
        """The delete worker RAISED (WR-03): surfaced as the
        MON_DELETE_FAILED error toast — a confirmed delete that dies is
        never a silent no-op."""

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
                 session: "MonitorSession | None" = None,
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
        # 261018-08g (SOAK-1/F1): the cross-navigation session state —
        # the shared instance arrives from the composition root (the
        # app's build_monitor_screen); None builds a private one so
        # every existing direct-construction test stays
        # source-compatible.
        self._session: MonitorSession = (
            session if session is not None else MonitorSession())
        # the scan state (event-loop side only; workers post into it) —
        # screen-LOCAL by design (the mount kick rebuilds it; the F1
        # fix deletes the cached-instance design, so a fresh screen
        # starts fresh exactly like today's first visit after boot)
        self._active_tab = "running"
        self._scan: Any = None
        self._summaries: dict[str, Any] = {}
        self._live: set[str] = set()
        self._watermarks: dict[str, float] = {}
        self._root_stats: dict[str, Any] = {}
        self._scales: dict[str, tuple[int, int, int] | None] = {}
        self._resumes: dict[str, int] = {}
        # 261018-kvj: the per-root cell state — {root: {key: CellRow}}
        # and {root: {(model, task): CellProgress}}
        self._cell_rows: dict[str, dict[str, Any]] = {}
        self._cell_progress: dict[str, dict] = {}
        self._card_order: list[str] = []
        # the graduation map (261018-kvj Task 2): root -> state as of
        # the last rendered scan; screen-local by design
        self._last_states: dict[str, str] = {}
        # 261018-kvj #41: True from mount until the first scan message
        self._scanning = True
        # per-worker run ids (WR-02): bumped on every kick so a
        # superseded worker's late post drops
        self._full_run_id = 0
        self._frontier_run_id = 0
        self._rerun_stage_id = 0
        # 261016-vxr (VXR-2): the kill worker's stage id (the WR-02
        # idiom — a superseded kill's late outcome toast drops)
        self._kill_stage_id = 0
        # 261018-toe: the delete worker's stage id (the same WR-02
        # idiom — a superseded delete's late outcome toast drops)
        self._delete_stage_id = 0
        self._pending_rescan = False
        self._frontier_timer = None
        self._full_timer = None
        self._narrow = False
        # 261018-rze: the cadence render gates' sentinels — None forces
        # the first pass through the full structural path, and on_mount
        # resets them so the L-toggle recompose (fresh empty Labels)
        # repaints the fresh widget tree in the active language
        self._tabs_sig: tuple[int, int, str] | None = None
        self._scan_note_shown: bool | None = None
        self._cards_sig: tuple | None = None
        # 261018-rze deviation gate: the History rows' rendered-content
        # signature (see _render_history — textual 8.2.8's update_cell
        # refreshes unconditionally, so the diff pass itself needed a
        # gate)
        self._history_sig: tuple | None = None

    # ===== the session write-through properties (261018-08g, SOAK-1) =====
    # expected_totals / fallback_starts / ever_discovered live on the
    # shared MonitorSession so they survive the rebuild-per-navigation
    # design (261018-kvj: attached_root is retired with the attach
    # concept — the stats seams and the vanished-root memory remain).

    @property
    def _expected_totals(self) -> "dict[str, int]":
        return self._session.expected_totals

    @property
    def _fallback_starts(self) -> "dict[str, float]":
        return self._session.fallback_starts

    @property
    def _ever_discovered(self) -> "set[str]":
        return self._session.ever_discovered

    # ===== compose / mount =====

    def compose(self) -> ComposeResult:
        """The two-tab frame (#41 optimistic paint): nav bars, the
        title bar (the cadence note right-aligned — standing chrome,
        D-09, byte-unchanged for the pty lane's monitor marker), the
        one-row tab header with (n) count badges, ONE content region
        whose children toggle display (single focus, single list), and
        the bottom bar. The scanning note renders at mount BEFORE any
        scan lands — skeleton + note only, never a fabricated row."""
        yield TopMenuBar()
        with Horizontal(id="mon-title-bar"):
            yield Label(S.MON_SCREEN_TITLE, id="mon-screen-title")
            yield Label(S.MON_SCAN_NOTE, id="mon-scan-note")
        with Horizontal(id="mon-tab-header"):
            yield Label("", id="mon-tab-running", classes="mon-tab")
            yield Label("", id="mon-tab-history", classes="mon-tab")
        with Vertical(id="mon-content"):
            yield Static("", id="mon-scanning-note")
            yield Static("", id="mon-running-empty")
            yield ListView(id="mon-cards")
            yield DataTable(id="mon-history")
            yield Static("", id="mon-history-empty")
        yield BottomBar()

    def on_mount(self) -> None:
        """Paint the tab skeleton, focus the active tab's list, arm the
        cadence.

        261015-ehc (EHC-1): the mount body is IDEMPOTENT — the L language
        toggle re-invokes it after a recompose (the app's _rerender_screen
        mechanism), so the cadence timers stop BEFORE re-arming (a bare
        second set_interval would orphan the first pair firing forever).
        """
        # 261018-rze (f, LOAD-BEARING): the recompose rebuilds the
        # compose tree with FRESH empty Labels — the render gates MUST
        # reset here or the unchanged sentinels would gate away the
        # updates and the recomposed tabs/cards would render empty in
        # the stale language
        self._tabs_sig = None
        self._scan_note_shown = None
        self._cards_sig = None
        self._history_sig = None
        for timer in (self._frontier_timer, self._full_timer):
            if timer is not None:
                timer.stop()
                if timer is self._frontier_timer:
                    self._frontier_timer = None
                else:
                    self._full_timer = None
        self._narrow = self.size.width < _NARROW_WIDTH
        history = self.query_one("#mon-history", DataTable)
        history.cursor_type = "row"
        history.zebra_stripes = True
        self.query_one("#mon-running-empty", Static).update(
            S.MON_RUNNING_EMPTY)
        self.query_one("#mon-history-empty", Static).update(
            S.MON_HISTORY_EMPTY)
        self._render_all()
        self._focus_active()
        # 261018-toe: the per-active-tab footer projection — scheduled
        # after the refresh so the BottomBar's keycap child is mounted
        # (the Running-tab filter must land before the first paint is
        # ever observed; the bar's own on_mount projects the unfiltered
        # rows and this refresh corrects them). Mount + tab switch ONLY
        # — never the cadence (the rze byte-silence gates).
        self.call_after_refresh(self._refresh_footer_keys)
        # the D-09 cadence: every tick dispatches a worker (never an
        # inline scan); the mount kick covers the first full pass so
        # the screen never waits 60s for its first rows
        self._tick_full()
        self._frontier_timer = self.set_interval(
            self._frontier_interval, self._tick_frontier)
        self._full_timer = self.set_interval(
            self._full_interval, self._tick_full)

    def on_resize(self) -> None:
        """Re-derive the width mode (the bar/state-word degradation)."""
        narrow = self.size.width < _NARROW_WIDTH
        if narrow != self._narrow:
            self._narrow = narrow
            self._render_all()

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
        """One root's entries progress through the TOLERANT service
        seam (C4J-3): a fake without ``entries_progress`` (every
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
        """The full scan + EVERY live root's stats/cells/progress/
        resume/scale read — all off the event loop (T-11-07-01/04).
        Per-root tolerant: a root whose read raises is skipped (the
        per-file skip idiom), the other roots still land."""
        try:
            result = self._service.full_scan(self._watermarks or None)
        except Exception:  # noqa: BLE001 — the tolerant-reader promise:
            # the previous render stands (last-known-good), never a crash
            return
        payload: dict[str, _RootRead] = {}
        for summary in result.sweeps:
            if summary.state != SWEEP_RUNNING:
                continue
            read = self._read_live_root(str(summary.root))
            if read is not None:
                payload[str(summary.root)] = read
        self.post_message(self.FullScanned(result, payload, run_id))

    def _read_live_root(self, root: str) -> "_RootRead | None":
        """One live root's worker-side reads; None = the per-root skip
        (a raising read drops THAT root only — the per-file idiom)."""
        try:
            return _RootRead(
                stats=self._stats_of(root),
                cells=self._service.cells_view(root),
                progress=self._entries_progress_of(root),
                resume=self._service.resume_count(root),
                scale=self._service.sweep_scale(root))
        except Exception:  # noqa: BLE001 — the tolerant-reader promise
            return None

    def _stats_of(self, root: str) -> Any:
        """One root's stats with the launch injections threaded."""
        return self._service.stats(
            root,
            expected_total=self._expected_totals.get(root),
            fallback_start=self._fallback_starts.get(root))

    def _tick_frontier(self) -> None:
        """The 2s tick: dispatch ONE frontier worker that iterates
        EVERY live root (a no-op pass while nothing runs — the cadence
        stays armed, the degradation-sweep contract)."""
        if not self._live:
            return
        self._frontier_run_id += 1
        self._run_frontier(self._frontier_run_id)

    @work(exclusive=True, thread=True, group="mon-frontier",
          exit_on_error=False)
    def _run_frontier(self, run_id: int) -> None:
        """The light 2s pass over EVERY live root in the SAME exclusive
        worker (frontier_scan + stats + entries_progress per root; the
        elapsed accrues continuously, D-17) — all off the event loop,
        per-root tolerant."""
        snapshots: dict = {}
        stats_map: dict = {}
        progress_map: dict = {}
        for root in sorted(self._live):
            read = self._read_frontier_root(root)
            if read is None:
                continue
            snapshot, stats, progress = read
            snapshots[root] = snapshot
            stats_map[root] = stats
            progress_map[root] = progress
        self.post_message(self.FrontierScanned(
            snapshots, stats_map, progress_map, run_id))

    def _read_frontier_root(
            self, root: str) -> "tuple | None":
        """One live root's frontier reads; None = the per-root skip (a
        raising read drops THAT root only — the per-file idiom)."""
        try:
            return (self._service.frontier_scan(root),
                    self._stats_of(root),
                    self._entries_progress_of(root))
        except Exception:  # noqa: BLE001 — the tolerant-reader promise
            return None

    # ===== message handlers (event-loop side: render only) =====

    def on_monitor_screen_full_scanned(self, message: FullScanned) -> None:
        """Both tabs compose from the scan; the graduation diff fires
        on observed running->terminal transitions (261018-kvj Task 2);
        caches for roots that left the live set drop (the vanished-root
        degradation — no stale cards)."""
        if message.run_id != self._full_run_id:
            return  # a superseded scan's late post (WR-02)
        result = message.result
        # graduation BEFORE the state map updates: only transitions the
        # screen OBSERVED fire (a fresh screen's first scan has no
        # prior — no stale toast, the honest first-paint rule)
        for summary in result.sweeps:
            root_key = str(summary.root)
            previous = self._last_states.get(root_key)
            if previous == SWEEP_RUNNING:
                if summary.state == SWEEP_FINISHED:
                    self.app.notify(S.MON_GRADUATED_DONE_TOAST.format(
                        root=Path(root_key).name))
                elif summary.state == SWEEP_ARTIFACTS_ONLY:
                    self.app.notify(
                        S.MON_GRADUATED_INTERRUPTED_TOAST.format(
                            root=Path(root_key).name))
        self._last_states = {
            str(summary.root): summary.state for summary in result.sweeps}
        self._scan = result
        self._watermarks = dict(result.watermarks or {})
        self._summaries = {
            str(summary.root): summary for summary in result.sweeps}
        live = {str(summary.root) for summary in result.sweeps
                if summary.state == SWEEP_RUNNING}
        self._live = live
        # (the property getter returns the session's LIVE set — update
        # mutates it in place; an |= assignment would need a setter)
        self._ever_discovered.update(
            {str(summary.root) for summary in result.sweeps})
        for root_key, read in message.payload.items():
            self._root_stats[root_key] = read.stats
            self._cell_rows[root_key] = {
                f"{row.model}__{row.task}": row
                for row in (read.cells or ())}
            if read.progress is not None:
                self._cell_progress[root_key] = read.progress
            self._resumes[root_key] = read.resume
            self._scales[root_key] = read.scale
        # vanished-root degradation: every per-root cache for a root
        # that is no longer live drops (a deleted or finished root's
        # card leaves; its History row carries the fresh scan state)
        for cache in (self._root_stats, self._cell_rows,
                      self._cell_progress, self._resumes, self._scales):
            for stale in [key for key in cache if key not in live]:
                del cache[stale]
        self._scanning = False
        self._render_all()
        self._focus_active()
        if self._pending_rescan:
            self._pending_rescan = False
            self.app.notify(S.MON_RESCAN_TOAST.format(
                n=len(result.sweeps)))

    def on_monitor_screen_frontier_scanned(
            self, message: FrontierScanned) -> None:
        """The live cards' stats/progress/cell-state refresh from the
        light pass; new (model, task) rows appear live (the driver
        mkdirs before the executor runs)."""
        if message.run_id != self._frontier_run_id:
            return
        for root_key, snapshot in message.snapshots.items():
            if root_key not in self._live:
                continue
            self._root_stats[root_key] = message.stats[root_key]
            if message.progress.get(root_key) is not None:
                self._cell_progress[root_key] = message.progress[root_key]
            self._cell_rows[root_key] = self._merge_cell_states(
                self._cell_rows.get(root_key, {}),
                snapshot.cell_states or {})
        self._scanning = False
        self._render_all()
        self._focus_active()

    @staticmethod
    def _merge_cell_states(current: dict, cell_states: dict) -> dict:
        """Fold a frontier snapshot's per-seed states into one root's
        cell rows (the frontier-merge idiom, per-root since 261018-kvj):
        known rows take the fresh seed state, unseen (model, task, seed)
        triples appear live."""
        merged = dict(current)
        for (model, task, seed), state in cell_states.items():
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
                    seeds=tuple(seeds[number] for number in sorted(seeds)),
                    newest_mtime=row.newest_mtime)
        return merged

    # ===== the derivation + rendering (event-loop side only) =====

    def _cards(self) -> "list[_RunCard]":
        """The Running tab's card list: live roots grouped by their
        multi-GPU base (the ``-mgpu-w{i}`` sibling naming), freshest
        activity first (a missing mtime last), base name as the
        tiebreak — the live run is always visible at the top."""
        groups: dict[str, list[str]] = {}
        for root_key in self._live:
            groups.setdefault(_mgpu_base(root_key), []).append(root_key)
        cards = [_RunCard(base, sorted(roots))
                 for base, roots in groups.items()]

        def _sort_key(card: _RunCard) -> tuple:
            mtimes = [
                self._summaries[root_key].newest_mtime
                for root_key in card.roots
                if root_key in self._summaries
                and self._summaries[root_key].newest_mtime is not None]
            if not mtimes:
                return (1, 0.0, card.base)
            return (0, -max(mtimes), card.base)

        cards.sort(key=_sort_key)
        return cards

    def _history_rows(self) -> "list[tuple[Any, bool]]":
        """The History tab's rows: every non-running root (✓ finished /
        ⏸ interrupted) newest-activity first, PLUS the dual-presence
        rows — a LIVE root that carries prior history (resume markers
        present: the same-root re-run workflow) keeps its History row
        with the badge (surfaced, never deduplicated away)."""
        rows: list[tuple[Any, bool]] = []
        if self._scan is not None:
            for summary in self._scan.sweeps:
                root_key = str(summary.root)
                if summary.state == SWEEP_RUNNING:
                    if self._resumes.get(root_key, 0) > 0:
                        rows.append((summary, True))
                    continue
                rows.append((summary, False))

        def _sort_key(item: "tuple[Any, bool]") -> tuple:
            summary = item[0]
            mtime = summary.newest_mtime
            if mtime is None:
                return (1, 0.0, str(summary.root))
            return (0, -mtime, str(summary.root))

        rows.sort(key=_sort_key)
        return rows

    def _render_all(self) -> None:
        """One full render pass over the tabbed surface (idempotent —
        every cadence tick and tab switch lands here).

        261018-rze (e): the pass is SUPPRESSED while another screen is
        stacked above (a modal, the min-size guard) — the base surface
        never repaints beneath it; the next 2s tick after dismissal
        refreshes. Graduation and rescan toasts fire in the message
        handlers BEFORE this pass and are unaffected."""
        if not self.is_running:
            return
        if self.app.screen is not self:
            return  # a modal or the min-size guard is stacked above
        cards = self._cards()
        history = self._history_rows()
        self._render_scan_note()
        self._render_tabs(len(cards), len(history))
        self._render_cards(cards)
        self._render_history(history)
        self._apply_visibility(bool(cards), len(history))

    def _render_scan_note(self) -> None:
        """#41: the scanning note paints from mount until the first
        scan message lands (skeleton + note only — no fabricated rows).

        261018-rze (b): the note's update call fires ONLY on the
        scanning state flip — repeated renders at the same ``_scanning``
        value perform zero update calls (textual already change-guards
        the ``.display`` assignments)."""
        note = self.query_one("#mon-scanning-note", Static)
        if self._scanning:
            if self._scan_note_shown is not True:
                note.update(S.MON_SCANNING, layout=False)
                self._scan_note_shown = True
            note.display = True
        else:
            note.display = False
            self._scan_note_shown = False

    def _render_tabs(self, running_count: int, history_count: int) -> None:
        """The one-row tab header: both titles keep their WORDS with
        (n) count badges; the ACTIVE tab renders on the live theme
        accent, the inactive one dim (the nav.py slot-marker precedent
        — the accent resolves at render time, never a hardcoded hex,
        and rich-native ``dim`` only: $token styles crash the Static
        render path, the 09-03 probe pin).

        261018-rze (a): the tab Labels update only when the
        (running, history, active-tab) signature changes — a steady
        tick over unchanged counts performs zero tab writes. The
        ``layout=False`` update is the textual-blessed case for
        single-line fixed-height labels (the size cannot change)."""
        sig = (running_count, history_count, self._active_tab)
        if sig == self._tabs_sig:
            return  # unchanged counts and tab: nothing to paint
        self._tabs_sig = sig
        accent = str(self.app.current_theme.accent)
        running_text = Text.assemble(
            Text(S.MON_TAB_RUNNING), Text(" "),
            Text(S.MON_TAB_COUNT.format(n=running_count)))
        history_text = Text.assemble(
            Text(S.MON_TAB_HISTORY), Text(" "),
            Text(S.MON_TAB_COUNT.format(n=history_count)))
        if self._active_tab == "running":
            running_text.stylize(accent)
            history_text.stylize("dim")
        else:
            running_text.stylize("dim")
            history_text.stylize(accent)
        self.query_one("#mon-tab-running", Label).update(
            running_text, layout=False)
        self.query_one("#mon-tab-history", Label).update(
            history_text, layout=False)

    def _card_content(self, card: _RunCard) -> "list[tuple[str, Text]]":
        """One running card's CONTENT — the ORDERED (css-classes, Text)
        pairs the card renders: run name, the manifest scale (the
        honest unknown when nothing parses), and — for a PLAIN run —
        the done/total 10-cell bar + the current-cell line (stats.
        current + the per-cell progress grammar) + the resume note. A
        PURE WORKER GROUP (the base root itself not live — the
        orchestrator runs only at the ``-mgpu-w{i}`` siblings) renders
        EVERY root as a worker row (no duplicate primary lines); a live
        base renders its own lines plus its sibling worker rows.

        261018-rze (c): the ONE content definition shared by BOTH
        render paths — the rebuild path (``_card_widget``'s ListItem
        construction) and the in-place path (the existing Labels'
        content update) — so the two can never drift."""
        primary = card.roots[0]
        base_live = card.roots[0] == card.base
        scale = self._scales.get(primary)
        lines: list[tuple[str, Text]] = [
            ("mon-card-name", Text(Path(card.base).name)),
            ("mon-card-scale", Text(
                S.MON_CARD_SCALE.format(
                    scale="×".join(str(part) for part in scale))
                if scale else S.MON_SCALE_UNKNOWN,
                style="dim")),
        ]
        worker_roots = card.roots[1:]
        if base_live:
            summary = self._summaries.get(primary)
            stats = self._root_stats.get(primary)
            done = (stats.done if stats is not None
                    else (summary.done if summary is not None else 0))
            total = None
            if stats is not None and stats.total is not None:
                total = stats.total
            elif summary is not None:
                total = summary.total
            accent = str(self.app.current_theme.accent)
            lines.append(("mon-card-total",
                          _progress_fraction(done, total, True)))
            lines.append(("mon-card-current", _current_cell_line(
                stats, self._cell_progress.get(primary), self._narrow,
                accent)))
            resume = self._resumes.get(primary, 0)
            if resume > 0:
                note_copy = (S.MON_RESUME_NOTE_SHORT if self._narrow
                             else S.MON_RESUME_NOTE)
                lines.append(("mon-card-resume",
                              Text(note_copy.format(n=resume),
                                   style="dim")))
        else:
            worker_roots = card.roots
        for worker_root in worker_roots:
            worker_summary = self._summaries.get(worker_root)
            worker_stats = self._root_stats.get(worker_root)
            worker_done = (worker_stats.done if worker_stats is not None
                           else (worker_summary.done
                                 if worker_summary is not None else 0))
            worker_total = None
            if worker_stats is not None and worker_stats.total is not None:
                worker_total = worker_stats.total
            elif worker_summary is not None:
                worker_total = worker_summary.total
            lines.append(("mon-card-worker", Text.assemble(
                Text(Path(worker_root).name, style="dim"),
                Text(" "),
                _progress_fraction(worker_done, worker_total, True))))
        return lines

    def _card_widget(self, card: _RunCard) -> ListItem:
        """One running card's WIDGET — the thin constructor over the
        shared ``_card_content`` builder (261018-rze: the rebuild path's
        widget tree stays byte-identical; see ``_card_content``)."""
        return ListItem(Vertical(
            *[Label(text, classes=classes)
              for classes, text in self._card_content(card)],
            classes="mon-card"))

    def _refresh_card_labels(self, cards: "list[_RunCard]") -> bool:
        """The unchanged-sig in-place refresh (261018-rze, c): walk the
        EXISTING ListItem's Label children in DOM order and update ONLY
        the labels whose content changed (``layout=False`` — the
        single-line fixed-height case) — a steady tick with unchanged
        data performs ZERO widget writes, and the ListItem objects plus
        the ListView's index are never touched (the operator's cursor
        identity survives every steady tick).

        Returns False on any count mismatch (a sig bug — the defensive
        fallback routes to the proven rebuild path, never a crash)."""
        list_view = self.query_one("#mon-cards", ListView)
        if len(list_view.children) != len(cards):
            return False
        for item, card in zip(list_view.children, cards):
            content = self._card_content(card)
            labels = list(item.query(Label))
            if len(labels) != len(content):
                return False
            for label, (_classes, text) in zip(labels, content):
                if str(label.content) != str(text):
                    label.update(text, layout=False)
        return True

    def _render_cards(self, cards: "list[_RunCard]") -> None:
        """Render the card list (few items — live roots). 261018-rze
        (c): the STRUCTURE signature (roots identity/order, base_live,
        resume-note presence — the three things that change a card's
        LABEL COUNT; NEVER progress/scale text) gates the rebuild; a
        content-only change refreshes the existing Labels in place. The
        rebuild path re-pins the cursor index clamped so a structural
        rebuild never steals the operator's selection (the WR-05
        spirit; a list's identity is positional, cards never reorder
        except on activity changes)."""
        sig = tuple(
            (tuple(card.roots), card.roots[0] == card.base,
             self._resumes.get(card.roots[0], 0) > 0)
            for card in cards)
        if sig == self._cards_sig and self._refresh_card_labels(cards):
            self._card_order = [card.roots[0] for card in cards]
            return
        list_view = self.query_one("#mon-cards", ListView)
        previous = list_view.index
        list_view.clear()
        self._card_order = []
        for card in cards:
            list_view.append(self._card_widget(card))
            self._card_order.append(card.roots[0])
        if self._card_order:
            # an unfocused-but-populated list still highlights row 0 (a
            # bare enter through the screen binding must act on a real
            # selection); a rebuild never steals the operator's index
            list_view.index = max(
                0, min(previous if previous is not None else 0,
                       len(self._card_order) - 1))
        self._cards_sig = sig

    def _history_columns(self) -> "list[tuple[str, str]]":
        return [("", "state"), (S.MON_COL_ROOT, "root"),
                (S.MON_COL_PROGRESS, "progress"),
                (S.MON_COL_ACTIVITY, "activity")]

    @staticmethod
    def _activity_cell(mtime: "float | None") -> Text:
        """The newest-activity cell: local wall-clock data, or the dash
        when the scan carried no mtime (data, never fabricated)."""
        if mtime is None:
            return Text(S.MON_ETA_UNKNOWN, style=_STYLE_DIM)
        return Text(time.strftime("%m-%d %H:%M", time.localtime(mtime)),
                    style=_STYLE_DIM)

    def _render_history(self, rows: "list[tuple[Any, bool]]") -> None:
        """Diff the History table (WR-05: the cursor row identity
        survives every cadence rebuild); empty renders the designed
        copy row.

        261018-rze (the sixth gate — an execution-time deviation from
        the plan's "update_cell early-returns on equal values" premise,
        which does NOT hold on textual 8.2.8: ``update_cell`` refreshes
        UNCONDITIONALLY, so the display-gated table was dirtied 8x per
        steady tick and the compositor repainted the whole card region
        anyway): the rendered-rows signature (root, state, badge,
        done/total, mtime — every input the cells render) gates the
        diff pass; an unchanged history performs ZERO table work. The
        on_mount reset keeps the L-toggle recompose's fresh table
        populated."""
        sig = tuple(
            (str(summary.root), summary.state, dual,
             summary.done, summary.total, summary.newest_mtime)
            for summary, dual in rows)
        if sig == self._history_sig:
            return
        self._history_sig = sig
        table = self.query_one("#mon-history", DataTable)
        row_map: dict[str, list] = {}
        if not rows:
            row_map["__empty__"] = [
                S.MON_HISTORY_EMPTY, "", "", ""]
        else:
            for summary, dual in rows:
                root_key = str(summary.root)
                copy, style = _history_state_cells().get(
                    summary.state, (summary.state, _STYLE_DIM))
                state_cell = Text(copy, style=style)
                name_cell = Text(summary.root.name)
                if dual:
                    # the same-root re-run is LIVE: its card sits on the
                    # Running tab while this row carries the badge
                    name_cell = Text.assemble(
                        name_cell,
                        Text(f" {S.MON_HISTORY_RERUN_BADGE}",
                             style=_STYLE_RUNNING))
                row_map[root_key] = [
                    state_cell, name_cell,
                    _progress_fraction(summary.done, summary.total, False),
                    self._activity_cell(summary.newest_mtime)]
        _set_table_rows(table, self._history_columns(), row_map)

    def _apply_visibility(self, cards_exist: bool,
                          history_count: int) -> None:
        """Toggle the content region's children: ONLY the active tab's
        list renders (single focus, single list); the scanning note is
        orthogonal (mount-window chrome)."""
        running_active = self._active_tab == "running"
        self.query_one("#mon-cards").display = (
            running_active and cards_exist)
        self.query_one("#mon-running-empty").display = (
            running_active and not cards_exist)
        self.query_one("#mon-history").display = (
            not running_active and history_count > 0)
        self.query_one("#mon-history-empty").display = (
            not running_active and history_count == 0)

    def _focus_active(self) -> None:
        """Focus the ACTIVE tab's list (the single-focus design); an
        empty active tab focuses NOTHING (screen-level bindings own the
        keys — the empty Running tab's enter routes to slot 4). Runs
        after every scan render too: the app-level AUTO_FOCUS ("*")
        grabs the first focusable widget on screen push even when the
        list is hidden+empty, which would otherwise swallow the enter
        the empty-state copy advertises.

        261018-rze (d): a branch whose target ALREADY holds focus skips
        the ``.focus()`` call — a steady tick's steal-back on the
        focused widget is pure churn (a focus call repaints the focus
        ring even when the target is unchanged)."""
        if not self.is_running:
            return
        if self._active_tab == "running":
            if self._card_order:
                cards_list = self.query_one("#mon-cards", ListView)
                if cards_list is not self.focused:
                    cards_list.focus()
            elif self.focused is not None:
                self.set_focus(None)
        elif self._history_rows():
            history_table = self.query_one("#mon-history", DataTable)
            if history_table is not self.focused:
                history_table.focus()
        elif self.focused is not None:
            self.set_focus(None)

    # ===== interactions =====

    #: The History-scoped footer keys (261018-toe): the [d]/[e] row
    #: actions render their keycaps ONLY while the History tab is the
    #: active tab.
    _TAB_SCOPED_FOOTER_KEYS: ClassVar[frozenset[str]] = frozenset(
        {"d", "e"})

    def _footer_pairs(self) -> "list[tuple[str, str]]":
        """The bottom bar's left-segment projection (261018-toe):
        ``binding_row`` over ``BINDINGS`` with the History-scoped d/e
        rows dropped unless the History tab is active — the Running-tab
        footer stays byte-identical to the pre-[d]/[e] render (the
        uncommitted D-03 monitor goldens must not change)."""
        pairs: list[tuple[str, str]] = []
        for binding in self.BINDINGS:
            row = binding_row(binding)
            if row is None:
                continue
            if (self._active_tab != "history"
                    and row[0] in self._TAB_SCOPED_FOOTER_KEYS):
                continue
            pairs.append(row)
        return pairs

    def _refresh_footer_keys(self) -> None:
        """Repaint the bottom bar's left keycaps for the ACTIVE tab
        (261018-toe). Fires on mount and on tab switch ONLY — never
        inside ``_render_all`` and never on the 2s cadence (the rze
        byte-silence gates hold)."""
        try:
            bar = self.query_one(BottomBar)
        except Exception:  # noqa: BLE001 — the bar not mounted yet
            return  # unreachable through the call_after_refresh scheduling
        bar.refresh_left_pairs(self._footer_pairs())

    def action_switch_tab(self) -> None:
        """left/right/tab: flip the two tabs (either direction — two
        tabs), repaint, and move focus to the active tab's list."""
        self._active_tab = ("history" if self._active_tab == "running"
                            else "running")
        self._render_all()
        self._focus_active()
        # 261018-toe: the per-tab footer projection follows the flip
        self._refresh_footer_keys()

    def _focused_root(self) -> "str | None":
        """The focused tab's selection root: the focused running card's
        action root (the group primary), or the focused History row's
        root — None when the active tab has no selection (the scoped
        keys' silent-refusal basis)."""
        if self._active_tab == "running":
            if not self._card_order:
                return None
            index = self.query_one("#mon-cards", ListView).index
            if index is None or not 0 <= index < len(self._card_order):
                return None
            return self._card_order[index]
        table = self.query_one("#mon-history", DataTable)
        try:
            row_key = str(table.coordinate_to_cell_key(
                table.cursor_coordinate)[0].value)
        except Exception:  # noqa: BLE001 — an empty table
            return None
        if row_key == "__empty__":
            return None
        return row_key

    async def action_row_action(self) -> None:
        """[enter] with no focused list (the complementary chokepoint
        to the widgets' own select events). The Running tab's EMPTY
        state routes to slot 4 — the ONLY launch gate (slot 5 never
        duplicates it); a focused selection drills the run's cells."""
        if self._active_tab == "running" and not self._card_order:
            if self.app.below_minimum_grid:
                return
            await self.app.action_nav(4)
            return
        root_key = self._focused_root()
        if root_key is not None:
            self._open_run_drill(root_key)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """enter on a running card (the ListView's native select — the
        event carries the selected INDEX directly)."""
        index = event.index
        if index is None or not 0 <= index < len(self._card_order):
            return
        self._open_run_drill(self._card_order[index])

    def on_data_table_row_selected(
            self, event: DataTable.RowSelected) -> None:
        """enter on the History table's native select event (mouse and
        key share this chokepoint)."""
        if event.data_table.id != "mon-history":
            return
        root_key = self._focused_root()
        if root_key is not None:
            self._open_run_drill(root_key)

    def _open_run_drill(self, root_key: str) -> None:
        """Open the per-run cells drill (either tab): the read-once
        snapshot worker (WR-06-guarded push lands on the message)."""
        if self.app.below_minimum_grid:
            return
        self._read_run_cells(root_key)

    @work(exclusive=True, thread=True, group="mon-drill",
          exit_on_error=False)
    def _read_run_cells(self, root_key: str) -> None:
        """The drill's ONE read of cells_view + entries_progress, off
        the event loop (the LogTailModal read-once precedent — live
        refresh stays on the running card; the drill is a snapshot)."""
        try:
            cells = self._service.cells_view(root_key)
            progress = self._entries_progress_of(root_key)
        except Exception:  # noqa: BLE001 — the tolerant-reader promise
            return
        self.post_message(self.DrillReady(root_key, cells, progress))

    def on_monitor_screen_drill_ready(self, message: DrillReady) -> None:
        if self.app.below_minimum_grid:
            return
        rows = {f"{row.model}__{row.task}": row
                for row in (message.cells or ())}
        self.app.push_screen(RunCellsModal(
            message.root, rows, message.progress, self))

    @work(exclusive=True, thread=True, group="mon-detail",
          exit_on_error=False)
    def open_cell_detail(self, root_key: str, row: Any) -> None:
        """Read the row's run records off the event loop, then push the
        detail modal (fields verbatim — data, never elided). Called by
        the RunCellsModal (the FailuresModal parent-pass idiom)."""
        records: dict[int, dict] = {}
        for seed in row.seeds:
            record = self._service.cell_record(
                root_key, row.model, row.task, seed.seed)
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
        """[f]: the failures modal over the FOCUSED run's root (either
        tab); no selection is silent."""
        if self.app.below_minimum_grid:
            return
        root_key = self._focused_root()
        if root_key is None:
            return
        self._open_failures(root_key)

    @work(exclusive=True, thread=True, group="mon-failures",
          exit_on_error=False)
    def _open_failures(self, root_key: str) -> None:
        """Read the failure list off the event loop, then push."""
        failures = self._service.failures_view(root_key)
        self.post_message(self.FailuresRead(root_key, failures))

    def on_monitor_screen_failures_read(
            self, message: FailuresRead) -> None:
        if self.app.below_minimum_grid:
            return
        self.app.push_screen(FailuresModal(
            message.root, message.failures, self))

    def action_show_log_tail(self) -> None:
        """[t]: the log-tail modal over the FOCUSED run's tee (a
        History root or a CLI-launched live root has none — the
        designed unavailable state, never a fabricated empty log)."""
        if self.app.below_minimum_grid:
            return
        root_key = self._focused_root()
        if root_key is None:
            return
        tee = self._launcher.tee_path_for(root_key)
        self.app.push_screen(LogTailModal(
            Path(root_key).name, tee,
            tail_reader=self._service.read_log_tail,
            interval=self._frontier_interval))

    def action_attach_path(self) -> None:
        """[a]: the manual-root path modal — validation via the service
        predicate; an invalid path keeps the modal open with the reason
        row (never silent, never attached). A valid root joins the
        scan set on the next pass and lands on ITS tab (the tabs list
        every discovered run — no attach state remains)."""
        if self.app.below_minimum_grid:
            return

        def on_submit(path: str):
            if self._service.add_manual_root(path):
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

    # ===== the D-13 launch-injection seam =====

    def note_launch(self, root: str, cells: int) -> None:
        """Record a TUI-launched sweep's plan (the 11-04 stats seams) —
        the session seeds the expected total / the fallback start; the
        fresh screen's next scan renders the run (WR-02: a
        ``cells == 0`` re-run note POPS any stale expected total a
        prior launch at the same root left behind)."""
        self._session.note_launch(root, cells)

    def attached_running_counts(self) -> "tuple[bool, str, str, str]":
        """The ExitModal seam (261018-kvj basis change): the FRESHEST
        running root from the last scan and its live done/total (absent
        markers when unknown — never a fabricated number). Registry
        roots merge at the app (launcher.live_sweeps); this read
        catches the CLI-launched (probed) running roots the registry
        does not know. No attach state remains — the scan is the truth."""
        if self._scan is None:
            return (False, "", "", "")
        freshest = None
        for summary in self._scan.sweeps:
            if summary.state != SWEEP_RUNNING:
                continue
            if (freshest is None
                    or (summary.newest_mtime or 0.0)
                    > (freshest.newest_mtime or 0.0)):
                freshest = summary
        if freshest is None:
            return (False, "", "", "")
        root_key = str(freshest.root)
        stats = self._root_stats.get(root_key)
        done = (str(stats.done) if stats is not None
                else S.CFG_VALUE_ABSENT)
        total = (str(stats.total)
                 if stats is not None and stats.total is not None
                 else S.CFG_VALUE_ABSENT)
        return (True, root_key, done, total)

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
        seeds = derive_rerun_seeds(
            failures, self._cell_rows.get(root, {}))
        pairs = len({(row.model, row.task) for row in failures or ()})
        self.app.push_screen(LaunchConfirmModal(
            message=S.MON_RERUN_CONFIRM.format(
                pairs=pairs,
                seeds=", ".join(str(seed) for seed in seeds),
                n=pairs * len(seeds)),
            on_confirm=lambda: self._rerun_pipeline(root)))

    def _rerun_pipeline(self, root: str) -> None:
        """The gated re-run: env preflight first (the SAME gate), then
        the from-failures launch, then the toast."""
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
        off the event loop) with the root's cell rows as fallback —
        when NOTHING is derivable the pipeline REFUSES LOUDLY
        (``RerunFailed`` -> the error toast; the launcher is never
        consulted) and the silent ``[42]`` default is gone. The E2'
        re-prompt path re-invokes this worker and re-derives
        identically."""
        try:
            failures = self._service.failures_view(root)
            seeds = derive_rerun_seeds(
                failures, self._cell_rows.get(root, {}))
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

    # ===== the [k] kill channel (261016-vxr, VXR-2; tab-scoped kvj) =====

    def action_kill_running(self) -> None:
        """[k]: stop the FOCUSED running card's run through the
        launcher's kill channel — behind its OWN y-only confirm (enter
        structurally inert, EHC-2); the console NEVER exits on this
        path (stopping a training task and quitting the console are
        distinct operator acts). Degradations: below the minimum grid
        nothing opens (WR-06); no focused selection is silent (the
        [f]/[t] precedent); a focused root NOT in ``live_sweeps()``
        (a History row, a CLI-launched live root, or already dead)
        refuses BEFORE the confirm with MON_KILL_UNAVAILABLE — never a
        confirm the channel cannot execute."""
        if self.app.below_minimum_grid:
            return
        root_key = self._focused_root()
        if root_key is None:
            return
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

    def _kill_confirmed(self, root_key: str) -> None:
        """y landed on the kill confirm: bump the kill stage id (the
        WR-02 idiom — a superseded kill's late outcome toast drops) and
        dispatch the off-loop kill worker."""
        self._kill_stage_id += 1
        self._run_kill(root_key, self._kill_stage_id)

    @work(exclusive=True, thread=True, group="mon-kill",
          exit_on_error=False)
    def _run_kill(self, root_key: str, run_id: int) -> None:
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
            outcome = (kill_getter(root_key) if kill_getter is not None
                       else sweep_launcher_module.OUTCOME_NOOP)
        except Exception as exc:  # noqa: BLE001 — WR-03
            self.post_message(self.KillFailed(
                str(exc) or repr(exc), root_key, run_id))
            return
        self.post_message(self.KillFinished(outcome, root_key, run_id))

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

    # ===== the [d] delete channel (261018-toe — History-tab scoped) =====

    def _root_is_live(self, root_key: str) -> bool:
        """The [d]/[e] liveness predicate: the last scan's
        SWEEP_RUNNING state for the root (covers probed CLI roots and
        the dual-presence badge rows) OR the launcher registry's live
        set — a live root is never deleted and never resumed."""
        summary = self._summaries.get(root_key)
        if summary is not None and summary.state == SWEEP_RUNNING:
            return True
        return root_key in self._launcher.live_sweeps()

    def action_delete_history(self) -> None:
        """[d] (History tab only): open the strong y-only delete confirm
        over the FOCUSED History row's root — the message names the FULL
        root path and the training-item count (derived off the event
        loop). Degradations: below the minimum grid nothing opens
        (WR-06); off-tab or without a focused row is silent (the [f]/[t]
        precedent); a LIVE root refuses BEFORE any modal with
        MON_DELETE_REFUSED_LIVE — never a confirm whose rm -rf would cut
        a running sweep's artifacts out from under it."""
        if self.app.below_minimum_grid:
            return
        if self._active_tab != "history":
            return
        root_key = self._focused_root()
        if root_key is None:
            return
        if self._root_is_live(root_key):
            self.app.notify(
                S.MON_DELETE_REFUSED_LIVE.format(root=root_key))
            return
        self._read_delete_count(root_key)

    @work(exclusive=True, thread=True, group="mon-drill",
          exit_on_error=False)
    def _read_delete_count(self, root_key: str) -> None:
        """The confirm's honest training-item count: ONE off-loop
        cells_view read, the per-row seed counts summed (the read-once
        drill precedent — the drill family's cells read group)."""
        try:
            cells = self._service.cells_view(root_key)
            count = sum(sweep_monitor.entry_fold(row).total
                        for row in (cells or ()))
        except Exception:  # noqa: BLE001 — the tolerant-reader promise
            return
        self.post_message(self.DeleteReady(root_key, count))

    def on_monitor_screen_delete_ready(self, message: DeleteReady) -> None:
        if self.app.below_minimum_grid:
            return
        self.app.push_screen(DeleteConfirmModal(
            message=S.MON_DELETE_CONFIRM.format(
                root=message.root, n=message.count),
            root=message.root,
            on_confirm=lambda: self._delete_confirmed(message.root)))

    def _delete_confirmed(self, root_key: str) -> None:
        """y landed on the delete confirm: bump the delete stage id (the
        WR-02 idiom — a superseded delete's late outcome toast drops)
        and dispatch the off-loop delete worker."""
        self._delete_stage_id += 1
        self._run_delete(root_key, self._delete_stage_id)

    @work(exclusive=True, thread=True, group="mon-delete",
          exit_on_error=False)
    def _run_delete(self, root_key: str, run_id: int) -> None:
        """The rm -rf in a WORKER THREAD (never the event loop — the
        kill-channel discipline): (a) RE-CHECK liveness first (the
        confirm-to-worker race — a root that went live between y and
        this worker is refused, nothing deleted); (b) the delete_root
        seam (adapter-tier ``shutil.rmtree`` tolerant of a missing dir;
        the tolerant getattr seam — the kill_sweep precedent, so a
        service face without it is never ty-flagged) plus the
        best-effort tolerant manual-root hygiene removal; (c) the
        outcome posted back to the loop (the LogTailModal read-once
        precedent). WR-03: an exception posts DeleteFailed, never a
        silent post-confirm no-op."""
        try:
            if self._root_is_live(root_key):
                self.post_message(self.DeleteFinished(
                    "refused_live", root_key, run_id))
                return
            delete_getter = getattr(self._service, "delete_root", None)
            if delete_getter is None:
                # a service face without the seam (every pre-existing
                # nav-shell/run-config fake): nothing was deleted —
                # surface loudly, never a false success toast
                self.post_message(self.DeleteFailed(
                    "delete_root seam unavailable on the monitor service",
                    root_key, run_id))
                return
            delete_getter(root_key)
            remove_getter = getattr(
                self._service, "remove_manual_root", None)
            if remove_getter is not None:
                # best-effort hygiene: the root itself is already gone;
                # a failed registry rewrite must never fail the delete
                try:
                    remove_getter(root_key)
                except Exception:  # noqa: BLE001, S110 — swallowed
                    pass
        except Exception as exc:  # noqa: BLE001 — WR-03
            self.post_message(self.DeleteFailed(
                str(exc) or repr(exc), root_key, run_id))
            return
        self.post_message(self.DeleteFinished("deleted", root_key, run_id))

    def on_monitor_screen_delete_finished(
            self, message: DeleteFinished) -> None:
        """The delete outcome: the success toast plus an immediate full
        rescan so the row disappears (the [r] idiom, without the rescan
        count toast); the refused-live race surfaces its own refusal
        toast — nothing was deleted."""
        if message.run_id != self._delete_stage_id:
            return  # a superseded delete's late post (WR-02)
        if message.outcome == "refused_live":
            self.app.notify(
                S.MON_DELETE_REFUSED_LIVE.format(root=message.root))
            return
        self.app.notify(S.MON_DELETE_TOAST.format(root=message.root))
        self._tick_full()

    def on_monitor_screen_delete_failed(self, message: DeleteFailed) -> None:
        """WR-03: the delete worker raised — the error toast names it."""
        if message.run_id != self._delete_stage_id:
            return
        self.app.notify(
            S.MON_DELETE_FAILED.format(error=message.error),
            severity="error")


