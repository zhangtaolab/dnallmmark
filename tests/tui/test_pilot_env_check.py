"""
Tier-2 Pilot suite for the env-check screen (Phase 8, 08-06).

Pins the ENV-01..04 presentation contract end-to-end against the REAL
``DnallmMarkTui`` with constructor-injected deterministic fakes (RESEARCH
Pattern 7; D-03 — no real kernel, GPU or otherwise, ever executes in this
suite; the service protocol is the injection seam):

- cache hit (same-day persisted state): all eight rows render in their
  FINAL pass/fail states plus the last-check line, and the worker never
  spawns (D-05);
- cache miss: rows start pending, then fill row-by-row via posted worker
  messages in main() kernel order; persist is called ONCE with the whole
  item list including the deliberate FAIL's detail lines;
- the pending -> checking -> pass/fail state progression is observable
  mid-run (a deliberately slow gated fake — the T-08-07 UI-responsiveness
  assertion: the event loop keeps processing while a kernel blocks);
- the verdict block: the critical-fail line names the failing CRITICAL
  kernels and the routing line carries the missing-dataset count and the
  CLI audit command when dataset_dirs fails; an all-pass run renders the
  ready verdict;
- the refresh key resets every row to pending and re-runs (call counts
  double);
- enter opens the drill-down modal with the kernel's lines VERBATIM
  (wrapped, never elided); app-level bindings do not fire while the modal
  is open; esc closes it;
- the last-check line matches the persisted checked_at string format
  exactly (ENV-02, halfwidth colon);
- the state strings are glyph-first and distinct (NO_COLOR legibility);
- 08-06 Task 2, the composed app at rest: the two nav-shell bars
  visible on boot (the 09-03 migration replaced the Footer), the
  ``?`` help modal (every binding, Chinese labels, esc closes), the
  80x24 min-size guard (swap, live dimension updates, restore), the
  NO_COLOR scenario (rendered glyphs stay distinct), and the styles
  contract (zero hex, declared spacing tokens only).

Pilot discipline (08-RESEARCH Pattern 7 / Pitfall 7): ``await
pilot.pause()`` before every assertion; worker completion is awaited via
``app.workers.wait_for_complete()`` (never a time.sleep); the gated fake
synchronizes on a ``threading.Event`` — a deterministic primitive, not a
timed sleep.
"""

import re
import threading
from datetime import datetime, timedelta
from pathlib import Path

from env_smoke import CheckResult
from rich.text import Text
from textual.widgets import DataTable, RichLog, Static

import tui.app as tui_app_module
import tui.screens.about as about_screen_module
import tui.screens.env_check as env_check_screen_module
import tui.screens.wizard as wizard_screen_module
from tui.app import (
    DnallmMarkTui,
    HelpModal,
    MinSizeScreen,
)
from tui.screens.env_check import EnvCheckBackend, EnvCheckScreen, EnvDetailModal
from tui.screens.nav import BottomBar, TopMenuBar
from tui.services import env_check as env_check_service
from tui.strings import (
    APP_HELP_LABEL,
    APP_HELP_ROW,
    APP_HELP_TITLE,
    APP_MIN_SIZE_MESSAGE,
    APP_QUIT_LABEL,
    ENV_DETAIL_LABEL,
    ENV_DETAIL_TITLE,
    ENV_KERNEL_DEGRADED,
    ENV_KERNEL_LABELS,
    ENV_LAST_CHECK_LINE,
    ENV_REFRESH_LABEL,
    ENV_ROUTE_MISSING_DATASETS,
    ENV_ROUTE_MISSING_MODELS,
    ENV_STATE_CHECKING,
    ENV_STATE_FAIL,
    ENV_STATE_PASS,
    ENV_STATE_PENDING,
    ENV_STORAGE_LABELS,
    ENV_STORAGE_NOTE,
    ENV_STORAGE_TITLE,
    ENV_VERDICT_CRITICAL_FAIL,
    ENV_VERDICT_PASS,
)

# The seven kernel ids in main() order — the row-order contract (08-01).
MAIN_KERNEL_ORDER = tuple(ENV_KERNEL_LABELS)

_SCREEN_MODULE_FILE = Path(env_check_screen_module.__file__)
_APP_MODULE_FILE = Path(tui_app_module.__file__)
_STYLES_FILE = _APP_MODULE_FILE.parent / "styles.tcss"

# 09-06 i18n close-out: the zero-Chinese grep lock extends to the two
# Phase 9 screen modules (wizard/about) — the scanned module list, the
# assertion itself unchanged.
_GREP_LOCK_MODULES = (
    _SCREEN_MODULE_FILE,
    Path(wizard_screen_module.__file__),
    Path(about_screen_module.__file__),
)


# =====================================================================
# Deterministic fakes (D-03: zero real kernels in this suite)
# =====================================================================

def _pass(name, lines=None):
    """A passing CheckResult (short synthetic detail lines)."""
    return CheckResult(
        name=name, ok=True,
        lines=tuple(lines) if lines else (f"PASS: {name} ok",),
    )


def _fail(name, lines=None):
    """A failing CheckResult (short synthetic detail lines)."""
    return CheckResult(
        name=name, ok=False,
        lines=tuple(lines) if lines else (f"FAIL: {name} broken",),
    )


