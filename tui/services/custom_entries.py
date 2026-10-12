"""
custom_entries — the user-owned custom-registry store (Phase 9, 09-01,
CUST-01/02/06; D-08/D-11/D-12).

The ONLY write seam over the user-owned custom registries
(``~/.config/dnallmmark/custom_models.json`` /
``custom_datasets.json``): read (tolerant, management-view direct —
Pitfall 7), gauntlet-land, session-undo, enabled-toggle. Everything the
09-04/09-05 wizard screens and the 09-02 gauntlet do is orchestration
over these functions; every later custom-registry write joins here, never
beside it (D-08: one write seam, zero torn-file paths).

Contract (locked decisions):

- D-08 (gauntlet-all-pass-before-land): this module performs NO
  validation and runs NO gauntlet — callers land only after the collect-
  all validator and the 09-02 subprocess gauntlet both pass. Because a
  failed gauntlet never calls ``land``, a failed entry is never written
  (zero-rollback by construction); ``undo`` reverses a JUST-landed entry
  within the same session.
- D-11 (import/export at the service tier): the custom registry FILE is
  the share unit — export is a verbatim byte copy, import validates
  before any merge (the import readers land with the schema task).
- D-12 (add-only): entries are landed and removed as whole keys; there is
  no edit path (edit = undo + re-record through the wizard).
- Store shape (the registry_loader merge contract): the file top level
  stays a PLAIN ``{key: entry}`` map — no envelope key. The loader merges
  EVERY top-level key as a registry entry, so an envelope (e.g.
  ``{"schema_version": 1, "entries": {...}}``) would either collide with
  an official key or become a garbage entry (the 09-RESEARCH
  anti-pattern).
- Path normalization (Pitfall 4): ``run_finetune.py`` resolves
  ``Model_path``/``Dataset_path`` by STRING CONCATENATION over the
  pipeline dir, so landed rows carry pipeline-RELATIVE paths — ``land``
  converts an absolute operator path via ``os.path.relpath`` against the
  pipeline dir. A landed path starting with a filesystem root is a bug.
- Name stamps (Pitfall 6/11): ``run_finetune.py`` reads
  ``row["Dataset_name"]`` with DIRECT key access and ``run_sweep.py``
  aligns ``Dataset_name`` with the registry key — ``land`` stamps
  ``Model_name=key`` (models) and ``Dataset_name=key`` (datasets), and
  lands ``Train``/``Dev``/``Test`` as ints (bool excluded from every
  numeric coercion, the D-14 discipline).
- D-09 (enabled semantics): ``set_enabled`` writes the LITERAL JSON
  boolean into the entry; absence means enabled. Reads never rewrite
  entries that lack the field (the loader-side skip lands in 09-02).
- T-09-03 (write authorization): no code path here targets the official
  ``pipeline/{models,datasets}_info.json`` — writes resolve exclusively
  under ``settings.config_dir()`` through ``settings.atomic_write``
  (binding constraint 11, the cardinal separation).

ZERO textual imports (the services-tier invariant declared in
``tui/services/__init__.py``; locked by
``tests/tui/test_import_lock.py``). Dependencies: stdlib +
``artifact_loader`` (the D-19 tolerant seam) + ``registry_loader`` (the
file-name twins) + ``tui.services.settings`` (the D-04 config root +
atomic-write rails — no new path or write code).
"""

import json
import os
from pathlib import Path

import artifact_loader  # top-level module (pipeline/ sys.path root, D-19)
import registry_loader  # top-level module (pipeline/ sys.path root, D-02)

from tui.services import settings

# ===== Kinds and file names (the registry_loader CUSTOM_*_NAME twins) =====
#
# The file names are IMPORTED from the loader (not retyped) so the store
# and the overlay reader can never diverge on what the file is called —
# the tracer seam depends on the identical name resolving on both sides.

KIND_MODELS = "models"
KIND_DATASETS = "datasets"

