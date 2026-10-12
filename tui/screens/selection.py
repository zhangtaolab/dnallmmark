"""
selection — the selection screen (Phase 8, 08-07; SEL-01..04 presentation).

The operator's daily surface: model/dataset tables browsed one at a time
(the ``m`` toggle), k9s-style type-to-filter over the 08-05 grammar,
spacebar marks into stable app-state sets (one set per list, both alive
while either table is visible), the preset/template modals over the 08-05
services, and the SEL-04 presence column from the 08-04 n_audit data.

Contract (locked decisions):

- Presentation only (the ``tui/screens/`` tier contract): filtering,
  preset derivation, template validation, and presence all live in
  ``tui/services/`` — this screen wires injected service calls to widgets
  and formats their results (binding constraint 5: TUI orchestrates,
  never computes).
- SEL-01 (mark-set mechanism): marks live in SHARED app-state sets keyed
  on registry keys, never inside the DataTable (08-RESEARCH Pitfall 1 —
  DataTable has no multi-select). Spacebar toggles the cursor row's
  membership and updates the dedicated mark column in place via
  ``update_cell``; filter rebuilds (``clear`` + re-``add_row`` with the
  same keys) and the ``m`` table switch can never lose them. Both sets
  are constructor-injected by the composition root so the matrix screen
  (08-07 Task 2) reads the same live sets.
- SEL-01 (filter): the Input drives the injected parse/apply pair; the
  unknown-axis diagnostics render as the dim warning line while valid
  terms still apply; the (N/total) readout is live; esc clears and
  refocuses the table.
- SEL-02 (presets, replacing semantics): applying a preset REPLACES the
  relevant mark set(s) — tier-1 marks pair models AND tasks, tier-2
  models only, all marks every registry key in both lists, customs
  restore both sets as saved. Keys absent from the current registry are
  skipped with the loud warning; the menu order is tier-1, tier-2, all,
  customs sorted by name.
- SEL-03 (templates, fail-closed): import validates collect-all through
  the injected service — a failed import renders the numbered problem
  list and applies NOTHING; a successful import replaces the marks.
- SEL-04 (presence): cells render the 08-04 ``Presence`` values — present
  = pass glyph + thousands-separated exact counts (formatting happens
  only here), missing = the missing word, unknown = the gap-filler copy,
  and the n_audit-absent column state renders the documented copy. The
  ``missing`` flag decision is the service's (tier-1 tested); the screen
  never re-derives it.
- D-11 (10-05): the presence snapshot is the MERGED audit — the
  committed n_audit overlaid with the queue's reconcile-pass rows
  (``download_queue.merge_presence`` over ``reconciled_rows``, a pure
  read of the queue state file inside the exclusive worker; the
  UNCHANGED ``registries.presence_for`` maps the merged view — the
  10-02 contract). Presence flips ✗->✓ exactly on reconcile-pass; a
  landed-but-mismatched dataset never flips. ``apply_queue_event``
  re-runs the snapshot worker on a done event (the app-level forward
  landed in 10-04), so the flip is live on the mounted screen.
- D-14 (10-05): presence-✗ dataset rows enqueue into the SHARED
  download queue through the same service call and the same outcome
  toasts as the data-manager screen's ``d`` (one vocabulary) — the
  kick lives on the app; the models view never enqueues.
- D-03 (the read seam): every file-reading service call — the
  registry/n_audit load AND the preset-menu read (both registries, the
  priorities file, and presets.json) — runs in an exclusive
  ``@work(exclusive=True, thread=True)`` worker (the default worker
  group makes them mutually exclusive, so reads never overlap and none
  ever blocks the event loop, T-08-07); the single loading row covers
  the load seam; results cross the thread boundary only via
  ``post_message``. A result arriving while the min-size guard is up is
  dropped — no chrome may open over the guard (WR-06: the push is async,
  so it can fire while the guard is the active screen).
- I18N-01: zero Chinese literals in this module — every operator-facing
  string renders through ``tui/strings.py`` constants (grep-enforced);
  registry keys, filter axes, and JSON pointers stay English verbatim.
- ModalScreen for every modal surface (presets, templates, path/name
  input, confirms, row detail): app/screen bindings do not fire while a
  modal is on top (Pitfall 11).
"""

import json
import os
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Protocol

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    DataTable,
    Footer,
    Input,
    Label,
    ListItem,
    ListView,
    RichLog,
    SelectionList,
    Static,
)
from textual.widgets.selection_list import Selection

from tui.screens.matrix import MatrixScreen
from tui.screens.nav import BottomBar, TopMenuBar
from tui.services import custom_entries as custom_entries_service
from tui.services import download_queue as download_queue_service
from tui.services import registries as registries_service
from tui.services import selection as selection_service
from tui.services import settings as settings_service
from tui.services import templates as templates_service
from tui.services.custom_validation import (
    METRIC_REGISTRY,
    ValidationSources,
    validate_dataset_candidate,
    validate_import_document,
    validate_model_candidate,
)
from tui.services.download_queue import EnqueueOutcome, QueueEvent
from tui.services.gauntlet import GauntletService
from tui.services.registries import (
    PRESENCE_MISSING,
    PRESENCE_PRESENT,
    Presence,
)
from tui.strings import (
    APP_MODAL_BACK_LABEL,
    DL_DISABLED_TOAST,
    DL_UNKNOWN_TOAST,
    ENV_DETAIL_LABEL,
    NAV_LABEL_ABOUT,
    NAV_LABEL_DATA,
    NAV_LABEL_ENV,
    NAV_LABEL_MONITOR,
    NAV_LABEL_RUN_CONFIG,
    NAV_LABEL_SELECTION,
    QUEUE_CLI_UNAVAILABLE,
    QUEUE_PERSIST_FAILED_TOAST,
    QUEUE_TOAST_ALREADY_QUEUED,
    QUEUE_TOAST_ENQUEUED,
    SEL_COL_CATEGORY,
    SEL_COL_MARK,
    SEL_COL_METRIC,
    SEL_COL_MODEL,
    SEL_COL_PRESENCE,
    SEL_COL_SIZE,
    SEL_COL_SPECIES,
    SEL_COL_TASK,
    SEL_COL_TYPE,
    SEL_COUNT_CUSTOM_SEGMENT,
    SEL_CUSTOM_BADGE,
    SEL_DISABLED_MARK_WARNING,
    SEL_DISABLED_SUFFIX,
    SEL_ENQUEUE_LABEL,
    SEL_ENQUEUE_PRESENT_TOAST,
    SEL_FILTER_COUNT,
    SEL_FILTER_KEY_LABEL,
    SEL_FILTER_LABEL,
    SEL_FILTER_NO_MATCH,
    SEL_FILTER_PLACEHOLDER,
    SEL_FILTER_UNKNOWN_AXIS,
    SEL_LOADING_ROW,
    SEL_MARK_LABEL,
    SEL_MATRIX_LABEL,
    SEL_N_AUDIT_MISSING,
    SEL_PRESENCE_MISSING,
    SEL_PRESENCE_PRESENT,
    SEL_PRESENCE_UNKNOWN,
    SEL_PRESET_ALL,
    SEL_PRESET_APPLIED,
    SEL_PRESET_LABEL,
    SEL_PRESET_NAME_PLACEHOLDER,
    SEL_PRESET_NO_CUSTOMS,
    SEL_PRESET_OVERWRITE_CONFIRM,
    SEL_PRESET_SAVE_FAILED,
    SEL_PRESET_SAVED,
    SEL_PRESET_TIER_1,
    SEL_PRESET_TIER_2,
    SEL_PRESET_TITLE,
    SEL_PRESET_UNKNOWN_KEYS,
    SEL_REGISTRY_LOAD_FAILED,
    SEL_SAVE_PRESET_LABEL,
    SEL_SCREEN_TITLE_DATASETS,
    SEL_SCREEN_TITLE_MODELS,
    SEL_STATUS_LINE,
    SEL_SWITCH_LABEL,
    SEL_TEMPLATE_EXPORTED,
    SEL_TEMPLATE_IMPORTED,
    SEL_TEMPLATE_LABEL,
    SEL_TEMPLATE_MENU_EXPORT,
    SEL_TEMPLATE_MENU_IMPORT,
    SEL_TEMPLATE_MENU_TIERS,
    SEL_TEMPLATE_PATH_PLACEHOLDER,
    SEL_TEMPLATE_PROBLEM_LINE,
    SEL_TEMPLATE_PROBLEMS,
    SEL_TEMPLATE_TITLE,
    SEL_TEMPLATE_WRITE_FAILED,
    SEL_TOGGLE_DISABLED_TOAST,
    SEL_TOGGLE_ENABLED_TOAST,
    SEL_TOGGLE_LABEL,
    SEL_TOGGLE_OFFICIAL_NOOP,
    SEL_WIZARD_LABEL,
)

if TYPE_CHECKING:
    from textual import getters

    from tui.app import DnallmMarkTui

# ===== Service data shapes (the injection contract's vocabulary) =====


