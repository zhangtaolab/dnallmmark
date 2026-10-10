"""
Unit tests for the D-10 extensions to ``script/convert_registry.py``.

Two suites live here:

- **Regression pins** for the committed converter behavior (c3843d7): the
  stock ``--to-json --merge-existing`` merge (adds new names, overwrites
  fields on shared names, preserves existing keys not named in the CSV) and
  the numeric discipline (preset numeric columns coerce to int, empty cells
  stay strings, ``Model_size`` stays the verbatim string). These pin the
  behavior the 03-02 unification depends on so the extensions cannot
  regress it.
- **Extension tests** for the D-10 additions (03-02): ``--rename-name``
  (merge-key + name-cell rewrite for the 3 bare ``gene_exp.*`` dataset
  names), the name-column-lands-as-field contract (``key == Model_name`` /
  ``key == Dataset_name`` for every entry — what ``run_finetune.py``'s
  dict read site and tests/test_registry_unification.py both require), and
  ``--derive-operational`` (operational four derived for the 6 json-only
  card entries per the documented convention).
- **Provenance extension tests** (06-04, DATA-04/DATA-05): the six
  provenance columns round-trip through ``--to-csv`` ->
  ``--to-json --merge-existing`` to identical JSON values; an ingest CSV
  missing expected columns aborts naming the expected set (the D-10
  wrong-count family); ``--to-csv`` of the enriched registry emits all 17
  columns.

The converter is exercised through its module API (``to_json`` with an
``argparse.Namespace`` shaped exactly like the real parser output, plus a
``parse_args`` wiring test) — conftest puts ``script/`` on ``sys.path``
(same contract as ``tests/test_aggregation.py``).

See also:
    - ``script/convert_registry.py`` — the converter under test.
    - ``tests/test_registry_unification.py`` — the single-source contract
      over the real unified registries.
"""

import argparse
import json
import sys
from pathlib import Path

import convert_registry  # conftest puts script/ on sys.path
import pytest

MODELS_TSV_HEADER = ("Model_name\tModel_path\tModel_size\tTokenizer"
                     "\tMean_token_length\n")
# The datasets surface carries the six provenance columns (06-04, DATA-04/
# DATA-05) — every datasets fixture must present the full 17-column header
# or the abort-on-missing-columns ingest (D-10 wrong-count family) refuses.
DATASETS_TSV_HEADER = ("Index\tDataset_name\tDataset_path\tTrain\tTest\tDev"
                       "\ttype\tlabels\tlength\tmetric\tCategory"
                       "\tsource\tcitation\tlicense\tpreprocessing"
                       "\tdownload_url\tdownload_url_alternates\n")


def _provenance_cells(**overrides):
    """Six provenance cells with D-10-safe defaults (never blank)."""
    cells = {
        "source": "https://example.org/source",
        "citation": "Test Author et al., \"A dataset\", Journal, 2024",
        "license": "Unspecified",
        "preprocessing": "train/dev/test CSVs; Dev carved via make_dev_splits",
        "download_url": "https://modelscope.cn/datasets/org/name",
        "download_url_alternates": "Unspecified",
    }
    cells.update(overrides)
    return cells


def _datasets_row(index, name, provenance=None, **field_overrides):
    """One datasets CSV row line from column values + provenance cells."""
    fields = {
        "Index": str(index),
        "Dataset_name": name,
        "Dataset_path": f"datasets/{name}",
        "Train": "100",
        "Test": "10",
        "Dev": "0",
        "type": "binary",
        "labels": "2",
        "length": "500",
        "metric": "f1",
        "Category": "Plants",
        **field_overrides,
    }
    cells = _provenance_cells(**(provenance or {}))
    values = [fields[c] for c in (
        "Index", "Dataset_name", "Dataset_path", "Train", "Test", "Dev",
        "type", "labels", "length", "metric", "Category",
    )] + [cells[c] for c in (
        "source", "citation", "license", "preprocessing",
        "download_url", "download_url_alternates",
    )]
    return "\t".join(values) + "\n"


