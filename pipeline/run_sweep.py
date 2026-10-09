"""
Drive the model x task x seed fine-tuning sweep matrix (F2 / REV-02).

``run_finetune.py`` trains ONE model on ONE task under ONE seed per
invocation. This driver enumerates the full matrix from the unified JSON
registries and, per cell, launches one ``run_finetune.py`` subprocess,
then aggregates per-run records, a sweep manifest, and a failure manifest.
Per the 2026-10-09 maintainer directive (D-05), this phase implements and
unit-tests the runner WITHOUT a single model run: real mode is exercised
exclusively through the injectable executor seam in ``tests/test_sweep.py``
(the fake executor), and ``--dry-run`` is the only other sanctioned
execution — this driver must NEVER launch run_finetune.py for real this
phase.

Output layout (seed-isolated, G1/REV-02)::

    {output_root}/{model}/{task}/seed_{seed}/
        trainer_state.json   <- resume marker written by run_finetune.py
                                (per-seed: a different seed never skips)
        final_metrics.json   <- written by run_finetune.py
        run_record.json      <- written by THIS driver (schema below)

run_record.json schema (per seed dir)::

    {
        "model": "...", "task": "...", "seed": 42,
        "status": "completed" | "failed" | "skipped",
        "output_dir": ".../seed_42",
        "metrics": { ... },
        "vram_probe": {
            "gpu_mem_total": null, "init_max_mem": null,
            "batch_size": null, "gradient_accumulation_steps": null
        },
        "git_commit": "<repo HEAD at launch>",
        "started_at": "...", "finished_at": "...",
        "error": null
    }

``metrics`` carries the cell's ``final_metrics.json`` keys VERBATIM —
suite-native keys (e.g. ``eval_AUROC``), never pre-translated: the
suite-registry -> export-key mapping layer is REV-03 / Phase 4's explicit
deliverable with its own key-parity tests, and pre-mapping here would
duplicate that layer untested.

``vram_probe`` uses NULL-WHEN-UNKNOWN semantics per seed (REV-02):
``run_finetune.py`` today prints VRAM numbers (gpu_mem_total, init max
memory, batch size, grad_accum) to stdout without persisting them, so the
runner records ``null`` for each rather than inventing data; the four keys
document where the numbers will land once the pipeline persists them.

``started_at`` / ``finished_at`` / ``git_commit`` are RUNTIME OBSERVATIONS
(Phase 2 discipline): recorded once at observation time, never
regenerated, never diffed. Everything else is deterministic — the matrix
iterates in ``sorted()`` order and every JSON file is written with
``sort_keys=True, indent=4, ensure_ascii=False``, so two dry-runs over the
same inputs produce byte-identical manifests.

Invocation contract (cwd):
    Every ``run_finetune.py`` subprocess is launched with cwd pinned to
    THIS script's own directory (``pipeline/``) and an ABSOLUTE
    ``--output_dir``. ``run_finetune.py`` loads ``./finetune_config.yaml``
    and defaults its output root to ``./finetuned`` CWD-relatively
    (research Pitfall 3), so a subprocess launched from any other
    directory would fail to find its config or write outputs to the wrong
    root. The subprocess is built as an argv LIST —
    ``--target_model`` / ``--target_dataset`` / ``--seed`` /
    ``--output_dir`` as separate elements — and NEVER a shell string
    (T-03-10: registry values must not pass through a shell).

Registry contract (D-10 single source):
    The matrix derives from the unified JSON registries —
    ``models_info.json`` keys (the canonical model names) x
    ``datasets_info.json`` entries with truthy ``Train``. The .txt
    registries no longer exist (retired by plan 03-02).

Failure boundary:
    A cell is recorded ``failed`` when the executor raises a
    ``subprocess.SubprocessError`` or ``OSError`` — the failure modes of
    the launch seam — OR when the executor exits 0 but the cell dir has
    no ``final_metrics.json`` (CR-02): ``run_finetune.py``'s designed
    blind-except isolation (D-08) swallows a training failure and still
    exits 0 without writing metrics, so the missing file is the only
    reliable training-failure signal from the child. Any other exception
    is a driver/executor BUG and aborts the sweep loudly instead of being
    recorded across thousands of cells (and no blind ``except Exception``
    is introduced: D-08 forbids noqa outside run_finetune.py's three
    designed isolation sites).

--dry-run:
    Enumerates the matrix and writes ONLY ``sweep_manifest.json``
    (planned cells with status ``planned`` + their planned seed-isolated
    outdirs) — no subprocess, no cell directories, no run records — which
    is what makes the runner fully CPU-testable under D-05.

FUTURE E2E note (documented here, deliberately NOT executed — D-05):
    On-disk dataset directories are DOUBLE-NESTED after a fresh unzip of
    a suite archive (the zip extracts as ``suite-name/suite-name/task-dir``
    while ``datasets_info.json`` Dataset_path values expect
    ``datasets/suite-name/task-dir``). The extra nesting must be flattened
    before real runs resume at the E2E gate.

Usage (run from the repo root; the subprocess cwd is pinned internally)::

    # enumerate + manifest only (no subprocess, no cell dirs)
    python pipeline/run_sweep.py --dry-run \\
        --models plant-dnamamba-6mer --tasks GUE__emp_H3 \\
        --seeds 42,43 --output-root ./finetuned

See also:
    ``pipeline/run_finetune.py`` — the per-cell training entry point
    (its outdir construction carries the same seed_{seed} segment this
    driver's layout contract relies on).
    ``tests/test_sweep.py`` — the dry-run / fake-executor contract tests.
"""

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
RUN_FINETUNE = PIPELINE_DIR / "run_finetune.py"

