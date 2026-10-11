"""
Tier-1 service tests for ``tui/services/templates.py`` (Phase 8, 08-05).

Pinned decisions:

- **D-07 (one-way contract, ratified 2026-10-11):**
  ``schemas/run_template.json`` is a strict draft-2020-12 schema —
  ``additionalProperties: false`` at every object level, top-level
  ``schema_version`` const 1, ``$id`` under the repo schemas URL — covering
  the complete run parameter set (models x tasks x seeds x PEFT x
  config-variant x GA). The GA semantics live in ``$comment``:
  ``GA = max(1, effective_batch // batch_size)`` with maintainer default 16
  (a small-model batch of 64 yields GA 1 — TUI-REQUIREMENTS open question
  #7, matching Phase 7 D-10 child-side semantics). Field names are frozen
  once landed: templates are shared between operators and the Phase 11
  run-config screen consumes the SAME schema.
- **SEL-03 (fail-fast collect-all):** ``validate_template`` collects EVERY
  problem in one pointer-ordered list — never one error at a time. A failed
  import changes no state because validation completes before any caller
  applies marks.
- **SEL-03 (empty edge):** models/tasks carry ``minItems: 1`` — an empty
  selection can neither import nor export;
  ``effective_batch_size`` has minimum 1 (boundary pinned here).
- **SEL-03 (adjacency/interop):** ``template_to_tiers`` /
  ``tiers_to_template`` round-trip preserving model and task MEMBERSHIP
  exactly, against the ``pipeline/sweep_priorities.json`` two-tier list
  shape (tier 1 = list of ``{model, task}`` pair dicts, tier 2 = list of
  model-name strings — the run_sweep ``--priority-file`` grammar, where a
  bare model name covers the model's every task and a spec may omit
  ``task``).
- **D-06 (zero hardcoding):** no tier model name from the committed
  priorities file appears in any service module — the file is the single
  source (the scan below reads the names as data, never embeds them).
- **T-08-04 (pure data):** templates are never evaluated — no code path
  executes strings from a template; validation is the only import gate.

See also:
    ``tui/services/templates.py`` — the service under test.
    ``schemas/flops_report.json`` — the strict-schema precedent copied.
    ``pipeline/run_sweep.py`` ``load_priority_tiers`` — the tier grammar.
    ``tests/tui/test_services_selection.py`` — the selection half.
"""

import json
from pathlib import Path

import jsonschema
import pytest

from tui.services import templates

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_PRIORITIES = REPO_ROOT / "pipeline" / "sweep_priorities.json"
SERVICES_DIR = REPO_ROOT / "tui" / "services"

# The committed priorities SHAPE with synthetic names (D-06: real tier
# names never appear in Python — tests included; where real content
# matters the committed file is read as data).
TIER_FIXTURE = [
    [
        {"model": "model-a", "task": "task-x"},
        {"model": "model-b", "task": "task-x"},
        {"model": "model-a", "task": "task-y"},
    ],
    ["model-c", "model-d", "model-e"],
]


def full_valid_document():
    """A template exercising every ratified field, all valid."""
    return {
        "schema_version": 1,
        "models": ["model-a", "model-b"],
        "tasks": ["task-x", "task-y"],
        "seeds": [42, 43, 44],
        "peft": "lora",
        "config_variant": "probe",
        "curve_fractions": [0.1, 0.25],
        "subset_file": "subsets/e2e.json",
        "effective_batch_size": 16,
        "num_train_epochs": 2,
        "cache_dir": "/tmp/dnallmmark-cache",
    }


def multi_violation_document():
    """A template with (at least) five simultaneous distinct violations."""
    return {
        # schema_version and tasks are MISSING (2 x required)
        "models": [],                  # minItems 1
        "peft": "lora123",             # enum
        "config_variant": "bogus",     # enum
        "effective_batch_size": 0,     # minimum 1
        "seeds": ["42"],               # items type integer
        "surprise": True,              # additionalProperties
    }


def real_priorities():
    """The committed priorities file, read as data (D-06 single source)."""
    return json.loads(REAL_PRIORITIES.read_text(encoding="utf-8"))


# ===== D-07: the schema itself (the one-way contract) =====


def test_schema_file_validates_as_draft_2020_12():
    """Draft202012Validator.check_schema passes over the committed schema."""
    schema = templates.load_schema()
    assert isinstance(schema, dict)
    jsonschema.Draft202012Validator.check_schema(schema)  # no raise = valid


