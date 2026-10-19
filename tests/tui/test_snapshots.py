"""
Snapshot goldens for the six canonical console screens — the FALLBACK
lane (Phase 12, 12-03; TEST-01/SC5, D-03/D-11).

Why the fallback lane (the plugin verdict, 12-RESEARCH Area 8)
----------------------------------------------------------------
``pytest-textual-snapshot>=1.1,<2`` is RESOLVER-BLOCKED against this
repo's committed floor: its exact ``syrupy==4.8.0`` pin requires
``pytest>=7.0.0,<9.0.0`` while the repo commits ``pytest>=9.1.1`` —

    error: No solution found when resolving dependencies
    cause: Because syrupy==4.8.0 depends on pytest>=7.0.0,<9.0.0 and
    pytest-textual-snapshot>=1.1.0 depends on syrupy==4.8.0, ...
    And because you require pytest>=9.1.1 ...

The community ``--no-deps`` workaround is FORBIDDEN (it would silently
pin pytest 8 under the committed floor); zero pyproject/uv.lock change
lands. Instead this module uses Textual core's own
``App.run_test(size=(120, 40))`` + ``App.export_screenshot()`` (SVG,
byte-deterministic across independent app instances — probe-verified on
textual 8.2.8 + pytest 9.1.1) and plain UTF-8 STRING EQUALITY against
committed SVG files. The comparison is honestly an SVG-text diff —
"pixel compare" at SVG fidelity; rasterizing (cairosvg) is NOT
sanctioned and no syrupy/jinja2 is ever imported.

The corpus (the frozen 9 — 12-UI-SPEC table + DCL-03)
-----------------------------------------------------
=========================  =====================================
Golden id                  Screen state
=========================  =====================================
env_check                  populated cache-hit boot (8 kernels) + the
                           five-row storage overview (261014-f4w)
selection_models           models view, 2 marks, filter 1/3
selection_datasets         datasets view (the m flip), 1 mark
data_manager               mixed missing rows + queue states
data_manager_presence      the v-toggled full presence view
run_config                 marks + params + live preview line + the
                           log-dir row, save hint, and the two new
                           bottom-bar labels (261014-f4w)
monitor_running            worker root + all five glyphs + ETA
monitor_empty              no sweeps discovered (empty copy)
wizard                     populated step-1 with advisories
=========================  =====================================

Stability rules (D-11, contract)
--------------------------------
- ONE terminal size: 120x40 (the design grid) for every golden.
- Frozen fixtures: constructor-injected deterministic fakes, pinned
  ``checked_at`` / ``newest_mtime=None`` / scripted stats — zero
  wall-clock reads, zero filesystem scans, zero network/GPU (Pilot's
  run_test is headless; the SVG references a CDN font URL as a constant
  string only).
- Cursor blink is disabled on every Input before export — the blink
  phase is wall-clock state and must never ride a golden.
- ``⠋`` is the static glyph; no spinner frames inside goldens.

Regeneration contract (Pitfall 4)
---------------------------------
``make snapshot-update`` is the ONLY regeneration path (it runs this
module with ``--regenerate`` under ``uv run --group dev --group tui``).
``pytest --snapshot-update`` DOES NOTHING here — no plugin is
installed. CI (``make test``) COMPARES and goes red on drift; it never
regenerates. The maintainer reviews every SVG in a browser/editor
before the first commit and after any regeneration (D-03), then
commits the refreshed files together with the change that drifted the
render.
"""

import asyncio
import contextlib
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

# ===== sys.path bootstrap (the tests/tui/conftest.py contract, inlined) =====
# Script mode (`make snapshot-update` -> this module with --regenerate)
# runs WITHOUT pytest's conftest chain, so the two import roots are
# inserted here — idempotent under pytest, where conftest already did it:
# the repo root for package-qualified ``tui`` imports, pipeline/ for the
# top-level ``env_smoke`` module (the gen_progress.py precedent).
_REPO_ROOT = Path(__file__).resolve().parents[2]
for _root in (str(_REPO_ROOT / "pipeline"), str(_REPO_ROOT)):
    if _root not in sys.path:
        sys.path.insert(0, _root)

# ===== zh language pin (the tests/tui/conftest.py contract, inlined) =====
# Script mode lacks the conftest chain too, and the committed goldens
# are zh-rendered: pin the registry to zh BEFORE any tui import so the
# module-level from-import copies freeze zh (261015-ehc, EHC-1 — the
# registry defaults to English).
from tui import strings as _tui_strings

_tui_strings.set_language("zh")

