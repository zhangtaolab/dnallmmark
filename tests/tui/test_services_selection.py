"""
Tier-1 service tests for ``tui/services/selection.py`` (Phase 8, 08-05).

Pinned decisions:

- **D-06 (presets derive, never hardcode):** presets derive from
  ``pipeline/sweep_priorities.json`` at read time — tier-1 (model+task
  pairs), tier-2 (model-name list), and all (the passed registry key
  lists); zero tier model names are hardcoded in Python (the file is the
  single source — tier edits require zero code changes). Preset names
  missing from the current registry are returned as ``unknown_keys`` for
  loud warning surfacing, never silently dropped (registry-evolution
  tolerance).
- **SEL-02 (ordering):** derivation order is deterministic — file order
  within each tier; the preset menu order is tier-1, tier-2, all, then
  saved customs sorted by name.
- **SEL-02 (empty edge):** no saved custom presets yields an empty
  customs mapping (rendered as the documented empty state by 08-07),
  never an error.
- **D-04 (config root only):** saved custom presets persist as
  ``presets.json`` under the XDG config root (schema_version 1, presets
  mapped name -> {models, tasks}), written atomically through the 08-04
  settings helpers — the state root is never used.
- **Damaged priorities file:** a missing/corrupt/malformed file yields
  EMPTY presets plus a load-error signal — never an exception.
- **Filter grammar (SEL-01 backing):** space-separated AND terms; each
  term a bare substring (matched against the entry key plus display
  fields) or ``axis=value`` over the 08-04 canonical entry keys (models
  species/type/size -> size_m; datasets category/type/metric). An unknown
  axis yields a diagnostic while valid terms still parse; matching is
  case-insensitive; results preserve registry order; no match is a plain
  empty list.
- **Decoupling:** the module imports NOTHING from
  ``tui.services.registries`` — entries and keys arrive as parameters
  (the 08-07 screen wires the two together).

See also:
    ``tui/services/selection.py`` — the service under test.
    ``tui/services/templates.py`` — the template half (08-05 Task 2).
    ``pipeline/sweep_priorities.json`` — the single source.
"""

import ast
import json
from pathlib import Path

