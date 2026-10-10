"""PIPE-02 environment smoke gate — the E2' dual gate's environment half.

CONTRACT (binding, PIPE-02 / D-05; AMENDED 2026-10-11): this script is
executed by the maintainer on the GB10 GPU machine, as the second half
of the E2' launch dual gate (DNALLM stable release + this env smoke +
explicit maintainer authorization). SMOKE SANCTION (maintainer
directive, 2026-10-11): executed smoke is additionally permitted as
EXPLICIT, BOUNDED plan TASKS on this GB10 host (this machine IS the
GB10); ``python3 -m py_compile`` remains a valid agent-side proof but
is no longer the ONLY sanctioned form. The boundary holds: executed
smoke lives only inside a plan's task on this host — it NEVER enters
``make test`` or any CI workflow (CI stays GPU-free), and the full E2'
three-seed sweep remains maintainer dual-gate. The module banner and
this docstring ARE that contract; CI's ruff + ty gates cover the file
statically, and ty sees the GPU imports as ``Any`` via the existing
``replace-imports-with-any`` config — no config change needed.

Checkable surface (every check prints a greppable ``PASS:``/``FAIL:`` line;
ANY failure forces a final non-zero exit):

1. ``torch`` and ``transformers`` import, and their ``__version__`` values
   match the ``[gpu]`` group pins READ FROM ``pyproject.toml`` (tomllib —
   the versions are never hardcoded twice; the installed version's local
   suffix, e.g. ``2.11.0+cu130``, is compared by release segment because
   the pin grammar cannot express it);
2. ``import dnallm`` resolves (installed from the local dev clone per
   PIPE-02);
3. ``torch.cuda.is_available()`` and ``device_count >= 1``, with the
   device name and memory printed;
4. every ``datasets_info.json`` ``Dataset_path`` directory exists on disk
   (the 7 GUE re-extraction gate is VISIBLE here: missing dirs are listed
   BY NAME; when a missing expected dir has a double-nested sibling —
   the fresh-unzip ``suite/suite/task`` layout — a note says so);
5. a single small-tensor matmul, proving executability end to end;
6. ``numpy`` major version >= the floor PARSED from the repo's own
   ``pyproject.toml`` dependency string (``numpy>=2.0,<3`` in the
   ``[data]`` group — the floor is read, never duplicated). Maintainer
   heads-up 2026-10-11: dnallm 1.2.1 pins ``numpy>=2.0.0`` directly
   (upstream retired numpy 1.x on 2026-10-10; 1.x users stay on the
   0.8.x series); this repo is already aligned (``numpy>=2.0,<3``,
   uv.lock 2.5.3), and this check makes the alignment visible on GB10;
7. ``peft`` imports and its version prints (06-01, the SC-6 lanes): the
   suite hard-imports peft at module top (dnallm/finetune/trainer.py:58
   @ v1.2.1), so the LoRA/IA3 lanes need it importable in this
   environment (suite floor ``peft>=0.14.0``).

One NON-GATING diagnostic prints the installed ``datasets`` and
``pyarrow`` versions when importable (dnallm 1.2.1 caps
``datasets<=3.2.0`` and declares no pyarrow constraint — the 0.8.x-era
pyarrow cap is gone; useful context on the GPU box, but dnallm's own
constraints govern resolution; this gate does NOT enforce them).

Usage (maintainer, on GB10, inside the GPU environment)::

    python pipeline/env_smoke.py

Exit code: 0 when every check passes, 1 when any check fails (each
failure named on its own FAIL line).

See also:
    ``pipeline/run_sweep.py`` — the E2' sweep driver launched only AFTER
    this gate and the DNALLM-stable-release gate both pass.
    ``pyproject.toml`` — the ``[gpu]`` group carrying the version pins
    this script asserts against.
"""

import json
import re
import sys
import tomllib
from importlib import import_module
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PIPELINE_DIR.parent
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
DATASETS_INFO_PATH = PIPELINE_DIR / "datasets_info.json"
DATASETS_ROOT = PIPELINE_DIR / "datasets"


