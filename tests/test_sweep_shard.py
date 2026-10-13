"""
Unit tests for ``pipeline/run_sweep_shard.py`` (12-01, MGPU-01/SC1).

Every behavior bullet of the plan's Tasks 1-2 is pinned here:

- **LPT sharding is a pure function with frozen properties** — the
  partition of requested BASE models over N workers is DISJOINT by
  construction and COVERS the input (each model assigned to exactly one
  worker), DETERMINISTIC (two calls equal), and pins both tie-breaks:
  equal ``size (M)`` sorts registry-name ascending, equal accumulated
  loads pick the LOWEST worker index. A registry entry whose ``size (M)``
  is missing / None / non-numeric shards with weight 0.0 and never
  crashes (the custom-entries reality). ``workers=1`` degenerates to one
  shard covering the input; ``workers == len(models)`` gives each worker
  exactly one model with the LARGEST model on worker 0.
- **The frozen worker-root naming** — ``worker_root(base, i)`` is
  ``{base}-mgpu-w{i}``, a SIBLING of the base root; the tee log
  ``worker_log_path(base, i)`` is the root's ``.log``-suffixed sibling.
  One naming authority: 12-04's --merge imports this same function.
- **Worker argv composition** — every worker is an ordinary
  ``run_sweep.py`` invocation: argv is a LIST of str (never a shell
  string, T-03-10), element 1 ends with run_sweep.py, ``--models``
  carries exactly worker i's shard csv, ``--output-root`` carries the
  frozen ``worker_root(base, i)`` path, unrecognized tokens are forwarded
  VERBATIM as the passthrough tail, and ``--dry-run`` is appended iff
  requested.
- **The spawn discipline is the launcher's VERBATIM (plus one env key)** —
  ``start_new_session=True``, ``cwd`` pinned to ``run_sweep.PIPELINE_DIR``,
  ``env`` a superset of ``os.environ`` with ``PYTHONUNBUFFERED == "1"`` and
  ``CUDA_VISIBLE_DEVICES == str(gpu_i)`` (the worker index under default
  ``--gpus``; the given token per index under ``--gpus "2,5"`` — duplicate
  tokens are operator-owned strings, arity-validated only, and forward
  verbatim without crashing), ``stdout`` the open per-worker sibling-log
  handle, ``stderr=subprocess.STDOUT``.
- **Collect-all fail-fast validation** (the ``_validate_filters``
  discipline) — ``--workers 0``, a malformed ``--gpus`` token, a
  ``--gpus`` arity mismatch, a provided-but-empty ``--models`` value,
  unknown model names vs the registry, and ``--workers`` exceeding the
  requested model count (the empty-shard refusal naming both counts) ALL
  refuse with every problem listed together; a frozen-root collision (a
  worker root equal to the base root or another worker root) refuses the
  same way (T-12-01-01).
- **Aggregated exit honesty (T-12-01-04)** — the orchestrator spawns all
  N, waits ALL N (a dead worker never prevents siblings from being
  waited and reported), exits 0 iff every worker exited 0, and otherwise
  exits 1 after printing a per-worker verdict table (exit code, worker
  root, log path, failed-cell count read from that worker's
  sweep_failures.json when present).
- **The disjointness proof (D-06)** — per-worker dry-run manifests over
  lpt shards have pairwise-disjoint cell identities, a union equal to the
  unsharded dry-run's cells, and each manifest's ``matrix.models`` equals
  its shard; proven in-process AND through a REAL two-worker subprocess
  chain (real Popen, real run_sweep.py children, CPU-only --dry-run —
  the D-05 local shape) whose sibling tee logs exist and are non-empty.

The orchestrator is stdlib-only and CPU-testable: no test assumes N>1
GPUs, launches real training, or probes nvidia-smi (D-05). The real-
subprocess test is the ONLY one that spawns real children, bounded to a
2-model fixture registry x 1 task x 1 seed under --dry-run.

See also:
    ``pipeline/run_sweep_shard.py`` — the orchestrator under test.
    ``tests/test_sweep.py`` — the single-sweep driver contract these
    workers are ordinary invocations of.
"""

