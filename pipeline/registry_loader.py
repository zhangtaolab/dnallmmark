"""
registry_loader.py — official + custom registry overlay (Phase 7,
CUST-05 / D-06..D-08).

One shared merge seam for the unified JSON registries: every registry
consumer loads through this module, so the official view and the optional
user-owned custom overlay can never diverge across call sites (D-08
single-source precedent; the five load sites are run_sweep x3,
run_finetune module level x1, script/audit_n_frequencies.py x1).

Contract (locked decisions):
- **byte-identity when absent** (D-06): with no custom file present, the
  OFFICIAL dict object is returned as-is, untouched — behavior identical
  to the former per-site ``json.load`` calls, every existing test green
  unmodified.
- **custom files live OUTSIDE the repo** (binding constraint 11): the
  overlay directory is user-owned (``~/.config/dnallmmark`` by default);
  the official files under ``pipeline/`` are NEVER written by any flow
  through this loader — it is strictly read-only over both sides.
- **collision fail-fast** (D-08): a custom key equal to an official key
  exits naming the key AND the paths of both files — custom entries may
  only ADD keys, never shadow official ones.
- **fail-loud on malformed** (T-07-04): a present-but-malformed custom
  file (invalid JSON, non-object top level, unreadable) is a hard error
  naming the file — never a silent skip (宁可噪声不可静默少计).
- **official-file failures propagate** (D-08 导入时序不变): a missing
  official file raises OSError uncaught. ``run_finetune.py`` loads the
  registries at MODULE level and its crash-on-missing import-time
  behavior is contract — the loader must not absorb it.
- **no cache** (D-18 discipline): callers re-load per use; the loader is
  stateless and multi-process safe.

Path resolution (D-07 — hand-rolled, platformdirs deliberately NOT
imported): platformdirs is absent from every CPU-side dependency group
(only a GPU-lane transitive of jupyter_core/setuptools/wandb, verified in
Phase 7 research Pitfall 2) and ROADMAP binding constraint 10 reserves it
for the Phase 8 [tui] group, so importing it here would crash the CI dev
lane. This resolver yields the identical Linux path; Phase 8 may
consolidate onto platformdirs behind this same seam.

Stdlib only (json/os/pathlib — ``SystemExit`` is raised as a builtin, no
``sys`` import), so every lane (dev/CI/GPU) can import this module.
"""

import json
import os
from pathlib import Path

_MODULE_DIR = Path(__file__).resolve().parent

MODELS_INFO_NAME = "models_info.json"
DATASETS_INFO_NAME = "datasets_info.json"
CUSTOM_MODELS_NAME = "custom_models.json"
CUSTOM_DATASETS_NAME = "custom_datasets.json"


def custom_registry_dir():
    """Resolve the user-owned custom overlay directory (D-07).

    Resolution order:

    1. ``DNALLMMARK_CUSTOM_REGISTRY_DIR`` — overrides the ENTIRE custom
       directory (the whole-dir override reading of D-07 覆盖整个目录;
       no ``dnallmmark`` suffix is appended to it — test injection points
       a tmp_path here directly). An empty value is treated as unset.
    2. ``XDG_CONFIG_HOME`` — joined with ``dnallmmark``.
    3. ``~/.config`` — joined with ``dnallmmark`` (the platformdirs
       default path on Linux; see the module docstring for why the
       platformdirs library itself is not imported here).

    Returns:
        Path: the custom overlay directory (may not exist — absence is
        the D-06 byte-identity case).
    """
    override = os.environ.get("DNALLMMARK_CUSTOM_REGISTRY_DIR")
    if override:
        return Path(override)
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "dnallmmark"
    return Path.home() / ".config" / "dnallmmark"


def _load_registry(official_path, custom_path):
    """Load one registry: official file, then the optional custom overlay.

    Args:
        official_path (Path): the official registry file. Missing/unready
            files raise OSError uncaught — the run_finetune import-time
            contract (the loader never absorbs official-file failures).
        custom_path (Path): the user-owned custom overlay file. Absent ->
            the official dict object is returned untouched (D-06
            byte-identity).

    Returns:
        dict: the official registry, with custom entries merged in when
        the custom file exists (custom keys appended in file order).

    Raises:
        OSError: the OFFICIAL file is missing/unreadable (propagates).
        SystemExit: the custom file exists but is malformed (invalid
        JSON, non-object top level, unreadable), or a custom key collides
        with an official key — each error names the file(s) involved.
    """
    with open(official_path, "r", encoding="utf-8") as f:
        registry = json.load(f)
    if not custom_path.is_file():
        return registry

    try:
        with open(custom_path, "r", encoding="utf-8") as f:
            custom = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(
            f"[Error] custom registry file {custom_path} is not readable "
            f"JSON: {exc}"
        ) from exc
    if not isinstance(custom, dict):
        raise SystemExit(
            f"[Error] custom registry file {custom_path} top level must "
            f"be a JSON object mapping entry keys to entry objects, got "
            f"{type(custom).__name__}"
        )
    for key in custom:
        if key in registry:
            raise SystemExit(
                f"[Error] custom registry key '{key}' collides with an "
                f"official registry key (custom entries may only ADD "
                f"keys, never shadow official ones) — custom file: "
                f"{custom_path}; official file: {official_path}"
            )
    registry.update(custom)
    return registry


def load_models_registry(registry_dir=None):
    """Load the models registry: official + optional custom overlay.

    Args:
        registry_dir (Path | str | None): directory holding the official
            ``models_info.json``. ``None`` (the run_finetune module-level
            convention) defaults to this module's own directory — the
            ``pipeline/`` dir, where the official registries live.

    Returns:
        dict: the merged registry (official dict object as-is when no
        custom overlay is present).
    """
    base = _MODULE_DIR if registry_dir is None else Path(registry_dir)
    return _load_registry(
        base / MODELS_INFO_NAME,
        custom_registry_dir() / CUSTOM_MODELS_NAME,
    )


def load_datasets_registry(registry_dir=None):
    """Load the datasets registry: official + optional custom overlay.

    Args:
        registry_dir (Path | str | None): directory holding the official
            ``datasets_info.json``. ``None`` defaults to this module's
            own directory (see ``load_models_registry``).

    Returns:
        dict: the merged registry (official dict object as-is when no
        custom overlay is present).
    """
    base = _MODULE_DIR if registry_dir is None else Path(registry_dir)
    return _load_registry(
        base / DATASETS_INFO_NAME,
        custom_registry_dir() / CUSTOM_DATASETS_NAME,
    )
