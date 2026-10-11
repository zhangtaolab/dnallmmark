"""
Tier-1 service tests for ``tui/services/settings.py`` (Phase 8, 08-04).

Pinned decisions:

- D-04 (state/config split): the settings service resolves the two XDG
  roots SEPARATELY through platformdirs — env-check state to
  ``user_state_dir("dnallmmark")`` (Linux
  ``~/.local/state/dnallmmark``), user-owned presets/templates/settings
  to ``user_config_dir("dnallmmark")`` (the same root as the Phase 7
  custom registries). Check results never persist under the config root
  and presets never persist under the state root — the split is absolute.
- Whole-dir env overrides (the Phase 7 ``DNALLMMARK_CUSTOM_REGISTRY_DIR``
  precedent, ``pipeline/registry_loader.py:57-81``):
  ``DNALLMMARK_TUI_STATE_DIR`` / ``DNALLMMARK_TUI_CONFIG_DIR`` beat
  platformdirs; an EMPTY value is treated as unset.
- D-10: the TUI side resolves through the platformdirs LIBRARY (the
  pipeline-side hand-rolled resolver stays untouched) — the delegation
  tests pin the call, not just the path it happens to produce.
- T-08-03 (atomic writes): every persistence site writes tmp +
  ``os.replace`` through ``atomic_write`` — a torn file is impossible on
  success and no ``.tmp`` residue survives.

See also:
    ``tui/services/settings.py`` — the service under test.
    ``pipeline/registry_loader.py`` — the override-chain idiom mirrored.
"""

from pathlib import Path

from tui.services import settings as settings_module
from tui.services.settings import atomic_write, config_dir, state_dir


def _platformdirs_spy(sentinel, appname_expected):
    """A platformdirs stand-in that pins the appname and returns a sentinel."""

    def _resolve(appname):
        assert appname == appname_expected
        return sentinel

    return _resolve


def test_state_dir_env_override_beats_platformdirs(monkeypatch, tmp_path):
    """DNALLMMARK_TUI_STATE_DIR set -> the whole override dir wins (D-04)."""
    monkeypatch.setenv("DNALLMMARK_TUI_STATE_DIR", str(tmp_path))
    assert state_dir() == tmp_path


def test_state_dir_unset_delegates_to_platformdirs(monkeypatch):
    """No override -> platformdirs user_state_dir("dnallmmark") (D-04/D-10)."""
    monkeypatch.delenv("DNALLMMARK_TUI_STATE_DIR", raising=False)
    sentinel = Path("/sentinel-state")
    monkeypatch.setattr(
        settings_module,
        "user_state_dir",
        _platformdirs_spy(sentinel, "dnallmmark"),
    )
    assert state_dir() == sentinel


def test_state_dir_empty_value_is_unset(monkeypatch):
    """An empty override value behaves as unset (registry_loader precedent)."""
    monkeypatch.setenv("DNALLMMARK_TUI_STATE_DIR", "")
    sentinel = Path("/sentinel-state")
    monkeypatch.setattr(
        settings_module,
        "user_state_dir",
        _platformdirs_spy(sentinel, "dnallmmark"),
    )
    assert state_dir() == sentinel


def test_config_dir_env_override_beats_platformdirs(monkeypatch, tmp_path):
    """DNALLMMARK_TUI_CONFIG_DIR set -> the whole override dir wins (D-04)."""
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    assert config_dir() == tmp_path


def test_config_dir_unset_delegates_to_platformdirs(monkeypatch):
    """No override -> platformdirs user_config_dir("dnallmmark") (D-04/D-10)."""
    monkeypatch.delenv("DNALLMMARK_TUI_CONFIG_DIR", raising=False)
    sentinel = Path("/sentinel-config")
    monkeypatch.setattr(
        settings_module,
        "user_config_dir",
        _platformdirs_spy(sentinel, "dnallmmark"),
    )
    assert config_dir() == sentinel


def test_config_dir_empty_value_is_unset(monkeypatch):
    """An empty override value behaves as unset (registry_loader precedent)."""
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", "")
    sentinel = Path("/sentinel-config")
    monkeypatch.setattr(
        settings_module,
        "user_config_dir",
        _platformdirs_spy(sentinel, "dnallmmark"),
    )
    assert config_dir() == sentinel


def test_state_and_config_roots_are_resolved_independently(monkeypatch, tmp_path):
    """D-04: each root follows only its own override — no cross-wiring."""
    state_override = tmp_path / "state"
    monkeypatch.setenv("DNALLMMARK_TUI_STATE_DIR", str(state_override))
    monkeypatch.setattr(
        settings_module,
        "user_config_dir",
        _platformdirs_spy(Path("/sentinel-config"), "dnallmmark"),
    )
    monkeypatch.delenv("DNALLMMARK_TUI_CONFIG_DIR", raising=False)
    assert state_dir() == state_override
    assert config_dir() == Path("/sentinel-config")


def test_atomic_write_creates_parents_and_leaves_no_tmp_residue(tmp_path):
    """T-08-03: tmp + os.replace — parent dirs created, no .tmp residue.

    Writing twice to the same target must leave exactly ONE valid file:
    the second write replaces the first atomically and the tmp sibling
    never survives a successful write.
    """
    target = tmp_path / "nested" / "state" / "env_check.json"
    atomic_write(target, "first")
    atomic_write(target, "second")
    assert target.read_text(encoding="utf-8") == "second"
    assert list(target.parent.iterdir()) == [target]
