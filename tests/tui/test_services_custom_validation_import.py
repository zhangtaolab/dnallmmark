"""
Tier-1 service tests for the D-11 import/export tier (Phase 9, 09-01:
``schemas/custom_registry.json`` + validate-before-merge + byte-verbatim
export).

Pinned decisions:

- **D-11 (import/export at the service tier):** import = tolerant
  artifact_loader read + jsonschema validation against the committed
  entry schema + EVERY key collision (official AND existing custom)
  listed once in file order — nothing merges on any problem. Export =
  the user-owned registry file copied VERBATIM (byte-identical) to the
  operator path; an absent/empty registry yields the empty-state signal
  and creates nothing at the destination.
- **Entry-shape contract:** the schema describes the ENTRY shapes
  ($defs/model_entry, $defs/dataset_entry) under the run_template.json
  discipline — strict draft 2020-12, additionalProperties false, $id
  under the repo schemas URL, per-entry ``schema_version`` const 1. The
  file TOP LEVEL stays a plain ``{key: entry}`` map — no envelope key
  (registry_loader merges EVERY top-level key; the $comment documents
  both load-bearing rules: plain top level + pipeline-RELATIVE landed
  paths, Pitfall 4).
- **Required = the wizard-required subset:** models
  Model_path/size (M)/type/Tokenizer; datasets
  Dataset_path/Category/Train/Dev/Test/labels/type/metric. Optional
  strings default to "" at composition time; optional numerics may be
  absent; ``Index`` is enumerated as optional (inert — no verified
  consumer reads it); the custom-only enabled/quirks (models) /
  enabled/label_column (datasets) fields are enumerated.
- **Tolerance (untrusted file input):** an unreadable, non-JSON, or
  non-object-top-level import file yields a single problem line naming
  the path — never an exception, never a partial merge.

See also:
    ``tui/services/custom_validation.py`` — validate_import_document.
    ``tui/services/custom_entries.py`` — read_import_candidates /
    export_registry.
    ``schemas/run_template.json`` — the schema discipline mirrored.
    ``tests/tui/test_services_templates.py`` — the jsonschema precedent.
"""

import hashlib
import json
from pathlib import Path

import jsonschema
import pytest

from tui.services import custom_entries
from tui.services import custom_validation as cv

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "custom_registry.json"
CONFIG_ENV = "DNALLMMARK_TUI_CONFIG_DIR"

MODEL_ENTRY_REQUIRED = ["Model_path", "Tokenizer", "size (M)", "type"]
DATASET_ENTRY_REQUIRED = [
    "Category", "Dataset_path", "Dev", "Test", "Train", "labels", "metric",
    "type",
]


def make_model_entry(**overrides):
    """A full 16-field model entry plus the custom-only enabled field."""
    entry = {
        "Mean_token_length": 6,
        "Model_name": "imported-lm-a",
        "Model_path": "models/imported-lm-a",
        "Model_size": "100M",
        "Tokenizer": "6mer",
        "architecture": "Bert",
        "context_len (bp)": 2000,
        "huggingface": "org/imported-lm-a",
        "mean_token_len": 6,
        "modelscope": "org/imported-lm-a",
        "name": "ImportedLM-A",
        "series": "",
        "size (M)": 89,
        "species": "plants",
        "tokenizer": "6-mer",
        "type": "MLM",
        "enabled": True,
    }
    entry.update(overrides)
    return entry


def make_dataset_entry(**overrides):
    """A full 17-field dataset entry plus the custom-only fields."""
    entry = {
        "Category": "Plants",
        "Dataset_name": "Imported__task_a",
        "Dataset_path": "datasets/Imported/task_a",
        "Dev": 2,
        "Test": 2,
        "Train": 3,
        "Index": 9999,
        "citation": "",
        "download_url": "",
        "download_url_alternates": "",
        "labels": 2,
        "length": 512,
        "license": "",
        "metric": "f1",
        "preprocessing": "",
        "source": "",
        "type": "binary",
        "enabled": True,
        "label_column": "label",
    }
    entry.update(overrides)
    return entry


