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
   Since Phase 14 (D14-01) the payload is schema v2: the Phase 13
   minimal shape EXTENDED additively with the frozen MGPU-03 consumer
   fields — ``queue_depth`` (derived, see ``_publish_state``), one
   ``workers[]`` row per ``--workers`` index (gpu + in-flight cell +
   counters), and the run's ``failures`` view — frozen in
   ``schemas/dispatch_state.json`` and validated by the consumer test.
   Every state write (mode evidence, skip filter, claim — a dedicated
   claim-time write inside the worker loop — finalize, containment,
   terminal statuses) also RENDERS the frozen payload as a plain-line
   terminal table via ``_render_state`` (D14-02/D14-03: ``flush=True``
   prints under the state lock; no timer loop, no TUI library).
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

Dry-run (13-02, SC1): ``--dry-run`` branches AFTER enumeration/priority
(and after the zero-cell refusal — an empty enumeration refuses
identically dry or real) and BEFORE the lock. It mirrors the static
dry-run projection exactly (matrix + ``status: "planned"`` records
through ``run_sweep._manifest_payload`` / ``_write_json``) with ONE
extra ``"orchestrator_mode": "dispatch"`` sweep-flags marker, writes
ONLY ``{root}/sweep_manifest.json``, and returns: no lock, no state
file, no claims, no tees, no children — byte-identical across runs and
equal to static-mode enumeration for identical inputs.

