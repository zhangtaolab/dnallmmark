"""
Unit tests for the migration-inventory orchestrator (05-02, DATA-01/D-17/OQ6).

``compare_derived`` and ``write_sha256_manifest`` are pure functions over a
synthetic committed/regenerated tree pair with planted diffs of known
categories (compare.py's vocabulary — the comparator itself is NOT edited);
``run_inventory`` is covered at orchestration level with an injected fake
chain runner over the same synthetic layout (the real chain run happens
live at migration time and its output is committed as
``baseline/f6-migration-inventory.json``).

The script NEVER creates any git tag — the SHA256 manifest it can emit is
the data-v2 gate's tamper-evidence input, not the tag (D-17/OQ3).

See also:
    - ``baseline/compare.py`` — the diff vocabulary owner.
    - ``tests/test_determinism.py`` — the copytree+chdir pattern the real
      chain runner reuses.
"""

import json

from run_migration_inventory import (
    compare_derived,
    run_inventory,
    write_sha256_manifest,
)

# The synthetic derived surface: two comparison files, the index, and the
# two F6-new artifacts. Paths are repo-relative on the committed side.
DERIVED = {
    "data/models_comparison.json": "models_comparison.json",
    "data/models_comparison_plant.json": "models_comparison_plant.json",
    "data/tasks.json": "tasks.json",
    "data/permutation_tests.json": "permutation_tests.json",
    "data/manifest.json": "manifest.json",
}


def _write(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=4, sort_keys=True), encoding="utf-8")


def _committed_pair(tmp_path):
    """Build a synthetic committed root + scratch regen root with planted diffs.

    Committed vs regenerated:

    - models_comparison.json — CHANGED: every model entry gains
      ``weighted_score`` (EXTRA_IN_REGEN) and one rank moves (INT)
    - models_comparison_plant.json — IDENTICAL
    - tasks.json — CHANGED: one metric string re-cased (VALUE)
    - permutation_tests.json — NEW (absent on the committed side)
    - manifest.json — NEW
    """
    committed = tmp_path / "committed"
    regen = tmp_path / "regen"

    comparison_committed = {
        "model-a": {"model": {"name": "A"},
                    "performance": {"rank": 2, "rank_score": 10.0}},
        "model-b": {"model": {"name": "B"},
                    "performance": {"rank": 1, "rank_score": 12.0}},
    }
    comparison_regen = {
        "model-a": {"model": {"name": "A"},
                    "performance": {"rank": 1, "rank_score": 10.0,
                                    "weighted_score": 0.25}},
        "model-b": {"model": {"name": "B"},
                    "performance": {"rank": 2, "rank_score": 12.0,
                                    "weighted_score": 0.5}},
    }
    _write(committed / "data" / "models_comparison.json", comparison_committed)
    _write(regen / "models_comparison.json", comparison_regen)

    plant = {"model-a": {"model": {"name": "A"}, "performance": {"rank": 1}}}
    _write(committed / "data" / "models_comparison_plant.json", plant)
    _write(regen / "models_comparison_plant.json", plant)

    _write(committed / "data" / "tasks.json",
           {"version": "1.0.0", "tasks": [{"task": "t1", "metric": "f1"}]})
    _write(regen / "tasks.json",
           {"version": "1.0.0", "tasks": [{"task": "t1", "metric": "F1"}]})

    _write(regen / "permutation_tests.json", {"info": {"family_size": 1}, "pairs": []})
    _write(regen / "manifest.json",
           {"data_version": "1.1.0", "generated_from": "a" * 40, "date": "2026-10-10"})
    return committed, regen


