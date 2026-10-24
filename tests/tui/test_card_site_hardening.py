"""
The card-extraction family pin (Phase 8, 08-09, Task 2 — the Truth-6
round-2 structural floor).

Why this pin is load-bearing:

the 08-08 gap closure made the LOAD-path seams tolerant of the Phase 7
loader's deliberately-merged non-dict card values (the empty-card
projection, chain 1) — but the projection keeps the value VERBATIM, so
every downstream consumer of the ``card`` field inherits the untrusted
shape. The round-2 verification reproduced two SCREEN-SIDE direct card
reads crashing the whole console through textual 8.2.8's
``App._handle_exception`` (``build_wizard``'s observed-vocabularies
comprehensions on ANY ``w`` press; ``_open_detail`` -> ``RowDetailModal``
on ``enter`` over the degraded row), and a third site
(``_manual_landing_path``) surviving only behind an incidental shield.
08-09 landed the isinstance guards; THIS pin makes the family closure
STRUCTURAL — an extraction site cannot silently regrow anywhere in
``tui/``.

The invariant (both directions):

- every card EXTRACTION site — an ``X["card"]`` subscript or an
  ``X.get("card")`` call — must live in one of the four allowlisted
  functions, each of which must still contain an ``isinstance(...,
  dict)`` guard (deleting a guard fails the pin even though the site
  stays allowlisted);
- any NEW extraction site anywhere in ``tui/`` fails naming file:line
  until it gets a guard AND a conscious allowlist + ledger decision.

Non-vacuity floor: the scan must find at least 4 extraction nodes, so a
parsing regression (a pattern-form change that hides every site) cannot
pass the pin silently on an empty collection. The positive control
drives the same scanner over a temp module holding one unguarded
extraction — proving the detector detects, so the green tree-assertion
cannot pass vacuously through a broken pattern.

Per-site sweep ledger — the COMPLETE enumeration of card-field access
on ``tui/`` paths at 08-09 plan time (29 raw grep hits, every one
accounted for; this table is the human-readable twin of ALLOWLIST):

| # | Site | Access shape | Disposition |
|---|------|--------------|-------------|
| 1 | screens/selection.py build_wizard observed vocabularies | ``entry["card"].get(...)`` x6 over ALL merged entries (any ``w`` press, any cursor) | GUARD — 08-09 Task 1 (crash site 1) |
| 2 | screens/selection.py _open_detail | ``entry.get("card") or {}`` — truthy non-dict defeats the ``or`` | GUARD — 08-09 Task 1 (crash site 2a) |
| 3 | screens/selection.py RowDetailModal (param ``self._card``, ``.items()``) | reads its constructor param only | SAFE BY CONTRACT after site 2's guard — the modal's sole call site passes only dicts; annotation ``card: dict`` stays truthful; NOT modified |
| 4 | screens/selection.py _manual_landing_path | ``(entry.get("card") or {}).get("Model_path")`` — same defeated idiom | GUARD — 08-09 Task 1 hardening (was shielded only incidentally by the UNKNOWN-presence early return) |
| 5 | screens/selection.py management-read loop + _custom_model_entry/_custom_dataset_entry | loop passes the management entry to the projections after ``if not isinstance(entry, dict): continue``; the projections' ``card.get(...)`` reads are param-typed | ALREADY SAFE — the loop guard is the sole feed |
| 6 | services/registries.py _project_model_entry/_project_dataset_entry | param-typed card reads behind their own non-dict early returns | ALREADY SAFE — 08-08 |
| 7 | services/selection.py model_presence | ``card = entry.get("card")`` + isinstance-guarded ``.get`` | ALREADY SAFE — the 08-08 guard; the idiom Task 1 mirrors |
| 8 | every other screen (matrix, data_manager, monitor, env_check, run_config, about, wizard, nav) + tui/app.py | zero card-extraction hits in the sweep | NO CARD READS — the pin enforces this stays true |

ALLOWLIST = exactly rows 1, 2, 4, 7 (the four extraction-bearing
functions). Row 3 and row 5's projections are param-consumers outside
the extraction pattern (documented above, not pinned); row 8 is the
pin's core guarantee.

Boundary honesty: the pin covers EXTRACTION sites (pulling the card
field off an entry). Param-typed card reads (``registries
_project_*_entry``, ``selection _custom_model_entry`` /
``_custom_dataset_entry``, ``RowDetailModal._card``) are out of the
pattern's reach BY DESIGN — the ledger documents each as
guarded-by-construction-site with its evidence row, and any NEW
extraction feeding them would itself be a new extraction node the pin
catches.
"""

