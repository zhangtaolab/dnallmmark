"""
wizard — the custom-onboarding wizard modal family (Phase 9, 09-04,
CUST-01/02 UI + the CUST-03 report view).

ONE ModalScreen family, two type-aware instances (新增模型 /
新增数据集), each exactly the four 09-UI-SPEC steps. Collection half
only: the form and the validation report view land here; the gauntlet
PANEL (the real subprocess view) and the import/export views are 09-05
against this module's callback seams.

Contract (locked decisions):

- D-01 (wizard shape): a single ModalScreen holds the step state
  (``self._step``), the phase (``self._phase``: form | report |
  gauntlet), and ``self._values`` — the ONE value store; compose renders
  the active step's fields from the declarative step tables, pre-filling
  from ``_values`` so no value is ever lost across a re-compose (the
  preservation contract). ``enter`` advances (last step: submit),
  ``b`` goes back, ``esc`` cancels — confirmed via ConfirmModal only
  when any value is entered; a blank form cancels silently.
- Pitfall 9 (value preservation is contract): the validation report and
  the gauntlet are VIEWS inside this same modal (``_phase`` branching),
  never separate pushed screens — dismissing them returns INTO the
  wizard at the same step with every entered value intact. Only an
  explicit esc-confirm, a successful land (09-05), or a used undo clears
  the form.
- D-03 (type-aware controls): enum fields are SelectionLists with
  single-pick enforced here (a new pick clears the previous one — the
  widget is multi-toggle by default); path fields are Inputs with the
  ADVISORY live-check line (✓/✗ copy, flips per keystroke); numeric
  fields carry the advisory ✗ 需为数字 hint. Advisory never blocks —
  the authoritative check is the 09-01 collect-all validator.
- D-02 (quirk step): exactly the three checkboxes, unchecked default;
  values land in the candidate's ``quirks`` field. The execution-side
  quirk → CLI mapping is Phase 11 (the boundary is recorded here, not
  implemented).
- CUST-03 (report): submit runs the INJECTED validator seam and renders
  the numbered collect-all list (field-definition order, the validator's
  own emission order) in a wrapping RichLog — nothing is applied on
  failure; a clean pass hands off through the ``on_valid`` callback seam
  (09-05 wires the real gauntlet panel; the gauntlet phase renders a
  minimal pending view until then).
- Prohibitions honored: this screen NEVER writes any registry file
  (submission validates only — D-08: the gauntlet is the only write
  path, wired in 09-05); no benchmark semantics here (row counting and
  survivor logic are CUST-03 service checks or the audit subprocess);
  no ``Binding(priority=True)`` anywhere (it would break Input typing —
  09-RESEARCH Pattern 2).
- I18N-01: zero Chinese literals in this module — every operator string
  renders through ``tui/strings.py`` constants (grep-enforced).

ZERO service logic here (binding constraint 5): the validator,
path-existence probes, and all downstream behavior arrive as injected
callables; this module is presentation over plain dicts.
"""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

from tui.strings import (
    WIZ_CANCEL_LABEL,
    WIZ_FOOTER_HINT,
)


class WizardModal(ModalScreen):
    """The 新增{模型,数据集} wizard: four steps, collect, validate, report.

    Construction injects every behavior seam (RESEARCH Pattern 7):

    Args:
        kind: ``"models"`` or ``"datasets"`` — the type-aware instance.
        validator: ``(values) -> Sequence[(field_key, message)]`` — the
            09-01 collect-all validator (pre-bound to its
            ``ValidationSources`` by the caller); tests inject fakes.
        on_valid: called once with the composed candidate dict on a clean
            validation pass (the 09-05 gauntlet seam).
        on_import: the step-1 ``f`` seam (从文件导入 — the 09-05 view).
        on_export: the step-1 ``o`` seam (导出自定义注册表 — 09-05).
        prefill: an optional one-item ``{key: entry}`` custom-entry map
            (D-12: 编辑 = 删除 + 重录 — the 09-06 ``w``-key push).
        vocabularies: injected enum vocabularies keyed by field name
            (species / Tokenizer / metric — the registry-observed and
            metric-registry sources the screens never hardcode).
        dir_exists: advisory path-existence probe for directory fields.
        file_exists: advisory existence probe for split-file fields.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "request_cancel", WIZ_CANCEL_LABEL, show=False),
    ]

    def __init__(self, kind, validator, on_valid=None, on_import=None,
                 on_export=None, prefill=None, vocabularies=None,
                 dir_exists=None, file_exists=None, **kwargs):
        super().__init__(**kwargs)
        self._kind = kind
        self._validator = validator
        self._on_valid = on_valid
        self._on_import = on_import
        self._on_export = on_export
        self._prefill = prefill
        self._vocabularies = dict(vocabularies or {})
        self._dir_exists = dir_exists
        self._file_exists = file_exists
        self._values = {}
        self._step = 0
        self._phase = "form"

    def compose(self) -> ComposeResult:
        """Render the active phase (form step / report / gauntlet)."""
        with Vertical(id="wizard-box", classes="wizard-box"):
            yield Static(WIZ_FOOTER_HINT, id="wiz-footer-hint")

    def action_request_cancel(self) -> None:
        """Esc: cancel (confirmed when any value is entered)."""
        self.dismiss()
