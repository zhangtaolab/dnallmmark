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
  an omit-on-failure fallback; ``derive_about_data`` additionally wraps
  every probe call so even an unexpected raise degrades to the neutral
  value (the screen composes on any machine).
- Auto-Default #13 (honest machine-derivable values only): every value
  traces to a real source on the machine; the 里程碑阶段 row is the one
  static milestone constant (rendered from ``tui/strings.py`` by the
  screen — it is milestone metadata, not a machine probe).
- The deps vocabulary is the five locked names (textual / platformdirs /
  jsonschema / numpy / torch) — torch is legitimately absent on CPU
  machines and renders 未安装 there.
- The official counts read the committed registry files DIRECTLY through
  ``artifact_loader`` (tolerant, official-only): the Phase 7 loader's
  merged view is the pipeline's authority, but the 官方 row must stay
  62/50 when customs are landed, and a display probe must degrade to 0
  where the loader would propagate an OSError (the fail-loud loader
  contract stays untouched — this module never routes through it).

ZERO textual imports (the services-tier invariant declared in
``tui/services/__init__.py``; locked by ``tests/tui/test_import_lock.py``).
Dependencies: stdlib (tomllib/subprocess/importlib.metadata) +
``artifact_loader`` (tolerant reads) + ``registry_loader`` (the official
file-name constants — imported, never retyped) +
``tui.services.custom_entries`` (the 09-01 store) +
``tui.services.registries`` (the n_audit seam).
"""

import importlib.metadata
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import artifact_loader  # top-level module (pipeline/ sys.path root, D-19)
import registry_loader  # top-level module (pipeline/ sys.path root, D-02)

from tui.services import custom_entries, registries
from tui.services.registries import RegistryCounts

# ===== Locations (resolved from this module's own file, never CWD) =====

REPO_ROOT = Path(__file__).resolve().parents[2]
#: The official registries' directory (names imported from the loader).
_PIPELINE_DIR = REPO_ROOT / "pipeline"
#: The repo's own version source (the 软件版本 row).
_PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"

# ===== The five-name dependency probe vocabulary =====

PROBED_PACKAGES = ("textual", "platformdirs", "jsonschema", "numpy", "torch")

#: The 仓库地址 row value (English verbatim, I18N-01).
REPO_URL = "https://github.com/zhangtaolab/dnallmmark"

#: T-09-08: the git probe is bounded — never a console-blocking subprocess.
GIT_PROBE_TIMEOUT_SECONDS = 3.0

#: The neutral counts value — a module-level frozen instance (NamedTuple,
#: immutable) so the dataclass default is a constant, not a call.
_ZERO_COUNTS = RegistryCounts(0, 0)


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
    official_counts: RegistryCounts = _ZERO_COUNTS
    custom_counts: "tuple[int, int]" = (0, 0)
    n_audit_present: bool = False
    deps: "dict[str, str | None]" = field(default_factory=dict)
    repo_url: str = REPO_URL


def software_version(pyproject_path=None) -> str:
    """The pyproject ``[project] version``, read tolerantly.

    Args:
        pyproject_path: the pyproject.toml to read; None means the repo's
            own (tests inject a tmp file).

    Returns:
        str: the version string, or ``""`` when the file is missing,
        unparseable, lacks a ``[project] version``, or the field is not a
        string (the repo's missing-value convention — never a raise).
    """
    path = (
        Path(pyproject_path) if pyproject_path is not None
        else _PYPROJECT_PATH
    )
    try:
        with open(path, "rb") as handle:
            document = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return ""
    project = document.get("project")
    if not isinstance(project, dict):
        return ""
    version = project.get("version")
    return version if isinstance(version, str) else ""


def git_short_sha(repo_root=None) -> "str | None":
    """The short HEAD sha via a bounded, read-only git probe (T-09-08).

    LIST argv (never a shell), ``rev-parse --short HEAD`` only, a short
    timeout, and an omit-on-failure fallback: a git-less machine, a
    non-repo directory, or a timeout each yield None — the value is
    simply omitted from the 软件版本 row.

    Args:
        repo_root: the directory to probe; None means the repo root.

    Returns:
        str | None: the short sha, or None when unresolvable.
    """
    root = Path(repo_root) if repo_root is not None else REPO_ROOT
    try:
        process = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            check=False,  # a non-repo exit is the omit path, not an error
            text=True,
            timeout=GIT_PROBE_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if process.returncode != 0:
        return None
    sha = process.stdout.strip()
    return sha or None


def package_version(package: str) -> "str | None":
    """One installed package's version via importlib.metadata.

    Args:
        package (str): the distribution name to probe.

    Returns:
        str | None: the version string, or None when the package is not
        installed on this machine (the 未安装 row source — e.g. torch on
        a CPU machine).
    """
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None
    except Exception:  # noqa: BLE001 — T-09-08: any probe failure degrades
        return None


def official_counts() -> RegistryCounts:
    """The OFFICIAL-only registry entry counts (62/50 committed).

    Reads the official registry files directly through
    ``artifact_loader`` (the tolerant None sentinel): the 官方 row must
    not count a landed custom overlay (the merged view would double-count
    customs next to the separate 自定义 segment), and a display probe
    must degrade to 0 rather than propagate the loader's fail-loud
    OSError. See the module docstring for why this is a display probe,
    not a second loader.
    """
    models = artifact_loader.load_json_artifact(
        _PIPELINE_DIR / registry_loader.MODELS_INFO_NAME)
    datasets = artifact_loader.load_json_artifact(
        _PIPELINE_DIR / registry_loader.DATASETS_INFO_NAME)
    return RegistryCounts(
        models=len(models) if isinstance(models, dict) else 0,
        datasets=len(datasets) if isinstance(datasets, dict) else 0,
    )


def custom_counts() -> "tuple[int, int]":
    """The landed custom-entry counts via the 09-01 direct read.

    The MANAGEMENT-VIEW read (``custom_entries.read_entries`` — disabled
    entries included, visible = counted); absence of the user-owned files
    is the ``(0, 0)`` empty edge, and an unreadable file degrades the
    same way (tolerance, never a raise).
    """
    models, _ = custom_entries.read_entries(custom_entries.KIND_MODELS)
    datasets, _ = custom_entries.read_entries(custom_entries.KIND_DATASETS)
    return len(models), len(datasets)


def n_audit_present() -> bool:
    """True when the committed n_audit.json presence artifact reads.

    The same seam the SEL-04 presence column uses (the 08-04 service's
    tolerant load); deterministic — no clock, no machine state beyond the
    committed artifact.
    """
    return registries.load_n_audit() is not None


def derive_about_data(pyproject_path=None, repo_root=None) -> AboutData:
    """Aggregate every probe into one ``AboutData`` — never raises.

    Every probe call is wrapped (T-09-08): even an unexpected raise inside
    a probe degrades to that field's neutral value so the aggregate still
    returns and the screen composes on any machine.

    Args:
        pyproject_path: optional pyproject.toml override (test injection).
        repo_root: optional git-probe root override (test injection).

    Returns:
        AboutData: the complete snapshot.
    """

    def _safe(probe, neutral):
        try:
            return probe()
        except Exception:  # noqa: BLE001 — T-09-08 absorb-and-degrade
            return neutral

    deps: dict[str, str | None] = {}
    for package in PROBED_PACKAGES:
        deps[package] = _safe(
            lambda name=package: package_version(name), None)

    return AboutData(
        software_version=_safe(
            lambda: software_version(pyproject_path), ""),
        git_sha=_safe(lambda: git_short_sha(repo_root), None),
        official_counts=_safe(official_counts, RegistryCounts(0, 0)),
        custom_counts=_safe(custom_counts, (0, 0)),
        n_audit_present=_safe(n_audit_present, False),
        deps=deps,
        repo_url=REPO_URL,
    )
