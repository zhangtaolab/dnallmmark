"""
Multi-worker sweep orchestration: launch mode (12-01, MGPU-01/SC1, D-07)
+ merge mode (12-04, MGPU-02 artifact half, D-09).

``run_sweep.py`` drives ONE sweep over a model x task x seed matrix on
one GPU. This orchestrator scales throughput out to N GPUs by partitioning
the requested BASE models into N disjoint shards and launching one
ordinary ``run_sweep.py`` subprocess per shard, each pinned to exactly one
GPU via ``CUDA_VISIBLE_DEVICES`` and each writing under its OWN frozen
output root. Per D-07 this is a NEW entry: ``run_sweep.py`` and
``run_finetune.py`` stay byte-untouched (their argv surface is frozen by
the tier-1 suite and the TUI composer), and the orchestrator COMPOSES —
it imports ``run_sweep`` / ``registry_loader`` as sibling modules and
never re-implements enumeration, argv building, or validation.

Invocation (run from anywhere; each worker's cwd is pinned internally to
``pipeline/`` — run_sweep's own documented cwd contract)::

    python pipeline/run_sweep_shard.py --workers 2 \
        --models plant-dnabert-6mer,GENERanno-eukaryote-0.5b-base \
        --tasks GUE__emp_H3 --seeds 42,43 --output-root ./finetuned

MERGE MODE (12-04, D-09) — after the N workers finish, union their
frozen roots into ONE verified consumer root::

    python pipeline/run_sweep_shard.py --merge --workers 2 \
        --output-root ./finetuned

Semantics: the merge reads every frozen-named worker root (the SAME
``worker_root()`` the launch path used — one naming authority, so launch
and merge can never disagree about where worker artifacts live) and
copies each cell's DATA-ARTIFACT allowlist (``MERGE_ALLOWLIST``:
run_record / final_metrics / trainer_state / seed_result / flops_report,
plus ``frac_*/`` recursion for curve cells) into the merged root with
COPY + SHA256-VERIFY per file — hash, copy, re-hash, compare; any
mismatch refuses the whole merge BEFORE the merged manifests land. Never
a symlink (symlinks break when worker roots are cleaned and do not
survive cross-host copies), never a move (a move would destroy the
worker root's re-runnability). ``checkpoint-*/`` and ``runs/`` trees are
EXCLUDED by default and copy only under the explicit
``--include-checkpoints`` escape hatch (research A2: checkpoints are
worker resume state; verified consumers read only the JSONs). The merged
``sweep_manifest.json`` unions every worker's cells with each
``output_dir`` REWRITTEN onto the merged root (leaving worker paths
dangles them after runbook cleanup — Pitfall 5), unions
matrix.models/tasks/seeds, and unions ``sweep_failures.json`` with the
same rewrite. LANE FLAGS (every cell key outside the identity
projection — peft/config_variant/num_train_epochs/subset_file/
effective_batch_size/cache_dir as recorded via sweep_flags) must be
EQUAL across worker manifests: a mismatch is a collect-all DIAGNOSTIC
listing the differing value per root per flag, never a silent
pick-first (Pitfall 6 — merging a lora worker with a base worker is a
different experiment than either). Cleanup: the merge NEVER mutates a
worker root and NEVER deletes anything — workers stay re-runnable in
isolation (D-08) until the maintainer deletes them post-merge, an
explicit runbook step taken only after the merged root is verified.
gen_progress warning (the generator's own docstring repeats it): NEVER
pass worker roots AND their merged root together — every cell would
appear twice; worker roots for the live view, the merged root alone for
the post-run view.

CLEANUP MODE (14-02, MGPU-05, D14-09..D14-12) — after the merge is
verified, remove the worker roots safely (replacing the manual
``rm -rf`` runbook step, docs/multi-gpu.md)::

    python pipeline/run_sweep_shard.py --cleanup --workers 2 \
        --output-root ./finetuned --yes /abs/resolved/finetuned

Semantics: verify, then offer removal behind an exact typed phrase.
Leg A runs ``script/export_runs.py --dry-run`` as a SUBPROCESS over the
merged root (never an import — export_runs pulls numpy/yaml/scipy at
module top; this orchestrator stays stdlib-headless); leg B requires
the merged manifest's ``(model, task, seed)`` cell set to EQUAL the
union of the worker manifests' (both truths must hold: a manifest can
lie about a tree the exporter walks, and a tree can hide cells the
manifest omits — Pitfall 6's false-green). Only then is the removal
plan printed — every existing ``worker_root()`` sibling root plus its
``{base}-mgpu-w{i}-*.log`` per-launch logs (the Q5 ruling: the full
manual recipe, roots AND logs) — and only the exact typed phrase (the
resolved ``--output-root`` string) authorizes removal of exactly those
listed paths. The merged root is NEVER a removal target; dispatch
roots refuse with a named needs-no-cleanup error before any
verification. ``--gpus`` is meaningless in cleanup mode and ignored.

Every token the orchestrator does not own (``--tasks``, ``--seeds``,
``--peft``, ``--num_train_epochs``, ``--registry-dir``, ...) is passed
through VERBATIM to every worker after the orchestrator's own flags —
``run_sweep.py`` stays the single owner of sweep-flag validation and
help. Task/seed flag problems therefore surface INSIDE each worker at
its own startup and are reported in this orchestrator's verdict table
(a worker that dies at argv validation exits non-zero like any other
dead worker). In merge mode the passthrough remainder must be EMPTY (a
merge takes no sweep flags) and ``--models`` is not required (the
worker manifests are the merge's source of truth).

Frozen naming (ONE authority — the merge mode imports these exact
functions, so launch and merge can never disagree about where worker
artifacts live)::

    worker root: {output-root}-mgpu-w{i}      (a SIBLING of the base root)
    worker log:  {output-root}-mgpu-w{i}-{launch-stamp}.log  (one file per
                 launch — the launcher's tee idiom, WR-02: a resume
                 relaunch never truncates the prior crash log)

Disjointness proof, three lines (D-06 — the concurrency invariant):

1. A worker writes only under its own root: every run_sweep write target
   derives from ``cell_dir_for`` = ``{root}/{model}/{task}/seed_{seed}/``
   or is one of the two ROOT-LEVEL manifests.
2. The root-level ``sweep_manifest.json`` / ``sweep_failures.json`` are
   why shared roots are FORBIDDEN, not merely sloppy: two workers on one
   root would collide last-writer-wins over both files even with
   perfectly disjoint model sets (research Pitfall 1) — hence the frozen
   sibling roots and the orchestrator's refusal of any configuration
   where a worker root would alias the base root or another worker root.
3. Worker i's root differs from worker j's by construction, so no path
   at any depth is ever shared; marker-skip (``trainer_state.json``) is
   the ONLY concurrency/resume guard and needs no locks, claim files, or
   ports (D-06 LOCKED — disjointness is the static guarantee, the marker
   is the resume backstop).

Process semantics (the ``sweep_launcher._spawn`` discipline, copied
VERBATIM plus exactly one added env key):

- Each worker is spawned with ``start_new_session=True`` — its own
  process group and session. Ctrl-C on the orchestrator therefore does
  NOT kill the workers (they are resume-safe via the marker; this is by
  design, A4). To stop ONE worker::

      kill -TERM -$(ps -o pgid= -p <worker pid> | tr -d ' ')

  (the killpg recipe: signal the worker's whole process group so its
  run_finetune children die with it).
- ``env`` is an explicit ``{**os.environ, "PYTHONUNBUFFERED": "1",
  "CUDA_VISIBLE_DEVICES": str(gpu_i)}`` copy — the ONLY delta from the
  launcher is the CUDA key. The isolation chain is inherited end-to-end:
  run_sweep spawns run_finetune with no ``env`` kwarg (verbatim
  inheritance) and never touches ``CUDA_VISIBLE_DEVICES`` itself, so
  torch sees exactly the one GPU this env names.
- ``CUDA_VISIBLE_DEVICES`` values are OPERATOR-OWNED strings: the
  orchestrator validates ARITY only (``--gpus`` element count ==
  ``--workers``) and never probes nvidia-smi or assumes any device
  count (D-05 — this module must stay CPU-testable; GPU assignment is
  CLI input, not runtime discovery).
- Worker stdout/stderr tee into the per-launch timestamped sibling log
  (``{base}-mgpu-w{i}-{stamp}.log`` — the launcher's own tee idiom,
  WR-02: a resume relaunch writes a NEW log instead of truncating the
  crash evidence; stderr is redirected onto stdout's handle); the
  orchestrator waits ALL workers and reports an aggregated verdict —
  exit 0 iff every worker exited 0, otherwise exit 1 after a
  per-worker verdict table (exit code, worker root, log path,
  failed-cell count read from that worker's ``sweep_failures.json``
  when present). A dead worker never touches its siblings:
  independent sessions + disjoint roots (SC2).

Sharding: LPT (longest-processing-time-first) by the registry's
``size (M)`` — models sorted size-descending (registry-name ascending
tie-break), each assigned to the worker with the least accumulated size
(lowest worker index tie-break). Deterministic, disjoint by
construction, and a good-enough static load proxy because every worker
runs the SAME task set, so model size dominates the per-worker
differential (research A1; ``--models`` remains the manual override when
the operator knows better). A registry entry with a missing or
non-numeric ``size (M)`` shards with weight 0.0 — never a crash (the
custom-entries reality).

Validation is collect-all fail-fast (the ``_validate_filters``
discipline): ``--workers < 1``, malformed/arity-mismatched ``--gpus``, a
provided-but-empty ``--models`` value, unknown model names vs the
registry, ``--workers`` exceeding the requested model count (empty
shards would spawn no-op workers writing fresh empty manifests), and any
frozen-root collision are ALL listed together, then the orchestrator
exits non-zero before a single worker spawns.

E2' boundary note: the TUI's typed-phrase gate is a TUI-composed-path
structural feature; the CLI — ``run_sweep.py`` today, this orchestrator
now — is the maintainer trust surface and deliberately carries NO such
gate. The full statement lives in ``docs/multi-gpu.md`` (12-04).

N>1 GPU validation runs on the other machine per D-05 (documented
procedure, never a CI lane); this host proves the orchestration CPU-side
via the injectable spawner seam, in-process dry-runs, and real
``--dry-run`` subprocess chains — never real training, never N>1 GPUs.

See also:
    ``pipeline/run_sweep.py`` — the single-sweep driver each worker is
    an ordinary invocation of (enumerate_matrix, the --models filter,
    the cwd contract).
    ``tui/services/sweep_launcher.py`` — the launch discipline this
    module copies verbatim (``_spawn``).
    ``tests/test_sweep_shard.py`` — the tier-1 contract tests.
"""

