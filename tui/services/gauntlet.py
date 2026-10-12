"""
gauntlet — the CUST-04 error-detection gauntlet orchestration (Phase 9,
09-02; D-06/D-07/D-08).

The gauntlet is the phase's safety story: a candidate custom entry
lands ONLY after real tooling passes over it (D-08). Both legs are REAL
subprocesses over in-repo stdlib scripts (CPU, sub-second — live-probed
in the Phase 9 research), so the whole gauntlet is tier-1 testable with
real processes in CI:

- **dry-run precheck** (D-06): ``pipeline/run_sweep.py --dry-run`` with
  the candidate staged alongside the operator's existing customs into a
  TEMP overlay dir pinned via ``DNALLMMARK_CUSTOM_REGISTRY_DIR`` — CLI
  parity as the mechanism: the dry-run path IS the pure-planning
  function, so a candidate that passes here enumerates in a real sweep.
- **audit reconciliation** (D-07): ``script/audit_n_frequencies.py``
  against a CANDIDATE-ONLY temp registry dir with an ABSOLUTE
  ``Dataset_path`` and EVERY output flag pointed at temp paths — the
  kernels (row counts, non-ACGT census, subset survival) are the audit
  script's alone; this service only parses and compares declared-vs-
  measured (binding constraint 5: TUI orchestrates, never computes).

Verdicts come from PARSED ARTIFACTS, never exit codes alone (Pitfall
5): the dry-run pass = exit 0 AND a ``sweep_manifest.json`` whose cells
contain the candidate key with status ``planned`` (a zero-cell or
candidate-absent manifest is a FAIL); the audit pass = the parsed
``n_audit.json`` fields (``missing`` false, three splits each with
rows > 0, ``unified_eval_n`` > 0, declared ``Train``/``Dev``/``Test``
== measured rows per split). The non-ACGT census is reported detail
data (drill-down), never a failure condition — official datasets carry
non-ACGT rows by design.

Service boundary (D-08): this module NEVER writes the user-owned custom
registries — landing after all-pass is the caller's act through the
``custom_entries`` store (the 09-01 seam). Every staging dir is a
``tempfile.TemporaryDirectory`` cleaned on exit, so a failed gauntlet
leaves NO state anywhere outside those temp dirs (failed entries never
land). A timeout or a crash yields a failed ``GauntletItem`` carrying
the verbatim captured output — never a hang, never an exception
crossing the service boundary.

Subprocess discipline (T-09-05, the Phase 7 T-03-10 rule): argv is a
LIST (``sys.executable`` + ABSOLUTE script paths — registry values
never pass through a shell, no string interpolation), and the env is
constructed explicitly as ``os.environ`` plus exactly ONE override.
Every item carries its ``run_id`` (the WR-02 tag-and-drop seam the
09-05 panel consumes to drop stale async results); the service itself
holds no global mutable state.

ZERO textual imports (the services-tier invariant declared in
``tui/services/__init__.py``; locked by
``tests/tui/test_import_lock.py``). Dependencies: stdlib (subprocess/
tempfile/json/os/sys) + ``artifact_loader`` (tolerant artifact parses,
D-19) + ``registry_loader`` (official file-name constants) + the
sibling ``custom_entries`` store (the existing-custom staging read) and
``settings`` (``atomic_write`` for the staging files).
"""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

# ===== Locations (resolved from this module's own file, never CWD) =====

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The subprocess legs' script names, resolved against the repo root.
RUN_SWEEP_NAME = "run_sweep.py"
AUDIT_SCRIPT_NAME = "audit_n_frequencies.py"

#: Artifact contract names (the subprocess writers' own constants —
#: restated here because importing the writers would violate the
#: services-tier import discipline; the names are pinned by the tier-1
#: real-subprocess tests, which read the artifacts the real writers
#: emit).
MANIFEST_NAME = "sweep_manifest.json"
N_AUDIT_NAME = "n_audit.json"

#: The whole-dir overlay override (the registry_loader env contract).
CUSTOM_DIR_ENV = "DNALLMMARK_CUSTOM_REGISTRY_DIR"

#: GauntletItem.leg values (the kind-aware item vocabulary — a model
#: candidate gauntlets the dry-run leg ONLY; a dataset candidate runs
#: both, n_audit being dataset-only by design).
LEG_DRY_RUN = "dry_run"
LEG_AUDIT = "audit"

#: The injectable subprocess seam's type: called as
#: ``runner(argv, capture_output=True, text=True, timeout=..., env=...)``
#: and returning a ``subprocess.CompletedProcess``-sh object.
Runner = Callable[..., Any]


@dataclass(frozen=True)
class GauntletItem:
    """One gauntlet leg's structured verdict (rendered by the 09-05
    panel from GAUNTLET_* strings — this type carries DATA, not copy).

    Attributes:
        run_id: the caller's run tag, echoed verbatim (WR-02 tag-and-
            drop; stale ids are dropped by the panel, never mixed).
        kind: ``KIND_MODELS`` or ``KIND_DATASETS``.
        leg: ``LEG_DRY_RUN`` or ``LEG_AUDIT``.
        name: the candidate registry key.
        ok: the leg verdict (artifact-based, never exit-code-alone).
        details: structured data tokens (e.g. ``"planned_cells=1"``) —
            machine-readable facts the panel formats.
        raw_output: the verbatim captured subprocess output (stdout +
            stderr; the drill-down content).
    """

    run_id: str
    kind: str
    leg: str
    name: str
    ok: bool
    details: tuple[str, ...] = ()
    raw_output: str = ""


