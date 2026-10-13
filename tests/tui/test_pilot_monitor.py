"""
Tier-2 Pilot suite for the monitor screen (Phase 11, 11-07; menu slot 5,
D-03/D-09/D-13, MON-01..05 over the 11-04 scanner service).

Pins the slot-5 screen and its app/nav wiring against the REAL
``DnallmMarkTui`` with constructor-injected deterministic fakes (no real
filesystem scan, no real registry read, no real subprocess, no real
sleep — the D-03 discipline; the cadence is proven by directly invoking
the interval callbacks plus fake call counters, never by sleeping):

- Task 1 (the shell): the stacked regions compose at 120x40 AND 80x24;
  the discovered pane renders the three sweep states with counts + the
  progress-bar grammar + the unknown-total degradation; the cell table
  renders per-seed glyphs (incl. the resume marker and curve
  mini-counts); the stats-line variants; the resume note; the cadence
  dispatches workers and stops on unmount; zero Chinese literals;
- Task 2 (interactions): attach moves the marker and rebinds; the [a]
  path modal (valid/invalid); the cell detail; the [f] failures modal
  with the gated re-run; the [t] log tail with tee/no-tee variants; the
  [r] rescan toast; the 68-char-key backstop;
- Task 3 (integration + degradation): the D-13 auto-nav, the extended
  q-intercept predicate, the degradation sweep, the responsiveness
  proof while a scan blocks.
"""

import re
from pathlib import Path

from rich.text import Text
from textual.widgets import DataTable, Label, RichLog, Static

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
    CELL_QUEUED,
    CELL_RUNNING,
    CELL_SKIPPED,
    ETA_NONE,
    ETA_PENDING,
    ETA_POINT,
    SWEEP_ARTIFACTS_ONLY,
    SWEEP_FINISHED,
    SWEEP_RUNNING,
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
    MON_CELLS_EMPTY,
    MON_CELLS_TITLE,
    MON_DISCOVERED_EMPTY,
    MON_DISCOVERED_TITLE,
    MON_ETA_PENDING,
    MON_FAILURES_EMPTY,
    MON_FRACTION_LINE,
    MON_RESUME_NOTE,
    MON_SCAN_NOTE,
    MON_SCREEN_TITLE,
    MON_STATE_ARTIFACTS_SWEEP,
    MON_STATE_DONE,
    MON_STATE_FINISHED_SWEEP,
    MON_STATE_RUNNING_SWEEP,
    MON_STATS_LINE,
    MON_STATS_LINE_NO_CURRENT,
    MON_STATS_LINE_UNKNOWN_TOTAL,
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

def _summary(root, state, done=None, total=None):
    """One SweepSummary fixture (root name -> tmp-ish path string)."""
    return SweepSummary(
        root=Path(f"/scans/{root}"), state=state,
        done=done if done is not None else 0,
        total=total, newest_mtime=None)


def _eta(mode, point=None, lo=None, hi=None):
    return EtaEstimate(mode, point, lo, hi)


def _stats(done=0, total=None, current=None, elapsed=None, eta=None):
    return SweepStats(
        done=done, total=total, current=current,
        elapsed_seconds=elapsed,
        eta=eta if eta is not None else _eta(ETA_NONE))


def _current(model, task, seed):
    return CurrentCell(model=model, task=task, seed=seed)


def _row(model, task, seeds, fractions=None):
    """One CellRow fixture; seeds maps seed -> machine state; fractions
    maps seed -> tuple of (frac_name, state) pairs."""
    cells = []
    for seed, state in seeds.items():
        cells.append(CellSeed(
            seed=seed, state=state,
            fraction_states=fractions.get(seed) if fractions else None))
    return CellRow(model=model, task=task, seeds=tuple(cells))


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
                 rerun_lanes=None):
        self._scans = list(scans) if scans else []
        self._cells = dict(cells or {})
        self._stats = dict(stats or {})
        self._frontiers = dict(frontiers or {})
        self._failures = dict(failures or {})
        self._tails = dict(tails or {})
        self._resume = dict(resume_counts or {})
        self._scales = dict(scales or {})
        self._valid_roots = set(valid_roots)
        self._manual_roundtrip = (
            manual_roundtrip if manual_roundtrip is not None else [])
        self._records = dict(records or {})
        self._rerun_lanes = dict(rerun_lanes or {})
        self.full_calls = []
        self.frontier_calls = []
        self.cells_calls = []
        self.stats_calls = []
        self.failures_calls = []
        self.tail_calls = []
        self.record_calls = []
        self.rerun_lane_calls = []
        self.added_roots = []

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
        return self._failures.get(str(root), ())

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


