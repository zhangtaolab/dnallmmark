"""
Tier-1 service tests for ``tui/services/custom_validation.py`` (Phase 9,
09-01 — the D-05 collect-all validator lane, full CUST-03 matrix).

Pinned decisions:

- **D-05 (collect-all, one pass):** ``validate_model_candidate`` /
  ``validate_dataset_candidate`` return EVERY problem as ordered
  ``(field_key, message)`` pairs in FIELD-DEFINITION order — a candidate
  with a colliding key AND a missing path AND a non-numeric size yields
  exactly 3 numbered problems, never the first only; ordering follows the
  declared field order (key → Model_path → size (M) → …), never dict
  iteration.
- **CUST-03 nine-check matrix:** required/non-empty key + name format;
  numeric type checks with bool excluded (Train/Dev/Test ints,
  size (M)/labels/length numerics); enum membership (dataset Category,
  dataset type, model type, species/tokenizer within the injected
  observed vocabularies, metric in the metric registry); key collision
  against official AND existing custom; path existence under the injected
  fs root; split-file parseability (train.csv/dev.csv/test.csv, utf-8
  csv.reader, non-empty header, header contains sequence AND the
  collected label column, malformed rows skipped like the audit kernel);
  row count > 0 per split with declared == well-formed count;
  label-column validity; metric-in-registry.
- **Metric single authority (IN-03 successor):** the frozen
  ``METRIC_REGISTRY`` (28 names — Pitfall 8: 28, not 27) equals
  ``export_runs.SUITE_CANONICAL`` element-for-element, proven by the
  parity test importing export_runs through the tests/conftest.py
  sys.path — the SERVICE module never imports it (script/ is not on the
  TUI bootstrap path; numpy top-level import).
- **Copy single home:** every problem message composes from
  ``tui/strings.py`` constants (WIZ_PROBLEM_* wordings) — the service
  module carries ZERO inline Chinese copy (source-scan locked).
- **Never raise on untrusted input:** wrong Python shapes (lists where
  strings expected, bools where ints expected, non-dict candidates) and
  non-UTF-8 CSVs yield problem lines, never exceptions.
- **A5:** huggingface/modelscope are non-empty free text — no URL syntax
  over-validation (official values are org/repo strings).

See also:
    ``tui/services/custom_validation.py`` — the validator under test.
    ``script/audit_n_frequencies.py`` ``audit_split`` — the CSV parse
    discipline mirrored here (the authoritative measurement stays the
    09-02 subprocess).
    ``tests/tui/test_services_custom_entries.py`` — the store + tracer lane.
"""

import re
from pathlib import Path

from tui import strings
from tui.services import custom_validation as cv

REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = REPO_ROOT / "pipeline"
CJK_RE = re.compile(r"[一-鿿]")


def write_split(dataset_dir, split, rows, header="sequence,label"):
    """Write one split CSV: header + one field per well-formed row."""
    lines = [header]
    lines.extend(f"ACGT,{value}" for value in rows)
    (dataset_dir / f"{split}.csv").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


# ===== Fixtures: tmp fs roots + real split CSVs (never the real home) =====


def make_model_fs(tmp_path):
    """A tmp fs root holding the fixture model dir."""
    root = tmp_path / "fsroot"
    (root / "models" / "my-custom-lm").mkdir(parents=True)
    return root


def make_dataset_fs(tmp_path):
    """A tmp fs root holding the fixture dataset dir with 3/2/2 rows."""
    root = tmp_path / "fsroot"
    dataset_dir = root / "datasets" / "MyCustom" / "demo_task"
    dataset_dir.mkdir(parents=True)
    write_split(dataset_dir, "train", [0, 1, 0])
    write_split(dataset_dir, "dev", [1, 0])
    write_split(dataset_dir, "test", [0, 1])
    return root


#: Synthetic observed vocabularies (the 09-04/09-05 screens build the
#: real ones from the registries; the validator only checks membership
#: in whatever is injected).
OBSERVED_SPECIES = ("plants", "animals", "microbe")
OBSERVED_TOKENIZERS = (
    "BPE", "6mer", "singlebase", "one-hot", "6-mer", "overlapped 6-mer",
)


