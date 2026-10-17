"""
The services-textual-free import lock (Phase 8, 08-03).

Locks the foundation invariant declared in ``tui/services/__init__.py``:
NO module under ``tui/services/`` imports ``textual`` — top-level or
nested, directly. Presentation belongs to screens; services stay pure
orchestration + I/O so every CPU lane (dev/CI) can import them without
a display (binding constraint 2; D-03 keeps kernel execution on
screen-owned thread workers).

Phase 7 absence-lock discipline (absence = the lock): each services
source file is parsed with ``ast`` and walked node-by-node, so an
import hidden inside a function or class body fails the lock exactly as
hard as a top-level one. Non-vacuous by assertion: the glob must find
at least one file — the lock means nothing over an empty directory
(``registries.py``, landed by this same plan, is the first resident).

See also:
    ``tui/services/__init__.py`` — the contract this test locks.
"""

import ast
from pathlib import Path

SERVICES_DIR = Path(__file__).resolve().parents[2] / "tui" / "services"


def _textual_imports(path):
    """Yield a description of every textual import in ``path`` (if any)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == "textual":
                    yield f"line {node.lineno}: import {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            # node.module is None for relative imports (`from . import x`)
            # — those can never reach the external textual package.
            module = node.module or ""
            if module.split(".")[0] == "textual":
                yield f"line {node.lineno}: from {module} import ..."


def test_services_layer_imports_zero_textual():
    """Every ``tui/services/*.py`` carries zero textual imports (any depth)."""
    files = sorted(SERVICES_DIR.glob("*.py"))
    assert files, (
        "vacuous lock: no tui/services/*.py files found — the lock means "
        "nothing over an empty directory"
    )
    for path in files:
        offenders = list(_textual_imports(path))
        assert not offenders, (
            f"{path.name} violates the services-textual-free contract: "
            + "; ".join(offenders)
        )
