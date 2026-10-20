"""
Materialize deterministic stratified subset datasets for smoke/validation
sweeps (Phase 15, VAL-02 / D15-05..D15-08).

Purpose
-------
Reads REAL benchmark dataset CSVs and writes a 5%-scale stratified subset
of each requested task: subset ``train/dev/test.csv`` files under a
dedicated subset output root, plus a dedicated subset registry directory
carrying MEASURED row counts. Subset runs then train through the frozen
Phase 13/14 dispatch CLI with zero pipeline code changes: the child
(``run_finetune.py``) always loads the OFFICIAL registries and joins
``dataset_base + Dataset_path``, so subsets are materialized at the
official-relative ``Dataset_path`` under an overridden ``--dataset_root``
and the subset registry keeps OFFICIAL keys with ``Dataset_path`` VERBATIM
(the two-layer registry seam — only ``Train``/``Dev``/``Test`` become the
measured subset counts).

Sampling semantics (exact, D15-06)
----------------------------------
Per split INDEPENDENTLY (train, dev, and test each sampled on its own):

- ``k = max(1, int(n * fraction))`` capped at ``n`` — the small-split
  floor-of-1 rule (a 0-row dev/test split breaks DNADataset; splits with
  fewer than 20 rows at 5% still keep one row). ``fraction`` defaults to
  0.05.
- ``actual_fraction = k / n`` is recorded per split in the subset
  registry's ``subset`` provenance object.
- Stratification: rows are grouped by their integer label; ``k`` is
  allocated across classes by LARGEST REMAINDER over the proportional
  class quotas (integer arithmetic, no float drift), visiting classes in
  sorted-label order. Ties on remainder are broken so the EARLIEST sorted
  label receives the extra row (e.g. a balanced binary split's extra row
  goes to label 0).
- Selection: each class's index list is shuffled with ONE
  ``random.Random(seed)`` instance shared across the whole run and
  consumed in a fixed iteration order — tasks in ``--tasks`` order as
  given on the CLI, splits in train/dev/test order, classes in
  sorted-label order. Fixed inputs + seed therefore regenerate
  byte-identical outputs (run-twice idempotent; single-operator offline
  use — concurrent invocations into the same roots are not coordinated).
- Emitted rows keep ORIGINAL FILE ORDER (selection picks row indices;
  rows are never re-shuffled in the output).

Input / output
--------------
- Input: the OFFICIAL ``pipeline/datasets_info.json`` /
  ``pipeline/models_info.json`` (always — read-only; the third-registry-
  class discipline) and the three CSVs at
  ``{dataset-root}/{Dataset_path}/{train,dev,test}.csv``.
- Per-task validation before any write: the declared registry
  ``Train``/``Dev``/``Test`` must equal the measured on-disk CSV data-row
  counts (count guard); the header must carry ``sequence`` and ``label``
  columns; every row must match the header field count; labels must be
  integers (multilabel ``;`` labels and regression labels abort the task
  loudly). A header-only or 0-data-row split refuses the task. Any
  refusal writes NOTHING for that task.
- Output: ``{output-root}/datasets/{Dataset_path}/{train,dev,test}.csv``
  (LF line endings, byte-identical on every platform) and
  ``{registry-dir}/datasets_info.json`` (selected entries: official keys
  and ``Dataset_path`` verbatim, only ``Train``/``Dev``/``Test`` replaced
  by measured subset counts, plus a ``subset`` provenance object with
  ``generator``/``seed``/``fraction``/``actual_fraction``/``source_counts``)
  and ``{registry-dir}/models_info.json`` (the ``--models`` entries
  copied VERBATIM from the official registry). All JSON is
  ``indent=4, sort_keys=True, ensure_ascii=False`` + trailing newline.

Isolation (D15-07 — third registry class)
-----------------------------------------
The generator NEVER opens the official registry files or the user custom
registry files for writing. It refuses to run when the resolved
``--registry-dir`` equals or contains the official registry dir
(``pipeline/``) or resolves to the custom registry dir (resolved
read-only exactly like ``pipeline/registry_loader.custom_registry_dir``:
``DNALLMMARK_CUSTOM_REGISTRY_DIR`` > ``XDG_CONFIG_HOME``/dnallmmark >
``~/.config/dnallmmark``). Subset registries/config/output roots never
share a root with real runs (e.g. output under ``pipeline/datasets-smoke/``
+ ``pipeline/registry-smoke/``, both gitignored).

Usage (from repo root)::

    uv run --group data python script/make_subset_datasets.py \
        --dataset-root <real> --output-root <subset> \
        --registry-dir <subset registry> --models <keys> \
        --tasks <keys> [--fraction 0.05] [--seed 42]

See also:
    ``script/make_dev_splits.py`` — the stratified-CSV-sampling script
    whose structure (fail-fast CSV validation, count guard, byte-stable
    writes) this generator mirrors.
    ``pipeline/registry_loader.py`` — the official/custom registry
    resolution whose custom-dir rule is reimplemented here read-only.
    ``docs/multi-gpu.md`` — the dispatch-mode smoke procedure that
    consumes these subsets via ``--dataset_root``.
"""