class FakeMonitorLauncher:
    """The launcher-seam fake for the monitor screen (recorded)."""

    def __init__(self, preflight=None, live=(), tee=None,
                 rerun_outcomes=None):
        self._preflight = (preflight if preflight is not None
                           else EnvPreflight(
                               can_launch=True, reasons=(),
                               failed_kernels=()))
        self._live = tuple(live)
        self._tee = dict(tee or {})
        self._rerun_outcomes = (
            list(rerun_outcomes) if rerun_outcomes else None)
        self.env_calls = 0
        self.rerun_calls = []

    def env_preflight(self, kernels=None):
        self.env_calls += 1
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

    def phrase_matches(self, typed, output_root):
        return typed == Path(str(output_root)).name

    def live_sweeps(self):
        return self._live

    def tee_path_for(self, root):
        return self._tee.get(str(root))


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
        _summary("finetuned", SWEEP_RUNNING, done=12, total=36),
        _summary("finetuned-e2e-rerun", SWEEP_FINISHED,
                 done=9300, total=9300),
        _summary("seed-9527-artifacts", SWEEP_ARTIFACTS_ONLY, done=5),
    ), watermarks={})


# =====================================================================
# Task 1 — the screen shell (both grids, discovered pane, cells, stats)
# =====================================================================

async def test_screen_composes_stacked_regions_at_both_grids():
    """The stacked regions compose at 120x40 AND 80x24 with both bars."""
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
        discovered = screen.query_one("#mon-discovered-region")
        cells = screen.query_one("#mon-cells-region")
        assert discovered.region.height >= 4, (
            "the discovered region is fixed-height (title+header+rows)")
        assert cells.region.height >= 3, "the cell region takes the flex"
        assert screen.query_one("#mon-stats-line", Label) is not None

    monitor = FakeMonitorService(scans=[_three_state_scan()])
    app = _app(monitor=monitor)
    async with app.run_test(size=(80, 24)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        table = screen.query_one("#mon-discovered", DataTable)
        column_keys = {str(key.value) for key in table.columns}
        assert "scale" not in column_keys, (
            "the 80-col degradation drops the scale column")
        assert _label_text(screen, "#mon-screen-title") == MON_SCREEN_TITLE


async def test_discovered_pane_renders_three_states_and_counts():
    """The three D-03 states render glyph-first with the count title."""
    monitor = FakeMonitorService(scans=[_three_state_scan()])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert _label_text(screen, "#mon-discovered-title") == (
            MON_DISCOVERED_TITLE.format(n=3))
        table = screen.query_one("#mon-discovered", DataTable)
        assert table.row_count == 3, "one row per discovered sweep"
        assert _table_text(table, "/scans/finetuned",
                           "state") == MON_STATE_RUNNING_SWEEP
        assert _table_text(table, "/scans/finetuned-e2e-rerun",
                           "state") == MON_STATE_FINISHED_SWEEP
        assert _table_text(table, "/scans/seed-9527-artifacts",
                           "state") == MON_STATE_ARTIFACTS_SWEEP
        assert _table_text(table, "/scans/finetuned", "root") == (
            "finetuned")


async def test_discovered_progress_bar_grammar_and_unknown_total():
    """The phase-10 progress grammar verbatim: {done}/{total} + the
    10-cell bar on running rows; the unknown-total degradation."""
    monitor = FakeMonitorService(scans=[_three_state_scan()])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        table = app.screen.query_one("#mon-discovered", DataTable)
        running = _table_text(table, "/scans/finetuned", "progress")
        assert "12/36" in running
        assert "█" in running and "·" in running, (
            "the 10-cell bar rides the fraction"
        )
        assert running.count("█") == 3, (
            "12/36 rounds to 3 filled cells of 10")
        finished = _table_text(table, "/scans/finetuned-e2e-rerun",
                               "progress")
        assert "9300/9300" in finished
        assert "█" not in finished, "finished rows carry no bar"
        unknown = _table_text(table, "/scans/seed-9527-artifacts",
                              "progress")
        assert unknown == MON_TOTAL_UNKNOWN, (
            "the unknown-total row renders the designed copy, never a "
            "fabricated fraction"
        )


async def test_cell_table_per_seed_glyphs_and_curve_minicounts():
    """Per-seed glyphs incl. the resume marker; curve mini-counts."""
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=3, total=36),), watermarks={})],
        cells={"/scans/finetuned": (
            _row("plant-dnamamba-6mer", "GUE__emp_H3",
                 {42: CELL_RUNNING, 43: CELL_QUEUED, 44: CELL_QUEUED}),
            _row("plant-dnabert-6mer", "GUE__emp_H3",
                 {42: CELL_COMPLETED, 43: CELL_SKIPPED, 44: CELL_COMPLETED}),
            _row("plant-dnabert-6mer", "mouse__DMS",
                 {42: CELL_FAILED, 43: CELL_FAILED, 44: CELL_FAILED}),
        )},
        stats={"/scans/finetuned": _stats(
            done=3, total=36,
            current=_current("plant-dnamamba-6mer", "GUE__emp_H3", 42),
            elapsed=4360.0,
            eta=_eta(ETA_POINT, point=7560.0))},
        resume_counts={"/scans/finetuned": 1},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        screen.attach("/scans/finetuned")
        await _settle(pilot, app)
        table = screen.query_one("#mon-cells", DataTable)
        assert table.row_count == 3
        row = "plant-dnabert-6mer__GUE__emp_H3"
        assert _table_text(table, row, "seed_42").startswith("✓")
        assert _table_text(table, row, "seed_43").startswith("⊘"), (
            "the resume marker renders the distinct skipped glyph"
        )
        assert _table_text(table, "plant-dnabert-6mer__mouse__DMS",
                           "seed_42").startswith("✗")
        assert _table_text(table, "plant-dnamamba-6mer__GUE__emp_H3",
                           "seed_42").startswith("⠋")
        assert _table_text(table, "plant-dnamamba-6mer__GUE__emp_H3",
                           "seed_43").startswith("◌")
        # the words ride the wide cells (the glyph+word redundancy)
        assert MON_STATE_DONE.split(" ")[1] in _table_text(
            table, row, "seed_42")
        # the resume note rides the cells title row (standing chrome)
        assert MON_RESUME_NOTE.format(n=1) in _label_text(
            screen, "#mon-resume-note")
        assert _label_text(screen, "#mon-cells-title") == (
            MON_CELLS_TITLE.format(root="finetuned"))


