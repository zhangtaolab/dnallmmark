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
    """The committed official registries: 62 models, 50 trainable
    tasks, no diagnostic (the 08-03 RegistryCounts(62, 50) precedent —
    committed data, pinned as counts)."""
    official = run_config.official_keys()
    assert official.diagnostic is None
    assert len(official.models) == 62
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
    "--num_train_epochs", "--effective_batch_size", "--cache_dir",
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
    and run_sweep re-refuses at start.)"""
    spec = run_config.RunSpec(
        models=("m1", "m2"), tasks=("t1",), seeds=(42,),
        peft="lora", config_variant="probe",
        curve_fractions=(0.25, 0.5),
        subset_file="./subs/fairness.json",
        num_train_epochs=1, effective_batch_size=16,
        output_root="./sweeps/run-x",
        cache_dir="./hf-cache",
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
        "--cache_dir", str((REPO_ROOT / "hf-cache").resolve()),
    ]


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
    """Relative values in, absolute out — output_root/subset/cache all
    resolve against REPO_ROOT (D-14: the subprocess's own CWD
    resolution can never diverge)."""
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",),
        output_root="./finetuned",
        subset_file="./fairness.json",
        cache_dir="./cache",
    )
    argv = run_config.compose_argv(spec)
    assert flag_value(argv, "--output-root") == str(
        (REPO_ROOT / "finetuned").resolve())
    assert flag_value(argv, "--subset_file") == str(
        (REPO_ROOT / "fairness.json").resolve())
    assert flag_value(argv, "--cache_dir") == str(
        (REPO_ROOT / "cache").resolve())


def test_compose_argv_absolute_overrides_pass_through():
    spec = run_config.RunSpec(
        models=("m",), tasks=("t",),
        output_root="/data/sweeps/run-y",
        subset_file="/data/fairness.json",
        cache_dir="/data/hf-cache",
    )
    argv = run_config.compose_argv(spec)
    assert flag_value(argv, "--output-root") == "/data/sweeps/run-y"
    assert flag_value(argv, "--subset_file") == "/data/fairness.json"
    assert flag_value(argv, "--cache_dir") == "/data/hf-cache"


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