def run_to_json(tmp_path, tsv_text, existing=None, kind="models",
                rename_name=None, derive_operational=False):
    """Run the converter's ``--to-json`` direction over fixture files.

    Builds the ``argparse.Namespace`` the real parser produces for the
    flags below (verified by ``test_cli_wires_new_flags``) and calls
    ``to_json`` directly, returning the parsed output registry.

    Args:
        tmp_path (Path): pytest tmp dir for the fixture files.
        tsv_text (str): TSV fixture (tab-delimited, LF or CRLF).
        existing (dict | None): registry for ``--merge-existing``.
        kind (str): ``models`` or ``datasets`` preset.
        rename_name (list[str] | None): ``--rename-name FROM=TO`` values.
        derive_operational (bool): ``--derive-operational``.

    Returns:
        dict: the output registry parsed from the written JSON.
    """
    csv_path = tmp_path / "input.txt"
    csv_path.write_text(tsv_text, encoding="utf-8", newline="")
    out_path = tmp_path / "out.json"
    merge_path = ""
    if existing is not None:
        merge_path = tmp_path / "existing.json"
        merge_path.write_text(json.dumps(existing), encoding="utf-8")
        merge_path = str(merge_path)
    args = argparse.Namespace(
        to_json=True, to_csv=False, kind=kind,
        input=str(csv_path), output=str(out_path),
        merge_existing=merge_path or None,
        map=[], numeric=[], columns=[], crlf=False,
        rename_name=list(rename_name or []),
        derive_operational=derive_operational,
    )
    convert_registry.to_json(args, convert_registry.KIND_PRESETS[kind])
    return json.loads(out_path.read_text(encoding="utf-8"))


def card_entry(name, size, tokenizer, token_len):
    """Build a models_info.json card entry (the 11 dev-registry keys)."""
    return {
        "name": name,
        "size (M)": size,
        "type": "MLM",
        "tokenizer": tokenizer,
        "mean_token_len": token_len,
        "architecture": "Transformer",
        "series": "TestSeries",
        "context_len (bp)": 1024,
        "species": "plants",
        "huggingface": "test/model",
        "modelscope": "test/model",
    }


# ===== Stock-merge regression pins (committed c3843d7 behavior) =====


def test_stock_merge_adds_overwrites_preserves(tmp_path):
    """--merge-existing: CSV adds new names, overwrites shared fields,
    and preserves existing keys not named in the CSV."""
    existing = {
        "keeper": {"series": "solo"},
        "shared": {"series": "old", "note": "keep-me"},
    }
    tsv = (MODELS_TSV_HEADER
           + "shared\tmodels/shared\t10M\tBPE\t6\n"
             "fresh\tmodels/fresh\t20M\tBPE\t6\n")
    result = run_to_json(tmp_path, tsv, existing=existing, kind="models")
    assert set(result) == {"keeper", "shared", "fresh"}
    assert result["keeper"] == {"series": "solo"}  # untouched
    assert result["shared"]["Model_path"] == "models/shared"  # CSV fields land
    assert result["shared"]["note"] == "keep-me"  # merge, not replace
    assert result["fresh"]["Model_size"] == "20M"  # verbatim string
    assert result["fresh"]["Mean_token_length"] == 6  # numeric coercion


def test_numeric_discipline_unchanged(tmp_path):
    """Preset numeric columns coerce to int; empty cells stay strings;
    ``Model_size`` stays the verbatim string (e.g. ``470M``)."""
    tsv = (MODELS_TSV_HEADER
           + "big\tmodels/big\t470M\tBPE\t6\n"
             "tiny\tmodels/tiny\t<1M\tBPE\t1\n")
    result = run_to_json(tmp_path, tsv, kind="models")
    assert result["big"]["Model_size"] == "470M"
    assert result["big"]["Mean_token_length"] == 6
    assert result["tiny"]["Model_size"] == "<1M"

    tsv_ds = (DATASETS_TSV_HEADER
              + _datasets_row(1, "d1")
              + _datasets_row(2, "d2", Dev=""))
    result = run_to_json(tmp_path, tsv_ds, kind="datasets")
    assert result["d1"]["Dev"] == 0  # numeric cell coerced
    assert result["d1"]["Train"] == 100
    assert result["d2"]["Dev"] == ""  # empty cell stays a string
    assert result["d1"]["license"] == "Unspecified"  # provenance round-trips
    assert result["d2"]["download_url"].startswith("https://")


