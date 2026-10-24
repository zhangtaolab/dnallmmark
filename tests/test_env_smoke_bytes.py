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
  matmul; synthetic all-present model + dataset registries -> exit 0,
  PASS trailer.
- **S2 torch-missing**: the torch import seam raises ImportError -> the
  torch-unavailable FAIL line renders in its exact slot (after peft,
  before numpy), cuda and matmul yield failed results with no output of
  their own, exit 1, FAIL trailer with the 3-group count (the directory
  kernels are not torch-gated and pass).
- **S3 dataset-missing**: synthetic registry with 2 of 3 dirs missing,
  one carrying the double-nested note continuation line -> verbatim
  indented missing-list block, exit 1 (the model-dirs kernel passes —
  the 261014-dcl eighth line precedes the dataset block).
- **S4 override-root (KERNEL level, never main())**: both directory
  kernels called with an explicit ``root`` over tmp dirs — the headline
  annotation names the root as given, the join is VERBATIM (a root
  without a trailing separator still yields exactly one separator), and
  missing model dirs list by name in sorted-key order (261014-dcl).

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
- ``PIPELINE_DIR`` is pinned at a synthetic tmp pipeline dir with BOTH
  info-file module attrs (``MODELS_INFO_PATH`` / ``DATASETS_INFO_PATH``)
  pointing into that layout — the registry-relative joins resolve
  against the pinned dir, and the default-branch root annotation is the
  FIXED `` (root: pipeline/)`` token, so the goldens stay
  checkout-independent (double-nested sibling dirs materialized on
  demand).

See also:
    ``pipeline/env_smoke.py`` — the module under characterization.
    ``tests/test_run_finetune_contracts.py`` — the three source-grep
    contract tests over the same file (left untouched by D-02).
