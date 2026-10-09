"""
Carve stratified 10% dev splits for Dev-empty benchmark tasks (F1 / REV-01).

Purpose
-------
The dev-side benchmark datasets arrived without dev (eval) splits for 18
tasks (16 binary + 2 multiclass). Without an eval split, checkpoint
selection under ``load_best_model_at_end`` / early stopping has nothing
to evaluate against — and the dnallm suite's EVAL-01 contract
(``dnallm/finetune/trainer.py`` L568-605 @ revision 483a35c) either
hard-errors or, if ``finetune.allow_test_as_eval`` were ever enabled,
would optimize on the test set. This script carves a dev split for every
Dev-empty task so neither can happen.

Split policy (exact)
--------------------
For each class ``c`` with ``n_c >= 2`` training rows, dev receives
exactly ``max(1, n_c // 10)`` rows of that class. A class with exactly 1
row contributes 0 dev rows (carving it would leave train without the
class). Classes are visited in sorted label order under ONE
``np.random.default_rng(42)`` per task; the per-class selection is
``rng.permutation(class_indices)[:dev_c]``. dev.csv and the rewritten
train.csv preserve the original train.csv row order (selection picks row
indices; rows are never re-shuffled), so the same input + seed
regenerates byte-identical CSVs (auditable, diffable).

Input / output
--------------
- Input: ``pipeline/datasets_info.json`` (the D-10 unified registry) and
  ``pipeline/datasets/<Dataset_path>/train.csv``. Two CSV layouts occur
  across the benchmark and both are handled via the header: 2-column
  ``sequence,label`` and 3-column ``name,sequence,label``. Labels must be
  integers (single-label classification covers all 18 tasks; multilabel
  ``;`` labels and regression labels abort that task loudly).
- Output per split task: ``dev.csv`` next to train.csv (new), train.csv
  rewritten without the carved rows (all other columns carried verbatim,
  LF line endings), and the registry's ``Train``/``Dev`` values updated
  in place (``indent=4, sort_keys=True, ensure_ascii=False`` — matching
  the converter-produced serialization, so later diffs are value-only).
- Count guard: the registry ``Train`` count must equal the on-disk
  train.csv data-row count before carving (research assumption A4); any
  mismatch aborts that task loudly (SystemExit naming the task and both
  numbers) with zero writes.
- Idempotency: a task whose dev.csv already exists AND whose registry Dev
  is non-zero is skipped with a loud message and zero writes.

Usage (from repo root)::

    ~/.local/bin/uv run --group data python script/make_dev_splits.py
    ~/.local/bin/uv run --group data python script/make_dev_splits.py --check

``--check`` verifies registry/disk agreement over every registry entry
(registry Train == train.csv rows; registry Dev > 0 with a dev.csv whose
row count == Dev) and writes nothing. A dataset directory not found at
its Dataset_path — the known suite double-nesting unzip quirk
(suite-name/suite-name/task-dir), deferred to the E2E gate — emits a
WARNING line and is excluded from the pass count; any hard mismatch
exits non-zero with a per-task report. In split mode a Dev-empty task
with an unlocatable directory is a hard error (flatten the directory
locally and re-run — a file move, not a model run).

Recovery: the original full train.csv is re-downloadable from Zenodo
(see the README dataset section) if a re-carve is ever needed; the carve
itself is deterministic (seed=42), so re-running on the original file
reproduces the same splits.

See also:
    ``pipeline/run_finetune.py`` — refuses Dev-less tasks before model
    load (the driver-side half of the EVAL-01 two-layer enforcement).
    ``pipeline/datasets_info.json`` — the unified registry this updates.
    ``script/convert_registry.py`` — the D-10 registry converter whose
    serialization discipline the registry writes mirror.
"""

import argparse
import csv
import json
from pathlib import Path

import numpy as np

# ===== Configuration =====

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "pipeline" / "datasets_info.json"
DATASETS_ROOT = REPO_ROOT / "pipeline" / "datasets"
SEED = 42


class TaskSkip(Exception):
    """A malformed/inconsistent dataset aborts its task; the run continues."""