KIND_FILE_NAMES = {
    KIND_MODELS: registry_loader.CUSTOM_MODELS_NAME,
    KIND_DATASETS: registry_loader.CUSTOM_DATASETS_NAME,
}

# ===== Locations (resolved from this module's own file, never CWD) =====

REPO_ROOT = Path(__file__).resolve().parents[2]
#: Landed ``Model_path``/``Dataset_path`` values are stored relative to
#: the pipeline dir — the base ``run_finetune.py`` string-concatenates
#: against (Pitfall 4).
PIPELINE_DIR = REPO_ROOT / "pipeline"

#: The official registries — the never-written cardinal files (T-09-03).
OFFICIAL_REGISTRY_PATHS = (
    PIPELINE_DIR / registry_loader.MODELS_INFO_NAME,
    PIPELINE_DIR / registry_loader.DATASETS_INFO_NAME,
)


def custom_registry_path(kind):
    """Resolve the user-owned custom-registry file path for ``kind``.

    The file lives under ``settings.config_dir()`` (the D-04 XDG config
    root — the same root the pipeline-side resolver yields on Linux), so
    a file written here is what ``registry_loader`` reads through
    ``custom_registry_dir()`` when both resolve the default root.

    Args:
        kind (str): ``KIND_MODELS`` or ``KIND_DATASETS``.

    Returns:
        Path: the custom-registry file path (may not exist yet — absence
        is the D-06 byte-identity case and no read creates it).

    Raises:
        ValueError: ``kind`` is not one of the two kinds.
    """
    if kind not in KIND_FILE_NAMES:
        raise ValueError(
            f"unknown registry kind {kind!r} — expected one of "
            f"{sorted(KIND_FILE_NAMES)}"
        )
    return settings.config_dir() / KIND_FILE_NAMES[kind]


def read_entries(kind):
    """Read the user-owned custom registry tolerantly (Pitfall 7).

    The MANAGEMENT-VIEW direct read: unlike ``registry_loader`` (which
    hides ``enabled: false`` entries once the D-09 skip lands), this read
    returns every landed entry regardless of enabled state — you cannot
    re-enable what you cannot see. Absence creates no file and is NOT an
    error (the empty edge); a present-but-unreadable file yields an error
    message, never an exception.

    Args:
        kind (str): ``KIND_MODELS`` or ``KIND_DATASETS``.

    Returns:
        tuple[dict, str | None]: ``(entries, None)`` — the plain
        ``{key: entry}`` map (``{}`` when the file is absent) — or
        ``({}, message)`` when the file exists but is unreadable or its
        top level is not a JSON object.
    """
    path = custom_registry_path(kind)
    if not path.is_file():
        return {}, None
    doc = artifact_loader.load_json_artifact(path)
    if doc is None:
        return {}, f"custom registry file unreadable or not valid JSON: {path}"
    if not isinstance(doc, dict):
        return {}, (
            f"custom registry top level must be a JSON object mapping "
            f"entry keys to entry objects: {path}"
        )
    return doc, None


def land(kind, key, entry):
    """Land one validated entry into the user-owned registry (D-08).

    Normalizes before the write (Pitfall 4/6/11): an absolute
    ``Model_path``/``Dataset_path`` becomes pipeline-relative via
    ``os.path.relpath``; ``Model_name=key`` (models) /
    ``Dataset_name=key`` (datasets) are stamped; ``Train``/``Dev``/``Test``
    coerce to int (bool excluded — a bool is never coerced). The wizard's
    ``key`` form field, when it rides along inside ``entry``, is dropped:
    the landed entry shape mirrors the official field set plus the
    custom-only fields, and ``key`` is not one of them.

    This function performs NO validation — the caller has already run the
    collect-all validator and the 09-02 gauntlet (D-08).

    Args:
        kind (str): ``KIND_MODELS`` or ``KIND_DATASETS``.
        key (str): the registry key (must be collision-free — the
            validator's job upstream).
        entry (dict): the field values for the entry.

    Returns:
        Path: the registry file written (the land-toast's ``{path}``).

    Raises:
        ValueError: the existing registry file is unreadable — a
            read-modify-write over a corrupt file is refused loudly (the
            tolerant read is for the management view; the write seam is
            strict).
    """
    entries, error = read_entries(kind)
    if error is not None:
        raise ValueError(f"cannot land into an unreadable registry: {error}")
    entries[key] = _normalize_entry(kind, key, entry)
    return _write_entries(kind, entries)


