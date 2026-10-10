"""
Unit tests for ``script/build_frontier.py`` (SC-6/REV-05, 06-02).

The frontier generator derives cost-accuracy rows from the F2 run-record
tree through the exporter's single-reader + single-metric authorities
(``export_runs.load_run_records`` / ``resolve_dataset_metric`` /
``resolve_metric_key`` — never a re-walk, never a re-derived mapping).
Every behavior of the plan's Task 3 is pinned here:

- **row derivation** — one row per COMPLETED run record: ``model`` (the
  alias display name), ``base_model`` (alias-suffix-stripped join key),
  ``method`` (+lora/+ia3/+probe suffix first, else the record ``peft``
  field, else none), ``wall_hours`` (finished_at minus started_at,
  WALL-CLOCK), ``total_flos`` (record metrics, hard-required),
  ``trainable_params_pct`` (record metrics; null + disclosed note when
  the record predates the 06-02 persistence), ``score`` (the task's
  primary metric resolved through the exporter surface — the synthetic
  registry declares legacy ``F1`` so the legacy translation is exercised),
  and ``score_delta`` (method score minus the none-method mean for the
  same (base_model, task); null + disclosed when no counterpart run
  exists — the method=none rows are the reference, not delta-bearing);
- **missing-FLOPs abort** — a completed record without ``total_flos``
  aborts loudly NAMING THE RECORD PATH (mirroring the exporter's
  ``_collect_cell_values`` hard error);
- **determinism** — the same tree emits byte-identical JSON and CSV
  across two runs (sorted iteration, sort_keys, no clock);
- **schema** — both the generator's emission and the committed
  ``tests/fixtures/frontier/frontier_sample.json`` validate against
  ``schemas/frontier.json``;
- **chain-produced fixture** — the committed fixture equals the
  generator's emission over the canonical synthetic tree, byte for byte
  (never hand-authored; the regeneration path is the test itself);
- **publication gate** — no ``dnallm-mark/data/frontier.json`` exists and
  the generator's default output dir is a SIBLING of the input root (the
  resolved-OQ gate: the artifact lands with real post-E2' numbers only);
- **probe forward-compatibility** — a ``+probe`` alias derives
  method=probe with the stripped base (06-05's lane);
- **--data-md appendix** — the optional markdown emission renders the
  same rows as a generated table (implemented + tested, NOT wired).

The runner is stdlib + jsonschema only; no torch/dnallm import anywhere.

See also:
    ``script/build_frontier.py`` — the generator under test.
    ``script/export_runs.py`` — the imported reader/metric authorities.
    ``tests/test_export_runs.py`` — the fixture-tree builder pattern this
    module adapts locally.
"""

import json
from pathlib import Path

import build_frontier  # conftest puts script/ on sys.path
import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "frontier.json"
FIXTURE_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "frontier" / "frontier_sample.json"
)
COMMITTED_FRONTIER = REPO_ROOT / "dnallm-mark" / "data" / "frontier.json"

# The synthetic registry slice: metric "F1" exercises the LEGACY
# dataset-metric translation (F1 -> f1) on the score path.
DATASETS_INFO = {
    "FakeDS__task": {
        "Category": "Plants",
        "Dataset_name": "FakeDS__task",
        "Dataset_path": "datasets/FakeDS/task",
        "Dev": 100, "Test": 200, "Train": 300, "Index": 1,
        "labels": 2, "length": 500, "metric": "F1", "type": "binary",
    },
}


def _write_datasets_info(tmp_path):
    path = tmp_path / "datasets_info.json"
    path.write_text(json.dumps(DATASETS_INFO), encoding="utf-8")
    return path


def _write_record(root, model, task, seed, metrics, *, peft="none",
                  started="2026-10-10T00:00:00+00:00",
                  finished="2026-10-10T01:30:00+00:00",
                  status="completed"):
    """Materialize one {root}/{model}/{task}/seed_{seed}/run_record.json
    cell (adapted locally from tests/test_export_runs.py's builder)."""
    seed_dir = root / model / task / f"seed_{seed}"
    seed_dir.mkdir(parents=True)
    record = {
        "model": model,
        "task": task,
        "seed": seed,
        "peft": peft,
        "status": status,
        "output_dir": str(seed_dir),
        "metrics": metrics,
        "vram_probe": {
            "gpu_mem_total": None, "init_max_mem": None,
            "batch_size": None, "gradient_accumulation_steps": None,
        },
        "git_commit": "testshash",
        "started_at": started,
        "finished_at": finished,
        "error": None,
    }
    (seed_dir / "run_record.json").write_text(
        json.dumps(record), encoding="utf-8")
    return seed_dir


