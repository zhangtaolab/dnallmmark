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

import re
from pathlib import Path

from rich.text import Text
from textual.widgets import Input, SelectionList, Static

import tui.screens.run_config as run_config_screen_module
from tui.app import DnallmMarkTui
from tui.screens.nav import BottomBar, TopMenuBar
from tui.screens.run_config import PickerEntries, RunConfigScreen
from tui.screens.selection import PresetMenu, SelectionData
from tui.services import registries as registries_service
from tui.services import run_config as run_config_service
from tui.services import selection as selection_service
from tui.services.download_queue import merge_presence
from tui.services.run_config import PreviewResult, RunSpec
from tui.services.sweep_launcher import (
    EnvPreflight,
    GateSummary,
    LaunchOutcome,
)
from tui.strings import (
    CFG_CACHE_DEFAULT,
    CFG_EMPTY_SELECTION_PROBLEM,
    CFG_FIELD_PEFT,
    CFG_FIELD_VARIANT,
    CFG_PICKER_DATASETS,
    CFG_PICKER_MODELS,
    CFG_PREVIEW_LINE,
    CFG_PREVIEW_PROBLEMS,
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
                 live=()):
        self._preflight = (preflight if preflight is not None
                           else EnvPreflight(
                               can_launch=True, reasons=(),
                               failed_kernels=()))
        self._summary = summary
        self._outcomes = list(outcomes) if outcomes else None
        self._live = tuple(live)
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
        return self._summary or GateSummary(
            models=1, tasks=1, seeds=3, cells=3,
            output_root="./finetuned", is_e2x=False,
            expected_phrase="finetuned")

    def launch_spec(self, spec, phrase=None):
        self.launch_calls.append((spec, phrase))
        if self._outcomes:
            return self._outcomes.pop(0)
        return LaunchOutcome(
            spawned=True, root="/repo/finetuned",
            tee_path="/state/logs/sweep.log", error=None)

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

    def probe_zenodo(self):
        return "not_public"

    def run_task(self, *args, **kwargs):
        raise AssertionError("the run-config tests never run queue tasks")


def _app(run_service=None, launcher=None):
    """The real app over the fake services (constructor injection)."""
    return DnallmMarkTui(
        env_check_service=_EnvCacheHitFake(),
        selection_service=_SelectionFake(),
        download_queue_service=_QueueDriverFake(),
        run_config_service=(run_service if run_service is not None
                            else FakeRunConfigService()),
        launcher_service=(launcher if launcher is not None
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
        screen = app.screen
        picker = screen.query_one("#cfg-picker", SelectionList)
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


async def test_params_defaults_render():
    """Every CFG-01 field renders its default: seeds 42,43,44; the
    choice rows 'none ▾'; absent values '—'; the subset default; the
    dirs defaults; the cache placeholder."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_run_config(pilot, app)
        screen = app.screen
        assert screen.query_one("#cfg-input-seeds", Input).value == "42,43,44"
        assert _label_text(screen, "#cfg-value-peft") == "none ▾"
        assert _label_text(screen, "#cfg-value-variant") == "none ▾"
        assert screen.query_one("#cfg-input-curve", Input).value == ""
        assert CFG_SUBSET_OFF in _label_text(screen, "#cfg-subset-value")
        assert "pipeline/eval_subsets.json" in _label_text(
            screen, "#cfg-subset-value")
        assert screen.query_one("#cfg-input-epochs", Input).value == ""
        assert screen.query_one("#cfg-input-ebs", Input).value == ""
        assert screen.query_one("#cfg-input-output-root", Input).value == (
            "./finetuned")
        assert screen.query_one("#cfg-input-dataset-root", Input).value == (
            "./datasets")
        cache = screen.query_one("#cfg-input-cache", Input)
        assert cache.value == ""
        assert _plain(cache.placeholder) == CFG_CACHE_DEFAULT
        # the field labels render at the design grid
        assert _label_text(screen, "#cfg-label-peft") == CFG_FIELD_PEFT
        assert _label_text(screen, "#cfg-label-variant") == CFG_FIELD_VARIANT


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
# Task 1 — the i18n grep lock (the 11-05 contract note)
# =====================================================================

def test_run_config_module_carries_zero_chinese_literals():
    """I18N-01 single home: no operator-facing copy in the screen."""
    source = _RUN_CONFIG_MODULE_FILE.read_text(encoding="utf-8")
    offenders = re.findall(r"[一-鿿]", source)
    assert not offenders, (
        "Chinese literals must live in tui/strings.py only "
        f"({len(offenders)} found in {_RUN_CONFIG_MODULE_FILE.name})"
    )
