"""gen_progress — offline generator of the web progress mirror (WEB-01).

Purpose
-------
Serialize one or more sweep output roots into the static JSON the
read-only progress page renders — ``dnallm-mark/data/progress/sweep.json``
— so the team can follow a multi-day sweep in a browser without SSH
access to the training host (D-02, under the static-hosting constraint:
regeneration is a manual/CI step, the page fetches once on load, and
reload equals refresh — no backend, no polling, no CDN addition).

Direction of truth
------------------
``tui.services.sweep_monitor`` — the pure, textual-free scanner
(Phase 11). This script IMPORTS the scanner and serializes ITS
dataclasses verbatim (``SweepSummary`` / ``SweepStats`` / ``CurrentCell``
/ ``EtaEstimate`` / ``CellRow`` / ``CellSeed`` plus the machine-string
vocabularies ``finished``/``running``/``artifacts_only``,
``completed``/``failed``/``skipped``/``running``/``queued``,
``pending``/``point``/``range``/``none``). It never re-walks artifact
trees and never re-derives states, counts, or ETAs — the D-05
same-source discipline; the import-lock test keeps the scanner
textual-free, so this script runs headless.

``newest_mtime`` is deliberately NOT emitted (a churn signal, not
team-facing data — the checker recommendation ratified in the 12-UI-SPEC).
``state_counts`` is derived from the same cells pass (the page's summary
chips; seed states outside the scanner vocabulary pass through verbatim
in ``cells`` and are not counted in the five chips).

Behavior
--------
Per root, in argv order — one sweep entry per root, NO dedupe (the
honest mirror of the TUI's N-row discovery):

1. ``full_scan`` classifies the root (manifest present -> finished);
2. ``cells_view`` derives the per-(model, task) cell rows;
3. ``stats`` derives done/total/current/elapsed/ETA (``now`` is the
   injected generator clock).

A root the scanner yields nothing for (nonexistent, unreadable, or no
artifacts) prints one ``[Skip]`` console line and is ABSENT from the
JSON — never a half-entry. Damaged artifacts degrade through the
scanner's tolerant readers; this script never crashes on a damaged root.

Multi-root warning (the runbook rule, 12-04): NEVER pass worker roots
AND their merged root together — every cell would appear twice (two
sweeps in the JSON, double-counted in the page's selector view). Pass
every worker root for the live view, or the merged root alone for the
post-run view.

Determinism: ``json.dump(..., sort_keys=True, indent=4,
ensure_ascii=False)`` — the same roots plus the same pinned ``now``
produce byte-identical output. ``generated_at`` is ISO-8601 UTC from
the generator clock (the injected ``now`` when given, the real clock
otherwise); the page renders it verbatim, never a client clock.

Usage
-----
From the repo root (``--output`` resolves relative paths against the
CWD — the export_runs.py CWD convention)::

    uv run --group tui --group dev python script/gen_progress.py \\
        [ROOT ...] --output dnallm-mark/data/progress/sweep.json

No positional ROOT -> the scanner's ``DEFAULT_OUTPUT_ROOTS`` (the two
``./finetuned`` resolutions). The env carries the ``tui`` group because
the scanner chain imports platformdirs via ``tui.services.settings``.

See also:
    - ``tui/services/sweep_monitor.py`` — the scanner; every emitted
      field's semantics live there and nowhere else.
    - ``dnallm-mark/js/progress.js`` — the page consuming this JSON.
    - ``script/export_runs.py`` — the script-conventions precedent.
"""

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

# ===== sys.path bootstrap (the tests/conftest.py contract, inlined) =====
# Both roots BEFORE the scanner import: the repo root for the
# package-qualified ``tui`` import, pipeline/ for the scanner's
# top-level siblings (run_sweep, artifact_loader).
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "pipeline"))

from tui.services import sweep_monitor

#: The frozen data-contract version (12-UI-SPEC): bump on any breaking
#: shape change.
SCHEMA_VERSION = 1

#: The five cell-state keys the summary chips render (scanner
#: vocabulary; key order is irrelevant under sort_keys).
_CELL_STATE_KEYS = (
    sweep_monitor.CELL_COMPLETED,
    sweep_monitor.CELL_FAILED,
    sweep_monitor.CELL_SKIPPED,
    sweep_monitor.CELL_RUNNING,
    sweep_monitor.CELL_QUEUED,
)


