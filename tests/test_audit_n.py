"""
Unit tests for ``script/audit_n_frequencies.py`` (F7 / REV-07).

Every behavior bullet of the plan's Task 1 is pinned here over synthetic
CSV fixtures (the ``tests/test_dev_splits.py`` style — no real dataset
under ``pipeline/datasets/`` is touched):

- **N-census + charset classes** — non-ACGT characters (outside
  ``ACGTacgt``, ``|`` separator excluded) are counted per split with a
  per-character breakdown; strict (``ACGTacgt|``) survivors exclude
  N-containing rows (uppercased — lowercase ``n`` included), N-tolerant
  (``ACGTNacgtn|``) survivors keep them; other characters (e.g. ``X``)
  are rejected by BOTH classes;
- **length window** — the boundary row (exactly 10010 chars) survives,
  the over-length row (10011) is dropped from both classes but still
  counted in the row/char census;
- **malformed-row skip** — a wrong-field-count row prints a ``[Skip]``
  line and is never counted (untrusted-data discipline);
- **missing dataset dir** — explicit missing row + WARNING naming the
  task (the 7 GUE tasks are visible, never blank), and no subset entry;
- **min-over-model-classes** — unified eval N = min(strict, tolerant)
  test-survivor counts;
- **every emitted ID survives** — each subset ID passes an independent
  oracle of the pipeline's filter semantics, the list is sorted
  ascending, and its length equals the unified N;
- **artifact contracts** — the CSV header row, the missing-task CSV
  rows, the eval_subsets.json shape (parseable, ascending IDs), the
  DATA.md one-row-per-registry-task table, schema validation of the
  emitted JSON, and byte-identical re-emission (determinism).

See also:
    - ``script/audit_n_frequencies.py`` — the audit under test.
    - ``tests/test_schemas.py`` — the committed-artifact schema bucket.
"""

import csv
import json
from pathlib import Path

import audit_n_frequencies  # conftest puts script/ on sys.path
from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO / "schemas" / "n_audit.json"


def oracle_survives(seq, valid_chars):
    """Independent oracle of the pipeline filter semantics
    (run_finetune.py:832-839 / suite check_sequence @483a35c):
    ``set(seq.upper())`` within the class charset AND ``len <= 10010``
    (``minl=0`` can never reject)."""
    return (
        len(seq) <= audit_n_frequencies.MAX_LENGTH
        and set(seq.upper()) <= set(valid_chars)
    )


def write_split(task_dir, split, seqs):
    """Write a synthetic 2-column split CSV (sequence,label)."""
    lines = ["sequence,label"]
    for i, seq in enumerate(seqs):
        lines.append(f"{seq},{i % 2}")
    (task_dir / f"{split}.csv").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")


def make_registry_entry(path):
    """Build a unified-registry dataset entry fixture."""
    return {
        "Index": 1, "Dataset_name": path.split("/")[-1],
        "Dataset_path": path, "Train": 0, "Dev": 0, "Test": 0,
        "type": "binary", "labels": 2, "length": 500, "metric": "f1",
        "Category": "Microbe",
    }


def build_task(root, rel, splits):
    """Materialize a synthetic task dir under ``root/rel``."""
    task_dir = root / rel
    task_dir.mkdir(parents=True)
    for split, seqs in splits.items():
        write_split(task_dir, split, seqs)
    return task_dir


def run_audit(registry, root, out):
    """Drive audit_registry + write_artifacts into ``out``."""
    tasks, subsets = audit_n_frequencies.audit_registry(registry, root)
    paths = audit_n_frequencies.write_artifacts(
        tasks, subsets, out / "data", out / "eval_subsets.json",
        out / "DATA.md",
    )
    return tasks, subsets, paths


# ===== census + charset classes =====


def test_n_census_and_charset_classes(tmp_path):
    """Non-ACGT chars counted per char; strict drops N rows (any case),
    N-tolerant keeps them, other chars drop from both; lowercase acgt is
    clean ACGT and never counted non-ACGT."""
    seqs = ["ACGT", "acgt", "ACGTN", "nn", "ACGTX"]
    build_task(tmp_path, "GUE/emp_H3", {"test": seqs})
    registry = {"GUE__emp_H3": make_registry_entry("datasets/GUE/emp_H3")}
    tasks, _subsets, _paths = run_audit(registry, tmp_path, tmp_path / "out")
    stats = tasks["GUE__emp_H3"]["splits"]["test"]
    assert stats["rows"] == 5
    # non-ACGT: N(1) + n,n(2) + X(1) = 4 over 3 rows; a/c/g/t clean
    assert stats["non_acgt_chars"] == 4
    assert stats["rows_with_non_acgt"] == 3
    assert stats["by_char"] == {"N": 1, "n": 2, "X": 1}
    # strict (uppercased membership in ACGTacgt|): rows 0,1 only
    assert stats["strict_survivors"] == 2
    # N-tolerant: rows 0,1,2,3 (X still rejected)
    assert stats["n_tolerant_survivors"] == 4


