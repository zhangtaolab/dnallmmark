"""
wizard — the custom-onboarding wizard modal family (Phase 9, 09-04,
CUST-01/02 UI + the CUST-03 report view).

ONE ModalScreen family, two type-aware instances (the add-model and
add-dataset wizards, each exactly the four 09-UI-SPEC steps). Collection
half only: the form and the validation report view land here; the
gauntlet PANEL (the real subprocess view) and the import/export views
are 09-05 against this module's callback seams.

Contract (locked decisions):

- D-01 (wizard shape): a single ModalScreen holds the step state
  (``self._step``), the phase (``self._phase``: form | report |
  gauntlet), and ``self._values`` — the ONE value store; compose renders
  the active step's fields from the declarative step tables, pre-filling
  from ``_values`` so no value is ever lost across a re-compose (the
  preservation contract). ``enter`` advances (last step: submit), ``b``
  goes back, ``esc`` cancels — confirmed via ConfirmModal only when any
  value is entered; a blank form cancels silently.
- Pitfall 9 (value preservation is contract): the validation report and
  the gauntlet are VIEWS inside this same modal (``_phase`` branching),
  never separate pushed screens — dismissing them returns INTO the
  wizard at the same step with every entered value intact. Only an
  explicit esc-confirm, a successful land (09-05), or a used undo clears
  the form.
- D-03 (type-aware controls): enum fields are SelectionLists with
  single-pick enforced here (a new pick clears the previous one — the
  widget is multi-toggle by default); path fields are Inputs with the
  ADVISORY live-check line (the check-ok/check-missing copy, flipping
  per keystroke); numeric fields carry the advisory needs-number hint.
  Advisory never blocks — the authoritative check is the 09-01
  collect-all validator (the operator may be onboarding a
  not-yet-downloaded path; fool-proofing does not become blocking).
- D-02 (quirk step): exactly the three checkboxes, unchecked default;
  values land in the candidate's ``quirks`` field. The execution-side
  quirk-to-CLI mapping is Phase 11 (the boundary is recorded here, not
  implemented).
- CUST-03 (report): submit runs the INJECTED validator seam and renders
  the numbered collect-all list (the validator's own field-definition
  emission order) in a wrapping RichLog — nothing is applied on failure;
  a clean pass hands off through the ``on_valid`` callback seam (09-05
  wires the real gauntlet panel; until then the gauntlet phase renders a
  minimal pending view).
- Modal isolation (inherited): ModalScreen blocks every base-screen
  binding (including the 09-03 digit navigation) while open.
- Prohibitions honored: this screen NEVER writes any registry file
  (submission validates only — D-08: the gauntlet is the only write
  path, wired in 09-05); no benchmark semantics here (row counting and
  survivor logic are CUST-03 service checks or the audit subprocess);
  no priority bindings anywhere (one would fire before the focused
  widget's own keys and break Input typing — 09-RESEARCH Pattern 2).
- I18N-01: zero Chinese literals in this module — every operator string
  renders through ``tui/strings.py`` constants (grep-enforced).

ZERO service logic here (binding constraint 5): the validator and the
path-existence probes arrive as injected callables; this module is
presentation over plain dicts.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Checkbox,
    Input,
    RichLog,
    SelectionList,
    Static,
)
from textual.widgets.selection_list import Selection

from tui.screens.selection import ConfirmModal
from tui.services.custom_validation import (
    DATASET_CATEGORY_VALUES,
    DATASET_TYPE_VALUES,
    MODEL_TYPE_VALUES,
)
from tui.strings import (
    ENV_STATE_PENDING,
    GAUNTLET_TITLE,
    WIZ_BACK_LABEL,
    WIZ_BORDER_TITLE,
    WIZ_CANCEL_CONFIRM,
    WIZ_CANCEL_LABEL,
    WIZ_EXPORT_LABEL,
    WIZ_FOOTER_HINT,
    WIZ_FOOTER_HINT_LAST,
    WIZ_GAUNTLET_BACK_HINT,
    WIZ_IMPORT_LABEL,
    WIZ_KIND_DATASETS,
    WIZ_KIND_MODELS,
    WIZ_NEXT_LABEL,
    WIZ_NUMERIC_HINT,
    WIZ_PATH_EXISTS,
    WIZ_PATH_MISSING_ADVISORY,
    WIZ_PROBLEM_LINE,
    WIZ_PROBLEMS_HEADER,
    WIZ_QUIRK_FP32_ONLY,
    WIZ_QUIRK_NO_SAFETENSORS,
    WIZ_QUIRK_SPECIAL_HEAD,
    WIZ_REPORT_BACK_HINT,
    WIZ_REPORT_TITLE,
    WIZ_SPLIT_FILE_PLACEHOLDER,
    WIZD_FIELD_LABELS,
    WIZD_STEPS,
    WIZM_FIELD_LABELS,
    WIZM_STEPS,
)

# ===== Locations =====
# The advisory path probes resolve relative paths against the pipeline
# dir — the same base the 09-01 validator's ``ValidationSources.fs_root``
# uses by default (the constant mirrors the service's own; a runtime
# import would couple the screen to the service tier for one path).
REPO_ROOT = Path(__file__).resolve().parents[2]
_PIPELINE_DIR = REPO_ROOT / "pipeline"

#: The wizard modal's width rule (09-UI-SPEC Spacing amendment): the
#: Phase 8 modal token widens to ``min(100, width - 4)`` cells — the UAT
#: lesson that 68-char registry keys and long paths must fit. Textual
#: CSS has no ``min()``/arithmetic (probe-pinned on 8.2.8), so the exact
#: formula is applied in code (``_apply_chrome``); styles.tcss carries
#: the base width and the token-only rules.
_WIZARD_MAX_WIDTH = 100


# ===== Declarative step tables =====


@dataclass(frozen=True)
class FieldSpec:
    """One wizard form field: registry field id, widget id, control kind.

    Attributes:
        field: the ``self._values`` key — the registry field name the
            09-01 validator expects (``"key"`` is the registry-key form
            field, never a landed entry field).
        wid: the widget DOM id suffix (queried as ``#wiz-{wid}``).
        control: ``input`` (free text) · ``path`` (Input + the advisory
            existence line) · ``splitfile`` (a split-file-name Input +
            advisory line, checked under the dataset path) · ``numeric``
            (Input + the advisory number hint) · ``selection`` (a
            single-pick SelectionList) · ``quirks`` (the D-02 checkbox
            trio, one spec rendering three checkboxes).
        vocabulary: the fixed enum options; ``None`` means the options
            arrive through the injected ``vocabularies`` mapping (the
            registry-observed / metric-registry sources).
        label_key: the ``WIZ* FIELD_LABELS`` key rendering this field's
            label (defaults to ``field``).
    """

    field: str
    wid: str
    control: str
    vocabulary: "tuple[str, ...] | None" = None
    label_key: "str | None" = None


@dataclass(frozen=True)
class StepSpec:
    """One wizard step: its strings-constant name + ordered fields."""

    name: str
    fields: "tuple[FieldSpec, ...]"


@dataclass(frozen=True)
class KindSpec:
    """One type-aware wizard instance's tables and label map."""

    steps: "tuple[StepSpec, ...]"
    labels: dict
    kind_name: str


#: The D-02 quirk checkbox trio: entry ``quirks`` key -> (label constant,
#: widget id). Unchecked default; the values land in the candidate's
#: ``quirks`` field (the execution-side mapping is Phase 11's).
QUIRK_FIELDS = (
    ("no_safetensors", WIZ_QUIRK_NO_SAFETENSORS, "quirk-no-safetensors"),
    ("fp32_only", WIZ_QUIRK_FP32_ONLY, "quirk-fp32-only"),
    ("special_head", WIZ_QUIRK_SPECIAL_HEAD, "quirk-special-head"),
)

#: The model wizard's four steps (09-UI-SPEC step table, CUST-01).
MODEL_STEPS = (
    StepSpec(WIZM_STEPS[0], (
        FieldSpec("key", "key", "input"),
        FieldSpec("Model_path", "model-path", "path"),
        FieldSpec("size (M)", "size-m", "numeric"),
        FieldSpec("species", "species", "selection"),
    )),
    StepSpec(WIZM_STEPS[1], (
        FieldSpec("type", "type", "selection",
                  vocabulary=tuple(MODEL_TYPE_VALUES)),
        FieldSpec("architecture", "architecture", "input"),
        FieldSpec("Tokenizer", "tokenizer", "selection"),
        FieldSpec("context_len (bp)", "context-len", "numeric"),
    )),
    StepSpec(WIZM_STEPS[2], (
        FieldSpec("huggingface", "huggingface", "input"),
        FieldSpec("modelscope", "modelscope", "input"),
        FieldSpec("series", "series", "input"),
    )),
    StepSpec(WIZM_STEPS[3], (
        FieldSpec("quirks", "quirks", "quirks"),
    )),
)

#: The dataset wizard's four steps (09-UI-SPEC step table, CUST-02).
#: The step-2 split-file Inputs collect FILE NAMES (advisory live
#: existence under the dataset path) — the Train/Dev/Test row counts
#: are NEVER wizard fields: declarations derive at composition
#: downstream (the 09-01 decision), so the composed candidate carries
#: none of them. Task_type stores under the registry field name
#: ``type`` (Auto-Default #11).
DATASET_STEPS = (
    StepSpec(WIZD_STEPS[0], (
        FieldSpec("key", "key", "input"),
        FieldSpec("Dataset_path", "dataset-path", "path"),
        FieldSpec("Category", "category", "selection",
                  vocabulary=tuple(DATASET_CATEGORY_VALUES)),
    )),
    StepSpec(WIZD_STEPS[1], (
        FieldSpec("train_file", "train-file", "splitfile",
                  label_key="Train"),
        FieldSpec("dev_file", "dev-file", "splitfile", label_key="Dev"),
        FieldSpec("test_file", "test-file", "splitfile", label_key="Test"),
        FieldSpec("label_column", "label-column", "input"),
        FieldSpec("labels", "labels", "numeric"),
        FieldSpec("length", "length", "numeric"),
    )),
    StepSpec(WIZD_STEPS[2], (
        FieldSpec("type", "type", "selection",
                  vocabulary=tuple(DATASET_TYPE_VALUES)),
        FieldSpec("metric", "metric", "selection"),
    )),
    StepSpec(WIZD_STEPS[3], (
        FieldSpec("citation", "citation", "input"),
        FieldSpec("source", "source", "input"),
        FieldSpec("license", "license", "input"),
        FieldSpec("preprocessing", "preprocessing", "input"),
    )),
)

#: Kind -> the type-aware instance's tables + labels.
KINDS: dict = {
    "models": KindSpec(
        steps=MODEL_STEPS,
        labels=WIZM_FIELD_LABELS,
        kind_name=WIZ_KIND_MODELS,
    ),
    "datasets": KindSpec(
        steps=DATASET_STEPS,
        labels=WIZD_FIELD_LABELS,
        kind_name=WIZ_KIND_DATASETS,
    ),
}

#: The numeric-input fields whose text composes as a JSON number when
#: parseable (unparseable text passes through raw — the collect-all
#: validator's numeric check flags it, never the screen).
_NUMERIC_FIELDS = frozenset(
    {"size (M)", "context_len (bp)", "labels", "length"})


# ===== Default advisory probes (real fs, resolution mirroring 09-01) =====


def _default_dir_exists(raw):
    """Advisory directory-existence probe (absolute as-is, else pipeline)."""
    path = Path(raw)
    if not path.is_absolute():
        path = _PIPELINE_DIR / path
    return path.is_dir()


def _default_file_exists(raw):
    """Advisory file-existence probe (absolute as-is, else pipeline)."""
    path = Path(raw)
    if not path.is_absolute():
        path = _PIPELINE_DIR / path
    return path.is_file()


def _parses_as_number(text):
    """True when the advisory numeric hint should clear."""
    try:
        float(text)
    except ValueError:
        return False
    return True


class WizardModal(ModalScreen):
    """The add-model / add-dataset wizard: collect, validate, report.

    Construction injects every behavior seam (RESEARCH Pattern 7):

    Args:
        kind: ``"models"`` or ``"datasets"`` — the type-aware instance.
        validator: ``(values) -> Sequence[(field_key, message)]`` — the
            09-01 collect-all validator (pre-bound to its
            ``ValidationSources`` by the caller); tests inject fakes.
        on_valid: called once with the composed candidate dict on a
            clean validation pass (the 09-05 gauntlet seam).
        on_import: the step-1 ``f`` seam (the file-import view, 09-05).
        on_export: the step-1 ``o`` seam (the registry export, 09-05).
        prefill: an optional one-item ``{key: entry}`` custom-entry map
            (D-12: edit = delete + re-record — the 09-06 ``w`` push).
        vocabularies: injected enum vocabularies keyed by field name
            (species / Tokenizer / metric — the registry-observed and
            metric-registry sources; empty = the list renders empty and
            validation skips, the 09-01 empty-vocabulary rule).
        dir_exists: advisory path-existence probe for directory fields
            (default: the real fs, resolution mirroring 09-01).
        file_exists: advisory existence probe for split-file fields.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "request_cancel", WIZ_CANCEL_LABEL, show=False),
        Binding("enter", "advance", WIZ_NEXT_LABEL, show=False),
        Binding("b", "go_back", WIZ_BACK_LABEL, show=False),
        # Step-1-only affordances (D-11): declared once, the actions
        # no-op outside step 1; the views are 09-05 against the seams.
        Binding("f", "do_import", WIZ_IMPORT_LABEL, show=False),
        Binding("o", "do_export", WIZ_EXPORT_LABEL, show=False),
    ]

    def __init__(self, kind, validator, on_valid=None, on_import=None,
                 on_export=None, prefill=None, vocabularies=None,
                 dir_exists=None, file_exists=None, **kwargs):
        super().__init__(**kwargs)
        if kind not in KINDS:
            raise ValueError(
                f"unknown wizard kind {kind!r} — expected one of "
                f"{sorted(KINDS)}"
            )
        self._kind = kind
        self._validator = validator
        self._on_valid = on_valid
        self._on_import = on_import
        self._on_export = on_export
        self._vocabularies = {k: tuple(v)
                              for k, v in (vocabularies or {}).items()}
        self._dir_exists = dir_exists or _default_dir_exists
        self._file_exists = file_exists or _default_file_exists
        kind_spec = KINDS[kind]
        self._steps = kind_spec.steps
        self._labels = kind_spec.labels
        self._step = 0
        self._phase = "form"
        self._problems = []
        self._candidate = None
        #: wid -> field (the advisory/changed-event router).
        self._wid_field = {
            spec.wid: spec.field
            for step in self._steps for spec in step.fields
        }
        # Heterogeneous by design: string field values plus the
        # quirk checkbox state dict (D-02) — plain dict, Any values.
        self._values: dict = {"quirks": {name: False
                                       for name, _, _ in QUIRK_FIELDS}}
        self._apply_prefill(prefill)

    # ===== Prefill (D-12: edit = delete + re-record) =====

    def _apply_prefill(self, prefill):
        """Fold a one-item ``{key: entry}`` custom map into ``_values``.

        Every entry field that maps to a wizard field prefills it — the
        key included, so the collect-all collision check forces the
        change (the D-12 discipline needs no edit surface); fields the
        entry does not carry stay blank. The split-file-name inputs have
        no entry counterpart (landed rows carry row counts, not file
        names) and are never prefilled; ``enabled`` and the name stamps
        are land-time service fields the form never collects.
        """
        if not prefill:
            return
        items = list(prefill.items())
        if len(items) != 1 or not isinstance(items[0][1], dict):
            raise ValueError(
                "prefill must be a one-item {key: entry} custom-entry map"
            )
        key, entry = items[0]
        self._values["key"] = key
        for step in self._steps:
            for spec in step.fields:
                if spec.control == "quirks":
                    quirks = entry.get("quirks")
                    if isinstance(quirks, dict):
                        for name, _, _ in QUIRK_FIELDS:
                            self._values["quirks"][name] = bool(
                                quirks.get(name, False))
                    continue
                if spec.field in entry:
                    self._values[spec.field] = entry[spec.field]

    # ===== Compose (the active phase view) =====

    def compose(self) -> ComposeResult:
        """Render the active phase: the form step, the report, gauntlet."""
        with Vertical(id="wizard-box", classes="wizard-box"):
            if self._phase == "form":
                yield from self._compose_step()
            elif self._phase == "report":
                yield RichLog(wrap=True, id="wiz-report-log")
                yield Static(WIZ_REPORT_BACK_HINT,
                             id="wiz-report-hint")
            else:  # gauntlet — the minimal pending view (panel = 09-05)
                yield Static(ENV_STATE_PENDING, id="wiz-gauntlet-pending")
                yield Static(WIZ_GAUNTLET_BACK_HINT,
                             id="wiz-gauntlet-hint")

    def _compose_step(self):
        """The active step's fields, pre-filled from ``_values``."""
        step = self._steps[self._step]
        for spec in step.fields:
            yield Static(
                self._labels.get(spec.label_key or spec.field,
                                 spec.field),
                classes="wiz-field-label",
            )
            value = self._values.get(spec.field, "")
            if spec.control in ("input", "path", "numeric", "splitfile"):
                placeholder = (WIZ_SPLIT_FILE_PLACEHOLDER
                               if spec.control == "splitfile" else "")
                yield Input(value="" if value is None else str(value),
                            placeholder=placeholder,
                            id=f"wiz-{spec.wid}")
                yield Static("", id=f"wiz-{spec.wid}-check",
                             classes="wiz-check")
            elif spec.control == "selection":
                options = self._options_for(spec)
                yield SelectionList(
                    *(Selection(option, option,
                                initial_state=(option == value))
                      for option in options),
                    id=f"wiz-{spec.wid}",
                )
            elif spec.control == "quirks":
                for name, label, wid in QUIRK_FIELDS:
                    yield Checkbox(
                        label,
                        value=bool(self._values["quirks"].get(name)),
                        id=f"wiz-{wid}",
                    )
        hint = (WIZ_FOOTER_HINT_LAST
                if self._step == len(self._steps) - 1 else WIZ_FOOTER_HINT)
        yield Static(hint, id="wiz-footer-hint")

    def _options_for(self, spec):
        """The enum options: the fixed vocabulary, else the injected one."""
        if spec.vocabulary is not None:
            return spec.vocabulary
        return tuple(self._vocabularies.get(spec.field, ()))

    # ===== Chrome: border title (accent step number) + the width rule =====

    def _apply_chrome(self) -> None:
        """Set the border title + the min(100, width-4) box width."""
        box = self.query_one("#wizard-box", Vertical)
        if self._phase == "form":
            step = self._steps[self._step]
            indicator = f"[{self.app.current_theme.accent} bold]" \
                        f"{self._step + 1}/{len(self._steps)}[/]"
            box.border_title = WIZ_BORDER_TITLE.format(
                kind=KINDS[self._kind].kind_name,
                indicator=indicator,
                step=step.name,
            )
        elif self._phase == "report":
            box.border_title = WIZ_REPORT_TITLE.format(
                kind=KINDS[self._kind].kind_name)
        else:  # gauntlet pending
            box.border_title = GAUNTLET_TITLE.format(
                key=self._values.get("key", ""))
        box.styles.width = min(
            _WIZARD_MAX_WIDTH, max(20, self.size.width - 4))

    def on_mount(self) -> None:
        """Apply chrome + the initial advisory lines."""
        self._apply_chrome()
        self._refresh_advisories()

    def on_resize(self, event: events.Resize) -> None:
        """Re-apply the width rule (the terminal resized under us)."""
        self._apply_chrome()

    # ===== Value routing (every control funnels into ``_values``) =====

    def on_input_changed(self, event: Input.Changed) -> None:
        """Every keystroke lands in ``_values`` + the advisory lines."""
        wid = (event.input.id or "")
        if not wid.startswith("wiz-"):
            return
        field = self._wid_field.get(wid[4:])
        if field is None:
            return
        self._values[field] = event.value
        self._refresh_advisories()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter inside an Input advances (the Input eats the key)."""
        if self._phase == "form":
            await self.action_advance()

    def on_selection_list_selection_toggled(
            self, event: SelectionList.SelectionToggled) -> None:
        """Single-pick enforcement: a new pick clears the previous one."""
        selection_list = event.selection_list
        wid = (selection_list.id or "")
        field = self._wid_field.get(wid[4:])
        if field is None:
            return
        selected = list(selection_list.selected)
        if len(selected) > 1:
            keep = event.selection.value  # the newly toggled pick wins
            for value in selected:
                if value != keep:
                    # deselect accepts the option VALUE directly — no
                    # re-selection message fires (programmatic, no loop)
                    selection_list.deselect(value)
            selected = [keep]
        self._values[field] = selected[0] if selected else ""

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Quirk checkboxes land in the ``quirks`` dict (D-02)."""
        wid = (event.checkbox.id or "")
        for name, _, quirk_wid in QUIRK_FIELDS:
            if wid == f"wiz-{quirk_wid}":
                self._values["quirks"][name] = bool(event.value)

    # ===== Advisory lines (D-03 — advisory only, never blocking) =====

    def _refresh_advisories(self) -> None:
        """Update every advisory line present in the active step."""
        for spec in self._steps[self._step].fields:
            if spec.control not in ("path", "numeric", "splitfile"):
                continue
            check = self.query(f"#wiz-{spec.wid}-check").first(Static)
            if check is None:
                continue  # not in the DOM (different phase/step)
            text, css_class = self._advisory_for(spec)
            check.update(text)
            check.classes = f"wiz-check {css_class}" if css_class else \
                "wiz-check"

    def _advisory_for(self, spec):
        """One field's advisory (text, css class); blank lines stay blank.

        Returns:
            tuple[str, str]: the line text and the extra CSS class
            (``wiz-check-ok`` / ``wiz-check-bad`` / ``wiz-hint-bad`` /
            ``""`` for blank).
        """
        value = self._values.get(spec.field, "")
        if not isinstance(value, str) or not value.strip():
            return "", ""
        if spec.control == "numeric":
            if _parses_as_number(value):
                return "", ""
            return WIZ_NUMERIC_HINT, "wiz-hint-bad"
        if spec.control == "path":
            if self._dir_exists(value):
                return WIZ_PATH_EXISTS, "wiz-check-ok"
            return WIZ_PATH_MISSING_ADVISORY, "wiz-check-bad"
        # splitfile: the name is checked under the collected dataset path
        dataset_path = self._values.get("Dataset_path", "")
        if not isinstance(dataset_path, str) or not dataset_path.strip():
            return "", ""
        target = str(Path(dataset_path) / value)
        if self._file_exists(target):
            return WIZ_PATH_EXISTS, "wiz-check-ok"
        return WIZ_PATH_MISSING_ADVISORY, "wiz-check-bad"

    # ===== Navigation: enter / b / esc =====

    async def action_advance(self) -> None:
        """Enter: next step; last step submits; report/gauntlet return."""
        if self._phase != "form":
            await self._return_to_form()
        elif self._step < len(self._steps) - 1:
            self._step += 1
            await self.recompose()
            self._apply_chrome()
            self._refresh_advisories()
        else:
            await self._submit()

    # ===== Submit: compose, validate, report / hand off (CUST-03) =====

    async def _submit(self) -> None:
        """Step-4 enter: run the injected validator; problems render as
        the collect-all report (nothing applied), a clean pass hands the
        candidate to the gauntlet seam (09-05 wires the real panel)."""
        candidate = self._compose_candidate()
        problems = list(self._validator(candidate) or [])
        if problems:
            self._problems = problems
            self._phase = "report"
            await self.recompose()
            self._apply_chrome()
            self._write_report()
        else:
            self._candidate = candidate
            self._phase = "gauntlet"
            await self.recompose()
            self._apply_chrome()
            if self._on_valid is not None:
                self._on_valid(candidate)

    def _write_report(self) -> None:
        """Render the numbered collect-all list (validator emission order)."""
        log = self.query_one("#wiz-report-log", RichLog)
        log.write(WIZ_PROBLEMS_HEADER.format(n=len(self._problems)))
        for index, (field_key, message) in enumerate(self._problems):
            log.write(WIZ_PROBLEM_LINE.format(
                i=index + 1,
                field_label=self._labels.get(field_key, field_key),
                problem=message,
            ))

    def _compose_candidate(self):
        """Assemble ``_values`` into the candidate dict the 09-01
        validator and the 09-05 gauntlet/land seam expect.

        The screen stamps NOTHING the services own: no name stamps
        (``Model_name``/``Dataset_name`` are the land service's), no
        path relativization, no enabled flag. The split-file names are
        advisory-only collection and never ride along (Train/Dev/Test
        derive at composition downstream — the 09-01 decision).
        Numeric-input text composes as a number when parseable; the
        optional free-text fields compose as empty strings, never None.
        """
        candidate = {}
        for step in self._steps:
            for spec in step.fields:
                if spec.control == "quirks":
                    candidate["quirks"] = dict(self._values["quirks"])
                    continue
                if spec.control == "splitfile":
                    continue
                value = self._values.get(spec.field, "")
                if spec.field in _NUMERIC_FIELDS:
                    candidate[spec.field] = self._as_number(value)
                else:
                    candidate[spec.field] = (
                        value if isinstance(value, str) else str(value))
        return candidate

    @staticmethod
    def _as_number(value):
        """Numeric-input text -> int/float when parseable (integral
        text stays int); unparseable text passes through raw so the
        collect-all validator reports it — the screen never hides a
        defect an advisory already flagged."""
        if not isinstance(value, str):
            return value
        text = value.strip()
        if not text:
            return ""
        try:
            return int(text)
        except ValueError:
            try:
                return float(text)
            except ValueError:
                return value

    async def action_go_back(self) -> None:
        """b: one step back, values preserved (auto-default #4)."""
        if self._phase != "form":
            return
        if self._step > 0:
            self._step -= 1
            await self.recompose()
            self._apply_chrome()
            self._refresh_advisories()

    async def action_request_cancel(self) -> None:
        """Esc: report/gauntlet return; a blank form cancels; entered
        values confirm through the destructive gate first."""
        if self._phase != "form":
            await self._return_to_form()
            return
        filled = self._filled_steps()
        if filled == 0:
            self.dismiss()
            return
        self.app.push_screen(ConfirmModal(
            WIZ_CANCEL_CONFIRM.format(n=filled),
            on_confirm=self._abandon,
        ))

    def _abandon(self) -> None:
        """The confirm's destructive choice: discard the form."""
        self.dismiss()

    def action_do_import(self) -> None:
        """f on step 1: the file-import seam (the view is 09-05's)."""
        if self._phase == "form" and self._step == 0 and self._on_import:
            self._on_import()

    def action_do_export(self) -> None:
        """o on step 1: the registry-export seam (the view is 09-05's)."""
        if self._phase == "form" and self._step == 0 and self._on_export:
            self._on_export()

    async def _return_to_form(self) -> None:
        """Report/gauntlet dismissal: same step, every value intact."""
        self._phase = "form"
        await self.recompose()
        self._apply_chrome()
        self._refresh_advisories()

    # ===== The esc-confirm filled-step count =====

    def _filled_steps(self):
        """Count steps holding at least one value (the confirm's {n})."""
        filled = 0
        for step in self._steps:
            for spec in step.fields:
                if spec.control == "quirks":
                    if any(self._values["quirks"].values()):
                        filled += 1
                        break
                    continue
                value = self._values.get(spec.field)
                if value is None or value == "":
                    continue
                if isinstance(value, str) and not value.strip():
                    continue
                filled += 1
                break
        return filled
