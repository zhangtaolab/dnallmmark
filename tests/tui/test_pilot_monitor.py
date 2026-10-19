"""
Tier-2 Pilot suite for the monitor screen (Phase 11, 11-07; menu slot 5,
D-03/D-09/D-13; 261018-kvj two-tab redesign over the 11-04 scanner).

Pins the slot-5 TWO-TAB surface (the maintainer's 2026-10-18 15:01
contract) and its app/nav wiring against the REAL ``DnallmMarkTui``
with constructor-injected deterministic fakes (no real filesystem
scan, no real registry read, no real subprocess, no real sleep — the
D-03 discipline; the cadence is proven by directly invoking the
interval callbacks plus fake call counters, never by sleeping):

- The tabs: 正在运行/Running (default landing, one card per live run,
  multi-GPU worker rows INSIDE one card) and 历史/History (completed /
  interrupted runs, newest activity first, the dual-presence badge);
  left/right/tab all switch; count badges render on both titles.
- The card: run name, manifest scale (honest unknown), done/total +
  10-cell bar, the current-cell line (per-cell progress/ETA grammar),
  the resume note; enter drills the run's (model, task) snapshot
  (RunCellsModal -> CellDetailModal).
- The scoped keys: k/t/f act on the FOCUSED tab's selection (registry
  kill gate, tee/no-tee, failures) and refuse honestly without one; a
  and r stay screen-global; the Running tab's empty state's enter
  routes to slot 4 (the ONLY launch gate).
- #41 optimistic paint (skeleton + scanning note at mount, zero
  fabricated rows), graduation toasts on observed running->terminal
  transitions, the vanished-root degradation, the responsiveness proof
  while a scan blocks, and the 08g session-survival pair (fresh screen
  per nav + the shared MonitorSession).
- 261018-rze (the cadence render gates, the maintainer's 2026-10-18
  19:57 flicker report): a steady tick over UNCHANGED data performs
  ZERO widget writes with the ListItem identity preserved, a changed
  progress updates the card's Labels IN PLACE, ``_render_all`` is
  inert under a stacked modal and resumes after dismissal, and
  ``_focus_active`` no-ops when the target already holds focus (both
  branches).
"""

import re
import time
from contextlib import contextmanager
from pathlib import Path
from typing import cast
from unittest import mock

from rich.text import Text
from textual.screen import ModalScreen
from textual.widgets import (
    DataTable,
    Label,
    ListItem,
    ListView,
    RichLog,
    Static,
)

import tui.screens.monitor as monitor_screen_module
from tui.app import DnallmMarkTui
from tui.screens.monitor import MonitorScreen
from tui.screens.nav import BottomBar, TopMenuBar
from tui.screens.selection import PresetMenu, SelectionData
from tui.services import registries as registries_service
from tui.services.download_queue import merge_presence
from tui.services.sweep_launcher import (
    EnvPreflight,
    GateRefusal,
    LaunchOutcome,
)
from tui.services.sweep_monitor import (
    CELL_COMPLETED,
    CELL_FAILED,
    CELL_INTERRUPTED,
    CELL_QUEUED,
    CELL_RUNNING,
    CELL_SKIPPED,
    ETA_NONE,
    ETA_POINT,
    SWEEP_ARTIFACTS_ONLY,
    SWEEP_FINISHED,
    SWEEP_RUNNING,
    CellProgress,
    CellRow,
    CellSeed,
    CurrentCell,
    EtaEstimate,
    FailureRow,
    FrontierSnapshot,
    ScanResult,
    SweepStats,
    SweepSummary,
)
from tui.strings import (
    MON_ATTACHED_TOAST,
    MON_COL_SEED,
    MON_DETAIL_STEPS,
    MON_FAILURES_EMPTY,
    MON_GRADUATED_DONE_TOAST,
    MON_HISTORY_EMPTY,
    MON_HISTORY_RERUN_BADGE,
    MON_LOG_TEE_LINE,
    MON_PROGRESS_INDETERMINATE,
    MON_RESUME_NOTE,
    MON_RUNNING_EMPTY,
    MON_SCAN_NOTE,
    MON_SCANNING,
    MON_SCREEN_TITLE,
    MON_STATE_DONE,
    MON_STATE_INTERRUPTED,
    MON_STATE_QUEUED,
    MON_STATE_RUNNING,
    MON_STRIP_ELAPSED,
    MON_STRIP_ETA,
    MON_STRIP_ETA_RANGE,
    MON_STRIP_RATE,
    MON_TAB_COUNT,
    MON_TAB_HISTORY,
    MON_TAB_RUNNING,
    MON_TOTAL_UNKNOWN,
)

# The i18n grep lock (the test_pilot_env_check.py precedent): the new
# screen module joins the zero-Chinese-literals scan (11-05 contract
# note — each new Pilot suite adds its screen module to its tuple).
_MONITOR_MODULE_FILE = Path(monitor_screen_module.__file__)
_GREP_LOCK_MODULES = (
    _MONITOR_MODULE_FILE,
)


# =====================================================================
# Deterministic fakes (D-03: no real scan / registry / state / spawn)
# =====================================================================

def _summary(root, state, done=None, total=None, mtime=None):
    """One SweepSummary fixture (root name -> tmp-ish path string)."""
    return SweepSummary(
        root=Path(f"/scans/{root}"), state=state,
        done=done if done is not None else 0,
        total=total, newest_mtime=mtime)

def _eta(mode, point=None, lo=None, hi=None):
    return EtaEstimate(mode, point, lo, hi)

def _stats(done=0, total=None, current=None, elapsed=None, eta=None):
    return SweepStats(
        done=done, total=total, current=current,
        elapsed_seconds=elapsed,
        eta=eta if eta is not None else _eta(ETA_NONE))

def _current(model, task, seed):
    return CurrentCell(model=model, task=task, seed=seed)

def _row(model, task, seeds, fractions=None, mtime=None):
    """One CellRow fixture; seeds maps seed -> machine state; fractions
    maps seed -> tuple of (frac_name, state) pairs."""
    cells = []
    for seed, state in seeds.items():
        cells.append(CellSeed(
            seed=seed, state=state,
            fraction_states=fractions.get(seed) if fractions else None))
    return CellRow(model=model, task=task, seeds=tuple(cells),
                   newest_mtime=mtime)


class FakeMonitorService:
    """The monitor-service fake (the injection seam's fake side).

    Deterministic and recording: scripted per-root scans/cells/stats;
    every call counted. The screen never touches the artifact tree
    except through this seam (the plan's rendering-only prohibition).
    """

    def __init__(self, scans=None, cells=None, stats=None,
                 frontiers=None, failures=None, tails=None,
                 resume_counts=None, scales=None,
                 valid_roots=(), manual_roundtrip=None, records=None,
                 rerun_lanes=None, progress=None,
                 delete_raises=None):
        self._scans = list(scans) if scans else []
        self._cells = dict(cells or {})
        self._stats = dict(stats or {})
        self._frontiers = dict(frontiers or {})
        # C4J-3 (261015-c4j): the entries_progress fake —
        # {(model, task): CellProgress}; absent from every pre-C4J fake
        # so the screen's tolerant getattr seam stays pinned by omission
        self._progress = dict(progress or {})
        # WR-02 staging: a LIST value is a per-call SEQUENCE of reads
        # (each failures_view call pops the next while more than one
        # remains, the last is sticky) so a test can stage a DIFFERENT
        # worker-side re-read than the confirm-side one; a TUPLE value
        # is ONE sticky read (the pre-existing fixture shape)
        self._failures = {
            str(key): (list(value) if isinstance(value, list) else [value])
            for key, value in (failures or {}).items()}
        self._tails = dict(tails or {})
        self._resume = dict(resume_counts or {})
        self._scales = dict(scales or {})
        self._valid_roots = set(valid_roots)
        self._manual_roundtrip = (
            manual_roundtrip if manual_roundtrip is not None else [])
        self._records = dict(records or {})
        self._rerun_lanes = dict(rerun_lanes or {})
        # 261018-toe ([d]): the delete_root scripting — a raiser for the
        # WR-03 surface; the recording lists prove the seam call
        self._delete_raises = delete_raises
        self.full_calls = []
        self.frontier_calls = []
        self.cells_calls = []
        self.stats_calls = []
        self.progress_calls = []
        self.failures_calls = []
        self.tail_calls = []
        self.record_calls = []
        self.rerun_lane_calls = []
        self.added_roots = []
        self.delete_calls = []
        self.removed_manual_roots = []

    # ----- the scan surface -----

    #: optional degradation hooks (Task 3): a gate the scan waits on
    #: (the responsiveness proof) and a one-shot throw (the corrupt
    #: tree beyond the loader's tolerance).
    full_scan_gate = None
    full_scan_throws = False

    def full_scan(self, prev_watermarks=None):
        self.full_calls.append(dict(prev_watermarks or {}))
        if self.full_scan_throws:
            self.full_scan_throws = False
            raise RuntimeError("damaged artifact tree")
        gate = self.full_scan_gate
        if gate is not None:
            gate.wait(timeout=5.0)   # bounded: a bug never hangs the lane
        if self._scans:
            self._last_scan = self._scans.pop(0)
        return getattr(self, "_last_scan",
                       ScanResult(sweeps=(), watermarks={}))

    def frontier_scan(self, root):
        self.frontier_calls.append(str(root))
        return self._frontiers.get(str(root), FrontierSnapshot(
            root=Path(root), state=SWEEP_ARTIFACTS_ONLY,
            newest_mtime=None, newest_cell=None, cell_states={}))

    def cells_view(self, root):
        self.cells_calls.append(str(root))
        return self._cells.get(str(root), ())

    def entries_progress(self, root):
        self.progress_calls.append(str(root))
        return dict(self._progress)

    def stats(self, root, expected_total=None, fallback_start=None):
        self.stats_calls.append((str(root), expected_total,
                                 fallback_start))
        return self._stats.get(
            str(root), _stats(done=0, total=None))

    def sweep_scale(self, root):
        return self._scales.get(str(root))

    def resume_count(self, root):
        return self._resume.get(str(root), 0)

    # ----- the modal surfaces -----

    def failures_view(self, root):
        self.failures_calls.append(str(root))
        scripted = self._failures.get(str(root))
        if scripted is None:
            return ()
        if len(scripted) > 1:
            return scripted.pop(0)   # WR-02: the staged next read
        return scripted[0]

    def rerun_lane(self, root):
        self.rerun_lane_calls.append(str(root))
        return self._rerun_lanes.get(str(root), ("none", "none"))

    def cell_record(self, root, model, task, seed):
        self.record_calls.append((str(root), model, task, seed))
        return self._records.get((str(root), model, task, seed))

    def read_log_tail(self, path, max_lines=200, max_bytes=65536):
        self.tail_calls.append(str(path))
        return self._tails.get(str(path))

    # ----- the attach surface -----

    def is_sweep_root(self, path):
        return str(path) in self._valid_roots or Path(
            str(path)).name in self._valid_roots

    def add_manual_root(self, path):
        self.added_roots.append(str(path))
        if self._manual_roundtrip:
            return self._manual_roundtrip.pop(0)
        return True

    # ----- the [d] delete surface (261018-toe) -----

    def delete_root(self, root):
        """The scripted delete seam: records the resolved root and
        optionally raises (the WR-03 surface); the outcome vocabulary is
        the SCREEN's (the worker computes refused_live itself)."""
        self.delete_calls.append(str(root))
        if self._delete_raises is not None:
            raise self._delete_raises

    def remove_manual_root(self, path):
        """The best-effort manual-root hygiene recording."""
        self.removed_manual_roots.append(str(path))
        return True


class FakeMonitorLauncher:
    """The launcher-seam fake for the monitor screen (recorded)."""

    def __init__(self, preflight=None, live=(), tee=None,
                 rerun_outcomes=None, env_raises=None,
                 single_gpu_blocked=None,
                 kill_outcomes=None, kill_raises=None,
                 resume_outcomes=None, live_matrices=None):
        self._preflight = (preflight if preflight is not None
                           else EnvPreflight(
                               can_launch=True, reasons=(),
                               failed_kernels=()))
        self._live = tuple(live)
        self._tee = dict(tee or {})
        self._rerun_outcomes = (
            list(rerun_outcomes) if rerun_outcomes else None)
        # 261018-toe ([e]): the launch_from_pairs scripting — a
        # per-call outcome list (the rerun_outcomes pattern)
        self._resume_outcomes = (
            list(resume_outcomes) if resume_outcomes else None)
        self._env_raises = env_raises
        # EHC-3 (261015-ehc): the single-GPU guard seam (None = the
        # method absent-equivalent — never blocks)
        self._single_gpu_blocked = single_gpu_blocked
        # 261016-vxr (VXR-2): the kill_sweep scripting — a per-call
        # outcome list (popped per call, the rerun_outcomes pattern), a
        # raiser for the WR-03 surface, and the recording list
        self._kill_outcomes = list(kill_outcomes) if kill_outcomes else None
        self._kill_raises = kill_raises
        # 261019-o8e: the live_sweep_matrices fake — None (the default)
        # keeps the method UNDEFINED (pin-by-omission, the
        # entries_progress precedent: every pre-existing fake keeps
        # exercising the root-wide fallback); a dict value is the sticky
        # return; a callable is invoked per read (arbitrary scripting:
        # the mutation legs read a mutable holder, the raising leg
        # raises).
        if live_matrices is not None:
            if callable(live_matrices):
                self.live_sweep_matrices = live_matrices
            else:
                def _sticky_matrices():
                    return live_matrices
                self.live_sweep_matrices = _sticky_matrices
        self.env_calls = 0
        self.rerun_calls = []
        self.resume_calls = []
        self.kill_calls = []

    #: optional kill-blocking gate (VXR-2, the responsiveness proof):
    #: kill_sweep waits on it — the full_scan_gate precedent.
    kill_gate = None

    def env_preflight(self, kernels=None):
        self.env_calls += 1
        if self._env_raises is not None:
            raise self._env_raises
        return self._preflight

    def launch_from_failures(self, failures_path, seeds, output_root,
                             peft="none", config_variant="none",
                             phrase=None):
        self.rerun_calls.append((str(failures_path), tuple(seeds),
                                 str(output_root), peft, config_variant,
                                 phrase))
        if self._rerun_outcomes:
            return self._rerun_outcomes.pop(0)
        return LaunchOutcome(
            spawned=True, root=str(output_root),
            tee_path="/state/logs/sweep_rerun.log", error=None)

    def launch_from_pairs(self, pairs, seeds, output_root,
                          peft="none", config_variant="none",
                          phrase=None):
        """The scripted [e] seam (261018-toe): records the derived
        pairs/seeds/lane + the threaded phrase, optionally pops the
        next staged outcome (the rerun_outcomes pattern)."""
        self.resume_calls.append((tuple(pairs), tuple(seeds),
                                  str(output_root), peft, config_variant,
                                  phrase))
        if self._resume_outcomes:
            return self._resume_outcomes.pop(0)
        return LaunchOutcome(
            spawned=True, root=str(output_root),
            tee_path="/state/logs/sweep_resume.log", error=None)

    def phrase_matches(self, typed, output_root):
        return typed == Path(str(output_root)).name

    def live_sweeps(self):
        return self._live

    def kill_sweep(self, root):
        """The scripted kill channel (VXR-2): records the resolved root,
        optionally raises / blocks on the gate / pops the next outcome;
        the launcher's signalled default."""
        self.kill_calls.append(str(root))
        if self._kill_raises is not None:
            raise self._kill_raises
        gate = self.kill_gate
        if gate is not None:
            gate.wait(timeout=5.0)   # bounded: a bug never hangs the lane
        if self._kill_outcomes:
            return self._kill_outcomes.pop(0)
        return "signalled"

    def tee_path_for(self, root):
        return self._tee.get(str(root))

    def single_gpu_launch_blocked(self):
        return self._single_gpu_blocked


# ----- the app-shell fakes (the nav-shell suite's minimal set) -----

class _EnvCacheHitFake:
    """The minimal env-check service fake (same-day cache hit)."""

    def cached_results(self):
        from env_smoke import CheckResult

        from tui.strings import ENV_KERNEL_LABELS
        return ("2026-10-11 09:30", tuple(
            CheckResult(name=k, ok=True, lines=(f"PASS: {k}",))
            for k in ENV_KERNEL_LABELS
        ))

    def storage_rows(self):
        # F4W-04 (261014-f4w): frozen display rows — no filesystem scan.
        from tui.services.run_config import StorageRow

        return (
            StorageRow("model_root", "/golden/models", True),
            StorageRow("dataset_root", "/golden/datasets", False),
            StorageRow("output_root", "/golden/finetuned", True),
            StorageRow("log_dir", "/golden/logs", False),
            StorageRow("cache_dir", "/golden/cache", True),
        )

    def kernels(self):
        raise AssertionError("a cache-hit boot must never spawn the worker")

    def persist(self, results):
        raise AssertionError("a cache-hit boot must never persist")


class _SelectionFake:
    """The minimal selection-service fake (empty data, real grammar)."""

    def load_selection_data(self):
        return SelectionData()

    def preset_menu(self):
        return PresetMenu(options=(), load_error=None)

    def custom_names(self):
        return ()

    def save_preset(self, name, models, tasks):
        raise AssertionError("the monitor tests never save presets")

    def parse_filter(self, query):
        from tui.services import selection as selection_service

        return selection_service.parse_filter_query(query)

    def apply_filter(self, entries, parsed):
        from tui.services import selection as selection_service

        return selection_service.apply_filter(entries, parsed.terms)

    def import_template(self, path):
        raise AssertionError("never imports templates")

    def export_template(self, path, models, tasks):
        raise AssertionError("never exports templates")

    def export_tiers(self, path, models, tasks):
        raise AssertionError("never exports tiers")


class _QueueDriverFake:
    """The minimal download-queue fake (inert, driver surface only)."""

    def load(self):
        return None

    def entries(self):
        return ()

    def claim_next(self):
        return None

    def missing_datasets(self):
        return ()

    def merged_audit_tasks(self):
        return merge_presence(registries_service.load_n_audit(), {})

    def presence_rows(self):
        # DCL-03 (261014-dcl): the full-view read the slot-3 mount also
        # delegates through the queue — inert like the missing set
        return ()

    def probe_zenodo(self):
        return "not_public"

    def run_task(self, *args, **kwargs):
        raise AssertionError("the monitor tests never run queue tasks")


def _app(monitor=None, launcher=None):
    """The real app over the fake services (constructor injection)."""
    return DnallmMarkTui(
        env_check_service=_EnvCacheHitFake(),
        selection_service=_SelectionFake(),
        download_queue_service=_QueueDriverFake(),
        monitor_service=(monitor if monitor is not None
                         else FakeMonitorService()),
        monitor_launcher=(launcher if launcher is not None
                          else FakeMonitorLauncher()),
    )


# =====================================================================
# Pilot helpers
# =====================================================================

def _plain(content) -> str:
    """Plain text of a Static's content (cells may carry rich Text)."""
    return content.plain if isinstance(content, Text) else str(content)

def _label_text(screen, selector) -> str:
    return _plain(screen.query_one(selector, Label).content)

def _table_text(table: DataTable, row_key: str, column_key: str) -> str:
    """One DataTable cell as plain text."""
    value = table.get_cell(row_key, column_key)
    return value.plain if isinstance(value, Text) else str(value)

def _card_texts(screen, classes: str) -> "list[str]":
    """Every card line of one card class, in card order."""
    return [
        _plain(widget.content)
        for widget in screen.query(f".{classes}")]

def _toast_messages(app):
    """The active notification messages (the toast assertions)."""
    return [notification.message for notification in app._notifications]

async def _open_monitor(pilot, app):
    """Push the monitor screen and deterministically await its scans."""
    app.push_screen(app.build_monitor_screen())
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()

async def _settle(pilot, app, rounds=3):
    """Await sequential worker->handler chains (each round: workers,
    then the messages they posted)."""
    for _ in range(rounds):
        await app.workers.wait_for_complete()
        await pilot.pause()

def _three_state_scan():
    """The canonical three-root scan: running + finished + artifacts."""
    return ScanResult(sweeps=(
        _summary("finetuned", SWEEP_RUNNING, done=12, total=36,
                 mtime=3000.0),
        _summary("finetuned-e2e-rerun", SWEEP_FINISHED,
                 done=9300, total=9300, mtime=2000.0),
        _summary("seed-9527-artifacts", SWEEP_ARTIFACTS_ONLY, done=5,
                 mtime=1000.0),
    ), watermarks={})

# =====================================================================
# Task 1 — the two-tab shell (both grids, cards, history, scoped keys)
# =====================================================================

async def test_screen_composes_tabbed_regions_at_both_grids():
    """The two-tab frame composes at 120x40 AND 80x24 with both bars,
    the title bar (the cadence note BYTE-unchanged — the pty lane's
    monitor marker depends on it), the one-row tab header, and —
    261019-f0x — the B+D horizontal split (#mon-left 1fr beside the
    composed-but-hidden #mon-right pane placeholders)."""
    monitor = FakeMonitorService(scans=[_three_state_scan()])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert isinstance(screen, MonitorScreen)
        assert list(screen.query(TopMenuBar)), "the top bar renders"
        assert list(screen.query(BottomBar)), "the bottom bar renders"
        assert _label_text(screen, "#mon-screen-title") == MON_SCREEN_TITLE
        assert _label_text(screen, "#mon-scan-note") == MON_SCAN_NOTE, (
            "the D-09 cadence note is standing chrome on the title row"
        )
        assert screen.query_one("#mon-tab-header") is not None
        assert screen.query_one("#mon-content") is not None
        # 261019-f0x: the content region is the B+D split — the left
        # pane carries every existing child, the right pane's two
        # placeholder widgets exist (Task 2 activates the pane)
        assert screen.query_one("#mon-left") is not None
        assert screen.query_one("#mon-detail") is not None
        assert screen.query_one("#mon-right-log") is not None
        assert screen.query_one("#mon-right").display is True, (
            "wide + Running + cards: the D pane shows beside the matrix"
        )
        # the default landing is the Running tab, its card list focused
        assert screen._active_tab == "running"
        assert screen.focused is not None
        assert screen.focused.id == "mon-cards"

    monitor = FakeMonitorService(
        scans=[_three_state_scan()],
        cells={"/scans/finetuned": (
            _row("plant-dnamamba-6mer", "GUE__emp_H3",
                 {42: CELL_RUNNING, 43: CELL_QUEUED, 44: CELL_QUEUED}),)},
        stats={"/scans/finetuned": _stats(done=12, total=36)},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(80, 24)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert _label_text(screen, "#mon-screen-title") == MON_SCREEN_TITLE
        cards = screen.query_one("#mon-cards", ListView)
        assert len(cards) == 1, "the 80-col grid still carries the card"
        # the narrow degradation: the strip drops the bar and the rate,
        # the matrix drops to per-model count rows (no column header)
        strip = _card_texts(screen, "mon-card-strip")[0]
        assert "░" not in strip and "█" not in strip, (
            "the narrow strip drops the segmented bar"
        )
        assert "it/s" not in strip, "the narrow strip drops the rate"
        assert "12/36" in strip, "the fraction stays (data, not decor)"
        assert not screen.query(".mon-matrix-head"), (
            "the narrow matrix renders no column header"
        )
        narrow_rows = _card_texts(screen, "mon-matrix-row")
        assert len(narrow_rows) == 1, "one count row per model"
        assert narrow_rows[0].startswith("plant-dnamamba-6mer")
        assert "⏵1" in narrow_rows[0] and "◌2" in narrow_rows[0], (
            "the narrow row carries the model's glyph counts"
        )


async def test_tab_switch_keys_and_count_badges():
    """left, right, AND tab each move focus between the two tabs from
    either tab's focused list; the active tab header re-accents and the
    (n)/(m) count badges render on both titles."""
    monitor = FakeMonitorService(scans=[_three_state_scan()])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert _label_text(screen, "#mon-tab-running") == (
            f"{MON_TAB_RUNNING} {MON_TAB_COUNT.format(n=1)}")
        assert _label_text(screen, "#mon-tab-history") == (
            f"{MON_TAB_HISTORY} {MON_TAB_COUNT.format(n=2)}")

        await pilot.press("right")
        await pilot.pause()
        assert screen._active_tab == "history", (
            "right switches Running -> History")
        assert screen.focused.id == "mon-history", (
            "the History table takes the single focus")
        assert screen.query_one("#mon-history").display is True
        assert screen.query_one("#mon-cards").display is False
        # the active tab title swapped styling: the running title is no
        # longer the accented one (its content stays the same words)
        assert _label_text(screen, "#mon-tab-running") == (
            f"{MON_TAB_RUNNING} {MON_TAB_COUNT.format(n=1)}")

        await pilot.press("left")
        await pilot.pause()
        assert screen._active_tab == "running", (
            "left switches History -> Running")
        assert screen.focused.id == "mon-cards"

        await pilot.press("tab")
        await pilot.pause()
        assert screen._active_tab == "history", (
            "tab toggles to History even from the focused card list "
            "(the declared priority seam owns the key)")
        await pilot.press("tab")
        await pilot.pause()
        assert screen._active_tab == "running"


async def test_running_tab_renders_one_card_per_live_run():
    """261019-f0x (the B skeleton): the running card = ONE summary
    strip line (name + per-category counts + the done/total fraction +
    the deterministic 20-cell bar + minute-granularity elapsed + the
    point-ETA-with-wall-clock + the derived rate or the honest dash)
    over the matrix (head + one glyph row per model) — every number an
    existing service field or pure arithmetic over them."""
    from tui.services.sweep_monitor import format_eta

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=12, total=36, mtime=1.0),),
            watermarks={})],
        cells={"/scans/finetuned": (
            _row("plant-dnamamba-6mer", "GUE__emp_H3",
                 {42: CELL_RUNNING, 43: CELL_QUEUED, 44: CELL_QUEUED}),)},
        stats={"/scans/finetuned": _stats(
            done=12, total=36,
            current=_current("plant-dnamamba-6mer", "GUE__emp_H3", 42),
            elapsed=4360.0, eta=_eta(ETA_POINT, point=7560.0))},
        progress={
            ("plant-dnamamba-6mer", "GUE__emp_H3"): CellProgress(
                step=300, max_steps=1000, percent=30, eta_seconds=700.0)},
        resume_counts={"/scans/finetuned": 0},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        cards = screen.query_one("#mon-cards", ListView)
        assert len(cards) == 1, "one live run = one card"
        assert screen._card_order == ["/scans/finetuned"]
        strip = _card_texts(screen, "mon-card-strip")[0]
        assert "finetuned" in strip, "the strip leads with the root name"
        assert "12/36" in strip, "the stats fraction rides the strip"
        assert "⏵1" in strip and "◌2" in strip, (
            "the per-category counts (running 1, queued 2)"
        )
        assert "✓" not in strip and "✗" not in strip, (
            "zero-count categories render nothing (queued always does)"
        )
        # the 20-cell bar over the seed counts (1 running, 2 queued of
        # 3): floor 6/13 + the one leftover to running's larger
        # remainder — deterministic
        assert strip.count("█") == 7 and strip.count("░") == 13, (
            "the 20-cell floor+largest-remainder allocation"
        )
        assert MON_STRIP_ELAPSED.format(t="1h13m") in strip, (
            "minute granularity: 4360s -> 1h13m"
        )
        clock = time.strftime(
            "%H:%M", time.localtime(time.time() + 7560.0))
        assert MON_STRIP_ETA.format(
            eta=format_eta(7560.0), clock=clock) in strip, (
            "the point ETA + its wall-clock landing"
        )
        assert MON_STRIP_RATE.format(rate="1.0") in strip, (
            "the derived rate: (1000-300)/700 = 1.0 it/s, pure "
            "arithmetic over the parsed service fields"
        )
        # the matrix: head + one row per model, the group's seed glyphs
        head = _card_texts(screen, "mon-matrix-head")[0]
        assert "GUE__emp_H3" in head, "the task key heads its column"
        rows = _card_texts(screen, "mon-matrix-row")
        assert len(rows) == 1, "one row per model"
        assert rows[0].startswith("plant-dnamamba-6mer")
        assert "⏵◌◌" in rows[0], "the group's seed glyphs, seed order"
        assert not screen.query(".mon-card-resume"), (
            "a first run carries no resume note"
        )

    # the honest unknowns: no cells, no current cell, unknown total —
    # the strip renders the designed unknowns, never a fabricated line
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "cli-sweep", SWEEP_RUNNING, done=2, mtime=1.0),),
            watermarks={})],
        stats={"/scans/cli-sweep": _stats(done=2, total=None)},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        strip = _card_texts(screen, "mon-card-strip")[0]
        assert MON_TOTAL_UNKNOWN in strip
        assert MON_STRIP_ELAPSED.format(t="—") in strip, (
            "elapsed None renders the dash"
        )
        assert "≈" not in strip, "no derivable ETA -> no formatted ETA"
        assert "it/s" not in strip
        assert not _card_texts(screen, "mon-matrix-row"), (
            "no cells -> no matrix rows (never fabricated rows)"
        )


