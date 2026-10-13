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
- **Merge mode (12-04, MGPU-02 artifact half, D-09)** — the union of N
  frozen-named worker roots into ONE verified consumer root: lane-flag
  equality across worker manifests (Pitfall 6 — a lora worker merged
  with a base worker is a different experiment than either), the
  ``output_dir`` prefix-rewrite onto the merged root (Pitfall 5 — worker
  paths dangle after runbook cleanup), the data-artifact allowlist scope
  with the ``--include-checkpoints`` hatch (A2), copy + SHA256-verify
  that refuses on ANY hash mismatch before the merged manifests land,
  consumer equivalence over the REAL ``export_runs.load_run_records``
  walk and the scanner's manifest branch, idempotent re-merge, and
  worker-root immutability.
- **The D-08 isolation re-run (12-05)** — an in-process
  ``run_sweep.main() --from-failures`` over ONE worker's failures
  manifest re-attempts exactly that worker's failed cell (the completed
  sibling seed of the same pair skips via the seed-scoped
  ``trainer_state.json`` marker, so the fake child runs exactly ONCE),
  every write lands under that worker's root, and the healthy worker's
  tree is byte- and mtime-identical after (the fake child writes
  ``final_metrics.json`` + ``trainer_state.json`` — the
  ``tests/test_sweep.py`` monkeypatched-subprocess.run idiom).
- **The N=1 degenerate local smoke (12-05, D-05)** — the REAL spawner
  with ``--workers 1 --gpus 0 --dry-run`` over a two-model fixture
  registry: exactly one frozen ``-mgpu-w0`` root whose manifest covers
  BOTH models, the sibling tee log non-empty, main exit 0 — the
  degenerate-but-valid single-GPU CUDA_VISIBLE_DEVICES=0 chain proven
  on this host; N=2 belongs to the other machine's documented procedure
  (docs/multi-gpu.md), never to an executor or CI run.

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
from datetime import datetime
from pathlib import Path

import export_runs  # conftest puts script/ on sys.path
import pytest
import registry_loader  # conftest puts pipeline/ on sys.path
import run_sweep  # conftest puts pipeline/ on sys.path
import run_sweep_shard

# Repo-root bootstrap (the tests/tui/conftest.py contract, inlined —
# this module lives at tests/ level where the parent conftest provides
# only script/, baseline/, and pipeline/): the consumer-equivalence rows
# import the scanner package-qualified.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tui.services import sweep_monitor

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


def run_cli(monkeypatch, argv, spawner=None, clock=None):
    """Invoke ``run_sweep_shard.main()`` with a patched argv (the
    injectable clock pins deterministic per-launch log stamps — the
    sweep_launcher ``clock`` idiom)."""
    full_argv = ["run_sweep_shard.py", *argv]
    monkeypatch.setattr(sys, "argv", full_argv)
    run_sweep_shard.main(spawner=spawner, clock=clock)
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
    tee log is a PER-LAUNCH timestamped ``.log`` sibling of the worker
    root (WR-02: one file per launch, the launcher's tee idiom — a
    resume relaunch never truncates the prior crash log). 12-04's
    --merge imports worker_root — one naming authority."""
    base = tmp_path / "finetuned"
    assert run_sweep_shard.worker_root(base, 0) == \
        tmp_path / "finetuned-mgpu-w0"
    assert run_sweep_shard.worker_root(base, 1) == \
        tmp_path / "finetuned-mgpu-w1"
    assert run_sweep_shard.worker_root(base, 12) == \
        tmp_path / "finetuned-mgpu-w12"
    assert run_sweep_shard.worker_log_path(base, 0, "20261013_090000") == \
        tmp_path / "finetuned-mgpu-w0-20261013_090000.log"
    assert run_sweep_shard.worker_log_path(base, 1, "20261013_090500") == \
        tmp_path / "finetuned-mgpu-w1-20261013_090500.log"


def test_resume_relaunch_never_truncates_prior_worker_log(
        tmp_path, monkeypatch):
    """WR-02: the documented recovery path (a worker dies; relaunch the
    orchestrator — workers are resume-safe via the trainer_state marker,
    A4/D-08) must not destroy the evidence: the relaunch derives a FRESH
    per-launch tee filename (the sweep_launcher timestamp idiom), so the
    previous launch's crash log survives verbatim instead of being
    opened \"w\" and truncated at the frozen path."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    argv = [
        "--workers", "1",
        "--models", "model-a",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
        "--tasks", "task-x", "--seeds", "42",
    ]
    clocks = iter([datetime(2026, 10, 13, 9, 0, 0),
                   datetime(2026, 10, 13, 9, 5, 0)])
    clock = lambda: next(clocks)  # noqa: E731 — one stamp per launch

    # launch 1: the worker crashes (its tee log is the diagnostic)
    with pytest.raises(SystemExit):
        run_cli(monkeypatch, argv, spawner=make_fake_spawner(
            [], returncodes=[1]), clock=clock)
    first_log = run_sweep_shard.worker_log_path(base, 0, "20261013_090000")
    assert first_log.is_file(), "the crashed launch teed into its log"
    crash_evidence = "CUDA OOM boom — the crash evidence\n"
    first_log.write_text(crash_evidence, encoding="utf-8")

    # the resume relaunch (worker 0 re-runs resume-safe): a NEW log
    run_cli(monkeypatch, argv, spawner=make_fake_spawner(
        [], returncodes=[0]), clock=clock)
    assert first_log.read_text(encoding="utf-8") == crash_evidence, (
        "the relaunch must NOT truncate the prior launch's log"
    )
    second_log = run_sweep_shard.worker_log_path(base, 0, "20261013_090500")
    assert second_log.is_file(), "the relaunch tees into a fresh log"


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
    clock = lambda: datetime(2026, 10, 13, 8, 30, 0)  # noqa: E731
    run_cli(monkeypatch, [
        "--workers", "2",
        "--models", "model-a,model-b,model-c",
        "--output-root", str(base),
        "--dry-run",
        *passthrough,
    ], spawner=make_fake_spawner(calls), clock=clock)
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
            run_sweep_shard.worker_log_path(
                base, i, "20261013_083000")), (
            "stdout tees into the per-launch timestamped sibling log "
            "handle (WR-02 — never the prior launch's frozen path)"
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


def test_gpus_non_numeric_tokens_forward_verbatim(tmp_path, monkeypatch):
    """WR-01: --gpus tokens are OPERATOR-OWNED strings — a GPU UUID or a
    MIG instance id is a legitimate CUDA_VISIBLE_DEVICES value and must
    forward VERBATIM (the documented contract: ARITY-validated only, no
    int coercion, D-05)."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    calls = []
    mig = "MIG-GPU-9f3c2e1b/1/0"
    run_cli(monkeypatch, [
        "--workers", "2",
        "--gpus", f"0,{mig}",
        "--models", "model-a,model-b",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
        "--tasks", "task-x", "--seeds", "42",
    ], spawner=make_fake_spawner(calls))
    assert len(calls) == 2, "non-numeric tokens must not refuse"
    assert [c["kwargs"]["env"]["CUDA_VISIBLE_DEVICES"] for c in calls] == \
        ["0", mig]


def test_gpus_problems_refuse_collect_all(tmp_path, monkeypatch):
    """An empty --gpus element and an arity mismatch each refuse with
    every problem listed together (malformed = an EMPTY element; a
    non-decimal token is a verbatim operator-owned string, WR-01)."""
    registry_dir = make_registry(tmp_path)
    common = [
        "--models", "model-a,model-b",
        "--output-root", str(tmp_path / "finetuned"),
        "--registry-dir", str(registry_dir),
        "--tasks", "task-x", "--seeds", "42",
    ]
    with pytest.raises(SystemExit) as empty_element:
        run_cli(monkeypatch, [
            "--workers", "2", "--gpus", "0,,1", *common,
        ], spawner=make_fake_spawner([]))
    assert "empty GPU id element" in str(empty_element.value)

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


def test_frozen_root_collision_refuses_collect_all(tmp_path, monkeypatch):
    """A worker root that would alias the base root (or another worker
    root) refuses collect-all before any spawn (T-12-01-01: shared roots
    collide last-writer-wins over the root-level manifests — Pitfall 1).
    With the frozen naming function the sibling roots are distinct by
    construction, so the guard is proven by pinning a colliding naming
    function: the point is that the guard is WIRED and fires."""
    registry_dir = make_registry(tmp_path)
    calls = []

    def colliding_worker_root(base_root, index):
        # every worker aliased onto the base root — the forbidden shape
        return base_root

    monkeypatch.setattr(run_sweep_shard, "worker_root",
                        colliding_worker_root)
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--workers", "2",
            "--models", "model-a,model-b",
            "--output-root", str(tmp_path / "finetuned"),
            "--registry-dir", str(registry_dir),
            "--tasks", "task-x", "--seeds", "42",
        ], spawner=make_fake_spawner(calls))
    message = str(excinfo.value)
    assert "equal the base output root" in message
    assert not calls, "the collision must refuse BEFORE any spawn"


# ===== aggregated exit honesty (T-12-01-04) =====


def test_all_zero_workers_exit_zero(tmp_path, monkeypatch, capsys):
    """Every worker exiting 0 means the orchestrator exits 0 (main
    returns normally) after printing the verdict table."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    run_cli(monkeypatch, [
        "--workers", "2",
        "--models", "model-a,model-b",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
        "--tasks", "task-x", "--seeds", "42",
    ], spawner=make_fake_spawner([], returncodes=[0, 0]))
    out = capsys.readouterr().out
    assert "All 2 worker(s) exited 0." in out