import argparse
import csv
import json
import os
import random
from pathlib import Path

# ===== Configuration =====

REPO_ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_REGISTRY_DIR = REPO_ROOT / "pipeline"
OFFICIAL_DATASETS_PATH = OFFICIAL_REGISTRY_DIR / "datasets_info.json"
OFFICIAL_MODELS_PATH = OFFICIAL_REGISTRY_DIR / "models_info.json"
# The RNG consumption-order contract: tasks in --tasks CLI order, splits
# in this fixed order, classes in sorted-label order (D15-06).
SPLITS = ("train", "dev", "test")
GENERATOR_NAME = "script/make_subset_datasets.py"
DEFAULT_FRACTION = 0.05
DEFAULT_SEED = 42


class TaskSkip(Exception):
    """A malformed/inconsistent dataset aborts its task; the run continues."""


def parse_args():
    """Parse CLI arguments.

    Returns:
        argparse.Namespace: Parsed arguments.

    Raises:
        SystemExit: On missing required flags (argparse) or an empty
            ``--tasks``/``--models``/out-of-range ``--fraction`` value.
    """
    parser = argparse.ArgumentParser(
        description="Materialize deterministic stratified subset datasets "
                    "(seed-governed, default 5%) plus a dedicated subset "
                    "registry for smoke/validation sweeps"
    )
    parser.add_argument(
        "--dataset-root", required=True,
        help="REAL datasets root (the root Dataset_path resolves against)"
    )
    parser.add_argument(
        "--output-root", required=True,
        help="subset datasets root to write under (never a real-run root)"
    )
    parser.add_argument(
        "--registry-dir", required=True,
        help="subset registry OUTPUT dir (never the official pipeline/ or "
             "the custom registry dir — refused)"
    )
    parser.add_argument(
        "--models", required=True,
        help="comma-separated model keys copied verbatim into the subset "
             "models_info.json"
    )
    parser.add_argument(
        "--tasks", required=True,
        help="comma-separated dataset keys (official registry keys)"
    )
    parser.add_argument(
        "--fraction", type=float, default=DEFAULT_FRACTION,
        help="per-split sampling fraction (default 0.05)"
    )
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SEED,
        help="sampling seed governing the shared random.Random instance "
             "(default 42)"
    )
    args = parser.parse_args()
    args.tasks = [task.strip() for task in args.tasks.split(",") if task.strip()]
    args.models = [m.strip() for m in args.models.split(",") if m.strip()]
    if not args.tasks:
        raise SystemExit("[Error] --tasks is empty — nothing to generate")
    if not args.models:
        raise SystemExit("[Error] --models is empty — no registry to copy")
    if not 0 < args.fraction <= 1:
        raise SystemExit(
            f"[Error] --fraction must be in (0, 1], got {args.fraction}"
        )
    return args


def custom_registry_dir():
    """Resolve the user-owned custom registry directory (read-only twin).

    Reimplements ``pipeline/registry_loader.custom_registry_dir``
    resolution WITHOUT importing pipeline code (the generator stays a
    standalone offline script): ``DNALLMMARK_CUSTOM_REGISTRY_DIR`` whole-
    dir override > ``XDG_CONFIG_HOME``/dnallmmark > ``~/.config/
    dnallmmark``. Nothing here reads or writes the custom files.

    Returns:
        Path: The custom overlay directory (may not exist).
    """
    override = os.environ.get("DNALLMMARK_CUSTOM_REGISTRY_DIR")
    if override:
        return Path(override)
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "dnallmmark"
    return Path.home() / ".config" / "dnallmmark"


