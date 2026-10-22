"""
Tier-2 Pilot suite for the run-config screen (Phase 11, 11-06; slot 4,
D-01..D-05, D-14, D-19, the LNC-01..03 launch-confirmation pipeline, and the
D-06 exit triple).

Pins the slot-4 screen and its app/nav wiring against the REAL
``DnallmMarkTui`` with constructor-injected deterministic fakes (no real
kernel, no real registry read, no real XDG write, no real subprocess —
the D-03 discipline; the pure grammar functions parse_params/
resolve_dirs/parse_filter delegate to the real modules, which are pure
and stdlib-only):

- Task 1 (the shell): both columns compose at 120x40 AND 80x24; the
  status-line counts; ``m`` flips the picker kind; ``/`` filters;
  space marks + persists (the fake's load proves the round-trip);
  disabled customs warn and never mark; every params row renders its
  default (the ``—`` absent family, seeds 42,43,44); the preview line
  re-renders on mark change through the run-id-tagged worker; the
  empty-selection problem copy; zero Chinese literals in the module;
- Task 2 (the gate): the [p] modal's verbatim argv + numbered problems;
  the [enter] 启动确认 pipeline (problems block, env block with verbatim
  reasons, non-E2' confirm, the E2' typed-phrase live-match escalation,
  launch toasts, the enter-key pin);
- Task 3 (exit + choices): the app-level q intercept (ExitModal
  detach/kill/cancel, default detach), the PEFT/变体 RadioSet flows,
  the 公平子集 toggle copy pair.
"""

import json
import re
import threading
from pathlib import Path
from typing import ClassVar

from rich.text import Text
from textual.widgets import Checkbox, DirectoryTree, Input, SelectionList, Static

import tui.screens.run_config as run_config_screen_module
from tui.app import DnallmMarkTui
from tui.screens.nav import BottomBar, TopMenuBar
from tui.screens.run_config import (
    DirPickerModal,
    PickerEntries,
    PickerList,
    RunConfigScreen,
)
from tui.screens.selection import PresetMenu, SelectionData
from tui.services import registries as registries_service
from tui.services import run_config as run_config_service
from tui.services import selection as selection_service
from tui.services import settings as tui_settings
from tui.services.download_queue import merge_presence
from tui.services.run_config import PreviewResult, RunSpec
from tui.services.sweep_launcher import (
    EnvPreflight,
    GateSummary,
    GpuCapacityBlock,
    LaunchOutcome,
)
from tui.strings import (
    CFG_ARGV_LABEL,
    CFG_CACHE_DEFAULT,
    CFG_DATASET_ROOT_DEFAULT,
    CFG_EMPTY_SELECTION_PROBLEM,
    CFG_FIELD_LOG_DIR,
    CFG_FIELD_MODEL_ROOT,
    CFG_FIELD_PEFT,
    CFG_FIELD_VARIANT,
    CFG_LOG_DIR_DEFAULT,
    CFG_MODEL_ROOT_DEFAULT,
    CFG_PICKER_DATASETS,
    CFG_PICKER_MODELS,
    CFG_PREVIEW_LINE,
    CFG_PREVIEW_NOTE,
    CFG_PREVIEW_PROBLEMS,
    CFG_SAVE_DEFAULTS_TOAST,
    CFG_STATUS_LINE,
    CFG_SUBSET_OFF,
    NAV_LABEL_SELECTION,
    SEL_DISABLED_MARK_WARNING,
    SEL_FILTER_COUNT,
    SEL_SWITCH_LABEL,
)

# The i18n grep lock (the test_pilot_env_check.py precedent): the new
# screen module joins the zero-Chinese-literals scan (11-05 contract
# note — each new Pilot suite adds its screen module to its tuple).
_RUN_CONFIG_MODULE_FILE = Path(run_config_screen_module.__file__)
_GREP_LOCK_MODULES = (
    _RUN_CONFIG_MODULE_FILE,
)


# =====================================================================
# Deterministic fakes (D-03: no real kernel / registry / state / spawn)
# =====================================================================

def _model_entry(key, **overrides):
    """One canonical model entry (the 08-04 view, fake data)."""
    entry = {
        "key": key, "type": "MLM", "species": "plant",
        "size_m": 86.0, "card": {},
    }
    entry.update(overrides)
    return entry


def _dataset_entry(key, **overrides):
    """One canonical dataset entry (the 08-04 view, fake data)."""
    entry = {
        "key": key, "category": "GUE", "type": "cls",
        "metric": "accuracy", "card": {},
    }
    entry.update(overrides)
    return entry


#: The picker fixture: two official models + one enabled custom + one
#: DISABLED custom (the disabled-mark warning row), two tasks.
_FAKE_MODELS = (
    _model_entry("model-a"),
    _model_entry("model-b"),
    _model_entry("cust-one"),
    _model_entry("cust-off"),
)
_FAKE_DATASETS = (
    _dataset_entry("task-1"),
    _dataset_entry("task-2"),
)
_FAKE_CUSTOM_STATUS = {
    "cust-one": {"custom": True, "enabled": True},
    "cust-off": {"custom": True, "enabled": False},
}


class FakeRunConfigService:
    """The run-config service fake (the injection seam's fake side).

    Deterministic and recording: the pure grammar legs (parse_params /
    resolve_dirs / parse_filter / apply_filter) delegate to the REAL
    modules (pure, stdlib-only — the grammar the screen must consume);
    the state legs run in memory (no XDG file ever opens); ``preview``
    derives deterministic counts from the spec unless a script list is
    pinned; every call is recorded for the assertions.
    """

    def __init__(self, entries=None, spec=None, preview_script=None,
                 path_states=None, phrase_expected="finetuned",
                 probe_names=frozenset({"model-a"})):
        self.entries = entries if entries is not None else PickerEntries(
            model_entries=tuple(_FAKE_MODELS),
            dataset_entries=tuple(_FAKE_DATASETS),
            custom_status=dict(_FAKE_CUSTOM_STATUS),
        )
        self._spec = spec if spec is not None else RunSpec(
            models=(), tasks=())
        self._preview_script = (
            list(preview_script) if preview_script else None)
        self._path_states = dict(path_states or {})
        self.phrase_expected = phrase_expected
        self.probe_names = probe_names
        self.preview_calls = []
        self.saved_specs = []

    # ----- the picker + state surface -----

    def picker_entries(self):
        return self.entries

    def load_state(self):
        return self._spec

    def save_state(self, spec):
        self.saved_specs.append(spec)
        self._spec = spec

    def save_directory_defaults(self, spec):
        """261014-f4w (the c2l mixing precedent): the single write leg
        delegates to the REAL service — the save tests assert the file
        the real seam writes (under the conftest's tmp config pin, never
        the real home)."""
        return run_config_service.save_directory_defaults(spec)

    def path_state(self, value):
        """'exists' | 'missing' | 'unset' — scripted per value."""
        if not value:
            return "unset"
        return self._path_states.get(value, "missing")

    # ----- the pure grammar legs (REAL module delegation) -----

    def parse_params(self, raw):
        return run_config_service.parse_params(raw)

    def resolve_dirs(self, spec):
        return run_config_service.resolve_dirs(spec)

    def parse_filter(self, query):
        return selection_service.parse_filter_query(query)

    def apply_filter(self, entries, parsed):
        return selection_service.apply_filter(entries, parsed.terms)

    def probe_ineligible(self):
        return self.probe_names

    # ----- the preview / gate surface -----

    def preview(self, spec):
        self.preview_calls.append(spec)
        if self._preview_script:
            result = self._preview_script.pop(0)
            if result is not None:
                return result
        fractions = max(1, len(spec.curve_fractions))
        cells = (len(spec.models) * len(spec.tasks)
                 * len(spec.seeds) * fractions)
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

    def compose_dispatch_argv(self, spec):
        """16-04: the dispatch composer delegates to the REAL module
        (the pure-grammar-leg precedent — parse_params/resolve_dirs) so
        the [p] verbatim-argv assertions exercise the real argv
        authority the launcher routes through (one composition source,
        zero drift between preview and spawn)."""
        return run_config_service.compose_dispatch_argv(spec)

    def expected_phrase(self, output_root):
        return self.phrase_expected

    def phrase_matches(self, typed, output_root):
        return typed == self.phrase_expected


class FakeLauncherService:
    """The launcher service fake (recorded, scripted outcomes)."""

    def __init__(self, preflight=None, summary=None, outcomes=None,
                 live=(), confirm_raises=None, launch_raises=None,
                 single_gpu_blocked=None, kill_raises=None):
        self._preflight = (preflight if preflight is not None
                           else EnvPreflight(
                               can_launch=True, reasons=(),
                               failed_kernels=()))
        self._summary = summary
        self._outcomes = list(outcomes) if outcomes else None
        self._live = tuple(live)
        self._confirm_raises = confirm_raises
        self._launch_raises = launch_raises
        # WR-02 (08 review, fix batch 261017-klw): the raising-kill knob —
        # a kill_sweep that raises BEFORE recording is the fan-out-abort
        # probe; one that raises AFTER recording proves the NEXT root is
        # still attempted.
        self._kill_raises = kill_raises
        # EHC-3 (261015-ehc): the single-GPU guard seam (None = the
        # method absent-equivalent — never blocks)
        self._single_gpu_blocked = single_gpu_blocked
        self.env_calls = 0
        self.confirm_calls = []
        self.launch_calls = []
        self.kill_calls = []
        self.detach_calls = []

    def env_preflight(self, kernels=None):
        self.env_calls += 1
        return self._preflight

    def gate_confirm_data(self, spec):
        self.confirm_calls.append(spec)
        if self._confirm_raises is not None:
            raise self._confirm_raises
        return self._summary or GateSummary(
            models=1, tasks=1, seeds=3, cells=3,
            output_root="./finetuned", is_e2x=False,
            expected_phrase="finetuned")

    def launch_spec(self, spec, phrase=None):
        self.launch_calls.append((spec, phrase))
        if self._launch_raises is not None:
            raise self._launch_raises
        if self._outcomes:
            return self._outcomes.pop(0)
        return LaunchOutcome(
            spawned=True, root="/repo/finetuned",
            tee_path="/state/logs/sweep.log", error=None)

    def launch_from_failures(self, failures_path, seeds, output_root,
                             peft="none", config_variant="none",
                             phrase=None):
        return LaunchOutcome(
            spawned=True, root=str(output_root),
            tee_path="/state/logs/sweep_rerun.log", error=None)

    def phrase_matches(self, typed, output_root):
        from pathlib import Path

        return typed == Path(str(output_root)).name

    def kill_sweep(self, root):
        self.kill_calls.append(root)
        if self._kill_raises is not None:
            raise self._kill_raises
        return "signalled"

    def detach(self, root):
        self.detach_calls.append(root)
        return "detached"

    def live_sweeps(self):
        return self._live

    def tee_path_for(self, root):
        return None

    def single_gpu_launch_blocked(self, requested_workers=1):
        """16-03 (D16-10): the multi-GPU capacity seam — the requested
        workers ride the slot-4 gate's threading (default 1 keeps the
        zero-arg monitor reads valid, Pitfall 3)."""
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
        raise AssertionError("the run-config tests never save presets")

    def parse_filter(self, query):
        return selection_service.parse_filter_query(query)

    def apply_filter(self, entries, parsed):
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
        raise AssertionError("the run-config tests never run queue tasks")


class _MonitorShellFake:
    """The minimal monitor-service fake (11-07): the launched root
    discovered running with a known plan + stats (the D-13 lane)."""

    def __init__(self, root="/repo/finetuned", done=1, total=3):
        self.root = root
        self._done = done
        self._total = total

    def full_scan(self, prev_watermarks=None):
        from pathlib import Path

        from tui.services.sweep_monitor import (
            SWEEP_RUNNING,
            ScanResult,
            SweepSummary,
        )
        return ScanResult(sweeps=(
            SweepSummary(root=Path(self.root), state=SWEEP_RUNNING,
                         done=self._done, total=self._total,
                         newest_mtime=None),), watermarks={})

    def frontier_scan(self, root):
        from pathlib import Path

        from tui.services.sweep_monitor import (
            FrontierSnapshot,
        )
        return FrontierSnapshot(
            root=Path(str(root)), state="running", newest_mtime=None,
            newest_cell=None, cell_states={})

    def cells_view(self, root):
        return ()

    def stats(self, root, expected_total=None, fallback_start=None):
        from tui.services.sweep_monitor import EtaEstimate, SweepStats

        return SweepStats(
            done=self._done, total=self._total, current=None,
            elapsed_seconds=None, eta=EtaEstimate("none", None, None, None))

    def sweep_scale(self, root):
        return None

    def resume_count(self, root):
        return 0

    def rerun_lane(self, root):
        return ("none", "none")

    def failures_view(self, root):
        return ()

    def cell_record(self, root, model, task, seed):
        return None

    def read_log_tail(self, path, max_lines=200, max_bytes=65536):
        return None

    def is_sweep_root(self, path):
        return False

    def add_manual_root(self, path):
        return False


def _app(run_service=None, launcher=None, monitor=None):
    """The real app over the fake services (constructor injection)."""
    return DnallmMarkTui(
        env_check_service=_EnvCacheHitFake(),
        selection_service=_SelectionFake(),
        download_queue_service=_QueueDriverFake(),
        run_config_service=(run_service if run_service is not None
                            else FakeRunConfigService()),
        launcher_service=(launcher if launcher is not None
                          else FakeLauncherService()),
        monitor_service=(monitor if monitor is not None
                         else _MonitorShellFake()),
        monitor_launcher=(launcher if launcher is not None
                          else FakeLauncherService()),
    )


# =====================================================================
# Pilot helpers
# =====================================================================

def _plain(content) -> str:
    """Plain text of a Static's content (cells may carry rich Text)."""
    return content.plain if isinstance(content, Text) else str(content)


def _label_text(screen, selector) -> str:
    return _plain(screen.query_one(selector, Static).content)


def _toast_messages(app):
    """The active notification messages (the toast assertions)."""
    return [notification.message for notification in app._notifications]


async def _open_run_config(pilot, app):
    """Push the run-config screen and deterministically await its load."""
    app.push_screen(app.build_run_config_screen())
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()


async def _settle(pilot, app, rounds=3):
    """Await sequential worker->handler chains (each round: workers,
    then the messages they posted)."""
    for _ in range(rounds):
        await app.workers.wait_for_complete()
        await pilot.pause()


# =====================================================================
# Task 1 — the screen shell (both grids, pickers, params, preview)
# =====================================================================

async def test_screen_composes_two_columns_at_both_grids():
    """The two-column split composes at 120x40 AND 80x24 with both bars."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        assert isinstance(screen, RunConfigScreen)
        assert list(screen.query(TopMenuBar)), "the top bar renders"
        assert list(screen.query(BottomBar)), "the bottom bar renders"
        picker = screen.query_one("#cfg-picker-col")
        params = screen.query_one("#cfg-params-col")
        assert picker.region.width >= 50, (
            "the picker column takes ~56 cells at 120 "
            f"(is {picker.region.width})")
        assert params.region.width >= 50, (
            "the params column takes the remainder "
            f"(is {params.region.width})")
        assert screen.query_one("#cfg-preview-line", Static) is not None

    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        picker = screen.query_one("#cfg-picker-col")
        params = screen.query_one("#cfg-params-col")
        assert 32 <= picker.region.width <= 42, (
            "the picker column narrows to ~38 cells at 80 "
            f"(is {picker.region.width})")
        assert params.region.width >= 30, (
            f"the params column keeps the remainder at 80 "
            f"(is {params.region.width})")


async def test_status_line_renders_selection_counts():
    """The title row's right segment carries the marked counts."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        assert _label_text(screen, "#cfg-status-line") == (
            CFG_STATUS_LINE.format(
                n=1, models_total=len(run_service.entries.model_entries),
                m=1, tasks_total=len(run_service.entries.dataset_entries),
            ))
        # the picker title carries the SAME marked/total counts
        assert _label_text(screen, "#cfg-picker-title") == (
            CFG_PICKER_MODELS.format(n=1, total=4) + f" · [m] {SEL_SWITCH_LABEL}")


async def test_m_flips_picker_kind_and_title():
    """m flips models <-> datasets; the title flips with it (D-01)."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        assert _label_text(screen, "#cfg-picker-title") == (
            CFG_PICKER_MODELS.format(n=0, total=4) + f" · [m] {SEL_SWITCH_LABEL}")
        await pilot.press("m")
        await pilot.pause()
        assert _label_text(screen, "#cfg-picker-title") == (
            CFG_PICKER_DATASETS.format(n=0, total=2) + f" · [m] {NAV_LABEL_SELECTION}")
        await pilot.press("m")
        await pilot.pause()
        assert _label_text(screen, "#cfg-picker-title") == (
            CFG_PICKER_MODELS.format(n=0, total=4) + f" · [m] {SEL_SWITCH_LABEL}")


async def test_slash_focuses_filter_and_narrows_rows():
    """The / grammar: focus the filter Input, type, the count narrows."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        picker = screen.query_one("#cfg-picker", SelectionList)
        assert len(picker.options) == 4
        await pilot.press("slash")
        await pilot.pause()
        assert app.focused is screen.query_one("#cfg-filter", Input)
        for char in "model-a":
            await pilot.press(char)
        await pilot.pause()
        assert screen.query_one("#cfg-filter", Input).value == "model-a"
        assert _label_text(screen, "#cfg-filter-count") == (
            SEL_FILTER_COUNT.format(n=1, total=4))
        assert len(picker.options) == 1, "the filtered list narrows"
        # esc clears the filter and refocuses the picker
        await pilot.press("escape")
        await pilot.pause()
        assert screen.query_one("#cfg-filter", Input).value == ""
        assert len(picker.options) == 4
        assert app.focused is picker


async def test_space_marks_model_and_persists_roundtrip():
    """space marks the cursor's model, persists through the service, and
    a fresh screen over the SAME fake reloads the mark (XDG round-trip
    proven at the seam — the fake's load_state is the persisted truth)."""
    run_service = FakeRunConfigService()
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        picker = screen.query_one("#cfg-picker", SelectionList)
        assert app.focused is picker, "the picker takes the initial focus"
        await pilot.press("space")
        await _settle(pilot, app)
        assert run_service.saved_specs, "the mark persisted through save"
        saved = run_service.saved_specs[-1]
        assert saved.models == ("model-a",), (
            "space marks the cursor's row (the first model)")
        assert _label_text(screen, "#cfg-picker-title") == (
            CFG_PICKER_MODELS.format(n=1, total=4) + f" · [m] {SEL_SWITCH_LABEL}")
        await pilot.press("m")
        await pilot.pause()
        await pilot.press("space")
        await _settle(pilot, app)
        assert run_service.saved_specs[-1].tasks == ("task-1",)
        assert _label_text(screen, "#cfg-picker-title") == (
            CFG_PICKER_DATASETS.format(n=1, total=2) + f" · [m] {NAV_LABEL_SELECTION}")

    # the round-trip: a NEW screen over the same service reloads the marks
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        assert _label_text(screen, "#cfg-status-line") == (
            CFG_STATUS_LINE.format(n=1, models_total=4, m=1, tasks_total=2))


async def test_space_on_disabled_custom_warns_never_marks():
    """A disabled custom row warns (the inherited vocabulary) and never
    joins the spec — never silent (SEL-01 boundary)."""
    run_service = FakeRunConfigService()
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        # cust-off is the 4th row (registry order + appended customs)
        for _ in range(3):
            await pilot.press("down")
        await pilot.pause()
        await pilot.press("space")
        await pilot.pause()
        warnings = [message for message in _toast_messages(app)
                    if SEL_DISABLED_MARK_WARNING.format(key="cust-off")
                    in message]
        assert warnings, "the disabled row warns through the toast"
        assert all(spec.models == () for spec in run_service.saved_specs), (
            "a disabled custom must never join the spec")


