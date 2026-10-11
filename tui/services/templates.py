"""
templates — run-configuration template service (Phase 8, 08-05).

The one-way-contract service (D-07, SEL-03): strict schema validation with
collect-all problem listing for operator-shared template JSON, template
export that is valid by construction, and the pure ``sweep_priorities``
tier interop pair.

Contract (locked decisions):

- D-07 (one-way, ratified 2026-10-11): ``schemas/run_template.json`` is the
  published contract — strict draft 2020-12, ``additionalProperties: false``
  at every object level, top-level ``schema_version`` const 1, ``$id`` under
  the repo schemas URL. The field set, the GA semantics (GA = max(1,
  effective_batch // batch_size), maintainer default 16, small-model batch
  64 -> GA 1), and the ratification provenance live in the schema's own
  ``$comment``, next to the fields they govern. Field names are FROZEN:
  templates are shared between operators and the Phase 11 run-config screen
  consumes the same schema — no renames after landing.
- SEL-03 (fail-fast collect-all): ``validate_template`` collects EVERY
  problem in one pointer-ordered list — never one error at a time — so a
  failed import changes no state (validation completes before any caller
  applies marks; the caller applies nothing unless the list is empty).
- SEL-03 (empty edge): models/tasks carry ``minItems: 1`` — an empty
  selection can neither be imported (validation problem) nor exported
  (``export_selection_template`` refuses loudly); ``effective_batch_size``
  carries minimum 1.
- SEL-03 (tier interop): ``template_to_tiers`` / ``tiers_to_template`` are
  a pure-function pair over the ``pipeline/sweep_priorities.json`` list
  shape — the run_sweep ``--priority-file`` grammar (an ordered list of
  tiers; each entry a bare model name, covering the model's every task, or
  a ``{model, task}`` spec that may omit ``task``). A template is a
  cross-product selection, so its faithful priorities encoding is one tier
  of explicit pairs (a bare name would cover the model's UNSELECTED tasks
  too); both compositions preserve model and task MEMBERSHIP exactly.
  Registry membership is out of scope here (registry-blind): the selection
  service surfaces unknown keys against the registries (D-06).
- D-06 (zero hardcoding): no tier model name appears in this module —
  ``pipeline/sweep_priorities.json`` is the single source; tier edits
  require zero code changes.
- T-08-04 (pure data): a template is never evaluated — no code path
  executes strings from a template; strict validation is the only import
  gate.
- IO discipline: template-file reads go through ``artifact_loader``'s
  tolerant None sentinel (existence diagnostics only); import validation
  itself is strict and separate. Reads never touch user state; this
  service persists nothing (exports are returned as dicts — the caller
  writes operator-chosen paths).

ZERO textual imports (the services-tier invariant declared in
``tui/services/__init__.py``; locked by
``tests/tui/test_import_lock.py``). Dependencies: stdlib + jsonschema (the
dev/CI test and typecheck lanes carry it; see the 08-05 SUMMARY for the
[tui]-runtime wiring note) + ``artifact_loader`` (the D-19 tolerant seam).
"""

from pathlib import Path

import artifact_loader  # top-level module (pipeline/ sys.path root, D-19)
import jsonschema

# ===== Locations (resolved from this module's own file, never CWD) =====

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "run_template.json"

# ===== Ratified defaults (mirrored from the schema's property annotations) =====

DEFAULT_SEEDS = (42, 43, 44)
DEFAULT_PEFT = "none"
DEFAULT_CONFIG_VARIANT = "default"

#: The complete exportable parameter vocabulary — every key outside this
#: set is a loud error in ``export_selection_template`` (nothing is
#: silently dropped from an exported, shareable document).
_EXPORT_PARAM_KEYS = frozenset({
    "seeds",
    "peft",
    "config_variant",
    "curve_fractions",
    "subset_file",
    "effective_batch_size",
    "num_train_epochs",
    "cache_dir",
})

#: The optional fields, emitted only when present in params.
_OPTIONAL_DOC_KEYS = (
    "curve_fractions",
    "subset_file",
    "effective_batch_size",
    "num_train_epochs",
    "cache_dir",
)


def load_schema():
    """Load the committed strict run-template schema (D-07).

    Returns:
        dict: the parsed ``schemas/run_template.json`` document.

    Raises:
        RuntimeError: the committed schema is missing or unreadable — that
            is a repo integrity failure (the schema is part of the code,
            not operator input), so it fails loudly instead of degrading.
    """
    schema = artifact_loader.load_json_artifact(SCHEMA_PATH)
    if not _is_json_object(schema):
        raise RuntimeError(
            f"run_template schema unreadable at {SCHEMA_PATH} — the "
            "committed schemas/run_template.json is the D-07 contract; a "
            "missing or corrupt schema is a repo integrity failure, not an "
            "input problem"
        )
    return schema


