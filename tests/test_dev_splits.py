"""
Unit tests for ``script/make_dev_splits.py`` (F1 / REV-01 part 1).

Every behavior bullet of the plan's Task 2 is pinned here:

- **determinism** — same input + seed=42 carves byte-identical dev.csv and
  train.csv (pure-function equality AND end-to-end file bytes);
- **stratification policy** — per class with ``n_c >= 2`` rows, dev
  receives exactly ``max(1, n_c // 10)`` rows; every such class is
  represented; total dev size is within ``num_classes`` of the 10% target;
- **rare-class policy** — a 1-row class contributes 0 dev rows (stays
  entirely in train); a 2-row class contributes 1, leaving 1 train row;
- **count guard** — a registry/on-disk Train mismatch aborts the task
  loudly (SystemExit naming the task and both numbers) and writes nothing;
- **idempotency** — a task whose dev.csv exists AND whose registry Dev is
  non-zero is skipped with a loud message and zero writes;
- **registry write discipline** — Train/Dev updates change exactly those
  two values and repeated writes are byte-stable (converter-matching
  ``indent=4, sort_keys=True, ensure_ascii=False`` serialization).

The split functions are pure/fixture-driven (conftest puts ``script/`` on
``sys.path``); no real dataset under ``pipeline/datasets/`` is touched.

See also:
    - ``script/make_dev_splits.py`` — the generator under test.
    - ``tests/test_registry_unification.py`` — the registry contract the
      updated file must keep satisfying.
"""

import json

import make_dev_splits  # conftest puts script/ on sys.path
import pytest

LABEL_HEADER_2COL = ["sequence", "label"]
LABEL_HEADER_3COL = ["name", "sequence", "label"]


def synth_rows(n, labels_for):
    """Build ``(sequence, label)`` rows; ``labels_for(i)`` gives label i."""
    return [(f"SEQ{i:04d}", labels_for(i)) for i in range(n)]


def write_task_dir(root, path, header, rows, label_idx=-1):
    """Materialize a synthetic dataset dir with a train.csv.

    Args:
        root (Path): datasets root (tmp_path).
        path (str): Dataset_path value (e.g. ``suite/task``).
        header (list[str]): CSV header fields.
        rows (list[tuple]): ``(sequence, label)`` rows; a 3-column header
            gets synthetic name cells.
        label_idx (int): ignored; derived from the header length.

    Returns:
        Path: the task directory.
    """
    task_dir = root / path
    task_dir.mkdir(parents=True)
    lines = [",".join(header)]
    for i, (seq, label) in enumerate(rows):
        if len(header) == 3:
            lines.append(f"row{i:04d},{seq},{label}")
        else:
            lines.append(f"{seq},{label}")
    (task_dir / "train.csv").write_text("\n".join(lines) + "\n",
                                        encoding="utf-8")
    return task_dir


def make_entry(path, train, dev=0):
    """Build a unified-registry dataset entry fixture."""
    return {
        "Index": 1, "Dataset_name": path.split("/")[-1],
        "Dataset_path": path, "Train": train, "Test": 10, "Dev": dev,
        "type": "binary", "labels": 2, "length": 500, "metric": "f1",
        "Category": "Plants",
    }


# ===== carve_stratified_dev: policy + determinism (pure) =====


def test_carve_is_deterministic():
    """Same rows + seed=42 -> identical (dev, train) pair, twice."""
    rows = synth_rows(100, lambda i: str(i % 2))
    dev1, train1 = make_dev_splits.carve_stratified_dev(rows)
    dev2, train2 = make_dev_splits.carve_stratified_dev(rows)
    assert dev1 == dev2
    assert train1 == train2