"""

import contextlib
import io
import json
import os
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

# Synthetic model registry (3 models, all present in every scenario —
# the 261014-dcl model_dirs kernel passes ahead of the dataset block).
SYNTHETIC_MODELS_REGISTRY = {
    "fake_model_a": {"Model_path": "models/fake/model_a"},
    "fake_model_b": {"Model_path": "models/fake/model_b"},
    "fake_model_c": {"Model_path": "models/fake/model_c"},
}


def _run_scenario(mode, monkeypatch, tmp_path, capsys=None):
    """Run ``env_smoke.main()`` under one fully pinned scenario.

    Args:
        mode (str): ``"all_pass"``, ``"torch_missing"``, or
            ``"dataset_missing"``.
        monkeypatch: The pytest monkeypatch fixture (or a MonkeyPatch
            instance on the recording path).
        tmp_path (Path): Directory for the synthetic pipeline layout
            (both info files + materialized models/ and datasets/ dirs).
        capsys: The pytest capsys fixture when running under pytest;
            ``None`` captures via ``contextlib.redirect_stdout``
            instead (identical bytes — the recording path used to
            produce the EXPECTED_* literals below).

    Returns:
        tuple[str, int]: (full captured stdout, main()'s return value).
    """
    pipeline_dir = tmp_path / "pipeline"
    datasets_root = pipeline_dir / "datasets"
    models_root = pipeline_dir / "models"
    pipeline_dir.mkdir(parents=True)
    (pipeline_dir / "models_info.json").write_text(
        json.dumps(SYNTHETIC_MODELS_REGISTRY), encoding="utf-8")
    info_path = pipeline_dir / "datasets_info.json"
    info_path.write_text(json.dumps(SYNTHETIC_REGISTRY), encoding="utf-8")
    for model in ("model_a", "model_b", "model_c"):
        (models_root / "fake" / model).mkdir(parents=True)
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
    monkeypatch.setattr(env_smoke, "PIPELINE_DIR", pipeline_dir)
    monkeypatch.setattr(env_smoke, "MODELS_INFO_PATH",
                        pipeline_dir / "models_info.json")
    monkeypatch.setattr(env_smoke, "DATASETS_INFO_PATH", info_path)
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
PASS: all 3 registry model dir(s) present on disk (root: pipeline/)
PASS: all 3 registry dataset dir(s) present on disk (root: pipeline/)
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
PASS: all 3 registry model dir(s) present on disk (root: pipeline/)
PASS: all 3 registry dataset dir(s) present on disk (root: pipeline/)
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
PASS: all 3 registry model dir(s) present on disk (root: pipeline/)
FAIL: 2 of 3 registry dataset dir(s) missing on disk (the E2' launch gate) (root: pipeline/):
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


def test_s4_override_root_annotation_verbatim_join_and_missing_listing(
        monkeypatch, tmp_path):
    """S4 (KERNEL level, 261014-dcl — never main()): an explicit override
    root redirects BOTH directory kernels — the headline annotation names
    the root exactly as given, the join is VERBATIM (a root without a
    trailing separator still yields exactly one separator before the
    registry value's own prefix), and missing model dirs list by name in
    sorted-key order."""
    pipeline_dir = tmp_path / "pipeline"
    pipeline_dir.mkdir()
    (pipeline_dir / "models_info.json").write_text(json.dumps({
        "fake_model_b": {"Model_path": "models/store/model_b"},
        "fake_model_a": {"Model_path": "models/store/model_a"},
    }), encoding="utf-8")
    (pipeline_dir / "datasets_info.json").write_text(json.dumps({
        "fake_task_a": {"Dataset_path": "datasets/store/task_a"},
    }), encoding="utf-8")
    monkeypatch.setattr(env_smoke, "MODELS_INFO_PATH",
                        pipeline_dir / "models_info.json")
    monkeypatch.setattr(env_smoke, "DATASETS_INFO_PATH",
                        pipeline_dir / "datasets_info.json")
    # the store root is given WITHOUT a trailing separator on purpose —
    # the verbatim-join pin (exactly one separator ever joins root and
    # registry value, the 261014-c2l run_finetune semantics).
    store = tmp_path / "store"
    (store / "models" / "store" / "model_a").mkdir(parents=True)
    (store / "datasets" / "store" / "task_a").mkdir(parents=True)
    # fake_model_b's dir stays absent — the missing-listing leg.

    models_result = env_smoke.check_model_dirs(root=str(store))
    assert models_result.name == "model_dirs"
    assert models_result.ok is False
    assert models_result.lines == (
        (f"FAIL: 1 of 2 registry model dir(s) missing on disk "
         f"(root: {store}):"),
        "  - fake_model_b",  # sorted-key order, exactly one listing line
    )

    datasets_result = env_smoke.check_dataset_dirs(root=str(store))
    assert datasets_result.name == "dataset_dirs"
    assert datasets_result.ok is True
    assert datasets_result.lines == (
        (f"PASS: all 1 registry dataset dir(s) present on disk "
         f"(root: {store})"),
    )

    # the helper-level verbatim-join pin: the override branch rstrips
    # then appends exactly one separator; the default branch resolves
    # against the module's own pipeline dir.
    assert env_smoke._effective_base(str(store)) == f"{store}{os.sep}"
    assert env_smoke._effective_base(None) == (
        f"{env_smoke.PIPELINE_DIR}{os.sep}")


# ===== 08-08 WR-01: the directory kernels degrade fail-closed =====

def test_directory_kernels_degrade_fail_closed_on_corrupt_registry(
        monkeypatch, tmp_path):
    """A missing or corrupt official registry yields a named ok=False
    CheckResult from BOTH directory kernels — ONE FAIL line in the
    main() torch-gate wording shape (the registry file, then the
    exception type + message) — so the E2' gate stays fail-closed and
    deterministic, never a traceback on exactly the broken-checkout
    state it exists to diagnose."""
    corrupt = tmp_path / "corrupt_info.json"
    corrupt.write_text("{ not json", encoding="utf-8")
    absent = tmp_path / "absent_info.json"

    # corrupt JSON: the JSONDecodeError branch on both kernels
    monkeypatch.setattr(env_smoke, "MODELS_INFO_PATH", corrupt)
    monkeypatch.setattr(env_smoke, "DATASETS_INFO_PATH", corrupt)
    models_result = env_smoke.check_model_dirs()
    assert models_result.name == "model_dirs"
    assert models_result.ok is False
    assert len(models_result.lines) == 1  # ONE FAIL line
    line = models_result.lines[0]
    assert line.startswith("FAIL: ")
    assert str(corrupt) in line
    assert "JSONDecodeError" in line
    # the exception message rides along (this corrupt content's own
    # parser wording — "{ not json" fails at the first property name)
    assert "Expecting property name" in line

    datasets_result = env_smoke.check_dataset_dirs()
    assert datasets_result.name == "dataset_dirs"
    assert datasets_result.ok is False
    assert len(datasets_result.lines) == 1
    line = datasets_result.lines[0]
    assert line.startswith("FAIL: ")
    assert str(corrupt) in line
    assert "JSONDecodeError" in line

    # the OSError branch of the same guard: a nonexistent registry path
    monkeypatch.setattr(env_smoke, "MODELS_INFO_PATH", absent)
    monkeypatch.setattr(env_smoke, "DATASETS_INFO_PATH", absent)
    models_missing = env_smoke.check_model_dirs()
    assert models_missing.ok is False
    assert str(absent) in models_missing.lines[0]
    assert "FileNotFoundError" in models_missing.lines[0]
    datasets_missing = env_smoke.check_dataset_dirs()
    assert datasets_missing.ok is False
    assert str(absent) in datasets_missing.lines[0]
    assert "FileNotFoundError" in datasets_missing.lines[0]


def test_directory_kernels_fail_closed_on_non_dict_top_level_registry(
        monkeypatch, tmp_path):
    """A readable, valid-JSON registry whose top level is NOT an object
    — a top-level list or null, a plausible hand-edit or bad-merge state
    of a broken checkout — yields the SAME named one-line FAIL result
    from BOTH directory kernels (WR-01, 261016-a4f): the registry path,
    then ``not a JSON object (top-level {type})``. The kernels can never
    traceback on ``sorted()``/entry access again, so the E2' gate
    renders its FAIL line + trailer and exits 1 deterministically."""
    list_registry = tmp_path / "list_info.json"
    list_registry.write_text(
        json.dumps([{"Model_path": "models/a/b"}]), encoding="utf-8")
    null_registry = tmp_path / "null_info.json"
    null_registry.write_text("null", encoding="utf-8")

    for path, type_name in (
        (list_registry, "list"),
        (null_registry, "NoneType"),
    ):
        for module_attr, kernel, kernel_id in (
            ("MODELS_INFO_PATH", env_smoke.check_model_dirs, "model_dirs"),
            ("DATASETS_INFO_PATH",
             env_smoke.check_dataset_dirs, "dataset_dirs"),
        ):
            monkeypatch.setattr(env_smoke, module_attr, path)
            result = kernel()
            assert result.name == kernel_id
            assert result.ok is False
            assert len(result.lines) == 1  # ONE named FAIL line
            line = result.lines[0]
            assert line.startswith("FAIL: read registry")
            assert str(path) in line
            assert "not a JSON object" in line
            assert f"top-level {type_name}" in line


def test_directory_kernels_count_shape_broken_entries_as_missing(
        monkeypatch, tmp_path):
    """Broken registry ENTRY shapes read as fail-closed missing
    (cannot-verify = missing): a non-dict entry, an entry lacking its
    path field, AND an entry with an EMPTY path string (WR-02,
    261016-a4f — ``base + ""`` resolves to the existing base dir, so
    the model kernel previously rendered a false all-present PASS) all
    join the FAIL missing listing BY NAME, while a healthy entry
    renders exactly as before (present, never listed)."""
    (tmp_path / "models_info.json").write_text(json.dumps({
        "m-healthy": {"Model_path": "models/m/healthy"},
        "m-emptypath": {"Model_path": ""},
        "m-nondict": [1, 2],
        "m-nopath": {},
    }), encoding="utf-8")
    (tmp_path / "datasets_info.json").write_text(json.dumps({
        "d-healthy": {"Dataset_path": "datasets/d/healthy"},
        "d-emptypath": {"Dataset_path": ""},
        "d-nondict": [1, 2],
        "d-nopath": {},
    }), encoding="utf-8")
    (tmp_path / "models" / "m" / "healthy").mkdir(parents=True)
    (tmp_path / "datasets" / "d" / "healthy").mkdir(parents=True)
    monkeypatch.setattr(env_smoke, "MODELS_INFO_PATH",
                        tmp_path / "models_info.json")
    monkeypatch.setattr(env_smoke, "DATASETS_INFO_PATH",
                        tmp_path / "datasets_info.json")

    # the S4 kernel-level precedent: an explicit root so the healthy
    # dirs resolve against the tmp layout, annotation names the root
    models_result = env_smoke.check_model_dirs(root=str(tmp_path))
    assert models_result.ok is False
    assert models_result.lines == (
        (f"FAIL: 3 of 4 registry model dir(s) missing on disk "
         f"(root: {tmp_path}):"),
        "  - m-emptypath",
        "  - m-nondict",
        "  - m-nopath",
    )

    datasets_result = env_smoke.check_dataset_dirs(root=str(tmp_path))
    assert datasets_result.ok is False
    assert datasets_result.lines == (
        (f"FAIL: 3 of 4 registry dataset dir(s) missing on disk "
         f"(the E2' launch gate) (root: {tmp_path}):"),
        "  - d-emptypath",
        "  - d-nondict",
        "  - d-nopath",
    )
