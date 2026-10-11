"""
Tier-2 Pilot boot test for the 08-03 tracer (Phase 8).

Boots the REAL ``DnallmMarkTui`` headlessly — the same class the
``make tui`` recipe (``uv run --group tui --group gpu python -m tui``)
runs — and asserts the tracer contract end-to-end:

- the app opens on the env-check screen (the registered opening screen);
- the table carries exactly the seven fixed rows in ``main()`` kernel
  order, each rendering the pending state plus its kernel label from
  ``tui/strings.py`` constants (I18N-01), keyed on the stable kernel id;
- pressing ``q`` quits cleanly (return code 0).

Pilot discipline (08-RESEARCH Pattern 7 / Pitfall 7): ``await
pilot.pause()`` before every assertion — message-driven state (screen
mount, row composition) must settle first; ``asyncio_mode = "auto"``
(pyproject, 08-02) makes the async test need no marker.

No fakes on this path: the shell makes zero service calls and zero
kernel imports (plan prohibition), so the boot is deterministic
CPU-side.
"""

from textual.widgets import DataTable

from tui.app import DnallmMarkTui
from tui.screens.env_check import EnvCheckScreen
from tui.strings import ENV_KERNEL_LABELS, ENV_STATE_PENDING


async def test_boots_on_env_check_shell_seven_pending_rows_quits_on_q():
    """The tracer path: boot → env-check shell → 7 pending rows → q quits."""
    app = DnallmMarkTui()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        # the app opened on the env-check screen
        assert isinstance(app.screen, EnvCheckScreen), (
            "the console must open on the env-check screen"
        )

        table = app.screen.query_one(DataTable)
        assert table.row_count == 7, (
            "the shell must carry exactly the seven fixed kernel rows"
        )

        # main() kernel order + pending state + strings labels (I18N-01);
        # each row is keyed on its stable kernel id (the 08-06 update seam)
        for index, (kernel_id, label) in enumerate(
                ENV_KERNEL_LABELS.items()):
            expected = [ENV_STATE_PENDING, label]
            assert table.get_row_at(index) == expected, (
                f"row {index} must render the pending state + label in "
                f"main() kernel order (expected {kernel_id})"
            )
            assert table.get_row(kernel_id) == expected, (
                f"row must be keyed on the stable kernel id {kernel_id!r}"
            )

        # q quits cleanly (the app-level binding registered in 08-03)
        await pilot.press("q")
        await pilot.pause()
        assert app.return_code == 0, "q must quit the console cleanly"
