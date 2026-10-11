"""
Tier-1 service tests for ``tui/services/registries.py`` (Phase 8; 08-03
tracer, 08-04 expansion).

The tui → pipeline seam proof: the first services module imports the
REAL pipeline registry loader and returns the REAL committed registry
counts — no fakes on this path (the plan's acceptance criterion). Pinned
decisions:

- one-directional seam: the service imports ``registry_loader`` as a
  top-level module; the parent ``tests/conftest.py`` supplies the
  ``pipeline/`` sys.path root for this lane (``tests/tui/conftest.py``
  adds the repo root for the package-qualified ``tui`` import).
- machine independence (the ``tests/test_registry_loader.py``
  ``pin_custom_dir`` discipline, its Pitfall 3): the custom overlay dir
  is pinned to a fresh empty tmp dir, so the assertions pin the
  COMMITTED official registries — 62 models / 50 datasets — regardless
  of any local ``~/.config/dnallmmark/custom_{models,datasets}.json``
  a machine may carry. The overlay MERGE semantics are pinned by
  ``tests/test_registry_loader.py``; these tests pin the seam plus the
  real data.
- 08-04 entry view (SEL-04/D-08): canonical entry keys {key, type,
  species, size_m, card} / {key, category, type, metric, card}; the
  model-card casing twins resolved once via the service's canonical
  constants; presence_for returns PURE data (exact integer rows, no
  formatting — the 08-07 screen formats); n_audit reads go through
  the tolerant artifact_loader None sentinel with the repo-root path
  resolved from the module's own location, never CWD.

See also:
    ``tui/services/registries.py`` — the service under test.
    ``tests/test_registry_loader.py`` — the overlay merge contract.
"""

import re
from pathlib import Path

import registry_loader  # conftest puts pipeline/ on sys.path

from tui.services import registries as registries_module
from tui.services.registries import (
    MODEL_CARD_MEAN_TOKEN_LEN_FIELD,
    MODEL_CARD_SIZE_FIELD,
    MODEL_CARD_TOKENIZER_FIELD,
    PRESENCE_MISSING,
    PRESENCE_PRESENT,
    PRESENCE_UNAVAILABLE,
    PRESENCE_UNKNOWN,
    load_dataset_entries,
    load_model_entries,
    load_n_audit,
    load_registry_counts,
    presence_for,
)


def test_load_registry_counts_returns_committed_registry_counts(
        monkeypatch, tmp_path):
    """The seam returns the real committed counts: (62, 50).

    ``load_registry_counts()`` loads through
    ``pipeline/registry_loader`` (the overlay-merged view); with the
    custom overlay pinned empty, the merged view IS the committed
    official registry.
    """
    empty_overlay = tmp_path / "custom"
    empty_overlay.mkdir()
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(empty_overlay))

    assert load_registry_counts() == (62, 50)


# ===== Entry view (08-04, SEL-04) =====


def test_load_model_entries_projects_the_canonical_keys(monkeypatch,
                                                        tmp_path):
    """62 entries, each EXACTLY {key, type, species, size_m, card}."""
    empty_overlay = tmp_path / "custom"
    empty_overlay.mkdir()
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(empty_overlay))
    entries = load_model_entries()
    assert len(entries) == 62
    for entry in entries:
        assert set(entry) == {"key", "type", "species", "size_m", "card"}
        assert isinstance(entry["key"], str)
        assert isinstance(entry["type"], str)
        assert isinstance(entry["species"], str)
        assert isinstance(entry["size_m"], float)
        assert isinstance(entry["card"], dict)


def test_load_dataset_entries_projects_the_canonical_keys(monkeypatch,
                                                          tmp_path):
    """50 entries, each EXACTLY {key, category, type, metric, card}."""
    empty_overlay = tmp_path / "custom"
    empty_overlay.mkdir()
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(empty_overlay))
    entries = load_dataset_entries()
    assert len(entries) == 50
    for entry in entries:
        assert set(entry) == {"key", "category", "type", "metric", "card"}
        assert isinstance(entry["category"], str)
        assert isinstance(entry["type"], str)
        assert isinstance(entry["metric"], str)


def test_entry_keys_are_the_registry_row_keys(monkeypatch, tmp_path):
    """Entry keys == the registry dict keys (the stable row_key vocab)."""
    empty_overlay = tmp_path / "custom"
    empty_overlay.mkdir()
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(empty_overlay))
    assert {e["key"] for e in load_model_entries()} == set(
        registry_loader.load_models_registry()
    )
    assert {e["key"] for e in load_dataset_entries()} == set(
        registry_loader.load_datasets_registry()
    )


def test_entry_lists_and_counts_stay_consistent(monkeypatch, tmp_path):
    """load_registry_counts is implemented over the entry loaders."""
    empty_overlay = tmp_path / "custom"
    empty_overlay.mkdir()
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(empty_overlay))
    counts = load_registry_counts()
    assert len(load_model_entries()) == counts.models
    assert len(load_dataset_entries()) == counts.datasets


def test_model_entries_carry_raw_values_with_empty_string_absents():
    """Filter axes hold the RAW registry values; absent -> "" not None."""
    entries = {e["key"]: e for e in load_model_entries()}
    # Chaoba's committed card carries empty type/species — the repo
    # data convention: missing values are "", never None/0.
    assert entries["Chaoba"]["type"] == ""
    assert entries["Chaoba"]["species"] == ""
    assert "" in {e["type"] for e in entries.values()}
    # a populated card passes through verbatim
    assert entries["Chaoba"]["card"]["Model_size"] == "400M"


