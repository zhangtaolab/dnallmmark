"""
custom_validation — the D-05 collect-all candidate validator (Phase 9,
09-01, CUST-03).

The fourth ``_validate_filters``-discipline instance: ONE pass collects
EVERY field problem as ordered ``(field_key, message)`` pairs in
field-definition order — a candidate with three broken fields yields
three numbered problems, never the first only, and no untrusted input
shape ever raises (the wizard submits operator text; the import lane
submits parsed JSON). Presentation is NOT here: the pairs carry machine
field keys and strings-composed messages; the screens map keys to labels
(``WIZM_FIELD_LABELS`` / ``WIZD_FIELD_LABELS``) and render the numbered
report lines.

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
  mirror reuses the audit kernel's exact parse discipline (utf-8
  ``csv.reader``, header membership, malformed-row skip); the
  AUTHORITATIVE row/non-ACGT/subset measurement stays in the 09-02
  subprocess.
- Problem ordering: field-DEFINITION order (the wizard's field order —
  the same order the operator typed them in), never sorted by accident
  of dict iteration; one field defect yields ONE problem (the numeric
  checks skip values the required check already owns).
- Metric single authority (IN-03 successor): ``METRIC_REGISTRY`` is the
  frozen 28-name SUITE_CANONICAL twin — parity-locked by the tier-1 test
  importing ``script/export_runs.py`` through the tests/conftest.py
  sys.path; NEVER imported here at runtime (script/ is not on the TUI
  bootstrap path; numpy top-level import).
- Copy single home: every message composes from ``tui/strings.py``
  constants (the WIZ_PROBLEM_* family) — zero inline operator copy in
  this module.
- D-11 (import validate-before-merge): ``validate_import_document``
  validates an imported registry document against the committed
  ``schemas/custom_registry.json`` ENTRY schema (strict draft 2020-12,
  ``additionalProperties: false``) plus BOTH collision families,
  collect-all in FILE order — nothing merges on any problem (the merge
  itself is 09-05's per-entry gauntlet). Untrusted file reads are
  tolerant (the ``read_import_candidates`` lane in ``custom_entries``).
- Bool exclusion (D-14): ``bool`` is a subclass of ``int`` — every
  numeric check excludes it explicitly before the ``isinstance`` test
  (jsonschema's integer/number types exclude bool by default on the
  import lane).

ZERO textual imports (the services-tier invariant declared in
``tui/services/__init__.py``; locked by
``tests/tui/test_import_lock.py``). Dependencies: stdlib +
jsonschema + ``artifact_loader`` (the D-19 tolerant seam) +
``tui.strings`` (the i18n single home).
"""

import csv
from dataclasses import dataclass, field
from pathlib import Path

import artifact_loader  # top-level module (pipeline/ sys.path root, D-19)
import jsonschema

from tui import strings

# ===== Locations (resolved from this module's own file, never CWD) =====

REPO_ROOT = Path(__file__).resolve().parents[2]
#: Default fs root for the path-existence checks: the pipeline dir is the
#: base official ``models/...`` / ``datasets/...`` paths resolve against
#: (tests inject a tmp root).
PIPELINE_DIR = REPO_ROOT / "pipeline"
#: The committed entry-shape contract (D-11) governing imported files.
IMPORT_SCHEMA_PATH = REPO_ROOT / "schemas" / "custom_registry.json"

#: Registry kind -> the schema $def describing that kind's entry shape.
IMPORT_ENTRY_DEFS = {"models": "model_entry", "datasets": "dataset_entry"}

# ===== The metric registry — the frozen 28-name SUITE_CANONICAL twin =====
#
# Single authority (IN-03): script/export_runs.py SUITE_CANONICAL is the
# owner; this constant is its TUI-side twin, parity-locked by the tier-1
# test (the count is 28, NOT 27 — 09-RESEARCH Pitfall 8). Never import
# export_runs here: it pulls numpy at module top and script/ is not on
# the TUI bootstrap sys.path.
METRIC_REGISTRY = frozenset({
    "accuracy", "precision", "recall", "f1", "f1_micro", "f1_weighted",
    "f1_samples", "precision_micro", "precision_weighted",
    "precision_samples", "recall_micro", "recall_weighted",
    "recall_samples", "mcc", "matthews_correlation", "AUROC", "AUPRC",
    "AUROC_ovr", "AUROC_ovo", "TPR", "TNR", "FPR", "FNR", "mse", "mae",
    "r2", "pearsonr", "spearmanr",
})  # 28 names — parity test pins the exact set

# ===== Fixed enum vocabularies (the registry-observed values) =====