async def test_matrix_glyph_grid_and_style_only_highlight():
    """261019-f0x: the matrix paints EVERY (model, task) group's seed
    glyphs in the existing state vocabulary (models/tasks sorted) and
    the focused group's highlight is STYLE-ONLY — the reverse spans
    move with the focus while every row's plain WIDTH stays identical
    (in-place updates stay layout-stable)."""
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=2, total=6, mtime=1.0),),
            watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1",
                 {42: CELL_COMPLETED, 43: CELL_FAILED}),
            _row("model-a", "task-2", {42: CELL_RUNNING}),
            _row("model-b", "task-1", {42: CELL_QUEUED}),
            _row("model-b", "task-2",
                 {43: CELL_COMPLETED, 44: CELL_COMPLETED}),
        )},
        stats={"/scans/finetuned": _stats(done=2, total=6)},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert screen._focus_pos == (0, 0), (
            "the initial focus is the first card's (0, 0)"
        )
        rows = _card_texts(screen, "mon-matrix-row")
        assert len(rows) == 2, "one row per model (sorted)"
        assert rows[0].startswith("model-a") and rows[1].startswith(
            "model-b")
        # the glyph grid: per (model, task) the group's seed glyphs
        assert "✓✗" in rows[0], "model-a x task-1: completed + failed"
        assert "⏵" in rows[0], "model-a x task-2: running"
        assert "◌" in rows[1], "model-b x task-1: queued"
        assert "✓✓" in rows[1], "model-b x task-2: two completed"

        labels = list(screen.query(".mon-matrix-row"))
        widths_before = [len(label.content.plain) for label in labels]

        def reverse_spans(label) -> list:
            return [span for span in label.content.spans
                    if "reverse" in str(span.style)]

        assert reverse_spans(labels[0]), (
            "the focused group's glyph cells carry the reverse style"
        )
        assert not reverse_spans(labels[1]), (
            "unfocused rows carry no reverse span"
        )

        await pilot.press("right")
        await pilot.pause()
        assert screen._focus_pos == (0, 1), "right moves the column"
        rows_after = _card_texts(screen, "mon-matrix-row")
        assert [len(text) for text in rows_after] == widths_before, (
            "the highlight is style-only — every row keeps its width"
        )
        assert reverse_spans(labels[0]), (
            "the moved focus stays highlighted on its new column"
        )
        # the style move: the reverse span sits over the task-2 group's
        # glyph position (the second column), not the first
        row0_plain = rows_after[0]
        task2_offset = (row0_plain.find("⏵"))
        span = reverse_spans(labels[0])[0]
        assert span.start <= task2_offset < span.end


async def test_matrix_arrow_focus_moves_clamps_and_crosses_cards():
    """261019-f0x: ←/→ move the focused column (clamped at the row
    edges — no tab-switch); ↑/↓ move the model row and CROSS to the
    adjacent card at the edges (the ListView index follows
    programmatically, the focus landing on the adjacent card's
    first/last row, column carried)."""
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(
            _summary("run-a", SWEEP_RUNNING, done=1, total=8, mtime=2.0),
            _summary("run-b", SWEEP_RUNNING, done=2, total=8, mtime=1.0),
        ), watermarks={})],
        cells={
            "/scans/run-a": (
                _row("m1", "t1", {42: CELL_RUNNING}),
                _row("m1", "t2", {42: CELL_QUEUED}),
                _row("m2", "t1", {42: CELL_COMPLETED}),
                _row("m2", "t2", {42: CELL_FAILED}),
            ),
            "/scans/run-b": (
                _row("m3", "t3", {42: CELL_RUNNING}),
                _row("m4", "t3", {42: CELL_QUEUED}),
            ),
        },
        stats={"/scans/run-a": _stats(done=1, total=8),
               "/scans/run-b": _stats(done=2, total=8)},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        cards = screen.query_one("#mon-cards", ListView)
        assert cards.index == 0
        assert screen._focus_pos == (0, 0)
        await pilot.press("right")
        await pilot.pause()
        assert screen._focus_pos == (0, 1), "right: col 0 -> 1"
        assert screen._active_tab == "running", (
            "a focus move never switches tabs"
        )
        await pilot.press("right")
        await pilot.pause()
        assert screen._focus_pos == (0, 1), (
            "clamped at the row edge — no wrap, no tab-switch"
        )
        await pilot.press("down")
        await pilot.pause()
        assert screen._focus_pos == (1, 1), "down: row 0 -> 1"
        await pilot.press("down")
        await pilot.pause()
        assert screen._focus_pos == (0, 0), (
            "the card edge crosses to run-b's FIRST row"
        )
        assert cards.index == 1, "the ListView index follows the cross"
        await pilot.press("up")
        await pilot.pause()
        assert screen._focus_pos == (1, 0), (
            "the card edge back lands on run-a's LAST row, col carried"
        )
        assert cards.index == 0
        await pilot.press("left")
        await pilot.pause()
        assert screen._focus_pos == (1, 0), (
            "left clamps at col 0 of a one-task row (t1 only for m2)"
        )


async def test_click_selects_card_without_drill_then_enter_drills():
    """261019-n0w (the maintainer's live test): a mouse CLICK on a
    running card SELECTS and focuses that card and NEVER opens the
    RunCellsModal (the MatrixCardsList override drops the stock
    ``Selected`` post textual 8.2.8's click path fires); a following
    Enter — the keyboard action_select path — still drills.
    click = select/focus, Enter = drill."""
    from tui.screens.monitor import MatrixCardsList, RunCellsModal

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(
            _summary("run-a", SWEEP_RUNNING, done=1, total=8, mtime=2.0),
            _summary("run-b", SWEEP_RUNNING, done=2, total=8, mtime=1.0),
        ), watermarks={})],
        cells={
            "/scans/run-a": (
                _row("m1", "t1", {42: CELL_RUNNING}),
                _row("m1", "t2", {42: CELL_QUEUED}),
                _row("m2", "t1", {42: CELL_COMPLETED}),
                _row("m2", "t2", {42: CELL_FAILED}),
            ),
            "/scans/run-b": (
                _row("m3", "t3", {42: CELL_RUNNING}),
                _row("m4", "t3", {42: CELL_QUEUED}),
            ),
        },
        stats={"/scans/run-a": _stats(done=1, total=8),
               "/scans/run-b": _stats(done=2, total=8)},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        cards = screen.query_one("#mon-cards", MatrixCardsList)
        assert cards.index == 0, "the first card holds the cursor"
        # the plan's sanctioned fallback: the SECOND card sits below the
        # fold (the first card's ListItem stretches across the visible
        # list, so a positional pilot click cannot land on it) — post
        # the exact message the mouse path produces instead. The REAL
        # SGR mouse path stays pty-pinned in test_pty_driver.py.
        cards.children[1].post_message(
            ListItem._ChildClicked(cards.children[1]))
        await pilot.pause()
        assert cards.index == 1, "the click moved the card selection"
        assert screen.focused is cards, "the click focused the list"
        assert not isinstance(app.screen, RunCellsModal), (
            "a click NEVER opens the drill modal"
        )
        await pilot.press("enter")
        await _settle(pilot, app)
        assert isinstance(app.screen, RunCellsModal), (
            "Enter — the keyboard path — remains the ONLY drill trigger"
        )
        await pilot.press("escape")
        await pilot.pause()


async def test_highlighted_card_renders_without_block_cursor_fill():
    """261019-n0w (the all-blue left pane): the highlighted card — the
    ListItem under #mon-cards carrying the ``-highlight`` class —
    renders with NO block-cursor fill: the effective background is
    fully transparent and the text-style applies neither bold nor
    reverse (the app-level ID rule outranks BOTH of the ListView
    DEFAULT_CSS ``-highlight`` variants); the left pane reads as
    content, the group reverse glyphs + the pane's detail header stay
    the focus affordance."""
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=1, total=2, mtime=1.0),),
            watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_RUNNING}),)},
        stats={"/scans/finetuned": _stats(done=1, total=2)},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        cards = screen.query_one("#mon-cards", ListView)
        assert cards.index == 0
        item = cards.children[cards.index]
        assert "-highlight" in item.classes, (
            "the cursor row carries the highlight class"
        )
        assert item.styles.background.a == 0, (
            "the highlighted card paints NO fill — fully transparent"
        )
        assert not item.styles.text_style.bold, "no bold text-style"
        assert not item.styles.text_style.reverse, "no reverse text-style"


async def test_arrow_precedence_focus_vs_tab_switch():
    """261019-f0x binding precedence: with a focused card carrying
    >= 1 group ←/→ move the matrix focus and do NOT switch tabs; with
    cards but NO groups, on the empty Running tab, and on History they
    switch tabs exactly as before (the kvj contract); Tab always
    switches; History ↑/↓ still move the History table cursor (the
    delegated native actions)."""
    # with groups: right moves focus, never flips the tab (the scan
    # also carries a finished root so the History leg has rows to move
    # its cursor over — the delegation pin is non-vacuous)
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(
            _summary("finetuned", SWEEP_RUNNING, done=1, total=2,
                     mtime=2.0),
            _summary("old-run", SWEEP_FINISHED, done=1, total=1,
                     mtime=1.0),
        ), watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_RUNNING}),
            _row("model-a", "task-2", {42: CELL_QUEUED}),)},
        stats={"/scans/finetuned": _stats(done=1, total=2)},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        await pilot.press("right")
        await pilot.pause()
        assert screen._active_tab == "running"
        assert screen._focus_pos == (0, 1)
        await pilot.press("tab")
        await pilot.pause()
        assert screen._active_tab == "history", (
            "Tab always switches, even with a focused group"
        )
        # History up/down move the table cursor (delegated native)
        table = screen.query_one("#mon-history", DataTable)
        assert table.row_count == 1
        await pilot.press("down")
        await pilot.pause()
        assert screen.focused is table, (
            "the History table keeps the focus — no focus trap"
        )
        await pilot.press("left")
        await pilot.pause()
        assert screen._active_tab == "running", (
            "left on History switches back (no groups consulted there)"
        )

    # cards but NO groups (the kvj fixture shape): the arrows switch
    monitor = FakeMonitorService(scans=[_three_state_scan()])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert screen._card_order, "the card exists"
        assert screen._focused_group() is None, (
            "its fixture scripts no cell rows — no groups"
        )
        await pilot.press("right")
        await pilot.pause()
        assert screen._active_tab == "history", (
            "no groups on Running: right switches tabs exactly as before"
        )
        await pilot.press("left")
        await pilot.pause()
        assert screen._active_tab == "running"

    # the EMPTY Running tab: the arrows switch (the standing kvj pin)
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(), watermarks={})])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        await pilot.press("right")
        await pilot.pause()
        assert screen._active_tab == "history"
        await pilot.press("left")
        await pilot.pause()
        assert screen._active_tab == "running"


async def test_enter_drill_cursor_pins_to_focused_group():
    """261019-f0x: [enter] on the focused card opens the RunCellsModal
    with the modal's cursor PINNED to the focused group's row (the
    additive focus_key) — moving the matrix focus before the enter
    drills the SAME run but lands the modal cursor on the new group."""
    from tui.screens.monitor import RunCellsModal

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=1, total=2, mtime=1.0),),
            watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_COMPLETED}),
            _row("model-a", "task-2", {42: CELL_RUNNING}),)},
        stats={"/scans/finetuned": _stats(done=1, total=2)},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        await pilot.press("right")   # focus (0, 1) = model-a x task-2
        await pilot.pause()
        assert screen._focus_pos == (0, 1)
        await pilot.press("enter")
        await _settle(pilot, app)
        assert isinstance(app.screen, RunCellsModal)
        table = app.screen.query_one("#mon-runcells-table", DataTable)
        cursor_key = str(table.coordinate_to_cell_key(
            table.cursor_coordinate)[0].value)
        assert cursor_key == "model-a__task-2", (
            "the modal cursor opens on the focused group's row"
        )
        await pilot.press("escape")
        await pilot.pause()


# =====================================================================
# 261019-f0x Task 2 — the D right pane (focused-group detail + the
# live tee tail on the frontier cadence)
# =====================================================================

def _pane_fixture_monitor(tee_path=None, tails=None):
    """The right-pane fixture: one running root, one running seed with
    derivable progress (step/max/percent/eta -> a derivable rate), a
    second group for the focus-move pin."""
    return FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=1, total=2, mtime=1.0),),
            watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_RUNNING,
                                       43: CELL_QUEUED}),
            _row("model-a", "task-2", {42: CELL_COMPLETED}),)},
        stats={"/scans/finetuned": _stats(
            done=1, total=2,
            current=_current("model-a", "task-1", 42))},
        progress={
            ("model-a", "task-1"): CellProgress(
                step=300, max_steps=1000, percent=30, eta_seconds=700.0)},
        tails=dict(tails or {}),
    )


_PANE_TEE = "/state/logs/sweep_pane.log"


def _detail_plain(screen) -> str:
    return _plain(screen.query_one("#mon-detail", Static).content)


def _pane_log_text(screen) -> str:
    return "\n".join(line.text for line in screen.query_one(
        "#mon-right-log", RichLog).lines)


async def test_right_pane_detail_from_existing_fields_only():
    """(a)+(b): the pane's detail renders the focused group's header,
    one line per seed with the state glyph words, and the running
    seed's steps/percent/eta + the derived rate over the SHARED grammar
    — and NO loss/lr/epoch token ever renders in the detail (the log
    region carries them; T-f0x-02 — no underived field is stated)."""
    from tui.services.sweep_monitor import format_eta

    monitor = _pane_fixture_monitor(tails={
        _PANE_TEE: ("10:31:36 epoch 2.00  step 300/1000  loss 0.4077",
                    "10:31:53 epoch 2.02  step 310/1000  loss 0.4051")})
    launcher = FakeMonitorLauncher(tee={"/scans/finetuned": _PANE_TEE})
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert screen.query_one("#mon-right").display is True, (
            "wide + Running + cards: the pane shows"
        )
        detail = _detail_plain(screen)
        assert "model-a × task-1" in detail, "the focused group's header"
        assert MON_COL_SEED.format(seed=42) in detail
        assert MON_COL_SEED.format(seed=43) in detail, (
            "one line per seed, sorted"
        )
        assert MON_STATE_RUNNING in detail and MON_STATE_QUEUED in detail
        assert "300/1000 30%" in detail and "███" in detail, (
            "the shared steps/percent/bar grammar"
        )
        assert format_eta(700.0) in detail, "the checkpoint-pair eta"
        assert MON_STRIP_RATE.format(rate="1.0") in detail, (
            "the derived rate (1000-300)/700"
        )
        # 261019-n0w: the D composition's two new lines sit between the
        # header and the first seed line — (a) the 20-cell bar line
        # (6 filled + 14 open at 30%), (b) the step/max + point-ETA line
        detail_lines = detail.split("\n")
        assert detail_lines[0] == "model-a × task-1", "the header first"
        bar_line = detail_lines[1]
        assert "█" * 6 in bar_line and "░" * 14 in bar_line, (
            "the 20-cell bar: 6 filled + 14 open at 30%"
        )
        assert "30%" in bar_line
        assert MON_STRIP_RATE.format(rate="1.0") in bar_line, (
            "the bar line carries the derived rate"
        )
        step_line = detail_lines[2]
        assert MON_DETAIL_STEPS.format(step=300, max=1000) in step_line, (
            "the step/max line (zh == en data-forward)"
        )
        # the point ETA + wall clock — parens shaped for either active
        # language (en "(HH:MM)", zh "（HH:MM）")
        assert re.search(
            rf"{re.escape(format_eta(700.0))}\s*[（(]\d{{2}}:\d{{2}}[）)]",
            step_line), "the point ETA with its wall clock"
        assert MON_COL_SEED.format(seed=42) in detail_lines[3], (
            "the per-seed lines follow the two new lines"
        )
        # (b) the no-fabrication pin: the log lines mention loss/epoch,
        # the DETAIL never does
        for token in ("loss", "epoch", "lr"):
            assert token not in detail, (
                f"the detail region must never state {token} — the log "
                "region carries it"
            )
        log_text = _pane_log_text(screen)
        assert "loss 0.4077" in log_text and "epoch 2.00" in log_text, (
            "the log region carries the verbatim tee lines"
        )
        assert MON_LOG_TEE_LINE.format(path=_PANE_TEE) in log_text, (
            "the dim tee line names the file"
        )


async def test_right_pane_detail_follows_focus_move():
    """(c): a focus move (the arrow) repaints the detail immediately —
    the header swaps to the new group from the caches. 261019-n0w: the
    two new D lines follow the FOCUSED group — a group with no progress
    entry renders NEITHER (never the previous group's numbers)."""
    monitor = _pane_fixture_monitor()
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert "model-a × task-1" in _detail_plain(screen)
        assert MON_DETAIL_STEPS.format(step=300, max=1000) in (
            _detail_plain(screen)), "the focused group carries the lines"
        await pilot.press("right")
        await pilot.pause()
        detail = _detail_plain(screen)
        assert "model-a × task-2" in detail, (
            "the detail header follows the focused group"
        )
        assert "model-a × task-1" not in detail
        assert MON_DETAIL_STEPS.format(step=300, max=1000) not in detail, (
            "task-2 has no progress entry — the step line is ABSENT"
        )
        assert "█" * 6 not in detail and "30%" not in detail, (
            "the bar line is ABSENT too — the lines follow the focus"
        )


@contextmanager
def _frozen_pane_clock():
    """261019-n0w: the pane's new step line carries the ETA wall clock
    (the strip's single-read convention over the monitor module's
    ``time``) — pin it so a minute boundary between the initial render
    and the steady-tick leg can never flip the lines signature (the
    golden drives' ``_frozen_mon_clock`` precedent)."""
    original = monitor_screen_module.time

    class _FrozenTime:
        @staticmethod
        def time():
            return 1_800_000_000.0

        @staticmethod
        def strftime(fmt, value):
            return original.strftime(fmt, value)

        @staticmethod
        def localtime(seconds=None):
            return original.localtime(
                1_800_000_000.0 if seconds is None else seconds)

    with mock.patch.object(monitor_screen_module, "time", _FrozenTime):
        yield


async def test_right_pane_tail_sig_gates_and_rewrite():
    """(d): a steady frontier tick over the SAME tail performs ZERO
    RichLog writes; a CHANGED scripted tail rewrites in place.
    261019-n0w: the steady leg also spies the #mon-detail Static —
    zero update calls (the lines-signature gate covers the new D
    bar/step lines; the rze law)."""
    monitor = _pane_fixture_monitor(tails={
        _PANE_TEE: ("[01:00:05] epoch 1", "[01:00:40] done")})
    launcher = FakeMonitorLauncher(tee={"/scans/finetuned": _PANE_TEE})
    app = _app(monitor=monitor, launcher=launcher)
    with _frozen_pane_clock():
        async with app.run_test(size=(120, 40)) as pilot:
            await _open_monitor(pilot, app)
            screen = app.screen
            log = screen.query_one("#mon-right-log", RichLog)
            assert "[01:00:05] epoch 1" in _pane_log_text(screen), (
                "the scripted tail landed"
            )
            clear_patcher, clear_mock = _spy(log, "clear")
            write_patcher, write_mock = _spy(log, "write")
            detail = screen.query_one("#mon-detail", Static)
            detail_patcher, detail_mock = _spy(detail, "update")
            try:
                screen._tick_frontier()
                await _settle(pilot, app)
                assert clear_mock.call_count == 0 and (
                    write_mock.call_count == 0), (
                    "a steady tick over the SAME tail performs zero "
                    "RichLog writes — the lines signature gates"
                )
                assert detail_mock.call_count == 0, (
                    "a steady tick performs zero #mon-detail writes — "
                    "the lines-signature gate covers the new D bar/step "
                    "lines (the rze law)"
                )
                monitor._tails[_PANE_TEE] = ("[02:00:05] epoch 2",)
                screen._tick_frontier()
                await _settle(pilot, app)
                assert clear_mock.call_count == 1, "the changed tail rewrites"
                assert "[02:00:05] epoch 2" in _pane_log_text(screen)
                assert "[01:00:05] epoch 1" not in _pane_log_text(screen)
            finally:
                clear_patcher.stop()
                write_patcher.stop()
                detail_patcher.stop()


async def test_right_pane_no_tee_unavailable_and_no_reads():
    """(e): a root with no tee renders MON_LOG_UNAVAILABLE once and
    schedules NO reads (the [t] modal's contract; the fabricated pty
    root keeps byte-silence by the same shape)."""
    from tui.strings import MON_LOG_UNAVAILABLE

    monitor = _pane_fixture_monitor()
    app = _app(monitor=monitor, launcher=FakeMonitorLauncher())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        screen._tick_frontier()
        await _settle(pilot, app)
        assert MON_LOG_UNAVAILABLE in _pane_log_text(screen), (
            "the CLI-launched state renders the designed copy"
        )
        assert monitor.tail_calls == [], (
            "no tee -> no read was ever scheduled"
        )


async def test_right_pane_hidden_when_narrow_t_still_opens():
    """(f): below the narrow threshold the whole pane hides and [t]
    remains the log surface (the modal still opens)."""
    from tui.screens.monitor import LogTailModal

    monitor = _pane_fixture_monitor()
    app = _app(monitor=monitor, launcher=FakeMonitorLauncher())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert screen.query_one("#mon-right").display is True
        await pilot.resize_terminal(80, 24)
        await pilot.pause()
        assert screen.query_one("#mon-right").display is False, (
            "the narrow grid hides the whole pane"
        )
        await pilot.press("t")
        await _settle(pilot, app)
        assert isinstance(app.screen, LogTailModal), (
            "[t] remains the log surface in narrow mode"
        )
        await pilot.press("escape")
        await pilot.pause()


async def test_right_pane_tail_write_suppressed_under_modal():
    """(g): a stacked modal suppresses the tail WRITE (the read may
    proceed — the next tick catches up): a changed tail arriving under
    a modal leaves the pane's content untouched, the tick after
    dismissal lands it."""
    class _DummyPaneModal(ModalScreen):
        def compose(self):
            yield Static("dummy")

    monitor = _pane_fixture_monitor(tails={
        _PANE_TEE: ("[01:00:05] epoch 1",)})
    launcher = FakeMonitorLauncher(tee={"/scans/finetuned": _PANE_TEE})
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert "[01:00:05] epoch 1" in _pane_log_text(screen)
        app.push_screen(_DummyPaneModal())
        await pilot.pause()
        monitor._tails[_PANE_TEE] = ("[03:00:05] epoch 3",)
        screen._tick_frontier()
        await _settle(pilot, app)
        assert "[01:00:05] epoch 1" in _pane_log_text(screen), (
            "the write skipped beneath the modal — the pane stays still"
        )
        assert "[03:00:05] epoch 3" not in _pane_log_text(screen)
        app.pop_screen()
        await pilot.pause()
        screen._tick_frontier()
        await _settle(pilot, app)
        assert "[03:00:05] epoch 3" in _pane_log_text(screen), (
            "the tick after dismissal catches up"
        )


