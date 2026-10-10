"""
Source-contract tests for ``pipeline/run_finetune.py`` (F1 / REV-01,
F2 / REV-02).

``run_finetune.py`` is read as SOURCE TEXT and never imported: it does
``import torch`` / ``from dnallm import ...`` at module level, which are
unavailable in the CPU-only test environment — an import would fail for
the wrong reason (the same rationale as ``tests/test_known_defects.py``,
which pioneered the read-source-never-import pattern for pipeline
files). The contracts asserted here are textual/structural:

- **refusal-guard placement** — the REFUSED guard (the driver-side half
  of the two-layer EVAL-01 enforcement) must appear BEFORE both the
  ``load_model_and_tokenizer(`` call site and the ``data_dict = {}``
  construction, so a Dev-less dataset can never reach a model load. For
  the model-load site the identifier immediately followed by an open
  paren is matched — distinguishing the call from the module-top import,
  where a comma follows the identifier instead.
- **config purity** — the string ``allow_test_as_eval`` must appear in
  NEITHER finetune YAML: the dnallm suite's EVAL-01 semantics
  (``dnallm/finetune/trainer.py`` L568-605 @ revision 483a35c) make test
  eval strictly opt-in via that key (config default False), so our
  configs leaving it unset is precisely what keeps checkpoint selection
  off the test set — this test pins that the key is never introduced.
- **seed-isolated output layout (G1/REV-02)** — the outdir construction
  must carry a ``seed_{seed}/`` segment with the ``trainer_state.json``
  resume check immediately following it in the same block, making the
  resume marker seed-scoped (seed 43 runs after seed 42's marker exists
  in a sibling dir — resume never skips a different seed).
- **per-model base-config reload (D-11)** — the base
  ``load_config("./finetune_config.yaml")`` assignment must appear
  EXACTLY once, INSIDE the model loop (after the ``models_info.items()``
  iteration header, before the custom-head membership check), with the
  pre-loop load gone: the custom-head override REPLACES ``configs`` with
  the with_head YAML and never restores it, so only a fresh in-loop load
  guarantees the model after ``evo2_1b_base``/``megaDNA_updated`` starts
  with no ``head_config`` residue.
- **grad_accum reset per dataset (D-07 / WR-01)** — the YAML-default
  ``default_grad_accum`` snapshot (taken AFTER the custom-head reload, so
  head models snapshot the with_head YAML's default) must be restored at
  the top of the dataset loop, BEFORE the
  adjustment block reads ``gradient_accumulation_steps`` — a per-task
  grad_accum from dataset A must never persist into dataset B.
- **fp32-only models (CR-01)** — ``models_only_support_fp32`` must match
  the deprecated pipeline's membership and force ``fp16``/``bf16`` off
  before ``DNATrainer`` construction, so the global ``bf16: True`` in
  ``finetune_config.yaml`` never trains those registry models in
  reduced precision.
- **dataset presence guard (WR-02)** — an ``os.path.isdir(dataset_path)``
  skip-guard precedes ``DNADataset.load_local_data`` so an unlocatable
  dataset dir (a documented expected state) logs and continues instead of
  aborting the whole model loop.
- **completion-marker ordering (WR-13)** — in the ``trainer.train()``
  success block, ``final_metrics.json`` is written BEFORE the
  ``trainer_state.json`` resume marker is copied: the marker is the
  completion signal both this script's resume check and
  ``run_sweep.py``'s skip check read, so it must be the FINAL act of a
  successful cell — copying it first opens a kill window (OOM killer /
  SIGKILL / power loss) in which the cell is permanently "done" with no
  metrics and is never retrained.
- **quirk-registry parity (WR-03/WR-04, 04-04)** — the four legacy quirk
  behaviors port with their parity contracts, each comparing the ACTIVE
  source against ``pipeline/dnallmmark_pipeline.py`` read as TEXT (the
  deprecated file stays untouched — read-only behavioral reference per
  F10): (1) ``models_no_char_n`` — the ACGT-alphabet conditional at the
  ``validate_sequences`` call site (list members get the ACGT-only
  charset, all others the N-allowing one); (2)
  ``models_with_limited_length`` — the per-model max_length caps, WIRED
  at the max_length-determination block (the legacy dict was defined but
  never applied — AUD-15 dead config made functional); (3)
  ``model_not_use_safetensors`` — the 11-entry UNION (legacy's
  plant-dnamamba-6mer AND the rewrite's PlantGFM both present); (4) the
  length-tier rounding — ``determine_batch_size`` (the legacy tier table)
  as the initial batch cap composed BEFORE the VRAM estimators, with the
  legacy grad_accum compensation at the adjustment site.
- **registry name drift (LEGACY_NAME_MAP)** — the legacy quirk lists
  predate the D-10 registry unification: ``PlantCAD2-Large-l48-d1536``
  was renamed to ``PlantCAD2-Large`` and ``prokbert-mini-c`` /
  ``prokbert-mini-long`` / ``MutBERT`` were dropped. Parity is asserted
  MODULO this documented map — a blind verbatim legacy copy (dead names
  resurrected, rename missed) FAILS the tests instead of passing.
- **unified eval subset (F7 Q3 / REV-07, 05-03)** — ``--subset_file``
  (JSON task -> integer row-ID list, the audit's
  ``pipeline/eval_subsets.json``) is validated fail-fast against the
  registry keys and per-task test-split row ranges (ALL problems
  collected, ``[Error]`` exit — the ``run_sweep._validate_filters``
  discipline), and an injectable apply seam restricts the TEST split
  via the wrapped Dataset's ``select`` — placed between
  ``DNADataset.load_local_data`` and ``validate_sequences`` so the
  audited IDs are the actually-evaluated rows; train/dev are NEVER
  selected (dev drives checkpoint selection, research A4); an absent
  flag invokes no select anywhere (byte-identical code path).

See also:
    ``script/make_dev_splits.py`` — the remediation the guard names.
    ``tests/test_known_defects.py`` — the read-source-never-import
    rationale's origin.
    ``tests/test_sweep.py`` — the sweep runner whose subprocesses rely
    on this seed-isolated layout contract.
    ``tests/test_registry_unification.py`` — the 62-entry unified
    registry every quirk-list member must resolve against.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_FINETUNE = REPO_ROOT / "pipeline" / "run_finetune.py"
LEGACY_PIPELINE = REPO_ROOT / "pipeline" / "dnallmmark_pipeline.py"
MODELS_INFO = REPO_ROOT / "pipeline" / "models_info.json"
FINETUNE_CONFIGS = [
    REPO_ROOT / "pipeline" / "finetune_config.yaml",
    REPO_ROOT / "pipeline" / "finetune_config_with_head.yaml",
]

# Legacy -> unified-registry name mapping for the quirk lists (04-04).
# Values are the CURRENT registry name forms; None marks a model DROPPED
# at the D-10 unification (it must NOT be ported into any active list).
LEGACY_NAME_MAP = {
    "PlantCAD2-Large-l48-d1536": "PlantCAD2-Large",  # renamed
    "prokbert-mini-c": None,     # dropped — registry has no such model
    "prokbert-mini-long": None,  # dropped
    "MutBERT": None,             # dropped (registry carries MutBERT-Multi)
}


def list_members(src, name):
    """Regex-extract the quoted members of a ``name = [...]`` list."""
    match = re.search(rf"{name} = \[(.*?)\]", src, re.DOTALL)
    assert match is not None, f"no {name} = [...] list found in source"
    return re.findall(r'"([^"]+)"', match.group(1))


def composed_members(src, name):
    """Effective membership of a registry assignment, resolving one level
    of ``<other-list> + [...]`` composition (the form models_no_char_n
    uses in BOTH the active and the legacy source)."""
    match = re.search(rf"{name} = ([^\n=]+?)\s*\+\s*\[(.*?)\]", src, re.DOTALL)
    if match is not None:
        prefix = match.group(1).strip()
        members = re.findall(r'"([^"]+)"', match.group(2))
        return list_members(src, prefix) + members
    return list_members(src, name)


def dict_members(src, name):
    """Regex-extract the ``"key": value`` pairs of a ``name = {...}`` dict."""
    match = re.search(rf"{name} = \{{(.*?)\}}", src, re.DOTALL)
    assert match is not None, f"no {name} = {{...}} dict found in source"
    return dict(re.findall(r'"([^"]+)":\s*(\d+)', match.group(1)))


def apply_legacy_name_map(names):
    """Map legacy names to current registry forms, dropping the None-
    mapped (dropped-at-unification) names — the blind-copy guard."""
    return {
        mapped
        for mapped in (LEGACY_NAME_MAP.get(name, name) for name in names)
        if mapped is not None
    }


def registry_keys():
    """The unified models registry's keys — the name authority (D-10)."""
    return set(json.loads(MODELS_INFO.read_text(encoding="utf-8")))