#: Model type (09-RESEARCH Code Examples: MLM/CLM/DL).
MODEL_TYPE_VALUES = ("MLM", "CLM", "DL")
#: Dataset Category — the four observed registry values (UI-SPEC adds
#: none).
DATASET_CATEGORY_VALUES = ("Animals", "Plants", "Microbe", "Multiple")
#: Dataset Task_type — stored under the registry field name ``type``
#: (UI-SPEC Auto-Default #11).
DATASET_TYPE_VALUES = ("binary", "multiclass", "regression", "multilabel")

# ===== Field-definition orders (the problem emission order, D-05) =====
#
# The wizard's field order per kind — steps 1..4, fields in declaration
# order inside each step. Every check appends its problem keyed by the
# field it belongs to, so the collected list reads in the same order the
# operator filled the form. ``key`` is the wizard's registry-key form
# field; it is NOT an entry field (land drops it).

MODEL_FIELD_ORDER = (
    "key",                # step 1: the registry key
    "Model_path",         # step 1: local model path
    "size (M)",           # step 1: size
    "species",            # step 1: species (optional)
    "type",               # step 2: type (MLM/CLM/DL)
    "architecture",       # step 2: architecture (free text)
    "Tokenizer",          # step 2: tokenizer (canonical casing twin)
    "context_len (bp)",   # step 2: context_len (bp) (int-or-str officially)
    "huggingface",        # step 3: huggingface (free text, A5)
    "modelscope",         # step 3: modelscope (free text, A5)
    "series",             # step 3: series (free text)
    "quirks",             # step 4: quirk checklist (D-02)
)

DATASET_FIELD_ORDER = (
    "key",                # step 1: the registry key
    "Dataset_path",       # step 1: dataset path
    "Category",           # step 1: Category
    "label_column",       # step 2: label column (custom-only field)
    "Train",              # step 2: train split declaration
    "Dev",                # step 2: dev split declaration
    "Test",               # step 2: test split declaration
    "labels",             # step 2: label count
    "length",             # step 2: sequence length (optional)
    "type",               # step 3: Task_type (registry field `type`)
    "metric",             # step 3: primary metric
    "citation",           # step 4: citation (optional free text)
    "source",             # step 4: source (optional free text)
    "license",            # step 4: license (optional free text)
    "preprocessing",      # step 4: preprocessing (optional free text)
)

#: The split declarations map to fixed file names under the dataset dir
#: (the audit kernel's train/dev/test convention).
SPLIT_FILE_NAMES = (("Train", "train.csv"), ("Dev", "dev.csv"),
                    ("Test", "test.csv"))


@dataclass(frozen=True)
class ValidationSources:
    """The injected data sources every CUST-03 check resolves against.

    D-05: the validator is a pure function over ``values`` plus this
    namespace — it never reads the registries, the custom files, or the
    filesystem roots itself. The 09-04/09-05 screens construct it from
    ``registry_loader`` (official keys), ``custom_entries.read_entries``
    (existing customs), ``METRIC_REGISTRY``, and the pipeline dir; tests
    construct it from synthetic sets and tmp roots.

    Attributes:
        official_model_keys: official model registry keys (collision set).
        official_dataset_keys: official dataset registry keys.
        existing_custom_models: the existing custom model entries map
            (``{key: entry}`` — keys are the collision set).
        existing_custom_datasets: the existing custom dataset entries map.
        metric_registry: the frozen metric-name authority (defaults to
            the SUITE_CANONICAL twin METRIC_REGISTRY).
        fs_root: the root relative paths resolve against for existence
            checks (absolute paths check as-is).
        observed_species: observed species vocabulary (enum source).
        observed_tokenizers: observed tokenizer vocabulary (enum source).
    """

    official_model_keys: frozenset = frozenset()
    official_dataset_keys: frozenset = frozenset()
    existing_custom_models: dict = field(default_factory=dict)
    existing_custom_datasets: dict = field(default_factory=dict)
    metric_registry: frozenset = METRIC_REGISTRY
    fs_root: Path = PIPELINE_DIR
    observed_species: tuple = ()
    observed_tokenizers: tuple = ()


