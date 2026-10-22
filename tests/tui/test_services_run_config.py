"""
Tier-1 service tests for ``tui/services/run_config.py`` (Phase 11,
11-02 — CFG-01/02/03 + LNC-03's service-tier foundation).

Three lanes, per the plan:

- **Model/validation/persistence suite** (Task 1) — the RunSpec frozen
  dataclass + defaults, ``parse_params`` collect-all problem codes,
  ``validate_composition`` refusals (variant x peft, probe-eligible
  gating), the XDG ``run_config.json`` round-trip (tolerant load:
  missing/corrupt/shape-drift return the default spec, never raise),
  ``resolve_dirs`` repo-relative-default/absolute-override separation
  (D-14), and the D-05 import-purity probe (importing the service
  leaves torch/dnallm/transformers absent from ``sys.modules``).
- **Same-source preview + gates suite** (Task 2) —
  ``load_probe_ineligible`` read-source extraction (fixture text AND
  the real 9-name frozen list in pipeline/run_finetune.py — never
  imported, torch lives at its module top), ``preview`` over the real
  registries through the IMPORTED ``run_sweep.enumerate_matrix`` (tuple
  parity, curve 4-tuples, peft/variant alias names, composition
  problems), ``official_keys`` overlay-free loading (direct json.load,
  never registry_loader — Pitfall 5) with fail-closed diagnostics, the
  ``is_full_e2x`` superset predicate (D-02: official-only key sets,
  alias-stripped base names, >= 3 seeds), and the exact-match typed
  phrase (D-07).
- **argv composition suite** (Task 3) — ``compose_argv`` sweep-driver
  argv (LIST of str, present-only pairs in the pinned order, absent
  flags contribute ZERO elements — D-12 parity, absolute resolution of
  output_root/subset/cache against REPO_ROOT — D-14) and
  ``compose_from_failures_argv`` (the [r] re-run path, D-11).

Every persistence test injects a tmp state root via
``DNALLMMARK_TUI_STATE_DIR`` — the real ``~/.local/state/dnallmmark``
is never read or written.

See also:
    ``tui/services/run_config.py`` — the service under test.
    ``pipeline/run_sweep.py`` — the same-source planning functions
    (enumerate_matrix / base_model_name — imported, never copied).
    ``tests/tui/test_services_download_queue.py`` — the tier-1 idioms.
"""

import json
import subprocess
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
import run_sweep  # top-level module (pipeline/ sys.path root) — same-source parity

from tui.services import run_config, settings

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_REGISTRY_DIR = REPO_ROOT / "pipeline"
RUN_FINETUNE_PATH = REPO_ROOT / "pipeline" / "run_finetune.py"

#: Two committed model keys + three committed task keys for the
#: real-registry preview lane (2 x 3 x 3 = 18 cells — the count-parity
#: anchor; the keys themselves are committed registry data).
PREVIEW_MODELS = ("plant-dnabert-6mer", "plant-dnagpt-BPE")
PREVIEW_TASKS = ("GUE__emp_H3", "iDNA_ABF_datasets__5mC", "GUE__virus_species_40")

#: The frozen probe-ineligible names, pinned verbatim from
#: pipeline/run_finetune.py:527-537 (T-11-02-04 parity tripwire — the
#: UI-SPEC's stale "7 names" claim is corrected by this literal). BOTH
#: space spellings are load-bearing (two distinct registry rows).
PROBE_INELIGIBLE_NAMES = frozenset({
    "enformer-official-rough",
    "SPACE",
    "space",
    "borzoi-replicate-0",
    "flashzoi-replicate-0",
    "evo2_1b_base",
    "megaDNA_updated",
    "gpn-brassicales",
    "Omni-DNA-700M",
})


def pin_state_dir(monkeypatch, tmp_path):
    """Point the TUI state root at a tmp dir — the real XDG state home
    is never touched (the settings contract)."""
    state = tmp_path / "state"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    return state


def flag_value(argv, flag):
    """The argv element immediately following ``flag`` (the
    tests/test_sweep.py idiom)."""
    return argv[argv.index(flag) + 1]


# =====================================================================
# Lane 1 — import purity + RunSpec model (Task 1)
# =====================================================================


def test_importing_service_leaves_gpu_stack_absent():
    """D-05 codified in a FRESH interpreter: importing the service
    (which module-level-imports ``run_sweep`` for the pure planning
    functions) must leave torch/dnallm/transformers absent from
    ``sys.modules``. The live-probe discipline demands a subprocess —
    the SUITE's own process may legitimately hold torch by this point
    on the GB10 dev host (the env-check kernels import it when the
    gpu stack is installed), so an in-process assert would prove
    nothing about THIS module."""
    probe = (
        "import sys\n"
        f"sys.path.insert(0, {str(REAL_REGISTRY_DIR)!r})\n"
        f"sys.path.insert(0, {str(REPO_ROOT)!r})\n"
        "import tui.services.run_config\n"
        "assert 'run_sweep' in sys.modules, 'same-source import'\n"
        "for banned in ('torch', 'dnallm', 'transformers'):\n"
        "    assert banned not in sys.modules, banned\n"
        "print('pure')\n"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", probe],
        capture_output=True, text=True, cwd=REPO_ROOT, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "pure"


def test_runspec_defaults():
    """The defaults spec: seeds 42/43/44, PEFT none, variant none,
    curve off, subset off, no epochs/EBS override, repo-relative output
    root (D-14), both storage roots UNSET (the D-19 display-only
    dataset-root default retired, 261014-c2l), cache absent."""
    spec = run_config.RunSpec(models=("m",), tasks=("t",))
    assert spec.models == ("m",)
    assert spec.tasks == ("t",)
    assert spec.seeds == (42, 43, 44)
    assert spec.peft == "none"
    assert spec.config_variant == "none"
    assert spec.curve_fractions == ()
    assert spec.subset_file is None
    assert spec.num_train_epochs is None
    assert spec.effective_batch_size is None
    assert spec.batch_size is None
    assert spec.output_root == "./finetuned"
    assert spec.dataset_root is None
    assert spec.model_root is None
    assert spec.cache_dir is None
    assert spec.log_dir is None, (
        "the log dir defaults UNSET (261014-f4w) — the child's own "
        "./logs default governs"
    )


def test_runspec_is_frozen():
    """The download_queue dataclass discipline: machine data, never
    mutated in place. setattr (not attribute assignment): ty correctly
    reads frozen dataclass properties as read-only — the 08-01
    ty-vs-intent precedent; the noqa covers the inverse ruff conflict
    (B010)."""
    spec = run_config.RunSpec(models=("m",), tasks=("t",))
    with pytest.raises(FrozenInstanceError):
        setattr(spec, "peft", "lora")  # noqa: B010


def test_runspec_normalizes_selection_sorted_dedup():
    """Selection normalizes to sorted deduped tuples (the run_sweep
    sorted-set discipline, deterministic for argv + persistence)."""
    spec = run_config.RunSpec(
        models=("b-model", "a-model", "b-model"),
        tasks=("t2", "t1", "t1"),
    )
    assert spec.models == ("a-model", "b-model")
    assert spec.tasks == ("t1", "t2")


# =====================================================================
# Lane 1 — parse_params (Task 1)
# =====================================================================


def test_parse_params_happy_path_all_fields():
    """Every param parses from the screen's field dict of strings;
    seeds dedupe+sort (the run_sweep seeds discipline), curve
    fractions collapse sorted in (0, 1], epochs/EBS as ints."""
    partials, problems = run_config.parse_params({
        "seeds": "43, 42, 42",
        "curve": "0.5,0.25,0.5",
        "num_train_epochs": "3",
        "effective_batch_size": "16",
        "batch_size": "8",
    })
    assert problems == ()
    assert partials == {
        "seeds": (42, 43),
        "curve_fractions": (0.25, 0.5),
        "num_train_epochs": 3,
        "effective_batch_size": 16,
        "batch_size": 8,
    }


@pytest.mark.parametrize("raw", ["42,x", "1.5", "", "   "])
def test_parse_params_seeds_invalid(raw):
    """Any non-int seed token — or a provided-but-empty seeds field —
    is ONE collect-all problem carrying the raw value (machine data,
    the screen renders copy)."""
    partials, problems = run_config.parse_params({"seeds": raw})
    assert problems == (("seeds_invalid", raw),)
    assert "seeds" not in partials


@pytest.mark.parametrize("raw", ["0", "1.5", "0.0", "x,y"])
def test_parse_params_curve_invalid(raw):
    """Curve fractions outside (0, 1] or unparseable — one
    ``curve_invalid`` problem with the raw value (the run_sweep
    parse_curve_fractions bounds, mirrored WITHOUT its sys.exit)."""
    partials, problems = run_config.parse_params({"curve": raw})
    assert problems == (("curve_invalid", raw),)
    assert "curve_fractions" not in partials


@pytest.mark.parametrize("raw", ["0", "-1", "x", "1.5"])
def test_parse_params_epochs_invalid(raw):
    """Epochs must be an int >= 1 (the run_sweep flag_problems bound)."""
    partials, problems = run_config.parse_params({"num_train_epochs": raw})
    assert problems == (("epochs_invalid", raw),)
    assert "num_train_epochs" not in partials


@pytest.mark.parametrize("raw", ["0", "-1", "x", "2.5"])
def test_parse_params_ebs_invalid(raw):
    """effective_batch_size must be an int >= 1 (the run_sweep
    flag_problems bound)."""
    partials, problems = run_config.parse_params({"effective_batch_size": raw})
    assert problems == (("ebs_invalid", raw),)
    assert "effective_batch_size" not in partials


@pytest.mark.parametrize("raw", ["0", "-1", "x", "2.5"])
def test_parse_params_batch_size_invalid(raw):
    """261023-abu: batch_size must be an int >= 1 — the epochs/ebs shape
    verbatim over the per-device starting micro-batch (the run_sweep
    flag_problems bound mirrored; the shard CLI / run_sweep / dispatch
    stay the validation authorities)."""
    partials, problems = run_config.parse_params({"batch_size": raw})
    assert problems == (("batch_size_invalid", raw),)
    assert "batch_size" not in partials


def test_parse_params_empty_values_mean_absent():
    """A cleared optional field (None or whitespace) is OFF — no
    problem, no partial (the constructor defaults govern)."""
    partials, problems = run_config.parse_params({
        "num_train_epochs": "",
        "effective_batch_size": None,
        "batch_size": "  ",
        "curve": "  ",
    })
    assert problems == ()
    assert partials == {}


def test_parse_params_absent_keys_mean_defaults():
    """An empty field dict parses to zero partials and zero problems —
    every default lives on the RunSpec constructor."""
    partials, problems = run_config.parse_params({})
    assert partials == {}
    assert problems == ()


def test_parse_params_collects_all_problems_together():
    """Collect-all: every field's problem is listed in one pass, never
    first-fail-only (the validation vocabulary of the sweep driver)."""
    partials, problems = run_config.parse_params({
        "seeds": "x",
        "curve": "2",
        "num_train_epochs": "0",
        "effective_batch_size": "0",
        "batch_size": "0",
    })
    assert problems == (
        ("seeds_invalid", "x"),
        ("curve_invalid", "2"),
        ("epochs_invalid", "0"),
        ("ebs_invalid", "0"),
        ("batch_size_invalid", "0"),
    )
    assert partials == {}


# =====================================================================
# Lane 1 — validate_composition (Task 1)
# =====================================================================


FIXTURE_PROBE_INELIGIBLE = frozenset({"evo2_1b_base", "SPACE", "space"})


def test_validate_composition_clean_spec_has_no_problems():
    spec = run_config.RunSpec(
        models=("plant-dnabert-6mer",), tasks=("GUE__emp_H3",),
    )
    assert run_config.validate_composition(spec, FIXTURE_PROBE_INELIGIBLE) == ()


def test_validate_composition_empty_models():
    spec = run_config.RunSpec(models=(), tasks=("t",))
    assert run_config.validate_composition(spec, FIXTURE_PROBE_INELIGIBLE) == (
        ("empty_selection", None),
    )


def test_validate_composition_empty_tasks():
    spec = run_config.RunSpec(models=("m",), tasks=())
    assert run_config.validate_composition(spec, FIXTURE_PROBE_INELIGIBLE) == (
        ("empty_selection", None),
    )


@pytest.mark.parametrize("variant,peft", [
    ("probe", "lora"), ("probe", "ia3"),
    ("head", "lora"), ("head", "ia3"),
    ("curve", "lora"), ("curve", "ia3"),
])
def test_validate_composition_refuses_variant_x_peft(variant, peft):
    """The 11-01 driver refusal mirrored as a preview problem: two
    alias suffixes cannot name one cell (all 3 variants x both adapter
    modes)."""
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",), peft=peft, config_variant=variant,
    )
    assert run_config.validate_composition(spec, FIXTURE_PROBE_INELIGIBLE) == (
        ("variant_peft", f"{variant}+{peft}"),
    )


