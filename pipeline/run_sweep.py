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
        "peft": "none" | "lora" | "ia3",
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
regenerated, never diffed — and a resumed sweep's ``skipped`` cells
therefore never rewrite an existing ``run_record.json`` (WR-12): the
previous run's record (its status, metrics, commit, timestamps) is the
cell's provenance, and this run's skipped view is reported by the
manifest only. Everything else is deterministic — the matrix
iterates in ``sorted()`` order (with an optional ``--priority-file`` tier
order as the primary key composed over that stable fallback, 05-04) and
every JSON file is written with
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
    reliable training-failure signal from the child — OR when the file
    is present but not valid JSON (WR-11): the child writes it inside
    its D-08 blind-except scope, so a mid-write death (e.g. disk full)
    can leave a truncated file with the child still exiting 0 —
    child-data corruption, not a driver bug, so it fails the cell and
    the sweep continues instead of an uncaught ``JSONDecodeError``
    aborting every remaining cell. Any other exception is a
    driver/executor BUG and aborts the sweep loudly instead of being
    recorded across thousands of cells (and no blind ``except Exception``
    is introduced: D-08 forbids noqa outside run_finetune.py's three
    designed isolation sites).

--dry-run:
    Enumerates the matrix and writes ONLY ``sweep_manifest.json``
    (planned cells with status ``planned`` + their planned seed-isolated
    outdirs) — no subprocess, no cell directories, no run records — which
    is what makes the runner fully CPU-testable under D-05.