def test_stratification_policy_exact_per_class_counts():
    """Classes with n_c >= 2 contribute exactly max(1, n_c // 10) dev
    rows each; every such class is represented; the total is within
    num_classes of the 10% target."""
    # 50 a / 7 b / 2 c -> 5 + 1 + 1 = 7 dev rows (target 5.9, 3 classes)
    rows = ([("s", "a")] * 50 + [("s", "b")] * 7 + [("s", "c")] * 2)
    dev, _train = make_dev_splits.carve_stratified_dev(rows)
    dev_by_class = {}
    for _seq, label in dev:
        dev_by_class[label] = dev_by_class.get(label, 0) + 1
    assert dev_by_class == {"a": 5, "b": 1, "c": 1}
    n = len(rows)
    assert abs(len(dev) - n / 10) <= 3  # within num_classes of the target


def test_rare_class_policy():
    """A 1-row class contributes 0 dev rows (stays entirely in train);
    a 2-row class contributes exactly 1, leaving 1 train row."""
    rows = [("only-x", "x"), ("y1", "y"), ("y2", "y"), ("z1", "z"), ("z2", "z")]
    dev, train = make_dev_splits.carve_stratified_dev(rows)
    dev_labels = [label for _seq, label in dev]
    train_labels = [label for _seq, label in train]
    assert "x" not in dev_labels  # 1-row class: 0 dev rows
    assert "x" in train_labels  # ...and it stays in train
    assert dev_labels.count("y") == 1  # 2-row class: 1 dev row
    assert train_labels.count("y") == 1  # ...leaving 1 train row
    assert dev_labels.count("z") == 1
    assert train_labels.count("z") == 1


def test_output_order_preserved():
    """Dev rows are sorted by original index; train rows keep the
    original file order (rows are never re-shuffled on write)."""
    rows = synth_rows(40, lambda i: str(i % 2))
    dev, train = make_dev_splits.carve_stratified_dev(rows)
    assert dev == sorted(dev, key=lambda r: int(r[0][3:]))  # SEQ index order
    assert train == [r for r in rows if r not in set(dev)]  # original order
    assert len(dev) + len(train) == 40
    assert not set(dev) & set(train)


# ===== split_task: file-level orchestration =====


def test_split_task_end_to_end_byte_determinism(tmp_path):
    """Carving the same synthetic train.csv twice (fresh copies, seed=42)
    produces byte-identical dev.csv and train.csv, updates the registry
    entry to the on-disk counts, and supports both CSV layouts."""
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    for root in (root_a, root_b):
        write_task_dir(root, "suite/task", LABEL_HEADER_2COL,
                       synth_rows(40, lambda i: str(i % 2)))

    def carve(root):
        registry = {"suite__task": make_entry("suite/task", 40)}
        status = make_dev_splits.split_task(
            "suite__task", registry["suite__task"], registry,
            datasets_root=root)
        dev = (root / "suite/task/dev.csv").read_text(encoding="utf-8")
        train = (root / "suite/task/train.csv").read_text(encoding="utf-8")
        return status, dev, train, registry["suite__task"]

    status_a, dev_a, train_a, entry_a = carve(root_a)
    status_b, dev_b, train_b, entry_b = carve(root_b)
    assert status_a == status_b == "split"
    assert dev_a == dev_b  # byte-identical dev.csv
    assert train_a == train_b  # byte-identical rewritten train.csv
    assert entry_a == entry_b  # identical registry updates
    assert entry_a["Dev"] == 4  # 20+20 rows -> 2 dev per class
    assert entry_a["Train"] == 36
    # rows preserved verbatim, dev keeps original order
    dev_rows = dev_a.strip().splitlines()
    assert dev_rows[0] == "sequence,label"
    assert len(dev_rows) == 5  # header + 4
    seqs = [line.split(",")[0] for line in dev_rows[1:]]
    assert seqs == sorted(seqs, key=lambda s: int(s[3:]))


