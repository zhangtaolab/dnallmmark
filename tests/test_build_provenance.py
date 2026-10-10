# =====================================================================
# test_build_provenance.py — provenance emitter contracts (06-04, DATA-04/DATA-05)
#
# Pins the registry-driven emitter over synthetic registries: determinism
# (byte-identical re-emission, no clock), DATA.md marker safety (ONLY the
# content between the GENERATED PROVENANCE BEGIN/END markers changes;
# maintainer-authored sections are byte-identical), the append-when-absent
# bootstrap path, the Unspecified discipline (blank or missing provenance
# cells abort loudly — the committed artifact never carries a blank), and
# schema conformance of the emitted JSON against schemas/provenance.json.
#
# See also:
#     - ``script/build_provenance.py`` — the emitter under test.
#     - ``tests/test_schemas.py`` — the committed-artifact bucket.
# =====================================================================

import csv
import json
from pathlib import Path

import build_provenance  # conftest puts script/ on sys.path
import pytest
from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parents[1]

PROVENANCE_FIELDS = ("source", "citation", "license", "preprocessing",
                     "download_url", "download_url_alternates")


def make_registry():
    """A small synthetic registry with all six provenance fields populated.

    Mirrors the real registry's mix: a resolved license, an Unspecified
    license, and an Unspecified citation.
    """
    def entry(**prov):
        base = {
            "Dataset_name": "unused-name-field", "Dataset_path": "datasets/x",
            "Train": 100, "Test": 10, "Dev": 1, "type": "binary",
            "labels": 2, "length": 500, "metric": "f1", "Category": "Plants",
            "Index": 1,
        }
        base.update({
            "source": "https://example.org/source",
            "citation": 'Some One et al., "A dataset", Journal, 2024',
            "license": "Unspecified",
            "preprocessing": "train/dev/test CSVs; Dev carved by make_dev_splits",
            "download_url": "https://modelscope.cn/datasets/org/name",
            "download_url_alternates": "Unspecified",
        })
        base.update(prov)
        return base

    return {
        "BEND__CpG_methylation": entry(license="Unspecified"),
        "GUE__emp_H3": entry(),
        "zeta__last_sorted": entry(license="CC BY-NC-SA 4.0"),
    }


def emit(tmp_path, registry=None, data_md_name="DATA.md", seed_markdown=None):
    """Run the emitter over a synthetic registry into tmp dirs.

    Args:
        tmp_path (Path): pytest tmp dir.
        registry (dict | None): registry (default: :func:`make_registry`).
        data_md_name (str): name for the DATA.md fixture file.
        seed_markdown (str | None): pre-existing DATA.md content (None ->
            an absent file, exercising creation).

    Returns:
        tuple: ``(data_dir, data_md)`` paths the emitter wrote.
    """
    data_dir = tmp_path / "data"
    data_md = tmp_path / data_md_name
    if seed_markdown is not None:
        data_md.write_text(seed_markdown, encoding="utf-8")
    build_provenance.write_artifacts(registry or make_registry(),
                                      data_dir, data_md)
    return data_dir, data_md


# ===== Determinism =====


def test_emission_is_deterministic(tmp_path):
    """Two runs over the same registry produce byte-identical artifacts
    (json, csv, DATA.md) — sorted iteration, sort_keys, no clock."""
    dir_a, md_a = emit(tmp_path / "run_a")
    dir_b, md_b = emit(tmp_path / "run_b")
    for name in ("provenance.json", "provenance.csv"):
        assert (dir_a / name).read_bytes() == (dir_b / name).read_bytes()
    assert md_a.read_bytes() == md_b.read_bytes()


def test_reemission_over_its_own_output_is_a_no_op(tmp_path):
    """Emitting over the already-emitted DATA.md changes nothing (the
    drift-gate invariant `make data` depends on)."""
    data_dir, data_md = emit(tmp_path)
    before = data_md.read_bytes()
    build_provenance.write_artifacts(make_registry(), data_dir, data_md)
    assert data_md.read_bytes() == before


# ===== Row construction + Unspecified discipline =====


def test_rows_cover_every_registry_entry_in_sorted_order():
    """One row per registry entry, sorted by dataset name, carrying the
    six provenance fields plus the dataset key."""
    rows = build_provenance.build_rows(make_registry())
    assert [row["dataset"] for row in rows] == sorted(make_registry())
    for row in rows:
        assert set(row) == {"dataset", *PROVENANCE_FIELDS}


def test_blank_provenance_cell_aborts(tmp_path):
    """A blank provenance value aborts the emission naming the dataset and
    field — the committed artifact never carries a blank cell."""
    registry = make_registry()
    registry["GUE__emp_H3"]["license"] = ""
    with pytest.raises(SystemExit, match=r"GUE__emp_H3.*license|license.*GUE__emp_H3"):
        build_provenance.write_artifacts(registry, tmp_path / "data",
                                         tmp_path / "DATA.md")


def test_missing_provenance_key_aborts(tmp_path):
    """A registry entry missing a provenance column aborts the emission."""
    registry = make_registry()
    del registry["GUE__emp_H3"]["citation"]
    with pytest.raises(SystemExit, match="citation"):
        build_provenance.write_artifacts(registry, tmp_path / "data",
                                         tmp_path / "DATA.md")


