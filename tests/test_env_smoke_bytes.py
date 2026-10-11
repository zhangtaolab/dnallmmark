"""
Golden byte-characterization suite for ``pipeline/env_smoke.py``
(Phase 8, plan 08-01 / D-02, ENV-01).

Why these bytes are load-bearing:

- **D-02 (ENV-01)**: the Phase 8 TUI env-check services IMPORT the
  env_smoke kernels and consume structured results; the CLI stdout is at
  the same time the E2' maintainer dual gate's greppable contract. Any
  byte drift in what that gate greps silently changes what the gate
  measures, so this suite pins the FULL stdout (and the 0/1 exit int)
  BEFORE the structured-return refactor — it is a characterization suite
  and must pass against the UNMODIFIED module — and must stay green
  through and after the refactor.
- The three source-grep contract tests in
  ``tests/test_run_finetune_contracts.py`` pin the same file's strings
  and wiring from the source side; this suite pins the rendered output
  side. Together they box the refactor in from both directions.

Pinned scenarios (full-stdout byte equality, never line presence):

- **S1 all-pass**: import seams monkeypatched with fake modules whose
  ``__version__`` values match the current pyproject ``[gpu]`` pins
  (torch carries its ``+cu130`` local suffix on purpose so the
  release-segment comparison path is the one exercised); a fake
  CUDA-visible torch (1 device, controlled name/memory) and a successful
  matmul; a synthetic all-present dataset registry -> exit 0, PASS
  trailer.
- **S2 torch-missing**: the torch import seam raises ImportError -> the
  torch-unavailable FAIL line renders in its exact slot (after peft,
  before numpy), cuda and matmul yield failed results with no output of
  their own, exit 1, FAIL trailer with the 3-group count.
- **S3 dataset-missing**: synthetic registry with 2 of 3 dirs missing,
  one carrying the double-nested note continuation line -> verbatim
  indented missing-list block, exit 1.

Determinism seams (machine-independent, CPU-only — CI-safe):

- ``env_smoke.REPO_ROOT`` is pinned to a sentinel path because the
  header line embeds the absolute repo path (the real pyproject is still
  read through the module-bound ``PYPROJECT_PATH`` — pin/floor lines
  exercise the real parser).
- fake modules are injected through ``sys.modules``, which covers BOTH
  import paths in the module: the ``importlib.import_module`` seam and
  main()'s literal ``import torch`` statement. For S2,
  ``sys.modules["torch"] = None`` is the import system's documented
  halt sentinel — both import sites raise the same deterministic
  ImportError on any host, GPU stack present or not.
- ``DATASETS_INFO_PATH`` / ``DATASETS_ROOT`` are pointed at a synthetic
  tmp registry (double-nested sibling dirs materialized on demand).

See also:
    ``pipeline/env_smoke.py`` — the module under characterization.
    ``tests/test_run_finetune_contracts.py`` — the three source-grep
    contract tests over the same file (left untouched by D-02).
"""

import contextlib
import io
import json
import sys
import types
from pathlib import Path
from typing import cast

import env_smoke  # conftest puts pipeline/ on sys.path

# The header line embeds REPO_ROOT (absolute, host-specific) — pin it so
# the golden bytes are checkout-independent. PYPROJECT_PATH stays real:
# the pin/floor lines below exercise the actual pyproject parser.
PINNED_REPO_ROOT = Path("/pin/dnallmmark")

# Fake-module facts. The __version__ values MATCH the current pyproject
# [gpu] pins (torch==2.11.0, transformers==5.17.0) so S1's version-pin
# lines PASS; torch deliberately carries the +cu130 local suffix so the
# release-segment comparison (installed 2.11.0+cu130 vs pin 2.11.0) is
# the exercised path. A future pin bump legitimately breaks this golden
# — updating the literals here is the intended maintenance act.
FAKE_TORCH_VERSION = "2.11.0+cu130"
FAKE_TRANSFORMERS_VERSION = "5.17.0"
FAKE_PEFT_VERSION = "0.21.2"
FAKE_NUMPY_VERSION = "2.5.3"
FAKE_DATASETS_VERSION = "4.58.2"
FAKE_PYARROW_VERSION = "22.0.0"
FAKE_DEVICE_NAME = "Fake GPU GB10"
FAKE_DEVICE_BYTES = 128 * 1024 ** 3  # -> "128.0 GiB" under the :.1f format