async def test_cell_table_curve_seed_renders_mini_counts():
    """A curve seed cell renders the folded glyph + {done}/{total}."""
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=1, total=9),), watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_RUNNING}, fractions={
                42: (("frac_0.3", CELL_COMPLETED),
                     ("frac_0.6", CELL_RUNNING),
                     ("frac_1.0", CELL_QUEUED)),
            }),
        )},
        stats={"/scans/finetuned": _stats(
            done=1, total=9, elapsed=100.0, eta=_eta(ETA_PENDING))},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        app.screen.attach("/scans/finetuned")
        await _settle(pilot, app)
        table = app.screen.query_one("#mon-cells", DataTable)
        cell = _table_text(table, "model-a__task-1", "seed_42")
        assert cell.startswith("⠋"), (
            "the curve seed folds to the running glyph")
        assert "1/3" in cell, (
            "the mini-counts carry the fraction done/total"
        )


async def test_stats_line_variants():
    """The three D-17 stats-line variants render verbatim."""
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=5, total=36),), watermarks={})],
        cells={"/scans/finetuned": ()},
        stats={"/scans/finetuned": _stats(
            done=5, total=36,
            current=_current("model-a", "task-1", 42),
            elapsed=4360.0, eta=_eta(ETA_POINT, point=7560.0))},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        app.screen.attach("/scans/finetuned")
        await _settle(pilot, app)
        line = _label_text(app.screen, "#mon-stats-line")
        assert line == MON_STATS_LINE.format(
            done=5, total=36,
            model="model-a", task="task-1", seed=42,
            elapsed="1:12:40", eta="2.1h"), (
            f"the full stats line renders verbatim (is {line!r})"
        )

    # the 80-col variant drops the current segment
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=5, total=36),), watermarks={})],
        cells={"/scans/finetuned": ()},
        stats={"/scans/finetuned": _stats(
            done=5, total=36,
            current=_current("model-a", "task-1", 42),
            elapsed=4360.0, eta=_eta(ETA_POINT, point=7560.0))},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(80, 24)) as pilot:
        await _open_monitor(pilot, app)
        app.screen.attach("/scans/finetuned")
        await _settle(pilot, app)
        line = _label_text(app.screen, "#mon-stats-line")
        assert line == MON_STATS_LINE_NO_CURRENT.format(
            done=5, total=36, elapsed="1:12:40", eta="2.1h")

    # the unknown-total degradation (CLI-launched, no manifest yet)
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=2),), watermarks={})],
        cells={"/scans/finetuned": ()},
        stats={"/scans/finetuned": _stats(
            done=2, total=None, elapsed=100.0, eta=_eta(ETA_NONE))},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        app.screen.attach("/scans/finetuned")
        await _settle(pilot, app)
        line = _label_text(app.screen, "#mon-stats-line")
        assert line == MON_STATS_LINE_UNKNOWN_TOTAL.format(
            done=2, elapsed="0:01:40"), (
            f"the unknown-total variant renders verbatim (is {line!r})"
        )