def test_nonzero_worker_exits_one_with_verdict_table(
        tmp_path, monkeypatch, capsys):
    """Any nonzero worker exits the orchestrator 1 after the verdict
    table lists EVERY worker (exit code, root, log path, failed-cell
    count from that worker's sweep_failures.json); a dead worker never
    prevents siblings from being waited and reported (death isolation)."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    # worker 0 died after 3 failed cells: its root carries the failures
    # manifest the verdict table must count
    dead_root = run_sweep_shard.worker_root(base, 0)
    dead_root.mkdir(parents=True)
    failures = [
        {"model": "model-a", "task": "task-x", "seed": seed,
         "output_dir": f"{dead_root}/model-a/task-x/seed_{seed}",
         "error": "boom"}
        for seed in (42, 43, 44)
    ]
    (dead_root / "sweep_failures.json").write_text(
        json.dumps(failures), encoding="utf-8")
    calls = []
    clock = lambda: datetime(2026, 10, 13, 8, 30, 0)  # noqa: E731
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--workers", "2",
            "--models", "model-a,model-b",
            "--output-root", str(base),
            "--registry-dir", str(registry_dir),
            "--tasks", "task-x", "--seeds", "42",
        ], spawner=make_fake_spawner(calls, returncodes=[1, 0]),
            clock=clock)
    assert excinfo.value.code == 1
    assert len(calls) == 2
    out = capsys.readouterr().out
    # every worker reported: exit codes, roots, log paths, failed counts
    assert "exit=1" in out and "exit=0" in out
    assert "failed=3" in out, (
        "the dead worker's failed-cell count comes from its "
        "sweep_failures.json"
    )
    assert "failed=-" in out, (
        "the healthy worker has no failures manifest — displayed as '-'"
    )
    for i in (0, 1):
        assert str(run_sweep_shard.worker_root(base, i)) in out
        assert str(run_sweep_shard.worker_log_path(
            base, i, "20261013_083000")) in out, (
            "the verdict table names the log THIS launch teed into"
        )
    assert "1/2 worker(s) failed" in out


def test_dead_worker_does_not_prevent_sibling_wait(
        tmp_path, monkeypatch):
    """Worker 0 exits nonzero FIRST (scripted) — worker 1 is still
    waited: wait-all is unconditional (death isolation)."""
    registry_dir = make_registry(tmp_path)
    procs = []

    def tracking_spawn(argv, **kwargs):
        proc = FakeProc(1 if len(procs) == 0 else 0)
        procs.append(proc)
        return proc

    with pytest.raises(SystemExit):
        run_cli(monkeypatch, [
            "--workers", "2",
            "--models", "model-a,model-b",
            "--output-root", str(tmp_path / "finetuned"),
            "--registry-dir", str(registry_dir),
            "--tasks", "task-x", "--seeds", "42",
        ], spawner=tracking_spawn)
    assert len(procs) == 2
    assert all(proc.waited for proc in procs), (
        "wait-all: the dead worker 0 never prevents worker 1 from being "
        "waited and reported"
    )


# ===== the disjointness proof (D-06) =====


def _manifest_cells(root):
    """Parse a dry-run manifest: (cell identities, matrix models)."""
    manifest = json.loads(
        (root / "sweep_manifest.json").read_text(encoding="utf-8"))
    identities = {
        (cell["model"], cell["task"], cell["seed"])
        for cell in manifest["cells"]
    }
    output_dirs = {cell["output_dir"] for cell in manifest["cells"]}
    return identities, output_dirs, manifest["matrix"]["models"]


def test_dry_run_disjointness_in_process(tmp_path, monkeypatch):
    """Per-worker dry-run manifests over lpt shards: pairwise-disjoint
    cell identities, union == the unsharded dry-run's cells, each
    manifest's matrix.models == its shard (the D-06 static proof)."""
    registry_dir = make_registry(tmp_path)
    sizes = {"model-a": 100, "model-b": 50, "model-c": 10}
    shards = run_sweep_shard.lpt_shard(
        ["model-a", "model-b", "model-c"], 2, sizes)
    assert shards == [["model-a"], ["model-b", "model-c"]]
    base = tmp_path / "finetuned"

    per_worker = []
    for i, shard in enumerate(shards):
        root = run_sweep_shard.worker_root(base, i)
        run_sweep_cli(monkeypatch, [
            "--dry-run",
            "--models", ",".join(shard),
            "--tasks", "task-x,task-z",
            "--seeds", "42,43",
            "--output-root", str(root),
            "--registry-dir", str(registry_dir),
        ])
        per_worker.append(_manifest_cells(root))

    # pairwise disjoint identities AND literally disjoint output dirs
    identities_0, dirs_0, models_0 = per_worker[0]
    identities_1, dirs_1, models_1 = per_worker[1]
    assert not (identities_0 & identities_1)
    assert not (dirs_0 & dirs_1)
    assert models_0 == ["model-a"]
    assert models_1 == ["model-b", "model-c"]

    # union == the unsharded dry-run over the same task/seed axes
    unsharded_root = tmp_path / "finetuned-unsharded"
    run_sweep_cli(monkeypatch, [
        "--dry-run",
        "--models", "model-a,model-b,model-c",
        "--tasks", "task-x,task-z",
        "--seeds", "42,43",
        "--output-root", str(unsharded_root),
        "--registry-dir", str(registry_dir),
    ])
    unsharded = _manifest_cells(unsharded_root)
    assert identities_0 | identities_1 == unsharded[0], (
        "the shards must cover exactly the unsharded matrix"
    )


