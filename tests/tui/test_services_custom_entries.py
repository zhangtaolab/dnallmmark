"""
Tier-1 service tests for ``tui/services/custom_entries.py`` (Phase 9,
09-01 — the TRACER lane).

Pinned decisions:

- **D-08 (gauntlet-all-pass-before-land):** land/undo/set_enabled are the
  ONLY custom-registry write paths; every write goes through
  ``settings.atomic_write`` (tmp sibling + os.replace) with
  ``json.dumps(indent=4, ensure_ascii=False)``.
- **Tracer truth (the phase's riskiest bet, proven headless):** a
  synthetic valid candidate landed into a tmp config dir
  (``DNALLMMARK_TUI_CONFIG_DIR``) that is ALSO the overlay dir
  (``DNALLMMARK_CUSTOM_REGISTRY_DIR``) is visible in
  ``registry_loader.load_models_registry()`` output — the write →
  overlay-load seam works end-to-end before any UI exists; undo returns
  the merged registry to official-only (62/50).
- **Pitfall 4 (pipeline-relative paths):** land converts absolute
  ``Model_path``/``Dataset_path`` via ``os.path.relpath`` against the
  pipeline dir — a landed path starting with a filesystem root is a bug.
- **Pitfall 6/11 (name stamps):** ``Model_name``/``Dataset_name`` land
  stamped equal to the key; ``Train``/``Dev``/``Test`` land as ints with
  bool EXCLUDED from coercion (a bool stays visible, never silently
  transformed).
- **T-09-03 (write authorization):** the official registry files are
  hash-pinned unchanged across land/undo/toggle — binding constraint 11,
  the cardinal separation.
- **Pitfall 7 (management view):** ``read_entries`` is the DIRECT read
  of the user-owned file — disabled entries stay visible, and an absent
  file reads as ``({}, None)`` creating nothing.

Every test injects tmp env roots — the real ``~/.config/dnallmmark``
(this machine HAS one) is never touched.

See also:
    ``tui/services/custom_entries.py`` — the store under test.
    ``pipeline/registry_loader.py`` — the overlay reader the tracer
    exercises (Phase 7 seam).
    ``tests/tui/test_services_custom_validation.py`` — the validator lane.
"""

import hashlib
import json

import pytest
import registry_loader  # top-level module (pipeline/ sys.path root)

from tui.services import custom_entries, settings

CONFIG_ENV = settings.CONFIG_DIR_ENV
OVERLAY_ENV = "DNALLMMARK_CUSTOM_REGISTRY_DIR"


def pin_same_tmp_root(tmp_path, monkeypatch):
    """Point BOTH roots (TUI config + pipeline overlay) at one tmp dir.

    The tracer's load-bearing setup: the store writes
    ``settings.config_dir() / custom_models.json`` and the loader reads
    ``custom_registry_dir() / custom_models.json`` — the same file on the
    same tmp root, never the real home.
    """
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path))
    monkeypatch.setenv(OVERLAY_ENV, str(tmp_path))
    return tmp_path


def full_model_candidate(tmp_path):
    """A synthetic model candidate in the full official 16-field shape.

    ``Model_path`` is ABSOLUTE (the operator-entered form; land
    relativizes it — Pitfall 4).
    """
    return {
        "key": "tracer-custom-lm",
        "Model_name": "stale-name-land-overwrites",
        "Model_path": str(tmp_path / "models" / "tracer-custom-lm"),
        "Model_size": "100M",
        "Tokenizer": "6mer",
        "architecture": "Bert",
        "context_len (bp)": 2000,
        "huggingface": "zhangtaolab/tracer-custom-lm",
        "mean_token_len": 6,
        "Mean_token_length": 6,
        "modelscope": "zhangtaolab/tracer-custom-lm",
        "name": "TracerCustomLM",
        "series": "PDLLMs",
        "size (M)": 89,
        "species": "plants",
        "tokenizer": "6-mer",
        "type": "MLM",
    }


