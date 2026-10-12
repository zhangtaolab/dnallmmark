"""
Tier-2 Pilot suite for the custom-onboarding wizard (Phase 9, 09-04;
CUST-01/02 UI + the CUST-03 report view).

Pins the wizard modal family end-to-end against the REAL
``DnallmMarkTui`` with every behavior seam injected (RESEARCH Pattern
7 — the 09-01 validator, the 09-05 gauntlet/import/export callbacks,
and the advisory path probes are deterministic fakes; no service file,
registry, or custom-registry root is ever touched by a faked run):

- the model wizard (Task 1): the four UI-SPEC steps render their exact
  field sets and controls (Inputs, path Inputs with the advisory
  ✓/✗ line, numeric Inputs with the 需为数字 hint, single-pick
  SelectionLists over the injected vocabularies, the three D-02 quirk
  checkboxes unchecked); the border title carries the step indicator;
  enter advances / b returns with every value preserved / esc cancels —
  confirmed via ConfirmModal only when any value is entered (the
  filled-step count named), a blank form cancels silently;
- the dataset wizard + report (Task 2): the four dataset steps, the
  submit → collect-all report (numbered, field-definition order, a
  wrapping RichLog), the preservation contract (esc from the report
  returns to step 4 with values intact), the clean-pass on_valid
  payload shape, Task_type stored under the registry field ``type``,
  and the 28-name injected metric vocabulary;
- prefill + seams + the terminal backstop (Task 3): the D-12 prefill
  round-trip and the unchanged-key collision report, the f/o step-1
  seams, and the 80×24 long-text backstop (a 68-char key and a >100-
  char path stay enterable and the report echoes the full value).

Pilot discipline: ``await pilot.pause()`` before every assertion;
keypad drives are real key events (a focused Input eats printable keys
— typing is typing, never navigation).
"""

import re
import threading
from functools import partial
from pathlib import Path

from textual.widgets import Checkbox, Input, RichLog, SelectionList, Static

from tui.app import DnallmMarkTui
from tui.screens.selection import PresetMenu, SelectionData
from tui.screens.wizard import WizardModal
from tui.services import selection as selection_service
from tui.services.custom_entries import custom_registry_path
from tui.services.custom_validation import METRIC_REGISTRY
from tui.services.gauntlet import LEG_AUDIT, LEG_DRY_RUN, GauntletItem
from tui.strings import (
    ENV_STATE_PENDING,
    GAUNTLET_BANNER_FAIL,
    GAUNTLET_DRILL_HINT,
    GAUNTLET_EXPORT_EMPTY_TOAST,
    GAUNTLET_EXPORTED_TOAST,
    GAUNTLET_IMPORT_CONFLICTS,
    GAUNTLET_IMPORTED_TOAST,
    GAUNTLET_ITEM_AUDIT,
    GAUNTLET_ITEM_DRY_RUN,
    GAUNTLET_ROW_DRY_RUN_PASS,
    GAUNTLET_ROW_FAIL,
    GAUNTLET_ROW_LANDED,
    GAUNTLET_ROW_PASS,
    GAUNTLET_ROW_PENDING,
    GAUNTLET_ROW_RUNNING,
    GAUNTLET_TITLE,
    GAUNTLET_UNDO_AFFORDANCE,
    GAUNTLET_UNDO_TOAST,
    SEL_TEMPLATE_PROBLEM_LINE,
    WIZ_CANCEL_CONFIRM,
    WIZ_FOOTER_HINT,
    WIZ_FOOTER_HINT_LAST,
    WIZ_GAUNTLET_BACK_HINT,
    WIZ_NUMERIC_HINT,
    WIZ_PATH_EXISTS,
    WIZ_PATH_MISSING_ADVISORY,
    WIZ_PROBLEM_COLLISION_CUSTOM,
    WIZ_PROBLEM_COLLISION_OFFICIAL,
    WIZ_PROBLEM_LINE,
    WIZ_PROBLEM_PATH_MISSING,
    WIZ_PROBLEMS_HEADER,
    WIZ_QUIRK_FP32_ONLY,
    WIZ_QUIRK_NO_SAFETENSORS,
    WIZ_QUIRK_SPECIAL_HEAD,
    WIZ_REPORT_BACK_HINT,
    WIZ_REPORT_TITLE,
    WIZD_FIELD_LABELS,
    WIZD_STEPS,
    WIZM_FIELD_LABELS,
    WIZM_STEPS,
)

# The i18n grep gate target (the zero-Chinese-literals module).
_WIZARD_MODULE_FILE = Path(__file__).resolve().parents[2] / "tui" / "screens" / "wizard.py"

_SPECIES_VOCAB = ("human", "plants")
_TOKENIZER_VOCAB = ("BPE", "6-mer", "overlapped 6-mer")
#: The report-line label map the numbered assertions render through.
_DATASET_LABELS = WIZD_FIELD_LABELS
#: A registry key of exactly the UAT-lesson length (68 chars).
_KEY68 = "plant-dnamamba-" + "x" * 53


# =====================================================================
# Deterministic fakes (D-03: no real kernel / registry read)
# =====================================================================

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
        raise AssertionError("the wizard tests never save presets")

    def parse_filter(self, query):
        return selection_service.parse_filter_query(query)

    def apply_filter(self, entries, parsed):
        return selection_service.apply_filter(entries, parsed.terms)

    def import_template(self, path):
        raise AssertionError("the wizard tests never import templates")

    def export_template(self, path, models, tasks):
        raise AssertionError("the wizard tests never export templates")

    def export_tiers(self, path, models, tasks):
        raise AssertionError("the wizard tests never export tiers")


class _Seams:
    """Deterministic capture over every injected wizard behavior seam."""

    def __init__(self, problems=()):
        self.problems = list(problems)
        self.validator_calls = []
        self.valid_calls = []
        self.import_calls = []
        self.export_calls = []

    def validator(self, values):
        self.validator_calls.append(values)
        return list(self.problems)

    def on_valid(self, candidate):
        self.valid_calls.append(candidate)

    def on_import(self):
        self.import_calls.append(1)

    def on_export(self):
        self.export_calls.append(1)


def _app():
    """The real app over the cache-hit env fake + the empty selection."""
    return DnallmMarkTui(
        env_check_service=_EnvCacheHitFake(),
        selection_service=_SelectionFake(),
    )


def _model_wizard(seams, **kwargs):
    """A model wizard with the full seam set + the observed vocabularies."""
    vocabularies = {"species": _SPECIES_VOCAB, "Tokenizer": _TOKENIZER_VOCAB}
    vocabularies.update(kwargs.pop("vocabularies", {}))
    return WizardModal(
        kind="models",
        validator=seams.validator,
        on_valid=seams.on_valid,
        on_import=seams.on_import,
        on_export=seams.on_export,
        vocabularies=vocabularies,
        **kwargs,
    )


def _dataset_wizard(seams, **kwargs):
    """A dataset wizard; the metric vocabulary defaults to one fake name
    (the real 28-name registry has its own dedicated test)."""
    vocabularies = {"metric": ("f1",)}
    vocabularies.update(kwargs.pop("vocabularies", {}))
    return WizardModal(
        kind="datasets",
        validator=seams.validator,
        on_valid=seams.on_valid,
        on_import=seams.on_import,
        on_export=seams.on_export,
        vocabularies=vocabularies,
        **kwargs,
    )


def _plain_title(wizard):
    """The wizard box's border title with the markup tags stripped."""
    box = wizard.query_one("#wizard-box")
    return re.sub(r"\[[^\]]*\]", "", box.border_title or "")


async def _open(pilot, app, wizard):
    """Push the wizard and settle."""
    app.push_screen(wizard)
    await pilot.pause()
    assert app.screen is wizard


async def _type(pilot, wizard, wid, text):
    """Focus one wizard Input and type the text through real key events."""
    inp = wizard.query_one(f"#wiz-{wid}", Input)
    inp.focus()
    await pilot.pause()
    await pilot.press(*list(text))
    await pilot.pause()
    return inp


async def _clear(pilot, inp):
    """Delete the current text through real backspace events."""
    await pilot.press(*(["backspace"] * len(inp.value)))
    await pilot.pause()


# =====================================================================
# Task 1 — the model wizard: steps, controls, esc/b/enter semantics
# =====================================================================

