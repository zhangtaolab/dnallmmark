"""
app.py — ``DnallmMarkTui``, the console's composition root (Phase 8, 08-02
skeleton; 08-03 tracer wiring; 08-06 full root).

Composition root ONLY: the app wires the title, the stylesheet, the
screen registry, the app-level bindings, the service injection seam, the
help modal, and the min-size guard — nothing else. Zero check/mark/
filter logic ever lands here (binding constraint 5: TUI orchestrates,
never computes); every later Phase 8-12 plan adds screens and services
onto this root.

08-06 wiring:

- Service injection: the constructor accepts an optional
  ``env_check_service`` override (the ``EnvCheckServiceProtocol`` seam —
  tier-2 Pilot tests inject deterministic fakes so no real kernel, GPU
  or otherwise, ever executes in CI, D-03); None means the real service.
- App-level bindings (08-UI-SPEC Keyboard map): ``q`` opens the quit
  confirmation from any screen (261016-v0z: no exit without an explicit
  operator confirm — no live sweep opens the Y/N quit modal, a live
  sweep the kill/detach ExitModal; the inherited ctrl+q default is
  declared explicitly and routes through the same guard; 261017-cdr:
  ``ctrl+c`` exits from any BASE-SCREEN focus through the same confirm
  chain — an ``on_event`` intercept, so it survives the filter-input
  focus trap while the restored capital Q types as a plain letter
  again, and action_quit guards against exit-modal stacking);
  ``?`` opens the help modal listing every active binding with
  its Chinese label from ``tui/strings.py`` (I18N-01).
- Min-size guard (08-UI-SPEC Terminal Contract): below 80x24 the app
  renders ONLY the min-size message with the current dimensions — a
  dedicated screen swapped in on mount/resize and popped when the
  terminal grows back; nothing else is visible while it is on top.

08-07 wiring:

- The selection seam: ``selection_service`` (the same Protocol-injection
  pattern) plus the shared app-state mark sets — every selection/matrix
  screen is built through ``build_selection_screen`` so the sets are the
  same live instances (SEL-01 persistence).

10-04 wiring (the D-02/SC5 execution spine):

- The queue seam: the constructor accepts ``download_queue_service``
  (the driver-surface Protocol; None builds the real
  ``DownloadQueueService``). The app owns ONE shared instance — the
  driver worker, the data-manager screen, and (in 10-05) the
  selection/env screens all mutate the same queue.
- The driver worker: ONE exclusive ``@work(exclusive=True, thread=True)``
  loop over ``claim_next -> run_task -> post QueueEventMessage`` that
  RETURNS when no pending entry remains — ``wait_for_complete`` can
  never hang. ``kick_download_queue`` is guarded by a deterministic busy
  flag (set synchronously in kick, cleared in the worker finally) so a
  second enqueue never cancels an in-flight download (T-10-04-02).
- Boot resume (D-06): ``boot_resume_queue`` (service.load + kick iff
  pending entries exist) is scheduled ONLY by ``tui/__main__.main`` —
  never by ``App.on_mount``; test-constructed apps stay provably inert
  (T-10-04-03).
"""

import inspect
import json
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, ClassVar, Protocol, cast

from rich.text import Text
from textual import events, work
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Vertical
from textual.message import Message
from textual.screen import ModalScreen, Screen
from textual.widgets import Footer, Input, Static
from textual.worker import get_current_worker

from tui import strings as S
from tui.screens.about import AboutScreen
from tui.screens.data_manager import DataManagerBackend, DataManagerScreen
from tui.screens.env_check import EnvCheckScreen, EnvCheckServiceProtocol
from tui.screens.monitor import (
    MonitorBackend,
    MonitorLauncherProtocol,
    MonitorScreen,
    MonitorServiceProtocol,
)
from tui.screens.nav import NAV_SLOT_BY_INDEX, binding_row
from tui.screens.run_config import (
    LauncherBackend,
    LauncherServiceProtocol,
    RunConfigBackend,
    RunConfigScreen,
    RunConfigServiceProtocol,
)
from tui.screens.selection import (
    SelectionQueueBackend,
    SelectionScreen,
    SelectionServiceProtocol,
)
from tui.services import settings
from tui.services.download_queue import (
    KIND_MODEL,
    KIND_ZENODO_BUNDLE,
    DownloadQueueService,
    QueueEntry,
    QueueEvent,
)

# 08-UI-SPEC Terminal Contract: the minimum grid. Below this, only the
# min-size message renders (re-checked on every resize).
MIN_WIDTH = 80
MIN_HEIGHT = 24


