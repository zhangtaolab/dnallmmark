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

import pytest

import convert_registry  # conftest puts script/ on sys.path

MODELS_TSV_HEADER = ("Model_name\tModel_path\tModel_size\tTokenizer"
                     "\tMean_token_length\n")
DATASETS_TSV_HEADER = ("Index\tDataset_name\tDataset_path\tTrain\tTest\tDev"
                       "\ttype\tlabels\tlength\tmetric\tCategory\n")


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
              + "1\td1\tdatasets/d1\t100\t10\t0\tbinary\t2\t500\tf1\tPlants\n"
                "2\td2\tdatasets/d2\t50\t5\t\tbinary\t2\t500\tf1\tPlants\n")
    result = run_to_json(tmp_path, tsv_ds, kind="datasets")
    assert result["d1"]["Dev"] == 0  # numeric cell coerced
    assert result["d1"]["Train"] == 100
    assert result["d2"]["Dev"] == ""  # empty cell stays a string


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
              + "1\td1\tdatasets/d1\t100\t10\t0\tbinary\t2\t500\tf1\tPlants\n")
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
           + "7\tgene_exp.x\tdatasets/suite/gene_exp.x\t100\t10\t0"
             "\tbinary\t2\t500\tspearman\tPlants\n")
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
           + "7\tgene_exp.x\tdatasets/suite/gene_exp.x\t100\t10\t0"
             "\tbinary\t2\t500\tspearman\tPlants\n"
             "8\tsuite__gene_exp.x\tdatasets/suite/gene_exp.x\t100\t10\t0"
             "\tbinary\t2\t500\tspearman\tPlants\n")
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
    with pytest.raises(SystemExit, match="models"):
        run_to_json(tmp_path, tsv, kind="datasets", derive_operational=True)
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
