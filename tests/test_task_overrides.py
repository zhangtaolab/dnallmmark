"""
Unit tests for ``pipeline/task_overrides.py`` (quick-261027-fyt,
OVERRIDES-FILE-TOLERANT-LOADER).

The ONE tolerant reader over the user-owned ``task_overrides.json`` —
a task-keyed temporary-unavailability overlay (unavailable + reason +
since per registry task key). Pinned decisions:

- SAME-ROOT pin: the file resolves through ``directories_config
  .config_dir()`` — the SAME root ``directories.json`` lives under,
  never a second hand-rolled resolver (resolution-order pins mirror
  ``tests/test_directories_config.py``).
- FAIL-OPEN (the ruled policy, opposite of directories.json's
  fail-loud): an exclusion list must never block the benchmark — an
  absent file is the NORMAL zero-override state (degraded None), and a
  present-but-malformed file (unreadable / invalid JSON / non-dict top
  level / non-dict ``tasks``) yields ZERO overrides with ``degraded``
  carrying the PATH (each consumer composes its own message; I18N-01).
- ENTRY TOLERANCE: non-dict entries drop; only ``unavailable is True``
  flags (false / absent / truthy-non-true never); ``reason``/``since``
  read only as str (anything else reads as ""); keys unknown to the
  dataset registry STAY in the mapping — consumers join structurally,
  so a model key in the file affects nothing (the file is task-scoped).

Machine independence: the root conftest's autouse
``_pin_directories_config_root`` fixture points
DNALLMMARK_TUI_CONFIG_DIR at a per-test empty tmp dir, so every test
here starts from the absent-file case; resolution-order tests delenv
the pin (and XDG_CONFIG_HOME) and re-pin what they need — the
tests/test_directories_config.py discipline.

See also:
    ``pipeline/directories_config.py`` — the same-root resolver + the
    contract style this module mirrors.
    ``tests/tui/test_services_registries.py`` — the availability
    overlay over the presence layer.
    ``tests/test_sweep.py`` — the enumerate/warn/skip CLI behavior.
"""

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))  # tui.services.settings (same-root pin)

import directories_config
import task_overrides  # conftest puts pipeline/ on sys.path

from tui.services import settings as tui_settings

# ===== helpers =====


def _write_overrides(root, payload, name=None):
    """Write a task_overrides.json (or raw text) under ``root``."""
    target = root / (name or task_overrides.TASK_OVERRIDES_FILE_NAME)
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


# ===== Resolution order (the directories_config same-root pin) =====


def test_overrides_path_is_the_directories_config_root_joined(tmp_path,
                                                              monkeypatch):
    """overrides_path() == directories_config.config_dir() /
    task_overrides.json — the SAME-ROOT pin, never a second resolver."""
    _clear_env(monkeypatch)
    override = tmp_path / "injected-config"
    override.mkdir()
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(override))
    assert task_overrides.overrides_path() == (
        directories_config.config_dir()
        / task_overrides.TASK_OVERRIDES_FILE_NAME)
    assert task_overrides.overrides_path().name == "task_overrides.json"


def test_whole_dir_env_override_moves_the_file(tmp_path, monkeypatch):
    """DNALLMMARK_TUI_CONFIG_DIR re-pinned moves the resolved file (the
    whole-dir override; test injection points a tmp_path directly)."""
    _clear_env(monkeypatch)
    first = tmp_path / "config-one"
    first.mkdir()
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(first))
    assert task_overrides.overrides_path().parent == first
    second = tmp_path / "config-two"
    second.mkdir()
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(second))
    assert task_overrides.overrides_path().parent == second


def test_empty_env_override_is_treated_as_unset(tmp_path, monkeypatch):
    """An EMPTY whole-dir override value reads as unset — the XDG basis
    governs (the settings.py empty-means-unset convention)."""
    _clear_env(monkeypatch)
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", "")
    xdg = tmp_path / "xdg-home"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    assert task_overrides.overrides_path() == (
        xdg / "dnallmmark" / task_overrides.TASK_OVERRIDES_FILE_NAME)


