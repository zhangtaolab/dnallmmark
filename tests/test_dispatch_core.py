"""
Unit tests for ``pipeline/dispatch_core.py`` + the ``--mode`` surface
(13-01, MGPU-01/MGPU-02).

Coverage named by the plan (SC ids are the phase acceptance tests):

- **SC3 (double-claim is structurally refused)** — ``claim_cell`` on a
  live-claimed cell returns None (the O_EXCL ``EEXIST``), the original
  claim is untouched, and within one run no second child is ever spawned
  for one cell.
- **SC2 (kill-proven resume)** — landed with Task 2 (the skip filter +
  the two-run kill test over one shared root).
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

import json
import subprocess
import sys
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


# ===== the singleton lock + mode isolation =====


def test_dispatch_lock_held_refuses_loudly(tmp_path, monkeypatch):
    """A pre-existing dispatcher lock refuses the launch loudly naming
    the lock path (T-13-02): exactly ONE dispatcher per root, ever."""
    registry_dir = make_registry(tmp_path)
    base = (tmp_path / "finetuned").resolve()
    ledger_dir = dispatch_core.ledger_dir_for(base)
    ledger_dir.mkdir(parents=True)
    lock_path = ledger_dir / dispatch_core.DISPATCHER_LOCK_NAME
    lock_path.write_text(
        json.dumps({"pid": 999999, "run_id": "other-run",
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
    assert str(lock_path) in str(excinfo.value)
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
