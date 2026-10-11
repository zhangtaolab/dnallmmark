# =====================================================================
# conftest.py — pytest bootstrap for the tui/ test lane (Phase 8, 08-02)
#
# The parent tests/conftest.py already provides the pipeline-side import
# roots (script/, baseline/, pipeline/ — its contract at :40-44) and the
# TEST-02 thread pinning; it runs for tests/tui/ too (pytest loads every
# conftest from the rootdir down). This conftest adds the ONE root the
# parent does not: the repo root itself.
#
# Why: tui is imported package-qualified (`import tui`,
# `from tui.app import DnallmMarkTui`) and plain pytest does NOT put the
# repo root on sys.path (no src/ layout, tests/ carries no __init__.py —
# 08-RESEARCH Pitfall 4); without this insert, tier-1/tier-2 tests raise
# ModuleNotFoundError under plain pytest exactly where CI runs them.
# =====================================================================

import sys
from pathlib import Path

# ===== Import root =====
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))  # tui (package-qualified imports; pipeline/ comes from the parent conftest)
