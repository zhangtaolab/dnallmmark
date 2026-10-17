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
import os
import re
from pathlib import Path

import pytest
import registry_loader  # conftest puts pipeline/ on sys.path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_FINETUNE = REPO_ROOT / "pipeline" / "run_finetune.py"


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


def test_non_utf8_custom_file_fails_loud_naming_file(tmp_path, monkeypatch):
    """CR-01 (09 review): a custom registry saved in a non-UTF-8 encoding
    (e.g. GBK entry names — a plausible operator artifact for this
    project's audience; the schema tests themselves round-trip
    ``自定义系列`` content) exits naming the file — the same fail-loud
    contract as any other unreadable custom file. A raw
    ``UnicodeDecodeError`` (a ``ValueError`` sibling of
    ``json.JSONDecodeError``, caught by neither existing clause) would
    crash ``run_finetune.py`` at module level with a bare traceback and
    strand the selection screen's load worker (its tolerant seam
    degrades only on ``(OSError, SystemExit)``)."""
    custom_dir = pin_custom_dir(monkeypatch, tmp_path)
    registry_dir = make_official_registry(tmp_path)
    (custom_dir / "custom_models.json").write_bytes(
        '{"k": "自定义"}'.encode("gbk"))

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
    # WR-04 (phase-07 review): root ignores mode bits — without this skip
    # guard (the tests/test_artifact_loader.py:48-49 idiom) a root CI
    # container reads the file fine, the overlay merges, no SystemExit
    # fires, and the test fails spuriously.
    if os.access(custom_path, os.R_OK):
        pytest.skip("permission bits not enforced (running as root)")
    try:
        with pytest.raises(SystemExit) as excinfo:
            registry_loader.load_models_registry(registry_dir)

        assert str(custom_path) in str(excinfo.value)
    finally:
        custom_path.chmod(0o644)


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


# ===== run_finetune rewiring (source contract — read-source-never-import) =====