def parse_args():
    """Parse CLI arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Carve stratified 10% dev splits (seed=42) for "
                    "Dev-empty benchmark tasks; updates the unified registry"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Verify registry/disk agreement only (writes nothing); "
             "exit non-zero on any hard mismatch"
    )
    return parser.parse_args()


def select_dev_indices(labels, seed=SEED):
    """Select the dev-split row indices for a label sequence.

    Stratification: classes are visited in sorted label order under one
    ``np.random.default_rng(seed)`` instance; each class with
    ``n_c >= 2`` rows contributes exactly ``max(1, n_c // 10)`` rows
    (a 1-row class contributes none — it stays entirely in train).

    Args:
        labels (list[str]): Label value per row (grouping key, verbatim).
        seed (int): Per-task RNG seed (determinism contract).

    Returns:
        list[int]: Sorted dev row indices (original file order).
    """
    by_label = {}
    for index, label in enumerate(labels):
        by_label.setdefault(label, []).append(index)
    rng = np.random.default_rng(seed)
    dev_indices = set()
    for label in sorted(by_label):
        indices = by_label[label]
        if len(indices) < 2:
            continue  # rare-class policy: 1-row class stays in train
        dev_c = max(1, len(indices) // 10)
        picked = rng.permutation(indices)[:dev_c]
        dev_indices.update(int(i) for i in picked)
    return sorted(dev_indices)


def carve_stratified_dev(rows, seed=SEED):
    """Carve a stratified dev split from parsed rows.

    Args:
        rows (list[tuple]): ``(sequence, label)`` pairs in file order.
        seed (int): Per-task RNG seed (default 42).

    Returns:
        tuple[list, list]: ``(dev_rows, train_rows)`` — the carved dev
        rows sorted by original index, and the remaining train rows in
        original order. Rows are never re-shuffled.
    """
    labels = [label for _sequence, label in rows]
    dev_index = set(select_dev_indices(labels, seed))
    dev_rows = [rows[i] for i in sorted(dev_index)]
    train_rows = [row for i, row in enumerate(rows) if i not in dev_index]
    return dev_rows, train_rows


def read_csv_rows(csv_path, task_name):
    """Read a benchmark CSV as ``(header, raw_rows)``.

    Args:
        csv_path (Path): CSV file (LF or CRLF line endings both accepted).
        task_name (str): Calling task name for error messages.

    Returns:
        tuple[list[str], list[list[str]]]: Header fields and raw data rows.

    Raises:
        TaskSkip: If the file is empty or any row's field count differs
            from the header's (malformed row — the task aborts).
    """
    with open(csv_path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        if header is None:
            raise TaskSkip(f"[Skip] {task_name}: {csv_path} is empty "
                           "(no header line)")
        rows = list(reader)
    for lineno, row in enumerate(rows, start=2):
        if len(row) != len(header):
            raise TaskSkip(
                f"[Skip] {task_name}: row {lineno} of {csv_path.name} has "
                f"{len(row)} fields, expected {len(header)} — malformed row"
            )
    return header, rows


def parse_labels(rows, label_idx, task_name):
    """Extract and integer-validate the label column.

    Args:
        rows (list[list[str]]): Raw CSV data rows.
        label_idx (int): Index of the label column in the header.
        task_name (str): Calling task name for error messages.

    Returns:
        list[str]: Label values (verbatim strings — the grouping key).

    Raises:
        TaskSkip: If any label is not an integer (stratified carving is
            only defined for single-label classification; multilabel
            ";" labels and regression labels abort the task).
    """
    labels = []
    for lineno, row in enumerate(rows, start=2):
        raw = row[label_idx]
        try:
            int(raw)
        except ValueError:
            raise TaskSkip(
                f"[Skip] {task_name}: row {lineno} label {raw!r} is not an "
                "integer — stratified carving is only defined for "
                "single-label classification"
            ) from None
        labels.append(raw)
    return labels


def write_csv(path, header, rows):
    """Write a benchmark CSV (header + rows, LF line endings)."""
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def apply_registry_update(registry, name, train_count, dev_count):
    """Update one task's Train/Dev in the registry dict (in place).

    Args:
        registry (dict): The unified registry (mutated in place).
        name (str): Task key.
        train_count (int): New post-carve train row count.
        dev_count (int): New dev row count.
    """
    entry = registry[name]
    entry["Train"] = train_count
    entry["Dev"] = dev_count


def write_registry(path, registry):
    """Write the unified registry with the converter's serialization
    (``indent=4, sort_keys=True, ensure_ascii=False`` + trailing newline)
    so registry rewrites stay value-only diffs."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(registry, fh, indent=4, sort_keys=True,
                  ensure_ascii=False)
        fh.write("\n")


