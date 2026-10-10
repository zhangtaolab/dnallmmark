"""N-frequency / non-ACGT census + unified eval-subset emission (F7 / REV-07).

Purpose
-------
Audit every task in the unified datasets registry over its on-disk split
CSVs and publish, from code (never hand-counted):

1. ``dnallm-mark/data/n_audit.json`` — per task x split: row count, total
   sequence characters, non-ACGT character census (characters outside
   ``ACGTacgt`` over the sequence column, the ``|`` pair separator
   excluded), rows containing at least one non-ACGT character, and the
   survivor counts under BOTH pipeline charset classes, plus the unified
   eval N per task and a missing flag (the 7 not-yet-re-extracted GUE
   tasks are explicit missing rows, never silent absences).
2. ``dnallm-mark/data/n_audit.csv`` — the same census as a flat
   reviewer-facing table (one row per task x split, plus one row per
   missing task).
3. ``pipeline/eval_subsets.json`` — the pure ``task -> row-ID list`` map
   consumed by ``pipeline/run_finetune.py --subset_file``: for every task
   with a readable test split, the sorted row indices passing the COMMON
   (strict-charset) filter, truncated to the unified eval N, so every
   model evaluates an identical, provable sample count (F7 Q1).
4. ``DATA.md`` — the published appendix table (one row per registry task,
   including the missing ones) plus the method notes. The whole file is
   GENERATED here; do not edit it by hand.

Direction of truth
------------------
``pipeline/datasets_info.json`` (the D-10 unified registry) is the task
authority — every registry key appears in the audit exactly once (present
with counts, or missing with a WARNING line). ``Dataset_path`` values
carry the leading ``datasets/`` prefix and resolve against ``pipeline/``
in the pipeline driver; with the default ``--datasets-root`` (``pipeline/
datasets``) that prefix is stripped here.

Filter semantics mirror the pipeline EXACTLY (``run_finetune.py``
``validate_sequences`` call at :837-839, suite ``check_sequence`` at
``dnallm/utils/sequence.py`` @483a35c, read-only): a row survives a
class iff ``set(seq.upper())`` is a subset of the class charset AND
``0 <= len(seq) <= 10010``. The ``gc=(0,1)`` default of that call can
never reject (``calc_gc_content`` always returns a value in ``[0, 1]``,
0.0 for the empty sequence), so it imposes no additional constraint and
is not re-implemented. Two classes exist (the pipeline's per-model
conditional at :832-836): STRICT ``"ACGTacgt|"`` (``models_no_char_n``
members — a single N discards the whole row) and N-TOLERANT
``"ACGTNacgtn|"`` (every other model). The unified eval N per task is
the MIN over the per-class test survivor counts — the strictest class
governs — and the subset ID list holds the first N strict-passing row
indices in ascending file order (deterministic; CSV row order is the
index space of the Hugging Face ``Dataset.select`` the pipeline applies).

Untrusted-data discipline (T-05-07): the split CSVs are Zenodo-sourced
and never authored by this repo. Reading is parse-only (stdlib
``csv.reader``, bounded field sizes), malformed rows are skipped
per-row with a ``[Skip]`` line and never counted, and nothing is ever
``eval``-ed, ``exec``-ed, or dynamically interpreted. The audit never
writes into the dataset tree.

Determinism (REV-07 ordering): sorted task iteration, ``sort_keys=True``
serialization, no clock — re-running over unchanged on-disk data is
byte-identical. The audit reads gitignored local datasets, so it is a
LOCAL maintainer step only: it never joins the ``make data`` chain and
CI never runs it.

Usage (from the repo root, REPO_ROOT-relative paths)::

    uv run --group data python script/audit_n_frequencies.py

Missing dataset dirs (the 7 GUE tasks pending the documented E2E-gate
re-extraction) print a WARNING naming the task and are reported as
explicit missing rows — the run still completes.

See also:
    - ``pipeline/run_finetune.py`` — the ``--subset_file`` consumer and
      the filter semantics mirrored here (:832-839).
    - ``script/make_dev_splits.py`` — the untrusted-CSV reading pattern.
    - ``tests/test_audit_n.py`` — the fixture-driven behavior contracts.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

# ===== Configuration =====

# The two pipeline charset classes (run_finetune.py:832-836, verbatim
# literals). Suite check_sequence compares set(seq.upper()) against
# set(valid_chars) — case-sensitive literal membership after uppercasing
# the sequence (the lowercase members of the charsets are therefore inert
# for the check; they are kept so the constants ARE the pipeline's).
STRICT_VALID_CHARS = "ACGTacgt|"       # models_no_char_n members
N_TOLERANT_VALID_CHARS = "ACGTNacgtn|"  # every other model
MIN_LENGTH = 0                          # validate_sequences(minl=0, ...)
MAX_LENGTH = 10010                      # validate_sequences(..., maxl=10010, ...)

_STRICT_SET = set(STRICT_VALID_CHARS)
_TOLERANT_SET = set(N_TOLERANT_VALID_CHARS)
# Characters NOT counted as non-ACGT: the ACGT alphabet in both cases,
# plus the "|" pair separator (GUE__EPI_GM12878 seq_sep — excluded from
# the non-ACGT census by plan contract). translate() with this table
# keeps exactly the counted characters (one C-level pass per row).
_NON_ACGT_DELETE = str.maketrans("", "", "ACGTacgt|")

CSV_HEADER = [
    "task", "split", "missing", "rows", "total_chars", "non_acgt_chars",
    "rows_with_non_acgt", "strict_survivors", "n_tolerant_survivors",
    "unified_eval_n",
]
SPLIT_ORDER = ("train", "dev", "test")


def resolve_dataset_dir(datasets_root: Path, dataset_path: str) -> Path:
    """Resolve a registry ``Dataset_path`` against the datasets root.

    ``Dataset_path`` values carry the ``datasets/`` prefix the pipeline
    resolves against ``pipeline/`` itself (``base_dir + Dataset_path``);
    against ``--datasets-root`` (default ``pipeline/datasets``) the
    prefix is stripped.

    Args:
        datasets_root (Path): Root containing the source-group dirs.
        dataset_path (str): Registry ``Dataset_path`` value.

    Returns:
        Path: The task's dataset directory.
    """
    rel = dataset_path.removeprefix("datasets/")
    return datasets_root / rel


def _survives(upper_chars: set[str], allowed: set[str], length: int) -> bool:
    """One row's suite check_sequence verdict for one charset class.

    Mirrors dnallm check_sequence @483a35c exactly: length window
    ``MIN_LENGTH <= length <= MAX_LENGTH`` and literal charset membership
    of ``set(seq.upper())`` (the ``gc=(0,1)`` range of the pipeline call
    can never reject — see the module docstring — and is not checked).

    Args:
        upper_chars (set[str]): ``set(seq.upper())`` of the row.
        allowed (set[str]): The class charset as a set.
        length (int): ``len(seq)``.

    Returns:
        bool: True iff the row survives this class.
    """
    return (
        MIN_LENGTH <= length <= MAX_LENGTH
        and upper_chars <= allowed
    )


def audit_split(
    csv_path: Path, task: str, split: str, *, collect_ids: bool = False,
) -> tuple[dict[str, Any] | None, list[int]]:
    """Census one split CSV under the untrusted-data discipline.

    Parse-only: malformed rows (field count differing from the header)
    are skipped per-row with a ``[Skip]`` line and never counted; nothing
    is dynamically interpreted; a missing/unreadable file or a header
    without a ``sequence`` column returns ``(None, [])`` after a WARNING.

    Args:
        csv_path (Path): The split CSV.
        task (str): Task name (error messages).
        split (str): Split name (error messages).
        collect_ids (bool): Also collect the ascending row indices
            surviving the STRICT class (the eval-subset candidates).
            Only the test split needs this.

    Returns:
        tuple: ``(stats, strict_ids)`` — ``stats`` is the split census
        dict or ``None`` when unreadable; ``strict_ids`` is the ascending
        strict-survivor row-index list (empty unless ``collect_ids``).
    """
    stats: dict[str, Any] = {
        "rows": 0,
        "total_chars": 0,
        "non_acgt_chars": 0,
        "rows_with_non_acgt": 0,
        "by_char": Counter(),
        "strict_survivors": 0,
        "n_tolerant_survivors": 0,
    }
    strict_ids: list[int] = []
    if not csv_path.is_file():
        print(f"WARNING {task}/{split}: {csv_path} not found — split "
              "excluded from the audit")
        return None, strict_ids
    try:
        with open(csv_path, "r", encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)  # bounded parsing: csv field-size limit applies
            try:
                header = next(reader, None)
                if header is None:
                    print(f"WARNING {task}/{split}: {csv_path} is empty "
                          "(no header line) — split excluded")
                    return None, strict_ids
                if "sequence" not in header:
                    print(f"WARNING {task}/{split}: {csv_path.name} header "
                          f"has no 'sequence' column: {header} — split "
                          "excluded")
                    return None, strict_ids
                seq_idx = header.index("sequence")
                row_index = -1
                for row in reader:
                    row_index += 1
                    if len(row) != len(header):
                        print(f"  [Skip] {task}/{split}: row "
                              f"{row_index + 2} of {csv_path.name} has "
                              f"{len(row)} fields, expected {len(header)} "
                              "— malformed row, not counted")
                        continue
                    seq = row[seq_idx]
                    stats["rows"] += 1
                    length = len(seq)
                    stats["total_chars"] += length
                    rest = seq.translate(_NON_ACGT_DELETE)
                    if rest:
                        stats["non_acgt_chars"] += len(rest)
                        stats["rows_with_non_acgt"] += 1
                        stats["by_char"].update(rest)
                    upper_chars = set(seq.upper())
                    if _survives(upper_chars, _STRICT_SET, length):
                        stats["strict_survivors"] += 1
                        if collect_ids:
                            strict_ids.append(row_index)
                    if _survives(upper_chars, _TOLERANT_SET, length):
                        stats["n_tolerant_survivors"] += 1
            except (csv.Error, UnicodeDecodeError) as exc:
                print(f"WARNING {task}/{split}: malformed CSV {csv_path}: "
                      f"{exc} — split excluded")
                return None, strict_ids
    except OSError as exc:
        print(f"WARNING {task}/{split}: cannot read {csv_path}: {exc} — "
              "split excluded")
        return None, strict_ids
    return stats, strict_ids


def audit_task(
    name: str, entry: dict[str, Any], datasets_root: Path,
) -> tuple[dict[str, Any], list[int] | None]:
    """Audit one registry task: its splits, unified eval N, subset IDs.

    A missing dataset dir yields the explicit missing row
    (``missing: true``, null splits/unified N) plus a WARNING naming the
    task — never a silent absence. A present dir without a readable test
    split gets a null unified N and no subset entry (the fairness map
    only promises tasks it could actually measure).

    Args:
        name (str): Registry task key.
        entry (dict): The task's registry entry (``Dataset_path``).
        datasets_root (Path): Root the dataset dir resolves against.

    Returns:
        tuple: ``(task_result, subset_ids)`` — the n_audit.json task
        object and the eval-subset ID list (``None`` when none can be
        computed).
    """
    dataset_dir = resolve_dataset_dir(datasets_root, entry["Dataset_path"])
    if not dataset_dir.is_dir():
        print(f"WARNING {name}: dataset dir not found at {dataset_dir} "
              "(pending re-extraction) — reported as a missing row")
        return {"missing": True, "unified_eval_n": None, "splits": None}, None

    splits: dict[str, Any] = {}
    test_strict_ids: list[int] = []
    for split in SPLIT_ORDER:
        stats, ids = audit_split(
            dataset_dir / f"{split}.csv", name, split,
            collect_ids=(split == "test"),
        )
        if stats is None:
            continue
        splits[split] = stats
        if split == "test":
            test_strict_ids = ids

    if "test" not in splits:
        return {"missing": False, "unified_eval_n": None, "splits": splits}, None

    test_stats = splits["test"]
    # F7 Q1: the unified eval N is the MIN over the per-model-class
    # surviving counts — the strictest class governs, so every model can
    # evaluate the same number of rows.
    unified = min(
        test_stats["strict_survivors"], test_stats["n_tolerant_survivors"]
    )
    # The subset IDs: ascending strict-passing row indices, truncated to
    # N. Every emitted ID itself survives the COMMON filter by
    # construction (Pitfall 4).
    subset_ids = sorted(test_strict_ids)[:unified]
    result = {
        "missing": False,
        "unified_eval_n": unified,
        "splits": splits,
    }
    return result, subset_ids


def audit_registry(
    registry: dict[str, Any], datasets_root: Path,
) -> tuple[dict[str, Any], dict[str, list[int]]]:
    """Audit every registry task in sorted order (deterministic).

    Args:
        registry (dict): The unified datasets registry.
        datasets_root (Path): Root the dataset dirs resolve against.

    Returns:
        tuple: ``(tasks, subsets)`` — the n_audit.json task map and the
        eval-subset ID map (tasks with no computable subset omitted).
    """
    tasks: dict[str, Any] = {}
    subsets: dict[str, list[int]] = {}
    for name in sorted(registry):
        result, subset_ids = audit_task(name, registry[name], datasets_root)
        tasks[name] = result
        if subset_ids is not None:
            subsets[name] = subset_ids
    return tasks, subsets


def _jsonify_split(stats: dict[str, Any]) -> dict[str, Any]:
    """Split census dict with the Counter serialized as a sorted dict."""
    out = dict(stats)
    out["by_char"] = dict(sorted(stats["by_char"].items()))
    return out


def emit_audit_json(path: Path, tasks: dict[str, Any]) -> None:
    """Write ``n_audit.json`` (sorted keys, no clock — byte-stable)."""
    payload = {
        "tasks": {
            name: {
                "missing": task["missing"],
                "unified_eval_n": task["unified_eval_n"],
                "splits": (
                    None
                    if task["splits"] is None
                    else {
                        split: _jsonify_split(stats)
                        for split, stats in task["splits"].items()
                    }
                ),
            }
            for name, task in tasks.items()
        }
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=4, sort_keys=True, ensure_ascii=False)
        fh.write("\n")


def emit_audit_csv(path: Path, tasks: dict[str, Any]) -> None:
    """Write ``n_audit.csv`` — flat table, header row first.

    One row per task x split for present tasks; one row per missing
    task (empty counts — the repo's missing-metric convention, never a
    zero that would read as "measured zero").
    """
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(CSV_HEADER)
        for name in sorted(tasks):
            task = tasks[name]
            if task["missing"] or not task["splits"]:
                unified = "" if task["unified_eval_n"] is None else task["unified_eval_n"]
                writer.writerow([name, "", "true" if task["missing"] else "false"] +
                                ["", "", "", "", "", "", unified])
                continue
            for split in SPLIT_ORDER:
                if split not in task["splits"]:
                    continue
                stats = task["splits"][split]
                writer.writerow([
                    name, split, "false", stats["rows"], stats["total_chars"],
                    stats["non_acgt_chars"], stats["rows_with_non_acgt"],
                    stats["strict_survivors"], stats["n_tolerant_survivors"],
                    task["unified_eval_n"],
                ])


def emit_subsets(path: Path, subsets: dict[str, list[int]]) -> None:
    """Write ``eval_subsets.json`` — one task per line, byte-stable.

    The plain ``json.dump`` of a >100k-element ID list would put the
    whole map on one line; one task per line stays greppable while
    remaining exactly the ``--subset_file`` input shape.
    """
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("{\n")
        names = sorted(subsets)
        for position, name in enumerate(names):
            ids = json.dumps(subsets[name], separators=(",", ":"))
            comma = "," if position < len(names) - 1 else ""
            fh.write(f"{json.dumps(name)}: {ids}{comma}\n")
        fh.write("}\n")


def _md_cell(value: int | None) -> str:
    """Markdown cell for an optional integer ('-' when absent)."""
    return "-" if value is None else str(value)


def emit_data_md(path: Path, tasks: dict[str, Any]) -> None:
    """Write ``DATA.md`` — the published appendix (whole file generated).

    One table row per registry task, present or missing; the prose
    blocks are fixed strings so regeneration is byte-identical.
    """
    lines = [
        "# Dataset Audit: N-Frequency and Non-ACGT Census (F7 / REV-07)",
        "",
        "> GENERATED by `script/audit_n_frequencies.py` — do not edit by",
        "> hand; regenerate from the repo root with",
        "> `uv run --group data python script/audit_n_frequencies.py`.",
        "> The audit reads the local (gitignored) dataset tree; it is a",
        "> maintainer step and never runs in CI.",
        "",
        "This appendix publishes the dataset census the reviewers asked",
        "for: per-split row counts and non-ACGT character totals for",
        "every task in the unified registry, plus the unified evaluation",
        "sample counts that make cross-model fairness directly provable",
        "(every model evaluates an identical number of test rows per",
        "task). The machine-readable forms are downloadable from the",
        "site as [`data/n_audit.json`](dnallm-mark/data/n_audit.json) and",
        "[`data/n_audit.csv`](dnallm-mark/data/n_audit.csv); the eval-",
        "subset ID lists consumed by the pipeline live in",
        "`pipeline/eval_subsets.json` (the `run_finetune.py",
        "--subset_file` input).",
        "",
        "## Method",
        "",
        "- **Filter semantics** mirror the pipeline exactly",
        "  (`run_finetune.py` `validate_sequences` at :837-839; suite",
        "  `check_sequence` @483a35c): a row survives a charset class",
        "  iff `set(seq.upper())` is contained in the class charset and",
        "  `0 <= len(sequence) <= 10010`.",
        "- **Two model classes** exist (the pipeline's per-model",
        "  conditional at :832-836): strict `ACGTacgt|`",
        "  (`models_no_char_n` members — one N discards the whole row)",
        "  and N-tolerant `ACGTNacgtn|` (every other model).",
        "- **Unified eval N** per task = min over the per-class test",
        "  survivor counts — the strictest class governs.",
        "- **Eval subset** = the first N strict-passing test-row indices",
        "  in ascending file order; every emitted ID itself survives the",
        "  common filter by construction.",
        "- **Non-ACGT census** counts characters outside `ACGTacgt` over",
        "  the sequence column, the `|` pair separator excluded;",
        "  per-character breakdowns are in the JSON artifact.",
        "- **Determinism**: sorted iteration, `sort_keys` serialization,",
        "  no clock — re-running over unchanged data is byte-identical.",
        "",
        "## Missing datasets (pending re-extraction)",
        "",
    ]
    missing = [name for name in sorted(tasks) if tasks[name]["missing"]]
    if missing:
        lines.append(
            f"{len(missing)} registry task(s) have no dataset directory "
            "on disk yet — the documented GUE archive re-extraction "
            "(suite double-nesting quirk) deferred to the E2' launch "
            "gate. They are reported below as missing rows and gate "
            "E2', not the audit:"
        )
        lines.append("")
        for name in missing:
            lines.append(f"- `{name}`")
    else:
        lines.append("None — every registry task has on-disk data.")
    lines += [
        "",
        "## Appendix: per-task census",
        "",
        (
            "| Task | Status | Train N | Dev N | Test N | Train non-ACGT"
            " | Dev non-ACGT | Test non-ACGT | Test strict-pass"
            " | Test N-tolerant | Unified eval N |"
        ),
        (
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---"
            " | --- |"
        ),
    ]
    for name in sorted(tasks):
        task = tasks[name]
        if task["missing"] or not task["splits"]:
            status = ("missing (re-extraction pending)" if task["missing"]
                      else "no readable splits")
            lines.append(
                f"| {name} | {status} | - | - | - | - | - | - | - | -"
                f" | {_md_cell(task['unified_eval_n'])} |"
            )
            continue
        splits = task["splits"]
        cells = []
        for split in SPLIT_ORDER:
            stats = splits.get(split)
            if stats is None:
                cells += ["-", "-"]
            else:
                cells += [str(stats["rows"]), str(stats["non_acgt_chars"])]
        test = splits.get("test")
        strict = "-" if test is None else str(test["strict_survivors"])
        tolerant = "-" if test is None else str(test["n_tolerant_survivors"])
        # Column order: Train N, Dev N, Test N, then non-ACGT per split —
        # cells were appended split-major, so interleave.
        rows_n = [cells[0], cells[2], cells[4]]
        non_acgt = [cells[1], cells[3], cells[5]]
        lines.append(
            f"| {name} | present | " + " | ".join(rows_n) + " | "
            + " | ".join(non_acgt) + f" | {strict} | {tolerant} | "
            f"{_md_cell(task['unified_eval_n'])} |"
        )
    lines.append("")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def write_artifacts(
    tasks: dict[str, Any],
    subsets: dict[str, list[int]],
    data_dir: Path,
    subsets_out: Path,
    data_md: Path,
) -> list[Path]:
    """Emit every artifact (deterministic; parent dirs created).

    Args:
        tasks (dict): The n_audit task map (from :func:`audit_registry`).
        subsets (dict): The eval-subset ID map.
        data_dir (Path): Destination for n_audit.json / n_audit.csv.
        subsets_out (Path): Destination for eval_subsets.json.
        data_md (Path): Destination for the generated DATA.md.

    Returns:
        list[Path]: The written artifact paths.
    """
    for directory in (data_dir, subsets_out.parent, data_md.parent):
        directory.mkdir(parents=True, exist_ok=True)
    json_path = data_dir / "n_audit.json"
    csv_path = data_dir / "n_audit.csv"
    emit_audit_json(json_path, tasks)
    emit_audit_csv(csv_path, tasks)
    emit_subsets(subsets_out, subsets)
    emit_data_md(data_md, tasks)
    return [json_path, csv_path, subsets_out, data_md]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments (REPO_ROOT-relative defaults)."""
    parser = argparse.ArgumentParser(
        prog="audit_n_frequencies",
        description=(
            "N-frequency / non-ACGT census over the on-disk dataset tree "
            "+ unified eval-subset emission (F7 / REV-07)."
        ),
    )
    parser.add_argument(
        "--datasets-root", type=Path, default=REPO_ROOT / "pipeline" / "datasets",
        help="root containing the source-group dataset dirs "
             "(default: %(default)s)",
    )
    parser.add_argument(
        "--registry-dir", type=Path, default=REPO_ROOT / "pipeline",
        help="directory holding datasets_info.json (default: %(default)s)",
    )
    parser.add_argument(
        "--data-dir", type=Path, default=REPO_ROOT / "dnallm-mark" / "data",
        help="destination for n_audit.json / n_audit.csv (default: %(default)s)",
    )
    parser.add_argument(
        "--subsets-out", type=Path, default=REPO_ROOT / "pipeline" / "eval_subsets.json",
        help="destination for the eval-subset ID map consumed by "
             "run_finetune.py --subset_file (default: %(default)s)",
    )
    parser.add_argument(
        "--data-md", type=Path, default=REPO_ROOT / "DATA.md",
        help="destination for the generated DATA.md appendix "
             "(default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: audit the registry, emit the artifacts."""
    args = parse_args(argv)
    registry_path = args.registry_dir / "datasets_info.json"
    with open(registry_path, "r", encoding="utf-8") as fh:
        registry = json.load(fh)

    tasks, subsets = audit_registry(registry, args.datasets_root)
    artifacts = write_artifacts(
        tasks, subsets, args.data_dir, args.subsets_out, args.data_md,
    )

    present = sum(1 for task in tasks.values() if not task["missing"])
    missing = [name for name in sorted(tasks) if tasks[name]["missing"]]
    print(f"Audited {len(tasks)} registry task(s): {present} present, "
          f"{len(missing)} missing")
    for name in missing:
        print(f"  WARNING {name}: reported as a missing row "
              "(pending re-extraction)")
    for path in artifacts:
        print(f"  ✅ {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
