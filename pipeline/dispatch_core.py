"""
Dynamic dispatch engine: ONE dispatcher, per-GPU worker loops, ONE shared
root (13-01, MGPU-01/MGPU-02).

``run_sweep_shard.py`` static mode partitions MODELS once and runs N
``run_sweep.py`` workers under frozen ``{root}-mgpu-w{i}`` sibling roots.
This engine is the alternative ``--mode dispatch``: a SINGLE dispatcher
process owns a deterministic in-memory (model x task x seed[, fraction])
cell queue, and one thin worker loop per ``--workers`` entry — permanently
bound to one ``--gpus`` token — claims the next cell, spawns ONE
``run_finetune.py`` child for it, waits, records, and claims the next.
Every cell lands at the ordinary ``run_sweep.cell_dir_for`` path under the
ONE shared root (worker-independent cell outputs — no sibling roots, no
merge step, MGPU-02); per D-07 the orchestrator COMPOSES: enumeration,
priority order, argv building, cell layout, and every constant come from
``run_sweep`` imports, never re-implemented.

Usage (run from anywhere; each child's cwd is pinned internally to
``pipeline/`` — run_finetune's documented cwd contract)::

    python pipeline/run_sweep_shard.py --mode dispatch --workers 2 \\
        --gpus 0,1 --models plant-dnabert-6mer,GENERanno-eukaryote-0.5b-base \\
        --output-root ./finetuned --tasks GUE__emp_H3 --seeds 42,43

Strict protocol order (crash-safety contract — Pitfall 8 of the phase
research; every step's guard depends on the ones before it):

1. **VALIDATE + ENUMERATE** — the sweep-flag remainder re-parses through
   ``run_sweep.parse_args`` itself (run_sweep stays the single flag
   owner, D-07), the shard ``--models`` filter merges in, and the whole
   ``run_sweep.main`` startup validation family mirrors collect-all
   BEFORE anything touches the root. An ENUMERATED matrix of zero cells
   refuses by name BEFORE the lock is acquired (never a silent
   full-registry fallback — the WR-07 family).
2. **LOCK** — one singleton ``dispatcher.lock`` per root, created with
   ``os.open(O_CREAT | O_EXCL)``: a second dispatcher on a live-locked
   root is refused loudly; the singleton is what makes claim reclaim
   without leases sound (D13-11).
3. **MODE EVIDENCE** — ``dispatch_state.json`` is written at the root
   BEFORE any claim or spawn (atomic tmp+``os.replace``, single writer).
4. **SKIP FILTER** — on relaunch, a cell is skipped iff its child-side
   ``trainer_state.json`` marker exists (the authoritative completion
   guard, D-06) OR its ledger claim already says ``completed``; a stale
   claim (``claimed``/``failed`` from a dead run) is requeued — no
   lease, no timeout.
5. **CLAIM BEFORE SPAWN** — the per-cell claim file is created
   ``O_CREAT | O_EXCL`` in the ledger dir BEFORE the child exists, so a
   crash can never leave a spawned cell without a claim.
6. **FINALIZE AFTER ARTIFACT CHECK** — the child's exit 0 alone is NOT
   completion (CR-02: ``run_finetune.py``'s blind-except isolation
   swallows training failures at exit 0): a cell completes only when the
   child exited 0 AND ``final_metrics.json`` is present in its cell dir.
   Failed cells are recorded and NEVER requeued within the live run
   (decision A2 — Phase 14's MGPU-04 owns re-run).

Orphan-children relaunch caveat (decision A5): children spawn with
``start_new_session=True``, so a SIGKILLed dispatcher leaves its children
RUNNING (they are resume-safe via the marker — by design). Before
relaunching a root whose dispatcher was killed, KILL THE ORPHANS first —
each claim JSON records its child pid, which makes them findable. The
tested protocol covers child death + normal relaunch (SC2) and
dead-dispatcher lock reclaim; an orphan-aware relaunch gate is
deliberately out of scope (documented, not protocol-gated).

See also:
    ``pipeline/run_sweep_shard.py`` — the CLI entry that routes
    ``--mode dispatch`` here (and whose ``_parse_gpus`` / log-stamp
    discipline this engine reuses).
    ``pipeline/run_sweep.py`` — the single owner of enumeration, argv,
    layout, and every constant consumed here.
    ``tests/test_dispatch_core.py`` — the SC2/SC3 + happy-path contract
    tests.
"""

import hashlib
import json
import os
import subprocess
import sys
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import directories_config  # sibling module (the F4W-01 startup config)
import registry_loader  # sibling module (registry views for the validation join)
import run_sweep  # sibling module: enumeration/argv/layout/constants (D-07)
import run_sweep_shard  # sibling module: _parse_gpus + the log-stamp format