async def test_model_step_one_renders_ui_spec_fields_and_title():
    """Step 1: key/path/size Inputs + the species SelectionList + title."""
    seams = _Seams()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(seams)
        await _open(pilot, app, wizard)
        assert _plain_title(wizard) == (
            f"新增模型 — 步骤 1/4 · {WIZM_STEPS[0]}"
        )
        assert wizard.query_one("#wiz-key", Input).value == ""
        path_input = wizard.query_one("#wiz-model-path", Input)
        assert path_input.value == ""
        wizard.query_one("#wiz-size-m", Input)
        species = wizard.query_one("#wiz-species", SelectionList)
        assert [s.value for s in species.options] == list(_SPECIES_VOCAB)
        # the advisory line under the path field renders blank initially
        assert str(
            wizard.query_one("#wiz-model-path-check", Static).content) == ""
        # the footer hint is the copy-table wording
        assert str(
            wizard.query_one("#wiz-footer-hint", Static).content
        ) == WIZ_FOOTER_HINT


async def test_model_steps_two_three_four_render_ui_spec_controls():
    """Steps 2-4: type/tokenizer SelectionLists, numeric context_len,
    source Inputs, and the three unchecked D-02 quirks."""
    seams = _Seams()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(seams)
        await _open(pilot, app, wizard)
        wizard.query_one("#wiz-key", Input).focus()
        await pilot.pause()
        await pilot.press("enter")  # Input.Submitted advances
        await pilot.pause()
        assert _plain_title(wizard) == (
            f"新增模型 — 步骤 2/4 · {WIZM_STEPS[1]}"
        )
        type_list = wizard.query_one("#wiz-type", SelectionList)
        assert [s.value for s in type_list.options] == ["MLM", "CLM", "DL"]
        wizard.query_one("#wiz-architecture", Input)
        tokenizer = wizard.query_one("#wiz-tokenizer", SelectionList)
        assert [s.value for s in tokenizer.options] == list(_TOKENIZER_VOCAB)
        wizard.query_one("#wiz-context-len", Input)
        # step 3: the three source Inputs
        await pilot.press("enter")
        await pilot.pause()
        assert _plain_title(wizard) == (
            f"新增模型 — 步骤 3/4 · {WIZM_STEPS[2]}"
        )
        wizard.query_one("#wiz-huggingface", Input)
        wizard.query_one("#wiz-modelscope", Input)
        wizard.query_one("#wiz-series", Input)
        # step 4: exactly the three quirks, unchecked
        await pilot.press("enter")
        await pilot.pause()
        assert _plain_title(wizard) == (
            f"新增模型 — 步骤 4/4 · {WIZM_STEPS[3]}"
        )
        quirk_labels = (
            str(cb.label) for cb in wizard.query(Checkbox))
        assert sorted(quirk_labels) == sorted(
            (WIZ_QUIRK_NO_SAFETENSORS, WIZ_QUIRK_FP32_ONLY,
             WIZ_QUIRK_SPECIAL_HEAD))
        for checkbox in wizard.query(Checkbox):
            assert checkbox.value is False, "quirks default unchecked"
        # the last step's footer hint substitutes the submit keycap
        assert str(
            wizard.query_one("#wiz-footer-hint", Static).content
        ) == WIZ_FOOTER_HINT_LAST


async def test_b_returns_with_every_value_preserved():
    """b goes back one step; the typed value survives the re-compose."""
    seams = _Seams()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(seams)
        await _open(pilot, app, wizard)
        key_input = await _type(pilot, wizard, "key", "my-custom-lm")
        await pilot.press("enter")
        await pilot.pause()
        assert "步骤 2/4" in _plain_title(wizard)
        # b must not type into a field: leave the Input first
        wizard.set_focus(None)
        await pilot.pause()
        await pilot.press("b")
        await pilot.pause()
        assert "步骤 1/4" in _plain_title(wizard)
        assert wizard.query_one("#wiz-key", Input).value == "my-custom-lm"
        assert key_input.value == "my-custom-lm"


async def test_esc_blank_form_dismisses_silently():
    """A blank form cancels with no confirm (the empty edge)."""
    seams = _Seams()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(seams)
        await _open(pilot, app, wizard)
        wizard.set_focus(None)
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert app.screen is not wizard, "the blank wizard must dismiss"
        assert "Confirm" not in type(app.screen).__name__, (
            "a blank form never confirms"
        )


async def test_esc_with_values_confirms_naming_filled_steps():
    """Any entered value gates esc through ConfirmModal; Enter abandons,
    Esc continues editing (the destructive-list gate)."""
    seams = _Seams()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(seams)
        await _open(pilot, app, wizard)
        await _type(pilot, wizard, "key", "my-lm")
        wizard.set_focus(None)
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        confirm = app.screen
        assert "Confirm" in type(confirm).__name__, (
            "esc with values must confirm before discarding"
        )
        message = str(confirm.query_one(Static).content)
        assert message == WIZ_CANCEL_CONFIRM.format(n=1)
        # Esc continues: back inside the wizard, values intact
        await pilot.press("escape")
        await pilot.pause()
        assert app.screen is wizard
        assert wizard.query_one("#wiz-key", Input).value == "my-lm"
        # Esc again re-confirms; Enter abandons (the destructive choice)
        wizard.set_focus(None)
        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert app.screen is not wizard, "Enter on the confirm abandons"


async def test_single_pick_selection_keeps_only_the_new_pick():
    """A new pick clears the previous one (UI-SPEC Interaction #6)."""
    seams = _Seams()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(seams)
        await _open(pilot, app, wizard)
        species = wizard.query_one("#wiz-species", SelectionList)
        species.focus()
        await pilot.pause()
        await pilot.press("enter")          # toggle human on
        await pilot.pause()
        assert species.selected == ["human"]
        await pilot.press("down")
        await pilot.press("enter")          # toggle plants on
        await pilot.pause()
        assert species.selected == ["plants"], (
            "a new pick must clear the previous one"
        )


async def test_path_advisory_flips_per_keystroke(tmp_path):
    """The live line under a path field flips ✓/✗ on Input.Changed."""
    seams = _Seams()
    exists_dir = tmp_path / "models" / "my-lm"
    exists_dir.mkdir(parents=True)
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(seams)
        await _open(pilot, app, wizard)
        check = wizard.query_one("#wiz-model-path-check", Static)
        inp = await _type(pilot, wizard, "model-path", str(tmp_path / "nope"))
        assert str(check.content) == WIZ_PATH_MISSING_ADVISORY
        await _clear(pilot, inp)
        await pilot.press(*list(str(exists_dir)))
        await pilot.pause()
        assert str(check.content) == WIZ_PATH_EXISTS
        # the advisory never blocks: advancing away is still possible
        wizard.set_focus(None)
        await pilot.press("enter")
        await pilot.pause()
        assert "步骤 2/4" in _plain_title(wizard)


async def test_numeric_advisory_hint_is_dim_and_advisory():
    """Non-numeric content shows the ✗ 需为数字 hint; numbers clear it."""
    seams = _Seams()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(seams)
        await _open(pilot, app, wizard)
        check = wizard.query_one("#wiz-size-m-check", Static)
        inp = await _type(pilot, wizard, "size-m", "abc")
        assert str(check.content) == WIZ_NUMERIC_HINT
        await _clear(pilot, inp)
        await pilot.press(*list("86.5"))
        await pilot.pause()
        assert str(check.content) == "", "a number clears the hint"


async def test_screen_module_carries_zero_chinese_literals():
    """I18N-01 single-home: no operator-facing copy outside strings.py."""
    source = _WIZARD_MODULE_FILE.read_text(encoding="utf-8")
    offenders = re.findall(r"[一-鿿]", source)
    assert not offenders, (
        "Chinese literals must live in tui/strings.py only "
        f"({len(offenders)} found in {_WIZARD_MODULE_FILE.name})"
    )


# =====================================================================
# Task 2 — the dataset wizard + the submit -> collect-all report
# =====================================================================

async def _advance(pilot, wizard, times=1):
    """Advance through ``times`` steps via the screen-level enter path."""
    for _ in range(times):
        wizard.set_focus(None)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()


async def _submit(pilot, wizard):
    """Reach step 4 and press enter (the submit keycap)."""
    await _advance(pilot, wizard, times=3)
    wizard.set_focus(None)
    await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()


def _report_text(wizard):
    """The report log's full text: strips joined in strip order (the
    wrap never elides — trailing padding alone is dropped)."""
    log = wizard.query_one("#wiz-report-log", RichLog)
    return [strip.text for strip in log.lines]