def _mixed_results():
    """Seven passes + the dataset_dirs FAIL — the standard scenario.

    The dataset_dirs failure carries the real kernel's byte-stable line
    shapes (the missing-count FAIL line, the ``  - name`` listing lines,
    and a double-nested note line) so the routing count and the
    drill-down long-text path are exercised against contract-shaped
    data; the model_dirs pass carries the 261014-dcl annotated headline.
    """
    return [
        _pass("version_pins", ["PASS: torch 2.11.0 == pyproject [gpu] pin"]),
        _pass("dnallm",
              ["PASS: import dnallm resolves (/opt/dnallm/__init__.py)"]),
        _pass("peft", ["PASS: peft 0.21.2 importable"]),
        _pass("cuda", ["PASS: CUDA available, 1 device(s)",
                       "PASS: device 0: NVIDIA GB10, 186.5 GiB total memory"]),
        _pass("matmul", ["PASS: small-tensor matmul executed (sum == 512.0)"]),
        _pass("numpy", ["PASS: numpy 2.5.3 >= pyproject floor"]),
        _pass("model_dirs", [
            ("PASS: all 62 registry model dir(s) present on disk "
             "(root: pipeline/)"),
        ]),
        _fail("dataset_dirs", [
            ("FAIL: 2 of 50 registry dataset dir(s) missing on disk "
             "(the E2' launch gate) (root: pipeline/):"),
            "  - GUE__emp_H3",
            ("  - GUE__prom_core  [double-nested: the fresh-unzip "
             "suite/suite/task layout needs flattening]"),
        ]),
    ]


class FakeEnvCheckService:
    """Deterministic env-check service fake (the injection seam's fake side).

    ``cached`` fixes the same-day cache answer (a ``(checked_at, results)``
    tuple, or None for a miss); ``results`` is the no-cache run's kernel
    outcome sequence (each kernel resolves instantly, in order); ``gate``
    optionally blocks the FIRST kernel on a ``threading.Event`` — the
    deliberately slow fake the T-08-07 responsiveness assertions use.
    """

    def __init__(self, cached=None, results=None,
                 checked_at="2026-10-11 09:30", gate=None):
        self.cached = cached
        self.results = list(results) if results is not None else _mixed_results()
        self.checked_at = checked_at
        self.gate = gate
        self.kernel_queries = 0   # kernels() calls (worker spawns)
        self.kernel_calls = []    # executed kernel ids, in execution order
        self.persist_calls = []   # each entry: the full result list

    def cached_results(self):
        """The fixed cache answer."""
        return self.cached

    def storage_rows(self):
        # F4W-04 (261014-f4w): frozen display rows — no filesystem scan.
        from tui.services.run_config import StorageRow

        return (
            StorageRow("model_root", "/golden/models", True),
            StorageRow("dataset_root", "/golden/datasets", False),
            StorageRow("output_root", "/golden/finetuned", True),
            StorageRow("log_dir", "/golden/logs", False),
            StorageRow("cache_dir", "/golden/cache", True),
        )

    def kernels(self):
        """One zero-arg callable per result, keyed on the kernel id."""
        self.kernel_queries += 1
        kernels = {}
        for index, result in enumerate(self.results):
            kernels[result.name] = self._make_kernel(result, index)
        return kernels

    def _make_kernel(self, result, index):
        def _kernel():
            if index == 0 and self.gate is not None:
                self.gate.wait(timeout=10)  # deterministic gate, not a sleep
            self.kernel_calls.append(result.name)
            return result
        return _kernel

    def persist(self, results):
        """Record the whole list; return the fixed display string."""
        self.persist_calls.append(list(results))
        return self.checked_at


# =====================================================================
# Render-reading helpers
# =====================================================================

def _cell(value):
    """Plain text of a DataTable cell (state cells carry rich Text styles)."""
    return value.plain if isinstance(value, Text) else str(value)


def _row(table, index):
    """A row's cell texts as plain strings."""
    return [_cell(cell) for cell in table.get_row_at(index)]


def _label_text(screen, selector):
    """The current text of a Label/Static (the last-check line, etc.)."""
    content = screen.query_one(selector).content
    return content.plain if isinstance(content, Text) else str(content)


def _verdict_lines(screen):
    """The verdict block's rendered line texts, top to bottom."""
    box = screen.query_one("#env-verdict")
    return [str(static.content) for static in box.query(Static)]


async def _wait_for_check(pilot, app):
    """Deterministically wait for the worker run to complete + flush."""
    await app.workers.wait_for_complete()
    await pilot.pause()


# =====================================================================
# Pilot tests — the screen behaviors (ENV-01..03 presentation)
# =====================================================================

async def test_cache_hit_renders_final_states_and_last_check_without_worker():
    """D-05: a same-day cache hit renders instantly and spawns zero kernels."""
    fake = FakeEnvCheckService(cached=("2026-10-11 09:30", _mixed_results()))
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, EnvCheckScreen)

        table = screen.query_one(DataTable)
        assert table.row_count == 8
        for index, result in enumerate(_mixed_results()):
            row = _row(table, index)
            expected_glyph = ENV_STATE_PASS if result.ok else ENV_STATE_FAIL
            assert row[0] == expected_glyph, (
                f"row {index} ({result.name}) must render its FINAL state"
            )
            assert row[1] == ENV_KERNEL_LABELS[result.name]

        # the last-check line renders from the persisted checked_at (ENV-02)
        assert _label_text(screen, "#env-last-check") == (
            ENV_LAST_CHECK_LINE.format(checked_at="2026-10-11 09:30")
        )

        # the worker never spawned: zero kernel queries, zero executions,
        # zero persistence (the cache is the only render source)
        assert fake.kernel_queries == 0
        assert fake.kernel_calls == []
        assert fake.persist_calls == []