def test_unspecified_is_preserved_not_blank(tmp_path):
    """Unresolved values stay the literal string Unspecified — the honest
    publication-safe state, never a blank or null."""
    data_dir, _ = emit(tmp_path)
    doc = json.loads((data_dir / "provenance.json").read_text(encoding="utf-8"))
    licenses = {row["dataset"]: row["license"] for row in doc["rows"]}
    assert licenses["BEND__CpG_methylation"] == "Unspecified"
    assert licenses["zeta__last_sorted"] == "CC BY-NC-SA 4.0"


# ===== DATA.md marker safety =====


def test_marker_section_replaces_only_between_markers(tmp_path):
    """With markers present, ONLY the content between them changes; the
    maintainer-authored sections before and after are byte-identical."""
    prose_before = "# Maintainer notes\n\nKeep this prose untouched.\n\n"
    prose_after = "\n## Afterword\n\nAlso untouched.\n"
    seed = (prose_before
            + build_provenance.BEGIN_MARKER + "\nSTALE CONTENT\n"
            + build_provenance.END_MARKER + prose_after)
    _data_dir, data_md = emit(tmp_path, seed_markdown=seed)
    text = data_md.read_text(encoding="utf-8")
    assert text.startswith(prose_before)
    assert text.endswith(prose_after)
    assert "STALE CONTENT" not in text
    assert build_provenance.BEGIN_MARKER in text
    assert build_provenance.END_MARKER in text
    # The table rows landed between the markers.
    begin = text.index(build_provenance.BEGIN_MARKER)
    end = text.index(build_provenance.END_MARKER)
    section = text[begin:end]
    for name in sorted(make_registry()):
        assert name in section


def test_append_when_markers_absent(tmp_path):
    """Without markers (the bootstrap over the pre-provenance DATA.md),
    the section is appended and the existing content is preserved
    byte-for-byte as a prefix."""
    existing = "# Old generated audit\n\n| a | b |\n"
    _data_dir, data_md = emit(tmp_path, seed_markdown=existing)
    text = data_md.read_text(encoding="utf-8")
    assert text.startswith(existing)
    assert build_provenance.BEGIN_MARKER in text
    assert text.index(build_provenance.END_MARKER) > text.index(
        build_provenance.BEGIN_MARKER)


def test_unbalanced_marker_aborts(tmp_path):
    """A BEGIN marker with no END marker aborts loudly instead of
    duplicating sections."""
    seed = ("# Notes\n\n" + build_provenance.BEGIN_MARKER + "\nstranded\n")
    with pytest.raises(SystemExit, match="marker"):
        emit(tmp_path, seed_markdown=seed)


# ===== Artifact shape + schema =====


def test_emitted_json_validates_against_schema(tmp_path):
    """The emitted provenance.json validates against the strict committed
    schema (draft 2020-12; every field required, no blanks). The
    minItems/maxItems row pin (50 = the committed corpus) is relaxed for
    the synthetic registry here; the committed artifact itself is pinned
    in full by the tests/test_schemas.py ``provenance`` bucket."""
    data_dir, _ = emit(tmp_path)
    schema = json.loads((REPO / "schemas" / "provenance.json")
                        .read_text(encoding="utf-8"))
    schema["properties"]["rows"].pop("minItems", None)
    schema["properties"]["rows"].pop("maxItems", None)
    doc = json.loads((data_dir / "provenance.json").read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(doc))
    assert not errors, "\n".join(e.message for e in errors[:5])


def test_emitted_csv_has_header_and_sorted_rows(tmp_path):
    """The CSV is the maintainer-editable surface: header first, one row
    per dataset in sorted order, comma-quoting neutral (csv module)."""
    data_dir, _ = emit(tmp_path)
    with open(data_dir / "provenance.csv", encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == ["dataset", *PROVENANCE_FIELDS]
    assert [row[0] for row in rows[1:]] == sorted(make_registry())
    for row in rows[1:]:
        assert all(cell.strip() for cell in row), "no blank CSV cells"


def test_committed_artifacts_match_emission(tmp_path):
    """The committed artifacts are exactly what the emitter produces over
    the committed registry (chain-produced, never hand-edited). DATA.md
    is a transform of its committed self: seeding the fixture with the
    committed file, re-emission must be byte-identical (the no-op proof
    the drift gate depends on)."""
    registry = json.loads((REPO / "pipeline" / "datasets_info.json")
                          .read_text(encoding="utf-8"))
    committed_md = (REPO / "DATA.md").read_text(encoding="utf-8")
    data_dir, data_md = emit(tmp_path, registry=registry,
                             seed_markdown=committed_md)
    committed_dir = REPO / "dnallm-mark" / "data"
    assert (committed_dir / "provenance.json").read_bytes() == \
        (data_dir / "provenance.json").read_bytes()
    assert (committed_dir / "provenance.csv").read_bytes() == \
        (data_dir / "provenance.csv").read_bytes()
    assert committed_md.encode("utf-8") == data_md.read_bytes()


def test_committed_registry_has_no_blank_provenance_cells():
    """All 50 committed registry entries carry non-blank provenance values."""
    registry = json.loads((REPO / "pipeline" / "datasets_info.json")
                          .read_text(encoding="utf-8"))
    assert len(registry) == 50
    for name, entry in registry.items():
        for field in PROVENANCE_FIELDS:
            assert isinstance(entry.get(field), str) and entry[field].strip(), \
                f"{name}.{field} is blank or missing"