# =====================================================================
# 261019-f0x Task 3 — the [w] wide toggle (matrix <-> the A-style dense
# per-cell table, the k9s narrow/wide precedent)
# =====================================================================

async def test_wide_toggle_dense_table_enter_and_restore():
    """[w]: the toggle paints the dense per-cell table (one row per
    seed — the state WORDS, the progress grammar on the running seed);
    enter drills the row's OWN root with the cursor at its group; [w]
    again restores the matrix with the prior focus preserved."""
    from tui.screens.monitor import RunCellsModal

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=1, total=2, mtime=1.0),),
            watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_RUNNING,
                                       43: CELL_QUEUED}),)},
        stats={"/scans/finetuned": _stats(
            done=1, total=2,
            current=_current("model-a", "task-1", 42))},
        progress={
            ("model-a", "task-1"): CellProgress(
                step=300, max_steps=1000, percent=30, eta_seconds=700.0)},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        # move the matrix focus to col 0 (already there) and row 0;
        # toggle wide — 261019-pe0 re-pin: [w] is the THREE-STATE cycle
        # (matrix -> tree -> wide), so reaching wide takes TWO presses
        # (the tree pass-through between them preserves the focus)
        await pilot.press("w")
        await pilot.pause()
        assert screen._wide is False, "the first w lands TREE, not wide"
        await pilot.press("w")
        await pilot.pause()
        assert screen._wide is True
        assert screen.focused.id == "mon-wide", (
            "the wide surface takes the focus"
        )
        wide = screen.query_one("#mon-wide", DataTable)
        assert wide.display is True and screen.query_one(
            "#mon-cards").display is False
        assert wide.row_count == 2, "one row per SEED (per-cell, not fold)"
        running_key = "/scans/finetuned::model-a__task-1::42"
        assert _table_text(wide, running_key, "state") == MON_STATE_RUNNING
        assert _table_text(wide, running_key, "seed") == "s42"
        assert _table_text(wide, running_key, "model") == "model-a"
        assert _table_text(wide, running_key, "task") == "task-1"
        assert "300/1000 30%" in _table_text(wide, running_key, "progress")
        assert _table_text(wide, running_key, "rate") == (
            MON_STRIP_RATE.format(rate="1.0"))
        queued_key = "/scans/finetuned::model-a__task-1::43"
        assert _table_text(wide, queued_key, "state") == MON_STATE_QUEUED
        assert _table_text(wide, queued_key, "progress") == "—", (
            "non-running seeds carry the dim dash"
        )
        # enter on the wide table drills the row's root with the
        # cursor pinned to its group
        await pilot.press("enter")
        await _settle(pilot, app)
        assert isinstance(app.screen, RunCellsModal)
        drill = app.screen.query_one("#mon-runcells-table", DataTable)
        assert str(drill.coordinate_to_cell_key(
            drill.cursor_coordinate)[0].value) == "model-a__task-1", (
            "the wide row's group pins the drill cursor"
        )
        await pilot.press("escape")
        await pilot.pause()
        # [w] back: the matrix restores with the pre-toggle focus (the
        # return press stays ONE w — wide -> matrix directly on the
        # 261019-pe0 cycle; the assert proves the focus survived BOTH
        # the tree pass-through AND the wide round trip)
        await pilot.press("w")
        await pilot.pause()
        assert screen._wide is False
        assert screen.query_one("#mon-cards").display is True
        assert screen.focused.id == "mon-cards"
        assert screen._focus_pos == (0, 0), (
            "the pre-toggle matrix focus survived the tree pass-through "
            "and the wide round trip"
        )


async def test_wide_keycap_running_tab_only():
    """The [w] keycap renders on the Running tab's footer ONLY (the
    d/e precedent mirrored)."""
    from tui.screens.nav import KeycapsStatic
    from tui.strings import MON_WIDE_KEYCAP

    monitor = _pane_fixture_monitor()
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        await pilot.pause()

        def footer_text() -> str:
            return str(screen.query_one(
                "#nav-left-keycaps", KeycapsStatic).content)

        assert "[w]" in footer_text() and MON_WIDE_KEYCAP in footer_text()
        await pilot.press("tab")
        await pilot.pause()
        assert "[w]" not in footer_text(), (
            "the History-tab footer drops the [w] keycap"
        )
        assert "[d]" in footer_text(), "the d/e projection stands"
        await pilot.press("tab")
        await pilot.pause()
        assert "[w]" in footer_text()


async def test_wide_mode_arrows_delegate_to_the_table():
    """Wide-mode arrows: ←/→ flip tabs (no matrix focus in wide mode)
    and ↑/↓ move the wide table's cursor through the delegated native
    actions (one code path, both tables)."""
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=1, total=2, mtime=1.0),),
            watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_RUNNING}),
            _row("model-a", "task-2", {43: CELL_QUEUED}),)},
        stats={"/scans/finetuned": _stats(done=1, total=2)},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        # 261019-pe0 re-pin: TWO w presses reach wide (the cycle passes
        # through tree first — the same truth, one more keypress)
        await pilot.press("w")
        await pilot.pause()
        await pilot.press("w")
        await pilot.pause()
        wide = screen.query_one("#mon-wide", DataTable)
        assert wide.row_count == 2
        before = wide.cursor_row
        await pilot.press("down")
        await pilot.pause()
        assert wide.cursor_row == before + 1, (
            "down moved the wide cursor (the delegated native action)"
        )
        await pilot.press("up")
        await pilot.pause()
        assert wide.cursor_row == before, "up moved it back"
        await pilot.press("right")
        await pilot.pause()
        assert screen._active_tab == "history", (
            "wide mode: the arrows switch tabs (no matrix focus)"
        )
        await pilot.press("left")
        await pilot.pause()
        assert screen._active_tab == "running"


# =====================================================================
# 261019-o8e — the live-pair scoping (the Running tab's current-sweep
# views scope to the LIVE sweep's planned pair set; every evidence gap
# falls back root-wide)
# =====================================================================

#: the maintainer's 2026-10-19 17:23 reused-root fixture: the ONE
#: live-planned pair (its seeds 42 running + 43/44 queued) beside THREE
#: residue models from previous smoke runs (classified interrupted)
#: under the SAME root; the stats seam is scripted ROOT-WIDE
#: (done=9 total=36 — deliberately different from the filtered truth
#: 0/3, so a fallback leak is unmissable).
_LIVE_MODEL = "hyenadna-large-1m-seqlen-hf"
_LIVE_TASK = "GUE__emp_H3"
_RESIDUE_MODELS = ("nucleotide-transformer-500m",
                   "plant-dnabert-6mer",
                   "plant-dnamamba-6mer")
_LIVE_PAIR = frozenset({(_LIVE_MODEL, _LIVE_TASK)})


def _reused_root_monitor(progress=None) -> FakeMonitorService:
    """The four-model reused-root cells fixture (the sorted model order
    puts the live model FIRST — the clamp pin relies on row 0 being
    live and row 1 residue). 261019-pe0: the optional ``progress`` maps
    (model, task) -> CellProgress for the tree-state pins (every
    pre-existing call site passes nothing and stays identical)."""
    return FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=9, total=36, mtime=1.0),),
            watermarks={})],
        cells={"/scans/finetuned": (
            _row(_LIVE_MODEL, _LIVE_TASK,
                 {42: CELL_RUNNING, 43: CELL_QUEUED, 44: CELL_QUEUED}),
            _row("nucleotide-transformer-500m", "GUE__emp_H3",
                 {42: CELL_INTERRUPTED}),
            _row("plant-dnabert-6mer", "GUE__emp_H3",
                 {42: CELL_INTERRUPTED, 43: CELL_INTERRUPTED}),
            _row("plant-dnamamba-6mer", "GUE__virus_species_4",
                 {42: CELL_INTERRUPTED}),
        )},
        stats={"/scans/finetuned": _stats(done=9, total=36)},
        progress=progress,
    )


async def test_live_pair_evidence_scopes_matrix_strip_and_wide():
    """261019-o8e — the maintainer's case (2026-10-19 17:23): ONE
    launched model at a REUSED root renders exactly ONE matrix row with
    its own seeds; the same-root residue (previous smoke runs,
    classified interrupted) appears NOWHERE in the card, the strip's
    glyph counts, the done/total (0/3 over the FILTERED seeds — not the
    root-wide stats seam's 9/36), or the [w] wide table — and the drill
    modal stays ROOT-WIDE (all four models) with its cursor pinned to
    the focused (filtered) group."""
    from tui.screens.monitor import RunCellsModal

    app = _app(monitor=_reused_root_monitor(),
               launcher=FakeMonitorLauncher(
                   live_matrices={"/scans/finetuned": _LIVE_PAIR}))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        rows = _card_texts(screen, "mon-matrix-row")
        assert len(rows) == 1, "exactly ONE model row — the launched one"
        # the 20-cell name column truncates the 27-char model name; the
        # "hyenadna" prefix is unique among the four fixture models
        assert rows[0].startswith("hyenadna"), (
            "the surviving row is the live-planned model"
        )
        strip = _card_texts(screen, "mon-card-strip")[0]
        card = strip + "\n" + "\n".join(rows)
        for residue in _RESIDUE_MODELS:
            assert residue not in card, (
                f"residue model {residue} leaked into the Running card"
            )
        assert "0/3" in strip and "9/36" not in strip, (
            "the done/total derives over the FILTERED seeds (0/3), "
            "never the root-wide stats seam (9/36)"
        )
        assert "⏵1" in strip and "◌2" in strip, (
            "the glyph counts are the filtered seeds only: 1 running + "
            "2 queued"
        )
        assert "⏸" not in strip, (
            "the three residue interrupted seeds never count"
        )
        # [w]: the wide table carries the filtered pair's three seeds —
        # 261019-pe0 re-pin: TWO presses (the cycle passes through tree
        # first; the tree rows are the same filtered set, pinned in the
        # dedicated tree test below)
        await pilot.press("w")
        await pilot.pause()
        await pilot.press("w")
        await pilot.pause()
        wide = screen.query_one("#mon-wide", DataTable)
        assert wide.row_count == 3, "one row per FILTERED seed"
        for row_key in wide.rows:
            assert _table_text(wide, row_key.value, "model") == (
                _LIVE_MODEL), "every wide row names the live model only"
        # [w] back, then the drill: ROOT-WIDE by design (the full-root
        # snapshot — residue stays drillable there), cursor pinned to
        # the focused (filtered) group's row
        await pilot.press("w")
        await pilot.pause()
        await pilot.press("enter")
        await _settle(pilot, app)
        assert isinstance(app.screen, RunCellsModal)
        table = app.screen.query_one("#mon-runcells-table", DataTable)
        assert table.row_count == 4, (
            "the drill modal keeps the FULL-ROOT truth (four models)"
        )
        assert str(table.coordinate_to_cell_key(
            table.cursor_coordinate)[0].value) == (
            f"{_LIVE_MODEL}__{_LIVE_TASK}"), (
            "the modal cursor still pins to the focused (filtered) group"
        )
        await pilot.press("escape")
        await pilot.pause()


async def test_live_evidence_fallbacks_never_scope():
    """261019-o8e — the fallback honesty: a launcher WITHOUT the
    method (every pre-existing fake), a root mapped to None
    (live-but-unknown argv), an EMPTY pair set (degenerate parse), and
    a RAISING live_sweep_matrices call ALL keep today's root-wide row
    set — a live card never renders an empty matrix through an
    evidence gap."""
    def _raising():
        raise RuntimeError("evidence unavailable")

    legs = (
        ("no method", None),
        ("root mapped to None", {"/scans/finetuned": None}),
        ("empty pair set", {"/scans/finetuned": frozenset()}),
        ("raising call", _raising),
    )
    for label, scripted in legs:
        app = _app(monitor=_reused_root_monitor(),
                   launcher=FakeMonitorLauncher(
                       live_matrices=scripted))
        async with app.run_test(size=(120, 40)) as pilot:
            await _open_monitor(pilot, app)
            screen = app.screen
            rows = _card_texts(screen, "mon-matrix-row")
            assert len(rows) == 4, (
                f"fallback leg ({label}): ALL FOUR models render — "
                "today's root-wide behavior, never empty"
            )
            strip = _card_texts(screen, "mon-card-strip")[0]
            assert "9/36" in strip, (
                f"fallback leg ({label}): the stats-seam done/total "
                "precedence stands"
            )


async def test_live_pair_set_change_rebuilds_then_steady_tick_silent():
    """261019-o8e — the gate law over the filter transition: evidence
    first arrives root-wide-scoped (the root ABSENT from a fresh empty
    dict -> four rows), then the scripted pair set narrows it -> the
    ListView REBUILDS once (ListItem identity changes; the filtered
    models/tasks tuples ARE the cards sig's shape legs), and one more
    tick over the SAME evidence performs ZERO widget writes with the
    ListItem identity surviving (the rze zero-write idiom)."""
    holder: dict = {}
    app = _app(monitor=_reused_root_monitor(),
               launcher=FakeMonitorLauncher(
                   live_matrices=lambda: holder))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        cards = screen.query_one("#mon-cards", ListView)
        root_wide_item = cards.children[0]
        assert len(_card_texts(screen, "mon-matrix-row")) == 4, (
            "the root is absent from the (fresh, empty) evidence dict: "
            "the root-wide first paint"
        )
        holder["/scans/finetuned"] = _LIVE_PAIR
        screen._tick_frontier()
        await _settle(pilot, app)
        assert cards.children[0] is not root_wide_item, (
            "the live-pair-set change REBUILT through the existing "
            "structure signature"
        )
        rows = _card_texts(screen, "mon-matrix-row")
        assert len(rows) == 1 and rows[0].startswith("hyenadna")
        rebuilt_item = cards.children[0]
        clear_patcher, clear_mock = _spy(cards, "clear")
        label_spies = [_spy(label, "update")
                       for label in rebuilt_item.query(Label)]
        try:
            screen._tick_frontier()
            await _settle(pilot, app)
            assert clear_mock.call_count == 0, (
                "a steady tick over the SAME evidence never rebuilds"
            )
            for patcher, mocked in label_spies:
                assert mocked.call_count == 0, (
                    "a steady tick over the SAME evidence performs zero "
                    "card Label writes (the rze law)"
                )
        finally:
            clear_patcher.stop()
            for patcher, _mocked in label_spies:
                patcher.stop()
        assert cards.children[0] is rebuilt_item, (
            "the ListItem identity survives the steady tick"
        )


async def test_focus_clamps_into_filtered_set_on_evidence_transition():
    """261019-o8e — the focus clamp: with the focus sitting on a
    RESIDUE model's group (the root-wide phase), the arriving pair set
    narrows the shape and ``_normalize_focus`` clamps the stored
    position into the filtered set on the SAME render pass — the right
    pane's header names the clamped (live) group, never an empty pane,
    never a dangling residue focus."""
    holder: dict = {}
    app = _app(monitor=_reused_root_monitor(),
               launcher=FakeMonitorLauncher(
                   live_matrices=lambda: holder))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert screen._focus_pos == (0, 0)
        # real key presses (the suite's rule): down lands the focus on
        # row 1 — the first RESIDUE model in the sorted root-wide shape
        await pilot.press("down")
        await pilot.pause()
        assert screen._focus_pos == (1, 0)
        assert screen._focused_group()[1] in _RESIDUE_MODELS, (
            "the pre-transition focus sits on a residue group"
        )
        holder["/scans/finetuned"] = _LIVE_PAIR
        screen._tick_frontier()
        await _settle(pilot, app)
        assert screen._focus_pos == (0, 0), (
            "the residue focus clamped into the filtered shape"
        )
        assert screen._focused_group()[1] == _LIVE_MODEL, (
            "the focused group is the clamped (live) model"
        )
        detail = _detail_plain(screen)
        assert detail, "the pane never renders empty at the transition"
        assert detail.splitlines()[0].startswith(_LIVE_MODEL), (
            "the pane header names the clamped group (the 40-col pane "
            "truncates the 41-char header — the prefix is the pin)"
        )
        for residue in _RESIDUE_MODELS:
            assert residue not in detail, (
                f"the clamped pane never names {residue}"
            )


# =====================================================================
# 261019-pe0 — the TREE state (the left pane's third state: the [w]
# cycle matrix -> tree -> wide, the auto-fallback when the matrix
# cannot fit, the locked navigation contract, the click law, and the
# gate-law extension to the per-card RunCardTree)
# =====================================================================

#: Eight 20-char task keys — the overflow fixture (the matrix needs
#: 20 + 8x14 = 132 cells against the ~80-cell left pane at 120 cols,
#: so the auto default is TREE without any manual press).
_OVERFLOW_TASKS = tuple(
    f"GUE__overflow_task_{index:02d}" for index in range(8))


def _tree_nodes(tree):
    """Every model/task node of a card tree, in visible order."""
    for model_node in tree.root.children:
        yield model_node
        yield from model_node.children


def _visible_tree_nodes(tree) -> "list[tuple]":
    """The VISIBLE nodes' data keys, top to bottom (the public
    line-walk — what the operator's up/down moves through)."""
    keys: list = []
    line = 0
    while True:
        node = tree.get_node_at_line(line)
        if node is None:
            return keys
        keys.append(node.data)
        line += 1


def _node_labels(tree) -> "list[str]":
    """Every node's plain label (model + task nodes, tree order)."""
    return [node.label.plain if isinstance(node.label, Text)
            else str(node.label) for node in _tree_nodes(tree)]


async def test_tree_state_renders_model_and_task_nodes():
    """261019-pe0 — the tree state renders over the o8e reused-root
    fixture: ONE model node naming the live model with done/total 0/3
    over the FILTERED seeds (never the stats seam's 9/36), NO residue
    model node, its task child carrying the task key + the s42 running
    glyph + the parsed percent + the derived rate + the s43/s44 queued
    glyphs; [w] again lands wide, [w] again restores the matrix with
    the prior focus (the three-state cycle)."""
    from tui.screens.monitor import RunCardTree

    app = _app(monitor=_reused_root_monitor(progress={
        (_LIVE_MODEL, _LIVE_TASK): CellProgress(
            step=300, max_steps=1000, percent=30, eta_seconds=700.0)}),
        launcher=FakeMonitorLauncher(
            live_matrices={"/scans/finetuned": _LIVE_PAIR}))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        await pilot.press("w")
        await pilot.pause()
        assert screen._left_mode == "tree"
        tree = screen.query_one(
            "#mon-cards", ListView).children[0].query_one(RunCardTree)
        labels = "\n".join(_node_labels(tree))
        # the model node: the live model + the FILTERED done/total
        assert _LIVE_MODEL in labels and "0/3" in labels, (
            "the model node's done/total derives over the FILTERED "
            "seeds (the o8e basis)"
        )
        assert "9/36" not in labels, "never the root-wide stats seam"
        for residue in _RESIDUE_MODELS:
            assert residue not in labels, (
                f"residue model {residue} never gains a tree node"
            )
        # the task node: the key + the per-seed cluster with the compact
        # inline percent + rate on the running seed, glyph-only queued
        assert _LIVE_TASK in labels
        assert "s42" in labels and "s43" in labels and "s44" in labels
        assert "⏵" in labels and "◌" in labels
        assert "30%" in labels, "the parsed percent rides the task node"
        assert MON_STRIP_RATE.format(rate="1.0") in labels, (
            "the derived rate: (1000-300)/700 = 1.0 it/s"
        )
        # the cycle continues: wide, then matrix with the prior focus
        await pilot.press("w")
        await pilot.pause()
        assert screen._wide is True
        await pilot.press("w")
        await pilot.pause()
        assert screen._left_mode == "matrix"
        assert not list(screen.query(RunCardTree)), (
            "the matrix rebuild carries no tree widget"
        )
        assert screen._focus_pos == (0, 0), (
            "the pre-cycle matrix focus survives the round trip"
        )


async def test_tree_navigation_contract():
    """261019-pe0 — the LOCKED navigation contract (the maintainer's
    2026-10-19 18:14-18:16 ruling), driven ONLY with real key presses:
    up/down move between VISIBLE nodes clamped (NO card crossing in
    tree state — the matrix card-cross law is matrix-scoped); right
    expands-or-into-children; left collapses-or-to-parent (the
    invisible root is never a cursor target); Enter on a MODEL node
    toggles and NEVER opens a modal; Enter on a TASK node drills with
    the modal cursor pinned to that group; asterisk toggles
    expand/collapse-ALL; Tab ALWAYS switches (the kvj law)."""
    from tui.screens.monitor import RunCardTree, RunCellsModal

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=1, total=4, mtime=1.0),),
            watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_RUNNING}),
            _row("model-a", "task-2", {43: CELL_QUEUED}),
            _row("model-b", "task-1", {42: CELL_COMPLETED}),
            _row("model-b", "task-2", {42: CELL_FAILED}),)},
        stats={"/scans/finetuned": _stats(done=1, total=4)},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        await pilot.press("w")
        await pilot.pause()
        cards = screen.query_one("#mon-cards", ListView)
        tree = cards.children[0].query_one(RunCardTree)
        # entering tree pins the cursor onto the focused group's task
        # node (the focus unification)
        assert tree.cursor_node.data == (
            "task", "/scans/finetuned", "model-a", "task-1")
        # down: the next visible node (the second task child)
        await pilot.press("down")
        await pilot.pause()
        assert tree.cursor_node.data == (
            "task", "/scans/finetuned", "model-a", "task-2")
        # left on a task node -> the parent model node
        await pilot.press("left")
        await pilot.pause()
        assert tree.cursor_node.data == (
            "model", "/scans/finetuned", "model-a")
        assert tree.cursor_node.is_expanded
        # left on the EXPANDED model node -> collapses (children hidden)
        await pilot.press("left")
        await pilot.pause()
        assert tree.cursor_node.is_collapsed
        assert ("task", "/scans/finetuned", "model-a", "task-1") \
            not in _visible_tree_nodes(tree), (
                "the collapse hid the task children")
        # left on the collapsed top-level model -> no-op (the invisible
        # root is NEVER a cursor target)
        await pilot.press("left")
        await pilot.pause()
        assert tree.cursor_node.data == (
            "model", "/scans/finetuned", "model-a")
        # right on the COLLAPSED model -> expands WITHOUT moving
        await pilot.press("right")
        await pilot.pause()
        assert tree.cursor_node.data == (
            "model", "/scans/finetuned", "model-a")
        assert tree.cursor_node.is_expanded
        # right on the EXPANDED model -> into the first child
        await pilot.press("right")
        await pilot.pause()
        assert tree.cursor_node.data == (
            "task", "/scans/finetuned", "model-a", "task-1")
        # right on a task/leaf node -> no-op
        await pilot.press("right")
        await pilot.pause()
        assert tree.cursor_node.data == (
            "task", "/scans/finetuned", "model-a", "task-1")
        # up at the FIRST visible node clamps — NO card crossing (the
        # maintainer's tree up/down review flag)
        await pilot.press("up")
        await pilot.pause()
        assert tree.cursor_node.data == (
            "model", "/scans/finetuned", "model-a")
        await pilot.press("up")
        await pilot.pause()
        assert tree.cursor_node.data == (
            "model", "/scans/finetuned", "model-a")
        assert cards.index == 0, "the tree arrows never cross cards"
        # Enter on a MODEL node: toggles expansion, NEVER a modal
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        assert app.screen is screen, (
            "enter on a model node NEVER opens a modal"
        )
        assert tree.cursor_node.is_collapsed, "enter toggled the model"
        # Enter on a TASK node: drills with the cursor pinned to that
        # group's row (the _drill_focus_key truth)
        await pilot.press("right")   # re-expand (no move)
        await pilot.pause()
        await pilot.press("right")   # into the first child
        await pilot.pause()
        assert tree.cursor_node.data == (
            "task", "/scans/finetuned", "model-a", "task-1")
        await pilot.press("enter")
        await _settle(pilot, app)
        assert isinstance(app.screen, RunCellsModal)
        table = app.screen.query_one("#mon-runcells-table", DataTable)
        assert str(table.coordinate_to_cell_key(
            table.cursor_coordinate)[0].value) == "model-a__task-1", (
                "the drill cursor pins to the entered task node's group"
            )
        await pilot.press("escape")
        await pilot.pause()
        # asterisk from all-expanded: collapse ALL (only model nodes
        # remain visible)
        await pilot.press("*")
        await pilot.pause()
        for node in tree.root.children:
            assert node.is_collapsed
        visible = _visible_tree_nodes(tree)
        assert visible and all(key[0] == "model" for key in visible), (
            "no task node is visible after collapse-all"
        )
        # asterisk again: expand ALL
        await pilot.press("*")
        await pilot.pause()
        for node in tree.root.children:
            assert node.is_expanded
        assert len(_visible_tree_nodes(tree)) == 6
        # Tab ALWAYS switches Running/History from any tree position
        await pilot.press("tab")
        await pilot.pause()
        assert screen._active_tab == "history"


