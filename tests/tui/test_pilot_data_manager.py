"""
Tier-2 Pilot suite for the data-manager screen (Phase 10, 10-04;
D-13/D-14/D-15 + the app-level execution spine).

Pins the slot-3 screen and the D-02/SC5 execution wiring against the REAL
``DnallmMarkTui`` with constructor-injected deterministic fakes (no real
kernel, no real registry write, no real network, no real subprocess — the
D-03 discipline):

- Task 1 (the shell + the spine): digit 3 switches to the real
  DataManagerScreen with both shell bars and zero placeholder artifacts;
  a test-constructed app is INERT (the driver never auto-starts at
  App.on_mount — T-10-04-03) yet never hangs
  (``app.workers.wait_for_complete()`` returns promptly — the driver
  exits on an empty queue by design); the kick busy-guard makes two
  rapid kicks start exactly ONE worker (T-10-04-02);
- Task 2 (the interaction surface): the two panes render from fake data,
  the five queue states / progress cells / reconcile cells / banners /
  Zenodo line render their glyph+copy+style vocabulary, the d/r/x/a/
  enter/g/z actions drive the service seams with honest toasts, and the
  WR-06 guard keeps every modal below the minimum grid;
- Task 3 (the driver loop end-to-end): enqueue -> kick -> worker ->
  event -> row/toast/missing-refresh over the fake service, live
  progress streaming, the blocked-task responsiveness proof (T-08-07
  lineage / T-10-04-05), and the worker-exit + restart semantics.
"""

import asyncio
import re
import threading
from pathlib import Path

from env_smoke import CheckResult  # top-level module (pipeline/ sys.path root)
from rich.text import Text
from textual.binding import Binding

from tui.app import DnallmMarkTui
from tui.screens.data_manager import DataManagerScreen
from tui.screens.nav import BottomBar, TopMenuBar
from tui.screens.selection import PresetMenu, SelectionData
from tui.services import registries as registries_service
from tui.services import selection as selection_service
from tui.services.download_queue import (
    EnqueueOutcome,
    QueueEntry,
    QueueEvent,
    merge_presence,
)
from tui.strings import NAV_PLACEHOLDER_TOAST

# =====================================================================
# Deterministic fakes (D-03: no real kernel / registry / network / spawn)
# =====================================================================

def _queue_entry(key, state="pending", **overrides):
    """One QueueEntry with the canonical defaults (test fixture sugar)."""
    fields = {
        "key": key, "kind": "dataset", "state": state, "attempts": 0,
        "enqueued_at": "2026-10-12T10:00:00", "started_at": None,
        "finished_at": None, "last_percent": None, "interrupted": False,
        "log_path": None, "problems": (), "reconcile": None,
    }
    fields.update(overrides)
    return QueueEntry(**fields)


class FakeQueueService:
    """The app-level driver-queue fake (the injection seam's fake side).

    Deterministic and recording: ``claim_next`` transitions the head
    pending entry to ``downloading`` (the service contract), ``run_task``
    resolves through the scripted ``results`` mapping (default: done)
    firing the optional ``progress_script`` percents through the
    progress callback (duplicates included — the app-level throttle is
    what dedupes), and every call is recorded for the spine assertions.
    ``gate`` blocks the FIRST claim_next and ``progress_gate`` blocks
    run_task after the scripted 40% tick — the deliberately blocked
    fakes the busy-guard, live-progress, and responsiveness proofs use.

    The missing set models the D-11 semantics exactly: a key is missing
    until its entry reaches ``done`` (landing alone never flips).
    """

    def __init__(self, entries=(), results=None, gate=None,
                 probe_state="not_public", progress_script=None,
                 progress_gate=None, load_seed=(), on_drain=None):
        self._entries = [_queue_entry(*item) if isinstance(item, tuple)
                         else item for item in entries]
        self._results = dict(results) if results else {}
        self._gate = gate
        self.probe_state = probe_state
        self._progress_script = dict(progress_script or {})
        self._progress_gate = progress_gate
        # the boot-read seed (10-06 Task 2): load() rehydrates these
        # entries exactly once — the persisted file's contents as the
        # fresh boot would read them
        self._load_seed = [_queue_entry(*item) if isinstance(item, tuple)
                           else item for item in load_seed]
        # WR-02: fired at the drain instant (claim_next found nothing,
        # the busy flag still set) — the lost-wakeup race window hook
        self._on_drain = on_drain
        self.load_calls = 0
        self.claim_next_calls = 0
        self.run_task_calls = []
        self.cancel_calls = []
        self.progress_fired = []
        self.entries_calls = 0
        self.missing_calls = 0

    def add_entry(self, entry):
        """Append one entry post-construction (the restart proof)."""
        self._entries.append(entry)

    # ----- the driver surface (the app protocol) -----

    def load(self):
        self.load_calls += 1
        if self._load_seed:
            self._entries.extend(self._load_seed)
            self._load_seed = []   # the boot read happens once

    def entries(self):
        self.entries_calls += 1
        return list(self._entries)

    def claim_next(self):
        self.claim_next_calls += 1
        if self._gate is not None:
            self._gate.wait(timeout=10)  # deterministic gate, not a sleep
        for index, entry in enumerate(self._entries):
            if entry.state != "pending":
                continue
            claimed = _queue_entry(
                entry.key, state="downloading",
                attempts=entry.attempts + 1, started_at="2026-10-12T10:00:01")
            self._entries[index] = claimed
            return claimed
        if self._on_drain is not None:
            # the drain instant: nothing pending, the busy flag is STILL
            # set — WR-02's lost-wakeup window opens exactly here
            self._on_drain()
        return None

    def run_task(self, key, run_id, progress_cb=None):
        self.run_task_calls.append(key)
        for percent in self._progress_script.get(key, ()):
            self.progress_fired.append((key, percent))
            if progress_cb is not None:
                progress_cb(key, percent)
            if percent == 40 and self._progress_gate is not None:
                self._progress_gate.wait(timeout=10)
        state, percent = self._results.get(key, ("done", 100))
        for index, entry in enumerate(self._entries):
            if entry.key == key:
                self._entries[index] = _queue_entry(
                    key, state=state, last_percent=percent)
        return QueueEvent(
            run_id=run_id, key=key, kind="dataset", state=state,
            last_percent=percent, problems=(), details=(),
            log_path=None)

    def cancel(self, key):
        self.cancel_calls.append(key)
        return "signalled"

    def resolve_channel(self, key):
        # the real Backend's drill-down reads the channel through the
        # queue (the _QueueReadFake None convention — an unknown channel
        # renders its detail honestly)
        return None

    # ----- the screen-side reads the DataManagerBackend delegates to -----

    def missing_datasets(self):
        # the D-11 shape: missing until the entry is done (reconcile
        # pass) — landing alone never flips presence. CR-01: this now
        # MIRRORS the fixed real-service rule (the merged view over
        # reconcile-pass entries), never masks it; the real service is
        # pinned separately in test_services_download_queue.py and by
        # the Backend lane over the seeded real service below.
        self.missing_calls += 1
        return tuple(
            _missing_row(entry.key) for entry in self._entries
            if entry.state != "done")

    def merged_audit_tasks(self):
        # CR-01: delegate to the REAL merge rule — the committed n_audit
        # overlaid with this fake's done entries through the production
        # pure function, so the Pilot summary lane and the production
        # summary lane compute over the same semantics by construction.
        committed = registries_service.load_n_audit() or {}
        overlay = {entry.key: (1, 1, 1) for entry in self._entries
                   if entry.state == "done"}
        return merge_presence(committed, overlay)

    def probe_zenodo(self):
        return self.probe_state


class _EnvCacheHitFake:
    """The minimal env-check service fake (same-day cache hit)."""

    def cached_results(self):
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
        raise AssertionError("the data-manager tests never save presets")

    def parse_filter(self, query):
        return selection_service.parse_filter_query(query)

    def apply_filter(self, entries, parsed):
        return selection_service.apply_filter(entries, parsed.terms)

    def import_template(self, path):
        raise AssertionError("the data-manager tests never import templates")

    def export_template(self, path, models, tasks):
        raise AssertionError("the data-manager tests never export templates")

    def export_tiers(self, path, models, tasks):
        raise AssertionError("the data-manager tests never export tiers")


def _app(queue=None):
    """The real app with cache-hit env + empty selection + the queue fake."""
    return DnallmMarkTui(
        env_check_service=_EnvCacheHitFake(),
        selection_service=_SelectionFake(),
        download_queue_service=(queue if queue is not None
                                else FakeQueueService()),
    )


def _toast_messages(app):
    """The active notification messages (the toast assertions)."""
    return [notification.message for notification in app._notifications]


async def _open_data_manager(pilot, app):
    """Switch to slot 3 and deterministically await the mount workers."""
    await pilot.press("3")
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()


# =====================================================================
# Task 1 — the slot-3 shell + the app-level execution spine
# =====================================================================