class HelpModal(ModalScreen):
    """The ``?`` help modal: every active binding, Chinese labels.

    ModalScreen so app/screen bindings do not fire while it is open
    (Pitfall 11); the rows arrive pre-built from the app (the binding
    descriptions ARE the strings-module copy — no copy lives here).
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", S.APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, rows: "list[tuple[str, str]]", **kwargs):
        super().__init__(**kwargs)
        self._rows = list(rows)

    def compose(self) -> ComposeResult:
        with Vertical(id="help-box"):
            for key, label in self._rows:
                # A rich Text content object is never markup-parsed — the
                # keycap renders as literal text. Key displays may be
                # markup-reserved characters (the selection screen's "/"
                # filter keycap parsed as a broken auto-closing tag and
                # crashed the console — the row must stay literal).
                yield Static(Text(S.APP_HELP_ROW.format(key=key, label=label)))
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#help-box", Vertical).border_title = S.APP_HELP_TITLE


class MinSizeScreen(Screen):
    """The below-minimum terminal state: ONLY the min-size message.

    A plain Screen (not a ModalScreen) so the screen beneath is not
    rendered at all — the message with the current dimensions is the
    entire visible surface (08-UI-SPEC Terminal Contract).
    """

    def __init__(self, width: int, height: int, **kwargs):
        super().__init__(**kwargs)
        self._width = width
        self._height = height

    def compose(self) -> ComposeResult:
        yield Static(self._message(), id="min-size-message")

    def _message(self) -> str:
        return S.APP_MIN_SIZE_MESSAGE.format(w=self._width, h=self._height)

    def update_dimensions(self, width: int, height: int) -> None:
        """Keep the displayed dimensions current on further below-min resizes."""
        self._width = width
        self._height = height
        self.query_one("#min-size-message", Static).update(self._message())


class ExitModal(ModalScreen):
    """The D-06 exit triple: [enter] detach (default) / [k] kill / [esc]
    return — pushed by ``action_quit`` when a live sweep exists.

    WR-05 (phase-11 stale-refresh review): the modal carries EVERY live
    root as a sequence (a bare str normalizes to a one-root tuple — the
    single-root call shape keeps working); [k] kills and [enter]
    detaches ALL of them before the app exits — no sweep survives a
    kill-and-quit the operator believed terminal, and no GPU stays
    occupied by a sweep believed killed.

    The kill path blocks up to the launcher's kill grace (SIGTERM ->
    poll -> SIGKILL escalation) — the brief wait the plan names; the
    app is exiting either way. 11-06 formats the done/total fields
    with the absent marker (the launcher carries no progress; the
    monitor's live counts land in 11-07; the multi-root form drops
    them — per-root counts from one attached root would mix sources).

    WR-02 (08 review, fix batch 261017-klw): the kill fan-out NO LONGER
    runs on the event loop — [k] delegates to the app's exit-kill
    worker (the monitor.py mon-kill discipline: blocking kill polling
    belongs on a worker thread, never on the loop), the exit lands on
    the ExitKillsDone completion, and a per-root broad guard keeps
    every root attempted even when one kill raises. Edge semantics:
    [k] is a COMMITTED intent — after k, esc no longer cancels the
    exit (the completion message still arrives and exits; before WR-02
    esc-after-k was unreachable anyway because k froze the loop).

    The 261017-dnr affordance ruling (DNR-4): the Footer now ADVERTISES
    the triple the copy names — enter/k render with keycaps lifted
    verbatim from the message wording, and the message's
    [enter]/[k]/[esc] tokens render bold (the cdr Rich-Text pattern).
    Visibility only: enter's default fire is BY DESIGN from Phase 11
    (detach-and-exit stays the advertised-and-real default; the
    coordinator's keep-semantics ruling).
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        # DNR-4 (261017-dnr): the triple is VISIBLE — enter/k carry
        # show=True with keycaps whose wording is lifted VERBATIM from
        # the LNC_EXIT_MESSAGE copy (they say exactly what the message
        # says), so the three-key Footer matches the copy that already
        # names them. Visibility only: enter remains the detach-and-exit
        # DEFAULT (the Phase-11 design — the coordinator's keep-
        # semantics ruling); key/action semantics byte-unchanged.
        Binding("enter", "detach_quit", S.LNC_EXIT_DETACH_KEYCAP,
                show=True),
        Binding("k", "kill_quit", S.LNC_EXIT_KILL_KEYCAP, show=True),
        Binding("escape", "dismiss", S.APP_MODAL_BACK_LABEL),
    ]

    def __init__(self, roots, launcher, message: str, **kwargs):
        super().__init__(**kwargs)
        if isinstance(roots, str):
            roots = (roots,)   # the single-root call shape
        self._roots = tuple(roots)
        self._launcher = launcher
        self._message = message

    def compose(self) -> ComposeResult:
        # DNR-4 (261017-dnr): the [enter]/[k]/[esc] tokens render BOLD
        # via the Rich Text API (the 261017-cdr QuitConfirmModal
        # pattern — Text content is never markup-parsed, so the literal
        # bracket tokens stay literal; 'bold' is a Rich core style, no
        # $token MissingStyle hazard on the Static path). highlight_words
        # mutates the Text IN PLACE and returns the count (cdr-probed
        # rich text.py:639 -> int) — never chained, two-step only. BOTH
        # message forms (LNC_EXIT_MESSAGE / LNC_EXIT_MESSAGE_MULTI)
        # carry the same triple tokens, so one tuple covers each render.
        message = Text(self._message)
        message.highlight_words(("[enter]", "[k]", "[esc]"), style="bold")
        with Vertical(id="exit-modal-box", classes="modal-box"):
            yield Static(message)
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#exit-modal-box", Vertical).border_title = (
            S.LNC_EXIT_TITLE)

    def action_detach_quit(self) -> None:
        """[enter] the default: drop every live handle (each sweep
        survives, resume-safe by the trainer_state marker contract),
        then exit."""
        for root in self._roots:
            self._launcher.detach(root)
        self.app.exit()

    def action_kill_quit(self) -> None:
        """[k] SIGTERM every live process group, then exit — dispatched
        to the app's exit-kill worker (WR-02): the blocking kill polling
        runs off the event loop and the exit lands on the completion
        message (never before every root was attempted). No loop, no
        synchronous ``self.app.exit()`` here."""
        # WR-02: the composition root owns the exit-kill worker; the
        # cast narrows MessagePump's ``App[object]`` (the RunConfigScreen
        # getters.app idiom — a cast because DnallmMarkTui is this
        # module's own class, defined below the modal).
        cast("DnallmMarkTui", self.app).request_kill_and_exit(
            tuple(self._roots))


