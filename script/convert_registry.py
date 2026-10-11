"""Registry converter: JSON <-> CSV, bidirectional, for pipeline metadata registries.

Purpose
-------
Convert the pipeline metadata registries between their JSON object form
(``{name: {field: value, ...}}``) and a flat CSV table form (one row per
entry, ``name`` in a designated name column). Three presets:

- ``models``    : ``pipeline/models_info.{json,csv}``   (name column ``Model_name``)
- ``datasets``  : ``pipeline/datasets_info.{json,csv}``  (name column ``Dataset_name``)
- ``provenance``: ``dnallm-mark/data/provenance.csv``    (name column
  ``dataset`` — the 7-column provenance slice the emitter ships; a
  MERGE-ONLY correction ingest into the datasets registry, MED-03)

Direction of truth (D-10, 2026-10-09): **JSON is the single source of truth.**
CSV is a regenerable, human/spreadsheet-friendly projection used for editing
and exchange; ``--to-csv`` is always safe to re-run. ``--to-json`` is the
ingest path used when unifying a legacy tabular registry into the JSON tree.

Behavior
--------
``--to-json``  Read CSV rows into ``{name: {col: value}}``. Numeric columns
               (preset per kind, extendable via ``--numeric``) are coerced to
               int. The ingest validates that the CSV header carries every
               preset column (the D-10 abort-on-missing-columns family:
               a partial header can never silently drop fields — the error
               names the expected set; columns arriving via ``--map`` count
               as satisfied). With ``--merge-existing PATH`` the CSV fields
               are merged
               into an existing JSON registry: existing keys not named in
               the CSV are preserved; CSV-derived keys overwrite. Column
               names are
               kept verbatim as JSON keys unless renamed via ``--map from=to``
               (repeatable). The name-column cell also lands verbatim as a
               field on every merged entry (D-10: ``key == Model_name`` /
               ``key == Dataset_name`` must hold — the pipeline reads the name
               field from each JSON entry). ``--rename-name from=to``
               (repeatable) rewrites BOTH the merge key and the name-column
               cell before merging, for name-form drift between a legacy
               tabular registry and the JSON keys (a rename that collides with
               another CSV row aborts loudly). ``--derive-operational``
               (models kind, requires ``--merge-existing``) fills the
               operational four for card-only entries that did not come from
               the CSV: ``Model_path = models/{key}``, ``Model_size`` from the
               ``size (M)`` card value with an ``M`` suffix when numeric,
               ``Tokenizer``/``Mean_token_length`` from the
               ``tokenizer``/``mean_token_len`` card values, and
               ``Model_name = key``; existing values are never overwritten and
               card keys are never modified. The datasets preset carries the
               six provenance columns (06-04, DATA-04/DATA-05):
               ``source``, ``citation``, ``license``, ``preprocessing``,
               ``download_url``, ``download_url_alternates`` — unresolved
               values are the literal string ``Unspecified``, never blank
               (the maintainer-editable surface is the CSV projection).
               The ``provenance`` preset (MED-03, phase-06 review) is the
               correction ingest for the emitted
               ``dnallm-mark/data/provenance.csv``: name column
               ``dataset``, six required provenance columns, no numeric
               coercion, and two discipline guards — it REQUIRES
               ``--merge-existing`` (the slice is a correction path over
               the datasets registry, never a standalone ingest) and
               REFUSES rows naming datasets absent from the merge
               registry (a correction edits existing rows; a skeletal
               add would be untrainable). The merged name lands under
               the registry's own ``Dataset_name`` field (the D-10
               ``key == Dataset_name`` contract), not the CSV's
               ``dataset`` column.

``--to-csv``   Flatten JSON entries to CSV. Columns default to the preset
               order; JSON entries missing a column get an empty cell (card
               fields are intentionally lossy in this direction — only the
               listed columns are emitted). ``--columns`` overrides.

Line endings default to LF (git-friendly); ``--crlf`` emits CRLF to match the
legacy ``.txt`` files' style. JSON output is ``indent=4, sort_keys=True,
ensure_ascii=False`` per the project determinism discipline.

Usage
-----
    # Legacy TSV (.txt) -> JSON (unification ingest; handles CRLF input)
    python script/convert_registry.py --kind models --to-json \\
        --input pipeline/models_info.txt --output /tmp/models_info.json \\
        --merge-existing pipeline/models_info.json

    # Provenance correction round-trip (MED-03, the DATA.md-documented
    # maintainer path): edit a cell in the emitted CSV, re-ingest, re-run
    # `make data` to regenerate provenance.{json,csv} + the DATA.md appendix
    python script/convert_registry.py --kind provenance --to-json \\
        --input dnallm-mark/data/provenance.csv \\
        --output pipeline/datasets_info.json \\
        --merge-existing pipeline/datasets_info.json

    # JSON -> CSV (regenerate the human-editable view)
    python script/convert_registry.py --kind models --to-csv \\
        --input pipeline/models_info.json --output pipeline/models_info.csv

    # Round-trip check (operational columns survive json -> csv -> json)
    python script/convert_registry.py --kind datasets --to-csv \\
        --input pipeline/datasets_info.json --output /tmp/d.csv \\
    && python script/convert_registry.py --kind datasets --to-json \\
        --input /tmp/d.csv --output /tmp/d.json && diff <(python -c \\
        "import json;print(json.dumps(json.load(open('pipeline/datasets_info.json')),sort_keys=True,indent=1))") \\
        <(python -c "import json;print(json.dumps(json.load(open('/tmp/d.json')),sort_keys=True,indent=1))")

See also:
    ``script/audit_n_frequencies.py`` for the stdlib-only registry-reading
    style this script follows.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

# ===== Configuration =====

# Per-kind presets: name column, registry name field, default CSV column
# order, numeric columns, and per-kind ingest discipline flags.
#
# ``name_field`` (MED-03, phase-06 review): the JSON field the merged
# entry's name lands in. For models/datasets it equals the CSV name
# column (the D-10 ``key == Model_name`` / ``key == Dataset_name``
# contract). The ``provenance`` slice preset reads the 7-column
# ``data/provenance.csv`` the emitter ships (name column ``dataset``) but
# merges into the DATASETS registry, whose name field is ``Dataset_name``
# — landing the name under ``dataset`` would add a redundant field to
# every entry; the preset maps it onto the registry's own name field
# instead (a no-op value-wise: D-10 already pins the equality).
#
# ``merge_only``: the provenance preset is a CORRECTION path over an
# existing datasets registry, never a standalone ingest (its slice lacks
# every operational column) and never an add path (a row naming a
# dataset absent from the merge registry would create a skeletal,
# untrainable entry — refused loudly; new datasets flow through the full
# ``--kind datasets`` ingest per docs/ONBOARDING.md).
KIND_PRESETS = {
    "models": {
        "name_column": "Model_name",
        "name_field": "Model_name",
        "columns": [
            "Model_name",
            "Model_path",
            "Model_size",
            "Tokenizer",
            "Mean_token_length",
        ],
        "numeric": ["Mean_token_length"],
    },
    "datasets": {
        "name_column": "Dataset_name",
        "name_field": "Dataset_name",
        "columns": [
            "Index",
            "Dataset_name",
            "Dataset_path",
            "Train",
            "Test",
            "Dev",
            "type",
            "labels",
            "length",
            "metric",
            "Category",
            # Six provenance columns (06-04, DATA-04/DATA-05): the D-10
            # single-source registry carries them; unknown values are the
            # literal "Unspecified", never blank.
            "source",
            "citation",
            "license",
            "preprocessing",
            "download_url",
            "download_url_alternates",
        ],
        "numeric": ["Index", "Train", "Test", "Dev", "labels", "length"],
    },
    # The provenance correction slice (MED-03, phase-06 review): ingests
    # the emitted dnallm-mark/data/provenance.csv (7 columns: the dataset
    # key + the six provenance fields) back into pipeline/datasets_info.json
    # via --to-json --merge-existing — the documented reviewer-facing
    # correction path named in the DATA.md appendix, the provenance
    # schema $comment, and the emitter's BEGIN marker.
    "provenance": {
        "name_column": "dataset",
        "name_field": "Dataset_name",
        "columns": [
            "dataset",
            "source",
            "citation",
            "license",
            "preprocessing",
            "download_url",
            "download_url_alternates",
        ],
        "numeric": [],
        "merge_only": True,
    },
}


def parse_args():
    """Parse CLI arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Convert pipeline metadata registries between JSON and CSV"
    )
    parser.add_argument("--kind", choices=sorted(KIND_PRESETS), required=True,
                        help="Which registry preset to use")
    direction = parser.add_mutually_exclusive_group(required=True)
    direction.add_argument("--to-json", action="store_true",
                           help="CSV -> JSON (ingest/unification direction)")
    direction.add_argument("--to-csv", action="store_true",
                           help="JSON -> CSV (regenerate the tabular view)")
    parser.add_argument("--input", required=True, help="Input file path")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--merge-existing", default=None,
                        help="Existing JSON registry to merge CSV fields into "
                             "(--to-json only); keys not named in the CSV are preserved")
    parser.add_argument("--map", action="append", default=[], metavar="FROM=TO",
                        help="Rename a CSV column to a different JSON key "
                             "(repeatable, --to-json only)")
    parser.add_argument("--rename-name", action="append", default=[],
                        metavar="FROM=TO",
                        help="Rename a CSV entry name — rewrites BOTH the merge "
                             "key and the name-column cell — before merging "
                             "(repeatable, --to-json only; a rename that "
                             "collides with another CSV row aborts)")
    parser.add_argument("--derive-operational", action="store_true",
                        help="Fill the operational four for card-only entries "
                             "coming from --merge-existing (models kind, "
                             "--to-json only)")
    parser.add_argument("--numeric", action="append", default=[],
                        metavar="COL",
                        help="Additional numeric columns to coerce to int "
                             "(repeatable, --to-json only; preset numeric columns always coerce)")
    parser.add_argument("--columns", action="append", default=[],
                        metavar="COL",
                        help="Override emitted CSV column order (--to-csv only; "
                             "repeatable, replaces the preset order)")
    parser.add_argument("--crlf", action="store_true",
                        help="Write CRLF line endings (legacy .txt style); default LF")
    return parser.parse_args()


