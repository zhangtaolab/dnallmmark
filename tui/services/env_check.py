"""
env_check — env-check orchestration + same-day cache (Phase 8, 08-04,
ENV-01/ENV-02).

The service half of the env-check panel: it runs the env_smoke kernels,
persists their structured results under the D-04 state root, and answers
the same-day cache question. The 08-06 screen renders what this module
returns; Phase 11 wires launch gating onto the same judgments
(env_gate/quick_check).

Contract (locked decisions):

- D-02 (kernels imported, never re-implemented): the REAL kernel
  sequence is ``pipeline/env_smoke``'s, imported as a top-level module
  (pipeline/ is a sys.path root — the ``tui/__main__.py`` bootstrap at
  runtime, ``tests/conftest.py`` under pytest). This service never runs
  env_smoke as a child process and never parses its stdout; it consumes
  ``CheckResult`` values directly. CLI and TUI can never disagree about
  pass/fail because there is one implementation.
- D-05 (cache semantics): "same day" is a LOCAL CALENDAR DAY comparison
  (Pitfall 8) — the operator reads the checked_at date on their local
  clock, so the comparison runs on the same basis. ``checked_at``
  persists as the local naive ``YYYY-MM-DD HH:MM`` display value and
  ``checked_at_iso`` as the ISO-8601 UTC instant of the same moment. A
  same-day restart loads the cached result and runs ZERO kernels; the
  refresh path forces a full re-run by simply not consulting the cache.
- D-05 (tolerance): every read goes through ``artifact_loader``'s None
  sentinel — a torn, corrupt, or missing state file is a cache miss
  (full re-run), never a crash. Partial failures persist WHOLE (every
  item's status and detail lines) so the next startup renders them.
- T-08-03 (atomic persistence): writes go through
  ``settings.atomic_write`` (tmp + os.replace); persisting twice is
  idempotent — one valid file, no residue.
- D-03 (GPU discipline): importing this module executes no kernel; the
  default sequence CALLS the real kernels (CUDA/matmul touch the GPU)
  only when a caller runs it — the GB10 host. CI tests inject fakes.

State-file shape (schema_version 1)::

    {
      "schema_version": 1,
      "checked_at": "2026-10-11 16:20",         # local naive display value
      "checked_at_iso": "2026-10-11T08:20:00+00:00",
      "items": [{"name": "cuda", "ok": false, "lines": ["FAIL: ..."]}]
    }

ZERO textual imports (the services-tier invariant,
``tests/tui/test_import_lock.py``). Dependencies: stdlib + the pipeline
seams (env_smoke, artifact_loader) + the sibling settings service.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import artifact_loader  # top-level module (pipeline/ sys.path root, D-19)
import env_smoke  # top-level module (pipeline/ sys.path root, D-02)
from env_smoke import CheckResult

from tui.services import settings

STATE_SCHEMA_VERSION = 1
STATE_FILE_NAME = "env_check.json"
CHECKED_AT_FORMAT = "%Y-%m-%d %H:%M"  # local naive — the displayed value


def default_state_path():
    """The env-check state file location (D-04: the STATE root).

    Returns:
        Path: ``settings.state_dir() / "env_check.json"`` — Linux
        default ``~/.local/state/dnallmmark/env_check.json``. Check
        results never live under the config root (the split is
        absolute).
    """
    return settings.state_dir() / STATE_FILE_NAME


def load_cached(path):
    """Tolerantly load the persisted env-check state.

    Args:
        path: the state file (str or os.PathLike).

    Returns:
        The parsed state dict, or None when the file is missing,
        unreadable, empty, truncated, or not valid JSON (the
        artifact_loader None sentinel — a cache miss, never a crash).
        Structurally valid JSON that merely lacks expected keys is
        returned as-is; key-level checks belong to callers
        (``is_same_local_day`` reads a missing checked_at as a miss).
    """
    return artifact_loader.load_json_artifact(path)


def is_same_local_day(state, now=None):
    """Compare the state's checked_at date to now's LOCAL calendar date.

    The basis is LOCAL calendar time by decision (Pitfall 8): the
    displayed last-checked date is the operator's local clock, so the
    comparison must agree with what is displayed — never UTC.

    Args:
        state: the loaded state dict (from ``load_cached``); None or a
            state without a parseable ``checked_at`` reads as a miss.
        now: the comparison moment as a naive LOCAL datetime; None
            means ``datetime.now()``.

    Returns:
        bool: True when checked_at falls on now's local calendar day.
    """
    checked_at = state.get("checked_at") if isinstance(state, dict) else None
    if not isinstance(checked_at, str):
        return False
    try:
        checked_date = datetime.strptime(checked_at[:10], "%Y-%m-%d").date()
    except ValueError:
        return False
    moment = datetime.now() if now is None else now
    return checked_date == moment.date()


def run_full_check(kernels=None, state_path=None, now=None):
    """Run the full env check and persist the result (ENV-01).

    Args:
        kernels: an injectable sequence of zero-arg callables, each
            returning one ``CheckResult`` — results come back in the
            given order (CI tests inject fakes, D-03). None means the
            REAL env_smoke kernel sequence in main() order:
            version_pins, dnallm, peft, cuda, matmul, numpy,
            dataset_dirs — cuda/matmul behind the torch-import gate
            with the two ok=False empty-lines fallback when torch is
            unavailable.
        state_path: where to persist; None means
            ``default_state_path()`` (the D-04 state root).
        now: the check moment as a naive LOCAL datetime (see
            ``persist``); None means now.

    Returns:
        list[CheckResult]: the executed kernel results, in order.
    """
    if kernels is None:
        kernels = list(default_kernels().values())
    results = [kernel() for kernel in kernels]
    path = default_state_path() if state_path is None else Path(state_path)
    persist(path, results, now=now)
    return results


def default_kernels():
    """The REAL env_smoke kernel sequence, in main() order (D-02).

    Builds zero-arg callables over the imported kernels so every caller
    (``run_full_check`` here, ``quick_check``'s launch-required subset,
    the 08-06 worker posting one message per kernel) shares ONE
    sequence definition. The torch-import gate mirrors main()'s literal
    import: when torch cannot import, cuda and matmul return the
    ok=False empty-lines placeholders — the same two values main()
    appends on its torch-unavailable branch.

    Returns:
        dict[str, callable]: kernel id -> zero-arg callable returning
        one ``CheckResult``; insertion order == main() order.
    """
    pins = env_smoke.read_gpu_pins(env_smoke.PYPROJECT_PATH)
    floor = env_smoke.read_numpy_floor_major(env_smoke.PYPROJECT_PATH)

    def _version_pins():
        return env_smoke.check_version_pins(pins)

    def _dnallm():
        return env_smoke.check_dnallm()

    def _peft():
        return env_smoke.check_peft()

    def _cuda():
        torch = _import_torch_or_none()
        if torch is None:
            return CheckResult(name="cuda", ok=False, lines=())
        return env_smoke.check_cuda(torch)

    def _matmul():
        torch = _import_torch_or_none()
        if torch is None:
            return CheckResult(name="matmul", ok=False, lines=())
        return env_smoke.check_matmul(torch)

    def _numpy():
        return env_smoke.check_numpy(floor)

    def _dataset_dirs():
        return env_smoke.check_dataset_dirs()

    return {
        "version_pins": _version_pins,
        "dnallm": _dnallm,
        "peft": _peft,
        "cuda": _cuda,
        "matmul": _matmul,
        "numpy": _numpy,
        "dataset_dirs": _dataset_dirs,
    }


def _import_torch_or_none():
    """The torch-import gate mirroring env_smoke.main()'s literal import.

    Any import-time failure is the two-False fallback, never a traceback
    (the smoke gate's own contract). The import is deferred to CALL time
    — importing this service module on a CPU box executes nothing.
    """
    try:
        import torch
    except Exception:  # noqa: BLE001 — mirrors main()'s gate: ANY
        # import-time failure is the fallback, never a traceback
        return None
    return torch


def persist(path, results, now=None):
    """Persist the check results under the D-04 state root (D-05).

    Partial failures persist whole: every item's name, ok flag, and
    detail lines are written, so the next startup renders the failure
    detail without re-running. The write is atomic
    (``settings.atomic_write`` — tmp + os.replace); persisting twice
    leaves a single valid file.

    Args:
        path: the state file to write (str or os.PathLike).
        results: the ``CheckResult`` values to persist, in kernel order.
        now: the check moment as a naive LOCAL datetime — the single
            instant both timestamp forms derive from; None means now.
    """
    moment = datetime.now() if now is None else now
    payload = {
        "schema_version": STATE_SCHEMA_VERSION,
        "checked_at": moment.strftime(CHECKED_AT_FORMAT),
        # The ISO-8601 UTC instant of the SAME moment — one write, both
        # bases (Pitfall 8: display and comparison are local; the ISO
        # form preserves the absolute instant).
        "checked_at_iso": moment.astimezone(timezone.utc).isoformat(),
        "items": [
            {
                "name": result.name,
                "ok": result.ok,
                "lines": list(result.lines),
            }
            for result in results
        ],
    }
    settings.atomic_write(
        Path(path),
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
    )
