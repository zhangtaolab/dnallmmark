"""
Tier-1 suite for the about service (Phase 9, 09-03, D-13 slot 6 + T-09-08).

Pins the tolerant derivations behind the 关于 screen:

- every probe fails soft (a missing pyproject, an absent package, a
  git-less machine, an unreadable n_audit each yield their neutral value
  and the aggregate still returns — the screen composes on any machine;
  the T-09-08 mitigation);
- official counts are OFFICIAL-only (62/50 against the committed
  registries — never the overlay-merged view, which would count customs
  twice next to the separate 自定义 segment);
- custom counts come from the 09-01 store's direct management read
  (disabled customs included — visible = counted);
- the deps probe maps package → version-or-None with absent → None (the
  screen renders 未安装);
- the git sha probe is a LIST-argv read-only rev-parse with a short
  timeout and an omit-on-failure fallback (never a shell, never a block).

Isolation (the 09-01 discipline): DNALLMMARK_TUI_CONFIG_DIR (and
DNALLMMARK_CUSTOM_REGISTRY_DIR, belt-and-braces) are pinned at tmp_path —
the real ~/.config/dnallmmark is never read.
"""

import importlib.metadata
import json
import subprocess
from pathlib import Path

import tui.services.about as about
import tui.services.registries as registries
from tui.services.about import AboutData
from tui.services.registries import RegistryCounts
from tui.strings import (
    ABOUT_DEP_ABSENT,
    ABOUT_ROW_DATA,
    ABOUT_ROW_DEPS,
    ABOUT_ROW_MILESTONE,
    ABOUT_ROW_REPO,
    ABOUT_ROW_SOFTWARE,
    ABOUT_TITLE,
)


# =====================================================================
# Isolation helper (the 09-01 discipline)
# =====================================================================

def _pin_config_roots(monkeypatch, tmp_path):
    """Pin both config-root env overrides at tmp_path (never the real home)."""
    config = tmp_path / "config"
    config.mkdir(exist_ok=True)
    monkeypatch.setenv("DNALLMMARK_TUI_CONFIG_DIR", str(config))
    # belt-and-braces: even if a probe ever routed through registry_loader,
    # the overlay resolves to an empty tmp dir (absent file = no overlay)
    monkeypatch.setenv(
        "DNALLMMARK_CUSTOM_REGISTRY_DIR", str(tmp_path / "custom-empty"))
    return config


def _write_custom_registries(config, models, datasets):
    """Write user-owned custom registry files under the pinned config root."""
    (config / "custom_models.json").write_text(
        json.dumps(models), encoding="utf-8")
    (config / "custom_datasets.json").write_text(
        json.dumps(datasets), encoding="utf-8")


# =====================================================================
# software_version — pyproject [project] version, tolerant
# =====================================================================

def test_software_version_reads_pyproject_project_version(tmp_path):
    """The version comes from pyproject.toml [project] version."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "x"\nversion = "9.9.9"\n', encoding="utf-8")
    assert about.software_version(pyproject) == "9.9.9"


def test_software_version_missing_file_is_empty(tmp_path):
    """A missing pyproject yields the neutral empty string, never a raise."""
    assert about.software_version(tmp_path / "nope.toml") == ""


def test_software_version_invalid_toml_is_empty(tmp_path):
    """Unparseable TOML yields the neutral empty string."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project\nbroken", encoding="utf-8")
    assert about.software_version(pyproject) == ""


def test_software_version_missing_project_table_or_field_is_empty(tmp_path):
    """No [project] table / no version field / non-string version → ""."""
    no_table = tmp_path / "a.toml"
    no_table.write_text("[tool.x]\nkey = 1\n", encoding="utf-8")
    assert about.software_version(no_table) == ""

    no_version = tmp_path / "b.toml"
    no_version.write_text('[project]\nname = "x"\n', encoding="utf-8")
    assert about.software_version(no_version) == ""

    non_string = tmp_path / "c.toml"
    non_string.write_text("[project]\nversion = 2\n", encoding="utf-8")
    assert about.software_version(non_string) == ""