def statement_index(src, code):
    """Index of ``code`` as a REAL statement (at a line start, so a
    commented-out or string-embedded copy never satisfies the contract),
    or -1 — wiring assertions must not match dead text."""
    match = re.search(rf"^[^\S\n]*{re.escape(code)}", src, re.MULTILINE)
    return match.start() if match else -1


def test_dev_refusal_guard_precedes_data_dict():
    """The REFUSED guard's source index precedes both the
    load_model_and_tokenizer( call site and the data_dict = {} line —
    a Dev-less dataset is refused before any model load."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    guard_idx = src.find("REFUSED:")
    assert guard_idx != -1, (
        "the REFUSED refusal guard is missing from run_finetune.py "
        "(F1/REV-01 part 2)"
    )
    call_idx = src.find("load_model_and_tokenizer(")
    assert call_idx != -1, (
        "no load_model_and_tokenizer( call site found (the identifier "
        "followed by an open paren; the module-top import is followed by "
        "a comma and must not match)"
    )
    data_dict_idx = src.find("data_dict = {}")
    assert data_dict_idx != -1, "no data_dict = {} construction found"
    assert guard_idx < call_idx, (
        "the refusal guard must precede the load_model_and_tokenizer "
        f"call site (guard at {guard_idx}, call at {call_idx}) — a "
        "Dev-less dataset would load a model before being refused"
    )
    assert guard_idx < data_dict_idx, (
        "the refusal guard must precede the data_dict construction "
        f"(guard at {guard_idx}, data_dict at {data_dict_idx})"
    )


def test_configs_never_enable_test_as_eval():
    """Config purity: allow_test_as_eval appears in neither finetune
    YAML — the suite's EVAL-01 opt-in (config default False) must stay
    off so test-set checkpoint selection stays impossible."""
    for config_path in FINETUNE_CONFIGS:
        text = config_path.read_text(encoding="utf-8")
        assert "allow_test_as_eval" not in text, (
            f"{config_path.name} sets allow_test_as_eval — the suite's "
            "EVAL-01 contract keeps test eval opt-in-only precisely so "
            "checkpoint selection never runs against test; remove the "
            "key (the config default False is the enforced state)"
        )


def test_seed_isolated_output_layout():
    """G1/REV-02: the outdir construction carries a seed_ segment and the
    trainer_state.json resume check immediately follows it in the same
    block — the resume marker is seed-scoped, so resume never skips a
    different seed."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    outdir_idx = src.find(
        'f"{save_root}/{model_save_name}/{dataset_name}/seed_{seed}/"'
    )
    assert outdir_idx != -1, (
        "the outdir f-string lacks the seed_ segment — output dirs are "
        "seed-agnostic and the trainer_state.json resume skip would "
        "silently skip a different seed (G1/REV-02)"
    )
    resume_idx = src.find('os.path.exists(outdir + "trainer_state.json")')
    assert resume_idx != -1, "no trainer_state.json resume check found"
    assert resume_idx > outdir_idx, (
        "the trainer_state.json resume check must immediately follow the "
        f"outdir construction in the same block (outdir at {outdir_idx}, "
        f"resume check at {resume_idx}) — a resume check elsewhere would "
        "not be seed-scoped by the outdir's seed component"
    )


