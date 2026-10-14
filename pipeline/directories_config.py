"""
directories_config.py — the ONE shared startup config for run-artifact
directories (261014-f4w, F4W-01).

A user-owned ``directories.json`` under the XDG CONFIG root
(``~/.config/dnallmmark/directories.json`` on Linux) carries up to five
directory keys — ``model_root`` / ``dataset_root`` / ``output_root`` /
``log_dir`` / ``cache_dir`` — that make the storage-root overrides of
261014-c2l (plus this task's ``--log_dir`` and the sweep's
``--output-root``) persistent for BARE ``run_sweep.py`` /
``run_finetune.py`` invocations: a multi-day sweep relaunch no longer
re-types the flags, and the slot-4 save action (Task 2) writes the file
the operators edit by hand.

Contract (locked decisions):

- **Precedence** (F4W-01, ONE merge point consumed by both scripts):
  explicit CLI flag > file key > built-in default. ``effective()``
  implements the first two steps; the built-in literal stays at each
  consumer (ADD-ALONGSIDE, the 261014-c2l precedent — never promote the
  default into this module).
- **Byte-identity when absent**: with NO file and NO flags, every
  touched path resolves byte-identically to today — an absent file
  returns ``{}``, an absent key contributes nothing, and the consumers'
  default branches keep their exact current expressions. Existing
  default-path tests stay green unmodified.
- **D-10 coexistence (hand-rolled resolver)**: this module resolves the
  config root with the SAME conventions as ``tui/services/settings.py``
  (``DNALLMMARK_TUI_CONFIG_DIR`` whole-dir override, empty = unset >
  ``XDG_CONFIG_HOME`` / dnallmmark > ``~/.config`` / dnallmmark) but
  hand-rolled on the stdlib — ``platformdirs`` stays OUT of the
  pipeline (stdlib purity is load-bearing; the registry_loader D-07
  precedent). The TUI write path (``settings.atomic_write`` over
  ``platformdirs``) and this read path resolve the SAME file by design
  — the same-root agreement is test-pinned.
- **Fail-loud tolerance policy** (the registry_loader T-07-04
  precedent): a PRESENT but malformed file (invalid JSON, non-dict top
  level, unreadable) raises ``SystemExit`` naming the path — never a
  silently-ignored corrupt file, which would silently redirect a
  multi-day run to the wrong roots (the wrong-root hazard class this
  codebase treats as worst-case). The DISPLAY twin
  ``load_directories_tolerant`` returns ``{}`` on ANY failure instead:
  display surfaces degrade, and a corrupt file self-heals on the next
  slot-4 save (the write is a whole-file replace).
- **Key tolerance**: each of the five known keys is read only as a
  non-empty stripped str (a whitespace-only or empty value = the key is
  absent); non-str values are dropped; unknown top-level keys (a
  ``schema_version`` envelope included) are ignored.

Stdlib only (json/os/pathlib — ``SystemExit`` is a builtin, no ``sys``
import), so every lane (dev/CI/GPU) and the TUI services tier can
import this module: as a sibling module from run_sweep/run_finetune
(pipeline/ on sys.path at interpreter startup), and as a top-level
module from the TUI/tests via the existing pipeline/ sys.path root (the
registry_loader import mechanics).
"""

import json
import os
from pathlib import Path

#: The single file name under the config root (the TUI write seam writes
#: exactly this name — the same-root pin).
DIRECTORIES_FILE_NAME = "directories.json"

#: The frozen five-key vocabulary and the canonical order every consumer
#: shares (the slot-1 storage overview and the slot-4 save document both
#: iterate this tuple; keys outside it are ignored on load).
DIRECTORY_KEYS = (
    "model_root",
    "dataset_root",
    "output_root",
    "log_dir",
    "cache_dir",
)


def config_dir():
    """Resolve the user-owned config root holding ``directories.json``.

    Resolution order (the ``tui/services/settings.py`` conventions,
    hand-rolled — platformdirs deliberately NOT imported, D-10):

    1. ``DNALLMMARK_TUI_CONFIG_DIR`` — overrides the ENTIRE directory
       (no suffix is appended; test injection points a tmp_path here
       directly). An empty value is treated as unset.
    2. ``XDG_CONFIG_HOME`` — joined with ``dnallmmark``.
    3. ``~/.config`` — joined with ``dnallmmark`` (the platformdirs
       default path on Linux).

    Returns:
        Path: the config root (may not exist — absence is the
        byte-identity-when-absent case).
    """
    override = os.environ.get("DNALLMMARK_TUI_CONFIG_DIR")
    if override:
        return Path(override)
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "dnallmmark"
    return Path.home() / ".config" / "dnallmmark"


