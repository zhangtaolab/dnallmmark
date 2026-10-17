"""
run_config — the run-config screen (Phase 11, 11-06; menu slot 4).

The operator's composition surface: OWN model/dataset pickers (the
slot-2 interaction grammar over the registries — D-01 ruling B: slot-2
state is NEVER read), the full CFG-01 params pane, the CFG-02/D-14 dirs
section, the live same-source dry-run preview line (CFG-03/D-05), the
``[p]`` detail modal, the terraform-style launch-confirmation pipeline (LNC-01..03)
and the RadioSet choice modals. The app-level ``q`` intercept
(ExitModal, D-06) lives in ``tui/app.py``.

Contract (locked decisions):

- PRESENTATION ONLY (the ``tui/screens/`` tier contract): enumeration,
  verdicts, phrase checks, validation, and persistence all live behind
  the two injected service Protocols — widgets render and post intent.
  The gate never trusts the preview line's cache: every gate step
  recomputes through the services (the staleness bug class designed
  out, T-11-06-02).
- D-01: the pickers own their marks COMPLETELY — marks live in the
  run-spec itself (``spec.models`` / ``spec.tasks``), persist through
  the service to XDG (atomic), and reload at mount. The selection
  screen's mark sets are never read here.
- WR-02: every worker carries its own group and run id — preview,
  mount-load, and the four gate stages never cancel each other, and a
  superseded worker's late post drops in the handler.
- WR-06: every async modal push checks ``app.below_minimum_grid`` — no
  chrome may open over the min-size guard.
- The enter-key pin (UI-checker fix 2): ``enter`` on the picker or an
  unfocused surface opens the launch confirmation; any focused Input consumes its own
  Enter — typing can never launch (Pilot-asserted). The picker subclass
  shadows the inherited OptionList ``enter`` binding with the gate
  action; choice rows shadow it with the RadioSet action.
- T-11-06-01/04: the E2' live-enter wiring reads the SERVICE
  ``phrase_matches`` verdict per keystroke (the widget holds no
  matching logic), and every gate I/O stage (enumeration, env kernels,
  the spawn itself) runs in a thread worker — the console never
  freezes.

I18N-01: zero Chinese literals in this module — every operator-facing
string renders through ``tui/strings.py`` constants (grep-enforced);
registry keys, argv, reasons, and paths stay data, verbatim.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Protocol

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Checkbox,
    DirectoryTree,
    Footer,
    Input,
    Label,
    RadioButton,
    RadioSet,
    RichLog,
    SelectionList,
    Static,
    Tree,
)
from textual.widgets.selection_list import Selection

from tui import strings as S
from tui.screens.nav import BottomBar, TopMenuBar
from tui.screens.selection import LaunchConfirmModal
from tui.services import custom_entries as custom_entries_service
from tui.services import registries as registries_service
from tui.services import run_config as run_config_service
from tui.services import selection as selection_service
from tui.services import sweep_launcher as sweep_launcher_module
from tui.services.run_config import (
    PARAM_CURVE,
    PARAM_EBS,
    PARAM_EPOCHS,
    PARAM_SEEDS,
    PreviewResult,
    RunSpec,
)
from tui.services.sweep_launcher import (
    EnvPreflight,
    GateRefusal,
    GateSummary,
    LaunchOutcome,
)

if TYPE_CHECKING:
    from textual import getters

    from tui.app import DnallmMarkTui

#: The canonical fairness-subset default (auto-default 7 — the repo's
#: E2' fairness file; shown dim when the toggle is off).
DEFAULT_SUBSET_PATH = "pipeline/eval_subsets.json"

#: The width threshold for the 80-col degradations (the UI-SPEC
#: responsive rules: params labels shorten below the design grid).
_NARROW_WIDTH = 100

_STYLE_DIM = "$text-muted"
_STYLE_WARN = "$warning"


# =====================================================================
# Service data + Protocols (the constructor-injection seam)
# =====================================================================


@dataclass(frozen=True)
class PickerEntries:
    """One picker snapshot — the registries + custom status (pure data).

    Attributes:
        model_entries: canonical model entries (overlay-merged officials
            + enabled customs, then disabled customs appended).
        dataset_entries: canonical dataset entries (same composition).
        custom_status: key -> ``{"custom": bool, "enabled": bool}`` for
            every landed custom entry (official keys absent — the badge,
            never position, marks customs).
    """

    model_entries: tuple[dict, ...] = ()
    dataset_entries: tuple[dict, ...] = ()
    custom_status: dict[str, dict] = field(default_factory=dict)


class RunConfigServiceProtocol(Protocol):
    """The run-config service surface the screen consumes.

    The real ``RunConfigBackend`` and the tier-2 Pilot fakes both
    conform structurally — no registry read, XDG write, or pipeline
    source read ever executes in a faked Pilot run (D-03).
    """

    def picker_entries(self) -> PickerEntries:
        """The registries + custom-status snapshot (worker-read seam)."""

    def load_state(self) -> RunSpec:
        """The XDG-persisted spec (tolerant whole-default load)."""

    def save_state(self, spec: RunSpec) -> None:
        """Persist the spec atomically (D-01)."""

    def save_directory_defaults(self, spec: RunSpec) -> Path:
        """Write the five dir values to directories.json; return the
        path (F4W-03, 261014-f4w)."""

    def preview(self, spec: RunSpec) -> PreviewResult:
        """The same-source dry-run preview (D-05 — never re-derived)."""

    def parse_params(self, raw: dict) -> tuple[dict, tuple]:
        """Collect-all parse of the params pane's raw strings."""

    def resolve_dirs(self, spec: RunSpec) -> Any:
        """Project the spec's dirs to their display/argv forms (D-14)."""

    def probe_ineligible(self) -> frozenset:
        """The frozen probe-ineligible names (read-source, 9 today)."""

    def path_state(self, value: "str | None") -> str:
        """'exists' | 'missing' | 'unset' — one path's advisory state."""

    def parse_filter(self, query: str) -> Any:
        """Parse a filter query (the 08-05 grammar)."""

    def apply_filter(self, entries: Sequence[dict], parsed: Any) -> list:
        """Apply parsed terms to entries (pure, order-preserving)."""

    def compose_argv(self, spec: RunSpec) -> list:
        """The run_sweep LIST argv (verbatim, the [p] modal renders it)."""

    def expected_phrase(self, output_root: str) -> str:
        """The E2' typed phrase this output root demands."""

    def phrase_matches(self, typed: str, output_root: str) -> bool:
        """The exact-match verdict (D-07 — the service tier owns it)."""


class RunConfigBackend:
    """The real run-config service adapter — delegation glue only.

    The semantics stay in the tested services: the 11-02 ``run_config``
    module owns preview/validation/persistence/argv, the 08-05
    ``selection`` module owns the filter grammar (the interaction
    grammar is reused — NEVER the slot-2 state, D-01), and the 08-04
    ``registries`` + custom_entries services own the picker entries
    (the SelectionBackend composition minus presence).
    """

    def picker_entries(self) -> PickerEntries:
        """The registries + every landed custom (the picker rows)."""
        model_entries: list[dict] = list(
            registries_service.load_model_entries())
        dataset_entries: list[dict] = list(
            registries_service.load_dataset_entries())
        custom_status: dict[str, dict] = {}
        for kind, entries in (
            ("models", model_entries),
            ("datasets", dataset_entries),
        ):
            management, _management_error = (
                custom_entries_service.read_entries(kind))
            merged_keys = {entry["key"] for entry in entries}
            for key, entry in management.items():
                if not isinstance(entry, dict):
                    continue  # never a badge target (the loader's shape)
                custom_status[key] = {
                    "custom": True,
                    "enabled": entry.get("enabled") is not False,
                }
                if key not in merged_keys:
                    # the disabled customs the overlay loader hides —
                    # appended so the picker renders every landed entry
                    entries.append({"key": key, "card": entry})
        return PickerEntries(
            model_entries=tuple(model_entries),
            dataset_entries=tuple(dataset_entries),
            custom_status=custom_status,
        )

    def load_state(self) -> RunSpec:
        return run_config_service.load_state()

    def save_state(self, spec: RunSpec) -> None:
        run_config_service.save_state(spec)

    def save_directory_defaults(self, spec: RunSpec) -> Path:
        """Thin delegation to the tested service (F4W-03) — the write
        stays in the tier the save seam's tests pin."""
        return run_config_service.save_directory_defaults(spec)

    def preview(self, spec: RunSpec) -> PreviewResult:
        return run_config_service.preview(spec)

    def parse_params(self, raw: dict) -> tuple[dict, tuple]:
        return run_config_service.parse_params(raw)

    def resolve_dirs(self, spec: RunSpec) -> Any:
        return run_config_service.resolve_dirs(spec)

    def probe_ineligible(self) -> frozenset:
        return run_config_service.probe_ineligible()

    def path_state(self, value: "str | None") -> str:
        """The path advisory: exists / missing / unset (a stat, off-loop
        in the preview worker; nonexistent roots stay advisory-only —
        the sweep mkdirs, D-14)."""
        if not value:
            return "unset"
        return "exists" if Path(value.strip()).exists() else "missing"

    def parse_filter(self, query: str) -> Any:
        return selection_service.parse_filter_query(query)

    def apply_filter(self, entries: Sequence[dict], parsed: Any) -> list:
        return selection_service.apply_filter(entries, parsed.terms)

    def compose_argv(self, spec: RunSpec) -> list:
        return run_config_service.compose_argv(spec)

    def expected_phrase(self, output_root: str) -> str:
        return run_config_service.expected_phrase(output_root)

    def phrase_matches(self, typed: str, output_root: str) -> bool:
        return run_config_service.phrase_matches(typed, output_root)


class LauncherServiceProtocol(Protocol):
    """The launcher service surface the screen consumes (11-03)."""

    def env_preflight(self, kernels: Any = None) -> EnvPreflight:
        """The D-08 preflight over the frozen phase-8 face."""

    def gate_confirm_data(self, spec: RunSpec) -> GateSummary:
        """The FRESH confirm-gate summary (never screen state)."""

    def launch_spec(self, spec: RunSpec,
                    phrase: "str | None" = None) -> Any:
        """The structurally gated launch (refusal before any spawn)."""

    def launch_from_failures(self, failures_path, seeds, output_root,
                             peft: str = "none",
                             config_variant: str = "none",
                             phrase: "str | None" = None) -> Any:
        """The D-11 from-failures launch (the monitor's gated re-run;
        CR-01: an E2'-class effective matrix demands the phrase)."""

    def phrase_matches(self, typed: str, output_root: str) -> bool:
        """The exact-match E2' phrase verdict (the shared launcher
        satisfies the monitor's re-prompt seam too — one object, two
        protocol faces)."""

    def kill_sweep(self, root: str) -> str:
        """SIGTERM the process group (D-06 exit triple, k path)."""

    def detach(self, root: str) -> str:
        """Drop the handle, the sweep survives (D-06 default)."""

    def live_sweeps(self) -> tuple:
        """The live roots (the ExitModal predicate)."""

    def tee_path_for(self, root: str) -> "str | None":
        """One live root's tee path (None = the CLI-launched state)."""