def _full_metrics(f1, *, flos=1.0e15, pct=100.0, runtime=100.0):
    """A post-06-02-persistence metrics payload (suite-native keys)."""
    return {
        "eval_f1": f1,
        "eval_loss": 0.3,
        "total_flos": flos,
        "train_runtime": runtime,
        "trainable_params": 89493508,
        "total_params": 89493508,
        "trainable_params_pct": pct,
    }


def _canonical_tree(root):
    """The committed fixture's synthetic tree: base + alias cells for one
    model pair, a pre-persistence base record, a missing-counterpart
    alias, legacy-metric resolution — the fixture is the generator's
    emission over exactly this shape (chain-produced)."""
    root.mkdir(parents=True)
    # model-a: the none-method reference (3 seeds, mean f1 0.92).
    _write_record(root, "model-a", "FakeDS__task", 42, _full_metrics(0.90))
    _write_record(root, "model-a", "FakeDS__task", 43, _full_metrics(0.92))
    _write_record(root, "model-a", "FakeDS__task", 44, _full_metrics(0.94))
    # model-a+lora: adapter cells (2 seeds) with persisted params.
    def _lora_metrics(f1):
        return {
            "eval_f1": f1,
            "eval_loss": 0.35,
            "total_flos": 2.0e13,
            "train_runtime": 60.0,
            "trainable_params": 296450,
            "total_params": 89493508,
            "trainable_params_pct": 0.331253,
        }

    _write_record(
        root, "model-a+lora", "FakeDS__task", 42, _lora_metrics(0.89),
        peft="lora", started="2026-10-10T00:00:00+00:00",
        finished="2026-10-10T00:45:00+00:00")
    _write_record(
        root, "model-a+lora", "FakeDS__task", 43, _lora_metrics(0.91),
        peft="lora", started="2026-10-10T00:00:00+00:00",
        finished="2026-10-10T00:45:00+00:00")
    # model-b: a PRE-persistence record (no trainable_params keys).
    _write_record(
        root, "model-b", "FakeDS__task", 42,
        {"eval_f1": 0.75, "eval_loss": 0.4, "total_flos": 5.0e14,
         "train_runtime": 90.0},
        started="2026-10-10T00:00:00+00:00",
        finished="2026-10-10T02:00:00+00:00")
    # model-c+lora: an alias with NO base counterpart run.
    _write_record(
        root, "model-c+lora", "FakeDS__task", 42,
        {**_full_metrics(0.60, flos=3.0e13, pct=0.4)},
        peft="lora", started="2026-10-10T00:00:00+00:00",
        finished="2026-10-10T00:30:00+00:00")
    return root


def _run_generator(tmp_path, tree_builder=_canonical_tree):
    """Run the generator over a synthetic tree; return (rows, out_dir)."""
    root = tree_builder(tmp_path / "finetuned")
    datasets_path = _write_datasets_info(tmp_path)
    out_dir = tmp_path / "frontier-out"
    build_frontier.write_frontier(root, datasets_path, out_dir)
    rows = json.loads(
        (out_dir / "frontier.json").read_text(encoding="utf-8"))["rows"]
    return rows, out_dir, root


def _row(rows, model, seed):
    matched = [r for r in rows if r["model"] == model and r["seed"] == seed]
    assert len(matched) == 1, f"expected exactly one {model}/{seed} row"
    return matched[0]


# =====================================================================
# Row derivation
# =====================================================================

def test_rows_derive_every_column_from_the_record_contracts(tmp_path):
    """One row per COMPLETED record; every column traces to the record
    contracts: alias display/base split, method derivation, wall_hours
    from the timestamps, total_flos from metrics, pct from the 06-02
    persistence (null + disclosed for pre-persistence records), score via
    the exporter's legacy-metric resolution (F1 -> eval_f1), score_delta
    against the none-method mean (null + disclosed with no counterpart;
    none rows are the reference)."""
    rows, _out, _root = _run_generator(tmp_path)
    assert [r["model"] for r in rows] == [
        "model-a", "model-a", "model-a",
        "model-a+lora", "model-a+lora",
        "model-b",
        "model-c+lora",
    ], "rows iterate model dirs then seeds in sorted order"

    base_42 = _row(rows, "model-a", 42)
    assert base_42["base_model"] == "model-a"
    assert base_42["method"] == "none"
    assert base_42["score"] == 0.90, (
        "score must resolve the task's primary metric through the exporter "
        "surface: registry 'F1' -> slot 'f1' -> record key eval_f1"
    )
    assert base_42["wall_hours"] == 1.5
    assert base_42["total_flos"] == 1.0e15
    assert base_42["trainable_params_pct"] == 100.0
    assert base_42["score_delta"] is None
    assert any("reference" in note for note in base_42["notes"]), (
        "a method=none row must disclose that it IS the delta reference"
    )

    lora_42 = _row(rows, "model-a+lora", 42)
    assert lora_42["base_model"] == "model-a", (
        "base_model is the alias-suffix-stripped join key"
    )
    assert lora_42["method"] == "lora"
    assert lora_42["score"] == 0.89
    assert lora_42["trainable_params_pct"] == 0.331253
    assert lora_42["wall_hours"] == 0.75
    assert lora_42["score_delta"] == pytest.approx(0.89 - 0.92), (
        "score_delta = method score minus the none-method MEAN for the "
        "same (base_model, task) — here mean(0.90, 0.92, 0.94) = 0.92"
    )
    assert lora_42["notes"] == []

    pre = _row(rows, "model-b", 42)
    assert pre["trainable_params_pct"] is None
    assert any("predates" in note for note in pre["notes"]), (
        "a record without the persistence keys must carry a disclosed "
        "null — skip-as-data, never a silent drop"
    )
    assert pre["wall_hours"] == 2.0

    orphan = _row(rows, "model-c+lora", 42)
    assert orphan["base_model"] == "model-c"
    assert orphan["score_delta"] is None
    assert any("counterpart" in note for note in orphan["notes"]), (
        "an alias with no completed none-method base run must disclose the "
        "missing counterpart"
    )