async def test_stats_line_pending_eta_degradation():
    """Before the first completion the ETA renders the pending copy."""
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=0, total=36),), watermarks={})],
        cells={"/scans/finetuned": ()},
        stats={"/scans/finetuned": _stats(
            done=0, total=36, elapsed=60.0, eta=_eta(ETA_PENDING))},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        app.screen.attach("/scans/finetuned")
        await _settle(pilot, app)
        assert MON_ETA_PENDING in _label_text(app.screen, "#mon-stats-line")


async def test_empty_states_are_designed_rows():
    """No sweeps discovered: both panes render their designed empty
    copy and the cadence keeps running."""
    monitor = FakeMonitorService(scans=[ScanResult(sweeps=(), watermarks={})])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert _label_text(screen, "#mon-discovered-title") == (
            MON_DISCOVERED_TITLE.format(n=0))
        discovered = screen.query_one("#mon-discovered", DataTable)
        assert _table_text(discovered, "__empty__",
                           "state") == MON_DISCOVERED_EMPTY
        cells = screen.query_one("#mon-cells", DataTable)
        assert _table_text(cells, "__empty__", "model") == MON_CELLS_EMPTY
        # the cadence stays armed
        screen._tick_full()
        await _settle(pilot, app)
        assert len(monitor.full_calls) >= 2


async def test_cadence_dispatches_workers_and_stops_on_unmount():
    """D-09 cadence: the mount kick + the interval callbacks dispatch
    the exclusive workers (fake counters prove the chain — never real
    sleeps); switching away leaves no zombie workers."""
    monitor = FakeMonitorService(
        scans=[_three_state_scan()],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_RUNNING}),)},
        stats={"/scans/finetuned": _stats(
            done=1, total=36, elapsed=10.0, eta=_eta(ETA_NONE))},
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

        screen.attach("/scans/finetuned")
        await _settle(pilot, app)
        before_frontier = len(monitor.frontier_calls)
        screen._tick_frontier()   # the interval's callback, invoked directly
        await _settle(pilot, app)
        assert len(monitor.frontier_calls) > before_frontier, (
            "the frontier tick dispatched the scan worker (the fake "
            "counter is the cadence proof)"
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
# Task 2 — interactions (attach, [a], cell detail, [f], [t], [r])
# =====================================================================

async def test_attach_via_enter_moves_marker_and_rebinds():
    """Enter on a discovered row attaches: the marker moves and the
    stats/cells rebind to that root (fake posts per-root data)."""
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(
            _summary("root-a", SWEEP_RUNNING, done=1, total=9),
            _summary("root-b", SWEEP_RUNNING, done=7, total=9),
        ), watermarks={})],
        cells={
            "/scans/root-a": (
                _row("model-a", "task-1", {42: CELL_RUNNING}),),
            "/scans/root-b": (
                _row("model-b", "task-2", {42: CELL_COMPLETED}),),
        },
        stats={
            "/scans/root-a": _stats(
                done=1, total=9, elapsed=60.0, eta=_eta(ETA_NONE)),
            "/scans/root-b": _stats(
                done=7, total=9, elapsed=600.0, eta=_eta(ETA_NONE)),
        },
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        assert screen.focused.id == "mon-discovered"
        await pilot.press("enter")   # row 0: root-a
        await _settle(pilot, app)
        table = screen.query_one("#mon-discovered", DataTable)
        assert _table_text(table, "/scans/root-a", "state").startswith("◆")
        assert not _table_text(table, "/scans/root-b",
                               "state").startswith("◆")
        assert "model-a" in _table_text(
            screen.query_one("#mon-cells", DataTable),
            "model-a__task-1", "model")
        assert "60" in _label_text(screen, "#mon-stats-line") or (
            "0:01:00" in _label_text(screen, "#mon-stats-line"))

        # down + enter: the marker MOVES to root-b, everything rebinds
        await pilot.press("down")
        await pilot.press("enter")
        await _settle(pilot, app)
        assert not _table_text(table, "/scans/root-a",
                               "state").startswith("◆")
        assert _table_text(table, "/scans/root-b", "state").startswith("◆")
        assert "model-b" in _table_text(
            screen.query_one("#mon-cells", DataTable),
            "model-b__task-2", "model")
        assert "0:10:00" in _label_text(screen, "#mon-stats-line")
        assert MON_ATTACHED_TOAST not in _toast_messages(app) or any(
            "root-b" in message for message in _toast_messages(app))