#: Ledger directory under the shared root — one JSON claim file per cell
#: plus the singleton dispatcher lock. ONE naming authority (the
#: ``worker_root`` discipline): tests pin these names, and Phase 14's
#: consumers (MGPU-03/04) read them.
LEDGER_DIR_NAME = "dispatch_ledger"

#: The run-level state file at the ROOT (mode evidence + counts ground
#: truth; the Phase 14 live-view contract extends this file).
DISPATCH_STATE_NAME = "dispatch_state.json"

#: The singleton dispatcher lock, INSIDE the ledger dir (created only
#: after the ledger dir exists, so the lock's presence implies the dir).
DISPATCHER_LOCK_NAME = "dispatcher.lock"

#: Claim state vocabulary: ``claimed`` at claim time, finalized to
#: ``completed`` only after the CR-02 artifact check, else ``failed``.
CLAIM_STATE_CLAIMED = "claimed"
CLAIM_STATE_COMPLETED = "completed"
CLAIM_STATE_FAILED = "failed"

#: ``dispatch_state.json`` schema version (Phase 13 minimal shape).
DISPATCH_STATE_SCHEMA_VERSION = 1

# The relaunch skip-filter verdicts (pure per-cell decisions).
_DECISION_SKIP = "skip"
_DECISION_FRESH = "fresh"
_DECISION_REQUEUE = "requeue"


def parse_sweep_remainder(passthrough):
    """Re-parse the passthrough through ``run_sweep``'s own parser.

    The dispatch mode needs the enumeration/lane axes (``--tasks``,
    ``--seeds``, ``--peft``, ``--curve``, ``--config-variant``,
    ``--priority-file``, the pass-through family) that live in the
    ``parse_known_args`` remainder. Hand-rolled readers would duplicate
    argparse ``choices``/``type``/``nargs='?'`` semantics and drift, so
    the remainder re-parses through ``run_sweep.parse_args`` itself via
    the ``sys.argv`` swap — run_sweep stays the single owner of sweep-flag
    validation and help (D-07, research Pattern 3). A dispatch launch
    missing ``--seeds`` therefore dies here with argparse's own usage
    exit (code 2) exactly like a static worker would inside its process
    (phase research Pitfall 9 — pinned as the accepted shape).

    Args:
        passthrough (list[str]): the verbatim ``parse_known_args``
            remainder (all-run_sweep-owned tokens by construction).

    Returns:
        argparse.Namespace: run_sweep's parsed namespace over the
        remainder.
    """
    saved = sys.argv
    try:
        sys.argv = ["run_sweep.py", *passthrough]
        return run_sweep.parse_args()
    finally:
        sys.argv = saved


def dispatch_worker_log_path(base_root, index, timestamp):
    """Return the per-launch dispatch worker tee log path.

    ``{base}-dispatch-w{index}-{timestamp}.log`` — a ``.log`` SIBLING of
    the shared root, distinct from the static mode's
    ``{base}-mgpu-w{index}-{timestamp}.log`` naming. One file per worker
    per launch (WR-02, the ``worker_log_path`` discipline): a resume
    relaunch derives a FRESH stamp via the injectable clock and never
    truncates the previous launch's crash log.

    Args:
        base_root (Path | str): the RESOLVED shared output root.
        index (int): the worker index (0-based).
        timestamp (str): the per-launch stamp (one for every worker —
            ``run_sweep_shard.WORKER_LOG_TIMESTAMP_FORMAT`` over the
            launch instant).

    Returns:
        Path: ``{base}-dispatch-w{index}-{timestamp}.log`` (not created
        here).
    """
    base = Path(base_root)
    return Path(f"{base}-dispatch-w{index}-{timestamp}.log")


def ledger_dir_for(root):
    """Return the ledger dir ``{root}/dispatch_ledger`` (ONE authority).

    Args:
        root (Path | str): the RESOLVED shared output root.

    Returns:
        Path: the ledger directory (not created here).
    """
    return Path(root) / LEDGER_DIR_NAME


def _cell_key(cell):
    """Project a cell tuple to its JSON-safe dict key.

    Args:
        cell (tuple): ``(model, task, seed)`` or ``(model, task, seed,
        fraction)``.

    Returns:
        dict: ``{"model", "task", "seed", "fraction"}`` (fraction None
        for plain cells).
    """
    return {
        "model": cell[0],
        "task": cell[1],
        "seed": cell[2],
        "fraction": cell[3] if len(cell) > 3 else None,
    }


def _canonical_cell_json(cell):
    """Deterministic canonical JSON for one cell tuple (digest input).

    Args:
        cell (tuple): the cell identity.

    Returns:
        str: compact sorted-key JSON over the tuple as a list.
    """
    return json.dumps(
        list(cell), ensure_ascii=False, sort_keys=True,
        separators=(",", ":"))