# ===== D-10 extensions =====


def test_name_column_lands_as_field(tmp_path):
    """The name-column cell lands verbatim as a field on every merged
    entry, so ``key == Model_name`` / ``key == Dataset_name`` holds —
    the contract run_finetune.py's dict read site reads and
    tests/test_registry_unification.py pins."""
    tsv = (MODELS_TSV_HEADER
           + "alpha\tmodels/alpha\t10M\tBPE\t6\n")
    result = run_to_json(tmp_path, tsv, kind="models")
    assert result["alpha"]["Model_name"] == "alpha"

    tsv_ds = (DATASETS_TSV_HEADER
              + _datasets_row(1, "d1"))
    result = run_to_json(tmp_path, tsv_ds, kind="datasets")
    assert result["d1"]["Dataset_name"] == "d1"


def test_rename_name_merges_into_existing_key(tmp_path):
    """--rename-name rewrites the merge key AND the name-column cell: a
    CSV row named ``gene_exp.x`` merged with
    ``--rename-name gene_exp.x=suite__gene_exp.x`` lands INSIDE the
    existing ``suite__gene_exp.x`` entry — no duplicate key added."""
    existing = {
        "suite__gene_exp.x": {
            "Dataset_path": "datasets/suite/gene_exp.x",
            "Train": 100, "Dev": 0,
        },
    }
    tsv = (DATASETS_TSV_HEADER
           + _datasets_row(7, "gene_exp.x",
                           Dataset_path="datasets/suite/gene_exp.x",
                           metric="spearman"))
    result = run_to_json(tmp_path, tsv, existing=existing, kind="datasets",
                         rename_name=["gene_exp.x=suite__gene_exp.x"])
    assert set(result) == {"suite__gene_exp.x"}  # key set unchanged
    entry = result["suite__gene_exp.x"]
    assert entry["Dataset_name"] == "suite__gene_exp.x"  # cell renamed
    assert entry["Category"] == "Plants"  # CSV fields merged in
    assert entry["Index"] == 7
    assert entry["Train"] == 100


def test_rename_name_collision_aborts(tmp_path):
    """Two CSV rows mapping to the same final name (one renamed onto the
    other) abort loudly instead of merging silently."""
    tsv = (DATASETS_TSV_HEADER
           + _datasets_row(7, "gene_exp.x",
                           Dataset_path="datasets/suite/gene_exp.x",
                           metric="spearman")
           + _datasets_row(8, "suite__gene_exp.x",
                           Dataset_path="datasets/suite/gene_exp.x",
                           metric="spearman"))
    with pytest.raises(SystemExit, match="suite__gene_exp.x"):
        run_to_json(tmp_path, tsv, kind="datasets",
                    rename_name=["gene_exp.x=suite__gene_exp.x"])