@dataclass(frozen=True)
class SelectionData:
    """One loaded snapshot of the registries + presence (pure data).

    Attributes:
        model_entries: canonical 08-04 model entries (registry order).
        dataset_entries: canonical 08-04 dataset entries.
        presence: registry key -> 08-04 ``Presence`` (the real backend
            fills dataset keys from n_audit; keys absent here render the
            unknown cell).
        audit_available: False when n_audit.json is missing/corrupt —
            every presence cell then renders the documented copy.
        models_load_error: the registry path when the models read failed
            (the tolerant-loader None result), else None.
        datasets_load_error: the datasets-read failure path, else None.
    """

    model_entries: tuple[dict, ...] = ()
    dataset_entries: tuple[dict, ...] = ()
    presence: dict[str, Presence] = field(default_factory=dict)
    audit_available: bool = True
    models_load_error: "str | None" = None
    datasets_load_error: "str | None" = None
    #: The custom-status map (09-06, additive — the default keeps every
    #: Phase 8 fake conforming unchanged): registry key -> ``{"custom":
    #: True, "enabled": bool}`` for every LANDED custom entry (both
    #: states, from the management second read); official keys are absent
    #: from the map entirely (D-10: the badge, not position, marks them).
    custom_status: dict[str, dict] = field(default_factory=dict)


@dataclass(frozen=True)
class PresetOption:
    """One preset-menu entry — pure data; the screen applies it.

    Attributes:
        id: ``tier-1`` | ``tier-2`` | ``all`` | ``custom:<name>``.
        kind: ``derived`` | ``custom`` (labels map on the id/kind).
        name: the custom preset's name (None for the derived built-ins).
        models: model registry keys to mark, derivation order.
        tasks: task registry keys to mark (``()`` for tier-2).
        unknown_keys: members absent from the current registries — the
            loud-surfacing channel (never silently dropped).
    """

    id: str
    kind: str
    name: "str | None"
    models: tuple[str, ...] = ()
    tasks: tuple[str, ...] = ()
    unknown_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class PresetMenu:
    """The derived preset menu plus the damaged-priorities signal."""

    options: tuple[PresetOption, ...] = ()
    load_error: "str | None" = None


@dataclass(frozen=True)
class TemplateImport:
    """A template-import outcome — collect-all, fail-closed.

    Attributes:
        ok: True only when the file parsed AND validated — the caller
            applies marks only then.
        problems: every problem as ``(location, message)`` — the JSON
            pointer for validation problems, the path for load failures.
        models: the template's model keys (valid imports only).
        tasks: the template's task keys (valid imports only).
    """

    ok: bool = False
    problems: tuple[tuple[str, str], ...] = ()
    models: tuple[str, ...] = ()
    tasks: tuple[str, ...] = ()


class SelectionServiceProtocol(Protocol):
    """The selection-service surface the screen consumes.

    The constructor-injection seam (the 08-06 pattern): the screen
    depends on this protocol, not on any concrete service — the real
    ``SelectionBackend`` (delegation glue over the 08-04/08-05 service
    modules) and the tier-2 Pilot fakes both conform structurally, so no
    registry file, priorities file, or template file is ever touched by
    a faked Pilot run.
    """

    def load_selection_data(self) -> SelectionData:
        """The registries + presence snapshot (the worker-read seam)."""

    def preset_menu(self) -> PresetMenu:
        """The preset menu: tier-1, tier-2, all, then customs sorted."""

    def custom_names(self) -> tuple[str, ...]:
        """The saved custom-preset names (the overwrite check)."""

    def save_preset(self, name: str, models: Iterable[str],
                    tasks: Iterable[str]) -> None:
        """Persist a custom preset under the config root."""

    def parse_filter(self, query: str) -> Any:
        """Parse a filter query (the 08-05 ParsedFilter shape)."""

    def apply_filter(self, entries: Sequence[dict], parsed: Any) -> list[dict]:
        """Apply parsed terms to entries (pure, order-preserving)."""

    def import_template(self, path: str) -> TemplateImport:
        """Read + collect-all validate one template file (fail-closed)."""

    def export_template(self, path: str, models: Iterable[str],
                        tasks: Iterable[str]) -> None:
        """Export the selection as a run template to the path."""

    def export_tiers(self, path: str, models: Iterable[str],
                     tasks: Iterable[str]) -> None:
        """Export the selection as a sweep_priorities tier list."""


class SelectionBackend:
    """The real selection service — delegation glue over 08-04/08-05.

    Every semantic stays in the tested service modules; this adapter only
    reshapes them into the object seam the screen's constructor injection
    consumes. The registry read is wrapped tolerantly AT THIS SEAM (the
    advisory-UI survivability rule): a missing official registry file or
    a malformed custom overlay degrades to the documented load-error
    state naming the path — the app stays alive (registry_loader's own
    fail-loud contract is untouched for pipeline consumers).
    """

    def __init__(self, config_dir: "str | None" = None,
                 priorities_path: "str | None" = None):
        """Adapt the services over injectable roots (tests point at tmp).

        Args:
            config_dir: the XDG config root; None means the 08-04 default.
            priorities_path: the sweep_priorities file; None means the
                committed pipeline file.
        """
        self._config_dir = config_dir
        self._priorities_path = priorities_path

    # ----- the registries + presence snapshot -----

    def load_selection_data(self) -> SelectionData:
        """The registries + presence snapshot (the worker-read seam).

        Both registry reads degrade independently (a failed models read
        leaves the dataset table healthy); presence fills per DATASET
        key from the committed n_audit through the pure 08-04 mapping.

        The 09-06 composition: the overlay-merged entries (enabled
        customs) are UNIONED with the management second read (ALL
        customs) — disabled customs append after the merged entries so
        the table renders every landed entry exactly once, and
        ``custom_status`` records the custom/official + enabled truth the
        badge, the toggle, and the count line render from. Both reads
        resolve the SAME custom file (the overlay root when pinned), so
        the two views can never disagree about which keys exist
        (Pitfall 7).

        The 10-05 composition (D-11): the presence view is the MERGED
        audit — the committed n_audit overlaid with the queue's
        reconcile-pass rows (``merge_presence`` over ``reconciled_rows``,
        a pure tolerant read of the queue state file — no service
        instance, no write). The committed file alone can never flip a
        freshly downloaded dataset (only the explicit ``g`` re-audit
        refreshes it), so the flip rides here; the UNCHANGED
        ``presence_for`` maps the merged view (semantic 6: a
        landed-but-mismatched dataset never flips — only done entries
        reach the overlay).
        """
        model_entries, models_error = _load_entries(
            registries_service.load_model_entries, _MODELS_REGISTRY_PATH,
        )
        dataset_entries, datasets_error = _load_entries(
            registries_service.load_dataset_entries, _DATASETS_REGISTRY_PATH,
        )
        custom_status: dict[str, dict] = {}
        for kind, entries, project in (
            ("models", model_entries, _custom_model_entry),
            ("datasets", dataset_entries, _custom_dataset_entry),
        ):
            management, _management_error = (
                custom_entries_service.read_entries(
                    kind, registry_dir=_overlay_registry_dir(),
                )
            )
            merged_keys = {entry["key"] for entry in entries}
            for key, entry in management.items():
                if not isinstance(entry, dict):
                    continue  # never a badge target (the loader's shape)
                custom_status[key] = {
                    "custom": True,
                    "enabled": entry.get("enabled") is not False,
                }
                if key not in merged_keys:
                    entries.append(project(key, entry))
        committed_audit = registries_service.load_n_audit()
        overlay_rows = download_queue_service.reconciled_rows()
        audit = download_queue_service.merge_presence(
            committed_audit, overlay_rows)
        presence: dict[str, Presence] = {}
        if audit:
            presence = {
                entry["key"]: registries_service.presence_for(
                    entry["key"], audit,
                )
                for entry in dataset_entries
            }
        return SelectionData(
            model_entries=tuple(model_entries),
            dataset_entries=tuple(dataset_entries),
            presence=presence,
            # the column renders whenever ANY truth source exists — the
            # committed baseline OR live reconcile rows (an audit-less
            # machine with a done queue entry still shows its flip;
            # other keys render the unknown cell)
            audit_available=(committed_audit is not None)
            or bool(overlay_rows),
            models_load_error=models_error,
            datasets_load_error=datasets_error,
            custom_status=custom_status,
        )

    # ----- presets (SEL-02, D-06: derived, never hardcoded) -----

    def preset_menu(self) -> PresetMenu:
        """tier-1, tier-2, all (derived) then customs sorted by name."""
        model_entries, _ = _load_entries(
            registries_service.load_model_entries, _MODELS_REGISTRY_PATH,
        )
        dataset_entries, _ = _load_entries(
            registries_service.load_dataset_entries, _DATASETS_REGISTRY_PATH,
        )
        derivation = selection_service.derive_presets(
            self._priorities_path or str(_DEFAULT_PRIORITIES_PATH),
            [entry["key"] for entry in model_entries],
            [entry["key"] for entry in dataset_entries],
        )
        options = tuple(
            PresetOption(
                id=preset.id, kind="derived", name=None,
                models=preset.models, tasks=preset.tasks,
                unknown_keys=preset.unknown_keys,
            )
            for preset in derivation.presets
        )
        customs = selection_service.load_custom_presets(self._config_root())
        options += tuple(
            PresetOption(
                id=f"custom:{name}", kind="custom", name=name,
                models=tuple(value["models"]),
                tasks=tuple(value["tasks"]),
            )
            for name, value in sorted(customs.items())
        )
        return PresetMenu(options=options, load_error=derivation.load_error)

    def custom_names(self) -> tuple[str, ...]:
        """The saved custom-preset names, sorted (the overwrite check)."""
        return tuple(sorted(
            selection_service.load_custom_presets(self._config_root())
        ))

    def save_preset(self, name: str, models: Iterable[str],
                    tasks: Iterable[str]) -> None:
        """Persist a custom preset under the config root (atomic)."""
        selection_service.save_custom_preset(
            name, models, tasks, self._config_root(),
        )

    # ----- the filter grammar (pure 08-05 delegation) -----

    def parse_filter(self, query: str) -> Any:
        """Parse a filter query (the pure 08-05 grammar)."""
        return selection_service.parse_filter_query(query)

    def apply_filter(self, entries: Sequence[dict], parsed: Any) -> list[dict]:
        """Apply parsed terms to entries."""
        return selection_service.apply_filter(entries, parsed.terms)

    # ----- templates (SEL-03, D-07: strict, collect-all, fail-closed) -----

    def import_template(self, path: str) -> TemplateImport:
        """Read + collect-all validate one template file (fail-closed)."""
        doc, load_error = templates_service.load_template_file(path)
        if load_error is not None:
            return TemplateImport(
                ok=False, problems=((str(path), load_error),),
            )
        problems = templates_service.validate_template(doc)
        if problems:
            return TemplateImport(ok=False, problems=tuple(problems))
        if not isinstance(doc, dict):
            # unreachable post-validation (the schema requires an object)
            # — the guard narrows the type, never fires on real input
            return TemplateImport(
                ok=False,
                problems=((str(path), "template must be a JSON object"),),
            )
        return TemplateImport(
            ok=True,
            models=tuple(doc["models"]),
            tasks=tuple(doc["tasks"]),
        )

    def export_template(self, path: str, models: Iterable[str],
                        tasks: Iterable[str]) -> None:
        """Export the selection as a run template (valid by construction)."""
        doc = templates_service.export_selection_template(models, tasks)
        _write_json(Path(path), doc)

    def export_tiers(self, path: str, models: Iterable[str],
                     tasks: Iterable[str]) -> None:
        """Export the selection as a sweep_priorities tier list."""
        doc = templates_service.export_selection_template(models, tasks)
        _write_json(Path(path), templates_service.template_to_tiers(doc))

    def _config_root(self) -> Path:
        """The config root: the injected dir or the 08-04 default."""
        return (
            Path(self._config_dir) if self._config_dir is not None
            else settings_service.config_dir()
        )


