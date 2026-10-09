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

- **AUD-01-P0** — species-as-dataset: result JSONs carry a MODEL-organism
  string as a dataset entry's ``species`` (e.g. ``"athaliana"``) instead
  of the dataset's arena category. PIVOTED in Phase 03-01 (decision D-03):
  the original lock anchored on the old pipeline's construction-site AST
  and retired in the same commit as F10's deprecation of
  ``pipeline/dnallmmark_pipeline.py``. The contract now asserts the
  EXPORT-CHAIN OUTPUT directly over a repo-authored fixture result JSON
  (:func:`test_aud01_species_matches_dataset_arena_category`): every
  dataset entry's ``species`` must equal the dataset's ``Category`` row
  in ``pipeline/datasets_info.txt`` (Animals/Plants/Microbe/Multiple).
  The pipeline modules are never imported (``torch``/``dnallm`` at module
  level are unavailable CPU-side; an import would xfail for the wrong
  reason — a false lock). An UNMARKED companion test
  (:func:`test_aud01_contract_fixture_has_expected_shape`) keeps the lock
  honest: the lock's own ``xfail`` marker swallows every failure inside
  its body, so a fixture edit that deletes the defect must fail OUTSIDE
  the marker (WR-01).
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

import csv
import json
from pathlib import Path

import pytest
import summarize_comparison
from compare import walk

REPO_ROOT = Path(__file__).resolve().parents[1]
# Read as DATA, never imported: the pipeline modules do `import torch` /
# `from dnallm import ...` at module level and are unimportable in the
# CPU-only test environment. The D-03 export-chain contract joins the TSV
# registry and a repo-authored fixture as text/JSON — no pipeline import.
DATASETS_INFO = REPO_ROOT / "pipeline" / "datasets_info.txt"
DEFECT_FIXTURE = (
    REPO_ROOT / "tests" / "fixtures" / "export_chain"
    / "defect_species_performance.json"
)
# The legal species value set: the verbatim Category column of
# datasets_info.txt (Animals 20 / Plants 15 / Microbe 13 / Multiple 2).
VALID_SPECIES = frozenset({"Animals", "Plants", "Microbe", "Multiple"})


def _load_category_map():
    """Return ``{Dataset_name: Category}`` parsed from the TSV registry.

    ``datasets_info.txt`` arrives from the dev branch with CRLF line
    endings on every row; opening with ``newline=""`` hands line-ending
    handling to the stdlib csv reader, which normalizes ``\r\n`` row
    terminators (the documented CRLF-tolerant pattern).

    Returns:
        dict[str, str]: dataset/task name -> arena Category.
    """
    with DATASETS_INFO.open("r", encoding="utf-8", newline="") as fh:
        return {
            row["Dataset_name"]: row["Category"]
            for row in csv.DictReader(fh, delimiter="\t")
        }


def _load_fixture():
    """Load the defect-bearing result-JSON fixture as a dict."""
    return json.loads(DEFECT_FIXTURE.read_text(encoding="utf-8"))


def test_aud01_contract_fixture_has_expected_shape():
    """Unmarked companion: the fixture must carry the contract shape.

    Deliberately NOT xfail-marked (WR-01 discipline, adapted with the
    D-03 pivot): ``xfail(strict=True)`` on the lock intercepts every
    failure inside its body — including an explicit ``pytest.fail`` —
    reporting XFAIL with exit 0, so the lock alone degrades SILENTLY to
    locking nothing if the fixture loses its contract shape (a fixture
    edit deleting the defect entry, renaming the ``species`` key, or
    breaking the datasets_info join). This companion goes RED in exactly
    that case: update the fixture deliberately (flagged in the plan),
    never silently.
    """
    doc = _load_fixture()
    entries = doc.get("performance")
    assert isinstance(entries, dict) and len(entries) >= 2, (
        "fixture must be a result-JSON: top-level performance dict with "
        "at least two dataset entries"
    )
    category_map = _load_category_map()
    for name, entry in entries.items():
        assert isinstance(entry, dict), f"{name}: entry must be a dict"
        assert isinstance(entry.get("dataset"), dict), (
            f"{name}: entry must carry a dataset sub-dict"
        )
        assert "species" in entry["dataset"], (
            f"{name}: dataset sub-dict lost its species key — the AUD-01 "
            "lock has nothing to assert; update the fixture deliberately"
        )
        assert name in category_map, (
            f"{name}: fixture dataset resolves to no Category row in "
            f"{DATASETS_INFO} — the lock's join key is broken"
        )


@pytest.mark.xfail(strict=True,
                   reason="AUD-01-P0 species-as-dataset — Phase 4 fix")
def test_aud01_species_matches_dataset_arena_category():
    """Export-chain contract (D-03 pivot): every dataset entry's
    ``species`` must equal the dataset's arena Category from
    ``pipeline/datasets_info.txt``, never a model organism.

    The fixture deliberately carries the defect: its
    ``plant-genomic-benchmark__poly_a.arabidopsis_thaliana`` entry has
    ``species="athaliana"`` — a real MODEL-registry species value
    (``pipeline/models_info.json``) leaked into a dataset field — while
    the dataset's Category is ``Plants``. Today the asserts fail on that
    entry, so the test xfails; Phase 4's F3(2) dataset-side species
    table makes producers write the Category, this test XPASSes, and the
    strict marker FAILS the suite until it is removed in the same commit
    as the fix (house rule above).
    """
    category_map = _load_category_map()
    doc = _load_fixture()
    for name, entry in doc["performance"].items():
        species = entry["dataset"]["species"]
        assert species in VALID_SPECIES, (
            f"{name}: dataset.species {species!r} is a model organism, "
            f"not an arena category (legal values: {sorted(VALID_SPECIES)})"
        )
        expected = category_map[name]
        assert species == expected, (
            f"{name}: dataset.species is {species!r} but the dataset's "
            f"Category is {expected!r} — species must carry the arena "
            "category from datasets_info, never the model organism"
        )


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