def test_base_config_reload_is_per_model():
    """D-11: the base config load appears EXACTLY once, inside the model
    loop (after the models_info.items() header, before the custom-head
    membership check) — every model starts from a freshly loaded base so
    the custom-head override cannot leak head_config residue across
    models; the pre-loop load is gone."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    base_load = 'load_config("./finetune_config.yaml")'
    occurrences = src.count(base_load)
    assert occurrences == 1, (
        f"the base config load must appear EXACTLY once (found "
        f"{occurrences}) — exactly one per-model reload inside the model "
        "loop, with the pre-loop load removed (D-11)"
    )
    load_idx = src.find(base_load)
    loop_idx = src.find("models_info.items():")
    assert loop_idx != -1, "no models_info.items() model-loop header found"
    head_check_idx = src.find(
        'model_name in ["evo2_1b_base", "megaDNA_updated"]'
    )
    assert head_check_idx != -1, "no custom-head membership check found"
    assert loop_idx < load_idx, (
        "the base config load must sit INSIDE the model loop (loop header "
        f"at {loop_idx}, load at {load_idx}) — a pre-loop load is the "
        "D-11 leak (the custom-head override replaces configs without "
        "restoring it)"
    )
    assert load_idx < head_check_idx, (
        "the base config load must precede the custom-head membership "
        f"check (load at {load_idx}, membership check at {head_check_idx}) "
        "so the with_head override applies on top of a fresh base for "
        "head models only"
    )


def test_grad_accum_reset_per_dataset():
    """D-07: default_grad_accum is snapshotted AFTER the custom-head config
    reload (WR-01: evo2_1b_base / megaDNA_updated snapshot the with_head
    YAML's default, not the base config's) and restored inside the dataset
    loop BEFORE the adjustment block reads gradient_accumulation_steps — a
    per-task grad_accum from dataset A never persists into dataset B."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    snapshot_idx = src.find("default_grad_accum = configs")
    assert snapshot_idx != -1, (
        "no default_grad_accum snapshot after the per-model config reloads "
        "(D-07) — the per-dataset reset needs the YAML default captured "
        "before any dataset can mutate it"
    )
    with_head_idx = src.find(
        'load_config("./finetune_config_with_head.yaml")'
    )
    assert with_head_idx != -1, "no custom-head config reload found"
    assert with_head_idx < snapshot_idx, (
        "the snapshot must be taken AFTER the custom-head reload "
        f"(with_head reload at {with_head_idx}, snapshot at {snapshot_idx}) "
        "— snapshotting from the base config forces the base YAML's "
        "grad_accum onto head models and would clobber any with_head "
        "grad_accum change (WR-01)"
    )
    reset_idx = src.find(
        'configs["finetune"].gradient_accumulation_steps = default_grad_accum'
    )
    assert reset_idx != -1, (
        "no grad_accum reset assignment inside the dataset loop (D-07) — "
        "the adjustment block would re-read the previous dataset's "
        "mutated value"
    )
    read_match = re.search(
        r'(?<![\w])grad_accum = configs\[\"finetune\"\]'
        r"\.gradient_accumulation_steps",
        src,
    )
    read_idx = read_match.start() if read_match else -1
    assert read_idx != -1, (
        "no gradient_accumulation_steps adjustment read found — the "
        "reset contract is anchored on this read"
    )
    assert snapshot_idx < reset_idx, (
        "the snapshot must be taken before the reset restores it "
        f"(snapshot at {snapshot_idx}, reset at {reset_idx})"
    )
    assert reset_idx < read_idx, (
        "the reset must precede the adjustment read of "
        f"gradient_accumulation_steps (reset at {reset_idx}, read at "
        f"{read_idx}) — otherwise dataset B starts from dataset A's "
        "mutated value"
    )