async def test_attach_path_invalid_keeps_modal_never_attaches():
    """[a] with an invalid path: the toast copy renders INSIDE the
    modal (never silent), the root is never added, never attached."""
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
        # never attached, never persisted (the fake records the ATTEMPT;
        # the predicate refused it — add_manual_root returned False)
        assert monitor.added_roots == ["/no/such/root"]
        # the screen behind never attached
        await pilot.press("escape")
        await pilot.pause()
        assert app.screen._attached_root is None
        table = app.screen.query_one("#mon-discovered", DataTable)
        assert not any(
            _table_text(table, str(row_key), "state").startswith("◆")
            for row_key in ("/scans/finetuned",
                            "/scans/finetuned-e2e-rerun",
                            "/scans/seed-9527-artifacts"))


async def test_attach_path_valid_adds_attaches_and_persists():
    """[a] with a valid root: add_manual_root called, the toast fires,
    and the root attaches (the fake round-trip)."""
    from tui.screens.selection import PathInputModal

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(), watermarks={})],
        manual_roundtrip=[True],
        cells={"/scans/manual-root": (
            _row("model-x", "task-x", {42: CELL_COMPLETED}),)},
        stats={"/scans/manual-root": _stats(
            done=1, total=1, elapsed=5.0, eta=_eta(ETA_NONE))},
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
        assert str(app.screen._attached_root) == "/scans/manual-root"


async def test_cell_detail_renders_states_fractions_record_verbatim():
    """The cell-detail modal: full keys, per-seed states, fraction
    lines, and the run_record fields VERBATIM (data, never elided)."""
    from tui.screens.monitor import CellDetailModal

    record = {
        "status": "completed", "started_at": "2026-10-13T01:00:00+00:00",
        "finished_at": "2026-10-13T01:01:05+00:00",
        "error": "", "peft": "none", "config_variant": "none",
        "metrics": {"accuracy": 0.9123},
    }
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=1, total=3),), watermarks={})],
        cells={"/scans/finetuned": (
            _row("plant-dnabert-6mer", "GUE__emp_H3",
                 {42: CELL_RUNNING}, fractions={
                     42: (("frac_0.3", CELL_COMPLETED),
                          ("frac_0.6", CELL_QUEUED)),
                 }),
        )},
        stats={"/scans/finetuned": _stats(
            done=1, total=3, elapsed=30.0, eta=_eta(ETA_NONE))},
        records={
            ("/scans/finetuned", "plant-dnabert-6mer", "GUE__emp_H3",
             42): record,
        },
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        screen.attach("/scans/finetuned")
        await _settle(pilot, app)
        screen.query_one("#mon-cells", DataTable).focus()
        await pilot.press("enter")
        await _settle(pilot, app)
        assert isinstance(app.screen, CellDetailModal)
        await pilot.pause()   # the modal's on_mount writes the title
        joined = "\n".join(line.text for line
                           in app.screen.query_one(
                               "#mon-celldetail-log", RichLog).lines)
        assert "plant-dnabert-6mer" in str(
            app.screen.query_one("#mon-celldetail-box").border_title)
        assert "GUE__emp_H3" in str(
            app.screen.query_one("#mon-celldetail-box").border_title)
        assert "s42" in joined
        assert MON_FRACTION_LINE.format(
            fraction="0.3", state=MON_STATE_DONE) in joined
        for field_name, value in record.items():
            assert f"{field_name}: {value}" in joined, (
                f"the record field {field_name} renders verbatim")


async def test_failures_modal_rows_drill_and_empty_state():
    """[f]: one row per failure, enter drills the verbatim error, and
    the empty list renders the designed zero copy."""
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
            "finetuned", SWEEP_RUNNING, done=3, total=5),), watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_FAILED}),)},
        stats={"/scans/finetuned": _stats(
            done=3, total=5, elapsed=60.0, eta=_eta(ETA_NONE))},
        failures={"/scans/finetuned": failures},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        app.screen.attach("/scans/finetuned")
        await _settle(pilot, app)
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

    # the empty list renders the designed zero copy
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_FINISHED, done=5, total=5),), watermarks={})],
        failures={"/scans/finetuned": ()},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        app.screen.attach("/scans/finetuned")
        await _settle(pilot, app)
        await pilot.press("f")
        await _settle(pilot, app)
        assert isinstance(app.screen, FailuresModal)
        table = app.screen.query_one("#mon-failures-table", DataTable)
        assert _table_text(table, "__empty__", "model") == (
            MON_FAILURES_EMPTY)


