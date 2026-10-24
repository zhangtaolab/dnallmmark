"""Tests for the freeze_snapshot primitive (REV-03/OQ7).

Pins the pure function over a fixture tree: it writes a tar + a SHA256
manifest matching the baseline/data-v1.sha256 line format, records the
passed commit hash, and takes paths + output dir as parameters (no
repo-global constants). The actual invocation is intentionally unwired
this phase (Phase 6 packaging).

See also:
    - ``baseline/data-v1.sha256`` — the manifest convention pinned here.
"""

import hashlib
import tarfile

import freeze_snapshot  # conftest puts script/ on sys.path
import pytest


@pytest.fixture
def fixture_tree(tmp_path, monkeypatch):
    """A small derived-data-like tree; CWD pinned so relative paths work."""
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "a.json").write_text('{"a": 1}\n', encoding="utf-8")
    (tmp_path / "data" / "b.json").write_text('{"b": 2}\n', encoding="utf-8")
    (tmp_path / "data" / "tasks.json").write_text('{"t": []}\n', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_freeze_snapshot_writes_tar_and_manifest(fixture_tree, tmp_path):
    """Tar + manifest land under the parameterized output dir; the manifest
    records the commit hash and hashes match recomputation; the tar round-
    trips the file contents under their given relative paths."""
    out_dir = tmp_path / "snapshots"
    archive, manifest = freeze_snapshot.freeze_snapshot(
        ["data/a.json", "data/tasks.json", "data/b.json"],
        out_dir,
        "deadbeef1234",
    )
    assert archive == out_dir / "snapshot-deadbeef1234.tar"
    assert manifest == out_dir / "snapshot-deadbeef1234.sha256"
    assert archive.exists() and manifest.exists()

    lines = manifest.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "# commit deadbeef1234"
    body = lines[1:]
    assert len(body) == 3
    # Line format: "<sha256>  <path>" (two spaces), paths sorted.
    assert [line.split("  ", 1)[1] for line in body] == [
        "data/a.json", "data/b.json", "data/tasks.json",
    ]
    for line in body:
        digest, path = line.split("  ", 1)
        assert len(digest) == 64 and digest == digest.lower()
        assert digest == hashlib.sha256((tmp_path / path).read_bytes()).hexdigest()

    with tarfile.open(archive) as tar:
        names = sorted(tar.getnames())
        assert names == ["data/a.json", "data/b.json", "data/tasks.json"]
        member = tar.extractfile("data/a.json")
        assert member is not None
        extracted = member.read()
    assert extracted == b'{"a": 1}\n'