def test_derive_operational_fills_card_only_entries(tmp_path):
    """--derive-operational: entries from --merge-existing that lack the
    operational four gain derived values; entries already carrying them
    (and CSV-supplied entries) are untouched; card keys are never
    modified."""
    existing = {
        "CardOnly": card_entry("CardOnly", 94, "6-mer", 6),
        "HasOps": {
            **card_entry("HasOps", 88, "singlebase", 1),
            "Model_name": "HasOps",
            "Model_path": "models/custom",  # pre-existing — must survive
            "Model_size": "88M",
            "Tokenizer": "singlebase",
            "Mean_token_length": 1,
        },
    }
    tsv = (MODELS_TSV_HEADER
           + "FromCsv\tmodels/from_csv\t30M\tBPE\t6\n")
    result = run_to_json(tmp_path, tsv, existing=existing, kind="models",
                         derive_operational=True)
    derived = result["CardOnly"]
    assert derived["Model_path"] == "models/CardOnly"  # key convention
    assert derived["Model_size"] == "94M"  # card value + M suffix
    assert derived["Tokenizer"] == "6-mer"
    assert derived["Mean_token_length"] == 6
    assert derived["Model_name"] == "CardOnly"
    assert derived["name"] == "CardOnly"  # card keys unmodified
    assert derived["size (M)"] == 94
    assert derived["tokenizer"] == "6-mer"
    # Already-operational merge-existing entry: untouched by derivation
    assert result["HasOps"]["Model_path"] == "models/custom"
    # CSV-supplied entry: keeps its own verbatim operational values
    assert result["FromCsv"]["Model_path"] == "models/from_csv"
    assert result["FromCsv"]["Model_size"] == "30M"


def test_derive_operational_size_formatting(tmp_path):
    """Numeric ``size (M)`` gains an ``M`` suffix; non-numeric card sizes
    pass through verbatim."""
    existing = {
        "FloatSize": card_entry("FloatSize", 8.1, "singlebase", 1),
        "StrSize": card_entry("StrSize", "~1B", "BPE", 6),
    }
    tsv = MODELS_TSV_HEADER + "other\tmodels/other\t5M\tBPE\t6\n"
    result = run_to_json(tmp_path, tsv, existing=existing, kind="models",
                         derive_operational=True)
    assert result["FloatSize"]["Model_size"] == "8.1M"
    assert result["StrSize"]["Model_size"] == "~1B"


def test_derive_operational_requires_models_kind_and_merge_existing(tmp_path):
    """--derive-operational is a models-kind, --merge-existing flag:
    other combinations abort with a clear error."""
    tsv = MODELS_TSV_HEADER + "a\tmodels/a\t5M\tBPE\t6\n"
    tsv_ds = (DATASETS_TSV_HEADER
              + _datasets_row(1, "d0", Train="10"))
    with pytest.raises(SystemExit, match="models"):
        run_to_json(tmp_path, tsv_ds, existing={"d0": {"Train": 10}},
                    kind="datasets", derive_operational=True)
    with pytest.raises(SystemExit, match="merge-existing"):
        run_to_json(tmp_path, tsv, kind="models", derive_operational=True)


def test_cli_wires_new_flags(monkeypatch, tmp_path):
    """The CLI accepts the new flags and parses them into the namespace
    ``to_json`` consumes (the surface the 03-02 unification invokes)."""
    monkeypatch.setattr(sys, "argv", [
        "convert_registry.py", "--kind", "models", "--to-json",
        "--input", str(tmp_path / "in.txt"),
        "--output", str(tmp_path / "out.json"),
        "--merge-existing", str(tmp_path / "ex.json"),
        "--rename-name", "gene_exp.x=suite__gene_exp.x",
        "--derive-operational",
    ])
    args = convert_registry.parse_args()
    assert args.rename_name == ["gene_exp.x=suite__gene_exp.x"]
    assert args.derive_operational is True


# ===== 06-04 provenance columns (DATA-04 / DATA-05) =====

PROVENANCE_COLUMNS = ("source", "citation", "license", "preprocessing",
                      "download_url", "download_url_alternates")


def run_to_csv(tmp_path, registry, kind="datasets", columns=None):
    """Run the converter's ``--to-csv`` direction over a fixture registry.

    Args:
        tmp_path (Path): pytest tmp dir for the fixture files.
        registry (dict): JSON registry object.
        kind (str): ``models`` or ``datasets`` preset.
        columns (list[str] | None): optional ``--columns`` override.

    Returns:
        str: the emitted CSV text.
    """
    in_path = tmp_path / "in.json"
    in_path.write_text(json.dumps(registry), encoding="utf-8")
    out_path = tmp_path / "out.csv"
    args = argparse.Namespace(
        to_json=False, to_csv=True, kind=kind,
        input=str(in_path), output=str(out_path),
        merge_existing=None,
        map=[], numeric=[], columns=list(columns or []),
        crlf=False, rename_name=[], derive_operational=False,
    )
    convert_registry.to_csv(args, convert_registry.KIND_PRESETS[kind])
    return out_path.read_text(encoding="utf-8")