def read_gpu_pins(pyproject_path):
    """Read the ``[gpu]`` dependency-group version pins from pyproject.toml.

    The pins are PARSED, never duplicated: this function is the single
    reader, so bumping a pin in pyproject.toml is the only act needed to
    move the gate.

    Args:
        pyproject_path (Path): The repo's pyproject.toml.

    Returns:
        dict[str, str]: ``{package name: pinned version}`` for every
        ``name==version`` requirement in the ``[gpu]`` group.

    Raises:
        SystemExit: the file is unreadable, unparseable, or has no
            ``[gpu]`` group with ``==`` pins (a gate script must fail
            loudly on its own configuration, not guess).
    """
    try:
        with open(pyproject_path, "rb") as fh:
            doc = tomllib.load(fh)
    except OSError as exc:
        sys.exit(f"FAIL: cannot read {pyproject_path}: {exc}")
    except tomllib.TOMLDecodeError as exc:
        sys.exit(f"FAIL: {pyproject_path} is not valid TOML: {exc}")
    group = doc.get("dependency-groups", {}).get("gpu")
    if not isinstance(group, list):
        sys.exit(f"FAIL: {pyproject_path} has no [dependency-groups.gpu] list")
    pins = {}
    for requirement in group:
        if "==" in requirement:
            name, _, version = requirement.partition("==")
            pins[name.strip()] = version.strip()
    if not pins:
        sys.exit("FAIL: [dependency-groups.gpu] carries no name==version pins")
    return pins


def release_segment(version):
    """The release segment of an installed version (local suffix stripped).

    The installed torch reports e.g. ``2.11.0+cu130`` while the pin grammar
    (``torch==2.11.0``) cannot express the local suffix — the gate compares
    release segments.

    Args:
        version (str): An installed package's ``__version__``.

    Returns:
        str: Everything before the first ``+``.
    """
    return version.partition("+")[0]


def read_numpy_floor_major(pyproject_path):
    """Read the numpy ``>=`` floor's MAJOR version from pyproject.toml.

    The floor is PARSED from the repo's own dependency string
    (``numpy>=2.0,<3`` in the ``[data]`` group), never duplicated — the
    same no-duplicated-constants discipline as read_gpu_pins. Maintainer
    heads-up 2026-10-11: dnallm 1.2.1 pins ``numpy>=2.0.0`` directly
    (upstream retired numpy 1.x on 2026-10-10; 1.x users stay on the
    0.8.x series).

    Args:
        pyproject_path (Path): The repo's pyproject.toml.

    Returns:
        int: The major version of the first ``>=`` bound on numpy.

    Raises:
        SystemExit: no numpy requirement with a ``>=`` bound is found —
            a gate script must fail loudly on its own configuration.
    """
    try:
        with open(pyproject_path, "rb") as fh:
            doc = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        sys.exit(f"FAIL: cannot read {pyproject_path}: {exc}")
    for group in doc.get("dependency-groups", {}).values():
        if not isinstance(group, list):
            continue
        for requirement in group:
            match = re.match(r"numpy\s*>=\s*([0-9]+)", requirement)
            if match:
                return int(match.group(1))
    sys.exit(
        f"FAIL: no 'numpy>=X' requirement found in {pyproject_path} "
        "dependency-groups — cannot derive the numpy floor"
    )


def check_numpy(floor_major):
    """Check 6: numpy major version >= the pyproject-parsed floor.

    Args:
        floor_major (int): The parsed numpy ``>=`` floor major version.

    Returns:
        bool: True when numpy imported and its major version qualifies.
    """
    numpy = import_or_fail("numpy")
    if numpy is None:
        return False
    installed_major = int(str(numpy.__version__).split(".")[0])
    if installed_major >= floor_major:
        print(
            f"PASS: numpy {numpy.__version__} >= pyproject floor "
            f"(major >= {floor_major}; dnallm 1.2.1 requires numpy>=2)"
        )
        return True
    print(
        f"FAIL: numpy {numpy.__version__} major {installed_major} < "
        f"pyproject floor {floor_major} (dnallm 1.2.1 requires numpy>=2)"
    )
    return False


