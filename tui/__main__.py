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
- 261015-ehc (EHC-1): this module owns the ONLY persisted-language boot
  load — ``load_persisted_language`` reads ``language.json`` under the XDG
  state root tolerantly (missing/corrupt/wrong-value → DEFAULT_LANGUAGE,
  never raises, never blocks boot) and ``main`` applies it (plus the
  binding-description remap — class BINDINGS freeze at import in the
  import-time language) BEFORE ``app.run``. Test-constructed apps never
  read the file (the boot_resume_queue inertness precedent).
"""

import json
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
from tui import strings as S
from tui.app import DnallmMarkTui, remap_binding_descriptions
from tui.services import settings

#: The persisted language file under the XDG state root (EHC-1).
LANGUAGE_FILE_NAME = "language.json"


def load_persisted_language() -> str:
    """Tolerantly load the persisted UI language (the ONLY boot read).

    Resolution: a readable ``language.json`` carrying a ``language`` value
    in ``LANGUAGES`` wins; anything else (missing file, unreadable,
    non-JSON, wrong shape, unknown value) resolves to ``DEFAULT_LANGUAGE``
    — never raises, never blocks boot (T-ehc-02).

    Returns:
        str: the boot language.
    """
    try:
        doc = json.loads(
            (settings.state_dir() / LANGUAGE_FILE_NAME).read_text(
                encoding="utf-8"))
        language = doc.get("language") if isinstance(doc, dict) else None
    except (OSError, ValueError):
        return S.DEFAULT_LANGUAGE
    if language in S.LANGUAGES:
        return language
    return S.DEFAULT_LANGUAGE


def main() -> int:
    """Run the DNALLM-Mark console (display runtime; blocks until quit).

    Applies the persisted language BEFORE ``run`` (the EHC-1 boot load —
    the only place the language file is read; the remap follows because
    class BINDINGS descriptions froze at import), then schedules
    ``boot_resume_queue`` BEFORE ``run`` (the D-06 boot path): a restart
    with persisted pending work resumes the download queue automatically.
    These ``call_later`` hooks are the ONLY auto-start paths in the
    codebase — ``App.on_mount`` never kicks, so test-constructed apps
    stay inert (10-04, T-10-04-03).

    Returns:
        Process exit code — 0 on a clean quit.
    """
    language = load_persisted_language()
    if language != S.language():
        S.set_language(language)
        remap_binding_descriptions(S.DEFAULT_LANGUAGE, language)
    app = DnallmMarkTui()
    app.call_later(app.boot_resume_queue)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