def ensure_registry_isolation(registry_dir):
    """Refuse registry dirs overlapping the official or custom registries.

    D15-07 (third registry class): the subset registry must never land on
    the official registry dir (``pipeline/`` — that would overwrite the
    official ``{models,datasets}_info.json``), on any directory CONTAINING
    it, or on the custom registry dir (that would overwrite the user's
    ``custom_{models,datasets}.json``).

    Args:
        registry_dir (str): The ``--registry-dir`` CLI value.

    Returns:
        Path: The resolved registry dir (safe to write under).

    Raises:
        SystemExit: When the resolved dir violates the isolation rule —
            before any file is opened for writing.
    """
    resolved = Path(registry_dir).expanduser().resolve()
    official = OFFICIAL_REGISTRY_DIR.resolve()
    if resolved == official or official.is_relative_to(resolved):
        raise SystemExit(
            f"[Error] --registry-dir {resolved} equals or contains the "
            f"official registry dir {official} — subset registries are a "
            "third registry class and must never overwrite official files "
            "(D15-07)"
        )
    custom = custom_registry_dir().expanduser().resolve()
    if resolved == custom:
        raise SystemExit(
            f"[Error] --registry-dir {resolved} resolves to the custom "
            "registry dir — subset registries are a third registry class "
            "and must never overwrite custom files (D15-07)"
        )
    return resolved


def subset_size(n, fraction):
    """Compute the pinned D15-06 split size.

    Rule: ``k = max(1, int(n * fraction))`` capped at ``n`` — the
    floor-of-1 small-split rule (never a 0-row split), never more rows
    than the split holds.

    Args:
        n (int): Data-row count of the split (must be >= 1 in the
            generator flow; 0-row splits are refused before sampling).
        fraction (float): Sampling fraction.

    Returns:
        int: The subset row count ``k`` for the split.
    """
    if n <= 0:
        return 0
    return min(max(1, int(n * fraction)), n)


def select_stratified_indices(labels, k, rng):
    """Select ``k`` row indices stratified by label.

    Allocation: ``k`` is distributed over classes by LARGEST REMAINDER on
    the integer proportional quotas (``k * class_size // total`` with the
    residue breaking ties); classes are visited in sorted-label order and
    remainder ties give the extra row to the EARLIEST sorted label. Each
    class's index list is shuffled with the SHARED ``rng`` in
    sorted-label visit order (the run-level consumption-order contract),
    and the returned indices are sorted — rows are emitted in ORIGINAL
    FILE ORDER.

    Args:
        labels (list[str]): Integer-valid label value per row (grouping
            key, verbatim string).
        k (int): Rows to select (``0 <= k <= len(labels)``).
        rng (random.Random): The shared per-run instance — deterministic
            given fixed seed + consumption order.

    Returns:
        list[int]: Sorted selected row indices (original file order).
    """
    by_label = {}
    for index, label in enumerate(labels):
        by_label.setdefault(label, []).append(index)
    order = sorted(by_label, key=int)
    total = len(labels)
    base = {}
    remainder = {}
    for label in order:
        whole, frac = divmod(k * len(by_label[label]), total)
        base[label] = whole
        remainder[label] = frac
    extra = k - sum(base.values())
    # Largest remainder first; the stable sort keeps sorted-label order on
    # remainder ties, so the earliest sorted label receives the extra row.
    for label in sorted(order, key=lambda lab: -remainder[lab])[:extra]:
        base[label] += 1
    picked = set()
    for label in order:
        indices = list(by_label[label])
        rng.shuffle(indices)
        picked.update(indices[: base[label]])
    return sorted(picked)


