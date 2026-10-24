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

# ===== zh language pin (261015-ehc, EHC-1) =====
# tui/strings.py defaults to ENGLISH (the committed default); this pin
# flips the registry to zh BEFORE any test module imports it, so the
# test-side ``from tui.strings import X`` copies freeze zh and match the
# zh-rendering apps the committed Pilot assertions pin (conftest runs
# before test-module imports by construction). Default-English coverage
# lives as dedicated Pilot tests (tests/tui/test_pilot_boot.py).
from tui import strings

strings.set_language("zh")
