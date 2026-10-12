"""
custom_validation — the D-05 collect-all candidate validator (Phase 9,
09-01, CUST-03).

The fourth ``_validate_filters``-discipline instance: ONE pass collects
EVERY field problem as ordered ``(field_key, message)`` pairs in
field-definition order — a candidate with three broken fields yields
three numbered problems, never the first only, and no untrusted input
shape ever raises (the wizard submits operator text; the import lane
submits parsed JSON). Presentation is NOT here: the pairs carry machine
field keys, the screens map them to labels and compose the numbered
report lines from ``tui/strings.py``.

Contract (locked decisions):

- D-05 (collect-all pure function): ``validate_model_candidate`` /
  ``validate_dataset_candidate`` take ``(values, data_sources)`` with
  every external fact INJECTED — official keys, existing custom entries,
  the metric registry, the fs root, the observed vocabularies — so the
  matrix is tier-1 testable headless against tmp roots and synthetic
  sets, never the real home (this machine HAS a real
  ``~/.config/dnallmmark``).
- Binding constraint 5 (TUI orchestrates, never computes): the checks
  cover field-level validity only — no ranking, normalization, survivor
  arithmetic, or metric computation ever lands here. The split-count
  mirror uses the audit kernel's exact parse discipline; the
  AUTHORITATIVE row/non-ACGT/subset measurement stays in the 09-02
  subprocess.
- Problem ordering: field-DEFINITION order (the wizard's field order —
  the same order the operator typed them in), never sorted by accident
  of dict iteration.
- Bool exclusion (D-14): ``bool`` is a subclass of ``int`` — every
  numeric check excludes it explicitly before the ``isinstance`` test.

Scope note (09-01 task split): this module lands with the traversal
skeleton plus the required / key-collision / numeric checks; the enum,
path-existence, split-file, label-column, and metric-registry checks and
the ``METRIC_REGISTRY`` constant land with the follow-up task in this
same plan.

ZERO textual imports (the services-tier invariant declared in
``tui/services/__init__.py``; locked by
``tests/tui/test_import_lock.py``). Dependencies: stdlib only at this
stage (``jsonschema`` joins with the import-schema task).
"""

from dataclasses import dataclass, field
from pathlib import Path

# ===== Locations (resolved from this module's own file, never CWD) =====

REPO_ROOT = Path(__file__).resolve().parents[2]
#: Default fs root for the path-existence checks: the pipeline dir is the
#: base official ``models/...`` / ``datasets/...`` paths resolve against
#: (tests inject a tmp root).
PIPELINE_DIR = REPO_ROOT / "pipeline"

# ===== Field-definition orders (the problem emission order, D-05) =====
#
# The wizard's field order per kind — steps 1..4, fields in declaration
# order inside each step. Every check appends its problem keyed by the
# field it belongs to, so the collected list reads in the same order the
# operator filled the form. ``key`` is the wizard's registry-key form
# field; it is NOT an entry field (land drops it).

MODEL_FIELD_ORDER = (
    "key",                # step 1: 键名 (the registry key)
    "Model_path",         # step 1: 本地路径
    "size (M)",           # step 1: 规模
    "species",            # step 1: 物种
    "type",               # step 2: 类型 (MLM/CLM/DL)
    "architecture",       # step 2: architecture (free text)
    "Tokenizer",          # step 2: tokenizer (canonical casing twin)
    "context_len (bp)",   # step 2: context_len (bp)
    "huggingface",        # step 3: huggingface (free text)
    "modelscope",         # step 3: modelscope (free text)
    "series",             # step 3: series (free text)
    "quirks",             # step 4: quirk checklist (D-02)
)

DATASET_FIELD_ORDER = (
    "key",                # step 1: 键名 (the registry key)
    "Dataset_path",       # step 1: 数据集路径
    "Category",           # step 1: Category
    "label_column",       # step 2: 标签列 (custom-only field)
    "Train",              # step 2: train split declaration
    "Dev",                # step 2: dev split declaration
    "Test",               # step 2: test split declaration
    "labels",             # step 2: 标签数
    "length",             # step 2: 序列长度 (optional)
    "type",               # step 3: Task_type (registry field `type`)
    "metric",             # step 3: 主指标
    "citation",           # step 4: citation (optional free text)
    "source",             # step 4: source (optional free text)
    "license",            # step 4: license (optional free text)
    "preprocessing",      # step 4: preprocessing (optional free text)
)

# ===== Required-field sets (the wizard-required subset; D-11 schema) =====
#
# Train/Dev/Test are deliberately NOT in the dataset required set: the
# wizard never collects them — the split counting derives the declared
# ints from the CSVs (the equality check compares a PRESENT declaration
# against the count; absence means "derive me").

MODEL_REQUIRED_FIELDS = (
    "key", "Model_path", "size (M)", "type", "Tokenizer",
)

DATASET_REQUIRED_FIELDS = (
    "key", "Dataset_path", "Category", "labels", "type", "metric",
)

#: Numeric fields: int-strict (split counts) vs number-tolerant (sizes,
#: label counts, lengths). Every numeric check excludes bool first (D-14).
MODEL_NUMERIC_FIELDS = ("size (M)",)
DATASET_INT_FIELDS = ("Train", "Dev", "Test")
DATASET_NUMERIC_FIELDS = ("labels", "length")