def test_validate_composition_probe_ineligible_one_problem_per_model():
    """variant=probe + selected ineligible models: ONE problem per
    model, in sorted selection order — collect-all, never
    first-only."""
    spec = run_config.RunSpec(
        models=("SPACE", "evo2_1b_base", "plant-dnabert-6mer"),
        tasks=("t",),
        config_variant="probe",
    )
    assert run_config.validate_composition(spec, FIXTURE_PROBE_INELIGIBLE) == (
        ("probe_ineligible", "SPACE"),
        ("probe_ineligible", "evo2_1b_base"),
    )


def test_validate_composition_probe_eligible_models_pass():
    """variant=probe over eligible models: no problem; and ineligible
    models under a NON-probe variant are fine (head/curve lanes have no
    eligibility list)."""
    spec = run_config.RunSpec(
        models=("evo2_1b_base",), tasks=("t",), config_variant="head",
    )
    assert run_config.validate_composition(spec, FIXTURE_PROBE_INELIGIBLE) == ()


def test_validate_composition_refuses_filesystem_root_output_root():
    """WR-07 (phase-11 review): an output root whose RESOLVED form is
    the filesystem root (basename "") is refused as a composition
    problem — such a root makes the E2' expected phrase the empty
    string (the fail-open hazard) and would scatter the sweep's cells
    directly under /."""
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",), output_root="/",
    )
    assert run_config.validate_composition(spec, FIXTURE_PROBE_INELIGIBLE) == (
        ("output_root_invalid", "/"),
    )


def test_phrase_matches_never_matches_an_empty_expected_phrase():
    """WR-07: the typed gate FAILS CLOSED on a degenerate phrase — an
    output root resolving to the filesystem root (expected_phrase "")
    can never match, not even the empty string itself (typing one char
    and deleting it must not flip the indicator to match and launch)."""
    assert run_config.expected_phrase("/") == ""
    assert run_config.phrase_matches("", "/") is False
    assert run_config.phrase_matches("anything", "/") is False
    assert run_config.phrase_matches("/", "/") is False


# =====================================================================
# Lane 1 — XDG persistence (Task 1)
# =====================================================================


def test_persistence_round_trip_defaults(monkeypatch, tmp_path):
    state = pin_state_dir(monkeypatch, tmp_path)
    spec = run_config.RunSpec(models=(), tasks=())
    run_config.save_state(spec)
    assert (state / "run_config.json").is_file()
    loaded = run_config.load_state()
    assert loaded == spec
    doc = json.loads((state / "run_config.json").read_text(encoding="utf-8"))
    assert doc["params"]["batch_size"] is None, (
        "an unset batch_size persists as None (261023-abu — like every "
        "optional param)"
    )


def test_persistence_round_trip_full_spec(monkeypatch, tmp_path):
    state = pin_state_dir(monkeypatch, tmp_path)
    spec = run_config.RunSpec(
        models=("b", "a"),
        tasks=("t2", "t1"),
        seeds=(7, 8),
        peft="lora",
        config_variant="probe",
        curve_fractions=(0.25, 0.5),
        subset_file="/tmp/subset.json",
        num_train_epochs=1,
        effective_batch_size=16,
        batch_size=8,
        output_root="/data/sweeps/run-a",
        dataset_root="/data/datasets",
        model_root="/data/models",
        cache_dir="/data/cache",
        log_dir="/data/logs",
    )
    run_config.save_state(spec)
    assert run_config.load_state() == spec
    doc = json.loads((state / "run_config.json").read_text(encoding="utf-8"))
    assert doc["schema_version"] == 1
    assert doc["models"] == ["a", "b"]
    assert doc["params"]["seeds"] == [7, 8]
    assert doc["params"]["peft"] == "lora"
    assert doc["params"]["config_variant"] == "probe"
    assert doc["params"]["curve_fractions"] == [0.25, 0.5]
    assert doc["params"]["batch_size"] == 8, (
        "a typed batch_size round-trips through params (261023-abu)"
    )
    assert doc["dirs"]["output_root"] == "/data/sweeps/run-a"
    assert doc["dirs"]["dataset_root"] == "/data/datasets"
    assert doc["dirs"]["model_root"] == "/data/models", (
        "the persisted dirs payload carries the new model_root key "
        "(261014-c2l)"
    )
    assert doc["dirs"]["log_dir"] == "/data/logs", (
        "the persisted dirs payload carries the log_dir key (261014-f4w)"
    )


def test_load_state_missing_file_returns_default(monkeypatch, tmp_path):
    pin_state_dir(monkeypatch, tmp_path)
    loaded = run_config.load_state()
    assert loaded == run_config.RunSpec(models=(), tasks=())


def test_load_state_corrupt_json_returns_default(monkeypatch, tmp_path):
    state = pin_state_dir(monkeypatch, tmp_path)
    state.mkdir(parents=True, exist_ok=True)
    (state / "run_config.json").write_text("{not json", encoding="utf-8")
    assert run_config.load_state() == run_config.RunSpec(models=(), tasks=())


def test_load_state_schema_drift_returns_default(monkeypatch, tmp_path):
    """A forward-dated schema_version is never misread (the
    download_queue SCHEMA_VERSION discipline)."""
    state = pin_state_dir(monkeypatch, tmp_path)
    state.mkdir(parents=True, exist_ok=True)
    (state / "run_config.json").write_text(
        json.dumps({"schema_version": 2, "models": [], "tasks": []}),
        encoding="utf-8",
    )
    assert run_config.load_state() == run_config.RunSpec(models=(), tasks=())


@pytest.mark.parametrize("doc", [
    {"schema_version": 1, "models": "not-a-list", "tasks": []},
    {"schema_version": 1, "models": [], "tasks": ["t"], "params": "nope"},
    {"schema_version": 1, "models": [], "tasks": [], "dirs": 3},
    {"schema_version": 1, "models": [1, 2], "tasks": []},
    {"schema_version": 1, "models": [], "tasks": [],
     "params": {"seeds": ["x"]}},
    {"schema_version": 1, "models": [], "tasks": [],
     "params": {"peft": "weird"}},
    {"schema_version": 1, "models": [], "tasks": [],
     "params": {"config_variant": "bogus"}},
    {"schema_version": 1, "models": [], "tasks": [],
     "params": {"num_train_epochs": 0}},
    {"schema_version": 1, "models": [], "tasks": [],
     "params": {"curve_fractions": [1.5]}},
    {"schema_version": 1, "models": [], "tasks": [],
     "params": {"batch_size": 0}},
    {"schema_version": 1, "models": [], "tasks": [],
     "dirs": {"output_root": ""}},
])
def test_load_state_shape_drift_returns_default(monkeypatch, tmp_path, doc):
    """Any structural deviation — wrong types, out-of-vocabulary
    enums, out-of-bounds numerics, empty output_root — yields the
    WHOLE default spec, never a partially-misread one."""
    state = pin_state_dir(monkeypatch, tmp_path)
    state.mkdir(parents=True, exist_ok=True)
    (state / "run_config.json").write_text(json.dumps(doc), encoding="utf-8")
    assert run_config.load_state() == run_config.RunSpec(models=(), tasks=())


# =====================================================================
# Legacy migration (261014-c2l — the D-19 retirement)
# =====================================================================


def _write_state_doc(monkeypatch, tmp_path, doc):
    """Write a hand-composed persisted document, pin the state root."""
    state = pin_state_dir(monkeypatch, tmp_path)
    state.mkdir(parents=True, exist_ok=True)
    (state / "run_config.json").write_text(
        json.dumps(doc, indent=4, sort_keys=True), encoding="utf-8")
    return state


_PRE_CHANGE_DOC = {
    "schema_version": 1,
    "models": ["model-a"],
    "tasks": ["task-1"],
    "params": {
        "seeds": [42, 43, 44],
        "peft": "none",
        "config_variant": "none",
        "curve_fractions": [],
        "subset_file": None,
        "num_train_epochs": None,
        "effective_batch_size": None,
    },
    "dirs": {
        "output_root": "./finetuned",
        "dataset_root": "./datasets",
        "cache_dir": None,
    },
}


def test_legacy_dataset_root_default_loads_as_unset(monkeypatch, tmp_path):
    """A pre-change persisted state file whose dirs.dataset_root is
    exactly the retired D-19 display-only default './datasets' loads as
    a spec with dataset_root None and composes NO --dataset_root
    element — byte-identical launches from pre-change state files (the
    value was never threaded; threading it would double the
    'datasets/' path segment)."""
    _write_state_doc(monkeypatch, tmp_path, _PRE_CHANGE_DOC)
    spec = run_config.load_state()
    assert spec.dataset_root is None
    assert spec.model_root is None, (
        "a pre-change file carries no model_root key — the tolerant "
        "read maps the absence to unset (backward compatible, no "
        "schema_version bump)"
    )