def test_lpt_partitions_the_official_registry():
    """lpt over the committed official registry's model names partitions
    ALL of them across 2 and 4 workers — disjoint and covering over the
    live 62-model view (env-pinned: official registry only)."""
    models_info = registry_loader.load_models_registry()
    names = sorted(models_info)
    sizes = {
        name: entry.get("size (M)")
        for name, entry in models_info.items()
    }
    assert len(names) >= 4
    for workers in (2, 4):
        shards = run_sweep_shard.lpt_shard(names, workers, sizes)
        assert len(shards) == workers
        assert all(shards), "no empty shard when models >= workers"
        flattened = [name for shard in shards for name in shard]
        assert sorted(flattened) == names
        assert len(flattened) == len(set(flattened))


def test_real_two_worker_dry_run_subprocess_chain(tmp_path, monkeypatch):
    """The REAL spawner end-to-end, CPU-only: two real python subprocesses
    run real run_sweep.py --dry-run over a tmp registry fixture; both
    frozen-root manifests exist with disjoint planned cells, both sibling
    tee logs exist and are non-empty, and main returns 0 (the D-05 local
    shape — never N>1 GPUs, never real training)."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    clock = lambda: datetime(2026, 10, 13, 12, 0, 0)  # noqa: E731
    run_cli(monkeypatch, [
        "--workers", "2",
        "--models", "model-a,model-b",
        "--tasks", "task-x",
        "--seeds", "42",
        "--dry-run",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], clock=clock)  # real spawner: main(spawner=None) -> subprocess.Popen

    identities = {}
    for i, expected_models in ((0, ["model-a"]), (1, ["model-b"])):
        root = run_sweep_shard.worker_root(base, i)
        manifest_path = root / "sweep_manifest.json"
        assert manifest_path.is_file(), (
            f"worker {i} must have written its frozen-root manifest"
        )
        worker_identities, _worker_dirs, matrix_models = \
            _manifest_cells(root)
        assert matrix_models == expected_models
        assert all(cell[1] == "task-x" and cell[2] == 42
                   for cell in worker_identities)
        identities[i] = worker_identities
        log = run_sweep_shard.worker_log_path(base, i, "20261013_120000")
        assert log.is_file(), f"worker {i} tee log must exist"
        assert log.read_text(encoding="utf-8").strip(), (
            f"worker {i} tee log must capture the child's output"
        )
    assert not (identities[0] & identities[1]), (
        "the two real workers planned disjoint cells"
    )


# ===== merge mode (12-04, MGPU-02 artifact half, D-09) =====


def write_manifest(root, cells, models, tasks, seeds):
    """Write a ``sweep_manifest.json`` fixture in the exact
    ``run_sweep._manifest_payload`` shape (matrix dict + cells list)."""
    payload = {
        "matrix": {
            "models": sorted(models),
            "tasks": sorted(tasks),
            "seeds": sorted(seeds),
            "output_root": str(root),
        },
        "cells": cells,
    }
    (root / run_sweep.MANIFEST_NAME).write_text(
        json.dumps(payload), encoding="utf-8")


def make_manifest_cell(worker, model, task, seed, status="completed",
                       fraction=None, **lane):
    """One manifest cell fixture: the five identity keys (the
    ``_manifest_payload`` projection) plus optional lane keys."""
    return {
        "model": model,
        "task": task,
        "seed": seed,
        "status": status,
        "output_dir": str(
            run_sweep.cell_dir_for(worker, model, task, seed, fraction)),
        **lane,
    }


def make_lane_pair(tmp_path, name, lane_a, lane_b):
    """Two frozen-named worker roots whose manifests differ ONLY in the
    given lane keys (no cell trees — the lane-equality refusal fires at
    validation, before any copy)."""
    base = (tmp_path / name).resolve()
    roots = []
    for index, lane in enumerate((lane_a, lane_b)):
        root = run_sweep_shard.worker_root(base, index)
        root.mkdir(parents=True)
        write_manifest(
            root,
            cells=[make_manifest_cell(root, f"model-{index}", "task-x",
                                      42, **lane)],
            models=[f"model-{index}"], tasks=["task-x"], seeds=[42])
        roots.append(root)
    return base, roots


def test_merge_refuses_unequal_peft_lane(tmp_path, monkeypatch):
    """A peft lane difference across worker manifests refuses collect-all
    listing the flag and BOTH roots, before any merged manifest lands
    (Pitfall 6: merging a lora worker with a base worker produces a
    manifest lying about half its cells)."""
    base, roots = make_lane_pair(
        tmp_path, "finetuned", {"peft": "lora"}, {"peft": "none"})
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--merge", "--workers", "2", "--output-root", str(base),
        ])
    message = str(excinfo.value)
    assert "peft" in message
    for root in roots:
        assert str(root) in message, (
            "the diagnostic must list the differing value per root"
        )
    assert not (base / run_sweep.MANIFEST_NAME).exists(), (
        "the refusal must land BEFORE any merged manifest is written"
    )


def test_merge_refuses_unequal_num_train_epochs_lane(
        tmp_path, monkeypatch):
    """A num_train_epochs lane difference refuses the same collect-all
    way (the second pinned lane axis)."""
    base, roots = make_lane_pair(
        tmp_path, "finetuned",
        {"num_train_epochs": 3}, {"num_train_epochs": 1})
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--merge", "--workers", "2", "--output-root", str(base),
        ])
    message = str(excinfo.value)
    assert "num_train_epochs" in message
    for root in roots:
        assert str(root) in message


def test_rewrite_output_dir_swaps_worker_prefix_to_merged():
    """The prefix swap: a worker-rooted output_dir rewrites onto the
    merged root, preserving the {model}/{task}/seed_{n} suffix verbatim
    (Pitfall 5 — leaving worker paths dangles them after runbook
    cleanup)."""
    worker = Path("/tmp/base-mgpu-w0")
    merged = Path("/tmp/base")
    assert run_sweep_shard._rewrite_output_dir(
        "/tmp/base-mgpu-w0/model-a/task-x/seed_42", worker,
        merged) == "/tmp/base/model-a/task-x/seed_42"


def test_rewrite_output_dir_preserves_frac_child_suffix():
    """A curve cell's frac child keeps its full suffix verbatim (curve
    manifest cells point INTO the frac dir)."""
    worker = Path("/tmp/base-mgpu-w1")
    merged = Path("/tmp/base")
    assert run_sweep_shard._rewrite_output_dir(
        "/tmp/base-mgpu-w1/model-b/task-x/seed_42/frac_0.5", worker,
        merged) == "/tmp/base/model-b/task-x/seed_42/frac_0.5"


def test_rewrite_output_dir_non_matching_prefix_passes_through():
    """Defensive negative: a path NOT under the worker root passes
    through UNCHANGED (validation owns refusing it — the swap never
    invents a match)."""
    worker = Path("/tmp/base-mgpu-w0")
    merged = Path("/tmp/base")
    outside = "/somewhere/else/model-a/task-x/seed_42"
    assert run_sweep_shard._rewrite_output_dir(
        outside, worker, merged) == outside


def test_rewrite_output_dir_sibling_worker_prefix_guard():
    """The boundary guard: w0's root is a raw string PREFIX of w1's
    (``...-mgpu-w0`` vs ``...-mgpu-w01``) — the swap must NOT fire across
    the sibling boundary."""
    worker = Path("/tmp/base-mgpu-w0")
    merged = Path("/tmp/base")
    sibling = "/tmp/base-mgpu-w01/model-a/task-x/seed_42"
    assert run_sweep_shard._rewrite_output_dir(
        sibling, worker, merged) == sibling


# ----- the two-worker fixture pair (Task 2's behavior rows) -----


def _write_cell_artifacts(cell_dir, model, task, seed, flops=True):
    """Materialize a cell dir's allowlisted artifacts with realistic
    minimal payloads (run_record / seed_result valid for the exporter
    walk; flops optional — a missing allowlisted file is skipped and
    counted, never an error)."""
    cell_dir.mkdir(parents=True, exist_ok=True)
    contents = {
        "run_record.json": {
            "model": model, "task": task, "seed": seed,
            "status": "completed", "peft": "none",
            "config_variant": "none", "train_fraction": None,
            "output_dir": str(cell_dir), "metrics": {"total_flos": 1.0},
            "git_commit": "test", "started_at": None,
            "finished_at": None, "error": None,
        },
        "final_metrics.json": {"eval_loss": 0.5, "eval_accuracy": 0.9},
        "trainer_state.json": {"global_step": 10, "log_history": []},
        "seed_result.json": {
            "model_name": model, "task_name": task, "seed": seed,
            "timestamp": "2026-10-13T00:00:00Z",
            "metrics": {"seed_suite_metric": 0.5},
        },
    }
    if flops:
        contents["flops_report.json"] = {
            "schema_version": 1, "total_flops_exact": 123456.0,
            "layer_details": {},
        }
    for name, payload in contents.items():
        (cell_dir / name).write_text(
            json.dumps(payload), encoding="utf-8")


def make_worker_pair(tmp_path, name="finetuned"):
    """Build the two-worker fixture tree pair.

    Worker 0 (model-a): a curve-shaped cell (seed_42 with a frac_0.5
    child, both carrying the full allowlist), a plain cell (seed_43)
    whose dir also carries the stray checkpoint-500/ + runs/ dirs, and a
    planned-but-never-run cell (task-y, dir absent); one failure entry.
    Worker 1 (model-b): two plain cells (four allowlisted files each —
    no flops_report.json, pinning the missing-file skip); no failures.
    """
    base = (tmp_path / name).resolve()
    w0 = run_sweep_shard.worker_root(base, 0)
    w1 = run_sweep_shard.worker_root(base, 1)

    _write_cell_artifacts(
        w0 / "model-a" / "task-x" / "seed_42", "model-a", "task-x", 42)
    _write_cell_artifacts(
        w0 / "model-a" / "task-x" / "seed_42" / "frac_0.5",
        "model-a", "task-x", 42)
    seed_43 = w0 / "model-a" / "task-x" / "seed_43"
    _write_cell_artifacts(seed_43, "model-a", "task-x", 43)
    (seed_43 / "checkpoint-500").mkdir()
    (seed_43 / "checkpoint-500" / "optimizer.pt").write_text(
        "ckpt", encoding="utf-8")
    (seed_43 / "runs").mkdir()
    (seed_43 / "runs" / "events.out.tfevents").write_text(
        "tb", encoding="utf-8")
    write_manifest(
        w0,
        cells=[
            make_manifest_cell(w0, "model-a", "task-x", 42),
            make_manifest_cell(w0, "model-a", "task-x", 43),
            make_manifest_cell(w0, "model-a", "task-y", 42,
                               status="planned"),
        ],
        models=["model-a"], tasks=["task-x", "task-y"], seeds=[42, 43])
    (w0 / run_sweep.FAILURES_NAME).write_text(
        json.dumps([
            {"model": "model-a", "task": "task-y", "seed": 42,
             "output_dir": str(w0 / "model-a" / "task-y" / "seed_42"),
             "error": "boom"},
        ]), encoding="utf-8")

    _write_cell_artifacts(
        w1 / "model-b" / "task-x" / "seed_42", "model-b", "task-x", 42,
        flops=False)
    _write_cell_artifacts(
        w1 / "model-b" / "task-x" / "seed_43", "model-b", "task-x", 43,
        flops=False)
    write_manifest(
        w1,
        cells=[
            make_manifest_cell(w1, "model-b", "task-x", 42),
            make_manifest_cell(w1, "model-b", "task-x", 43),
        ],
        models=["model-b"], tasks=["task-x"], seeds=[42, 43])
    (w1 / run_sweep.FAILURES_NAME).write_text("[]", encoding="utf-8")
    return base, [w0, w1]


def _snapshot_tree(root):
    """Snapshot every file under root: path -> (bytes, mtime_ns)."""
    snapshot = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            snapshot[path] = (
                path.read_bytes(), path.stat().st_mtime_ns)
    return snapshot


def _worker_allowlisted_files(worker_root):
    """Every allowlisted source file under a worker root (fixture truth
    for the merged-copy assertions)."""
    return sorted(
        path for path in worker_root.rglob("*")
        if path.is_file() and path.name in run_sweep_shard.MERGE_ALLOWLIST)


def run_merge_cli(monkeypatch, base, workers=2, extra=None):
    """Invoke the merge mode over a fixture base root."""
    argv = ["--merge", "--workers", str(workers),
            "--output-root", str(base)]
    run_cli(monkeypatch, [*argv, *(extra or [])])


def test_merge_happy_path_copies_allowlist_and_rewrites(
        tmp_path, monkeypatch, capsys):
    """The happy path: every allowlisted source file lands at its exact
    relative path under the merged root byte-identical; checkpoint-*/
    and runs/ are ABSENT by default; the never-run cell contributes its
    rewritten manifest entry but no files (counted in the console);
    every merged cell's output_dir sits under the merged root with the
    {model}/{task}/seed_{n} suffix verbatim; matrix and failures union
    correctly; the console reports per-worker counts + the union
    count."""
    base, roots = make_worker_pair(tmp_path)
    run_merge_cli(monkeypatch, base)

    # 1. every allowlisted source file copied byte-identical to the same
    #    relative path under the merged root
    for worker in roots:
        for src in _worker_allowlisted_files(worker):
            rel = src.relative_to(worker)
            dst = base / rel
            assert dst.is_file(), f"missing merged copy: {dst}"
            assert dst.read_bytes() == src.read_bytes(), (
                f"merged copy differs from source: {dst}"
            )
        # 2. checkpoint-*/ and runs/ ABSENT by default (A2 scope pin)
        for stray in worker.rglob("checkpoint-*"):
            assert not (base / stray.relative_to(worker)).exists()
        for stray in worker.rglob("runs"):
            assert not (base / stray.relative_to(worker)).exists()

    # 3. the never-run cell contributed NO files
    assert not (base / "model-a" / "task-y").exists()

    # 4. the merged manifest: union of cells, every output_dir rewritten
    manifest = json.loads(
        (base / run_sweep.MANIFEST_NAME).read_text(encoding="utf-8"))
    assert len(manifest["cells"]) == 5, "3 (w0) + 2 (w1) union cells"
    for cell in manifest["cells"]:
        assert cell["output_dir"] == str(
            base / cell["model"] / cell["task"] / f"seed_{cell['seed']}"
        ), ("every merged output_dir must sit under the merged root with "
            "the {model}/{task}/seed_{n} suffix verbatim (Pitfall 5)")
    assert manifest["matrix"] == {
        "models": ["model-a", "model-b"],
        "tasks": ["task-x", "task-y"],
        "seeds": [42, 43],
        "output_root": str(base),
    }

    # 5. failures union with the same rewrite
    failures = json.loads(
        (base / run_sweep.FAILURES_NAME).read_text(encoding="utf-8"))
    assert failures == [
        {"model": "model-a", "task": "task-y", "seed": 42,
         "output_dir": str(base / "model-a" / "task-y" / "seed_42"),
         "error": "boom"},
    ]

    # 6. console honesty: per-worker copied counts + union count
    out = capsys.readouterr().out
    assert "[Merge] worker 0: 15 file(s)" in out, (
        "w0 = seed_42(5) + frac_0.5(5) + seed_43(5); strays excluded"
    )
    assert "[Merge] worker 1: 8 file(s)" in out, (
        "w1 = two plain cells x 4 files (flops_report absent = skipped)"
    )
    assert "1 cell(s) with no files on disk" in out, (
        "the never-run cell is counted, not silently dropped"
    )
    assert "5 cell(s)" in out and "1 failure entry(ies)" in out


def test_merge_include_checkpoints_hatch_copies_strays(
        tmp_path, monkeypatch):
    """--include-checkpoints: the checkpoint-*/ and runs/ trees copy
    verbatim (verified like everything else)."""
    base, _roots = make_worker_pair(tmp_path)
    run_merge_cli(monkeypatch, base, extra=["--include-checkpoints"])
    merged_seed_43 = base / "model-a" / "task-x" / "seed_43"
    assert (merged_seed_43 / "checkpoint-500" / "optimizer.pt"
            ).read_text(encoding="utf-8") == "ckpt"
    assert (merged_seed_43 / "runs" / "events.out.tfevents"
            ).read_text(encoding="utf-8") == "tb"


def test_copy_verified_unit_happy(tmp_path):
    """_copy_verified: a clean copy returns True and the destination
    bytes equal the source's."""
    src = tmp_path / "src.json"
    src.write_text('{"a": 1}', encoding="utf-8")
    dst = tmp_path / "nested" / "dst.json"
    assert run_sweep_shard._copy_verified(src, dst) is True
    assert dst.read_text(encoding="utf-8") == '{"a": 1}'


