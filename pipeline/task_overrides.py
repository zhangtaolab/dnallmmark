"""
task_overrides.py — the ONE tolerant reader over the user-owned
``task_overrides.json`` task-unavailability overlay (quick-261027-fyt).

A maintainer hand-authors ``task_overrides.json`` at the SAME config
root as ``directories.json`` (``~/.config/dnallmmark`` on Linux)
carrying temporary-unavailability flags per registry TASK key::

    {"tasks": {"<registry task key>": {"unavailable": true,
                                       "reason": "<free text>",
                                       "since": "<ISO date>"}}}

The live motivation was the GUE__fungi_species_20 x FungiHelixSeek
diagnosis (10k-token uniform sequences x a 263M MoE at the 32 GB
ceiling) — the maintainer ruled the MECHANISM must exist so a "this
task is unrunnable for now" verdict is ONE hand-edit, never a code
change, and never a hardcoded task name (the diagnosis is the
motivation, not a key in code). Deleting the entry (or the whole
file) restores the task EVERYWHERE on the next read — the file is the
ONLY state; no sweep artifact, registry row, TUI state, or committed
JSON records unavailability.

Contract (locked decisions):

- **SAME-ROOT pin** (the D-12/D-10 precedent): the file resolves
  through ``directories_config.config_dir()`` — the SAME resolver and
  root ``directories.json`` lives under (``DNALLMMARK_TUI_CONFIG_DIR``
  whole-dir override, empty = unset > ``XDG_CONFIG_HOME`` / dnallmmark
  > ``~/.config`` / dnallmmark), imported as the sibling module. NEVER
  a second hand-rolled copy of the resolver.
- **Fail-open tolerance** (the ruled policy — deliberately the
  OPPOSITE of ``directories_config``'s fail-loud): an ABSENT file is
  the normal zero-override state (``degraded`` None), and a
  present-but-malformed file (unreadable, invalid JSON, non-dict top
  level, non-dict ``tasks``) yields ZERO overrides with ``degraded``
  carrying the file's PATH — each consumer composes its own
  message/copy (I18N-01 for the TUI), and every surface makes the
  degradation VISIBLE (the CLI prints one ``[Warning]``; the wizard
  renders the degraded hint). Why fail-open here when
  ``directories.json`` is fail-loud: opposite hazards demand opposite
  policies — a corrupt directories file silently redirects a
  multi-day run to the wrong roots (worst case data loss, so it must
  abort), while a corrupt exclusion list that reads as empty merely
  lets a task RUN instead of skipping (recoverable, so it must never
  block the benchmark).
- **Entry tolerance**: a non-dict entry value drops (never coerced,
  never an exception); only ``unavailable is True`` flags (false /
  absent / truthy-non-true never); ``reason``/``since`` are read only
  as ``str`` (anything else reads as ``""``); keys unknown to the
  dataset registry STAY in the mapping — the loader never joins
  against a registry, and every consumer joins structurally, so an
  unknown key (a model key included) acts nowhere (the file is
  task-scoped by consumption, not by filtering).
- **Byte-identity when absent**: with NO file on the resolution
  chain, ``load_task_overrides()`` returns the empty mapping with
  ``degraded`` None and every consumer's absent-file branch keeps its
  exact current behavior — enumerate enumerates the same cells, the
  pickers render the same rows, the committed presence contract is
  untouched (the layer-split ruling: availability is a RUNTIME overlay
  merged AFTER presence; ``presence_for`` never sees this file).

Stdlib only (json/pathlib), so every lane (dev/CI/GPU) and the TUI
services tier can import this module: as a sibling module from
run_sweep (pipeline/ on sys.path at interpreter startup), and as a
top-level module from the TUI/tests via the existing pipeline/
sys.path root (the registry_loader import mechanics).
"""

import json
from pathlib import Path
from typing import NamedTuple

import directories_config  # sibling module — the SAME-ROOT resolver pin

#: The single file name under the config root (beside directories.json
#: — the same-root pin; the file is hand-authored, never written by
#: any code path).
TASK_OVERRIDES_FILE_NAME = "task_overrides.json"


