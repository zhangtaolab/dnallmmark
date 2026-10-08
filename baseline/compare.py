"""Order-insensitive recursive value comparison of two JSON files.

Compares a committed JSON file against a regenerated counterpart and reports
every value difference while ignoring key order — the canonical tool for
data-chain validation (decision D-06): textual diffs conflate key order with
values, so pin validation must go through a parsed, recursive walk.

Diff classes (the complete vocabulary — both output modes use it):

- ``TYPE``              — compared values have different JSON types
- ``MISSING_IN_REGEN``  — key present in committed, absent in regenerated
- ``EXTRA_IN_REGEN``    — key present in regenerated, absent in committed
- ``LEN``               — lists of different lengths
- ``FLOAT_ULP``         — float diff with relative delta < 1e-12 (summation-order noise)
- ``FLOAT_BIG``         — float diff with relative delta >= 1e-12 (real change)
- ``BOOL``              — bool/int cross-type value mismatch
- ``VALUE``             — string (or other scalar) mismatch

Relative delta is computed as ``abs(a - b) / max(abs(a), abs(b), 1e-300)``.

Usage (explicit paths, repo-root tooling — never CWD-relative)::

    python3 baseline/compare.py <committed.json> <regenerated.json>
    python3 baseline/compare.py --summary-json <committed.json> <regenerated.json>

``--summary-json`` prints a single JSON object to stdout with keys ``committed``
(string), ``regen`` (string), ``total`` (int), ``counts`` (object mapping each
diff class to its count; ``{}`` when no diffs) and ``diffs`` — the COMPLETE,
untruncated list of ``{kind, path, detail}`` objects in walk order (dict keys
visited in sorted order, so the diff sequence is process-independent), so that
``len(diffs) == total == sum(counts.values())`` always holds. The machine mode
is the contract the plan 01-03 migration gate consumes. The human-readable
mode caps its detail lines at 8 (models_comparison.json alone carries ~42 diffs;
a report does not need every line).

Exit codes (identical in both modes):

- 0 — no diffs found (VALUES IDENTICAL, order-insensitive)
- 1 — at least one diff found
- 2 — file-load or usage error (clear message, no traceback)

See also:
    - ``baseline/data-v1.sha256`` — SHA256 manifest of the 52 derived JSON
      files frozen at git tag ``data-v1`` (the pre-fix byte baseline).
    - ``baseline/PIN-VALIDATION.md`` — empirical pin-validation evidence built
      on this comparator (D-05/D-06).
    - ``script/get_task_performance.py`` — project script-skeleton conventions.
"""

import argparse
import json
import sys
from collections import Counter


def walk(a, b, path, diffs):
    """Recursively compare parsed JSON values, appending diff tuples.

    Diffs are appended as ``(kind, path, detail)`` in walk order; dict keys are
    compared as sets and iterated in ``sorted()`` order, so key order never
    produces a diff and the diff sequence is deterministic across processes
    (independent of ``PYTHONHASHSEED`` string-hash randomization).

    Args:
        a: Value from the committed file.
        b: Value from the regenerated file.
        path: JSONPath-like string locating the value (``/key/subkey[3]``).
        diffs: List that diff tuples are appended to.
    """
    if type(a) is not type(b) and not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        diffs.append(("TYPE", path, f"{type(a).__name__} vs {type(b).__name__}"))
        return
    if isinstance(a, dict):
        for k in sorted(set(a) - set(b)):
            diffs.append(("MISSING_IN_REGEN", path + "/" + str(k), "key only in committed"))
        for k in sorted(set(b) - set(a)):
            diffs.append(("EXTRA_IN_REGEN", path + "/" + str(k), "key only in regen"))
        for k in sorted(set(a) & set(b)):
            walk(a[k], b[k], path + "/" + str(k), diffs)
    elif isinstance(a, list):
        if len(a) != len(b):
            diffs.append(("LEN", path, f"{len(a)} vs {len(b)}"))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                walk(x, y, f"{path}[{i}]", diffs)
    elif isinstance(a, float) or isinstance(a, int):
        if isinstance(a, bool) or isinstance(b, bool):
            if a != b:
                diffs.append(("BOOL", path, f"{a} vs {b}"))
            return
        if a == b:
            return
        rel = abs(a - b) / max(abs(a), abs(b), 1e-300)
        if rel < 1e-12:
            diffs.append(("FLOAT_ULP", path, f"{a!r} vs {b!r} rel={rel:.2e}"))
        else:
            diffs.append(("FLOAT_BIG", path, f"{a!r} vs {b!r} rel={rel:.2e}"))
    else:
        if a != b:
            diffs.append(("VALUE", path, f"{a!r} vs {b!r}"))


def main(argv=None):
    """Parse arguments, compare the two JSON files, emit the report.

    Args:
        argv: Argument list (defaults to ``sys.argv[1:]``).

    Returns:
        int: Process exit code — 0 no diffs, 1 diffs found, 2 load/usage error.
    """
    parser = argparse.ArgumentParser(
        description="Order-insensitive recursive value comparison of two JSON files.",
    )
    parser.add_argument(
        "--summary-json",
        action="store_true",
        help="print a single machine-readable JSON object (complete untruncated diff inventory) instead of the capped human report",
    )
    parser.add_argument("committed", help="path to the committed (reference) JSON file")
    parser.add_argument("regen", help="path to the regenerated (candidate) JSON file")
    args = parser.parse_args(argv)

    try:
        with open(args.committed, encoding="utf-8") as f:
            committed = json.load(f)
    except (OSError, ValueError) as e:
        print(f"Error: cannot read committed file {args.committed}: {e}", file=sys.stderr)
        return 2
    try:
        with open(args.regen, encoding="utf-8") as f:
            regen = json.load(f)
    except (OSError, ValueError) as e:
        print(f"Error: cannot read regenerated file {args.regen}: {e}", file=sys.stderr)
        return 2

    diffs = []
    walk(committed, regen, "", diffs)
    counts = Counter(d[0] for d in diffs)

    if args.summary_json:
        summary = {
            "committed": args.committed,
            "regen": args.regen,
            "total": len(diffs),
            "counts": dict(counts),
            "diffs": [{"kind": kind, "path": path, "detail": detail} for (kind, path, detail) in diffs],
        }
        print(json.dumps(summary))
    else:
        print(f"{args.committed.split('/')[-1]}: {dict(counts) if counts else 'VALUES IDENTICAL (order-insensitive)'}")
        for kind, path, detail in diffs[:8]:
            print(f"  [{kind}] {path[:110]}: {detail}")
        if len(diffs) > 8:
            print(f"  ... and {len(diffs)-8} more")

    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
