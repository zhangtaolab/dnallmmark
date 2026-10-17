"""
The ``@work`` never-exit structural pin (Phase 8, 08-08, gap missing-item 3).

Why this pin is load-bearing:

textual 8.2.8's ``work()`` decorator defaults to ``exit_on_error=True``
— a worker whose body raises escapes into ``App._handle_exception``,
which "Always results in the app exiting" (verified from the installed
package during the 08 verification). The CR-01 crash chains reproduced
exactly that: a hand-edited registry input raised through a ``@work``
read worker and took the WHOLE console down. The never-exit floor is
therefore STRUCTURAL: every ``@work`` site in ``tui/`` must either

- pass ``exit_on_error=False`` in its decorator call (textual then logs
  the worker error while the console stays alive — the residual net), OR
- own an internal broad guard (a ``try`` whose handler catches
  ``Exception``/``BaseException`` or is bare) that renders the degraded
  state itself — the monitor/run_config last-known-good and
  GateWorkerError patterns.

This test AST-parses every ``tui/**/*.py`` module, collects every
function whose decorator list contains a call to textual's ``work``
decorator, and enforces that dichotomy for every site — present and
future. The per-site ledger in 08-08-PLAN.md documents the 24 HEAD
sites' classification; this pin supersedes the ledger going forward
(any site it flags gets the kwarg, no snapshot trusting).

Non-vacuity floor: the scan must find at least 20 sites, so a parsing
regression (e.g. a decorator-form change that hides every site) cannot
pass the test silently on an empty collection.

Scope note: SPECIFIC exception handlers (``except (OSError,
json.JSONDecodeError)``) do NOT satisfy the floor — a specific tuple
lets any other exception type escape. Only Exception/BaseException/bare
handlers qualify (implement as specced — deliberately not widened).
"""

import ast
from pathlib import Path

TUI_ROOT = Path(__file__).resolve().parents[2] / "tui"

#: The non-vacuity floor (24 ``@work`` sites at 08-08 HEAD; the count
#: only ever grows in this milestone).
MIN_WORK_SITES = 20

_BROAD_HANDLER_NAMES = {"Exception", "BaseException"}


def _is_work_call(node: ast.AST) -> bool:
    """True when ``node`` is a call to textual's ``work`` decorator.

    Covers both spellings — the bare ``@work(...)`` name this codebase
    uses (``from textual import work``) and a future qualified
    ``textual.work(...)`` attribute form.
    """
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == "work"
    if isinstance(func, ast.Attribute):
        return func.attr == "work"
    return False


def _passes_exit_on_error_false(call: ast.Call) -> bool:
    """True when the decorator call carries ``exit_on_error=False``."""
    return any(
        keyword.arg == "exit_on_error"
        and isinstance(keyword.value, ast.Constant)
        and keyword.value.value is False
        for keyword in call.keywords
    )


def _is_broad_handler(handler: ast.ExceptHandler) -> bool:
    """True for ``except Exception``/``BaseException``/bare handlers.

    Specific exception types or tuples (``except OSError``, ``except
    (OSError, json.JSONDecodeError)``) do NOT qualify — anything outside
    the named types still escapes the worker.
    """
    if handler.type is None:
        return True  # bare ``except:`` — catches everything
    names: list[str] = []
    if isinstance(handler.type, ast.Name):
        names = [handler.type.id]
    elif isinstance(handler.type, ast.Tuple):
        names = [
            element.id for element in handler.type.elts
            if isinstance(element, ast.Name)
        ]
    return any(name in _BROAD_HANDLER_NAMES for name in names)


def _has_internal_broad_guard(func: ast.AST) -> bool:
    """True when the worker body owns a broad ``except`` somewhere."""
    return any(
        isinstance(node, ast.Try)
        and any(_is_broad_handler(handler) for handler in node.handlers)
        for node in ast.walk(func)
    )


def _scan_work_sites():
    """Every ``@work`` site in ``tui/``: (path, decorator line, name).

    One ledger row per function: the first ``work`` call in the
    decorator list identifies the site (no function here stacks two
    ``work`` decorators).
    """
    sites = []
    for path in sorted(TUI_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if _is_work_call(decorator):
                    sites.append((path, decorator.lineno, node.name, node))
                    break
    return sites


def test_every_work_site_never_exits_the_console():
    """Every ``@work`` site in ``tui/`` carries ``exit_on_error=False``
    or an internal broad guard — no worker exception can exit the
    console through textual 8.2.8's default ``exit_on_error=True``."""
    sites = _scan_work_sites()
    assert len(sites) >= MIN_WORK_SITES, (
        f"the scan found only {len(sites)} @work sites in tui/ "
        f"(floor {MIN_WORK_SITES}) — a parsing regression would pass "
        "this pin vacuously; investigate the decorator-form detection"
    )

    offenders = []
    for path, lineno, name, func in sites:
        work_call = next(
            decorator for decorator in func.decorator_list
            if _is_work_call(decorator)
        )
        if _passes_exit_on_error_false(work_call):
            continue
        if _has_internal_broad_guard(func):
            continue
        offenders.append(
            f"{path.relative_to(TUI_ROOT.parent)}:{lineno} {name}")
    assert not offenders, (
        "every @work site must pass exit_on_error=False or own an "
        "internal except-Exception handler (the never-exit floor, "
        "08-08 gap missing-item 3) — offending sites:\n  "
        + "\n  ".join(offenders)
    )