def test_missing_total_flos_aborts_naming_the_record(tmp_path):
    """A completed record missing total_flos aborts loudly naming the
    record path (mirroring export_runs._collect_cell_values — FLOPs is a
    hard-required bare number; emitting 0 or '' would falsify)."""
    root = tmp_path / "finetuned"
    root.mkdir()
    _write_record(
        root, "model-a", "FakeDS__task", 42,
        {"eval_f1": 0.9, "eval_loss": 0.3})  # no total_flos
    with pytest.raises(RuntimeError) as excinfo:
        build_frontier.build_frontier_rows(root, DATASETS_INFO)
    message = str(excinfo.value)
    assert "total_flos" in message
    expected_path = (
        root / "model-a" / "FakeDS__task" / "seed_42" / "run_record.json")
    assert str(expected_path) in message, (
        "the abort must NAME the record path so the operator can fix the "
        f"cell: {message}"
    )


def test_probe_alias_is_forward_compatible_method(tmp_path):
    """A +probe alias (06-05's frozen-probe lane) derives method=probe
    with the stripped base; a NON-aliased dir whose record carries a peft
    field derives the method from the record field."""
    rows, _out, _root = _run_generator(tmp_path, tree_builder=_probe_tree)
    probe = _row(rows, "model-d+probe", 42)
    assert probe["method"] == "probe"
    assert probe["base_model"] == "model-d"
    from_record = _row(rows, "model-e", 42)
    assert from_record["method"] == "lora", (
        "without an alias suffix, the record peft field is the method "
        "source (suffix first, record field second, none last)"
    )
    assert from_record["base_model"] == "model-e"


def _probe_tree(parent):
    """Two method-derivation edge cells: a +probe alias dir whose record
    says peft=none (suffix wins), and a base-name dir whose record carries
    peft=lora (record field wins when no suffix)."""
    root = parent / "finetuned"
    root.mkdir(parents=True)
    _write_record(
        root, "model-d+probe", "FakeDS__task", 42,
        _full_metrics(0.8), peft="none")
    _write_record(
        root, "model-e", "FakeDS__task", 42,
        _full_metrics(0.7), peft="lora")
    return root


# =====================================================================
# Determinism + dual emission
# =====================================================================

def test_emission_is_byte_deterministic(tmp_path):
    """The same synthetic tree emits byte-identical frontier.json AND
    frontier.csv across two runs (sorted iteration, sort_keys, no clock)."""
    datasets_path = _write_datasets_info(tmp_path)
    outputs = []
    for run in range(2):
        root = _canonical_tree(tmp_path / f"tree-{run}")
        out_dir = tmp_path / f"frontier-out-{run}"
        build_frontier.write_frontier(root, datasets_path, out_dir)
        outputs.append((
            (out_dir / "frontier.json").read_bytes(),
            (out_dir / "frontier.csv").read_bytes(),
        ))
    assert outputs[0][0] == outputs[1][0], (
        "two runs over the same tree must produce byte-identical JSON"
    )
    assert outputs[0][1] == outputs[1][1], (
        "two runs over the same tree must produce byte-identical CSV "
        "(stable column order)"
    )


def test_csv_column_order_is_stable(tmp_path):
    """The CSV carries the fixed column order and one line per row."""
    rows, out_dir, _root = _run_generator(tmp_path)
    lines = (out_dir / "frontier.csv").read_text(encoding="utf-8").splitlines()
    assert lines[0] == (
        "model,base_model,task,seed,method,wall_hours,total_flos,"
        "trainable_params_pct,score,score_delta,notes"
    )
    assert len(lines) == len(rows) + 1, "header + one line per row"


