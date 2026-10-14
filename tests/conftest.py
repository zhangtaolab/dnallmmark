# =====================================================================
# conftest.py — pytest bootstrap for the DNALLM-Mark test harness
#
# Runs BEFORE any test module is imported (pytest loads conftest first),
# which is what makes the two jobs below order-safe:
#   1. Thread pinning (TEST-02): numpy reductions stay single-threaded
#      and reproducible — pins must land before any test-module numpy
#      import, so they live in top-level code, not a fixture.
#   2. Import roots: `script/`, `baseline/`, and `pipeline/` are not packages;
#      inserting them on sys.path makes `summarize_comparison`, `compare`,
#      `run_sweep`, `export_runs`, and `freeze_snapshot` (04-02: vendored
#      statistics + exporter core + snapshot primitive) importable from every
#      test module. (get_task_performance is gone — deleted at 04-05 when the
#      pivot's input side retired; export_runs owns the task-file shape.)
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
sys.path.insert(0, str(REPO_ROOT / "script"))   # summarize_comparison, export_runs, freeze_snapshot
sys.path.insert(0, str(REPO_ROOT / "baseline")) # compare (walk) for reuse
sys.path.insert(0, str(REPO_ROOT / "pipeline")) # run_sweep (stdlib-only sweep driver)


# ===== Startup-config machine-independence pin (261014-f4w, F4W-01) =====
#
# run_sweep.main and run_finetune's module top now read the REAL XDG
# config root for directories.json at startup (the F4W startup config),
# so without a pin every existing sweep/env-check/run-config test would
# thread whatever directories.json happens to exist on the maintainer's
# machine into the run under test — the exact hazard the custom-overlay
# pin above guards for DNALLMMARK_CUSTOM_REGISTRY_DIR. Pin the whole
# config dir to a per-test tmp path (empty value = unset; empty dir =
# the byte-identity-when-absent case). A test-body monkeypatch.setenv
# later in the chain overrides the pin (tests of the file behavior
# itself re-pin at their own tmp); resolution-order tests delenv it.
# Autouse at the ROOT conftest: the fixture applies to the whole tests/
# tree, tests/tui/ included (conftest chains).

import pytest


@pytest.fixture(autouse=True)
def _pin_directories_config_root(tmp_path_factory, monkeypatch):
    """Empty-dir pin over the F4W startup-config root for every test.

    tmp_path_FACTORY (never the per-test tmp_path): several existing
    tests assert the EXACT contents of their tmp_path (the
    atomic-write no-residue and never-persists lanes), so the pin
    directory must not live inside it."""
    pinned = tmp_path_factory.mktemp("no-directories-config")
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(pinned))