def test_fp32_only_models_forced_to_full_precision():
    """CR-01: run_finetune.py forces fp16/bf16 off for the fp32-only quirk
    models — the SAME membership the deprecated pipeline carries (the
    behavioral reference) — before DNATrainer is constructed, so the
    global bf16: True in finetune_config.yaml never trains these models
    in reduced precision."""
    active = RUN_FINETUNE.read_text(encoding="utf-8")
    legacy = LEGACY_PIPELINE.read_text(encoding="utf-8")

    active_list = list_members(active, "models_only_support_fp32")
    legacy_list = list_members(legacy, "models_only_support_fp32")
    assert active_list, (
        "models_only_support_fp32 is missing/empty from run_finetune.py — "
        "the global bf16: True trains these models in reduced precision"
    )
    assert sorted(active_list) == sorted(legacy_list), (
        "run_finetune.py's fp32-only membership must match the deprecated "
        f"pipeline's list (active {sorted(active_list)} vs legacy "
        f"{sorted(legacy_list)}) — the deprecated file is the behavioral "
        "reference"
    )
    override_idx = active.find("if model_name in models_only_support_fp32:")
    assert override_idx != -1, (
        "no fp32 override guarded by models_only_support_fp32 (CR-01) — "
        "the list exists but nothing forces fp16/bf16 off with it"
    )
    tail = active[override_idx:]
    assert 'configs["finetune"].fp16 = False' in tail, (
        "the fp32 override must set fp16 = False"
    )
    assert 'configs["finetune"].bf16 = False' in tail, (
        "the fp32 override must set bf16 = False (the YAML default is True)"
    )
    trainer_idx = active.find("trainer = DNATrainer(")
    assert trainer_idx != -1, "no DNATrainer construction found"
    assert override_idx < trainer_idx, (
        "the fp32 override must precede DNATrainer construction "
        f"(override at {override_idx}, trainer at {trainer_idx}) so the "
        "trainer never sees reduced-precision flags for these models"
    )


def test_dataset_presence_guard_precedes_dataset_load():
    """WR-02: the dataset-dir presence guard (ported from the deprecated
    pipeline's os.path.exists check) precedes the DNADataset.load_local_data
    call site — an unlocatable dataset dir is a documented expected state
    (the suite double-nesting unzip quirk) and must log + continue to the
    next dataset, never raise an uncaught exception that kills the model
    loop."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    guard_idx = src.find("if not os.path.isdir(dataset_path):")
    assert guard_idx != -1, (
        "no dataset-presence guard (WR-02) — DNADataset.load_local_data "
        "would raise an uncaught exception for an unlocatable dataset dir "
        "and kill the rest of the model loop"
    )
    load_idx = src.find("DNADataset.load_local_data(")
    assert load_idx != -1, "no DNADataset.load_local_data call site found"
    assert guard_idx < load_idx, (
        "the presence guard must precede the dataset load "
        f"(guard at {guard_idx}, load at {load_idx}) — a guard after the "
        "load cannot protect it"
    )


def test_final_metrics_written_before_resume_marker():
    """WR-13: in the trainer.train() success block, final_metrics.json is
    written BEFORE the trainer_state.json resume marker is copied — the
    marker is the completion signal both this script's resume check and
    run_sweep.py's skip check read, so it must be the FINAL act of a
    successful cell. Copying the marker first opens a kill window (OOM
    killer, SIGKILL, power loss) in which the cell is permanently "done"
    with no metrics and is never retrained."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    write_idx = src.find('open(outdir + "final_metrics.json"')
    assert write_idx != -1, (
        "no final_metrics.json write found — the sweep driver's "
        "completed/failed contract depends on this file existing"
    )
    copy_idx = src.find(
        'shutil.copy(outdir + f"checkpoint-{last_step}/trainer_state.json"'
    )
    assert copy_idx != -1, (
        "no trainer_state.json resume-marker copy found — without the "
        "marker, resume would retrain every cell"
    )
    assert write_idx < copy_idx, (
        "final_metrics.json must be written before the trainer_state.json "
        f"resume marker is copied (write at {write_idx}, copy at "
        f"{copy_idx}) — the marker promises the metrics exist, so it must "
        "be the final act of a successful cell; a process death between "
        "the two otherwise leaves a cell permanently done-with-no-metrics "
        "that no later sweep ever retrains (WR-13)"
    )