import json
import subprocess
import sys

import pytest
import run_sweep  # conftest puts pipeline/ on sys.path
import run_sweep_shard

# ===== machine-independence pin (WR-03 / the test_sweep.py idiom) =====
#
# Worker argv derivation joins the requested --models names against the
# registry_loader view (official + custom overlay), and the lpt weights
# read the same registry — so a maintainer-local custom overlay must not
# leak into these tests. Pin BOTH overlay env vars to a fresh empty dir
# for every test here, exactly as tests/test_sweep.py does.


@pytest.fixture(autouse=True)
def _pin_custom_registry_overlay(tmp_path, monkeypatch):
    """Empty-dir pin over the custom overlay for every test here."""
    pinned = tmp_path / "no-custom-overlay"
    pinned.mkdir()
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(pinned))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(pinned))


# ===== helpers (local copies of the test_sweep.py idioms — the suite
# stays self-contained; run_cli targets run_sweep_shard.main and takes
# the injectable spawner, so a shared import would diverge anyway) =====


def write_registry(root, models, datasets):
    """Materialize unified-registry fixtures under ``root``."""
    (root / "models_info.json").write_text(
        json.dumps(models), encoding="utf-8")
    (root / "datasets_info.json").write_text(
        json.dumps(datasets), encoding="utf-8")


def make_registry(tmp_path):
    """Build a 3-model x 3-task registry fixture (task-y has Train=0).

    The models carry distinct numeric ``size (M)`` values (100/50/10) so
    CLI-driven lpt tests have a pinned expected partition:
    workers=2 shards as [[model-a], [model-b, model-c]].
    """
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    write_registry(
        registry_dir,
        models={
            "model-a": {"Model_name": "model-a", "Model_path": "models/a",
                        "size (M)": 100},
            "model-b": {"Model_name": "model-b", "Model_path": "models/b",
                        "size (M)": 50},
            "model-c": {"Model_name": "model-c", "Model_path": "models/c",
                        "size (M)": 10},
        },
        datasets={
            "task-x": {"Dataset_name": "task-x", "Train": 100, "Dev": 10},
            "task-y": {"Dataset_name": "task-y", "Train": 0, "Dev": 0},
            "task-z": {"Dataset_name": "task-z", "Train": 50, "Dev": 5},
        },
    )
    return registry_dir


def run_cli(monkeypatch, argv, spawner=None):
    """Invoke ``run_sweep_shard.main()`` with a patched argv."""
    full_argv = ["run_sweep_shard.py", *argv]
    monkeypatch.setattr(sys, "argv", full_argv)
    run_sweep_shard.main(spawner=spawner)
    return full_argv


def run_sweep_cli(monkeypatch, argv):
    """Invoke ``run_sweep.main()`` with a patched argv (worker mimic)."""
    full_argv = ["run_sweep.py", *argv]
    monkeypatch.setattr(sys, "argv", full_argv)
    run_sweep.main()
    return full_argv


def flag_value(argv, flag):
    """Return the argv element immediately following ``flag``."""
    assert flag in argv, f"{flag} missing from argv: {argv!r}"
    return argv[argv.index(flag) + 1]


class FakeProc:
    """Minimal Popen stand-in: wait() records the scripted returncode."""

    def __init__(self, returncode=0):
        self.returncode = None
        self._scripted = returncode
        self.waited = False

    def wait(self, timeout=None):
        self.waited = True
        self.returncode = self._scripted
        return self._scripted


def make_fake_spawner(calls, returncodes=None):
    """Build an injectable spawner capturing (argv, kwargs) per call."""

    def spawn(argv, **kwargs):
        calls.append({"argv": list(argv), "kwargs": kwargs})
        index = len(calls) - 1
        code = returncodes[index] if returncodes is not None else 0
        return FakeProc(code)

    return spawn


# ===== lpt_shard: pure-function property tests =====