async def test_tree_click_selects_node_without_drill():
    """261019-pe0 — the CLICK LAW (the n0w precedent extended): a click
    on a tree node SELECTS and FOCUSES it and NEVER drills — the cursor
    moved, the ListView index followed to the clicked CARD (the
    two-card fixture makes this assertable), focus landed on the tree,
    and NO modal opened; Enter afterwards still drills the focused task
    node. The click is the synthetic events.Click carrying the exact
    style meta the REAL SGR path produces (the n0w sanctioned fallback
    — the second card sits below the fold at this grid); the real SGR
    path stays pty-pinned in Task 2."""
    from textual import events

    from tui.screens.monitor import RunCardTree, RunCellsModal

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(
            _summary("run-a", SWEEP_RUNNING, done=1, total=2, mtime=2.0),
            _summary("run-b", SWEEP_RUNNING, done=1, total=1, mtime=1.0),
        ), watermarks={})],
        cells={
            "/scans/run-a": (
                _row("m1", "t1", {42: CELL_RUNNING}),
                _row("m1", "t2", {43: CELL_QUEUED}),),
            "/scans/run-b": (
                _row("m3", "t3", {42: CELL_RUNNING}),),
        },
        stats={"/scans/run-a": _stats(done=1, total=2),
               "/scans/run-b": _stats(done=1, total=1)},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        cards = screen.query_one("#mon-cards", ListView)
        assert cards.index == 0
        await pilot.press("w")
        await pilot.pause()
        tree_b = cards.children[1].query_one(RunCardTree)
        target_key = ("task", "/scans/run-b", "m3", "t3")
        line = _visible_tree_nodes(tree_b).index(target_key)
        import rich.style
        from textual.style import Style

        # the cast: textual's Style (the runtime carrier of the meta
        # dict) duck-types rich's — the events.py annotation names the
        # rich class while the real event stream passes textual's
        tree_b.post_message(events.Click(
            widget=tree_b, x=6, y=line, delta_x=0, delta_y=0, button=0,
            shift=False, meta=False, ctrl=False,
            style=cast(rich.style.Style,
                       Style.from_meta({"line": line}))))
        await pilot.pause()
        await pilot.pause()
        assert tree_b.cursor_node.data == target_key, (
            "the click moved the tree cursor onto the clicked node"
        )
        assert cards.index == 1, "the click SELECTED the card"
        assert screen.focused is tree_b, "the click focused the tree"
        assert not isinstance(app.screen, RunCellsModal), (
            "a tree click NEVER opens the drill modal"
        )
        # Enter — the keyboard path — remains the ONLY drill trigger
        await pilot.press("enter")
        await _settle(pilot, app)
        assert isinstance(app.screen, RunCellsModal)


async def test_matrix_overflow_defaults_to_tree_and_manual_holds():
    """261019-pe0 — the AUTO-FALLBACK: a fixture whose task set exceeds
    the left pane's matrix budget renders TREE by default at (120, 40)
    with NO manual press; a manual [w] choice to matrix HOLDS across a
    steady cadence tick with unchanged structure; a STRUCTURAL change
    (a new task appears) resets the manual choice and the pane falls
    back to tree; a narrow-size boot derives honestly (the narrow
    matrix is per-model count rows — no task columns to overflow)."""
    from tui.screens.monitor import RunCardTree

    overflow_cells = tuple(
        _row("model-a", task, {42: CELL_QUEUED})
        for task in _OVERFLOW_TASKS)

    def _overflow_monitor(cells=overflow_cells):
        return FakeMonitorService(
            scans=[ScanResult(sweeps=(_summary(
                "finetuned", SWEEP_RUNNING, done=0, total=8, mtime=1.0),),
                watermarks={})],
            cells={"/scans/finetuned": cells},
            stats={"/scans/finetuned": _stats(done=0, total=8)})

    app = _app(monitor=_overflow_monitor())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        # the FIRST scan paint derived TREE with no manual press
        assert screen._left_mode == "tree"
        assert screen._left_mode_user is None, "auto, not manual"
        cards = screen.query_one("#mon-cards", ListView)
        assert cards.children[0].query_one(RunCardTree) is not None
        assert not _card_texts(screen, "mon-matrix-row")
        # the manual choice: two w presses reach matrix (tree -> wide ->
        # matrix on the cycle) and HOLD across a steady frontier tick
        await pilot.press("w")
        await pilot.pause()
        assert screen._left_mode == "wide"
        await pilot.press("w")
        await pilot.pause()
        assert screen._left_mode == "matrix"
        assert screen._left_mode_user == "matrix"
        assert _card_texts(screen, "mon-matrix-row"), (
            "the manual choice renders the matrix"
        )
        screen._tick_frontier()
        await _settle(pilot, app)
        assert screen._left_mode == "matrix", (
            "the manual choice holds across the steady tick"
        )
        # a STRUCTURAL change resets the manual choice -> auto (tree)
        monitor = screen._service
        monitor._cells["/scans/finetuned"] = overflow_cells + (
            _row("model-a", "GUE__overflow_task_99", {42: CELL_QUEUED}),)
        screen._tick_full()
        await _settle(pilot, app)
        assert screen._left_mode_user is None, (
            "the structural change reset the manual choice"
        )
        assert screen._left_mode == "tree", (
            "the pane fell back to the auto default (tree)"
        )
        assert screen.query(RunCardTree)

    # the narrow boot derives honestly: at (90, 40) the narrow matrix is
    # per-model COUNT rows (no task columns — the overflow the tree
    # solves is a column-count problem), so auto stays matrix
    app = _app(monitor=_overflow_monitor())
    async with app.run_test(size=(90, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert screen._narrow is True
        assert screen._left_mode == "matrix"
        assert screen._derive_left_mode() == "matrix", (
            "the narrow count-row matrix never overflows"
        )


async def test_tree_steady_tick_zero_write_and_rebuild_preserves_state():
    """261019-pe0 — the GATE LAW over the tree (the rze/f0x family
    extended): after the initial tree paint (model-b collapsed, the
    cursor parked on a task node), one steady tick over UNCHANGED data
    performs ZERO tree writes (no clear, no set_label) and zero
    ListView/Label writes; a node-set change (a new task) rebuilds the
    tree ONCE with every model's expansion state and the cursor node
    preserved (identity-equivalent by data key)."""
    from tui.screens.monitor import RunCardTree

    cells = tuple(
        _row("model-a", task, {42: CELL_QUEUED})
        for task in _OVERFLOW_TASKS[:6]) + (
        _row("model-b", "GUE__steady_task_1", {42: CELL_RUNNING}),)
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=0, total=7, mtime=1.0),),
            watermarks={})],
        cells={"/scans/finetuned": cells},
        stats={"/scans/finetuned": _stats(done=0, total=7)})
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        cards = screen.query_one("#mon-cards", ListView)
        assert screen._left_mode == "tree", "the overflow default"
        tree = cards.children[0].query_one(RunCardTree)
        # arrangement: model-b collapsed, the cursor on model-a's first
        # task node (the cache-sync messages land on the pauses)
        model_b = next(node for node in tree.root.children
                       if node.data[2] == "model-b")
        model_b.collapse()
        screen._tree_move(tree, tree.root.children[0].children[0])
        await pilot.pause()
        await pilot.pause()
        cursor_key = tree.cursor_node.data
        assert cursor_key[0] == "task"
        # the steady tick over UNCHANGED data: zero writes everywhere
        spies = {"tree clear": _spy(tree, "clear")}
        spies.update({
            f"node set_label {index}": _spy(node, "set_label")
            for index, node in enumerate(_tree_nodes(tree))})
        spies.update({
            f"card label {index} update": _spy(label, "update")
            for index, label in enumerate(
                cards.children[0].query(Label))})
        try:
            screen._tick_frontier()
            await _settle(pilot, app)
            for name, (_patcher, mocked) in spies.items():
                assert mocked.call_count == 0, (
                    f"a steady tree tick performed a {name} — the gate "
                    "law is broken"
                )
        finally:
            for patcher, _mocked in spies.values():
                patcher.stop()
        # the node-set change: a NEW task under model-a -> the rebuild
        monitor._cells["/scans/finetuned"] = cells + (
            _row("model-a", "GUE__steady_task_9", {42: CELL_QUEUED}),)
        screen._tick_full()
        await _settle(pilot, app)
        new_tree = cards.children[0].query_one(RunCardTree)
        assert new_tree is not tree, "the structure change rebuilt"
        new_model_b = next(node for node in new_tree.root.children
                           if node.data[2] == "model-b")
        assert new_model_b.is_collapsed, (
            "the collapsed model stayed collapsed through the rebuild"
        )
        assert new_tree.cursor_node.data == cursor_key, (
            "the cursor node survived the rebuild (same data key)"
        )
        assert screen._tree_find(
            new_tree, "/scans/finetuned", "model-a",
            "GUE__steady_task_9") is not None, (
                "the new task node is present after the rebuild"
            )


async def test_tree_focus_unification_feeds_right_pane():
    """261019-pe0 — the FOCUS UNIFICATION: matrix/tree/wide share the
    (model, task) coordinate. Entering tree from a matrix focus at
    (0, 1) lands the tree cursor on that model's SECOND task node with
    the pane naming it; a tree cursor move to another task node feeds
    the pane exactly as the matrix focus does; entering wide lands the
    wide cursor on the focused group's row; leaving wide repaints the
    matrix reverse highlight on the same group."""
    from tui.screens.monitor import RunCardTree

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=1, total=4, mtime=1.0),),
            watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_RUNNING}),
            _row("model-a", "task-2", {43: CELL_QUEUED}),
            _row("model-b", "task-1", {42: CELL_COMPLETED}),
            _row("model-b", "task-2", {42: CELL_FAILED}),)},
        stats={"/scans/finetuned": _stats(done=1, total=4)})
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        await pilot.press("right")
        await pilot.pause()
        assert screen._focus_pos == (0, 1)
        # entering tree: the cursor lands the focused group's task node
        await pilot.press("w")
        await pilot.pause()
        tree = screen.query_one(
            "#mon-cards", ListView).children[0].query_one(RunCardTree)
        assert tree.cursor_node.data == (
            "task", "/scans/finetuned", "model-a", "task-2")
        assert _detail_plain(screen).splitlines()[0] == (
            "model-a × task-2"), "the pane follows the tree cursor"
        # a tree cursor move feeds the pane (the exact matrix tail)
        await pilot.press("down")   # -> model-b (column carried)
        await pilot.pause()
        await pilot.press("down")   # -> model-b's first task node
        await pilot.pause()
        assert tree.cursor_node.data == (
            "task", "/scans/finetuned", "model-b", "task-1")
        assert _detail_plain(screen).splitlines()[0] == (
            "model-b × task-1")
        # entering wide: the cursor lands the focused group's row
        await pilot.press("w")
        await pilot.pause()
        assert screen._wide is True
        wide = screen.query_one("#mon-wide", DataTable)
        row_key = str(wide.coordinate_to_cell_key(
            wide.cursor_coordinate)[0].value)
        assert screen._wide_row_group(row_key) == (
            "/scans/finetuned", "model-b__task-1"), (
                "the wide cursor sits on the focused group's row"
            )
        # leaving wide: the matrix reverse highlight sits on the same
        # group
        await pilot.press("w")
        await pilot.pause()
        assert screen._left_mode == "matrix"
        focused = screen._focused_group()
        assert (focused[1], focused[2]) == ("model-b", "task-1"), (
            "the wide cursor's group became the matrix focus"
        )


async def test_history_tab_lists_runs_newest_first_with_states():
    """The History tab: finished runs carry the ✓ word, interrupted
    (prior-artifacts) runs the muted ⏸ word, rows sort newest activity
    first, and the progress column renders the fraction (never a bar
    on a non-running row)."""
    monitor = FakeMonitorService(scans=[_three_state_scan()])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        await pilot.press("right")
        await pilot.pause()
        table = screen.query_one("#mon-history", DataTable)
        order = [str(key.value) for key in table.rows]
        assert order == ["/scans/finetuned-e2e-rerun",
                         "/scans/seed-9527-artifacts"], (
            "the non-running roots list newest-activity first"
        )
        assert _table_text(table, "/scans/finetuned-e2e-rerun",
                           "state") == MON_STATE_DONE
        assert _table_text(table, "/scans/seed-9527-artifacts",
                           "state") == MON_STATE_INTERRUPTED
        assert "⏵" not in _table_text(table, "/scans/seed-9527-artifacts",
                                       "state")
        finished_progress = _table_text(
            table, "/scans/finetuned-e2e-rerun", "progress")
        assert "9300/9300" in finished_progress
        assert "█" not in finished_progress, "history rows carry no bar"
        assert _table_text(table, "/scans/seed-9527-artifacts",
                           "progress") == MON_TOTAL_UNKNOWN
        assert _table_text(table, "/scans/finetuned-e2e-rerun",
                           "root") == "finetuned-e2e-rerun"
        assert _table_text(table, "/scans/finetuned-e2e-rerun",
                           "activity") == time.strftime(
            "%m-%d %H:%M", time.localtime(2000.0)), (
            "the newest-activity cell renders the scan's mtime as local "
            "wall-clock data"
        )


async def test_dual_presence_badge_on_history_row():
    """A root with BOTH a live handle and historical cells (resume
    markers present — the same-root re-run workflow): its live card
    renders on Running AND its History row carries the re-run badge
    (surfaced with a badge, never deduplicated away)."""
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(
            _summary("finetuned", SWEEP_RUNNING, done=9300, total=9312,
                     mtime=2000.0),
            _summary("older-run", SWEEP_FINISHED, done=3, total=3,
                     mtime=1000.0),
        ), watermarks={})],
        stats={"/scans/finetuned": _stats(done=9300, total=9312)},
        resume_counts={"/scans/finetuned": 12},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        cards = screen.query_one("#mon-cards", ListView)
        assert len(cards) == 1, "the re-run root is a live card"
        resume_note = _card_texts(screen, "mon-card-resume")
        assert resume_note == [MON_RESUME_NOTE.format(n=12)]
        await pilot.press("right")
        await pilot.pause()
        table = screen.query_one("#mon-history", DataTable)
        order = [str(key.value) for key in table.rows]
        assert order == ["/scans/finetuned", "/scans/older-run"], (
            "the dual-presence row lists first (its live mtime is the "
            "freshest activity)"
        )
        root_cell = _table_text(table, "/scans/finetuned", "root")
        assert root_cell == f"finetuned {MON_HISTORY_RERUN_BADGE}", (
            "the History row carries the dual-presence badge"
        )
        assert _table_text(table, "/scans/older-run", "root") == (
            "older-run"), "the plain history row carries no badge"


async def test_mgpu_worker_roots_group_inside_one_card():
    """261018-kvj over delta A's fixture (12-05), re-pinned on the
    261019-f0x B skeleton: the two frozen ``{root}-mgpu-w{i}`` sibling
    worker roots render as ONE CARD whose strip names the GROUP and
    whose matrix carries the merged groups (the worker-row lines are
    retired with the old card body); the finished default root stays a
    History row."""
    from tui.services.sweep_monitor import format_eta

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(
            _summary("finetuned-mgpu-w0", SWEEP_RUNNING, done=4,
                     total=10, mtime=2000.0),
            _summary("finetuned-mgpu-w1", SWEEP_RUNNING, done=2,
                     total=20, mtime=1000.0),
            _summary("finetuned", SWEEP_FINISHED, done=6, total=6,
                     mtime=3000.0),
        ), watermarks={})],
        cells={"/scans/finetuned-mgpu-w0": (
            _row("model-a", "task-x", {42: CELL_RUNNING}),)},
        stats={
            "/scans/finetuned-mgpu-w0": _stats(
                done=4, total=10,
                current=_current("model-a", "task-x", 42),
                eta=_eta(ETA_POINT, point=3600.0)),
            "/scans/finetuned-mgpu-w1": _stats(
                done=2, total=20, eta=_eta(ETA_POINT, point=7200.0)),
        },
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        cards = screen.query_one("#mon-cards", ListView)
        assert len(cards) == 1, (
            "the two worker roots are ONE run card (the mgpu naming)"
        )
        strip = _card_texts(screen, "mon-card-strip")[0]
        assert strip.startswith(" finetuned"), (
            "the strip names the GROUP (the stripped base), never w0/w1"
        )
        assert "6/30" in strip, (
            "the fraction aggregates the roots' stats (4/10 + 2/20)"
        )
        assert MON_STRIP_ETA_RANGE.format(
            lo=format_eta(3600.0), hi=format_eta(7200.0)) in strip, (
            "TWO derivable roots -> the min-max ETA range (never a "
            "fabricated single point)"
        )
        assert not screen.query(".mon-card-worker"), (
            "the worker-row lines are retired with the old card body"
        )
        rows = _card_texts(screen, "mon-matrix-row")
        assert len(rows) == 1 and rows[0].startswith("model-a"), (
            "the merged matrix carries w0's groups (w1 scripts none)"
        )
        # the card's action root is the primary (the base-named group's
        # first live root); enter drills it
        assert screen._card_order == ["/scans/finetuned-mgpu-w0"]
        # the finished default root is a History row, not a card
        await pilot.press("right")
        await pilot.pause()
        table = screen.query_one("#mon-history", DataTable)
        assert [str(key.value) for key in table.rows] == ["/scans/finetuned"]


async def test_enter_drills_run_cells_then_cell_detail():
    """Enter on the focused card opens the per-run cells snapshot
    (RunCellsModal) whose rows render the folded state + progress
    grammar; enter again opens the existing CellDetailModal path.
    261019-f0x re-pin: the modal's cursor opens PINNED to the focused
    group's row (the sorted-first model, plant-dnabert here), so the
    second enter drills THAT group — the drill family itself is
    byte-unchanged; only the opening cursor follows the matrix focus."""
    from tui.screens.monitor import CellDetailModal, RunCellsModal
    from tui.strings import MON_RUN_CELLS_TITLE

    record = {"status": "completed", "metrics": {"accuracy": 0.9123}}
    focused_record = {"status": "skipped", "reason": "resume marker"}
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=3, total=36, mtime=1.0),),
            watermarks={})],
        cells={"/scans/finetuned": (
            _row("plant-dnamamba-6mer", "GUE__emp_H3",
                 {42: CELL_RUNNING, 43: CELL_QUEUED, 44: CELL_QUEUED}),
            _row("plant-dnabert-6mer", "GUE__emp_H3",
                 {42: CELL_COMPLETED, 43: CELL_SKIPPED, 44: CELL_COMPLETED}),
        )},
        stats={"/scans/finetuned": _stats(done=3, total=36)},
        progress={
            ("plant-dnamamba-6mer", "GUE__emp_H3"): CellProgress(
                step=300, max_steps=1000, percent=30)},
        records={
            ("/scans/finetuned", "plant-dnamamba-6mer", "GUE__emp_H3",
             42): record,
            ("/scans/finetuned", "plant-dnamamba-6mer", "GUE__emp_H3",
             43): None,
            ("/scans/finetuned", "plant-dnamamba-6mer", "GUE__emp_H3",
             44): None,
            # the FOCUSED group's record (the pinned cursor's row)
            ("/scans/finetuned", "plant-dnabert-6mer", "GUE__emp_H3",
             42): focused_record,
        },
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("enter")   # the focused card
        await _settle(pilot, app)
        assert isinstance(app.screen, RunCellsModal)
        table = app.screen.query_one("#mon-runcells-table", DataTable)
        assert table.row_count == 2
        running = "plant-dnamamba-6mer__GUE__emp_H3"
        completed = "plant-dnabert-6mer__GUE__emp_H3"
        assert _table_text(table, running, "state") == (
            f"{MON_STATE_RUNNING} 0/3")
        assert _table_text(table, running, "progress") == (
            "300/1000 30% ███······· —")
        assert _table_text(table, completed, "state") == (
            f"{MON_STATE_DONE} 3/3")
        assert MON_RUN_CELLS_TITLE.format(root="finetuned") in str(
            app.screen.query_one("#mon-runcells-box").border_title)
        # the pinned cursor: the sorted-first model's row (the focused
        # group), not the drill's live-on-top row 0
        assert str(table.coordinate_to_cell_key(
            table.cursor_coordinate)[0].value) == completed

        await pilot.press("enter")   # the PINNED row drills the detail
        await _settle(pilot, app)
        assert isinstance(app.screen, CellDetailModal)
        assert "plant-dnabert-6mer" in str(
            app.screen.query_one("#mon-celldetail-box").border_title)
        joined = "\n".join(line.text for line in app.screen.query_one(
            "#mon-celldetail-log", RichLog).lines)
        for field_name, value in focused_record.items():
            assert f"{field_name}: {value}" in joined, (
                f"the record field {field_name} renders verbatim")


async def test_enter_on_history_row_drills_that_run():
    """Enter on a focused History row drills THAT run's cells (the
    read-once snapshot names the run)."""
    from tui.screens.monitor import RunCellsModal
    from tui.strings import MON_RUN_CELLS_TITLE

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(
            _summary("old-run", SWEEP_FINISHED, done=1, total=1,
                     mtime=100.0),
        ), watermarks={})],
        cells={"/scans/old-run": (
            _row("model-z", "task-9", {42: CELL_COMPLETED}),)},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        await pilot.press("right")
        await pilot.pause()
        assert screen.focused.id == "mon-history"
        await pilot.press("enter")
        await _settle(pilot, app)
        assert isinstance(app.screen, RunCellsModal)
        assert MON_RUN_CELLS_TITLE.format(root="old-run") in str(
            app.screen.query_one("#mon-runcells-box").border_title)
        table = app.screen.query_one("#mon-runcells-table", DataTable)
        assert _table_text(table, "model-z__task-9", "state") == (
            f"{MON_STATE_DONE} 1/1")


async def test_scoped_keys_refuse_honestly_without_selection():
    """The scoped keys route by the FOCUSED tab: k on a History row
    (never in live_sweeps) refuses with MON_KILL_UNAVAILABLE before
    any confirm; t on a History root (no tee) renders the designed
    unavailable log state; f/t/k on the EMPTY Running tab are silent
    (no selection)."""
    from tui.screens.monitor import LogTailModal
    from tui.strings import MON_KILL_UNAVAILABLE, MON_LOG_UNAVAILABLE

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(
            _summary("old-run", SWEEP_FINISHED, done=1, total=1,
                     mtime=100.0),), watermarks={})],
        failures={"/scans/old-run": ()},
    )
    launcher = FakeMonitorLauncher(live=())
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        await pilot.press("right")
        await pilot.pause()
        # k on the History row: the registry gate refuses pre-confirm
        await pilot.press("k")
        await _settle(pilot, app)
        assert MON_KILL_UNAVAILABLE.format(
            root="/scans/old-run") in _toast_messages(app)
        assert launcher.kill_calls == []
        # t on the History row: no tee — the designed unavailable state
        await pilot.press("t")
        await _settle(pilot, app)
        assert isinstance(app.screen, LogTailModal)
        joined = "\n".join(line.text for line in app.screen.query_one(
            "#mon-log-tail", RichLog).lines)
        assert MON_LOG_UNAVAILABLE in joined
        assert monitor.tail_calls == []
        await pilot.press("escape")
        await pilot.pause()

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(), watermarks={})])
    launcher = FakeMonitorLauncher()
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert not screen._card_order, "the empty Running tab holds"
        for key in ("k", "t", "f"):
            await pilot.press(key)
            await _settle(pilot, app)
        assert isinstance(app.screen, MonitorScreen), (
            "no selection: the scoped keys open nothing"
        )
        assert _toast_messages(app) == [], "and stay fully silent"
        assert launcher.kill_calls == []
        assert monitor.failures_calls == []


async def test_running_empty_state_is_actionable_copy():
    """No live runs: the Running tab renders the actionable empty copy
    (the enter-route affordance named); the History tab renders its own
    designed empty row; the cadence stays armed."""
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(
            _summary("old-run", SWEEP_FINISHED, done=1, total=1,
                     mtime=100.0),), watermarks={})])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        empty = screen.query_one("#mon-running-empty", Static)
        assert empty.display is True, "the empty region renders"
        assert _plain(empty.content) == MON_RUNNING_EMPTY
        before = len(monitor.full_calls)
        screen._tick_full()
        await _settle(pilot, app)
        assert len(monitor.full_calls) > before, "the cadence stays armed"

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(), watermarks={})])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        await pilot.press("right")
        await pilot.pause()
        table = screen.query_one("#mon-history", DataTable)
        assert _table_text(table, "__empty__", "state") == MON_HISTORY_EMPTY
        empty = screen.query_one("#mon-history-empty", Static)
        assert empty.display is True, (
            "a history with zero rows renders its empty region")


async def test_cadence_dispatches_workers_and_stops_on_unmount():
    """D-09 cadence: the mount kick + the interval callbacks dispatch
    the exclusive workers (fake counters prove the chain — never real
    sleeps); the frontier worker iterates EVERY live root in one pass;
    switching away leaves no zombie workers."""
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(
            _summary("root-a", SWEEP_RUNNING, done=1, total=9, mtime=1.0),
            _summary("root-b", SWEEP_RUNNING, done=7, total=9, mtime=2.0),
        ), watermarks={})],
        cells={"/scans/root-a": (
            _row("model-a", "task-1", {42: CELL_RUNNING}),)},
        stats={"/scans/root-a": _stats(done=1, total=9)},
        frontiers={"/scans/root-a": FrontierSnapshot(
            root=Path("/scans/root-a"), state=SWEEP_RUNNING,
            newest_mtime=None, newest_cell=None, cell_states={})},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert len(monitor.full_calls) >= 1, (
            "the mount kick runs the full scan immediately (never a "
            "60s blank screen)"
        )
        assert screen._frontier_timer is not None, (
            "the 2s frontier interval is armed"
        )
        assert screen._full_timer is not None, (
            "the 60s full interval is armed"
        )

        before_frontier = len(monitor.frontier_calls)
        screen._tick_frontier()   # the interval's callback, invoked directly
        await _settle(pilot, app)
        assert len(monitor.frontier_calls) > before_frontier, (
            "the frontier tick dispatched the scan worker (the fake "
            "counter is the cadence proof)"
        )
        assert set(monitor.frontier_calls) >= {"/scans/root-a",
                                               "/scans/root-b"}, (
            "ONE frontier pass iterates EVERY live root"
        )

        before_full = len(monitor.full_calls)
        screen._tick_full()
        await _settle(pilot, app)
        assert len(monitor.full_calls) > before_full

        # switching away: the timers stop (Textual cancels on unmount)
        # and no monitor worker survives
        await app.switch_screen(app.get_default_screen())
        await _settle(pilot, app)
        mon_workers = [
            worker for worker in app.workers
            if str(getattr(worker, "group", "") or "").startswith("mon-")
        ]
        assert not mon_workers, (
            f"no zombie monitor workers after unmount "
            f"({[w.group for w in mon_workers]})"
        )