async def test_marked_then_disabled_custom_leaves_spec_at_load():
    """WR-07: a custom marked in a previous session and disabled since
    (management overlay) must LEAVE the loaded spec at mount. Before:
    the row rendered UNMARKED (mark suppression) while the status-line
    counts, the preview, and the launch enumeration all included it —
    and both mark paths refuse disabled rows, so it could never be
    unmarked from the UI (the only escape was re-enabling the entry).
    After: the sanitized spec agrees with the rendered marks, and the
    first preview-worker save persists the sanitized spec (XDG
    self-heals). Both axes: models AND dataset customs."""
    entries = PickerEntries(
        model_entries=tuple(_FAKE_MODELS),
        dataset_entries=tuple(_FAKE_DATASETS)
        + (_dataset_entry("cust-ds-off"),),
        custom_status={**_FAKE_CUSTOM_STATUS,
                       "cust-ds-off": {"custom": True, "enabled": False}},
    )
    run_service = FakeRunConfigService(
        entries=entries,
        spec=RunSpec(models=("cust-off", "model-a"),
                     tasks=("cust-ds-off", "task-1")))
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        assert screen._spec.models == ("model-a",), (
            "the marked-then-disabled custom model must leave the spec "
            "at load — the render, the counts, and the launch must "
            "agree"
        )
        assert screen._spec.tasks == ("task-1",), (
            "the same holds for a marked-then-disabled custom dataset"
        )
        # the status line counts the SANITIZED selection (render ==
        # spec): 1 model of 4 rows, 1 task of 3 rows
        assert _label_text(screen, "#cfg-status-line") == (
            CFG_STATUS_LINE.format(n=1, models_total=4, m=1, tasks_total=3))
        # the first save through the preview worker persists the
        # sanitized spec — the stale XDG state self-heals
        assert all(
            "cust-off" not in spec.models
            and "cust-ds-off" not in spec.tasks
            for spec in run_service.saved_specs), (
            "the sanitized spec is what persists"
        )


async def test_params_defaults_render():
    """Every CFG-01 field renders its default: seeds 42,43,44; the
    choice rows 'none ▾'; absent values '—'; the subset default; the
    dirs defaults; the cache placeholder. The storage-root inputs
    default EMPTY with their prompt hints (the D-19 './datasets'
    display default retired with the live flags, 261014-c2l)."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        assert screen.query_one("#cfg-input-seeds", Input).value == "42,43,44"
        assert _label_text(screen, "#cfg-value-peft") == "none ▾"
        assert _label_text(screen, "#cfg-value-variant") == "none ▾"
        assert screen.query_one("#cfg-input-curve", Input).value == ""
        from tui.strings import CFG_SUBSET_OFF_WITH_PATH

        assert _label_text(screen, "#cfg-subset-value") == (
            CFG_SUBSET_OFF_WITH_PATH.format(
                path="pipeline/eval_subsets.json")), (
            "the OFF copy renders wholly through the strings.py "
            "constant (WR-08 — no inline CJK punctuation composition)"
        )
        assert screen.query_one("#cfg-input-epochs", Input).value == ""
        assert screen.query_one("#cfg-input-ebs", Input).value == ""
        from tui.strings import (
            CFG_BATCH_SIZE_DEFAULT,
            CFG_FIELD_BATCH_SIZE,
        )

        batch_size = screen.query_one("#cfg-input-batch-size", Input)
        assert batch_size.value == "", (
            "the batch field renders EMPTY at defaults (261023-abu — an "
            "empty field threads NO --batch_size)"
        )
        assert _plain(batch_size.placeholder) == CFG_BATCH_SIZE_DEFAULT
        assert _label_text(
            screen, "#cfg-label-batch-size") == CFG_FIELD_BATCH_SIZE
        assert screen.query_one("#cfg-input-output-root", Input).value == (
            "./finetuned")
        dataset_root = screen.query_one("#cfg-input-dataset-root", Input)
        assert dataset_root.value == ""
        assert _plain(dataset_root.placeholder) == CFG_DATASET_ROOT_DEFAULT
        model_root = screen.query_one("#cfg-input-model-root", Input)
        assert model_root.value == ""
        assert _plain(model_root.placeholder) == CFG_MODEL_ROOT_DEFAULT
        assert _label_text(screen, "#cfg-label-model-root") == (
            CFG_FIELD_MODEL_ROOT)
        cache = screen.query_one("#cfg-input-cache", Input)
        assert cache.value == ""
        assert _plain(cache.placeholder) == CFG_CACHE_DEFAULT
        # the field labels render at the design grid
        assert _label_text(screen, "#cfg-label-peft") == CFG_FIELD_PEFT
        assert _label_text(screen, "#cfg-label-variant") == CFG_FIELD_VARIANT


async def test_params_input_values_render_in_export():
    """The params Input VALUES are visible in the rendered output (the
    11-UAT empty-bar phenomenon): export_screenshot() must carry the
    seeds value and the dirs defaults as text — a height-1 row clipping
    a default (bordered, height-3) Input shows only its top border and
    silently hides the value the operator typed/set. The storage-root
    rows default empty (261014-c2l) and their PROMPT HINTS render in
    the placeholder's place."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await _settle(pilot, app)
        svg = app.export_screenshot()
        assert "42,43,44" in svg, (
            "the seeds value must render on the params row (the 11-UAT "
            "empty-bar bug: the Input's value row is clipped away)")
        assert "./finetuned" in svg
        assert "模型根" in svg, (
            "the model-root row's label renders (261014-c2l)"
        )
        assert svg.count("—（默认") == 5, (
            "ALL FIVE prompt hints render in the placeholder's place "
            "(the SVG encodes their inner space as &#160;, so the "
            "contiguous constant is pinned by its stable prefix — five "
            "hits = the model-root, dataset-root, and log-dir rows "
            "(261014-f4w) + the 16-04 GPUs default-assignment row "
            "(WR-03 copy) + the 261023-abu batch-size dynamic-scaling "
            "row, the same CFG_CACHE_DEFAULT grammar)"
        )
        assert "./datasets" not in svg, (
            "the retired D-19 './datasets' display default no longer "
            "renders — the empty value row is the honest unset state"
        )


async def test_model_root_input_threads_absolute_flag_into_argv():
    """261014-c2l: typing a model root into #cfg-input-model-root
    composes a spec whose service-side argv carries --model_root as the
    RESOLVED ABSOLUTE string (an absolute input passes through
    verbatim), while the untouched dataset-root field contributes no
    --dataset_root element — the persisted-spec path over the REAL
    compose_argv (the fake's compose_argv is display-only, so the
    service module is the argv authority here)."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        model_root = screen.query_one("#cfg-input-model-root", Input)
        model_root.value = "/mnt/storage"
        await _settle(pilot, app)
        saved = run_service.saved_specs[-1]
        assert saved.model_root == "/mnt/storage", (
            "the typed model root persists into the composed spec"
        )
        assert saved.dataset_root is None, (
            "the untouched dataset-root field contributes nothing"
        )
        argv = run_config_service.compose_argv(saved)
        assert argv[argv.index("--model_root") + 1] == "/mnt/storage", (
            "the service-side argv threads --model_root as the "
            "resolved absolute string"
        )
        assert "--dataset_root" not in argv


async def test_batch_size_input_threads_flag_and_invalid_problem():
    """261023-abu: typing 8 into #cfg-input-batch-size composes a spec
    whose service-side DISPATCH argv carries --batch_size 8 (the
    model-root typing idiom over the dispatch composer); typing 0
    raises batch_size_invalid, which renders through the preview
    problems path's GENERIC code+detail fallback exactly like
    epochs_invalid/ebs_invalid (no copy mapping, by design), and the
    invalid raw never persists (last-valid governs)."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        batch_input = screen.query_one("#cfg-input-batch-size", Input)
        batch_input.value = "8"
        await _settle(pilot, app)
        saved = run_service.saved_specs[-1]
        assert saved.batch_size == 8, (
            "the typed batch size persists into the composed spec"
        )
        argv = run_config_service.compose_dispatch_argv(saved)
        assert argv[argv.index("--batch_size") + 1] == "8", (
            "the threaded dispatch argv carries --batch_size 8"
        )
        # invalid: the mirror fires, the problem surfaces through the
        # generic fallback, the raw never persists
        batch_input.value = "0"
        await _settle(pilot, app)
        assert run_service.saved_specs[-1].batch_size == 8, (
            "an invalid field contributes no partial (last-valid governs)"
        )
        await pilot.press("p")
        await pilot.pause()
        from tui.screens.run_config import PreviewModal

        assert isinstance(app.screen, PreviewModal)
        log = app.screen.query_one("#cfg-preview-log")
        joined = "\n".join(
            line.text for line in log.lines).replace("\n", "")
        assert "batch_size_invalid: 0" in joined, (
            "the machine problem renders through the generic "
            "code+detail fallback (the epochs_invalid/ebs_invalid "
            "shape — no copy mapping, by design)"
        )


async def test_params_labels_shorten_at_80_columns():
    """The 80-col degradations: eff_batch_size + the short dirs title."""
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        from tui.strings import (
            CFG_DIRS_TITLE_SHORT,
            CFG_FIELD_EBS_SHORT,
        )
        assert _label_text(screen, "#cfg-label-ebs") == CFG_FIELD_EBS_SHORT
        assert _label_text(screen, "#cfg-dirs-title") == CFG_DIRS_TITLE_SHORT


async def test_preview_line_renders_and_updates_on_mark():
    """The preview line renders the fake's counts and re-renders when a
    mark changes (the run-id-tagged worker path)."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        assert _label_text(screen, "#cfg-preview-line") == (
            CFG_PREVIEW_LINE.format(
                models=1, tasks=1, seeds=3, cells=3))
        # the cursor sits on model-a (the marked first row): space
        # UN-marks it — the preview flips to the empty-selection problem
        await pilot.press("space")
        await _settle(pilot, app)
        assert _label_text(screen, "#cfg-preview-line") == (
            CFG_PREVIEW_PROBLEMS.format(n=1))
        # re-mark: the counts return (the loaded spec already carries
        # task-1 — 1 model x 1 task x 3 seeds = 3 cells)
        await pilot.press("space")
        await _settle(pilot, app)
        assert _label_text(screen, "#cfg-preview-line") == (
            CFG_PREVIEW_LINE.format(models=1, tasks=1, seeds=3, cells=3))


async def test_preview_line_empty_selection_problem():
    """No selection: the problems header renders (the [p] modal owns
    the numbered list)."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        assert _label_text(screen, "#cfg-preview-line") == (
            CFG_PREVIEW_PROBLEMS.format(n=1))
        assert CFG_EMPTY_SELECTION_PROBLEM not in _label_text(
            screen, "#cfg-preview-line"), (
            "the numbered list lives in the [p] modal, not the line")


async def test_probe_hint_renders_under_variant_probe():
    """变体=probe renders the ⚠ hint naming the frozen intersection —
    via a RadioSet choice (Task 3 lands the modal; here the default
    mount path proves the hint row exists and stays hidden by default).
    """
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        hint = screen.query_one("#cfg-hint-variant-probe", Static)
        assert not hint.display, "the probe hint stays hidden at none"


# =====================================================================
# Task 2 — the [p] modal + the launch-confirmation pipeline + launch toasts
# =====================================================================

async def test_preview_modal_renders_argv_and_problems():
    """[p]: the dimension summary, the same-source note, the LIST argv
    VERBATIM, and the numbered problems when any. 16-04 lockstep: the
    verbatim argv is the DISPATCH composer's output (every slot-4
    launch composes run_sweep_shard --mode dispatch, UI-SPEC
    auto-default #9) — asserted space-flat because the real argv wraps
    across RichLog lines at the modal width."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("p")
        await pilot.pause()
        from tui.screens.run_config import PreviewModal

        assert isinstance(app.screen, PreviewModal)
        log = app.screen.query_one("#cfg-preview-log")
        joined = "\n".join(line.text for line in log.lines)
        assert CFG_PREVIEW_LINE.format(
            models=1, tasks=1, seeds=3, cells=3) in joined
        assert CFG_PREVIEW_NOTE in joined
        expected_argv = CFG_ARGV_LABEL + " ".join(str(part) for part in (
            run_service.compose_dispatch_argv(
                RunSpec(models=("model-a",), tasks=("task-1",)))))
        flat = "".join(line.text for line in log.lines).replace(" ", "")
        assert expected_argv.replace(" ", "") in flat, (
            "the [p] modal shows the dispatch argv verbatim"
        )
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, RunConfigScreen)


async def test_preview_modal_numbers_problems():
    """A problems preview renders the numbered list in the [p] modal."""
    run_service = FakeRunConfigService()
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("p")
        await pilot.pause()
        from tui.screens.run_config import PreviewModal
        from tui.strings import CFG_EMPTY_SELECTION_PROBLEM as COPY

        assert isinstance(app.screen, PreviewModal)
        log = app.screen.query_one("#cfg-preview-log")
        joined = "\n".join(line.text for line in log.lines)
        assert CFG_PREVIEW_PROBLEMS.format(n=1) in joined
        assert f"1. {COPY}" in joined
        assert CFG_ARGV_LABEL not in joined, (
            "a problems preview composes no argv")


async def test_gate_happy_path_confirms_and_launches():
    """The full non-E2' happy path: enter -> enumeration clean -> env ok
    -> ConfirmModal with the summary -> enter -> launch_spec(spec) ->
    the success toast (the D-13 auto-nav half lands in 11-07)."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(summary=GateSummary(
        models=1, tasks=1, seeds=3, cells=3, output_root="./finetuned",
        is_e2x=False, expected_phrase="finetuned"))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")   # the picker holds focus: the gate
        await _settle(pilot, app, rounds=4)
        from tui.screens.selection import ConfirmModal, LaunchConfirmModal

        assert isinstance(app.screen, ConfirmModal), (
            "the non-E2' gate lands on the summary confirm")
        assert isinstance(app.screen, LaunchConfirmModal), (
            "the gate confirm is the LAUNCH variant (EHC-2)")
        message = str(app.screen._message)
        from tui.strings import LNC_GATE_CONFIRM, LNC_GATE_SUMMARY

        assert LNC_GATE_SUMMARY.format(
            models=1, tasks=1, seeds=3, cells=3,
            output_root="./finetuned") in message
        assert LNC_GATE_CONFIRM in message, (
            "the confirm copy names the [y] keycap")
        # EHC-2: a stray double-enter can NEVER launch — the enter
        # after the gate-opening one lands on the documented no-op
        await pilot.press("enter")
        await _settle(pilot, app, rounds=3)
        assert launcher.launch_calls == [], (
            "enter must never pass a launch confirmation (EHC-2)")
        assert isinstance(app.screen, ConfirmModal), (
            "the inert enter leaves the modal up")
        await pilot.press("y")
        await _settle(pilot, app, rounds=3)
        assert len(launcher.launch_calls) == 1, "y launches exactly once"
        spec, phrase = launcher.launch_calls[0]
        assert spec.models == ("model-a",)
        assert phrase is None, "a non-E2' launch carries no phrase"
        toasts = _toast_messages(app)
        from tui.strings import LNC_LAUNCH_TOAST

        assert any(LNC_LAUNCH_TOAST.format(
            cells=3, output_root="./finetuned") in toast
            for toast in toasts), toasts


async def test_gate_single_gpu_busy_refuses_naming_the_running_root():
    """The capacity stage (16-03, D16-10 — the EHC-3 stage replaced in
    place): with the capacity seam reporting a structured block, the
    gate refuses at the problems stage rendering the AMENDED bilingual
    copy naming the running root AND the counts (workers + gpu count)
    — BEFORE the env preflight, any confirm, or the launch; the y key
    is never even reachable."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(single_gpu_blocked=GpuCapacityBlock(
        roots=("/repo/finetuned-live",), requested_workers=1,
        gpu_count=1))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        from tui.screens.run_config import ProblemsModal

        assert isinstance(app.screen, ProblemsModal), (
            "the capacity pre-check blocks before any confirm"
        )
        log = app.screen.query_one("#cfg-problems-log")
        joined = "\n".join(line.text for line in log.lines)
        from tui.strings import LNC_SINGLE_GPU_BLOCKED

        assert LNC_SINGLE_GPU_BLOCKED.format(workers=1,
                                             roots="/repo/finetuned-live",
                                             n=1) in (
            joined.replace("\n", "")), (
            "the refusal renders the amended bilingual copy naming the "
            "root AND the counts"
        )
        assert launcher.env_calls == 0, "blocked before the env preflight"
        assert launcher.confirm_calls == [], "blocked before the confirm"
        assert launcher.launch_calls == [], "nothing ever spawns"


async def test_gate_fakes_without_the_single_gpu_seam_never_block():
    """EHC-3 fake tolerance (the 11-03 precedent): a launcher WITHOUT
    the single_gpu_launch_blocked method runs the full gate normally —
    the tolerant getattr seam reads as never blocked."""
    # a fake class with the seam method ABSENT entirely (the attribute
    # deleted off the class — getattr then reads None)
    seamless = type(
        "Seamless", (FakeLauncherService,),
        dict(FakeLauncherService.__dict__))
    del seamless.single_gpu_launch_blocked
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = seamless(summary=GateSummary(
        models=1, tasks=1, seeds=3, cells=3, output_root="./finetuned",
        is_e2x=False, expected_phrase="finetuned"))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        from tui.screens.selection import ConfirmModal

        assert isinstance(app.screen, ConfirmModal), (
            "a seam-less fake reaches the confirm normally"
        )


async def test_gate_problems_blocked_launch_never_called():
    """Enumeration problems: ONLY the problems modal opens, launch_spec
    is never called (nothing else opens)."""
    run_service = FakeRunConfigService()
    launcher = FakeLauncherService()
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        from tui.screens.run_config import ProblemsModal

        assert isinstance(app.screen, ProblemsModal)
        log = app.screen.query_one("#cfg-problems-log")
        joined = "\n".join(line.text for line in log.lines)
        assert CFG_PREVIEW_PROBLEMS.format(n=1) in joined
        assert launcher.env_calls == 0, (
            "problems block BEFORE the env preflight")
        assert launcher.launch_calls == []


async def test_gate_live_root_refusal_names_the_root():
    """CR-02: a launch into an already-LIVE output root is refused at
    the problems stage naming the root — the operator must kill/detach
    or pick a different root first; the gate never reaches the env
    preflight, the confirm, or the spawn."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    live_root = str(Path("./finetuned").resolve())
    launcher = FakeLauncherService(live=(live_root,))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        from tui.screens.run_config import ProblemsModal

        assert isinstance(app.screen, ProblemsModal)
        log = app.screen.query_one("#cfg-problems-log")
        joined = "\n".join(line.text for line in log.lines)
        assert live_root in joined.replace("\n", ""), (
            "the refusal names the live output root"
        )
        assert launcher.env_calls == 0, "blocked before the env preflight"
        assert launcher.confirm_calls == [], "blocked before the confirm"
        assert launcher.launch_calls == [], "nothing ever spawns"


