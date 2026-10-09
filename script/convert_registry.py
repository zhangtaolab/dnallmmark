"""Registry converter: JSON <-> CSV, bidirectional, for pipeline metadata registries.

Purpose
-------
Convert the pipeline metadata registries between their JSON object form
(``{name: {field: value, ...}}``) and a flat CSV table form (one row per
entry, ``name`` in a designated name column). Two registries are preset:

- ``models``  : ``pipeline/models_info.{json,csv}``   (name column ``Model_name``)
- ``datasets``: ``pipeline/datasets_info.{json,csv}``  (name column ``Dataset_name``)

Direction of truth (D-10, 2026-10-09): **JSON is the single source of truth.**
CSV is a regenerable, human/spreadsheet-friendly projection used for editing
and exchange; ``--to-csv`` is always safe to re-run. ``--to-json`` is the
ingest path used when unifying a legacy tabular registry into the JSON tree.

Behavior
--------
``--to-json``  Read CSV rows into ``{name: {col: value}}``. Numeric columns
               (preset per kind, extendable via ``--numeric``) are coerced to
               int. With ``--merge-existing PATH`` the CSV fields are merged
               into an existing JSON registry: existing keys not named in the
               CSV are preserved; CSV-derived keys overwrite. Column names are
               kept verbatim as JSON keys unless renamed via ``--map from=to``
               (repeatable). The final operational/card key naming is owned by
               the Phase 3 plan (D-10); this script is deliberately neutral.

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
    ``script/get_task_performance.py`` for the stdlib-only registry-reading
    style this script follows.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

# ===== Configuration =====

# Per-kind presets: name column, default CSV column order, numeric columns.
KIND_PRESETS = {
    "models": {
        "name_column": "Model_name",
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
        ],
        "numeric": ["Index", "Train", "Test", "Dev", "labels", "length"],
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


def read_csv_rows(path, name_column, numeric_columns):
    """Read a CSV/TSV file into an ordered ``{name: {col: value}}`` mapping.

    Handles both comma and tab delimiters (sniffed from the header line) so
    the legacy ``.txt`` TSV registries and new ``.csv`` files both ingest.

    Args:
        path (str): Input CSV/TSV path.
        name_column (str): Column holding the entry name (becomes the JSON key).
        numeric_columns (set): Columns whose values coerce to int when possible.

    Returns:
        dict: Ordered mapping of name -> fields (CSV column names verbatim).

    Raises:
        SystemExit: If the file is missing, the header lacks the name column,
            or duplicate names are found.
    """
    src = Path(path)
    if not src.is_file():
        sys.exit(f"[Error] Input file not found: {path}")
    with open(src, "r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
        except csv.Error:
            dialect = csv.excel  # fall back to comma
        reader = csv.DictReader(f, dialect=dialect)
        if reader.fieldnames is None or name_column not in reader.fieldnames:
            sys.exit(f"[Error] Header of {path} lacks name column "
                     f"'{name_column}' (found: {reader.fieldnames})")
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
    numeric = set(preset["numeric"]) | set(args.numeric) | set(renames)
    rows = read_csv_rows(args.input, preset["name_column"], numeric)
    for name, fields in rows.items():
        rows[name] = {renames.get(col, col): value for col, value in fields.items()}

    registry = {}
    if args.merge_existing:
        with open(args.merge_existing, "r", encoding="utf-8") as f:
            registry = json.load(f)

    added, merged = 0, 0
    for name, fields in rows.items():
        if name in registry:
            registry[name].update(fields)
            merged += 1
        else:
            registry[name] = fields
            added += 1

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=4, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    print(f"✅ {args.input} -> {out}: {added} entries added, {merged} merged, "
          f"{len(registry)} total")


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
    preset = KIND_PRESETS[args.kind]
    if args.to_json:
        to_json(args, preset)
    else:
        to_csv(args, preset)


if __name__ == "__main__":
    main()