def model_sources(
    fs_root,
    existing_custom_models=None,
    observed_species=OBSERVED_SPECIES,
    observed_tokenizers=OBSERVED_TOKENIZERS,
):
    """Synthetic sources with one official + one custom model key."""
    return cv.ValidationSources(
        fs_root=fs_root,
        official_model_keys=frozenset({"plant-dnabert-6mer"}),
        official_dataset_keys=frozenset({"GUE__emp_H3"}),
        existing_custom_models=(
            {"my-prev-lm": {"size (M)": 1}}
            if existing_custom_models is None else existing_custom_models
        ),
        existing_custom_datasets={},
        observed_species=observed_species,
        observed_tokenizers=observed_tokenizers,
    )


def dataset_sources(fs_root):
    """Synthetic sources with one official + one custom dataset key."""
    return cv.ValidationSources(
        fs_root=fs_root,
        official_model_keys=frozenset({"plant-dnabert-6mer"}),
        official_dataset_keys=frozenset({"GUE__emp_H3"}),
        existing_custom_models={},
        existing_custom_datasets={"MyPrev__task": {"labels": 2}},
        observed_species=OBSERVED_SPECIES,
        observed_tokenizers=OBSERVED_TOKENIZERS,
    )


def full_model_values(fs_root):
    """A full model candidate over an EXISTING tmp model dir (the
    operator-entered absolute-path form; land relativizes later)."""
    return {
        "key": "my-custom-lm",
        "Model_path": str(fs_root / "models" / "my-custom-lm"),
        "size (M)": 89,
        "species": "plants",
        "type": "MLM",
        "architecture": "Bert",
        "Tokenizer": "6mer",
        "context_len (bp)": 2000,
        "huggingface": "zhangtaolab/my-custom-lm",
        "modelscope": "zhangtaolab/my-custom-lm",
        "series": "PDLLMs",
        "quirks": {"no_safetensors": False, "fp32_only": False, "special_head": False},
    }


def full_dataset_values(fs_root):
    """A full dataset candidate over REAL tmp split CSVs (3/2/2 rows,
    declared counts equal to the well-formed counts)."""
    return {
        "key": "MyCustom__demo_task",
        "Dataset_path": str(fs_root / "datasets" / "MyCustom" / "demo_task"),
        "Category": "Plants",
        "label_column": "label",
        "Train": 3,
        "Dev": 2,
        "Test": 2,
        "labels": 2,
        "length": 512,
        "type": "binary",
        "metric": "f1",
        "citation": "synthetic",
        "source": "https://example.com",
        "license": "MIT",
        "preprocessing": "synthetic",
    }


# ===== Happy path: full candidates yield zero problems =====


def test_full_model_candidate_validates_with_zero_problems(tmp_path):
    fs = make_model_fs(tmp_path)
    problems = cv.validate_model_candidate(
        full_model_values(fs), model_sources(fs)
    )
    assert problems == []


def test_full_dataset_candidate_validates_with_zero_problems(tmp_path):
    fs = make_dataset_fs(tmp_path)
    problems = cv.validate_dataset_candidate(
        full_dataset_values(fs), dataset_sources(fs)
    )
    assert problems == []


def test_sources_default_to_empty_injections(tmp_path):
    """A bare ValidationSources validates clean candidates whose paths
    are absolute — every external fact is injected, none is fetched."""
    problems = cv.validate_model_candidate(
        full_model_values(make_model_fs(tmp_path)), cv.ValidationSources()
    )
    assert problems == []
    problems = cv.validate_dataset_candidate(
        full_dataset_values(make_dataset_fs(tmp_path)), cv.ValidationSources()
    )
    assert problems == []


# ===== Collect-all: every problem in one pass, field-definition order =====


def test_three_simultaneous_defects_yield_three_ordered_problems(tmp_path):
    """Colliding key + missing Model_path + non-numeric size -> exactly 3
    problems, in field-definition order (key, Model_path, size (M)),
    each carrying its field key."""
    fs = make_model_fs(tmp_path)
    values = full_model_values(fs)
    values["key"] = "plant-dnabert-6mer"   # official collision
    values["Model_path"] = ""              # required
    values["size (M)"] = "abc"             # numeric
    problems = cv.validate_model_candidate(values, model_sources(fs))
    assert len(problems) == 3
    keys = [field for field, _message in problems]
    assert keys == ["key", "Model_path", "size (M)"]


