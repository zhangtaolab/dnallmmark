"""
Known-defect locks: the three confirmed data-chain defects, pinned
test-first as ``xfail(strict=True)`` tests (D-03/D-04/D-07) and UNMARKED to
permanent green contracts in Phase 4 (D-13 — each fix landed together with
the deliberate marker removal in the same commit: AUD-01 in 04-01 Task 1,
WR-03 in 04-01 Task 2, WR-02 in 04-01 Task 3).

House rule: a defect's fix lands ONLY together with the deliberate removal
of its marker in the same commit. Every marker carried ``strict=True``
and the finding ID in its reason string — with strict semantics an
unexpected XPASS FAILS the suite (verified live on pytest 9.1.1 in the
Phase 2 research), so a Phase 4 fix that leaves its marker behind can never
pass silently, and a marker removed without the fix turns red immediately.

The three former locks (defect semantics pinned test-first, each fixed and
unmarked in Phase 4):

- **AUD-01-P0** — species-as-dataset: result JSONs carry a MODEL-organism
  string as a dataset entry's ``species`` (e.g. ``"athaliana"``) instead
  of the dataset's arena category. PIVOTED in Phase 03-01 (decision D-03):
  the original lock anchored on the old pipeline's construction-site AST
  and retired in the same commit as F10's deprecation of
  ``pipeline/dnallmmark_pipeline.py``. The contract now asserts the
  EXPORT-CHAIN OUTPUT directly over a repo-authored fixture result JSON
  (:func:`test_aud01_species_matches_dataset_arena_category`): every
  dataset entry's ``species`` must equal the dataset's ``Category`` field
  in the unified ``pipeline/datasets_info.json``
  (Animals/Plants/Microbe/Multiple). The Category source was retargeted
  from the retired ``datasets_info.txt`` to the unified JSON in the same
  commit as the .txt retirement (D-03/D-10 interlock, 03-02). The
  pipeline modules are never imported (``torch``/``dnallm`` at module
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

import json
from pathlib import Path

import pytest
import summarize_comparison
from compare import walk

REPO_ROOT = Path(__file__).resolve().parents[1]
# Read as DATA, never imported: the pipeline modules do `import torch` /
# `from dnallm import ...` at module level and are unimportable in the
# CPU-only test environment. The D-03 export-chain contract joins the
# unified JSON registry and a repo-authored fixture as text/JSON — no
# pipeline import. (Category source retargeted from the retired
# datasets_info.txt to the unified JSON in the same commit as the .txt
# retirement, 03-02.)
DATASETS_INFO = REPO_ROOT / "pipeline" / "datasets_info.json"
DEFECT_FIXTURE = (
    REPO_ROOT / "tests" / "fixtures" / "export_chain"
    / "defect_species_performance.json"
)
DATA_DIR = REPO_ROOT / "dnallm-mark" / "data"
MODEL_PERFORMANCE_DIR = DATA_DIR / "model_performance"
# The legal species value set: the verbatim Category field of the unified
# datasets_info.json (Animals 20 / Plants 15 / Microbe 13 / Multiple 2).
VALID_SPECIES = frozenset({"Animals", "Plants", "Microbe", "Multiple"})


def _load_category_map():
    """Return ``{Dataset_name: Category}`` read from the unified JSON registry.

    Keys are the ``Source__task``-form dataset names (the same form the
    result-JSON ``performance`` dict and the fixture use), so the join is
    a plain key lookup — no name normalization, no delimiter parsing.

    Returns:
        dict[str, str]: dataset/task name -> arena Category.
    """
    with DATASETS_INFO.open("r", encoding="utf-8") as fh:
        registry = json.load(fh)
    return {name: entry["Category"] for name, entry in registry.items()}


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


def test_aud01_species_matches_dataset_arena_category():
    """Export-chain contract (D-03 pivot): every dataset entry's
    ``species`` must equal the dataset's arena Category from the unified
    ``pipeline/datasets_info.json``, never a model organism.

    The fixture originally carried the defect: its
    ``plant-genomic-benchmark__poly_a.arabidopsis_thaliana`` entry had
    ``species="athaliana"`` — a real MODEL-registry species value
    (``pipeline/models_info.json``) leaked into a dataset field — while
    the dataset's Category is ``Plants``. The asserts failed on that
    entry until the Phase 4 fix (04-01 Task 1: fixture entry corrected to
    ``"Plants"`` + marker removed in the same commit); the contract is now
    a permanent green guard over the fixture's shape.
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


def _real_tree_arena_groups():
    """Derive the real-tree arena groups exactly as the FIXED grouping join
    in ``summarize_comparison`` does: registry ``Category`` (via
    :func:`_load_category_map`) over the dataset names present in the
    committed ``model_performance`` files, with Multiple resolved to the
    maintainer-confirmed majority arena (production ``MAJORITY_ARENA`` —
    one source of truth).

    Returns:
        dict[str, list[str]]: arena (Animals/Plants/Microbe) -> member names.
    """
    category_map = _load_category_map()
    present = set()
    for path in sorted(MODEL_PERFORMANCE_DIR.glob("*_performance.json")):
        present.update(
            json.loads(path.read_text(encoding="utf-8"))["performance"]
        )
    groups = {}
    for name in present:
        category = category_map[name]
        arena = summarize_comparison.MAJORITY_ARENA.get(category, category)
        groups.setdefault(arena, []).append(name)
    return groups


