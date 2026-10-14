"""
Unit tests for ``pipeline/directories_config.py`` (261014-f4w, F4W-01).

The ONE shared startup-config loader: tier-1 pins over the resolver
order, the strict/tolerant load pair, the key-tolerance policy, and the
effective() precedence merge both scripts consume.

Machine-independence: the root conftest's autouse
``_pin_directories_config_root`` fixture points
DNALLMMARK_TUI_CONFIG_DIR at a per-test empty tmp dir, so every test
here starts from the absent-file case; resolution-order tests delenv
the pin (and XDG_CONFIG_HOME) and re-pin what they need — the
tests/test_registry_loader.py discipline.

The same-root pin imports ``tui.services.settings`` (platformdirs —
the [tui] group rides every pytest lane): the ROOT conftest carries
the pipeline/ import root but not the repo root, so the repo root is
inserted locally for the package-qualified ``tui`` import (the
tests/tui/conftest.py contract, inlined — the ty extra-paths mirror).
"""

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))  # tui.services.settings (same-root pin)

import directories_config  # conftest puts pipeline/ on sys.path

from tui.services import settings as tui_settings

# ===== helpers =====


def _write_config(root, payload, name=None):
    """Write a directories.json (or raw text) under ``root``."""
    target = root / (name or directories_config.DIRECTORIES_FILE_NAME)
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        target.write_text(payload, encoding="utf-8")
    else:
        target.write_text(json.dumps(payload), encoding="utf-8")
    return target


def _clear_env(monkeypatch):
    """Unset both resolver env vars (resolution-order tests)."""
    monkeypatch.delenv("DNALLMMARK_TUI_CONFIG_DIR", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)


# ===== Resolution order (the settings.py conventions) =====


def test_whole_dir_env_override_wins(tmp_path, monkeypatch):
    """DNALLMMARK_TUI_CONFIG_DIR overrides the ENTIRE directory — the
    config file resolves directly under it, never XDG/home."""
    _clear_env(monkeypatch)
    override = tmp_path / "injected-config"
    override.mkdir()
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(override))
    xdg = tmp_path / "xdg-home"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    assert directories_config.config_dir() == override
    assert directories_config.config_path() == (
        override / directories_config.DIRECTORIES_FILE_NAME)


def test_empty_env_override_is_treated_as_unset(tmp_path, monkeypatch):
    """An EMPTY whole-dir override value reads as unset — the XDG basis
    governs (the settings.py empty-means-unset convention)."""
    _clear_env(monkeypatch)
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", "")
    xdg = tmp_path / "xdg-home"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    assert directories_config.config_dir() == xdg / "dnallmmark"


def test_xdg_config_home_basis(tmp_path, monkeypatch):
    """With the override unset, XDG_CONFIG_HOME joins with dnallmmark."""
    _clear_env(monkeypatch)
    xdg = tmp_path / "xdg-home"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    assert directories_config.config_dir() == xdg / "dnallmmark"


def test_home_default_when_both_unset(tmp_path, monkeypatch):
    """With both env vars unset, the resolver falls back to the pinned
    HOME's .config/dnallmmark (the platformdirs Linux default path)."""
    _clear_env(monkeypatch)
    home = tmp_path / "fake-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    assert directories_config.config_dir() == (
        home / ".config" / "dnallmmark")


def test_config_path_agrees_with_tui_settings_config_dir(
        tmp_path, monkeypatch):
    """D-10 same-root pin: under the injected env, this hand-rolled
    resolver and the platformdirs-based TUI write root resolve the SAME
    directory — the slot-4 save action writes the exact file this
    loader reads."""
    injected = tmp_path / "same-root"
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(injected))
    assert directories_config.config_dir() == tui_settings.config_dir()
    assert directories_config.config_path() == (
        tui_settings.config_dir() / directories_config.DIRECTORIES_FILE_NAME)


# ===== load_directories — the strict read =====


def test_missing_file_returns_empty_dict(tmp_path, monkeypatch):
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    assert directories_config.load_directories() == {}


def test_all_five_keys_load_stripped(tmp_path, monkeypatch):
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    _write_config(tmp_path, {
        "model_root": "  /mnt/models  ",
        "dataset_root": "/mnt/datasets",
        "output_root": "/mnt/out",
        "log_dir": "/mnt/logs",
        "cache_dir": "/mnt/cache",
    })
    assert directories_config.load_directories() == {
        "model_root": "/mnt/models",
        "dataset_root": "/mnt/datasets",
        "output_root": "/mnt/out",
        "log_dir": "/mnt/logs",
        "cache_dir": "/mnt/cache",
    }, "values load STRIPPED (whitespace is not part of the path)"