async def test_rerun_confirm_routes_launch_from_failures_and_attaches():
    """[f] -> r -> confirm: launch_from_failures called with the root's
    failures file + the sweep's seeds; the toast fires and the re-run
    sweep auto-attaches (T-11-07-03: the same pipeline)."""
    from tui.screens.monitor import FailuresModal
    from tui.screens.selection import ConfirmModal
    from tui.strings import MON_RERUN_CONFIRM, MON_RERUN_TOAST

    failures = (FailureRow(model="model-a", task="task-1", seed=42,
                           error="boom", output_dir="/x"),)
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=3, total=5),), watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_FAILED, 43: CELL_QUEUED}),)},
        stats={"/scans/finetuned": _stats(
            done=3, total=5, elapsed=60.0, eta=_eta(ETA_NONE))},
        failures={"/scans/finetuned": failures},
    )
    launcher = FakeMonitorLauncher()
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        app.screen.attach("/scans/finetuned")
        await _settle(pilot, app)
        await pilot.press("f")
        await _settle(pilot, app)
        assert isinstance(app.screen, FailuresModal)
        await pilot.press("r")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmModal), (
            "the re-run always sits behind its own confirm"
        )
        assert MON_RERUN_CONFIRM.format(n=1) in str(
            app.screen.query_one(Static).content)
        await pilot.press("enter")   # confirm
        await _settle(pilot, app)
        assert launcher.env_calls == 1, "the env preflight re-entered"
        assert len(launcher.rerun_calls) == 1
        failures_path, seeds, root, _peft, _variant, phrase = (
            launcher.rerun_calls[0])
        assert failures_path == "/scans/finetuned/sweep_failures.json"
        assert seeds == (42, 43), "the sweep's own seeds fan out"
        assert root == "/scans/finetuned"
        assert phrase is None, "an ordinary partial re-run carries no phrase"
        assert MON_RERUN_TOAST.format(
            cells="—", root="finetuned") in _toast_messages(app)
        assert str(app.screen._attached_root) == "/scans/finetuned"


async def test_note_launch_cells_zero_clears_stale_expected_total():
    """WR-02: the re-run's note_launch(root, 0) clears a prior launch's
    stale expected total at the same root — the next stats call threads
    expected_total=None (the honest unknown), never the prior sweep's
    number; a real plan (cells > 0) still injects."""
    monitor = FakeMonitorService(scans=[ScanResult(sweeps=(
        _summary("finetuned", SWEEP_RUNNING, done=1, total=2),),
        watermarks={})])
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        screen.note_launch("/scans/finetuned", 9300)
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
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=3, total=5),), watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a+lora", "task-1", {42: CELL_FAILED, 43: CELL_QUEUED}),)},
        stats={"/scans/finetuned": _stats(done=3, total=5)},
        failures={"/scans/finetuned": failures},
        rerun_lanes={"/scans/finetuned": ("lora", "none")},
    )
    launcher = FakeMonitorLauncher()
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        app.screen.attach("/scans/finetuned")
        await _settle(pilot, app)
        await pilot.press("f")
        await _settle(pilot, app)
        assert isinstance(app.screen, FailuresModal)
        await pilot.press("r")
        await pilot.pause()
        await pilot.press("enter")   # confirm the re-run
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
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=1, total=2),), watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_FAILED}),)},
        stats={"/scans/finetuned": _stats(
            done=1, total=2, elapsed=60.0, eta=_eta(ETA_NONE))},
        failures={"/scans/finetuned": failures},
    )
    launcher = FakeMonitorLauncher(preflight=EnvPreflight(
        can_launch=False,
        reasons=("torch: import failed", "cuda: no device"),
        failed_kernels=("torch", "cuda")))
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        app.screen.attach("/scans/finetuned")
        await _settle(pilot, app)
        await pilot.press("f")
        await _settle(pilot, app)
        assert isinstance(app.screen, FailuresModal)
        await pilot.press("r")
        await pilot.press("enter")   # confirm the re-run
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
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=3, total=9),), watermarks={})],
        cells={"/scans/finetuned": (
            _row(f"model-{index}", "task-1",
                 {42: CELL_FAILED, 43: CELL_FAILED, 44: CELL_FAILED})
            for index in range(3))},
        stats={"/scans/finetuned": _stats(done=3, total=9)},
        failures={"/scans/finetuned": failures},
    )
    launcher = FakeMonitorLauncher(rerun_outcomes=[
        GateRefusal(stage="phrase", expected="finetuned"),
    ])
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        app.screen.attach("/scans/finetuned")
        await _settle(pilot, app)
        await pilot.press("f")
        await _settle(pilot, app)
        assert isinstance(app.screen, FailuresModal)
        await pilot.press("r")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmModal)
        await pilot.press("enter")   # confirm the re-run
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
        await pilot.press("enter")   # the exact match confirms
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
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=1, total=2),), watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_FAILED}),)},
        stats={"/scans/finetuned": _stats(done=1, total=2)},
        failures={"/scans/finetuned": failures},
    )
    launcher = FakeMonitorLauncher(rerun_outcomes=[GateRefusal(
        stage="problems",
        problems=(("official_keys",
                   "unreadable or shape-invalid: pipeline/models_info.json"),),
    )])
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        app.screen.attach("/scans/finetuned")
        await _settle(pilot, app)
        await pilot.press("f")
        await _settle(pilot, app)
        await pilot.press("r")
        await pilot.pause()
        await pilot.press("enter")   # confirm the re-run
        await _settle(pilot, app)
        toasts = _toast_messages(app)
        assert any(
            "official_keys" in message
            and "unreadable or shape-invalid" in message
            for message in toasts), toasts
        assert len(launcher.rerun_calls) == 1, "no second attempt"


