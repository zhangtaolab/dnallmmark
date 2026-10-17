"""Parity tests for the vendored aggregate_seeds statistics block (SC-2/REV-03).

The function under test is a VERBATIM vendored copy of
``dnallm/finetune/sweep.py::aggregate_seeds`` at suite revision 483a35c
(see the provenance banner in ``script/export_runs.py``; the suite repo is
read-only and never imported — CONTEXT exporter-Q1). These tests pin the
vendored copy to the suite semantics WITHOUT importing the suite: every
expected value is recomputed independently from ``scipy.stats.t`` and
``numpy`` in this file, so a behavioral edit to the vendored section fails
here (T-04-03).

Pinned behavior (the n-guard, D-14/SEED-01):

- n < 1                  -> ValueError (empty input)
- n == 1                 -> sd None (ddof=1 undefined), ci95 None, method "none"
- n == 2                 -> ci95 None, method "none"
- 3 <= n < 10, t         -> Student-t interval, method "t"
- 3 <= n < 10, omit      -> ci95 None, method "omitted"
- n >= 10                -> seeded percentile bootstrap, method "bootstrap-percentile"
- bad small_n_ci / non-flat input -> ValueError

The statistics block carries EXACTLY {"n_seeds", "mean", "sd", "ci95",
"method"} and the three module constants carry the suite values
(SMALL_N_CI_CHOICES / CI_MIN_SEEDS / BOOTSTRAP_MIN_SEEDS).

See also:
    - ``tests/test_determinism.py`` — the real-tree counterpart of this
      pinned-behavior parity style.
    - ``tests/test_export_runs.py`` — the exporter core built on top of the
      vendored statistics.
"""

from collections.abc import Sequence
from typing import cast

import export_runs  # conftest puts script/ on sys.path
import numpy as np
import pytest
from scipy import stats


def agg(
    values: Sequence[float],
    *,
    n_bootstrap: int = 500,
    bootstrap_seed: int = 42,
    small_n_ci: str = "t-interval",
):
    """Call the vendored aggregate_seeds with the suite-example kwargs."""
    return export_runs.aggregate_seeds(
        values,
        n_bootstrap=n_bootstrap,
        bootstrap_seed=bootstrap_seed,
        small_n_ci=small_n_ci,
    )


def test_n_guard_boundaries():
    """n=2 -> no interval; n=3/9 -> t; n=10 -> bootstrap (the 2/3/9/10 pins)."""
    two = agg([0.4, 0.6])
    assert two["n_seeds"] == 2
    assert two["ci95"] is None
    assert two["method"] == "none"
    for n in (3, 9):
        vals = [0.5 + 0.01 * i for i in range(n)]
        block = agg(vals)
        assert block["n_seeds"] == n
        assert block["method"] == "t"
        assert block["ci95"] is not None
    ten = agg([0.5] * 10)
    assert ten["n_seeds"] == 10
    assert ten["method"] == "bootstrap-percentile"
    assert ten["ci95"] is not None


def test_omit_policy_reports_omitted_for_small_n():
    """3 <= n < 10 with small_n_ci='omit' -> ci95 None, method 'omitted'."""
    block = agg([0.4, 0.5, 0.6], small_n_ci="omit")
    assert block["n_seeds"] == 3
    assert block["ci95"] is None
    assert block["method"] == "omitted"


@pytest.mark.parametrize("n", [3, 5, 9])
def test_t_interval_matches_scipy_recomputation(n):
    """ci95 equals mean +/- t.ppf(0.975, n-1) * sd(ddof=1)/sqrt(n), recomputed here."""
    vals = [round(0.4 + 0.037 * i, 6) for i in range(n)]
    block = agg(vals)
    arr = np.asarray(vals, dtype=float)
    mean = float(arr.mean())
    sem = float(arr.std(ddof=1) / np.sqrt(n))
    tcrit = float(stats.t.ppf(0.975, n - 1))
    assert block["mean"] == pytest.approx(mean)
    assert block["sd"] == pytest.approx(float(arr.std(ddof=1)))
    assert block["ci95"][0] == pytest.approx(mean - tcrit * sem)
    assert block["ci95"][1] == pytest.approx(mean + tcrit * sem)


def test_bootstrap_deterministic_under_seed():
    """Same seed -> identical ci95; the mean is seed-independent; interval brackets."""
    vals = [0.1 * i for i in range(12)]
    first = agg(vals, n_bootstrap=2000, bootstrap_seed=7)
    first_again = agg(vals, n_bootstrap=2000, bootstrap_seed=7)
    assert first["ci95"] == first_again["ci95"], "same seed must reproduce the interval"
    assert first["method"] == "bootstrap-percentile"
    other = agg(vals, n_bootstrap=2000, bootstrap_seed=99)
    # A different seed produces its own deterministic valid interval; the
    # point estimate is seed-independent (the plan's "may differ" is a
    # permission, not an obligation, so only validity is asserted).
    assert other["ci95"][0] <= other["mean"] <= other["ci95"][1]
    assert other["mean"] == pytest.approx(first["mean"])


def test_single_seed_degenerate_block():
    """n=1: sd None, ci95 None, method 'none', mean == the value, exact key set."""
    block = agg([0.7])
    assert block == {
        "n_seeds": 1,
        "mean": 0.7,
        "sd": None,
        "ci95": None,
        "method": "none",
    }


def test_value_error_cases():
    """Empty input, non-flat input and an invalid small_n_ci all raise."""
    with pytest.raises(ValueError):
        agg([])
    # Deliberately mistyped input (non-flat): the runtime must reject it —
    # cast documents the intent without weakening the check.
    non_flat = cast("Sequence[float]", [[1.0, 2.0], [3.0, 4.0]])
    with pytest.raises(ValueError):
        agg(non_flat)
    with pytest.raises(ValueError):
        agg([0.5, 0.6, 0.7], n_bootstrap=10, bootstrap_seed=1, small_n_ci="banana")


def test_vendored_constants_match_suite_values():
    """The three module constants carry the suite values @483a35c."""
    assert export_runs.SMALL_N_CI_CHOICES == ("t-interval", "omit")
    assert export_runs.CI_MIN_SEEDS == 3
    assert export_runs.BOOTSTRAP_MIN_SEEDS == 10
