"""
Golden-file tests over the synthetic fixture chain (D-09, TEST-03 synthetic half).

Runs the re-scoped chain (04-05 pivot retirement) —
``summarize_comparison.main()`` under ``chdir`` into a tmp copy of
``tests/fixtures/synthetic_models/`` (with the synthetic registry slice
injected), plus the JS index generator over the COMMITTED
``tests/fixtures/synthetic_task_performance/`` fixture tree via the
copy-into-fixture-tree trick — and value-compares every regenerated file
against the committed goldens in ``tests/fixtures/golden/`` using
``baseline/compare.py``'s ``walk()``: the canonical D-06 diff vocabulary,
reused rather than re-implemented (Don't Hand-Roll rule).

The synthetic_task_performance fixture IS the retired pivot's own final
output: chain-produced once by ``script/get_task_performance.py``
(deterministic by FIX-05) immediately before its deletion and committed as a
fixture input. The goldens themselves are untouched by the retirement — they
were chain-produced when the full chain (pivot included) created this suite,
and the fixture bytes are identical to what the pivot produced, so the
re-scoped chain regenerates the same values. Until E2' regenerates them via
``script/export_runs.py``, committed task_performance data is static.

Comparison is by VALUE, never by bytes: on the same machine zero diffs of ANY
class are expected — including ``FLOAT_ULP`` — so the assertion is
``diffs == []``. Cross-machine float noise is explicitly not claimed
(PIN-VALIDATION scope); byte-identical assertions are reserved for the
02-03 same-machine determinism run.

Goldens are chain-produced, never hand-authored: they were byte-copied from
an identical chain run when this suite was created (see SUMMARY). If
regeneration ever disagrees beyond the vocabulary, the disagreement is
investigated — goldens are never hand-edited to match chain output.

See also:
    - ``tests/test_aggregation.py`` — the aggregation pure functions.
    - ``tests/test_export_runs.py`` — the pivot-shape owner (folded coverage).
    - ``tests/js/generate-tasks-index.test.js`` — the JS unit lane.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import summarize_comparison
from compare import walk

# WR-06: all three tests below consume ``chain_result``, whose JS-generator
# step shells out to ``node`` — on a node-less machine the module must SKIP
# cleanly, not die on a raw FileNotFoundError inside the fixture. This is
# what makes the pytest-only fast lane (``make test-fast``) genuinely
# node-free.
pytestmark = pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node >=18 required for the JS generator step of this test",
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_DIR = REPO_ROOT / "tests" / "fixtures" / "synthetic_models"
SYNTHETIC_TASKS_DIR = REPO_ROOT / "tests" / "fixtures" / "synthetic_task_performance"
GOLDEN_DIR = REPO_ROOT / "tests" / "fixtures" / "golden"
GENERATOR = REPO_ROOT / "scripts" / "generate-tasks-index.js"

# Synthetic registry slice (FIX-02): summarize_comparison groups datasets by
# the datasets_info.json Category join with a hard fail on unregistered
# names. The FakeDS dataset names do not exist in the real registry (and
# MUST hard-fail against it), so the synthetic chain runs against this slice
# whose Category values equal the per-dataset species values already carried
# in the synthetic model fixtures — keeping the goldens byte-identical under
# the grouping-source switch (semantics-preserving on the synthetic tree).
SYNTHETIC_REGISTRY = REPO_ROOT / "tests" / "fixtures" / "synthetic_datasets_info.json"

# One comparison file per synthetic species group + the all-tasks file — the
# synthetic tree yields exactly one dataset per species (D-09 engineering).
COMPARISON_FILES = (
    "models_comparison.json",
    "models_comparison_animal.json",
    "models_comparison_plant.json",
    "models_comparison_microbe.json",
)
TASKS_INDEX = "tasks.json"


def _run_synthetic_chain(tmp_path, monkeypatch):
    """Run the re-scoped synthetic chain inside ``tmp_path``.

    Inputs: the synthetic model_performance tree (copied) and the committed
    synthetic_task_performance fixture (copied as the JS generator's task
    tree — the retired pivot's final output is a fixture input now, not a
    chain step). Steps: ``summarize_comparison.main()`` with the synthetic
    registry slice injected, then the JS index generator via the copy trick.

    Args:
        tmp_path: pytest tmp dir (becomes the chain's CWD).
        monkeypatch: pytest monkeypatch (drives the chdir).

    Returns:
        Tuple ``(work, js_data)`` — the chain CWD (holding the regenerated
        comparison files) and the JS fixture-tree data dir (holding the
        regenerated ``tasks.json``).
    """
    staged = tmp_path / "model_performance"
    staged.mkdir()
    for fixture in sorted(SYNTHETIC_DIR.glob("*_performance.json")):
        shutil.copy(fixture, staged / fixture.name)

    # JS copy trick (research Pattern 4): the generator resolves
    # __dirname-relative paths and executes at import, so run a COPY placed
    # inside <tmp>/inner/ next to a <tmp>/dnallm-mark/data/task_performance/
    # fixture tree — never the repo tree.
    inner = tmp_path / "inner"
    inner.mkdir()
    js_data = tmp_path / "dnallm-mark" / "data"
    (js_data / "task_performance").mkdir(parents=True)
    for task_file in sorted(SYNTHETIC_TASKS_DIR.glob("*.json")):
        shutil.copy(task_file, js_data / "task_performance" / task_file.name)

    monkeypatch.chdir(tmp_path)
    # FIX-02: the grouping join reads summarize_comparison.REGISTRY_PATH —
    # inject the synthetic slice so the FakeDS names resolve (against the
    # real registry they would hard-fail by design).
    monkeypatch.setattr(summarize_comparison, "REGISTRY_PATH", SYNTHETIC_REGISTRY)
    summarize_comparison.main()

    shutil.copy(GENERATOR, inner / "gen.js")
    subprocess.run(["node", str(inner / "gen.js")], check=True, capture_output=True)
    return tmp_path, js_data


def _assert_no_diffs(name, golden_path, regen_path):
    """Value-compare a regenerated file against its golden via ``walk()``.

    Args:
        name: File name (for the failure message).
        golden_path: Committed golden file (the reference).
        regen_path: Regenerated counterpart.
    """
    diffs = []
    walk(
        json.loads(golden_path.read_text(encoding="utf-8")),
        json.loads(regen_path.read_text(encoding="utf-8")),
        "",
        diffs,
    )
    assert diffs == [], f"{name}: {len(diffs)} diff(s) vs golden: {diffs[:8]}"


@pytest.fixture
def chain_result(tmp_path, monkeypatch):
    """The regenerated synthetic chain outputs (work dir + JS data dir)."""
    return _run_synthetic_chain(tmp_path, monkeypatch)


def test_synthetic_comparison_files_match_goldens(chain_result):
    """All four regenerated comparison files are value-identical to the
    committed goldens — zero diffs of any class, FLOAT_ULP included."""
    work, _ = chain_result
    for name in COMPARISON_FILES:
        regen = work / name
        assert regen.exists(), f"chain did not produce {name}"
        _assert_no_diffs(name, GOLDEN_DIR / name, regen)


def test_tasks_index_matches_golden(chain_result):
    """The JS-generated tasks.json matches its golden via the same vocabulary
    (one golden-generation flow: produced by the same copy trick over the
    committed synthetic_task_performance fixture)."""
    _, js_data = chain_result
    regen = js_data / TASKS_INDEX
    assert regen.exists(), "JS generator did not produce tasks.json"
    _assert_no_diffs(TASKS_INDEX, GOLDEN_DIR / TASKS_INDEX, regen)


def test_golden_file_set_is_exact(chain_result):
    """The comparison covers the file set exactly: the chain produces exactly
    the four comparison files (one per species group + overall), and the
    golden directory holds exactly those four plus tasks.json — nothing
    untested, nothing missing."""
    work, _ = chain_result
    produced = {p.name for p in work.glob("models_comparison*.json")}
    assert produced == set(COMPARISON_FILES)

    golden_entries = {p.name for p in GOLDEN_DIR.iterdir() if p.is_file()}
    assert golden_entries == set(COMPARISON_FILES) | {TASKS_INDEX}