def test_copy_verified_unit_detects_corruption(tmp_path, monkeypatch):
    """_copy_verified returns False when the destination bytes differ
    from the source's after the copy step — simulated by pre-writing a
    tampered destination and neutering the copy (it never repairs
    silently)."""
    src = tmp_path / "src.json"
    src.write_text('{"a": 1}', encoding="utf-8")
    dst = tmp_path / "dst.json"
    dst.write_text('{"tampered": true}', encoding="utf-8")

    def no_op_copyfile(src_path, dst_path):
        pass  # the copy "succeeds" but lands nothing — dst stays tampered

    monkeypatch.setattr(
        run_sweep_shard.shutil, "copyfile", no_op_copyfile)
    assert run_sweep_shard._copy_verified(src, dst) is False, (
        "a destination whose post-copy bytes differ from the source must "
        "refuse (D-09 verification)"
    )


def test_copy_verified_unit_oserror_converts_to_refusal(
        tmp_path, monkeypatch):
    """WR-04: an OSError raised by the copy step (ENOSPC / EACCES / a
    read-only destination) converts to the designed refusal path —
    False — never a raw traceback out of the verify pass."""
    src = tmp_path / "src.json"
    src.write_text('{"a": 1}', encoding="utf-8")

    def raising_copyfile(src_path, dst_path):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(
        run_sweep_shard.shutil, "copyfile", raising_copyfile)
    assert run_sweep_shard._copy_verified(
        src, tmp_path / "nested" / "dst.json") is False, (
        "an OSError from the copy must land in the mismatch-refusal "
        "path, not propagate as a traceback"
    )