def test_provenance_columns_round_trip(tmp_path):
    """A CSV carrying the six provenance columns re-ingests to identical
    JSON values (``--to-json --merge-existing`` over the CSV produced by
    ``--to-csv`` of the same registry) — the D-10 edit surface."""
    registry = {
        "BEND__CpG_methylation": {
            "Dataset_name": "BEND__CpG_methylation",
            "Dataset_path": "datasets/BEND/CpG_methylation",
            "Train": 743095, "Test": 106227, "Dev": 109717,
            "type": "binary", "labels": 2, "length": 500,
            "metric": "AUPRC", "Category": "Animals", "Index": 1,
            **_provenance_cells(license="Unspecified"),
        },
        "GUE__emp_H3": {
            "Dataset_name": "GUE__emp_H3",
            "Dataset_path": "datasets/GUE/emp_H3",
            "Train": 11971, "Test": 1497, "Dev": 1497,
            "type": "binary", "labels": 2, "length": 500,
            "metric": "f1", "Category": "Microbe", "Index": 2,
            **_provenance_cells(license="CC BY-NC-SA 4.0",
                                 citation="Zhou et al., 2023"),
        },
    }
    csv_text = run_to_csv(tmp_path, registry)
    # --to-csv emits all 17 columns with values (no blank provenance cells).
    header = csv_text.splitlines()[0].split(",")
    assert header[:1] == ["Index"]  # preset order starts with Index
    for col in PROVENANCE_COLUMNS:
        assert col in header
    assert len(header) == 17

    # Ingest the emitted CSV back with --merge-existing over the same
    # registry: every value (including all six provenance fields) is
    # identical — the round-trip is lossless.
    csv_path = tmp_path / "roundtrip.csv"
    csv_path.write_text(csv_text, encoding="utf-8")
    merge_path = tmp_path / "existing.json"
    merge_path.write_text(json.dumps(registry), encoding="utf-8")
    out_path = tmp_path / "roundtrip.json"
    args = argparse.Namespace(
        to_json=True, to_csv=False, kind="datasets",
        input=str(csv_path), output=str(out_path),
        merge_existing=str(merge_path),
        map=[], numeric=[], columns=[], crlf=False,
        rename_name=[], derive_operational=False,
    )
    convert_registry.to_json(args, convert_registry.KIND_PRESETS["datasets"])
    result = json.loads(out_path.read_text(encoding="utf-8"))
    assert result == registry


def test_to_csv_emits_empty_cells_only_where_value_genuinely_absent(tmp_path):
    """``--to-csv`` of an entry missing a provenance column emits an empty
    cell for it (the pre-seeding state); after seeding, no blank cells
    remain — the emitter discipline is what forbids blanks, not the
    converter."""
    registry = {
        "d1": {"Dataset_name": "d1", "Dataset_path": "datasets/d1"},
    }
    csv_text = run_to_csv(tmp_path, registry)
    header = csv_text.splitlines()[0].split(",")
    source_idx = header.index("source")
    row = csv_text.splitlines()[1].split(",")
    assert row[source_idx] == ""  # genuinely absent -> empty cell