async def test_digit3_switches_to_shell_both_bars_zero_placeholder():
    """D-13: digit 3 opens the real screen — both bars, no placeholder."""
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_data_manager(pilot, app)
        assert isinstance(app.screen, DataManagerScreen), (
            "digit 3 must switch to the real data-manager screen"
        )
        assert list(app.screen.query(TopMenuBar)), "the top bar must render"
        assert list(app.screen.query(BottomBar)), "the bottom bar must render"
        assert NAV_PLACEHOLDER_TOAST.format(n=10) not in (
            _toast_messages(app)), (
            "slot 3 must never fire the placeholder phase toast"
        )
        # the digit-nav bindings exist on the screen (the shell contract)
        keys = {binding.key for binding in DataManagerScreen.BINDINGS
                if isinstance(binding, Binding)}
        for digit in ("1", "2", "3", "4", "5", "6"):
            assert digit in keys, f"nav digit {digit} must be bound"


async def test_boot_is_inert_driver_never_autostarts_never_hangs():
    """T-10-04-03: a test-constructed app never starts the driver; the
    worker set still drains promptly (the no-hang proof — the driver
    exits on an empty queue by design, so wait_for_complete returns)."""
    fake = FakeQueueService()
    app = _app(queue=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        # the driver NEVER ran: no claim, no task (App.on_mount inert)
        assert fake.claim_next_calls == 0, (
            "the driver must never auto-start at App.on_mount"
        )
        assert fake.run_task_calls == []
        assert app._queue_busy is False
        # the no-hang proof: every worker completes within the bound
        await asyncio.wait_for(
            app.workers.wait_for_complete(), timeout=10)
        await pilot.pause()
        assert fake.claim_next_calls == 0, "no worker may claim after drain"


async def test_busy_guard_two_rapid_kicks_start_exactly_one_worker():
    """T-10-04-02: the kick busy-guard — two rapid kicks never start a
    second (exclusive-cancelling) worker; exactly one claim happens."""
    gate = threading.Event()
    fake = FakeQueueService(entries=[_queue_entry("GUE__emp_H3")], gate=gate)
    app = _app(queue=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.kick_download_queue()
        app.kick_download_queue()  # the second kick must be a guarded no-op
        # let the worker thread reach (and block inside) claim_next
        for _ in range(100):
            await pilot.pause()
            if fake.claim_next_calls >= 1:
                break
        assert fake.claim_next_calls == 1, (
            "the busy guard must make the second kick a no-op"
        )
        gate.set()
        await asyncio.wait_for(
            app.workers.wait_for_complete(), timeout=10)
        await pilot.pause()
        # ONE worker ran: one task claim + one drain check (claim None)
        # — and the generation never advanced past 1, the direct proof
        # the second kick was a guarded no-op (an unguarded second kick
        # would have cancelled and restarted the driver at generation 2)
        assert fake.claim_next_calls == 2, (
            "exactly one worker: the task claim + the drain check"
        )
        assert app._queue_generation == 1, (
            "the busy guard must keep the second kick a no-op"
        )
        assert fake.run_task_calls == ["GUE__emp_H3"], (
            "the task executed exactly once"
        )


async def test_kick_on_empty_queue_exits_and_wait_for_complete_returns():
    """The SC5 no-hang contract: a kicked driver over an empty queue
    exits immediately — wait_for_complete is bounded, and a later
    enqueue + kick restarts it (the restart half is pinned in Task 3)."""
    fake = FakeQueueService()
    app = _app(queue=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.kick_download_queue()
        await asyncio.wait_for(
            app.workers.wait_for_complete(), timeout=10)
        await pilot.pause()
        assert fake.claim_next_calls == 1, "one claim over the empty queue"
        assert fake.run_task_calls == []
        assert app._queue_busy is False, "the busy flag clears on exit"


# =====================================================================
# Task 2 — the full interaction surface (two panes, states, actions)
# =====================================================================

from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, RichLog, Static

from tui.screens.data_manager import (
    ChannelDetail,
    DataManagerBackend,
    MissingSnapshot,
)
from tui.services import download_queue as download_queue_module
from tui.services.download_queue import MissingInfo, ReauditOutcome
from tui.strings import (
    DL_BUNDLE_TASK_NAME,
    DL_DISABLED_TOAST,
    DL_UNKNOWN_TOAST,
    DL_MISSING_EMPTY,
    DL_MISSING_TITLE,
    DL_PRESENCE_SUMMARY,
    DL_SCREEN_TITLE,
    DL_ZENODO_DISABLED_TOAST,
    DL_ZENODO_FAILED,
    DL_ZENODO_NOT_PUBLIC,
    DL_ZENODO_PROBING,
    DL_ZENODO_PUBLIC,
    QUEUE_BANNER_MISMATCH,
    QUEUE_CANCEL_NOOP,
    QUEUE_CLI_UNAVAILABLE,
    QUEUE_CONFIRM_CANCEL_DOWNLOADING,
    QUEUE_CONFIRM_CANCEL_PENDING,
    QUEUE_EMPTY,
    QUEUE_FLIP_TOAST,
    QUEUE_PROGRESS_INDETERMINATE,
    QUEUE_RECONCILE_MISMATCH,
    QUEUE_RECONCILE_PASS,
    QUEUE_RECONCILE_RUNNING,
    QUEUE_RESTART_NOTE,
    QUEUE_RETRY_NOOP,
    QUEUE_STATE_DONE,
    QUEUE_STATE_DOWNLOADING,
    QUEUE_STATE_FAILED,
    QUEUE_STATE_MISMATCH,
    QUEUE_STATE_PENDING,
    QUEUE_TITLE,
    QUEUE_TOAST_ALREADY_QUEUED,
    QUEUE_PERSIST_FAILED_TOAST,
    QUEUE_TOAST_ENQUEUED,
    QUEUE_TOAST_ENQUEUED_ALL,
)

#: The 68-char-key backstop fixture (the UAT lesson: the longest
#: committed dataset key length).
LONG_KEY = "x" * 68

_GUE_URL = "https://www.modelscope.cn/datasets/lgq12697/GUE"


def _missing_row(key, total=1000, channel="downloadable",
                 reason=None, url=_GUE_URL):
    return MissingInfo(key=key, declared_total=total, channel=channel,
                       reason_code=reason, source_url=url)


def _std_missing():
    """The 3-missing standard fixture (the 80x24 mockup volume)."""
    return (
        _missing_row("GUE__emp_H3", 7349),
        _missing_row("mouse__DMS", 12411),
        _missing_row("plant__vista-100m", 64350),
    )


def _reconcile(declared=None, measured=None, verdict="pass"):
    return {"verdict": verdict, "declared": declared,
            "measured": measured, "unified_eval_n": None}


class FakeDataManagerService:
    """The screen-protocol fake (the injection seam's fake side).

    Deterministic and recording: fixed snapshot/entries, scripted
    enqueue outcomes, a mutable pending-removal cancel, per-key channel
    details and logs, and an optionally gated re-audit (the blocking
    fake the g-worker responsiveness proof uses).
    """

    def __init__(self, missing=(), total=50, present=47, entries=(),
                 probe_state="not_public", enqueue_outcomes=None,
                 enqueue_all_count=0, channel_details=None, logs=None,
                 reaudit_gate=None, probe_gate=None, load_diagnostic=None):
        self._missing = tuple(missing)
        self._total = total
        self._present = present
        self.entries_list = [_queue_entry(*item) if isinstance(item, tuple)
                             else item for item in entries]
        self.probe_state = probe_state
        self._enqueue_outcomes = dict(enqueue_outcomes or {})
        self._enqueue_all_count = enqueue_all_count
        self._channel_details = dict(channel_details or {})
        self._logs = dict(logs or {})
        self._reaudit_gate = reaudit_gate
        self._probe_gate = probe_gate
        self._load_diagnostic = load_diagnostic
        self.snapshot_calls = 0
        self.enqueue_calls = []
        self.enqueue_all_calls = 0
        self.zenodo_calls = 0
        self.retry_calls = []
        self.cancel_calls = []
        self.reaudit_calls = 0

    def missing_snapshot(self):
        self.snapshot_calls += 1
        # the diagnostic kwarg rides only when set — the fake stays
        # constructible against a snapshot shape that predates it
        extra = ({"load_diagnostic": self._load_diagnostic}
                 if self._load_diagnostic is not None else {})
        return MissingSnapshot(rows=self._missing, total=self._total,
                               present=self._present, **extra)

    def entries(self):
        return tuple(self.entries_list)

    def enqueue(self, key):
        self.enqueue_calls.append(key)
        outcome = self._enqueue_outcomes.get(key)
        if outcome is not None:
            return outcome
        self.entries_list.append(_queue_entry(key))
        return EnqueueOutcome(action="enqueued", key=key)

    def enqueue_all(self):
        self.enqueue_all_calls += 1
        return self._enqueue_all_count

    def enqueue_zenodo(self):
        self.zenodo_calls += 1
        return EnqueueOutcome(
            action="enqueued", key=download_queue_module.ZENODO_BUNDLE_KEY)

    def retry(self, key):
        self.retry_calls.append(key)
        return True

    def cancel(self, key):
        self.cancel_calls.append(key)
        self.entries_list = [entry for entry in self.entries_list
                             if entry.key != key]
        return "removed"

    def reaudit(self, run_id):
        self.reaudit_calls += 1
        if self._reaudit_gate is not None:
            self._reaudit_gate.wait(timeout=10)
        return ReauditOutcome(ok=True, details=("exit_code=0",))

    def probe_zenodo(self):
        if self._probe_gate is not None:
            self._probe_gate.wait(timeout=10)
        return self.probe_state

    def channel_detail(self, key):
        detail = self._channel_details.get(key)
        if detail is not None:
            return detail
        return ChannelDetail(key=key, source_url=_GUE_URL, argv=None,
                             channel="downloadable", reason_code=None)

    def read_log(self, key):
        return self._logs.get(key, ())


def _cell_text(value):
    """Plain text of a DataTable cell (cells carry rich Text)."""
    return value.plain if isinstance(value, Text) else str(value)


def _row(table, index):
    """A row's cell texts as plain strings."""
    return [_cell_text(cell) for cell in table.get_row_at(index)]


def _label_text(screen, selector):
    content = screen.query_one(selector).content
    return content.plain if isinstance(content, Text) else str(content)


async def _open_screen(pilot, app, service):
    """Push the screen over the fake service; await the mount workers."""
    app.push_screen(DataManagerScreen(data_service=service))
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()


def _queue_table(screen):
    return screen.query_one("#dl-queue", DataTable)


def _missing_table(screen):
    return screen.query_one("#dl-missing", DataTable)


# ---------------------------------------------------------------------
# Rendering: the two panes from fake data
# ---------------------------------------------------------------------

async def test_both_panes_render_from_fake_data():
    """The standard fixture: 3 missing rows + 2 queue rows + titles."""
    service = FakeDataManagerService(
        missing=_std_missing(),
        entries=(_queue_entry("GUE__emperven_H3"),
                 _queue_entry("mouse__DMS", "downloading",
                              last_percent=42)))
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        screen = app.screen
        assert isinstance(screen, DataManagerScreen)

        missing = _missing_table(screen)
        assert missing.row_count == 3
        first = _row(missing, 0)
        assert first[0] == "✗ GUE__emp_H3"
        assert first[1] == "7,349", "thousands separators, English digits"

        queue = _queue_table(screen)
        assert queue.row_count == 2
        # no terminal states: stable file order holds
        assert [_row(queue, i)[0] for i in range(2)] == [
            "GUE__emperven_H3", "mouse__DMS"]

        assert _label_text(screen, "#dl-missing-title") == (
            DL_MISSING_TITLE.format(n=3))
        assert _label_text(screen, "#dl-queue-title") == (
            QUEUE_TITLE.format(n=2))
        assert _label_text(screen, "#dl-screen-title") == DL_SCREEN_TITLE
        assert _label_text(screen, "#dl-presence-summary") == (
            DL_PRESENCE_SUMMARY.format(present=47, total=50, missing=3))


async def test_five_queue_states_render_glyph_copy_and_style():
    """Each of the five states renders its glyph-first copy + style."""
    service = FakeDataManagerService(entries=(
        _queue_entry("k-pending"),
        _queue_entry("k-downloading", "downloading", last_percent=42),
        _queue_entry("k-done", "done", last_percent=100,
                     reconcile=_reconcile(
                         declared={"Train": 3, "Dev": 4, "Test": 3},
                         measured={"train": 3, "dev": 4, "test": 3})),
        _queue_entry("k-failed", "failed", problems=("exit_1",)),
        _queue_entry("k-mismatch", "mismatch", reconcile=_reconcile(
            declared={"Train": 10}, measured={"train": 3},
            verdict="mismatch")),
    ))
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        table = _queue_table(app.screen)

        def row_of(key):
            for index in range(table.row_count):
                if _row(table, index)[0] == key:
                    return table.get_row_at(index)
            raise AssertionError(f"row {key} not found")

        expected = (
            ("k-pending", QUEUE_STATE_PENDING, "$text-muted"),
            ("k-downloading", QUEUE_STATE_DOWNLOADING, "dim"),
            ("k-done", QUEUE_STATE_DONE, "bold $success"),
            ("k-failed", QUEUE_STATE_FAILED, "bold $error"),
            ("k-mismatch", QUEUE_STATE_MISMATCH, "$warning"),
        )
        for key, copy, style in expected:
            cell = row_of(key)[1]
            assert _cell_text(cell) == copy, f"{key} state cell copy"
            assert cell.style == style, f"{key} state cell style"


async def test_progress_cell_percent_bar_and_indeterminate():
    """D-03/auto-default 3: parsed percent + 10-cell bar; unparsed
    renders the indeterminate glyph, never a fabricated percent."""
    service = FakeDataManagerService(entries=(
        _queue_entry("k-42", "downloading", last_percent=42),
        _queue_entry("k-none", "downloading"),
        _queue_entry("k-done", "done", last_percent=100),
        _queue_entry("k-fail", "failed", last_percent=55),
        _queue_entry("k-fail-none", "failed"),
        _queue_entry("k-pend"),
    ))
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        table = _queue_table(app.screen)

        def progress_of(key):
            for index in range(table.row_count):
                if _row(table, index)[0] == key:
                    return table.get_row_at(index)[2]
            raise AssertionError(f"row {key} not found")

        bar42 = progress_of("k-42")
        assert _cell_text(bar42) == " 42% ████······", (
            "right-aligned 4-cell percent + 10-cell bar (4 filled)"
        )
        assert _cell_text(progress_of("k-none")) == (
            QUEUE_PROGRESS_INDETERMINATE)
        assert _cell_text(progress_of("k-done")) == "100%"
        assert _cell_text(progress_of("k-fail")) == "55%"
        assert _cell_text(progress_of("k-fail-none")) == "—"
        assert _cell_text(progress_of("k-pend")) == "—"


async def test_reconcile_cells_four_vocabularies():
    """pass / running (post-landing transient) / mismatch / dash."""
    service = FakeDataManagerService(entries=(
        _queue_entry("k-pass", "done", last_percent=100,
                     reconcile=_reconcile(
                         measured={"train": 30, "dev": 4, "test": 3})),
        _queue_entry("k-running", "downloading", last_percent=100),
        _queue_entry("k-still-downloading", "downloading",
                     last_percent=42),
        _queue_entry("k-mismatch", "mismatch", reconcile=_reconcile(
            declared={"Train": 10}, measured={"train": 3},
            verdict="mismatch")),
        _queue_entry("k-pending"),
    ))
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        table = _queue_table(app.screen)

        def reconcile_of(key):
            for index in range(table.row_count):
                if _row(table, index)[0] == key:
                    return _cell_text(table.get_row_at(index)[3])
            raise AssertionError(f"row {key} not found")

        assert reconcile_of("k-pass") == QUEUE_RECONCILE_PASS.format(n=37)
        assert reconcile_of("k-running") == QUEUE_RECONCILE_RUNNING
        assert reconcile_of("k-still-downloading") == "—"
        assert reconcile_of("k-mismatch") == QUEUE_RECONCILE_MISMATCH.format(
            n=10, m=3)
        assert reconcile_of("k-pending") == "—"


async def test_both_empty_states_render():
    """The happy zero + the empty queue rows (SEL-01 empty edges)."""
    service = FakeDataManagerService(missing=(), total=50, present=50,
                                     entries=())
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        screen = app.screen
        assert _row(_missing_table(screen), 0) == [
            DL_MISSING_EMPTY.format(total=50), ""]
        assert _row(_queue_table(screen), 0) == [QUEUE_EMPTY, "", "", ""]


async def test_mismatch_banner_block_and_sort_to_top():
    """D-07/D-09: one banner per mismatch under the queue title; the
    mismatch and failed rows sort to the top of the table."""
    service = FakeDataManagerService(entries=(
        _queue_entry("k-done", "done", last_percent=100,
                     reconcile=_reconcile(measured={"train": 1})),
        _queue_entry("k-failed", "failed"),
        _queue_entry("k-mismatch", "mismatch", reconcile=_reconcile(
            declared={"Train": 7349}, measured={"train": 12},
            verdict="mismatch")),
    ))
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        screen = app.screen
        banners = [static for static
                   in screen.query_one("#dl-queue-banners").query(Static)]
        assert len(banners) == 1, "exactly one banner for one mismatch"
        banner_text = banners[0].content.plain if isinstance(
            banners[0].content, Text) else str(banners[0].content)
        assert banner_text == QUEUE_BANNER_MISMATCH.format(
            key="k-mismatch", n=7349, m=12)
        assert banners[0].has_class("queue-banner-mismatch")

        table = _queue_table(screen)
        order = [_row(table, i)[0] for i in range(table.row_count)]
        assert order == ["k-failed", "k-mismatch", "k-done"], (
            "mismatch and failed sort to the top; stable file order within"
        )


async def test_recovered_rows_append_the_restart_note():
    """D-06 restart visibility: interrupted pending rows carry the dim
    note segment (the disabled-suffix append idiom)."""
    service = FakeDataManagerService(entries=(
        _queue_entry("k1", interrupted=True),))
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        task_cell = _row(_queue_table(app.screen), 0)[0]
        assert QUEUE_RESTART_NOTE in task_cell, (
            "the restart note renders on the recovered row"
        )


async def test_bundle_row_renders_the_task_name():
    """The zenodo bundle row's task cell renders the bundle label."""
    service = FakeDataManagerService(entries=(
        _queue_entry(download_queue_module.ZENODO_BUNDLE_KEY,
                     kind="zenodo_bundle"),))
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        assert _row(_queue_table(app.screen), 0)[0] == DL_BUNDLE_TASK_NAME


# ---------------------------------------------------------------------
# The Zenodo line (D-12 four states) + the z behavior
# ---------------------------------------------------------------------

def _zenodo_line(screen):
    return _label_text(screen, "#dl-zenodo-line")


async def test_zenodo_line_four_states():
    """probing dim / not-public dim with HH:MM / public actionable /
    probe-failed warning — each with its contract copy."""
    # probing: a gated probe keeps the mount worker in flight — the
    # line holds the probing copy until the answer flips it
    gate = threading.Event()
    service = FakeDataManagerService(probe_state="public",
                                     probe_gate=gate)
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        app.push_screen(DataManagerScreen(data_service=service))
        for _ in range(20):
            await pilot.pause()
            if _zenodo_line(app.screen) == DL_ZENODO_PROBING:
                break
        assert _zenodo_line(app.screen) == DL_ZENODO_PROBING, (
            "the line renders the probing copy while the probe runs"
        )
        gate.set()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert _zenodo_line(app.screen) == DL_ZENODO_PUBLIC, (
            "the answer flips the line to the public copy"
        )

    for state, expected_text in (
        ("not_public", DL_ZENODO_NOT_PUBLIC),
        ("failed", DL_ZENODO_FAILED),
    ):
        service = FakeDataManagerService(probe_state=state)
        app = _app()
        async with app.run_test(size=(120, 40)) as pilot:
            await _open_screen(pilot, app, service)
            line = _zenodo_line(app.screen)
            if "{HH:MM}" in expected_text:
                assert line.startswith(
                    expected_text.split("{HH:MM}")[0]), (
                    f"{state}: the not-public copy prefix")
                assert line.endswith("）"), (
                    f"{state}: the HH:MM suffix renders")
            else:
                assert expected_text.split("{error}")[0] in line, (
                    f"{state}: the failed copy prefix")


async def test_z_enqueues_only_when_public_never_silent_otherwise():
    """public -> enqueue + kick; not-public/failed -> the explanatory
    toast, zero enqueues (D-12: z is never silent)."""
    for state in ("not_public", "failed"):
        service = FakeDataManagerService(probe_state=state)
        app = _app()
        async with app.run_test(size=(120, 40)) as pilot:
            await _open_screen(pilot, app, service)
            await pilot.press("z")
            await pilot.pause()
            assert service.zenodo_calls == 0
            assert DL_ZENODO_DISABLED_TOAST in _toast_messages(app)

    service = FakeDataManagerService(probe_state="public")
    app = _app(queue=FakeQueueService())
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        await pilot.press("z")
        await pilot.pause()
        assert service.zenodo_calls == 1
        assert QUEUE_TOAST_ENQUEUED.format(
            key=DL_BUNDLE_TASK_NAME) in _toast_messages(app)


# ---------------------------------------------------------------------
# The d/r/x/a actions over the fakes
# ---------------------------------------------------------------------

async def test_d_enqueues_missing_cursor_with_all_outcome_toasts():
    """d happy path (toast + kick + reload), already-queued, disabled,
    and cli-unavailable toasts — never silent."""
    outcomes = {
        "mouse__DMS": EnqueueOutcome(action="already_queued",
                                     key="mouse__DMS"),
        "plant__vista-100m": EnqueueOutcome(
            action="disabled", key="plant__vista-100m",
            reason_code="shape_d_layout", source_url=_GUE_URL),
    }
    service = FakeDataManagerService(missing=_std_missing(),
                                     enqueue_outcomes=outcomes)
    queue_fake = FakeQueueService()
    app = _app(queue=queue_fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)

        # happy: cursor row 0 (GUE__emp_H3, focused by default)
        await pilot.press("d")
        await pilot.pause()
        assert service.enqueue_calls == ["GUE__emp_H3"]
        assert QUEUE_TOAST_ENQUEUED.format(
            key="GUE__emp_H3") in _toast_messages(app)
        assert queue_fake.claim_next_calls >= 1, "enqueued -> kicked"

        # already queued: move to row 1
        _missing_table(app.screen).move_cursor(row=1)
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        assert QUEUE_TOAST_ALREADY_QUEUED.format(
            key="mouse__DMS") in _toast_messages(app)

        # disabled channel: row 2
        _missing_table(app.screen).move_cursor(row=2)
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        assert DL_DISABLED_TOAST.format(
            key="plant__vista-100m") in _toast_messages(app)

    # cli-unavailable (its own fixture — a fresh notification list)
    service = FakeDataManagerService(
        missing=(_missing_row("k-cli"),),
        enqueue_outcomes={"k-cli": EnqueueOutcome(
            action="cli_unavailable", key="k-cli")})
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        await pilot.press("d")
        await pilot.pause()
        assert QUEUE_CLI_UNAVAILABLE in _toast_messages(app)

    # persist_failed (WR-04): the honest never-wrote toast, no row
    service = FakeDataManagerService(
        missing=(_missing_row("k-ro"),),
        enqueue_outcomes={"k-ro": EnqueueOutcome(
            action="persist_failed", key="k-ro")})
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        rows_before = _queue_table(app.screen).row_count
        await pilot.press("d")
        await pilot.pause()
        assert QUEUE_PERSIST_FAILED_TOAST.format(
            key="k-ro") in _toast_messages(app), (
            "the refused enqueue must never be silent"
        )
        assert _queue_table(app.screen).row_count == rows_before

    # unknown (WR-06): the neutral channel-unavailable toast names the
    # machine reason — never the shape-D mirror-layout copy
    service = FakeDataManagerService(
        missing=(_missing_row("k-nfs"),),
        enqueue_outcomes={"k-nfs": EnqueueOutcome(
            action="unknown", key="k-nfs",
            reason_code="registry_unreadable")})
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        await pilot.press("d")
        await pilot.pause()
        assert DL_UNKNOWN_TOAST.format(
            key="k-nfs", reason="registry_unreadable"
        ) in _toast_messages(app), (
            "a registry-read failure must NOT render the mirror-layout "
            "copy (a factually wrong diagnosis, WR-06)"
        )
        assert DL_DISABLED_TOAST.format(key="k-nfs") not in (
            _toast_messages(app))


async def test_a_enqueues_all_with_count_toast():
    """a: the count toast carries {n} (an honest zero included)."""
    service = FakeDataManagerService(missing=_std_missing(),
                                     enqueue_all_count=3)
    queue_fake = FakeQueueService()
    app = _app(queue=queue_fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        await pilot.press("a")
        await pilot.pause()
        assert service.enqueue_all_calls == 1
        assert QUEUE_TOAST_ENQUEUED_ALL.format(
            n=3) in _toast_messages(app)
        assert queue_fake.claim_next_calls >= 1


async def test_r_retries_failed_and_mismatch_noops_others():
    """r on failed -> retry + kick; on done -> the honest noop toast."""
    service = FakeDataManagerService(entries=(
        _queue_entry("k-failed", "failed"),
        _queue_entry("k-done", "done"),
    ))
    queue_fake = FakeQueueService()
    app = _app(queue=queue_fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        _queue_table(app.screen).focus()
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()
        assert service.retry_calls == ["k-failed"]
        assert queue_fake.claim_next_calls >= 1

        _queue_table(app.screen).move_cursor(row=1)
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()
        assert QUEUE_RETRY_NOOP in _toast_messages(app)
        assert service.retry_calls == ["k-failed"]


async def test_x_cancel_confirms_both_variants_and_noops_others():
    """pending -> the remove confirm; downloading -> the signal
    confirm; done -> the noop toast; esc always backs out."""
    service = FakeDataManagerService(entries=(
        _queue_entry("k-pending"),
        _queue_entry("k-downloading", "downloading"),
        _queue_entry("k-done", "done"),
    ))
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        table = _queue_table(app.screen)
        table.focus()
        await pilot.pause()

        # pending: the confirm fires; esc cancels (no service call)
        await pilot.press("x")
        await pilot.pause()
        assert isinstance(app.screen, ModalScreen)
        assert QUEUE_CONFIRM_CANCEL_PENDING.format(
            key="k-pending") in [
                str(w.content) for w in app.screen.query(Static)]
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, ModalScreen)
        assert service.cancel_calls == []

        # pending: enter confirms -> the cancel seam runs
        await pilot.press("x")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert service.cancel_calls == ["k-pending"]
        await app.workers.wait_for_complete()
        await pilot.pause()

        # downloading (now the cursor row after the reload): the copy
        # names the channel's own resume retention
        table = _queue_table(app.screen)
        table.focus()
        await pilot.pause()
        await pilot.press("x")
        await pilot.pause()
        assert isinstance(app.screen, ModalScreen)
        texts = [str(w.content) for w in app.screen.query(Static)]
        assert any(QUEUE_CONFIRM_CANCEL_DOWNLOADING.format(key=key)
                   in text for key in ("k-downloading",)
                   for text in texts), texts
        await pilot.press("escape")
        await pilot.pause()

        # done: the noop toast
        table = _queue_table(app.screen)
        table.focus()
        table.move_cursor(row=1)
        await pilot.pause()
        await pilot.press("x")
        await pilot.pause()
        assert QUEUE_CANCEL_NOOP in _toast_messages(app)


# ---------------------------------------------------------------------
# The drill-down (D-03 verbatim) + the guards
# ---------------------------------------------------------------------

async def test_drill_down_renders_key_url_argv_reconcile_log(
        monkeypatch):
    """enter on a queue row: the full key, the registry download_url,
    the composed argv, the reconcile numbers, and the verbatim log."""
    monkeypatch.setattr(download_queue_module, "resolve_modelscope_cli",
                        lambda cli_path=None: Path("/fake/modelscope"))
    service = FakeDataManagerService(
        entries=(_queue_entry(
            "GUE__emp_H3", "done", last_percent=100,
            reconcile=_reconcile(
                declared={"Train": 3}, measured={"train": 3})),),
        logs={"GUE__emp_H3": ("[argv]", "/fake download", "[exit] 0")},
        channel_details={"GUE__emp_H3": ChannelDetail(
            key="GUE__emp_H3", source_url=_GUE_URL,
            argv=("/fake/modelscope", "download", "--dataset",
                  "lgq12697/GUE"),
            channel="downloadable", reason_code=None)})
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        _queue_table(app.screen).focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, ModalScreen), "the detail opens"
        log = app.screen.query_one("#dl-detail-log", RichLog)
        rendered = "\n".join(strip.text for strip in log.lines)
        assert "GUE__emp_H3" in rendered, "the full key"
        assert _GUE_URL in rendered, "the registry download_url"
        assert "/fake/modelscope download --dataset" in rendered, (
            "the composed LIST argv"
        )
        assert "train" in rendered, "the reconcile numbers"
        assert "/fake download" in rendered, "the verbatim log lines"
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, ModalScreen)


async def test_drill_down_opens_for_missing_rows_too(monkeypatch):
    """enter on a missing row: key + url + argv (the pre-queue detail)."""
    monkeypatch.setattr(download_queue_module, "resolve_modelscope_cli",
                        lambda cli_path=None: Path("/fake/modelscope"))
    service = FakeDataManagerService(missing=_std_missing())
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        # the missing table is focused at mount
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, ModalScreen)
        log = app.screen.query_one("#dl-detail-log", RichLog)
        rendered = "\n".join(strip.text for strip in log.lines)
        assert "GUE__emp_H3" in rendered
        assert _GUE_URL in rendered


async def test_no_modal_below_minimum_grid_enter_is_dead():
    """WR-06: below 80x24 no chrome opens — enter over the guard does
    nothing; growing back restores the screen."""
    service = FakeDataManagerService(missing=_std_missing())
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        await _open_screen(pilot, app, service)
        await pilot.resize_terminal(79, 23)
        await pilot.pause()
        from tui.app import MinSizeScreen
        assert isinstance(app.screen, MinSizeScreen)
        await pilot.press("enter")
        await pilot.pause()
        assert not isinstance(app.screen, ModalScreen), (
            "no modal may open over the min-size guard"
        )
        await pilot.resize_terminal(80, 24)
        await pilot.pause()
        assert isinstance(app.screen, DataManagerScreen)


async def test_68_char_key_renders_in_both_tables_reads_full_in_detail():
    """The UAT backstop: a 68-char key truncates in-cell in BOTH tables
    without column collision and reads full in the detail."""
    service = FakeDataManagerService(
        missing=(_missing_row(LONG_KEY, 123456),),
        entries=(_queue_entry(LONG_KEY, "downloading", last_percent=5),),
        channel_details={LONG_KEY: ChannelDetail(
            key=LONG_KEY, source_url=_GUE_URL, argv=None,
            channel="downloadable", reason_code=None)})
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        await _open_screen(pilot, app, service)
        screen = app.screen
        missing_cell = _row(_missing_table(screen), 0)[0]
        assert missing_cell.startswith("✗ ")
        assert "…" in missing_cell, "in-cell truncation at the width"
        assert len(missing_cell) <= 33

        queue_cell = _row(_queue_table(screen), 0)[0]
        assert "…" in queue_cell
        assert len(queue_cell) <= 33

        # no collision: the neighboring cells still render their content
        assert _row(_queue_table(screen), 0)[1] == QUEUE_STATE_DOWNLOADING

        # full key in detail
        _queue_table(screen).focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        rendered = "\n".join(
            strip.text
            for strip in app.screen.query_one(
                "#dl-detail-log", RichLog).lines)
        assert LONG_KEY in rendered, "the detail reads the full key"


async def test_both_regions_visible_at_80x24_standard_fixture():
    """The 80x24 mockup geometry: 3 missing + 2 queued -> both regions
    visible on the minimum grid."""
    service = FakeDataManagerService(
        missing=_std_missing(),
        entries=(_queue_entry("GUE__emperven_H3"),
                 _queue_entry("mouse__DMS", "downloading",
                              last_percent=42)))
    app = _app()
    async with app.run_test(size=(80, 24)) as pilot:
        await _open_screen(pilot, app, service)
        screen = app.screen
        missing_region = screen.query_one("#dl-missing-region", Vertical)
        queue_region = screen.query_one("#dl-queue-region", Vertical)
        assert missing_region.region.height >= 5, (
            "the missing region keeps its fixed budget"
        )
        assert queue_region.region.height >= 4, (
            "the queue region stays visible at the minimum grid"
        )
        assert _missing_table(screen).visible
        assert _queue_table(screen).visible


# ---------------------------------------------------------------------
# The g re-audit (D-10/R-03) — worker-proven
# ---------------------------------------------------------------------

async def test_g_reruns_reaudit_in_worker_ui_stays_responsive():
    """g on a mismatch row reruns the audit in the worker (a blocking
    fake + returning pauses IS the proof); the reload follows."""
    gate = threading.Event()
    service = FakeDataManagerService(
        entries=(_queue_entry("k-mismatch", "mismatch", reconcile=(
            _reconcile(declared={"Train": 9}, measured={"train": 3},
                       verdict="mismatch"))),),
        reaudit_gate=gate)
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        snapshot_calls_before = service.snapshot_calls
        _queue_table(app.screen).focus()
        await pilot.pause()
        await pilot.press("g")
        await pilot.pause()
        # the audit blocks in the worker thread — these pauses return
        for _ in range(10):
            await pilot.pause()
        assert service.reaudit_calls == 1, "the audit started in a worker"
        gate.set()
        await asyncio.wait_for(
            app.workers.wait_for_complete(), timeout=10)
        await pilot.pause()
        assert service.snapshot_calls > snapshot_calls_before, (
            "the outcome refreshes the tables via a reload"
        )


async def test_g_on_non_mismatch_row_is_a_silent_noop():
    """The g binding is live on mismatch rows only."""
    service = FakeDataManagerService(entries=(
        _queue_entry("k-done", "done"),))
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        _queue_table(app.screen).focus()
        await pilot.press("g")
        await pilot.pause()
        assert service.reaudit_calls == 0


# ---------------------------------------------------------------------
# The Backend adapter + the per-screen i18n lock
# ---------------------------------------------------------------------

class _QueueReadFake:
    """The queue-side fake for the Backend adapter unit checks."""

    def __init__(self, spec):
        self._spec = spec

    def resolve_channel(self, key):
        return self._spec if key == self._spec.key else None

    def entries(self):
        return ()


def test_backend_channel_detail_composes_url_and_argv(monkeypatch):
    """The adapter: the registry URL wins; the argv composes only for
    downloadable channels with a resolved CLI; degraded carries the
    machine reason."""
    monkeypatch.setattr(download_queue_module, "resolve_modelscope_cli",
                        lambda cli_path=None: Path("/fake/modelscope"))
    from tui.services.download_queue import ChannelSpec

    downloadable = ChannelSpec(
        key="GUE__emp_H3", repo_id="lgq12697/GUE", shape="A",
        local_dir=Path("/repo/pipeline/datasets/GUE"),
        include=("emp_H3/*",), exclude=("*.DS_Store",), rename=None,
        final_task_dir="emp_H3", source_url=_GUE_URL, reason_code=None)
    detail = DataManagerBackend(_QueueReadFake(downloadable)
                                ).channel_detail("GUE__emp_H3")
    assert detail.source_url == _GUE_URL
    assert detail.channel == "downloadable"
    assert detail.argv is not None
    assert detail.argv[0] == "/fake/modelscope"
    assert "download" in detail.argv

    degraded = ChannelSpec(
        key="k-shape-d", repo_id="lgq12697/Genomic_Benchmarks", shape=None,
        local_dir=None, include=(), exclude=(), rename=None,
        final_task_dir="x", source_url=_GUE_URL,
        reason_code="shape_d_layout")
    detail = DataManagerBackend(
        _QueueReadFake(degraded)).channel_detail("k-shape-d")
    assert detail.channel == "disabled"
    assert detail.reason_code == "shape_d_layout"
    assert detail.argv is None


def test_backend_missing_snapshot_flips_over_real_seeded_state_cr01(
        monkeypatch, tmp_path):
    """CR-01 at the tier the Pilot e2e previously faked: the REAL
    DataManagerBackend over the REAL DownloadQueueService with a seeded
    done+reconciled entry and a committed-view n_audit that still says
    missing — the row LEAVES the missing pane AND the presence summary
    counts it present (rows and DL_PRESENCE_SUMMARY move together)."""
    import json
    from email.message import Message
    from urllib.error import HTTPError

    from tui.services import settings as tui_settings

    def offline_opener(url, timeout=None):
        raise HTTPError(url, 404, "Not Found", Message(), None)

    # the committed view: GUE__emp_H3 still missing (pre-`g` reality)
    n_audit = tmp_path / "n-audit" / "n_audit.json"
    n_audit.parent.mkdir(parents=True)
    n_audit.write_text(json.dumps(
        {"tasks": {"GUE__emp_H3": {"missing": True}}}), encoding="utf-8")
    monkeypatch.setattr(registries_service, "N_AUDIT_PATH", n_audit)
    state = tmp_path / "state"
    monkeypatch.setenv(tui_settings.STATE_DIR_ENV, str(state))
    state.mkdir(parents=True, exist_ok=True)
    # the seeded queue: done WITH a measured reconcile (the overlay source)
    (state / download_queue_module.QUEUE_FILE_NAME).write_text(json.dumps({
        "schema_version": 1,
        "entries": [{
            "key": "GUE__emp_H3", "kind": "dataset", "state": "done",
            "attempts": 1, "enqueued_at": "2026-10-12T00:00:00+00:00",
            "started_at": None, "finished_at": None, "last_percent": 100,
            "interrupted": False, "log_path": None, "problems": [],
            "reconcile": {"verdict": "pass", "declared": {"Train": 10},
                          "measured": {"train": 10, "dev": 2, "test": 2},
                          "unified_eval_n": 2}}],
    }, indent=4, ensure_ascii=False), encoding="utf-8")
    real_service = download_queue_module.DownloadQueueService(
        zenodo_fetch=offline_opener)

    snapshot = DataManagerBackend(real_service).missing_snapshot()

    assert [row.key for row in snapshot.rows] == [], (
        "the reconciled key must leave the missing pane over the REAL "
        "service (the merged view), not just over the Pilot fake"
    )
    assert snapshot.total == 1
    assert snapshot.present == 1, (
        "the presence summary must count the reconciled key present — "
        "the summary moves with the rows (the CR-01 flip)"
    )
    assert snapshot.missing == 0


def test_data_manager_module_carries_zero_chinese_literals():
    """I18N-01 single home: no operator-facing copy in the screen."""
    source = (Path(__file__).parents[2] / "tui" / "screens"
              / "data_manager.py").read_text(encoding="utf-8")
    offenders = re.findall(r"[一-鿿]", source)
    assert not offenders, (
        f"Chinese literals must live in tui/strings.py only "
        f"({len(offenders)} found in data_manager.py)"
    )


# =====================================================================
# Task 3 — the driver loop end-to-end + event application + gates
# =====================================================================

async def test_driver_e2e_rows_toast_and_missing_refresh():
    """The enqueue -> kick -> worker -> event loop over the fake queue:
    final states render, the done entry fires the flip toast, the
    reconciled key leaves the missing list, and the FAILED row updated
    through apply_queue_event WITHOUT a snapshot reload."""
    fake = FakeQueueService(
        entries=[_queue_entry("k-one"), _queue_entry("k-two")],
        results={"k-one": ("done", 100), "k-two": ("failed", 55)})
    app = _app(queue=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_data_manager(pilot, app)  # digit 3 over the shared fake
        screen = app.screen
        missing_reads_before = fake.missing_calls
        # pre-state: both keys missing, both rows queued
        assert _missing_table(screen).row_count == 2
        assert _queue_table(screen).row_count == 2

        app.kick_download_queue()
        await asyncio.wait_for(
            app.workers.wait_for_complete(), timeout=10)
        await pilot.pause()
        await asyncio.wait_for(
            app.workers.wait_for_complete(), timeout=10)
        await pilot.pause()

        # final states on the rows (mismatch/failed sort first: k-two)
        table = _queue_table(screen)
        assert _row(table, 0)[0] == "k-two"
        assert _row(table, 0)[1] == QUEUE_STATE_FAILED
        assert _row(table, 1)[0] == "k-one"
        assert _row(table, 1)[1] == QUEUE_STATE_DONE

        # the done entry fired the app-level flip toast
        assert QUEUE_FLIP_TOAST.format(key="k-one") in _toast_messages(app)
        assert not any(QUEUE_FLIP_TOAST.format(key="k-two")
                       in message for message in _toast_messages(app))

        # the reconciled key left the missing list (the failed one stays)
        assert _missing_table(screen).row_count == 1
        assert _row(_missing_table(screen), 0)[0].endswith("k-two")

        # row updates without a full reload: exactly ONE extra missing
        # read ran (the done-triggered reload) — the failed row reached
        # its final state through apply_queue_event alone, no snapshot
        assert fake.run_task_calls == ["k-one", "k-two"]
        assert fake.missing_calls == missing_reads_before + 1


async def test_progress_streams_live_and_throttles_duplicates():
    """Live progress: the row's cell updates at intermediate percents
    while the task is mid-flight; duplicate consecutive percents never
    post twice (the app-level throttle over the fake's duplicates)."""
    gate = threading.Event()
    fake = FakeQueueService(
        entries=[_queue_entry("k-live")],
        results={"k-live": ("done", 100)},
        progress_script={"k-live": (10, 10, 25, 25, 40, 40, 100, 100)},
        progress_gate=gate)
    app = _app(queue=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_data_manager(pilot, app)
        screen = app.screen
        applied: list[int] = []
        original = screen.apply_queue_progress

        def spy(key, percent):
            applied.append(percent)
            original(key, percent)

        screen.apply_queue_progress = spy

        app.kick_download_queue()
        # the task blocks after the 40% tick — poll pauses until the
        # cell carries the live 40% bar (each returning pause IS the
        # responsiveness evidence)
        table = _queue_table(screen)
        live = None
        for _ in range(200):
            await pilot.pause()
            for index in range(table.row_count):
                if _row(table, index)[0] == "k-live":
                    live = _cell_text(table.get_row_at(index)[2])
                    break
            if live and live.startswith(" 40%"):
                break
        assert live is not None and live.startswith(" 40%"), (
            "the progress cell must stream the live intermediate percent"
        )
        assert live == " 40% ████······", f"the live bar renders: {live!r}"

        gate.set()
        await asyncio.wait_for(
            app.workers.wait_for_complete(), timeout=10)
        await pilot.pause()
        # the throttle: the claim tick (None) leads; duplicates in the
        # script never post twice
        assert applied == [None, 10, 25, 40, 100], (
            "the claim tick + deduped percents are the exact post stream"
        )
        for index in range(table.row_count):
            if _row(table, index)[0] == "k-live":
                assert _cell_text(
                    table.get_row_at(index)[2]) == "100%"
                break


async def test_blocked_task_never_freezes_the_console():
    """T-10-04-05 (the T-08-07 lineage): while run_task blocks in its
    thread, keypresses still reach the app — the r noop toast fires."""
    gate = threading.Event()
    fake = FakeQueueService(
        entries=[_queue_entry("k-blocked")],
        results={"k-blocked": ("failed", None)},
        progress_script={"k-blocked": (40,)},
        progress_gate=gate)
    app = _app(queue=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_data_manager(pilot, app)
        screen = app.screen
        _queue_table(screen).focus()
        await pilot.pause()
        app.kick_download_queue()
        # wait until the task is in flight (the downloading state shows)
        table = _queue_table(screen)
        for _ in range(200):
            await pilot.pause()
            if any(_row(table, i)[1] == QUEUE_STATE_DOWNLOADING
                   for i in range(table.row_count)):
                break
        assert any(_row(table, i)[1] == QUEUE_STATE_DOWNLOADING
                   for i in range(table.row_count)), (
            "the blocked task renders the downloading state"
        )
        # the console is live: r on the downloading row fires the toast
        await pilot.press("r")
        await pilot.pause()
        assert QUEUE_RETRY_NOOP in _toast_messages(app), (
            "keypresses must reach the app while a task blocks"
        )
        gate.set()
        await asyncio.wait_for(
            app.workers.wait_for_complete(), timeout=10)
        await pilot.pause()


async def test_worker_exits_on_drain_and_restarts_on_next_kick():
    """After the queue drains, no driver worker runs; a later enqueue +
    kick restarts it (the busy flag re-arms)."""
    fake = FakeQueueService(entries=[_queue_entry("k-one")])
    app = _app(queue=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_data_manager(pilot, app)
        app.kick_download_queue()
        await asyncio.wait_for(
            app.workers.wait_for_complete(), timeout=10)
        await pilot.pause()
        assert app._queue_busy is False
        assert not any(worker.name == "run_download_queue"
                       for worker in app.workers), (
            "the driver must not linger after the drain"
        )
        assert fake.run_task_calls == ["k-one"]

        # a later enqueue + kick restarts the driver
        fake.add_entry(_queue_entry("k-two"))
        app.kick_download_queue()
        await asyncio.wait_for(
            app.workers.wait_for_complete(), timeout=10)
        await pilot.pause()
        assert fake.run_task_calls == ["k-one", "k-two"]


async def test_kick_in_the_drain_window_never_strands_a_pending_entry():
    """WR-02 (the lost-wakeup race, made deterministic): an enqueue+kick
    landing INSIDE the window between the worker's final claim_next
    (the drain scan) and the finally busy-clear sees the flag still set
    and is a guarded no-op — the finally's pending re-check must re-kick
    so the newly appended entry never strands with no driver running."""
    holder: dict = {}
    fired = {"once": False}

    def enqueue_and_kick_in_the_lost_window():
        # exactly the operator's d-press racing the drain: appends a
        # pending entry, kicks, and the kick hits the STILL-SET busy
        # flag (a guarded no-op — the generation must not advance here).
        # Fires ONCE (a permanently-armed hook would re-arm the race on
        # every later drain and never let the driver exit).
        if fired["once"]:
            return
        fired["once"] = True
        holder["fake"].add_entry(_queue_entry("k-two"))
        holder["app"].kick_download_queue()

    fake = FakeQueueService(
        entries=[_queue_entry("k-one")],
        results={"k-one": ("done", 100), "k-two": ("done", 100)},
        on_drain=enqueue_and_kick_in_the_lost_window)
    app = _app(queue=fake)
    holder["fake"] = fake
    holder["app"] = app
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.kick_download_queue()
        # the window kick happens on the worker thread; both the first
        # driver AND the re-kicked successor must drain to completion
        for _ in range(3):
            await asyncio.wait_for(
                app.workers.wait_for_complete(), timeout=10)
            await pilot.pause()

        assert fake.run_task_calls == ["k-one", "k-two"], (
            "the entry enqueued inside the drain window must still run — "
            "the drain-side release-and-recheck keeps the SAME driver "
            "going (WR-02, no restart, no stranded pending entry)"
        )
        assert app._queue_generation == 1, (
            "the window kick itself was the guarded no-op (no generation "
            "bump); the SAME driver absorbed the racing entry"
        )
        assert app._queue_busy is False
        assert not any(worker.name == "run_download_queue"
                       for worker in app.workers), (
            "the driver must fully drain and exit after absorbing the "
            "racing entry"
        )


async def test_x_on_downloading_row_confirms_and_signals_the_seam():
    """The cancel-through-app path: the confirm copy for a downloading
    row names the resume retention; confirming reaches the queue seam."""
    fake = FakeQueueService(
        entries=[_queue_entry("k-dl", "downloading", last_percent=42)])
    app = _app(queue=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_data_manager(pilot, app)
        screen = app.screen
        _queue_table(screen).focus()
        await pilot.pause()
        await pilot.press("x")
        await pilot.pause()
        assert isinstance(app.screen, ModalScreen)
        texts = [str(widget.content) for widget in app.screen.query(Static)]
        assert any(QUEUE_CONFIRM_CANCEL_DOWNLOADING.format(key="k-dl")
                   in text for text in texts), (
            "the downloading confirm copy renders"
        )
        await pilot.press("enter")
        await pilot.pause()
        assert fake.cancel_calls == ["k-dl"], (
            "the confirmed cancel reaches the shared queue seam"
        )


async def test_queue_event_reaches_the_screen_under_the_drill_down():
    """WR-03: while the drill-down modal is open (``self.screen`` IS the
    modal, which defines no queue handler), a completed task's event
    still reaches the data-manager screen beneath — the row flips to its
    terminal state WITHOUT waiting for the modal to close."""
    fake = FakeQueueService(
        entries=[_queue_entry("k-modal")],
        results={"k-modal": ("failed", 55)})
    app = _app(queue=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_data_manager(pilot, app)
        screen = app.screen
        table = _queue_table(screen)
        table.focus()
        await pilot.pause()
        await pilot.press("enter")    # the drill-down opens over the row
        await pilot.pause()
        assert isinstance(app.screen, ModalScreen)
        assert getattr(app.screen, "apply_queue_event", None) is None, (
            "the modal itself defines no queue handler (the premise)"
        )

        app.kick_download_queue()
        await asyncio.wait_for(
            app.workers.wait_for_complete(), timeout=10)
        await pilot.pause()

        # the row UNDER the modal already carries the terminal state
        states = {_row(table, i)[0]: _row(table, i)[1]
                  for i in range(table.row_count)}
        assert states.get("k-modal") == QUEUE_STATE_FAILED, (
            "the queue event must forward past the modal to the screen "
            "beneath — a top-of-stack-only forward loses the refresh"
        )
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, ModalScreen)


async def test_queue_event_reaches_selection_under_its_modal():
    """WR-03's second consumer: a done event arriving while the
    SELECTION screen has a modal open (the s-preset PathInputModal)
    still reaches the selection screen's ``apply_queue_event`` — the
    D-11 live flip is delayed by nothing, not even an open modal."""
    fake = FakeQueueService(
        entries=[_queue_entry("k-flip")],
        results={"k-flip": ("done", 100)})
    app = _app(queue=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.press("2")    # the selection screen
        await pilot.pause()
        screen = app.screen
        assert type(screen).__name__ == "SelectionScreen"
        received: list = []
        original = screen.apply_queue_event

        def spy(event):
            received.append(event)
            original(event)

        screen.apply_queue_event = spy
        await pilot.press("s")    # the save-preset modal opens on top
        await pilot.pause()
        assert isinstance(app.screen, ModalScreen)
        assert getattr(app.screen, "apply_queue_event", None) is None

        app.kick_download_queue()
        await asyncio.wait_for(
            app.workers.wait_for_complete(), timeout=10)
        await pilot.pause()

        assert [(event.key, event.state) for event in received] == [
            ("k-flip", "done")], (
            "the done event must reach the selection screen under the "
            "modal — the D-11 live flip never waits on a modal"
        )


async def test_queue_event_reaches_screen_under_cancel_confirm():
    """WR-03's ConfirmModal path: a completed task's event reaches the
    data-manager screen while the x-cancel confirm is the top of the
    stack — the row refreshes under the confirm, and dismissing it
    shows the fresh state immediately."""
    fake = FakeQueueService(
        entries=[_queue_entry("k-confirm")],
        results={"k-confirm": ("failed", 55)})
    app = _app(queue=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_data_manager(pilot, app)
        screen = app.screen
        table = _queue_table(screen)
        table.focus()
        await pilot.pause()
        await pilot.press("x")    # the pending-row cancel confirm opens
        await pilot.pause()
        assert isinstance(app.screen, ModalScreen)
        assert getattr(app.screen, "apply_queue_event", None) is None

        app.kick_download_queue()
        await asyncio.wait_for(
            app.workers.wait_for_complete(), timeout=10)
        await pilot.pause()

        states = {_row(table, i)[0]: _row(table, i)[1]
                  for i in range(table.row_count)}
        assert states.get("k-confirm") == QUEUE_STATE_FAILED, (
            "the row must refresh under the open ConfirmModal too"
        )
        await pilot.press("escape")
        await pilot.pause()
        assert fake.cancel_calls == [], "esc backs out; no cancel ran"


# =====================================================================
# Task 2 — the env-check route hint + the digit-3 path (10-05, D-14;
# zero env_check.py edits this plan — the amended constant flows through
# the existing render path, and digit 3 is the ONE navigation path)
# =====================================================================

from tui.strings import ENV_KERNEL_LABELS, ENV_ROUTE_MISSING_DATASETS


class _EnvDatasetDirsFailFake:
    """The env-check fake whose cached run carries the dataset_dirs FAIL
    (the route fixture — the route line renders from the cache hit, no
    kernel ever spawns)."""

    def cached_results(self):
        passes = tuple(
            CheckResult(name=kernel_id, ok=True,
                        lines=(f"PASS: {kernel_id}",))
            for kernel_id in ENV_KERNEL_LABELS
            if kernel_id != "dataset_dirs"
        )
        fail = CheckResult(name="dataset_dirs", ok=False, lines=(
            ("FAIL: 2 of 50 registry dataset dir(s) missing on disk "
             "(the E2' launch gate):"),
            "  - GUE__EPI_GM12878",
            "  - GUE__fungi_species_20",
        ))
        return ("2026-10-11 09:30", passes + (fail,))

    def kernels(self):
        raise AssertionError("a cache-hit boot must never spawn the worker")

    def persist(self, results):
        raise AssertionError("a cache-hit boot must never persist")


async def test_env_route_hint_renders_and_digit3_is_the_one_path():
    """ENV-03 landing: the RENDERED route line (the real verdict render
    path over the dataset_dirs failure fixture) carries the [3] keycap
    segment naming the data-manager screen, and pressing 3 from the env
    screen switches to the real DataManagerScreen over the injected
    fake queue (the shared-instance wiring)."""
    app = DnallmMarkTui(
        env_check_service=_EnvDatasetDirsFailFake(),
        selection_service=_SelectionFake(),
        download_queue_service=FakeQueueService(),
    )
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        # the rendered verdict block: the ready verdict (every CRITICAL
        # kernel passed) + the route line for the routing failure
        lines = [
            str(static.content)
            for static in app.screen.query_one("#env-verdict").query(Static)
        ]
        route_line = ENV_ROUTE_MISSING_DATASETS.format(n=2)
        assert route_line in lines, (
            "the route line must render through the real render path"
        )
        # the [3] keycap segment IS in the rendered line (the ENV-03
        # navigation affordance — the amended 10-03 constant, zero
        # env_check.py code changes)
        assert "[3]" in route_line
        assert "前往数据管理" in route_line

        # digit 3: the one navigation path — the data-manager screen
        # mounts over the SHARED fake queue
        await pilot.press("3")
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, DataManagerScreen), (
            "digit 3 from the env screen must switch to the "
            "DataManagerScreen"
        )


# =====================================================================
# Task 1 (10-06) — the degradation edge sweep at the screen tier: the
# CLI-absent state is a first-class UI state (toast, no row, screen
# usable), the corrupt-load diagnostic surfaces as a status line, and
# a registry-unknown queue row renders with its state intact.
# =====================================================================

async def test_cli_unavailable_enqueue_never_adds_a_row_screen_usable():
    """SC5/D-01 degradation: a cli_unavailable enqueue outcome renders
    its error toast, adds NO queue row, and the screen stays fully
    usable (missing list, existing entries, the Zenodo line)."""
    service = FakeDataManagerService(
        missing=_std_missing(),
        entries=(_queue_entry("k-existing", "failed"),),
        enqueue_outcomes={"GUE__emp_H3": EnqueueOutcome(
            action="cli_unavailable", key="GUE__emp_H3")})
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        screen = app.screen
        rows_before = _queue_table(screen).row_count

        await pilot.press("d")
        await pilot.pause()

        assert QUEUE_CLI_UNAVAILABLE in _toast_messages(app)
        assert _queue_table(screen).row_count == rows_before, (
            "a refused enqueue must never add a queue row"
        )
        assert not any(entry.key == "GUE__emp_H3"
                       for entry in service.entries_list)
        # the screen stays fully usable
        assert _missing_table(screen).row_count == 3
        assert _row(_queue_table(screen), 0)[1] == QUEUE_STATE_FAILED
        assert _zenodo_line(screen) != ""


async def test_load_diagnostic_surfaces_as_status_line():
    """The corrupt-state contract at the screen tier: a load diagnostic
    from the snapshot renders as a VISIBLE status line under the title
    bar (never a crash, never silent loss) while both panes keep
    rendering; a healthy snapshot renders no diagnostic line at all."""
    diagnostic = ("download queue state file unreadable, moved aside: "
                  "/tmp/x/download_queue.json (Expecting value: line 1 "
                  "column 1 (char 0))")
    service = FakeDataManagerService(
        missing=_std_missing(),
        entries=(_queue_entry("k-existing"),),
        load_diagnostic=diagnostic)
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        screen = app.screen
        line = screen.query_one("#dl-load-diagnostic")
        assert line.display is True, (
            "the diagnostic must surface as a visible status line"
        )
        content = line.content
        rendered = content.plain if isinstance(content, Text) else str(
            content)
        assert diagnostic in rendered, (
            "the diagnostic renders verbatim (data, never translated)"
        )
        # both panes still render their rows
        assert _missing_table(screen).row_count == 3
        assert _queue_table(screen).row_count == 1

    # the healthy path: no diagnostic line occupies the layout
    service = FakeDataManagerService(missing=_std_missing())
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        assert app.screen.query_one("#dl-load-diagnostic").display is False


async def test_unknown_channel_queue_row_renders_state_intact():
    """Registry evolution at the screen tier: a queue row whose key has
    vanished from the registry renders with its state intact, and the
    drill-down names the unknown channel + machine reason."""
    service = FakeDataManagerService(
        entries=(_queue_entry("VanishedRepo__gone_task", "failed",
                              problems=("unknown_key",)),),
        channel_details={"VanishedRepo__gone_task": ChannelDetail(
            key="VanishedRepo__gone_task", source_url=None, argv=None,
            channel="unknown", reason_code="unknown_key")})
    app = _app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_screen(pilot, app, service)
        screen = app.screen
        assert _row(_queue_table(screen), 0)[0] == "VanishedRepo__gone_task"
        assert _row(_queue_table(screen), 0)[1] == QUEUE_STATE_FAILED, (
            "the unknown-channel row renders with its state intact"
        )
        _queue_table(screen).focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        rendered = "\n".join(
            strip.text for strip in app.screen.query_one(
                "#dl-detail-log", RichLog).lines)
        assert "channel: unknown (unknown_key)" in rendered, (
            "the drill-down names the degraded channel disposition"
        )


# =====================================================================
# Task 2 (10-06) — restart rehydration end-to-end: the boot-resume app
# tier (kick exactly when pending work exists, never twice) and the
# D-06 visible-recovery screen proof over the REAL Backend + real
# service + a pinned state root.
# =====================================================================

async def test_boot_resume_rehydrates_and_kicks_once():
    """D-06 at the app tier: boot_resume_queue over a rehydrated
    pending entry kicks the driver exactly once — the entry runs to
    done and the generation never advances past 1."""
    fake = FakeQueueService(
        load_seed=[("GUE__emp_H3",)],
        results={"GUE__emp_H3": ("done", 100)})
    app = _app(queue=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.boot_resume_queue()
        await asyncio.wait_for(
            app.workers.wait_for_complete(), timeout=10)
        await pilot.pause()
        assert fake.load_calls == 1, "the boot read ran"
        assert fake.run_task_calls == ["GUE__emp_H3"], (
            "the rehydrated pending entry resumed through the driver"
        )
        assert app._queue_generation == 1
        assert app._queue_busy is False


async def test_boot_resume_without_pending_never_kicks():
    """Zero pending (an empty seed / only-terminal entries) -> no kick:
    the driver never claims, the busy flag stays down."""
    for seed in ([], [("k-done", "done")]):
        fake = FakeQueueService(load_seed=seed)
        app = _app(queue=fake)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            app.boot_resume_queue()
            await pilot.pause()
            assert fake.claim_next_calls == 0, (
                "boot resume must never kick without pending work"
            )
            assert app._queue_busy is False
            assert app._queue_generation == 0


async def test_second_boot_resume_while_busy_starts_no_second_worker():
    """The busy guard through the boot path: while the driver is
    mid-claim, a second boot_resume call is a guarded no-op — the
    generation stays 1 and exactly one worker runs the task."""
    gate = threading.Event()
    fake = FakeQueueService(load_seed=[("k-one",)], gate=gate)
    app = _app(queue=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.boot_resume_queue()
        for _ in range(100):
            await pilot.pause()
            if fake.claim_next_calls >= 1:
                break
        assert fake.claim_next_calls == 1

        app.boot_resume_queue()   # while the first claim is gated
        await pilot.pause()

        assert fake.claim_next_calls == 1, (
            "the second boot resume must not start a second worker"
        )
        assert app._queue_generation == 1
        gate.set()
        await asyncio.wait_for(
            app.workers.wait_for_complete(), timeout=10)
        await pilot.pause()
        assert fake.run_task_calls == ["k-one"]
        assert app._queue_generation == 1, (
            "the guarded second boot resume never restarted the driver"
        )


async def test_data_manager_rehydrates_real_backend_seeded_downloading(
        monkeypatch, tmp_path):
    """The D-06 visible-recovery contract through the REAL Backend over
    the REAL DownloadQueueService + a pinned state root: a state file
    persisted mid-download rehydrates at mount (the Backend's tolerant
    load + the downgrade) and the row renders the pending glyph with
    the QUEUE_RESTART_NOTE segment; the queue never kicks (the test app
    is inert, T-10-04-03), and the Zenodo probe rides the service's
    fetch seam — the lane is provably offline."""
    import json
    from email.message import Message
    from urllib.error import HTTPError

    from tui.services import download_queue as download_queue_module_
    from tui.services import settings as tui_settings

    probe_calls = []

    def offline_opener(url, timeout=None):
        probe_calls.append(url)
        raise HTTPError(url, 404, "Not Found", Message(), None)

    state = tmp_path / "state"
    monkeypatch.setenv(tui_settings.STATE_DIR_ENV, str(state))
    state.mkdir(parents=True, exist_ok=True)
    (state / download_queue_module_.QUEUE_FILE_NAME).write_text(json.dumps({
        "schema_version": 1,
        "entries": [{
            "key": "GUE__emp_H3", "kind": "dataset",
            "state": "downloading", "attempts": 1,
            "enqueued_at": "2026-10-12T00:00:00+00:00",
            "started_at": "2026-10-12T00:01:00+00:00",
            "finished_at": None, "last_percent": 62,
            "interrupted": False, "log_path": None,
            "problems": [], "reconcile": None}],
    }, indent=4, ensure_ascii=False), encoding="utf-8")
    real_service = download_queue_module_.DownloadQueueService(
        zenodo_fetch=offline_opener)
    app = DnallmMarkTui(
        env_check_service=_EnvCacheHitFake(),
        selection_service=_SelectionFake(),
        download_queue_service=real_service)
    async with app.run_test(size=(120, 40)) as pilot:
        await _open_data_manager(pilot, app)   # digit 3 -> real Backend
        screen = app.screen
        table = _queue_table(screen)
        assert table.row_count == 1, "the seeded entry rehydrated"
        row = _row(table, 0)
        assert row[0].startswith("GUE__emp_H3")
        assert QUEUE_RESTART_NOTE[:4] in row[0], (
            "the recovered row carries the visible restart-note segment "
            "(in-cell truncation may clip its tail — the 10-04 contract; "
            "the full note rides the drill-down)"
        )
        assert row[1] == QUEUE_STATE_PENDING, (
            "the interrupted entry renders as pending (the downgrade)"
        )
        # the drill-down carries the FULL note (the D-03 completeness)
        table.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        rendered = "\n".join(
            strip.text for strip in app.screen.query_one(
                "#dl-detail-log", RichLog).lines)
        assert QUEUE_RESTART_NOTE in rendered
        await pilot.press("escape")
        await pilot.pause()
        # the queue never kicked: the test app is inert (T-10-04-03)
        assert app._queue_busy is False
        assert screen.query_one("#dl-load-diagnostic").display is False
        # the probe rode the service seam — the lane is offline
        assert probe_calls and "zenodo.org" in probe_calls[0], (
            "the real adapter's probe must route through the fetch seam"
        )
        assert _zenodo_line(screen) != DL_ZENODO_PROBING