def test_models_no_char_n_parity_with_name_map():
    """WR-03: the ACGT-alphabet list matches the deprecated pipeline's
    models_no_char_n MODULO the documented legacy name map — current
    registry name forms only (dropped names resurrected or the rename
    missed both fail), every member resolves against the unified
    registry, and the validate_sequences call site actually applies the
    conditional charset."""
    active = RUN_FINETUNE.read_text(encoding="utf-8")
    legacy = LEGACY_PIPELINE.read_text(encoding="utf-8")

    active_list = composed_members(active, "models_no_char_n")
    legacy_list = composed_members(legacy, "models_no_char_n")
    assert active_list, (
        "models_no_char_n is missing/empty from run_finetune.py — every "
        "model validates against the ACGT-only charset, so models that "
        "tolerate N bases would have them silently dropped instead"
    )
    expected = apply_legacy_name_map(legacy_list)
    assert set(active_list) == expected, (
        "models_no_char_n must equal the legacy list mapped to current "
        f"registry names (active {sorted(set(active_list))} vs expected "
        f"{sorted(expected)}) — either a legacy name was blindly copied "
        "(dropped names must NOT be resurrected) or a live quirk was lost"
    )
    resurrected = {n for n in LEGACY_NAME_MAP if LEGACY_NAME_MAP[n] is None
                   and n in active_list}
    assert not resurrected, (
        f"dead registry names resurrected into models_no_char_n: "
        f"{sorted(resurrected)} — these models do not exist in the "
        "unified registry (D-10 drops)"
    )
    unresolved = [n for n in active_list if n not in registry_keys()]
    assert not unresolved, (
        f"models_no_char_n members not in the unified registry: "
        f"{unresolved} — the registry is the name authority (D-10)"
    )
    # deeplearning_models is the composition prefix on both sides — pin
    # its membership equality too (all four quirk registries asserted).
    assert (sorted(list_members(active, "deeplearning_models"))
            == sorted(list_members(legacy, "deeplearning_models"))), (
        "deeplearning_models membership diverged from the deprecated "
        "pipeline's list"
    )
    # Wiring: the conditional charset at the validate_sequences site,
    # with the exact legacy strings (deprecated pipeline :1055). The
    # conditional expression places the ACGT literal BEFORE the guard
    # line, so the window includes preceding context.
    cond_idx = statement_index(active, "if model_name in models_no_char_n")
    assert cond_idx != -1, (
        "no models_no_char_n conditional — the list exists but "
        "validate_sequences never applies it (dead list, the WR-03 bug)"
    )
    validate_idx = statement_index(active, "dataset.validate_sequences(")
    assert validate_idx != -1, "no validate_sequences call site found"
    window = active[max(0, cond_idx - 200):validate_idx + 200]
    assert '"ACGTacgt|"' in window, (
        'list members must validate against "ACGTacgt|" (the ACGT-only '
        "charset)"
    )
    assert '"ACGTNacgtn|"' in window, (
        'non-members must validate against "ACGTNacgtn|" (N-allowing) — '
        "hardcoding either charset for ALL models is the divergence the "
        "parity port closes"
    )
    assert cond_idx < validate_idx, (
        "the charset conditional must precede the validate_sequences call"
    )


def test_models_with_limited_length_wired():
    """WR-03/AUD-15: the per-model max_length caps match the deprecated
    pipeline's models_with_limited_length (name-mapped) AND are WIRED —
    the legacy dict was defined but never applied (dead config); the
    rewrite must clamp max_length at the determination block, and every
    member must resolve against the unified registry."""
    active = RUN_FINETUNE.read_text(encoding="utf-8")
    legacy = LEGACY_PIPELINE.read_text(encoding="utf-8")

    active_caps = dict_members(active, "models_with_limited_length")
    legacy_caps = dict_members(legacy, "models_with_limited_length")
    assert active_caps, (
        "models_with_limited_length is missing/empty from run_finetune.py "
        "— prokbert-mini and plant-dnabert-6mer would run past their "
        "documented context caps"
    )
    expected = {
        LEGACY_NAME_MAP.get(name, name): value
        for name, value in legacy_caps.items()
        if LEGACY_NAME_MAP.get(name, name) is not None
    }
    assert active_caps == expected, (
        f"models_with_limited_length must equal the legacy caps "
        f"(active {active_caps} vs expected {expected})"
    )
    unresolved = [n for n in active_caps if n not in registry_keys()]
    assert not unresolved, (
        f"models_with_limited_length members not in the unified registry: "
        f"{unresolved} (D-10 name authority)"
    )
    # Wiring (the AUD-15 point — legacy never used the dict): a clamp on
    # max_length guarded by the dict, downstream of the max_length
    # determination (the max_token_len clamp) and upstream of the batch
    # sizing that consumes max_length.
    clamp_idx = statement_index(
        active, "if model_name in models_with_limited_length:")
    assert clamp_idx != -1, (
        "no models_with_limited_length guard — the dict exists but "
        "nothing clamps max_length with it (the AUD-15 dead-config state)"
    )
    clamp_block = active[clamp_idx:clamp_idx + 400]
    compact = re.sub(r"\s+", "", clamp_block)
    assert ("min(max_length,models_with_limited_length[model_name])"
            in compact), (
        "the guard must CLAMP max_length to the per-model cap "
        "(min(max_length, models_with_limited_length[model_name])), not "
        "merely reference the dict"
    )
    max_token_idx = statement_index(
        active, "if max_token_len and max_length > max_token_len:")
    assert max_token_idx != -1, "no max_token_len clamp found"
    estimator_idx = statement_index(
        active, "if auto_batch_size and count == 0:")
    assert estimator_idx != -1, "no auto-batch estimator block found"
    assert max_token_idx < clamp_idx < estimator_idx, (
        "the per-model clamp must sit after the max_length-determination "
        "block and before the batch sizing that consumes max_length "
        f"(token-len clamp at {max_token_idx}, clamp at {clamp_idx}, "
        f"estimator at {estimator_idx})"
    )