def _default_runner(argv, **kwargs):
    """The real subprocess seam (the injectable default).

    Args:
        argv (list): the LIST argv (never a shell string).
        **kwargs: ``timeout``/``env`` (forwarded to ``subprocess.run``).

    Returns:
        subprocess.CompletedProcess: with captured text stdout/stderr.
    """
    return subprocess.run(argv, capture_output=True, text=True, **kwargs)


class GauntletService:
    """The CUST-04 gauntlet orchestrator (injectable runner, run-id
    tagged items, temp-only staging, never a write to user state)."""

    def __init__(self, runner=None, timeout_dry_run=60, timeout_audit=300,
                 repo_root=None):
        """Configure the service (no state beyond construction args).

        Args:
            runner (Runner | None): the subprocess seam; ``None`` uses
                the real ``subprocess.run`` (fakes inject here).
            timeout_dry_run (int): per-call timeout seconds for the
                dry-run leg (T-09-07; overridable, default 60).
            timeout_audit (int): per-call timeout seconds for the audit
                leg (overridable, default 300 — bounded by CSV size).
            repo_root (Path | str | None): the repo root the script and
                official-registry paths resolve against; ``None`` = this
                module's own repo root (never CWD).
        """
        self._runner: Runner = _default_runner if runner is None else runner
        self._timeout_dry_run = timeout_dry_run
        self._timeout_audit = timeout_audit
        self._repo_root = REPO_ROOT if repo_root is None else Path(repo_root)
        self._pipeline_dir = self._repo_root / "pipeline"

    # ===== Leg 1: dry-run precheck (D-06) =====

    def dry_run_precheck(self, kind, candidate_key, entry, run_id):
        """Gauntlet one candidate through ``run_sweep.py --dry-run``.

        Stages the operator's existing customs + the candidate (forced
        ``enabled: true`` — a disabled entry cannot be gauntleted) into
        a temp overlay dir, then runs the REAL dry-run subprocess under
        ``DNALLMMARK_CUSTOM_REGISTRY_DIR=<staging>`` with the official
        counterpart on the other axis (derived at read time: first
        official dataset key in file order with truthy ``Train`` for
        model candidates, first official model key for dataset
        candidates — never a hardcoded constant).

        Args:
            kind (str): ``KIND_MODELS`` or ``KIND_DATASETS``.
            candidate_key (str): the candidate registry key.
            entry (dict): the candidate's field values.
            run_id (str): the caller's run tag (echoed on the item).

        Returns:
            GauntletItem: ok=True iff exit 0 AND the parsed manifest's
            cells contain the candidate key with status ``planned``;
            every failure path returns a failed item (never raises).
        """
        raise NotImplementedError("D-06 dry-run precheck lands in GREEN")

    # ===== Leg 2: audit reconciliation (D-07) =====

    def audit_reconciliation(self, candidate_key, entry, declared_splits,
                             run_id):
        """Reconcile one DATASET candidate through the audit subprocess.

        Stages a candidate-ONLY temp registry dir (an ABSOLUTE
        ``Dataset_path`` — the pathlib join replaces the root, Pitfall
        3), overrides EVERY audit output flag to temp paths (Pitfall 1),
        pins the env override to an EMPTY temp dir (operator isolation,
        Pitfall 2), then parses the temp ``n_audit.json`` into the
        verdict.

        Args:
            candidate_key (str): the candidate dataset key.
            entry (dict): the candidate's field values (the LANDED
                relative ``Dataset_path`` form is absolutized here).
            declared_splits (dict): the declared ``Train``/``Dev``/
                ``Test`` ints (the reconciliation's declared side).
            run_id (str): the caller's run tag (echoed on the item).

        Returns:
            GauntletItem: ok=True iff missing is false, all three splits
            have rows > 0, unified_eval_n > 0, and declared == measured
            per split; non-ACGT census values ride the details as data.
        """
        raise NotImplementedError("D-07 audit leg lands in 09-02 Task 3")

    def reconcile(self, kind, candidate_key, entry, run_id,
                  declared_splits=None):
        """The kind-aware entry point the 09-05 panel calls.

        Models gauntlet the dry-run leg ONLY; datasets run BOTH legs
        sequentially under one run_id (n_audit is dataset-only by
        design — verified).

        Args:
            kind (str): ``KIND_MODELS`` or ``KIND_DATASETS``.
            candidate_key (str): the candidate registry key.
            entry (dict): the candidate's field values.
            run_id (str): the run tag shared by every returned item.
            declared_splits (dict | None): declared split counts
                (dataset kind only; ``None`` means no declarations —
                the reconciliation compares only the measured side).

        Returns:
            list[GauntletItem]: one (models) or two (datasets) items in
            execution order, all carrying ``run_id``.
        """
        raise NotImplementedError("reconcile lands in 09-02 Task 3")

    # ===== Shared internals =====

    def _official_registry(self, filename):
        """Read one OFFICIAL registry file directly (not the overlay
        loader) — the counterpart must be an official key regardless of
        any custom overlay state.

        Args:
            filename (str): the registry file name.

        Returns:
            dict: the parsed official registry (file order preserved).
        """
        with open(self._pipeline_dir / filename, "r", encoding="utf-8") as fh:
            return json.load(fh)