import argparse
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import registry_loader  # sibling module (pipeline/ on sys.path)
import run_sweep  # sibling module: PIPELINE_DIR + the worker entry

WORKER_SCRIPT = run_sweep.PIPELINE_DIR / "run_sweep.py"

#: Per-launch worker-log timestamp format — the ``sweep_launcher``
#: ``TEE_TIMESTAMP_FORMAT`` discipline: every (re)launch derives a FRESH
#: tee filename, so the documented resume relaunch (a worker dies;
#: relaunch the orchestrator — workers are resume-safe via the marker,
#: A4/D-08) never opens the previous launch's crash log with ``"w"`` and
#: truncates the exact evidence that explains the crash (WR-02).
WORKER_LOG_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# The injectable spawner seam (the sweep_launcher :475 idiom): tests run
# CPU-only by injecting a fake; the real path is Popen with the launcher's
# verbatim kwargs plus the one CUDA_VISIBLE_DEVICES env key.
_DEFAULT_SPAWNER = subprocess.Popen


def worker_root(base_root, index):
    """Return the frozen per-worker output root — a SIBLING of the base
    root: ``{base}-mgpu-w{index}``.

    Defined ONCE here as the single naming authority: 12-04's --merge
    imports this function, so launch and merge can never disagree about
    where worker artifacts live.

    Args:
        base_root (Path | str): the RESOLVED base output root.
        index (int): the worker index (0-based).

    Returns:
        Path: ``{base}-mgpu-w{index}`` (not created here).
    """
    base = Path(base_root)
    return Path(f"{base}-mgpu-w{index}")


def worker_log_path(base_root, index, timestamp):
    """Return the per-launch worker tee log path — a timestamped
    ``.log`` SIBLING of the worker root.

    ``{base}-mgpu-w{index}-{timestamp}.log`` — the sweep_launcher's
    per-launch tee discipline (WR-02): the worker ROOT naming stays the
    single frozen authority for where worker artifacts live, while the
    LOG gets one file per launch so a resume relaunch never truncates
    the previous launch's diagnostic log.

    Args:
        base_root (Path | str): the RESOLVED base output root.
        index (int): the worker index (0-based).
        timestamp (str): the per-launch stamp (one for every worker —
            ``WORKER_LOG_TIMESTAMP_FORMAT`` over the launch instant).

    Returns:
        Path: ``{base}-mgpu-w{index}-{timestamp}.log`` (not created
        here).
    """
    base = Path(base_root)
    return Path(f"{base}-mgpu-w{index}-{timestamp}.log")


