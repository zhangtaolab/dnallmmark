"""
Unit tests for ``pipeline/dispatch_core.py`` + the ``--mode`` surface
(13-01, MGPU-01/MGPU-02).

Coverage named by the plan (SC ids are the phase acceptance tests):

- **SC3 (double-claim is structurally refused)** — ``claim_cell`` on a
  live-claimed cell returns None (the O_EXCL ``EEXIST``), the original
  claim is untouched, and within one run no second child is ever spawned
  for one cell.
- **SC2 (kill-proven resume)** — the skip filter (marker OR
  ledger-completed skip; stale-claim requeue with atomic claim
  replacement), the dead-pid lock reclaim (A5) with the live-pid loud
  refusal, skip-set order purity, and the two-run kill test over ONE
  shared root: run 1 kills one cell mid-flight (fake child returning
  SIGKILL), the relaunch re-dispatches EXACTLY that cell, and every
  cell ends with exactly one artifact set (no duplicates, no orphans).
- **Happy path** — 3 models x 2 tasks x 2 seeds over ``--workers 2``
  with per-cell fake children: exactly 12 spawns, every artifact set at
  ``run_sweep.cell_dir_for`` paths under the ONE shared root, zero
  ``{root}-mgpu-w{i}`` sibling roots, every claim ``completed``,
  ``dispatch_state.json`` written BEFORE any spawn and finalized with
  counts.
- **The verbatim static spawn discipline** — argv LIST,
  ``start_new_session=True``, cwd pinned to ``run_sweep.PIPELINE_DIR``,
  env superset with ``PYTHONUNBUFFERED == "1"`` and the worker's
  ``CUDA_VISIBLE_DEVICES`` token, ``stderr=STDOUT``, stdout teed into
  the frozen ``{base}-dispatch-w{i}-{stamp}.log`` sibling.
- **Lane threading** — ``--peft lora`` rides the remainder: cells
  enumerate under the ALIAS names and each argv carries
  ``--target_model <base>`` + ``--save_model_name <alias>`` +
  ``--peft lora`` (the run_sweep alias semantics, composed verbatim).
- **SC1 dry-run goldens (13-02)** — ``--mode dispatch --dry-run``
  writes ONLY ``{root}/sweep_manifest.json`` (no lock, no state file,
  no claims, no children) with every cell ``status: "planned"`` and the
  ``orchestrator_mode: "dispatch"`` marker; two consecutive runs are
  byte-identical; the planned identity set equals the UNION of
  static-mode per-worker dry-run manifests for identical inputs
  (identity projection only — output_dirs differ by root by design);
  ``--priority-file`` reorders the planned cells without changing the
  set; peft rides alias identities while config_variant joins every
  cell via the sweep_flags merge.
- **Validation mirror refusals** — the variant x peft remainder
  combination refuses by name; a missing ``--seeds`` exits with
  argparse's code 2 (Pitfall 9, pinned); an empty ``--models`` value
  refuses naming the flag; an ENUMERATED matrix of zero cells refuses
  BEFORE the lock is acquired (never a silent full-registry fallback).
- **The singleton lock** — a held lock refuses loudly naming the lock
  path; the STATIC launch path never acquires any lock (mode
  isolation); ``--mode dispatch`` + ``--merge`` on one command line is
  refused with the named A6 problem.
- **The frozen naming** — ``claim_filename`` is deterministic and
  injective over the tricky tuple set (``+`` aliases, ``__`` task keys,
  float fractions, a deliberately ``--``-containing name pair), each
  claim JSON's cell key agrees with its filename's encoded fields, and
  the worker tee log naming is frozen.
- **Mode coexistence (13-02 Task 2, MGPU-06)** — ``--merge`` refuses
  ANY root set carrying run-recorded dispatch evidence
  (``dispatch_state.json``, the ``dispatch_ledger`` dir, or a manifest
  ``orchestrator_mode: "dispatch"`` cell marker) with the named
  "needs no merge" problem BEFORE any copy; a static-only root set
  merges exactly as before (the control); an explicit ``--mode static``
  launch is pinned byte-identical to the default at the argv /
  worker-root / tee-log level; the dispatch x merge combination
  refusal is re-asserted adjacent to the merge suites.

Fake children derive the cell dir EXACTLY the way the real child does —
root + SAVE-NAME model + task + ``seed_{--seed}`` (under ``--peft`` /
``--config-variant`` the save name is the ALIAS carried by
``--save_model_name``) — because ``--output_dir`` carries the ROOT
(Pitfall 2); assertions always go through ``run_sweep.cell_dir_for``
(Pitfall 1 — never a ``seed{k}`` literal). Per-cell scripted fakes are
used everywhere multi-worker ordering could interleave (Pitfall 7).
CPU-only: no test assumes N>1 GPUs, launches real training, or probes
nvidia-smi (D-05).

See also:
    ``pipeline/dispatch_core.py`` — the engine under test.
    ``tests/test_sweep_shard.py`` — the static-mode contract suite that
    stays byte-identical (the mode-isolation tripwire).
"""

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote

import dispatch_core
import pytest
import run_sweep  # conftest puts pipeline/ on sys.path
import run_sweep_shard

REPO_ROOT = Path(__file__).resolve().parents[1]

# ===== machine-independence pin (the test_sweep_shard.py idiom) =====
#
# Dispatch enumeration joins the requested --models names against the
# registry_loader view (official + custom overlay), so a maintainer-local
# custom overlay must not leak into these tests. Pin BOTH overlay env
# vars to a fresh empty dir for every test here. The root conftest
# additionally pins the directories.json XDG config dir per-test.


@pytest.fixture(autouse=True)
def _pin_custom_registry_overlay(tmp_path, monkeypatch):
    """Empty-dir pin over the custom overlay for every test here."""
    pinned = tmp_path / "no-custom-overlay"
    pinned.mkdir()
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(pinned))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(pinned))


# ===== helpers (local copies of the test_sweep_shard.py:125-222 idioms —
# the suite stays self-contained; run_cli targets run_sweep_shard.main
# and takes the injectable spawner/clock) =====


def write_registry(root, models, datasets):
    """Materialize unified-registry fixtures under ``root``."""
    (root / "models_info.json").write_text(
        json.dumps(models), encoding="utf-8")
    (root / "datasets_info.json").write_text(
        json.dumps(datasets), encoding="utf-8")


def make_registry(tmp_path):
    """Build the 3-model x 3-task registry fixture (task-y has Train=0).

    Same shape as the shard suite's fixture; sizes are irrelevant to
    dispatch (no LPT) but keep the fixtures identical for reuse.
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
    injectable spawner/clock seams — the shard-suite idiom)."""
    full_argv = ["run_sweep_shard.py", *argv]
    monkeypatch.setattr(sys, "argv", full_argv)
    run_sweep_shard.main(spawner=spawner, clock=clock)
    return full_argv


def run_sweep_cli(monkeypatch, argv):
    """Invoke ``run_sweep.main()`` with a patched argv (worker mimic —
    the comparison idiom Plan 13-02's static-union equality needs)."""
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

    def __init__(self, returncode=0, pid=4242):
        self.pid = pid  # the dispatcher records it into the claim JSON
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


def make_child_spawner(calls, exit_for=None):
    """Build a PER-CELL scripted fake child (Pitfall 7 discipline).

    Derives the cell dir exactly the way the real child does —
    ``--output_dir`` carries the ROOT, so the cell dir is root +
    SAVE-NAME model + task + ``seed_{--seed}`` (the save name is the
    ALIAS under ``--save_model_name``, else ``--target_model``; a
    ``--train_fraction`` nests ``frac_{f}`` under the seed dir) — and
    writes the success artifact pair for exit-0 cells. ``exit_for``
    maps ``(save name, task, seed)`` to a scripted returncode so a kill
    lands on ONE targeted cell regardless of worker interleaving. Every
    call also records whether ``dispatch_state.json`` already existed
    (the write-order pin).
    """

    def spawn(argv, **kwargs):
        root = Path(flag_value(argv, "--output_dir"))
        record = {
            "argv": list(argv),
            "kwargs": kwargs,
            "state_existed": (
                root / dispatch_core.DISPATCH_STATE_NAME).is_file(),
        }
        calls.append(record)
        save = (
            flag_value(argv, "--save_model_name")
            if "--save_model_name" in argv
            else flag_value(argv, "--target_model"))
        task = flag_value(argv, "--target_dataset")
        seed = int(flag_value(argv, "--seed"))
        cell_dir = root / save / task / f"seed_{seed}"
        if "--train_fraction" in argv:
            cell_dir = cell_dir / (
                f"frac_{flag_value(argv, '--train_fraction')}")
        code = 0
        if exit_for is not None:
            code = exit_for.get((save, task, seed), 0)
        if code == 0:
            cell_dir.mkdir(parents=True, exist_ok=True)
            (cell_dir / run_sweep.METRICS_NAME).write_text(
                json.dumps({"eval_loss": 0.5, "eval_accuracy": 0.9}),
                encoding="utf-8")
            (cell_dir / run_sweep.RESUME_MARKER).write_text(
                '{"global_step": 1}', encoding="utf-8")
        return FakeProc(code)

    return spawn


def spawn_identities(calls):
    """Project captured spawn argvs to (model, task, seed) identities."""
    return [
        (flag_value(call["argv"], "--target_model"),
         flag_value(call["argv"], "--target_dataset"),
         int(flag_value(call["argv"], "--seed")))
        for call in calls
    ]


DISPATCH_ARGV = [
    "--mode", "dispatch",
    "--workers", "2",
    "--models", "model-a,model-b,model-c",
    "--tasks", "task-x,task-z",
    "--seeds", "42,43",
]


# ===== happy path: the end-to-end tracer through the injectable seams =====


