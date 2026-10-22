"""
record_tui_live_svg.py — the live TUI SVG recording driver (quick-261022-pa6).

Drives the REAL operator console (``DnallmMarkTui``, zero injected services)
through the proven 2x2 dual-GPU journey — boot env check -> slot-4 picker
marks -> m-flip dataset marks -> params (seeds 42, 1 epoch, workers 2, GPUs
0,1, fresh output root) -> live preview line -> [p] dispatch argv preview ->
the Y/N gate -> the real dispatch launch -> the monitor through completion —
exporting every stage as a design-grid (120x40) SVG screenshot plus an
honest operation record (RECORD.md + evidence.json) generated from the
run's own meta.

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
  launcher tee, run_config.json, and monitor_roots land there. The REAL
  config root stays live (directories.json wiring + customs render);
  ``DNALLMMARK_TUI_CONFIG_DIR`` is never set. The temp state dir is KEPT
  on every path (it holds the tee log — evidence) and recorded in the
  meta.
- MODES: ``--dry-run`` prints the journey timeline + resolved targets with
  zero app spawn and zero preflight side effects; ``--no-launch`` is the
  full rehearsal (real app, real registries, drive to the gate, capture
  stages 01-06, press ``n`` at the confirm — zero GPU work); the default
  is the LIVE mode (real launch + completion poll). The dnallm-import and
  GPU-idle preflight legs run only in live mode.
- DISPLAY-ONLY /proc evidence: completion polling reuses the repo's own
  ``tui.services.sweep_launcher.probe_cli_sweeps`` (read-only cmdline
  reads of this host's process table). The driver NEVER signals any
  process: on timeout or failure the sweep SURVIVES detached in its own
  session and the record documents how to reach it. No fabricated
  success: a failed or timed-out run exports the failure-state capture,
  records exactly what was observed, and exits nonzero.

Usage:
    python scripts/live/record_tui_live_svg.py --dry-run
    python scripts/live/record_tui_live_svg.py --no-launch
    python scripts/live/record_tui_live_svg.py [--interval 180] [--timeout 5400]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# The tui/__main__.py bootstrap idiom: the repo root (for package-qualified
# tui imports) and REPO_ROOT/pipeline (for the top-level pipeline seam
# modules) both land on sys.path BEFORE the tui imports below.
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "pipeline"))

import directories_config  # top-level module (pipeline/ sys.path root)
from rich.text import Text
from textual.containers import Vertical
from textual.pilot import Pilot
from textual.widgets import Input, Label, Static

from tui import strings as S
from tui.app import DnallmMarkTui
from tui.screens.env_check import EnvCheckScreen
from tui.screens.monitor import MonitorScreen
from tui.screens.run_config import (
    EnvBlockModal,
    PickerList,
    PreviewModal,
    ProblemsModal,
    RunConfigScreen,
    _GateConfirmModal,
)
from tui.services import sweep_launcher  # DISPLAY-ONLY /proc probe reuse

# ===== The locked journey combo (presence VERIFIED in preflight) =====

MODELS = ("plant-dnabert-6mer", "plant-dnamamba-6mer")
TASKS = ("GUE__emp_H3", "iDNA_ABF_datasets__5mC")
SEEDS_TEXT = "42"
EPOCHS_TEXT = "1"
WORKERS_TEXT = "2"
GPUS_TEXT = "0,1"

#: The pinned design grid every capture exports at (the golden lane size).
GRID = (120, 40)

#: 2 models x 2 tasks x 1 seed — the completion contract.
EXPECTED_CELLS = 4

#: dispatch_state.json statuses that end the orchestrator's run (the rest
#: of the vocabulary is transient). Language-neutral machine data.
_DISPATCH_TERMINAL_OK = "completed"
_DISPATCH_TERMINAL_BAD = {"failed", "interrupted"}

#: Poll cadence for every bounded wait (seconds).
_POLL_STEP = 0.5

MODELS_INFO = REPO_ROOT / "pipeline" / "models_info.json"
DATASETS_INFO = REPO_ROOT / "pipeline" / "datasets_info.json"


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


def _count_seed_artifacts(root: Path, name: str, seed: str) -> int:
    """Count ``{root}/**/seed_{seed}/{name}`` files (layout-neutral walk)."""
    marker = f"seed_{seed}"
    return sum(1 for path in root.rglob(name)
               if path.parent.name == marker)


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


def preflight(args: argparse.Namespace) -> dict:
    """Verify every precondition the journey assumes.

    The dnallm-import and GPU-idle legs run only in live mode (the plan's
    skip rule); the offline flag, registry presence, fresh-root, and
    writable-path legs run in every spawned mode. Returns the resolved
    targets dict (recorded in the meta + printed by --dry-run consumers).
    """
    live = not args.no_launch
    targets: dict = {"root_arg": args.root}

    if os.environ.get("HF_HUB_OFFLINE") != "1":
        raise PreflightError(
            "HF_HUB_OFFLINE != '1' — the offline discipline is asserted "
            "before anything spawns (docs/multi-gpu.md runbook: export "
            "HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1)")

    if live:
        try:
            import dnallm  # noqa: F401 — import IS the check
        except ImportError as exc:
            raise PreflightError(
                f"import dnallm failed ({exc}) — memory rule: after "
                "uv sync, reinstall dnallm editable from the local dev "
                "clone (../DNALLM): uv pip install -e ../DNALLM") from exc

    # Registry presence through the real consumers' chain: the cards'
    # Model_path/Dataset_path joined on the directories.json-seeded root
    # (default pipeline/), naming EVERY missing key at once.
    try:
        models_info = json.loads(MODELS_INFO.read_text(encoding="utf-8"))
        datasets_info = json.loads(
            DATASETS_INFO.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PreflightError(
            f"official registries unreadable: {exc}") from exc
    dirs = directories_config.load_directories_tolerant()
    model_base = _dir_base(dirs.get("model_root"), REPO_ROOT / "pipeline")
    dataset_base = _dir_base(
        dirs.get("dataset_root"), REPO_ROOT / "pipeline")

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
    try:
        svg_dir.mkdir(parents=True, exist_ok=True)
        probe = svg_dir / ".pa6-write-probe"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
        for path in (Path(args.record), Path(args.evidence)):
            path.parent.mkdir(parents=True, exist_ok=True)
            touch = path.parent / ".pa6-write-probe"
            touch.write_text("", encoding="utf-8")
            touch.unlink()
    except OSError as exc:
        raise PreflightError(
            f"output paths not writable under {svg_dir}/"
            f"{Path(args.record).parent}: {exc}") from exc
    return targets


# =====================================================================
# The run context (meta bookkeeping shared by every stage)
# =====================================================================


class RunContext:
    """One recording's bookkeeping: args, resolved targets, the evidence
    meta, and the monotonic stage clock."""

    def __init__(self, args: argparse.Namespace, targets: dict,
                 state_dir: Path) -> None:
        self.args = args
        self.targets = targets
        self.state_dir = state_dir
        self.svg_dir = Path(args.svg_dir)
        self.root = Path(targets["root_resolved"])
        self.t0 = time.monotonic()
        self.rehearsal = bool(args.no_launch)
        self.meta: dict = {
            "mode": "rehearsal" if self.rehearsal else "live",
            "started_at": _now_iso(),
            "host": platform.node(),
            "root_arg": args.root,
            "root_resolved": str(self.root),
            "state_dir": str(state_dir),
            "grid": list(GRID),
            "models": list(MODELS),
            "tasks": list(TASKS),
            "seeds": SEEDS_TEXT,
            "epochs": EPOCHS_TEXT,
            "workers": WORKERS_TEXT,
            "gpus": GPUS_TEXT,
            "cards": targets.get("cards", {}),
            "gpu_names": targets.get("gpu_names", ""),
            "stages": {},
            "nvidia_snapshots": [],
            "monitor_captures": [],
            "argv_line": None,
            "argv": None,
            "tee_path": None,
            "dispatch_state": None,
            "completion": None,
            "notes": [],
            "rehearsal": self.rehearsal,
            "exit_code": None,
            "failure": None,
        }

    def stage(self, name: str) -> None:
        self.meta["stages"][name] = {
            "at": _now_iso(),
            "elapsed_s": round(time.monotonic() - self.t0, 1)}
        print(f"[{time.monotonic() - self.t0:8.1f}s] stage: {name}",
              flush=True)

    def note(self, text: str) -> None:
        self.meta["notes"].append(text)
        print(f"[{time.monotonic() - self.t0:8.1f}s] note: {text}",
              flush=True)

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
# The journey stages
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
                    await ctx.export(pilot, app, "98_monitor_failure")
                except Exception:  # noqa: BLE001, S110 — the record still lands
                    pass
    except Exception as exc:  # noqa: BLE001 — the harness-level catch
        failure = failure or f"harness error: {exc!r}"

    ctx.meta["exit_code"] = 1 if failure else 0
    if failure:
        ctx.meta["failure"] = failure
    if launched and not failure:
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
    """Write evidence.json always; the RECORD.md draft for live runs."""
    evidence = Path(ctx.args.evidence)
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(
        json.dumps(ctx.meta, indent=2, ensure_ascii=False),
        encoding="utf-8")
    print(f"[out] evidence: {evidence}", flush=True)
    if ctx.rehearsal:
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="The live TUI SVG recording driver (Pilot lane).")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the journey timeline without spawning")
    parser.add_argument("--no-launch", action="store_true",
                        help="full rehearsal: drive to the gate, capture, "
                             "press n — zero GPU work")
    parser.add_argument("--root", default="pipeline/finetuned-tui-pa6",
                        help="the fresh sweep output root (default: "
                             "pipeline/finetuned-tui-pa6)")
    parser.add_argument("--state-base",
                        default="/root/autodl-tmp/dnallmmark-data/tui-live",
                        help="the data-disk base for the fresh per-"
                             "recording TUI state dir")
    parser.add_argument("--svg-dir", default="docs/live/svg",
                        help="where the stage SVGs land")
    parser.add_argument("--record", default="docs/live/RECORD.md",
                        help="the operation record path (live mode)")
    parser.add_argument("--evidence", default="docs/live/evidence.json",
                        help="the machine-readable meta sidecar")
    parser.add_argument("--interval", type=float, default=180.0,
                        help="watch-loop cadence in seconds")
    parser.add_argument("--timeout", type=float, default=5400.0,
                        help="overall live-run deadline in seconds")
    args = parser.parse_args(argv)

    if args.dry_run:
        return _dry_run(args)

    try:
        targets = preflight(args)
    except PreflightError as exc:
        print(f"[preflight] HALT: {exc}", file=sys.stderr, flush=True)
        return 2

    state_base = Path(args.state_base)
    state_base.mkdir(parents=True, exist_ok=True)
    state_dir = Path(tempfile.mkdtemp(prefix="tui-live-pa6-", dir=state_base))
    # Set BEFORE constructing the app: the launcher tee, run_config.json,
    # and monitor_roots all land under this root (the disk policy keeps
    # it on the data disk). KEPT on every path — it holds the tee log.
    os.environ["DNALLMMARK_TUI_STATE_DIR"] = str(state_dir)
    print(f"[setup] state dir: {state_dir}", flush=True)
    print(f"[setup] root: {targets['root_resolved']} "
          f"(rehearsal={args.no_launch})", flush=True)

    return asyncio.run(_recording(args, targets, state_dir))


if __name__ == "__main__":
    raise SystemExit(main())