async def test_gate_live_root_precheck_reads_repo_root_basis_any_cwd(
        monkeypatch, tmp_path):
    """WR-01 (screen side, gap #2): the CR-02 live-root pre-check reads
    the ``resolve_dirs`` basis — a RELATIVE output_root composed while
    the TUI process CWD is outside the repo still names and blocks the
    REPO_ROOT key the argv will thread (``output_root_abs``, D-14); no
    phantom ``{cwd}``-rooted key slips past the gate to a second sweep
    into the live root."""
    repo_root = Path(__file__).resolve().parents[2]
    repo_key = str((repo_root / "finetuned").resolve())
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",), output_root="finetuned"))
    launcher = FakeLauncherService(live=(repo_key,))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        monkeypatch.chdir(tmp_path)   # CWD != REPO_ROOT at gate time
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        from tui.screens.run_config import ProblemsModal

        assert isinstance(app.screen, ProblemsModal), (
            "the pre-check FIRES on the REPO_ROOT basis key — a "
            "{cwd}-rooted key would slip past to the confirm"
        )
        log = app.screen.query_one("#cfg-problems-log")
        joined = "\n".join(line.text for line in log.lines)
        assert repo_key in joined.replace("\n", ""), (
            "the refusal names the REPO_ROOT-basis live key"
        )
        assert launcher.env_calls == 0, "blocked before the env preflight"
        assert launcher.launch_calls == [], "nothing ever spawns"


# =====================================================================
# Phase 16 (16-04, TUI-02) — the multi-GPU dispatch params section,
# the three mirror problems, and the capacity-stage threading
# =====================================================================


class _RecordingCapacityLauncher(FakeLauncherService):
    """16-04: records the requested_workers the gate threads into the
    capacity seam (the spec-composition evidence)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.requested_workers_calls: list[int] = []

    def single_gpu_launch_blocked(self, requested_workers=1):
        self.requested_workers_calls.append(requested_workers)
        return self._single_gpu_blocked


async def test_gate_capacity_stage_threads_spec_workers_and_refuses():
    """D16-10 (16-04): the capacity stage threads requested_workers from
    the COMPOSED spec — a typed workers 2 reaches the seam — and an
    over-capacity block refuses at the problems stage with the amended
    copy naming roots AND the counts; the within-capacity leg passes
    the stage through env preflight to the confirm (the chain-order
    evidence style — problems -> capacity -> env -> confirm, zero
    weakening)."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))

    # leg 1 — within capacity: the typed workers reach the seam and the
    # chain passes the stage to env preflight then the confirm face
    recorder = _RecordingCapacityLauncher(summary=GateSummary(
        models=1, tasks=1, seeds=3, cells=3, output_root="./finetuned",
        is_e2x=False, expected_phrase="finetuned"))
    app = _app(run_service=run_service, launcher=recorder)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        app.screen.query_one("#cfg-input-workers", Input).value = "2"
        await _settle(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        from tui.screens.selection import ConfirmModal

        assert recorder.requested_workers_calls[-1] == 2, (
            "the capacity stage threads the composed spec's workers"
        )
        assert recorder.env_calls == 1, (
            "within capacity the chain passes the stage to env preflight"
        )
        assert isinstance(app.screen, ConfirmModal), (
            "the within-capacity leg reaches the confirm face"
        )

    # leg 2 — over capacity: the problems stage renders the amended
    # copy naming the roots + the counts, BEFORE env or any confirm
    blocked = _RecordingCapacityLauncher(
        single_gpu_blocked=GpuCapacityBlock(
            roots=("/repo/finetuned-live",), requested_workers=2,
            gpu_count=2))
    app = _app(run_service=run_service, launcher=blocked)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        app.screen.query_one("#cfg-input-workers", Input).value = "2"
        await _settle(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        from tui.screens.run_config import ProblemsModal

        assert isinstance(app.screen, ProblemsModal), (
            "the over-capacity leg refuses at the problems stage"
        )
        assert blocked.requested_workers_calls[-1] == 2
        log = app.screen.query_one("#cfg-problems-log")
        joined = "\n".join(
            line.text for line in log.lines).replace("\n", "")
        from tui.strings import LNC_SINGLE_GPU_BLOCKED

        assert LNC_SINGLE_GPU_BLOCKED.format(
            roots="/repo/finetuned-live", workers=2, n=2) in joined, (
            "the refusal names the live root AND the counts"
        )
        assert blocked.env_calls == 0, "blocked before the env preflight"
        assert blocked.confirm_calls == [], "blocked before the confirm"
        assert blocked.launch_calls == [], "nothing ever spawns"


async def test_mgpu_section_renders_live_default_and_placeholder():
    """UI-SPEC C.1 (16-04): the params pane carries the multi-GPU
    dispatch section between the effective_batch_size row and the dirs
    title — the workers Input holding the LIVE default value "1" (a
    VALUE, never a placeholder), the GPUs Input EMPTY with the
    CFG_GPUS_DEFAULT placeholder, and the dim CFG_MGPU_HINT row;
    existing classes only (zero new TCSS for slot-4)."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        from tui.strings import (
            CFG_FIELD_GPUS,
            CFG_FIELD_WORKERS,
            CFG_GPUS_DEFAULT,
            CFG_MGPU_HINT,
            CFG_MGPU_TITLE,
        )

        assert _label_text(screen, "#cfg-mgpu-title") == CFG_MGPU_TITLE
        assert _label_text(
            screen, "#cfg-label-workers") == CFG_FIELD_WORKERS
        assert _label_text(screen, "#cfg-label-gpus") == CFG_FIELD_GPUS
        workers = screen.query_one("#cfg-input-workers", Input)
        assert workers.value == "1", (
            "the workers default is a LIVE value, never a placeholder"
        )
        assert workers.placeholder == "", (
            "no placeholder grammar on the workers field (Pitfall 8)"
        )
        gpus = screen.query_one("#cfg-input-gpus", Input)
        assert gpus.value == "", (
            "values are never guessed into the GPUs field"
        )
        assert gpus.placeholder == CFG_GPUS_DEFAULT
        assert _label_text(screen, "#cfg-hint-mgpu") == CFG_MGPU_HINT
        # the section sits BETWEEN the EBS row and the DIRS title
        order = [node.id for node in screen.query(
            "#cfg-label-ebs, #cfg-mgpu-title, #cfg-dirs-title")]
        assert order == ["cfg-label-ebs", "cfg-mgpu-title",
                         "cfg-dirs-title"], (
            "the section lands between the EBS row and the dirs title"
        )


async def test_mgpu_section_short_title_swaps_at_narrow_grid():
    """The 80-col degradation swaps in the short section title (the
    CFG_DIRS_TITLE pair mechanism reused verbatim)."""
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        await _open_run_config(pilot, app)
        from tui.strings import CFG_MGPU_TITLE_SHORT

        assert _label_text(
            app.screen, "#cfg-mgpu-title") == CFG_MGPU_TITLE_SHORT


async def test_mgpu_fields_thread_into_spec_last_valid_governs():
    """Spec threading (16-04): typing workers 2 + GPUs 1,0 composes a
    spec with workers 2 and the sorted/deduped gpus ("0","1"); garbage
    in a field raises its mirror and contributes NO partial (the
    last-valid value governs, the invalid raw never persists); the
    DEFAULTS spec persists workers 1 / gpus None (the child's
    first-workers default at launch — WR-03; never a resolved list,
    Pitfall 8)."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        screen.query_one("#cfg-input-workers", Input).value = "2"
        screen.query_one("#cfg-input-gpus", Input).value = "1,0"
        await _settle(pilot, app)
        saved = run_service.saved_specs[-1]
        assert saved.workers == 2
        assert saved.gpus == ("0", "1"), (
            "the typed list normalizes sorted + deduped (house rule)"
        )
        # garbage workers: the mirror fires, the invalid raw NEVER
        # persists — the last-valid value governs
        screen.query_one("#cfg-input-workers", Input).value = "x"
        await _settle(pilot, app)
        assert run_service.saved_specs[-1].workers == 2, (
            "an invalid field contributes no partial (last-valid governs)"
        )
        assert run_service.saved_specs[-1].gpus == ("0", "1")
        # a CLEARED field follows the screen's established
        # last-valid-governs rule (the Phase-11 parse_params semantics
        # — identical to epochs/curve/ebs; 16-04 changes nothing here)
        screen.query_one("#cfg-input-gpus", Input).value = ""
        await _settle(pilot, app)
        assert run_service.saved_specs[-1].gpus == ("0", "1")

    # the DEFAULTS leg (Pitfall 8): a fresh screen that never typed a
    # list persists workers 1 / gpus None — all-detected, never a
    # resolved list guessed into the state document
    defaults_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    app2 = _app(run_service=defaults_service)
    async with app2.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app2)
        saved = defaults_service.saved_specs[-1]
        assert saved.workers == 1
        assert saved.gpus is None, (
            "a defaults spec persists all-detected as None (Pitfall 8)"
        )


async def test_mgpu_mirror_problems_render_numbered():
    """UI-SPEC C.3 (16-04): the three mirror problems render as
    numbered problem lines through _problem_line with the verbatim
    copy — workers 需为…/GPUs 需为…/workers (…) 超过 … (collect-all;
    the seeds/curve precedent)."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        # leg A — both field mirrors at once (collect-all)
        screen.query_one("#cfg-input-workers", Input).value = "x"
        screen.query_one("#cfg-input-gpus", Input).value = "0,a"
        await _settle(pilot, app)
        await pilot.press("p")
        await pilot.pause()
        from tui.screens.run_config import PreviewModal
        from tui.strings import (
            CFG_GPUS_INVALID_PROBLEM,
            CFG_WORKERS_INVALID_PROBLEM,
        )

        assert isinstance(app.screen, PreviewModal)
        log = app.screen.query_one("#cfg-preview-log")
        joined = "\n".join(
            line.text for line in log.lines).replace("\n", "")
        assert f"1. {CFG_WORKERS_INVALID_PROBLEM.format(value='x')}" in (
            joined)
        assert f"2. {CFG_GPUS_INVALID_PROBLEM.format(value='0,a')}" in (
            joined)
        await pilot.press("escape")
        await pilot.pause()
        # leg B — the short-side arity mirror (both legs parse clean)
        screen = app.screen
        screen.query_one("#cfg-input-workers", Input).value = "3"
        screen.query_one("#cfg-input-gpus", Input).value = "0,1"
        await _settle(pilot, app)
        await pilot.press("p")
        await pilot.pause()
        from tui.strings import CFG_WORKERS_EXCEED_GPUS_PROBLEM

        assert isinstance(app.screen, PreviewModal)
        log = app.screen.query_one("#cfg-preview-log")
        joined = "\n".join(
            line.text for line in log.lines).replace("\n", "")
        expected = (
            f"1. {CFG_WORKERS_EXCEED_GPUS_PROBLEM.format(workers=3, n=2)}")
        assert expected in joined, (
            "the structured (workers, gpu_count) pair formats the copy"
        )


async def test_preview_modal_dispatch_argv_defaults_shape():
    """[p] (16-04): the verbatim argv is the DISPATCH composer's output
    (the same composer the launcher routes through — one composition
    source, zero drift): run_sweep_shard.py --mode dispatch with
    --workers ALWAYS explicit (the A2 pin) and NO --gpus element at
    defaults (Pitfall 8); a typed GPU list threads --gpus present-only
    (D-12 parity)."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("p")
        await pilot.pause()
        from tui.screens.run_config import PreviewModal

        assert isinstance(app.screen, PreviewModal)
        log = app.screen.query_one("#cfg-preview-log")
        flat = "".join(line.text for line in log.lines).replace(" ", "")
        assert "run_sweep_shard.py" in flat
        assert "--modedispatch" in flat, (
            "every slot-4 launch composes the dispatch argv (auto-#9)"
        )
        assert "--workers1" in flat, (
            "the A2 pin: --workers is always explicit, even at 1"
        )
        assert "--gpus" not in flat, (
            "a defaults spec composes ZERO --gpus elements (Pitfall 8)"
        )
        await pilot.press("escape")
        await pilot.pause()
        # a typed GPU list threads --gpus present-only
        app.screen.query_one("#cfg-input-gpus", Input).value = "0,1"
        await _settle(pilot, app)
        await pilot.press("p")
        await pilot.pause()
        assert isinstance(app.screen, PreviewModal)
        log = app.screen.query_one("#cfg-preview-log")
        flat = "".join(line.text for line in log.lines).replace(" ", "")
        assert "--gpus0,1" in flat


# =====================================================================
# Phase 16 (16-04, Task 2) — the dispatch-plan preview line on both
# confirm faces + the gate-order extension
# =====================================================================


class _StageOrderLauncher(FakeLauncherService):
    """16-04 gate-order evidence: records the stage seams in fire order
    (capacity -> env -> confirm-data) beside the FakeLauncherService
    outcomes."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stage_events: list[str] = []

    def single_gpu_launch_blocked(self, requested_workers=1):
        self.stage_events.append("capacity")
        return self._single_gpu_blocked

    def env_preflight(self, kernels=None):
        self.stage_events.append("env")
        return super().env_preflight(kernels)

    def gate_confirm_data(self, spec):
        self.stage_events.append("confirm")
        return super().gate_confirm_data(spec)


async def test_confirm_face_renders_dispatch_plan_line():
    """UI-SPEC C.5 (16-04): _GateConfirmModal renders
    LNC_GATE_DISPATCH_LINE DIRECTLY above the pair list with workers/
    GPUs/cells filled from GateSummary (the modal renders, never
    computes). 16-05 Rule-1 lockstep: the line moved OUT of
    #cfg-gate-log into its own Static — at the design grid the ~50-cell
    zh/en wording wraps to 2 visual rows inside the scroll-bounded
    log, so the 14-logical-line content outgrew the 14-row bound and
    RichLog auto_scroll clipped the line's own top half (probed
    scroll_y=1; only the wrap fragment rendered). The Static wraps and
    grows outside the bound; the log carries 12 capped pairs + 1 total
    line = 13 rows <= the 14-row UX-5 bound."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(summary=GateSummary(
        models=1, tasks=1, seeds=3, cells=3, output_root="./finetuned",
        is_e2x=False, expected_phrase="finetuned",
        pairs=tuple((f"model-{index:02d}", f"task-{index:02d}")
                    for index in range(15)),
        workers=2, gpus_display="0,1"))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        from textual.widgets import RichLog

        from tui.screens.run_config import _GateConfirmModal
        from tui.strings import (
            LNC_GATE_DISPATCH_LINE,
            LNC_GATE_PAIRS_MORE,
        )

        assert isinstance(app.screen, _GateConfirmModal)
        dispatch = app.screen.query_one("#cfg-gate-dispatch", Static)
        assert _plain(dispatch.content) == (
            LNC_GATE_DISPATCH_LINE.format(
                workers=2, gpus="0,1", cells=3)), (
            "the dispatch line renders directly above the pair list, "
            "its numbers from GateSummary"
        )
        # the wrap-clip fix: the line's FIRST visual row stays in view
        # (auto_scroll can never scroll it away) and the log below it
        # holds the capped pair list
        log = app.screen.query_one("#cfg-gate-log", RichLog)
        assert log.scroll_y == 0, (
            "the log no longer overflows its bound (13 rows <= 14)"
        )
        lines = [line.text for line in log.lines]
        assert "model-00" in lines[0], (
            "the pair list still renders below the line"
        )
        assert lines[-1] == LNC_GATE_PAIRS_MORE.format(pairs=15)
        assert len(lines) == 13, (
            "the UX-5 bound holds with the line OUTSIDE the log: "
            "12 capped pairs + 1 total == 13 rows <= the 14-row bound"
        )


async def test_dispatch_line_cells_equal_summary_line_cells():
    """Auto-default #7: the dispatch line's {cells} is the SAME fresh
    same-source enumeration the summary line shows — one value, two
    renders; the copy carries the honest-preview framing marker."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(summary=GateSummary(
        models=1, tasks=1, seeds=3, cells=3, output_root="./finetuned",
        is_e2x=False, expected_phrase="finetuned",
        workers=1, gpus_display="0..0"))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        from tui.screens.run_config import _GateConfirmModal
        from tui.strings import (
            LNC_GATE_DISPATCH_LINE,
            LNC_GATE_SUMMARY,
        )

        assert isinstance(app.screen, _GateConfirmModal)
        message = str(app.screen._message)
        assert LNC_GATE_SUMMARY.format(
            models=1, tasks=1, seeds=3, cells=3,
            output_root="./finetuned") in message
        # 16-05 lockstep: the dispatch line reads from its Static (the
        # wrap-clip fix moved it out of the scroll-bounded log)
        dispatch = app.screen.query_one("#cfg-gate-dispatch", Static)
        line = _plain(dispatch.content)
        assert line == LNC_GATE_DISPATCH_LINE.format(
            workers=1, gpus="0..0", cells=3), (
            "both lines carry the SAME GateSummary cells"
        )
        assert "（预览）" in line, (
            "the honest-preview framing marker rides the line"
        )


async def test_e2x_face_renders_dispatch_line_phrase_mechanics_unchanged():
    """D16-11/D16-12 (16-04): E2PhraseModal renders the SAME dispatch
    line DIRECTLY above the warning block; the phrase input, the
    expected-phrase copy, and the match mechanics are byte-unchanged
    (the line is additive copy, never a gate alteration)."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(summary=GateSummary(
        models=62, tasks=50, seeds=3, cells=9300,
        output_root="./finetuned", is_e2x=True,
        expected_phrase="finetuned",
        workers=2, gpus_display="0..1"))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        from tui.screens.run_config import E2PhraseModal
        from tui.strings import (
            LNC_E2_MATCH_OK,
            LNC_E2_MISMATCH,
            LNC_E2_WARNING,
            LNC_GATE_DISPATCH_LINE,
        )

        assert isinstance(app.screen, E2PhraseModal)
        texts = [_plain(static.content)
                 for static in app.screen.query(Static)]
        expected = LNC_GATE_DISPATCH_LINE.format(
            workers=2, gpus="0..1", cells=9300)
        assert expected in texts, (
            "the dispatch line renders on the E2' face too"
        )
        assert texts.index(expected) + 1 == texts.index(LNC_E2_WARNING), (
            "the line sits DIRECTLY above the warning block"
        )
        # the phrase mechanics are byte-unchanged: mismatch -> match ->
        # matched-enter advance -> y launches with the typed phrase
        indicator = app.screen.query_one("#cfg-e2-indicator", Static)
        assert _plain(indicator.content) == LNC_E2_MISMATCH.format(
            dirname="finetuned")
        e2_input = app.screen.query_one("#cfg-e2-input", Input)
        e2_input.value = "wrong"
        await pilot.pause()
        assert _plain(indicator.content) == LNC_E2_MISMATCH.format(
            dirname="finetuned")
        e2_input.value = "finetuned"
        await pilot.pause()
        assert _plain(indicator.content) == LNC_E2_MATCH_OK
        await pilot.press("enter")     # the matched advance (never launch)
        await _settle(pilot, app, rounds=2)
        assert launcher.launch_calls == []
        await pilot.press("y")
        await _settle(pilot, app, rounds=3)
        assert len(launcher.launch_calls) == 1
        _spec, phrase = launcher.launch_calls[0]
        assert phrase == "finetuned"