def test_dispatch_happy_path_end_to_end(tmp_path, monkeypatch):
    """3 models x 2 tasks x 2 seeds over --workers 2 with per-cell fake
    children: exactly 12 spawns, every argv targets run_finetune.py with
    the SHARED root as --output_dir, every artifact set lands at a
    cell_dir_for path under the ONE root, zero -mgpu-w{i} sibling roots,
    every claim completed, and the state file carries mode + counts."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    calls = []
    clock = lambda: datetime(2026, 10, 20, 4, 0, 0, tzinfo=UTC)
    run_cli(monkeypatch, [
        *DISPATCH_ARGV,
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner(calls), clock=clock)

    assert len(calls) == 12, "one spawn per enumerated cell"
    expected = run_sweep.enumerate_matrix(
        ["model-a", "model-b", "model-c"], ["task-x", "task-z"],
        [42, 43], registry_dir)
    assert len(expected) == 12
    for call in calls:
        argv = call["argv"]
        assert isinstance(argv, list)
        assert all(isinstance(element, str) for element in argv)
        assert argv[0] == sys.executable
        assert argv[1].endswith("run_finetune.py"), (
            "dispatch spawns run_finetune children directly (Shape 1)"
        )
        assert flag_value(argv, "--output_dir") == str(base), (
            "the child receives the SHARED root (never a worker root)"
        )
        env = call["kwargs"]["env"]
        assert env["CUDA_VISIBLE_DEVICES"] in {"0", "1"}, (
            "each spawn carries exactly one worker's GPU token"
        )
    for model, task, seed in expected:
        cell_dir = run_sweep.cell_dir_for(base, model, task, seed)
        assert (cell_dir / run_sweep.METRICS_NAME).is_file()
        assert (cell_dir / run_sweep.RESUME_MARKER).is_file()
    ledger_dir = dispatch_core.ledger_dir_for(base)
    claims = sorted(
        path for path in ledger_dir.glob("*.json")
        if path.name != dispatch_core.DISPATCHER_LOCK_NAME)
    assert len(claims) == 12
    for claim_path in claims:
        payload = json.loads(claim_path.read_text(encoding="utf-8"))
        assert payload["state"] == "completed"
        assert payload["child_pid"] == 4242, (
            "the child pid recorded into the claim after spawn"
        )
    state = json.loads(
        (base / dispatch_core.DISPATCH_STATE_NAME).read_text(
            encoding="utf-8"))
    assert state["mode"] == "dispatch"
    assert state["status"] == "done"
    assert state["counts"] == {
        "total": 12, "completed": 12, "failed": 0, "skipped": 0}
    assert state["run_id"]
    assert state["run_id"] == json.loads(
        claims[0].read_text(encoding="utf-8"))["run_id"]
    for i in (0, 1):
        assert not run_sweep_shard.worker_root(base, i).exists(), (
            "dispatch writes ONE shared root — never sibling worker roots"
        )
    assert not (ledger_dir / dispatch_core.DISPATCHER_LOCK_NAME).exists(), (
        "the singleton lock is released after the drain"
    )
    assert not list(base.rglob("*.tmp")), "no atomic-write tmp residue"


def test_child_pid_durable_on_disk_while_child_runs(tmp_path, monkeypatch):
    """CR-03 pin: for the child's ENTIRE lifetime the on-disk claim names
    its pid — a spy child reads its own claim during wait() (i.e. while
    it "runs") and observes state 'claimed' with a NON-null child_pid.
    The documented orphan-recovery procedure (kill the orphans named by
    the claims before relaunch) depends on this; the pid used to reach
    disk only at finalize, i.e. after the child had already exited."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    observed = []

    def spy_spawner(argv, **kwargs):
        root = Path(flag_value(argv, "--output_dir"))
        save = (
            flag_value(argv, "--save_model_name")
            if "--save_model_name" in argv
            else flag_value(argv, "--target_model"))
        cell = (save, flag_value(argv, "--target_dataset"),
                int(flag_value(argv, "--seed")))

        class SpyProc(FakeProc):
            def wait(self, timeout=None):
                # The dispatcher already spawned us and (CR-03) already
                # persisted our pid — read the claim NOW, mid-"training".
                claim_path = (
                    dispatch_core.ledger_dir_for(root)
                    / dispatch_core.claim_filename(cell))
                observed.append(
                    json.loads(claim_path.read_text(encoding="utf-8")))
                return super().wait(timeout=timeout)

        # Success artifacts, exactly the make_child_spawner discipline:
        # without final_metrics.json the CR-02 artifact check fails the
        # cell and the run's exit-1 SystemExit escapes the test.
        cell_dir = root / save / cell[1] / f"seed_{cell[2]}"
        cell_dir.mkdir(parents=True, exist_ok=True)
        (cell_dir / run_sweep.METRICS_NAME).write_text(
            json.dumps({"eval_loss": 0.5}), encoding="utf-8")
        (cell_dir / run_sweep.RESUME_MARKER).write_text(
            '{"global_step": 1}', encoding="utf-8")
        return SpyProc(0)

    run_cli(monkeypatch, [
        "--mode", "dispatch", "--workers", "1",
        "--models", "model-a", "--tasks", "task-x", "--seeds", "42,43",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=spy_spawner)
    assert len(observed) == 2, "each child observed its own claim"
    for claim in observed:
        assert claim["state"] == dispatch_core.CLAIM_STATE_CLAIMED, (
            "the mid-run claim is still in the claimed state"
        )
        assert claim["child_pid"] == 4242, (
            "the child pid is durable on disk WHILE the child runs"
        )


def test_dispatch_state_file_exists_before_any_spawn(tmp_path, monkeypatch):
    """Pitfall 8 write-order pin: every spawn observes
    dispatch_state.json ALREADY on disk — the mode evidence precedes any
    claim/spawn, so a crash mid-run can never leave the root without
    evidence."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    calls = []
    run_cli(monkeypatch, [
        "--mode", "dispatch", "--workers", "2",
        "--models", "model-a", "--tasks", "task-x", "--seeds", "42,43",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner(calls))
    assert len(calls) == 2
    assert all(call["state_existed"] for call in calls), (
        "dispatch_state.json must exist at the root before any spawn"
    )


def test_dispatch_spawn_kwargs_verbatim_discipline(tmp_path, monkeypatch):
    """Every spawn carries the verbatim STATIC discipline minus
    worker-root naming: argv LIST, own session, cwd pinned to
    run_sweep.PIPELINE_DIR, env copy + PYTHONUNBUFFERED + the ONE
    CUDA_VISIBLE_DEVICES token, stderr onto stdout's tee, stdout teed
    into the frozen dispatch worker log sibling."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    calls = []
    clock = lambda: datetime(2026, 10, 20, 4, 30, 0, tzinfo=UTC)
    monkeypatch.setenv("DISPATCH_TEST_SENTINEL", "xyz")
    run_cli(monkeypatch, [
        "--mode", "dispatch", "--workers", "1", "--gpus", "3",
        "--models", "model-a", "--tasks", "task-x", "--seeds", "42",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner(calls), clock=clock)
    assert len(calls) == 1
    argv = calls[0]["argv"]
    kwargs = calls[0]["kwargs"]
    assert argv[0] == sys.executable
    assert argv[1].endswith("run_finetune.py")
    assert flag_value(argv, "--target_model") == "model-a"
    assert flag_value(argv, "--target_dataset") == "task-x"
    assert flag_value(argv, "--seed") == "42"
    assert flag_value(argv, "--output_dir") == str(base)
    assert kwargs["start_new_session"] is True
    assert kwargs["cwd"] == str(run_sweep.PIPELINE_DIR)
    assert kwargs["stderr"] == subprocess.STDOUT
    env = kwargs["env"]
    assert env["DISPATCH_TEST_SENTINEL"] == "xyz", (
        "env is a copy of os.environ (superset)"
    )
    assert env["PYTHONUNBUFFERED"] == "1"
    assert env["CUDA_VISIBLE_DEVICES"] == "3", (
        "the --gpus token forwards verbatim as this worker's pin"
    )
    assert kwargs["stdout"].name == str(
        dispatch_core.dispatch_worker_log_path(base, 0, "20261020_043000")), (
        "stdout tees into the per-launch dispatch worker log (WR-02)"
    )


def test_dispatch_single_worker_drains_whole_queue(tmp_path, monkeypatch):
    """EDGE MGPU-01/empty: --workers 1 (the single-element degenerate)
    drains the WHOLE queue — every one of the 12 spawns pinned to the
    one GPU token."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    calls = []
    run_cli(monkeypatch, [
        "--mode", "dispatch", "--workers", "1",
        "--models", "model-a,model-b,model-c",
        "--tasks", "task-x,task-z", "--seeds", "42,43",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner(calls))
    assert len(calls) == 12
    assert all(call["kwargs"]["env"]["CUDA_VISIBLE_DEVICES"] == "0"
               for call in calls)


def test_dispatch_workers_are_not_model_bound(tmp_path, monkeypatch):
    """Pitfall 3 isolation: the static empty-shard refusal
    (--workers > model count) must NOT fire in dispatch mode — dispatch
    workers pull from a queue, they do not own models."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    calls = []
    run_cli(monkeypatch, [
        "--mode", "dispatch", "--workers", "4",
        "--models", "model-a", "--tasks", "task-x", "--seeds", "42",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner(calls))
    assert len(calls) == 1, "the single cell spawns exactly once"
    state = json.loads(
        (base / dispatch_core.DISPATCH_STATE_NAME).read_text(
            encoding="utf-8"))
    assert state["counts"]["completed"] == 1


def test_dispatch_gpus_override_tokens_forward_verbatim(
        tmp_path, monkeypatch):
    """--gpus "5,7" maps token-per-index into CUDA_VISIBLE_DEVICES
    (operator-owned strings; which worker claims which cell is
    scheduler-dependent, so the pin is per-spawn membership)."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    calls = []
    run_cli(monkeypatch, [
        "--mode", "dispatch", "--workers", "2", "--gpus", "5,7",
        "--models", "model-a,model-b", "--tasks", "task-x",
        "--seeds", "42,43",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner(calls))
    assert len(calls) == 4
    for call in calls:
        assert call["kwargs"]["env"]["CUDA_VISIBLE_DEVICES"] in {"5", "7"}


def test_dispatch_queue_order_is_deterministic(tmp_path, monkeypatch):
    """Identical inputs enumerate identical queues: with --workers 1 the
    spawn order IS the queue order, equal across two runs and equal to
    run_sweep.enumerate_matrix's sorted() base order; a --priority-file
    permutes it through apply_priority_order (stable reorder)."""
    registry_dir = make_registry(tmp_path)

    def launch(base_root, extra=()):
        calls = []
        run_cli(monkeypatch, [
            "--mode", "dispatch", "--workers", "1",
            "--models", "model-a,model-b,model-c",
            "--tasks", "task-x,task-z", "--seeds", "42,43",
            "--output-root", str(base_root),
            "--registry-dir", str(registry_dir),
            *extra,
        ], spawner=make_child_spawner(calls))
        return spawn_identities(calls)

    order1 = launch((tmp_path / "r1").resolve())
    order2 = launch((tmp_path / "r2").resolve())
    assert order1 == order2, "identical inputs enumerate identical queues"
    expected = run_sweep.enumerate_matrix(
        ["model-a", "model-b", "model-c"], ["task-x", "task-z"],
        [42, 43], registry_dir)
    assert order1 == [tuple(cell) for cell in expected], (
        "the queue order is enumerate_matrix's sorted() base order"
    )
    # priority reorder threads through verbatim (D13-03)
    priorities = tmp_path / "priorities.json"
    priorities.write_text(
        json.dumps([[{"model": "model-c", "task": "task-x"}]]),
        encoding="utf-8")
    prioritized = launch(
        (tmp_path / "r3").resolve(),
        extra=["--priority-file", str(priorities)])
    assert prioritized[0] == ("model-c", "task-x", 42), (
        "the tier entry's cells run first (apply_priority_order)"
    )
    assert sorted(prioritized) == sorted(order1), (
        "the priority reorder permutes WITHOUT duplicating or dropping"
    )


# ===== --from-failures scoping (CR-01, phase-13 review) =====


def test_dispatch_from_failures_scopes_enumeration_to_failed_pairs(
        tmp_path, monkeypatch):
    """CR-01 pin: a dispatch launch scoped by --from-failures enumerates
    EXACTLY the manifest's failed (model, task) pairs across the requested
    seeds — never the full --models x --tasks filter matrix (the silent
    full-matrix fallback the zero-cell refusal family exists to prevent)."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    failures = tmp_path / "sweep_failures.json"
    failures.write_text(
        json.dumps([{"model": "model-b", "task": "task-z"}]),
        encoding="utf-8")
    calls = []
    run_cli(monkeypatch, [
        "--mode", "dispatch", "--workers", "2",
        "--models", "model-a,model-b,model-c",
        "--tasks", "task-x,task-z", "--seeds", "42,43",
        "--from-failures", str(failures),
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner(calls))
    assert sorted(spawn_identities(calls)) == [
        ("model-b", "task-z", 42), ("model-b", "task-z", 43)], (
        "exactly the failed pair's cells across the requested seeds"
    )
    state = json.loads(
        (base / dispatch_core.DISPATCH_STATE_NAME).read_text(
            encoding="utf-8"))
    assert state["counts"] == {
        "total": 2, "completed": 2, "failed": 0, "skipped": 0}


def test_dispatch_from_failures_malformed_manifest_refuses_loudly(
        tmp_path, monkeypatch):
    """CR-01 pin: a --from-failures manifest with an unknown model name
    refuses through run_sweep.load_failure_pairs' collect-all validation
    BEFORE anything touches the root — the same loud refusal every
    run_sweep.main launch performs, never a silent no-op."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    failures = tmp_path / "sweep_failures.json"
    failures.write_text(
        json.dumps([{"model": "model-zz", "task": "task-x"}]),
        encoding="utf-8")
    calls = []
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--mode", "dispatch", "--workers", "1",
            "--models", "model-a", "--tasks", "task-x", "--seeds", "42",
            "--from-failures", str(failures),
            "--output-root", str(base),
            "--registry-dir", str(registry_dir),
        ], spawner=make_child_spawner(calls))
    message = str(excinfo.value)
    assert "--from-failures" in message
    assert "not in registry" in message
    assert not calls
    assert not base.exists(), "refused before the root was touched"


def test_dispatch_from_failures_clean_manifest_never_full_sweep(
        tmp_path, monkeypatch, capsys):
    """CR-01 pin: a CLEAN manifest (0 failed pairs) is an explicit
    zero-cell run — the mirrored message prints, the dispatch zero-cell
    refusal fires by name, and NOT ONE cell of the wide filter matrix
    spawns (a clean manifest must never silently become a full sweep)."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    failures = tmp_path / "sweep_failures.json"
    failures.write_text("[]", encoding="utf-8")
    calls = []
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--mode", "dispatch", "--workers", "1",
            "--models", "model-a,model-b", "--tasks", "task-x",
            "--seeds", "42,43",
            "--from-failures", str(failures),
            "--output-root", str(base),
            "--registry-dir", str(registry_dir),
        ], spawner=make_child_spawner(calls))
    assert "0 cell" in str(excinfo.value), (
        "the zero-cell refusal catches the filtered-to-empty matrix"
    )
    out = capsys.readouterr().out
    assert "is clean (0 failed pairs)" in out, (
        "the mirrored explicit-zero-cell message prints first"
    )
    assert "NOT a full sweep" in out
    assert not calls
    assert not base.exists()


# ===== lane threading =====


def test_dispatch_peft_lane_enumerates_and_spawns_under_alias(
        tmp_path, monkeypatch):
    """--peft lora rides the remainder: cells enumerate under the ALIAS
    model names, each argv targets --target_model <base> plus
    --save_model_name <alias> + --peft lora (run_sweep.build_argv
    semantics composed verbatim), artifacts land under the alias cell
    dir, and the claim carries the alias cell key + lane flags."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    calls = []
    run_cli(monkeypatch, [
        "--mode", "dispatch", "--workers", "1",
        "--models", "model-a", "--tasks", "task-x", "--seeds", "42",
        "--peft", "lora",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner(calls))
    assert len(calls) == 1
    argv = calls[0]["argv"]
    assert flag_value(argv, "--target_model") == "model-a", (
        "the registry join stays on BASE names"
    )
    assert flag_value(argv, "--save_model_name") == "model-a+lora"
    assert flag_value(argv, "--peft") == "lora"
    cell_dir = run_sweep.cell_dir_for(base, "model-a+lora", "task-x", 42)
    assert (cell_dir / run_sweep.METRICS_NAME).is_file(), (
        "the fake child wrote under the ALIAS dir (the save-name rule)"
    )
    claim = json.loads(
        (dispatch_core.ledger_dir_for(base) / dispatch_core.claim_filename(
            ("model-a+lora", "task-x", 42))).read_text(encoding="utf-8"))
    assert claim["cell"] == {
        "model": "model-a+lora", "task": "task-x", "seed": 42,
        "fraction": None}
    assert claim["lane"]["peft"] == "lora"


# ===== 13-02 Task 1: the dry-run plan artifact (SC1 goldens) =====


def _read_manifest(root):
    """Parse ``{root}/sweep_manifest.json`` (planned or executed)."""
    return json.loads(
        (Path(root) / run_sweep.MANIFEST_NAME).read_text(encoding="utf-8"))


def _manifest_identities(root):
    """Project a manifest's cells to (model, task, seed) identity tuples.

    The SC1 comparison vocabulary: identities ONLY, never absolute
    output_dir paths (worker roots and the dispatch shared root differ
    by design — only the cell identities must agree).
    """
    return {
        (cell["model"], cell["task"], cell["seed"])
        for cell in _read_manifest(root)["cells"]
    }


def test_dispatch_dry_run_writes_only_plan_manifest(tmp_path, monkeypatch):
    """SC1/MGPU-01: a dispatch dry-run leaves the root with EXACTLY
    sweep_manifest.json — no ledger dir, no state file, no
    trainer_state.json anywhere, no dispatch/mgpu worker logs or roots,
    and the injected spawner is NEVER called. The manifest carries the
    static dry-run projection (matrix with sorted unions + the resolved
    root, cells with status 'planned' at cell_dir_for paths) plus the
    orchestrator_mode marker merged into every cell."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    calls = []
    run_cli(monkeypatch, [
        *DISPATCH_ARGV, "--dry-run",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner(calls))
    assert calls == [], "the dry-run never spawns a child"
    assert sorted(path.name for path in base.iterdir()) == [
        run_sweep.MANIFEST_NAME], (
        "the dry-run's ONLY output is the plan manifest"
    )
    assert not dispatch_core.ledger_dir_for(base).exists(), (
        "no ledger — the dry-run branch runs before the lock section"
    )
    assert not (base / dispatch_core.DISPATCH_STATE_NAME).exists()
    assert not list(base.rglob(run_sweep.RESUME_MARKER))
    assert not list(base.parent.glob(f"{base.name}-dispatch-w*.log"))
    assert not list(base.parent.glob(f"{base.name}-mgpu-w*")), (
        "no static worker sibling roots either"
    )
    manifest = _read_manifest(base)
    assert manifest["matrix"] == {
        "models": ["model-a", "model-b", "model-c"],
        "tasks": ["task-x", "task-z"],
        "seeds": [42, 43],
        "output_root": str(base),
    }
    expected = run_sweep.enumerate_matrix(
        ["model-a", "model-b", "model-c"], ["task-x", "task-z"],
        [42, 43], registry_dir)
    assert len(manifest["cells"]) == len(expected) == 12
    for cell, expected_cell in zip(manifest["cells"], expected):
        assert cell["model"] == expected_cell[0]
        assert cell["task"] == expected_cell[1]
        assert cell["seed"] == expected_cell[2]
        assert cell["status"] == "planned"
        assert cell["output_dir"] == str(run_sweep.cell_dir_for(
            base, expected_cell[0], expected_cell[1], expected_cell[2]))
        assert cell["orchestrator_mode"] == "dispatch"


def test_dispatch_dry_run_is_byte_identical_across_runs(
        tmp_path, monkeypatch):
    """SC1 golden: two consecutive dry-runs over the identical
    registry/filters/seeds write byte-identical manifests (the
    _write_json indent=4 / ensure_ascii=False / sort_keys discipline) —
    the first bytes are copied aside so the second run's overwrite is
    compared, not assumed."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    common = [
        *DISPATCH_ARGV, "--dry-run",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ]
    run_cli(monkeypatch, list(common), spawner=make_child_spawner([]))
    manifest_path = base / run_sweep.MANIFEST_NAME
    aside = tmp_path / "first-manifest.json"
    aside.write_bytes(manifest_path.read_bytes())
    run_cli(monkeypatch, list(common), spawner=make_child_spawner([]))
    assert hashlib.sha256(
        aside.read_bytes()).hexdigest() == hashlib.sha256(
        manifest_path.read_bytes()).hexdigest(), (
        "consecutive dry-runs serialize byte-identically"
    )


def test_dispatch_dry_run_identity_set_equals_static_union(
        tmp_path, monkeypatch):
    """SC1 union equality (the disjointness-test comparison idiom): the
    dispatch dry-run's identity set over --models A,B,C / --tasks /
    --seeds equals the UNION of two static per-worker dry-run manifests
    over the same axes (LPT shards) — compared over identity tuples
    ONLY; output_dir sets are never compared (worker roots vs the ONE
    shared root differ by design)."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    run_cli(monkeypatch, [
        *DISPATCH_ARGV, "--dry-run",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner([]))
    dispatch_identities = _manifest_identities(base)

    sizes = {"model-a": 100, "model-b": 50, "model-c": 10}
    shards = run_sweep_shard.lpt_shard(
        ["model-a", "model-b", "model-c"], 2, sizes)
    assert shards == [["model-a"], ["model-b", "model-c"]]
    static_union = set()
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
        static_union |= _manifest_identities(root)
    assert dispatch_identities == static_union, (
        "dispatch enumeration equals static-mode enumeration for "
        "identical inputs (identity projection only)"
    )
    assert len(dispatch_identities) == 12


def test_dispatch_dry_run_priority_reorders_planned_cells(
        tmp_path, monkeypatch):
    """A --priority-file reorders the planned cells into the queue order
    (the manifest's cell LIST order carries it) while the identity SET
    is unchanged; a second dry-run without the file plans the same SET
    in the sorted() base order."""
    registry_dir = make_registry(tmp_path)
    priorities = tmp_path / "priorities.json"
    priorities.write_text(
        json.dumps([[{"model": "model-c", "task": "task-x"}]]),
        encoding="utf-8")
    with_prio = (tmp_path / "with-prio").resolve()
    without_prio = (tmp_path / "without-prio").resolve()
    common = [
        "--mode", "dispatch", "--workers", "2",
        "--models", "model-a,model-b,model-c",
        "--tasks", "task-x,task-z", "--seeds", "42,43",
        "--dry-run",
        "--registry-dir", str(registry_dir),
    ]
    run_cli(monkeypatch, [
        *common, "--priority-file", str(priorities),
        "--output-root", str(with_prio),
    ], spawner=make_child_spawner([]))
    run_cli(monkeypatch, [
        *common, "--output-root", str(without_prio),
    ], spawner=make_child_spawner([]))

    def cell_order(root):
        return [
            (cell["model"], cell["task"], cell["seed"])
            for cell in _read_manifest(root)["cells"]]

    prioritized = cell_order(with_prio)
    plain = cell_order(without_prio)
    assert prioritized[0] == ("model-c", "task-x", 42), (
        "the tier entry's cells plan first (apply_priority_order)"
    )
    assert sorted(prioritized) == sorted(plain), (
        "the priority reorder permutes the queue WITHOUT changing the set"
    )
    assert plain == sorted(plain), (
        "the no-file dry-run plans in the sorted() base order"
    )
    assert set(plain) == {
        tuple(cell) for cell in run_sweep.enumerate_matrix(
            ["model-a", "model-b", "model-c"], ["task-x", "task-z"],
            [42, 43], registry_dir)}


def test_dispatch_dry_run_peft_alias_and_variant_flag_shapes(
        tmp_path, monkeypatch):
    """Lane flags on the plan artifact: a --peft lora dry-run plans
    cells under the ALIAS model names with 'peft' NOT a manifest key
    (peft rides the identities, mirroring run_sweep); a
        --config-variant probe dry-run plans under {model}+probe names
    and carries config_variant in every cell via the sweep_flags merge
    (the only lane axis that joins)."""
    registry_dir = make_registry(tmp_path)

    lora_root = (tmp_path / "lora").resolve()
    run_cli(monkeypatch, [
        "--mode", "dispatch", "--workers", "1",
        "--models", "model-a", "--tasks", "task-x", "--seeds", "42",
        "--peft", "lora", "--dry-run",
        "--output-root", str(lora_root),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner([]))
    lora_manifest = _read_manifest(lora_root)
    assert lora_manifest["matrix"]["models"] == ["model-a+lora"]
    assert len(lora_manifest["cells"]) == 1
    lora_cell = lora_manifest["cells"][0]
    assert lora_cell["model"] == "model-a+lora"
    assert "peft" not in lora_cell, (
        "peft rides the alias identities, never a manifest key"
    )
    assert lora_cell["orchestrator_mode"] == "dispatch"

    probe_root = (tmp_path / "probe").resolve()
    run_cli(monkeypatch, [
        "--mode", "dispatch", "--workers", "1",
        "--models", "model-a", "--tasks", "task-x", "--seeds", "42",
        "--config-variant", "probe", "--dry-run",
        "--output-root", str(probe_root),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner([]))
    probe_manifest = _read_manifest(probe_root)
    assert len(probe_manifest["cells"]) == 1
    probe_cell = probe_manifest["cells"][0]
    assert probe_cell["model"] == "model-a+probe"
    assert probe_cell["config_variant"] == "probe", (
        "a present variant joins every cell via the sweep_flags merge"
    )
    assert probe_cell["orchestrator_mode"] == "dispatch"


# ===== validation mirror refusals (collect-all, named) =====


def test_dispatch_refuses_variant_peft_combination(tmp_path, monkeypatch):
    """The remainder combination run_sweep refuses collect-all
    (run_sweep.py:1796-1802) refuses in dispatch mode too, naming both
    flags, before any spawn or root write."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    calls = []
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--mode", "dispatch", "--workers", "1",
            "--models", "model-a", "--tasks", "task-x", "--seeds", "42",
            "--peft", "lora", "--config-variant", "probe",
            "--output-root", str(base),
            "--registry-dir", str(registry_dir),
        ], spawner=make_child_spawner(calls))
    message = str(excinfo.value)
    assert "--config-variant" in message
    assert "--peft" in message
    assert "never compose" in message
    assert not calls
    assert not base.exists(), "refused before the root was touched"


def test_dispatch_missing_seeds_exits_argparse_code_2(
        tmp_path, monkeypatch):
    """Pitfall 9 pinned as accepted: a dispatch launch without --seeds
    dies at the remainder re-parse with argparse's own usage exit
    (code 2), exactly like a static worker would inside its process."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    calls = []
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--mode", "dispatch", "--workers", "1",
            "--models", "model-a", "--tasks", "task-x",
            "--output-root", str(base),
            "--registry-dir", str(registry_dir),
        ], spawner=make_child_spawner(calls))
    assert excinfo.value.code == 2
    assert not calls


def test_dispatch_empty_models_value_refuses(tmp_path, monkeypatch):
    """A provided-but-empty --models value refuses by name (the WR-14
    twin), never degrading toward a full-registry dispatch."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    calls = []
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--mode", "dispatch", "--workers", "1",
            "--models", ",",
            "--tasks", "task-x", "--seeds", "42",
            "--output-root", str(base),
            "--registry-dir", str(registry_dir),
        ], spawner=make_child_spawner(calls))
    assert "--models" in str(excinfo.value)
    assert "no model names" in str(excinfo.value)
    assert not calls


def test_dispatch_zero_enumeration_refuses_before_lock(
        tmp_path, monkeypatch):
    """EDGE MGPU-01/empty: a registry/filter combination that passes
    name validation but enumerates ZERO cells (an empty datasets
    registry) refuses by name BEFORE the lock is acquired — no state
    file, no ledger, root untouched, never a full-registry fallback."""
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    write_registry(
        registry_dir,
        models={"model-a": {"Model_name": "model-a",
                            "Model_path": "models/a"}},
        datasets={},
    )
    base = (tmp_path / "finetuned").resolve()
    calls = []
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--mode", "dispatch", "--workers", "1",
            "--models", "model-a", "--seeds", "42",
            "--output-root", str(base),
            "--registry-dir", str(registry_dir),
        ], spawner=make_child_spawner(calls))
    message = str(excinfo.value)
    assert "0 cell" in message
    assert "never falls back" in message
    assert not calls
    assert not base.exists(), (
        "no lock acquired, no state evidence — refused pre-lock"
    )


def test_dispatch_subset_file_validated_at_startup(tmp_path, monkeypatch):
    """WR-01 pin: a bad --subset_file map (here: an unknown task key)
    refuses at dispatch STARTUP through run_sweep._validate_subset_file's
    collect-all problem list — before any spawn and before the root is
    touched — never one burned child launch per cell recorded as N cell
    failures. A VALID map is the control: it threads through and the
    run proceeds."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    bad_subset = tmp_path / "subset-bad.json"
    bad_subset.write_text(
        json.dumps({"no-such-task": [1, 2]}), encoding="utf-8")
    calls = []
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--mode", "dispatch", "--workers", "1",
            "--models", "model-a", "--tasks", "task-x", "--seeds", "42",
            "--subset_file", str(bad_subset),
            "--output-root", str(base),
            "--registry-dir", str(registry_dir),
        ], spawner=make_child_spawner(calls))
    message = str(excinfo.value)
    assert "--subset_file" in message
    assert "not in datasets registry" in message
    assert not calls
    assert not base.exists(), "refused before the root was touched"

    good_subset = tmp_path / "subset-good.json"
    good_subset.write_text(
        json.dumps({"task-x": [1, 2]}), encoding="utf-8")
    good_base = (tmp_path / "finetuned-good").resolve()
    run_cli(monkeypatch, [
        "--mode", "dispatch", "--workers", "1",
        "--models", "model-a", "--tasks", "task-x", "--seeds", "42",
        "--subset_file", str(good_subset),
        "--output-root", str(good_base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner(calls))
    assert len(calls) == 1, "a valid map threads through to the child"
    assert flag_value(calls[0]["argv"], "--subset_file") == str(
        good_subset), "the resolved absolute path rides the child argv"


# ===== the singleton lock + mode isolation =====


def test_dispatch_lock_live_pid_refuses_naming_holder(
        tmp_path, monkeypatch):
    """A pre-existing dispatcher lock naming a LIVE pid (this test
    process's own pid) refuses the launch loudly naming the pid, the
    recorded run_id, AND the lock path (T-13-02/T-13-03): exactly ONE
    dispatcher per root, ever."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    ledger_dir = dispatch_core.ledger_dir_for(base)
    ledger_dir.mkdir(parents=True)
    lock_path = ledger_dir / dispatch_core.DISPATCHER_LOCK_NAME
    lock_path.write_text(
        json.dumps({"pid": os.getpid(), "run_id": "alive-run",
                    "started_at": "2026-10-20T00:00:00+00:00"}),
        encoding="utf-8")
    calls = []
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--mode", "dispatch", "--workers", "1",
            "--models", "model-a", "--tasks", "task-x", "--seeds", "42",
            "--output-root", str(base),
            "--registry-dir", str(registry_dir),
        ], spawner=make_child_spawner(calls))
    message = str(excinfo.value)
    assert str(os.getpid()) in message, "the refusal names the live pid"
    assert "alive-run" in message, "the refusal names the holder run_id"
    assert str(lock_path) in message
    assert not calls


def test_static_launch_never_acquires_dispatch_lock(
        tmp_path, monkeypatch):
    """Mode isolation (Pitfall 3): the STATIC path never acquires any
    dispatch lock — a static fake launch leaves no dispatch_ledger and
    never writes the base root (the static N=1 pin)."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    calls = []
    run_cli(monkeypatch, [
        "--workers", "1", "--models", "model-a",
        "--tasks", "task-x", "--seeds", "42",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_fake_spawner(calls))
    assert len(calls) == 1, "the static run_sweep.py worker spawn"
    assert calls[0]["argv"][1].endswith("run_sweep.py")
    assert not base.exists(), (
        "the static launch mode writes ONLY frozen sibling roots"
    )
    assert not dispatch_core.ledger_dir_for(base).exists(), (
        "the static path acquires no dispatch lock / ledger"
    )


def test_dispatch_merge_combination_refused(tmp_path, monkeypatch):
    """A6 (locked): --mode dispatch + --merge on one command line is
    refused with the named problem BEFORE either mode runs (MGPU-06 —
    dispatch roots need no merge)."""
    base = (tmp_path / "finetuned").resolve()
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--mode", "dispatch", "--merge",
            "--workers", "1", "--output-root", str(base),
        ])
    message = str(excinfo.value)
    assert "dispatch" in message
    assert "no merge" in message


def test_mode_flag_visible_in_help():
    """The --help surface shows the --mode flag with both choices and
    English help (D13-05/D13-08/D-10)."""
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "pipeline" / "run_sweep_shard.py"), "--help"],
        capture_output=True, text=True, check=True, timeout=120)
    assert "--mode" in result.stdout
    assert "static" in result.stdout
    assert "dispatch" in result.stdout