# ===== F4W startup-config pin (the tests/conftest.py autouse twin) =====
# Script mode also lacks the root conftest's autouse
# DNALLMMARK_TUI_CONFIG_DIR pin, and the golden drive must stay
# machine-independent: a maintainer's real ~/.config/dnallmmark/
# directories.json must never leak into a golden (the fakes hold the
# rendered values, but the module import surface stays honest too).
# Under pytest this assignment is harmless — the autouse fixture
# re-pins per test.
os.environ["DNALLMMARK_TUI_CONFIG_DIR"] = str(
    Path(__file__).parent / "__snapshots__" / ".config-pin")

from env_smoke import CheckResult
from textual.widgets import Input

from tui.app import DnallmMarkTui
from tui.screens.data_manager import (
    ChannelDetail,
    DataManagerScreen,
    MissingSnapshot,
)
from tui.screens.env_check import EnvCheckScreen
from tui.screens.run_config import PickerEntries
from tui.screens.selection import (
    PresetMenu,
    SelectionData,
)
from tui.screens.wizard import WizardModal
from tui.services import registries as registries_service
from tui.services import run_config as run_config_service
from tui.services import selection as selection_service
from tui.services.download_queue import (
    EnqueueOutcome,
    MissingInfo,
    PresenceRow,
    QueueEntry,
    ReauditOutcome,
    merge_presence,
)
from tui.services.registries import (
    PRESENCE_MISSING,
    PRESENCE_PRESENT,
    Presence,
)
from tui.services.run_config import PreviewResult, RunSpec
from tui.services.sweep_launcher import (
    EnvPreflight,
    GateSummary,
    LaunchOutcome,
)
from tui.services.sweep_monitor import (
    CELL_COMPLETED,
    CELL_FAILED,
    CELL_INTERRUPTED,
    CELL_QUEUED,
    CELL_RUNNING,
    CELL_SKIPPED,
    ETA_POINT,
    SWEEP_FINISHED,
    SWEEP_RUNNING,
    CellRow,
    CellSeed,
    CurrentCell,
    EtaEstimate,
    FrontierSnapshot,
    ScanResult,
    SweepStats,
    SweepSummary,
)
from tui.strings import ENV_KERNEL_LABELS

#: The committed golden directory (the plugin-default layout, kept for
#: familiarity; there is NO plugin here — plain files under git).
SNAP_DIR = Path(__file__).parent / "__snapshots__"

#: D-11: the ONE golden size — the design grid.
GOLDEN_SIZE = (120, 40)

#: The frozen env-check cache moment (the boot-test precedent).
_CACHED_CHECKED_AT = "2026-10-11 09:30"


# =====================================================================
# Deterministic fakes (mined from the per-screen Pilot suites — the
# same constructor-injection seams, the same no-fs/no-clock discipline)
# =====================================================================

