"""
Pins for ``script/make_subset_datasets.py`` (Phase 15, VAL-02 — D15-06
sampling semantics, D15-07 registry isolation, D15-08 multiclass fixture,
D15-15 CPU-gate safety).

Nine behaviors, mirroring the ``tests/test_determinism.py`` idioms
(subprocess runs with ``sys.executable`` + pinned cwd, full-tree byte
snapshots keyed by POSIX-relative path):

1. run-twice byte-identity: two subprocess runs over the same fabricated
   official-key tree into two fresh tmp roots produce byte-identical
   trees and registries (fresh roots make the file-set comparison exact —
   a silently-not-written file cannot pass vacuously, the WR-04
   discipline in its strongest form).
2. stratification math: the measured label distributions of the two real
   sweep datasets (5mC 1055/1055, 117/117, 1172/1172; emp_H3 5821/6150,
   735/762, 742/755) allocate exactly ``k = max(1, int(n * 0.05))`` rows
   by largest remainder (ties → earliest sorted label).
3. multiclass: the committed 3-class fixture (``tests/fixtures/
   subset_fixture``) allocates k=3 as 1/1/1 — both real sweep datasets
   are binary, so the fixture is where multiclass stratification is
   proven (D15-08).
4. floor rule: ``k = max(1, int(n * fraction))`` capped at ``n`` — never
   0, never above n; ``actual_fraction == k/n`` is recorded in the
   registry (asserted end-to-end in behavior 6).
5. ordering: selected rows keep original file order, and the same inputs
   + seed select identical rows twice.
6. registry fidelity: official keys + official ``Dataset_path`` verbatim,
   only ``Train``/``Dev``/``Test`` replaced by measured counts (+ the
   ``subset`` provenance object); ``models_info`` entries parsed-equal to
   the official registry.
7. isolation (D15-07): sha256 of the official registry files — and the
   custom registry files when present (skip-if-absent, machine-
   independent) — is unchanged across EVERY generator run in this module
   (autouse fixture); the generator refuses a ``--registry-dir`` that
   equals or contains the official registry dir or resolves to the
   custom registry dir, with zero writes.
8. fail-fast (V5): header-only split, declared≠measured counts,
   malformed rows, and non-integer (multilabel/regression) labels each
   refuse the task loudly with zero output writes and a non-zero exit.
9. no writes outside the explicit ``--output-root``/``--registry-dir``:
   the input tree is read-only and nothing lands outside the two roots.

Note on emp_H3 test split (37/37, not the plan bullet's 36/38): the
research table's allocation column is internally inconsistent with the
pinned largest-remainder rule (its own train row already contradicts the
rule its dev/test rows follow). Measured labels 742/755 give quotas
74*742/1497 = 36.68 and 74*755/1497 = 37.32 — floors 36+37, extra row to
the LARGER remainder (label 0) → 37/37. Verified against the real probe
CSVs downloaded this session; dev (735/762 → 36/38) matches the bullet.

TDD shape: the production behavior landed with this plan's Task-1 tracer
(the 12-05 proof-suite precedent) — non-vacuity is proven by throwaway
mutations (tie-break flip, floor-rule drop, order-emission drop) that
were confirmed to redden the matching pins, reverted, never committed.

See also:
    - ``script/make_subset_datasets.py`` — the generator under test.
    - ``tests/test_determinism.py`` — the run-twice byte-identity idiom.
    - ``tests/test_dev_splits.py`` — the fail-fast CSV validation twin.
"""

import csv
import hashlib
import json
import os
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

import make_subset_datasets  # conftest puts script/ on sys.path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPO_ROOT / "script" / "make_subset_datasets.py"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "subset_fixture"
OFFICIAL_REGISTRY_PATHS = (
    REPO_ROOT / "pipeline" / "models_info.json",
    REPO_ROOT / "pipeline" / "datasets_info.json",
)
TASK_KEY = "iDNA_ABF_datasets__5mC"
MODEL_KEY = "plant-dnabert-6mer"
# The fabricated tree honors the official registry's declared counts
# (train/dev/test 2110/234/2344, i%2 labels → 1055/1055, 117/117,
# 1172/1172) so the count guard passes and the official-registry
# validation path is exercised end-to-end.
FABRICATED_SPLITS = (("train", 2110), ("dev", 234), ("test", 2344))