async def test_dataset_form_renders_the_four_ui_spec_steps():
    """The dataset steps carry the UI-SPEC field sets and controls."""
    seams = _Seams()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _dataset_wizard(seams)
        await _open(pilot, app, wizard)
        # step 1: key + path (with advisory line) + the Category list
        assert _plain_title(wizard) == (
            f"新增数据集 — 步骤 1/4 · {WIZD_STEPS[0]}"
        )
        wizard.query_one("#wiz-key", Input)
        wizard.query_one("#wiz-dataset-path", Input)
        wizard.query_one("#wiz-dataset-path-check", Static)
        category = wizard.query_one("#wiz-category", SelectionList)
        assert [s.value for s in category.options] == [
            "Animals", "Plants", "Microbe", "Multiple"]
        # step 2: the three split-file Inputs + label column + numerics
        await _advance(pilot, wizard)
        assert _plain_title(wizard) == (
            f"新增数据集 — 步骤 2/4 · {WIZD_STEPS[1]}"
        )
        for wid in ("train-file", "dev-file", "test-file"):
            wizard.query_one(f"#wiz-{wid}", Input)
            wizard.query_one(f"#wiz-{wid}-check", Static)
        wizard.query_one("#wiz-label-column", Input)
        wizard.query_one("#wiz-labels", Input)
        wizard.query_one("#wiz-labels-check", Static)
        wizard.query_one("#wiz-length", Input)
        # step 3: Task_type + the injected metric vocabulary
        await _advance(pilot, wizard)
        assert _plain_title(wizard) == (
            f"新增数据集 — 步骤 3/4 · {WIZD_STEPS[2]}"
        )
        task_type = wizard.query_one("#wiz-type", SelectionList)
        assert [s.value for s in task_type.options] == [
            "binary", "multiclass", "regression", "multilabel"]
        metric = wizard.query_one("#wiz-metric", SelectionList)
        assert [s.value for s in metric.options] == ["f1"]
        # step 4: the four provenance Inputs
        await _advance(pilot, wizard)
        assert _plain_title(wizard) == (
            f"新增数据集 — 步骤 4/4 · {WIZD_STEPS[3]}"
        )
        for wid in ("citation", "source", "license", "preprocessing"):
            wizard.query_one(f"#wiz-{wid}", Input)


async def test_split_file_advisory_checks_under_the_dataset_path(tmp_path):
    """The split-file live line probes the file under the dataset dir."""
    seams = _Seams()
    dataset_dir = tmp_path / "datasets" / "my-ds"
    dataset_dir.mkdir(parents=True)
    (dataset_dir / "train.csv").write_text(
        "sequence,label\nACGT,1\n", encoding="utf-8")
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _dataset_wizard(seams)
        await _open(pilot, app, wizard)
        await _type(pilot, wizard, "dataset-path", str(dataset_dir))
        await _advance(pilot, wizard)
        check = wizard.query_one("#wiz-train-file-check", Static)
        inp = await _type(pilot, wizard, "train-file", "nope.csv")
        assert str(check.content) == WIZ_PATH_MISSING_ADVISORY
        await _clear(pilot, inp)
        await pilot.press(*list("train.csv"))
        await pilot.pause()
        assert str(check.content) == WIZ_PATH_EXISTS


async def test_metric_selection_offers_the_28_name_registry():
    """The injected metric vocabulary carries the full 28 names."""
    seams = _Seams()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _dataset_wizard(
            seams, vocabularies={"metric": sorted(METRIC_REGISTRY)})
        await _open(pilot, app, wizard)
        await _advance(pilot, wizard, times=2)
        metric = wizard.query_one("#wiz-metric", SelectionList)
        assert len(metric.options) == 28
        assert "spearmanr" in [s.value for s in metric.options]


async def test_submit_renders_the_numbered_report_in_field_order():
    """A failing submit renders every problem numbered, validator order."""
    problems = [
        ("key", "problem-one"),
        ("Dataset_path", "problem-two"),
        ("labels", "problem-three"),
    ]
    seams = _Seams(problems=problems)
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _dataset_wizard(seams)
        await _open(pilot, app, wizard)
        await _type(pilot, wizard, "key", "my-ds")
        await _submit(pilot, wizard)
        assert _plain_title(wizard) == WIZ_REPORT_TITLE.format(kind="数据集")
        assert str(wizard.query_one(
            "#wiz-report-hint", Static).content) == WIZ_REPORT_BACK_HINT
        joined = "".join(t.rstrip() for t in _report_text(wizard))
        header = WIZ_PROBLEMS_HEADER.format(n=3)
        assert header in joined
        for index, (field_key, message) in enumerate(problems):
            line = WIZ_PROBLEM_LINE.format(
                i=index + 1,
                field_label=_DATASET_LABELS[field_key],
                problem=message)
            assert line in joined, "field-definition order, numbered"
        # nothing applied on failure — no callback ever fired
        assert seams.valid_calls == []
        # the validator saw the composed candidate (values keyed by field)
        assert seams.validator_calls[0]["key"] == "my-ds"


async def test_esc_from_report_returns_to_step_4_with_values_intact():
    """Dismissing the report returns INTO the wizard, values intact."""
    seams = _Seams(problems=[("key", "boom")])
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _dataset_wizard(seams)
        await _open(pilot, app, wizard)
        await _type(pilot, wizard, "key", "my-ds")
        await _submit(pilot, wizard)
        wizard.set_focus(None)
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert _plain_title(wizard) == (
            f"新增数据集 — 步骤 4/4 · {WIZD_STEPS[3]}"
        )
        # b back through the steps to step 1 — the value survived the
        # report round-trip AND the back navigation
        for _ in range(3):
            wizard.set_focus(None)
            await pilot.pause()
            await pilot.press("b")
            await pilot.pause()
        assert _plain_title(wizard) == (
            f"新增数据集 — 步骤 1/4 · {WIZD_STEPS[0]}"
        )
        assert wizard.query_one("#wiz-key", Input).value == "my-ds"
        # re-submit reproduces the report (nothing was lost or applied)
        await _submit(pilot, wizard)
        assert _plain_title(wizard) == WIZ_REPORT_TITLE.format(kind="数据集")


async def test_clean_pass_transitions_to_gauntlet_and_fires_on_valid():
    """A clean pass hands the composed candidate to the gauntlet seam."""
    seams = _Seams()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _dataset_wizard(seams)
        await _open(pilot, app, wizard)
        await _type(pilot, wizard, "key", "my-ds")
        await _type(pilot, wizard, "dataset-path", "datasets/my-ds")
        category = wizard.query_one("#wiz-category", SelectionList)
        category.focus()
        await pilot.pause()
        await pilot.press("down")     # Plants
        await pilot.press("enter")
        await pilot.pause()
        await _advance(pilot, wizard)
        await _type(pilot, wizard, "label-column", "label")
        await _type(pilot, wizard, "labels", "7")
        await _type(pilot, wizard, "length", "512")
        await _advance(pilot, wizard)
        task_type = wizard.query_one("#wiz-type", SelectionList)
        task_type.focus()
        await pilot.pause()
        await pilot.press("enter")     # binary
        await pilot.pause()
        metric = wizard.query_one("#wiz-metric", SelectionList)
        metric.focus()
        await pilot.press("enter")     # f1
        await pilot.pause()
        await _advance(pilot, wizard)  # step 3 -> 4
        await _type(pilot, wizard, "citation", "Marin et al., 2026")
        wizard.set_focus(None)
        await pilot.pause()
        await pilot.press("enter")     # submit on step 4
        await pilot.pause()
        # the gauntlet pending view + the single on_valid call
        assert str(wizard.query_one(
            "#wiz-gauntlet-pending", Static).content) == ENV_STATE_PENDING
        assert str(wizard.query_one(
            "#wiz-gauntlet-hint", Static).content) == WIZ_GAUNTLET_BACK_HINT
        assert _plain_title(wizard) == GAUNTLET_TITLE.format(key="my-ds")
        assert len(seams.valid_calls) == 1
        payload = seams.valid_calls[0]
        assert payload == {
            "key": "my-ds",
            "Dataset_path": "datasets/my-ds",
            "Category": "Plants",
            "label_column": "label",
            "labels": 7,           # numerics compose as numbers
            "length": 512,
            "type": "binary",      # Task_type stored under registry `type`
            "metric": "f1",
            "citation": "Marin et al., 2026",
            "source": "",          # optional strings compose as ""
            "license": "",
            "preprocessing": "",
        }
        assert "Task_type" not in payload
        # the split-file names are advisory-only: Train/Dev/Test derive
        # at composition downstream (the 09-01 decision) — never carried
        assert not any(k in payload for k in ("Train", "Dev", "Test"))
        # esc from the gauntlet returns to the form, values intact
        wizard.set_focus(None)
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert _plain_title(wizard) == (
            f"新增数据集 — 步骤 4/4 · {WIZD_STEPS[3]}"
        )
        assert wizard.query_one("#wiz-citation", Input).value == (
            "Marin et al., 2026")