def test_split_task_handles_three_column_layout(tmp_path):
    """The name,sequence,label layout (NT/plant tasks) carves with the
    name column carried through verbatim."""
    rows = synth_rows(20, lambda i: str(i % 2))
    write_task_dir(tmp_path, "nt/task", LABEL_HEADER_3COL, rows)
    registry = {"nt__task": make_entry("nt/task", 20)}
    status = make_dev_splits.split_task(
        "nt__task", registry["nt__task"], registry, datasets_root=tmp_path)
    assert status == "split"
    dev_lines = (tmp_path / "nt/task/dev.csv").read_text(
        encoding="utf-8").strip().splitlines()
    assert dev_lines[0] == "name,sequence,label"
    assert len(dev_lines) == 3  # header + 2 (one per class)
    for line in dev_lines[1:]:
        name, seq, _label = line.split(",")
        assert name.startswith("row")  # name cells preserved
        assert seq.startswith("SEQ")


def test_count_guard_aborts_and_writes_nothing(tmp_path):
    """A registry/on-disk Train mismatch aborts the task loudly with the
    task name and both numbers (SystemExit) and writes nothing."""
    write_task_dir(tmp_path, "suite/task", LABEL_HEADER_2COL,
                   synth_rows(40, lambda i: str(i % 2)))
    registry = {"suite__task": make_entry("suite/task", 50)}  # stale count
    train_before = (tmp_path / "suite/task/train.csv").read_bytes()
    with pytest.raises(SystemExit, match=r"50.*40|40.*50"):
        make_dev_splits.split_task(
            "suite__task", registry["suite__task"], registry,
            datasets_root=tmp_path)
    assert not (tmp_path / "suite/task/dev.csv").exists()  # nothing written
    assert (tmp_path / "suite/task/train.csv").read_bytes() == train_before
    assert registry["suite__task"]["Train"] == 50  # registry untouched
    assert registry["suite__task"]["Dev"] == 0


def test_idempotent_skip_writes_nothing(tmp_path):
    """dev.csv existing AND registry Dev non-zero -> loud skip, zero writes."""
    task_dir = write_task_dir(tmp_path, "suite/task", LABEL_HEADER_2COL,
                              synth_rows(36, lambda i: str(i % 2)))
    (task_dir / "dev.csv").write_text("sequence,label\n", encoding="utf-8")
    registry = {"suite__task": make_entry("suite/task", 36, dev=4)}
    train_before = (task_dir / "train.csv").read_bytes()
    dev_before = (task_dir / "dev.csv").read_bytes()
    status = make_dev_splits.split_task(
        "suite__task", registry["suite__task"], registry,
        datasets_root=tmp_path)
    assert status == "skipped"
    assert (task_dir / "train.csv").read_bytes() == train_before
    assert (task_dir / "dev.csv").read_bytes() == dev_before
    assert registry["suite__task"]["Train"] == 36  # entry untouched


def test_dev_registered_but_missing_skips_loudly(tmp_path):
    """Dev non-zero but dev.csv absent is an inconsistent state: the task
    is skipped loudly (never re-carved — that would double-carve train)."""
    write_task_dir(tmp_path, "suite/task", LABEL_HEADER_2COL,
                   synth_rows(36, lambda i: str(i % 2)))
    registry = {"suite__task": make_entry("suite/task", 36, dev=4)}
    with pytest.raises(make_dev_splits.TaskSkip, match="dev.csv"):
        make_dev_splits.split_task(
            "suite__task", registry["suite__task"], registry,
            datasets_root=tmp_path)
    assert not (tmp_path / "suite/task/dev.csv").exists()


def test_malformed_row_skips_task(tmp_path):
    """A wrong-column-count or non-integer label aborts the task loudly
    (TaskSkip) with zero writes — splits are all-or-nothing per task."""
    task_dir = tmp_path / "suite/task"
    task_dir.mkdir(parents=True)
    bad = "sequence,label\nSEQ0001,0\nSEQ0002,not-an-int\n"
    (task_dir / "train.csv").write_text(bad, encoding="utf-8")
    registry = {"suite__task": make_entry("suite/task", 2)}
    with pytest.raises(make_dev_splits.TaskSkip):
        make_dev_splits.split_task(
            "suite__task", registry["suite__task"], registry,
            datasets_root=tmp_path)
    assert not (task_dir / "dev.csv").exists()

    (task_dir / "train.csv").write_text(
        "sequence,label\nSEQ0001,0,extra\n", encoding="utf-8")
    with pytest.raises(make_dev_splits.TaskSkip):
        make_dev_splits.split_task(
            "suite__task", registry["suite__task"], registry,
            datasets_root=tmp_path)
    assert not (task_dir / "dev.csv").exists()