def test_pre_change_doc_batch_size_absent_loads_none(
        monkeypatch, tmp_path):
    """261023-abu: a pre-change persisted state file (no batch_size
    key) loads with batch_size None — byte-identical launches, zero
    --batch_size argv elements, no schema_version bump (the
    workers/gpus absent-key precedent)."""
    _write_state_doc(monkeypatch, tmp_path, _PRE_CHANGE_DOC)
    spec = run_config.load_state()
    assert spec.batch_size is None
    assert "--batch_size" not in run_config.compose_dispatch_argv(
        run_config.RunSpec(
            models=spec.models, tasks=spec.tasks,
            batch_size=spec.batch_size))
    argv = run_config.compose_argv(spec)
    assert "--dataset_root" not in argv
    assert "--model_root" not in argv


def test_legacy_custom_dataset_root_loads_through_live(monkeypatch, tmp_path):
    """A persisted CUSTOM dataset_root value (anything other than the
    retired literal) loads through and composes the ABSOLUTE flag — the
    feature going live (261014-c2l)."""
    doc = {
        **_PRE_CHANGE_DOC,
        "dirs": {
            "output_root": "./finetuned",
            "dataset_root": "/mnt/storage",
            "cache_dir": None,
        },
    }
    _write_state_doc(monkeypatch, tmp_path, doc)
    spec = run_config.load_state()
    assert spec.dataset_root == "/mnt/storage"
    argv = run_config.compose_argv(spec)
    assert flag_value(argv, "--dataset_root") == "/mnt/storage"


# =====================================================================
# Lane 1 — resolve_dirs (Task 1)
# =====================================================================


def test_resolve_dirs_defaults_repo_relative_display_absolute_argv():
    """D-14: the default output root stays './finetuned' for DISPLAY
    but resolves ABSOLUTE against REPO_ROOT for argv; both storage
    roots default UNSET -> None (the D-19 display-only dataset-root
    default retired, 261014-c2l); cache absent -> None."""
    spec = run_config.RunSpec(models=("m",), tasks=("t",))
    plan = run_config.resolve_dirs(spec)
    assert plan.output_root == "./finetuned"
    assert plan.output_root_abs == str((REPO_ROOT / "finetuned").resolve())
    assert plan.dataset_root is None
    assert plan.dataset_root_abs is None
    assert plan.model_root is None
    assert plan.model_root_abs is None
    assert plan.cache_dir_abs is None
    assert plan.log_dir is None, (
        "the log dir defaults UNSET for display (261014-f4w)"
    )
    assert plan.log_dir_abs is None


def test_resolve_dirs_explicit_overrides_resolve_absolute():
    """An explicit override always threads ABSOLUTE (D-14) — a relative
    override resolves against REPO_ROOT, an absolute one passes
    through unchanged (both storage roots + the log dir included,
    261014-c2l + 261014-f4w)."""
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",),
        output_root="./sweeps/run-b",
        dataset_root="/data/datasets",
        model_root="./m-root",
        cache_dir="./hf-cache",
        log_dir="./run-logs",
    )
    plan = run_config.resolve_dirs(spec)
    assert plan.output_root == "./sweeps/run-b"
    assert plan.output_root_abs == str((REPO_ROOT / "sweeps" / "run-b").resolve())
    assert plan.dataset_root == "/data/datasets"
    assert plan.dataset_root_abs == "/data/datasets"
    assert plan.model_root == "./m-root"
    assert plan.model_root_abs == str((REPO_ROOT / "m-root").resolve())
    assert plan.cache_dir_abs == str((REPO_ROOT / "hf-cache").resolve())
    assert plan.log_dir == "./run-logs"
    assert plan.log_dir_abs == str((REPO_ROOT / "run-logs").resolve())


def test_resolve_dirs_log_dir_absolute_passes_through():
    """The log-dir display/argv twins mirror dataset_root: an absolute
    value passes through unchanged for argv (261014-f4w)."""
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",), log_dir="/mnt/logs")
    plan = run_config.resolve_dirs(spec)
    assert plan.log_dir == "/mnt/logs"
    assert plan.log_dir_abs == "/mnt/logs"


def test_resolve_dirs_absent_log_dir_is_none():
    spec = run_config.RunSpec(models=("m",), tasks=("t",), log_dir=None)
    plan = run_config.resolve_dirs(spec)
    assert plan.log_dir is None
    assert plan.log_dir_abs is None


def test_resolve_dirs_absent_dataset_root_is_none():
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",), dataset_root=None,
    )
    plan = run_config.resolve_dirs(spec)
    assert plan.dataset_root is None
    assert plan.dataset_root_abs is None


def test_resolve_dirs_nonexistent_output_root_is_advisory_only():
    """Resolution NEVER fails on a nonexistent output root — the sweep
    driver mkdirs it (advisory-only, D-14)."""
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",), output_root="./does/not/exist/yet",
    )
    plan = run_config.resolve_dirs(spec)
    assert plan.output_root_abs == str(
        (REPO_ROOT / "does" / "not" / "exist" / "yet").resolve())


# =====================================================================
# Lane 2 — PROBE_INELIGIBLE read-source extraction (Task 2)
# =====================================================================


FIXTURE_SOURCE = '''"""fake pipeline module for the extractor lane."""
import torch  # the reason this is read as text, never imported

PROBE_INELIGIBLE = [
    "model-a",   # a dedicated loader
    "model-b",   # another one
    "SPACE",     # case-sensitive twin
]

OTHER_LIST = ["unrelated", "names"]
'''


def test_load_probe_ineligible_extracts_from_fixture_text():
    """The extractor regex-scans the literal inside ANY source text and
    string-literal-scans inside the brackets — the read-source pattern
    (run_finetune imports torch at module top; import is impossible)."""
    names = run_config.load_probe_ineligible(FIXTURE_SOURCE)
    assert names == frozenset({"model-a", "model-b", "SPACE"})


def test_load_probe_ineligible_raises_without_literal():
    with pytest.raises(ValueError):
        run_config.load_probe_ineligible("OTHER_LIST = [1, 2]\nx = 1\n")


def test_probe_ineligible_real_file_pinned_to_nine_names():
    """Parity tripwire (T-11-02-04 / Pitfall 7): the extraction over
    the REAL pipeline source equals the frozen 9-name literal — both
    space spellings, evo2/megaDNA, gpn-brassicales, Omni-DNA-700M.
    The names are NEVER duplicated in the service or strings.py; this
    pin is the single drift alarm (the UI-SPEC's stale '7 names' claim
    is corrected by this literal)."""
    names = run_config.probe_ineligible()
    assert names == PROBE_INELIGIBLE_NAMES
    assert len(names) == 9
    for anchor in ("SPACE", "space", "evo2_1b_base", "megaDNA_updated",
                   "gpn-brassicales", "Omni-DNA-700M"):
        assert anchor in names


@pytest.mark.parametrize("model", sorted(PROBE_INELIGIBLE_NAMES))
def test_validate_composition_probe_refuses_every_real_frozen_name(model):
    """Each of the REAL 9 frozen names, under variant=probe, yields its
    own probe_ineligible problem (the full-matrix sweep over the real
    list, not a fixture subset)."""
    spec = run_config.RunSpec(
        models=(model,), tasks=("GUE__emp_H3",), config_variant="probe",
    )
    problems = run_config.validate_composition(spec, run_config.probe_ineligible())
    assert problems == (("probe_ineligible", model),)


# =====================================================================
# Lane 2 — same-source preview (Task 2)
# =====================================================================


def test_preview_real_registry_count_parity():
    """2 models x 3 tasks x 3 seeds = 18 cells; the cells ARE the
    imported enumerate_matrix output VERBATIM (D-05 same-source — the
    test re-derives them through run_sweep directly)."""
    spec = run_config.RunSpec(
        models=PREVIEW_MODELS, tasks=PREVIEW_TASKS, seeds=(42, 43, 44),
    )
    result = run_config.preview(spec)
    assert result.models_count == 2
    assert result.tasks_count == 3
    assert result.seeds_count == 3
    assert result.fractions_count is None
    assert result.cells_count == 18
    assert result.problems == ()
    assert all(len(cell) == 3 for cell in result.cells)
    expected = run_sweep.enumerate_matrix(
        list(PREVIEW_MODELS), list(PREVIEW_TASKS), [42, 43, 44],
        REAL_REGISTRY_DIR,
    )
    assert list(result.cells) == expected


def test_preview_curve_expansion_four_tuples():
    """Curve fractions expand each cell to (model, task, seed,
    fraction) 4-tuples — the layout contract lives in the imported
    enumeration, never re-implemented here."""
    spec = run_config.RunSpec(
        models=("plant-dnabert-6mer",), tasks=("GUE__emp_H3",),
        seeds=(42,), curve_fractions=(0.25, 0.5),
    )
    result = run_config.preview(spec)
    assert result.fractions_count == 2
    assert result.cells_count == 2
    assert result.cells == (
        ("plant-dnabert-6mer", "GUE__emp_H3", 42, 0.25),
        ("plant-dnabert-6mer", "GUE__emp_H3", 42, 0.5),
    )


def test_preview_peft_alias_names_in_cells():
    """peft=lora enumerates under the alias name — the 11-01/06-02
    aliasing seen through the same-source preview."""
    spec = run_config.RunSpec(
        models=("plant-dnabert-6mer",), tasks=("GUE__emp_H3",),
        seeds=(42,), peft="lora",
    )
    result = run_config.preview(spec)
    assert result.cells == (("plant-dnabert-6mer+lora", "GUE__emp_H3", 42),)


def test_preview_variant_alias_names_in_cells():
    """variant=probe aliases {model}+probe; head keeps the BASE name
    for the frozen pair (evo2_1b_base) while aliasing the rest."""
    spec = run_config.RunSpec(
        models=("evo2_1b_base", "plant-dnabert-6mer"),
        tasks=("GUE__emp_H3",), seeds=(42,), config_variant="head",
    )
    result = run_config.preview(spec)
    assert {cell[0] for cell in result.cells} == {
        "evo2_1b_base", "plant-dnabert-6mer+head"}
    probe_spec = run_config.RunSpec(
        models=("plant-dnabert-6mer",), tasks=("GUE__emp_H3",),
        seeds=(42,), config_variant="probe",
    )
    assert run_config.preview(probe_spec).cells == (
        ("plant-dnabert-6mer+probe", "GUE__emp_H3", 42),)


def test_preview_problems_empty_selection():
    spec = run_config.RunSpec(models=(), tasks=PREVIEW_TASKS)
    result = run_config.preview(spec)
    assert result.problems == (("empty_selection", None),)
    assert result.cells == ()
    assert result.cells_count == 0


def test_preview_problems_variant_peft():
    spec = run_config.RunSpec(
        models=PREVIEW_MODELS, tasks=PREVIEW_TASKS,
        peft="ia3", config_variant="curve",
    )
    result = run_config.preview(spec)
    assert result.problems == (("variant_peft", "curve+ia3"),)