async def test_gate_chain_multi_gpu_walk_dispatch_line_on_faces():
    """The extended gate-order walk (D16-14, zero weakening): a
    full-scope multi-GPU spec (workers 2 typed) walks problems ->
    capacity -> env -> confirm-data -> the E2' typed phrase IN ORDER
    (the stage-sequence evidence) with the dispatch line present on
    the reached face; a subset-scope spec walks to the Y/N confirm
    with the line present; the launched spec carries workers 2."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))

    # leg 1 — full scope: the E2' typed-phrase face
    full = _StageOrderLauncher(summary=GateSummary(
        models=62, tasks=50, seeds=3, cells=9300,
        output_root="./finetuned", is_e2x=True,
        expected_phrase="finetuned",
        workers=2, gpus_display="0,1"))
    app = _app(run_service=run_service, launcher=full)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        app.screen.query_one("#cfg-input-workers", Input).value = "2"
        await _settle(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        from tui.screens.run_config import E2PhraseModal
        from tui.strings import LNC_GATE_DISPATCH_LINE

        assert isinstance(app.screen, E2PhraseModal)
        assert full.stage_events == ["capacity", "env", "confirm"], (
            "the chain order holds: problems (clean) -> capacity -> "
            "env -> confirm-data -> the E2' face"
        )
        texts = [_plain(static.content)
                 for static in app.screen.query(Static)]
        assert LNC_GATE_DISPATCH_LINE.format(
            workers=2, gpus="0,1", cells=9300) in texts
        # the walk completes: y launches the multi-GPU spec
        e2_input = app.screen.query_one("#cfg-e2-input", Input)
        e2_input.value = "finetuned"
        await pilot.pause()
        await pilot.press("enter")
        await pilot.press("y")
        await _settle(pilot, app, rounds=3)
        assert len(full.launch_calls) == 1
        spec, _phrase = full.launch_calls[0]
        assert spec.workers == 2, (
            "the typed multi-GPU spec reaches the launch"
        )

    # leg 2 — subset scope: the Y/N confirm face with the line
    subset = _StageOrderLauncher(summary=GateSummary(
        models=1, tasks=1, seeds=3, cells=3, output_root="./finetuned",
        is_e2x=False, expected_phrase="finetuned",
        workers=2, gpus_display="0,1"))
    app = _app(run_service=run_service, launcher=subset)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        app.screen.query_one("#cfg-input-workers", Input).value = "2"
        await _settle(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        from tui.screens.run_config import _GateConfirmModal

        assert isinstance(app.screen, _GateConfirmModal)
        assert subset.stage_events == ["capacity", "env", "confirm"]
        # 16-05 lockstep: the dispatch line reads from its Static (the
        # wrap-clip fix moved it out of the scroll-bounded log)
        dispatch = app.screen.query_one("#cfg-gate-dispatch", Static)
        assert _plain(dispatch.content) == (
            LNC_GATE_DISPATCH_LINE.format(
                workers=2, gpus="0,1", cells=3))


async def test_gate_env_block_renders_reasons_verbatim():
    """Env preflight FAIL: the failing kernel names, the reasons
    VERBATIM, and the [1] route hint — launch never called."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(preflight=EnvPreflight(
        can_launch=False,
        reasons=("FAIL: python_kernel — torch missing",
                 "FAIL: cuda_kernel — no device"),
        failed_kernels=("python_kernel", "cuda_kernel")))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        from tui.screens.run_config import EnvBlockModal
        from tui.strings import ENV_QUICK_CHECK_FAIL, LNC_ENV_BLOCKED_HINT

        assert isinstance(app.screen, EnvBlockModal)
        header = _plain(app.screen.query_one(
            "#cfg-envblock-header", Static).content)
        assert header == ENV_QUICK_CHECK_FAIL.format(
            kernel_names="python_kernel, cuda_kernel")
        log = app.screen.query_one("#cfg-envblock-log")
        joined = "\n".join(line.text for line in log.lines)
        assert "FAIL: python_kernel — torch missing" in joined
        assert "FAIL: cuda_kernel — no device" in joined
        assert _plain(app.screen.query_one(
            "#cfg-envblock-hint", Static).content) == LNC_ENV_BLOCKED_HINT
        assert launcher.launch_calls == []


async def test_gate_e2x_phrase_flow():
    """The E2' typed-phrase escalation (EHC-2, 261015-ehc): a wrong
    dirname renders the mismatch and enter is a no-op; the exact
    dirname flips the indicator and enter ADVANCES to the y-ready
    state (input blurred, indicator on the [y] wording, nothing
    launched — a further enter does nothing); y fires the launch WITH
    the phrase (the phrase stays double insurance ON TOP of y)."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(summary=GateSummary(
        models=62, tasks=50, seeds=3, cells=9300,
        output_root="./finetuned", is_e2x=True,
        expected_phrase="finetuned"))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        from textual.widgets import Input as TextInput

        from tui.screens.run_config import E2PhraseModal
        from tui.strings import (
            LNC_E2_MATCH_OK,
            LNC_E2_MISMATCH,
            LNC_E2_TYPE_PROMPT,
        )

        assert isinstance(app.screen, E2PhraseModal)
        assert LNC_E2_TYPE_PROMPT.format(
            dirname="finetuned") in [
                _plain(static.content)
                for static in app.screen.query(Static)]
        indicator = app.screen.query_one("#cfg-e2-indicator", Static)
        assert _plain(indicator.content) == LNC_E2_MISMATCH.format(
            dirname="finetuned")

        # wrong dirname: indicator stays mismatched, enter is a no-op
        for char in "finetune_":
            await pilot.press(char)
        await pilot.pause()
        assert _plain(indicator.content) == LNC_E2_MISMATCH.format(
            dirname="finetuned")
        await pilot.press("enter")
        await _settle(pilot, app, rounds=3)
        assert launcher.launch_calls == [], (
            "a mismatch enter must never launch")
        assert isinstance(app.screen, E2PhraseModal)

        # complete the exact dirname: the indicator flips live
        await pilot.press(*"x")   # still wrong
        await pilot.pause()
        assert _plain(indicator.content) == LNC_E2_MISMATCH.format(
            dirname="finetuned")
        e2_input = app.screen.query_one("#cfg-e2-input", TextInput)
        e2_input.value = ""      # reset for the clean exact-match path
        await pilot.pause()
        for char in "finetuned":
            await pilot.press(char)
        await pilot.pause()
        assert _plain(indicator.content) == LNC_E2_MATCH_OK
        # the matched enter ADVANCES: input blurred (y armed), modal
        # stays up, nothing launches — and a further enter is inert
        await pilot.press("enter")
        await _settle(pilot, app, rounds=3)
        assert launcher.launch_calls == [], (
            "the matched enter advances, it never launches (EHC-2)")
        assert isinstance(app.screen, E2PhraseModal)
        assert app.focused is not e2_input, (
            "the advance blurs the input — that is what arms the y key")
        assert _plain(indicator.content) == LNC_E2_MATCH_OK
        await pilot.press("enter")
        await _settle(pilot, app, rounds=2)
        assert launcher.launch_calls == [], (
            "a further enter still never launches"
        )
        assert isinstance(app.screen, E2PhraseModal)
        await pilot.press("y")
        await _settle(pilot, app, rounds=3)
        assert len(launcher.launch_calls) == 1
        spec, phrase = launcher.launch_calls[0]
        assert phrase == "finetuned", (
            "the E2' y-confirm carries the typed phrase")
        assert spec.models == ("model-a",)


async def test_gate_e2x_three_consecutive_mismatches_stay_mismatched():
    """Three consecutive mismatch entries never unlock enter (the
    brief's edge — no 'three strikes' bypass)."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(summary=GateSummary(
        models=62, tasks=50, seeds=3, cells=9300,
        output_root="./finetuned", is_e2x=True,
        expected_phrase="finetuned"))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        from tui.screens.run_config import E2PhraseModal

        assert isinstance(app.screen, E2PhraseModal)
        e2_input = app.screen.query_one("#cfg-e2-input", Input)
        for attempt in ("wrong-one", "wrong-two", "wrong-three"):
            e2_input.value = attempt
            await pilot.pause()
            await pilot.press("enter")
            await _settle(pilot, app, rounds=2)
            assert isinstance(app.screen, E2PhraseModal), (
                f"mismatch {attempt!r} must not dismiss the gate")
        assert launcher.launch_calls == []


async def test_enter_key_pin_inputs_never_launch():
    """THE PIN (UI-checker fix 2): a focused Input consumes its own
    Enter — typing can never launch; enter on the picker opens the
    gate."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService()
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        # focus the seeds Input and press enter: NO gate opens
        seeds = screen.query_one("#cfg-input-seeds", Input)
        seeds.focus()
        await pilot.pause()
        assert app.focused is seeds
        await pilot.press("enter")
        await _settle(pilot, app, rounds=2)
        assert isinstance(app.screen, RunConfigScreen), (
            "an Input's own Enter must never open the gate")
        assert launcher.env_calls == 0
        # the picker: enter OPENS the gate (the enumeration runs)
        screen.query_one("#cfg-picker").focus()
        await pilot.pause()
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        assert launcher.env_calls >= 1, (
            "enter on the picker must open the launch confirmation")


async def test_gate_worker_exception_releases_flag_and_surfaces():
    """WR-03: a gate worker raising (registry OSError, malformed
    overlay, probe ValueError) must never wedge the gate — the error
    toast surfaces it and a second [enter] re-enters the pipeline (the
    re-entrancy guard was released)."""
    from tui.strings import LNC_LAUNCH_FAILED_TOAST

    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(
        confirm_raises=OSError("models_info.json unreadable"))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        assert any(LNC_LAUNCH_FAILED_TOAST.format(
            error="models_info.json unreadable") in toast
            for toast in _toast_messages(app)), _toast_messages(app)
        assert screen_gate_active(app.screen) is False, (
            "the exception path released the pre-modal gate flag"
        )
        # the gate is re-enterable: the pipeline re-runs (env again)
        env_before = launcher.env_calls
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        assert launcher.env_calls > env_before, (
            "a second [enter] re-enters the gate — no permanent wedge"
        )


def screen_gate_active(screen) -> bool:
    """The screen's gate re-entrancy flag (WR-03's wedge probe)."""
    return screen._gate_active


async def test_gate_launch_exception_after_confirm_is_never_silent():
    """WR-03's worst instance: the launch worker dying AFTER the
    operator confirmed must surface an error — never a silent no-op
    launch."""
    from tui.screens.selection import ConfirmModal
    from tui.strings import LNC_LAUNCH_FAILED_TOAST

    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(launch_raises=RuntimeError("spawn boom"))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        assert isinstance(app.screen, ConfirmModal)
        await pilot.press("y")   # confirm -> the launch worker raises
        await _settle(pilot, app, rounds=3)
        assert any(LNC_LAUNCH_FAILED_TOAST.format(error="spawn boom")
                   in toast for toast in _toast_messages(app)), (
            "the confirm-then-crash path surfaces the error"
        )


async def test_gate_worker_error_scope_tags_split_the_id_spaces():
    """IN-02 (08 review, fix batch 261017-klw): the GateWorkerError
    staleness filter compares run_id against EXACTLY ONE counter per
    scope tag — a superseded STAGE error whose id numerically equals the
    CURRENT launch id (both counters increment independently from 1) is
    DROPPED, so a successful launch is never followed by a spurious
    launch-failed toast; a genuinely-current error in either space still
    surfaces, and the run_id-None mount worker always surfaces."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService()
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        screen._gate_stage_id = 1
        screen._gate_launch_id = 3
        screen._gate_active = True

        # the COLLISION: a stale stage error (belongs to stage id 1)
        # whose id numerically equals the CURRENT launch id (3) — today
        # it passes the either-counter filter and surfaces a spurious
        # launch-failed toast right after a successful launch
        screen.post_message(screen.GateWorkerError(
            "stage boom", run_id=3, scope="stage"))
        await pilot.pause()
        assert not any("stage boom" in toast
                       for toast in _toast_messages(app)), (
            "a stale STAGE error whose id collides with the launch "
            "counter must be dropped (IN-02)"
        )
        assert screen_gate_active(screen) is True, (
            "a dropped stale error never touches the gate flag"
        )

        # control 1: the same id in the LAUNCH space IS current
        screen.post_message(screen.GateWorkerError(
            "launch boom", run_id=3, scope="launch"))
        await pilot.pause()
        assert any("launch boom" in toast
                   for toast in _toast_messages(app)), (
            "a CURRENT launch error still surfaces (IN-02)"
        )
        assert screen_gate_active(screen) is False, (
            "a surfaced error releases the gate flag"
        )

        # control 2: a current STAGE id surfaces
        screen._gate_active = True
        screen.post_message(screen.GateWorkerError(
            "current stage boom", run_id=1, scope="stage"))
        await pilot.pause()
        assert any("current stage boom" in toast
                   for toast in _toast_messages(app)), (
            "a CURRENT stage error still surfaces (IN-02)"
        )

        # control 3: the mount worker (run_id None) always surfaces
        screen._gate_active = True
        screen.post_message(screen.GateWorkerError("mount boom"))
        await pilot.pause()
        assert any("mount boom" in toast
                   for toast in _toast_messages(app)), (
            "the run_id-None mount worker always surfaces (IN-02)"
        )
        assert screen_gate_active(screen) is False


async def test_gate_spawn_failure_toast_nothing_launched():
    """Spawn failure: the failed toast fires; nothing launched."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(outcomes=[LaunchOutcome(
        spawned=False, root="", tee_path=None,
        error="[Errno 13] Permission denied")])
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        from tui.screens.selection import ConfirmModal

        assert isinstance(app.screen, ConfirmModal)
        await pilot.press("y")
        await _settle(pilot, app, rounds=3)
        from tui.strings import LNC_LAUNCH_FAILED_TOAST

        assert any(LNC_LAUNCH_FAILED_TOAST.format(
            error="[Errno 13] Permission denied") in toast
            for toast in _toast_messages(app))


async def test_e2x_modal_composes_at_80_with_long_root():
    """The 80x24 backstop: the E2' modal composes at the minimum grid
    with a long root name (no wrap collision)."""
    long_name = "finetuned-e2e-full-matrix-rerun-20261013"
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)),
        phrase_expected=long_name)
    launcher = FakeLauncherService(summary=GateSummary(
        models=62, tasks=50, seeds=3, cells=9300,
        output_root=f"./{long_name}", is_e2x=True,
        expected_phrase=long_name))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(80, 24)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        from tui.screens.run_config import E2PhraseModal

        assert isinstance(app.screen, E2PhraseModal)
        box = app.screen.query_one("#cfg-e2-box")
        assert box.region.height <= 22, (
            "the modal composes inside the 22-row content budget")
        assert box.region.width <= 80
        for char in long_name:
            await pilot.press(char)
        await pilot.pause()
        indicator = app.screen.query_one("#cfg-e2-indicator", Static)
        from tui.strings import LNC_E2_MATCH_OK

        assert _plain(indicator.content) == LNC_E2_MATCH_OK


async def test_gate_console_stays_responsive_while_env_blocked():
    """T-11-06-04: a blocking env preflight runs in a worker — the
    console keeps responding while it blocks."""
    import threading

    release = threading.Event()

    class _BlockingLauncher(FakeLauncherService):
        def env_preflight(self, kernels=None):
            release.wait(timeout=10)
            return super().env_preflight(kernels)

    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = _BlockingLauncher()
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await pilot.pause()
        # while the env kernel blocks, m still flips the picker (the
        # event loop never froze)
        await pilot.press("m")
        await pilot.pause()
        assert _label_text(app.screen, "#cfg-picker-title") == (
            CFG_PICKER_DATASETS.format(n=1, total=2) + f" · [m] {NAV_LABEL_SELECTION}"), (
            "m must still flip the picker while the env worker blocks")
        release.set()
        await _settle(pilot, app, rounds=4)
        from tui.screens.selection import ConfirmModal

        assert isinstance(app.screen, ConfirmModal)


async def test_gate_modal_push_guarded_below_minimum_grid():
    """T-11-06-06 (WR-06): a gate completing while the min-size guard is
    up never pushes chrome over it; growing back restores the screen."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService()
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        from tui.app import MinSizeScreen

        await pilot.resize_terminal(60, 20)
        await pilot.pause()
        assert isinstance(app.screen, MinSizeScreen)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        assert isinstance(app.screen, MinSizeScreen), (
            "no gate chrome may open over the min-size guard")
        assert not app.screen_stack[0].query(
            "ConfirmModal"), "nothing opened beneath the guard either"
        await pilot.resize_terminal(120, 40)
        await pilot.pause()
        assert isinstance(app.screen, RunConfigScreen)


# =====================================================================
# Task 3 — the exit triple (app-level q) + the choice modals
# =====================================================================

async def test_q_with_no_live_sweep_opens_quit_confirm():
    """261016-v0z (the maintainer's always-confirm ruling): no live
    sweep — q opens the plain Y/N quit-confirm modal, never a direct
    exit; enter is structurally inert (EHC-2), q inside the modal is
    blocked by the modal binding chain, and y is the ONLY confirm key."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("q")
        await pilot.pause()
        from tui.app import QuitConfirmModal
        from tui.strings import LNC_EXIT_CONFIRM, LNC_EXIT_TITLE

        assert isinstance(app.screen, QuitConfirmModal), (
            "no live sweep: q must open the quit confirm, never exit")
        assert not app._exit, "q alone must never quit the console"
        assert str(app.screen.query_one(
            "#quit-confirm-box").border_title) == LNC_EXIT_TITLE
        message = _plain(app.screen.query(Static)[0].content)
        assert LNC_EXIT_CONFIRM in message, message

        # enter is structurally inert — a stray double-enter can never
        # quit (the EHC-2 idiom, extended to the quit surface)
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, QuitConfirmModal), (
            "enter must never confirm a quit")
        assert not app._exit

        # q INSIDE the modal is inert (the modal binding chain blocks
        # app-level bindings — Pitfall 11)
        await pilot.press("q")
        await pilot.pause()
        assert isinstance(app.screen, QuitConfirmModal), (
            "repeat q under the modal must not quit or reopen anything")
        assert not app._exit

        # y is the ONLY confirm key
        await pilot.press("y")
        await pilot.pause()
        assert app._exit, "y confirms the quit"


async def test_quit_confirm_n_and_esc_cancel():
    """The quit confirm's cancel pair: n and esc both return to the
    screen with nothing recorded — the app stays alive."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("q")
        await pilot.pause()
        from tui.app import QuitConfirmModal

        assert isinstance(app.screen, QuitConfirmModal)
        await pilot.press("n")
        await pilot.pause()
        assert isinstance(app.screen, RunConfigScreen), (
            "n cancels the quit confirm back to the screen")
        assert not app._exit, "n must never quit"

        # reopen and esc likewise — nothing recorded
        await pilot.press("q")
        await pilot.pause()
        assert isinstance(app.screen, QuitConfirmModal)
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, RunConfigScreen), (
            "esc cancels the quit confirm back to the screen")
        assert not app._exit, "esc must never quit"


async def test_ctrlq_with_live_sweep_routes_to_exit_modal():
    """The regression pin (probe P1): ctrl+q already dispatches to the
    overridden action_quit on 8.2.8 — a live sweep opens the ExitModal
    (kill/detach/cancel), and q INSIDE that modal is inert (no
    double-confirm escape)."""
    launcher = FakeLauncherService(live=("/repo/finetuned",))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("ctrl+q")
        await pilot.pause()
        from tui.app import ExitModal

        assert isinstance(app.screen, ExitModal), (
            "ctrl+q with a live sweep must route through the ExitModal")
        assert not app._exit, "ctrl+q alone must never exit"
        await pilot.press("q")
        await pilot.pause()
        assert isinstance(app.screen, ExitModal), (
            "q under the ExitModal stays inert — no double-confirm")
        assert not app._exit