class TaskOverrideEntry(NamedTuple):
    """One flagged task's override — pure data (reason/since coerced).

    Attributes:
        reason (str): the free-text operator reason ("" when absent or
            non-str in the file).
        since (str): the free-text date/identifier ("" when absent or
            non-str).
    """

    reason: str
    since: str


class TaskOverrides(NamedTuple):
    """The tolerant-load result: the flagged mapping + degradation.

    Attributes:
        unavailable (dict[str, TaskOverrideEntry]): every flagged task
            key (only ``unavailable is True`` entries), in file order.
        degraded (str | None): the PATH of a present-but-malformed file
            (the consumer composes its own message/copy from it); None
            for an absent file — absence is the normal zero-override
            state, never an error.
    """

    unavailable: dict[str, TaskOverrideEntry]
    degraded: "str | None"


def overrides_path():
    """The ``task_overrides.json`` location under the resolved config
    root — ``directories_config.config_dir()`` joined with the file
    name (the SAME root ``directories.json`` lives under; the resolver
    is imported, never re-implemented).

    Returns:
        Path: the file location (may not exist — absence is the
        zero-override case).
    """
    return directories_config.config_dir() / TASK_OVERRIDES_FILE_NAME


def _parse_entries(raw_tasks, path):
    """Project a parsed ``tasks`` mapping to the flagged-entry mapping.

    Args:
        raw_tasks (dict): the file's ``tasks`` value (a dict, checked
            by the caller).
        path (Path): the file the value came from (unused here — entry
            tolerance never degrades the whole file; kept for signature
            symmetry with the directories_config twin).

    Returns:
        dict[str, TaskOverrideEntry]: the flagged keys only, in file
        order (non-dict entries dropped; only ``unavailable is True``
        flags; reason/since read only as str).
    """
    unavailable: dict[str, TaskOverrideEntry] = {}
    for key, entry in raw_tasks.items():
        if not isinstance(entry, dict):
            continue  # non-dict entries drop (never coerced)
        if entry.get("unavailable") is not True:
            continue  # only the literal JSON true flags
        reason = entry.get("reason")
        since = entry.get("since")
        unavailable[key] = TaskOverrideEntry(
            reason=reason if isinstance(reason, str) else "",
            since=since if isinstance(since, str) else "",
        )
    return unavailable


def load_task_overrides(path=None):
    """The ONE tolerant reader (fail-open — the ruled policy).

    Missing file -> zero overrides with ``degraded`` None (the normal
    state). A present-but-malformed file (unreadable, invalid JSON,
    non-dict top level, non-dict ``tasks``) -> zero overrides with
    ``degraded`` carrying the path — an exclusion list must never
    block the benchmark, but the degradation is never silent: every
    consumer surfaces it (the CLI warning, the wizard hint).

    Args:
        path: an explicit file path; None resolves ``overrides_path()``.

    Returns:
        TaskOverrides: the flagged mapping + the degradation path (or
        None).
    """
    target = overrides_path() if path is None else Path(path)
    if not target.is_file():
        return TaskOverrides(unavailable={}, degraded=None)
    try:
        with open(target, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return TaskOverrides(unavailable={}, degraded=str(target))
    if not isinstance(raw, dict):
        return TaskOverrides(unavailable={}, degraded=str(target))
    raw_tasks = raw.get("tasks")
    if not isinstance(raw_tasks, dict):
        return TaskOverrides(unavailable={}, degraded=str(target))
    return TaskOverrides(
        unavailable=_parse_entries(raw_tasks, target), degraded=None)


def unavailable_tasks(path=None):
    """The mapping-only convenience over ``load_task_overrides``.

    The form the sweep driver's enumeration join and warning path
    consume — the degraded flag is dropped (a malformed file never
    blocks enumeration; main() composes its own warning through the
    full ``load_task_overrides`` read).

    Args:
        path: an explicit file path; None resolves ``overrides_path()``.

    Returns:
        dict[str, TaskOverrideEntry]: the flagged task keys only.
    """
    return load_task_overrides(path).unavailable
