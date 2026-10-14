"""
registries — the registry-view service (Phase 8; 08-03 tracer, 08-04
entry view + presence expansion).

The FIRST module on the tui → pipeline seam, landed as the phase tracer's
service slice: it exists to prove the one-directional import boundary with
real data before any horizontal expansion — if the seam is wrong, the
tracer finds it after one commit instead of after four plans of layered
services. The 08-04 expansion grows the same module into the full
non-visual selection foundation: canonical entry lists (the 08-05 filter
axes and 08-07 table columns), the n_audit presence mapping (SEL-04), and
the counts (retained over the entry loaders).

Contract:

- ZERO textual imports — directly or transitively (the foundation
  invariant declared in ``tui/services/__init__.py``; locked by
  ``tests/tui/test_import_lock.py``). Presentation belongs to screens;
  services stay importable by every CPU lane without a display
  (binding constraint 2).
- ``registry_loader`` and ``artifact_loader`` are imported as TOP-LEVEL
  modules, never as ``pipeline.xxx``: ``pipeline/`` is a sys.path root,
  not a package (no ``__init__.py``). At console runtime the
  ``tui/__main__.py`` bootstrap inserts ``REPO_ROOT/pipeline`` before
  any services import; under pytest the parent ``tests/conftest.py``
  supplies the same root.
- Zero re-implementation (binding constraint 5: TUI orchestrates, never
  computes): every registry semantic — the official
  ``models_info.json`` / ``datasets_info.json`` load, the custom
  overlay merge, the collision fail-fast — stays in the Phase 7 loader
  this module delegates to; every JSON read goes through
  ``artifact_loader``'s tolerant None sentinel (never a bare
  ``json.load``).
- Canonical model-card field reading (08-04): the committed model cards
  carry duplicate-casing twins whose values GENUINELY diverge
  (agro-nucleotide-transformer-1b: ``Tokenizer`` '6mer' vs
  ``tokenizer`` '6-mer'; prokbert-mini: ``Mean_token_length`` 6 vs
  ``mean_token_len`` 1) — every consumer reads exactly ONE canonical
  field, declared once by this module's ``MODEL_CARD_*`` constants:
  ``Tokenizer`` (not ``tokenizer``), ``Mean_token_length`` (not
  ``mean_token_len``), and the numeric ``size (M)`` (not the ``Model_size``
  "400M" string twin). The ``card`` value preserves the original dict
  verbatim, both twins included — the constants are the read
  discipline, not a mutation of the committed data.
- SEL-04 (D-08): presence reads the committed ``n_audit.json``
  artifact — the TUI computes nothing; row counts travel as EXACT
  integers with no aggregation, rounding, or formatting (the 08-07
  screen renders; copy lives in ``tui/strings.py``). The n_audit path
  is resolved from this module's own location, never the CWD.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

import artifact_loader  # top-level module (pipeline/ sys.path root, D-19)
import registry_loader  # top-level module (pipeline/ sys.path root, D-02/D-19)

# ===== Canonical model-card field constants (the casing twins resolved) =====

MODEL_CARD_SIZE_FIELD = "size (M)"  # numeric; NOT the Model_size "400M" twin
MODEL_CARD_TOKENIZER_FIELD = "Tokenizer"  # NOT the lowercase twin
MODEL_CARD_MEAN_TOKEN_LEN_FIELD = "Mean_token_length"  # NOT mean_token_len

# ===== Presence status vocabulary (SEL-04) =====

PRESENCE_PRESENT = "present"
PRESENCE_MISSING = "missing"
PRESENCE_UNKNOWN = "unknown"
#: Column-level sentinel: n_audit.json itself is absent/unreadable —
#: every row renders the documented empty-state copy (the 08-07 screen).
PRESENCE_UNAVAILABLE = "unavailable"

# ===== Locations (resolved from this module's own file, never CWD) =====

REPO_ROOT = Path(__file__).resolve().parents[2]
N_AUDIT_PATH = REPO_ROOT / "dnallm-mark" / "data" / "n_audit.json"


class RegistryCounts(NamedTuple):
    """Overlay-merged registry entry counts (models, datasets).

    Compares equal to the plain tuple ``(models, datasets)`` — the named
    fields exist for call-site readability, not a separate type contract.
    """

    models: int
    datasets: int


@dataclass(frozen=True)
class Presence:
    """One dataset row's local-data presence (SEL-04, D-08) — pure data.

    Attributes:
        status (str): one of the ``PRESENCE_*`` vocabulary — the 08-07
            screen maps it to glyphs and copy; nothing here renders.
        rows (tuple[int, int, int] | None): the EXACT integer
            ``(train, dev, test)`` row counts for present tasks; None
            for every other status (no aggregation, rounding, or
            formatting ever happens in this service).
    """

    status: str
    rows: tuple[int, int, int] | None


def load_model_entries():
    """The overlay-merged model registry as canonical entries.

    Delegates to ``pipeline/registry_loader`` (official + custom
    overlay) and projects each card to the canonical entry view.

    Returns:
        list[dict]: one entry per registry key, in registry file order,
        each exactly ``{key, type, species, size_m, card}``:

        - ``key`` (str): the registry key — the stable row_key
          vocabulary (D-06);
        - ``type`` (str): the card's ``type`` (MLM/CLM/DL), ``""`` when
          absent (the repo data convention: missing values are empty
          strings, never None/0);
        - ``species`` (str): the card's ``species``, ``""`` when absent;
        - ``size_m`` (float): ``MODEL_CARD_SIZE_FIELD`` ("size (M)") as
          a float — 0.0 when absent or unparseable — never the
          ``Model_size`` "400M" string twin;
        - ``card`` (dict): the original registry card, verbatim (both
          casing twins preserved; read via the ``MODEL_CARD_*``
          constants).
    """
    models = registry_loader.load_models_registry()
    return [
        {
            "key": key,
            "type": card.get("type") or "",
            "species": card.get("species") or "",
            "size_m": _to_float(card.get(MODEL_CARD_SIZE_FIELD)),
            "card": card,
        }
        for key, card in models.items()
    ]


def load_dataset_entries():
    """The overlay-merged dataset registry as canonical entries.

    Returns:
        list[dict]: one entry per registry key, in registry file order,
        each exactly ``{key, category, type, metric, card}`` — the
        category/type/metric filter axes carry the raw registry values
        (``""`` when absent); ``card`` is the original dict verbatim.
    """
    datasets = registry_loader.load_datasets_registry()
    return [
        {
            "key": key,
            "category": card.get("Category") or "",
            "type": card.get("type") or "",
            "metric": card.get("metric") or "",
            "card": card,
        }
        for key, card in datasets.items()
    ]


def load_registry_counts() -> RegistryCounts:
    """Return the entry counts of the overlay-merged registries.

    Implemented over the canonical entry loaders (08-04): the counts and
    the entry lists can never disagree. The committed official
    registries carry 59 models / 50 datasets; a machine-local custom
    overlay adds to those counts.

    Returns:
        RegistryCounts: ``(models, datasets)`` entry counts —
        ``(59, 50)`` against the committed registries with no custom
        overlay present.
    """
    return RegistryCounts(
        models=len(load_model_entries()),
        datasets=len(load_dataset_entries()),
    )


def load_n_audit():
    """Read the committed n_audit.json presence artifact (D-08).

    The path is resolved from this module's own location (repo root via
    ``__file__``), never the CWD; the read goes through
    ``artifact_loader``'s tolerant None sentinel.

    Returns:
        dict | None: the artifact's ``tasks`` mapping (task key ->
        ``{"missing": bool, "splits": {...} | None, ...}``), or None
        when the file is missing, corrupt, unreadable, or lacks a valid
        tasks mapping (the column-unavailable case; the service stays
        alive).
    """
    doc = artifact_loader.load_json_artifact(N_AUDIT_PATH)
    if not isinstance(doc, dict):
        return None
    tasks = doc.get("tasks")
    if not isinstance(tasks, dict):
        return None
    return tasks


def presence_for(task_key, audit_tasks):
    """Map one task key to its presence status + exact row counts.

    Pure data (SEL-04): the 08-07 screen renders; counts travel as
    exact integers. Cases, in decision order:

    1. ``audit_tasks`` None (n_audit missing/corrupt) ->
       ``PRESENCE_UNAVAILABLE`` for EVERY key — the column-level
       empty state.
    2. ``task_key`` absent from the mapping (registry/audit drift,
       either direction) -> ``PRESENCE_UNKNOWN``, never an exception.
    3. ``missing`` is true -> ``PRESENCE_MISSING`` with ``rows`` None
       regardless of any counts (D-08: the flag is the authority —
       the committed missing tasks carry ``splits: null`` anyway).
    4. ``missing`` false -> ``PRESENCE_PRESENT`` with the exact
       integer ``(train, dev, test)`` rows from the splits; a present
       flag whose splits cannot yield three integer rows reads as
       ``PRESENCE_UNKNOWN`` (cannot determine — degrade, never crash).

    Args:
        task_key (str): the dataset registry key (the row's task).
        audit_tasks (dict | None): the tasks mapping from
            ``load_n_audit()``.

    Returns:
        Presence: the frozen pure-data presence value.
    """
    if audit_tasks is None:
        return Presence(status=PRESENCE_UNAVAILABLE, rows=None)
    entry = audit_tasks.get(task_key)
    if not isinstance(entry, dict):
        return Presence(status=PRESENCE_UNKNOWN, rows=None)
    if entry.get("missing") is True:
        return Presence(status=PRESENCE_MISSING, rows=None)
    splits = entry.get("splits")
    if not isinstance(splits, dict):
        return Presence(status=PRESENCE_UNKNOWN, rows=None)
    # Early-return extraction: a present flag whose splits cannot yield
    # three integer rows reads as UNKNOWN (cannot determine — degrade,
    # never crash). bool is excluded from "integer" (the D-14
    # bool-exclusion discipline).
    extracted = []
    for split in ("train", "dev", "test"):
        value = splits.get(split)
        if not isinstance(value, dict):
            return Presence(status=PRESENCE_UNKNOWN, rows=None)
        count = value.get("rows")
        if not isinstance(count, int) or isinstance(count, bool):
            return Presence(status=PRESENCE_UNKNOWN, rows=None)
        extracted.append(count)
    return Presence(
        status=PRESENCE_PRESENT,
        rows=(extracted[0], extracted[1], extracted[2]),
    )


def _to_float(value, default=0.0):
    """Coerce a registry card value to float, defaulting on absence.

    Args:
        value: the raw card value (numeric, numeric string, or absent).
        default (float): the value for absent/unparseable input (the
            plan's "0.0 when absent").

    Returns:
        float: the coerced value.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
