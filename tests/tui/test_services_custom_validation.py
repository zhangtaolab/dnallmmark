"""
Tier-1 service tests for ``tui/services/custom_validation.py`` (Phase 9,
09-01 — the D-05 collect-all validator lane).

Pinned decisions:

- **D-05 (collect-all, one pass):** ``validate_model_candidate`` /
  ``validate_dataset_candidate`` return EVERY problem as ordered
  ``(field_key, message)`` pairs in FIELD-DEFINITION order — a candidate
  with a colliding key AND a missing path AND a non-numeric size yields
  exactly 3 numbered problems, never the first only; ordering follows the
  declared field order (key → Model_path → size (M) → …), never dict
  iteration.
- **Never raise on untrusted input:** wrong Python shapes (lists where
  strings expected, bools where ints expected, non-dict candidates) yield
  problems, never exceptions.
- **CUST-03 collision families:** the key check covers official AND
  existing-custom collisions in the same pass, each naming the key.
- **D-14 (bool exclusion):** bool is a subclass of int — every numeric
  check excludes it before the isinstance test.
- **Injected sources (D-05):** every test builds ``ValidationSources``
  from synthetic sets / tmp roots — the validator never reads the real
  registries or the real home itself.

Scope (09-01 task split): this lane lands with the required /
key-collision / numeric checks; the enum, path-existence, split-file,
label-column, and metric-registry matrix (and the SUITE_CANONICAL parity
test) land with the follow-up tasks in this plan.

See also:
    ``tui/services/custom_validation.py`` — the validator under test.
    ``tests/tui/test_services_custom_entries.py`` — the store + tracer lane.
    ``tests/tui/test_services_templates.py`` — the collect-all precedent.
"""

from pathlib import Path

from tui.services import custom_validation as cv

REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = REPO_ROOT / "pipeline"


def model_sources(**overrides):
    """Synthetic sources with one official and one custom model key."""
    base = {
        "official_model_keys": frozenset({"plant-dnabert-6mer"}),
        "official_dataset_keys": frozenset({"GUE__emp_H3"}),
        "existing_custom_models": {"my-prev-lm": {"size (M)": 1}},
        "existing_custom_datasets": {},
    }
    base.update(overrides)
    return cv.ValidationSources(**base)


def dataset_sources(**overrides):
    """Synthetic sources with one official and one custom dataset key."""
    base = {
        "official_model_keys": frozenset({"plant-dnabert-6mer"}),
        "official_dataset_keys": frozenset({"GUE__emp_H3"}),
        "existing_custom_models": {},
        "existing_custom_datasets": {"MyPrev__task": {"labels": 2}},
    }
    base.update(overrides)
    return cv.ValidationSources(**base)


