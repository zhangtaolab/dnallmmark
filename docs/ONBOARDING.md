# Onboarding: Adding a New Model or Dataset

Two checklists for extending the benchmark. **Every step below is
CPU-only / dry-run** — no GPU is needed to validate the mechanics end to
end; the only GPU steps are the actual training runs, which the maintainer
launches separately (see the README's pipeline section). Each step shows
the exact command and its expected output, run from the repository root.

## Adding a new model

### 1. Add the registry entry

Edit `pipeline/models_info.json` and add one entry keyed by the model's
directory name under `pipeline/models/` (the registry is the single
source of truth, D-10). Two field sets are required:

- the **card** fields the leaderboard renders — `name`, `size (M)`,
  `type` (`MLM` / `CLM` / `DL`), `tokenizer`, `mean_token_len`,
  `architecture`, `series`, `context_len (bp)`, `species`, `huggingface`,
  `modelscope`;
- the **operational four** the pipeline reads — `Model_name`,
  `Model_path` (`models/<key>`), `Model_size`, `Tokenizer`,
  `Mean_token_length` (a `--derive-operational` ingest can fill these
  from card values; see `script/convert_registry.py`).

Unknown values may be left empty in the card — the frontend defensively
renders missing card fields — but never invent them.

### 2. Validate the round-trip (CPU)

```bash
uv run --group data python script/convert_registry.py --kind models --to-csv \
    --input pipeline/models_info.json --output /tmp/models_info.csv
```

Expected output:

```
✅ pipeline/models_info.json -> /tmp/models_info.csv: 62 rows, columns=['Model_name', 'Model_path', 'Model_size', 'Tokenizer', 'Mean_token_length']
```

Your new model must appear as its own row; the row count must equal the
registry size.

### 3. Add model quirks if needed (pipeline)

If the model needs special handling, add its name to the relevant quirk
list inside `pipeline/run_finetune.py`'s `if __name__ == "__main__":`
block: `model_not_use_safetensors`, `deeplearning_models`,
`models_no_char_n`, `models_with_limited_length`,
`models_only_support_fp32`, or `special_models` (loads the with-head
config variant). Most HF-compatible transformers models need none.

### 4. Re-run the registry contract tests (CPU)

```bash
uv run --group dev pytest tests/test_model_registry.py tests/test_registry_unification.py -q
```

Expected output:

```
N passed in <1s
```

These pin the single-source contracts (key == name field, operational
columns present, JSON/CSV consistency).

### 5. Validate the sweep matrix with a dry run (CPU, launches nothing)

```bash
uv run --group dev python pipeline/run_sweep.py --dry-run \
    --models <your-model> --seeds 42,43,44 --output-root /tmp/onboard-check
```

Expected output:

```
[Dry-run] 150 planned cell(s) over 1 model(s) x 50 task(s) x 3 seed(s); manifest: /tmp/onboard-check/sweep_manifest.json
```

(one cell per model x task x seed; `sweep_manifest.json` lists each cell
with `"status": "planned"` and its seed-isolated output dir
`{root}/{model}/{task}/seed_{seed}`). This proves the registry join, the
matrix enumeration, and the argv construction — without launching any
training. To validate a subset, add `--tasks <name1,name2>`.

### 6. GPU runs (maintainer, not part of onboarding)

The actual fine-tuning runs on the GPU host: `pipeline/run_sweep.py`
without `--dry-run` (or `pipeline/run_finetune.py` directly, from
`pipeline/`). See the README's *Benchmark Pipeline* section.

## Adding a new dataset

### 1. Add the registry entry (including provenance)

Edit the CSV projection of the datasets registry and ingest it — never
hand-edit `pipeline/datasets_info.json` (D-10: the JSON is authoritative
but the CSV is the editing surface):

```bash
# Regenerate the editable CSV from the current registry:
uv run --group data python script/convert_registry.py --kind datasets --to-csv \
    --input pipeline/datasets_info.json --output /tmp/datasets_info.csv
```

Add one row with all 17 columns: the operational fields (`Index`
(next free), `Dataset_name` in `Source__task` form, `Dataset_path`
(`datasets/<group>/<task>`), `Train`/`Test`/`Dev` row counts, `type`,
`labels`, `length`, `metric` (one of `f1`, `mcc`, `spearmanr`, `AUPRC`
in the performance-JSON schema's closed enum, plus `r2` — the
registry's three `plant-genomic-benchmark__gene_exp.*` tasks declare
`r2`, a pre-existing registry↔schema divergence: the committed
performance JSONs and the schema enums carry only the four enum values,
so a new `r2` task keeps the registry/pipeline working but a new FIFTH
metric value turns the schema tests red until every enum copy is
updated together), `Category`
(`Animals` / `Plants` / `Microbe` — this drives arena grouping), and the
six provenance columns `source`, `citation`, `license`, `preprocessing`,
`download_url`, `download_url_alternates` — unresolved provenance values
are the literal `Unspecified`, never blank (see
[DATA.md](../DATA.md)).

Ingest:

```bash
uv run --group data python script/convert_registry.py --kind datasets --to-json \
    --input /tmp/datasets_info.csv --output pipeline/datasets_info.json \
    --merge-existing pipeline/datasets_info.json
```

Expected output:

```
✅ /tmp/datasets_info.csv -> pipeline/datasets_info.json: 0 entries added, 51 merged, 0 renamed, 0 derived, 51 total
```

The ingest aborts loudly if the CSV header is missing any expected
column — regenerate the CSV rather than hand-crafting a header.

### 2. Place the split files

Create `pipeline/datasets/<group>/<task>/` with `train.csv`,
`dev.csv`, `test.csv` in the suite's CSV layout (a `sequence` column;
labels integer or `;`-separated for multilabel). If the upstream source
has no dev split, carve one with the stratified splitter:

```bash
uv run --group data python script/make_dev_splits.py --check
```

Expected output ends with a per-task agreement report and exit 0; a
registry/disk count mismatch is a hard error naming the task.

### 3. Check the metric mapping surface (CPU)

The dataset's primary metric is read from the registry `metric` column
(the exporter owns the metric-key mapping — `script/export_runs.py`'s
`resolve_dataset_metric`, re-exported to `summarize_comparison`). If your
dataset introduces a metric name not already in the 28-name canonical
map, the schema enum tests fail — update the schema copies together (see
`tests/test_schemas.py`).

### 4. Dev-split rule

Every task needs a non-empty dev split: checkpoint selection and early
stopping evaluate on dev, and the pipeline refuses to run without one
(EVAL-01 — the suite never silently evaluates on test). `--check` in step
2 verifies this.

### 5. Validate the sweep matrix with a dry run (CPU, launches nothing)

```bash
uv run --group dev python pipeline/run_sweep.py --dry-run \
    --models plant-dnabert-6mer --tasks <your-new-task> --seeds 42 \
    --output-root /tmp/onboard-check
```

Expected output:

```
[Dry-run] 1 planned cell(s) over 1 model(s) x 1 task(s) x 1 seed(s); manifest: /tmp/onboard-check/sweep_manifest.json
```

### 6. Regenerate the derived data + provenance (CPU)

After the entry lands, refresh the derived artifacts and check the drift
gate:

```bash
make data
git status --porcelain dnallm-mark/data/ DATA.md   # must show ONLY your intended changes
```

`make data` re-runs the aggregation chain including the provenance
emitter; on an already-committed tree it is a byte-identical no-op (CI
enforces this — see [METHODOLOGY](METHODOLOGY.md)). The provenance table
row count is pinned to the corpus size in
`schemas/provenance.json` — update that pin deliberately when the corpus
grows.

### 7. Full local gate (CPU)

```bash
make test && make lint && make typecheck
```

All three must pass before committing the new dataset.

## See also

- [METHODOLOGY](METHODOLOGY.md) — how the numbers are computed.
- [Reproducing the leaderboard](../README.md#reproducing-the-leaderboard)
  (README) — the fresh-clone reproduction path.
- `script/convert_registry.py` — the registry converter (both checklists'
  ingest path).