async def test_model_clean_pass_composes_quirks_and_numerics():
    """The model candidate carries the quirks dict + numeric coercion."""
    seams = _Seams()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(seams)
        await _open(pilot, app, wizard)
        await _type(pilot, wizard, "key", "my-lm")
        await _type(pilot, wizard, "size-m", "88")
        await _advance(pilot, wizard)
        type_list = wizard.query_one("#wiz-type", SelectionList)
        type_list.focus()
        await pilot.pause()
        await pilot.press("down")      # CLM
        await pilot.press("enter")
        await pilot.pause()
        await _advance(pilot, wizard)
        await _advance(pilot, wizard)
        # one quirk checked on step 4
        fp32 = wizard.query_one("#wiz-quirk-fp32-only", Checkbox)
        fp32.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert fp32.value is True
        wizard.set_focus(None)
        await pilot.pause()
        await pilot.press("enter")     # submit
        await pilot.pause()
        assert len(seams.valid_calls) == 1
        payload = seams.valid_calls[0]
        assert payload == {
            "key": "my-lm",
            "Model_path": "",
            "size (M)": 88,
            "species": "",
            "type": "CLM",
            "architecture": "",
            "Tokenizer": "",
            "context_len (bp)": "",
            "huggingface": "",
            "modelscope": "",
            "series": "",
            "quirks": {"no_safetensors": False,
                       "fp32_only": True,
                       "special_head": False},
        }


async def test_report_wraps_the_68_char_key_never_elides():
    """The overflow edge: a 68-char key in a problem wraps in the RichLog
    (the full value rendered across strips, nothing truncated)."""
    seams = _Seams(problems=[
        ("key", WIZ_PROBLEM_COLLISION_OFFICIAL.format(key=_KEY68))])
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(seams)
        await _open(pilot, app, wizard)
        await _submit(pilot, wizard)
        texts = _report_text(wizard)
        assert len(texts) > 2, "the long problem must wrap, not fit one line"
        joined = "".join(t.rstrip() for t in texts)
        assert _KEY68 in joined, "the full key renders across the wrap"


# =====================================================================
# Task 3 — prefill (D-12), the f/o seams, the 80x24 long-text backstop
# =====================================================================

#: A landed custom model entry the prefill source provides (the 09-01
#: land shape: the key field is dropped, the name stamps + quirks ride).
_PREFILL_MODEL = {
    "my-custom-lm": {
        "Model_name": "my-custom-lm",
        "Model_path": "models/my-custom-lm",
        "size (M)": 88,
        "species": "plants",
        "type": "CLM",
        "architecture": "Bert",
        "Tokenizer": "6-mer",
        "context_len (bp)": 1000,
        "huggingface": "org/my-custom-lm",
        "modelscope": "org/my-custom-lm",
        "series": "MySeries",
        "quirks": {"no_safetensors": True, "fp32_only": False,
                   "special_head": False},
        "enabled": False,
    },
}


async def test_prefill_fills_every_model_field_across_all_steps():
    """D-12: a cursor custom entry prefills every field, quirks included."""
    seams = _Seams()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(seams, prefill=_PREFILL_MODEL)
        await _open(pilot, app, wizard)
        # step 1 — the key included (collision validation forces changes)
        assert wizard.query_one("#wiz-key", Input).value == "my-custom-lm"
        assert wizard.query_one(
            "#wiz-model-path", Input).value == "models/my-custom-lm"
        assert str(wizard.query_one(
            "#wiz-model-path-check", Static).content) == (
            WIZ_PATH_MISSING_ADVISORY)  # prefill refreshes advisories too
        assert wizard.query_one("#wiz-size-m", Input).value == "88"
        assert wizard.query_one(
            "#wiz-species", SelectionList).selected == ["plants"]
        # step 2 — enum prefill renders selected, numerics as text
        await _advance(pilot, wizard)
        assert wizard.query_one("#wiz-type", SelectionList).selected == ["CLM"]
        assert wizard.query_one(
            "#wiz-architecture", Input).value == "Bert"
        assert wizard.query_one(
            "#wiz-tokenizer", SelectionList).selected == ["6-mer"]
        assert wizard.query_one("#wiz-context-len", Input).value == "1000"
        # step 3 — the source fields
        await _advance(pilot, wizard)
        assert wizard.query_one(
            "#wiz-huggingface", Input).value == "org/my-custom-lm"
        assert wizard.query_one("#wiz-series", Input).value == "MySeries"
        # step 4 — the quirk checkbox states carried
        await _advance(pilot, wizard)
        assert wizard.query_one(
            "#wiz-quirk-no-safetensors", Checkbox).value is True
        assert wizard.query_one(
            "#wiz-quirk-fp32-only", Checkbox).value is False
        # b back to step 1 — the prefill survived navigation (D-12 re-record)
        for _ in range(3):
            wizard.set_focus(None)
            await pilot.pause()
            await pilot.press("b")
            await pilot.pause()
        assert wizard.query_one("#wiz-key", Input).value == "my-custom-lm"


async def test_prefill_dataset_maps_entry_fields_not_split_names():
    """The dataset prefill maps entry fields; the split-file inputs (no
    entry counterpart — landed rows carry counts, not names) stay blank."""
    seams = _Seams()
    prefill = {"my-ds": {
        "Dataset_name": "my-ds",
        "Dataset_path": "datasets/my-ds",
        "Category": "Plants",
        "label_column": "label",
        "labels": 7,
        "length": 512,
        "type": "multiclass",
        "metric": "f1",
        "citation": "Marin et al., 2026",
        "Train": 3, "Dev": 2, "Test": 1,
    }}
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _dataset_wizard(seams, prefill=prefill)
        await _open(pilot, app, wizard)
        assert wizard.query_one("#wiz-key", Input).value == "my-ds"
        assert wizard.query_one(
            "#wiz-dataset-path", Input).value == "datasets/my-ds"
        assert wizard.query_one(
            "#wiz-category", SelectionList).selected == ["Plants"]
        await _advance(pilot, wizard)
        for wid in ("train-file", "dev-file", "test-file"):
            assert wizard.query_one(f"#wiz-{wid}", Input).value == ""
        assert wizard.query_one("#wiz-label-column", Input).value == "label"
        assert wizard.query_one("#wiz-labels", Input).value == "7"
        await _advance(pilot, wizard)
        assert wizard.query_one(
            "#wiz-type", SelectionList).selected == ["multiclass"]
        assert wizard.query_one(
            "#wiz-metric", SelectionList).selected == ["f1"]


async def test_prefill_unchanged_key_yields_the_collision_report():
    """D-12 self-enforcement: submitting the unchanged key surfaces the
    collision problem — the delete-and-rerecord discipline needs no edit
    surface."""
    seams = _Seams(problems=[
        ("key", WIZ_PROBLEM_COLLISION_OFFICIAL.format(key="my-custom-lm"))])
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(seams, prefill=_PREFILL_MODEL)
        await _open(pilot, app, wizard)
        await _submit(pilot, wizard)
        joined = "".join(t.rstrip() for t in _report_text(wizard))
        assert WIZ_PROBLEM_LINE.format(
            i=1,
            field_label=WIZM_FIELD_LABELS["key"],
            problem=WIZ_PROBLEM_COLLISION_OFFICIAL.format(
                key="my-custom-lm"),
        ) in joined
        assert seams.valid_calls == []


async def test_f_and_o_bindings_fire_only_on_step_one():
    """The step-1 affordances route to the seams; later steps no-op."""
    seams = _Seams()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(seams)
        await _open(pilot, app, wizard)
        wizard.set_focus(None)
        await pilot.pause()
        await pilot.press("f")
        await pilot.pause()
        assert seams.import_calls == [1]
        await pilot.press("o")
        await pilot.pause()
        assert seams.export_calls == [1]
        # step 2+: the bindings exist but no-op outside step 1
        await _advance(pilot, wizard)
        wizard.set_focus(None)
        await pilot.pause()
        await pilot.press("f")
        await pilot.press("o")
        await pilot.pause()
        assert seams.import_calls == [1]
        assert seams.export_calls == [1]


async def test_backstop_80x24_long_text_stays_enterable_and_readable():
    """The UI-Considerations long-text backstop (the structured lift):
    at 80x24 a 68-char key and a >100-char path stay enterable (the
    Input buffer holds them) and the report echoes the FULL values on
    wrapped lines with no column collision."""
    path_long = "/data/dnallm/models/" + "d" * 88 + "/my-lm"
    assert len(path_long) > 100
    seams = _Seams(problems=[
        ("key", WIZ_PROBLEM_COLLISION_OFFICIAL.format(key=_KEY68)),
        ("Model_path", WIZ_PROBLEM_PATH_MISSING.format(path=path_long)),
    ])
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.resize_terminal(80, 24)
        wizard = _model_wizard(seams)
        await _open(pilot, app, wizard)
        # the modal honors the amended width rule at the minimum grid
        box = wizard.query_one("#wizard-box")
        assert box.region.width == 76, (
            "min(100, width-4) at 80 columns — the amendment's exact cap"
        )
        key_input = await _type(pilot, wizard, "key", _KEY68)
        assert key_input.value == _KEY68, "the Input buffer holds all 68"
        path_input = await _type(pilot, wizard, "model-path", path_long)
        assert path_input.value == path_long
        await _submit(pilot, wizard)
        texts = _report_text(wizard)
        assert len(texts) > 3, "both long problems wrap, never fit"
        joined = "".join(t.rstrip() for t in texts)
        assert _KEY68 in joined, "the full key echoes across the wrap"
        assert path_long in joined, "the full path echoes across the wrap"
        assert "…" not in joined and "..." not in joined, (
            "nothing elides in the report"
        )


