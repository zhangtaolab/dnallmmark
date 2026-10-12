"""
__main__.py — the ``python -m tui`` entry point (Phase 8, 08-02).

The console's only launch path (``make tui`` →
``uv run --group tui --group gpu python -m tui``). Runs the sys.path
bootstrap BEFORE importing ``tui.app`` or anything that touches a pipeline
seam.

Contract:

- REPO_ROOT is derived from ``__file__`` — NEVER from the CWD. The make
  recipe may be invoked from any directory; a CWD-relative bootstrap would
  import the wrong tree or none at all. (This mirrors the load-bearing
  ``tests/conftest.py`` sys.path idiom.)
- ``pipeline/`` is a sys.path root, not a package (no ``__init__.py``): the
  services layer imports ``env_smoke`` / ``registry_loader`` /
  ``artifact_loader`` as top-level modules (dependency direction tui →
  pipeline, D-02/D-19), so ``REPO_ROOT/pipeline`` must be on sys.path before
  those imports happen.
- The repo root itself is inserted first so package-qualified imports
  (``tui.app``) resolve regardless of how ``__main__`` was reached.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Each insert lands at sys.path[0], so pipeline/ ends up first — both roots
# are repo-local directories; no shadowing risk.
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "pipeline"))

# Imported after the bootstrap on purpose (ruff's default rule set does not
# flag placement here): tui.app — and, through the services it will wire, the
# pipeline seams — requires the sys.path inserts above to have run first.
from tui.app import DnallmMarkTui


def main() -> int:
    """Run the DNALLM-Mark console (display runtime; blocks until quit).

    Schedules ``boot_resume_queue`` BEFORE ``run`` (the D-06 boot path):
    a restart with persisted pending work resumes the download queue
    automatically. This ``call_later`` is the ONLY auto-start path in
    the codebase — ``App.on_mount`` never kicks, so test-constructed
    apps stay inert (10-04, T-10-04-03).

    Returns:
        Process exit code — 0 on a clean quit.
    """
    app = DnallmMarkTui()
    app.call_later(app.boot_resume_queue)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
