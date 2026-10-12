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
import re
import shutil
import signal
import subprocess
import sys
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import registry_loader  # top-level module (pipeline/ sys.path root)

from tui.services import registries, settings

# ===== Locations (resolved from this module's own file, never CWD) =====

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The queue state file name under the XDG state root (D-05).
QUEUE_FILE_NAME = "download_queue.json"

#: The log subdirectory + file naming under the state root (D-03).
LOG_DIR_NAME = "logs"

#: The persisted schema version (bump = corrupt-family on read — a
#: forward-dated file is moved aside, never misread).
SCHEMA_VERSION = 1

#: D-02 verbatim five states, in lifecycle order.
QUEUE_STATES = ("pending", "downloading", "done", "failed", "mismatch")

#: The one entry kind this plan carries (models land in later plans).
KIND_DATASET = "dataset"

#: The canonical persisted entry field order — the exact set, nothing
#: may ever appear outside it (SC5: zero credential surface).
_ENTRY_FIELDS = (
    "key", "kind", "state", "attempts", "enqueued_at", "started_at",
    "finished_at", "last_percent", "interrupted", "log_path", "problems",
    "reconcile",
)

# ===== R-02 channel shape table (code-owned external-repo data) =====
#
# The live-probed ModelScope repo census (10-RESEARCH, HubApi file trees
# over all 15 repos): only 38/50 registry keys map cleanly onto "repo
# task-subdir == registry task component". The table below is data
# about EXTERNAL repos (not user config), hardcoded at module top like
# gauntlet's ``_AUDIT_SPLIT_ORDER``. A repo id absent from the table
# degrades to disabled-with-reason (registry/mirror evolution
# tolerance), never a crash.

#: Shape A — repo task subdir at repo root == the registry task
#: component (38 keys: ``--local_dir pipeline/datasets/<Group>``,
#: ``--include "<task>/*"``).
SHAPE_A_REPOS = frozenset({
    "forrestzhang/BEND",
    "forrestzhang/Deep4mC_datasets",
    "lgq12697/GUE",
    "lgq12697/nucleotide_transformer_downstream_tasks",
    "lgq12697/plant-genomic-benchmark",
    "forrestzhang/iDNA_ABF_datasets",
    "forrestzhang/iPro-WAEL_datasets",
})

#: Shape B — the whole repo is one task with CSVs at the repo root
#: (5 keys: ``--local_dir pipeline/datasets/<Group>/<task>``, no
#: include).
SHAPE_B_REPOS = frozenset({
    "zhangtaolab/cross_species_leaf_absolute_translation",
    "zhangtaolab/cross_species_leaf_on_off_translation",
    "zhangtaolab/plant-multi-species-core-promoters",
    "zhangtaolab/plant-multi-species-lncRNAs",
    "zhangtaolab/plant-multi-species-sequence-conservation",
})

#: Shape C — the repo subtree name differs from the registry dir name
#: (3 histone keys: shape-A argv over the repo subtree, then a
#: post-landing rename to the registry dir name).
SHAPE_C_REPO = "zhangtaolab/plant-multi-species-histone-modifications"

#: The shape-C per-key repo-subtree map (registry key -> repo subtree).
SHAPE_C_SUBTREES = {
    "PDLLMs_datasets__plant-multi-species-H3K27ac": "H3K27ac",
    "PDLLMs_datasets__plant-multi-species-H3K27me3": "H3K27me3",
    "PDLLMs_datasets__plant-multi-species-H3K4me3": "H3K4me3",
}

#: Shape D — upstream mirror layouts that are NOT one-click landable
#: (Genomic_Benchmarks parquet demo dirs x3, open-chromatin
#: full/mini): no argv is ever composed; the drill-down shows the URL.
SHAPE_D_REPOS = frozenset({
    "lgq12697/Genomic_Benchmarks",
    "zhangtaolab/plant-multi-species-open-chromatin",
})

#: Reason codes (machine vocabulary — the screens render, never parse).
REASON_SHAPE_D = "shape_d_layout"
REASON_UNKNOWN_REPO = "unknown_repo_shape"
REASON_NO_MIRROR = "no_modelscope_mirror"
REASON_MALFORMED_REPO_ID = "malformed_repo_id"
REASON_MALFORMED_PATH = "malformed_dataset_path"
REASON_REGISTRY_UNREADABLE = "registry_unreadable"

#: Reason codes whose channel disposition is "disabled" (a deliberate
#: no-download policy); every other reason is the defensive "unknown".
_DISABLED_REASONS = frozenset({REASON_SHAPE_D, REASON_UNKNOWN_REPO})

#: The repo-id allowlist (T-10-01-01): a registry-derived value must
#: match ``namespace/name`` word chars before it can ever reach argv.
REPO_ID_RE_PART = r"[\w.-]+/[\w.-]+"

#: The modelscope host test (R-01): the exact apex or any subdomain.
_MODELSCOPE_HOST = "modelscope.cn"

#: The CLI's own junk exclusion (live-probed: ``--include "<task>/*"``
#: still admits ``.DS_Store``; harmless but excluded by default).
EXCLUDE_PATTERNS = ("*.DS_Store",)