async def test_ctrlq_no_sweep_opens_quit_confirm():
    """261016-v0z: ctrl+q with NO live sweep opens the same quit
    confirm as q — the inherited default is never a direct exit."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("ctrl+q")
        await pilot.pause()
        from tui.app import QuitConfirmModal

        assert isinstance(app.screen, QuitConfirmModal), (
            "ctrl+q with no live sweep must open the quit confirm")
        assert not app._exit, "ctrl+q alone must never quit the console"


async def test_q_and_ctrlq_below_min_grid_never_exit():
    """V0Z-4: below 80x24, q AND ctrl+q exit nothing and open nothing —
    including with a live sweep (this closes the latent fall-through
    where a live sweep + below-min grid previously reached an unguarded
    ``self.exit()``)."""
    from tui.app import ExitModal, MinSizeScreen

    launcher = FakeLauncherService(live=("/repo/finetuned",))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.resize_terminal(60, 20)
        await pilot.pause()
        assert isinstance(app.screen, MinSizeScreen)

        await pilot.press("q")
        await pilot.pause()
        assert not app._exit, (
            "below the min grid a live sweep + q must never exit "
            "(the latent fall-through)")
        assert not any(isinstance(screen, ExitModal)
                       for screen in app.screen_stack), (
            "no ExitModal may open over the min-size guard")
        assert isinstance(app.screen, MinSizeScreen), (
            "the guard stays the top screen")

        await pilot.press("ctrl+q")
        await pilot.pause()
        assert not app._exit, "ctrl+q below the min grid must never exit"
        assert not any(isinstance(screen, ExitModal)
                       for screen in app.screen_stack)
        assert isinstance(app.screen, MinSizeScreen)

    # the q leg with NO live sweep must not exit below the grid either
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.resize_terminal(60, 20)
        await pilot.pause()
        assert isinstance(app.screen, MinSizeScreen)
        await pilot.press("q")
        await pilot.pause()
        assert not app._exit, (
            "q below the min grid with no sweep must never exit either")
        assert isinstance(app.screen, MinSizeScreen)


async def test_q_with_live_sweep_pushes_exit_modal():
    """A live sweep intercepts q: the ExitModal with the D-06 triple."""
    launcher = FakeLauncherService(live=("/repo/finetuned",))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("q")
        await pilot.pause()
        from tui.app import ExitModal
        from tui.strings import LNC_EXIT_MESSAGE, LNC_EXIT_TITLE

        assert isinstance(app.screen, ExitModal)
        box = app.screen.query_one("#exit-modal-box")
        assert str(box.border_title) == LNC_EXIT_TITLE
        message = _plain(app.screen.query(Static)[0].content)
        assert LNC_EXIT_MESSAGE.format(
            done="—", total="—", root="finetuned") in message, message


async def test_exit_modal_footer_shows_enter_k_keycaps():
    """DNR-4 (261017-dnr): the ExitModal triple is visible at a glance —
    enter/k bindings carry show=True with the new keycaps (wording
    lifted verbatim from the LNC_EXIT_MESSAGE copy) and escape shows;
    visibility only, enter stays the detach-and-exit default (the
    Phase-11 design — the behavior tests below run unedited)."""
    launcher = FakeLauncherService(live=("/repo/finetuned",))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("q")
        await pilot.pause()
        from textual.binding import Binding
        from textual.widgets import Footer as FooterWidget

        from tui.app import ExitModal
        from tui.strings import (
            LNC_EXIT_DETACH_KEYCAP,
            LNC_EXIT_KILL_KEYCAP,
        )

        assert isinstance(app.screen, ExitModal)
        entries = {binding.key: binding
                   for binding in ExitModal.BINDINGS
                   if isinstance(binding, Binding)}
        assert entries["enter"].show is True, (
            "the enter default must render in the Footer"
        )
        assert entries["enter"].description == LNC_EXIT_DETACH_KEYCAP
        assert entries["enter"].action == "detach_quit", (
            "visibility only — enter still detaches (Phase-11 default)"
        )
        assert entries["k"].show is True, (
            "the k kill key must render in the Footer"
        )
        assert entries["k"].description == LNC_EXIT_KILL_KEYCAP
        assert entries["k"].action == "kill_quit"
        assert entries["escape"].show is True
        assert app.screen.query(FooterWidget), (
            "the modal composes a Footer — the keycaps render"
        )


async def test_exit_modal_message_bolds_triple_tokens():
    """DNR-4 (261017-dnr): the exit message's [enter]/[k]/[esc] tokens
    are prominent — the message Static's content is a rich Text with a
    bold span over every triple-token occurrence while the plain value
    still carries the formatted LNC_EXIT_MESSAGE byte-unchanged
    (span-safe existing assertions)."""
    launcher = FakeLauncherService(live=("/repo/finetuned",))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("q")
        await pilot.pause()
        from tui.app import ExitModal
        from tui.strings import LNC_EXIT_MESSAGE

        assert isinstance(app.screen, ExitModal)
        content = app.screen.query(Static)[0].content
        assert isinstance(content, Text), (
            "the message composes as a rich Text over the registry "
            "constant — never a markup string"
        )
        plain = content.plain
        assert LNC_EXIT_MESSAGE.format(
            done="—", total="—", root="finetuned") in plain, plain
        for token in ("[enter]", "[k]", "[esc]"):
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


async def test_exit_enter_detaches_then_exits():
    """[enter] the default: detach recorded, exit initiated."""
    launcher = FakeLauncherService(live=("/repo/finetuned",))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("q")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert launcher.detach_calls == ["/repo/finetuned"]
        assert launcher.kill_calls == [], "detach never kills"
        assert app._exit, "detach-then-quit initiates the exit"


async def test_exit_k_kills_then_exits():
    """[k] SIGTERMs the process group then exits."""
    launcher = FakeLauncherService(live=("/repo/finetuned",))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("q")
        await pilot.pause()
        await pilot.press("k")
        await pilot.pause()
        assert launcher.kill_calls == ["/repo/finetuned"]
        assert launcher.detach_calls == [], "kill never detaches"
        assert app._exit, "kill-then-quit initiates the exit"


async def test_exit_esc_returns_nothing_recorded():
    """[esc] cancels the quit — still on screen, nothing recorded."""
    launcher = FakeLauncherService(live=("/repo/finetuned",))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("q")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, RunConfigScreen)
        assert launcher.detach_calls == []
        assert launcher.kill_calls == []
        assert not app._exit, "esc cancels the quit entirely"


async def test_exit_modal_multi_root_kills_every_live_sweep():
    """WR-05 (gap #6): with MULTIPLE live sweeps, the exit modal names
    EVERY live root (full resolved paths — basenames collide: two
    ``finetuned`` roots are the triggering scenario) with the count,
    and [k] kills ALL of them before the app exits — no sweep survives
    a 终止后退出 the operator believed terminal."""
    root_a = "/repo/a/finetuned"
    root_b = "/repo/b/finetuned"
    launcher = FakeLauncherService(live=(root_a, root_b))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("q")
        await pilot.pause()
        from tui.app import ExitModal
        from tui.strings import LNC_EXIT_MESSAGE_MULTI

        assert isinstance(app.screen, ExitModal)
        message = _plain(app.screen.query(Static)[0].content)
        assert LNC_EXIT_MESSAGE_MULTI.format(
            n=2, roots=f"{root_a}, {root_b}") in message, message
        await pilot.press("k")
        await pilot.pause()
        assert launcher.kill_calls == [root_a, root_b], (
            "[k] kills EVERY live root — never roots[0] alone"
        )
        assert launcher.detach_calls == [], "kill never detaches"
        assert app._exit, "kill-then-quit initiates the exit"


async def test_exit_modal_multi_root_enter_detaches_every_live_sweep():
    """WR-05 (the detach twin): [enter] detaches ALL live roots (each
    survives as its own orphaned session leader — resume-safe by the
    trainer_state marker contract) and then the app exits."""
    root_a = "/repo/a/finetuned"
    root_b = "/repo/b/finetuned"
    launcher = FakeLauncherService(live=(root_a, root_b))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("q")
        await pilot.pause()
        from tui.app import ExitModal

        assert isinstance(app.screen, ExitModal)
        await pilot.press("enter")
        await pilot.pause()
        assert launcher.detach_calls == [root_a, root_b], (
            "[enter] detaches EVERY live root"
        )
        assert launcher.kill_calls == [], "detach never kills"
        assert app._exit, "detach-then-quit initiates the exit"


# =====================================================================
# The 2026-10-17 fix batch (08 review WR-01/02/03) — the exit-channel
# trio: ctrl+c copy delegation on selection-holding Inputs, the
# off-loop kill-and-exit, and the mixed live-root modal form
# (261017-mad: the ctrl+c legs below are the WITHDRAWN-intercept native
# forms — the delegation branch rode out with the intercept)
# =====================================================================


async def test_ctrlc_copies_when_input_holds_a_real_selection():
    """WR-01 (08 review, fix batch 261017-klw) — the 261017-mad native
    form: the ctrl+c interception is WITHDRAWN, so on a BASE screen a
    selection-holding focused Input and ctrl+c reach textual 8.2.8's
    own ``ctrl+c,super+c -> copy`` Input binding (``_input.py:139``)
    directly — ZERO app seam involved (the retired delegation branch
    existed only to rescue the copy the intercept was ambushing; the
    native binding delivers the same clipboard copy). The selection is
    driven by REAL key presses (home, then shift+end) after typing —
    never a private-attribute poke. The collapsed-contrast leg
    (261017-mad): an EMPTY selection + ctrl+c opens NO exit surface
    either — the inherited notify-only help_quit default fires (the
    maintainer-ruling acceptance, deliberately not pinned), never the
    exit confirm the retired intercept used to open."""
    from tui.app import ExitModal, QuitConfirmModal

    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        seeds_input = app.screen.query_one("#cfg-input-seeds", Input)
        seeds_input.focus()
        await pilot.pause()
        # collapse the select_on_focus whole-content selection, then TYPE
        # (a real selection must survive its own typing flow)
        await pilot.press("end")
        for char in "hello":
            await pilot.press(char)
        await pilot.pause()
        assert seeds_input.value == "42,43,44hello", (
            "the typed text landed (typing sanity for the selection flow)"
        )
        # drive the REAL selection: home, then shift+end selects the line
        await pilot.press("home")
        await pilot.press("shift+end")
        await pilot.pause()
        assert seeds_input.selected_text == "42,43,44hello", (
            "shift+end drove a non-empty selection (probe-pinned seam)"
        )
        value_before = seeds_input.value

        await pilot.press("ctrl+c")
        await pilot.pause()

        assert not any(isinstance(screen, (ExitModal, QuitConfirmModal))
                       for screen in app.screen_stack), (
            "ctrl+c over a selection-holding Input must NOT open any "
            "exit surface (the Input's own copy binding owns the key)"
        )
        assert isinstance(app.screen, RunConfigScreen), (
            "the base screen stays top — the key was a copy, not an exit"
        )
        assert not app._exit, "a copy gesture never exits the console"
        assert app.clipboard == "42,43,44hello", (
            "the selected text reached the app clipboard (textual's own "
            "Input copy binding fired — no app seam)"
        )
        assert seeds_input.value == value_before, (
            "copy never mutates the Input (cut would; copy must not)"
        )

        # the CONTRAST (the empty-selection case, same Input): collapse
        # the selection, ctrl+c -> NO exit surface (the inherited
        # notify-only default; the retired intercept used to open the
        # quit confirm here — the withdrawal's exact ambush closure)
        await pilot.press("end")
        await pilot.pause()
        assert seeds_input.selected_text == "", (
            "end collapsed the selection for the contrast leg"
        )
        await pilot.press("ctrl+c")
        await pilot.pause()
        assert not any(
            isinstance(screen, (ExitModal, QuitConfirmModal))
            for screen in app.screen_stack), (
            "an EMPTY selection must open no exit surface either — the "
            "terminal copy gesture never meets an exit (MAD-2)"
        )
        assert isinstance(app.screen, RunConfigScreen)
        assert not app._exit


async def test_ctrlc_without_input_focus_ambushes_nothing():
    """MAD-2 (the ambush scenario pin): a bare ctrl+c on a base screen
    with NO Input focus opens NO modal anywhere and never exits — the
    retired 261017-cdr intercept used to route exactly this press into
    the exit confirm, which is how an unscoped terminal ctrl+shift+c
    copy passthrough (an indistinguishable 0x03) ambushed the operator
    with the exit confirm while they tried to copy. Withdrawn: the key
    now hits textual's inherited notify-only help_quit default (names
    ctrl+q; no modal, no exit — accepted as harmless per the ruling,
    deliberately not pinned)."""
    from tui.app import ExitModal, QuitConfirmModal

    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        # no Input focused (the picker/params chrome owns focus)
        await pilot.press("ctrl+c")
        await pilot.pause()
        assert not any(
            isinstance(screen, (ExitModal, QuitConfirmModal))
            for screen in app.screen_stack), (
            "a bare ctrl+c must open no exit surface (the "
            "terminal-copy passthrough ambush is closed)"
        )
        assert isinstance(app.screen, RunConfigScreen), (
            "the base screen stays top"
        )
        assert not app._exit, "a bare ctrl+c never exits"


async def test_exit_k_kills_every_root_then_exits_on_completion():
    """WR-02 (08 review, fix batch 261017-klw): [k] on the multi-root
    ExitModal fans the kill out through ONE app-level thread worker —
    every live root is SIGTERMed BEFORE the exit lands (the exit is
    driven by worker completion, never by a synchronous loop), the
    console never runs the blocking kill polling on the event loop (the
    monitor's mon-kill discipline, now honored on the exit path)."""
    root_a = "/repo/a"
    root_b = "/repo/b"
    launcher = FakeLauncherService(live=(root_a, root_b))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("q")
        await pilot.pause()
        from tui.app import ExitModal

        assert isinstance(app.screen, ExitModal)
        await pilot.press("k")
        await _settle(pilot, app, rounds=3)
        assert launcher.kill_calls == [root_a, root_b], (
            "the worker attempts EVERY live root — kill before exit"
        )
        assert launcher.detach_calls == [], "kill never detaches"
        assert app._exit, (
            "the exit lands on worker completion (ExitKillsDone -> exit)"
        )


async def test_exit_k_raising_kill_still_attempts_every_root_and_exits():
    """WR-02's guard pin: a kill_sweep that RAISES can never strand a
    killed-but-unexited console — the per-root broad guard logs and the
    fan-out CONTINUES (every root attempted), and the completion posts
    unconditionally so the app still exits. Today the first raise
    escapes the synchronous loop action: root B is never attempted and
    the exception takes the action down."""
    root_a = "/repo/a"
    root_b = "/repo/b"
    launcher = FakeLauncherService(
        live=(root_a, root_b), kill_raises=OSError("no such process"))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("q")
        await pilot.pause()
        from tui.app import ExitModal

        assert isinstance(app.screen, ExitModal)
        await pilot.press("k")
        await _settle(pilot, app, rounds=3)
        assert launcher.kill_calls == [root_a, root_b], (
            "a raising kill must not abort the fan-out — root B is still "
            "attempted (per-root broad guard, WR-02)"
        )
        assert app._exit, (
            "ExitKillsDone posts unconditionally — the console still exits"
        )


async def test_mixed_roots_exit_names_and_kills_both_tui_and_attached():
    """WR-03 (08 review, fix batch 261017-klw): exactly ONE TUI-launched
    live root PLUS the monitor's attached root being a DIFFERENT running
    (CLI-launched) sweep now joins the MULTI-root ExitModal form — both
    full paths named via LNC_EXIT_MESSAGE_MULTI, and [k] kills BOTH (no
    CLI-launched sweep survives a kill-and-exit silently). The attached
    root rides a minimal seam stub (attached_running_counts on the real
    but unmounted monitor screen — never a mounted MonitorScreen)."""
    from tui.app import ExitModal
    from tui.strings import LNC_EXIT_MESSAGE_MULTI

    launcher = FakeLauncherService(live=("/repo/tui-root",))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        monitor_screen = app.build_monitor_screen()
        monitor_screen.attached_running_counts = lambda: (
            True, "/repo/cli-root", "3", "9")
        app._monitor_screen = monitor_screen
        await pilot.press("ctrl+q")
        await pilot.pause()

        assert isinstance(app.screen, ExitModal)
        assert app.screen._roots == ("/repo/tui-root", "/repo/cli-root"), (
            "the mixed form carries BOTH live roots — the attached "
            "CLI-launched sweep is never silently dropped (WR-03)"
        )
        message = _plain(app.screen.query(Static)[0].content)
        assert LNC_EXIT_MESSAGE_MULTI.format(
            n=2, roots="/repo/tui-root, /repo/cli-root") in message, (
            message)
        await pilot.press("k")
        await _settle(pilot, app, rounds=3)
        assert launcher.kill_calls == ["/repo/tui-root", "/repo/cli-root"], (
            "[k] acts on BOTH roots — no unnamed sweep keeps the GPU on"
        )
        assert app._exit


async def test_mixed_roots_exit_enter_detaches_both():
    """WR-03's detach twin: [enter] on the mixed-root form detaches BOTH
    the TUI root and the attached CLI root — every live root is named
    and acted on, on every exit path."""
    from tui.app import ExitModal

    launcher = FakeLauncherService(live=("/repo/tui-root",))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        monitor_screen = app.build_monitor_screen()
        monitor_screen.attached_running_counts = lambda: (
            True, "/repo/cli-root", "3", "9")
        app._monitor_screen = monitor_screen
        await pilot.press("ctrl+q")
        await pilot.pause()

        assert isinstance(app.screen, ExitModal)
        await pilot.press("enter")
        await pilot.pause()
        assert launcher.detach_calls == ["/repo/tui-root", "/repo/cli-root"], (
            "[enter] detaches BOTH roots (each survives resume-safe)"
        )
        assert launcher.kill_calls == [], "detach never kills"
        assert app._exit


async def test_q_uppercase_is_a_plain_typing_letter_again():
    """CDR-1 (261017-cdr): the 261016-vxr uppercase-Q intercept is FULLY
    withdrawn — a capital Q is a PLAIN TYPING LETTER again everywhere.
    Over a focused base-screen Input it TYPES (the select_on_focus
    replace semantics the lowercase-q pin documents), opens no modal
    anywhere in the stack, and never exits (the any-focus exit role
    passed to ctrl+c at 261017-cdr and to F10 at 261017-mad — the
    2026-10-17 16:02 final ruling)."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        seeds_input = app.screen.query_one("#cfg-input-seeds", Input)
        seeds_input.focus()
        await pilot.pause()
        await pilot.press("Q")
        await pilot.pause()
        # select_on_focus: the focused Input's content is selected, so
        # the typed Q REPLACES it — the standard replace-typing shape
        assert seeds_input.value == "Q", (
            "a capital Q must TYPE into the focused base-screen Input"
        )
        assert isinstance(app.screen, RunConfigScreen), (
            "a capital Q opens no modal on a base screen"
        )
        assert not any(screen.is_modal for screen in app.screen_stack), (
            "no modal anywhere in the stack — Q is not an exit key anymore"
        )
        assert not app._exit, "a capital Q never exits"


async def test_q_lowercase_still_types_into_inputs():
    """VXR-3 regression pin: lowercase q keeps its Input semantics —
    it types, opens no modal (byte-unchanged behavior)."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        seeds_input = app.screen.query_one("#cfg-input-seeds", Input)
        seeds_input.focus()
        await pilot.pause()
        await pilot.press("q")
        await pilot.pause()
        # Textual Input's select_on_focus: focus() selects the content,
        # so the typed q REPLACES it — the standard focused-input typing
        # semantics (the key arrives at the Input, not the app binding)
        assert seeds_input.value == "q", (
            "lowercase q still types into the focused Input"
        )
        assert isinstance(app.screen, RunConfigScreen), (
            "lowercase q opens no modal while an Input holds focus"
        )


async def test_modal_exit_semantics_native_ctrlc_and_f10():
    """MAD-2/MAD-1 (the 261017-mad withdrawal): under modals ctrl+c is
    NATIVELY chain-cut — the inherited help_quit default is
    non-priority, so an open modal's binding chain consumes it (no exit
    surface, nothing typed, exactly one modal; identical to the retired
    intercept's modal guard, now free). f10 under a NON-exit
    Input-bearing modal is a NEW legitimate quit intent (the ctrl+q
    family semantics): the priority chain fires over the modal, the
    QuitConfirmModal stacks OVER it, and esc peels back to the modal
    beneath. A capital Q still types inside modal Inputs (the E2'
    phrase rationale, pinned)."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        from tui.app import QuitConfirmModal
        from tui.screens.selection import PathInputModal

        # (a) under the QuitConfirmModal: exactly one, never a second
        await pilot.press("q")   # no live sweep -> the quit confirm
        await pilot.pause()
        assert isinstance(app.screen, QuitConfirmModal)
        await pilot.press("ctrl+c")
        await pilot.pause()
        assert sum(isinstance(screen, QuitConfirmModal)
                   for screen in app.screen_stack) == 1, (
            "ctrl+c under a modal is natively chain-cut — never a second"
        )
        assert not app._exit, "ctrl+c under a modal never quits"
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, RunConfigScreen)

        # (c)/(d) an Input-bearing modal top: ctrl+c pushes nothing and
        # types nothing; f10 stacks the quit confirm OVER it (new
        # legitimate intent — PathInputModal is deliberately outside the
        # CDR-4 guard set) and esc peels back; a capital Q still TYPES
        app.push_screen(PathInputModal(
            "title", "placeholder", on_submit=lambda _path: None))
        await pilot.pause()
        path_input = app.screen.query_one("#path-input", Input)
        value_before = path_input.value
        await pilot.press("ctrl+c")
        await pilot.pause()
        assert not any(isinstance(screen, QuitConfirmModal)
                       for screen in app.screen_stack), (
            "ctrl+c under an input modal pushes no exit surface"
        )
        assert not app._exit
        assert path_input.value == value_before, "ctrl+c never types"
        # f10 over the input modal: the priority chain fires, the quit
        # confirm stacks OVER the input modal, esc peels back
        await pilot.press("f10")
        await pilot.pause()
        assert isinstance(app.screen, QuitConfirmModal), (
            "f10 stacks the quit confirm over a non-exit modal"
        )
        assert sum(isinstance(screen, PathInputModal)
                   for screen in app.screen_stack) == 1, (
            "the input modal stays beneath — one stack, never a replace"
        )
        assert not app._exit
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, PathInputModal), (
            "esc peels back to the input modal beneath"
        )
        path_input.focus()
        await pilot.pause()
        await pilot.press("Q")
        await pilot.pause()
        assert path_input.value == "Q", (
            "capital Q stays typeable inside modal Inputs"
        )
        assert isinstance(app.screen, PathInputModal), (
            "no quit, no second modal under the input modal"
        )
        assert not app._exit

    # (b) the ExitModal twin, with a live sweep: exactly one
    launcher = FakeLauncherService(live=("/repo/finetuned",))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        from tui.app import ExitModal

        await pilot.press("q")
        await pilot.pause()
        assert isinstance(app.screen, ExitModal)
        await pilot.press("ctrl+c")
        await pilot.pause()
        assert sum(isinstance(screen, ExitModal)
                   for screen in app.screen_stack) == 1, (
            "ctrl+c under the ExitModal must never stack a second one"
        )
        assert not app._exit, "ctrl+c under the ExitModal never quits"


async def test_ctrlq_under_exit_modal_never_stacks_second():
    """CDR-4 (the P9 stacking defect closed): the priority ctrl+q
    binding fires over open modals (the full binding-chain walk), so a
    ctrl+q pressed while an exit-family modal is top re-entered
    action_quit and stacked a second exit modal. The action_quit guard
    returns immediately when an ExitModal or QuitConfirmModal is top —
    no key combination can push a second exit-family modal while one is
    top (KillConfirmModal/E2PhraseModal deliberately out: quit over
    them is new legitimate intent)."""
    launcher = FakeLauncherService(live=("/repo/finetuned",))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        from tui.app import ExitModal

        await pilot.press("q")
        await pilot.pause()
        assert isinstance(app.screen, ExitModal)
        await pilot.press("ctrl+q")
        await pilot.pause()
        assert sum(isinstance(screen, ExitModal)
                   for screen in app.screen_stack) == 1, (
            "ctrl+q under the ExitModal must never stack a second one"
        )
        assert not app._exit, "ctrl+q under the ExitModal never exits"

    # the QuitConfirmModal twin: fresh app, no live sweep
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        from tui.app import QuitConfirmModal

        await pilot.press("q")
        await pilot.pause()
        assert isinstance(app.screen, QuitConfirmModal)
        await pilot.press("ctrl+q")
        await pilot.pause()
        assert sum(isinstance(screen, QuitConfirmModal)
                   for screen in app.screen_stack) == 1, (
            "ctrl+q under the QuitConfirmModal must never stack a second"
        )
        assert not app._exit, "ctrl+q under the QuitConfirmModal never exits"


async def test_exit_keys_below_min_grid_never_exit():
    """MAD-1/MAD-2: below 80x24 BOTH exit candidates — f10 (the
    priority binding) and ctrl+c (the withdrawn intercept's key) —
    open nothing and exit nothing: every path routes into action_quit
    whose first leg is the WR-06 posture (no chrome over the guard,
    never an unguarded exit), live sweep included. Before AND after
    pins (while f10 was inert nothing opened either; the intercept's
    below-grid leg already returned through the same guard)."""
    from tui.app import ExitModal, MinSizeScreen

    launcher = FakeLauncherService(live=("/repo/finetuned",))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.resize_terminal(60, 20)
        await pilot.pause()
        assert isinstance(app.screen, MinSizeScreen)
        await pilot.press("f10")
        await pilot.pause()
        assert not app._exit, "f10 below the min grid must never exit"
        assert not any(isinstance(screen, ExitModal)
                       for screen in app.screen_stack), (
            "no ExitModal may open over the min-size guard (f10)"
        )
        assert isinstance(app.screen, MinSizeScreen), (
            "the guard stays the top screen (f10)"
        )
        await pilot.press("ctrl+c")
        await pilot.pause()
        assert not app._exit, "ctrl+c below the min grid must never exit"
        assert not any(isinstance(screen, ExitModal)
                       for screen in app.screen_stack), (
            "no ExitModal may open over the min-size guard (ctrl+c)"
        )
        assert isinstance(app.screen, MinSizeScreen), (
            "the guard stays the top screen (ctrl+c)"
        )


# =====================================================================
# The 2026-10-17 16:02 exit-key final ruling (261017-mad) — F10 is the
# any-focus primary exit: a DECLARED priority binding (the probe-
# confirmed declarative seam; no on_event fallback), routing through the
# v0z confirm chain from ANY base-screen focus — including a focused
# Input (non-printable f10 passes the consume-key filter that strips
# printable priority bindings) — and over open modals (the ctrl+q P9
# mechanism, owned by the CDR-4 exit-family guard)
# =====================================================================


async def test_f10_no_sweep_opens_quit_confirm_over_focused_input():
    """MAD-1 (the 2026-10-17 16:02 final ruling): F10 is the ANY-FOCUS
    primary exit — the DECLARED priority binding fires over a focused
    base-screen Input (probe-pinned on textual 8.2.8: the App priority
    check runs BEFORE the focused-widget forward, and non-printable f10
    passes the consume-key filter that strips printable priority
    bindings), opening the QuitConfirmModal through the v0z chain (no
    live sweep), the Input value unchanged, no exit; y confirms the quit
    the f10 opened. The live-seam proof is this test itself: before the
    binding lands it fails with f10 inert (no modal opens)."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        from tui.app import QuitConfirmModal

        seeds_input = app.screen.query_one("#cfg-input-seeds", Input)
        seeds_input.focus()
        await pilot.pause()
        # collapse the select_on_focus whole-content auto-selection (the
        # WR-01 tests' selection-driving discipline): this leg pins the
        # PRIORITY reach itself, never any selection interplay
        await pilot.press("end")
        await pilot.pause()
        value_before = seeds_input.value
        await pilot.press("f10")
        await pilot.pause()
        assert isinstance(app.screen, QuitConfirmModal), (
            "f10 must fire the quit chain over a focused Input (the "
            "declared priority seam)"
        )
        assert not app._exit, "f10 alone never quits — the chain confirms"
        assert seeds_input.value == value_before, (
            "the f10 keypress is consumed — never typed into the Input"
        )
        await pilot.press("y")
        await pilot.pause()
        assert app._exit, "y confirms the quit the f10 opened"


async def test_f10_live_sweep_routes_to_exit_modal_over_focused_input():
    """MAD-1: with a live sweep, f10 from a focused Input routes to the
    ExitModal (the v0z live leg) — input unchanged, never exited. The
    F10 twin of the CDR-2 live-sweep leg; priority reach identical, only
    the modal differs."""
    launcher = FakeLauncherService(live=("/repo/finetuned",))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        from tui.app import ExitModal

        seeds_input = app.screen.query_one("#cfg-input-seeds", Input)
        seeds_input.focus()
        await pilot.pause()
        # collapse the select_on_focus auto-selection (the WR-01 idiom)
        await pilot.press("end")
        await pilot.pause()
        value_before = seeds_input.value
        await pilot.press("f10")
        await pilot.pause()
        assert isinstance(app.screen, ExitModal), (
            "f10 over a focused Input routes through the live-sweep leg"
        )
        assert not app._exit
        assert seeds_input.value == value_before, "f10 never types"


async def test_f10_under_exit_modal_never_stacks_second():
    """MAD-1: the priority f10 fires over open modals (the P9 mechanism,
    the ctrl+q twin) and re-enters action_quit, whose CDR-4 exit-family
    guard returns immediately — exactly ONE exit modal, never a second,
    never an exit."""
    launcher = FakeLauncherService(live=("/repo/finetuned",))
    app = _app(launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        from tui.app import ExitModal

        await pilot.press("q")
        await pilot.pause()
        assert isinstance(app.screen, ExitModal)
        await pilot.press("f10")
        await pilot.pause()
        assert sum(isinstance(screen, ExitModal)
                   for screen in app.screen_stack) == 1, (
            "f10 under the ExitModal must never stack a second one"
        )
        assert not app._exit, "f10 under the ExitModal never exits"

    # the QuitConfirmModal twin: fresh app, no live sweep
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        from tui.app import QuitConfirmModal

        await pilot.press("q")
        await pilot.pause()
        assert isinstance(app.screen, QuitConfirmModal)
        await pilot.press("f10")
        await pilot.pause()
        assert sum(isinstance(screen, QuitConfirmModal)
                   for screen in app.screen_stack) == 1, (
            "f10 under the QuitConfirmModal must never stack a second"
        )
        assert not app._exit, "f10 under the QuitConfirmModal never exits"


async def test_quit_confirm_footer_shows_y_n_keycaps():
    """CDR-3: the quit confirm's answer keys are visible at a glance —
    the y/n bindings carry show=True with the live-language
    LNC_EXIT_CONFIRM_YES/NO descriptions so the modal's Footer renders
    the y/n keycaps beside esc; enter stays show=False (the inert
    no-op is never advertised). QuitConfirmModal is in the L-toggle
    remap registry, so the keycaps re-derive on language switch."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("q")
        await pilot.pause()
        from textual.binding import Binding
        from textual.widgets import Footer as FooterWidget

        from tui.app import QuitConfirmModal
        from tui.strings import LNC_EXIT_CONFIRM_NO, LNC_EXIT_CONFIRM_YES

        assert isinstance(app.screen, QuitConfirmModal)
        entries = {binding.key: binding
                   for binding in QuitConfirmModal.BINDINGS
                   if isinstance(binding, Binding)}
        assert entries["y"].show is True, (
            "the y answer key must render in the Footer"
        )
        assert entries["y"].description == LNC_EXIT_CONFIRM_YES
        assert entries["n"].show is True, (
            "the n answer key must render in the Footer"
        )
        assert entries["n"].description == LNC_EXIT_CONFIRM_NO
        assert entries["enter"].show is False, (
            "the inert enter no-op is never advertised"
        )
        assert app.screen.query(FooterWidget), (
            "the modal composes a Footer — the keycaps render"
        )


async def test_quit_confirm_message_bolds_y_n_tokens():
    """CDR-3: the message's [Y]/[N] tokens are prominent — the message
    Static's content is a rich Text (the Text API, never markup
    strings: Text content is never markup-parsed, so the bracket tokens
    stay literal) with a bold span covering every [Y] and [N]
    occurrence; the plain value still carries LNC_EXIT_CONFIRM
    byte-unchanged so every existing content assertion keeps passing."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("q")
        await pilot.pause()
        from tui.app import QuitConfirmModal
        from tui.strings import LNC_EXIT_CONFIRM

        assert isinstance(app.screen, QuitConfirmModal)
        content = app.screen.query(Static)[0].content
        assert isinstance(content, Text), (
            "the message composes as a rich Text over the registry "
            "constant — never a markup string"
        )
        plain = content.plain
        assert LNC_EXIT_CONFIRM in plain, plain
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


async def test_launch_confirm_footer_shows_y_n_keycaps():
    """DNR-1 (261017-dnr): the launch confirm's answer keys are visible
    at a glance — the LaunchConfirmModal y/n bindings carry show=True
    with the live-language descriptions (LNC_GATE_CONFIRM_YES /
    LNC_EXIT_CONFIRM_NO — the exact reuse) so every launch surface's
    Footer (the slot-4 gate AND the monitor re-run, both this base)
    renders the y/n keycaps beside esc; the inherited base enter stays
    show=False (the EHC-2 inert no-op is never advertised)."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(summary=GateSummary(
        models=1, tasks=1, seeds=3, cells=3, output_root="./finetuned",
        is_e2x=False, expected_phrase="finetuned"))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")   # the picker holds focus: the gate
        await _settle(pilot, app, rounds=4)
        from textual.binding import Binding
        from textual.widgets import Footer as FooterWidget

        from tui.screens.selection import ConfirmModal, LaunchConfirmModal
        from tui.strings import (
            LNC_EXIT_CONFIRM_NO,
            LNC_GATE_CONFIRM_YES,
        )

        assert isinstance(app.screen, LaunchConfirmModal), (
            "the slot-4 gate confirm is the launch variant"
        )
        entries = {binding.key: binding
                   for binding in LaunchConfirmModal.BINDINGS
                   if isinstance(binding, Binding)}
        assert entries["y"].show is True, (
            "the y answer key must render in the Footer"
        )
        assert entries["y"].description == LNC_GATE_CONFIRM_YES
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


async def test_gate_confirm_message_bolds_y_n_tokens():
    """DNR-1 (261017-dnr): the gate confirm line's [Y]/[N] tokens are
    prominent — the message Static's content is a rich Text (the cdr
    Text-API pattern: never markup strings, the bracket tokens stay
    literal) with a bold span covering every [Y] and [N] occurrence;
    the plain value still carries LNC_GATE_CONFIRM byte-unchanged so
    every existing _plain()/str() content assertion keeps passing."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(summary=GateSummary(
        models=1, tasks=1, seeds=3, cells=3, output_root="./finetuned",
        is_e2x=False, expected_phrase="finetuned"))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")   # the gate
        await _settle(pilot, app, rounds=4)
        from tui.strings import LNC_GATE_CONFIRM

        content = app.screen.query_one("#cfg-gate-message", Static).content
        assert isinstance(content, Text), (
            "the confirm line composes as a rich Text over the registry "
            "constant — never a markup string"
        )
        plain = content.plain
        assert LNC_GATE_CONFIRM in plain, plain
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