def test_monitor_module_carries_zero_chinese_literals():
    """I18N-01 single home: no operator-facing copy in the module."""
    source = _MONITOR_MODULE_FILE.read_text(encoding="utf-8")
    offenders = re.findall(r"[一-鿿]", source)
    assert not offenders, (
        "Chinese literals must live in tui/strings.py only "
        f"({len(offenders)} found in {_MONITOR_MODULE_FILE.name})"
    )

# =====================================================================
# Task 2 — interactions ([a], [f]+re-run family, [t], [r], cursors)
# =====================================================================

async def test_attach_path_invalid_keeps_modal_never_adds():
    """[a] with an invalid path: the toast copy renders INSIDE the
    modal (never silent), the root is never added."""
    from tui.screens.selection import PathInputModal
    from tui.strings import MON_ATTACH_INVALID_TOAST

    monitor = FakeMonitorService(
        scans=[_three_state_scan()], manual_roundtrip=[False])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("a")
        await pilot.pause()
        assert isinstance(app.screen, PathInputModal)
        await pilot.press(*"/no/such/root")
        await pilot.press("enter")
        await pilot.pause()
        # the modal stays open with the invalid copy as its problem row
        assert isinstance(app.screen, PathInputModal)
        problems = app.screen.query_one("#path-problems", Static)
        assert MON_ATTACH_INVALID_TOAST.format(
            path="/no/such/root") in _plain(problems.content)
        # never persisted (the fake records the ATTEMPT; the predicate
        # refused it — add_manual_root returned False)
        assert monitor.added_roots == ["/no/such/root"]
        await pilot.press("escape")
        await pilot.pause()
        # the tabs behind never grew a row
        screen = app.screen
        cards = screen.query_one("#mon-cards", ListView)
        assert len(cards) == 1, "no new card appeared"


async def test_attach_path_valid_rescans_root_joins_its_tab():
    """[a] with a valid root: add_manual_root called, the toast fires,
    the immediate rescan lands, and the root joins ITS tab (a finished
    root lands on History — the tabs list every discovered run; no
    attach state remains)."""
    from tui.screens.selection import PathInputModal

    manual_scan = ScanResult(sweeps=(
        _summary("manual-root", SWEEP_FINISHED, done=1, total=1,
                 mtime=100.0),
    ), watermarks={})
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(), watermarks={}), manual_scan],
        manual_roundtrip=[True],
        valid_roots={"/scans/manual-root"},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("a")
        await pilot.pause()
        assert isinstance(app.screen, PathInputModal)
        await pilot.press(*"/scans/manual-root")
        await pilot.press("enter")
        await _settle(pilot, app)
        assert not isinstance(app.screen, PathInputModal), (
            "a valid path dismisses the modal"
        )
        assert monitor.added_roots == ["/scans/manual-root"]
        assert MON_ATTACHED_TOAST.format(
            root="manual-root") in _toast_messages(app)
        screen = app.screen
        await pilot.press("right")
        await pilot.pause()
        table = screen.query_one("#mon-history", DataTable)
        assert "/scans/manual-root" in {
            str(key.value) for key in table.rows}, (
            "the manually added finished root joined the History tab")


async def test_attach_tilde_spelled_root_validates_and_joins_real_scanner(
        monkeypatch, tmp_path):
    """CR-01 (gap #1) over the two-tab surface: a ``~`` -spelled root
    submitted through the [a] modal VALIDATES (add_manual_root expands
    + resolves internally) and the RESOLVED root joins the scan — over
    the REAL MonitorBackend/scanner (temp HOME + temp state dir; the
    coverage hole: every earlier Pilot attach test used absolute fake
    paths)."""
    import json

    from tui.screens.monitor import MonitorBackend
    from tui.screens.selection import PathInputModal
    from tui.services import settings, sweep_monitor

    tmp_home = tmp_path / "home"
    tmp_home.mkdir()
    monkeypatch.setenv("HOME", str(tmp_home))
    monkeypatch.setenv(
        settings.STATE_DIR_ENV, str(tmp_path / "state"))
    # hermetic discovery: the scan reads EXACTLY the tmp HOME's manual
    # root — the repo defaults (pipeline/finetuned, the live smoke's
    # read-only territory) are never walked by this lane
    monkeypatch.setattr(sweep_monitor, "DEFAULT_OUTPUT_ROOTS", ())

    model, task = "model-a", "task-1"
    seed_dir = tmp_home / "sweeps" / "run1" / model / task / "seed_42"
    seed_dir.mkdir(parents=True)
    (seed_dir / "run_record.json").write_text(json.dumps({
        "status": "completed", "model": model, "task": task, "seed": 42,
    }), encoding="utf-8")

    app = _app(monitor=MonitorBackend())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        await pilot.press("a")
        await pilot.pause()
        assert isinstance(app.screen, PathInputModal)
        await pilot.press(*"~/sweeps/run1")
        await pilot.press("enter")
        await _settle(pilot, app)
        assert not isinstance(app.screen, PathInputModal), (
            "the ~ -spelled root VALIDATED (add_manual_root expands + "
            "resolves internally) — the modal dismisses"
        )
        resolved = (tmp_home / "sweeps" / "run1").resolve()
        # the fresh record's mtime sits inside the churn grace, so the
        # scanner classifies the discovered root RUNNING — it renders as
        # the Running tab's card under its RESOLVED key (the service's
        # own classification; the screen only renders it)
        assert screen._card_order == [str(resolved)], (
            "the scanner discovered the root under the RESOLVED path "
            "(the literal '~' spelling never lands)"
        )
        assert "run1" in _card_texts(screen, "mon-card-strip")[0]
        # enter drills it and the record's row renders over the REAL path
        await pilot.press("enter")
        await _settle(pilot, app)
        from tui.screens.monitor import RunCellsModal

        assert isinstance(app.screen, RunCellsModal)
        drill = app.screen.query_one("#mon-runcells-table", DataTable)
        assert _table_text(drill, f"{model}__{task}", "state") == (
            f"{MON_STATE_DONE} 1/1"), (
            "the completed record's row renders (the drill reads a REAL "
            "path — never an empty snapshot)"
        )


def test_restart_reattach_probe_evidence_through_real_launcher_wiring(
        monkeypatch, tmp_path):
    """The 2026-10-19 reattach gap, pinned at the REAL wiring shape:
    the app injects MonitorBackend over run_config's LauncherBackend
    facade — NOT a bare SweepLauncher. After a console restart the
    launcher REGISTRY is empty and the /proc probe is the ONLY live
    evidence; the facade must forward ``live_sweep_matrices`` or the
    tolerant getattr in MonitorBackend._live_evidence degrades to
    registry-only and a still-running detached sweep falls back to its
    STALE manifest and classifies finished (the maintainer repro:
    finetuned-smoke alive in /proc, the Running tab empty)."""
    import json
    import sys

    from tui.screens.monitor import MonitorBackend
    from tui.screens.run_config import LauncherBackend
    from tui.services import settings, sweep_launcher, sweep_monitor

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state_dir))
    monkeypatch.setattr(sweep_monitor, "DEFAULT_OUTPUT_ROOTS", ())

    root = tmp_path / "sweeps" / "detached"
    root.mkdir(parents=True)
    # the trap: a PREVIOUS run's manifest still sits at the root —
    # without live evidence the scan reads it and says "finished"
    (root / "sweep_manifest.json").write_text(json.dumps({
        "cells": [{"model": "plant-dnabert-6mer",
                   "task": "GUE__emp_H3", "seed": 42,
                   "status": "completed"}]}), encoding="utf-8")
    (state_dir / "monitor_roots.json").write_text(json.dumps({
        "schema_version": 1, "roots": [str(root)]}), encoding="utf-8")

    argv = [
        sys.executable,
        str(Path(__file__).resolve().parents[1] / "pipeline"
            / "run_sweep.py"),
        "--models", "plant-dnabert-6mer",
        "--tasks", "GUE__emp_H3",
        "--seeds", "42",
        "--output-root", str(root),
    ]
    monkeypatch.setattr(sweep_launcher, "probe_cli_sweeps",
                        lambda: {str(root.resolve()): tuple(argv)})

    backend = MonitorBackend(launcher=LauncherBackend())
    result = backend.full_scan()
    states = {summary.root.name: summary.state
              for summary in result.sweeps}
    assert states == {"detached": sweep_monitor.SWEEP_RUNNING}, (
        "the probed live sweep must classify RUNNING through the app's "
        "real facade wiring — registry-empty restart is the exact case "
        "the /proc probe exists for"
    )


def test_backend_entries_progress_threads_live_started_guard(
        monkeypatch, tmp_path):
    """261020-9vh — the maintainer's live shape through the REAL
    wiring: a reused root whose RUNNING pair (probe-derived live_pairs
    membership + the checkpoint child's activity signal) holds a
    checkpoint ~13h stale, with BOTH probes monkeypatched to the tmp
    root and a live start of now-60s -> MonitorBackend over the
    LauncherBackend facade returns NO entry for the pair (the numbers
    are unknown-until-first-save, never the previous run's 40%). The
    same fixture with the starts probe reading {} (no start evidence)
    returns today's 40% entry; a launcher WITHOUT the method (every
    pre-existing fake) rides the tolerant getattr leg to the same
    today-behavior."""
    import json
    import os
    import sys
    import types

    from tui.screens.monitor import MonitorBackend
    from tui.screens.run_config import LauncherBackend
    from tui.services import settings, sweep_launcher

    state_dir = tmp_path / "state"
    state_dir.mkdir()
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state_dir))

    root = tmp_path / "sweeps" / "reused"
    seed = root / "plant-dnabert-6mer" / "GUE__emp_H3" / "seed_42"
    checkpoint = seed / "checkpoint-19968"
    checkpoint.mkdir(parents=True)
    (checkpoint / "trainer_state.json").write_text(json.dumps(
        {"global_step": 19968, "max_steps": 49911}), encoding="utf-8")
    stale = time.time() - 13 * 3600.0
    for path in sorted(seed.rglob("*")):
        os.utime(path, (stale, stale))
    os.utime(seed, (stale, stale))

    pair = ("plant-dnabert-6mer", "GUE__emp_H3")
    argv = (
        sys.executable,
        str(Path(__file__).resolve().parents[1] / "pipeline"
            / "run_sweep.py"),
        "--models", "plant-dnabert-6mer",
        "--tasks", "GUE__emp_H3",
        "--seeds", "42",
        "--output-root", str(root),
    )
    root_key = str(root.resolve())
    monkeypatch.setattr(sweep_launcher, "probe_cli_sweeps",
                        lambda: {root_key: argv})

    backend = MonitorBackend(launcher=LauncherBackend())

    # the live-repro shape: a start of now-60s makes the ~13h-stale
    # checkpoint predate it -> NO entry, never the previous run's 40%
    monkeypatch.setattr(sweep_launcher, "probe_cli_sweep_starts",
                        lambda: {root_key: time.time() - 60.0})
    guarded = backend.entries_progress(root)
    assert pair not in guarded, (
        "the stale checkpoint's numbers never render while the live "
        "run has not saved its own first checkpoint"
    )

    # no start evidence: today's 40% entry returns (the fallback)
    monkeypatch.setattr(sweep_launcher, "probe_cli_sweep_starts", dict)
    fallback = backend.entries_progress(root)
    assert fallback[pair].percent == 40, (
        "without live-start evidence the parse keeps today's behavior"
    )

    # the tolerant getattr leg: a launcher without live_sweep_started
    # (every pre-existing fake — here the pre-9vh facade shape) reads
    # None and keeps the same today-behavior
    bare = MonitorBackend(launcher=types.SimpleNamespace(
        live_sweeps=lambda: (),
        live_sweep_matrices=lambda: {root_key: frozenset({pair})},
    ))
    today = bare.entries_progress(root)
    assert today[pair].percent == 40, (
        "a launcher without the method rides the fallback — never a "
        "fabricated staleness"
    )


async def test_failures_modal_rows_drill_and_empty_state():
    """[f] over the FOCUSED running card: one row per failure, enter
    drills the verbatim error, and the empty list renders the designed
    zero copy."""
    from tui.screens.monitor import FailureDetailModal, FailuresModal
    from tui.strings import MON_FAILURE_ROW as ROW_COPY

    failures = (
        FailureRow(model="model-a", task="task-1", seed=42,
                   error="CUDA out of memory: tried to allocate 2.00 GiB",
                   output_dir="/scans/finetuned/model-a/task-1/seed_42"),
        FailureRow(model="model-a", task="task-2", seed=43,
                   error="KeyError: 'dataset'",
                   output_dir="/x"),
    )
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=3, total=5, mtime=1.0),),
            watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_FAILED}),)},
        stats={"/scans/finetuned": _stats(done=3, total=5)},
        failures={"/scans/finetuned": failures},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("f")
        await _settle(pilot, app)
        assert isinstance(app.screen, FailuresModal)
        table = app.screen.query_one("#mon-failures-table", DataTable)
        assert table.row_count == 2
        assert _table_text(table, "failure-0", "model") == ROW_COPY.format(
            model="model-a", task="task-1", seed=42)
        # enter drills the VERBATIM error
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, FailureDetailModal)
        joined = "\n".join(line.text for line in app.screen.query_one(
            "#mon-faildetail-log", RichLog).lines)
        assert "CUDA out of memory" in joined
        assert "2.00 GiB" in joined
        await pilot.press("escape")
        await pilot.pause()

    # the empty list renders the designed zero copy (a History root: f
    # scopes to the focused tab's selection there too)
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_FINISHED, done=5, total=5, mtime=1.0),),
            watermarks={})],
        failures={"/scans/finetuned": ()},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("right")
        await pilot.pause()
        await pilot.press("f")
        await _settle(pilot, app)
        assert isinstance(app.screen, FailuresModal)
        table = app.screen.query_one("#mon-failures-table", DataTable)
        assert _table_text(table, "__empty__", "model") == (
            MON_FAILURES_EMPTY)


def _rerun_fixture_monitor(failures, **overrides):
    """The canonical [f]->[r] fixture: one running root + failures."""
    fixture: dict = {
        "scans": [ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=3, total=5, mtime=1.0),),
            watermarks={})],
        "cells": {"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_FAILED}),)},
        "stats": {"/scans/finetuned": _stats(done=3, total=5)},
        "failures": {"/scans/finetuned": failures},
    }
    fixture.update(overrides)
    return FakeMonitorService(**fixture)


async def test_rerun_confirm_routes_launch_from_failures():
    """[f] -> r -> confirm: launch_from_failures called with the root's
    failures file + the FAILURE-referenced seed set; the toast fires
    (T-11-07-03: the same pipeline).

    WR-02 (sanctioned pin change, 11-08): the seeds derive from the
    failure rows themselves — with cells {42: FAILED, 43: QUEUED} but
    the single failure row at seed 42, the launch receives (42,)."""
    from tui.screens.monitor import FailuresModal
    from tui.screens.selection import ConfirmModal
    from tui.strings import MON_RERUN_CONFIRM, MON_RERUN_TOAST

    failures = (FailureRow(model="model-a", task="task-1", seed=42,
                           error="boom", output_dir="/x"),)
    monitor = _rerun_fixture_monitor(failures, cells={
        "/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_FAILED, 43: CELL_QUEUED}),)})
    launcher = FakeMonitorLauncher()
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("f")
        await _settle(pilot, app)
        assert isinstance(app.screen, FailuresModal)
        await pilot.press("r")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmModal), (
            "the re-run always sits behind its own confirm"
        )
        assert MON_RERUN_CONFIRM.format(
            pairs=1, seeds="42", n=1) in str(
            app.screen.query_one(Static).content)
        # EHC-2: enter REFUSES the re-run confirm; y launches it
        await pilot.press("enter")
        await _settle(pilot, app)
        assert launcher.env_calls == 0, (
            "enter must never pass a launch confirmation (EHC-2)")
        assert launcher.rerun_calls == []
        assert isinstance(app.screen, ConfirmModal), (
            "the inert enter leaves the re-run confirm up"
        )
        await pilot.press("y")   # confirm
        await _settle(pilot, app)
        assert launcher.env_calls == 1, "the env preflight re-entered"
        assert len(launcher.rerun_calls) == 1
        failures_path, seeds, root, _peft, _variant, phrase = (
            launcher.rerun_calls[0])
        assert failures_path == "/scans/finetuned/sweep_failures.json"
        assert seeds == (42,), (
            "the failure-referenced seed set fans out — the queued alias "
            "seed is never silently re-attempted"
        )
        assert root == "/scans/finetuned"
        assert phrase is None, "an ordinary partial re-run carries no phrase"
        assert MON_RERUN_TOAST.format(
            cells="—", root="finetuned") in _toast_messages(app)


async def test_rerun_single_gpu_busy_refuses_before_the_confirm():
    """EHC-3 (261015-ehc ruling 3): with the single-GPU guard seam
    reporting live roots, the [f]->[r] request REFUSES before the
    re-run confirm modal is ever pushed — the bilingual toast names
    the running root, y is never reachable, nothing launches."""
    from tui.screens.monitor import FailuresModal
    from tui.screens.selection import ConfirmModal
    from tui.strings import LNC_SINGLE_GPU_BLOCKED

    failures = (FailureRow(model="model-a", task="task-1", seed=42,
                           error="boom", output_dir="/x"),)
    monitor = _rerun_fixture_monitor(failures)
    launcher = FakeMonitorLauncher(
        single_gpu_blocked=("/scans/finetuned-live",))
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("f")
        await _settle(pilot, app)
        assert isinstance(app.screen, FailuresModal)
        await pilot.press("r")
        await _settle(pilot, app)
        assert not isinstance(app.screen, ConfirmModal), (
            "the single-GPU pre-check refuses BEFORE the confirm modal"
        )
        assert any(LNC_SINGLE_GPU_BLOCKED.format(
            roots="/scans/finetuned-live") in message
            for message in _toast_messages(app)), _toast_messages(app)
        assert launcher.env_calls == 0, "the preflight never runs"
        assert launcher.rerun_calls == [], "nothing ever launches"


async def test_rerun_seeds_derive_from_failure_rows_not_a_default():
    """WR-02 (gap #3): with the run's cell rows EMPTY (no cells landed
    — the [f] window before the rows arrive), the re-run's seed fan-out
    derives from the FAILURE rows themselves (seed 43 here) — never the
    silent ``[42]`` default that would re-run a different experiment
    than the one confirmed."""
    from tui.screens.monitor import FailuresModal
    from tui.screens.selection import ConfirmModal
    from tui.strings import MON_RERUN_CONFIRM

    failures = (FailureRow(model="model-x", task="task-x", seed=43,
                           error="boom", output_dir="/x"),)
    monitor = _rerun_fixture_monitor(failures, cells={})
    launcher = FakeMonitorLauncher()
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert screen._cell_rows.get("/scans/finetuned", {}) == {}, (
            "the empty-cells staging holds"
        )
        await pilot.press("f")
        await _settle(pilot, app)
        assert isinstance(app.screen, FailuresModal)
        await pilot.press("r")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmModal)
        assert MON_RERUN_CONFIRM.format(
            pairs=1, seeds="43", n=1) in str(
            app.screen.query_one(Static).content)
        await pilot.press("y")   # confirm (EHC-2: y launches)
        await _settle(pilot, app)
        assert len(launcher.rerun_calls) == 1
        _path, seeds, _root, _peft, _variant, _phrase = (
            launcher.rerun_calls[0])
        assert seeds == (43,), (
            "the failure rows are the derivation source — the silent "
            "[42] default is gone"
        )


async def test_rerun_underivable_seeds_refuses_loudly_never_launches():
    """WR-02 (refuse loudly): when NOTHING is derivable — the worker's
    own failures_view re-read yields no seeds AND the run's cell rows
    are empty — the pipeline posts RerunFailed (the error toast carries
    MON_RERUN_NO_SEEDS under the ✗ prefix) and launch_from_failures is
    NEVER called: a confirmed GPU spend never becomes a different,
    unconfirmed experiment."""
    from tui.screens.monitor import FailuresModal
    from tui.strings import LNC_LAUNCH_FAILED_TOAST, MON_RERUN_NO_SEEDS

    failures = (FailureRow(model="model-x", task="task-x", seed=42,
                           error="boom", output_dir="/x"),)
    monitor = _rerun_fixture_monitor(failures, cells={})
    # the confirm-side read sees the seed-42 row; the WORKER-side
    # re-read (the second call) yields NOTHING (the staged empty
    # re-read — the derivation finds no seeds)
    monitor._failures["/scans/finetuned"] = [failures, ()]
    launcher = FakeMonitorLauncher()
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("f")
        await _settle(pilot, app)
        assert isinstance(app.screen, FailuresModal)
        await pilot.press("r")
        await pilot.press("y")   # confirm the re-run (EHC-2)
        await _settle(pilot, app)
        assert LNC_LAUNCH_FAILED_TOAST.format(
            error=MON_RERUN_NO_SEEDS) in _toast_messages(app), (
            "the underivable seed set refuses LOUDLY — never a default"
        )
        assert launcher.rerun_calls == [], (
            "the launcher is never consulted when nothing is derivable"
        )


async def test_rerun_confirm_names_pairs_times_seeds_estimate():
    """WR-03 (gap #4): the confirm names the PLANNED-CELL estimate —
    len(distinct (model, task) pairs) x len(seeds), the exact
    enumeration launch_from_failures performs — so the confirmed GPU
    spend is never understated. Two failures at two pairs and two
    seeds confirm 4 planned cells and launch the full fan-out."""
    from tui.screens.monitor import FailuresModal
    from tui.screens.selection import ConfirmModal
    from tui.strings import MON_RERUN_CONFIRM

    failures = (
        FailureRow(model="model-a", task="task-1", seed=42,
                   error="boom", output_dir="/x"),
        FailureRow(model="model-b", task="task-2", seed=43,
                   error="boom", output_dir="/y"),
    )
    monitor = _rerun_fixture_monitor(failures, cells={})
    launcher = FakeMonitorLauncher()
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("f")
        await _settle(pilot, app)
        assert isinstance(app.screen, FailuresModal)
        await pilot.press("r")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmModal)
        copy = str(app.screen.query_one(Static).content)
        assert MON_RERUN_CONFIRM.format(
            pairs=2, seeds="42, 43", n=4) in copy, (
            "the confirm names the pair count AND the seed fan-out with "
            "their product — the exact enumeration the launch performs"
        )
        await pilot.press("y")   # confirm (EHC-2: y launches)
        await _settle(pilot, app)
        assert len(launcher.rerun_calls) == 1
        _path, seeds, _root, _peft, _variant, _phrase = (
            launcher.rerun_calls[0])
        assert seeds == (42, 43), (
            "confirm and launch share ONE derivation — the confirmed "
            "fan-out is the executed fan-out"
        )


async def test_note_launch_cells_zero_clears_stale_expected_total():
    """WR-02: the re-run's note_launch(root, 0) clears a prior launch's
    stale expected total at the same root — the next stats call threads
    expected_total=None (the honest unknown), never the prior sweep's
    number; a real plan (cells > 0) still injects."""
    monitor = FakeMonitorService(scans=[ScanResult(sweeps=(
        _summary("finetuned", SWEEP_RUNNING, done=1, total=2, mtime=1.0),),
        watermarks={})])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        screen.note_launch("/scans/finetuned", 9300)
        screen._tick_frontier()
        await _settle(pilot, app)
        assert monitor.stats_calls[-1][1] == 9300, (
            "the launch plan injects the expected total"
        )

        screen.note_launch("/scans/finetuned", 0)   # the re-run note
        screen._tick_frontier()                     # the next stats read
        await _settle(pilot, app)
        assert monitor.stats_calls[-1][1] is None, (
            "the re-run's unknown plan clears the stale expectation — "
            "never 9300 for a 15-cell re-run"
        )
        assert monitor.stats_calls[-1][2] is not None, (
            "the fallback start still threads (the run scoping seam)"
        )

        screen.note_launch("/scans/finetuned", 15)
        screen._tick_frontier()
        await _settle(pilot, app)
        assert monitor.stats_calls[-1][1] == 15


async def test_rerun_carries_source_sweep_lane_never_base_default():
    """WR-01: a --peft lora sweep's [r] re-run threads the SOURCE lane
    into launch_from_failures (recovered via the service's rerun_lane)
    — never a none/none default that would re-train BASE cells of the
    failed pairs instead of the confirmed alias cells."""
    from tui.screens.monitor import FailuresModal

    failures = (FailureRow(model="model-a+lora", task="task-1", seed=42,
                           error="boom", output_dir="/x"),)
    monitor = _rerun_fixture_monitor(failures, rerun_lanes={
        "/scans/finetuned": ("lora", "none")})
    launcher = FakeMonitorLauncher()
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("f")
        await _settle(pilot, app)
        assert isinstance(app.screen, FailuresModal)
        await pilot.press("r")
        await pilot.pause()
        await pilot.press("y")   # confirm the re-run (EHC-2)
        await _settle(pilot, app)
        assert monitor.rerun_lane_calls == ["/scans/finetuned"], (
            "the lane is read through the service seam"
        )
        assert len(launcher.rerun_calls) == 1
        _path, _seeds, _root, peft, variant, _phrase = (
            launcher.rerun_calls[0])
        assert peft == "lora", "the source sweep's lane threads through"
        assert variant == "none"