def test_xdg_config_home_basis(tmp_path, monkeypatch):
    """With the override unset, XDG_CONFIG_HOME joins with dnallmmark."""
    _clear_env(monkeypatch)
    xdg = tmp_path / "xdg-home"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    assert task_overrides.overrides_path().parent == xdg / "dnallmmark"


def test_home_default_when_both_unset(tmp_path, monkeypatch):
    """With both env vars unset, the resolver falls back to the pinned
    HOME's .config/dnallmmark."""
    _clear_env(monkeypatch)
    home = tmp_path / "fake-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    assert task_overrides.overrides_path().parent == (
        home / ".config" / "dnallmmark")


def test_overrides_path_agrees_with_tui_settings_config_dir(
        tmp_path, monkeypatch):
    """The D-10 same-root pin holds for this file too: under the
    injected env, the pipeline resolver and the platformdirs-based TUI
    write root resolve the SAME directory."""
    injected = tmp_path / "same-root"
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(injected))
    assert task_overrides.overrides_path().parent == (
        tui_settings.config_dir())


# ===== The tolerant load (fail-open, the ruled policy) =====


def test_absent_file_is_the_normal_zero_override_state(tmp_path,
                                                       monkeypatch):
    """No file anywhere on the chain -> empty mapping, degraded None
    (absence is normal, never an error — byte-identity for every
    consumer)."""
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    loaded = task_overrides.load_task_overrides()
    assert loaded.unavailable == {}
    assert loaded.degraded is None
    assert task_overrides.unavailable_tasks() == {}


@pytest.mark.parametrize("payload", [
    "{not json",                       # invalid JSON
    "",                                # empty file
    '["a", "list"]',                   # non-dict top level
    '"a bare string"',                 # non-dict top level (str)
    '{"no_tasks": {}}',                # no tasks mapping
    '{"tasks": [1, 2]}',               # non-dict tasks
])
def test_malformed_file_yields_zero_overrides_and_degraded_path(
        tmp_path, monkeypatch, payload):
    """A PRESENT but malformed file -> ZERO overrides + degraded
    carrying the PATH — fail-open (an exclusion list must never block
    the benchmark) but never silent (each surface composes its own
    warning from the path)."""
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    target = _write_overrides(tmp_path, payload)
    loaded = task_overrides.load_task_overrides()
    assert loaded.unavailable == {}
    assert loaded.degraded == str(target)
    assert task_overrides.unavailable_tasks() == {}


def test_malformed_file_with_explicit_path_still_degrades(tmp_path):
    """The explicit-path form degrades identically (degraded carries
    exactly the path given)."""
    target = tmp_path / "custom-overrides.json"
    target.write_text("{not json", encoding="utf-8")
    loaded = task_overrides.load_task_overrides(target)
    assert loaded.unavailable == {}
    assert loaded.degraded == str(target)


def test_directory_at_path_reads_as_absent_not_raises(tmp_path,
                                                      monkeypatch):
    """A directory at the file's location reads as ABSENT (the
    directories_config ``is_file()`` convention) — never an exception,
    never a degradation: the tolerant reader only attempts to parse
    things that are files."""
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    (tmp_path / task_overrides.TASK_OVERRIDES_FILE_NAME).mkdir()
    loaded = task_overrides.load_task_overrides()
    assert loaded.unavailable == {}
    assert loaded.degraded is None


# ===== Entry shapes (the tolerance table) =====


def test_unavailable_true_flags_with_reason_and_since(tmp_path,
                                                      monkeypatch):
    """The canonical entry: unavailable true + str reason/since."""
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    _write_overrides(tmp_path, {"tasks": {
        "GUE__virus_species_40": {
            "unavailable": True,
            "reason": "10k-token uniform sequences at the 32 GB ceiling",
            "since": "2026-10-27",
        },
    }})
    loaded = task_overrides.load_task_overrides()
    assert loaded.unavailable == {
        "GUE__virus_species_40": task_overrides.TaskOverrideEntry(
            reason="10k-token uniform sequences at the 32 GB ceiling",
            since="2026-10-27",
        ),
    }
    assert loaded.degraded is None


