"""
Single-source registry contract (D-10): JSON is the only registry form.

The dev branch arrived with dual registries — operational ``.txt`` TSVs
(what ``run_finetune.py`` read via ``pd.read_table``) plus ``.json`` card
registries — drifting by 24 model names. Decision D-10 (2026-10-09)
unified them into the JSON registries as the single source of truth;
03-02 merged the tabular operational fields in via
``script/convert_registry.py`` and retired both ``.txt`` files.

CSV is the sanctioned ON-DEMAND PROJECTION of a registry
(``script/convert_registry.py --to-csv``) for spreadsheet editing and
exchange — it is regenerable at any time and is NEVER committed: a
tracked ``pipeline/*.csv`` or ``pipeline/*.txt`` registry would reintroduce
the dual-source drift this contract exists to prevent.

What is pinned here (the unification arithmetic, maintainer live-verified
on the real dev data before this test was written):

- **models** — exactly 62 entries: 38 shared (card + tabular operational),
  18 tabular-only (operational fields, card fields deliberately absent
  until Phase 4 fills them per D-10 — PlantHelixSeek was the 19th such
  name until 03-03 filled its card from the D-09 ModelScope model card,
  taking the registry to 45 card-bearing entries; the 17 remaining absent
  names are enumerated below so the gap is explicit, never silent), and
  6 json-only (card + derived operational four). Every entry carries the
  operational four (Model_path, Model_size, Tokenizer, Mean_token_length)
  and ``key == Model_name``.
- **datasets** — exactly 50 entries, every one operationally complete
  (Index, Dataset_path, Train, Test, Dev, type, labels, length, metric,
  Category — Index and Category arrived only with the 03-02 merge),
  ``key == Dataset_name``, and zero bare ``gene_exp.*`` keys (the 3 legacy
  bare names were renamed to the ``Source__task`` form during unification).

See also:
    - ``script/convert_registry.py`` — the only sanctioned conversion path
      (and its ``--to-csv`` projection).
    - ``tests/test_convert_registry.py`` — the converter behavior tests.
    - ``pipeline/run_finetune.py`` — the JSON read site this contract feeds.
"""

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS_INFO = REPO_ROOT / "pipeline" / "models_info.json"
DATASETS_INFO = REPO_ROOT / "pipeline" / "datasets_info.json"

# The models-registry operational four: every unified entry carries these.
OPERATIONAL_FOUR = ("Model_path", "Model_size", "Tokenizer", "Mean_token_length")
# The 11 model-card keys the dev .json registry carried on all 44 entries
# (45 since 03-03 filled PlantHelixSeek's card per D-09).
CARD_KEYS = frozenset({
    "architecture", "context_len (bp)", "huggingface", "mean_token_len",
    "modelscope", "name", "series", "size (M)", "species", "tokenizer",
    "type",
})
# The 17 remaining txt-only model names (operational fields, no card yet —
# Phase 4 fills them per D-10; PlantHelixSeek left this set in 03-03 when
# D-09 filled its card from the ModelScope model card).
TXT_ONLY_MODELS = frozenset({
    "Chaoba", "Chaoba_all_species", "Chaoba_denseMamba", "FungiHelixSeek",
    "GENA-LM-yeast", "PlantCAD2-Large", "PlantCaduceus_l24", "PlantGFM",
    "Shorkie_LM", "SpeciesLM-fungi-downstream-k1",
    "SpeciesLM-fungi-upstream-k1", "denseSSM_plant_genome", "mamba2_370M",
    "mamba2_plant_genome", "plant-dnamamba-singlebase", "prokbert", "space",
})
# The datasets-registry operational columns: every unified entry carries
# these (Index and Category arrived with the 03-02 tabular merge).
DATASET_OPERATIONAL = (
    "Index", "Dataset_path", "Train", "Test", "Dev", "type", "labels",
    "length", "metric", "Category",
)


def test_no_tabular_registry_tracked():
    """Single source of truth: no .txt or .csv registry under pipeline/.

    CSV is the sanctioned on-demand projection via
    ``script/convert_registry.py --to-csv`` and is never committed; a
    tracked tabular registry would reintroduce the D-10 dual-source drift.
    """
    tracked = subprocess.run(
        ["git", "ls-files", "--", "pipeline/*.txt", "pipeline/*.csv"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert tracked == "", (
        f"tabular registry files are tracked under pipeline/ (D-10 "
        f"violation): {tracked}"
    )


def test_models_registry_single_source():
    """models_info.json: 62 entries, operational four everywhere,
    key == Model_name, the 11-key card on exactly the 45 card-bearing
    entries, card-absent set == the enumerated 17 txt-only names."""
    registry = json.loads(MODELS_INFO.read_text(encoding="utf-8"))
    assert len(registry) == 62, (
        f"expected exactly 62 unified model entries (38 shared + 18 "
        f"txt-only + 6 json-only, maintainer live-verified), got {len(registry)}"
    )
    for key, entry in registry.items():
        missing = [c for c in OPERATIONAL_FOUR if c not in entry]
        assert not missing, f"{key}: missing operational fields {missing}"
        assert key == entry["Model_name"], (
            f"{key}: key != Model_name ({entry['Model_name']!r})"
        )
    card_bearing = {k for k, e in registry.items() if CARD_KEYS <= set(e)}
    card_absent = set(registry) - card_bearing
    assert len(card_bearing) == 45, (
        f"expected the 11-key card on exactly 45 entries (44 at unification "
        f"+ PlantHelixSeek filled by 03-03/D-09), got {len(card_bearing)}"
    )
    assert card_absent == TXT_ONLY_MODELS, (
        "card-absent set drifted from the enumerated 17 remaining txt-only "
        f"names (extra: {sorted(card_absent - TXT_ONLY_MODELS)}, missing: "
        f"{sorted(TXT_ONLY_MODELS - card_absent)}) — update the enumeration "
        "deliberately (Phase 4 fills cards per D-10)"
    )


def test_datasets_registry_single_source():
    """datasets_info.json: 50 operationally-complete entries,
    key == Dataset_name, zero bare gene_exp keys."""
    registry = json.loads(DATASETS_INFO.read_text(encoding="utf-8"))
    assert len(registry) == 50, (
        f"expected exactly 50 dataset entries, got {len(registry)}"
    )
    for key, entry in registry.items():
        missing = [c for c in DATASET_OPERATIONAL if c not in entry]
        assert not missing, f"{key}: missing operational columns {missing}"
        assert key == entry["Dataset_name"], (
            f"{key}: key != Dataset_name ({entry['Dataset_name']!r})"
        )
    bare = [k for k in registry if k.startswith("gene_exp.")]
    assert not bare, (
        f"bare gene_exp keys survived unification (must be the "
        f"plant-genomic-benchmark__gene_exp.* form): {bare}"
    )
