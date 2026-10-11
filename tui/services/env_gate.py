"""
env_gate — the pure env-gate judgment (Phase 8, 08-04, ENV-03/D-09).
RED SKELETON: signatures only; behavior lands in the GREEN commit.
"""

from dataclasses import dataclass


CRITICAL = frozenset()
ROUTING = frozenset()


@dataclass(frozen=True)
class GateVerdict:
    """RED skeleton — behavior lands in GREEN."""

    can_launch: bool
    reasons: tuple[str, ...]
    route_to_data: bool


def gate_verdict(results):
    """RED skeleton — behavior lands in GREEN."""
    return None