class LauncherBackend:
    """The real launcher adapter: module-level preflight/confirm legs
    over the APP-OWNED shared ``SweepLauncher`` instance (one registry —
    the ExitModal and the 11-07 monitor read the same live sweeps)."""

    def __init__(self, launcher: Any = None):
        self._launcher = (launcher if launcher is not None
                          else sweep_launcher_module.SweepLauncher())

    def env_preflight(self, kernels: Any = None) -> EnvPreflight:
        return sweep_launcher_module.env_preflight(kernels)

    def gate_confirm_data(self, spec: RunSpec) -> GateSummary:
        return sweep_launcher_module.gate_confirm_data(spec)

    def launch_spec(self, spec: RunSpec,
                    phrase: "str | None" = None) -> Any:
        return self._launcher.launch_spec(spec, phrase)

    def launch_from_failures(self, failures_path, seeds, output_root,
                             peft="none", config_variant="none",
                             phrase=None) -> Any:
        return self._launcher.launch_from_failures(
            failures_path, seeds, output_root,
            peft=peft, config_variant=config_variant, phrase=phrase)

    def phrase_matches(self, typed, output_root) -> bool:
        """Delegates to the service tier (the modal's live verdict)."""
        return run_config_service.phrase_matches(typed, output_root)

    def kill_sweep(self, root: str) -> str:
        return self._launcher.kill_sweep(root)

    def detach(self, root: str) -> str:
        return self._launcher.detach(root)

    def live_sweeps(self) -> tuple:
        return self._launcher.live_sweeps()

    def tee_path_for(self, root: str) -> "str | None":
        return self._launcher.tee_path_for(root)

    def single_gpu_launch_blocked(self) -> "tuple[str, ...] | None":
        """The EHC-3 pre-check seam over the shared launcher (the
        tolerant getattr both directions: the wrapped launcher may
        predate the method — a fake or older double reads as never
        blocked, the 11-03 precedent)."""
        blocked = getattr(
            self._launcher, "single_gpu_launch_blocked", None)
        return blocked() if blocked is not None else None


def _problem_line(code: str, detail: object) -> str:
    """One machine problem as its copy row (data, never re-worded).

    Known composition/parse codes map to their landed constants; any
    other code (the official-keys diagnostic, future codes) renders the
    code + detail verbatim — data discipline.
    """
    if code == "empty_selection":
        return S.CFG_EMPTY_SELECTION_PROBLEM
    if code == "seeds_invalid":
        return S.CFG_SEEDS_INVALID_PROBLEM.format(value=detail)
    if code == "curve_invalid":
        return S.CFG_CURVE_INVALID_PROBLEM.format(value=detail)
    if code == "probe_ineligible":
        return S.CFG_PROBE_INELIGIBLE_PROBLEM.format(model=detail)
    if code == "variant_peft":
        return S.CFG_COMPOSITION_PROBLEM
    if code == "output_root_invalid":
        return S.CFG_OUTPUT_ROOT_PROBLEM.format(value=detail)
    if code == "single_gpu_busy":
        # EHC-3 (261015-ehc): {roots} carries the joined live roots
        return S.LNC_SINGLE_GPU_BLOCKED.format(roots=detail)
    return f"{code}: {detail}"


def _numbered_problems(problems: Sequence[tuple]) -> list[str]:
    """The collect-all numbered problem list (the gauntlet shape)."""
    lines = [S.CFG_PREVIEW_PROBLEMS.format(n=len(problems))]
    lines.extend(
        S.CFG_PREVIEW_PROBLEM_LINE.format(i=index + 1,
                                        problem=_problem_line(code, detail))
        for index, (code, detail) in enumerate(problems)
    )
    return lines


# =====================================================================
# Picker widgets (the slot-2 interaction grammar, own state — D-01)
# =====================================================================


class PickerList(SelectionList):
    """The slot-4 picker: the SelectionList with the enter-key pin.

    The inherited OptionList ``enter`` binding (select) is SHADOWED by
    the gate action — enter on the picker opens the launch confirmation (the
    UI-checker fix 2 pin; only space toggles a mark).

    Disabled customs stay CURSOR-REACHABLE (native ``disabled=`` rows
    are skipped by OptionList navigation, which would silently hide
    them); the toggle chokepoint below warns instead — never silent,
    never marked (the SEL-01 boundary, keyboard AND mouse paths — both
    funnel through ``OptionSelected``).
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "open_gate", show=False),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._row_keys: list[str] = []
        self._row_disabled: list[bool] = []

    def action_open_gate(self) -> None:
        """Delegate to the screen's gate action — unprefixed actions do
        NOT resolve across the widget->screen boundary on 8.2.8 (a
        missing widget action falls through to the SAME screen binding;
        probe-pinned in this plan's development). The getattr guard
        narrows the generic Screen type (ty)."""
        handler = getattr(self.screen, "action_open_gate", None)
        if handler is not None:
            handler()

    def set_rows(self, keys: Sequence[str], prompts: Sequence[Text],
                 marked: Sequence[bool], disabled: Sequence[bool],
                 anchor_key: "str | None" = None) -> None:
        """Rebuild the rows, preserving the cursor where it still fits.

        ``anchor_key`` (the toggle paths — the row set is IDENTICAL
        before and after) additionally restores BOTH the highlighted row
        (pinned to the registry KEY, not the index) and the EXACT
        pre-rebuild scroll offset. WHY: textual 8.2.8's ``clear_options``
        resets the scroll and ``watch_highlighted`` force-scrolls the
        restored cursor to a viewport EDGE (``scroll_to_region(
        force=True)``), so the full rebuild visibly jumps the list on
        every space toggle; the captured offset is re-applied after the
        restore (and re-asserted once the layout refresh settles — the
        final authority over the watcher's edge snap). Without an
        anchor (or when the key left the row set) today's index-clamp
        behavior stands exactly, scroll untouched.
        """
        self._row_keys = list(keys)
        self._row_disabled = list(disabled)
        highlighted = self.highlighted
        prev_y = self.scroll_offset.y
        self.clear_options()
        rows = [
            Selection(prompt, key, initial_state=mark)
            for prompt, key, mark
            in zip(prompts, keys, marked, strict=True)
        ]
        if rows:
            self.add_options(rows)
            if anchor_key is not None and anchor_key in self._row_keys:
                # the highlighted restore fires the 8.2.8 edge-snap
                # watcher; the explicit scroll_to back to the captured
                # offset is the final authority (synchronous on
                # ScrollView), the call_after_refresh follow-up
                # re-asserts it after add_options' pending layout
                # refresh settles.
                self.highlighted = self._row_keys.index(anchor_key)
                self.scroll_to(y=prev_y, animate=False, immediate=True)
                self.call_after_refresh(
                    lambda: self.scroll_to(
                        y=prev_y, animate=False, immediate=True))
            else:
                self.highlighted = min(
                    highlighted if highlighted is not None else 0,
                    len(rows) - 1)

    def key_at(self, index: "int | None") -> "str | None":
        """The registry key at a row index (None when out of range)."""
        if index is None or not 0 <= index < len(self._row_keys):
            return None
        return self._row_keys[index]

    def disabled_at(self, index: "int | None") -> bool:
        """True when the row at the index is a disabled custom."""
        return (index is not None
                and 0 <= index < len(self._row_disabled)
                and self._row_disabled[index])

    def action_select(self) -> None:
        """The toggle chokepoint: a disabled custom WARNS, never marks.

        Both interaction paths funnel here (the keyboard space binding
        and ``_on_click``), so one override covers both. NOTE: private
        ``_on_*`` message handlers are MRO-dispatched on 8.2.8 (an
        override + ``super()`` call DOUBLE-fires) — the action layer is
        the safe seam (probe-pinned in this plan's development).
        """
        index = self.highlighted
        if self.disabled_at(index):
            key = self.key_at(index)
            if key is not None:
                self.post_message(DisabledMarkRequested(self, key))
            return
        super().action_select()


class DisabledMarkRequested(Message):
    """Space on a disabled custom row — the screen warns, never marks."""

    def __init__(self, picker: PickerList, key: str) -> None:
        self.picker = picker
        self.key = key
        super().__init__()


class ChoiceRow(Static, can_focus=True):
    """A focusable params choice row: the value + ▾ (enter opens the
    RadioSet modal — the preset-modal family)."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "pick_choice", show=False),
    ]

    def __init__(self, field: str, value: str = "", **kwargs) -> None:
        super().__init__("", **kwargs)
        self.field = field
        self.set_value(value)

    def action_pick_choice(self) -> None:
        """Delegate to the screen's choice action (the 8.2.8 action
        boundary — see PickerList.action_open_gate)."""
        handler = getattr(self.screen, "action_pick_choice", None)
        if handler is not None:
            handler()

    def set_value(self, value: str) -> None:
        """Render one choice value with the dim ▾ affordance."""
        self.update(Text.assemble(
            Text(value), Text(" ▾", style="dim")))


# =====================================================================
# Modals (ModalScreen — app/screen bindings blocked while open)
# =====================================================================


class _PickerReturnModal(ModalScreen):
    """Slot-4 modal base: dismiss returns focus to ``#cfg-picker``.

    Delta B (Phase 12, 12-03; 11-UAT advisory #1 — rules B1/B4):
    Textual restores the PRE-MODAL focused widget on modal pop, and the
    gate pipeline pushes its modals from async worker messages — so the
    operator can legitimately be typing in a params Input when the
    modal lands, and the restored focus is that Input: digits 1-6 then
    get eaten by the Input and navigation deadlocks (recovery was
    restart). ONE shared hook at dismiss time covers every path — the
    escape bindings all route through ``Screen.action_dismiss`` ->
    ``self.dismiss()`` and the explicit ``dismiss()`` call sites inherit
    it (probe-verified mechanics, textual 8.2.8; the screen below is
    captured BEFORE ``super().dismiss()`` because 8.2.8's ``pop_screen``
    pops the stack synchronously). The filter Input's Enter path
    (``run_config.py``:1389) is the precedent — this is that behavior
    at the modal boundary.
    """

    def dismiss(self, result: "Any | None" = None):
        # delta B: capture the screen below FIRST — super().dismiss()
        # pops it from the stack synchronously (textual 8.2.8).
        screen_stack = self.app.screen_stack
        below = (screen_stack[-2]
                 if len(screen_stack) > 1 and screen_stack[-1] is self
                 else None)
        awaitable = super().dismiss(result)
        if below is not None:
            try:
                picker = below.query_one("#cfg-picker", PickerList)
                picker.call_after_refresh(picker.focus)
            except Exception:  # noqa: BLE001, S110 — wrong screen below (never slot 4): the
                # designed blind-except isolation (the run_finetune.py
                # per-line-noqa precedent) — plain pop, never crash
                pass
        return awaitable


class PreviewModal(_PickerReturnModal):
    """The [p] dry-run preview modal: summary + same-source note + the LIST
    argv VERBATIM + the numbered problems (data, never restated)."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", S.APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, lines: "tuple[str, ...]", **kwargs):
        super().__init__(**kwargs)
        self._lines = tuple(lines)

    def compose(self) -> ComposeResult:
        with Vertical(id="cfg-preview-box", classes="modal-box"):
            yield RichLog(wrap=True, id="cfg-preview-log")
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#cfg-preview-box", Vertical).border_title = (
            S.CFG_PREVIEW_MODAL_TITLE)
        log = self.query_one("#cfg-preview-log", RichLog)
        for line in self._lines:
            log.write(line)


class ProblemsModal(_PickerReturnModal):
    """The gate's numbered-problems refusal — launch blocked, nothing
    else opens (LNC-01; the problems are the service's machine list
    rendered through the copy mapping)."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", S.APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, problems: "tuple[tuple, ...]", **kwargs):
        super().__init__(**kwargs)
        self._problems = tuple(problems)

    def compose(self) -> ComposeResult:
        with Vertical(id="cfg-problems-box", classes="modal-box"):
            yield RichLog(wrap=True, id="cfg-problems-log")
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#cfg-problems-box", Vertical).border_title = (
            S.LNC_GATE_TITLE)
        log = self.query_one("#cfg-problems-log", RichLog)
        for line in _numbered_problems(self._problems):
            log.write(line)