def test_pipe_separator_excluded_from_non_acgt(tmp_path):
    """The '|' pair separator (GUE__EPI_GM12878 seq_sep) is excluded
    from the non-ACGT census and survives both charsets."""
    build_task(tmp_path, "GUE/EPI", {"test": ["ACGT|TGCA"]})
    registry = {"T": make_registry_entry("datasets/GUE/EPI")}
    tasks, _subsets, _paths = run_audit(registry, tmp_path, tmp_path / "out")
    stats = tasks["T"]["splits"]["test"]
    assert stats["non_acgt_chars"] == 0
    assert stats["rows_with_non_acgt"] == 0
    assert stats["by_char"] == {}
    assert stats["strict_survivors"] == 1
    assert stats["n_tolerant_survivors"] == 1


def test_length_window_boundary(tmp_path):
    """Exactly 10010 chars survives both classes (suite: only > maxl
    rejects); 10011 drops from both but stays in the row/char census."""
    seqs = ["A" * 10010, "A" * 10011]
    build_task(tmp_path, "GUE/len", {"test": seqs})
    registry = {"T": make_registry_entry("datasets/GUE/len")}
    tasks, _subsets, _paths = run_audit(registry, tmp_path, tmp_path / "out")
    stats = tasks["T"]["splits"]["test"]
    assert stats["rows"] == 2
    assert stats["total_chars"] == 10010 + 10011
    assert stats["strict_survivors"] == 1
    assert stats["n_tolerant_survivors"] == 1


# ===== untrusted-data discipline =====


def test_malformed_row_skipped_and_warned(tmp_path, capsys):
    """A wrong-field-count row prints a [Skip] line naming the task and
    is never counted anywhere."""
    task_dir = build_task(tmp_path, "GUE/mal", {})
    content = "sequence,label\nACGT,0\nBROKEN-ROW\nACGT,1\n"
    (task_dir / "test.csv").write_text(content, encoding="utf-8")
    registry = {"T": make_registry_entry("datasets/GUE/mal")}
    tasks, _subsets, _paths = run_audit(registry, tmp_path, tmp_path / "out")
    stats = tasks["T"]["splits"]["test"]
    assert stats["rows"] == 2  # the malformed row never counted
    captured = capsys.readouterr()
    assert "[Skip]" in captured.out
    assert "T/test" in captured.out


def test_missing_dir_reported_as_missing_with_warning(tmp_path, capsys):
    """A registry task without an on-disk dir is an explicit missing row
    with a WARNING naming it — never a silent absence or zero-filled
    counts — and gets no subset entry."""
    build_task(tmp_path, "GUE/here", {"test": ["ACGT"]})
    registry = {
        "PRESENT": make_registry_entry("datasets/GUE/here"),
        "GUE__virus_covid": make_registry_entry("datasets/GUE/absent"),
    }
    tasks, subsets, _paths = run_audit(registry, tmp_path, tmp_path / "out")
    assert tasks["GUE__virus_covid"]["missing"] is True
    assert tasks["GUE__virus_covid"]["unified_eval_n"] is None
    assert tasks["GUE__virus_covid"]["splits"] is None
    assert "GUE__virus_covid" not in subsets
    captured = capsys.readouterr()
    assert "WARNING GUE__virus_covid" in captured.out
    # the present neighbor is unaffected
    assert tasks["PRESENT"]["missing"] is False
    assert tasks["PRESENT"]["unified_eval_n"] == 1


# ===== unified N + subset IDs =====


def test_unified_n_is_min_over_model_classes(tmp_path):
    """unified_eval_n = min(strict, tolerant) test survivors — the
    strictest class governs; with no N rows both classes equal rows."""
    build_task(tmp_path, "GUE/nrows", {"test": ["ACGT"] * 4 + ["ACGTN", "NN"]})
    build_task(tmp_path, "GUE/clean", {"test": ["ACGT"] * 3})
    registry = {
        "WITH_N": make_registry_entry("datasets/GUE/nrows"),
        "CLEAN": make_registry_entry("datasets/GUE/clean"),
    }
    tasks, subsets, _paths = run_audit(registry, tmp_path, tmp_path / "out")
    assert tasks["WITH_N"]["unified_eval_n"] == 4  # min(4, 6)
    assert tasks["CLEAN"]["unified_eval_n"] == 3   # min(3, 3)
    assert len(subsets["WITH_N"]) == 4
    assert len(subsets["CLEAN"]) == 3