def import_sources():
    """Synthetic collision sets: one official + one existing custom key
    per kind."""
    return cv.ValidationSources(
        official_model_keys=frozenset({"plant-dnabert-6mer"}),
        official_dataset_keys=frozenset({"GUE__emp_H3"}),
        existing_custom_models={"my-prev-lm": {"size (M)": 1}},
        existing_custom_datasets={"MyPrev__task": {"labels": 2}},
    )


def write_import_file(tmp_path, doc, name="import.json"):
    path = tmp_path / name
    path.write_text(json.dumps(doc, indent=4, ensure_ascii=False),
                    encoding="utf-8")
    return path


# ===== The committed schema (the entry-shape contract) =====


def test_schema_file_is_valid_draft_2020_12():
    assert SCHEMA_PATH.is_file()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == (
        "https://raw.githubusercontent.com/zhangtaolab/dnallmmark"
        "/main/schemas/custom_registry.json"
    )
    assert "$defs" in schema


def test_schema_defs_carry_additional_properties_false():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    for def_name in ("model_entry", "dataset_entry"):
        entry_schema = schema["$defs"][def_name]
        assert entry_schema["type"] == "object"
        assert entry_schema["additionalProperties"] is False, def_name


def test_schema_required_sets_match_the_wizard_subset():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert sorted(schema["$defs"]["model_entry"]["required"]) == (
        MODEL_ENTRY_REQUIRED
    )
    assert sorted(schema["$defs"]["dataset_entry"]["required"]) == (
        DATASET_ENTRY_REQUIRED
    )


def test_schema_enums_pin_category_and_dataset_type():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    dataset_props = schema["$defs"]["dataset_entry"]["properties"]
    assert dataset_props["Category"]["enum"] == [
        "Animals", "Plants", "Microbe", "Multiple",
    ]
    assert dataset_props["type"]["enum"] == [
        "binary", "multiclass", "regression", "multilabel",
    ]


def test_schema_enumerates_custom_only_and_inert_fields():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    model_props = schema["$defs"]["model_entry"]["properties"]
    assert model_props["enabled"] == {"type": "boolean"}
    assert sorted(model_props["quirks"]["properties"]) == [
        "fp32_only", "no_safetensors", "special_head",
    ]
    assert all(
        prop == {"type": "boolean"}
        for prop in model_props["quirks"]["properties"].values()
    )
    assert model_props["schema_version"] == {"const": 1}
    dataset_props = schema["$defs"]["dataset_entry"]["properties"]
    assert dataset_props["enabled"] == {"type": "boolean"}
    assert dataset_props["label_column"] == {"type": "string"}
    # Index is inert to every verified consumer — optional integer.
    assert dataset_props["Index"] == {"type": "integer"}
    assert "Index" not in schema["$defs"]["dataset_entry"]["required"]


def test_schema_comment_documents_the_two_load_bearing_rules():
    comment = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))["$comment"]
    lowered = comment.lower()
    assert "relative" in lowered      # pipeline-RELATIVE landed paths
    assert "envelope" in lowered      # plain {key: entry} top level


def test_model_entry_with_unknown_extra_field_fails_schema():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(
        schema["$defs"]["model_entry"]
    )
    clean = make_model_entry()
    assert list(validator.iter_errors(clean)) == []
    dirty = make_model_entry(surprise=True)
    errors = list(validator.iter_errors(dirty))
    assert len(errors) == 1
    assert "surprise" in errors[0].message


# ===== validate_import_document: collect-all, file order =====


def test_two_clean_entries_validate_with_zero_problems():
    doc = {
        "imported-lm-a": make_model_entry(),
        "imported-lm-b": make_model_entry(
            Model_name="imported-lm-b",
            Model_path="models/imported-lm-b",
            name="ImportedLM-B",
        ),
    }
    problems = cv.validate_import_document(
        custom_entries.KIND_MODELS, doc, import_sources()
    )
    assert problems == []