async def test_no_cache_fills_rows_async_and_persists_whole_list_once():
    """Cache miss: per-row async fill in main() order; persist once, whole."""
    fake = FakeEnvCheckService(cached=None)
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await _wait_for_check(pilot, app)

        table = app.screen.query_one(DataTable)
        for index, result in enumerate(_mixed_results()):
            row = _row(table, index)
            assert row[0] == (
                ENV_STATE_PASS if result.ok else ENV_STATE_FAIL
            ), f"row {index} ({result.name}) must reach its final glyph"
            # the summary column carries the kernel's own first detail line
            # (the byte-stable env_smoke wording, prefix-stripped)
            first_line = result.lines[0]
            summary = (first_line.removeprefix("PASS: ")
                              .removeprefix("FAIL: "))
            assert row[2] == summary, (
                f"row {index} summary must be the kernel's own first line"
            )

        # kernels resolved in deterministic main() order (D-03)
        assert fake.kernel_calls == list(MAIN_KERNEL_ORDER)

        # persist was called ONCE with the FULL item list, the deliberate
        # FAIL's detail lines included (D-05: partial failures persist whole)
        assert len(fake.persist_calls) == 1
        persisted = fake.persist_calls[0]
        assert [result.name for result in persisted] == list(MAIN_KERNEL_ORDER)
        fail_item = next(result for result in persisted if not result.ok)
        assert fail_item.name == "dataset_dirs"
        assert "  - GUE__emp_H3" in fail_item.lines

        # the last-check line renders from the fresh run's persisted moment
        assert _label_text(app.screen, "#env-last-check") == (
            ENV_LAST_CHECK_LINE.format(checked_at=fake.checked_at)
        )


async def test_gated_kernel_shows_checking_progression_ui_stays_responsive():
    """T-08-07: a blocked kernel shows checking; the loop keeps processing."""
    gate = threading.Event()
    fake = FakeEnvCheckService(cached=None, gate=gate)
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        # the worker blocks inside kernel 0; poll pauses (each pause returning
        # IS the responsiveness proof — the event loop is never blocked)
        table = app.screen.query_one(DataTable)
        for _ in range(100):
            await pilot.pause()
            if _row(table, 0)[0] == ENV_STATE_CHECKING:
                break
        assert _row(table, 0)[0] == ENV_STATE_CHECKING, (
            "the in-flight row must render the checking state"
        )
        for index in range(1, 8):
            assert _row(table, index)[0] == ENV_STATE_PENDING, (
                f"row {index} must still be pending while kernel 0 blocks"
            )
        gate.set()
        await _wait_for_check(pilot, app)
        assert _row(table, 0)[0] == ENV_STATE_PASS


async def test_critical_fail_verdict_names_kernels_and_routes_missing_data():
    """ENV-03: critical-fail line names failing kernels; routing line + CLI."""
    results = [
        _pass("version_pins"),
        _pass("dnallm"),
        _pass("peft"),
        _fail("cuda", ["FAIL: torch.cuda.is_available() is False — no visible GPU"]),
        _fail("matmul", ["FAIL: small-tensor matmul diverged"]),
        _pass("numpy"),
        _pass("model_dirs", [
            ("PASS: all 62 registry model dir(s) present on disk "
             "(root: pipeline/)"),
        ]),
        _fail("dataset_dirs", [
            ("FAIL: 7 of 50 registry dataset dir(s) missing on disk "
             "(the E2' launch gate) (root: pipeline/):"),
            *[f"  - GUE__task_{number}" for number in range(7)],
        ]),
    ]
    fake = FakeEnvCheckService(cached=None, results=results)
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await _wait_for_check(pilot, app)
        lines = _verdict_lines(app.screen)
        # the critical-fail line names BOTH failing CRITICAL kernels (main()
        # order) with the Phase-11 blocking note, from the strings constant
        expected_verdict = ENV_VERDICT_CRITICAL_FAIL.format(
            kernel_names="cuda, matmul")
        assert expected_verdict in lines
        # 11-05 amendment (11-UI-SPEC Existing-Surface Amendments): the
        # blocking is real this phase — present tense through the launch
        # gate; the retired future-tense wiring note is gone for good
        # (same constant name, same {kernel_names} field, ✗ glyph kept)
        assert "启动已被运行配置启动门阻断" in expected_verdict
        assert "启动流程将被阻断" not in expected_verdict
        # the routing line carries the missing-dataset count AND the CLI
        # audit command (I18N-01: the command stays English verbatim)
        assert ENV_ROUTE_MISSING_DATASETS.format(n=7) in lines


async def test_all_pass_renders_ready_verdict_and_no_routing_line():
    """An all-pass run renders the ready verdict and nothing else below."""
    results = [_pass(kernel_id) for kernel_id in MAIN_KERNEL_ORDER]
    fake = FakeEnvCheckService(cached=None, results=results)
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await _wait_for_check(pilot, app)
        assert _verdict_lines(app.screen) == [ENV_VERDICT_PASS]


async def test_refresh_resets_rows_to_pending_and_reruns():
    """The refresh key is the only re-run path: rows reset, kernels re-run."""
    gate = threading.Event()
    fake = FakeEnvCheckService(cached=None, gate=gate)
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        gate.set()  # the first run completes immediately
        await pilot.pause()
        await _wait_for_check(pilot, app)
        assert len(fake.kernel_calls) == 8
        assert len(fake.persist_calls) == 1

        gate.clear()  # the second run blocks in kernel 0 (observable reset)
        await pilot.press("r")
        table = app.screen.query_one(DataTable)
        for _ in range(100):
            await pilot.pause()
            if _row(table, 0)[0] == ENV_STATE_CHECKING:
                break
        # every row was reset (row 0 is in-flight again — it was a final
        # pass glyph a moment ago; rows 1-7 are back to pending)
        assert _row(table, 0)[0] == ENV_STATE_CHECKING
        for index in range(1, 8):
            assert _row(table, index)[0] == ENV_STATE_PENDING

        gate.set()
        await _wait_for_check(pilot, app)
        assert len(fake.kernel_calls) == 16  # every kernel re-ran
        assert len(fake.persist_calls) == 2  # and persisted again