def test_preview_problems_probe_ineligible_real_name():
    """A real frozen name under variant=probe: the cells still preview
    (honest about what would run) AND the composition problem is
    carried — preview never hides a launch blocker."""
    spec = run_config.RunSpec(
        models=("evo2_1b_base",), tasks=("GUE__emp_H3",),
        seeds=(42,), config_variant="probe",
    )
    result = run_config.preview(spec)
    assert result.problems == (("probe_ineligible", "evo2_1b_base"),)
    assert result.cells == (("evo2_1b_base+probe", "GUE__emp_H3", 42),)


def test_preview_unknown_names_intersect_to_zero_cells():
    """Unknown filter names intersect to an empty enumeration — the
    preview reports the honest zero (run_sweep's own start-time
    validation stays the loud guard)."""
    spec = run_config.RunSpec(
        models=("no-such-model",), tasks=("GUE__emp_H3",), seeds=(42,),
    )
    result = run_config.preview(spec)
    assert result.cells_count == 0
    assert result.models_count == 0


# =====================================================================
# Lane 2 — official-only key sets (Task 2)
# =====================================================================


def test_official_keys_real_registries():
    """The committed official registries: 59 models, 50 trainable
    tasks, no diagnostic (the 08-03 RegistryCounts(62, 50) precedent —
    committed data, pinned as counts)."""
    official = run_config.official_keys()
    assert official.diagnostic is None
    assert len(official.models) == 59
    assert len(official.tasks) == 50


def test_official_keys_is_overlay_free(monkeypatch, tmp_path):
    """Pitfall 5 behavioral pin: a custom overlay entry NEVER joins the
    official key sets — direct json.load, never registry_loader (the
    overlay merges customs into the enumeration; comparing against the
    merged view would under-gate E2')."""
    custom_dir = tmp_path / "custom"
    custom_dir.mkdir()
    (custom_dir / "custom_models.json").write_text(
        json.dumps({"custom-model-x": {"size (M)": 1}}), encoding="utf-8")
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(custom_dir))
    official = run_config.official_keys()
    assert "custom-model-x" not in official.models
    assert official.diagnostic is None


def test_official_keys_trainable_tasks_only(tmp_path):
    """Official tasks are the TRAINABLE entries (truthy Train) — an
    untrainable entry can never be part of the full matrix, so
    including it would make E2' unreachable."""
    (tmp_path / "models_info.json").write_text(
        json.dumps({"m1": {}, "m2": {}}), encoding="utf-8")
    (tmp_path / "datasets_info.json").write_text(
        json.dumps({
            "t1": {"Train": 1},
            "t2": {"Train": 0},
            "t3": {"Train": 2110},
        }), encoding="utf-8")
    official = run_config.official_keys(tmp_path)
    assert official.diagnostic is None
    assert official.models == frozenset({"m1", "m2"})
    assert official.tasks == frozenset({"t1", "t3"})


def test_official_keys_missing_file_fail_closed(tmp_path):
    """An absent registry file: empty sets + a diagnostic naming the
    path — never a silent empty compare (T-11-02-02)."""
    official = run_config.official_keys(tmp_path)
    assert official.models == frozenset()
    assert official.tasks == frozenset()
    assert official.diagnostic is not None
    assert "models_info.json" in official.diagnostic
    assert "datasets_info.json" in official.diagnostic


def test_official_keys_corrupt_json_fail_closed(tmp_path):
    (tmp_path / "models_info.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "datasets_info.json").write_text("{}", encoding="utf-8")
    official = run_config.official_keys(tmp_path)
    assert official.models == frozenset()
    assert official.tasks == frozenset()
    assert "models_info.json" in official.diagnostic


def test_official_keys_shape_invalid_fail_closed(tmp_path):
    """A JSON list is shape-invalid for a registry (must be a dict of
    entries)."""
    (tmp_path / "models_info.json").write_text("[]", encoding="utf-8")
    (tmp_path / "datasets_info.json").write_text("{}", encoding="utf-8")
    official = run_config.official_keys(tmp_path)
    assert official.models == frozenset()
    assert official.diagnostic is not None


# =====================================================================
# Lane 2 — the E2' verdict (Task 2)
# =====================================================================


def _full_official_spec(official, seeds=(42, 43, 44)):
    return run_config.RunSpec(
        models=tuple(official.models),
        tasks=tuple(official.tasks),
        seeds=seeds,
    )


def test_is_full_e2x_full_official_three_seeds_true():
    official = run_config.official_keys()
    assert run_config.is_full_e2x(_full_official_spec(official), official)


def test_is_full_e2x_missing_one_model_false():
    official = run_config.official_keys()
    models = tuple(sorted(official.models)[:-1])  # drop one
    spec = run_config.RunSpec(models=models, tasks=tuple(official.tasks))
    assert not run_config.is_full_e2x(spec, official)


def test_is_full_e2x_missing_one_task_false():
    official = run_config.official_keys()
    tasks = tuple(sorted(official.tasks)[:-1])
    spec = run_config.RunSpec(models=tuple(official.models), tasks=tasks)
    assert not run_config.is_full_e2x(spec, official)


def test_is_full_e2x_two_seeds_false():
    official = run_config.official_keys()
    spec = _full_official_spec(official, seeds=(42, 43))
    assert not run_config.is_full_e2x(spec, official)


def test_is_full_e2x_custom_only_false():
    official = run_config.official_keys()
    spec = run_config.RunSpec(
        models=("custom-model-x",), tasks=tuple(official.tasks))
    assert not run_config.is_full_e2x(spec, official)


def test_is_full_e2x_superset_escalation_true():
    """O4 resolution: official UNION customs still escalates to the
    typed gate — the run contains the full re-run; under-gating is the
    hazard (supersedes UI-SPEC #9's 'custom => never E2'' reading)."""
    official = run_config.official_keys()
    spec = run_config.RunSpec(
        models=tuple(official.models) + ("custom-model-x",),
        tasks=tuple(official.tasks) + ("custom-task-y",),
    )
    assert run_config.is_full_e2x(spec, official)


def test_is_full_e2x_alias_names_strip_to_base_peft():
    """Selection carrying +lora alias names under peft=lora: the
    verdict compares BASE names (run_sweep.base_model_name strip)."""
    official = run_config.official_keys()
    spec = run_config.RunSpec(
        models=tuple(f"{model}+lora" for model in official.models),
        tasks=tuple(official.tasks),
        peft="lora",
    )
    assert run_config.is_full_e2x(spec, official)


def test_is_full_e2x_alias_names_strip_to_base_variant():
    official = run_config.official_keys()
    spec = run_config.RunSpec(
        models=tuple(f"{model}+probe" for model in official.models),
        tasks=tuple(official.tasks),
        config_variant="probe",
    )
    assert run_config.is_full_e2x(spec, official)


def test_is_full_e2x_diagnostic_never_true():
    """Fail-closed (T-11-02-02): a diagnostic-bearing OfficialKeys
    blocks the gate even over a spec that would otherwise qualify —
    empty official sets must never satisfy the superset predicate by
    vacuity. The caller surfaces the diagnostic as a problem."""
    diagnostic = run_config.OfficialKeys(
        frozenset(), frozenset(), "unreadable or shape-invalid: ...")
    assert not run_config.is_full_e2x(
        run_config.RunSpec(
            models=tuple("m" for _ in range(3)), tasks=("t",)),
        diagnostic)


def test_is_full_e2x_diagnostic_from_missing_registry_never_true(tmp_path):
    """The caller-visible rule end-to-end: a tmp registry dir with a
    missing file yields the diagnostic OfficialKeys, over which a
    full-selection spec never reads True."""
    official = run_config.official_keys(tmp_path)
    assert official.diagnostic is not None
    real = run_config.official_keys()
    spec = _full_official_spec(real)
    assert not run_config.is_full_e2x(spec, official)


# =====================================================================
# Lane 2 — the typed phrase (Task 2)
# =====================================================================


def test_expected_phrase_nested_root_basename():
    assert run_config.expected_phrase("/data/sweeps/run-2026-10") == "run-2026-10"


def test_expected_phrase_trailing_slash_root():
    assert run_config.expected_phrase("/data/sweeps/run-a/") == "run-a"


def test_expected_phrase_relative_default_root():
    assert run_config.expected_phrase("./finetuned") == "finetuned"


def test_phrase_matches_exact_equality():
    assert run_config.phrase_matches("run-a", "/data/sweeps/run-a") is True


@pytest.mark.parametrize("typed", ["run-a ", " run-a", "RUN-A", "run", "run-a/"])
def test_phrase_matches_every_non_exact_variant_fails(typed):
    """Exact string equality — no stripping, no case folding, no
    prefix (D-07: the typed-phrase gate is spawner-refusal-proof
    because nothing normalizes the operator's input)."""
    assert run_config.phrase_matches(typed, "/data/sweeps/run-a") is False


# =====================================================================
# Lane 3 — run_sweep argv composition (Task 3)
# =====================================================================


def test_compose_argv_defaults_exactly_ten_base_elements():
    """A defaults spec composes EXACTLY the 10 base elements — absent
    flags contribute ZERO elements (D-12 absent parity)."""
    spec = run_config.RunSpec(
        models=PREVIEW_MODELS, tasks=("GUE__emp_H3",), seeds=(42, 43, 44),
    )
    argv = run_config.compose_argv(spec)
    assert argv == [
        sys.executable,
        str(REAL_REGISTRY_DIR / "run_sweep.py"),
        "--models", "plant-dnabert-6mer,plant-dnagpt-BPE",
        "--tasks", "GUE__emp_H3",
        "--seeds", "42,43,44",
        "--output-root", str((REPO_ROOT / "finetuned").resolve()),
    ]


@pytest.mark.parametrize("flag", [
    "--peft", "--config-variant", "--curve", "--subset_file",
    "--num_train_epochs", "--effective_batch_size", "--batch_size",
    "--cache_dir",
    "--model_root", "--dataset_root", "--log_dir",
])
def test_compose_argv_absent_flags_contribute_zero_elements(flag):
    spec = run_config.RunSpec(models=("m",), tasks=("t",))
    argv = run_config.compose_argv(spec)
    assert flag not in argv
    assert len(argv) == 10


def test_compose_argv_full_spec_element_for_element():
    """Every optional flag present: the argv pinned ELEMENT-FOR-ELEMENT
    — the [p] modal and the 11-03 launcher consume this argv verbatim,
    so the order is pinned exactly once, here. (The spec carries both
    alias axes only to exercise the order; composition validation —
    not the mechanical composer — refuses the variant x peft combo,
    and run_sweep re-refuses at start.) The storage tail
    (261014-c2l + 261014-f4w) pins --cache_dir, --model_root,
    --dataset_root, --log_dir — the same order run_sweep's build_argv
    pins element-for-element."""
    spec = run_config.RunSpec(
        models=("m1", "m2"), tasks=("t1",), seeds=(42,),
        peft="lora", config_variant="probe",
        curve_fractions=(0.25, 0.5),
        subset_file="./subs/fairness.json",
        num_train_epochs=1, effective_batch_size=16, batch_size=8,
        output_root="./sweeps/run-x",
        cache_dir="./hf-cache",
        model_root="./m-root",
        dataset_root="./d-root",
        log_dir="./run-logs",
    )
    argv = run_config.compose_argv(spec)
    assert argv == [
        sys.executable,
        str(REAL_REGISTRY_DIR / "run_sweep.py"),
        "--models", "m1,m2",
        "--tasks", "t1",
        "--seeds", "42",
        "--output-root", str((REPO_ROOT / "sweeps" / "run-x").resolve()),
        "--peft", "lora",
        "--config-variant", "probe",
        "--curve", "0.25,0.5",
        "--subset_file", str((REPO_ROOT / "subs" / "fairness.json").resolve()),
        "--num_train_epochs", "1",
        "--effective_batch_size", "16",
        "--batch_size", "8",
        "--cache_dir", str((REPO_ROOT / "hf-cache").resolve()),
        "--model_root", str((REPO_ROOT / "m-root").resolve()),
        "--dataset_root", str((REPO_ROOT / "d-root").resolve()),
        "--log_dir", str((REPO_ROOT / "run-logs").resolve()),
    ]


def test_compose_argv_threads_both_storage_roots_when_set():
    """261014-c2l (the D-19 retirement guard): a spec with BOTH storage
    roots set composes BOTH flags — the dataset root is live, joined by
    the model root, model-before-dataset in the pinned tail order."""
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",),
        model_root="/mnt/storage", dataset_root="/mnt/storage",
    )
    argv = run_config.compose_argv(spec)
    assert flag_value(argv, "--model_root") == "/mnt/storage"
    assert flag_value(argv, "--dataset_root") == "/mnt/storage"
    assert argv.index("--model_root") < argv.index("--dataset_root"), (
        "--model_root must precede --dataset_root (the pinned tail "
        "order, matching run_sweep.build_argv)"
    )


