"""
The CR-01 render-time i18n pin (quick-261016-hhx — the 08 delta review's
critical finding).

Why this pin is load-bearing:

``tui/strings.py``'s ``set_language`` rebinds the registry constants
through ``globals()`` so MODULE-ATTRIBUTE reads (``S.CONST``) resolve the
new language immediately — but any value captured into a consuming
module's module-level tuple/dict or a class-body ClassVar at IMPORT time
is frozen forever in the boot language (production boots English:
``tui/__main__`` imports the whole screen tree before the persisted
language loads). The L toggle (and a persisted-zh boot) then renders a
MIXED-language console — zh chrome over en column headers, state words,
keycaps, wizard labels — while the zh-pinned test conftest imports
everything under zh and structurally cannot see the production en-boot
path.

The fix converts every frozen structure to a render-time re-derivation
function (the ``env_check.py``/``matrix.py`` pattern), with four
sanctioned exceptions:

- ``tui/screens/nav.py`` ``NAV_SLOTS`` / ``_NAV_SLOTS_LANGUAGE`` — the
  documented mount-time re-translation site (``TopMenuBar`` re-translates
  the frozen labels through ``translate_value`` at every mount);
- any class-body ``BINDINGS`` assignment — frozen at import by textual
  8.2.8 (``Binding.description`` cannot be mutated), owned by
  ``remap_binding_descriptions`` which rebuilds them in place on every
  toggle/boot-remap;
- ``tui/app.py`` ``TITLE`` — re-set by the toggle itself
  (``self.title = S.APP_TITLE``).

The invariant (test 1, structural): parsing every ``tui/**/*.py`` except
``strings.py``, NO module-top-level or class-body assignment may
reference a ``tui.strings`` registry constant — through the module alias
(``S.CONST``) or a from-imported binding — except the four sanctioned
sites above. A future frozen capture fails HERE naming file:line, before
it can ship a mixed-language render.

The behavioral pin (test 2): a Pilot test toggles L on the mounted
data-manager screen and asserts the queue table's column headers and the
pending row's state cell equal the FRESH module-attribute reads under
the new language — pre-fix this fails with the frozen import-time values
(zh under the conftest pin), post-fix it passes. Assertions compare
against module-attribute reads, NEVER literals, so a copy value change
cannot silently unpin them.

The wizard pin (test 3): a freshly built kind spec carries the ACTIVE
language's step names and field labels (unit-level, via the render-time
builder) — restored zh returns zh copy.
"""

import ast
from pathlib import Path

from env_smoke import CheckResult
from rich.text import Text
from textual.widgets import DataTable

from tui import strings as tui_strings
from tui.app import DnallmMarkTui, remap_binding_descriptions
from tui.services.download_queue import QueueEntry

REPO_ROOT = Path(__file__).resolve().parents[2]
TUI_ROOT = REPO_ROOT / "tui"

#: The sanctioned frozen-capture sites (the module header's four): the
#: nav bar's mount-time re-translation pair, class-body BINDINGS
#: (remap-owned), and the app TITLE (toggle-owned).
_ALLOWLIST = {
    # (repo-relative path, target name) — a module-level OR class-body
    # assignment with this target in this file may reference registry
    # constants.
    ("tui/screens/nav.py", "NAV_SLOTS"),
    ("tui/screens/nav.py", "_NAV_SLOTS_LANGUAGE"),
    ("tui/app.py", "TITLE"),
}
#: The any-module entry: class-body ``BINDINGS`` declarations everywhere
#: (remap_binding_descriptions owns their live translation).
_ALLOWLIST_ANY_MODULE = {"BINDINGS"}