MANIFEST_NAME = "sweep_manifest.json"
FAILURES_NAME = "sweep_failures.json"
RECORD_NAME = "run_record.json"
RESUME_MARKER = "trainer_state.json"
METRICS_NAME = "final_metrics.json"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Drive the model x task x seed fine-tuning sweep matrix "
                    "(run_finetune.py per cell)")

    parser.add_argument(
        "--models",
        type=str,
        default=None,
        help="Comma-separated model filter (default: all models_info.json keys)"
    )

    parser.add_argument(
        "--tasks",
        type=str,
        default=None,
        help="Comma-separated task filter (default: all datasets_info.json "
             "entries with truthy Train)"
    )

    parser.add_argument(
        "--seeds",
        type=str,
        required=True,
        help="Comma-separated integer seeds (one seed-isolated outdir per seed)"
    )

    parser.add_argument(
        "--output-root",
        type=str,
        default="./finetuned",
        help="Sweep output root (default: ./finetuned, resolved absolute; "
             "cells land under {root}/{model}/{task}/seed_{seed}/)"
    )

    parser.add_argument(
        "--registry-dir",
        type=str,
        default=None,
        help="Directory holding models_info.json / datasets_info.json "
             "(default: this script's own directory, i.e. pipeline/)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Enumerate the matrix and write ONLY sweep_manifest.json — "
             "no subprocess, no cell dirs, no run records"
    )

    return parser.parse_args()


def enumerate_matrix(models_filter, tasks_filter, seeds, registry_dir):
    """Build the sorted (model, task, seed) cell list from the registries.

    Args:
        models_filter (list[str] | None): restrict to these models_info.json
            keys; None means all keys.
        tasks_filter (list[str] | None): restrict to these datasets_info.json
            keys; None means every entry with truthy Train.
        seeds (list[int]): seed values to fan out per (model, task) pair.
        registry_dir (Path | str): directory holding the unified JSON
            registries (the D-10 single source — there is no .txt to read).

    Returns:
        list[tuple[str, str, int]]: sorted cells (model, task, seed).
    """
    registry_dir = Path(registry_dir)
    with open(registry_dir / "models_info.json", "r", encoding="utf-8") as f:
        models_info = json.load(f)
    with open(registry_dir / "datasets_info.json", "r", encoding="utf-8") as f:
        datasets_info = json.load(f)

    models = sorted(models_info)
    if models_filter:
        allowed_models = set(models_filter)
        models = [model for model in models if model in allowed_models]
    tasks = sorted(
        key for key, entry in datasets_info.items() if entry.get("Train")
    )
    if tasks_filter:
        allowed_tasks = set(tasks_filter)
        tasks = [task for task in tasks if task in allowed_tasks]
    return sorted(
        (model, task, seed)
        for model in models
        for task in tasks
        for seed in seeds
    )