# =====================================================================
# Task 4 (09-05 Task 1) — the gauntlet panel: async rows, run-id drop,
# land-only-on-all-pass, the failure banner
# =====================================================================

_LAND_PATH = "/tmp/pinned/custom_models.json"


class _FakeGauntlet:
    """Deterministic gauntlet service (the 09-02 service's two per-leg
    entry points, gated per (leg, run_id) — the 08-06 gated-fake idiom).

    Outcome tables are a plain bool (every call) or a dict keyed by
    candidate key / ``(run_id, key)`` (dict default True) — the (run_id,
    key) form is the WR-02 fixture's per-run discrimination.
    """

    def __init__(self, dry_ok=True, audit_ok=True, gates=None):
        self.dry_ok = dry_ok
        self.audit_ok = audit_ok
        self.gates = gates or {}
        self.dry_calls = []
        self.audit_calls = []

    @staticmethod
    def _outcome(table, run_id, key):
        if isinstance(table, dict):
            if (run_id, key) in table:
                return table[(run_id, key)]
            return table.get(key, True)
        return bool(table)

    def dry_run_precheck(self, kind, key, entry, run_id):
        self.dry_calls.append((kind, key, run_id))
        gate = self.gates.get((LEG_DRY_RUN, run_id))
        if gate is not None:
            gate.wait(timeout=10)  # deterministic gate, never a sleep
        ok = self._outcome(self.dry_ok, run_id, key)
        if ok:
            return GauntletItem(
                run_id=run_id, kind=kind, leg=LEG_DRY_RUN, name=key,
                ok=True, details=("planned_cells=6",),
                raw_output="planned 6 cell(s) for " + key)
        return GauntletItem(
            run_id=run_id, kind=kind, leg=LEG_DRY_RUN, name=key,
            ok=False, details=("exit_nonzero", "exit_code=1"),
            raw_output="sweep: ERROR bad entry " + key)

    def audit_reconciliation(self, key, entry, declared_splits, run_id):
        self.audit_calls.append((key, run_id))
        ok = self._outcome(self.audit_ok, run_id, key)
        if ok:
            return GauntletItem(
                run_id=run_id, kind="datasets", leg=LEG_AUDIT, name=key,
                ok=True, details=("train_rows=8", "unified_eval_n=6"),
                raw_output="audit ok " + key)
        return GauntletItem(
            run_id=run_id, kind="datasets", leg=LEG_AUDIT, name=key,
            ok=False, details=("train_rows=0",),
            raw_output="audit: empty train split " + key)


class _StoreFake:
    """Capture over the land/undo seams — the panel's ONLY write path."""

    def __init__(self, land_path=_LAND_PATH):
        self.land_calls = []
        self.undo_calls = []
        self._land_path = land_path

    def land(self, kind, key, entry):
        self.land_calls.append((kind, key, entry))
        return self._land_path

    def undo(self, kind, key):
        self.undo_calls.append((kind, key))
        return True


def _gauntlet_row_text(wizard, group, item):
    """One gauntlet row's current text (re-queried: recompose replaces)."""
    row = wizard.query_one(f"#gauntlet-row-{group}-{item}", Static)
    return str(row.content)


def _gauntlet_banner(wizard):
    return str(wizard.query_one("#gauntlet-banner", Static).content)


async def _wait_row_becomes(pilot, wizard, group, item, expected):
    """Pause-loop until one row's content equals ``expected`` (pauses
    returning while a worker blocks IS the responsiveness proof)."""
    for _ in range(100):
        await pilot.pause()
        if _gauntlet_row_text(wizard, group, item) == expected:
            break
    assert _gauntlet_row_text(wizard, group, item) == expected


async def _wait_banner_becomes(pilot, wizard, expected):
    for _ in range(100):
        await pilot.pause()
        if _gauntlet_banner(wizard) == expected:
            break
    assert _gauntlet_banner(wizard) == expected


async def _settled(pilot, app):
    """Every worker finished + its messages handed to the event loop."""
    await app.workers.wait_for_complete()
    await pilot.pause()
    await pilot.pause()


def _toasts(app):
    """The app's toast messages in fire order (the selection-suite idiom)."""
    return [notification.message for notification in app._notifications]


async def test_gauntlet_panel_progression_pending_running_done():
    """Truth 1: kind-aware rows progress ◌ 待检 → ⠋ …运行中 → ✓ with the
    structured summaries; the console stays responsive (thread worker)."""
    gate = threading.Event()
    service = _FakeGauntlet(gates={(LEG_DRY_RUN, 1): gate})
    seams = _Seams()
    store = _StoreFake()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(
            seams, gauntlet_service=service,
            land=store.land, undo=store.undo)
        await _open(pilot, app, wizard)
        await _type(pilot, wizard, "key", "my-lm")
        await _submit(pilot, wizard)
        # the model panel: exactly one row (dry-run leg only) with the
        # panel title + drill hint; pending or already running (the
        # worker races the first pause — both are the launch state)
        assert _plain_title(wizard) == GAUNTLET_TITLE.format(key="my-lm")
        hint = str(wizard.query_one("#gauntlet-hint", Static).content)
        assert GAUNTLET_DRILL_HINT in hint and WIZ_GAUNTLET_BACK_HINT in hint
        pending = GAUNTLET_ROW_PENDING.format(item=GAUNTLET_ITEM_DRY_RUN)
        running = GAUNTLET_ROW_RUNNING.format(item=GAUNTLET_ITEM_DRY_RUN)
        assert _gauntlet_row_text(wizard, 0, 0) in (pending, running)
        await _wait_row_becomes(pilot, wizard, 0, 0, running)
        gate.set()
        await _settled(pilot, app)
        assert _gauntlet_row_text(wizard, 0, 0) == (
            GAUNTLET_ROW_DRY_RUN_PASS.format(cells="6"))
        # enter on the focused row drills into the verbatim output; esc
        # returns to the panel with every row intact
        await pilot.press("enter")
        await pilot.pause()
        drill = wizard.query_one("#gauntlet-drill-log", RichLog)
        joined = "".join(strip.text for strip in drill.lines)
        assert "planned 6 cell(s) for my-lm" in joined
        await pilot.press("escape")
        await pilot.pause()
        assert _gauntlet_row_text(wizard, 0, 0) == (
            GAUNTLET_ROW_DRY_RUN_PASS.format(cells="6"))


async def test_gauntlet_dataset_panel_runs_both_legs_in_order():
    """The dataset panel renders BOTH item rows; the not-yet-started audit
    row stays 待检 while the dry-run leg is in flight (the observable
    per-item progression), then both complete with their summaries."""
    gate = threading.Event()
    service = _FakeGauntlet(gates={(LEG_DRY_RUN, 1): gate})
    seams = _Seams()
    store = _StoreFake()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _dataset_wizard(
            seams, gauntlet_service=service,
            land=store.land, undo=store.undo)
        await _open(pilot, app, wizard)
        await _type(pilot, wizard, "key", "my-ds")
        await _submit(pilot, wizard)
        running = GAUNTLET_ROW_RUNNING.format(item=GAUNTLET_ITEM_DRY_RUN)
        await _wait_row_becomes(pilot, wizard, 0, 0, running)
        # the audit leg has not started: its row is still pending
        assert _gauntlet_row_text(wizard, 0, 1) == (
            GAUNTLET_ROW_PENDING.format(item=GAUNTLET_ITEM_AUDIT))
        gate.set()
        await _settled(pilot, app)
        assert _gauntlet_row_text(wizard, 0, 0) == (
            GAUNTLET_ROW_DRY_RUN_PASS.format(cells="6"))
        assert _gauntlet_row_text(wizard, 0, 1) == GAUNTLET_ROW_PASS.format(
            item=GAUNTLET_ITEM_AUDIT,
            summary="train_rows=8, unified_eval_n=6")
        # both legs ran, dry-run first
        assert service.dry_calls == [("datasets", "my-ds", 1)]
        assert service.audit_calls == [("my-ds", 1)]


