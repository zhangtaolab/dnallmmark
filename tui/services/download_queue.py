"""
download_queue — the DATA-01/DATA-02 download-queue service (Phase 10,
10-01; D-01..D-08, R-01..R-03).

The download channel's whole orchestration core: the persistent
five-state queue, the ModelScope channel-resolution table over the
OFFICIAL registry, the CLI presence probe, and the Popen execution
engine with progress parsing, post-landing verification, the shape-C
rename, and process-group cancel. Later plans (reconcile gate, Zenodo
entry, screens) compose on this state machine and argv composer.

Contract (locked decisions):

- D-01/D-02 (SC5): the download is a ``modelscope`` CLI subprocess —
  ``Popen`` with a LIST argv (the console-script path + ``--dataset`` +
  ``--local_dir`` + ``--include``/``--exclude``), ``start_new_session=
  True``, stdout/stderr PIPEs, and an env that is EXACTLY
  ``dict(os.environ)`` (zero overrides — credentials stay the CLI's own
  business in ``~/.modelscope``). This module NEVER imports modelscope
  (it is in no uv group; its absence is a probed error state) and never
  imports textual (the services-tier invariant, locked by
  ``tests/tui/test_import_lock.py``).
- D-04: one task runs at a time — ``claim_next()`` hands the head
  pending entry to the caller-owned worker loop; ``run_task`` executes
  one claimed key.
- D-05: queue state persists at ``settings.state_dir() /
  download_queue.json`` (the same XDG state root as env_check state;
  ``DNALLMMARK_TUI_STATE_DIR`` injectable) with schema_version 1 and a
  per-dataset-key entries array; every state transition persists
  through ``settings.atomic_write``. The schema carries NO credential
  field of any kind.
- D-06: ``load()`` is tolerant — entries persisted as ``downloading``
  downgrade to ``pending`` with ``interrupted=true`` (interrupted ->
  pending); failed entries persist as failed (re-queueable via
  ``retry``); a corrupt/unparseable file is moved aside to
  ``download_queue.json.corrupt`` and the diagnostic returns as a
  string (never an exception, never silent loss). The channel's own
  resume machinery (``.msc`` skip + ``._____temp`` Range partials)
  makes a re-invoke a resume — the queue never hand-rolls downloads.
- D-08: entries are dataset-key-granular and enqueue is idempotent per
  key (an existing entry of any state yields ``already_queued``, no
  state change). Shared-repo keys (GUE) each compose their own include
  scope; no dedupe machinery.
- R-01: channel resolution reads the official registry entry's
  ``download_url`` first; if and only if that URL's host is not
  modelscope.cn does it fall back to ``download_url_alternates``; the
  repo id is derived by urlparse path parsing and validated against an
  allowlist regex before it can ever reach argv — zero registry-file
  changes, and every resolution records the winning ``source_url``.
- R-02: exactly 46 of the 50 official keys are one-click downloadable
  (38 shape-A + 5 shape-B + 3 shape-C) and 4 are disabled-with-reason
  (the Genomic_Benchmarks parquet layouts and
  plant-multi-species-open-chromatin); the shape classification is a
  code-owned table at module top (external-repo data, the gauntlet
  ``_AUDIT_SPLIT_ORDER`` idiom).
- D-03: progress parsing is best-effort over the CLI's stderr (ANSI
  strip + CR split + the two live-probed percent regexes); unparsed
  output yields percent ``None`` (the screen's indeterminate render
  carries the contract); the two stdout markers are detected as data;
  the full verbatim stdout+stderr is written to a per-key log file
  under the state root (drill-down content, never translated).
- Pitfall 3: after exit 0, the post-landing check requires
  ``pipeline/datasets/<Group>/<final_task_dir>/{train,dev,test}.csv``
  to all exist BEFORE any done transition — the CLI reports success for
  an empty filtered include set, so exit 0 alone can never mean done.

Subprocess discipline (the Phase 7 T-03-10 rule, Pitfall 1): argv is a
LIST, the Popen handle is owned directly (never a wrapper PID — the
live-probe orphan lesson), and cancel goes through ``os.killpg`` on the
process group (SIGTERM, wait, SIGKILL escalation). Nothing the service
itself writes ever lands outside the XDG state root (queue state + log
files); the committed registries and ``n_audit.json`` are read-only to
this module.

ZERO textual imports. Dependencies: stdlib (subprocess/threading/os/
sys/re/json/shutil/signal) + ``registry_loader`` (official file-name
constants) + the sibling ``registries`` (committed n_audit presence)
and ``settings`` (state root + atomic write) services.
"""