def split_task(name, entry, registry, datasets_root=DATASETS_ROOT):
    """Carve the dev split for one task, all-or-nothing.

    Order of operations makes an interrupted run self-healing on re-run:
    the deterministic carve overwrites any half-written dev.csv with the
    same bytes before train.csv and the registry are updated.

    Args:
        name (str): Task key (for messages and the registry update).
        entry (dict): The task's unified-registry entry (mutated on
            success: Train/Dev updated to the on-disk counts).
        registry (dict): The full registry (unused directly; the entry is
            part of it — kept in the signature for call-site symmetry).
        datasets_root (Path): Root that Dataset_path resolves against.

    Returns:
        str: ``"split"`` if the task was carved, ``"skipped"`` if
        idempotently skipped (zero writes).

    Raises:
        SystemExit: If the dataset dir is unlocatable, or the registry
            Train count disagrees with the on-disk train.csv data rows
            (count guard — nothing is written).
        TaskSkip: If the CSV is malformed (bad header, wrong field count,
            non-integer label) or Dev is registered but dev.csv is
            missing (inconsistent state — never re-carved).
    """
    dataset_dir = datasets_root / entry["Dataset_path"]
    train_csv = dataset_dir / "train.csv"
    dev_csv = dataset_dir / "dev.csv"

    if dev_csv.exists() and entry.get("Dev"):
        print(f"  [Skip] {name}: dev.csv exists and Dev={entry['Dev']} "
              "— nothing to do")
        return "skipped"
    if entry.get("Dev") and not dev_csv.exists():
        raise TaskSkip(
            f"[Skip] {name}: registry Dev={entry['Dev']} but dev.csv is "
            f"missing at {dev_csv} — inconsistent state, refusing to "
            "re-carve (that would double-carve train); reconcile manually"
        )
    if not dataset_dir.is_dir():
        raise SystemExit(
            f"[Error] {name}: dataset dir not found at {dataset_dir} — if "
            "this is the suite double-nesting unzip quirk "
            "(suite-name/suite-name/task-dir), flatten the directory "
            "locally and re-run (see the module docstring)"
        )

    header, rows = read_csv_rows(train_csv, name)
    try:
        label_idx = header.index("label")
    except ValueError:
        raise TaskSkip(
            f"[Skip] {name}: {train_csv.name} header has no 'label' "
            f"column: {header}"
        ) from None
    labels = parse_labels(rows, label_idx, name)

    # Count guard (research assumption A4): registry Train must equal the
    # on-disk data-row count, or training-step math (num_train_data) and
    # the carve counts would both be built on sand.
    registry_train = int(entry["Train"])
    if registry_train != len(rows):
        raise SystemExit(
            f"[Error] {name}: registry Train={registry_train} but "
            f"{train_csv} has {len(rows)} data rows — refusing to carve "
            "(registry/disk mismatch); reconcile the registry first"
        )

    dev_index = set(select_dev_indices(labels))
    dev_rows = [rows[i] for i in sorted(dev_index)]
    train_rows = [row for i, row in enumerate(rows) if i not in dev_index]

    write_csv(dev_csv, header, dev_rows)
    write_csv(train_csv, header, train_rows)
    apply_registry_update(registry, name, len(train_rows), len(dev_rows))
    print(f"  ✅ {name}: carved {len(dev_rows)} dev rows "
          f"(train {registry_train} -> {len(train_rows)})")
    return "split"