async def test_gauntlet_all_pass_lands_once_renders_undo_and_clears_form():
    """Truth 3: all-✓ lands exactly once through the store seam, renders
    the landed row + toast + [u] affordance, and clears the form (a land
    is one of the three clearing events)."""
    service = _FakeGauntlet()
    seams = _Seams()
    store = _StoreFake()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(
            seams, gauntlet_service=service,
            land=store.land, undo=store.undo)
        await _open(pilot, app, wizard)
        await _type(pilot, wizard, "key", "my-lm")
        await _type(pilot, wizard, "model-path", "models/my-lm")
        await _submit(pilot, wizard)
        await _settled(pilot, app)
        # land fired EXACTLY once with the composed candidate
        assert len(store.land_calls) == 1
        kind, key, entry = store.land_calls[0]
        assert (kind, key) == ("models", "my-lm")
        assert entry["key"] == "my-lm"
        assert entry["Model_path"] == "models/my-lm"
        # the landed row + success toast + the active undo affordance
        landed = GAUNTLET_ROW_LANDED.format(key="my-lm", path=_LAND_PATH)
        assert _gauntlet_banner(wizard) == landed
        assert _toasts(app)[-1] == landed
        assert str(wizard.query_one(
            "#gauntlet-undo", Static).content) == GAUNTLET_UNDO_AFFORDANCE
        # u: session undo — removes exactly the just-landed key, once
        wizard.set_focus(None)
        await pilot.pause()
        await pilot.press("u")
        await pilot.pause()
        assert store.undo_calls == [("models", "my-lm")]
        assert _toasts(app)[-1] == GAUNTLET_UNDO_TOAST.format(key="my-lm")
        assert str(wizard.query_one("#gauntlet-undo", Static).content) == ""
        await pilot.press("u")  # the affordance is single-use
        await pilot.pause()
        assert store.undo_calls == [("models", "my-lm")]
        # esc returns to the form CLEARED (land cleared it)
        await pilot.press("escape")
        await pilot.pause()
        assert _plain_title(wizard) == (
            f"新增模型 — 步骤 1/4 · {WIZM_STEPS[0]}"
        )
        assert wizard.query_one("#wiz-key", Input).value == ""


async def test_gauntlet_any_fail_banner_verbatim_never_lands_values_intact(
        tmp_path, monkeypatch):
    """Truth 2 / CUST-04 core: any ✗ renders the prominent banner
    verbatim (官方注册表零触碰), never lands (the tmp custom root never
    gains the file), drills down verbatim, and esc returns with every
    value intact."""
    from tui.services import custom_entries
    from tui.services.settings import CONFIG_DIR_ENV

    monkeypatch.setenv(CONFIG_DIR_ENV, str(tmp_path))
    service = _FakeGauntlet(dry_ok=False)
    seams = _Seams()
    land_calls = []

    def land_spy(kind, key, entry):
        land_calls.append((kind, key))
        return custom_entries.land(kind, key, entry)

    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(
            seams, gauntlet_service=service, land=land_spy,
            undo=custom_entries.undo)
        await _open(pilot, app, wizard)
        await _type(pilot, wizard, "key", "my-lm")
        await _type(pilot, wizard, "model-path", "models/my-lm")
        await _submit(pilot, wizard)
        await _settled(pilot, app)
        # the failed row renders the verbatim detail tokens
        assert _gauntlet_row_text(wizard, 0, 0) == GAUNTLET_ROW_FAIL.format(
            item=GAUNTLET_ITEM_DRY_RUN,
            summary="exit_nonzero, exit_code=1")
        # the banner is the Copywriting row VERBATIM (hardcoded pin)
        banner = _gauntlet_banner(wizard)
        assert banner == GAUNTLET_BANNER_FAIL.format(key="my-lm")
        assert banner == "✗ gauntlet 未通过 — my-lm 未落盘（官方注册表零触碰）"
        # no undo affordance, no success toast
        assert str(wizard.query_one("#gauntlet-undo", Static).content) == ""
        assert _toasts(app) == []
        # NEVER landed: zero seam calls and the custom file never created
        assert land_calls == []
        assert not custom_registry_path("models").exists()
        # drill-down carries the subprocess's own output lines verbatim
        await pilot.press("enter")
        await pilot.pause()
        drill = wizard.query_one("#gauntlet-drill-log", RichLog)
        joined = "".join(strip.text for strip in drill.lines)
        assert "sweep: ERROR bad entry my-lm" in joined
        await pilot.press("escape")
        await pilot.pause()
        # esc returns to the form at step 4 with EVERY value intact (the
        # model step 4 is the quirk trio — b back to step 1 reads the key)
        await pilot.press("escape")
        await pilot.pause()
        assert _plain_title(wizard) == (
            f"新增模型 — 步骤 4/4 · {WIZM_STEPS[3]}"
        )
        for _ in range(3):
            wizard.set_focus(None)
            await pilot.pause()
            await pilot.press("b")
            await pilot.pause()
        assert _plain_title(wizard) == (
            f"新增模型 — 步骤 1/4 · {WIZM_STEPS[0]}"
        )
        assert wizard.query_one("#wiz-key", Input).value == "my-lm"
        assert wizard.query_one(
            "#wiz-model-path", Input).value == "models/my-lm"


async def test_gauntlet_stale_result_from_cancelled_run_never_overwrites():
    """Truth 4 / WR-02: run 1 blocks mid-leg carrying a FAIL; abandoning
    the panel (esc) and resubmitting runs the fresh PASS to completion;
    run 1's late result posts AFTER — the handlers drop it (the landed
    state is never overwritten, run 1 never lands)."""
    gate = threading.Event()
    service = _FakeGauntlet(
        dry_ok={(1, "my-lm"): False},          # run 1 carries a stale FAIL
        gates={(LEG_DRY_RUN, 1): gate},
    )
    seams = _Seams()
    store = _StoreFake()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(
            seams, gauntlet_service=service,
            land=store.land, undo=store.undo)
        await _open(pilot, app, wizard)
        await _type(pilot, wizard, "key", "my-lm")
        await _submit(pilot, wizard)
        running = GAUNTLET_ROW_RUNNING.format(item=GAUNTLET_ITEM_DRY_RUN)
        await _wait_row_becomes(pilot, wizard, 0, 0, running)

        # abandon the in-flight run: esc returns to the form (values
        # intact), the resubmit launches the fresh run
        await pilot.press("escape")
        await pilot.pause()
        assert _plain_title(wizard) == (
            f"新增模型 — 步骤 4/4 · {WIZM_STEPS[3]}"
        )
        await _submit(pilot, wizard)
        # the fresh run completes and lands while run 1 still blocks
        landed = GAUNTLET_ROW_LANDED.format(key="my-lm", path=_LAND_PATH)
        await _wait_banner_becomes(pilot, wizard, landed)
        assert len(store.land_calls) == 1

        # release run 1's blocked leg — its late item posts after the
        # fresh run completed; the drop keeps the fresh verdicts intact
        gate.set()
        await _settled(pilot, app)
        assert _gauntlet_row_text(wizard, 0, 0) == (
            GAUNTLET_ROW_DRY_RUN_PASS.format(cells="6")), (
            "a stale result from the abandoned run must never overwrite"
        )
        assert _gauntlet_banner(wizard) == landed
        assert len(store.land_calls) == 1, "run 1 never lands"


# =====================================================================
# Task 5 (09-05 Task 2) — session undo over the real store, the D-11
# import view (per-entry sequential gauntlet), the export view
# =====================================================================

class _ImportSeams:
    """Capture over the import read/validate seams (D-11)."""

    def __init__(self, doc=None, read_error=None, problems=()):
        self.doc = doc
        self.read_error = read_error
        self.problems = list(problems)
        self.read_calls = []
        self.validate_calls = []

    def read(self, path):
        self.read_calls.append(path)
        if self.read_error is not None:
            return None, self.read_error
        return self.doc, None

    def validate(self, doc):
        self.validate_calls.append(doc)
        return list(self.problems)


async def _press_step_one_key(pilot, app, key):
    """Press a step-1 affordance with nothing focused (plain binding)."""
    app.screen.set_focus(None)
    await pilot.pause()
    await pilot.press(key)
    await pilot.pause()


async def _submit_path(pilot, app, path):
    """Type the path into the open path prompt and press enter."""
    inp = app.screen.query_one("#wizard-path-input", Input)
    inp.focus()
    await pilot.pause()
    await pilot.press(*list(str(path)))
    await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()


def _prompt_log_text(app):
    """The open path prompt's problem report lines, joined."""
    log = app.screen.query_one("#wizard-path-problems", RichLog)
    return [strip.text for strip in log.lines]