def test_merge_refuses_with_designed_diagnostic_on_copy_oserror(
        tmp_path, monkeypatch):
    """WR-04 merge level: a copy step that raises OSError refuses with
    the designed collect-all diagnostic (not a stack trace) and the
    merged manifests are NOT written."""
    base, _roots = make_worker_pair(tmp_path)

    def oserror_copyfile(src_path, dst_path):
        raise OSError(13, "Permission denied")

    monkeypatch.setattr(
        run_sweep_shard.shutil, "copyfile", oserror_copyfile)
    with pytest.raises(SystemExit) as excinfo:
        run_merge_cli(monkeypatch, base)
    message = str(excinfo.value)
    assert "merge refused" in message, (
        "the operator must get the designed merge-refusal diagnostic, "
        "not an OSError traceback"
    )
    assert not (base / run_sweep.MANIFEST_NAME).exists(), (
        "the merged manifest must never land on a failed copy"
    )
    assert not (base / run_sweep.FAILURES_NAME).exists()


def test_merge_refuses_on_hash_mismatch_without_manifests(
        tmp_path, monkeypatch):
    """Merge level: a monkeypatched copy that corrupts every file makes
    main refuse, and the merged manifests are NOT written (a partial
    corrupt merge never lands)."""
    base, _roots = make_worker_pair(tmp_path)

    def corrupting_copyfile(src_path, dst_path):
        Path(dst_path).write_text("corrupted-by-fake", encoding="utf-8")

    monkeypatch.setattr(
        run_sweep_shard.shutil, "copyfile", corrupting_copyfile)
    with pytest.raises(SystemExit) as excinfo:
        run_merge_cli(monkeypatch, base)
    assert "SHA256 mismatch" in str(excinfo.value)
    assert not (base / run_sweep.MANIFEST_NAME).exists(), (
        "the merged manifest must never land on a corrupt copy"
    )
    assert not (base / run_sweep.FAILURES_NAME).exists()


