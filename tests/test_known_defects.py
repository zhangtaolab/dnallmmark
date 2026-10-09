"""
Known-defect locks: the three confirmed data-chain defects as
``xfail(strict=True)`` tests (D-03/D-04/D-07).

House rule: a defect's fix lands ONLY together with the deliberate removal
of its marker in the same commit. Every marker below carries ``strict=True``
and the finding ID in its reason string — with strict semantics an
unexpected XPASS FAILS the suite (verified live on pytest 9.1.1 in the
Phase 2 research), so a Phase 4 fix that leaves its marker behind can never
pass silently, and a marker removed without the fix turns red immediately.

The three locks (defect semantics pinned test-first, fixed in Phase 4):

- **AUD-01-P0** — species-as-dataset: the producer's dataset-entry
  construction sources ``species`` from the MODEL row while every sibling
  field reads the DATASET row. Locked via an AST source-contract check —
  the pipeline module is never imported (``torch``/``dnallm`` at module
  level are unavailable CPU-side; an import would xfail for the wrong
  reason — a false lock).
- **WR-02** — ``baseline/compare.py`` treats an equal-value bool/int
  cross-type pair (``True`` vs ``1``) as identical: the canonical
  comparator stays silent exactly where the 47 pinned task files carry
  bf16/fp16 booleans. Locked by driving ``walk()`` directly.
- **WR-03** — ``summarize_comparison.get_float`` passes non-finite floats
  (``"nan"``/``"inf"``/``"-inf"``) through, so a NaN metric survives the
  presence gate and poisons a whole task's normalization. Locked by
  calling ``get_float`` directly (the same function whose green tests in
  ``tests/test_aggregation.py`` pin today's pass-through behavior).

Each body is minimal and independently exercised (false-lock guard): the
locks fail on their defect assertions, not on collection or import errors.

See also:
    - ``.planning/phases/01-audit-release-foundations/01-REVIEW-DISPOSITION.md``
      — the D-04/D-05 routing these locks implement.
    - ``tests/test_aggregation.py`` — the green ``get_float`` contract
      tests whose non-finite pass-through pins these locks build on.
"""

import ast
from pathlib import Path

import pytest
import summarize_comparison
from compare import walk

REPO_ROOT = Path(__file__).resolve().parents[1]
# Read as SOURCE TEXT, never imported: pipeline/dnallmmark_pipeline.py does
# `import torch` / `from dnallm import ...` at module level (lines 16-18) and
# is unimportable in the CPU-only test environment.
PIPELINE_SOURCE = REPO_ROOT / "pipeline" / "dnallmmark_pipeline.py"


@pytest.mark.xfail(strict=True,
                   reason="AUD-01-P0 species-as-dataset — Phase 4 fix")
def test_producer_writes_dataset_species_not_model_organism():
    """The dataset entry constructed by the producer must source ``species``
    from the DATASET row (``row.get``), like every sibling field — never
    from the model row (``model_row.get``).

    Anchors on structure, not text: the unique ``ast.Assign`` whose target
    is a subscript and whose dict literal contains a ``"dataset"`` sub-dict
    (verified unique in the current source). The one-line source fact being
    locked, at ``pipeline/dnallmmark_pipeline.py:1229``::

        "species": model_row.get("species", "unknown"),

    while every sibling field (lines 1230-1236) reads ``row.get(...)``.
    Today the assert fails, so the test xfails; a Phase 4 fix that switches
    the site to ``row.get(...)`` makes it XPASS and FAIL the suite until
    this marker is removed in the same commit.

    Phase 3 caution: the dnallm-dev pipeline adaptation may move or
    restructure this construction site — in that case this anchor gets a
    DELIBERATE one-line update (flagged in the plan), never a silent xfail.
    If the site disappears entirely, the trailing ``pytest.fail`` makes the
    test fail honestly rather than lock nothing.
    """
    tree = ast.parse(PIPELINE_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        # The construction site: master_performance_dict["performance"][name] = {...}
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Subscript)
            and isinstance(node.value, ast.Dict)
        ):
            ds = next(
                (
                    v
                    for k, v in zip(node.value.keys, node.value.values)
                    if isinstance(k, ast.Constant) and k.value == "dataset"
                ),
                None,
            )
            if isinstance(ds, ast.Dict):
                sp = next(
                    (
                        v
                        for k, v in zip(ds.keys, ds.values)
                        if isinstance(k, ast.Constant) and k.value == "species"
                    ),
                    None,
                )
                # Correct behavior: row.get("species", ...). Buggy (today):
                # model_row.get("species", ...).
                is_row_get = (
                    isinstance(sp, ast.Call)
                    and isinstance(sp.func, ast.Attribute)
                    and sp.func.attr == "get"
                    and isinstance(sp.func.value, ast.Name)
                    and sp.func.value.id == "row"
                )
                assert is_row_get, (
                    "dataset.species must be read from the dataset row "
                    "(row.get), never the model row (model_row.get)"
                )
                return
    pytest.fail("construction site not found — pipeline structure changed")


@pytest.mark.xfail(strict=True,
                   reason="WR-02 equal-value bool/int cross-type pairs must be "
                          "reported — Phase 4 fix")
def test_compare_reports_equal_value_bool_int_cross_type():
    """The canonical comparator must report an equal-value bool/int
    cross-type pair instead of staying silent.

    Live risk this silence hides: the 47 pinned task files carry bf16/fp16
    booleans — a regeneration that emits ``1`` where the committed file has
    ``true`` (or vice versa) compares as identical today, so a real type
    change in published data would pass the D-06 vocabulary unnoticed.
    """
    diffs = []
    walk(True, 1, "", diffs)
    assert diffs, "bool/int cross-type pair with equal value must produce a diff"


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param("nan", id="nan"),
        pytest.param("inf", id="inf"),
        pytest.param("-inf", id="-inf"),
    ],
)
@pytest.mark.xfail(strict=True,
                   reason="WR-03 non-finite metrics must be excluded by the "
                          "presence gate — Phase 4 fix")
def test_nonfinite_metric_excluded_from_ranking(bad):
    """A non-finite metric value must coerce to the default (be excluded),
    never pass through as a float.

    Today ``get_float`` returns ``nan``/``inf``/``-inf`` for these inputs
    (pinned as plain assertions in ``tests/test_aggregation.py``), the
    value passes the presence gate as present, and a single NaN zeroes or
    poisons the whole task's MinMax/z-score normalization for every model.
    """
    assert summarize_comparison.get_float(bad, default=None) is None
