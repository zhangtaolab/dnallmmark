"""
Tier-1 service tests for ``tui/services/quick_check.py`` (Phase 8, 08-04,
ENV-04/D-09).

Pinned decisions:

- ENV-04/D-09: the quick check revalidates the LAUNCH-REQUIRED subset —
  all eight kernel ids EXCEPT matmul, the heavyweight calibration-class
  GPU smoke (a launch pre-flight must be light; the full matmul
  calibration stays in the full check; 261014-dcl joined model_dirs so
  the pre-flight validates model dirs under the configured root).
- D-05: the quick-check result is computed ON DEMAND and never
  persisted as the full result — it is a pre-launch re-validation, not
  a cache entry. The service exposes no persistence of it.
- D-03: CI tests inject fakes and monkeypatch the default sequence —
  real GPU kernels execute only on the GB10 host.
- The kernel list is injectable so Phase 11's launch screen can reuse
  the same subset definition with its own wiring.

See also:
    ``tui/services/quick_check.py`` — the service under test.
    ``tui/services/env_check.py`` — the default kernel sequence shared.
    ``tui/services/env_gate.py`` — the judgment over check results.
"""

from env_smoke import CheckResult  # conftest puts pipeline/ on sys.path

from tui.services import env_check
from tui.services.quick_check import QUICK_CHECK_KERNEL_IDS, run_quick_check


def _fake_kernel(name):
    """A zero-arg fake kernel returning one passing CheckResult."""

    def _run():
        return CheckResult(name=name, ok=True, lines=(f"PASS: {name}",))

    return _run


def test_quick_check_ids_are_the_seven_non_matmul_kernels_in_main_order():
    """EXACTLY seven ids — matmul excluded, main() order preserved (D-09;
    261014-dcl joined model_dirs before dataset_dirs)."""
    assert QUICK_CHECK_KERNEL_IDS == (
        "version_pins",
        "dnallm",
        "peft",
        "cuda",
        "numpy",
        "model_dirs",
        "dataset_dirs",
    )
    assert "matmul" not in QUICK_CHECK_KERNEL_IDS


def test_run_quick_check_injected_kernels_return_in_kernel_order():
    """Injected fakes: results come back in the given kernel order."""
    kernels = [_fake_kernel(kid) for kid in QUICK_CHECK_KERNEL_IDS]
    results = run_quick_check(kernels=kernels)
    assert [result.name for result in results] == list(
        QUICK_CHECK_KERNEL_IDS
    )
    assert all(result.ok for result in results)


def test_run_quick_check_default_is_env_check_sequence_minus_matmul(
        monkeypatch):
    """No injection -> the shared env_check sequence filtered to the seven.

    The default sequence is monkeypatched to fakes (D-03 — no real
    kernel executes); what is under test is the SUBSET selection: the
    service must take env_check's main()-order sequence and drop
    exactly matmul.
    """

    def fake_default_kernels():
        return {
            kid: _fake_kernel(kid)
            for kid in (
                "version_pins",
                "dnallm",
                "peft",
                "cuda",
                "matmul",
                "numpy",
                "model_dirs",
                "dataset_dirs",
            )
        }

    monkeypatch.setattr(env_check, "default_kernels", fake_default_kernels)
    results = run_quick_check()
    assert [result.name for result in results] == list(
        QUICK_CHECK_KERNEL_IDS
    )
    assert "matmul" not in [result.name for result in results]


def test_run_quick_check_never_persists(tmp_path, monkeypatch):
    """D-05: computed on demand — no state file is ever written."""
    monkeypatch.setenv("DNALLMMARK_TUI_STATE_DIR", str(tmp_path))
    kernels = [_fake_kernel(kid) for kid in QUICK_CHECK_KERNEL_IDS]
    results = run_quick_check(kernels=kernels)
    assert len(results) == 7
    assert list(tmp_path.iterdir()) == []  # nothing landed anywhere