def test_import_rejects_metric_outside_the_registry():
    """WR-03 (09 review): the import lane runs the SAME metric enum the
    wizard lane runs — a shared file with ``"metric": "bleu"`` passes the
    schema (a plain string) but must NOT import: the downstream scripts
    cannot compute an unregistered primary metric, a defect this gate
    exists to catch before launch."""
    doc = {"Imported__task_a": make_dataset_entry(metric="bleu")}
    problems = cv.validate_import_document(
        custom_entries.KIND_DATASETS, doc, import_sources()
    )
    assert len(problems) == 1
    key, message = problems[0]
    assert key == "Imported__task_a"
    assert message.startswith("metric: ")
    assert "bleu" in message


def test_import_rejects_model_type_outside_the_frozen_triple():
    """WR-03 (09 review): the model-side twin — ``"type": "RNN"`` passes
    the schema but the wizard lane would refuse it; both lanes accept
    exactly the same documents."""
    doc = {"imported-lm-a": make_model_entry(type="RNN")}
    problems = cv.validate_import_document(
        custom_entries.KIND_MODELS, doc, import_sources()
    )
    assert len(problems) == 1
    key, message = problems[0]
    assert key == "imported-lm-a"
    assert message.startswith("type: ")
    assert "RNN" in message


def test_import_metric_check_uses_the_injected_registry():
    """The import enum resolves through the injected metric_registry (the
    D-05 seam) — an injected vocabulary governs the import lane exactly
    as it governs the wizard lane."""
    sources = cv.ValidationSources(
        metric_registry=frozenset({"accuracy"}),
    )
    problems_ok = cv.validate_import_document(
        custom_entries.KIND_DATASETS,
        {"Imported__task_a": make_dataset_entry(metric="accuracy")},
        sources,
    )
    problems_bad = cv.validate_import_document(
        custom_entries.KIND_DATASETS,
        {"Imported__task_a": make_dataset_entry(metric="f1")},
        sources,
    )
    assert problems_ok == []
    assert len(problems_bad) == 1
    assert problems_bad[0][1].startswith("metric: ")


def test_both_collision_kinds_listed_once_in_one_pass():
    """One key colliding official AND one colliding existing custom —
    both in the SAME numbered pass, in file order, each exactly once."""
    doc = {
        "plant-dnabert-6mer": make_model_entry(),  # official collision
        "my-prev-lm": make_model_entry(),          # custom collision
        "clean-lm": make_model_entry(),            # clean
    }
    problems = cv.validate_import_document(
        custom_entries.KIND_MODELS, doc, import_sources()
    )
    assert len(problems) == 2
    assert [key for key, _message in problems] == [
        "plant-dnabert-6mer", "my-prev-lm",
    ]


def test_every_schema_problem_collected_for_broken_entries():
    doc = {
        "broken": make_model_entry(
            **{"size (M)": "abc", "type": 42}
        ),  # wrong types
        "incomplete": {"Model_path": "models/x"},  # missing required
    }
    problems = cv.validate_import_document(
        custom_entries.KIND_MODELS, doc, import_sources()
    )
    keys = [key for key, _message in problems]
    assert keys.count("broken") >= 2   # size (M) + type
    assert keys.count("incomplete") >= 3  # Tokenizer/size (M)/type missing


def test_nothing_merges_on_any_problem(tmp_path, monkeypatch):
    """A failed import validation leaves the user-owned store untouched
    — validation is pure; the merge (09-05's per-entry gauntlet) never
    runs on problems."""
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path))
    doc = {"plant-dnabert-6mer": make_model_entry()}
    problems = cv.validate_import_document(
        custom_entries.KIND_MODELS, doc, import_sources()
    )
    assert problems
    assert not custom_entries.custom_registry_path(
        custom_entries.KIND_MODELS
    ).exists()  # no store file materialized by validation


def test_non_object_document_yields_single_problem():
    for doc in (None, ["a"], "x", 42):
        problems = cv.validate_import_document(
            custom_entries.KIND_MODELS, doc, import_sources()
        )
        assert isinstance(problems, list) and len(problems) == 1
        assert problems[0][0] == ""