def test_dataset_collect_all_spans_all_required_fields(tmp_path):
    fs = make_dataset_fs(tmp_path)
    values = full_dataset_values(fs)
    for field in ("Dataset_path", "Category", "label_column", "labels",
                  "type", "metric"):
        values[field] = ""
    values["key"] = ""
    problems = cv.validate_dataset_candidate(values, dataset_sources(fs))
    keys = [field for field, _message in problems]
    assert keys == [
        "key", "Dataset_path", "Category", "label_column", "labels",
        "type", "metric",
    ]


def test_problems_follow_field_definition_order_not_dict_order(tmp_path):
    """A candidate whose dict inserts size before path still reports
    path first — ordering is the DECLARED field order."""
    fs = make_model_fs(tmp_path)
    values = {
        "size (M)": "abc",
        "Model_path": "",
        "key": "my-custom-lm",
        "type": "MLM",
        "Tokenizer": "6mer",
    }
    problems = cv.validate_model_candidate(values, model_sources(fs))
    keys = [field for field, _message in problems]
    assert keys == ["Model_path", "size (M)"]


# ===== Key checks: required, format, collisions =====


def test_key_collisions_official_and_custom_each_reported(tmp_path):
    fs = make_model_fs(tmp_path)
    sources = model_sources(fs)
    official_hit = dict(full_model_values(fs), key="plant-dnabert-6mer")
    problems = cv.validate_model_candidate(official_hit, sources)
    assert [field for field, _ in problems] == ["key"]
    assert "plant-dnabert-6mer" in problems[0][1]

    custom_hit = dict(full_model_values(fs), key="my-prev-lm")
    problems = cv.validate_model_candidate(custom_hit, sources)
    assert [field for field, _ in problems] == ["key"]
    assert "my-prev-lm" in problems[0][1]


def test_key_collision_check_covers_both_families_in_one_pass(tmp_path):
    """A key present in BOTH collision sets reports both problems (the
    same pass covers official AND existing custom)."""
    fs = make_model_fs(tmp_path)
    sources = model_sources(
        fs, existing_custom_models={"plant-dnabert-6mer": {"size (M)": 1}}
    )
    values = dict(full_model_values(fs), key="plant-dnabert-6mer")
    problems = cv.validate_model_candidate(values, sources)
    key_problems = [message for field, message in problems if field == "key"]
    assert key_problems == [
        strings.WIZ_PROBLEM_COLLISION_OFFICIAL.format(
            key="plant-dnabert-6mer"),
        strings.WIZ_PROBLEM_COLLISION_CUSTOM.format(
            key="plant-dnabert-6mer"),
    ]


def test_empty_or_whitespace_key_is_a_required_problem(tmp_path):
    fs = make_model_fs(tmp_path)
    for bad in ("", "   "):
        values = dict(full_model_values(fs), key=bad)
        problems = cv.validate_model_candidate(values, model_sources(fs))
        assert [field for field, _ in problems] == ["key"]
    values = dict(full_model_values(fs), key=None)
    problems = cv.validate_model_candidate(values, model_sources(fs))
    assert [field for field, _ in problems] == ["key"]


def test_key_with_path_separator_is_a_format_problem(tmp_path):
    fs = make_model_fs(tmp_path)
    values = dict(full_model_values(fs), key="evil/key")
    problems = cv.validate_model_candidate(values, model_sources(fs))
    assert [field for field, _ in problems] == ["key"]
    values = dict(full_model_values(fs), key="evil\\key")
    problems = cv.validate_model_candidate(values, model_sources(fs))
    assert [field for field, _ in problems] == ["key"]


# ===== Numeric checks (bool excluded, D-14) =====


def test_size_numeric_check_rejects_strings_and_bools(tmp_path):
    fs = make_model_fs(tmp_path)
    for bad in ("abc", True, False, [89]):
        values = dict(full_model_values(fs), **{"size (M)": bad})
        problems = cv.validate_model_candidate(values, model_sources(fs))
        assert [field for field, _ in problems] == ["size (M)"], bad
    for good in (89, 89.5, 0):
        values = dict(full_model_values(fs), **{"size (M)": good})
        assert cv.validate_model_candidate(values, model_sources(fs)) == []


