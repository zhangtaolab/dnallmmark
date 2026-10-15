"""
record_tui_demo.py — the deterministic TUI demo scene driver (quick-261015-pex).

Drives the REAL operator console (``uv run --group tui --group gpu python -m
tui``) through scripted operator-journey scenes on a real pty, relaying every
byte the console renders verbatim to stdout — under ``asciinema rec`` that
stdout IS the cast; ``agg`` then renders the GIF (``scripts/demo/record.sh``
wraps the chain).

Contract:

- ANCHOR AUTHORITY: every wait-for-text step anchors on a string derived from
  ``tui/strings.py`` constants (resolved per the active scene language) or on
  language-neutral DATA (registry keys, seeds, paths). After any UI copy
  change, re-derive the anchors from ``tui/strings.py`` — never from this
  file's history. This driver NEVER edits ``tui/`` source.
- The console boots in the default English; ``--lang zh`` presses ``L`` on
  camera right after boot (the toggle itself is footage) and restores the
  boot language before the recording ends.
- Each recording spawns the console with a FRESH per-recording
  ``DNALLMMARK_TUI_STATE_DIR`` (deterministic queue/run-spec/env-cache state)
  while the real config root stays live (customs/presets render); any custom
  enabled-flag the demo toggles is restored on camera.
- Real-download and real-training targets are chosen by a LIVE presence scan
  at recording time (registry x disk x ``pipeline/dnllm_compat.json`` for
  models; the committed ``n_audit`` view for datasets) — never hardcoded.
- Scene prep only ever touches the demo-scoped roots (``pipeline/
  finetuned-demo``, ``pipeline/finetuned-demo-fail``) and the exact scanned
  download-target directories — never the real ``pipeline/finetuned`` tree.
- pexpect is imported LAZILY inside the spawn path: ``--dry-run`` and
  ``--list-scenes`` run under plain ``uv run --group dev`` with no pexpect,
  no GPU, no network. The recording invocation pulls it on demand via
  ``uv run --group dev --with pexpect==4.9.0`` (the textual-dev precedent;
  never a committed dependency group).
- Under asciinema the driver's stdout must carry ONLY relayed console bytes:
  all diagnostics go to a per-recording meta JSON sidecar
  (``docs/demo/.meta-<scene>-<lang>.json``) that
  ``--recorded-row`` consumes to refresh ``docs/demo/RECORDED.md``.

Usage:
    python scripts/demo/record_tui_demo.py --list-scenes
    python scripts/demo/record_tui_demo.py --scene NAME --lang en --dry-run
    python scripts/demo/record_tui_demo.py --scene NAME --lang zh
    python scripts/demo/record_tui_demo.py --recorded-row NAME --lang en
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# The tui/__main__.py bootstrap idiom: the repo root (for ``tui`` package
# imports) and REPO_ROOT/pipeline (for the top-level pipeline seam modules
# the textual-free registry services import) both land on sys.path before
# the tui imports below.
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "pipeline"))

from tui import strings as S  # post-bootstrap by design
from tui.services import registries as registries_service

# ===== Terminal key bytes =====
ESC = "\x1b"
TAB = "\t"
STAB = "\x1b[Z"
ENTER = "\r"
DOWN = "\x1b[B"
SPACE = " "
BS = "\x7f"
END = "\x1b[F"

#: The pinned pty grid the console renders on (>= the 80x24 minimum).
TERMINAL_ROWS = 30
TERMINAL_COLS = 100

#: The demo training matrix (pre-authorized bounded GPU, quick-261015-pex).
DEMO_MODEL = "plant-dnabert-6mer"
DEMO_TASK = "iDNA_ABF_datasets__5mC"
DEMO_SEEDS_MAIN = "42,43"
DEMO_SEEDS_FAIL = "42"
DEMO_EPOCHS = "1"
#: The demo sweeps nest under the gitignored REPO-LEVEL finetuned/ tree
#: (the launcher resolves "./" on the REPO_ROOT basis) — nesting keeps
#: them inside the monitor's default DISCOVERY scan root, so the
#: discovered table lists them natively (the sibling-root spelling from
#: the plan could never be discovered without a manual attach, which
#: proved flaky in rehearsal). The REAL pipeline/finetuned tree (the
#: pipeline's own default) is never written; finetuned/ is gitignored
#: wholesale.
DEMO_ROOT_ARG = "./finetuned/demo"
DEMO_FAIL_ROOT_ARG = "./finetuned/demo-fail"
DEMO_ROOT = REPO_ROOT / "finetuned" / "demo"
DEMO_FAIL_ROOT = REPO_ROOT / "finetuned" / "demo-fail"
#: The landed demo custom entry key (wizard scene, en recording).
DEMO_CUSTOM_KEY = "demo-custom-model"
#: The saved demo preset name (selection-presets scene).
DEMO_PRESET_NAME = "demo-walkthrough"

DOCS_DEMO_DIR = REPO_ROOT / "docs" / "demo"
RECORDED_MD = DOCS_DEMO_DIR / "RECORDED.md"

DEFAULT_TIMEOUT = 30.0
DOWNLOAD_TIMEOUT = 1200.0
TRAINING_TIMEOUT = 900.0


class DriverError(RuntimeError):
    """A scene failed: an anchor timed out, prep guard tripped, or the
    console exited unexpectedly. The recording must be re-run."""


# =====================================================================
# The step DSL — declarative timelines as data
# =====================================================================

Step = tuple  # ("send", bytes, settle_seconds) | ("anchor", (bytes,), timeout, label) | ("wait", seconds, label)


@dataclass
class ScanResult:
    """The live presence scan every scene builder consumes."""

    model_target: str | None = None
    model_target_path: str | None = None
    missing_datasets: list[str] = field(default_factory=list)
    dataset_target: str | None = None
    dataset_target_dir: Path | None = None
    dataset_target_downs: int = 0
    custom_keys: list[str] = field(default_factory=list)
    demo_custom_present: bool = False
    card: dict = field(default_factory=dict)


@dataclass
class SceneMeta:
    """What one recording actually used (the RECORDED.md truth source)."""

    scene: str = ""
    lang: str = ""
    date: str = ""
    boot_lang: str = ""
    wall_seconds: float = 0.0
    notes: list[str] = field(default_factory=list)
    targets: dict = field(default_factory=dict)


class Builder:
    """Builds one scene's timeline, tracking the expected UI language so
    anchors resolve through ``tui/strings.py`` in the language the console
    is showing at that moment."""

    def __init__(self, boot_lang: str, body_lang: str, speed: float):
        self.lang = boot_lang
        self.boot_lang = boot_lang
        self.body_lang = body_lang
        self.speed = speed
        self.steps: list[tuple] = []
        self.notes: list[str] = []

    # ----- resolution -----

    def _resolve(self, name: str, fmt: dict | None = None) -> str:
        S.set_language(self.lang)
        value = getattr(S, name)
        if fmt:
            value = value.format(**fmt)
        return value

    # ----- steps -----

    def note(self, text: str) -> None:
        self.notes.append(text)
        self.steps.append(("wait", 0.0, text))

    def raw(self, data: str, settle: float = 0.4, label: str = "") -> None:
        self.steps.append(("send", data.encode("utf-8"),
                           settle * self.speed, label))

    def key(self, data: str, settle: float = 0.4) -> None:
        self.raw(data, settle)

    def nav(self, digit: str, settle: float = 0.9) -> None:
        """A navigation digit — always ESC-prefixed so no focused input
        (or open modal beneath) ever swallows it. The ESC goes out as its
        OWN write with a gap: ESC and the digit in one chunk parse as
        Alt+digit, never as two keystrokes."""
        self.raw(ESC, settle=0.18)
        self.raw(digit, settle=settle)

    def global_key(self, key: str, settle: float = 0.9) -> None:
        """An app-level key (L, q) — ESC-prefixed (needs the unfocused
        screen; a focused input would type it), same own-write ESC rule
        as nav()."""
        self.raw(ESC, settle=0.18)
        self.raw(key, settle=settle)

    def anchor(self, *candidates: str, timeout: float = DEFAULT_TIMEOUT,
               label: str = "") -> None:
        patterns = tuple(c.encode("utf-8") for c in candidates)
        self.steps.append(("anchor", patterns, timeout * self.speed
                           if timeout < 100 else timeout,
                           label or candidates[0][:48]))

    def branch(self, *cases: tuple[str, str], timeout: float = DEFAULT_TIMEOUT,
               label: str = "") -> None:
        """Anchor on alternatives, then send the MATCHED case's bytes (or
        nothing for an empty action) — the runtime-conditional idiom for
        first-time-vs-overwrite flows."""
        patterns = tuple(case[0].encode("utf-8") for case in cases)
        actions = tuple(case[1] for case in cases)
        self.steps.append(("branch", patterns, actions, timeout,
                           label or cases[0][0][:48]))

    def A(self, name: str, fmt: dict | None = None, substring: str | None = None,
          timeout: float = DEFAULT_TIMEOUT, label: str | None = None) -> None:
        """Anchor on a strings.py constant (optionally a fixed substring of
        it, immune to the format fields)."""
        value = self._resolve(name, fmt)
        if substring is not None:
            value = substring
        self.anchor(value, timeout=timeout, label=label or name)

    def wait(self, seconds: float, label: str = "") -> None:
        self.steps.append(("wait", seconds * self.speed, label))

    def flush(self) -> None:
        """Drop everything rendered so far from future anchor searches —
        the phase-boundary idiom: a stale frame from an earlier phase
        (e.g. the A-setup's transient '2 seeds' preview line) must never
        satisfy a later phase's anchor (probe-pinned in rehearsal)."""
        self.steps.append(("flush",))

    # ----- composite idioms -----

    def toggle_language(self, to_lang: str) -> None:
        """Press L on camera and anchor the arrival toast."""
        self.lang = to_lang
        self.global_key("L", settle=0.2)
        self.A("APP_LANGUAGE_TOAST", timeout=10)

    def restore_boot_language(self) -> None:
        if self.lang != self.boot_lang:
            self.toggle_language(self.boot_lang)

    def filter_position(self, table_key: str, settle: float = 1.2) -> None:
        """The k9s positioning idiom, STAYING FILTERED: focus the filter,
        narrow to exactly one row, TAB to the table (the filter stays
        applied, the cursor rides the row). For d/e/w actions that must
        hit the positioned row — ESC here would clear the filter and
        reset the cursor to row 0 of the FULL table (probe-pinned)."""
        self.key("/", settle=0.3)
        self.raw(table_key, settle=settle)
        self.key(TAB, settle=0.5)
        self.notes.append(f"position cursor on {table_key} via filter+tab")

    def filter_mark(self, table_key: str, *, unmark: bool = False,
                    settle: float = 0.5) -> None:
        """filter_position + SPACE the cursor row + ESC to clear and
        refocus (the marks live in shared state — the ESC cannot lose
        them; the scene's NEXT key acts on the unfiltered table)."""
        self.filter_position(table_key)
        self.key(SPACE, settle=settle)
        self.key(ESC, settle=0.6)
        verb = "unmark" if unmark else "mark"
        self.notes.append(f"{verb} {table_key} via filter+tab")


def wait_env_settled(b: Builder) -> None:
    """Wait out the boot env check before navigating (a cold boot's
    kernels run ~30s and a nav digit sent mid-boot can be lost)."""
    critical = b._resolve("ENV_VERDICT_CRITICAL_FAIL", {"kernel_names": ""})
    route = b._resolve("ENV_ROUTE_MISSING_DATASETS", {"n": ""})
    models_route = b._resolve("ENV_ROUTE_MISSING_MODELS", {"n": ""})
    b.anchor(b._resolve("ENV_VERDICT_PASS"),
             critical.split("{")[0], route.split("{")[0],
             models_route.split("{")[0],
             timeout=300, label="boot env check settled")


def boot_prologue(b: Builder) -> None:
    """Detect the boot language by anchor (fresh state dir always boots
    English, but verify honestly)."""
    b.anchor(S.NAV_LABEL_ENV, _in_zh("NAV_LABEL_ENV"),
             timeout=90, label="boot screen")


def _in_zh(name: str) -> str:
    lang = S.language()
    S.set_language("zh")
    try:
        return getattr(S, name)
    finally:
        S.set_language(lang)


# =====================================================================
# The live presence scan (targeting truth — never hardcoded)
# =====================================================================

def _config_root() -> Path:
    override = os.environ.get("DNALLMMARK_TUI_CONFIG_DIR")
    if override:
        return Path(override)
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "dnallmmark"
    return Path.home() / ".config" / "dnallmmark"


def run_scan() -> ScanResult:
    """Live presence scan: the smallest missing ADAPTED model and the
    n_audit-missing datasets (the TUI's own presence source), replicating
    the textual-free service reads the console performs."""
    result = ScanResult()
    compat = json.loads(
        (REPO_ROOT / "pipeline" / "dnallm_compat.json").read_text(
            encoding="utf-8"))["models"]
    models = json.loads(
        (REPO_ROOT / "pipeline" / "models_info.json").read_text(
            encoding="utf-8"))
    missing: list[tuple[float, str, str]] = []
    for key, card in models.items():
        if not isinstance(card, dict):
            continue
        if not compat.get(key, {}).get("dnllm_adapted"):
            continue
        model_path = card.get("Model_path")
        if not isinstance(model_path, str) or not model_path:
            continue
        if (REPO_ROOT / "pipeline" / model_path).is_dir():
            continue
        size = card.get("size (M)")
        rank = (float(size)
                if isinstance(size, (int, float)) and not isinstance(size, bool)
                else float("inf"))
        missing.append((rank, key, model_path))
    missing.sort()
    if missing:
        result.model_target = missing[0][1]
        result.model_target_path = missing[0][2]

    audit = registries_service.load_n_audit() or {}
    datasets = json.loads(
        (REPO_ROOT / "pipeline" / "datasets_info.json").read_text(
            encoding="utf-8"))
    for key, entry in datasets.items():
        if not isinstance(entry, dict):
            continue
        if (registries_service.presence_for(key, audit).status
                == registries_service.PRESENCE_MISSING):
            result.missing_datasets.append(key)
    if result.missing_datasets:
        result.dataset_target = result.missing_datasets[0]
        result.dataset_target_downs = 0  # cursor starts on the first row
        dataset_path = datasets[result.dataset_target].get("Dataset_path")
        if isinstance(dataset_path, str) and dataset_path:
            result.dataset_target_dir = REPO_ROOT / "pipeline" / dataset_path

    custom_file = _config_root() / "custom_models.json"
    if custom_file.is_file():
        try:
            customs = json.loads(custom_file.read_text(encoding="utf-8"))
            result.custom_keys = sorted(
                key for key, value in customs.items() if isinstance(value, dict))
        except (OSError, ValueError):
            result.custom_keys = []
    result.demo_custom_present = DEMO_CUSTOM_KEY in result.custom_keys
    card = models.get(DEMO_MODEL)
    result.card = card if isinstance(card, dict) else {}
    return result


# =====================================================================
# Scene prep — demo-scoped filesystem resets only
# =====================================================================

def _guarded_rm(path: Path, allowed_parent: Path, allowed_names: set[str]) -> None:
    if path.parent != allowed_parent or path.name not in allowed_names:
        raise DriverError(
            f"refusing to delete outside the demo scope: {path}")
    if path.exists():
        shutil.rmtree(path)


def scene_prep(scene: str, lang: str, scan: ScanResult) -> list[str]:
    """Per-scene filesystem prep. Returns the prep notes for the meta
    sidecar. NEVER touches the real pipeline/finetuned tree."""
    notes: list[str] = []
    if scene == "launch-monitor-kill":
        _guarded_rm(DEMO_ROOT, REPO_ROOT / "finetuned",
                    {"demo"})
        _guarded_rm(DEMO_FAIL_ROOT, REPO_ROOT / "finetuned",
                    {"demo-fail"})
        # The fast-failure sweep (the missing reset dataset fails the cell
        # for real) runs OFF-CAMERA through the maintainer CLI surface:
        # the console becomes input-dead after a SECOND in-session launch
        # on this box (WINDOWS row), so the on-camera session carries
        # exactly ONE launch. RECORDED.md documents the prep.
        failures = DEMO_FAIL_ROOT / "sweep_failures.json"
        if not failures.is_file():
            import subprocess
            subprocess.run(
                ["uv", "run", "--group", "gpu", "python",
                 str(REPO_ROOT / "pipeline" / "run_sweep.py"),
                 "--models", DEMO_MODEL,
                 "--tasks", scan.dataset_target or DEMO_TASK,
                 "--seeds", DEMO_SEEDS_FAIL,
                 "--output-root", str(DEMO_FAIL_ROOT),
                 "--num_train_epochs", DEMO_EPOCHS],
                cwd=str(REPO_ROOT), check=False, timeout=600,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        entries = (json.loads(failures.read_text(encoding="utf-8"))
                   if failures.is_file() else [])
        if not entries:
            raise DriverError(
                "the prep fail-sweep produced no failures — the dataset "
                "reset is missing (run the audit reset first)")
        notes.append(f"wiped finetuned/demo; the fail root "
                     f"finetuned/demo-fail carries {len(entries)} real "
                     "failure(s) from the off-camera CLI prep sweep")
    elif scene == "model-download" and scan.model_target_path:
        model_dir = REPO_ROOT / "pipeline" / scan.model_target_path
        _guarded_rm(model_dir, (REPO_ROOT / "pipeline" / "models").resolve(),
                    {Path(scan.model_target_path).name})
        notes.append(
            f"reset download target {scan.model_target_path} before spawn "
            "(the re-record lever)")
    elif scene == "dataset-download":
        if not scan.dataset_target:
            raise DriverError(
                "no n_audit-missing dataset on this box — the dataset "
                "scene requires the reset lever (see docs/demo/RECORDED.md)")
        if scan.dataset_target_dir is None:
            raise DriverError(
                f"missing dataset {scan.dataset_target} carries no "
                "Dataset_path — cannot prep")
        if scan.dataset_target_dir.exists():
            if scan.dataset_target_dir.parent.parent != (
                    REPO_ROOT / "pipeline" / "datasets"):
                raise DriverError(
                    "dataset target outside pipeline/datasets: "
                    f"{scan.dataset_target_dir}")
            shutil.rmtree(scan.dataset_target_dir)
            notes.append(
                f"re-deleted {scan.dataset_target_dir.relative_to(REPO_ROOT)} "
                "before spawn (the re-record lever)")
    elif scene in ("wizard", "custom-entries"):
        if not scan.demo_custom_present:
            card = scan.card
            if not card:
                raise DriverError("plant-dnabert-6mer card unreadable")
            entry = {
                "Model_path": str(card.get("Model_path", "")),
                "size (M)": card.get("size (M)"),
                "species": str(card.get("species", "")),
                "type": str(card.get("type", "")),
                "architecture": str(card.get("architecture") or ""),
                "Tokenizer": str(card.get("Tokenizer", "")),
                "context_len (bp)": card.get("context_len (bp)"),
                "huggingface": str(card.get("huggingface", "")),
                "modelscope": str(card.get("modelscope", "")),
                "series": str(card.get("series", "")),
                "quirks": {},
                "enabled": True,
            }
            # the real onboarding write seam (the wizard gauntlet's land
            # call) — the entry carries the plant-dnabert-6mer card's own
            # values under the demo key; documented in RECORDED.md
            from tui.services import custom_entries
            custom_entries.land("models", DEMO_CUSTOM_KEY, entry)
            scan.demo_custom_present = True
            notes.append(
                f"landed custom entry {DEMO_CUSTOM_KEY} via the "
                "custom_entries service before recording (this box "
                "carried no customs; the wizard's own land path)")
    elif scene == "rerun-from-failures":
        failures = DEMO_FAIL_ROOT / "sweep_failures.json"
        if not failures.is_file():
            raise DriverError(
                "pipeline/finetuned-demo-fail carries no sweep_failures.json "
                "— record launch-monitor-kill first")
        entries = json.loads(failures.read_text(encoding="utf-8"))
        if not entries:
            raise DriverError(
                "sweep_failures.json is empty — the rerun scene has no "
                "failures to re-run")
        notes.append(f"attach target carries {len(entries)} real failure(s)")
    return notes


# =====================================================================
# The ten scenes
# =====================================================================

def scene_env_check(b: Builder, sc: ScanResult) -> None:
    boot_prologue(b)
    if b.body_lang != b.lang:
        b.toggle_language(b.body_lang)
    # fresh state dir => the 8 kernels run live on boot; wait for the
    # verdict (any verdict shape means the kernels finished)
    verdict_pass = b._resolve("ENV_VERDICT_PASS")
    critical = b._resolve("ENV_VERDICT_CRITICAL_FAIL",
                          {"kernel_names": ""})
    route = b._resolve("ENV_ROUTE_MISSING_DATASETS", {"n": ""})
    b.anchor(verdict_pass, critical.split("{")[0], route.split("{")[0],
             timeout=240, label="first env check verdict")
    b.key(ESC, settle=0.18)
    b.key("r", settle=1.0)  # re-run every kernel
    # (no transient "checking" anchor: textual coalesces frames, and a
    # kernel that finishes within one frame never emits the state — the
    # completion verdict is the honest re-run anchor)
    b.anchor(verdict_pass, critical.split("{")[0], route.split("{")[0],
             timeout=240, label="re-run verdict")
    b.key(ENTER, settle=1.0)  # drill-down on the cursor row (version_pins)
    b.anchor("version_pins", timeout=15, label="drill-down title")
    b.key(ESC, settle=0.6)
    b.note("8 kernels live on boot (fresh state dir); r re-run; "
           "version_pins drill-down")


def scene_selection_presets(b: Builder, sc: ScanResult) -> None:
    boot_prologue(b)
    if b.body_lang != b.lang:
        b.toggle_language(b.body_lang)
    b.nav("2")
    b.A("SEL_SCREEN_TITLE_MODELS", timeout=30)
    # space marks on plant-dnabert-6mer and neighbors (the family rows)
    b.key("/", settle=0.3)
    b.raw("plant-dnabert", settle=1.2)
    b.key(TAB, settle=0.5)
    for _ in range(3):
        b.key(SPACE, settle=0.5)
        b.key(DOWN, settle=0.35)
    b.key(ESC, settle=0.7)
    # the registry-grammar filter (axis:value), then esc
    b.key("/", settle=0.3)
    b.raw("species:plants", settle=1.2)
    b.key(TAB, settle=0.5)
    b.wait(0.8)
    b.key(ESC, settle=0.7)
    # preset picker apply (cursor on tier-1 E2E pairs)
    b.key("p", settle=1.0)
    b.A("SEL_PRESET_TITLE", timeout=15)
    b.key(ENTER, settle=1.2)
    b.A("SEL_PRESET_APPLIED", substring=b._resolve(
        "SEL_PRESET_APPLIED", {"preset": "x", "n": 1, "m": 1}).split("x")[0],
        timeout=15, label="preset applied toast")
    # save the current marks as a named preset; a prior recording's name
    # lands on the overwrite confirm instead — only THAT path takes enter
    # (a stray enter on the closed modal would open the card drill-down)
    b.key("s", settle=1.0)
    b.A("SEL_PRESET_NAME_PLACEHOLDER", timeout=15,
        label="save-preset modal")
    b.raw(DEMO_PRESET_NAME, settle=0.6)
    b.key(ENTER, settle=1.2)
    b.branch(
        (b._resolve("SEL_PRESET_SAVED",
                    {"name": DEMO_PRESET_NAME, "n": 1, "m": 1}).split("1")[0],
         ""),
        (b._resolve("SEL_PRESET_OVERWRITE_CONFIRM",
                    {"name": DEMO_PRESET_NAME}).split(DEMO_PRESET_NAME)[0],
         ENTER),
        timeout=15, label="saved-or-overwrite")
    b.anchor(
        b._resolve("SEL_PRESET_SAVED",
                   {"name": DEMO_PRESET_NAME, "n": 1, "m": 1}).split("1")[0],
        timeout=15, label="preset saved toast")
    # presence matrix
    b.key("v", settle=1.4)
    b.A("MATRIX_TITLE", fmt={"models": 59, "datasets": 50}, timeout=20,
        label="matrix title")
    b.wait(1.0)
    b.key(ESC, settle=0.7)
    b.note("space marks on the plant-dnabert family (filter+tab idiom); "
           "species:plants registry-grammar filter; tier-1 preset apply; "
           f"preset save '{DEMO_PRESET_NAME}'; 59x50 presence matrix")


def scene_model_download(b: Builder, sc: ScanResult) -> None:
    if not sc.model_target:
        raise DriverError(
            "no missing ADAPTED model on this box — record the honest "
            "already-downloaded surface instead (see the plan's fallback)")
    boot_prologue(b)
    if b.body_lang != b.lang:
        b.toggle_language(b.body_lang)
    b.flush()
    b.nav("2")
    b.A("SEL_SCREEN_TITLE_MODELS", timeout=30)
    b.filter_position(sc.model_target)  # stay filtered: d acts on the row
    b.key("d", settle=1.0)
    # anchors clip-safely: the download column sits at the right edge of
    # the 100-col grid, so the cell text is CLIPPED mid-word on the wire
    # ("⠋ downloadin" — probe-pinned); anchor the clipped-stable prefix.
    b.anchor("downloadin", timeout=90, label="download starts (claim tick)")
    # EHC-4 observation window: the percent/rate ticks render only while
    # the transfer actually streams — the maintainer's ModelScope mirror
    # is fast enough that a small model can finish inside one render
    # frame (RECORDED.md documents what the GIF truly shows)
    b.wait(5.0)
    b.anchor("\u2713 downloa", timeout=DOWNLOAD_TIMEOUT,
             label="finished flip (download cell)")
    b.wait(1.0)
    b.note(f"REAL ModelScope download of {sc.model_target} (smallest "
           "missing adapted model, live scan) with percent + transfer-rate "
           "ticks; download column flip")


def scene_dataset_download(b: Builder, sc: ScanResult) -> None:
    if not sc.dataset_target:
        raise DriverError("no missing dataset — scene requires the reset")
    boot_prologue(b)
    if b.body_lang != b.lang:
        b.toggle_language(b.body_lang)
    b.nav("3")
    b.A("DL_PRESENCE_SUMMARY", fmt={"present": 49, "total": 50,
                                    "missing": 1},
        substring=b._resolve("DL_PRESENCE_SUMMARY",
                             {"present": 49, "total": 50,
                              "missing": 1}).split("49")[0],
        timeout=30, label="slot 3 arrival")
    b.flush()
    b.key("v", settle=1.2)
    b.A("DL_MISSING_TITLE", fmt={"n": len(sc.missing_datasets)},
        substring=b._resolve(
            "DL_MISSING_TITLE", {"n": len(sc.missing_datasets)}
        ).split(str(len(sc.missing_datasets)))[0],
        timeout=20, label="missing view")
    for _ in range(sc.dataset_target_downs):
        b.key(DOWN, settle=0.3)
    b.key("d", settle=1.2)
    # (the toast wraps after the glyph — anchor the post-glyph word)
    b.anchor("enqueued", timeout=20, label="enqueue toast")
    # queue-row percent + progress bar + rate (the EHC-4 surface) render
    # only while the transfer streams — the maintainer's ModelScope
    # mirror is fast enough that small datasets finish inside one render
    # frame, so the observation is a timed window and the COMPLETION is
    # the anchor: the reconcile cell's "rows match" + the full-list
    # presence summary flipping to all-present (both deterministic data)
    b.wait(6.0)
    b.anchor(b._resolve("QUEUE_RECONCILE_PASS",
                        {"n": 10581}).split("10581")[1], timeout=120,
             label="reconcile cell (rows match)")
    b.anchor(b._resolve("DL_PRESENCE_SUMMARY", {"present": 50, "total": 50,
                                                "missing": 0}),
             timeout=120, label="presence summary all-present")
    # drill-down on the finished queue row (focus the queue table first)
    b.key(TAB, settle=0.6)
    b.key(ENTER, settle=1.4)
    b.anchor("download_url", timeout=20, label="queue drill-down")
    b.key(ESC, settle=0.7)
    b.note(f"REAL ModelScope dataset download of {sc.dataset_target} "
           "(the box's one n_audit-missing key, reset lever documented in "
           "RECORDED.md) with queue percent + progress bar + rate; "
           "reconcile flip; queue-row drill-down")


def _walk_to_input(b: Builder, back_steps: int) -> None:
    """Walk focus backward from the picker into the params/dirs column.

    The probe-pinned focus facts (textual 8.2.8, quick-261015-pex
    rehearsal): a focused Input KEEPS focus on esc (the key never
    reaches the screen binding), and the picker (SelectionList) traps
    forward tab — the only road from the picker into the params column
    is shift-tab through the filter, which WRAPS to the column's last
    input (log dir), then further back-steps walk the field order in
    reverse. Forward tab inside the params column works normally."""
    b.key(STAB, settle=0.25)  # picker -> filter
    b.key(STAB, settle=0.25)  # filter -> wraps to the last input
    for _ in range(back_steps):
        b.key(STAB, settle=0.25)


#: From the wrap point (log dir) backward to each field:
#: log-dir -> cache(1) -> model-root(2) -> dataset-root(3) ->
#: output-root(4) -> ebs(5) -> epochs(6) -> subset(7) -> curve(8) ->
#: variant(9) -> peft(10) -> seeds(11)
_STAB_TO_SEEDS = 11
_TAB_SEEDS_TO_EPOCHS = 5  # peft, variant, curve, subset, epochs
_TAB_EPOCHS_TO_ROOT = 2   # ebs, output root
_TAB_ROOT_TO_PICKER = 6   # dataset-root, model-root, cache, log-dir, filter, picker


def _clear_and_type(b: Builder, text: str, prev_len: int) -> None:
    """Clear the focused input (END + margin backspaces — extra BS on an
    empty input is a no-op; one BS was observed lost to END's settle in
    rehearsal) and type the new value."""
    b.key(END, settle=0.4)
    for _ in range(prev_len + 3):
        b.key(BS, settle=0.06)
    b.raw(text, settle=1.0)


def _preview_line_anchor(b: Builder, seeds_count: int) -> None:
    """Anchor the live preview line for the composed matrix — the
    semantic proof the seeds edit landed (an echo anchor on '42,43'
    would also match the stale '42,43,44' frame)."""
    b.A("CFG_PREVIEW_LINE",
        fmt={"models": 1, "tasks": 1, "seeds": seeds_count,
             "cells": seeds_count},
        timeout=20, label=f"preview line ({seeds_count} seeds)")


def _run_config_setup(b: Builder, task: str, seeds: str, seeds_count: int,
                      root: str, prev_seeds_len: int, prev_root_len: int,
                      first: bool = True) -> None:
    """The slot-4 composition idiom shared by the preview and launch
    scenes: mark model+task via the filter+tab idiom, then edit seeds,
    epochs, and the output root (backward walk in, forward walk out).
    The root edit carries no echo anchor by design — the later gate
    summary / argv anchors are the typo-guard (an echo on
    'finetuned-demo' would also match the stale '-fail' frame)."""
    if first:
        b.filter_mark(DEMO_MODEL)
        b.key("m", settle=1.0)
        b.A("CFG_PICKER_DATASETS", substring=b._resolve(
            "CFG_PICKER_DATASETS", {"n": 1, "total": 2}).split("1")[0],
            timeout=15, label="datasets picker")
    b.filter_mark(task)
    _walk_to_input(b, _STAB_TO_SEEDS)
    _clear_and_type(b, seeds, prev_seeds_len)
    _preview_line_anchor(b, seeds_count)
    for _ in range(_TAB_SEEDS_TO_EPOCHS):
        b.key(TAB, settle=0.3)
    b.raw(DEMO_EPOCHS, settle=0.6)
    for _ in range(_TAB_EPOCHS_TO_ROOT):
        b.key(TAB, settle=0.3)
    _clear_and_type(b, root, prev_root_len)
    for _ in range(_TAB_ROOT_TO_PICKER):
        b.key(TAB, settle=0.25)  # forward through the dirs back to the picker


def scene_run_config_preview(b: Builder, sc: ScanResult) -> None:
    boot_prologue(b)
    if b.body_lang != b.lang:
        b.toggle_language(b.body_lang)
    wait_env_settled(b)
    b.nav("4")
    b.A("CFG_PARAMS_TITLE", timeout=60, label="slot 4 arrival")
    b.anchor(b._resolve("CFG_PICKER_MODELS",
                        {"n": 0, "total": 59}).split("0")[0], timeout=30,
             label="models picker populated")
    b.wait(0.8)
    _run_config_setup(b, DEMO_TASK, DEMO_SEEDS_MAIN, 2, DEMO_ROOT_ARG,
                      prev_seeds_len=len("42,43,44"),
                      prev_root_len=len("./finetuned"))
    b.key("p", settle=1.4)
    b.A("CFG_PREVIEW_MODAL_TITLE", timeout=15, label="preview modal")
    b.A("CFG_ARGV_LABEL", timeout=10, label="argv label")
    b.anchor(DEMO_ROOT_ARG.rsplit("/", 1)[-1], timeout=10,
             label="typo-guard: demo root in argv")
    b.anchor(DEMO_SEEDS_MAIN, timeout=10, label="seeds in argv")
    b.anchor(DEMO_EPOCHS, timeout=10, label="epochs in argv")
    b.wait(1.5)
    b.key(ESC, settle=0.8)
    b.note(f"picker m flip + filter marks ({DEMO_MODEL}, {DEMO_TASK}); "
           f"seeds {DEMO_SEEDS_MAIN}; epochs {DEMO_EPOCHS}; output root "
           f"{DEMO_ROOT_ARG}; verbatim dry-run argv preview")


def scene_launch_monitor_kill(b: Builder, sc: ScanResult) -> None:
    boot_prologue(b)
    if b.body_lang != b.lang:
        b.toggle_language(b.body_lang)
    wait_env_settled(b)
    b.nav("4")
    b.A("CFG_PARAMS_TITLE", timeout=60, label="slot 4 arrival")
    b.anchor(b._resolve("CFG_PICKER_MODELS",
                        {"n": 0, "total": 59}).split("0")[0], timeout=30,
             label="models picker populated")
    b.wait(0.8)

    # The launch: the bounded demo training (2 seeds, 1 epoch) on the
    # present task. (The session carries exactly ONE launch: the console
    # becomes input-dead after a second in-session launch on this box —
    # WINDOWS row; the fast-failure sweep is the rerun scene's subject.)
    _run_config_setup(b, DEMO_TASK, DEMO_SEEDS_MAIN, 2, DEMO_ROOT_ARG,
                      prev_seeds_len=len("42,43,44"),
                      prev_root_len=len("./finetuned"))
    b.key(ENTER, settle=2.0)  # open the gate
    gate_prompt = b._resolve("LNC_GATE_CONFIRM").split("[y]")[0]
    b.anchor(gate_prompt, timeout=30, label="gate confirm")
    b.key(ENTER, settle=1.6)  # EHC-2: enter stays inert on launch confirms
    b.wait(1.2)  # the GIF shows the modal NOT reacting to enter
    b.key("y", settle=6.0)  # the one key that launches

    # Monitor: with a SINGLE in-session launch the auto-switch and
    # auto-attach both fire — the live stats line is the attach proof.
    # (No flush here: the auto-switch renders inside the settle, and
    # flushing after it would eat the evidence.)
    b.key("5", settle=1.5)  # belt-and-braces (a no-op when switched)
    b.anchor("0/2", timeout=60, label="live stats (attached, seed 42 runs)")

    # The whole post-launch sequence fits inside the pre-stall window:
    # the console reliably stops processing input ~60s after launch on
    # this box (around the first cell's completion output burst —
    # WINDOWS row), so every step below lands early and the kill happens
    # mid-seed-42 (the fold-then-kill sequence is unreachable here).
    # Post-modal navigation digits go out RAW with wide gaps: an ESC
    # inside a modal's deferred dismissal eats the following key
    # (probe-pinned across rehearsals).
    b.key("t", settle=2.0)  # log-tail modal (the training log streams)
    b.A("MON_LOG_TITLE", substring=b._resolve(
        "MON_LOG_TITLE", {"root": "x"}).split("x")[0], timeout=20,
        label="log tail")
    b.wait(2.0)
    b.key(ESC, settle=2.0)
    b.key("f", settle=1.6)  # failures modal (empty mid-run)
    b.anchor(b._resolve("MON_FAILURES_TITLE", {"n": 0}), timeout=20,
             label="failures modal")
    b.wait(1.0)
    b.key(ESC, settle=2.0)
    b.wait(0.5)

    # EHC-3: a second gated launch while the sweep is live is refused at
    # stage 0. The attempt re-aims at the (non-live) fail root — the
    # CR-02 live-root refusal would otherwise fire FIRST for the demo
    # root itself, and the EHC-3 guard must be the refuser, naming the
    # running root. (No launch-toast anchor after y: the toast renders
    # only when the launch worker retires, which for a long-lived sweep
    # is late — the refusal below only fires while the sweep is genuinely
    # live, which makes IT the proof of the launch.)
    b.flush()
    b.key("4", settle=2.0)
    # the picker kind resets to models on every slot-4 revisit
    b.anchor(b._resolve("CFG_PICKER_MODELS",
                        {"n": 0, "total": 59}).split("0")[0], timeout=30,
             label="slot 4 revisit")
    b.wait(0.8)
    _walk_to_input(b, 4)  # back to the output-root field
    _clear_and_type(b, DEMO_FAIL_ROOT_ARG, len(DEMO_ROOT_ARG))
    for _ in range(_TAB_ROOT_TO_PICKER):
        b.key(TAB, settle=0.25)
    b.key(ENTER, settle=2.5)
    # (the problems modal wraps the refusal at ~54 cols — anchor the
    # pre-wrap segment only)
    b.anchor(b._resolve("LNC_SINGLE_GPU_BLOCKED",
                        {"roots": "x"}).split("single-")[0]
             + "single-", timeout=30, label="EHC-3 single-GPU refusal")
    b.wait(2.0)
    # q->k straight from slot 4 (no post-modal navigation needed): q is
    # app-level; with the live sweep it pushes the exit modal, k kills
    b.note(f"REAL launch of {DEMO_MODEL} x {DEMO_TASK} seeds "
           f"{DEMO_SEEDS_MAIN} epochs {DEMO_EPOCHS} at {DEMO_ROOT_ARG} "
           "through the y-gate (enter shown inert); auto-switch + live "
           "0/2 stats; log tail; failures modal empty mid-run; EHC-3 "
           "stage-0 refusal naming the running root; q->k kills the "
           "sweep mid-seed-42 (the console's cell-completion stall "
           "makes the fold-then-kill sequence unreachable on this box — "
           "WINDOWS row)")


def scene_rerun_from_failures(b: Builder, sc: ScanResult) -> None:
    boot_prologue(b)
    wait_env_settled(b)  # settle BEFORE the L toggle (boot-race pinned)
    if b.body_lang != b.lang:
        b.toggle_language(b.body_lang)
    b.nav("5")
    b.A("MON_SCREEN_TITLE", timeout=30, label="monitor")
    b.key("a", settle=1.2)
    b.A("MON_ATTACH_TITLE", timeout=15, label="attach modal")
    b.raw("finetuned/demo-fail", settle=0.8)
    b.key(ENTER, settle=2.5)
    b.anchor(b._resolve("MON_CELLS_TITLE",
                        {"root": DEMO_FAIL_ROOT.name}), timeout=20,
             label="entries table over the fail root")
    b.wait(1.5)
    b.flush()
    b.key("f", settle=1.6)
    # (the failures ROW clips at the modal width — the long task key
    # truncates before the seed segment; the (1) title IS the proof the
    # real failure is listed)
    b.anchor(b._resolve("MON_FAILURES_TITLE", {"n": 1}), timeout=20,
             label="failures modal with the real failure")
    b.key("r", settle=1.6)
    # (the confirm wraps at ~54 cols — anchor the pre-wrap segment)
    b.anchor(b._resolve("MON_RERUN_CONFIRM",
                        {"pairs": 1, "seeds": DEMO_SEEDS_FAIL, "n": 1}
                        ).split(" × ")[0], timeout=20, label="rerun confirm")
    b.key(ENTER, settle=1.5)  # EHC-2: enter inert on the re-run confirm
    b.wait(1.2)
    b.key("y", settle=3.0)
    # (no launch-toast anchor: the launch worker retires late for a
    # long-lived sweep — the stats-line reset IS the launch proof)
    b.flush()
    b.anchor("0/1", timeout=60, label="rerun started (stats reset)")
    # the dataset is present again (the download scene restored it), so
    # the failed seed retrains FOR REAL and folds to done
    b.anchor("1/1", timeout=TRAINING_TIMEOUT, label="entry folded done")
    b.wait(1.5)
    b.note("attach the fail root (repo-relative path form); the real "
           "failure from launch A is listed; "
           "r->y (enter shown inert) re-runs it at the sweep's own root; "
           "the now-present dataset lets the seed retrain to completion")


def scene_language_toggle(b: Builder, sc: ScanResult) -> None:
    boot_prologue(b)
    # en recording: show the EN bars first, then toggle zh, navigate, back.
    if b.body_lang == "en":
        b.nav("2")
        b.A("SEL_SCREEN_TITLE_MODELS", timeout=30, label="en models screen")
        b.toggle_language("zh")
        b.nav("1")
        b.A("ENV_SCREEN_TITLE", timeout=20, label="zh re-render")
        b.wait(1.2)
        b.toggle_language("en")
    else:
        b.toggle_language("zh")
        b.nav("2")
        b.A("SEL_SCREEN_TITLE_MODELS", timeout=30, label="zh models screen")
        b.wait(1.2)
        b.toggle_language("en")
    b.note("the L live toggle: full-screen re-render, bars/footer follow, "
           "one navigation in the toggled language, restored before quit")


def scene_wizard(b: Builder, sc: ScanResult) -> None:
    boot_prologue(b)
    if b.body_lang != b.lang:
        b.toggle_language(b.body_lang)
    # dataset wizard (slot 3): real edits, enter/b, esc-cancel, no landing
    b.nav("3")
    b.A("DL_PRESENCE_SUMMARY", substring=b._resolve(
        "DL_PRESENCE_SUMMARY", {"present": 49, "total": 50,
                                "missing": 1}).split("49")[0],
        timeout=30, label="slot 3 arrival")
    b.flush()
    b.key("w", settle=1.4)
    b.A("WIZ_BORDER_TITLE", substring=b._resolve("WIZ_KIND_DATASETS"),
        timeout=20, label="dataset wizard opens")
    b.raw("demo-ds-walkthrough", settle=0.5)  # key
    b.key(TAB, settle=0.4)
    b.raw("datasets/GUE/emp_H3", settle=0.7)  # a real path (advisory shows)
    b.key(ENTER, settle=1.2)  # advance to step 2
    b.anchor("2/4", timeout=15, label="step 2")
    b.key("b", settle=1.2)  # back to step 1
    b.anchor("1/4", timeout=15, label="back on step 1")
    b.key(ENTER, settle=1.0)
    b.anchor("2/4", timeout=15, label="forward again")
    b.key(ESC, settle=1.2)  # cancel with values filled
    b.A("WIZ_CANCEL_CONFIRM", substring=b._resolve(
        "WIZ_CANCEL_CONFIRM", {"n": 1}).split("1")[0], timeout=15,
        label="cancel confirm")
    b.key(ENTER, settle=1.0)  # discard (a plain confirm: enter confirms)
    # model wizard (slot 2): open, one step, esc (the demo custom entry
    # was landed through the real onboarding service before recording —
    # RECORDED.md documents it; the prefilled edit form over that row is
    # the custom-entries scene's footage)
    b.nav("2")
    b.A("SEL_SCREEN_TITLE_MODELS", timeout=30)
    b.key("w", settle=1.4)
    b.A("WIZ_BORDER_TITLE", substring=b._resolve("WIZ_KIND_MODELS"),
        timeout=20, label="model wizard opens")
    b.key(ENTER, settle=1.0)  # one step forward
    b.anchor("2/4", timeout=15, label="one step")
    b.key(ESC, settle=0.8)  # blank form cancels silently
    b.note("dataset wizard with real field edits (enter/b, esc-cancel, "
           "nothing landed); model wizard open/step/esc over the blank "
           "form")


def scene_custom_entries(b: Builder, sc: ScanResult) -> None:
    if not sc.demo_custom_present:
        raise DriverError(
            f"custom entry {DEMO_CUSTOM_KEY} not present in the real "
            "config root — record the wizard scene (en) first")
    boot_prologue(b)
    if b.body_lang != b.lang:
        b.toggle_language(b.body_lang)
    b.nav("2")
    b.A("SEL_SCREEN_TITLE_MODELS", timeout=30)
    b.filter_position(DEMO_CUSTOM_KEY)  # stay filtered: e/w act on the row
    b.key("e", settle=1.2)  # disable
    b.A("SEL_TOGGLE_DISABLED_TOAST", fmt={"key": DEMO_CUSTOM_KEY},
        substring=b._resolve("SEL_TOGGLE_DISABLED_TOAST",
                             {"key": DEMO_CUSTOM_KEY}).split(
                                 DEMO_CUSTOM_KEY)[0],
        timeout=15, label="disabled toast")
    b.A("SEL_DISABLED_SUFFIX", timeout=15, label="disabled suffix")
    b.wait(0.8)
    b.key("e", settle=1.2)  # RESTORE on camera (PEX-3)
    b.A("SEL_TOGGLE_ENABLED_TOAST", fmt={"key": DEMO_CUSTOM_KEY},
        substring=b._resolve("SEL_TOGGLE_ENABLED_TOAST",
                             {"key": DEMO_CUSTOM_KEY}).split(
                                 DEMO_CUSTOM_KEY)[0],
        timeout=15, label="enabled toast")
    b.key("w", settle=1.4)  # prefilled edit form on the custom row
    b.A("WIZ_BORDER_TITLE", substring=b._resolve("WIZ_KIND_MODELS"),
        timeout=20, label="prefilled wizard")
    b.anchor(DEMO_CUSTOM_KEY, timeout=15, label="prefilled key")
    b.key(ESC, settle=1.0)
    b.A("WIZ_CANCEL_CONFIRM", substring=b._resolve(
        "WIZ_CANCEL_CONFIRM", {"n": 1}).split("1")[0], timeout=15,
        label="cancel confirm")
    b.key(ENTER, settle=1.0)
    b.note(f"e disables {DEMO_CUSTOM_KEY} (disabled suffix renders) and "
           "RESTORES it; w opens the prefilled edit form; esc discards")


SCENES: dict[str, Callable[[Builder, ScanResult], None]] = {
    "env-check": scene_env_check,
    "selection-presets": scene_selection_presets,
    "model-download": scene_model_download,
    "dataset-download": scene_dataset_download,
    "run-config-preview": scene_run_config_preview,
    "launch-monitor-kill": scene_launch_monitor_kill,
    "rerun-from-failures": scene_rerun_from_failures,
    "language-toggle": scene_language_toggle,
    "wizard": scene_wizard,
    "custom-entries": scene_custom_entries,
}

SCENE_BLURBS = {
    "env-check": "8 kernels live on boot (fresh state), r re-run, drill-down",
    "selection-presets": "marks, registry-grammar filter, preset apply/save, "
                         "59x50 presence matrix",
    "model-download": "REAL ModelScope model download (live-scan target) "
                      "with percent + rate, flip",
    "dataset-download": "REAL ModelScope dataset download, queue percent + "
                        "bar + rate, reconcile flip, drill-down",
    "run-config-preview": "picker marks, seeds/epochs/output-root edits, "
                          "verbatim dry-run argv preview",
    "launch-monitor-kill": "real fast-failure launch, y-gate (enter inert), "
                           "EHC-3 refusal, live monitor, log tail, q->k kill",
    "rerun-from-failures": "attach, real failures modal, r->y rerun driven "
                           "to completion",
    "language-toggle": "the L live toggle, full re-render, restored",
    "wizard": "dataset wizard edits + cancel; model wizard (en lands a real "
              "custom entry through the gauntlet)",
    "custom-entries": "e disable/restore with the disabled suffix, w "
                      "prefilled edit form",
}


# =====================================================================
# The runner — pty spawn + the streaming relay
# =====================================================================

def _relay_pump(child, relay_state: dict) -> None:
    """The ONLY reader of the console pty: every chunk goes to stdout
    (what asciinema records) verbatim AND into the scan buffer."""
    import pexpect  # lazy: never imported in --dry-run / --list-scenes
    while True:
        try:
            chunk = child.read_nonblocking(size=65536, timeout=0.15)
        except pexpect.TIMEOUT:
            continue
        except (pexpect.EOF, OSError, ValueError):
            relay_state["eof"] = True
            return
        if not chunk:
            relay_state["eof"] = True
            return
        relay_state["buffer"].extend(chunk)
        sys.stdout.buffer.write(chunk)
        sys.stdout.buffer.flush()


def run_scene(scene: str, lang: str, args: argparse.Namespace) -> int:
    import pexpect  # lazy

    scan = run_scan()
    prep_notes = scene_prep(scene, lang, scan)
    state_dir = tempfile.mkdtemp(prefix=f"tui-demo-{scene}-{lang}-")
    meta = SceneMeta(scene=scene, lang=lang,
                     date=time.strftime("%Y-%m-%d"),
                     targets={
                         "model_target": scan.model_target,
                         "dataset_target": scan.dataset_target,
                         "demo_model": DEMO_MODEL,
                         "demo_task": DEMO_TASK,
                         "demo_seeds": DEMO_SEEDS_MAIN,
                         "demo_epochs": DEMO_EPOCHS,
                         "demo_root": DEMO_ROOT_ARG,
                         "demo_fail_root": DEMO_FAIL_ROOT_ARG,
                         "custom_key": (DEMO_CUSTOM_KEY
                                        if scan.demo_custom_present else None),
                     })
    meta.notes.extend(prep_notes)

    builder = Builder(boot_lang="en", body_lang=lang, speed=args.speed)
    SCENES[scene](builder, scan)
    builder.restore_boot_language()
    steps = builder.steps
    meta.notes.extend(builder.notes)

    env = dict(os.environ)
    env["DNALLMMARK_TUI_STATE_DIR"] = state_dir
    env["TERM"] = "xterm-256color"
    command = shlex_split(args.tui_cmd)
    started = time.time()
    child = pexpect.spawn(
        command[0], command[1:], dimensions=(TERMINAL_ROWS, TERMINAL_COLS),
        env=env, cwd=str(REPO_ROOT), encoding=None, timeout=5)

    relay_state = {"buffer": bytearray(), "search": 0, "eof": False}
    import threading
    pump = threading.Thread(
        target=_relay_pump, args=(child, relay_state), daemon=True)
    pump.start()

    exit_code = 0
    try:
        _run_steps(child, steps, relay_state, meta)
        _quit(child, relay_state, builder)
        _wait_eof(relay_state, timeout=60)
        child.close(force=True)
    except DriverError:
        exit_code = 2
        raise
    finally:
        meta.wall_seconds = round(time.time() - started, 1)
        screen_tail = relay_state.get("screen_tail")
        if isinstance(screen_tail, str):
            meta.notes.insert(0, "SCREEN AT FAILURE:\n" + screen_tail)
        _write_meta(meta, exit_code)
        shutil.rmtree(state_dir, ignore_errors=True)
        child.terminate(force=True)
    return exit_code


def shlex_split(value: str) -> list[str]:
    import shlex
    return shlex.split(value)


def _screen_tail(relay_state: dict, size: int = 2000) -> str:
    """A stripped, deduplicated tail of the rendered screen — the failure
    diagnostic (what the console was showing when an anchor died)."""
    import re as _re
    raw = bytes(relay_state["buffer"][-size * 8:])
    text = _re.sub(rb"\x1b\[[0-9;]*[A-Za-z]", b"", raw).decode(
        "utf-8", "replace")
    lines = [line.rstrip() for line in text.split("\r\n")]
    dedup: list[str] = []
    for line in lines:
        if line and (not dedup or dedup[-1] != line):
            dedup.append(line)
    return "\n".join(dedup[-24:])


def _wait_for(relay_state: dict, patterns: tuple[bytes, ...],
              timeout: float, label: str) -> int:
    """Search the relayed stream for the first pattern to appear; the
    search cursor (``search``) persists across anchors so each wait sees
    only text that arrived after the previous match — never stale frames
    from before it. (Distinct from the pump's arrival watermark: data can
    arrive between the cursor and the buffer end at any moment.)"""
    deadline = time.time() + timeout
    while True:
        buffer = relay_state["buffer"]
        start = relay_state["search"]
        for index, pattern in enumerate(patterns):
            found = buffer.find(pattern, start)
            if found >= 0:
                relay_state["search"] = found + len(pattern)
                return index
        if relay_state["eof"]:
            raise DriverError(
                f"console exited before anchor {label!r} appeared")
        if time.time() > deadline:
            relay_state["screen_tail"] = _screen_tail(relay_state)
            raise DriverError(
                f"anchor {label!r} not seen within {timeout:.0f}s "
                f"(patterns: {patterns!r})")
        time.sleep(0.1)


def _drain(relay_state: dict, seconds: float) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline and not relay_state["eof"]:
        time.sleep(0.1)


def _run_steps(child, steps: list[tuple], relay_state: dict,
               meta: SceneMeta) -> None:
    for step in steps:
        kind = step[0]
        if kind == "send":
            _, data, settle, _label = step
            child.send(data)
            _drain(relay_state, settle)
        elif kind == "anchor":
            _, patterns, timeout, label = step
            _wait_for(relay_state, patterns, timeout, label)
        elif kind == "branch":
            _, patterns, actions, timeout, label = step
            index = _wait_for(relay_state, patterns, timeout, label)
            action = actions[index]
            if action:
                child.send(action.encode("utf-8"))
                _drain(relay_state, 1.2)
        elif kind == "wait":
            _, seconds, _label = step
            _drain(relay_state, seconds)
        elif kind == "flush":
            relay_state["search"] = len(relay_state["buffer"])


def _quit(child, relay_state: dict, builder: Builder) -> None:
    """q (ESC-prefixed, own-write ESC — never Alt+q); if a live sweep
    pushes the exit modal, RAW k kills it (esc would dismiss the modal —
    never prefix k). A direct quit shows no modal: the wait then ends at
    EOF, which _wait_for surfaces as its exited-before-anchor error —
    that specific outcome is the SUCCESS path, so it is caught here."""
    S.set_language(builder.boot_lang)
    exit_prefix = S.LNC_EXIT_MESSAGE.format(
        done="0", total="0", root="x").split("0")[0].encode("utf-8")
    for attempt in range(2):
        child.send(ESC.encode())
        _drain(relay_state, 0.8)
        child.send(b"q")
        try:
            _wait_for(relay_state, (exit_prefix,),
                      timeout=15, label="quit")
            break
        except DriverError as error:
            if "console exited before" in str(error):
                return  # the clean direct quit — no live sweep, no modal
            if attempt:  # second failure: a modal may have eaten the q
                raise
    child.send(b"k")  # the exit modal is up: RAW k kills the live sweep
    _wait_eof(relay_state, timeout=120)


def _wait_eof(relay_state: dict, timeout: float) -> None:
    deadline = time.time() + timeout
    while not relay_state["eof"] and time.time() < deadline:
        time.sleep(0.2)
    if not relay_state["eof"]:
        raise DriverError("console did not exit after quit")


def _write_meta(meta: SceneMeta, exit_code: int) -> None:
    DOCS_DEMO_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "scene": meta.scene, "lang": meta.lang, "date": meta.date,
        "boot_lang": meta.boot_lang, "wall_seconds": meta.wall_seconds,
        "notes": meta.notes, "targets": meta.targets,
        "exit_code": exit_code,
    }
    path = DOCS_DEMO_DIR / f".meta-{meta.scene}-{meta.lang}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                    encoding="utf-8")


# =====================================================================
# RECORDED.md — the honesty ledger
# =====================================================================

def _human(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / 1024 / 1024:.1f} MB"
    return f"{size / 1024:.1f} KB"


def recorded_row(scene: str, lang: str) -> None:
    """Refresh one RECORDED.md row from the recording's meta sidecar plus
    the on-disk cast/gif sizes (called by record.sh after agg renders)."""
    meta_path = DOCS_DEMO_DIR / f".meta-{scene}-{lang}.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    cast = DOCS_DEMO_DIR / "casts" / f"{scene}-{lang}.cast"
    gif = DOCS_DEMO_DIR / "gifs" / f"{scene}-{lang}.gif"
    notes = "; ".join(meta.get("notes", []))
    targets = meta.get("targets", {})
    real = ", ".join(
        f"{key}={value}" for key, value in targets.items() if value)
    row = (f"| {scene} | {lang} | {real} — {notes} "
           f"| casts/{cast.name} ({_human(cast.stat().st_size)}) "
           f"| gifs/{gif.name} ({_human(gif.stat().st_size)}) "
           f"| {meta.get('date', '')} |")
    header = [
        "# TUI demo recording ledger",
        "",
        "Every row states what the GIF truly shows: the real targets the",
        "live presence scan chose, the resets applied before spawn (the",
        "re-record lever), and honest notes for anything that degraded.",
        "Regenerate any row: `scripts/demo/record.sh <scene> <lang> [speed]`.",
        "",
        "Scene | Lang | Real targets / what actually happened | Cast | GIF | Date",
        "|---|---|---|---|---|---|",
    ]
    if not RECORDED_MD.is_file():
        RECORDED_MD.write_text("\n".join(header) + "\n", encoding="utf-8")
    lines = RECORDED_MD.read_text(encoding="utf-8").splitlines()
    prefix = f"| {scene} | {lang} |"
    kept = [line for line in lines if not line.startswith(prefix)]
    kept.append(row)
    kept.append("")
    RECORDED_MD.write_text("\n".join(kept) + "\n", encoding="utf-8")


# =====================================================================
# CLI
# =====================================================================

def _dry_run(scene: str, lang: str, args: argparse.Namespace) -> int:
    scan = run_scan()
    builder = Builder(boot_lang="en", body_lang=lang, speed=args.speed)
    SCENES[scene](builder, scan)
    builder.restore_boot_language()
    print(f"scene={scene} lang={lang} speed={args.speed}")
    print(f"scan: model_target={scan.model_target} "
          f"dataset_target={scan.dataset_target} "
          f"missing_datasets={scan.missing_datasets} "
          f"customs={scan.custom_keys}")
    print(f"{len(builder.steps)} steps "
          f"(boot_lang=en body_lang={lang} end_lang={builder.lang}):")
    for index, step in enumerate(builder.steps, start=1):
        kind = step[0]
        if kind == "send":
            _, data, settle, label = step
            shown = data.decode("utf-8", "replace")
            shown = shown.replace("\x1b", "ESC").replace(
                "\r", "ENTER").replace("\t", "TAB")
            print(f"  {index:3d}.    {shown!r}"
                  f"  (settle {settle:.1f}s) {label}")
        elif kind in ("anchor", "branch"):
            timeout = step[2] if kind == "anchor" else step[3]
            label = step[3] if kind == "anchor" else step[4]
            print(f"  {index:3d}. {kind:7s} {label!r} "
                  f"(timeout {timeout:.0f}s)")
        elif kind == "flush":
            print(f"  {index:3d}. flush   (ignore all prior output)")
        else:
            _, seconds, label = step
            print(f"  {index:3d}. wait    {seconds:.1f}s {label}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="The deterministic TUI demo scene driver.")
    parser.add_argument("--scene", choices=sorted(SCENES))
    parser.add_argument("--lang", choices=["en", "zh"], default="en")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the scene timeline without spawning")
    parser.add_argument("--list-scenes", action="store_true")
    parser.add_argument(
        "--tui-cmd",
        default="uv run --group tui --group gpu python -m tui",
        help="the console launch command (default: the make tui form)")
    parser.add_argument(
        "--speed", type=float, default=1.0,
        help="driver pacing multiplier for settles/waits (agg playback "
        "speed is record.sh's concern)")
    parser.add_argument("--recorded-row", metavar="SCENE",
                        help="refresh the RECORDED.md row (post-record)")
    args = parser.parse_args(argv)

    if args.list_scenes:
        for name in SCENES:
            print(f"{name:22s} {SCENE_BLURBS[name]}")
        return 0
    if args.recorded_row:
        recorded_row(args.recorded_row, args.lang)
        return 0
    if not args.scene:
        parser.error("--scene is required (or --list-scenes)")
    if args.dry_run:
        return _dry_run(args.scene, args.lang, args)
    return run_scene(args.scene, args.lang, args)


if __name__ == "__main__":
    raise SystemExit(main())
