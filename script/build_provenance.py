"""Dataset provenance emission (DATA-04 / DATA-05, 06-04).

Purpose
-------
Project the six provenance columns of the unified datasets registry
(``pipeline/datasets_info.json`` — the D-10 single source of truth) into
the reviewer-facing downloadable artifacts and the generated DATA.md
appendix:

1. ``dnallm-mark/data/provenance.json`` — ``{"rows": [...]}``, one row per
   registry dataset (sorted), each carrying ``dataset`` + the six provenance
   fields; strict-schema'd by ``schemas/provenance.json`` (the
   tests/test_schemas.py ``provenance`` bucket).
2. ``dnallm-mark/data/provenance.csv`` — the same rows as a flat CSV (the
   n_audit.{json,csv} dual-artifact convention). **This CSV is the
   maintainer-editable surface**: corrections are made here, then ingested
   with ``script/convert_registry.py --to-json --merge-existing`` — never
   by hand-editing the JSON registry (D-10).
3. The ``DATA.md`` appendix between the explicit GENERATED PROVENANCE
   BEGIN/END markers — regeneration replaces ONLY the marked section; the
   maintainer-authored sections around it are byte-identical after a run.
   When the markers are absent (the first run over a pre-provenance
   DATA.md), the section is appended.

Unspecified discipline (CONTEXT Area 2, binding)
------------------------------------------------
Provenance values were research-drafted from public sources (dataset
papers, ModelScope/HF/GitHub pages; 2026-10-11). Every unresolved
license/citation/download cell is the literal string ``Unspecified`` with
the source link in ``source`` — NEVER blank. The generated table is
reviewed by the maintainer before publication (the Phase 6 Task 4
blocking checkpoint); corrections flow CSV -> convert_registry
``--to-json --merge-existing`` -> re-run this emitter.

Determinism
-----------
Sorted iteration, ``sort_keys=True`` serialization, csv-module neutral
quoting (T-06-11: values are data and are never executed), no clock —
re-running over an unchanged registry is byte-identical, so the emitter
joins the ``make data`` chain and is drift-gated.

Usage (from the repo root, REPO_ROOT-relative paths)::

    uv run --group data python script/build_provenance.py

See also:
    - ``script/convert_registry.py`` — the ingest path for CSV corrections.
    - ``script/audit_n_frequencies.py`` — the emission-trio convention.
    - ``schemas/provenance.json`` — the strict artifact schema.
    - ``tests/test_build_provenance.py`` — the behavior contracts.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

# ===== Configuration =====

PROVENANCE_FIELDS = (
    "source",
    "citation",
    "license",
    "preprocessing",
    "download_url",
    "download_url_alternates",
)

CSV_HEADER = ["dataset", *PROVENANCE_FIELDS]

# DATA.md marker discipline: the appendix lives strictly between these
# HTML comments; everything outside them is maintainer-authored and is
# never touched by regeneration.
BEGIN_MARKER = (
    "<!-- GENERATED PROVENANCE BEGIN — script/build_provenance.py; do not"
    " edit by hand: correct values in dnallm-mark/data/provenance.csv,"
    " ingest via script/convert_registry.py --to-json --merge-existing,"
    " then re-run `make data` -->"
)
END_MARKER = "<!-- GENERATED PROVENANCE END -->"


def build_rows(registry: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    """Build the sorted provenance rows from the registry.

    Args:
        registry (dict): The unified datasets registry (D-10 JSON form).

    Returns:
        list[dict]: One row per dataset (sorted by name), each carrying
        ``dataset`` plus the six provenance fields.

    Raises:
        SystemExit: If any entry is missing a provenance field or carries
            a blank value — the committed artifact never has blank cells
            (the Unspecified discipline).
    """
    rows: list[dict[str, str]] = []
    for name in sorted(registry):
        entry = registry[name]
        row: dict[str, str] = {"dataset": name}
        for field in PROVENANCE_FIELDS:
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                sys.exit(
                    f"[Error] {name}: provenance field '{field}' is missing"
                    f" or blank ({value!r}) — unresolved values must be the"
                    " literal string 'Unspecified', never blank"
                )
            row[field] = value
        rows.append(row)
    return rows


def emit_json(path: Path, rows: list[dict[str, str]]) -> None:
    """Write ``provenance.json`` (sorted keys, no clock — byte-stable)."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"rows": rows}, fh, indent=4, sort_keys=True,
                  ensure_ascii=False)
        fh.write("\n")


def emit_csv(path: Path, rows: list[dict[str, str]]) -> None:
    """Write ``provenance.csv`` — header row first, neutral csv quoting.

    The csv module's QUOTE_MINIMAL quoting neutralizes embedded commas and
    quotes (T-06-11); values are data and are never executed anywhere in
    the ingest path.
    """
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(CSV_HEADER)
        for row in rows:
            writer.writerow([row[key] for key in CSV_HEADER])


def _md_cell(value: str) -> str:
    """Markdown-table cell (pipes escaped; values are plain text)."""
    return value.replace("|", "\\|")


