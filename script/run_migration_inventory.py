"""Tree-level migration-inventory orchestrator for leaderboard data migrations (DATA-01, D-17/OQ6).

Purpose
-------
Produce the machine-readable, categorized before/after inventory a data
migration gate requires: copy the committed data tree to a scratch tree,
run the regeneration chain inside the scratch copy (the
``tests/test_determinism.py`` copytree+chdir pattern), value-compare every
derived file against its committed counterpart through ``baseline/compare.py``
's own ``walk()`` (the comparator is NOT edited — D-17/OQ6), and aggregate
per-category counts across the tree into one JSON document. The data-v2
gate (post-E2') reuses this orchestrator; the F6 migration (05-02) is its
first consumer and commits its output as
``baseline/f6-migration-inventory.json``.

Also provides ``--write-manifest <out>``: a SHA256 manifest over the derived
data files following the ``baseline/data-v1.sha256`` line convention
(``<sha256>  <repo-relative-path>``, two spaces, sorted) — the tamper-evidence
continuity the data-v2 tag requires. This script NEVER creates, moves, or
pushes any git tag (the tag is the maintainer's sign-off act; D-17/OQ3).

Direction of truth
------------------
``baseline/compare.py``'s diff vocabulary (TYPE / MISSING_IN_REGEN /
EXTRA_IN_REGEN / LEN / FLOAT_ULP / FLOAT_BIG / INT / BOOL / BOOL_CROSS /
VALUE) — reused via ``walk()``, never re-implemented. The regeneration chain
is exactly ``make data``'s: ``script/summarize_comparison.py`` (CWD-relative,
run inside the scratch copy), ``script/permutation_tests.py``
(REPO_ROOT-relative), and ``scripts/generate-tasks-index.js`` (the
copy-into-scratch-tree trick — the generator is ``__dirname``-relative and
must never run against the repo tree).

Behavior
--------
``run_inventory``:

1. scratch  a tmp tree with the committed inputs copied in
   (``model_performance/``, the JS-visible ``task_performance/`` tree, and
   a copy of the JS generator under ``inner/gen.js``);
2. chain    summarize (cwd=scratch) -> permutation_tests (--output into
   scratch) -> node inner/gen.js (cwd=scratch);
3. compare  every derived file (committed vs scratch) via ``walk()``; a
   file present in scratch but absent from the committed tree is reported
   as ``status: "new"`` (e.g. the F6 migration's permutation_tests.json +
   manifest.json);
4. emit     ``{"data_version", "generated_from", "date", "files": [...],
   "totals": {...}}`` — per-file status/total/counts plus tree-level
   aggregates. Pass/fail on attribution is a HUMAN/gate judgment over this
   document (the F6 migration expects EXTRA_IN_REGEN counts only, from the
   weighted_score additions) — the orchestrator reports, it does not judge.

Usage
-----
From the repo root (run BEFORE the tree moves, so the committed side is the
pre-migration content)::

    uv run --group data python script/run_migration_inventory.py \
        --output baseline/f6-migration-inventory.json

    uv run --group data python script/run_migration_inventory.py \
        --write-manifest baseline/data-v2.sha256

See also:
    - ``baseline/compare.py`` — the diff vocabulary owner.
    - ``tests/test_migration_inventory.py`` — the synthetic-tree unit lane.
    - ``CHANGELOG.md`` — the human registry linking to each inventory.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "dnallm-mark" / "data"
SUMMARY_SCRIPT = REPO_ROOT / "script" / "summarize_comparison.py"
PERMUTATION_SCRIPT = REPO_ROOT / "script" / "permutation_tests.py"
GENERATOR = REPO_ROOT / "scripts" / "generate-tasks-index.js"

# baseline/compare.py is not a package sibling of this script (only
# tests/conftest.py puts baseline/ on sys.path) — load the module by file
# path, the D-17/OQ6 "comparator untouched, reused" contract.
_COMPARE_PATH = REPO_ROOT / "baseline" / "compare.py"
_COMPARE_SPEC = importlib.util.spec_from_file_location("compare", _COMPARE_PATH)
assert _COMPARE_SPEC is not None and _COMPARE_SPEC.loader is not None
_COMPARE = importlib.util.module_from_spec(_COMPARE_SPEC)
_COMPARE_SPEC.loader.exec_module(_COMPARE)
walk = _COMPARE.walk

# The derived artifacts the inventory compares and the manifest covers. Each
# entry maps the repo-relative path (committed side / manifest line) to its
# location inside a scratch tree (regenerated side).
DERIVED_FILES: dict[str, str] = {
    "dnallm-mark/data/models_comparison.json": "models_comparison.json",
    "dnallm-mark/data/models_comparison_animal.json": "models_comparison_animal.json",
    "dnallm-mark/data/models_comparison_plant.json": "models_comparison_plant.json",
    "dnallm-mark/data/models_comparison_microbe.json": "models_comparison_microbe.json",
    "dnallm-mark/data/tasks.json": "dnallm-mark/data/tasks.json",
    "dnallm-mark/data/permutation_tests.json": "permutation_tests.json",
    "dnallm-mark/data/manifest.json": "manifest.json",
}

_READ_CHUNK = 1 << 20


def _run_checked(cmd: list[str], cwd: Path) -> None:
    """Run one chain step, raising with captured output on failure.

    Args:
        cmd: Command argv (``sys.executable`` resolves to the venv python
            under ``uv run``; the child inherits this process's environment).
        cwd: Working dir for the step (the scratch chain root).
    """
    proc = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"chain step failed with exit {proc.returncode}: "
            f"{' '.join(cmd)}\n"
            f"--- stdout tail ---\n{proc.stdout[-1500:]}\n"
            f"--- stderr tail ---\n{proc.stderr[-1500:]}"
        )


def regenerate_into_scratch(scratch: Path, *, data_dir: Path = DATA_DIR) -> None:
    """Run the full regeneration chain inside a scratch copy of the inputs.

    Copies ``model_performance/`` and the JS-visible ``task_performance/``
    tree plus the JS generator (the copy trick — the generator is
    ``__dirname``-relative and would otherwise write the REAL data tree),
    then runs summarize with ``cwd=scratch`` (its CWD-relative convention
    writes the comparisons + manifest into the scratch root), the
    permutation engine with an explicit scratch output, and the JS index
    generator.

    Args:
        scratch: The scratch chain root (created if absent; inputs copied
            read-only-into-scratch, never the published tree).
        data_dir: The committed data tree to copy inputs from.
    """
    shutil.copytree(data_dir / "model_performance", scratch / "model_performance")
    (scratch / "inner").mkdir(parents=True)
    shutil.copy(GENERATOR, scratch / "inner" / "gen.js")
    shutil.copytree(
        data_dir / "task_performance", scratch / "dnallm-mark" / "data" / "task_performance"
    )

    _run_checked([sys.executable, str(SUMMARY_SCRIPT)], cwd=scratch)
    _run_checked(
        [
            sys.executable, str(PERMUTATION_SCRIPT),
            "--input-dir", str(scratch / "model_performance"),
            "--output", str(scratch / "permutation_tests.json"),
        ],
        cwd=scratch,
    )
    _run_checked(["node", str(scratch / "inner" / "gen.js")], cwd=scratch)


def compare_derived(committed_root: Path, regen_dir: Path,
                    derived: dict[str, str] = DERIVED_FILES) -> dict[str, Any]:
    """Value-compare every derived file (committed vs regenerated).

    Args:
        committed_root: Root against which the repo-relative committed paths
            resolve (``REPO_ROOT`` for the real tree; a synthetic layout in
            tests).
        regen_dir: The scratch root holding the regenerated outputs.
        derived: Mapping of repo-relative committed path -> scratch-relative
            regenerated path.

    Returns:
        The inventory dict ``{"files": [...], "totals": {...}}`` — one entry
        per derived file with ``status`` (``identical`` / ``changed`` /
        ``new``), ``total`` diff count and per-category ``counts``; plus
        tree-level totals aggregating the categories.
    """
    files: list[dict[str, Any]] = []
    category_totals: Counter[str] = Counter()
    n_identical = n_changed = n_new = 0

    for rel, scratch_rel in sorted(derived.items()):
        committed_path = committed_root / rel
        regen_path = regen_dir / scratch_rel

        entry: dict[str, Any] = {"path": rel}
        if not committed_path.exists():
            if not regen_path.exists():
                entry["status"] = "absent"
            else:
                entry["status"] = "new"
                n_new += 1
            files.append(entry)
            continue
        if not regen_path.exists():
            entry["status"] = "missing_in_regen"
            files.append(entry)
            continue

        diffs: list[tuple[str, str, str]] = []
        walk(
            json.loads(committed_path.read_text(encoding="utf-8")),
            json.loads(regen_path.read_text(encoding="utf-8")),
            "",
            diffs,
        )
        counts = Counter(kind for kind, _, _ in diffs)
        entry["status"] = "changed" if diffs else "identical"
        entry["total"] = len(diffs)
        entry["counts"] = dict(sorted(counts.items()))
        category_totals.update(counts)
        if diffs:
            n_changed += 1
        else:
            n_identical += 1
        files.append(entry)

    return {
        "files": files,
        "totals": {
            "files_total": len(derived),
            "files_identical": n_identical,
            "files_changed": n_changed,
            "files_new": n_new,
            "diffs_total": sum(category_totals.values()),
            "counts": dict(sorted(category_totals.items())),
        },
    }


def sha256_file(path: Path) -> str:
    """Streaming SHA256 hexdigest of one file (hashlib — never hand-rolled).

    Args:
        path: File to hash.

    Returns:
        The hex digest string.
    """
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(_READ_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_sha256_manifest(rel_paths: Sequence[str], out_path: Path) -> list[str]:
    """Emit a SHA256 manifest in the ``baseline/data-v1.sha256`` convention.

    One ``<sha256>  <path>`` line per file (two spaces), paths repo-relative
    POSIX, lines sorted by path — the tamper-evidence continuity across data
    versions. No header line (data-v1.sha256 has none).

    Args:
        rel_paths: Repo-relative POSIX path strings to freeze.
        out_path: Manifest destination.

    Returns:
        The ordered list of manifest lines written.
    """
    ordered = sorted(str(Path(p).as_posix()) for p in rel_paths)
    lines = [f"{sha256_file(REPO_ROOT / rel)}  {rel}" for rel in ordered]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines


def run_inventory(output: Path, *, data_version: str, generated_from: str,
                  date: str, data_dir: Path = DATA_DIR,
                  committed_root: Path | None = None,
                  chain_runner=regenerate_into_scratch) -> dict[str, Any]:
    """Full orchestrator: scratch regeneration + comparison + inventory emit.

    Args:
        output: Destination for the inventory JSON.
        data_version: The migration's data_version stamp (recorded; the
            inventory never invents one).
        generated_from: The pre-migration commit sha (recorded).
        date: The migration date, ISO ``YYYY-MM-DD`` (recorded).
        data_dir: The committed data tree (inputs + committed counterparts).
        committed_root: Root resolving the committed side of the comparison
            (defaults to ``REPO_ROOT``; synthetic roots in tests).
        chain_runner: The regeneration callable (injectable for tests);
            called as ``chain_runner(scratch, data_dir=data_dir)``.

    Returns:
        The inventory document (also written to ``output``).
    """
    with tempfile.TemporaryDirectory(prefix="f6-inventory-") as tmp:
        scratch = Path(tmp) / "scratch"
        chain_runner(scratch, data_dir=data_dir)
        inventory = compare_derived(committed_root or REPO_ROOT, scratch)
    doc = {
        "data_version": data_version,
        "generated_from": generated_from,
        "date": date,
        **inventory,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(doc, indent=4, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return doc


def main(argv: Sequence[str] | None = None) -> int:
    """CLI: inventory mode by default; ``--write-manifest`` emits the SHA256
    manifest over the derived data files instead (the data-v2 gate reuses it)."""
    parser = argparse.ArgumentParser(
        prog="run_migration_inventory",
        description=(
            "Tree-level migration inventory: scratch-regenerate the data "
            "chain and categorize every diff vs the committed tree "
            "(DATA-01, D-17/OQ6)."
        ),
    )
    parser.add_argument("--output", type=Path,
                        default=REPO_ROOT / "baseline" / "f6-migration-inventory.json",
                        help="inventory destination (default: %(default)s)")
    parser.add_argument("--data-version", default="1.1.0",
                        help="data_version stamp recorded in the inventory (default: %(default)s)")
    parser.add_argument("--generated-from", default=None,
                        help="pre-migration commit sha; defaults to HEAD at invocation "
                             "(the F6 migration passes the recorded pre-migration sha)")
    parser.add_argument("--date", default="1970-01-01",
                        help="migration date, ISO YYYY-MM-DD (default: %(default)s)")
    parser.add_argument("--write-manifest", type=Path, default=None,
                        help="INSTEAD of the inventory, emit a SHA256 manifest over the "
                             "derived data files at this path (data-v1.sha256 convention)")
    args = parser.parse_args(argv)

    if args.write_manifest is not None:
        existing = [rel for rel in DERIVED_FILES if (REPO_ROOT / rel).exists()]
        lines = write_sha256_manifest(existing, args.write_manifest)
        print(f"Froze {len(lines)} derived file(s) -> {args.write_manifest}")
        return 0

    generated_from = args.generated_from
    if generated_from is None:
        probe = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
            capture_output=True, text=True, check=True,
        )
        generated_from = probe.stdout.strip()

    doc = run_inventory(
        args.output,
        data_version=args.data_version,
        generated_from=generated_from,
        date=args.date,
    )
    totals = doc["totals"]
    print(
        f"Inventory: {totals['files_changed']} changed / {totals['files_new']} new / "
        f"{totals['files_identical']} identical — {totals['diffs_total']} diff(s) "
        f"{totals['counts']} -> {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