def test_lpt_partition_is_disjoint_and_covering():
    """Each requested model lands in exactly one worker: the per-worker
    lists are pairwise disjoint and their union is the whole input."""
    models = ["m1", "m2", "m3", "m4", "m5", "m6", "m7"]
    sizes = {"m1": 400, "m2": 8.1, "m3": 86, "m4": 400, "m5": 12,
             "m6": 300, "m7": 1}
    for workers in (2, 3):
        shards = run_sweep_shard.lpt_shard(models, workers, sizes)
        assert len(shards) == workers
        flattened = [name for shard in shards for name in shard]
        assert sorted(flattened) == sorted(models), (
            "union of shards must equal the input model set"
        )
        # disjoint by construction: no model appears twice
        assert len(flattened) == len(set(flattened)), (
            "each model must be assigned to exactly one worker"
        )


def test_lpt_is_deterministic():
    """Two calls over the same inputs return the equal partition."""
    models = ["m1", "m2", "m3", "m4"]
    sizes = {"m1": 10, "m2": 400, "m3": 86, "m4": 400}
    first = run_sweep_shard.lpt_shard(models, 2, sizes)
    second = run_sweep_shard.lpt_shard(models, 2, sizes)
    assert first == second


def test_lpt_tie_breaks_are_pinned():
    """Equal sizes sort registry-name ascending; equal accumulated loads
    pick the lowest worker index."""
    # equal sizes -> assignment order is name ascending, then round-robin
    # over workers with the lowest index winning ties: a->w0, b->w1, c->w0
    equal_sizes = {"a": 10, "b": 10, "c": 10}
    assert run_sweep_shard.lpt_shard(["c", "a", "b"], 2, equal_sizes) == [
        ["a", "c"], ["b"]
    ]
    # equal loads -> lowest worker index: after x->w0, y->w1 the loads are
    # equal again, so z joins worker 0
    assert run_sweep_shard.lpt_shard(
        ["x", "y", "z"], 2, {"x": 10, "y": 10, "z": 10}) == [
        ["x", "z"], ["y"]
    ]


def test_lpt_missing_or_non_numeric_size_weights_zero():
    """A missing / None / non-numeric ``size (M)`` shards with weight 0.0
    and never crashes (the custom-entries reality)."""
    models = ["x", "y", "z"]
    broken = {"x": None, "y": "not-a-number"}
    zeroed = {"x": 0.0, "y": 0.0, "z": 0.0}
    broken_shards = run_sweep_shard.lpt_shard(models, 2, broken)
    zeroed_shards = run_sweep_shard.lpt_shard(models, 2, zeroed)
    assert broken_shards == zeroed_shards, (
        "unusable sizes must behave exactly like explicit 0.0 weights"
    )
    flattened = [name for shard in broken_shards for name in shard]
    assert sorted(flattened) == sorted(models)


def test_lpt_single_worker_degenerate():
    """workers=1 degenerates to one shard covering the whole input."""
    shards = run_sweep_shard.lpt_shard(
        ["b", "a", "c"], 1, {"a": 1, "b": 2, "c": 3})
    assert len(shards) == 1
    assert sorted(shards[0]) == ["a", "b", "c"]


def test_lpt_workers_equal_model_count_one_each():
    """workers == len(models): each worker gets exactly one model, the
    LARGEST lands on worker 0 (LPT assigns the first, biggest item to the
    then-least-loaded worker 0)."""
    shards = run_sweep_shard.lpt_shard(
        ["small", "big", "mid"], 3,
        {"small": 1, "big": 900, "mid": 40})
    assert [shard for shard in shards] == [["big"], ["mid"], ["small"]]


# ===== the frozen naming authority =====


def test_worker_root_and_log_naming_is_frozen(tmp_path):
    """worker_root is the SIBLING {base}-mgpu-w{i} of the base root; the
    tee log is its .log-suffixed sibling. 12-04's --merge imports these
    exact functions — one naming authority."""
    base = tmp_path / "finetuned"
    assert run_sweep_shard.worker_root(base, 0) == \
        tmp_path / "finetuned-mgpu-w0"
    assert run_sweep_shard.worker_root(base, 1) == \
        tmp_path / "finetuned-mgpu-w1"
    assert run_sweep_shard.worker_root(base, 12) == \
        tmp_path / "finetuned-mgpu-w12"
    assert run_sweep_shard.worker_log_path(base, 0) == \
        tmp_path / "finetuned-mgpu-w0.log"
    assert run_sweep_shard.worker_log_path(base, 1) == \
        tmp_path / "finetuned-mgpu-w1.log"