def _utc_stamp(epoch: float) -> str:
    """ISO-8601 UTC, second precision, Z-suffixed (the UI-SPEC stamp)."""
    return datetime.fromtimestamp(float(epoch), tz=UTC).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _current_cell_payload(current):
    """``CurrentCell`` -> the frozen ``{model, task, seed}`` object."""
    if current is None:
        return None
    return {"model": current.model, "task": current.task,
            "seed": current.seed}


def _eta_payload(eta):
    """``EtaEstimate`` -> all four frozen fields; exactly the mode's
    meaningful fields carry values, the rest stay null."""
    return {
        "mode": eta.mode,
        "point_seconds": eta.point_seconds,
        "lo_seconds": eta.lo_seconds,
        "hi_seconds": eta.hi_seconds,
    }


def _state_counts(cells):
    """The five cell states -> seed counts over the same cells pass.

    Seed states outside the scanner vocabulary (unknown record statuses
    pass through verbatim in ``cells``) are not counted here: the five
    chips ARE the vocabulary; the raw string stays visible in its cell.
    """
    counts = {state: 0 for state in _CELL_STATE_KEYS}
    for row in cells:
        for seed in row.seeds:
            if seed.state in counts:
                counts[seed.state] += 1
    return counts


def _cells_payload(cells):
    """``CellRow`` tuple -> the frozen per-row dicts (``fraction_states``
    pairs serialize as JSON arrays natively)."""
    return [
        {
            "model": row.model,
            "task": row.task,
            "seeds": [
                {
                    "seed": seed.seed,
                    "state": seed.state,
                    "fraction_states": seed.fraction_states,
                }
                for seed in row.seeds
            ],
        }
        for row in cells
    ]


def _sweep_payload(summary, cells, stats):
    """One sweep entry: scanner dataclass fields under frozen names."""
    return {
        "root": summary.root.name,
        "state": summary.state,
        "done": stats.done,
        "total": stats.total,
        "elapsed_seconds": stats.elapsed_seconds,
        "current": _current_cell_payload(stats.current),
        "eta": _eta_payload(stats.eta),
        "state_counts": _state_counts(cells),
        "cells": _cells_payload(cells),
    }


def _write_json(path: Path, payload: dict) -> None:
    """The deterministic-JSON discipline (run_sweep's ``_write_json``):
    sort_keys + indent 4 + ensure_ascii False -> byte-stable output."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=4, ensure_ascii=False,
                  sort_keys=True)


def main(argv=None, now=None) -> int:
    # ===== Configuration =====
    parser = argparse.ArgumentParser(
        description="Generate the static web progress mirror "
                    "(dnallm-mark/data/progress/sweep.json) from sweep "
                    "output roots via the pure scanner.")
    parser.add_argument(
        "roots", nargs="*", type=Path, default=[],
        help="sweep output root(s): one sweep entry per root, in argv "
             "order (multi-worker: pass every worker root; NEVER also "
             "the merged root — cells would double-count). Default: "
             "the scanner's DEFAULT_OUTPUT_ROOTS.")
    parser.add_argument(
        "--output", type=Path,
        default=REPO_ROOT / "dnallm-mark" / "data" / "progress"
        / "sweep.json",
        help="output JSON path (CWD-relative when relative; default: "
             "dnallm-mark/data/progress/sweep.json under the repo "
             "root).")
    args = parser.parse_args(argv)

    now_epoch = time.time() if now is None else float(now)
    root_list = [
        Path(root).expanduser().resolve() for root in args.roots
    ] or [
        Path(root).expanduser().resolve()
        for root in sweep_monitor.DEFAULT_OUTPUT_ROOTS
    ]

    scan = sweep_monitor.full_scan(roots=root_list, now=now_epoch)
    summaries = {str(summary.root): summary for summary in scan.sweeps}

    sweeps = []
    for root in root_list:
        summary = summaries.get(str(root))
        if summary is None:
            print(f"  [Skip] {root.name}: root not found or unreadable")
            continue
        cells = sweep_monitor.cells_view(root)
        if summary.state != sweep_monitor.SWEEP_FINISHED and not cells:
            print(f"  [Skip] {root.name}: no sweep artifacts")
            continue
        stats = sweep_monitor.stats(root, now=now_epoch)
        sweeps.append(_sweep_payload(summary, cells, stats))

    payload = {
        "version": SCHEMA_VERSION,
        "generated_at": _utc_stamp(now_epoch),
        "sweeps": sweeps,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    _write_json(args.output, payload)
    print(f"✅ Progress mirror written: {args.output} "
          f"({len(sweeps)} sweeps)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