class _FakeCudaProps:
    name = FAKE_DEVICE_NAME
    total_memory = FAKE_DEVICE_BYTES


class _FakeCuda:
    @staticmethod
    def is_available():
        return True

    @staticmethod
    def device_count():
        return 1

    @staticmethod
    def get_device_properties(idx):
        assert idx == 0, "device_count() is 1 — only device 0 is queried"
        return _FakeCudaProps()


class _FakeMatmulSum:
    def sum(self):
        return self

    def item(self):
        # 8x8 all-ones matmul: every entry is 8 (dot of two 8-long ones
        # vectors), 64 entries -> 512.0 (the derived, non-magic constant).
        return 512.0


class _FakeOnesTensor:
    def __matmul__(self, other):
        return _FakeMatmulSum()


def _fake_ones(*args):
    return _FakeOnesTensor()


def _fake_module(name, version=None, origin=None):
    """Build one deterministic fake module for the sys.modules seam.

    Args:
        name (str): The module's ``__name__``.
        version (str | None): Optional controlled ``__version__``.
        origin (str | None): Optional controlled ``__file__`` (defaults
            to a ``/fake/site-packages/...`` path).

    Returns:
        types.ModuleType: The fake module.
    """
    module = types.ModuleType(name)
    module.__file__ = (
        origin if origin is not None
        else f"/fake/site-packages/{name}/__init__.py"
    )
    if version is not None:
        # Assignment form (`module.__version__ = ...`) is the ty conflict
        # this exists to avoid: ty resolves that literal dunder write as
        # an undeclared ModuleType attribute.
        setattr(module, "__version__", version)  # noqa: B010
    return module


def _fake_torch():
    """Build the S1/S3 torch fake: CUDA-visible, 1 device, matmul-ready."""
    torch = _fake_module("torch", version=FAKE_TORCH_VERSION)
    torch.cuda = _FakeCuda
    torch.ones = _fake_ones
    return torch


# Synthetic dataset registry (3 tasks; S3 leaves b absent entirely and c
# present only in its double-nested suite/suite/task form).
SYNTHETIC_REGISTRY = {
    "fake_task_a": {"Dataset_path": "datasets/suite_a/task_a"},
    "fake_task_b": {"Dataset_path": "datasets/suite_b/task_b"},
    "fake_task_c": {"Dataset_path": "datasets/suite_c/task_c"},
}


