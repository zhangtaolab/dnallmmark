"""
env_gate — the pure env-gate judgment (Phase 8, 08-04, ENV-03/D-09).

Classifies env-check failures into CRITICAL (block launch) and ROUTING
(missing data -> data management) by kernel id. Phase 8 renders this
verdict on the env-check panel; Phase 11's launch screen wires the
actual blocking hook onto the SAME pure judgment — the judgment itself
never gains I/O, state, or presentation.

Contract (locked decisions):

- D-09: the judgment lands NOW; the block (preventing entry into the
  launch flow) is Phase 11 wiring. This module stays pure — a function
  over ``CheckResult`` values, no persistence, no textual, no I/O.
- CRITICAL — a failure in any of these blocks launch and contributes
  its detail lines to ``reasons``:
  ``version_pins`` / ``dnallm`` / ``peft`` / ``cuda`` / ``matmul`` /
  ``numpy``. matmul is critical for the GATE (the full check's
  calibration-class smoke must pass before a real run) even though
  ENV-04 keeps it out of the QUICK-CHECK subset; numpy is critical
  because the data chain's ``numpy>=2`` floor is a hard requirement.
- ROUTING — ``dataset_dirs``: a failure means local data is missing,
  which routes the operator to data management (the Phase 10 panel);
  it does NOT block ``can_launch`` by itself (a dry run / non-data
  flow stays launchable — and the routing signal is advisory until
  Phase 11 wires its hook).
- Disjointness: CRITICAL and ROUTING share no kernel id and their
  union is exactly the seven main()-order kernel ids — every current
  kernel has exactly one disposition.
- Forward tolerance: results whose kernel id is in NEITHER set are
  ignored deterministically — a future kernel cannot crash the
  judgment; its disposition is a deliberate later decision.
- Reasons order: failing kernels' detail lines in the input list's
  (main() kernel) order, never set-iteration order.

ZERO textual imports (the services-tier invariant,
``tests/tui/test_import_lock.py``). Dependencies: stdlib only (+ the
``CheckResult`` type from the imported pipeline seam for docs).
"""

from collections.abc import Sequence
from dataclasses import dataclass

from env_smoke import CheckResult  # top-level module (pipeline/ sys.path root)

CRITICAL = frozenset(
    {
        "version_pins",
        "dnallm",
        "peft",
        "cuda",
        "matmul",
        "numpy",
    }
)
ROUTING = frozenset({"dataset_dirs"})


@dataclass(frozen=True)
class GateVerdict:
    """The pure launch judgment over a check-results list (D-09).

    Attributes:
        can_launch (bool): False when any CRITICAL kernel failed. The
            Phase 8 panel renders this; Phase 11's launch screen blocks
            on it.
        reasons (tuple[str, ...]): the failing CRITICAL kernels' detail
            lines, in main() kernel order — exactly what the operator
            needs to read when launch is blocked.
        route_to_data (bool): True when a ROUTING kernel failed (local
            data missing -> data management guidance; Phase 10 owns the
            panel).
    """

    can_launch: bool
    reasons: tuple[str, ...]
    route_to_data: bool


def gate_verdict(results: Sequence[CheckResult]) -> GateVerdict:
    """Judge a check-results list: launchable, why not, routed?

    Args:
        results: a sequence of ``CheckResult`` values (the env_smoke
            kernel results, live or rebuilt from cached state via
            ``CheckResult(**item)``). Unknown kernel ids are ignored
            (forward tolerance).

    Returns:
        GateVerdict: the frozen pure judgment — Phase 8 renders it,
        Phase 11 blocks on it.
    """
    reasons: list[str] = []
    route_to_data = False
    can_launch = True
    for result in results:
        if result.ok:
            continue
        if result.name in CRITICAL:
            can_launch = False
            reasons.extend(result.lines)
        elif result.name in ROUTING:
            route_to_data = True
        # ids in neither set: ignored deterministically (forward
        # tolerance — a future kernel's disposition is a deliberate
        # later decision, never an implicit one).
    return GateVerdict(
        can_launch=can_launch,
        reasons=tuple(reasons),
        route_to_data=route_to_data,
    )