def full_model_values():
    """A full model candidate exercising every field, all valid."""
    return {
        "key": "my-custom-lm",
        "Model_path": "models/my-custom-lm",
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


def full_dataset_values():
    """A full dataset candidate exercising every field, all valid."""
    return {
        "key": "MyCustom__demo_task",
        "Dataset_path": "datasets/MyCustom/demo_task",
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


def test_full_model_candidate_validates_with_zero_problems():
    problems = cv.validate_model_candidate(full_model_values(), model_sources())
    assert problems == []


def test_full_dataset_candidate_validates_with_zero_problems():
    problems = cv.validate_dataset_candidate(
        full_dataset_values(), dataset_sources()
    )
    assert problems == []


def test_sources_default_to_empty_injections():
    """A bare ValidationSources validates a clean candidate — every
    external fact is injected, none is fetched."""
    problems = cv.validate_model_candidate(full_model_values(), cv.ValidationSources())
    assert problems == []
    problems = cv.validate_dataset_candidate(
        full_dataset_values(), cv.ValidationSources()
    )
    assert problems == []


# ===== Collect-all: every problem in one pass, field-definition order =====


def test_three_simultaneous_defects_yield_three_ordered_problems():
    """Colliding key + missing Model_path + non-numeric size -> exactly 3
    problems, in field-definition order (key, Model_path, size (M))."""
    values = full_model_values()
    values["key"] = "plant-dnabert-6mer"   # official collision
    values["Model_path"] = ""              # required
    values["size (M)"] = "abc"             # numeric
    problems = cv.validate_model_candidate(values, model_sources())
    assert len(problems) == 3
    keys = [field for field, _message in problems]
    assert keys == ["key", "Model_path", "size (M)"]


def test_dataset_collect_all_spans_all_required_fields():
    values = full_dataset_values()
    for field in ("Dataset_path", "Category", "labels", "type", "metric"):
        values[field] = ""
    values["key"] = ""
    problems = cv.validate_dataset_candidate(values, dataset_sources())
    keys = [field for field, _message in problems]
    assert keys == [
        "key", "Dataset_path", "Category", "labels", "type", "metric",
    ]


def test_problems_follow_field_definition_order_not_dict_order():
    """A candidate whose dict inserts size before path still reports
    path first — ordering is the DECLARED field order."""
    values = {
        "size (M)": "abc",
        "Model_path": "",
        "key": "my-custom-lm",
        "type": "MLM",
        "Tokenizer": "6mer",
    }
    problems = cv.validate_model_candidate(values, model_sources())
    keys = [field for field, _message in problems]
    assert keys == ["Model_path", "size (M)"]


# ===== Key checks: required, format, collisions =====


def test_key_collisions_official_and_custom_each_reported():
    sources = model_sources()
    official_hit = dict(full_model_values(), key="plant-dnabert-6mer")
    problems = cv.validate_model_candidate(official_hit, sources)
    assert [field for field, _ in problems] == ["key"]
    assert "plant-dnabert-6mer" in problems[0][1]

    custom_hit = dict(full_model_values(), key="my-prev-lm")
    problems = cv.validate_model_candidate(custom_hit, sources)
    assert [field for field, _ in problems] == ["key"]
    assert "my-prev-lm" in problems[0][1]


def test_key_collision_check_covers_both_families_in_one_pass():
    """A key present in BOTH collision sets reports both problems (the
    same pass covers official AND existing custom)."""
    sources = model_sources(
        existing_custom_models={"plant-dnabert-6mer": {"size (M)": 1}}
    )
    values = dict(full_model_values(), key="plant-dnabert-6mer")
    problems = cv.validate_model_candidate(values, sources)
    key_problems = [message for field, message in problems if field == "key"]
    assert len(key_problems) == 2
    assert any("official" in message for message in key_problems)
    assert any("custom" in message for message in key_problems)


def test_empty_or_whitespace_key_is_a_required_problem():
    for bad in ("", "   "):
        values = dict(full_model_values(), key=bad)
        problems = cv.validate_model_candidate(values, model_sources())
        assert [field for field, _ in problems] == ["key"]
    values = dict(full_model_values(), key=None)
    problems = cv.validate_model_candidate(values, model_sources())
    assert [field for field, _ in problems] == ["key"]


def test_key_with_path_separator_is_a_format_problem():
    values = dict(full_model_values(), key="evil/key")
    problems = cv.validate_model_candidate(values, model_sources())
    assert [field for field, _ in problems] == ["key"]
    values = dict(full_model_values(), key="evil\\key")
    problems = cv.validate_model_candidate(values, model_sources())
    assert [field for field, _ in problems] == ["key"]


# ===== Numeric checks (bool excluded, D-14) =====


def test_size_numeric_check_rejects_strings_and_bools():
    for bad in ("abc", True, False, [89]):
        values = dict(full_model_values(), **{"size (M)": bad})
        problems = cv.validate_model_candidate(values, model_sources())
        assert [field for field, _ in problems] == ["size (M)"], bad
    for good in (89, 89.5, 0):
        values = dict(full_model_values(), **{"size (M)": good})
        assert cv.validate_model_candidate(values, model_sources()) == []


def test_split_counts_are_int_strict_with_bool_excluded():
    """Train/Dev/Test accept ints only — floats and bools are problems;
    an ABSENT declaration is not (the split counting derives it)."""
    for bad in (3.5, True, "3", [3]):
        values = dict(full_dataset_values(), Train=bad)
        problems = cv.validate_dataset_candidate(values, dataset_sources())
        assert [field for field, _ in problems] == ["Train"], bad
    absent = full_dataset_values()
    del absent["Train"]
    assert cv.validate_dataset_candidate(absent, dataset_sources()) == []


def test_labels_and_length_numeric_checks():
    for bad in ("2", True, None):
        values = dict(full_dataset_values(), labels=bad)
        problems = cv.validate_dataset_candidate(values, dataset_sources())
        assert [field for field, _ in problems] == ["labels"], bad
    values = dict(full_dataset_values(), length="512")
    problems = cv.validate_dataset_candidate(values, dataset_sources())
    assert [field for field, _ in problems] == ["length"]
    # Optional length may be absent entirely.
    absent = full_dataset_values()
    del absent["length"]
    assert cv.validate_dataset_candidate(absent, dataset_sources()) == []


# ===== Untrusted input: problems, never exceptions =====


def test_non_dict_candidates_yield_problems_never_raise():
    for bad in (None, ["a", "b"], "just-a-string", 42):
        problems = cv.validate_model_candidate(bad, model_sources())
        assert isinstance(problems, list) and len(problems) == 1
        assert problems[0][0] == "key"
        problems = cv.validate_dataset_candidate(bad, dataset_sources())
        assert isinstance(problems, list) and len(problems) == 1


def test_wrong_python_shapes_yield_problems_never_raise():
    """Lists where strings expected, bools where ints expected — every
    combination collects problems without raising."""
    values = full_model_values()
    values["Model_path"] = ["not", "a", "string"]
    values["size (M)"] = True
    values["key"] = {"nested": "dict"}
    problems = cv.validate_model_candidate(values, model_sources())
    assert isinstance(problems, list) and len(problems) >= 2
    keys = [field for field, _ in problems]
    assert keys[0] == "key"


def test_none_sources_defaults_to_empty_injections():
    """A None data_sources degrades to the empty namespace — the pure
    function never dereferences a missing argument."""
    problems = cv.validate_model_candidate(full_model_values(), None)
    assert problems == []


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