class _StaleRunFake(FakeEnvCheckService):
    """WR-02's interleave, deterministic: run 1 blocks in its FIRST
    kernel carrying STALE results (version_pins FAIL); the refresh run
    resolves instantly with FRESH results (version_pins PASS) and
    completes while run 1's thread is still blocked. Releasing the gate
    then lets the cancelled run's late CheckItemDone land AFTER the
    fresh run's completion — the handlers must drop it."""

    def __init__(self):
        stale_results = [
            _fail("version_pins", ["FAIL: stale run result"]),
            *_mixed_results()[1:],
        ]
        super().__init__(cached=None, results=stale_results)
        self.first_gate = threading.Event()
        self.gate = self.first_gate
        self._kernels_calls = 0

    def kernels(self):
        self._kernels_calls += 1
        if self._kernels_calls > 1:
            # the refresh run: instant kernels with the FRESH results
            self.gate = None
            self.results = _mixed_results()
        return super().kernels()


async def test_refresh_race_stale_result_never_overwrites_the_fresh_run():
    """WR-02: a cancelled refresh's late kernel result lands after the
    new run completed — it must be dropped, never overwrite the fresh
    row/summary/last-check."""
    fake = _StaleRunFake()
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        table = app.screen.query_one(DataTable)
        # run 1 blocks inside its first kernel (the stale version_pins)
        for _ in range(100):
            await pilot.pause()
            if _row(table, 0)[0] == ENV_STATE_CHECKING:
                break
        assert _row(table, 0)[0] == ENV_STATE_CHECKING

        # the refresh starts the fresh run (cancelling run 1) — it runs
        # to completion and renders its outcome while run 1 still blocks
        await pilot.press("r")
        for _ in range(100):
            await pilot.pause()
            if _label_text(app.screen, "#env-last-check"):
                break
        assert _row(table, 0) == [
            ENV_STATE_PASS,
            ENV_KERNEL_LABELS["version_pins"],
            "torch 2.11.0 == pyproject [gpu] pin",
        ], "the FRESH run's version_pins result must render"
        assert _label_text(app.screen, "#env-last-check") == (
            ENV_LAST_CHECK_LINE.format(checked_at=fake.checked_at)
        )

        # release the stale run's blocked kernel — its late CheckItemDone
        # posts after the fresh run completed. wait_for_complete cannot
        # return before the stale thread finished, so the message is in
        # the queue; the pauses below hand it to the event loop.
        fake.first_gate.set()
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.pause()

        # the stale result was DROPPED: the fresh glyph, summary, and
        # last-check line are all intact (the overwrite is the bug)
        assert _row(table, 0) == [
            ENV_STATE_PASS,
            ENV_KERNEL_LABELS["version_pins"],
            "torch 2.11.0 == pyproject [gpu] pin",
        ], "a stale result from the cancelled run must never overwrite"
        assert _label_text(app.screen, "#env-last-check") == (
            ENV_LAST_CHECK_LINE.format(checked_at=fake.checked_at)
        )
        # exactly one run persisted (the stale thread never reached
        # persist — it returned at the next cancellation poll)
        assert len(fake.persist_calls) == 1


async def test_enter_opens_verbatim_drilldown_modal_blocks_app_bindings():
    """Drill-down: verbatim lines (wrapped, never elided); ModalScreen blocks."""
    fake = FakeEnvCheckService(cached=None)
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await _wait_for_check(pilot, app)

        # move the cursor to the dataset_dirs row (last row — the FAIL with
        # the long double-nested line, i.e. the long-text drill-down case)
        for _ in range(7):
            await pilot.press("down")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(app.screen, EnvDetailModal), "enter must open the modal"
        modal = app.screen
        expected = _mixed_results()[-1]
        assert modal.kernel_id == "dataset_dirs"
        # the modal carries the kernel's lines VERBATIM — byte-for-byte the
        # byte-stable env_smoke contract text (D-02), never elided
        assert modal.detail_lines == expected.lines
        assert modal.query_one("#env-detail-box").border_title == (
            ENV_DETAIL_TITLE.format(
                kernel_id="dataset_dirs",
                label=ENV_KERNEL_LABELS["dataset_dirs"],
            )
        )
        # the RichLog rendered every line — whitespace-normalized ordered
        # containment proves wrapping dropped nothing (wrap, not elide)
        log = modal.query_one("#env-detail-log", RichLog)
        rendered = " ".join(
            "".join(strip.text for strip in log.lines).split()
        )
        cursor = 0
        for line in expected.lines:
            needle = " ".join(line.split())
            position = rendered.find(needle, cursor)
            assert position >= 0, f"drill-down must render {line!r} in order"
            cursor = position + len(needle)

        # app-level bindings do NOT fire while the modal is open (Pitfall 11)
        await pilot.press("r")
        await pilot.pause()
        assert len(fake.kernel_calls) == 8, "r must not refresh through the modal"
        await pilot.press("q")
        await pilot.pause()
        assert app.return_code is None, "q must not quit through the modal"

        # esc closes the modal and the app keeps running
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, EnvDetailModal)