@dataclass(frozen=True)
class ValidationSources:
    """The injected data sources every CUST-03 check resolves against.

    D-05: the validator is a pure function over ``values`` plus this
    namespace — it never reads the registries, the custom files, or the
    filesystem roots itself. The 09-04/09-05 screens construct it from
    ``registry_loader`` (official keys), ``custom_entries.read_entries``
    (existing customs), the frozen ``METRIC_REGISTRY``, and the pipeline
    dir; tests construct it from synthetic sets and tmp roots.

    Attributes:
        official_model_keys: official model registry keys (collision set).
        official_dataset_keys: official dataset registry keys.
        existing_custom_models: the existing custom model entries map
            (``{key: entry}`` — keys are the collision set).
        existing_custom_datasets: the existing custom dataset entries map.
        metric_registry: the frozen metric-name authority (SUITE_CANONICAL
            twin; lands with the metric task in this plan).
        fs_root: the root relative paths resolve against for existence
            checks (absolute paths check as-is).
        observed_species: observed species vocabulary (enum source).
        observed_tokenizers: observed tokenizer vocabulary (enum source).
    """

    official_model_keys: frozenset = frozenset()
    official_dataset_keys: frozenset = frozenset()
    existing_custom_models: dict = field(default_factory=dict)
    existing_custom_datasets: dict = field(default_factory=dict)
    metric_registry: frozenset = frozenset()
    fs_root: Path = PIPELINE_DIR
    observed_species: tuple = ()
    observed_tokenizers: tuple = ()


def validate_model_candidate(values, data_sources):
    """Validate one model wizard candidate, collect-ALL (D-05, CUST-03).

    Args:
        values (dict): the wizard's field values, keyed by field name
            (the registry key under ``"key"``). Any other Python shape
            yields collected problems, never an exception.
        data_sources (ValidationSources): the injected namespace (D-05).

    Returns:
        list[tuple[str, str]]: every problem as ``(field_key, message)``
        in MODEL_FIELD_ORDER — empty means the candidate passes this
        task's check subset (required / key-collision / numeric).
    """
    sources = data_sources or ValidationSources()
    problems = []
    if not isinstance(values, dict):
        return [("key", f"candidate must be a JSON object, got {type(values).__name__}")]
    _check_key(values, sources, sources.official_model_keys,
               sources.existing_custom_models, problems)
    _check_required(values, MODEL_REQUIRED_FIELDS, problems)
    _check_numeric(values, MODEL_NUMERIC_FIELDS, problems)
    return problems


def validate_dataset_candidate(values, data_sources):
    """Validate one dataset wizard candidate, collect-ALL (D-05, CUST-03).

    Args:
        values (dict): the wizard's field values, keyed by field name
            (the registry key under ``"key"``). Any other Python shape
            yields collected problems, never an exception.
        data_sources (ValidationSources): the injected namespace (D-05).

    Returns:
        list[tuple[str, str]]: every problem as ``(field_key, message)``
        in DATASET_FIELD_ORDER — empty means the candidate passes this
        task's check subset (required / key-collision / numeric).
    """
    sources = data_sources or ValidationSources()
    problems = []
    if not isinstance(values, dict):
        return [("key", f"candidate must be a JSON object, got {type(values).__name__}")]
    _check_key(values, sources, sources.official_dataset_keys,
               sources.existing_custom_datasets, problems)
    _check_required(values, DATASET_REQUIRED_FIELDS, problems)
    _check_int_fields(values, DATASET_INT_FIELDS, problems)
    _check_numeric(values, DATASET_NUMERIC_FIELDS, problems)
    return problems


# ===== Check kernels (each appends in field-definition order) =====


def _check_key(values, sources, official_keys, existing_custom, problems):
    """Required + name-format + collision checks over the ``key`` field.

    A registry key becomes a JSON object key and flows into file names —
    it must be non-empty and must never smuggle a path separator. Both
    collision families (official AND existing custom) are checked in the
    same pass (CUST-03: 键名与官方及既有自定义不冲突).
    """
    key = values.get("key")
    if not isinstance(key, str) or not key.strip():
        problems.append(("key", "required field missing or empty"))
        return
    if "/" in key or "\\" in key:
        problems.append(("key", f"key must not contain path separators: {key!r}"))
    if key in official_keys:
        problems.append(("key", f"collides with an official registry key: {key}"))
    if isinstance(existing_custom, dict) and key in existing_custom:
        problems.append(("key", f"collides with an existing custom entry key: {key}"))


def _check_required(values, required_fields, problems):
    """Required/non-empty check over the wizard-required subset."""
    for name in required_fields:
        if name == "key":
            continue  # checked by _check_key with its richer semantics
        if _is_absent(values.get(name)):
            problems.append((name, "required field missing or empty"))


def _check_int_fields(values, int_fields, problems):
    """Int-strict numeric check (split counts), bool excluded (D-14).

    Values the required check owns (``None``/empty) are skipped here —
    one field defect yields ONE problem, never a required+numeric pair.
    """
    for name in int_fields:
        if _is_absent(values.get(name)):
            continue  # absent declarations derive from the split counts
        value = values[name]
        if isinstance(value, bool) or not isinstance(value, int):
            problems.append((name, f"needs an integer, got {type(value).__name__}"))


def _check_numeric(values, numeric_fields, problems):
    """Number-tolerant numeric check, bool excluded (D-14).

    Same single-defect rule as ``_check_int_fields``: absence/emptiness
    belongs to the required check; this check owns non-numeric content.
    """
    for name in numeric_fields:
        value = values.get(name)
        if _is_absent(value):
            continue  # optional numerics may be absent
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            problems.append(
                (name, f"needs a numeric value, got {type(value).__name__}")
            )


def _is_absent(value):
    """True when ``value`` is missing/empty — the required check's case."""
    return value is None or (isinstance(value, str) and not value.strip())