def config_path():
    """The ``directories.json`` location under the resolved config root.

    Returns:
        Path: ``config_dir() / DIRECTORIES_FILE_NAME`` — the SAME file
        the TUI's slot-4 save action writes (the D-10 same-root pin;
        agreement with ``tui.services.settings.config_dir()`` is
        test-pinned).
    """
    return config_dir() / DIRECTORIES_FILE_NAME


def _parse_directories(raw, path):
    """Validate a parsed JSON document against the five-key vocabulary.

    Args:
        raw: the parsed JSON value (any type — a non-dict top level is
            the malformed case).
        path (Path): the file the value came from (error naming).

    Returns:
        dict[str, str]: the known keys with non-empty stripped str
        values (empty/whitespace/non-str values dropped; unknown keys
        ignored).

    Raises:
        SystemExit: the top level is not a JSON object (naming the
        path and the actual type — the fail-loud policy).
    """
    if not isinstance(raw, dict):
        raise SystemExit(
            f"[Error] directories config file {path} top level must be "
            f"a JSON object mapping directory keys to path strings, got "
            f"{type(raw).__name__}"
        )
    directories: dict[str, str] = {}
    for key in DIRECTORY_KEYS:
        value = raw.get(key)
        if not isinstance(value, str):
            continue  # non-str values are dropped (never coerced)
        stripped = value.strip()
        if stripped:
            directories[key] = stripped
    return directories


def load_directories(path=None):
    """Load the strict startup config (the pipeline consumers' read).

    Missing file -> ``{}`` (the byte-identity case). A PRESENT but
    malformed file raises ``SystemExit`` naming the path — a corrupt
    file must abort the child at startup, never silently redirect a
    multi-day run to the wrong roots (the T-07-04 fail-loud
    precedent).

    Args:
        path: an explicit file path; None resolves ``config_path()``.

    Returns:
        dict[str, str]: the five-key vocabulary subset actually present
        (values stripped non-empty; see ``_parse_directories``).

    Raises:
        SystemExit: the file exists but is unreadable, invalid JSON, or
        not a JSON object — each error names the path and the reason.
    """
    target = config_path() if path is None else Path(path)
    if not target.is_file():
        return {}
    try:
        with open(target, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SystemExit(
            f"[Error] directories config file {target} is not readable "
            f"JSON: {exc}"
        ) from exc
    return _parse_directories(raw, target)


def load_directories_tolerant(path=None):
    """The DISPLAY twin of ``load_directories`` — ``{}`` on ANY failure.

    The TUI's mount-time seeding and the slot-1 storage overview
    degrade to defaults when the file is missing OR corrupt (display
    surfaces never crash on a bad file); the pipeline consumers stay
    fail-loud. A corrupt file self-heals on the next slot-4 save — the
    write is a whole-file atomic replace, never a merge.

    Args:
        path: an explicit file path; None resolves ``config_path()``.

    Returns:
        dict[str, str]: the present known keys, or ``{}`` on any
        failure (missing file, unreadable, invalid JSON, non-dict top
        level).
    """
    try:
        return load_directories(path)
    except SystemExit:
        return {}


def effective(cli_value, key, path=None):
    """The precedence merge: explicit CLI flag > file key > (None).

    Implemented ONCE and consumed by both scripts (F4W-01) — the
    built-in default stays at each consumer's site (ADD-ALONGSIDE):
    a ``None`` return means "the consumer's own default branch
    governs", keeping the absent-everywhere path byte-identical to
    today.

    Args:
        cli_value (str | None): the parsed argparse value (None = the
            flag was absent).
        key (str): one of ``DIRECTORY_KEYS``.
        path: an explicit config file path; None resolves
            ``config_path()``.

    Returns:
        str | None: the CLI value when set, else the strict file value
        for the key, else None.
    """
    if cli_value is not None:
        return cli_value
    return load_directories(path).get(key)
