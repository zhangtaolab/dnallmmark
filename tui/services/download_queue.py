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
- D-09 (10-02): after every landed download the service automatically
  runs the audit row-count kernel as a subprocess — a candidate-only
  temp registry containing exactly the one key with an ABSOLUTE
  ``Dataset_path``, ``--datasets-root`` pointed at an inert temp dir,
  all four output flags at temp paths, and ``CUSTOM_DIR_ENV`` pinned to
  an empty temp overlay (the gauntlet audit-leg shape re-implemented
  in-module, 10-RESEARCH Q4). The TUI never counts CSV rows itself —
  the kernels are the audit subprocess's alone; this service stages,
  invokes, parses, and compares declared-vs-measured, nothing more.
  Verdicts come from the parsed temp ``n_audit.json``: pass iff
  ``missing`` false, train/dev/test each rows > 0 (bool excluded),
  ``unified_eval_n`` > 0, and every declared ``Train``/``Dev``/``Test``
  int equals the measured rows per split.
- D-09 done gate: done = landed AND reconcile pass; a reconcile
  mismatch lands the entry in state ``mismatch`` carrying the declared
  and measured numbers for the banner — mismatch NEVER auto-deletes
  anything (D-07).
- D-11: ``merge_presence(audit_tasks, reconcile_results)`` overlays
  reconcile-PASS keys (``reconciled_rows()`` over the persisted done
  entries) onto the committed n_audit view so the UNCHANGED
  ``registries.presence_for`` flips to present — a landed-but-
  mismatched dataset never flips (UI-SPEC semantic 6); the committed
  ``n_audit.json`` itself is never written by this path.
- D-10/R-03: the committed ``dnallm-mark/data/n_audit.json`` baseline
  is NEVER written by the reconcile or presence paths; only the
  explicit ``reaudit_baseline`` method runs the audit script with its
  DEFAULT outputs (the four worktree artifacts, maintainer review and
  commit) — no automatic path ever calls it.

Subprocess discipline (the Phase 7 T-03-10 rule, Pitfall 1): argv is a
LIST, the Popen handle is owned directly (never a wrapper PID — the
live-probe orphan lesson), and cancel goes through ``os.killpg`` on the
process group (SIGTERM, wait, SIGKILL escalation). Nothing the service
itself writes ever lands outside the XDG state root (queue state + log
files); the committed registries and ``n_audit.json`` are read-only to
this module.

