# =====================================================================
# conftest.py — pytest bootstrap for the DNALLM-Mark test harness
#
# Runs BEFORE any test module is imported (pytest loads conftest first),
# which is what makes the two jobs below order-safe:
#   1. Thread pinning (TEST-02): numpy reductions stay single-threaded
#      and reproducible — pins must land before any test-module numpy
#      import, so they live in top-level code, not a fixture.
#   2. Import roots: `script/`, `baseline/`, and `pipeline/` are not packages;
#      inserting them on sys.path makes `summarize_comparison`,
#      `get_task_performance`, `compare`, and `run_sweep` importable from
#      every test module.
# =====================================================================

import os
import sys
from pathlib import Path

# ===== Thread pinning (TEST-02) =====
# FORCE-assign, not setdefault (WR-05): conftest runs before any test-module
# numpy import, so the assignment is effective for this process AND for
# every subprocess the suite spawns (the determinism lane inherits it).
# setdefault let a preset hostile value (e.g. an HPC module exporting
# OMP_NUM_THREADS=4) silently skip the pin and turn
# test_thread_pinning_is_active_at_test_time red with a bare AssertionError.
# Overriding the caller's environment is safe here: the pins only affect
# this test process's BLAS/OpenMP pools, and single-threaded reductions are
# the point of TEST-02 — an env-pinned nonzero count is not accepted.
for _var in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ[_var] = "1"  # pin: stable reductions, no oversubscription

# ===== Import roots =====
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "script"))   # summarize_comparison, get_task_performance
sys.path.insert(0, str(REPO_ROOT / "baseline")) # compare (walk) for reuse
sys.path.insert(0, str(REPO_ROOT / "pipeline")) # run_sweep (stdlib-only sweep driver)