def write_split_csv(dataset_dir, split, rows):
    """Write one split CSV the audit-kernel way: header + data rows."""
    lines = ["sequence,label"]
    lines.extend(f"ACGT,{value}" for value in rows)
    (dataset_dir / f"{split}.csv").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def full_dataset_candidate(tmp_path):
    """A synthetic dataset candidate over REAL tmp split CSVs.

    The declared ``Train``/``Dev``/``Test`` equal the well-formed row
    counts (3/2/2) — the fixture satisfies the split-count mirror that
    lands with the follow-up validator task in this plan.
    """
    dataset_dir = tmp_path / "datasets" / "tracer-custom-ds"
    dataset_dir.mkdir(parents=True)
    write_split_csv(dataset_dir, "train", [0, 1, 0])
    write_split_csv(dataset_dir, "dev", [1, 0])
    write_split_csv(dataset_dir, "test", [0, 1])
    return {
        "key": "TracerCustom__demo_task",
        "Dataset_name": "stale-name-land-overwrites",
        "Dataset_path": str(dataset_dir),
        "Category": "Plants",
        "label_column": "label",
        "Train": 3,
        "Dev": 2,
        "Test": 2,
        "Index": 9999,
        "labels": 2,
        "length": 512,
        "license": "MIT",
        "metric": "f1",
        "preprocessing": "synthetic tracer fixture",
        "source": "https://example.com/tracer",
        "citation": "Tracer fixture (synthetic)",
        "type": "binary",
    }


# ===== The tracer: write → overlay-load seam, end-to-end headless =====


def test_tracer_land_then_overlay_load_then_undo(tmp_path, monkeypatch):
    """THE phase tracer: land → registry_loader overlay sees the
    candidate (63 models / 51 datasets over the official 62/50); undo →
    the merged registries return to official-only (62/50)."""
    root = pin_same_tmp_root(tmp_path, monkeypatch)

    model = full_model_candidate(root)
    dataset = full_dataset_candidate(root)

    models = registry_loader.load_models_registry()
    datasets = registry_loader.load_datasets_registry()
    assert len(models) == 62 and len(datasets) == 50  # official-only base

    model_key = model.pop("key")
    dataset_key = dataset.pop("key")
    custom_entries.land(custom_entries.KIND_MODELS, model_key, model)
    custom_entries.land(custom_entries.KIND_DATASETS, dataset_key, dataset)

    models = registry_loader.load_models_registry()
    datasets = registry_loader.load_datasets_registry()
    assert model_key in models and dataset_key in datasets
    assert len(models) == 63
    assert len(datasets) == 51
    # The landed rows carry the name stamps the pipeline reads directly
    # (run_finetune reads Dataset_name by direct key access — Pitfall 11)
    # and pipeline-RELATIVE paths (string-concat resolution — Pitfall 4).
    assert models[model_key]["Model_name"] == model_key
    assert not models[model_key]["Model_path"].startswith("/")
    assert datasets[dataset_key]["Dataset_name"] == dataset_key
    assert not datasets[dataset_key]["Dataset_path"].startswith("/")

    assert custom_entries.undo(custom_entries.KIND_MODELS, model_key) is True
    assert custom_entries.undo(custom_entries.KIND_DATASETS, dataset_key) is True
    models = registry_loader.load_models_registry()
    datasets = registry_loader.load_datasets_registry()
    assert model_key not in models and dataset_key not in datasets
    assert len(models) == 62
    assert len(datasets) == 50


def test_single_overlay_pin_routes_writes_to_the_pinned_root(
        tmp_path, monkeypatch):
    """WR-01 (09 review): pinning ONLY ``DNALLMMARK_CUSTOM_REGISTRY_DIR``
    (the documented whole-dir override) routes every WRITE through the
    pinned root — the same root the read side and the pipeline overlay
    loader resolve. Pre-fix, the write rail resolved
    ``settings.config_dir()`` unconditionally: a land/toggle/undo in a
    single-var-pin configuration silently targeted the divergent config
    root, so the toggle deterministically missed the key and a just-
    landed entry was invisible to the table AND the loader."""
    overlay = tmp_path / "overlay-root"
    overlay.mkdir()
    # The deliberately DIVERGENT TUI config root: a write landing here
    # would be invisible to both read rails (and to the loader). Also
    # keeps the test machine-safe pre-fix — the real home is never
    # touched even while reproducing the divergence.
    config = tmp_path / "config-root"
    config.mkdir()
    monkeypatch.setenv(OVERLAY_ENV, str(overlay))
    monkeypatch.setenv(CONFIG_ENV, str(config))

    path = custom_entries.land(custom_entries.KIND_MODELS, "pinned-lm", {
        "Model_path": str(tmp_path / "models" / "pinned-lm"),
        "type": "MLM",
    })

    # the land wrote the overlay loader's root, and the divergent config
    # root stayed empty — never two files
    assert path == overlay / registry_loader.CUSTOM_MODELS_NAME
    assert list(config.iterdir()) == []
    # the default read (the management view's root) sees it on the SAME
    # file, as does the pipeline-side resolver
    entries, error = custom_entries.read_entries(custom_entries.KIND_MODELS)
    assert error is None and list(entries) == ["pinned-lm"]
    assert registry_loader.custom_registry_dir() == overlay
    # the toggle finds the key and rewrites the SAME file
    assert custom_entries.set_enabled(
        custom_entries.KIND_MODELS, "pinned-lm", False)
    entries, _ = custom_entries.read_entries(custom_entries.KIND_MODELS)
    assert entries["pinned-lm"]["enabled"] is False
    assert list(config.iterdir()) == []
    # undo removes it from the SAME file
    assert custom_entries.undo(custom_entries.KIND_MODELS, "pinned-lm")
    entries, _ = custom_entries.read_entries(custom_entries.KIND_MODELS)
    assert entries == {}