# ===== fake-spawner proofs: argv + the verbatim launch kwargs =====


def test_worker_argv_and_spawn_kwargs_under_default_gpus(
        tmp_path, monkeypatch):
    """Each worker is an ordinary run_sweep.py invocation with the frozen
    shard csv + worker root, verbatim passthrough, --dry-run iff
    requested, and the sweep_launcher._spawn discipline VERBATIM plus the
    one CUDA_VISIBLE_DEVICES env key."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    # the passthrough remainder preserves command-line order verbatim —
    # --registry-dir rides it too (the orchestrator only READS it for
    # its validation join; run_sweep stays its owner)
    passthrough = ["--registry-dir", str(registry_dir),
                   "--tasks", "task-x", "--seeds", "42,43",
                   "--num_train_epochs", "1"]
    calls = []
    monkeypatch.setenv("SHARD_TEST_SENTINEL", "xyz")
    run_cli(monkeypatch, [
        "--workers", "2",
        "--models", "model-a,model-b,model-c",
        "--output-root", str(base),
        "--dry-run",
        *passthrough,
    ], spawner=make_fake_spawner(calls))
    assert len(calls) == 2, "one spawn per worker"
    expected_shards = [["model-a"], ["model-b", "model-c"]]
    for i, call in enumerate(calls):
        argv = call["argv"]
        kwargs = call["kwargs"]
        # argv is a LIST of str, never a shell string (T-03-10)
        assert isinstance(argv, list)
        assert all(isinstance(element, str) for element in argv)
        assert argv[0] == sys.executable
        assert argv[1].endswith("run_sweep.py"), (
            "the launch target is run_sweep.py itself"
        )
        assert flag_value(argv, "--models") == ",".join(expected_shards[i])
        assert flag_value(argv, "--output-root") == str(
            run_sweep_shard.worker_root(base, i))
        # passthrough tokens preserved VERBATIM, in order, in EVERY worker
        start = argv.index(str(run_sweep_shard.worker_root(base, i))) + 1
        assert argv[start:start + len(passthrough)] == passthrough
        # --dry-run present (requested) as the final element
        assert argv[-1] == "--dry-run"
        # the launcher's spawn kwargs, verbatim (plus one env key)
        assert kwargs["start_new_session"] is True
        assert kwargs["cwd"] == str(run_sweep.PIPELINE_DIR)
        assert kwargs["stderr"] == subprocess.STDOUT
        env = kwargs["env"]
        assert env["SHARD_TEST_SENTINEL"] == "xyz", (
            "env is a copy of os.environ (superset)"
        )
        assert env["PYTHONUNBUFFERED"] == "1"
        assert env["CUDA_VISIBLE_DEVICES"] == str(i), (
            "default --gpus assigns the worker index as the GPU id"
        )
        assert kwargs["stdout"].name == str(
            run_sweep_shard.worker_log_path(base, i)), (
            "stdout tees into the per-worker sibling log handle"
        )


def test_dry_run_flag_absent_when_not_requested(tmp_path, monkeypatch):
    """Without --dry-run no worker argv carries the flag."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    calls = []
    run_cli(monkeypatch, [
        "--workers", "2",
        "--models", "model-a,model-b",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
        "--tasks", "task-x", "--seeds", "42",
    ], spawner=make_fake_spawner(calls))
    assert len(calls) == 2
    for call in calls:
        assert "--dry-run" not in call["argv"]