def test_dataset_entries_carry_raw_values():
    """Dataset filter axes pass the committed card values through."""
    entries = {e["key"]: e for e in load_dataset_entries()}
    bend = entries["BEND__CpG_methylation"]
    assert bend["category"] == "Animals"
    assert bend["type"] == "multilabel"
    assert bend["metric"] == "AUPRC"


def test_size_m_is_the_numeric_card_field_as_float():
    """size_m == float(card["size (M)"]) — the numeric field, not the
    "400M" string twin (the projection choice is load-bearing)."""
    for entry in load_model_entries():
        assert entry["size_m"] == float(entry["card"]["size (M)"])


def test_model_card_casing_twins_have_one_canonical_reading():
    """The casing twins are resolved ONCE, by the service's constants.

    The committed cards carry duplicate-casing twins whose values
    genuinely diverge (agro-nucleotide-transformer-1b: Tokenizer '6mer'
    vs tokenizer '6-mer'; prokbert-mini: Mean_token_length 6 vs
    mean_token_len 1) — every consumer must read one canonical field.
    """
    assert MODEL_CARD_SIZE_FIELD == "size (M)"
    assert MODEL_CARD_TOKENIZER_FIELD == "Tokenizer"
    assert MODEL_CARD_MEAN_TOKEN_LEN_FIELD == "Mean_token_length"


# ===== n_audit presence (SEL-04, D-08) =====


def _synthetic_audit_tasks():
    """A synthetic tasks mapping covering every presence shape."""
    return {
        "T__present": {
            "missing": False,
            "splits": {
                "train": {"rows": 743095},
                "dev": {"rows": 109717},
                "test": {"rows": 106227},
            },
            "unified_eval_n": 106224,
        },
        "T__missing": {
            "missing": True,
            "splits": None,
            "unified_eval_n": None,
        },
    }


def test_presence_present_returns_exact_integer_rows():
    """missing=false -> present with the exact (train, dev, test) ints."""
    presence = presence_for("T__present", _synthetic_audit_tasks())
    assert presence.status == PRESENCE_PRESENT
    assert presence.rows == (743095, 109717, 106227)
    for count in presence.rows:
        assert isinstance(count, int)
        assert not isinstance(count, bool)


def test_presence_missing_flag_beats_any_counts():
    """missing=true -> missing with rows None, regardless of counts."""
    tasks = {
        "T": {
            "missing": True,
            "splits": {
                "train": {"rows": 5},
                "dev": {"rows": 5},
                "test": {"rows": 5},
            },
        }
    }
    presence = presence_for("T", tasks)
    assert presence.status == PRESENCE_MISSING
    assert presence.rows is None


def test_presence_unknown_for_key_absent_from_audit():
    """Registry/audit drift (either direction) -> unknown, no exception."""
    presence = presence_for("registry-only-task", _synthetic_audit_tasks())
    assert presence.status == PRESENCE_UNKNOWN
    assert presence.rows is None


def test_presence_unavailable_when_audit_is_none():
    """Absent/unreadable n_audit -> column-unavailable for EVERY key."""
    for key in ("anything", "T__present", ""):
        presence = presence_for(key, None)
        assert presence.status == PRESENCE_UNAVAILABLE
        assert presence.rows is None


def test_load_n_audit_reads_the_real_committed_artifact():
    """The committed n_audit.json: 50 tasks, real presence data."""
    tasks = load_n_audit()
    assert tasks is not None
    assert len(tasks) == 50
    present = presence_for("BEND__CpG_methylation", tasks)
    assert present.status == PRESENCE_PRESENT
    assert present.rows == (743095, 109717, 106227)
    missing = presence_for("GUE__EPI_GM12878", tasks)
    assert missing.status == PRESENCE_MISSING
    assert missing.rows is None


def test_every_registry_dataset_key_maps_to_a_definite_presence():
    """Real-data adjacency: all 50 registry keys resolve to present or
    missing against the committed audit — no unknown, no exception."""
    tasks = load_n_audit()
    statuses = {
        presence_for(entry["key"], tasks).status
        for entry in load_dataset_entries()
    }
    assert statuses == {PRESENCE_PRESENT, PRESENCE_MISSING}


def test_load_n_audit_corrupt_file_yields_none(tmp_path, monkeypatch):
    """A corrupt n_audit.json -> None sentinel; the service stays alive."""
    corrupt = tmp_path / "n_audit.json"
    corrupt.write_text('{"tasks": {"trunca', encoding="utf-8")
    monkeypatch.setattr(registries_module, "N_AUDIT_PATH", corrupt)
    assert load_n_audit() is None
    # the column-unavailable sentinel flows from the None audit
    assert presence_for("any", None).status == PRESENCE_UNAVAILABLE


def test_load_n_audit_missing_file_yields_none(tmp_path, monkeypatch):
    """A missing n_audit.json -> None sentinel, never a crash."""
    monkeypatch.setattr(
        registries_module, "N_AUDIT_PATH", tmp_path / "absent.json"
    )
    assert load_n_audit() is None


def test_service_source_carries_zero_chinese_and_no_rendered_copy():
    """SEL-04 purity: the service returns data — copy and formatting
    belong to the 08-07 screen (I18N-01: tui/strings.py is the only
    home for operator copy)."""
    source = Path(registries_module.__file__).read_text(encoding="utf-8")
    assert not re.search(r"[一-鿿]", source)