#: A two-entry import document in FILE ORDER (ds-a declared before ds-b).
_IMPORT_DOC = {
    "ds-a": {"Dataset_path": "datasets/ds-a", "Category": "Plants",
             "type": "binary", "metric": "f1"},
    "ds-b": {"Dataset_path": "datasets/ds-b", "Category": "Microbe",
             "type": "multiclass", "metric": "mcc"},
}


async def test_import_conflicts_render_numbered_report_nothing_merges():
    """D-11 fail-closed: any conflict renders the numbered conflicts
    report (keys full-length) and NOTHING merges — the modal stays open."""
    key68 = "d" * 68
    problems = [
        (key68, WIZ_PROBLEM_COLLISION_OFFICIAL.format(key=key68)),
        ("ds-x", WIZ_PROBLEM_COLLISION_CUSTOM.format(key="ds-x")),
    ]
    imports = _ImportSeams(doc={"ds-x": {}}, problems=problems)
    service = _FakeGauntlet()
    store = _StoreFake()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _dataset_wizard(
            _Seams(), gauntlet_service=service,
            land=store.land, undo=store.undo,
            import_read=imports.read, import_validate=imports.validate)
        await _open(pilot, app, wizard)
        await _press_step_one_key(pilot, app, "f")
        assert app.screen is not wizard, "the import path prompt opens"
        await _submit_path(pilot, app, "/share/custom_datasets.json")
        # the numbered conflicts report: header + both lines, key full
        lines = _prompt_log_text(app)
        joined = "".join(line.rstrip() for line in lines)
        assert lines[0].strip() == GAUNTLET_IMPORT_CONFLICTS.format(n=2)
        assert SEL_TEMPLATE_PROBLEM_LINE.format(
            n=1, location=key68,
            message=WIZ_PROBLEM_COLLISION_OFFICIAL.format(key=key68),
        ).rstrip() in joined or key68 in joined, (
            "the 68-char key renders full-length (wrap, not truncate)"
        )
        assert "ds-x" in joined
        # the modal stays open — nothing merged, nothing landed
        assert app.screen is not wizard
        assert service.dry_calls == []
        assert store.land_calls == []
        assert imports.validate_calls and imports.validate_calls[0] == {
            "ds-x": {}}
        # esc closes the prompt back to the wizard at step 1
        await pilot.press("escape")
        await pilot.pause()
        assert app.screen is wizard
        assert _plain_title(wizard) == (
            f"新增数据集 — 步骤 1/4 · {WIZD_STEPS[0]}"
        )


async def test_import_unreadable_file_yields_tolerant_problem_lines():
    """The untrusted-input edge: an unreadable/malformed file renders
    tolerant-loader problem lines through the same report surface —
    nothing merges, no crash."""
    read_error = "import file unreadable or not valid JSON: /nope/x.json"
    imports = _ImportSeams(read_error=read_error)
    service = _FakeGauntlet()
    store = _StoreFake()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _dataset_wizard(
            _Seams(), gauntlet_service=service,
            land=store.land, undo=store.undo,
            import_read=imports.read, import_validate=imports.validate)
        await _open(pilot, app, wizard)
        await _press_step_one_key(pilot, app, "f")
        await _submit_path(pilot, app, "/nope/x.json")
        lines = _prompt_log_text(app)
        joined = "".join(line.rstrip() for line in lines)
        assert lines[0].strip() == GAUNTLET_IMPORT_CONFLICTS.format(n=1)
        assert read_error in joined, "the tolerant-loader line verbatim"
        # nothing merges, the modal stays open, no crash
        assert app.screen is not wizard
        assert service.dry_calls == []
        assert store.land_calls == []
        assert imports.validate_calls == []


async def test_import_two_entries_sequential_entry_level_rollback():
    """D-08 entry-level rollback: entries gauntlet sequentially in FILE
    ORDER — ds-a lands and STAYS, ds-b fails and never lands, the banner
    names ds-b only; the toast carries {n} for the landed count."""
    service = _FakeGauntlet(dry_ok={"ds-b": False})
    store = _StoreFake()
    imports = _ImportSeams(doc=_IMPORT_DOC)
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _dataset_wizard(
            _Seams(), gauntlet_service=service,
            land=store.land, undo=store.undo,
            import_read=imports.read, import_validate=imports.validate)
        await _open(pilot, app, wizard)
        await _press_step_one_key(pilot, app, "f")
        await _submit_path(pilot, app, "/share/custom_datasets.json")
        assert app.screen is wizard, "the clean file enters the panel"
        # grouped per entry: header rows carry each entry's gauntlet title
        head_a = wizard.query_one("#gauntlet-head-0", Static)
        head_b = wizard.query_one("#gauntlet-head-1", Static)
        assert str(head_a.content) == GAUNTLET_TITLE.format(key="ds-a")
        assert str(head_b.content) == GAUNTLET_TITLE.format(key="ds-b")
        await _settled(pilot, app)
        # sequential, in the file's declaration order
        assert [call[1] for call in service.dry_calls] == ["ds-a", "ds-b"]
        assert [call[0] for call in service.audit_calls] == ["ds-a", "ds-b"]
        # entry-level rollback: exactly ds-a landed, ds-b never landed
        assert [call[1] for call in store.land_calls] == ["ds-a"]
        assert str(wizard.query_one(
            "#gauntlet-status-0", Static).content) == (
            GAUNTLET_ROW_LANDED.format(key="ds-a", path=_LAND_PATH))
        assert str(wizard.query_one(
            "#gauntlet-status-1", Static).content) == (
            GAUNTLET_BANNER_FAIL.format(key="ds-b"))
        # the import-completion toast carries the landed count
        assert _toasts(app) == [GAUNTLET_IMPORTED_TOAST.format(
            n=1, kind="数据集")]
        # esc returns to the form — the import never touched its values
        await pilot.press("escape")
        await pilot.pause()
        assert _plain_title(wizard) == (
            f"新增数据集 — 步骤 1/4 · {WIZD_STEPS[0]}"
        )


async def test_import_all_pass_lands_every_entry_in_file_order():
    """The many edge: a fully passing two-entry file lands BOTH entries
    in file order and the toast carries {n} == 2."""
    service = _FakeGauntlet()
    store = _StoreFake()
    imports = _ImportSeams(doc=_IMPORT_DOC)
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _dataset_wizard(
            _Seams(), gauntlet_service=service,
            land=store.land, undo=store.undo,
            import_read=imports.read, import_validate=imports.validate)
        await _open(pilot, app, wizard)
        await _press_step_one_key(pilot, app, "f")
        await _submit_path(pilot, app, "/share/custom_datasets.json")
        await _settled(pilot, app)
        assert [call[1] for call in store.land_calls] == ["ds-a", "ds-b"]
        for index, key in enumerate(("ds-a", "ds-b")):
            assert str(wizard.query_one(
                f"#gauntlet-status-{index}", Static).content) == (
                GAUNTLET_ROW_LANDED.format(key=key, path=_LAND_PATH))
        assert _toasts(app) == [GAUNTLET_IMPORTED_TOAST.format(
            n=2, kind="数据集")]


async def test_undo_via_real_store_removes_exactly_the_landed_key(
        tmp_path, monkeypatch):
    """Session undo through the REAL 09-01 store on a tmp config root:
    after u the landed key is gone from the user-owned registry file."""
    from tui.services import custom_entries
    from tui.services.settings import CONFIG_DIR_ENV

    monkeypatch.setenv(CONFIG_DIR_ENV, str(tmp_path))
    service = _FakeGauntlet()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(
            _Seams(), gauntlet_service=service,
            land=custom_entries.land, undo=custom_entries.undo)
        await _open(pilot, app, wizard)
        await _type(pilot, wizard, "key", "my-lm")
        await _submit(pilot, wizard)
        await _settled(pilot, app)
        entries, error = custom_entries.read_entries("models")
        assert error is None and list(entries) == ["my-lm"]
        wizard.set_focus(None)
        await pilot.pause()
        await pilot.press("u")
        await pilot.pause()
        assert _toasts(app)[-1] == GAUNTLET_UNDO_TOAST.format(key="my-lm")
        entries, error = custom_entries.read_entries("models")
        assert error is None and entries == {}, (
            "undo removes exactly the just-landed key from the file"
        )