def _run_scenario(mode, monkeypatch, tmp_path, capsys=None):
    """Run ``env_smoke.main()`` under one fully pinned scenario.

    Args:
        mode (str): ``"all_pass"``, ``"torch_missing"``, or
            ``"dataset_missing"``.
        monkeypatch: The pytest monkeypatch fixture (or a MonkeyPatch
            instance on the recording path).
        tmp_path (Path): Directory for the synthetic dataset registry.
        capsys: The pytest capsys fixture when running under pytest;
            ``None`` captures via ``contextlib.redirect_stdout``
            instead (identical bytes — the recording path used to
            produce the EXPECTED_* literals below).

    Returns:
        tuple[str, int]: (full captured stdout, main()'s return value).
    """
    datasets_root = tmp_path / "datasets"
    info_path = tmp_path / "datasets_info.json"
    info_path.write_text(json.dumps(SYNTHETIC_REGISTRY), encoding="utf-8")
    if mode in ("all_pass", "torch_missing"):
        for suite, task in (
            ("suite_a", "task_a"),
            ("suite_b", "task_b"),
            ("suite_c", "task_c"),
        ):
            (datasets_root / suite / task).mkdir(parents=True)
    elif mode == "dataset_missing":
        (datasets_root / "suite_a" / "task_a").mkdir(parents=True)
        # suite_c/task_c stays absent, but its double-nested sibling
        # exists — the fresh-unzip layout the note names.
        (datasets_root / "suite_c" / "suite_c" / "task_c").mkdir(parents=True)
    else:
        raise ValueError(f"unknown scenario mode: {mode!r}")

    monkeypatch.setattr(env_smoke, "REPO_ROOT", PINNED_REPO_ROOT)
    monkeypatch.setattr(env_smoke, "DATASETS_INFO_PATH", info_path)
    monkeypatch.setattr(env_smoke, "DATASETS_ROOT", datasets_root)
    for name, module in (
        ("transformers", _fake_module(
            "transformers", version=FAKE_TRANSFORMERS_VERSION)),
        ("dnallm", _fake_module("dnallm")),
        ("peft", _fake_module("peft", version=FAKE_PEFT_VERSION)),
        ("numpy", _fake_module("numpy", version=FAKE_NUMPY_VERSION)),
        ("datasets", _fake_module(
            "datasets", version=FAKE_DATASETS_VERSION)),
        ("pyarrow", _fake_module(
            "pyarrow", version=FAKE_PYARROW_VERSION)),
    ):
        monkeypatch.setitem(sys.modules, name, module)
    if mode == "torch_missing":
        # sys.modules values are typed ModuleType; None is the import
        # system's documented halt sentinel (both import sites in
        # env_smoke raise the same deterministic ImportError).
        monkeypatch.setitem(
            sys.modules, "torch", cast(types.ModuleType, None))
    else:
        monkeypatch.setitem(sys.modules, "torch", _fake_torch())

    if capsys is not None:
        rc = env_smoke.main()
        return capsys.readouterr().out, rc
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        rc = env_smoke.main()
    return buffer.getvalue(), rc


# ===== Golden expectations =====
#
# Recorded by RUNNING _run_scenario() against the UNMODIFIED module (the
# redirect_stdout recording path) — never transcribed from memory. The
# line ORDER is contract: kernel blocks in main()'s call order, the INFO
# diagnostics line after numpy and before dataset dirs, the torch
# gate's two FAIL lines (when torch is missing) between peft and numpy,
# trailer last. Any drift here is a gate-contract change, not cosmetics.

EXPECTED_S1_ALL_PASS = """\
=== PIPE-02 env smoke (dnallmmark @ /pin/dnallmmark) ===
PASS: import torch resolves (/fake/site-packages/torch/__init__.py)
PASS: torch 2.11.0 == pyproject [gpu] pin
PASS: import transformers resolves (/fake/site-packages/transformers/__init__.py)
PASS: transformers 5.17.0 == pyproject [gpu] pin
PASS: import dnallm resolves (/fake/site-packages/dnallm/__init__.py)
PASS: peft 0.21.2 importable (SC-6 LoRA/IA3 lanes; suite floor peft>=0.14.0)
PASS: CUDA available, 1 device(s)
PASS: device 0: Fake GPU GB10, 128.0 GiB total memory
PASS: small-tensor matmul executed (sum == 512.0)
PASS: import numpy resolves (/fake/site-packages/numpy/__init__.py)
PASS: numpy 2.5.3 >= pyproject floor (major >= 2; dnallm 1.2.1 requires numpy>=2)
INFO (not gated): datasets 4.58.2, pyarrow 22.0.0 (dnallm 1.2.1 caps datasets<=5.1.0, no pyarrow pin — dnallm's own constraints govern resolution)
PASS: all 3 registry dataset dir(s) present on disk
=== SMOKE RESULT: PASS (all checks green) ===
"""