def test_split_counts_are_int_strict_with_bool_excluded(tmp_path):
    """Train/Dev/Test accept ints only — floats and bools are problems;
    an ABSENT declaration is not (the split counting derives it)."""
    fs = make_dataset_fs(tmp_path)
    for bad in (3.5, True, "3", [3]):
        values = dict(full_dataset_values(fs), Train=bad)
        problems = cv.validate_dataset_candidate(values, dataset_sources(fs))
        assert [field for field, _ in problems] == ["Train"], bad
    absent = full_dataset_values(fs)
    del absent["Train"]
    assert cv.validate_dataset_candidate(absent, dataset_sources(fs)) == []


def test_labels_and_length_numeric_checks(tmp_path):
    fs = make_dataset_fs(tmp_path)
    for bad in ("2", True, None):
        values = dict(full_dataset_values(fs), labels=bad)
        problems = cv.validate_dataset_candidate(values, dataset_sources(fs))
        assert [field for field, _ in problems] == ["labels"], bad
    values = dict(full_dataset_values(fs), length="512")
    problems = cv.validate_dataset_candidate(values, dataset_sources(fs))
    assert [field for field, _ in problems] == ["length"]
    # Optional length may be absent entirely.
    absent = full_dataset_values(fs)
    del absent["length"]
    assert cv.validate_dataset_candidate(absent, dataset_sources(fs)) == []


# ===== Enum membership (CUST-03 check 3) =====


def test_dataset_category_enum_outside_observed_values(tmp_path):
    fs = make_dataset_fs(tmp_path)
    values = dict(full_dataset_values(fs), Category="Fungi")
    problems = cv.validate_dataset_candidate(values, dataset_sources(fs))
    assert [field for field, _ in problems] == ["Category"]
    assert problems[0][1] == strings.WIZ_PROBLEM_ENUM.format(
        value="Fungi", allowed=", ".join(cv.DATASET_CATEGORY_VALUES)
    )


def test_dataset_type_enum_outside_task_types(tmp_path):
    fs = make_dataset_fs(tmp_path)
    values = dict(full_dataset_values(fs), type="quaternary")
    problems = cv.validate_dataset_candidate(values, dataset_sources(fs))
    assert [field for field, _ in problems] == ["type"]
    for good in ("binary", "multiclass", "regression", "multilabel"):
        values = dict(full_dataset_values(fs), type=good)
        assert cv.validate_dataset_candidate(
            values, dataset_sources(fs)
        ) == [], good


def test_model_type_enum_outside_mlm_clm_dl(tmp_path):
    fs = make_model_fs(tmp_path)
    values = dict(full_model_values(fs), type="RNN")
    problems = cv.validate_model_candidate(values, model_sources(fs))
    assert [field for field, _ in problems] == ["type"]
    for good in ("MLM", "CLM", "DL"):
        values = dict(full_model_values(fs), type=good)
        assert cv.validate_model_candidate(
            values, model_sources(fs)
        ) == [], good


def test_species_membership_against_injected_vocabulary(tmp_path):
    """species is OPTIONAL (blank allowed) but when filled must be within
    the injected observed vocabulary."""
    fs = make_model_fs(tmp_path)
    values = dict(full_model_values(fs), species="fungi")
    problems = cv.validate_model_candidate(values, model_sources(fs))
    assert [field for field, _ in problems] == ["species"]
    values = dict(full_model_values(fs), species="")
    assert cv.validate_model_candidate(values, model_sources(fs)) == []


def test_tokenizer_membership_against_injected_vocabulary(tmp_path):
    fs = make_model_fs(tmp_path)
    values = dict(full_model_values(fs), Tokenizer="8mer")
    problems = cv.validate_model_candidate(values, model_sources(fs))
    assert [field for field, _ in problems] == ["Tokenizer"]


def test_enum_membership_skipped_when_vocabulary_not_injected(tmp_path):
    """An empty injected vocabulary means 'nothing to check against' —
    species/tokenizer never fail on a partially-built source set."""
    fs = make_model_fs(tmp_path)
    sources = model_sources(fs, observed_species=(), observed_tokenizers=())
    values = dict(full_model_values(fs), species="anything", Tokenizer="whatever")
    problems = cv.validate_model_candidate(values, sources)
    assert [field for field, _ in problems if field in ("species", "Tokenizer")] == []


