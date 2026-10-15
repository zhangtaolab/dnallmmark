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
from textual.widgets import DataTable, Label, Static

from tui import strings
from tui.app import DnallmMarkTui, remap_binding_descriptions
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


# =====================================================================
# The L language toggle (261015-ehc, EHC-1 — Task 2 Pilot tests)
# =====================================================================


def _toast_messages(app):
    """The active notification messages (the toast assertions)."""
    return [notification.message for notification in app._notifications]


def _env_row_word(app, row: int = 0) -> str:
    """The first data row's kernel-label cell (plain text)."""
    table = app.screen.query_one(DataTable)
    cell = table.get_row_at(row)[1]
    return cell.plain if isinstance(cell, Text) else str(cell)


async def test_default_language_renders_english_on_a_fresh_boot():
    """EHC-1: the committed default is English — with the registry set
    to en inside the test (conftest pins zh at collection), a freshly
    constructed app's opening screen renders the English copy: the
    screen title, a state word, and the storage title."""
    strings.set_language("en")
    try:
        app = DnallmMarkTui(env_check_service=_CacheHitFake())
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            title = str(
                app.screen.query_one("#env-screen-title", Label).content)
            assert title == "Environment Check", (
                "the committed default language is English"
            )
            assert _env_row_word(app) == "version pins", (
                "kernel labels render in the active language"
            )
            storage_labels = app.screen.query(Static).filter(
                ".env-storage-title")
            assert storage_labels, "the storage section must render"
            assert str(storage_labels.first().content) == (
                strings.ENV_STORAGE_TITLE)
            assert strings.APP_TITLE == "DNALLM-Mark Console"
    finally:
        strings.set_language("zh")


async def test_L_toggles_language_live_without_restart():
    """EHC-1: L flips zh -> en on the SAME mounted screen (title + row
    word re-render), the footer's quit label follows, a toast fires;
    a second L returns zh. No restart, no unhandled-key error."""
    app = DnallmMarkTui(env_check_service=_CacheHitFake())
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert strings.language() == "zh"
        assert _env_row_word(app) == "版本 pin"
        title_before = str(
            app.screen.query_one("#env-screen-title", Label).content)

        await pilot.press("L")
        await pilot.pause()
        await pilot.pause()

        assert strings.language() == "en", "L must flip the registry"
        assert isinstance(app.screen, EnvCheckScreen), (
            "the SAME screen stays mounted (no restart, no re-push)"
        )
        title_after = str(
            app.screen.query_one("#env-screen-title", Label).content)
        assert title_after == "Environment Check" != title_before
        assert _env_row_word(app) == "version pins", (
            "the row re-renders in the new language (the recompose-alone "
            "row-loss trap is the probe this pins)"
        )
        footer = str(app.screen.query_one(
            "#nav-right-keycaps", Static).content)
        assert "Quit" in footer and "退出" not in footer, (
            "the app-level footer labels follow the toggle"
        )
        assert strings.APP_LANGUAGE_TOAST in _toast_messages(app), (
            "the confirmation toast fires"
        )

        await pilot.press("L")
        await pilot.pause()
        await pilot.pause()
        assert strings.language() == "zh"
        assert _env_row_word(app) == "版本 pin", (
            "the second L returns the zh copy"
        )


async def test_L_persists_language_and_boot_loads_it_back(
        monkeypatch, tmp_path):
    """EHC-1: L writes language.json under the redirectable XDG state
    root; the __main__ boot-load helper (called directly) reads it back;
    a corrupt or absent file resolves to DEFAULT_LANGUAGE, never
    raises."""
    import json as json_module

    import tui.__main__ as tui_main
    from tui.services import settings

    state = tmp_path / "state"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    try:
        app = DnallmMarkTui(env_check_service=_CacheHitFake())
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            await pilot.press("L")
            await pilot.pause()

            persisted = json_module.loads(
                (state / "language.json").read_text(encoding="utf-8"))
            assert persisted == {"language": "en"}, (
                "pressing L persists the new language"
            )
            assert tui_main.load_persisted_language() == "en", (
                "the boot-load helper reads the choice back"
            )

        # corrupt / wrong-value / absent files resolve to the default
        (state / "language.json").write_text(
            "{not json", encoding="utf-8")
        assert (tui_main.load_persisted_language()
                == strings.DEFAULT_LANGUAGE)
        (state / "language.json").write_text(
            json_module.dumps({"language": "klingon"}), encoding="utf-8")
        assert (tui_main.load_persisted_language()
                == strings.DEFAULT_LANGUAGE)
        (state / "language.json").unlink()
        assert (tui_main.load_persisted_language()
                == strings.DEFAULT_LANGUAGE)
    finally:
        # module state is test-process-wide: restore BOTH the language
        # and the remapped class BINDINGS descriptions (the toggle
        # remutates them globally — an en residue breaks later zh
        # footer/help assertions)
        strings.set_language("zh")
        remap_binding_descriptions("en", "zh")


async def test_constructing_the_app_never_reads_the_language_file(
        monkeypatch, tmp_path):
    """EHC-1 (the boot_resume_queue inertness precedent): constructing
    DnallmMarkTui NEVER reads language.json — the boot load lives only
    in tui/__main__.main, so test-constructed apps stay inert."""
    import json as json_module

    import tui.__main__ as tui_main
    from tui.services import settings

    state = tmp_path / "state"
    state.mkdir(parents=True)
    (state / tui_main.LANGUAGE_FILE_NAME).write_text(
        json_module.dumps({"language": "zh"}), encoding="utf-8")
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))

    strings.set_language("en")
    try:
        DnallmMarkTui(env_check_service=_CacheHitFake())
        assert strings.language() == "en", (
            "construction must not apply the persisted language"
        )
    finally:
        strings.set_language("zh")