# ===== D-03 progress parsing (the live-probed stderr contract) =====
#
# stderr carries (1) a two-line pkg_resources deprecation warning to
# skip when scanning for real errors (Pitfall 5) and (2) tqdm progress
# with ANSI cursor-up escapes and CR updates because files download in
# parallel. Parsing is BEST-EFFORT: unparsed output yields percent
# None and the screen's indeterminate render carries the contract.

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
FILE_PCT_RE = re.compile(r"Downloading \[([^\]]+)\]:\s+(\d+)%")
ITEMS_PCT_RE = re.compile(r"Processing (\d+) items:\s+(\d+)%")

#: The two stdout markers (clean one-liners, live-probed verbatim).
START_MARKER = "Downloading Dataset to directory"
SUCCESS_MARKER = "Successfully Downloaded from dataset"

#: The known pkg_resources noise lines skipped by
#: ``first_real_error_line`` (the drill-down still shows everything).
PKG_RESOURCES_NOISE = (
    "UserWarning: pkg_resources is deprecated",
    "import pkg_resources",
)

# ===== Engine problem codes (machine vocabulary) =====

PROBLEM_CLI_UNAVAILABLE = "cli_unavailable"
PROBLEM_CANCELLED = "cancelled_by_operator"
PROBLEM_LANDING_INCOMPLETE = "landing_incomplete"
PROBLEM_RENAME_TARGET_EXISTS = "rename_target_exists"
PROBLEM_RENAME_ERROR = "rename_error"
PROBLEM_SUBPROCESS_ERROR = "subprocess_error"

#: The reap loop's wait chunk (re-checked for cancel between chunks —
#: there is NO artificial total timeout by design: multi-GB legitimate
#: transfers are normal; operator cancel is the bounded escape,
#: T-10-01-04).
REAP_INTERVAL_SECONDS = 5
#: After SIGTERM, how long to wait before the SIGKILL escalation.
SIGTERM_GRACE_SECONDS = 10
#: The reader threads' pipe chunk size.
READ_CHUNK_BYTES = 4096

#: The landing gate's required split files (the audit kernel's own
#: split order).
LANDING_SPLITS = ("train.csv", "dev.csv", "test.csv")


def clean_chunk(chunk):
    """Normalize one stderr chunk: CR -> LF, then strip ANSI escapes.

    Args:
        chunk (str): the raw decoded chunk.

    Returns:
        str: the cleaned text (regex-safe for the percent patterns).
    """
    return ANSI_RE.sub("", chunk.replace("\r", "\n"))


def parse_progress(chunk):
    """Best-effort percent extraction from one stderr chunk.

    Args:
        chunk (str): the raw decoded chunk (CR/ANSI-laden is fine).

    Returns:
        tuple: ``(files, items)`` — ``files`` maps each seen file to
        its latest INTEGER percent (empty when none parsed); ``items``
        is the file-count roll-up integer percent or None
        (indeterminate — the screen contract).
    """
    clean = clean_chunk(chunk)
    files = FILE_PCT_RE.findall(clean)
    items = ITEMS_PCT_RE.findall(clean)
    return ({name: int(percent) for name, percent in files}
            if files else {},
            int(items[-1][1]) if items else None)


def first_real_error_line(text):
    """The first non-noise line of a captured stream (the failure
    summary scan; the drill-down still shows everything, D-03).

    Skips the two known pkg_resources warning lines the CLI emits at
    boot (Pitfall 5) and blank lines.

    Args:
        text (str): the captured stream text.

    Returns:
        str | None: the first real line, or None when only noise.
    """
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if any(line.startswith(prefix)
               for prefix in PKG_RESOURCES_NOISE):
            continue
        return line
    return None


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
class ChannelSpec:
    """One dataset key's resolved download channel — pure data derived
    from the official registry entry plus the R-02 shape table.

    Attributes:
        key: the dataset registry key.
        repo_id: the modelscope ``namespace/repo`` (validated against
            the allowlist regex) — None when no mirror resolved.
        shape: "A" / "B" / "C" for the downloadable layouts; None for
            every degraded disposition.
        local_dir: the ABSOLUTE ``--local_dir`` target under
            ``pipeline/datasets`` (None for degraded specs).
        include: the ``--include`` patterns (empty for shape B).
        exclude: the ``--exclude`` junk patterns.
        rename: the shape-C post-landing rename pair
            (``<Group>/<subtree>``, ``<Group>/<registry-task-dir>``)
            relative to ``pipeline/datasets``; None otherwise.
        final_task_dir: the registry task component the landing check
            requires under ``pipeline/datasets/<Group>`` (None when the
            ``Dataset_path`` itself is malformed).
        source_url: the winning registry URL (R-01 data).
        reason_code: None for a downloadable channel; the machine
            reason otherwise (``shape_d_layout``,
            ``unknown_repo_shape``, ``no_modelscope_mirror``,
            ``malformed_repo_id``, ...).
    """

    key: str
    repo_id: str | None
    shape: str | None
    local_dir: Path | None
    include: tuple[str, ...]
    exclude: tuple[str, ...]
    rename: tuple[str, str] | None
    final_task_dir: str | None
    source_url: str | None
    reason_code: str | None


@dataclass(frozen=True)
class MissingInfo:
    """One missing dataset row for the data-manager missing list
    (D-13's input; pure data, the screen renders)."""

    key: str
    declared_total: int
    channel: str
    reason_code: str | None
    source_url: str | None