# ===== Read edge: absent file is empty, never an error, never created =====


def test_read_entries_absent_file_is_empty_and_creates_nothing(
    tmp_path, monkeypatch
):
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path))
    for kind in (custom_entries.KIND_MODELS, custom_entries.KIND_DATASETS):
        path = custom_entries.custom_registry_path(kind)
        assert not path.exists()
        entries, error = custom_entries.read_entries(kind)
        assert entries == {}
        assert error is None
        assert not path.exists()  # the read creates no file


def test_read_entries_tolerates_corrupt_and_non_object_files(
    tmp_path, monkeypatch
):
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path))
    path = custom_entries.custom_registry_path(custom_entries.KIND_MODELS)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json", encoding="utf-8")
    entries, error = custom_entries.read_entries(custom_entries.KIND_MODELS)
    assert entries == {}
    assert "unreadable" in error

    path.write_text("[1, 2, 3]", encoding="utf-8")
    entries, error = custom_entries.read_entries(custom_entries.KIND_MODELS)
    assert entries == {}
    assert "object" in error


def test_land_over_a_corrupt_registry_refuses_loudly(tmp_path, monkeypatch):
    """The tolerant read is for the management view; the WRITE seam is
    strict — a read-modify-write over a corrupt file is refused."""
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path))
    path = custom_entries.custom_registry_path(custom_entries.KIND_MODELS)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="unreadable"):
        custom_entries.land(custom_entries.KIND_MODELS, "m", {"size (M)": 1})


# ===== Land normalization (Pitfall 4/6/11) =====


def test_land_relativizes_absolute_paths_and_stamps_names(tmp_path, monkeypatch):
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path))
    model = full_model_candidate(tmp_path)
    key = model.pop("key")
    custom_entries.land(custom_entries.KIND_MODELS, key, model)
    landed, _error = custom_entries.read_entries(custom_entries.KIND_MODELS)
    import os

    assert not os.path.isabs(landed[key]["Model_path"])
    assert landed[key]["Model_path"].startswith("..")
    assert landed[key]["Model_name"] == key  # the stale fixture name is gone
    # The wizard's key form field never lands as an entry field.
    assert "key" not in landed[key]


def test_land_coerces_split_ints_but_never_bools(tmp_path, monkeypatch):
    """Train/Dev/Test coerce (str/integral float -> int); a bool is
    EXCLUDED from coercion and stays visible (the D-14 discipline)."""
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path))
    dataset = full_dataset_candidate(tmp_path)
    key = dataset.pop("key")
    dataset["Train"] = "3"        # digit string -> 3
    dataset["Dev"] = 2.0          # integral float -> 2
    dataset["Test"] = True        # bool -> stays True, never 1
    custom_entries.land(custom_entries.KIND_DATASETS, key, dataset)
    landed, _error = custom_entries.read_entries(custom_entries.KIND_DATASETS)
    entry = landed[key]
    assert entry["Train"] == 3 and isinstance(entry["Train"], int)
    assert entry["Dev"] == 2 and isinstance(entry["Dev"], int)
    assert entry["Test"] is True  # excluded: unchanged, still visible


def test_landed_file_is_indented_utf8_verbatim_json(tmp_path, monkeypatch):
    """ensure_ascii=False + indent 4: non-ASCII content round-trips as
    literal characters, and the bytes are exactly the canonical dump."""
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path))
    model = full_model_candidate(tmp_path)
    key = model.pop("key")
    model["series"] = "自定义系列"
    custom_entries.land(custom_entries.KIND_MODELS, key, model)
    path = custom_entries.custom_registry_path(custom_entries.KIND_MODELS)
    text = path.read_text(encoding="utf-8")
    assert "自定义系列" in text  # not \\u escapes
    assert text == json.dumps(json.loads(text), indent=4, ensure_ascii=False)


# ===== The single write rail (atomic_write is the only write call) =====


