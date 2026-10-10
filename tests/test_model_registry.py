"""
Unified models registry integrity (03-03, PIPE-03/AUD-05 groundwork).

03-02's D-10 unification landed a single-source 62-entry JSON registry;
03-03 filled PlantHelixSeek's 11-key model card from the maintainer-
provided ModelScope card (D-09: modelscope.cn/models/zhangtaolab/
PlantHelixSeek), taking the registry from 44 to 45 card-bearing entries
while the 62-entry total and every operational field stayed unchanged.

What is pinned here (shape/completeness/count, complementing
``tests/test_registry_unification.py``'s unification-arithmetic pins):

- the registry parses, holds exactly 62 entries, and ``key == Model_name``
  on every entry (the dict read site in ``run_finetune.py`` depends on it);
- exactly one entry is keyed ``PlantHelixSeek`` and its key set is EXACTLY
  the operational four + ``Model_name`` + the 11-key card (16 keys — no
  extra, no missing);
- every PlantHelixSeek card field is non-empty after str-strip (no empty
  strings, no nulls — AUD-05 groundwork requires complete metadata);
- the numeric trio (size (M), mean_token_len, context_len (bp)) is
  int/float, matching the CrossDNA card convention;
- ALL 62 entries carry the complete 11-key card (45 through 03-03; the
  final 17 filled by 04-04 carryover Q2 — 62/62 complete, the state the
  REV-03 exporter's modelCard join depends on).

Card-value provenance (each field traces to the D-09 card or the entry's
operational priors from the 03-02 ingest): 470M params -> size (M) 470 ==
Model_size "470M"; single-nucleotide resolution -> tokenizer "singlebase"
== Tokenizer, mean_token_len 1 == Mean_token_length; "Max context:
8,192 bp" -> context_len (bp) 8192; "pretrained with masked language
modeling (MLM)" -> type "MLM"; "DNA Language Model for Plants" -> species
"plants"; Model Details architecture row -> "HelixSeek (Transformer +
KDA + MLA + MoE)"; the family name -> series/name "PlantHelixSeek";
from_pretrained("zhangtaolab/PlantHelixSeek") -> huggingface; the D-09
page itself -> modelscope.

See also:
    - ``tests/test_registry_unification.py`` — the single-source contract
      (62/50 counts, operational completeness, 62/62 card completeness).
    - ``script/convert_registry.py`` — the only sanctioned registry
      conversion path.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS_INFO = REPO_ROOT / "pipeline" / "models_info.json"

# Same constants as tests/test_registry_unification.py (duplicated
# deliberately: each suite pins its own copy of the contract vocabulary).
OPERATIONAL_FOUR = frozenset({
    "Model_path", "Model_size", "Tokenizer", "Mean_token_length",
})
CARD_KEYS = frozenset({
    "architecture", "context_len (bp)", "huggingface", "mean_token_len",
    "modelscope", "name", "series", "size (M)", "species", "tokenizer",
    "type",
})
NAME_FIELD = "Model_name"
NUMERIC_TRIO = ("size (M)", "mean_token_len", "context_len (bp)")
# 16 = operational four + Model_name + the 11-key card. (The plan's "15
# keys" omitted Model_name, which the key == Model_name contract requires
# on every entry.)
PLANTHELIXSEEK_EXPECTED_KEYS = OPERATIONAL_FOUR | CARD_KEYS | {NAME_FIELD}
CARD_BEARING_COUNT = 62  # 44 at unification + PlantHelixSeek (03-03/D-09) + 17 (04-04 Q2)


def _load_registry():
    return json.loads(MODELS_INFO.read_text(encoding="utf-8"))


def test_registry_parses_with_62_entries_and_name_key_contract():
    """The registry parses, holds exactly 62 entries, and every entry's
    key equals its Model_name field (the run_finetune.py dict read site
    iterates .items() and addresses row["Model_name"])."""
    registry = _load_registry()
    assert len(registry) == 62, (
        f"expected exactly 62 model entries, got {len(registry)}"
    )
    for key, entry in registry.items():
        assert key == entry.get(NAME_FIELD), (
            f"{key}: key != Model_name ({entry.get(NAME_FIELD)!r})"
        )


def test_planthelixseek_entry_shape_is_exactly_ops_plus_card():
    """Exactly one PlantHelixSeek entry exists and its key set is exactly
    operational four + Model_name + the 11-key card (16 keys, no extra,
    no missing)."""
    registry = _load_registry()
    matches = [k for k in registry if k == "PlantHelixSeek"]
    assert matches == ["PlantHelixSeek"], (
        f"expected exactly one PlantHelixSeek key, got {matches}"
    )
    entry = registry["PlantHelixSeek"]
    assert set(entry) == PLANTHELIXSEEK_EXPECTED_KEYS, (
        f"PlantHelixSeek key set mismatch (extra: "
        f"{sorted(set(entry) - PLANTHELIXSEEK_EXPECTED_KEYS)}, missing: "
        f"{sorted(PLANTHELIXSEEK_EXPECTED_KEYS - set(entry))})"
    )


def test_planthelixseek_card_fields_complete_and_numeric_trio_numeric():
    """Every card field is non-empty after str-strip (no empty strings,
    no nulls — AUD-05 groundwork requires complete metadata) and the
    numeric trio is int/float (CrossDNA card convention)."""
    entry = _load_registry()["PlantHelixSeek"]
    for field in sorted(CARD_KEYS):
        assert field in entry, f"missing card field {field!r}"
        value = entry[field]
        assert value is not None, f"{field} is null"
        assert str(value).strip() != "", f"{field} is empty after strip"
    for field in NUMERIC_TRIO:
        value = entry[field]
        assert isinstance(value, (int, float)) and not isinstance(value, bool), (
            f"{field} must be int/float, got {type(value).__name__} "
            f"({value!r})"
        )


def test_planthelixseek_card_agrees_with_operational_priors():
    """The card cross-checks against the operational four carried in by
    the 03-02 D-10 ingest (size, tokenizer, token length) — the D-09 card
    and the operational registry describe the same model."""
    entry = _load_registry()["PlantHelixSeek"]
    assert entry["size (M)"] == 470 and entry["Model_size"] == "470M"
    assert entry["tokenizer"] == entry["Tokenizer"] == "singlebase"
    assert entry["mean_token_len"] == entry["Mean_token_length"] == 1


def test_every_entry_carries_the_complete_card():
    """ALL 62 entries carry the complete 11-key card (44 at the 03-02
    unification + PlantHelixSeek by 03-03/D-09 + the final 17 by 04-04
    carryover Q2) — the exporter's modelCard join is total over the
    registry."""
    registry = _load_registry()
    complete = [k for k, e in registry.items() if CARD_KEYS <= set(e)]
    assert len(complete) == CARD_BEARING_COUNT, (
        f"expected {CARD_BEARING_COUNT} complete-card entries, got "
        f"{len(complete)} (absent: {sorted(set(registry) - set(complete))})"
    )
    assert "PlantHelixSeek" in complete