def test_mode_static_explicit_matches_default(tmp_path, monkeypatch):
    """Pattern-1 byte-identity pin: an explicit --mode static launch
    behaves identically to the default (same worker argv modulo the root
    substitution, same spawn discipline)."""
    registry_dir = make_registry(tmp_path)
    base_default = (tmp_path / "finetuned-default").resolve()
    base_explicit = (tmp_path / "finetuned-explicit").resolve()
    clock = lambda: datetime(2026, 10, 20, 5, 0, 0, tzinfo=UTC)
    calls_default = []
    calls_explicit = []
    common = [
        "--workers", "1", "--models", "model-a",
        "--tasks", "task-x", "--seeds", "42",
        "--registry-dir", str(registry_dir),
    ]
    run_cli(monkeypatch, ["--output-root", str(base_default), *common],
            spawner=make_fake_spawner(calls_default), clock=clock)
    run_cli(monkeypatch, [
        "--mode", "static", "--output-root", str(base_explicit), *common],
        spawner=make_fake_spawner(calls_explicit), clock=clock)

    def normalized(call, root):
        argv = [element.replace(root, "ROOT")
                for element in call["argv"]]
        kwargs = dict(call["kwargs"])
        kwargs["stdout"] = Path(kwargs["stdout"].name.replace(root, "ROOT"))
        return {"argv": argv, "kwargs": kwargs}

    assert [normalized(c, str(base_default)) for c in calls_default] == [
        normalized(c, str(base_explicit)) for c in calls_explicit], (
        "explicit --mode static is byte-identical to the default launch"
    )