def test_emitted_ids_survive_common_filter_and_are_first_n(tmp_path):
    """Every emitted subset ID passes an independent oracle of the
    pipeline filter; IDs are ascending file order; the list is the
    first N strict survivors; train/dev rows never enter the map."""
    test_seqs = [
        "ACGT", "ACGTN", "TGCA", "nn", "AAAA", "ACGTX", "CCCC",
    ]
    build_task(tmp_path, "GUE/mix", {
        "train": ["ACGT"] * 5,
        "dev": ["ACGTN"],       # N in dev must not affect the subset
        "test": test_seqs,
    })
    registry = {"T": make_registry_entry("datasets/GUE/mix")}
    tasks, subsets, _paths = run_audit(registry, tmp_path, tmp_path / "out")
    ids = subsets["T"]
    expected_strict = [
        i for i, seq in enumerate(test_seqs)
        if oracle_survives(seq, "ACGTacgt|")
    ]
    unified = tasks["T"]["unified_eval_n"]
    assert ids == expected_strict[:unified]
    assert ids == sorted(ids)
    # independent oracle: every emitted ID itself survives
    for row_id in ids:
        assert oracle_survives(test_seqs[row_id], "ACGTacgt|")


# ===== artifact contracts =====


def test_csv_header_and_rows(tmp_path):
    """The CSV carries the exact header row; present tasks get one row
    per split, missing tasks one row with missing=true and empty
    counts (never zeros that would read as measured)."""
    build_task(tmp_path, "GUE/csv", {"train": ["ACGT"], "test": ["ACGT"]})
    registry = {
        "P": make_registry_entry("datasets/GUE/csv"),
        "M": make_registry_entry("datasets/GUE/none"),
    }
    _tasks, _subsets, _paths = run_audit(registry, tmp_path, tmp_path / "out")
    with open(tmp_path / "out" / "data" / "n_audit.csv",
              encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == audit_n_frequencies.CSV_HEADER
    body = {row[0]: row for row in rows[1:]}
    assert set(body) == {"P", "M"}
    assert [row[1] for row in rows[1:] if row[0] == "P"] == [
        "train", "test",
    ]
    missing_row = body["M"]
    assert missing_row[2] == "true"
    assert missing_row[3:9] == [""] * 6  # counts empty, not zero
    for row in rows[1:]:
        if row[0] == "P":
            assert row[2] == "false"
            assert row[3] == "1"


def test_subsets_json_shape(tmp_path):
    """eval_subsets.json parses as the pure task -> ID-list map with
    ascending lists (the exact --subset_file input shape)."""
    build_task(tmp_path, "GUE/sub", {
        "test": ["ACGT", "ACGTN", "TGCA", "GGGG"],
    })
    registry = {"T": make_registry_entry("datasets/GUE/sub")}
    _tasks, _subsets, _paths = run_audit(registry, tmp_path, tmp_path / "out")
    loaded = json.loads(
        (tmp_path / "out" / "eval_subsets.json").read_text(encoding="utf-8"))
    assert loaded == {"T": [0, 2, 3]}
    assert all(
        isinstance(v, list) and v == sorted(v) for v in loaded.values()
    )


def test_emitted_json_validates_schema(tmp_path):
    """The fixture-produced n_audit.json validates against the strict
    schemas/n_audit.json contract (present + missing tasks covered)."""
    build_task(tmp_path, "GUE/v", {"test": ["ACGT", "ACGTN"]})
    registry = {
        "P": make_registry_entry("datasets/GUE/v"),
        "M": make_registry_entry("datasets/GUE/absent"),
    }
    _tasks, _subsets, _paths = run_audit(registry, tmp_path, tmp_path / "out")
    doc = json.loads(
        (tmp_path / "out" / "data" / "n_audit.json").read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema).iter_errors(doc))
    assert not errors, "\n".join(e.message for e in errors)


def test_data_md_row_per_registry_task(tmp_path):
    """DATA.md carries one table row per registry task, missing tasks
    included (visibly marked, never blank)."""
    build_task(tmp_path, "GUE/md", {"test": ["ACGT"]})
    registry = {
        "PRESENT_TASK": make_registry_entry("datasets/GUE/md"),
        "MISSING_TASK": make_registry_entry("datasets/GUE/gone"),
    }
    _tasks, _subsets, _paths = run_audit(registry, tmp_path, tmp_path / "out")
    text = (tmp_path / "out" / "DATA.md").read_text(encoding="utf-8")
    table_rows = [
        line for line in text.splitlines()
        if line.startswith(("| PRESENT_TASK ", "| MISSING_TASK "))
    ]
    assert len(table_rows) == 2
    missing_line = next(
        line for line in table_rows if line.startswith("| MISSING_TASK"))
    assert "missing" in missing_line


def test_deterministic_byte_identical_emission(tmp_path):
    """Two audits over the same fixtures emit byte-identical artifacts
    (sorted iteration + sort_keys + no clock)."""
    build_task(tmp_path, "GUE/det", {
        "train": ["ACGT", "ACGTN"], "test": ["ACGT", "NN", "TGCA"],
    })
    registry = {
        "T": make_registry_entry("datasets/GUE/det"),
        "M": make_registry_entry("datasets/GUE/gone"),
    }
    _t1, _s1, paths1 = run_audit(registry, tmp_path, tmp_path / "out1")
    _t2, _s2, paths2 = run_audit(registry, tmp_path, tmp_path / "out2")
    for p1, p2 in zip(paths1, paths2, strict=True):
        assert p1.read_bytes() == p2.read_bytes(), p1.name