def print_ecosystem_diagnostics():
    """NON-GATING INFO line: installed datasets/pyarrow versions, if any.

    dnallm 1.2.1 caps ``datasets<=3.2.0`` and declares no pyarrow
    constraint (the 0.8.x-era pyarrow cap is gone — verified read-only
    against the v1.2.1 pyproject); those constraints govern the GPU
    environment's RESOLUTION, not this gate — the line is context for
    the maintainer reading the smoke output on GB10.
    Unimportable packages print as ``not installed``; nothing here can
    fail the gate.
    """
    versions = {}
    for package in ("datasets", "pyarrow"):
        try:
            versions[package] = str(import_module(package).__version__)
        except ImportError:
            versions[package] = "not installed"
        except Exception as exc:  # noqa: BLE001 — a DIAGNOSTIC must never
            # crash the gate: any import-time failure is reported, that's all
            versions[package] = f"import failed ({type(exc).__name__})"
    print(
        "INFO (not gated): datasets "
        f"{versions['datasets']}, pyarrow {versions['pyarrow']} "
        "(dnallm 1.2.1 caps datasets<=3.2.0, no pyarrow pin — dnallm's "
        "own constraints govern resolution)"
    )


def import_or_fail(module_name):
    """Import one module, printing the PASS/FAIL line for check 2's idiom.

    Any import-time failure is a FAIL line naming the exception class —
    a smoke gate must report, never traceback.

    Args:
        module_name (str): The module to import.

    Returns:
        The imported module, or ``None`` when the import failed.
    """
    try:
        module = import_module(module_name)
    except Exception as exc:  # noqa: BLE001 — the smoke gate's contract:
        # ANY import-time failure is a named FAIL line, never a traceback
        print(f"FAIL: import {module_name} — {type(exc).__name__}: {exc}")
        return None
    origin = getattr(module, "__file__", None) or "(built-in)"
    print(f"PASS: import {module_name} resolves ({origin})")
    return module


def check_version_pins(pins):
    """Check 1: torch/transformers import and match the pyproject pins.

    Args:
        pins (dict[str, str]): The parsed ``[gpu]`` pins.

    Returns:
        bool: True when every pinned package imported and matched.
    """
    ok = True
    for package in sorted(pins):
        module = import_or_fail(package)
        if module is None:
            ok = False
            continue
        installed = release_segment(str(getattr(module, "__version__", "?")))
        pinned = pins[package]
        if installed == pinned:
            print(f"PASS: {package} {installed} == pyproject [gpu] pin")
        else:
            ok = False
            print(
                f"FAIL: {package} {installed!r} != pyproject [gpu] pin "
                f"{pinned!r}"
            )
    return ok


def check_dnallm():
    """Check 2: ``import dnallm`` resolves (the local dev-clone install).

    Returns:
        bool: True when the import resolved.
    """
    return import_or_fail("dnallm") is not None


def check_peft():
    """Check 7 (06-01): ``import peft`` resolves, version printed.

    The SC-6 LoRA/IA3 lanes build on peft: the suite hard-imports it at
    module top (dnallm/finetune/trainer.py:58 @ v1.2.1 (30dfd6d)), so a
    GPU environment without an importable peft cannot construct
    DNATrainer at all. Suite floor ``peft>=0.14.0`` (v1.2.1 pyproject);
    the resolved version prints here for the smoke record.

    Returns:
        bool: True when peft imported (version printed on the PASS line).
    """
    try:
        peft = import_module("peft")
    except Exception as exc:  # noqa: BLE001 — the smoke gate's contract:
        # ANY import-time failure is a named FAIL line, never a traceback
        print(f"FAIL: import peft — {type(exc).__name__}: {exc}")
        return False
    version = str(getattr(peft, "__version__", "?"))
    print(
        f"PASS: peft {version} importable "
        "(SC-6 LoRA/IA3 lanes; suite floor peft>=0.14.0)"
    )
    return True