def test_safetensors_list_is_legacy_union():
    """WR-03 union fix: model_not_use_safetensors is EXACTLY the legacy
    set plus PlantGFM (11 entries) — the legacy list carried
    plant-dnamamba-6mer which the rewrite dropped, and the rewrite added
    PlantGFM which the legacy lacked; the union keeps both so neither
    side loses a model needing the quirk. Every member resolves against
    the unified registry."""
    active = RUN_FINETUNE.read_text(encoding="utf-8")
    legacy = LEGACY_PIPELINE.read_text(encoding="utf-8")

    active_list = list_members(active, "model_not_use_safetensors")
    legacy_list = list_members(legacy, "model_not_use_safetensors")
    assert set(active_list) == set(legacy_list) | {"PlantGFM"}, (
        "model_not_use_safetensors must be the exact 11-entry union "
        "(legacy set plus PlantGFM) — active: "
        f"{sorted(set(active_list))}, legacy|PlantGFM: "
        f"{sorted(set(legacy_list) | {'PlantGFM'})}"
    )
    assert len(active_list) == 11, (
        f"expected exactly 11 union entries, got {len(active_list)}"
    )
    assert "plant-dnamamba-6mer" in active_list, (
        "plant-dnamamba-6mer (legacy member) missing — the rewrite's drop "
        "would leave this model failing to save checkpoints it cannot "
        "serialize as safetensors"
    )
    assert "PlantGFM" in active_list, "PlantGFM (rewrite member) missing"
    unresolved = [n for n in active_list if n not in registry_keys()]
    assert not unresolved, (
        f"safetensors list members not in the unified registry: "
        f"{unresolved} (D-10 name authority)"
    )
    guard_idx = statement_index(
        active, "if model_name in model_not_use_safetensors:")
    assert guard_idx != -1, (
        "no model_not_use_safetensors guard — the list exists but "
        "save_safetensors is never disabled with it"
    )
    disable_idx = statement_index(
        active, 'configs["finetune"].save_safetensors = False')
    assert disable_idx != -1 and disable_idx > guard_idx, (
        "the guard must set save_safetensors = False in its branch"
    )


def test_length_tier_rounding_parity():
    """WR-04: determine_batch_size is the legacy tier table verbatim
    (behaviorally proven by exec-ing the extracted pure function from
    BOTH sources — no torch import needed), and the tier cap is WIRED as
    the initial batch cap composed BEFORE the VRAM estimators with the
    legacy grad_accum compensation preserved at the adjustment site."""
    active = RUN_FINETUNE.read_text(encoding="utf-8")
    legacy = LEGACY_PIPELINE.read_text(encoding="utf-8")

    def extract_fn(src):
        match = re.search(
            r"def determine_batch_size\(.*?return dynamic_batch_size",
            src, re.DOTALL,
        )
        assert match is not None, (
            "no determine_batch_size function found — the WR-04 length-"
            "tier table is missing"
        )
        namespace = {}
        exec(match.group(0), namespace)  # noqa: S102 - pure extracted fn
        return namespace["determine_batch_size"]

    active_fn = extract_fn(active)
    legacy_fn = extract_fn(legacy)
    # Tier boundaries (legacy semantics): <=512 full, then //2 //4 //8
    # //16 //32 at 1024/2048/4096/8192/16384, else 1 — and the max(1, ..)
    # floor at every tier.
    cases = [
        (512, 32, 32), (513, 32, 16), (1024, 32, 16), (1025, 32, 8),
        (2048, 32, 8), (2049, 32, 4), (4096, 32, 4), (4097, 32, 2),
        (8192, 32, 2), (8193, 32, 1), (16384, 32, 1), (16385, 32, 1),
        (2048, 3, 1),   # max(1, 3 // 4) floor
        (1024, 1, 1),   # floor at batch_size 1
        (512, 0, 0),
    ]
    for max_length, batch_size, expected in cases:
        assert legacy_fn(max_length, batch_size) == expected, (
            f"legacy oracle self-check failed at ({max_length}, "
            f"{batch_size}) — the parity oracle's tier table changed"
        )
        assert active_fn(max_length, batch_size) == expected, (
            f"active determine_batch_size diverged from the legacy tier "
            f"table at (max_length={max_length}, batch_size="
            f"{batch_size}): expected {expected}"
        )
    # Wiring 1: the tier cap is computed from the resolved max_length
    # BEFORE the VRAM estimator block runs.
    tier_call_idx = statement_index(
        active, "tier_batch_cap = determine_batch_size(max_length, batch_size)")
    assert tier_call_idx != -1, (
        "determine_batch_size is never called with the resolved "
        "max_length/batch_size — dead function, the WR-04 bug"
    )
    estimator_idx = statement_index(
        active, "if auto_batch_size and count == 0:")
    assert estimator_idx != -1, "no auto-batch estimator block found"
    assert tier_call_idx < estimator_idx, (
        "the tier cap must be computed BEFORE the VRAM estimator runs "
        f"(tier call at {tier_call_idx}, estimator at {estimator_idx})"
    )
    # Wiring 2: composition — bs_new is min()'d with the tier cap so the
    # estimators only ever reduce below it, never raise past it.
    cap_idx = statement_index(active, "bs_new = min(bs_new, tier_batch_cap)")
    assert cap_idx != -1, (
        "no bs_new = min(bs_new, tier_batch_cap) composition — the VRAM "
        "estimators can raise the batch past the length-tier cap"
    )
    # Wiring 3: the legacy grad_accum compensation at the adjustment site.
    comp_idx = statement_index(
        active, "scaling_factor = max(1, batch_size // bs_new)")
    assert comp_idx != -1, (
        "no grad_accum compensation (max(1, batch_size // bs_new)) at the "
        "adjustment site — a tier/VRAM reduction would silently shrink "
        "the effective batch (legacy parity requires the scaling factor)"
    )
    assert comp_idx > cap_idx, (
        "the grad_accum compensation must sit at the adjustment site, "
        "after the tier-capped bs_new is determined"
    )


