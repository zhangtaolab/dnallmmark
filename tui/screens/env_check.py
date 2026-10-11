"""
env_check — the env-check screen shell (Phase 8, 08-03 tracer).

The thinnest presentation slice of the console: a DataTable carrying the
seven fixed env-check rows, every row in the pending state. This is the
shell the 08-06 screen build fills — the thread worker, per-kernel async
row fill, the verdict/routing block, and the footer chrome all land
there. The tracer proves only the boot path (composition root → screen →
strings constants) with zero service calls and zero env_smoke imports
(plan prohibition: the tracer must not grow beyond the one path).

Contract:

- Presentation only, per the ``tui/screens/`` tier contract: no business
  logic, no workers, no service calls — the rows are fixed shell state.
- Zero Chinese literals: every operator-facing string renders through
  ``tui/strings.py`` constants (I18N-01 single-home rule) — kernel ids
  and labels come from ``ENV_KERNEL_LABELS`` (main() kernel order), the
  pending state from ``ENV_STATE_PENDING``, column headers from the
  ``ENV_COL_*`` constants.
- Row keys are the stable kernel ids (the ``CheckResult.name``
  vocabulary landed by 08-01): 08-06's worker updates rows by these keys
  (``update_cell``), and the row order — ``version_pins, dnallm, peft,
  cuda, matmul, numpy, dataset_dirs`` — is the 08-UI-SPEC Screen-1
  row-order contract.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable

from tui.strings import (
    ENV_COL_ITEM,
    ENV_COL_STATE,
    ENV_KERNEL_LABELS,
    ENV_STATE_PENDING,
)


class EnvCheckScreen(Screen):
    """Env-check shell: seven fixed pending rows (filled by 08-06)."""

    def compose(self) -> ComposeResult:
        """Yield the empty kernel table; rows land in ``on_mount``."""
        yield DataTable(id="env-kernels")

    def on_mount(self) -> None:
        """Compose the seven fixed pending rows in main() kernel order.

        ``ENV_KERNEL_LABELS`` is defined in main() kernel order (the
        08-02 strings contract), so iteration order IS the row-order
        contract; the dict keys double as the stable DataTable row keys.
        """
        table = self.query_one("#env-kernels", DataTable)
        table.cursor_type = "row"   # 08-UI-SPEC DataTable usage contract
        table.zebra_stripes = True  # same
        table.add_columns(ENV_COL_STATE, ENV_COL_ITEM)
        for kernel_id, label in ENV_KERNEL_LABELS.items():
            table.add_row(ENV_STATE_PENDING, label, key=kernel_id)