def test_land_routes_through_settings_atomic_write(tmp_path, monkeypatch):
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path))
    calls = []
    real = settings.atomic_write

    def spy(path, text):
        calls.append((path, text))
        real(path, text)

    monkeypatch.setattr(custom_entries.settings, "atomic_write", spy)
    model = full_model_candidate(tmp_path)
    key = model.pop("key")
    custom_entries.land(custom_entries.KIND_MODELS, key, model)
    assert len(calls) == 1
    assert calls[0][0] == custom_entries.custom_registry_path(
        custom_entries.KIND_MODELS
    )


def test_module_body_has_no_direct_file_writes():
    """The write-rail lock: atomic_write is the only write call — the
    module body carries no write_text/os.replace/json.dump of its own."""
    source = custom_entries.__file__
    with open(source, encoding="utf-8") as handle:
        body = handle.read()
    assert "settings.atomic_write" in body
    for forbidden in ("write_text", "os.replace", "json.dump("):
        assert forbidden not in body, forbidden


# ===== Undo + enabled toggle (D-08/D-09) =====


def test_undo_absent_key_or_file_is_a_noop_false(tmp_path, monkeypatch):
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path))
    assert custom_entries.undo(custom_entries.KIND_MODELS, "ghost") is False
    assert not custom_entries.custom_registry_path(
        custom_entries.KIND_MODELS
    ).exists()  # the no-op creates no file either


def test_set_enabled_writes_the_literal_boolean(tmp_path, monkeypatch):
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path))
    model = full_model_candidate(tmp_path)
    key = model.pop("key")
    custom_entries.land(custom_entries.KIND_MODELS, key, model)

    assert custom_entries.set_enabled(
        custom_entries.KIND_MODELS, key, False
    ) is True
    entries, _error = custom_entries.read_entries(custom_entries.KIND_MODELS)
    assert entries[key]["enabled"] is False

    assert custom_entries.set_enabled(
        custom_entries.KIND_MODELS, key, True
    ) is True
    entries, _error = custom_entries.read_entries(custom_entries.KIND_MODELS)
    assert entries[key]["enabled"] is True


def test_reads_never_rewrite_entries_lacking_enabled(tmp_path, monkeypatch):
    """The enabled field appears ONLY through the toggle — reads leave a
    landed entry byte-identical (D-09 absence-means-enabled)."""
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path))
    model = full_model_candidate(tmp_path)
    key = model.pop("key")
    path = custom_entries.land(custom_entries.KIND_MODELS, key, model)
    before = path.read_bytes()
    for _ in range(3):
        custom_entries.read_entries(custom_entries.KIND_MODELS)
    assert path.read_bytes() == before


def test_set_enabled_absent_key_returns_false(tmp_path, monkeypatch):
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path))
    assert custom_entries.set_enabled(
        custom_entries.KIND_MODELS, "ghost", True
    ) is False


# ===== T-09-03: the official files are provably untouched =====


def test_official_registries_hash_unchanged_across_all_writes(
    tmp_path, monkeypatch
):
    pin_same_tmp_root(tmp_path, monkeypatch)
    before = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in custom_entries.OFFICIAL_REGISTRY_PATHS
    }
    model = full_model_candidate(tmp_path)
    model_key = model.pop("key")
    dataset = full_dataset_candidate(tmp_path)
    dataset_key = dataset.pop("key")
    custom_entries.land(custom_entries.KIND_MODELS, model_key, model)
    custom_entries.land(custom_entries.KIND_DATASETS, dataset_key, dataset)
    custom_entries.set_enabled(custom_entries.KIND_MODELS, model_key, False)
    custom_entries.set_enabled(custom_entries.KIND_DATASETS, dataset_key, True)
    custom_entries.undo(custom_entries.KIND_MODELS, model_key)
    custom_entries.undo(custom_entries.KIND_DATASETS, dataset_key)
    after = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in custom_entries.OFFICIAL_REGISTRY_PATHS
    }
    assert before == after


# ===== API shape =====


def test_custom_registry_path_rejects_unknown_kind(tmp_path, monkeypatch):
    monkeypatch.setenv(CONFIG_ENV, str(tmp_path))
    with pytest.raises(ValueError, match="kind"):
        custom_entries.custom_registry_path("bogus")


def test_file_names_are_the_registry_loader_twins():
    """The store and the overlay reader can never diverge on the file
    names — the mapping IS the loader's constants."""
    assert custom_entries.KIND_FILE_NAMES == {
        custom_entries.KIND_MODELS: registry_loader.CUSTOM_MODELS_NAME,
        custom_entries.KIND_DATASETS: registry_loader.CUSTOM_DATASETS_NAME,
    }