async def test_e2_matched_indicator_bolds_tokens_keycaps_stay_hidden():
    """DNR-3 (261017-dnr): on the exact-phrase match the indicator's
    [Y]/[N] tokens render bold (the matched branch only — the mismatch
    branch stays a plain string), with .plain still equal to
    LNC_E2_MATCH_OK; the y/n bindings STAY show=False by design — they
    only arm after the matched-enter blur, and a visible y keycap while
    the Input holds focus would advertise a key that types into it."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(summary=GateSummary(
        models=62, tasks=50, seeds=3, cells=9300,
        output_root="./finetuned", is_e2x=True,
        expected_phrase="finetuned"))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")   # the gate escalates to E2'
        await _settle(pilot, app, rounds=4)
        from textual.binding import Binding

        from tui.screens.run_config import E2PhraseModal
        from tui.strings import LNC_E2_MATCH_OK

        assert isinstance(app.screen, E2PhraseModal)
        for char in "finetuned":
            await pilot.press(char)
        await pilot.pause()
        indicator = app.screen.query_one("#cfg-e2-indicator", Static)
        content = indicator.content
        assert isinstance(content, Text), (
            "the MATCHED indicator composes as a rich Text (the bold "
            "token pattern); the mismatch branch stays a plain string"
        )
        assert _plain(content) == LNC_E2_MATCH_OK
        plain = content.plain
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
        # the DNR-3 pin: the y/n keycaps stay hidden while the Input
        # holds focus (armed-after-blur semantics — visibility would
        # advertise a key that types into the Input)
        entries = {binding.key: binding
                   for binding in E2PhraseModal.BINDINGS
                   if isinstance(binding, Binding)}
        assert entries["y"].show is False, (
            "y stays hidden until the matched-enter blur arms it"
        )
        assert entries["n"].show is False, (
            "n stays hidden until the matched-enter blur arms it"
        )


async def test_peft_choice_radioset_flow():
    """The PEFT choice row: enter opens the RadioSet; picking lora
    writes the param, persists, refreshes the preview + alias hint."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        from tui.screens.run_config import ChoiceRow

        peft_row = screen.query_one("#cfg-value-peft", ChoiceRow)
        peft_row.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        from textual.widgets import RadioSet as RadioSetWidget

        from tui.screens.run_config import ChoiceModal

        assert isinstance(app.screen, ChoiceModal)
        assert app.screen.query_one(RadioSetWidget) is not None
        # navigate to lora (the second radio) and press it
        await pilot.press("down")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert _plain(peft_row.content).startswith("lora")
        assert run_service.saved_specs[-1].peft == "lora"
        hint = screen.query_one("#cfg-hint-peft", Static)
        assert hint.display
        from tui.strings import CFG_PEFT_ALIAS_PREVIEW

        assert CFG_PEFT_ALIAS_PREVIEW.format(
            model="model-a", mode="lora") in _plain(hint.content)