def _validate_filters(models_filter, tasks_filter, registry_dir):
    """Fail fast on --models/--tasks names the registries do not know.

    A typo'd filter name would otherwise intersect with the registry keys
    to an EMPTY matrix that writes a manifest, prints "Sweep finished: 0
    cell(s)" and exits 0 — a silently successful no-op for a driver meant
    to launch multi-day GPU sweeps (WR-07). Tasks the operator explicitly
    requested that have no train split (falsy ``Train``) are refused for
    the same reason: the matrix can never run them, so enumerating them
    away silently is also a no-op.

    Args:
        models_filter (list[str] | None): requested --models names.
        tasks_filter (list[str] | None): requested --tasks names.
        registry_dir (Path | str): directory holding the unified JSON
            registries.

    Raises:
        SystemExit: listing the unknown and/or untrainable names.
    """
    if not models_filter and not tasks_filter:
        return
    registry_dir = Path(registry_dir)
    with open(registry_dir / "models_info.json", "r", encoding="utf-8") as f:
        models_info = json.load(f)
    with open(registry_dir / "datasets_info.json", "r", encoding="utf-8") as f:
        datasets_info = json.load(f)
    unknown_models = sorted(set(models_filter or []) - set(models_info))
    unknown_tasks = sorted(set(tasks_filter or []) - set(datasets_info))
    untrainable_tasks = sorted(
        task for task in (tasks_filter or [])
        if task in datasets_info and not datasets_info[task].get("Train")
    )
    problems = []
    if unknown_models:
        problems.append(f"--models names not in registry: {unknown_models}")
    if unknown_tasks:
        problems.append(f"--tasks names not in registry: {unknown_tasks}")
    if untrainable_tasks:
        problems.append(
            "--tasks with no train split (Train is falsy): "
            f"{untrainable_tasks}"
        )
    if problems:
        sys.exit(f"[Error] {'; '.join(problems)}")


def cell_dir_for(output_root, model, task, seed):
    """Return the seed-isolated cell dir {root}/{model}/{task}/seed_{seed}."""
    return Path(output_root) / model / task / f"seed_{seed}"


def build_argv(model, task, seed, output_root):
    """Build the run_finetune.py argv for one cell — a LIST, never a string.

    Args:
        model (str): value for --target_model.
        task (str): value for --target_dataset.
        seed (int): value for --seed.
        output_root (str | Path): ABSOLUTE root for --output_dir (the
            subprocess resolves it against its own cwd, which is pinned
            to pipeline/ — see the module docstring's invocation contract).

    Returns:
        list[str]: the argv, each flag and value a separate element.
    """
    return [
        sys.executable,
        str(RUN_FINETUNE),
        "--target_model", str(model),
        "--target_dataset", str(task),
        "--seed", str(seed),
        "--output_dir", str(output_root),
    ]


def launch_subprocess(model, task, seed, output_root):
    """Default executor: run run_finetune.py for one cell.

    cwd is pinned to PIPELINE_DIR because finetune_config.yaml and the
    ./finetuned default are CWD-relative in run_finetune.py (research
    Pitfall 3); shell is never used (T-03-10).

    Raises:
        subprocess.CalledProcessError: the run exited nonzero (check=True).
        OSError: the subprocess could not be spawned.
    """
    return subprocess.run(
        build_argv(model, task, seed, output_root),
        cwd=PIPELINE_DIR,
        check=True,
    )


def _utc_now_iso():
    """ISO-8601 UTC timestamp — a runtime observation, never regenerated."""
    return datetime.now(UTC).isoformat()