async def test_rerun_env_block_renders_the_same_modal():
    """A preflight FAIL on the re-run renders the SAME env-block modal
    as slot 4 — the re-run can never bypass the gate (T-11-07-03)."""
    from tui.screens.env_check import EnvCheckScreen  # noqa: F401
    from tui.screens.monitor import FailuresModal
    from tui.screens.run_config import EnvBlockModal
    from tui.strings import ENV_QUICK_CHECK_FAIL

    failures = (FailureRow(model="model-a", task="task-1", seed=42,
                           error="boom", output_dir="/x"),)
    monitor = _rerun_fixture_monitor(failures)
    launcher = FakeMonitorLauncher(preflight=EnvPreflight(
        can_launch=False,
        reasons=("torch: import failed", "cuda: no device"),
        failed_kernels=("torch", "cuda")))
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("f")
        await _settle(pilot, app)
        assert isinstance(app.screen, FailuresModal)
        await pilot.press("r")
        await pilot.press("y")   # confirm the re-run (EHC-2)
        await _settle(pilot, app)
        assert isinstance(app.screen, EnvBlockModal), (
            "a doomed re-run never launches — the same env block"
        )
        joined = "\n".join(line.text for line in app.screen.query_one(
            "#cfg-envblock-log", RichLog).lines)
        assert "torch: import failed" in joined
        assert "cuda: no device" in joined
        assert ENV_QUICK_CHECK_FAIL.format(
            kernel_names="torch, cuda") in _plain(app.screen.query_one(
                "#cfg-envblock-header", Static).content)
        assert launcher.rerun_calls == [], (
            "the launch never happened after the env block"
        )


async def test_rerun_e2x_phrase_refusal_reprompts_then_launches():
    """CR-01: a complete failures manifest over 3 seeds IS the full
    matrix — the service's phrase-stage refusal re-prompts the E2'
    typed phrase on the monitor (the D-07 escalation, same modal as
    slot 4), and only the typed match re-launches WITH the phrase."""
    from tui.screens.monitor import FailuresModal
    from tui.screens.run_config import E2PhraseModal
    from tui.screens.selection import ConfirmModal
    from tui.strings import MON_RERUN_TOAST

    failures = tuple(
        FailureRow(model=f"model-{index}", task="task-1", seed=seed,
                   error="boom", output_dir="/x")
        for index in range(3) for seed in (42, 43, 44))
    monitor = _rerun_fixture_monitor(failures, cells={})
    launcher = FakeMonitorLauncher(rerun_outcomes=[
        GateRefusal(stage="phrase", expected="finetuned"),
    ])
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("f")
        await _settle(pilot, app)
        assert isinstance(app.screen, FailuresModal)
        await pilot.press("r")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmModal)
        await pilot.press("y")   # confirm the re-run (EHC-2)
        await _settle(pilot, app)
        assert isinstance(app.screen, E2PhraseModal), (
            "the phrase-stage refusal escalates to the typed-phrase "
            "modal — the E2' boundary holds on the [f]->[r] path"
        )
        assert launcher.rerun_calls[0][5] is None, (
            "the first attempt carried no phrase (the gate refused)"
        )
        await pilot.press("f", "i", "n")   # a partial phrase stays mismatched
        await pilot.pause()
        assert isinstance(app.screen, E2PhraseModal)
        for key in "etuned":
            await pilot.press(key)
        await pilot.pause()
        await pilot.press("enter")   # the exact match ADVANCES (EHC-2)
        await pilot.pause()
        await pilot.press("y")       # y carries the typed phrase
        await _settle(pilot, app)
        assert len(launcher.rerun_calls) == 2
        assert launcher.rerun_calls[1][5] == "finetuned", (
            "the re-prompt's typed phrase threads the re-launch"
        )
        assert MON_RERUN_TOAST.format(
            cells="—", root="finetuned") in _toast_messages(app)


async def test_rerun_problems_refusal_surfaces_error_toast():
    """CR-01: a problems-stage refusal (official-keys diagnostic /
    unevaluatable manifest) is never a silent no-op — the launch-failed
    toast names the problems and NOTHING launches."""
    failures = (FailureRow(model="model-a", task="task-1", seed=42,
                           error="boom", output_dir="/x"),)
    monitor = _rerun_fixture_monitor(failures)
    launcher = FakeMonitorLauncher(rerun_outcomes=[GateRefusal(
        stage="problems",
        problems=(("official_keys",
                   "unreadable or shape-invalid: pipeline/models_info.json"),),
    )])
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("f")
        await _settle(pilot, app)
        await pilot.press("r")
        await pilot.pause()
        await pilot.press("y")   # confirm the re-run (EHC-2)
        await _settle(pilot, app)
        toasts = _toast_messages(app)
        assert any(
            "official_keys" in message
            and "unreadable or shape-invalid" in message
            for message in toasts), toasts
        assert len(launcher.rerun_calls) == 1, "no second attempt"


async def test_rerun_worker_exception_surfaces_error_toast():
    """WR-03 (the monitor sibling): a re-run worker raising after the
    operator confirmed is surfaced as the error toast — never a silent
    no-op launch."""
    from tui.strings import LNC_LAUNCH_FAILED_TOAST

    failures = (FailureRow(model="model-a", task="task-1", seed=42,
                           error="boom", output_dir="/x"),)
    monitor = _rerun_fixture_monitor(failures)
    launcher = FakeMonitorLauncher(
        env_raises=OSError("quick-check kernel spawn failed"))
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("f")
        await _settle(pilot, app)
        await pilot.press("r")
        await pilot.pause()
        await pilot.press("y")   # confirm the re-run (EHC-2)
        await _settle(pilot, app)
        assert any(LNC_LAUNCH_FAILED_TOAST.format(
            error="quick-check kernel spawn failed") in toast
            for toast in _toast_messages(app)), _toast_messages(app)
        assert launcher.rerun_calls == [], "nothing launched"


async def test_log_tail_renders_lines_and_tee_line():
    """[t] over the focused running card's tee: the bounded tail renders
    + the dim tee line names the file (D-10)."""
    from tui.screens.monitor import LogTailModal
    from tui.strings import MON_LOG_TEE_LINE

    tee_path = "/state/logs/sweep_20261013_finetuned.log"
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=1, total=2, mtime=1.0),),
            watermarks={})],
        stats={"/scans/finetuned": _stats(done=1, total=2)},
        tails={tee_path: ("[01:00:05] epoch 1", "[01:00:40] done")},
    )
    launcher = FakeMonitorLauncher(tee={"/scans/finetuned": tee_path})
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("t")
        await _settle(pilot, app)
        assert isinstance(app.screen, LogTailModal)
        joined = "\n".join(line.text for line in app.screen.query_one(
            "#mon-log-tail", RichLog).lines)
        assert "[01:00:05] epoch 1" in joined
        assert "[01:00:40] done" in joined
        assert MON_LOG_TEE_LINE.format(path=tee_path) in _label_text(
            app.screen, "#mon-log-tee-line")
        # esc returns; the tail stops with the modal
        reads_before = len(monitor.tail_calls)
        await pilot.press("escape")
        await _settle(pilot, app)
        assert isinstance(app.screen, MonitorScreen)
        assert len(monitor.tail_calls) == reads_before, (
            "no tail read fires after esc (the timer stopped)"
        )


async def test_log_tail_no_tee_is_designed_unavailable():
    """[t] with no tee (a CLI-launched sweep): the unavailable state
    renders and NO refresh is ever scheduled."""
    from tui.screens.monitor import LogTailModal
    from tui.strings import MON_LOG_UNAVAILABLE

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=1, total=2, mtime=1.0),),
            watermarks={})],
        stats={"/scans/finetuned": _stats(done=1, total=2)},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("t")
        await pilot.pause()
        assert isinstance(app.screen, LogTailModal)
        joined = "\n".join(line.text for line in app.screen.query_one(
            "#mon-log-tail", RichLog).lines)
        assert MON_LOG_UNAVAILABLE in joined, (
            "the CLI-launched state renders the designed copy — never a "
            "fabricated empty log"
        )
        assert monitor.tail_calls == [], (
            "no refresh was ever scheduled without a tee"
        )
        await pilot.press("escape")
        await pilot.pause()


async def test_rescan_fires_immediate_full_scan_with_toast():
    """[r]: an immediate full rescan outside the 60s cadence; the
    toast carries the discovered count."""
    from tui.strings import MON_RESCAN_TOAST

    monitor = FakeMonitorService(
        scans=[_three_state_scan(), _three_state_scan()])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        calls_after_mount = len(monitor.full_calls)
        await pilot.press("r")
        await _settle(pilot, app)
        assert len(monitor.full_calls) > calls_after_mount, (
            "[r] dispatched the immediate full rescan"
        )
        assert MON_RESCAN_TOAST.format(n=3) in _toast_messages(app)


async def test_table_updates_preserve_cursor_across_ticks():
    """WR-05 (phase-11 review): the cadence rebuilds are diff-preserving
    — a frontier tick never resets the card list's index and a full
    scan never resets the History table's cursor row identity, so an
    [enter] pressed after a tick acts on the row the operator SEES."""
    monitor = FakeMonitorService(
        scans=[_three_state_scan()],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_RUNNING}),)},
        stats={"/scans/finetuned": _stats(done=1, total=9)},
        frontiers={"/scans/finetuned": FrontierSnapshot(
            root=Path("/scans/finetuned"), state=SWEEP_RUNNING,
            newest_mtime=None, newest_cell=("model-a", "task-1", 42),
            cell_states={
                ("model-a", "task-1", 42): CELL_RUNNING,
            })},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen

        discovered = screen.query_one("#mon-history", DataTable)
        await pilot.press("right")
        await pilot.pause()
        discovered.action_cursor_down()    # row 1: the artifacts root
        await pilot.pause()
        root_before = str(discovered.coordinate_to_cell_key(
            discovered.cursor_coordinate)[0].value)
        assert root_before == "/scans/seed-9527-artifacts"
        screen._tick_full()                # the 60s rebuild
        await _settle(pilot, app)
        assert str(discovered.coordinate_to_cell_key(
            discovered.cursor_coordinate)[0].value) == root_before, (
            "a full-scan rebuild must not snap the History cursor"
        )

        await pilot.press("left")
        await pilot.pause()
        cards = screen.query_one("#mon-cards", ListView)
        cards.action_cursor_down() if len(cards) > 1 else None
        index_before = cards.index
        screen._tick_frontier()            # the 2s card rebuild
        await _settle(pilot, app)
        assert cards.index == index_before, (
            "a frontier tick must not snap the card selection"
        )


async def test_long_keys_backstop_cards_and_drill():
    """The 68-char-key lesson: long model/task keys truncate in-cell
    (never breaking the grid) and the full key rides the detail."""
    from tui.screens.monitor import CellDetailModal, RunCellsModal

    long_model = ("plant-dnabert-6mer-with-a-very-long-custom-alias-name"
                  "-that-exceeds-any-column")
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(
            _summary("finetuned-a-really-long-root-name-here",
                     SWEEP_RUNNING, done=1, total=2, mtime=1.0),),
            watermarks={})],
        cells={"/scans/finetuned-a-really-long-root-name-here": (
            _row(long_model, "GUE__emp_H3", {42: CELL_COMPLETED}),)},
        stats={"/scans/finetuned-a-really-long-root-name-here": _stats(
            done=1, total=2)},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        strip = _card_texts(screen, "mon-card-strip")[0]
        assert "finetuned-a-really-long-root-name-here" in strip, (
            "the strip carries the full root name (visual overflow clips)"
        )
        # the 68-char-key backstop on the matrix: the model column
        # ellipsis-truncates to the 20-cell name column, never a broken
        # grid (display-only; the full key rides the detail)
        rows = _card_texts(screen, "mon-matrix-row")
        assert len(rows) == 1
        assert rows[0][:20].endswith("…") and len(rows[0]) > 20, (
            "the long model name truncates with the ellipsis at the "
            "20-cell name column boundary"
        )
        await pilot.press("enter")
        await _settle(pilot, app)
        assert isinstance(app.screen, RunCellsModal)
        cells_table = app.screen.query_one("#mon-runcells-table", DataTable)
        model_cell = _table_text(cells_table, f"{long_model}__GUE__emp_H3",
                                 "model")
        assert "…" in model_cell, (
            "the in-cell truncation carries the ellipsis (display-only)"
        )
        # the full key rides the detail (never elided)
        await pilot.press("enter")
        await _settle(pilot, app)
        assert isinstance(app.screen, CellDetailModal)
        assert long_model in str(
            app.screen.query_one("#mon-celldetail-box").border_title)

# =====================================================================
# Task 2 — #41 optimistic paint, graduation, the empty-state route
# =====================================================================

async def test_optimistic_paint_skeleton_before_first_scan():
    """#41 (261018-kvj): the tab skeleton + the scanning note paint
    IMMEDIATELY on mount (zero scan round-trips — no 3.5s blank); the
    first scan message clears the note and fills the tabs. No data is
    fabricated during the scan window — skeleton + note only."""
    import threading

    gate = threading.Event()
    monitor = FakeMonitorService(scans=[_three_state_scan()])
    monitor.full_scan_gate = gate
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        app.push_screen(app.build_monitor_screen())
        await pilot.pause()
        await pilot.pause()
        screen = app.screen
        note = screen.query_one("#mon-scanning-note", Static)
        assert note.display is True, (
            "the scanning note paints BEFORE any scan lands"
        )
        assert _plain(note.content) == MON_SCANNING
        assert _label_text(screen, "#mon-tab-running") == (
            f"{MON_TAB_RUNNING} {MON_TAB_COUNT.format(n=0)}"), (
            "the tab skeleton renders zero counts — never fabricated rows"
        )
        assert len(screen.query_one("#mon-cards", ListView)) == 0

        gate.set()   # release the gated scan
        await _settle(pilot, app)
        assert screen.query_one("#mon-scanning-note").display is False, (
            "the first scan message clears the note"
        )
        assert len(screen.query_one("#mon-cards", ListView)) == 1


async def test_graduation_toast_and_running_to_history_move():
    """261018-kvj Task 2: a root transitioning running -> finished
    BETWEEN two on-screen scans fires the graduation toast naming the
    run, the card leaves Running, and the History row appears; a FRESH
    screen's first scan fires NO toast (no prior observation)."""
    monitor = FakeMonitorService(scans=[
        ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=35, total=36, mtime=2.0),),
            watermarks={}),
        ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_FINISHED, done=36, total=36, mtime=3.0),),
            watermarks={}),
    ])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert len(screen.query_one("#mon-cards", ListView)) == 1
        assert _toast_messages(app) == [], (
            "a fresh screen's first scan never fires a toast"
        )
        screen._tick_full()   # THIS scan observes the finish
        await _settle(pilot, app)
        assert MON_GRADUATED_DONE_TOAST.format(
            root="finetuned") in _toast_messages(app), (
            "the observed running->finished transition graduates loudly"
        )
        assert len(screen.query_one("#mon-cards", ListView)) == 0, (
            "the graduated card left the Running tab"
        )
        await pilot.press("right")
        await pilot.pause()
        table = screen.query_one("#mon-history", DataTable)
        assert "/scans/finetuned" in {
            str(key.value) for key in table.rows}, (
            "the graduated run joined the History tab"
        )

    # the interrupted graduation variant names the run with its own copy
    from tui.strings import MON_GRADUATED_INTERRUPTED_TOAST

    monitor = FakeMonitorService(scans=[
        ScanResult(sweeps=(_summary(
            "killed-run", SWEEP_RUNNING, done=2, total=9, mtime=2.0),),
            watermarks={}),
        ScanResult(sweeps=(_summary(
            "killed-run", SWEEP_ARTIFACTS_ONLY, done=2, mtime=3.0),),
            watermarks={}),
    ])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        screen._tick_full()
        await _settle(pilot, app)
        assert MON_GRADUATED_INTERRUPTED_TOAST.format(
            root="killed-run") in _toast_messages(app)


async def test_running_empty_enter_routes_to_slot4():
    """The Running tab's empty state enter navigates to slot 4 (the
    Run Config screen gains focus) — slot 4 owns the ONLY launch gate;
    slot 5 never duplicates it."""
    from tui.screens.run_config import RunConfigScreen

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(), watermarks={})])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert screen.query_one("#mon-running-empty").display is True
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        assert isinstance(app.screen, RunConfigScreen), (
            "enter on the empty Running tab routes to the launch gate"
        )


async def test_language_toggle_recompose_keeps_cadence_idempotent():
    """EHC-1 over the tabbed surface: the L toggle's recompose re-invokes
    on_mount — the cadence timers stop BEFORE re-arming (no orphaned
    pair firing forever), the tabs re-render in the ACTIVE language,
    and the screen state (cards, tab, selection) survives the rebuild."""
    from tui import strings as strings_module

    monitor = FakeMonitorService(scans=[_three_state_scan()])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        # the ACTIVE language's title renders first (a persisted zh
        # state file flips the boot language — never assume en)
        before_lang = strings_module.language()
        before_index = 0 if before_lang == "zh" else 1
        after_index = 1 - before_index
        assert _label_text(screen, "#mon-tab-history").startswith(
            strings_module._REGISTRY["MON_TAB_HISTORY"][before_index]), (
            "the mounted tabs render the boot language"
        )
        frontier_before = screen._frontier_timer
        full_before = screen._full_timer

        await pilot.press("L")
        await _settle(pilot, app)
        # the OTHER language's titles render (the recompose re-reads
        # the registry)
        assert _label_text(screen, "#mon-tab-history").startswith(
            strings_module._REGISTRY["MON_TAB_HISTORY"][after_index]), (
            "the recomposed tabs render the ACTIVE language"
        )
        assert screen._frontier_timer is not frontier_before, (
            "the recompose re-armed a FRESH frontier timer"
        )
        assert screen._full_timer is not full_before
        # exactly one live pair: the old timers stopped, the cadence
        # keeps dispatching (a bare second set_interval would double)
        before = len(monitor.frontier_calls)
        screen._tick_frontier()
        await _settle(pilot, app)
        assert len(monitor.frontier_calls) > before
        mon_frontier_workers = [
            worker for worker in app.workers
            if str(getattr(worker, "group", "") or "") == "mon-frontier"]
        assert len(mon_frontier_workers) <= 1, (
            "the recomposed cadence never doubles its workers"
        )
        # the state survived: the card and the selection are intact
        assert screen._card_order == ["/scans/finetuned"]
        await pilot.press("L")   # restore the boot language
        await _settle(pilot, app)
        assert strings_module.language() == before_lang


# =====================================================================
# Task 3 — the degradation sweep (T-11-07-02) + responsiveness (04)
# =====================================================================

async def test_degradation_corrupt_record_renders_last_known_good():
    """A service that THROWS mid-scan (the damaged-tree edge beyond the
    loader's tolerance): the previous render stands, the console never
    crashes (T-11-07-02)."""
    monitor = FakeMonitorService(
        scans=[_three_state_scan(), _three_state_scan()])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert len(screen.query_one("#mon-cards", ListView)) == 1, (
            "the healthy first render landed"
        )
        # a throwing full scan: the worker absorbs it; the tabs stand
        monitor.full_scan_throws = True
        screen._tick_full()
        await _settle(pilot, app)
        assert isinstance(app.screen, MonitorScreen), (
            "a throwing scan never crashes the console"
        )
        assert len(screen.query_one("#mon-cards", ListView)) == 1, (
            "the last-known-good render stands"
        )


async def test_degradation_manifest_mid_write_stays_running():
    """A manifest missing mid-write: the running rules hold (no
    finished flip, unknown total) — the finished state requires the
    COMPLETE manifest."""
    monitor = FakeMonitorService(scans=[ScanResult(sweeps=(
        _summary("finetuned", SWEEP_RUNNING, done=2, mtime=1.0),
    ), watermarks={})] * 3)
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        strip = _card_texts(screen, "mon-card-strip")[0]
        assert MON_TOTAL_UNKNOWN in strip, (
            "no manifest means the honest unknown total"
        )
        screen._tick_full()
        await _settle(pilot, app)
        assert len(screen.query_one("#mon-cards", ListView)) == 1, (
            "no manifest means no finished flip — the running rules hold"
        )


async def test_degradation_artifacts_only_never_running_card():
    """The prior-artifacts root renders on History with the ⏸ word and
    the unknown total — never a fabricated running card."""
    monitor = FakeMonitorService(scans=[ScanResult(sweeps=(
        _summary("seed-9527-artifacts", SWEEP_ARTIFACTS_ONLY, done=5,
                 mtime=1.0),
    ), watermarks={})] * 2)
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert len(screen.query_one("#mon-cards", ListView)) == 0, (
            "an artifacts-only root is NEVER a running card"
        )
        await pilot.press("right")
        await pilot.pause()
        table = screen.query_one("#mon-history", DataTable)
        state = _table_text(table, "/scans/seed-9527-artifacts", "state")
        assert state == MON_STATE_INTERRUPTED
        assert "⏵" not in state, "artifacts-only never renders running"
        assert _table_text(table, "/scans/seed-9527-artifacts",
                           "progress") == MON_TOTAL_UNKNOWN


async def test_degradation_live_root_deleted_mid_monitor():
    """A live root deleted mid-monitor: the scan skips it, its card and
    caches drop, the History tab keeps the other roots — no crash, no
    stale card."""
    with_root = ScanResult(sweeps=(
        _summary("finetuned", SWEEP_RUNNING, done=1, total=4, mtime=2.0),
        _summary("other", SWEEP_FINISHED, done=2, total=2, mtime=1.0),
    ), watermarks={})
    monitor = FakeMonitorService(
        scans=[with_root])   # the mount scan; the drop scan appends below
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        cards = screen.query_one("#mon-cards", ListView)
        assert len(cards) == 1
        assert "/scans/finetuned" in screen._cell_rows

        monitor._scans.append(ScanResult(sweeps=(
            _summary("other", SWEEP_FINISHED, done=2, total=2, mtime=1.0),
        ), watermarks={}))
        screen._tick_full()   # THIS scan drops the deleted root
        await _settle(pilot, app)
        assert isinstance(app.screen, MonitorScreen), "no crash"
        assert len(cards) == 0, "the deleted root's card dropped"
        assert "/scans/finetuned" not in screen._cell_rows, (
            "no stale per-root cache survives the vanished root"
        )


async def test_degradation_min_size_guard_round_trip_with_open_modal():
    """An open monitor modal survives the below-min round trip (the
    app-level guard owns the behavior; the screen must not fight it)."""
    from tui.app import MinSizeScreen
    from tui.screens.monitor import FailuresModal

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=1, total=2, mtime=1.0),),
            watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_FAILED}),)},
        stats={"/scans/finetuned": _stats(done=1, total=2)},
        failures={"/scans/finetuned": (
            FailureRow(model="model-a", task="task-1", seed=42,
                       error="boom", output_dir="/x"),)},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("f")
        await _settle(pilot, app)
        assert isinstance(app.screen, FailuresModal)

        await pilot.resize_terminal(60, 20)
        await pilot.pause()
        assert isinstance(app.screen, MinSizeScreen), (
            "below the minimum grid the guard is the whole surface"
        )
        await pilot.resize_terminal(120, 40)
        await pilot.pause()
        assert isinstance(app.screen, FailuresModal), (
            "the open modal survives the round trip beneath the guard"
        )


async def test_console_stays_responsive_while_scan_blocks():
    """T-11-07-04: while a fake full scan BLOCKS on a threading.Event,
    pilot presses still reach the app (a modal opens) — the console
    never freezes because every tick dispatches a worker."""
    import threading

    monitor = FakeMonitorService(scans=[_three_state_scan()])
    monitor.full_scan_gate = threading.Event()
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        # arm the block, then dispatch a full scan that will hang
        monitor.full_scan_gate = threading.Event()
        app.screen._tick_full()
        await pilot.pause()
        await pilot.pause()
        # the press still lands (a toast-capable action opens chrome)
        await pilot.press("a")
        await pilot.pause()
        from tui.screens.selection import PathInputModal

        assert isinstance(app.screen, PathInputModal), (
            "the console stays responsive while the scan worker blocks"
        )
        await pilot.press("escape")
        await pilot.pause()
        monitor.full_scan_gate.set()   # release; the worker completes
        await _settle(pilot, app)
        assert isinstance(app.screen, MonitorScreen)


# =====================================================================
# 261016-vxr (VXR-1/VXR-2/VXR-3): the [k] kill confirm over the
# launcher channel, scoped to the focused running card
# =====================================================================


def _kill_fixture_monitor():
    """The canonical k-kill fixture: one running root + cells + stats."""
    return FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=1, total=2, mtime=1.0),),
            watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_RUNNING}),)},
        stats={"/scans/finetuned": _stats(done=1, total=2)},
    )


async def test_k_opens_kill_confirm_y_kills_without_exiting():
    """VXR-2: k over the FOCUSED running card's live TUI-launched root
    opens the y-only kill confirm (enter structurally inert — EHC-2
    extended to the kill; n/esc cancel), and y dispatches the off-loop
    kill through the launcher channel with the RESOLVED root — the
    console NEVER exits on this path (stop training != exit console)."""
    from tui.screens.monitor import KillConfirmModal
    from tui.strings import MON_KILL_CONFIRM, MON_KILL_TOAST

    launcher = FakeMonitorLauncher(live=("/scans/finetuned",))
    app = _app(monitor=_kill_fixture_monitor(), launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)

        await pilot.press("k")
        await pilot.pause()
        assert isinstance(app.screen, KillConfirmModal), (
            "k over the focused live TUI sweep opens the kill confirm"
        )
        assert MON_KILL_CONFIRM in _plain(
            app.screen.query_one(Static).content)
        assert "/scans/finetuned" in str(
            app.screen.query_one("#confirm-box").border_title), (
            "the border title names the root the kill would signal"
        )

        # EHC-2: enter is structurally inert on the kill confirm
        await pilot.press("enter")
        await _settle(pilot, app)
        assert isinstance(app.screen, KillConfirmModal), (
            "enter must never confirm a kill (EHC-2)"
        )
        assert launcher.kill_calls == []

        # n cancels back to the monitor, nothing signalled
        await pilot.press("n")
        await pilot.pause()
        assert isinstance(app.screen, MonitorScreen)
        assert launcher.kill_calls == []

        # reopen with k, esc likewise cancels
        await pilot.press("k")
        await pilot.pause()
        assert isinstance(app.screen, KillConfirmModal)
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, MonitorScreen)
        assert launcher.kill_calls == []

        # reopen, y: the worker kills via the channel exactly once
        await pilot.press("k")
        await pilot.pause()
        assert isinstance(app.screen, KillConfirmModal)
        await pilot.press("y")
        await _settle(pilot, app)
        assert launcher.kill_calls == ["/scans/finetuned"], (
            "y dispatched the kill with the RESOLVED focused root"
        )
        assert not app._exit, (
            "stopping training NEVER exits the console"
        )
        assert MON_KILL_TOAST.format(
            root="/scans/finetuned") in _toast_messages(app)


