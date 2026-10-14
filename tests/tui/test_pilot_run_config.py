"""
Tier-2 Pilot suite for the run-config screen (Phase 11, 11-06; slot 4,
D-01..D-05, D-14, D-19, the LNC-01..03 launch-gate pipeline, and the
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
  the [enter] 启动门 pipeline (problems block, env block with verbatim
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
    SEL_DISABLED_MARK_WARNING,
    SEL_FILTER_COUNT,
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

    def expected_phrase(self, output_root):
        return self.phrase_expected

    def phrase_matches(self, typed, output_root):
        return typed == self.phrase_expected


class FakeLauncherService:
    """The launcher service fake (recorded, scripted outcomes)."""

    def __init__(self, preflight=None, summary=None, outcomes=None,
                 live=(), confirm_raises=None, launch_raises=None):
        self._preflight = (preflight if preflight is not None
                           else EnvPreflight(
                               can_launch=True, reasons=(),
                               failed_kernels=()))
        self._summary = summary
        self._outcomes = list(outcomes) if outcomes else None
        self._live = tuple(live)
        self._confirm_raises = confirm_raises
        self._launch_raises = launch_raises
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
        return "signalled"

    def detach(self, root):
        self.detach_calls.append(root)
        return "detached"

    def live_sweeps(self):
        return self._live

    def tee_path_for(self, root):
        return None


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
            CFG_PICKER_MODELS.format(n=1, total=4))


async def test_m_flips_picker_kind_and_title():
    """m flips models <-> datasets; the title flips with it (D-01)."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        assert _label_text(screen, "#cfg-picker-title") == (
            CFG_PICKER_MODELS.format(n=0, total=4))
        await pilot.press("m")
        await pilot.pause()
        assert _label_text(screen, "#cfg-picker-title") == (
            CFG_PICKER_DATASETS.format(n=0, total=2))
        await pilot.press("m")
        await pilot.pause()
        assert _label_text(screen, "#cfg-picker-title") == (
            CFG_PICKER_MODELS.format(n=0, total=4))


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
            CFG_PICKER_MODELS.format(n=1, total=4))
        await pilot.press("m")
        await pilot.pause()
        await pilot.press("space")
        await _settle(pilot, app)
        assert run_service.saved_specs[-1].tasks == ("task-1",)
        assert _label_text(screen, "#cfg-picker-title") == (
            CFG_PICKER_DATASETS.format(n=1, total=2))

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
        assert svg.count("—（默认") == 3, (
            "ALL THREE storage-dir prompt hints render in the "
            "placeholder's place (the SVG encodes their inner space as "
            "&#160;, so the contiguous constant is pinned by its stable "
            "prefix — three hits = the model-root, dataset-root, and "
            "log-dir rows, 261014-f4w)"
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
# Task 2 — the [p] modal + the launch-gate pipeline + launch toasts
# =====================================================================

async def test_preview_modal_renders_argv_and_problems():
    """[p]: the dimension summary, the same-source note, the LIST argv
    VERBATIM, and the numbered problems when any."""
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
        assert CFG_ARGV_LABEL + " ".join(
            run_service.compose_argv(
                RunSpec(models=("model-a",), tasks=("task-1",)))) in joined
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
        from tui.screens.selection import ConfirmModal

        assert isinstance(app.screen, ConfirmModal), (
            "the non-E2' gate lands on the summary confirm")
        message = str(app.screen._message)
        from tui.strings import LNC_GATE_SUMMARY

        assert LNC_GATE_SUMMARY.format(
            models=1, tasks=1, seeds=3, cells=3,
            output_root="./finetuned") in message
        await pilot.press("enter")
        await _settle(pilot, app, rounds=3)
        assert len(launcher.launch_calls) == 1, "confirm launches once"
        spec, phrase = launcher.launch_calls[0]
        assert spec.models == ("model-a",)
        assert phrase is None, "a non-E2' launch carries no phrase"
        toasts = _toast_messages(app)
        from tui.strings import LNC_LAUNCH_TOAST

        assert any(LNC_LAUNCH_TOAST.format(
            cells=3, output_root="./finetuned") in toast
            for toast in toasts), toasts


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
    """The E2' typed-phrase escalation: a wrong dirname renders the
    mismatch and enter is a no-op; the exact dirname flips the
    indicator and enter fires the launch WITH the phrase."""
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
        await pilot.press("enter")
        await _settle(pilot, app, rounds=3)
        assert len(launcher.launch_calls) == 1
        spec, phrase = launcher.launch_calls[0]
        assert phrase == "finetuned", (
            "the E2' confirm carries the typed phrase")
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
            "enter on the picker must open the launch gate")


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
        await pilot.press("enter")   # confirm -> the launch worker raises
        await _settle(pilot, app, rounds=3)
        assert any(LNC_LAUNCH_FAILED_TOAST.format(error="spawn boom")
                   in toast for toast in _toast_messages(app)), (
            "the confirm-then-crash path surfaces the error"
        )


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
        await pilot.press("enter")
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
            CFG_PICKER_DATASETS.format(n=1, total=2)), (
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

async def test_q_with_no_live_sweep_quits_directly():
    """D-06: no live sweep — q quits directly (no ExitModal)."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        await pilot.press("q")
        await pilot.pause()
        from tui.app import ExitModal

        assert not any(isinstance(screen, ExitModal)
                       for screen in app.screen_stack), (
            "no live sweep: q must never push the ExitModal")
        # App.exit() sets the private _exit flag (the deterministic
        # signal on 8.2.8 — no public is_exiting exists)
        assert app._exit, "q with no live sweep quits directly"


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
        await pilot.press("enter")   # confirm the launch
        await _settle(pilot, app, rounds=4)

        # the D-13 proof: the ACTIVE screen is the monitor, attached
        assert isinstance(app.screen, MonitorScreen), (
            "a successful launch auto-navigates to the monitor screen"
        )
        screen = app.screen
        assert screen._attached_root is not None
        assert screen._attached_root.name == "finetuned"
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
        await pilot.press("enter")   # the matched submit: dismiss + launch
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