def test_schema_pins_the_ratified_field_set():
    """The one-way contract, pinned exactly as ratified 2026-10-11."""
    schema = templates.load_schema()
    assert isinstance(schema, dict)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == (
        "https://raw.githubusercontent.com/zhangtaolab/dnallmmark"
        "/main/schemas/run_template.json"
    )
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["schema_version", "models", "tasks"]
    props = schema["properties"]
    assert props["schema_version"] == {"const": 1}
    for field in ("models", "tasks"):
        assert props[field]["type"] == "array"
        assert props[field]["items"] == {"type": "string"}
        assert props[field]["minItems"] == 1
        assert props[field]["uniqueItems"] is True
    assert props["seeds"] == {
        "type": "array",
        "items": {"type": "integer"},
        "default": [42, 43, 44],
    }
    assert props["peft"] == {"enum": ["none", "lora", "ia3"], "default": "none"}
    assert props["config_variant"] == {
        "enum": ["default", "head", "probe", "curve"],
        "default": "default",
    }
    assert props["curve_fractions"] == {"type": "array", "items": {"type": "number"}}
    assert props["subset_file"] == {"type": "string"}
    assert props["effective_batch_size"] == {"type": "integer", "minimum": 1}
    assert props["num_train_epochs"] == {"type": "number", "exclusiveMinimum": 0}
    assert props["cache_dir"] == {"type": "string"}


def test_schema_comment_records_provenance_and_ga_semantics():
    """$comment carries the D-07 provenance + the maintainer GA wording."""
    schema = templates.load_schema()
    assert isinstance(schema, dict)
    comment = schema["$comment"]
    assert "D-07" in comment
    assert "one-way" in comment
    assert "2026-10-11" in comment          # ratification date
    assert "Phase 11" in comment            # the forward consumer
    assert "GA = max(1, effective_batch // batch_size)" in comment
    assert "16" in comment                  # maintainer default
    assert "64" in comment                  # small-model batch 64 -> GA 1


def test_load_schema_missing_file_raises_runtime_error(tmp_path, monkeypatch):
    """A missing/corrupt committed schema is a loud repo-integrity error."""
    monkeypatch.setattr(templates, "SCHEMA_PATH", tmp_path / "absent.json")
    with pytest.raises(RuntimeError, match="run_template"):
        templates.load_schema()


# ===== SEL-03: collect-all validation (never one error at a time) =====


def test_validate_template_full_valid_document_returns_empty_problem_list():
    """Every ratified field present and valid -> zero problems."""
    problems = templates.validate_template(full_valid_document())
    assert isinstance(problems, list)
    assert problems == []


def test_validate_template_minimal_document_validates_without_seeds():
    """The seeds-default case: required-only doc is already valid — the
    seeds/peft/config_variant defaults apply when the fields are absent."""
    doc = {"schema_version": 1, "models": ["model-a"], "tasks": ["task-x"]}
    problems = templates.validate_template(doc)
    assert isinstance(problems, list)
    assert problems == []


def test_multi_violation_document_lists_every_problem_in_one_call():
    """SEL-03 collect-all: every simultaneous violation is listed together,
    each entry a (json_pointer, message) pair, ordered by pointer."""
    problems = templates.validate_template(multi_violation_document())
    assert isinstance(problems, list)
    assert len(problems) >= 5, "collect-all: at least five problems at once"
    for problem in problems:
        assert isinstance(problem, tuple)
        assert len(problem) == 2
        assert isinstance(problem[0], str) and isinstance(problem[1], str)
    pointers = [pointer for pointer, _message in problems]
    assert pointers == sorted(pointers), "problems are ordered by pointer"
    # Every distinct violation location is present in the one list:
    assert "" in pointers                       # required x2 + additionalProperties
    assert "/config_variant" in pointers        # bad enum
    assert "/effective_batch_size" in pointers  # minimum 1 boundary
    assert "/models" in pointers                # minItems 1
    assert "/peft" in pointers                  # bad enum
    assert "/seeds/0" in pointers               # items type integer


def test_validate_template_non_dict_documents_are_problems_not_crashes():
    """Untrusted input of any shape yields collected problems, never raises."""
    for doc in (None, ["not", "a", "dict"], "just-a-string"):
        problems = templates.validate_template(doc)
        assert isinstance(problems, list)
        assert len(problems) >= 1