def claim_filename(cell):
    """Return the frozen claim filename for one cell (test-pinned).

    Scheme (the plan's frozen discretion decision): percent-encode each
    identity field via ``urllib.parse.quote`` with an EMPTY safe set,
    join the ``model`` / ``task`` / ``seed{n}`` (plus ``frac{f}`` for
    curve cells) fields with the token ``--``, then append ``-`` + the
    first 12 hex chars of SHA-256 over the canonical JSON of the cell
    tuple, extension ``.json``. The digest suffix guarantees injectivity
    regardless of quoting edge cases — model aliases carry ``+`` (encoded
    ``%2B``), task keys carry ``__``, curve fractions are floats, and a
    name containing a literal ``--`` could otherwise collide with the
    join token (phase research Pitfall 5). The full tuple is ALSO stored
    inside the claim JSON, so the ledger is self-describing.

    Args:
        cell (tuple): ``(model, task, seed)`` or ``(model, task, seed,
        fraction)``.

    Returns:
        str: the claim filename (no directory component).
    """
    fields = [str(cell[0]), str(cell[1]), f"seed{cell[2]}"]
    if len(cell) > 3:
        fields.append(f"frac{cell[3]}")
    encoded = "--".join(quote(field, safe="") for field in fields)
    digest = hashlib.sha256(
        _canonical_cell_json(cell).encode("utf-8")).hexdigest()[:12]
    return f"{encoded}-{digest}.json"


def _dump_json_handle(handle, payload):
    """Serialize one payload with the ``_write_json`` discipline.

    ``indent=4, ensure_ascii=False, sort_keys=True`` — byte-deterministic
    serialization for every ledger/state file (the
    ``run_sweep._write_json`` discipline, mirrored for the fd form).

    Args:
        handle: a writable text file object.
        payload (dict): the JSON object to write.
    """
    json.dump(payload, handle, indent=4, ensure_ascii=False,
              sort_keys=True)


def claim_cell(ledger_dir, cell, payload):
    """Create-or-refuse one cell claim — ``O_CREAT | O_EXCL``.

    The exclusive create fails ``EEXIST`` even when the path is a
    symlink (POSIX no-follow guarantee — a planted symlink cannot
    redirect the create onto an outside target, T-13-01), so a second
    claim on a live-claimed cell is STRUCTURALLY refused (SC3): this is
    the defense-in-depth layer under the single in-memory queue.

    Args:
        ledger_dir (Path): the ledger directory (exists).
        cell (tuple): the cell identity (names the file).
        payload (dict): the claim JSON content (caller builds it via
            ``_claim_payload``).

    Returns:
        Path | None: the claim file path, or None when the cell is
        already claimed (structurally refused).
    """
    path = Path(ledger_dir) / claim_filename(cell)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        return None
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        _dump_json_handle(handle, payload)
    return path


def read_claim(ledger_dir, cell):
    """Tolerantly read one cell's claim JSON.

    Tolerance direction is deliberate (decision: the honest direction): a
    MISSING file returns None (the cell is fresh); a file that exists but
    is unreadable, malformed, or not an object returns ``{}`` — an empty
    dict, which never compares ``state == "completed"`` — so a corrupt
    claim requeues the cell instead of skipping it.

    Args:
        ledger_dir (Path): the ledger directory.
        cell (tuple): the cell identity.

    Returns:
        dict | None: the parsed claim object, ``{}`` for a present but
        unusable file, or None when no claim file exists.
    """
    path = Path(ledger_dir) / claim_filename(cell)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _atomic_write_json(path, payload):
    """Atomic JSON write: tmp file + ``os.replace`` (P10 prevention).

    Single-writer discipline: the state file is written only under the
    dispatcher's state lock; a claim file is written only by the worker
    thread that owns it. The tmp name is per-target, and only one writer
    ever targets a given path, so the tmp never races.

    Args:
        path (Path): the destination file.
        payload (dict): the JSON object to write.
    """
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as handle:
        _dump_json_handle(handle, payload)
    os.replace(tmp, path)


def finalize_claim(claim_path, payload):
    """Rewrite one claim with its final state (single writer).

    Called only by the worker thread that owns the claim, after
    ``wait()`` + the CR-02 artifact check — the payload already carries
    ``state``/``finished_at``/``exit_code``/``error``.

    Args:
        claim_path (Path): the claim file (exists).
        payload (dict): the finalized claim content.
    """
    _atomic_write_json(Path(claim_path), payload)