# ===== The download-queue enqueue seam (10-05, D-14: the d action) =====


class SelectionQueueServiceProtocol(Protocol):
    """The enqueue surface the selection screen's ``d`` action consumes.

    The minimal shared seam (D-14's one-vocabulary rule): enqueue is
    the SAME service call the data-manager screen's ``d`` makes — the
    app-level kick stays on the app (``app.kick_download_queue``), never
    on this seam. The real adapter and the tier-2 Pilot fakes conform
    structurally (the EnvCheckServiceProtocol pattern).
    """

    def enqueue(self, key: str) -> EnqueueOutcome:
        """Idempotently enqueue one dataset key into the shared queue."""


class SelectionQueueBackend:
    """The real enqueue adapter — thin delegation glue (the
    ``EnvCheckBackend`` idiom) over the app's SHARED queue instance.

    The two-Protocol seam (the 10-04 ``DataManagerBackend`` shape): the
    app's driver-surface ``QueueDriverProtocol`` does not declare
    ``enqueue``, so this adapter bridges the app-level shared instance
    into the screen's minimal Protocol — an enqueue from the selection
    screen, the data-manager screen, and the driver all mutate ONE
    queue. A default-constructed backend builds its own real service
    for the never-injected path (inert until ``enqueue`` is called).
    """

    def __init__(self, queue: Any = None):
        """Adapt over one (shared) queue service instance.

        Args:
            queue: the app-level queue service; None builds a fresh
                real ``DownloadQueueService``. Typed ``Any``
                deliberately — the adapter boundary between the app's
                driver-surface Protocol and the screen's Protocol (the
                documented DataManagerBackend boundary pattern).
        """
        self._queue: Any = (queue if queue is not None
                            else download_queue_service
                            .DownloadQueueService())

    def enqueue(self, key: str) -> EnqueueOutcome:
        """Delegate the idempotent enqueue (D-08 semantics)."""
        return self._queue.enqueue(key)


# ===== The custom-onboarding service (09-06: the w/e actions' seam) =====


class CustomOnboardingBackend:
    """Delegation glue over the 09-01/09-02 custom-onboarding services.

    The ``w``/``e`` actions' service seam (the 08-06 injection pattern):
    the management read (the w-prefill source), the atomic enable toggle
    (D-09), and the fully-wired ``WizardModal`` composition (validator
    pre-bound to its ``ValidationSources``, the real gauntlet, and the
    09-01 store seams). Constructor defaults are the real services;
    Pilot fakes inject. Like ``SelectionBackend``, this class only
    composes — every semantic lives in the tested service modules
    (binding constraint 5).
    """

    def __init__(self, gauntlet_service: "GauntletService | None" = None):
        """Adapt the services (tests inject a fake gauntlet).

        Args:
            gauntlet_service: the 09-02 gauntlet orchestrator; None
                builds the real one at wizard-composition time.
        """
        self._gauntlet_service = gauntlet_service

    def read_entries(self, kind: str) -> "tuple[dict, str | None]":
        """The management read (Pitfall 7): every landed entry of kind."""
        return custom_entries_service.read_entries(kind)

    def set_enabled(self, kind: str, key: str, enabled: bool) -> bool:
        """The atomic enable/disable toggle (D-09, the single write seam)."""
        return custom_entries_service.set_enabled(kind, key, enabled)

    def build_wizard(self, kind: str, prefill: "dict | None",
                     on_changed: "Callable[[], None] | None"):
        """Compose the fully-wired wizard over the real services.

        Args:
            kind: ``"models"`` or ``"datasets"`` (the active table's kind).
            prefill: the cursor custom row's one-item ``{key: entry}``
                map (D-12), or None for a blank form.
            on_changed: fires after every successful land/undo so the
                table/badge/count refresh (the land-completion callback).

        Returns:
            WizardModal: the 09-04/09-05 modal with the validator, the
            gauntlet, and the store seams pre-bound to real services.
        """
        # Lazy import: wizard imports ConfirmModal from THIS module — a
        # module-top import would be circular (the composition only
        # runs on a w press, long after both modules loaded).
        from tui.screens.wizard import WizardModal

        model_entries, _models_error = _load_entries(
            registries_service.load_model_entries, _MODELS_REGISTRY_PATH,
        )
        dataset_entries, _datasets_error = _load_entries(
            registries_service.load_dataset_entries, _DATASETS_REGISTRY_PATH,
        )
        custom_models, _models_read_error = (
            custom_entries_service.read_entries("models"))
        custom_datasets, _datasets_read_error = (
            custom_entries_service.read_entries("datasets"))
        observed_species = tuple(sorted({
            entry["card"].get("species")
            for entry in model_entries
            if entry["card"].get("species")
        }))
        observed_tokenizers = tuple(sorted({
            entry["card"].get(registries_service.MODEL_CARD_TOKENIZER_FIELD)
            for entry in model_entries
            if entry["card"].get(registries_service.MODEL_CARD_TOKENIZER_FIELD)
        }))
        # Official keys = merged minus landed customs — exact under the
        # loader's collision fail-fast (a landed custom never shadows an
        # official key, so the difference set IS the official key set).
        sources = ValidationSources(
            official_model_keys=(
                frozenset(entry["key"] for entry in model_entries)
                - frozenset(custom_models)
            ),
            official_dataset_keys=(
                frozenset(entry["key"] for entry in dataset_entries)
                - frozenset(custom_datasets)
            ),
            existing_custom_models=custom_models,
            existing_custom_datasets=custom_datasets,
            observed_species=observed_species,
            observed_tokenizers=observed_tokenizers,
        )

        if kind == "models":
            def validator(values):
                return validate_model_candidate(values, sources)
        else:
            def validator(values):
                return validate_dataset_candidate(values, sources)

        def land(entry_kind, key, entry):
            result = custom_entries_service.land(entry_kind, key, entry)
            if on_changed is not None:
                on_changed()
            return result

        def undo(entry_kind, key):
            removed = custom_entries_service.undo(entry_kind, key)
            if removed and on_changed is not None:
                on_changed()
            return removed

        return WizardModal(
            kind=kind,
            validator=validator,
            prefill=prefill,
            vocabularies={
                "species": observed_species,
                "Tokenizer": observed_tokenizers,
                "metric": tuple(sorted(METRIC_REGISTRY)),
            },
            gauntlet_service=self._gauntlet_service or GauntletService(),
            land=land,
            undo=undo,
            import_read=lambda path: (
                custom_entries_service.read_import_candidates(path, kind)),
            import_validate=lambda doc: (
                validate_import_document(kind, doc, sources)),
            export_registry=lambda dest: (
                custom_entries_service.export_registry(kind, dest)),
            has_custom_entries=lambda: bool(
                custom_entries_service.read_entries(kind)[0]),
        )


# ===== Locations (resolved through the 08-04 service's own REPO_ROOT) =====

_MODELS_REGISTRY_PATH = (
    registries_service.REPO_ROOT / "pipeline" / "models_info.json"
)
_DATASETS_REGISTRY_PATH = (
    registries_service.REPO_ROOT / "pipeline" / "datasets_info.json"
)
_DEFAULT_PRIORITIES_PATH = (
    registries_service.REPO_ROOT / "pipeline" / "sweep_priorities.json"
)


def _load_entries(loader: Callable[[], list[dict]], registry_path: Path):
    """One tolerant registry read: (entries, None) or ([], the path).

    The advisory-UI survivability seam (SEL-01 empty edge): a missing
    official file (OSError) or a malformed custom overlay (SystemExit,
    the loader's fail-loud contract) degrades to the documented
    load-error state naming the path — never an exception through the
    screen, and the loader's own contract stays untouched for pipeline
    consumers.
    """
    try:
        return list(loader()), None
    except (OSError, SystemExit):
        return [], str(registry_path)


