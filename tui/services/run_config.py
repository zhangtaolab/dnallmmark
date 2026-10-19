"""
run_config — the slot-4 composition service (Phase 11, 11-02; CFG-01/
CFG-02/CFG-03 + LNC-03's service-tier foundation).

The pure brain under the run-config screen and the launch confirmation: the
run-spec model + collect-all validation, XDG persistence of the slot-4
OWN selection, directory resolution, the same-source dry-run preview,
the E2' verdict + typed-phrase check, the PROBE_INELIGIBLE read-source
extraction, and run_sweep argv composition. Every verdict the launch
gate enforces lives HERE, where no widget path can skip it (D-07 /
LNC-03); screens render, never compute.

Contract (locked decisions):

- D-01 (slot-4-owned state): this service persists its OWN models/
  tasks selection + params + dirs to ``settings.state_dir() /
  run_config.json`` (schema_version 1, atomic writes, tolerant load).
  It never reads the slot-2 selection service, presets, or templates —
  the preview and the launch read this screen's selection only.
- D-05 (same-source preview): the preview imports the pure planning
  functions from ``run_sweep`` (module-level top-level import through
  the existing ``pipeline/`` sys.path root — stdlib-only and
  headless-importable, live-probed 0.012s with zero torch) and NEVER
  re-implements enumeration: ``preview`` returns the
  ``enumerate_matrix`` output VERBATIM (tuples; 4-tuples under curve
  fractions) plus counts. Importing this module leaves torch/dnallm
  absent from ``sys.modules`` (pinned by the tier-1 suite).
- D-02/D-07 (E2' boundary): ``is_full_e2x`` compares BASE model names
  (alias-stripped via ``run_sweep.base_model_name``) and tasks against
  the OFFICIAL-ONLY key sets loaded by direct ``json.load`` of
  ``pipeline/models_info.json`` + ``datasets_info.json`` — overlay-
  free, NEVER ``registry_loader`` (the overlay merges custom entries
  into the enumeration; comparing against the merged view would
  under-gate — Pitfall 5). Predicate: ``models_base superset official
  and tasks superset official and len(seeds) >= 3``. SUPerset, not
  equality (O4 resolution): a custom+full mix STILL escalates to the
  typed gate — the run contains the full re-run, and under-gating is
  the hazard; UI-SPEC auto-default #9's "custom => never E2'" wording
  is superseded by this safer reading. Unreadable/shape-invalid
  official registries surface as a fail-closed diagnostic — the
  verdict NEVER returns True over silent empty sets (the caller
  surfaces the diagnostic as a problem; T-11-02-02). The typed-phrase
  check is exact string equality on the resolved output-root basename
  and lives in THIS tier — the modal can render its output, never
  bypass it (D-07).
- D-14/D-19 (dirs): defaults are repo-relative (``./finetuned``, cache
  absent — and, since 261014-c2l, BOTH roots absent) and stay
  repo-relative for DISPLAY; any explicit override resolves to an
  ABSOLUTE path (against REPO_ROOT) before argv threading. D-19 is
  RETIRED (261014-c2l): the dataset root now threads ``--dataset_root``
  LIVE, joined by the new ``--model_root`` — present-only, absolute,
  in the pinned compose_argv tail order, consuming the pipeline flags
  of the same names. The pre-change display-only default
  ``./datasets`` maps to UNSET at load (``LEGACY_DATASET_ROOT_DEFAULT``)
  so every pre-change persisted state file keeps launching
  byte-identically (the value was never threaded; threading it would
  double the ``datasets/`` path segment).
  A nonexistent output root is advisory-only (the sweep driver
  mkdirs it); resolution never fails on it.
- D-12 (absent parity in composition): ``compose_argv`` threads a
  flag ONLY when present — absent flags contribute ZERO argv
  elements; the exact element order is pinned by the tier-1 suite.
- D-11 ([r] re-run): ``compose_from_failures_argv`` targets
  ``run_sweep --from-failures``. CR-01 (phase-11 review) retired the
  "never the full matrix by construction" premise — a COMPLETE failures
  manifest re-run over 3 seeds IS the full matrix — so the composed
  path's E2' gate lives in ``sweep_launcher.launch_from_failures``
  (the effective matrix recomputed and gated before this composer
  runs; this argv builder stays mechanical).
- PROBE_INELIGIBLE (Pitfall 7): the frozen list lives in
  ``pipeline/run_finetune.py``, which imports torch at module top and
  is therefore NEVER imported here — the names are extracted from the
  file read as SOURCE TEXT (the tests/test_run_finetune_contracts.py
  read-source-never-import pattern) and never duplicated anywhere
  else.
- Zero copied enumeration logic (D-05 prohibition): everything matrix-
  shaped derives from the imported ``run_sweep`` functions; any alias
  math in this module is a violation.

Tolerance policy: ``load_state`` NEVER raises — a missing, corrupt,
or shape-drifted state file returns the DEFAULT spec (seeds 42/43/44,
PEFT none, variant none, subset off, output ``./finetuned``, both
storage roots unset) whole, never a partially-misread one. A
pre-change file whose ``dirs.dataset_root`` is exactly the retired
display-only default loads as UNSET (the legacy mapping above).
Since 261014-f4w the loaded (or default) spec is post-processed by
``seed_directory_defaults`` over ``directories_config``
(the user-owned ``directories.json`` startup file, read tolerantly):
the file seeds DEFAULTS, session state overrides — and every
``load_state`` consumer (the env kernels' root kwargs, the slot-4
input prefill, the slot-1 storage overview) is file-aware through
that ONE seam. The materialization consequence is honest and
designed: the next preview save persists seeded values into
``run_config.json`` as session state.
Validation mirrors run_sweep's own
bounds but returns collect-all problems as machine tuples
  ``(field_code, value)`` — data, never screen copy; the sys.exit-ing
  run_sweep validators are never called from parse paths.

ZERO textual imports (the services-tier invariant declared in
``tui/services/__init__.py``; locked by
``tests/tui/test_import_lock.py`` — the glob extends over this module
automatically). ZERO Chinese literals (the WR-05 services i18n lock).
Dependencies: stdlib + ``run_sweep`` (same-source) + the sibling
``settings`` service (state root + atomic write).
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path

import directories_config  # top-level module (pipeline/ sys.path root, the F4W startup config — stdlib-only, import-purity holds)
import run_sweep  # top-level module (pipeline/ sys.path root, D-05 same-source)

from tui.services import settings

# ===== Locations + pinned constants =====

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The sweep driver this service composes argv for (D-06: execution is
#: ALWAYS a run_sweep.py subprocess — never in-process).
RUN_SWEEP_SCRIPT = REPO_ROOT / "pipeline" / "run_sweep.py"

#: The default registry dir for preview/official-key loads (the
#: committed official registries).
DEFAULT_REGISTRY_DIR = REPO_ROOT / "pipeline"

#: The torch-importing pipeline module read as SOURCE TEXT for the
#: frozen probe-ineligible names (Pitfall 7 — never imported).
RUN_FINETUNE_SOURCE = REPO_ROOT / "pipeline" / "run_finetune.py"

#: Slot-4 persistence (D-01): the run-config state file under the XDG
#: STATE root (``DNALLMMARK_TUI_STATE_DIR`` injectable; atomic writes
#: through ``settings``).
RUN_CONFIG_FILE_NAME = "run_config.json"
SCHEMA_VERSION = 1

#: The param vocabularies (the run_sweep flag choices verbatim).
PEFT_MODES = ("none", "lora", "ia3")
CONFIG_VARIANTS = ("none", "head", "probe", "curve")

#: D-14 defaults: repo-relative for display; argv always threads the
#: absolute resolution.
DEFAULT_OUTPUT_ROOT = "./finetuned"
#: The RETIRED D-19 display-only default (261014-c2l): no longer the
#: live RunSpec default — consumed ONLY by the tolerant-load legacy
#: migration, which maps a persisted dataset_root of exactly this
#: value to None (the value was never threaded, and threading it would
#: resolve "datasets/..." under <repo>/datasets producing a doubled
#: path — byte-identical launches from pre-change state files instead).
LEGACY_DATASET_ROOT_DEFAULT = "./datasets"
DEFAULT_SEEDS = (42, 43, 44)

#: Machine problem codes — collect-all validation vocabulary (the
#: screens render copy over these, never parse them).
PROBLEM_EMPTY_SELECTION = "empty_selection"
PROBLEM_VARIANT_PEFT = "variant_peft"
PROBLEM_PROBE_INELIGIBLE = "probe_ineligible"
PROBLEM_SEEDS_INVALID = "seeds_invalid"
PROBLEM_CURVE_INVALID = "curve_invalid"
PROBLEM_EPOCHS_INVALID = "epochs_invalid"
PROBLEM_EBS_INVALID = "ebs_invalid"
#: WR-07 (phase-11 review): an output root whose resolved form is the
#: filesystem root (an empty basename — and an empty E2' expected
#: phrase, which must never satisfy the typed gate).
PROBLEM_OUTPUT_ROOT_INVALID = "output_root_invalid"

#: The screen's field-dict keys (the run_sweep flag vocabulary; the
#: params pane fields carry these names).
PARAM_SEEDS = "seeds"
PARAM_CURVE = "curve"
PARAM_EPOCHS = "num_train_epochs"
PARAM_EBS = "effective_batch_size"

# =====================================================================
# The run-spec model (CFG-01)
# =====================================================================


@dataclass(frozen=True)
class RunSpec:
    """One complete operator-composed run configuration — pure machine
    data, the single input of preview / validation / argv composition.

    The selection normalizes to sorted deduped tuples (the run_sweep
    sorted-set discipline — deterministic argv and persistence).
    ``models``/``tasks`` carry BASE registry names; alias names appear
    only in the enumerated cells (11-01's aliasing machinery).

    Attributes:
        models: selected BASE model keys (sorted, deduped; may be
            empty — composition validation refuses it).
        tasks: selected task keys (sorted, deduped; may be empty).
        seeds: seed fan-out (default ``(42, 43, 44)`` — the E2'
            three-seed boundary's default posture).
        peft: adapter mode, one of ``PEFT_MODES`` (default "none").
        config_variant: variant lane, one of ``CONFIG_VARIANTS``
            (default "none").
        curve_fractions: curve-lane fractions in (0, 1], sorted
            (empty = lane off).
        subset_file: fairness-subset map path (None = off).
        num_train_epochs: epoch override (None = YAML governs).
        effective_batch_size: target effective batch size (None = the
            child's YAML gradient-accumulation governs).
        output_root: sweep output root, repo-relative by default
            (D-14; ``DEFAULT_OUTPUT_ROOT``).
        dataset_root: dataset storage root — threads ``--dataset_root``
            (absolute against REPO_ROOT) when set (D-19 retired,
            261014-c2l; None = the child's script-dir resolution
            governs).
        model_root: model storage root — threads ``--model_root``
            (absolute against REPO_ROOT) when set (261014-c2l; None =
            the child's script-dir resolution governs).
        log_dir: error-log directory — threads ``--log_dir`` (absolute
            against REPO_ROOT) when set (261014-f4w; None = the child's
            own ``./logs`` default governs).
        cache_dir: HF cache override (None = the child's env/default
            resolution governs).
    """

    models: tuple[str, ...]
    tasks: tuple[str, ...]
    seeds: tuple[int, ...] = DEFAULT_SEEDS
    peft: str = "none"
    config_variant: str = "none"
    curve_fractions: tuple[float, ...] = ()
    subset_file: str | None = None
    num_train_epochs: int | None = None
    effective_batch_size: int | None = None
    output_root: str = DEFAULT_OUTPUT_ROOT
    dataset_root: str | None = None
    model_root: str | None = None
    log_dir: str | None = None
    cache_dir: str | None = None

    def __post_init__(self):
        object.__setattr__(
            self, "models", tuple(sorted(set(self.models))))
        object.__setattr__(
            self, "tasks", tuple(sorted(set(self.tasks))))
        object.__setattr__(
            self, "seeds", tuple(sorted(set(self.seeds))))
        object.__setattr__(
            self, "curve_fractions",
            tuple(sorted(set(self.curve_fractions))))


#: The tolerant-load fallback: the defaults spec with an EMPTY
#: selection (a corrupt/drifted file resets to defaults, never to a
#: guessed partial state).
DEFAULT_RUN_SPEC = RunSpec(models=(), tasks=())


# =====================================================================
# Param parsing (collect-all, machine problems)
# =====================================================================


def _clean_str(value):
    """The field value as a stripped str; None for None/empty."""
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    token = value.strip()
    return token or None


def _parse_seeds(value):
    """Parse a comma-separated int seed list (the run_sweep seeds
    discipline mirrored WITHOUT its sys.exit: skip empty elements,
    dedupe, sort). Returns the tuple, or None when any token is not
    an int or nothing parses (provided-but-empty is invalid — the
    WR-14 spirit)."""
    tokens = value.split(",")
    seeds = []
    for part in tokens:
        token = part.strip()
        if not token:
            continue
        try:
            seeds.append(int(token))
        except ValueError:
            return None
    if not seeds:
        return None
    return tuple(sorted(set(seeds)))


def _parse_fractions(value):
    """Parse a comma-separated fraction list in (0, 1] (the run_sweep
    parse_curve_fractions bounds mirrored WITHOUT its sys.exit:
    duplicates collapse, order sorts ascending). Returns the tuple, or
    None when any token is non-numeric, out of bounds, or nothing
    parses."""
    fractions = []
    for part in value.split(","):
        token = part.strip()
        if not token:
            return None
        try:
            number = float(token)
        except ValueError:
            return None
        if not 0 < number <= 1:
            return None
        fractions.append(number)
    if not fractions:
        return None
    return tuple(sorted(set(fractions)))


def _parse_positive_int(value):
    """Parse an int >= 1 (the run_sweep flag_problems bound). Returns
    the int or None."""
    try:
        number = int(value.strip())
    except ValueError:
        return None
    if number < 1:
        return None
    return number


def parse_params(raw):
    """Parse the screen's field dict of strings into RunSpec partials.

    Collect-all (the sweep driver's validation vocabulary): every
    field's problem is listed in one pass, each problem a machine
    tuple ``(code, raw_value)``; an INVALID field contributes NO
    partial (the caller blocks on the problems before composing), an
    ABSENT or cleared field contributes no partial either (the RunSpec
    constructor defaults govern). The sys.exit-ing run_sweep
    validators are never called — the bounds are mirrored here.

    Args:
        raw (dict): the params pane's field values, keyed by the
            ``PARAM_*`` vocabulary (``seeds``, ``curve``,
            ``num_train_epochs``, ``effective_batch_size``); values
            are strings (None = field cleared).

    Returns:
        tuple[dict, tuple[tuple[str, object], ...]]: ``(partials,
        problems)`` — partials is a dict of valid parsed kwargs
        (``seeds`` / ``curve_fractions`` / ``num_train_epochs`` /
        ``effective_batch_size``), problems the collect-all list.
    """
    partials: dict = {}
    problems: list[tuple[str, object]] = []

    raw_seeds = raw.get(PARAM_SEEDS)
    if raw_seeds is not None:
        seeds = _parse_seeds(raw_seeds) if isinstance(raw_seeds, str) else None
        if seeds is None:
            problems.append((PROBLEM_SEEDS_INVALID, raw_seeds))
        else:
            partials["seeds"] = seeds

    raw_curve = _clean_str(raw.get(PARAM_CURVE))
    if raw_curve is not None:
        fractions = _parse_fractions(raw_curve)
        if fractions is None:
            problems.append((PROBLEM_CURVE_INVALID, raw.get(PARAM_CURVE)))
        else:
            partials["curve_fractions"] = fractions

    raw_epochs = _clean_str(raw.get(PARAM_EPOCHS))
    if raw_epochs is not None:
        epochs = _parse_positive_int(raw_epochs)
        if epochs is None:
            problems.append((PROBLEM_EPOCHS_INVALID, raw.get(PARAM_EPOCHS)))
        else:
            partials["num_train_epochs"] = epochs

    raw_ebs = _clean_str(raw.get(PARAM_EBS))
    if raw_ebs is not None:
        ebs = _parse_positive_int(raw_ebs)
        if ebs is None:
            problems.append((PROBLEM_EBS_INVALID, raw.get(PARAM_EBS)))
        else:
            partials["effective_batch_size"] = ebs

    return partials, tuple(problems)


# =====================================================================
# Composition validation (the 11-01 driver refusals, mirrored)
# =====================================================================


def validate_composition(spec, probe_ineligible):
    """Validate a spec's composition — collect-all machine problems.

    Mirrors the sweep driver's own start-time refusals (11-01) as
    cheap composition-time prevention; the child stays authoritative
    in every case. Problems:

    - ``("empty_selection", None)`` when models OR tasks is empty;
    - ``("variant_peft", "{variant}+{peft}")`` when a variant lane
      and an adapter lane are both set (two alias suffixes cannot
      name one cell);
    - ``("probe_ineligible", model)`` — ONE per selected model — when
      variant is ``probe`` and the model is in the frozen
      probe-ineligible list;
    - ``("output_root_invalid", output_root)`` — WR-07 (phase-11
      review) — when the resolved output root is the filesystem root
      (empty basename): the E2' expected phrase would be the empty
      string (the typed gate must never compare against it) and the
      sweep would scatter cell dirs directly under ``/``.

    Args:
        spec (RunSpec): the composed spec (BASE model names).
        probe_ineligible (frozenset[str]): the frozen probe-ineligible
            names (``probe_ineligible()`` reads them from the real
            pipeline source).

    Returns:
        tuple[tuple[str, object], ...]: the collect-all problems
        (empty = composition clean).
    """
    problems: list[tuple[str, object]] = []
    if not spec.models or not spec.tasks:
        problems.append((PROBLEM_EMPTY_SELECTION, None))
    if spec.config_variant != "none" and spec.peft != "none":
        problems.append((
            PROBLEM_VARIANT_PEFT,
            f"{spec.config_variant}+{spec.peft}",
        ))
    if spec.config_variant == "probe":
        for model in spec.models:
            if model in probe_ineligible:
                problems.append((PROBLEM_PROBE_INELIGIBLE, model))
    if Path(spec.output_root).resolve().name == "":
        problems.append((PROBLEM_OUTPUT_ROOT_INVALID, spec.output_root))
    return tuple(problems)


# =====================================================================
# XDG persistence (D-01)
# =====================================================================


def _state_path(state_path=None):
    if state_path is None:
        return settings.state_dir() / RUN_CONFIG_FILE_NAME
    return Path(state_path)


def _persist_payload(spec):
    """The persisted document: schema envelope + selection + params +
    dirs (the exact field set — nothing outside it may appear; six dirs
    keys counting output_root, log_dir joined 261014-f4w)."""
    return {
        "schema_version": SCHEMA_VERSION,
        "models": list(spec.models),
        "tasks": list(spec.tasks),
        "params": {
            "seeds": list(spec.seeds),
            "peft": spec.peft,
            "config_variant": spec.config_variant,
            "curve_fractions": list(spec.curve_fractions),
            "subset_file": spec.subset_file,
            "num_train_epochs": spec.num_train_epochs,
            "effective_batch_size": spec.effective_batch_size,
        },
        "dirs": {
            "output_root": spec.output_root,
            "dataset_root": spec.dataset_root,
            "model_root": spec.model_root,
            "log_dir": spec.log_dir,
            "cache_dir": spec.cache_dir,
        },
    }


def save_state(spec, state_path=None):
    """Persist the spec to ``settings.state_dir() / run_config.json``
    (or an explicit path) through ``settings.atomic_write`` — a reader
    never observes a torn file (T-08-03).

    Args:
        spec (RunSpec): the spec to persist.
        state_path: an explicit file path; None resolves the XDG state
            root default (tests inject ``DNALLMMARK_TUI_STATE_DIR``).
    """
    settings.atomic_write(
        _state_path(state_path),
        json.dumps(
            _persist_payload(spec),
            indent=4,
            ensure_ascii=False,
            sort_keys=True,
        ),
    )


def _str_tuple(value):
    """A persisted list of str -> sorted deduped tuple; None when the
    shape is wrong (never coerces a drifted value)."""
    if not isinstance(value, list):
        return None
    if any(not isinstance(item, str) or not item for item in value):
        return None
    return tuple(sorted(set(value)))


def _int_tuple(value):
    """A persisted list of int (bool excluded) -> sorted deduped
    tuple; None when the shape is wrong or empty."""
    if not isinstance(value, list) or not value:
        return None
    numbers = []
    for item in value:
        if not isinstance(item, int) or isinstance(item, bool):
            return None
        numbers.append(item)
    return tuple(sorted(set(numbers)))


def _fraction_tuple(value):
    """A persisted fraction list -> sorted deduped tuple in (0, 1];
    None when the shape/bounds are wrong (an empty list = lane off is
    VALID and returns ``()``)."""
    if not isinstance(value, list):
        return None
    fractions = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            return None
        number = float(item)
        if not 0 < number <= 1:
            return None
        fractions.append(number)
    return tuple(sorted(set(fractions)))


def _optional_int_at_least_one(value):
    """A persisted int >= 1 or None; None otherwise (never coerces a
    drifted value — the caller treats None as default-whole-spec)."""
    if value is None:
        return True, None
    if isinstance(value, int) and not isinstance(value, bool) and value >= 1:
        return True, value
    return False, None


def _optional_str(value):
    """A persisted str (non-empty) or None; shape failure flagged."""
    if value is None:
        return True, None
    if isinstance(value, str) and value:
        return True, value
    return False, None


def _spec_from_doc(doc):
    """Rebuild a RunSpec from a persisted document; None when ANY
    field's shape/vocabulary is off — the whole-default policy (a
    partially-misread spec is worse than a reset one)."""
    models = _str_tuple(doc.get("models"))
    tasks = _str_tuple(doc.get("tasks"))
    if models is None or tasks is None:
        return None
    params = doc.get("params")
    dirs = doc.get("dirs")
    if not isinstance(params, dict) or not isinstance(dirs, dict):
        return None

    seeds = _int_tuple(params.get("seeds"))
    if seeds is None:
        return None
    peft = params.get("peft")
    config_variant = params.get("config_variant")
    if peft not in PEFT_MODES or config_variant not in CONFIG_VARIANTS:
        return None
    fractions = _fraction_tuple(params.get("curve_fractions"))
    if fractions is None:
        return None
    ok_epochs, epochs = _optional_int_at_least_one(
        params.get("num_train_epochs"))
    ok_ebs, ebs = _optional_int_at_least_one(
        params.get("effective_batch_size"))
    ok_subset, subset = _optional_str(params.get("subset_file"))
    if not (ok_epochs and ok_ebs and ok_subset):
        return None

    output_root = dirs.get("output_root")
    if not isinstance(output_root, str) or not output_root:
        return None
    ok_dataset, dataset_root = _optional_str(dirs.get("dataset_root"))
    ok_model_root, model_root = _optional_str(dirs.get("model_root"))
    ok_log_dir, log_dir = _optional_str(dirs.get("log_dir"))
    ok_cache, cache_dir = _optional_str(dirs.get("cache_dir"))
    if not (ok_dataset and ok_model_root and ok_log_dir and ok_cache):
        return None
    # 261014-c2l legacy migration: the D-19 display-only default was
    # never threaded; mapping the exact literal to unset preserves
    # byte-identical launches from pre-change state files (threading it
    # would resolve "datasets/..." under <repo>/datasets, doubling the
    # path segment). Any OTHER persisted custom value loads through
    # live — the feature's purpose.
    if dataset_root == LEGACY_DATASET_ROOT_DEFAULT:
        dataset_root = None

    return RunSpec(
        models=models,
        tasks=tasks,
        seeds=seeds,
        peft=peft,
        config_variant=config_variant,
        curve_fractions=fractions,
        subset_file=subset,
        num_train_epochs=epochs,
        effective_batch_size=ebs,
        output_root=output_root,
        dataset_root=dataset_root,
        model_root=model_root,
        log_dir=log_dir,
        cache_dir=cache_dir,
    )


def seed_directory_defaults(spec, file_dirs):
    """Fill a spec's UNSET dir fields from the startup file's values.

    The F4W-01 mount-time seeding contract: the file seeds DEFAULTS,
    session state overrides — every SET field survives untouched, and
    ``output_root`` (str-typed with a default, so the default literal
    is the only seedable signal — the documented conflation) fills only
    when the loaded value is exactly ``DEFAULT_OUTPUT_ROOT``. The seed
    is a PREFILL the operator sees in the slot-4 inputs and can edit,
    with one honest materialization consequence: the next preview save
    persists seeded values into ``run_config.json`` as session state
    (the designed override semantics).

    Args:
        spec (RunSpec): the loaded (or default) spec.
        file_dirs (dict[str, str]): ``load_directories_tolerant()``'s
            view (already stripped-non-empty by the loader).

    Returns:
        RunSpec: the seed-applied spec (the input spec unchanged on an
        empty dict — the byte-identical-when-absent case).
    """
    if not file_dirs:
        return spec
    changes: dict[str, object] = {}
    for key in ("model_root", "dataset_root", "log_dir", "cache_dir"):
        if getattr(spec, key) is None and file_dirs.get(key):
            changes[key] = file_dirs[key]
    if (spec.output_root == DEFAULT_OUTPUT_ROOT
            and file_dirs.get("output_root")):
        changes["output_root"] = file_dirs["output_root"]
    if not changes:
        return spec
    return replace(spec, **changes)


def load_state(state_path=None):
    """Load the persisted spec — tolerant, NEVER raises — then apply
    the directories.json seeding (261014-f4w).

    A missing file, corrupt JSON, a forward-dated schema_version, or
    ANY shape drift (wrong field types, out-of-vocabulary enums,
    out-of-bounds numerics) returns ``DEFAULT_RUN_SPEC`` WHOLE — never
    a partially-misread spec and never an exception (the settings
    contract; T-11-02-05). The loaded (or default) spec is then
    post-processed through ``seed_directory_defaults`` over
    ``directories_config.load_directories_tolerant()`` — the ONE seam
    every load_state consumer (the env kernels' root kwargs, the
    selection presence base, the slot-4 input prefill, the slot-1
    storage overview) is file-aware through; a missing/corrupt file
    seeds nothing (byte-identical load).

    Args:
        state_path: an explicit file path; None resolves the XDG state
            root default.

    Returns:
        RunSpec: the seed-applied persisted spec, or the seed-applied
        defaults.
    """
    try:
        doc = json.loads(_state_path(state_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        doc = None
    loaded = DEFAULT_RUN_SPEC
    if isinstance(doc, dict) and doc.get("schema_version") == SCHEMA_VERSION:
        parsed = _spec_from_doc(doc)
        if parsed is not None:
            loaded = parsed
    return seed_directory_defaults(
        loaded, directories_config.load_directories_tolerant())


# =====================================================================
# Directory resolution (D-14/D-19)
# =====================================================================


@dataclass(frozen=True)
class DirPlan:
    """The spec's directories in both forms — pure data.

    Attributes:
        output_root: the DISPLAY form, verbatim (repo-relative by
            default — the operator reads what they configured).
        output_root_abs: the ARGV form — always absolute, resolved
            against REPO_ROOT (a nonexistent root is advisory-only;
            the sweep driver mkdirs it).
        dataset_root: the DISPLAY form (None when unset).
        dataset_root_abs: the ABSOLUTE form (None when unset).
            Threaded as ``--dataset_root`` whenever set (D-19 retired,
            261014-c2l — the display-verbatim/argv-absolute split of
            D-14 applies to it like every other path).
        model_root: the DISPLAY form (None when unset).
        model_root_abs: the ABSOLUTE form (None when unset). Threaded
            as ``--model_root`` whenever set (261014-c2l) — the
            dataset-root twin.
        log_dir: the DISPLAY form (None when unset). The error-log
            directory (261014-f4w).
        log_dir_abs: the ABSOLUTE form (None when unset), resolved
            against REPO_ROOT the same way as every other path. Threaded
            as ``--log_dir`` whenever set.
        cache_dir_abs: the ABSOLUTE cache override (None when absent).
            Threaded — ``compose_argv`` threads ``--cache_dir``
            whenever set (IN-01, phase-11 review); ``DirPlan`` exposes
            the resolved form.
    """

    output_root: str
    output_root_abs: str
    dataset_root: str | None
    dataset_root_abs: str | None
    model_root: str | None
    model_root_abs: str | None
    log_dir: str | None
    log_dir_abs: str | None
    cache_dir_abs: str | None


def _abs_against_repo_root(value):
    """Resolve a possibly-relative path to an absolute string against
    REPO_ROOT (an absolute input passes through unchanged — pathlib
    join semantics). The TUI process may run from any CWD, and the
    launch composes ABSOLUTE flags so the subprocess's own CWD
    resolution cannot diverge (D-14)."""
    return str((REPO_ROOT / value).resolve())


def resolve_dirs(spec):
    """Project a spec's directory settings into their display/argv
    forms (D-14).

    Args:
        spec (RunSpec): the composed spec.

    Returns:
        DirPlan: display forms verbatim + absolute argv forms.
    """
    return DirPlan(
        output_root=spec.output_root,
        output_root_abs=_abs_against_repo_root(spec.output_root),
        dataset_root=spec.dataset_root,
        dataset_root_abs=(
            _abs_against_repo_root(spec.dataset_root)
            if spec.dataset_root else None
        ),
        model_root=spec.model_root,
        model_root_abs=(
            _abs_against_repo_root(spec.model_root)
            if spec.model_root else None
        ),
        log_dir=spec.log_dir,
        log_dir_abs=(
            _abs_against_repo_root(spec.log_dir)
            if spec.log_dir else None
        ),
        cache_dir_abs=(
            _abs_against_repo_root(spec.cache_dir)
            if spec.cache_dir else None
        ),
    )


# =====================================================================
# PROBE_INELIGIBLE — read-source extraction (Pitfall 7)
# =====================================================================

#: The frozen list's assignment shape in pipeline/run_finetune.py
#: (non-greedy to the closing bracket; the file's inline comments
#: carry no ']' — the parity test alarms on any drift).
_PROBE_INELIGIBLE_RE = re.compile(
    r"PROBE_INELIGIBLE\s*=\s*\[(.*?)\]", re.DOTALL)

#: String literals inside the brackets (single-line; the frozen names
#: carry no embedded quotes).
_STRING_LITERAL_RE = re.compile(r'"([^"\n]+)"')


def load_probe_ineligible(source_text):
    """Extract the frozen ``PROBE_INELIGIBLE`` names from source text.

    ``pipeline/run_finetune.py`` imports torch at module top, so the
    list is UNIMPORTABLE CPU-side — it is read as SOURCE TEXT (the
    tests/test_run_finetune_contracts.py read-source-never-import
    pattern). The names are never duplicated anywhere else; the tier-1
    parity test against the real file is the single drift alarm.

    Args:
        source_text (str): the pipeline module's text.

    Returns:
        frozenset[str]: the frozen names (9 today).

    Raises:
        ValueError: the literal is absent from the text.
    """
    match = _PROBE_INELIGIBLE_RE.search(source_text)
    if match is None:
        raise ValueError(
            "PROBE_INELIGIBLE literal not found in source text")
    return frozenset(_STRING_LITERAL_RE.findall(match.group(1)))


def probe_ineligible():
    """The frozen probe-ineligible names from the REAL pipeline
    source (``pipeline/run_finetune.py`` read as text).

    Returns:
        frozenset[str]: the frozen names.
    """
    return load_probe_ineligible(
        RUN_FINETUNE_SOURCE.read_text(encoding="utf-8"))


# =====================================================================
# Same-source preview (CFG-03 / D-05)
# =====================================================================


@dataclass(frozen=True)
class PreviewResult:
    """One dry-run preview — the imported enumeration VERBATIM plus
    its counts and the composition problems (pure data; the screen
    renders, never recomputes).

    Attributes:
        models_count: distinct model identities in the cells (ALIAS
            names under peft/variant — what will run; an unknown
            selection name intersects to zero here, honestly).
        tasks_count: distinct tasks in the cells.
        seeds_count: distinct seeds in the cells.
        fractions_count: the curve-lane fraction count, or None when
            the lane is off (an axis-mode property of the spec, not of
            the possibly-empty intersection).
        cells_count: total enumerated cells.
        cells: the ``run_sweep.enumerate_matrix`` tuples VERBATIM —
            (model, task, seed) triples, (model, task, seed, fraction)
            quadruples under curve fractions.
        problems: the Task-1 composition problems (empty selection /
            variant x peft / probe-ineligible), machine tuples.
    """

    models_count: int
    tasks_count: int
    seeds_count: int
    fractions_count: int | None
    cells_count: int
    cells: tuple
    problems: tuple[tuple[str, object], ...]


def preview(spec, registry_dir=None):
    """The same-source dry-run preview (D-05: the imported
    enumeration, never a re-implementation).

    The enumeration goes through ``run_sweep.enumerate_matrix`` with
    the spec's alias params (peft / config_variant / fractions) — the
    exact code path execution uses; alias cells appear as the
    enumeration emits them. The composition problems are validated
    over the REAL frozen probe-ineligible names.

    Args:
        spec (RunSpec): the composed spec.
        registry_dir: the registry dir for the enumeration; None
            resolves the committed ``pipeline/`` default.

    Returns:
        PreviewResult: counts + verbatim cells + problems.
    """
    if registry_dir is None:
        registry_dir = DEFAULT_REGISTRY_DIR
    if not spec.models or not spec.tasks:
        # run_sweep's filters are FALSY-semantics (None = no filter;
        # ``enumerate_matrix`` treats an empty list the same way), so
        # an empty selection fed straight in would silently enumerate
        # the FULL registry matrix — the WR-07 hazard the driver
        # refuses at its own start. The preview guards the same edge:
        # an empty selection previews ZERO cells and the
        # empty_selection problem says why.
        cells: tuple = ()
    else:
        cells = tuple(run_sweep.enumerate_matrix(
            list(spec.models), list(spec.tasks), list(spec.seeds),
            registry_dir,
            peft=spec.peft,
            fractions=list(spec.curve_fractions) or None,
            config_variant=spec.config_variant,
        ))
    return PreviewResult(
        models_count=len({cell[0] for cell in cells}),
        tasks_count=len({cell[1] for cell in cells}),
        seeds_count=len({cell[2] for cell in cells}),
        fractions_count=(
            len(spec.curve_fractions) if spec.curve_fractions else None),
        cells_count=len(cells),
        cells=cells,
        problems=validate_composition(spec, probe_ineligible()),
    )


# =====================================================================
# Official-only key sets (D-02 — the E2' authorization reference)
# =====================================================================

#: The official registry file names (direct json.load targets —
#: NEVER through ``registry_loader``, whose overlay view merges
#: custom entries into the enumeration; comparing against the merged
#: view would under-gate: Pitfall 5 / T-11-02-01).
MODELS_INFO_NAME = "models_info.json"
DATASETS_INFO_NAME = "datasets_info.json"


@dataclass(frozen=True)
class OfficialKeys:
    """The official-only key sets — the E2' predicate's reference.

    Attributes:
        models: every ``models_info.json`` key (the full official
            model registry).
        tasks: every ``datasets_info.json`` key with truthy ``Train``
            (the full official TRAINABLE task set — the only tasks the
            matrix can ever run).
        diagnostic: None when both files loaded; otherwise a message
            naming the unreadable/shape-invalid path(s). A diagnostic
            ALWAYS pairs with EMPTY sets — fail-closed: the gate
            blocks on the diagnostic instead of comparing against
            silently-empty sets (T-11-02-02).
    """

    models: frozenset[str]
    tasks: frozenset[str]
    diagnostic: str | None


def _load_official_doc(path):
    """Direct-load one official registry file; None when unreadable or
    shape-invalid (not a dict). Overlay state is structurally
    invisible here — plain ``json.load`` never consults the custom
    overlay dir or its env var."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            doc = json.load(handle)
    except (OSError, ValueError):
        return None
    if not isinstance(doc, dict):
        return None
    return doc


def official_keys(registry_dir=None):
    """Load the official-only key sets (overlay-free, Pitfall 5).

    Args:
        registry_dir: the dir holding the two official registry
            files; None resolves the committed ``pipeline/`` default.

    Returns:
        OfficialKeys: the key sets with a None diagnostic, or EMPTY
        sets plus a diagnostic naming every unreadable/shape-invalid
        path (fail-closed).
    """
    registry_dir = Path(
        DEFAULT_REGISTRY_DIR if registry_dir is None else registry_dir)
    models_doc = _load_official_doc(registry_dir / MODELS_INFO_NAME)
    tasks_doc = _load_official_doc(registry_dir / DATASETS_INFO_NAME)
    diagnostics = []
    if models_doc is None:
        diagnostics.append(
            f"unreadable or shape-invalid: "
            f"{registry_dir / MODELS_INFO_NAME}")
    if tasks_doc is None:
        diagnostics.append(
            f"unreadable or shape-invalid: "
            f"{registry_dir / DATASETS_INFO_NAME}")
    if diagnostics:
        return OfficialKeys(frozenset(), frozenset(), "; ".join(diagnostics))
    tasks = frozenset(
        key for key, entry in tasks_doc.items()
        if isinstance(entry, dict) and entry.get("Train")
    )
    return OfficialKeys(frozenset(models_doc), tasks, None)


# =====================================================================
# The E2' verdict + the typed phrase (D-02 / D-07)
# =====================================================================

#: The three-seed authorization boundary (D-02: 59 x 50 x 3).
E2X_MIN_SEEDS = 3


def is_full_e2x(spec, official):
    """The E2' verdict: does this spec contain the FULL official
    re-run (D-02)?

    Predicate: BASE model names superset the official models AND
    tasks superset the official trainable tasks AND at least three
    seeds. Aliases strip to base via ``run_sweep.base_model_name``
    (the same-source strip). SUPerset, not equality (O4): a
    custom+full mix still escalates to the typed gate — the run
    contains the full re-run, and under-gating is the hazard.

    Fail-closed: a diagnostic-bearing ``official`` NEVER returns True
    — empty official sets must not satisfy the superset predicate by
    vacuity; the caller surfaces the diagnostic as a problem and the
    gate blocks (T-11-02-02).

    Args:
        spec (RunSpec): the composed spec.
        official (OfficialKeys): the official-only key sets.

    Returns:
        bool: True only when the spec is a full official run with
        >= 3 seeds over a cleanly-loaded official reference.
    """
    if official.diagnostic is not None:
        return False
    bases = {
        run_sweep.base_model_name(model, spec.peft, spec.config_variant)
        for model in spec.models
    }
    return (bases >= official.models
            and set(spec.tasks) >= official.tasks
            and len(spec.seeds) >= E2X_MIN_SEEDS)


def expected_phrase(output_root):
    """The phrase the operator must type: the resolved output root's
    final path component (D-02).

    Args:
        output_root (str | Path): the output root as configured.

    Returns:
        str: the basename of its resolved absolute path.
    """
    return Path(output_root).resolve().name


def phrase_matches(typed, output_root):
    """The typed-phrase check — EXACT string equality (D-07).

    No stripping, no case folding, no prefix acceptance: the check
    lives in this service tier so no widget path can normalize its
    way past it. 11-03's launcher re-proves it before spawn.

    WR-07 (phase-11 review): FAILS CLOSED on an empty expected phrase
    — an output root resolving to the filesystem root (``Path("/").
    resolve().name == ""``) can never match, not even the empty string
    itself. An authorization boundary never fails open on a degenerate
    configuration.

    Args:
        typed (str): what the operator typed.
        output_root (str | Path): the configured output root.

    Returns:
        bool: True only on the exact expected phrase.
    """
    expected = expected_phrase(output_root)
    return bool(expected) and typed == expected


# =====================================================================
# run_sweep argv composition (D-06 / D-12 / D-11)
# =====================================================================


def compose_argv(spec):
    """Compose the run_sweep.py launch argv for a validated spec.

    A LIST of str (never a shell string — the phase-10/D-06
    discipline): the interpreter, the driver script, the three matrix
    filters, and the ABSOLUTE output root, then PRESENT-ONLY flag
    pairs appended in the pinned order ``--peft``, ``--config-
    variant``, ``--curve``, ``--subset_file``, ``--num_train_epochs``,
    ``--effective_batch_size``, ``--cache_dir``, ``--model_root``,
    ``--dataset_root``, ``--log_dir`` (the pinned storage tail,
    261014-c2l + 261014-f4w — the same order run_sweep's
    ``build_argv`` pins element-for-element). An ABSENT flag
    contributes ZERO elements (D-12 absent parity — a defaults spec
    composes exactly the 10 base elements). Path-valued flags resolve
    ABSOLUTE against REPO_ROOT before threading (D-14). The [p]
    modal and the 11-03 launcher consume this argv verbatim; the
    element order is pinned by the tier-1 suite, here only.

    Composition validation (empty selection / variant x peft /
    probe-ineligible) is the CALLER's gate step — this composer is
    mechanical and re-refuses only the empty selection defensively.

    Args:
        spec (RunSpec): the composed spec.

    Returns:
        list[str]: the launch argv.

    Raises:
        ValueError: models or tasks is empty (the defensive backstop —
            validation refuses it before composition ever runs).
    """
    if not spec.models or not spec.tasks:
        raise ValueError(
            "compose_argv refuses an empty selection — the preview/"
            "launch confirmation owns refusing it; this is the defensive "
            "backstop")
    argv = [
        sys.executable,
        str(RUN_SWEEP_SCRIPT),
        "--models", ",".join(spec.models),
        "--tasks", ",".join(spec.tasks),
        "--seeds", ",".join(str(seed) for seed in spec.seeds),
        "--output-root", _abs_against_repo_root(spec.output_root),
    ]
    if spec.peft != "none":
        argv += ["--peft", spec.peft]
    if spec.config_variant != "none":
        argv += ["--config-variant", spec.config_variant]
    if spec.curve_fractions:
        argv += ["--curve",
                 ",".join(str(f) for f in spec.curve_fractions)]
    if spec.subset_file:
        argv += ["--subset_file",
                 _abs_against_repo_root(spec.subset_file)]
    if spec.num_train_epochs is not None:
        argv += ["--num_train_epochs", str(spec.num_train_epochs)]
    if spec.effective_batch_size is not None:
        argv += ["--effective_batch_size",
                 str(spec.effective_batch_size)]
    if spec.cache_dir:
        argv += ["--cache_dir", _abs_against_repo_root(spec.cache_dir)]
    if spec.model_root:
        argv += ["--model_root", _abs_against_repo_root(spec.model_root)]
    if spec.dataset_root:
        argv += ["--dataset_root",
                 _abs_against_repo_root(spec.dataset_root)]
    if spec.log_dir:
        argv += ["--log_dir", _abs_against_repo_root(spec.log_dir)]
    return argv


def compose_from_failures_argv(failures_path, seeds, output_root,
                               peft="none", config_variant="none",
                               extra=None):
    """Compose the ``--from-failures`` re-run argv (D-11, the [r]
    path).

    A mechanical argv builder: the E2' gate for this path lives in the
    CALLER (``sweep_launcher.launch_from_failures`` recomputes the
    effective matrix — failure pairs × the requested seeds — and applies
    the same ``is_full_e2x`` predicate + typed-phrase gate as
    ``launch_spec``; CR-01, phase-11 review: a complete failures
    manifest over 3 seeds IS the full matrix). Seeds and the ABSOLUTE
    output root thread like the main path; peft/variant pairs are
    present-only; ``extra`` (a list of str, e.g. ``["--dry-run"]``)
    appends verbatim at the tail for the caller's own flags.

    Args:
        failures_path: the ``sweep_failures.json`` path (resolved
            absolute before threading).
        seeds (iterable[int]): the re-run seed fan-out.
        output_root (str | Path): the output root (absolute-resolved).
        peft (str): adapter mode (none = absent).
        config_variant (str): variant lane (none = absent).
        extra (list[str] | None): caller-owned trailing elements.

    Returns:
        list[str]: the re-run argv.
    """
    argv = [
        sys.executable,
        str(RUN_SWEEP_SCRIPT),
        "--from-failures", str(Path(failures_path).resolve()),
        "--seeds", ",".join(str(seed) for seed in seeds),
        "--output-root", _abs_against_repo_root(output_root),
    ]
    if peft != "none":
        argv += ["--peft", peft]
    if config_variant != "none":
        argv += ["--config-variant", config_variant]
    if extra:
        argv += list(extra)
    return argv


# =====================================================================
# argv_matrix — the compose_argv inverse (261017-uwr, UWR-2 Task 1)
# =====================================================================

#: The value-carrying run_sweep flags the inverse pair-scan knows (a
#: recognized flag consumes the NEXT element; everything else is
#: skipped — ``--dry-run``/``--priority-file`` never change the pair
#: set). ``--output-root`` is consumed so its VALUE can never be
#: misread as a flag position.
_ARGV_VALUE_FLAGS = frozenset({
    "--models", "--tasks", "--seeds", "--output-root", "--registry-dir",
    "--peft", "--config-variant", "--curve", "--from-failures",
    "--subset_file",
})


def _argv_flag_values(argv) -> dict[str, str]:
    """Pair-scan one argv into ``{flag: value}`` (a recognized flag
    consumes the next element; later occurrences win, argparse's own
    behavior). Tolerant by construction: unknown elements are skipped,
    a trailing flag with no value reads absent."""
    elements = [str(element) for element in argv]
    values: dict[str, str] = {}
    index = 0
    while index < len(elements):
        element = elements[index]
        if element in _ARGV_VALUE_FLAGS and index + 1 < len(elements):
            values[element] = elements[index + 1]
            index += 2
            continue
        index += 1
    return values


def _comma_filter_names(value: "str | None") -> "tuple[str, ...] | None":
    """A ``--models``/``--tasks`` comma list -> the name tuple; None
    when the flag is ABSENT (the driver's full-registry default,
    run_sweep.py:336-349 — a None filter enumerates every key) or
    parses to nothing (the driver's own sys.exit shape: a sweep that
    never launched)."""
    if value is None:
        return None
    names = tuple(token.strip() for token in value.split(",")
                  if token.strip())
    return names or None


def argv_matrix(argv, registry_dir=None) -> "frozenset[tuple[str, str]] | None":
    """Recover a sweep argv's PLANNED (model, task) pair matrix — the
    compose_argv inverse (261017-uwr, UWR-2).

    The liveness-evidence source for the monitor's three-state cell
    derivation: a discovered cell is RUNNING only when its
    (model, task) pair is a member of a live sweep's planned matrix.
    Everything derives through the SAME run_sweep functions execution
    uses (D-05 — never a naive cross product): the pairs are the
    ``enumerate_matrix`` cell projection (ALIAS names under
    peft/config-variant — the cell-dir identity), and a
    ``--from-failures`` argv threads the driver's own
    ``load_failure_pairs`` + the enumerate-and-filter the driver runs
    (run_sweep.py:1878-1896), so an alias-lane re-run's matrix carries
    the alias identity its cells will actually create (the pairs
    verbatim for a base re-run).

    Returns None — live-but-unknown, the caller renders that root with
    LEGACY activity semantics, never a false interrupt — when: no
    ``run_sweep.py`` element; ``--seeds`` absent (the driver marks it
    required) or unparseable; a ``--peft``/``--config-variant`` outside
    the vocabularies or a ``--curve`` outside (0, 1] (argv the driver's
    argparse would have refused); or the failures manifest unreadable /
    invalid (``load_failure_pairs``'s SystemExit/OSError/ValueError
    caught — the ``sweep_launcher._from_failures_refusal`` idiom).

    Documented edge (accepted, over-claim is the safe direction):
    ``--subset_file`` is not re-filtered — a subset-excluded pair reads
    live (renders queued, not interrupted) while its sweep runs.

    Args:
        argv: the launch argv (the registry's ``meta.argv`` or a probed
            ``/proc`` cmdline — any str sequence).
        registry_dir: the enumeration registry dir override; None
            resolves the committed ``pipeline/`` default.

    Returns:
        frozenset[tuple[str, str]] | None: the planned pair matrix, or
        None for an unparseable/non-sweep argv.
    """
    elements = [str(element) for element in argv]
    if not any(element.endswith("run_sweep.py") for element in elements):
        return None
    values = _argv_flag_values(elements)
    seeds = _parse_seeds(values["--seeds"]) if "--seeds" in values else None
    if seeds is None:
        return None
    peft = values.get("--peft", "none")
    if peft not in PEFT_MODES:
        return None
    config_variant = values.get("--config-variant", "none")
    if config_variant not in CONFIG_VARIANTS:
        return None
    fractions = None
    if "--curve" in values:
        fractions = _parse_fractions(values["--curve"])
        if fractions is None:
            return None
    enumeration_dir = Path(
        DEFAULT_REGISTRY_DIR if registry_dir is None else registry_dir)
    if values.get("--registry-dir"):
        enumeration_dir = Path(values["--registry-dir"])
    cells = run_sweep.enumerate_matrix(
        list(_comma_filter_names(values.get("--models")) or ()),
        list(_comma_filter_names(values.get("--tasks")) or ()),
        list(seeds),
        enumeration_dir,
        peft=peft,
        fractions=list(fractions) if fractions else None,
        config_variant=config_variant,
    )
    if "--from-failures" in values:
        try:
            failure_pairs = run_sweep.load_failure_pairs(
                values["--from-failures"], enumeration_dir)
        except (SystemExit, OSError, ValueError):
            return None
        cells = [
            cell for cell in cells
            if (run_sweep.base_model_name(cell[0], peft, config_variant),
                cell[1]) in failure_pairs
        ]
    return frozenset((str(cell[0]), str(cell[1])) for cell in cells)


# =====================================================================
# The directories.json save seam + the storage overview (261014-f4w)
# =====================================================================


def save_directory_defaults(spec, config_path=None):
    """Persist the spec's directory values as the startup defaults file.

    Writes the COMPLETE five-key document — a ``schema_version`` 1
    envelope with every ``DIRECTORY_KEYS`` key present, each value the
    RESOLVED ABSOLUTE form from ``resolve_dirs`` (``""`` for unset) —
    through ``settings.atomic_write`` to
    ``settings.config_dir() / directories.json`` (or the explicit
    path), returning the written path.

    Absolute-only storage is the divergence guard: bare-CLI resolution
    (CWD basis) and TUI resolution (REPO_ROOT basis) agree on every
    stored value, and the loader's empty-means-absent policy makes the
    all-empty save equivalent to defaults (the restore path is "clear
    the inputs and save").

    D-10 coexistence, write side: the TUI writes through
    ``settings.atomic_write`` over platformdirs while the pipeline
    reads through the hand-rolled strict resolver — the same-file
    agreement is test-pinned (``directories_config.config_path()``).

    Args:
        spec (RunSpec): the spec whose dir values become the defaults
            (the slot-4 ``s`` action composes it from the inputs).
        config_path: an explicit file path; None resolves the config
            root default.

    Returns:
        Path: the written file's path (for the success toast).
    """
    plan = resolve_dirs(spec)
    # The "" = unset convention covers output_root's default literal too
    # (the str-typed field always carries a value, so the DEFAULT literal
    # is the unset signal — the same conflation the seeding documents):
    # an all-defaults save writes five empty strings and loads back as
    # {} — exactly the defaults.
    values = {
        "model_root": plan.model_root_abs or "",
        "dataset_root": plan.dataset_root_abs or "",
        "output_root": (
            plan.output_root_abs
            if spec.output_root != DEFAULT_OUTPUT_ROOT else ""),
        "log_dir": plan.log_dir_abs or "",
        "cache_dir": plan.cache_dir_abs or "",
    }
    target = (Path(config_path) if config_path is not None
              else settings.config_dir()
              / directories_config.DIRECTORIES_FILE_NAME)
    settings.atomic_write(
        target,
        json.dumps(
            {"schema_version": SCHEMA_VERSION, **values},
            indent=4,
            ensure_ascii=False,
            sort_keys=True,
        ),
    )
    return target


@dataclass(frozen=True)
class StorageRow:
    """One storage-overview row — pure data (labels and glyphs live in
    strings/screens).

    Attributes:
        key: one of ``DIRECTORY_KEYS``.
        path: the EFFECTIVE absolute path for the key (spec projection
            or the documented display default).
        exists: a plain ``Path.exists()`` stat over the path.
        on_demand: True only for the cache row — lazily-created-on-
            first-use is a fact of the KEY (HF mkdirs it at training),
            so an absent cache is a neutral on-demand state, never a
            missing-dir error (261019-v3g, WINDOWS #33).
        writable: the writability probe answer, set ONLY for a PRESENT
            cache row (``_cache_writable``); None for every non-cache
            row and every absent cache row — present-but-unwritable is
            the real failure, absent-and-on-demand is not.

    The two 261019-v3g fields are ``repr=False`` deliberately: the row
    repr stays byte-stable for the diagnostics that already print it
    (the environmental defaults-test failure text on a live-pipeline
    box), while the fields remain first-class data for tests and the
    screen render.
    """

    key: str
    path: str
    exists: bool
    on_demand: bool = field(default=False, repr=False)
    writable: "bool | None" = field(default=None, repr=False)


def _cache_writable(path: str) -> bool:
    """The cache-row writability probe (261019-v3g, WINDOWS #33).

    A thin module-level ``os.access(path, os.W_OK)`` seam — advisory
    display data only, never a launch gate — and monkeypatchable in
    tests (the DETERMINISTIC unwritable pin: no chmod simulation, no
    uid dependence).

    Args:
        path: the EFFECTIVE cache path, already known to exist (the
            caller probes only present cache rows).

    Returns:
        bool: whether the current process may write into the dir.
    """
    return os.access(path, os.W_OK)


#: The unset display defaults, mirroring the REAL consumers (a launch
#: composed from a defaults spec resolves exactly these): both storage
#: roots resolve against the committed pipeline dir, the log dir
#: against pipeline/logs, the cache against the run_finetune module-top
#: ../../cache default (REPO_ROOT/cache).
_STORAGE_DEFAULTS = {
    "model_root": str(DEFAULT_REGISTRY_DIR),
    "dataset_root": str(DEFAULT_REGISTRY_DIR),
    "log_dir": str(DEFAULT_REGISTRY_DIR / "logs"),
    "cache_dir": str(REPO_ROOT / "cache"),
}


def storage_overview(spec=None):
    """The five effective storage directories for the overview display.

    Rows come back in ``DIRECTORY_KEYS`` order over the seed-applied
    ``load_state()`` (or an explicit spec): per key the spec's
    ``*_abs`` projection (``log_dir`` resolved against REPO_ROOT the
    same way), with the ``_STORAGE_DEFAULTS`` display defaults filling
    the unset keys and ``output_root`` always resolving (the str-typed
    field). ``exists`` is a plain ``Path.exists()`` stat. Since
    261019-v3g (WINDOWS #33) the cache row additionally carries
    ``on_demand`` True (a fact of the key) and, only when it EXISTS,
    the ``_cache_writable`` probe answer in ``writable`` — the display
    mirrors WHERE artifacts land for a launch composed from the current
    session state — the same seam the env kernels check roots through;
    presentation lives in the screen.

    Args:
        spec (RunSpec | None): an explicit spec; None derives from the
            seed-applied ``load_state()``.

    Returns:
        tuple[StorageRow, ...]: five rows in ``DIRECTORY_KEYS`` order.
    """
    loaded = spec if spec is not None else load_state()
    plan = resolve_dirs(loaded)
    projections = {
        "model_root": plan.model_root_abs,
        "dataset_root": plan.dataset_root_abs,
        "output_root": plan.output_root_abs,
        "log_dir": plan.log_dir_abs,
        "cache_dir": plan.cache_dir_abs,
    }
    rows = []
    for key in directories_config.DIRECTORY_KEYS:
        path = projections[key] or _STORAGE_DEFAULTS[key]
        exists = Path(path).exists()
        # 261019-v3g (WINDOWS #33): the cache dir is lazily created on
        # first use — a fact of the KEY, not the filesystem — so its
        # row is on_demand always, and writability is probed ONLY when
        # it exists (present-but-unwritable is the real failure; an
        # absent on-demand dir is never probed). Non-cache rows keep
        # both fields at their defaults: zero behavioral change to
        # paths or exists.
        on_demand = key == "cache_dir"
        writable = _cache_writable(path) if on_demand and exists else None
        rows.append(StorageRow(
            key=key, path=path, exists=exists,
            on_demand=on_demand, writable=writable))
    return tuple(rows)


def directory_picker_root(value):
    """The DirectoryTree root for one dir input's current value.

    The four-step fallback chain (F4W-05, pure Path logic):

    1. the STRIPPED value when it exists on disk;
    2. its nearest EXISTING ancestor (walk parents until one exists);
    3. REPO_ROOT;
    4. Path.home().

    The maintainer motivation: no hand-typed paths — the picker opens
    already rooted where the operator's value points, and a partially
    typed path still lands somewhere sensible. Determinism-under-test
    note: the Path.home() last resort is UNREACHABLE while REPO_ROOT
    exists (a checkout always has one) — kept for completeness over an
    ever-empty tree, documented as such.

    Args:
        value (str | None): the focused dir input's current value
            (empty/None skips straight to REPO_ROOT).

    Returns:
        Path: the picker's root directory.
    """
    stripped = (value or "").strip()
    if stripped:
        candidate = Path(stripped)
        if candidate.exists():
            return candidate
        for ancestor in candidate.parents:
            if ancestor.exists():
                return ancestor
    return REPO_ROOT
