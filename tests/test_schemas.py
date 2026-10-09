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
    "task_performance": (
        REPO / "schemas" / "task_performance.json",
        sorted((DATA / "task_performance").glob("*.json")),
    ),
    "models_comparison": (
        REPO / "schemas" / "models_comparison.json",
        [
            DATA / f
            for f in (
                "models_comparison.json",
                "models_comparison_animal.json",
                "models_comparison_plant.json",
                "models_comparison_microbe.json",
            )
        ],
    ),
    "tasks_index": (
        REPO / "schemas" / "tasks_index.json",
        [DATA / "tasks.json"],
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


# Pinned corpus sizes (WR-03): the glob-built buckets parametrize to ZERO
# pytest items when the data tree is missing or partial, so the 42-file and
# 47-file validation silently vanishes while the suite stays green. The
# pins fail loudly instead. Update them DELIBERATELY when the corpus grows.
EXPECTED_BUCKET_SIZES = {
    "model_performance": 42,
    "task_performance": 47,
    "models_comparison": 4,
    "tasks_index": 1,
}


def test_schema_bucket_counts_are_pinned():
    """WR-03 canary: every bucket holds exactly its pinned file count.

    A glob over a missing/partial ``dnallm-mark/data`` tree cannot fail on
    its own — an empty glob just yields zero parametrized validation items
    (a vacuous pass). The literal-path buckets fail loudly per missing
    file, but their counts are pinned here too so an accidental list edit
    cannot shrink coverage unnoticed.
    """
    for name, (schema_path, paths) in SCHEMA_FILES.items():
        expected = EXPECTED_BUCKET_SIZES[name]
        assert paths, (
            f"{name}: no committed data files found for schema "
            f"{schema_path.name} — the dnallm-mark/data tree is missing "
            "or partial; this bucket's parametrized validation is vacuous"
        )
        assert len(paths) == expected, (
            f"{name}: found {len(paths)} files, expected {expected} — "
            "update the pin deliberately when the committed corpus grows"
        )


def test_metric_enum_matches_committed_data(validators):
    """D-02 self-check: the schema metric enum equals the metric values in data.

    Collects every ``dataset.metric`` value across all committed
    model_performance files and asserts the authored schema's closed enum
    is exactly that set — so enum and data cannot silently diverge: a new
    dataset metric turns this test red until the schema is updated.

    Args:
        validators: session-scoped validator map (fixture).
    """
    observed = set()
    for path in SCHEMA_FILES["model_performance"][1]:
        doc = json.loads(path.read_text(encoding="utf-8"))
        observed |= {entry["dataset"]["metric"] for entry in doc["performance"].values()}

    schema = validators["model_performance"].schema
    schema_enum = set(
        schema["$defs"]["datasetEntry"]["properties"]["dataset"]["properties"]["metric"]["enum"]
    )
    assert schema_enum == observed == {"f1", "mcc", "spearmanr", "AUPRC"}, (
        f"schema enum {sorted(schema_enum)} != observed data {sorted(observed)} — "
        "update the schema (D-02 forced versioning) or fix the drifted data"
    )