def test_merge_refuses_missing_worker_root(tmp_path, monkeypatch):
    """A worker root that does not exist refuses collect-all naming it."""
    base, roots = make_worker_pair(tmp_path)
    import shutil as shutil_module
    shutil_module.rmtree(roots[1])
    with pytest.raises(SystemExit) as excinfo:
        run_merge_cli(monkeypatch, base)
    assert str(roots[1]) in str(excinfo.value)


def test_merge_refuses_worker_root_without_manifest(
        tmp_path, monkeypatch):
    """A worker root present on disk but without its sweep_manifest.json
    refuses collect-all naming it (an incomplete merge never lands)."""
    base, roots = make_worker_pair(tmp_path)
    (roots[1] / run_sweep.MANIFEST_NAME).unlink()
    with pytest.raises(SystemExit) as excinfo:
        run_merge_cli(monkeypatch, base)
    assert str(roots[1]) in str(excinfo.value)


def test_merge_refuses_stray_passthrough(tmp_path, monkeypatch):
    """--merge with stray passthrough tokens refuses (merge takes no
    sweep flags)."""
    base, _roots = make_worker_pair(tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        run_merge_cli(monkeypatch, base, extra=["--seeds", "42"])
    assert "--seeds" in str(excinfo.value)


def test_merged_root_is_consumer_equivalent(tmp_path, monkeypatch):
    """The D-09 acceptance: export_runs.load_run_records over the merged
    root returns EXACTLY the union of the per-worker record sets (the
    walk keys on model names x seed_(\\d+) dirs, both preserved verbatim
    by the copy), and sweep_monitor.full_scan classifies the merged root
    through the manifest branch — state finished with full counts."""
    base, roots = make_worker_pair(tmp_path)
    run_merge_cli(monkeypatch, base)

    def key_set(root):
        tree = export_runs.load_run_records(root)
        return {
            (model, task, seed)
            for model, tasks in tree.items()
            for task, seeds in tasks.items()
            for seed in seeds
        }

    union = key_set(roots[0]) | key_set(roots[1])
    assert union, "the fixture must carry worker records"
    assert key_set(base) == union, (
        "the merged root must read as exactly the union of the worker "
        "roots through the REAL exporter walk"
    )

    scan = sweep_monitor.full_scan(roots=[base])
    assert len(scan.sweeps) == 1
    summary = scan.sweeps[0]
    assert summary.state == sweep_monitor.SWEEP_FINISHED, (
        "the merged manifest puts the root in the scanner's "
        "first-match manifest branch"
    )
    assert summary.total == 5
    assert summary.done == 4, "4 completed + 1 planned (planned never counts)"


def test_merge_is_idempotent_byte_stable(tmp_path, monkeypatch):
    """Re-running --merge over unchanged workers rewrites byte-identical
    merged manifests (the deterministic JSON discipline) with overwrite
    semantics — no spurious copy failures."""
    base, _roots = make_worker_pair(tmp_path)
    run_merge_cli(monkeypatch, base)
    first_manifest = (base / run_sweep.MANIFEST_NAME).read_bytes()
    first_failures = (base / run_sweep.FAILURES_NAME).read_bytes()
    run_merge_cli(monkeypatch, base)  # second merge over the same tree
    assert (base / run_sweep.MANIFEST_NAME).read_bytes() == first_manifest
    assert (base / run_sweep.FAILURES_NAME).read_bytes() == first_failures


def test_remerge_with_changed_worker_set_refuses_on_stale_cells(
        tmp_path, monkeypatch):
    """WR-03: re-merging over a previously-merged root after the worker
    set CHANGED must refuse naming the stale cell files. The merge never
    deletes and _copy_verified only overwrites what it copies, so the
    previous merge's cells stay on disk while the new manifest claims
    they are absent — and export_runs walks the FILE TREE, so the stale
    cells would silently leak into the exported leaderboard numbers."""
    import shutil as shutil_module

    base, roots = make_worker_pair(tmp_path)
    run_merge_cli(monkeypatch, base)  # first merge: model-a + model-b
    manifest_before = (base / run_sweep.MANIFEST_NAME).read_bytes()

    # the changed worker set: worker 1 re-planned WITHOUT its seed_43
    # cell (files + manifest cell gone — the reachable relaunch shape)
    shutil_module.rmtree(roots[1] / "model-b" / "task-x" / "seed_43")
    write_manifest(
        roots[1],
        cells=[make_manifest_cell(roots[1], "model-b", "task-x", 42)],
        models=["model-b"], tasks=["task-x"], seeds=[42])

    with pytest.raises(SystemExit) as excinfo:
        run_merge_cli(monkeypatch, base)
    message = str(excinfo.value)
    assert "model-b/task-x/seed_43" in message, (
        "the refusal must name the stale cell files the new merge does "
        "not cover"
    )
    assert "merge refused" in message
    # the first merge's manifests stand unchanged (refusal landed first)
    assert (base / run_sweep.MANIFEST_NAME).read_bytes() == manifest_before


def test_remerge_unchanged_worker_set_stays_idempotent_under_stale_guard(
        tmp_path, monkeypatch):
    """WR-03 positive control: the stale-file guard does not fire for an
    UNCHANGED worker set — every pre-existing allowlisted file under the
    merged root IS in the copy plan, so the idempotent re-merge passes
    (the byte-stable contract keeps holding)."""
    base, _roots = make_worker_pair(tmp_path)
    run_merge_cli(monkeypatch, base)
    run_merge_cli(monkeypatch, base)  # identical worker set: no refusal
    manifest = json.loads(
        (base / run_sweep.MANIFEST_NAME).read_text(encoding="utf-8"))
    assert len(manifest["cells"]) == 5


def test_merge_leaves_worker_roots_immutable(tmp_path, monkeypatch):
    """After merge, every worker file's bytes AND mtime are unchanged
    (copy-only semantics — workers stay re-runnable in isolation, D-08;
    the merge never mutates a worker root)."""
    base, roots = make_worker_pair(tmp_path)
    before = {root: _snapshot_tree(root) for root in roots}
    run_merge_cli(monkeypatch, base)
    run_merge_cli(monkeypatch, base, extra=["--include-checkpoints"])
    for root in roots:
        assert _snapshot_tree(root) == before[root], (
            f"worker root {root} must be byte- and mtime-identical after "
            "one default merge and one checkpoints-hatch merge"
        )


# ===== the D-08 isolation re-run (12-05, MGPU-02/SC2 — zero new code) =====


def make_isolation_pair(tmp_path, name="finetuned"):
    """Two worker trees for the D-08 isolation re-run.

    Worker 0 (model-a): ONE completed cell (seed_42 — full artifacts
    incl. the ``trainer_state.json`` resume marker) and ONE failed cell
    (seed_43, never run — its dir does not exist) listed in w0's
    ``sweep_failures.json``; both seeds belong to the SAME (model, task)
    pair, so the from-failures re-enumeration covers both and only the
    marker can save the completed one. Worker 1 (model-b): fully
    completed, clean failures manifest — the healthy sibling whose root
    the re-run must never touch.
    """
    base = (tmp_path / name).resolve()
    w0 = run_sweep_shard.worker_root(base, 0)
    w1 = run_sweep_shard.worker_root(base, 1)

    _write_cell_artifacts(
        w0 / "model-a" / "task-x" / "seed_42", "model-a", "task-x", 42)
    write_manifest(
        w0,
        cells=[
            make_manifest_cell(w0, "model-a", "task-x", 42),
            make_manifest_cell(w0, "model-a", "task-x", 43,
                               status="failed"),
        ],
        models=["model-a"], tasks=["task-x"], seeds=[42, 43])
    (w0 / run_sweep.FAILURES_NAME).write_text(
        json.dumps([
            {"model": "model-a", "task": "task-x", "seed": 43,
             "output_dir": str(w0 / "model-a" / "task-x" / "seed_43"),
             "error": "boom"},
        ]), encoding="utf-8")

    _write_cell_artifacts(
        w1 / "model-b" / "task-x" / "seed_42", "model-b", "task-x", 42)
    write_manifest(
        w1,
        cells=[make_manifest_cell(w1, "model-b", "task-x", 42)],
        models=["model-b"], tasks=["task-x"], seeds=[42])
    (w1 / run_sweep.FAILURES_NAME).write_text("[]", encoding="utf-8")
    return base, w0, w1


def test_d08_from_failures_rerun_is_isolated_to_w0(tmp_path, monkeypatch):
    """D-08 (SC2): an in-process ``run_sweep.main() --from-failures``
    over w0's failures manifest re-attempts EXACTLY w0's failed cell
    (the completed seed-42 cell of the same pair is skipped via the
    seed-scoped ``trainer_state.json`` marker — the fake child executes
    exactly ONCE), every write lands under w0's root, and everything
    else in the tree — w1's artifacts and manifests included — is
    byte- and mtime-identical after (a failed worker's recovery never
    touches a healthy worker; the runbook's one-line re-run, D-08)."""
    registry_dir = make_registry(tmp_path)
    _base, w0, _w1 = make_isolation_pair(tmp_path)

    def snapshot_outside_w0():
        """Every file in the tree EXCEPT the w0 subtree: (bytes, mtime)."""
        return {
            path: (path.read_bytes(), path.stat().st_mtime_ns)
            for path in sorted(tmp_path.rglob("*"))
            if path.is_file() and w0 not in path.parents
        }

    before = snapshot_outside_w0()
    launched = []

    def fake_child(argv, **kwargs):
        # the tests/test_sweep.py monkeypatched-subprocess.run idiom:
        # _git_commit() also rides subprocess.run — give it a stdout
        if argv[:1] == ["git"]:
            return subprocess.CompletedProcess(
                argv, returncode=0, stdout="fakehash\n")
        launched.append(list(argv))
        # mimic run_finetune.py's success artifacts: the child receives
        # the worker ROOT as --output_dir and derives the cell dir the
        # same way the real child does (the fake-executor idiom)
        cell_dir = (
            Path(flag_value(argv, "--output_dir"))
            / flag_value(argv, "--target_model")
            / flag_value(argv, "--target_dataset")
            / f"seed_{flag_value(argv, '--seed')}")
        cell_dir.mkdir(parents=True, exist_ok=True)
        (cell_dir / "final_metrics.json").write_text(
            json.dumps({"eval_loss": 0.5, "eval_accuracy": 0.9}),
            encoding="utf-8")
        (cell_dir / "trainer_state.json").write_text(
            '{"global_step": 1}', encoding="utf-8")
        return subprocess.CompletedProcess(argv, returncode=0)

    monkeypatch.setattr(run_sweep.subprocess, "run", fake_child)
    run_sweep_cli(monkeypatch, [
        "--from-failures", str(w0 / run_sweep.FAILURES_NAME),
        "--output-root", str(w0),
        "--registry-dir", str(registry_dir),
        "--seeds", "42,43",
        "--num_train_epochs", "1",
    ])  # main() returns normally — the re-run exits 0

    # exactly ONE child: the failed cell only — the completed cell was
    # skipped by the seed-scoped marker, never re-attempted
    assert len(launched) == 1, (
        "the from-failures re-run must execute exactly the failed cell; "
        "the marker-skipped sibling never invokes the executor"
    )
    assert flag_value(launched[0], "--target_model") == "model-a"
    assert flag_value(launched[0], "--target_dataset") == "task-x"
    assert flag_value(launched[0], "--seed") == "43"
    assert flag_value(launched[0], "--output_dir") == str(w0), (
        "the re-run child receives w0's own root as its output root"
    )

    # nothing outside w0 changed — w1's tree is snapshot-identical
    assert snapshot_outside_w0() == before, (
        "the isolation re-run must write NOTHING outside w0's root — "
        "the healthy worker's files keep their bytes AND mtimes (D-08)"
    )

    # the re-run's own manifest records this run's view: the completed
    # cell skipped (marker), the failed cell now completed
    manifest = json.loads(
        (w0 / run_sweep.MANIFEST_NAME).read_text(encoding="utf-8"))
    statuses = {cell["seed"]: cell["status"] for cell in manifest["cells"]}
    assert statuses == {42: "skipped", 43: "completed"}, (
        "the manifest reflects THIS run's view while the per-cell record "
        "keeps the original run's — the two artifacts answer different "
        "questions (WR-12)"
    )
    rerun_failures = json.loads(
        (w0 / run_sweep.FAILURES_NAME).read_text(encoding="utf-8"))
    assert rerun_failures == [], "the recovered cell leaves no failure"


# ===== the N=1 degenerate local smoke (12-05, D-05 — GB10-legal) =====


def test_n1_degenerate_real_subprocess_smoke(tmp_path, monkeypatch):
    """D-05 local semantics proof (12-05): the REAL spawner with
    ``--workers 1 --gpus 0 --dry-run`` over a two-model fixture registry
    spawns one real run_sweep child, writes the ONE frozen ``-mgpu-w0``
    root manifest covering BOTH models, tees the sibling log, and main
    exits 0. This host (GB10) has exactly ONE GPU — index 0 — so this
    is the degenerate-but-valid CUDA_VISIBLE_DEVICES=0 chain, executed
    here and only here; N=2 is the OTHER machine's documented procedure
    (docs/multi-gpu.md §"The 9-step N=2 multi-GPU smoke procedure"),
    never an executor or CI run (D-05)."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    clock = lambda: datetime(2026, 10, 13, 12, 0, 0)  # noqa: E731
    run_cli(monkeypatch, [
        "--workers", "1",
        "--gpus", "0",
        "--models", "model-a,model-b",
        "--tasks", "task-x",
        "--seeds", "42",
        "--dry-run",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], clock=clock)  # real spawner: main(spawner=None) -> subprocess.Popen

    w0 = run_sweep_shard.worker_root(base, 0)
    assert (w0 / "sweep_manifest.json").is_file(), (
        "the single degenerate worker must have written its frozen-root "
        "manifest"
    )
    identities, _worker_dirs, matrix_models = _manifest_cells(w0)
    assert matrix_models == ["model-a", "model-b"], (
        "workers=1 carries the WHOLE requested model set (the LPT "
        "degenerate shard)"
    )
    assert identities == {
        ("model-a", "task-x", 42), ("model-b", "task-x", 42)}, (
        "the degenerate worker planned exactly the 2-model matrix"
    )
    log = run_sweep_shard.worker_log_path(base, 0, "20261013_120000")
    assert log.is_file() and log.read_text(encoding="utf-8").strip(), (
        "the sibling tee log exists and captured the child's output"
    )
    assert not run_sweep_shard.worker_root(base, 1).exists(), (
        "workers=1 never creates a w1 root"
    )
    assert not base.exists(), (
        "the launch mode writes ONLY frozen sibling roots — never the "
        "base root itself (shared roots are FORBIDDEN, Pitfall 1)"
    )