def validate_template(doc):
    """Validate a template document against the strict D-07 schema.

    Collect-ALL (SEL-03): every problem is collected in ONE call — the
    import flow surfaces them together (numbered, pointer-ordered) and
    applies nothing unless the list is empty. Untrusted input of any shape
    (None, lists, strings) yields collected problems, never an exception.

    Args:
        doc: the parsed template document (any JSON value).

    Returns:
        list[tuple[str, str]]: every problem as ``(json_pointer, message)``
        — RFC 6901 pointers (``/models``, ``/seeds/0``; the empty string
        for document-root problems), jsonschema's message verbatim —
        sorted by pointer (then message) so the list is deterministic. An
        empty list means the document is a valid run template.
    """
    validator = jsonschema.Draft202012Validator(load_schema())
    problems = [
        (_json_pointer(error.absolute_path), error.message)
        for error in validator.iter_errors(doc)
    ]
    return sorted(problems)


def export_selection_template(models, tasks, params=None):
    """Build a schema-valid run-template document from a selection.

    Defaults materialize (a minimal export is fully explicit and
    self-describing): seeds ``[42, 43, 44]``, peft ``"none"``,
    config_variant ``"default"``. Models/tasks dedupe preserving first
    occurrence. Valid by construction: the built document is validated
    before it is returned, so an export can never emit a document another
    operator's import would reject.

    Args:
        models: the selected model registry keys (any iterable).
        tasks: the selected task registry keys (any iterable).
        params (dict | None): optional overrides — exactly the
            ``_EXPORT_PARAM_KEYS`` vocabulary; an unknown key is a loud
            error (never a silent drop from a shareable file).

    Returns:
        dict: the run-template document (schema-valid, incl.
        ``schema_version`` 1).

    Raises:
        ValueError: empty models or tasks (the SEL-03 empty edge — an
            empty selection cannot be exported); an unknown params key; or
            params values that would make the document invalid (the
            collect-all problem list is included in the message).
    """
    merged = dict(params) if params else {}
    unknown = sorted(set(merged) - _EXPORT_PARAM_KEYS)
    if unknown:
        raise ValueError(
            f"unknown template params {unknown} — exportable keys are "
            f"{sorted(_EXPORT_PARAM_KEYS)}; nothing is silently dropped "
            "from an exported template"
        )
    model_list = list(dict.fromkeys(models))
    task_list = list(dict.fromkeys(tasks))
    if not model_list or not task_list:
        raise ValueError(
            "an empty selection cannot be exported as a run template — "
            "models and tasks each need at least one entry (the schema's "
            "minItems 1)"
        )
    doc = {
        "schema_version": 1,
        "models": model_list,
        "tasks": task_list,
        "seeds": list(merged.get("seeds", DEFAULT_SEEDS)),
        "peft": merged.get("peft", DEFAULT_PEFT),
        "config_variant": merged.get("config_variant", DEFAULT_CONFIG_VARIANT),
    }
    for key in _OPTIONAL_DOC_KEYS:
        if merged.get(key) is not None:
            doc[key] = merged[key]
    problems = validate_template(doc)
    if problems:
        raise ValueError(
            "the export parameters produce an invalid template: "
            + "; ".join(f"{pointer}: {message}" for pointer, message in problems)
        )
    return doc


def load_template_file(path):
    """Read a template file tolerantly, for existence diagnostics only.

    Import VALIDATION is strict and separate (``validate_template``): this
    helper only distinguishes a parsed document from a missing/corrupt
    file, never raising — the import flow surfaces the message alongside
    any validation problems.

    Args:
        path: the template file to read.

    Returns:
        tuple[object | None, str | None]: ``(doc, None)`` on a successful
        read; ``(None, message)`` when the file is missing or not valid
        JSON.
    """
    target = Path(path)
    if not target.exists():
        return None, f"template file not found: {target}"
    doc = artifact_loader.load_json_artifact(target)
    if doc is None:
        return None, f"template file unreadable or not valid JSON: {target}"
    return doc, None


def template_to_tiers(template):
    """Convert a run template into the sweep_priorities tier-list shape.

    A template is a cross-product selection (every selected model over
    every selected task), so the faithful priorities encoding is ONE tier
    of explicit ``{model, task}`` pairs, models-major (a bare model name
    would cover the model's UNSELECTED tasks too). The output is a valid
    ``run_sweep --priority-file`` document.

    Args:
        template (dict): a template document carrying string-list
            ``models``/``tasks`` (validate first — see ``validate_template``).

    Returns:
        list: ``[[{"model": m, "task": t}, ...]]`` — one tier of the full
        cross-product, model order outermost.

    Raises:
        ValueError: ``template`` is not an object, or its models/tasks are
            not lists of strings.
    """
    models = _string_list_field(template, "models")
    tasks = _string_list_field(template, "tasks")
    return [
        [
            {"model": model, "task": task}
            for model in models
            for task in tasks
        ]
    ]