def test_ingest_aborts_on_missing_expected_columns(tmp_path):
    """A CSV missing an expected column aborts with the wrong-count error
    naming the expected set (the D-10 abort-on-missing-columns family) —
    a partial header can never silently drop provenance fields."""
    legacy_header = ("Index\tDataset_name\tDataset_path\tTrain\tTest\tDev"
                     "\ttype\tlabels\tlength\tmetric\tCategory\n")
    tsv = legacy_header + _datasets_row(1, "d1").rsplit("\t", 6)[0] + "\n"
    with pytest.raises(SystemExit, match="source") as excinfo:
        run_to_json(tmp_path, tsv, kind="datasets")
    message = str(excinfo.value)
    for col in PROVENANCE_COLUMNS:
        assert col in message, f"abort must name the expected set ({col})"


def test_ingest_aborts_on_partially_missing_provenance_columns(tmp_path):
    """Dropping exactly one provenance column (the subtle drift case)
    still aborts naming that column."""
    header_cols = (DATASETS_TSV_HEADER.strip().split("\t"))
    header_cols.remove("license")
    header = "\t".join(header_cols) + "\n"
    full_row = _datasets_row(1, "d1").strip().split("\t")
    # Remove the license cell (same position as in the header).
    license_idx = (DATASETS_TSV_HEADER.strip().split("\t")).index("license")
    del full_row[license_idx]
    tsv = header + "\t".join(full_row) + "\n"
    with pytest.raises(SystemExit, match="license"):
        run_to_json(tmp_path, tsv, kind="datasets")


def test_models_ingest_also_validates_expected_columns(tmp_path):
    """The wrong-count validation is family-general: a models CSV missing
    ``Tokenizer`` aborts too (unless the column arrives via ``--map``)."""
    tsv = ("Model_name\tModel_path\tModel_size\tMean_token_length\n"
           "a\tmodels/a\t5M\t6\n")
    with pytest.raises(SystemExit, match="Tokenizer"):
        run_to_json(tmp_path, tsv, kind="models")


def test_map_target_satisfies_expected_columns(tmp_path):
    """A CSV column renamed onto an expected name via ``--map`` satisfies
    the expected-columns check (the legacy-unification path keeps
    working): ``Tok`` maps to ``Tokenizer``."""
    tsv = ("Model_name\tModel_path\tModel_size\tTok\tMean_token_length\n"
           "a\tmodels/a\t5M\tBPE\t6\n")
    csv_path = tmp_path / "input.txt"
    csv_path.write_text(tsv, encoding="utf-8", newline="")
    out_path = tmp_path / "out.json"
    args = argparse.Namespace(
        to_json=True, to_csv=False, kind="models",
        input=str(csv_path), output=str(out_path),
        merge_existing=None,
        map=["Tok=Tokenizer"], numeric=[], columns=[], crlf=False,
        rename_name=[], derive_operational=False,
    )
    convert_registry.to_json(args, convert_registry.KIND_PRESETS["models"])
    result = json.loads(out_path.read_text(encoding="utf-8"))
    assert result["a"]["Tokenizer"] == "BPE"


def test_committed_datasets_registry_round_trips(tmp_path):
    """The real ``pipeline/datasets_info.json`` carries all six provenance
    columns across all entries and round-trips losslessly (the D-10
    guarantee the maintainer-edit surface depends on)."""
    registry_path = (Path(__file__).resolve().parents[1]
                     / "pipeline" / "datasets_info.json")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(registry) == 50
    for name, entry in registry.items():
        for col in PROVENANCE_COLUMNS:
            assert col in entry, f"{name} lacks {col}"
            assert entry[col], f"{name}.{col} is blank"
    csv_text = run_to_csv(tmp_path, registry)
    csv_path = tmp_path / "rt.csv"
    csv_path.write_text(csv_text, encoding="utf-8")
    out_path = tmp_path / "rt.json"
    args = argparse.Namespace(
        to_json=True, to_csv=False, kind="datasets",
        input=str(csv_path), output=str(out_path),
        merge_existing=str(registry_path),
        map=[], numeric=[], columns=[], crlf=False,
        rename_name=[], derive_operational=False,
    )
    convert_registry.to_json(args, convert_registry.KIND_PRESETS["datasets"])
    result = json.loads(out_path.read_text(encoding="utf-8"))
    assert result == registry