@dataclass(frozen=True)
class QueueEvent:
    """One task-run outcome (the WR-02 run-id-tagged event the future
    screen consumes; DATA, never copy).

    Attributes:
        run_id: the caller's run tag, echoed verbatim.
        key: the dataset registry key.
        kind: the entry kind (``KIND_DATASET`` this plan).
        state: the entry's persisted end state.
        last_percent: the last parsed integer percent (None when
            nothing parsed — indeterminate, the screen contract).
        problems: machine problem codes (empty on done).
        details: structured data tokens (``exit_code=0``,
            ``success_marker=true``, ``missing=<relpath>`` ...).
        log_path: the verbatim log file path relative to the state
            root, or None when no log could be written.
    """

    run_id: str
    key: str
    kind: str
    state: str
    last_percent: int | None
    problems: tuple[str, ...]
    details: tuple[str, ...]
    log_path: str | None


def _default_spawner(argv, **kwargs):
    """The real Popen seam (the injectable default).

    The service itself passes the fixed kwargs on every call
    (``start_new_session=True``, ``stdout``/``stderr`` PIPEs, the exact
    ``env``), so the default is a pure forward to ``subprocess.Popen``.

    Args:
        argv (list): the LIST argv (never a shell string).
        **kwargs: ``env``/``start_new_session``/``stdout``/``stderr``.

    Returns:
        subprocess.Popen: the owned process handle.
    """
    return subprocess.Popen(argv, **kwargs)


def resolve_modelscope_cli(cli_path=None):
    """Resolve the modelscope console script (live-probed order).

    ``python -m modelscope`` does NOT work (no ``__main__``) — only the
    console script does. Resolution order:

    1. the explicit ``cli_path`` argument, used verbatim;
    2. ``Path(sys.executable).parent / "modelscope"`` when that sibling
       exists (the venv layout this console runs under);
    3. ``shutil.which("modelscope")`` (PATH installs).

    Args:
        cli_path (str | Path | None): an explicit console-script path.

    Returns:
        Path | None: the console-script path, or None on a CLI-absent
        machine (the probed unavailable state — never an import).
    """
    if cli_path is not None:
        return Path(cli_path)
    sibling = Path(sys.executable).parent / "modelscope"
    if sibling.is_file():
        return sibling
    found = shutil.which("modelscope")
    return Path(found) if found is not None else None


def channel_state(spec):
    """Map one resolved ChannelSpec to its disposition vocabulary.

    Args:
        spec (ChannelSpec): a ``resolve_channel`` result.

    Returns:
        str: ``downloadable`` (reason None) / ``disabled`` (the
        deliberate shape-D and unknown-repo reasons) / ``unknown``
        (every defensive reason — no mirror, malformed values, an
        unreadable registry).
    """
    if spec.reason_code is None:
        return "downloadable"
    if spec.reason_code in _DISABLED_REASONS:
        return "disabled"
    return "unknown"


def compose_download_argv(spec, cli_path):
    """Compose the modelscope CLI argv for one downloadable spec.

    The live-probed invocation shape (console script, never
    ``python -m modelscope`` — it has no ``__main__``):

    - shape A: ``[cli, "download", "--dataset", repo, "--local_dir",
      <pipeline/datasets/<Group>>, "--include", "<task>/*",
      "--exclude", "*.DS_Store"]``
    - shape B: the same minus ``--include``, with ``--local_dir``
      pointing at ``<Group>/<task>`` (CSVs live at the repo root);
    - shape C: the shape-A argv with the REPO subtree include (the
      post-landing rename corrects the dir name).

    Args:
        spec (ChannelSpec): a ``resolve_channel`` result.
        cli_path (str | Path): the resolved console-script path.

    Returns:
        list[str] | None: the LIST argv (values can never become flags
        — no shell ever parses them), or None for every degraded spec
        (nothing is composed for a disabled/unknown channel).
    """
    if spec.reason_code is not None or spec.local_dir is None:
        return None
    argv = [str(cli_path), "download",
            "--dataset", spec.repo_id,
            "--local_dir", str(spec.local_dir)]
    for pattern in spec.include:
        argv += ["--include", pattern]
    for pattern in spec.exclude:
        argv += ["--exclude", pattern]
    return argv


def _is_modelscope_url(url):
    """True when ``url``'s host is modelscope.cn (apex or subdomain)."""
    if not isinstance(url, str) or not url:
        return False
    host = urlparse(url).netloc.rpartition("@")[2].partition(":")[0]
    host = host.lower()
    return host == _MODELSCOPE_HOST or host.endswith(
        "." + _MODELSCOPE_HOST)


def _repo_id_from_url(url):
    """Derive the ``namespace/repo`` id from a modelscope dataset URL.

    The live-probed derivation: the urlparse path split on
    ``/datasets/`` takes the last segment, stripped of slashes.

    Args:
        url (str): the winning modelscope URL.

    Returns:
        str | None: the repo id, or None when the path yields nothing.
    """
    path = urlparse(url).path
    segment = path.split("/datasets/")[-1].strip("/")
    return segment or None


def _sanitize_key(key):
    """The repo filename convention: path separators -> underscores."""
    return key.replace("/", "_").replace("\\", "_")


def _pump(stream, on_chunk):
    """Drain one pipe to EOF on the calling (daemon) thread.

    Decodes each chunk with ``errors="replace"`` — the capture stays
    verbatim-ish for the log while a mid-character chunk boundary can
    never crash the reader (best-effort by contract).

    Args:
        stream: a binary pipe with ``read(n)`` (Popen PIPE or a fake).
        on_chunk: callable(str) invoked per decoded chunk.
    """
    try:
        while True:
            chunk = stream.read(READ_CHUNK_BYTES)
            if not chunk:
                break
            on_chunk(chunk.decode("utf-8", errors="replace"))
    except (OSError, ValueError):
        pass    # the pipe died with the process; the reap owns the rest