class _EnvCacheHitFake:
    """The env-check service fake: a same-day cache hit, zero kernels."""

    def cached_results(self):
        return (_CACHED_CHECKED_AT, tuple(
            CheckResult(name=kernel_id, ok=True,
                        lines=(f"PASS: {kernel_id}",))
            for kernel_id in ENV_KERNEL_LABELS
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
        raise AssertionError("a cache-hit golden must never spawn kernels")

    def persist(self, results):
        raise AssertionError("a cache-hit golden must never persist")


class _SelectionGoldenService:
    """The selection-service fake over the standard 3-model/2-dataset
    fixture with mixed presence (the test_pilot_selection.py data); the
    filter legs delegate to the REAL pure grammar."""

    def __init__(self, data=None):
        self.data = data if data is not None else self._standard_data()

    @staticmethod
    def _standard_data():
        return SelectionData(
            model_entries=(
                {"key": "plant-dnamamba-6mer", "type": "MLM",
                 "species": "plants", "size_m": 396.0,
                 "card": {"type": "MLM", "species": "plants",
                          "size (M)": 396, "Tokenizer": "6mer"}},
                {"key": "plant-dnabert-6mer", "type": "MLM",
                 "species": "plants", "size_m": 86.0,
                 "card": {"type": "MLM", "species": "plants",
                          "size (M)": 86, "Tokenizer": "6mer"}},
                {"key": "PlantHelixSeek", "type": "DL",
                 "species": "plants", "size_m": 151.0,
                 "card": {"type": "DL", "species": "plants",
                          "size (M)": 151}},
            ),
            dataset_entries=(
                {"key": "GUE__emp_H3", "category": "Animals",
                 "type": "binary", "metric": "f1",
                 "card": {"Category": "Animals", "type": "binary",
                          "metric": "f1"}},
                {"key": "mouse__DMS", "category": "Animals",
                 "type": "binary", "metric": "f1",
                 "card": {"Category": "Animals", "type": "binary",
                          "metric": "f1"}},
            ),
            presence={
                "GUE__emp_H3": Presence(
                    status=PRESENCE_PRESENT,
                    rows=(743095, 109717, 106227)),
                "mouse__DMS": Presence(status=PRESENCE_MISSING, rows=None),
            },
            # DCL-02 (261014-dcl): FIXED mixed model presence — the
            # golden renders the live cells deterministically regardless
            # of which models exist on the exporting machine.
            model_presence={
                "plant-dnamamba-6mer":
                    selection_service.MODEL_PRESENCE_PRESENT,
                "plant-dnabert-6mer":
                    selection_service.MODEL_PRESENCE_MISSING,
                "PlantHelixSeek":
                    selection_service.MODEL_PRESENCE_UNKNOWN,
            },
        )

    def load_selection_data(self):
        return self.data

    def preset_menu(self):
        return PresetMenu(options=(), load_error=None)

    def custom_names(self):
        return ()

    def save_preset(self, name, models, tasks):
        raise AssertionError("the goldens never save presets")

    def parse_filter(self, query):
        return selection_service.parse_filter_query(query)

    def apply_filter(self, entries, parsed):
        return selection_service.apply_filter(entries, parsed.terms)

    def import_template(self, path):
        raise AssertionError("the goldens never import templates")

    def export_template(self, path, models, tasks):
        raise AssertionError("the goldens never export templates")

    def export_tiers(self, path, models, tasks):
        raise AssertionError("the goldens never export tiers")


class _SelectionEmptyFake(_SelectionGoldenService):
    """The shell fake for non-selection goldens (empty data)."""

    def __init__(self):
        super().__init__(data=SelectionData())


class _RunConfigGoldenService:
    """The run-config service fake (the test_pilot_run_config.py fake,
    compact): real pure-grammar legs, in-memory state, deterministic
    preview counts."""

    def __init__(self, spec=None):
        self._spec = spec if spec is not None else RunSpec(
            models=(), tasks=())

    def picker_entries(self):
        return PickerEntries(
            model_entries=(
                {"key": "model-a", "type": "MLM", "species": "plant",
                 "size_m": 86.0, "card": {}},
                {"key": "model-b", "type": "MLM", "species": "plant",
                 "size_m": 396.0, "card": {}},
                {"key": "cust-one", "type": "MLM", "species": "plant",
                 "size_m": 1.0, "card": {}},
                {"key": "cust-off", "type": "MLM", "species": "plant",
                 "size_m": 1.0, "card": {}},
            ),
            dataset_entries=(
                {"key": "task-1", "category": "GUE", "type": "cls",
                 "metric": "accuracy", "card": {}},
                {"key": "task-2", "category": "GUE", "type": "cls",
                 "metric": "accuracy", "card": {}},
            ),
            custom_status={
                "cust-one": {"custom": True, "enabled": True},
                "cust-off": {"custom": True, "enabled": False},
            },
        )

    def load_state(self):
        return self._spec

    def save_state(self, spec):
        self._spec = spec

    def save_directory_defaults(self, spec):
        # F4W-03: display-only stub — the golden drive presses
        # neither [s] nor ctrl+o (D-11 stability rules).
        raise AssertionError(
            "the goldens never save directory defaults")

    def path_state(self, value):
        if not value:
            return "unset"
        return "missing"

    def parse_params(self, raw):
        return run_config_service.parse_params(raw)

    def resolve_dirs(self, spec):
        return run_config_service.resolve_dirs(spec)

    def parse_filter(self, query):
        return selection_service.parse_filter_query(query)

    def apply_filter(self, entries, parsed):
        return selection_service.apply_filter(entries, parsed.terms)

    def probe_ineligible(self):
        return frozenset({"model-a"})

    def preview(self, spec):
        cells = (len(spec.models) * len(spec.tasks)
                 * len(spec.seeds)
                 * max(1, len(spec.curve_fractions)))
        problems: tuple = ()
        if not spec.models or not spec.tasks:
            problems = (("empty_selection", None),)
        return PreviewResult(
            models_count=len(spec.models),
            tasks_count=len(spec.tasks),
            seeds_count=len(spec.seeds),
            fractions_count=(len(spec.curve_fractions)
                             if spec.curve_fractions else None),
            cells_count=cells,
            cells=(),
            problems=problems,
        )

    def compose_argv(self, spec):
        return ("/usr/bin/python", "run_sweep.py", "--models",
                *spec.models, "--tasks", *spec.tasks)

    def expected_phrase(self, output_root):
        return "finetuned"

    def phrase_matches(self, typed, output_root):
        return typed == "finetuned"


class _LauncherFake:
    """The launcher-seam fake (recorded inert; the goldens never gate)."""

    def env_preflight(self, kernels=None):
        return EnvPreflight(can_launch=True, reasons=(),
                            failed_kernels=())

    def gate_confirm_data(self, spec):
        return GateSummary(models=1, tasks=1, seeds=3, cells=3,
                           output_root="./finetuned", is_e2x=False,
                           expected_phrase="finetuned")

    def launch_spec(self, spec, phrase=None):
        return LaunchOutcome(spawned=True, root="/repo/finetuned",
                             tee_path="/state/logs/sweep.log", error=None)

    def launch_from_failures(self, failures_path, seeds, output_root,
                             peft="none", config_variant="none",
                             phrase=None):
        return LaunchOutcome(spawned=True, root=str(output_root),
                             tee_path="/state/logs/rerun.log", error=None)

    def phrase_matches(self, typed, output_root):
        return typed == "finetuned"

    def kill_sweep(self, root):
        return "signalled"

    def detach(self, root):
        return "detached"

    def live_sweeps(self):
        return ()

    def tee_path_for(self, root):
        return None


def _monitor_summary(root, state, done=0, total=None):
    """One SweepSummary (newest_mtime frozen None — no clock in goldens)."""
    return SweepSummary(root=Path(f"/scans/{root}"), state=state,
                        done=done, total=total, newest_mtime=None)


def _monitor_stats(done=0, total=None, current=None, elapsed=None,
                   eta=None):
    return SweepStats(
        done=done, total=total, current=current,
        elapsed_seconds=elapsed,
        eta=eta if eta is not None else EtaEstimate("none", None, None,
                                                    None))


def _monitor_row(model, task, seeds):
    """One CellRow; seeds maps seed -> machine state (all five glyph
    states ride the monitor_running golden)."""
    return CellRow(model=model, task=task, seeds=tuple(
        CellSeed(seed=seed, state=state, fraction_states=None)
        for seed, state in seeds.items()))


class _MonitorGoldenService:
    """The monitor-service fake (scripted per-root scans/cells/stats —
    the test_pilot_monitor.py fake, compact)."""

    def __init__(self, scans=None, cells=None, stats=None,
                 resume_counts=None):
        self._scans = list(scans) if scans else [
            ScanResult(sweeps=(), watermarks={})]
        self._cells = dict(cells or {})
        self._stats = dict(stats or {})
        self._resume = dict(resume_counts or {})

    def full_scan(self, prev_watermarks=None):
        if self._scans:
            self._last_scan = self._scans.pop(0)
        return getattr(self, "_last_scan",
                       ScanResult(sweeps=(), watermarks={}))

    def frontier_scan(self, root):
        return FrontierSnapshot(
            root=Path(str(root)), state="running", newest_mtime=None,
            newest_cell=None, cell_states={})

    def cells_view(self, root):
        return self._cells.get(str(root), ())

    def stats(self, root, expected_total=None, fallback_start=None):
        return self._stats.get(str(root),
                               _monitor_stats(done=0, total=None))

    def sweep_scale(self, root):
        return None

    def resume_count(self, root):
        return self._resume.get(str(root), 0)

    def failures_view(self, root):
        return ()

    def rerun_lane(self, root):
        return ("none", "none")

    def cell_record(self, root, model, task, seed):
        return None

    def read_log_tail(self, path, max_lines=200, max_bytes=65536):
        return None

    def is_sweep_root(self, path):
        return True

    def add_manual_root(self, path):
        return True


def _running_monitor_service():
    """The monitor_running golden fixture (delta A's proof golden): the
    discovered pane lists a multi-GPU worker root NEXT TO a default
    root; the attached cell table carries all five glyphs; the stats
    line carries elapsed + point ETA (all frozen values).

    261017-uwr (Task 4): ONE interrupted pair row joins the fixture —
    the PlantHelixSeek-style dead pair (WINDOWS #34's residue shape) —
    so the golden demonstrates the ⏸ glyph, the live-on-top ordering,
    and the context header's three-segment counts alongside ⏵. The
    ONLY fixture change: no factory, drive function, or assertion
    weakens."""
    return _MonitorGoldenService(
        scans=[ScanResult(sweeps=(
            _monitor_summary("finetuned-mgpu-w0", SWEEP_RUNNING,
                             done=12, total=36),
            _monitor_summary("finetuned-smoke", SWEEP_FINISHED,
                             done=1, total=1),
        ), watermarks={})],
        cells={"/scans/finetuned-mgpu-w0": (
            _monitor_row("plant-dnamamba-6mer", "GUE__emp_H3",
                         {42: CELL_RUNNING, 43: CELL_QUEUED,
                          44: CELL_QUEUED}),
            _monitor_row("plant-dnabert-6mer", "GUE__emp_H3",
                         {42: CELL_COMPLETED, 43: CELL_SKIPPED,
                          44: CELL_COMPLETED}),
            _monitor_row("plant-dnabert-6mer", "mouse__DMS",
                         {42: CELL_FAILED, 43: CELL_FAILED,
                          44: CELL_FAILED}),
            _monitor_row("PlantHelixSeek", "mouse__DMS",
                         {42: CELL_INTERRUPTED}),
        )},
        stats={"/scans/finetuned-mgpu-w0": _monitor_stats(
            done=3, total=36,
            current=CurrentCell(model="plant-dnamamba-6mer",
                                task="GUE__emp_H3", seed=42),
            elapsed=4360.0,
            eta=EtaEstimate(ETA_POINT, 7560.0, None, None))},
        resume_counts={"/scans/finetuned-mgpu-w0": 1},
    )


class _QueueInertFake:
    """The app-level driver-queue fake (inert — the goldens never kick
    the driver; the run-config suite's minimal shell fake)."""

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
        return ()

    def probe_zenodo(self):
        return "not_public"

    def run_task(self, *args, **kwargs):
        raise AssertionError("the goldens never run queue tasks")


def _dm_queue_entry(key, state="pending", **overrides):
    """One QueueEntry with pinned timestamps (the 10-04 fixture sugar)."""
    fields = {
        "key": key, "kind": "dataset", "state": state, "attempts": 0,
        "enqueued_at": "2026-10-12T10:00:00", "started_at": None,
        "finished_at": None, "last_percent": None, "interrupted": False,
        "log_path": None, "problems": (), "reconcile": None,
    }
    fields.update(overrides)
    return QueueEntry(**fields)


def _dm_missing_row(key, total=1000):
    return MissingInfo(
        key=key, declared_total=total, channel="downloadable",
        reason_code=None,
        source_url="https://www.modelscope.cn/datasets/lgq12697/GUE")


class _DataManagerGoldenService:
    """The data-manager screen-service fake: the two panes over mixed
    presence/verified states (3 missing rows + a 4-state queue incl. a
    reconcile-verified done entry — the 10-04 fixtures)."""

    def __init__(self):
        self.entries_list = [
            _dm_queue_entry("GUE__emperven_H3"),
            _dm_queue_entry("mouse__DMS", "downloading",
                            last_percent=42),
            _dm_queue_entry("GUE__emp_H3", "done",
                            reconcile={"verdict": "pass",
                                       "declared": 7349,
                                       "measured": 7349,
                                       "unified_eval_n": None}),
            _dm_queue_entry("plant__vista-100m", "failed",
                            attempts=2,
                            problems=("Killed",)),
        ]

    def missing_snapshot(self):
        return MissingSnapshot(
            rows=(
                _dm_missing_row("GUE__emp_H3", 7349),
                _dm_missing_row("mouse__DMS", 12411),
                _dm_missing_row("plant__vista-100m", 64350),
            ),
            total=50, present=47,
            # DCL-03: the full-view fixture (fixed mixed statuses — the
            # v-toggled golden renders deterministic values)
            presence_rows=(
                PresenceRow(
                    key="GUE__emp_H3",
                    status=registries_service.PRESENCE_PRESENT,
                    declared_total=7349),
                PresenceRow(
                    key="mouse__DMS",
                    status=registries_service.PRESENCE_MISSING,
                    declared_total=12411),
                PresenceRow(
                    key="ghost__drift",
                    status=registries_service.PRESENCE_UNKNOWN,
                    declared_total=0),
            ))

    def entries(self):
        return tuple(self.entries_list)

    def enqueue(self, key):
        self.entries_list.append(_dm_queue_entry(key))
        return EnqueueOutcome(action="enqueued", key=key)

    def enqueue_all(self):
        return 0

    def enqueue_zenodo(self):
        return EnqueueOutcome(action="enqueued", key="zenodo-bundle")

    def retry(self, key):
        return True

    def cancel(self, key):
        return "removed"

    def reaudit(self, run_id):
        return ReauditOutcome(ok=True, details=("exit_code=0",))

    def probe_zenodo(self):
        return "not_public"

    def channel_detail(self, key):
        return ChannelDetail(
            key=key,
            source_url=("https://www.modelscope.cn/datasets/lgq12697/"
                        "GUE"),
            argv=None, channel="downloadable", reason_code=None)

    def read_log(self, key):
        return ()


#: The frozen data-manager clock moment (the Zenodo probe's HH:MM).
_DM_FROZEN_NOW = datetime(2026, 10, 13, 12, 0, 0, tzinfo=UTC)


@contextlib.contextmanager
def _frozen_dm_clock():
    """D-11 fixture freeze: the Zenodo probe line renders a screen-side
    wall-clock HH:MM with NO ``now=`` seam (data_manager.py:668 —
    ``datetime.now().astimezone().strftime``) — pin the module's
    ``datetime`` for the export window (fix the fixture, never the
    compare; the only wall-clock reachable from any golden drive).
    """
    module = sys.modules["tui.screens.data_manager"]
    original = module.datetime

    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return _DM_FROZEN_NOW.replace(tzinfo=tz)

    # setattr (not attribute assignment): ty correctly reads frozen
    # ModuleType as having no `datetime` attribute — the test_services_env_gate
    # precedent (script mode has no monkeypatch fixture to lean on).
    setattr(module, "datetime", _FrozenDatetime)  # noqa: B010
    try:
        yield
    finally:
        setattr(module, "datetime", original)  # noqa: B010


#: The frozen monitor clock moment (261019-f0x): the summary strip's
#: ETA wall-clock landing reads ``time.time()`` through the monitor
#: module's own ``time`` — pin it for the export window (the
#: _frozen_dm_clock precedent; without the freeze the minute boundary
#: breaks test_golden_export_is_deterministic_across_instances).
_MON_FROZEN_EPOCH = 1791321600.0  # 2026-10-07 12:00:00 UTC


@contextlib.contextmanager
def _frozen_mon_clock():
    """261019-f0x fixture freeze: every wall-clock read the monitor
    screen renders (the strip's ETA "(HH:MM)" landing, the detail's
    local-time segments) routes through ``tui.screens.monitor``'s
    module-level ``time`` — pin it for the export window."""
    module = sys.modules["tui.screens.monitor"]
    original = module.time

    class _FrozenTime:
        @staticmethod
        def time():
            return _MON_FROZEN_EPOCH

        @staticmethod
        def strftime(fmt, value):
            return original.strftime(fmt, value)

        @staticmethod
        def localtime(seconds=None):
            return original.localtime(
                _MON_FROZEN_EPOCH if seconds is None else seconds)

    setattr(module, "time", _FrozenTime)  # noqa: B010
    try:
        yield
    finally:
        setattr(module, "time", original)  # noqa: B010


def _golden_app(selection=None, run_config=None, monitor=None):
    """The real app with EVERY seam faked (no real service ever runs)."""
    return DnallmMarkTui(
        env_check_service=_EnvCacheHitFake(),
        selection_service=(selection if selection is not None
                           else _SelectionEmptyFake()),
        download_queue_service=_QueueInertFake(),
        run_config_service=(run_config if run_config is not None
                            else _RunConfigGoldenService()),
        launcher_service=_LauncherFake(),
        monitor_service=(monitor if monitor is not None
                         else _MonitorGoldenService()),
        monitor_launcher=_LauncherFake(),
    )


# =====================================================================
# The golden corpus — one app builder + one drive per id
# =====================================================================

async def _settle(pilot, app, rounds=3):
    """The house settle: sequential worker->handler chains."""
    for _ in range(rounds):
        await app.workers.wait_for_complete()
        await pilot.pause()


async def _drive_env_check(pilot, app):
    """The opening screen over the cache-hit fake (the boot contract)."""
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()
    assert isinstance(app.screen, EnvCheckScreen)


async def _drive_selection_models(pilot, app):
    """Models view: 2 marks + the live filter with (n/total) counts."""
    app.push_screen(app.build_selection_screen())
    await _settle(pilot, app)
    await pilot.press("space")
    await pilot.pause()
    await pilot.press("down")
    await pilot.press("space")
    await pilot.pause()
    await pilot.press("slash")
    await pilot.pause()
    for char in "dnabert":
        await pilot.press(char)
    await pilot.pause()


async def _drive_selection_datasets(pilot, app):
    """Datasets view (the m flip) with one task marked + presence."""
    app.push_screen(app.build_selection_screen())
    await _settle(pilot, app)
    await pilot.press("m")
    await pilot.pause()
    await pilot.press("space")
    await pilot.pause()


async def _drive_data_manager(pilot, app):
    """The two panes over the mixed presence/verified fixture (the
    Zenodo probe clock frozen — see _frozen_dm_clock)."""
    with _frozen_dm_clock():
        app.push_screen(DataManagerScreen(
            data_service=_DataManagerGoldenService()))
        await _settle(pilot, app)


async def _drive_data_manager_presence(pilot, app):
    """DCL-03 (261014-dcl): the same fixture with v pressed — the full
    official-registry presence view replaces the missing table (title,
    glyph-prefixed keys, declared totals; the same frozen clock)."""
    with _frozen_dm_clock():
        app.push_screen(DataManagerScreen(
            data_service=_DataManagerGoldenService()))
        await _settle(pilot, app)
        await pilot.press("v")
        await pilot.pause()


async def _drive_run_config(pilot, app):
    """The post-delta-B slot-4 screen: 2 model marks + params + the
    live preview line (2 x 1 x 3 = 6)."""
    app.push_screen(app.build_run_config_screen())
    await _settle(pilot, app)


async def _drive_monitor_running(pilot, app):
    """261019-f0x (the B-skeleton + D-right-pane proof view): the
    multi-GPU worker root renders as the Running tab's ONE card — the
    summary strip (the w0 root's stats fraction, elapsed + the
    point-ETA wall clock over the frozen clock, the rate dash — no
    progress scripted) over the matrix of every (model, task) group
    with the focused group's style-only highlight; the right pane
    carries the focused group's detail (per-seed states, the honest
    indeterminate) and the designed no-tee state (the launcher fake's
    tee is None — the pane's log region renders MON_LOG_UNAVAILABLE,
    never a fabricated empty log); the History tab header carries the
    finished smoke row."""
    with _frozen_mon_clock():
        app.push_screen(app.build_monitor_screen())
        await _settle(pilot, app)


async def _drive_monitor_empty(pilot, app):
    """The zero-run boot: the Running tab renders its actionable empty
    copy on the settled (scan-landed, note-cleared) surface — the
    right pane hidden (no cards), the same frozen monitor clock."""
    with _frozen_mon_clock():
        app.push_screen(app.build_monitor_screen())
        await _settle(pilot, app)


async def _drive_wizard(pilot, app):
    """A populated model-wizard step 1 with live advisories: the path
    probe injected (deterministic, no fs) -> the missing-path ✗ line;
    a non-numeric size -> the numeric hint."""
    wizard = WizardModal(
        kind="models",
        validator=lambda values: [],
        on_valid=lambda candidate: None,
        on_import=lambda: None,
        on_export=lambda: None,
        vocabularies={"species": ("human", "plants"),
                      "Tokenizer": ("BPE", "6-mer", "overlapped 6-mer")},
        dir_exists=lambda raw: False,
    )
    app.push_screen(wizard)
    await pilot.pause()
    key_input = wizard.query_one("#wiz-key", Input)
    key_input.focus()
    await pilot.pause()
    await pilot.press(*list("my-custom-lm"))
    await pilot.pause()
    path_input = wizard.query_one("#wiz-model-path", Input)
    path_input.focus()
    await pilot.pause()
    await pilot.press(*list("models/my-lm"))
    await pilot.pause()
    size_input = wizard.query_one("#wiz-size-m", Input)
    size_input.focus()
    await pilot.pause()
    await pilot.press(*list("abc"))
    await pilot.pause()


#: The frozen corpus registry — golden id -> (app builder, drive).
GOLDENS = {
    "env_check": (
        lambda: _golden_app(), _drive_env_check),
    "selection_models": (
        lambda: _golden_app(selection=_SelectionGoldenService()),
        _drive_selection_models),
    "selection_datasets": (
        lambda: _golden_app(selection=_SelectionGoldenService()),
        _drive_selection_datasets),
    "data_manager": (
        lambda: _golden_app(), _drive_data_manager),
    "data_manager_presence": (
        lambda: _golden_app(), _drive_data_manager_presence),
    "run_config": (
        lambda: _golden_app(run_config=_RunConfigGoldenService(
            spec=RunSpec(models=("model-a", "model-b"),
                         tasks=("task-1",)))),
        _drive_run_config),
    "monitor_running": (
        lambda: _golden_app(monitor=_running_monitor_service()),
        _drive_monitor_running),
    "monitor_empty": (
        lambda: _golden_app(), _drive_monitor_empty),
    "wizard": (
        lambda: _golden_app(), _drive_wizard),
}


# =====================================================================
# The harness (probe-verified: run_test(size) + export_screenshot is
# byte-deterministic across independent app instances)
# =====================================================================

async def _export_golden(golden_id: str) -> str:
    """Boot, drive, and export ONE golden's SVG at the design grid."""
    build, drive = GOLDENS[golden_id]
    app = build()
    async with app.run_test(size=GOLDEN_SIZE) as pilot:
        await drive(pilot, app)
        await pilot.pause()
        # D-11: the Input cursor blink is wall-clock phase — kill it on
        # every Input before the export (fix the fixture, never the
        # compare).
        for input_widget in app.screen.query(Input):
            input_widget.cursor_blink = False
        await pilot.pause()
        return app.export_screenshot()


def _golden(golden_id: str) -> str:
    """Read one committed golden (UTF-8 — the CJK copy decodes)."""
    path = SNAP_DIR / f"{golden_id}.svg"
    if not path.exists():
        pytest.fail(
            f"golden __snapshots__/{golden_id}.svg is missing — "
            "regenerate via `make snapshot-update` (the ONLY "
            "regeneration path; pytest --snapshot-update does NOTHING "
            "in the fallback lane)")
    return path.read_text(encoding="utf-8")


# =====================================================================
# The golden tests (one per id — CI compares, never regenerates)
# =====================================================================


def test_env_check_golden():
    """The cache-hit env boot: eight PASS rows + the last-check line."""
    assert asyncio.run(_export_golden("env_check")) == _golden(
        "env_check")


def test_selection_models_golden():
    """Models view: 2 marks, the filter live with (1/3) counts."""
    assert asyncio.run(_export_golden("selection_models")) == _golden(
        "selection_models")


def test_selection_datasets_golden():
    """Datasets view (the m flip): one mark + presence cells."""
    assert asyncio.run(_export_golden("selection_datasets")) == _golden(
        "selection_datasets")


def test_data_manager_golden():
    """The two panes: mixed missing rows + 4-state queue + summary."""
    assert asyncio.run(_export_golden("data_manager")) == _golden(
        "data_manager")


def test_data_manager_presence_golden():
    """DCL-03: the v-toggled full view — glyph-prefixed official keys
    with declared totals beside the untouched queue pane."""
    assert asyncio.run(_export_golden("data_manager_presence")) == _golden(
        "data_manager_presence")


def test_run_config_golden():
    """Slot 4 post-delta-B: marks + params + the live preview line."""
    assert asyncio.run(_export_golden("run_config")) == _golden(
        "run_config")


def test_monitor_running_golden():
    """The multi-GPU proof: worker root row + five glyphs + stats/ETA."""
    assert asyncio.run(_export_golden("monitor_running")) == _golden(
        "monitor_running")


def test_monitor_empty_golden():
    """The zero-sweep boot: the designed empty copy in both panes."""
    assert asyncio.run(_export_golden("monitor_empty")) == _golden(
        "monitor_empty")


def test_wizard_golden():
    """The populated wizard step: fields + the live advisory lines."""
    assert asyncio.run(_export_golden("wizard")) == _golden("wizard")


# =====================================================================
# Non-vacuousness (T-12-03-02/03): determinism across independent
# instances + sensitivity to fixture drift
# =====================================================================

def test_golden_export_is_deterministic_across_instances():
    """The probe result codified: two INDEPENDENT app instances export
    byte-identical SVGs for the same fixture."""
    first = asyncio.run(_export_golden("monitor_running"))
    second = asyncio.run(_export_golden("monitor_running"))
    assert first == second


def test_golden_compare_is_sensitive_to_fixture_state():
    """The compare is not vacuous: two DIFFERENT fixture states export
    DISTINCT SVGs (red-on-drift is real)."""
    running = asyncio.run(_export_golden("monitor_running"))
    empty = asyncio.run(_export_golden("monitor_empty"))
    assert running != empty


# =====================================================================
# The regeneration entry (Pitfall 4 — the ONLY regeneration path is
# `make snapshot-update`, which runs this block; MAINTAINER-ONLY, the
# refreshed SVGs are reviewed before commit per D-03)
# =====================================================================

def _regenerate_all() -> None:
    """(Re)write every committed golden from the factories above."""
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    for golden_id in GOLDENS:
        svg = asyncio.run(_export_golden(golden_id))
        (SNAP_DIR / f"{golden_id}.svg").write_text(svg, encoding="utf-8")
        print(f"  ✅ golden written: tests/tui/__snapshots__/"
              f"{golden_id}.svg ({len(svg)} chars)")
    print(f"\n{len(GOLDENS)} goldens regenerated — REVIEW each SVG in a "
          "browser/editor (D-03) before committing; CI compares, it "
          "never regenerates.")


if __name__ == "__main__":
    if "--regenerate" in sys.argv:
        _regenerate_all()
    else:
        print(__doc__)
        print("Usage: python tests/tui/test_snapshots.py --regenerate "
              "(or: make snapshot-update)")
        sys.exit(2)
