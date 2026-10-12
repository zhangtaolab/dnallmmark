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
from pathlib import Path

from textual.widgets import Checkbox, Input, RichLog, SelectionList, Static

from tui.app import DnallmMarkTui
from tui.screens.selection import PresetMenu, SelectionData
from tui.screens.wizard import WizardModal
from tui.services import selection as selection_service
from tui.services.custom_validation import METRIC_REGISTRY
from tui.strings import (
    ENV_STATE_PENDING,
    GAUNTLET_TITLE,
    WIZ_CANCEL_CONFIRM,
    WIZ_FOOTER_HINT,
    WIZ_FOOTER_HINT_LAST,
    WIZ_GAUNTLET_BACK_HINT,
    WIZ_NUMERIC_HINT,
    WIZ_PATH_EXISTS,
    WIZ_PATH_MISSING_ADVISORY,
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