def test_compose_argv_is_a_list_of_str():
    """LIST argv, every element a str (the phase-10/D-06 discipline —
    values never become flags through a shell)."""
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",), peft="ia3",
        subset_file="/abs/subset.json", num_train_epochs=2,
    )
    argv = run_config.compose_argv(spec)
    assert isinstance(argv, list)
    assert all(isinstance(element, str) for element in argv)
    assert flag_value(argv, "--peft") == "ia3"
    assert flag_value(argv, "--subset_file") == "/abs/subset.json"
    assert flag_value(argv, "--num_train_epochs") == "2"


def test_compose_argv_absolute_resolution_against_repo_root():
    """Relative values in, absolute out — output_root/subset/cache and
    both storage roots resolve against REPO_ROOT (D-14: the
    subprocess's own CWD resolution can never diverge)."""
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",),
        output_root="./finetuned",
        subset_file="./fairness.json",
        cache_dir="./cache",
        model_root="./m-root",
        dataset_root="./d-root",
    )
    argv = run_config.compose_argv(spec)
    assert flag_value(argv, "--output-root") == str(
        (REPO_ROOT / "finetuned").resolve())
    assert flag_value(argv, "--subset_file") == str(
        (REPO_ROOT / "fairness.json").resolve())
    assert flag_value(argv, "--cache_dir") == str(
        (REPO_ROOT / "cache").resolve())
    assert flag_value(argv, "--model_root") == str(
        (REPO_ROOT / "m-root").resolve())
    assert flag_value(argv, "--dataset_root") == str(
        (REPO_ROOT / "d-root").resolve())


def test_compose_argv_absolute_overrides_pass_through():
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",),
        output_root="/data/sweeps/run-y",
        subset_file="/data/fairness.json",
        cache_dir="/data/hf-cache",
        model_root="/mnt/models",
        dataset_root="/mnt/datasets",
    )
    argv = run_config.compose_argv(spec)
    assert flag_value(argv, "--output-root") == "/data/sweeps/run-y"
    assert flag_value(argv, "--subset_file") == "/data/fairness.json"
    assert flag_value(argv, "--cache_dir") == "/data/hf-cache"
    assert flag_value(argv, "--model_root") == "/mnt/models"
    assert flag_value(argv, "--dataset_root") == "/mnt/datasets"


def test_compose_argv_empty_models_raises_defensively():
    spec = run_config.RunSpec(models=(), tasks=("t",))
    with pytest.raises(ValueError):
        run_config.compose_argv(spec)


def test_compose_argv_empty_tasks_raises_defensively():
    spec = run_config.RunSpec(models=("m",), tasks=())
    with pytest.raises(ValueError):
        run_config.compose_argv(spec)


def test_compose_from_failures_argv_shape():
    """The [r] re-run path (D-11): --from-failures with the RESOLVED
    failures path, seeds, absolute output root, present-only
    peft/variant pairs, and any extra elements appended last. A
    from-failures enumeration can never be the full matrix by
    construction — never subject to the E2' typed gate."""
    argv = run_config.compose_from_failures_argv(
        "/data/sweeps/run-z/sweep_failures.json",
        seeds=(42, 43, 44),
        output_root="./sweeps/run-z",
        peft="lora",
        config_variant="probe",
        extra=["--dry-run"],
    )
    assert argv == [
        sys.executable,
        str(REAL_REGISTRY_DIR / "run_sweep.py"),
        "--from-failures", "/data/sweeps/run-z/sweep_failures.json",
        "--seeds", "42,43,44",
        "--output-root", str((REPO_ROOT / "sweeps" / "run-z").resolve()),
        "--peft", "lora",
        "--config-variant", "probe",
        "--dry-run",
    ]


def test_compose_from_failures_argv_defaults_eight_elements():
    argv = run_config.compose_from_failures_argv(
        "./sweep_failures.json", seeds=(42,), output_root="/data/r",
    )
    assert argv == [
        sys.executable,
        str(REAL_REGISTRY_DIR / "run_sweep.py"),
        "--from-failures", str((REPO_ROOT / "sweep_failures.json").resolve()),
        "--seeds", "42",
        "--output-root", "/data/r",
    ]
    assert "--peft" not in argv
    assert "--config-variant" not in argv


# =====================================================================
# 16-03 (TUI-02, D16-09) — the dispatch composer + workers/gpus spec
# fields + the three collect-all mirrors. The frozen shard CLI
# (run_sweep_shard.py, either mode) stays the single validation
# authority; these mirrors are cheap pre-filters (Pattern 7).
# =====================================================================


def test_dispatch_spec_defaults_workers_one_gpus_none_no_gpus_element():
    """A spec constructed without workers/gpus carries the defaults
    (workers 1, gpus None — all-detected, resolved at LAUNCH time,
    Pitfall 8) and the composer threads NO --gpus element (D-12
    present-only parity: a defaults spec contributes zero --gpus
    elements) while --workers renders EXPLICITLY (the A2 pin — the
    field carries a live value)."""
    spec = run_config.RunSpec(models=("m",), tasks=("t",))
    assert spec.workers == 1
    assert spec.gpus is None
    argv = run_config.compose_dispatch_argv(spec)
    assert "--gpus" not in argv
    assert flag_value(argv, "--workers") == "1", (
        "--workers is ALWAYS explicit (the A2 pin)"
    )
    assert flag_value(argv, "--mode") == "dispatch"


def test_compose_dispatch_argv_shape_workers_two_gpus_pinned():
    """The dispatch argv pinned ELEMENT-FOR-ELEMENT over the frozen
    shard CLI surface: --mode dispatch, --workers ALWAYS explicit,
    --gpus present-only when typed, --models, the ABSOLUTE
    --output-root, then the passthrough --tasks/--seeds and the SAME
    pinned present-only sweep-flag tail compose_argv threads."""
    spec = run_config.RunSpec(
        models=("m1", "m2"), tasks=("t1",), seeds=(42, 43),
        workers=2, gpus=("0", "1"),
        output_root="./sweeps/dispatch-x",
        peft="lora", config_variant="probe",
        curve_fractions=(0.25, 0.5),
        subset_file="./subs/fairness.json",
        num_train_epochs=1, effective_batch_size=16, batch_size=8,
        cache_dir="./hf-cache", model_root="./m-root",
        dataset_root="./d-root", log_dir="./run-logs",
    )
    argv = run_config.compose_dispatch_argv(spec)
    assert argv == [
        sys.executable,
        str(REAL_REGISTRY_DIR / "run_sweep_shard.py"),
        "--mode", "dispatch",
        "--workers", "2",
        "--gpus", "0,1",
        "--models", "m1,m2",
        "--output-root", str((REPO_ROOT / "sweeps" / "dispatch-x").resolve()),
        "--tasks", "t1",
        "--seeds", "42,43",
        "--peft", "lora",
        "--config-variant", "probe",
        "--curve", "0.25,0.5",
        "--subset_file", str((REPO_ROOT / "subs" / "fairness.json").resolve()),
        "--num_train_epochs", "1",
        "--effective_batch_size", "16",
        "--batch_size", "8",
        "--cache_dir", str((REPO_ROOT / "hf-cache").resolve()),
        "--model_root", str((REPO_ROOT / "m-root").resolve()),
        "--dataset_root", str((REPO_ROOT / "d-root").resolve()),
        "--log_dir", str((REPO_ROOT / "run-logs").resolve()),
    ]


def test_compose_dispatch_argv_output_root_absolute_against_repo_root():
    """D-14 discipline inherited: a relative output root resolves
    ABSOLUTE against REPO_ROOT in the composed dispatch argv (the same
    basis compose_argv threads — the subprocess's own CWD resolution
    can never diverge)."""
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",), output_root="./finetuned")
    argv = run_config.compose_dispatch_argv(spec)
    assert flag_value(argv, "--output-root") == str(
        (REPO_ROOT / "finetuned").resolve())


def test_compose_dispatch_argv_defaults_fourteen_base_elements():
    """A defaults spec (no optional flags, no gpus) composes EXACTLY
    the 14 base elements — absent sweep flags and an unset gpus
    contribute ZERO elements (the compose_argv D-12 parity over the
    dispatch base)."""
    spec = run_config.RunSpec(models=("m",), tasks=("t",))
    argv = run_config.compose_dispatch_argv(spec)
    assert len(argv) == 14
    assert all(isinstance(element, str) for element in argv)


@pytest.mark.parametrize("raw_workers", ["abc", "0", "-1", "1.5"])
def test_parse_params_workers_invalid_mirrors(raw_workers):
    """workers must parse as an integer >= 1 (the run_sweep_shard
    --workers bound mirrored WITHOUT its sys.exit)."""
    partials, problems = run_config.parse_params(
        {"workers": raw_workers})
    assert (run_config.PROBLEM_WORKERS_INVALID, raw_workers) in problems
    assert "workers" not in partials


@pytest.mark.parametrize("raw_gpus", ["0,x", "uuid-gpu", "1,,0", "-1,0"])
def test_parse_params_gpus_invalid_mirrors(raw_gpus):
    """gpus must be comma-separated non-negative INDICES — deliberately
    NARROWER than the shard CLI's UUID/MIG grammar (the documented
    asymmetry, Pitfall 7: a UUID typed into the TUI is refused by the
    mirror though the CLI would accept it). An EMPTY field is ABSENT
    (the all-detected default), never invalid — the epochs idiom."""
    partials, problems = run_config.parse_params({"gpus": raw_gpus})
    assert (run_config.PROBLEM_GPUS_INVALID, raw_gpus) in problems
    assert "gpus" not in partials