# ===== frozen naming: claim filenames + worker logs =====


def test_claim_filename_deterministic_and_injective():
    """claim_filename is deterministic and injective over the tricky
    tuple set: + aliases, __ task keys, float fractions, and a
    deliberately ---containing name pair whose naive field join would
    collide (Pitfall 5 — the digest suffix guarantees injectivity)."""
    tricky = [
        ("model-a", "GUE__emp_H3", 42),
        ("model-a+lora", "GUE__emp_H3", 42),
        ("model-a", "GUE__emp_H3", 43),
        ("model-a", "GUE__emp_H3", 42, 0.25),
        ("model-a", "GUE__emp_H3", 42, 0.5),
        ("m--x", "t", 1),
        ("m", "x--t", 1),
        ("m", "t", 1),
    ]
    names = [dispatch_core.claim_filename(cell) for cell in tricky]
    assert len(set(names)) == len(tricky), (
        "distinct tuples must map to distinct claim filenames"
    )
    for cell, name in zip(tricky, names):
        assert dispatch_core.claim_filename(cell) == name, (
            "claim naming is deterministic"
        )
    base_name = dispatch_core.claim_filename(tricky[0])
    assert base_name.startswith("model-a--GUE__emp_H3--seed42-")
    digest = base_name[: -len(".json")].rsplit("-", 1)[1]
    assert len(digest) == 12
    assert all(char in "0123456789abcdef" for char in digest)
    alias_name = dispatch_core.claim_filename(tricky[1])
    assert alias_name.startswith("model-a%2Blora--"), (
        "the + alias percent-encodes (safe set empty)"
    )
    frac_name = dispatch_core.claim_filename(tricky[3])
    assert "--frac0.25-" in frac_name, "the fraction rides its own field"