from tui.services import registries
from tui.services import selection
from tui.services.selection import (
    AxisTerm,
    ParsedFilter,
    PresetDerivation,
    SubstringTerm,
    UnknownAxis,
    apply_filter,
    derive_presets,
    load_custom_presets,
    parse_filter_query,
    save_custom_preset,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_PRIORITIES = REPO_ROOT / "pipeline" / "sweep_priorities.json"
SERVICES_DIR = REPO_ROOT / "tui" / "services"

# Synthetic priorities fixture in the committed two-tier shape, carrying
# ONE unknown tier-2 name (D-06: real tier names never appear in Python —
# tests included; the real file is read as data below).
PRIORITIES_FIXTURE = [
    [
        {"model": "model-a", "task": "task-x"},
        {"model": "model-b", "task": "task-x"},
    ],
    ["model-c", "ghost-model"],
]
MODEL_KEYS = ("model-a", "model-b", "model-c", "model-d")
TASK_KEYS = ("task-x", "task-y", "task-z")
KNOWN_AXES = ("category", "metric", "size", "species", "type")


def write_priorities(tmp_path, tiers, name="sweep_priorities.json"):
    """Materialize a priorities fixture file; return its path."""
    path = tmp_path / name
    path.write_text(json.dumps(tiers), encoding="utf-8")
    return path


def model_entries():
    """Synthetic canonical MODEL entries (the 08-04 entry vocabulary)."""
    return [
        {"key": "plant-dnabert-6mer", "type": "MLM",
         "species": "plants", "size_m": 86.0, "card": {"Tokenizer": "6mer"}},
        {"key": "nucleotide-transformer-500m", "type": "MLM",
         "species": "multi-species", "size_m": 494.2, "card": {}},
        {"key": "gpn", "type": "DL", "species": "", "size_m": 0.0,
         "card": {}},
    ]


def dataset_entries():
    """Synthetic canonical DATASET entries (the 08-04 entry vocabulary)."""
    return [
        {"key": "GUE__emp_H3", "category": "Microbe", "type": "binary",
         "metric": "f1", "card": {}},
        {"key": "BEND__CpG_methylation", "category": "Animals",
         "type": "multilabel", "metric": "AUPRC", "card": {}},
    ]


# ===== D-06 / SEL-02: preset derivation =====


def test_derive_presets_tier1_marks_pair_models_and_tasks(tmp_path):
    path = write_priorities(tmp_path, PRIORITIES_FIXTURE)
    derivation = derive_presets(path, MODEL_KEYS, TASK_KEYS)
    assert isinstance(derivation, PresetDerivation)
    assert derivation.load_error is None
    by_id = {preset.id: preset for preset in derivation.presets}
    tier1 = by_id["tier-1"]
    assert tier1.models == ("model-a", "model-b")
    assert tier1.tasks == ("task-x",)
    assert tier1.unknown_keys == ()


def test_derive_presets_tier2_marks_models_only(tmp_path):
    path = write_priorities(tmp_path, PRIORITIES_FIXTURE)
    derivation = derive_presets(path, MODEL_KEYS, TASK_KEYS)
    assert isinstance(derivation, PresetDerivation)
    by_id = {preset.id: preset for preset in derivation.presets}
    tier2 = by_id["tier-2"]
    assert tier2.models == ("model-c", "ghost-model")
    assert tier2.tasks == ()          # models only — no task inferred
    assert tier2.unknown_keys == ("ghost-model",)


def test_derive_presets_tier2_unknown_name_surfaced_exactly(tmp_path):
    """D-06 loud surfacing: the one fixture name absent from the registry
    keys appears in unknown_keys EXACTLY — never silently dropped."""
    path = write_priorities(tmp_path, PRIORITIES_FIXTURE)
    derivation = derive_presets(path, MODEL_KEYS, TASK_KEYS)
    assert isinstance(derivation, PresetDerivation)
    assert derivation.load_error is None
    by_id = {preset.id: preset for preset in derivation.presets}
    assert by_id["tier-2"].unknown_keys == ("ghost-model",)


def test_derive_presets_all_returns_every_passed_key(tmp_path):
    path = write_priorities(tmp_path, PRIORITIES_FIXTURE)
    derivation = derive_presets(path, MODEL_KEYS, TASK_KEYS)
    assert isinstance(derivation, PresetDerivation)
    by_id = {preset.id: preset for preset in derivation.presets}
    all_preset = by_id["all"]
    assert all_preset.models == MODEL_KEYS   # registry order, verbatim
    assert all_preset.tasks == TASK_KEYS
    assert all_preset.unknown_keys == ()     # keys came FROM the registry


def test_derive_presets_menu_order_is_deterministic(tmp_path):
    """SEL-02 ordering: tier-1, tier-2, all (customs follow, sorted — the
    load_custom_presets tests pin that half)."""
    path = write_priorities(tmp_path, PRIORITIES_FIXTURE)
    derivation = derive_presets(path, MODEL_KEYS, TASK_KEYS)
    assert isinstance(derivation, PresetDerivation)
    assert tuple(preset.id for preset in derivation.presets) == (
        "tier-1", "tier-2", "all",
    )


def test_derive_presets_tier1_unknown_members_surfaced_not_dropped(tmp_path):
    """An unknown pair model AND an unknown pair task both surface in
    unknown_keys while still carrying in the preset membership."""
    tiers = [
        [
            {"model": "model-a", "task": "task-x"},
            {"model": "ghost-model", "task": "ghost-task"},
        ],
        ["model-c"],
    ]
    path = write_priorities(tmp_path, tiers)
    derivation = derive_presets(path, MODEL_KEYS, TASK_KEYS)
    assert isinstance(derivation, PresetDerivation)
    assert derivation.load_error is None
    tier1 = {preset.id: preset for preset in derivation.presets}["tier-1"]
    assert tier1.models == ("model-a", "ghost-model")
    assert tier1.tasks == ("task-x", "ghost-task")
    assert tier1.unknown_keys == ("ghost-model", "ghost-task")


def test_derive_presets_damaged_file_yields_empty_presets_plus_load_error(
        tmp_path):
    """Missing / corrupt / malformed priorities files: empty presets plus a
    load-error signal — never an exception."""
    # missing file
    derivation = derive_presets(tmp_path / "absent.json", MODEL_KEYS, TASK_KEYS)
    assert isinstance(derivation, PresetDerivation)
    assert derivation.presets == ()
    assert isinstance(derivation.load_error, str)
    assert "sweep_priorities" in derivation.load_error
    # corrupt JSON
    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{not json", encoding="utf-8")
    derivation = derive_presets(corrupt, MODEL_KEYS, TASK_KEYS)
    assert isinstance(derivation, PresetDerivation)
    assert derivation.presets == ()
    assert isinstance(derivation.load_error, str)
    # wrong shapes: not a list / not two tiers / malformed pair / non-string name
    for tiers in (
        {},                                   # not a list
        [["model-a"]],                        # only one tier
        [["model-a"], [], ["model-b"]],       # three tiers
        [[{"model": "model-a"}], ["model-b"]],  # pair missing 'task'
        [[("model-a", "task-x")], ["model-b"]],  # pair is not a dict
        [["model-a"], [42]],                  # tier-2 name is not a string
    ):
        path = write_priorities(tmp_path, tiers)
        derivation = derive_presets(path, MODEL_KEYS, TASK_KEYS)
        assert isinstance(derivation, PresetDerivation)
        assert derivation.presets == (), f"expected empty presets for {tiers!r}"
        assert isinstance(derivation.load_error, str), (
            f"expected a load error for {tiers!r}"
        )


def test_derive_presets_over_the_committed_priorities_file():
    """The real file derives cleanly against the real registry keys —
    expected membership computed FROM the file and registries as data
    (D-06: zero hardcoding, so tier edits never break this test)."""
    tiers = json.loads(REAL_PRIORITIES.read_text(encoding="utf-8"))
    model_keys = tuple(e["key"] for e in registries.load_model_entries())
    task_keys = tuple(e["key"] for e in registries.load_dataset_entries())
    derivation = derive_presets(REAL_PRIORITIES, model_keys, task_keys)
    assert isinstance(derivation, PresetDerivation)
    assert derivation.load_error is None
    by_id = {preset.id: preset for preset in derivation.presets}
    pair_models = list(dict.fromkeys(p["model"] for p in tiers[0]))
    pair_tasks = list(dict.fromkeys(p["task"] for p in tiers[0]))
    tier2_names = list(dict.fromkeys(tiers[1]))
    assert by_id["tier-1"].models == tuple(pair_models)
    assert by_id["tier-1"].tasks == tuple(pair_tasks)
    assert by_id["tier-2"].models == tuple(tier2_names)
    assert by_id["all"].models == model_keys
    assert by_id["all"].tasks == task_keys
    # Unknown keys derive from the data comparison, never assumptions:
    expected_unknown = tuple(
        name for name in tier2_names if name not in set(model_keys)
    )
    assert by_id["tier-2"].unknown_keys == expected_unknown
    assert by_id["tier-1"].unknown_keys == tuple(
        m for m in pair_models if m not in set(model_keys)
    ) + tuple(t for t in pair_tasks if t not in set(task_keys))


# ===== SEL-02: custom presets (XDG config root, atomic, sorted) =====


def test_save_load_custom_preset_round_trip(tmp_path):
    config_dir = tmp_path / "config"
    save_custom_preset("mine", {"model-b", "model-a"}, {"task-y"}, config_dir)
    presets = load_custom_presets(config_dir)
    assert isinstance(presets, dict)
    assert presets == {
        "mine": {"models": ["model-a", "model-b"], "tasks": ["task-y"]},
    }
    # The file is presets.json under the config root with schema_version 1:
    payload = json.loads((config_dir / "presets.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["presets"] == {
        "mine": {"models": ["model-a", "model-b"], "tasks": ["task-y"]},
    }


def test_save_overwrites_existing_name_atomically(tmp_path):
    config_dir = tmp_path / "config"
    save_custom_preset("x", {"model-a"}, {"task-x"}, config_dir)
    save_custom_preset("x", {"model-b", "model-c"}, {"task-y"}, config_dir)
    presets = load_custom_presets(config_dir)
    assert isinstance(presets, dict)
    assert presets["x"] == {
        "models": ["model-b", "model-c"], "tasks": ["task-y"],
    }
    # Atomic write leaves exactly one file, no tmp residue:
    assert list(config_dir.iterdir()) == [config_dir / "presets.json"]


def test_load_custom_presets_missing_root_is_an_empty_mapping(tmp_path):
    """SEL-02 empty edge: no saved presets -> empty mapping, never error."""
    presets = load_custom_presets(tmp_path / "never-created")
    assert isinstance(presets, dict)
    assert presets == {}


def test_load_custom_presets_corrupt_file_is_an_empty_mapping(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "presets.json").write_text("{not json", encoding="utf-8")
    presets = load_custom_presets(config_dir)
    assert isinstance(presets, dict)
    assert presets == {}


def test_load_custom_presets_unknown_schema_version_is_an_empty_mapping(
        tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "presets.json").write_text(
        json.dumps({
            "schema_version": 2,
            "presets": {"mine": {"models": ["model-a"], "tasks": ["task-x"]}},
        }),
        encoding="utf-8",
    )
    presets = load_custom_presets(config_dir)
    assert isinstance(presets, dict)
    assert presets == {}


def test_load_custom_presets_names_sort_deterministically(tmp_path):
    """Menu order: customs sorted by name regardless of save order."""
    config_dir = tmp_path / "config"
    save_custom_preset("beta", {"model-a"}, {"task-x"}, config_dir)
    save_custom_preset("alpha", {"model-b"}, {"task-y"}, config_dir)
    presets = load_custom_presets(config_dir)
    assert isinstance(presets, dict)
    assert list(presets) == ["alpha", "beta"]


# ===== SEL-01 backing: the pure filter grammar =====


def test_parse_filter_query_substring_and_axis_terms():
    parsed = parse_filter_query("plant type=MLM")
    assert isinstance(parsed, ParsedFilter)
    assert parsed.terms == (SubstringTerm("plant"), AxisTerm("type", "MLM"))
    assert parsed.diagnostics == ()


def test_parse_filter_query_empty_query_is_empty_everywhere():
    parsed = parse_filter_query("")
    assert isinstance(parsed, ParsedFilter)
    assert parsed.terms == ()
    assert parsed.diagnostics == ()


def test_parse_filter_query_unknown_axis_diagnostic_valid_terms_still_parse():
    parsed = parse_filter_query("bogus=1 type=MLM")
    assert isinstance(parsed, ParsedFilter)
    assert parsed.terms == (AxisTerm("type", "MLM"),)
    assert parsed.diagnostics == (UnknownAxis("bogus", KNOWN_AXES),)


def test_parse_filter_query_known_axis_vocabulary_is_the_ui_contract():
    """The five 08-04 canonical axes — models species/type/size (-> the
    size_m field), datasets category/type/metric (UI-SPEC keyboard
    contract)."""
    for axis in KNOWN_AXES:
        parsed = parse_filter_query(f"{axis}=x")
        assert isinstance(parsed, ParsedFilter)
        assert parsed.diagnostics == (), f"axis {axis} must be known"


def test_apply_filter_ands_terms_and_preserves_registry_order():
    entries = model_entries()
    parsed = parse_filter_query("plant type=MLM")
    assert isinstance(parsed, ParsedFilter)
    result = apply_filter(entries, parsed.terms)
    assert isinstance(result, list)
    assert [entry["key"] for entry in result] == ["plant-dnabert-6mer"]
    # AND semantics: the type axis alone keeps BOTH MLM entries in order
    result = apply_filter(entries, (AxisTerm("type", "MLM"),))
    assert isinstance(result, list)
    assert [entry["key"] for entry in result] == [
        "plant-dnabert-6mer", "nucleotide-transformer-500m",
    ]


def test_apply_filter_matching_is_case_insensitive():
    entries = model_entries()
    result = apply_filter(entries, (AxisTerm("type", "mlm"),))
    assert isinstance(result, list)
    assert len(result) == 2
    result = apply_filter(entries, (SubstringTerm("PLANT"),))
    assert isinstance(result, list)
    assert [entry["key"] for entry in result] == ["plant-dnabert-6mer"]


def test_apply_filter_size_axis_matches_the_size_m_field():
    """The operator-facing axis is `size`; the canonical field is size_m
    (str(86.0) == '86.0' contains '86')."""
    entries = model_entries()
    result = apply_filter(entries, (AxisTerm("size", "86"),))
    assert isinstance(result, list)
    assert [entry["key"] for entry in result] == ["plant-dnabert-6mer"]


def test_apply_filter_axis_absent_from_entry_kind_never_matches():
    """`category` over MODEL entries (which have no category field) is a
    plain empty result, not a crash and not a false match."""
    entries = model_entries()
    result = apply_filter(entries, (AxisTerm("category", "Plants"),))
    assert isinstance(result, list)
    assert result == []


def test_apply_filter_dataset_axes():
    entries = dataset_entries()
    parsed = parse_filter_query("category=Animals type=multilabel")
    assert isinstance(parsed, ParsedFilter)
    result = apply_filter(entries, parsed.terms)
    assert isinstance(result, list)
    assert [entry["key"] for entry in result] == ["BEND__CpG_methylation"]
    result = apply_filter(entries, (AxisTerm("metric", "auprc"),))
    assert isinstance(result, list)
    assert [entry["key"] for entry in result] == ["BEND__CpG_methylation"]


def test_apply_filter_no_match_is_a_plain_empty_list():
    result = apply_filter(model_entries(), (SubstringTerm("zzz-no-match"),))
    assert isinstance(result, list)
    assert result == []


def test_apply_filter_no_terms_returns_every_entry_in_order():
    entries = model_entries()
    result = apply_filter(entries, ())
    assert isinstance(result, list)
    assert result == entries


# ===== Decoupling + lane discipline: source scans =====


def test_selection_module_never_imports_registries():
    """Decoupled by design: entries and registry keys arrive as parameters
    (the 08-07 screen wires the two together) — no import form of
    tui.services.registries may appear at any AST depth."""
    tree = ast.parse(Path(selection.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("tui.services.registries")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert module != "tui.services.registries"
            if module == "tui.services":
                assert "registries" not in [a.name for a in node.names]


def test_selection_module_never_references_the_state_root():
    """D-04: presets persist under the CONFIG root only — the state root is
    not this module's business (settings.atomic_write is the write path)."""
    source = Path(selection.__file__).read_text(encoding="utf-8")
    assert "state_dir" not in source
    assert "user_state_dir" not in source


def test_selection_module_reads_json_only_through_the_tolerant_loader():
    source = Path(selection.__file__).read_text(encoding="utf-8")
    assert "json.load(" not in source


def test_no_tier_names_hardcoded_in_any_service_module():
    """D-06: every tier model name from the committed priorities file is
    absent from every tui/services module (names read as data here)."""
    names = set()
    for tier in json.loads(REAL_PRIORITIES.read_text(encoding="utf-8")):
        for entry in tier:
            names.add(entry if isinstance(entry, str) else entry["model"])
    assert names, "vacuous: the committed priorities file has no tier names"
    modules = sorted(SERVICES_DIR.glob("*.py"))
    assert modules, "vacuous: no tui/services/*.py files found"
    for module in modules:
        source = module.read_text(encoding="utf-8")
        for name in names:
            assert name not in source, f"{name} hardcoded in {module}"
