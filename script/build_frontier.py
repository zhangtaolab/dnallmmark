"""Cost-accuracy frontier table generator (SC-6/REV-05, 06-02).

Purpose
-------
Derive the cost-accuracy frontier rows from the F2 run-record tree and
emit the dual ``frontier.json`` + ``frontier.csv`` artifacts (the n_audit
convention) plus an optional generated-markdown appendix (``--data-md``).
One row per COMPLETED run record:

- ``model``      the cell's model name as-is (the ALIAS display name for
                 adapter cells, e.g. ``plant-dnabert-6mer+lora``);
- ``base_model`` the alias-suffix-stripped join key (``+lora``/``+ia3``/
                 ``+probe`` — probe is deliberate forward-compatibility
                 for the 06-05 frozen-probe lane);
- ``task``/``seed`` the cell coordinates;
- ``method``     the alias suffix first (+lora/+ia3/+probe), else the
                 run_record ``peft`` field, else ``none``;
- ``wall_hours`` ``finished_at`` minus ``started_at`` — WALL-CLOCK
                 hours, not GPU-hours (precise GPU accounting stays
                 null-when-unknown per the vram_probe contract; the basis
                 is disclosed in ``schemas/frontier.json``);
- ``total_flos`` from record metrics — hard-required: a completed record
                 missing it aborts loudly naming the record path
                 (mirroring ``export_runs._collect_cell_values``; emitting
                 0 or the empty string would falsify the number);
- ``trainable_params_pct`` from record metrics — the 06-02 run_finetune
                 persistence (computed after the DNATrainer ctor for
                 EVERY mode; a full run reports 100.0). Null with a
                 disclosed note when the record predates that
                 persistence;
- ``score``      the task's primary metric resolved through the
                 exporter's metric surface (registry ``metric`` ->
                 ``resolve_dataset_metric`` -> slot; record key ->
                 ``resolve_metric_key`` -> slot match);
- ``score_delta`` the row's score minus the none-method MEAN score for
                 the same ``(base_model, task)``; null with a disclosed
                 note when no counterpart run exists. ``method=none``
                 rows are the reference — delta is defined for adapter
                 rows only;
- ``notes``      every per-row disclosure (skip-as-data, never a silent
                 drop).

Direction of truth
------------------
The F2 run-record tree read through ``export_runs.load_run_records`` —
the SINGLE reader authority; this script never re-walks the tree — and
``pipeline/datasets_info.json`` metric declarations resolved through
``export_runs.resolve_dataset_metric`` / ``resolve_metric_key`` — the
SINGLE metric authority (IN-03; never a re-derived mapping). An
unregistered task aborts (KeyError — the exporter's hard-fail join
discipline). Emission is deterministic: sorted iteration,
``sort_keys=True``, a fixed CSV column order, and no live clock — the
same tree produces byte-identical artifacts.

Publication gate (resolved research OQ 1): the committed
``dnallm-mark/data/frontier.json`` artifact and any DATA.md site link
stay gated on real post-E2' numbers. Until then the default output dir
is a SIBLING of the input root (``{input-root}/frontier`` — the D-16
discipline: committed data moves only in inventoried migration commits)
and the CI-side shape pin is the generator-produced fixture at
``tests/fixtures/frontier/frontier_sample.json``. Nothing registers in
tests/test_schemas.py SCHEMA_FILES until the first real data file lands
(that bucket arrives with the artifact).

Usage
-----
From the repo root (REPO_ROOT-relative defaults)::

    uv run --group data python script/build_frontier.py \\
        --input-root finetuned --output-dir finetuned/frontier

See also:
    ``script/export_runs.py`` — the imported reader/metric authorities
    and the FLOPs-abort discipline mirrored here.
    ``pipeline/run_finetune.py`` — the trainable-params persistence
    producer (06-02).
    ``pipeline/run_sweep.py`` — the run_record producer (the peft field
    is the record-level method source).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from export_runs import (
    load_run_records,
    resolve_dataset_metric,
    resolve_metric_key,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

# Alias suffixes stripped for the base-model join (+probe is 06-05's
# frozen-probe lane arriving on this same seam).
ALIAS_SUFFIXES = ("+lora", "+ia3", "+probe")

CSV_COLUMNS = [
    "model", "base_model", "task", "seed", "method", "wall_hours",
    "total_flos", "trainable_params_pct", "score", "score_delta", "notes",
]


def _alias_suffix(model: str) -> str | None:
    """The trailing adapter/probe suffix, if any."""
    for suffix in ALIAS_SUFFIXES:
        if model.endswith(suffix):
            return suffix
    return None


def _strip_alias(model: str) -> str:
    """The base-model join key (alias suffix removed)."""
    suffix = _alias_suffix(model)
    return model[: -len(suffix)] if suffix else model


def _derive_method(model: str, record: dict[str, Any]) -> str:
    """Suffix first (+lora/+ia3/+probe), else the record peft field, else
    none — the dir name is the physical isolation truth, the record field
    the mode marker the sweep wrote."""
    suffix = _alias_suffix(model)
    if suffix:
        return suffix[1:]
    peft = record.get("peft")
    if isinstance(peft, str) and peft:
        return peft
    return "none"


def _finite(value: Any) -> float | None:
    """Coerce to a finite float, or ``None`` (the exporter's WR-03
    semantics: non-finite = missing)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _wall_hours(record: dict[str, Any]) -> float | None:
    """``finished_at`` minus ``started_at`` in wall-clock hours (6dp), or
    ``None`` when either timestamp is absent/unparseable/negative — the
    null is disclosed in the row notes."""
    started = record.get("started_at")
    finished = record.get("finished_at")
    if not started or not finished:
        return None
    try:
        delta = (
            datetime.fromisoformat(finished)
            - datetime.fromisoformat(started)
        )
    except (TypeError, ValueError):
        return None
    seconds = delta.total_seconds()
    if seconds < 0:
        return None
    return round(seconds / 3600.0, 6)