# =====================================================================
# Schema validation + the committed fixture
# =====================================================================

def test_generator_emission_validates_against_the_schema(tmp_path):
    _rows, out_dir, _root = _run_generator(tmp_path)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    payload = json.loads(
        (out_dir / "frontier.json").read_text(encoding="utf-8"))
    errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)
    assert not errors, f"schema violations: {[e.message for e in errors]}"


def test_committed_fixture_validates_against_the_schema():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)
    assert not errors, f"schema violations: {[e.message for e in errors]}"


def test_committed_fixture_is_generator_produced(tmp_path):
    """The committed fixture equals the generator's emission over the
    canonical synthetic tree, BYTE for BYTE — chain-produced only, never
    hand-authored (this test IS the regeneration path: change the tree or
    the generator, and this fails until the fixture is re-run)."""
    datasets_path = _write_datasets_info(tmp_path)
    root = _canonical_tree(tmp_path / "finetuned")
    out_dir = tmp_path / "frontier-out"
    build_frontier.write_frontier(root, datasets_path, out_dir)
    assert (out_dir / "frontier.json").read_bytes() == (
        FIXTURE_PATH.read_bytes()
    ), (
        "the committed fixture must be the generator's output over the "
        "canonical tree — regenerate with the generator, never hand-edit"
    )


def test_no_committed_frontier_artifact_exists():
    """The resolved-OQ publication gate: no dnallm-mark/data/frontier.json
    is committed and no DATA.md link exists — the artifact + site link
    land with real post-E2' numbers only."""
    assert not COMMITTED_FRONTIER.exists(), (
        "dnallm-mark/data/frontier.json must NOT exist until real "
        "post-E2' numbers arrive (resolved research OQ 1)"
    )
    data_md = REPO_ROOT / "DATA.md"
    assert "frontier" not in data_md.read_text(encoding="utf-8").lower(), (
        "DATA.md must carry no frontier link in this plan"
    )


def test_default_output_dir_is_a_sibling_of_the_input_root(tmp_path):
    """The CLI's default output dir derives {input-root}/frontier — NEVER
    dnallm-mark/data (committed data moves only in inventoried migration
    commits; the artifact is gated on real numbers)."""
    parser_default = build_frontier._argument_defaults()
    assert parser_default["output_dir"] is None, (
        "--output-dir must default to None (derived as a sibling of the "
        "input root) — a dnallm-mark/data default would publish early"
    )


# =====================================================================
# --data-md appendix (implemented + tested, NOT wired)
# =====================================================================

def test_data_md_renders_the_same_rows_as_a_table(tmp_path):
    """--data-md emits a generated markdown appendix table over the SAME
    rows, stamped as generated (the DATA.md appendix convention), and is
    byte-deterministic."""
    datasets_path = _write_datasets_info(tmp_path)
    root = _canonical_tree(tmp_path / "finetuned")
    out_dir = tmp_path / "frontier-out"
    md_path = tmp_path / "frontier_appendix.md"
    build_frontier.write_frontier(root, datasets_path, out_dir, data_md=md_path)
    text = md_path.read_text(encoding="utf-8")
    assert "GENERATED by" in text and "do not edit" in text.lower(), (
        "the appendix must carry the generated-file stamp"
    )
    assert "| model |" in text, "the markdown table header must exist"
    assert text.count("\n| model-a ") >= 1
    rows = json.loads(
        (out_dir / "frontier.json").read_text(encoding="utf-8"))["rows"]
    assert text.count("\n| ") == len(rows) + 1, (
        "one markdown table line per frontier row plus the header"
    )
    # Determinism: a second run over the same tree is byte-identical.
    md_second = tmp_path / "frontier_appendix2.md"
    root2 = _canonical_tree(tmp_path / "finetuned2")
    out2 = tmp_path / "frontier-out2"
    build_frontier.write_frontier(root2, datasets_path, out2, data_md=md_second)
    assert md_second.read_bytes() == md_path.read_bytes()


# =====================================================================
# Import discipline (CPU-safe)
# =====================================================================

def test_module_imports_the_exporter_authorities_never_rewalks():
    """build_frontier imports load_run_records + the metric-resolution
    helpers from export_runs (the single reader + single metric authority)
    — the tree walk and the metric mapping are never re-derived."""
    src = (REPO_ROOT / "script" / "build_frontier.py").read_text(
        encoding="utf-8")
    assert "from export_runs import" in src
    for name in ("load_run_records", "resolve_dataset_metric",
                 "resolve_metric_key"):
        assert name in src, (
            f"{name} must be imported from export_runs — never re-derived"
        )
    assert "iterdir" not in src, (
        "the module must not walk the tree itself — load_run_records is "
        "the single reader authority"
    )