# The models-registry operational columns (D-10): every unified entry must
# carry these four, whatever its origin (tabular row, card, or derivation).
OPERATIONAL_COLUMNS = ("Model_path", "Model_size", "Tokenizer",
                       "Mean_token_length")


def format_model_size(size):
    """Format a ``size (M)`` card value as a ``Model_size`` string.

    Numeric card sizes gain an ``M`` suffix (matching the legacy tabular
    convention, e.g. ``94`` -> ``"94M"``); non-numeric values pass through
    verbatim (e.g. ``"~1B"``).

    Args:
        size: The ``size (M)`` card value (int, float, or str).

    Returns:
        str: The ``Model_size`` string.
    """
    if isinstance(size, bool):
        return str(size)
    if isinstance(size, (int, float)):
        return f"{size}M"
    return str(size)


def derive_operational_fields(registry, csv_names):
    """Fill derived operational fields for card-only entries (D-10).

    Entries that did NOT come from the CSV (they survive from
    ``--merge-existing``) and lack any of the operational four gain derived
    values: ``Model_path = models/{key}`` (the old pipeline's key-derived
    convention), ``Model_size`` from the ``size (M)`` card value with an
    ``M`` suffix when numeric, ``Tokenizer``/``Mean_token_length`` from the
    ``tokenizer``/``mean_token_len`` card values, and ``Model_name = key``.
    Existing values are never overwritten; card keys are never modified.

    Args:
        registry (dict): The merged registry (mutated in place).
        csv_names (set): Entry names supplied by the CSV — never derived.

    Returns:
        int: Number of entries that gained derived fields.
    """
    derived = 0
    for key, entry in registry.items():
        if key in csv_names:
            continue  # came from the CSV — carries the operational fields
        if all(col in entry for col in OPERATIONAL_COLUMNS):
            continue  # already operational — untouched
        size = entry.get("size (M)")
        updates = {
            "Model_name": key,
            "Model_path": f"models/{key}",
            "Model_size": format_model_size(size) if size is not None else None,
            "Tokenizer": entry.get("tokenizer"),
            "Mean_token_length": entry.get("mean_token_len"),
        }
        changed = False
        for col, value in updates.items():
            if value is None or col in entry:
                continue  # no card source, or never overwrite an existing value
            entry[col] = value
            changed = True
        if changed:
            derived += 1
    return derived