def read_csv_rows(csv_path, task_name, split):
    """Read one split CSV as ``(header, raw_rows)``.

    Args:
        csv_path (Path): The split CSV file.
        task_name (str): Calling task name for error messages.
        split (str): Split name ("train"/"dev"/"test") for messages.

    Returns:
        tuple[list[str], list[list[str]]]: Header fields and raw data rows.

    Raises:
        TaskSkip: If the file is missing/unreadable, empty (no header), a
            header-only file with zero data rows, or any row's field
            count differs from the header's (malformed row — the V5
            input-validation control for untrusted downloaded CSVs).
    """
    try:
        with open(csv_path, "r", encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            if header is None:
                raise TaskSkip(
                    f"[Skip] {task_name}: {csv_path} is empty (no header "
                    "line)"
                )
            rows = list(reader)
    except OSError as exc:
        raise TaskSkip(
            f"[Skip] {task_name}: cannot read {csv_path}: {exc}"
        ) from None
    if not rows:
        raise TaskSkip(
            f"[Skip] {task_name}: {csv_path} is header-only (0 data rows) "
            "— a 0-row split breaks DNADataset; refusing"
        )
    for lineno, row in enumerate(rows, start=2):
        if len(row) != len(header):
            raise TaskSkip(
                f"[Skip] {task_name}: row {lineno} of {split}.csv has "
                f"{len(row)} fields, expected {len(header)} — malformed row"
            )
    return header, rows


def label_column_index(header, task_name, split):
    """Locate the label column, validating the ``sequence,label`` contract.

    Args:
        header (list[str]): CSV header fields.
        task_name (str): Calling task name for error messages.
        split (str): Split name for messages.

    Returns:
        int: Index of the ``label`` column.

    Raises:
        TaskSkip: If the header carries no ``sequence`` or no ``label``
            column (the benchmark CSV contract).
    """
    if "sequence" not in header or "label" not in header:
        raise TaskSkip(
            f"[Skip] {task_name}: {split}.csv header {header} violates the "
            "sequence,label contract (needs both columns)"
        )
    return header.index("label")


def parse_labels(rows, label_idx, task_name, split):
    """Extract and integer-validate the label column.

    Args:
        rows (list[list[str]]): Raw CSV data rows.
        label_idx (int): Index of the label column in the header.
        task_name (str): Calling task name for error messages.
        split (str): Split name for messages.

    Returns:
        list[str]: Label values (verbatim strings — the grouping key).

    Raises:
        TaskSkip: If any label is not an integer (stratified sampling is
            only defined for single-label classification; multilabel ";"
            labels and regression labels abort the task loudly).
    """
    labels = []
    for lineno, row in enumerate(rows, start=2):
        raw = row[label_idx]
        try:
            int(raw)
        except ValueError:
            raise TaskSkip(
                f"[Skip] {task_name}: row {lineno} of {split}.csv label "
                f"{raw!r} is not an integer — stratified sampling is only "
                "defined for single-label classification"
            ) from None
        labels.append(raw)
    return labels


def write_csv(path, header, rows):
    """Write one subset CSV (header + rows, LF line endings, byte-stable
    on every platform via ``lineterminator="\\n"`` on a ``newline=""``
    handle)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def write_json(path, payload):
    """Write one registry JSON with the converter serialization
    (``indent=4, sort_keys=True, ensure_ascii=False`` + trailing newline)
    so registry writes stay value-only diffs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=4, sort_keys=True, ensure_ascii=False)
        fh.write("\n")