async def test_variant_choice_probe_hint_flow():
    """The variant RadioSet: probe selection surfaces the ⚠ hint naming
    the frozen intersection (model-a is in the fake's frozen set)."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        from tui.screens.run_config import ChoiceRow

        variant_row = screen.query_one("#cfg-value-variant", ChoiceRow)
        variant_row.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        # probe is the third option (none/head/probe): two downs
        await pilot.press("down")
        await pilot.press("down")
        await pilot.pause()
        await pilot.press("enter")
        await _settle(pilot, app)
        assert run_service.saved_specs[-1].config_variant == "probe"
        hint = screen.query_one("#cfg-hint-variant-probe", Static)
        assert hint.display
        from tui.strings import CFG_VARIANT_PROBE_HINT

        assert CFG_VARIANT_PROBE_HINT.format(
            models="model-a") in _plain(hint.content)


async def test_subset_toggle_copy_pair():
    """The fairness-subset toggle: off renders the dim default; on
    renders the path value + reveals the path Input + persists the
    subset file through the worker."""
    run_service = FakeRunConfigService()
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        value = screen.query_one("#cfg-subset-value", Static)
        assert CFG_SUBSET_OFF in _plain(value.content)
        assert not screen.query_one("#cfg-input-subset", Input).display
        checkbox = screen.query_one("#cfg-subset-toggle", Checkbox)
        checkbox.focus()
        await pilot.pause()
        await pilot.press("space")
        await _settle(pilot, app)
        from tui.strings import CFG_SUBSET_ON

        assert CFG_SUBSET_ON.format(
            path="pipeline/eval_subsets.json") in _plain(value.content)
        assert screen.query_one("#cfg-input-subset", Input).display
        # the spec carries the subset file through the worker save
        assert (run_service.saved_specs[-1].subset_file
                == "pipeline/eval_subsets.json")


# =====================================================================
# Task 1 — the i18n grep lock (the 11-05 contract note)
# =====================================================================

def test_run_config_module_carries_zero_chinese_literals():
    """I18N-01 single home: no operator-facing copy in the screen.

    WR-08 (phase-12 review): the scan now also covers the CJK
    punctuation + fullwidth-form ranges (U+3000–U+303F, U+FF00–U+FFEF)
    — the subset-OFF copy's fullwidth parentheses previously composed
    inline in the screen and were INVISIBLE to the ideograph-only
    regex, so the lock passed while the single-home contract was
    violated."""
    source = _RUN_CONFIG_MODULE_FILE.read_text(encoding="utf-8")
    offenders = re.findall(r"[一-鿿　-〿＀-￯]", source)
    assert not offenders, (
        "Chinese literals (incl. CJK punctuation / fullwidth forms) "
        "must live in tui/strings.py only "
        f"({len(offenders)} found in {_RUN_CONFIG_MODULE_FILE.name})"
    )


# =====================================================================
# Task 3 — the D-13 launch -> auto-nav integration (11-07)
# =====================================================================

async def test_launch_success_auto_navigates_to_monitor_attached():
    """D-13: a confirmed launch fires the toast, then auto-navigates to
    the monitor screen with the new sweep attached and the expected
    total threaded; a q press then opens the ExitModal (live sweep)."""
    from tui.app import ExitModal
    from tui.screens.monitor import MonitorScreen
    from tui.strings import LNC_EXIT_MESSAGE

    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(
        summary=GateSummary(
            models=1, tasks=1, seeds=3, cells=3, output_root="./finetuned",
            is_e2x=False, expected_phrase="finetuned"),
        live=("/repo/finetuned",))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")   # the gate
        await _settle(pilot, app, rounds=4)
        from tui.screens.selection import ConfirmModal

        assert isinstance(app.screen, ConfirmModal)
        await pilot.press("y")   # confirm the launch (EHC-2)
        await _settle(pilot, app, rounds=4)

        # the D-13 proof: the ACTIVE screen is the monitor, attached
        assert isinstance(app.screen, MonitorScreen), (
            "a successful launch auto-navigates to the monitor screen"
        )
        screen = app.screen
        # 261018-kvj: the attach concept retired with the two-tab
        # redesign — the D-13 survival proof is the session's stats seams
        assert screen._expected_totals.get("/repo/finetuned") == 3, (
            "the launch plan threads the expected total (the 11-04 seam)"
        )
        assert screen._fallback_starts.get("/repo/finetuned") is not None

        # the q intercept: a live sweep present via the fake launcher
        await pilot.press("q")
        await _settle(pilot, app)
        assert isinstance(app.screen, ExitModal), (
            "q with a live sweep opens the ExitModal, never quits"
        )
        message = str(app.screen._message)
        assert LNC_EXIT_MESSAGE.format(
            done="1", total="3", root="finetuned") in message, (
            f"the live counts thread from the monitor (is {message!r})"
        )
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, MonitorScreen)


# =====================================================================
# Delta B (Phase 12, 12-03) — modal dismiss returns focus to the picker
#
# The 11-UAT advisory #1 trap: Textual restores the PRE-MODAL focused
# widget on modal pop, and the gate pipeline pushes its modals from
# async worker messages — so the operator can be typing in a params
# Input when the modal lands. B1: after ANY slot-4 modal dismisses
# (esc / cancel / confirm / submit paths), app.focused is the
# #cfg-picker PickerList. B2: digits navigate immediately after. B3:
# the filter-Enter precedent is unchanged. B4: defensive degrade when
# the screen below carries no picker.
# =====================================================================

def _assert_focused_picker(app, screen):
    """B1's single assertion: focus IS the picker (never an Input)."""
    picker = screen.query_one("#cfg-picker", PickerList)
    assert app.focused is picker, (
        f"B1: focus must return to #cfg-picker (is {app.focused!r})"
    )
    return picker


async def _settle_dismiss(pilot):
    """Await the pop + the call_after_refresh focus callback."""
    await pilot.pause()
    await pilot.pause()


class _GatedConfirmLauncher(FakeLauncherService):
    """The confirm-data worker gated by a test Event (the deterministic
    trap: the modal pushes from the worker while a params Input holds
    focus — the UAT deadlock shape, never a timed sleep)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gate: threading.Event | None = None

    def gate_confirm_data(self, spec):
        if self.gate is not None:
            self.gate.wait(timeout=10)
        return super().gate_confirm_data(spec)


class _GatedPreviewService(FakeRunConfigService):
    """The enumeration worker's preview leg gated (same trap shape).

    The gate arms explicitly BEFORE the [enter] press so the mount-time
    preview worker runs ungated.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gate: threading.Event | None = None

    def preview(self, spec):
        self.preview_calls.append(spec)
        if self.gate is not None:
            self.gate.wait(timeout=10)
        return FakeRunConfigService.preview(self, spec)


class _GatedEnvLauncher(FakeLauncherService):
    """The env-preflight worker gated (same trap shape)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gate: threading.Event | None = None

    def env_preflight(self, kernels=None):
        if self.gate is not None:
            self.gate.wait(timeout=10)
        return super().env_preflight(kernels)


def _trap_run_service():
    """The gate-viable spec fixture (1 model x 1 task x 3 seeds)."""
    return FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))


async def _park_focus_in_params_input(pilot, app):
    """Park screen focus in the seeds Input (the trap surface)."""
    seeds = app.screen.query_one("#cfg-input-seeds", Input)
    seeds.focus()
    await pilot.pause()
    assert app.focused is seeds
    return seeds


async def test_b1_preview_modal_esc_refocuses_picker():
    """[p] from a params-pane focus surface; esc -> the picker (B1)."""
    app = _app(run_service=_trap_run_service())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        from tui.screens.run_config import PreviewModal

        # park focus on a params-pane row (pre-modal focus != picker)
        peft_row = screen.query_one("#cfg-value-peft")
        peft_row.focus()
        await pilot.pause()
        await pilot.press("p")
        await pilot.pause()
        assert isinstance(app.screen, PreviewModal)
        await pilot.press("escape")
        await _settle_dismiss(pilot)
        _assert_focused_picker(app, screen)


async def test_b1_choice_modal_esc_and_pick_refocuses_picker():
    """The RadioSet choice modal: BOTH dismiss paths (esc + the
    radio-pick) land on the picker (B1)."""
    app = _app(run_service=_trap_run_service())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        from tui.screens.run_config import ChoiceModal

        peft_row = screen.query_one("#cfg-value-peft")
        # esc path
        peft_row.focus()
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, ChoiceModal)
        await pilot.press("escape")
        await _settle_dismiss(pilot)
        _assert_focused_picker(app, screen)
        # the radio-pick path (dismiss via on_radio_set_changed)
        peft_row.focus()
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, ChoiceModal)
        await pilot.press("down")
        await pilot.press("enter")
        await pilot.pause()
        _assert_focused_picker(app, screen)


async def test_b1_gate_confirm_esc_refocuses_picker_digits_navigate():
    """THE UAT deadlock reproduction: the confirm modal pushed from the
    gated worker while the seeds Input held focus; esc lands on the
    picker (B1) and the very next digit navigates (B2)."""
    release = threading.Event()
    launcher = _GatedConfirmLauncher(summary=GateSummary(
        models=1, tasks=1, seeds=3, cells=3, output_root="./finetuned",
        is_e2x=False, expected_phrase="finetuned"))
    app = _app(run_service=_trap_run_service(), launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        from tui.screens.data_manager import DataManagerScreen
        from tui.screens.selection import ConfirmModal

        launcher.gate = release          # arm the trap (modal not yet up)
        await pilot.press("enter")       # the gate pipeline starts
        await _park_focus_in_params_input(pilot, app)
        release.set()                    # the confirm modal lands NOW
        await _settle(pilot, app, rounds=4)
        assert isinstance(app.screen, ConfirmModal)
        await pilot.press("escape")
        await _settle_dismiss(pilot)
        _assert_focused_picker(app, screen)
        # B2: the nav digit is consumed by the shell, not the Input
        await pilot.press("3")
        await _settle(pilot, app)
        assert isinstance(app.screen, DataManagerScreen), (
            "B2: after a modal dismiss the digit keys must navigate"
        )


async def test_b1_gate_problems_esc_refocuses_picker():
    """The problems modal from the gated enumeration worker; esc ->
    the picker (B1)."""
    release = threading.Event()
    run_service = _GatedPreviewService()   # empty spec -> problems
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        from tui.screens.run_config import ProblemsModal

        run_service.gate = release
        await pilot.press("enter")
        await _park_focus_in_params_input(pilot, app)
        release.set()
        await _settle(pilot, app, rounds=4)
        assert isinstance(app.screen, ProblemsModal)
        await pilot.press("escape")
        await _settle_dismiss(pilot)
        _assert_focused_picker(app, screen)


async def test_b1_env_block_esc_refocuses_picker():
    """The env-block refusal from the gated env worker; esc -> the
    picker (B1)."""
    release = threading.Event()
    launcher = _GatedEnvLauncher(preflight=EnvPreflight(
        can_launch=False,
        reasons=("FAIL: python_kernel — torch missing",),
        failed_kernels=("python_kernel",)))
    app = _app(run_service=_trap_run_service(), launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        from tui.screens.run_config import EnvBlockModal

        launcher.gate = release
        await pilot.press("enter")
        await _park_focus_in_params_input(pilot, app)
        release.set()
        await _settle(pilot, app, rounds=4)
        assert isinstance(app.screen, EnvBlockModal)
        await pilot.press("escape")
        await _settle_dismiss(pilot)
        _assert_focused_picker(app, screen)


async def test_b1_e2x_phrase_modal_esc_refocuses_picker():
    """The E2' typed-phrase modal (its Input takes focus on mount);
    esc -> the picker (B1)."""
    release = threading.Event()
    launcher = _GatedConfirmLauncher(summary=GateSummary(
        models=62, tasks=50, seeds=3, cells=9300,
        output_root="./finetuned", is_e2x=True,
        expected_phrase="finetuned"))
    app = _app(run_service=_trap_run_service(), launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        from tui.screens.run_config import E2PhraseModal

        launcher.gate = release
        await pilot.press("enter")
        await _park_focus_in_params_input(pilot, app)
        release.set()
        await _settle(pilot, app, rounds=4)
        assert isinstance(app.screen, E2PhraseModal)
        assert app.focused is app.screen.query_one("#cfg-e2-input", Input)
        await pilot.press("escape")
        await _settle_dismiss(pilot)
        _assert_focused_picker(app, screen)


async def test_b1_e2x_submit_path_refocuses_picker():
    """The E2' matched-enter submit path (dismiss via
    on_input_submitted): a FAILED spawn keeps the app on slot 4 (no
    D-13 auto-nav) so the focus landing is assertable (B1)."""
    release = threading.Event()
    launcher = _GatedConfirmLauncher(
        summary=GateSummary(
            models=62, tasks=50, seeds=3, cells=9300,
            output_root="./finetuned", is_e2x=True,
            expected_phrase="finetuned"),
        outcomes=[LaunchOutcome(
            spawned=False, root="", tee_path=None, error="boom")])
    app = _app(run_service=_trap_run_service(), launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        from tui.screens.run_config import E2PhraseModal

        launcher.gate = release
        await pilot.press("enter")
        await _park_focus_in_params_input(pilot, app)
        release.set()
        await _settle(pilot, app, rounds=4)
        assert isinstance(app.screen, E2PhraseModal)
        for char in "finetuned":
            await pilot.press(char)
        await pilot.pause()
        await pilot.press("enter")   # the matched ADVANCE: blur, no launch
        await pilot.pause()
        await pilot.press("y")       # the y submit: dismiss + launch (EHC-2)
        await _settle(pilot, app, rounds=3)
        assert isinstance(app.screen, RunConfigScreen), (
            "the failed spawn keeps the console on slot 4"
        )
        _assert_focused_picker(app, screen)


async def test_b2_digit_navigates_immediately_after_preview_dismiss():
    """B2 standalone: right after the [p] esc, digit 3 switches the
    screen (the nav shell owns the key)."""
    app = _app(run_service=_trap_run_service())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        from tui.screens.data_manager import DataManagerScreen

        await pilot.press("p")
        await pilot.pause()
        await pilot.press("escape")
        await _settle_dismiss(pilot)
        await pilot.press("3")
        await _settle(pilot, app)
        assert isinstance(app.screen, DataManagerScreen)


async def test_b3_filter_enter_returns_to_picker_unchanged():
    """B3: the filter Input's Enter-returns-to-picker precedent is
    unchanged (run_config.py:1388-1389 — the pattern the fix rides)."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        await pilot.press("slash")
        await pilot.pause()
        assert app.focused is screen.query_one("#cfg-filter", Input)
        await pilot.press("enter")
        await pilot.pause()
        _assert_focused_picker(app, screen)


async def test_b4_dismiss_without_picker_below_degrades_to_plain_pop():
    """B4 defensive edge: the base over a screen with no #cfg-picker
    (never slot 4 — a pushed-from-elsewhere modal) degrades to a plain
    pop, never crashes."""
    from textual.binding import Binding

    from tui.screens.env_check import EnvCheckScreen
    from tui.screens.run_config import _PickerReturnModal
    from tui.strings import APP_MODAL_BACK_LABEL

    class _BareModal(_PickerReturnModal):
        """The base with only the escape binding (no picker below)."""
        BINDINGS: ClassVar[list[Binding]] = [
            Binding("escape", "dismiss", APP_MODAL_BACK_LABEL)]

    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()   # booted on the env-check screen
        assert isinstance(app.screen, EnvCheckScreen)
        app.push_screen(_BareModal())
        await pilot.pause()
        assert isinstance(app.screen, _BareModal)
        await pilot.press("escape")
        await _settle_dismiss(pilot)
        assert isinstance(app.screen, EnvCheckScreen), (
            "the override degrades to a plain pop when no picker below"
        )


# =====================================================================
# 261014-f4w — the log-dir row, the [s] save action, and the ctrl+o
# directory picker (Task 3)
# =====================================================================


class _PersistingRunService(FakeRunConfigService):
    """The fake with save_state ALSO writing the REAL state file — the
    no-bypass proof for the picker path (the picked value must flow
    through the normal Input.Changed -> preview-worker persist path,
    observed on disk, not around it)."""

    def save_state(self, spec):
        super().save_state(spec)
        run_config_service.save_state(spec)


class _RealLoadRunService(FakeRunConfigService):
    """The fake with load_state delegating to the REAL service — the
    seeded-prefill proof (the seeding lives inside the real load_state;
    the fake side stays for the picker entries and preview)."""

    def load_state(self):
        return run_config_service.load_state()


async def test_log_dir_row_renders_with_placeholder_hint():
    """The log-dir row (the model-root row twin): label renders, value
    empty, the placeholder == CFG_LOG_DIR_DEFAULT, the advisory slot
    exists (261014-f4w, F4W-03)."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        log_dir = screen.query_one("#cfg-input-log-dir", Input)
        assert log_dir.value == ""
        assert _plain(log_dir.placeholder) == CFG_LOG_DIR_DEFAULT
        assert _label_text(screen, "#cfg-label-log-dir") == (
            CFG_FIELD_LOG_DIR)
        assert screen.query_one("#cfg-adv-log-dir", Static) is not None


async def test_log_dir_input_threads_absolute_flag_into_argv():
    """Typing /mnt/logs into #cfg-input-log-dir composes a spec whose
    service-side argv carries --log_dir as the RESOLVED ABSOLUTE string
    (the test_model_root_input_threads_absolute_flag_into_argv shape),
    joined after --dataset_root in the pinned tail."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        log_dir = screen.query_one("#cfg-input-log-dir", Input)
        log_dir.value = "/mnt/logs"
        await _settle(pilot, app)
        saved = run_service.saved_specs[-1]
        assert saved.log_dir == "/mnt/logs"
        argv = run_config_service.compose_argv(saved)
        assert argv[argv.index("--log_dir") + 1] == "/mnt/logs"
        assert "--dataset_root" not in argv, (
            "the untouched dataset-root field contributes nothing"
        )


async def test_save_defaults_writes_file_and_toasts_path(
        tmp_path, monkeypatch):
    """[s] (focus outside an Input — Inputs consume printable keys)
    composes the spec from the inputs and writes the five-key
    schema-1 document under the injected config root; the toast names
    the written path; unset dirs persist as \"\" (F4W-03)."""
    import directories_config

    config_root = tmp_path / "f4w-save-config"
    config_root.mkdir()
    monkeypatch.setenv(tui_settings.CONFIG_DIR_ENV, str(config_root))
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        screen.query_one("#cfg-input-model-root", Input).value = "/mnt/models"
        await _settle(pilot, app)
        # focus sits on the picker (never inside an Input) — [s] fires
        screen.query_one("#cfg-picker", PickerList).focus()
        await pilot.press("s")
        await pilot.pause()
        written = config_root / directories_config.DIRECTORIES_FILE_NAME
        assert written.is_file(), "the [s] action wrote directories.json"
        doc = json.loads(written.read_text(encoding="utf-8"))
        assert doc["schema_version"] == 1
        assert doc["model_root"] == "/mnt/models"
        assert doc["dataset_root"] == ""
        assert doc["log_dir"] == ""
        assert CFG_SAVE_DEFAULTS_TOAST.format(path=str(written)) in (
            _toast_messages(app)), "the toast names the written path"


async def test_mount_prefills_dir_inputs_from_directories_json(
        tmp_path, monkeypatch):
    """The seeded prefill: with a directories.json present and no
    run_config.json, a fresh mount shows the file's value in the
    corresponding dir input (the file seeds DEFAULTS through the one
    load_state seam — F4W-01's TUI half)."""
    import directories_config

    monkeypatch.setenv(tui_settings.STATE_DIR_ENV, str(tmp_path / "state"))
    config_root = tmp_path / "f4w-prefill-config"
    config_root.mkdir()
    monkeypatch.setenv(tui_settings.CONFIG_DIR_ENV, str(config_root))
    (config_root / directories_config.DIRECTORIES_FILE_NAME).write_text(
        json.dumps({
            "model_root": str(tmp_path / "file-models"),
            "log_dir": str(tmp_path / "file-logs"),
        }),
        encoding="utf-8",
    )
    app = _app(run_service=_RealLoadRunService())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        assert screen.query_one("#cfg-input-model-root", Input).value == (
            str(tmp_path / "file-models"))
        assert screen.query_one("#cfg-input-log-dir", Input).value == (
            str(tmp_path / "file-logs"))
        assert screen.query_one("#cfg-input-dataset-root", Input).value == ""


async def test_dir_picker_selects_through_the_normal_persist_path(
        tmp_path, monkeypatch):
    """F4W-05's full loop: focus a dir input, ctrl+o mounts the picker
    rooted at its value; the tree lists directories only; enter
    descends a collapsed node; [f] fills the input with the picked
    directory's ABSOLUTE path, closes with focus restored, and the
    picked value reaches the PERSISTED state file through the normal
    preview path (the no-bypass proof)."""
    state = tmp_path / "state"
    monkeypatch.setenv(tui_settings.STATE_DIR_ENV, str(state))
    root = tmp_path / "a"
    (root / "b" / "sub").mkdir(parents=True)
    (root / "c").mkdir()
    (root / "not-a-dir.txt").write_text("file", encoding="utf-8")
    run_service = _PersistingRunService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        model_root = screen.query_one("#cfg-input-model-root", Input)
        model_root.value = str(root)
        await _settle(pilot, app)
        model_root.focus()
        await pilot.press("ctrl+o")
        await pilot.pause(0.3)  # the async first-children load
        assert isinstance(app.screen, DirPickerModal)
        tree = app.screen.query_one("#cfg-dirpick-tree", DirectoryTree)
        child_names = {
            Path(str(node.data.path)).name
            for node in tree.root.children
        }
        assert child_names == {"b", "c"}, (
            "directories only — the file node never appears"
        )
        # descend: cursor onto b (line 0 is the root), enter expands it
        await pilot.press("down")
        await pilot.press("enter")
        await pilot.pause(0.3)  # b's children load asynchronously
        assert isinstance(app.screen, DirPickerModal), (
            "enter on a COLLAPSED node descends, never fills+closes"
        )
        # the dedicated select key fills through the normal path
        await pilot.press("f")
        await pilot.pause()
        assert not isinstance(app.screen, DirPickerModal), "the modal closed"
        picked = str((root / "b").resolve())
        assert model_root.value == picked
        assert app.focused is model_root, (
            "focus returns to the ORIGIN INPUT, never the picker"
        )
        await _settle(pilot, app)
        doc = json.loads(
            (state / "run_config.json").read_text(encoding="utf-8"))
        assert doc["dirs"]["model_root"] == picked, (
            "the picked value flowed through the normal Input.Changed -> "
            "preview-worker persist path (no bypass)"
        )


