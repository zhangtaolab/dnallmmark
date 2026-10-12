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
import threading

from env_smoke import CheckResult  # top-level module (pipeline/ sys.path root)
from textual.binding import Binding

from tui.app import DnallmMarkTui
from tui.screens.data_manager import DataManagerScreen
from tui.screens.nav import BottomBar, TopMenuBar
from tui.screens.selection import PresetMenu, SelectionData
from tui.services import selection as selection_service
from tui.services.download_queue import QueueEntry, QueueEvent
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
    resolves through the scripted ``results`` mapping (default: done),
    and every call is recorded for the spine assertions. ``gate`` blocks
    the FIRST claim_next on a ``threading.Event`` — the deliberately
    blocked fake the busy-guard and responsiveness proofs use.
    """

    def __init__(self, entries=(), results=None, gate=None,
                 probe_state="not_public"):
        self._entries = [_queue_entry(*item) if isinstance(item, tuple)
                         else item for item in entries]
        self._results = dict(results) if results else {}
        self._gate = gate
        self.probe_state = probe_state
        self.load_calls = 0
        self.claim_next_calls = 0
        self.run_task_calls = []

    # ----- the driver surface (the app protocol) -----

    def load(self):
        self.load_calls += 1

    def entries(self):
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
        return None

    def run_task(self, key, run_id, progress_cb=None):
        self.run_task_calls.append(key)
        state, percent = self._results.get(key, ("done", 100))
        for index, entry in enumerate(self._entries):
            if entry.key == key:
                self._entries[index] = _queue_entry(
                    key, state=state, last_percent=percent)
        return QueueEvent(
            run_id=run_id, key=key, kind="dataset", state=state,
            last_percent=percent, problems=(), details=(),
            log_path=None)

    # ----- the screen-side reads the DataManagerBackend delegates to -----

    def missing_datasets(self):
        return ()

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