def _primary_score(metrics: dict[str, Any], slot: str) -> float | None:
    """The record's value for the task's primary-metric export slot.

    Iterates the record's metric keys in INSERTION order and keeps the
    LAST finite value whose exporter resolution lands on ``slot`` —
    EXACTLY the collision rule ``export_runs._collect_cell_values``
    applies (its per-slot ``[seed] = value`` assignment lets the last
    insertion-order key win), so a record whose metrics carry two
    spellings resolving to one slot (e.g. a run_record ``AUROC`` beside
    a suite ``eval_AUROC`` after the seed_result merge) yields the SAME
    number the leaderboard exporter would emit (LOW-07, phase-06
    review: this resolver previously took the FIRST SORTED key,
    silently diverging from the exporter under exactly that collision).
    The single-key case is identical under both rules.
    """
    value: float | None = None
    for key, raw in metrics.items():
        if resolve_metric_key(key) == slot:
            candidate = _finite(raw)
            if candidate is not None:
                value = candidate
    return value


def build_frontier_rows(
    input_root: Path, datasets_info: dict[str, Any]
) -> list[dict[str, Any]]:
    """Derive the frontier rows from the run-record tree.

    Two sorted passes: (1) collect the none-method per-seed scores per
    ``(base_model, task)`` — the score_delta reference population; (2)
    emit one row per COMPLETED record with every derivation and its
    disclosures. Non-completed records contribute nothing (status lives
    in the run_record/manifest contracts, not the frontier).

    Args:
        input_root: The sweep output root (``{model}/{task}/seed_{n}/``).
        datasets_info: The datasets registry (the metric-declaration
            join source; an unregistered task aborts — the exporter's
            hard-fail discipline).

    Returns:
        The row list, in sorted (model, task, seed) order.

    Raises:
        RuntimeError: a completed record is missing a finite
            ``total_flos`` — the message names the record path (FLOPs is
            a required bare number; 0 or ``""`` would falsify it).
        KeyError: the tree carries a task absent from ``datasets_info``.
    """
    input_root = Path(input_root)
    tree = load_run_records(input_root)

    def slot_for(task: str) -> str:
        metric = datasets_info[task]["metric"]
        return resolve_dataset_metric(metric)

    none_scores: dict[tuple[str, str], list[float]] = {}
    for model in sorted(tree):
        base = _strip_alias(model)
        for task in sorted(tree[model]):
            for seed in sorted(tree[model][task]):
                record = tree[model][task][seed]
                if record.get("status") != "completed":
                    continue
                if _derive_method(model, record) != "none":
                    continue
                score = _primary_score(
                    record.get("metrics") or {}, slot_for(task))
                if score is not None:
                    none_scores.setdefault((base, task), []).append(score)

    rows: list[dict[str, Any]] = []
    for model in sorted(tree):
        base = _strip_alias(model)
        for task in sorted(tree[model]):
            slot = slot_for(task)
            for seed in sorted(tree[model][task]):
                record = tree[model][task][seed]
                if record.get("status") != "completed":
                    continue
                metrics = record.get("metrics") or {}
                record_path = (
                    input_root / model / task / f"seed_{seed}"
                    / "run_record.json"
                )
                flos = _finite(metrics.get("total_flos"))
                if flos is None:
                    raise RuntimeError(
                        f"completed run record is missing a finite "
                        f"'total_flos' (the frontier requires the bare "
                        f"FLOPs number — emitting 0 or '' would falsify "
                        f"it): {record_path}"
                    )
                notes: list[str] = []
                pct = _finite(metrics.get("trainable_params_pct"))
                if pct is None:
                    notes.append(
                        "trainable_params_pct absent — the record "
                        "predates the 06-02 run_finetune persistence"
                    )
                score = _primary_score(metrics, slot)
                if score is None:
                    notes.append(
                        f"primary metric "
                        f"{datasets_info[task]['metric']!r} (slot "
                        f"{slot!r}) has no finite value in the record — "
                        "score undefined"
                    )
                wall = _wall_hours(record)
                if wall is None:
                    notes.append(
                        "started_at/finished_at missing or unparseable — "
                        "wall_hours undefined"
                    )
                method = _derive_method(model, record)
                if method == "none":
                    delta = None
                    notes.append(
                        "method=none is the score_delta reference — "
                        "delta is defined for adapter rows only"
                    )
                elif score is None:
                    delta = None
                    notes.append(
                        "no finite score for this row — score_delta "
                        "undefined"
                    )
                else:
                    counterparts = none_scores.get((base, task))
                    if not counterparts:
                        delta = None
                        notes.append(
                            f"no completed none-method run for "
                            f"({base}, {task}) — no score_delta "
                            "counterpart"
                        )
                    else:
                        delta = score - (
                            sum(counterparts) / len(counterparts)
                        )
                rows.append({
                    "model": model,
                    "base_model": base,
                    "task": task,
                    "seed": seed,
                    "method": method,
                    "wall_hours": wall,
                    "total_flos": flos,
                    "trainable_params_pct": pct,
                    "score": score,
                    "score_delta": delta,
                    "notes": notes,
                })
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """Deterministic JSON write (the repo-wide byte convention)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=4, ensure_ascii=False, sort_keys=True)


def _csv_cell(value: Any) -> str:
    """One CSV cell: nulls empty, notes joined, everything else str()."""
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(value)
    return str(value)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Deterministic CSV write: the fixed CSV_COLUMNS order, \n line
    endings (byte-stable across platforms)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(CSV_COLUMNS)
        for row in rows:
            writer.writerow(
                [_csv_cell(row[column]) for column in CSV_COLUMNS])


def _md_cell(value: Any) -> str:
    """One markdown table cell (pipes escaped, nulls empty)."""
    text = _csv_cell(value)
    return text.replace("|", "\\|")


def _write_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    """Render the SAME rows as a generated markdown appendix table (the
    DATA.md appendix convention: a generated-file stamp, one table row
    per frontier row). NOT wired into DATA.md in 06-02 — it activates
    when real post-E2' data exists."""
    lines = [
        (
            "<!-- GENERATED by script/build_frontier.py -- do not edit by "
            "hand: regenerate with the generator over the run-record "
            "tree -->"
        ),
        "",
        "## Cost-accuracy frontier (generated appendix)",
        "",
        "| " + " | ".join(CSV_COLUMNS) + " |",
        "|" + "---|" * len(CSV_COLUMNS),
    ]
    for row in rows:
        lines.append(
            "| " + " | ".join(
                _md_cell(row[column]) for column in CSV_COLUMNS
            ) + " |"
        )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_frontier(
    input_root: Path,
    datasets_info_path: Path,
    output_dir: Path,
    data_md: Path | None = None,
) -> list[dict[str, Any]]:
    """Build the rows and emit the dual artifacts (+ optional markdown).

    Args:
        input_root: The sweep output root.
        datasets_info_path: The datasets registry JSON path.
        output_dir: Destination for frontier.json + frontier.csv.
        data_md: Optional markdown-appendix destination (implemented +
            tested; NOT wired into DATA.md until real post-E2' data
            exists).

    Returns:
        The derived rows (in emission order).
    """
    with Path(datasets_info_path).open("r", encoding="utf-8") as fh:
        datasets_info = json.load(fh)
    rows = build_frontier_rows(Path(input_root), datasets_info)
    _write_json(Path(output_dir) / "frontier.json", {"rows": rows})
    _write_csv(Path(output_dir) / "frontier.csv", rows)
    if data_md is not None:
        _write_markdown(Path(data_md), rows)
    return rows


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="build_frontier",
        description=(
            "Cost-accuracy frontier table generator: F2 run records -> "
            "frontier.{json,csv} (+ optional --data-md appendix)."
        ),
    )
    parser.add_argument(
        "--input-root", type=Path, default=REPO_ROOT / "finetuned",
        help="sweep output root (default: %(default)s)")
    parser.add_argument(
        "--datasets-info", type=Path,
        default=REPO_ROOT / "pipeline" / "datasets_info.json",
        help="datasets registry, the metric-declaration join source "
             "(default: %(default)s)")
    parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="frontier.{json,csv} destination (default: derived as "
             "{input-root}/frontier — a sibling of the sweep output, "
             "NEVER dnallm-mark/data: the committed artifact is gated on "
             "real post-E2' numbers)")
    parser.add_argument(
        "--data-md", type=Path, default=None,
        help="additionally render the rows as a generated markdown "
             "appendix table at this path (implemented + tested; NOT "
             "wired into DATA.md until real post-E2' data exists)")
    return parser


def _argument_defaults() -> dict[str, Any]:
    """The parser's defaults (the publication-gate test's surface)."""
    return {
        action.dest: action.default
        for action in _build_parser()._actions
        if action.dest != "help"
    }


def main(argv: Sequence[str] | None = None) -> int:
    """CLI: repo-root-runnable with REPO_ROOT-relative defaults."""
    args = _build_parser().parse_args(argv)
    output_dir = (
        args.output_dir
        if args.output_dir is not None
        else args.input_root / "frontier"
    )
    rows = write_frontier(
        args.input_root, args.datasets_info, output_dir, args.data_md)
    print(
        f"Frontier: {len(rows)} row(s) -> "
        f"{output_dir / 'frontier.json'} + "
        f"{output_dir / 'frontier.csv'}"
    )
    if args.data_md is not None:
        print(f"Markdown appendix: {args.data_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
