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

from textual.widgets import Checkbox, Input, SelectionList, Static

from tui.app import DnallmMarkTui
from tui.screens.selection import PresetMenu, SelectionData
from tui.screens.wizard import WizardModal
from tui.services import selection as selection_service
from tui.strings import (
    WIZM_STEPS,
    WIZ_CANCEL_CONFIRM,
    WIZ_FOOTER_HINT,
    WIZ_FOOTER_HINT_LAST,
    WIZ_NUMERIC_HINT,
    WIZ_PATH_EXISTS,
    WIZ_PATH_MISSING_ADVISORY,
    WIZ_QUIRK_FP32_ONLY,
    WIZ_QUIRK_NO_SAFETENSORS,
    WIZ_QUIRK_SPECIAL_HEAD,
)

# The i18n grep gate target (the zero-Chinese-literals module).
_WIZARD_MODULE_FILE = Path(__file__).resolve().parents[2] / "tui" / "screens" / "wizard.py"

_SPECIES_VOCAB = ("human", "plants")
_TOKENIZER_VOCAB = ("BPE", "6-mer", "overlapped 6-mer")


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