def generate_subset_task(name, official_entry, dataset_root, output_root,
                         fraction, seed, rng):
    """Generate the subset for one task, all-or-nothing.

    Validation (CSV reads, header/label checks, the declared-vs-measured
    count guard) completes for ALL THREE splits before any write, so any
    refusal leaves zero output files. Sampling then consumes the shared
    ``rng`` in train/dev/test order (the run-level determinism contract).

    Args:
        name (str): Official registry task key.
        official_entry (dict): The task's official registry entry
            (read-only; the subset entry is a copy).
        dataset_root (str): REAL datasets root (Dataset_path resolves
            against it).
        output_root (str): Subset output root.
        fraction (float): Sampling fraction.
        seed (int): The run seed (recorded in the provenance object).
        rng (random.Random): The shared per-run instance.

    Returns:
        dict: The subset registry entry — official keys and Dataset_path
            VERBATIM, ``Train``/``Dev``/``Test`` replaced by measured
            subset counts, plus the ``subset`` provenance object.

    Raises:
        TaskSkip: On any validation failure (zero writes).
    """
    dataset_dir = Path(dataset_root) / official_entry["Dataset_path"]
    declared = {}
    for split in SPLITS:
        try:
            declared[split] = int(official_entry[split.capitalize()])
        except (KeyError, TypeError, ValueError):
            raise TaskSkip(
                f"[Skip] {name}: official registry entry has no integer "
                f"{split.capitalize()} count — refusing"
            ) from None

    # Read and validate ALL splits first (zero writes on any refusal).
    split_data = {}
    for split in SPLITS:
        csv_path = dataset_dir / f"{split}.csv"
        header, rows = read_csv_rows(csv_path, name, split)
        label_idx = label_column_index(header, name, split)
        labels = parse_labels(rows, label_idx, name, split)
        split_data[split] = (header, rows, labels)

    # Count guard: declared registry counts must equal measured data rows
    # (the make_dev_splits discipline — sampling on a mismatched base
    # would build subset counts on sand).
    for split in SPLITS:
        measured = len(split_data[split][1])
        if measured != declared[split]:
            raise TaskSkip(
                f"[Skip] {name}: registry {split.capitalize()}="
                f"{declared[split]} but {split}.csv has {measured} data "
                "rows — refusing (declared/measured mismatch); zero writes"
            )

    # Sample + write per split (train/dev/test order — RNG contract).
    subset_entry = dict(official_entry)
    out_dir = Path(output_root) / official_entry["Dataset_path"]
    counts = {}
    actual_fraction = {}
    source_counts = {}
    for split in SPLITS:
        header, rows, labels = split_data[split]
        n = len(rows)
        k = subset_size(n, fraction)
        picked = select_stratified_indices(labels, k, rng)
        write_csv(out_dir / f"{split}.csv", header,
                  [rows[i] for i in picked])
        counts[split] = k
        actual_fraction[split] = k / n
        source_counts[split] = n

    subset_entry["Train"] = counts["train"]
    subset_entry["Dev"] = counts["dev"]
    subset_entry["Test"] = counts["test"]
    subset_entry["subset"] = {
        "generator": GENERATOR_NAME,
        "seed": seed,
        "fraction": fraction,
        "actual_fraction": actual_fraction,
        "source_counts": source_counts,
    }
    return subset_entry


def main():
    """Entry point: generate subsets for every --tasks key, then write the
    subset registry. Per-task refusals continue the run; any failure exits
    non-zero."""
    args = parse_args()
    registry_dir = ensure_registry_isolation(args.registry_dir)

    # The OFFICIAL registries are always the read source (third-registry-
    # class discipline — never a writable view).
    datasets_info = json.loads(
        OFFICIAL_DATASETS_PATH.read_text(encoding="utf-8"))
    models_info = json.loads(
        OFFICIAL_MODELS_PATH.read_text(encoding="utf-8"))

    unknown_tasks = [t for t in args.tasks if t not in datasets_info]
    if unknown_tasks:
        raise SystemExit(
            f"[Error] unknown --tasks key(s) {unknown_tasks} — not in the "
            f"official registry {OFFICIAL_DATASETS_PATH}"
        )
    unknown_models = [m for m in args.models if m not in models_info]
    if unknown_models:
        raise SystemExit(
            f"[Error] unknown --models key(s) {unknown_models} — not in "
            f"the official registry {OFFICIAL_MODELS_PATH}"
        )

    # ONE rng instance for the whole run, consumed in fixed order: tasks
    # in --tasks CLI order, splits in SPLITS order, classes sorted.
    rng = random.Random(args.seed)
    subset_entries = {}
    failed = 0
    for name in args.tasks:
        try:
            entry = generate_subset_task(
                name, datasets_info[name], args.dataset_root,
                args.output_root, args.fraction, args.seed, rng)
        except TaskSkip as exc:
            print(f"  {exc}")
            failed += 1
            continue
        subset_entries[name] = entry
        print(f"  ✅ {name}: train {entry['Train']} / dev {entry['Dev']} / "
              f"test {entry['Test']} rows "
              f"(source {entry['subset']['source_counts']['train']}/"
              f"{entry['subset']['source_counts']['dev']}/"
              f"{entry['subset']['source_counts']['test']})")

    if subset_entries:
        write_json(registry_dir / "datasets_info.json", subset_entries)
        write_json(registry_dir / "models_info.json",
                   {key: models_info[key] for key in args.models})

    print(f"✅ {len(subset_entries)} subset dataset(s) written under "
          f"{args.output_root} (fraction={args.fraction}, seed="
          f"{args.seed}); registry: {registry_dir}")
    if failed:
        raise SystemExit(
            f"[Error] {failed} task(s) refused — see the [Skip] lines above"
        )


if __name__ == "__main__":
    main()