def validate_model_candidate(values, data_sources):
    """Validate one model wizard candidate, collect-ALL (D-05, CUST-03).

    The nine-check matrix, model side: required/non-empty key + name
    format; numeric type checks (size (M), bool excluded); enum
    membership (type in MLM/CLM/DL; species/Tokenizer within the
    injected observed vocabularies); key collision against official AND
    existing custom; Model_path existence under the injected fs root.
    huggingface/modelscope/series are non-empty free text (A5 — no URL
    syntax over-validation).

    Args:
        values (dict): the wizard's field values, keyed by field name
            (the registry key under ``"key"``). Any other Python shape
            yields collected problems, never an exception.
        data_sources (ValidationSources): the injected namespace (D-05).

    Returns:
        list[tuple[str, str]]: every problem as ``(field_key, message)``
        in MODEL_FIELD_ORDER; empty means the candidate passes.
    """
    sources = data_sources or ValidationSources()
    if not isinstance(values, dict):
        return [
            ("key", strings.WIZ_PROBLEM_NOT_OBJECT.format(
                type=type(values).__name__))
        ]
    problems = []
    _check_key(values, sources.official_model_keys,
               sources.existing_custom_models, problems)
    _check_required(values, "Model_path", problems)
    _check_path_exists(values.get("Model_path"), sources.fs_root,
                       "Model_path", problems)
    _check_required(values, "size (M)", problems)
    _check_numeric(values, "size (M)", problems)
    _check_enum(values, "species", sources.observed_species, problems,
                optional=True)
    _check_required(values, "type", problems)
    _check_enum(values, "type", MODEL_TYPE_VALUES, problems)
    _check_required(values, "Tokenizer", problems)
    _check_enum(values, "Tokenizer", sources.observed_tokenizers, problems)
    return problems


def validate_dataset_candidate(values, data_sources):
    """Validate one dataset wizard candidate, collect-ALL (D-05, CUST-03).

    The nine-check matrix, dataset side: required/non-empty key + name
    format; numeric type checks (Train/Dev/Test int-strict, labels/length
    numerics, bool excluded); enum membership (Category; type;
    metric in the metric registry); key collision against official AND
    existing custom; Dataset_path existence under the injected fs root;
    split-file parseability (train.csv/dev.csv/test.csv under the dataset
    dir — utf-8 csv.reader, non-empty header, header contains sequence
    AND the collected label column, malformed rows skipped like the audit
    kernel); row count > 0 per split with declared == well-formed count
    (the declaration mirrors the audit parse rule; the authoritative
    measurement stays the 09-02 subprocess).

    Args:
        values (dict): the wizard's field values, keyed by field name
            (the registry key under ``"key"``). Any other Python shape
            yields collected problems, never an exception.
        data_sources (ValidationSources): the injected namespace (D-05).

    Returns:
        list[tuple[str, str]]: every problem as ``(field_key, message)``
        in DATASET_FIELD_ORDER; empty means the candidate passes.
    """
    sources = data_sources or ValidationSources()
    if not isinstance(values, dict):
        return [
            ("key", strings.WIZ_PROBLEM_NOT_OBJECT.format(
                type=type(values).__name__))
        ]
    problems = []
    _check_key(values, sources.official_dataset_keys,
               sources.existing_custom_datasets, problems)
    _check_required(values, "Dataset_path", problems)
    dataset_dir = _check_path_exists(values.get("Dataset_path"),
                                     sources.fs_root, "Dataset_path",
                                     problems)
    _check_required(values, "Category", problems)
    _check_enum(values, "Category", DATASET_CATEGORY_VALUES, problems)
    _check_required(values, "label_column", problems)
    _check_split_fields(values, dataset_dir, problems)
    _check_required(values, "labels", problems)
    _check_numeric(values, "labels", problems)
    _check_numeric(values, "length", problems)
    _check_required(values, "type", problems)
    _check_enum(values, "type", DATASET_TYPE_VALUES, problems)
    _check_required(values, "metric", problems)
    _check_enum(values, "metric", sources.metric_registry, problems)
    return problems


# ===== Check kernels (each appends in field-definition order) =====


def _check_key(values, official_keys, existing_custom, problems):
    """Required + name-format + collision checks over the ``key`` field.

    A registry key becomes a JSON object key and flows into file names —
    it must be non-empty and must never smuggle a path separator. Both
    collision families (official AND existing custom) are checked in the
    same pass (CUST-03: the key must collide with neither official nor existing custom).
    """
    key = values.get("key")
    if not isinstance(key, str) or not key.strip():
        problems.append(("key", strings.WIZ_PROBLEM_REQUIRED))
        return
    if "/" in key or "\\" in key:
        problems.append(
            ("key", strings.WIZ_PROBLEM_KEY_FORMAT.format(key=key))
        )
    if key in official_keys:
        problems.append(
            ("key", strings.WIZ_PROBLEM_COLLISION_OFFICIAL.format(key=key))
        )
    if isinstance(existing_custom, dict) and key in existing_custom:
        problems.append(
            ("key", strings.WIZ_PROBLEM_COLLISION_CUSTOM.format(key=key))
        )