@pytest.mark.parametrize("entry", [
    {"unavailable": False, "reason": "r"},   # explicit false
    {"reason": "r"},                         # absent
    {"unavailable": "yes", "reason": "r"},   # truthy non-true str
    {"unavailable": 1, "reason": "r"},       # truthy non-true int
    {},                                      # empty entry
])
def test_non_true_unavailable_never_flags(tmp_path, monkeypatch, entry):
    """Only the literal JSON ``true`` flags — everything else (false,
    absent, truthy-non-true) reads as not flagged, and a not-flagged
    entry stays OUT of the mapping entirely."""
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    _write_overrides(tmp_path, {"tasks": {"T": entry}})
    loaded = task_overrides.load_task_overrides()
    assert loaded.unavailable == {}
    assert loaded.degraded is None


def test_non_dict_entry_is_dropped(tmp_path, monkeypatch):
    """A non-dict entry value drops (never coerced, never an
    exception) — the loader-level shape tolerance."""
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    _write_overrides(tmp_path, {"tasks": {
        "bad": "a string entry",
        "good": {"unavailable": True, "reason": "r", "since": "s"},
    }})
    loaded = task_overrides.load_task_overrides()
    assert set(loaded.unavailable) == {"good"}


@pytest.mark.parametrize("reason,since", [
    (None, None),
    (7, ["2026"]),
    ("str reason", 3.14),
])
def test_non_str_reason_and_since_read_as_empty(tmp_path, monkeypatch,
                                                reason, since):
    """reason/since read ONLY as str — anything else reads as ""."""
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    _write_overrides(tmp_path, {"tasks": {
        "T": {"unavailable": True, "reason": reason, "since": since},
    }})
    loaded = task_overrides.load_task_overrides()
    assert loaded.unavailable["T"] == task_overrides.TaskOverrideEntry(
        reason=reason if isinstance(reason, str) else "",
        since=since if isinstance(since, str) else "",
    )


def test_absent_reason_and_since_read_as_empty(tmp_path, monkeypatch):
    """An unavailable-true entry with no reason/since fields flags with
    both read as ""."""
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    _write_overrides(tmp_path, {"tasks": {"T": {"unavailable": True}}})
    assert task_overrides.unavailable_tasks()["T"] == (
        task_overrides.TaskOverrideEntry(reason="", since=""))


def test_unknown_keys_stay_in_the_mapping(tmp_path, monkeypatch):
    """Keys unknown to the dataset registry STAY in the mapping — the
    file is task-scoped but the loader never joins against a registry;
    consumers ignore unknown keys structurally (a model key in the file
    affects nothing)."""
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    _write_overrides(tmp_path, {"tasks": {
        "not-a-task-key": {"unavailable": True, "reason": "x",
                           "since": "2026-10-27"},
        "some-model-name": {"unavailable": True, "reason": "y",
                            "since": "2026-10-27"},
    }})
    assert set(task_overrides.unavailable_tasks()) == {
        "not-a-task-key", "some-model-name"}


def test_multiple_entries_all_flag(tmp_path, monkeypatch):
    """Every flagged key lands in the mapping with its own entry."""
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    _write_overrides(tmp_path, {"tasks": {
        "T__one": {"unavailable": True, "reason": "r1", "since": "d1"},
        "T__two": {"unavailable": True, "reason": "r2", "since": "d2"},
        "T__three": {"unavailable": False},
    }})
    loaded = task_overrides.load_task_overrides()
    assert set(loaded.unavailable) == {"T__one", "T__two"}
    assert loaded.unavailable["T__two"].reason == "r2"
    assert loaded.unavailable["T__one"].since == "d1"


def test_unknown_top_level_keys_are_ignored(tmp_path, monkeypatch):
    """A schema-version envelope or any other top-level key is ignored
    (only ``tasks`` is read) — the directories_config key-tolerance
    idiom."""
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(tmp_path))
    _write_overrides(tmp_path, {
        "schema_version": 1,
        "tasks": {"T": {"unavailable": True, "reason": "r", "since": "s"}},
    })
    assert set(task_overrides.unavailable_tasks()) == {"T"}