def undo(kind, key):
    """Remove one key from the user-owned registry (session undo, D-08).

    Reverses a JUST-landed entry within the same session (the wizard's
    ``[u]`` affordance). Removing an absent key — or an absent/corrupt
    file — is a no-op returning False, never an error (undo is the
    safety net; it must not develop its own failure modes).

    Args:
        kind (str): ``KIND_MODELS`` or ``KIND_DATASETS``.
        key (str): the registry key to remove.

    Returns:
        bool: True when the key was removed and the file rewritten.
    """
    entries, error = read_entries(kind)
    if error is not None or key not in entries:
        return False
    del entries[key]
    _write_entries(kind, entries)
    return True


def set_enabled(kind, key, enabled):
    """Write the literal ``enabled`` boolean into one entry (D-09).

    Absence means enabled (the 09-02 loader contract); only the literal
    JSON boolean disables. Reads never rewrite entries lacking the field
    — this toggle is the one sanctioned way the field appears.

    Args:
        kind (str): ``KIND_MODELS`` or ``KIND_DATASETS``.
        key (str): the registry key to toggle.
        enabled (bool): the literal boolean to store (coerced via
            ``bool()`` so JSON true/false is guaranteed).

    Returns:
        bool: True when the entry was found and the file rewritten.
    """
    entries, error = read_entries(kind)
    if error is not None:
        return False
    entry = entries.get(key)
    if not isinstance(entry, dict):
        return False
    entry["enabled"] = bool(enabled)
    _write_entries(kind, entries)
    return True


# ===== Internal: normalization + the single write rail =====


def _normalize_entry(kind, key, entry):
    """Apply the land-time normalization (Pitfall 4/6/11) to one entry.

    Args:
        kind (str): ``KIND_MODELS`` or ``KIND_DATASETS``.
        key (str): the registry key being landed.
        entry (dict): the raw field values from the caller.

    Returns:
        dict: a NEW dict (the caller's dict is never mutated) with
        pipeline-relative paths, the name stamp, and int split counts.
    """
    landed = dict(entry) if isinstance(entry, dict) else {}
    landed.pop("key", None)  # the wizard form key never lands as a field
    path_field = (
        "Model_path" if kind == KIND_MODELS else "Dataset_path"
    )
    raw_path = landed.get(path_field)
    if isinstance(raw_path, str) and raw_path and os.path.isabs(raw_path):
        landed[path_field] = os.path.relpath(raw_path, PIPELINE_DIR)
    name_field = "Model_name" if kind == KIND_MODELS else "Dataset_name"
    landed[name_field] = key
    for split in ("Train", "Dev", "Test"):
        if split in landed:
            landed[split] = _coerce_split_int(landed[split])
    return landed


def _coerce_split_int(value):
    """Coerce one declared split count to int (bool excluded, D-14).

    Accepts a non-bool int, an integral float, or a digit string; any
    other value (a bool included) is returned UNCHANGED so a bad
    declaration stays visible instead of being silently transformed —
    validation upstream is what refuses it.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return value
    return value


def _write_entries(kind, entries):
    """Persist the entries map through the ONE write rail (T-08-03).

    Args:
        kind (str): ``KIND_MODELS`` or ``KIND_DATASETS``.
        entries (dict): the complete plain ``{key: entry}`` map.

    Returns:
        Path: the registry file written.
    """
    path = custom_registry_path(kind)
    settings.atomic_write(path, json.dumps(entries, indent=4, ensure_ascii=False))
    return path