def _claim_payload(cell, lane, gpu, run_id, claimed_at):
    """Build the ``claimed``-state claim JSON for one cell.

    The lane flags (peft, config_variant, subset_file,
    effective_batch_size, num_train_epochs, and the cell's curve
    fraction) are the Phase 14 MGPU-04 failure re-run feed — recorded at
    claim time so a re-run can reconstruct the exact experiment.

    Args:
        cell (tuple): the cell identity.
        lane (dict): the lane flags WITHOUT the per-cell fraction.
        gpu (str): the claiming worker's GPU token.
        run_id (str): the dispatcher run id.
        claimed_at (str): ISO timestamp.

    Returns:
        dict: the claim payload (state ``claimed``, ``child_pid`` None
        until the spawn fills it).
    """
    payload = {
        "cell": _cell_key(cell),
        "state": CLAIM_STATE_CLAIMED,
        "lane": {**lane, "train_fraction": (
            cell[3] if len(cell) > 3 else None)},
        "gpu": gpu,
        "dispatcher_pid": os.getpid(),
        "child_pid": None,
        "run_id": run_id,
        "claimed_at": claimed_at,
        "finished_at": None,
        "exit_code": None,
        "error": None,
    }
    return payload


def acquire_dispatcher_lock(ledger_dir, run_id, started_at):
    """Acquire the singleton dispatcher lock for one root.

    ``os.open(O_CREAT | O_EXCL | O_WRONLY)`` — the create is atomic at
    the filesystem level, so two dispatchers racing on one root resolve
    to exactly one winner (T-13-02). The lock JSON records the pid,
    run_id, and started timestamp for the refusal diagnostic and the
    audit trail (T-13-03).

    Args:
        ledger_dir (Path): the ledger directory (exists).
        run_id (str): this run's id (``uuid4().hex``).
        started_at (str): ISO timestamp.

    Returns:
        Path: the lock file path (now held; release with
        ``release_dispatcher_lock``).

    Raises:
        SystemExit: the lock file already exists — a second dispatcher
        on the same root is refused loudly naming the lock path.
    """
    lock_path = Path(ledger_dir) / DISPATCHER_LOCK_NAME
    payload = {
        "pid": os.getpid(),
        "run_id": run_id,
        "started_at": started_at,
    }
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                     0o644)
    except FileExistsError:
        sys.exit(
            f"[Error] dispatcher lock already held at {lock_path} — "
            "exactly ONE dispatcher may run per output root (MGPU-02); "
            "stop the running dispatcher before relaunching"
        )
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        _dump_json_handle(handle, payload)
    return lock_path


def release_dispatcher_lock(lock_path):
    """Release (unlink) the dispatcher lock; never raises.

    Args:
        lock_path (Path): the lock file (missing is tolerated — e.g. a
            root manually cleaned mid-run).
    """
    try:
        os.unlink(lock_path)
    except OSError:
        pass


def relaunch_decision(root, ledger_dir, cell):
    """Pure per-cell relaunch decision: skip, fresh, or requeue.

    Skip iff the child-side ``trainer_state.json`` marker exists (the
    AUTHORITATIVE completion guard, D-06 — the child wrote it, so the
    cell is done regardless of what the ledger says) OR the claim file
    parses with state ``completed`` AND its cell key agrees (the ledger
    layer — skips provably-finished cells even when the marker is
    absent). A present-but-unusable claim (unreadable JSON, cell-key
    disagreement, state ``claimed``/``failed``) is a STALE claim from a
    dead run: requeue it — sound precisely because the singleton lock
    guarantees no second dispatcher exists (D13-11; no lease, no
    timeout). Purely per-cell (no cross-claim state), so the skip set is
    order-independent by construction.

    Args:
        root (Path): the RESOLVED shared output root.
        ledger_dir (Path): the ledger directory.
        cell (tuple): the enumerated cell.

    Returns:
        str: ``"skip"`` | ``"fresh"`` | ``"requeue"``.
    """
    fraction = cell[3] if len(cell) > 3 else None
    marker = run_sweep.cell_dir_for(
        root, cell[0], cell[1], cell[2], fraction) / run_sweep.RESUME_MARKER
    if marker.exists():
        return _DECISION_SKIP
    claim = read_claim(ledger_dir, cell)
    if claim is None:
        return _DECISION_FRESH
    if claim.get("cell") == _cell_key(cell) and \
            claim.get("state") == CLAIM_STATE_COMPLETED:
        return _DECISION_SKIP
    return _DECISION_REQUEUE


def _now_iso():
    """ISO-8601 UTC timestamp — a runtime observation, never regenerated."""
    return datetime.now(UTC).isoformat()


def _write_state(state_path, state):
    """Atomically write ``dispatch_state.json`` (single writer, P10).

    Args:
        state_path (Path): ``{root}/dispatch_state.json``.
        state (dict): the full state payload.
    """
    _atomic_write_json(state_path, state)