def test_claim_json_agrees_with_filename(tmp_path):
    """Each claim file's JSON cell key agrees with its filename's
    encoded fields — the ledger is self-describing (Pitfall 5 warning
    sign pinned as a test)."""
    ledger = tmp_path / "ledger"
    ledger.mkdir()
    for cell in [("model-a+lora", "GUE__emp_H3", 42),
                 ("model-a", "GUE__emp_H3", 42, 0.5)]:
        payload = dispatch_core._claim_payload(
            cell, {"peft": "lora"}, "0", "run-x",
            "2026-10-20T00:00:00+00:00")
        path = dispatch_core.claim_cell(ledger, cell, payload)
        assert path is not None
        head = path.name[: -len(".json")].rsplit("-", 1)[0]
        fields = head.split("--")
        assert [unquote(field) for field in fields[:2]] == [
            cell[0], cell[1]]
        assert fields[2] == f"seed{cell[2]}"
        if len(cell) > 3:
            assert fields[3] == f"frac{cell[3]}"
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        assert on_disk["cell"] == dispatch_core._cell_key(cell)


def test_dispatch_worker_log_and_ledger_naming_is_frozen(tmp_path):
    """The dispatch naming authorities are frozen (the worker_root
    discipline): the tee log is {base}-dispatch-w{i}-{stamp}.log, a
    SIBLING of the shared root, distinct from the static -mgpu-w naming;
    the ledger dir is {root}/dispatch_ledger."""
    base = tmp_path / "finetuned"
    assert dispatch_core.dispatch_worker_log_path(
        base, 0, "20261020_040000") == (
        tmp_path / "finetuned-dispatch-w0-20261020_040000.log")
    assert dispatch_core.dispatch_worker_log_path(
        base, 12, "20261020_040500") == (
        tmp_path / "finetuned-dispatch-w12-20261020_040500.log")
    assert dispatch_core.ledger_dir_for(base) == (
        base / "dispatch_ledger")
    assert dispatch_core.DISPATCH_STATE_NAME == "dispatch_state.json"
    assert dispatch_core.DISPATCHER_LOCK_NAME == "dispatcher.lock"


# ===== SC3: the structural double-claim refusal =====


def test_claim_cell_double_claim_structurally_refused(tmp_path):
    """SC3: a second claim on a live-claimed cell returns the structural
    refusal (None) and the original claim is untouched — the O_EXCL
    create fails EEXIST regardless of the payload."""
    ledger = tmp_path / "ledger"
    ledger.mkdir()
    cell = ("model-a", "task-x", 42)
    first = dispatch_core.claim_cell(
        ledger, cell,
        dispatch_core._claim_payload(cell, {}, "0", "run-1", "t1"))
    assert first is not None
    second = dispatch_core.claim_cell(
        ledger, cell,
        dispatch_core._claim_payload(cell, {}, "1", "run-2", "t2"))
    assert second is None, "the live claim structurally refuses (SC3)"
    payload = json.loads(first.read_text(encoding="utf-8"))
    assert payload["run_id"] == "run-1", "the original claim is intact"


# ===== Task 2: resume semantics — skip filter, requeue, lock reclaim =====


def _write_hand_claim(ledger_dir, cell, state, run_id="hand-run"):
    """Hand-write one ledger claim fixture in the given state."""
    payload = dispatch_core._claim_payload(
        cell, {}, "7", run_id, "2026-10-20T00:00:00+00:00")
    payload["state"] = state
    path = ledger_dir / dispatch_core.claim_filename(cell)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _write_marker(base, cell):
    """Hand-write the trainer_state.json resume marker for one cell."""
    fraction = cell[3] if len(cell) > 3 else None
    cell_dir = run_sweep.cell_dir_for(
        base, cell[0], cell[1], cell[2], fraction)
    cell_dir.mkdir(parents=True, exist_ok=True)
    (cell_dir / run_sweep.RESUME_MARKER).write_text(
        '{"global_step": 9}', encoding="utf-8")
    return cell_dir