Failure re-run (14-03, MGPU-04, D14-05..D14-08): ``--rerun-failed``
(the shard parser's orchestrator-owned flag; implies dispatch mode)
re-runs the UNION of failed cells recorded in the claim ledger —
``state: failed`` claims across ALL prior runs on the root — with the
claim-time lane flags replayed VERBATIM through ``build_argv`` (the
12-04 lane-blindness fix, D14-06). The branch sits BEFORE the
``--models`` requirement and never re-parses the remainder (the ledger
defines models AND seeds); the ONLY accepted passthrough token is
``--registry-dir``. Unequal lane signatures among the failed cells
refuse loudly naming each differing flag per cell (D14-08); a failed
cell whose child-side ``trainer_state.json`` marker appeared since the
failure is SKIPPED (the marker stays authoritative, D-06). Original
failed claims are never mutated: each is copied VERBATIM ``O_EXCL``
under ``dispatch_ledger/archive/`` and the canonical slot receives the
fresh claim carrying a ``rerun_of`` link (Option C, the Q1 ruling) —
the audit trail is append-only.

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
import time
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

#: The claim-genealogy archive directory INSIDE the ledger dir (14-03,
#: D14-07 Option C): superseded original claims are copied VERBATIM here
#: (``O_EXCL``, append-only) before the canonical slot receives the
#: fresh re-run claim. A SUBDIRECTORY by design — the ledger scans glob
#: ``*.json`` NON-recursively, so the canonical slot keeps its O(1)
#: ``read_claim`` meaning and archive files never mix into the scan.
ARCHIVE_DIR_NAME = "archive"

#: Claim state vocabulary: ``claimed`` at claim time, finalized to
#: ``completed`` only after the CR-02 artifact check, else ``failed``.
CLAIM_STATE_CLAIMED = "claimed"
CLAIM_STATE_COMPLETED = "completed"
CLAIM_STATE_FAILED = "failed"

#: ``dispatch_state.json`` schema version. v2 (Phase 14, D14-01/D14-04):
#: the Phase 13 minimal shape EXTENDED additively with the frozen
#: MGPU-03 consumer fields — ``queue_depth``, per-worker ``workers``
#: rows (gpu + in-flight cell + counters), and the run's ``failures``
#: view — validated by the consumer test against the committed
#: ``schemas/dispatch_state.json`` (the frozen contract; later changes
#: are additive-only under the D14-04 same-commit discipline).
DISPATCH_STATE_SCHEMA_VERSION = 2

#: The create-to-write grace window (CR-02, phase-13 review): the lock's
#: ``O_EXCL`` create is atomic but its payload write happens afterwards,
#: so a lock that exists yet parses to NO holder may be an IN-FLIGHT
#: writer inside that window. A second dispatcher reading in the window
#: must NOT reclaim (the reclaim would overwrite the first dispatcher's
#: lock and put two dispatchers on one root); only a file older than
#: this window is a provably dead writer (crashed mid-write) and
#: reclaimable.
_LOCK_WRITE_GRACE_SECONDS = 5.0

# The relaunch skip-filter verdicts (pure per-cell decisions).
_DECISION_SKIP = "skip"
_DECISION_FRESH = "fresh"
_DECISION_REQUEUE = "requeue"

# The pending-queue tag marking an MGPU-04 re-run entry: the worker's
# claim step performs the D14-07 genealogy (archive + fresh claim with
# rerun_of) instead of the SC3 silent skip when the canonical failed
# claim EEXISTs (the Pitfall 1 collision knot).
_TAG_RERUN = "rerun"

# Passthrough tokens a --rerun-failed launch refuses (T-14-08, Pitfall
# 5): scoping tokens would double-scope the ledger-driven re-run;
# lane tokens would blend command-line lanes with claim-time lanes
# (D14-06 replay is verbatim, never blended).
_RERUN_SCOPING_TOKENS = ("--from-failures", "--tasks", "--seeds")
_RERUN_LANE_TOKENS = (
    "--peft", "--config-variant", "--subset_file",
    "--effective_batch_size", "--batch_size", "--num_train_epochs",
    "--cache_dir",
    "--model_root", "--dataset_root", "--log_dir",
)


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


def overwrite_claim(ledger_dir, cell, payload):
    """Atomically REPLACE one stale claim (the requeue path, Task 2).

    A requeued cell's claim file already exists (state ``claimed`` or
    ``failed`` from a dead run) — the singleton lock guarantees no
    second dispatcher lives, so replacing it is sound (D13-11: stale
    claims are reclaimable precisely BECAUSE no second dispatcher can
    exist; no lease, no timeout). The replace is atomic (tmp +
    ``os.replace``): a crash mid-reclaim leaves either the old stale
    claim or the new one, never a torn file.

    Args:
        ledger_dir (Path): the ledger directory.
        cell (tuple): the cell identity (names the file).
        payload (dict): the fresh claim content.

    Returns:
        Path: the claim file path (now owned by this run).
    """
    path = Path(ledger_dir) / claim_filename(cell)
    _atomic_write_json(path, payload)
    return path


def _archive_filename(cell, original_run):
    """The frozen archive filename for one superseded attempt.

    ``{claim stem}--run-{run_id prefix}.json`` — keyed by the ORIGINAL
    attempt's ``run_id`` so the name is injective across attempts (a
    second-level re-run of a re-run archives under the re-run's own
    ``run_id``).

    Args:
        cell (tuple): the cell identity.
        original_run (str): the original attempt's run id.

    Returns:
        str: the archive filename (no directory component).
    """
    stem = claim_filename(cell)[:-len(".json")]
    return f"{stem}--run-{original_run[:8]}.json"


def archive_superseded_claim(ledger_dir, cell, original_payload):
    """Archive one superseded claim ``O_EXCL`` under ``archive/`` (D14-07).

    Option C (the planner's Q1 ruling): a re-run NEVER mutates or
    destroys the original failed claim — the ORIGINAL payload is copied
    VERBATIM to ``dispatch_ledger/archive/{claim stem}--run-{run_id
    prefix}.json`` created with ``O_CREAT | O_EXCL`` (the ``claim_cell``
    no-follow guarantee — a planted symlink can neither be followed nor
    silently overwritten, T-14-06). The archive name is keyed by the
    ORIGINAL attempt's ``run_id``, so it is injective across attempts:
    a second-level re-run of a re-run archives under the re-run's own
    ``run_id``. ``EEXIST`` refuses loudly — the audit history is
    append-only and can never be overwritten.

    Args:
        ledger_dir (Path): the ledger directory.
        cell (tuple): the cell identity (names the canonical claim the
            archive filename derives from).
        original_payload (dict): the original failed claim JSON, used
            VERBATIM (must carry a non-empty string ``run_id``).

    Returns:
        str: the archive FILENAME (relative to the archive dir) — the
        value the fresh claim's ``rerun_of`` link records.

    Raises:
        ValueError: the original payload carries no usable ``run_id``
            (the caller — the worker's re-run claim step — turns this
            into a loud per-cell failure, never a silent skip).
        FileExistsError: the archive file already exists (audit
            history protected; the re-run refuses).
    """
    original_run = original_payload.get("run_id")
    if not isinstance(original_run, str) or not original_run:
        raise ValueError(
            f"cannot archive the claim for cell {cell}: the original "
            "payload carries no usable run_id"
        )
    archive_dir = Path(ledger_dir) / ARCHIVE_DIR_NAME
    archive_dir.mkdir(parents=True, exist_ok=True)
    filename = _archive_filename(cell, original_run)
    path = archive_dir / filename
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError as exc:
        raise FileExistsError(
            f"archive file {path} already exists — the ledger's audit "
            "history is append-only and never overwritten (D14-07); "
            "refusing the re-run"
        ) from exc
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        _dump_json_handle(handle, original_payload)
    return filename


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
    effective_batch_size, batch_size — the per-device starting
    micro-batch, 261023-abu — num_train_epochs, cache_dir, the three
    storage roots model_root/dataset_root/log_dir — all additive,
    14-03 — and the cell's curve fraction) are the Phase 14 MGPU-04
    failure re-run feed — recorded at claim time so a re-run can
    reconstruct the exact experiment (D14-06; replay reads tolerantly,
    so pre-change claims lacking the newer keys replay with the flag
    absent — zero argv elements, never a refusal).

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


def _read_lock_holder(lock_path):
    """Tolerantly read the lock JSON for the reclaim decision.

    Args:
        lock_path (Path): the lock file.

    Returns:
        dict | None: the parsed lock object, or None when unreadable,
        malformed, or not an object (each maps to the reclaim branch —
        an unusable lock cannot name a live holder).
    """
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def acquire_dispatcher_lock(ledger_dir, run_id, started_at):
    """Acquire the singleton dispatcher lock for one root.

    ``os.open(O_CREAT | O_EXCL | O_WRONLY)`` — the create is atomic at
    the filesystem level, so two dispatchers racing on one root resolve
    to exactly one winner (T-13-02). The lock JSON records the pid,
    run_id, and started timestamp for the refusal diagnostic and the
    audit trail (T-13-03).

    Stale-lock reclaim (decision A5, pid-liveness): on an existing lock
    the recorded pid is probed with ``os.kill(pid, 0)`` — a LIVE pid
    (or a PermissionError, i.e. a live dispatcher under another user)
    refuses loudly naming the pid, run_id, and lock path; a
    ``ProcessLookupError`` (provably dead) or a lock that parses but
    carries no usable pid is RECLAIMED by atomic overwrite.
    Reclaim-on-provable-death only is the safe direction for pid reuse
    (T-13-03: a reused live pid refuses); singleton-dispatcher semantics
    make the overwrite sound — a second dispatcher structurally cannot
    exist while the first lives.

    Create-to-write window (CR-02, phase-13 review): an UNREADABLE or
    EMPTY lock may be an in-flight writer between its atomic ``O_EXCL``
    create and its payload write — reclaiming it immediately would
    atomically overwrite the first dispatcher's lock and put TWO
    dispatchers on one root. Such a lock is reclaimed only when older
    than ``_LOCK_WRITE_GRACE_SECONDS`` (a provably dead writer); a
    fresh one refuses loudly as a possible in-flight writer.

    Args:
        ledger_dir (Path): the ledger directory (exists).
        run_id (str): this run's id (``uuid4().hex``).
        started_at (str): ISO timestamp.

    Returns:
        Path: the lock file path (now held; release with
        ``release_dispatcher_lock``).

    Raises:
        SystemExit: the lock names a LIVE holder — refused loudly naming
        the pid, run_id, and lock path; or the lock is unreadable and
        younger than the create-to-write grace window (a possible
        in-flight writer).
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
        holder = _read_lock_holder(lock_path)
        if holder is None:
            # CR-02: an empty/unreadable lock with a FRESH mtime may be
            # an in-flight writer inside the create-to-write window —
            # refuse; the singleton guarantee must hold in that window
            # too. Only a file older than the grace window is a provably
            # dead writer (crashed mid-write) and reclaimable. An
            # unstatable file also refuses (the safe direction).
            try:
                age = time.time() - lock_path.stat().st_mtime
            except OSError:
                age = 0.0
            if age < _LOCK_WRITE_GRACE_SECONDS:
                sys.exit(_unwritten_lock_refusal(lock_path))
            _atomic_write_json(lock_path, payload)  # provably stale
            return lock_path
        if isinstance(holder.get("pid"), int):
            holder_pid = holder["pid"]
            holder_run = holder.get("run_id")
            try:
                os.kill(holder_pid, 0)
            except (ProcessLookupError, OverflowError):
                # ProcessLookupError: provably dead. OverflowError (WR-02,
                # phase-13 review): a pid too large to signal (e.g. 2**63
                # in a corrupt-but-parseable lock) cannot be a live
                # holder — both fall through to the reclaim, never an
                # unhandled crash on the recovery path (the designed
                # tolerant-read contract: a malformed lock is RECLAIMED).
                pass
            except PermissionError:
                # A live dispatcher under ANOTHER user — same loud
                # refusal (only the superuser may signal it; the safe
                # direction is to treat it as alive)
                sys.exit(_live_holder_refusal(
                    lock_path, holder_pid, holder_run))
            else:
                sys.exit(_live_holder_refusal(
                    lock_path, holder_pid, holder_run))
        # A parseable lock with no usable pid, or a provably dead
        # holder: reclaim by atomic overwrite (decision A5).
        _atomic_write_json(lock_path, payload)
        return lock_path
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        _dump_json_handle(handle, payload)
    return lock_path


def _live_holder_refusal(lock_path, holder_pid, holder_run):
    """Build the live-holder refusal message (names pid + run_id)."""
    return (
        f"[Error] dispatcher lock at {lock_path} is held by a LIVE "
        f"dispatcher (pid {holder_pid}, run_id {holder_run!r}) — exactly "
        "ONE dispatcher may run per output root (MGPU-02); stop the "
        "running dispatcher before relaunching (if the pid is stale, the "
        "holder is dead and the next launch reclaims automatically)"
    )


def _unwritten_lock_refusal(lock_path):
    """Build the in-flight-writer refusal (CR-02, phase-13 review)."""
    return (
        f"[Error] dispatcher lock at {lock_path} exists but names no "
        "holder and was created moments ago — another dispatcher may be "
        "between its lock create and its payload write; retry in a few "
        "seconds (a lock left unwritten by a crashed writer is reclaimed "
        f"automatically once older than "
        f"{_LOCK_WRITE_GRACE_SECONDS:.0f}s)"
    )


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
    """Atomically write ``dispatch_state.json`` and render it (P10, D14-02).

    The single choke point for every state transition: the atomic
    write lands FIRST, then ``_render_state`` prints the exact frozen
    payload just written — the renderer must never observe anything the
    on-disk consumer cannot (the side-channel anti-pattern). Runs
    under the caller's ``state_lock``, so renders never interleave.

    Args:
        state_path (Path): ``{root}/dispatch_state.json``.
        state (dict): the full state payload.
    """
    _atomic_write_json(state_path, state)
    _render_state(state)


def _render_state(state):
    """Render the frozen state payload as plain stdout lines (D14-02).

    One header line naming status / queue depth / done / failed /
    skipped, then one row per ``workers[]`` entry showing the worker's
    in-flight cell (``model/task/seed_N`` plus ``/frac_F`` for curve
    cells) or ``-``. Plain prints with ``flush=True`` — the block-
    buffering pitfall: a piped/pty consumer must see each table the
    moment it is written, not in an end-of-run burst. Called ONLY from
    ``_write_state`` after the atomic write (no timer loop, no TUI
    library, no second file — D14-02/D14-01).

    Output failures are swallowed best-effort (T-14-01): a dying
    consumer view (closed pipe, unencodable stream) must NEVER fail a
    cell via the CR-04 containment, kill a worker thread, or abort the
    drain.

    Args:
        state (dict): the frozen payload just written to disk.
    """
    try:
        counts = state["counts"]
        print(
            f"[Dispatch] status={state['status']} "
            f"queue={state['queue_depth']} "
            f"done={counts['completed']}/{counts['total']} "
            f"failed={counts['failed']} skipped={counts['skipped']}",
            flush=True)
        for worker in state["workers"]:
            cell = worker["in_flight"]
            if cell is None:
                detail = "-"
            else:
                detail = (
                    f"{cell['model']}/{cell['task']}/seed_{cell['seed']}")
                if cell["fraction"] is not None:
                    detail += f"/frac_{cell['fraction']}"
            print(
                f"  w{worker['index']} gpu={worker['gpu']}: {detail}",
                flush=True)
    except (BrokenPipeError, OSError, ValueError):
        # BrokenPipeError/OSError: the consumer view died (closed pipe,
        # fd error). ValueError covers UnicodeEncodeError — an
        # unencodable stream is still a view failure, never a cell
        # failure. Swallow and keep draining.
        pass


def _publish_state(context):
    """Refresh the v2 consumer fields and write ``dispatch_state.json``.

    The ONE state-publication idiom (D14-01): every state transition
    calls this under ``context["state_lock"]``, which recomputes the
    additive consumer fields from the context's ground truth and hands
    the frozen payload to ``_write_state`` — so the written file and the
    rendered table observe exactly the same payload, never side-channel
    state (the anti-pattern).

    Snapshot invariant (the Pitfall 3 decision, frozen in
    ``schemas/dispatch_state.json``): at EVERY write,

    ``counts.completed + counts.failed + counts.skipped + queue_depth
    + (workers whose in_flight is non-null) == counts.total``.

    ``queue_depth`` is DERIVED (``total - completed - failed - skipped
    - active workers``), never ``len(pending)``: the two locks are
    never held together, a cell popped-but-not-yet-claimed transiently
    counts in the derived depth, and the claim-time write moves it into
    its worker's ``in_flight`` slot — the identity holds at every
    observed write by construction, transient window included.

    Args:
        context (dict): the dispatcher's shared context. The caller
            MUST hold ``context["state_lock"]`` (single writer, P10).
    """
    state = context["state"]
    counts = context["counts"]
    in_flight = context["in_flight"]
    active = sum(1 for slot in in_flight.values() if slot is not None)
    state["counts"] = dict(counts)
    state["queue_depth"] = (
        counts["total"] - counts["completed"] - counts["failed"]
        - counts["skipped"] - active)
    state["workers"] = [
        {
            "index": index,
            "gpu": context["gpus"][index],
            "in_flight": in_flight.get(index),
            "cells": entry["cells"],
            "completed": entry["completed"],
            "failed": entry["failed"],
        }
        for index, entry in sorted(context["worker_stats"].items())
    ]
    state["updated_at"] = _now_iso()
    _write_state(context["state_path"], state)


def _publish_state_pre_drain(context, lock_path):
    """Publish state while the lock's release is NOT yet guaranteed.

    WR-01 (phase-14 review): the pre-drain publishes inside
    ``_launch_and_drain`` run AFTER ``acquire_dispatcher_lock`` but
    BEFORE the drain's ``try/finally`` guarantees the release — an I/O
    failure there (ENOSPC/EACCES on the root, the same failure class
    the CR-04 worker containment was built for) must not leak
    ``dispatcher.lock`` on disk naming this run behind a raw traceback.
    Mirror the tee-open refusal discipline (the sibling failure path):
    release the lock, then exit with the designed diagnostic — no
    children were spawned, so nothing else needs containment.

    Args:
        context (dict): the dispatcher's shared context (single-threaded
            here — the drain has not started, no ``state_lock`` needed).
        lock_path (Path): the acquired lock file to release on failure.

    Raises:
        SystemExit: the state write failed with an ``OSError`` — the
            lock is released first and the message names the cause.
    """
    try:
        _publish_state(context)
    except OSError as exc:
        release_dispatcher_lock(lock_path)
        sys.exit(
            f"[Error] writing dispatch state failed: {exc} — no "
            "children spawned; the dispatcher lock is released"
        )


def _spawn_worker(index, gpu, tee, context):
    """One per-GPU worker loop: claim -> spawn -> wait -> record -> next.

    Runs as a THREAD owned by the dispatcher (the sanctioned queue
    mechanics: ``Popen.wait()`` releases the GIL, so N workers overlap
    their child waits). The loop pops cells from the shared pending list
    under the queue lock — a cell is handed to exactly one worker — then
    CLAIMS (O_EXCL) BEFORE spawning, waits, applies the CR-02 artifact
    check, finalizes the claim, and updates the state counts under the
    state lock. Failed cells are recorded and NOT requeued (decision A2).

    Phase 14 view maintenance (D14-01): the worker's ``in_flight`` slot
    (``context["in_flight"][index]``) is set to the claimed cell key
    after a successful claim and cleared inside the finalize critical
    section before its state write; a failed finalize also appends the
    compact failure entry to the state's ``failures`` view, so
    ``len(failures) == counts.failed`` at rest.

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
                cell, tag = pending.pop(0)
            claim_path = None
            payload = None
            accounted = False  # set atomically with the count increment
            try:
                model, task, seed = cell[0], cell[1], cell[2]
                fraction = cell[3] if len(cell) > 3 else None
                cell_dir = run_sweep.cell_dir_for(
                    context["root"], model, task, seed, fraction)
                payload = _claim_payload(
                    cell, context["lane"], gpu, context["run_id"],
                    _now_iso())
                if tag == _TAG_RERUN:
                    # MGPU-04 re-run claim step (14-03, D14-07 Option C —
                    # the Pitfall 1 collision knot): the canonical slot
                    # still holds the ORIGINAL failed claim the scan read,
                    # so the fresh O_EXCL create EEXISTs by design. On
                    # EEXIST: archive the original VERBATIM (O_EXCL under
                    # archive/ — append-only audit history), then write
                    # the fresh claim over the canonical slot carrying the
                    # rerun_of link. The SC3 silent skip must NEVER fire
                    # for a rerun-tagged cell — an EEXIST whose original
                    # read yields nothing usable refuses loudly instead
                    # (the CR-04 containment fails the cell; exit 1).
                    claim_path = claim_cell(
                        context["ledger_dir"], cell, payload)
                    if claim_path is None:
                        original = read_claim(
                            context["ledger_dir"], cell)
                        if not isinstance(original, dict) or not (
                                isinstance(original.get("run_id"), str)
                                and original.get("run_id")):
                            raise RuntimeError(
                                f"re-run of cell {cell}: the canonical "
                                "claim exists but is unusable for "
                                "genealogy (no run_id) — refusing "
                                "loudly, never a silent skip"
                            )
                        payload["rerun_of"] = {
                            "archive": archive_superseded_claim(
                                context["ledger_dir"], cell, original),
                            "run_id": original["run_id"],
                            "claimed_at": original.get("claimed_at"),
                        }
                        claim_path = overwrite_claim(
                            context["ledger_dir"], cell, payload)
                elif tag == _DECISION_REQUEUE:
                    # Stale claim from a dead run: atomically REPLACED with
                    # this run's payload (new run_id/gpu/timestamps). Sound
                    # because the singleton lock guarantees no second
                    # dispatcher (D13-11 — no lease, no timeout).
                    claim_path = overwrite_claim(
                        context["ledger_dir"], cell, payload)
                else:
                    claim_path = claim_cell(
                        context["ledger_dir"], cell, payload)
                    if claim_path is None:
                        # SC3 structural refusal — defense-in-depth under
                        # the single in-memory queue: the cell is already
                        # claimed (a file the skip filter could not see).
                        # Skip it; never spawn a second child for one cell.
                        with state_lock:
                            context["counts"]["skipped"] += 1
                            context["state"]["counts"] = dict(
                                context["counts"])
                        continue
                stats["cells"] += 1
                # Claim-time state write (D14-03 — the 8th call site):
                # set this worker's in-flight slot and publish BEFORE
                # the spawn, so the live table shows the cell WHILE the
                # child trains and the derived queue_depth keeps the
                # snapshot invariant across the pop-to-claim window.
                # The publication is best-effort BY DESIGN (T-14-01):
                # the ledger claim — the truth — is already on disk, so
                # a state-file I/O failure here must not fail the cell
                # through the CR-04 containment (the finalize and
                # end-of-run writes remain the accounting guarantees).
                # The slot is set regardless so the next successful
                # write snapshots it.
                with state_lock:
                    context["in_flight"][index] = _cell_key(cell)
                    try:
                        _publish_state(context)
                    except OSError:
                        pass
                argv = run_sweep.build_argv(
                    model, task, seed, str(context["root"]),
                    peft=context["peft"],
                    train_fraction=fraction,
                    subset_file=context["subset_file"],
                    effective_batch_size=context["effective_batch_size"],
                    batch_size=context["batch_size"],
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
                    # CR-03 (phase-13 review): persist the pid IMMEDIATELY,
                    # before wait() — the on-disk claim must name the child
                    # for the child's ENTIRE lifetime (the documented
                    # orphan-recovery procedure reads child pids from the
                    # claim JSON; leaving the write to finalize_claim kept
                    # the claim at "child_pid": null for the whole training
                    # run, exactly the window in which a dispatcher kill
                    # leaves orphans).
                    _atomic_write_json(claim_path, payload)
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
                # run_record write (15-04, the A3 supersession): AFTER
                # the CR-02 artifact check, BEFORE finalize_claim — the
                # record lands while the claim is still in-memory
                # terminal, so any refusal/failure here flows through
                # the CR-04 containment with accounted=False (the claim
                # is rewritten failed dispatcher-side, counts.failed,
                # exit 1 — never a silently record-less green run).
                write_cell_run_record(
                    cell, cell_dir, payload, context["git_commit"])
                finalize_claim(claim_path, payload)
                with state_lock:
                    # Clear the in-flight slot BEFORE the count lands so
                    # the write's derived queue_depth keeps the snapshot
                    # invariant (the cell moves from in-flight to its
                    # terminal count atomically under this lock).
                    context["in_flight"][index] = None
                    if error is None:
                        context["counts"]["completed"] += 1
                        stats["completed"] += 1
                    else:
                        context["counts"]["failed"] += 1
                        stats["failed"] += 1
                        context["state"]["failures"].append({
                            "model": model,
                            "task": task,
                            "seed": seed,
                            "fraction": fraction,
                            "finished_at": payload["finished_at"],
                        })
                    accounted = True
                    _publish_state(context)
            except Exception as exc:  # noqa: BLE001 — containment boundary
                # CR-04 (phase-13 review): any dispatcher-side failure
                # OUTSIDE the spawn seam (claim create/overwrite,
                # finalize, the state write — e.g. ENOSPC/EACCES) fails
                # THIS cell loudly and the drain CONTINUES; the failed
                # count drives the exit-1 path. Without this boundary the
                # exception killed the worker THREAD, silently dropped
                # the remaining queue, and the run reported status "done"
                # with exit 0 — a false success on the orchestrator's
                # error path. If this handler itself dies (a systemic
                # write failure), the post-join accounting assertion in
                # run_dispatch refuses loudly instead.
                if not accounted:
                    # WR-03 (phase-13 review): the claim rewrite is gated
                    # on the SAME flag as the count. accounted=True means
                    # finalize_claim ALREADY persisted this cell's
                    # truthful terminal state and the count was already
                    # incremented — the only operation after that point
                    # is the state write, so an exception there must NOT
                    # overwrite a completed claim with
                    # failed/dispatcher-side failure/exit_code null (the
                    # ledger is Phase 14 MGPU-04's designed re-run feed;
                    # a lying claim re-runs completed cells). The
                    # end-of-run final write persists the truthful
                    # counts — swallow and continue.
                    if claim_path is not None and payload is not None:
                        payload["exit_code"] = None
                        payload["error"] = (
                            f"dispatcher-side failure: "
                            f"{type(exc).__name__}: {exc}")
                        payload["finished_at"] = _now_iso()
                        payload["state"] = CLAIM_STATE_FAILED
                        try:
                            finalize_claim(claim_path, payload)
                        except OSError:
                            pass  # best-effort: the failed count + exit 1
                            # below remain the hard guarantee
                    # Counted here ONLY if the normal path never reached
                    # its increment (double-counting a cell that already
                    # incremented completed/failed would corrupt the
                    # accounting assertion in run_dispatch).
                    with state_lock:
                        context["in_flight"][index] = None
                        context["counts"]["failed"] += 1
                        stats["failed"] += 1
                        context["state"]["failures"].append({
                            "model": model,
                            "task": task,
                            "seed": seed,
                            "fraction": fraction,
                            "finished_at": _now_iso(),
                        })
                        _publish_state(context)
    finally:
        try:
            tee.close()
        except OSError:
            pass


def _claim_lane(payload):
    """Tolerantly project one claim's ``lane`` dict.

    A missing, non-object, or corrupt lane degrades to ``{}`` — the
    tolerant-read contract (never crash-or-trust): the re-run replays
    what IS recorded and treats absent keys as absent flags.

    Args:
        payload (dict): a parsed claim payload.

    Returns:
        dict: the claim's lane dict, or ``{}`` when unusable.
    """
    lane = payload.get("lane")
    return lane if isinstance(lane, dict) else {}


def write_cell_run_record(cell, cell_dir, payload, git_commit):
    """Compose and write one cell's ``run_record.json`` at claim
    finalize (15-04 — the Phase 13 A3 supersession).

    Phase 13 decision A3 (13-01-PLAN.md:121-124) locked dispatch roots
    as record-less and deferred a producer to a "documented Phase
    14/15 handoff" that never landed; the 15-01 smoke then proved the
    gap (``export_runs.py`` walks
    ``{root}/{model}/{task}/seed_{n}/run_record.json`` and skips every
    cell without one — a green dispatch root exported ZERO records),
    and the maintainer's Option 1 ruling (15-01-SUMMARY, 2026-10-20)
    puts the writer HERE, at exactly the handoff point A3 deferred.
    ``run_sweep.py`` stays untouched (the schema authority frozen): the
    skeleton is REUSED through ``run_sweep._new_record`` — the exact
    call ``run_matrix`` makes for the same cell — so the
    cell-identity fields (model/task/seed/peft/config_variant/
    train_fraction/output_dir) are identical by construction, never
    re-implemented (D-07).

    Ordering (pinned by the 15-04 contract tests): the CHILD writes
    ``trainer_state.json`` last (WR-13); the WORKER composes and writes
    this record AFTER the CR-02 artifact check and BEFORE
    ``finalize_claim`` — so every failure mode below flows through the
    existing CR-04 containment with ``accounted=False``: the claim is
    rewritten failed with the dispatcher-side error, ``counts.failed``
    increments, the run exits 1, and a finalized completed claim can
    never be rewritten (the WR-03 invariant holds — after
    ``accounted=True`` only the state write follows).

    Composition (trust boundary — the record is attestation): built
    ONLY from what THIS cell produced and THIS dispatcher claimed.
    Metrics are ``json.load``-ed VERBATIM from the cell's own
    ``final_metrics.json`` (completed claims only); the lane is read
    tolerantly from the claim payload through ``_claim_lane`` (the
    claim-time record is the D14-06 replay authority, so the record's
    lane IS the lane the child ran); ``started_at`` is the claim's
    ``claimed_at`` and ``finished_at`` the claim's ``finished_at`` (the
    dispatch runtime observations of this attempt); ``vram_probe``
    stays the skeleton's four nulls (dispatch children never run the
    probe); ``git_commit`` is the run's ONE observation (the
    run_matrix parity — never per cell).

    Failure semantics (run_matrix parity for the same on-disk input):
    a corrupt/unparseable ``final_metrics.json`` on a completed claim —
    a truncated JSON body OR non-UTF-8/unreadable bytes (both flavors;
    the tolerance set of the existing-record check below) — flips the
    RECORD to failed with run_sweep's WR-11 error text while the CLAIM
    stays completed (engine semantics untouched — the record never lies
    about unusable metrics); a failed claim yields a failed record
    carrying the claim's own error text with metrics null — failed
    cells are never invisible again.

    Write predicate (WR-12 adapted to dispatch — deliberately STRICTER
    than run_sweep.py:1614, whose ``status != "skipped" or not exists``
    test overwrites ANY existing record, a completed one included, for
    every cell it actually re-runs): an existing record that parses
    with status ``completed`` is NEVER overwritten — a named
    ``FileExistsError`` refusal raises (failing the cell through CR-04)
    so prior provenance survives; any other existing record (a prior
    attempt's FAILED record, or an unparseable file whose provenance is
    unprovable) is replaced atomically — the relaunch/--rerun-failed
    recovery contract. Forcing a retrain of a completed cell therefore
    takes deleting BOTH ``trainer_state.json`` (the resume marker) AND
    ``run_record.json`` by hand — the marker-delete-alone flow that
    suffices under run_matrix meets a loud, tested refusal here.
    Skipped cells never reach this function (the documented, deliberate
    divergence from run_sweep's synthesized skipped records: no record
    is synthesized; ``dispatch_state`` counts report the skip).

    Args:
        cell (tuple): the cell identity (model, task, seed[, fraction]).
        cell_dir (Path | str): the cell's ``cell_dir_for`` directory.
        payload (dict): the FINALIZED-IN-MEMORY claim payload (terminal
            state already assigned; ``finalize_claim`` rewrites the
            claim file right after this call).
        git_commit (str | None): the run's one git-commit observation
            (``context["git_commit"]``, computed once per dispatch run).

    Raises:
        FileExistsError: the record path exists and parses with status
            ``completed`` — completed provenance is never overwritten.
    """
    model, task, seed = cell[0], cell[1], cell[2]
    lane = _claim_lane(payload)
    cell_dir = Path(cell_dir)
    record = run_sweep._new_record(
        model, task, seed, cell_dir, git_commit,
        lane.get("peft") or "none",
        train_fraction=lane.get("train_fraction"),
        config_variant=lane.get("config_variant") or "none",
    )
    if payload.get("state") == CLAIM_STATE_COMPLETED:
        try:
            with open(cell_dir / run_sweep.METRICS_NAME, "r",
                      encoding="utf-8") as handle:
                record["metrics"] = json.load(handle)
            record["status"] = "completed"
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            # WR-11 (the run_sweep.py:1570-1591 parity): the child left
            # a partial file while still exiting 0, so the claim
            # completed on the existence-only CR-02 check — the RECORD
            # reports the honest failure; metrics stay null. The
            # tolerance set matches the existing-record check below:
            # non-UTF-8 bytes raise UnicodeDecodeError (a ValueError,
            # NOT a json.JSONDecodeError) and must land in this branch
            # too — never escape into the CR-04 containment (WR-01).
            record["status"] = "failed"
            record["error"] = (
                "final_metrics.json is corrupt/unreadable "
                f"({exc}); the child left a partial file")
    else:
        # Failed cells get records too (run_matrix parity): the claim's
        # own error text, metrics null.
        record["status"] = "failed"
        record["error"] = payload.get("error")
    record["started_at"] = payload.get("claimed_at")
    record["finished_at"] = payload.get("finished_at")
    # run_matrix always has the cell dir on disk (it mkdirs BEFORE the
    # executor runs); a dispatch child that dies before creating
    # anything — the CR-02 swallow shape — leaves no dir, yet its
    # failed record must still land (mkdir parity, never a second
    # failure mode stacked on the cell's own verdict).
    cell_dir.mkdir(parents=True, exist_ok=True)
    record_path = cell_dir / run_sweep.RECORD_NAME
    if record_path.exists():
        try:
            existing = json.loads(
                record_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            # Unprovable provenance (not a parseable COMPLETED record)
            # — replaceable; the atomic write below surfaces any real
            # I/O failure loudly through CR-04.
            existing = None
        if isinstance(existing, dict) and existing.get(
                "status") == "completed":
            raise FileExistsError(
                f"run_record {record_path} already exists with status "
                "completed — completed provenance is never overwritten "
                "(WR-12; deliberately stricter than run_sweep.py:1614, "
                "which overwrites records of retrained cells); refusing "
                "the cell"
            )
    _atomic_write_json(record_path, record)


def _cell_from_key(cell_key):
    """Rebuild a cell tuple from a claim's JSON cell key.

    Args:
        cell_key: the claim's ``cell`` value (any shape; non-conforming
            shapes return None — the scan never trusts them).

    Returns:
        tuple | None: ``(model, task, seed)`` or ``(model, task, seed,
        fraction)``, or None when the key is not a usable cell identity.
    """
    if not isinstance(cell_key, dict):
        return None
    model = cell_key.get("model")
    task = cell_key.get("task")
    seed = cell_key.get("seed")
    fraction = cell_key.get("fraction")
    if not isinstance(model, str) or not model:
        return None
    if not isinstance(task, str) or not task:
        return None
    if isinstance(seed, bool) or not isinstance(seed, int):
        return None
    if fraction is None:
        return (model, task, seed)
    if isinstance(fraction, bool) or not isinstance(
            fraction, (int, float)):
        return None
    return (model, task, seed, fraction)


def _cell_str(cell):
    """Render one cell tuple for diagnostics (``model/task/seed_N``)."""
    text = f"{cell[0]}/{cell[1]}/seed_{cell[2]}"
    if len(cell) > 3:
        text += f"/frac_{cell[3]}"
    return text


def _validate_rerun_passthrough(passthrough):
    """Validate the raw passthrough tokens of a ``--rerun-failed`` launch.

    The re-run is LEDGER-DRIVEN (D14-05): its scope comes from the
    failed claims and its lane from the claim-time records, so the
    command line may contribute NEITHER. The ONLY accepted token is
    ``--registry-dir`` (space or equals form) — every other token
    refuses with a named message scoping the refusal (T-14-08, the
    Pitfall 5 closure): scoping tokens get the double-scope wording
    (D14-05/MGPU-04), lane tokens the lane-replay wording (D14-06),
    anything else refuses generically.

    Args:
        passthrough (list[str]): the verbatim ``parse_known_args``
            remainder.

    Returns:
        str | None: the ``--registry-dir`` value when given, else None.

    Raises:
        SystemExit: any token other than ``--registry-dir`` (collect-all
        over every offending token).
    """
    problems = []
    registry_dir = None
    tokens = list(passthrough)
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "--registry-dir":
            if index + 1 < len(tokens):
                registry_dir = tokens[index + 1]
                index += 2
                continue
            problems.append(
                "--rerun-failed: --registry-dir requires a value"
            )
            index += 1
            continue
        if token.startswith("--registry-dir="):
            registry_dir = token.split("=", 1)[1]
            index += 1
            continue
        if token in _RERUN_SCOPING_TOKENS:
            problems.append(
                f"--rerun-failed refuses the scoping token {token!r} "
                "(D14-05, MGPU-04): the re-run scope is the ledger's "
                "failed claims across ALL prior runs on the root — "
                "never blend two scoping mechanisms on one command"
            )
        elif token in _RERUN_LANE_TOKENS:
            problems.append(
                f"--rerun-failed refuses the lane token {token!r} "
                "(D14-06): lane flags replay VERBATIM from the "
                "claim-time lane records — pass lane flags on the "
                "ORIGINAL launch, never the re-run"
            )
        else:
            problems.append(
                f"--rerun-failed accepts no passthrough token {token!r} "
                "(only --registry-dir may accompany a re-run)"
            )
        index += 1
    if problems:
        sys.exit(f"[Error] {'; '.join(problems)}")
    return registry_dir


def _scan_failed_claims(ledger_dir):
    """Scan the ledger for failed claims (the MGPU-04 re-run feed).

    Sorted, tolerant, and integrity-checked: corrupt/unreadable claims
    contribute nothing and are never trusted (the ``read_claim``
    contract); a claim qualifies iff its payload ``state`` is
    ``failed`` AND its cell key rebuilds and MATCHES the claim filename
    tuple (``claim_filename``) — a claim whose stored identity
    disagrees with its name is not a runnable cell. Every exclusion is
    NAMED (WR-02, phase-14 review): the recovery tool whose job is
    completeness over the failed set says what it dropped — the
    relaunch path's "never a silent skip" discipline — while the trust
    direction stays fail-safe (an unusable claim is never re-queued,
    never trusted).

    Args:
        ledger_dir (Path): the ledger directory (a missing dir scans to
            empty lists).

    Returns:
        tuple[list, list[str]]: ``(qualified, excluded)`` — the
        ``(cell, payload)`` pairs sorted by filename, plus one
        ``"{name} ({reason})"`` diagnostic per dropped file in scan
        order.
    """
    qualified = []
    excluded = []
    if not ledger_dir.is_dir():
        return qualified, excluded
    for path in sorted(ledger_dir.glob("*.json")):
        if path.name == DISPATCHER_LOCK_NAME:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            excluded.append(f"{path.name} (unreadable/unparseable)")
            continue
        if not isinstance(payload, dict):
            excluded.append(f"{path.name} (payload is not an object)")
            continue
        if payload.get("state") != CLAIM_STATE_FAILED:
            continue
        cell = _cell_from_key(payload.get("cell"))
        if cell is None or claim_filename(cell) != path.name:
            excluded.append(
                f"{path.name} (state failed but the stored cell key "
                "is unusable or disagrees with the filename)")
            continue
        qualified.append((cell, payload))
    return qualified, excluded


def _rerun_lane_refusal(qualified, union_keys):
    """Build the heterogeneous-lane refusal (D14-08, the run_merge shape).

    A flag differs when more than one distinct canonical value appears
    across the failed claims' lanes (compared over the UNION key set —
    an absent key reads as None, matching its replay semantics; the
    per-cell ``train_fraction`` is cell identity, not lane, and is
    excluded). The refusal names, PER CELL, each differing flag and
    that cell's value — the collect-all discipline over every differing
    flag.

    Args:
        qualified (list[tuple]): the ``(cell, payload)`` scan result.
        union_keys (list[str]): the sorted union of lane keys across
            the qualified claims (minus ``train_fraction``).

    Returns:
        str: the ``[Error] ...`` message for ``sys.exit``.
    """
    lanes = [(cell, _claim_lane(payload)) for cell, payload in qualified]
    problems = []
    for flag in union_keys:
        values = {
            run_sweep_shard._canonical_lane_value(lane.get(flag))
            for _cell, lane in lanes}
        if len(values) > 1:
            listed = "; ".join(
                f"{_cell_str(cell)} = "
                f"{'<absent>' if lane.get(flag) is None else lane.get(flag)!r}"
                for cell, lane in lanes)
            problems.append(
                f"lane flag '{flag}' differs across the failed cells — "
                f"{listed} (unequal lanes are different experiments, "
                "D14-08; re-run one lane at a time or fix the ledger)"
            )
    return f"[Error] {'; '.join(problems)}"


def _run_rerun_failed(args, passthrough, spawner, clock, workers, gpus):
    """The MGPU-04 ledger-driven failure re-run (14-03, D14-05..D14-08).

    Reached from ``run_dispatch`` BEFORE the ``--models`` requirement
    and WITHOUT ``parse_sweep_remainder`` (Pitfall 7: the failed claims
    define models AND seeds — a re-run launch needs neither flag and
    must not die the argparse-code-2 ``--seeds`` death). Protocol:
    validate the raw passthrough (only ``--registry-dir`` accepted)
    -> scan the ledger for failed claims (a ZERO-failed root prints the
    explicit no-failed-cells verdict and returns exit 0 — the
    drained-root precedent, A7; unusable claims are excluded BY NAME,
    never silently — WR-02, phase-14 review) -> registry-join every
    failed cell's BASE model name (fail-safe, T-14-07) -> refuse
    heterogeneous lane
    signatures (D14-08) -> mirror the ordinary startup validation
    family over the replayed lane (WR-03, phase-14 review: the subset
    map and the registry-name alignment, BEFORE any launch — never one
    burned child per cell) -> marker-vs-failed precedence per cell (the
    Phase 13 D-06 adjacency: a failed cell that later gained the
    ``trainer_state.json`` marker is SKIPPED, never re-run) -> replay
    through the ordinary launch machinery with the claim-time lane.

    Args:
        args (argparse.Namespace): the parsed SHARD flags (output_root,
            rerun_failed).
        passthrough (list[str]): the verbatim remainder (only
            ``--registry-dir`` accepted).
        spawner: injectable spawner seam (None uses ``Popen``).
        clock: injectable ``datetime.now``-shaped seam.
        workers (int): the validated ``--workers`` count.
        gpus (list[str] | None): the parsed ``--gpus`` tokens.

    Returns:
        None: via ``_launch_and_drain`` (exits 1 on failed cells).

    Raises:
        SystemExit: passthrough refusals, registry-join refusals, the
        heterogeneous-lane refusal, the startup-validation refusals
        (WR-03), and the launch machinery's own.
    """
    output_root = Path(args.output_root).resolve()
    registry_arg = _validate_rerun_passthrough(passthrough)
    registry_dir = (
        Path(registry_arg).resolve() if registry_arg
        else run_sweep.PIPELINE_DIR)
    ledger_dir = ledger_dir_for(output_root)

    qualified, excluded = _scan_failed_claims(ledger_dir)
    if excluded:
        # WR-02 (phase-14 review): name every dropped claim — a failed
        # cell whose claim is corrupt (disk fault, hand tampering) must
        # not vanish from the re-run feed without a trace, the relaunch
        # counterpart's "never a silent skip" discipline (still never
        # re-queued: the trust direction stays fail-safe).
        print(
            f"[Rerun] [Skip] {len(excluded)} unusable claim(s) excluded "
            f"from the re-run feed: {'; '.join(excluded)}"
        )
    if not qualified:
        # A7 ruling (Pitfall 7): the drained-root precedent — an
        # explicit verdict and exit 0, never a fall-through into
        # full-matrix enumeration. With exclusions the verdict names the
        # distinction (WR-02): "no failed claims" and "only unusable
        # claims" are different operator realities.
        if excluded:
            print(
                f"[Dispatch] no failed cells to re-run on {output_root} "
                "— the ledger holds 0 usable failed claim(s) "
                f"({len(excluded)} excluded as unusable, named above); "
                "nothing spawned"
            )
        else:
            print(
                f"[Dispatch] no failed cells to re-run on {output_root} — "
                "the ledger holds no failed claims; nothing spawned"
            )
        return

    # Registry join (fail-safe, T-14-07): a forged or renamed claim
    # cannot widen scope silently — every failed cell's model resolves
    # to its BASE registry name through the claim's OWN lane (the CR-01
    # ``base_model_name`` join discipline, not the manifest reader).
    run_sweep._validate_filters(
        sorted({
            run_sweep.base_model_name(
                cell[0], _claim_lane(payload).get("peft") or "none",
                _claim_lane(payload).get("config_variant") or "none")
            for cell, payload in qualified}),
        sorted({cell[1] for cell, _payload in qualified}),
        registry_dir)

    # Lane homogeneity (D14-08): the replay set must share ONE lane
    # signature — canonicalized with the run_merge discipline
    # (deterministic sorted-JSON, never set-iteration order). The
    # comparison universe is the UNION of lane keys across the failed
    # claims (minus the per-cell train_fraction), with every lane
    # projected onto that key set: an ABSENT key and a key recorded as
    # None replay identically (zero argv elements, the Pitfall 4
    # absent-parity discipline), so they must COMPARE identically too —
    # a Phase-13 five-key lane beside a Phase-14 nine-key lane with
    # equal values is ONE lane, never a refusal.
    union_keys = sorted(
        {key for _cell, payload in qualified
         for key in _claim_lane(payload)} - {"train_fraction"})
    signature_groups = {}
    for cell, payload in qualified:
        lane = _claim_lane(payload)
        signature = {key: lane.get(key) for key in union_keys}
        signature_groups.setdefault(
            run_sweep_shard._canonical_lane_value(signature),
            (lane, []))[1].append(cell)
    if len(signature_groups) > 1:
        sys.exit(_rerun_lane_refusal(qualified, union_keys))
    agreed_lane = next(iter(signature_groups.values()))[0]

    # WR-03 (phase-14 review): mirror the ordinary path's startup
    # validation family over the REPLAYED lane before any launch. The
    # re-run previously joined the registry and proceeded straight to
    # ``_launch_and_drain``, so a subset map deleted since the original
    # run (or a registry whose Dataset_name rows diverged since) burned
    # one child per cell at the child's own per-cell validation,
    # recording N failed claims — the exact phase-13 WR-01
    # burned-children hazard, on the recovery path, repeatable by
    # re-running ``--rerun-failed`` (the claims stay failed). The view
    # is the CURRENT registry — the same one the join above used
    # (T-14-07) — so validating the replayed map against it is
    # consistency, not a fidelity break.
    registry_view = registry_loader.load_datasets_registry(registry_dir)
    replayed_subset = agreed_lane.get("subset_file")
    if replayed_subset is not None:
        run_sweep._validate_subset_file(replayed_subset, registry_view)
    run_sweep._validate_dataset_name_alignment(registry_view)

    # Archive-collision adjacency (D14-07): the archive for an original
    # attempt is O_EXCL and append-only — one already existing while
    # the canonical slot still names the SAME run_id (a crash between
    # the archive create and the canonical overwrite, or manual
    # tampering) refuses loudly BEFORE any spawn, by name. The
    # worker's own O_EXCL create remains the structural backstop
    # (T-14-06) for anything the pre-check cannot see.
    collisions = []
    for cell, payload in qualified:
        original_run = payload.get("run_id")
        if not isinstance(original_run, str) or not original_run:
            continue  # the worker's genealogy step refuses this loudly
        expected = (
            Path(ledger_dir) / ARCHIVE_DIR_NAME
            / _archive_filename(cell, original_run))
        if expected.is_file():
            collisions.append(
                f"archive for cell {_cell_str(cell)} (run "
                f"{original_run[:8]}) already exists at {expected} — "
                "the ledger's audit history is append-only and never "
                "overwritten (D14-07); refusing the re-run"
            )
    if collisions:
        sys.exit(f"[Error] {'; '.join(collisions)}")

    # The launch lane from the ONE agreed signature — tolerant reads
    # (Pitfall 4): a pre-Phase-14 claim lacking cache_dir (or any later
    # lane key) replays with the flag ABSENT — zero argv elements, the
    # build_argv absent-parity discipline, never a KeyError, never a
    # refusal.
    lane_values = {
        "peft": agreed_lane.get("peft") or "none",
        "config_variant": agreed_lane.get("config_variant") or "none",
        "subset_file": agreed_lane.get("subset_file"),
        "effective_batch_size": agreed_lane.get("effective_batch_size"),
        "batch_size": agreed_lane.get("batch_size"),
        "num_train_epochs": agreed_lane.get("num_train_epochs"),
        "cache_dir": agreed_lane.get("cache_dir"),
        "model_root": agreed_lane.get("model_root"),
        "dataset_root": agreed_lane.get("dataset_root"),
        "log_dir": agreed_lane.get("log_dir"),
    }

    # Marker-vs-failed precedence per qualified cell: the scan already
    # proved the claim says failed; ``relaunch_decision`` adds the
    # marker layer (a failure whose cell completed since — e.g. a plain
    # relaunch finished it — is SKIPPED, the marker stays authoritative
    # and is never re-run).
    pending = []
    skipped = 0
    for cell, _payload in qualified:
        if relaunch_decision(
                output_root, ledger_dir, cell) == _DECISION_SKIP:
            skipped += 1
        else:
            pending.append((cell, _TAG_RERUN))
    return _launch_and_drain(
        output_root, [cell for cell, _payload in qualified], pending,
        skipped, lane_values, workers, gpus, spawner, clock)


def _launch_and_drain(output_root, cells, pending, skipped, lane_values,
                      workers, gpus, spawner, clock):
    """LOCK -> MODE EVIDENCE -> skip filter -> drain -> verdicts.

    The shared post-validation launch machinery for BOTH dispatch entry
    paths: the ordinary enumerated run (``pending=None`` — the relaunch
    skip filter runs HERE, after the mode-evidence write, preserving the
    render progression the 14-01 pins observe) and the MGPU-04 re-run
    (``pending`` precomputed by ``_run_rerun_failed`` with
    ``_TAG_RERUN`` tags and the marker-skips already counted).

    Args:
        output_root (Path): the RESOLVED shared output root.
        cells (list[tuple]): every cell in this launch's scope (the
            ``counts.total`` ground truth).
        pending (list | None): precomputed ``(cell, tag)`` entries, or
            None to derive them here via the relaunch skip filter.
        skipped (int): the precomputed ``counts.skipped`` seed (0 for
            the ordinary path — its filter counts its own).
        lane_values (dict): the launch lane flags — the keys of the
            claim-time lane dict (peft, config_variant, subset_file,
            effective_batch_size, batch_size, num_train_epochs,
            cache_dir,
            model_root, dataset_root, log_dir); recorded verbatim into
            every claim and replayed into ``build_argv``.
        workers (int): the validated ``--workers`` count.
        gpus (list[str] | None): the parsed ``--gpus`` tokens (None
            defaults to one index-string per worker).
        spawner: injectable spawner seam (None uses ``Popen``).
        clock: injectable ``datetime.now``-shaped seam (ONE call names
            every worker tee log stamp, WR-02).

    Raises:
        SystemExit: the singleton-lock refusal, the tee-open refusal,
        the post-join accounting refusal, or exit 1 on failed cells.
    """
    # LOCK -> MODE EVIDENCE -> QUEUE (the module docstring's protocol)
    ledger_dir = ledger_dir_for(output_root)
    ledger_dir.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex
    started_at = _now_iso()
    # ONE git-commit observation per dispatch run (the run_matrix
    # parity: run_sweep.run_matrix calls _git_commit() once per run,
    # never per cell) — every run_record this run writes carries the
    # same commit (15-04).
    git_commit = run_sweep._git_commit()
    lock_path = acquire_dispatcher_lock(ledger_dir, run_id, started_at)
    seam = subprocess.Popen if spawner is None else spawner
    state_path = output_root / DISPATCH_STATE_NAME
    # Default GPU assignment (operator-owned strings; no probing, D-05)
    # resolves BEFORE the state build: the v2 consumer payload names one
    # gpu per worker row from the very first write on.
    if gpus is None:
        gpus = [str(i) for i in range(workers)]
    counts = {
        "total": len(cells),
        "completed": 0,
        "failed": 0,
        "skipped": skipped,
    }
    worker_stats = {
        i: {"cells": 0, "completed": 0, "failed": 0}
        for i in range(workers)}
    state = {
        "schema_version": DISPATCH_STATE_SCHEMA_VERSION,
        "mode": "dispatch",
        "run_id": run_id,
        "status": "running",
        "started_at": started_at,
        "updated_at": started_at,
        "counts": dict(counts),
        # ---- Phase 14 additive consumer fields (D14-01, schema v2;
        #      frozen in schemas/dispatch_state.json — every v1 key is
        #      present unchanged) ----
        "queue_depth": counts["total"],
        "workers": [
            {
                "index": i,
                "gpu": gpus[i],
                "in_flight": None,
                "cells": 0,
                "completed": 0,
                "failed": 0,
            }
            for i in range(workers)
        ],
        "failures": [],
    }
    context = {
        "root": output_root,
        "ledger_dir": ledger_dir,
        "run_id": run_id,
        "git_commit": git_commit,
        "state_path": state_path,
        "state": state,
        "counts": counts,
        "pending": pending if pending is not None else [],
        "queue_lock": threading.Lock(),
        "state_lock": threading.Lock(),
        "worker_stats": worker_stats,
        "in_flight": {i: None for i in range(workers)},
        "gpus": gpus,
        "spawner": seam,
        "peft": lane_values.get("peft") or "none",
        "config_variant": lane_values.get("config_variant") or "none",
        "subset_file": lane_values.get("subset_file"),
        "effective_batch_size": lane_values.get("effective_batch_size"),
        "batch_size": lane_values.get("batch_size"),
        "num_train_epochs": lane_values.get("num_train_epochs"),
        "cache_dir": lane_values.get("cache_dir"),
        "model_root": lane_values.get("model_root"),
        "dataset_root": lane_values.get("dataset_root"),
        "log_dir": lane_values.get("log_dir"),
        "lane": dict(lane_values),
    }
    # WR-01 (phase-14 review): this write and the two below run AFTER
    # the lock is acquired but BEFORE the drain's try/finally guarantees
    # its release — route them through the guard that releases + exits
    # with the designed diagnostic on an I/O failure (never a raw
    # traceback leaking dispatcher.lock on disk).
    # BEFORE any claim (mode evidence).
    _publish_state_pre_drain(context, lock_path)

    if pending is None:
        # Relaunch skip filter (the module docstring's step 4): skip iff
        # the marker exists (authoritative, D-06) OR the ledger says
        # completed; a stale claim (claimed/failed from a dead run)
        # requeues. Purely per-cell, so the skip set is
        # order-independent by construction.
        for cell in cells:
            decision = relaunch_decision(output_root, ledger_dir, cell)
            if decision == _DECISION_SKIP:
                counts["skipped"] += 1
            else:
                context["pending"].append((cell, decision))
        # Still BEFORE any claim/spawn.
        _publish_state_pre_drain(context, lock_path)

    now = datetime.now if clock is None else clock
    launch_stamp = now().strftime(
        run_sweep_shard.WORKER_LOG_TIMESTAMP_FORMAT)

    if not context["pending"]:
        # The relaunch half of the zero-cell decision (EDGE
        # MGPU-02/empty): a fully drained root is an explicit
        # nothing-to-do verdict and exit 0 — never a re-spawn storm.
        state["status"] = "done"
        _publish_state_pre_drain(context, lock_path)
        release_dispatcher_lock(lock_path)
        print(
            f"[Dispatch] nothing to do — all {len(cells)} enumerated "
            f"cell(s) are already complete on {output_root}; no workers "
            "spawned"
        )
        return

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

    # CR-04 (phase-13 review): post-join accounting assertion — every
    # enumerated cell must be accounted for (completed + failed + skipped
    # == total) BEFORE any success path. A worker thread that dies
    # despite the per-cell containment in _spawn_worker (e.g. the
    # containment's own state write hitting ENOSPC) leaves cells
    # popped-but-unaccounted; printing the verdict table, writing
    # status "done", and exiting 0 there would be a false success on
    # the orchestrator's error path (automation sees success and never
    # relaunches). Refuse loudly with an honest "incomplete" status.
    drained = (
        counts["completed"] + counts["failed"] + counts["skipped"])
    if drained != counts["total"]:
        state["status"] = "incomplete"
        _publish_state(context)
        sys.exit(
            f"[Error] dispatch accounting mismatch: {drained}/"
            f"{counts['total']} cells accounted for — a worker died "
            "unexpectedly; unrun cells remain queued in the ledger"
        )

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
    _publish_state(context)
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


def run_dispatch(args, passthrough, spawner=None, clock=None):
    """The dispatch engine entry (routed from ``run_sweep_shard.main``).

    Protocol (the module docstring's strict order): validate + enumerate
    (zero-cell refusal BEFORE the lock) -> [``--dry-run``: write ONLY the
    plan manifest and return] -> mkdir ledger -> singleton lock
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

    Re-run branch (14-03, MGPU-04): when ``args.rerun_failed`` is set
    the engine routes into ``_run_rerun_failed`` AFTER the
    ``--workers``/``--gpus`` validation but BEFORE the ``--models``
    requirement and WITHOUT re-parsing the remainder — the ledger's
    failed claims define the scope (models AND seeds), the claim-time
    lane replays verbatim, and the original claims are archived (see
    the module docstring's failure-re-run paragraph).

    Args:
        args (argparse.Namespace): the parsed SHARD flags (workers, gpus,
            models, output_root, mode, rerun_failed).
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
    if getattr(args, "rerun_failed", False):
        # 14-03 (MGPU-04, D14-05): the ledger-driven re-run branch —
        # BEFORE the --models requirement refusal below and WITHOUT
        # parse_sweep_remainder (Pitfall 7): the failed claims define
        # models AND seeds, so a re-run launch needs NEITHER flag and
        # must not die the argparse-code-2 --seeds death. The
        # --workers/--gpus validation above applies unchanged.
        if problems:
            sys.exit(f"[Error] {'; '.join(problems)}")
        return _run_rerun_failed(
            args, passthrough, spawner=spawner, clock=clock,
            workers=workers, gpus=gpus)
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
    # batch_size >= 1 (261023-abu),
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
    if sweep_args.batch_size is not None and \
            sweep_args.batch_size < 1:
        problems.append(
            f"--batch_size must be >= 1, got {sweep_args.batch_size}"
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

    # WR-01 (phase-13 review): pre-validate the subset map ONCE at
    # dispatch start — the D-14 collect-all mirror run_sweep.main
    # performs (run_sweep.py:1860-1869) — against the same
    # overlay-merged registry view the matrix enumeration joins on. A
    # bad map (unreadable, non-object, unknown task keys, non-integer
    # IDs) refuses HERE by name, before anything touches the root —
    # never one burned child launch per cell recorded as N cell
    # failures. The child's validate_subset_file re-check per cell
    # stays authoritative (defense-in-depth, not a shared import).
    if subset_file_abs is not None:
        run_sweep._validate_subset_file(
            subset_file_abs,
            registry_loader.load_datasets_registry(registry_dir))

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
    # CR-01 (phase-13 review): --from-failures is HONORED, never
    # accept-and-ignored. The remainder re-parse accepts the flag, so a
    # silent no-op here meant a typo'd manifest never validated AND a
    # dispatch scoped by a failures manifest silently ran the FULL filter
    # matrix (the exact WR-07 hazard the zero-cell refusal below exists
    # to prevent). Mirrors run_sweep.main verbatim: the manifest
    # validates loudly through run_sweep.load_failure_pairs (the same
    # collect-all refusal every run_sweep launch performs), then the
    # filter joins on BASE model names across the requested seeds. A
    # clean manifest filters to zero cells and the zero-cell refusal
    # below catches it BY NAME — an explicit zero-cell run, never a
    # silent full sweep.
    failure_pairs = None
    if sweep_args.from_failures is not None:
        failure_pairs = run_sweep.load_failure_pairs(
            sweep_args.from_failures, registry_dir)
    if failure_pairs is not None:
        if failure_pairs:
            print(
                f"[From-failures] {len(failure_pairs)} failed (model, "
                f"task) pair(s) in {sweep_args.from_failures}; enumerating "
                "their cells across the requested seeds"
            )
        else:
            # A clean manifest is a legitimate outcome (the sweep
            # completed) — mirrored message: explicit zero-cell run, NOT
            # a full sweep.
            print(
                f"[From-failures] {sweep_args.from_failures} is clean (0 "
                "failed pairs) — explicit zero-cell run, NOT a full sweep"
            )
        cells = [
            cell for cell in cells
            if (run_sweep.base_model_name(
                    cell[0], sweep_args.peft, config_variant), cell[1])
            in failure_pairs
        ]
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

    if args.dry_run:
        # The dry-run plan artifact (13-02, SC1 / MGPU-01's dry-run-
        # provable enumeration): mirror the static dry-run projection
        # EXACTLY (run_sweep.py:1909-1946) so ONE manifest shape spans
        # both modes — planned cells carry status "planned" (never
        # terminal in the 11-04 scanner semantics: planned never counts
        # as done, T-13-07) and output_dir at the cell_dir_for path
        # under the ONE shared root. The sweep_flags dict mirrors
        # run_sweep.main's present-keys-only construction verbatim
        # (subset_file / effective_batch_size / batch_size /
        # num_train_epochs /
        # cache_dir / model_root / dataset_root / log_dir /
        # config_variant; peft does NOT join — it rides the ALIAS
        # identities, only config_variant joins among the two lane
        # axes) PLUS one extra "orchestrator_mode": "dispatch" marker —
        # the A7 dry-run-root evidence the merge refusal reads (real
        # runs carry dispatch_state.json instead). The branch sits
        # AFTER the zero-cell refusal, so an empty enumeration refuses
        # identically dry or real, and BEFORE the lock: NO lock, NO
        # state file, NO claims, NO tees, NO spawns (the run_sweep
        # dry-run contract, mirrored — the root gains ONLY
        # sweep_manifest.json).
        sweep_flags = {}
        if subset_file_abs is not None:
            sweep_flags["subset_file"] = subset_file_abs
        if sweep_args.effective_batch_size is not None:
            sweep_flags["effective_batch_size"] = (
                sweep_args.effective_batch_size)
        if sweep_args.batch_size is not None:
            sweep_flags["batch_size"] = sweep_args.batch_size
        if sweep_args.num_train_epochs is not None:
            sweep_flags["num_train_epochs"] = sweep_args.num_train_epochs
        if cache_dir_abs is not None:
            sweep_flags["cache_dir"] = cache_dir_abs
        if model_root_abs is not None:
            sweep_flags["model_root"] = model_root_abs
        if dataset_root_abs is not None:
            sweep_flags["dataset_root"] = dataset_root_abs
        if log_dir_abs is not None:
            sweep_flags["log_dir"] = log_dir_abs
        if sweep_args.config_variant is not None:
            sweep_flags["config_variant"] = sweep_args.config_variant
        sweep_flags["orchestrator_mode"] = "dispatch"
        matrix = {
            "models": sorted({cell[0] for cell in cells}),
            "tasks": sorted({cell[1] for cell in cells}),
            "seeds": sorted({cell[2] for cell in cells}),
            "output_root": str(output_root),
        }
        planned_records = [
            {
                "model": cell[0],
                "task": cell[1],
                "seed": cell[2],
                "status": "planned",
                "output_dir": str(run_sweep.cell_dir_for(
                    output_root, cell[0], cell[1], cell[2],
                    cell[3] if len(cell) > 3 else None)),
            }
            for cell in cells
        ]
        output_root.mkdir(parents=True, exist_ok=True)
        run_sweep._write_json(
            output_root / run_sweep.MANIFEST_NAME,
            run_sweep._manifest_payload(
                matrix, planned_records, sweep_flags),
        )
        print(
            f"[Dry-run] [Dispatch] {len(cells)} planned cell(s) over "
            f"{len(matrix['models'])} model(s) x {len(matrix['tasks'])} "
            f"task(s) x {len(matrix['seeds'])} seed(s); manifest: "
            f"{output_root / run_sweep.MANIFEST_NAME}"
        )
        return

    # LOCK -> MODE EVIDENCE -> QUEUE -> drain, through the shared
    # launch machinery (the 14-03 extraction — the MGPU-04 re-run
    # replays through the identical worker loops). The claim-time lane
    # dict now carries cache_dir (the D14-06 gap) plus the three
    # storage roots (the A8 ruling) — additive keys, recorded for
    # replay fidelity and replayed tolerantly.
    lane_values = {
        "peft": sweep_args.peft,
        "config_variant": config_variant,
        "subset_file": subset_file_abs,
        "effective_batch_size": sweep_args.effective_batch_size,
        "batch_size": sweep_args.batch_size,
        "num_train_epochs": sweep_args.num_train_epochs,
        "cache_dir": cache_dir_abs,
        "model_root": model_root_abs,
        "dataset_root": dataset_root_abs,
        "log_dir": log_dir_abs,
    }
    return _launch_and_drain(
        output_root, cells, None, 0, lane_values, workers, gpus,
        spawner, clock)