def test_validate_template_bool_is_not_an_integer_seed():
    """jsonschema excludes bools from integer — True as a seed is a problem
    (the D-14 bool-exclusion discipline)."""
    doc = dict(full_valid_document(), seeds=[42, True])
    problems = templates.validate_template(doc)
    assert isinstance(problems, list)
    assert "/seeds/1" in [pointer for pointer, _message in problems]


# ===== SEL-03: export (always schema-valid, empty selection refused) =====


def test_export_minimal_params_materializes_defaults_and_validates():
    """export with no params -> schema-valid doc with the ratified defaults
    (seeds 42/43/44, peft none, config_variant default) and no optional keys."""
    doc = templates.export_selection_template(["model-a"], ["task-x"])
    assert isinstance(doc, dict)
    assert doc["schema_version"] == 1
    assert doc["models"] == ["model-a"]
    assert doc["tasks"] == ["task-x"]
    assert doc["seeds"] == [42, 43, 44]
    assert doc["peft"] == "none"
    assert doc["config_variant"] == "default"
    for optional in ("curve_fractions", "subset_file", "effective_batch_size",
                     "num_train_epochs", "cache_dir"):
        assert optional not in doc
    assert templates.validate_template(doc) == []


def test_export_full_params_round_trips_through_validation():
    """Every optional field present in params lands in the doc and validates."""
    params = {
        "seeds": [7],
        "peft": "ia3",
        "config_variant": "curve",
        "curve_fractions": [0.1, 0.25],
        "subset_file": "subsets/e2e.json",
        "effective_batch_size": 16,
        "num_train_epochs": 2,
        "cache_dir": "/tmp/dnallmmark-cache",
    }
    doc = templates.export_selection_template(["model-a"], ["task-x"], params)
    assert isinstance(doc, dict)
    for key, value in params.items():
        assert doc[key] == value
    assert templates.validate_template(doc) == []


def test_export_dedupes_preserving_first_occurrence():
    doc = templates.export_selection_template(
        ["model-b", "model-a", "model-b"], ["task-x", "task-x"]
    )
    assert isinstance(doc, dict)
    assert doc["models"] == ["model-b", "model-a"]
    assert doc["tasks"] == ["task-x"]


def test_export_empty_selection_raises_value_error():
    """SEL-03 empty edge: an empty selection cannot be exported as a template."""
    with pytest.raises(ValueError):
        templates.export_selection_template([], ["task-x"])
    with pytest.raises(ValueError):
        templates.export_selection_template(["model-a"], [])


def test_export_unknown_param_key_raises_naming_it():
    """Nothing silently dropped: a param key outside the ratified field set
    is a loud error, not a quiet omission from the exported document."""
    with pytest.raises(ValueError, match="epochz"):
        templates.export_selection_template(
            ["model-a"], ["task-x"], {"epochz": 3}
        )


# ===== SEL-03: sweep_priorities tier interop (pure-function pair) =====


def test_tiers_to_template_collects_membership_in_file_order():
    """Tier order then entry order, first occurrence wins; the doc validates."""
    template = templates.tiers_to_template(TIER_FIXTURE, {})
    assert isinstance(template, dict)
    assert template["models"] == [
        "model-a", "model-b", "model-c", "model-d", "model-e",
    ]
    assert template["tasks"] == ["task-x", "task-y"]
    assert templates.validate_template(template) == []


def test_interop_round_trip_preserves_membership_exactly():
    """tiers -> template -> tiers: model and task MEMBERSHIP preserved
    exactly, in both composition directions."""
    template = templates.tiers_to_template(TIER_FIXTURE, {})
    assert isinstance(template, dict)
    tiers = templates.template_to_tiers(template)
    assert isinstance(tiers, list)
    assert isinstance(tiers[0], list)
    pair_models = {pair["model"] for pair in tiers[0]}
    pair_tasks = {pair["task"] for pair in tiers[0]}
    assert pair_models == {"model-a", "model-b", "model-c", "model-d", "model-e"}
    assert pair_tasks == {"task-x", "task-y"}
    # The reverse composition preserves template membership too:
    template2 = templates.tiers_to_template(tiers, {})
    assert isinstance(template2, dict)
    assert set(template2["models"]) == set(template["models"])
    assert set(template2["tasks"]) == set(template["tasks"])