def test_sc2_kill_test_resume_exactly_once(tmp_path, monkeypatch):
    """SC2 (the P1 acceptance test): run 1 with one SIGKILLed cell (the
    fake child returns -9 and writes NO artifacts) drains with that cell
    failed and all others completed; the relaunch over the SAME root
    (killed cell now succeeding) spawns ONLY the killed cell; final
    state — every cell has exactly one final_metrics.json +
    trainer_state.json set, every claim completed, per-cell spawn counts
    are 1 for skip-cells and 2 for the killed cell (no duplicates, no
    orphans). Exactly-once is proven from evidence ON DISK (ledger +
    artifact counts + captured argvs), never from return codes alone."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    killed = ("model-b", "task-z", 43)
    argv = [
        "--mode", "dispatch", "--workers", "2",
        "--models", "model-a,model-b,model-c",
        "--tasks", "task-x,task-z", "--seeds", "42,43",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ]
    # run 1: the targeted cell's child dies by SIGKILL mid-cell
    calls1 = []
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, argv, spawner=make_child_spawner(
            calls1, exit_for={killed: -9}))
    assert excinfo.value.code == 1, "a run with a failed cell exits 1"
    assert len(calls1) == 12
    assert len(set(spawn_identities(calls1))) == 12, (
        "every cell spawned exactly once in run 1"
    )
    state1 = json.loads(
        (base / dispatch_core.DISPATCH_STATE_NAME).read_text(
            encoding="utf-8"))
    assert state1["counts"] == {
        "total": 12, "completed": 11, "failed": 1, "skipped": 0}
    killed_claim = (dispatch_core.ledger_dir_for(base)
                    / dispatch_core.claim_filename(killed))
    assert json.loads(
        killed_claim.read_text(encoding="utf-8"))["state"] == "failed"
    assert not (dispatch_core.ledger_dir_for(base)
                / dispatch_core.DISPATCHER_LOCK_NAME).exists(), (
        "the lock is released even on the failed-exit drain"
    )
    run1_run_id = state1["run_id"]

    # run 2 (relaunch, same root): the killed cell now succeeds — the
    # marker/ledger skip set covers every completed cell, and ONLY the
    # killed cell (stale failed claim -> requeue) re-dispatches
    calls2 = []
    run_cli(monkeypatch, argv, spawner=make_child_spawner(calls2))
    assert spawn_identities(calls2) == [killed], (
        "the relaunch re-dispatches EXACTLY the killed cell"
    )
    state2 = json.loads(
        (base / dispatch_core.DISPATCH_STATE_NAME).read_text(
            encoding="utf-8"))
    assert state2["counts"] == {
        "total": 12, "completed": 1, "failed": 0, "skipped": 11}
    assert state2["run_id"] != run1_run_id, "a fresh run id per launch"

    # exactly-once evidence on disk: every cell has EXACTLY one artifact
    # set under its cell_dir_for path
    expected = run_sweep.enumerate_matrix(
        ["model-a", "model-b", "model-c"], ["task-x", "task-z"],
        [42, 43], registry_dir)
    for model, task, seed in expected:
        cell_dir = run_sweep.cell_dir_for(base, model, task, seed)
        assert (cell_dir / run_sweep.METRICS_NAME).is_file()
        assert (cell_dir / run_sweep.RESUME_MARKER).is_file()
    assert len(list(base.rglob(run_sweep.METRICS_NAME))) == 12, (
        "no duplicate artifact sets anywhere in the root"
    )
    # every claim completed, ONE claim file per cell (no orphans)
    ledger_dir = dispatch_core.ledger_dir_for(base)
    claims = sorted(
        path for path in ledger_dir.glob("*.json")
        if path.name != dispatch_core.DISPATCHER_LOCK_NAME)
    assert len(claims) == 12
    for claim_path in claims:
        payload = json.loads(claim_path.read_text(encoding="utf-8"))
        assert payload["state"] == "completed"
    # the requeued claim carries the NEW run's identity
    revived = json.loads(killed_claim.read_text(encoding="utf-8"))
    assert revived["run_id"] == state2["run_id"]
    assert not list(ledger_dir.glob("*.tmp")), "no atomic-write residue"

    # per-cell spawn counts: 1 everywhere except the killed cell (2)
    all_identities = spawn_identities(calls1) + spawn_identities(calls2)
    for cell in expected:
        expected_count = 2 if tuple(cell) == killed else 1
        assert all_identities.count(tuple(cell)) == expected_count, (
            f"cell {cell} spawned exactly {expected_count} time(s)"
        )


def test_skip_filter_marker_and_claim_layers(tmp_path, monkeypatch):
    """The two-layer skip: a cell with trainer_state.json in its cell dir
    is skipped (marker AUTHORITATIVE, D-06) even with no claim; a cell
    whose claim state is completed is skipped even with no marker; a
    failed claim requeues (MGPU-02 resume semantics)."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    ledger_dir = dispatch_core.ledger_dir_for(base)
    ledger_dir.mkdir(parents=True)
    _write_marker(base, ("model-a", "task-x", 42))  # marker, no claim
    _write_hand_claim(  # completed claim, no marker
        ledger_dir, ("model-a", "task-x", 43),
        dispatch_core.CLAIM_STATE_COMPLETED)
    _write_hand_claim(  # failed claim -> requeue
        ledger_dir, ("model-a", "task-x", 44),
        dispatch_core.CLAIM_STATE_FAILED)
    calls = []
    run_cli(monkeypatch, [
        "--mode", "dispatch", "--workers", "1",
        "--models", "model-a", "--tasks", "task-x", "--seeds", "42,43,44",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner(calls))
    assert spawn_identities(calls) == [("model-a", "task-x", 44)], (
        "only the failed-claim cell requeues; both skip layers hold"
    )
    state = json.loads(
        (base / dispatch_core.DISPATCH_STATE_NAME).read_text(
            encoding="utf-8"))
    assert state["counts"] == {
        "total": 3, "completed": 1, "failed": 0, "skipped": 2}


def test_requeued_claim_atomically_replaced_with_new_identity(
        tmp_path, monkeypatch):
    """A requeued cell's stale claim is atomically REPLACED at re-claim,
    carrying the new run_id / gpu / timestamps; fresh cells keep the
    strict O_EXCL path; no tmp residue lands in the ledger."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    ledger_dir = dispatch_core.ledger_dir_for(base)
    ledger_dir.mkdir(parents=True)
    cell = ("model-a", "task-x", 42)
    stale = _write_hand_claim(
        ledger_dir, cell, dispatch_core.CLAIM_STATE_CLAIMED,
        run_id="dead-run")
    assert json.loads(stale.read_text(encoding="utf-8"))["run_id"] == (
        "dead-run")
    calls = []
    run_cli(monkeypatch, [
        "--mode", "dispatch", "--workers", "1", "--gpus", "5",
        "--models", "model-a", "--tasks", "task-x", "--seeds", "42",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner(calls))
    assert len(calls) == 1
    state = json.loads(
        (base / dispatch_core.DISPATCH_STATE_NAME).read_text(
            encoding="utf-8"))
    revived = json.loads(stale.read_text(encoding="utf-8"))
    assert revived["run_id"] == state["run_id"], (
        "the replaced claim carries THIS run's id"
    )
    assert revived["gpu"] == "5"
    assert revived["claimed_at"]
    assert revived["state"] == "completed"
    assert not list(ledger_dir.glob("*.tmp")), (
        "the replace left no tmp residue (atomic tmp + os.replace)"
    )


def test_lock_dead_pid_is_reclaimed(tmp_path, monkeypatch):
    """A5: a lock naming a provably DEAD pid (a reaped real subprocess)
    is reclaimed — run_dispatch proceeds and the lock file then carries
    the new run's identity."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()  # reaped: the pid is provably dead
    ledger_dir = dispatch_core.ledger_dir_for(base)
    ledger_dir.mkdir(parents=True)
    lock_path = ledger_dir / dispatch_core.DISPATCHER_LOCK_NAME
    lock_path.write_text(
        json.dumps({"pid": dead.pid, "run_id": "dead-run",
                    "started_at": "2026-10-20T00:00:00+00:00"}),
        encoding="utf-8")
    calls = []
    run_cli(monkeypatch, [
        "--mode", "dispatch", "--workers", "1",
        "--models", "model-a", "--tasks", "task-x", "--seeds", "42",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner(calls))
    assert len(calls) == 1, "the dead-pid lock is reclaimed, run proceeds"
    state = json.loads(
        (base / dispatch_core.DISPATCH_STATE_NAME).read_text(
            encoding="utf-8"))
    assert state["counts"]["completed"] == 1
    assert not lock_path.exists(), "released after the drain"


def test_lock_malformed_content_is_reclaimed(tmp_path, monkeypatch):
    """A5: a malformed/unreadable lock cannot name a live holder — the
    run reclaims it by atomic overwrite and proceeds. The lock's mtime
    is BACKDATED past the create-to-write grace window (CR-02): a
    malformed lock from a dead run is old by definition, while a FRESH
    unwritten lock is an in-flight writer and refuses (see below)."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    ledger_dir = dispatch_core.ledger_dir_for(base)
    ledger_dir.mkdir(parents=True)
    lock_path = ledger_dir / dispatch_core.DISPATCHER_LOCK_NAME
    lock_path.write_text("not json at all {", encoding="utf-8")
    stale = time.time() - (
        dispatch_core._LOCK_WRITE_GRACE_SECONDS + 60.0)
    os.utime(lock_path, (stale, stale))
    calls = []
    run_cli(monkeypatch, [
        "--mode", "dispatch", "--workers", "1",
        "--models", "model-a", "--tasks", "task-x", "--seeds", "42",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner(calls))
    assert len(calls) == 1


def test_lock_empty_fresh_window_refuses_inflight_writer(
        tmp_path, monkeypatch):
    """CR-02 pin: an EMPTY lock file with a FRESH mtime is treated as an
    in-flight writer inside the create-to-write window — the launch
    refuses loudly instead of reclaiming (reclaiming there would put TWO
    dispatchers on one root, defeating the singleton guarantee)."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    ledger_dir = dispatch_core.ledger_dir_for(base)
    ledger_dir.mkdir(parents=True)
    lock_path = ledger_dir / dispatch_core.DISPATCHER_LOCK_NAME
    lock_path.write_text("", encoding="utf-8")  # fresh mtime: just written
    calls = []
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--mode", "dispatch", "--workers", "1",
            "--models", "model-a", "--tasks", "task-x", "--seeds", "42",
            "--output-root", str(base),
            "--registry-dir", str(registry_dir),
        ], spawner=make_child_spawner(calls))
    message = str(excinfo.value)
    assert str(lock_path) in message
    assert "no holder" in message
    assert "retry" in message, "the refusal tells the operator to retry"
    assert not calls, "no child spawns while the window is unresolved"
    assert lock_path.read_text(encoding="utf-8") == "", (
        "the possibly-in-flight lock is left untouched (never reclaimed)"
    )