def test_gpus_override_and_duplicate_tokens_forward_verbatim(
        tmp_path, monkeypatch):
    """--gpus "2,5" maps token-per-index into CUDA_VISIBLE_DEVICES;
    duplicate tokens ("0,0") are operator-owned strings — arity-only
    validation, no crash, verbatim forwarding."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()

    calls = []
    run_cli(monkeypatch, [
        "--workers", "2",
        "--gpus", "2,5",
        "--models", "model-a,model-b",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
        "--tasks", "task-x", "--seeds", "42",
    ], spawner=make_fake_spawner(calls))
    assert [c["kwargs"]["env"]["CUDA_VISIBLE_DEVICES"] for c in calls] == \
        ["2", "5"]

    dup_calls = []
    run_cli(monkeypatch, [
        "--workers", "2",
        "--gpus", "0,0",
        "--models", "model-a,model-b",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
        "--tasks", "task-x", "--seeds", "42",
    ], spawner=make_fake_spawner(dup_calls))
    assert len(dup_calls) == 2, "duplicate gpu tokens must not crash"
    assert [c["kwargs"]["env"]["CUDA_VISIBLE_DEVICES"]
            for c in dup_calls] == ["0", "0"]


# ===== collect-all fail-fast validation =====


def test_workers_exceeding_model_count_refuses(tmp_path, monkeypatch):
    """--workers > the filtered model count refuses collect-all, naming
    both counts, before any worker spawns (the empty-shard hazard)."""
    registry_dir = make_registry(tmp_path)
    calls = []
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--workers", "3",
            "--models", "model-a,model-b",
            "--output-root", str(tmp_path / "finetuned"),
            "--registry-dir", str(registry_dir),
            "--tasks", "task-x", "--seeds", "42",
        ], spawner=make_fake_spawner(calls))
    message = str(excinfo.value)
    assert "3" in message and "2" in message, (
        "the refusal must name both the worker count and the model count"
    )
    assert not calls, "validation must refuse BEFORE any spawn"


def test_unknown_model_names_refuse(tmp_path, monkeypatch):
    """A requested model name absent from the registry refuses collect-all
    listing the unknown names."""
    registry_dir = make_registry(tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--workers", "1",
            "--models", "model-a,ghost-model",
            "--output-root", str(tmp_path / "finetuned"),
            "--registry-dir", str(registry_dir),
            "--tasks", "task-x", "--seeds", "42",
        ], spawner=make_fake_spawner([]))
    assert "ghost-model" in str(excinfo.value)


def test_gpus_problems_refuse_collect_all(tmp_path, monkeypatch):
    """A malformed --gpus token and an arity mismatch each refuse with
    every problem listed together."""
    registry_dir = make_registry(tmp_path)
    common = [
        "--models", "model-a,model-b",
        "--output-root", str(tmp_path / "finetuned"),
        "--registry-dir", str(registry_dir),
        "--tasks", "task-x", "--seeds", "42",
    ]
    with pytest.raises(SystemExit) as malformed:
        run_cli(monkeypatch, [
            "--workers", "2", "--gpus", "0,zero", *common,
        ], spawner=make_fake_spawner([]))
    assert "zero" in str(malformed.value)

    with pytest.raises(SystemExit) as arity:
        run_cli(monkeypatch, [
            "--workers", "2", "--gpus", "0,1,2", *common,
        ], spawner=make_fake_spawner([]))
    assert "--gpus" in str(arity.value)


def test_empty_models_value_refuses(tmp_path, monkeypatch):
    """A provided-but-empty --models value refuses instead of degrading
    (the WR-14 discipline)."""
    registry_dir = make_registry(tmp_path)
    with pytest.raises(SystemExit):
        run_cli(monkeypatch, [
            "--workers", "1",
            "--models", ",",
            "--output-root", str(tmp_path / "finetuned"),
            "--registry-dir", str(registry_dir),
            "--tasks", "task-x", "--seeds", "42",
        ], spawner=make_fake_spawner([]))


def test_workers_must_be_at_least_one(tmp_path, monkeypatch):
    """--workers 0 refuses collect-all."""
    registry_dir = make_registry(tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--workers", "0",
            "--models", "model-a",
            "--output-root", str(tmp_path / "finetuned"),
            "--registry-dir", str(registry_dir),
            "--tasks", "task-x", "--seeds", "42",
        ], spawner=make_fake_spawner([]))
    assert "--workers" in str(excinfo.value)