def _check_required(values, name, problems):
    """Required/non-empty check over one wizard-required field."""
    if _is_absent(values.get(name)):
        problems.append((name, strings.WIZ_PROBLEM_REQUIRED))


def _check_numeric(values, name, problems):
    """Number-tolerant numeric check, bool excluded (D-14).

    Values the required check owns (``None``/empty) are skipped — one
    field defect yields ONE problem, never a required+numeric pair.
    """
    value = values.get(name)
    if _is_absent(value):
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        problems.append(
            (name, strings.WIZ_PROBLEM_NEEDS_NUMERIC.format(
                value=_display(value)))
        )


def _check_enum(values, name, allowed, problems, optional=False):
    """Enum-membership check against a fixed or injected vocabulary.

    Skips absent values (the required check owns them; optional enums
    allow blank) and EMPTY vocabularies (nothing injected = nothing to
    check against — a partially-built source set never fails a
    candidate). Non-string values are problems (an unhashable list must
    never reach the membership test), never an exception.
    """
    if not allowed:
        return
    value = values.get(name)
    if _is_absent(value):
        return
    if not isinstance(value, str) or value not in allowed:
        problems.append(
            (name, strings.WIZ_PROBLEM_ENUM.format(
                value=_display(value), allowed=", ".join(allowed)))
        )


def _check_path_exists(raw, fs_root, field, problems):
    """Path-existence check under the injected fs root (CUST-03 check 5).

    Absolute paths check as-is (the operator-entered form); relative
    paths resolve against ``fs_root``. Advisory live checks are the
    screen's business — here the check is authoritative collect-all.

    Returns:
        Path | None: the resolved existing directory (callers use it for
        the split-file checks), or None when it does not resolve.
    """
    if not isinstance(raw, str) or not raw.strip():
        return None  # the required check owns this defect
    path = Path(raw)
    if not path.is_absolute():
        path = Path(fs_root) / path
    if not path.is_dir():
        problems.append(
            (field, strings.WIZ_PROBLEM_PATH_MISSING.format(path=raw))
        )
        return None
    return path


def _check_split_fields(values, dataset_dir, problems):
    """All checks over one trio of split-declaration fields (Train/Dev/
    Test), per field in order: int-strict numeric (always — the check is
    field-level, independent of dir resolution) then the split-file
    parse/count checks (only when the dataset dir resolved; a missing dir
    is the Dataset_path field's own problem and subsumes file noise).
    """
    label_column = values.get("label_column")
    for split_field, file_name in SPLIT_FILE_NAMES:
        declared = values.get(split_field)
        if not _is_absent(declared) and (
            isinstance(declared, bool) or not isinstance(declared, int)
        ):
            problems.append(
                (split_field, strings.WIZ_PROBLEM_NEEDS_INTEGER.format(
                    value=_display(declared)))
            )
        if dataset_dir is None:
            continue
        csv_path = dataset_dir / file_name
        counted = _count_well_formed_rows(
            csv_path, label_column, split_field, problems
        )
        if counted is None:
            continue  # parseability problem already emitted
        if counted == 0:
            problems.append((split_field, strings.WIZ_PROBLEM_SPLIT_ZERO_ROWS))
            continue
        if _is_absent(declared):
            continue  # absent declarations derive from the count
        if isinstance(declared, bool) or not isinstance(declared, int):
            continue  # the int-strict check above owns this defect
        if declared != counted:
            problems.append(
                (split_field, strings.WIZ_PROBLEM_SPLIT_COUNT_MISMATCH.format(
                    declared=declared, counted=counted))
            )


