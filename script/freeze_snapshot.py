"""Freeze a derived-data snapshot: tar + SHA256 manifest + frozen commit hash (REV-03).

Purpose
-------
Produce a tamper-evident archive of the leaderboard's derived data files:
a tar of the given paths plus a SHA256 manifest whose line format follows
the ``baseline/data-v1.sha256`` convention (``<sha256>  <path>``, two
spaces), with the frozen commit hash recorded both in the artifact names
(``snapshot-<hash>.tar`` / ``snapshot-<hash>.sha256``) and on the
manifest's header line.

This module is a TESTED PRIMITIVE in Phase 4 only: the actual invocation is
intentionally unwired — Phase 6 packaging decides which paths get frozen
and where the artifact lands (data still moves at E2'; OQ7 resolved to
parameterized paths + output dir, no repo-global constants).

Usage
-----
::

    python script/freeze_snapshot.py \\
        --paths dnallm-mark/data/models_comparison.json ... \\
        --output-dir baseline/snapshots \\
        --commit-hash "$(git rev-parse HEAD)"

See also:
    - ``baseline/data-v1.sha256`` — the manifest line-format convention.
    - ``script/export_runs.py`` — the exporter whose output gets frozen.
"""

from __future__ import annotations

import argparse
import hashlib
import tarfile
from collections.abc import Sequence
from pathlib import Path

_READ_CHUNK = 1 << 20


def _sha256_file(path: Path) -> str:
    """Streaming SHA256 hexdigest of one file (never hand-roll — hashlib)."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(_READ_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def freeze_snapshot(
    paths: Sequence[str | Path], output_dir: Path, commit_hash: str
) -> tuple[Path, Path]:
    """Freeze the given files into a tar + SHA256 manifest named by the commit.

    Side effects are confined to ``output_dir`` (pure with respect to the
    frozen inputs): the archive stores each file under exactly the given
    path, and the manifest carries one ``<sha256>  <path>`` line per file
    (sorted, two spaces — the baseline/data-v1.sha256 convention) behind a
    ``# commit <hash>`` header line recording the frozen revision.

    Args:
        paths: files to freeze, as repo-relative POSIX path strings (the
            manifest convention).
        output_dir: destination directory (created if absent).
        commit_hash: the frozen commit; recorded in both artifact names
            and on the manifest header.

    Returns:
        ``(archive_path, manifest_path)``.
    """
    ordered = sorted(str(Path(p).as_posix()) for p in paths)
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"snapshot-{commit_hash}.tar"
    manifest = output_dir / f"snapshot-{commit_hash}.sha256"
    with tarfile.open(archive, "w") as tar:
        for rel in ordered:
            tar.add(rel, arcname=rel)
    lines = [f"# commit {commit_hash}"]
    lines.extend(f"{_sha256_file(Path(rel))}  {rel}" for rel in ordered)
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return archive, manifest


def main(argv: Sequence[str] | None = None) -> int:
    """CLI wrapper. Intentionally unwired from any Makefile target this
    phase — Phase 6 packaging owns the invocation policy."""
    parser = argparse.ArgumentParser(
        prog="freeze_snapshot",
        description="Freeze derived-data files: tar + SHA256 manifest + commit hash (REV-03).",
    )
    parser.add_argument("--paths", nargs="+", required=True,
                        help="repo-relative files to freeze")
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="destination directory for the snapshot artifacts")
    parser.add_argument("--commit-hash", required=True,
                        help="the frozen commit (e.g. $(git rev-parse HEAD))")
    args = parser.parse_args(argv)
    archive, manifest = freeze_snapshot(args.paths, args.output_dir, args.commit_hash)
    print(f"Froze {len(args.paths)} file(s) at commit {args.commit_hash}")
    print(f"  archive:  {archive}")
    print(f"  manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
