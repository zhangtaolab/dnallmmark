"""
registries — the registry-view service (Phase 8, 08-03 tracer).

The FIRST module on the tui → pipeline seam, landed as the phase tracer's
service slice: it exists to prove the one-directional import boundary with
real data before any horizontal expansion — if the seam is wrong, the
tracer finds it after one commit instead of after four plans of layered
services.

Contract:

- ZERO textual imports — directly or transitively (the foundation
  invariant declared in ``tui/services/__init__.py``; locked by
  ``tests/tui/test_import_lock.py``). Presentation belongs to screens;
  services stay importable by every CPU lane without a display
  (binding constraint 2).
- ``registry_loader`` is imported as a TOP-LEVEL module, never as
  ``pipeline.registry_loader``: ``pipeline/`` is a sys.path root, not a
  package (no ``__init__.py``). At console runtime the
  ``tui/__main__.py`` bootstrap inserts ``REPO_ROOT/pipeline`` before
  any services import; under pytest the parent ``tests/conftest.py``
  supplies the same root.
- Zero re-implementation (binding constraint 5: TUI orchestrates, never
  computes): every registry semantic — the official
  ``models_info.json`` / ``datasets_info.json`` load, the custom
  overlay merge, the collision fail-fast — stays in the Phase 7 loader
  this module delegates to.
- The 08-04+ expansion (entry lists, filter axes, card columns) reads
  the same loaders through this module; ``load_registry_counts`` is the
  tracer slice of that view, not a parallel implementation.
- 08-04 additions (RED SKELETONS — behavior lands in the GREEN commit):
  the canonical entry view (``load_model_entries`` /
  ``load_dataset_entries``), the n_audit presence mapping
  (``load_n_audit`` / ``presence_for``).
"""

from dataclasses import dataclass
from typing import NamedTuple

import registry_loader  # top-level module (pipeline/ sys.path root, D-02/D-19)

# ===== RED skeletons (08-04) — canonical model-card field constants =====
MODEL_CARD_SIZE_FIELD = ""
MODEL_CARD_TOKENIZER_FIELD = ""
MODEL_CARD_MEAN_TOKEN_LEN_FIELD = ""

# ===== RED skeletons (08-04) — presence status vocabulary =====
PRESENCE_PRESENT = ""
PRESENCE_MISSING = ""
PRESENCE_UNKNOWN = ""
PRESENCE_UNAVAILABLE = ""


@dataclass(frozen=True)
class Presence:
    """RED skeleton — behavior lands in GREEN."""

    status: str
    rows: tuple[int, int, int] | None


def load_model_entries():
    """RED skeleton — behavior lands in GREEN."""
    return None


def load_dataset_entries():
    """RED skeleton — behavior lands in GREEN."""
    return None


def load_n_audit():
    """RED skeleton — behavior lands in GREEN."""
    return None


def presence_for(task_key, audit_tasks):
    """RED skeleton — behavior lands in GREEN."""
    return None


class RegistryCounts(NamedTuple):
    """Overlay-merged registry entry counts (models, datasets).

    Compares equal to the plain tuple ``(models, datasets)`` — the named
    fields exist for call-site readability, not a separate type contract.
    """

    models: int
    datasets: int


def load_registry_counts() -> RegistryCounts:
    """Return the entry counts of the overlay-merged registries.

    Delegates entirely to ``pipeline/registry_loader`` (Phase 7,
    CUST-05): official registries merged with the optional user-owned
    custom overlay (add-only semantics). The committed official
    registries carry 62 models / 50 datasets; a machine-local custom
    overlay adds to those counts.

    Returns:
        RegistryCounts: ``(models, datasets)`` entry counts —
        ``(62, 50)`` against the committed registries with no custom
        overlay present.
    """
    return RegistryCounts(
        models=len(registry_loader.load_models_registry()),
        datasets=len(registry_loader.load_datasets_registry()),
    )