def _coerce_size(value):
    """Coerce a registry ``size (M)`` value to a float weight.

    Missing, None, or non-numeric values coerce to 0.0 — the
    custom-entries reality (a hand-authored overlay entry may carry a
    string like ``"600M+"`` or omit the key entirely); such a model
    still shards, weighted neutrally, and nothing crashes.

    Args:
        value: the raw registry value.

    Returns:
        float: the LPT weight (0.0 when unusable).
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def lpt_shard(models, workers, sizes):
    """Partition ``models`` over ``workers`` by LPT size weighting.

    Longest-processing-time-first greedy bin-packing: models sorted by
    weight DESCENDING (registry-name ascending tie-break), each assigned
    to the worker with the least accumulated weight (lowest worker index
    tie-break). Deterministic, and disjoint-by-construction — each model
    is assigned exactly once, so the shards partition the input.

    Args:
        models (list[str]): the requested BASE model names.
        workers (int): the worker count (``len(models) >= workers`` is
            the caller's validated invariant).
        sizes (dict): model name -> raw registry ``size (M)`` value;
            unusable values coerce to 0.0 via ``_coerce_size``.

    Returns:
        list[list[str]]: one model list per worker, in worker-index
        order (each list in LPT assignment order — deterministic).
    """
    weights = {name: _coerce_size(sizes.get(name)) for name in models}
    ordered = sorted(models, key=lambda name: (-weights[name], name))
    loads = [0.0] * workers
    shards = [[] for _ in range(workers)]
    for name in ordered:
        # least accumulated load wins; equal loads pick the lowest
        # worker index (the explicit tuple tie-break — min's first-
        # occurrence preference made structural)
        target = min(range(workers), key=lambda i: (loads[i], i))
        shards[target].append(name)
        loads[target] += weights[name]
    return shards


def parse_args(argv=None):
    """Parse the orchestrator-owned flags; everything else is passthrough.

    The orchestrator owns the five launch flags (``--workers``,
    ``--gpus``, ``--models``, ``--output-root``, ``--dry-run``) plus the
    two merge-mode flags (``--merge``, ``--include-checkpoints`` — 12-04),
    the two cleanup-mode flags (``--cleanup``, ``--yes`` — 14-02), and
    the rerun-mode flag (``--rerun-failed`` — 14-03; implies dispatch
    mode); every UNRECOGNIZED token from the command line lands in the
    returned remainder. In LAUNCH mode the remainder is appended VERBATIM to every
    worker argv (run_sweep stays the single owner of sweep-flag
    validation and help — the D-07 argv-surface-minimization answer); in
    MERGE and CLEANUP modes it must be EMPTY (neither takes sweep
    flags).
    ``--registry-dir`` stays a passthrough token but is READ for this
    module's own validation join so the orchestrator and the workers see
    the same registry view.

    Args:
        argv (list[str] | None): argv to parse (None reads sys.argv).

    Returns:
        tuple[argparse.Namespace, list[str]]: parsed orchestrator flags
        and the verbatim passthrough remainder.
    """
    parser = argparse.ArgumentParser(
        description="Orchestrate N run_sweep.py workers over disjoint "
                    "model shards, one GPU each (multi-GPU throughput, "
                    "MGPU-01/SC1), or --merge their frozen worker roots "
                    "into one verified consumer root (12-04, D-09)")
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel run_sweep.py workers (default: 1). The "
             "requested --models are LPT-sharded by registry size (M) "
             "into exactly this many disjoint shards; must not exceed "
             "the model count (an empty shard would spawn a no-op worker)"
    )
    parser.add_argument(
        "--gpus",
        type=str,
        default=None,
        help='Comma-separated GPU ids, one per worker, e.g. "0,1" '
             "(default: 0..workers-1). Each value is passed verbatim as "
             "that worker's CUDA_VISIBLE_DEVICES — operator-owned "
             "strings, ARITY-validated only (no nvidia-smi probing, no "
             "device-count assumption)"
    )
    parser.add_argument(
        "--models",
        type=str,
        default=None,
        help="Comma-separated model names to shard across the workers "
             "(REQUIRED for launch mode; every name must exist in the "
             "models registry — the same join run_sweep's --models filter "
             "uses). Merge mode takes no --models (the worker manifests "
             "are the merge's source of truth)"
    )
    parser.add_argument(
        "--output-root",
        type=str,
        default="./finetuned",
        help="Base sweep output root (default: ./finetuned, resolved "
             "absolute). Worker i writes under the frozen SIBLING root "
             "{base}-mgpu-w{i} with its tee log at "
             "{base}-mgpu-w{i}-{launch-stamp}.log (one log per launch, "
             "WR-02) — shared roots are forbidden (root-level manifests "
             "collide)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Forward --dry-run to every worker: each enumerates its "
             "shard and writes ONLY its planned sweep_manifest.json — no "
             "subprocess, no cell dirs (the CPU-side disjointness proof)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="static",
        choices=["static", "dispatch"],
        help="Orchestration mode (13-01, MGPU-06): 'static' (default) = "
             "legacy LPT model-sharded run_sweep.py workers under frozen "
             "{root}-mgpu-w{i} sibling roots; 'dispatch' = ONE dispatcher "
             "process feeding idle per-GPU workers from a deterministic "
             "(model x task x seed) cell queue under ONE shared root "
             "guarded by an O_EXCL claim ledger and a singleton "
             "dispatcher lock (dispatch roots need no merge)"
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        default=False,
        help="MERGE MODE (12-04, D-09): instead of launching, read the "
             "frozen worker roots {output-root}-mgpu-w{0..N-1} and merge "
             "them into the single --output-root — copy each cell's "
             "data-artifact allowlist with SHA256 verify (never a "
             "symlink, never a move) and write the union "
             "sweep_manifest.json / sweep_failures.json with every "
             "output_dir rewritten onto the merged root. Takes no sweep "
             "flags (the passthrough remainder must be empty) and no "
             "--models"
    )
    parser.add_argument(
        "--include-checkpoints",
        action="store_true",
        default=False,
        help="Merge-mode escape hatch (research A2): ALSO copy "
             "checkpoint-*/ trees and runs/ verbatim. Default OFF — "
             "checkpoints are worker resume state and nobody re-runs the "
             "merged root; only the MERGE_ALLOWLIST data artifacts merge "
             "by default"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        default=False,
        help="CLEANUP MODE (14-02, MGPU-05, D14-09..D14-12): verify the "
             "merged --output-root (an export_runs.py --dry-run "
             "subprocess + manifest cell-set equality vs the worker "
             "manifests), then — only if BOTH legs pass — remove the "
             "frozen worker roots {output-root}-mgpu-w{0..N-1} and "
             "their {base}-mgpu-w{i}-*.log per-launch logs behind an "
             "exact typed confirmation (--yes PHRASE; PHRASE = the "
             "resolved --output-root string, D14-11). The merged root "
             "is NEVER removed; dispatch roots refuse (they need no "
             "cleanup)"
    )
    parser.add_argument(
        "--yes",
        type=str,
        default=None,
        metavar="PHRASE",
        help="Cleanup gate phrase (non-interactive, D14-11): must equal "
             "the RESOLVED --output-root string EXACTLY. Without --yes, "
             "an interactive terminal prompts once; EOF, a mismatch, or "
             "a non-interactive launch refuses with nothing removed"
    )
    parser.add_argument(
        "--rerun-failed",
        action="store_true",
        default=False,
        help="RERUN MODE (14-03, MGPU-04, D14-05..D14-08): re-run the "
             "union of FAILED cells recorded in the dispatch ledger "
             "(state:failed claims across ALL prior runs on "
             "--output-root) through the dispatch engine — implies "
             "--mode dispatch and needs NEITHER --models NOR --seeds "
             "(the ledger defines both). Lane flags (peft/variant/"
             "epochs/subset/ebs/cache_dir/storage roots) replay "
             "VERBATIM from the claim-time lane records (D14-06); "
             "unequal lanes among the failed cells refuse loudly "
             "(D14-08); the original failed claims are preserved "
             "verbatim under dispatch_ledger/archive/ with rerun_of "
             "links on the fresh claims (D14-07). Orchestrator-owned "
             "vocabulary (this parser, never the passthrough — no "
             "collision with run_sweep's --from-failures); only "
             "--registry-dir may accompany it"
    )
    return parser.parse_known_args(argv)


def _parse_gpus(raw, problems):
    """Parse the ``--gpus`` comma list into verbatim operator-owned
    STRINGS, collecting problems.

    Each token forwards verbatim as one worker's
    ``CUDA_VISIBLE_DEVICES`` — a decimal index, a GPU UUID, or a MIG
    instance id are all legitimate values (WR-01: the documented
    contract is ARITY-validated only; int coercion here would refuse a
    legal UUID/MIG pin on the very hosts that need it, D-05). The only
    malformed token is an EMPTY element.

    Args:
        raw (str | None): the flag value (None = default 0..workers-1).
        problems (list[str]): the collect-all problems list.

    Returns:
        list[str] | None: the verbatim tokens, or None when the flag is
        absent (the caller decides the default).
    """
    if raw is None:
        return None
    gpus = []
    for token in raw.split(","):
        stripped = token.strip()
        if not stripped:
            problems.append(f"empty GPU id element in --gpus {raw!r}")
            continue
        gpus.append(stripped)  # verbatim operator-owned string (D-05)
    return gpus


def _registry_dir_from_passthrough(passthrough):
    """Read a passthrough ``--registry-dir`` for this module's own
    validation join (both ``--registry-dir X`` and ``--registry-dir=X``).

    The flag is NOT orchestrator-owned — it stays in the passthrough and
    forwards verbatim — but validation must join the requested model
    names against the SAME registry view the workers will use, or a
    fixture/custom registry would false-refuse or false-accept.

    Args:
        passthrough (list[str]): the verbatim remainder tokens.

    Returns:
        Path | None: the registry dir (None = registry_loader's own
        default, pipeline/).
    """
    for index, token in enumerate(passthrough):
        if token == "--registry-dir" and index + 1 < len(passthrough):
            return Path(passthrough[index + 1])
        if token.startswith("--registry-dir="):
            return Path(token.split("=", 1)[1])
    return None


def _failed_cell_count(worker_root_path):
    """Count a worker's failed cells from its sweep_failures.json.

    Args:
        worker_root_path (Path): the worker's frozen output root.

    Returns:
        int | None: the failure-entry count when the manifest exists and
        parses; None otherwise (a --dry-run worker never writes one).
    """
    path = Path(worker_root_path) / run_sweep.FAILURES_NAME
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, list):
        return None
    return len(payload)


# ===== merge mode (12-04, MGPU-02 artifact half, D-09) =====
#
# After N workers finish, the data chain must read ONE root: export_runs,
# the monitor, and gen_progress all consume the MERGED tree unchanged.
# The merge lives in this same entry (ONE naming authority — it imports
# worker_root, so launch and merge can never disagree about where worker
# artifacts live) and is COPY + SHA256-VERIFY, never a symlink and never
# a move (D-09: symlinks break when worker roots are cleaned and do not
# survive cross-host copies; a move would destroy the worker root's
# re-runnability). The merge NEVER mutates a worker root and NEVER
# deletes anything — worker-root cleanup is the runbook's explicit
# maintainer step, taken only after the merged root is verified.

#: The data-artifact allowlist copied per cell dir: the five JSON
#: artifacts every downstream consumer reads (export_runs walks
#: run_record.json and adopts seed_result.json; trainer_state.json is the
#: resume marker / global_step source; final_metrics.json is the
#: training-failure signal; flops_report.json is the FLOPs evidence).
#: checkpoint-*/ and runs/ are EXCLUDED by default (resume state for
#: workers only — nobody re-runs the merged root, and full-checkpoint
#: copy at E2' scale is disk-insane) and join only under the explicit
#: --include-checkpoints escape hatch (research A2).
MERGE_ALLOWLIST = (
    "run_record.json",
    "final_metrics.json",
    "trainer_state.json",
    "seed_result.json",
    "flops_report.json",
)

#: Cell-dict keys that IDENTITY a cell (the ``_manifest_payload``
#: projection); every OTHER cell key is a lane flag merged in via
#: sweep_flags and must be EQUAL across worker manifests (Pitfall 6).
_IDENTITY_CELL_KEYS = frozenset(
    {"model", "task", "seed", "status", "output_dir"})


def _write_json(path, payload):
    """Deterministic JSON write (the run_sweep._write_json discipline,
    mirrored locally so the merged manifests serialize byte-identically
    to what the driver itself would write — sort_keys + indent 4 +
    ensure_ascii False)."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=4, ensure_ascii=False,
                  sort_keys=True)


def _sha256_file(path):
    """Stream-SHA256 a file's bytes; ``None`` when unreadable.

    Args:
        path (Path): the file to hash.

    Returns:
        str | None: the hex digest, or None on OSError (the caller's
        verify then fails for this file — an unreadable source is a
        refused copy, never a silent skip).
    """
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def _copy_verified(src, dst):
    """Copy one file with D-09 verification: hash, copy, re-hash, compare.

    COPY + SHA256-VERIFY — never a symlink, never a move. The
    destination's parents are created; the copy OVERWRITES (idempotent
    re-merge: re-copying identical bytes re-verifies green). Any mismatch
    — an unreadable source, or an OSError from the mkdir/copy step
    itself (ENOSPC / EACCES / a read-only destination — WR-04: converted
    here so the operator gets the designed merge-refusal diagnostic,
    never a raw traceback) — returns False; the caller collects the
    failure and refuses the whole merge before any merged manifest
    lands (a partial corrupt merge never becomes a sweep root).

    Args:
        src (Path): the worker-root source file.
        dst (Path): the merged-root destination.

    Returns:
        bool: True iff the destination's SHA256 equals the source's
        after the copy.
    """
    src_hash = _sha256_file(src)
    if src_hash is None:
        return False
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    except OSError:
        return False
    return _sha256_file(dst) == src_hash