def _strings_aliases(tree: ast.Module) -> "tuple[set[str], set[str]]":
    """(module-alias names, from-imported binding names) for one tree.

    Covers both import forms: ``from tui import strings [as X]`` (the
    screens' ``S`` alias) and ``from tui.strings import A, B`` (direct
    constant bindings — frozen copies of the constants themselves).
    """
    aliases: set[str] = set()
    from_names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module == "tui":
            for alias in node.names:
                if alias.name == "strings":
                    aliases.add(alias.asname or "strings")
        elif node.module == "tui.strings":
            for alias in node.names:
                from_names.add(alias.asname or alias.name)
    return aliases, from_names


def _references_registry_constant(node: ast.expr, aliases: set[str],
                                  from_names: set[str],
                                  registry: set[str]) -> bool:
    """True when the expression reads a registry constant ANYWHERE inside
    it — a bare ``S.CONST``, a ``S.CONST[...]`` subscript, a
    ``S.CONST.split(...)`` projection, or a from-imported binding."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Attribute):
            if (isinstance(sub.value, ast.Name)
                    and sub.value.id in aliases
                    and sub.attr in registry):
                return True
        elif (isinstance(sub, ast.Name)
                and sub.id in from_names and sub.id in registry):
            return True
    return False


def _flag_module_captures(tree: ast.Module, rel: str, aliases: set[str],
                          from_names: set[str], registry: set[str],
                          ) -> list[str]:
    """The offender messages for ONE parsed module (the per-file half of
    the checker — a plain function per call so the inner walk closes
    over call-local bindings, never loop variables)."""
    messages: list[str] = []

    def visit(stmts: list[ast.stmt], owner: str) -> None:
        for stmt in stmts:
            if isinstance(stmt, ast.ClassDef):
                visit(stmt.body, f"{owner}.{stmt.name}")
                continue
            if not isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                continue
            if stmt.value is None or not _references_registry_constant(
                    stmt.value, aliases, from_names, registry):
                continue
            targets = (stmt.targets if isinstance(stmt, ast.Assign)
                       else [stmt.target])
            names = [target.id for target in targets
                     if isinstance(target, ast.Name)]
            allowed = (any((rel, name) in _ALLOWLIST for name in names)
                       or any(name in _ALLOWLIST_ANY_MODULE
                              for name in names))
            if not allowed:
                messages.append(
                    f"{rel}:{stmt.lineno} {owner} — module/class-level "
                    f"capture of tui.strings registry constant(s) into "
                    f"{names or '<non-name target>'!r} (read S.* at "
                    "render time instead — CR-01)")

    visit(tree.body, "<module>")
    return messages


def import_frozen_capture_violations(paths) -> "list[str]":
    """The offender messages for the given modules — every failure names
    file:line and the captured target.

    Args:
        paths: iterable of ``.py`` paths (the ``tui/`` tree or a temp
            control module).

    Returns:
        list[str]: empty when no module/class-level assignment outside
        the allowlist references a ``tui.strings`` registry constant.
    """
    registry = set(tui_strings._REGISTRY)
    messages: list[str] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.name == "strings.py":
            continue  # the registry module itself defines the constants
        try:
            rel = str(path.relative_to(REPO_ROOT))
        except ValueError:
            rel = str(path)
        tree = ast.parse(
            path.read_text(encoding="utf-8"), filename=str(path))
        aliases, from_names = _strings_aliases(tree)
        if not aliases and not from_names:
            continue  # the module never touches the strings registry
        messages.extend(
            _flag_module_captures(tree, rel, aliases, from_names, registry))
    return messages


def test_no_import_frozen_registry_captures():
    """CR-01, structural: no module-top-level or class-body assignment
    outside the four sanctioned sites references a tui.strings registry
    constant — every copy value re-derives at render time (the
    env_check/matrix pattern), so the L toggle and a persisted-zh boot
    render ONE language everywhere."""
    paths = sorted(TUI_ROOT.rglob("*.py"))
    violations = import_frozen_capture_violations(paths)
    assert not violations, (
        "module/class-level captures of tui.strings constants freeze the "
        "boot language into the render (CR-01) — offending sites:\n  "
        + "\n  ".join(violations)
    )


def test_scanner_flags_frozen_capture_positive_control(tmp_path):
    """The positive control: the detector itself detects a frozen
    capture, so the green tree-assertion above cannot pass vacuously
    through a broken pattern — the scanner flags the temp module's
    module-level tuple capture naming file:line (the
    test_card_site_hardening idiom)."""
    module = tmp_path / "positive_control.py"
    module.write_text(
        "from tui import strings as S\n"
        "\n"
        "_COLUMNS = (\n"
        '    ("task", S.QUEUE_COL_TASK, 33),\n'
        ")\n",
        encoding="utf-8",
    )

    flagged = import_frozen_capture_violations([module])
    assert any(
        f"{module}:3 <module>" in message for message in flagged), (
        f"the positive control must be flagged naming file:line, got: "
        f"{flagged}"
    )


# =====================================================================
# The behavioral pins (the toggle Pilot + the wizard unit)
# =====================================================================


class _EnvCacheHitFake:
    """The minimal env-check service fake (same-day cache hit) — the
    boot screen must spawn zero real kernels."""

    def cached_results(self):
        return ("2026-10-16 09:30", tuple(
            CheckResult(name=kernel_id, ok=True,
                        lines=(f"PASS: {kernel_id}",))
            for kernel_id in tui_strings.ENV_KERNEL_LABELS
        ))

    def storage_rows(self):
        from tui.services.run_config import StorageRow

        return (
            StorageRow("model_root", "/golden/models", True),
            StorageRow("dataset_root", "/golden/datasets", False),
            StorageRow("output_root", "/golden/finetuned", True),
            StorageRow("log_dir", "/golden/logs", False),
            StorageRow("cache_dir", "/golden/cache", True),
        )

    def kernels(self):
        raise AssertionError("a cache-hit boot must never spawn the worker")

    def persist(self, results):
        raise AssertionError("a cache-hit boot must never persist")


class _OnePendingQueueFake:
    """The minimal app-level queue fake: the slot-3 screen mounts over
    ONE pending DATASET entry (its snapshot/misses stay empty — the
    queue pane's headers and state cell are the only surfaces under
    test). ``claim_next``/``run_task`` satisfy the app's driver Protocol
    surface but never run — nothing enqueues, so no driver is kicked
    (the test-constructed app inertness contract)."""

    def __init__(self):
        self._entry = QueueEntry(
            key="GUE__emp_H3", kind="dataset", state="pending", attempts=0,
            enqueued_at="2026-10-16T10:00:00", started_at=None,
            finished_at=None, last_percent=None, interrupted=False,
            log_path=None, problems=(), reconcile=None)

    def load(self):
        return None

    def entries(self):
        return [self._entry]

    def claim_next(self):
        return None

    def run_task(self, key, run_id, progress_cb=None):
        raise AssertionError("no download ever runs in this pin")

    def missing_datasets(self):
        return ()

    def presence_rows(self):
        return ()

    def merged_audit_tasks(self):
        return {}  # the Backend's summary lane over a not-None n_audit

    def probe_zenodo(self):
        return "not_public"


def _cell_text(value):
    """Plain text of one DataTable cell (cells carry rich Text)."""
    return value.plain if isinstance(value, Text) else str(value)


def _header(table, column_key):
    """One rendered column-header label (the sibling-suite idiom — an
    unannotated helper keeps the textual Columns mapping's str-keyed
    lookup out of ty's literal-key reach)."""
    return str(table.columns[column_key].label)


async def test_toggle_rerderives_data_manager_columns_and_state_cells(
        monkeypatch, tmp_path):
    """CR-01, behavioral: pressing L on the mounted data-manager screen
    re-derives the queue table's column headers and the pending row's
    state cell in the NEW language — every assertion compares against
    FRESH module-attribute reads, never literals (value-change-proof for
    the WR-01 QUEUE_STATE_PENDING edit).

    The conftest pins zh BEFORE the screen modules import, so this Pilot
    boots as the production en-boot mirror in reverse: the headers render
    zh first, then the L press must flip them to en. STATE_DIR_ENV is
    monkeypatched so the toggle's language.json write lands in tmp_path;
    the CRITICAL finally-block restores BOTH the active language and the
    class BINDINGS descriptions (the toggle rebuilds them in place —
    later zh Pilot/golden tests depend on the restore)."""
    from tui.services import settings as tui_settings

    state = tmp_path / "state"
    state.mkdir(parents=True)
    monkeypatch.setenv(tui_settings.STATE_DIR_ENV, str(state))
    app = DnallmMarkTui(
        env_check_service=_EnvCacheHitFake(),
        download_queue_service=_OnePendingQueueFake(),
    )
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("3")
            await pilot.pause()
            await app.workers.wait_for_complete()
            await pilot.pause()
            table = app.screen.query_one("#dl-queue", DataTable)

            # pre-toggle (zh under the conftest pin): the header equals
            # the fresh module-attribute read — BOTH sides of the toggle
            # assert the same way, so a value change can never unpin it
            assert tui_strings.language() == "zh"
            assert _header(table, "task") == (
                tui_strings.QUEUE_COL_TASK), (
                "the zh queue header must equal the fresh registry read"
            )
            pending_zh = tui_strings.QUEUE_STATE_PENDING
            assert _cell_text(table.get_row_at(0)[1]) == pending_zh, (
                "the pending row's state cell must equal the fresh "
                "registry read (zh)"
            )

            # the toggle: headers + state cells re-derive (CR-01)
            await pilot.press("L")
            await pilot.pause()
            await app.workers.wait_for_complete()
            await pilot.pause()

            assert tui_strings.language() == "en"
            table = app.screen.query_one("#dl-queue", DataTable)
            assert _header(table, "task") == (
                tui_strings.QUEUE_COL_TASK), (
                "post-toggle the queue header must equal the FRESH en "
                "read — a frozen import-time value here is the CR-01 bug"
            )
            assert _header(table, "state") == (
                tui_strings.QUEUE_COL_STATE), (
                "post-toggle the state header must equal the FRESH en read"
            )
            pending_en = tui_strings.QUEUE_STATE_PENDING
            assert pending_en != pending_zh, (
                "the pin's discriminating precondition: the two "
                "languages must disagree on the pending state word"
            )
            assert _cell_text(table.get_row_at(0)[1]) == pending_en, (
                "the pending row's state cell must re-derive to the "
                "fresh en registry read"
            )
    finally:
        tui_strings.set_language("zh")
        remap_binding_descriptions("en", "zh")


def test_kind_spec_reads_active_language():
    """CR-01, wizard: a freshly built kind spec reads the ACTIVE
    language's step names and field labels (unit-level over the
    render-time builder) — under en it carries en copy, restored zh it
    carries zh."""
    from tui import strings as S
    from tui.screens import wizard

    try:
        tui_strings.set_language("en")
        spec = wizard._kind_spec("models")
        assert spec.steps[0].name == S.WIZM_STEPS[0], (
            "the kind spec's step names must be the fresh en reads"
        )
        assert spec.labels["key"] == S.WIZM_FIELD_LABELS["key"], (
            "the field-label map must be the fresh en read"
        )
        assert spec.kind_name == S.WIZ_KIND_MODELS

        tui_strings.set_language("zh")
        spec_zh = wizard._kind_spec("models")
        assert spec_zh.steps[0].name == S.WIZM_STEPS[0], (
            "restored zh, the same call returns the fresh zh reads"
        )
        assert spec_zh.steps[0].name != spec.steps[0].name, (
            "the two languages must disagree on the step name (the pin's "
            "discriminating precondition)"
        )
        assert spec_zh.kind_name == S.WIZ_KIND_MODELS
    finally:
        tui_strings.set_language("zh")