def read_csv_rows(path, name_column, numeric_columns, required_header=None):
    """Read a CSV/TSV file into an ordered ``{name: {col: value}}`` mapping.

    Handles both comma and tab delimiters (sniffed from the HEADER LINE
    ONLY — data rows legitimately embed commas inside quoted or
    tab-delimited provenance values, which misleads a sample-wide sniff)
    so the legacy ``.txt`` TSV registries and new ``.csv`` files both
    ingest.

    Args:
        path (str): Input CSV/TSV path.
        name_column (str): Column holding the entry name (becomes the JSON key).
        numeric_columns (set): Columns whose values coerce to int when possible.
        required_header (set | None): Column names the raw header must carry
            (the D-10 abort-on-missing-columns family). ``None`` skips the
            check. ``--map`` targets are pre-subtracted by the caller; the
            caller adds the ``--map`` source names instead.

    Returns:
        dict: Ordered mapping of name -> fields (CSV column names verbatim).

    Raises:
        SystemExit: If the file is missing, the header lacks the name column
            or any ``required_header`` column, or duplicate names are found.
    """
    src = Path(path)
    if not src.is_file():
        sys.exit(f"[Error] Input file not found: {path}")
    with open(src, "r", encoding="utf-8-sig", newline="") as f:
        header_line = f.readline()
        f.seek(0)
        # Sniff ONLY the delimiter, and ONLY from the header line: data rows
        # legitimately embed commas inside provenance values (misleading a
        # sample-wide sniff), and a header-only sniff carries no quotes for
        # the Sniffer to bind a quotechar to — so quoting stays the standard
        # excel form rather than the sniffed (quote-less) dialect.
        try:
            delimiter = csv.Sniffer().sniff(
                header_line, delimiters=",\t"
            ).delimiter
        except csv.Error:
            delimiter = ","  # fall back to comma
        reader = csv.DictReader(f, delimiter=delimiter)
        if reader.fieldnames is None or name_column not in reader.fieldnames:
            sys.exit(f"[Error] Header of {path} lacks name column "
                     f"'{name_column}' (found: {reader.fieldnames})")
        if required_header:
            missing = sorted(required_header - set(reader.fieldnames))
            if missing:
                sys.exit(
                    f"[Error] Header of {path} is missing expected "
                    f"column(s): {', '.join(missing)}; the ingest requires "
                    f"the preset column set: {sorted(required_header)} — "
                    "regenerate the CSV with --to-csv before editing it"
                )
        rows, seen = {}, set()
        for row in reader:
            name = (row.get(name_column) or "").strip()
            if not name:
                continue
            if name in seen:
                sys.exit(f"[Error] Duplicate name '{name}' in {path}")
            seen.add(name)
            fields = {}
            for col, raw in row.items():
                if col is None or col == name_column:
                    continue
                value = (raw or "").strip()
                if col in numeric_columns:
                    try:
                        value = int(value)
                    except ValueError:
                        pass  # leave as string (e.g. empty Dev cells)
                fields[col] = value
            rows[name] = fields
    return rows


