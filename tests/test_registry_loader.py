"""
Contract tests for ``pipeline/registry_loader.py`` (Phase 7, CUST-05 /
D-06..D-08).

The overlay seam merges user-owned custom registries over the official
ones. Every behavior pinned here is a locked decision:

- **byte-identity when absent** (D-06): no custom file present -> the
  returned dict equals ``json.loads`` of the official file text — today's
  behavior, exactly (CUST-05 backward-compat clause, D-06).
- **collision fail-fast** (D-08): a custom key equal to an official key
  exits naming the key AND both file paths — the clear-error discipline.
- **fail-loud on malformed** (T-07-04): a present-but-malformed custom
  file is a hard error naming the file, never a silent skip.
- **path resolution** (D-07): ``DNALLMMARK_CUSTOM_REGISTRY_DIR`` overrides
  the ENTIRE custom directory (the whole-dir override reading of D-07 —
  "覆盖整个目录"; the suffix join applies to the two config-home bases
  only); otherwise ``XDG_CONFIG_HOME`` else ``~/.config``, each joined
  with ``dnallmmark``.
- **official-file failures propagate** (D-08 导入时序不变): a missing
  official file raises OSError uncaught — the loader must not absorb it,
  because ``run_finetune.py``'s import-time crash-on-missing behavior is
  contract.

Every test that loads a registry pins ``DNALLMMARK_CUSTOM_REGISTRY_DIR``
via monkeypatch (RESEARCH Pitfall 3) so outcomes are machine-independent:
once real custom files exist on a machine, an unpinned test would see the
local overlay and diverge from CI.

See also:
    ``pipeline/registry_loader.py`` — the loader under test.
    ``tests/test_sweep.py`` — the ``write_registry`` fixture shape reused
    below.
"""

import json

import pytest
import registry_loader  # conftest puts pipeline/ on sys.path


def write_registry(root, models, datasets):
    """Materialize unified-registry fixtures under ``root``
    (the tests/test_sweep.py:115-120 shape)."""
    (root / "models_info.json").write_text(
        json.dumps(models), encoding="utf-8")
    (root / "datasets_info.json").write_text(
        json.dumps(datasets), encoding="utf-8")


def pin_custom_dir(monkeypatch, tmp_path, name="custom"):
    """Pin the custom overlay to a fresh empty tmp dir (Pitfall 3).

    Returns the pinned directory so tests can populate it.
    """
    custom_dir = tmp_path / name
    custom_dir.mkdir()
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(custom_dir))
    return custom_dir


def make_official_registry(tmp_path):
    """Build a 2-model x 2-task official registry fixture; return its dir."""
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    write_registry(
        registry_dir,
        models={
            "model-a": {"Model_name": "model-a", "Model_path": "models/a"},
            "model-b": {"Model_name": "model-b", "Model_path": "models/b"},
        },
        datasets={
            "task-x": {"Dataset_name": "task-x", "Train": 100, "Dev": 10},
            "task-y": {"Dataset_name": "task-y", "Train": 50, "Dev": 5},
        },
    )
    return registry_dir


# ===== absent overlay = byte identity (D-06) =====


def test_absent_overlay_models_returns_official_dict_verbatim(
        tmp_path, monkeypatch):
    """No custom_models.json -> the returned dict equals json.loads of the
    official file text (byte-identical behavior, CUST-05)."""
    pin_custom_dir(monkeypatch, tmp_path)
    registry_dir = make_official_registry(tmp_path)
    merged = registry_loader.load_models_registry(registry_dir)
    official_text = (registry_dir / "models_info.json").read_text(
        encoding="utf-8")
    assert merged == json.loads(official_text)


def test_absent_overlay_datasets_returns_official_dict_verbatim(
        tmp_path, monkeypatch):
    """No custom_datasets.json -> the returned dict equals json.loads of
    the official file text (byte-identical behavior, CUST-05)."""
    pin_custom_dir(monkeypatch, tmp_path)
    registry_dir = make_official_registry(tmp_path)
    merged = registry_loader.load_datasets_registry(registry_dir)
    official_text = (registry_dir / "datasets_info.json").read_text(
        encoding="utf-8")
    assert merged == json.loads(official_text)


# ===== merge: custom keys ADD over the official view (D-06) =====


def test_custom_models_key_merges_over_official(tmp_path, monkeypatch):
    """A custom_models.json adding one new key merges: the returned dict
    has every official key plus the custom key, custom entry verbatim."""
    custom_dir = pin_custom_dir(monkeypatch, tmp_path)
    registry_dir = make_official_registry(tmp_path)
    custom_entry = {"Model_name": "model-custom", "Model_path": "models/c"}
    (custom_dir / "custom_models.json").write_text(
        json.dumps({"model-custom": custom_entry}), encoding="utf-8")

    merged = registry_loader.load_models_registry(registry_dir)

    assert set(merged) == {"model-a", "model-b", "model-custom"}
    assert merged["model-custom"] == custom_entry


def test_custom_datasets_key_merges_over_official(tmp_path, monkeypatch):
    """A custom_datasets.json adding one new key merges: the returned dict
    has every official key plus the custom key, custom entry verbatim."""
    custom_dir = pin_custom_dir(monkeypatch, tmp_path)
    registry_dir = make_official_registry(tmp_path)
    custom_entry = {"Dataset_name": "task-custom", "Train": 20, "Dev": 2}
    (custom_dir / "custom_datasets.json").write_text(
        json.dumps({"task-custom": custom_entry}), encoding="utf-8")

    merged = registry_loader.load_datasets_registry(registry_dir)

    assert set(merged) == {"task-x", "task-y", "task-custom"}
    assert merged["task-custom"] == custom_entry


