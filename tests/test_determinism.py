"""
Real-tree determinism regression over the committed data chain (D-10, TEST-03
real half) — RE-SCOPED at 04-05 (pivot retirement, SC-2/OQ6).

The data-regeneration chain is now ``script/summarize_comparison.py`` + the
JS index generator ONLY: ``script/get_task_performance.py`` is deleted, and
the 47 committed ``task_performance/`` files are static committed data until
E2' regenerates them via ``script/export_runs.py`` — they are INPUTS this
test copies, never outputs it regenerates, and nothing in the repo can
overwrite them (T-04-11). The Makefile ``data`` target documents the same
scope.

Runs the re-scoped chain as subprocesses with ``cwd=tmp`` over a
``shutil.copytree`` copy of the 42 real committed model_performance inputs
PLUS the 47 committed task_performance inputs (the JS generator's source
tree), plus the JS index generator via the copy-into-fixture-tree trick —
TWICE inside one pytest tmp tree, then asserts three things:

1. the two runs' outputs are byte-identical (run 1 == run 2), and
2. every regenerated output (4 ``models_comparison*`` files +
   ``tasks.json``) is byte-identical to its committed counterpart under
   ``dnallm-mark/data/`` — including tasks.json, which pins the committed
   index to the committed task files, and
3. the committed tree itself is untouched (``git status --porcelain`` over
   ``dnallm-mark/data/`` is empty) — the published numbers are read-only to
   the suite, and an interrupted run cannot have modified them either.

Scope (Pitfall 5 / PIN-VALIDATION): byte equality is claimed SAME-MACHINE
only — cross-arch float sums (``sum_zscore`` ULP noise) are explicitly not
claimed. Concurrency edge: interrupted or parallel chain runs guarantee
nothing; this regression runs serially in an isolated tmp tree and writes
only under it.

Wall time: two chain runs — measured ~0.3s per run on the dev machine
(2026-10-09, warm page cache); D-10's ``~40s per chain run`` figure was a
conservative planning estimate that was never re-timed, and this suite runs
far faster than it. The lane stays ``slow``-marked regardless (research
A5/A6): the real-tree run is qualitatively heavier than the unit lane, and
``make test-fast`` keeps it out of the inner loop by marker, not by
measured cost. ``make test`` and plain ``pytest`` include it.

See also:
    - ``tests/test_golden.py`` — the synthetic-tree (fast) counterpart.
    - ``baseline/PIN-VALIDATION.md`` — the same-machine byte-determinism
      evidence this test automates, and the D-06 diff vocabulary.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "dnallm-mark" / "data"
SUMMARY_SCRIPT = REPO_ROOT / "script" / "summarize_comparison.py"
GENERATOR = REPO_ROOT / "scripts" / "generate-tasks-index.js"

# JS copy-trick layout (research Pattern 4): the generator resolves
# TASK_PERFORMANCE_DIR/OUTPUT_FILE relative to __dirname and executes at
# module load, so it must run as a COPY inside the tmp tree — running the
# repo script directly would read and write the REAL dnallm-mark/data/ tree.
JS_INNER_DIR = "inner"
JS_DATA_RELPATH = "dnallm-mark/data"
JS_INDEX_RELPATH = "dnallm-mark/data/tasks.json"


def _run_checked(cmd, cwd):
    """Run one chain step, raising with captured output on failure.

    Args:
        cmd: Command argv (list of str/Path) — ``sys.executable`` resolves to
            the venv python under ``uv run`` (research A4), and the child
            inherits this process's environment, including the conftest
            thread pinning.
        cwd: Working dir for the step (the tmp chain root).
    """
    proc = subprocess.run(
        [str(c) for c in cmd],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,  # failure handled below with the captured output
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"chain step failed with exit {proc.returncode}: "
            f"{' '.join(str(c) for c in cmd)}\n"
            f"--- stdout tail ---\n{proc.stdout[-1500:]}\n"
            f"--- stderr tail ---\n{proc.stderr[-1500:]}"
        )


def _snapshot_outputs(work):
    """Collect the chain's regenerated JSON outputs under ``work``.

    Outputs are exactly the ``models_comparison*.json`` files (written to
    the work root by summarize) plus the generated ``tasks.json`` (the JS
    copy-trick layout). The copied inputs — ``model_performance/`` and the
    JS-visible ``task_performance/`` copy — are excluded: task files are
    static committed data until E2', inputs the test copies, not outputs it
    regenerates. Keys are POSIX relative paths so run-1 vs run-2 and
    regenerated vs committed comparisons address files by stable names.

    Args:
        work: The tmp chain root.

    Returns:
        Dict ``{relative_posix_path: bytes}`` over the chain outputs.
    """
    snapshot = {
        p.relative_to(work).as_posix(): p.read_bytes()
        for p in sorted(work.glob("models_comparison*.json"))
    }
    snapshot[JS_INDEX_RELPATH] = (work / JS_INDEX_RELPATH).read_bytes()
    return snapshot


def _run_chain_once(work):
    """Run the re-scoped chain once inside ``work``, leaving only run outputs.

    Every chain output is REMOVED first (WR-04): the
    ``models_comparison*.json`` files and the generated ``tasks.json``.
    Without this, a run-2 file-set shrink (an output silently not written)
    is masked — run 1's leftover copy of that file would enter snapshot 2
    with run-1 bytes and every comparison would pass vacuously. With the
    cleanup, each run must write its FULL output set from scratch. The
    copied inputs (``model_performance/``, the JS-visible
    ``task_performance/`` tree) are never touched.

    Args:
        work: The tmp chain root (holds the copied inputs and the JS
            copy-trick layout).

    Returns:
        Dict ``{relative_posix_path: bytes}`` of all regenerated outputs.
    """
    for stale in work.glob("models_comparison*.json"):
        stale.unlink()
    (work / JS_INDEX_RELPATH).unlink(missing_ok=True)

    # summarize resolves inputs/outputs against CWD at call time (paths are
    # locals inside main()) — running it with cwd=work keeps every write
    # inside the tmp tree. The JS generator is __dirname-relative and reads
    # the copied task tree the same way.
    _run_checked([sys.executable, SUMMARY_SCRIPT], cwd=work)
    _run_checked(["node", work / JS_INNER_DIR / "gen.js"], cwd=work)

    return _snapshot_outputs(work)


@pytest.mark.slow
def test_chain_is_deterministic_and_matches_committed(tmp_path_factory):
    """Two runs of the re-scoped chain (summarize + JS generator) over the
    real copied inputs are byte-identical to each other AND reproduce the
    committed derived files; the committed tree is never written to."""
    work = tmp_path_factory.mktemp("det")

    # Real committed inputs, copied read-only-into-tmp: the chain runs
    # against the copy, never the published tree. task_performance/ is an
    # INPUT (static committed data until E2' — nothing regenerates it), so
    # it is copied once as the JS generator's source tree.
    shutil.copytree(DATA_DIR / "model_performance", work / "model_performance")
    (work / JS_INNER_DIR).mkdir()
    shutil.copy(GENERATOR, work / JS_INNER_DIR / "gen.js")
    shutil.copytree(
        DATA_DIR / "task_performance", work / JS_DATA_RELPATH / "task_performance"
    )

    snapshot1 = _run_chain_once(work)
    snapshot2 = _run_chain_once(work)

    # (1) run-to-run byte determinism (same machine — see module docstring).
    if snapshot1 != snapshot2:
        differing = sorted(
            name
            for name in set(snapshot1) | set(snapshot2)
            if snapshot1.get(name) != snapshot2.get(name)
        )
        pytest.fail(
            "chain is not byte-deterministic across runs "
            f"(first differing files: {differing[:10]})"
        )

    # (2) file-set exactness: the chain must produce exactly the four
    # committed comparison files plus the tasks index — nothing else.
    committed_comparison_names = {
        p.name for p in DATA_DIR.glob("models_comparison*.json")
    }
    regen_comparison_names = {
        name for name in snapshot1 if name != JS_INDEX_RELPATH
    }
    assert regen_comparison_names == committed_comparison_names, (
        "regenerated comparison file set differs from committed: "
        f"{sorted(regen_comparison_names)} vs "
        f"{sorted(committed_comparison_names)}"
    )
    assert set(snapshot1) == committed_comparison_names | {JS_INDEX_RELPATH}, (
        f"chain produced unexpected output files: {sorted(snapshot1)}"
    )

    # (2b) every regenerated output byte-identical to its committed
    # counterpart, with a per-file message naming the drifted file.
    # tasks.json drifting means the index no longer matches the committed
    # task files; a comparison file drifting means published numbers moved.
    for name in sorted(snapshot1):
        committed = (
            DATA_DIR / "tasks.json" if name == JS_INDEX_RELPATH else DATA_DIR / name
        )
        assert committed.exists(), (
            f"{name}: regenerated output has no committed counterpart "
            f"at {committed}"
        )
        assert committed.read_bytes() == snapshot1[name], (
            f"{name} drifted from committed tree ({committed}) — a "
            "generator edit or committed-data edit changed published numbers"
        )

    # (3) the committed tree is read-only to the suite: prove the test (and
    # the chain it spawned) left dnallm-mark/data/ untouched.
    porcelain = subprocess.run(
        ["git", "status", "--porcelain", "--", "dnallm-mark/data/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert porcelain.strip() == "", (
        f"test wrote into the committed data tree: {porcelain.strip()}"
    )
