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
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import artifact_loader  # top-level module (pipeline/ sys.path root, D-19)
import registry_loader  # top-level module (pipeline/ sys.path root)

from tui.services import settings
from tui.services.custom_entries import (
    KIND_DATASETS,
    KIND_FILE_NAMES,
    KIND_MODELS,
    read_entries,
)

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

#: The audit kernel's own split order (``SPLIT_ORDER`` in the script)
#: and the declared-count field each split reconciles against.
_AUDIT_SPLIT_ORDER = ("train", "dev", "test")
_DECLARED_SPLIT_FIELDS = (
    ("train", "Train"),
    ("dev", "Dev"),
    ("test", "Test"),
)

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

    The service itself passes ``capture_output=True, text=True`` (plus
    ``timeout``/``env``) on every call — the same kwargs the fakes
    record — so the default is a pure forward to ``subprocess.run``.

    Args:
        argv (list): the LIST argv (never a shell string).
        **kwargs: ``capture_output``/``text``/``timeout``/``env``.

    Returns:
        subprocess.CompletedProcess: with captured text stdout/stderr.
    """
    return subprocess.run(argv, check=False, **kwargs)


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
        counterpart, counterpart_error = self._dry_run_counterpart(kind)
        if counterpart_error is not None:
            # WR-02 (09 review): a missing/corrupt OFFICIAL registry is
            # a failed item, never an exception across the service
            # boundary (mirrors the existing_custom_registry_unreadable
            # path below) — an escaping OSError would kill the wizard's
            # gauntlet worker before any item posts and the panel rows
            # would stay in-flight forever.
            return self._failed_item(
                run_id, kind, LEG_DRY_RUN, candidate_key,
                ("official_registry_unreadable",),
                raw_output=counterpart_error)
        if counterpart is None:
            return self._failed_item(
                run_id, kind, LEG_DRY_RUN, candidate_key,
                ("no_official_counterpart",))
        existing, read_error = read_entries(kind)
        if read_error is not None:
            # A corrupt user-owned registry cannot be silently dropped
            # from the staged view (the real pipeline would fail loud on
            # it) — surface the read failure, launch nothing.
            return self._failed_item(
                run_id, kind, LEG_DRY_RUN, candidate_key,
                ("existing_custom_registry_unreadable",),
                raw_output=read_error)
        with tempfile.TemporaryDirectory(
                prefix="dnallmmark-gauntlet-") as tmp:
            staging = Path(tmp) / "overlay"
            staging.mkdir()
            merged = dict(existing)
            merged[candidate_key] = {**_as_entry(entry),
                                     "enabled": True}
            settings.atomic_write(
                staging / KIND_FILE_NAMES[kind],
                json.dumps(merged, indent=4, ensure_ascii=False))
            out_root = Path(tmp) / "out"
            argv = [sys.executable,
                    str(self._pipeline_dir / RUN_SWEEP_NAME), "--dry-run"]
            if kind == KIND_MODELS:
                argv += ["--models", candidate_key,
                         "--tasks", counterpart]
            else:
                argv += ["--models", counterpart,
                         "--tasks", candidate_key]
            argv += ["--seeds", "42", "--output-root", str(out_root)]
            env = dict(os.environ)
            env[CUSTOM_DIR_ENV] = str(staging)
            proc, launch_failure = self._invoke(
                argv, env, self._timeout_dry_run)
            if launch_failure is not None:
                return self._failed_item(
                    run_id, kind, LEG_DRY_RUN, candidate_key,
                    launch_failure)
            raw = (proc.stdout or "") + (proc.stderr or "")
            if proc.returncode != 0:
                return self._failed_item(
                    run_id, kind, LEG_DRY_RUN, candidate_key,
                    ("exit_nonzero",
                     "exit_code=" + str(proc.returncode)),
                    raw_output=raw)
            manifest = artifact_loader.load_json_artifact(
                out_root / MANIFEST_NAME)
            if manifest is None:
                return self._failed_item(
                    run_id, kind, LEG_DRY_RUN, candidate_key,
                    ("manifest_unreadable",), raw_output=raw)
            cells = manifest.get("cells") if isinstance(manifest, dict) \
                else None
            cells = cells if isinstance(cells, list) else []
            planned = [
                cell for cell in cells
                if isinstance(cell, dict)
                and candidate_key in (cell.get("model"), cell.get("task"))
            ]
            ok = bool(planned) and all(
                cell.get("status") == "planned" for cell in planned)
            return GauntletItem(
                run_id=run_id, kind=kind, leg=LEG_DRY_RUN,
                name=candidate_key, ok=ok,
                details=("planned_cells=" + str(len(planned)),),
                raw_output=raw)

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
        with tempfile.TemporaryDirectory(
                prefix="dnallmmark-gauntlet-") as tmp:
            tmp_path = Path(tmp)
            registry_dir = tmp_path / "regdir"
            registry_dir.mkdir()
            audit_out = tmp_path / "audit-out"
            audit_out.mkdir()
            empty_overlay = tmp_path / "empty-overlay"
            empty_overlay.mkdir()
            datasets_root = tmp_path / "datasets-root"
            datasets_root.mkdir()
            staged_entry = _as_entry(entry)
            # Pitfall 3: the LANDED Dataset_path is pipeline-relative;
            # the audit's resolve_dataset_dir joins against
            # --datasets-root one level differently than the trainer's
            # string concat, so the staged copy carries the ABSOLUTE
            # form (a pathlib absolute join replaces the root — the
            # join against datasets_root is deliberately inert).
            raw_path = staged_entry.get("Dataset_path")
            if isinstance(raw_path, str) and raw_path:
                staged_entry["Dataset_path"] = str(
                    (self._pipeline_dir / raw_path).resolve())
            (registry_dir / registry_loader.DATASETS_INFO_NAME).write_text(
                json.dumps({candidate_key: staged_entry}, indent=4,
                           ensure_ascii=False),
                encoding="utf-8")
            argv = [sys.executable,
                    str(self._repo_root / "script" / AUDIT_SCRIPT_NAME),
                    "--registry-dir", str(registry_dir),
                    "--datasets-root", str(datasets_root),
                    "--data-dir", str(audit_out),
                    "--subsets-out", str(audit_out / "eval_subsets.json"),
                    "--data-md", str(audit_out / "DATA.md")]
            env = dict(os.environ)
            env[CUSTOM_DIR_ENV] = str(empty_overlay)   # Pitfall 2
            proc, launch_failure = self._invoke(
                argv, env, self._timeout_audit)
            if launch_failure is not None:
                return self._failed_item(
                    run_id, KIND_DATASETS, LEG_AUDIT, candidate_key,
                    launch_failure)
            raw = (proc.stdout or "") + (proc.stderr or "")
            if proc.returncode != 0:
                return self._failed_item(
                    run_id, KIND_DATASETS, LEG_AUDIT, candidate_key,
                    ("exit_nonzero",
                     "exit_code=" + str(proc.returncode)),
                    raw_output=raw)
            audit = artifact_loader.load_json_artifact(
                audit_out / N_AUDIT_NAME)
            if audit is None:
                return self._failed_item(
                    run_id, KIND_DATASETS, LEG_AUDIT, candidate_key,
                    ("n_audit_unreadable",), raw_output=raw)
            record = None
            if isinstance(audit, dict):
                tasks = audit.get("tasks")
                if isinstance(tasks, dict):
                    maybe = tasks.get(candidate_key)
                    if isinstance(maybe, dict):
                        record = maybe
            if record is None:
                return self._failed_item(
                    run_id, KIND_DATASETS, LEG_AUDIT, candidate_key,
                    ("candidate_absent_from_n_audit",), raw_output=raw)
            return self._audit_verdict(
                run_id, candidate_key, record, declared_splits, raw)

    def _audit_verdict(self, run_id, candidate_key, record,
                       declared_splits, raw):
        """Turn one parsed n_audit.json task record into an item.

        Pass criteria (D-07, all from the parsed artifact — the audit
        subprocess owns every benchmark semantic): ``missing`` false;
        train/dev/test each present with rows > 0; ``unified_eval_n`` >
        0 (subset survival); and the declared ``Train``/``Dev``/``Test``
        ints equal the measured rows per split (the reconciliation). The
        non-ACGT census and survivor counts ride the details as DATA —
        never failure conditions.

        Args:
            run_id (str): the caller's run tag.
            candidate_key (str): the candidate dataset key.
            record (dict): the parsed ``tasks.{key}`` record.
            declared_splits (dict | None): declared split counts keyed
                by the official field names (``None`` skips the
                reconciliation's declared side).
            raw (str): the verbatim subprocess output.

        Returns:
            GauntletItem: the audit-leg verdict.
        """
        problems = []
        data = []
        if record.get("missing") is not False:
            problems.append("missing=true")
        splits = record.get("splits")
        splits = splits if isinstance(splits, dict) else {}
        measured = {}
        for split in _AUDIT_SPLIT_ORDER:
            stats = splits.get(split)
            stats = stats if isinstance(stats, dict) else {}
            rows = stats.get("rows")
            if not isinstance(rows, int) or isinstance(rows, bool) \
                    or rows <= 0:
                problems.append(split + "_rows=" + repr(rows))
            else:
                measured[split] = rows
                data.append(split + "_rows=" + str(rows))
                data.append(split + "_non_acgt_chars="
                            + str(stats.get("non_acgt_chars")))
                data.append(split + "_strict_survivors="
                            + str(stats.get("strict_survivors")))
                data.append(split + "_n_tolerant_survivors="
                            + str(stats.get("n_tolerant_survivors")))
        unified = record.get("unified_eval_n")
        if not isinstance(unified, int) or isinstance(unified, bool) \
                or unified <= 0:
            problems.append("unified_eval_n=" + repr(unified))
        else:
            data.append("unified_eval_n=" + str(unified))
        for split, field in _DECLARED_SPLIT_FIELDS:
            declared = (declared_splits or {}).get(field)
            if declared is None or split not in measured:
                continue    # absent declaration is legal; missing splits
                            # already carry their own rows problem
            if declared != measured[split]:
                problems.append(
                    field + "_mismatch_declared=" + str(declared)
                    + "_measured=" + str(measured[split]))
        return GauntletItem(
            run_id=run_id, kind=KIND_DATASETS, leg=LEG_AUDIT,
            name=candidate_key, ok=not problems,
            details=tuple(problems) + tuple(data), raw_output=raw)

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
        items = [self.dry_run_precheck(kind, candidate_key, entry, run_id)]
        if kind == KIND_DATASETS:
            items.append(self.audit_reconciliation(
                candidate_key, entry, declared_splits, run_id))
        return items

    # ===== Shared internals =====

    def _dry_run_counterpart(self, kind):
        """Resolve the official counterpart for the OTHER matrix axis.

        Derived deterministically at read time — never a hardcoded key
        constant: the first official datasets key in file order with
        truthy ``Train`` for model candidates (the dry-run refuses
        Train-falsy tasks), the first official models key for dataset
        candidates. Read DIRECTLY from the official files so overlay
        state can never leak a custom key into the counterpart slot.

        WR-02 (09 review): the registry read is absorbed here — a
        missing/corrupt official file yields ``(None, diagnostic)``
        (the caller turns it into a failed item), never an exception
        across the service boundary.

        Args:
            kind (str): ``KIND_MODELS`` or ``KIND_DATASETS``.

        Returns:
            tuple[str | None, str | None]: ``(counterpart, None)`` —
            or ``(None, diagnostic)`` when the official registry cannot
            be read, or ``(None, None)`` when it holds no usable key.
        """
        try:
            if kind == KIND_MODELS:
                registry = self._official_registry(
                    registry_loader.DATASETS_INFO_NAME)
                for key, entry in registry.items():
                    if isinstance(entry, dict) and entry.get("Train"):
                        return key, None
                return None, None
            registry = self._official_registry(
                registry_loader.MODELS_INFO_NAME)
            for key in registry:
                return key, None
            return None, None
        except (OSError, json.JSONDecodeError,
                UnicodeDecodeError) as exc:
            # WR-06 (09 review): UnicodeDecodeError is the ValueError
            # SIBLING of json.JSONDecodeError (not a subclass — the
            # CR-01 registry_loader.py:132 reasoning): a non-UTF-8
            # official registry must degrade to the same failed item,
            # never cross the service boundary.
            return None, repr(exc)

    def _invoke(self, argv, env, timeout):
        """Run one subprocess leg through the injectable seam.

        Every launch failure is absorbed into a details tuple — a
        timeout or a crash NEVER crosses the service boundary as an
        exception (T-09-07); the caller turns the tuple into a failed
        item.

        Args:
            argv (list): the LIST argv (never a shell string).
            env (dict): the explicit env (os.environ + one override).
            timeout (int): the leg's timeout seconds.

        Returns:
            tuple: ``(proc, None)`` with the CompletedProcess-shaped
            result, or ``(None, details)`` when the runner timed out or
            crashed.
        """
        try:
            # errors="replace" (the download_queue WR-05 twin): the
            # gauntlet launches CJK/emoji-emitting scripts; a non-UTF-8
            # LC_CTYPE host decodes their output to replacement
            # characters — never a UnicodeDecodeError absorbed as a
            # spurious subprocess_error for a kernel that ran fine.
            proc = self._runner(argv, capture_output=True, text=True,
                                errors="replace",
                                timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            return None, ("timeout",
                          "timeout_seconds=" + str(timeout))
        except Exception as exc:  # noqa: BLE001 — the service boundary
            # (T-09-07): ANY launch failure yields a failed item, never
            # an exception crossing to the panel worker.
            return None, ("subprocess_error", repr(exc))
        return proc, None

    @staticmethod
    def _failed_item(run_id, kind, leg, name, details, raw_output=""):
        """Build one failed item (the shared failure-path shape)."""
        return GauntletItem(
            run_id=run_id, kind=kind, leg=leg, name=name, ok=False,
            details=tuple(details), raw_output=raw_output)

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


def _as_entry(entry):
    """Coerce one candidate value to the dict staging requires.

    Args:
        entry: the caller's candidate field values.

    Returns:
        dict: ``entry`` when it is already a dict, else ``{}`` (the
        validator upstream owns shape problems — staging never crashes).
    """
    return dict(entry) if isinstance(entry, dict) else {}