ZERO textual imports. Dependencies: stdlib (subprocess/threading/os/
sys/re/json/shutil/signal/tempfile) + ``artifact_loader`` (tolerant
artifact parses) + ``registry_loader`` (official file-name constants)
+ the sibling ``registries`` (committed n_audit presence) and
``settings`` (state root + atomic write) services.
"""

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import artifact_loader  # top-level module (pipeline/ sys.path root, D-19)
import registry_loader  # top-level module (pipeline/ sys.path root)

from tui.services import registries, settings, zenodo_bundle

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

#: The DATA-04 whole-package bundle kind (10-03): ``run_task``
#: dispatches these entries to the zenodo branch — fresh probe ->
#: defensive parse -> streamed download to staging -> guarded extract
#: -> per-key landing check -> per-key reconcile (D-12).
KIND_ZENODO_BUNDLE = "zenodo_bundle"

#: The bundle entry's queue identity — the only Zenodo string constant
#: in this module (the record id/URL live in ``zenodo_bundle``).
ZENODO_BUNDLE_KEY = "zenodo-19135551"

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

#: The enqueue action for a persistence refusal (WR-04): the entry
#: never landed — the queue state file could not be written (read-only
#: state root, full disk, quota). The screens toast it, never silently.
ACTION_PERSIST_FAILED = "persist_failed"

#: The enqueue action for every defensive degraded reason outside
#: ``_DISABLED_REASONS`` (WR-06): no mirror, malformed values, an
#: unreadable registry — a channel-unavailable state carrying its OWN
#: reason code, never collapsed into the shape-D ``disabled`` outcome
#: whose toast claims a mirror layout the channel never resolved.
ACTION_UNKNOWN = "unknown"

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

# ===== The D-09/D-10 reconcile kernel (10-02) =====
#
# After every landed download the service runs the audit row-count
# kernel as a subprocess — the Phase 9 gauntlet audit-leg shape
# re-implemented in-module (the 10-RESEARCH Q4 ruling: a thin
# re-implementation, NOT a GauntletService import — the gauntlet's
# candidate/custom staging semantics are not this leg's). The kernels
# (row counting, non-ACGT census, subset survival) are the audit
# script's alone; this service stages, invokes, parses, and compares
# declared-vs-measured — nothing more (binding constraint 5).

#: The subprocess legs' script name, resolved against the repo root.
AUDIT_SCRIPT_NAME = "audit_n_frequencies.py"

#: The audit leg's parsed artifact name (the writer's own constant,
#: restated — importing the writer would violate the services-tier
#: import discipline).
N_AUDIT_NAME = "n_audit.json"

#: The whole-dir overlay override (the registry_loader env contract):
#: every reconcile/reaudit env pins it to an EMPTY temp dir so the
#: operator's real custom overlay can never leak into a verdict or the
#: refreshed baseline (T-10-02-02/03).
CUSTOM_DIR_ENV = "DNALLMMARK_CUSTOM_REGISTRY_DIR"

#: The audit kernel's own split order and the declared-count field each
#: split reconciles against (the gauntlet's constants, verbatim).
_AUDIT_SPLIT_ORDER = ("train", "dev", "test")
_DECLARED_SPLIT_FIELDS = (
    ("train", "Train"),
    ("dev", "Dev"),
    ("test", "Test"),
)

#: ReconcileOutcome.verdict values.
VERDICT_PASS = "pass"
VERDICT_MISMATCH = "mismatch"
VERDICT_FAILED = "failed"

#: The reconcile/reaudit subprocess timeouts (T-10-02-05: bounded,
#: constructor-overridable; a hang is absorbed into a failed outcome).
DEFAULT_TIMEOUT_RECONCILE = 300
DEFAULT_TIMEOUT_REAUDIT = 300

# ===== Engine problem codes (machine vocabulary) =====

PROBLEM_CLI_UNAVAILABLE = "cli_unavailable"
PROBLEM_CANCELLED = "cancelled_by_operator"
PROBLEM_LANDING_INCOMPLETE = "landing_incomplete"
PROBLEM_RENAME_TARGET_EXISTS = "rename_target_exists"
PROBLEM_RENAME_ERROR = "rename_error"
PROBLEM_SUBPROCESS_ERROR = "subprocess_error"

#: The zenodo bundle branch's problem codes (10-03; machine
#: vocabulary — the screens render, never parse).
PROBLEM_RECORD_NOT_PUBLIC = "record_not_public"
PROBLEM_RECORD_UNREADABLE = "record_unreadable"
PROBLEM_FILE_LIST_UNREADABLE = "record_file_list_unreadable"
PROBLEM_BUNDLE_DOWNLOAD_FAILED = "bundle_download_failed"
PROBLEM_BUNDLE_LANDED_ZERO = "bundle_landed_zero"
PROBLEM_BUNDLE_RECONCILE_FAILED = "bundle_reconcile_failed"

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


# ===== The D-11 presence overlay (10-02 Task 2) =====


def merge_presence(audit_tasks, reconcile_results):
    """Overlay reconcile-pass rows onto the committed n_audit view.

    The D-11 flip substrate (RESEARCH Pattern 3): a PURE data
    composition — the committed ``n_audit.json`` alone can never flip a
    freshly downloaded dataset's presence (that file only changes via
    the explicit ``g`` re-audit), so the selection/env screens consume
    ``merge_presence(load_n_audit(), reconciled_rows())`` and the
    UNCHANGED Phase 8 ``registries.presence_for`` maps the merged view
    (its four-status vocabulary stays the contract).

    Only reconcile-PASS (done) keys belong in ``reconcile_results`` —
    a landed-but-mismatched dataset NEVER flips (UI-SPEC semantic 6);
    ``run_task``'s done gate is what enforces that upstream.

    Args:
        audit_tasks (dict | None): the committed tasks mapping from
            ``registries.load_n_audit()`` (None = missing/corrupt —
            the overlay alone still serves the column).
        reconcile_results (dict): ``{key: (train, dev, test)}`` — the
            measured row ints for done entries (from
            ``reconciled_rows``).

    Returns:
        dict: a NEW tasks-shaped dict: ``dict(audit_tasks or {})``
        overlaid with ``{key: {"missing": False, "splits": {...}}}``
        per reconcile-pass key. Inputs are never mutated; zero I/O.
    """
    merged = dict(audit_tasks) if audit_tasks else {}
    for key, rows in (reconcile_results or {}).items():
        train, dev, test = rows
        merged[key] = {
            "missing": False,
            "splits": {
                "train": {"rows": train},
                "dev": {"rows": dev},
                "test": {"rows": test},
            },
        }
    return merged


def reconciled_rows(state_path=None):
    """Derive the reconcile-pass overlay from the persisted queue state.

    Read-only and tolerant (the artifact_loader None sentinel —
    degrade, never crash): entries with state ``done`` and a populated
    ``reconcile.measured`` contribute ``{key: (train, dev, test)}``;
    every other shape (mismatch, failed, pending, done without a
    reconcile, non-integer measured rows, an absent/corrupt file)
    contributes nothing.

    Args:
        state_path: the queue state file; None resolves
            ``settings.state_dir() / QUEUE_FILE_NAME``.

    Returns:
        dict: ``{key: (train, dev, test)}`` for done entries (empty
        when nothing reconciled or the state is unreadable).
    """
    if state_path is None:
        path = settings.state_dir() / QUEUE_FILE_NAME
    else:
        path = Path(state_path)
    doc = artifact_loader.load_json_artifact(path)
    if not isinstance(doc, dict):
        return {}
    entries = doc.get("entries")
    if not isinstance(entries, list):
        return {}
    results: dict[str, tuple[int, int, int]] = {}
    for raw in entries:
        if not isinstance(raw, dict) or raw.get("state") != "done":
            continue
        key = raw.get("key")
        if not isinstance(key, str) or not key:
            continue
        reconcile = raw.get("reconcile")
        if not isinstance(reconcile, dict):
            continue
        measured = reconcile.get("measured")
        if not isinstance(measured, dict):
            continue
        rows = []
        for split in _AUDIT_SPLIT_ORDER:
            value = measured.get(split)
            if not isinstance(value, int) or isinstance(value, bool):
                rows = None
                break
            rows.append(value)
        if rows is None:
            continue
        results[key] = (rows[0], rows[1], rows[2])
    return results


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
            ``unknown_key`` / ``disabled`` (the shape-D and
            unknown-repo reasons only) / ``unknown`` (every defensive
            reason — no mirror, malformed values, an unreadable
            registry; WR-06) / ``cli_unavailable`` / ``persist_failed``
            (the unwritable-state-rail refusal, WR-04).
        key: the requested dataset key.
        reason_code: the machine reason when action is ``disabled`` or
            ``unknown`` (e.g. ``shape_d_layout``,
            ``registry_unreadable``) — None otherwise.
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


@dataclass(frozen=True)
class ReconcileOutcome:
    """One reconcile leg's structured verdict (D-09/D-10; DATA, never
    screen copy — the 10-04 banner renders these).

    Attributes:
        ok: True iff verdict is ``pass`` (the done gate).
        verdict: ``pass`` / ``mismatch`` / ``failed`` — ``mismatch`` is
            a parsed-artifact verdict that disproves the declared shape
            (declared-vs-measured inequality, missing still true, a
            split with no positive rows, unified_eval_n not positive);
            ``failed`` is every infrastructure failure (nonzero exit,
            timeout, unparseable/absent n_audit.json, key absent from
            the tasks map, launch error, unreadable registry).
        declared: the registry entry's declared ``Train``/``Dev``/
            ``Test`` ints that carried a declaration (None when the
            entry declared none).
        measured: the parsed per-split row counts (an int per split the
            record carried, 0 included — the banner's data; None when
            nothing was measured).
        unified_eval_n: the parsed unified eval N (int or None).
        problems: machine problem codes (on mismatch they name the
            split and BOTH numbers, e.g.
            ``Train_mismatch_declared=10_measured=3``).
        raw_output: the verbatim captured subprocess output.
    """

    ok: bool
    verdict: str
    declared: dict | None
    measured: dict | None
    unified_eval_n: int | None
    problems: tuple[str, ...]
    raw_output: str = ""


@dataclass(frozen=True)
class ReauditOutcome:
    """One explicit ``g`` re-audit's structured result (D-10/R-03;
    DATA, never screen copy).

    The re-audit runs the audit script with its DEFAULT outputs — the
    four artifacts land in the WORKTREE exactly as the CLI command
    writes them (``python script/audit_n_frequencies.py``, the command
    ENV_ROUTE already prints); the git diff is the maintainer's review
    surface and the maintainer commits the refreshed baseline. There is
    deliberately NO atomic-replace trickery and NO narrow write here.

    Attributes:
        ok: True iff the subprocess exited 0.
        details: machine data tokens (``exit_code=0``, ``timeout``,
            ``timeout_seconds=N``, ``subprocess_error=<repr>``).
        raw_output: the verbatim captured subprocess output.
    """

    ok: bool
    details: tuple[str, ...]
    raw_output: str = ""


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


def _default_runner(argv, **kwargs):
    """The real completed-process seam (the injectable default; the
    gauntlet runner shape — used by the reconcile/reaudit legs).

    The service itself passes ``capture_output=True, text=True,
    errors="replace"`` (plus ``timeout``/``env``) on every call — the
    same kwargs the fakes record — so the default is a pure forward to
    ``subprocess.run`` (the replace policy keeps a non-UTF-8-locale
    decode a replacement-character capture, never an exception — WR-05).

    Args:
        argv (list): the LIST argv (never a shell string).
        **kwargs: ``capture_output``/``text``/``errors``/``timeout``/
            ``env``.

    Returns:
        subprocess.CompletedProcess: with captured text stdout/stderr.
    """
    return subprocess.run(argv, check=False, **kwargs)


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
                 runner=None, cli_path=None,
                 timeout_reconcile=DEFAULT_TIMEOUT_RECONCILE,
                 timeout_reaudit=DEFAULT_TIMEOUT_REAUDIT,
                 zenodo_fetch=None):
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
            runner: the completed-process seam for the reconcile/reaudit
                legs (the gauntlet runner shape: ``argv,
                capture_output=True, text=True, errors="replace",
                timeout=..., env=...``); None wraps ``subprocess.run``.
            cli_path: an explicit modelscope console-script path; None
                probes the standard resolution order at each use.
            timeout_reconcile: per-reconcile timeout seconds
                (T-10-02-05; default 300).
            timeout_reaudit: per-reaudit timeout seconds (default 300).
            zenodo_fetch: the urlopen-shaped seam for the whole
                DATA-04 bundle branch (probe + record fetch + file
                downloads); None uses the real ``urllib.request`` (the
                bundle lane is stdlib HTTP — NO modelscope CLI is ever
                involved, D-12).
        """
        self._repo_root = (REPO_ROOT if repo_root is None
                           else Path(repo_root).resolve())
        self._pipeline_dir = self._repo_root / "pipeline"
        if state_path is None:
            state_path = settings.state_dir() / QUEUE_FILE_NAME
        self._state_path = Path(state_path)
        self._spawner: Any = (_default_spawner if spawner is None
                              else spawner)
        self._runner: Any = (_default_runner if runner is None
                             else runner)
        self._timeout_reconcile = timeout_reconcile
        self._timeout_reaudit = timeout_reaudit
        self._cli_path = cli_path
        self._zenodo_fetch = zenodo_fetch
        self._lock = threading.Lock()
        self._entries: list[dict] = []
        self._cancel_requested: set[str] = set()
        self._active: dict[str, Any] = {}
        # The most recent corrupt-load diagnostic, remembered for the
        # session (10-06): ``load()`` returns it exactly once (the file
        # is quarantined on first read), but the screen's later
        # snapshot reloads must still surface it — never silent loss.
        self._last_diagnostic: str | None = None

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
            if entry["state"] != "downloading":
                continue
            if entry["key"] in self._active:
                # a LIVE run owns this state: the boot-time downgrade is
                # for interrupted restarts only — a mid-flight reload
                # (the screen's snapshot worker re-loading the file
                # while the driver executes) must never re-queue the
                # entry currently being downloaded (10-06)
                continue
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
        self._last_diagnostic = message   # session memory (10-06)
        try:
            os.replace(path, path.with_name(path.name + ".corrupt"))
        except OSError as exc:
            message += "; sidecar move failed: " + repr(exc)
        self._entries = []
        return message

    def last_load_diagnostic(self):
        """The most recent corrupt-load diagnostic, or None.

        Session memory (10-06): ``load()`` returns the diagnostic string
        exactly once (the corrupt file is quarantined on that first
        read, so every later load is healthy), but the degradation must
        stay visible — the screen's snapshot reads this accessor so the
        status line survives its reloads until the process exits. A
        healthy session never sets it; a healthy load never clears it.

        Returns:
            str | None: the remembered diagnostic, or None.
        """
        with self._lock:
            return self._last_diagnostic

    def state_root(self):
        """The queue's OWN state root — the parent of the state file.

        IN-05: entry ``log_path`` values resolve against THIS root (the
        exact seam ``_write_log`` writes through), so a service
        constructed with an explicit ``state_path`` outside
        ``settings.state_dir()`` reads back the logs it wrote — the
        drill-down never silently empties.

        Returns:
            Path: the state root the state file and logs live under.
        """
        return self._state_path.parent

    def entries(self):
        """Immutable copies of the current entries, in file order.

        Returns:
            list[QueueEntry]: frozen snapshots — mutating them can
            never touch the service's live state.
        """
        with self._lock:
            return [_frozen(entry) for entry in self._entries]

    def _persist_locked(self):
        """Write the whole queue through the ONE atomic rail (D-05).

        WR-04: an ``OSError`` from the rail (read-only state dir, full
        disk, quota) is ABSORBED into a returned diagnostic — never an
        exception across the pinned never-raises mutator boundary. The
        callers own the degraded outcome: ``enqueue`` refuses and rolls
        its append back, ``claim_next`` reverts the claim and answers
        None, ``_finish`` still emits the event carrying a
        ``persist_error=`` problem; the remaining mutators (retry,
        cancel, the boot downgrade) simply keep their in-memory truth —
        the state file catches up on the next successful write or the
        restart downgrade.

        Returns:
            str | None: the failure diagnostic, or None on success.
        """
        doc = {
            "schema_version": SCHEMA_VERSION,
            "entries": [{field: entry[field] for field in _ENTRY_FIELDS}
                        for entry in self._entries],
        }
        try:
            settings.atomic_write(
                self._state_path,
                json.dumps(doc, indent=4, ensure_ascii=False))
        except OSError as exc:
            return repr(exc)
        return None

    # ===== Mutators (enqueue / retry / cancel) =====

    def _resolve_cli(self):
        """Resolve the CLI with the AVAILABILITY gate (10-06).

        ``resolve_modelscope_cli`` returns an explicit ``cli_path``
        verbatim (the pinned 10-01 contract — a pure resolution
        function). The availability gates (``enqueue``/``run_task``)
        additionally refuse a resolved path that points NOWHERE: an
        explicit pointer to nowhere IS the probed-unavailable state —
        the honest ``cli_unavailable`` outcome, never a spawn attempt
        of a nonexistent binary.

        Returns:
            Path | None: an existing console-script path, or None.
        """
        cli = resolve_modelscope_cli(self._cli_path)
        if cli is not None and not cli.is_file():
            return None
        return cli

    def enqueue(self, key):
        """Idempotently append one pending dataset entry (D-08).

        Outcome order: an existing entry of ANY state yields
        ``already_queued`` with no state change; an unknown official
        key yields ``unknown_key`` (custom keys are not download
        targets — the official registry is the only URL authority); a
        shape-D/unknown-repo channel yields ``disabled`` and every
        OTHER degraded reason (no mirror, malformed values, an
        unreadable registry) yields ``unknown`` — each carrying the
        machine reason + the drill-down ``source_url`` (WR-06: the
        screens can never claim the mirror-layout copy for a reason
        that is not it); a CLI-absent machine yields
        ``cli_unavailable``; a state file that cannot be written yields
        ``persist_failed`` (the append is rolled back — WR-04: never an
        exception, never a ghost row); otherwise the pending entry
        appends and persists (``enqueued``).

        Args:
            key (str): the dataset registry key.

        Returns:
            EnqueueOutcome: the structured result (never an exception).
        """
        cli = self._resolve_cli()
        with self._lock:
            if any(entry["key"] == key for entry in self._entries):
                return EnqueueOutcome(
                    action="already_queued", key=key)
            spec = self.resolve_channel(key)
            if spec is None:
                return EnqueueOutcome(action="unknown_key", key=key)
            if spec.reason_code is not None:
                action = ("disabled" if spec.reason_code in _DISABLED_REASONS
                          else ACTION_UNKNOWN)
                return EnqueueOutcome(
                    action=action, key=key,
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
            if self._persist_locked() is not None:
                self._entries.pop()   # the refusal leaves no ghost row
                return EnqueueOutcome(
                    action=ACTION_PERSIST_FAILED, key=key)
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

    def enqueue_zenodo(self):
        """Idempotently append the whole-package bundle entry (D-12).

        The DATA-04 alternate entry: ONE ``kind=zenodo_bundle`` task
        keyed ``ZENODO_BUNDLE_KEY`` — the whole record lands in a
        single queue row whose task cell renders the bundle task name.
        NO CLI probe runs here: the bundle lane is stdlib HTTP (the
        modelscope CLI's probed-unavailable state is irrelevant); the
        publication probe happens at RUN time, so activation is the
        probe flipping — zero code change.

        Returns:
            EnqueueOutcome: ``enqueued`` or ``already_queued`` (the
            D-08 per-key idempotence, the key being the bundle key).
        """
        with self._lock:
            if any(entry["key"] == ZENODO_BUNDLE_KEY
                   for entry in self._entries):
                return EnqueueOutcome(
                    action="already_queued", key=ZENODO_BUNDLE_KEY)
            self._entries.append({
                "key": ZENODO_BUNDLE_KEY,
                "kind": KIND_ZENODO_BUNDLE,
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
            return EnqueueOutcome(
                action="enqueued", key=ZENODO_BUNDLE_KEY)

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
        the channel, D-06 resume). For the zenodo bundle lane (no
        process handle — stdlib HTTP) the flag alone carries the
        cancel: ``_run_zenodo_bundle`` polls it at every stage boundary
        and finishes failed ``cancelled_by_operator`` (WR-01). Any
        other state or absent key: a no-op.

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
        stamped, persisted before returning; the restart note's
        ``interrupted`` flag clears HERE (IN-01) — the claim IS the
        resume the note announces, so the flag must not linger on the
        downloading/done/failed rows that follow. WR-04: when that
        persist fails (unwritable state rail), the claim is REVERTED to
        the entry's exact prior shape and None is returned — never an
        exception, never a persisted-downloading entry with no run.

        Returns:
            QueueEntry | None: the claimed snapshot, or None when no
            pending entry exists (or the claim could not persist).
        """
        with self._lock:
            for entry in self._entries:
                if entry["state"] != "pending":
                    continue
                prior = (entry["state"], entry["attempts"],
                         entry["started_at"], entry["interrupted"])
                entry["state"] = "downloading"
                entry["attempts"] = entry["attempts"] + 1
                entry["started_at"] = _now_iso()
                entry["interrupted"] = False
                if self._persist_locked() is not None:
                    entry["state"], entry["attempts"], entry[
                        "started_at"], entry["interrupted"] = prior
                    return None
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
        rename first, then all three split CSVs must exist) -> the
        D-09 reconcile gate: pass -> done (the entry's reconcile field
        populated), mismatch -> state mismatch carrying the declared
        and measured numbers (D-07: nothing is ever deleted), failed
        reconcile -> state failed. The verbatim stdout+stderr plus the
        reconcile output land in ``logs/<sanitized-key>.log`` under the
        state root (D-03).

        Args:
            key (str): the claimed dataset registry key.
            run_id (str): the caller's run tag (echoed on the event).
            progress_cb: optional ``callable(key, percent)`` fired from
                the stderr reader thread.

        Returns:
            QueueEvent: the structured outcome (state persisted).
        """
        if self._entry_kind(key) == KIND_ZENODO_BUNDLE:
            return self._run_zenodo_bundle(key, run_id)
        cli = self._resolve_cli()
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
        # D-09: done = landed AND reconcile pass (the 10-01 amendment).
        outcome = self.reconcile_dataset(key, run_id)
        details.append("reconcile_verdict=" + outcome.verdict)
        if outcome.ok:
            return self._finish(
                key, run_id, "done", percent_state["last_fired"], (),
                tuple(details), stdout_text, stderr_text, argv=argv,
                returncode=returncode,
                reconcile=self._reconcile_payload(outcome),
                reconcile_raw=outcome.raw_output)
        state = ("mismatch" if outcome.verdict == VERDICT_MISMATCH
                 else "failed")
        return self._finish(
            key, run_id, state, percent_state["last_fired"],
            outcome.problems, tuple(details), stdout_text, stderr_text,
            argv=argv, returncode=returncode,
            reconcile=(self._reconcile_payload(outcome)
                       if outcome.verdict == VERDICT_MISMATCH else None),
            reconcile_raw=outcome.raw_output)

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

    # ===== The DATA-04 zenodo bundle branch (10-03, D-12) =====

    # ===== The D-12 publication probe through this service (10-06) =====

    def probe_zenodo(self):
        """The D-12 publication probe through the service's fetch seam.

        The data-manager Backend probes THROUGH the queue when it
        carries this method (the shared-seam rule): routing the real
        adapter's probe here means the constructor's ``zenodo_fetch``
        injection governs it exactly like the bundle lane — the whole
        queue surface is offline-testable by construction, and the
        probe state stays session-memory only (D-12, zero persistence).

        Returns:
            str: ``public`` / ``not_public`` / ``failed``.
        """
        return zenodo_bundle.probe_zenodo_public(opener=self._zenodo_fetch)

    def _entry_kind(self, key):
        """The persisted kind of one entry (dataset when absent)."""
        with self._lock:
            for entry in self._entries:
                if entry["key"] == key:
                    return entry["kind"]
        return KIND_DATASET

    def _cancel_requested_for(self, key):
        """True when the operator cancelled this in-flight key.

        WR-01: the zenodo bundle lane has NO process handle to signal
        (stdlib HTTP, not a Popen group), so its stage boundaries poll
        this probe instead — the CLI lane's reap loop keeps its own
        unlocked read (the owned-handle contract there).
        """
        with self._lock:
            return key in self._cancel_requested

    def _run_zenodo_bundle(self, key, run_id):
        """Execute the whole-package bundle task (never raises).

        The D-12 activation lane — every stage defensive, every
        failure an explicit problem code with verbatim diagnostics in
        ``details``/the drill-down log:

        1. FRESH ``probe_zenodo_public`` (not public -> failed
           ``record_not_public`` with the probe state in details — the
           live-today 404 state);
        2. ``fetch_record_json`` + ``parse_record_files`` (defensive;
           zero conforming entries -> failed
           ``record_file_list_unreadable`` — derive-never-hardcode);
        3. ``download_bundle_files`` into the staging dir under the
           state root (ANY per-file failure -> failed
           ``bundle_download_failed`` — the lane has no byte-resume
           machinery by design; retry re-runs from scratch);
        4. ``extract_bundle_archives`` into ``pipeline/datasets``
           (zip-slip guarded — traversal members are skipped with a
           problem, never extracted);
        5. the post-landing existence check over every
           currently-missing dataset key (the 10-01 checker per key);
        6. per-key reconcile through the 10-02 leg for every LANDED
           key; ``entry.reconcile`` carries the per-key verdict map.

        WR-01 (the operator's bounded escape, T-10-06-01's cancel): the
        cancel-requested flag is honored at EVERY stage boundary (before
        the probe, before the parse, before the download, inside the
        per-file loop through the ``should_cancel`` seam, and before the
        reconcile) — a cancelled bundle finishes failed with
        ``cancelled_by_operator``, mirroring the CLI lane's reap-loop
        contract; no artificial timeout bounds a legitimate multi-GB
        transfer.

        Final state: done iff at least one key landed AND zero
        mismatches; mismatch if any landed key mismatched; failed if
        nothing landed or any stage failed. The branch writes NOTHING
        outside the staging dir + ``pipeline/datasets`` — the
        committed registries and ``n_audit`` stay untouched.

        Args:
            key (str): the claimed bundle key (``ZENODO_BUNDLE_KEY``).
            run_id (str): the caller's run tag (echoed on the event).

        Returns:
            QueueEvent: the structured outcome (state persisted).
        """
        def cancelled():
            return self._cancel_requested_for(key)

        details: list[str] = []
        missing_keys = [row.key for row in self.missing_datasets()]
        details.append("missing_keys=" + str(len(missing_keys)))
        if cancelled():
            return self._finish_cancelled(key, run_id, details)
        probe_state = zenodo_bundle.probe_zenodo_public(
            opener=self._zenodo_fetch)
        details.append("probe=" + probe_state)
        if probe_state != zenodo_bundle.PROBE_PUBLIC:
            return self._finish(
                key, run_id, "failed", None,
                (PROBLEM_RECORD_NOT_PUBLIC,), tuple(details))
        if cancelled():
            return self._finish_cancelled(key, run_id, details)
        record, record_error = zenodo_bundle.fetch_record_json(
            fetch=self._zenodo_fetch)
        if record is None:
            details.append("record_error=" + str(record_error))
            return self._finish(
                key, run_id, "failed", None,
                (PROBLEM_RECORD_UNREADABLE,), tuple(details))
        files = zenodo_bundle.parse_record_files(record)
        details.append("bundle_files=" + str(len(files)))
        if not files:
            return self._finish(
                key, run_id, "failed", None,
                (PROBLEM_FILE_LIST_UNREADABLE,), tuple(details))
        if cancelled():
            return self._finish_cancelled(key, run_id, details)
        staging = settings.state_dir() / zenodo_bundle.STAGING_DIR_NAME
        downloaded, failures = zenodo_bundle.download_bundle_files(
            files, staging, fetch=self._zenodo_fetch,
            should_cancel=cancelled)
        details.append("downloaded=" + str(len(downloaded)))
        if cancelled():
            # a cancel that landed mid-loop (or during the last file's
            # tail) — the loop already stopped at the seam
            return self._finish_cancelled(key, run_id, details)
        if failures:
            details.extend("download_failure=" + failure
                           for failure in failures)
            return self._finish(
                key, run_id, "failed", None,
                (PROBLEM_BUNDLE_DOWNLOAD_FAILED,), tuple(details),
                stderr_text="\n".join(failures))
        extracted, extract_problems = zenodo_bundle.extract_bundle_archives(
            downloaded, self._pipeline_dir / "datasets")
        details.append("extracted=" + str(extracted))
        details.extend(extract_problems)
        if cancelled():
            return self._finish_cancelled(key, run_id, details)
        try:
            registry = self._official_registry()
        except (OSError, json.JSONDecodeError,
                UnicodeDecodeError) as exc:
            details.append("registry_unreadable=" + repr(exc))
            return self._finish(
                key, run_id, "failed", None,
                (PROBLEM_SUBPROCESS_ERROR,), tuple(details),
                stderr_text="\n".join(extract_problems))
        landed, not_landed = self._bundle_landed_keys(
            missing_keys, registry)
        details.append("landed=" + str(len(landed)))
        details.extend("not_landed=" + token for token in not_landed)
        if not landed:
            return self._finish(
                key, run_id, "failed", None,
                (PROBLEM_BUNDLE_LANDED_ZERO,), tuple(details),
                stderr_text="\n".join(extract_problems))
        if cancelled():
            return self._finish_cancelled(key, run_id, details)
        per_key: dict[str, str] = {}
        problems_out: list[str] = []
        has_mismatch = False
        reconcile_failed = False
        reconcile_raw_parts: list[str] = []
        for landed_key in landed:
            outcome = self.reconcile_dataset(landed_key, run_id)
            per_key[landed_key] = outcome.verdict
            reconcile_raw_parts.append(outcome.raw_output)
            if outcome.verdict == VERDICT_MISMATCH:
                has_mismatch = True
            elif outcome.verdict == VERDICT_FAILED:
                reconcile_failed = True
            if outcome.verdict != VERDICT_PASS:
                problems_out.extend(
                    landed_key + ":" + problem
                    for problem in outcome.problems)
        state = ("mismatch" if has_mismatch
                 else "failed" if reconcile_failed else "done")
        if state == "done":
            problems_final: tuple[str, ...] = ()
        elif not problems_out:
            problems_final = (PROBLEM_BUNDLE_RECONCILE_FAILED,)
        else:
            problems_final = tuple(problems_out)
        return self._finish(
            key, run_id, state, None, problems_final, tuple(details),
            stderr_text="\n".join(extract_problems),
            reconcile={"per_key": per_key},
            reconcile_raw="\n".join(reconcile_raw_parts))

    def _bundle_landed_keys(self, missing_keys, registry):
        """The post-landing existence check (the 10-01 checker per
        key): every currently-missing key whose task dir now carries
        all three split CSVs.

        Args:
            missing_keys (list[str]): the missing set from
                ``missing_datasets`` (computed before the stages ran).
            registry (dict): the official registry (already read).

        Returns:
            tuple: ``(landed, not_landed)`` — the landed keys and one
            diagnostic token per still-missing key naming its missing
            splits.
        """
        datasets_root = self._pipeline_dir / "datasets"
        landed: list[str] = []
        not_landed: list[str] = []
        for missing_key in missing_keys:
            entry = registry.get(missing_key)
            derived = (_group_and_task(entry)
                       if isinstance(entry, dict) else None)
            if derived is None:
                continue
            group, task = derived
            missing_splits = self._missing_splits(
                datasets_root / group / task)
            if missing_splits:
                not_landed.append(
                    missing_key + ":" + ",".join(missing_splits))
            else:
                landed.append(missing_key)
        return landed, not_landed

    # ===== The reconcile leg (D-09: automatic post-landing audit) =====

    def reconcile_dataset(self, key, run_id):
        """Reconcile one landed key through the real audit subprocess.

        The gauntlet audit-leg staging re-implemented for the
        official-key variant (10-RESEARCH Pattern 2): a CANDIDATE-ONLY
        temp registry dir holding exactly ``{key: entry}`` with the
        ``Dataset_path`` ABSOLUTIZED against the pipeline dir (the
        pathlib join replaces ``--datasets-root`` — that root is
        deliberately inert, gauntlet Pitfall 3), an inert temp
        datasets-root, ALL FOUR output flags at temp paths (the
        committed artifacts are unreachable, T-10-02-01), and the env
        pinned to ``os.environ`` plus exactly one override pointing
        ``CUSTOM_DIR_ENV`` at an EMPTY temp dir (operator isolation).
        The verdict comes from the PARSED temp ``n_audit.json``
        (``tasks.{key}``), never the exit code alone; the declared side
        is the official registry entry's ``Train``/``Dev``/``Test``
        ints (an absent declaration skips that split's comparison — the
        gauntlet rule).

        This method NEVER raises and never mutates queue state — every
        failure edge is absorbed into a ``failed`` outcome carrying the
        verbatim captured output.

        Args:
            key (str): the landed dataset registry key.
            run_id (str): the caller's run tag (future event wiring).

        Returns:
            ReconcileOutcome: the structured verdict.
        """
        try:
            registry = self._official_registry()
        except (OSError, json.JSONDecodeError,
                UnicodeDecodeError) as exc:
            return self._failed_reconcile("registry_unreadable",
                                          repr(exc))
        entry = registry.get(key)
        if not isinstance(entry, dict):
            return self._failed_reconcile("unknown_key", "key=" + key)
        staged_entry = dict(entry)
        raw_path = staged_entry.get("Dataset_path")
        if isinstance(raw_path, str) and raw_path:
            # ABSOLUTE form: the audit's resolve_dataset_dir joins
            # ``datasets_root / rel``; a pathlib join against an
            # absolute path REPLACES the root, so the inert temp
            # datasets-root can never redirect the read.
            staged_entry["Dataset_path"] = str(
                (self._pipeline_dir / raw_path).resolve())
        declared = {}
        for _split, field in _DECLARED_SPLIT_FIELDS:
            value = entry.get(field)
            if isinstance(value, int) and not isinstance(value, bool):
                declared[field] = value
        with tempfile.TemporaryDirectory(
                prefix="dnallmmark-reconcile-") as tmp:
            tmp_path = Path(tmp)
            registry_dir = tmp_path / "regdir"
            registry_dir.mkdir()
            audit_out = tmp_path / "audit-out"
            audit_out.mkdir()
            empty_overlay = tmp_path / "empty-overlay"
            empty_overlay.mkdir()
            datasets_root = tmp_path / "datasets-root"
            datasets_root.mkdir()
            (registry_dir / registry_loader.DATASETS_INFO_NAME).write_text(
                json.dumps({key: staged_entry}, indent=4,
                           ensure_ascii=False),
                encoding="utf-8")
            argv = [sys.executable,
                    str(self._repo_root / "script" / AUDIT_SCRIPT_NAME),
                    "--registry-dir", str(registry_dir),
                    "--datasets-root", str(datasets_root),
                    "--data-dir", str(audit_out),
                    "--subsets-out", str(audit_out / "eval_subsets.json"),
                    "--data-md", str(audit_out / "DATA.md")]
            env = dict(os.environ)
            env[CUSTOM_DIR_ENV] = str(empty_overlay)
            proc, launch_failure = self._invoke(
                argv, env, self._timeout_reconcile)
            if launch_failure is not None:
                return self._failed_reconcile(*launch_failure)
            raw = (proc.stdout or "") + (proc.stderr or "")
            if proc.returncode != 0:
                return self._failed_reconcile(
                    "exit_nonzero",
                    "exit_code=" + str(proc.returncode), raw=raw)
            audit = artifact_loader.load_json_artifact(
                audit_out / N_AUDIT_NAME)
            if audit is None:
                return self._failed_reconcile("n_audit_unreadable",
                                              raw=raw)
            record = None
            if isinstance(audit, dict):
                tasks = audit.get("tasks")
                if isinstance(tasks, dict):
                    maybe = tasks.get(key)
                    if isinstance(maybe, dict):
                        record = maybe
            if record is None:
                return self._failed_reconcile("key_absent_from_n_audit",
                                              raw=raw)
            return self._reconcile_verdict(record, declared, raw)

    def _reconcile_verdict(self, record, declared, raw):
        """Turn one parsed n_audit task record into a verdict.

        Pass criteria (the gauntlet ``_audit_verdict`` semantics
        verbatim — the audit subprocess owns every benchmark semantic):
        ``missing`` false; train/dev/test each rows > 0 (bool excluded);
        ``unified_eval_n`` > 0; and every DECLARED ``Train``/``Dev``/
        ``Test`` int equal to the measured rows per split. Every
        parsed-record violation is a ``mismatch`` (the artifact
        disproves the declared shape); infrastructure failures never
        reach this method. The non-ACGT census rides the record as
        data, never a failure condition.

        Args:
            record (dict): the parsed ``tasks.{key}`` record.
            declared (dict): the declared split counts keyed by the
                official field names (empty = nothing declared).
            raw (str): the verbatim subprocess output.

        Returns:
            ReconcileOutcome: pass or mismatch (never failed).
        """
        problems = []
        if record.get("missing") is not False:
            problems.append("missing=true")
        splits = record.get("splits")
        splits = splits if isinstance(splits, dict) else {}
        measured = {}
        for split in _AUDIT_SPLIT_ORDER:
            stats = splits.get(split)
            stats = stats if isinstance(stats, dict) else {}
            rows = stats.get("rows")
            if isinstance(rows, int) and not isinstance(rows, bool):
                measured[split] = rows
            if not isinstance(rows, int) or isinstance(rows, bool) \
                    or rows <= 0:
                problems.append(split + "_rows=" + repr(rows))
        unified = record.get("unified_eval_n")
        unified_eval_n = (unified
                          if isinstance(unified, int)
                          and not isinstance(unified, bool)
                          else None)
        if unified_eval_n is None or unified_eval_n <= 0:
            problems.append("unified_eval_n=" + repr(unified))
        for split, field in _DECLARED_SPLIT_FIELDS:
            declared_value = declared.get(field)
            if declared_value is None or split not in measured:
                continue    # absent declaration is legal; a split with
                            # no measured int already carries its own
                            # rows problem
            if declared_value != measured[split]:
                problems.append(
                    field + "_mismatch_declared=" + str(declared_value)
                    + "_measured=" + str(measured[split]))
        return ReconcileOutcome(
            ok=not problems,
            verdict=(VERDICT_PASS if not problems else VERDICT_MISMATCH),
            declared=dict(declared) if declared else None,
            measured=measured if measured else None,
            unified_eval_n=unified_eval_n,
            problems=tuple(problems), raw_output=raw)

    @staticmethod
    def _failed_reconcile(*problems, raw=""):
        """Build one failed reconcile outcome (the shared failure
        path — machine codes + verbatim output, never an exception)."""
        return ReconcileOutcome(
            ok=False, verdict=VERDICT_FAILED, declared=None,
            measured=None, unified_eval_n=None,
            problems=tuple(problems), raw_output=raw)

    @staticmethod
    def _reconcile_payload(outcome):
        """The persisted entry.reconcile dict for one outcome (the
        overlay source reconciled_rows reads; None on failed)."""
        return {
            "verdict": outcome.verdict,
            "declared": outcome.declared,
            "measured": outcome.measured,
            "unified_eval_n": outcome.unified_eval_n,
        }

    def _invoke(self, argv, env, timeout):
        """Run one completed-process leg through the injectable seam.

        Every launch failure is absorbed into a problems tuple — a
        timeout or a crash NEVER crosses the service boundary as an
        exception (the gauntlet ``_invoke`` discipline). The runner
        decodes with ``text=True, errors="replace"`` (WR-05, matching
        ``_pump``'s policy): the audit script emits CJK/emoji markers,
        and a non-UTF-8 ``LC_CTYPE`` host must decode them to
        replacement characters — never raise ``UnicodeDecodeError``
        inside ``subprocess.run`` and turn a healthy audit into a
        spurious failed verdict (the phase-8/9 GBK class).

        Args:
            argv (list): the LIST argv (never a shell string).
            env (dict): the explicit env (os.environ + one override).
            timeout (int): the leg's timeout seconds.

        Returns:
            tuple: ``(proc, None)`` with the CompletedProcess-shaped
            result, or ``(None, problems)`` when the runner timed out
            or crashed.
        """
        try:
            proc = self._runner(argv, capture_output=True, text=True,
                                errors="replace",
                                timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            return None, ("timeout",
                          "timeout_seconds=" + str(timeout))
        except Exception as exc:  # noqa: BLE001 — the service boundary
            # (the _invoke discipline): ANY launch failure yields a
            # failed outcome, never an exception crossing to the worker.
            return None, ("subprocess_error", repr(exc))
        return proc, None

    # ===== The explicit g re-audit (D-10/R-03: default outputs) =====

    def reaudit_baseline(self, run_id):
        """Refresh the committed audit baseline via the audit script's
        DEFAULT outputs (the maintainer's ``g`` action semantics).

        R-03: argv is EXACTLY ``[sys.executable, <absolute script
        path>]`` with NO output flags — the script writes its four repo
        artifacts (``dnallm-mark/data/n_audit.json``,
        ``n_audit.csv``, ``pipeline/eval_subsets.json``, ``DATA.md``)
        into the WORKTREE for maintainer review and commit; no
        temp+replace, no narrow write. The env is ``os.environ`` plus
        exactly one override pinning ``CUSTOM_DIR_ENV`` at an EMPTY
        temp dir (custom entries never leak into the refreshed
        baseline, T-10-02-03). Reachable ONLY through this explicit
        method — no automatic path (reconcile, presence) ever calls
        it; the committed baseline is otherwise read-only to this
        module.

        NEVER raises: nonzero exit, timeout, and launch errors are
        absorbed into a not-ok outcome carrying the verbatim output.

        Args:
            run_id (str): the caller's run tag (future event wiring).

        Returns:
            ReauditOutcome: the structured result.
        """
        with tempfile.TemporaryDirectory(
                prefix="dnallmmark-reaudit-") as tmp:
            argv = [sys.executable,
                    str(self._repo_root / "script" / AUDIT_SCRIPT_NAME)]
            env = dict(os.environ)
            env[CUSTOM_DIR_ENV] = str(Path(tmp))   # the empty overlay
            proc, launch_failure = self._invoke(
                argv, env, self._timeout_reaudit)
            if launch_failure is not None:
                return ReauditOutcome(
                    ok=False, details=launch_failure)
            raw = (proc.stdout or "") + (proc.stderr or "")
            if proc.returncode != 0:
                return ReauditOutcome(
                    ok=False,
                    details=("exit_nonzero",
                             "exit_code=" + str(proc.returncode)),
                    raw_output=raw)
            return ReauditOutcome(
                ok=True, details=("exit_code=0",), raw_output=raw)

    def _finish_cancelled(self, key, run_id, details):
        """The zenodo bundle lane's cancel exit (WR-01): failed with the
        shared ``cancelled_by_operator`` problem — the reap-loop
        contract mirrored for the handle-less stdlib-HTTP lane."""
        return self._finish(
            key, run_id, "failed", None, (PROBLEM_CANCELLED,),
            tuple(details))

    def _finish(self, key, run_id, state, percent, problems, details,
                stdout_text="", stderr_text="", argv=None,
                returncode=None, reconcile=None, reconcile_raw=""):
        """Persist one terminal transition + write the verbatim log +
        emit the event (the single exit path for every outcome).

        ``reconcile`` replaces the entry's reconcile field (None on
        every path that did not reach a reconcile verdict); the
        reconcile leg's verbatim output appends to the log under a
        ``[reconcile]`` section (D-03 drill-down completeness).

        WR-04: a failing persist NEVER raises here — the event still
        fires (the row refreshes, the driver survives) carrying a
        ``persist_error=<repr>`` problem so the row and drill-down
        surface the degradation; the in-memory entry keeps the terminal
        state and the file catches up on the next successful write or
        the restart downgrade.
        """
        log_rel = self._write_log(key, stdout_text, stderr_text, argv,
                                  returncode, reconcile_raw)
        kind = KIND_DATASET
        final_problems = list(problems)
        with self._lock:
            for entry in self._entries:
                if entry["key"] != key:
                    continue
                entry["state"] = state
                entry["finished_at"] = _now_iso()
                entry["last_percent"] = percent
                entry["log_path"] = log_rel
                entry["reconcile"] = reconcile
                kind = entry["kind"]
                persist_error = self._persist_locked()
                if persist_error is not None:
                    final_problems.append(
                        "persist_error=" + persist_error)
                entry["problems"] = final_problems
                break
        self._cancel_requested.discard(key)
        return QueueEvent(
            run_id=run_id, key=key, kind=kind, state=state,
            last_percent=percent, problems=tuple(final_problems),
            details=tuple(details), log_path=log_rel)

    def _write_log(self, key, stdout_text, stderr_text, argv,
                   returncode, reconcile_raw=""):
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
        if reconcile_raw:
            text += "\n[reconcile]\n" + reconcile_raw
        try:
            settings.atomic_write(
                self._state_path.parent / LOG_DIR_NAME / name, text)
        except OSError:
            return None
        return LOG_DIR_NAME + "/" + name

    # ===== Missing-set derivation (the D-13 input) =====

    def missing_datasets(self):
        """MissingInfo rows for official keys missing per the MERGED view.

        Computed over the official registry (direct file read, never
        the custom overlay — download targets are the official
        ModelScope mirrors) plus the D-11 merged presence view: the
        committed ``n_audit.json`` overlaid with this queue's
        reconcile-pass rows (``merge_presence`` over ``reconciled_rows``
        over this service's own state path — the exact substrate the
        selection screen consumes; CR-01). A landed-and-reconciled key
        therefore LEAVES the missing list the moment its queue entry
        turns done; the committed file itself stays read-only (the
        merge is pure). A landed-but-mismatched key never flips (only
        done entries reach the overlay). An absent/unreadable committed
        n_audit yields NO rows — the missing set is unknowable, not
        "everything".

        Returns:
            list[MissingInfo]: one frozen row per missing official key,
            in registry file order.
        """
        audit_tasks = registries.load_n_audit()
        if audit_tasks is None:
            # the missing set is unknowable without the committed view
            # (overlay keys read PRESENT and every other key UNKNOWN —
            # no row either way), so the early return is equivalent.
            return []
        try:
            registry = self._official_registry()
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return []
        merged = merge_presence(
            audit_tasks, reconciled_rows(self._state_path))
        rows = []
        for key, entry in registry.items():
            if not isinstance(entry, dict):
                continue
            presence = registries.presence_for(key, merged)
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

    def merged_audit_tasks(self):
        """The D-11 merged presence view through THIS service's state
        path (CR-01): ``merge_presence(registries.load_n_audit(),
        reconciled_rows(self._state_path))`` — the one substrate the
        selection screen's snapshot, the missing pane, and the presence
        summary all consume, served through the queue so an explicitly
        constructed ``state_path`` stays authoritative. The committed
        ``n_audit.json`` is never written by this path (the merge is
        pure; only the explicit ``g`` re-audit refreshes the baseline).

        Returns:
            dict: the merged tasks view — the committed mapping
            overlaid with ``{key: {"missing": False, "splits": ...}}``
            per reconcile-pass key (the committed view alone when
            nothing reconciled, the overlay alone when the committed
            file is absent).
        """
        return merge_presence(
            registries.load_n_audit(), reconciled_rows(self._state_path))

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