def test_lock_empty_stale_window_is_reclaimed(tmp_path, monkeypatch):
    """CR-02 pin: an EMPTY lock older than the grace window is a provably
    dead writer (crashed between create and write) — reclaimed and the
    run proceeds."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    ledger_dir = dispatch_core.ledger_dir_for(base)
    ledger_dir.mkdir(parents=True)
    lock_path = ledger_dir / dispatch_core.DISPATCHER_LOCK_NAME
    lock_path.write_text("", encoding="utf-8")
    stale = time.time() - (
        dispatch_core._LOCK_WRITE_GRACE_SECONDS + 60.0)
    os.utime(lock_path, (stale, stale))
    calls = []
    run_cli(monkeypatch, [
        "--mode", "dispatch", "--workers", "1",
        "--models", "model-a", "--tasks", "task-x", "--seeds", "42",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner(calls))
    assert len(calls) == 1, "the expired empty lock is reclaimed"


def test_lock_out_of_range_pid_reclaimed_not_crashed(
        tmp_path, monkeypatch):
    """WR-02 pin: a parseable lock whose pid is out of signal range
    (2**63) is reclaimed — never an unhandled OverflowError traceback on
    the recovery path (an impossible pid is provably not a live holder)."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    ledger_dir = dispatch_core.ledger_dir_for(base)
    ledger_dir.mkdir(parents=True)
    (ledger_dir / dispatch_core.DISPATCHER_LOCK_NAME).write_text(
        json.dumps({"pid": 2**63, "run_id": "corrupt-run",
                    "started_at": "2026-10-20T00:00:00+00:00"}),
        encoding="utf-8")
    calls = []
    run_cli(monkeypatch, [
        "--mode", "dispatch", "--workers", "1",
        "--models", "model-a", "--tasks", "task-x", "--seeds", "42",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner(calls))
    assert len(calls) == 1, (
        "the impossible pid reclaims (no OverflowError crash) and the "
        "run proceeds"
    )
    state = json.loads(
        (base / dispatch_core.DISPATCH_STATE_NAME).read_text(
            encoding="utf-8"))
    assert state["counts"]["completed"] == 1


def test_skip_set_is_order_independent(tmp_path):
    """EDGE MGPU-02/ordering: the relaunch skip set is a pure function
    of per-cell (marker presence, claim state) — the SAME ledger/marker
    state built in two DIFFERENT creation orders yields the identical
    skip/requeue decision set."""
    cells = [
        ("model-a", "task-x", 42),
        ("model-a", "task-x", 43),
        ("model-b", "task-x", 42),
        ("model-b", "task-x", 43),
        ("model-c", "task-x", 42),
    ]

    def build(root_name, reversed_order):
        root = (tmp_path / root_name).resolve()
        ledger_dir = dispatch_core.ledger_dir_for(root)
        writes = [
            lambda: _write_marker(root, ("model-a", "task-x", 42)),
            lambda: _write_hand_claim(
                ledger_dir, ("model-a", "task-x", 42),
                dispatch_core.CLAIM_STATE_COMPLETED),
            lambda: _write_hand_claim(
                ledger_dir, ("model-a", "task-x", 43),
                dispatch_core.CLAIM_STATE_FAILED),
            lambda: _write_hand_claim(
                ledger_dir, ("model-b", "task-x", 43),
                dispatch_core.CLAIM_STATE_CLAIMED),
            lambda: _write_marker(root, ("model-c", "task-x", 42)),
        ]
        if reversed_order:
            writes.reverse()  # same final state, opposite creation order
        for write in writes:
            write()
        return [
            dispatch_core.relaunch_decision(root, ledger_dir, cell)
            for cell in cells]

    forward = build("r-order-1", reversed_order=False)
    backward = build("r-order-2", reversed_order=True)
    assert forward == backward, (
        "the same ledger state in any creation order yields the "
        "identical per-cell skip/requeue decisions"
    )
    assert forward == [
        "skip", "requeue", "fresh", "requeue", "skip"]


def test_drained_root_relaunch_is_nothing_to_do(
        tmp_path, monkeypatch, capsys):
    """EDGE MGPU-02/empty: a relaunch over a fully completed root queues
    ZERO cells, prints the explicit nothing-to-do verdict, spawns
    nothing, and exits 0."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    argv = [
        "--mode", "dispatch", "--workers", "2",
        "--models", "model-a,model-b",
        "--tasks", "task-x", "--seeds", "42,43",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ]
    calls1 = []
    run_cli(monkeypatch, argv, spawner=make_child_spawner(calls1))
    assert len(calls1) == 4
    calls2 = []
    run_cli(monkeypatch, argv, spawner=make_child_spawner(calls2))
    assert calls2 == [], "a fully drained root spawns nothing"
    out = capsys.readouterr().out
    assert "nothing to do" in out
    state = json.loads(
        (base / dispatch_core.DISPATCH_STATE_NAME).read_text(
            encoding="utf-8"))
    assert state["status"] == "done"
    assert state["counts"] == {
        "total": 4, "completed": 0, "failed": 0, "skipped": 4}


def test_malformed_claims_requeue_never_crash_never_skip(
        tmp_path, monkeypatch):
    """Malformed-claim tolerance: a claim whose JSON does not parse, and
        one whose cell key disagrees with the pending cell, are both
        treated as STALE claims (requeue) — never a crash, never a
        silent skip."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    ledger_dir = dispatch_core.ledger_dir_for(base)
    ledger_dir.mkdir(parents=True)
    broken = ledger_dir / dispatch_core.claim_filename(
        ("model-a", "task-x", 42))
    broken.write_text("{ torn json", encoding="utf-8")
    disagreeing = dispatch_core._claim_payload(
        ("OTHER-model", "task-x", 42), {}, "0", "other-run", "t")
    (ledger_dir / dispatch_core.claim_filename(
        ("model-a", "task-x", 43))).write_text(
        json.dumps(disagreeing), encoding="utf-8")
    calls = []
    run_cli(monkeypatch, [
        "--mode", "dispatch", "--workers", "1",
        "--models", "model-a", "--tasks", "task-x", "--seeds", "42,43,44",
        "--output-root", str(base),
        "--registry-dir", str(registry_dir),
    ], spawner=make_child_spawner(calls))
    assert sorted(spawn_identities(calls)) == [
        ("model-a", "task-x", 42),
        ("model-a", "task-x", 43),
        ("model-a", "task-x", 44),
    ], "malformed and cell-key-disagreeing claims both requeue"
    state = json.loads(
        (base / dispatch_core.DISPATCH_STATE_NAME).read_text(
            encoding="utf-8"))
    assert state["counts"] == {
        "total": 3, "completed": 3, "failed": 0, "skipped": 0}


# ===== worker-thread containment + honest accounting (CR-04) =====


def _flaky_finalize(monkeypatch, fail_first_n):
    """Patch ``dispatch_core.finalize_claim`` to raise ENOSPC on the
    first ``fail_first_n`` calls — an exception from a worker thread
    OUTSIDE the spawn seam, exactly the failure class the CR-04
    containment boundary exists for."""
    real = dispatch_core.finalize_claim
    calls = [0]

    def patched(claim_path, payload):
        calls[0] += 1
        if calls[0] <= fail_first_n:
            raise OSError(28, "No space left on device")
        real(claim_path, payload)

    monkeypatch.setattr(dispatch_core, "finalize_claim", patched)


def _worker_state_writes_always_fail(monkeypatch):
    """Patch ``dispatch_core._write_state`` to raise ENOSPC on every
    WORKER-thread call (main-thread writes succeed, so the accounting
    write itself lands and its honesty is assertable)."""
    real = dispatch_core._write_state

    def patched(state_path, state):
        if threading.current_thread() is not threading.main_thread():
            raise OSError(28, "No space left on device")
        real(state_path, state)

    monkeypatch.setattr(dispatch_core, "_write_state", patched)


def test_worker_finalize_failure_fails_cell_not_run(
        tmp_path, monkeypatch):
    """CR-04 pin (containment): an exception from a worker thread
    OUTSIDE the spawn seam (here: ENOSPC on the first finalize) fails
    THAT cell and the drain CONTINUES — all 4 cells still spawn, the
    stricken cell is recorded with a dispatcher-side failure, and the
    run exits 1 on the failed count. Never a silent queue drop behind a
    false success."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    _flaky_finalize(monkeypatch, fail_first_n=1)
    calls = []
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--mode", "dispatch", "--workers", "1",
            "--models", "model-a,model-b", "--tasks", "task-x",
            "--seeds", "42,43",
            "--output-root", str(base),
            "--registry-dir", str(registry_dir),
        ], spawner=make_child_spawner(calls))
    assert excinfo.value.code == 1, "the failed cell drives the exit-1 path"
    assert len(calls) == 4, (
        "every cell still spawns — the drain continues past the failure"
    )
    state = json.loads(
        (base / dispatch_core.DISPATCH_STATE_NAME).read_text(
            encoding="utf-8"))
    assert state["counts"] == {
        "total": 4, "completed": 3, "failed": 1, "skipped": 0}, (
        "honest accounting: the stricken cell is FAILED, not dropped"
    )
    failed_errors = [
        json.loads(path.read_text(encoding="utf-8"))["error"]
        for path in dispatch_core.ledger_dir_for(base).glob("*.json")
        if path.name != dispatch_core.DISPATCHER_LOCK_NAME
        and json.loads(path.read_text(encoding="utf-8"))["state"]
        == dispatch_core.CLAIM_STATE_FAILED]
    expected_error = (
        "dispatcher-side failure: OSError: [Errno 28] No space left "
        "on device")
    assert failed_errors == [expected_error], (
        "the claim records the dispatcher-side failure by name"
    )


@pytest.mark.filterwarnings(
    "ignore::pytest.PytestUnhandledThreadExceptionWarning")
def test_worker_death_drains_loudly_incomplete(tmp_path, monkeypatch):
    """CR-04 pin (accounting assertion): when the containment boundary
    ITSELF dies (here: finalize always fails AND every worker state
    write fails, so the containment's own accounting write raises), the
    run NEVER reports done/exit 0 — the post-join assertion writes an
    honest status 'incomplete' and refuses by name with the
    drained/total counts."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    _flaky_finalize(monkeypatch, fail_first_n=10**9)  # always fail
    _worker_state_writes_always_fail(monkeypatch)
    calls = []
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--mode", "dispatch", "--workers", "1",
            "--models", "model-a,model-b", "--tasks", "task-x",
            "--seeds", "42,43",
            "--output-root", str(base),
            "--registry-dir", str(registry_dir),
        ], spawner=make_child_spawner(calls))
    message = str(excinfo.value)
    assert "accounting mismatch" in message
    assert "1/4" in message, "the refusal names the drained/total counts"
    assert len(calls) == 1, "only the first cell spawned before the death"
    state = json.loads(
        (base / dispatch_core.DISPATCH_STATE_NAME).read_text(
            encoding="utf-8"))
    assert state["status"] == "incomplete", (
        "never 'done' — the state tells the truth about the drain"
    )
    assert not (dispatch_core.ledger_dir_for(base)
                / dispatch_core.DISPATCHER_LOCK_NAME).exists(), (
        "the lock is still released on the refused drain"
    )