async def test_log_tail_renders_lines_and_tee_line():
    """[t] with a tee: the bounded tail renders + the dim tee line
    names the file (D-10)."""
    from tui.screens.monitor import LogTailModal
    from tui.strings import MON_LOG_TEE_LINE

    tee_path = "/state/logs/sweep_20261013_finetuned.log"
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=1, total=2),), watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_RUNNING}),)},
        stats={"/scans/finetuned": _stats(
            done=1, total=2, elapsed=60.0, eta=_eta(ETA_NONE))},
        tails={tee_path: ("[01:00:05] epoch 1", "[01:00:40] done")},
    )
    launcher = FakeMonitorLauncher(tee={"/scans/finetuned": tee_path})
    app = _app(monitor=monitor, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        app.screen.attach("/scans/finetuned")
        await _settle(pilot, app)
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
            "finetuned", SWEEP_RUNNING, done=1, total=2),), watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_RUNNING}),)},
        stats={"/scans/finetuned": _stats(
            done=1, total=2, elapsed=60.0, eta=_eta(ETA_NONE))},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        app.screen.attach("/scans/finetuned")
        await _settle(pilot, app)
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


async def test_long_keys_backstop_both_tables():
    """The 68-char-key lesson: long model/task keys truncate in-cell
    (never breaking the grid) and the full key rides the detail."""
    from tui.screens.monitor import CellDetailModal

    long_model = ("plant-dnabert-6mer-with-a-very-long-custom-alias-name"
                  "-that-exceeds-any-column")
    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(
            _summary("finetuned-a-really-long-root-name-here",
                     SWEEP_RUNNING, done=1, total=2),), watermarks={})],
        cells={"/scans/finetuned-a-really-long-root-name-here": (
            _row(long_model, "GUE__emp_H3", {42: CELL_COMPLETED}),)},
        stats={"/scans/finetuned-a-really-long-root-name-here": _stats(
            done=1, total=2, elapsed=60.0, eta=_eta(ETA_NONE))},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        table = screen.query_one("#mon-discovered", DataTable)
        root_cell = _table_text(
            table, "/scans/finetuned-a-really-long-root-name-here",
            "root")
        assert root_cell == "finetuned-a-really-long-root-name-here"
        screen.attach("/scans/finetuned-a-really-long-root-name-here")
        await _settle(pilot, app)
        cells_table = screen.query_one("#mon-cells", DataTable)
        model_cell = _table_text(cells_table, f"{long_model}__GUE__emp_H3",
                                 "model")
        assert "…" in model_cell, (
            "the in-cell truncation carries the ellipsis (display-only)"
        )
        # the full key rides the detail (never elided)
        screen.query_one("#mon-cells", DataTable).focus()
        await pilot.press("enter")
        await _settle(pilot, app)
        assert isinstance(app.screen, CellDetailModal)
        assert long_model in str(
            app.screen.query_one("#mon-celldetail-box").border_title)


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
        table = app.screen.query_one("#mon-discovered", DataTable)
        assert table.row_count == 3, "the healthy first render landed"
        # a throwing full scan: the worker absorbs it; the rows stand
        monitor.full_scan_throws = True
        app.screen._tick_full()
        await _settle(pilot, app)
        assert isinstance(app.screen, MonitorScreen), (
            "a throwing scan never crashes the console"
        )
        assert app.screen.query_one(
            "#mon-discovered", DataTable).row_count == 3, (
            "the last-known-good render stands")