def _spawn_worker(index, gpu, tee, context):
    """One per-GPU worker loop: claim -> spawn -> wait -> record -> next.

    Runs as a THREAD owned by the dispatcher (the sanctioned queue
    mechanics: ``Popen.wait()`` releases the GIL, so N workers overlap
    their child waits). The loop pops cells from the shared pending list
    under the queue lock — a cell is handed to exactly one worker — then
    CLAIMS (O_EXCL) BEFORE spawning, waits, applies the CR-02 artifact
    check, finalizes the claim, and updates the state counts under the
    state lock. Failed cells are recorded and NOT requeued (decision A2).

    Args:
        index (int): the worker index (diagnostics + tee log naming).
        gpu (str): this worker's permanent ``CUDA_VISIBLE_DEVICES``
            token (operator-owned string, never probed).
        tee: this worker's tee handle (held for the whole drain, closed
            by this loop's finally — SIM115 rationale).
        context (dict): the dispatcher's shared context (pending list,
            locks, counts, state, lane args, spawner seam).
    """
    stats = context["worker_stats"][index]
    pending = context["pending"]
    queue_lock = context["queue_lock"]
    state_lock = context["state_lock"]
    try:
        while True:
            with queue_lock:
                if not pending:
                    return
                cell = pending.pop(0)
            model, task, seed = cell[0], cell[1], cell[2]
            fraction = cell[3] if len(cell) > 3 else None
            cell_dir = run_sweep.cell_dir_for(
                context["root"], model, task, seed, fraction)
            payload = _claim_payload(
                cell, context["lane"], gpu, context["run_id"], _now_iso())
            claim_path = claim_cell(context["ledger_dir"], cell, payload)
            if claim_path is None:
                # SC3 structural refusal — defense-in-depth under the
                # single in-memory queue: the cell is already claimed
                # (a stale file the skip filter could not see). Skip it;
                # never spawn a second child for one cell.
                with state_lock:
                    context["counts"]["skipped"] += 1
                continue
            stats["cells"] += 1
            argv = run_sweep.build_argv(
                model, task, seed, str(context["root"]),
                peft=context["peft"],
                train_fraction=fraction,
                subset_file=context["subset_file"],
                effective_batch_size=context["effective_batch_size"],
                num_train_epochs=context["num_train_epochs"],
                cache_dir=context["cache_dir"],
                config_variant=context["config_variant"],
                model_root=context["model_root"],
                dataset_root=context["dataset_root"],
                log_dir=context["log_dir"],
            )
            error = None
            code = None
            try:
                # The verbatim static spawn discipline
                # (run_sweep_shard.py:1201-1212) minus worker-root
                # naming: argv LIST, own session, cwd pinned to
                # pipeline/, env copy + PYTHONUNBUFFERED + the ONE
                # CUDA_VISIBLE_DEVICES token, stderr onto stdout's tee.
                proc = context["spawner"](
                    list(argv),
                    start_new_session=True,
                    cwd=str(run_sweep.PIPELINE_DIR),
                    env={
                        **os.environ,
                        "PYTHONUNBUFFERED": "1",
                        "CUDA_VISIBLE_DEVICES": gpu,
                    },
                    stdout=tee,
                    stderr=subprocess.STDOUT,
                )
                payload["child_pid"] = getattr(proc, "pid", None)
                code = proc.wait()
            except (subprocess.SubprocessError, OSError) as exc:
                # The run_matrix failure boundary mirrored: launch-seam
                # failures fail the cell, never the dispatcher.
                error = f"{type(exc).__name__}: {exc}"
            if error is None and code != 0:
                error = f"child exited {code}"
            elif error is None and not (
                    cell_dir / run_sweep.METRICS_NAME).is_file():
                # CR-02: exit 0 without final_metrics.json is the
                # child's designed training-failure signal.
                error = (
                    "child exited 0 but final_metrics.json is missing "
                    "(run_finetune.py swallowed a training failure)"
                )
            payload["exit_code"] = code
            payload["error"] = error
            payload["finished_at"] = _now_iso()
            payload["state"] = (
                CLAIM_STATE_COMPLETED if error is None
                else CLAIM_STATE_FAILED)
            finalize_claim(claim_path, payload)
            with state_lock:
                if error is None:
                    context["counts"]["completed"] += 1
                    stats["completed"] += 1
                else:
                    context["counts"]["failed"] += 1
                    stats["failed"] += 1
                context["state"]["counts"] = dict(context["counts"])
                context["state"]["updated_at"] = _now_iso()
                _write_state(context["state_path"], context["state"])
    finally:
        try:
            tee.close()
        except OSError:
            pass