def test_missing_dataset_dir_aborts(tmp_path):
    """A Dev-empty task whose dataset dir is absent aborts loudly (the
    double-nesting quirk remediation pointer)."""
    registry = {"suite__task": make_entry("suite/absent", 40)}
    with pytest.raises(SystemExit, match="suite/absent"):
        make_dev_splits.split_task(
            "suite__task", registry["suite__task"], registry,
            datasets_root=tmp_path)


# ===== registry write discipline =====


def test_registry_update_changes_exactly_train_dev(tmp_path):
    """apply_registry_update + write_registry: exactly the two values
    change, every other key/value is untouched, repeated writes are
    byte-stable, and the serialization matches the converter's."""
    registry = {
        "b_task": make_entry("suite/b", 10, dev=1),
        "a_task": make_entry("suite/a", 40),
    }
    registry["a_task"]["Category"] = "Animals"
    path = tmp_path / "datasets_info.json"
    make_dev_splits.write_registry(path, registry)
    before = json.loads(path.read_text(encoding="utf-8"))

    make_dev_splits.apply_registry_update(registry, "a_task", 36, 4)
    make_dev_splits.write_registry(path, registry)
    after = json.loads(path.read_text(encoding="utf-8"))

    assert after["a_task"]["Train"] == 36  # the two values change
    assert after["a_task"]["Dev"] == 4
    assert after["a_task"]["Category"] == "Animals"  # everything else kept
    assert after["b_task"] == before["b_task"]  # sibling untouched
    changed = {k for k in after["a_task"]
               if after["a_task"][k] != before["a_task"][k]}
    assert changed == {"Train", "Dev"}

    first = path.read_bytes()
    make_dev_splits.write_registry(path, json.loads(first))  # repeat
    assert path.read_bytes() == first  # byte-stable
    assert first.endswith(b"\n")  # converter-matching trailing newline
    assert b'"Category": "Animals"' in first  # indent=4, sorted keys


# ===== --check mode =====


def test_run_check_reports_agreement_mismatch_and_missing_dir(tmp_path):
    """--check's verifier: consistent tasks count OK; a Train mismatch is
    a hard failure; an unlocatable dir is a WARNING excluded from the
    pass count. Writes nothing."""
    write_task_dir(tmp_path, "suite/good", LABEL_HEADER_2COL,
                   synth_rows(36, lambda i: str(i % 2)))
    (tmp_path / "suite/good/dev.csv").write_text(
        "sequence,label\nSEQ0001,0\nSEQ0002,1\n", encoding="utf-8")
    write_task_dir(tmp_path, "suite/bad", LABEL_HEADER_2COL,
                   synth_rows(30, lambda i: str(i % 2)))
    (tmp_path / "suite/bad/dev.csv").write_text(
        "sequence,label\nSEQ0001,0\n", encoding="utf-8")
    registry = {
        "suite__good": make_entry("suite/good", 36, dev=2),
        "suite__bad": make_entry("suite/bad", 40, dev=1),  # Train mismatch
        "suite__gone": make_entry("suite/gone", 10, dev=1),  # dir absent
    }
    ok, warnings, failures = make_dev_splits.run_check(
        registry, datasets_root=tmp_path)
    assert ok == 1  # the good task only
    assert len(warnings) == 1 and "suite__gone" in warnings[0]
    assert len(failures) == 1 and "suite__bad" in failures[0]
    assert "40" in failures[0] and "30" in failures[0]