def test_parse_params_workers_exceeds_gpus_mirror():
    """A TYPED GPU list shorter than workers raises
    workers_exceeds_gpus (the CLI's own --gpus arity refusal mirrored
    on the short side only; a longer list stays CLI-authoritative).
    The detail is structured data — (workers, gpu_count) — for the
    16-04 screen copy, never pre-worded text."""
    partials, problems = run_config.parse_params(
        {"workers": "2", "gpus": "0"})
    assert "workers" in partials and partials["workers"] == 2
    assert "gpus" in partials and partials["gpus"] == ("0",)
    assert ((run_config.PROBLEM_WORKERS_EXCEED_GPUS, (2, 1))
            in problems), problems


def test_parse_params_workers_gpus_valid_pair_clean():
    partials, problems = run_config.parse_params(
        {"workers": "2", "gpus": "1,0"})
    assert problems == ()
    assert partials["workers"] == 2
    assert partials["gpus"] == ("0", "1")


def test_parse_params_workers_gpus_absent_mean_defaults():
    """Absent/cleared workers/gpus fields contribute NO partial — the
    RunSpec constructor defaults govern (the seeds/epochs idiom)."""
    partials, problems = run_config.parse_params(
        {"seeds": "42", "workers": "", "gpus": ""})
    assert problems == ()
    assert "workers" not in partials
    assert "gpus" not in partials


def test_no_workers_vs_models_problem_code_exists():
    """The shard CLI's 'workers exceeds model count' refusal is
    STATIC-mode-only (it sits after the dispatch return in
    run_sweep_shard) — the dispatch path mirrors NO such problem code
    (the plan's Test 5 grep-level pin)."""
    codes = [value for name, value in vars(run_config).items()
             if name.startswith("PROBLEM_")]
    assert codes, "the problem registry is non-vacuous"
    offenders = [code for code in codes
                 if "model" in str(code)]
    assert offenders == [], (
        f"no workers-vs-models mirror may exist: {offenders}"
    )


def test_persistence_round_trip_workers_gpus(monkeypatch, tmp_path):
    """workers/gpus persist and load back identically; gpus None
    NEVER persists as a resolved/guessed list (Pitfall 8 — resolution
    happens at LAUNCH time only)."""
    state = pin_state_dir(monkeypatch, tmp_path)
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",), workers=3, gpus=("0", "1", "2"))
    run_config.save_state(spec)
    assert run_config.load_state() == spec
    doc = json.loads((state / "run_config.json").read_text(encoding="utf-8"))
    assert doc["params"]["workers"] == 3
    assert doc["params"]["gpus"] == ["0", "1", "2"]
    # gpus None persists as None — never a resolved list (Pitfall 8)
    run_config.save_state(run_config.RunSpec(models=("m",), tasks=("t",)))
    doc = json.loads((state / "run_config.json").read_text(encoding="utf-8"))
    assert doc["params"]["gpus"] is None
    assert doc["params"]["workers"] == 1


def test_pre_phase16_state_document_loads_workers_gpus_defaults(
        monkeypatch, tmp_path):
    """The backward-compat edge: a pre-Phase-16 state document (no
    workers/gpus keys anywhere) loads through the absent-key path as
    workers 1 / gpus None — byte-identical launches from old files."""
    state = pin_state_dir(monkeypatch, tmp_path)
    state.mkdir(parents=True)
    doc = {
        "schema_version": 1,
        "models": ["m"],
        "tasks": ["t"],
        "params": {
            "seeds": [42],            "peft": "none",
            "config_variant": "none",
            "curve_fractions": [],
            "subset_file": None,
            "num_train_epochs": None,
            "effective_batch_size": None,
        },
        "dirs": {
            "output_root": "./finetuned",
            "dataset_root": None,
            "model_root": None,
            "log_dir": None,
            "cache_dir": None,
        },
    }
    (state / "run_config.json").write_text(
        json.dumps(doc), encoding="utf-8")
    loaded = run_config.load_state()
    assert loaded.workers == 1
    assert loaded.gpus is None


def test_runspec_gpus_normalizes_sorted_deduped():
    """gpus normalizes to a sorted deduped tuple in __post_init__ (the
    house discipline — deterministic argv and persistence)."""
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",), gpus=("1", "0", "1"))
    assert spec.gpus == ("0", "1")


# =====================================================================
# 261014-f4w — file-default seeding + the atomic save seam + the
# storage overview (Task 2)
# =====================================================================


def pin_config_dir(monkeypatch, tmp_path, payload=None):
    """Point DNALLMMARK_TUI_CONFIG_DIR at a tmp root and optionally
    write a directories.json there (overrides the root conftest's
    autouse empty-dir pin — the test-body setenv wins)."""
    import directories_config  # top-level module (pipeline/ sys.path root)

    config_root = tmp_path / "f4w-config"
    config_root.mkdir()
    monkeypatch.setenv(settings.CONFIG_DIR_ENV, str(config_root))
    if payload is not None:
        (config_root / directories_config.DIRECTORIES_FILE_NAME).write_text(
            json.dumps(payload), encoding="utf-8")
    return config_root


def test_seed_directory_defaults_fills_none_fields():
    """The pure seeding function: each None dir field fills from the
    file dict; output_root fills ONLY at the DEFAULT literal (the
    str-typed field's one seedable signal — the conflation is the
    documented mount-time PREFILL semantics); an empty dict returns
    the spec unchanged."""
    spec = run_config.RunSpec(models=("m",), tasks=("t",))
    seeded = run_config.seed_directory_defaults(spec, {
        "model_root": "/mnt/models",
        "dataset_root": "/mnt/datasets",
        "log_dir": "/mnt/logs",
        "cache_dir": "/mnt/cache",
    })
    assert seeded.model_root == "/mnt/models"
    assert seeded.dataset_root == "/mnt/datasets"
    assert seeded.log_dir == "/mnt/logs"
    assert seeded.cache_dir == "/mnt/cache"
    assert seeded.output_root == "./finetuned", (
        "no output_root key in the dict — the spec value stands"
    )


def test_seed_directory_defaults_output_root_only_at_default_literal():
    """A CUSTOM persisted output_root survives seeding (session state
    overrides); the DEFAULT literal is the only seedable value."""
    custom = run_config.RunSpec(
        models=("m",), tasks=("t",), output_root="./sweeps/custom")
    seeded = run_config.seed_directory_defaults(
        custom, {"output_root": "/mnt/out"})
    assert seeded.output_root == "./sweeps/custom"
    default = run_config.RunSpec(models=("m",), tasks=("t",))
    seeded_default = run_config.seed_directory_defaults(
        default, {"output_root": "/mnt/out"})
    assert seeded_default.output_root == "/mnt/out"


def test_seed_directory_defaults_set_fields_never_overwritten():
    """Session state wins: a SET field is never overwritten by the
    file's value (the file seeds DEFAULTS only)."""
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",),
        model_root="/session/models", log_dir="/session/logs")
    seeded = run_config.seed_directory_defaults(spec, {
        "model_root": "/file/models", "log_dir": "/file/logs",
    })
    assert seeded.model_root == "/session/models"
    assert seeded.log_dir == "/session/logs"


def test_seed_directory_defaults_empty_dict_returns_spec_unchanged():
    spec = run_config.RunSpec(models=("m",), tasks=("t",))
    assert run_config.seed_directory_defaults(spec, {}) == spec


def test_load_state_seeds_from_directories_json(monkeypatch, tmp_path):
    """load_state post-processes the loaded spec over the tolerant file
    read: unset dir fields prefill from directories.json under the
    injected config root — the mount-time PREFILL the slot-4 inputs and
    the env kernels consume through the one seam."""
    pin_state_dir(monkeypatch, tmp_path)
    pin_config_dir(monkeypatch, tmp_path, {
        "model_root": "/mnt/models",
        "dataset_root": "/mnt/datasets",
        "log_dir": "/mnt/logs",
    })
    loaded = run_config.load_state()
    assert loaded.model_root == "/mnt/models"
    assert loaded.dataset_root == "/mnt/datasets"
    assert loaded.log_dir == "/mnt/logs"
    assert loaded.cache_dir is None, "no cache_dir key — stays unset"


def test_load_state_set_fields_survive_seeding(monkeypatch, tmp_path):
    """A persisted session value wins over the file's key — the file
    seeds DEFAULTS, session state overrides."""
    pin_state_dir(monkeypatch, tmp_path)
    run_config.save_state(run_config.RunSpec(
        models=("m",), tasks=("t",), model_root="/session/models"))
    pin_config_dir(monkeypatch, tmp_path, {"model_root": "/file/models"})
    loaded = run_config.load_state()
    assert loaded.model_root == "/session/models"


def test_load_state_corrupt_directories_json_leaves_spec_untouched(
        monkeypatch, tmp_path):
    """The tolerant twin: a corrupt directories.json degrades to no
    seeding — the load itself stays byte-identical (display surfaces
    never crash on a bad file; the pipeline consumers stay fail-loud)."""
    pin_state_dir(monkeypatch, tmp_path)
    pin_config_dir(monkeypatch, tmp_path, "{not json")
    loaded = run_config.load_state()
    assert loaded.model_root is None
    assert loaded.dataset_root is None
    assert loaded.log_dir is None


def test_load_state_no_file_returns_todays_values(monkeypatch, tmp_path):
    """The no-file representative: with no run_config.json and no
    directories.json, load_state returns exactly today's defaults."""
    pin_state_dir(monkeypatch, tmp_path)
    pin_config_dir(monkeypatch, tmp_path)
    assert run_config.load_state() == run_config.RunSpec(
        models=(), tasks=())


def test_save_directory_defaults_writes_five_key_document(
        monkeypatch, tmp_path):
    """The atomic save seam: the complete five-key document (schema
    envelope 1, every DIRECTORY_KEY present, RESOLVED ABSOLUTE values,
    empty string for unset) lands under the injected config root; the
    written file reads back through the STRICT loader with exactly the
    set values."""
    import directories_config

    config_root = pin_config_dir(monkeypatch, tmp_path)
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",),
        model_root="./m-root", log_dir="/abs/logs")
    written = run_config.save_directory_defaults(spec)
    assert written == config_root / directories_config.DIRECTORIES_FILE_NAME
    doc = json.loads(written.read_text(encoding="utf-8"))
    assert doc["schema_version"] == 1
    assert set(doc) == {
        "schema_version", *directories_config.DIRECTORY_KEYS}
    assert doc["model_root"] == str((REPO_ROOT / "m-root").resolve())
    assert doc["log_dir"] == "/abs/logs", (
        "an absolute value threads through as its resolved self"
    )
    assert doc["dataset_root"] == "", (
        "an unset dir persists as the empty string (the loader's "
        "empty-means-absent policy)"
    )
    assert doc["output_root"] == "", (
        "the DEFAULT output_root literal is the unset signal (the "
        "str-typed field's documented conflation) — an all-default "
        "output root saves as empty"
    )
    assert directories_config.load_directories() == {
        "model_root": str((REPO_ROOT / "m-root").resolve()),
        "log_dir": "/abs/logs",
    }, "the written file reads back through the strict loader"