def run_dispatch(args, passthrough, spawner=None, clock=None):
    """The dispatch engine entry (routed from ``run_sweep_shard.main``).

    Protocol (the module docstring's strict order): validate + enumerate
    (zero-cell refusal BEFORE the lock) -> mkdir ledger -> singleton lock
    -> ``dispatch_state.json`` mode evidence -> pending queue -> one
    worker thread per ``--workers`` entry (permanently bound to
    ``gpus[i]``) -> join -> per-worker verdict table -> final state ->
    lock released in ``finally``. Exit 0 iff zero cells failed, else
    exit 1 (failures recorded in the ledger; Phase 14 owns re-run). An
    empty PENDING set (a fully-drained relaunch) prints the explicit
    nothing-to-do verdict and returns WITHOUT spawning anything.

    Output-root precedence (locked decision): the SHARD flag
    ``--output-root`` (default ``./finetuned``, resolved absolute) IS the
    dispatch root — ``directories.json``'s ``output_root`` key does NOT
    redirect the orchestrator (identical to static mode's forwarding).
    The other four directory keys (cache_dir / model_root / dataset_root
    / log_dir) apply flag > file key > default exactly as
    ``run_sweep.main`` does — they ride the remainder.

    Args:
        args (argparse.Namespace): the parsed SHARD flags (workers, gpus,
            models, output_root, mode).
        passthrough (list[str]): the verbatim ``parse_known_args``
            remainder (the sweep-flag family, re-parsed through
            run_sweep's own parser).
        spawner: an injectable spawner seam (the ``run_sweep_shard``
            ``_DEFAULT_SPAWNER`` idiom); None uses ``subprocess.Popen``.
        clock: an injectable ``datetime.now``-shaped callable; ONE call
            names every worker tee log stamp (WR-02).

    Raises:
        SystemExit: any collect-all validation refusal, the zero-cell
        refusal, the singleton-lock refusal, or exit 1 on failed cells.
    """
    # ========================= Configuration =========================
    # Orchestrator-flag validation (collect-all, the static discipline)
    problems = []
    workers = args.workers
    if workers < 1:
        problems.append(f"--workers must be >= 1, got {workers}")
    gpus = run_sweep_shard._parse_gpus(args.gpus, problems)
    if gpus is not None and workers >= 1 and len(gpus) != workers:
        problems.append(
            f"--gpus arity mismatch: {len(gpus)} GPU id(s) for "
            f"--workers {workers} (one id per worker)"
        )
    # --models is dispatch-mode-required (the WR-07 closure: a
    # full-registry dispatch must be an explicit run_sweep-side omission,
    # never an orchestrator default)
    models_filter = None
    if args.models is None:
        problems.append(
            "--models is required for dispatch mode (omit --models on "
            "run_sweep.py itself to run all models — never an "
            "orchestrator default)"
        )
    else:
        models_filter = [
            m.strip() for m in args.models.split(",") if m.strip()]
        if not models_filter:
            problems.append(
                f"--models {args.models!r} produced no model names after "
                "stripping empty elements"
            )
    if args.dry_run:
        problems.append(
            "--dry-run dispatch planning lands with Plan 13-02 — refusing "
            "rather than spawning real children under a dry-run expectation"
        )

    # Remainder re-parse: run_sweep stays the single flag owner (D-07).
    # A dispatch launch without --seeds dies HERE with argparse's usage
    # exit (code 2) — the pinned Pitfall 9 shape.
    sweep_args = parse_sweep_remainder(passthrough)

    # Seeds/tasks with run_sweep's own strips-to-empty refusals mirrored
    # (WR-14: a provided-but-empty filter must abort, never degrade to
    # the full matrix).
    seeds = sorted(
        {int(s.strip()) for s in sweep_args.seeds.split(",")
         if s.strip()})
    if not seeds:
        problems.append(
            f"--seeds {sweep_args.seeds!r} produced no integer values "
            "after stripping empty elements; pass at least one seed, "
            "e.g. --seeds 42"
        )
    tasks_filter = None
    if sweep_args.tasks is not None:
        tasks_filter = [
            t.strip() for t in sweep_args.tasks.split(",") if t.strip()]
        if not tasks_filter:
            problems.append(
                f"--tasks {sweep_args.tasks!r} produced no task names "
                "after stripping empty elements; omit --tasks to run all "
                "trainable tasks"
            )

    # flag_problems mirror of run_sweep.main's collect-all (source of
    # truth: run_sweep.py:1737-1804 — effective_batch_size >= 1,
    # num_train_epochs >= 1, non-empty subset_file / cache_dir /
    # model_root / dataset_root / log_dir, and the variant x peft
    # never-compose refusal). Mirrored because NO run_sweep.main runs in
    # dispatch mode — the children are run_finetune.py directly.
    if sweep_args.effective_batch_size is not None and \
            sweep_args.effective_batch_size < 1:
        problems.append(
            f"--effective_batch_size must be >= 1, got "
            f"{sweep_args.effective_batch_size}"
        )
    if sweep_args.num_train_epochs is not None and \
            sweep_args.num_train_epochs < 1:
        problems.append(
            f"--num_train_epochs must be >= 1, got "
            f"{sweep_args.num_train_epochs}"
        )
    for flag_name, value in (
            ("--subset_file", sweep_args.subset_file),
            ("--cache_dir", sweep_args.cache_dir),
            ("--model_root", sweep_args.model_root),
            ("--dataset_root", sweep_args.dataset_root),
            ("--log_dir", sweep_args.log_dir)):
        if value is not None and not value.strip():
            problems.append(
                f"{flag_name} {value!r} is empty — refusing to thread a "
                "pathless flag"
            )
    if sweep_args.config_variant is not None and \
            sweep_args.peft != "none":
        problems.append(
            f"--config-variant {sweep_args.config_variant} refuses --peft "
            f"{sweep_args.peft}: variant lanes and adapter lanes never "
            "compose (alias names are disjoint; the child additionally "
            "refuses probe×peft at its argv boundary)"
        )

    if problems:
        sys.exit(f"[Error] {'; '.join(problems)}")

    # registry_dir derived from the re-parsed namespace exactly as
    # run_sweep.main does (run_sweep.py:1638-1640)
    registry_dir = (
        Path(sweep_args.registry_dir).resolve()
        if sweep_args.registry_dir else run_sweep.PIPELINE_DIR
    )
    run_sweep._validate_filters(models_filter, tasks_filter, registry_dir)
    run_sweep._validate_dataset_name_alignment(
        registry_loader.load_datasets_registry(registry_dir))

    # Directory-key resolution: flag > directories.json file key > None
    # (the run_sweep.py:1650-1670 recipe) for the four child-side keys;
    # output_root comes from the SHARD flag only (the locked precedence
    # decision — the file's output_root key never redirects the
    # orchestrator).
    file_dirs = directories_config.load_directories()
    cache_dir_arg = (
        sweep_args.cache_dir if sweep_args.cache_dir is not None
        else file_dirs.get("cache_dir"))
    model_root_arg = (
        sweep_args.model_root if sweep_args.model_root is not None
        else file_dirs.get("model_root"))
    dataset_root_arg = (
        sweep_args.dataset_root if sweep_args.dataset_root is not None
        else file_dirs.get("dataset_root"))
    log_dir_arg = (
        sweep_args.log_dir if sweep_args.log_dir is not None
        else file_dirs.get("log_dir"))
    subset_file_abs = (
        str(Path(sweep_args.subset_file).resolve())
        if sweep_args.subset_file is not None else None)
    cache_dir_abs = (
        str(Path(cache_dir_arg).resolve())
        if cache_dir_arg is not None else None)
    model_root_abs = (
        str(Path(model_root_arg).resolve())
        if model_root_arg is not None else None)
    dataset_root_abs = (
        str(Path(dataset_root_arg).resolve())
        if dataset_root_arg is not None else None)
    log_dir_abs = (
        str(Path(log_dir_arg).resolve())
        if log_dir_arg is not None else None)
    output_root = Path(args.output_root).resolve()

    # Enumeration + priority order (run_sweep verbatim, D-07): the
    # queue's base order is enumerate_matrix's sorted() order, permuted
    # by apply_priority_order's stable reorder when --priority-file is
    # present — identical inputs enumerate identical queues.
    fractions = (
        run_sweep.parse_curve_fractions(sweep_args.curve)
        if sweep_args.curve is not None else None)
    config_variant = sweep_args.config_variant or "none"
    cells = run_sweep.enumerate_matrix(
        models_filter, tasks_filter, seeds, registry_dir,
        peft=sweep_args.peft, fractions=fractions,
        config_variant=config_variant)
    if sweep_args.priority_file is not None:
        tiers = run_sweep.load_priority_tiers(
            sweep_args.priority_file, registry_dir)
        cells = run_sweep.apply_priority_order(cells, tiers)
    if not cells:
        # Zero-enumeration refusal BEFORE the lock (EDGE MGPU-01/empty):
        # an empty registry/filter intersection refuses by name — never
        # a silent full-registry fallback (the WR-07 family).
        sys.exit(
            f"[Error] dispatch enumeration produced 0 cell(s) "
            f"(models={models_filter}, tasks={tasks_filter}, "
            f"seeds={seeds}, registry={registry_dir}) — refusing to "
            "launch an empty dispatch run; an empty filter intersection "
            "never falls back to the full registry"
        )

    # LOCK -> MODE EVIDENCE -> QUEUE (the module docstring's protocol)
    ledger_dir = ledger_dir_for(output_root)
    ledger_dir.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex
    started_at = _now_iso()
    lock_path = acquire_dispatcher_lock(ledger_dir, run_id, started_at)
    seam = subprocess.Popen if spawner is None else spawner
    state_path = output_root / DISPATCH_STATE_NAME
    counts = {
        "total": len(cells),
        "completed": 0,
        "failed": 0,
        "skipped": 0,
    }
    state = {
        "schema_version": DISPATCH_STATE_SCHEMA_VERSION,
        "mode": "dispatch",
        "run_id": run_id,
        "status": "running",
        "started_at": started_at,
        "updated_at": started_at,
        "counts": dict(counts),
    }
    _write_state(state_path, state)  # BEFORE any claim (mode evidence)

    # Pending queue — every enumerated cell on a fresh root; the
    # relaunch skip filter (Task 2) reuses relaunch_decision here.
    pending = list(cells)

    now = datetime.now if clock is None else clock
    launch_stamp = now().strftime(
        run_sweep_shard.WORKER_LOG_TIMESTAMP_FORMAT)
    worker_stats = {
        i: {"cells": 0, "completed": 0, "failed": 0}
        for i in range(workers)}
    context = {
        "root": output_root,
        "ledger_dir": ledger_dir,
        "run_id": run_id,
        "state_path": state_path,
        "state": state,
        "counts": counts,
        "pending": pending,
        "queue_lock": threading.Lock(),
        "state_lock": threading.Lock(),
        "worker_stats": worker_stats,
        "spawner": seam,
        "peft": sweep_args.peft,
        "config_variant": config_variant,
        "subset_file": subset_file_abs,
        "effective_batch_size": sweep_args.effective_batch_size,
        "num_train_epochs": sweep_args.num_train_epochs,
        "cache_dir": cache_dir_abs,
        "model_root": model_root_abs,
        "dataset_root": dataset_root_abs,
        "log_dir": log_dir_abs,
        "lane": {
            "peft": sweep_args.peft,
            "config_variant": config_variant,
            "subset_file": subset_file_abs,
            "effective_batch_size": sweep_args.effective_batch_size,
            "num_train_epochs": sweep_args.num_train_epochs,
        },
    }

    if not pending:
        # The relaunch half of the zero-cell decision (EDGE
        # MGPU-02/empty): a fully drained root is an explicit
        # nothing-to-do verdict and exit 0 — never a re-spawn storm.
        counts["skipped"] = len(cells)
        state["counts"] = dict(counts)
        state["status"] = "done"
        state["updated_at"] = _now_iso()
        _write_state(state_path, state)
        release_dispatcher_lock(lock_path)
        print(
            f"[Dispatch] nothing to do — all {len(cells)} enumerated "
            f"cell(s) are already complete on {output_root}; no workers "
            "spawned"
        )
        return

    # Default GPU assignment (operator-owned strings; no probing, D-05)
    if gpus is None:
        gpus = [str(i) for i in range(workers)]

    tees = []
    try:
        try:
            for i in range(workers):
                log_i = dispatch_worker_log_path(output_root, i,
                                                 launch_stamp)
                log_i.parent.mkdir(parents=True, exist_ok=True)
                # Deliberately NOT a context manager (SIM115, the
                # launcher's rationale): the tee must stay open for the
                # whole drain — every child of this worker writes into
                # it. Held here, closed by the worker loop's finally.
                tees.append(open(  # noqa: SIM115
                    log_i, "w", encoding="utf-8"))
        except OSError as exc:
            sys.exit(
                f"[Error] opening dispatch worker tee failed: {exc} — "
                "no children spawned; the dispatcher lock is released"
            )
        threads = []
        for i in range(workers):
            thread = threading.Thread(
                target=_spawn_worker,
                args=(i, gpus[i], tees[i], context),
                name=f"dispatch-w{i}",
            )
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
    finally:
        for tee in tees:
            try:
                tee.close()
            except OSError:
                pass
        release_dispatcher_lock(lock_path)

    print("Dispatch verdicts:")
    for i in range(workers):
        entry = worker_stats[i]
        print(
            f"  worker {i}: cells={entry['cells']} "
            f"completed={entry['completed']} "
            f"failed={entry['failed']} gpu={gpus[i]} "
            f"log={dispatch_worker_log_path(output_root, i, launch_stamp)}"
        )
    state["status"] = "done"
    state["updated_at"] = _now_iso()
    _write_state(state_path, state)
    print(
        f"[Dispatch] {counts['completed']}/{counts['total']} cell(s) "
        f"completed, {counts['failed']} failed, {counts['skipped']} "
        f"skipped; state: {state_path}"
    )
    if counts["failed"]:
        print(
            "[Dispatch] failed cells are recorded in the ledger for "
            "re-run (Phase 14 MGPU-04) — failed cells are NOT requeued "
            "within a live run"
        )
        sys.exit(1)
