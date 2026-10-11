"""
artifact_loader.py — tolerant JSON artifact reads (Phase 7, PIPE-03).

Single pure, stateless loader for pipeline-emitted JSON artifacts
(``flops_report.json`` first; the Phase 11 monitor and Phase 8
``tui/services`` reuse the same contract — D-19: dependency direction
tui -> pipeline).

Contract (D-17/D-18):
- Parse-level tolerance ONLY: a file that is missing, unreadable
  (OSError — includes permission failures), undecodable (a multibyte
  sequence truncated mid-character), empty, or not valid JSON returns the
  None sentinel. Read-then-decode keeps the empty file as the explicitly
  nameable decode case (``json.loads("")`` raises ``JSONDecodeError``).
- Structurally valid JSON that merely lacks expected keys is NOT
  corruption — it is returned as-is; key-level checks belong to callers.
- No cache, no state: callers keep their own last-known-good (D-18 —
  testable, multi-process safe).

Zero dependencies beyond stdlib ``json`` + ``pathlib`` (D-19), so every
lane (dev/CI/GPU) can import this module.
"""

import json
from pathlib import Path


def load_json_artifact(path):
    """Tolerantly read a JSON artifact from disk.

    Args:
        path: the file to read (str or os.PathLike).

    Returns:
        The parsed JSON document (dict, list, or scalar), or None when the
        file is missing, unreadable, empty, truncated, or not valid JSON.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
