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
import sys
from pathlib import Path

import pytest

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
    """D-05 codified: importing the service (which module-level-imports
    ``run_sweep`` for the pure planning functions) must leave the GPU
    stack absent from ``sys.modules`` — the live-probe assertion."""
    assert "torch" not in sys.modules
    assert "dnallm" not in sys.modules
    assert "transformers" not in sys.modules


def test_runspec_defaults():
    """The defaults spec: seeds 42/43/44, PEFT none, variant none,
    curve off, subset off, no epochs/EBS override, repo-relative dirs
    (D-14), cache absent."""
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
    assert spec.output_root == "./finetuned"
    assert spec.dataset_root == "./datasets"
    assert spec.cache_dir is None


def test_runspec_is_frozen():
    """The download_queue dataclass discipline: machine data, never
    mutated in place."""
    spec = run_config.RunSpec(models=("m",), tasks=("t",))
    with pytest.raises(Exception):
        spec.peft = "lora"  # type: ignore[misc]


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
    })
    assert problems == ()
    assert partials == {
        "seeds": (42, 43),
        "curve_fractions": (0.25, 0.5),
        "num_train_epochs": 3,
        "effective_batch_size": 16,
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


def test_parse_params_empty_values_mean_absent():
    """A cleared optional field (None or whitespace) is OFF — no
    problem, no partial (the constructor defaults govern)."""
    partials, problems = run_config.parse_params({
        "num_train_epochs": "",
        "effective_batch_size": None,
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
    })
    assert problems == (
        ("seeds_invalid", "x"),
        ("curve_invalid", "2"),
        ("epochs_invalid", "0"),
        ("ebs_invalid", "0"),
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
        output_root="/data/sweeps/run-a",
        dataset_root="/data/datasets",
        cache_dir="/data/cache",
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
    assert doc["dirs"]["output_root"] == "/data/sweeps/run-a"


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
# Lane 1 — resolve_dirs (Task 1)
# =====================================================================


def test_resolve_dirs_defaults_repo_relative_display_absolute_argv():
    """D-14: the default output root stays './finetuned' for DISPLAY
    but resolves ABSOLUTE against REPO_ROOT for argv; the dataset root
    likewise; cache absent -> None (never threaded)."""
    spec = run_config.RunSpec(models=("m",), tasks=("t",))
    plan = run_config.resolve_dirs(spec)
    assert plan.output_root == "./finetuned"
    assert plan.output_root_abs == str((REPO_ROOT / "finetuned").resolve())
    assert plan.dataset_root == "./datasets"
    assert plan.dataset_root_abs == str((REPO_ROOT / "datasets").resolve())
    assert plan.cache_dir_abs is None


def test_resolve_dirs_explicit_overrides_resolve_absolute():
    """An explicit override always threads ABSOLUTE (D-14) — a relative
    override resolves against REPO_ROOT, an absolute one passes
    through unchanged."""
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",),
        output_root="./sweeps/run-b",
        dataset_root="/data/datasets",
        cache_dir="./hf-cache",
    )
    plan = run_config.resolve_dirs(spec)
    assert plan.output_root == "./sweeps/run-b"
    assert plan.output_root_abs == str((REPO_ROOT / "sweeps" / "run-b").resolve())
    assert plan.dataset_root == "/data/datasets"
    assert plan.dataset_root_abs == "/data/datasets"
    assert plan.cache_dir_abs == str((REPO_ROOT / "hf-cache").resolve())


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
