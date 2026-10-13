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
from textual.widgets import DataTable, Label, Static

import tui.screens.monitor as monitor_screen_module
from tui.app import DnallmMarkTui
from tui.screens.monitor import MonitorScreen
from tui.screens.nav import BottomBar, TopMenuBar
from tui.screens.selection import PresetMenu, SelectionData
from tui.services import registries as registries_service
from tui.services.download_queue import merge_presence
from tui.services.sweep_monitor import (
    CELL_COMPLETED,
    CELL_FAILED,
    CELL_QUEUED,
    CELL_RUNNING,
    CELL_SKIPPED,
    ETA_NONE,
    ETA_PENDING,
    ETA_POINT,
    ETA_RANGE,
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
from tui.services.sweep_launcher import (
    EnvPreflight,
    LaunchOutcome,
)
from tui.strings import (
    MON_CELLS_EMPTY,
    MON_CELLS_TITLE,
    MON_DISCOVERED_EMPTY,
    MON_DISCOVERED_TITLE,
    MON_ETA_PENDING,
    MON_ETA_UNKNOWN,
    MON_RESUME_NOTE,
    MON_SCAN_NOTE,
    MON_SCREEN_TITLE,
    MON_STATE_ARTIFACTS_SWEEP,
    MON_STATE_DONE,
    MON_STATE_FAILED,
    MON_STATE_FINISHED_SWEEP,
    MON_STATE_RUNNING,
    MON_STATE_RUNNING_SWEEP,
    MON_STATE_SKIPPED,
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
    _MON_MODULE_FILE,
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
                 valid_roots=(), manual_roundtrip=None):
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
        self.full_calls = []
        self.frontier_calls = []
        self.cells_calls = []
        self.stats_calls = []
        self.failures_calls = []
        self.tail_calls = []
        self.added_roots = []

    # ----- the scan surface -----

    def full_scan(self, prev_watermarks=None):
        self.full_calls.append(dict(prev_watermarks or {}))
        if not self._scans:
            return ScanResult(sweeps=(), watermarks={})
        return self._scans.pop(0)

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
                             peft="none", config_variant="none"):
        self.rerun_calls.append((str(failures_path), tuple(seeds),
                                 str(output_root), peft, config_variant))
        if self._rerun_outcomes:
            return self._rerun_outcomes.pop(0)
        return LaunchOutcome(
            spawned=True, root=str(output_root),
            tee_path="/state/logs/sweep_rerun.log", error=None)

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