async def test_kill_confirm_footer_shows_y_n_keycaps():
    """DNR-2 (261017-dnr): the kill confirm's answer keys are visible at
    a glance — the KillConfirmModal y/n bindings carry show=True with
    the exact-reuse descriptions (MON_KILL_KEYCAP for y, the
    LNC_EXIT_CONFIRM_NO pair for n) so the Footer renders the y/n
    keycaps beside esc; the inherited base enter stays show=False (the
    EHC-2 inert no-op is never advertised)."""
    launcher = FakeMonitorLauncher(live=("/scans/finetuned",))
    app = _app(monitor=_kill_fixture_monitor(), launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("k")
        await pilot.pause()
        from textual.binding import Binding
        from textual.widgets import Footer as FooterWidget

        from tui.screens.monitor import KillConfirmModal
        from tui.screens.selection import ConfirmModal
        from tui.strings import LNC_EXIT_CONFIRM_NO, MON_KILL_KEYCAP

        assert isinstance(app.screen, KillConfirmModal)
        entries = {binding.key: binding
                   for binding in KillConfirmModal.BINDINGS
                   if isinstance(binding, Binding)}
        assert entries["y"].show is True, (
            "the y answer key must render in the Footer"
        )
        assert entries["y"].description == MON_KILL_KEYCAP, (
            "y reuses the exact 停止/Kill pair — it is what y does"
        )
        assert entries["n"].show is True, (
            "the n answer key must render in the Footer"
        )
        assert entries["n"].description == LNC_EXIT_CONFIRM_NO
        base_entries = {binding.key: binding
                        for binding in ConfirmModal.BINDINGS
                        if isinstance(binding, Binding)}
        assert base_entries["enter"].show is False, (
            "the inert enter no-op is never advertised (EHC-2)"
        )
        assert app.screen.query(FooterWidget), (
            "the modal composes a Footer — the keycaps render"
        )


async def test_kill_confirm_message_bolds_y_n_tokens():
    """DNR-2 (261017-dnr): the kill confirm's [Y]/[N] tokens are
    prominent — the message Static's content is a rich Text with a bold
    span over every [Y]/[N] occurrence while the plain value still
    carries MON_KILL_CONFIRM byte-unchanged (span-safe existing
    assertions); the #confirm-box id and message-Static-first layout
    are preserved (on_mount + the first-Static test queries)."""
    launcher = FakeMonitorLauncher(live=("/scans/finetuned",))
    app = _app(monitor=_kill_fixture_monitor(), launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("k")
        await pilot.pause()
        from tui.screens.monitor import KillConfirmModal
        from tui.strings import MON_KILL_CONFIRM

        assert isinstance(app.screen, KillConfirmModal)
        content = app.screen.query_one(Static).content
        assert isinstance(content, Text), (
            "the message composes as a rich Text over the registry "
            "constant — never a markup string"
        )
        plain = content.plain
        assert MON_KILL_CONFIRM in plain, plain
        for token in ("[Y]", "[N]"):
            offset = plain.find(token)
            assert offset != -1, f"the {token} token must be present"
            while offset != -1:
                start, end = offset, offset + len(token)
                covered = any(span.start <= start and span.end >= end
                              and str(span.style) == "bold"
                              for span in content.spans)
                assert covered, (
                    f"the {token} at offset {offset} must carry a bold "
                    "span (Text.highlight_words)"
                )
                offset = plain.find(token, end)


async def test_k_outcome_toasts_dead_noop_and_failure():
    """VXR-2 outcome surfaces: already_dead -> MON_KILL_TOAST_DEAD; noop
    (the channel no longer knows the root) -> MON_KILL_UNAVAILABLE; a
    RAISING kill_sweep -> the MON_KILL_FAILED error toast (WR-03 — a
    post-confirm worker death surfaces, never a silent no-op)."""
    from tui.screens.monitor import KillConfirmModal
    from tui.strings import (
        MON_KILL_FAILED,
        MON_KILL_TOAST_DEAD,
        MON_KILL_UNAVAILABLE,
    )

    for outcome, expected_toast in (
            ("already_dead",
             lambda: MON_KILL_TOAST_DEAD.format(root="/scans/finetuned")),
            ("noop",
             lambda: MON_KILL_UNAVAILABLE.format(root="/scans/finetuned"))):
        launcher = FakeMonitorLauncher(
            live=("/scans/finetuned",), kill_outcomes=[outcome])
        app = _app(monitor=_kill_fixture_monitor(), launcher=launcher)
        async with app.run_test(size=(120, 40)) as pilot:
            await _open_monitor(pilot, app)
            await pilot.press("k")
            await pilot.pause()
            assert isinstance(app.screen, KillConfirmModal)
            await pilot.press("y")
            await _settle(pilot, app)
            assert expected_toast() in _toast_messages(app), (
                f"the {outcome} outcome surfaces its designed toast"
            )
            assert not app._exit

    launcher = FakeMonitorLauncher(
        live=("/scans/finetuned",),
        kill_raises=OSError("killpg failed"))
    app = _app(monitor=_kill_fixture_monitor(), launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("k")
        await pilot.pause()
        await pilot.press("y")
        await _settle(pilot, app)
        assert MON_KILL_FAILED.format(
            error="killpg failed") in _toast_messages(app), (
            "a raising kill surfaces the error toast — never silence"
        )
        assert not app._exit


async def test_k_focused_root_not_live_refuses_before_the_confirm():
    """VXR-2: a focused root NOT in live_sweeps() (CLI-launched or
    already dead) surfaces MON_KILL_UNAVAILABLE and NEVER opens a
    confirm the channel cannot execute — kill_sweep is never called."""
    from tui.screens.monitor import KillConfirmModal
    from tui.strings import MON_KILL_UNAVAILABLE

    launcher = FakeMonitorLauncher(live=())   # nothing TUI-launched
    app = _app(monitor=_kill_fixture_monitor(), launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("k")
        await _settle(pilot, app)
        assert MON_KILL_UNAVAILABLE.format(
            root="/scans/finetuned") in _toast_messages(app)
        assert not any(isinstance(screen, KillConfirmModal)
                       for screen in app.screen_stack), (
            "no confirm may open over a channel that cannot kill"
        )
        assert launcher.kill_calls == []


async def test_k_without_selection_or_below_grid_is_silent():
    """VXR-2 degradation: no selection on the active tab -> k is silent
    (the [f]/[t] precedent — no toast, no modal); below the minimum
    grid with a LIVE focused root -> no modal ever opens (no chrome
    over the guard)."""
    from tui.app import MinSizeScreen
    from tui.screens.monitor import KillConfirmModal

    monitor = FakeMonitorService(scans=[ScanResult(sweeps=(), watermarks={})])
    launcher = FakeMonitorLauncher(live=("/scans/finetuned",))
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("k")
        await _settle(pilot, app)
        assert isinstance(app.screen, MonitorScreen), (
            "no selection: k opens nothing"
        )
        assert _toast_messages(app) == [], "no selection: k is fully silent"
        assert launcher.kill_calls == []

    app = _app(monitor=_kill_fixture_monitor(),
               launcher=FakeMonitorLauncher(live=("/scans/finetuned",)))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.resize_terminal(60, 20)
        await pilot.pause()
        assert isinstance(app.screen, MinSizeScreen)
        await pilot.press("k")
        await _settle(pilot, app)
        assert not any(isinstance(screen, KillConfirmModal)
                       for screen in app.screen_stack), (
            "no kill chrome may open over the min-size guard"
        )


async def test_k_kill_never_consults_the_single_gpu_guard():
    """VXR-2 (EHC-3 pin): the kill path NEVER consults the single-GPU
    serialization guard — kill is the REMEDY for a busy single-GPU
    machine, not a launch; a guard reporting live roots must not block
    the stop."""
    from tui.screens.monitor import KillConfirmModal

    launcher = FakeMonitorLauncher(
        live=("/scans/finetuned",),
        single_gpu_blocked=("/scans/somewhere-else",))
    app = _app(monitor=_kill_fixture_monitor(), launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("k")
        await pilot.pause()
        assert isinstance(app.screen, KillConfirmModal), (
            "the single-GPU guard never gates the kill confirm"
        )
        await pilot.press("y")
        await _settle(pilot, app)
        assert launcher.kill_calls == ["/scans/finetuned"], (
            "y still kills on a guard-reported-busy machine"
        )


async def test_kill_runs_off_the_event_loop_console_stays_responsive():
    """VXR-2: kill_sweep blocks up to the launcher's kill grace — the
    call lands in the exclusive mon-kill worker, never on the event
    loop: while the kill blocks, the console still opens chrome (the
    responsiveness precedent), and the outcome toast lands once the
    gate releases."""
    import threading

    from tui.screens.monitor import KillConfirmModal
    from tui.screens.selection import PathInputModal
    from tui.strings import MON_KILL_TOAST

    gate = threading.Event()
    launcher = FakeMonitorLauncher(live=("/scans/finetuned",))
    launcher.kill_gate = gate
    app = _app(monitor=_kill_fixture_monitor(), launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("k")
        await pilot.pause()
        assert isinstance(app.screen, KillConfirmModal)
        await pilot.press("y")   # the worker now blocks on the gate
        await pilot.pause()
        await pilot.pause()

        # the loop stays responsive while the kill worker blocks
        await pilot.press("a")
        await pilot.pause()
        assert isinstance(app.screen, PathInputModal), (
            "the console stays responsive while kill_sweep blocks"
        )
        await pilot.press("escape")
        await pilot.pause()

        gate.set()   # release; the worker completes and posts
        await _settle(pilot, app, rounds=4)
        assert launcher.kill_calls == ["/scans/finetuned"]
        assert MON_KILL_TOAST.format(
            root="/scans/finetuned") in _toast_messages(app)


async def test_monitor_help_lists_the_kill_row():
    """VXR-2/261017-cdr/261017-mad: the ? help modal over the monitor
    carries the k row (the BINDINGS projection — the keycap joins after
    the tab-switch row); the 261016-vxr app-level Q row is RETIRED with
    its intercept."""
    from tui.app import HelpModal
    from tui.strings import (
        APP_HELP_ROW,
        MON_KILL_KEYCAP,
        MON_TAB_SWITCH_KEYCAP,
    )

    app = _app(monitor=FakeMonitorService(scans=[_three_state_scan()]))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("question_mark")
        await pilot.pause()
        assert isinstance(app.screen, HelpModal)
        rows = [str(static.content) for static in app.screen.query(Static)]
        assert APP_HELP_ROW.format(key="k", label=MON_KILL_KEYCAP) in rows, (
            "the slot-5 kill keycap lists in the monitor help"
        )
        assert APP_HELP_ROW.format(
            key="tab", label=MON_TAB_SWITCH_KEYCAP) in rows, (
            "the tab-switch keycap lists in the monitor help"
        )
        assert not any(row.startswith("[Q]") for row in rows), (
            "the retired any-focus Q row must not list"
        )

# =====================================================================
# 261018-toe — the [d] delete family (History-tab scoped, the kill
# family's mirror: strong y-only confirm, worker-thread rm -rf, live
# refusal pre-modal AND in-worker, per-tab footer keycaps)
# =====================================================================


def _history_fixture_monitor(cells=None):
    """The canonical [d]/[e] fixture: one FINISHED History root + its
    cell rows (2+1 seed counts across a failed, a completed, and an
    interrupted row)."""
    if cells is None:
        cells = (
            _row("model-a", "task-1", {42: CELL_FAILED,
                                       43: CELL_COMPLETED}),
            _row("model-b", "task-2", {42: CELL_INTERRUPTED}),
        )
    return FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "old-run", SWEEP_FINISHED, done=3, total=4, mtime=100.0),),
            watermarks={})],
        cells={"/scans/old-run": cells},
    )


async def test_d_opens_delete_confirm_y_deletes_and_rescans():
    """261018-toe: d over the FOCUSED History row opens the strong
    y-only DeleteConfirmModal naming the FULL root path and the honest
    training-item count (the summed per-row seed counts); enter is
    structurally inert; n cancels; y dispatches the off-loop deletion
    through the delete_root seam + the manual-root hygiene, fires the
    success toast, and the full rescan follows (the row disappears)."""
    from tui.screens.monitor import DeleteConfirmModal
    from tui.strings import MON_DELETE_CONFIRM, MON_DELETE_TOAST

    monitor = _history_fixture_monitor()
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("right")
        await pilot.pause()

        full_calls_before = len(monitor.full_calls)
        await pilot.press("d")
        await _settle(pilot, app)
        assert isinstance(app.screen, DeleteConfirmModal), (
            "d over the focused History row opens the delete confirm"
        )
        copy = _plain(app.screen.query_one(Static).content)
        assert MON_DELETE_CONFIRM.format(
            root="/scans/old-run", n=3) in copy, copy
        assert "/scans/old-run" in str(
            app.screen.query_one("#confirm-box").border_title), (
            "the border title names the root the deletion would remove"
        )

        # EHC-2: enter is structurally inert on the delete confirm
        await pilot.press("enter")
        await _settle(pilot, app)
        assert isinstance(app.screen, DeleteConfirmModal), (
            "enter must never confirm a deletion (EHC-2)"
        )
        assert monitor.delete_calls == []

        # n cancels back to the monitor, nothing deleted
        await pilot.press("n")
        await pilot.pause()
        assert isinstance(app.screen, MonitorScreen)
        assert monitor.delete_calls == []

        # reopen with d; y deletes through the seam exactly once
        await pilot.press("d")
        await _settle(pilot, app)
        assert isinstance(app.screen, DeleteConfirmModal)
        await pilot.press("y")
        await _settle(pilot, app)
        assert monitor.delete_calls == ["/scans/old-run"], (
            "y dispatched the deletion with the RESOLVED focused root"
        )
        assert monitor.removed_manual_roots == ["/scans/old-run"], (
            "the manual-root hygiene rides the delete worker"
        )
        assert MON_DELETE_TOAST.format(
            root="/scans/old-run") in _toast_messages(app)
        assert len(monitor.full_calls) > full_calls_before, (
            "the deletion triggers an immediate full rescan"
        )


async def test_d_uppercase_twins_match_lowercase():
    """SOAK-2/F3 on the delete surface: the displayed copy advertises
    [Y]/[N] — uppercase Y deletes exactly like y, N cancels like n."""
    from tui.screens.monitor import DeleteConfirmModal
    from tui.strings import MON_DELETE_TOAST

    monitor = _history_fixture_monitor()
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("right")
        await pilot.pause()
        await pilot.press("d")
        await _settle(pilot, app)
        assert isinstance(app.screen, DeleteConfirmModal)
        await pilot.press("N")   # the uppercase cancel twin
        await pilot.pause()
        assert isinstance(app.screen, MonitorScreen)
        assert monitor.delete_calls == []
        await pilot.press("d")
        await _settle(pilot, app)
        await pilot.press("Y")   # the uppercase confirm twin
        await _settle(pilot, app)
        assert monitor.delete_calls == ["/scans/old-run"]
        assert MON_DELETE_TOAST.format(
            root="/scans/old-run") in _toast_messages(app)


async def test_d_live_root_refuses_before_the_confirm():
    """The fail-safe pin (NON-VACUOUS): a root whose last scan state is
    SWEEP_RUNNING — the dual-presence badge row shape — can NEVER open
    the delete modal: the refusal toast fires first and delete_root is
    never called."""
    from tui.screens.monitor import DeleteConfirmModal
    from tui.strings import MON_DELETE_REFUSED_LIVE

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(
            _summary("rerun-root", SWEEP_RUNNING, done=1, total=2,
                     mtime=100.0),), watermarks={})],
        cells={"/scans/rerun-root": (
            _row("model-a", "task-1", {42: CELL_COMPLETED}),)},
        stats={"/scans/rerun-root": _stats(done=1, total=2)},
    )
    app = _app(monitor=monitor, launcher=FakeMonitorLauncher(
        live=("/scans/rerun-root",)))
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        # the dual-presence row sits on History (resume markers > 0)
        monitor._resume["/scans/rerun-root"] = 3
        screen = app.screen
        screen._tick_full()
        await _settle(pilot, app)
        # the card carries a group -> the arrows move the matrix focus;
        # TAB always switches (the 261019-f0x precedence)
        await pilot.press("tab")
        await pilot.pause()
        await pilot.press("d")
        await _settle(pilot, app)
        assert MON_DELETE_REFUSED_LIVE.format(
            root="/scans/rerun-root") in _toast_messages(app)
        assert not any(isinstance(screen, DeleteConfirmModal)
                       for screen in app.screen_stack), (
            "no delete confirm may open over a live root"
        )
        assert monitor.delete_calls == []


async def test_d_confirm_to_worker_race_refused_live():
    """The race closer: a root that goes LIVE between the y confirm and
    the delete worker is refused IN THE WORKER (the re-check) — nothing
    is deleted and the refusal toast surfaces (never a silent no-op)."""
    import threading

    from tui.screens.monitor import DeleteConfirmModal
    from tui.strings import MON_DELETE_REFUSED_LIVE

    class _FlipLiveLauncher(FakeMonitorLauncher):
        """live_sweeps() reports the flip-set roots once the event is
        set — the confirm-to-worker race scripting."""

        def __init__(self, live_later):
            super().__init__()
            self._live_later = tuple(live_later)
            self.flip = threading.Event()

        def live_sweeps(self):
            if self.flip.is_set():
                return self._live_later
            return self._live

    monitor = _history_fixture_monitor()
    launcher = _FlipLiveLauncher(("/scans/old-run",))
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("right")
        await pilot.pause()
        await pilot.press("d")
        await _settle(pilot, app)
        assert isinstance(app.screen, DeleteConfirmModal), (
            "the pre-modal check passed while the root was still dead"
        )
        launcher.flip.set()   # the root goes live AFTER the confirm
        await pilot.press("y")
        await _settle(pilot, app)
        assert monitor.delete_calls == [], (
            "the worker-side re-check refused — nothing was deleted"
        )
        assert MON_DELETE_REFUSED_LIVE.format(
            root="/scans/old-run") in _toast_messages(app)


async def test_d_off_tab_no_selection_and_below_grid_are_silent():
    """The [f]/[t] scoping precedent on [d]: on the RUNNING tab with a
    focused card, with no History selection, and below the minimum
    grid — d opens nothing, silently (no toast, no modal)."""
    from tui.app import MinSizeScreen
    from tui.screens.monitor import DeleteConfirmModal

    # on the Running tab with a focused card: silent
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=1, total=2, mtime=1.0),),
            watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_RUNNING}),)},
        stats={"/scans/finetuned": _stats(done=1, total=2)},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("d")
        await _settle(pilot, app)
        assert isinstance(app.screen, MonitorScreen), (
            "d on the Running tab opens nothing"
        )
        assert _toast_messages(app) == []
        assert monitor.delete_calls == []

    # no History rows at all: silent on the History tab
    monitor = FakeMonitorService(scans=[ScanResult(sweeps=(), watermarks={})])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("right")
        await pilot.pause()
        await pilot.press("d")
        await _settle(pilot, app)
        assert isinstance(app.screen, MonitorScreen)
        assert _toast_messages(app) == []
        assert monitor.delete_calls == []

    # below the minimum grid with a focused History row: no chrome
    app = _app(monitor=_history_fixture_monitor())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("right")
        await pilot.pause()
        await pilot.resize_terminal(60, 20)
        await pilot.pause()
        assert isinstance(app.screen, MinSizeScreen)
        await pilot.press("d")
        await _settle(pilot, app)
        assert not any(isinstance(screen, DeleteConfirmModal)
                       for screen in app.screen_stack), (
            "no delete chrome may open over the min-size guard"
        )


async def test_d_worker_exception_surfaces_error_toast():
    """WR-03: a raising delete_root after the operator confirmed y
    surfaces the MON_DELETE_FAILED error toast — never a silent
    no-op."""
    from tui.strings import MON_DELETE_FAILED

    monitor = _history_fixture_monitor()
    monitor._delete_raises = OSError("read-only filesystem")
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("right")
        await pilot.pause()
        await pilot.press("d")
        await _settle(pilot, app)
        await pilot.press("y")
        await _settle(pilot, app)
        assert MON_DELETE_FAILED.format(
            error="read-only filesystem") in _toast_messages(app), (
            "a raising delete surfaces the error toast — never silence"
        )


async def test_d_e_footer_keycaps_history_tab_only():
    """The per-active-tab footer ruling: the [d]/[e] keycaps render in
    the bottom bar's left segment ONLY while the History tab is active
    — the Running tab's footer stays byte-identical to the pre-[d]/[e]
    projection (the uncommitted monitor goldens hold), and the flip
    both ways follows the tab switch."""
    from tui.screens.nav import KeycapsStatic
    from tui.strings import MON_DELETE_KEYCAP, MON_RESUME_KEYCAP

    monitor = _history_fixture_monitor()
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        await pilot.pause()   # let the mount footer refresh land

        def footer_text() -> str:
            return str(screen.query_one(
                "#nav-left-keycaps", KeycapsStatic).content)

        assert "[d]" not in footer_text() and "[e]" not in footer_text(), (
            "the Running-tab footer carries NO d/e keycaps"
        )
        await pilot.press("right")
        await pilot.pause()
        copy = footer_text()
        assert "[d]" in copy and MON_DELETE_KEYCAP in copy, copy
        assert "[e]" in copy and MON_RESUME_KEYCAP in copy, copy
        await pilot.press("left")
        await pilot.pause()
        assert "[d]" not in footer_text() and "[e]" not in footer_text(), (
            "the flip back drops the d/e keycaps again"
        )


# =====================================================================
# 261018-toe — the [e] resume family (History-tab scoped: honest
# confirm over the derived incomplete pairs, the shared
# preflight/launch/E2' stages through launch_from_pairs)
# =====================================================================


async def test_e_confirm_names_pairs_times_seeds_and_launches():
    """261018-toe: e over the FOCUSED History row derives the incomplete
    set off-loop and the confirm names it HONESTLY — pairs × seeds with
    the completed-cells-skip note; y reaches launch_from_pairs with the
    SAME derived pairs/seeds/lane (the worker's re-derivation equals
    the confirm-side one — WR-02/03), never the [f] failures path."""
    from tui.screens.selection import ConfirmModal
    from tui.strings import MON_RESUME_CONFIRM, MON_RESUME_TOAST

    monitor = _history_fixture_monitor()
    launcher = FakeMonitorLauncher()
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("right")
        await pilot.pause()
        await pilot.press("e")
        await _settle(pilot, app)
        assert isinstance(app.screen, ConfirmModal), (
            "the resume always sits behind its own launch confirm"
        )
        copy = str(app.screen.query_one(Static).content)
        assert MON_RESUME_CONFIRM.format(
            pairs=2, seeds="42, 43", n=4) in copy, copy

        # EHC-2: enter is structurally inert on the launch confirm
        await pilot.press("enter")
        await _settle(pilot, app)
        assert isinstance(app.screen, ConfirmModal)
        assert launcher.env_calls == 0

        await pilot.press("y")   # confirm (EHC-2: y launches)
        await _settle(pilot, app)
        assert launcher.env_calls == 1, "the env preflight re-entered"
        assert len(launcher.resume_calls) == 1
        pairs, seeds, root, peft, variant, phrase = launcher.resume_calls[0]
        assert pairs == (("model-a", "task-1"), ("model-b", "task-2")), (
            "exactly the failed + interrupted pairs, sorted distinct — "
            "the worker's re-derivation equals the confirm-side one"
        )
        assert seeds == (42, 43), "the root's own seed set fans out"
        assert root == "/scans/old-run"
        assert peft == "none" and variant == "none"
        assert phrase is None, "an ordinary partial resume carries no phrase"
        assert launcher.rerun_calls == [], (
            "the resume NEVER routes through the [f] failures path"
        )
        assert monitor.rerun_lane_calls == ["/scans/old-run"] * 2, (
            "the lane is read through the service seam on BOTH sides of "
            "the confirm (the derive worker + the launch worker)"
        )
        assert MON_RESUME_TOAST.format(
            cells="—", root="old-run") in _toast_messages(app)


async def test_e_nothing_to_resume_toast_launcher_untouched():
    """A root whose cells are all complete: the nothing-to-resume toast
    lands, NO modal opens, and the launcher is never consulted."""
    from tui.screens.selection import ConfirmModal
    from tui.strings import MON_RESUME_NOTHING

    monitor = _history_fixture_monitor(cells=(
        _row("model-a", "task-1", {42: CELL_COMPLETED,
                                   43: CELL_SKIPPED}),))
    launcher = FakeMonitorLauncher()
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("right")
        await pilot.pause()
        await pilot.press("e")
        await _settle(pilot, app)
        assert MON_RESUME_NOTHING.format(
            root="/scans/old-run") in _toast_messages(app)
        assert not isinstance(app.screen, ConfirmModal)
        assert launcher.env_calls == 0
        assert launcher.resume_calls == []


