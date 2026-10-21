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
  ListView owns the cursor natively — click selects/focuses, enter
  drills (261019-n0w) — cards are few
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
- 261019-f0x (the maintainer's 2026-10-18 10:48 redesign — the
  approved variant-B skeleton plus the variant-D right pane): the
  Running card is the B SKELETON — one
  summary strip line (root name + per-category seed counts + the
  done/total fraction + the 20-cell segmented bar + minute-granularity
  elapsed + ETA point/range + the derived it/s rate, every number an
  existing service field or pure arithmetic over them, honest
  unknowns never fabricated) over a MATRIX of every (model, task)
  group (rows = models, columns = tasks, per-seed glyphs in the
  existing state vocabulary), with ←/→/↑/↓ driving the GROUP focus
  (clamped; ↑/↓ cross to the adjacent card at the edges, the ListView
  index follows programmatically; the highlight is style-only —
  ``reverse`` — so in-place updates stay layout-stable) while the
  arrows keep switching tabs exactly as before on the empty Running
  tab, with no groups, and on History (the kvj contract; Tab always
  switches; History ↑/↓ delegate to the focused DataTable's NATIVE
  cursor actions — probed present on textual 8.2.8). The D RIGHT PANE
  (~40 cols, hidden below ``_NARROW_WIDTH`` and off the Running tab,
  never focusable) renders the FOCUSED group's detail from existing
  service data ONLY — per-seed states, the running seed's steps/
  percent/eta over the shared progress grammar + the derived rate —
  NO loss/lr/epoch/context/params line ever renders (those live in
  the log, which is SHOWN: the root's live tee tail over the EXISTING
  ``read_log_tail``/``tee_path_for`` seams, its own exclusive
  ``mon-tail`` worker group on the 2s frontier cadence, bounded like
  the [t] modal, the designed no-tee state when the launch has no
  tee). Every NEW widget joins the rze gate family: strip/matrix/
  detail/tail are content-signature gated (a steady tick writes
  zero), the tail write skips beneath a stacked modal (the read may
  proceed — the next tick catches up), and ``on_mount`` resets every
  new sentinel so the L-toggle recompose fully repaints. [w] toggles
  the matrix <-> the A-style dense per-cell table (the k9s precedent,
  droppable per the maintainer's flag).
- 261019-n0w (the maintainer's live-test fix batch over the landed f0x
  tab): (1) a mouse CLICK on a running card selects and focuses it and
  NEVER opens the drill modal — the ``MatrixCardsList`` subclass drops
  the stock ``_on_list_item__child_clicked`` ``Selected`` post, so
  Enter (the keyboard ``action_select`` path) stays the ONLY drill
  trigger; (2) the highlighted card renders as CONTENT, not a
  block-cursor fill — the app-level ``#mon-cards > ListItem.-highlight``
  transparent rule outranks both of the ListView DEFAULT_CSS
  ``-highlight`` variants, and the group reverse glyphs + the right
  pane's detail header remain the focus affordance; (3) the pane's
  detail carries the approved D composition's two data lines — the
  20-cell progress bar (percent + derived rate) and the step/max +
  point-ETA line — over service-honest fields ONLY (T-f0x-02 held:
  loss/lr/epoch/context/params still never stated).
- 261019-o8e (the maintainer's 2026-10-19 17:23 reused-root report): the
  Running tab's current-sweep views — the matrix row set, the strip's
  glyph counts + done/total, and the [w] wide table — scope to the LIVE
  sweep's planned pair set (the launcher's ``live_sweep_matrices``
  evidence: registry argv + /proc probe, threaded worker-side into BOTH
  cadence messages and stored BEFORE the render that consumes it) per
  root of a card before the merge, so same-root historical residue
  (previous smoke runs) leaves the Running view while the RunCellsModal
  drill and the History tab keep the full-root truth. Every evidence
  gap — no method, absent root, None (unparseable argv), empty set, a
  raising call — falls back root-wide (a live card never renders an
  empty matrix); the filtered models/tasks tuples ARE the cards sig's
  shape legs and the filtered row map IS the wide sig, so the rze/f0x
  gate law (rebuild-on-shape-change, steady zero-write, focus clamps
  through ``_normalize_focus``) holds by construction.
- 261020-blt (the maintainer's twice-reported "only one model shows"
  case, 2026-10-20 07:08/08:17): the Running views render the union of
  the
  DISCOVERED cells and the live sweep's PLANNED cells — the
  ``live_sweep_plans`` evidence ((pairs, seeds) per root: the
  registry's argv authoritative, the /proc probe filling; pairs-only
  evidence adapts with seeds UNKNOWN, never fabricated) — through the
  ONE per-root seam ``_root_scoped_rows``: planned-but-undiscovered
  pairs synthesize QUEUED rows via the existing grammar, discovered
  rows complete their planned-but-unstarted seeds as queued, and
  off-plan residue seeds drop from the Running views ONLY when the
  seeds are known (the o8e law at seed level). Counts (the strip's
  glyphs + done/total, the tree's labels, the [w] wide table) derive
  over the union — total = Σ pairs × planned seeds — and the union is
  a pure function of (plan, discovered rows), so the models/tasks
  shape legs carry it into the gate law (a plan landing mid-session
  rebuilds once, steady ticks write zero). The drill, History, and [e]
  read the SERVICE ``cells_view`` (root-wide discovered truth) — a
  synthesized row never reaches them, by construction not by filter.
- 261019-pe0 (the maintainer's 2026-10-19 18:14-18:16 scalability
  ruling): the left pane is a THREE-STATE cycle matrix -> tree -> wide
  over [w] (the keycap stays MON_WIDE_KEYCAP byte-identical — no footer
  churn beyond the new [*] keycap). TREE = one ``RunCardTree`` per card
  under the strip (model nodes: name + filtered done/total, the o8e
  basis; task leaves: the key + the per-seed glyph cluster with the
  compact inline percent + derived rate on running seeds whose progress
  parses — glyph only otherwise, never a fabricated number) deriving
  from the SAME ``_card_rows`` merged map (the o8e filter applies for
  free). AUTO-FALLBACK (no persisted mode): when any card's matrix
  width exceeds the pane budget the pane DEFAULTS to tree (a PURE
  function of the task sets + the width — it cannot flap between ticks
  with unchanged inputs); a MANUAL [w] choice HOLDS exactly until the
  next STRUCTURAL change (the per-card structure tuple: card set /
  model or task set / narrow flip) or a remount (on_mount resets to
  auto). The NAV CONTRACT is LOCKED and implemented verbatim: up/down
  move between visible nodes (the tree's native clamped cursor — NO
  card crossing in tree state; the matrix card-cross law is
  matrix-scoped); right expands-or-into-children; left
  collapses-or-to-parent (the invisible root is never a target); Enter
  on a model node toggles (NEVER a modal), on a task node drills with
  the cursor pinned; ``*`` toggles expand/collapse-ALL across every
  card; Tab ALWAYS switches. CLICK selects the node + the CARD and
  never drills (the n0w law extended). The GATE LAW extends: the
  per-card tree structure signature gates the rebuild (preserving
  expansion + cursor through the screen-side caches), label-only
  changes update via ``set_label`` in place, the cards signature gains
  the effective-mode leg, and on_mount resets every new sentinel.
- 261020-asm (the maintainer's 2026-10-20 07:12 ruling, tree-variant E):
  the slot-5 tree ENTERS with every MODEL node EXPANDED — every task
  row visible on mount, on a structural (gate-law) rebuild, and on
  every card that appears mid-session. The default lives in ONE site
  (``_TREE_DEFAULT_EXPANDED``, read by ``_build_card_tree`` — the one
  build path the construction and the rebuild legs share); the
  ``_tree_expand`` cache holds only the OPERATOR's own collapse
  choices, so every untouched model (and every fresh card) takes the
  expanded default while an operator collapse persists across
  structural rebuilds and SURVIVES the 2s cadence steady ticks (the
  gate law: a steady tick performs zero tree writes). The locked pe0
  nav contract is UNCHANGED — ``*`` reads the LIVE tree state (from
  the all-open entry it collapses everything, the collapsed-away
  cursor salvaging onto its model node), never this default.
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
from textual import events, work
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen, Screen
from textual.widget import Widget
from textual.widgets import (
    DataTable,
    Footer,
    Label,
    ListItem,
    ListView,
    RichLog,
    Static,
    Tree,
)

from tui import strings as S
from tui.screens.nav import BottomBar, TopMenuBar, binding_row
from tui.screens.selection import (
    ConfirmModal,
    LaunchConfirmModal,
    PathInputModal,
)
from tui.services import dispatch_state, gpu_probe, sweep_monitor
from tui.services import run_config as run_config_svc
from tui.services import sweep_launcher as sweep_launcher_module
from tui.services.sweep_monitor import (
    CELL_COMPLETED,
    CELL_FAILED,
    CELL_INTERRUPTED,
    CELL_QUEUED,
    CELL_RUNNING,
    CELL_SKIPPED,
    ETA_POINT,
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


# =====================================================================
# 261019-f0x — the B-skeleton strip/matrix helpers (pure presentation
# over the existing service seams; every number a service field or
# arithmetic over them). The 261018-kvj card lines (scale / total /
# current / worker rows) RETIRED with this block: the current cell's
# live numbers moved to the D right pane and the [w] wide table, both
# over the SHARED ``_entry_progress_cell`` grammar.
# =====================================================================

#: The matrix/strip glyph styles (rich-native names ONLY — $token
#: styles crash the Static/Label render path, the 09-03 probe pin;
#: DataTable keeps the $token vocabulary, Labels never do).
_MATRIX_GLYPH_STYLES: "dict[str, str]" = {
    CELL_COMPLETED: "green",
    CELL_RUNNING: "cyan bold",
    CELL_FAILED: "red bold",
    CELL_SKIPPED: "dim",
    CELL_INTERRUPTED: "dim",
    CELL_QUEUED: "dim",
}

#: The strip's count-category order (glyphs re-derived from the
#: glyph-first MON_STATE_* constants; non-zero categories render,
#: queued always does).
_STRIP_COUNT_STATES: tuple[str, ...] = (
    CELL_COMPLETED, CELL_RUNNING, CELL_FAILED,
    CELL_INTERRUPTED, CELL_SKIPPED, CELL_QUEUED)

#: The per-seed merge priority when the same (model, task) appears
#: under multiple roots of one card (running wins; first state wins
#: inside a tier — deterministic).
_SEED_MERGE_PRIORITY: "dict[str, int]" = {
    CELL_RUNNING: 0,
    CELL_FAILED: 1,
    CELL_INTERRUPTED: 2,
    CELL_COMPLETED: 3,
    CELL_SKIPPED: 3,
    CELL_QUEUED: 4,
}

#: The matrix's fixed name-column width and the task-column bounds.
_MATRIX_NAME_WIDTH = 20
_MATRIX_MIN_COL_WIDTH = 4
_MATRIX_MAX_COL_WIDTH = 14

#: The strip's segmented-bar geometry.
_BAR_WIDTH = 20


def _state_glyph(state: str) -> str:
    """One machine state's glyph token (the glyph-first MON_STATE_*
    constants; an unrecognized state renders verbatim — honest)."""
    copy, _style = _cell_state_cells().get(state, (state, _STYLE_DIM))
    return _glyph_of(copy)


def _matrix_col_width(task_key: str) -> int:
    """One task column's width: ``max(4, min(len(task)+1, 14))``."""
    return max(_MATRIX_MIN_COL_WIDTH,
               min(len(task_key) + 1, _MATRIX_MAX_COL_WIDTH))


def _format_elapsed_short(seconds: float) -> str:
    """The strip's elapsed segment — minute granularity, a PURE function
    over the stats field (``45m`` / ``2h14m`` / ``3d2h``; the plan's
    4360.0s fixture renders ``1h13m``)."""
    total_minutes = max(0, round(seconds / 60))
    days, remainder = divmod(total_minutes, 1440)
    hours, minutes = divmod(remainder, 60)
    if days:
        return f"{days}d{hours}h"
    if hours:
        return f"{hours}h{minutes}m"
    return f"{minutes}m"


def _rate_of(progress: Any) -> "str | None":
    """The derived it/s rate — PURE arithmetic over the parsed service
    fields: ``(max_steps - step) / eta_seconds`` when all three are
    present and the eta is positive. A rate FIELD does not exist in the
    service tier (never a new service read); None -> the honest dash."""
    if (progress is None
            or progress.max_steps is None or progress.step is None
            or progress.eta_seconds is None
            or progress.eta_seconds <= 0):
        return None
    rate = ((progress.max_steps - progress.step)
            / progress.eta_seconds)
    return f"{rate:.1f}"


def _strip_bar(counts: "dict[str, int]") -> Text:
    """The strip's 20-cell segmented bar (261019-f0x): whole-cell FLOOR
    allocation over the five categories (done/running/failed/
    interrupted+skipped/queued), leftover cells to the largest
    remainder with a deterministic category-order tiebreak; the queued
    remainder renders the ░ dim channel. A zero-seed run renders the
    all-░ bar — the honest shape, never fabricated progress."""
    cells = [
        (counts.get(CELL_COMPLETED, 0), "green", "█"),
        (counts.get(CELL_RUNNING, 0), "cyan", "█"),
        (counts.get(CELL_FAILED, 0), "red", "█"),
        (counts.get(CELL_INTERRUPTED, 0) + counts.get(CELL_SKIPPED, 0),
         "dim", "█"),
        (counts.get(CELL_QUEUED, 0), "dim", "░"),
    ]
    total = sum(count for count, _style, _char in cells)
    if total <= 0:
        return Text("░" * _BAR_WIDTH, style="dim")
    exact = [count * _BAR_WIDTH / total for count, _style, _char in cells]
    quotas = [int(value) for value in exact]
    leftover = _BAR_WIDTH - sum(quotas)
    # largest remainder first; the category order breaks ties
    order = sorted(
        range(len(cells)),
        key=lambda index: (quotas[index] - exact[index], index))
    for index in order[:leftover]:
        quotas[index] += 1
    bar = Text()
    for (count, style, char), quota in zip(cells, quotas):
        if count > 0 and quota > 0:
            bar += Text(char * quota, style=style)
    return bar


# ===== Phase 16 (16-01, TUI-01): the G GPU-lanes panel helpers =====

#: The provider seam's shape: ``provider(timeout)`` returns the frozen
#: rows tuple (sorted by index), the EMPTY tuple (zero GPUs — the
#: explicit empty state), or None (the ONE absent outcome every probe
#: failure mode shares, D16-02).
GpuProbeProvider = Callable[[float], "tuple[gpu_probe.GpuRow, ...] | None"]

#: The lane row's bar width (UI-SPEC Surface A rule 3 — 10 cells, safe
#: at the 80-column floor with the widest 6-digit MiB values).
_GPU_BAR_WIDTH = 10

#: The pre-first-probe state (the #41 optimistic-paint law, 16-01): the
#: panel renders the header row ONLY — note blank, zero lane rows —
#: until the first probe message lands; never a guessed lane.
_GPU_PENDING = object()


def _default_gpu_probe_provider(timeout: float) -> "tuple[gpu_probe.GpuRow, ...] | None":
    """The REAL probe through the service seam (D16-01/D16-03) — the
    fixed-argv nvidia-smi CSV call under the ~2s per-call timeout; the
    injectable default the Pilot/golden lanes replace with fabricated
    :class:`gpu_probe.GpuRow` tuples (CI zero-GPU, D16-14)."""
    return gpu_probe.probe(timeout=timeout)


#: 16-02 (TUI-03, D16-06): the dispatch-state reader seam's shape —
#: ``(root) -> DispatchStateView | None``; None means NO block (an
#: absent or damaged ``dispatch_state.json`` — the static/CLI sweep
#: root and the ``-mgpu-w*`` worker root, byte-identical to today).
DispatchStateReader = Callable[
    [str], "dispatch_state.DispatchStateView | None"]


def _default_dispatch_state_reader(root: str
                                   ) -> "dispatch_state.DispatchStateView | None":
    """The REAL tolerant frozen-v2 read (the injectable default — the
    16-01 gpu-probe provider shape): one ``{root}/dispatch_state.json``
    read through the service (the artifact_loader None sentinel covers
    absent/damaged; the cell-scale stale projection rides the view,
    D16-08/WR-02). The Pilot lanes fabricate frozen
    :class:`DispatchStateView` dataclasses here; 16-05's goldens
    thread fixture views the same way."""
    return dispatch_state.read_dispatch_state(root)


def _gpu_util_bar(utilization_pct: int) -> Text:
    """The lane row's 10-cell segmented utilization bar (16-01): whole-
    cell FLOOR allocation (the ``_strip_bar`` grammar) — filled cells
    the cyan running channel, the remainder the dim ``░`` open channel;
    activity semantics with NO per-threshold recoloring (a fabricated
    warning threshold is a number the probe never provided — UI-SPEC
    Surface A rule 3)."""
    filled = max(0, min(_GPU_BAR_WIDTH,
                        int(utilization_pct * _GPU_BAR_WIDTH / 100)))
    bar = Text()
    if filled:
        bar += Text("█" * filled, style="cyan")
    if filled < _GPU_BAR_WIDTH:
        bar += Text("░" * (_GPU_BAR_WIDTH - filled), style="dim")
    return bar


def _gpu_lane_text(row: "gpu_probe.GpuRow") -> Text:
    """One lane row's content (16-01): the ``MON_GPU_ROW`` data text
    with the utilization bar spliced after the ``GPU {i}`` head (UI-SPEC
    Surface A rule 3 — the constant registers the data-forward wording
    VERBATIM; the bar composes in code over it)."""
    data = S.MON_GPU_ROW.format(
        i=row.index, util=row.utilization_pct, used=row.memory_used_mib,
        total=row.memory_total_mib, temp=row.temperature_c)
    head = f"GPU {row.index}"
    tail = data[len(head):] if data.startswith(head) else f"  {data}"
    return Text.assemble(
        head, "  [", _gpu_util_bar(row.utilization_pct), "]", tail)


class _SeedStateFold:
    """The synthetic fold the right pane's progress line and the [w]
    wide table feed the SHARED ``_entry_progress_cell`` grammar (the
    grammar reads ``.state`` only — the retired ``_RunningFold``
    generalised to the seed's own state)."""

    __slots__ = ("state",)

    def __init__(self, state: str) -> None:
        self.state = state


class MatrixCardsList(ListView):
    """The ``#mon-cards`` list — click suppression (261019-n0w, the
    maintainer's live test): a mouse click on a running card SELECTS
    and FOCUSES it and NEVER opens the RunCellsModal. Textual 8.2.8's
    stock ``_on_list_item__child_clicked`` posts ``Selected`` after
    moving the cursor, and the screen's drill handler treats every
    ``Selected`` as an enter — the defect. This override is the stock
    body MINUS the ``Selected`` post; Enter (the keyboard
    ``action_select`` -> ``Selected`` path) remains the ONLY drill
    trigger. The subclass IS a ListView, so every
    ``query_one("#mon-cards", ListView)`` site resolves unchanged.

    Execution note (Rule 1 — the plan assumed a plain override
    shadows the stock handler; it does NOT): textual's
    ``_get_dispatch_methods`` walks the FULL MRO and invokes the
    naming-convention handler from EVERY class, so the stock body ran
    AFTER this override on the first cut. ``event.prevent_default()``
    is textual's own suppression for exactly that (it breaks the MRO
    walk before the base class yields its handler); ``stop()`` alone
    only stops DOM bubbling. Probe-verified: with both flags the
    Selected post never fires and Enter still drills."""

    def _on_list_item__child_clicked(
            self, event: ListItem._ChildClicked) -> None:
        event.stop()
        event.prevent_default()
        self.focus()
        self.index = self._nodes.index(event.item)


class RunCardTree(Tree):  # type: ignore[type-arg]
    """The Running card's TREE-state widget (261019-pe0, the maintainer's
    2026-10-19 18:14 scalability ruling): one tree per card under the
    card's strip, model nodes at the top level (``show_root=False`` — the
    invisible root is never a cursor target), task nodes as leaves.

    The construction contract (probed textual 8.2.8): ``Tree.__init__``
    takes NO ``auto_expand``/``show_root`` kwargs — they are attribute
    assignments after the super call (``show_root`` is a reactive whose
    watcher resets the cursor, harmless pre-mount).

    CLICK LAW (the n0w MatrixCardsList precedent EXTENDED): a click on a
    tree node's label SELECTS and FOCUSES it and NEVER drills — Enter
    stays the ONLY drill trigger. The stock ``Tree._on_click`` label
    branch sets the cursor then ``run_action("select_cursor")`` (posting
    NodeSelected -> the screen's drill/toggle dispatch), which is exactly
    the misfire this override removes. ``event.stop()`` +
    ``event.prevent_default()`` (BOTH — the n0w MRO lesson: textual's
    ``_get_dispatch_methods`` walks the full MRO and would run the stock
    body after this override; ``prevent_default`` breaks that walk —
    probe-verified in the 261019-pe0 pilot lane). The toggle-ICON branch
    (``meta["toggle"]``) keeps the native behavior (toggle expand only,
    posts nothing). The CardPicked message is the one thing posted: the
    owning screen selects the CARD (the ListView index follows — the one
    card-focus authority). ``auto_expand=False`` neutralizes the stock
    ``_expand_node_on_select`` so ALL expand/collapse flows through the
    screen's explicit calls — one code path for the locked Enter rule.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)
        self.auto_expand = False
        self.show_root = False

    def on_mount(self) -> None:
        """Notify the owning screen the tree is live (261019-pe0): the
        mode-switch render appends the card ListItems asynchronously
        (textual defers the mount — a same-pass ``query_one`` on the
        fresh item finds nothing, probed), so the screen's post-switch
        FOCUS move cannot resolve the tree synchronously. The mount
        notification is the deterministic hook: the screen focuses the
        FOCUSED card's tree when it lands."""
        self.post_message(self.TreeMounted(self))

    class TreeMounted(Message):
        """The tree's mount completed — the screen may now focus it."""

        def __init__(self, tree: "RunCardTree") -> None:
            self.tree = tree
            super().__init__()

    class CardPicked(Message):
        """A label-region click landed on a node: the owning screen
        selects the CARD (the ListView index follows). Never a drill —
        click selects, Enter drills (the locked contract)."""

        def __init__(self, tree: "RunCardTree") -> None:
            self.tree = tree
            super().__init__()

    async def _on_click(self, event: events.Click) -> None:
        meta = event.style.meta
        if "line" not in meta:
            return  # the stock no-op region (no node under the click)
        event.stop()
        event.prevent_default()  # the n0w MRO-walk lesson — BOTH flags
        node = self.get_node_at_line(meta["line"])
        if meta.get("toggle", False):
            # the toggle icon: native behavior ONLY (expand/collapse,
            # posts nothing)
            if node is not None:
                self._toggle_node(node)
            return
        self.focus()
        # CardPicked BEFORE the cursor write: the card select must land
        # ahead of the NodeHighlighted the cursor move posts, so the
        # screen's highlight sync resolves against the CLICKED card (the
        # index is the card-focus authority)
        self.post_message(self.CardPicked(self))
        self.cursor_line = meta["line"]


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

    def _live_started_for(self, root) -> "float | None":
        """The root's live-process start epoch (261020-9vh) — the
        stale-checkpoint guard's evidence leg, read through the SAME
        tolerant-getter idiom as ``_live_evidence``: a launcher without
        ``live_sweep_started`` (every pre-existing fake), a raising
        call, or a non-numeric/non-int-float value reads None — today's
        parse, never a fabricated staleness. The registry's spawn
        moment wins per root; the /proc probe covers CLI-launched
        sweeps (the maintainer's exact case)."""
        if self._launcher is None:
            return None
        getter = getattr(self._launcher, "live_sweep_started", None)
        if getter is None:
            return None
        try:
            starts = getter() or {}
            value = starts.get(str(Path(root).expanduser().resolve()))
        except Exception:  # noqa: BLE001 — the tolerant-reader promise
            return None
        if (isinstance(value, (int, float))
                and not isinstance(value, bool)):
            return float(value)
        return None

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
        it; the delegation lands here with the evidence threading).
        261020-9vh: ``live_started`` threads the root's live-process
        start so a reused root never renders the PREVIOUS run's parsed
        numbers while the live run has not saved its own first
        checkpoint (the all-None drop below)."""
        _live_roots, matrices = self._live_evidence()
        return sweep_monitor.entries_progress(
            root, live_pairs=self._live_pairs_for(root, matrices),
            live_started=self._live_started_for(root))

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

    def launch_from_pairs(self, pairs, seeds, output_root,
                          peft="none", config_variant="none",
                          phrase=None) -> Any:
        """261018-toe: the [e] resume over the materialized-pairs seam
        — delegate to the injected launcher (the launch_from_failures
        adapter twin). Reached through the tolerant getattr seam in the
        resume launch worker (the kill_sweep precedent: deliberately
        NOT declared in the Protocol so the pre-existing launcher fakes
        are never ty-flagged)."""
        if self._launcher is None:
            return None
        return self._launcher.launch_from_pairs(
            pairs, seeds, output_root,
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
                 focus_key: "str | None" = None, **kwargs):
        super().__init__(**kwargs)
        self._root = root
        self._rows = dict(rows)
        self._progress = dict(progress or {})
        # 261019-f0x: the ADDITIVE focus key — when present the modal's
        # cursor pins to that group's row after the row diff (the
        # [enter]-from-the-matrix drill lands on the focused group);
        # every pre-existing construction site passes nothing and opens
        # at row 0 exactly as before
        self._focus_key = focus_key
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
        if self._focus_key is not None and self._focus_key in rows:
            try:
                table.move_cursor(
                    row=table.get_row_index(self._focus_key),
                    animate=False, scroll=False)
            except Exception:  # noqa: BLE001, S110 — the row vanished:
                pass  # the cursor simply stays at row 0 (the mid-diff)
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
    # 261019-f0x: left/right became the matrix-focus movers on the
    # Running tab (action_arrow_horizontal — they still switch tabs on
    # the empty Running tab, with no groups, and on History; Tab always
    # switches) and up/down joined the priority family
    # (action_arrow_vertical — the matrix rows on Running, the focused
    # DataTable's NATIVE cursor actions everywhere else, probed on
    # textual 8.2.8). The ListView's own up/down bindings are thereby
    # superseded: the card selection moves programmatically at the
    # matrix's card edges.
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "row_action", S.ENV_DETAIL_LABEL),
        Binding("left", "arrow_horizontal(-1)", show=False, priority=True),
        Binding("right", "arrow_horizontal(1)", show=False, priority=True),
        Binding("up", "arrow_vertical(-1)", show=False, priority=True),
        Binding("down", "arrow_vertical(1)", show=False, priority=True),
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
        # 261019-f0x: [w] toggled the matrix <-> the wide table; 261019-pe0
        # made it the THREE-STATE cycle over the Running tab's left pane
        # (matrix -> tree -> wide -> matrix — the maintainer's scalability
        # ruling: the f0x matrix cannot hold a real 62x50 sweep). The
        # keycap label stays MON_WIDE_KEYCAP byte-identical (no footer
        # churn); the keycap renders ONLY while the Running tab is active
        # (the _footer_pairs projection, the d/e precedent); on History
        # the key is a silent no-op.
        Binding("w", "cycle_left", S.MON_WIDE_KEYCAP),
        # 261019-pe0 (the locked tree nav contract): [*] toggles
        # expand-ALL / collapse-ALL across EVERY card's tree (any
        # collapsed model -> all expand; else all collapse; a
        # collapsed-away cursor node moves to its model node).
        # Running-tab-effective in TREE mode, silent elsewhere (the
        # d/e/w precedent).
        Binding("*", "tree_toggle_all", S.MON_TREE_TOGGLE_KEYCAP),
        Binding("1", "app.nav(1)", S.NAV_LABEL_ENV, show=False),
        Binding("2", "app.nav(2)", S.NAV_LABEL_SELECTION, show=False),
        Binding("3", "app.nav(3)", S.NAV_LABEL_DATA, show=False),
        Binding("4", "app.nav(4)", S.NAV_LABEL_RUN_CONFIG, show=False),
        Binding("5", "app.nav(5)", S.NAV_LABEL_MONITOR, show=False),
        Binding("6", "app.nav(6)", S.NAV_LABEL_ABOUT, show=False),
    ]

    class FullScanned(Message):
        """The 60s full scan arrived (worker thread -> loop; WR-02):
        the scan result plus each live root's per-root payload.
        261019-o8e/261020-blt: ``plans`` threads the launcher's
        live-sweep planned-CELLS evidence (None = no fresh read — the
        previous screen cache stands; the mount-kick scan is what first
        lands evidence for a fresh screen)."""

        def __init__(self, result: Any, payload: "dict[str, _RootRead]",
                     run_id: int, plans: "dict | None" = None) -> None:
            self.result = result
            self.payload = payload
            self.run_id = run_id
            self.plans = plans
            super().__init__()

    class FrontierScanned(Message):
        """The 2s frontier pass over EVERY live root arrived (worker
        thread -> loop; WR-02) — per-root snapshots/stats/progress.
        261019-o8e/261020-blt: ``plans`` threads the same live-sweep
        planned-CELLS evidence (None = no fresh read — the previous
        screen cache stands). 16-02: ``dispatch`` threads the per-root
        dispatch-state views the SAME way (None = no fresh read — the
        previous ``_dispatch_views`` cache stands)."""

        def __init__(self, snapshots: dict, stats: dict, progress: dict,
                     run_id: int, plans: "dict | None" = None,
                     dispatch: "dict | None" = None) -> None:
            self.snapshots = snapshots
            self.stats = stats
            self.progress = progress
            self.run_id = run_id
            self.plans = plans
            self.dispatch = dispatch
            super().__init__()

    class GpuProbed(Message):
        """The GPU probe pass arrived (worker thread -> loop; 16-01 +
        the WR-02 run tag): the frozen rows tuple sorted by index
        (D16-04), ``()`` = zero GPUs (the explicit empty state), or
        ``None`` = the ONE absent outcome every failure mode shares
        (D16-02 — the panel renders the honest note, never a crash)."""

        def __init__(self, rows: "tuple[gpu_probe.GpuRow, ...] | None",
                     run_id: int) -> None:
            self.rows = rows
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
        261018-kvj — the LogTailModal read-once precedent). 261019-f0x:
        ``focus_key`` threads the focused group's row to the modal."""

        def __init__(self, root: str, cells: Any, progress: dict,
                     focus_key: "str | None" = None) -> None:
            self.root = root
            self.cells = cells
            self.progress = dict(progress or {})
            self.focus_key = focus_key
            super().__init__()

    class RerunPreflightDone(Message):
        """The re-run preflight verdict arrived (worker -> loop).
        261018-toe: ``resume`` routes the post-preflight launch — False
        (the default, every existing post site) is the [f]->[r]
        failures path; True is the [e] resume path."""

        def __init__(self, verdict, root: str, run_id: int,
                     resume: bool = False) -> None:
            self.verdict = verdict
            self.root = root
            self.run_id = run_id
            self.resume = resume
            super().__init__()

    class RerunFinished(Message):
        """The re-run launch outcome arrived (worker -> loop).
        261018-toe: ``resume`` flags the [e] path so the shared outcome
        handler renders MON_RESUME_TOAST and the E2' phrase re-prompt
        routes back through the RESUME launch worker."""

        def __init__(self, outcome, root: str, run_id: int,
                     resume: bool = False) -> None:
            self.outcome = outcome
            self.root = root
            self.run_id = run_id
            self.resume = resume
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

    class RightTailRead(Message):
        """The D right pane's tail read arrived (worker thread -> loop;
        261019-f0x — the LogTailModal TailRead precedent): the bounded
        tee lines plus the mon-tail stage id (a superseded focus's late
        lines drop, the WR-02 idiom)."""

        def __init__(self, lines: tuple, run_id: int) -> None:
            self.lines = lines
            self.run_id = run_id
            super().__init__()

    def __init__(self,
                 monitor_service: "MonitorServiceProtocol | None" = None,
                 launcher_service: "MonitorLauncherProtocol | None" = None,
                 frontier_interval: float = FRONTIER_INTERVAL_SECONDS,
                 full_interval: float = FULL_INTERVAL_SECONDS,
                 session: "MonitorSession | None" = None,
                 gpu_probe_provider: "GpuProbeProvider | None" = None,
                 dispatch_state_reader: "DispatchStateReader | None" = None,
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
        # 16-01 (TUI-01): the GPU probe provider — constructor-
        # injectable so the Pilot/golden lanes fabricate frozen GpuRow
        # dataclasses (CI zero-GPU, D16-14 — the _golden_app
        # constructor-injection shape); None means the REAL nvidia-smi
        # probe (D16-01). The composition root threads it through
        # build_monitor_screen (the 261018-08g rebuild-per-navigation
        # discipline: the seam lives on the screen constructor, the app
        # supplies it).
        self._gpu_probe_provider: GpuProbeProvider = (
            gpu_probe_provider if gpu_probe_provider is not None
            else _default_gpu_probe_provider)
        # 16-02 (TUI-03, D16-06): the dispatch-state reader — the SAME
        # constructor-injection shape (the 16-01 gpu-probe provider
        # seam): None means the REAL tolerant frozen-v2 read of
        # ``{root}/dispatch_state.json``; the Pilot lanes fabricate
        # frozen DispatchStateView dataclasses and 16-05's goldens
        # thread fixture views through the composition root.
        self._dispatch_state_reader: DispatchStateReader = (
            dispatch_state_reader if dispatch_state_reader is not None
            else _default_dispatch_state_reader)
        # the per-root dispatch views ({root: DispatchStateView | None})
        # — stored by the frontier pass BEFORE the render that reads it
        # (the o8e evidence-first ordering); a None entry = NO block;
        # the vanished-root degradation drops entries with the others
        self._dispatch_views: dict = {}
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
        # 261019-o8e + 261020-blt: the LIVE-SWEEP planned-CELLS evidence
        # — the launcher's live_sweep_plans() read (resolved root ->
        # (pairs frozenset, seeds tuple | None) | None), stored by BOTH
        # cadence handlers BEFORE the render pass that consumes it (see
        # the handler comments); {} = fresh-but-empty evidence
        # (fallback); a root's None entry = live-but-unknown
        self._live_plans: dict = {}
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
        # 261019-f0x: the matrix group focus — (row, col) relative to
        # the FOCUSED card (the ListView index IS the card focus);
        # clamped on every render against the merged matrix shape
        self._focus_pos: tuple[int, int] | None = None
        # 261019-f0x: the D right pane's content-signature gates (the
        # _history_sig precedent) + the mon-tail worker's stage id (the
        # WR-02 idiom — a superseded focus's late lines drop)
        self._right_detail_sig: tuple | None = None
        self._right_tail_sig: tuple | None = None
        self._tail_stage_id = 0
        # 261019-f0x Task 3 + 261019-pe0: the left pane's MODE MACHINE —
        # [w] cycles matrix -> tree -> wide -> matrix (the effective mode
        # always valid; "wide" is reachable ONLY through a manual cycle —
        # auto derives matrix/tree alone). The manual hold window:
        # ``_left_mode_user`` (None = auto) holds until the per-card
        # STRUCTURE tuple changes (card set / model or task set / narrow
        # flip) or a remount — ``_left_mode_struct_sig`` detects the
        # change and resets the choice to auto. ``_tree_sigs`` /
        # ``_tree_expand`` / ``_tree_cursor`` are the per-action-root
        # tree gate-law caches (structure sig / expansion map / cursor
        # node key — they survive the ListItem rebuilds that destroy the
        # widget state, preserving the operator's tree exactly).
        self._left_mode = "matrix"
        self._left_mode_user: str | None = None
        self._left_mode_struct_sig: tuple | None = None
        self._tree_sigs: dict[str, tuple] = {}
        self._tree_expand: dict[str, dict[str, bool]] = {}
        self._tree_cursor: dict[str, tuple] = {}
        # the wide table's rendered-content signature
        self._wide_sig: tuple | None = None
        # 16-01: the G panel's probe state + render gate — ``_gpu_rows``
        # holds the LAST probe outcome (_GPU_PENDING before the first
        # probe message lands; None = absent; () = zero GPUs; otherwise
        # the sorted frozen rows), ``_gpu_sig`` is the rze-law sentinel
        # over (probe-state note, row count, the FULL formatted per-row
        # values — Pitfall 5), and ``_gpu_run_id`` tags the probe posts
        # (the WR-02 idiom — a superseded worker's late post drops).
        self._gpu_rows: Any = _GPU_PENDING
        self._gpu_sig: tuple | None = None
        self._gpu_run_id = 0

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

    @property
    def _wide(self) -> bool:
        """The [w] cycle's wide leg (261019-pe0): a READ-ONLY projection
        over the mode machine — every pre-existing ``_wide`` read site
        (the wide render/visibility/focus/arrow branches + the pilot
        asserts) stays byte-unchanged; writes go through the mode
        machine (``_left_mode``), never here."""
        return self._left_mode == "wide"

    # ===== compose / mount =====

    def compose(self) -> ComposeResult:
        """The two-tab frame (#41 optimistic paint): nav bars, the
        title bar (the cadence note right-aligned — standing chrome,
        D-09, byte-unchanged for the pty lane's monitor marker), the
        one-row tab header with (n) count badges, ONE content region —
        the 261019-f0x B+D horizontal split: ``#mon-left`` (1fr, the
        existing children verbatim) beside ``#mon-right`` (40, the D
        right pane's ``#mon-detail`` + ``#mon-right-log`` placeholders;
        display toggled in code) — and the bottom bar. The scanning
        note renders at mount BEFORE any scan lands — skeleton + note
        only, never a fabricated row."""
        yield TopMenuBar()
        with Horizontal(id="mon-title-bar"):
            yield Label(S.MON_SCREEN_TITLE, id="mon-screen-title")
            yield Label(S.MON_SCAN_NOTE, id="mon-scan-note")
        with Horizontal(id="mon-tab-header"):
            yield Label("", id="mon-tab-running", classes="mon-tab")
            yield Label("", id="mon-tab-history", classes="mon-tab")
        with Horizontal(id="mon-content"):
            with Vertical(id="mon-left"):
                yield Static("", id="mon-scanning-note")
                yield Static("", id="mon-running-empty")
                yield MatrixCardsList(id="mon-cards")
                yield DataTable(id="mon-wide")
                yield DataTable(id="mon-history")
                yield Static("", id="mon-history-empty")
            with Vertical(id="mon-right"):
                yield Static("", id="mon-detail")
                yield RichLog(id="mon-right-log", max_lines=200,
                              markup=False, wrap=False)
        # 16-01 (TUI-01, D16-05): the standing G GPU-lanes panel — a
        # full-width section under the tab content, visible on BOTH
        # tabs (GPU state is machine-level, never run-level), above the
        # bottom bar. The header row paints at mount (title + BLANK
        # note); the lanes land with the first probe message (the #41
        # optimistic-paint law — never a guessed lane). Display-only
        # chrome: the lane region's can_focus clears in on_mount (the
        # #mon-right-log precedent) and no keybinding exists.
        with Vertical(id="mon-gpu"):
            with Horizontal(id="mon-gpu-header"):
                yield Label(S.MON_GPU_TITLE, id="mon-gpu-title")
                yield Label("", id="mon-gpu-note")
            yield VerticalScroll(id="mon-gpu-lanes")
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
        # the stale language. 261019-f0x: every NEW sentinel (the
        # strip/matrix cards sig carries the focus, the right pane's
        # detail/tail sigs, the wide table's sig) resets with them.
        # 261019-pe0: the mode machine's sentinels reset too — the
        # L-toggle recompose lands AUTO-MODE (the manual choice dies
        # with the remount) and the tree gate-law caches clear so the
        # fresh widgets rebuild from scratch.
        self._tabs_sig = None
        self._scan_note_shown = None
        self._cards_sig = None
        self._history_sig = None
        self._right_detail_sig = None
        self._right_tail_sig = None
        self._wide_sig = None
        # 16-01: the G panel's sentinel resets with them — the
        # recomposed panel (fresh empty Labels) repaints from the
        # last-known probe rows in the fresh language, never gates away
        self._gpu_sig = None
        self._left_mode = "matrix"
        self._left_mode_user = None
        self._left_mode_struct_sig = None
        self._tree_sigs = {}
        self._tree_expand = {}
        self._tree_cursor = {}
        # the pane's RichLog is display-only (never focusable — every
        # key stays screen-level, no focus trap)
        self.query_one("#mon-right-log", RichLog).can_focus = False
        # 16-01: the G panel is display-only standing chrome (the same
        # precedent — the panel never joins the focus chain)
        self.query_one("#mon-gpu-lanes", VerticalScroll).can_focus = False
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
        # 261019-f0x Task 3: the [w] wide table's setup (display stays
        # code-controlled — hidden until the toggle)
        wide = self.query_one("#mon-wide", DataTable)
        wide.cursor_type = "row"
        wide.zebra_stripes = True
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
        """Re-derive the width mode (the bar/state-word degradation and
        the 261019-f0x pane visibility — a width crossing re-kicks the
        tail after the render)."""
        narrow = self.size.width < _NARROW_WIDTH
        if narrow != self._narrow:
            self._narrow = narrow
            self._render_all()
            self._kick_right_tail()

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

    def _read_live_plans(self) -> "dict | None":
        """The launcher's live-sweep planned-CELLS evidence — resolved
        root -> (pairs frozenset, seeds tuple | None) | None — read
        WORKER-side (off the event loop; the ``_entries_progress_of``
        getattr precedent). Reader PRECEDENCE (261020-blt):
        ``live_sweep_plans`` first; a launcher without it (every o8e
        fake and every pre-blt double) falls back to the o8e ADAPTER
        over ``live_sweep_matrices`` — a bare frozenset value becomes
        the seeds-UNKNOWN plan ``(value, None)`` (the pairs-only filter
        applies with NO seed completion: the o8e render byte-identical,
        which is why the o8e pins stay green), and None / non-frozenset
        garbage stays None. No method at all, or any RAISING call,
        reads None = "no fresh evidence, keep the previous screen
        cache" (the tolerant-reader promise); a dict — even {} — IS
        fresh evidence (an empty dict scopes nothing: every root falls
        back root-wide)."""
        plans_getter = getattr(self._launcher, "live_sweep_plans", None)
        if plans_getter is not None:
            try:
                return dict(plans_getter() or {})
            except Exception:  # noqa: BLE001 — the tolerant-reader promise
                return None
        legacy = getattr(self._launcher, "live_sweep_matrices", None)
        if legacy is None:
            return None
        try:
            return {
                root: ((value, None)
                       if isinstance(value, frozenset) else None)
                for root, value in dict(legacy() or {}).items()}
        except Exception:  # noqa: BLE001 — the tolerant-reader promise
            return None

    @work(exclusive=True, thread=True, group="mon-full")
    def _run_full_scan(self, run_id: int) -> None:
        """The full scan + EVERY live root's stats/cells/progress/
        resume/scale read — all off the event loop (T-11-07-01/04).
        Per-root tolerant: a root whose read raises is skipped (the
        per-file skip idiom), the other roots still land.
        261019-o8e: the live-plans read sits BEFORE the try (it never
        raises) so an evidence failure can never mask a scan."""
        plans = self._read_live_plans()
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
        self.post_message(self.FullScanned(result, payload, run_id,
                                           plans))

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
        stays armed, the degradation-sweep contract).

        16-01 (16-RESEARCH Pitfall 1): the GPU probe dispatch fires
        BEFORE the live-root guard — GPU state is MACHINE-level, so the
        G panel probes on an idle machine too (its own exclusive
        worker group, never inside the live-root pass)."""
        self._tick_gpu()
        if not self._live:
            return
        self._frontier_run_id += 1
        self._run_frontier(self._frontier_run_id)

    def _tick_gpu(self) -> None:
        """Dispatch the G panel's probe worker (16-01, D16-03): its OWN
        exclusive ``mon-gpu`` group (the 10-04 per-group lesson — a
        shared group would cancel the frontier pass), one worker per
        frontier tick, never an inline probe."""
        self._gpu_run_id += 1
        self._run_gpu_probe(self._gpu_run_id)

    @work(exclusive=True, thread=True, group="mon-gpu", exit_on_error=False)
    def _run_gpu_probe(self, run_id: int) -> None:
        """The probe pass (worker thread -> loop): call the provider
        under the ~2s per-call timeout and post the run-tagged outcome
        (WR-02). The service never raises and neither does the worker
        (the worker-guard discipline — an absent render, never a
        crash)."""
        try:
            rows = self._gpu_probe_provider(gpu_probe.PROBE_TIMEOUT_SECONDS)
        except Exception:  # noqa: BLE001 — the tolerant-provider promise
            rows = None
        self.post_message(self.GpuProbed(rows, run_id))

    @work(exclusive=True, thread=True, group="mon-frontier",
          exit_on_error=False)
    def _run_frontier(self, run_id: int) -> None:
        """The light 2s pass over EVERY live root in the SAME exclusive
        worker (frontier_scan + stats + entries_progress per root; the
        elapsed accrues continuously, D-17) — all off the event loop,
        per-root tolerant. 261019-o8e: the live-plans read rides the
        same pass (once, at the top — never raises). 16-02 (UI-SPEC B
        rule 7): the dispatch-state read rides the SAME pass too — ONE
        additional service read per live root, no new timer, no new
        worker group."""
        plans = self._read_live_plans()
        snapshots: dict = {}
        stats_map: dict = {}
        progress_map: dict = {}
        dispatch_map: dict = {}
        for root in sorted(self._live):
            dispatch_map[root] = self._read_dispatch_state(root)
            read = self._read_frontier_root(root)
            if read is None:
                continue
            snapshot, stats, progress = read
            snapshots[root] = snapshot
            stats_map[root] = stats
            progress_map[root] = progress
        self.post_message(self.FrontierScanned(
            snapshots, stats_map, progress_map, run_id, plans,
            dispatch_map))

    def _read_dispatch_state(
            self, root: str) -> "dispatch_state.DispatchStateView | None":
        """One live root's dispatch-state view (16-02): the tolerant
        read through the injectable seam; ANY failure (absent file,
        damaged JSON, a raising reader) reads None — NO block, never a
        crash (the worker-guard discipline)."""
        try:
            return self._dispatch_state_reader(root)
        except Exception:  # noqa: BLE001 — the tolerant-reader promise
            return None

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
        # 261019-o8e: the evidence lands BEFORE any state mutation or
        # render — the render pass and its structure signature must
        # read the SAME evidence dict (a store-after-render would flap
        # one tick: the sig computed root-wide, the paint filtered)
        if message.plans is not None:
            self._live_plans = message.plans
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
        # card leaves; its History row carries the fresh scan state;
        # 16-02: the dispatch views drop with them)
        for cache in (self._root_stats, self._cell_rows,
                      self._cell_progress, self._resumes, self._scales,
                      self._dispatch_views):
            for stale in [key for key in cache if key not in live]:
                del cache[stale]
        self._scanning = False
        self._render_all()
        self._focus_active()
        # 261019-f0x: cards landing/leaving flips the pane's visibility —
        # kick the tail state so the first card's pane paints with the
        # scan (the no-tee state renders inline, a tee schedules the
        # mon-tail read)
        self._kick_right_tail()
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
        # 261019-o8e: same load-bearing ordering as the full-scan
        # handler — the evidence stores BEFORE the render that reads it
        if message.plans is not None:
            self._live_plans = message.plans
        # 16-02: the dispatch views land the same evidence-first way
        # (the structure signature's dispatch legs and the painted
        # block must read the SAME dict — the o8e flap rule)
        if message.dispatch is not None:
            self._dispatch_views = message.dispatch
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
        # 261019-f0x (b): the pane's tail rides the 2s frontier cadence
        # while it is visible and a tee exists (the mon-tail worker —
        # its OWN exclusive group, the LogTailModal mon-logtail
        # precedent; the frontier worker itself is untouched)
        self._kick_right_tail()

    def on_monitor_screen_gpu_probed(self, message: GpuProbed) -> None:
        """Store the probe outcome and render the G panel (a run-id
        mismatch drops the superseded post — WR-02; the panel itself is
        content-signature gated inside the render)."""
        if message.run_id != self._gpu_run_id:
            return
        self._gpu_rows = message.rows
        self._render_gpu_panel()

    def _render_gpu_panel(self) -> None:
        """The G GPU-lanes panel render (16-01, the rze law): the pass
        is content-signature gated over (probe-state note, row count,
        the FULL formatted per-row values — 16-RESEARCH Pitfall 5) so a
        steady tick over unchanged readings performs ZERO widget writes
        (the pty byte-silence pin), suppressed while a modal is stacked
        (the ``_render_all`` early-return); ``on_mount`` resets the
        sentinel so the L-toggle recompose repaints.

        States (UI-SPEC Surface A rule 5, all explicit): pending ->
        header row only (note blank, zero lanes); absent -> the
        ``MON_GPU_ABSENT`` note with ZERO lanes (never fabricated
        lanes, never a crash); zero GPUs -> exactly ONE
        ``MON_GPU_NONE`` lane row; otherwise one lane row per GPU
        (already sorted by index — D16-04)."""
        if not self.is_running:
            return
        if self.app.screen is not self:
            return  # a modal or the min-size guard is stacked above
        rows = self._gpu_rows
        if rows is _GPU_PENDING:
            note = ""
            lanes: tuple[Text, ...] = ()
        elif rows is None:
            note = S.MON_GPU_ABSENT
            lanes = ()
        elif not rows:
            note = ""
            lanes = (Text(S.MON_GPU_NONE),)
        else:
            note = ""
            lanes = tuple(_gpu_lane_text(row) for row in rows)
        previous = self._gpu_sig
        lane_texts = tuple(lane.plain for lane in lanes)
        sig = (note, lane_texts)
        if sig == previous:
            return  # unchanged readings: nothing to paint (Pitfall 5)
        self._gpu_sig = sig
        # each region writes ONLY on its own leg's change — a value
        # change re-renders the lanes but never touches a healthy note;
        # a pending -> absent flip updates the note alone (16-01 Task 4)
        if previous is None or previous[0] != note:
            self.query_one("#mon-gpu-note", Label).update(
                note, layout=False)
        if previous is not None and previous[1] == lane_texts:
            return  # only the note changed — the lane region stands
        region = self.query_one("#mon-gpu-lanes", VerticalScroll)
        region.remove_children()
        if lanes:
            region.mount(*[
                Label(lane, classes="mon-gpu-lane") for lane in lanes])

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

    def _focused_card(self) -> "_RunCard | None":
        """The FOCUSED card — the ListView index IS the card focus
        (clamped to the card list; None when no cards)."""
        cards = self._cards()
        if not cards:
            return None
        index = self.query_one("#mon-cards", ListView).index
        if index is None:
            index = 0
        return cards[max(0, min(index, len(cards) - 1))]

    def _focused_group(self) -> "tuple | None":
        """The focused card's focused (card, model, task, CellRow)
        group — ``(row, col)`` resolved through the ListView index and
        the merged row map, CLAMPED against the matrix shape (a
        vanished row/col clamps to the last valid position; an empty
        matrix resolves None)."""
        card = self._focused_card()
        if card is None:
            return None
        rows = self._card_rows(card)
        models = sorted({row.model for row in rows.values()})
        if not models:
            return None
        row_index, col_index = self._focus_pos or (0, 0)
        row_index = max(0, min(row_index, len(models) - 1))
        model = models[row_index]
        tasks = sorted({row.task for row in rows.values()
                        if row.model == model})
        col_index = max(0, min(col_index, len(tasks) - 1))
        row = rows.get(f"{model}__{tasks[col_index]}")
        if row is None:
            return None
        return card, model, tasks[col_index], row

    def _normalize_focus(self) -> None:
        """Write the CLAMPED focus back (the stored position follows
        the matrix shape — a vanished row/col clamps to the last valid
        position, an empty matrix clears it)."""
        focused = self._focused_group()
        if focused is None:
            self._focus_pos = None
            return
        card, model, task, _row = focused
        rows = self._card_rows(card)
        models = sorted({row.model for row in rows.values()})
        tasks = sorted({row.task for row in rows.values()
                        if row.model == model})
        self._focus_pos = (models.index(model), tasks.index(task))

    def _cards_struct_legs(self, cards: "list[_RunCard]") -> tuple:
        """The per-card STRUCTURE legs (261019-pe0): the ``_cards_signature``
        loop body WITHOUT the index/focus/mode legs — the exact tuple the
        mode machine's hold-check watches (a change here resets the manual
        [w] choice to auto: card set / model or task set / narrow flip /
        resume-note presence / base_live). 16-02: the dispatch legs
        (has-block, worker count, stale flag — Pitfall 6) join so a
        dispatch card's label-count changes rebuild while value-only
        changes ride the in-place refresh."""
        per_card = []
        for card in cards:
            rows = self._card_rows(card)
            per_card.append((
                tuple(card.roots), card.roots[0] == card.base,
                self._resumes.get(card.roots[0], 0) > 0, self._narrow,
                tuple(sorted({row.model for row in rows.values()})),
                tuple(sorted({row.task for row in rows.values()})),
                self._dispatch_structure_legs(self._card_dispatch(card))))
        return tuple(per_card)

    def _card_dispatch(self, card: "_RunCard"
                       ) -> "dispatch_state.DispatchStateView | None":
        """The card's dispatch-state view (16-02): the PRIMARY root's
        read — a dispatch run writes ONE shared root (its card is
        single-root by the ``-mgpu-w{i}`` grouping); static/CLI sweep
        roots and worker roots carry no ``dispatch_state.json`` so
        their cards read None and render NO block (byte-identical to
        today — UI-SPEC B rule 5)."""
        return self._dispatch_views.get(card.roots[0])

    @staticmethod
    def _dispatch_structure_legs(
            view: "dispatch_state.DispatchStateView | None") -> tuple:
        """The dispatch block's STRUCTURE legs (16-02, Pitfall 6): the
        block's presence, the worker-row count, and the stale/malformed
        row's presence — the LABEL-COUNT-changing inputs ONLY. A
        value-only change (counts moving, a worker flipping busy to
        idle) is deliberately absent so it rides the in-place label
        refresh and the ListItem/cursor identity survives."""
        if view is None:
            return (False, 0, False)
        return (True, len(view.workers),
                bool(view.stale or view.malformed))

    def _cards_signature(self, cards: "list[_RunCard]") -> tuple:
        """The STRUCTURE signature (261018-rze c + 261019-f0x): per
        card the roots identity/order, base_live, the resume-note
        presence, the narrow mode, and the MERGED MATRIX SHAPE (the
        models/tasks tuples — everything label-count/order-changing),
        PLUS the focus tuple and the focused card index (a focus move
        repaints the highlight — structural for the two affected rows,
        still zero ListView churn via ``_repaint_focus_move``).
        261019-pe0: the EFFECTIVE MODE joins as the final leg — a mode
        switch flips the card's widget shape (strip+resume+matrix Labels
        vs strip+resume+RunCardTree) and MUST force the rebuild."""
        index = self.query_one("#mon-cards", ListView).index
        return (self._cards_struct_legs(cards), index, self._focus_pos,
                self._left_mode)

    def _matrix_width_budget(self) -> int:
        """The left pane's matrix width budget (261019-pe0): the DOM read
        (``#mon-left``'s container width) capped by the screen-width
        arithmetic (``width - 40`` on the wide grid where ``#mon-right``
        holds its 40-col allocation, the full width when narrow —
        tui/styles.tcss). The cap is LOAD-BEARING (probe-pinned): at the
        FIRST scan paint the pane's display flip has not re-laid-out yet,
        so the DOM read still reflects the pane-hidden stretch (~120
        cells at the wide grid) and would admit a matrix that overflows
        the moment the layout catches up — the cap projects the budget
        the pane WILL claim. A failed/non-positive DOM read (the
        pre-layout on_mount window) takes the arithmetic alone."""
        cap = max(0, self.size.width - (0 if self._narrow else 40))
        try:
            width = self.query_one("#mon-left").container_size.width
            if width and width > 0:
                return min(width, cap)
        except Exception:  # noqa: BLE001, S110 — pre-layout: the
            # arithmetic cap below covers the window
            pass
        return cap

    def _card_matrix_overflows(self, card: _RunCard) -> bool:
        """261019-pe0: does the card's f0x matrix exceed the pane's width
        budget? ``needed = the name column + every task column`` over the
        SAME merged row map the matrix renders (the o8e filter applies
        for free). NARROW never overflows — the narrow matrix is
        per-model COUNT rows (no task columns at all; the tree solves a
        column-count problem), and the narrow leg of the structure
        signature already resets the manual mode on the flip."""
        if self._narrow:
            return False
        rows = self._card_rows(card)
        tasks = sorted({row.task for row in rows.values()})
        if not tasks:
            return False
        needed = _MATRIX_NAME_WIDTH + sum(
            _matrix_col_width(task) for task in tasks)
        return needed > self._matrix_width_budget()

    def _derive_left_mode(self) -> str:
        """The EFFECTIVE left-pane mode (261019-pe0): the manual [w]
        choice when one holds, else the AUTO default — tree iff ANY
        card's matrix overflows the pane budget, matrix otherwise. A
        PURE function of (the task sets, the width): unchanged inputs
        can never flip the mode between ticks (T-pe0-02), and "wide" is
        reachable only through the manual cycle, never auto."""
        if self._left_mode_user is not None:
            return self._left_mode_user
        cards = self._cards()
        return ("tree" if any(self._card_matrix_overflows(card)
                              for card in cards) else "matrix")

    def _repaint_focus_move(self) -> None:
        """A focus-only change (the arrow movers land here): the shared
        builder repaints the two affected matrix-row Labels IN PLACE
        (``_refresh_card_labels`` — content comparison, zero ListView
        churn) and the new focus folds into the structure signature so
        the next cadence render is a clean no-op; a count mismatch
        routes to the proven rebuild path (never a crash). The D right
        pane follows immediately: the detail repaints from the caches,
        the tail re-kicks (within one mon-tail round trip)."""
        cards = self._cards()
        if self._refresh_card_labels(cards):
            self._cards_sig = self._cards_signature(cards)
        else:
            self._render_cards(cards)
        self._render_right_detail()
        self._kick_right_tail()

    # ===== the D right pane (261019-f0x Task 2) =====

    def _pane_visible(self) -> bool:
        """The pane shows iff wide grid + Running tab + cards exist (a
        display-only region — never focusable, no focus trap)."""
        return (not self._narrow and self._active_tab == "running"
                and bool(self._card_order))

    def _right_detail_lines(self) -> "list[Text]":
        """The focused group's detail lines from EXISTING service data
        ONLY — the approved D composition: the model x task header,
        then (when the group's progress parses) the 20-cell progress
        BAR line (filled/open cells + the integer percent + the derived
        rate) and the STEP/ETA line (step/max + the point ETA with its
        wall-clock landing, or the honest dash), then one line per seed
        (the state glyph word, re-derived at call time — CR-01) with
        the running seed's steps/percent/eta over the SHARED progress
        grammar. NO loss/lr/epoch/context/params line ever renders:
        those live in the log, which the pane SHOWS (T-f0x-02 — no
        underived field is ever stated)."""
        focused = self._focused_group()
        if focused is None:
            return []
        card, model, task, row = focused
        width = 40
        try:
            width = max(
                8, self.query_one("#mon-detail", Static).container_size
                .width or 40)
        except Exception:  # noqa: BLE001 — pre-layout: the CSS width
            width = 40
        header = Text(f"{model} × {task}", style="bold cyan")
        header.truncate(width, overflow="ellipsis", pad=False)
        lines = [header]
        # 261019-pe0: the group progress resolution lives in
        # ``_group_progress`` (shared with the tree's task labels)
        progress = self._group_progress(card, model, task)
        accent = str(self.app.current_theme.accent)
        if progress is not None:
            # (a) the D bar line — 20 cells at the strip's bar width
            # (the _entry_progress_cell rounding idiom), then the
            # percent + the derived rate (the variant-D filled/open
            # shapes)
            filled = max(0, min(_BAR_WIDTH,
                                round(progress.percent * _BAR_WIDTH / 100)))
            bar = Text("█" * filled, style=accent)
            bar += Text("░" * (_BAR_WIDTH - filled), style="dim")
            bar += Text("  ")
            bar += Text(f"{progress.percent}%")
            bar += Text("  ")
            rate = _rate_of(progress)
            bar += (Text(S.MON_STRIP_RATE.format(rate=rate))
                    if rate is not None else Text(_DASH, style="dim"))
            lines.append(bar)
            # (b) the step/ETA line — step/max + the ETA leg mirroring
            # the strip's point grammar (wall clock over the module
            # time — golden-freezable, the strip's single-read
            # convention). The RANGE leg can never occur here: one
            # CellProgress object resolves, so point or dash only.
            if progress.step is not None and progress.max_steps is not None:
                step = Text(S.MON_DETAIL_STEPS.format(
                    step=progress.step, max=progress.max_steps))
                step += Text("  ")
                if progress.eta_seconds is not None:
                    step += Text(S.MON_STRIP_ETA.format(
                        eta=format_eta(progress.eta_seconds),
                        clock=time.strftime(
                            "%H:%M", time.localtime(
                                time.time() + progress.eta_seconds))))
                else:
                    step += Text(_DASH, style="dim")
                lines.append(step)
        for cell_seed in sorted(row.seeds, key=lambda s: s.seed):
            copy, _style = _cell_state_cells().get(
                cell_seed.state, (cell_seed.state, _STYLE_DIM))
            line = Text(f"{S.MON_COL_SEED.format(seed=cell_seed.seed)} ",
                        style="dim")
            line += Text(copy, style=_MATRIX_GLYPH_STYLES.get(
                cell_seed.state, "dim"))
            if (cell_seed.state == CELL_RUNNING
                    and progress is not None):
                line += Text(" ")
                line += _entry_progress_cell(
                    _SeedStateFold(CELL_RUNNING), progress, False, accent)
                rate = _rate_of(progress)
                line += Text(" ")
                line += (Text(S.MON_STRIP_RATE.format(rate=rate))
                         if rate is not None
                         else Text(_DASH, style="dim"))
            lines.append(line)
        return lines

    def _render_right_detail(self) -> None:
        """Paint the detail region — the lines-signature gate (the
        _history_sig precedent): an unchanged detail performs ZERO
        writes on the cadence (the #mon-detail CSS height bounds the
        region; content truncates, never reflows the pane)."""
        if not self.is_running:
            return
        if not self._pane_visible():
            return
        lines = self._right_detail_lines()
        if not lines:
            return
        sig = tuple(line.plain for line in lines)
        if sig == self._right_detail_sig:
            return
        self._right_detail_sig = sig
        detail = self.query_one("#mon-detail", Static)
        joined = Text()
        for index, line in enumerate(lines):
            if index:
                joined += Text("\n")
            joined += line
        detail.update(joined)

    def _tee_for_card(self, card: "_RunCard | None") -> "str | None":
        """The card's tee — ``tee_path_for`` over the card's roots,
        first non-None (worker groups resolve their worker tee;
        CLI-launched roots return None everywhere)."""
        if card is None:
            return None
        for root in card.roots:
            tee = self._launcher.tee_path_for(root)
            if tee is not None:
                return str(tee)
        return None

    def _kick_right_tail(self) -> None:
        """One tail kick (the pane-visible gate inside): a card with a
        tee schedules the mon-tail read (stage-id tagged); no tee
        renders the designed unavailable state ONCE (sig-gated) and
        NEVER schedules a read — the [t] modal's contract."""
        if not self.is_running or not self._pane_visible():
            return
        tee = self._tee_for_card(self._focused_card())
        if tee is None:
            sig = ("no-tee",)
            if sig != self._right_tail_sig:
                self._right_tail_sig = sig
                log = self.query_one("#mon-right-log", RichLog)
                log.clear()
                log.write(Text(S.MON_LOG_UNAVAILABLE, style="dim"))
            return
        self._tail_stage_id += 1
        self._read_right_tail(tee, self._tail_stage_id)

    @work(exclusive=True, thread=True, group="mon-tail",
          exit_on_error=False)
    def _read_right_tail(self, tee: str, run_id: int) -> None:
        """One bounded tail read OFF the event loop (WR-03-wrapped: a
        raising read posts nothing — the last-good lines stand; the
        [t] modal's tolerant-refresh precedent)."""
        try:
            lines = self._service.read_log_tail(tee, max_lines=30)
        except Exception:  # noqa: BLE001 — tolerant refresh
            return
        self.post_message(self.RightTailRead(tuple(lines or ()), run_id))

    def on_monitor_screen_right_tail_read(
            self, message: RightTailRead) -> None:
        """The tail lines arrived: drop superseded stages (WR-02), skip
        the write beneath a stacked modal (the read already happened —
        the next tick catches up), gate on the lines signature (the
        tee + the lines: unchanged content performs ZERO RichLog
        calls), changed lines clear + rewrite in order (plain dim
        verbatim log data, markup=False)."""
        if message.run_id != self._tail_stage_id:
            return
        if self.app.screen is not self:
            return  # modal suppression — the base surface stays still
        tee = self._tee_for_card(self._focused_card())
        if tee is None:
            return
        sig = (tee, *message.lines)
        if sig == self._right_tail_sig:
            return
        self._right_tail_sig = sig
        log = self.query_one("#mon-right-log", RichLog)
        log.clear()
        log.write(Text(S.MON_LOG_TEE_LINE.format(path=tee),
                       style="dim"))
        for line in message.lines:
            log.write(Text(str(line), style="dim"))

    def _move_focus_col(self, delta: int) -> None:
        """←/→ on the matrix: move the focused column within its row,
        CLAMPED at the row edges — no tab-switch at the edges (Tab is
        the switcher)."""
        focused = self._focused_group()
        if focused is None:
            return
        _card, model, task, _row = focused
        rows = self._card_rows(focused[0])
        models = sorted({row.model for row in rows.values()})
        tasks = sorted({row.task for row in rows.values()
                        if row.model == model})
        col_index = max(0, min(
            tasks.index(task) + delta, len(tasks) - 1))
        self._focus_pos = (models.index(model), col_index)
        self._repaint_focus_move()

    def _move_focus_row(self, delta: int) -> None:
        """↑/↓ on the matrix: move the focused model row; at the
        card's edge CROSS to the adjacent card (the ListView index
        follows programmatically, carrying the focus to its first/last
        row — the column carries). With cards but no groups the arrows
        stay alive by moving the CARD selection (the ListView's native
        semantics); with no cards they no-op."""
        cards = self._cards()
        if not cards:
            return
        focused = self._focused_group()
        if focused is None:
            list_view = self.query_one("#mon-cards", ListView)
            current = list_view.index if list_view.index is not None else 0
            list_view.index = max(0, min(current + delta,
                                         len(cards) - 1))
            return
        card, model, task, _row = focused
        rows = self._card_rows(card)
        models = sorted({row.model for row in rows.values()})
        tasks = sorted({row.task for row in rows.values()
                        if row.model == model})
        row_index = models.index(model)
        col_index = tasks.index(task)
        target = row_index + delta
        if 0 <= target < len(models):
            self._focus_pos = (target, col_index)
        else:
            # the card edge: cross to the adjacent card, first/last row
            card_index = next(
                (index for index, candidate in enumerate(cards)
                 if candidate.roots == card.roots), 0)
            next_index = card_index + (1 if delta > 0 else -1)
            if not 0 <= next_index < len(cards):
                return  # clamped at the outer edge
            list_view = self.query_one("#mon-cards", ListView)
            list_view.index = next_index
            other = cards[next_index]
            other_rows = self._card_rows(other)
            other_models = sorted(
                {row.model for row in other_rows.values()})
            if not other_models:
                self._focus_pos = None
            else:
                self._focus_pos = (
                    0 if delta > 0 else len(other_models) - 1, col_index)
                # the carried column clamps to the crossed card's shape
                self._normalize_focus()
        self._repaint_focus_move()

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
        self._render_wide()
        self._render_history(history)
        self._render_right_detail()
        # 16-01: the G panel rides the shared pass (its own signature
        # gate keeps a steady tick at zero writes; the recompose path
        # repaints from the last-known rows through the on_mount reset)
        self._render_gpu_panel()
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

    def _root_live_plan(self, root) -> "tuple | None":
        """One root's live-sweep PLAN — the (pairs frozenset, seeds
        tuple | None) evidence pair (261020-blt) — read from the
        screen's ``_live_plans`` cache keyed by RESOLVED root (the
        ``MonitorBackend._live_pairs_for`` idiom). Returns the tuple
        ONLY when leg 0 is a non-empty frozenset; a miss, a None entry
        (live-but-unknown argv), or a degenerate empty set all read
        None — no plan, never a scope."""
        entry = self._live_plans.get(
            str(Path(root).expanduser().resolve()))
        if (isinstance(entry, tuple) and isinstance(entry[0], frozenset)
                and entry[0]):
            return entry
        return None

    def _root_live_pairs(self, root) -> "frozenset | None":
        """One root's live-sweep planned-pair set for PRESENTATION
        scoping (261019-o8e): the PAIRS leg of the root's plan
        (261020-blt — ``_root_live_plan`` leg 0). The None vocabulary
        is the DELIBERATE divergence from the service helper —
        ``MonitorBackend._live_pairs_for`` returns the EMPTY set on a
        strict miss because the service derives per-seed STATES (a
        dead root: every non-terminal cell derives interrupted), while
        THIS screen-side None means "scope nothing, render root-wide":
        an absent root, a None entry (live-but-unknown argv), or an
        empty set (degenerate parse) all fall back — a live card NEVER
        renders an empty matrix through an evidence gap."""
        plan = self._root_live_plan(root)
        return plan[0] if plan is not None else None

    def _root_scoped_rows(self, root) -> "dict[str, Any]":
        """One root's RUNNING-VIEW row map — discovered ∪ planned
        (261020-blt), THE one per-root seam every current-sweep view
        reads (the merged card map, the tree, the strip counts — and
        ``_render_wide`` directly). Three legs over the o8e drop:

        1. NO plan (every evidence gap): the discovered rows verbatim —
           today's root-wide render, never an empty map.
        2. A plan HOLDS: rows outside ``plan[0]`` drop (the o8e
           same-root residue law), then the union — every planned pair
           without a discovered row SYNTHESIZES an all-queued CellRow
           through the existing grammar; a discovered row with a KNOWN
           seed basis (the plan's own leg 1, non-empty) rebuilds to
           EXACTLY the planned seeds — per planned seed the discovered
           CellSeed verbatim (states + fraction_states) when the seed
           numbers match, else a queued CellSeed, and discovered seeds
           OUTSIDE the plan drop (the residue law at seed level);
           a discovered row with a BORROWED basis (the pairs-only
           adapter — seeds unknown) stays verbatim: seeds are NEVER
           fabricated, so the o8e render is byte-identical.
        3. The basis' degenerate legs: a KNOWN-empty leg 1 borrows the
           root's discovered seed set (the o8e adapter's synthesized
           rows carry one queued glyph per borrowed seed); an empty
           borrow too synthesizes NAME-ONLY rows (``seeds=()``) — a
           fabricated seed NUMBER is never constructed.

        SCOPE LAW: consumed by the Running views ONLY — the drill,
        History, and [e] read the SERVICE ``cells_view`` (the
        root-wide discovered truth), so a synthesized row never reaches
        them (by construction, not by filter). DISPLAY-ONLY data: the
        synthesized rows never gate a launch, kill, or exit."""
        discovered = dict(self._cell_rows.get(root) or {})
        plan = self._root_live_plan(root)
        if plan is None:
            return discovered
        pairs, planned_seeds = plan
        scoped = {key: row for key, row in discovered.items()
                  if (row.model, row.task) in pairs}
        known_basis = tuple(planned_seeds or ())
        borrowed = not known_basis
        seed_basis = known_basis or tuple(sorted({
            cell_seed.seed for row in scoped.values()
            for cell_seed in row.seeds}))
        rows: dict[str, Any] = {}
        for model, task in sorted(pairs):
            key = f"{model}__{task}"
            row = scoped.get(key)
            if row is None:
                # the planned-but-undiscovered pair (the driver mkdirs a
                # cell only when it REACHES it): the all-queued row
                rows[key] = sweep_monitor.CellRow(
                    model=model, task=task,
                    seeds=tuple(sweep_monitor.CellSeed(
                        seed=seed, state=CELL_QUEUED,
                        fraction_states=None)
                        for seed in seed_basis),
                    newest_mtime=None)
            elif borrowed:
                rows[key] = row  # seeds unknown: verbatim, never guessed
            else:
                # the discovered row completed to EXACTLY the planned
                # seeds (missing ones queued, off-plan residue dropped)
                by_seed = {cell_seed.seed: cell_seed
                           for cell_seed in row.seeds}
                rows[key] = sweep_monitor.CellRow(
                    model=model, task=task,
                    seeds=tuple(
                        by_seed[seed] if seed in by_seed
                        else sweep_monitor.CellSeed(
                            seed=seed, state=CELL_QUEUED,
                            fraction_states=None)
                        for seed in known_basis),
                    newest_mtime=row.newest_mtime)
        return rows

    def _card_rows(self, card: _RunCard) -> "dict[str, Any]":
        """The card's merged row map (261019-f0x): the per-root
        ``_root_scoped_rows`` seam over ``card.roots`` keyed
        ``f"{model}__{task}"``; when the same key appears under
        multiple roots (not the mgpu sharding case, but honest) the
        per-seed states merge with the priority running > failed >
        interrupted > completed/skipped > queued (first state wins
        inside a tier — deterministic). This ONE map feeds the strip
        counts, the matrix, the right pane, and the [w] table — never
        re-derived differently.

        261019-o8e: the map is the LIVE-SWEEP-SCOPED view when the
        launcher's evidence holds a planned pair set for a root (rows
        of THAT root outside the set — same-root historical residue —
        drop BEFORE the merge, per root, so an mgpu card keeps pairs
        live in ANY of its worker roots); a root without evidence
        contributes all its rows (the root-wide fallback).

        261020-blt: the rows are the DISCOVERED-∪-PLANNED cells —
        ``_root_scoped_rows`` synthesizes queued rows for the plan's
        not-yet-mkdir'd pairs (the driver reaches a cell only when it
        runs it), so the map's shape legs carry the union into the
        cards signature: a plan landing mid-session rebuilds ONCE, and
        a steady tick derives identical rows (the union is a pure
        function of (plan, discovered rows)) -> zero widget writes.
        The merge is unchanged — a synthesized row's queued seeds
        (priority 4) lose to every discovered state, so the moment a
        planned cell's dir lands its discovered truth replaces the
        synthesized seeds automatically."""
        merged: dict[str, Any] = {}
        for root in card.roots:
            scoped = self._root_scoped_rows(root)
            for key, row in scoped.items():
                existing = merged.get(key)
                merged[key] = (
                    row if existing is None
                    else self._merge_group_rows(existing, row))
        return merged

    @staticmethod
    def _merge_group_rows(first: Any, second: Any) -> Any:
        """Two roots' rows for one (model, task) key: the per-seed
        union under ``_SEED_MERGE_PRIORITY`` (min wins; first wins
        inside a tier), seeds sorted, newest mtime maxed."""
        seeds = {cell_seed.seed: cell_seed
                 for cell_seed in first.seeds}
        for cell_seed in second.seeds:
            present = seeds.get(cell_seed.seed)
            if (present is None
                    or _SEED_MERGE_PRIORITY.get(
                        cell_seed.state, 99) < _SEED_MERGE_PRIORITY.get(
                            present.state, 99)):
                seeds[cell_seed.seed] = cell_seed
        return sweep_monitor.CellRow(
            model=first.model, task=first.task,
            seeds=tuple(seeds[number] for number in sorted(seeds)),
            newest_mtime=max(first.newest_mtime or 0.0,
                             second.newest_mtime or 0.0) or None)

    @staticmethod
    def _card_seed_counts(rows: "dict[str, Any]") -> "dict[str, int]":
        """The strip/matrix count basis: per-state seed counts over the
        merged row map (the CELLS' own states — independent of the
        stats seam's done/total)."""
        counts: dict[str, int] = {}
        for row in rows.values():
            for cell_seed in row.seeds:
                counts[cell_seed.state] = (
                    counts.get(cell_seed.state, 0) + 1)
        return counts

    def _card_filter_active(self, card: _RunCard) -> bool:
        """261019-o8e: the live-sweep scoping is ACTIVE for the card
        when ANY of its roots carries a non-None planned-pair set —
        the done/total basis switches to the FILTERED seed counts for
        exactly those cards (the strip's glyph counts and fraction can
        never disagree about the filter)."""
        return any(self._root_live_pairs(root) is not None
                   for root in card.roots)

    @staticmethod
    def _card_filtered_done_total(
            counts: "dict[str, int]") -> "tuple[int, int]":
        """The strip's done/total over the FILTERED seed counts
        (261019-o8e): done = the terminal states (completed+failed+
        skipped — the stats-line done convention), total = every
        filtered seed. Elapsed/ETA/rate stay stats-seam-scope (the
        locked fix names glyph counts + done/total only)."""
        done = (counts.get(CELL_COMPLETED, 0)
                + counts.get(CELL_FAILED, 0)
                + counts.get(CELL_SKIPPED, 0))
        return done, sum(counts.values())

    def _card_done_total(self, card: _RunCard) -> "tuple[int, int | None]":
        """The strip's done/total fraction — the existing precedence
        aggregated over the card's roots: per root stats.done/total
        (falling back to the scan summary), total None-propagating (any
        unknown root total -> the honest unknown)."""
        done = 0
        total: int | None = 0
        for root in card.roots:
            stats = self._root_stats.get(root)
            summary = self._summaries.get(root)
            done += (stats.done if stats is not None
                     else (summary.done if summary is not None else 0))
            root_total = None
            if stats is not None and stats.total is not None:
                root_total = stats.total
            elif summary is not None:
                root_total = summary.total
            if root_total is None:
                total = None
            elif total is not None:
                total += root_total
        return done, total

    def _card_elapsed_seconds(self, card: _RunCard) -> "float | None":
        """max(elapsed_seconds) over the card's roots — None when no
        root carries one (the honest dash)."""
        values = [
            stats.elapsed_seconds
            for root in card.roots
            if (stats := self._root_stats.get(root)) is not None
            and stats.elapsed_seconds is not None]
        return max(values) if values else None

    def _card_eta_points(self, card: _RunCard) -> "list[float]":
        """The card's derivable point-ETA estimates (the ETA_POINT mode
        only — pending/range/none contribute nothing, the honest dash
        legs; the multi-root min–max range derives over these)."""
        points: list[float] = []
        for root in card.roots:
            stats = self._root_stats.get(root)
            if (stats is not None and stats.eta is not None
                    and stats.eta.mode == ETA_POINT
                    and stats.eta.point_seconds is not None):
                points.append(stats.eta.point_seconds)
        return points

    def _card_rate(self, card: _RunCard) -> "str | None":
        """The strip's derived it/s: the running CURRENT cell's
        CellProgress across the card's roots (first derivable in root
        order — deterministic), pure arithmetic via ``_rate_of``."""
        for root in card.roots:
            stats = self._root_stats.get(root)
            if stats is None or stats.current is None:
                continue
            progress = (self._cell_progress.get(root) or {}).get(
                (stats.current.model, stats.current.task))
            rate = _rate_of(progress)
            if rate is not None:
                return rate
        return None

    def _card_strip(self, card: _RunCard, counts: "dict[str, int]",
                    done: int, total: "int | None") -> Text:
        """The ONE summary strip line (the approved variant-B shape):
        root name bold, then glyph+count per category (non-zero
        categories render, queued always does), the done/total fraction
        (261019-o8e: the CALLER-threaded pair — the filtered seed
        counts' basis when the live-sweep scoping is active, the stats
        precedence otherwise; the honest unknown when total is None),
        the 20-cell segmented bar (skipped in narrow), the elapsed
        segment, the ETA segment (point + wall clock / multi-root
        min–max range / the dash), and the derived rate (skipped in
        narrow). Every wall-clock read routes through this module's
        ``time`` (golden-freezable)."""
        strip = Text(f" {Path(card.base).name}", style="bold")
        strip += Text("  ")
        for state in _STRIP_COUNT_STATES:
            count = counts.get(state, 0)
            if count or state == CELL_QUEUED:
                strip += Text(_state_glyph(state),
                              style=_MATRIX_GLYPH_STYLES.get(state, "dim"))
                strip += Text(f"{count} ")
        strip += Text(" ")
        if total is None:
            strip += Text(S.MON_TOTAL_UNKNOWN, style="dim")
        else:
            strip += Text(f"{done}/{total}", style="bold cyan")
        if not self._narrow:
            strip += Text("  ")
            strip += _strip_bar(counts)
        strip += Text("  ")
        elapsed = self._card_elapsed_seconds(card)
        strip += Text(S.MON_STRIP_ELAPSED.format(
            t=(_format_elapsed_short(elapsed)
               if elapsed is not None else _DASH)))
        strip += Text("  ")
        points = self._card_eta_points(card)
        if not points:
            strip += Text(_DASH, style="dim")
        elif len(points) == 1:
            # the point ETA with its wall-clock landing — the ONE
            # wall-clock read in the strip (module time, freezable)
            clock = time.strftime(
                "%H:%M", time.localtime(time.time() + points[0]))
            strip += Text(S.MON_STRIP_ETA.format(
                eta=format_eta(points[0]), clock=clock))
        else:
            strip += Text(S.MON_STRIP_ETA_RANGE.format(
                lo=format_eta(min(points)), hi=format_eta(max(points))))
        if not self._narrow:
            rate = self._card_rate(card)
            strip += Text("  ")
            if rate is not None:
                strip += Text(S.MON_STRIP_RATE.format(rate=rate))
            else:
                strip += Text(_DASH, style="dim")
        return strip

    def _card_matrix(
            self, rows: "dict[str, Any]",
            focused_pair: "tuple[str, str] | None") -> "list[tuple[str, Text]]":
        """The matrix grid (the approved variant-B shape): EVERY
        (model, task) group of the run — models and tasks in sorted
        order, each intersection its seed glyphs in the existing state
        vocabulary (rich-native styles; the $token-crash probe pin),
        the FOCUSED group's glyphs additionally styled reverse
        (style-only — the width never changes, so in-place updates stay
        layout-stable). Narrow degrades to per-model count rows (no
        columns, no header)."""
        models = sorted({row.model for row in rows.values()})
        if not models:
            return []
        tasks = sorted({row.task for row in rows.values()})
        lines: list[tuple[str, Text]] = []
        if not self._narrow:
            head = Text(" " * _MATRIX_NAME_WIDTH, style="dim")
            for task in tasks:
                width = _matrix_col_width(task)
                cell = Text(task, style="dim")
                cell.truncate(width, overflow="ellipsis", pad=True)
                head += cell
            lines.append(("mon-matrix-head", head))
        for model in models:
            model_rows = {
                key: row for key, row in rows.items() if row.model == model}
            line = Text(model)
            line.truncate(_MATRIX_NAME_WIDTH, overflow="ellipsis",
                          pad=True)
            if self._narrow:
                counts = self._card_seed_counts(model_rows)
                for state in _STRIP_COUNT_STATES:
                    count = counts.get(state, 0)
                    if count or state == CELL_QUEUED:
                        line += Text(" ", style="dim")
                        line += Text(
                            f"{_state_glyph(state)}{count}",
                            style=_MATRIX_GLYPH_STYLES.get(state, "dim"))
                lines.append(("mon-matrix-row", line))
                continue
            for task in tasks:
                width = _matrix_col_width(task)
                row = model_rows.get(f"{model}__{task}")
                group = Text()
                if row is not None:
                    focused = (focused_pair is not None
                               and focused_pair == (model, task))
                    seeds = sorted(row.seeds, key=lambda s: s.seed)
                    overflow = len(seeds) > width
                    if overflow:
                        # the honest backstop: more seeds than the
                        # column is wide — the leading seeds + the
                        # ellipsis (never a crash, never a reflow)
                        seeds = seeds[:width - 1]
                    for cell_seed in seeds:
                        style = _MATRIX_GLYPH_STYLES.get(
                            cell_seed.state, "dim")
                        if focused:
                            style = f"{style} reverse"
                        group += Text(_state_glyph(cell_seed.state),
                                      style=style)
                    if overflow:
                        group += Text("…", style="dim")
                group += Text(" " * max(0, width - len(group.plain)))
                line += group
            lines.append(("mon-matrix-row", line))
        return lines

    def _card_content(self, card: _RunCard) -> "list[tuple[str, Text]]":
        """One running card's CONTENT — the ORDERED (css-classes, Text)
        pairs the card renders: the summary strip FIRST, the resume
        note (when the primary carries markers), then the matrix head +
        one row per model. The 261018-kvj card lines (scale / total /
        current / worker rows) are RETIRED — the merged row map IS the
        card body now.

        261018-rze (c): the ONE content definition shared by BOTH
        render paths — the rebuild path (``_card_widget``'s ListItem
        construction) and the in-place path (the existing Labels'
        content update) — so the two can never drift.

        261019-o8e: rows + counts compute ONCE; the strip's done/total
        derives over the FILTERED counts when the live-sweep scoping is
        active for the card (the glyph counts and the fraction share
        the one basis), else today's stats-seam precedence.

        261019-pe0: in TREE mode this builder returns ONLY the strip +
        resume-note lines — the per-card ``RunCardTree`` carries the
        body (a non-Label widget, so ``_refresh_card_labels``'
        ``query(Label)`` walk matches; the mode leg in ``_cards_sig``
        forces the ListItem rebuild on every switch)."""
        rows = self._card_rows(card)
        counts = self._card_seed_counts(rows)
        if self._card_filter_active(card):
            done, total = self._card_filtered_done_total(counts)
        else:
            done, total = self._card_done_total(card)
        lines: list[tuple[str, Text]] = [
            ("mon-card-strip", self._card_strip(
                card, counts, done, total))]
        resume = self._resumes.get(card.roots[0], 0)
        if resume > 0:
            note_copy = (S.MON_RESUME_NOTE_SHORT if self._narrow
                         else S.MON_RESUME_NOTE)
            lines.append(("mon-card-resume",
                          Text(note_copy.format(n=resume),
                               style="dim")))
        # 16-02 (TUI-03, UI-SPEC Surface B rule 1 + the A4 interleave):
        # the dispatch block — under the summary strip / resume note,
        # above the matrix/tree body, all ``mon-card-resume`` family;
        # NO view (absent/damaged file) renders NO block at all, so
        # static/worker cards stay byte-identical (rule 5)
        dispatch_view = self._card_dispatch(card)
        if dispatch_view is not None:
            lines.extend(self._dispatch_block_lines(dispatch_view))
        if self._left_mode == "tree":
            return lines  # the tree under the strip is the card's body
        focused_pair = None
        focused = self._focused_group()
        # ``_cards()`` builds fresh _RunCard instances per call — the
        # focused-card test compares the ROOTS identity (the card's
        # identity), never the wrapper object
        if focused is not None and focused[0].roots == card.roots:
            focused_pair = (focused[1], focused[2])
        lines.extend(self._card_matrix(rows, focused_pair))
        return lines

    def _dispatch_block_lines(
            self, view: "dispatch_state.DispatchStateView"
    ) -> "list[tuple[str, Text]]":
        """The dispatch block's (classes, Text) pairs (16-02, UI-SPEC
        Surface B rules 2-4): the stale/malformed warning row ABOVE the
        dispatch line, then one worker row per ``workers[]`` entry IN
        ARRAY ORDER — all ``mon-card-resume`` family (the dim secondary
        role; rich-native styles ONLY — $token styles crash the Label
        render path, the 09-03 probe pin; the warning row carries the
        strip's rich-native color-channel family in ``yellow``, the
        $warning analog).

        Every value rides the view VERBATIM (the status passthrough
        rule; queue depth is NEVER recomputed — TUI orchestrates,
        never computes); a missing value renders the honest dash
        (``_DASH`` — data, never a fabricated number).
        """
        lines: list[tuple[str, Text]] = []
        if view.stale or view.malformed:
            lines.append(("mon-card-resume", Text(
                S.MON_DISPATCH_STALE.format(
                    age=view.stale_age_s,
                    grace=int(dispatch_state.DISPATCH_STALE_SECONDS)),
                style="yellow")))
        counts = view.counts
        done = (counts.completed if counts is not None
                and counts.completed is not None else _DASH)
        total = (counts.total if counts is not None
                 and counts.total is not None else _DASH)
        status = view.status if view.status is not None else _DASH
        queue = (view.queue_depth if view.queue_depth is not None
                 else _DASH)
        lines.append(("mon-card-resume", Text(
            S.MON_DISPATCH_LINE.format(
                status=status, done=done, total=total, queue=queue),
            style="dim")))
        for worker in view.workers:
            index = worker.index if worker.index is not None else _DASH
            gpu = worker.gpu if worker.gpu is not None else _DASH
            if worker.in_flight is None:
                lines.append(("mon-card-resume", Text(
                    S.MON_DISPATCH_WORKER_IDLE.format(i=index, gpu=gpu),
                    style="dim")))
                continue
            cell = worker.in_flight
            row_text = S.MON_DISPATCH_WORKER_BUSY.format(
                i=index, gpu=gpu,
                model=(cell.model if cell.model is not None else _DASH),
                task=(cell.task if cell.task is not None else _DASH),
                seed=(cell.seed if cell.seed is not None else _DASH))
            if cell.fraction is not None:
                row_text += f" × frac_{cell.fraction}"
            lines.append(("mon-card-resume", Text(row_text, style="dim")))
        return lines

    def _card_widget(self, card: _RunCard) -> ListItem:
        """One running card's WIDGET — the thin constructor over the
        shared ``_card_content`` builder (261018-rze: the rebuild path's
        widget tree stays byte-identical; see ``_card_content``).
        261019-pe0: in TREE mode a POPULATED ``RunCardTree`` joins after
        the Labels — populated AT CONSTRUCTION (textual defers the
        mount, so a same-pass ``query_one`` cannot fill it — probed);
        ``_build_card_tree`` is the one build path shared with the
        in-place structure change."""
        children: list = [
            Label(text, classes=classes)
            for classes, text in self._card_content(card)]
        if self._left_mode == "tree":
            tree = RunCardTree(classes="mon-card-tree")
            self._build_card_tree(tree, card)
            children.append(tree)
        return ListItem(Vertical(*children, classes="mon-card"))

    # ===== the TREE state's per-card body (261019-pe0) =====

    #: 261020-asm (the maintainer's tree-variant E ruling, 2026-10-20
    #: 07:12): a fresh ``RunCardTree`` build enters with EVERY model
    #: node EXPANDED — the operator sees every task row on mount, on a
    #: structural rebuild, and on every card that appears mid-session.
    #: The ``_tree_expand`` cache holds only the operator's OWN collapse
    #: choices; a model absent from the cache (and every fresh card)
    #: takes this default. ``*`` reads the live tree state, never this
    #: default — from the all-open entry it collapses everything.
    _TREE_DEFAULT_EXPANDED = True

    def _group_progress(self, card: _RunCard, model: str, task: str):
        """One group's PARSED progress — the ``_right_detail_lines``
        resolution (first root of the card whose progress carries a
        percent), shared with the tree's task labels since 261019-pe0 so
        the pane and the tree can never disagree. None when nothing
        parses (the honest glyph-only rendering)."""
        for root in card.roots:
            candidate = (self._cell_progress.get(root) or {}).get(
                (model, task))
            if candidate is not None and candidate.percent is not None:
                return candidate
        return None

    def _tree_model_label(self, model: str,
                          rows: "dict[str, Any]") -> Text:
        """A model node's label: the name bold + the filtered done/total
        dim — done/total over THAT MODEL's rows of the ONE merged map
        with the o8e basis (terminal = completed+failed+skipped over all
        its filtered seeds; the ``_card_filtered_done_total``
        arithmetic, never a stats-seam read)."""
        model_rows = {key: row for key, row in rows.items()
                      if row.model == model}
        counts = self._card_seed_counts(model_rows)
        done, total = self._card_filtered_done_total(counts)
        label = Text(model, style="bold")
        label += Text(f"  {done}/{total}", style="dim")
        return label

    def _tree_task_label(self, card: _RunCard, model: str, task: str,
                         rows: "dict[str, Any]") -> Text:
        """A task node's label: the task key + the per-seed cluster in
        the pane's seed-line grammar — per sorted seed the ``s{n}``
        token (dim) + the state glyph (the matrix glyph styles); a
        RUNNING seed whose group progress parses carries the COMPACT
        inline form (the integer percent cyan-bold + the derived rate);
        a running seed without parsed progress renders the glyph ONLY —
        honest, never a fabricated number, no steps/bar grammar (the
        maintainer's example shape). A narrow tree stays full: the
        labels are data, width-tolerant."""
        label = Text(task)
        label += Text("  ")
        row = rows.get(f"{model}__{task}")
        if row is None:
            return label
        progress = self._group_progress(card, model, task)
        for cell_seed in sorted(row.seeds, key=lambda s: s.seed):
            label += Text(f"{S.MON_COL_SEED.format(seed=cell_seed.seed)} ",
                          style="dim")
            label += Text(_state_glyph(cell_seed.state),
                          style=_MATRIX_GLYPH_STYLES.get(
                              cell_seed.state, "dim"))
            if (cell_seed.state == CELL_RUNNING
                    and progress is not None):
                label += Text(" ")
                label += Text(f"{progress.percent}%", style="cyan bold")
                rate = _rate_of(progress)
                label += Text(" ")
                label += (Text(S.MON_STRIP_RATE.format(rate=rate))
                          if rate is not None
                          else Text(_DASH, style="dim"))
        return label

    def _tree_move(self, tree: RunCardTree, node) -> None:
        """Move the tree cursor to a node SAFELY: touch the line map
        first (``move_cursor`` reads the node's CACHED line index, set
        only during textual 8.2.8's ``_tree_lines`` build — a freshly
        built or structurally changed tree must rebuild it first,
        probe-pinned) and refuse the move onto a hidden node (a task
        under a collapsed parent — the caller falls back to the model
        node)."""
        tree.get_node_at_line(0)  # forces the line-map build
        if node._line < 0:
            return
        tree.move_cursor(node)

    def _tree_find(self, tree: RunCardTree, action_root: str,
                   model: str, task: "str | None" = None):
        """The tree's node for a (model, task) group — task node when
        ``task`` is given, else the model node; None when absent."""
        model_key = ("model", action_root, model)
        for node in tree.root.children:
            if node.data == model_key:
                if task is None:
                    return node
                task_key = ("task", action_root, model, task)
                for child in node.children:
                    if child.data == task_key:
                        return child
                return None
        return None

    def _build_card_tree(self, tree: RunCardTree, card: _RunCard) -> None:
        """Build one card's tree content — THE one build path shared by
        the construction leg (``_card_widget``: a fresh widget pre-mount)
        and the in-place structure change (``_render_card_tree``: the
        per-card tree sig moved — e.g. a task moving between models, a
        change the cards sig cannot see). Node data tuples are the node
        identity: ``("model", action_root, model)`` /
        ``("task", action_root, model, task)``.

        The GATE LAW's preservation: expansion states come from the
        screen-side ``_tree_expand`` cache (a FRESH tree defaults every
        model EXPANDED — ``_TREE_DEFAULT_EXPANDED``, the 261020-asm
        variant-E ruling; the maintainer's example shows task children
        inline), the cursor re-pins by key lookup through
        ``_tree_cursor`` — the captured key when it still exists, else
        the focused group's task node, else the first node. Both caches
        survive the ListItem rebuilds that destroy the widget state and
        are kept fresh by the NodeExpanded/NodeCollapsed/NodeHighlighted
        handlers."""
        rows = self._card_rows(card)
        action_root = card.roots[0]
        tasks_of = {
            model: sorted({row.task for row in rows.values()
                           if row.model == model})
            for model in sorted({row.model for row in rows.values()})}
        struct = tuple((model, tuple(tasks_of[model]))
                       for model in tasks_of)
        expanded = self._tree_expand.get(action_root) or {}
        tree.reset("")
        tree.root.expand()
        node_map: dict[tuple, Any] = {}
        for model, model_tasks in tasks_of.items():
            model_node = tree.root.add(
                self._tree_model_label(model, rows),
                data=("model", action_root, model),
                allow_expand=True,
                expand=expanded.get(model, self._TREE_DEFAULT_EXPANDED))
            node_map[("model", action_root, model)] = model_node
            for task in model_tasks:
                node_map[("task", action_root, model, task)] = (
                    model_node.add_leaf(
                        self._tree_task_label(card, model, task, rows),
                        data=("task", action_root, model, task)))
        self._tree_sigs[action_root] = struct
        # the cursor re-pin: capture key > focused group > first node; a
        # captured task node hidden under a collapsed model falls back
        # to its model node (the visible ancestor)
        node = node_map.get(self._tree_cursor.get(action_root) or ())
        if node is None:
            focused = self._focused_group()
            if (focused is not None and card.roots[0] == action_root
                    and focused[0].roots == card.roots):
                node = node_map.get(
                    ("task", action_root, focused[1], focused[2]))
                if node is None:
                    node = node_map.get(("model", action_root, focused[1]))
        if node is None and node_map:
            node = next(iter(node_map.values()))
        if node is not None:
            tree.get_node_at_line(0)  # the line map: fresh for _line
            if node._line < 0 and node.parent is not None:
                node = node.parent
            if node._line >= 0:
                tree.move_cursor(node)

    def _render_card_tree(self, card: _RunCard, item: Widget) -> None:
        """The tree-state per-card render (the rze/f0x gate law's tree
        leg): an UNCHANGED per-card structure signature performs the
        label pass ONLY — ``TreeNode.set_label`` where the rendered Text
        differs (plain + spans compare, the f0x in-place precedent); a
        CHANGED signature rebuilds through ``_build_card_tree`` (the
        caches preserve expansion + cursor). A just-rebuilt ListItem
        resolves no tree (textual defers the mount — probed): the
        construction path already built its content, so the pass is a
        no-op there."""
        try:
            tree = item.query_one(RunCardTree)
        except Exception:  # noqa: BLE001 — the fresh-construction pass
            return
        rows = self._card_rows(card)
        action_root = card.roots[0]
        tasks_of = {
            model: sorted({row.task for row in rows.values()
                           if row.model == model})
            for model in sorted({row.model for row in rows.values()})}
        struct = tuple((model, tuple(tasks_of[model]))
                       for model in tasks_of)
        if struct != self._tree_sigs.get(action_root):
            self._build_card_tree(tree, card)
            return
        for model_node in tree.root.children:
            data = model_node.data
            if not (isinstance(data, tuple) and data
                    and data[0] == "model"):
                continue
            model = data[2]
            label = self._tree_model_label(model, rows)
            current = model_node.label
            if (not isinstance(current, Text)
                    or current.plain != label.plain
                    or current.spans != label.spans):
                model_node.set_label(label)
            for task_node in model_node.children:
                task_data = task_node.data
                if not (isinstance(task_data, tuple)
                        and task_data[0] == "task"):
                    continue
                task_label = self._tree_task_label(
                    card, model, task_data[3], rows)
                task_current = task_node.label
                if (not isinstance(task_current, Text)
                        or task_current.plain != task_label.plain
                        or task_current.spans != task_label.spans):
                    task_node.set_label(task_label)

    def _focused_card_tree(self) -> "RunCardTree | None":
        """The FOCUSED card's tree (the tree-state navigation target):
        resolved through the ListView index (the one card-focus
        authority), clamped, None-guarded — INDEPENDENT of which widget
        holds focus (the screen's priority arrows own the keys either
        way)."""
        list_view = self.query_one("#mon-cards", ListView)
        children = list_view.children
        if not children:
            return None
        index = list_view.index
        if index is None:
            index = 0
        index = max(0, min(index, len(children) - 1))
        try:
            return children[index].query_one(RunCardTree)
        except Exception:  # noqa: BLE001 — matrix-mode items carry none
            return None

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
                current = label.content
                # 261019-f0x: the comparison covers the SPANS too — the
                # focus highlight is a STYLE-ONLY change (reverse over
                # the same glyphs, same width), invisible to a plain-
                # text compare but a real repaint the operator sees
                if (not isinstance(current, Text)
                        or current.plain != text.plain
                        or current.spans != text.spans):
                    label.update(text, layout=False)
        return True

    def _render_cards(self, cards: "list[_RunCard]") -> None:
        """Render the card list (few items — live roots). 261018-rze
        (c) + 261019-f0x: the STRUCTURE signature (roots identity/
        order, base_live, resume-note presence, narrow, the merged
        matrix shape, the focus tuple + focused card index — every
        label-count/order-changing input; NEVER progress/rate text)
        gates the rebuild; a content-only change refreshes the existing
        Labels in place. The rebuild path re-pins the cursor index
        clamped so a structural rebuild never steals the operator's
        selection (the WR-05 spirit; a list's identity is positional,
        cards never reorder except on activity changes).

        261019-pe0 mode plumbing (TOP of the pass, before
        ``_normalize_focus``): (a) the STRUCTURAL hold-check — a change
        in the per-card structure tuple resets the manual [w] choice to
        auto; (b) the effective mode re-derives (user or auto). The
        manual hold window is EXACTLY "until the per-card structure
        tuple changes (card set / model or task set / narrow flip) or a
        remount". In TREE mode the per-card tree pass runs at the END
        (both the in-place and the rebuild path — a steady tick updates
        the tree labels in place exactly as the card Labels)."""
        struct = self._cards_struct_legs(cards)
        if struct != self._left_mode_struct_sig:
            self._left_mode_user = None
            self._left_mode_struct_sig = struct
        self._left_mode = self._derive_left_mode()
        self._normalize_focus()
        sig = self._cards_signature(cards)
        if sig == self._cards_sig and self._refresh_card_labels(cards):
            self._card_order = [card.roots[0] for card in cards]
        else:
            list_view = self.query_one("#mon-cards", ListView)
            previous = list_view.index
            list_view.clear()
            self._card_order = []
            for card in cards:
                list_view.append(self._card_widget(card))
                self._card_order.append(card.roots[0])
            if self._card_order:
                # an unfocused-but-populated list still highlights row 0
                # (a bare enter through the screen binding must act on a
                # real selection); a rebuild never steals the index
                list_view.index = max(
                    0, min(previous if previous is not None else 0,
                           len(self._card_order) - 1))
            # the signature recomputes AFTER the index pin — the
            # assignment above changes an input the sig carries
            # (261019-f0x), and a stale sig would rebuild again on the
            # very next tick
            self._cards_sig = self._cards_signature(cards)
        if self._left_mode == "tree":
            list_view = self.query_one("#mon-cards", ListView)
            for item, card in zip(list_view.children, cards):
                self._render_card_tree(card, item)

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

    # ===== the [w] three-state cycle (261019-f0x Task 3 -> 261019-pe0) =====

    def action_cycle_left(self) -> None:
        """[w]: cycle the Running tab's left pane matrix -> tree -> wide
        -> matrix (261019-pe0, the maintainer's scalability ruling — the
        f0x matrix cannot hold a real 62x50 sweep). History tab: silent
        no-op (the [d]/[e] off-tab precedent). The CHOICE is stored into
        both the manual hold (``_left_mode_user``) and the effective
        mode — effective immediately; the hold-check in
        ``_render_cards`` keeps it until the next structural change.

        FOCUS UNIFICATION around the switch (the o8e ``_normalize_focus``
        precedent — matrix/tree/wide share the ``(model, task)``
        coordinate): LEAVING wide derives ``_focus_pos`` from the wide
        cursor row FIRST (the rows still hold the pre-switch state);
        ENTERING tree pins the tree cursor onto the focused group's task
        node (after the render — the widget must exist); ENTERING wide
        moves the wide cursor to the focused group's first row (after
        the render — the rows must exist). The pre-switch focus is never
        cleared, so every pass-through restores it."""
        if self._active_tab != "running":
            return
        order = ("matrix", "tree", "wide")
        current = self._left_mode if self._left_mode in order else "matrix"
        target = order[(order.index(current) + 1) % len(order)]
        if current == "wide":
            self._leave_wide_derive_focus()
        self._left_mode_user = target
        self._left_mode = target
        self._render_all()
        self._focus_active()
        # entering TREE needs no further call here: the fresh-appended
        # trees mount asynchronously (probed), so the FOCUS move rides
        # the tree's OWN mount notification (RunCardTree.TreeMounted ->
        # the screen focuses the focused card's tree — the enter
        # routing contract); the CURSOR pin already landed at the
        # construction build. Entering WIDE pins below (the widget is
        # composed at mount; only its rows changed).
        if target == "wide":
            self._enter_wide_pin()
        self._kick_right_tail()

    def _leave_wide_derive_focus(self) -> None:
        """Leaving wide (wide -> matrix): derive ``_focus_pos`` from the
        wide table's CURRENT cursor row — the ``_wide_row_group``
        reverse lookup, the row's ``model__task`` resolved over the
        owning card's merged row map, then ``_normalize_focus``. The
        ListView index follows the row's card (the coordinate is
        card-relative — the honest unification; the matrix cross-card
        move precedent). Called BEFORE the mode flips (the read needs
        the live cursor)."""
        try:
            wide = self.query_one("#mon-wide", DataTable)
            row_key = str(wide.coordinate_to_cell_key(
                wide.cursor_coordinate)[0].value)
        except Exception:  # noqa: BLE001 — an empty table
            return
        group = self._wide_row_group(row_key)
        if group is None:
            return
        root, key = group
        cards = self._cards()
        for index, card in enumerate(cards):
            if root not in card.roots:
                continue
            row = self._card_rows(card).get(key)
            if row is not None:
                rows = self._card_rows(card)
                models = sorted({r.model for r in rows.values()})
                tasks = sorted({r.task for r in rows.values()
                                if r.model == row.model})
                self._focus_pos = (models.index(row.model),
                                   tasks.index(row.task))
            self.query_one("#mon-cards", ListView).index = index
            self._normalize_focus()
            return

    def _enter_wide_pin(self) -> None:
        """Entering wide: move the wide cursor onto the FOCUSED group's
        first row (the ``root::model__task::`` key prefix among the
        rendered rows — only when a focused group exists; the WR-05
        no-animation re-pin idiom)."""
        focused = self._focused_group()
        if focused is None:
            return
        card, model, task, _row = focused
        wide = self.query_one("#mon-wide", DataTable)
        for root in card.roots:
            prefix = f"{root}::{model}__{task}::"
            for row_key in wide.rows:
                key = str(row_key.value)
                if key.startswith(prefix):
                    try:
                        wide.move_cursor(
                            row=wide.get_row_index(key),
                            animate=False, scroll=False)
                    except Exception:  # noqa: BLE001, S110 — mid-diff:
                        pass  # the cursor stays where the diff left it
                    return

    def _pin_tree_cursor_to_focus(self) -> None:
        """Entering tree: pin the FOCUSED card's tree cursor onto the
        focused group's TASK node (the key-lookup helper); a task node
        hidden under a collapsed model falls back to its model node
        (``_tree_move`` refuses hidden nodes). After ``_render_all`` +
        ``_focus_active`` — the widget must exist."""
        tree = self._focused_card_tree()
        card = self._focused_card()
        focused = self._focused_group()
        if tree is None or card is None:
            return
        action_root = card.roots[0]
        tree.get_node_at_line(0)  # the line map: fresh for the checks
        node = None
        if focused is not None and focused[0].roots == card.roots:
            node = self._tree_find(
                tree, action_root, focused[1], focused[2])
            if node is None or node._line < 0:
                node = self._tree_find(
                    tree, action_root, focused[1])
        if node is not None:
            tree.move_cursor(node)

    def action_tree_toggle_all(self) -> None:
        """[*] (261019-pe0, the locked contract): expand-ALL /
        collapse-ALL across EVERY card's tree — any collapsed model ->
        all expand; else all collapse (a collapsed-away cursor node
        moves to its model node, salvaged through the parent chain
        BEFORE the collapse and re-pinned after the structural refresh).
        Running-tab-effective in TREE mode only, silent elsewhere (the
        [w] precedent)."""
        if self._active_tab != "running" or self._left_mode != "tree":
            return
        list_view = self.query_one("#mon-cards", ListView)
        trees: list[RunCardTree] = []
        should_expand = False
        for item in list_view.children:
            try:
                tree = item.query_one(RunCardTree)
            except Exception:  # noqa: BLE001, S112 — matrix-mode items
                continue
            trees.append(tree)
            if any(node.is_collapsed for node in tree.root.children
                   if node.allow_expand):
                should_expand = True
        if not trees:
            return
        for tree in trees:
            salvage = None
            if not should_expand:
                # a cursor under a model that is about to collapse moves
                # to ITS model node — salvage the parent BEFORE hiding
                cursor = tree.cursor_node
                if (cursor is not None
                        and isinstance(cursor.data, tuple)
                        and cursor.data and cursor.data[0] == "task"
                        and cursor.parent is not None):
                    salvage = cursor.parent
            for node in tree.root.children:
                if node.allow_expand:
                    if should_expand:
                        node.expand()
                    else:
                        node.collapse()
            if salvage is not None:
                self._tree_move(tree, salvage)

    def _wide_row_group(self, row_key: str) -> "tuple[str, str] | None":
        """One wide-table row key's (root, ``model__task``) pair — the
        reverse lookup over the live cell-row caches (never a string
        parse of data-bearing keys)."""
        for card in self._cards():
            for root in card.roots:
                for key in (self._cell_rows.get(root) or {}):
                    if row_key.startswith(f"{root}::{key}::"):
                        return root, key
        return None

    def _render_wide(self) -> None:
        """The A-style dense per-cell table: one row per (root, model,
        task, seed) across ALL live cards, diffed via the EXISTING
        ``_set_table_rows`` (WR-05 cursor identity) and gated by the
        rendered-content signature (the ``_history_sig`` precedent —
        textual 8.2.8's ``update_cell`` refreshes unconditionally).
        Columns: the per-seed state word (NOT the fold — wide is
        per-CELL), model, task, seed, the shared progress grammar on
        running seeds, the derived rate; the root column renders ONLY
        on multi-card sweeps (the 120-col budget — single-card sweeps
        keep the compact grid)."""
        if not self._wide:
            return
        cards = self._cards()
        multi_card = len(cards) > 1
        accent = str(self.app.current_theme.accent)
        columns = ([(S.MON_COL_ROOT, "root")] if multi_card else []) + [
            (S.MON_COL_STATE, "state"), (S.MON_COL_MODEL, "model"),
            (S.MON_COL_TASK, "task"), (S.MON_COL_SEED, "seed"),
            (S.MON_COL_PROGRESS, "progress"), ("", "rate")]
        row_map: dict[str, list] = {}
        for card in cards:
            for root in card.roots:
                # 261020-blt: the wide table reads the SAME per-root
                # union seam as the matrix — the synthesized queued
                # cells render through the existing per-seed grammar
                # (the queued state word + the dash progress, exactly a
                # discovered queued cell today); the wide content sig
                # derives from this row_map, so the union's re-diff is
                # automatic (261019-o8e's filter note superseded by the
                # seam)
                progress_map = self._cell_progress.get(root) or {}
                rows = self._root_scoped_rows(root)
                for key in sorted(rows):
                    row = rows[key]
                    progress = progress_map.get((row.model, row.task))
                    for cell_seed in sorted(row.seeds,
                                            key=lambda s: s.seed):
                        copy, style = _cell_state_cells().get(
                            cell_seed.state,
                            (cell_seed.state, _STYLE_DIM))
                        cells: list = []
                        if multi_card:
                            cells.append(Text(Path(root).name,
                                              style="dim"))
                        cells.append(Text(copy, style=style))
                        cells.append(Text(row.model))
                        cells.append(Text(row.task))
                        cells.append(Text(S.MON_COL_SEED.format(
                            seed=cell_seed.seed)))
                        cells.append(_entry_progress_cell(
                            _SeedStateFold(cell_seed.state), progress,
                            self._narrow, accent))
                        rate = _rate_of(progress)
                        cells.append(
                            Text(S.MON_STRIP_RATE.format(rate=rate))
                            if (rate is not None
                                and cell_seed.state == CELL_RUNNING)
                            else Text(_DASH, style="dim"))
                        row_map[f"{root}::{key}::{cell_seed.seed}"] = cells
        sig = (multi_card, self._narrow,
               tuple((key, *(str(cell) for cell in cells))
                     for key, cells in row_map.items()))
        if sig == self._wide_sig:
            return
        self._wide_sig = sig
        _set_table_rows(self.query_one("#mon-wide", DataTable),
                        columns, row_map)

    def _apply_visibility(self, cards_exist: bool,
                          history_count: int) -> None:
        """Toggle the content region's children: ONLY the active tab's
        list renders (single focus, single list); the scanning note is
        orthogonal (mount-window chrome). 261019-f0x: [w] toggles
        #mon-cards/#mon-wide on the Running tab; the D right pane
        displays iff wide grid + Running tab + cards exist (narrow mode
        hides the whole pane — [t] remains the log surface there)."""
        running_active = self._active_tab == "running"
        self.query_one("#mon-cards").display = (
            running_active and cards_exist and not self._wide)
        self.query_one("#mon-wide").display = (
            running_active and cards_exist and self._wide)
        self.query_one("#mon-running-empty").display = (
            running_active and not cards_exist)
        self.query_one("#mon-history").display = (
            not running_active and history_count > 0)
        self.query_one("#mon-history-empty").display = (
            not running_active and history_count == 0)
        self.query_one("#mon-right").display = (
            not self._narrow and running_active and cards_exist)

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
                if self._left_mode == "wide":
                    target = self.query_one("#mon-wide", DataTable)
                elif self._left_mode == "tree":
                    # 261019-pe0: the tree (inside the focused card's
                    # ListItem — can_focus_children, probed) holds focus
                    # so its OWN enter binding consumes Enter (the
                    # NodeSelected routing); resolved through the
                    # ListView index, clamped, None-guarded
                    target = self._focused_card_tree()
                    if target is None:
                        return
                else:
                    target = self.query_one("#mon-cards", ListView)
                if target is not self.focused:
                    target.focus()
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

    #: The Running-scoped footer keys (261019-f0x): the [w] toggle's
    #: keycap renders ONLY while the Running tab is active (the d/e
    #: precedent, mirrored). 261019-pe0: [*] joins (the tree-state
    #: expand/collapse-all — same projection).
    _RUNNING_SCOPED_FOOTER_KEYS: ClassVar[frozenset[str]] = frozenset(
        {"w", "*"})

    def _footer_pairs(self) -> "list[tuple[str, str]]":
        """The bottom bar's left-segment projection (261018-toe):
        ``binding_row`` over ``BINDINGS`` with the History-scoped d/e
        rows dropped unless the History tab is active — the Running-tab
        footer stays byte-identical to the pre-[d]/[e] render (the
        uncommitted D-03 monitor goldens must not change). 261019-f0x:
        the [w] keycap drops everywhere EXCEPT the Running tab (the
        mirrored projection)."""
        pairs: list[tuple[str, str]] = []
        for binding in self.BINDINGS:
            row = binding_row(binding)
            if row is None:
                continue
            if (self._active_tab != "history"
                    and row[0] in self._TAB_SCOPED_FOOTER_KEYS):
                continue
            if (self._active_tab != "running"
                    and row[0] in self._RUNNING_SCOPED_FOOTER_KEYS):
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
        # 261019-f0x: the pane's visibility followed the flip — the
        # tail state re-kicks on the way back to the Running tab
        self._kick_right_tail()

    def action_arrow_horizontal(self, delta: int) -> None:
        """←/→ (261019-f0x): on the Running tab's focused card with
        >= 1 group they move the matrix focus (clamped — NO tab-switch
        at the edges; Tab is the switcher); everywhere else (the empty
        Running tab, no groups, wide mode, History) they switch tabs
        exactly as before — the kvj tab-switch contract, the pty pin
        family.

        261019-pe0 TREE branch (the LOCKED nav contract, BEFORE the
        matrix branch): → on a COLLAPSED model node expands it (cursor
        stays), on an EXPANDED model node moves into the first child,
        on a task node no-ops; ← on an EXPANDED model node collapses it,
        on a task node (or a top-level collapsed model — the invisible
        root is NEVER a cursor target) moves to the parent. With cards
        on the Running tab in tree mode the arrows NEVER switch tabs
        (no-op at the contract's edges); with no cards they keep the
        switch."""
        if (self._active_tab == "running"
                and self._left_mode == "tree" and self._card_order):
            tree = self._focused_card_tree()
            if tree is not None:
                self._tree_arrow_horizontal(tree, delta)
            return
        if (self._active_tab == "running" and not self._wide
                and self._focused_group() is not None):
            self._move_focus_col(delta)
            return
        self.action_switch_tab()

    def _tree_arrow_horizontal(self, tree: RunCardTree,
                               delta: int) -> None:
        """The tree state's ←/→ rules over one card's tree (the locked
        contract — see ``action_arrow_horizontal``)."""
        node = tree.cursor_node
        if node is None or not (isinstance(node.data, tuple) and node.data):
            return
        if delta > 0:
            if node.data[0] != "model":
                return  # a task/leaf node: no-op
            if not node.is_expanded:
                node.expand()
            elif node.children:
                self._tree_move(tree, node.children[0])
            return
        if node.data[0] == "model" and node.is_expanded:
            node.collapse()
            return
        parent = node.parent
        if parent is not None and not parent.is_root:
            self._tree_move(tree, parent)

    def action_arrow_vertical(self, delta: int) -> None:
        """↑/↓ (261019-f0x): on the Running tab in matrix mode they
        move the focused model row (crossing to the adjacent card at
        the edges, the ListView index following programmatically);
        every other surface delegates to the focused DataTable's
        NATIVE cursor actions (action_cursor_up/action_cursor_down —
        probed present on textual 8.2.8; one code path, both tables).
        No key becomes dead and no focus trap is introduced
        (T-f0x-03).

        261019-pe0 TREE branch: the arrows delegate to the focused
        card's tree's NATIVE cursor actions — movement between VISIBLE
        lines, CLAMPED at the edges; NO card crossing in tree state
        (the matrix card-cross law is matrix-scoped — the maintainer's
        locked contract)."""
        if self._active_tab == "running":
            if self._left_mode == "tree":
                tree = self._focused_card_tree()
                if tree is not None:
                    (tree.action_cursor_down if delta > 0
                     else tree.action_cursor_up)()
                return
            if not self._wide:
                self._move_focus_row(delta)
                return
        table = self.focused
        if isinstance(table, DataTable):
            (table.action_cursor_down if delta > 0
             else table.action_cursor_up)()

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
        duplicates it); a focused selection drills the run's cells
        (261019-f0x: the Running tab's drill carries the focused
        group's key so the modal's cursor pins to its row)."""
        if self._active_tab == "running" and not self._card_order:
            if self.app.below_minimum_grid:
                return
            await self.app.action_nav(4)
            return
        root_key = self._focused_root()
        if root_key is not None:
            self._open_run_drill(root_key, self._drill_focus_key())

    def _drill_focus_key(self) -> "str | None":
        """The [enter] drill's additive focus key — the focused group's
        ``model__task`` on the Running tab (None everywhere else: the
        RunCellsModal opens at its own row 0 exactly as before).
        261019-o8e: the focused pair is filtered-scoped but ALWAYS
        exists among the modal's root-wide rows (the drill reads the
        unfiltered cells_view — see _read_run_cells)."""
        if self._active_tab != "running":
            return None
        focused = self._focused_group()
        if focused is None:
            return None
        return f"{focused[1]}__{focused[2]}"

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """enter on a running card (the ListView's native select — the
        event carries the selected INDEX directly)."""
        index = event.index
        if index is None or not 0 <= index < len(self._card_order):
            return
        self._open_run_drill(self._card_order[index],
                             self._drill_focus_key())

    # ===== the tree-state message handlers (261019-pe0) =====

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:  # type: ignore[type-arg]
        """Enter on a tree node (the focused tree's OWN enter binding
        consumes the key before the screen's row_action — the routing
        contract): a MODEL node toggles expansion and NEVER opens a
        modal (the locked rule; ``auto_expand=False`` makes the stock
        ``_expand_node_on_select`` a no-op, so THIS is the one toggle
        path); a TASK node drills the RunCellsModal with the cursor
        pinned to that group (the ``_drill_focus_key`` path; the WR-06
        guard lives inside ``_open_run_drill``)."""
        if not isinstance(event.control, RunCardTree):
            return  # no other Tree exists on this screen (the guard)
        data = event.node.data
        if not (isinstance(data, tuple) and data):
            return
        if data[0] == "model":
            event.node.toggle()
        elif data[0] == "task":
            self._open_run_drill(data[1], f"{data[2]}__{data[3]}")

    def on_tree_node_highlighted(
            self, event: Tree.NodeHighlighted) -> None:  # type: ignore[type-arg]
        """A tree cursor move (the pane-feed seam): write the shared
        ``(model, task)`` focus coordinate from the node's data tuple —
        a task node pins its (row, col); a model node carries the column
        and clamps through ``_normalize_focus`` (the o8e idiom) — then
        the EXACT ``_repaint_focus_move`` tail: the right pane (detail +
        tail) follows the focused task node exactly as the matrix focus
        does. Highlights from a card OTHER than the focused one are
        ignored (a rebuild's build-pin — the card focus is the ListView
        index; the operator's cross-card moves go through CardPicked)."""
        if not isinstance(event.control, RunCardTree):
            return
        data = event.node.data
        if not (isinstance(data, tuple) and data
                and data[0] in ("model", "task")):
            return
        action_root = data[1]
        focused_card = self._focused_card()
        if (focused_card is None
                or focused_card.roots[0] != action_root):
            return
        self._tree_cursor[action_root] = data
        rows = self._card_rows(focused_card)
        models = sorted({row.model for row in rows.values()})
        if data[2] not in models:
            return
        row_index = models.index(data[2])
        if data[0] == "task":
            tasks = sorted({row.task for row in rows.values()
                            if row.model == data[2]})
            if data[3] in tasks:
                self._focus_pos = (row_index, tasks.index(data[3]))
        else:
            _row, carried = self._focus_pos or (0, 0)
            self._focus_pos = (row_index, carried)
            self._normalize_focus()
        self._render_right_detail()
        self._kick_right_tail()

    def on_run_card_tree_tree_mounted(
            self, message: RunCardTree.TreeMounted) -> None:
        """A card tree finished mounting (the mode-switch render's
        asynchronous append): focus the FOCUSED card's tree — the enter
        routing contract needs the tree (not the ListView) holding
        focus in tree state, and the post-switch ``_focus_active`` call
        ran before the mount landed. Idempotent by the rze (d) law (a
        tree that already holds focus is skipped)."""
        if (self._active_tab != "running"
                or self._left_mode != "tree"):
            return
        tree = self._focused_card_tree()
        if tree is message.tree and self.focused is not message.tree:
            message.tree.focus()

    def on_run_card_tree_card_picked(
            self, message: RunCardTree.CardPicked) -> None:
        """A label-region tree click's card select: resolve the tree's
        ancestor ListItem position in the ListView children and set the
        index (the ONE card-focus authority — the click law). The
        highlight/sync flow runs idempotently behind it (CardPicked is
        posted BEFORE the cursor write in ``_on_click``)."""
        list_view = self.query_one("#mon-cards", ListView)
        for index, item in enumerate(list_view.children):
            try:
                if item.query_one(RunCardTree) is message.tree:
                    list_view.index = index
                    return
            except Exception:  # noqa: BLE001, S112 — matrix-mode items
                continue

    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:  # type: ignore[type-arg]
        """The tree gate-law cache sync: a model node's expansion change
        lands in ``_tree_expand`` so the next rebuild (widget or
        in-place) preserves the operator's tree."""
        self._sync_tree_expand(event, True)

    def on_tree_node_collapsed(self, event: Tree.NodeCollapsed) -> None:  # type: ignore[type-arg]
        """The collapsed twin of the expansion cache sync."""
        self._sync_tree_expand(event, False)

    def _sync_tree_expand(self, event: "Tree.NodeExpanded | Tree.NodeCollapsed",  # type: ignore[type-arg]
                          expanded: bool) -> None:
        if not isinstance(event.control, RunCardTree):
            return
        data = event.node.data
        if isinstance(data, tuple) and data and data[0] == "model":
            self._tree_expand.setdefault(data[1], {})[data[2]] = expanded

    def on_data_table_row_selected(
            self, event: DataTable.RowSelected) -> None:
        """enter on a table's native select event (mouse and key share
        this chokepoint): the History table drills the focused row's
        run; the wide table (261019-f0x) drills the row's OWN root with
        the cursor pinned to its group (the reverse lookup — never a
        string parse of data-bearing keys)."""
        if event.data_table.id == "mon-history":
            root_key = self._focused_root()
            if root_key is not None:
                self._open_run_drill(root_key)
            return
        if event.data_table.id != "mon-wide":
            return
        try:
            row_key = str(event.data_table.coordinate_to_cell_key(
                event.data_table.cursor_coordinate)[0].value)
        except Exception:  # noqa: BLE001 — an empty table
            return
        group = self._wide_row_group(row_key)
        if group is None:
            return
        self._open_run_drill(group[0], group[1])

    def _open_run_drill(self, root_key: str,
                        focus_key: "str | None" = None) -> None:
        """Open the per-run cells drill (either tab): the read-once
        snapshot worker (WR-06-guarded push lands on the message).
        261019-f0x: ``focus_key`` (ADDITIVE, default None) pins the
        modal's cursor to the focused group's row when present."""
        if self.app.below_minimum_grid:
            return
        self._read_run_cells(root_key, focus_key)

    @work(exclusive=True, thread=True, group="mon-drill",
          exit_on_error=False)
    def _read_run_cells(self, root_key: str,
                        focus_key: "str | None" = None) -> None:
        """The drill's ONE read of cells_view + entries_progress, off
        the event loop (the LogTailModal read-once precedent — live
        refresh stays on the running card; the drill is a snapshot).
        261019-o8e: the FULL-ROOT-SNAPSHOT contract — the drill stays
        ROOT-WIDE by design (same-root residue stays visible and
        drillable here and on the History side; the Running tab's
        scoping is presentation-only, never a deletion).
        261020-blt: the SCOPE LAW — this reads the SERVICE cells_view,
        so the screen's planned-cell union (synthesized queued rows)
        can NEVER reach the drill, by construction not by filter."""
        try:
            cells = self._service.cells_view(root_key)
            progress = self._entries_progress_of(root_key)
        except Exception:  # noqa: BLE001 — the tolerant-reader promise
            return
        self.post_message(self.DrillReady(root_key, cells, progress,
                                          focus_key))

    def on_monitor_screen_drill_ready(self, message: DrillReady) -> None:
        if self.app.below_minimum_grid:
            return
        rows = {f"{row.model}__{row.task}": row
                for row in (message.cells or ())}
        self.app.push_screen(RunCellsModal(
            message.root, rows, message.progress, self,
            focus_key=message.focus_key))

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
        # The capacity pre-check (261015-ehc EHC-3, replaced in place
        # by 16-03 D16-10) BEFORE pushing the confirm (the tolerant
        # getattr seam — a fake without the method never blocks, the
        # 11-03 precedent; the service's own stage-0 guard is the
        # structural backstop; a ZERO-ARG read — a re-run is a
        # one-worker plain launch, Pitfall 3) — y is never reached on
        # a refused machine.
        blocked_getter = getattr(
            self._launcher, "single_gpu_launch_blocked", None)
        blocked = (blocked_getter()
                   if blocked_getter is not None else None)
        if blocked:
            roots = ", ".join(blocked.roots)
            workers = blocked.requested_workers
            self.app.notify(
                S.LNC_SINGLE_GPU_BLOCKED.format(roots=roots, workers=workers,
                                                n=blocked.gpu_count),
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

    def _resume_pipeline(self, root: str) -> None:
        """The gated resume (261018-toe): the SAME preflight stage as
        [f]->[r], with the resume=True flag routing the post-preflight
        dispatch into the resume launch worker."""
        self._rerun_stage_id += 1
        self._run_rerun_preflight(
            root, self._rerun_stage_id, resume=True)

    @work(exclusive=True, thread=True, group="mon-rerun")
    def _run_rerun_preflight(self, root: str, run_id: int,
                             resume: bool = False) -> None:
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
            self.RerunPreflightDone(verdict, root, run_id, resume=resume))

    def _dispatch_rerun_launch(self, root: str, resume: bool,
                               run_id: int,
                               phrase: "str | None" = None) -> None:
        """Route the post-preflight launch (261018-toe): the [f]->[r]
        failures path routes to ``_run_rerun_launch`` byte-unchanged
        (``resume=False``, every existing behavior); the [e] resume
        path routes to the ``_run_resume_launch`` worker — and the E2'
        phrase re-prompt threads back through the SAME routing."""
        if resume:
            self._run_resume_launch(root, run_id, phrase)
        else:
            self._run_rerun_launch(root, run_id, phrase)

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
        self._dispatch_rerun_launch(
            message.root, message.resume, message.run_id)

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
                    # modal's confirm callback returns None. 261018-toe:
                    # the re-prompt routes back through the SAME lane it
                    # refused on — the resume worker when the refusal
                    # came from launch_from_pairs, the [f]->[r]
                    # failures worker otherwise.
                    self._dispatch_rerun_launch(
                        root, message.resume,
                        self._rerun_stage_id, typed_phrase)

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
                # 16-03 (D16-10): the detail is the structured
                # GpuCapacityBlock — format the amended copy from its
                # fields, never compute.
                block = next(
                    value for code, value in outcome.problems
                    if code == sweep_launcher_module.PROBLEM_SINGLE_GPU)
                roots = "; ".join(block.roots)
                workers = block.requested_workers
                self.app.notify(
                    S.LNC_SINGLE_GPU_BLOCKED.format(roots=roots, workers=workers,
                                                    n=block.gpu_count),
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
            cell_count = (str(cells) if cells is not None
                          else S.MON_ETA_UNKNOWN)
            # 261018-toe: the [e] resume renders its own success toast;
            # the [f]->[r] failures path stays byte-unchanged below.
            if message.resume:
                self.app.notify(S.MON_RESUME_TOAST.format(
                    cells=cell_count,
                    root=Path(message.root).name))
            else:
                self.app.notify(S.MON_RERUN_TOAST.format(
                    cells=cell_count,
                    root=Path(message.root).name))
            self.note_launch(message.root, 0)
            return
        self.app.notify(
            S.LNC_LAUNCH_FAILED_TOAST.format(
                error=getattr(outcome, "error", None) or ""),
            severity="error")

    # ===== the [e] resume channel (261018-toe — History-tab scoped) =====

    class ResumeReady(Message):
        """The [e] derivation arrived (worker thread -> loop;
        261018-toe): the incomplete pairs, the seed fan-out, and the
        recovered lane over one off-loop read."""

        def __init__(self, root: str, pairs, seeds, lane) -> None:
            self.root = root
            self.pairs = tuple(pairs)
            self.seeds = tuple(seeds)
            self.lane = lane
            super().__init__()

    def action_resume_history(self) -> None:
        """[e] (History tab only): resume the FOCUSED History row's
        INCOMPLETE items — the (model, task) pairs whose fold state is
        failed or interrupted, over the root's own seed set (completed
        cells skip via the existing trainer_state resume markers).
        Degradations mirror the [d] family: below the minimum grid
        nothing opens; off-tab or without a focused row is silent; a
        LIVE root refuses before any modal (a second launch at the same
        root would conflict); an empty incomplete set surfaces the
        nothing-to-resume toast with no modal and no launcher call."""
        if self.app.below_minimum_grid:
            return
        if self._active_tab != "history":
            return
        root_key = self._focused_root()
        if root_key is None:
            return
        if self._root_is_live(root_key):
            self.app.notify(
                S.MON_RESUME_REFUSED_LIVE.format(root=root_key))
            return
        self._derive_resume(root_key)

    @work(exclusive=True, thread=True, group="mon-resume",
          exit_on_error=False)
    def _derive_resume(self, root_key: str) -> None:
        """The [e] derivation off the event loop (the confirm-side
        estimate): cells_view -> the pure incomplete_pairs_view fold +
        the ONE shared derive_rerun_seeds over the root's cell rows +
        the rerun_lane recovery; posts ResumeReady. Tolerant read (a
        raising derivation drops — [e] is re-pressable)."""
        try:
            cells = self._service.cells_view(root_key)
            rows = {f"{row.model}__{row.task}": row
                    for row in (cells or ())}
            pairs = sweep_monitor.incomplete_pairs_view(cells)
            seeds = derive_rerun_seeds((), rows)
            lane = self._service.rerun_lane(root_key)
        except Exception:  # noqa: BLE001 — the tolerant-reader promise
            return
        self.post_message(self.ResumeReady(
            root_key, pairs, seeds, lane))

    def on_monitor_screen_resume_ready(self, message: ResumeReady) -> None:
        if not message.pairs:
            self.app.notify(
                S.MON_RESUME_NOTHING.format(root=message.root))
            return
        if self.app.below_minimum_grid:
            return
        # The capacity pre-check (the request_rerun mirror; 261015-ehc
        # EHC-3 replaced in place by 16-03 D16-10) BEFORE pushing the
        # confirm — y is never reached on a refused machine (a
        # ZERO-ARG read, Pitfall 3 — a resume is a one-worker plain
        # launch)
        blocked_getter = getattr(
            self._launcher, "single_gpu_launch_blocked", None)
        blocked = (blocked_getter()
                   if blocked_getter is not None else None)
        if blocked:
            roots = ", ".join(blocked.roots)
            workers = blocked.requested_workers
            self.app.notify(
                S.LNC_SINGLE_GPU_BLOCKED.format(roots=roots, workers=workers,
                                                n=blocked.gpu_count),
                severity="error")
            return
        pairs = len(message.pairs)
        self.app.push_screen(LaunchConfirmModal(
            message=S.MON_RESUME_CONFIRM.format(
                pairs=pairs,
                seeds=", ".join(str(seed) for seed in message.seeds),
                n=pairs * len(message.seeds)),
            on_confirm=lambda: self._resume_pipeline(message.root)))

    @work(exclusive=True, thread=True, group="mon-rerun")
    def _run_resume_launch(self, root: str, run_id: int,
                           phrase: "str | None" = None) -> None:
        """The [e] resume launch (261018-toe): RE-DERIVE the pairs/
        seeds/lane off the event loop (the WR-02/03 one-shared-
        derivation discipline — the confirmed GPU spend and the
        executed GPU spend share the derivation), refuse loudly when
        nothing is derivable, then launch through the materialized-
        pairs seam (``launch_from_pairs`` -> the delegated
        ``launch_from_failures`` pipeline verbatim: single-GPU
        stage-0, official-keys, the E2' phrase gate over the
        pairs×seeds effective matrix). The outcome rides the SHARED
        RerunFinished handler — the E2' phrase re-prompt routes back
        through THIS worker via the resume=True flag).

        261020-blt: the SCOPE LAW — this derivation reads the SERVICE
        cells_view (the root-wide discovered truth), so the screen's
        planned-cell union never leaks a synthesized row into the
        confirmed/executed GPU spend."""
        try:
            cells = self._service.cells_view(root)
            rows = {f"{row.model}__{row.task}": row
                    for row in (cells or ())}
            pairs = sweep_monitor.incomplete_pairs_view(cells)
            if not pairs:
                self.post_message(self.RerunFailed(
                    S.MON_RESUME_NOTHING.format(root=root),
                    root, run_id))
                return
            seeds = derive_rerun_seeds((), rows)
            if not seeds:
                self.post_message(self.RerunFailed(
                    S.MON_RERUN_NO_SEEDS, root, run_id))
                return
            peft, config_variant = self._service.rerun_lane(root)
            launch_getter = getattr(
                self._launcher, "launch_from_pairs", None)
            if launch_getter is None:
                self.post_message(self.RerunFailed(
                    "launch_from_pairs seam unavailable on the "
                    "launcher", root, run_id))
                return
            outcome = launch_getter(
                pairs, seeds, root,
                peft=peft, config_variant=config_variant, phrase=phrase)
        except Exception as exc:  # noqa: BLE001 — WR-03: post-confirm
            # worker death surfaces, never a silent no-op launch
            self.post_message(self.RerunFailed(
                str(exc) or repr(exc), root, run_id))
            return
        self.post_message(self.RerunFinished(
            outcome, root, run_id, resume=True))

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


