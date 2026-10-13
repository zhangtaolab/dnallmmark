"""
Multi-worker sweep orchestration: launch mode (12-01, MGPU-01/SC1, D-07).

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

Every token the orchestrator does not own (``--tasks``, ``--seeds``,
``--peft``, ``--num_train_epochs``, ``--registry-dir``, ...) is passed
through VERBATIM to every worker after the orchestrator's own flags —
``run_sweep.py`` stays the single owner of sweep-flag validation and
help. Task/seed flag problems therefore surface INSIDE each worker at
its own startup and are reported in this orchestrator's verdict table
(a worker that dies at argv validation exits non-zero like any other
dead worker).

Frozen naming (ONE authority — 12-04's ``--merge`` imports these exact
functions, so launch and merge can never disagree about where worker
artifacts live)::

    worker root: {output-root}-mgpu-w{i}      (a SIBLING of the base root)
    worker log:  {output-root}-mgpu-w{i}.log  (a SIBLING of the worker root)

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
- Worker stdout/stderr tee into the per-worker sibling log (stderr is
  redirected onto stdout's handle); the orchestrator waits ALL workers
  and reports an aggregated verdict — exit 0 iff every worker exited 0,
  otherwise exit 1 after a per-worker verdict table (exit code, worker
  root, log path, failed-cell count read from that worker's
  ``sweep_failures.json`` when present). A dead worker never touches
  its siblings: independent sessions + disjoint roots (SC2).

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
import json
import os
import subprocess
import sys
from pathlib import Path

import registry_loader  # sibling module (pipeline/ on sys.path)
import run_sweep  # sibling module: PIPELINE_DIR + the worker entry

WORKER_SCRIPT = run_sweep.PIPELINE_DIR / "run_sweep.py"

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


def worker_log_path(base_root, index):
    """Return the per-worker tee log path — the worker root's ``.log``
    sibling (a sibling of the root, never inside it: the artifact tree
    stays pure and the log survives root-cleanup decisions)."""
    return Path(f"{worker_root(base_root, index)}.log")


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
    two merge-mode flags (``--merge``, ``--include-checkpoints`` — 12-04);
    every UNRECOGNIZED token from the command line lands in the returned
    remainder. In LAUNCH mode the remainder is appended VERBATIM to every
    worker argv (run_sweep stays the single owner of sweep-flag
    validation and help — the D-07 argv-surface-minimization answer); in
    MERGE mode it must be EMPTY (a merge takes no sweep flags).
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
             "{base}-mgpu-w{i} with its tee log at {base}-mgpu-w{i}.log — "
             "shared roots are forbidden (root-level manifests collide)"
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
    return parser.parse_known_args(argv)


def _parse_gpus(raw, problems):
    """Parse the ``--gpus`` comma list into ints, collecting problems.

    Args:
        raw (str | None): the flag value (None = default 0..workers-1).
        problems (list[str]): the collect-all problems list.

    Returns:
        list[int] | None: parsed ids, or None when the flag is absent or
        unusable (the caller decides the default).
    """
    if raw is None:
        return None
    gpus = []
    for token in raw.split(","):
        stripped = token.strip()
        if not stripped:
            problems.append(f"empty GPU id element in --gpus {raw!r}")
            continue
        try:
            gpus.append(int(stripped))
        except ValueError:
            problems.append(f"non-numeric GPU id {stripped!r} in --gpus")
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
# Interface skeleton (RED stage): the flags parse and the seams exist so
# the behavior rows can fail against a cleanly importing module; the
# merge behavior itself lands with the GREEN commit.

#: The data-artifact allowlist copied per cell dir: the five JSON
#: artifacts every downstream consumer reads (export_runs walks
#: run_record.json and adopts seed_result.json; trainer_state.json is the
#: resume marker / global_step source; final_metrics.json is the
#: training-failure signal; flops_report.json is the FLOPs evidence).
#: checkpoint-*/ and runs/ are EXCLUDED by default and join only under
#: the explicit --include-checkpoints escape hatch (research A2).
MERGE_ALLOWLIST = (
    "run_record.json",
    "final_metrics.json",
    "trainer_state.json",
    "seed_result.json",
    "flops_report.json",
)


def _copy_verified(src, dst):
    """Copy one file with D-09 verification: SHA256 the source, copy,
    re-hash the destination, compare. Never a symlink, never a move."""
    raise NotImplementedError("12-04 merge mode: pending GREEN")


def _rewrite_output_dir(cell_dir_str, worker_root, merged_root):
    """Startswith-guarded prefix swap of a cell/failure ``output_dir``
    from its worker root onto the merged root; a non-matching prefix
    passes through unchanged (defensive)."""
    raise NotImplementedError("12-04 merge mode: pending GREEN")


def run_merge(args, passthrough):
    """Merge N frozen-named worker roots into one verified consumer root
    (validation collect-all, allowlist copy + SHA256 verify, manifest and
    failures union with output_dir rewrite, lane-flag equality)."""
    raise NotImplementedError("12-04 merge mode: pending GREEN")


def main(spawner=None):
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
    """
    args, passthrough = parse_args()
    if args.merge:
        return run_merge(args, passthrough)
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

    # Default GPU assignment: the worker index (operator-owned strings;
    # no device probing, D-05)
    if gpus is None:
        gpus = list(range(workers))

    # LPT shard over the registry's size (M) weights (0.0 when unusable)
    sizes = {name: entry.get("size (M)") for name, entry
             in models_info.items()}
    shards = lpt_shard(models, workers, sizes)

    seam = _DEFAULT_SPAWNER if spawner is None else spawner
    procs = []
    tees = []
    try:
        for i in range(workers):
            root_i = worker_root(base_root, i)
            log_i = worker_log_path(base_root, i)
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
            procs.append(seam(
                list(argv),
                start_new_session=True,
                cwd=str(run_sweep.PIPELINE_DIR),
                env={
                    **os.environ,
                    "PYTHONUNBUFFERED": "1",
                    "CUDA_VISIBLE_DEVICES": str(gpus[i]),
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
            f"log={worker_log_path(base_root, i)}"
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