async def test_e_live_root_refuses_before_any_modal():
    """A live root (the dual-presence badge row shape) never resumes:
    the refusal toast fires before any modal and nothing launches."""
    from tui.screens.selection import ConfirmModal
    from tui.strings import MON_RESUME_REFUSED_LIVE

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(
            _summary("rerun-root", SWEEP_RUNNING, done=1, total=2,
                     mtime=100.0),), watermarks={})],
        cells={"/scans/rerun-root": (
            _row("model-a", "task-1", {42: CELL_FAILED}),)},
        stats={"/scans/rerun-root": _stats(done=1, total=2)},
    )
    launcher = FakeMonitorLauncher(live=("/scans/rerun-root",))
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        monitor._resume["/scans/rerun-root"] = 3
        app.screen._tick_full()
        await _settle(pilot, app)
        await pilot.press("tab")   # the card has a group: tab switches
        await pilot.pause()
        await pilot.press("e")
        await _settle(pilot, app)
        assert MON_RESUME_REFUSED_LIVE.format(
            root="/scans/rerun-root") in _toast_messages(app)
        assert not isinstance(app.screen, ConfirmModal)
        assert launcher.env_calls == 0
        assert launcher.resume_calls == []


async def test_e_single_gpu_busy_refuses_before_the_confirm():
    """EHC-3 (the request_rerun mirror): the single-GPU guard pre-checks
    BEFORE the resume confirm — y is never reached on a busy
    single-GPU machine."""
    from tui.screens.selection import ConfirmModal
    from tui.strings import LNC_SINGLE_GPU_BLOCKED

    monitor = _history_fixture_monitor()
    launcher = FakeMonitorLauncher(
        single_gpu_blocked=("/scans/somewhere-live",))
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("right")
        await pilot.pause()
        await pilot.press("e")
        await _settle(pilot, app)
        assert not isinstance(app.screen, ConfirmModal), (
            "the single-GPU pre-check refuses BEFORE the confirm modal"
        )
        assert any(LNC_SINGLE_GPU_BLOCKED.format(
            roots="/scans/somewhere-live") in message
            for message in _toast_messages(app)), _toast_messages(app)
        assert launcher.env_calls == 0
        assert launcher.resume_calls == []


async def test_e_env_block_renders_the_same_modal():
    """A preflight FAIL renders the SAME env-block modal as slot 4 and
    [f]->[r] — the resume can never bypass the gate."""
    from tui.screens.run_config import EnvBlockModal

    monitor = _history_fixture_monitor()
    launcher = FakeMonitorLauncher(preflight=EnvPreflight(
        can_launch=False,
        reasons=("cuda: no device",),
        failed_kernels=("cuda",)))
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("right")
        await pilot.pause()
        await pilot.press("e")
        await _settle(pilot, app)
        await pilot.press("y")   # confirm the resume (EHC-2)
        await _settle(pilot, app)
        assert isinstance(app.screen, EnvBlockModal), (
            "a doomed resume never launches — the same env block"
        )
        assert launcher.resume_calls == []


async def test_e_e2x_phrase_refusal_reprompts_through_the_resume_worker():
    """CR-01 on the resume lane: a full-matrix incomplete set over 3
    seeds refuses at the phrase stage (Task 1's service-tier proof
    surfacing here) — the E2' re-prompt appears, and the typed phrase
    threads back through the RESUME worker (resume_calls grows, the
    [f] failures path is NEVER consulted)."""
    from tui.screens.run_config import E2PhraseModal
    from tui.screens.selection import ConfirmModal

    cells = tuple(
        _row(f"model-{index}", "task-1", {seed: CELL_FAILED
                                          for seed in (42, 43, 44)})
        for index in range(3))
    monitor = _history_fixture_monitor(cells=cells)
    launcher = FakeMonitorLauncher(resume_outcomes=[
        GateRefusal(stage="phrase", expected="old-run")])
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("right")
        await pilot.pause()
        await pilot.press("e")
        await _settle(pilot, app)
        assert isinstance(app.screen, ConfirmModal)
        await pilot.press("y")   # confirm the resume (EHC-2)
        await _settle(pilot, app)
        assert isinstance(app.screen, E2PhraseModal), (
            "the phrase-stage refusal escalates to the typed-phrase "
            "modal — the E2' boundary holds on the [e] path"
        )
        assert launcher.resume_calls[0][5] is None, (
            "the first attempt carried no phrase (the gate refused)"
        )
        for key in "old-run":
            await pilot.press(key)
        await pilot.pause()
        await pilot.press("enter")   # the exact match ADVANCES (EHC-2)
        await pilot.pause()
        await pilot.press("y")       # y carries the typed phrase
        await _settle(pilot, app)
        assert len(launcher.resume_calls) == 2
        assert launcher.resume_calls[1][5] == "old-run", (
            "the re-prompt's typed phrase threads the resume re-launch"
        )
        assert launcher.rerun_calls == [], (
            "the routing pin: the resume re-prompt routes through the "
            "RESUME worker, never the [f] failures path"
        )


async def test_e_preflight_exception_surfaces_error_toast():
    """WR-03 through the shared pipeline: a raising preflight after the
    operator confirmed y surfaces the error toast — never a silent
    no-op launch."""
    from tui.strings import LNC_LAUNCH_FAILED_TOAST

    monitor = _history_fixture_monitor()
    launcher = FakeMonitorLauncher(
        env_raises=OSError("quick-check kernel spawn failed"))
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        await pilot.press("right")
        await pilot.pause()
        await pilot.press("e")
        await _settle(pilot, app)
        await pilot.press("y")   # confirm the resume (EHC-2)
        await _settle(pilot, app)
        assert any(LNC_LAUNCH_FAILED_TOAST.format(
            error="quick-check kernel spawn failed") in toast
            for toast in _toast_messages(app)), _toast_messages(app)
        assert launcher.resume_calls == [], "nothing launched"

# =====================================================================
# 261017-uwr redirects — the drill ordering/glyphs + the eta segment
# (the always-visible cells table became the read-once drill)
# =====================================================================


def _uwr_row(model, states, newest_mtime=None):
    """One CellRow fixture with explicit seed states (the _row twin
    carrying the UWR-4 newest_mtime sort key)."""
    return CellRow(
        model=model, task="task-x",
        seeds=tuple(CellSeed(seed=42 + index, state=state,
                             fraction_states=None)
                    for index, state in enumerate(states)),
        newest_mtime=newest_mtime)


def _uwr_service(cells):
    """The fake service over one live running root."""
    return FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned-smoke", SWEEP_RUNNING, done=2, total=5, mtime=1.0),),
            watermarks={})],
        cells={"/scans/finetuned-smoke": tuple(cells)},
        stats={"/scans/finetuned-smoke": _stats(done=2, total=5)},
    )


async def _drill_uwr_cells(pilot, app):
    """Open the run drill over the fixture's running root."""
    from tui.screens.monitor import RunCellsModal

    await pilot.press("enter")   # the focused card
    await _settle(pilot, app)
    assert isinstance(app.screen, RunCellsModal)
    return app.screen.query_one("#mon-runcells-table", DataTable)


async def test_drill_live_on_top_ordering_with_fresh_running_first():
    """UWR-4 carried into the drill: group 0 running rows on top
    (freshest newest_mtime FIRST, mtime-None last), group 1 unfinished
    non-running rows (failed / interrupted / queued) key ASC, group 2
    completed rows sink — the live row is never buried under dead
    history."""
    monitor = _uwr_service((
        _uwr_row("d-done", (CELL_COMPLETED,)),
        _uwr_row("m-int", (CELL_INTERRUPTED,)),
        _uwr_row("a-run-old", (CELL_RUNNING,), newest_mtime=1000.0),
        _uwr_row("z-run-fresh", (CELL_RUNNING,), newest_mtime=2000.0),
        _uwr_row("c-queued", (CELL_QUEUED,)),
        _uwr_row("b-fail", (CELL_FAILED,)),
        _uwr_row("y-run-nomtime", (CELL_RUNNING,)),
    ))
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        table = await _drill_uwr_cells(pilot, app)
        order = [str(key.value) for key in table.rows]
        assert order == [
            "z-run-fresh__task-x",   # group 0: freshest running first
            "a-run-old__task-x",
            "y-run-nomtime__task-x",  # running without mtime last
            "b-fail__task-x",        # group 1: unfinished, key ASC
            "c-queued__task-x",
            "m-int__task-x",
            "d-done__task-x",        # group 2: completed sinks
        ], order
        await pilot.press("escape")
        await pilot.pause()


async def test_interrupted_entry_renders_glyph_word_and_counts():
    """UWR-1's render leg in the drill: an interrupted fold row carries
    the ⏸ glyph-word + its done/total seed counts (wide), and the
    narrow grid keeps the glyph + counts form (the state-word
    degradation)."""
    monitor = _uwr_service((
        _uwr_row("model-dead", (CELL_INTERRUPTED, CELL_INTERRUPTED)),
    ))
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        table = await _drill_uwr_cells(pilot, app)
        entry = "model-dead__task-x"
        assert _table_text(table, entry, "state") == (
            f"{MON_STATE_INTERRUPTED} 0/2"), (
            "the interrupted fold renders the ⏸ glyph-word + its "
            "terminal/total seed counts"
        )
        assert _table_text(table, entry, "progress") == "—", (
            "interrupted rows carry no progress (nothing parses)"
        )
        await pilot.press("escape")
        await pilot.pause()

    # the narrow degradation at the 80-col grid
    app = _app(monitor=_uwr_service((
        _uwr_row("model-dead", (CELL_INTERRUPTED,)),
    )))
    async with app.run_test(size=(80, 24)) as pilot:
        await _open_monitor(pilot, app)
        table = await _drill_uwr_cells(pilot, app)
        assert _table_text(
            table, "model-dead__task-x", "state") == "⏸ 0/1", (
            "narrow drops the state word — the ⏸ glyph + counts remain"
        )


async def test_running_entry_renders_eta_segment_or_honest_dash():
    """VXR-1 in the drill: a running entry whose CellProgress carries a
    derivable eta appends the format_eta segment after the bar; eta
    None renders the trailing dim dash — the honest underivable, never
    a fabricated number."""
    from tui.services.sweep_monitor import format_eta

    monitor = _uwr_service((
        _row("model-a", "task-1", {42: CELL_RUNNING}),
        _row("model-b", "task-2", {42: CELL_RUNNING}),
    ))
    monitor._progress = {
        ("model-a", "task-1"): CellProgress(
            step=300, max_steps=1000, percent=30, eta_seconds=1800.0),
        ("model-b", "task-2"): CellProgress(
            step=600, max_steps=1000, percent=60),  # eta underivable
    }
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        table = await _drill_uwr_cells(pilot, app)
        assert _table_text(table, "model-a__task-1", "progress") == (
            f"300/1000 30% ███······· {format_eta(1800.0)}"), (
            "the derivable eta rides the progress cell after the bar"
        )
        assert _table_text(table, "model-b__task-2", "progress") == (
            "600/1000 60% ██████···· —"), (
            "eta None renders the trailing dim dash, never a guess"
        )


async def test_running_entry_without_progress_renders_indeterminate():
    """The honest degradation in the drill: a RUNNING entry whose
    progress source yields nothing renders the designed indeterminate
    constant, never a fabricated number. The row is a CURVE cell
    (fraction_states) — the entry fold composes over the seed's own
    folded state."""
    monitor = _uwr_service((
        _row("model-a", "task-1",
             {42: CELL_RUNNING, 43: CELL_QUEUED}, fractions={
                 42: (("frac_0.3", CELL_COMPLETED),
                      ("frac_0.6", CELL_RUNNING),
                      ("frac_1.0", CELL_QUEUED)),
             }),))
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        table = await _drill_uwr_cells(pilot, app)
        entry = "model-a__task-1"
        assert _table_text(table, entry, "state") == (
            f"{MON_STATE_RUNNING} 0/2"), (
            "the curve seed folds to the running entry state"
        )
        assert _table_text(table, entry, "progress") == (
            MON_PROGRESS_INDETERMINATE), (
            "nothing parses — the honest indeterminate, never a number"
        )


async def test_history_reorder_preserves_cursor_identity():
    """WR-05 over the History table: a scan that changes the
    newest-first ORDER (a root's activity overtakes another's) rebuilds
    the rows in the new order while the operator's CURSOR ROW IDENTITY
    survives the reorder (move_cursor by key, scroll=False)."""
    first = ScanResult(sweeps=(
        _summary("run-a", SWEEP_FINISHED, done=1, total=1, mtime=1000.0),
        _summary("run-b", SWEEP_FINISHED, done=1, total=1, mtime=2000.0),
    ), watermarks={})
    monitor = FakeMonitorService(scans=[first])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        await pilot.press("right")
        await pilot.pause()
        table = screen.query_one("#mon-history", DataTable)
        assert [str(key.value) for key in table.rows] == [
            "/scans/run-b", "/scans/run-a"]
        table.action_cursor_down()   # row 1: run-a
        await pilot.pause()
        assert str(table.coordinate_to_cell_key(
            table.cursor_coordinate)[0].value) == "/scans/run-a"

        # run-a overtakes: the order flips, the cursor follows its KEY
        monitor._scans.append(ScanResult(sweeps=(
            _summary("run-a", SWEEP_FINISHED, done=1, total=1, mtime=9000.0),
            _summary("run-b", SWEEP_FINISHED, done=1, total=1, mtime=2000.0),
        ), watermarks={}))
        screen._tick_full()
        await _settle(pilot, app)
        assert [str(key.value) for key in table.rows] == [
            "/scans/run-a", "/scans/run-b"]
        assert str(table.coordinate_to_cell_key(
            table.cursor_coordinate)[0].value) == "/scans/run-a", (
            "the cursor follows its ROW KEY across the reorder — the "
            "operator's selection never snaps to row 0"
        )


# =====================================================================
# 261018-08g (SOAK-1/F1): the session hoist over the fresh-build factory
# =====================================================================

async def test_build_monitor_screen_builds_fresh_instances_over_one_session():
    """The F1 fix's structural pin: ``build_monitor_screen`` returns a
    FRESH MonitorScreen per call (the deleted cached-instance design
    never repainted after its first removal — the dead-5 freeze), and
    every build carries the ONE shared MonitorSession constructed on
    the composition root (the SEL-01 marks-set precedent)."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        first = app.build_monitor_screen()
        second = app.build_monitor_screen()
        assert first is not second, (
            "each navigation must build a fresh MonitorScreen — the "
            "cached-instance design is the dead-5 root cause"
        )
        assert first._session is app._monitor_session, (
            "a built screen reads the composition-root session"
        )
        assert second._session is app._monitor_session, (
            "every build shares the ONE session — navigation state "
            "must not fork per instance"
        )


async def test_session_launch_injections_survive_rebuilds():
    """The session hoist's state-survival pin: the D-13 launch
    injections recorded through one screen (or the session) are visible
    on a FRESHLY BUILT screen — the guarantee the cached instance used
    to provide, now without the repaint bug. The cells==0 re-run
    semantics (a stale expected total pops, WR-02) survive too.
    (261018-kvj: the attach field retired with the attach concept —
    the stats seams are the surviving state.)"""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        first = app.build_monitor_screen()
        app.push_screen(first)
        await _settle(pilot, app)
        first.note_launch("/scans/finetuned", 3)
        app.pop_screen()
        await pilot.pause()

        second = app.build_monitor_screen()
        assert second is not first
        assert second._expected_totals.get("/scans/finetuned") == 3, (
            "the D-13 expected total survives the rebuild"
        )
        assert second._fallback_starts.get("/scans/finetuned") is not None, (
            "the fallback start survives the rebuild"
        )

        # WR-02 semantics ride on the session: a cells==0 note (the
        # re-run flow) clears the stale expected total
        app._monitor_session.note_launch("/scans/finetuned", 0)
        assert "/scans/finetuned" not in second._expected_totals, (
            "a cells==0 note pops the stale expected total (WR-02)"
        )


async def test_sweep_launched_records_via_session_lands_on_fresh_screen():
    """The D-13 auto-nav on the fresh-instance design: ``sweep_launched``
    records on the shared session WITHOUT building a screen, and the
    MonitorSwitchRequested handler switches to a FRESH build reading
    the session — the launch lands with its expected total."""
    from tui.screens.monitor import MonitorScreen as _MonitorScreen

    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert app._monitor_screen is None, (
            "no monitor screen exists before the first launch"
        )
        app.sweep_launched("/scans/launched-root", 5)
        # the record landed on the session synchronously — no screen
        # was built to carry it (the F1 design: the fresh screen is
        # built by the switch handler)
        assert app._monitor_session.expected_totals.get(
            "/scans/launched-root") == 5
        assert app._monitor_session.fallback_starts.get(
            "/scans/launched-root") is not None
        await _settle(pilot, app, rounds=4)
        assert isinstance(app.screen, _MonitorScreen), (
            "the D-13 message switched to the monitor screen"
        )
        screen = app.screen
        assert screen._expected_totals.get("/scans/launched-root") == 5, (
            "the fresh screen reads the expected total from the session"
        )


async def test_kill_confirm_uppercase_twins_match_lowercase():
    """261018-08g (SOAK-2/F3): the kill confirm's copy advertises [Y]/
    [N] — uppercase Y must fire the kill callback exactly like y (the
    console never exits), uppercase N must cancel exactly like n. On
    HEAD the uppercase presses were inert (the soak read the modal as
    a dead console)."""
    from tui.screens.monitor import KillConfirmModal

    launcher = FakeMonitorLauncher(live=("/scans/finetuned",))
    app = _app(monitor=_kill_fixture_monitor(), launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)

        await pilot.press("k")
        await pilot.pause()
        assert isinstance(app.screen, KillConfirmModal)
        # uppercase N cancels, nothing signalled
        await pilot.press("N")
        await pilot.pause()
        assert isinstance(app.screen, MonitorScreen), (
            "uppercase N must cancel the kill confirm (the copy says [N])"
        )
        assert launcher.kill_calls == []

        # uppercase Y fires the confirm callback — the console stays up
        await pilot.press("k")
        await pilot.pause()
        assert isinstance(app.screen, KillConfirmModal)
        await pilot.press("Y")
        await _settle(pilot, app)
        assert launcher.kill_calls == ["/scans/finetuned"], (
            "uppercase Y dispatched the kill exactly like y"
        )
        assert not app._exit, "uppercase Y kills the sweep, never the console"


# =====================================================================
# 261018-rze — the cadence render gates' pins (steady-tick silence)
# =====================================================================

def _cadence_gate_fake() -> FakeMonitorService:
    """The render-gate pin fixture: ONE running root (scripted stats +
    progress — deterministic, zero wall-clock reads inside a render) plus
    one finished History row, enough surface for every pin (cards, tabs,
    both focus branches)."""
    return FakeMonitorService(
        scans=[ScanResult(sweeps=(
            _summary("finetuned", SWEEP_RUNNING, done=3, total=10,
                     mtime=2.0),
            _summary("older-run", SWEEP_FINISHED, done=2, total=2,
                     mtime=1.0),
        ), watermarks={})],
        cells={"/scans/finetuned": (
            _row("plant-dnamamba-6mer", "GUE__emp_H3",
                 {42: CELL_RUNNING}),)},
        stats={"/scans/finetuned": _stats(
            done=3, total=10,
            current=_current("plant-dnamamba-6mer", "GUE__emp_H3", 42))},
        progress={
            ("plant-dnamamba-6mer", "GUE__emp_H3"): CellProgress(
                step=300, max_steps=1000, percent=30)},
    )


def _spy(widget, method_name: str):
    """A counting spy over one widget method (wraps the bound original —
    the plan's mock.patch.object(wraps=...) idiom; the caller stops the
    patcher, the mock keeps its count)."""
    patcher = mock.patch.object(
        widget, method_name, wraps=getattr(widget, method_name))
    return patcher, patcher.start()


async def test_steady_tick_performs_zero_widget_writes():
    """261018-rze (the maintainer's 2026-10-18 19:57 flicker report): a
    steady tick over UNCHANGED data performs ZERO widget writes — no
    ListView rebuild, no tab Label update, no scan-note update, no card
    Label update, no focus call — and the ListItem identity survives
    (the operator's cursor identity never resets)."""
    app = _app(monitor=_cadence_gate_fake())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        cards_list = screen.query_one("#mon-cards", ListView)
        item = cards_list.children[0]
        spies = {
            "ListView clear": _spy(cards_list, "clear"),
            "running tab update": _spy(
                screen.query_one("#mon-tab-running", Label), "update"),
            "history tab update": _spy(
                screen.query_one("#mon-tab-history", Label), "update"),
            "scan-note update": _spy(
                screen.query_one("#mon-scanning-note", Static), "update"),
            "cards focus": _spy(cards_list, "focus"),
        }
        spies.update({
            f"card label {index} update": _spy(label, "update")
            for index, label in enumerate(item.query(Label))})
        try:
            # the steady tick: the cadence handlers land in exactly this
            # pair over unchanged caches
            screen._render_all()
            screen._focus_active()
            for name, (_patcher, mocked) in spies.items():
                assert mocked.call_count == 0, (
                    f"a steady tick performed a {name} — the flicker is "
                    "back")
        finally:
            for patcher, _mocked in spies.values():
                patcher.stop()
        assert cards_list.children[0] is item, (
            "the ListItem identity survives every steady tick")


async def test_progress_change_updates_card_labels_in_place():
    """261018-rze (c): a tick with CHANGED progress updates ONLY the
    affected card's Label content in place — the ListItem objects and
    the ListView's index are untouched (the clear spy stays at zero:
    content changed, structure did not). The honest path drives it: the
    fake's scripted stats advance and one frontier tick propagates them
    through the worker -> message -> render chain."""
    monitor = _cadence_gate_fake()
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        cards_list = screen.query_one("#mon-cards", ListView)
        item = cards_list.children[0]
        index_before = cards_list.index
        patcher, clear_mock = _spy(cards_list, "clear")
        try:
            monitor._stats["/scans/finetuned"] = _stats(
                done=4, total=10,
                current=_current("plant-dnamamba-6mer", "GUE__emp_H3", 42))
            screen._tick_frontier()
            await _settle(pilot, app)
        finally:
            patcher.stop()
        strip_line = _card_texts(screen, "mon-card-strip")[0]
        assert "4/10" in strip_line, (
            "the changed fraction paints (the in-place update landed)")
        assert clear_mock.call_count == 0, (
            "a content-only change must never rebuild the list")
        assert cards_list.children[0] is item, (
            "the ListItem object is the same one (updated, not rebuilt)")
        assert cards_list.index == index_before, (
            "the operator's cursor index is untouched")


async def test_render_all_inert_under_modal_and_resumes_after():
    """261018-rze (e): while any modal is stacked above the monitor, a
    cadence render writes NOTHING beneath it (the base surface stays
    still under the modal); the tick after dismissal refreshes normally
    (a changed stat lands)."""
    class _DummyModal(ModalScreen):
        """The minimal stacked screen — the suppression proof needs any
        modal above the monitor, content irrelevant."""

        def compose(self):
            yield Static("dummy")

    app = _app(monitor=_cadence_gate_fake())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        cards_list = screen.query_one("#mon-cards", ListView)
        item = cards_list.children[0]
        app.push_screen(_DummyModal())
        await pilot.pause()
        assert app.screen is not screen, "the modal is stacked above"
        spies = {
            "ListView clear": _spy(cards_list, "clear"),
            "running tab update": _spy(
                screen.query_one("#mon-tab-running", Label), "update"),
            "history tab update": _spy(
                screen.query_one("#mon-tab-history", Label), "update"),
        }
        spies.update({
            f"card label {index} update": _spy(label, "update")
            for index, label in enumerate(item.query(Label))})
        try:
            screen._render_all()
            for name, (_patcher, mocked) in spies.items():
                assert mocked.call_count == 0, (
                    f"the base pass fired beneath the modal: {name}")
        finally:
            for patcher, _mocked in spies.values():
                patcher.stop()
        # dismissal: the next tick refreshes — a changed stat lands
        app.pop_screen()
        await pilot.pause()
        screen._root_stats["/scans/finetuned"] = _stats(
            done=5, total=10,
            current=_current("plant-dnamamba-6mer", "GUE__emp_H3", 42))
        screen._render_all()
        assert "5/10" in _card_texts(screen, "mon-card-strip")[0], (
            "the tick after dismissal refreshes the base surface")


async def test_focus_active_noops_when_target_already_focused():
    """261018-rze (d): _focus_active skips the .focus() call when the
    intended target already holds focus (a steady tick's steal-back on
    the focused widget was pure churn) but still re-applies focus after
    it was lost — BOTH branches (the cards ListView and the History
    DataTable)."""
    app = _app(monitor=_cadence_gate_fake())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        cards_list = screen.query_one("#mon-cards", ListView)
        assert screen.focused is cards_list
        patcher, focus_mock = _spy(cards_list, "focus")
        try:
            screen._focus_active()
            assert focus_mock.call_count == 0, (
                "no focus call when the cards list already holds focus")
            screen.set_focus(None)
            screen._focus_active()
            assert focus_mock.call_count == 1, (
                "focus is re-applied after it was lost (AUTO_FOCUS "
                "steal-back preserved)")
            await pilot.pause()   # focus() lands via call_later
            assert screen.focused is cards_list
        finally:
            patcher.stop()

        # the History branch mirrors: switch to the populated tab
        # (the card carries a group -> tab, never the arrow)
        await pilot.press("tab")
        await pilot.pause()
        history_table = screen.query_one("#mon-history", DataTable)
        assert screen.focused is history_table
        patcher, focus_mock = _spy(history_table, "focus")
        try:
            screen._focus_active()
            assert focus_mock.call_count == 0, (
                "no focus call when the history table already holds focus")
            screen.set_focus(None)
            screen._focus_active()
            assert focus_mock.call_count == 1
            await pilot.pause()   # focus() lands via call_later
            assert screen.focused is history_table
        finally:
            patcher.stop()