def _git_commit():
    """Return the repo HEAD sha at launch (None outside a git repo)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PIPELINE_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    return result.stdout.strip() or None


def _write_json(path, payload):
    """Deterministic JSON write (Phase 2 discipline)."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False, sort_keys=True)


def _new_record(model, task, seed, cell_dir, git_commit):
    """Build the run_record skeleton (statuses/timestamps filled by caller)."""
    return {
        "model": model,
        "task": task,
        "seed": seed,
        "status": None,
        "output_dir": str(cell_dir),
        "metrics": None,
        "vram_probe": {
            "gpu_mem_total": None,
            "init_max_mem": None,
            "batch_size": None,
            "gradient_accumulation_steps": None,
        },
        "git_commit": git_commit,
        "started_at": None,
        "finished_at": None,
        "error": None,
    }


def _manifest_payload(matrix, records):
    """Build the sweep manifest from matrix definition + cell records."""
    return {
        "matrix": matrix,
        "cells": [
            {
                "model": record["model"],
                "task": record["task"],
                "seed": record["seed"],
                "status": record["status"],
                "output_dir": record["output_dir"],
            }
            for record in records
        ],
    }


def run_matrix(cells, output_root, executor=None):
    """Execute the sweep matrix, writing run records + manifests.

    Per cell (in sorted order): a pre-existing trainer_state.json in the
    cell dir marks the cell ``skipped`` with NO executor invocation;
    otherwise the executor runs, and on success the cell's
    final_metrics.json keys are copied VERBATIM into the record's
    ``metrics`` (suite-native — translation is REV-03's job). A cell is
    recorded ``failed`` with the error text and an entry in the failures
    manifest when the executor raises (subprocess.SubprocessError /
    OSError — the launch-seam failure modes) OR when the executor exits
    0 but the cell dir has no final_metrics.json (CR-02:
    run_finetune.py's blind-except isolation makes a training failure
    exit 0 without writing metrics, so the missing file — not the exit
    status — is the training-failure signal). sweep_failures.json is
    written on EVERY run — an empty list when no cell failed — so a
    stale failures manifest can never outlive its sweep (WR-06).

    Args:
        cells (list[tuple[str, str, int]]): (model, task, seed) cells.
        output_root (str | Path): sweep output root (resolved absolute).
        executor (callable | None): ``executor(model, task, seed,
            output_root)``; defaults to launch_subprocess. Injectable for
            the fake-executor tests (D-05: real mode is never launched
            this phase outside those tests).

    Returns:
        list[dict]: the run records, one per cell, in sorted-cell order.
    """
    executor = executor if executor is not None else launch_subprocess
    output_root = Path(output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    git_commit = _git_commit()

    records = []
    failures = []
    for model, task, seed in sorted(cells):
        cell_dir = cell_dir_for(output_root, model, task, seed)
        record = _new_record(model, task, seed, cell_dir, git_commit)
        record["started_at"] = _utc_now_iso()
        if (cell_dir / RESUME_MARKER).exists():
            # Seed-scoped resume marker (G1): only THIS (model, task,
            # seed) cell is done — a sibling seed still runs.
            record["status"] = "skipped"
        else:
            cell_dir.mkdir(parents=True, exist_ok=True)
            try:
                executor(model, task, seed, str(output_root))
                metrics_path = cell_dir / METRICS_NAME
                if not metrics_path.exists():
                    # CR-02: run_finetune.py's designed blind-except
                    # isolation (D-08) swallows a training failure and
                    # still exits 0 WITHOUT writing final_metrics.json —
                    # so exit status alone cannot distinguish a completed
                    # training from a failed one. A successful executor
                    # with no metrics file IS a failed cell: record it
                    # failed (never "completed" with null metrics) so
                    # the per-cell audit artifacts never lie about the
                    # sweep's outcome.
                    record["status"] = "failed"
                    record["error"] = (
                        "executor exited 0 but final_metrics.json is "
                        "missing (run_finetune.py swallowed a training "
                        "failure)"
                    )
                    failures.append({
                        "model": model,
                        "task": task,
                        "seed": seed,
                        "output_dir": str(cell_dir),
                        "error": record["error"],
                    })
                else:
                    record["status"] = "completed"
                    with open(metrics_path, "r", encoding="utf-8") as f:
                        record["metrics"] = json.load(f)
            except (subprocess.SubprocessError, OSError) as exc:
                record["status"] = "failed"
                record["error"] = f"{type(exc).__name__}: {exc}"
                failures.append({
                    "model": model,
                    "task": task,
                    "seed": seed,
                    "output_dir": str(cell_dir),
                    "error": record["error"],
                })
        record["finished_at"] = _utc_now_iso()
        _write_json(cell_dir / RECORD_NAME, record)
        records.append(record)

    matrix = {
        "models": sorted({model for model, _, _ in cells}),
        "tasks": sorted({task for _, task, _ in cells}),
        "seeds": sorted({seed for _, _, seed in cells}),
        "output_root": str(output_root),
    }
    _write_json(output_root / MANIFEST_NAME, _manifest_payload(matrix, records))
    # Always write the failures manifest — an empty list when no cell
    # failed (WR-06): writing it only on failure would leave a previous
    # run's stale sweep_failures.json sitting next to a fresh
    # all-clean sweep_manifest.json, contradictory audit artifacts for
    # the same output root.
    _write_json(output_root / FAILURES_NAME, failures)
    return records


def main():
    # ========================= Configuration =========================
    args = parse_args()
    registry_dir = (
        Path(args.registry_dir).resolve() if args.registry_dir else PIPELINE_DIR
    )
    output_root = Path(args.output_root).resolve()
    seeds = sorted({int(s.strip()) for s in args.seeds.split(",") if s.strip()})
    models_filter = (
        [m.strip() for m in args.models.split(",") if m.strip()]
        if args.models else None
    )
    tasks_filter = (
        [t.strip() for t in args.tasks.split(",") if t.strip()]
        if args.tasks else None
    )

    # Fail fast on typo'd/untrainable filters BEFORE any cell is
    # enumerated (WR-07): an unknown name would otherwise intersect to an
    # empty matrix that writes a manifest and exits 0 "successfully".
    _validate_filters(models_filter, tasks_filter, registry_dir)
    cells = enumerate_matrix(models_filter, tasks_filter, seeds, registry_dir)

    if args.dry_run:
        matrix = {
            "models": sorted({model for model, _, _ in cells}),
            "tasks": sorted({task for _, task, _ in cells}),
            "seeds": sorted({seed for _, _, seed in cells}),
            "output_root": str(output_root),
        }
        planned_records = [
            {
                "model": model,
                "task": task,
                "seed": seed,
                "status": "planned",
                "output_dir": str(cell_dir_for(output_root, model, task, seed)),
            }
            for model, task, seed in cells
        ]
        output_root.mkdir(parents=True, exist_ok=True)
        _write_json(
            output_root / MANIFEST_NAME,
            {"matrix": matrix, "cells": planned_records},
        )
        print(
            f"[Dry-run] {len(cells)} planned cell(s) over "
            f"{len(matrix['models'])} model(s) x {len(matrix['tasks'])} "
            f"task(s) x {len(matrix['seeds'])} seed(s); manifest: "
            f"{output_root / MANIFEST_NAME}"
        )
        return

    records = run_matrix(cells, output_root, executor=None)
    completed = sum(1 for r in records if r["status"] == "completed")
    skipped = sum(1 for r in records if r["status"] == "skipped")
    failed = sum(1 for r in records if r["status"] == "failed")
    print(
        f"Sweep finished: {len(records)} cell(s) — {completed} completed, "
        f"{skipped} skipped, {failed} failed; manifest: "
        f"{output_root / MANIFEST_NAME}"
    )
    if failed:
        print(f"Failures recorded in: {output_root / FAILURES_NAME}")


if __name__ == "__main__":
    main()