def test_run_finetune_module_level_loads_route_through_registry_loader():
    """run_finetune.py's module-level registry loads call the overlay
    loader, and the former direct opens of the info JSON filenames are
    gone from executable positions.

    ``run_finetune.py`` is read as SOURCE TEXT and never imported (it
    does ``import torch`` / ``from dnallm import ...`` at module level,
    unavailable CPU-side — the test_run_finetune_contracts.py
    philosophy): the contract is asserted textually. The calls must sit
    at module level (column 0) so the import-time load order and
    crash-on-missing behavior are preserved (D-08 导入时序不变)."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")

    # the sibling-module import is present
    assert re.search(r"^import registry_loader\b", src, re.MULTILINE), (
        "run_finetune.py must import the sibling registry_loader module "
        "(sys.path[0] = pipeline/ when run as a script)"
    )
    # the module-level loads route through the loader (column 0 =
    # module-level statements, the former direct loads' position)
    assert re.search(
        r"^datasets_info = registry_loader\.load_datasets_registry\(\)",
        src, re.MULTILINE), (
        "module-level datasets_info load must call "
        "registry_loader.load_datasets_registry() at module level"
    )
    assert re.search(
        r"^models_info = registry_loader\.load_models_registry\(\)",
        src, re.MULTILINE), (
        "module-level models_info load must call "
        "registry_loader.load_models_registry() at module level"
    )
    # the former direct opens are gone (no executable open of the info
    # JSON filenames remains, at any indentation)
    for name in ("datasets_info", "models_info"):
        assert not re.search(
            rf"open\([^)]*[\"']{name}\.json[\"']", src), (
            f"run_finetune.py must not open {name}.json directly — all "
            "registry reads route through registry_loader"
        )


# ===== enabled:false skip (D-09, Phase 9 09-02 — additive tests only) =====
#
# The loader-level true disable: a custom entry whose ``enabled`` field
# is the literal JSON ``false`` is skipped at load time — absent and
# ``true`` both load (D-09 缺席=启用). Official entries carry no
# ``enabled`` field, so the absent-overlay byte-identity contract above
# and every pre-existing test are untouched; these functions are
# APPEND-ONLY coverage over the new semantics.


def test_disabled_custom_model_entry_is_skipped(tmp_path, monkeypatch):
    """A custom model entry whose ``enabled`` is the literal JSON false
    is ABSENT from load_models_registry() output (D-09); a sibling
    enabled entry in the same file still loads."""
    custom_dir = pin_custom_dir(monkeypatch, tmp_path)
    registry_dir = make_official_registry(tmp_path)
    (custom_dir / "custom_models.json").write_text(
        json.dumps({
            "model-off": {"Model_name": "model-off", "Model_path": "models/o",
                          "enabled": False},
            "model-on": {"Model_name": "model-on", "Model_path": "models/n",
                         "enabled": True},
        }),
        encoding="utf-8")

    merged = registry_loader.load_models_registry(registry_dir)

    assert "model-off" not in merged
    assert merged["model-on"]["Model_name"] == "model-on"
    assert set(merged) == {"model-a", "model-b", "model-on"}


def test_disabled_custom_dataset_entry_is_skipped(tmp_path, monkeypatch):
    """A custom dataset entry with ``enabled: false`` is absent from
    load_datasets_registry() output (D-09, datasets side)."""
    custom_dir = pin_custom_dir(monkeypatch, tmp_path)
    registry_dir = make_official_registry(tmp_path)
    (custom_dir / "custom_datasets.json").write_text(
        json.dumps({
            "task-off": {"Dataset_name": "task-off", "Train": 10, "Dev": 1,
                         "enabled": False},
        }),
        encoding="utf-8")

    merged = registry_loader.load_datasets_registry(registry_dir)

    assert set(merged) == {"task-x", "task-y"}


def test_enabled_true_and_absent_field_both_load(tmp_path, monkeypatch):
    """Absence means enabled (D-09 缺席=启用): entries with ``enabled:
    true`` and with NO enabled field at all both merge — only the
    literal JSON false disables."""
    custom_dir = pin_custom_dir(monkeypatch, tmp_path)
    registry_dir = make_official_registry(tmp_path)
    (custom_dir / "custom_models.json").write_text(
        json.dumps({
            "model-explicit": {"Model_name": "model-explicit",
                               "enabled": True},
            "model-implicit": {"Model_name": "model-implicit"},
        }),
        encoding="utf-8")

    merged = registry_loader.load_models_registry(registry_dir)

    assert "model-explicit" in merged
    assert "model-implicit" in merged


def test_only_literal_false_disables_sentinels(tmp_path, monkeypatch):
    """The sentinel is the JSON literal false ONLY (the ``is not False``
    filter): the string ``"false"``, the int ``0``, and JSON null
    (``None``) do NOT skip — every non-literal-false value loads."""
    custom_dir = pin_custom_dir(monkeypatch, tmp_path)
    registry_dir = make_official_registry(tmp_path)
    (custom_dir / "custom_models.json").write_text(
        json.dumps({
            "model-str": {"Model_name": "model-str", "enabled": "false"},
            "model-zero": {"Model_name": "model-zero", "enabled": 0},
            "model-null": {"Model_name": "model-null", "enabled": None},
        }),
        encoding="utf-8")

    merged = registry_loader.load_models_registry(registry_dir)

    assert set(merged) == {
        "model-a", "model-b", "model-str", "model-zero", "model-null",
    }


def test_disabled_entry_colliding_with_official_still_fails_fast(
        tmp_path, monkeypatch):
    """The skip sits AFTER the collision loop: a disabled entry whose
    key collides with an official key still trips the D-08 fail-fast (a
    disabled shadow attempt is refused, never silently ignored)."""
    custom_dir = pin_custom_dir(monkeypatch, tmp_path)
    registry_dir = make_official_registry(tmp_path)
    (custom_dir / "custom_models.json").write_text(
        json.dumps({"model-a": {"Model_name": "disabled-twin",
                                "enabled": False}}),
        encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        registry_loader.load_models_registry(registry_dir)

    assert "model-a" in str(excinfo.value)


def test_merged_key_order_official_file_order_then_custom_file_order(
        tmp_path, monkeypatch):
    """Ordering: official keys keep official-file order, then landed
    custom keys in custom-file order — a disabled key is skipped without
    disturbing the order of the entries around it."""
    custom_dir = pin_custom_dir(monkeypatch, tmp_path)
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    write_registry(
        registry_dir,
        models={
            "zeta-model": {"Model_name": "zeta-model"},
            "alpha-model": {"Model_name": "alpha-model"},
        },
        datasets={"task-x": {"Dataset_name": "task-x", "Train": 1}})
    (custom_dir / "custom_models.json").write_text(
        json.dumps({
            "c-first": {"Model_name": "c-first"},
            "c-disabled": {"Model_name": "c-disabled", "enabled": False},
            "c-last": {"Model_name": "c-last"},
        }),
        encoding="utf-8")

    merged = registry_loader.load_models_registry(registry_dir)

    assert list(merged) == ["zeta-model", "alpha-model",
                            "c-first", "c-last"]


def test_no_custom_file_official_keys_in_file_order(tmp_path, monkeypatch):
    """With no custom file, the official dict is returned untouched —
    its key sequence equals the official file's own order (the D-06
    byte-identity path executes no filtering at all)."""
    pin_custom_dir(monkeypatch, tmp_path)
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    official_order = ["m-three", "m-one", "m-two"]
    write_registry(
        registry_dir,
        models={key: {"Model_name": key} for key in official_order},
        datasets={"task-x": {"Dataset_name": "task-x", "Train": 1}})

    merged = registry_loader.load_models_registry(registry_dir)

    assert list(merged) == official_order


def test_non_dict_custom_entry_still_merges_after_skip_filter(
        tmp_path, monkeypatch):
    """A custom entry whose value is not a JSON object merges exactly as
    before the D-09 filter: the skip inspects ``enabled`` only on dict
    entries — a non-dict value has no enabled field and must not crash
    the loader where it previously merged."""
    custom_dir = pin_custom_dir(monkeypatch, tmp_path)
    registry_dir = make_official_registry(tmp_path)
    (custom_dir / "custom_models.json").write_text(
        json.dumps({
            "model-scalar": [1, 2],
            "model-off": {"Model_name": "model-off", "enabled": False},
        }),
        encoding="utf-8")

    merged = registry_loader.load_models_registry(registry_dir)

    assert merged["model-scalar"] == [1, 2]
    assert "model-off" not in merged