def test_whitespace_and_empty_values_drop_the_key(tmp_path, monkeypatch):
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    _write_config(tmp_path, {
        "model_root": "   ",
        "dataset_root": "",
        "output_root": "/mnt/out",
    })
    assert directories_config.load_directories() == {"output_root": "/mnt/out"}


def test_unknown_keys_and_schema_version_envelope_ignored(
        tmp_path, monkeypatch):
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    _write_config(tmp_path, {
        "schema_version": 1,
        "future_key": "/nowhere",
        "log_dir": "/mnt/logs",
    })
    assert directories_config.load_directories() == {"log_dir": "/mnt/logs"}


def test_non_str_values_are_dropped(tmp_path, monkeypatch):
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    _write_config(tmp_path, {
        "model_root": 42,
        "dataset_root": ["/mnt/datasets"],
        "log_dir": None,
        "cache_dir": "/mnt/cache",
    })
    assert directories_config.load_directories() == {"cache_dir": "/mnt/cache"}


@pytest.mark.parametrize("payload", [
    "{not json",
    "[]",
    '"a string"',
    "3",
])
def test_malformed_present_file_raises_systemexit_naming_path(
        tmp_path, monkeypatch, payload):
    """The fail-loud policy (the registry_loader T-07-04 precedent): a
    PRESENT but malformed file — invalid JSON, non-dict top level —
    aborts naming the path, never a silent {} that would redirect a
    multi-day run to the wrong roots."""
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    path = _write_config(tmp_path, payload)
    with pytest.raises(SystemExit) as excinfo:
        directories_config.load_directories()
    assert str(path) in str(excinfo.value)


def test_unreadable_file_raises_systemexit_naming_path(
        tmp_path, monkeypatch):
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    path = _write_config(tmp_path, '{"model_root": "/mnt/models"}')
    path.chmod(0o000)
    try:
        readable_as_root = path.read_text(encoding="utf-8")
    except OSError:
        readable_as_root = None
    path.chmod(0o644)
    if readable_as_root is not None:
        pytest.skip(
            "running as root — permission bits cannot make a file "
            "unreadable (the chmod-based persist-failure precedent)")
    path.chmod(0o000)
    with pytest.raises(SystemExit) as excinfo:
        directories_config.load_directories()
    path.chmod(0o644)
    assert str(path) in str(excinfo.value)


# ===== load_directories_tolerant — the display twin =====


@pytest.mark.parametrize("payload", [
    "{not json",
    "[]",
    '"a string"',
])
def test_tolerant_returns_empty_on_every_failure_mode(
        tmp_path, monkeypatch, payload):
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    _write_config(tmp_path, payload)
    assert directories_config.load_directories_tolerant() == {}


def test_tolerant_reads_valid_files_like_strict(tmp_path, monkeypatch):
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    _write_config(tmp_path, {"log_dir": "/mnt/logs"})
    assert directories_config.load_directories_tolerant() == {
        "log_dir": "/mnt/logs"}


def test_tolerant_missing_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    assert directories_config.load_directories_tolerant() == {}


# ===== effective() — the precedence merge =====


def test_effective_flag_beats_file_key(tmp_path, monkeypatch):
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    _write_config(tmp_path, {"log_dir": "/mnt/logs"})
    assert directories_config.effective(
        "/flag/logs", "log_dir") == "/flag/logs"


def test_effective_file_fills_absent_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    _write_config(tmp_path, {"log_dir": "/mnt/logs"})
    assert directories_config.effective(None, "log_dir") == "/mnt/logs"


def test_effective_none_when_both_absent(tmp_path, monkeypatch):
    """The ADD-ALONGSIDE contract: a None return means the consumer's
    own default branch governs — byte-identical to today."""
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    _write_config(tmp_path, {"log_dir": "/mnt/logs"})
    assert directories_config.effective(None, "model_root") is None


def test_directory_keys_is_the_frozen_five():
    """The canonical five-key vocabulary and order every consumer
    shares (the slot-1 overview and the slot-4 save document)."""
    assert directories_config.DIRECTORY_KEYS == (
        "model_root", "dataset_root", "output_root", "log_dir", "cache_dir")