def test_template_to_tiers_is_the_models_major_cross_product():
    """A template is a cross-product selection; its faithful priorities
    encoding is one tier of explicit {model, task} pairs (a bare name would
    cover the model's UNSELECTED tasks too), models-major."""
    template = templates.export_selection_template(
        ["model-a", "model-b"], ["task-x", "task-y"]
    )
    assert isinstance(template, dict)
    assert templates.template_to_tiers(template) == [
        [
            {"model": "model-a", "task": "task-x"},
            {"model": "model-a", "task": "task-y"},
            {"model": "model-b", "task": "task-x"},
            {"model": "model-b", "task": "task-y"},
        ]
    ]


def test_tiers_to_template_pair_without_task_contributes_model_only():
    """The run_sweep grammar: a spec may omit task (covers every task) —
    model-only at the interop level, no task inferred."""
    template = templates.tiers_to_template(
        [[{"model": "model-a"}, {"model": "model-b", "task": "task-x"}]]
    )
    assert isinstance(template, dict)
    assert template["models"] == ["model-a", "model-b"]
    assert template["tasks"] == ["task-x"]


def test_tiers_to_template_names_only_tiers_cannot_become_a_template():
    """A tiers file with no task-bearing entry has nothing a template's
    minItems-1 tasks field could carry — loud ValueError, never a fake."""
    with pytest.raises(ValueError, match="task"):
        templates.tiers_to_template([["model-a", "model-b"]])


def test_tiers_to_template_malformed_entry_raises_naming_position():
    with pytest.raises(ValueError, match="tier 0 entry 1"):
        templates.tiers_to_template(
            [[{"model": "model-a", "task": "task-x"}, 42]]
        )


def test_template_to_tiers_malformed_template_raises():
    with pytest.raises(ValueError, match="models"):
        templates.template_to_tiers({"schema_version": 1, "tasks": ["task-x"]})


def test_interop_over_the_committed_priorities_file():
    """The real file round-trips: expected membership derived FROM the file
    (D-06 — never hardcoded), and the derived template validates clean."""
    tiers = real_priorities()
    template = templates.tiers_to_template(tiers, {"peft": "lora"})
    assert isinstance(template, dict)
    pair_models, pair_tasks, tier_names = [], [], []
    for tier in tiers:
        for entry in tier:
            if isinstance(entry, str):
                tier_names.append(entry)
            else:
                pair_models.append(entry["model"])
                if entry.get("task") is not None:
                    pair_tasks.append(entry["task"])
    expected_models = list(dict.fromkeys(pair_models + tier_names))
    expected_tasks = list(dict.fromkeys(pair_tasks))
    assert template["models"] == expected_models
    assert template["tasks"] == expected_tasks
    assert template["peft"] == "lora"
    assert templates.validate_template(template) == []


# ===== IO: tolerant load for existence diagnostics (validation is separate) =====


def test_load_template_file_missing_corrupt_and_valid(tmp_path):
    missing = tmp_path / "absent.json"
    result = templates.load_template_file(missing)
    assert isinstance(result, tuple) and len(result) == 2
    doc, error = result
    assert doc is None
    assert "not found" in error

    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{not json", encoding="utf-8")
    result = templates.load_template_file(corrupt)
    assert isinstance(result, tuple) and len(result) == 2
    doc, error = result
    assert doc is None
    assert "not valid JSON" in error

    good = tmp_path / "good.json"
    good.write_text(json.dumps(full_valid_document()), encoding="utf-8")
    result = templates.load_template_file(good)
    assert isinstance(result, tuple) and len(result) == 2
    doc, error = result
    assert error is None
    assert doc == full_valid_document()


# ===== D-06 + lane discipline: source scans =====


def test_no_tier_names_hardcoded_in_any_service_module():
    """D-06: every tier model name from the committed priorities file is
    absent from every tui/services module — the file is the single source
    (names read as data here, never embedded in Python)."""
    names = set()
    for tier in real_priorities():
        for entry in tier:
            names.add(entry if isinstance(entry, str) else entry["model"])
    assert names, "vacuous: the committed priorities file has no tier names"
    modules = sorted(SERVICES_DIR.glob("*.py"))
    assert modules, "vacuous: no tui/services/*.py files found"
    for module in modules:
        source = module.read_text(encoding="utf-8")
        for name in names:
            assert name not in source, f"{name} hardcoded in {module}"


def test_service_reads_json_only_through_the_tolerant_loader():
    """The 08-04 read discipline: no bare json.load in the service module."""
    source = Path(templates.__file__).read_text(encoding="utf-8")
    assert "json.load(" not in source