async def test_export_with_zero_customs_toasts_writes_nothing(
        tmp_path, monkeypatch):
    """The empty edge: zero landed customs short-circuits to the toast
    BEFORE any path is asked; nothing at the destination is created."""
    from tui.services.settings import CONFIG_DIR_ENV

    monkeypatch.setenv(CONFIG_DIR_ENV, str(tmp_path))
    export_calls = []

    def export_never(dest_path):
        export_calls.append(dest_path)
        return True, None

    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _dataset_wizard(
            _Seams(), export_registry=export_never,
            has_custom_entries=lambda: False)
        await _open(pilot, app, wizard)
        await _press_step_one_key(pilot, app, "o")
        assert app.screen is wizard, "no path prompt in the empty state"
        assert _toasts(app) == [GAUNTLET_EXPORT_EMPTY_TOAST]
        assert export_calls == []
        assert list(tmp_path.iterdir()) == [], "nothing created anywhere"


async def test_export_copies_the_landed_registry_verbatim_bytes(
        tmp_path, monkeypatch):
    """The real-file integration variant: the exported file's bytes
    equal the landed registry file's bytes (the file IS the share unit)."""
    from tui.services import custom_entries
    from tui.services.settings import CONFIG_DIR_ENV

    monkeypatch.setenv(CONFIG_DIR_ENV, str(tmp_path))
    custom_entries.land("datasets", "ds-a", {
        "Dataset_path": "datasets/ds-a", "Category": "Plants"})
    dest = tmp_path / "share" / "custom_datasets.json"
    dest.parent.mkdir(parents=True)  # copyfile needs an existing parent
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _dataset_wizard(
            _Seams(),
            export_registry=partial(custom_entries.export_registry,
                                    "datasets"),
            has_custom_entries=partial(_has_entries, "datasets"))
        await _open(pilot, app, wizard)
        await _press_step_one_key(pilot, app, "o")
        assert app.screen is not wizard, "the export path prompt opens"
        await _submit_path(pilot, app, dest)
        assert app.screen is wizard
        assert _toasts(app) == [GAUNTLET_EXPORTED_TOAST.format(path=dest)]
        assert dest.is_file()
        assert dest.read_bytes() == custom_registry_path(
            "datasets").read_bytes(), "byte-verbatim copy"


def _has_entries(kind):
    """The real empty-state probe (the 09-06 wiring reads the store)."""
    from tui.services import custom_entries

    entries, error = custom_entries.read_entries(kind)
    return error is None and bool(entries)


# =====================================================================
# Task 6 (09-05 Task 3) — panel hardening: 80x24 wrap + scroll bounds,
# drill-down bounds, the guard round trip with the wizard open
# =====================================================================

async def test_import_panel_many_entries_scroll_within_bound_at_80x24():
    """The overflow edge (UI-Considerations: gauntlet lists wrap+scroll
    with the Phase 8 max-height bound): a 6-entry import at 80x24 keeps
    the modal inside the grid — the entry rows live in a bounded
    scrollable region whose bottom is REACHABLE (no clipped statuses)."""
    doc = {f"ds-{i}": {"Dataset_path": f"datasets/ds-{i}",
                       "Category": "Plants"} for i in range(6)}
    service = _FakeGauntlet()
    store = _StoreFake()
    imports = _ImportSeams(doc=doc)
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _dataset_wizard(
            _Seams(), gauntlet_service=service,
            land=store.land, undo=store.undo,
            import_read=imports.read, import_validate=imports.validate)
        await _open(pilot, app, wizard)
        await _press_step_one_key(pilot, app, "f")
        await _submit_path(pilot, app, "/share/custom_datasets.json")
        await _settled(pilot, app)
        assert len(store.land_calls) == 6
        box = wizard.query_one("#wizard-box")
        assert box.region.height <= 24 and box.region.width <= 80, (
            "the modal never exceeds the 80x24 grid"
        )
        rows = wizard.query_one("#gauntlet-rows")
        assert rows.styles.max_height is not None, (
            "the entry rows carry an explicit scroll bound"
        )
        assert rows.virtual_size.height > rows.size.height, (
            "6 entries overflow the bound — the region must scroll"
        )
        assert rows.max_scroll_y > 0, "the bottom is reachable by scroll"
        rows.scroll_to(y=rows.max_scroll_y, animate=False)
        await pilot.pause()
        last_status = wizard.query_one("#gauntlet-status-5", Static)
        assert last_status.region.y < 24, (
            "after scrolling, the last entry's status renders inside the "
            "grid (nothing permanently clipped)"
        )


async def test_drill_down_50_lines_scroll_within_bound_at_80x24():
    """A drill-down with 50 verbatim ~90-char output lines: the log
    wraps (no line elided) and scrolls inside its bound; the modal never
    exceeds the grid."""
    raw = "\n".join(f"LINE-{i:02d}-" + "y" * 80 for i in range(50))
    service = _FakeGauntlet()
    service._raw_override = raw
    original = service.dry_run_precheck

    def dry_with_raw(kind, key, entry, run_id):
        item = original(kind, key, entry, run_id)
        return GauntletItem(run_id=item.run_id, kind=item.kind,
                            leg=item.leg, name=item.name, ok=item.ok,
                            details=item.details, raw_output=raw)

    service.dry_run_precheck = dry_with_raw
    store = _StoreFake()
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _model_wizard(
            _Seams(), gauntlet_service=service,
            land=store.land, undo=store.undo)
        await _open(pilot, app, wizard)
        await _type(pilot, wizard, "key", "my-lm")
        await _submit(pilot, wizard)
        await _settled(pilot, app)
        await pilot.press("enter")  # drill into the focused row
        await pilot.pause()
        drill = wizard.query_one("#gauntlet-drill-log", RichLog)
        joined = "".join(strip.text for strip in drill.lines)
        assert "LINE-00" in joined and "LINE-49" in joined, (
            "every verbatim line present — nothing elided"
        )
        assert drill.styles.max_height is not None, "the bound is set"
        assert len(drill.lines) > 50, "the long lines wrap (never fit)"
        assert drill.max_scroll_y > 0, "the log scrolls within its bound"
        box = wizard.query_one("#wizard-box")
        assert box.region.height <= 24, "the modal never exceeds the grid"


async def test_import_conflict_report_wraps_long_values_at_80x24():
    """The report wrap at 80x24: a 68-char key and a >100-char path in
    conflict problem lines render FULL across wrapped lines in the
    scroll-bounded report — never truncated, never elided."""
    key68 = "k" * 68
    path_long = "/data/dnallm/datasets/" + "d" * 90 + "/x.json"
    problems = [
        (key68, WIZ_PROBLEM_COLLISION_OFFICIAL.format(key=key68)),
        (path_long, WIZ_PROBLEM_PATH_MISSING.format(path=path_long)),
    ]
    imports = _ImportSeams(doc={"ds-x": {}}, problems=problems)
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        wizard = _dataset_wizard(
            _Seams(), gauntlet_service=_FakeGauntlet(),
            land=_StoreFake().land, undo=_StoreFake().undo,
            import_read=imports.read, import_validate=imports.validate)
        await _open(pilot, app, wizard)
        await _press_step_one_key(pilot, app, "f")
        await _submit_path(pilot, app, path_long)
        lines = _prompt_log_text(app)
        joined = "".join(line.rstrip() for line in lines)
        assert key68 in joined, "the full key renders across the wrap"
        assert path_long in joined, "the full path renders across the wrap"
        assert "…" not in joined and "..." not in joined, (
            "nothing elides in the conflict report"
        )


async def test_resize_below_minimum_mid_gauntlet_guard_round_trip():
    """WR-01 with the wizard open: below 80x24 mid-gauntlet the min-size
    guard takes over; growing back restores the panel with its in-flight
    row state intact — and the gated run still completes and lands."""
    gate = threading.Event()
    service = _FakeGauntlet(gates={(LEG_DRY_RUN, 1): gate})
    store = _StoreFake()
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        from tui.app import MinSizeScreen

        wizard = _model_wizard(
            _Seams(), gauntlet_service=service,
            land=store.land, undo=store.undo)
        await _open(pilot, app, wizard)
        await _type(pilot, wizard, "key", "my-lm")
        await _submit(pilot, wizard)
        running = GAUNTLET_ROW_RUNNING.format(item=GAUNTLET_ITEM_DRY_RUN)
        await _wait_row_becomes(pilot, wizard, 0, 0, running)
        # shrink below the minimum grid mid-gauntlet -> the guard swaps in
        await pilot.resize_terminal(60, 20)
        await pilot.pause()
        assert isinstance(app.screen, MinSizeScreen)
        # grow back -> the panel restores with the in-flight row intact
        await pilot.resize_terminal(120, 40)
        await pilot.pause()
        assert app.screen is wizard
        assert _gauntlet_row_text(wizard, 0, 0) == running
        # the gated run completes and lands across the round trip
        gate.set()
        await _settled(pilot, app)
        assert len(store.land_calls) == 1
        assert _gauntlet_row_text(wizard, 0, 0) == (
            GAUNTLET_ROW_DRY_RUN_PASS.format(cells="6"))
