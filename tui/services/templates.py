"""
templates — run-configuration template service (Phase 8, 08-05).

RED SKELETON (TDD): the failing tests in
``tests/tui/test_services_templates.py`` are committed together with these
None-returning signatures; the implementation (strict D-07 schema
validation with collect-all problem listing, export, and the
sweep_priorities tier interop pair) lands with the GREEN commit.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "run_template.json"


def load_schema():
    """RED skeleton — implementation lands with the GREEN commit."""
    return None


def validate_template(doc):
    """RED skeleton — implementation lands with the GREEN commit."""
    return None


def export_selection_template(models, tasks, params=None):
    """RED skeleton — implementation lands with the GREEN commit."""
    return None


def load_template_file(path):
    """RED skeleton — implementation lands with the GREEN commit."""
    return None


def template_to_tiers(template):
    """RED skeleton — implementation lands with the GREEN commit."""
    return None


def tiers_to_template(tiers, params=None):
    """RED skeleton — implementation lands with the GREEN commit."""
    return None