import ast
from pathlib import Path

TUI_ROOT = Path(__file__).resolve().parents[2] / "tui"

#: The non-vacuity floor: 5 card-extraction nodes at 08-09 HEAD (2 in
#: build_wizard's guarded comprehensions, 1 each in _open_detail,
#: _manual_landing_path, model_presence); the count only grows.
MIN_CARD_EXTRACTION_NODES = 4

#: The COMPLETE allowlist of card-extraction functions (sweep-ledger
#: rows 1, 2, 4, 7): ``<repo-relative path>::<function name>``.
ALLOWLIST = {
    "tui/screens/selection.py::build_wizard",
    "tui/screens/selection.py::_open_detail",
    "tui/screens/selection.py::_manual_landing_path",
    "tui/services/selection.py::model_presence",
}

#: The owner reported for module-level extraction nodes (none exist at
#: HEAD; a module-level read would be outside every function's guard).
_MODULE_OWNER = "<module>"


def _is_card_extraction(node: ast.AST) -> bool:
    """True for a card EXTRACTION node — an ``X["card"]`` subscript or
    an ``X.get("card")`` call.

    Param-typed reads (``card.get("type")`` — the first argument is not
    the constant ``"card"``) and attribute reads (``self._card``) are
    deliberately OUT of the pattern: they never pull the field off an
    entry, and their guards are the ledger's by-construction rows.
    """
    if isinstance(node, ast.Subscript):
        return (isinstance(node.slice, ast.Constant)
                and node.slice.value == "card")
    if isinstance(node, ast.Call):
        func = node.func
        return (isinstance(func, ast.Attribute)
                and func.attr == "get"
                and bool(node.args)
                and isinstance(node.args[0], ast.Constant)
                and node.args[0].value == "card")
    return False


def _scan_tree(node: ast.AST, owner: str, path: Path,
               sites: list[tuple[Path, str, int]]) -> None:
    """Recursive walk mapping every extraction node to its NEAREST
    enclosing (Async)FunctionDef — a nested function owns its reads."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        owner = node.name
    if _is_card_extraction(node):
        # every extraction node is an expression (Subscript/Call), so
        # the stmt|expr narrowing gives ty the lineno attribute
        assert isinstance(node, ast.expr), (
            "card-extraction nodes are expressions by construction")
        sites.append((path, owner, node.lineno))
    for child in ast.iter_child_nodes(node):
        _scan_tree(child, owner, path, sites)


def scan_card_extraction_sites(paths) -> "list[tuple[Path, str, int]]":
    """(path, function, lineno) for every card-extraction node in the
    given modules — the importable detector the positive control drives.

    Args:
        paths: iterable of ``.py`` paths (the ``tui/`` tree or a temp
            control module).

    Returns:
        list[tuple[Path, str, int]]: one row per extraction node, each
        named for its nearest enclosing function (``<module>`` at module
        level).
    """
    sites: list[tuple[Path, str, int]] = []
    for raw_path in paths:
        path = Path(raw_path)
        tree = ast.parse(
            path.read_text(encoding="utf-8"), filename=str(path))
        _scan_tree(tree, _MODULE_OWNER, path, sites)
    return sites


def _has_dict_isinstance(func: ast.AST) -> bool:
    """True when the function contains an ``isinstance(<x>, dict)`` call
    — the 08-08/08-09 guard idiom's presence check."""
    for node in ast.walk(func):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "isinstance"
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Name)
                and node.args[1].id == "dict"):
            return True
    return False


