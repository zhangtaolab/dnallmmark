# =====================================================================
# conftest.py — pytest bootstrap for the DNALLM-Mark test harness
#
# Runs BEFORE any test module is imported (pytest loads conftest first),
# which is what makes the two jobs below order-safe:
#   1. Thread pinning (TEST-02): numpy reductions stay single-threaded
#      and reproducible — pins must land before any test-module numpy
#      import, so they live in top-level code, not a fixture.
#   2. Import roots: `script/` and `baseline/` are not packages; inserting
#      them on sys.path makes `summarize_comparison`, `get_task_performance`,
#      and `compare` importable from every test module.
# =====================================================================

import os
import sys
from pathlib import Path

# ===== Thread pinning (TEST-02) =====
for _var in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ.setdefault(_var, "1")  # pin: stable reductions, no oversubscription

# ===== Import roots =====
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "script"))   # summarize_comparison, get_task_performance
sys.path.insert(0, str(REPO_ROOT / "baseline")) # compare (walk) for reuse