def to_json(args, preset):
    """Convert CSV rows to a JSON registry, optionally merging into an existing one."""
    renames = dict(m.split("=", 1) for m in args.map)
    name_renames = dict(m.split("=", 1) for m in args.rename_name)
    numeric = set(preset["numeric"]) | set(args.numeric) | set(renames)
    # D-10 abort-on-missing-columns: every preset column must arrive —
    # either directly in the raw header or via a --map rename whose source
    # name IS in the header (an unsatisfiable map target fails loudly too).
    required_header = (
        set(preset["columns"]) - set(renames.values())
    ) | set(renames.keys())
    rows = read_csv_rows(args.input, preset["name_column"], numeric,
                         required_header=required_header)
    for name, fields in rows.items():
        rows[name] = {renames.get(col, col): value for col, value in fields.items()}

    registry = {}
    if args.merge_existing:
        with open(args.merge_existing, "r", encoding="utf-8") as f:
            registry = json.load(f)
    elif preset.get("merge_only"):
        sys.exit(
            f"[Error] --kind {args.kind} requires --merge-existing — the "
            "provenance slice is a correction path over the datasets "
            "registry, not a standalone ingest"
        )
    if preset.get("merge_only"):
        # A correction CSV edits existing rows: a name absent from the
        # merge registry is a typo (or a new dataset taking the wrong
        # path), and merging it would add a skeletal entry with no
        # operational columns — refuse, naming every unknown row.
        unknown = sorted(set(rows) - set(registry))
        if unknown:
            sys.exit(
                f"[Error] --kind {args.kind} CSV names dataset(s) absent "
                f"from the merge registry: {', '.join(unknown)} — the "
                "correction path edits existing rows; add new datasets "
                "through the full --kind datasets ingest "
                "(docs/ONBOARDING.md)"
            )

    name_field = preset["name_field"]
    added, merged, renamed_count = 0, 0, 0
    seen = set()
    for name, fields in rows.items():
        final_name = name_renames.get(name, name)
        if final_name != name:
            renamed_count += 1
        if final_name in seen:
            sys.exit(f"[Error] Name collision after --rename-name: CSV rows "
                     f"'{name}' and '{final_name}' both map to '{final_name}'")
        seen.add(final_name)
        # The name lands verbatim as the REGISTRY's name field so
        # key == name field holds for every entry (D-10 single-source
        # contract; for the provenance slice that field is Dataset_name,
        # not the CSV's `dataset` column — MED-03).
        fields[name_field] = final_name
        if final_name in registry:
            registry[final_name].update(fields)
            merged += 1
        else:
            registry[final_name] = fields
            added += 1

    derived = 0
    if args.derive_operational:
        if not args.merge_existing:
            sys.exit("[Error] --derive-operational requires --merge-existing "
                     "(it derives fields for entries that come from the "
                     "existing registry, not from the CSV)")
        if args.kind != "models":
            sys.exit("[Error] --derive-operational applies to --kind models only")
        derived = derive_operational_fields(registry, csv_names=seen)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=4, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    print(f"✅ {args.input} -> {out}: {added} entries added, {merged} merged, "
          f"{renamed_count} renamed, {derived} derived, {len(registry)} total")


def to_csv(args, preset):
    """Flatten a JSON registry to CSV columns (missing fields become empty cells)."""
    with open(args.input, "r", encoding="utf-8") as f:
        registry = json.load(f)

    name_column = preset["name_column"]
    columns = args.columns or preset["columns"]
    if name_column not in columns:
        columns = [name_column] + [c for c in columns if c != name_column]

    lineterm = "\r\n" if args.crlf else "\n"
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator=lineterm)
        writer.writerow(columns)
        for name in sorted(registry):
            entry = registry[name]
            writer.writerow([
                name if col == name_column else entry.get(col, "")
                for col in columns
            ])
    print(f"✅ {args.input} -> {out}: {len(registry)} rows, columns={columns}")


def main():
    """Entry point: dispatch to the requested conversion direction."""
    args = parse_args()
    if args.to_csv and (args.rename_name or args.derive_operational):
        sys.exit("[Error] --rename-name/--derive-operational apply to "
                 "--to-json only")
    preset = KIND_PRESETS[args.kind]
    if args.to_json:
        to_json(args, preset)
    else:
        to_csv(args, preset)


if __name__ == "__main__":
    main()