def test_metric_outside_registry_is_a_problem(tmp_path):
    fs = make_dataset_fs(tmp_path)
    values = dict(full_dataset_values(fs), metric="bleu")
    problems = cv.validate_dataset_candidate(values, dataset_sources(fs))
    assert [field for field, _ in problems] == ["metric"]


def test_huggingface_modelscope_accept_free_text(tmp_path):
    """A5: org/repo-shaped free text, no URL syntax over-validation."""
    fs = make_model_fs(tmp_path)
    for value in ("org/repo", "not a url at all", "https://x.y/z", "我的模型"):
        values = dict(full_model_values(fs), huggingface=value, modelscope=value)
        problems = cv.validate_model_candidate(values, model_sources(fs))
        assert problems == [], value


# ===== Path existence under the injected fs root (CUST-03 check 5) =====


def test_model_path_missing_is_a_problem(tmp_path):
    fs = make_model_fs(tmp_path)
    ghost = str(fs / "models" / "ghost")
    values = dict(full_model_values(fs), Model_path=ghost)
    problems = cv.validate_model_candidate(values, model_sources(fs))
    assert problems == [
        ("Model_path", strings.WIZ_PROBLEM_PATH_MISSING.format(path=ghost))
    ]


def test_relative_paths_resolve_against_the_injected_fs_root(tmp_path):
    """Relative Model_path/Dataset_path resolve under fs_root — present
    dirs validate; missing dirs yield the path problem."""
    fs = make_model_fs(tmp_path)
    values = full_model_values(fs)
    values["Model_path"] = "models/my-custom-lm"  # relative, exists
    assert cv.validate_model_candidate(values, model_sources(fs)) == []
    values["Model_path"] = "models/ghost"
    problems = cv.validate_model_candidate(values, model_sources(fs))
    assert [field for field, _ in problems] == ["Model_path"]


def test_dataset_path_missing_is_a_problem_and_splits_subsumed(tmp_path):
    """A missing dataset dir yields ONE path problem (the split checks
    are subsumed — no triple file-not-found noise)."""
    fs = make_dataset_fs(tmp_path)
    ghost = str(fs / "datasets" / "Ghost" / "task")
    values = dict(full_dataset_values(fs), Dataset_path=ghost)
    problems = cv.validate_dataset_candidate(values, dataset_sources(fs))
    assert [field for field, _ in problems] == ["Dataset_path"]


# ===== Split-file checks (CUST-03 checks 6/7/8 — audit-kernel mirror) =====


def test_valid_split_files_validate_with_declared_counts(tmp_path):
    fs = make_dataset_fs(tmp_path)
    assert cv.validate_dataset_candidate(
        full_dataset_values(fs), dataset_sources(fs)
    ) == []


def test_zero_data_row_split_yields_row_count_problem(tmp_path):
    fs = make_dataset_fs(tmp_path)
    dataset_dir = fs / "datasets" / "MyCustom" / "demo_task"
    write_split(dataset_dir, "dev", [])  # header only, zero data rows
    values = dict(full_dataset_values(fs), Dev=0)
    problems = cv.validate_dataset_candidate(values, dataset_sources(fs))
    assert [field for field, _ in problems] == ["Dev"]
    assert "0" in problems[0][1]  # the zero-row count is in the message


def test_header_lacking_sequence_yields_parseability_problem(tmp_path):
    fs = make_dataset_fs(tmp_path)
    dataset_dir = fs / "datasets" / "MyCustom" / "demo_task"
    write_split(dataset_dir, "train", [0, 1, 0], header="seq,label")
    problems = cv.validate_dataset_candidate(
        full_dataset_values(fs), dataset_sources(fs)
    )
    assert [field for field, _ in problems] == ["Train"]
    assert "sequence" in problems[0][1]