import json
import os
import shutil
import signal
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import registry_loader  # top-level module (pipeline/ sys.path root)

from tui.services import registries, settings

# ===== Locations (resolved from this module's own file, never CWD) =====

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The queue state file name under the XDG state root (D-05).
QUEUE_FILE_NAME = "download_queue.json"

#: The persisted schema version (bump = corrupt-family on read — a
#: forward-dated file is moved aside, never misread).
SCHEMA_VERSION = 1

#: D-02 verbatim five states, in lifecycle order.
QUEUE_STATES = ("pending", "downloading", "done", "failed", "mismatch")

#: The one entry kind this plan carries (models land in later plans).
KIND_DATASET = "dataset"


@dataclass(frozen=True)
class QueueEntry:
    """One queue row's immutable snapshot (the persisted field set,
    exactly — no credential field of any kind, SC5)."""

    key: str
    kind: str
    state: str
    attempts: int
    enqueued_at: str
    started_at: str | None
    finished_at: str | None
    last_percent: int | None
    interrupted: bool
    log_path: str | None
    problems: tuple[str, ...]
    reconcile: dict | None


@dataclass(frozen=True)
class EnqueueOutcome:
    """One enqueue attempt's structured result — machine codes + data,
    never screen copy (the 10-04 screen renders these).

    Attributes:
        action: one of ``enqueued`` / ``already_queued`` /
            ``unknown_key`` / ``disabled`` / ``cli_unavailable``.
        key: the requested dataset key.
        reason_code: the machine reason when action is ``disabled``
            (e.g. ``shape_d_layout``) — None otherwise.
        source_url: the winning registry URL (drill-down data) when
            the channel resolved; None otherwise.
    """

    action: str
    key: str
    reason_code: str | None = None
    source_url: str | None = None


@dataclass(frozen=True)
class MissingInfo:
    """One missing dataset row for the data-manager missing list
    (D-13's input; pure data, the screen renders)."""

    key: str
    declared_total: int
    channel: str
    reason_code: str | None
    source_url: str | None


class DownloadQueueService:
    """The persistent download queue (injectable spawner/CLI seams,
    thread-safe mutators, temp-free state under the XDG state root)."""

    def __init__(self, repo_root=None, state_path=None, spawner=None,
                 runner=None, cli_path=None):
        """Configure the service.

        Args:
            repo_root: the repo root the official registry and
                ``pipeline/datasets`` resolve against; None = this
                module's own repo root (never CWD).
            state_path: the queue state file; None resolves
                ``settings.state_dir() / QUEUE_FILE_NAME``.
            spawner: the Popen-shaped subprocess seam (``argv, **kwargs``
                -> Popen-like); None wraps ``subprocess.Popen`` with the
                fixed kwargs (start_new_session=True, PIPEs).
            runner: the completed-process seam reserved for the 10-02
                reconcile leg (the gauntlet runner shape); stored, not
                yet called by this plan.
            cli_path: an explicit modelscope console-script path; None
                probes the standard resolution order at each use.
        """
        self._repo_root = REPO_ROOT if repo_root is None else Path(repo_root)
        self._pipeline_dir = self._repo_root / "pipeline"
        if state_path is None:
            state_path = settings.state_dir() / QUEUE_FILE_NAME
        self._state_path = Path(state_path)
        self._spawner = spawner if spawner is not None else _default_spawner
        self._runner: Any = runner
        self._cli_path = cli_path
        self._lock = threading.Lock()
        self._entries: list[dict] = []
        self._cancel_requested: set[str] = set()
        self._active: dict[str, Any] = {}

    # ===== Lane 1 (Task 1): state machine + persistence =====

    def load(self):
        """Tolerantly load the queue state file (D-06)."""
        raise NotImplementedError

    def entries(self):
        """Immutable copies of the current entries, file order."""
        raise NotImplementedError

    def enqueue(self, key):
        """Idempotently append one pending dataset entry (D-08)."""
        raise NotImplementedError

    def enqueue_all_missing(self):
        """Enqueue every missing downloadable key; return the count."""
        raise NotImplementedError

    def retry(self, key):
        """Re-queue one failed/mismatch entry; True when applied."""
        raise NotImplementedError

    def cancel(self, key):
        """Remove a pending entry, or signal the active download."""
        raise NotImplementedError

    def missing_datasets(self):
        """MissingInfo rows for official keys missing per n_audit."""
        raise NotImplementedError


def _default_spawner(argv, **kwargs):
    """The real Popen seam (the injectable default)."""
    raise NotImplementedError