async def test_last_check_line_matches_persisted_checked_at_format_exactly():
    """ENV-02: the rendered line is the persisted checked_at shape verbatim."""
    checked_at = "2026-10-11 09:30"
    # the persisted display shape IS the service's CHECKED_AT_FORMAT
    # (local naive YYYY-MM-DD HH:MM — Pitfall 8's display basis; the
    # deliberate naive construction below IS the contract under test)
    assert datetime.strptime(  # noqa: DTZ007 — naive local is the display shape
        checked_at, env_check_service.CHECKED_AT_FORMAT
    ) == datetime(2026, 10, 11, 9, 30)  # noqa: DTZ001 — naive local, same basis

    fake = FakeEnvCheckService(cached=(checked_at, _mixed_results()))
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        line = _label_text(app.screen, "#env-last-check")
        assert line == ENV_LAST_CHECK_LINE.format(checked_at=checked_at)
        # halfwidth colon, YYYY-MM-DD HH:MM (the ENV-02 verbatim format)
        assert re.fullmatch(r"上次检查: \d{4}-\d{2}-\d{2} \d{2}:\d{2}", line)


def test_state_and_verdict_strings_are_glyph_first_and_distinct():
    """Glyph+color redundancy: distinct leading glyphs carry every state."""
    state_glyphs = [
        ENV_STATE_PASS[0],
        ENV_STATE_FAIL[0],
        ENV_STATE_PENDING[0],
        ENV_STATE_CHECKING[0],
    ]
    assert state_glyphs == ["✓", "✗", "◌", "⠋"]
    assert len(set(state_glyphs)) == 4
    for verdict_line in (
        ENV_VERDICT_PASS,
        ENV_VERDICT_CRITICAL_FAIL,
        ENV_ROUTE_MISSING_DATASETS,
        ENV_ROUTE_MISSING_MODELS,
    ):
        assert verdict_line[0] in {"✓", "✗", "⚠"}, (
            "every color-coded verdict carries its glyph first (NO_COLOR)"
        )


async def test_model_dirs_fail_renders_model_route_without_dataset_line():
    """The 261014-dcl per-kernel routing: a model_dirs FAIL with
    dataset_dirs PASS renders ONLY ENV_ROUTE_MISSING_MODELS — the count
    from the kernel's own listing lines, never a fabricated zero-count
    datasets line (and no download promise: models are placed
    manually)."""
    results = [
        _pass("version_pins"),
        _pass("dnallm"),
        _pass("peft"),
        _pass("cuda"),
        _pass("matmul"),
        _pass("numpy"),
        _fail("model_dirs", [
            ("FAIL: 3 of 62 registry model dir(s) missing on disk "
             "(root: pipeline/):"),
            "  - evo2_1b_base",
            "  - megaDNA_updated",
            "  - PlantHelixSeek",
        ]),
        _pass("dataset_dirs"),
    ]
    fake = FakeEnvCheckService(cached=None, results=results)
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await _wait_for_check(pilot, app)
        lines = _verdict_lines(app.screen)
        # the ready verdict: the routing failure never blocks
        assert ENV_VERDICT_PASS in lines
        # the model route line carries the listing-line count (3)
        assert ENV_ROUTE_MISSING_MODELS.format(n=3) in lines
        # NO datasets routing line — that kernel itself passed
        assert not any(
            line.startswith("⚠") and "数据集目录缺失" in line
            for line in lines
        ), "a passing dataset_dirs must never render a datasets route"


# =====================================================================
# The real backend adapter (sync — real 08-04 service functions, tmp paths)
# =====================================================================

def test_backend_rebuilds_cached_results_from_same_day_state(tmp_path):
    """A same-day persisted state round-trips into (checked_at, results)."""
    path = tmp_path / "env_check.json"
    now = datetime.now().astimezone()
    env_check_service.persist(path, _mixed_results(), now=now)

    cached = EnvCheckBackend(state_path=path).cached_results()
    assert cached is not None
    checked_at, results = cached
    assert checked_at == now.strftime(env_check_service.CHECKED_AT_FORMAT)
    assert [result.name for result in results] == list(MAIN_KERNEL_ORDER)
    assert [result.ok for result in results] == [
        result.ok for result in _mixed_results()
    ]
    # the FAIL detail lines survive the persistence round trip verbatim
    assert results[-1].lines == _mixed_results()[-1].lines


def test_backend_yesterday_state_is_a_cache_miss(tmp_path):
    """Yesterday's state does not satisfy startup (D-05 calendar-day rule)."""
    path = tmp_path / "env_check.json"
    yesterday = datetime.now().astimezone() - timedelta(days=1)
    env_check_service.persist(path, _mixed_results(), now=yesterday)
    assert EnvCheckBackend(state_path=path).cached_results() is None


def test_backend_same_day_seven_item_state_is_a_cache_miss(tmp_path):
    """The 261014-dcl coverage guard: a same-day state file persisted by
    the PRE-change build (seven items — no model_dirs) reads as a cache
    MISS — the screen re-runs once and persists eight, instead of
    stranding the new model_dirs row pending forever."""
    path = tmp_path / "env_check.json"
    now = datetime.now().astimezone()
    pre_change_results = [
        result for result in _mixed_results()
        if result.name != "model_dirs"
    ]
    assert len(pre_change_results) == 7  # the pre-change shape, exactly
    env_check_service.persist(path, pre_change_results, now=now)

    assert EnvCheckBackend(state_path=path).cached_results() is None


def test_backend_corrupt_state_is_a_cache_miss(tmp_path):
    """A corrupt state file is a None-sentinel miss, never a crash."""
    path = tmp_path / "env_check.json"
    path.write_text("{ not json", encoding="utf-8")
    assert EnvCheckBackend(state_path=path).cached_results() is None


