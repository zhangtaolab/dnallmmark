"""
Tier-2 Pilot boot test for the composed console (Phase 8; 08-03 tracer,
updated by the 08-06 screen build).

Boots the REAL ``DnallmMarkTui`` headlessly — the same class the
``make tui`` recipe (``uv run --group tui --group gpu python -m tui``)
runs — and asserts the boot contract end-to-end:

- the app opens on the env-check screen (the registered opening screen);
- the table carries exactly the eight fixed rows in ``main()`` kernel
  order (261014-dcl added the model_dirs row before dataset_dirs), each
  rendering its FINAL state (the fake's cache hit renders instantly —
  the 08-06 cache path), its kernel label from ``tui/strings.py``
  constants (I18N-01), keyed on the stable kernel id;
- the last-check line renders from the cached ``checked_at`` (ENV-02);
- pressing ``q`` quits cleanly (return code 0).

08-06 update: the shell this test pinned (seven PENDING rows, zero
service calls) was replaced by the full screen build — the boot test now
injects a deterministic same-day cache-hit fake through the app's
constructor seam (D-03: no real kernel — GPU or otherwise — executes in
CI) and asserts the populated cache-hit boot instead of the shell boot.

Pilot discipline (08-RESEARCH Pattern 7 / Pitfall 7): ``await
pilot.pause()`` before every assertion; ``asyncio_mode = "auto"``
(pyproject, 08-02) makes the async test need no marker.
"""

from env_smoke import CheckResult
from rich.text import Text
from textual.widgets import DataTable, Label

from tui.app import DnallmMarkTui
from tui.screens.env_check import EnvCheckScreen
from tui.strings import (
    ENV_KERNEL_LABELS,
    ENV_LAST_CHECK_LINE,
    ENV_STATE_PASS,
)

# A deterministic same-day cache hit: every kernel passed, checked at a
# fixed moment. kernels()/persist() raise if ever called — a cache hit
# must spawn ZERO kernels (D-05) and the boot test must prove it.
_CACHED_CHECKED_AT = "2026-10-11 09:30"
_CACHED_RESULTS = tuple(
    CheckResult(name=kernel_id, ok=True, lines=(f"PASS: {kernel_id}",))
    for kernel_id in ENV_KERNEL_LABELS
)


class _CacheHitFake:
    """The minimal env-check service fake for the boot path (D-03)."""

    def cached_results(self):
        return (_CACHED_CHECKED_AT, _CACHED_RESULTS)

    def kernels(self):
        raise AssertionError("a same-day cache hit must never spawn the worker")

    def persist(self, results):
        raise AssertionError("a same-day cache hit must never persist")


def _cell(value):
    """Plain text of a DataTable cell (state cells carry rich Text styles)."""
    return value.plain if isinstance(value, Text) else str(value)


async def test_boots_on_env_check_screen_quits_on_q():
    """The boot path: app -> env-check screen -> cached final rows -> q quits."""
    app = DnallmMarkTui(env_check_service=_CacheHitFake())
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        # the app opened on the env-check screen
        assert isinstance(app.screen, EnvCheckScreen), (
            "the console must open on the env-check screen"
        )

        table = app.screen.query_one(DataTable)
        assert table.row_count == 8, (
            "the screen must carry exactly the eight fixed kernel rows"
        )

        # main() kernel order + final cached states + strings labels
        # (I18N-01); each row is keyed on its stable kernel id; the summary
        # column carries the kernel's own first detail line (prefix-stripped
        # — the fake's lines are "PASS: {kernel_id}", so the summary IS the
        # kernel id)
        for index, (kernel_id, label) in enumerate(
                ENV_KERNEL_LABELS.items()):
            expected = [ENV_STATE_PASS, label, kernel_id]
            assert [_cell(cell) for cell in table.get_row_at(index)] == (
                expected
            ), (
                f"row {index} must render the cached final state + label "
                f"+ summary in main() kernel order (expected {kernel_id})"
            )
            assert [_cell(cell) for cell in table.get_row(kernel_id)] == (
                expected
            ), f"row must be keyed on the stable kernel id {kernel_id!r}"

        # the last-check line renders from the cached checked_at (ENV-02)
        last_check = app.screen.query_one("#env-last-check", Label)
        line = str(last_check.content)
        assert line == ENV_LAST_CHECK_LINE.format(
            checked_at=_CACHED_CHECKED_AT
        )

        # q quits cleanly (the app-level binding registered in 08-03)
        await pilot.press("q")
        await pilot.pause()
        assert app.return_code == 0, "q must quit the console cleanly"