def test_save_directory_defaults_all_empty_loads_back_as_defaults(
        monkeypatch, tmp_path):
    """The divergence guard made visible: an all-empty save (every dir
    unset, output_root at its default literal) loads back as {} —
    equivalent to defaults, so the restore path is 'clear the inputs
    and save'."""
    import directories_config

    pin_config_dir(monkeypatch, tmp_path)
    written = run_config.save_directory_defaults(
        run_config.RunSpec(models=(), tasks=()))
    assert directories_config.load_directories() == {}
    doc = json.loads(written.read_text(encoding="utf-8"))
    for key in directories_config.DIRECTORY_KEYS:
        assert doc[key] == "", (
            f"{key} must persist empty — five empty strings load back "
            "as the absent-everywhere defaults"
        )


def test_save_directory_defaults_custom_output_root_persists(
        monkeypatch, tmp_path):
    """A CUSTOM output_root (anything other than the default literal)
    persists as its resolved absolute form — the slot-4 save captures
    a real override."""
    import directories_config

    pin_config_dir(monkeypatch, tmp_path)
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",), output_root="./sweeps/custom")
    written = run_config.save_directory_defaults(spec)
    doc = json.loads(written.read_text(encoding="utf-8"))
    assert doc["output_root"] == str(
        (REPO_ROOT / "sweeps" / "custom").resolve())
    assert directories_config.load_directories()["output_root"] == str(
        (REPO_ROOT / "sweeps" / "custom").resolve())


def test_save_directory_defaults_explicit_path_round_trip(
        monkeypatch, tmp_path):
    """The explicit-path seam: the save honors a caller-provided path
    (tests, future exporters) and still writes the same document."""
    import directories_config

    pin_config_dir(monkeypatch, tmp_path)
    target = tmp_path / "elsewhere" / "directories.json"
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",), dataset_root="/mnt/datasets")
    written = run_config.save_directory_defaults(spec, config_path=target)
    assert written == target
    assert directories_config.load_directories(target) == {
        "dataset_root": "/mnt/datasets",
    }, "the default output_root literal persists empty — only real "
    "overrides survive the read-back"


def test_save_directory_defaults_agrees_with_directories_config_path(
        monkeypatch, tmp_path):
    """The D-10 same-root pin from the write side: the returned path
    equals directories_config.config_path() under the injected env —
    the TUI write seam and the pipeline read seam resolve ONE file."""
    import directories_config

    pin_config_dir(monkeypatch, tmp_path)
    written = run_config.save_directory_defaults(
        run_config.RunSpec(models=(), tasks=()))
    assert written == directories_config.config_path()


def test_storage_overview_full_spec_rows(monkeypatch, tmp_path):
    """storage_overview: five frozen rows in DIRECTORY_KEYS order over
    the seed-applied load_state — a fully-set spec carries the spec's
    absolute paths with real exists flags over tmp dirs."""
    pin_state_dir(monkeypatch, tmp_path)
    pin_config_dir(monkeypatch, tmp_path)
    existing = tmp_path / "model-store"
    existing.mkdir()
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",),
        model_root=str(existing),
        dataset_root=str(tmp_path / "dataset-store"),
        log_dir=str(tmp_path / "run-logs"),
        cache_dir=str(tmp_path / "hf-cache"),
        output_root="./sweeps/f4w",
    )
    rows = run_config.storage_overview(spec)
    import directories_config

    assert [row.key for row in rows] == list(
        directories_config.DIRECTORY_KEYS)
    by_key = {row.key: row for row in rows}
    assert by_key["model_root"].path == str(existing)
    assert by_key["model_root"].exists is True
    assert by_key["dataset_root"].path == str(tmp_path / "dataset-store")
    assert by_key["dataset_root"].exists is False
    assert by_key["log_dir"].path == str(tmp_path / "run-logs")
    assert by_key["log_dir"].exists is False
    assert by_key["cache_dir"].path == str(tmp_path / "hf-cache")
    assert by_key["cache_dir"].exists is False
    assert by_key["output_root"].path == str(
        (REPO_ROOT / "sweeps" / "f4w").resolve())
    # 261019-v3g (WINDOWS #33) new-field extensions — zero existing
    # assertions above touched: the cache row is on_demand by KEY (the
    # HF cache is lazily created at first use) and, being ABSENT here,
    # is never writability-probed; every non-cache row — even one that
    # EXISTS (model_root) — carries on_demand False / writable None.
    assert by_key["cache_dir"].on_demand is True
    assert by_key["cache_dir"].writable is None
    assert by_key["model_root"].on_demand is False
    assert by_key["model_root"].writable is None
    for key in ("dataset_root", "log_dir", "output_root"):
        assert by_key[key].on_demand is False, key
        assert by_key[key].writable is None, key


def test_storage_overview_defaults_mirror_real_consumers(
        monkeypatch, tmp_path):
    """With the defaults spec (and no file), the unset display defaults
    mirror the REAL consumers: model/dataset roots -> the committed
    pipeline dir, output_root -> the resolved ./finetuned, log_dir ->
    pipeline/logs, cache -> REPO_ROOT/cache (the run_finetune module-top
    ../../cache default)."""
    pin_state_dir(monkeypatch, tmp_path)
    pin_config_dir(monkeypatch, tmp_path)
    # 2026-10-19 hermeticity fix (maintainer "fix error" ruling): the
    # fresh-checkout premise (default log/cache dirs ABSENT) must not
    # depend on THIS machine's run artifacts (pipeline/logs exists on
    # any dev box that ever ran the pipeline — the nightly
    # environmental failure). Re-point the frozen default table at the
    # tmp root: both truths survive machine-independent — the paths
    # still MIRROR the very constants the service reads (the patched
    # dict IS the service's source), and absent-by-default still pins
    # the honest-glyph derivation.
    for key, rel in (("model_root", "pipeline"),
                     ("dataset_root", "pipeline"),
                     ("log_dir", "pipeline/logs"),
                     ("cache_dir", "cache")):
        monkeypatch.setitem(run_config._STORAGE_DEFAULTS, key,
                            str(tmp_path / rel))
    rows = run_config.storage_overview()
    by_key = {row.key: row for row in rows}
    assert by_key["model_root"].path == str(tmp_path / "pipeline")
    assert by_key["dataset_root"].path == str(tmp_path / "pipeline")
    assert by_key["output_root"].path == str(
        (REPO_ROOT / "finetuned").resolve())
    assert by_key["log_dir"].path == str(tmp_path / "pipeline" / "logs")
    assert by_key["cache_dir"].path == str(tmp_path / "cache")
    assert by_key["log_dir"].exists is False, (
        "the hermetic default log dir is absent (fresh-checkout "
        "truth, machine-independent) — the honest glyph derivation"
    )
    # 261019-v3g (WINDOWS #33) new-field extensions, appended AFTER the
    # assertions above (this test's on-box environmental failure stays
    # byte-identical): the default cache row (REPO_ROOT/cache — absent
    # on a fresh checkout) is on_demand by KEY, so it renders the
    # neutral on-demand state, never the missing-root ✗; the four
    # non-cache rows never claim on-demand.
    assert by_key["cache_dir"].exists is False
    assert by_key["cache_dir"].on_demand is True
    assert by_key["cache_dir"].writable is None
    for key in ("model_root", "dataset_root", "output_root", "log_dir"):
        assert by_key[key].on_demand is False, key


def test_storage_overview_seeded_over_load_state(monkeypatch, tmp_path):
    """storage_overview() with no explicit spec derives from the
    seed-applied load_state() — a directories.json value appears in the
    rows even with no persisted run_config.json (one seam)."""
    pin_state_dir(monkeypatch, tmp_path)
    file_root = tmp_path / "file-models"
    file_root.mkdir()
    pin_config_dir(monkeypatch, tmp_path, {
        "model_root": str(file_root)})
    rows = run_config.storage_overview()
    by_key = {row.key: row for row in rows}
    assert by_key["model_root"].path == str(file_root)
    assert by_key["model_root"].exists is True


def test_storage_overview_present_cache_writability_probe(
        monkeypatch, tmp_path):
    """261019-v3g (WINDOWS #33): a PRESENT cache row carries the
    writability probe answer — a real writable tmp cache dir yields
    writable True, a monkeypatched probe returning False yields
    writable False (the DETERMINISTIC unwritable pin: no chmod
    simulation, no uid dependence) — while non-cache rows keep
    writable None even when they exist (the probe is cache-only)."""
    pin_state_dir(monkeypatch, tmp_path)
    pin_config_dir(monkeypatch, tmp_path)
    cache = tmp_path / "hf-cache"
    cache.mkdir()
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",), cache_dir=str(cache))

    rows = run_config.storage_overview(spec)
    by_key = {row.key: row for row in rows}
    assert by_key["cache_dir"].exists is True
    assert by_key["cache_dir"].on_demand is True
    assert by_key["cache_dir"].writable is True, (
        "a real writable tmp cache dir the test itself created"
    )

    monkeypatch.setattr(run_config, "_cache_writable", lambda path: False)
    rows = run_config.storage_overview(spec)
    by_key = {row.key: row for row in rows}
    assert by_key["cache_dir"].writable is False, (
        "the module-level probe seam is the unwritable answer's source"
    )

    # the probe is cache-only: an EXISTING non-cache row (model_root
    # defaults to the committed pipeline dir, which exists) is never
    # probed and never claims on-demand.
    assert by_key["model_root"].exists is True
    assert by_key["model_root"].writable is None
    assert by_key["model_root"].on_demand is False


# =====================================================================
# 261014-f4w — the directory-picker root chain (Task 3's service tier)
# =====================================================================


def test_directory_picker_root_existing_value_wins(tmp_path):
    """An on-disk value roots the tree at itself (the no-hand-typing
    motivation: the picker opens where the operator's value points)."""
    existing = tmp_path / "model-store"
    existing.mkdir()
    assert run_config.directory_picker_root(str(existing)) == existing


def test_directory_picker_root_nonexistent_finds_nearest_ancestor(
        tmp_path):
    """A nonexistent deep path roots the tree at its NEAREST EXISTING
    ancestor (a partially typed path still lands somewhere sensible —
    the nested-tmp fixture exercises the chain up to the
    existing-ancestor step, never the home fallback)."""
    nested = tmp_path / "a" / "b" / "c"
    nested.parent.mkdir(parents=True)  # a/b exists, a/b/c does not
    assert run_config.directory_picker_root(str(nested)) == nested.parent
    deeper = tmp_path / "a" / "b" / "c" / "d" / "e"
    assert run_config.directory_picker_root(str(deeper)) == nested.parent