def test_backend_persist_returns_display_string_and_writes_state(tmp_path):
    """persist returns the checked_at display string it actually persisted."""
    path = tmp_path / "env_check.json"
    backend = EnvCheckBackend(state_path=path)
    checked_at = backend.persist(_mixed_results())
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", checked_at)
    state = env_check_service.load_cached(path)
    assert state["checked_at"] == checked_at  # display == persisted value
    assert len(state["items"]) == 8


def test_backend_kernels_delegate_to_the_service_main_order_sequence():
    """kernels() is the shared 08-04 sequence — main() order, nothing runs."""
    backend = EnvCheckBackend(state_path=Path("/unused/env_check.json"))
    assert list(backend.kernels()) == list(MAIN_KERNEL_ORDER)


# =====================================================================
# Source-level i18n gate (permanent CI enforcement of the verify gate)
# =====================================================================

def test_screen_module_carries_zero_chinese_literals():
    """I18N-01 single-home: no operator-facing copy outside tui/strings.py."""
    for module_file in _GREP_LOCK_MODULES:
        source = module_file.read_text(encoding="utf-8")
        offenders = re.findall(r"[一-鿿]", source)
        assert not offenders, (
            "Chinese literals must live in tui/strings.py only "
            f"({len(offenders)} found in {module_file.name})"
        )


def test_app_module_carries_zero_chinese_literals():
    """I18N-01 single-home: the composition root carries zero copy too."""
    source = _APP_MODULE_FILE.read_text(encoding="utf-8")
    offenders = re.findall(r"[一-鿿]", source)
    assert not offenders, (
        "Chinese literals must live in tui/strings.py only "
        f"({len(offenders)} found in {_APP_MODULE_FILE.name})"
    )


# =====================================================================
# Task 2 — the composed app at rest (footer, help modal, min-size, styles)
# =====================================================================

async def test_app_boots_with_nav_bars_visible_on_env_check():
    """The composed console boots on env check with the two shell bars
    (the 09-03 migration: the bars replaced the retired Header/Footer —
    the former footer-visibility assertion migrated with the chrome)."""
    fake = FakeEnvCheckService(cached=("2026-10-11 09:30", _mixed_results()))
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, EnvCheckScreen)
        assert app.screen.query_one(TopMenuBar).display, (
            "the top menu bar must render (D-13)"
        )
        assert app.screen.query_one(BottomBar).display, (
            "the bottom submenu bar must render (D-15)"
        )


async def test_help_modal_lists_bindings_and_esc_closes():
    """The ? modal: every binding row from strings, esc closes, q blocked."""
    fake = FakeEnvCheckService(cached=("2026-10-11 09:30", _mixed_results()))
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.press("question_mark")
        await pilot.pause()
        assert isinstance(app.screen, HelpModal), "? must open the help modal"

        modal = app.screen
        assert modal.query_one("#help-box").border_title == APP_HELP_TITLE
        rows = [str(static.content) for static in modal.query(Static)]
        # every binding row, Chinese labels from strings via APP_HELP_ROW
        # (app: q quit + ? help; env screen: r refresh + enter detail —
        # the s row retired with the 09-03 nav-shell migration: menu slot
        # 2 supersedes the alias, and the digit bindings are show=False
        # so the modal's rows are exactly this map)
        expected_rows = [
            APP_HELP_ROW.format(key="q", label=APP_QUIT_LABEL),
            APP_HELP_ROW.format(key="?", label=APP_HELP_LABEL),
            APP_HELP_ROW.format(key="r", label=ENV_REFRESH_LABEL),
            APP_HELP_ROW.format(key="enter", label=ENV_DETAIL_LABEL),
        ]
        assert rows == expected_rows

        # the modal is modal: q does not quit through it
        await pilot.press("q")
        await pilot.pause()
        assert app.return_code is None

        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, HelpModal)
        assert isinstance(app.screen, EnvCheckScreen)


async def test_min_size_guard_swaps_updates_and_restores():
    """Below 80x24 ONLY the min-size message renders; growing restores."""
    fake = FakeEnvCheckService(cached=("2026-10-11 09:30", _mixed_results()))
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, EnvCheckScreen)

        # shrink below the minimum grid -> the guard screen swaps in
        await pilot.resize_terminal(60, 20)
        await pilot.pause()
        assert isinstance(app.screen, MinSizeScreen), (
            "below 80x24 the min-size screen must be the active screen"
        )
        message = app.screen.query_one("#min-size-message", Static)
        assert str(message.content) == APP_MIN_SIZE_MESSAGE.format(w=60, h=20)
        # the message is the ONLY composed content — nothing else renders
        # (the screen beneath is not displayed while a plain Screen is on
        # top)
        assert len(list(app.screen.query(Static))) == 1

        # still below, new dimensions -> the message stays current
        await pilot.resize_terminal(50, 15)
        await pilot.pause()
        assert str(message.content) == APP_MIN_SIZE_MESSAGE.format(w=50, h=15)

        # grow back to the design grid -> the env-check screen restores
        await pilot.resize_terminal(120, 40)
        await pilot.pause()
        assert isinstance(app.screen, EnvCheckScreen)
        assert app.screen.query_one(DataTable).row_count == 8


