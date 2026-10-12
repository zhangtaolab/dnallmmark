"""
about — the 关于-screen derivation service (Phase 9, 09-03, D-13 slot 6).

Read-only, tolerant derivations for the five fixed about rows (软件版本 /
数据版本 / 里程碑阶段 / 依赖版本 / 仓库地址): software version from
pyproject.toml plus the git short sha, OFFICIAL-only registry counts
(62/50 — never the overlay-merged view, which would count customs twice
next to the separate 自定义 segment), custom counts via the 09-01 store's
direct management read, the n_audit 在场 signal, and per-package
dependency probes via importlib.metadata (absent → None, rendered 未安装
by the screen).

Contract (locked decisions):

- T-09-08 (tolerance): every probe fails soft — a missing pyproject, an
  absent package, a git-less machine, an unreadable n_audit each yield
  their neutral value and the aggregate still returns; no derivation can
  raise into compose or block the console. The git sha probe is a
  LIST-argv read-only ``rev-parse --short HEAD`` with a short timeout and
  an omit-on-failure fallback.
- Auto-Default #13 (honest machine-derivable values only): every value
  traces to a real source on the machine; the 里程碑阶段 row is the one
  static milestone constant (rendered from ``tui/strings.py`` by the
  screen — it is milestone metadata, not a machine probe).
- The deps vocabulary is the five locked names (textual / platformdirs /
  jsonschema / numpy / torch) — torch is legitimately absent on CPU
  machines and renders 未安装 there.

ZERO textual imports (the services-tier invariant declared in
``tui/services/__init__.py``; locked by ``tests/tui/test_import_lock.py``).
Dependencies: stdlib + ``artifact_loader`` (tolerant reads) +
``registry_loader`` (the official file-name constants) +
``tui.services.custom_entries`` (the 09-01 store) +
``tui.services.registries`` (the n_audit seam).

SKELETON (RED): the probes return their neutral values; derivations land
with the GREEN step.
"""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import registry_loader  # top-level module (pipeline/ sys.path root, D-02)

from tui.services.registries import RegistryCounts

# ===== Locations (resolved from this module's own file, never CWD) =====

REPO_ROOT = Path(__file__).resolve().parents[2]
#: The official registries' directory (names imported from the loader).
_PIPELINE_DIR = REPO_ROOT / "pipeline"

# ===== The five-name dependency probe vocabulary =====

PROBED_PACKAGES = ("textual", "platformdirs", "jsonschema", "numpy", "torch")

#: The 仓库地址 row value (English verbatim, I18N-01).
REPO_URL = "https://github.com/zhangtaolab/dnallmmark"

#: T-09-08: the git probe is bounded — never a console-blocking subprocess.
GIT_PROBE_TIMEOUT_SECONDS = 3.0


@dataclass(frozen=True)
class AboutData:
    """One complete about-screen snapshot — pure, label-safe data.

    Attributes:
        software_version: the pyproject ``[project] version`` (``""`` when
            unreadable — the repo's missing-value convention).
        git_sha: the short HEAD sha, or None when git is absent/not a repo.
        official_counts: the OFFICIAL registry entry counts (62/50 against
            the committed files; ``(0, 0)`` when even they are unreadable).
        custom_counts: ``(models, datasets)`` landed custom-entry counts
            from the 09-01 direct read (disabled included).
        n_audit_present: True when the committed n_audit artifact reads.
        deps: package → version-or-None over ``PROBED_PACKAGES`` order.
        repo_url: the constant 仓库地址 value.
    """

    software_version: str = ""
    git_sha: "str | None" = None
    official_counts: RegistryCounts = RegistryCounts(0, 0)
    custom_counts: "tuple[int, int]" = (0, 0)
    n_audit_present: bool = False
    deps: "dict[str, str | None]" = field(default_factory=dict)
    repo_url: str = REPO_URL


def software_version(pyproject_path=None) -> str:
    """The pyproject ``[project] version`` read tolerantly (skeleton)."""
    return ""


def git_short_sha(repo_root=None) -> "str | None":
    """The short HEAD sha via a bounded read-only git probe (skeleton)."""
    return None


def package_version(package: str) -> "str | None":
    """One package's installed version, None when absent (skeleton)."""
    return None


def official_counts() -> RegistryCounts:
    """The OFFICIAL-only registry entry counts (skeleton)."""
    return RegistryCounts(0, 0)


def custom_counts() -> "tuple[int, int]":
    """The landed custom-entry counts via the 09-01 store (skeleton)."""
    return (0, 0)


def n_audit_present() -> bool:
    """True when the committed n_audit artifact reads (skeleton)."""
    return False


def derive_about_data(pyproject_path=None, repo_root=None) -> AboutData:
    """Aggregate every probe into one AboutData (never raises, skeleton)."""
    return AboutData()