def _rewrite_output_dir(cell_dir_str, worker_root, merged_root):
    """Prefix-swap a cell/failure ``output_dir`` onto the merged root.

    Startswith-GUARDED with the boundary check the raw prefix test lacks:
    ``.../finetuned-mgpu-w0`` is a raw string PREFIX of
    ``.../finetuned-mgpu-w01`` — an unguarded swap there would corrupt
    the sibling worker's path — so only an exact match or a
    ``/``-boundary match rewrites. A non-matching prefix passes through
    UNCHANGED (defensive: a manifest recording paths outside its own
    worker root is the validation pass's problem to refuse, never this
    swap's to silently rewrite).

    Args:
        cell_dir_str (str): the recorded output_dir string.
        worker_root (Path | str): the cell's own worker root.
        merged_root (Path | str): the merged consumer root.

    Returns:
        str: the rewritten path (or the input, verbatim, on no match).
    """
    worker = str(worker_root)
    if not cell_dir_str.startswith(worker):
        return cell_dir_str
    rest = cell_dir_str[len(worker):]
    if rest != "" and not rest.startswith("/"):
        return cell_dir_str  # sibling-prefix boundary (w0 vs w01)
    return f"{merged_root}{rest}"


def _lane_signature(manifest):
    """Per lane-flag value sets over every non-identity cell key.

    Lane flags are the sweep_flags keys run_sweep merges into every cell
    (config_variant / num_train_epochs / subset_file /
    effective_batch_size / cache_dir) plus any lane key a future driver
    records the same way (e.g. peft): they describe the EXPERIMENT, not
    the cell. Values canonicalize via sorted-key JSON so sets compare
    stably across manifests.

    Args:
        manifest (dict): a parsed worker sweep_manifest.json.

    Returns:
        dict: flag name -> set of canonical value strings.
    """
    lanes = {}
    cells = manifest.get("cells")
    if not isinstance(cells, list):
        return lanes
    for cell in cells:
        if not isinstance(cell, dict):
            continue
        for key, value in cell.items():
            if key in _IDENTITY_CELL_KEYS:
                continue
            lanes.setdefault(key, set()).add(
                json.dumps(value, sort_keys=True, default=str))
    return lanes


def _canonical_lane_value(value):
    """Deterministic canonical form for one root's lane-value collection.

    A lane's per-root value is a SET of per-cell canonical strings (or
    None when the root lacks the flag): sets canonicalize through
    ``sorted()`` first — ``json.dumps(value, default=str)`` alone would
    serialize ``str(set)``, whose element order is the set's internal
    iteration order (PYTHONHASHSEED-dependent across processes and
    insertion-history-dependent even within one), so two IDENTICAL
    lanes could be falsely refused (WR-05). Anything else (None, dict,
    scalar) canonicalizes with sorted keys, unchanged.

    Args:
        value: the per-root lane value (set | frozenset | None | other
            JSON-shaped value).

    Returns:
        str: the deterministic canonical string.
    """
    if isinstance(value, (set, frozenset)):
        return json.dumps(sorted(value), default=str)
    return json.dumps(value, sort_keys=True, default=str)