# ===== collision with an official key fails fast (D-08) =====


def test_custom_models_key_colliding_with_official_fails_fast(
        tmp_path, monkeypatch):
    """A custom key equal to an official key exits naming the key AND the
    paths of BOTH the official and the custom file (D-08 clear-error)."""
    custom_dir = pin_custom_dir(monkeypatch, tmp_path)
    registry_dir = make_official_registry(tmp_path)
    (custom_dir / "custom_models.json").write_text(
        json.dumps({"model-a": {"Model_name": "evil-twin"}}),
        encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        registry_loader.load_models_registry(registry_dir)

    message = str(excinfo.value)
    assert "model-a" in message
    assert str(registry_dir / "models_info.json") in message
    assert str(custom_dir / "custom_models.json") in message


def test_custom_datasets_key_colliding_with_official_fails_fast(
        tmp_path, monkeypatch):
    """A custom dataset key equal to an official key exits naming the key
    AND both file paths (D-08 clear-error, datasets side)."""
    custom_dir = pin_custom_dir(monkeypatch, tmp_path)
    registry_dir = make_official_registry(tmp_path)
    (custom_dir / "custom_datasets.json").write_text(
        json.dumps({"task-x": {"Dataset_name": "evil-twin"}}),
        encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        registry_loader.load_datasets_registry(registry_dir)

    message = str(excinfo.value)
    assert "task-x" in message
    assert str(registry_dir / "datasets_info.json") in message
    assert str(custom_dir / "custom_datasets.json") in message


# ===== malformed custom file: fail loud, never silent (T-07-04) =====


def test_malformed_custom_models_json_fails_loud_naming_file(
        tmp_path, monkeypatch):
    """A custom file containing invalid JSON exits naming the file —
    never a silent ignore (the 宁可噪声 discipline)."""
    custom_dir = pin_custom_dir(monkeypatch, tmp_path)
    registry_dir = make_official_registry(tmp_path)
    (custom_dir / "custom_models.json").write_text(
        "{not valid json", encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        registry_loader.load_models_registry(registry_dir)

    assert str(custom_dir / "custom_models.json") in str(excinfo.value)


def test_custom_datasets_top_level_not_object_fails_loud_naming_file(
        tmp_path, monkeypatch):
    """A custom file whose top level is not a JSON object exits naming
    the file (the overlay is a key -> entry map; anything else is
    malformed)."""
    custom_dir = pin_custom_dir(monkeypatch, tmp_path)
    registry_dir = make_official_registry(tmp_path)
    (custom_dir / "custom_datasets.json").write_text(
        json.dumps(["not", "an", "object"]), encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        registry_loader.load_datasets_registry(registry_dir)

    assert str(custom_dir / "custom_datasets.json") in str(excinfo.value)


def test_unreadable_custom_file_fails_loud_naming_file(
        tmp_path, monkeypatch):
    """A present-but-unreadable custom file (permissions) exits naming
    the file — same fail-loud contract as malformed content, never a
    traceback and never a silent skip."""
    custom_dir = pin_custom_dir(monkeypatch, tmp_path)
    registry_dir = make_official_registry(tmp_path)
    custom_path = custom_dir / "custom_models.json"
    custom_path.write_text(
        json.dumps({"model-custom": {}}), encoding="utf-8")
    custom_path.chmod(0o000)

    with pytest.raises(SystemExit) as excinfo:
        registry_loader.load_models_registry(registry_dir)

    assert str(custom_path) in str(excinfo.value)


# ===== custom-dir resolution order (D-07) =====


def test_custom_registry_dir_env_var_wins(monkeypatch, tmp_path):
    """DNALLMMARK_CUSTOM_REGISTRY_DIR overrides the ENTIRE custom
    directory — the whole-dir override reading of D-07 (覆盖整个目录);
    no dnallmmark suffix is appended to it."""
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(tmp_path))
    assert registry_loader.custom_registry_dir() == tmp_path


def test_custom_registry_dir_xdg_config_home(monkeypatch, tmp_path):
    """Without the env var, XDG_CONFIG_HOME is joined with dnallmmark."""
    monkeypatch.delenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", raising=False)
    xdg = tmp_path / "xdg"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    assert registry_loader.custom_registry_dir() == xdg / "dnallmmark"


def test_custom_registry_dir_defaults_to_config_home(monkeypatch, tmp_path):
    """Without env var or XDG, ~/.config is joined with dnallmmark (the
    platformdirs-default path on Linux — D-07)."""
    monkeypatch.delenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert (registry_loader.custom_registry_dir()
            == tmp_path / ".config" / "dnallmmark")


# ===== official-file failures propagate (D-08 导入时序不变) =====


def test_missing_official_models_file_raises_oserror(tmp_path, monkeypatch):
    """A missing OFFICIAL file raises OSError uncaught — the loader does
    not absorb official-file failures (run_finetune import-time
    contract)."""
    pin_custom_dir(monkeypatch, tmp_path)
    empty_dir = tmp_path / "no-registry"
    empty_dir.mkdir()
    with pytest.raises(OSError):
        registry_loader.load_models_registry(empty_dir)


def test_missing_official_datasets_file_raises_oserror(
        tmp_path, monkeypatch):
    """A missing OFFICIAL datasets file raises OSError uncaught
    (run_finetune import-time contract, datasets side)."""
    pin_custom_dir(monkeypatch, tmp_path)
    empty_dir = tmp_path / "no-registry"
    empty_dir.mkdir()
    with pytest.raises(OSError):
        registry_loader.load_datasets_registry(empty_dir)
