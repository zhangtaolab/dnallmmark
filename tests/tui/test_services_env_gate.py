"""
Tier-1 service tests for ``tui/services/env_gate.py`` (Phase 8, 08-04,
ENV-03/D-09).

Pinned decisions:

- D-09: the gate JUDGMENT lands now as a pure function; the blocking
  hook (actually preventing entry into the launch flow) is wired by
  Phase 11's launch screen onto this same verdict.
- CRITICAL vs ROUTING: a CRITICAL failure blocks launch and its detail
  lines become the reasons; a ROUTING failure (the two directory
  kernels — model_dirs/dataset_dirs, 261014-dcl) routes WITHOUT
  blocking can_launch by itself. The sets are disjoint and their union
  covers all eight kernel ids — matmul is CRITICAL (ENV-04 keeps it out
  of the QUICK subset, not out of the gate), numpy is CRITICAL (the
  data chain's hard floor), the directory kernels are ROUTING-only.
- Reasons order: failing kernels' detail lines in main() kernel order
  (the input list's order), never set-iteration order.
- Forward tolerance: kernel ids outside both sets are ignored
  deterministically — a future kernel cannot crash the judgment.
- Only fake CheckResults run here — no kernel executes (D-03).

See also:
    ``tui/services/env_gate.py`` — the service under test.
    ``tui/services/quick_check.py`` — the launch-required subset service.
    ``pipeline/env_smoke.py`` — the kernel ids and main() order.
"""

import dataclasses

import pytest
from env_smoke import CheckResult  # conftest puts pipeline/ on sys.path

from tui.services.env_gate import CRITICAL, ROUTING, GateVerdict, gate_verdict

# main()'s result-list order — the kernel-id vocabulary (08-01;
# 261014-dcl inserted model_dirs before dataset_dirs — eight ids).
MAIN_KERNEL_ORDER = (
    "version_pins",
    "dnallm",
    "peft",
    "cuda",
    "matmul",
    "numpy",
    "model_dirs",
    "dataset_dirs",
)


def _results(*specs):
    """Build a CheckResult list from (name, ok) pairs, in given order.

    A passing kernel carries one PASS line; a failing kernel carries two
    FAIL lines — enough to pin which kernel's lines land in reasons and
    in which order.
    """
    return [
        CheckResult(
            name=name,
            ok=ok,
            lines=(
                (f"PASS: {name}",)
                if ok
                else (f"FAIL: {name} line 1", f"FAIL: {name} line 2")
            ),
        )
        for name, ok in specs
    ]


def _all_pass():
    return _results(*((kid, True) for kid in MAIN_KERNEL_ORDER))


def test_all_pass_launches_with_empty_reasons_and_no_routing():
    """Zero failures -> can_launch True, no reasons, no data routing."""
    verdict = gate_verdict(_all_pass())
    assert verdict == GateVerdict(
        can_launch=True, reasons=(), route_to_data=False
    )


def test_critical_fail_blocks_launch_with_its_detail_lines():
    """A CRITICAL failure (cuda) blocks launch; its lines are the reasons."""
    results = _results(
        ("version_pins", True),
        ("dnallm", True),
        ("peft", True),
        ("cuda", False),
        ("matmul", True),
        ("numpy", True),
        ("model_dirs", True),
        ("dataset_dirs", True),
    )
    verdict = gate_verdict(results)
    assert verdict.can_launch is False
    assert verdict.reasons == ("FAIL: cuda line 1", "FAIL: cuda line 2")
    assert verdict.route_to_data is False


def test_two_critical_failures_collect_reasons_in_kernel_order():
    """Multiple critical failures: reasons follow main() kernel order."""
    results = _results(
        ("version_pins", True),
        ("dnallm", True),
        ("peft", True),
        ("cuda", False),
        ("matmul", True),
        ("numpy", False),
        ("model_dirs", True),
        ("dataset_dirs", True),
    )
    verdict = gate_verdict(results)
    assert verdict.can_launch is False
    # cuda (main-order index 3) precedes numpy (index 5) — the input
    # list's order, not set iteration order.
    assert verdict.reasons == (
        "FAIL: cuda line 1",
        "FAIL: cuda line 2",
        "FAIL: numpy line 1",
        "FAIL: numpy line 2",
    )


def test_dataset_dirs_failure_routes_to_data_without_blocking():
    """A ROUTING failure alone never blocks can_launch (D-09)."""
    results = _results(
        ("version_pins", True),
        ("dnallm", True),
        ("peft", True),
        ("cuda", True),
        ("matmul", True),
        ("numpy", True),
        ("model_dirs", True),
        ("dataset_dirs", False),
    )
    verdict = gate_verdict(results)
    assert verdict.can_launch is True
    assert verdict.reasons == ()
    assert verdict.route_to_data is True


def test_model_dirs_failure_routes_without_blocking():
    """The model_dirs twin (261014-dcl): a missing model dir is ROUTING
    — it sets route_to_data and NEVER touches can_launch (models have
    no CLI download command; blocking would strand a dry run)."""
    results = _results(
        ("version_pins", True),
        ("dnallm", True),
        ("peft", True),
        ("cuda", True),
        ("matmul", True),
        ("numpy", True),
        ("model_dirs", False),
        ("dataset_dirs", True),
    )
    verdict = gate_verdict(results)
    assert verdict.can_launch is True, (
        "a model_dirs failure must never block the launch"
    )
    assert verdict.reasons == ()
    assert verdict.route_to_data is True


def test_critical_and_routing_failures_together_signal_both():
    """cuda FAIL + dataset_dirs FAIL -> blocked AND routed (both signals)."""
    results = _results(
        ("version_pins", True),
        ("dnallm", True),
        ("peft", True),
        ("cuda", False),
        ("matmul", True),
        ("numpy", True),
        ("model_dirs", True),
        ("dataset_dirs", False),
    )
    verdict = gate_verdict(results)
    assert verdict.can_launch is False
    assert verdict.reasons == ("FAIL: cuda line 1", "FAIL: cuda line 2")
    assert verdict.route_to_data is True


def test_critical_and_routing_sets_are_disjoint_and_cover_all_eight():
    """Disjoint sets; union == the eight kernel ids; memberships pinned."""
    assert not (CRITICAL & ROUTING), "CRITICAL and ROUTING must be disjoint"
    assert CRITICAL | ROUTING == set(MAIN_KERNEL_ORDER)
    assert CRITICAL == {
        "version_pins",
        "dnallm",
        "peft",
        "cuda",
        "matmul",
        "numpy",
    }
    assert ROUTING == {"model_dirs", "dataset_dirs"}


def test_unknown_kernel_ids_are_ignored_deterministically():
    """A failing future kernel id is ignored — forward tolerance."""
    results = [
        *_all_pass()[:3],
        CheckResult(name="future_kernel", ok=False,
                    lines=("FAIL: future line",)),
        *_all_pass()[3:],
    ]
    verdict = gate_verdict(results)
    assert verdict == GateVerdict(
        can_launch=True, reasons=(), route_to_data=False
    )


def test_gate_verdict_is_frozen():
    """The verdict value is immutable (a pure judgment, D-09)."""
    verdict = gate_verdict(_all_pass())
    # setattr (not attribute assignment): ty correctly reads frozen
    # dataclass properties as read-only — the 08-01 ty-vs-intent
    # precedent — while runtime still raises FrozenInstanceError. The
    # trailing noqa covers the inverse ruff conflict (B010), same
    # justification as the 08-01 site.
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(verdict, "can_launch", False)  # noqa: B010