def test_empty_document_yields_a_problem_line():
    problems = cv.validate_import_document(
        custom_entries.KIND_MODELS, {}, import_sources()
    )
    assert len(problems) == 1


def test_non_object_entry_is_a_problem_not_a_crash():
    doc = {"good": make_model_entry(), "bad": [1, 2]}
    problems = cv.validate_import_document(
        custom_entries.KIND_MODELS, doc, import_sources()
    )
    assert [key for key, _message in problems] == ["bad"]


def test_unknown_kind_raises_for_the_caller(tmp_path):
    with pytest.raises(ValueError):
        cv.validate_import_document("bogus", {}, import_sources())


# ===== read_import_candidates: tolerant read, file order =====


def test_missing_file_yields_error_naming_the_path(tmp_path):
    missing = tmp_path / "absent.json"
    entries, error = custom_entries.read_import_candidates(
        missing, custom_entries.KIND_MODELS
    )
    assert entries is None
    assert str(missing) in error


def test_non_json_and_non_object_files_yield_errors(tmp_path):
    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{not json", encoding="utf-8")
    entries, error = custom_entries.read_import_candidates(
        corrupt, custom_entries.KIND_MODELS
    )
    assert entries is None
    assert "unreadable" in error or "not valid JSON" in error

    listed = tmp_path / "listed.json"
    listed.write_text("[1, 2]", encoding="utf-8")
    entries, error = custom_entries.read_import_candidates(
        listed, custom_entries.KIND_MODELS
    )
    assert entries is None
    assert "object" in error


def test_file_order_preserved_into_candidates(tmp_path):
    """dict insertion order == file order — the 09-05 sequential
    gauntlet consumes entries in the file's own order (pinned)."""
    doc = {
        "z-late": make_model_entry(Model_name="z-late"),
        "a-early": make_model_entry(Model_name="a-early"),
        "m-middle": make_model_entry(Model_name="m-middle"),
    }
    path = write_import_file(tmp_path, doc)
    entries, error = custom_entries.read_import_candidates(
        path, custom_entries.KIND_MODELS
    )
    assert error is None
    assert list(entries) == ["z-late", "a-early", "m-middle"]


# ===== export_registry: byte-verbatim share unit =====


def test_export_is_byte_identical_hash_pinned(tmp_path, monkeypatch):
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path))
    model = make_model_entry()
    src = custom_entries.land(custom_entries.KIND_MODELS, "share-lm", model)
    dest = tmp_path / "shared" / "custom_models.json"
    dest.parent.mkdir(parents=True)
    ok, error = custom_entries.export_registry(
        custom_entries.KIND_MODELS, dest
    )
    assert ok is True and error is None
    assert hashlib.sha256(dest.read_bytes()).hexdigest() == (
        hashlib.sha256(src.read_bytes()).hexdigest()
    )


def test_export_absent_registry_yields_empty_state_creates_nothing(
    tmp_path, monkeypatch
):
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path / "cfg"))
    dest = tmp_path / "dest.json"
    ok, error = custom_entries.export_registry(
        custom_entries.KIND_MODELS, dest
    )
    assert ok is False
    assert error  # the empty-state signal carries a diagnostic
    assert not dest.exists()


def test_export_empty_registry_yields_empty_state(tmp_path, monkeypatch):
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path))
    model = make_model_entry()
    key = "undo-me"
    custom_entries.land(custom_entries.KIND_MODELS, key, model)
    assert custom_entries.undo(custom_entries.KIND_MODELS, key) is True
    dest = tmp_path / "dest.json"
    ok, _error = custom_entries.export_registry(
        custom_entries.KIND_MODELS, dest
    )
    assert ok is False
    assert not dest.exists()


def test_export_unreadable_registry_yields_empty_state_signal(
    tmp_path, monkeypatch
):
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path))
    path = custom_entries.custom_registry_path(custom_entries.KIND_MODELS)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json", encoding="utf-8")
    dest = tmp_path / "dest.json"
    ok, _error = custom_entries.export_registry(
        custom_entries.KIND_MODELS, dest
    )
    assert ok is False
    assert not dest.exists()