async def test_min_size_guard_help_suppressed_grow_never_strands():
    """WR-01: ? below the minimum opens nothing (no chrome over the
    guard — a modal there would be popped INSTEAD of the guard on grow,
    stranding the console on the min-size screen at full size); growing
    back restores the screen beneath."""
    fake = FakeEnvCheckService(cached=("2026-10-11 09:30", _mixed_results()))
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, EnvCheckScreen)

        # shrink below the minimum grid -> the guard screen swaps in
        await pilot.resize_terminal(60, 20)
        await pilot.pause()
        assert isinstance(app.screen, MinSizeScreen)

        # ? is suppressed below the minimum: no modal pushed over the
        # guard (the stack stays env + guard)
        await pilot.press("question_mark")
        await pilot.pause()
        assert isinstance(app.screen, MinSizeScreen)
        assert not any(
            isinstance(screen, HelpModal) for screen in app.screen_stack
        ), "no chrome may open over the min-size guard"

        # growing back restores the env-check screen — never the stranded
        # guard at full size
        await pilot.resize_terminal(120, 40)
        await pilot.pause()
        assert isinstance(app.screen, EnvCheckScreen), (
            "the console must never be stranded on the min-size screen "
            "at full size"
        )
        assert app._min_size_screen is None

        # ? works again once above the minimum
        await pilot.press("question_mark")
        await pilot.pause()
        assert isinstance(app.screen, HelpModal)


async def test_no_color_scenario_keeps_distinct_glyphs(monkeypatch):
    """NO_COLOR: the app runs and rendered glyphs stay distinct per state."""
    monkeypatch.setenv("NO_COLOR", "1")
    fake = FakeEnvCheckService(cached=("2026-10-11 09:30", _mixed_results()))
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert app.no_color is True, "textual must register the NO_COLOR mode"

        table = app.screen.query_one(DataTable)
        states = [_row(table, index)[0] for index in range(8)]
        # glyph-first redundancy: with color gone, the DISTINCT glyphs are
        # the entire state signal — both present in the cached mix
        assert {state[0] for state in states} == {
            ENV_STATE_PASS[0], ENV_STATE_FAIL[0],
        }
        assert states[0][0] == ENV_STATE_PASS[0]
        assert states[-1][0] == ENV_STATE_FAIL[0]


def test_styles_tcss_zero_hex_and_declared_spacing_tokens_only():
    """The styles contract: theme variables only; declared spacing tokens."""
    css = _STYLES_FILE.read_text(encoding="utf-8")
    stripped = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)

    # no hardcoded hex in any property value (the optional single-site
    # brand theme is deliberately not landed — so ZERO hex anywhere)
    hex_offenders = re.findall(r":\s*[^;{}]*#[0-9a-fA-F]{3,8}", stripped)
    assert not hex_offenders, f"hardcoded hex forbidden: {hex_offenders}"

    # padding/margin values only from the declared scale: 0/1/2 (the
    # documented exceptions) and 4/8/12 (the md/lg/xl tokens)
    for declaration in re.findall(r"(?:padding|margin)\s*:\s*([^;]+);",
                                  stripped):
        for number in re.findall(r"\d+", declaration):
            assert int(number) in {0, 1, 2, 4, 8, 12}, (
                f"undeclared spacing value {number} in {declaration.strip()!r}"
            )


# =====================================================================
# 261014-f4w — the slot-1 storage overview (F4W-04)
# =====================================================================


def _storage_row_texts(screen):
    """The rendered storage rows' plain texts (glyph + label + path)."""
    return [
        _cell(row.content)
        for row in screen.query("#env-storage .env-storage-row")
    ]


async def test_storage_section_renders_all_five_rows():
    """F4W-04: the section renders the title, all five rows (label +
    absolute path verbatim + the ✓/✗ existence glyph over the frozen
    fixture's exists flags), and the footer note routing edits to
    slot 4 — read-only, no new bindings."""
    fake = FakeEnvCheckService(cached=None, results=_mixed_results())
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _wait_for_check(pilot, app)
        screen = app.screen
        assert _label_text(screen, ".env-storage-title") == (
            ENV_STORAGE_TITLE)
        rows = _storage_row_texts(screen)
        assert len(rows) == 5
        expected = (
            (ENV_STORAGE_LABELS["model_root"], "/golden/models", True),
            (ENV_STORAGE_LABELS["dataset_root"], "/golden/datasets", False),
            (ENV_STORAGE_LABELS["output_root"], "/golden/finetuned", True),
            (ENV_STORAGE_LABELS["log_dir"], "/golden/logs", False),
            (ENV_STORAGE_LABELS["cache_dir"], "/golden/cache", True),
        )
        for text, (label, path, exists) in zip(rows, expected, strict=True):
            glyph = ENV_STATE_PASS if exists else ENV_STATE_FAIL
            assert text.startswith(glyph), (
                f"the glyph leads its row (NO_COLOR carrier): {text!r}"
            )
            assert label in text and path in text, (
                f"the label and the path render verbatim: {text!r}"
            )
        assert _label_text(screen, ".env-storage-note") == ENV_STORAGE_NOTE


async def test_storage_section_rerenders_on_refresh():
    """The r refresh action re-renders the storage section (a slot-4 dir
    change reflects after [r] — the documented staleness boundary)."""

    class _MovedStorageFake(FakeEnvCheckService):
        """The frozen fixture with the model root moved — fresh rows."""

        def storage_rows(self):
            from tui.services.run_config import StorageRow

            return (
                StorageRow("model_root", "/moved/models", True),
                StorageRow("dataset_root", "/golden/datasets", False),
                StorageRow("output_root", "/golden/finetuned", True),
                StorageRow("log_dir", "/golden/logs", False),
                StorageRow("cache_dir", "/golden/cache", True),
            )

    fake = _MovedStorageFake(cached=None, results=_mixed_results())
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _wait_for_check(pilot, app)
        screen = app.screen
        await pilot.press("r")
        await _wait_for_check(pilot, app)
        rows = _storage_row_texts(screen)
        assert any("/moved/models" in text for text in rows), (
            "the refresh re-rendered the section from the fresh rows"
        )