# =====================================================================
# git_short_sha — LIST argv, short timeout, omit on failure (T-09-08)
# =====================================================================

def test_git_short_sha_returns_short_sha_on_success(monkeypatch, tmp_path):
    """A resolved HEAD yields its short sha; the argv is a read-only LIST."""
    calls = {}

    def fake_run(argv, **kwargs):
        calls["argv"] = argv
        calls["kwargs"] = kwargs
        return subprocess.CompletedProcess(argv, 0, stdout="a8dba7c\n", stderr="")

    monkeypatch.setattr(about.subprocess, "run", fake_run)
    assert about.git_short_sha(tmp_path) == "a8dba7c"
    # LIST argv, read-only rev-parse, short timeout (T-09-08)
    assert calls["argv"] == [
        "git", "-C", str(tmp_path), "rev-parse", "--short", "HEAD"]
    assert calls["kwargs"]["timeout"] == about.GIT_PROBE_TIMEOUT_SECONDS


def test_git_short_sha_nonzero_exit_returns_none(monkeypatch, tmp_path):
    """git present but not a repo (exit 1) → None, never a raise."""
    def fake_run(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="fatal: …")

    monkeypatch.setattr(about.subprocess, "run", fake_run)
    assert about.git_short_sha(tmp_path) is None


def test_git_short_sha_missing_git_or_timeout_returns_none(monkeypatch, tmp_path):
    """git absent (OSError) or timed out → None (omit-on-failure fallback)."""
    def raise_oserror(argv, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr(about.subprocess, "run", raise_oserror)
    assert about.git_short_sha(tmp_path) is None

    def raise_timeout(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, about.GIT_PROBE_TIMEOUT_SECONDS)

    monkeypatch.setattr(about.subprocess, "run", raise_timeout)
    assert about.git_short_sha(tmp_path) is None


# =====================================================================
# package_version — importlib.metadata probe, absent → None
# =====================================================================

def test_package_version_absent_package_returns_none():
    """A package no machine has probes to None (the 未安装 row source)."""
    assert about.package_version("dnallmmark-no-such-package-xyz") is None


def test_package_version_present_package_returns_metadata_version():
    """An installed package probes to its importlib.metadata version."""
    assert about.package_version("pytest") == (
        importlib.metadata.version("pytest"))


def test_probed_packages_vocabulary_is_the_five_locked_names():
    """The probe set is exactly textual/platformdirs/jsonschema/numpy/torch."""
    assert about.PROBED_PACKAGES == (
        "textual", "platformdirs", "jsonschema", "numpy", "torch")


# =====================================================================
# counts — official-only 62/50 + custom via the 09-01 store
# =====================================================================

def test_official_counts_committed_registries_are_62_50():
    """Official counts are the committed registries' own entry counts."""
    assert about.official_counts() == RegistryCounts(models=62, datasets=50)


def test_official_counts_stay_official_with_custom_overlay_landed(
        monkeypatch, tmp_path):
    """A landed custom entry must NOT inflate the 官方 counts — the overlay-
    merged view would double-count it next to the separate 自定义 segment."""
    config = _pin_config_roots(monkeypatch, tmp_path)
    _write_custom_registries(
        config,
        models={"my-lm": {"Model_name": "my-lm"}},
        datasets={"my-ds": {"Dataset_name": "my-ds", "Train": 3},
                  "my-ds-2": {"Dataset_name": "my-ds-2", "Train": 4}},
    )
    assert about.official_counts() == RegistryCounts(models=62, datasets=50)


def test_custom_counts_read_the_user_owned_store(monkeypatch, tmp_path):
    """自定义 counts come from the 09-01 direct read (all landed entries)."""
    config = _pin_config_roots(monkeypatch, tmp_path)
    assert about.custom_counts() == (0, 0)  # absent files — the empty edge
    _write_custom_registries(
        config,
        models={"my-lm": {"Model_name": "my-lm"},
                "my-lm-off": {"Model_name": "my-lm-off", "enabled": False}},
        datasets={"my-ds": {"Dataset_name": "my-ds", "Train": 3},
                  "my-ds-2": {"Dataset_name": "my-ds-2", "Train": 4}},
    )
    # visible = counted: disabled entries stay in the landed total
    assert about.custom_counts() == (2, 2)


# =====================================================================
# n_audit presence
# =====================================================================

def test_n_audit_present_true_against_committed_artifact():
    """The committed n_audit.json satisfies presence (deterministic, no clock)."""
    assert about.n_audit_present() is True


def test_n_audit_present_false_when_artifact_missing(monkeypatch):
    """An absent/unreadable n_audit probes False — degrade, never crash."""
    monkeypatch.setattr(registries, "load_n_audit", lambda: None)
    assert about.n_audit_present() is False


# =====================================================================
# repo url + copy constants
# =====================================================================

def test_repo_url_constant():
    """The repo row renders the project URL constant."""
    assert about.REPO_URL == "https://github.com/zhangtaolab/dnallmmark"


def test_about_copy_constants_are_the_ui_spec_wording():
    """The ABOUT_ block is the 09-UI-SPEC Copywriting wording verbatim."""
    assert ABOUT_TITLE == "关于 DNALLM-Mark"
    assert (ABOUT_ROW_SOFTWARE, ABOUT_ROW_DATA, ABOUT_ROW_MILESTONE,
            ABOUT_ROW_DEPS, ABOUT_ROW_REPO) == (
        "软件版本", "数据版本", "里程碑阶段", "依赖版本", "仓库地址")
    assert ABOUT_DEP_ABSENT == "未安装"


# =====================================================================
# derive_about_data — the aggregate (always composes)
# =====================================================================

def test_derive_about_data_aggregates_every_probe(
        monkeypatch, tmp_path):
    """The aggregate carries every probe's value over injected roots."""
    _pin_config_roots(monkeypatch, tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nversion = "3.2.1"\n', encoding="utf-8")
    monkeypatch.setattr(
        about.subprocess, "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 0, stdout="beef42\n", stderr=""))

    data = about.derive_about_data(pyproject_path=pyproject,
                                   repo_root=tmp_path)
    assert isinstance(data, AboutData)
    assert data.software_version == "3.2.1"
    assert data.git_sha == "beef42"
    assert data.official_counts == RegistryCounts(62, 50)
    assert data.custom_counts == (0, 0)
    assert data.n_audit_present is True
    assert data.repo_url == about.REPO_URL
    # every probed package carries a version-or-None entry, probed order
    assert tuple(data.deps) == about.PROBED_PACKAGES
    assert data.deps["textual"] == importlib.metadata.version("textual")


def test_derive_about_data_never_raises_into_compose(monkeypatch, tmp_path):
    """T-09-08: every probe raising is absorbed — the aggregate still
    returns with neutral values (the screen composes on any machine)."""
    _pin_config_roots(monkeypatch, tmp_path)

    def boom(*args, **kwargs):
        raise RuntimeError("probe exploded")

    monkeypatch.setattr(about, "software_version", boom)
    monkeypatch.setattr(about, "git_short_sha", boom)
    monkeypatch.setattr(about, "official_counts", boom)
    monkeypatch.setattr(about, "custom_counts", boom)
    monkeypatch.setattr(about, "n_audit_present", boom)
    monkeypatch.setattr(about, "package_version", boom)

    data = about.derive_about_data()
    assert data.software_version == ""
    assert data.git_sha is None
    assert data.official_counts == RegistryCounts(0, 0)
    assert data.custom_counts == (0, 0)
    assert data.n_audit_present is False
    assert data.deps == {}
    assert data.repo_url == about.REPO_URL


def test_derive_about_data_default_root_is_the_repo_pyproject():
    """No injected root: the repo's own pyproject.toml is read (0.7.1)."""
    data = about.derive_about_data()
    repo_pyproject = Path(about.__file__).resolve().parents[2] / "pyproject.toml"
    assert repo_pyproject.is_file()
    assert data.software_version == "0.7.1"