def _count_well_formed_rows(csv_path, label_column, field, problems):
    """Count well-formed rows in one split CSV, the audit kernel way.

    Args:
        csv_path (Path): the split file.
        label_column: the collected label column name (membership is
            checked only when it is a non-empty string — a blank column
            is the label-column field's own required problem).
        field (str): the field key problems attach to (the split).
        problems (list): the collect-all sink.

    Returns:
        int | None: the well-formed row count, or None when the file is
        missing/unreadable/malformed (the parseability problem has been
        appended — the authoritative measurement stays the subprocess).
    """
    if not csv_path.is_file():
        problems.append(
            (field, strings.WIZ_PROBLEM_SPLIT_FILE_MISSING.format(
                file=csv_path.name))
        )
        return None
    try:
        with open(csv_path, "r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, None)
            if header is None:
                problems.append(
                    (field, strings.WIZ_PROBLEM_SPLIT_NO_HEADER.format(
                        file=csv_path.name))
                )
                return None
            if "sequence" not in header:
                problems.append(
                    (field, strings.WIZ_PROBLEM_SPLIT_NO_SEQUENCE.format(
                        file=csv_path.name))
                )
                return None
            if (isinstance(label_column, str) and label_column
                    and label_column not in header):
                problems.append(
                    (field, strings.WIZ_PROBLEM_SPLIT_NO_LABEL_COLUMN.format(
                        column=label_column, file=csv_path.name))
                )
                return None
            count = 0
            for row in reader:
                if len(row) != len(header):
                    continue  # malformed row — skipped, not counted, not fatal
                count += 1
            return count
    except (OSError, csv.Error, UnicodeDecodeError) as exc:
        problems.append(
            (field, strings.WIZ_PROBLEM_SPLIT_UNREADABLE.format(
                file=csv_path.name, reason=exc))
        )
        return None


# ===== Import validation (D-11 validate-before-merge) =====


def load_import_schema():
    """Load the committed custom-registry entry schema (D-11).

    Returns:
        dict: the parsed ``schemas/custom_registry.json`` document.

    Raises:
        RuntimeError: the committed schema is missing or unreadable — a
            repo integrity failure (the schema is part of the code, not
            operator input), the ``templates.load_schema`` discipline.
    """
    schema = artifact_loader.load_json_artifact(IMPORT_SCHEMA_PATH)
    if not isinstance(schema, dict) or "$defs" not in schema:
        raise RuntimeError(
            f"custom_registry schema unreadable at {IMPORT_SCHEMA_PATH} — "
            "the committed schemas/custom_registry.json is the D-11 entry "
            "contract; a missing or corrupt schema is a repo integrity "
            "failure, not an input problem"
        )
    return schema


def validate_import_document(kind, doc, data_sources):
    """Validate an imported registry document, collect-ALL (D-11).

    The import gate (the run_template.json discipline over untrusted
    files): structural top-level check (plain ``{key: entry}`` map — the
    loader merge contract), then PER ENTRY in FILE order the schema
    validation (jsonschema ``Draft202012Validator`` collect-all against
    the kind's $def) plus BOTH collision families (official AND existing
    custom, each listed once). NOTHING MERGES on any problem — this
    function is pure; the 09-05 sequential gauntlet consumes the entries
    only when the problem list is empty.

    Args:
        kind (str): ``custom_entries.KIND_MODELS`` or ``KIND_DATASETS``
            (``"models"`` / ``"datasets"``).
        doc: the parsed import document (any JSON value — non-object
            shapes yield collected problems, never an exception).
        data_sources (ValidationSources): the injected namespace (D-05)
            — the official-key and existing-custom collision sets.

    Returns:
        list[tuple[str, str]]: every problem as ``(key, message)`` in
        file order (``""`` for document-level problems); empty means the
        document is importable.

    Raises:
        ValueError: ``kind`` is not one of the two registry kinds.
    """
    if kind not in IMPORT_ENTRY_DEFS:
        raise ValueError(
            f"unknown registry kind {kind!r} — expected one of "
            f"{sorted(IMPORT_ENTRY_DEFS)}"
        )
    sources = data_sources or ValidationSources()
    if not isinstance(doc, dict):
        return [
            ("", (
                f"import document must be a JSON object mapping entry "
                f"keys to entry objects, got {type(doc).__name__}"
            ))
        ]
    if not doc:
        return [("", "import document carries no entries")]
    official_keys = (
        sources.official_model_keys if kind == "models"
        else sources.official_dataset_keys
    )
    existing_custom = (
        sources.existing_custom_models if kind == "models"
        else sources.existing_custom_datasets
    )
    entry_schema = load_import_schema()["$defs"][IMPORT_ENTRY_DEFS[kind]]
    validator = jsonschema.Draft202012Validator(entry_schema)
    problems = []
    for key, entry in doc.items():  # dict order == file order
        if not isinstance(entry, dict):
            problems.append(
                (key, (
                    f"entry must be a JSON object, got "
                    f"{type(entry).__name__}"
                ))
            )
            continue
        if key in official_keys:
            problems.append(
                (key, strings.WIZ_PROBLEM_COLLISION_OFFICIAL.format(key=key))
            )
        if isinstance(existing_custom, dict) and key in existing_custom:
            problems.append(
                (key, strings.WIZ_PROBLEM_COLLISION_CUSTOM.format(key=key))
            )
        for error in validator.iter_errors(entry):
            problems.append((key, error.message))
    return problems


# ===== Small helpers =====


def _is_absent(value):
    """True when ``value`` is missing/empty — the required check's case."""
    return value is None or (isinstance(value, str) and not value.strip())


def _display(value):
    """Render a bad value for a problem message (strings verbatim)."""
    return value if isinstance(value, str) else repr(value)
