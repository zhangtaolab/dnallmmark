"""
wizard — the custom-onboarding wizard modal family (Phase 9, 09-04 +
09-05; CUST-01/02 UI, the CUST-03 report view, and the CUST-04 gauntlet
panel with the D-11 import/export views).

ONE ModalScreen family, two type-aware instances (the add-model and
add-dataset wizards, each exactly the four 09-UI-SPEC steps). The
collection half (09-04) lands the form and the validation report view;
the writing half (09-05) lands the gauntlet PANEL — the real async
subprocess view — plus the session-undo affordance and the import/export
views behind the step-1 ``f``/``o`` seams.

Contract (locked decisions):

- D-01 (wizard shape): a single ModalScreen holds the step state
  (``self._step``), the phase (``self._phase``: form | report |
  gauntlet | drill), and ``self._values`` — the ONE value store; compose
  renders the active step's fields from the declarative step tables,
  pre-filling from ``_values`` so no value is ever lost across a
  re-compose (the preservation contract). ``enter`` advances (last step:
  submit), ``b`` goes back, ``esc`` cancels — confirmed via ConfirmModal
  only when any value is entered; a blank form cancels silently.
- Pitfall 9 (value preservation is contract): the validation report,
  the gauntlet panel, and the drill-down are VIEWS inside this same
  modal (``_phase`` branching), never separate pushed screens —
  dismissing them returns INTO the wizard at the same step with every
  entered value intact. Only an explicit esc-confirm, a successful land,
  or a used undo clears the form.
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
  a clean pass transitions into the gauntlet phase (the ``on_valid``
  callback fires as the observer seam).
- CUST-04 / D-06/D-07/D-08 (the gauntlet panel, 09-05): the panel
  renders one row per kind-aware item (models: dry-run only; datasets:
  dry-run + audit — the service's own ``reconcile`` leg rule mirrored
  1:1) and drives the INJECTED gauntlet service per leg from ONE
  exclusive ``@work(thread=True)`` worker (the 08-06 discipline: the
  console never freezes; posting per-item messages, polling
  ``is_cancelled`` between legs). Every message carries the run id; the
  handlers drop stale ids (WR-02) AND anything not addressed to a live
  gauntlet view. All-✓ lands exactly once THROUGH THE INJECTED land
  seam (the 09-01 store — this screen never writes a file); any ✗
  renders the prominent zero-touch banner and lands nothing. The
  verdicts are ALWAYS the service's parsed-artifact results — the panel
  renders them, never recomputes (binding constraint 5).
- D-11 (import/export, 09-05): ``f`` pushes the import path prompt —
  the collect-all import validation renders its numbered conflicts
  through the same report surface and NOTHING merges on any problem; a
  clean file re-enters this same panel grouped per entry, entries
  gauntleted sequentially in FILE order, a failing entry reverting at
  entry level while the others land. ``o`` short-circuits the
  empty-state toast before any path is asked and otherwise copies the
  registry through the injected export seam (verbatim byte copy).
- Modal isolation (inherited): ModalScreen blocks every base-screen
  binding (including the 09-03 digit navigation) while open.
- Prohibitions honored: this screen NEVER writes any registry file —
  land/undo/export go through the injected store seams exclusively
  (D-08: the all-✓ gauntlet completion is the only custom-registry
  write path, and the official registries are never written by any
  flow); no benchmark semantics here (row counting and survivor logic
  are CUST-03 service checks or the audit subprocess); no priority
  bindings anywhere (one would fire before the focused widget's own
  keys and break Input typing — 09-RESEARCH Pattern 2).
- I18N-01: zero Chinese literals in this module — every operator string
  renders through ``tui/strings.py`` constants (grep-enforced).

ZERO service logic here (binding constraint 5): the validator, the
gauntlet service, the store seams, and the path-existence probes arrive
as injected callables; this module is presentation over plain dicts and
the service's structured items.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from rich.text import Text
from textual import events, work
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Vertical, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import (
    Checkbox,
    Footer,
    Input,
    RichLog,
    SelectionList,
    Static,
)
from textual.widgets.selection_list import Selection
from textual.worker import get_current_worker

from tui import strings as S
from tui.screens.selection import ConfirmModal
from tui.services.custom_validation import (
    DATASET_CATEGORY_VALUES,
    DATASET_TYPE_VALUES,
    MODEL_TYPE_VALUES,
)
from tui.services.gauntlet import LEG_AUDIT, LEG_DRY_RUN, GauntletItem

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
    ("no_safetensors", S.WIZ_QUIRK_NO_SAFETENSORS, "quirk-no-safetensors"),
    ("fp32_only", S.WIZ_QUIRK_FP32_ONLY, "quirk-fp32-only"),
    ("special_head", S.WIZ_QUIRK_SPECIAL_HEAD, "quirk-special-head"),
)

#: The model wizard's four steps (09-UI-SPEC step table, CUST-01).
MODEL_STEPS = (
    StepSpec(S.WIZM_STEPS[0], (
        FieldSpec("key", "key", "input"),
        FieldSpec("Model_path", "model-path", "path"),
        FieldSpec("size (M)", "size-m", "numeric"),
        FieldSpec("species", "species", "selection"),
    )),
    StepSpec(S.WIZM_STEPS[1], (
        FieldSpec("type", "type", "selection",
                  vocabulary=tuple(MODEL_TYPE_VALUES)),
        FieldSpec("architecture", "architecture", "input"),
        FieldSpec("Tokenizer", "tokenizer", "selection"),
        FieldSpec("context_len (bp)", "context-len", "numeric"),
    )),
    StepSpec(S.WIZM_STEPS[2], (
        FieldSpec("huggingface", "huggingface", "input"),
        FieldSpec("modelscope", "modelscope", "input"),
        FieldSpec("series", "series", "input"),
    )),
    StepSpec(S.WIZM_STEPS[3], (
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
    StepSpec(S.WIZD_STEPS[0], (
        FieldSpec("key", "key", "input"),
        FieldSpec("Dataset_path", "dataset-path", "path"),
        FieldSpec("Category", "category", "selection",
                  vocabulary=tuple(DATASET_CATEGORY_VALUES)),
    )),
    StepSpec(S.WIZD_STEPS[1], (
        FieldSpec("train_file", "train-file", "splitfile",
                  label_key="Train"),
        FieldSpec("dev_file", "dev-file", "splitfile", label_key="Dev"),
        FieldSpec("test_file", "test-file", "splitfile", label_key="Test"),
        FieldSpec("label_column", "label-column", "input"),
        FieldSpec("labels", "labels", "numeric"),
        FieldSpec("length", "length", "numeric"),
    )),
    StepSpec(S.WIZD_STEPS[2], (
        FieldSpec("type", "type", "selection",
                  vocabulary=tuple(DATASET_TYPE_VALUES)),
        FieldSpec("metric", "metric", "selection"),
    )),
    StepSpec(S.WIZD_STEPS[3], (
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
        labels=S.WIZM_FIELD_LABELS,
        kind_name=S.WIZ_KIND_MODELS,
    ),
    "datasets": KindSpec(
        steps=DATASET_STEPS,
        labels=S.WIZD_FIELD_LABELS,
        kind_name=S.WIZ_KIND_DATASETS,
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


# ===== The gauntlet panel (CUST-04 UI, 09-05) =====

#: Row text styles (theme tokens; the glyph carries the state under
#: NO_COLOR — the glyph+color redundancy rule). Probe-pinned on 8.2.8:
#: ``Text(style="$token")`` updates render correctly in Statics AFTER
#: mount (the styling pass below runs post-recompose, never in compose).
_ROW_STYLE_DIM = "$text-muted"
_ROW_STYLE_PASS = "bold $success"
_ROW_STYLE_FAIL = "bold $error"

#: The drill-down RichLog's scroll bound (the 08-06 env-detail precedent:
#: a height cap is not a spacing token — wrap + scroll, never elide).
_DRILL_LOG_MAX_HEIGHT = 20

#: Rows the gauntlet panel reserves OUTSIDE the scrollable entry region
#: (the box border top+bottom, the banner, the undo affordance, the
#: hint line, one spare) — the entry region's code-applied max-height
#: cap is the grid height minus this (same scroll-bound rule).
_PANEL_CHROME_ROWS = 6


def _first_or_none(query):
    """The safe empty-tolerant lookup: ``DOMQuery.first`` RAISES
    ``NoMatches`` on an empty query (probe-pinned on 8.2.8 — it never
    returns None), while the panel's optional widgets (a drill view
    holds the DOM; single-mode heads never exist) need a None path."""
    return query.nodes[0] if query.nodes else None


class _GauntletRow(Static):
    """One focusable gauntlet row (``enter`` drills into its item)."""

    can_focus = True


def _legs_for_kind(kind):
    """The kind-aware leg composition (the 09-02 service's own
    ``reconcile`` rule mirrored exactly: models gauntlet the dry-run leg
    ONLY; datasets run both legs sequentially — n_audit is dataset-only
    by design).

    Args:
        kind (str): ``"models"`` or ``"datasets"``.

    Returns:
        list[tuple[str, str]]: ``(leg, label)`` pairs in execution order.
    """
    legs = [(LEG_DRY_RUN, S.GAUNTLET_ITEM_DRY_RUN)]
    if kind == "datasets":
        legs.append((LEG_AUDIT, S.GAUNTLET_ITEM_AUDIT))
    return legs


def _detail_value(details, token):
    """Extract one ``token=value`` detail's value (data, verbatim).

    Args:
        details (tuple[str, ...]): the item's structured detail tokens.
        token (str): the token name (e.g. ``"planned_cells"``).

    Returns:
        str: the value after ``=``, or ``""`` when the token is absent.
    """
    prefix = token + "="
    for detail in details:
        if detail.startswith(prefix):
            return detail[len(prefix):]
    return ""


class _PathPromptModal(ModalScreen):
    """The f/o path entry prompt (the PathInputModal idiom, 09-05).

    Differences from the selection-screen idiom, both plan-owned: the
    problems view is a wrapping scroll-bounded RichLog (import conflict
    lists carry 68-char keys and wrap, never truncate), and a clean pass
    dismisses into an ASYNC accept continuation (the import transition
    recomposes the wizard beneath this modal).

    ``validate(path)`` returns ``None`` on success or a problems
    sequence — the numbered report renders through the injected header
    and the modal stays open (fail-closed: nothing was applied). WR-04
    (09 review): the validate call runs in an exclusive thread worker
    (the PresetMenuLoaded pattern) — the f/o seams perform real file
    I/O (the import read, the export copy) and must never run on the
    event loop (D-03: the console never freezes).
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", S.APP_MODAL_BACK_LABEL),
    ]

    #: The problems log's scroll bound (the wrap-never-elide rule; a
    #: height cap is not a spacing token — the env-detail precedent).
    _PROBLEMS_MAX_HEIGHT = 12

    class Validated(Message, namespace="path_prompt"):
        """The validation worker finished: the path, its verdict
        (``None`` problems = clean pass), and the submit GENERATION the
        worker served (WR-07, 09 review — a superseded submit's verdict
        is dropped by the handler)."""

        def __init__(self, path: str, problems,
                     generation: int) -> None:
            self.path = path
            self.problems = problems
            self.generation = generation
            super().__init__()

    def __init__(self, title, placeholder, problems_header, validate,
                 accept, **kwargs):
        super().__init__(**kwargs)
        self._title = title
        self._placeholder = placeholder
        self._problems_header = problems_header
        self._validate = validate
        self._accept = accept
        # WR-07 (09 review): the submit generation — bumped on every
        # submit, captured by the worker it spawns; a Validated message
        # from any but the CURRENT generation is a superseded verdict.
        self._generation = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="wizard-path-box", classes="modal-box"):
            yield Input(placeholder=self._placeholder,
                        id="wizard-path-input")
            yield RichLog(wrap=True, id="wizard-path-problems")
            yield Footer()

    def on_mount(self) -> None:
        box = self.query_one("#wizard-path-box", Vertical)
        box.border_title = self._title
        log = self.query_one("#wizard-path-problems", RichLog)
        log.styles.max_height = self._PROBLEMS_MAX_HEIGHT
        self.query_one("#wizard-path-input", Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Submit the value; the validation itself runs in the worker
        (WR-04 — the I/O never runs on the event loop). Each submit
        bumps the generation: any verdict from an EARLIER submit is
        superseded (WR-07 — exclusive=True cancels the worker object,
        but its thread still runs to completion and posts)."""
        value = event.value.strip()
        if not value:
            return
        self._generation += 1
        self._validate_in_worker(value, self._generation)

    @work(exclusive=True, thread=True, exit_on_error=False)
    def _validate_in_worker(self, path: str, generation: int) -> None:
        """Run the injected validate seam OFF the event loop (WR-04, the
        D-03 discipline): a network-mounted import path or a slow disk
        blocks here, not the console. The verdict crosses back as the
        ``Validated`` message tagged with the generation captured ON THE
        EVENT LOOP before the I/O (WR-07 — the multi-event interleavings
        the worker's existence makes reachable: an esc mid-validation or
        a superseding submit must be able to drop the verdict; the
        handler's guards plus the wizard-side generation-keyed stash
        close them). The worker performs no DOM access."""
        problems = self._validate(path, generation)
        self.post_message(
            self.Validated(path, problems, generation))

    async def on_path_prompt_validated(self, message: Validated) -> None:
        """Render the worker's verdict: the numbered problems report
        (fail-closed, the modal stays open), or the dismiss into the
        async accept continuation — only for the CURRENT generation on
        a LIVE modal (WR-07: a superseded submit's verdict is dropped;
        an esc/closed modal's verdict is dropped — the ExportStateReady
        discipline — else dismiss() would fire twice and pop_screen()
        would pop the WIZARD beneath, and the accept would land a
        cancelled import on the detached wizard)."""
        if message.generation != self._generation:
            return  # superseded submit — drop
        if self.app.screen is not self:
            return  # esc/closed — drop
        if message.problems:
            log = self.query_one("#wizard-path-problems", RichLog)
            log.clear()
            log.write(self._problems_header.format(n=len(message.problems)))
            for index, (location, msg) in enumerate(message.problems):
                log.write(S.SEL_TEMPLATE_PROBLEM_LINE.format(
                    n=index + 1, location=location, message=msg))
        else:
            self.dismiss()
            await self._accept(message.path, message.generation)


class WizardModal(ModalScreen):
    """The add-model / add-dataset wizard: collect, validate, gauntlet.

    Construction injects every behavior seam (RESEARCH Pattern 7):

    Args:
        kind: ``"models"`` or ``"datasets"`` — the type-aware instance.
        validator: ``(values) -> Sequence[(field_key, message)]`` — the
            09-01 collect-all validator (pre-bound to its
            ``ValidationSources`` by the caller); tests inject fakes.
        on_valid: called once with the composed candidate dict on a
            clean validation pass (the observer seam; the gauntlet
            panel itself is internal, driven by ``gauntlet_service``).
        on_import: the step-1 ``f`` fallback seam (fires only when the
            09-05 import seams are NOT injected — the legacy 09-04
            callback).
        on_export: the step-1 ``o`` fallback seam (same rule).
        prefill: an optional one-item ``{key: entry}`` custom-entry map
            (D-12: edit = delete + re-record — the 09-06 ``w`` push).
        vocabularies: injected enum vocabularies keyed by field name
            (species / Tokenizer / metric — the registry-observed and
            metric-registry sources; empty = the list renders empty and
            validation skips, the 09-01 empty-vocabulary rule).
        dir_exists: advisory path-existence probe for directory fields
            (default: the real fs, resolution mirroring 09-01).
        file_exists: advisory existence probe for split-file fields.
        gauntlet_service: the 09-02 ``GauntletService`` (or fake) — the
            panel drives its two per-leg entry points
            (``dry_run_precheck`` / ``audit_reconciliation``; per-item
            ◌→⠋→✓/✗ progression requires a service call per leg, so
            the batch ``reconcile`` is mirrored leg-for-leg here).
            ``None`` keeps the 09-04 minimal pending view.
        land: ``(kind, key, entry) -> Path`` — the 09-01 store's land
            (the ONLY write the panel performs; called exactly once per
            all-✓ entry).
        undo: ``(kind, key) -> bool`` — the 09-01 store's session undo
            behind the ``[u]`` affordance.
        import_read: ``(path) -> (doc | None, message | None)`` — the
            tolerant import-file read (pre-bound to the kind).
        import_validate: ``(doc) -> problems`` — the collect-all import
            validator (pre-bound to the kind + its collision sources).
        export_registry: ``(dest) -> (ok, diagnostic)`` — the 09-01
            verbatim registry export (pre-bound to the kind).
        has_custom_entries: ``() -> bool`` — the export empty-state
            pre-check (the flow short-circuits before asking a path).
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "request_cancel", S.WIZ_CANCEL_LABEL, show=False),
        Binding("enter", "advance", S.WIZ_NEXT_LABEL, show=False),
        Binding("b", "go_back", S.WIZ_BACK_LABEL, show=False),
        # Step-1-only affordances (D-11): declared once, the actions
        # no-op outside step 1; the real views ride the 09-05 seams with
        # the plain callbacks as the no-service fallback.
        Binding("f", "do_import", S.WIZ_IMPORT_LABEL, show=False),
        Binding("o", "do_export", S.WIZ_EXPORT_LABEL, show=False),
        # The session-undo affordance (D-08): active only in the landed
        # state (the action guards; single use per session).
        Binding("u", "undo_landed", S.GAUNTLET_UNDO_LABEL, show=False),
    ]

    def __init__(self, kind, validator, on_valid=None, on_import=None,
                 on_export=None, prefill=None, vocabularies=None,
                 dir_exists=None, file_exists=None, gauntlet_service=None,
                 land=None, undo=None, import_read=None,
                 import_validate=None, export_registry=None,
                 has_custom_entries=None, **kwargs):
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
        # The 09-05 writing-half seams (None = the legacy 09-04 views).
        self._gauntlet_service = gauntlet_service
        self._land = land
        self._undo = undo
        self._import_read = import_read
        self._import_validate = import_validate
        self._export_registry = export_registry
        self._has_custom_entries = has_custom_entries
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
        # ===== The gauntlet panel state (09-05) =====
        # The current run's id (WR-02): incremented on every launch; the
        # handlers drop every message whose id no longer matches AND
        # anything not addressed to a live gauntlet view — an abandoned
        # run can complete all-pass and still never land.
        self._run_id = 0
        self._gauntlet_mode = None      # None | "single" | "import"
        self._gauntlet_key = ""
        # (key, entry, declared_splits) in execution order (file order
        # for imports).
        self._gauntlet_queue: list = []
        # groups: {"key", "items": [...], "status": {"text","style"}}
        self._gauntlet_rows: list = []
        # The single-mode banner (landed row / failure banner) is STATE,
        # never DOM-only: a verdict or land arriving while a drill view
        # holds the DOM must survive the return recompose.
        self._gauntlet_banner = {"text": "", "style": ""}
        self._gauntlet_landed = 0
        self._undo_available = False
        self._drill_item: GauntletItem | None = None
        self._drill_row_id: str | None = None
        self._pending_import = {}  # generation -> stashed doc (WR-07)

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
        """Render the active phase: form step, report, gauntlet, drill."""
        with Vertical(id="wizard-box", classes="wizard-box"):
            if self._phase == "form":
                yield from self._compose_step()
            elif self._phase == "report":
                yield RichLog(wrap=True, id="wiz-report-log")
                yield Static(S.WIZ_REPORT_BACK_HINT,
                             id="wiz-report-hint")
            elif self._phase == "drill":
                yield RichLog(wrap=True, id="gauntlet-drill-log")
                yield Static(S.WIZ_GAUNTLET_BACK_HINT,
                             id="gauntlet-drill-hint")
            elif self._gauntlet_service is not None:
                yield from self._compose_gauntlet_panel()
            else:
                # The 09-04 minimal pending view (no service wired —
                # the composition root wires the real GauntletService).
                yield Static(S.ENV_STATE_PENDING, id="wiz-gauntlet-pending")
                yield Static(S.WIZ_GAUNTLET_BACK_HINT,
                             id="wiz-gauntlet-hint")

    def _compose_gauntlet_panel(self):
        """The gauntlet panel: grouped item rows + status lines + hints.

        Import mode renders one group per entry (its header row carries
        the entry's own gauntlet title, the adjacency-safe grouping);
        single mode's border title already names the key. Rows and
        status lines render from ``self._gauntlet_rows`` (the state is
        the source; a recompose can never lose a verdict). The entry
        rows live in a bounded scrollable region (the UI-Considerations
        gauntlet-list rule — many imported entries overflow the 80x24
        grid; the bound keeps the modal inside it with the bottom
        reachable; ``_apply_chrome`` owns the code-applied cap).
        """
        is_import = self._gauntlet_mode == "import"
        with VerticalScroll(id="gauntlet-rows"):
            for index, group in enumerate(self._gauntlet_rows):
                if is_import:
                    yield Static(S.GAUNTLET_TITLE.format(key=group["key"]),
                                 id=f"gauntlet-head-{index}")
                for item_index, row in enumerate(group["items"]):
                    yield _GauntletRow(
                        row["text"],
                        id=f"gauntlet-row-{index}-{item_index}")
                if is_import:
                    yield Static(group["status"]["text"],
                                 id=f"gauntlet-status-{index}")
        yield Static(self._gauntlet_banner["text"], id="gauntlet-banner")
        yield Static(S.GAUNTLET_UNDO_AFFORDANCE if self._undo_available
                     else "", id="gauntlet-undo")
        yield Static(f"{S.GAUNTLET_DRILL_HINT}  {S.WIZ_GAUNTLET_BACK_HINT}",
                     id="gauntlet-hint")

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
                placeholder = (S.WIZ_SPLIT_FILE_PLACEHOLDER
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
        hint = (S.WIZ_FOOTER_HINT_LAST
                if self._step == len(self._steps) - 1 else S.WIZ_FOOTER_HINT)
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
            box.border_title = S.WIZ_BORDER_TITLE.format(
                kind=KINDS[self._kind].kind_name,
                indicator=indicator,
                step=step.name,
            )
        elif self._phase == "report":
            box.border_title = S.WIZ_REPORT_TITLE.format(
                kind=KINDS[self._kind].kind_name)
        elif self._phase == "drill":
            label = self._drill_item_label()
            box.border_title = (S.GAUNTLET_DRILL_TITLE.format(item=label)
                                if label else S.GAUNTLET_TITLE.format(
                                    key=self._gauntlet_key))
        elif self._gauntlet_mode == "import":
            box.border_title = S.WIZ_IMPORT_LABEL
        elif self._gauntlet_service is not None:
            # the landed panel keeps its key even after the form clears
            box.border_title = S.GAUNTLET_TITLE.format(key=self._gauntlet_key)
        else:  # the 09-04 minimal pending view
            box.border_title = S.GAUNTLET_TITLE.format(
                key=self._values.get("key", ""))
        box.styles.width = min(
            _WIZARD_MAX_WIDTH, max(20, self.size.width - 4))
        rows = _first_or_none(self.query("#gauntlet-rows"))
        if rows is not None:
            # the entry region's scroll bound (grid minus the panel's
            # fixed chrome — recomputed on every resize like the width)
            rows.styles.height = "auto"
            rows.styles.max_height = max(
                4, self.size.height - _PANEL_CHROME_ROWS)

    def _drill_item_label(self):
        """The drilled item's label (from the panel state)."""
        if self._drill_row_id is None:
            return ""
        parts = self._drill_row_id.split("-")
        try:
            items = self._gauntlet_rows[int(parts[-2])]["items"]
            return items[int(parts[-1])]["label"]
        except (IndexError, KeyError, ValueError):
            return ""

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
            return S.WIZ_NUMERIC_HINT, "wiz-hint-bad"
        if spec.control == "path":
            if self._dir_exists(value):
                return S.WIZ_PATH_EXISTS, "wiz-check-ok"
            return S.WIZ_PATH_MISSING_ADVISORY, "wiz-check-bad"
        # splitfile: the name is checked under the collected dataset path
        dataset_path = self._values.get("Dataset_path", "")
        if not isinstance(dataset_path, str) or not dataset_path.strip():
            return "", ""
        target = str(Path(dataset_path) / value)
        if self._file_exists(target):
            return S.WIZ_PATH_EXISTS, "wiz-check-ok"
        return S.WIZ_PATH_MISSING_ADVISORY, "wiz-check-bad"

    # ===== Navigation: enter / b / esc =====

    async def action_advance(self) -> None:
        """Enter: next step; last step submits; report returns; a
        gauntlet ROW drills into its verbatim output; drill returns."""
        if self._phase == "form":
            if self._step < len(self._steps) - 1:
                self._step += 1
                await self.recompose()
                self._apply_chrome()
                self._refresh_advisories()
            else:
                await self._submit()
        elif self._phase == "drill":
            await self._show_gauntlet_panel()
        elif self._phase == "gauntlet" and self._gauntlet_service is not None:
            row = self.focused if isinstance(self.focused, _GauntletRow) \
                else None
            if row is not None:
                await self._open_drill(row)
        else:
            await self._return_to_form()

    # ===== Submit: compose, validate, report / hand off (CUST-03) =====

    async def _submit(self) -> None:
        """Step-4 enter: run the injected validator; problems render as
        the collect-all report (nothing applied), a clean pass enters
        the gauntlet phase — the real panel when the service seam is
        wired, the 09-04 minimal pending view otherwise."""
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
            if self._gauntlet_service is not None:
                await self._begin_single_gauntlet(candidate)
            else:
                await self.recompose()
                self._apply_chrome()
            if self._on_valid is not None:
                self._on_valid(candidate)

    def _write_report(self) -> None:
        """Render the numbered collect-all list (validator emission order)."""
        log = self.query_one("#wiz-report-log", RichLog)
        log.write(S.WIZ_PROBLEMS_HEADER.format(n=len(self._problems)))
        for index, (field_key, message) in enumerate(self._problems):
            log.write(S.WIZ_PROBLEM_LINE.format(
                i=index + 1,
                field_label=self._labels.get(field_key, field_key),
                problem=message,
            ))

    # ===== The gauntlet panel (CUST-04 UI, D-06/D-07/D-08 — 09-05) =====

    class GauntletItemChecking(Message):
        """One leg is starting (worker thread -> event loop).

        Carries the run id it belongs to — handlers drop messages from a
        superseded or abandoned run (WR-02).
        """

        def __init__(self, run_id: int, entry_key: str, leg: str) -> None:
            self.run_id = run_id
            self.entry_key = entry_key
            self.leg = leg
            super().__init__()

    class GauntletItemDone(Message):
        """One leg finished; carries the service's structured item.

        Carries the run id it belongs to — the worker's OS thread cannot
        be interrupted, so a cancelled run's in-flight leg can finish
        and post AFTER the new run's messages; the handlers drop it
        (WR-02) so a stale result never backfills a later row.
        """

        def __init__(self, run_id: int, item: GauntletItem) -> None:
            self.run_id = run_id
            self.item = item
            super().__init__()

    class GauntletEntryDone(Message):
        """One entry's every leg finished; carries the aggregate ok.

        The handler performs the ONLY write (the injected land seam) —
        on the event loop, keyed to the CURRENT run, so an abandoned
        run's all-✓ can never land (D-08).
        """

        def __init__(self, run_id: int, entry_key: str, ok: bool) -> None:
            self.run_id = run_id
            self.entry_key = entry_key
            self.ok = ok
            super().__init__()

    class GauntletRunDone(Message):
        """The whole run (single candidate or the whole import queue)
        finished; carries the run id (dropped when superseded)."""

        def __init__(self, run_id: int) -> None:
            self.run_id = run_id
            super().__init__()

    class ExportStateReady(Message):
        """The export empty-state probe finished OFF the event loop
        (WR-04, 09 review): ``has_custom_entries`` is a registry read —
        real file I/O the D-03 discipline routes through a worker; the
        handler toasts the empty state or opens the path prompt."""

        def __init__(self, empty: bool) -> None:
            self.empty = empty
            super().__init__()

    def _init_gauntlet_rows(self) -> None:
        """Build the panel state: one group per queued entry."""
        self._gauntlet_rows = [
            {"key": key,
             "items": [{"leg": leg, "label": label, "status": "pending",
                        "text": S.GAUNTLET_ROW_PENDING.format(item=label),
                        "item": None}
                       for leg, label in _legs_for_kind(self._kind)],
             "status": {"text": "", "style": ""}}
            for key, _entry, _declared in self._gauntlet_queue
        ]
        self._gauntlet_banner = {"text": "", "style": ""}

    async def _begin_single_gauntlet(self, candidate: dict) -> None:
        """Enter the panel for the wizard's own candidate and launch."""
        key = candidate.get("key", "")
        self._gauntlet_mode = "single"
        self._gauntlet_key = key
        self._gauntlet_queue = [(key, candidate, None)]
        self._gauntlet_landed = 0
        self._undo_available = False
        self._init_gauntlet_rows()
        await self._launch_gauntlet()

    async def _launch_gauntlet(self) -> None:
        """(Re)compose the panel view and start the exclusive worker.

        ``self._run_id`` increments HERE, at every launch — the single
        increment site; a superseded run's late messages are dropped by
        id, and any message arriving outside a live gauntlet view is
        dropped by the phase guard.
        """
        self._run_id += 1
        await self.recompose()
        self._apply_chrome()
        self._style_gauntlet_panel()
        self._gauntlet_worker()

    def _style_gauntlet_panel(self) -> None:
        """Apply row styles + initial focus (post-mount: probe-pinned).

        Every status surface re-renders FROM STATE — a verdict or land
        arriving while a drill view held the DOM survives the return.
        """
        for group_index, group in enumerate(self._gauntlet_rows):
            head = (_first_or_none(self.query(
                f"#gauntlet-head-{group_index}"))
                if self._gauntlet_mode == "import" else None)
            if head is not None:
                head.update(Text(S.GAUNTLET_TITLE.format(key=group["key"]),
                                 style=_ROW_STYLE_PASS))
            if self._gauntlet_mode == "import":
                status = _first_or_none(self.query(
                    f"#gauntlet-status-{group_index}"))
                if status is not None and group["status"]["text"]:
                    status.update(Text(group["status"]["text"],
                                       style=group["status"]["style"]))
            for item_index, row_state in enumerate(group["items"]):
                self._update_row_widget(group_index, item_index,
                                        row_state["text"],
                                        self._row_style(row_state["status"]))
        if self._gauntlet_banner["text"]:
            banner = _first_or_none(self.query("#gauntlet-banner"))
            if banner is not None:
                banner.update(Text(self._gauntlet_banner["text"],
                                   style=self._gauntlet_banner["style"]))
        restore = (_first_or_none(self.query(f"#{self._drill_row_id}"))
                   if self._drill_row_id else None)
        if restore is not None:
            restore.focus()
        else:
            # Always focus a live row: the pre-panel focus target (a form
            # Input) is gone after the recompose, and a stale focused
            # widget would swallow keys aimed at the panel (probe-pinned
            # by the import flow — esc from the panel must return).
            first = _first_or_none(self.query(_GauntletRow))
            if first is not None:
                first.focus()

    @staticmethod
    def _row_style(status):
        """The row text style for one status state."""
        if status == "pass":
            return _ROW_STYLE_PASS
        if status == "fail":
            return _ROW_STYLE_FAIL
        return _ROW_STYLE_DIM

    def _update_row_widget(self, group_index, item_index, text, style):
        """Update one row Static (state is already updated by callers)."""
        row = _first_or_none(
            self.query(f"#gauntlet-row-{group_index}-{item_index}"))
        if row is not None:  # a drill view may hold the DOM
            row.update(Text(text, style=style))

    @work(exclusive=True, thread=True, exit_on_error=False)
    def _gauntlet_worker(self) -> None:
        """Run every queued entry's legs in the worker thread (D-03).

        A plain ``def`` (an OS thread, never the event loop): each
        service call blocks here, not the UI — the console never
        freezes. Per leg: post the checking state, call, post the
        result (unconditionally — the cancelled thread's in-flight leg
        finishes and posts; the run-id drop is the handler's job, the
        exact WR-02 env-panel discipline); per entry: post the
        aggregate; per run: post the completion. The cancellation poll
        between legs/entries honors exclusive=True's cancel of a
        still-running previous launch. The panel performs NO writes and
        NO verdict computation — the service's parsed-artifact items are
        the only truth (binding constraint 5).
        """
        worker = get_current_worker()
        run_id = self._run_id  # the run this worker serves (WR-02)
        service = self._gauntlet_service
        if service is None:  # unreachable by construction (launch guard)
            return
        for entry_key, entry, declared in self._gauntlet_queue:
            if worker.is_cancelled:
                return
            ok = True
            for leg, _label in _legs_for_kind(self._kind):
                if worker.is_cancelled:
                    return
                self.post_message(
                    self.GauntletItemChecking(run_id, entry_key, leg))
                item = self._run_leg(service, leg, entry_key, entry,
                                     declared, run_id)
                self.post_message(self.GauntletItemDone(run_id, item))
                ok = ok and bool(item.ok)
            if worker.is_cancelled:
                return
            self.post_message(self.GauntletEntryDone(run_id, entry_key, ok))
        if worker.is_cancelled:
            return
        self.post_message(self.GauntletRunDone(run_id))

    def _run_leg(self, service, leg, entry_key, entry, declared, run_id):
        """Call the injected service's per-leg entry point (never here:
        verdicts come from the service's parsed artifacts)."""
        if leg == LEG_AUDIT:
            return service.audit_reconciliation(
                entry_key, entry, declared, run_id)
        return service.dry_run_precheck(
            self._kind, entry_key, entry, run_id)

    def _gauntlet_stale(self, run_id) -> bool:
        """True when a message no longer addresses a live gauntlet view
        of the CURRENT run (WR-02 id drop + the abandoned-view guard —
        an esc-then-resubmit window cannot backfill the form)."""
        return (run_id != self._run_id
                or self._phase not in ("gauntlet", "drill"))

    def _find_row(self, entry_key, leg):
        """Locate one item's (group, item) indices in the panel state."""
        for group_index, group in enumerate(self._gauntlet_rows):
            if group["key"] != entry_key:
                continue
            for item_index, row_state in enumerate(group["items"]):
                if row_state["leg"] == leg:
                    return group_index, item_index
        return None

    @staticmethod
    def _item_row_text(leg, label, item):
        """One finished item's row text (service data, never recomputed)."""
        if not item.ok:
            summary = ", ".join(item.details) or (item.raw_output or "")
            return S.GAUNTLET_ROW_FAIL.format(item=label, summary=summary)
        if leg == LEG_DRY_RUN:
            return S.GAUNTLET_ROW_DRY_RUN_PASS.format(
                cells=_detail_value(item.details, "planned_cells"))
        return S.GAUNTLET_ROW_PASS.format(
            item=label, summary=", ".join(item.details))

    # ===== Message handlers (event-loop side: rendering + the one write) =====

    def on_wizard_modal_gauntlet_item_checking(
            self, message: GauntletItemChecking) -> None:
        """Flip the in-flight row to the running state (inline fill)."""
        if self._gauntlet_stale(message.run_id):
            return
        found = self._find_row(message.entry_key, message.leg)
        if found is None:
            return
        group_index, item_index = found
        row_state = self._gauntlet_rows[group_index]["items"][item_index]
        row_state["status"] = "running"
        row_state["text"] = S.GAUNTLET_ROW_RUNNING.format(
            item=row_state["label"])
        self._update_row_widget(group_index, item_index, row_state["text"],
                                self._row_style("running"))

    def on_wizard_modal_gauntlet_item_done(
            self, message: GauntletItemDone) -> None:
        """Record the verdict and flip its row to the final glyph row."""
        if self._gauntlet_stale(message.run_id):
            return  # a superseded run's late result — dropped (WR-02)
        item = message.item
        found = self._find_row(item.name, item.leg)
        if found is None:
            return
        group_index, item_index = found
        row_state = self._gauntlet_rows[group_index]["items"][item_index]
        row_state["status"] = "pass" if item.ok else "fail"
        row_state["item"] = item
        row_state["text"] = self._item_row_text(
            row_state["leg"], row_state["label"], item)
        self._update_row_widget(group_index, item_index, row_state["text"],
                                self._row_style(row_state["status"]))

    def on_wizard_modal_gauntlet_entry_done(
            self, message: GauntletEntryDone) -> None:
        """All-✓ lands exactly once through the seam; any ✗ banners.

        This handler is the panel's ONLY write call site (the injected
        land seam — the 09-01 store's atomic write; this screen never
        touches a file). It runs keyed to the current run and a live
        gauntlet view, so an abandoned run can never land (D-08).
        """
        if self._gauntlet_stale(message.run_id):
            return
        is_import = self._gauntlet_mode == "import"
        group_index = next(
            (index for index, group in enumerate(self._gauntlet_rows)
             if group["key"] == message.entry_key), None)
        if group_index is None:
            return
        if message.ok:
            land = self._land
            if land is None:
                return  # no store seam wired — nothing can land
            entry = self._entry_for(message.entry_key)
            try:
                path = land(self._kind, message.entry_key, entry)
            except Exception as exc:  # noqa: BLE001 — the store seam's
                # failure must surface as a banner, never a crashed panel
                self._render_entry_status(
                    group_index, False, message.entry_key,
                    extra=S.SEL_TEMPLATE_WRITE_FAILED.format(error=exc),
                )
                return
            self._gauntlet_landed += 1
            landed = S.GAUNTLET_ROW_LANDED.format(
                key=message.entry_key, path=path)
            self._render_entry_status(group_index, True, message.entry_key,
                                      text=landed)
            if not is_import:
                # the success toast + the session-undo affordance (the
                # toast reuses the landed-row copy verbatim); a land is
                # one of the three form-clearing events
                self.app.notify(landed)
                self._undo_available = True
                undo = _first_or_none(self.query("#gauntlet-undo"))
                if undo is not None:
                    undo.update(S.GAUNTLET_UNDO_AFFORDANCE)
                self._reset_form()
        else:
            self._render_entry_status(group_index, False,
                                      message.entry_key)

    def on_wizard_modal_gauntlet_run_done(
            self, message: GauntletRunDone) -> None:
        """Import completion toast (any n ≥ 1 landed; failures carry
        their own banners — a zero-land import never toasts success)."""
        if self._gauntlet_stale(message.run_id):
            return
        if (self._gauntlet_mode == "import" and self._gauntlet_landed > 0):
            self.app.notify(S.GAUNTLET_IMPORTED_TOAST.format(
                n=self._gauntlet_landed,
                kind=KINDS[self._kind].kind_name))

    def _entry_for(self, entry_key):
        """The queued entry dict for one key (single mode: candidate)."""
        for key, entry, _declared in self._gauntlet_queue:
            if key == entry_key:
                return entry
        return self._candidate if self._gauntlet_mode == "single" else {}

    def _render_entry_status(self, group_index, ok, entry_key, text=None,
                             extra=""):
        """Render one entry's landed row / failure banner.

        Single mode renders the shared banner line; import mode renders
        the entry group's own status line (entry-level rollback made
        visible — earlier groups keep their landed rows). The text lands
        in STATE first (a drill view may hold the DOM — the verdict must
        survive the return recompose), then in the widget if present.
        """
        if text is None:
            text = S.GAUNTLET_BANNER_FAIL.format(key=entry_key)
        if extra:
            text = text + "\n" + extra
        style = self._row_style("pass" if ok else "fail")
        if self._gauntlet_mode == "import":
            self._gauntlet_rows[group_index]["status"] = {
                "text": text, "style": style}
            target = _first_or_none(self.query(
                f"#gauntlet-status-{group_index}"))
        else:
            self._gauntlet_banner = {"text": text, "style": style}
            target = _first_or_none(self.query("#gauntlet-banner"))
        if target is not None:
            target.update(Text(text, style=style))

    def _reset_form(self) -> None:
        """Clear the form (a successful land clears it — one of the
        three clearing events with esc-confirm and a used undo)."""
        self._values = {"quirks": {name: False
                                   for name, _, _ in QUIRK_FIELDS}}
        self._step = 0

    # ===== Drill-down (enter on a row -> verbatim subprocess output) =====

    async def _open_drill(self, row) -> None:
        """Swap to the drill view over one row's item (same modal — the
        Pitfall 9 preservation contract)."""
        parts = (row.id or "").split("-")
        try:
            group = self._gauntlet_rows[int(parts[-2])]
            item = group["items"][int(parts[-1])]["item"]
        except (IndexError, KeyError, TypeError, ValueError):
            return
        if item is None:
            return  # a pending/running row has no output yet
        self._drill_item = item
        self._drill_row_id = row.id
        self._phase = "drill"
        await self.recompose()
        self._apply_chrome()
        log = self.query_one("#gauntlet-drill-log", RichLog)
        log.styles.max_height = _DRILL_LOG_MAX_HEIGHT
        for line in (item.raw_output or "").splitlines() or [""]:
            log.write(line)  # data, verbatim — never translated

    async def _show_gauntlet_panel(self) -> None:
        """Return from the drill view to the panel (state unchanged)."""
        self._phase = "gauntlet"
        await self.recompose()
        self._apply_chrome()
        self._style_gauntlet_panel()

    # ===== Session undo (D-08: explicit, immediately-after, once) =====

    def action_undo_landed(self) -> None:
        """``u``: remove exactly the just-landed key through the seam.

        Guarded to the landed state and single-use — the affordance is
        session-scoped (gone once the panel closes) and the toast is
        the confirmation (the UI-SPEC destructive list).
        """
        if (self._phase != "gauntlet" or not self._undo_available
                or self._undo is None):
            return
        self._undo_available = False
        self._undo(self._kind, self._gauntlet_key)
        toast = S.GAUNTLET_UNDO_TOAST.format(key=self._gauntlet_key)
        self.app.notify(toast)
        undo = _first_or_none(self.query("#gauntlet-undo"))
        if undo is not None:
            undo.update("")
        # the panel's final view names the undone state honestly (state
        # first — the same drill-view survival rule as every status)
        self._gauntlet_banner = {"text": toast, "style": _ROW_STYLE_DIM}
        banner = _first_or_none(self.query("#gauntlet-banner"))
        if banner is not None:
            banner.update(Text(toast, style=_ROW_STYLE_DIM))

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
        """Esc: drill returns to the panel; report/gauntlet return to the
        form; a blank form cancels; entered values confirm through the
        destructive gate first."""
        if self._phase == "drill":
            await self._show_gauntlet_panel()
            return
        if self._phase != "form":
            # Leaving the gauntlet panel abandons any in-flight run: the
            # phase guard in ``_gauntlet_stale`` drops its late messages,
            # so an abandoned all-✓ can never land (D-08) — the operator
            # resubmits and re-gauntlets.
            await self._return_to_form()
            return
        filled = self._filled_steps()
        if filled == 0:
            self.dismiss()
            return
        self.app.push_screen(ConfirmModal(
            S.WIZ_CANCEL_CONFIRM.format(n=filled),
            on_confirm=self._abandon,
        ))

    def _abandon(self) -> None:
        """The confirm's destructive choice: discard the form."""
        self.dismiss()

    def action_do_import(self) -> None:
        """f on step 1: the D-11 file-import flow.

        With the import seams wired this pushes the import path prompt
        (collect-all validation, fail-closed conflicts report, then the
        per-entry sequential gauntlet); the plain ``on_import`` callback
        remains the no-seam fallback (the 09-04 shape).
        """
        if not (self._phase == "form" and self._step == 0):
            return
        if self._import_read is not None and self._import_validate is not None:
            self.app.push_screen(_PathPromptModal(
                title=S.WIZ_IMPORT_LABEL,
                placeholder=S.SEL_TEMPLATE_PATH_PLACEHOLDER,
                problems_header=S.GAUNTLET_IMPORT_CONFLICTS,
                validate=self._validate_import_path,
                accept=self._accept_import_path,
            ))
        elif self._on_import is not None:
            self._on_import()

    def action_do_export(self) -> None:
        """o on step 1: the D-11 registry-export flow.

        The empty state short-circuits BEFORE any path is asked (zero
        landed customs → the toast, nothing written anywhere); the probe
        itself is a registry read, so it runs in the exclusive worker
        (WR-04, 09 review — D-03: file I/O never runs on the event
        loop); otherwise the worker's report routes to the injected
        export seam (the verbatim byte copy). The plain ``on_export``
        callback is the no-seam fallback.
        """
        if not (self._phase == "form" and self._step == 0):
            return
        if (self._export_registry is not None
                and self._has_custom_entries is not None):
            self._check_export_state()
        elif self._on_export is not None:
            self._on_export()

    @work(exclusive=True, thread=True, exit_on_error=False)
    def _check_export_state(self) -> None:
        """Read the store's empty-state probe OFF the event loop (WR-04).
        The worker performs no DOM access and no writes — the verdict
        crosses back as the ``ExportStateReady`` message."""
        probe = self._has_custom_entries
        if probe is None:  # unreachable by construction (the action guard)
            return
        self.post_message(self.ExportStateReady(not probe()))

    def on_wizard_modal_export_state_ready(
            self, message: ExportStateReady) -> None:
        """The probe's verdict: the empty-state toast, or the export path
        prompt — only while the wizard is still the live screen (an esc
        between the keypress and the report drops the flow, the same
        stale-message discipline as ``_gauntlet_stale``)."""
        if self.app.screen is not self:
            return
        if message.empty:
            self.app.notify(S.GAUNTLET_EXPORT_EMPTY_TOAST)
            return
        self.app.push_screen(_PathPromptModal(
            title=S.WIZ_EXPORT_LABEL,
            placeholder=S.SEL_TEMPLATE_PATH_PLACEHOLDER,
            problems_header=S.GAUNTLET_EXPORT_PROBLEMS,
            validate=self._validate_export_path,
            accept=self._accept_export_path,
        ))

    # ===== Import flow (D-11: fail-closed collect-all -> per-entry gauntlet) =====

    def _validate_import_path(self, path, generation):
        """The path prompt's validation seam: read tolerantly, then the
        collect-all import validator. ANY problem (including the
        read failure itself) renders as numbered report lines and
        nothing merges; a clean pass stashes the document for accept —
        keyed by the submit GENERATION (WR-07, 09 review: overlapping
        validations write separate slots, so an accept can never
        consume another submission's document — the old single slot
        raced last-writer-wins)."""
        read = self._import_read
        validate = self._import_validate
        if read is None or validate is None:
            return []  # unreachable by construction (the action guards)
        doc, read_error = read(path)
        if read_error is not None:
            self._pending_import.pop(generation, None)
            return [("", read_error)]
        problems = list(validate(doc) or [])
        self._pending_import[generation] = None if problems else doc
        return problems

    async def _accept_import_path(self, path, generation) -> None:
        """A clean import file enters the grouped per-entry gauntlet —
        consuming THIS submission's stashed document (generation-keyed,
        WR-07: a superseded accept cannot cross-consume)."""
        doc = self._pending_import.pop(generation, None)
        if not isinstance(doc, dict):
            return
        await self._begin_import_gauntlet(doc)

    async def _begin_import_gauntlet(self, doc) -> None:
        """Queue the imported entries in FILE order and launch.

        Imported entries may carry declared ``Train``/``Dev``/``Test``
        counts — extracted verbatim as the audit leg's declared side
        (data pass-through, never computed here); the wizard's own
        candidate declares none (derive-at-composition downstream).
        """
        queue = []
        for key, entry in doc.items():
            declared = None
            if isinstance(entry, dict):
                counts = {field: entry[field] for field in
                          ("Train", "Dev", "Test") if field in entry}
                declared = counts or None
            queue.append((key, entry, declared))
        self._gauntlet_mode = "import"
        self._gauntlet_key = ""
        self._gauntlet_queue = queue
        self._gauntlet_landed = 0
        self._undo_available = False
        self._drill_row_id = None
        self._init_gauntlet_rows()
        self._phase = "gauntlet"
        await self._launch_gauntlet()

    # ===== Export flow (D-11: the registry file IS the share unit) =====

    def _validate_export_path(self, path, generation):
        """Run the export through the seam; any failure renders as a
        write-failure problem line (nothing at the destination). The
        generation parameter is the shared prompt-seam shape (WR-07) —
        the export lane stashes nothing, so it is unused here."""
        export = self._export_registry
        if export is None:
            return []  # unreachable by construction (the action guards)
        try:
            ok, diagnostic = export(path)
        except OSError as exc:
            return [("", S.SEL_TEMPLATE_WRITE_FAILED.format(error=exc))]
        if ok:
            return None
        return [("", S.SEL_TEMPLATE_WRITE_FAILED.format(
            error=diagnostic or ""))]

    async def _accept_export_path(self, path, generation) -> None:
        """Toast the exported path (the copy already happened; the
        generation parameter is the shared prompt-seam shape — WR-07)."""
        self.app.notify(S.GAUNTLET_EXPORTED_TOAST.format(path=path))

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