# ===== Shared helpers =====


def _run_generator(dataset_root, output_root, registry_dir, cwd, env=None,
                   tasks=TASK_KEY, models=MODEL_KEY):
    """Run the generator once as a subprocess (flags fully explicit)."""
    argv = [
        sys.executable, str(GENERATOR),
        "--dataset-root", str(dataset_root),
        "--output-root", str(output_root),
        "--registry-dir", str(registry_dir),
        "--models", models,
        "--tasks", tasks,
        "--fraction", "0.05",
        "--seed", "42",
    ]
    return subprocess.run(
        argv, cwd=str(cwd), capture_output=True, text=True, check=False,
        env=env,
    )


def _fail_msg(proc):
    """Format a failed subprocess run for assertion messages."""
    return (f"exit {proc.returncode}\n--- stdout ---\n{proc.stdout}"
            f"\n--- stderr ---\n{proc.stderr}")


def _tree_snapshot(root):
    """Snapshot a tree as ``{relative_posix_path: bytes}`` over its files."""
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(Path(root).rglob("*"))
        if p.is_file()
    }


def _write_split(base, split, rows):
    """Write one fabricated split CSV (header + rows, LF endings)."""
    base.mkdir(parents=True, exist_ok=True)
    with open(base / f"{split}.csv", "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["sequence", "label"])
        writer.writerows(rows)


def _binary_rows(n):
    """Balanced binary rows ``("SEQ%06d", i % 2)`` in file order."""
    return [(f"SEQ{i:06d}", i % 2) for i in range(n)]


@pytest.fixture(scope="session")
def five_mc_tree(tmp_path_factory):
    """The fabricated official-key 5mC tree (read-only input, shared)."""
    root = tmp_path_factory.mktemp("fivemc-src") / "ds"
    base = root / "datasets" / "iDNA_ABF_datasets" / "5mC"
    for split, n in FABRICATED_SPLITS:
        _write_split(base, split, _binary_rows(n))
    return root


@pytest.fixture
def five_mc_run(five_mc_tree, tmp_path):
    """One completed generator run over the shared fabricated tree."""
    out_root = tmp_path / "sub"
    reg_dir = tmp_path / "reg"
    proc = _run_generator(five_mc_tree, out_root, reg_dir, cwd=tmp_path)
    assert proc.returncode == 0, _fail_msg(proc)
    return out_root, reg_dir


# ===== Behavior 7 (autouse): registries are never written =====


def _protected_registry_hashes():
    """sha256 the official registries + custom files when present.

    Custom files are resolved exactly like the generator's read-only
    twin of ``registry_loader.custom_registry_dir``; absent files are
    skipped so the pin stays machine-independent.
    """
    hashes = {}
    for path in OFFICIAL_REGISTRY_PATHS:
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    custom_dir = make_subset_datasets.custom_registry_dir()
    for name in ("custom_models.json", "custom_datasets.json"):
        candidate = custom_dir / name
        if candidate.is_file():
            hashes[str(candidate)] = hashlib.sha256(
                candidate.read_bytes()).hexdigest()
    return hashes


@pytest.fixture(autouse=True)
def _registries_never_written():
    """D15-07 strongest form: official + custom registry hashes are
    unchanged across every generator run this module performs."""
    before = _protected_registry_hashes()
    yield
    after = _protected_registry_hashes()
    assert after == before, (
        f"registry file(s) changed during the test: "
        f"{sorted(k for k in after if after[k] != before.get(k))}"
    )


# ===== Behavior 1: run-twice byte-identity =====


def test_run_twice_byte_identical(five_mc_tree, tmp_path):
    """Two subprocess runs over the same tree into two fresh roots
    produce byte-identical subset trees AND registries (D15-06)."""
    snapshots = []
    for run in (1, 2):
        out_root = tmp_path / f"sub{run}"
        reg_dir = tmp_path / f"reg{run}"
        proc = _run_generator(five_mc_tree, out_root, reg_dir, cwd=tmp_path)
        assert proc.returncode == 0, _fail_msg(proc)
        snapshot = _tree_snapshot(out_root)
        snapshot.update(_tree_snapshot(reg_dir))
        snapshots.append(snapshot)
    assert snapshots[0] == snapshots[1], (
        "generator is not byte-deterministic across runs; first differing "
        f"files: {sorted(k for k in set(snapshots[0]) | set(snapshots[1]) if snapshots[0].get(k) != snapshots[1].get(k))[:10]}"
    )
    # The expected full output set (three subset CSVs + two registries).
    assert set(snapshots[0]) == {
        "datasets/iDNA_ABF_datasets/5mC/train.csv",
        "datasets/iDNA_ABF_datasets/5mC/dev.csv",
        "datasets/iDNA_ABF_datasets/5mC/test.csv",
        "datasets_info.json",
        "models_info.json",
    }


# ===== Behavior 2: stratification math (pure helper) =====


@pytest.mark.parametrize(
    "name,n,class_sizes,expected_k,expected_alloc",
    [
        ("5mC train", 2110, (1055, 1055), 105, (53, 52)),
        ("5mC dev", 234, (117, 117), 11, (6, 5)),
        ("5mC test", 2344, (1172, 1172), 117, (59, 58)),
        ("emp_H3 train", 11971, (5821, 6150), 598, (291, 307)),
        ("emp_H3 dev", 1497, (735, 762), 74, (36, 38)),
        # 36/38 in the plan bullet is the research table's arithmetic slip
        # (see module docstring): largest remainder gives label 0 the
        # extra row → 37/37. Labels measured from the real probe CSVs.
        ("emp_H3 test", 1497, (742, 755), 74, (37, 37)),
    ],
)
def test_stratification_math(name, n, class_sizes, expected_k,
                             expected_alloc):
    """Measured 5% math: k sizing + largest-remainder allocation over the
    real sweep datasets' measured label distributions (D15-06)."""
    labels = ["0"] * class_sizes[0] + ["1"] * class_sizes[1]
    k = make_subset_datasets.subset_size(n, 0.05)
    assert k == expected_k, f"{name}: k={k}, expected {expected_k}"
    picked = make_subset_datasets.select_stratified_indices(
        labels, k, random.Random(42))
    assert len(picked) == k, f"{name}: picked {len(picked)} rows"
    counts = Counter(labels[i] for i in picked)
    assert (counts["0"], counts["1"]) == expected_alloc, (
        f"{name}: allocation ({counts['0']}, {counts['1']}), "
        f"expected {expected_alloc}"
    )


# ===== Behavior 3: multiclass fixture (D15-08) =====


def test_multiclass_fixture_stratification():
    """The committed 3-class fixture (train 60 rows, 20/20/20) at 5%
    selects k=3 as exactly 1/1/1 per class."""
    with open(FIXTURE_DIR / "train.csv", "r", encoding="utf-8",
              newline="") as fh:
        rows = list(csv.reader(fh))[1:]
    assert len(rows) == 60
    labels = [row[1] for row in rows]
    assert dict(sorted(Counter(labels).items())) == {"0": 20, "1": 20,
                                                     "2": 20}
    k = make_subset_datasets.subset_size(60, 0.05)
    assert k == 3
    picked = make_subset_datasets.select_stratified_indices(
        labels, k, random.Random(42))
    counts = Counter(labels[i] for i in picked)
    assert dict(sorted(counts.items())) == {"0": 1, "1": 1, "2": 1}


# ===== Behavior 4: the floor rule (never 0, capped at n) =====


@pytest.mark.parametrize("n,expected", [(12, 1), (19, 1), (20, 1), (1, 1)])
def test_floor_rule_small_splits(n, expected):
    """Splits with n < 20 at 5% still keep exactly one row (a 0-row
    dev/test split breaks DNADataset — Pitfall 5)."""
    assert make_subset_datasets.subset_size(n, 0.05) == expected


def test_floor_rule_never_zero_and_capped():
    """k stays within [1, n] for every viable n, and fraction=1.0 takes
    the whole split (the cap)."""
    for n in range(1, 60):
        k = make_subset_datasets.subset_size(n, 0.05)
        assert 1 <= k <= n, f"n={n}: k={k} outside [1, {n}]"
    assert make_subset_datasets.subset_size(5, 1.0) == 5


# ===== Behavior 5: original file order + stable selection =====


def test_rows_keep_original_file_order_and_stable_selection(five_mc_tree,
                                                            tmp_path):
    """Selected rows are emitted in original file order (monotonically
    non-decreasing source indices) and the same inputs + seed select
    identical rows across independent runs."""
    picked_runs = []
    for run in (1, 2):
        out_root = tmp_path / f"sub{run}"
        proc = _run_generator(five_mc_tree, out_root, tmp_path / f"reg{run}",
                              cwd=tmp_path)
        assert proc.returncode == 0, _fail_msg(proc)
        csv_path = (out_root / "datasets" / "iDNA_ABF_datasets" / "5mC"
                    / "train.csv")
        with open(csv_path, "r", encoding="utf-8", newline="") as fh:
            sequences = [row[0] for row in list(csv.reader(fh))[1:]]
        assert len(sequences) == 105
        indexes = [int(seq[3:]) for seq in sequences]  # "SEQ%06d"
        assert indexes == sorted(indexes), (
            "subset rows are not in original file order"
        )
        picked_runs.append(indexes)
    assert picked_runs[0] == picked_runs[1], (
        "selection differs across runs with identical inputs + seed"
    )


# ===== Behavior 6: registry fidelity (official keys verbatim) =====


def test_registry_fidelity(five_mc_run):
    """The subset registry keeps official keys + official Dataset_path
    verbatim with ONLY Train/Dev/Test replaced (+ provenance), and the
    subset models_info entries are parsed-equal to the official ones."""
    out_root, reg_dir = five_mc_run

    official_datasets = json.loads(
        (REPO_ROOT / "pipeline" / "datasets_info.json").read_text(
            encoding="utf-8"))
    official_entry = official_datasets[TASK_KEY]
    subset_datasets = json.loads(
        (reg_dir / "datasets_info.json").read_text(encoding="utf-8"))
    assert set(subset_datasets) == {TASK_KEY}
    subset_entry = subset_datasets[TASK_KEY]

    assert subset_entry["Dataset_path"] == official_entry["Dataset_path"]
    assert (subset_entry["Train"], subset_entry["Dev"],
            subset_entry["Test"]) == (105, 11, 117)
    ignored = {"Train", "Dev", "Test", "subset"}
    assert {k: v for k, v in subset_entry.items() if k not in ignored} == \
        {k: v for k, v in official_entry.items() if k not in ignored}, (
            "subset entry altered fields beyond Train/Dev/Test"
        )

    provenance = subset_entry["subset"]
    assert provenance["seed"] == 42
    assert provenance["fraction"] == 0.05
    for split, (k, n) in {"train": (105, 2110), "dev": (11, 234),
                          "test": (117, 2344)}.items():
        assert provenance["actual_fraction"][split] == k / n, split
        assert provenance["source_counts"][split] == n, split

    official_models = json.loads(
        (REPO_ROOT / "pipeline" / "models_info.json").read_text(
            encoding="utf-8"))
    subset_models = json.loads(
        (reg_dir / "models_info.json").read_text(encoding="utf-8"))
    assert subset_models == {MODEL_KEY: official_models[MODEL_KEY]}

    # The output tree sits at the official-relative Dataset_path under the
    # subset root — the child-resolution seam (zero pipeline changes).
    assert (out_root / official_entry["Dataset_path"] / "train.csv"
            ).is_file()


# ===== Behavior 7 (refusals): registry-dir isolation =====


def test_registry_dir_refusals(five_mc_tree, tmp_path):
    """The generator refuses --registry-dir on/containing the official
    registry dir and on the custom registry dir — zero writes (D15-07)."""
    out_root = tmp_path / "out"

    # Equals the official registry dir (would overwrite the official
    # registries themselves).
    proc = _run_generator(five_mc_tree, out_root, REPO_ROOT / "pipeline",
                          cwd=tmp_path)
    assert proc.returncode != 0, _fail_msg(proc)
    assert "official registry dir" in proc.stdout + proc.stderr
    assert not out_root.exists()

    # Contains the official registry dir (e.g. the repo root).
    proc = _run_generator(five_mc_tree, out_root, REPO_ROOT, cwd=tmp_path)
    assert proc.returncode != 0, _fail_msg(proc)
    assert "official registry dir" in proc.stdout + proc.stderr
    assert not out_root.exists()

    # Resolves to the custom registry dir (env override makes the pin
    # machine-independent while exercising the real resolution rule).
    custom_dir = tmp_path / "custom-reg"
    custom_dir.mkdir()
    env = {**os.environ,
           "DNALLMMARK_CUSTOM_REGISTRY_DIR": str(custom_dir)}
    proc = _run_generator(five_mc_tree, out_root, custom_dir, cwd=tmp_path,
                          env=env)
    assert proc.returncode != 0, _fail_msg(proc)
    assert "custom registry dir" in proc.stdout + proc.stderr
    assert not out_root.exists()


# ===== Behavior 8: fail-fast refusals (V5) =====


def _variant_tree(tmp_path, tag, train_rows):
    """Build a fabricated tree with custom train rows; dev/test honor the
    declared counts so the refusal isolates the train-side fault."""
    root = tmp_path / f"src-{tag}" / "ds"
    base = root / "datasets" / "iDNA_ABF_datasets" / "5mC"
    _write_split(base, "train", train_rows)
    _write_split(base, "dev", _binary_rows(234))
    _write_split(base, "test", _binary_rows(2344))
    return root


def _assert_refused(proc, out_root, reg_dir, diagnostic):
    """A refused task: non-zero exit, [Skip] line carrying the
    diagnostic, and zero writes anywhere."""
    assert proc.returncode != 0, _fail_msg(proc)
    assert "[Skip]" in proc.stdout, _fail_msg(proc)
    assert diagnostic in proc.stdout, _fail_msg(proc)
    assert not out_root.exists() or not any(out_root.rglob("*")), (
        f"refused task still wrote under {out_root}"
    )
    assert not reg_dir.exists() or not any(reg_dir.rglob("*")), (
        f"refused run still wrote a registry under {reg_dir}"
    )


def test_fail_fast_header_only_split(tmp_path):
    """A header-only (0 data rows) split refuses the task (a 0-row split
    breaks DNADataset)."""
    root = _variant_tree(tmp_path, "empty", [])
    out_root, reg_dir = tmp_path / "out", tmp_path / "reg"
    proc = _run_generator(root, out_root, reg_dir, cwd=tmp_path)
    _assert_refused(proc, out_root, reg_dir, "header-only (0 data rows)")


def test_fail_fast_declared_measured_mismatch(tmp_path):
    """Declared registry Train ≠ measured rows refuses the task with the
    declared-vs-measured diagnostic."""
    root = _variant_tree(tmp_path, "mismatch", _binary_rows(100))
    out_root, reg_dir = tmp_path / "out", tmp_path / "reg"
    proc = _run_generator(root, out_root, reg_dir, cwd=tmp_path)
    _assert_refused(proc, out_root, reg_dir,
                    "declared/measured mismatch")


def test_fail_fast_malformed_row(tmp_path):
    """A row whose field count differs from the header aborts loudly."""
    rows = _binary_rows(2110)
    rows[500] = ("SEQBROKEN", "1", "EXTRA_FIELD")
    root = _variant_tree(tmp_path, "malformed", rows)
    out_root, reg_dir = tmp_path / "out", tmp_path / "reg"
    proc = _run_generator(root, out_root, reg_dir, cwd=tmp_path)
    _assert_refused(proc, out_root, reg_dir, "malformed row")


def test_fail_fast_non_integer_label(tmp_path):
    """Multilabel ``;`` labels (and any non-integer label) abort loudly —
    stratified sampling is single-label-classification-only."""
    rows = _binary_rows(2110)
    rows[7] = ("SEQMULTI", "0;1")
    root = _variant_tree(tmp_path, "multilabel", rows)
    out_root, reg_dir = tmp_path / "out", tmp_path / "reg"
    proc = _run_generator(root, out_root, reg_dir, cwd=tmp_path)
    _assert_refused(proc, out_root, reg_dir, "not an integer")


# ===== Behavior 9: no writes outside the explicit roots =====


def test_no_writes_outside_explicit_roots(five_mc_tree, tmp_path):
    """After a successful run the input tree is unchanged and every new
    path under the sandbox lives under --output-root/--registry-dir (and
    nothing is written to the subprocess cwd)."""
    out_root = tmp_path / "sub"
    reg_dir = tmp_path / "reg"
    input_before = _tree_snapshot(five_mc_tree)
    proc = _run_generator(five_mc_tree, out_root, reg_dir, cwd=tmp_path)
    assert proc.returncode == 0, _fail_msg(proc)
    assert _tree_snapshot(five_mc_tree) == input_before, (
        "generator mutated its input tree"
    )
    for path in tmp_path.rglob("*"):
        relative = path.relative_to(tmp_path)
        assert relative.parts[0] in {"sub", "reg"}, (
            f"generator wrote outside its explicit roots: {path}"
        )


# ===== D15-15 real-artifact checks (15-03, skip-if-artifacts-absent) =====
#
# GPU-outcome assertions over the REAL produced artifacts of the 15-01
# smoke and the 15-03 12-cell subset sweep. The roots are gitignored
# runtime state (D15-12): present on the validation box, absent in CI —
# every check is ``skipif`` on artifact existence so the zero-GPU CI lane
# skips cleanly (D15-15) while the box asserts the real terminal states
# and the measured subset row counts.

SMOKE_ROOTS = (
    REPO_ROOT / "pipeline" / "finetuned-smoke",
    REPO_ROOT / "pipeline" / "finetuned-smoke-r2",
)
SWEEP_ROOT = REPO_ROOT / "pipeline" / "finetuned-sweep"
SUBSET_ROOT = REPO_ROOT / "pipeline" / "datasets-smoke"
SUBSET_REGISTRY = REPO_ROOT / "pipeline" / "registry-smoke" / "datasets_info.json"
# The two sweep tasks' measured subset counts (15-03 Task 1), as
# (task key, official-relative dataset dir, train/dev/test rows) triples.
SUBSET_EXPECT = (
    ("iDNA_ABF_datasets__5mC", "iDNA_ABF_datasets/5mC", (105, 11, 117)),
    ("GUE__emp_H3", "GUE/emp_H3", (598, 74, 74)),
)


@pytest.mark.parametrize(
    "smoke_root", SMOKE_ROOTS,
    ids=["finetuned-smoke", "finetuned-smoke-r2"])
def test_real_smoke_dispatch_terminal_state(smoke_root):
    """The 15-01 smoke root's dispatch_state is terminal ``done`` with
    2/2 completed (both GPUs produced cell artifacts, D15-02)."""
    state_path = smoke_root / "dispatch_state.json"
    if not state_path.is_file():
        pytest.skip(f"smoke runtime root absent (zero-GPU env): {smoke_root}")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["status"] == "done", state["status"]
    counts = state["counts"]
    assert counts["completed"] == counts["total"] == 2, counts
    assert counts["skipped"] == 0, counts


def test_real_sweep_dispatch_terminal_state():
    """The 15-03 12-cell subset sweep's dispatch_state is terminal
    ``done`` with 12/12 completed and ZERO skipped — the adjacency edge:
    the identical cell key ``plant-dnabert-6mer/
    iDNA_ABF_datasets__5mC/seed_42`` exists in BOTH the smoke root (full
    data) and the sweep root (subsets); a shared root would have skipped
    the sweep's cells on the smoke's trainer_state markers."""
    state_path = SWEEP_ROOT / "dispatch_state.json"
    if not state_path.is_file():
        pytest.skip(f"sweep runtime root absent (zero-GPU env): {SWEEP_ROOT}")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["status"] == "done", state["status"]
    counts = state["counts"]
    assert counts["completed"] == counts["total"] == 12, counts
    assert counts["skipped"] == 0, counts


@pytest.mark.parametrize("task_key, rel, splits", SUBSET_EXPECT)
def test_real_subset_rows_match_registry(task_key, rel, splits):
    """The on-disk subset CSV rows equal the pinned measured counts AND
    the subset registry's Train/Dev/Test (declared == measured, the
    T-15-04 discipline over the REAL generated subsets)."""
    base = SUBSET_ROOT / "datasets" / rel
    registry = SUBSET_REGISTRY
    if not base.is_dir() or not registry.is_file():
        pytest.skip(
            "subset runtime roots absent (zero-GPU env): "
            f"{base}, {registry}"
        )
    measured = {}
    for split, expected_n in zip(("train", "dev", "test"), splits):
        with open(base / f"{split}.csv", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))[1:]
        measured[split] = len(rows)
        assert len(rows) == expected_n, (task_key, split, len(rows))
    reg = json.loads(registry.read_text(encoding="utf-8"))
    entry = reg[task_key]
    assert (entry["Train"], entry["Dev"], entry["Test"]) == (
        measured["train"], measured["dev"], measured["test"]
    ), (task_key, entry)