class EnvBlockModal(_PickerReturnModal):
    """The env-block refusal (D-08): the failing kernel names, the
    reasons VERBATIM in a bounded RichLog, and the [1] route hint."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", S.APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, failed_kernels: "tuple[str, ...]",
                 reasons: "tuple[str, ...]", **kwargs):
        super().__init__(**kwargs)
        self._failed_kernels = tuple(failed_kernels)
        self._reasons = tuple(reasons)

    def compose(self) -> ComposeResult:
        with Vertical(id="cfg-envblock-box", classes="modal-box"):
            yield Static(S.ENV_QUICK_CHECK_FAIL.format(
                kernel_names=", ".join(self._failed_kernels)),
                id="cfg-envblock-header")
            yield RichLog(wrap=True, id="cfg-envblock-log")
            yield Static(S.LNC_ENV_BLOCKED_HINT, id="cfg-envblock-hint")
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#cfg-envblock-box", Vertical).border_title = (
            S.LNC_GATE_TITLE)
        log = self.query_one("#cfg-envblock-log", RichLog)
        for line in self._reasons:
            log.write(line)


class E2PhraseModal(_PickerReturnModal):
    """The E2' typed-phrase escalation (D-02/D-07/LNC-03; reworked for
    EHC-2, 261015-ehc ruling 2 — the phrase stays double insurance ON
    TOP of the y-confirm).

    The live mismatch/match indicator flips per keystroke through the
    INJECTED service verdict (``matches`` — the widget holds no
    matching logic, T-11-06-01). ``enter`` NEVER launches: on the
    exact-match verdict it ADVANCES to the y-ready state (blur the
    input — while the input holds focus, ``y`` and ``n`` type into it,
    which is correct; the blur is what arms the modal's ``y``/``n``
    bindings — the indicator stays on the [Y]/[N] wording); a mismatch
    enter stays the no-op pin. ``y`` then launches, carrying the typed
    phrase; ``n``/``esc`` cancel unchanged (UX-6, 261016-poa).
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "confirm_phrase", show=False),
        Binding("y", "confirm_phrase_y", show=False),
        Binding("n", "dismiss", show=False),
        Binding("escape", "dismiss", S.APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, dirname: str,
                 matches: "Callable[[str], bool]",
                 on_confirm: "Callable[[str], None]", **kwargs):
        super().__init__(**kwargs)
        self._dirname = dirname
        self._matches = matches
        self._on_confirm = on_confirm
        self._matched = False

    def compose(self) -> ComposeResult:
        with Vertical(id="cfg-e2-box", classes="modal-box"):
            yield Static(S.LNC_E2_WARNING, classes="cfg-e2-warning")
            yield Static(S.LNC_E2_AUTH_NOTE, classes="cfg-e2-warning")
            yield Static(S.LNC_E2_TYPE_PROMPT.format(dirname=self._dirname))
            yield Input(id="cfg-e2-input")
            yield Static(S.LNC_E2_MISMATCH.format(dirname=self._dirname),
                         id="cfg-e2-indicator")
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#cfg-e2-box", Vertical).border_title = S.LNC_GATE_TITLE
        self.query_one("#cfg-e2-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Every keystroke re-reads the SERVICE verdict (never local)."""
        if event.input.id != "cfg-e2-input":
            return
        self._matched = bool(self._matches(event.value))
        indicator = self.query_one("#cfg-e2-indicator", Static)
        if self._matched:
            # DNR-3 (261017-dnr): the MATCHED indicator's [Y]/[N] tokens
            # render BOLD via the Rich Text API (the 261017-cdr pattern —
            # Text content is never markup-parsed; highlight_words mutates
            # IN PLACE and returns an int, never chained). The y/n
            # bindings below STAY show=False BY DESIGN: they only arm
            # after the matched-enter blur — a visible y keycap while the
            # Input holds focus would advertise a key that types into
            # the Input; the armed-state bold copy carries the affordance
            # (the 261017 brief's simplicity ruling). The mismatch branch
            # stays a plain string.
            matched = Text(S.LNC_E2_MATCH_OK)
            matched.highlight_words(("[Y]", "[N]"), style="bold")
            indicator.update(matched)
            indicator.set_classes(["cfg-e2-match"])
        else:
            indicator.update(S.LNC_E2_MISMATCH.format(dirname=self._dirname))
            indicator.set_classes(["cfg-e2-mismatch"])

    def _advance_to_y_ready(self) -> None:
        """The matched-enter ADVANCE: blur the input (arming the modal's
        ``y``/``n`` bindings — textual 8.2.8's ``set_focus(None)`` clears
        focused-widget key consumption) and keep the indicator on the
        [Y]/[N] wording. Never dismisses, never confirms."""
        self.set_focus(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """The Input's own enter — advance on the matched verdict, no-op
        on a mismatch (typing can never launch; neither can enter)."""
        if event.input.id != "cfg-e2-input" or not self._matched:
            return  # a mismatch enter is a no-op (the pin)
        self._advance_to_y_ready()

    def action_confirm_phrase(self) -> None:
        """The modal-level enter binding — the same advance/no-op pair
        (enter can NEVER launch from this modal, EHC-2)."""
        if not self._matched:
            return
        self._advance_to_y_ready()

    def action_confirm_phrase_y(self) -> None:
        """``y`` — the one key that launches, live only once the input is
        blurred (armed by the matched-enter advance); a mismatch leaves
        it inert."""
        if not self._matched:
            return
        input_widget = self.query_one("#cfg-e2-input", Input)
        self.dismiss()
        self._on_confirm(input_widget.value)


class ChoiceModal(_PickerReturnModal):
    """The RadioSet choice modal (PEFT / variant — the preset-modal family:
    the first toggle applies the choice and closes)."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", S.APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, title: str, options: "tuple[str, ...]",
                 current: str,
                 on_pick: "Callable[[str], None]", **kwargs):
        super().__init__(**kwargs)
        self._title = title
        self._options = tuple(options)
        self._current = current
        self._on_pick = on_pick

    def compose(self) -> ComposeResult:
        with Vertical(id="cfg-choice-box", classes="modal-box"):
            yield RadioSet(*[
                RadioButton(option, option == self._current, id=option)
                for option in self._options
            ])
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#cfg-choice-box", Vertical).border_title = self._title
        self.query_one(RadioSet).focus()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """The first press applies the choice and closes (k9s-quick)."""
        value = str(event.pressed.id or "")
        self.dismiss()
        self._on_pick(value)


#: The confirm modal's pair-list cap (UX-5, 261016-poa): at most this
#: many model+dataset rows render before the LNC_GATE_PAIRS_MORE total
#: line — with the formula line + the confirm row the modal stays
#: inside the design grid even for a full-matrix plan (T-poa-02).
_GATE_PAIR_CAP = 12


class _GateConfirmModal(_PickerReturnModal, LaunchConfirmModal):
    """The launch confirmation's confirm over the shared slot-4 base
    (delta B, B4's one-shared-helper ruling; UX-5, 261016-poa): the
    local subclass adds the picker-return dismiss for this screen's
    push site AND the planned-pair task list — the actual model+dataset
    rows the sweep will run, SERVICE-DERIVED (``GateSummary.pairs``,
    never UI-computed), rendered in a bounded RichLog (the EnvBlockModal
    pattern): every pair within the cap, else the first
    ``_GATE_PAIR_CAP`` plus the LNC_GATE_PAIRS_MORE total line. Since
    261015-ehc (EHC-2) the base is ``LaunchConfirmModal`` — ``y``
    starts the sweep, ``n``/``esc`` cancel, ``enter`` lands on the
    documented no-op. The RichLog takes no focus-stealing measures: it
    has no y/n/enter bindings of its own, so the confirm keys fall
    through to the modal even from a clicked/focused log (Pilot-pinned).
    """

    def __init__(self, pairs: "tuple[tuple[str, str], ...] | None" = None,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self._pairs = tuple(pairs) if pairs is not None else ()

    def compose(self) -> ComposeResult:
        # DNR-1 (261017-dnr): the confirm line's [Y]/[y]/[N]/[n] tokens
        # render BOLD via the Rich Text API (the 261017-cdr
        # QuitConfirmModal pattern; the same 4-token tuple the
        # LaunchConfirmModal compose override carries — this subclass
        # owns its compose, so the wrap lands HERE). highlight_words
        # mutates the Text IN PLACE and returns the count (cdr-probed
        # rich text.py:639 -> int) — never chained, two-step only. The
        # Static keeps its #cfg-gate-message id; the pair-list RichLog,
        # cap logic, and on_mount stay untouched.
        message = Text(self._message)
        message.highlight_words(("[Y]", "[y]", "[N]", "[n]"), style="bold")
        with Vertical(id="cfg-gate-box", classes="modal-box"):
            yield Static(message, id="cfg-gate-message")
            yield RichLog(wrap=True, id="cfg-gate-log")
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#cfg-gate-box", Vertical).border_title = (
            S.LNC_GATE_TITLE)
        log = self.query_one("#cfg-gate-log", RichLog)
        for model, task in self._pairs[:_GATE_PAIR_CAP]:
            log.write(S.LNC_GATE_PAIR_LINE.format(model=model, task=task))
        if len(self._pairs) > _GATE_PAIR_CAP:
            log.write(S.LNC_GATE_PAIRS_MORE.format(
                pairs=len(self._pairs)))


class _DirsOnlyTree(DirectoryTree):
    """A DirectoryTree restricted to DIRECTORIES (F4W-05).

    Probe-pinned on textual 8.2.8: the directories-only mechanism is
    the overridable ``filter_paths`` METHOD — a seam called over every
    loaded directory's entries BEFORE nodes are added (there is no
    ``filter_directories`` on this version) — so files never appear as
    nodes and file-node selection is structurally unreachable. Enter
    dispatches ``Tree.action_select_cursor`` -> ``NodeSelected``, which
    BOTH the name-based ``_on_tree_node_selected`` handler and Tree's
    ``@on(NodeSelected)`` auto-expand toggle receive; ``auto_expand =
    False`` neutralizes the toggle (my expand + its toggle would
    collapse what enter opened), and the override below REPLACES the
    base handler — deliberately NO ``super()`` call (the probe-pinned
    MRO double-fire trap: override + super fires the base handler
    twice, posting DirectorySelected twice).
    """

    def __init__(self, path: "str | Path", **kwargs) -> None:
        super().__init__(path, **kwargs)
        # Kill Tree's @on(NodeSelected) toggle — this class owns the
        # enter semantics (collapsed descends, expanded selects).
        self.auto_expand = False

    def filter_paths(self, paths):
        """Directories only: files are filtered out before any node is
        added (zero new dependencies — core DirectoryTree)."""
        return (path for path in paths if path.is_dir())

    async def _on_tree_node_selected(
            self, event: "Tree.NodeSelected") -> None:
        """The enter semantics: a COLLAPSED node expands (descend — the
        children load through DirectoryTree's own NodeExpanded loader);
        an ALREADY-EXPANDED node selects (the native DirectorySelected
        event the modal's fill handler consumes).

        ``prevent_default()`` is load-bearing (probe-pinned on 8.2.8):
        textual dispatches the name-based private handler for EVERY
        class in the MRO that defines one — without it,
        DirectoryTree's own ``_on_tree_node_selected`` ALSO fires and
        posts DirectorySelected on the descend path (the modal closes
        on the very first enter). It also neutralizes Tree's
        ``@on(NodeSelected)`` auto-expand toggle, so ``auto_expand =
        False`` stays a redundant belt-and-braces guard.
        """
        event.stop()
        event.prevent_default()
        node = event.node
        if node.data is None:
            return
        if not node.is_expanded and node.allow_expand:
            node.expand()
        else:
            self.post_message(
                DirectoryTree.DirectorySelected(node, node.data.path))


class DirPickerModal(ModalScreen):
    """The ctrl+o directory picker (F4W-05): a directories-only
    DirectoryTree rooted per the fallback chain, over the FOCUSED dir
    input.

    NOT the ``_PickerReturnModal`` base — that base refocuses
    ``#cfg-picker``; this modal must return focus to the ORIGIN INPUT
    (a local dismiss override in the delta-B spirit, input-targeted).
    BOTH selection paths — the tree's native ``DirectorySelected``
    (enter on an already-expanded node; the probe-pinned event class on
    8.2.8) and the dedicated [f] select key — funnel into ONE
    fill-and-close handler: the programmatic value set fires
    ``Input.Changed``, so the screen's existing
    ``on_input_changed -> _refresh_preview`` validation/persistence
    path runs UNCHANGED (no bespoke pick validation, no bypass); esc
    cancels with the value untouched. DirectoryTree loads children
    asynchronously — Pilot tests pause for the first children to mount.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", S.APP_MODAL_BACK_LABEL),
        Binding("f", "select_dir", S.CFG_DIR_PICKER_SELECT_LABEL),
    ]

    def __init__(self, origin_input: Input, field_label: str,
                 root: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self._origin_input = origin_input
        self._field_label = field_label
        self._root = root

    def compose(self) -> ComposeResult:
        with Vertical(id="cfg-dirpick-box", classes="modal-box"):
            yield _DirsOnlyTree(str(self._root), id="cfg-dirpick-tree")
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#cfg-dirpick-box", Vertical).border_title = (
            S.CFG_DIR_PICKER_TITLE.format(field=self._field_label))
        self.query_one("#cfg-dirpick-tree", _DirsOnlyTree).focus()

    def dismiss(self, result: "Any | None" = None):
        """The input-targeted delta-B hook: capture the ORIGIN INPUT
        before ``super().dismiss()`` (8.2.8 pops the stack
        synchronously), then refocus it after — the esc path and both
        fill paths share this hook."""
        origin = self._origin_input
        awaitable = super().dismiss(result)
        origin.call_after_refresh(origin.focus)
        return awaitable

    def on_directory_tree_directory_selected(
            self, event: DirectoryTree.DirectorySelected) -> None:
        """The native selection path: enter on an already-expanded node
        (and the root)."""
        event.stop()
        self._fill_and_close(event.path)

    def action_select_dir(self) -> None:
        """[f] — select the cursor's directory (the dedicated key that
        works on a collapsed node's row too, where enter descends)."""
        tree = self.query_one("#cfg-dirpick-tree", _DirsOnlyTree)
        node = tree.cursor_node
        if node is None or node.data is None:
            return
        self._fill_and_close(node.data.path)

    def _fill_and_close(self, path: Path) -> None:
        """The ONE fill-and-close handler: dismiss, then set the origin
        input's value to the picked directory's ABSOLUTE path — the
        programmatic set fires ``Input.Changed``, so the unchanged
        preview/persist validation path runs (the no-bypass proof is
        the persisted state file carrying the picked root)."""
        origin = self._origin_input
        self.dismiss()
        origin.value = str(Path(path).resolve())


# =====================================================================
# The screen
# =====================================================================


class RunConfigScreen(Screen):
    """The run-config screen: own pickers + params + dirs + preview +
    the launch-confirmation pipeline over the two injected services."""

    # D-13 slot 4 (the top-menu active-slot marker the nav bar reads).
    NAV_SLOT: ClassVar[int] = 4

    if TYPE_CHECKING:
        # Narrows MessagePump's ``App[object]`` to the composition root
        # (the selection-screen idiom — no runtime import of tui.app).
        app = getters.app(DnallmMarkTui)

    # The D-15 bottom-bar vocabulary in declaration order (the wireframe
    # order), then the hidden pair: escape (clear filter) + the nav
    # digits (plain per-screen bindings routed to the app's nav action —
    # never priority, Pattern 2; the top bar carries the digit labels).
    # 261014-f4w inserts [s] save-defaults and ctrl+o dir-picker after
    # [p]: the declaration order is the bottom-bar/help order.
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("space", "toggle_mark", S.SEL_MARK_LABEL),
        Binding("m", "switch_kind", S.SEL_SWITCH_LABEL),
        Binding("slash", "focus_filter", S.SEL_FILTER_KEY_LABEL,
                key_display="/"),
        Binding("p", "preview_modal", S.CFG_PREVIEW_MODAL_TITLE),
        Binding("s", "save_directory_defaults", S.CFG_SAVE_DEFAULTS_LABEL),
        # BINDING-CHOICE RATIONALE (probe-pinned on textual 8.2.8): a
        # BARE letter cannot open the picker — the open condition is a
        # focused dir Input, and a focused Input consumes printable keys
        # (a bare "o" would type the letter; same for "s" inside an
        # Input, the p/m precedent), while ctrl+o is NOT an Input
        # binding on 8.2.8 and therefore falls through to the screen
        # exactly when the operator is inside a dir field (probed: an
        # app-level ctrl+o binding fires with an Input focused, the
        # Input's value untouched).
        Binding("ctrl+o", "open_dir_picker", S.CFG_DIR_PICKER_LABEL),
        Binding("enter", "open_gate", S.LNC_GATE_TITLE),
        Binding("escape", "clear_filter", show=False),
        Binding("1", "app.nav(1)", S.NAV_LABEL_ENV, show=False),
        Binding("2", "app.nav(2)", S.NAV_LABEL_SELECTION, show=False),
        Binding("3", "app.nav(3)", S.NAV_LABEL_DATA, show=False),
        Binding("4", "app.nav(4)", S.NAV_LABEL_RUN_CONFIG, show=False),
        Binding("5", "app.nav(5)", S.NAV_LABEL_MONITOR, show=False),
        Binding("6", "app.nav(6)", S.NAV_LABEL_ABOUT, show=False),
    ]

    # ===== Message classes (worker thread -> event loop, WR-02) =====

    class Loaded(Message):
        """The mount snapshot arrived (spec + picker entries)."""

        def __init__(self, spec: RunSpec, entries: PickerEntries) -> None:
            self.spec = spec
            self.entries = entries
            super().__init__()

    class PreviewLine(Message):
        """One preview recompute (save + preview + advisories + probe
        intersection), tagged with its run id — handlers drop stale."""

        def __init__(self, result: PreviewResult,
                     parse_problems: tuple, dir_states: dict,
                     probe_hits: tuple, run_id: int) -> None:
            self.result = result
            self.parse_problems = parse_problems
            self.dir_states = dir_states
            self.probe_hits = probe_hits
            self.run_id = run_id
            super().__init__()

    class GateEnumerationDone(Message):
        """The gate's FRESH enumeration answered (T-11-06-02)."""

        def __init__(self, result: PreviewResult,
                     parse_problems: tuple, run_id: int) -> None:
            self.result = result
            self.parse_problems = parse_problems
            self.run_id = run_id
            super().__init__()

    class EnvPreflightDone(Message):
        """The gate's env preflight answered (D-08)."""

        def __init__(self, verdict: EnvPreflight, run_id: int) -> None:
            self.verdict = verdict
            self.run_id = run_id
            super().__init__()

    class GateSummaryReady(Message):
        """The fresh confirm-gate summary arrived (never screen state)."""

        def __init__(self, summary: GateSummary, run_id: int) -> None:
            self.summary = summary
            self.run_id = run_id
            super().__init__()

    class LaunchFinished(Message):
        """One gated launch attempt finished (outcome or refusal)."""

        def __init__(self, outcome: Any, summary: "GateSummary | None",
                     run_id: int) -> None:
            self.outcome = outcome
            self.summary = summary
            self.run_id = run_id
            super().__init__()

    class GateWorkerError(Message):
        """A gate/mount worker RAISED (WR-03, phase-11 review): the
        failure is surfaced (error toast) and the pre-modal gate flag
        released — a worker exception must never wedge the gate or die
        as a silent no-op (the confirm-then-crash class).

        ``run_id`` is the dispatching worker's id (None for the mount
        load, which has no id space — always surfaced).

        IN-02 (08 review, fix batch 261017-klw): ``scope`` names the id
        space the run_id belongs to — ``'stage'`` (the
        enumeration/preflight/confirm-data workers) compares against
        ``_gate_stage_id``, ``'launch'`` (the launch worker) against
        ``_gate_launch_id``; None keeps the run_id-None mount-worker
        always-surface semantics. The two counters increment
        independently from 1, so an untagged either-counter comparison
        lets a superseded stage error whose id numerically equals the
        CURRENT launch id surface a spurious launch-failed toast — the
        scope tag restores exactly-one-counter comparison. Internal
        discriminator, NOT user copy."""

        def __init__(self, error: str,
                     run_id: "int | None" = None,
                     scope: "str | None" = None) -> None:
            self.error = error
            self.run_id = run_id
            self.scope = scope
            super().__init__()

    # ===== construction =====

    def __init__(self,
                 run_config_service: "RunConfigServiceProtocol | None" = None,
                 launcher_service: "LauncherServiceProtocol | None" = None,
                 **kwargs):
        super().__init__(**kwargs)
        self._run_service: RunConfigServiceProtocol = (
            run_config_service if run_config_service is not None
            else RunConfigBackend())
        self._launcher: LauncherServiceProtocol = (
            launcher_service if launcher_service is not None
            else LauncherBackend())
        self._entries = PickerEntries()
        self._spec = RunSpec(models=(), tasks=())
        self._subset_on = False
        self._picker_kind = "models"
        self._filter_query = ""
        # per-worker run ids (WR-02)
        self._preview_run_id = 0
        self._gate_stage_id = 0
        self._gate_launch_id = 0
        # gate bookkeeping (the re-entrancy guard spans the pre-modal
        # stages only — every modal push or terminal state releases it)
        self._gate_active = False
        self._gate_parse_problems: tuple = ()
        self._gate_summary: GateSummary | None = None
        self._last_preview: PreviewResult | None = None
        self._last_parse_problems: tuple = ()
        self._last_probe_hits: tuple = ()

    # ===== compose / mount =====

    def compose(self) -> ComposeResult:
        """The screen frame: nav bars, the title bar, the two-column
        split (picker | params, full-width rules — borders stay
        reserved for modals), the 1-row preview line, the bottom bar."""
        yield TopMenuBar()
        with Horizontal(id="cfg-title-bar"):
            yield Label(S.CFG_SCREEN_TITLE, id="cfg-screen-title")
            yield Label("", id="cfg-status-line")
        with Horizontal(id="cfg-columns"):
            with Vertical(id="cfg-picker-col"):
                yield Label(
                    S.CFG_PICKER_MODELS.format(n=0, total=0),
                    id="cfg-picker-title")
                with Horizontal(id="cfg-filter-bar"):
                    yield Label(S.SEL_FILTER_LABEL, id="cfg-filter-label")
                    yield Input(placeholder=S.SEL_FILTER_PLACEHOLDER,
                                id="cfg-filter", compact=True)
                    yield Label("", id="cfg-filter-count")
                yield PickerList(id="cfg-picker")
            with VerticalScroll(id="cfg-params-col"):
                yield Label(S.CFG_PARAMS_TITLE, id="cfg-params-title")
                with Horizontal(classes="cfg-param-row"):
                    yield Label(S.CFG_FIELD_SEEDS,
                                id="cfg-label-seeds",
                                classes="cfg-param-label")
                    # compact=True on every height-1-row Input (the
                    # selection-filter precedent): a default bordered
                    # Input is height 3, and the height-1 row clips it
                    # to its top border — the value row renders
                    # invisible (the 11-UAT empty-bar bug, 12-03 Rule 1).
                    yield Input(value="42,43,44", id="cfg-input-seeds",
                                classes="cfg-param-input", compact=True)
                with Horizontal(classes="cfg-param-row"):
                    yield Label(S.CFG_FIELD_PEFT, id="cfg-label-peft",
                                classes="cfg-param-label")
                    yield ChoiceRow("peft", "none", id="cfg-value-peft",
                                    classes="cfg-choice-value")
                yield Label("", id="cfg-hint-peft", classes="cfg-hint")
                with Horizontal(classes="cfg-param-row"):
                    yield Label(S.CFG_FIELD_VARIANT, id="cfg-label-variant",
                                classes="cfg-param-label")
                    yield ChoiceRow("variant", "none", id="cfg-value-variant",
                                    classes="cfg-choice-value")
                yield Label("", id="cfg-hint-variant-alias",
                            classes="cfg-hint")
                yield Label("", id="cfg-hint-variant-head",
                            classes="cfg-hint")
                yield Label("", id="cfg-hint-variant-probe",
                            classes="cfg-hint")
                with Horizontal(classes="cfg-param-row"):
                    yield Label(S.CFG_FIELD_CURVE, id="cfg-label-curve",
                                classes="cfg-param-label")
                    yield Input(value="", id="cfg-input-curve",
                                classes="cfg-param-input", compact=True)
                with Horizontal(classes="cfg-param-row"):
                    yield Label(S.CFG_FIELD_SUBSET, id="cfg-label-subset",
                                classes="cfg-param-label")
                    yield Checkbox(value=False, id="cfg-subset-toggle",
                                   classes="cfg-subset-toggle")
                    yield Static("", id="cfg-subset-value",
                                 classes="cfg-param-value")
                subset_path = Input(
                    value=DEFAULT_SUBSET_PATH, id="cfg-input-subset",
                    classes="cfg-param-input")
                subset_path.display = False
                yield subset_path
                yield Label("", id="cfg-adv-subset", classes="cfg-adv")
                with Horizontal(classes="cfg-param-row"):
                    yield Label(S.CFG_FIELD_EPOCHS, id="cfg-label-epochs",
                                classes="cfg-param-label")
                    yield Input(value="", id="cfg-input-epochs",
                                classes="cfg-param-input", compact=True)
                with Horizontal(classes="cfg-param-row"):
                    yield Label(S.CFG_FIELD_EBS, id="cfg-label-ebs",
                                classes="cfg-param-label")
                    yield Input(value="", id="cfg-input-ebs",
                                classes="cfg-param-input", compact=True)
                yield Label(S.CFG_DIRS_TITLE, id="cfg-dirs-title",
                            classes="cfg-section-title")
                with Horizontal(classes="cfg-param-row"):
                    yield Label(S.CFG_FIELD_OUTPUT_ROOT,
                                id="cfg-label-output-root",
                                classes="cfg-param-label")
                    yield Input(value="./finetuned",
                                id="cfg-input-output-root",
                                classes="cfg-param-input", compact=True)
                yield Label("", id="cfg-adv-output-root", classes="cfg-adv")
                with Horizontal(classes="cfg-param-row"):
                    yield Label(S.CFG_FIELD_DATASET_ROOT,
                                id="cfg-label-dataset-root",
                                classes="cfg-param-label")
                    # The legacy "./datasets" display default retired
                    # with D-19 (261014-c2l): the dataset root is a LIVE
                    # --dataset_root flag now, so the field defaults
                    # empty with its prompt hint.
                    yield Input(
                        value="", placeholder=S.CFG_DATASET_ROOT_DEFAULT,
                        id="cfg-input-dataset-root",
                        classes="cfg-param-input", compact=True)
                yield Label("", id="cfg-adv-dataset-root", classes="cfg-adv")
                with Horizontal(classes="cfg-param-row"):
                    yield Label(S.CFG_FIELD_MODEL_ROOT,
                                id="cfg-label-model-root",
                                classes="cfg-param-label")
                    # compact=True on the height-1-row Input (the 12-03
                    # Rule-1 discipline — see the seeds-row note above).
                    yield Input(
                        value="", placeholder=S.CFG_MODEL_ROOT_DEFAULT,
                        id="cfg-input-model-root",
                        classes="cfg-param-input", compact=True)
                yield Label("", id="cfg-adv-model-root", classes="cfg-adv")
                with Horizontal(classes="cfg-param-row"):
                    yield Label(S.CFG_FIELD_CACHE, id="cfg-label-cache",
                                classes="cfg-param-label")
                    yield Input(value="", placeholder=S.CFG_CACHE_DEFAULT,
                                id="cfg-input-cache",
                                classes="cfg-param-input", compact=True)
                yield Label("", id="cfg-adv-cache", classes="cfg-adv")
                with Horizontal(classes="cfg-param-row"):
                    yield Label(S.CFG_FIELD_LOG_DIR,
                                id="cfg-label-log-dir",
                                classes="cfg-param-label")
                    # compact=True on the height-1-row Input (the 12-03
                    # Rule-1 discipline — see the seeds-row note above).
                    yield Input(
                        value="", placeholder=S.CFG_LOG_DIR_DEFAULT,
                        id="cfg-input-log-dir",
                        classes="cfg-param-input", compact=True)
                yield Label("", id="cfg-adv-log-dir", classes="cfg-adv")
                # The dirs section's closing dim hint (F4W-03): the
                # restore-defaults copy for the [s] save action.
                yield Label(S.CFG_SAVE_DEFAULTS_HINT,
                            id="cfg-hint-save-defaults",
                            classes="cfg-hint")
        yield Label("", id="cfg-preview-line")
        # UX-4 (261016-poa): the persistent dim hint below the preview —
        # the enter/Y/N affordances are hidden bindings otherwise; the
        # existing .cfg-hint class carries the dim height-1 row styling.
        yield Label(S.CFG_GATE_HINT, id="cfg-gate-hint", classes="cfg-hint")
        yield BottomBar()

    def on_mount(self) -> None:
        """Load the persisted spec + picker entries off the event loop."""
        self._apply_width_mode()
        self._load()

    def on_resize(self) -> None:
        """Re-derive the width mode + re-truncate the picker prompts
        (no fixed dimensions in code — the resize contract)."""
        self._apply_width_mode()
        if self._entries.model_entries or self._entries.dataset_entries:
            self._render_picker()

    # ===== the mount read worker (D-03) =====

    @work(exclusive=True, thread=True, group="cfg-load")
    def _load(self) -> None:
        try:
            spec = self._run_service.load_state()
            entries = self._run_service.picker_entries()
        except Exception as exc:  # noqa: BLE001 — WR-03: surfaced, never
            # a silently blank screen (registry OSError / overlay faults)
            self.post_message(self.GateWorkerError(_exc_text(exc)))
            return
        self.post_message(self.Loaded(spec, entries))

    def on_run_config_screen_loaded(self, message: Loaded) -> None:
        self._spec = message.spec
        self._entries = message.entries
        self._sanitize_disabled_custom_marks()
        self._subset_on = message.spec.subset_file is not None
        subset_input = self.query_one("#cfg-input-subset", Input)
        subset_input.value = (message.spec.subset_file
                              or DEFAULT_SUBSET_PATH)
        subset_input.display = self._subset_on
        for input_id, value in (
            ("#cfg-input-seeds",
             ",".join(str(seed) for seed in message.spec.seeds)),
            ("#cfg-input-curve", ",".join(
                format(fraction, "g")
                for fraction in message.spec.curve_fractions)),
            ("#cfg-input-epochs",
             (str(message.spec.num_train_epochs)
              if message.spec.num_train_epochs is not None else "")),
            ("#cfg-input-ebs",
             (str(message.spec.effective_batch_size)
              if message.spec.effective_batch_size is not None else "")),
            ("#cfg-input-output-root", message.spec.output_root),
            ("#cfg-input-dataset-root",
             message.spec.dataset_root or ""),
            ("#cfg-input-model-root",
             message.spec.model_root or ""),
            ("#cfg-input-log-dir", message.spec.log_dir or ""),
            ("#cfg-input-cache", message.spec.cache_dir or ""),
        ):
            self.query_one(input_id, Input).value = value
        self.query_one("#cfg-value-peft", ChoiceRow).set_value(
            message.spec.peft)
        self.query_one("#cfg-value-variant", ChoiceRow).set_value(
            message.spec.config_variant)
        self.query_one("#cfg-subset-toggle", Checkbox).value = self._subset_on
        self._render_counts()
        self._render_subset_row()
        self._render_picker()
        self.query_one("#cfg-picker", PickerList).focus()
        self._refresh_preview()

    def _sanitize_disabled_custom_marks(self) -> None:
        """WR-07 (phase-12 review): drop marked-then-disabled customs
        from the loaded spec at mount.

        The picker suppresses the visual mark on disabled rows, and both
        mark paths refuse them — so a spec still carrying one (marked in
        a previous session, disabled in the management overlay since)
        rendered the row UNMARKED while the status line, the preview,
        and the launch-confirmation enumeration all counted and launched it, and
        the operator could not unmark it from the UI. Sanitizing here
        makes the spec agree with the render; the first preview-worker
        save then persists the sanitized spec (the XDG state
        self-heals). Enabled customs are untouched; official keys never
        appear in ``custom_status``."""
        disabled = frozenset(
            key for key, status in self._entries.custom_status.items()
            if status.get("custom")
            and not status.get("enabled", True))
        if not disabled:
            return
        models = tuple(
            model for model in self._spec.models if model not in disabled)
        tasks = tuple(
            task for task in self._spec.tasks if task not in disabled)
        if (models, tasks) != (self._spec.models, self._spec.tasks):
            self._spec = replace(self._spec, models=models, tasks=tasks)

    # ===== the preview worker (save + preview + advisories, WR-02) =====

    def _refresh_preview(self) -> None:
        """Bump the run id and recompute through the worker (the save
        rides the same worker: XDG I/O off the event loop, newest write
        wins — the exclusive group cancels any in-flight predecessor)."""
        spec, parse_problems = self._compose_spec()
        self._preview_run_id += 1
        self._run_preview(spec, parse_problems, self._preview_run_id)

    @work(exclusive=True, thread=True, group="cfg-preview")
    def _run_preview(self, spec: RunSpec, parse_problems: tuple,
                     run_id: int) -> None:
        try:
            self._run_service.save_state(spec)
            result = self._run_service.preview(spec)
            dir_states = {
                "output-root": self._run_service.path_state(spec.output_root),
                "dataset-root": self._run_service.path_state(
                    spec.dataset_root or ""),
                "model-root": self._run_service.path_state(
                    spec.model_root or ""),
                "log-dir": self._run_service.path_state(
                    spec.log_dir or ""),
                "cache": self._run_service.path_state(spec.cache_dir or ""),
                "subset": self._run_service.path_state(
                    spec.subset_file if spec.subset_file else ""),
            }
            probe_hits: tuple = ()
            if spec.config_variant == "probe":
                frozen = self._run_service.probe_ineligible()
                probe_hits = tuple(sorted(
                    key for key in self._picker_keys("models")
                    if key in frozen))
        except Exception:  # noqa: BLE001 — WR-03, the tolerant live-
            # refresh surface: the previous preview line stands (the
            # monitor-worker precedent); the same fault resurfaces at
            # the next gate attempt through the WR-03-wrapped gate
            # workers, never a per-keystroke toast flood.
            return
        self.post_message(self.PreviewLine(
            result, parse_problems, dir_states, probe_hits, run_id))

    def on_run_config_screen_preview_line(self, message: PreviewLine) -> None:
        if message.run_id != self._preview_run_id:
            return  # a superseded recompute's late post (WR-02)
        self._last_preview = message.result
        self._last_parse_problems = message.parse_problems
        self._last_probe_hits = message.probe_hits
        self._render_preview_line()
        self._render_hints(message.probe_hits)
        self._render_dir_advisories(message.dir_states)

    def _render_preview_line(self) -> None:
        """The 1-row preview line: the counts, the curve variant, or the
        inline-truncated problems header (the numbered list lives in
        the [p] modal)."""
        line = self.query_one("#cfg-preview-line", Label)
        result = self._last_preview
        if result is None:
            line.update("")
            line.set_classes([])
            return
        problems = tuple(self._last_parse_problems) + tuple(result.problems)
        if problems:
            line.update(S.CFG_PREVIEW_PROBLEMS.format(n=len(problems)))
            line.set_classes(["cfg-preview-problem"])
            return
        if result.fractions_count:
            text = S.CFG_PREVIEW_LINE_CURVE.format(
                models=result.models_count, tasks=result.tasks_count,
                seeds=result.seeds_count, fractions=result.fractions_count,
                cells=result.cells_count)
        else:
            text = S.CFG_PREVIEW_LINE.format(
                models=result.models_count, tasks=result.tasks_count,
                seeds=result.seeds_count, cells=result.cells_count)
        line.update(text)
        line.set_classes([])

    # ===== pickers (the slot-2 grammar over OWN state, D-01) =====

    def _current_entries(self) -> "tuple[tuple[dict, ...], str]":
        """(entries, kind) for the visible picker kind."""
        if self._picker_kind == "models":
            return tuple(self._entries.model_entries), "models"
        return tuple(self._entries.dataset_entries), "datasets"

    def _picker_keys(self, kind: str) -> "tuple[str, ...]":
        entries = (self._entries.model_entries if kind == "models"
                   else self._entries.dataset_entries)
        return tuple(str(entry["key"]) for entry in entries)

    def _render_picker(self, anchor_key: "str | None" = None) -> None:
        entries, kind = self._current_entries()
        picker = self.query_one("#cfg-picker", PickerList)
        marked_set = (set(self._spec.models) if kind == "models"
                      else set(self._spec.tasks))
        filtered = self._filtered_entries(entries)
        # in-item truncation at the column width (the 68-char-key
        # lesson: full keys stay available through the [p] argv)
        budget = max(10, (picker.size.width or 60) - 8)
        keys: list[str] = []
        prompts: list[Text] = []
        marked: list[bool] = []
        disabled: list[bool] = []
        for entry in filtered:
            key = str(entry["key"])
            status = self._entries.custom_status.get(key)
            is_custom = bool(status and status.get("custom"))
            is_disabled = bool(
                status and status.get("custom")
                and not status.get("enabled", True))
            segments: list[Text] = []
            if kind == "models" and is_custom:
                segments.append(Text(
                    f"{S.SEL_CUSTOM_BADGE} ", style="dim"))
            segments.append(Text(key))
            if is_disabled:
                segments.append(Text(S.SEL_DISABLED_SUFFIX, style="dim"))
            prompts.append(_truncate_text(
                Text.assemble(*segments), budget))
            keys.append(key)
            marked.append(key in marked_set and not is_disabled)
            disabled.append(is_disabled)
        picker.set_rows(keys, prompts, marked, disabled,
                        anchor_key=anchor_key)
        self._render_counts()
        self._render_filter_count(len(filtered), len(entries))

    def _filtered_entries(self, entries: "tuple[dict, ...]") -> list:
        """The 08-05 grammar over the canonical entries (the shared
        interaction grammar — never the slot-2 STATE, D-01)."""
        if not self._filter_query:
            return list(entries)
        try:
            parsed = self._run_service.parse_filter(self._filter_query)
            return list(self._run_service.apply_filter(entries, parsed))
        except Exception:  # noqa: BLE001 — a broken grammar never crashes
            return list(entries)

    def _render_filter_count(self, shown: int, total: int) -> None:
        self.query_one("#cfg-filter-count", Label).update(
            S.SEL_FILTER_COUNT.format(n=shown, total=total))

    def _render_counts(self) -> None:
        """The status line + the picker title (zero-one-many counts)."""
        self.query_one("#cfg-status-line", Label).update(
            S.CFG_STATUS_LINE.format(
                n=len(self._spec.models),
                models_total=len(self._entries.model_entries),
                m=len(self._spec.tasks),
                tasks_total=len(self._entries.dataset_entries)))
        if self._picker_kind == "models":
            self.query_one("#cfg-picker-title", Label).update(
                S.CFG_PICKER_MODELS.format(
                    n=len(self._spec.models),
                    total=len(self._entries.model_entries)))
        else:
            self.query_one("#cfg-picker-title", Label).update(
                S.CFG_PICKER_DATASETS.format(
                    n=len(self._spec.tasks),
                    total=len(self._entries.dataset_entries)))

    # ===== params pane (CFG-01 exhaustive) =====

    def _text_value(self, input_id: str) -> str:
        return self.query_one(input_id, Input).value.strip()

    def _compose_spec(self) -> "tuple[RunSpec, tuple]":
        """Compose the CURRENT spec from the widgets (event-loop side
        only) — collect-all parse problems ride along; an invalid field
        contributes no partial (the last-valid value governs) and never
        persists."""
        raw = {
            PARAM_SEEDS: self._text_value("#cfg-input-seeds") or None,
            PARAM_CURVE: self._text_value("#cfg-input-curve") or None,
            PARAM_EPOCHS: self._text_value("#cfg-input-epochs") or None,
            PARAM_EBS: self._text_value("#cfg-input-ebs") or None,
        }
        partials, problems = self._run_service.parse_params(raw)
        subset_file = None
        if self._subset_on:
            subset_file = (self._text_value("#cfg-input-subset")
                           or DEFAULT_SUBSET_PATH)
        kwargs: dict[str, Any] = {
            "subset_file": subset_file,
            "output_root": (self._text_value("#cfg-input-output-root")
                            or run_config_service.DEFAULT_OUTPUT_ROOT),
            "dataset_root": self._text_value("#cfg-input-dataset-root") or None,
            "model_root": self._text_value("#cfg-input-model-root") or None,
            "log_dir": self._text_value("#cfg-input-log-dir") or None,
            "cache_dir": self._text_value("#cfg-input-cache") or None,
        }
        kwargs.update(partials)
        spec = replace(self._spec, **kwargs)
        if not problems:
            self._spec = spec
        return spec, problems

    def _render_hints(self, probe_hits: "tuple[str, ...]") -> None:
        """The derived dim hint lines under their fields."""
        first_model = (self._spec.models[0] if self._spec.models
                       else S.CFG_VALUE_ABSENT)
        peft_hint = self.query_one("#cfg-hint-peft", Label)
        if self._spec.peft != "none":
            peft_hint.update(S.CFG_PEFT_ALIAS_PREVIEW.format(
                model=first_model, mode=self._spec.peft))
            peft_hint.display = True
        else:
            peft_hint.display = False
        alias = self.query_one("#cfg-hint-variant-alias", Label)
        head = self.query_one("#cfg-hint-variant-head", Label)
        probe = self.query_one("#cfg-hint-variant-probe", Label)
        variant = self._spec.config_variant
        if variant != "none":
            alias.update(S.CFG_VARIANT_ALIAS_PREVIEW.format(
                model=first_model, variant=variant))
            alias.display = True
        else:
            alias.display = False
        if variant == "head":
            head.update(S.CFG_VARIANT_HEAD_NOTE)
            head.display = True
        else:
            head.display = False
        if variant == "probe" and probe_hits:
            probe.update(S.CFG_VARIANT_PROBE_HINT.format(
                models=", ".join(probe_hits)))
            probe.display = True
        else:
            probe.display = False

    def _render_subset_row(self) -> None:
        """The off(default)/on(path) value copy pair (both shapes live
        in ``tui/strings.py`` — the I18N-01 single home, WR-08)."""
        path = (self._text_value("#cfg-input-subset")
                if self._subset_on else DEFAULT_SUBSET_PATH)
        if self._subset_on:
            text = S.CFG_SUBSET_ON.format(path=path)
        else:
            text = S.CFG_SUBSET_OFF_WITH_PATH.format(path=path)
        self.query_one("#cfg-subset-value", Static).update(
            Text(text, style=_STYLE_DIM if not self._subset_on else ""))

    def _render_dir_advisories(self, dir_states: dict) -> None:
        """The wizard advisories: exists / missing; unset renders
        nothing (an advisory is only meaningful for a set path)."""
        for state_key, adv_id in (
            ("output-root", "#cfg-adv-output-root"),
            ("dataset-root", "#cfg-adv-dataset-root"),
            ("model-root", "#cfg-adv-model-root"),
            ("log-dir", "#cfg-adv-log-dir"),
            ("cache", "#cfg-adv-cache"),
            ("subset", "#cfg-adv-subset"),
        ):
            label = self.query_one(adv_id, Label)
            state = dir_states.get(state_key, "unset")
            if state == "exists":
                label.update(Text(S.WIZ_PATH_EXISTS, style="$success"))
                label.display = True
            elif state == "missing":
                label.update(Text(S.WIZ_PATH_MISSING_ADVISORY,
                                  style="$error"))
                label.display = True
            else:
                label.display = False

    def _apply_width_mode(self) -> None:
        """The 80-col degradations: short labels + the narrow label
        column below the design grid (deterministic, re-derived on
        resize)."""
        narrow = self.size.width < _NARROW_WIDTH
        params = self.query_one("#cfg-params-col", VerticalScroll)
        params.set_classes(["cfg-narrow"] if narrow else ["cfg-wide"])
        self.query_one("#cfg-label-ebs", Label).update(
            S.CFG_FIELD_EBS_SHORT if narrow else S.CFG_FIELD_EBS)
        self.query_one("#cfg-dirs-title", Label).update(
            S.CFG_DIRS_TITLE_SHORT if narrow else S.CFG_DIRS_TITLE)

    # ===== event handlers (event-loop side: render + intent) =====

    def on_selection_list_selection_toggled(
            self, event: SelectionList.SelectionToggled) -> None:
        """space marked/unmarked a row — the spec's own sets carry the
        marks (D-01); persist + preview through the worker."""
        if event.selection_list.id != "cfg-picker":
            return
        key = str(event.selection.value)
        entries, kind = self._current_entries()
        known = {str(entry["key"]) for entry in entries}
        if key not in known:
            return  # a stale row from a superseded rebuild
        if kind == "models":
            marks = set(self._spec.models)
            marks.symmetric_difference_update({key})
            self._apply_spec_change(models=tuple(marks),
                                    picker_anchor=key)
        else:
            marks = set(self._spec.tasks)
            marks.symmetric_difference_update({key})
            self._apply_spec_change(tasks=tuple(marks),
                                    picker_anchor=key)

    def on_disabled_mark_requested(
            self, message: DisabledMarkRequested) -> None:
        """A disabled custom can never mark — the inherited warning."""
        self.app.notify(
            S.SEL_DISABLED_MARK_WARNING.format(key=message.key),
            severity="warning")

    def on_input_changed(self, event: Input.Changed) -> None:
        """The filter drives the list live; every other Input is a
        param/dir change — persist + preview through the worker."""
        if event.input.id == "cfg-filter":
            self._filter_query = event.value
            if self._entries.model_entries or self._entries.dataset_entries:
                self._render_picker()
            return
        if event.input.id == "cfg-input-subset":
            self._render_subset_row()
        self._refresh_preview()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """A focused Input consumes its own Enter (the pin): param
        inputs re-apply; the filter returns focus to the picker. No
        Input path ever opens the gate."""
        if event.input.id == "cfg-filter":
            self.query_one("#cfg-picker", PickerList).focus()
            return
        self._refresh_preview()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """The fairness-subset toggle: on/off with the path row + advisory."""
        if event.checkbox.id != "cfg-subset-toggle":
            return
        self._subset_on = event.value
        self.query_one("#cfg-input-subset", Input).display = event.value
        self._render_subset_row()
        self._refresh_preview()

    # ===== actions (the screen keymap) =====

    def action_toggle_mark(self) -> None:
        """[space] with focus outside the picker — marks the picker's
        cursor row (one mark vocabulary anywhere)."""
        picker = self.query_one("#cfg-picker", PickerList)
        index = picker.highlighted
        key = picker.key_at(index)
        if key is None:
            return
        if picker.disabled_at(index):
            self.app.notify(
                S.SEL_DISABLED_MARK_WARNING.format(key=key),
                severity="warning")
            return
        entries, kind = self._current_entries()
        if key not in {str(entry["key"]) for entry in entries}:
            return
        if kind == "models":
            marks = set(self._spec.models)
            marks.symmetric_difference_update({key})
            self._apply_spec_change(models=tuple(marks),
                                    picker_anchor=key)
        else:
            marks = set(self._spec.tasks)
            marks.symmetric_difference_update({key})
            self._apply_spec_change(tasks=tuple(marks),
                                    picker_anchor=key)

    def action_switch_kind(self) -> None:
        """[m] flips models <-> datasets (the title flips with it)."""
        self._picker_kind = ("datasets"
                             if self._picker_kind == "models" else "models")
        self._render_picker()

    def action_focus_filter(self) -> None:
        """[/] focuses the filter Input (the inherited grammar)."""
        self.query_one("#cfg-filter", Input).focus()

    def action_clear_filter(self) -> None:
        """[esc] clears a live filter first (never quits — modals pop
        themselves); with no filter it is a no-op."""
        if self._filter_query:
            self._filter_query = ""
            self.query_one("#cfg-filter", Input).value = ""
            if self._entries.model_entries or self._entries.dataset_entries:
                self._render_picker()
            self.query_one("#cfg-picker", PickerList).focus()

    def action_pick_choice(self) -> None:
        """[enter] on a focused choice row — the RadioSet modal (the
        preset-modal family; selection writes the param + persists)."""
        if self.app.below_minimum_grid:
            return  # no chrome over the guard (WR-06)
        focused = self.focused
        if not isinstance(focused, ChoiceRow):
            return
        if focused.field == "peft":
            options, current, title = (
                run_config_service.PEFT_MODES, self._spec.peft,
                S.CFG_FIELD_PEFT)
        else:
            options, current, title = (
                run_config_service.CONFIG_VARIANTS,
                self._spec.config_variant, S.CFG_FIELD_VARIANT)

        def on_pick(value: str) -> None:
            focused.set_value(value)
            if focused.field == "peft":
                self._apply_spec_change(peft=value)
            else:
                self._apply_spec_change(config_variant=value)
            self._render_hints(self._last_probe_hits)
            self._refresh_preview()

        self.app.push_screen(ChoiceModal(title, options, current, on_pick))

    def action_preview_modal(self) -> None:
        """[p] — the dry-run detail modal + a forced preview refresh."""
        if self.app.below_minimum_grid:
            return  # no chrome over the guard (WR-06)
        self._refresh_preview()
        result = self._last_preview
        problems = tuple(self._last_parse_problems)
        if result is not None:
            problems += tuple(result.problems)
        if result is None:
            return
        lines: list[str] = []
        if result.fractions_count:
            lines.append(S.CFG_PREVIEW_LINE_CURVE.format(
                models=result.models_count, tasks=result.tasks_count,
                seeds=result.seeds_count, fractions=result.fractions_count,
                cells=result.cells_count))
        else:
            lines.append(S.CFG_PREVIEW_LINE.format(
                models=result.models_count, tasks=result.tasks_count,
                seeds=result.seeds_count, cells=result.cells_count))
        lines.append(S.CFG_PREVIEW_NOTE)
        if not problems and result.cells_count > 0:
            argv = self._run_service.compose_argv(self._spec)
            lines.append(S.CFG_ARGV_LABEL + " ".join(str(a) for a in argv))
        lines.extend(_numbered_problems(problems) if problems else [])
        self.app.push_screen(PreviewModal(tuple(lines)))

    # ===== the F4W actions (261014-f4w: [s] save-defaults, ctrl+o picker) =====

    @staticmethod
    def _dir_input_fields() -> "dict[str, str]":
        """The five dir-input ids -> their CFG_FIELD labels (the picker's
        modal title + the open-condition allowlist), re-derived at CALL
        time (CR-01, quick-261016-hhx — the 08 review: a class-body
        ClassVar froze the import-time language into the ctrl+o picker
        title; the function reads S.* fresh so the title follows the
        live language)."""
        return {
            "#cfg-input-output-root": S.CFG_FIELD_OUTPUT_ROOT,
            "#cfg-input-dataset-root": S.CFG_FIELD_DATASET_ROOT,
            "#cfg-input-model-root": S.CFG_FIELD_MODEL_ROOT,
            "#cfg-input-log-dir": S.CFG_FIELD_LOG_DIR,
            "#cfg-input-cache": S.CFG_FIELD_CACHE,
        }

    def action_save_directory_defaults(self) -> None:
        """[s] — atomically write the five dir values to
        directories.json and toast the written path (F4W-03).

        Synchronous is deliberate: a single deliberate keypress, one
        atomic two-syscall write (``settings.atomic_write`` — tmp
        sibling + ``os.replace``). The per-keystroke preview rides its
        worker because it fires on EVERY Input.Changed; a lone
        keypress's single small write does not need that machinery, and
        keeping it inline means the toast names the path the operator
        just saw written, never a stale worker's. Persisting the
        current inputs into run_config.json stays the preview worker's
        job — this action only writes the defaults file.
        """
        spec, _ = self._compose_spec()
        try:
            written = self._run_service.save_directory_defaults(spec)
        except Exception as exc:  # noqa: BLE001 — WR-03: surfaced as the
            # error toast, never a silently dropped keypress
            self.app.notify(
                S.CFG_SAVE_DEFAULTS_FAILED_TOAST.format(error=_exc_text(exc)),
                severity="error")
            return
        self.app.notify(S.CFG_SAVE_DEFAULTS_TOAST.format(path=str(written)))

    def action_open_dir_picker(self) -> None:
        """ctrl+o — open the DirPickerModal over the FOCUSED dir input
        (F4W-05).

        The open condition is an Input whose id is one of the five
        dir-input ids: any other focus is a silent no-op (never opens
        over the wrong field, never crashes — the filter Input and the
        subset path Input are deliberately excluded; they are not
        directories). The root comes from the tested tier's
        ``directory_picker_root`` fallback chain.
        """
        if self.app.below_minimum_grid:
            return  # no chrome over the guard (WR-06)
        focused = self.focused
        if not isinstance(focused, Input) or focused.id is None:
            return
        label = self._dir_input_fields().get(f"#{focused.id}")
        if label is None:
            return
        root = run_config_service.directory_picker_root(focused.value)
        self.app.push_screen(DirPickerModal(focused, label, root))

    # ===== the launch-confirmation pipeline (LNC-01..03 — [enter]) =====

    def action_open_gate(self) -> None:
        """[enter] opens the gate: fresh enumeration -> env preflight
        -> confirm / E2' typed phrase -> launch. Every step recomputes
        through the services (the preview line is never trusted)."""
        if self.app.below_minimum_grid:
            return  # no chrome over the guard (WR-06)
        if self._gate_active:
            return  # the pre-modal pipeline is already running
        spec, parse_problems = self._compose_spec()
        self._gate_active = True
        self._gate_parse_problems = parse_problems
        self._gate_stage_id += 1
        self._run_gate_enumeration(spec, self._gate_stage_id)

    @work(exclusive=True, thread=True, group="cfg-gate-enum")
    def _run_gate_enumeration(self, spec: RunSpec, run_id: int) -> None:
        """Step 1 — the FRESH same-source enumeration (worker: the
        console never freezes while the matrix enumerates, T-11-06-04;
        WR-03-wrapped: an exception surfaces, never a wedged gate)."""
        try:
            result = self._run_service.preview(spec)
        except Exception as exc:  # noqa: BLE001 — WR-03
            self.post_message(
                self.GateWorkerError(_exc_text(exc), run_id,
                                     scope="stage"))
            return
        self.post_message(
            self.GateEnumerationDone(result, self._gate_parse_problems,
                                     run_id))

    def on_run_config_screen_gate_enumeration_done(
            self, message: GateEnumerationDone) -> None:
        if message.run_id != self._gate_stage_id or not self._gate_active:
            return  # superseded or already terminal (WR-02)
        problems = tuple(message.parse_problems)
        problems += tuple(message.result.problems)
        if problems:
            # launch blocked — the numbered problems modal, nothing else
            self._gate_active = False
            if not self.app.below_minimum_grid:
                self.app.push_screen(ProblemsModal(problems))
            return
        # CR-02 (phase-11 review): refuse a launch into an already-LIVE
        # output root at the problems stage, naming the root — the
        # service's own _spawn guard is the structural backstop, but
        # the operator must see WHY before any confirm (kill/detach or
        # pick a different root first). WR-01 (stale-refresh review):
        # the key rides the resolve_dirs basis (output_root_abs — the
        # SAME REPO_ROOT basis the argv threads, D-14), never a
        # CWD-resolved reading that would miss the live key when the
        # TUI process runs outside the repo.
        spec, _ = self._compose_spec()
        root_key = str(self._run_service.resolve_dirs(spec).output_root_abs)
        if root_key in set(self._launcher.live_sweeps()):
            self._gate_active = False
            if not self.app.below_minimum_grid:
                self.app.push_screen(ProblemsModal(
                    (("live_root", root_key),)))
            return
        # EHC-3 (261015-ehc ruling 3): the single-GPU serialization
        # pre-check — beside the CR-02 live-root stage, BEFORE any env
        # preflight or confirm: on an effective-GPU-count == 1 machine
        # with a live sweep registered, the gate refuses naming the
        # running root(s) (the tolerant getattr seam — a fake without
        # the method never blocks, the 11-03 precedent; the service's
        # own stage-0 guard is the structural backstop).
        blocked_getter = getattr(
            self._launcher, "single_gpu_launch_blocked", None)
        blocked = (blocked_getter()
                   if blocked_getter is not None else None)
        if blocked:
            self._gate_active = False
            if not self.app.below_minimum_grid:
                self.app.push_screen(ProblemsModal(
                    (("single_gpu_busy", ", ".join(blocked)),)))
            return
        self._gate_stage_id += 1
        self._run_env_preflight(self._gate_stage_id)

    @work(exclusive=True, thread=True, group="cfg-gate-env")
    def _run_env_preflight(self, run_id: int) -> None:
        """Step 2 — the env preflight over the frozen phase-8 face
        (WR-03-wrapped)."""
        try:
            verdict = self._launcher.env_preflight()
        except Exception as exc:  # noqa: BLE001 — WR-03
            self.post_message(
                self.GateWorkerError(_exc_text(exc), run_id,
                                     scope="stage"))
            return
        self.post_message(self.EnvPreflightDone(verdict, run_id))

    def on_run_config_screen_env_preflight_done(
            self, message: EnvPreflightDone) -> None:
        if message.run_id != self._gate_stage_id or not self._gate_active:
            return
        if not message.verdict.can_launch:
            self._gate_active = False
            if not self.app.below_minimum_grid:
                self.app.push_screen(EnvBlockModal(
                    message.verdict.failed_kernels,
                    message.verdict.reasons))
            return
        spec, _ = self._compose_spec()
        self._gate_stage_id += 1
        self._run_confirm_data(spec, self._gate_stage_id)

    @work(exclusive=True, thread=True, group="cfg-gate-confirm")
    def _run_confirm_data(self, spec: RunSpec, run_id: int) -> None:
        """Step 3 — the FRESH confirm summary (never screen state,
        T-11-06-02; WR-03-wrapped)."""
        try:
            summary = self._launcher.gate_confirm_data(spec)
        except Exception as exc:  # noqa: BLE001 — WR-03
            self.post_message(
                self.GateWorkerError(_exc_text(exc), run_id,
                                     scope="stage"))
            return
        self.post_message(self.GateSummaryReady(summary, run_id))

    def on_run_config_screen_gate_summary_ready(
            self, message: GateSummaryReady) -> None:
        if message.run_id != self._gate_stage_id or not self._gate_active:
            return
        summary = message.summary
        self._gate_summary = summary
        self._gate_active = False  # the confirm modal owns the remainder
        if self.app.below_minimum_grid:
            return  # no chrome over the guard (WR-06)
        spec, _ = self._compose_spec()
        if summary.is_e2x:
            self.app.push_screen(E2PhraseModal(
                dirname=summary.expected_phrase,
                matches=lambda typed: self._run_service.phrase_matches(
                    typed, spec.output_root),
                on_confirm=lambda phrase: self._launch(phrase),
            ))
        else:
            self.app.push_screen(_GateConfirmModal(
                pairs=summary.pairs,
                message=(S.LNC_GATE_SUMMARY.format(
                    models=summary.models, tasks=summary.tasks,
                    seeds=summary.seeds, cells=summary.cells,
                    output_root=summary.output_root)
                    + "\n" + S.LNC_GATE_CONFIRM),
                on_confirm=lambda: self._launch(None),
            ))

    def _launch(self, phrase: "str | None") -> None:
        """Step 4 — the gated launch (worker: the spawn is OS I/O)."""
        spec, _ = self._compose_spec()
        self._gate_launch_id += 1
        self._run_launch(spec, phrase, self._gate_launch_id)

    @work(exclusive=True, thread=True, group="cfg-gate-launch")
    def _run_launch(self, spec: RunSpec, phrase: "str | None",
                    run_id: int) -> None:
        """Step 4 — the gated launch (worker: the spawn is OS I/O;
        WR-03-wrapped — dying here is AFTER the operator confirmed, the
        worst instance: surfaced as the error toast, never a silent
        no-op)."""
        try:
            outcome = self._launcher.launch_spec(spec, phrase)
        except Exception as exc:  # noqa: BLE001 — WR-03
            self.post_message(
                self.GateWorkerError(_exc_text(exc), run_id,
                                     scope="launch"))
            return
        self.post_message(
            self.LaunchFinished(outcome, self._gate_summary, run_id))

    def on_run_config_screen_launch_finished(
            self, message: LaunchFinished) -> None:
        if message.run_id != self._gate_launch_id:
            return
        outcome = message.outcome
        if isinstance(outcome, GateRefusal):
            # the service re-proved the gate after our live check — the
            # structural boundary held; surface it honestly
            if outcome.stage == "phrase":
                summary = message.summary
                spec, _ = self._compose_spec()
                dirname = (outcome.expected
                           or (summary.expected_phrase
                               if summary else self._run_service.expected_phrase(
                                   spec.output_root)))
                if not self.app.below_minimum_grid:
                    self.app.push_screen(E2PhraseModal(
                        dirname=dirname,
                        matches=lambda typed: (
                            self._run_service.phrase_matches(
                                typed, spec.output_root)),
                        on_confirm=lambda phrase_: self._launch(phrase_),
                    ))
                return
            if not self.app.below_minimum_grid:
                self.app.push_screen(ProblemsModal(outcome.problems))
            return
        if isinstance(outcome, LaunchOutcome):
            summary = message.summary
            if outcome.spawned:
                if summary is not None:
                    self.app.notify(S.LNC_LAUNCH_TOAST.format(
                        cells=summary.cells,
                        output_root=summary.output_root))
                # D-13's auto-nav half (11-07): record + attach + the
                # slot-5 jump over the app-owned monitor screen
                self.app.sweep_launched(
                    outcome.root,
                    summary.cells if summary is not None else 0)
                return
            self.app.notify(
                S.LNC_LAUNCH_FAILED_TOAST.format(
                    error=outcome.error or ""),
                severity="error")
            return

    def on_run_config_screen_gate_worker_error(
            self, message: GateWorkerError) -> None:
        """WR-03 (phase-11 review): a gate/mount worker raised — the
        pre-modal flag releases (the gate is re-enterable, never
        wedged) and the error toast surfaces it (a confirm-then-crash
        is never a silent no-op).

        IN-02 (08 review, fix batch 261017-klw): the staleness filter
        compares run_id against EXACTLY ONE counter — scope ``'launch'``
        against ``_gate_launch_id``, everything else (stage or untagged)
        against ``_gate_stage_id`` — never the either-counter collision
        that surfaced a superseded stage error as a spurious
        launch-failed toast. run_id None (the mount worker) always
        surfaces."""
        run_id = message.run_id
        if run_id is not None:
            if message.scope == "launch":
                if run_id != self._gate_launch_id:
                    return  # a superseded launch worker's late error
            elif run_id != self._gate_stage_id:
                return  # a superseded stage worker's late error (WR-02)
        self._gate_active = False
        self.app.notify(
            S.LNC_LAUNCH_FAILED_TOAST.format(error=message.error),
            severity="error")

    # ===== spec mutation (persist + preview through the worker) =====

    def _apply_spec_change(self, picker_anchor: "str | None" = None,
                           **changes: Any) -> None:
        """One spec mutation: advance the base, re-render counts, then
        persist + preview through the exclusive worker.

        ``picker_anchor`` is consumed HERE — never a spec field (the
        ``replace`` below receives only the real changes): the toggled
        registry key the picker rebuild restores its cursor + scroll
        around (UX-1, 261016-poa)."""
        self._spec = replace(self._spec, **changes)
        self._render_counts()
        self._render_picker(anchor_key=picker_anchor)
        self._refresh_preview()


def _truncate_text(text: Text, width: int) -> Text:
    """Ellipsis-truncate one rich Text in place (Rich's measurement)."""
    text.truncate(max(width, 1), overflow="ellipsis", pad=False)
    return text


def _exc_text(exc: BaseException) -> str:
    """One caught exception's message (empty str() falls back to
    repr — some OSErrers stringify empty, never toast an empty error)."""
    return str(exc) or repr(exc)
