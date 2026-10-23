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
        "config_variant": "none" | "head" | "probe" | "curve",
        "train_fraction": 0.25 | null,
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
    ~8,850 cells (59x50x3) and to guard against typo'd manual
    ``--models/--tasks`` re-run filters (research Pattern 6). Pairs join
    on BASE registry names: each failure entry records the cell identity
    (the ALIAS under ``--peft``) as ``model`` plus the registry name as
    ``base_model`` (MED-01, phase-06 review — a peft sweep's own manifest
    must feed back through this flag); the re-run's ``--peft`` mode
    re-derives the alias via enumerate_matrix, so a lora manifest
    recovered with ``--peft lora`` re-enumerates exactly the failed alias
    cells, and one recovered without ``--peft`` enumerates the base cells.
    Legacy alias-only manifests (no ``base_model``) recover through a
    known-suffix strip of ``model``. A CLEAN
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

--curve (06-05, SC-6/REV-08 F8 learning curves):
    ``--curve "0.25,0.5,1.0"`` (comma-separated train fractions in
    ``(0, 1]``) expands each (model, task, seed) cell into one cell per
    fraction — a (model, task, seed, fraction) 4-tuple — with output dirs
    ``{root}/{model}/{task}/seed_{seed}/frac_{f}/``: frac dirs NEST UNDER
    the seed dir, NEVER beside it (the trainer_state.json resume marker
    and the exporter walk stay (model, task, seed, fraction)-scoped; a
    sibling frac layout would corrupt both). The fraction list validates
    fail-fast collect-all (parse errors and bounds listed together,
    duplicates collapse, sorted ascending). Each cell's argv appends
    ``--train_fraction <f>`` as a separate LIST element;
    ``run_record.json`` gains a ``train_fraction`` field (float for curve
    cells, null otherwise). run_finetune applies the fraction to the
    TRAIN split only, via seed-governed shuffle-then-select — dev/test
    are untouched, so the eval_subsets discipline keeps test rows
    identical across fractions and models (the comparability guarantee
    the lane exists for). Dense checkpoints for offline harvesting come
    from the ``finetune_config_curve.yaml`` variant (eval/save every 100,
    logging every 50); ``extract_curve_points()`` reads the (step,
    eval-metrics) points back out of a trainer_state.json log_history.
    Composes with ``--peft`` (alias cells expand across fractions) and
    with ``--config-variant`` (alias cells expand across fractions the
    same way — ``{model}+probe/{task}/seed_{s}/frac_{f}/``).

--config-variant (11-01, D-18 — landed as ALIASING, never pass-through):
    ``--config-variant {head,probe,curve}`` threads the config-variant
    lane through the whole matrix using the existing ``--peft``
    aliasing machinery's exact shapes: cells enumerate under the ALIAS
    model name ``{model}+{variant}`` — ``head`` keeps the BASE name for
    exactly the frozen pair ``HEAD_KEEP_BASE_NAMES`` (verbatim from the
    child's save-name chain: their with-head config IS their base
    config) — while the registry and the ``--models`` filter join stays
    on BASE names; each cell's argv targets ``--target_model <base>``
    and appends ``--save_model_name <alias>`` + ``--config-variant <v>``
    as separate LIST elements. The explicit ``--save_model_name`` makes
    the DRIVER the single naming authority over the child's own
    identical self-aliasing branch (run_finetune.py:1198-1213): a pure
    pass-through would have every cell train successfully into the
    ``{model}+{variant}/`` dir the child derives on its own while the
    driver keys ``cell_dir_for`` on the base name — every cell recorded
    failed ("executor exited 0 but final_metrics.json is missing") and
    re-attempted forever (the retrain-forever trap, Phase 11 research
    Area 3). Variant and PEFT never compose: any both-set combination
    exits non-zero at sweep start naming both flags (two alias suffixes
    cannot name one cell; the child additionally refuses probe×peft at
    its argv boundary). ``run_record.json`` gains a ``config_variant``
    field (default ``"none"``, the peft-field precedent); the manifest
    merges ``config_variant`` into every cell via sweep_flags when the
    flag is present. Absent = byte-identical to today's enumeration,
    argv, and manifests.