def check_cuda(torch):
    """Check 3: CUDA visible, at least one device, name/memory printed.

    Args:
        torch: The imported torch module.

    Returns:
        bool: True when CUDA is available with >= 1 device.
    """
    if not torch.cuda.is_available():
        print("FAIL: torch.cuda.is_available() is False — no visible GPU")
        return False
    count = torch.cuda.device_count()
    if count < 1:
        print(f"FAIL: torch.cuda.device_count() == {count} (< 1)")
        return False
    print(f"PASS: CUDA available, {count} device(s)")
    for idx in range(count):
        props = torch.cuda.get_device_properties(idx)
        gib = props.total_memory / (1024 ** 3)
        print(
            f"PASS: device {idx}: {props.name}, "
            f"{gib:.1f} GiB total memory"
        )
    return True


def check_dataset_dirs():
    """Check 4: every registry Dataset_path dir exists (GUE gate visible).

    Missing dirs are listed BY NAME (the documented 7-GUE re-extraction
    gate blocks E2' launch — this check makes it visible, it does not fix
    it). When a missing expected dir has a double-nested sibling — the
    fresh suite-archive unzip layout ``{suite}/{suite}/{task}`` instead of
    ``{suite}/{task}`` — a note says the archive needs flattening.

    Returns:
        bool: True when every registry dataset dir exists.
    """
    with open(DATASETS_INFO_PATH, "r", encoding="utf-8") as fh:
        datasets_info = json.load(fh)
    missing = []
    double_nested = []
    for name in sorted(datasets_info):
        rel = datasets_info[name]["Dataset_path"].removeprefix("datasets/")
        expected = DATASETS_ROOT / rel
        if expected.is_dir():
            continue
        missing.append(name)
        parts = rel.split("/")
        if len(parts) >= 2 and (DATASETS_ROOT / parts[0] / parts[0]
                                / "/".join(parts[1:])).is_dir():
            double_nested.append(name)
    total = len(datasets_info)
    if missing:
        print(
            f"FAIL: {len(missing)} of {total} registry dataset dir(s) "
            "missing on disk (the E2' launch gate):"
        )
        for name in missing:
            note = (
                "  [double-nested: the fresh-unzip suite/suite/task layout "
                "needs flattening]"
                if name in double_nested
                else ""
            )
            print(f"  - {name}{note}")
        return False
    print(f"PASS: all {total} registry dataset dir(s) present on disk")
    return True


def check_matmul(torch):
    """Check 5: one small-tensor matmul — executability, nothing more.

    Args:
        torch: The imported torch module.

    Returns:
        bool: True when the matmul produced the expected value.
    """
    a = torch.ones(8, 8)
    result = (a @ a).sum().item()
    if result != 64.0:
        print(f"FAIL: small-tensor matmul produced {result!r}, expected 64.0")
        return False
    print("PASS: small-tensor matmul executed (sum == 64.0)")
    return True


def main():
    """Run every check; exit non-zero when any check failed."""
    print(f"=== PIPE-02 env smoke ({REPO_ROOT.name} @ {REPO_ROOT}) ===")
    pins = read_gpu_pins(PYPROJECT_PATH)
    results = []
    results.append(check_version_pins(pins))
    results.append(check_dnallm())
    results.append(check_peft())
    # The GPU-surface import as a LITERAL statement (deferred so a missing
    # GPU stack is a named FAIL line, never a traceback): the CUDA and
    # matmul checks below consume this module object directly.
    try:
        import torch
    except Exception as exc:  # noqa: BLE001 — the smoke gate's contract:
        # ANY import-time failure is a named FAIL line, never a traceback
        print(f"FAIL: import torch — {type(exc).__name__}: {exc}")
        torch = None
    if torch is not None:
        results.append(check_cuda(torch))
        results.append(check_matmul(torch))
    else:
        print("FAIL: torch unavailable — CUDA + matmul checks not run")
        results.append(False)
        results.append(False)
    results.append(check_numpy(read_numpy_floor_major(PYPROJECT_PATH)))
    print_ecosystem_diagnostics()
    results.append(check_dataset_dirs())

    failed = results.count(False)
    if failed:
        print(f"=== SMOKE RESULT: FAIL ({failed} check group(s) failed) ===")
        return 1
    print("=== SMOKE RESULT: PASS (all checks green) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