# ===== unified eval subset (F7 Q3 / REV-03, 05-03) =====


def extract_subset_fns():
    """Exec-extract ``validate_subset_file`` + ``apply_eval_subset`` from
    the run_finetune source (the read-source-never-import pattern —
    torch/dnallm are unavailable CPU-side; the two functions are pure
    and contiguous, ending right before ``set_seed``)."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    match = re.search(
        r"def validate_subset_file\(.*?\n(?=def set_seed)", src, re.DOTALL
    )
    assert match is not None, (
        "no validate_subset_file/apply_eval_subset functions found in "
        "run_finetune.py — the --subset_file validator and apply seam "
        "are missing (F7 Q3)"
    )
    namespace = {"json": json, "Path": Path}
    exec(match.group(0), namespace)  # noqa: S102 - pure extracted fns
    return namespace["validate_subset_file"], namespace["apply_eval_subset"]


class RecordingSplit:
    """Stub HF split: records ``.select`` calls (the test double for
    ``datasets.Dataset.select`` — the same primitive the suite's own
    ``sampling()`` uses)."""

    def __init__(self):
        self.select_calls = []

    def select(self, ids):
        self.select_calls.append(list(ids))
        return self


def write_subset_file(tmp_path, payload):
    """Write a subset-file JSON fixture, return its path."""
    path = tmp_path / "subsets.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


REGISTRY_5 = {
    "TASK": {"Dataset_name": "TASK", "Test": 5},
    "OTHER": {"Dataset_name": "OTHER", "Test": 3},
}


def test_subset_validator_accepts_valid_file(tmp_path):
    """Known registry keys with in-range integer ID lists load cleanly:
    no problems, and the loaded map is returned verbatim."""
    validate, _apply = extract_subset_fns()
    path = write_subset_file(tmp_path, {"TASK": [0, 4, 2]})
    subsets, problems = validate(path, REGISTRY_5)
    assert problems == []
    assert subsets == {"TASK": [0, 4, 2]}


def test_subset_validator_reports_every_malformed_class_by_name(tmp_path):
    """Unknown task key, non-integer ID, negative ID, and out-of-range ID
    are ALL collected in one pass and named per class — no partial
    application before validation completes."""
    validate, _apply = extract_subset_fns()
    path = write_subset_file(
        tmp_path,
        {"TASK": [0, "x", -1, 5], "UNKNOWN_TASK": [0]},
    )
    subsets, problems = validate(path, REGISTRY_5)
    assert subsets is None
    joined = "; ".join(problems)
    assert "UNKNOWN_TASK" in joined, "unknown key must be named"
    assert "'x'" in joined, "non-integer ID must be named"
    assert "-1" in joined, "negative ID must be named"
    assert "out of range [0, 5)" in joined, (
        "the out-of-range ID must be named with the task's row range"
    )
    # every malformed class present (not just the first)
    assert any("not in datasets_info" in p for p in problems)
    assert any("non-integer" in p for p in problems)
    assert any("negative" in p for p in problems)
    assert any("out of range" in p for p in problems)


def test_subset_validator_rejects_non_object_json(tmp_path):
    """A non-object top level (list, string) is reported as such."""
    validate, _apply = extract_subset_fns()
    for payload in ([1, 2], "nope", 7):
        path = write_subset_file(tmp_path, payload)
        subsets, problems = validate(path, REGISTRY_5)
        assert subsets is None
        assert any("expected an object" in p for p in problems), problems


def test_subset_validator_rejects_unreadable_file(tmp_path):
    """A missing/unreadable file is a problem, not a crash."""
    validate, _apply = extract_subset_fns()
    _subsets, problems = validate(tmp_path / "absent.json", REGISTRY_5)
    assert any("cannot read" in p for p in problems), problems


def test_subset_validator_rejects_non_list_value(tmp_path):
    """A task whose value is not a list is named with its actual type."""
    validate, _apply = extract_subset_fns()
    path = write_subset_file(tmp_path, {"TASK": 3})
    subsets, problems = validate(path, REGISTRY_5)
    assert subsets is None
    assert any("TASK" in p and "int" in p for p in problems), problems


def test_subset_validator_refuses_dataset_name_divergence(tmp_path):
    """WR-03 (05 review): a registry row whose Dataset_name differs from
    its registry key is refused by name — the map is keyed on registry
    KEYS at validation but applied by Dataset_name at the seam, so a
    divergent row would silently no-op that task's subset (full-split
    evaluation while the operator believes the unified-N fairness subset
    is applied). Coincident rows (REGISTRY_5 above) stay a no-op."""
    validate, _apply = extract_subset_fns()
    registry = {
        "TASK": {"Dataset_name": "TASK", "Test": 5},
        "DIVERGENT": {"Dataset_name": "renamed__task", "Test": 3},
    }
    path = write_subset_file(tmp_path, {"DIVERGENT": [0, 1]})
    subsets, problems = validate(path, registry)
    assert subsets is None, (
        "a divergent row must fail validation — never return the map"
    )
    assert any(
        "Dataset_name" in p and "DIVERGENT" in p for p in problems
    ), problems
    assert any("silently" in p for p in problems), (
        "the problem must say WHY divergence is refused"
    )


def test_apply_eval_subset_selects_test_split_only():
    """With subset IDs for the current dataset, the seam invokes select
    with EXACTLY those IDs on the test split — train and dev splits are
    never selected."""
    _validate, apply_fn = extract_subset_fns()
    train, dev, test = RecordingSplit(), RecordingSplit(), RecordingSplit()
    holder = {"train": train, "dev": dev, "test": test}
    apply_fn(holder, "TASK", {"TASK": [3, 1, 2]})
    assert test.select_calls == [[3, 1, 2]]
    assert train.select_calls == [], "train must never be selected"
    assert dev.select_calls == [], "dev must never be selected"


def test_apply_eval_subset_absent_flag_no_select_anywhere():
    """Absent flag (None): zero select calls anywhere — the code path is
    identical to today."""
    _validate, apply_fn = extract_subset_fns()
    splits = {name: RecordingSplit() for name in ("train", "dev", "test")}
    apply_fn(splits, "TASK", None)
    assert all(s.select_calls == [] for s in splits.values())


def test_apply_eval_subset_task_without_entry_no_call():
    """A dataset with no entry in the map runs full evaluation."""
    _validate, apply_fn = extract_subset_fns()
    splits = {name: RecordingSplit() for name in ("train", "dev", "test")}
    apply_fn(splits, "OTHER", {"TASK": [0, 1]})
    assert all(s.select_calls == [] for s in splits.values())


def test_subset_file_flag_declared_in_parse_args():
    """--subset_file exists with type=Path, default None, and help naming
    the JSON shape and that absence means full evaluation."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    arg_idx = src.find('"--subset_file"')
    assert arg_idx != -1, (
        "no --subset_file argument in parse_args() — the pipeline cannot "
        "consume pipeline/eval_subsets.json (F7 Q3)"
    )
    block = src[arg_idx:arg_idx + 600]
    assert "type=Path" in block, "--subset_file must be type=Path"
    assert "default=None" in block, "--subset_file must default to None"
    assert "full evaluation" in block, (
        "the help must state that an absent flag means full evaluation"
    )