--priority-file (05-04, E2' degradation order):
    A maintainer-curated JSON file — an ordered list of tiers, each a list
    of entries that are either bare model names or ``{model, task}`` specs
    (``pipeline/sweep_priorities.json`` is the committed instance: tier 1 =
    the PIPE-03 E2E pair; tier 2 = the maintainer-curated arena
    representatives, one per arena — animal GENERanno-eukaryote-0.5b-base,
    plant PlantCAD2-Small-l24-d0768, microbe Omni-DNA-700M — curated at the
    2026-10-10 Task-4 gate from the committed weighted_score arena leaders
    excluding the tier-1 pair). The
    tiers compose as the PRIMARY sort key — rank ``(tier index, entry
    specificity)``, a ``{model, task}`` spec outranking a bare model name
    within its tier, a cell matching several entries taking its best rank
    — over the existing ``sorted()`` cell order as the STABLE fallback, so
    unmatched cells keep today's exact order and seeds stay adjacent within
    a cell. Determinism is preserved when the file is absent: no flag, no
    reordering at all (byte-identical default enumeration). The file is
    validated fail-fast BEFORE any cell is enumerated: unknown model/task
    names vs the registries and structure problems are ALL listed, then
    the driver exits non-zero (the _validate_filters discipline, T-05-09).

--from-failures (05-04, failure recovery):
    ``--from-failures <sweep_failures.json>`` re-enumerates exactly the
    failed (model, task) pairs named in the manifest, across ALL requested
    seeds. Completed cells were already skipped by the seed-scoped resume
    marker, so simply re-running the same sweep command re-attempts
    exactly the failed cells — the filter exists to avoid re-enumerating
    ~9,300 cells (62x50x3) and to guard against typo'd manual
    ``--models/--tasks`` re-run filters (research Pattern 6). A CLEAN
    manifest (empty list — written on every run, WR-06) yields an EXPLICIT
    zero-cell run with a clear message, never a silent full sweep. The
    manifest is validated fail-fast exactly like the priority file.

--peft (06-02, SC-6/REV-05 adapter lanes):
    ``--peft {none,lora,ia3}`` (default ``none``) threads the adapter mode
    through the whole matrix: cells enumerate under the ALIAS model name
    ``{model}+lora`` / ``{model}+ia3`` (the output-dir and resume-marker
    identity) while the registry and the ``--models`` filter join stays on
    BASE names; each cell's argv targets ``--target_model <base>`` and
    appends ``--save_model_name <alias>`` + ``--peft <mode>`` as separate
    LIST elements (T-03-10 continuity); ``run_record.json`` gains a ``peft``
    field (default ``"none"``). Alias cells are name-isolated end-to-end:
    a separate model-level dir means a separate ``trainer_state.json``
    resume marker, so the seed-dir layout and the marker-skip logic are
    UNTOUCHED (an alias marker never skips a base cell). ``none`` is
    byte-identical to today's enumeration, argv, and records.

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
import functools
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

    parser.add_argument(
        "--priority-file",
        type=str,
        default=None,
        help="Maintainer-curated JSON of ordered tiers (each a list of bare "
             "model names or {model, task} specs) executed FIRST — the E2' "
             "degradation order; composed over the sorted() fallback "
             "(default: no reordering, today's exact order)"
    )

    parser.add_argument(
        "--from-failures",
        type=str,
        default=None,
        help="A sweep_failures.json manifest; re-enumerate exactly its "
             "failed (model, task) pairs across all requested seeds — a "
             "clean manifest yields an explicit zero-cell run, never a "
             "silent full sweep"
    )

    parser.add_argument(
        "--peft",
        type=str,
        default="none",
        choices=["none", "lora", "ia3"],
        help="Parameter-efficient mode threaded to every run_finetune.py "
             "subprocess (SC-6 adapter lanes, 06-02): 'lora'/'ia3' "
             "enumerate cells under the alias model names {model}+lora / "
             "{model}+ia3 (separate output dirs AND resume markers; "
             "registry filtering stays on base names, argv targets "
             "--target_model <base> --save_model_name <alias> --peft "
             "<mode>); 'none' (default) is byte-identical to today"
    )

    return parser.parse_args()


def enumerate_matrix(models_filter, tasks_filter, seeds, registry_dir,
                     peft="none"):
    """Build the sorted (model, task, seed) cell list from the registries.

    Under ``peft`` lora/ia3 (06-02) the emitted cells carry the ALIAS
    model name ``{model}+{mode}`` — the output-dir / resume-marker
    identity — while the registry iteration and the ``--models`` filter
    join stay on BASE names (argv targeting re-derives the base via
    suffix strip in ``build_argv``). Sorting happens AFTER the alias
    mapping, so the enumeration stays deterministic.

    Args:
        models_filter (list[str] | None): restrict to these models_info.json
            keys (BASE names); None means all keys.
        tasks_filter (list[str] | None): restrict to these datasets_info.json
            keys; None means every entry with truthy Train.
        seeds (list[int]): seed values to fan out per (model, task) pair.
        registry_dir (Path | str): directory holding the unified JSON
            registries (the D-10 single source — there is no .txt to read).
        peft (str): adapter mode (none/lora/ia3); none emits base-name
            cells byte-identical to the pre-peft enumeration.

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

    def cell_model(model):
        return f"{model}+{peft}" if peft != "none" else model

    return sorted(
        (cell_model(model), task, seed)
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


def _load_registry_key_sets(registry_dir):
    """Load the registry KEY sets both operator-input validators join on,
    plus the set of tasks that can never run (falsy ``Train``).

    Args:
        registry_dir (Path | str): directory holding the unified JSON
            registries (the D-10 single source).

    Returns:
        tuple[set, set, set]: ``(model keys, dataset keys, Train-falsy
        dataset keys)`` — the operator-input validators refuse a requested
        task from the third set for the same reason ``_validate_filters``
        does: the matrix can never run it, so accepting it would be
        silently inert.
    """
    registry_dir = Path(registry_dir)
    with open(registry_dir / "models_info.json", "r", encoding="utf-8") as f:
        models_info = json.load(f)
    with open(registry_dir / "datasets_info.json", "r", encoding="utf-8") as f:
        datasets_info = json.load(f)
    no_train_tasks = {
        task for task, row in datasets_info.items() if not row.get("Train")
    }
    return set(models_info), set(datasets_info), no_train_tasks


def _read_operator_json(path, flag_name):
    """Read an operator-supplied JSON file, exiting non-zero naming the
    file when it is unreadable or not valid JSON.

    Args:
        path (str): The flag's value (displayed in errors).
        flag_name (str): The flag name (displayed in errors).

    Returns:
        The parsed JSON value.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except OSError as exc:
        sys.exit(f"[Error] cannot read {flag_name} file {path}: {exc}")
    except json.JSONDecodeError as exc:
        sys.exit(f"[Error] {flag_name} file {path} is not valid JSON: {exc}")


def load_priority_tiers(path, registry_dir):
    """Parse and validate a --priority-file (fail-fast, all problems listed).

    The file must be a JSON ordered list of tiers; each tier a list of
    entries that are either bare model names (strings) or ``{model, task}``
    specs (a spec may omit ``task``, covering the model's every task).
    Unknown model/task names vs the registries, tasks with no train split
    (falsy ``Train`` — the _validate_filters discipline: the matrix can
    never run them, so prioritizing them would be silently inert), and
    every structural problem are collected and reported TOGETHER
    (T-05-09) BEFORE any cell is enumerated — the file steers multi-day
    GPU execution order, so a typo must fail fast.

    Args:
        path (str): --priority-file value.
        registry_dir (Path | str): directory holding the unified JSON
            registries.

    Returns:
        list[list[tuple[str, str | None]]]: tiers of ``(model, task)``
        entries (``task`` None for a bare model name).

    Raises:
        SystemExit: listing every problem.
    """
    raw = _read_operator_json(path, "--priority-file")
    if not isinstance(raw, list):
        sys.exit(
            "[Error] --priority-file must be a JSON list of tiers "
            f"(a list of lists), got: {type(raw).__name__} in {path}"
        )
    known_models, known_tasks, no_train_tasks = _load_registry_key_sets(registry_dir)
    problems = []
    tiers = []
    for tier_idx, tier in enumerate(raw):
        if not isinstance(tier, list):
            problems.append(
                f"tier {tier_idx} is not a list: {tier!r}"
            )
            tiers.append([])
            continue
        parsed_tier = []
        for entry_idx, entry in enumerate(tier):
            where = f"tier {tier_idx} entry {entry_idx}"
            if isinstance(entry, str):
                model, task = entry, None
            elif isinstance(entry, dict):
                extra_keys = sorted(set(entry) - {"model", "task"})
                if extra_keys:
                    problems.append(
                        f"{where} has unknown key(s) {extra_keys} — entries "
                        "are bare model names or {model, task} specs"
                    )
                    continue
                model = entry.get("model")
                task = entry.get("task")
                if not isinstance(model, str):
                    problems.append(
                        f"{where} is missing the 'model' key of its "
                        "{model, task} spec"
                    )
                    continue
                if task is not None and not isinstance(task, str):
                    problems.append(
                        f"{where} has a non-string 'task': {task!r}"
                    )
                    continue
            else:
                problems.append(
                    f"{where} is neither a bare model name nor a "
                    f"{{model, task}} spec: {entry!r}"
                )
                continue
            if model not in known_models:
                problems.append(
                    f"--priority-file model not in registry: {model!r} ({where})"
                )
                continue
            if task is not None and task not in known_tasks:
                problems.append(
                    f"--priority-file task not in registry: {task!r} ({where})"
                )
                continue
            if task is not None and task in no_train_tasks:
                problems.append(
                    "--priority-file task has no train split (Train is "
                    f"falsy): {task!r} ({where})"
                )
                continue
            parsed_tier.append((model, task))
        tiers.append(parsed_tier)
    if problems:
        sys.exit(f"[Error] {'; '.join(problems)}")
    return tiers


def apply_priority_order(cells, tiers):
    """Stable-reorder cells by priority tier rank over the sorted() fallback.

    Rank ``(tier index, entry specificity)`` is the PRIMARY sort key; a
    ``{model, task}`` spec (specificity 0) outranks a bare model name
    (specificity 1) within its tier; a cell matching several entries takes
    its BEST rank; unmatched cells rank after every tier. Python's sort is
    stable, so equal ranks keep the incoming (``sorted()``) order — seeds
    stay adjacent within a (model, task) cell because rank depends only on
    the (model, task) pair. With no matching entries anywhere the incoming
    order is returned unchanged (the byte-identical default contract).

    Args:
        cells (list[tuple[str, str, int]]): (model, task, seed) cells in
            the sorted() default order.
        tiers (list[list[tuple[str, str | None]]]): parsed priority tiers
            (see load_priority_tiers).

    Returns:
        list[tuple[str, str, int]]: the reordered cells.
    """
    fallback_rank = (len(tiers), 0)
    rank_cache = {}

    def pair_rank(model, task):
        key = (model, task)
        if key in rank_cache:
            return rank_cache[key]
        best = fallback_rank
        for tier_idx, tier in enumerate(tiers):
            for entry_model, entry_task in tier:
                if entry_model != model:
                    continue
                if entry_task is None or entry_task == task:
                    # A {model, task} spec (task set) is more specific than
                    # a bare model name within the same tier.
                    candidate = (tier_idx, 0 if entry_task is not None else 1)
                    best = min(best, candidate)
        rank_cache[key] = best
        return best

    return sorted(cells, key=lambda cell: pair_rank(cell[0], cell[1]))


def load_failure_pairs(path, registry_dir):
    """Parse and validate a --from-failures sweep_failures.json manifest.

    Extracts the failed ``(model, task)`` pairs (the seed is per-record;
    the re-run fans out over ALL requested seeds). Unknown model/task
    names vs the registries, tasks with no train split (falsy ``Train`` —
    the _validate_filters discipline: the matrix can never run them, so
    re-running them would be silently inert), and structural problems are
    collected and reported together, fail-fast.

    Args:
        path (str): --from-failures value (a sweep_failures.json file).
        registry_dir (Path | str): directory holding the unified JSON
            registries.

    Returns:
        set[tuple[str, str]]: the distinct failed (model, task) pairs.

    Raises:
        SystemExit: naming the file (unreadable/not JSON/not a list) or
            listing every key/structure problem.
    """
    raw = _read_operator_json(path, "--from-failures")
    if not isinstance(raw, list):
        sys.exit(
            f"[Error] --from-failures file {path} must be a JSON list of "
            f"failure entries, got: {type(raw).__name__}"
        )
    known_models, known_tasks, no_train_tasks = _load_registry_key_sets(registry_dir)
    problems = []
    pairs = set()
    for idx, entry in enumerate(raw):
        if not isinstance(entry, dict):
            problems.append(
                f"--from-failures entry {idx} is not an object: {entry!r}"
            )
            continue
        model = entry.get("model")
        task = entry.get("task")
        if not isinstance(model, str) or not isinstance(task, str):
            problems.append(
                f"--from-failures entry {idx} is missing string "
                "'model'/'task' keys"
            )
            continue
        if model not in known_models:
            problems.append(
                f"--from-failures model not in registry: {model!r} (entry {idx})"
            )
            continue
        if task not in known_tasks:
            problems.append(
                f"--from-failures task not in registry: {task!r} (entry {idx})"
            )
            continue
        if task in no_train_tasks:
            problems.append(
                "--from-failures task has no train split (Train is falsy): "
                f"{task!r} (entry {idx})"
            )
            continue
        pairs.add((model, task))
    if problems:
        sys.exit(f"[Error] {'; '.join(problems)}")
    return pairs


def cell_dir_for(output_root, model, task, seed):
    """Return the seed-isolated cell dir {root}/{model}/{task}/seed_{seed}."""
    return Path(output_root) / model / task / f"seed_{seed}"


def build_argv(model, task, seed, output_root, peft="none"):
    """Build the run_finetune.py argv for one cell — a LIST, never a string.

    Under ``peft`` lora/ia3 (06-02) the cell's model is the ALIAS
    (``{base}+{mode}``): argv targets the BASE registry name via
    ``--target_model`` (suffix-stripped — the alias is not a registry key)
    and appends ``--save_model_name <alias>`` + ``--peft <mode>`` as
    separate LIST elements, so the child resolves the alias save name
    explicitly and writes its outputs under the alias dir (name isolation
    end-to-end). Under ``none`` the argv is byte-identical to the pre-peft
    form — no extra elements.

    Args:
        model (str): value for the cell's model identity — the BASE name
            under peft=none, the ALIAS under lora/ia3 (value for
            --save_model_name then; --target_model gets the strip).
        task (str): value for --target_dataset.
        seed (int): value for --seed.
        output_root (str | Path): ABSOLUTE root for --output_dir (the
            subprocess resolves it against its own cwd, which is pinned
            to pipeline/ — see the module docstring's invocation contract).
        peft (str): adapter mode none/lora/ia3.

    Returns:
        list[str]: the argv, each flag and value a separate element.
    """
    argv = [
        sys.executable,
        str(RUN_FINETUNE),
        "--target_model",
        str(model.removesuffix(f"+{peft}") if peft != "none" else model),
        "--target_dataset", str(task),
        "--seed", str(seed),
        "--output_dir", str(output_root),
    ]
    if peft != "none":
        argv += ["--save_model_name", str(model), "--peft", peft]
    return argv


def launch_subprocess(model, task, seed, output_root, peft="none"):
    """Default executor: run run_finetune.py for one cell.

    cwd is pinned to PIPELINE_DIR because finetune_config.yaml and the
    ./finetuned default are CWD-relative in run_finetune.py (research
    Pitfall 3); shell is never used (T-03-10).

    Raises:
        subprocess.CalledProcessError: the run exited nonzero (check=True).
        OSError: the subprocess could not be spawned.
    """
    return subprocess.run(
        build_argv(model, task, seed, output_root, peft),
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


def _new_record(model, task, seed, cell_dir, git_commit, peft="none"):
    """Build the run_record skeleton (statuses/timestamps filled by caller).

    The ``peft`` field (06-02, string, default ``"none"``) marks the
    adapter mode the sweep was launched with — the frontier row derivation
    reads it (alias-suffix first, this field as the record-level source).
    """
    return {
        "model": model,
        "task": task,
        "seed": seed,
        "peft": peft,
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


def run_matrix(cells, output_root, executor=None, peft="none"):
    """Execute the sweep matrix, writing run records + manifests.

    Per cell (in the GIVEN order — ``main()`` passes the ``sorted()``
    enumeration, priority-ordered first when a ``--priority-file`` drives
    the sweep; direct callers pass whatever order they choose, and this
    function never re-sorts, so a priority order survives to the
    executor): a pre-existing trainer_state.json in the
    cell dir marks the cell ``skipped`` with NO executor invocation and
    WITHOUT overwriting any existing run_record.json (WR-12: the
    previous run's record is the cell's provenance; a fresh skipped
    record is written only when none exists — e.g. a standalone
    run_finetune.py invocation left the marker but no record);
    otherwise the executor runs, and on success the cell's
    final_metrics.json keys are copied VERBATIM into the record's
    ``metrics`` (suite-native — translation is REV-03's job). A cell is
    recorded ``failed`` with the error text and an entry in the failures
    manifest when the executor raises (subprocess.SubprocessError /
    OSError — the launch-seam failure modes) OR when the executor exits
    0 but the cell dir has no final_metrics.json (CR-02:
    run_finetune.py's blind-except isolation makes a training failure
    exit 0 without writing metrics, so the missing file — not the exit
    status — is the training-failure signal) OR when final_metrics.json
    is present but not valid JSON (WR-11: the child writes it inside
    its blind-except scope, so a mid-write death can leave a truncated
    file with the child still exiting 0 — the cell fails and the sweep
    continues). sweep_failures.json is
    written on EVERY run — an empty list when no cell failed — so a
    stale failures manifest can never outlive its sweep (WR-06).

    Args:
        cells (list[tuple[str, str, int]]): (model, task, seed) cells in
            the intended execution order (never re-sorted here). Under
            --peft the model component is the ALIAS name — the cell dir,
            record, and manifest all key by it.
        output_root (str | Path): sweep output root (resolved absolute).
        executor (callable | None): ``executor(model, task, seed,
            output_root)``; defaults to launch_subprocess (bound with this
            call's ``peft`` so the real launch path composes the adapter
            argv). Injectable for the fake-executor tests (D-05: real mode
            is never launched this phase outside those tests).
        peft (str): adapter mode none/lora/ia3 (06-02) — carried into the
            run_record ``peft`` field and the default executor's argv.

    Returns:
        list[dict]: the run records, one per cell, in the given cell order.
    """
    executor = (
        executor if executor is not None
        else functools.partial(launch_subprocess, peft=peft)
    )
    output_root = Path(output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    git_commit = _git_commit()

    records = []
    failures = []
    for model, task, seed in cells:
        cell_dir = cell_dir_for(output_root, model, task, seed)
        record = _new_record(model, task, seed, cell_dir, git_commit, peft)
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
                    try:
                        with open(metrics_path, "r", encoding="utf-8") as f:
                            record["metrics"] = json.load(f)
                        record["status"] = "completed"
                    except json.JSONDecodeError as exc:
                        # WR-11: run_finetune.py writes final_metrics.json
                        # inside its D-08 blind-except scope, so a
                        # mid-write death (e.g. disk full) can leave a
                        # truncated file with the child still exiting 0 —
                        # child-data corruption, not a driver bug. Fail
                        # the cell and continue the sweep instead of
                        # letting the decode error abort every remaining
                        # cell with no manifest ever written.
                        record["status"] = "failed"
                        record["error"] = (
                            "final_metrics.json is corrupt/unreadable "
                            f"({exc}); the child left a partial file"
                        )
                        failures.append({
                            "model": model,
                            "task": task,
                            "seed": seed,
                            "output_dir": str(cell_dir),
                            "error": record["error"],
                        })
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
        record_path = cell_dir / RECORD_NAME
        # WR-12: never overwrite an existing record for a SKIPPED cell.
        # The on-disk record of the run that actually trained (or failed)
        # the cell — status, verbatim metrics, git commit, wall-clock
        # times — is the only provenance linking the cell's outcome to
        # the run that produced it ("recorded once at observation time,
        # never regenerated"). Overwriting it with this run's
        # skipped/metrics-null view would destroy that provenance on
        # every resumed sweep; the manifest reports THIS run's view of
        # the cell. A skipped cell with NO record yet still gets one.
        if record["status"] != "skipped" or not record_path.exists():
            _write_json(record_path, record)
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
    # WR-14: a PROVIDED --models/--tasks/--seeds whose value strips to
    # nothing (e.g. --models , --models "" --seeds ,) must abort, not
    # degrade. An empty filter list is falsy, which _validate_filters'
    # early return and enumerate_matrix's `if models_filter:` both treat
    # as "no filter" — silently enumerating the FULL registry matrix
    # while the operator believes the run was scoped — and an empty seed
    # set enumerates 0 cells, writes a manifest, and exits 0: both are
    # WR-07's silently-surprising-matrix hazard in new shapes, so fail
    # fast naming the flag and its raw value. An ABSENT --models/--tasks
    # keeps full-matrix semantics; only provided-but-empty fails.
    seeds = sorted({int(s.strip()) for s in args.seeds.split(",") if s.strip()})
    if not seeds:
        sys.exit(
            f"[Error] --seeds {args.seeds!r} produced no integer values "
            "after stripping empty elements; pass at least one seed, "
            "e.g. --seeds 42"
        )
    models_filter = None
    if args.models is not None:
        models_filter = [m.strip() for m in args.models.split(",") if m.strip()]
        if not models_filter:
            sys.exit(
                f"[Error] --models {args.models!r} produced no model names "
                "after stripping empty elements; refusing to silently "
                "enumerate the full model registry — omit --models to run "
                "all models"
            )
    tasks_filter = None
    if args.tasks is not None:
        tasks_filter = [t.strip() for t in args.tasks.split(",") if t.strip()]
        if not tasks_filter:
            sys.exit(
                f"[Error] --tasks {args.tasks!r} produced no task names "
                "after stripping empty elements; refusing to silently "
                "enumerate the full task registry — omit --tasks to run "
                "all trainable tasks"
            )

    # Fail fast on typo'd/untrainable filters BEFORE any cell is
    # enumerated (WR-07): an unknown name would otherwise intersect to an
    # empty matrix that writes a manifest and exits 0 "successfully".
    _validate_filters(models_filter, tasks_filter, registry_dir)
    # Operator-supplied steering inputs (05-04, T-05-09): validated the
    # same fail-fast way BEFORE enumeration — both steer multi-day GPU
    # execution, so a typo'd key must abort loudly, never silently
    # reorder or filter the wrong matrix.
    tiers = None
    if args.priority_file is not None:
        tiers = load_priority_tiers(args.priority_file, registry_dir)
    failure_pairs = None
    if args.from_failures is not None:
        failure_pairs = load_failure_pairs(args.from_failures, registry_dir)
    cells = enumerate_matrix(
        models_filter, tasks_filter, seeds, registry_dir, peft=args.peft)
    if tiers is not None:
        # Tier rank as the PRIMARY sort key over the sorted() fallback —
        # no file, no reordering (byte-identical default enumeration).
        cells = apply_priority_order(cells, tiers)
    if failure_pairs is not None:
        if failure_pairs:
            print(
                f"[From-failures] {len(failure_pairs)} failed (model, task) "
                f"pair(s) in {args.from_failures}; enumerating their cells "
                "across the requested seeds"
            )
        else:
            # A clean manifest is a legitimate outcome (the sweep
            # completed) — but it must be an EXPLICIT zero-cell run with a
            # clear message, never a silent fall-through to the full
            # matrix (the exact hazard the filter exists to guard).
            print(
                f"[From-failures] {args.from_failures} is clean (0 failed "
                "pairs) — explicit zero-cell run, NOT a full sweep"
            )
        cells = [
            cell for cell in cells if (cell[0], cell[1]) in failure_pairs
        ]

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

    records = run_matrix(cells, output_root, executor=None, peft=args.peft)
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