def test_header_lacking_label_column_yields_parseability_problem(tmp_path):
    fs = make_dataset_fs(tmp_path)
    dataset_dir = fs / "datasets" / "MyCustom" / "demo_task"
    write_split(dataset_dir, "train", [0, 1, 0], header="sequence,y")
    problems = cv.validate_dataset_candidate(
        full_dataset_values(fs), dataset_sources(fs)
    )
    assert [field for field, _ in problems] == ["Train"]
    assert "label" in problems[0][1]


def test_empty_headerless_split_file_yields_parseability_problem(tmp_path):
    fs = make_dataset_fs(tmp_path)
    dataset_dir = fs / "datasets" / "MyCustom" / "demo_task"
    (dataset_dir / "test.csv").write_text("", encoding="utf-8")
    problems = cv.validate_dataset_candidate(
        full_dataset_values(fs), dataset_sources(fs)
    )
    assert [field for field, _ in problems] == ["Test"]


def test_missing_split_file_yields_parseability_problem(tmp_path):
    fs = make_dataset_fs(tmp_path)
    dataset_dir = fs / "datasets" / "MyCustom" / "demo_task"
    (dataset_dir / "test.csv").unlink()
    problems = cv.validate_dataset_candidate(
        full_dataset_values(fs), dataset_sources(fs)
    )
    assert [field for field, _ in problems] == ["Test"]


def test_malformed_rows_are_skipped_not_fatal(tmp_path):
    """Rows whose field count differs from the header are skipped (not
    counted, not fatal) — exactly the audit kernel discipline."""
    fs = make_dataset_fs(tmp_path)
    dataset_dir = fs / "datasets" / "MyCustom" / "demo_task"
    (dataset_dir / "train.csv").write_text(
        "sequence,label\nACGT,0\nBAD\nACGT,1\nACGT,0\n", encoding="utf-8"
    )
    # 3 well-formed rows (BAD skipped); declared Train=3 validates.
    assert cv.validate_dataset_candidate(
        full_dataset_values(fs), dataset_sources(fs)
    ) == []


def test_declared_count_mismatching_measured_rows_is_a_problem(tmp_path):
    fs = make_dataset_fs(tmp_path)
    values = dict(full_dataset_values(fs), Train=5)  # counted: 3
    problems = cv.validate_dataset_candidate(values, dataset_sources(fs))
    assert [field for field, _ in problems] == ["Train"]
    assert problems[0][1] == strings.WIZ_PROBLEM_SPLIT_COUNT_MISMATCH.format(
        declared=5, counted=3
    )


# ===== Encoding edges =====


def test_non_utf8_csv_yields_problem_line_not_exception(tmp_path):
    fs = make_dataset_fs(tmp_path)
    dataset_dir = fs / "datasets" / "MyCustom" / "demo_task"
    (dataset_dir / "train.csv").write_bytes(b"sequence,label\nACGT,\xff\n")
    problems = cv.validate_dataset_candidate(
        full_dataset_values(fs), dataset_sources(fs)
    )
    assert [field for field, _ in problems] == ["Train"]


def test_cjk_label_column_name_validates(tmp_path):
    fs = make_dataset_fs(tmp_path)
    dataset_dir = fs / "datasets" / "MyCustom" / "demo_task"
    for split in ("train", "dev", "test"):
        write_split(dataset_dir, split, [0, 1], header="sequence,标签")
    values = full_dataset_values(fs)
    values["label_column"] = "标签"
    values["Train"] = 2
    values["Dev"] = 2
    values["Test"] = 2
    assert cv.validate_dataset_candidate(values, dataset_sources(fs)) == []


# ===== Metric registry: the 28-name SUITE_CANONICAL twin (Pitfall 8) =====


def test_metric_registry_parity_with_suite_canonical():
    """The frozen constant equals export_runs.SUITE_CANONICAL
    element-for-element — 28 names, not 27 (Pitfall 8). The parity test
    imports export_runs through the tests/conftest.py sys.path; the
    SERVICE module never imports it."""
    import export_runs  # script/ on sys.path (tests/conftest.py) — test lane only

    assert cv.METRIC_REGISTRY == export_runs.SUITE_CANONICAL
    assert len(cv.METRIC_REGISTRY) == 28