--subset_file / --effective_batch_size / --num_train_epochs /
--cache_dir (07-03, PIPE-02 argv parity):
    Four pure pass-through flags threaded to every run_finetune.py child
    as separate LIST argv elements ONLY when present (underscore names
    only, zero alias mapping, D-11). An absent flag contributes ZERO argv
    elements — the child's YAML/defaults govern, byte-identical to today
    (D-12: ``--effective_batch_size`` accepts a BARE flag meaning 16 via
    ``nargs='?' const=16``). The GA arithmetic ``max(1, N // bs_new)``
    stays CHILD-side (run_finetune.py) — this driver never computes or
    re-derives gradient accumulation (D-10/D-16 product semantics). The
    two path flags resolve to ABSOLUTE paths at this layer BEFORE
    threading (D-15: the child cwd is pinned to pipeline/). Flag sanity
    (``effective_batch_size >= 1``, ``num_train_epochs >= 1``, non-empty
    subset path) is validated collect-all at startup, before any cell
    enumerates (Pitfall 5). ``--subset_file`` is additionally pre-validated
    ONCE at sweep start against the overlay-merged datasets registry
    (``_validate_subset_file``, D-14): every problem — unreadable,
    non-object, unknown registry key, malformed value — is listed together
    before a non-zero exit, never per-cell after model loads burn; the
    child's ``validate_subset_file`` remains the authoritative per-cell
    re-check (deliberate defense-in-depth, never a shared import — this
    module stays stdlib-only and headless-importable). The future TUI
    run-config screen (Phase 11) drives sweeps exclusively through these
    flags — they exist CLI-first with argv-shape proofs in
    ``tests/test_sweep.py``.
    ``--batch_size`` (261023-abu) joins the family as a plain valued
    int flag (the ``--num_train_epochs`` shape — NO bare-flag const,
    that is ``--effective_batch_size``'s D-12 niche): it threads the
    STARTING per-device micro-batch to every child, where the EXISTING
    ``determine_batch_size`` (run_finetune.py:602) scales it down by
    sequence-length tier — the per-device batch lever, distinct from
    ``--effective_batch_size``'s gradient-accumulation arithmetic (the
    two knobs coexist, documented never conflated), and
    ``batch_size >= 1`` joins the collect-all startup validation.

The advanced train-flag family (Phase 19, 19-01; PD-19-1..PD-19-7):
    ``ADVANCED_TRAIN_FLAGS`` is the frozen param vocabulary (flag, kind,
    lo, hi, choices, default_display) driving an argparse registration
    loop, the collect-all bounds/json guards
    (``advanced_flag_problems``), the present-only nested collection
    (``collect_advanced``), and the ``build_argv`` block: ONE contiguous
    ALPHABETICAL advanced block appended IMMEDIATELY AFTER ``--batch_size``
    and BEFORE ``--cache_dir`` in the pinned tail order (PD-19-2),
    present flags only — an absent family contributes ZERO argv
    elements and ZERO manifest keys (the D-12/D-13 whole-family absent
    parity). The family rides ONE nested ``"advanced"`` dict key in
    ``sweep_flags`` manifests (PD-19-7), written only when non-empty;
    dispatch_core mirrors the same table via its ``run_sweep`` import
    (lanes, worker context, dry-run, the DERIVED rerun-token family) and
    the Phase-19 TUI service consumes it the same way (PD-19-6 — the
    table is the one shared vocabulary). The child (run_finetune.py)
    keeps a LOCAL registration tuple and applies every present value as
    a ``configs["finetune"].<field> = value`` assignment after its
    variant reload and before its grad_accum snapshot (PD-19-4).

--model_root / --dataset_root (261014-c2l, storage-root overrides):
    Two pure pass-through flags threaded to every run_finetune.py child
    as separate LIST argv elements ONLY when present — the ROOT under
    which the child joins registry Model_path / Dataset_path values
    VERBATIM (the ``models/...``/``datasets/...`` prefixes are part of
    the registry value; no prefix stripping). Models and datasets can
    therefore live outside the tiny system disk (e.g. under
    /root/autodl-tmp) while the registry-relative resolution stays
    byte-identical when no override is given: absent flags contribute
    ZERO argv elements and ZERO manifest keys, and the child keeps
    resolving against its own script directory. Present values resolve
    ABSOLUTE at this layer before threading (D-15), refuse
    provided-but-empty at sweep start (the WR-05 discipline), and record
    in every manifest cell via sweep_flags (D-13 — the storage location
    of a benchmark cell's inputs is provenance worth keeping).

--log_dir + the directories.json startup read (261014-f4w, F4W-01/F4W-02):
    ``--log_dir`` joins the underscore pass-through family verbatim —
    the directory under which the child writes
    ``{model_name}_error_log.txt`` (absent = the child's own ``./logs``
    default governs, byte-identical). At startup ``main()`` reads the
    user-owned ``directories.json`` (``pipeline/directories_config``,
    the ONE shared loader) and merges its five keys — model_root /
    dataset_root / output_root / log_dir / cache_dir — with the flags:
    precedence explicit CLI flag > file key > built-in default at every
    consumer, ONE merge point. A bare ``run_sweep.py`` with a populated
    file threads the file's values exactly as if passed as flags
    (resolved-absolute argv elements + manifest recording); with NO file
    and NO flags every path resolves byte-identically to today. A
    malformed present file aborts naming the path (fail-loud); the
    ``--output-root`` argparse default is now None with ``./finetuned``
    as the documented fallback so the file's ``output_root`` key can
    fill it (the effective value feeds the SAME
    ``Path(...).resolve()`` line).

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
from typing import NamedTuple

import directories_config  # sibling module (the F4W-01 startup config, same stdlib-only purity)
import registry_loader  # sibling module (pipeline/ on sys.path, the same import mechanics tests use for run_sweep itself)

PIPELINE_DIR = Path(__file__).resolve().parent
RUN_FINETUNE = PIPELINE_DIR / "run_finetune.py"

MANIFEST_NAME = "sweep_manifest.json"
FAILURES_NAME = "sweep_failures.json"
RECORD_NAME = "run_record.json"
RESUME_MARKER = "trainer_state.json"
METRICS_NAME = "final_metrics.json"

# Head-variant keep-base exception, VERBATIM from the child's save-name
# chain (run_finetune.py:1207-1209: ``elif config_variant == "head" and
# model_name not in ("evo2_1b_base", "megaDNA_updated"):`` — the alias
# branch these two names are exempted from): the special_models pair's
# with-head config IS their base config (the unchanged auto-reload
# branch), so a --config-variant head run is semantically the plain run
# and keeps the BASE name — no +head alias is added for exactly these
# names (11-01, D-18). Pinned against source drift by the read-source
# parity test in tests/test_sweep.py (run_finetune.py imports torch at
# its module top and is never imported CPU-side).
HEAD_KEEP_BASE_NAMES = ("evo2_1b_base", "megaDNA_updated")


class AdvancedTrainFlag(NamedTuple):
    """One row of ``ADVANCED_TRAIN_FLAGS`` — the shared advanced-param
    vocabulary (Phase 19, PD-19-6).

    Fields:
        flag: the DASHED argv flag (``"--learning_rate"``) — the argparse
            target AND the threaded argv element; the TrainingConfig
            field name / lane-dict key is ``flag.lstrip("-")``
            (``learning_rate`` — every locked flag is underscores-only,
            so the dash-strip is the field name verbatim).
        kind: one of ``"int"`` / ``"float"`` / ``"enum"`` / ``"bool"`` /
            ``"json"`` — selects the argparse type/choices mapping.
        lo: inclusive lower bound (``None`` = unbounded).
        hi: inclusive upper bound (``None`` = unbounded).
        choices: the closed vocabulary for enum/bool kinds (``None``
            otherwise; bool carries ``("true", "false")`` as STRING
            choices at this layer — the child's own parser owns the
            str-to-bool conversion).
        default_display: the base ``finetune_config.yaml`` literal, for
            help text / the Phase-19 TUI placeholder (variant YAMLs
            differ — Pitfall 3; this is display copy, never a default
            value: an absent flag always means None).
    """

    flag: str
    kind: str
    lo: float | None
    hi: float | None
    choices: tuple[str, ...] | None
    default_display: str


#: The frozen advanced train-flag table (Phase 19, 19-01, PD-19-1/PD-19-6)
#: — THE param vocabulary for the whole chain: this module's argparse
#: family + collect-all guards + build_argv block, dispatch_core's lane
#: mirrors (lane_values, worker context, dry-run sweep_flags, the derived
#: rerun-token family — imported via the existing ``import run_sweep``),
#: and tui/services/run_config.py in plan 19-02 (same import). Rows are
#: ALPHABETICAL by flag = table order = argv block order (PD-19-2).
#: Bound rules: floats are inclusive sanity mirrors (learning_rate
#: [1e-9, 1.0] documents "values below 1e-9 are typos"); ints are >= 1
#: (the --batch_size guard shape); enums are the live-probed transformers
#: 5.17.0 vocabularies (12 SchedulerType, 3 IntervalStrategy — 19-RESEARCH
#: lines 154-155), never training-data memory. The child (run_finetune)
#: keeps its own LOCAL registration tuple (it must stay standalone); a
#: contracts parity test pins that family against this table.
ADVANCED_TRAIN_FLAGS = (
    AdvancedTrainFlag(
        "--learning_rate", "float", 1e-9, 1.0, None, "2e-5"),
)


def advanced_flag_problems(args):
    """Collect-all guard messages for the advanced family (Phase 19).

    Numeric rows check their inclusive bounds with the
    ``"--batch_size must be >= 1, got {v}"`` message shape (each message
    names the flag AND the bound); the json row guards the dict shape
    (``json.loads`` accepts arrays/scalars, TrainingArguments requires
    an object); enum/bool rows need NO collect-all guard — argparse
    ``choices`` refuses garbage at exit 2 before this ever runs. The
    SAME helper serves ``main()`` here and dispatch_core's mirror (no
    run_sweep.main runs in dispatch mode — one table, one guard loop,
    zero drift, PD-19-6).

    Args:
        args (argparse.Namespace): a parsed namespace carrying one
            attribute per table flag (run_sweep's own or the
            ``parse_sweep_remainder`` re-parse product).

    Returns:
        list[str]: the problem messages (empty when every present value
        is in bounds).
    """
    problems = []
    for spec in ADVANCED_TRAIN_FLAGS:
        value = getattr(args, spec.flag.lstrip("-"), None)
        if value is None:
            continue
        if spec.kind == "int":
            if spec.lo is not None and value < spec.lo:
                problems.append(
                    f"{spec.flag} must be >= {int(spec.lo)}, got {value}")
        elif spec.kind == "float":
            below = spec.lo is not None and value < spec.lo
            above = spec.hi is not None and value > spec.hi
            if below or above:
                bound = (
                    f">= {spec.lo}" if spec.hi is None
                    else f"in [{spec.lo}, {spec.hi}]")
                problems.append(
                    f"{spec.flag} must be {bound}, got {value}")
        elif spec.kind == "json" and not isinstance(value, dict):
            problems.append(
                f"{spec.flag} must be a JSON object, got "
                f"{type(value).__name__}")
    return problems


def collect_advanced(args):
    """Collect the PRESENT advanced-family values (Phase 19, PD-19-7).

    The whole family rides ONE nested dict — key = the TrainingConfig
    field name, value as parsed — built present-only (absent flag
    contributes no key, D-12). Consumers: ``main()``'s
    ``sweep_flags["advanced"]`` manifest write and run_matrix/``build_argv``
    threading here, and dispatch_core's ordinary lane collection + dry-run
    mirror (the same single-owner discipline as the guard helper).

    Args:
        args (argparse.Namespace): a parsed namespace carrying one
            attribute per table flag.

    Returns:
        dict[str, object]: the present-only advanced dict (EMPTY when no
        flag was given — the whole-family-absent parity shape).
    """
    advanced = {}
    for spec in ADVANCED_TRAIN_FLAGS:
        value = getattr(args, spec.flag.lstrip("-"), None)
        if value is not None:
            advanced[spec.flag.lstrip("-")] = value
    return advanced


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
        default=None,
        help="Sweep output root (default: ./finetuned, resolved absolute; "
             "cells land under {root}/{model}/{task}/seed_{seed}/). An "
             "absent flag falls back to directories.json's output_root "
             "key, then ./finetuned (261014-f4w)"
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

    parser.add_argument(
        "--curve",
        type=str,
        default=None,
        help="Comma-separated train fractions in (0, 1], e.g. "
             "'0.25,0.5,1.0' (SC-6 learning curves, 06-05): each (model, "
             "task, seed) cell expands to one cell per fraction, output "
             "nested UNDER the seed dir "
             "({root}/{model}/{task}/seed_{seed}/frac_{f}/ — never a "
             "sibling); each cell's argv appends --train_fraction <f> "
             "(run_finetune applies it to the TRAIN split only, "
             "seed-governed shuffle-then-select; dev/test untouched)"
    )

    parser.add_argument(
        "--subset_file",
        type=str,
        default=None,
        help="JSON file mapping dataset names to lists of test-split row "
             "IDs, threaded VERBATIM to every run_finetune.py subprocess "
             "as --subset_file <resolved absolute path> (07-03, PIPE-02 "
             "pass-through; the child's validate_subset_file remains the "
             "authoritative per-cell check)"
    )

    parser.add_argument(
        "--effective_batch_size",
        nargs="?",
        const=16,
        type=int,
        default=None,
        help="Target effective batch size threaded to every child as "
             "--effective_batch_size <N>. A BARE flag means 16; an ABSENT "
             "flag threads nothing (the child's YAML gradient-accumulation "
             "governs — byte-identical to today). GA = max(1, N // bs_new) "
             "is applied CHILD-side (run_finetune.py); this driver is pure "
             "pass-through and never computes gradient accumulation (D-10)"
    )

    parser.add_argument(
        "--batch_size",
        type=int,
        default=None,
        help="Starting per-device batch size threaded to every child as "
             "--batch_size <N> — the child's determine_batch_size then "
             "scales it DOWN by sequence-length tier (run_finetune.py:602; "
             "the threaded value is the STARTING micro-batch, not a "
             "guarantee). The per-device batch lever, distinct from "
             "--effective_batch_size's gradient-accumulation arithmetic "
             "which stays child-side (261023-abu; plain valued flag, the "
             "--num_train_epochs shape — no bare-flag const semantics)"
    )

    parser.add_argument(
        "--num_train_epochs",
        type=int,
        default=None,
        help="Epoch override threaded to every child as "
             "--num_train_epochs <N> (the flag overrides the loaded "
             "config's finetune num_train_epochs child-side; absent = the "
             "YAML value governs — pure pass-through, D-16)"
    )

    parser.add_argument(
        "--cache_dir",
        type=str,
        default=None,
        help="Cache directory threaded to every child as --cache_dir "
             "<resolved absolute path> (sets HF_HOME/MS_CACHE_HOME in the "
             "child via its argv pre-scan; absent = the directories.json "
             "cache_dir key, then the child's env/default resolution "
             "governs)"
    )

    parser.add_argument(
        "--model_root",
        type=str,
        default=None,
        help="Model storage root threaded to every child as --model_root "
             "<resolved absolute path> — the root under which the child "
             "resolves registry Model_path values verbatim (absent = the "
             "directories.json model_root key, then the child's "
             "script-dir resolution governs)"
    )

    parser.add_argument(
        "--dataset_root",
        type=str,
        default=None,
        help="Dataset storage root threaded to every child as "
             "--dataset_root <resolved absolute path> — the root under "
             "which the child resolves registry Dataset_path values "
             "verbatim (absent = the directories.json dataset_root key, "
             "then the child's script-dir resolution governs)"
    )

    parser.add_argument(
        "--log_dir",
        type=str,
        default=None,
        help="Error-log directory threaded to every child as --log_dir "
             "<resolved absolute path> — the directory under which the "
             "child writes {model_name}_error_log.txt (261014-f4w; "
             "absent = the directories.json log_dir key, then the "
             "child's own ./logs default governs, byte-identical)"
    )

    parser.add_argument(
        "--config-variant",
        type=str,
        default=None,
        choices=["head", "probe", "curve"],
        help="Config-variant lane threaded to every run_finetune.py "
             "subprocess via the --peft ALIASING machinery (11-01, D-18 "
             "— never a pass-through): 'probe'/'curve'/'head' enumerate "
             "cells under the alias model names {model}+probe / "
             "{model}+curve / {model}+head (separate output dirs AND "
             "resume markers; registry filtering stays on base names, "
             "argv targets --target_model <base> --save_model_name "
             "<alias> --config-variant <v>); 'head' keeps the BASE name "
             "for the frozen pair (evo2_1b_base, megaDNA_updated — their "
             "with-head config IS their base config); refuses --peft "
             "(two alias suffixes cannot name one cell); absent "
             "(default) is byte-identical to today"
    )

    # Phase 19 (19-01, PD-19-6): the advanced train-flag family,
    # table-driven over ADVANCED_TRAIN_FLAGS — one registration loop, the
    # kind -> type/choices mapping (int/float valued, enum/bool closed
    # vocabularies, json a json.loads type callable). Plain valued flags
    # (the --num_train_epochs shape — NO bare-flag const semantics); an
    # absent flag parses to None and threads nothing (D-12). Every value
    # is validated at the child (run_finetune applies it as a
    # configs["finetune"].<field> assignment); the collect-all bounds
    # mirror lives in main()'s flag_problems via advanced_flag_problems.
    for spec in ADVANCED_TRAIN_FLAGS:
        if spec.kind == "int":
            parser.add_argument(
                spec.flag, type=int, default=None,
                help=f"Advanced train param {spec.flag.lstrip('-')} "
                     f"(int, default {spec.default_display} in the base "
                     "YAML) threaded to every child as a plain valued "
                     "flag (the --num_train_epochs shape); the child "
                     "applies it as a configs['finetune'] field "
                     "assignment — absent = the YAML value governs")
        elif spec.kind == "float":
            parser.add_argument(
                spec.flag, type=float, default=None,
                help=f"Advanced train param {spec.flag.lstrip('-')} "
                     f"(float, default {spec.default_display} in the base "
                     "YAML) threaded to every child as a plain valued "
                     "flag (the --num_train_epochs shape); the child "
                     "applies it as a configs['finetune'] field "
                     "assignment — absent = the YAML value governs")
        elif spec.kind in ("enum", "bool"):
            parser.add_argument(
                spec.flag, choices=list(spec.choices or ()), default=None,
                help=f"Advanced train param {spec.flag.lstrip('-')} "
                     f"(one of {', '.join(spec.choices or ())}; default "
                     f"{spec.default_display} in the base YAML) threaded "
                     "to every child as a plain valued flag (the "
                     "--num_train_epochs shape); the child applies it as "
                     "a configs['finetune'] field assignment — absent = "
                     "the YAML value governs")
        else:  # json
            parser.add_argument(
                spec.flag, type=json.loads, default=None,
                help=f"Advanced train param {spec.flag.lstrip('-')} "
                     "(JSON object literal, e.g. "
                     "'{\"num_restarts\": 2}') threaded to every child "
                     "as a plain valued flag (the --num_train_epochs "
                     "shape); the child applies it as a "
                     "configs['finetune'] field assignment — absent = "
                     "the YAML value governs")

    return parser.parse_args()


def enumerate_matrix(models_filter, tasks_filter, seeds, registry_dir,
                     peft="none", fractions=None, config_variant="none"):
    """Build the sorted (model, task, seed[, fraction]) cell list.

    Under ``peft`` lora/ia3 (06-02) the emitted cells carry the ALIAS
    model name ``{model}+{mode}`` — the output-dir / resume-marker
    identity — while the registry iteration and the ``--models`` filter
    join stay on BASE names (argv targeting re-derives the base via
    suffix strip in ``build_argv``). Sorting happens AFTER the alias
    mapping, so the enumeration stays deterministic.

    Under ``config_variant`` head/probe/curve (11-01, D-18) the same
    aliasing discipline applies: cells carry ``{model}+{variant}``
    (``head`` keeps the BASE name for exactly the frozen pair
    ``HEAD_KEEP_BASE_NAMES`` — verbatim from the child's save-name
    chain, where their with-head config IS their base config). The
    variant axis is DISJOINT from peft — ``main()`` refuses any
    both-set combination — so the closure applies the variant rule only
    on the peft=none path.

    Under ``fractions`` (06-05 curve lane) each (model, task, seed) cell
    expands to one (model, task, seed, fraction) 4-tuple per fraction —
    the layout contract lives in ``cell_dir_for`` (frac nested UNDER the
    seed dir). ``fractions=None`` (the default) enumerates the exact
    3-tuple cells of today (byte-identical default).

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
        fractions (list[float] | None): curve fractions; each cell expands
            per fraction.
        config_variant (str): config variant (none/head/probe/curve);
            none emits base-name cells byte-identical to the pre-11-01
            enumeration.

    Returns:
        list[tuple]: sorted cells — (model, task, seed) triples, or
        (model, task, seed, fraction) quadruples under --curve.
    """
    models_info = registry_loader.load_models_registry(registry_dir)
    datasets_info = registry_loader.load_datasets_registry(registry_dir)

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
        if peft != "none":
            return f"{model}+{peft}"
        if config_variant in ("probe", "curve"):
            return f"{model}+{config_variant}"
        if config_variant == "head" and model not in HEAD_KEEP_BASE_NAMES:
            return f"{model}+head"
        return model

    if fractions:
        return sorted(
            (cell_model(model), task, seed, fraction)
            for model in models
            for task in tasks
            for seed in seeds
            for fraction in fractions
        )
    return sorted(
        (cell_model(model), task, seed)
        for model in models
        for task in tasks
        for seed in seeds
    )


def parse_curve_fractions(raw):
    """Parse + validate a ``--curve`` comma list (fail-fast, collect-all).

    Every problem is collected before the caller exits non-zero (the
    ``_validate_filters`` discipline, T-05-09): parse errors and
    out-of-bounds values are listed TOGETHER — the list steers multi-day
    GPU execution, so a typo must fail fast with every problem named.
    Valid fractions live in ``(0, 1]`` (``f <= 0`` is meaningless,
    ``f > 1`` is not a fraction); duplicate values collapse (two
    identical fractions map to one identical output dir); the returned
    list is sorted ascending so the enumeration and the manifest are
    deterministic.

    Args:
        raw (str): the ``--curve`` value.

    Returns:
        list[float]: sorted unique fractions.

    Raises:
        SystemExit: listing every problem, or when nothing parses.
    """
    problems = []
    fractions = []
    for part in raw.split(","):
        token = part.strip()
        if not token:
            problems.append(f"empty fraction element in {raw!r}")
            continue
        try:
            value = float(token)
        except ValueError:
            problems.append(f"non-numeric fraction {token!r}")
            continue
        if not 0 < value <= 1:
            problems.append(f"fraction {token!r} outside (0, 1]")
        else:
            fractions.append(value)
    if problems:
        sys.exit(f"[Error] --curve {'; '.join(problems)}")
    unique = sorted(set(fractions))
    if not unique:
        sys.exit(
            f"[Error] --curve {raw!r} produced no fractions after parsing"
        )
    return unique


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
    models_info = registry_loader.load_models_registry(registry_dir)
    datasets_info = registry_loader.load_datasets_registry(registry_dir)
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


def _validate_dataset_name_alignment(datasets_info):
    """Refuse registry rows whose ``Dataset_name`` diverges from their
    registry key (WR-06, phase-07 review).

    The sweep keys cell dirs and resume markers on registry KEYS
    (``cell_dir_for``), while the child writes its outputs under the
    row's ``Dataset_name`` (``run_finetune.py``'s outdir). Every row
    coincides today, but a divergent row — e.g. a user-authored custom
    overlay entry, the new divergence source this phase added — would
    train successfully into the ``Dataset_name`` dir while the sweep
    records the cell FAILED ("executor exited 0 but final_metrics.json is
    missing") and re-attempts it forever. ``validate_subset_file``
    already refuses divergence, but only for tasks present in a
    ``--subset_file``; this extends the loud refusal to the WHOLE merged
    registry at sweep start, the same collect-all discipline.

    Args:
        datasets_info (dict): the overlay-merged datasets registry — the
            same ``registry_loader`` view the matrix enumeration joins
            on. A row omitting ``Dataset_name`` defaults to its key (the
            child validator's reading) and cannot diverge.

    Raises:
        SystemExit: naming every divergent row.
    """
    divergent = sorted(
        key for key, row in datasets_info.items()
        if row.get("Dataset_name", key) != key
    )
    if divergent:
        sys.exit(
            "[Error] datasets registry rows whose Dataset_name diverges "
            f"from their registry key: {divergent} — run_sweep cell dirs "
            "are keyed on registry keys while run_finetune writes "
            "outputs under Dataset_name, so every cell of such a task "
            "would train successfully but record as failed and retrain "
            "forever; align the row's Dataset_name with its key or "
            "remove the row"
        )


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
    models_info = registry_loader.load_models_registry(registry_dir)
    datasets_info = registry_loader.load_datasets_registry(registry_dir)
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


def _validate_subset_file(path, datasets_info):
    """Fail fast on a ``--subset_file`` map the registry cannot join on
    (07-03, D-14).

    A bad subset map must abort the sweep at STARTUP with every problem
    listed together — never after the first cell's model load burns on a
    map that cannot join (the ``_validate_filters`` /
    ``parse_curve_fractions`` collect-all discipline, T-05-09). Checks:
    the file is readable JSON; the top level is an object; every key is a
    datasets-registry key; every value is a list of ints.

    Shallow BY DESIGN (research Open Q2 disposition): structure and
    registry membership only — bounds-vs-Test-count and deeper semantics
    stay child-side, where ``run_finetune.validate_subset_file`` is the
    authoritative per-cell re-check. Deliberate defense-in-depth, NOT a
    shared import: this module is stdlib-only and headless-importable
    (importing run_finetune would pull torch into CI), and extracting
    the child function would break the exec-extract contract tests.

    Args:
        path (str): the RESOLVED absolute ``--subset_file`` path.
        datasets_info (dict): the overlay-merged datasets registry — the
            same ``registry_loader`` source the matrix enumeration joins
            on, so keys validate against the identical view.

    Raises:
        SystemExit: listing every problem in one non-zero exit.
    """
    problems = []
    # WR-01 (phase-07 review): a DISTINCT unreadable sentinel — the JSON
    # literal ``null`` parses to None, which collided with a plain
    # ``loaded = None`` sentinel and passed startup validation with zero
    # problems, degrading the sweep to N per-cell CalledProcessError
    # failures instead of one collect-all startup abort.
    _unreadable = object()
    loaded = _unreadable
    try:
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        problems.append(f"cannot read {path}: {exc}")
    if loaded is not _unreadable and not isinstance(loaded, dict):
        problems.append(
            f"top-level JSON is {type(loaded).__name__}, expected an "
            "object mapping task names to lists of integer row IDs"
        )
    if isinstance(loaded, dict):
        unknown = sorted(set(loaded) - set(datasets_info))
        if unknown:
            problems.append(f"task keys not in datasets registry: {unknown}")
        for task in sorted(loaded):
            if task not in datasets_info:
                continue
            ids = loaded[task]
            if not isinstance(ids, list):
                problems.append(
                    f"{task}: value is {type(ids).__name__}, expected a "
                    "list of integer row IDs"
                )
                continue
            for row_id in ids:
                if isinstance(row_id, bool) or not isinstance(row_id, int):
                    problems.append(f"{task}: non-integer ID {row_id!r}")
    if problems:
        sys.exit(f"[Error] --subset_file {'; '.join(problems)}")


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

    MED-01 (phase-06 review): a ``--peft`` sweep's manifest records the
    ALIAS under ``model`` and the BASE registry name under ``base_model``;
    validation and the returned pairs run on BASE names, and the alias
    re-derives from the re-run's own ``--peft`` mode (enumerate_matrix
    re-aliases the cells). Legacy manifests without ``base_model`` fall
    back to stripping a known adapter suffix from ``model`` (the same
    strip ``build_argv`` applies) before refusing.

    Args:
        path (str): --from-failures value (a sweep_failures.json file).
        registry_dir (Path | str): directory holding the unified JSON
            registries.

    Returns:
        set[tuple[str, str]]: the distinct failed (base model, task)
            pairs.

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
        base_model = entry.get("base_model")
        if base_model is not None and not isinstance(base_model, str):
            problems.append(
                f"--from-failures entry {idx} has a non-string "
                f"'base_model' key: {base_model!r}"
            )
            continue
        join_name = base_model or model
        if join_name not in known_models:
            stripped = (
                join_name.removesuffix("+lora").removesuffix("+ia3")
            )
            if stripped != join_name and stripped in known_models:
                join_name = stripped
            else:
                problems.append(
                    f"--from-failures model not in registry: "
                    f"{join_name!r} (entry {idx})"
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
        pairs.add((join_name, task))
    if problems:
        sys.exit(f"[Error] {'; '.join(problems)}")
    return pairs


def cell_dir_for(output_root, model, task, seed, fraction=None):
    """Return the seed-isolated cell dir {root}/{model}/{task}/seed_{seed},
    optionally frac-nested UNDER the seed dir (06-05 curve lane:
    {root}/{model}/{task}/seed_{seed}/frac_{f}/ — the fraction ALWAYS
    nests under the seed dir, never beside it, so the trainer_state.json
    resume marker and the exporter walk stay (model, task, seed,
    fraction)-scoped)."""
    cell = Path(output_root) / model / task / f"seed_{seed}"
    if fraction is not None:
        cell = cell / f"frac_{fraction}"
    return cell


def base_model_name(model, peft="none", config_variant="none"):
    """Resolve a cell/alias model name to its BASE registry name.

    Under ``peft`` lora/ia3 (06-02) the cell, record, and failure-entry
    model identity is the ALIAS ``{base}+{mode}``; the registry join, the
    child's ``--target_model``, and ``--from-failures`` validation all
    operate on BASE names, so every alias consumer re-derives the base
    through this one suffix strip (MED-01, phase-06 review: failure
    entries used to record only the alias, which ``--from-failures``
    then rejected as not-in-registry).

    Under ``config_variant`` head/probe/curve (11-01, D-18) the same
    strip removes the ``+{variant}`` suffix AFTER the peft strip — a
    no-op for ``head`` on the frozen pair (no suffix was added) and for
    any name that never carried it (``str.removesuffix`` never invents a
    suffix). The two axes never compose (refused at ``main()``), so at
    most one suffix is ever present.

    Args:
        model (str): the cell's model identity — BASE under peft=none and
            no variant, ALIAS under lora/ia3 or a config variant.
        peft (str): adapter mode none/lora/ia3.
        config_variant (str): config variant none/head/probe/curve.

    Returns:
        str: the base registry name (the alias suffix removed).
    """
    if peft != "none":
        model = model.removesuffix(f"+{peft}")
    if config_variant != "none":
        model = model.removesuffix(f"+{config_variant}")
    return model


def build_argv(model, task, seed, output_root, peft="none",
               train_fraction=None, subset_file=None,
               effective_batch_size=None, batch_size=None,
               num_train_epochs=None,
               cache_dir=None, config_variant="none",
               model_root=None, dataset_root=None, log_dir=None,
               advanced=None):
    """Build the run_finetune.py argv for one cell — a LIST, never a string.

    Under ``peft`` lora/ia3 (06-02) the cell's model is the ALIAS
    (``{base}+{mode}``): argv targets the BASE registry name via
    ``--target_model`` (suffix-stripped — the alias is not a registry key)
    and appends ``--save_model_name <alias>`` + ``--peft <mode>`` as
    separate LIST elements, so the child resolves the alias save name
    explicitly and writes its outputs under the alias dir (name isolation
    end-to-end). Under ``none`` the argv is byte-identical to the pre-peft
    form — no extra elements.

    Under ``config_variant`` head/probe/curve (11-01, D-18) the same
    twin: ``--save_model_name <alias>`` + ``--config-variant <v>`` as
    separate LIST elements, with ``--target_model`` still carrying the
    BASE name. The explicit ``--save_model_name`` makes the DRIVER the
    single naming authority over the child's own identical
    self-aliasing branch (run_finetune.py:1198-1213, the
    explicit-save-name-wins rule): the alias dir the child writes and
    the alias dir ``cell_dir_for`` records can never diverge — the exact
    agreement a pure pass-through would break (retrain-forever trap).
    Under ``none`` (and no peft) no extra elements (byte-identical
    default).

    Under ``train_fraction`` (06-05 curve lane) the argv appends
    ``--train_fraction <f>`` as separate LIST elements; run_finetune
    applies it to the TRAIN split only and nests its output under
    ``seed_{seed}/frac_{f}/``. Absent fraction: no extra elements.

    Under the four pass-through flags (07-03, PIPE-02) each PRESENT flag
    appends exactly two LIST elements (flag then ``str(value)``) —
    ``--subset_file``, ``--effective_batch_size``,
    ``--num_train_epochs``, ``--cache_dir`` — followed by the pinned
    storage tail (261014-c2l + 261014-f4w) ``--model_root`` then
    ``--dataset_root`` then ``--log_dir`` (model-before-dataset, the
    --target_model-before---target_dataset axis order; the log dir
    joins last as the newest family member). An ABSENT
    flag contributes ZERO elements, so a no-flag sweep builds the exact
    pre-07-03 argv (D-12/D-13 absent parity). No gradient-accumulation
    arithmetic lives here: GA = max(1, N // bs_new) is the child's
    existing logic (D-10/ D-16 — this builder is pure pass-through).
    ``--batch_size`` (261023-abu) appends IMMEDIATELY AFTER
    ``--effective_batch_size`` — the two batch knobs adjacent
    everywhere, documented never conflated: batch_size threads the
    STARTING per-device micro-batch (the child's
    ``determine_batch_size`` scales it down by sequence-length tier),
    effective_batch_size threads the GA-derived effective target. The
    advanced family (Phase 19, PD-19-2) appends as ONE contiguous
    ALPHABETICAL block (table order) IMMEDIATELY AFTER the
    ``--batch_size`` append and BEFORE the ``--cache_dir`` append at
    every threading site — present flags only (two LIST elements each,
    the json kind serialized with ``json.dumps(sort_keys=True)``), an
    empty/absent dict contributes ZERO elements (the D-12/D-13
    whole-family absent parity).

    Args:
        model (str): value for the cell's model identity — the BASE name
            under peft=none and no variant, the ALIAS under lora/ia3 or
            a config variant (value for --save_model_name then;
            --target_model gets the strip).
        task (str): value for --target_dataset.
        seed (int): value for --seed.
        output_root (str | Path): ABSOLUTE root for --output_dir (the
            subprocess resolves it against its own cwd, which is pinned
            to pipeline/ — see the module docstring's invocation contract).
        peft (str): adapter mode none/lora/ia3.
        train_fraction (float | None): curve-lane fraction appended as
            ``--train_fraction <f>`` when given.
        subset_file (str | None): resolved ABSOLUTE subset-map path
            appended as ``--subset_file <path>`` when given (D-15).
        effective_batch_size (int | None): target effective batch size
            appended as ``--effective_batch_size <N>`` when given; the
            child derives gradient accumulation from it.
        batch_size (int | None): STARTING per-device micro-batch
            appended as ``--batch_size <N>`` when given, immediately
            after ``--effective_batch_size``; the child's
            ``determine_batch_size`` scales it down by sequence-length
            tier (run_finetune.py:602) — distinct from the GA-derived
            effective target (261023-abu).
        advanced (dict | None): the PRESENT advanced-family values
            (Phase 19, PD-19-7 — collect_advanced's product; keys are
            TrainingConfig field names) appended as one contiguous
            alphabetical block immediately after ``--batch_size``; the
            json kind serializes with sorted-key JSON, every other kind
            with ``str(value)``. None/empty contributes zero elements.
        num_train_epochs (int | None): epoch override appended as
            ``--num_train_epochs <N>`` when given.
        cache_dir (str | None): resolved ABSOLUTE cache directory
            appended as ``--cache_dir <path>`` when given (D-15).
        config_variant (str): config variant none/head/probe/curve;
            non-none appends the ``--save_model_name``/
            ``--config-variant`` twin (11-01, D-18).
        model_root (str | None): resolved ABSOLUTE model storage root
            appended as ``--model_root <path>`` when given — the root
            under which the child joins registry Model_path values
            verbatim.
        dataset_root (str | None): resolved ABSOLUTE dataset storage
            root appended as ``--dataset_root <path>`` when given — the
            Dataset_path twin.
        log_dir (str | None): resolved ABSOLUTE error-log directory
            appended as ``--log_dir <path>`` when given (261014-f4w) —
            the directory under which the child writes
            ``{model_name}_error_log.txt``.

    Returns:
        list[str]: the argv, each flag and value a separate element.
    """
    argv = [
        sys.executable,
        str(RUN_FINETUNE),
        "--target_model",
        str(base_model_name(model, peft, config_variant)),
        "--target_dataset", str(task),
        "--seed", str(seed),
        "--output_dir", str(output_root),
    ]
    if peft != "none":
        argv += ["--save_model_name", str(model), "--peft", peft]
    elif config_variant != "none":
        argv += ["--save_model_name", str(model),
                 "--config-variant", config_variant]
    if train_fraction is not None:
        argv += ["--train_fraction", str(train_fraction)]
    if subset_file is not None:
        argv += ["--subset_file", str(subset_file)]
    if effective_batch_size is not None:
        argv += ["--effective_batch_size", str(effective_batch_size)]
    if batch_size is not None:
        argv += ["--batch_size", str(batch_size)]
    if advanced:
        # Phase 19 (PD-19-2): ONE contiguous alphabetical advanced block,
        # immediately AFTER the --batch_size append and BEFORE the
        # --cache_dir append — pinned element-for-element by tests at
        # every threading site (this builder, the TUI composers in
        # 19-02, the dispatch worker context).
        for spec in ADVANCED_TRAIN_FLAGS:
            value = advanced.get(spec.flag.lstrip("-"))
            if value is None:
                continue
            if spec.kind == "json":
                argv += [spec.flag, json.dumps(value, sort_keys=True)]
            else:
                argv += [spec.flag, str(value)]
    if num_train_epochs is not None:
        argv += ["--num_train_epochs", str(num_train_epochs)]
    if cache_dir is not None:
        argv += ["--cache_dir", str(cache_dir)]
    if model_root is not None:
        argv += ["--model_root", str(model_root)]
    if dataset_root is not None:
        argv += ["--dataset_root", str(dataset_root)]
    if log_dir is not None:
        argv += ["--log_dir", str(log_dir)]
    return argv


def launch_subprocess(model, task, seed, output_root, peft="none",
                      train_fraction=None, subset_file=None,
                      effective_batch_size=None, batch_size=None,
                      num_train_epochs=None,
                      cache_dir=None, config_variant="none",
                      model_root=None, dataset_root=None, log_dir=None,
                      advanced=None):
    """Default executor: run run_finetune.py for one cell.

    cwd is pinned to PIPELINE_DIR because finetune_config.yaml and the
    ./finetuned default are CWD-relative in run_finetune.py (research
    Pitfall 3); shell is never used (T-03-10). The four pass-through
    flags (07-03) forward verbatim, ``batch_size`` (261023-abu)
    forwards beside ``effective_batch_size`` (the two batch knobs
    adjacent), the advanced family (Phase 19) forwards as the nested
    dict's alphabetical argv block (``advanced=None``/empty = zero
    elements, the whole-family absent parity), ``config_variant``
    (11-01, D-18) threads as the peft-style aliasing twin, the two
    storage-root flags (261014-c2l) and the error-log dir (261014-f4w)
    forward as resolved ABSOLUTE paths — the child is the authoritative
    validator in all cases.

    Raises:
        subprocess.CalledProcessError: the run exited nonzero (check=True).
        OSError: the subprocess could not be spawned.
    """
    return subprocess.run(
        build_argv(model, task, seed, output_root, peft, train_fraction,
                   subset_file, effective_batch_size, batch_size,
                   num_train_epochs,
                   cache_dir, config_variant, model_root, dataset_root,
                   log_dir, advanced),
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


def extract_curve_points(trainer_state):
    """Extract the (step, eval-metrics) learning-curve points from a
    trainer_state.json structure (SC-6/REV-08 F8, 06-05).

    Pure and CPU-side: consumes only the trainer_state dict (the file
    run_finetune copies next to final_metrics.json as the resume
    marker's companion), never a live trainer. ``log_history`` carries
    mixed records — plain loss/logging rows and evaluation rows; only
    entries with at least one ``eval_`` key are curve points (the dense
    cadence comes from the finetune_config_curve.yaml variant, eval every
    100 steps). Points return SORTED by step — log_history is append
    ordered in practice, but sorting makes the contract structural. A
    non-dict entry or an eval entry without a usable ``step`` is skipped
    (a point that cannot be placed on the curve is not a point); an
    absent/empty log_history yields ``[]``.

    Args:
        trainer_state (dict | None): a parsed trainer_state.json — only
            the ``log_history`` key is read; None/absent tolerated.

    Returns:
        list[tuple[int, dict]]: ``(step, {eval_*: value})`` points sorted
        by step (stable for equal steps).
    """
    history = (trainer_state or {}).get("log_history") or []
    points = []
    for entry in history:
        if not isinstance(entry, dict):
            continue
        step = entry.get("step")
        eval_metrics = {
            key: value for key, value in entry.items()
            if key.startswith("eval_")
        }
        if not eval_metrics or step is None:
            continue
        points.append((step, eval_metrics))
    return sorted(points, key=lambda point: point[0])


def _new_record(model, task, seed, cell_dir, git_commit, peft="none",
                train_fraction=None, config_variant="none"):
    """Build the run_record skeleton (statuses/timestamps filled by caller).

    The ``peft`` field (06-02, string, default ``"none"``) marks the
    adapter mode the sweep was launched with — the frontier row derivation
    reads it (alias-suffix first, this field as the record-level source).
    The ``config_variant`` field (11-01, string, default ``"none"`` — the
    peft-field precedent) marks the config-variant lane the same way.
    The ``train_fraction`` field (06-05, float for curve cells, null
    otherwise) marks the curve lane's fraction — the learning-curve
    reader groups by it.
    """
    return {
        "model": model,
        "task": task,
        "seed": seed,
        "peft": peft,
        "config_variant": config_variant,
        "train_fraction": train_fraction,
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


def _manifest_payload(matrix, records, sweep_flags=None):
    """Build the sweep manifest from matrix definition + cell records.

    PRESENT pass-through flags (07-03, D-13) merge into every cell dict —
    flag name -> threaded value (paths already resolved absolute by
    ``main()``, D-15). ABSENT flags contribute no keys, so a no-flag
    payload is byte-identical to the pre-07-03 five-key projection;
    ``_write_json``'s ``sort_keys=True`` keeps the serialization
    deterministic with the extra fields. run_record.json is deliberately
    NOT extended (D-02 spirit, research Open Q3): the flags are
    sweep-level run configuration recorded once in the manifest, never
    per-cell provenance fields.

    Args:
        matrix (dict): the matrix definition (models/tasks/seeds/
            output_root).
        records (list[dict]): per-cell record views (only the five
            manifest keys are projected — extra record fields never
            leak into the manifest).
        sweep_flags (dict | None): the present pass-through flags.

    Returns:
        dict: the manifest payload.
    """
    flags = sweep_flags or {}
    return {
        "matrix": matrix,
        "cells": [
            {
                "model": record["model"],
                "task": record["task"],
                "seed": record["seed"],
                "status": record["status"],
                "output_dir": record["output_dir"],
                **flags,
            }
            for record in records
        ],
    }


def run_matrix(cells, output_root, executor=None, peft="none",
               sweep_flags=None, config_variant="none", advanced=None):
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
    continues). Each failure entry records BOTH the cell's model identity
    (the ALIAS under ``--peft`` or ``--config-variant``, matching the
    cell dir and record) and its ``base_model`` (the registry name —
    MED-01, phase-06 review:
    ``--from-failures`` validates and joins on base names, so a peft
    sweep's own manifest must be recoverable). sweep_failures.json is
    written on EVERY run — an empty list when no cell failed — so a
    stale failures manifest can never outlive its sweep (WR-06).

    Args:
        cells (list[tuple]): (model, task, seed) triples, or (model, task,
            seed, fraction) quadruples under --curve (06-05), in the
            intended execution order (never re-sorted here). Under
            ``--peft`` the model component is the ALIAS name — the cell
            dir, record, and manifest all key by it; under ``--curve``
            the fraction component drives the frac-under-seed nesting.
        output_root (str | Path): sweep output root (resolved absolute).
        executor (callable | None): ``executor(model, task, seed,
            output_root, train_fraction=None)``; defaults to
            launch_subprocess (bound with this call's ``peft`` so the real
            launch path composes the adapter argv). Injectable for the
            fake-executor tests (D-05: real mode is never launched this
            phase outside those tests).
        peft (str): adapter mode none/lora/ia3 (06-02) — carried into the
            run_record ``peft`` field and the default executor's argv.
        sweep_flags (dict | None): the PRESENT pass-through flags
            (07-03, PIPE-02) — keys ``subset_file`` /
            ``effective_batch_size`` / ``num_train_epochs`` /
            ``cache_dir`` (plus the storage-root twins ``model_root`` /
            ``dataset_root``, 261014-c2l), values as threaded (paths
            already resolved absolute by ``main()``, D-15). Bound into the default
            executor's argv AND merged into every manifest cell (D-13);
            an empty/None dict binds nothing and records nothing
            (byte-identical default). A ``config_variant`` key (11-01:
            ``main()`` records a present variant for the manifest merge)
            is recorded in the manifest but NEVER re-bound into the
            executor argv here — the explicit ``config_variant`` param is
            the single argv authority, so the splat filters it out.
        config_variant (str): config variant none/head/probe/curve
            (11-01, D-18) — carried into the run_record
            ``config_variant`` field, the default executor's argv, and
            the failure entries' ``base_model`` derivation.
        advanced (dict | None): the PRESENT advanced-family values
            (Phase 19, PD-19-7) — bound into the default executor's
            argv exactly as ``config_variant`` is bound (explicitly,
            while the launch_kwargs splat filters the manifest-recording
            ``sweep_flags["advanced"]`` key back out, so no duplicate
            kwarg can collide with this param).

    Returns:
        list[dict]: the run records, one per cell, in the given cell order.
    """
    launch_kwargs = {
        key: value for key, value in (sweep_flags or {}).items()
        if key not in ("config_variant", "advanced")
    }
    executor = (
        executor if executor is not None
        else functools.partial(
            launch_subprocess, peft=peft, config_variant=config_variant,
            advanced=advanced, **launch_kwargs)
    )
    output_root = Path(output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    git_commit = _git_commit()

    records = []
    failures = []
    for cell in cells:
        # Curve cells are (model, task, seed, fraction) quadruples; plain
        # cells are triples. Normalized here so every downstream consumer
        # (cell dir, record, executor) sees one shape.
        model, task, seed = cell[0], cell[1], cell[2]
        fraction = cell[3] if len(cell) > 3 else None
        cell_dir = cell_dir_for(output_root, model, task, seed, fraction)
        record = _new_record(
            model, task, seed, cell_dir, git_commit, peft,
            train_fraction=fraction, config_variant=config_variant)
        record["started_at"] = _utc_now_iso()
        if (cell_dir / RESUME_MARKER).exists():
            # Seed-scoped resume marker (G1): only THIS (model, task,
            # seed) cell is done — a sibling seed still runs.
            record["status"] = "skipped"
        else:
            cell_dir.mkdir(parents=True, exist_ok=True)
            try:
                executor(model, task, seed, str(output_root),
                         train_fraction=fraction)
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
                        "base_model": base_model_name(model, peft, config_variant),
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
                            "base_model": base_model_name(model, peft, config_variant),
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
                    "base_model": base_model_name(model, peft, config_variant),
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
        "models": sorted({cell[0] for cell in cells}),
        "tasks": sorted({cell[1] for cell in cells}),
        "seeds": sorted({cell[2] for cell in cells}),
        "output_root": str(output_root),
    }
    _write_json(output_root / MANIFEST_NAME,
                _manifest_payload(matrix, records, sweep_flags))
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
    # F4W-01 startup read (261014-f4w): the user-owned directories.json
    # seeds the five directory settings for BARE invocations — ONE merge
    # point, precedence explicit CLI flag > file key > built-in default
    # (ADD-ALONGSIDE: absent everywhere keeps every consumer's default
    # branch byte-identical, so Path("./finetuned").resolve() below is
    # the identical expression applied to the effective value). A
    # malformed file aborts here naming the path (the fail-loud policy —
    # a silently-ignored corrupt file would redirect a multi-day run to
    # the wrong roots).
    file_dirs = directories_config.load_directories()
    output_root_arg = (
        args.output_root if args.output_root is not None
        else (file_dirs.get("output_root") or "./finetuned")
    )
    cache_dir_arg = (
        args.cache_dir if args.cache_dir is not None
        else file_dirs.get("cache_dir")
    )
    model_root_arg = (
        args.model_root if args.model_root is not None
        else file_dirs.get("model_root")
    )
    dataset_root_arg = (
        args.dataset_root if args.dataset_root is not None
        else file_dirs.get("dataset_root")
    )
    log_dir_arg = (
        args.log_dir if args.log_dir is not None
        else file_dirs.get("log_dir")
    )
    output_root = Path(output_root_arg).resolve()
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
    # WR-06 (phase-07 review): the registry-key == Dataset_name
    # coincidence the cell-dir/output-dir layout silently relies on,
    # asserted over the SAME overlay-merged registry view the matrix
    # enumeration joins on (a user-authored custom overlay row is a new
    # divergence source) — a divergent row would train successfully under
    # Dataset_name while the sweep records the cell failed forever.
    _validate_dataset_name_alignment(
        registry_loader.load_datasets_registry(registry_dir)
    )
    # Curve-lane fraction list (06-05): validated the same collect-all
    # fail-fast way BEFORE enumeration — parse errors and bounds are all
    # listed together, duplicates collapse, order is sorted ascending.
    fractions = None
    if args.curve is not None:
        fractions = parse_curve_fractions(args.curve)
    # Pass-through flag sanity + resolution (07-03, PIPE-02): the four
    # child flags validate collect-all here (Pitfall 5 — the child's own
    # guards are partial, so nonsense batch math must die at sweep start,
    # never mid-matrix), and the two path flags resolve to ABSOLUTE form
    # BEFORE threading (D-15 — the child cwd is pinned to pipeline/, so a
    # relative value would resolve against the wrong root). The
    # sweep_flags dict carries ONLY present flags: an absent flag threads
    # nothing at all (D-12 byte-identical-when-absent).
    flag_problems = []
    if args.effective_batch_size is not None and args.effective_batch_size < 1:
        flag_problems.append(
            f"--effective_batch_size must be >= 1, got "
            f"{args.effective_batch_size}"
        )
    if args.batch_size is not None and args.batch_size < 1:
        # 261023-abu: the --effective_batch_size twin over the
        # per-device STARTING batch — a zero/negative micro-batch is
        # nonsense batch math the child would only hit mid-matrix.
        flag_problems.append(
            f"--batch_size must be >= 1, got {args.batch_size}"
        )
    if args.num_train_epochs is not None and args.num_train_epochs < 1:
        flag_problems.append(
            f"--num_train_epochs must be >= 1, got {args.num_train_epochs}"
        )
    if args.subset_file is not None and not args.subset_file.strip():
        flag_problems.append(
            f"--subset_file {args.subset_file!r} is empty — refusing to "
            "thread a pathless flag"
        )
    if args.cache_dir is not None and not args.cache_dir.strip():
        # WR-05 (phase-07 review): the --subset_file twin — Path("").resolve()
        # is the CWD, so an empty --cache_dir would thread the repo root to
        # every child and its argv pre-scan would set HF_HOME/MS_CACHE_HOME
        # to the repository root (caches landing in the repo with no error
        # and no warning; a whitespace value resolves to a ' '-suffixed
        # path).
        flag_problems.append(
            f"--cache_dir {args.cache_dir!r} is empty — refusing to "
            "thread a pathless flag"
        )
    if args.model_root is not None and not args.model_root.strip():
        # WR-05 twin (261014-c2l): an empty --model_root would thread the
        # CWD as the model storage root — every child resolving
        # "models/..." under the sweep's launch directory instead of its
        # own script dir, a silent wrong-root hazard.
        flag_problems.append(
            f"--model_root {args.model_root!r} is empty — refusing to "
            "thread a pathless flag"
        )
    if args.dataset_root is not None and not args.dataset_root.strip():
        # WR-05 twin (261014-c2l): the --model_root twin over the dataset
        # resolution root.
        flag_problems.append(
            f"--dataset_root {args.dataset_root!r} is empty — refusing "
            "to thread a pathless flag"
        )
    if args.log_dir is not None and not args.log_dir.strip():
        # WR-05 twin (261014-f4w): the --model_root twin over the
        # error-log directory — an empty --log_dir would thread the CWD,
        # scattering {model_name}_error_log.txt files across the launch
        # directory. (File values are stripped-nonempty by the loader,
        # so this and its siblings remain FLAG-form guards.)
        flag_problems.append(
            f"--log_dir {args.log_dir!r} is empty — refusing to thread "
            "a pathless flag"
        )
    # Phase 19 (19-01): the advanced family's collect-all bounds/json
    # guards — the SAME table-driven loop dispatch_core's mirror calls
    # (one definition, zero drift, PD-19-6); enum/bool rows are refused
    # by argparse choices at parse time and need no guard here.
    flag_problems.extend(advanced_flag_problems(args))
    # T-11-01-03: variant and PEFT never compose. Two alias suffixes
    # cannot both name one cell (the child would take --save_model_name
    # from one lane while the driver recorded the other's dir); the
    # child already refuses probe x peft at its argv boundary
    # (run_finetune.py:775-789) — this driver-side refusal extends the
    # guard to head/curve and fails the WHOLE sweep before any cell
    # enumerates, never per-cell after a model load burns.
    if args.config_variant is not None and args.peft != "none":
        flag_problems.append(
            f"--config-variant {args.config_variant} refuses --peft "
            f"{args.peft}: variant lanes and adapter lanes never compose "
            "(alias names are disjoint; the child additionally refuses "
            "probe×peft at its argv boundary)"
        )
    if flag_problems:
        sys.exit(f"[Error] {'; '.join(flag_problems)}")
    subset_file_abs = (
        str(Path(args.subset_file).resolve())
        if args.subset_file is not None else None
    )
    cache_dir_abs = (
        str(Path(cache_dir_arg).resolve())
        if cache_dir_arg is not None else None
    )
    model_root_abs = (
        str(Path(model_root_arg).resolve())
        if model_root_arg is not None else None
    )
    dataset_root_abs = (
        str(Path(dataset_root_arg).resolve())
        if dataset_root_arg is not None else None
    )
    log_dir_abs = (
        str(Path(log_dir_arg).resolve())
        if log_dir_arg is not None else None
    )
    sweep_flags = {}
    if subset_file_abs is not None:
        sweep_flags["subset_file"] = subset_file_abs
    if args.effective_batch_size is not None:
        sweep_flags["effective_batch_size"] = args.effective_batch_size
    if args.batch_size is not None:
        # 261023-abu: a present starting per-device batch rides every
        # manifest cell (the **flags merge, D-13) AND the run_matrix
        # launch_kwargs partial — the micro-batch is experiment
        # semantics a rerun must replay.
        sweep_flags["batch_size"] = args.batch_size
    if args.num_train_epochs is not None:
        sweep_flags["num_train_epochs"] = args.num_train_epochs
    if cache_dir_abs is not None:
        sweep_flags["cache_dir"] = cache_dir_abs
    # Storage-root overrides (261014-c2l) and the log-dir override
    # (261014-f4w) join sweep_flags exactly like the pass-through family:
    # present keys both thread into every child argv (run_matrix's
    # launch_kwargs partial) and record in every manifest cell (the
    # **flags merge in _manifest_payload, D-13) — a storage-root override
    # silently changes WHICH model weights / dataset files a benchmark
    # cell consumed, and a log-dir override changes where its per-model
    # error logs land, so the manifest is the provenance record (T-c2l-02
    # extended). Absent-everywhere (no flag AND no file key) contributes
    # zero argv elements and zero manifest keys.
    if model_root_abs is not None:
        sweep_flags["model_root"] = model_root_abs
    if dataset_root_abs is not None:
        sweep_flags["dataset_root"] = dataset_root_abs
    if log_dir_abs is not None:
        sweep_flags["log_dir"] = log_dir_abs
    # Phase 19 (PD-19-7): the advanced family rides ONE nested dict key —
    # written ONLY when non-empty, so a no-flag sweep records ZERO
    # advanced keys anywhere in the manifest (the D-12/D-13 whole-family
    # absent parity; claim lanes mirror the same rule in dispatch_core).
    advanced = collect_advanced(args)
    if advanced:
        sweep_flags["advanced"] = advanced
    # 11-01 (D-18): normalize the variant axis once — args stores None
    # (absent) while every downstream consumer (enumerate_matrix,
    # build_argv, run_matrix, the from-failures join) speaks "none". A
    # PRESENT variant also joins sweep_flags, so the manifest merge is
    # free via **flags in _manifest_payload (D-13); run_matrix's
    # executor binding filters the key back out (its config_variant
    # param is the single argv authority).
    config_variant = args.config_variant or "none"
    if args.config_variant is not None:
        sweep_flags["config_variant"] = args.config_variant
    # D-14: pre-validate the subset map ONCE at sweep start against the
    # same overlay-merged registry view the matrix enumeration joins on
    # (registry_loader, post 07-02) — collect-all, before any cell's
    # model load can burn. The child's validate_subset_file re-checks per
    # cell (authoritative; defense-in-depth, not a shared import).
    if subset_file_abs is not None:
        _validate_subset_file(
            subset_file_abs,
            registry_loader.load_datasets_registry(registry_dir),
        )
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
        models_filter, tasks_filter, seeds, registry_dir, peft=args.peft,
        fractions=fractions, config_variant=config_variant)
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
            cell for cell in cells
            if (base_model_name(cell[0], args.peft, config_variant), cell[1])
            in failure_pairs
        ]

    if args.dry_run:
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
                "output_dir": str(
                    cell_dir_for(
                        output_root, cell[0], cell[1], cell[2],
                        cell[3] if len(cell) > 3 else None,
                    )
                ),
            }
            for cell in cells
        ]
        output_root.mkdir(parents=True, exist_ok=True)
        # The dry-run and real-run manifest paths record IDENTICALLY
        # (07-03, D-13): both project through _manifest_payload, so the
        # present sweep_flags join planned cells exactly as they join
        # executed cells — absent flags add no keys on either path.
        _write_json(
            output_root / MANIFEST_NAME,
            _manifest_payload(matrix, planned_records, sweep_flags),
        )
        print(
            f"[Dry-run] {len(cells)} planned cell(s) over "
            f"{len(matrix['models'])} model(s) x {len(matrix['tasks'])} "
            f"task(s) x {len(matrix['seeds'])} seed(s); manifest: "
            f"{output_root / MANIFEST_NAME}"
        )
        return

    records = run_matrix(cells, output_root, executor=None, peft=args.peft,
                         sweep_flags=sweep_flags,
                         config_variant=config_variant, advanced=advanced)
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