def _overlay_registry_dir():
    """The custom-registry root the overlay loader resolved (or None).

    The management second read honors ``DNALLMMARK_CUSTOM_REGISTRY_DIR``
    so the backend's two views — the overlay-merged entries and the
    management read — always describe ONE file (an env-pinned overlay
    must not be re-merged against the real home's customs; the default
    resolution of both roots is the same ``~/.config/dnallmmark``).
    """
    return os.environ.get("DNALLMMARK_CUSTOM_REGISTRY_DIR") or None


def _card_float(value) -> float:
    """Tolerant card numeric coercion (the 08-04 registries projection's
    own rule, mirrored here for management-read cards: absent or
    garbage renders as 0.0, never an exception through the screen)."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _custom_model_entry(key: str, card: dict) -> dict:
    """Project one custom card to the canonical model-entry view (the
    08-04 field contract — the registries service's own projection
    mirrored for the management read's appended rows)."""
    return {
        "key": key,
        "type": card.get("type") or "",
        "species": card.get("species") or "",
        "size_m": _card_float(card.get(registries_service.MODEL_CARD_SIZE_FIELD)),
        "card": card,
    }


def _custom_dataset_entry(key: str, card: dict) -> dict:
    """Project one custom card to the canonical dataset-entry view."""
    return {
        "key": key,
        "category": card.get("Category") or "",
        "type": card.get("type") or "",
        "metric": card.get("metric") or "",
        "card": card,
    }


def _write_json(path: Path, doc: object) -> None:
    """Atomically write one JSON document (the 08-04 helper)."""
    settings_service.atomic_write(
        path, json.dumps(doc, indent=2, ensure_ascii=False),
    )


# ===== Column geometry (key columns fit the real registry keys) =====
#
# DataTable columns render with 1 cell of padding on each side (the
# textual default ``cell_padding``) and the vertical scrollbar consumes 2
# more cells once rows exceed the height. The two key columns are pinned
# to the longest committed registry keys (UAT feedback: the old 80-col
# pin truncated real keys to a stub — 46 = the longest model key, 68 =
# the longest dataset key in ``pipeline/models_info.json`` /
# ``pipeline/datasets_info.json``), so the total budget (widths + 12
# padding + 2 scrollbar) grew past 80: 101 for the model view, 128 for
# the dataset view. On terminals narrower than the budget the DataTable
# scrolls horizontally — the matrix screen's h-scroll precedent; 80x24
# stays the minimum grid (the min-size guard), where the DataTable's own
# clipping/ellipsis applies — and full keys always render in the enter
# row-detail modal.

_MODELS_VIEW = "models"
_DATASETS_VIEW = "datasets"

_COL_MARK = "mark"
_COL_KEY = "key"
_COL_PRESENCE_KEY = "presence"

#: (column key, header constant, width) — the column keys are the
#: update_cell addressing scheme (English technical ids, I18N-01).
#: 46 — the longest committed model key fits exactly (UAT geometry).
_MODEL_KEY_W = 46
_MODEL_TYPE_W = 4
_MODEL_SPECIES_W = 8
_MODEL_SIZE_W = 7
_MODEL_PRESENCE_W = 20

#: 68 — the longest committed dataset key fits exactly (UAT geometry).
_DATASET_KEY_W = 68
_DATASET_CATEGORY_W = 8
_DATASET_TYPE_W = 10
_DATASET_METRIC_W = 8
_DATASET_PRESENCE_W = 18

_MODEL_COLUMNS: tuple[tuple[str, str, int], ...] = (
    (_COL_MARK, SEL_COL_MARK, 2),
    (_COL_KEY, SEL_COL_MODEL, _MODEL_KEY_W),
    ("type", SEL_COL_TYPE, _MODEL_TYPE_W),
    ("species", SEL_COL_SPECIES, _MODEL_SPECIES_W),
    ("size", SEL_COL_SIZE, _MODEL_SIZE_W),
    (_COL_PRESENCE_KEY, SEL_COL_PRESENCE, _MODEL_PRESENCE_W),
)

_DATASET_COLUMNS: tuple[tuple[str, str, int], ...] = (
    (_COL_MARK, SEL_COL_MARK, 2),
    (_COL_KEY, SEL_COL_TASK, _DATASET_KEY_W),
    ("category", SEL_COL_CATEGORY, _DATASET_CATEGORY_W),
    ("type", SEL_COL_TYPE, _DATASET_TYPE_W),
    ("metric", SEL_COL_METRIC, _DATASET_METRIC_W),
    (_COL_PRESENCE_KEY, SEL_COL_PRESENCE, _DATASET_PRESENCE_W),
)

# Row keys for the non-registry state rows (never mark/filter targets).
_LOADING_ROW_KEY = "_loading"
_NO_MATCH_ROW_KEY = "_no_match"
_REGISTRY_ERROR_ROW_KEY = "_registry_error"

# Per-cell rich Text styles: semantic theme tokens only (the 08-06
# idiom — the glyph carries meaning under NO_COLOR, color is the
# redundant channel).
_STYLE_DIM = "$text-muted"
_STYLE_MARK = "bold $accent"
_STYLE_PRESENCE_PASS = "$success"
_STYLE_PRESENCE_FAIL = "bold $error"
_STYLE_PRESENCE_UNKNOWN = "$text-muted"


def _truncate(text: Text, width: int) -> Text:
    """Ellipsis-truncate one rich Text in place to the width (Rich's own
    measurement — never hand-rolled width math)."""
    text.truncate(width, overflow="ellipsis", pad=False)
    return text


def _cell(value: object, width: int, style: "str | None" = None) -> Text:
    """One DataTable cell: plain text, ellipsis-truncated to the width."""
    return _truncate(
        Text(str(value), style=style) if style else Text(str(value)), width,
    )


def _size_text(value: object) -> str:
    """One model size: ``396.0`` renders as ``396``; absent renders blank.

    The repo data convention (missing = empty string, never null/0) — the
    registries service maps an absent ``size (M)`` to ``0.0``.
    """
    if not value:
        return ""
    return format(value, "g")


def _presence_cell(data: SelectionData, key: str) -> Text:
    """One presence cell from the 08-04 data — render only.

    The four statuses map to the contract formats: present carries the
    thousands-separated exact counts, missing the missing word, unknown
    the gap-filler copy, and the n_audit-absent column state renders the
    documented copy in every cell (SEL-04 boundary: the service already
    decided missing-vs-present; the screen formats only).
    """
    if not data.audit_available:
        return Text(SEL_N_AUDIT_MISSING, style=_STYLE_PRESENCE_FAIL)
    presence = data.presence.get(key)
    if presence is None or presence.status not in (
        PRESENCE_PRESENT, PRESENCE_MISSING,
    ):
        return Text(SEL_PRESENCE_UNKNOWN, style=_STYLE_PRESENCE_UNKNOWN)
    if presence.status == PRESENCE_MISSING:
        return Text(SEL_PRESENCE_MISSING, style=_STYLE_PRESENCE_FAIL)
    train, dev, test = presence.rows or (0, 0, 0)
    return Text(
        SEL_PRESENCE_PRESENT.format(
            train=f"{train:,}", dev=f"{dev:,}", test=f"{test:,}",
        ),
        style=_STYLE_PRESENCE_PASS,
    )


def _key_cell(key: str, status: "dict | None", width: int,
              accent_style: str) -> Text:
    """One key cell with the D-10 custom badge — render only.

    Custom entries carry the diamond prefix on the key cell: bold +
    accent when enabled, dim (with the disabled suffix) when disabled —
    the glyph + weight channel carries the meaning under NO_COLOR, the
    color is the redundant channel. Official rows render the bare key
    (the badge, never position, marks custom entries).

    Probe-pinned on 8.2.8 (the 09-03 nav-bar fact): rich Text SPANS
    styled with a Textual ``$token`` crash the render path
    (MissingStyle) — only whole-text styles resolve tokens — so the
    accent span carries the caller-resolved live theme accent and the
    disabled spans use rich's native ``dim``.
    """
    if not status or not status.get("custom"):
        return _cell(key, width)
    if status.get("enabled", True):
        return _truncate(Text.assemble(
            Text(f"{SEL_CUSTOM_BADGE} ", style=accent_style), Text(key),
        ), width)
    return _truncate(Text.assemble(
        Text(f"{SEL_CUSTOM_BADGE} ", style="dim"),
        Text(key),
        Text(SEL_DISABLED_SUFFIX, style="dim"),
    ), width)


def _preset_label(option: PresetOption) -> str:
    """The menu label for one preset option (derived ids map to copy)."""
    if option.kind == "custom":
        return option.name or option.id
    return {
        "tier-1": SEL_PRESET_TIER_1,
        "tier-2": SEL_PRESET_TIER_2,
        "all": SEL_PRESET_ALL,
    }.get(option.id, option.id)


# ===== Modals (ModalScreen — app/screen bindings blocked, Pitfall 11) =====


class PresetModal(ModalScreen):
    """The preset picker: a SelectionList of the derived + custom presets.

    SelectionList per the UI-SPEC Auto-Selected Default #13; the operator
    highlights a preset and presses enter (a toggle-to-selected in the
    widget's own semantics) — the first toggle applies the preset and
    closes the modal. The empty-customs entry renders as a dim line with
    the save-flow hint.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, options: Sequence[PresetOption],
                 customs_empty: bool, load_error: "str | None",
                 on_apply: "Callable[[PresetOption], None]", **kwargs):
        super().__init__(**kwargs)
        self._options = tuple(options)
        self._customs_empty = customs_empty
        self._load_error = load_error
        self._on_apply = on_apply

    def compose(self) -> ComposeResult:
        with Vertical(id="preset-box", classes="modal-box"):
            if self._load_error:
                yield Static(self._load_error, id="preset-load-error")
            yield SelectionList(
                *(Selection(_preset_label(option), option)
                  for option in self._options),
                id="preset-list",
            )
            if self._customs_empty:
                yield Static(SEL_PRESET_NO_CUSTOMS, id="preset-no-customs")
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#preset-box", Vertical).border_title = (
            SEL_PRESET_TITLE
        )

    def on_selection_list_selection_toggled(
            self, event: SelectionList.SelectionToggled) -> None:
        """A toggle applies the toggled preset and closes (first toggle)."""
        self.dismiss()
        self._on_apply(event.selection.value)


class TemplateMenuModal(ModalScreen):
    """The template menu: import / export / tier-convert (ListView)."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, on_choice: "Callable[[str], None]", **kwargs):
        super().__init__(**kwargs)
        self._on_choice = on_choice

    def compose(self) -> ComposeResult:
        with Vertical(id="template-menu-box", classes="modal-box"):
            yield ListView(
                ListItem(Static(SEL_TEMPLATE_MENU_IMPORT), id="tpl-import"),
                ListItem(Static(SEL_TEMPLATE_MENU_EXPORT), id="tpl-export"),
                ListItem(Static(SEL_TEMPLATE_MENU_TIERS), id="tpl-tiers"),
                id="template-menu-list",
            )
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#template-menu-box", Vertical).border_title = (
            SEL_TEMPLATE_TITLE
        )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Route the chosen menu entry; the menu dismisses itself."""
        action = {
            "tpl-import": "import",
            "tpl-export": "export",
            "tpl-tiers": "tiers",
        }.get(str(event.item.id))
        self.dismiss()
        if action is not None:
            self._on_choice(action)


class PathInputModal(ModalScreen):
    """A titled path/name input modal with a fail-closed problem view.

    ``on_submit(path)`` returns None on success (the modal dismisses) or
    a problems sequence — the modal then renders the numbered collect-all
    list and stays open (nothing was applied; the operator escapes).
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, title: str, placeholder: str,
                 on_submit: "Callable[[str], Sequence[tuple[str, str]] | None]",
                 **kwargs):
        super().__init__(**kwargs)
        self._title = title
        self._placeholder = placeholder
        self._on_submit = on_submit

    def compose(self) -> ComposeResult:
        with Vertical(id="path-input-box", classes="modal-box"):
            yield Input(placeholder=self._placeholder, id="path-input")
            yield Static("", id="path-problems")
            yield Footer()

    def on_mount(self) -> None:
        box = self.query_one("#path-input-box", Vertical)
        box.border_title = self._title
        self.query_one("#path-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Submit the value; render the problems when the call fails."""
        value = event.value.strip()
        if not value:
            return
        problems = self._on_submit(value)
        if problems:
            lines = [SEL_TEMPLATE_PROBLEMS.format(n=len(problems))]
            lines.extend(
                SEL_TEMPLATE_PROBLEM_LINE.format(
                    n=index + 1, location=location, message=message,
                )
                for index, (location, message) in enumerate(problems)
            )
            self.query_one("#path-problems", Static).update("\n".join(lines))
        else:
            self.dismiss()


class ConfirmModal(ModalScreen):
    """An Enter/Esc confirm over one message (the destructive gates).

    The message copy carries the key hints (the Copywriting Contract's
    confirm wording); the bindings themselves stay out of the footer.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "confirm", show=False),
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, message: str,
                 on_confirm: "Callable[[], None]", **kwargs):
        super().__init__(**kwargs)
        self._message = message
        self._on_confirm = on_confirm

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-box", classes="modal-box"):
            yield Static(self._message)
            yield Footer()

    def action_confirm(self) -> None:
        """Enter confirms (the message carries the key hints)."""
        self.dismiss()
        self._on_confirm()


class RowDetailModal(ModalScreen):
    """The row-detail drill-down: every card field, never elided.

    A wrapping, scrolling RichLog (the 08-06 drill-down pattern) renders
    the card's own fields verbatim — long values wrap, they are never
    elided (the table's ellipsis truncation is display-only).
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, entry_key: str, card: dict, **kwargs):
        super().__init__(**kwargs)
        self.entry_key = entry_key
        self._card = card

    def compose(self) -> ComposeResult:
        with Vertical(id="row-detail-box", classes="modal-box"):
            yield RichLog(wrap=True, id="row-detail-log")
            yield Footer()

    def on_mount(self) -> None:
        box = self.query_one("#row-detail-box", Vertical)
        box.border_title = self.entry_key
        log = self.query_one("#row-detail-log", RichLog)
        for field_name, value in self._card.items():
            log.write(f"{field_name}: {value}")


# ===== The screen =====


class SelectionScreen(Screen):
    """The selection screen: tables, filter, mark-set, presets, presence."""

    # D-13 slot 2 (the top-menu active-slot marker the nav bar reads).
    NAV_SLOT: ClassVar[int] = 2

    if TYPE_CHECKING:
        # Narrows MessagePump's ``App[object]`` to the composition root so
        # the app's own API (``below_minimum_grid``, WR-06) type-checks —
        # the runtime property is untouched (textual's own pattern, see
        # ``MessagePump.app``; no runtime import of tui.app — that would
        # be circular, the composition root imports this screen).
        app = getters.app(DnallmMarkTui)

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("space", "toggle_mark", SEL_MARK_LABEL),
        Binding("m", "switch_list", SEL_SWITCH_LABEL),
        Binding("p", "apply_preset", SEL_PRESET_LABEL),
        Binding("x", "open_templates", SEL_TEMPLATE_LABEL),
        Binding("s", "save_preset", SEL_SAVE_PRESET_LABEL),
        Binding("slash", "focus_filter", SEL_FILTER_KEY_LABEL,
                key_display="/"),
        # The 09-06 custom-entry actions (D-14/D-09): appended after the
        # mark/preset bindings and BEFORE the auxiliary actions — the
        # 09-UI-SPEC migration table's declaration order (the bottom
        # bar renders it; the clip policy drops least-primary first).
        Binding("w", "open_wizard", SEL_WIZARD_LABEL),
        Binding("e", "toggle_enabled", SEL_TOGGLE_LABEL),
        # The 10-05 enqueue action (D-14): between the e pair and the
        # auxiliary actions — the [d] keycap renders after the toggle
        # keycap and before the matrix keycap (one vocabulary with the
        # data-manager screen's d; labels live in tui/strings.py).
        Binding("d", "enqueue_dataset", SEL_ENQUEUE_LABEL),
        Binding("v", "open_matrix", SEL_MATRIX_LABEL),
        Binding("enter", "show_detail", ENV_DETAIL_LABEL, show=False),
        Binding("escape", "clear_filter", show=False),
        # The nav digits (09-03) — PLAIN per-screen bindings routed to
        # the app's ``nav`` action (never priority, Pattern 2); appended
        # AFTER the action bindings so the declaration order the bottom
        # bar renders is untouched. show=False: the top bar carries the
        # digit labels.
        Binding("1", "app.nav(1)", NAV_LABEL_ENV, show=False),
        Binding("2", "app.nav(2)", NAV_LABEL_SELECTION, show=False),
        Binding("3", "app.nav(3)", NAV_LABEL_DATA, show=False),
        Binding("4", "app.nav(4)", NAV_LABEL_RUN_CONFIG, show=False),
        Binding("5", "app.nav(5)", NAV_LABEL_MONITOR, show=False),
        Binding("6", "app.nav(6)", NAV_LABEL_ABOUT, show=False),
    ]

    class DataLoaded(Message):
        """The worker finished reading the registries + presence (D-03)."""

        def __init__(self, data: SelectionData) -> None:
            self.data = data
            super().__init__()

    class PresetMenuLoaded(Message):
        """The worker finished reading the preset menu (D-03, WR-04:
        both registries, the priorities file, and presets.json are
        reads — they never run on the event loop)."""

        def __init__(self, menu: PresetMenu) -> None:
            self.menu = menu
            super().__init__()

    def __init__(self,
                 selection_service: "SelectionServiceProtocol | None" = None,
                 marked_models: "set[str] | None" = None,
                 marked_tasks: "set[str] | None" = None,
                 custom_service: "CustomOnboardingBackend | None" = None,
                 queue_service: "SelectionQueueServiceProtocol | None" = None,
                 **kwargs):
        super().__init__(**kwargs)
        self._service: SelectionServiceProtocol = (
            selection_service if selection_service is not None
            else SelectionBackend()
        )
        # The 09-06 custom-onboarding seam (optional injection, real
        # default — existing Phase 8 fake injections run unchanged).
        self._custom: CustomOnboardingBackend = (
            custom_service if custom_service is not None
            else CustomOnboardingBackend()
        )
        # The 10-05 enqueue seam (optional injection, real default —
        # the D-14 shared queue; the app injects the app-level instance
        # through build_selection_screen so every screen enqueues into
        # ONE queue).
        self._queue: SelectionQueueServiceProtocol = (
            queue_service if queue_service is not None
            else SelectionQueueBackend()
        )
        # The shared app-state mark sets (SEL-01: marks live OUTSIDE the
        # table; the composition root injects the same live sets the
        # matrix screen reads).
        self._marked_models: set[str] = (
            marked_models if marked_models is not None else set()
        )
        self._marked_tasks: set[str] = (
            marked_tasks if marked_tasks is not None else set()
        )
        self._data: SelectionData | None = None
        self._view = _MODELS_VIEW
        self._query = ""
        # The parsed current query (empty terms = every entry). The
        # service owns the grammar; the screen only stores its output.
        self._parsed = self._service.parse_filter("")
        self._view_keys: frozenset[str] = frozenset()

    # ----- properties (the shared sets — Pilot assertions read these) -----

    @property
    def marked_models(self) -> "set[str]":
        """The live shared model mark set."""
        return self._marked_models

    @property
    def marked_tasks(self) -> "set[str]":
        """The live shared task mark set."""
        return self._marked_tasks

    # ----- layout -----

    def compose(self) -> ComposeResult:
        # The 09-03 migration retired the Textual Header/Footer (the two
        # shell bars own those rows now — row-neutral, D-16).
        yield TopMenuBar()
        with Horizontal(id="selection-title-bar"):
            yield Label(SEL_SCREEN_TITLE_MODELS, id="selection-screen-title")
            yield Label("", id="selection-status")
        with Horizontal(id="selection-filter-bar"):
            yield Label(SEL_FILTER_LABEL, id="selection-filter-label")
            yield Input(placeholder=SEL_FILTER_PLACEHOLDER,
                        id="selection-filter", compact=True)
            yield Label(SEL_FILTER_COUNT.format(n=0, total=0),
                        id="selection-filter-count")
        yield Label("", id="selection-filter-warning")
        yield DataTable(id="selection-table")
        yield BottomBar()

    def on_mount(self) -> None:
        """Compose the loading state, then the one exclusive read worker."""
        table = self.query_one("#selection-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        self._rebuild_rows()
        table.focus()
        self._update_status_line()
        self._load_data()

    # ----- the exclusive read worker (D-03: the only registry-read site) -----

    @work(exclusive=True, thread=True)
    def _load_data(self) -> None:
        """Read the registries + presence off the event loop."""
        data = self._service.load_selection_data()
        self.post_message(self.DataLoaded(data))

    @work(exclusive=True, thread=True)
    def _load_preset_menu(self) -> None:
        """Read the preset menu off the event loop (WR-04, the D-03
        worker contract): the menu build re-reads both registries, the
        priorities file, and presets.json — a cold cache or a
        network-mounted home must never stall the UI (T-08-07)."""
        menu = self._service.preset_menu()
        self.post_message(self.PresetMenuLoaded(menu))

    def on_selection_screen_data_loaded(self, message: DataLoaded) -> None:
        """Rows compose from the loaded snapshot (the loading row clears)."""
        self._data = message.data
        self._apply_filter()
        self._update_status_line()

    # ----- the app-forwarded queue events (10-05, D-11 live flip) -----

    def apply_queue_event(self, event: QueueEvent) -> None:
        """One app-forwarded queue event (the 10-04 generic forward):
        a done event IS a reconcile pass (the service's done gate,
        D-09), so it re-runs the existing exclusive snapshot worker —
        the overlay-wired presence view refreshes on the next render
        and the cursor row's cell flips in place. The table stays
        mounted; nothing navigates. A landed-but-mismatched dataset
        never flips (``reconciled_rows`` overlays done entries only —
        semantic 6)."""
        if event.state == "done":
            self._load_data()

    # ----- row composition (state rows vs data rows) -----

    def _rebuild_rows(self) -> None:
        """Rebuild the visible table for the current state.

        Marks live in the shared sets — a rebuild can never lose them
        (Pitfall 1); rows re-add with the SAME registry keys.
        """
        table = self.query_one("#selection-table", DataTable)
        columns = (
            _MODEL_COLUMNS if self._view == _MODELS_VIEW
            else _DATASET_COLUMNS
        )
        table.clear(columns=True)
        for column_key, header, width in columns:
            table.add_column(header, key=column_key, width=width)

        data = self._data
        if data is None:
            # the single loading row covers the registry/n_audit read
            # seam before rows compose (SEL-01 loading)
            self._view_keys = frozenset()
            self._add_state_row(
                table, SEL_LOADING_ROW, _LOADING_ROW_KEY, _STYLE_DIM,
            )
            self._update_count_readout(0, 0)
            return

        load_error = (
            data.models_load_error if self._view == _MODELS_VIEW
            else data.datasets_load_error
        )
        entries = self._view_entries()
        self._view_keys = frozenset(entry["key"] for entry in entries)
        if load_error is not None:
            # the registry-failure empty state names the path (SEL-01)
            self._add_state_row(
                table,
                SEL_REGISTRY_LOAD_FAILED.format(registry_path=load_error),
                _REGISTRY_ERROR_ROW_KEY, _STYLE_PRESENCE_FAIL,
            )
            self._update_count_readout(0, 0)
            return

        filtered = self._service.apply_filter(entries, self._parsed)
        if not filtered and entries:
            # zero matches render the documented no-match row with the
            # Esc-clear hint — never a blank table (SEL-01 empty edge)
            self._add_state_row(
                table, SEL_FILTER_NO_MATCH.format(total=len(entries)),
                _NO_MATCH_ROW_KEY, _STYLE_DIM,
            )
        else:
            for entry in filtered:
                table.add_row(*self._row_cells(entry), key=entry["key"])
        self._update_count_readout(len(filtered), len(entries))

    def _add_state_row(self, table: DataTable, text: str,
                       row_key: str, style: str) -> None:
        """One non-registry state row (the copy sits in the key column;
        the full value is stored untruncated — the table clips at the
        column budget, the copy itself is never elided)."""
        table.add_row("", Text(text, style=style), key=row_key)

    def _view_entries(self) -> list[dict]:
        """The active view's entries (registry order)."""
        data = self._data
        if data is None:
            return []
        return list(
            data.model_entries if self._view == _MODELS_VIEW
            else data.dataset_entries
        )

    def _row_cells(self, entry: dict) -> list:
        """The six cells of one data row, view-specific.

        The mark cell renders from the shared sets at add time; the
        spacebar updates it in place via ``update_cell`` afterwards.
        """
        key = entry["key"]
        marks = (
            self._marked_models if self._view == _MODELS_VIEW
            else self._marked_tasks
        )
        mark_cell = (
            Text("✓", style=_STYLE_MARK) if key in marks else ""
        )
        # Presence cells carry the FULL contract format — the DataTable
        # clips display at the column budget (no wrap, row height 1);
        # pre-truncation is only for the long registry keys below.
        # (_row_cells only composes with data loaded; the None branch is
        # the type narrowing, unreachable in practice.)
        data = self._data
        presence = (
            _presence_cell(data, key) if data is not None
            else Text(SEL_PRESENCE_UNKNOWN, style=_STYLE_PRESENCE_UNKNOWN)
        )
        badge_status = (
            data.custom_status.get(key) if data is not None else None
        )
        # The live theme's accent, resolved for the badge span (rich
        # spans cannot carry $token styles — probe-pinned, see _key_cell).
        accent_style = f"bold {self.app.current_theme.accent}"
        if self._view == _MODELS_VIEW:
            return [
                mark_cell,
                _key_cell(key, badge_status, _MODEL_KEY_W, accent_style),
                _cell(entry.get("type") or "", _MODEL_TYPE_W),
                _cell(entry.get("species") or "", _MODEL_SPECIES_W),
                _cell(_size_text(entry.get("size_m")), _MODEL_SIZE_W),
                presence,
            ]
        return [
            mark_cell,
            _key_cell(key, badge_status, _DATASET_KEY_W, accent_style),
            _cell(entry.get("category") or "", _DATASET_CATEGORY_W),
            _cell(entry.get("type") or "", _DATASET_TYPE_W),
            _cell(entry.get("metric") or "", _DATASET_METRIC_W),
            presence,
        ]

    # ----- readouts -----

    def _update_status_line(self) -> None:
        """The zero-one-many marked-counts readout (top-right) plus the
        conditional D-10 custom segment: with at least one LANDED custom
        entry a second dim segment appends the official/custom split
        counting both states (visible = counted — the counts derive from
        the management-read custom-status map, never the merged view);
        zero customs renders the exact Phase 8 line (byte-identical)."""
        data = self._data
        line = SEL_STATUS_LINE.format(
            n=len(self._marked_models),
            models_total=len(data.model_entries) if data else 0,
            m=len(self._marked_tasks),
            tasks_total=len(data.dataset_entries) if data else 0,
        )
        custom = data.custom_status if data else {}
        if not custom or data is None:
            self.query_one("#selection-status", Label).update(line)
            return
        custom_models = sum(
            1 for entry in data.model_entries
            if entry["key"] in custom
        )
        custom_datasets = sum(
            1 for entry in data.dataset_entries
            if entry["key"] in custom
        )
        segment = SEL_COUNT_CUSTOM_SEGMENT.format(
            official_models=len(data.model_entries) - custom_models,
            official_datasets=len(data.dataset_entries) - custom_datasets,
            custom_models=custom_models,
            custom_datasets=custom_datasets,
        )
        self.query_one("#selection-status", Label).update(Text.assemble(
            Text(line),
            # rich spans cannot carry $token styles (probe-pinned) — the
            # dim segment uses rich's native dim attribute
            Text(f" · {segment}", style="dim"),
        ))

    def _update_count_readout(self, visible: int, total: int) -> None:
        """The live (N/total) filter readout (right-aligned in the bar)."""
        self.query_one("#selection-filter-count", Label).update(
            SEL_FILTER_COUNT.format(n=visible, total=total)
        )

    def _render_filter_warning(self) -> None:
        """The dim unknown-axis warning line (valid terms still apply)."""
        label = self.query_one("#selection-filter-warning", Label)
        if not self._parsed.diagnostics:
            label.update("")
            return
        label.update("; ".join(
            SEL_FILTER_UNKNOWN_AXIS.format(
                axis=diagnostic.axis,
                axes=", ".join(diagnostic.known_axes),
            )
            for diagnostic in self._parsed.diagnostics
        ))

    def _apply_filter(self) -> None:
        """Re-apply the current query over the loaded data (rebuild)."""
        self._rebuild_rows()
        self._update_status_line()

    # ----- filter Input wiring -----

    def on_input_changed(self, event: Input.Changed) -> None:
        """Every keystroke re-parses and rebuilds (k9s type-to-filter)."""
        if event.input.id != "selection-filter":
            return
        self._query = event.value
        self._parsed = self._service.parse_filter(self._query)
        self._render_filter_warning()
        self._rebuild_rows()
        self._update_status_line()

    # ----- actions (user intent) -----

    def action_toggle_mark(self) -> None:
        """space: toggle the cursor row's mark (the mark column updates)."""
        table = self.query_one("#selection-table", DataTable)
        if not table.is_valid_coordinate(table.cursor_coordinate):
            # no cell under the cursor (a rowless table) — never marks
            # (coordinate_to_cell_key RAISES for invalid coordinates, it
            # never returns None; CR-03's crash class)
            return
        cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        row_key = cell_key[0]
        key = str(row_key.value)
        if key not in self._view_keys:
            return  # state rows (loading/no-match/error) never mark
        # T-09-13: marking a DISABLED custom row is blocked with the
        # warning — a mark the sweep can never see (the loader-level
        # skip) is refused at entry, never discovered at launch.
        disabled_status = self._custom_status_for(key)
        if disabled_status is not None and not disabled_status.get(
                "enabled", True):
            self.app.notify(
                SEL_DISABLED_MARK_WARNING.format(key=key),
                severity="warning",
            )
            return
        marks = (
            self._marked_models if self._view == _MODELS_VIEW
            else self._marked_tasks
        )
        if key in marks:
            marks.discard(key)
        else:
            marks.add(key)
        table.update_cell(
            row_key, _COL_MARK,
            Text("✓", style=_STYLE_MARK) if key in marks else "",
        )
        self._update_status_line()

    # ----- the custom-entry actions (09-06: w/e) -----

    def _cursor_key(self) -> "str | None":
        """The cursor row's registry key (None on state rows/empty)."""
        table = self.query_one("#selection-table", DataTable)
        if not table.is_valid_coordinate(table.cursor_coordinate):
            # coordinate_to_cell_key RAISES for invalid coordinates
            # (CR-03's crash class) — the guard is the None path
            return None
        key = str(table.coordinate_to_cell_key(
            table.cursor_coordinate)[0].value)
        return key if key in self._view_keys else None

    def _custom_status_for(self, key: "str | None") -> "dict | None":
        """The key's custom status (None = official or state row)."""
        if key is None or self._data is None:
            return None
        status = self._data.custom_status.get(key)
        if status is not None and status.get("custom"):
            return status
        return None

    def _on_custom_registry_changed(self) -> None:
        """A land/undo rewrote the user-owned registry — refresh the
        table/badge/count views through the existing exclusive worker."""
        self._load_data()

    def action_open_wizard(self) -> None:
        """w: open the new-entry wizard for the ACTIVE table's kind
        (D-14 — models table -> model wizard, datasets table -> dataset
        wizard; the menu carries no wizard item, the wizard is an
        action). A cursor custom row prefills from its landed entry (the
        D-12 re-record aid — the key rides along and the collect-all
        collision check forces the change); every other cursor state
        opens a blank form. The land-completion callback refreshes the
        table so the badge and the count segment appear."""
        if self._data is None:
            return
        key = self._cursor_key()
        prefill = None
        status = self._custom_status_for(key)
        if status is not None:
            entries, _error = self._custom.read_entries(self._view)
            entry = entries.get(key or "")
            if isinstance(entry, dict):
                prefill = {key: entry}
        self.app.push_screen(self._custom.build_wizard(
            kind=self._view,
            prefill=prefill,
            on_changed=self._on_custom_registry_changed,
        ))

    def action_toggle_enabled(self) -> None:
        """e: flip the cursor custom entry's enabled through the store's
        atomic seam (D-09 — the disable is loader-level run removal),
        toast the state pair, and refresh so the row's disabled state
        updates. An official row is a no-op with the honest toast —
        never silent; a state row (no registry key) stays silent like
        every other action."""
        key = self._cursor_key()
        if key is None:
            return
        status = self._custom_status_for(key)
        if status is None:
            self.app.notify(SEL_TOGGLE_OFFICIAL_NOOP)
            return
        enable = not status.get("enabled", True)
        if not self._custom.set_enabled(self._view, key, enable):
            # vanished between load and press, or an unreadable file —
            # refresh to the honest state rather than toasting a lie
            self._load_data()
            return
        self.app.notify(
            (SEL_TOGGLE_ENABLED_TOAST if enable
             else SEL_TOGGLE_DISABLED_TOAST).format(key=key),
        )
        self._load_data()

    def action_enqueue_dataset(self) -> None:
        """d: enqueue the cursor's MISSING dataset row into the shared
        download queue (10-05, D-14 — the SAME service call and the SAME
        outcome toasts as the data-manager screen's ``d``; one
        vocabulary). The outcome mapping mirrors the data-manager
        screen's pair exactly: enqueued -> the toast + the app-level
        kick; already_queued -> its toast; disabled (shape-D) ->
        ``DL_DISABLED_TOAST`` carrying the key (always diagnosable,
        R-02); cli_unavailable -> the probed-absent toast; unknown_key
        -> silent. The models view returns before any service call
        (models are not n_audit subjects — Phase 8 truth); a PRESENT
        row is a no-op with the honest toast, never silent and never a
        duplicate enqueue; state rows stay silent (the ``_cursor_key``
        None path). Enqueuing never navigates away."""
        if self._view == _MODELS_VIEW:
            return
        key = self._cursor_key()
        if key is None:
            return  # state rows (loading/no-match/error) never act
        presence = (
            self._data.presence.get(key) if self._data is not None else None
        )
        if presence is not None and presence.status == PRESENCE_PRESENT:
            self.app.notify(SEL_ENQUEUE_PRESENT_TOAST)
            return
        outcome = self._queue.enqueue(key)
        if outcome.action == "enqueued":
            self.app.notify(QUEUE_TOAST_ENQUEUED.format(key=key))
            self.app.kick_download_queue()
        elif outcome.action == "already_queued":
            self.app.notify(QUEUE_TOAST_ALREADY_QUEUED.format(key=key))
        elif outcome.action == "disabled":
            self.app.notify(
                DL_DISABLED_TOAST.format(key=key), severity="warning")
        elif outcome.action == "unknown":
            self.app.notify(
                DL_UNKNOWN_TOAST.format(
                    key=key, reason=outcome.reason_code or "unknown"),
                severity="warning")
        elif outcome.action == "cli_unavailable":
            self.app.notify(QUEUE_CLI_UNAVAILABLE, severity="error")
        elif outcome.action == "persist_failed":
            self.app.notify(
                QUEUE_PERSIST_FAILED_TOAST.format(key=key),
                severity="error")
        # unknown_key: silent return (the service already said it all)

    def action_switch_list(self) -> None:
        """m: toggle the model/dataset table (both mark sets persist)."""
        self._view = (
            _DATASETS_VIEW if self._view == _MODELS_VIEW else _MODELS_VIEW
        )
        self.query_one("#selection-screen-title", Label).update(
            SEL_SCREEN_TITLE_DATASETS
            if self._view == _DATASETS_VIEW else SEL_SCREEN_TITLE_MODELS
        )
        self._rebuild_rows()
        self._update_status_line()
        self.query_one("#selection-table", DataTable).focus()

    def action_focus_filter(self) -> None:
        """/: focus the filter Input (k9s type-to-filter)."""
        self.query_one("#selection-filter", Input).focus()

    def action_clear_filter(self) -> None:
        """esc: clear the filter and refocus the table."""
        self._query = ""
        self._parsed = self._service.parse_filter("")
        self.query_one("#selection-filter", Input).value = ""
        self._render_filter_warning()
        self._rebuild_rows()
        self._update_status_line()
        self.query_one("#selection-table", DataTable).focus()

    def action_apply_preset(self) -> None:
        """p: open the preset picker modal (the menu loads in the
        exclusive read worker — never on the event loop, WR-04)."""
        if self._data is None:
            return
        self._load_preset_menu()

    def on_selection_screen_preset_menu_loaded(
            self, message: PresetMenuLoaded) -> None:
        """The menu arrived from the worker: open the preset modal.

        Dropped below the minimum grid (WR-06): this push is ASYNC — the
        message can arrive while the min-size guard is the active screen
        (this screen sits beneath it, pump still running), and a modal
        pushed over the guard strands it at full size on grow (the
        restore pop fires only when the guard IS the top screen, WR-01).
        The operator re-presses ``p`` after growing back, the same
        degraded behavior ``action_help`` already has.
        """
        if self.app.below_minimum_grid:
            return  # below the minimum grid: no chrome over the guard
        menu = message.menu
        customs_empty = not any(
            option.kind == "custom" for option in menu.options
        )
        self.app.push_screen(PresetModal(
            options=menu.options,
            customs_empty=customs_empty,
            load_error=menu.load_error,
            on_apply=self._apply_preset,
        ))

    def _deliverable_keys(self, entries: "Sequence[dict]") -> frozenset[str]:
        """The registry keys a run can deliver — the loud-skip key set.

        Disabled customs stay visible in the table (the management read)
        but the loader excludes them, so they are NOT deliverable: a
        preset/template referencing one rides the Phase 8 unknown-key
        loud skip (warned, skipped — never a silently-unusable mark).
        """
        custom_status = self._data.custom_status if self._data else {}

        def _blocked(entry_key: str) -> bool:
            status = custom_status.get(entry_key)
            return bool(
                status and status.get("custom")
                and not status.get("enabled", True)
            )

        return frozenset(
            entry["key"] for entry in entries
            if not _blocked(entry["key"])
        )

    def _apply_preset(self, option: PresetOption) -> None:
        """Apply one preset with REPLACING semantics (SEL-02).

        The relevant set(s) are cleared then filled; keys absent from the
        loaded registries are skipped with the loud warning (registry
        evolution tolerance — recomputed against the live view so stale
        customs warn too, never silently dropped; a disabled custom key
        is equally undeliverable and rides the same loud skip).
        """
        model_keys = (
            self._deliverable_keys(self._data.model_entries)
            if self._data else frozenset()
        )
        task_keys = (
            self._deliverable_keys(self._data.dataset_entries)
            if self._data else frozenset()
        )
        unknown = [
            key for key in option.models if key not in model_keys
        ] + [
            key for key in option.tasks if key not in task_keys
        ]
        self._marked_models.clear()
        self._marked_models.update(
            key for key in option.models if key in model_keys
        )
        self._marked_tasks.clear()
        self._marked_tasks.update(
            key for key in option.tasks if key in task_keys
        )
        if unknown:
            self.app.notify(
                SEL_PRESET_UNKNOWN_KEYS.format(
                    n=len(unknown), keys=", ".join(unknown),
                ),
                severity="warning",
            )
        self.app.notify(SEL_PRESET_APPLIED.format(
            preset=_preset_label(option),
            n=len(self._marked_models),
            m=len(self._marked_tasks),
        ))
        self._rebuild_rows()
        self._update_status_line()
        self.query_one("#selection-table", DataTable).focus()

    def action_open_templates(self) -> None:
        """x: open the template menu modal."""
        if self._data is None:
            return
        self.app.push_screen(TemplateMenuModal(
            on_choice=self._on_template_choice,
        ))

    def _on_template_choice(self, action: str) -> None:
        """Route the chosen template menu entry to its input modal."""
        titles = {
            "import": SEL_TEMPLATE_MENU_IMPORT,
            "export": SEL_TEMPLATE_MENU_EXPORT,
            "tiers": SEL_TEMPLATE_MENU_TIERS,
        }
        self.app.push_screen(PathInputModal(
            title=titles[action],
            placeholder=SEL_TEMPLATE_PATH_PLACEHOLDER,
            on_submit={
                "import": self._submit_import,
                "export": self._submit_export,
                "tiers": self._submit_tiers,
            }[action],
        ))

    def _submit_import(self, path: str) -> "Sequence[tuple[str, str]] | None":
        """Import: validate collect-all; NOTHING applies on failure."""
        outcome = self._service.import_template(path)
        if not outcome.ok:
            return outcome.problems
        self._replace_marks(outcome.models, outcome.tasks)
        self.app.notify(SEL_TEMPLATE_IMPORTED.format(
            n=len(self._marked_models), m=len(self._marked_tasks),
        ))
        self._rebuild_rows()
        self._update_status_line()
        self.query_one("#selection-table", DataTable).focus()
        return None

    def _submit_export(self, path: str) -> "Sequence[tuple[str, str]] | None":
        """Export the current mark sets to the operator-chosen path."""
        try:
            self._service.export_template(
                path, sorted(self._marked_models), sorted(self._marked_tasks),
            )
        except ValueError as exc:
            # e.g. an empty selection cannot be exported (the service's
            # loud refusal) — surfaced in the modal, nothing written
            return ((path, str(exc)),)
        except OSError as exc:
            # an unwritable/invalid operator path (a parent that is a
            # file, a read-only location, a full disk) — fail closed in
            # the modal, the console never crashes (CR-02)
            return ((path, SEL_TEMPLATE_WRITE_FAILED.format(
                error=f"{type(exc).__name__}: {exc}",
            )),)
        self.app.notify(SEL_TEMPLATE_EXPORTED.format(path=path))
        return None

    def _submit_tiers(self, path: str) -> "Sequence[tuple[str, str]] | None":
        """Export the selection as a sweep_priorities tier list."""
        try:
            self._service.export_tiers(
                path, sorted(self._marked_models), sorted(self._marked_tasks),
            )
        except ValueError as exc:
            return ((path, str(exc)),)
        except OSError as exc:
            # the same fail-closed contract as the template export (CR-02)
            return ((path, SEL_TEMPLATE_WRITE_FAILED.format(
                error=f"{type(exc).__name__}: {exc}",
            )),)
        self.app.notify(SEL_TEMPLATE_EXPORTED.format(path=path))
        return None

    def _replace_marks(self, models: Iterable[str],
                       tasks: Iterable[str]) -> None:
        """Replace both mark sets, skipping keys unknown to the registry
        with the loud warning (the same loud-skip discipline as presets
        — disabled customs are equally undeliverable)."""
        model_keys = (
            self._deliverable_keys(self._data.model_entries)
            if self._data else frozenset()
        )
        task_keys = (
            self._deliverable_keys(self._data.dataset_entries)
            if self._data else frozenset()
        )
        unknown = [
            key for key in models if key not in model_keys
        ] + [
            key for key in tasks if key not in task_keys
        ]
        self._marked_models.clear()
        self._marked_models.update(
            key for key in models if key in model_keys
        )
        self._marked_tasks.clear()
        self._marked_tasks.update(key for key in tasks if key in task_keys)
        if unknown:
            self.app.notify(
                SEL_PRESET_UNKNOWN_KEYS.format(
                    n=len(unknown), keys=", ".join(unknown),
                ),
                severity="warning",
            )

    def action_save_preset(self) -> None:
        """s: save the current mark sets as a custom preset."""
        self.app.push_screen(PathInputModal(
            title=SEL_SAVE_PRESET_LABEL,
            placeholder=SEL_PRESET_NAME_PLACEHOLDER,
            on_submit=self._submit_save,
        ))

    def _submit_save(self, name: str) -> None:
        """An existing name confirms before the overwrite; else saves.

        The confirm push is deferred one refresh: the path modal
        dismisses itself (popping the TOP screen) immediately after this
        callback returns None, so the confirm must land on the stack
        AFTER that pop — pushing it here would dismiss the confirm
        instead of the input modal.
        """
        if name in self._service.custom_names():
            self.app.call_after_refresh(
                lambda name=name: self.app.push_screen(ConfirmModal(
                    message=SEL_PRESET_OVERWRITE_CONFIRM.format(name=name),
                    on_confirm=lambda: self._do_save(name),
                ))
            )
            return
        self._do_save(name)

    def _do_save(self, name: str) -> None:
        """Persist the current mark sets under the name + toast."""
        try:
            self._service.save_preset(
                name, sorted(self._marked_models), sorted(self._marked_tasks),
            )
        except OSError as exc:
            # an unwritable config root (a read-only location, a full
            # disk) — a warning toast, never a crash (CR-02: the save
            # flow degrades like every other write path)
            self.app.notify(
                SEL_PRESET_SAVE_FAILED.format(
                    error=f"{type(exc).__name__}: {exc}",
                ),
                severity="warning",
            )
            self.query_one("#selection-table", DataTable).focus()
            return
        self.app.notify(SEL_PRESET_SAVED.format(
            name=name,
            n=len(self._marked_models),
            m=len(self._marked_tasks),
        ))
        self.query_one("#selection-table", DataTable).focus()

    def action_open_matrix(self) -> None:
        """v: push the read-only matrix overview (the auxiliary view).

        The matrix receives THIS screen's loaded snapshot plus the same
        live shared mark sets (render-only; read-only by its absent
        bindings). Not pushed before the data loads — an empty snapshot
        has nothing to show.
        """
        if self._data is None:
            return
        self.app.push_screen(MatrixScreen(
            data=self._data,
            marked_models=self._marked_models,
            marked_tasks=self._marked_tasks,
        ))

    def action_show_detail(self) -> None:
        """enter (table unfocused): drill into the cursor row's card."""
        table = self.query_one("#selection-table", DataTable)
        if not table.is_valid_coordinate(table.cursor_coordinate):
            # no cell under the cursor (a rowless table) — nothing to
            # drill into (coordinate_to_cell_key RAISES, never None)
            return
        cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        self._open_detail(str(cell_key[0].value))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """enter on the focused table (its native select event)."""
        self._open_detail(str(event.row_key.value))

    def _open_detail(self, key: str) -> None:
        """Open the row-detail modal for a registry entry's full card."""
        entry = self._find_entry(key)
        if entry is None:
            return  # state rows have no detail — no-op
        self.app.push_screen(RowDetailModal(
            entry_key=key, card=entry.get("card") or {},
        ))

    def _find_entry(self, key: str) -> "dict | None":
        """The entry (either list) for a registry key, else None."""
        if self._data is None:
            return None
        for entry in self._data.model_entries + self._data.dataset_entries:
            if entry["key"] == key:
                return entry
        return None
