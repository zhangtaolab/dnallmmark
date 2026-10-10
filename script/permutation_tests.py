"""Pairwise permutation tests over the aggregate leaderboard view (F6 Q3, REV-04).

SKELETON (TDD RED, plan 05-02 Task 1): signatures only — bodies raise
NotImplementedError until the GREEN implementation lands in the same task.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

N_RESAMPLES = 10_000
SEED = 42
BATCH = 100


def build_artifact(
    zscore_matrix: Mapping[str, Mapping[str, float]],
    *,
    n_resamples: int = N_RESAMPLES,
    seed: int = SEED,
    batch: int = BATCH,
) -> dict[str, Any]:
    """RED skeleton."""
    raise NotImplementedError


def write_artifact(doc: dict[str, Any], path: Path) -> None:
    """RED skeleton."""
    raise NotImplementedError


def main(argv: Sequence[str] | None = None) -> int:
    """RED skeleton."""
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
