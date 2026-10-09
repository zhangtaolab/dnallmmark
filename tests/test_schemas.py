# =====================================================================
# test_schemas.py — committed-data JSON Schema contract validation (TEST-06)
#
# Validates every committed leaderboard JSON file against its strict
# draft-2020-12 schema in ``schemas/`` (D-01: additionalProperties false
# everywhere, every field required; D-02: closed enums). One parametrized
# pytest item per committed file, so a single drifted file is reported
# individually instead of failing an opaque batch.
#
# Usage:
#     make test-fast          # from repo root (uv run --group dev pytest -m "not slow")
#     uv run --group dev pytest tests/test_schemas.py -q
# =====================================================================

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "dnallm-mark" / "data"

# ===== Committed-file buckets (schema file -> data files it governs) =====
SCHEMA_FILES = {
    "model_performance": (
        REPO / "schemas" / "model_performance.json",
        sorted((DATA / "model_performance").glob("*.json")),
    ),
}


@pytest.fixture(scope="session")
def validators():
    """Build one ``Draft202012Validator`` per schema file.

    Returns:
        dict: schema bucket name -> compiled ``Draft202012Validator``.
    """
    return {
        name: Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))
        for name, (path, _) in SCHEMA_FILES.items()
    }


@pytest.mark.parametrize(
    "schema_name, path",
    [(name, p) for name, (_, paths) in SCHEMA_FILES.items() for p in paths],
)
def test_committed_file_matches_schema(validators, schema_name, path):
    """A committed leaderboard JSON file validates against its schema with zero errors.

    Args:
        validators: session-scoped validator map (fixture).
        schema_name: bucket name keying ``SCHEMA_FILES`` / ``validators``.
        path: committed JSON file (one pytest item per file).
    """
    doc = json.loads(path.read_text(encoding="utf-8"))
    errors = list(validators[schema_name].iter_errors(doc))
    assert not errors, "\n".join(
        f"{path.name} {e.json_path} [{e.validator}]: {e.message}"
        for e in errors[:10]
    )


def test_schema_documents_are_wellformed():
    """Every schema document is itself valid draft-2020-12 (``check_schema``)."""
    for name, (path, _) in SCHEMA_FILES.items():
        schema = json.loads(path.read_text(encoding="utf-8"))
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:  # noqa: BLE001 — re-raise with the bucket named
            pytest.fail(f"{name}: schema at {path} is not well-formed: {exc}")