def test_metric_registry_carries_verbatim_spot_names():
    assert "AUROC_ovr" in cv.METRIC_REGISTRY
    assert "spearmanr" in cv.METRIC_REGISTRY
    assert "accuracy" in cv.METRIC_REGISTRY
    assert "matthews_correlation" in cv.METRIC_REGISTRY


def test_service_module_never_imports_export_runs():
    """Runtime import of export_runs is impossible from the TUI (numpy
    top-level import; script/ not on the bootstrap path) — the module
    carries ZERO import statements reaching it (AST-walked, the
    import-lock discipline; documentation mentions stay legal)."""
    import ast

    source = Path(cv.__file__).read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert name.split(".")[0] != "export_runs", (
                f"import at line {getattr(node, 'lineno', '?')}"
            )


# ===== Untrusted input: problems, never exceptions =====


def test_non_dict_candidates_yield_problems_never_raise(tmp_path):
    fs = make_model_fs(tmp_path)
    for bad in (None, ["a", "b"], "just-a-string", 42):
        problems = cv.validate_model_candidate(bad, model_sources(fs))
        assert isinstance(problems, list) and len(problems) == 1
        assert problems[0][0] == "key"
        problems = cv.validate_dataset_candidate(bad, dataset_sources(fs))
        assert isinstance(problems, list) and len(problems) == 1


def test_wrong_python_shapes_yield_problems_never_raise(tmp_path):
    """Lists where strings expected, bools where ints expected — every
    combination collects problems without raising."""
    fs = make_model_fs(tmp_path)
    values = full_model_values(fs)
    values["Model_path"] = ["not", "a", "string"]
    values["size (M)"] = True
    values["key"] = {"nested": "dict"}
    problems = cv.validate_model_candidate(values, model_sources(fs))
    assert isinstance(problems, list) and len(problems) >= 2
    keys = [field for field, _ in problems]
    assert keys[0] == "key"


def test_none_sources_defaults_to_empty_injections(tmp_path):
    """A None data_sources degrades to the empty namespace — the pure
    function never dereferences a missing argument."""
    problems = cv.validate_model_candidate(
        full_model_values(make_model_fs(tmp_path)), None
    )
    assert problems == []


# ===== Copy single home: messages come from tui/strings.py only =====


def test_service_module_carries_zero_inline_chinese_copy():
    source = Path(cv.__file__).read_text(encoding="utf-8")
    assert not CJK_RE.search(source), "inline Chinese copy in the service"


def test_problem_wordings_compose_from_strings_constants(tmp_path):
    """The collision / path-missing / needs-numeric wordings are the
    UI-SPEC Copywriting rows verbatim, via strings constants."""
    fs = make_model_fs(tmp_path)
    values = dict(full_model_values(fs), key="plant-dnabert-6mer")
    problems = cv.validate_model_candidate(values, model_sources(fs))
    assert problems == [
        ("key", strings.WIZ_PROBLEM_COLLISION_OFFICIAL.format(
            key="plant-dnabert-6mer"))
    ]
    ghost = str(fs / "models" / "ghost")
    values = dict(full_model_values(fs), Model_path=ghost)
    problems = cv.validate_model_candidate(values, model_sources(fs))
    assert problems == [
        ("Model_path", strings.WIZ_PROBLEM_PATH_MISSING.format(path=ghost))
    ]
    values = dict(full_model_values(fs), **{"size (M)": "abc"})
    problems = cv.validate_model_candidate(values, model_sources(fs))
    assert problems == [
        ("size (M)", strings.WIZ_PROBLEM_NEEDS_NUMERIC.format(value="abc"))
    ]


# ===== Field-order contracts (the D-05 emission order) =====


def test_field_order_constants_match_the_wizard_step_order():
    assert cv.MODEL_FIELD_ORDER[:3] == ("key", "Model_path", "size (M)")
    assert cv.DATASET_FIELD_ORDER[:3] == ("key", "Dataset_path", "Category")
    # Train/Dev/Test sit with the data-file fields, before type/metric.
    dataset_fields = list(cv.DATASET_FIELD_ORDER)
    assert dataset_fields.index("Train") < dataset_fields.index("type")
    assert dataset_fields.index("Test") < dataset_fields.index("metric")
    # The default fs root is the pipeline dir (tests override).
    assert cv.ValidationSources().fs_root == PIPELINE_DIR