def run_check(registry, datasets_root=DATASETS_ROOT):
    """Verify registry/disk agreement over every registry entry.

    Writes nothing. Checks per locatable entry: registry Train equals the
    train.csv data-row count, registry Dev > 0, and dev.csv exists with
    exactly Dev rows and the same header as train.csv.

    Args:
        registry (dict): The unified registry.
        datasets_root (Path): Root that Dataset_path resolves against.

    Returns:
        tuple[int, list[str], list[str]]: ``(ok_count, warnings,
        failures)`` — warnings are unlocatable-dirs (excluded from the
        pass count), failures are hard mismatches.
    """
    ok, warnings, failures = 0, [], []
    for name, entry in registry.items():
        dataset_dir = datasets_root / entry["Dataset_path"]
        if not dataset_dir.is_dir():
            warnings.append(
                f"WARNING {name}: dataset dir not found at {dataset_dir} "
                "(double-nesting quirk deferred to the E2E gate) — "
                "excluded from the pass count"
            )
            continue
        dev = int(entry.get("Dev") or 0)
        if dev <= 0:
            failures.append(
                f"MISMATCH {name}: registry Dev={dev} — every task needs a "
                "dev split (run script/make_dev_splits.py without --check)"
            )
            continue
        dev_csv = dataset_dir / "dev.csv"
        if not dev_csv.is_file():
            failures.append(
                f"MISMATCH {name}: registry Dev={dev} but dev.csv missing "
                f"at {dev_csv}"
            )
            continue
        try:
            header, rows = read_csv_rows(dataset_dir / "train.csv", name)
            dev_header, dev_rows = read_csv_rows(dev_csv, name)
        except TaskSkip as exc:
            failures.append(f"MISMATCH {name}: unreadable CSV — {exc}")
            continue
        if int(entry["Train"]) != len(rows):
            failures.append(
                f"MISMATCH {name}: registry Train={entry['Train']} but "
                f"train.csv has {len(rows)} rows"
            )
        elif len(dev_rows) != dev:
            failures.append(
                f"MISMATCH {name}: registry Dev={dev} but dev.csv has "
                f"{len(dev_rows)} rows"
            )
        elif dev_header != header:
            failures.append(
                f"MISMATCH {name}: dev.csv header {dev_header} != train.csv "
                f"header {header}"
            )
        else:
            ok += 1
    return ok, warnings, failures


def main():
    """Entry point: split every Dev-empty task, or verify with --check."""
    args = parse_args()
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    if args.check:
        ok, warnings, failures = run_check(
            registry, datasets_root=DATASETS_ROOT)
        for line in warnings:
            print(line)
        for line in failures:
            print(line)
        if failures:
            raise SystemExit(
                f"[Error] {len(failures)} hard mismatch(es) — see the "
                "MISMATCH lines above"
            )
        print(f"✅ OK: registry/disk agreement for {ok} task(s) "
              f"({len(warnings)} unlocatable dir(s) excluded with WARNING)")
        return

    split_names = [name for name, entry in registry.items()
                   if not entry.get("Dev")]
    if not split_names:
        print("✅ No Dev-empty tasks — nothing to do.")
        return
    print(f"Carving dev splits for {len(split_names)} Dev-empty task(s) "
          f"(seed={SEED})")
    done = skipped = failed = 0
    for name in split_names:
        try:
            status = split_task(name, registry[name], registry,
                                datasets_root=DATASETS_ROOT)
        except TaskSkip as exc:
            print(f"  {exc}")
            failed += 1
            continue
        if status == "split":
            write_registry(REGISTRY_PATH, registry)
            done += 1
        else:
            skipped += 1
    print(f"✅ {done} split, {skipped} skipped, {failed} failed; "
          f"registry written: {REGISTRY_PATH}")
    if failed:
        raise SystemExit(
            f"[Error] {failed} task(s) failed to split — see the [Skip] "
            "lines above"
        )


if __name__ == "__main__":
    main()