def test_compare_derived_reports_planted_categories(tmp_path):
    """The planted diffs surface under compare.py's vocabulary with the
    expected per-file statuses: EXTRA_IN_REGEN + INT on the comparison,
    VALUE on the index, identical plant file, and the two new artifacts."""
    committed, regen = _committed_pair(tmp_path)
    result = compare_derived(committed, regen, derived=DERIVED)

    by_path = {entry["path"]: entry for entry in result["files"]}
    assert by_path["data/models_comparison.json"]["status"] == "changed"
    assert by_path["data/models_comparison.json"]["counts"] == {
        "EXTRA_IN_REGEN": 2,  # weighted_score on both models
        "INT": 2,             # both ranks swap 1<->2
    }
    assert by_path["data/models_comparison_plant.json"]["status"] == "identical"
    assert by_path["data/tasks.json"]["counts"] == {"VALUE": 1}
    assert by_path["data/permutation_tests.json"]["status"] == "new"
    assert by_path["data/manifest.json"]["status"] == "new"

    totals = result["totals"]
    assert totals["files_total"] == 5
    assert totals["files_changed"] == 2
    assert totals["files_identical"] == 1
    assert totals["files_new"] == 2
    assert totals["diffs_total"] == 5
    assert totals["counts"] == {
        "EXTRA_IN_REGEN": 2, "INT": 2, "VALUE": 1,
    }


def test_compare_derived_flags_missing_regen_output(tmp_path):
    """A derived file that exists committed but is NOT regenerated is
    reported as ``missing_in_regen`` — never silently dropped."""
    committed, regen = _committed_pair(tmp_path)
    (regen / "tasks.json").unlink()

    result = compare_derived(committed, regen, derived=DERIVED)
    by_path = {entry["path"]: entry for entry in result["files"]}
    assert by_path["data/tasks.json"]["status"] == "missing_in_regen"


def test_run_inventory_orchestrates_and_stamps(tmp_path):
    """run_inventory drives the (injected) chain runner inside a scratch tree,
    compares against the given committed root, and stamps the migration
    identity fields into the written document."""
    committed, _ = _committed_pair(tmp_path)

    calls = []

    def fake_chain_runner(scratch, *, data_dir):
        calls.append((scratch, data_dir))
        _write(scratch / "models_comparison.json",
               {"model-a": {"performance": {"weighted_score": 0.25}}})
        _write(scratch / "permutation_tests.json", {"info": {}, "pairs": []})

    out = tmp_path / "inv" / "inventory.json"
    doc = run_inventory(
        out,
        data_version="1.1.0",
        generated_from="b" * 40,
        date="2026-10-10",
        data_dir=committed / "data",
        committed_root=committed,
        chain_runner=fake_chain_runner,
    )
    assert len(calls) == 1  # the chain ran exactly once, inside the scratch
    assert doc["data_version"] == "1.1.0"
    assert doc["generated_from"] == "b" * 40
    assert doc["date"] == "2026-10-10"
    assert doc["totals"]["files_new"] >= 1
    # The document on disk is the canonical serialization of the return value.
    assert json.loads(out.read_text(encoding="utf-8")) == doc


def test_sha256_manifest_follows_data_v1_convention(tmp_path, monkeypatch):
    """--write-manifest output follows baseline/data-v1.sha256's line
    convention: ``<sha256>  <path>`` (two spaces), repo-relative POSIX
    paths, sorted — and never creates any git tag."""
    import hashlib

    import run_migration_inventory as rmi

    files = {
        "dnallm-mark/data/tasks.json": b'{"version":"1.0.0"}',
        "dnallm-mark/data/models_comparison.json": b'{"model-a":{}}',
        "dnallm-mark/data/models_comparison_animal.json": b'{"model-b":{}}',
    }
    for rel, content in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    monkeypatch.setattr(rmi, "REPO_ROOT", tmp_path)

    out = tmp_path / "out.sha256"
    lines = write_sha256_manifest(sorted(files), out)

    expected = [
        f"{hashlib.sha256(files[rel]).hexdigest()}  {rel}"
        for rel in sorted(files)
    ]
    assert lines == expected
    assert out.read_text(encoding="utf-8") == "\n".join(expected) + "\n"


def test_compare_derived_handles_absent_on_both_sides(tmp_path):
    """A derived path present on NEITHER side is reported ``absent`` (e.g.
    pre-artifact migrations) and contributes to no counter."""
    committed, regen = _committed_pair(tmp_path)
    (committed / "data" / "permutation_tests.json").unlink(missing_ok=True)
    (regen / "permutation_tests.json").unlink()

    result = compare_derived(committed, regen, derived=DERIVED)
    by_path = {entry["path"]: entry for entry in result["files"]}
    assert by_path["data/permutation_tests.json"]["status"] == "absent"
    assert result["totals"]["files_total"] == 5