def test_directory_picker_root_empty_value_is_repo_root():
    """An empty/whitespace value skips straight to REPO_ROOT (the
    default-viewing root for an unset field)."""
    assert run_config.directory_picker_root("") == run_config.REPO_ROOT
    assert run_config.directory_picker_root("   ") == run_config.REPO_ROOT
    assert run_config.directory_picker_root(None) == run_config.REPO_ROOT


# =====================================================================
# 261017-uwr — argv_matrix: the compose_argv inverse (the live-evidence
# matrix recovery; UWR-2 Task 1)
# =====================================================================


def _matrix_projection(models=None, tasks=None, seeds=(42,), peft="none",
                       fractions=None, config_variant="none"):
    """The same-source pair projection the inverse must reproduce
    (enumerate_matrix cells -> the (model, task) set)."""
    cells = run_sweep.enumerate_matrix(
        list(models) if models else None,
        list(tasks) if tasks else None,
        list(seeds),
        REAL_REGISTRY_DIR,
        peft=peft,
        fractions=list(fractions) if fractions else None,
        config_variant=config_variant,
    )
    return frozenset((str(cell[0]), str(cell[1])) for cell in cells)


def test_argv_matrix_round_trips_compose_argv_2x2():
    """The inverse over a committed-registry 2x2 spec: compose_argv ->
    argv_matrix returns EXACTLY the spec's (model, task) pairs (the
    same-source enumeration projected, never a naive cross product)."""
    spec = run_config.RunSpec(
        models=(PREVIEW_MODELS[0], PREVIEW_MODELS[1]),
        tasks=(PREVIEW_TASKS[0], PREVIEW_TASKS[2]),
        seeds=(42, 43), output_root="/tmp/uwr-roundtrip")
    expected = _matrix_projection(
        models=spec.models, tasks=spec.tasks, seeds=spec.seeds)
    assert run_config.argv_matrix(run_config.compose_argv(spec)) == expected
    assert len(expected) == 4  # 2 models x 2 tasks (seeds collapse)


def test_argv_matrix_single_model_spec_with_absent_flag_legs():
    """A defaults spec (no peft/variant/curve flags in argv — D-12
    absent parity) still round-trips: only the base matrix legs."""
    spec = run_config.RunSpec(
        models=(PREVIEW_MODELS[0],), tasks=(PREVIEW_TASKS[1],),
        seeds=(42,), output_root="/tmp/uwr-single")
    argv = run_config.compose_argv(spec)
    assert "--peft" not in argv and "--config-variant" not in argv
    assert run_config.argv_matrix(argv) == _matrix_projection(
        models=spec.models, tasks=spec.tasks)


def test_argv_matrix_peft_lora_round_trips_alias_pairs():
    """A lora spec's matrix carries the ALIAS cell names
    ("model+lora") — the enumeration output, never the bare filter
    names (the cell-dir identity CellRow documents)."""
    spec = run_config.RunSpec(
        models=(PREVIEW_MODELS[0],), tasks=(PREVIEW_TASKS[0],),
        seeds=(42,), peft="lora", output_root="/tmp/uwr-lora")
    matrix = run_config.argv_matrix(run_config.compose_argv(spec))
    assert matrix == _matrix_projection(
        models=spec.models, tasks=spec.tasks, peft="lora")
    assert matrix == frozenset({
        (f"{PREVIEW_MODELS[0]}+lora", PREVIEW_TASKS[0])})


def test_argv_matrix_curve_fractions_round_trip():
    """The --curve comma list parses through the (0, 1] fraction
    grammar and threads the fraction expansion (same-source)."""
    spec = run_config.RunSpec(
        models=(PREVIEW_MODELS[0],), tasks=(PREVIEW_TASKS[0],),
        seeds=(42,), config_variant="curve",
        curve_fractions=(0.25, 0.5), output_root="/tmp/uwr-curve")
    matrix = run_config.argv_matrix(run_config.compose_argv(spec))
    assert matrix == frozenset({
        (f"{PREVIEW_MODELS[0]}+curve", PREVIEW_TASKS[0])})


def test_argv_matrix_absent_models_tasks_mean_full_registry_legs():
    """--models/--tasks ABSENT parse as the None filters — the driver's
    own default semantics (run_sweep.py:336-349): the full-registry
    matrix over the argv's seeds."""
    argv = [
        sys.executable, str(REAL_REGISTRY_DIR / "run_sweep.py"),
        "--seeds", "42", "--output-root", "/tmp/uwr-full"]
    expected = _matrix_projection(seeds=(42,))
    assert run_config.argv_matrix(argv) == expected
    assert len(expected) > 100  # the real 59 x 50 registry shape


def test_argv_matrix_absent_seeds_or_driver_returns_none():
    """--seeds is required by the driver (its absence means the child
    never launched); no run_sweep.py element means the argv is not a
    sweep — both parse as None (live-but-unknown, never a matrix)."""
    no_seeds = [
        sys.executable, str(REAL_REGISTRY_DIR / "run_sweep.py"),
        "--models", PREVIEW_MODELS[0], "--output-root", "/tmp/uwr"]
    assert run_config.argv_matrix(no_seeds) is None
    not_driver = [
        sys.executable, str(REAL_REGISTRY_DIR / "run_finetune.py"),
        "--seeds", "42", "--output-root", "/tmp/uwr"]
    assert run_config.argv_matrix(not_driver) is None


def test_argv_matrix_from_failures_pairs_through_load_failure_pairs(
        tmp_path):
    """A --from-failures argv parses through the driver's OWN
    load_failure_pairs (never re-implemented): the failed pairs
    verbatim for a base re-run."""
    failures = tmp_path / "sweep_failures.json"
    failures.write_text(json.dumps([
        {"model": PREVIEW_MODELS[0], "task": PREVIEW_TASKS[0], "seed": 42},
    ]), encoding="utf-8")
    argv = [
        sys.executable, str(REAL_REGISTRY_DIR / "run_sweep.py"),
        "--from-failures", str(failures),
        "--seeds", "42", "--output-root", "/tmp/uwr-rerun"]
    assert run_config.argv_matrix(argv) == frozenset({
        (PREVIEW_MODELS[0], PREVIEW_TASKS[0])})


def test_argv_matrix_from_failures_unreadable_file_returns_none(
        tmp_path):
    """The sweep_launcher._from_failures_refusal idiom: SystemExit /
    OSError / ValueError are caught, never raised — an unevaluatable
    manifest maps the root to None (live-but-unknown, legacy
    rendering, never a false interrupt)."""
    broken = tmp_path / "not-a-list.json"
    broken.write_text(json.dumps({"not": "a list"}), encoding="utf-8")
    argv = [
        sys.executable, str(REAL_REGISTRY_DIR / "run_sweep.py"),
        "--from-failures", str(broken),
        "--seeds", "42", "--output-root", "/tmp/uwr-broken"]
    assert run_config.argv_matrix(argv) is None

    missing = tmp_path / "absent.json"
    argv_missing = [
        sys.executable, str(REAL_REGISTRY_DIR / "run_sweep.py"),
        "--from-failures", str(missing),
        "--seeds", "42", "--output-root", "/tmp/uwr-missing"]
    assert run_config.argv_matrix(argv_missing) is None


def test_argv_matrix_from_failures_lora_rerun_aliases_the_pairs(
        tmp_path):
    """A --peft lora from-failures re-run re-aliases the pairs through
    the SAME enumerate+filter the driver runs (run_sweep.py:1878-1896)
    — the re-run's cell dirs are {model}+lora, so the live matrix must
    carry the alias identity or its own live cells would read
    interrupted (the false interrupt UWR-2 forbids)."""
    failures = tmp_path / "sweep_failures.json"
    failures.write_text(json.dumps([
        {"model": PREVIEW_MODELS[0], "task": PREVIEW_TASKS[0], "seed": 42},
    ]), encoding="utf-8")
    argv = [
        sys.executable, str(REAL_REGISTRY_DIR / "run_sweep.py"),
        "--from-failures", str(failures),
        "--seeds", "42", "--peft", "lora",
        "--output-root", "/tmp/uwr-lora-rerun"]
    assert run_config.argv_matrix(argv) == frozenset({
        (f"{PREVIEW_MODELS[0]}+lora", PREVIEW_TASKS[0])})


def test_argv_matrix_out_of_vocabulary_peft_variant_return_none():
    """An argv the driver's argparse would have refused (a bogus --peft
    / --config-variant / non-integer --seeds / out-of-bounds --curve)
    parses as None — never a fabricated alias matrix."""
    for bad in (
        ["--peft", "loRA"],
        ["--config-variant", "turbo"],
        ["--seeds", "42,abc"],
        ["--curve", "1.5"],
    ):
        argv = [
            sys.executable, str(REAL_REGISTRY_DIR / "run_sweep.py"),
            "--models", PREVIEW_MODELS[0], "--tasks", PREVIEW_TASKS[0],
            "--output-root", "/tmp/uwr-bad", *bad]
        assert run_config.argv_matrix(argv) is None, bad


def test_argv_plan_returns_pairs_and_seeds():
    """261020-blt — the planned-CELLS reader: the verified 2x2 argv (two
    models x two committed-registry task keys, --seeds 42,43,44 — both
    task keys enumerate for BOTH models; GUE__virus_species_4 does NOT
    enumerate for plant-dnamamba-6mer and would silently shrink the
    plan) parses to EXACTLY the 4 (model, task) pairs AND the seeds
    tuple (the planned-cell union's two legs through ONE parse); an
    argv without --seeds reads None (live-but-unknown); argv_matrix
    over the SAME argvs returns the pairs / None through the blt
    delegation (byte-compatible by construction)."""
    argv = [
        sys.executable, str(REAL_REGISTRY_DIR / "run_sweep.py"),
        "--models", "plant-dnabert-6mer,plant-dnamamba-6mer",
        "--tasks", "GUE__emp_H3,GUE__prom_300_all",
        "--seeds", "42,43,44",
        "--output-root", "/tmp/blt-plan",
    ]
    plan = run_config.argv_plan(argv)
    assert plan == (
        frozenset({
            ("plant-dnabert-6mer", "GUE__emp_H3"),
            ("plant-dnabert-6mer", "GUE__prom_300_all"),
            ("plant-dnamamba-6mer", "GUE__emp_H3"),
            ("plant-dnamamba-6mer", "GUE__prom_300_all"),
        }),
        (42, 43, 44),
    ), "the reader couples the pairs and the seed fan-out in one parse"
    assert run_config.argv_matrix(argv) == plan[0], (
        "argv_matrix projects the SAME parse (the blt delegation)"
    )
    no_seeds = [
        sys.executable, str(REAL_REGISTRY_DIR / "run_sweep.py"),
        "--models", "plant-dnabert-6mer,plant-dnamamba-6mer",
        "--output-root", "/tmp/blt-no-seeds",
    ]
    assert run_config.argv_plan(no_seeds) is None
    assert run_config.argv_matrix(no_seeds) is None