def render_block(rows: list[dict[str, str]]) -> str:
    """Render the full marker-delimited appendix block (no trailing
    newline — the text following the END marker in DATA.md keeps its own).

    Args:
        rows: The provenance rows (from :func:`build_rows`).

    Returns:
        str: BEGIN marker line, the section body, END marker line.
    """
    unspecified_license = sum(1 for r in rows if r["license"] == "Unspecified")
    unspecified_citation = sum(1 for r in rows if r["citation"] == "Unspecified")
    preprocessing = rows[0]["preprocessing"] if rows else ""
    lines = [
        BEGIN_MARKER,
        "",
        "## Dataset provenance (DATA-04 / DATA-05)",
        "",
        "One row per benchmark dataset: where it comes from, under what",
        "terms, and where to download it. Values were research-drafted from",
        "public sources (dataset papers, ModelScope/Hugging Face/GitHub",
        "pages; 2026-10-11) and **reviewed and accepted by the maintainer",
        f"(2026-10-11)** — of the {len(rows)} datasets,",
        f"{unspecified_license} carry an unresolved license and",
        f"{unspecified_citation} an unresolved citation, marked as the",
        "literal `Unspecified` (never a blank cell), with the source link",
        "carried in the `source` column. Corrections flow through the",
        "downloadable CSV: edit `data/provenance.csv`, ingest via",
        "`script/convert_registry.py --to-json --merge-existing`, re-run",
        "`make data`.",
        "",
        f"**Preprocessing (uniform across all {len(rows)} datasets):**",
        f"{preprocessing}",
        "",
        "**Download policy:** the ModelScope mirror is the default URL",
        "where the dataset's maintainer organization hosts one, with the",
        "Hugging Face mirror as the alternate; datasets with no verified",
        "public mirror of the exact packaged form carry `Unspecified` — the",
        "exact packaged copies (per-task train/dev/test CSVs) ship in the",
        "project's Zenodo record linked from the README.",
        "",
        (
            "Machine-readable forms: [`data/provenance.json`]"
            "(dnallm-mark/data/provenance.json) and [`data/provenance.csv`]"
            "(dnallm-mark/data/provenance.csv) (schema:"
            "[`schemas/provenance.json`](schemas/provenance.json))."
        ),
        "",
        "| Dataset | Source | License | Citation |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        source_link = f"[link]({_md_cell(row['source'])})"
        lines.append(
            f"| {_md_cell(row['dataset'])} | {source_link} | "
            f"{_md_cell(row['license'])} | {_md_cell(row['citation'])} |"
        )
    lines += ["", END_MARKER]
    return "\n".join(lines)


def apply_data_md(data_md: Path, rows: list[dict[str, str]]) -> None:
    """Write the appendix into DATA.md under marker discipline.

    Markers present -> replace ONLY the content from the BEGIN marker
    through the END marker (maintainer sections byte-identical). Markers
    absent -> append the block (the bootstrap path). A BEGIN marker with
    no END marker aborts loudly.

    Args:
        data_md: The DATA.md path (read if present).
        rows: The provenance rows.
    """
    block = render_block(rows)
    if data_md.is_file():
        text = data_md.read_text(encoding="utf-8")
    else:
        text = ""
    if BEGIN_MARKER in text:
        if END_MARKER not in text:
            sys.exit(
                "[Error] DATA.md carries the GENERATED PROVENANCE BEGIN"
                " marker without its END marker — fix the file before"
                " regenerating"
            )
        begin = text.index(BEGIN_MARKER)
        end = text.index(END_MARKER) + len(END_MARKER)
        text = text[:begin] + block + text[end:]
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        text += ("\n" if text else "") + block + "\n"
    data_md.parent.mkdir(parents=True, exist_ok=True)
    data_md.write_text(text, encoding="utf-8")


def write_artifacts(
    registry: dict[str, dict[str, Any]], data_dir: Path, data_md: Path,
) -> list[Path]:
    """Emit every artifact (deterministic; parent dirs created).

    Args:
        registry: The unified datasets registry (D-10 JSON form).
        data_dir: Destination for provenance.json / provenance.csv.
        data_md: Destination for the DATA.md appendix.

    Returns:
        list[Path]: The written artifact paths.
    """
    rows = build_rows(registry)
    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = data_dir / "provenance.json"
    csv_path = data_dir / "provenance.csv"
    emit_json(json_path, rows)
    emit_csv(csv_path, rows)
    apply_data_md(data_md, rows)
    return [json_path, csv_path, data_md]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments (REPO_ROOT-relative defaults)."""
    parser = argparse.ArgumentParser(
        prog="build_provenance",
        description=(
            "Emit the dataset provenance artifacts (provenance.{json,csv}"
            " + the DATA.md appendix) from the unified registry"
            " (DATA-04/DATA-05)."
        ),
    )
    parser.add_argument(
        "--registry", type=Path,
        default=REPO_ROOT / "pipeline" / "datasets_info.json",
        help="the D-10 unified datasets registry (default: %(default)s)",
    )
    parser.add_argument(
        "--data-dir", type=Path, default=REPO_ROOT / "dnallm-mark" / "data",
        help="destination for provenance.json / provenance.csv"
             " (default: %(default)s)",
    )
    parser.add_argument(
        "--data-md", type=Path, default=REPO_ROOT / "DATA.md",
        help="destination for the generated DATA.md appendix"
             " (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: read the registry, emit the artifacts."""
    args = parse_args(argv)
    with open(args.registry, "r", encoding="utf-8") as fh:
        registry = json.load(fh)
    artifacts = write_artifacts(registry, args.data_dir, args.data_md)
    print(f"✅ Provenance artifacts ({len(registry)} datasets):")
    for path in artifacts:
        print(f"  ✅ {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