# ===== 13-02 Task 2: mode coexistence — merge refusal + static pins =====


def _write_static_worker(root, model, task="task-x", seed=42):
    """One static-style worker root fixture: a manifest + failures file
    in the run_sweep payload shape plus one cell's allowlisted
    artifacts (the merge-happy-path/control idiom, local copy)."""
    root.mkdir(parents=True, exist_ok=True)
    cell_dir = run_sweep.cell_dir_for(root, model, task, seed)
    cell_dir.mkdir(parents=True, exist_ok=True)
    (cell_dir / run_sweep.METRICS_NAME).write_text(
        json.dumps({"eval_loss": 0.5}), encoding="utf-8")
    (cell_dir / run_sweep.RESUME_MARKER).write_text(
        '{"global_step": 1}', encoding="utf-8")
    payload = {
        "matrix": {
            "models": [model], "tasks": [task], "seeds": [seed],
            "output_root": str(root),
        },
        "cells": [{
            "model": model, "task": task, "seed": seed,
            "status": "completed", "output_dir": str(cell_dir),
        }],
    }
    (root / run_sweep.MANIFEST_NAME).write_text(
        json.dumps(payload), encoding="utf-8")
    (root / run_sweep.FAILURES_NAME).write_text("[]", encoding="utf-8")
    return root


def test_root_has_dispatch_evidence_marker_matrix(tmp_path):
    """The evidence helper reads ONLY the three run-recorded markers:
    each alone triggers; a bare static root (manifest without the
    marker, no manifest at all, an absent root, or an unreadable
    manifest) carries no evidence — that absence IS the static world
    (MGPU-06 / D13-07, never directory-shape inference)."""
    helper = run_sweep_shard._root_has_dispatch_evidence

    static_root = _write_static_worker(tmp_path / "static", "model-a")
    assert helper(static_root) is False

    empty_root = tmp_path / "empty"
    empty_root.mkdir()
    assert helper(empty_root) is False
    assert helper(tmp_path / "absent") is False

    state_root = tmp_path / "state"
    state_root.mkdir()
    (state_root / dispatch_core.DISPATCH_STATE_NAME).write_text(
        "{}", encoding="utf-8")
    assert helper(state_root) is True

    ledger_root = tmp_path / "ledger-only"
    dispatch_core.ledger_dir_for(ledger_root).mkdir(parents=True)
    assert helper(ledger_root) is True

    marker_root = _write_static_worker(tmp_path / "marker", "model-a")
    manifest = json.loads(
        (marker_root / run_sweep.MANIFEST_NAME).read_text(
            encoding="utf-8"))
    manifest["cells"][0]["orchestrator_mode"] = "dispatch"
    (marker_root / run_sweep.MANIFEST_NAME).write_text(
        json.dumps(manifest), encoding="utf-8")
    assert helper(marker_root) is True

    corrupt_root = tmp_path / "corrupt"
    corrupt_root.mkdir()
    (corrupt_root / run_sweep.MANIFEST_NAME).write_text(
        "{ torn", encoding="utf-8")
    assert helper(corrupt_root) is False, (
        "an unreadable manifest carries no marker"
    )


def test_merge_refuses_dispatch_state_evidence_at_base(
        tmp_path, monkeypatch):
    """MGPU-06 mixed-mode refusal: a static-style worker pair with
    dispatch_state.json planted at the BASE root refuses with the named
    problem and NO file is copied (the base still holds only the
    evidence file — the refusal lands before the copy pass)."""
    base = (tmp_path / "finetuned").resolve()
    _write_static_worker(run_sweep_shard.worker_root(base, 0), "model-a")
    _write_static_worker(run_sweep_shard.worker_root(base, 1), "model-b")
    base.mkdir(parents=True, exist_ok=True)
    (base / dispatch_core.DISPATCH_STATE_NAME).write_text(
        "{}", encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--merge", "--workers", "2", "--output-root", str(base)])
    message = str(excinfo.value)
    assert f"dispatch root {base} needs no merge" in message
    assert "ONE shared root" in message
    assert sorted(path.name for path in base.iterdir()) == [
        dispatch_core.DISPATCH_STATE_NAME], (
        "refused BEFORE any copy — no merged manifest, no cell files"
    )


def test_merge_refuses_worker_root_ledger_evidence(tmp_path, monkeypatch):
    """The refusal fires for evidence on a DISCOVERED WORKER ROOT too
    (the dispatch_ledger dir marker): the merge names that root and
    never creates the merged root."""
    base = (tmp_path / "finetuned").resolve()
    _write_static_worker(run_sweep_shard.worker_root(base, 0), "model-a")
    w1 = _write_static_worker(
        run_sweep_shard.worker_root(base, 1), "model-b")
    dispatch_core.ledger_dir_for(w1).mkdir()  # evidence on the worker
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--merge", "--workers", "2", "--output-root", str(base)])
    assert f"dispatch root {w1} needs no merge" in str(excinfo.value)
    assert not base.exists(), "the merged root is never created"


def test_merge_refuses_dry_run_marker_only_evidence(tmp_path, monkeypatch):
    """A root whose ONLY evidence is the manifest orchestrator_mode
    marker (exactly what a dispatch dry-run root carries) refuses the
    same named way — the plan artifact is dispatch evidence."""
    base = (tmp_path / "finetuned").resolve()
    w0 = _write_static_worker(run_sweep_shard.worker_root(base, 0),
                              "model-a")
    _write_static_worker(run_sweep_shard.worker_root(base, 1), "model-b")
    manifest = json.loads(
        (w0 / run_sweep.MANIFEST_NAME).read_text(encoding="utf-8"))
    manifest["cells"][0]["orchestrator_mode"] = "dispatch"
    (w0 / run_sweep.MANIFEST_NAME).write_text(
        json.dumps(manifest), encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--merge", "--workers", "2", "--output-root", str(base)])
    assert f"dispatch root {w0} needs no merge" in str(excinfo.value)
    assert not base.exists()


def test_static_mode_explicit_pins_argv_roots_and_logs(
        tmp_path, monkeypatch):
    """EDGE MGPU-06/empty full pin: an explicit --mode static launch
    produces the identical captured argv list (worker roots included),
    identical spawn kwargs, and identical tee log file names as the
    same launch without --mode; the base root is never written either
    way (static writes ONLY frozen sibling roots)."""
    registry_dir = make_registry(tmp_path)
    clock = lambda: datetime(2026, 10, 20, 6, 0, 0, tzinfo=UTC)
    stamp = "20261020_060000"
    captured = {}
    for label, extra in (("default", []), ("explicit",
                                           ["--mode", "static"])):
        base = (tmp_path / f"finetuned-{label}").resolve()
        calls = []
        run_cli(monkeypatch, [
            *extra,
            "--workers", "2", "--models", "model-a,model-b",
            "--tasks", "task-x", "--seeds", "42",
            "--output-root", str(base),
            "--registry-dir", str(registry_dir),
        ], spawner=make_fake_spawner(calls), clock=clock)
        captured[label] = (base, calls)

    def normalized(call, root):
        argv = [element.replace(root, "ROOT") for element in call["argv"]]
        kwargs = dict(call["kwargs"])
        kwargs["stdout"] = Path(
            kwargs["stdout"].name.replace(root, "ROOT"))
        return {"argv": argv, "kwargs": kwargs}

    base_default, calls_default = captured["default"]
    base_explicit, calls_explicit = captured["explicit"]
    assert [normalized(c, str(base_default)) for c in calls_default] == [
        normalized(c, str(base_explicit)) for c in calls_explicit], (
        "explicit --mode static is byte-identical to the default launch"
    )
    for i in (0, 1):
        argv_root = flag_value(calls_default[i]["argv"], "--output-root")
        assert argv_root == str(
            run_sweep_shard.worker_root(base_default, i)), (
            "the worker ROOT rides the argv via the frozen naming"
        )
        log_default = run_sweep_shard.worker_log_path(
            base_default, i, stamp)
        log_explicit = run_sweep_shard.worker_log_path(
            base_explicit, i, stamp)
        assert log_default.is_file() and log_explicit.is_file(), (
            "both launches tee their worker logs (WR-02)"
        )
        assert log_default.name.replace(
            base_default.name, "ROOT") == log_explicit.name.replace(
            base_explicit.name, "ROOT"), (
            "identical tee log names modulo the launch dir (the log is "
            "a SIBLING of the base root, so its name embeds it by design)"
        )
    assert not base_default.exists() and not base_explicit.exists(), (
        "static mode never writes the base root (either spelling)"
    )


def test_dispatch_merge_combo_refusal_reasserted(tmp_path, monkeypatch):
    """EDGE MGPU-06/ordering adjacency: --mode dispatch combined with
    --merge on one command line refuses with the 13-01 named problem
    BEFORE any root is written."""
    base = (tmp_path / "finetuned").resolve()
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--mode", "dispatch", "--merge", "--workers", "1",
            "--output-root", str(base),
        ])
    message = str(excinfo.value)
    assert "--mode dispatch cannot combine with --merge" in message
    assert "need no merge" in message
    assert not base.exists()


def test_merge_happy_path_control_without_evidence(tmp_path, monkeypatch):
    """Control: a static-only root set (zero dispatch evidence) merges
    exactly as before — the merged manifest lands with the union cells
    and both cells' allowlisted files copy under the merged root (the
    no-evidence behavior is untouched)."""
    base = (tmp_path / "finetuned").resolve()
    _write_static_worker(run_sweep_shard.worker_root(base, 0), "model-a")
    _write_static_worker(run_sweep_shard.worker_root(base, 1), "model-b")
    run_cli(monkeypatch, [
        "--merge", "--workers", "2", "--output-root", str(base)])
    manifest = json.loads(
        (base / run_sweep.MANIFEST_NAME).read_text(encoding="utf-8"))
    assert sorted(cell["model"] for cell in manifest["cells"]) == [
        "model-a", "model-b"]
    for model in ("model-a", "model-b"):
        cell_dir = run_sweep.cell_dir_for(base, model, "task-x", 42)
        assert (cell_dir / run_sweep.METRICS_NAME).is_file()
        assert (cell_dir / run_sweep.RESUME_MARKER).is_file()