def test_real_tree_arena_membership():
    """Real-data guard for the FIX-02 grouping switch (04-01): the committed
    animal/microbe comparison files' dataset membership must match the
    Category-derived grouping — ``GUE__EPI_GM12878`` in the Animals arena
    and ``GUE__fungi_species_20`` in Microbe (the maintainer-confirmed
    swap), with arena sizes 22/13 corroborated by the per-model ``samples``
    ceiling inside the committed files themselves.
    """
    groups = _real_tree_arena_groups()
    animal, microbe = set(groups["Animals"]), set(groups["Microbe"])

    assert "GUE__EPI_GM12878" in animal, "EPI_GM12878 must group as Animals"
    assert "GUE__fungi_species_20" not in animal
    assert "GUE__fungi_species_20" in microbe, (
        "fungi_species_20 must group as Microbe"
    )
    assert "GUE__EPI_GM12878" not in microbe
    assert len(animal) == 22 and len(microbe) == 13, (
        f"arena sizes drifted: animal={len(animal)} microbe={len(microbe)}"
    )

    # The committed files corroborate the join-derived sizes: the per-model
    # ``samples`` ceiling equals the arena's dataset count.
    for fname, size in (
        ("models_comparison_animal.json", len(animal)),
        ("models_comparison_microbe.json", len(microbe)),
    ):
        comparison = json.loads((DATA_DIR / fname).read_text(encoding="utf-8"))
        max_samples = max(m["performance"]["samples"] for m in comparison.values())
        assert max_samples == size, (
            f"{fname}: max per-model samples {max_samples} contradicts the "
            f"join-derived {fname.removesuffix('.json')} dataset count {size}"
        )


def test_unregistered_dataset_aborts_grouping(tmp_path, monkeypatch):
    """FIX-02 hard-fail join: a result file referencing a dataset with no
    registry row aborts the run (``KeyError``) — a silent fallback to the
    file's ``species`` value would re-create the defect class being fixed.
    """
    staged = tmp_path / "model_performance"
    staged.mkdir()
    doc = _load_fixture()
    doc["performance"]["No__registry_row"] = dict(
        next(iter(doc["performance"].values()))
    )
    (staged / "unregistered_performance.json").write_text(
        json.dumps(doc), encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    with pytest.raises(KeyError):
        summarize_comparison.main()


def test_compare_reports_equal_value_bool_int_cross_type():
    """The canonical comparator must report an equal-value bool/int
    cross-type pair instead of staying silent.

    Live risk this silence hid before the fix (04-01 Task 3, WR-02): the
    47 pinned task files carry bf16/fp16 booleans — a regeneration that
    emits ``1`` where the committed file has ``true`` (or vice versa)
    compared as identical, so a real type change in published data would
    have passed the D-06 vocabulary unnoticed. The pair now reports as
    ``BOOL_CROSS``.
    """
    diffs = []
    walk(True, 1, "", diffs)
    assert diffs, "bool/int cross-type pair with equal value must produce a diff"


def test_compare_same_type_equal_values_stay_silent():
    """WR-02 converse: equal same-type pairs report nothing — ``true`` vs
    ``true`` and ``1`` vs ``1`` are genuinely identical JSON values, so the
    cross-type reporting added for WR-02 must not over-report."""
    diffs = []
    walk(True, True, "", diffs)
    walk(False, False, "", diffs)
    walk(1, 1, "", diffs)
    assert diffs == []


def test_compare_labels_int_vs_int_mismatch_as_int():
    """IN-01: a pure int-vs-int unequal pair (the species diff's rank /
    samples / top-K counters) carries the INT label, not FLOAT_BIG; equal
    ints stay silent; a mixed int/float unequal pair keeps the existing
    float label path unchanged."""
    diffs = []
    walk({"rank": 3, "n": 5}, {"rank": 4, "n": 5}, "", diffs)
    assert [(kind, path) for kind, path, _ in diffs] == [("INT", "/rank")], diffs

    mixed = []
    walk(3, 3.5, "", mixed)
    assert [kind for kind, _, _ in mixed] == ["FLOAT_BIG"], mixed


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param("nan", id="nan"),
        pytest.param("inf", id="inf"),
        pytest.param("-inf", id="-inf"),
    ],
)
def test_nonfinite_metric_excluded_from_ranking(bad):
    """A non-finite metric value must coerce to the default (be excluded),
    never pass through as a float.

    Before the fix (04-01 Task 2, WR-03) ``get_float`` returned
    ``nan``/``inf``/``-inf`` for these inputs (then pinned as plain
    assertions in ``tests/test_aggregation.py``), the value passed the
    presence gate as present, and a single NaN zeroed or poisoned the
    whole task's MinMax/z-score normalization for every model. The
    isfinite guard now returns the default for all three.
    """
    assert summarize_comparison.get_float(bad, default=None) is None
