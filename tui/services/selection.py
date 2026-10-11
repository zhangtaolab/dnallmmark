"""
selection — mark-set, preset, and filter-grammar service (Phase 8, 08-05).

RED SKELETON (TDD): the failing tests in
``tests/tui/test_services_selection.py`` are committed together with these
None-returning signatures and type shapes; the implementation (D-06 preset
derivation from pipeline/sweep_priorities.json, custom presets under the
XDG config root, and the pure filter grammar) lands with the GREEN commit.
"""

from dataclasses import dataclass
from typing import NamedTuple


@dataclass(frozen=True)
class Preset:
    """One derived preset (id, marks, unknown keys) — shapes land in GREEN."""

    id: str
    models: tuple
    tasks: tuple
    unknown_keys: tuple


@dataclass(frozen=True)
class PresetDerivation:
    """Derived presets plus the damaged-file load-error signal."""

    presets: tuple
    load_error: object


class SubstringTerm(NamedTuple):
    """A bare-substring filter term."""

    text: str


class AxisTerm(NamedTuple):
    """An ``axis=value`` filter term."""

    axis: str
    value: str


class UnknownAxis(NamedTuple):
    """A parse diagnostic: the unknown axis and the known-axis vocabulary."""

    axis: str
    known_axes: tuple


@dataclass(frozen=True)
class ParsedFilter:
    """A parsed filter query: valid terms plus diagnostics."""

    terms: tuple
    diagnostics: tuple


def derive_presets(priorities_path, model_keys, task_keys):
    """RED skeleton — implementation lands with the GREEN commit."""
    return None


def save_custom_preset(name, models, tasks, config_dir):
    """RED skeleton — implementation lands with the GREEN commit."""
    return None


def load_custom_presets(config_dir):
    """RED skeleton — implementation lands with the GREEN commit."""
    return None


def parse_filter_query(query):
    """RED skeleton — implementation lands with the GREEN commit."""
    return None


def apply_filter(entries, terms):
    """RED skeleton — implementation lands with the GREEN commit."""
    return None