async def test_storage_wrong_key_rows_never_crash_the_render():
    """Forward tolerance (the _apply_result_to_table precedent): a
    service row whose key is outside ENV_STORAGE_LABELS renders its key
    verbatim, never crashes."""
    from tui.services.run_config import StorageRow

    class _FutureKeyFake(FakeEnvCheckService):
        """One row keyed outside the label vocabulary."""

        def storage_rows(self):
            return (StorageRow("future_key", "/future/path", True),)

    fake = _FutureKeyFake(cached=None, results=_mixed_results())
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await _wait_for_check(pilot, app)
        screen = app.screen
        rows = _storage_row_texts(screen)
        assert len(rows) == 1
        assert "future_key" in rows[0] and "/future/path" in rows[0]


# =====================================================================
# 08-08 WR-01 — the env screen survives a broken checkout
# =====================================================================


class _RaisingKernelFake(FakeEnvCheckService):
    """WR-01 (08-08): the MIDDLE kernel raises RuntimeError — the row
    must degrade to the fail glyph with the degraded summary while the
    remaining kernels complete and the run persists whole."""

    def kernels(self):
        kernels = super().kernels()
        middle = list(kernels)[len(kernels) // 2]
        self.raising_id = middle

        def _raising():
            self.kernel_calls.append(middle)
            raise RuntimeError("kernel exploded on a broken checkout")

        kernels[middle] = _raising
        return kernels


async def test_raising_kernel_renders_degraded_row_and_app_stays_alive():
    """WR-01 (08-08): a raising kernel degrades to ONE fail row (the
    degraded summary = the exception type + message through the strings
    constant), the remaining kernels complete around it, the run
    persists WHOLE (D-05 partial-failure-persists-whole), and the app is
    alive at assert time — never a console exit."""
    fake = _RaisingKernelFake(cached=None)
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await _wait_for_check(pilot, app)

        assert app.return_code is None, "the console must stay alive"

        degraded_line = ENV_KERNEL_DEGRADED.format(
            error="RuntimeError: kernel exploded on a broken checkout")
        table = app.screen.query_one(DataTable)
        for index, (kernel_id, outcome) in enumerate(
                zip(MAIN_KERNEL_ORDER, _mixed_results(), strict=True)):
            row = _row(table, index)
            if kernel_id == fake.raising_id:
                assert row[0] == ENV_STATE_FAIL, (
                    "the raising kernel's row must degrade to the fail glyph"
                )
                # the summary derives from the degraded line's own first
                # detail line (the _summary_of prefix strip)
                assert row[2] == degraded_line.removeprefix("FAIL: ")
            else:
                # every other kernel completed with its OWN outcome (the
                # standard scenario's deliberate dataset_dirs FAIL
                # included — the raise never disturbed its neighbors)
                expected = (
                    ENV_STATE_PASS if outcome.ok else ENV_STATE_FAIL)
                assert row[0] == expected, (
                    f"kernel {kernel_id} must complete normally"
                )

        # every kernel still executed (the loop continued past the raise)
        assert fake.kernel_calls == list(MAIN_KERNEL_ORDER)
        # the run persisted WHOLE — eight items, the degraded one included
        assert len(fake.persist_calls) == 1
        persisted = fake.persist_calls[0]
        assert [result.name for result in persisted] == list(
            MAIN_KERNEL_ORDER)
        degraded = next(
            result for result in persisted
            if result.name == fake.raising_id)
        assert degraded.ok is False
        assert degraded.lines == (degraded_line,)


class _BrokenEnumerationFake(FakeEnvCheckService):
    """WR-01 (08-08): ``kernels()`` itself raises — the enumeration of
    the kernel sequence fails on exactly the broken-checkout state the
    opening screen exists to diagnose."""

    def kernels(self):
        raise RuntimeError("kernels() unavailable on a broken checkout")


async def test_broken_checkout_kernels_enumeration_survives():
    """WR-01 (08-08): a failing ``kernels()`` enumeration degrades EVERY
    ENV_KERNEL_LABELS row to the fail glyph with the degraded summary,
    the run routes through the same persist + completion tail, and the
    app survives — the console diagnoses the broken checkout instead of
    dying on it."""
    fake = _BrokenEnumerationFake(cached=None)
    app = DnallmMarkTui(env_check_service=fake)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await _wait_for_check(pilot, app)

        assert app.return_code is None, "the console must stay alive"

        degraded_summary = ENV_KERNEL_DEGRADED.format(
            error="RuntimeError: kernels() unavailable on a broken checkout",
        ).removeprefix("FAIL: ")
        table = app.screen.query_one(DataTable)
        for index, kernel_id in enumerate(MAIN_KERNEL_ORDER):
            row = _row(table, index)
            assert row[0] == ENV_STATE_FAIL, (
                f"row {kernel_id} must degrade to the fail glyph"
            )
            assert row[2] == degraded_summary

        # the run still routed through the persist + completion tail
        assert len(fake.persist_calls) == 1
        persisted = fake.persist_calls[0]
        assert [result.name for result in persisted] == list(
            MAIN_KERNEL_ORDER)
        assert all(result.ok is False for result in persisted)
        # the last-check line rendered — the run completed, not stranded
        assert _label_text(app.screen, "#env-last-check") == (
            ENV_LAST_CHECK_LINE.format(checked_at=fake.checked_at)
        )
