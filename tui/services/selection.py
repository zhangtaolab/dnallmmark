"""
selection — mark-set, preset, and filter-grammar service (Phase 8, 08-05).

The selection foundation's non-visual half (SEL-02/SEL-01 backing):
preset derivation from the single-source priorities file, custom-preset
persistence under the XDG config root, and the pure filter grammar the
08-07 selection screen's filter Input drives.

Contract (locked decisions):

- D-06 (presets derive, never hardcode): every preset derives from
  ``pipeline/sweep_priorities.json`` at READ time — tier-1 (the
  ``{model, task}`` pairs -> models AND tasks; a pair may omit ``task``
  — the run_sweep grammar's model-every-task spec, contributing its
  model only), tier-2 (the model-name list -> models only, no task
  inferred), and all (the passed registry key lists, registry order
  verbatim). ZERO tier model names are hardcoded here — the file is the
  single source, so tier edits require zero code changes. Preset names
  missing from the passed registry lists are returned as
  ``unknown_keys`` for loud warning surfacing (the 08-07 screen skips +
  warns) — never silently dropped; the derived models/tasks membership
  still CARRIES them (registry blindness is the registry's consumer's
  call, not this derivation's).
- SEL-02 (ordering): derivation order is deterministic — file order
  within each tier, first occurrence wins; the derivation returns
  tier-1, tier-2, all in that menu order, and ``load_custom_presets``
  yields customs sorted by name.
- SEL-02 (custom presets): saved presets persist as ``presets.json``
  under the XDG CONFIG root (D-04: ``{schema_version: 1, presets:
  {name: {models, tasks}}}``), written atomically through the 08-04
  settings helpers — the XDG STATE root is never used (check results
  live there; user-owned presets never do). Saving over an existing name
  overwrites (the confirm UX is 08-07's concern).
- Damaged priorities file: a missing, corrupt, or malformed file yields
  EMPTY presets plus a load-error signal — never an exception (the
  screen renders the signal; the operator is never blocked by a crash).
- Filter grammar (the 08-07 keyboard contract): space-separated AND
  terms; each term a bare substring (matched case-insensitively against
  the entry key plus display fields — every canonical field except the
  verbatim ``card``) or ``axis=value`` over the 08-04 canonical entry
  keys — models ``species``/``type``/``size`` (the operator-facing
  ``size`` axis maps to the ``size_m`` field), datasets
  ``category``/``type``/``metric``. Axis names are the lowercase
  vocabulary; values match as case-insensitive substrings (the k9s
  type-to-filter feel; ``size=86`` matches ``size_m`` 86.0). An unknown
  axis yields a diagnostic while valid terms still parse; results
  preserve registry order; no match is a plain empty list.
- DECOUPLED BY DESIGN: this module imports NOTHING from the registries
  service — entries and registry keys arrive as parameters (the 08-07
  screen wires the two together), keeping the grammar pure over injected
  data and testable with synthetic entries.
- ZERO textual imports (the services-tier invariant declared in
  ``tui/services/__init__.py``; locked by
  ``tests/tui/test_import_lock.py``). Dependencies: stdlib +
  ``artifact_loader`` (the D-19 tolerant read seam) + the 08-04 settings
  atomic-write helper.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

import artifact_loader  # top-level module (pipeline/ sys.path root, D-19)

from tui.services.settings import atomic_write

# ===== Preset ids (stable service ids; the 08-07 screen maps them to labels) =====

PRESET_TIER_1 = "tier-1"
PRESET_TIER_2 = "tier-2"
PRESET_ALL = "all"

# ===== Model presence vocabulary (DCL-02, 261014-dcl) =====

#: The models-column presence machine vocabulary — deliberately distinct
#: from the n_audit four-status vocabulary in ``registries.py`` (models
#: are not n_audit subjects; importing registries here would violate the
#: module's decoupling contract).
MODEL_PRESENCE_PRESENT = "present"
MODEL_PRESENCE_MISSING = "missing"
MODEL_PRESENCE_UNKNOWN = "unknown"

#: The custom-presets file name under the XDG config root (D-04).
PRESETS_FILE_NAME = "presets.json"
PRESETS_SCHEMA_VERSION = 1

# ===== Filter grammar vocabulary (the 08-07 keyboard contract) =====

#: Operator-facing axis -> canonical 08-04 entry field. The one rename:
#: the UI axis is ``size`` (UI-SPEC keyboard contract); the canonical
#: model-entry field is ``size_m``.
FILTER_AXIS_FIELDS = {
    "species": "species",
    "type": "type",
    "size": "size_m",
    "category": "category",
    "metric": "metric",
}

#: The known-axis tuple carried by unknown-axis diagnostics (sorted —
#: deterministic diagnostic content for the 08-07 warning line).
KNOWN_FILTER_AXES = tuple(sorted(FILTER_AXIS_FIELDS))


@dataclass(frozen=True)
class Preset:
    """One derived preset — pure data; the screen applies it to mark sets.

    Attributes:
        id (str): ``tier-1`` | ``tier-2`` | ``all`` — the stable service
            id (labels are the screen's business).
        models (tuple[str, ...]): the model registry keys to mark, in
            derivation (file) order — INCLUDING keys absent from the
            current registry (the screen skips + warns).
        tasks (tuple[str, ...]): the task registry keys to mark (``()``
            for tier-2 — models only).
        unknown_keys (tuple[str, ...]): every member found in the file
            but absent from the passed registry lists, in file order —
            the loud-surfacing channel (never silently dropped).
    """

    id: str
    models: tuple[str, ...]
    tasks: tuple[str, ...]
    unknown_keys: tuple[str, ...]


@dataclass(frozen=True)
class PresetDerivation:
    """The derived preset menu plus the damaged-file signal.

    Attributes:
        presets (tuple[Preset, ...]): tier-1, tier-2, all — in menu
            order; ``()`` when the priorities file is damaged.
        load_error (str | None): None on a healthy read; a message
            naming the path and every shape problem otherwise (the
            screen renders it; the derivation never raises).
    """

    presets: tuple[Preset, ...]
    load_error: "str | None"


class SubstringTerm(NamedTuple):
    """A bare-substring filter term (matched against key + display fields)."""

    text: str


class AxisTerm(NamedTuple):
    """An ``axis=value`` filter term over a canonical entry field."""

    axis: str
    value: str


class UnknownAxis(NamedTuple):
    """A parse diagnostic: the unknown axis and the known-axis vocabulary."""

    axis: str
    known_axes: tuple[str, ...]


@dataclass(frozen=True)
class ParsedFilter:
    """A parsed filter query: the valid terms plus the diagnostics.

    Attributes:
        terms (tuple[SubstringTerm | AxisTerm, ...]): the VALID terms, in
            query order — unknown-axis tokens are excluded here and
            surfaced through ``diagnostics`` instead.
        diagnostics (tuple[UnknownAxis, ...]): every unknown-axis token,
            in query order.
    """

    terms: "tuple[SubstringTerm | AxisTerm, ...]"
    diagnostics: tuple[UnknownAxis, ...]


def derive_presets(priorities_path, model_keys, task_keys):
    """Derive the preset menu from the priorities file (D-06, SEL-02).

    Args:
        priorities_path: the ``sweep_priorities.json`` file to read.
        model_keys: the current model registry keys (the overlay-merged
            view the caller loaded — this module never loads registries).
        task_keys: the current task registry keys.

    Returns:
        PresetDerivation: ``(tier-1, tier-2, all)`` presets in menu order
        with unknown-key surfacing, or empty presets plus a load-error
        message when the file is missing, corrupt, or malformed (the
        committed shape is exactly two tiers: tier-1 a list of
        ``{model, task}`` string pairs — ``task`` may be omitted, the
        run_sweep ``--priority-file`` grammar's model-every-task spec
        that ``tiers_to_template`` also accepts, contributing the model
        only — and tier-2 a list of model-name strings) — never an
        exception.
    """
    path = Path(priorities_path)
    doc = artifact_loader.load_json_artifact(path)
    if doc is None:
        return PresetDerivation(
            presets=(),
            load_error=f"sweep_priorities unreadable or not valid JSON: {path}",
        )
    problems = []
    if not isinstance(doc, list):
        problems.append(
            "sweep_priorities must be a JSON list of exactly two tiers, "
            f"got {type(doc).__name__}"
        )
        doc = []
    if len(doc) != 2:
        problems.append(
            "sweep_priorities must carry exactly two tiers (tier-1 pairs, "
            f"tier-2 names), got {len(doc)}"
        )
    pairs, names = [], []
    if len(doc) >= 1 and isinstance(doc[0], list):
        for index, entry in enumerate(doc[0]):
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("model"), str)
                or not (
                    entry.get("task") is None
                    or isinstance(entry.get("task"), str)
                )
            ):
                problems.append(
                    f"tier-1 entry {index} is not a {{model, task}} pair "
                    f"of strings: {entry!r}"
                )
            else:
                # ``task`` may be omitted (None) — the run_sweep
                # --priority-file grammar's model-every-task spec, the
                # same shape ``tiers_to_template`` accepts (WR-03); the
                # pair then contributes its model only
                pairs.append((entry["model"], entry.get("task")))
    elif len(doc) >= 1:
        problems.append("tier-1 must be a list of {model, task} pairs")
    if len(doc) >= 2 and isinstance(doc[1], list):
        for index, entry in enumerate(doc[1]):
            if not isinstance(entry, str):
                problems.append(
                    f"tier-2 entry {index} is not a model-name string: "
                    f"{entry!r}"
                )
            else:
                names.append(entry)
    elif len(doc) >= 2:
        problems.append("tier-2 must be a list of model-name strings")
    if problems:
        return PresetDerivation(
            presets=(),
            load_error=f"sweep_priorities damaged at {path}: "
            + "; ".join(problems),
        )

    model_key_set = set(model_keys)
    task_key_set = set(task_keys)
    tier1_models, tier1_tasks, tier1_unknown = [], [], []
    for model, task in pairs:
        _append_unique(tier1_models, model)
        if model not in model_key_set:
            _append_unique(tier1_unknown, model)
        if task is not None:
            # an omitted task is the model's-every-task spec — the preset
            # marks the model only, no task inferred (WR-03, the same
            # derivation tiers_to_template performs)
            _append_unique(tier1_tasks, task)
            if task not in task_key_set:
                _append_unique(tier1_unknown, task)
    tier2_models, tier2_unknown = [], []
    for name in names:
        _append_unique(tier2_models, name)
        if name not in model_key_set:
            _append_unique(tier2_unknown, name)
    return PresetDerivation(
        presets=(
            Preset(
                id=PRESET_TIER_1,
                models=tuple(tier1_models),
                tasks=tuple(tier1_tasks),
                unknown_keys=tuple(tier1_unknown),
            ),
            Preset(
                id=PRESET_TIER_2,
                models=tuple(tier2_models),
                tasks=(),
                unknown_keys=tuple(tier2_unknown),
            ),
            Preset(
                id=PRESET_ALL,
                models=tuple(model_keys),
                tasks=tuple(task_keys),
                unknown_keys=(),
            ),
        ),
        load_error=None,
    )


def save_custom_preset(name, models, tasks, config_dir):
    """Save (or atomically overwrite) a custom preset under the config root.

    Sets are stored as sorted unique lists — the same selection always
    produces the same file bytes. A missing/corrupt existing file starts
    fresh (the user-owned advisory file, T-08-06); saving over an
    existing name overwrites.

    Args:
        name (str): the preset name (the key in ``presets``).
        models: the selected model keys (any iterable — stored sorted).
        tasks: the selected task keys (any iterable — stored sorted).
        config_dir: the XDG config root (the 08-04 settings
            ``config_dir()``; injected so tests point at tmp_path).
    """
    root = Path(config_dir)
    presets = _read_custom_presets(root)
    presets[name] = {
        "models": sorted(set(models)),
        "tasks": sorted(set(tasks)),
    }
    payload = {
        "schema_version": PRESETS_SCHEMA_VERSION,
        "presets": presets,
    }
    atomic_write(
        root / PRESETS_FILE_NAME,
        json.dumps(payload, indent=4, ensure_ascii=False),
    )


def load_custom_presets(config_dir):
    """Load the saved custom presets (SEL-02).

    Tolerant by design (the file is user-owned advisory data, T-08-06):
    a missing root/file, corrupt JSON, an unknown ``schema_version``, or
    a malformed individual preset degrades to fewer presets — never an
    exception. Names yield in sorted order (the menu's custom tail).

    Args:
        config_dir: the XDG config root.

    Returns:
        dict: ``{name: {"models": [...], "tasks": [...]}}`` — the empty
        mapping when nothing is saved (the documented empty state the
        08-07 screen renders).
    """
    raw = _read_custom_presets(Path(config_dir))
    result = {}
    for name in sorted(raw):
        value = raw[name]
        if _is_preset_value(value):
            result[name] = {
                "models": list(value["models"]),
                "tasks": list(value["tasks"]),
            }
    return result


def parse_filter_query(query):
    """Parse a filter query into terms plus diagnostics.

    Grammar: whitespace-separated terms; a term containing ``=`` is an
    ``axis=value`` term (partitioned on the FIRST ``=``; axis names are
    the lowercase ``FILTER_AXIS_FIELDS`` vocabulary), otherwise a bare
    substring. Unknown-axis tokens become diagnostics and are EXCLUDED
    from the applied terms — valid terms still parse.

    Args:
        query (str): the raw filter input (``""`` parses to nothing).

    Returns:
        ParsedFilter: the valid terms and the diagnostics, each in query
        order.
    """
    terms, diagnostics = [], []
    for token in query.split():
        if "=" in token:
            axis, _, value = token.partition("=")
            if axis in FILTER_AXIS_FIELDS:
                terms.append(AxisTerm(axis, value))
            else:
                diagnostics.append(UnknownAxis(axis, KNOWN_FILTER_AXES))
        else:
            terms.append(SubstringTerm(token))
    return ParsedFilter(terms=tuple(terms), diagnostics=tuple(diagnostics))


def apply_filter(entries, terms):
    """Apply parsed filter terms to entry lists — pure, order-preserving.

    AND semantics: an entry survives only when EVERY term matches.
    Matching is case-insensitive: a bare substring against the str of
    every canonical field except ``card`` (the key included — it is a
    field); an axis term against the str of its mapped field (an entry
    whose kind lacks the field never matches; ``size`` maps to
    ``size_m``). Registry order is preserved verbatim.

    Args:
        entries (list[dict]): canonical 08-04 entries (injected — this
            module never loads registries).
        terms: the ``ParsedFilter.terms`` tuple (empty -> every entry).

    Returns:
        list[dict]: the matching entries, original order; a plain empty
        list when nothing matches (the 08-07 empty-state row).
    """
    return [
        entry for entry in entries
        if all(_entry_matches(entry, term) for term in terms)
    ]


def _read_custom_presets(config_root):
    """The raw presets mapping (tolerant) — {} on any unreadable shape.

    Args:
        config_root (Path): the config root directory.

    Returns:
        dict: the file's ``presets`` mapping, verbatim (per-preset shape
        validation is ``load_custom_presets``'s business; ``save`` only
        needs the mapping to merge into).
    """
    doc = artifact_loader.load_json_artifact(
        Path(config_root) / PRESETS_FILE_NAME
    )
    if not isinstance(doc, dict):
        return {}
    version = doc.get("schema_version")
    if version is not None and version != PRESETS_SCHEMA_VERSION:
        return {}
    presets = doc.get("presets")
    if not isinstance(presets, dict):
        return {}
    return presets


def _is_preset_value(value):
    """True when ``value`` is a ``{models, tasks}`` preset of string lists."""
    if not isinstance(value, dict):
        return False
    models = value.get("models")
    tasks = value.get("tasks")
    return _is_string_list(models) and _is_string_list(tasks)


def _is_string_list(value):
    """True when ``value`` is a list of strings."""
    return isinstance(value, list) and all(
        isinstance(item, str) for item in value
    )


def _entry_matches(entry, term):
    """True when one entry satisfies one filter term.

    Unknown term kinds and unmapped axes never match (defensive — parse
    only produces the two known kinds over known axes).
    """
    if isinstance(term, SubstringTerm):
        return _matches_substring(entry, term.text)
    if isinstance(term, AxisTerm):
        return _matches_axis(entry, term)
    return False


def _matches_substring(entry, text):
    """Case-insensitive substring over key + display fields (never card)."""
    needle = text.lower()
    for key, value in entry.items():
        if key == "card" or value is None:
            continue
        if needle in str(value).lower():
            return True
    return False


def _matches_axis(entry, term):
    """Case-insensitive substring over the term's mapped field value."""
    field = FILTER_AXIS_FIELDS.get(term.axis)
    if field is None:
        return False
    value = entry.get(field)
    if value is None:
        return False
    return term.value.lower() in str(value).lower()


def _append_unique(target, value):
    """Append ``value`` to ``target`` unless already present (first wins)."""
    if value not in target:
        target.append(value)


def model_presence(entries, base_dir, is_dir=None):
    """Decide per-model local download presence under ``base_dir``.

    The models-table presence decision (DCL-02, 261014-dcl): for each
    canonical entry, the registry ``Model_path`` joins the base
    VERBATIM — ``str(base_dir).rstrip(os.sep) + os.sep + value``, the
    value keeping its own ``models/`` prefix — exactly the
    ``pipeline/run_finetune`` model_base + Model_path semantics, so
    ``base_dir`` is a pipeline/-equivalent storage root. An entry whose
    card carries no usable ``Model_path`` string maps to UNKNOWN (never
    an exception). PRESENTATION ONLY split: this service DECIDES (pure
    machine vocabulary); the screen maps statuses to words.

    Args:
        entries (list[dict]): canonical model entries (injected — this
            module never loads registries).
        base_dir (str | Path): the effective model storage root (the
            run-config root when configured, the committed pipeline
            dir otherwise — the caller resolves and injects).
        is_dir (callable | None): the directory-existence seam; None
            means the real filesystem check (``os.path.isdir``). The
            parameter is the test/injection seam.

    Returns:
        dict[str, str]: entry key -> one of ``MODEL_PRESENCE_PRESENT`` /
        ``MODEL_PRESENCE_MISSING`` / ``MODEL_PRESENCE_UNKNOWN``.
    """
    if is_dir is None:
        is_dir = os.path.isdir
    base = str(base_dir).rstrip(os.sep) + os.sep
    statuses: dict[str, str] = {}
    for entry in entries:
        value = entry.get("card", {}).get("Model_path")
        if not isinstance(value, str) or not value:
            statuses[entry["key"]] = MODEL_PRESENCE_UNKNOWN
            continue
        statuses[entry["key"]] = (
            MODEL_PRESENCE_PRESENT if is_dir(base + value)
            else MODEL_PRESENCE_MISSING
        )
    return statuses