def _load_json_object(path, problems, what):
    """Load a JSON file that must be an object, collecting problems.

    Args:
        path (Path): the file to read.
        problems (list[str]): the collect-all problems list.
        what (str): a human label for the diagnostic.

    Returns:
        dict | None: the parsed object, or None (a problem was appended).
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        problems.append(f"{what} unreadable/invalid at {path}: {exc}")
        return None
    if not isinstance(payload, dict):
        problems.append(f"{what} at {path} is not a JSON object")
        return None
    return payload


def _resolve_cell_rel(output_dir, wroot, index, problems):
    """Resolve a cell's output_dir to (source dir, relative path) under
    its worker root, collecting problems on any path that does not sit
    under its own root.

    Args:
        output_dir (str): the cell's recorded output_dir.
        wroot (Path): the cell's worker root.
        index (int): the worker index (diagnostics).
        problems (list[str]): the collect-all problems list.

    Returns:
        tuple[Path, Path] | None: ``(source cell dir, dir relative to
        the worker root)``, or None (a problem was appended).
    """
    src_dir = Path(output_dir)
    try:
        return src_dir, src_dir.relative_to(wroot)
    except ValueError:
        pass
    # resolve() retry: symlinked tmp roots (macOS /private) spell the
    # same tree differently — compare resolved forms before refusing
    try:
        resolved = src_dir.resolve()
        return resolved, resolved.relative_to(wroot.resolve())
    except ValueError:
        problems.append(
            f"worker {index} cell output_dir {output_dir} is not under "
            f"its worker root {wroot}"
        )
        return None


def _root_has_dispatch_evidence(path):
    """True when ``path`` carries run-recorded dispatch-mode evidence.

    Reads ONLY the three markers a dispatch run itself writes (13-02,
    MGPU-06 / D13-07 — evidence-based, NEVER directory-shape inference):
    ``dispatch_state.json`` at the root (written before any claim),
    the ``dispatch_ledger`` dir (claims + the singleton lock), or a
    ``sweep_manifest.json`` whose cells carry the
    ``orchestrator_mode: "dispatch"`` marker (the 13-02 dry-run plan
    artifact — the one evidence a dry-run root ever carries). A root
    with NONE of the three is the static world: no evidence, and the
    merge proceeds exactly as before. An absent or unreadable manifest
    carries no marker (fail-open only in the absence of EVERY marker,
    which IS the static world — T-13-08).

    Args:
        path (Path | str): the root to inspect (need not exist).

    Returns:
        bool: True iff any run-recorded dispatch marker is present.
    """
    # Lazy import (the 09-06 cycle-breaking precedent, as in main()):
    # dispatch_core imports THIS module at its top (it reuses
    # _parse_gpus and the log-stamp format), so a module-top import
    # here would be circular.
    import dispatch_core

    root = Path(path)
    if (root / dispatch_core.DISPATCH_STATE_NAME).is_file():
        return True
    if (root / dispatch_core.LEDGER_DIR_NAME).is_dir():
        return True
    manifest_path = root / run_sweep.MANIFEST_NAME
    if not manifest_path.is_file():
        return False
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return False  # an unreadable manifest carries no marker
    if not isinstance(payload, dict):
        return False
    cells = payload.get("cells")
    if not isinstance(cells, list):
        return False
    return any(
        isinstance(cell, dict)
        and cell.get("orchestrator_mode") == "dispatch"
        for cell in cells)


def _dispatch_merge_refusal(path):
    """Build the named dispatch-root merge refusal (MGPU-06, T-13-06)."""
    return (
        f"dispatch root {path} needs no merge — dispatch mode writes "
        "ONE shared root (MGPU-06); refusing before any copy (merging "
        "dispatch evidence would double-count its cells into the "
        "consumer root)"
    )


def run_merge(args, passthrough):
    """Merge N frozen-named worker roots into one verified consumer root.

    Validation is collect-all fail-fast (the ``_validate_filters``
    discipline): ``--workers < 1``, a non-empty passthrough (merge takes
    no sweep flags), a provided ``--models`` (WR-06: the worker
    manifests are the merge's source of truth — never silently
    ignored), ``--dry-run`` combined with ``--merge``, ANY root in the
    merge's set carrying run-recorded dispatch evidence (13-02, MGPU-06
    — dispatch roots need no merge; evidence-based, never directory-shape
    inference), a missing
    worker root, a worker root without its sweep_manifest.json, an
    unreadable/non-object manifest or failures file, a manifest whose
    matrix/cells are the wrong shape, a cell whose output_dir does not
    sit under its own worker root, and ANY lane-flag difference across
    worker manifests (Pitfall 6 — the diagnostic lists the differing
    value per root per flag) are ALL listed together, then the merge
    exits non-zero before a single file is copied. ``--gpus`` is
    meaningless in merge mode and ignored.

    Stale-cell refusal (WR-03): a re-merge over a previously-merged
    root REFUSES if any allowlisted file already under the merged root
    is not covered by this merge's copy plan (the worker set changed —
    the exporter walks the file tree, not the manifest, so stale cells
    would silently leak into exported data); identical worker sets stay
    idempotent (every pre-existing file is in the plan).

    Copy scope per cell dir: the MERGE_ALLOWLIST files present (missing
    ones are skipped and counted — a cell that never ran has nothing to
    copy and stays invisible to the exporter, unchanged semantics),
    recursing into ``frac_*/`` children (curve cells); under
    ``--include-checkpoints`` also the whole ``checkpoint-*/`` and
    ``runs/`` trees (research A2). Destination = the same relative path
    under the merged root. Every copied file is SHA256-verified
    source-vs-destination; ANY mismatch refuses the merge with the file
    list and the merged manifests are NOT written (a partial corrupt
    merge never lands). On success: the merged sweep_manifest.json
    unions every worker's cells with output_dir rewritten onto the
    merged root, matrix.models/tasks/seeds unioned and output_root set
    to the merged root, and sweep_failures.json unions the worker
    failure entries with the same rewrite. Worker roots are left INTACT
    (re-runnable in isolation, D-08); deleting them is the runbook's
    explicit post-merge maintainer step.

    gen_progress warning (repeated from the generator's own docstring):
    NEVER pass worker roots AND their merged root together — every cell
    would appear twice. Worker roots for the live view, the merged root
    alone for the post-run view.

    Args:
        args (argparse.Namespace): the parsed orchestrator flags.
        passthrough (list[str]): the parse_known_args remainder (must be
            empty in merge mode).
    """
    problems = []
    workers = args.workers
    if workers < 1:
        problems.append(f"--workers must be >= 1, got {workers}")
    if passthrough:
        problems.append(
            "--merge takes no sweep flags; unrecognized token(s): "
            f"{passthrough}"
        )
    # --models is an orchestrator-owned flag, so it never lands in the
    # passthrough — refuse it explicitly (WR-06): a reused launch-mode
    # command line must fail loudly, never silently ignore --models
    if args.models is not None:
        problems.append(
            "--merge takes no --models (the worker manifests are the "
            "merge's source of truth)"
        )
    if args.dry_run:
        problems.append(
            "--dry-run is a launch-mode flag and cannot combine with "
            "--merge"
        )

    base_root = Path(args.output_root).resolve()
    worker_roots = [worker_root(base_root, i) for i in range(workers)]

    # Dispatch-evidence refusal (13-02, MGPU-06 / T-13-06): ANY root in
    # the merge's set carrying run-recorded dispatch evidence — the
    # merged-target base root OR an existing worker root — refuses by
    # name BEFORE any copy. Dispatch mode writes ONE shared root with
    # ordinary per-cell subpaths, so its roots need no merge and merging
    # one would double-count its cells into the consumer root (the
    # gen_progress/export hazard). Reads ONLY the run-recorded markers
    # (dispatch_state.json / dispatch_ledger / the manifest
    # orchestrator_mode marker — D13-07), never directory shape;
    # MERGE_ALLOWLIST, the copy pass, and every no-evidence static
    # behavior below stay untouched.
    if _root_has_dispatch_evidence(base_root):
        problems.append(_dispatch_merge_refusal(base_root))
    for wroot in worker_roots:
        if wroot != base_root and wroot.is_dir() and \
                _root_has_dispatch_evidence(wroot):
            problems.append(_dispatch_merge_refusal(wroot))

    manifests = {}
    failures = {}
    for index, wroot in enumerate(worker_roots):
        if not wroot.is_dir():
            problems.append(f"worker root {wroot} does not exist")
            continue
        manifest_path = wroot / run_sweep.MANIFEST_NAME
        if not manifest_path.is_file():
            problems.append(
                f"worker root {wroot} has no {run_sweep.MANIFEST_NAME} "
                "(an incomplete merge never lands)"
            )
            continue
        manifest = _load_json_object(
            manifest_path, problems, f"worker {index} manifest")
        if manifest is None:
            continue
        cells = manifest.get("cells")
        matrix = manifest.get("matrix")
        if not isinstance(cells, list):
            problems.append(
                f"worker {index} manifest at {manifest_path}: 'cells' is "
                "not a list"
            )
            continue
        if not isinstance(matrix, dict):
            problems.append(
                f"worker {index} manifest at {manifest_path}: 'matrix' "
                "is not an object"
            )
            continue
        manifests[index] = manifest
        # Failures: absent = a --dry-run worker (tolerated as empty); a
        # PRESENT file must parse as a list
        failures_path = wroot / run_sweep.FAILURES_NAME
        if not failures_path.is_file():
            failures[index] = []
            continue
        try:
            entries = json.loads(failures_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(
                f"worker {index} failures file unreadable at "
                f"{failures_path}: {exc}"
            )
            continue
        if not isinstance(entries, list):
            problems.append(
                f"worker {index} failures file at {failures_path} is not "
                "a JSON list"
            )
            continue
        failures[index] = entries

    # Lane equality (Pitfall 6): every cell key outside the identity
    # projection is a lane flag and must be EQUAL across worker
    # manifests — a merge of a lora worker with a base worker is a
    # different experiment than either, never a silent pick-first
    if len(manifests) > 1:
        signatures = {
            index: _lane_signature(manifest)
            for index, manifest in manifests.items()}
        all_flags = sorted(
            set().union(*(set(sig) for sig in signatures.values())))
        for flag in all_flags:
            per_root = {
                index: signatures[index].get(flag)
                for index in sorted(signatures)}
            if len({_canonical_lane_value(value)
                    for value in per_root.values()}) > 1:
                listed = "; ".join(
                    f"worker {index} ({worker_roots[index]}) = "
                    f"{sorted(per_root[index]) if per_root[index] is not None else '<absent>'}"
                    for index in sorted(per_root))
                problems.append(
                    f"lane flag '{flag}' differs across worker manifests "
                    f"— {listed} (unequal lanes are different "
                    "experiments; re-launch the workers with one lane)"
                )

    # Cell resolution (validation, BEFORE any copy): every cell's
    # output_dir must sit under its own worker root
    cell_plans = []  # (worker index, source cell dir, rel to worker root)
    for index in sorted(manifests):
        wroot = worker_roots[index]
        for cell in manifests[index]["cells"]:
            if not isinstance(cell, dict):
                problems.append(
                    f"worker {index} manifest has a non-object cell: "
                    f"{cell!r}"
                )
                continue
            output_dir = cell.get("output_dir")
            if not isinstance(output_dir, str) or not output_dir:
                problems.append(
                    f"worker {index} manifest cell is missing a string "
                    f"output_dir: {cell!r}"
                )
                continue
            resolved = _resolve_cell_rel(
                output_dir, wroot, index, problems)
            if resolved is not None:
                cell_plans.append(
                    (index, resolved[0], resolved[1]))

    if problems:
        sys.exit(f"[Error] {'; '.join(problems)}")

    # ===== copy pass =====

    def _scan_dir(dir_path):
        """Allowlisted files under one cell dir, recursing into frac_*/
        children (curve cells); checkpoint-*/ and runs/ join ONLY under
        --include-checkpoints (research A2)."""
        found = []
        try:
            entries = sorted(dir_path.iterdir())
        except OSError:
            return found  # a never-run cell dir vanished mid-merge
        for entry in entries:
            if entry.is_file() and entry.name in MERGE_ALLOWLIST:
                found.append(entry)
            elif entry.is_dir() and entry.name.startswith("frac_"):
                found.extend(_scan_dir(entry))
            elif (args.include_checkpoints and entry.is_dir()
                    and (entry.name.startswith("checkpoint-")
                         or entry.name == "runs")):
                found.extend(
                    child for child in sorted(entry.rglob("*"))
                    if child.is_file())
        return found

    copy_pairs = []  # (worker index, source file, rel to worker root)
    never_ran = {index: 0 for index in range(workers)}
    for index, src_dir, cell_rel in cell_plans:
        if not src_dir.is_dir():
            never_ran[index] += 1  # planned-but-never-run cell
            continue
        for src_file in _scan_dir(src_dir):
            copy_pairs.append(
                (index, src_file, cell_rel / src_file.relative_to(src_dir)))

    # Stale-cell guard (WR-03): a re-merge over a previously-merged root
    # whose worker set CHANGED would leave the previous merge's cell
    # files on disk — the merge never deletes, _copy_verified only
    # overwrites what it copies, and export_runs walks the FILE TREE
    # (not the manifest), so the stale cells would silently leak into
    # the exported numbers while the new manifest claims they are
    # absent. Refuse naming them (collect-all discipline); identical
    # worker sets stay idempotent — every pre-existing allowlisted file
    # IS in the plan and the guard passes silently.
    if base_root.is_dir():
        planned_dests = {base_root / rel for _i, _s, rel in copy_pairs}
        stale = sorted(
            path for path in base_root.rglob("*")
            if path.is_file() and path.name in MERGE_ALLOWLIST
            and path not in planned_dests)
        if stale:
            shown = "; ".join(str(path) for path in stale[:5])
            more = "" if len(stale) <= 5 else f" (+{len(stale) - 5} more)"
            sys.exit(
                f"[Error] merged root {base_root} carries {len(stale)} "
                "allowlisted file(s) this merge does NOT cover — the "
                "worker set changed since the previous merge and the "
                "stale cells would leak into exported data (the "
                "exporter walks the file tree, not the manifest): "
                f"{shown}{more}. Delete the merged root (or re-include "
                "the workers that produced them) and merge again — "
                "merge refused, merged manifests NOT written, worker "
                "roots untouched"
            )

    # ===== verify pass: every file hash-copy-rehash-compared; ANY
    # mismatch refuses the merge BEFORE the merged manifests land (a
    # partial corrupt merge never becomes a sweep root) =====
    copied = {index: 0 for index in range(workers)}
    mismatches = []
    for index, src_file, rel in copy_pairs:
        if _copy_verified(src_file, base_root / rel):
            copied[index] += 1
        else:
            mismatches.append(f"worker {index}: {src_file} -> "
                              f"{base_root / rel}")
    if mismatches:
        sys.exit(
            "[Error] SHA256 mismatch after copy — merge refused, merged "
            "manifests NOT written, worker roots untouched: "
            f"{'; '.join(mismatches)}"
        )

    # ===== manifest + failures union (output_dir prefix-rewritten) =====
    merged_cells = []
    models_union = set()
    tasks_union = set()
    seeds_union = set()
    for index in sorted(manifests):
        wroot = worker_roots[index]
        for cell in manifests[index]["cells"]:
            merged = dict(cell)
            if isinstance(merged.get("output_dir"), str):
                merged["output_dir"] = _rewrite_output_dir(
                    merged["output_dir"], wroot, base_root)
            merged_cells.append(merged)
        matrix = manifests[index].get("matrix") or {}
        for value in matrix.get("models") or []:
            models_union.add(value)
        for value in matrix.get("tasks") or []:
            tasks_union.add(value)
        for value in matrix.get("seeds") or []:
            seeds_union.add(value)
    merged_failures = []
    for index in sorted(manifests):
        wroot = worker_roots[index]
        for entry in failures[index]:
            if isinstance(entry, dict) and isinstance(
                    entry.get("output_dir"), str):
                entry = {
                    **entry,
                    "output_dir": _rewrite_output_dir(
                        entry["output_dir"], wroot, base_root),
                }
            merged_failures.append(entry)

    merged_matrix = {
        "models": sorted(models_union),
        "tasks": sorted(tasks_union),
        "seeds": sorted(seeds_union),
        "output_root": str(base_root),
    }
    base_root.mkdir(parents=True, exist_ok=True)
    _write_json(base_root / run_sweep.MANIFEST_NAME,
                {"matrix": merged_matrix, "cells": merged_cells})
    _write_json(base_root / run_sweep.FAILURES_NAME, merged_failures)

    for index in range(workers):
        never = (f", {never_ran[index]} cell(s) with no files on disk"
                 if never_ran[index] else "")
        print(f"[Merge] worker {index}: {copied[index]} file(s) copied "
              f"+ SHA256-verified from {worker_roots[index]}{never}")
    print(f"[Merge] union: {len(merged_cells)} cell(s) and "
          f"{len(merged_failures)} failure entry(ies) over "
          f"{len(manifests)} worker manifest(s) -> {base_root}")
    print(f"[Merge] wrote {base_root / run_sweep.MANIFEST_NAME} and "
          f"{base_root / run_sweep.FAILURES_NAME}")
    print("[Merge] worker roots left INTACT (re-runnable in isolation, "
          "D-08) — delete them manually only after verifying the merged "
          "root; never pass worker roots AND the merged root to "
          "gen_progress together (double-counted sweeps)")


# ===== cleanup mode (14-02, MGPU-05 / D14-09..D14-12) =====
#
# The runbook's post-merge step — delete the worker roots and their
# per-launch logs once the merged root is verified — becomes an
# evidence-gated, tested command. NEVER a bare rm -rf: removal is
# OFFERED only after BOTH verification legs hold (the export dry-run
# subprocess walks the FILE tree while the manifest check compares
# PLANNED sets — Pitfall 6's two different truths), and EXECUTES only
# behind an exact typed phrase (the resolved --output-root string, the
# Q4 ruling).

#: The export dry-run verification script (D14-10 leg A), derived from
#: the same repo-root constant the worker script uses — never a
#: CWD-relative guess. Reached ONLY through a ``sys.executable``
#: subprocess: export_runs imports numpy/yaml/scipy at its module top,
#: and this module must stay stdlib-headless (the 14-02 key-link
#: contract).
_EXPORT_RUNS_SCRIPT = (
    run_sweep.PIPELINE_DIR.parent / "script" / "export_runs.py")

#: The injectable export-subprocess seam (the ``_DEFAULT_SPAWNER``
#: idiom): tests inject a fake returning a CompletedProcess; the real
#: path is ``subprocess.run`` with captured output.
_DEFAULT_RUNNER = subprocess.run


def _dispatch_cleanup_refusal(path):
    """Build the named dispatch-root cleanup refusal (D14-11, D14-12)."""
    return (
        f"dispatch root {path} needs no cleanup — dispatch mode writes "
        "ONE shared root (MGPU-06) with no per-worker roots to remove; "
        "refusing before any verification or removal"
    )


def _cell_id_text(cell_id):
    """Deterministic display form of a ``(model, task, seed)`` cell id.

    Args:
        cell_id (tuple): the identity triple (elements may be ``None``
            in a malformed manifest — the text form sorts regardless).

    Returns:
        str: ``{model}/{task}/seed_{seed}``.
    """
    model, task, seed = cell_id
    return f"{model}/{task}/seed_{seed}"


def _manifest_cell_identities(manifest, path, what, problems):
    """Extract the set of ``(model, task, seed)`` identity tuples from a
    manifest's ``cells`` list — the ``_IDENTITY_CELL_KEYS`` projection
    minus ``status``/``output_dir`` (set-based, never order-sensitive).

    Args:
        manifest (dict): a parsed ``sweep_manifest.json`` object.
        path (Path): the manifest's path (diagnostics).
        what (str): a human label for the diagnostic.
        problems (list[str]): the collect-all problems list.

    Returns:
        set | None: the identity set, or ``None`` (a problem was
        appended).
    """
    cells = manifest.get("cells")
    if not isinstance(cells, list):
        problems.append(f"{what} at {path}: 'cells' is not a list")
        return None
    identities = set()
    for cell in cells:
        if not isinstance(cell, dict):
            continue
        identities.add(
            (cell.get("model"), cell.get("task"), cell.get("seed")))
    return identities


def run_cleanup(args, passthrough, runner=None, confirm_input=None):
    """Verify the merged root, then remove worker roots behind a typed gate.

    Replaces the manual ``rm -rf`` runbook step with an evidence-gated,
    operator-confirmed command (14-02, MGPU-05, D14-09..D14-12). Each
    stage gates the next:

    1. ``--workers >= 1``; the base root resolves absolute exactly as
       the launch path resolves it.
    2. Dispatch-evidence refusal (D14-11/D14-12): the base root OR any
       ``worker_root()`` sibling carrying run-recorded dispatch evidence
       refuses with the named needs-no-cleanup error BEFORE any
       verification — dispatch mode is one root by construction.
    3. Leg A (D14-10): ``script/export_runs.py --dry-run`` over the
       merged root through the injectable ``runner`` seam — a SUBPROCESS,
       never an import (stdlib-headless; the equals-form argument means
       a leading-dash root path can never re-parse as a flag, T-14-05).
       A non-zero exit refuses naming the returncode and the captured
       output tail.
    4. Leg B: the merged manifest's ``(model, task, seed)`` cell SET
       must EQUAL the union of the worker manifest sets (a missing
       MERGED manifest refuses — nothing has been verified; a missing
       worker manifest refuses naming the worker root); a discrepancy
       refuses listing the sorted missing/extra cells — never
       order-sensitive.
    5. Both legs green: print the removal plan — every EXISTING
       ``worker_root()`` path and every ``{base}-mgpu-w{i}-*.log``
       per-launch log (the Q5 ruling: the full manual recipe, roots AND
       logs), each listed by path before anything is touched.
    6. Gate (D14-11, the Q4 ruling): the required phrase is the resolved
       root string ``str(root)``. ``--yes PHRASE`` compares
       non-interactively; otherwise an interactive stdin prompts ONCE
       via the injectable ``confirm_input`` seam (default ``input``).
       EOF, a mismatch, or a non-interactive launch without ``--yes``
       refuses naming the phrase requirement — nothing removed.
    7. Removal: ``shutil.rmtree`` each listed root that still exists
       (an already-absent root is noted and skipped — never a crash),
       unlink each listed log, then post-check every listed path is
       gone. The merged root is NEVER a removal target.

    Args:
        args (argparse.Namespace): the parsed orchestrator flags.
        passthrough (list[str]): the parse_known_args remainder (main()
            already refused a non-empty one for ``--cleanup``).
        runner: injectable export-subprocess seam; ``None`` uses
            ``subprocess.run`` (the ``_DEFAULT_SPAWNER`` idiom).
        confirm_input: injectable gate reader; ``None`` uses ``input``.
    """
    problems = []
    workers = args.workers
    if workers < 1:
        problems.append(f"--workers must be >= 1, got {workers}")
    if problems:
        sys.exit(f"[Error] {'; '.join(problems)}")

    root = Path(args.output_root).resolve()
    worker_roots = [worker_root(root, i) for i in range(workers)]

    # (2) dispatch-evidence refusal — BEFORE any verification (the
    # runner is never invoked for a dispatch root; run_merge's
    # defense-in-depth shape: base root AND every worker root)
    if _root_has_dispatch_evidence(root):
        problems.append(_dispatch_cleanup_refusal(root))
    for wroot in worker_roots:
        if wroot != root and _root_has_dispatch_evidence(wroot):
            problems.append(_dispatch_cleanup_refusal(wroot))
    if problems:
        sys.exit(f"[Error] {'; '.join(problems)}")

    # (3) leg A: export dry-run SUBPROCESS over the merged root
    seam = _DEFAULT_RUNNER if runner is None else runner
    proc = seam(
        [sys.executable, str(_EXPORT_RUNS_SCRIPT), "--dry-run",
         f"--input-root={root}"],
        capture_output=True, text=True)
    stdout = getattr(proc, "stdout", None) or ""
    stderr = getattr(proc, "stderr", None) or ""
    captured = f"{stdout}{stderr}".strip()
    if proc.returncode != 0:
        tail = (f" — captured output tail: {captured[-400:]}"
                if captured else "")
        sys.exit(
            f"[Error] cleanup verification refused: export dry-run over "
            f"{root} exited {proc.returncode}{tail}; nothing removed, "
            "worker roots untouched"
        )
    dry_lines = [line for line in stdout.strip().splitlines() if line]
    print(f"[Cleanup] export dry-run: "
          f"{dry_lines[-1] if dry_lines else ''}")

    # (4) leg B: merged manifest cell set == union of worker sets
    merged_path = root / run_sweep.MANIFEST_NAME
    if not merged_path.is_file():
        sys.exit(
            f"[Error] cleanup verification refused: no "
            f"{run_sweep.MANIFEST_NAME} at the merged root {root} — "
            "nothing has been verified (merge first); nothing removed"
        )
    merged_manifest = _load_json_object(
        merged_path, problems, "merged manifest")
    if merged_manifest is None:
        sys.exit(f"[Error] {'; '.join(problems)}")
    merged_ids = _manifest_cell_identities(
        merged_manifest, merged_path, "merged manifest", problems)
    if merged_ids is None:
        sys.exit(f"[Error] {'; '.join(problems)}")
    worker_ids = set()
    for index, wroot in enumerate(worker_roots):
        manifest_path = wroot / run_sweep.MANIFEST_NAME
        if not manifest_path.is_file():
            problems.append(
                f"worker root {wroot} has no {run_sweep.MANIFEST_NAME} "
                "(nothing verified)"
            )
            continue
        manifest = _load_json_object(
            manifest_path, problems, f"worker {index} manifest")
        if manifest is None:
            continue
        ids = _manifest_cell_identities(
            manifest, manifest_path, f"worker {index} manifest", problems)
        if ids is not None:
            worker_ids |= ids
    if problems:
        sys.exit(f"[Error] {'; '.join(problems)}")
    if merged_ids != worker_ids:
        parts = []
        missing = sorted(worker_ids - merged_ids, key=_cell_id_text)
        extra = sorted(merged_ids - worker_ids, key=_cell_id_text)
        if missing:
            parts.append(
                "cell(s) in the worker manifests but MISSING from the "
                f"merged manifest: {[_cell_id_text(c) for c in missing]}")
        if extra:
            parts.append(
                "cell(s) in the merged manifest that NO worker claims: "
                f"{[_cell_id_text(c) for c in extra]}")
        sys.exit(
            f"[Error] cleanup verification refused: merged manifest cell "
            f"set ({len(merged_ids)}) != union of worker manifest cell "
            f"sets ({len(worker_ids)}) — {'; '.join(parts)}; nothing "
            "removed, worker roots untouched"
        )

    # (5) the removal plan: every path listed BEFORE anything is touched
    removal_targets = []
    for wroot in worker_roots:
        if wroot.exists():
            print(f"[Cleanup] remove worker root: {wroot}")
            removal_targets.append(wroot)
        else:
            print(f"[Cleanup] worker root already absent (skip): {wroot}")
        for log in sorted(Path(match) for match in glob.glob(
                glob.escape(f"{wroot}-") + "*.log")):
            print(f"[Cleanup] remove worker log: {log}")
            removal_targets.append(log)

    # (6) the typed-phrase gate
    phrase = str(root)
    typed = None
    if args.yes is not None:
        typed = args.yes
    elif confirm_input is not None or sys.stdin.isatty():
        reader = input if confirm_input is None else confirm_input
        try:
            typed = reader(
                f"[Cleanup] type '{phrase}' to remove the listed worker "
                "roots and logs: ")
        except EOFError:
            typed = None
    if typed != phrase:
        sys.exit(
            f"[Error] cleanup refused: the confirmation phrase does not "
            f"match — type the resolved output root '{phrase}' exactly "
            "(--yes PHRASE, or the interactive prompt); nothing removed, "
            "worker roots untouched"
        )

    # (7) removal + post-check (the merged root is never a target)
    removed = []
    removal_problems = []
    for path in removal_targets:
        if not path.exists():
            print(f"[Cleanup] already absent at removal time (skip): "
                  f"{path}")
            continue
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        except OSError as exc:
            removal_problems.append(f"{path}: {exc}")
            continue
        removed.append(path)
    survivors = [p for p in removal_targets if p.exists()]
    if removal_problems or survivors:
        sys.exit(
            "[Error] cleanup removal incomplete — "
            + (f"failed: {'; '.join(removal_problems)}"
               + ("; " if survivors else ""))
            + (f"still present: {survivors}" if survivors else "")
        )
    for path in removed:
        print(f"[Cleanup] removed {path}")
    print(f"[Cleanup] removed {len(removed)} path(s); merged root "
          f"{root} left INTACT")


def main(spawner=None, clock=None):
    """Validate, shard, spawn, wait, and report the aggregated verdict.

    Refuses collect-all (every problem listed together, then one
    non-zero exit — the ``_validate_filters`` discipline) on: workers <
    1, a malformed or arity-mismatched ``--gpus``, a provided-but-empty
    ``--models`` value, unknown model names vs the registry, workers
    exceeding the model count (empty-shard refusal), or any frozen-root
    collision. Then: LPT-shard, spawn ALL workers (each an ordinary
    run_sweep.py invocation under its frozen sibling root), wait ALL,
    print the per-worker verdict table, and exit 0 iff every worker
    exited 0 — otherwise exit 1. A dead worker never touches its
    siblings (independent sessions + disjoint roots, D-06/SC2).

    Args:
        spawner: an injectable spawner seam (the sweep_launcher :475
            idiom) — a callable with Popen's signature; None uses the
            module default (subprocess.Popen). Tests inject a fake to
            prove the launch kwargs CPU-only.
        clock: an injectable ``datetime.now``-shaped callable (the
            sweep_launcher ``clock`` idiom); None uses the real
            ``datetime.now``. ONE stamp per launch names every worker
            tee log (WR-02: a resume relaunch derives a fresh stamp and
            never truncates the prior launch's crash log).
    """
    args, passthrough = parse_args()
    # A6 (locked): --mode dispatch + --merge on one command line is
    # refused BEFORE either mode runs — dispatch writes ONE shared root
    # with ordinary per-cell subpaths, so dispatch roots need no merge
    # (MGPU-06); mode combination is deterministic, never order-dependent.
    if args.merge and args.mode == "dispatch":
        sys.exit(
            "[Error] --mode dispatch cannot combine with --merge: "
            "dispatch mode writes ONE shared root with ordinary "
            "per-cell subpaths ({root}/{model}/{task}/seed_{seed}/), so "
            "dispatch roots need no merge (MGPU-06) — run the modes "
            "separately"
        )
    if args.rerun_failed:
        # 14-03 (MGPU-04, D14-05, the Q3 ruling): --rerun-failed is
        # ORCHESTRATOR-OWNED vocabulary (a shard parser flag can never
        # collide with run_sweep's passthrough --from-failures, Pitfall
        # 5) and IMPLIES dispatch mode — it routes into the engine's
        # re-run branch BEFORE the --models/--seeds requirements (the
        # ledger defines both). Combination refusals fire in the A6
        # shape BEFORE any ledger work; the explicit --mode static
        # refusal needs the raw-token scan because "static" is also the
        # parser DEFAULT (an implicit static must not refuse).
        if args.merge:
            sys.exit(
                "[Error] --rerun-failed cannot combine with --merge: "
                "dispatch roots are ONE shared root that needs no "
                "merge (MGPU-06) — run the modes separately"
            )
        if args.mode == "static" and any(
                token == "--mode" or token.startswith("--mode=")
                for token in sys.argv[1:]):
            sys.exit(
                "[Error] --rerun-failed cannot combine with --mode "
                "static: --rerun-failed implies --mode dispatch (the "
                "re-run replays through the dispatch engine's worker "
                "loops)"
            )
        if args.dry_run:
            sys.exit(
                "[Error] --rerun-failed cannot combine with --dry-run: "
                "the re-run set IS the plan (the ledger's failed "
                "claims) — there is nothing left to enumerate dry"
            )
        if args.models is not None:
            sys.exit(
                "[Error] --rerun-failed takes no --models (D14-05): "
                "the re-run scope is the ledger's failed claims, never "
                "a command-line filter"
            )
        if args.cleanup:
            sys.exit(
                "[Error] --rerun-failed cannot combine with --cleanup: "
                "cleanup verifies and removes STATIC worker roots after "
                "a merge — a re-run launches dispatch children; run the "
                "modes separately"
            )
        # Lazy import (the cycle-breaking precedent below): the shard
        # parser owns the flag; the engine owns the re-run branch.
        import dispatch_core

        return dispatch_core.run_dispatch(
            args, passthrough, spawner=spawner, clock=clock)
    if args.cleanup:
        # 14-02 (D14-09..D14-12, the A6 refusal shape): cleanup is the
        # fourth sibling mode — verify the merged root, then offer
        # worker-root removal behind the typed gate. It takes no other
        # mode's flags; each combination refuses by name BEFORE any mode
        # runs (deterministic, never order-dependent).
        if args.merge:
            sys.exit(
                "[Error] --cleanup cannot combine with --merge: cleanup "
                "verifies the ALREADY-merged root and removes the "
                "worker roots — run --merge first, then --cleanup"
            )
        if args.mode == "dispatch":
            sys.exit(
                "[Error] --cleanup cannot combine with --mode dispatch: "
                "dispatch mode writes ONE shared root (MGPU-06) with no "
                "per-worker roots to clean up"
            )
        if args.dry_run:
            sys.exit(
                "[Error] --cleanup cannot combine with --dry-run: "
                "cleanup verifies and gates BEFORE anything is removed — "
                "there is nothing to dry-run"
            )
        if args.models is not None:
            sys.exit(
                "[Error] --cleanup takes no --models (the merged "
                "manifest is the cleanup's source of truth)"
            )
        if passthrough:
            sys.exit(
                "[Error] --cleanup takes no sweep flags; unrecognized "
                f"token(s): {passthrough}"
            )
        return run_cleanup(args, passthrough)
    if args.merge:
        return run_merge(args, passthrough)
    if args.mode == "dispatch":
        # Lazy import (the 09-06 WizardModal cycle-breaking precedent):
        # dispatch_core imports THIS module at its top (it reuses
        # _parse_gpus and the log-stamp format), so a module-top import
        # here would be circular.
        import dispatch_core

        return dispatch_core.run_dispatch(
            args, passthrough, spawner=spawner, clock=clock)
    problems = []

    # --models is launch-mode-required at the validation layer (argparse
    # cannot express "required unless --merge"); 12-04's merge mode reads
    # the worker manifests instead and takes no --models
    if args.models is None:
        problems.append(
            "--models is required for launch mode (only --merge runs "
            "without it)"
        )

    # --workers sanity
    workers = args.workers
    if workers < 1:
        problems.append(f"--workers must be >= 1, got {workers}")

    # --gpus parse (collect problems) + arity (only meaningful once the
    # token list parsed; the default assignment happens after the
    # collect-all exit so a broken flag never reaches the spawn loop)
    gpus = _parse_gpus(args.gpus, problems)
    if gpus is not None and workers >= 1 and len(gpus) != workers:
        problems.append(
            f"--gpus arity mismatch: {len(gpus)} GPU id(s) for "
            f"--workers {workers} (one id per worker)"
        )

    # --models parse: a provided value stripping to nothing must refuse,
    # never degrade to a full-registry shard (the WR-14 discipline)
    models = []
    if args.models is not None:
        models = sorted(
            {m.strip() for m in args.models.split(",") if m.strip()})
        if not models:
            problems.append(
                f"--models {args.models!r} produced no model names after "
                "stripping empty elements"
            )

    # Registry join: every requested name must exist in the SAME
    # registry view the workers will use (a passthrough --registry-dir
    # is honored for the join but still forwards verbatim)
    models_info = registry_loader.load_models_registry(
        _registry_dir_from_passthrough(passthrough))
    unknown_models = sorted(set(models) - set(models_info))
    if unknown_models:
        problems.append(f"--models names not in registry: {unknown_models}")

    # Empty-shard refusal (WR-07 shape): fewer models than workers would
    # spawn no-op workers that still write fresh empty manifests into
    # fresh roots — refuse naming both counts
    if models and workers >= 1 and len(models) < workers:
        problems.append(
            f"--workers {workers} exceeds the {len(models)} requested "
            "model(s) — every worker needs at least one model"
        )

    # Frozen-root collision refusal (T-12-01-01): with the frozen naming
    # function the sibling roots are distinct by construction, so this
    # guard is defense-in-depth — a future naming change must not be
    # able to silently reintroduce the root-level manifest collision
    # (Pitfall 1: shared roots are FORBIDDEN, not merely sloppy)
    base_root = Path(args.output_root).resolve()
    if workers >= 1:
        worker_roots = [worker_root(base_root, i) for i in range(workers)]
        colliding_base = [i for i, root in enumerate(worker_roots)
                          if root == base_root]
        if colliding_base:
            problems.append(
                f"worker root(s) {colliding_base} equal the base output "
                f"root {base_root} — workers must write SIBLING roots "
                f"({base_root}-mgpu-w{{i}}), never the base root itself"
            )
        seen = {}
        for i, root in enumerate(worker_roots):
            if root in seen:
                problems.append(
                    f"worker roots {seen[root]} and {i} collide on "
                    f"{root} — each worker must own exactly one "
                    "disjoint root"
                )
            else:
                seen[root] = i

    if problems:
        sys.exit(f"[Error] {'; '.join(problems)}")

    # Default GPU assignment: the worker index as a string (operator-
    # owned strings; no device probing, D-05)
    if gpus is None:
        gpus = [str(i) for i in range(workers)]

    # LPT shard over the registry's size (M) weights (0.0 when unusable)
    sizes = {name: entry.get("size (M)") for name, entry
             in models_info.items()}
    shards = lpt_shard(models, workers, sizes)

    seam = _DEFAULT_SPAWNER if spawner is None else spawner
    # ONE stamp per launch, shared by every worker tee log (WR-02: the
    # sweep_launcher TEE_TIMESTAMP_FORMAT discipline — each relaunch
    # derives a fresh filename instead of truncating the prior crash log)
    now = datetime.now if clock is None else clock
    launch_stamp = now().strftime(WORKER_LOG_TIMESTAMP_FORMAT)
    procs = []
    tees = []
    log_paths = []
    try:
        for i in range(workers):
            root_i = worker_root(base_root, i)
            log_i = worker_log_path(base_root, i, launch_stamp)
            argv = [
                sys.executable,
                str(WORKER_SCRIPT),
                "--models", ",".join(shards[i]),
                "--output-root", str(root_i),
            ]
            argv.extend(passthrough)
            if args.dry_run:
                argv.append("--dry-run")
            print(
                f"[Worker {i}] gpu={gpus[i]} models={len(shards[i])} "
                f"root={root_i} log={log_i}"
            )
            log_i.parent.mkdir(parents=True, exist_ok=True)
            # Deliberately NOT a context manager (SIM115, the launcher's
            # rationale): the tee handle must stay open for the child's
            # whole lifetime — a with-block would close it before the
            # child ever writes. Held here, closed after the wait loop.
            tee = open(  # noqa: SIM115
                log_i, "w", encoding="utf-8")
            tees.append(tee)
            log_paths.append(log_i)
            procs.append(seam(
                list(argv),
                start_new_session=True,
                cwd=str(run_sweep.PIPELINE_DIR),
                env={
                    **os.environ,
                    "PYTHONUNBUFFERED": "1",
                    "CUDA_VISIBLE_DEVICES": gpus[i],
                },
                stdout=tee,
                stderr=subprocess.STDOUT,
            ))
    except OSError as exc:
        for tee in tees:
            tee.close()
        sys.exit(
            f"[Error] spawning worker failed: {exc} — already-spawned "
            "workers keep running (separate sessions by design; see the "
            "killpg recipe in the module docstring)"
        )

    # Wait ALL workers: a dead worker never prevents its siblings from
    # being waited and reported (death isolation, SC2)
    codes = [proc.wait() for proc in procs]
    for tee in tees:
        tee.close()

    print("Worker verdicts:")
    for i in range(workers):
        failed = _failed_cell_count(worker_root(base_root, i))
        failed_display = "-" if failed is None else failed
        print(
            f"  worker {i}: exit={codes[i]} failed={failed_display} "
            f"root={worker_root(base_root, i)} "
            f"log={log_paths[i]}"
        )
    failed_workers = sum(1 for code in codes if code != 0)
    if failed_workers == 0:
        print(f"All {workers} worker(s) exited 0.")
        return
    print(
        f"{failed_workers}/{workers} worker(s) failed — isolation holds: "
        "a dead worker never touched its siblings (independent sessions "
        "+ disjoint roots); re-run one worker's failed cells with "
        "run_sweep.py --from-failures <worker root>/sweep_failures.json "
        "--output-root <worker root> [same lane flags as this launch]"
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