class QuitConfirmModal(ModalScreen):
    """The 261016-v0z no-sweep quit confirm: ``y`` exits, ``n``/``esc``
    cancel — no key combination kills the console without an explicit
    operator confirmation (the maintainer's 2026-10-16 ruling).

    ``enter`` is STRUCTURALLY inert: the key is bound to a documented
    no-op action (the LaunchConfirmModal EHC-2 idiom — a stray
    double-enter can never quit). Corrected inertness map (261017-cdr):
    plain ``q`` stays chain-cut under the modal (Pitfall 11 — the modal
    binding chain blocks the non-priority app binding), while the
    priority ``ctrl+q`` DOES fire over the modal and re-enters
    action_quit, whose exit-family guard (CDR-4) returns immediately —
    nothing observable happens; ``ctrl+c`` delegates to the modal-cut
    chain and is likewise inert (CDR-2). The 261017-cdr prominence
    ruling (CDR-3): the message's [Y]/[N] tokens render BOLD via the
    Rich Text API (``Text.highlight_words`` — Text content is never
    markup-parsed, so the literal bracket tokens stay literal; no
    markup-string ambiguity), and the y/n bindings carry show=True so
    the modal's Footer renders the y/n keycaps beside esc. Deliberately
    NOT the ExitModal surface: with a live sweep the kill/detach/cancel
    triple stays, and its ``[enter]`` detach default is that modal's
    own design — the two exit surfaces intentionally differ.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        # CDR-3 (261017-cdr): the answer keys are VISIBLE — y/n carry
        # show=True with the LNC_EXIT_CONFIRM_YES/NO descriptions, so
        # the modal's Footer renders them beside esc (QuitConfirmModal
        # is in the L-toggle remap registry; the keycaps re-derive on
        # language switch). enter stays show=False — the inert no-op is
        # never advertised.
        Binding("y", "confirm_quit", S.LNC_EXIT_CONFIRM_YES, show=True),
        Binding("n", "dismiss", S.LNC_EXIT_CONFIRM_NO, show=True),
        Binding("escape", "dismiss", S.APP_MODAL_BACK_LABEL),
        Binding("enter", "enter_inert", show=False),
    ]

    def __init__(self, message: str, **kwargs):
        super().__init__(**kwargs)
        self._message = message

    def compose(self) -> ComposeResult:
        # CDR-3: the [Y]/[N] tokens are bolded through the Rich Text
        # API, never markup strings — Text content is never
        # markup-parsed (the HelpModal literal-keycap precedent), so
        # the bracket tokens stay literal, and 'bold' is a Rich core
        # style (no $token MissingStyle hazard on the Static path).
        # highlight_words mutates the Text IN PLACE and returns the
        # count (probed in the installed rich: text.py:639 -> int) —
        # never chained.
        message = Text(self._message)
        message.highlight_words(("[Y]", "[N]"), style="bold")
        with Vertical(id="quit-confirm-box", classes="modal-box"):
            yield Static(message)
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#quit-confirm-box", Vertical).border_title = (
            S.LNC_EXIT_TITLE)

    def action_confirm_quit(self) -> None:
        """``y`` — the only key that confirms the quit (the ExitModal
        tail idiom: exit straight, no dismiss needed)."""
        self.app.exit()

    def action_enter_inert(self) -> None:
        """Enter is deliberately inert on the quit confirm (EHC-2
        extended to the exit surface by the 261016-v0z ruling: enter
        can never confirm a quit — a stray double-enter must not kill
        the console; the live-sweep ExitModal keeps its own ``[enter]``
        detach default by design — the two exit surfaces intentionally
        differ)."""
        # documented no-op: the enter binding lands here


class MonitorSwitchRequested(Message):
    """D-13: switch to the monitor screen with the newly launched sweep
    attached (posted by ``sweep_launched`` so the async screen switch
    rides the message loop — the queue-forward precedent)."""

    def __init__(self, root: str) -> None:
        self.root = root
        super().__init__()


class ExitKillsDone(Message):
    """WR-02 (08 review, fix batch 261017-klw): the app-level exit-kill
    worker attempted EVERY live root (each under its own broad guard) —
    the console may now exit. Posted UNCONDITIONALLY on worker
    completion, so a ``kill_sweep`` that raises can never strand a
    killed-but-unexited console: the exit lands on this message, never
    before every root was attempted."""

    def __init__(self) -> None:
        super().__init__()


class QueueDriverProtocol(Protocol):
    """The driver-surface queue Protocol the app consumes (10-04).

    The structural seam the tier-2 Pilot fakes conform to: the app only
    ever drives the queue (load/claim/run) — the screen-facing surface
    (snapshot reads, enqueue toasts, drill-down seams) lives behind
    ``DataManagerServiceProtocol`` in ``tui/screens/data_manager``.
    """

    def load(self) -> "str | None":
        """Tolerantly load the persisted queue state (D-06)."""

    def entries(self) -> "list[QueueEntry]":
        """The immutable entry snapshots, in file order."""

    def claim_next(self) -> "QueueEntry | None":
        """Claim the head pending entry (None when the queue is idle)."""

    def run_task(self, key: str, run_id: str,
                 progress_cb: Callable[..., None] | None
                 = None) -> QueueEvent:
        """Execute one claimed task; NEVER raises (the service boundary).
        The callback receives ``(key, percent)`` while no rate parses
        and ``(key, percent, speed)`` once one does (EHC-4 additive)."""


class QueueEventMessage(Message):
    """One completed queue task (driver worker thread -> event loop).

    Carries the driver generation it belongs to (WR-02) — the handler
    drops posts from a superseded generation. Behind the kick busy-guard
    two drivers can never overlap, so the drop path guards only the
    teardown-time exclusive cancellation.
    """

    def __init__(self, event: QueueEvent, generation: int) -> None:
        self.event = event
        self.generation = generation
        super().__init__()


class QueueProgressMessage(Message):
    """One live progress tick (driver worker thread -> event loop).

    Throttled to (percent, speed) PAIR changes at BOTH layers (the
    service's parser dedupes within a task; the driver dedupes across
    posts — EHC-4, 261015-ehc: a stalled percent with a streaming rate
    is a real tick); percent None is the indeterminate contract (the
    screen renders the indeterminate glyph, never a fabricated number).
    ``speed`` is the verbatim parsed rate token (None = the honest
    percent-only fallback).
    """

    def __init__(self, key: str, percent: "int | None",
                 generation: int, speed: "str | None" = None) -> None:
        self.key = key
        self.percent = percent
        self.generation = generation
        self.speed = speed
        super().__init__()


class QueueStalledMessage(Message):
    """The driver STOPPED because a claim could not persist (CR-02).

    A refusal-None out of ``claim_next`` (an unwritable state rail over
    a pending entry — the WR-04 absorbed refusal) exits the driver
    instead of re-driving into the claim->refuse->recheck livelock; the
    entry stays pending, the busy flag releases, and this message
    surfaces the stall through the persist-failure toast vocabulary.
    Carries the driver generation (dropped when superseded, WR-02).
    """

    def __init__(self, key: str, diagnostic: str,
                 generation: int) -> None:
        self.key = key
        self.diagnostic = diagnostic
        self.generation = generation
        super().__init__()


# =====================================================================
# The L language toggle's binding-description remap (261015-ehc, EHC-1)
# =====================================================================

#: The app-local Binding-carrying screen classes (the sys.modules sweep
#: below covers tui/screens/*; these four live HERE).
_APP_LOCAL_BINDING_SCREENS: "tuple[type, ...]" = (
    HelpModal, MinSizeScreen, ExitModal, QuitConfirmModal)


def _binding_owning_screen_classes() -> "list[type]":
    """Every class carrying a BINDINGS list the console renders.

    The tui/screens/* modules are swept through sys.modules (automatic:
    any future screen module joins coverage with zero registry edits) —
    translation of a description never re-declared happens through
    ``translate_value``'s byte-equality lookup, so extra classes are
    harmless no-ops.
    """
    classes: dict[str, type] = {
        f"{cls.__module__}.{cls.__qualname__}": cls
        for cls in _APP_LOCAL_BINDING_SCREENS
    }
    for module_name, module in list(sys.modules.items()):
        if module is None or not module_name.startswith("tui.screens"):
            continue
        for attr in vars(module).values():
            if (isinstance(attr, type) and issubclass(attr, Screen)
                    and "BINDINGS" in vars(attr)):
                classes[f"{attr.__module__}.{attr.__qualname__}"] = attr
    return list(classes.values())


def remap_binding_descriptions(from_lang: str, to_lang: str) -> None:
    """Translate every rendered binding description between languages.

    textual 8.2.8 probe-pinned: ``Binding.description`` is FROZEN
    (FrozenInstanceError), so each described entry is REBUILT IN PLACE —
    a new Binding carrying the original key/action/show/key_display/
    priority and the translated description (tuple shorthands rebuild
    their third element). Walks the app's own BINDINGS plus every
    Binding-owning screen class (app-local + the tui/screens sweep), so
    a screen constructed AFTER a toggle renders the active language too.

    Also called by ``tui/__main__``'s boot load (class declarations
    freeze at import in the import-time language; the persisted language
    needs the same remap before the first render).
    """
    owners: list[Any] = [DnallmMarkTui]
    owners.extend(_binding_owning_screen_classes())
    for owner in owners:
        bindings = owner.__dict__.get("BINDINGS")
        if not isinstance(bindings, list):
            continue
        for index, binding in enumerate(bindings):
            if isinstance(binding, Binding) and binding.description:
                bindings[index] = Binding(
                    binding.key,
                    binding.action,
                    S.translate_value(
                        binding.description, from_lang, to_lang),
                    show=binding.show,
                    key_display=binding.key_display,
                    priority=binding.priority,
                )
            elif (isinstance(binding, tuple) and len(binding) >= 3
                    and binding[2]):
                bindings[index] = (
                    (*binding[:2],
                     S.translate_value(binding[2], from_lang, to_lang),
                     *binding[3:]))


class DnallmMarkTui(App):
    """DNALLM-Mark operator console — composition root."""

    # I18N-01: operator-facing copy lives ONLY in tui/strings.py; screens
    # reference constants, never inline copy.
    TITLE = S.APP_TITLE

    # tui/styles.tcss — semantic Textual theme tokens only (08-UI-SPEC
    # Color contract; no hardcoded hex — the optional brand theme is
    # deliberately not landed, default theme tokens satisfy the contract).
    CSS_PATH = "styles.tcss"

    # App-level bindings: q opens the quit confirm from any screen
    # (unhandled keys bubble widget -> screen -> app, so a focused
    # DataTable does not swallow q; 261016-v0z — never a direct exit);
    # ? opens the help modal; L toggles the language (EHC-1, 261015-ehc —
    # uppercase L, no screen binds L/l; a focused Input consumes the
    # keystroke as text, which is the correct k9s behavior). The ClassVar
    # annotations mirror the App base declarations verbatim (the 08-03
    # RUF012 resolution) — framework-read class constants.
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", S.APP_QUIT_LABEL),
        # 261016-v0z: the DECLARED mirror of the inherited App default
        # (textual 8.2.8 app.py: ctrl+q -> quit, show=False,
        # priority=True). Probe-pinned merge semantics (dom.py
        # _merge_bindings walks reversed(cls.__mro__), per-key
        # last-writer-wins): this derived same-key entry REPLACES the
        # base entry entirely, and the action dispatch already resolved
        # to the overridden action_quit (App-level bindings run their
        # action on the app namespace) — the entry makes the inherited
        # surface DECLARED and drift-proof while behaving identically
        # (live sweep -> the ExitModal, none -> the quit confirm; never
        # a direct exit on any path). show=False keeps it out of the
        # footer/binding_row (the help row is declared manually in
        # _binding_rows); system=True preserves the framework default's
        # key-panel exclusion; priority=True preserves its
        # fires-over-focused-Input reach (ctrl+q cannot type into an
        # Input, so the priority-binding typing prohibition holds).
        Binding("ctrl+q", "quit", show=False, priority=True,
                system=True),
        Binding("question_mark", "help", S.APP_HELP_LABEL, key_display="?"),
        Binding("L", "toggle_language", S.APP_LANGUAGE_TOGGLE_LABEL),
    ]

    # Screen registry (key-switched full screens, 08-UI-SPEC Auto-Selected
    # Default #4): the env-check screen is the opening screen. The
    # selection/matrix screens (08-07) deliberately do NOT join this
    # zero-arg registry: they share the live app-state mark sets, so they
    # are built through build_selection_screen / the pushing screen —
    # a slot-built screen would carry fresh sets and silently lose marks.
    # The about screen (09-03, D-13 slot 6) is STATELESS — it joins the
    # zero-arg registry as permitted (the only live state it touches is
    # the derived snapshot inside one worker run).
    # Classes instantiate lazily on first name access; name-based access
    # builds the default (real) service — the injected-service path is
    # get_default_screen below.
    SCREENS: ClassVar[dict[str, Callable[[], Screen[Any]]]] = {
        "env_check": EnvCheckScreen,
        "about": AboutScreen,
    }

    def __init__(self, env_check_service: EnvCheckServiceProtocol | None = None,
                 selection_service: SelectionServiceProtocol | None = None,
                 download_queue_service: QueueDriverProtocol | None = None,
                 run_config_service: RunConfigServiceProtocol | None = None,
                 launcher_service: LauncherServiceProtocol | None = None,
                 monitor_service: MonitorServiceProtocol | None = None,
                 monitor_launcher: MonitorLauncherProtocol | None = None):
        """Compose the console with injectable services.

        Args:
            env_check_service: optional service override for the env-check
                screen (the tier-2 Pilot seam — tests inject deterministic
                fakes so no real kernel executes in CI, D-03). None means
                the real service (EnvCheckBackend over the 08-04 module).
            selection_service: optional service override for the selection
                screen (the same seam pattern, 08-07). None means the real
                service (SelectionBackend over the 08-04/08-05 modules).
            download_queue_service: optional override for the shared
                download-queue service (the 10-04 seam — the driver loop
                AND the data-manager screen run over this ONE instance).
                None means the real ``DownloadQueueService``.
            run_config_service: optional override for the run-config
                screen's service (the 11-06 seam — tests inject fakes so
                no registry read or XDG write executes). None means the
                real service, built per screen in the factory.
            launcher_service: optional override for the shared launcher
                service (the 11-06 seam). None builds the real
                ``LauncherBackend`` over ONE app-owned ``SweepLauncher``
                — the run-config gate, the ExitModal, and (11-07) the
                monitor's live-root scans all read this instance.
            monitor_service: optional override for the monitor screen's
                scan service (the 11-07 seam — tests inject fakes so no
                artifact-tree read executes). None builds the real
                ``MonitorBackend`` over the shared launcher.
            monitor_launcher: optional override for the monitor screen's
                re-run launcher seam (the 11-07 Pilot seam; None passes
                the shared launcher instance).
        """
        super().__init__()
        self._env_check_service = env_check_service
        self._selection_service = selection_service
        self._download_queue: QueueDriverProtocol = (
            download_queue_service if download_queue_service is not None
            else DownloadQueueService()
        )
        self._run_config_service = run_config_service
        # The app-owned shared launcher (the ExitModal predicate + the
        # 11-06 gate + 11-07's auto-nav/monitor read ONE registry).
        self._launcher: LauncherServiceProtocol = (
            launcher_service if launcher_service is not None
            else LauncherBackend()
        )
        # The 11-07 monitor seams: the scan service + the re-run
        # launcher face (both default to the shared registry).
        self._monitor_service = monitor_service
        self._monitor_launcher = monitor_launcher
        # The app-owned monitor screen (ONE cached instance — attach
        # state and the D-13 launch injections survive navigation).
        self._monitor_screen: MonitorScreen | None = None
        # The driver state (T-10-04-02): the busy flag is set
        # SYNCHRONOUSLY in kick and cleared in the worker's drain exit,
        # so two rapid enqueues can never start (and exclusive-cancel) a
        # second driver while a download is in flight. The generation
        # tags every driver post (WR-02). The lock makes the flag's
        # check-and-set (kick) atomic against the drain-side
        # release-and-recheck (WR-02's lost-wakeup guard).
        self._queue_busy = False
        self._queue_generation = 0
        self._queue_busy_lock = Lock()
        # The shared app-state mark sets (SEL-01): marks live HERE, never
        # inside a DataTable — the selection screen and the matrix screen
        # read the same live sets, so filter rebuilds, table switches,
        # and screen pushes can never lose them.
        self._marked_models: set[str] = set()
        self._marked_tasks: set[str] = set()
        # The active min-size guard screen (None = terminal at/above the
        # minimum grid).
        self._min_size_screen: MinSizeScreen | None = None

    def get_default_screen(self) -> EnvCheckScreen:
        """Open the console on the env-check screen (with the wired service)."""
        return EnvCheckScreen(env_check_service=self._env_check_service)

    def build_selection_screen(self) -> SelectionScreen:
        """Build the selection screen over the shared mark sets + queue.

        The screen factory (08-07): the injected-or-real service plus the
        SAME live mark-set instances every selection/matrix screen
        shares — constructed here, never through a zero-arg SCREENS slot
        (a slot-built screen would carry fresh sets and silently lose
        the SEL-01 persistence guarantee). 10-05 (D-14): the factory
        also bridges the app-level SHARED queue instance into the
        screen's enqueue seam (the SelectionQueueBackend two-Protocol
        bridge — the build_data_manager_screen rationale), so the
        selection screen's ``d``, the data-manager screen, and the
        driver all mutate ONE queue.
        """
        return SelectionScreen(
            selection_service=self._selection_service,
            marked_models=self._marked_models,
            marked_tasks=self._marked_tasks,
            queue_service=SelectionQueueBackend(self._download_queue),
        )

    def build_data_manager_screen(self) -> DataManagerScreen:
        """Build the data-manager screen over the SHARED queue service.

        The 10-04 factory (the build_selection_screen rationale): the
        screen's Backend adapter wraps the SAME app-level queue instance
        the driver worker drives, so an enqueue from the screen, a boot
        resume, and a driver event all mutate one queue — a zero-arg
        SCREENS slot would build a second service and silently fork the
        state.
        """
        return DataManagerScreen(
            data_service=DataManagerBackend(self._download_queue))

    def build_run_config_screen(self) -> RunConfigScreen:
        """Build the run-config screen over the injected-or-real
        services + the SHARED launcher.

        The 11-06 factory (the build_data_manager_screen rationale):
        the launcher is the app-owned shared instance so the screen's
        gate, the app's ExitModal, and (11-07) the monitor all read ONE
        live-sweep registry — a zero-arg SCREENS slot would build a
        second launcher and silently fork the live-sweep truth. The
        run-config service builds per screen (stateless adapter; the
        Pilot seam injects the fake here).
        """
        return RunConfigScreen(
            run_config_service=(self._run_config_service
                                if self._run_config_service is not None
                                else RunConfigBackend()),
            launcher_service=self._launcher,
        )

    def build_monitor_screen(self) -> MonitorScreen:
        """Build the monitor screen over the shared launcher + the
        injected-or-real scan service (the 11-07 factory).

        ONE cached instance (unlike the other rebuild-per-nav
        factories): the monitor's attach state and the D-13 launch
        injections are session state — navigating away and back must
        never drop the attached sweep. The screen re-composes on
        re-mount; the state survives on the instance.
        """
        if self._monitor_screen is None:
            self._monitor_screen = MonitorScreen(
                monitor_service=(
                    self._monitor_service
                    if self._monitor_service is not None
                    else MonitorBackend(launcher=self._launcher)),
                launcher_service=(
                    self._monitor_launcher
                    if self._monitor_launcher is not None
                    else self._launcher),
            )
        return self._monitor_screen

    # ===== Digit navigation (D-13, 09-03) =====

    async def action_nav(self, slot: int) -> None:
        """Route one top-menu digit press (the nav bars only render).

        Live slots switch the screen (switch_screen replaces the top of
        the stack — the depth never grows under digit navigation);
        placeholder slots are NEVER silent: the toast names the
        delivering phase (D-13). A press targeting the screen already
        active is a no-op (no redundant rebuild, no worker restart).
        """
        target = NAV_SLOT_BY_INDEX.get(slot)
        if target is None:
            return
        if target.phase is not None:
            self.notify(S.NAV_PLACEHOLDER_TOAST.format(n=target.phase))
            return
        current = self.screen
        if target.target == "env_check":
            if isinstance(current, EnvCheckScreen):
                return
            await self.switch_screen(self.get_default_screen())
        elif target.target == "selection":
            if isinstance(current, SelectionScreen):
                return
            await self.switch_screen(self.build_selection_screen())
        elif target.target == "data_manager":
            if isinstance(current, DataManagerScreen):
                return
            await self.switch_screen(self.build_data_manager_screen())
        elif target.target == "run_config":
            if isinstance(current, RunConfigScreen):
                return
            await self.switch_screen(self.build_run_config_screen())
        elif target.target == "monitor":
            if isinstance(current, MonitorScreen):
                return
            await self.switch_screen(self.build_monitor_screen())
        elif target.target == "about":
            if isinstance(current, AboutScreen):
                return
            # the stateless zero-arg SCREENS slot (D-13; the injected
            # service path does not exist for about — tests pin env roots)
            await self.switch_screen("about")

    # ===== The download-queue execution spine (10-04, D-02/SC5) =====

    def kick_download_queue(self) -> None:
        """Start the driver iff it is idle (the T-10-04-02 busy guard).

        The check-and-set runs under the busy lock (WR-02) — atomic
        against the worker's drain-side release-and-recheck, so a kick
        racing the drain either sees the flag released and starts the
        next driver itself, or is a guarded no-op while the SAME worker
        absorbs the entry it was racing. The flag is set SYNCHRONOUSLY
        here — before any await — so two rapid enqueues (or an enqueue
        racing boot resume) can never both reach ``run_download_queue``:
        an exclusive restart would CANCEL the in-flight download's
        worker thread mid-task. The worker's drain exit clears the flag
        under the same lock exactly when the queue has drained
        (``claim_next`` returned None and no pending entry exists), so
        a later enqueue restarts it.
        """
        with self._queue_busy_lock:
            if self._queue_busy:
                return
            self._queue_busy = True
            self._queue_generation += 1
        self.run_download_queue()

    @work(exclusive=True, thread=True, exit_on_error=False)
    def run_download_queue(self) -> None:
        """Drive the serial queue until it drains (never on the loop).

        One claim -> one task -> one event post, repeated; RETURNS when
        ``claim_next`` finds no pending entry — ``wait_for_complete`` can
        therefore never hang on an idle queue. All subprocess/HTTP I/O
        lives inside the service's ``run_task`` (D-02: spawn/reap/parse
        in this OS thread, never in-process, never on the event loop —
        SC5). Progress crosses as a second message throttled to
        integer-percent changes; every post carries the driver
        generation (WR-02).
        """
        worker = get_current_worker()
        generation = self._queue_generation
        # EHC-4: the throttle compares (percent, speed) PAIRS — a
        # percent stalled while the rate streams still posts.
        last_pair: dict[str, tuple[int | None, str | None]] = {}

        def on_progress(key: str, percent: "int | None",
                        speed: "str | None" = None) -> None:
            # throttle: the service dedupes within a task; this dedupes
            # the post itself across tasks/retries of the same key
            if (percent is not None
                    and last_pair.get(key) == (percent, speed)):
                return
            last_pair[key] = (percent, speed)
            self.post_message(
                QueueProgressMessage(key, percent, generation, speed))

        try:
            while True:
                if worker.is_cancelled:
                    return
                entry = self._download_queue.claim_next()
                if entry is None:
                    # CR-02: a None answer is EITHER a drained queue or
                    # a REFUSED claim (the WR-04 absorbed persist
                    # failure over a still-pending entry). Driving on
                    # after a refusal would re-claim and re-refuse
                    # forever (the livelock) — the driver exits and
                    # surfaces the stall instead. The signal is read
                    # through the optional service seam (fakes without
                    # it never refuse).
                    refusal_getter = getattr(
                        self._download_queue, "last_claim_refusal", None)
                    refusal = (refusal_getter()
                               if refusal_getter is not None else None)
                    # WR-02 (the lost-wakeup guard): an enqueue+kick that
                    # lands between this drain scan and the busy-flag
                    # release sees the flag still set and is a guarded
                    # no-op — the entry would strand with no driver. The
                    # release-and-recheck below is ATOMIC against kick's
                    # check-and-set (the shared lock): if the pending
                    # entry is already visible HERE, this SAME worker
                    # keeps driving it (no restart, no second driver —
                    # D-04 serial stays guaranteed); if not, the flag is
                    # released and any concurrent kick starts the next
                    # driver itself.
                    with self._queue_busy_lock:
                        if self._queue_generation != generation:
                            return  # a successor owns the flag
                        pending = False
                        try:
                            pending = any(
                                item.state == "pending"
                                for item
                                in self._download_queue.entries())
                        except Exception:  # noqa: BLE001 — never raise here
                            pending = False
                        if pending and refusal is None:
                            continue    # keep driving THIS worker
                        self._queue_busy = False
                    if refusal is not None:
                        self.post_message(QueueStalledMessage(
                            refusal[0], refusal[1], generation))
                    return  # drained (or stalled) — the no-hang contract
                if worker.is_cancelled:
                    return
                # the claim tick: one indeterminate post flips the row
                # to its downloading state before any percent parses
                # (unparsed CLI output may never fire a real tick)
                self.post_message(
                    QueueProgressMessage(entry.key, None, generation))
                event = self._download_queue.run_task(
                    entry.key,
                    f"driver-{generation}-{entry.key}",
                    progress_cb=on_progress,
                )
                self.post_message(QueueEventMessage(event, generation))
        finally:
            with self._queue_busy_lock:
                if self._queue_generation == generation:
                    self._queue_busy = False
                # a superseded generation owns the flag now — never
                # clear a successor's guard (the release-and-recheck
                # below is the only drain-side clear)

    def boot_resume_queue(self) -> None:
        """D-06 boot resume: load the persisted queue; kick iff work
        is pending (a restart with queued work resumes automatically).

        Scheduled ONLY by ``tui/__main__.main`` via ``call_later`` —
        never by ``App.on_mount``: test-constructed apps stay provably
        inert (T-10-04-03 — no real download can ever start from a Pilot
        test), while the operator's console resumes on boot.
        """
        self._download_queue.load()
        if any(entry.state == "pending"
               for entry in self._download_queue.entries()):
            self.kick_download_queue()

    def on_queue_event_message(self, message: QueueEventMessage) -> None:
        """One task finished: flip-toast on done, forward to the screens.

        The done state IS the reconcile pass (the service's done gate,
        D-09), so done is exactly the D-11 presence-flip moment — the
        app-level QUEUE_FLIP_TOAST fires here. WR-03: the forward
        reaches EVERY screen in the stack that defines
        ``apply_queue_event`` — while any modal is open (the drill-down,
        the cancel confirms, the selection screen's preset/confirm
        modals) ``self.screen`` is the modal, and a top-of-stack-only
        forward would be a silent no-op, losing the row refresh and the
        D-11 flip until some unrelated action reloaded the screen.
        """
        if message.generation != self._queue_generation:
            return  # a superseded driver's late post (WR-02)
        event = message.event
        if event.state == "done":
            # IN-03: the bundle row's flip toast formats the operator-
            # facing bundle label (the ONE name the z-enqueue toast
            # uses), never the raw queue key; a model done carries the
            # model-lane wording (MLC-01 — no reconcile leg exists on
            # that lane, so the dataset lane's reconciled-claim wording
            # must never render for it)
            if event.kind == KIND_ZENODO_BUNDLE:
                self.notify(S.QUEUE_FLIP_TOAST.format(key=S.DL_BUNDLE_TASK_NAME))
            elif event.kind == KIND_MODEL:
                self.notify(S.QUEUE_FLIP_TOAST_MODEL.format(key=event.key))
            else:
                self.notify(S.QUEUE_FLIP_TOAST.format(key=event.key))
        for screen in self.screen_stack:
            apply_event = getattr(screen, "apply_queue_event", None)
            if apply_event is not None:
                apply_event(event)

    def on_queue_progress_message(self, message: QueueProgressMessage) -> None:
        """One live progress tick: forward to every handler screen in
        the stack (the WR-03 modal rule — an open modal must not freeze
        the running row's cells)."""
        if message.generation != self._queue_generation:
            return  # a superseded driver's late post (WR-02)
        for screen in self.screen_stack:
            apply_progress = getattr(
                screen, "apply_queue_progress", None)
            if apply_progress is not None:
                apply_progress(message.key, message.percent,
                               message.speed)

    def on_queue_stalled_message(self, message: QueueStalledMessage) -> None:
        """The driver stalled on a persist-refused claim (CR-02): the
        operator-facing toast — the queue is wedged until the state rail
        is fixed; the entry stays pending for the fixed-rail re-kick."""
        if message.generation != self._queue_generation:
            return  # a superseded driver's late post (WR-02)
        self.notify(
            S.QUEUE_PERSIST_DRIVER_TOAST.format(key=message.key),
            severity="error")

    # ===== The D-13 launch -> auto-nav integration (11-07) =====

    def sweep_launched(self, root: str, cells: int) -> None:
        """A slot-4 launch succeeded: record the plan, attach the new
        sweep, and switch to the monitor screen (the toast has already
        fired on the run-config side).

        The record + attach land synchronously; the screen switch rides
        a posted message (the queue-forward precedent — the async
        ``switch_screen`` needs the message loop, never a bare fire).
        """
        screen = self.build_monitor_screen()
        screen.note_launch(root, cells)
        if not self.below_minimum_grid:
            self.post_message(MonitorSwitchRequested(root))

    async def on_monitor_switch_requested(
            self, message: MonitorSwitchRequested) -> None:
        """Complete the D-13 jump: switch to the (already attached)
        monitor screen (async handler — the message loop owns the
        coroutine, no bare task firing)."""
        screen = self._monitor_screen
        if screen is None or self.screen is screen:
            return
        if self.below_minimum_grid:
            return  # no chrome over the guard (WR-06)
        await self.switch_screen(screen)

    # ===== Min-size guard (08-UI-SPEC Terminal Contract) =====

    def on_mount(self) -> None:
        """Check the grid once at mount (resize events re-check live)."""
        # textual 8.2.8 probe-pinned fact (09-03): the boot screen is
        # appended to the stack WITHOUT push bookkeeping, so switching
        # away from it (switch_screen/pop_screen's _pop_result_callback)
        # raises IndexError on the empty callback list. Register the one
        # missing result-callback entry here so digit navigation can
        # switch away from the opening screen.
        self.screen._push_result_callback(self.screen, None)
        if self.size.width and self.size.height:
            self._apply_min_size_guard(self.size.width, self.size.height)

    def on_resize(self, event: events.Resize) -> None:
        """Re-evaluate the guard on every resize (shrink AND grow)."""
        self._apply_min_size_guard(event.size.width, event.size.height)

    def _apply_min_size_guard(self, width: int, height: int) -> None:
        """Below 80x24, swap in the min-size screen; at/above, restore.

        The guard screen is pushed as a plain Screen, so while it is on
        top NOTHING else renders (the message is the whole surface); a
        modal beneath it (e.g. an open drill-down) survives the round
        trip — the pop restores the exact stack. The pop itself only
        fires when the guard IS the active screen: popping the top screen
        unconditionally would remove a modal that legitimately sits
        beneath the guard and strand the guard itself (WR-01).
        """
        below = width < MIN_WIDTH or height < MIN_HEIGHT
        guard = self._min_size_screen
        if below:
            if guard is None:
                guard = MinSizeScreen(width, height)
                self._min_size_screen = guard
                self.push_screen(guard)
            else:
                # still below the minimum, different dimensions — keep
                # the displayed width/height current
                guard.update_dimensions(width, height)
        elif guard is not None:
            self._min_size_screen = None
            if self.screen is guard:
                self.pop_screen()

    @property
    def below_minimum_grid(self) -> bool:
        """True while the min-size guard screen is up (no chrome may open).

        The guard state every ASYNC chrome push must check (WR-06): a
        message-handler push can fire while the guard is the active
        screen (the screen beneath keeps pumping), and a modal pushed
        over the guard strands it at full size on grow — the restore pop
        fires only when the guard IS the top screen (WR-01).
        """
        return self._min_size_screen is not None

    # ===== Actions (app-level) =====

    async def action_quit(self) -> None:
        """The guarded exit (the 261016-v0z contract: q and ctrl+q
        ALWAYS confirm before exit — no key combination kills the console
        without an explicit operator confirmation; 261017-cdr adds
        ctrl+c as the any-focus trigger through the same chain).

        Legs, in order: (0) an exit-family modal already top returns
        IMMEDIATELY (the CDR-4 stacking guard — see below); (1) below
        the minimum grid NOTHING fires — no chrome over the guard
        (WR-06) and never an unguarded exit (the latent fall-through
        where a live sweep + below-min grid previously reached
        ``self.exit()`` is closed); (2) a live sweep
        (``live_sweeps`` non-empty OR the monitor's attached sweep
        running — a CLI-launched sweep the TUI did not spawn) pushes the
        ExitModal (kill/detach/cancel, default detach) instead of
        quitting, byte-unchanged — no double confirm on top of the
        operator's own kill/detach choice; (3) with neither, the
        QuitConfirmModal (y-only, EHC-2; n/esc cancel) — the old direct
        ``self.exit()`` tail is gone. 11-07 threads the monitor's live
        done/total into the ExitModal message (absent markers when
        unknown — never fabricated).

        WR-05 (phase-11 stale-refresh review): with MULTIPLE live
        sweeps the modal names EVERY live root (full resolved paths —
        basenames collide) with the count via LNC_EXIT_MESSAGE_MULTI
        (done/total dropped: per-root counts from one attached root
        would mix sources) and [k]/[enter] act on ALL of them; one live
        root keeps the single-root form byte-identical, and the
        attached-running-only path (a CLI-launched sweep the launcher
        never spawned) keeps today's single-root form unchanged (its
        kill stays the documented launcher-noop). WR-03 (08 review,
        fix batch 261017-klw): one TUI root PLUS a DIFFERENT attached
        running root joins the MULTI form — the modal names EVERY live
        root (a CLI-launched sweep never survives a kill-and-exit
        silently, no unnamed sweep keeps the GPU on detach-and-exit).
        Async — the App base declares the coroutine signature (ty LSP).
        """
        if isinstance(self.screen, (ExitModal, QuitConfirmModal)):
            # CDR-4 (261017-cdr, the P9/vxr finding): the priority
            # ctrl+q binding fires over open modals (the full
            # binding-chain walk) and re-entered here, stacking a
            # second exit modal over an open one — return instead, so
            # no key combination can push a second exit-family modal
            # while one is top. KillConfirmModal/E2PhraseModal (and
            # every launch-side/selection modal) are deliberately OUT
            # of the guard set: kill != exit, and a quit issued over
            # them is a NEW legitimate intent — the exit modal stacks
            # over them and esc peels back.
            return
        if self.below_minimum_grid:
            return  # below the minimum grid: nothing fires, never an exit
        roots = self._launcher.live_sweeps()
        attached_running = False
        done = S.CFG_VALUE_ABSENT
        total = S.CFG_VALUE_ABSENT
        attached_root = ""
        if self._monitor_screen is not None:
            (attached_running, attached_root,
             done, total) = self._monitor_screen.attached_running_counts()
        if roots or attached_running:
            # WR-03: an attached running root that is NOT one of the
            # launcher's roots (CLI-launched — the exact case
            # attached_running exists to catch) must not be silently
            # dropped by the single-root form below
            attached_extra = attached_running and attached_root not in roots
            if len(roots) > 1 or (roots and attached_extra):
                combined = tuple(roots) + (
                    (attached_root,) if attached_extra else ())
                self.push_screen(ExitModal(
                    roots=combined, launcher=self._launcher,
                    message=S.LNC_EXIT_MESSAGE_MULTI.format(
                        n=len(combined), roots=", ".join(combined))))
                return
            root = roots[0] if roots else attached_root
            self.push_screen(
                ExitModal(roots=(root,), launcher=self._launcher,
                          message=S.LNC_EXIT_MESSAGE.format(
                              done=done, total=total,
                              root=Path(root).name)))
            return
        self.push_screen(QuitConfirmModal(message=S.LNC_EXIT_CONFIRM))

    async def on_event(self, event: events.Event) -> None:
        """261017-cdr (CDR-2, the maintainer's 2026-10-17 revision):
        ctrl+c is the ANY-FOCUS primary exit — the intercept replaces
        the 261016-vxr uppercase-Q one (a capital Q is a plain typing
        letter again), routing through the v0z confirm chain so the
        quit works from ANY base-screen focus, including the
        filter-input focus trap.

        WR-01 (08 review, fix batch 261017-klw) — the copy delegation:
        when the focused widget is an ``Input`` holding a NON-EMPTY
        selection, ctrl+c delegates through ``super().on_event`` to
        textual 8.2.8's own ``ctrl+c,super+c -> copy`` Input binding
        (``_input.py:139``) — base-screen Inputs get copy parity with
        modal Inputs (the 08-REVIEW asymmetry: inside modals the key
        already delegates and copy works; the loss was base-screen
        only). The delegation fires ONLY for
        ``isinstance(self.focused, Input)`` with truthy
        ``selected_text`` while the top screen is non-modal — an empty
        selection, a non-Input focus, or no focus still routes ctrl+c
        into the action_quit chain exactly as today, and ctrl+c under
        modals stays inert (the not-modal guard precedes everything).
        NOT an exit bypass: a selection-holding Input + ctrl+c is the
        EHC-ratified explicit operator gesture on selected text.

        Why an ``on_event`` intercept and NOT a declared binding with
        the priority flag (probe-pinned on textual 8.2.8): a priority
        ctrl+c would deliver the same focused-Input reach (ctrl combos
        are never consumed by an Input), but the priority path walks
        the FULL binding chain, so it would also fire under EVERY open
        modal (the P9 mechanism) and stack an exit modal over the
        wizard, the E2' phrase modal, or a picker. The intercept with
        the explicit ``not is_modal`` guard delivers the same
        base-screen reach with base-screen-only semantics: under every
        modal the key delegates to ``super().on_event`` and the
        modal-cut binding chain, where the inherited ctrl+c help_quit
        default is non-priority and therefore chain-cut — inert, no
        notify. On base screens the intercept consumes the key before
        the machinery, so the inherited default never fires anywhere
        and no replacement binding is declared (it could never fire:
        shadowed on base screens, chain-cut under modals — dead code).
        Below the minimum grid the intercept routes into action_quit,
        whose first leg returns — the same behavior as q (the guard
        screen is a plain non-modal Screen). zellij's default config
        passes ctrl+c through to the pane program. Every other event
        delegates to the App base unchanged (lowercase q keeps its
        Input semantics; a capital Q types everywhere again).
        """
        if (isinstance(event, events.Key) and event.key == "ctrl+c"
                and self.screen is not None
                and not self.screen.is_modal):
            # WR-01: a selection-holding Input owns the key first —
            # delegate so the Input's own copy binding fires
            focused = self.focused
            if isinstance(focused, Input) and focused.selected_text:
                await super().on_event(event)
                return  # delegated: the Input's copy binding owns the key
            await self.action_quit()
            return  # consumed: never forwarded, never a notify
        await super().on_event(event)

    # ===== The exit-kill worker (WR-02, 08 review fix batch 261017-klw) =====

    def request_kill_and_exit(self, roots) -> None:
        """The ExitModal's [k] seam (WR-02): kill every live root OFF
        the event loop, then exit on completion.

        The modal never runs ``kill_sweep`` itself — each call blocks
        up to the launcher's kill grace (SIGTERM -> poll -> SIGKILL),
        and the multi-root form would stack those freezes serially on
        the loop (N roots that ignore SIGTERM = N x grace of a frozen
        console). This is the monitor.py mon-kill discipline brought to
        the exit path: the fan-out runs on one exclusive thread worker
        and the exit lands on the ``ExitKillsDone`` message — never
        before every root was attempted.
        """
        self._exit_kill_worker(tuple(roots))

    @work(exclusive=True, thread=True, group="exit-kill",
          exit_on_error=False)
    def _exit_kill_worker(self, roots: "tuple[str, ...]") -> None:
        """SIGTERM-fan-out over every live root, then post completion.

        Per-root broad guard: a raising ``kill_sweep`` is logged
        (timestamped print, the pipeline's logging convention — the app
        is exiting, the log rail is not a consumer here) and the
        fan-out CONTINUES — every root must be attempted even when one
        raises. ``ExitKillsDone`` posts UNCONDITIONALLY after the loop
        (also in the structural never-exit floor's belt-and-suspenders
        shape: ``exit_on_error=False`` AND an internal broad guard —
        tests/tui/test_work_site_hardening.py's pin).
        """
        for root in roots:
            try:
                self._launcher.kill_sweep(root)
            except Exception as exc:  # noqa: BLE001 — every root attempted
                print(
                    f"[{datetime.now().astimezone().strftime(
                        '%Y-%m-%d %H:%M:%S')}] "
                    f"exit-kill failed for {root}: "
                    f"{type(exc).__name__}: {exc}")
                continue
        self.post_message(ExitKillsDone())

    def on_exit_kills_done(self, message: ExitKillsDone) -> None:
        """Every root was attempted — the committed [k] intent
        completes: exit now (the only exit on the kill path; esc after
        k cannot cancel this, per the modal's WR-02 edge note)."""
        self.exit()

    def action_help(self) -> None:
        """The ``?`` key: the help modal over the current screen.

        Suppressed below the minimum grid: no chrome may open over the
        guard (a modal pushed there would be popped instead of the guard
        on grow, stranding the console on the min-size screen at full
        size — WR-01).
        """
        if self.below_minimum_grid:
            return  # below the minimum grid: no chrome over the guard
        self.push_screen(HelpModal(self._binding_rows()))

    def _binding_rows(self) -> "list[tuple[str, str]]":
        """Every active binding as (display key, active-language label) rows.

        App bindings first, then the active screen's — the help surface
        always reflects the live key map (k9s-style contextual help).
        The descriptions are the strings-module constants wired into the
        BINDINGS declarations — no copy is redefined here (I18N-01).
        The row projection itself is ``tui.screens.nav.binding_row``
        (moved there in 09-03 so the nav bars and the help modal share
        the ONE key-map source).
        """
        rows = [row for row in map(binding_row, self.BINDINGS)
                if row is not None]
        # 261016-v0z: the app-level exit keys whose bindings stay
        # show=False/system — the declared ctrl+q mirror (the inherited
        # default made explicit) — get their help rows HERE, after the
        # app bindings and before the screen's; resolved live from the
        # strings registry so the L toggle re-derives them. 261017-cdr:
        # the ctrl+c row is now the any-focus primary exit (the
        # on_event intercept routing through the v0z confirm chain);
        # the 261016-vxr Q row is retired with its intercept — a
        # capital Q is a plain typing letter again.
        rows.append(("ctrl+q", S.APP_CTRLQ_LABEL))
        rows.append(("ctrl+c", S.APP_CTRLC_LABEL))
        rows.extend(row for row
                    in map(binding_row, getattr(self.screen, "BINDINGS", []))
                    if row is not None)
        return rows

    # ===== The L language toggle (261015-ehc, EHC-1) =====

    async def _rerender_screen(self, screen: Screen) -> None:
        """Re-render ONE mounted screen in the ACTIVE language.

        textual 8.2.8 probe-pinned: ``recompose()`` rebuilds the compose
        tree but does NOT re-run the screen's own ``on_mount`` — and every
        base screen populates its tables/labels there, so recompose alone
        leaves EMPTY rows (proven live: the env-check table drops 8 -> 0).
        The uniform mechanism therefore recomposes the chrome AND
        re-invokes the screen's ``on_mount`` population: every base
        screen's on_mount is population-only over instance state behind
        exclusive workers (re-running is idempotent — the monitor's
        interval arming carries its own stop-before-re-arm guard, and
        env_check became population-only by guard: its re-mount path
        re-applies landed results or leaves an in-flight run's rows
        alone, WR-03 quick-261016-hhx), and modal content is ctor-frozen
        copy that recompose re-renders as declared.
        ``call_after_refresh`` schedules the coroutine; an awaitable
        on_mount result is awaited.
        """
        await screen.recompose()
        mount_hook = getattr(screen, "on_mount", None)
        if callable(mount_hook):
            result = mount_hook()
            if inspect.isawaitable(result):
                await result

    def action_toggle_language(self) -> None:
        """L — toggle zh <-> en LIVE, persist, and re-render everything.

        (a) the other language becomes active in ``tui/strings`` (every
        module-attribute read re-resolves); (b) the choice persists under
        the XDG state root as ``settings.LANGUAGE_FILE_NAME`` — the ONE
        filename definition, IN-02/261016-hhx (atomic, tolerant — a
        read-only state root degrades to no persistence, never a crash);
        (c) every rendered binding description is remapped (class BINDINGS
        rebuilt in place — Binding.description is frozen on 8.2.8); (d)
        every stacked screen re-renders (the ``_rerender_screen``
        mechanism) and the footers/bars follow; (e) the confirmation
        toast names the new language. Below the minimum grid the choice
        still lands and persists, but no chrome fires (the WR-06
        posture).
        """
        old = S.language()
        new = "zh" if old == "en" else "en"
        S.set_language(new)
        try:
            settings.atomic_write(
                settings.state_dir() / settings.LANGUAGE_FILE_NAME,
                json.dumps({"language": new}, ensure_ascii=False),
            )
        except OSError:
            pass  # tolerant: the toggle is live even when it can't persist
        remap_binding_descriptions(old, new)
        self.title = S.APP_TITLE
        if self.below_minimum_grid:
            return  # set + persist only — no chrome over the guard (WR-06)
        for screen in self.screen_stack:
            screen.call_after_refresh(self._rerender_screen, screen)
        self.notify(S.APP_LANGUAGE_TOAST)
