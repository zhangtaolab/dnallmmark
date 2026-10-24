"""
record_tui_live_svg.py — the live TUI SVG recording driver.

pa6 lane (quick-261022-pa6, the default ``--mode pa6``): drives the REAL
operator console (``DnallmMarkTui``, zero injected services) through the
proven 2x2 dual-GPU journey — boot env check -> slot-4 picker marks ->
m-flip dataset marks -> params (seeds 42, 1 epoch, workers 2, GPUs 0,1,
fresh output root) -> live preview line -> [p] dispatch argv preview ->
the Y/N gate -> the real dispatch launch -> the monitor through
completion — exporting every stage as a design-grid (120x40) SVG
screenshot plus an honest operation record (RECORD.md + evidence.json)
generated from the run's own meta.

full lane (quick-261022-tah, ``--mode full``): the production-scale
FungiHelixSeek journey — slot-2 model download (cursor on the model row,
``d`` -> the real KIND_MODEL queue lane) -> slot-3 enqueue-all (``a`` ->
every missing downloadable dataset) -> interval captures of the download
queue until it settles -> queue detail drill-down -> slot-4 wizard
(FungiHelixSeek + EVERY present dataset, seeds typed 42,43,44, workers 2,
GPUs 0,1, fresh root, epochs NEVER touched — the YAML default governs and
the argv preview asserts ``--num_train_epochs`` ABSENT; 261023-abu
``--batch-text N``: a typed positive integer is typed into the batch
input and the argv preview REQUIRES ``--batch_size N`` — default "" never
touches the batch input, the epochs-today discipline with the ABSENT
assertion mirrored; Phase 19 (19-03) ``--param NAME=VALUE`` (REPEATABLE,
the generalized --batch-text channel): each pair is typed/picked on the
slot-4 advanced section — Input-family kinds typed into
``#cfg-input-<dasherized>``, enum/bool kinds picked through the real
ChoiceModal RadioSet journey — and the argv preview asserts the PAIR:
every typed flag PRESENT with its serialized value, every UNTOUCHED
``ADVANCED_TRAIN_FLAGS`` flag ABSENT; names/values validate against the
frozen table at parse, and the channel is full-mode-only (the
--batch-text lane discipline)) -> the Y/N gate ->
``y`` -> the real dual-GPU dispatch -> a multi-day monitor watch (interval
captures + incremental evidence heartbeat + stall detector) -> automatic
REPORT.md + download_ledger.json generation from the run's own artifacts.
The full-mode defaults carry NO hard timeout (``--timeout 0`` — the stall
detector governs) and the sweep is NEVER killed on any path.

Contract:

- ANCHOR AUTHORITY: every asserted literal derives from ``tui/strings.py``
  constants resolved at runtime (e.g. ``S.CFG_PREVIEW_LINE``,
  ``S.LNC_GATE_CONFIRM``) or from language-neutral DATA (registry keys,
  counts, paths, the GPU tuple "0,1") — never text copied from this file's
  history. After any UI copy change, the anchors re-derive from
  ``tui/strings.py`` automatically. This driver NEVER edits ``tui/``
  source; it drives the real app from outside.
- PILOT LANE: the journey runs through ``App.run_test(size=(120, 40))`` +
  ``App.export_screenshot()`` (the tests/tui/test_snapshots.py fallback
  lane idiom — probe-verified byte-deterministic). NOT the pty/asciinema
  GIF lane (that is scripts/demo/record_tui_demo.py, a different tool).
- FRESH STATE: each recording sets a FRESH ``DNALLMMARK_TUI_STATE_DIR``
  under ``--state-base`` (default /root/autodl-tmp — the disk-capacity
  rule: no state under / or /root) BEFORE constructing the app, so the
  launcher tee, run_config.json, monitor_roots, the download queue state
  file, and the queue logs land there. The REAL config root stays live
  (directories.json wiring + customs render);
  ``DNALLMMARK_TUI_CONFIG_DIR`` is never set. The temp state dir is KEPT
  on every path (it holds the tee log — evidence) and recorded in the
  meta. The mkdtemp prefix is mode-pinned (``tui-live-pa6-`` /
  ``tui-live-fhs-``).
- MODES: ``--dry-run`` prints the journey timeline + resolved targets with
  zero app spawn and zero preflight side effects; ``--no-launch`` is the
  full rehearsal (real app, real registries, drive to the gate, capture
  the stages, press ``n`` at the confirm — zero GPU work, and in full mode
  zero network enqueue: the slot-2 leg only LOCATES the row, the slot-3
  leg only renders the view); the default is the LIVE mode (real launch +
  completion poll). The dnallm-import and GPU-idle preflight legs run
  only in live mode.
- FULL-MODE EVIDENCE: evidence.json is written INCREMENTALLY (atomic
  write after every stage and every interval, heartbeat
  ``{at, phase, interval_index}``) so progress is checkable from outside
  at any moment of the multi-day run; download_ledger.json lands at
  download settle; REPORT.md is auto-generated on completion (and as a
  best-effort draft on every failure path) from the run's own artifacts
  ONLY — no fabricated success, ever.
- DISPLAY-ONLY /proc evidence: completion polling reuses the repo's own
  ``tui.services.sweep_launcher.probe_cli_sweeps`` (read-only cmdline
  reads of this host's process table). The driver NEVER signals any
  process: on timeout, stall, or failure the sweep SURVIVES detached in
  its own session and the record documents how to reach it. No fabricated
  success: a failed, stalled, or timed-out run exports the failure-state
  capture, records exactly what was observed, and exits nonzero.

Usage:
    python scripts/live/record_tui_live_svg.py --mode pa6 --dry-run
    python scripts/live/record_tui_live_svg.py --mode pa6 --no-launch
    python scripts/live/record_tui_live_svg.py --mode pa6 \
        [--interval 180] [--timeout 5400]
    python scripts/live/record_tui_live_svg.py --mode full --dry-run
    python scripts/live/record_tui_live_svg.py --mode full --no-launch
    python scripts/live/record_tui_live_svg.py --mode full \
        [--dl-interval 600] [--interval 1800] [--stall-hours 6] \
        [--timeout 0]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# The tui/__main__.py bootstrap idiom: the repo root (for package-qualified
# tui imports) and REPO_ROOT/pipeline (for the top-level pipeline seam
# modules) both land on sys.path BEFORE the tui imports below.
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "pipeline"))

import directories_config  # top-level module (pipeline/ sys.path root)
import run_sweep  # top-level module (pipeline/ sys.path root)
from rich.text import Text
from textual.containers import Vertical
from textual.pilot import Pilot
from textual.widgets import (
    DataTable,
    Input,
    Label,
    RadioButton,
    RadioSet,
    Static,
)

from tui import strings as S
from tui.app import DnallmMarkTui
from tui.screens.data_manager import DataManagerScreen, QueueDetailModal
from tui.screens.env_check import EnvCheckScreen
from tui.screens.monitor import MonitorScreen
from tui.screens.run_config import (
    ChoiceModal,
    ChoiceRow,
    EnvBlockModal,
    PickerList,
    PreviewModal,
    ProblemsModal,
    RunConfigScreen,
    _GateConfirmModal,
)
from tui.screens.selection import SelectionScreen
from tui.services import download_queue, registries, sweep_launcher

# ===== The locked journey combo (presence VERIFIED in preflight) =====

MODELS = ("plant-dnabert-6mer", "plant-dnamamba-6mer")
TASKS = ("GUE__emp_H3", "iDNA_ABF_datasets__5mC")
SEEDS_TEXT = "42"
EPOCHS_TEXT = "1"
WORKERS_TEXT = "2"
GPUS_TEXT = "0,1"

# ===== The full-mode combo (quick-261022-tah) =====

MODE_PA6 = "pa6"
MODE_FULL = "full"

#: The single production model of the full journey (263M, modelscope
#: zhangtaolab/FungiHelixSeek, compat-adapted — preflight verifies the
#: card + the compat slot + the on-disk absence).
FULL_MODEL = "FungiHelixSeek"

#: The seeds typed into the wizard as the literal text "42,43,44".
FULL_SEEDS = ("42", "43", "44")
FULL_SEEDS_TEXT = "42,43,44"
FULL_WORKERS_TEXT = "2"
FULL_GPUS_TEXT = "0,1"

#: The pinned state-dir mkdtemp prefix (the Task-2 gate globs this).
FULL_STATE_PREFIX = "tui-live-fhs-"

#: Per-mode CLI default table (explicit flags always win).
_MODE_DEFAULTS: dict[str, dict[str, object]] = {
    MODE_PA6: {
        "root": "pipeline/finetuned-tui-pa6",
        "svg_dir": "docs/live/svg",
        "record": "docs/live/RECORD.md",
        "evidence": "docs/live/evidence.json",
        "interval": 180.0,
        "timeout": 5400.0,
    },
    MODE_FULL: {
        "root": "pipeline/finetuned-fhs-full",
        "svg_dir": "docs/live/fhs/svg",
        "record": "docs/live/fhs/RECORD.md",
        "evidence": "docs/live/fhs/evidence.json",
        "report": "docs/live/fhs/REPORT.md",
        "ledger": "docs/live/fhs/download_ledger.json",
        "dl_interval": 600.0,
        "interval": 1800.0,
        "timeout": 0.0,
    },
}

#: The full-mode preflight's data-disk floor (the download + sweep need
#: headroom for the model snapshot, up to 44 datasets, and days of run
#: artifacts; 1964G free at plan time).
_MIN_FREE_GIB = 200

#: The pinned design grid every capture exports at (the golden lane size).
GRID = (120, 40)

#: 2 models x 2 tasks x 1 seed — the completion contract (pa6).
EXPECTED_CELLS = 4

#: dispatch_state.json statuses that end the orchestrator's run (the rest
#: of the vocabulary is transient). Language-neutral machine data.
_DISPATCH_TERMINAL_OK = "completed"
_DISPATCH_TERMINAL_BAD = {"failed", "interrupted"}

#: The queue's active (non-terminal) states — the download-settle
#: predicate's machine vocabulary (D-02 five states).
_QUEUE_ACTIVE = ("pending", "downloading")

#: Poll cadence for every bounded wait (seconds).
_POLL_STEP = 0.5

MODELS_INFO = REPO_ROOT / "pipeline" / "models_info.json"
DATASETS_INFO = REPO_ROOT / "pipeline" / "datasets_info.json"

#: The YAML default config the epochs-less launch defers to (the report
#: states the effective epoch count from HERE, never a hardcoded literal).
FINETUNE_CONFIG_YAML = REPO_ROOT / "pipeline" / "finetune_config.yaml"


class DriverError(RuntimeError):
    """A journey stage failed: an anchor timed out, the gate refused, or
    the sweep ended without the expected artifacts. The recording must be
    re-run; the record still lands honestly."""


class GateRefusedError(DriverError):
    """The gate answered the enter with a refusal modal (ProblemsModal or
    EnvBlockModal) instead of the Y/N confirm — y is never pressed."""


class PreflightError(RuntimeError):
    """A preflight leg failed; nothing was spawned or written."""


# =====================================================================
# Small shared helpers
# =====================================================================


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _plain(content: object) -> str:
    """Plain text of a Static/Label content (cells may carry rich Text)."""
    if isinstance(content, Text):
        return content.plain
    return str(content)


def _label_text(screen, selector: str) -> str:
    return _plain(screen.query_one(selector, Static).content)


def _atomic_write(path: Path, text: str) -> None:
    """Write through a temp file + os.replace (the settings.atomic_write
    discipline) so an outside reader never sees a torn file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _query_gpu(args: list[str]) -> str:
    """Run one nvidia-smi query; stdout verbatim (empty on nonzero)."""
    result = subprocess.run(
        ["nvidia-smi", *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _gpu_snapshot() -> dict:
    """One watch-loop evidence snapshot: per-GPU utilization/memory/
    temperature plus the compute-app pid list (read-only)."""
    return {
        "at": _now_iso(),
        "query": _query_gpu([
            "--query-gpu=index,utilization.gpu,memory.used,temperature.gpu",
            "--format=csv,noheader"]),
        "compute_apps": _query_gpu(
            ["--query-compute-apps=pid", "--format=csv,noheader"]),
    }


def _count_seed_artifacts(root: Path, name: str,
                          seed: str | Iterable[str]) -> int:
    """Count ``{root}/**/seed_{seed}/{name}`` files (layout-neutral
    walk). ``seed`` generalizes to a seed SET (full mode counts across
    42/43/44); a bare string keeps the pa6 call shape byte-identical."""
    seeds = (seed,) if isinstance(seed, str) else tuple(seed)
    markers = {f"seed_{one}" for one in seeds}
    return sum(1 for path in root.rglob(name)
               if path.parent.name in markers)


def _count_per_seed(root: Path, name: str,
                    seeds: tuple[str, ...]) -> dict[str, int]:
    """Per-seed artifact counts (the full-mode completion contract is
    per-seed: len(present) under EVERY seed)."""
    return {seed: _count_seed_artifacts(root, name, (seed,))
            for seed in seeds}


# ===== The download queue's persisted state (read-only derivations) =====


def _queue_state_path(state_dir: Path) -> Path:
    """The queue state file under the recording's fresh state dir (the
    settings.state_dir() root the real service writes)."""
    return state_dir / download_queue.QUEUE_FILE_NAME


def _read_queue_entries(state_dir: Path) -> list[dict]:
    """Tolerant read-only read of the persisted queue entries (empty on
    absent/corrupt — the artifact_loader None-sentinel discipline)."""
    try:
        doc = json.loads(
            _queue_state_path(state_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(doc, dict):
        return []
    entries = doc.get("entries")
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict)]


def _queue_digest(entries: list[dict]) -> dict:
    """Per-state x per-kind entry counts (the interval evidence digest)."""
    digest: dict[str, int] = {}
    for entry in entries:
        state = str(entry.get("state", "?"))
        kind = str(entry.get("kind", "?"))
        digest[f"{kind}:{state}"] = digest.get(f"{kind}:{state}", 0) + 1
    return digest


def _entry(entries: list[dict], key: str) -> dict | None:
    return next((e for e in entries if e.get("key") == key), None)


def _newest_log_stat(logs_dir: Path) -> tuple[str, int]:
    """(name, size) of the newest queue log under the state dir's logs/
    (("", 0) when none) — the download-liveness signal."""
    try:
        newest = max(
            logs_dir.glob("*.log"),
            key=lambda path: path.stat().st_mtime, default=None)
    except OSError:
        return ("", 0)
    if newest is None:
        return ("", 0)
    try:
        return (newest.name, newest.stat().st_size)
    except OSError:
        return (newest.name, 0)


def _official_dataset_keys() -> list[str]:
    """The official dataset registry keys in file order (pure read)."""
    return [entry.get("key") for entry in registries.load_dataset_entries()
            if isinstance(entry.get("key"), str)]


def _derive_present(state_dir: Path) -> tuple[list[str], list[str]]:
    """The present set through the SAME chain the picker renders —
    ``merge_presence(load_n_audit(), reconciled_rows(state file))`` +
    ``registries.presence_for`` (pure reads; the committed audit is
    static during the run, so the before-view is the same chain WITHOUT
    the reconcile overlay). Returns (present_after, present_before)."""
    committed = registries.load_n_audit()
    keys = _official_dataset_keys()
    before = [key for key in keys
              if registries.presence_for(key, committed).status
              == registries.PRESENCE_PRESENT]
    merged = download_queue.merge_presence(
        committed,
        download_queue.reconciled_rows(_queue_state_path(state_dir)))
    after = [key for key in keys
             if registries.presence_for(key, merged).status
             == registries.PRESENCE_PRESENT]
    return after, before


class _StallWatch:
    """The shared stall detector: a caller-supplied ACTIVITY SIGNATURE
    (file mtimes/sizes/counts) unchanged for ``hours`` means stalled."""

    def __init__(self, hours: float) -> None:
        self._hours = max(0.0, hours)
        self._signature: object = None
        self._since: float | None = None

    def observe(self, signature: object) -> bool:
        """Record one observation; True iff the signature has now been
        unchanged for at least the configured hours."""
        if signature == self._signature:
            if self._since is None:
                self._since = time.monotonic()
                return False
            return (time.monotonic() - self._since) >= self._hours * 3600.0
        self._signature = signature
        self._since = None
        return False


# =====================================================================
# Preflight (halts with a named reason + exit 2)
# =====================================================================


def _dir_base(value: str | None, default: Path) -> Path:
    """Resolve a directories.json root the consumers' way: absolute values
    pass through, relative values resolve against REPO_ROOT, absent falls
    back to the built-in default."""
    if not value:
        return default
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return (REPO_ROOT / candidate).resolve()


def _probe_writable(dirs: tuple[Path, ...], files: tuple[Path, ...],
                    label: str) -> None:
    """The writable-path leg: probe one file inside every dir target and
    one temp sibling beside every file target (removed after)."""
    probes: list[Path] = []
    for directory in dirs:
        probes.append(directory / ".tui-live-write-probe")
    for path in files:
        probes.append(path.parent / ".tui-live-write-probe")
    try:
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
        for path in files:
            path.parent.mkdir(parents=True, exist_ok=True)
        for probe in probes:
            probe.write_text("", encoding="utf-8")
            probe.unlink()
    except OSError as exc:
        raise PreflightError(
            f"output path not writable ({label}): {exc}") from exc


def _free_gib(path: Path) -> int:
    """Free space (GiB) on the mount holding ``path`` (df -BG)."""
    result = subprocess.run(
        ["df", "-BG", str(path)], capture_output=True, text=True,
        check=False)
    if result.returncode != 0:
        return -1
    match = re.search(
        r"\n\S+\s+\S+\s+\S+\s+(\d+)G\s+", result.stdout)
    return int(match.group(1)) if match else -1


def preflight(args: argparse.Namespace) -> dict:
    """Verify every precondition the journey assumes.

    The dnallm-import and GPU-idle legs run only in live mode (the plan's
    skip rule); the offline flag, registry, fresh-root, and writable-path
    legs run in every spawned mode. The registry leg branches by mode:
    pa6 pins the 2x2 combo's on-disk presence; full verifies the
    FungiHelixSeek card + compat slot, the modelscope CLI, the dataset
    registry, the data-disk headroom, and RECORDS the model's on-disk
    presence (missing expected; a present model skips the slot-2 enqueue
    leg honestly). Returns the resolved targets dict (recorded in the
    meta + printed by --dry-run consumers).
    """
    live = not args.no_launch
    attach = bool(getattr(args, "attach_root", None))
    targets: dict = {"root_arg": args.root}

    if os.environ.get("HF_HUB_OFFLINE") != "1":
        raise PreflightError(
            "HF_HUB_OFFLINE != '1' — the offline discipline is asserted "
            "before anything spawns (docs/multi-gpu.md runbook: export "
            "HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1)")

    if attach:
        _preflight_attach_legs(args, targets)
        svg_dir = Path(args.svg_dir)
        _probe_writable((svg_dir,), (Path(args.evidence),
                                      Path(args.report)), "attach")
        return targets

    if live:
        try:
            import dnallm  # noqa: F401 — import IS the check
        except ImportError as exc:
            raise PreflightError(
                f"import dnallm failed ({exc}) — memory rule: after "
                "uv sync, reinstall dnallm editable from the local dev "
                "clone (../DNALLM): uv pip install -e ../DNALLM") from exc

    try:
        models_info = json.loads(MODELS_INFO.read_text(encoding="utf-8"))
        datasets_info = json.loads(
            DATASETS_INFO.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PreflightError(
            f"official registries unreadable: {exc}") from exc
    if not isinstance(models_info, dict) or not isinstance(datasets_info,
                                                            dict):
        raise PreflightError("official registries are not object-shaped")

    dirs = directories_config.load_directories_tolerant()
    model_base = _dir_base(dirs.get("model_root"), REPO_ROOT / "pipeline")
    dataset_base = _dir_base(
        dirs.get("dataset_root"), REPO_ROOT / "pipeline")

    if args.mode == MODE_FULL:
        _preflight_full_legs(args, targets, models_info)
    else:
        _preflight_pa6_combo(
            targets, models_info, datasets_info, model_base, dataset_base)

    if live:
        count = _query_gpu(["--query-gpu=index", "--format=csv,noheader"])
        indices = [line.strip() for line in count.splitlines() if line.strip()]
        if len(indices) != 2:
            raise PreflightError(
                f"nvidia-smi reports {len(indices)} GPUs (expected exactly "
                f"2): {count!r}")
        apps = _query_gpu(
            ["--query-compute-apps=pid", "--format=csv,noheader"])
        if apps:
            raise PreflightError(
                "GPUs are NOT idle — compute apps present (refusing to "
                f"share): {apps!r}")
        targets["gpu_names"] = _query_gpu(
            ["--query-gpu=name", "--format=csv,noheader"])

    root_resolved = (REPO_ROOT / Path(args.root)).resolve()
    if root_resolved.exists():
        raise PreflightError(
            f"output root {root_resolved} already exists — fresh-root "
            "discipline (a reused root's trainer_state markers would skip "
            "cells and fake success)")
    targets["root_resolved"] = str(root_resolved)

    svg_dir = Path(args.svg_dir)
    file_targets = [Path(args.evidence)]
    if args.mode == MODE_FULL:
        file_targets.extend([Path(args.report), Path(args.ledger)])
    else:
        file_targets.append(Path(args.record))
    _probe_writable((svg_dir,), tuple(file_targets), args.mode)
    return targets


def _preflight_attach_legs(args: argparse.Namespace,
                           targets: dict) -> None:
    """The --attach-root preflight: the root EXISTS and its dispatch
    orchestrator is LIVE (the sweep was already launched by another
    driver — this mode only WATCHES: monitor card + interval captures +
    auto-report; it never spawns anything, so the dnallm/GPU-idle/
    fresh-root legs do not apply)."""
    root = (REPO_ROOT / Path(args.attach_root)).resolve()
    if not root.is_dir():
        raise PreflightError(
            f"attach root {root} does not exist — nothing to watch")
    state_path = root / "dispatch_state.json"
    if not state_path.is_file():
        raise PreflightError(
            f"no dispatch_state.json under {root} — the sweep never "
            "launched (or has not created its state yet)")
    status = _dispatch_status(state_path)
    if status in _DISPATCH_TERMINAL_BAD or status == _DISPATCH_TERMINAL_OK:
        raise PreflightError(
            f"the dispatch orchestrator under {root} is already terminal "
            f"({status!r}) — nothing left to watch")
    targets["root_resolved"] = str(root)
    targets["attach"] = True


def _preflight_pa6_combo(targets: dict, models_info: dict,
                         datasets_info: dict, model_base: Path,
                         dataset_base: Path) -> None:
    """The pa6 registry leg: the 2x2 combo's on-disk presence through the
    real consumers' chain (card Model_path/Dataset_path joined on the
    directories.json-seeded root), naming EVERY missing key at once."""

    def _card_path(info: dict, key: str, field: str) -> str | None:
        card = info.get(key)
        if not isinstance(card, dict):
            return None
        value = card.get(field)
        return value if isinstance(value, str) and value else None

    missing: list[str] = []
    resolved_cards: dict[str, str] = {}
    for key in MODELS:
        rel = _card_path(models_info, key, "Model_path")
        if rel is None:
            missing.append(f"model {key} (no Model_path card)")
            continue
        resolved = model_base / rel
        resolved_cards[key] = str(resolved)
        if not resolved.is_dir():
            missing.append(f"model {key} -> {resolved}")
    for key in TASKS:
        rel = _card_path(datasets_info, key, "Dataset_path")
        if rel is None:
            missing.append(f"dataset {key} (no Dataset_path card)")
            continue
        resolved = dataset_base / rel
        resolved_cards[key] = str(resolved)
        if not resolved.is_dir():
            missing.append(f"dataset {key} -> {resolved}")
    if missing:
        raise PreflightError(
            "journey targets missing on disk (base roots: models="
            f"{model_base}, datasets={dataset_base}): " + "; ".join(missing))
    targets["cards"] = resolved_cards


def _preflight_full_legs(args: argparse.Namespace, targets: dict,
                         models_info: dict) -> None:
    """The full-mode registry legs: modelscope CLI, the FungiHelixSeek
    channel through the queue's OWN resolver (the one authority the
    model lane uses — card Model_path + compat verdict + modelscope
    repo id in one spec), the data-disk headroom, and the model's
    on-disk presence (RECORDED, never asserted — a present model
    honestly skips the slot-2 enqueue leg)."""
    cli = download_queue.resolve_modelscope_cli()
    if cli is None:
        raise PreflightError(
            "modelscope CLI unresolvable — both download lanes gate on it "
            "(it doubles as the modelscope-package proxy for the model "
            "child)")
    targets["modelscope_cli"] = str(cli)

    if not isinstance(models_info.get(FULL_MODEL), dict):
        raise PreflightError(
            f"{FULL_MODEL} absent from pipeline/models_info.json")
    service = download_queue.DownloadQueueService()
    spec = service.resolve_model_channel(FULL_MODEL)
    if spec is None:
        raise PreflightError(
            f"{FULL_MODEL} is not an official registry key (the model "
            "lane only downloads officials)")
    if spec.reason_code is not None:
        raise PreflightError(
            f"the model lane refuses {FULL_MODEL}: {spec.reason_code} "
            "(the queue's own resolve_model_channel verdict)")
    targets["model_repo_id"] = spec.repo_id
    targets["model_landing"] = str(spec.landing)
    targets["model_on_disk"] = bool(
        spec.landing is not None and spec.landing.is_dir())

    state_base = Path(args.state_base)
    state_base.mkdir(parents=True, exist_ok=True)
    free = _free_gib(state_base)
    if free < _MIN_FREE_GIB:
        raise PreflightError(
            f"only {free} GiB free on the mount holding {state_base} "
            f"(need >= {_MIN_FREE_GIB} GiB for the model + datasets + "
            "days of run artifacts)")


# =====================================================================
# The run context (meta bookkeeping shared by every stage)
# =====================================================================


class RunContext:
    """One recording's bookkeeping: args, resolved targets, the evidence
    meta, and the monotonic stage clock. Full mode flushes evidence.json
    INCREMENTALLY (after every stage + heartbeat) — the external progress
    surface of the multi-day run."""

    def __init__(self, args: argparse.Namespace, targets: dict,
                 state_dir: Path) -> None:
        self.args = args
        self.targets = targets
        self.state_dir = state_dir
        self.svg_dir = Path(args.svg_dir)
        self.root = Path(targets["root_resolved"])
        self.t0 = time.monotonic()
        self.rehearsal = bool(args.no_launch)
        self.full = args.mode == MODE_FULL
        self.attach = bool(getattr(args, "attach_root", None))
        self.seeds: tuple[str, ...] = (
            FULL_SEEDS if self.full else (SEEDS_TEXT,))
        if self.full:
            if self.attach:
                mode_name = "full"
            elif self.rehearsal:
                mode_name = "full-rehearsal"
            else:
                mode_name = "full"
        self.meta: dict = {
            "mode": mode_name,
            "driver_mode": args.mode,
            "started_at": _now_iso(),
            "host": platform.node(),
            "root_arg": args.root,
            "root_resolved": str(self.root),
            "state_dir": str(state_dir),
            "grid": list(GRID),
            "models": [FULL_MODEL] if self.full else list(MODELS),
            "tasks": None if self.full else list(TASKS),
            "seeds": FULL_SEEDS_TEXT if self.full else SEEDS_TEXT,
            "seeds_list": list(self.seeds),
            "epochs": None if self.full else EPOCHS_TEXT,
            "epochs_source": "yaml_default" if self.full else "typed",
            "workers": FULL_WORKERS_TEXT if self.full else WORKERS_TEXT,
            "gpus": FULL_GPUS_TEXT if self.full else GPUS_TEXT,
            "cards": targets.get("cards", {}),
            "gpu_names": targets.get("gpu_names", ""),
            "model": FULL_MODEL if self.full else None,
            "model_on_disk": targets.get("model_on_disk"),
            "model_repo_id": targets.get("model_repo_id"),
            "modelscope_cli": targets.get("modelscope_cli"),
            "stages": {},
            "nvidia_snapshots": [],
            "monitor_captures": [],
            "dl_captures": [],
            "queue_digests": [],
            "download": {},
            "present_set": None,
            "expected_cells": None,
            "heartbeat": {"at": _now_iso(), "phase": "start",
                          "interval_index": 0},
            "argv_line": None,
            "argv": None,
            "tee_path": None,
            "dispatch_state": None,
            "completion": None,
            "notes": [],
            "rehearsal": self.rehearsal,
            "report_written": False,
            "exit_code": None,
            "failure": None,
        }
        if self.attach:
            self._adopt_journey_evidence()

    def _adopt_journey_evidence(self) -> None:
        """Attach mode: CONTINUE the journey driver's evidence.json (the
        one sidecar contract) — adopt its run-history fields so nothing
        is overwritten, and record the journey driver's honest exit as a
        note. A missing/corrupt prior file starts fresh (the note says
        so)."""
        prior = _read_json(Path(self.args.evidence))
        if not prior:
            self.note(
                "attach watch: no prior evidence.json found — starting a "
                "fresh sidecar (the journey driver's evidence is absent)")
            return
        for field in (
                "started_at", "host", "gpu_names", "env_verdict",
                "stages", "notes", "nvidia_snapshots", "monitor_captures",
                "dl_captures", "queue_digests", "download", "argv_line",
                "argv", "tee_path", "epochs_input_value"):
            if field in prior:
                self.meta[field] = prior[field]
        if prior.get("failure"):
            self.meta["notes"].append(
                f"journey driver exit {prior.get('exit_code')}: "
                f"{prior['failure']}")
        self.meta["watch_driver"] = "attach"
        self.meta["watch_attached_at"] = _now_iso()

    def flush_evidence(self) -> None:
        """Atomic incremental write of the evidence sidecar (full mode's
        external progress surface; pa6 keeps its end-of-run single write)."""
        if not self.full:
            return
        _atomic_write(
            Path(self.args.evidence),
            json.dumps(self.meta, indent=2, ensure_ascii=False))

    def heartbeat(self, phase: str, interval_index: int) -> None:
        """Record one liveness beat + flush (the multi-day watch's outside
        checkable progress signal)."""
        self.meta["heartbeat"] = {
            "at": _now_iso(),
            "phase": phase,
            "interval_index": interval_index,
        }
        self.flush_evidence()

    def stage(self, name: str) -> None:
        self.meta["stages"][name] = {
            "at": _now_iso(),
            "elapsed_s": round(time.monotonic() - self.t0, 1)}
        print(f"[{time.monotonic() - self.t0:8.1f}s] stage: {name}",
              flush=True)
        self.flush_evidence()

    def note(self, text: str) -> None:
        self.meta["notes"].append(text)
        print(f"[{time.monotonic() - self.t0:8.1f}s] note: {text}",
              flush=True)
        self.flush_evidence()

    async def export(self, pilot: Pilot, app: DnallmMarkTui,
                     name: str) -> Path:
        """Disable cursor blink app-wide (the D-11 stability rule), settle,
        export the SVG at the design grid, record the stage."""
        for widget in app.query(Input):
            widget.cursor_blink = False
        await pilot.pause()
        svg = app.export_screenshot()
        path = self.svg_dir / f"{name}.svg"
        path.write_text(svg, encoding="utf-8")
        self.stage(name)
        return path


async def settle(app: DnallmMarkTui, pilot: Pilot, rounds: int = 3) -> None:
    """The house settle: sequential worker->handler chains."""
    for _ in range(rounds):
        await app.workers.wait_for_complete()
        await pilot.pause()


async def wait_until(pilot: Pilot, predicate: Callable[[], bool],
                     timeout: float, label: str) -> None:
    """Bounded poll loop (0.5 s cadence) that halts honestly on expiry."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            ok = predicate()
        except Exception:  # noqa: BLE001 — a not-yet-ready tree reads False
            ok = False
        if ok:
            return
        if time.monotonic() >= deadline:
            raise DriverError(
                f"stage '{label}' not reached within {timeout:.0f}s")
        await asyncio.sleep(_POLL_STEP)
        await pilot.pause()


def _screen_labels_text(app: DnallmMarkTui) -> str:
    """The joined plain text of the current screen's Labels (the monitor
    card wait's language-neutral substrate)."""
    parts: list[str] = []
    for widget in app.screen.query(Label):
        try:
            parts.append(_plain(widget.content))
        except Exception:  # noqa: BLE001, S110 — not-yet-mounted rows skip
            pass
    return "\n".join(parts)


# =====================================================================
# The journey stages (shared: boot env verdict + filter/type idioms)
# =====================================================================


async def _wait_env_settled(pilot: Pilot, app: DnallmMarkTui,
                            ctx: RunContext) -> str:
    """Wait for the boot env screen's verdict (the kernels are done once
    any verdict/route line renders), returning the rendered text."""
    pass_anchor = S.ENV_VERDICT_PASS
    fail_anchor = S.ENV_VERDICT_CRITICAL_FAIL.format(
        kernel_names="__x__").split("__x__")[0]
    route_anchor = S.ENV_ROUTE_MISSING_DATASETS.format(
        n="__x__").split("__x__")[0]

    def _verdict_text() -> str:
        screen = app.screen
        if not isinstance(screen, EnvCheckScreen):
            return ""
        box = screen.query_one("#env-verdict", Vertical)
        parts = [_plain(getattr(child, "content", ""))
                 for child in box.children]
        return "\n".join(parts)

    await wait_until(pilot, lambda: _verdict_text() != "",
                     300.0, "boot env check verdict")
    text = _verdict_text()
    if not any(anchor in text
               for anchor in (pass_anchor, fail_anchor, route_anchor)):
        # The kernels finished and rendered SOMETHING the anchor family
        # does not cover — record it honestly and keep going; the gate's
        # own env preflight is the authoritative block.
        print(f"[env] verdict text outside anchor family: {text!r}",
              flush=True)
    return text


async def _filter_mark(pilot: Pilot, screen: RunConfigScreen,
                       key: str) -> None:
    """The real filter idiom: '/' focuses #cfg-filter, the key text
    narrows the picker, tab moves to the picker, the cursor walks onto
    the exact target row (a bare-substring filter legitimately matches
    prefix-sharing siblings — e.g. the GUE__emp_H3K* family), space marks
    it, escape clears the filter (marks live in shared state)."""
    await pilot.press("slash")
    await pilot.pause()
    for char in key:
        await pilot.press(char)
    await pilot.pause()
    picker = screen.query_one("#cfg-picker", PickerList)
    rows = len(picker.options)
    if rows < 1:
        raise DriverError(
            f"filter {key!r} matched no picker rows")
    await pilot.press("tab")
    await pilot.pause()
    for _ in range(rows):
        if picker.key_at(picker.highlighted) == key:
            break
        await pilot.press("down")
        await pilot.pause()
    if picker.key_at(picker.highlighted) != key:
        raise DriverError(
            f"filter {key!r} matched {rows} rows and none of them is the "
            "target key")
    await pilot.press("space")
    await pilot.pause()
    await pilot.press("escape")
    await pilot.pause()


async def _type_into(pilot: Pilot, screen: RunConfigScreen,
                     input_id: str, text: str) -> None:
    """Focus an input by query, clear it (end + len+3 backspaces — extra
    backspace on an empty input is a no-op; never assume the prefill),
    then type the new value with real key presses."""
    widget = screen.query_one(input_id, Input)
    widget.focus()
    await pilot.pause()
    current = widget.value
    await pilot.press("end")
    await pilot.pause()
    for _ in range(len(current) + 3):
        await pilot.press("backspace")
    await pilot.pause()
    if widget.value != "":
        raise DriverError(
            f"{input_id} did not clear (still {widget.value!r} after "
            f"{len(current) + 3} backspaces)")
    for char in text:
        await pilot.press(char)
    await pilot.pause()
    if widget.value != text:
        raise DriverError(
            f"{input_id} holds {widget.value!r} (expected {text!r})")


# ===== Phase 19 (19-03): the --param channel (the generalized
# --batch-text typed-param contract over the advanced family) =====


def _parse_param_args(raw_values: list[str]) -> tuple:
    """Validate every ``--param NAME=VALUE`` pair against the frozen
    ``run_sweep.ADVANCED_TRAIN_FLAGS`` table (the single vocabulary
    authority — PD-19-11: names must be table flags, enum/bool values
    must come from the table's closed choices, int/float values must
    parse inside the table bounds, json values must be JSON objects).
    Returns the ``(row, raw_value)`` pairs in CLI order; raises
    ``ValueError`` with a message naming the valid vocabulary (the
    caller routes it to ``parser.error`` — refuse at parse, never
    mid-journey)."""
    parsed = []
    seen: set[str] = set()
    for raw in raw_values:
        name, sep, value = raw.partition("=")
        if not sep or not name or not value:
            raise ValueError(
                f"--param must be NAME=VALUE (got {raw!r})")
        field = name.lstrip("-").replace("-", "_")
        row = next(
            (spec for spec in run_sweep.ADVANCED_TRAIN_FLAGS
             if spec.flag.lstrip("-") == field), None)
        if row is None:
            vocabulary = ", ".join(
                spec.flag.lstrip("-")
                for spec in run_sweep.ADVANCED_TRAIN_FLAGS)
            raise ValueError(
                f"--param name {name!r} is not an ADVANCED_TRAIN_FLAGS "
                f"flag — the frozen 18-row table in pipeline/run_sweep.py "
                f"is the vocabulary (names: {vocabulary})")
        if field in seen:
            raise ValueError(
                f"--param {field} given twice — one value per flag")
        seen.add(field)
        if row.kind in ("enum", "bool"):
            if value not in (row.choices or ()):
                raise ValueError(
                    f"--param {field} must be one of "
                    f"{', '.join(row.choices or ())} (got {value!r})")
        elif row.kind == "int":
            try:
                number = int(value)
            except ValueError:
                raise ValueError(
                    f"--param {field} must be an integer (got "
                    f"{value!r})") from None
            lo, hi = row.lo, row.hi
            if lo is not None and number < lo:
                raise ValueError(
                    f"--param {field} must be >= {int(lo)} (got "
                    f"{value!r})")
            if hi is not None and number > hi:
                raise ValueError(
                    f"--param {field} must be <= {int(hi)} (got "
                    f"{value!r})")
        elif row.kind == "float":
            try:
                number = float(value)
            except ValueError:
                raise ValueError(
                    f"--param {field} must be a number (got "
                    f"{value!r})") from None
            below = row.lo is not None and number < row.lo
            above = row.hi is not None and number > row.hi
            if below or above:
                bound = (f">= {row.lo}" if row.hi is None
                         else f"in [{row.lo}, {row.hi}]")
                raise ValueError(
                    f"--param {field} must be {bound} (got {value!r})")
        else:  # json — the run_finetune argv-boundary dict shape
            try:
                obj = json.loads(value)
            except ValueError:
                raise ValueError(
                    f"--param {field} must be valid JSON (got "
                    f"{value!r})") from None
            if not isinstance(obj, dict):
                raise ValueError(
                    f"--param {field} must be a JSON object (got "
                    f"{value!r})")
        parsed.append((row, value))
    return tuple(parsed)


def _param_argv_token(row, value: str) -> str:
    """The argv token a typed ``--param`` value composes to — the EXACT
    ``_advanced_argv_elements`` serialization: the json kind re-dumps
    sorted-key (so a differently-spaced but equal JSON input normalizes
    identically), int/float via ``str`` of the PARSED number (a float
    ``2e-5`` composes as ``2e-05`` — the raw text never rides through),
    enum/bool verbatim (the closed string vocabulary)."""
    if row.kind == "json":
        return json.dumps(json.loads(value), sort_keys=True)
    if row.kind == "int":
        return str(int(value))
    if row.kind == "float":
        return str(float(value))
    return value


def _radioset_selected_id(app: DnallmMarkTui) -> str:
    """The open ChoiceModal's RadioSet cursor id — textual 8.2.8 marks
    the highlighted RadioButton with the ``-selected`` CSS class (probe-
    pinned; the cursor starts at the HEAD option regardless of the
    current mark, the peft-modal navigation precedent)."""
    radioset = app.screen.query_one(RadioSet)
    for button in radioset.query(RadioButton):
        if button.has_class("-selected"):
            return str(button.id)
    return ""


async def _drive_advanced_params(pilot: Pilot, app: DnallmMarkTui,
                                 screen: RunConfigScreen,
                                 ctx: RunContext) -> None:
    """The --param journey leg (19-03, PD-19-11): ensure the advanced
    section is EXPANDED (the [a] toggle — collapsed by default per
    PD-19-8), then for each parsed pair in order — Input-family kinds
    typed via the _type_into idiom into ``#cfg-input-<dasherized>``
    (the --batch-text idiom verbatim); enum/bool kinds driven through
    the REAL modal journey (focus the ChoiceRow, enter, verify the
    ChoiceModal lists the expected option, walk the RadioSet cursor
    onto it, first-toggle-apply). Every typed param is recorded in the
    evidence meta beside ``batch_input_value``."""
    picker = screen.query_one("#cfg-picker", PickerList)
    picker.focus()  # 'a' must reach the screen binding, never an Input
    await pilot.pause()
    section = screen.query_one("#cfg-adv-params", Vertical)
    if not section.display:
        await pilot.press("a")
        await wait_until(
            pilot, lambda: bool(section.display), 30.0,
            "advanced section expanded ([a])")
    typed: list[dict] = []
    for row, value in ctx.args.param_specs:
        field = row.flag.lstrip("-")
        dashed = field.replace("_", "-")
        if row.kind in ("enum", "bool"):
            choice_row = screen.query_one(f"#cfg-value-{dashed}", ChoiceRow)
            choice_row.focus()
            await pilot.pause()
            await pilot.press("enter")
            await wait_until(
                pilot, lambda: isinstance(app.screen, ChoiceModal), 30.0,
                f"choice modal for {field}")
            radioset = app.screen.query_one(RadioSet)
            option_ids = tuple(
                str(button.id) for button in radioset.query(RadioButton))
            if value not in option_ids:
                raise DriverError(
                    f"the {field} choice modal lists {option_ids!r} — the "
                    f"table vocabulary has no {value!r} option")
            for _press in range(len(option_ids)):
                if _radioset_selected_id(app) == value:
                    break
                await pilot.press("down")
                await pilot.pause()
            if _radioset_selected_id(app) != value:
                raise DriverError(
                    f"the {field} choice modal cursor never reached "
                    f"{value!r} (options {option_ids!r})")
            await pilot.press("enter")  # the first toggle applies + closes
            await wait_until(
                pilot, lambda: not isinstance(app.screen, ChoiceModal),
                30.0, f"choice modal closed ({field}={value})")
            if choice_row.value != value:
                raise DriverError(
                    f"#cfg-value-{dashed} holds {choice_row.value!r} "
                    f"after the pick (expected {value!r})")
        else:
            await _type_into(pilot, screen, f"#cfg-input-{dashed}", value)
        typed.append({"name": field, "value": value})
    ctx.meta["params_typed"] = typed


# =====================================================================
# The pa6 journey (unchanged behavior; --mode pa6 default)
# =====================================================================


async def journey(pilot: Pilot, app: DnallmMarkTui, ctx: RunContext) -> bool:
    """Drive the real app through the gate. Returns True when the launch
    path was taken (live mode); False when the rehearsal pressed n."""

    # --- a. boot settle + 01 ------------------------------------------
    env_verdict = await _wait_env_settled(pilot, app, ctx)
    ctx.meta["env_verdict"] = env_verdict
    await ctx.export(pilot, app, "01_boot_env_check")

    # --- b. navigate to slot 4 ----------------------------------------
    deadline = time.monotonic() + 120.0
    while not isinstance(app.screen, RunConfigScreen):
        await pilot.press("4")
        try:
            await wait_until(
                pilot, lambda: isinstance(app.screen, RunConfigScreen),
                10.0, "slot-4 navigation")
            break
        except DriverError:
            if time.monotonic() >= deadline:
                raise
    screen = app.screen
    assert isinstance(screen, RunConfigScreen)  # narrowing for ty
    await wait_until(
        pilot,
        lambda: len(screen.query_one("#cfg-picker", PickerList).options) > 0,
        60.0, "picker populated over the real registry")
    ctx.stage("slot4_arrived")

    # --- c. mark the 2 models -----------------------------------------
    for key in MODELS:
        await _filter_mark(pilot, screen, key)
    picker = screen.query_one("#cfg-picker", PickerList)
    selected = set(picker.selected)
    if not set(MODELS) <= selected:
        raise DriverError(
            f"model marks missing after the filter idiom: picker holds "
            f"{sorted(selected)!r}")
    ctx.stage("models_marked")
    await ctx.export(pilot, app, "02_picker_models")

    # --- d. m-flip + mark the 2 datasets -------------------------------
    await pilot.press("m")
    await pilot.pause()
    datasets_prefix = S.CFG_PICKER_DATASETS.format(
        n="__x__", total="__y__").split("__x__")[0]
    await wait_until(
        pilot,
        lambda: datasets_prefix in _label_text(screen, "#cfg-picker-title"),
        30.0, "datasets picker (m flip)")
    for key in TASKS:
        await _filter_mark(pilot, screen, key)
    selected = set(picker.selected)
    if not set(TASKS) <= selected:
        raise DriverError(
            f"task marks missing after the filter idiom: picker holds "
            f"{sorted(selected)!r}")
    ctx.stage("datasets_marked")
    await ctx.export(pilot, app, "03_picker_datasets")

    # --- e. params -----------------------------------------------------
    await _type_into(pilot, screen, "#cfg-input-seeds", SEEDS_TEXT)
    await _type_into(pilot, screen, "#cfg-input-epochs", EPOCHS_TEXT)
    await _type_into(pilot, screen, "#cfg-input-workers", WORKERS_TEXT)
    await _type_into(pilot, screen, "#cfg-input-gpus", GPUS_TEXT)
    await _type_into(pilot, screen, "#cfg-input-output-root", ctx.args.root)
    picker.focus()
    await settle(app, pilot, rounds=4)
    ctx.stage("params_typed")

    # --- f. the live preview line --------------------------------------
    expected_line = S.CFG_PREVIEW_LINE.format(
        models=len(MODELS), tasks=len(TASKS), seeds=1, cells=EXPECTED_CELLS)
    rendered = _label_text(screen, "#cfg-preview-line")
    if rendered != expected_line:
        raise DriverError(
            f"preview line mismatch: {rendered!r} != {expected_line!r}")
    ctx.stage("preview_line_asserted")
    await ctx.export(pilot, app, "04_run_config_params")

    # --- g. [p] dispatch argv preview ----------------------------------
    await pilot.press("p")
    await wait_until(
        pilot, lambda: isinstance(app.screen, PreviewModal), 30.0,
        "preview modal")
    lines = tuple(getattr(app.screen, "_lines", ()))
    argv_label = S.CFG_ARGV_LABEL
    argv_line = next(
        (str(line) for line in lines if str(line).startswith(argv_label)),
        "")
    tokens = argv_line[len(argv_label):].split() if argv_line else []
    ctx.meta["argv_line"] = argv_line
    ctx.meta["argv"] = tokens
    # The composer threads comma-joined matrix filters (models/tasks) —
    # the expected tokens mirror the pinned compose_dispatch_argv shape.
    expected_tokens = (
        "--mode", "dispatch", "--workers", WORKERS_TEXT,
        "--gpus", GPUS_TEXT, "--models", ",".join(MODELS),
        "--tasks", ",".join(TASKS), "--seeds", SEEDS_TEXT,
        "--num_train_epochs", EPOCHS_TEXT)
    for token in expected_tokens:
        if token not in tokens:
            raise DriverError(
                f"dispatch argv preview missing {token!r}: {argv_line!r}")
    if str(ctx.root) not in tokens:
        raise DriverError(
            f"dispatch argv preview missing the resolved root "
            f"{ctx.root}: {argv_line!r}")
    ctx.stage("argv_preview_asserted")
    await ctx.export(pilot, app, "05_run_config_preview")
    await pilot.press("escape")
    await wait_until(
        pilot, lambda: not isinstance(app.screen, PreviewModal), 30.0,
        "preview modal dismissed")

    # --- h. enter -> the Y/N gate --------------------------------------
    await settle(app, pilot, rounds=2)
    await pilot.press("enter")
    await wait_until(
        pilot,
        lambda: isinstance(
            app.screen, (_GateConfirmModal, ProblemsModal, EnvBlockModal)),
        180.0, "gate response (confirm or refusal)")
    if isinstance(app.screen, (ProblemsModal, EnvBlockModal)):
        # Honest halt: export the refusal, never press y.
        await ctx.export(pilot, app, "98_gate_refused")
        raise GateRefusedError(
            f"the gate refused the launch with "
            f"{type(app.screen).__name__} (see 98_gate_refused.svg)")
    assert isinstance(app.screen, _GateConfirmModal)
    message = str(getattr(app.screen, "_message", ""))
    if S.LNC_GATE_CONFIRM not in message:
        raise DriverError(
            f"gate message missing the confirm copy: {message!r}")
    dispatch_text = _plain(
        app.screen.query_one("#cfg-gate-dispatch", Static).content)
    if GPUS_TEXT not in dispatch_text:
        raise DriverError(
            f"gate dispatch-plan line missing GPUs {GPUS_TEXT!r}: "
            f"{dispatch_text!r}")
    ctx.stage("gate_confirm_reached")
    await ctx.export(pilot, app, "06_run_config_confirm")

    # --- i. n (rehearsal) or y (live) -----------------------------------
    if ctx.rehearsal:
        await pilot.press("n")
        await wait_until(
            pilot,
            lambda: not isinstance(app.screen, _GateConfirmModal), 30.0,
            "gate dismissed (rehearsal n)")
        ctx.stage("gate_dismissed_n")
        return False

    await pilot.press("y")
    ctx.stage("launch_y_pressed")
    try:
        await wait_until(
            pilot, lambda: isinstance(app.screen, MonitorScreen), 20.0,
            "monitor auto-switch")
    except DriverError:
        pass  # belt-and-braces below
    if not isinstance(app.screen, MonitorScreen):
        # The D-13 auto-switch rides a posted message through the launch
        # worker chain (preview -> env preflight -> spawn); a slow leg can
        # outlive the first wait — press 5 explicitly.
        await pilot.press("5")
        await wait_until(
            pilot, lambda: isinstance(app.screen, MonitorScreen), 60.0,
            "monitor via belt-and-braces 5")
    ctx.stage("monitor_switched")
    return True


async def watch_to_completion(pilot: Pilot, app: DnallmMarkTui,
                              ctx: RunContext) -> None:
    """The live-mode watch: wait for the root's monitor card + the
    dispatch orchestrator's state file, then poll on the --interval
    cadence until the repo's own /proc probe reports no live worker AND
    all 4 cells hold both artifacts."""
    basename = ctx.root.name

    # The launcher registry (the in-app spawn registered the root) feeds
    # the monitor's live_roots, so the card appears on the mount scan.
    async def _card_visible() -> None:
        await wait_until(
            pilot, lambda: basename in _screen_labels_text(app), 60.0,
            "monitor card for the launched root")

    try:
        await _card_visible()
    except DriverError:
        # The demo idiom fallback: [a] attach the resolved absolute path.
        ctx.note(
            "monitor card not discovered within 60s — driving the [a] "
            "attach modal with the resolved absolute path")
        await pilot.press("a")
        await wait_until(
            pilot,
            lambda: bool(app.screen.query("#path-input")), 30.0,
            "attach modal")
        path_input = app.screen.query_one("#path-input", Input)
        path_input.focus()
        await pilot.pause()
        for char in str(ctx.root):
            await pilot.press(char)
        await pilot.pause()
        await pilot.press("enter")
        await wait_until(
            pilot, lambda: not bool(app.screen.query("#path-input")), 30.0,
            "attach modal dismissed")
        await asyncio.sleep(3.0)
        await pilot.pause()
        await _card_visible()
    ctx.stage("monitor_card_visible")

    state_path = ctx.root / "dispatch_state.json"
    await wait_until(
        pilot, lambda: state_path.is_file(), 120.0,
        "dispatch_state.json (orchestrator alive signal)")
    ctx.stage("dispatch_state_present")

    # The tee lands under the fresh state dir's logs/ (O_EXCL name).
    logs_dir = ctx.state_dir / "logs"
    tee_deadline = time.monotonic() + 60.0
    while ctx.meta["tee_path"] is None:
        candidates = sorted(
            logs_dir.glob("*.log"),
            key=lambda path: path.stat().st_mtime, reverse=True)
        if candidates:
            ctx.meta["tee_path"] = str(candidates[0])
            break
        if time.monotonic() >= tee_deadline:
            break
        await asyncio.sleep(1.0)
        await pilot.pause()
    if ctx.meta["tee_path"] is None:
        ctx.note(f"no tee log found under {logs_dir} within 60s")

    interval = float(ctx.args.interval)
    deadline = time.monotonic() + float(ctx.args.timeout)
    capture_index = 0
    while True:
        # Sleep the interval in small chunks so the app's timers/workers
        # keep running (the monitor keeps refreshing under the exports).
        chunk_end = time.monotonic() + interval
        while time.monotonic() < chunk_end:
            await asyncio.sleep(min(2.0, max(0.0, chunk_end
                                             - time.monotonic())))
            await pilot.pause()

        capture_index += 1
        ctx.meta["nvidia_snapshots"].append(_gpu_snapshot())
        name = f"07_monitor_running_{capture_index:02d}"
        await ctx.export(pilot, app, name)
        ctx.meta["monitor_captures"].append(f"{name}.svg")

        root_key = str(ctx.root)
        probe = sweep_launcher.probe_cli_sweeps()
        probe_absent = root_key not in probe
        metrics = _count_seed_artifacts(ctx.root, "final_metrics.json",
                                        SEEDS_TEXT)
        flops = _count_seed_artifacts(ctx.root, "flops_report.json",
                                      SEEDS_TEXT)
        status = _dispatch_status(state_path)
        ctx.meta["completion"] = {
            "checked_at": _now_iso(),
            "probe_absent": probe_absent,
            "final_metrics": metrics,
            "flops_report": flops,
            "dispatch_status": status,
        }
        print(
            f"[watch] probe_absent={probe_absent} final_metrics={metrics} "
            f"flops={flops} dispatch_status={status!r}", flush=True)
        if probe_absent and metrics == EXPECTED_CELLS \
                and flops == EXPECTED_CELLS:
            ctx.meta["dispatch_state"] = _read_dispatch_state(state_path)
            return
        if time.monotonic() >= deadline:
            ctx.meta["dispatch_state"] = _read_dispatch_state(state_path)
            raise DriverError(
                f"overall timeout ({float(ctx.args.timeout):.0f}s) with "
                f"probe_absent={probe_absent}, final_metrics={metrics}, "
                f"flops={flops}, dispatch_status={status!r} — the sweep "
                "SURVIVES detached; see the re-attach section")
        failures_present = (ctx.root / "sweep_failures.json").is_file()
        if probe_absent and (metrics < EXPECTED_CELLS
                             or flops < EXPECTED_CELLS) and (
                failures_present
                or status in _DISPATCH_TERMINAL_BAD
                or status == _DISPATCH_TERMINAL_OK):
            ctx.meta["dispatch_state"] = _read_dispatch_state(state_path)
            raise DriverError(
                f"the sweep ended without the expected artifacts "
                f"(probe_absent={probe_absent}, final_metrics={metrics}, "
                f"flops={flops}, dispatch_status={status!r}, "
                f"sweep_failures.json={failures_present}) — honest "
                "failure; see the re-attach section")


def _dispatch_status(state_path: Path) -> str | None:
    """The dispatch orchestrator's status field (None when unreadable —
    corroboration only, never the sole signal)."""
    state = _read_dispatch_state(state_path)
    if isinstance(state, dict):
        value = state.get("status")
        if isinstance(value, str):
            return value
    return None


def _read_dispatch_state(state_path: Path) -> dict | None:
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


# =====================================================================
# The full journey (quick-261022-tah: download phase + multi-day run)
# =====================================================================


async def _navigate(pilot: Pilot, app: DnallmMarkTui, key: str,
                    screen_type: type, label: str) -> None:
    """Press a slot digit until the target screen type is active (the
    pa6 slot-4 navigation loop, generalized)."""
    deadline = time.monotonic() + 120.0
    while not isinstance(app.screen, screen_type):
        await pilot.press(key)
        try:
            await wait_until(
                pilot, lambda: isinstance(app.screen, screen_type),
                10.0, label)
            break
        except DriverError:
            if time.monotonic() >= deadline:
                raise


async def _locate_selection_row(pilot: Pilot, app: DnallmMarkTui,
                                key: str) -> None:
    """The selection screen's own filter idiom (pa6's _filter_mark shape
    re-targeted): '/' focuses #selection-filter, the key text narrows the
    table, the cursor walks onto the exact row (a bare filter legitimately
    matches prefix-sharing siblings — the row key reads via
    coordinate_to_cell_key exactly like the screen's _cursor_key)."""
    screen = app.screen
    assert isinstance(screen, SelectionScreen)  # narrowing for ty
    await pilot.press("slash")
    await pilot.pause()
    for char in key:
        await pilot.press(char)
    await pilot.pause()
    table = screen.query_one("#selection-table", DataTable)
    rows = table.row_count
    if rows < 1:
        raise DriverError(f"selection filter {key!r} matched no rows")
    table.focus()
    await pilot.pause()
    for _ in range(rows):
        coordinate = table.cursor_coordinate
        if table.is_valid_coordinate(coordinate):
            row_key = str(
                table.coordinate_to_cell_key(coordinate)[0].value)
            if row_key == key:
                return
        await pilot.press("down")
        await pilot.pause()
    raise DriverError(
        f"selection filter {key!r} matched {rows} rows and the cursor "
        "never reached the target row")


async def _slot2_model_leg(pilot: Pilot, app: DnallmMarkTui,
                           ctx: RunContext) -> None:
    """Slot 2: locate the FungiHelixSeek row (always) and, in live mode,
    press 'd' — the real KIND_MODEL enqueue through the app's own queue
    (the queue state file is the assertion; the toast is not)."""
    await _navigate(pilot, app, "2", SelectionScreen, "slot-2 navigation")
    screen = app.screen
    assert isinstance(screen, SelectionScreen)  # narrowing for ty
    await wait_until(
        pilot,
        lambda: screen.query_one("#selection-table", DataTable).row_count
        > 0,
        60.0, "selection table populated over the real registry")
    ctx.stage("slot2_arrived")
    await _locate_selection_row(pilot, app, FULL_MODEL)
    ctx.stage("model_row_located")
    await ctx.export(pilot, app, "002_model_row_missing")
    if ctx.rehearsal:
        ctx.note("rehearsal: slot-2 LOCATE only (no 'd', zero network)")
        return
    if ctx.targets.get("model_on_disk"):
        ctx.note(
            "model already on disk at preflight — the slot-2 enqueue leg "
            "is honestly skipped (gate outcome recorded)")
        return
    await pilot.press("d")
    await pilot.pause()

    def _model_active() -> bool:
        entry = _entry(
            _read_queue_entries(ctx.state_dir), FULL_MODEL)
        return (entry is not None
                and entry.get("kind") == download_queue.KIND_MODEL
                and entry.get("state") in _QUEUE_ACTIVE)

    try:
        await wait_until(pilot, _model_active, 30.0,
                         "model entry pending/downloading in the queue "
                         "state file")
    except DriverError:
        ctx.meta["download"]["model_enqueue"] = {
            "key": FULL_MODEL,
            "outcome": "refused_or_silent",
            "model_on_disk": ctx.targets.get("model_on_disk"),
            "modelscope_cli": ctx.targets.get("modelscope_cli"),
            "repo_id": ctx.targets.get("model_repo_id"),
        }
        raise DriverError(
            f"the slot-2 'd' press did not enqueue {FULL_MODEL} (no "
            "KIND_MODEL entry in the queue state file within 30s) — "
            "honest halt; the preflight facts are recorded in "
            "evidence.download.model_enqueue")
    entry = _entry(_read_queue_entries(ctx.state_dir), FULL_MODEL)
    ctx.meta["download"]["model_enqueue"] = {
        "key": FULL_MODEL,
        "outcome": "enqueued",
        "state": entry.get("state") if entry else None,
    }
    ctx.stage("model_enqueued")
    await ctx.export(pilot, app, "003_model_enqueued")


async def _slot3_dataset_leg(pilot: Pilot, app: DnallmMarkTui,
                             ctx: RunContext) -> None:
    """Slot 3: render the PRIMARY full presence view (always) and, in
    live mode, press 'a' — enqueue_all_missing through the real service
    (the queue state file holds the missing downloadable entries as
    pending; the disabled/unknown keys are skipped silently — the
    service's honest behavior)."""
    await _navigate(pilot, app, "3", DataManagerScreen,
                    "slot-3 navigation")
    screen = app.screen
    assert isinstance(screen, DataManagerScreen)  # narrowing for ty
    await wait_until(
        pilot,
        lambda: screen.query_one("#dl-missing", DataTable).row_count > 0,
        60.0, "data manager snapshot (dl-missing rows)")
    ctx.stage("slot3_arrived")
    await ctx.export(pilot, app, "004_data_presence_before")
    if ctx.rehearsal:
        ctx.note("rehearsal: slot-3 render only (no 'a', zero network)")
        return

    def _dataset_pending() -> bool:
        return any(
            entry.get("kind") == download_queue.KIND_DATASET
            and entry.get("state") in _QUEUE_ACTIVE
            for entry in _read_queue_entries(ctx.state_dir))

    await pilot.press("a")
    await pilot.pause()
    try:
        await wait_until(pilot, _dataset_pending, 60.0,
                         "dataset entries pending in the queue state file")
    except DriverError:
        entries = _read_queue_entries(ctx.state_dir)
        ctx.meta["download"]["dataset_enqueue"] = {
            "outcome": "nothing_enqueued",
            "entries": len(entries),
        }
        raise DriverError(
            "the slot-3 'a' press enqueued no dataset (no pending "
            "dataset entry in the queue state file within 60s) — honest "
            "halt (zero downloadable datasets is the honest-stop rule)")
    # NOTE: deliberately NO settle()/wait_for_complete here — the queue
    # drain worker runs for the WHOLE download phase (minutes-to-days)
    # and wait_for_complete would block the journey on it (the live-run
    # lesson: the enqueue wait above is the machine assertion; the pause
    # rounds below let the toast/reload renders land without waiting on
    # any worker).
    for _ in range(3):
        await pilot.pause()
    entries = _read_queue_entries(ctx.state_dir)
    dataset_entries = [
        entry for entry in entries
        if entry.get("kind") == download_queue.KIND_DATASET]
    ctx.meta["download"]["dataset_enqueue"] = {
        "outcome": "enqueued",
        "count": len(dataset_entries),
        "digest": _queue_digest(entries),
    }
    ctx.stage(f"datasets_enqueued_{len(dataset_entries)}")
    await ctx.export(pilot, app, "005_data_enqueue_all")


async def _download_settle_exports(pilot: Pilot, app: DnallmMarkTui,
                                   ctx: RunContext,
                                   entries: list[dict]) -> None:
    """The settle captures: the settled queue view, the v-toggled
    missing-only view (one capture, then v back), the final presence
    view, and the queue detail drill-down on a representative row."""
    screen = app.screen
    assert isinstance(screen, DataManagerScreen)  # narrowing for ty
    await ctx.export(pilot, app, "007_download_settled_queue")
    await pilot.press("v")
    await pilot.pause()
    await ctx.export(pilot, app, "007_download_settled_missing_view")
    await pilot.press("v")
    await pilot.pause()
    await ctx.export(pilot, app, "008_download_presence_final")

    table = screen.query_one("#dl-queue", DataTable)
    table.focus()
    await pilot.pause()
    done_keys = [
        entry.get("key") for entry in entries
        if entry.get("kind") == download_queue.KIND_DATASET
        and entry.get("state") == "done"]
    fallback = [
        entry.get("key") for entry in entries
        if entry.get("kind") == download_queue.KIND_DATASET]
    target = (done_keys or fallback or [None])[0]
    if isinstance(target, str):
        rows = table.row_count
        for _ in range(rows):
            coordinate = table.cursor_coordinate
            if table.is_valid_coordinate(coordinate):
                row_key = str(
                    table.coordinate_to_cell_key(coordinate)[0].value)
                if row_key == target:
                    break
            await pilot.press("down")
            await pilot.pause()
        await pilot.press("enter")
        await wait_until(
            pilot, lambda: isinstance(app.screen, QueueDetailModal), 30.0,
            "queue detail modal")
        await ctx.export(pilot, app, "009_queue_detail_modal")
        await pilot.press("escape")
        await wait_until(
            pilot, lambda: not isinstance(app.screen, QueueDetailModal),
            30.0, "queue detail modal dismissed")
    else:
        ctx.note("no dataset queue row for the detail drill-down "
                 "(the queue pane is empty at settle)")


async def _download_watch(pilot: Pilot, app: DnallmMarkTui,
                          ctx: RunContext) -> list[dict]:
    """The download-phase watch: capture 006_download_running_NNN every
    --dl-interval seconds until the queue settles (no pending/downloading
    entries on two reads >= 60 s apart AND the model entry terminal),
    the settle exports. A stall (--stall-hours with zero liveness
    signal) records honestly + captures 997 and keeps watching unless
    --exit-on-stall."""
    logs_dir = ctx.state_dir / "logs"
    interval = max(30.0, float(ctx.args.dl_interval))
    stall = _StallWatch(float(ctx.args.stall_hours))
    stall_captured = False
    capture_index = 0
    candidate_at: float | None = None
    candidate_digest: dict | None = None

    def _signature() -> tuple:
        state_file = _queue_state_path(ctx.state_dir)
        try:
            stat = state_file.stat()
            file_sig = (stat.st_mtime_ns, stat.st_size)
        except OSError:
            file_sig = (0, 0)
        log_name, log_size = _newest_log_stat(logs_dir)
        return (file_sig, log_name, log_size)

    while True:
        entries = _read_queue_entries(ctx.state_dir)
        active = [entry for entry in entries
                  if entry.get("state") in _QUEUE_ACTIVE]
        digest = _queue_digest(entries)
        model_entry = _entry(entries, FULL_MODEL)
        model_terminal = (
            model_entry is None
            or model_entry.get("state") not in _QUEUE_ACTIVE)
        if not active and model_terminal:
            if candidate_digest == digest \
                    and candidate_at is not None \
                    and time.monotonic() - candidate_at >= 60.0:
                ctx.meta["download"]["settle"] = {
                    "at": _now_iso(),
                    "digest": digest,
                }
                await _download_settle_exports(pilot, app, ctx, entries)
                return entries
            if candidate_digest != digest or candidate_at is None:
                candidate_at = time.monotonic()
                candidate_digest = digest
        else:
            candidate_at = None
            candidate_digest = None

        if stall.observe(_signature()):
            note = (f"download stall: no queue-state or log change for "
                    f"{float(ctx.args.stall_hours):.1f}h "
                    f"(digest={digest})")
            ctx.note(note)
            if not stall_captured:
                await ctx.export(pilot, app, "997_download_stall")
                stall_captured = True
            if ctx.args.exit_on_stall:
                raise DriverError(
                    "download stalled (--exit-on-stall) — the queue "
                    "SURVIVES; see the re-attach section")

        capture_index += 1
        name = f"006_download_running_{capture_index:03d}"
        log_name, log_size = _newest_log_stat(logs_dir)
        ctx.meta["queue_digests"].append({
            "at": _now_iso(), "capture": f"{name}.svg",
            "digest": digest, "newest_log": [log_name, log_size],
        })
        await ctx.export(pilot, app, name)
        ctx.meta["dl_captures"].append(f"{name}.svg")
        ctx.heartbeat("download", capture_index)
        await _sleep_interval(pilot, interval)


async def _sleep_interval(pilot: Pilot, interval: float) -> None:
    """Sleep one interval in small chunks so the app's timers/workers
    keep running (the pa6 watch-loop discipline)."""
    chunk_end = time.monotonic() + interval
    while time.monotonic() < chunk_end:
        await asyncio.sleep(min(2.0, max(0.0, chunk_end - time.monotonic())))
        await pilot.pause()


def _write_ledger(ctx: RunContext) -> dict:
    """The settle ledger: per queue key the final persisted state; the
    not-enqueued official keys with their resolve_channel disposition
    (read-only derivation through the real service's own resolver); the
    already-present-before keys; the derived present set + expected
    cells. Written to --ledger; returns the doc for the meta."""
    entries = _read_queue_entries(ctx.state_dir)
    present, before = _derive_present(ctx.state_dir)
    service = download_queue.DownloadQueueService(
        state_path=_queue_state_path(ctx.state_dir))
    queued_keys = {str(entry.get("key")) for entry in entries}
    not_enqueued: list[dict] = []
    for key in _official_dataset_keys():
        if key in queued_keys or key in set(before):
            continue
        spec = service.resolve_channel(key)
        if spec is None:
            not_enqueued.append(
                {"key": key, "channel": "unknown_key",
                 "reason": "unknown_key"})
            continue
        not_enqueued.append({
            "key": key,
            "channel": download_queue.channel_state(spec),
            "reason": spec.reason_code,
            "source_url": spec.source_url,
        })
    ledger = {
        "written_at": _now_iso(),
        "queue_entries": [
            {
                "key": entry.get("key"),
                "kind": entry.get("kind"),
                "state": entry.get("state"),
                "attempts": entry.get("attempts"),
                "problems": entry.get("problems"),
                "log_path": entry.get("log_path"),
                "enqueued_at": entry.get("enqueued_at"),
                "started_at": entry.get("started_at"),
                "finished_at": entry.get("finished_at"),
            }
            for entry in entries],
        "not_enqueued": not_enqueued,
        "present_before_download": sorted(before),
        "present_set": sorted(present),
        "expected_cells": len(present) * len(FULL_SEEDS),
    }
    _atomic_write(
        Path(ctx.args.ledger),
        json.dumps(ledger, indent=2, ensure_ascii=False))
    ctx.meta["present_set"] = sorted(present)
    ctx.meta["expected_cells"] = ledger["expected_cells"]
    ctx.meta["download"]["ledger"] = str(ctx.args.ledger)
    return ledger


async def _wizard_gate_full(pilot: Pilot, app: DnallmMarkTui,
                            ctx: RunContext,
                            present: list[str]) -> bool:
    """Slot 4 re-targeted (the pa6 c-h steps over the full combo): mark
    FungiHelixSeek, m-flip, mark EVERY present-set key, type the params
    (seeds 42,43,44; workers 2; gpus 0,1; the fresh root — the epochs
    input is NEVER touched, only READ), assert the preview line, the [p]
    argv (with --num_train_epochs ABSENT — the YAML-default proof), and
    the gate. Returns True on the live launch path."""
    await _navigate(pilot, app, "4", RunConfigScreen, "slot-4 navigation")
    screen = app.screen
    assert isinstance(screen, RunConfigScreen)  # narrowing for ty
    await wait_until(
        pilot,
        lambda: len(screen.query_one("#cfg-picker", PickerList).options) > 0,
        60.0, "picker populated over the real registry")
    ctx.stage("slot4_arrived")

    await _filter_mark(pilot, screen, FULL_MODEL)
    picker = screen.query_one("#cfg-picker", PickerList)
    if set(picker.selected) != {FULL_MODEL}:
        raise DriverError(
            f"model mark wrong after the filter idiom: picker holds "
            f"{sorted(picker.selected)!r}")
    ctx.stage("wizard_model_marked")
    await ctx.export(pilot, app, "010_wizard_model_marked")

    await pilot.press("m")
    await pilot.pause()
    datasets_prefix = S.CFG_PICKER_DATASETS.format(
        n="__x__", total="__y__").split("__x__")[0]
    await wait_until(
        pilot,
        lambda: datasets_prefix in _label_text(screen, "#cfg-picker-title"),
        30.0, "datasets picker (m flip)")
    for key in present:
        await _filter_mark(pilot, screen, key)
    # The picker's `selected` is scoped to the CURRENT kind's rendered
    # rows (SelectionList semantics — after the m-flip it holds the
    # dataset marks only), so the assert is the exact per-view set; the
    # model mark was asserted on the models view above, and the union is
    # proven by the preview line below (1 model x N tasks x 3 seeds).
    selected = set(picker.selected)
    if selected != set(present):
        raise DriverError(
            f"wizard dataset marks wrong: picker holds {len(selected)} "
            f"dataset marks, expected exactly the {len(present)}-key "
            "present set")
    ctx.stage("wizard_datasets_marked")
    await ctx.export(pilot, app, "011_wizard_datasets_marked")

    await _type_into(pilot, screen, "#cfg-input-seeds", FULL_SEEDS_TEXT)
    await _type_into(pilot, screen, "#cfg-input-workers",
                     FULL_WORKERS_TEXT)
    await _type_into(pilot, screen, "#cfg-input-gpus", FULL_GPUS_TEXT)
    await _type_into(pilot, screen, "#cfg-input-output-root", ctx.args.root)
    # 261023-abu: --batch-text N types the STARTING per-device batch into
    # the new input row (present-only threading); the default "" NEVER
    # touches the batch input — the epochs-today discipline.
    if ctx.args.batch_text:
        await _type_into(pilot, screen, "#cfg-input-batch-size",
                         ctx.args.batch_text)
    epochs_widget = screen.query_one("#cfg-input-epochs", Input)
    ctx.meta["epochs_input_value"] = epochs_widget.value
    batch_widget = screen.query_one("#cfg-input-batch-size", Input)
    ctx.meta["batch_input_value"] = batch_widget.value
    # 19-03: the --param channel — expand the advanced section and
    # type/pick every parsed pair (recorded in the meta beside
    # batch_input_value); the default [] NEVER touches the section.
    if ctx.args.param_specs:
        await _drive_advanced_params(pilot, app, screen, ctx)
    picker.focus()
    await settle(app, pilot, rounds=4)
    ctx.stage("params_typed")

    expected = len(present) * len(FULL_SEEDS)
    expected_line = S.CFG_PREVIEW_LINE.format(
        models=1, tasks=len(present), seeds=len(FULL_SEEDS), cells=expected)
    rendered = _label_text(screen, "#cfg-preview-line")
    if rendered != expected_line:
        raise DriverError(
            f"preview line mismatch: {rendered!r} != {expected_line!r}")
    ctx.stage("preview_line_asserted")
    await ctx.export(pilot, app, "012_run_config_params")

    await pilot.press("p")
    await wait_until(
        pilot, lambda: isinstance(app.screen, PreviewModal), 30.0,
        "preview modal")
    lines = tuple(getattr(app.screen, "_lines", ()))
    argv_label = S.CFG_ARGV_LABEL
    argv_line = next(
        (str(line) for line in lines if str(line).startswith(argv_label)),
        "")
    tokens = argv_line[len(argv_label):].split() if argv_line else []
    ctx.meta["argv_line"] = argv_line
    ctx.meta["argv"] = tokens
    expected_tokens = (
        "--mode", "dispatch", "--workers", FULL_WORKERS_TEXT,
        "--gpus", FULL_GPUS_TEXT, "--models", FULL_MODEL,
        "--tasks", ",".join(present), "--seeds", FULL_SEEDS_TEXT)
    for token in expected_tokens:
        if token not in tokens:
            raise DriverError(
                f"dispatch argv preview missing {token!r}: {argv_line!r}")
    if str(ctx.root) not in tokens:
        raise DriverError(
            f"dispatch argv preview missing the resolved root "
            f"{ctx.root}: {argv_line!r}")
    if "--num_train_epochs" in tokens:
        raise DriverError(
            f"dispatch argv preview carries --num_train_epochs "
            f"(the epochs input was never touched — the YAML default "
            f"must govern): {argv_line!r}")
    if ctx.args.batch_text:
        # 261023-abu: the typed starting batch threads --batch_size N.
        if "--batch_size" not in tokens or ctx.args.batch_text not in (
                tokens[tokens.index("--batch_size") + 1:
                       tokens.index("--batch_size") + 2]):
            raise DriverError(
                f"dispatch argv preview missing --batch_size "
                f"{ctx.args.batch_text} (the batch input was typed): "
                f"{argv_line!r}")
    elif "--batch_size" in tokens:
        raise DriverError(
            f"dispatch argv preview carries --batch_size "
            f"(the batch input was never touched — the child's YAML "
            f"default + dynamic scaling must govern): {argv_line!r}")
    # 19-03: the --param assertion PAIR (the 261023-abu --batch-text
    # contract, generalized loop-style over the table) — every typed
    # param REQUIRES its adjacent [flag, serialized-value] pair, and
    # every UNTOUCHED table flag must stay ABSENT (the YAML governs).
    # The value match is whitespace-piece-wise: a json-kind token
    # ({"a": 2}) legitimately carries spaces, so the single-space-joined
    # preview line splits it into pieces that must match IN ORDER.
    typed_tokens = {
        row.flag: _param_argv_token(row, value)
        for row, value in ctx.args.param_specs}
    for row, value in ctx.args.param_specs:
        flag = row.flag
        token = typed_tokens[flag]
        if flag not in tokens:
            raise DriverError(
                f"dispatch argv preview missing {flag} (the --param "
                f"channel typed {flag}={value}): {argv_line!r}")
        expected_pieces = token.split()
        start = tokens.index(flag) + 1
        if tokens[start:start + len(expected_pieces)] != expected_pieces:
            raise DriverError(
                f"dispatch argv preview missing the pair [{flag}, "
                f"{token}] (the --param channel typed {value}): "
                f"{argv_line!r}")
    for spec in run_sweep.ADVANCED_TRAIN_FLAGS:
        if spec.flag in typed_tokens:
            continue
        if spec.flag in tokens:
            raise DriverError(
                f"dispatch argv preview carries {spec.flag} (an "
                f"untouched table flag must stay ABSENT — the YAML "
                f"governs): {argv_line!r}")
    ctx.stage("argv_preview_asserted")
    await ctx.export(pilot, app, "013_run_config_preview")
    await pilot.press("escape")
    await wait_until(
        pilot, lambda: not isinstance(app.screen, PreviewModal), 30.0,
        "preview modal dismissed")

    await settle(app, pilot, rounds=2)
    await pilot.press("enter")
    await wait_until(
        pilot,
        lambda: isinstance(
            app.screen, (_GateConfirmModal, ProblemsModal, EnvBlockModal)),
        180.0, "gate response (confirm or refusal)")
    if isinstance(app.screen, (ProblemsModal, EnvBlockModal)):
        await ctx.export(pilot, app, "998_gate_refused")
        raise GateRefusedError(
            f"the gate refused the launch with "
            f"{type(app.screen).__name__} (see 998_gate_refused.svg)")
    assert isinstance(app.screen, _GateConfirmModal)
    message = str(getattr(app.screen, "_message", ""))
    if S.LNC_GATE_CONFIRM not in message:
        raise DriverError(
            f"gate message missing the confirm copy: {message!r}")
    dispatch_text = _plain(
        app.screen.query_one("#cfg-gate-dispatch", Static).content)
    if FULL_GPUS_TEXT not in dispatch_text:
        raise DriverError(
            f"gate dispatch-plan line missing GPUs {FULL_GPUS_TEXT!r}: "
            f"{dispatch_text!r}")
    ctx.stage("gate_confirm_reached")
    await ctx.export(pilot, app, "014_run_config_confirm")

    if ctx.rehearsal:
        await pilot.press("n")
        await wait_until(
            pilot,
            lambda: not isinstance(app.screen, _GateConfirmModal), 30.0,
            "gate dismissed (rehearsal n)")
        ctx.stage("gate_dismissed_n")
        return False

    await pilot.press("y")
    ctx.stage("launch_y_pressed")
    try:
        await wait_until(
            pilot, lambda: isinstance(app.screen, MonitorScreen), 20.0,
            "monitor auto-switch")
    except DriverError:
        pass  # belt-and-braces below
    if not isinstance(app.screen, MonitorScreen):
        await pilot.press("5")
        await wait_until(
            pilot, lambda: isinstance(app.screen, MonitorScreen), 60.0,
            "monitor via belt-and-braces 5")
    ctx.stage("monitor_switched")
    return True


async def journey_full(pilot: Pilot, app: DnallmMarkTui,
                       ctx: RunContext) -> bool:
    """The full production journey: boot -> slot-2 model download ->
    slot-3 enqueue-all -> download watch to settle -> ledger + matrix ->
    wizard -> gate -> (rehearsal n | live y + monitor)."""
    env_verdict = await _wait_env_settled(pilot, app, ctx)
    ctx.meta["env_verdict"] = env_verdict
    await ctx.export(pilot, app, "001_boot_env_check")

    await _slot2_model_leg(pilot, app, ctx)
    await _slot3_dataset_leg(pilot, app, ctx)
    if not ctx.rehearsal:
        await _download_watch(pilot, app, ctx)

    ledger = _write_ledger(ctx)
    present = list(ledger["present_set"])
    ctx.stage(f"matrix_derived_{len(present)}x{len(FULL_SEEDS)}")
    if not present:
        raise DriverError(
            "the present set is EMPTY after the download settle — honest "
            "halt (the ledger + draft report record why)")

    return await _wizard_gate_full(pilot, app, ctx, present)


def _max_mtime(root: Path) -> float:
    """Newest file mtime under the root (0.0 when empty) — the run-phase
    liveness signal."""
    newest = 0.0
    try:
        for path in root.rglob("*"):
            if path.is_file():
                newest = max(newest, path.stat().st_mtime)
    except OSError:
        pass
    return newest


async def _terminal_tail(pilot: Pilot, state_path: Path,
                         ctx: RunContext, expected: int) -> dict:
    """The pa6 ~80 s tail lesson: after the artifact counts reach the
    expected matrix, quiesce-poll (up to 10 min) for the orchestrator's
    terminal state + the trainer_state marker counts. Returns the final
    observation (honest either way)."""
    deadline = time.monotonic() + 600.0
    while True:
        status = _dispatch_status(state_path)
        trainers = _count_seed_artifacts(
            ctx.root, "trainer_state.json", FULL_SEEDS)
        state = _read_dispatch_state(state_path)
        counts = (state or {}).get("counts") \
            if isinstance(state, dict) else None
        if status == _DISPATCH_TERMINAL_OK and trainers == expected:
            return {"status": status, "trainer_state": trainers,
                    "counts": counts, "quiesced": True}
        if time.monotonic() >= deadline:
            return {"status": status, "trainer_state": trainers,
                    "counts": counts, "quiesced": False}
        await asyncio.sleep(5.0)
        await pilot.pause()


async def watch_run_full(pilot: Pilot, app: DnallmMarkTui,
                         ctx: RunContext) -> None:
    """The multi-day run watch: monitor card + [a]-attach fallback +
    dispatch_state + tee, then per-interval captures (gpu snapshot +
    dispatch digest + per-seed artifact counts) until the completion
    predicate (probe absent + per-seed counts == len(present) for BOTH
    artifacts), the failure end, the stall, or (if set) the hard timeout.
    The sweep is NEVER killed on any path."""
    expected = int(ctx.meta["expected_cells"] or 0)
    present_count = len(ctx.meta["present_set"] or [])
    basename = ctx.root.name

    async def _card_visible() -> None:
        await wait_until(
            pilot, lambda: basename in _screen_labels_text(app), 60.0,
            "monitor card for the launched root")

    try:
        await _card_visible()
    except DriverError:
        ctx.note(
            "monitor card not discovered within 60s — driving the [a] "
            "attach modal with the resolved absolute path")
        await pilot.press("a")
        await wait_until(
            pilot,
            lambda: bool(app.screen.query("#path-input")), 30.0,
            "attach modal")
        path_input = app.screen.query_one("#path-input", Input)
        path_input.focus()
        # The live-run lesson: the modal's on_mount focus races the first
        # key presses (the typed path arrived TRUNCATED and the submit
        # failed validation) — wait for REAL focus, then type and VERIFY
        # the value, clearing + retrying once on any mismatch.
        await wait_until(
            pilot, lambda: path_input.has_focus, 10.0,
            "attach input focus")
        await pilot.pause()
        typed_ok = False
        for _attempt in range(2):
            for char in str(ctx.root):
                await pilot.press(char)
            await pilot.pause()
            if path_input.value == str(ctx.root):
                typed_ok = True
                break
            await pilot.press("end")
            await pilot.pause()
            for _ in range(len(path_input.value) + 3):
                await pilot.press("backspace")
            await pilot.pause()
        if not typed_ok:
            raise DriverError(
                f"attach input holds {path_input.value!r} after two "
                f"typing attempts (expected {str(ctx.root)!r}) — honest "
                "halt; the sweep is unaffected")
        await pilot.press("enter")
        try:
            await wait_until(
                pilot, lambda: not bool(app.screen.query("#path-input")),
                30.0, "attach modal dismissed")
        except DriverError:
            problems = _plain(app.screen.query_one(
                "#path-problems", Static).content)
            raise DriverError(
                f"the attach modal refused the root (validation "
                f"problems: {problems!r}) — honest halt; the sweep is "
                "unaffected") from None
        await asyncio.sleep(3.0)
        await pilot.pause()
        await _card_visible()
    ctx.stage("monitor_card_visible")

    state_path = ctx.root / "dispatch_state.json"
    await wait_until(
        pilot, lambda: state_path.is_file(), 120.0,
        "dispatch_state.json (orchestrator alive signal)")
    ctx.stage("dispatch_state_present")

    logs_dir = ctx.state_dir / "logs"
    tee_deadline = time.monotonic() + 60.0
    while ctx.meta["tee_path"] is None:
        candidates = sorted(
            (path for path in logs_dir.glob("*.log")
             if "sweep_" in path.name),
            key=lambda path: path.stat().st_mtime, reverse=True)
        if not candidates and ctx.attach:
            # Attach mode: the sweep's tee was opened by the LAUNCHING
            # driver's state dir — search the pinned prefix family.
            candidates = sorted(
                Path(ctx.args.state_base).glob(
                    f"{FULL_STATE_PREFIX}*/logs/sweep_*.log"),
                key=lambda path: path.stat().st_mtime, reverse=True)
        if candidates:
            ctx.meta["tee_path"] = str(candidates[0])
            break
        if time.monotonic() >= tee_deadline:
            break
        await asyncio.sleep(1.0)
        await pilot.pause()
    if ctx.meta["tee_path"] is None:
        ctx.note(f"no sweep tee log found under {logs_dir} within 60s")

    tee_path = Path(ctx.meta["tee_path"]) if ctx.meta["tee_path"] else None

    def _tee_size() -> int:
        if tee_path is None:
            return -1
        try:
            return tee_path.stat().st_size
        except OSError:
            return -1

    # First run-phase capture (numbering continues past any existing
    # 015 family — an attach watch may follow a journey driver that
    # already captured some intervals before dying).
    existing = [path.name for path in ctx.svg_dir.glob(
        "015_monitor_running_*.svg")]
    indices = [int(name[len("015_monitor_running_"):-len(".svg")])
               for name in existing]
    capture_index = max(indices, default=0) + 1
    first_name = f"015_monitor_running_{capture_index:03d}"
    ctx.meta["nvidia_snapshots"].append(_gpu_snapshot())
    await ctx.export(pilot, app, first_name)
    ctx.meta["monitor_captures"].append(f"{first_name}.svg")
    ctx.heartbeat("run", capture_index)

    interval = max(30.0, float(ctx.args.interval))
    stall = _StallWatch(float(ctx.args.stall_hours))
    stall_captured = False
    deadline = (None if float(ctx.args.timeout) <= 0
                else time.monotonic() + float(ctx.args.timeout))
    capture_index = 1
    while True:
        await _sleep_interval(pilot, interval)
        capture_index += 1
        ctx.meta["nvidia_snapshots"].append(_gpu_snapshot())
        name = f"015_monitor_running_{capture_index:03d}"
        await ctx.export(pilot, app, name)
        ctx.meta["monitor_captures"].append(f"{name}.svg")

        root_key = str(ctx.root)
        probe = sweep_launcher.probe_cli_sweeps()
        probe_absent = root_key not in probe
        metrics = _count_per_seed(
            ctx.root, "final_metrics.json", FULL_SEEDS)
        flops = _count_per_seed(ctx.root, "flops_report.json", FULL_SEEDS)
        status = _dispatch_status(state_path)
        ctx.meta["completion"] = {
            "checked_at": _now_iso(),
            "probe_absent": probe_absent,
            "final_metrics_per_seed": metrics,
            "flops_report_per_seed": flops,
            "dispatch_status": status,
        }
        ctx.heartbeat("run", capture_index)
        print(
            f"[watch] probe_absent={probe_absent} "
            f"final_metrics={metrics} flops={flops} "
            f"dispatch_status={status!r}", flush=True)

        metrics_done = all(
            count == present_count for count in metrics.values())
        flops_done = all(
            count == present_count for count in flops.values())
        if probe_absent and metrics_done and flops_done:
            tail = await _terminal_tail(pilot, state_path, ctx, expected)
            ctx.meta["dispatch_state"] = _read_dispatch_state(state_path)
            ctx.meta["completion"]["terminal_tail"] = tail
            ctx.meta["completion"]["completed"] = True
            if not tail["quiesced"]:
                ctx.note(
                    "completion predicate met but the terminal tail did "
                    f"not quiesce within 600s (status={tail['status']!r},"
                    f" trainer_state={tail['trainer_state']}) — honest "
                    "observation; the artifacts are the authority")
            await settle(app, pilot, rounds=3)
            await asyncio.sleep(6.0)
            await ctx.export(pilot, app, "999_monitor_done")
            return

        failures_present = (ctx.root / "sweep_failures.json").is_file()
        if probe_absent and (not metrics_done or not flops_done) and (
                failures_present
                or status in _DISPATCH_TERMINAL_BAD
                or status == _DISPATCH_TERMINAL_OK):
            ctx.meta["dispatch_state"] = _read_dispatch_state(state_path)
            raise DriverError(
                f"the sweep ended without the expected artifacts "
                f"(probe_absent={probe_absent}, expected="
                f"{present_count}/seed, final_metrics={metrics}, "
                f"flops={flops}, dispatch_status={status!r}, "
                f"sweep_failures.json={failures_present}) — honest "
                "failure; the sweep is never killed")

        if deadline is not None and time.monotonic() >= deadline:
            ctx.meta["dispatch_state"] = _read_dispatch_state(state_path)
            raise DriverError(
                f"overall timeout ({float(ctx.args.timeout):.0f}s) with "
                f"probe_absent={probe_absent}, final_metrics={metrics}, "
                f"flops={flops}, dispatch_status={status!r} — the sweep "
                "SURVIVES detached; see the re-attach section")

        signature = (
            state_path.stat().st_mtime_ns if state_path.exists() else 0,
            tuple(sorted(metrics.items())),
            tuple(sorted(flops.items())),
            _max_mtime(ctx.root),
            _tee_size(),
        )
        if stall.observe(signature):
            ctx.note(
                f"run stall: no dispatch_state/artifact/root-file/tee "
                f"change for {float(ctx.args.stall_hours):.1f}h "
                f"(digest={signature[:2]})")
            if not stall_captured:
                await ctx.export(pilot, app, "997_monitor_stall")
                stall_captured = True
            if ctx.args.exit_on_stall:
                raise DriverError(
                    "run stalled (--exit-on-stall) — the sweep SURVIVES "
                    "detached; see the re-attach section")


# =====================================================================
# The full-mode auto report (REPORT.md from the run's own artifacts)
# =====================================================================


def _yaml_epochs_default() -> str:
    """The effective epoch count the epochs-less launch defers to (the
    finetune_config.yaml num_train_epochs; '?' when unreadable)."""
    try:
        text = FINETUNE_CONFIG_YAML.read_text(encoding="utf-8")
    except OSError:
        return "?"
    match = re.search(r"^\s*num_train_epochs:\s*(\S+)", text, re.MULTILINE)
    return match.group(1) if match else "?"


def _read_json(path: Path) -> dict | None:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


def _cell_rows(ctx: RunContext) -> list[dict]:
    """Walk the run root's per-cell artifacts (the model x task x seed
    matrix) — every row from an actually-run execution."""
    rows: list[dict] = []
    tasks = sorted(ctx.meta["present_set"] or [])
    for task in tasks:
        for seed in FULL_SEEDS:
            cell = ctx.root / FULL_MODEL / task / f"seed_{seed}"
            metrics = _read_json(cell / "final_metrics.json")
            flops = _read_json(cell / "flops_report.json")
            hardware = (flops or {}).get("hardware")
            hardware = hardware if isinstance(hardware, dict) else {}
            rows.append({
                "task": task,
                "seed": seed,
                "metrics": metrics,
                "train_runtime": (metrics or {}).get("train_runtime"),
                "flops_G": (flops or {}).get("total_flops_G"),
                "gpu_device": hardware.get("gpu_device"),
            })
    return rows


def _fmt(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _render_report(ctx: RunContext) -> str:
    """The auto-generated REPORT.md — from the run's own meta + on-disk
    artifacts ONLY (the pa6 _render_record discipline: every number
    traces to an actually-run execution; absent cells say absent)."""
    meta = ctx.meta
    present = list(meta["present_set"] or [])
    expected = int(meta["expected_cells"] or 0)
    epochs = _yaml_epochs_default()
    ledger_doc = _read_json(Path(ctx.args.ledger)) or {}
    lines: list[str] = []
    lines.append(
        "# TUI-driven FungiHelixSeek full sweep — operation report "
        "(quick-261022-tah)")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Date: `{meta['started_at']}` (UTC) — mode: "
                 f"**{meta['mode']}**")
    lines.append(f"- Host: `{meta['host']}` — GPUs: "
                 f"`{meta.get('gpu_names') or 'n/a'}`")
    lines.append(f"- What ran: {FULL_MODEL} x {len(present)} present "
                 f"datasets x seeds {FULL_SEEDS_TEXT} "
                 f"(workers={FULL_WORKERS_TEXT}, gpus={FULL_GPUS_TEXT}) "
                 f"— {expected} cells expected")
    lines.append(f"- Epochs: **{epochs}** from the YAML default "
                 "(`pipeline/finetune_config.yaml`) — NO override was "
                 "typed at the gate (the [p] argv asserted "
                 "`--num_train_epochs` ABSENT; the epochs input read "
                 f"`{meta.get('epochs_input_value')!r}` at launch)")
    lines.append(f"- Output root: `{meta['root_resolved']}` (fresh — no "
                 "trainer_state markers could skip cells)")
    lines.append(f"- TUI state dir (kept; holds the queue state + logs "
                 f"+ tee): `{meta['state_dir']}`")
    lines.append(f"- Driver exit code: **{meta['exit_code']}**"
                 + (f" — failure: {meta['failure']}" if meta["failure"]
                    else ""))
    lines.append("")
    lines.append("Every number in this report derives from the run's own "
                 "meta (`docs/live/fhs/evidence.json`), the download "
                 "ledger, and the on-disk cell artifacts — evidence from "
                 "the actually-run execution.")
    lines.append("")

    lines.append("## Download ledger")
    lines.append("")
    queue_rows = ledger_doc.get("queue_entries")
    if isinstance(queue_rows, list) and queue_rows:
        lines.append("| Key | Kind | Final state | Attempts | Problems | "
                     "Duration |")
        lines.append("|---|---|---|---|---|---|")
        for raw in queue_rows:
            if not isinstance(raw, dict):
                continue
            started = raw.get("started_at")
            finished = raw.get("finished_at")
            if isinstance(started, str) and isinstance(finished, str):
                duration = f"{started} .. {finished}"
            else:
                duration = "-"
            problems = raw.get("problems")
            lines.append(
                f"| {raw.get('key')} | {raw.get('kind')} "
                f"| {raw.get('state')} | {raw.get('attempts')} "
                f"| {', '.join(problems) if problems else '-'} "
                f"| {duration} |")
    else:
        lines.append("- (no queue entries — the rehearsal carries no "
                     "downloads)")
    not_enqueued = ledger_doc.get("not_enqueued")
    if isinstance(not_enqueued, list) and not_enqueued:
        lines.append("")
        lines.append("Not-enqueued official keys (the honest skip ledger):")
        lines.append("")
        lines.append("| Key | Channel | Reason |")
        lines.append("|---|---|---|")
        for raw in not_enqueued:
            if isinstance(raw, dict):
                lines.append(
                    f"| {raw.get('key')} | {raw.get('channel')} "
                    f"| {raw.get('reason') or '-'} |")
    before = ledger_doc.get("present_before_download")
    if isinstance(before, list):
        lines.append("")
        lines.append(f"- Already present BEFORE the downloads "
                     f"({len(before)}): {', '.join(sorted(before)) or '-'}")
    lines.append("")

    lines.append("## Run matrix summary")
    lines.append("")
    lines.append(f"- 1 model ({FULL_MODEL}) x {len(present)} present "
                 f"datasets x {len(FULL_SEEDS)} seeds = "
                 f"**{expected} expected cells**")
    lines.append(f"- Present set (the actually-downloaded present set, "
                 f"derived through the picker's own chain): "
                 f"{len(present)} keys")
    lines.append("")
    cells = _cell_rows(ctx)
    landed = [row for row in cells if row["metrics"] is not None]
    lines.append(f"- Cells with final_metrics.json on disk at report "
                 f"time: {len(landed)} / {expected}")
    lines.append("")

    lines.append("## Per-dataset x seed results")
    lines.append("")
    if cells:
        lines.append("| Dataset | Seed | eval_f1 | eval_accuracy | "
                     "eval_mcc | train_runtime (s) | FLOPs (G) | GPU |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for row in cells:
            metrics = row["metrics"] or {}
            marker = "" if row["metrics"] is not None else " (absent)"
            lines.append(
                f"| {row['task']}{marker} | {row['seed']} "
                f"| {_fmt(metrics.get('eval_f1'))} "
                f"| {_fmt(metrics.get('eval_accuracy'))} "
                f"| {_fmt(metrics.get('eval_mcc'))} "
                f"| {_fmt(row['train_runtime'])} "
                f"| {_fmt(row['flops_G'])} "
                f"| {row['gpu_device'] or '-'} |")
    else:
        lines.append("- (no cells on disk yet)")
    lines.append("")

    lines.append("## Failure / skip ledger")
    lines.append("")
    failures: list[str] = []
    for raw in queue_rows if isinstance(queue_rows, list) else []:
        if isinstance(raw, dict) and raw.get("state") not in (
                "done", None):
            problems = raw.get("problems")
            failures.append(
                f"- download {raw.get('key')}: {raw.get('state')} "
                f"(problems: {', '.join(problems) if problems else '-'})")
    absent_cells = [row for row in cells if row["metrics"] is None]
    for row in absent_cells:
        failures.append(
            f"- cell {row['task']} / seed {row['seed']}: no "
            "final_metrics.json (not run or failed — see the dispatch "
            "ledger under the root)")
    if (ctx.root / "sweep_failures.json").is_file():
        marker = ctx.root / "sweep_failures.json"
        failures.append(f"- sweep_failures.json present: {marker}")
    lines.extend(failures if failures
                 else ["- (none recorded)"])
    lines.append("")

    lines.append("## GPU utilization summary (per-interval snapshots)")
    lines.append("")
    snaps = meta["nvidia_snapshots"]
    if snaps:
        both_busy = sum(
            1 for snap in snaps
            if len([line for line in snap["compute_apps"].splitlines()
                    if line.strip()]) >= 2)
        lines.append(f"- {len(snaps)} snapshots; both GPUs busy in "
                     f"{both_busy} (compute apps >= 2 — honest about the "
                     "queue-tail idle phases)")
        for snap in (snaps[:2] + snaps[-2:] if len(snaps) > 4
                     else snaps):
            lines.append(f"- `{snap['at']}` query-gpu: "
                         f"`{snap['query']}` — compute apps: "
                         f"`{snap['compute_apps']}`")
    else:
        lines.append("- (none captured — the run did not reach the watch "
                     "loop)")
    lines.append("")

    lines.append("## Journey stage timings")
    lines.append("")
    lines.append("| Stage | At (UTC) | Elapsed (s) |")
    lines.append("|---|---|---|")
    for name, stamp in meta["stages"].items():
        lines.append(f"| {name} | {stamp['at']} | "
                     f"{stamp['elapsed_s']} |")
    lines.append("")

    lines.append("## Honest notes")
    lines.append("")
    for note in meta["notes"]:
        lines.append(f"- {note}")
    if meta.get("failure"):
        lines.append(f"- FAILURE: {meta['failure']}")
    lines.append("")

    lines.append("## Re-attach instructions")
    lines.append("")
    lines.append("The sweep is NEVER killed by the driver — if it is "
                 "still alive it survives detached in its own session:")
    lines.append("")
    lines.append(f"- TUI: slot 5, press `a`, type `{meta['root_resolved']}`")
    lines.append(f"- CLI: `cat {meta['root_resolved']}/dispatch_state.json`")
    if meta.get("tee_path"):
        lines.append(f"- Log tail: `tail -f {meta['tee_path']}`")
    lines.append("- Live view: `nvidia-smi`")
    lines.append("")
    return "\n".join(lines)


def _write_report(ctx: RunContext) -> None:
    """Write REPORT.md unless the completion path already wrote it (the
    draft/final distinction is the meta's completion + exit_code, carried
    inside the report itself)."""
    if ctx.meta.get("report_written"):
        return
    try:
        report = Path(ctx.args.report)
        _atomic_write(report, _render_report(ctx))
        ctx.meta["report_path"] = str(report)
        ctx.meta["report_written"] = True
        print(f"[out] report: {report}", flush=True)
    except OSError as exc:
        ctx.note(f"report write failed: {exc!r}")


async def _run_attach_watch(pilot: Pilot, app: DnallmMarkTui,
                            ctx: RunContext) -> None:
    """The --attach-root recovery lane: the sweep was already launched
    (typically by a journey driver that died post-launch); THIS driver
    instance only WATCHES it — slot 5, the monitor card/attach, then the
    standard multi-day run watch. It never spawns anything and never
    touches the sweep."""
    ledger_doc = _read_json(Path(ctx.args.ledger))
    present = (ledger_doc or {}).get("present_set")
    expected = (ledger_doc or {}).get("expected_cells")
    state_path = ctx.root / "dispatch_state.json"
    if not isinstance(present, list) or not present:
        # fallback: derive per-seed from the orchestrator's own total
        state = _read_dispatch_state(state_path) or {}
        counts = state.get("counts")
        total = counts.get("total") if isinstance(counts, dict) else None
        if not isinstance(total, int) or total <= 0:
            raise DriverError(
                "cannot derive the expected matrix for the attach watch "
                f"(ledger {ctx.args.ledger} carries no present_set and "
                f"dispatch_state total is {total!r}) — honest halt")
        expected = total
        ctx.note(
            f"attach watch: present set unknown (no ledger); expected "
            f"cells from dispatch_state.total={total}")
    ctx.meta["present_set"] = sorted(present) if present else None
    ctx.meta["expected_cells"] = expected
    ctx.meta["attach_root"] = str(ctx.root)
    ctx.stage("attach_context_primed")
    await _navigate(pilot, app, "5", MonitorScreen,
                    "slot-5 navigation (attach)")
    await watch_run_full(pilot, app, ctx)


# =====================================================================
# The recording runner
# =====================================================================


async def _recording(args: argparse.Namespace, targets: dict,
                     state_dir: Path) -> int:
    """One spawned recording: the real app over the fresh state dir."""
    ctx = RunContext(args, targets, state_dir)
    app = DnallmMarkTui()
    failure: str | None = None
    launched = False
    try:
        async with app.run_test(size=GRID) as pilot:
            try:
                if ctx.attach:
                    await _run_attach_watch(pilot, app, ctx)
                    _write_report(ctx)
                elif ctx.full:
                    launched = await journey_full(pilot, app, ctx)
                    if launched:
                        await watch_run_full(pilot, app, ctx)
                        _write_report(ctx)
                else:
                    launched = await journey(pilot, app, ctx)
                    if launched:
                        await watch_to_completion(pilot, app, ctx)
                        await settle(app, pilot, rounds=3)
                        await asyncio.sleep(6.0)  # the 2s cadence refresh
                        await ctx.export(pilot, app, "99_monitor_done")
            except GateRefusedError as exc:
                failure = str(exc)
            except DriverError as exc:
                failure = str(exc)
                try:
                    await ctx.export(
                        pilot, app,
                        "998_monitor_failure" if ctx.full
                        else "98_monitor_failure")
                except Exception:  # noqa: BLE001, S110 — record still lands
                    pass
    except Exception as exc:  # noqa: BLE001 — the harness-level catch
        failure = failure or f"harness error: {exc!r}"

    ctx.meta["exit_code"] = 1 if failure else 0
    ctx.meta["launched"] = launched
    if failure:
        ctx.meta["failure"] = failure
    if ctx.full:
        _write_report(ctx)  # best-effort draft on every non-final path
    elif launched and not failure:
        _attach_completion_evidence(ctx)
    _write_outputs(ctx)
    return 1 if failure else 0


def _attach_completion_evidence(ctx: RunContext) -> None:
    """Run the exact-path verification commands (repo-root-relative) and
    paste their verbatim outputs into the meta — the RECORD's completion
    rows derive from THESE, never from narration."""
    rel_root = ctx.root.relative_to(REPO_ROOT)
    commands = [
        f"find {rel_root} -path '*seed_42/final_metrics.json' | sort",
        f"find {rel_root} -path '*seed_42/flops_report.json' | wc -l",
        f"find {rel_root} -path '*seed_42/trainer_state.json' | wc -l",
    ]
    outputs: list[dict] = []
    for command in commands:
        result = subprocess.run(
            ["bash", "-c", command], cwd=str(REPO_ROOT),
            capture_output=True, text=True, check=False)
        outputs.append({
            "command": command,
            "stdout": result.stdout.strip(),
            "exit": result.returncode,
        })
    ctx.meta["completion_commands"] = outputs


def _write_outputs(ctx: RunContext) -> None:
    """Write evidence.json always; the RECORD.md draft for pa6 live
    runs (full mode's report is written by _write_report)."""
    evidence = Path(ctx.args.evidence)
    _atomic_write(
        evidence, json.dumps(ctx.meta, indent=2, ensure_ascii=False))
    print(f"[out] evidence: {evidence}", flush=True)
    if ctx.rehearsal or ctx.full:
        return
    record = Path(ctx.args.record)
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(_render_record(ctx), encoding="utf-8")
    print(f"[out] record: {record}", flush=True)


def _render_record(ctx: RunContext) -> str:
    """The RECORD.md draft, generated from the run's own meta only."""
    meta = ctx.meta
    lines: list[str] = []
    lines.append(
        "# Live 2x2 dual-GPU TUI run — operation record (quick-261022-pa6)")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Date: `{meta['started_at']}` (UTC) — mode: "
                 f"**{meta['mode']}**")
    lines.append(f"- Host: `{meta['host']}` — GPUs: "
                 f"`{meta.get('gpu_names') or 'n/a'}`")
    lines.append(f"- What ran: {len(MODELS)} models x {len(TASKS)} tasks "
                 f"x seed {SEEDS_TEXT} x {EPOCHS_TEXT} epoch(s), "
                 f"workers={WORKERS_TEXT}, gpus={GPUS_TEXT} — "
                 f"{EXPECTED_CELLS} cells expected")
    lines.append(f"- Models: {', '.join(MODELS)}")
    lines.append(f"- Tasks: {', '.join(TASKS)}")
    lines.append(f"- Output root: `{meta['root_resolved']}` "
                 "(fresh — no trainer_state markers could skip cells)")
    lines.append(f"- TUI state dir (kept; holds the tee log): "
                 f"`{meta['state_dir']}`")
    lines.append(f"- Driver exit code: **{meta['exit_code']}**"
                 + (f" — failure: {meta['failure']}" if meta["failure"]
                    else ""))
    lines.append("")
    lines.append("Every number in this record derives from the run's own "
                 "meta (`docs/live/evidence.json`) and from commands run "
                 "against the on-disk artifacts — evidence from the "
                 "actually-run execution.")
    lines.append("")
    lines.append("## Journey stage timings")
    lines.append("")
    lines.append("| Stage | At (UTC) | Elapsed (s) |")
    lines.append("|---|---|---|")
    for name, stamp in meta["stages"].items():
        lines.append(f"| {name} | {stamp['at']} | "
                     f"{stamp['elapsed_s']} |")
    lines.append("")
    lines.append("## Launch evidence")
    lines.append("")
    lines.append("- The launch went through the REAL gate: the y key on "
                 "the confirm face -> `LauncherBackend.launch_spec` -> "
                 "`run_config.compose_dispatch_argv` -> "
                 "`SweepLauncher._spawn` (start_new_session=True, cwd "
                 "pinned to pipeline/, tee under the state dir's logs/).")
    if meta.get("argv_line"):
        lines.append("- Dispatch argv (the [p] preview, verbatim):")
        lines.append("")
        lines.append("  ```")
        lines.append(f"  {meta['argv_line']}")
        lines.append("  ```")
    lines.append(f"- Tee log: `{meta.get('tee_path')}`")
    if isinstance(meta.get("dispatch_state"), dict):
        state = meta["dispatch_state"]
        lines.append(f"- dispatch_state.json summary: status="
                     f"`{state.get('status')}`, run_id="
                     f"`{state.get('run_id')}`")
    lines.append("")
    lines.append("## GPU evidence (per-interval nvidia-smi snapshots)")
    lines.append("")
    if meta["nvidia_snapshots"]:
        for snap in meta["nvidia_snapshots"]:
            lines.append(f"- `{snap['at']}` query-gpu: "
                         f"`{snap['query']}` — compute apps: "
                         f"`{snap['compute_apps']}`")
    else:
        lines.append("- (none captured — the run did not reach the watch "
                     "loop)")
    lines.append("")
    lines.append("## Completion verification")
    lines.append("")
    completion = meta.get("completion") or {}
    lines.append(f"- /proc probe (read-only `probe_cli_sweeps`) reports "
                 f"no live worker for the root: "
                 f"`{completion.get('probe_absent')}`")
    for entry in meta.get("completion_commands", []):
        lines.append("")
        lines.append("  ```bash")
        lines.append(f"  $ {entry['command']}")
        for line in entry["stdout"].splitlines():
            lines.append(f"  {line}")
        lines.append("  ```")
    if not meta.get("completion_commands"):
        lines.append("- (verification commands not run — see the failure "
                     "line above)")
    lines.append("")
    lines.append("## Honest notes")
    lines.append("")
    lines.append("- The committed SVG stages 01-06 come from THIS "
                 "launching run; the `--no-launch` rehearsal that "
                 "de-risked the choreography ran earlier against the real "
                 "app with zero GPU work and its captures were "
                 "overwritten, never committed.")
    if meta.get("failure"):
        lines.append(f"- FAILURE: {meta['failure']}")
    for note in meta["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    lines.append("## Re-attach instructions")
    lines.append("")
    lines.append("The sweep is NEVER killed by the driver — if it is "
                 "still alive it survives detached in its own session:")
    lines.append("")
    lines.append(f"- TUI: slot 5, press `a`, type `{meta['root_resolved']}`")
    lines.append(f"- CLI: `cat {meta['root_resolved']}/dispatch_state.json`")
    if meta.get("tee_path"):
        lines.append(f"- Log tail: `tail -f {meta['tee_path']}`")
    lines.append("- Live view: `nvidia-smi`")
    lines.append("")
    return "\n".join(lines)


# =====================================================================
# CLI
# =====================================================================


def _dry_run(args: argparse.Namespace) -> int:
    """Print the journey timeline + resolved targets. No app spawn, no
    preflight side effects (the record_tui_demo --dry-run discipline)."""
    if args.mode == MODE_FULL:
        return _dry_run_full(args)
    root_resolved = (REPO_ROOT / Path(args.root)).resolve()
    stages = [
        ("01_boot_env_check",
         "boot env screen verdict (<=300s cold kernels)", "export"),
        ("02_picker_models",
         f"slot-4 nav; filter+tab+space marks x {len(MODELS)}", "export"),
        ("03_picker_datasets",
         f"m flip; filter marks x {len(TASKS)}", "export"),
        ("04_run_config_params",
         f"params seeds={SEEDS_TEXT} epochs={EPOCHS_TEXT} workers={WORKERS_TEXT} gpus={GPUS_TEXT} root={args.root}; preview line 2x2x1=4",
         "export"),
        ("05_run_config_preview",
         "p modal; dispatch argv assertions", "export"),
        ("06_run_config_confirm",
         "enter -> Y/N gate; dispatch-plan line 0,1", "export"),
        ("launch",
         f"y -> real run_sweep_shard --mode dispatch --workers {WORKERS_TEXT} --gpus {GPUS_TEXT}",
         "live only"),
        (f"07_monitor_running_NN (every {args.interval:.0f}s)",
         "nvidia-smi snapshot + monitor capture + completion poll",
         "live only"),
        ("99_monitor_done",
         "probe absent + 4x final_metrics + 4x flops_report", "live only"),
        ("98_monitor_failure",
         "honest failure capture (timeout/cells)", "on failure"),
    ]
    print(f"mode={'rehearsal' if args.no_launch else 'live'} "
          f"grid={GRID[0]}x{GRID[1]}")
    print(f"models={MODELS} tasks={TASKS}")
    print(f"seeds={SEEDS_TEXT} epochs={EPOCHS_TEXT} "
          f"workers={WORKERS_TEXT} gpus={GPUS_TEXT} "
          f"cells={EXPECTED_CELLS}")
    print(f"root={args.root} -> {root_resolved}")
    print(f"state-base={args.state_base} svg-dir={args.svg_dir} "
          f"record={args.record} evidence={args.evidence}")
    print(f"interval={args.interval}s timeout={args.timeout}s")
    print(f"{len(stages)} stages:")
    for index, (name, what, when) in enumerate(stages, start=1):
        print(f"  {index:2d}. {name:34s} {when:11s} {what}")
    return 0


def _dry_run_full(args: argparse.Namespace) -> int:
    """The full-mode timeline: the download journey, the multi-day run
    posture, and the honest scale projection — zero spawn."""
    root_resolved = (REPO_ROOT / Path(args.root)).resolve()
    try:
        datasets_info = json.loads(
            DATASETS_INFO.read_text(encoding="utf-8"))
        dataset_count = len(datasets_info)
    except (OSError, ValueError):
        dataset_count = -1
    stages = [
        ("001_boot_env_check",
         "boot env screen verdict (<=300s cold kernels)", "export"),
        ("002_model_row_missing",
         (f"slot-2 nav; filter+cursor-walk onto {FULL_MODEL} "
          "(rehearsal: locate only)"), "export"),
        ("003_model_enqueued",
         "d -> real KIND_MODEL queue lane (queue state file asserted)",
         "live only"),
        ("004_data_presence_before",
         ("slot-3 nav; PRIMARY full presence view (rehearsal: render "
          "only)"), "export"),
        ("005_data_enqueue_all",
         "a -> enqueue_all_missing (count recorded)", "live only"),
        (f"006_download_running_NNN (every {args.dl_interval:.0f}s)",
         ("queue digest + newest log size + capture; settle = no "
          "pending/downloading on two reads >= 60s apart + model "
          "terminal"), "live only"),
        ("007_download_settled_queue",
         ("settled queue + v-toggled missing view + 008 final presence "
          "+ 009 queue detail drill-down"), "live only"),
        ("download_ledger.json",
         ("per-key outcomes + not-enqueued reasons + present set "
          "-> expected cells = present x 3"), "live only"),
        ("010_wizard_model_marked",
         f"slot-4; filter mark {FULL_MODEL}", "export"),
        ("011_wizard_datasets_marked",
         "m flip; filter mark EVERY present-set key", "export"),
        ("012_run_config_params",
         (f"seeds={FULL_SEEDS_TEXT} workers={FULL_WORKERS_TEXT} "
          f"gpus={FULL_GPUS_TEXT} root={args.root}; epochs NEVER "
          "touched (YAML default governs; input read + recorded)"),
         "export"),
        ("013_run_config_preview",
         "p modal; argv tokens asserted; --num_train_epochs ABSENT",
         "export"),
        ("014_run_config_confirm",
         "enter -> Y/N gate; dispatch-plan line 0,1", "export"),
        ("launch",
         ("y -> real run_sweep_shard --mode dispatch --workers "
          f"{FULL_WORKERS_TEXT} --gpus {FULL_GPUS_TEXT} --seeds "
          f"{FULL_SEEDS_TEXT}"), "live only"),
        (f"015_monitor_running_NNN (every {args.interval:.0f}s)",
         ("gpu snapshot + dispatch digest + per-seed artifact counts + "
          "heartbeat; completion = probe absent + present-count per "
          "seed for BOTH artifacts"), "live only"),
        ("999_monitor_done",
         ("terminal tail (status completed + trainer_state == expected,"
          " <=600s) + auto REPORT.md"), "live only"),
        ("997_monitor_stall / 998_monitor_failure",
         ("honest degradation captures (stall detector / failure end); "
          "the sweep is NEVER killed"), "on degradation"),
    ]
    print(f"mode={'full-rehearsal' if args.no_launch else 'full'} "
          f"grid={GRID[0]}x{GRID[1]}")
    print(f"model={FULL_MODEL} seeds={FULL_SEEDS_TEXT} "
          f"epochs=<yaml default, never typed> "
          f"workers={FULL_WORKERS_TEXT} gpus={FULL_GPUS_TEXT}")
    if getattr(args, "param_specs", ()):
        print("advanced-params=" + " ".join(
            f"{row.flag}={_param_argv_token(row, value)}"
            for row, value in args.param_specs)
            + " (typed/picked on the slot-4 advanced section; the [p] "
            "assertion REQUIRES each pair present and every untouched "
            "table flag ABSENT)")
    print(f"registry datasets={dataset_count} (present set derived at "
          "download settle; matrix = present x 3)")
    print(f"root={args.root} -> {root_resolved}")
    print(f"state-base={args.state_base} (prefix {FULL_STATE_PREFIX}) "
          f"svg-dir={args.svg_dir}")
    print(f"evidence={args.evidence} (incremental heartbeat) "
          f"ledger={args.ledger} report={args.report}")
    print(f"dl-interval={args.dl_interval}s interval={args.interval}s "
          f"stall-hours={args.stall_hours}s "
          f"exit-on-stall={bool(args.exit_on_stall)} "
          f"timeout={args.timeout}s (0 = no hard deadline; the stall "
          "detector governs)")
    print("scale honesty: pa6 actuals (4 cells, ~90M models, 1 epoch, "
          "55 min) project an optimistic floor ~3 days and a realistic "
          "5-10+ days at 263M x 3 epochs over up to ~46 datasets "
          "(BEND-class cells dominate); the executor closes the task "
          "in-flight and the driver outlives it.")
    print(f"{len(stages)} stages:")
    for index, (name, what, when) in enumerate(stages, start=1):
        print(f"  {index:2d}. {name:44s} {when:13s} {what}")
    return 0


def _fill_mode_defaults(args: argparse.Namespace) -> None:
    """Fill every mode-dependent default (explicit flags always win);
    the pa6 table reproduces the committed pa6 defaults exactly."""
    table = _MODE_DEFAULTS[args.mode]
    for name, value in table.items():
        if getattr(args, name, None) is None:
            setattr(args, name, value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="The live TUI SVG recording driver (Pilot lane).")
    parser.add_argument("--mode", choices=(MODE_PA6, MODE_FULL),
                        default=MODE_PA6,
                        help="journey profile: pa6 (the committed 2x2 "
                             "combo, default) or full (the FungiHelixSeek "
                             "download + multi-day production journey)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the journey timeline without spawning")
    parser.add_argument("--no-launch", action="store_true",
                        help="full rehearsal: drive to the gate, capture, "
                             "press n — zero GPU work (full mode also "
                             "enqueues nothing: locate/render only)")
    parser.add_argument("--attach-root", default=None,
                        help="full mode: ATTACH to an already-running "
                             "sweep root (post-launch watch only — "
                             "monitor card + interval captures + "
                             "auto-report; never spawns anything; "
                             "requires --mode full)")
    parser.add_argument("--root", default=None,
                        help="the fresh sweep output root (pa6 default: "
                             "pipeline/finetuned-tui-pa6; full default: "
                             "pipeline/finetuned-fhs-full)")
    parser.add_argument("--state-base",
                        default="/root/autodl-tmp/dnallmmark-data/tui-live",
                        help="the data-disk base for the fresh per-"
                             "recording TUI state dir")
    parser.add_argument("--svg-dir", default=None,
                        help="where the stage SVGs land (pa6 default: "
                             "docs/live/svg; full default: "
                             "docs/live/fhs/svg)")
    parser.add_argument("--record", default=None,
                        help="the operation record path (pa6 live mode; "
                             "pa6 default: docs/live/RECORD.md)")
    parser.add_argument("--evidence", default=None,
                        help="the machine-readable meta sidecar (full "
                             "mode writes it INCREMENTALLY; defaults per "
                             "mode)")
    parser.add_argument("--report", default=None,
                        help="full mode: the auto-generated REPORT.md "
                             "(default: docs/live/fhs/REPORT.md)")
    parser.add_argument("--ledger", default=None,
                        help="full mode: the download ledger written at "
                             "settle (default: "
                             "docs/live/fhs/download_ledger.json)")
    parser.add_argument("--dl-interval", type=float, default=None,
                        help="full mode: download-phase capture cadence "
                             "in seconds (default: 600)")
    parser.add_argument("--interval", type=float, default=None,
                        help="watch-loop cadence in seconds (pa6 default: "
                             "180; full default: 1800)")
    parser.add_argument("--stall-hours", type=float, default=6.0,
                        help="full mode: stall threshold in hours with "
                             "zero liveness signal (default: 6)")
    parser.add_argument("--exit-on-stall", action="store_true",
                        help="full mode: exit nonzero on stall (default: "
                             "record honestly and keep watching)")
    parser.add_argument("--timeout", type=float, default=None,
                        help="overall live-run deadline in seconds (pa6 "
                             "default: 5400; full default: 0 = NO hard "
                             "deadline — the stall detector governs)")
    parser.add_argument(
        "--batch-text", default="",
        help="full mode: a positive integer typed into the batch input "
             "row — the [p] argv assertion then REQUIRES --batch_size "
             "<value> (the STARTING per-device batch). Default '' NEVER "
             "touches the batch input (the epochs discipline; the argv "
             "asserts --batch_size ABSENT)")
    parser.add_argument(
        "--param", action="append", default=[], metavar="NAME=VALUE",
        help="full mode (repeatable): an advanced train param typed/"
             "picked on the slot-4 advanced section — NAME must be an "
             "ADVANCED_TRAIN_FLAGS flag name (pipeline/run_sweep.py is "
             "the vocabulary); Input kinds are typed, enum/bool kinds "
             "are picked through the real modal; the [p] argv assertion "
             "REQUIRES each typed flag present with its value while "
             "every UNTOUCHED table flag stays ABSENT")
    args = parser.parse_args(argv)
    if args.attach_root and args.mode != MODE_FULL:
        parser.error("--attach-root requires --mode full")
    if args.batch_text:
        if args.mode != MODE_FULL:
            parser.error("--batch-text requires --mode full")
        if not args.batch_text.isdigit() or int(args.batch_text) < 1:
            parser.error(
                "--batch-text must be a positive integer (a typed "
                "STARTING per-device batch), got "
                f"{args.batch_text!r}")
    # 19-03: the --param channel validates against the frozen table AT
    # PARSE (unknown names / out-of-vocabulary values never spawn an
    # app) and is full-mode-only — the --batch-text lane discipline.
    if args.param:
        if args.mode != MODE_FULL:
            parser.error("--param requires --mode full")
        try:
            args.param_specs = _parse_param_args(args.param)
        except ValueError as exc:
            parser.error(str(exc))
    else:
        args.param_specs = ()
    _fill_mode_defaults(args)

    if args.dry_run:
        return _dry_run(args)

    try:
        targets = preflight(args)
    except PreflightError as exc:
        print(f"[preflight] HALT: {exc}", file=sys.stderr, flush=True)
        return 2

    state_base = Path(args.state_base)
    state_base.mkdir(parents=True, exist_ok=True)
    prefix = FULL_STATE_PREFIX if args.mode == MODE_FULL else \
        "tui-live-pa6-"
    state_dir = Path(tempfile.mkdtemp(prefix=prefix, dir=state_base))
    # Set BEFORE constructing the app: the launcher tee, run_config.json,
    # monitor_roots, and the download queue state all land under this
    # root (the disk policy keeps it on the data disk). KEPT on every
    # path — it holds the tee log + queue evidence.
    os.environ["DNALLMMARK_TUI_STATE_DIR"] = str(state_dir)
    print(f"[setup] state dir: {state_dir}", flush=True)
    print(f"[setup] root: {targets['root_resolved']} "
          f"(rehearsal={args.no_launch})", flush=True)

    return asyncio.run(_recording(args, targets, state_dir))


if __name__ == "__main__":
    raise SystemExit(main())