def tiers_to_template(tiers, params=None):
    """Convert a sweep_priorities tier list into a run template.

    Grammar (the run_sweep ``--priority-file`` shape): an ordered list of
    tiers; each tier a list of entries that are either bare model-name
    strings or ``{model, task}`` specs (a spec may omit ``task`` — the
    model's every task; no task is INFERRED here, registry knowledge is
    out of scope for the interop). Membership collects tier order then
    entry order, first occurrence wins — deterministic derivation from the
    file (D-06).

    Args:
        tiers (list): the parsed priorities document (list of tiers).
        params (dict | None): optional template params — the same
            vocabulary as ``export_selection_template``.

    Returns:
        dict: the run-template document (schema-valid).

    Raises:
        ValueError: ``tiers`` is not a list of tiers; an entry is neither
            a bare name nor a valid ``{model, task}`` spec (the message
            names the tier and entry position); or the tiers carry no
            task-bearing entry (a template's tasks field needs at least
            one — a bare-name-only tiers file cannot be represented).
    """
    if not _is_json_list(tiers):
        raise ValueError(
            f"tiers must be a JSON list of tiers, got {type(tiers).__name__}"
        )
    models, tasks = [], []
    for tier_index, tier in enumerate(tiers):
        if not _is_json_list(tier):
            raise ValueError(f"tier {tier_index} is not a list: {tier!r}")
        for entry_index, entry in enumerate(tier):
            where = f"tier {tier_index} entry {entry_index}"
            if _is_json_string(entry):
                _append_unique(models, entry)
                continue
            if not _is_json_object(entry):
                raise ValueError(
                    f"{where} is neither a bare model name nor a "
                    f"{{model, task}} spec: {entry!r}"
                )
            model = entry.get("model")
            if not _is_json_string(model):
                raise ValueError(
                    f"{where} is missing the 'model' key of its "
                    "{model, task} spec"
                )
            task = entry.get("task")
            if task is not None and not _is_json_string(task):
                raise ValueError(f"{where} has a non-string 'task': {task!r}")
            _append_unique(models, model)
            if task is not None:
                _append_unique(tasks, task)
    if not tasks:
        raise ValueError(
            "the tiers file carries no {model, task} pair — a run template "
            "requires at least one task (the schema's minItems 1); a "
            "bare-name-only tiers file cannot be represented as a template"
        )
    return export_selection_template(models, tasks, params)


def _json_pointer(path_segments):
    """Render jsonschema's absolute path as an RFC 6901 JSON pointer.

    Args:
        path_segments: the error's ``absolute_path`` segments (integers
            index into arrays; strings name object properties).

    Returns:
        str: ``""`` for the document root, else ``/models``,
        ``/seeds/0``-style pointers with ``~`` and ``/`` escaped.
    """
    escaped = [
        str(segment).replace("~", "~0").replace("/", "~1")
        for segment in path_segments
    ]
    return "/" + "/".join(escaped) if escaped else ""


# ===== JSON-shape predicates =====
#
# Named wrappers (not bare isinstance) at every raise site: these are
# DATA-shape checks over parsed JSON, so ValueError is the semantically
# correct error (the export_runs.py discipline: ValueError for parse/shape
# failures, TypeError for wrong-typed Python arguments) — and the named
# predicate keeps the check readable at each site.


def _is_json_object(value):
    """True when ``value`` is a JSON object (a dict)."""
    return isinstance(value, dict)


def _is_json_list(value):
    """True when ``value`` is a JSON list."""
    return isinstance(value, list)


def _is_json_string(value):
    """True when ``value`` is a JSON string."""
    return isinstance(value, str)


def _is_string_list(value):
    """True when ``value`` is a JSON list of JSON strings."""
    return _is_json_list(value) and all(
        _is_json_string(item) for item in value
    )


def _string_list_field(template, field):
    """Extract a string-list field from a template, loudly.

    Args:
        template: the template document.
        field (str): the field name.

    Returns:
        list[str]: the field's value.

    Raises:
        ValueError: the template is not an object, or the field is not a
            list of strings.
    """
    if not _is_json_object(template):
        raise ValueError(
            f"template must be an object, got {type(template).__name__}"
        )
    value = template.get(field)
    if not _is_string_list(value):
        raise ValueError(
            f"template field {field!r} must be a list of strings — validate "
            "the template before tier conversion"
        )
    return value


def _append_unique(target, value):
    """Append ``value`` to ``target`` unless already present (first wins)."""
    if value not in target:
        target.append(value)