EXPECTED_S2_TORCH_MISSING = """\
=== PIPE-02 env smoke (dnallmmark @ /pin/dnallmmark) ===
FAIL: import torch — ModuleNotFoundError: import of torch halted; None in sys.modules
PASS: import transformers resolves (/fake/site-packages/transformers/__init__.py)
PASS: transformers 5.17.0 == pyproject [gpu] pin
PASS: import dnallm resolves (/fake/site-packages/dnallm/__init__.py)
PASS: peft 0.21.2 importable (SC-6 LoRA/IA3 lanes; suite floor peft>=0.14.0)
FAIL: import torch — ModuleNotFoundError: import of torch halted; None in sys.modules
FAIL: torch unavailable — CUDA + matmul checks not run
PASS: import numpy resolves (/fake/site-packages/numpy/__init__.py)
PASS: numpy 2.5.3 >= pyproject floor (major >= 2; dnallm 1.2.1 requires numpy>=2)
INFO (not gated): datasets 4.58.2, pyarrow 22.0.0 (dnallm 1.2.1 caps datasets<=5.1.0, no pyarrow pin — dnallm's own constraints govern resolution)
PASS: all 3 registry dataset dir(s) present on disk
=== SMOKE RESULT: FAIL (3 check group(s) failed) ===
"""

EXPECTED_S3_DATASET_MISSING = """\
=== PIPE-02 env smoke (dnallmmark @ /pin/dnallmmark) ===
PASS: import torch resolves (/fake/site-packages/torch/__init__.py)
PASS: torch 2.11.0 == pyproject [gpu] pin
PASS: import transformers resolves (/fake/site-packages/transformers/__init__.py)
PASS: transformers 5.17.0 == pyproject [gpu] pin
PASS: import dnallm resolves (/fake/site-packages/dnallm/__init__.py)
PASS: peft 0.21.2 importable (SC-6 LoRA/IA3 lanes; suite floor peft>=0.14.0)
PASS: CUDA available, 1 device(s)
PASS: device 0: Fake GPU GB10, 128.0 GiB total memory
PASS: small-tensor matmul executed (sum == 512.0)
PASS: import numpy resolves (/fake/site-packages/numpy/__init__.py)
PASS: numpy 2.5.3 >= pyproject floor (major >= 2; dnallm 1.2.1 requires numpy>=2)
INFO (not gated): datasets 4.58.2, pyarrow 22.0.0 (dnallm 1.2.1 caps datasets<=5.1.0, no pyarrow pin — dnallm's own constraints govern resolution)
FAIL: 2 of 3 registry dataset dir(s) missing on disk (the E2' launch gate):
  - fake_task_b
  - fake_task_c  [double-nested: the fresh-unzip suite/suite/task layout needs flattening]
=== SMOKE RESULT: FAIL (1 check group(s) failed) ===
"""


# ===== Scenario tests (full-stdout byte equality + exit ints) =====

def test_s1_all_pass_stdout_is_byte_exact(capsys, monkeypatch, tmp_path):
    """S1: every check green -> byte-exact stdout, exit int 0."""
    out, rc = _run_scenario("all_pass", monkeypatch, tmp_path, capsys)
    assert out == EXPECTED_S1_ALL_PASS
    assert isinstance(rc, int) and rc == 0


def test_s2_torch_missing_stdout_is_byte_exact(capsys, monkeypatch, tmp_path):
    """S2: torch import fails -> unavailable FAIL line in slot, exit 1."""
    out, rc = _run_scenario("torch_missing", monkeypatch, tmp_path, capsys)
    assert out == EXPECTED_S2_TORCH_MISSING
    assert isinstance(rc, int) and rc == 1


def test_s3_dataset_missing_stdout_is_byte_exact(capsys, monkeypatch, tmp_path):
    """S3: missing dataset dirs -> verbatim indented block, exit 1."""
    out, rc = _run_scenario("dataset_missing", monkeypatch, tmp_path, capsys)
    assert out == EXPECTED_S3_DATASET_MISSING
    assert isinstance(rc, int) and rc == 1