async def test_dir_picker_esc_cancels_unchanged(tmp_path, monkeypatch):
    """esc cancels: the input value and the persisted state file are
    untouched, focus still returns to the origin input."""
    state = tmp_path / "state"
    monkeypatch.setenv(tui_settings.STATE_DIR_ENV, str(state))
    root = tmp_path / "a"
    (root / "b").mkdir(parents=True)
    run_service = _PersistingRunService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        model_root = screen.query_one("#cfg-input-model-root", Input)
        model_root.value = str(root)
        await _settle(pilot, app)
        before = (state / "run_config.json").read_text(encoding="utf-8")
        model_root.focus()
        await pilot.press("ctrl+o")
        await pilot.pause(0.3)
        assert isinstance(app.screen, DirPickerModal)
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, DirPickerModal)
        assert model_root.value == str(root), "the value is untouched"
        assert app.focused is model_root
        assert (state / "run_config.json").read_text(
            encoding="utf-8") == before


async def test_dir_picker_roots_at_nearest_existing_ancestor(
        tmp_path, monkeypatch):
    """The fallback chain in the UI: a value pointing at a nonexistent
        deep path roots the tree at its nearest EXISTING ancestor (the
        tmp root)."""
    root = tmp_path / "a"
    root.mkdir()
    deep = root / "x" / "y" / "z"
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        model_root = screen.query_one("#cfg-input-model-root", Input)
        model_root.value = str(deep)
        await pilot.pause()
        model_root.focus()
        await pilot.press("ctrl+o")
        await pilot.pause(0.3)
        assert isinstance(app.screen, DirPickerModal)
        tree = app.screen.query_one("#cfg-dirpick-tree", DirectoryTree)
        assert Path(str(tree.path)) == root.resolve(), (
            "the tree roots at the deep path's nearest existing ancestor"
        )


# =====================================================================
# 261016-poa Task 1 — toggle anchor preservation (UX-1) + contrast pin
# (UX-2)
# =====================================================================


def _wide_entries(n=40):
    """The scrollable picker fixture: ``n`` sortable model keys (the
    list must overflow every design-grid viewport so the toggle path's
    scroll behavior is observable)."""
    return PickerEntries(
        model_entries=tuple(
            _model_entry(f"model-{i:02d}") for i in range(n)),
        dataset_entries=tuple(_FAKE_DATASETS),
        custom_status={},
    )


async def _walk_to_midviewport_scrolled(pilot, app, downs=35, ups=3):
    """Drive the cursor DEEP (past the bottom edge — the list scrolls,
    the cursor rides the edge) then back up so it sits MID-viewport over
    a scrolled list: the exact state a rebuild's bottom-edge snap
    breaks (a cursor still ON the edge re-lands on the edge and hides
    the bug)."""
    picker = app.screen.query_one("#cfg-picker", PickerList)
    for _ in range(downs):
        await pilot.press("down")
    for _ in range(ups):
        await pilot.press("up")
    await pilot.pause()
    before_y = picker.scroll_offset.y
    before_key = picker.key_at(picker.highlighted)
    assert before_y > 0, (
        "the fixture must scroll — a deeper cursor or smaller viewport"
    )
    return picker, before_key, before_y


async def test_space_toggle_deep_row_keeps_cursor_key_and_scroll_offset():
    """UX-1 (261016-poa): space-toggling a DEEP row in a scrolled picker
    leaves BOTH the highlighted registry key and the EXACT scroll offset
    unchanged. Pre-fix, the toggle's full rebuild ran
    ``PickerList.set_rows`` -> ``clear_options`` (textual 8.2.8 resets
    the scroll) -> highlighted restore -> ``watch_highlighted``'s
    ``scroll_to_region(force=True)`` snapped the cursor row to the
    viewport's BOTTOM EDGE — the visible list jump the maintainer
    reported. The fix pins the final offset to the captured pre-toggle
    value (byte-stable, never edge-derived)."""
    run_service = FakeRunConfigService(entries=_wide_entries())
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        picker = screen.query_one("#cfg-picker", PickerList)
        assert app.focused is picker
        picker, before_key, before_y = await _walk_to_midviewport_scrolled(
            pilot, app)
        await pilot.press("space")
        await _settle(pilot, app)
        assert picker.key_at(picker.highlighted) == before_key, (
            "the cursor stays on the SAME registry key across the toggle"
        )
        assert picker.scroll_offset.y == before_y, (
            "the scroll offset is byte-stable across the toggle — no "
            f"bottom-edge snap (was {before_y}, is "
            f"{picker.scroll_offset.y})"
        )
        assert run_service.saved_specs[-1].models == (before_key,), (
            "the toggled model joined the spec (the mark round-trip "
            "through the fake's save_state)"
        )


async def test_screen_space_toggle_keeps_cursor_key_and_scroll_offset():
    """UX-1 screen-level path: [space] with focus OFF the picker (a
    params choice row — no space binding of its own) marks the picker's
    cursor row through the screen action; the SAME key + scroll
    invariants hold (both mark paths funnel through the one anchored
    rebuild)."""
    run_service = FakeRunConfigService(entries=_wide_entries())
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        picker = screen.query_one("#cfg-picker", PickerList)
        picker, before_key, before_y = await _walk_to_midviewport_scrolled(
            pilot, app)
        # focus OFF the picker: the screen-level space action fires
        screen.query_one("#cfg-value-peft").focus()
        await pilot.pause()
        assert app.focused is not picker
        await pilot.press("space")
        await _settle(pilot, app)
        assert picker.key_at(picker.highlighted) == before_key, (
            "the screen-space path keeps the cursor key too"
        )
        assert picker.scroll_offset.y == before_y, (
            "the screen-space path keeps the scroll offset too"
        )
        assert run_service.saved_specs[-1].models == (before_key,), (
            "the screen-space path marks the same cursor row"
        )


def test_styles_carry_picker_scoped_selected_contrast_rule():
    """UX-2: styles.tcss overrides the MARKED-row component classes
    scoped to the PickerList TYPE selector ONLY. textual 8.2.8's
    SelectionList DEFAULT_CSS renders the marked row as $text-success on
    $panel (low contrast — the maintainer complaint); a bare
    ``SelectionList``/``OptionList`` rule would also restyle the
    selection screen's preset picker and the wizard's enum lists and
    drift THEIR goldens — forbidden. Presence pin; the visual truth is
    the run_config golden + the maintainer D-03 review."""
    tcss_path = (Path(__file__).resolve().parents[2] / "tui"
                 / "styles.tcss")
    source = tcss_path.read_text(encoding="utf-8")
    assert "PickerList > .selection-list--button-selected" in source, (
        "the selected component class is overridden on PickerList"
    )
    assert ("PickerList > .selection-list--button-selected-highlighted"
            in source), (
        "the selected+highlighted component class is overridden too"
    )
    assert "SelectionList >" not in source and (
        "\nSelectionList" not in source), (
        "no bare SelectionList rule — the selection screens' own lists "
        "must keep the 8.2.8 default (their goldens stay byte-identical)"
    )
    assert "OptionList >" not in source and "\nOptionList" not in source, (
        "no bare OptionList rule (same scope-leak guard)"
    )


async def test_filter_and_kind_flip_rebuilds_keep_index_clamp():
    """UX-1 regression pin: the anchor restore rides ONLY the toggle
    paths — the filter-typing and m-kind-flip rebuilds keep today's
    index-clamp behavior exactly (highlighted = min(previous, last
    row), no scroll restore)."""
    run_service = FakeRunConfigService(entries=_wide_entries())
    app = _app(run_service=run_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        picker = screen.query_one("#cfg-picker", PickerList)
        for _ in range(5):
            await pilot.press("down")
        await pilot.pause()
        assert picker.highlighted == 5
        # the m flip: 40 model rows -> 2 dataset rows; the clamp lands
        # on the LAST dataset row (min(5, 1) == 1)
        await pilot.press("m")
        await pilot.pause()
        assert picker.highlighted == 1
        assert picker.key_at(picker.highlighted) == "task-2"
        # flip back (clamp min(1, 39) == 1) then narrow to one row via
        # the filter: the clamp lands on the single surviving row
        await pilot.press("m")
        await pilot.pause()
        assert picker.highlighted == 1
        await pilot.press("slash")
        await pilot.pause()
        for char in "model-07":
            await pilot.press(char)
        await pilot.pause()
        assert picker.highlighted == 0
        assert picker.key_at(picker.highlighted) == "model-07"


# =====================================================================
# 261016-poa Task 2 — the launch-confirmation flow: planned-pair task
# list (UX-5), Y/N (UX-6), the entry hint line (UX-4)
# =====================================================================


def _pairs_fixture(n=20):
    """n scripted (model, task) pairs for the capped-list assertions."""
    return tuple(
        (f"model-{i:02d}", f"task-{i:02d}") for i in range(n))


async def test_gate_confirm_modal_lists_planned_pairs_capped():
    """UX-5: the non-E2' confirm modal lists the ACTUAL plan under the
    counts formula — one 模型+数据集 pair per line (LNC_GATE_PAIR_LINE)
    from summary.pairs, service-derived (the UI renders, never
    computes). With 20 scripted pairs the bounded RichLog shows the
    FIRST 12 plus LNC_GATE_PAIRS_MORE with the total, never the 13th
    pair; and from that scrollable-list state y STILL launches (the
    log never eats the confirm keys)."""
    from textual.widgets import RichLog

    from tui.screens.selection import ConfirmModal
    from tui.strings import LNC_GATE_PAIR_LINE, LNC_GATE_PAIRS_MORE

    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(summary=GateSummary(
        models=1, tasks=1, seeds=3, cells=3, output_root="./finetuned",
        is_e2x=False, expected_phrase="finetuned",
        pairs=_pairs_fixture(20)))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        assert isinstance(app.screen, ConfirmModal)
        log = app.screen.query_one("#cfg-gate-log", RichLog)
        joined = "\n".join(line.text for line in log.lines)
        assert LNC_GATE_PAIR_LINE.format(
            model="model-00", task="task-00") in joined, (
            "the first planned pair renders under the counts formula")
        assert LNC_GATE_PAIR_LINE.format(
            model="model-11", task="task-11") in joined, (
            "the 12th pair renders (the cap)")
        assert LNC_GATE_PAIR_LINE.format(
            model="model-12", task="task-12") not in joined, (
            "the 13th pair is capped away")
        assert LNC_GATE_PAIRS_MORE.format(pairs=20) in joined, (
            "the truncation line carries the total")
        await pilot.press("y")
        await _settle(pilot, app, rounds=3)
        assert len(launcher.launch_calls) == 1, (
            "y still launches from the scrollable-list state — the "
            "RichLog never eats the confirm keys"
        )


async def test_n_cancels_gate_confirm_without_launch():
    """UX-6: n on the launch-confirmation modal dismisses it (= esc) —
    nothing ever launches. The binding rides the LaunchConfirmModal
    BASE, so the slot-4 gate and the monitor [f] re-run both inherit
    it; enter stays the documented no-op (EHC-2 untouched)."""
    from tui.screens.selection import ConfirmModal

    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(summary=GateSummary(
        models=1, tasks=1, seeds=3, cells=3, output_root="./finetuned",
        is_e2x=False, expected_phrase="finetuned"))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        assert isinstance(app.screen, ConfirmModal)
        await pilot.press("n")
        await _settle_dismiss(pilot)
        assert isinstance(app.screen, RunConfigScreen), (
            "n dismisses the confirm modal"
        )
        assert launcher.launch_calls == [], "n never launches"


async def test_n_cancels_e2_modal_only_after_y_ready_blur():
    """UX-6 E2' twin: while the phrase Input holds focus, n TYPES (the
    character lands in the field); after the matched-enter advance
    (the y-ready blur), n dismisses the modal without launching."""
    from tui.screens.run_config import E2PhraseModal

    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(summary=GateSummary(
        models=62, tasks=50, seeds=3, cells=9300,
        output_root="./finetuned", is_e2x=True,
        expected_phrase="finetuned"))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        assert isinstance(app.screen, E2PhraseModal)
        e2_input = app.screen.query_one("#cfg-e2-input", Input)
        # while the Input holds focus, n is a character, never a key
        await pilot.press("n")
        await pilot.pause()
        assert e2_input.value == "n", (
            "n types into the focused phrase Input"
        )
        assert isinstance(app.screen, E2PhraseModal)
        # reach the y-ready state (exact phrase + the advance blur)
        e2_input.value = ""
        await pilot.pause()
        for char in "finetuned":
            await pilot.press(char)
        await pilot.pause()
        await pilot.press("enter")   # the ADVANCE: blur, never launch
        await _settle(pilot, app, rounds=2)
        assert isinstance(app.screen, E2PhraseModal)
        assert app.focused is not e2_input, "the advance blurred the input"
        await pilot.press("n")
        await _settle_dismiss(pilot)
        assert isinstance(app.screen, RunConfigScreen), (
            "n dismisses the E2' modal from the y-ready state"
        )
        assert launcher.launch_calls == [], "the n cancel never launches"


async def test_gate_hint_line_renders_below_preview():
    """UX-4: the persistent dim hint row renders CFG_GATE_HINT directly
    below the preview line (the hidden enter/Y/N bindings become
    discoverable on-screen)."""
    from tui.strings import CFG_GATE_HINT

    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        hint = screen.query_one("#cfg-gate-hint", Static)
        assert _plain(hint.content) == CFG_GATE_HINT
        assert "cfg-hint" in hint.classes, (
            "the row rides the existing dim height-1 hint styling"
        )
        ordered = [child.id or type(child).__name__
                   for child in screen.children]
        assert (ordered.index("cfg-preview-line")
                < ordered.index("cfg-gate-hint")), (
            "the hint sits immediately after the preview line"
        )


async def test_quit_confirm_uppercase_twins_match_lowercase():
    """261018-08g (SOAK-2/F3): the quit modal's copy advertises [Y]/[N]
    — the UPPERCASE twins must behave exactly like y/n (on HEAD an
    uppercase press left the process alive with the modal up, read as a
    dead console). Y quits; N cancels back to the screen."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("q")
        await pilot.pause()
        from tui.app import QuitConfirmModal

        assert isinstance(app.screen, QuitConfirmModal)
        # uppercase N dismisses exactly like n
        await pilot.press("N")
        await pilot.pause()
        assert isinstance(app.screen, RunConfigScreen), (
            "uppercase N must cancel the quit confirm (the copy says [N])"
        )
        assert not app._exit, "uppercase N must never quit"

        # uppercase Y confirms exactly like y
        await pilot.press("q")
        await pilot.pause()
        assert isinstance(app.screen, QuitConfirmModal)
        await pilot.press("Y")
        await pilot.pause()
        assert app._exit, "uppercase Y must confirm the quit (the copy says [Y])"


async def test_gate_confirm_and_e2_uppercase_twins_match_lowercase():
    """261018-08g (SOAK-2/F3): the launch-confirm family's uppercase
    twins — the gate's Y behaves exactly like y (launches), and the
    E2PhraseModal's Y behaves exactly like y on BOTH states: inert
    while the phrase input is un-armed (a mismatch never launches) and
    confirm-carrying-the-phrase once armed (the armed gate lives inside
    the action — the EHC y-only-confirm ruling preserved, uppercase
    included)."""
    run_service = FakeRunConfigService(spec=RunSpec(
        models=("model-a",), tasks=("task-1",)))
    launcher = FakeLauncherService(summary=GateSummary(
        models=1, tasks=1, seeds=3, cells=3,
        output_root="./finetuned", is_e2x=False,
        expected_phrase="finetuned"))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")   # the gate
        await _settle(pilot, app, rounds=4)
        from tui.screens.selection import ConfirmModal

        assert isinstance(app.screen, ConfirmModal)
        await pilot.press("Y")   # the UPPERCASE twin of y
        await _settle(pilot, app, rounds=4)
        assert len(launcher.launch_calls) == 1, (
            "uppercase Y confirms the launch exactly like y"
        )
        from tui.screens.monitor import MonitorScreen as _MonScreen

        assert isinstance(app.screen, _MonScreen), (
            "the confirmed launch auto-navigates to the monitor (D-13)"
        )

    # the E2' leg: unarmed Y is inert; armed Y confirms with the phrase
    launcher = FakeLauncherService(summary=GateSummary(
        models=62, tasks=50, seeds=3, cells=9300,
        output_root="./finetuned", is_e2x=True,
        expected_phrase="finetuned"))
    app = _app(run_service=run_service, launcher=launcher)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("enter")
        await _settle(pilot, app, rounds=4)
        from textual.widgets import Input as TextInput

        from tui.screens.run_config import E2PhraseModal

        assert isinstance(app.screen, E2PhraseModal)
        # UNARMED (a mismatch phrase): uppercase Y must never launch
        for char in "wrong":
            await pilot.press(char)
        await pilot.pause()
        await pilot.press("Y")
        await _settle(pilot, app, rounds=3)
        assert launcher.launch_calls == [], (
            "unarmed uppercase Y is inert exactly like unarmed y"
        )
        assert isinstance(app.screen, E2PhraseModal)
        # ARMED: the exact phrase + matched enter blur the input, then
        # uppercase Y confirms carrying the phrase
        e2_input = app.screen.query_one("#cfg-e2-input", TextInput)
        e2_input.value = ""
        await pilot.pause()
        for char in "finetuned":
            await pilot.press(char)
        await pilot.pause()
        await pilot.press("enter")   # the advance (blur -> armed)
        await _settle(pilot, app, rounds=3)
        assert app.focused is not e2_input, "the armed state is reached"
        await pilot.press("Y")
        await _settle(pilot, app, rounds=3)
        assert len(launcher.launch_calls) == 1, (
            "armed uppercase Y confirms exactly like armed y"
        )
        _spec, phrase = launcher.launch_calls[0]
        assert phrase == "finetuned", (
            "the uppercase confirm carries the typed phrase"
        )


async def test_picker_title_carries_the_m_switch_hint_in_both_kinds():
    """261018-08g (SOAK-5): the kind-switch key is DISCOVERABLE at the
    picker surface — the title carries the [m] affordance naming the
    kind m switches to, before AND after a switch_kind press (the soak
    tester pressed 't' three times — slot-2 semantics — and never found
    tasks; slot-4's key is m and was invisible in the truncated bar)."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        before = _label_text(screen, "#cfg-picker-title")
        assert "[m]" in before, (
            "the models-kind title carries the [m] keycap"
        )
        assert SEL_SWITCH_LABEL in before, (
            "the hint names the switch target (Datasets)"
        )
        await pilot.press("m")
        await pilot.pause()
        after = _label_text(screen, "#cfg-picker-title")
        assert "[m]" in after, (
            "the datasets-kind title carries the [m] keycap"
        )
        assert NAV_LABEL_SELECTION in after, (
            "the hint names the switch target (Models)"
        )