def _signal_group(proc, sig):
    """Signal one owned process's WHOLE group (Pitfall 1).

    Absorbs the already-dead races (the reap loop owns the outcome).
    """
    try:
        os.killpg(os.getpgid(proc.pid), sig)
    except (ProcessLookupError, PermissionError, OSError):
        pass


def _now_iso():
    """The current local moment as an ISO-8601 string."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _int_or_zero(value):
    """Coerce to a non-bool int, defaulting to 0 (the repo's defensive
    numeric convention)."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return 0


def _normalized_entry(raw):
    """Coerce one persisted entry to the canonical field set.

    Tolerant (D-06): absent fields default; an unknown persisted state
    reruns as pending; problems coerce to a list of strings. The
    output carries EXACTLY ``_ENTRY_FIELDS`` — nothing else survives.
    """
    state = raw.get("state")
    if state not in QUEUE_STATES:
        state = "pending"
    problems = raw.get("problems")
    problems = ([str(p) for p in problems]
                if isinstance(problems, list) else [])
    return {
        "key": str(raw.get("key") or ""),
        "kind": str(raw.get("kind") or KIND_DATASET),
        "state": state,
        "attempts": _int_or_zero(raw.get("attempts")),
        "enqueued_at": str(raw.get("enqueued_at") or ""),
        "started_at": raw.get("started_at"),
        "finished_at": raw.get("finished_at"),
        "last_percent": raw.get("last_percent"),
        "interrupted": bool(raw.get("interrupted")),
        "log_path": raw.get("log_path"),
        "problems": problems,
        "reconcile": raw.get("reconcile"),
    }


def _frozen(entry):
    """One internal persisted-form dict as an immutable QueueEntry."""
    return QueueEntry(
        key=entry["key"],
        kind=entry["kind"],
        state=entry["state"],
        attempts=entry["attempts"],
        enqueued_at=entry["enqueued_at"],
        started_at=entry["started_at"],
        finished_at=entry["finished_at"],
        last_percent=entry["last_percent"],
        interrupted=entry["interrupted"],
        log_path=entry["log_path"],
        problems=tuple(entry["problems"]),
        reconcile=entry["reconcile"],
    )


def _declared_total(entry):
    """Sum the declared ``Train``/``Dev``/``Test`` ints (non-int
    declarations contribute 0)."""
    return sum(_int_or_zero(entry.get(field))
               for field in ("Train", "Dev", "Test"))


def _group_and_task(entry):
    """Derive ``(Group, task)`` from the registry ``Dataset_path``.

    The committed form is ``datasets/<Group>/{task}``: Group is
    component 1 and task the last component. Anything shorter (or with
    an empty component) is malformed.

    Returns:
        tuple[str, str] | None: the pair, or None when malformed.
    """
    raw = entry.get("Dataset_path")
    if not isinstance(raw, str):
        return None
    parts = [part for part in raw.split("/")]
    if len(parts) < 3 or not all(parts):
        return None
    return parts[1], parts[-1]


