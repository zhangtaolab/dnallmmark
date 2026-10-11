# =====================================================================
# test_artifact_loader.py — tolerant JSON read contract (Phase 7, PIPE-03)
#
# Pins pipeline/artifact_loader.load_json_artifact to the D-17/D-18
# contract: parse-level tolerance ONLY (missing / unreadable / empty /
# truncated files return the None sentinel), structurally valid JSON that
# merely lacks expected keys is returned as-is, and the loader carries no
# state of its own.
#
# Usage:
#     uv run --group dev pytest tests/test_artifact_loader.py -q
# =====================================================================

import os

import pytest
from artifact_loader import load_json_artifact


def test_missing_file_returns_none(tmp_path):
    assert load_json_artifact(tmp_path / "absent.json") is None


def test_empty_file_returns_none(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text("", encoding="utf-8")
    assert load_json_artifact(path) is None


def test_truncated_json_returns_none(tmp_path):
    path = tmp_path / "truncated.json"
    path.write_text('{"schema_version": 1, "num', encoding="utf-8")
    assert load_json_artifact(path) is None


def test_truncated_utf8_sequence_returns_none(tmp_path):
    """A file cut mid-multibyte-character fails at decode, not parse —
    still a truncated artifact, still the None sentinel."""
    path = tmp_path / "utf.bin"
    path.write_bytes(b'{"a": "\xe4\xb8')
    assert load_json_artifact(path) is None


def test_unreadable_permissions_return_none(tmp_path):
    path = tmp_path / "locked.json"
    path.write_text("{}", encoding="utf-8")
    os.chmod(path, 0o000)
    if os.access(path, os.R_OK):
        pytest.skip("permission bits not enforced (running as root)")
    try:
        assert load_json_artifact(path) is None
    finally:
        os.chmod(path, 0o644)


def test_valid_json_without_expected_keys_is_returned(tmp_path):
    """D-17: key-level checks belong to callers — a structurally valid
    document missing every expected key is NOT corruption."""
    path = tmp_path / "sparse.json"
    path.write_text('{"foo": 1}', encoding="utf-8")
    assert load_json_artifact(path) == {"foo": 1}


def test_valid_json_document_round_trip(tmp_path):
    path = tmp_path / "valid.json"
    payload = {"a": [1, 2, 3], "b": None, "c": {"nested": True}}
    path.write_text(
        '{"a": [1, 2, 3], "b": null, "c": {"nested": true}}', encoding="utf-8"
    )
    assert load_json_artifact(path) == payload


def test_string_path_is_accepted(tmp_path):
    path = tmp_path / "strpath.json"
    path.write_text("[1, 2]", encoding="utf-8")
    assert load_json_artifact(str(path)) == [1, 2]


def test_loader_is_stateless_across_calls(tmp_path):
    """D-18: no cache, no state — a corrupt read leaves no residue that
    changes a subsequent valid read."""
    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{oops", encoding="utf-8")
    valid = tmp_path / "valid.json"
    valid.write_text('{"ok": true}', encoding="utf-8")
    assert load_json_artifact(corrupt) is None
    assert load_json_artifact(valid) == {"ok": True}
    assert load_json_artifact(corrupt) is None
