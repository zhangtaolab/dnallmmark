"""
settings — XDG roots + atomic writes for the TUI (Phase 8, 08-04, D-04).

The persistence-location service: every Phase 8+ module that reads or
writes user-local state resolves its roots HERE, so the D-04 state/config
split has exactly one implementation.

Contract (locked decisions):

- D-04 (state/config split): env-check results (regenerable machine
  state) resolve to the XDG STATE root — ``platformdirs
  user_state_dir("dnallmmark")``, Linux ``~/.local/state/dnallmmark``;
  user-owned presets/templates/settings (hand-authored config) resolve
  to the XDG CONFIG root — ``user_config_dir("dnallmmark")``, Linux
  ``~/.config/dnallmmark`` (the same root as the Phase 7 custom
  registries). Check results never persist under the config root and
  presets never persist under the state root — the split is absolute.
- Whole-dir env overrides (the Phase 7 ``DNALLMMARK_CUSTOM_REGISTRY_DIR``
  precedent, ``pipeline/registry_loader.py:57-81``):
  ``DNALLMMARK_TUI_STATE_DIR`` / ``DNALLMMARK_TUI_CONFIG_DIR`` override
  their ENTIRE root directory when set to a non-empty value; an EMPTY
  value is treated as unset. Tests point both at tmp_path subdirs — no
  test ever touches the real XDG home.
- D-10: this service resolves through the platformdirs LIBRARY. The
  pipeline-side hand-rolled env>XDG>home resolver in registry_loader
  stays untouched (pipeline stdlib purity is load-bearing); the two
  resolvers coexist by design and consolidation is permanently deferred.
- T-08-03 (atomic writes): every persistence site writes through
  ``atomic_write`` — a tmp sibling plus ``os.replace`` — so a reader can
  never observe a torn file; ``artifact_loader``'s None sentinel converts
  any residual damage into a cache miss, never a crash.

ZERO textual imports (the services-tier invariant declared in
``tui/services/__init__.py``; locked by
``tests/tui/test_import_lock.py``). Dependencies: stdlib + platformdirs.
"""

import os
from pathlib import Path

from platformdirs import user_config_dir, user_state_dir

APP_NAME = "dnallmmark"
STATE_DIR_ENV = "DNALLMMARK_TUI_STATE_DIR"
CONFIG_DIR_ENV = "DNALLMMARK_TUI_CONFIG_DIR"

#: The persisted-language filename under the XDG state root — the ONE
#: definition (IN-02, quick-261016-hhx: the 08 review; EHC-1's persisted
#: language file). Consumed by ``tui/__main__``'s boot read and the
#: app's toggle write; a rename in one place must never silently break
#: the other (the toggle would persist a file the boot never loads).
LANGUAGE_FILE_NAME = "language.json"


def state_dir():
    """Resolve the XDG STATE root for regenerable machine state (D-04).

    Resolution order:

    1. ``DNALLMMARK_TUI_STATE_DIR`` — overrides the ENTIRE directory (no
       suffix is appended; test injection points a tmp_path here
       directly). An empty value is treated as unset.
    2. ``platformdirs.user_state_dir("dnallmmark")`` — Linux
       ``~/.local/state/dnallmmark``.

    Returns:
        Path: the state root (may not exist yet — ``atomic_write``
        creates parents on demand).
    """
    override = os.environ.get(STATE_DIR_ENV)
    if override:
        return Path(override)
    return Path(user_state_dir(APP_NAME))


def config_dir():
    """Resolve the XDG CONFIG root for user-owned files (D-04).

    Resolution order:

    1. ``DNALLMMARK_TUI_CONFIG_DIR`` — overrides the ENTIRE directory
       (empty value = unset, the same whole-dir precedent).
    2. ``platformdirs.user_config_dir("dnallmmark")`` — Linux
       ``~/.config/dnallmmark`` (the same root the Phase 7 custom
       registries live under).

    Returns:
        Path: the config root (may not exist yet — ``atomic_write``
        creates parents on demand).
    """
    override = os.environ.get(CONFIG_DIR_ENV)
    if override:
        return Path(override)
    return Path(user_config_dir(APP_NAME))


def atomic_write(path, text):
    """Atomically write ``text`` to ``path`` (tmp sibling + os.replace).

    Parent directories are created on demand — the XDG roots do not
    exist on a fresh machine until the first write. The tmp sibling is
    consumed by the replace itself; a crash between the tmp write and
    the replace can leave a ``.tmp`` file behind but can never leave a
    torn target (T-08-03 mitigation).

    Args:
        path: the destination file (str or os.PathLike).
        text: the complete file contents as a str (written UTF-8).
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, target)