def test_subset_seam_sits_between_load_and_validate():
    """The apply seam is wired between the DNADataset.load_local_data call
    and the dataset.validate_sequences call — BEFORE validation, so the
    audited IDs are the actually-evaluated rows."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    load_idx = statement_index(src, "dataset = DNADataset.load_local_data(")
    assert load_idx != -1, "no DNADataset.load_local_data call site found"
    apply_idx = statement_index(
        src, "apply_eval_subset(dataset.dataset, dataset_name, eval_subsets)")
    assert apply_idx != -1, (
        "no apply_eval_subset(dataset.dataset, ...) wiring — the seam "
        "exists but is never invoked at the load/validate boundary "
        "(F7 Q3)"
    )
    validate_idx = statement_index(src, "dataset.validate_sequences(")
    assert validate_idx != -1, "no validate_sequences call site found"
    assert load_idx < apply_idx < validate_idx, (
        "the subset select must sit AFTER the dataset load and BEFORE "
        f"validate_sequences (load {load_idx}, apply {apply_idx}, "
        f"validate {validate_idx})"
    )


def test_subset_file_validated_fail_fast_with_error_exit():
    """The __main__ wiring validates the map and exits non-zero with an
    [Error] message listing the collected problems — before any model
    load (the _validate_filters discipline)."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    wiring_idx = statement_index(
        src, "eval_subsets, subset_problems = validate_subset_file(")
    assert wiring_idx != -1, (
        "no validate_subset_file call in the __main__ wiring — a bad "
        "--subset_file would be applied unvalidated (T-05-08)"
    )
    assert "[Error] invalid --subset_file" in src, (
        "the fail-fast exit must carry an [Error] invalid --subset_file "
        "message naming the problems"
    )
    model_loop_idx = src.find("models_info.items():")
    assert model_loop_idx != -1, "no model loop found"
    assert wiring_idx < model_loop_idx, (
        "the subset validation must run BEFORE the model loop — no "
        "partial application or model load ahead of validation"
    )