async def test_degradation_manifest_mid_write_stays_running():
    """A manifest missing mid-write: the running rules hold (no
    finished flip, unknown total) — the finished state requires the
    COMPLETE manifest."""
    monitor = FakeMonitorService(scans=[ScanResult(sweeps=(
        _summary("finetuned", SWEEP_RUNNING, done=2),
    ), watermarks={})] * 3)
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        table = app.screen.query_one("#mon-discovered", DataTable)
        assert _table_text(table, "/scans/finetuned",
                           "state") == MON_STATE_RUNNING_SWEEP
        assert _table_text(table, "/scans/finetuned",
                           "progress") == MON_TOTAL_UNKNOWN
        app.screen._tick_full()
        await _settle(pilot, app)
        assert _table_text(table, "/scans/finetuned",
                           "state") == MON_STATE_RUNNING_SWEEP, (
            "no manifest means no finished flip — the running rules hold"
        )


async def test_degradation_artifacts_only_never_running_glyph():
    """The prior-artifacts root renders the third state with the
    unknown total — never a fabricated running glyph or fraction."""
    monitor = FakeMonitorService(scans=[ScanResult(sweeps=(
        _summary("seed-9527-artifacts", SWEEP_ARTIFACTS_ONLY, done=5),
    ), watermarks={})] * 2)
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        table = app.screen.query_one("#mon-discovered", DataTable)
        state = _table_text(table, "/scans/seed-9527-artifacts", "state")
        assert state == MON_STATE_ARTIFACTS_SWEEP
        assert "●" not in state, "artifacts-only never renders running"
        assert _table_text(table, "/scans/seed-9527-artifacts",
                           "progress") == MON_TOTAL_UNKNOWN


async def test_degradation_attached_root_deleted_mid_monitor():
    """The attached root deleted mid-monitor: the scan skips it, the
    discovered row drops, the cell region returns to its empty state —
    no crash, no stale marker."""
    with_root = ScanResult(sweeps=(
        _summary("finetuned", SWEEP_RUNNING, done=1, total=4),
        _summary("other", SWEEP_FINISHED, done=2, total=2),
    ), watermarks={})
    monitor = FakeMonitorService(
        scans=[with_root, with_root])   # mount scan + the attach re-scan
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        screen = app.screen
        screen.attach("/scans/finetuned")
        await _settle(pilot, app)
        assert screen._attached_root is not None
        discovered = screen.query_one("#mon-discovered", DataTable)
        assert discovered.row_count == 2
        assert _table_text(discovered, "/scans/finetuned",
                           "state").startswith("◆")

        monitor._scans.append(ScanResult(sweeps=(
            _summary("other", SWEEP_FINISHED, done=2, total=2),
        ), watermarks={}))
        screen._tick_full()   # THIS scan drops the deleted root
        await _settle(pilot, app)
        assert isinstance(app.screen, MonitorScreen), "no crash"
        assert discovered.row_count == 1, "the deleted root's row dropped"
        assert screen._attached_root is None, "no stale attach"
        cells = screen.query_one("#mon-cells", DataTable)
        assert _table_text(cells, "__empty__", "model") == MON_CELLS_EMPTY
        assert _label_text(screen, "#mon-stats-line") == ""
        assert not _table_text(discovered, "/scans/other",
                               "state").startswith("◆"), (
            "no stale marker after the detach"
        )


async def test_degradation_min_size_guard_round_trip_with_open_modal():
    """An open monitor modal survives the below-min round trip (the
    app-level guard owns the behavior; the screen must not fight it)."""
    from tui.app import MinSizeScreen
    from tui.screens.monitor import FailuresModal

    monitor = FakeMonitorService(
        scans=[ScanResult(sweeps=(_summary(
            "finetuned", SWEEP_RUNNING, done=1, total=2),), watermarks={})],
        cells={"/scans/finetuned": (
            _row("model-a", "task-1", {42: CELL_FAILED}),)},
        stats={"/scans/finetuned": _stats(
            done=1, total=2, elapsed=60.0, eta=_eta(ETA_NONE))},
        failures={"/scans/finetuned": (
            FailureRow(model="model-a", task="task-1", seed=42,
                       error="boom", output_dir="/x"),)},
    )
    app = _app(monitor=monitor)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_monitor(pilot, app)
        app.screen.attach("/scans/finetuned")
        await _settle(pilot, app)
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

    gate = threading.Event()
    monitor = FakeMonitorService(scans=[_three_state_scan()])
    monitor.full_scan_gate = gate
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