def _find_function(tree: ast.AST,
                   name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """The first (Async)FunctionDef with the given name, else None."""
    for node in ast.walk(tree):
        if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == name):
            return node
    return None


def _rel(path: Path) -> str:
    """The repo-relative path string (the raw path outside the repo)."""
    try:
        return str(path.relative_to(TUI_ROOT.parent))
    except ValueError:
        return str(path)


def card_site_violations(paths) -> list[str]:
    """The offender messages for the given modules — every failure names
    file:line (or the allowlisted function's def line for a guard
    removal).

    Args:
        paths: iterable of ``.py`` paths.

    Returns:
        list[str]: empty when every extraction site is allowlisted and
        every allowlisted function still carries its dict guard.
    """
    messages: list[str] = []
    for path, owner, lineno in scan_card_extraction_sites(paths):
        identifier = f"{_rel(path)}::{owner}"
        if identifier not in ALLOWLIST:
            messages.append(
                f"{_rel(path)}:{lineno} {owner} — card extraction "
                "outside the allowlist (give it an isinstance(card, "
                "dict) guard, a ledger row, and a conscious ALLOWLIST "
                "decision)")
    for identifier in sorted(ALLOWLIST):
        rel, _, func_name = identifier.partition("::")
        path = TUI_ROOT.parent / rel
        tree = ast.parse(
            path.read_text(encoding="utf-8"), filename=rel)
        func = _find_function(tree, func_name)
        if func is None:
            messages.append(
                f"{rel} — allowlisted {func_name} no longer exists")
            continue
        if not _has_dict_isinstance(func):
            messages.append(
                f"{rel}:{func.lineno} {func_name} — allowlisted but its "
                "isinstance(card, dict) guard is gone")
    return messages


def test_every_card_extraction_site_is_guarded():
    """Every card extraction site in ``tui/`` lives in the four-function
    allowlisted, each function still carrying its isinstance guard —
    the crash family cannot regrow (08-09 Task 2, the structural floor
    over the sweep ledger)."""
    paths = sorted(TUI_ROOT.rglob("*.py"))
    sites = scan_card_extraction_sites(paths)
    assert len(sites) >= MIN_CARD_EXTRACTION_NODES, (
        f"the scan found only {len(sites)} card-extraction nodes in "
        f"tui/ (floor {MIN_CARD_EXTRACTION_NODES}) — a parsing "
        "regression would pass this pin vacuously; investigate the "
        "extraction-detection pattern"
    )
    violations = card_site_violations(paths)
    assert not violations, (
        "every card extraction site in tui/ must live in the guarded "
        "allowlist (the family-closure invariant, 08-09) — offending "
        "sites:\n  " + "\n  ".join(violations)
    )


def test_scanner_flags_unguarded_extraction_positive_control(tmp_path):
    """The positive control: the detector itself detects unguarded
    extraction, so the green tree-assertion above cannot pass vacuously
    through a broken pattern — the scanner finds the temp module's one
    extraction node (function + line), and the violation logic flags it
    naming file:line."""
    module = tmp_path / "positive_control.py"
    module.write_text(
        "def plain(entry):\n"
        '    return entry["card"].get("x")\n',
        encoding="utf-8",
    )

    assert scan_card_extraction_sites([module]) == [
        (module, "plain", 2)], (
        "the detector must find the unguarded extraction node"
    )
    flagged = card_site_violations([module])
    assert any(
        f"{module}:2 plain" in message for message in flagged), (
        f"the positive control must be flagged naming file:line, got: "
        f"{flagged}"
    )