class DownloadQueueService:
    """The persistent download queue (injectable spawner/CLI seams,
    thread-safe mutators, all state under the XDG state root)."""

    def __init__(self, repo_root=None, state_path=None, spawner=None,
                 runner=None, cli_path=None):
        """Configure the service.

        Args:
            repo_root: the repo root the official registry and
                ``pipeline/datasets`` resolve against; None = this
                module's own repo root (never CWD).
            state_path: the queue state file; None resolves
                ``settings.state_dir() / QUEUE_FILE_NAME``.
            spawner: the Popen-shaped subprocess seam (``argv,
                **kwargs`` -> Popen-like); None wraps
                ``subprocess.Popen`` with the fixed kwargs.
            runner: the completed-process seam reserved for the 10-02
                reconcile leg (the gauntlet runner shape); stored, not
                yet called by this plan.
            cli_path: an explicit modelscope console-script path; None
                probes the standard resolution order at each use.
        """
        self._repo_root = (REPO_ROOT if repo_root is None
                           else Path(repo_root).resolve())
        self._pipeline_dir = self._repo_root / "pipeline"
        if state_path is None:
            state_path = settings.state_dir() / QUEUE_FILE_NAME
        self._state_path = Path(state_path)
        self._spawner: Any = (_default_spawner if spawner is None
                              else spawner)
        self._runner: Any = runner
        self._cli_path = cli_path
        self._lock = threading.Lock()
        self._entries: list[dict] = []
        self._cancel_requested: set[str] = set()
        self._active: dict[str, Any] = {}

    # ===== Load / snapshot (D-06 tolerant recovery) =====

    def load(self):
        """Tolerantly load the queue state file.

        Absent file: empty queue, no error, no file created. Valid
        file: entries loaded, with every entry persisted as
        ``downloading`` downgraded to ``pending`` + ``interrupted``
        (D-06 — the downgrade itself persists per D-05). Corrupt,
        unparseable, or forward-dated file: moved aside to
        ``download_queue.json.corrupt``, entries empty, and the
        diagnostic returned (never an exception, never silent loss).

        Returns:
            str | None: the diagnostic when the file was quarantined;
            None on every healthy path. Idempotent.
        """
        with self._lock:
            return self._load_locked()

    def _load_locked(self):
        path = self._state_path
        if not path.is_file():
            self._entries = []
            return None
        try:
            with open(path, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, json.JSONDecodeError,
                UnicodeDecodeError) as exc:
            return self._quarantine_locked(repr(exc))
        if not isinstance(doc, dict) \
                or not isinstance(doc.get("entries"), list):
            return self._quarantine_locked(
                "top level must be a JSON object with an entries list")
        if doc.get("schema_version") != SCHEMA_VERSION:
            return self._quarantine_locked(
                "unsupported schema_version "
                + repr(doc.get("schema_version"))
                + " (expected " + str(SCHEMA_VERSION) + ")")
        entries = [_normalized_entry(raw)
                   for raw in doc["entries"] if isinstance(raw, dict)]
        downgraded = False
        for entry in entries:
            if entry["state"] == "downloading":
                entry["state"] = "pending"
                entry["interrupted"] = True
                downgraded = True
        self._entries = entries
        if downgraded:
            self._persist_locked()
        return None

    def _quarantine_locked(self, diagnostic):
        """Move the corrupt state file aside and reset to empty."""
        path = self._state_path
        message = ("download queue state file unreadable, moved aside: "
                   + str(path) + " (" + diagnostic + ")")
        try:
            os.replace(path, path.with_name(path.name + ".corrupt"))
        except OSError as exc:
            message += "; sidecar move failed: " + repr(exc)
        self._entries = []
        return message

    def entries(self):
        """Immutable copies of the current entries, in file order.

        Returns:
            list[QueueEntry]: frozen snapshots — mutating them can
            never touch the service's live state.
        """
        with self._lock:
            return [_frozen(entry) for entry in self._entries]

    def _persist_locked(self):
        """Write the whole queue through the ONE atomic rail (D-05)."""
        doc = {
            "schema_version": SCHEMA_VERSION,
            "entries": [{field: entry[field] for field in _ENTRY_FIELDS}
                        for entry in self._entries],
        }
        settings.atomic_write(
            self._state_path,
            json.dumps(doc, indent=4, ensure_ascii=False))

    # ===== Mutators (enqueue / retry / cancel) =====

    def enqueue(self, key):
        """Idempotently append one pending dataset entry (D-08).

        Outcome order: an existing entry of ANY state yields
        ``already_queued`` with no state change; an unknown official
        key yields ``unknown_key`` (custom keys are not download
        targets — the official registry is the only URL authority); a
        disabled/degraded channel yields ``disabled`` carrying the
        machine reason + the drill-down ``source_url``; a CLI-absent
        machine yields ``cli_unavailable``; otherwise the pending entry
        appends and persists (``enqueued``).

        Args:
            key (str): the dataset registry key.

        Returns:
            EnqueueOutcome: the structured result (never an exception).
        """
        cli = resolve_modelscope_cli(self._cli_path)
        with self._lock:
            if any(entry["key"] == key for entry in self._entries):
                return EnqueueOutcome(
                    action="already_queued", key=key)
            spec = self.resolve_channel(key)
            if spec is None:
                return EnqueueOutcome(action="unknown_key", key=key)
            if spec.reason_code is not None:
                return EnqueueOutcome(
                    action="disabled", key=key,
                    reason_code=spec.reason_code,
                    source_url=spec.source_url)
            if cli is None:
                return EnqueueOutcome(
                    action="cli_unavailable", key=key)
            self._entries.append({
                "key": key,
                "kind": KIND_DATASET,
                "state": "pending",
                "attempts": 0,
                "enqueued_at": _now_iso(),
                "started_at": None,
                "finished_at": None,
                "last_percent": None,
                "interrupted": False,
                "log_path": None,
                "problems": [],
                "reconcile": None,
            })
            self._persist_locked()
            return EnqueueOutcome(action="enqueued", key=key)

    def enqueue_all_missing(self):
        """Enqueue every missing downloadable dataset key.

        Rows whose channel is disabled or unknown are skipped silently
        (the disabled drill-down is the operator's path, not a queue
        row); already-queued keys contribute nothing to the count.

        Returns:
            int: the number of NEWLY enqueued keys.
        """
        count = 0
        for row in self.missing_datasets():
            if row.channel != "downloadable":
                continue
            outcome = self.enqueue(row.key)
            if outcome.action == "enqueued":
                count += 1
        return count

    def retry(self, key):
        """Re-queue one failed or mismatch entry as pending (D-06).

        Args:
            key (str): the dataset registry key.

        Returns:
            bool: True when the entry was failed/mismatch and is now
            pending (persisted); False for every other state (and for
            absent keys).
        """
        with self._lock:
            for entry in self._entries:
                if entry["key"] != key:
                    continue
                if entry["state"] not in ("failed", "mismatch"):
                    return False
                entry["state"] = "pending"
                entry["problems"] = []
                self._persist_locked()
                return True
            return False

    def cancel(self, key):
        """Cancel one entry.

        ``pending``: the entry is REMOVED from the file. ``downloading``:
        the cancel-requested flag is set and SIGTERM is sent via
        ``os.killpg`` to the recorded process group — the worker's reap
        loop completes the failed transition (partials are retained by
        the channel, D-06 resume). Any other state or absent key: a
        no-op.

        Args:
            key (str): the dataset registry key.

        Returns:
            str: ``removed`` / ``signalled`` / ``noop``.
        """
        proc = None
        with self._lock:
            entry = next((e for e in self._entries
                          if e["key"] == key), None)
            if entry is None:
                return "noop"
            if entry["state"] == "pending":
                self._entries.remove(entry)
                self._persist_locked()
                return "removed"
            if entry["state"] == "downloading":
                self._cancel_requested.add(key)
                proc = self._active.get(key)
                outcome = "signalled"
            else:
                return "noop"
        if proc is not None:
            _signal_group(proc, signal.SIGTERM)
        return outcome

    # ===== The single-task claim (D-04) =====

    def claim_next(self):
        """Claim the head pending entry for the worker (D-04: one task
        runs at a time; only the worker thread calls this).

        Transitions the first ``pending`` entry in file order to
        ``downloading`` with ``attempts`` incremented and ``started_at``
        stamped, persisted before returning.

        Returns:
            QueueEntry | None: the claimed snapshot, or None when no
            pending entry exists.
        """
        with self._lock:
            for entry in self._entries:
                if entry["state"] != "pending":
                    continue
                entry["state"] = "downloading"
                entry["attempts"] = entry["attempts"] + 1
                entry["started_at"] = _now_iso()
                self._persist_locked()
                return _frozen(entry)
            return None

    # ===== The execution engine (Task 3: spawn/stream/reap/cancel) =====

    def run_task(self, key, run_id, progress_cb=None):
        """Execute one claimed task end-to-end; NEVER raises.

        Re-probes the CLI (absent -> failed ``cli_unavailable``),
        resolves the channel (degraded -> failed with the reason),
        composes the argv, spawns through the injectable seam with
        ``start_new_session=True`` and PIPEs and an env that is exactly
        ``dict(os.environ)``, streams stderr through the best-effort
        parser (``progress_cb(key, percent)`` at most once per
        integer-percent change; None percent = indeterminate), reaps
        in cancel-aware chunks, then classifies: nonzero exit ->
        failed (``cancelled_by_operator`` when the flag is set, else
        ``exit_<code>``); exit 0 -> the Pitfall-3 landing gate (shape-C
        rename first, then all three split CSVs must exist) -> done or
        failed ``landing_incomplete``. The verbatim stdout+stderr lands
        in ``logs/<sanitized-key>.log`` under the state root (D-03).

        Args:
            key (str): the claimed dataset registry key.
            run_id (str): the caller's run tag (echoed on the event).
            progress_cb: optional ``callable(key, percent)`` fired from
                the stderr reader thread.

        Returns:
            QueueEvent: the structured outcome (state persisted).
        """
        cli = resolve_modelscope_cli(self._cli_path)
        if cli is None:
            return self._finish(
                key, run_id, "failed", None,
                (PROBLEM_CLI_UNAVAILABLE,), ("cli=missing",),
                argv=None, returncode=None)
        spec = self.resolve_channel(key)
        reason = spec.reason_code if spec is not None else "unknown_key"
        if spec is None or reason is not None:
            return self._finish(
                key, run_id, "failed", None, (reason,),
                ("channel_reason=" + reason,), argv=None,
                returncode=None)
        argv = compose_download_argv(spec, cli)
        if argv is None:
            return self._finish(
                key, run_id, "failed", None, (reason,),
                ("channel_reason=" + reason,), argv=None,
                returncode=None)
        try:
            proc = self._spawner(
                argv, env=dict(os.environ), start_new_session=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as exc:  # noqa: BLE001 — the service boundary
            # (the _invoke discipline): ANY launch failure yields a
            # failed event, never an exception crossing to the worker.
            return self._finish(
                key, run_id, "failed", None,
                (PROBLEM_SUBPROCESS_ERROR,), (repr(exc),),
                argv=argv, returncode=None)
        with self._lock:
            self._active[key] = proc
        stdout_parts: list[str] = []
        stderr_parts: list[str] = []
        percent_state = {"last_fired": None}

        def on_stdout(text):
            stdout_parts.append(text)

        def on_stderr(text):
            stderr_parts.append(text)
            if progress_cb is None:
                return
            files, items = parse_progress(text)
            percent = items
            if percent is None and files:
                percent = next(reversed(files.values()))
            if percent is None or percent == percent_state["last_fired"]:
                return
            percent_state["last_fired"] = percent
            progress_cb(key, percent)

        out_thread = threading.Thread(
            target=_pump, args=(proc.stdout, on_stdout), daemon=True)
        err_thread = threading.Thread(
            target=_pump, args=(proc.stderr, on_stderr), daemon=True)
        out_thread.start()
        err_thread.start()
        returncode = self._reap(proc, key)
        out_thread.join(timeout=5)
        err_thread.join(timeout=5)
        with self._lock:
            self._active.pop(key, None)
        stdout_text = "".join(stdout_parts)
        stderr_text = "".join(stderr_parts)
        details = [
            "exit_code=" + str(returncode),
            "start_marker=" + str(START_MARKER in stdout_text).lower(),
            "success_marker="
            + str(SUCCESS_MARKER in stdout_text).lower(),
        ]
        if returncode != 0:
            problem = (PROBLEM_CANCELLED
                       if key in self._cancel_requested
                       else "exit_" + str(returncode))
            return self._finish(
                key, run_id, "failed", percent_state["last_fired"],
                (problem,), tuple(details), stdout_text, stderr_text,
                argv=argv, returncode=returncode)
        landing_problem, landing_details = self._landing_details(spec)
        details.extend(landing_details)
        if landing_problem is not None:
            return self._finish(
                key, run_id, "failed", percent_state["last_fired"],
                (landing_problem,), tuple(details), stdout_text,
                stderr_text, argv=argv, returncode=returncode)
        return self._finish(
            key, run_id, "done", percent_state["last_fired"], (),
            tuple(details), stdout_text, stderr_text, argv=argv,
            returncode=returncode)

    def _reap(self, proc, key):
        """Reap one owned process in cancel-aware chunks (Pitfall 1).

        No artificial total timeout (T-10-01-04): waits in
        ``REAP_INTERVAL_SECONDS`` chunks, re-checking the
        cancel-requested flag; once cancel is seen, waits the SIGTERM
        grace window then escalates to SIGKILL on the WHOLE group.
        """
        while True:
            try:
                return proc.wait(timeout=REAP_INTERVAL_SECONDS)
            except subprocess.TimeoutExpired:
                if key not in self._cancel_requested:
                    continue
                try:
                    return proc.wait(timeout=SIGTERM_GRACE_SECONDS)
                except subprocess.TimeoutExpired:
                    _signal_group(proc, signal.SIGKILL)
                    return proc.wait()

    def _landing_details(self, spec):
        """Run the shape-C rename then the Pitfall-3 landing gate.

        Returns:
            tuple[str | None, list[str]]: ``(problem, details)`` — the
            problem code when the landing failed (None on success),
            plus the data tokens (rename outcome, landing=ok or the
            missing relative paths).
        """
        details = []
        if spec.rename is not None:
            applied = self._apply_rename(spec, details)
            if applied is not None:
                return applied, details
        datasets_root = self._pipeline_dir / "datasets"
        if spec.shape == "B":
            landing_dir = spec.local_dir
        else:
            landing_dir = spec.local_dir / spec.final_task_dir
        missing = []
        try:
            relative = landing_dir.relative_to(datasets_root)
        except ValueError:
            relative = Path(landing_dir.name)
        for split in LANDING_SPLITS:
            if not (landing_dir / split).is_file():
                missing.append(str(relative / split))
        if missing:
            details.extend("missing=" + rel for rel in missing)
            return PROBLEM_LANDING_INCOMPLETE, details
        details.append("landing=ok")
        return None, details

    def _apply_rename(self, spec, details):
        """The shape-C post-landing rename (the four explicit cases).

        Returns:
            str | None: a problem code when the rename must fail
            (``rename_target_exists`` / ``rename_error``); None when
            applied, skipped (target already complete), or fallen
            through (source absent — the landing check names the
            missing files).
        """
        datasets_root = self._pipeline_dir / "datasets"
        source = datasets_root / spec.rename[0]
        target = datasets_root / spec.rename[1]
        if target.exists():
            if self._missing_splits(target):
                if source.exists():
                    # operator data is NEVER overwritten
                    return PROBLEM_RENAME_TARGET_EXISTS
                details.append("rename=skip_source_absent")
                return None
            details.append("rename=skip_target_complete")
            return None
        if not source.exists():
            details.append("rename=skip_source_absent")
            return None
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            os.rename(source, target)
        except OSError as exc:
            details.append("rename_error=" + repr(exc))
            return PROBLEM_RENAME_ERROR
        details.append("rename=applied")
        return None

    @staticmethod
    def _missing_splits(task_dir):
        """The split files missing under one task dir (empty = all)."""
        return [split for split in LANDING_SPLITS
                if not (task_dir / split).is_file()]

    def _finish(self, key, run_id, state, percent, problems, details,
                stdout_text="", stderr_text="", argv=None,
                returncode=None):
        """Persist one terminal transition + write the verbatim log +
        emit the event (the single exit path for every outcome)."""
        log_rel = self._write_log(key, stdout_text, stderr_text, argv,
                                  returncode)
        kind = KIND_DATASET
        with self._lock:
            for entry in self._entries:
                if entry["key"] != key:
                    continue
                entry["state"] = state
                entry["finished_at"] = _now_iso()
                entry["last_percent"] = percent
                entry["problems"] = list(problems)
                entry["log_path"] = log_rel
                kind = entry["kind"]
                self._persist_locked()
                break
        self._cancel_requested.discard(key)
        return QueueEvent(
            run_id=run_id, key=key, kind=kind, state=state,
            last_percent=percent, problems=tuple(problems),
            details=tuple(details), log_path=log_rel)

    def _write_log(self, key, stdout_text, stderr_text, argv,
                   returncode):
        """Write the verbatim capture to ``logs/<sanitized-key>.log``
        under the state root (D-03 drill-down content).

        Returns:
            str | None: the log path relative to the state root, or
            None when the write itself failed (never a crash).
        """
        name = _sanitize_key(key) + ".log"
        argv_lines = "\n".join(argv) if argv is not None else "(none)"
        text = ("[argv]\n" + argv_lines
                + "\n[exit] " + ("-" if returncode is None
                                 else str(returncode))
                + "\n[stdout]\n" + stdout_text
                + "\n[stderr]\n" + stderr_text)
        try:
            settings.atomic_write(
                self._state_path.parent / LOG_DIR_NAME / name, text)
        except OSError:
            return None
        return LOG_DIR_NAME + "/" + name

    # ===== Missing-set derivation (the D-13 input) =====

    def missing_datasets(self):
        """MissingInfo rows for official keys missing per n_audit.

        Computed over the official registry (direct file read, never
        the custom overlay — download targets are the official
        ModelScope mirrors) plus the committed ``n_audit.json``
        presence view (``registries.load_n_audit``; the TUI computes
        nothing). An absent/unreadable n_audit yields NO rows — the
        missing set is unknowable, not "everything".

        Returns:
            list[MissingInfo]: one frozen row per missing official key,
            in registry file order.
        """
        audit_tasks = registries.load_n_audit()
        if audit_tasks is None:
            return []
        try:
            registry = self._official_registry()
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return []
        rows = []
        for key, entry in registry.items():
            if not isinstance(entry, dict):
                continue
            presence = registries.presence_for(key, audit_tasks)
            if presence.status != registries.PRESENCE_MISSING:
                continue
            spec = self._spec_from_entry(key, entry)
            rows.append(MissingInfo(
                key=key,
                declared_total=_declared_total(entry),
                channel=channel_state(spec),
                reason_code=spec.reason_code,
                source_url=spec.source_url))
        return rows

    # ===== Channel resolution (R-01/R-02) =====

    def resolve_channel(self, key):
        """Resolve one dataset key's download channel.

        R-01: the official entry's ``download_url`` first; only when
        that host is not modelscope.cn does the modelscope mirror in
        ``download_url_alternates`` win. The repo id is derived by
        urlparse path parsing and validated against the allowlist
        regex before anything reaches argv (T-10-01-01).

        Args:
            key (str): the dataset registry key.

        Returns:
            ChannelSpec | None: the resolved spec, or None when the
            key is not an official registry key (custom keys are not
            download targets).
        """
        try:
            registry = self._official_registry()
        except (OSError, json.JSONDecodeError,
                UnicodeDecodeError):
            return self._degraded_spec(
                key, reason=REASON_REGISTRY_UNREADABLE)
        entry = registry.get(key)
        if not isinstance(entry, dict):
            return None
        return self._spec_from_entry(key, entry)

    def _spec_from_entry(self, key, entry):
        """Resolve the channel for one official registry entry."""
        url = self._winning_url(entry)
        if url is None:
            return self._degraded_spec(
                key, reason=REASON_NO_MIRROR, source_url=None)
        repo_id = _repo_id_from_url(url)
        if not repo_id or not re.fullmatch(REPO_ID_RE_PART, repo_id):
            return self._degraded_spec(
                key, reason=REASON_MALFORMED_REPO_ID, source_url=url)
        derived = _group_and_task(entry)
        if derived is None:
            return self._degraded_spec(
                key, reason=REASON_MALFORMED_PATH, source_url=url,
                repo_id=repo_id)
        group, task = derived
        datasets_root = self._pipeline_dir / "datasets"
        if repo_id in SHAPE_D_REPOS:
            return self._degraded_spec(
                key, reason=REASON_SHAPE_D, source_url=url,
                repo_id=repo_id, shape=None, final_task_dir=task)
        if repo_id not in SHAPE_A_REPOS and repo_id not in SHAPE_B_REPOS \
                and repo_id != SHAPE_C_REPO:
            return self._degraded_spec(
                key, reason=REASON_UNKNOWN_REPO, source_url=url,
                repo_id=repo_id, shape=None, final_task_dir=task)
        exclude = EXCLUDE_PATTERNS
        if repo_id in SHAPE_B_REPOS:
            return ChannelSpec(
                key=key, repo_id=repo_id, shape="B",
                local_dir=datasets_root / group / task,
                include=(), exclude=exclude, rename=None,
                final_task_dir=task, source_url=url, reason_code=None)
        if repo_id == SHAPE_C_REPO:
            subtree = SHAPE_C_SUBTREES.get(key)
            if subtree is None:
                return self._degraded_spec(
                    key, reason=REASON_UNKNOWN_REPO, source_url=url,
                    repo_id=repo_id, shape=None, final_task_dir=task)
            return ChannelSpec(
                key=key, repo_id=repo_id, shape="C",
                local_dir=datasets_root / group,
                include=(subtree + "/*",), exclude=exclude,
                rename=(group + "/" + subtree, group + "/" + task),
                final_task_dir=task, source_url=url, reason_code=None)
        return ChannelSpec(
            key=key, repo_id=repo_id, shape="A",
            local_dir=datasets_root / group,
            include=(task + "/*",), exclude=exclude, rename=None,
            final_task_dir=task, source_url=url, reason_code=None)

    @staticmethod
    def _winning_url(entry):
        """R-01: the primary URL when it is the modelscope mirror,
        else the modelscope alternate — None when neither qualifies."""
        primary = entry.get("download_url")
        if _is_modelscope_url(primary):
            return primary
        alternate = entry.get("download_url_alternates")
        if _is_modelscope_url(alternate):
            return alternate
        return None

    @staticmethod
    def _degraded_spec(key, reason, source_url=None, repo_id=None,
                       shape=None, final_task_dir=None):
        """Build the never-crash degraded resolution (data, no argv)."""
        return ChannelSpec(
            key=key, repo_id=repo_id, shape=shape, local_dir=None,
            include=(), exclude=(), rename=None,
            final_task_dir=final_task_dir, source_url=source_url,
            reason_code=reason)

    def _official_registry(self):
        """Read the OFFICIAL dataset registry directly (not the
        overlay loader — download targets are the official ModelScope
        mirrors regardless of any custom overlay state).

        Returns:
            dict: the parsed official registry (file order preserved).
        """
        with open(self._pipeline_dir / registry_loader.DATASETS_INFO_NAME,
                  "r", encoding="utf-8") as fh:
            return json.load(fh)
