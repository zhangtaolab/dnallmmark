"""
quick_check — the launch-required subset re-validation (Phase 8, 08-04,
ENV-04/D-09).

The light pre-launch check: revalidate the subset of env_smoke kernels
a launch actually needs, skipping the heavyweight matmul smoke — a
calibration-class GPU exercise that belongs to the FULL check, not to a
launch pre-flight (D-09: the quick check is the lightweight
subset re-validation).

Contract (locked decisions):

- ENV-04/D-09: the subset is ALL seven kernel ids EXCEPT ``matmul`` —
  ``QUICK_CHECK_KERNEL_IDS`` — in main() kernel order. The subset
  definition lives HERE, once; Phase 11's launch screen and every
  consumer reuse it.
- D-05 (never persisted): the quick-check result is computed ON DEMAND
  and never persisted as the full result — it is a pre-launch
  re-validation, not a cache entry. This module performs no writes at
  all; the state file's semantics belong to ``env_check``.
- D-02/D-03: the default path executes the SAME imported env_smoke
  kernels through ``env_check.default_kernels()`` — the shared
  main()-order sequence — filtered to the subset. The kernel list is
  INJECTABLE so CI tests run fakes and the real GPU-touching kernels
  (cuda) execute only on the GB10 host.
- Judgment over the results is NOT repeated here —
  ``env_gate.gate_verdict`` owns it (one implementation, D-09).

ZERO textual imports (the services-tier invariant,
``tests/tui/test_import_lock.py``). Dependencies: the sibling
env_check service (and through it the imported pipeline kernels).
"""

from env_smoke import CheckResult  # top-level module (pipeline/ sys.path root)

from tui.services import env_check

# The launch-required subset: every kernel id except matmul, in main()
# kernel order. matmul stays out because it is the heavyweight
# calibration-class GPU smoke — the full check's job, not a launch
# pre-flight's (D-09 / ENV-04).
QUICK_CHECK_KERNEL_IDS = (
    "version_pins",
    "dnallm",
    "peft",
    "cuda",
    "numpy",
    "dataset_dirs",
)


def run_quick_check(kernels=None) -> list[CheckResult]:
    """Revalidate the launch-required subset (ENV-04).

    Args:
        kernels: an injectable sequence of zero-arg callables, each
            returning one ``CheckResult`` — results come back in the
            given order (CI tests inject fakes, D-03). None means the
            shared ``env_check.default_kernels()`` sequence filtered to
            ``QUICK_CHECK_KERNEL_IDS``.

    Returns:
        list[CheckResult]: the subset's results, in kernel order.
        Computed on demand; nothing is persisted (D-05).
    """
    if kernels is None:
        by_id = env_check.default_kernels()
        kernels = [by_id[kid] for kid in QUICK_CHECK_KERNEL_IDS]
    return [kernel() for kernel in kernels]
