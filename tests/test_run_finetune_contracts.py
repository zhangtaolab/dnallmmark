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
  (``dnallm/finetune/trainer.py`` L571-605 @ v1.2.1, tag 30dfd6d) make
  test eval strictly opt-in via that key (config default False), so our
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
- **adapter-run aliases + epochs override + trainable-params persistence
  (SC-6/REV-05, 06-02)** — ``--peft lora|ia3`` with NO explicit
  ``--save_model_name`` defaults the effective save name to
  ``{model}+lora`` / ``{model}+ia3`` (a separate model-level output dir
  AND therefore a separate ``trainer_state.json`` resume marker, with
  zero layout-code changes; an explicit ``--save_model_name`` always
  wins; the registry lookup / target_model filtering stays on the BASE
  name; ``none`` keeps exactly the base name — byte-identical outdir);
  ``--num_train_epochs`` (int, default None) OVERRIDES the loaded
  config's ``finetune.num_train_epochs`` only when given (the
  bounded-smoke knob — 06-02's 1-epoch LoRA smoke and 06-05's probe
  smoke), placed after the custom-head reload and before the epoch read;
  trainable/total params are computed immediately after the DNATrainer
  ctor (pure arithmetic over the constructed model — the suite PRINTS
  but does not PERSIST this accounting, trainer.py:248-288 @ v1.2.1) and
  merged into the final_metrics.json payload for EVERY mode including
  none (a full run reports 100.0) — the frontier table's producer.
- **--config-variant mechanism + frozen probe (SC-6/REV-05 F4, 06-05)** —
  ``--config-variant {head,probe,curve}`` (default None) loads its YAML
  via the module-level VARIANT_CONFIGS mapping at the exact in-loop slot
  the special_models reload occupies (after the per-model base reload,
  before the unchanged special_models branch and the D-11 grad_accum
  snapshot — the ACTIVE config governs); the frozen probe is the with_head
  block with head ``mlp``, ``frozen: true``, ``hidden_dims [512]``
  (suite-owned fields only); a module-level PROBE_INELIGIBLE list (the
  deeplearning four + the special_models two + the gpn/omnidna dedicated
  special-loader registry members, one provenance comment each) backs an
  argv-boundary guard refusing probe runs on special-loader models with a
  disclosing ``[Error]``; the probe variant alone defaults the save name
  to ``{model}+probe`` (the 06-02 alias seam); the per-dataset
  head_config.task_type assignment stays variant-unconditioned.

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
ENV_SMOKE = REPO_ROOT / "pipeline" / "env_smoke.py"
LEGACY_PIPELINE = REPO_ROOT / "pipeline" / "dnallmmark_pipeline.py"
MODELS_INFO = REPO_ROOT / "pipeline" / "models_info.json"
PROBE_CONFIG = REPO_ROOT / "pipeline" / "finetune_config_probe.yaml"
WITH_HEAD_CONFIG = REPO_ROOT / "pipeline" / "finetune_config_with_head.yaml"
FINETUNE_CONFIGS = [
    REPO_ROOT / "pipeline" / "finetune_config.yaml",
    REPO_ROOT / "pipeline" / "finetune_config_with_head.yaml",
    REPO_ROOT / "pipeline" / "finetune_config_probe.yaml",
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


def extract_fraction_fns():
    """Exec-extract ``validate_train_fraction`` + ``apply_train_fraction``
    (the read-source-never-import pattern; the two functions are pure —
    the span runs to ``def set_seed``, sweeping the module-level variant
    constants harmlessly along the way)."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    match = re.search(
        r"def validate_train_fraction\(.*?\n(?=def set_seed)", src, re.DOTALL
    )
    assert match is not None, (
        "no validate_train_fraction/apply_train_fraction functions found "
        "in run_finetune.py — the --train_fraction validator and apply "
        "seam are missing (REV-08/F8, 06-05)"
    )
    namespace = {}
    exec(match.group(0), namespace)  # noqa: S102 - pure extracted fns
    return (
        namespace["validate_train_fraction"],
        namespace["apply_train_fraction"],
    )


class ShuffleSplit:
    """Stub HF split: records ``shuffle``/``select`` calls (the fraction
    seam's primitives — the same Dataset API the eval-subset seam's
    ``select`` uses)."""

    def __init__(self, n=100):
        self.n = n
        self.shuffle_calls = []
        self.select_calls = []

    def __len__(self):
        return self.n

    def shuffle(self, seed=None):
        self.shuffle_calls.append((seed, self.n))
        return self

    def select(self, ids):
        self.select_calls.append(list(ids))
        return self


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


# =====================================================================
# dnallm v1.2.1 adaptation (06-01) — re-pinned suite citations
# =====================================================================

def test_suite_citations_pinned_to_v121_tag():
    """06-01: run_finetune.py carries ZERO stale pre-v1.2.1 revision
    citations — the suite's v1.2 revision (~26.9k insertions, commit
    92a8106) landed between 483a35c and v1.2.1 and shifted the cited
    line ranges, so adaptation anchors must pin to tag v1.2.1 (30dfd6d),
    never the moving dev branch. The EVAL-01 refusal comment cites the
    v1.2.1 anchor 'trainer.py L571-605 @ v1.2.1 (30dfd6d)' (same guard
    content, shifted lines), and the model-loading region documents the
    v1.2.1 attn_implementation='eager' hard pin so no redundant
    attention-implementation quirk is ever added on our side."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    assert "483a35c" not in src, (
        "a stale pre-v1.2.1 suite revision citation ('483a35c') survives "
        "in run_finetune.py — adaptation citations must be re-pinned to "
        "tag v1.2.1 (30dfd6d); the suite branch moved during the v1.2 "
        "revision and line anchors shifted"
    )
    assert "trainer.py L571-605 @ v1.2.1 (30dfd6d)" in src, (
        "the EVAL-01 refusal comment must cite the v1.2.1 anchor "
        "'trainer.py L571-605 @ v1.2.1 (30dfd6d)' — the guard block sits "
        "at L571-605 in v1.2.1 (L568-605 at the pre-v1.2 483a35c)"
    )
    load_idx = statement_index(
        src, "model, tokenizer = load_model_and_tokenizer("
    )
    assert load_idx != -1, "no load_model_and_tokenizer call site found"
    eager_idx = src.find("attn_implementation")
    assert eager_idx != -1, (
        "the model-loading region must document v1.2.1's hardcoded "
        "attn_implementation=\"eager\" in _load_model_by_task_type's "
        "model_load_kwargs — without the note a future quirk list would "
        "add a redundant attention-implementation override on our side"
    )
    assert "model.py:590-594" in src, (
        "the eager-pin note must cite its read-only suite anchor "
        "(model.py:590-594 @ v1.2.1)"
    )
    assert eager_idx < load_idx and load_idx - eager_idx < 2000, (
        "the eager-pin note must sit in the model-loading comment region "
        f"(note at {eager_idx}, load call at {load_idx}) — next to the "
        "load it explains, not far away in an unrelated block"
    )


# =====================================================================
# PEFT tracer wiring (06-01, SC-6 lane gate) — LoRA + IA3 passthrough
# =====================================================================

def test_peft_flags_mirror_the_subset_file_seam_shape():
    """--peft is an argparse choices flag (none/lora/ia3, default none)
    and --peft_dry_run a store_true — the --subset_file flag shape."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    peft_idx = src.find('"--peft"')
    assert peft_idx != -1, "no --peft argument in parse_args() (SC-6)"
    block = src[peft_idx:peft_idx + 900]
    assert 'choices=["none", "lora", "ia3"]' in block, (
        "--peft must be choices=[none, lora, ia3] (argparse rejects any "
        "other mode at the argv boundary)"
    )
    assert 'default="none"' in block, (
        "--peft must default to 'none' — the peft=none path is the "
        "byte-identical legacy surface (SC-6 gating tracer)"
    )
    dry_idx = src.find('"--peft_dry_run"')
    assert dry_idx != -1, "no --peft_dry_run argument in parse_args()"
    dry_block = src[dry_idx:dry_idx + 600]
    assert "action=" in dry_block and "store_true" in dry_block, (
        "--peft_dry_run must be a store_true flag"
    )


def test_peft_dry_run_without_adapter_mode_fails_fast():
    """--peft_dry_run with --peft none (or absent) is an argparse-adjacent
    fail-fast: an [Error] message naming BOTH flags, before the model
    loop — the dry run is validate-and-exit, there is no adapter to
    validate in none mode (mirrors the suite's own ctor refusal)."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    error_idx = src.find("[Error] --peft_dry_run requires")
    assert error_idx != -1, (
        "no [Error] fail-fast for --peft_dry_run without an adapter mode "
        "— the run would either silently full-train or die deep in the "
        "suite's ctor refusal instead of at the argv boundary"
    )
    message = src[error_idx:error_idx + 300]
    assert "--peft" in message and "--peft_dry_run" in message, (
        "the composition error must name both --peft_dry_run and --peft"
    )
    model_loop_idx = src.find("models_info.items():")
    assert error_idx < model_loop_idx, (
        "the composition check must run before the model loop (an "
        "argparse-adjacent fail-fast, never discovered mid-sweep)"
    )


def test_ctor_site_carries_use_lora_kwarg():
    """The DNATrainer ctor call site carries
    use_lora=(peft_mode == \"lora\") — LoRA enablement is a CONSTRUCTOR
    KWARG in the suite (trainer.py:369-376 @ v1.2.1), not a config
    field; a pure comparison evaluates False under the none default."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    ctor_idx = statement_index(src, "trainer = DNATrainer(")
    assert ctor_idx != -1, "no DNATrainer ctor call site found"
    ctor_block = src[ctor_idx:ctor_idx + 900]
    assert "use_lora=(peft_mode == \"lora\")" in ctor_block, (
        "the ctor call must pass use_lora=(peft_mode == \"lora\") — "
        "without the kwarg --peft lora silently full-trains (the suite "
        "has no config-field path for LoRA)"
    )


def test_use_ia3_mutation_precedes_ctor_inside_quirk_block():
    """configs[\"finetune\"].use_ia3 = True is set under an ia3-mode guard
    inside the per-dataset quirk-mutation block (the save_safetensors
    pattern) BEFORE the DNATrainer ctor reads it — IA3 enablement IS a
    TrainingConfig field (suite configs.py:326-334 @ v1.2.1)."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    guarded = re.search(
        r'if peft_mode == "ia3":\s*\n[^\S\n]*configs\["finetune"\]'
        r"\.use_ia3 = True",
        src,
    )
    assert guarded is not None, (
        'no guarded "if peft_mode == \\"ia3\\": configs[\\"finetune\\"]'
        '.use_ia3 = True" mutation — IA3 needs the TrainingConfig field '
        "set before the ctor, and the guard keeps the none default a "
        "no-op"
    )
    safetensors_idx = statement_index(
        src, 'configs["finetune"].save_safetensors = True'
    )
    assert safetensors_idx != -1, "no safetensors quirk mutation found"
    ctor_idx = statement_index(src, "trainer = DNATrainer(")
    assert ctor_idx != -1, "no DNATrainer ctor call site found"
    assert safetensors_idx < guarded.start() < ctor_idx, (
        "the use_ia3 mutation must sit in the per-dataset quirk block "
        f"(after the safetensors quirk at {safetensors_idx}, before the "
        f"ctor at {ctor_idx})"
    )
    dry_guarded = re.search(
        r"if peft_dry_run:\s*\n[^\S\n]*configs\[\"finetune\"\]"
        r"\.peft_dry_run = True",
        src,
    )
    assert dry_guarded is not None, (
        'no guarded "if peft_dry_run: configs[\\"finetune\\"]'
        '.peft_dry_run = True" mutation — the suite reads the '
        "TrainingConfig flag at ctor time to validate-and-exit"
    )
    assert guarded.start() < dry_guarded.start() < ctor_idx, (
        "the peft_dry_run mutation must also precede the ctor"
    )


def test_peft_none_save_name_is_exactly_the_base_name():
    """06-02 evolution of the 06-01 no-op contract, extended by 06-05's
    probe alias branch: the save-name resolution now carries the adapter
    alias AND the probe alias branches, but under peft=none + no variant
    the effective name is STILL exactly model_name (the final else branch
    of the chain) — the none-mode outdir is byte-identical to today's;
    every peft-driven config mutation remains mode-guarded so the none
    path evaluates exactly the pre-tracer statements."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    chain = re.search(
        r'if save_model_name:\s*\n'
        r'[^\S\n]*model_save_name = save_model_name\s*\n'
        r'[^\S\n]*elif peft_mode != "none":\s*\n'
        r'[^\S\n]*model_save_name = f"\{model_name\}\+\{peft_mode\}"\s*\n'
        r'[^\S\n]*elif config_variant == "probe":\s*\n'
        r'[^\S\n]*model_save_name = f"\{model_name\}\+probe"\s*\n'
        r"[^\S\n]*else:\s*\n"
        r"[^\S\n]*model_save_name = model_name",
        src,
    )
    assert chain is not None, (
        "the save-name resolution must be the four-branch chain "
        '(explicit --save_model_name) > (peft alias {model}+{mode}) > '
        "(probe alias {model}+probe, 06-05) > (base name) — an unchainable "
        "form (e.g. an or-expression) would either drop an alias default "
        "or change the none-mode name"
    )
    # Every configs["finetune"] mutation mentioning peft must be guarded;
    # an unguarded one would mutate the none path.
    for match in re.finditer(
        r'configs\["finetune"\]\.(use_ia3|peft_dry_run) = True', src
    ):
        preceding = src[max(0, match.start() - 200):match.start()]
        guard = re.search(
            r'if (peft_mode == "ia3"|peft_dry_run):\s*$', preceding
        )
        assert guard is not None, (
            f"peft mutation at offset {match.start()} is not mode-"
            "guarded — the peft=none path would diverge from the legacy "
            "surface (SC-6 gating tracer contract)"
        )


def test_adapter_alias_defaults_when_peft_mode_active():
    """With --peft lora/ia3 and NO explicit --save_model_name, the effective
    save name defaults to {model}+lora / {model}+ia3 — name isolation
    end-to-end: a separate model-level output dir and therefore a separate
    trainer_state.json resume marker, with zero layout-code changes (SC-6,
    REV-05/F4). The alias branch must reference the explicit flag's falsiness
    (elif after the explicit-if) so an explicit name always wins."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    alias_branch = re.search(
        r'elif peft_mode != "none":\s*\n'
        r'[^\S\n]*model_save_name = f"\{model_name\}\+\{peft_mode\}"',
        src,
    )
    assert alias_branch is not None, (
        'no "elif peft_mode != \\"none\\": model_save_name = '
        'f"{model_name}+{peft_mode}" branch — an adapter run without an '
        "explicit --save_model_name must default to the {model}+lora/+ia3 "
        "alias or it would share the base run's output dir AND resume "
        "marker (Pitfall 3)"
    )
    outdir_idx = src.find(
        'f"{save_root}/{model_save_name}/{dataset_name}/seed_{seed}/"'
    )
    assert outdir_idx != -1, "the seed-isolated outdir f-string is gone"
    assert alias_branch.start() < outdir_idx, (
        "the alias default must resolve BEFORE the outdir f-string "
        "consumes it — an alias applied after outdir construction would "
        "silently write the base dir"
    )


def test_explicit_save_model_name_wins_over_alias_default():
    """An explicitly passed --save_model_name always wins over the alias
    default: the explicit-flag branch is the FIRST branch of the save-name
    chain, immediately preceding the peft elif."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    explicit_idx = statement_index(src, "if save_model_name:")
    alias_idx = src.find('elif peft_mode != "none":')
    assert explicit_idx != -1, (
        "no explicit-flag branch in the save-name resolution — an explicit "
        "--save_model_name must take precedence over the alias default"
    )
    assert alias_idx != -1, "no peft alias branch found"
    assert 0 < alias_idx - explicit_idx < 200, (
        "the explicit --save_model_name branch must sit immediately before "
        "the peft elif in the same chain (a distant or inverted ordering "
        "would let the alias default override an explicit operator choice)"
    )


def test_registry_lookup_stays_on_base_model_name():
    """The registry lookup / target_model filtering still uses the BASE
    model name — the alias affects ONLY output naming. The model-loop
    filter compares model_name, and no quirk-list membership check or
    config mutation between the quirk block and the alias resolution
    references model_save_name."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    filter_idx = src.find(
        "if target_model is not None and model_name != target_model:"
    )
    assert filter_idx != -1, "the base-name target_model filter is gone"
    alias_idx = src.find(
        'model_save_name = f"{model_name}+{peft_mode}"'
    )
    assert alias_idx != -1, "no alias construction found"
    assert filter_idx < alias_idx, (
        "the target_model filter runs on model_name BEFORE the alias "
        "resolution — aliasing the registry lookup would break "
        "--target_model targeting for every adapter run"
    )
    quirk_start = src.find("if model_name in models_only_support_fp32:")
    assert quirk_start != -1, "no fp32 quirk membership check found"
    chain_start = statement_index(src, "save_root = output_dir")
    assert chain_start != -1, "no save_root resolution found"
    quirk_region = src[quirk_start:chain_start]
    assert "model_save_name" not in quirk_region, (
        "the quirk-mutation region must stay keyed on model_name — a "
        "model_save_name reference there would skip every quirk for "
        "adapter runs (the alias is not a registry name)"
    )


def test_num_train_epochs_flag_overrides_config_only_when_given():
    """--num_train_epochs (int, default None) OVERRIDES the loaded config's
    finetune.num_train_epochs when given and leaves the YAML value governing
    when absent (a None-guarded pure assignment — the --subset_file seam
    style). Placement: AFTER the custom-head reload (so it applies to
    whichever config is active) and BEFORE the epoch read that sizes
    logging/eval/save steps and the DNATrainer ctor. This is the
    bounded-smoke knob (plan-check blocker fix 2026-10-11: the smokes
    previously passed a flag that did not exist)."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    flag_idx = src.find('"--num_train_epochs"')
    assert flag_idx != -1, (
        "no --num_train_epochs argument in parse_args() — the bounded "
        "smokes (06-02 LoRA, 06-05 probe) pass this flag"
    )
    flag_block = src[flag_idx:flag_idx + 400]
    assert re.search(r"type=int", flag_block), (
        "--num_train_epochs must be type=int (an epoch count)"
    )
    assert re.search(r"default=None", flag_block), (
        "--num_train_epochs must default to None — absent flag means the "
        "YAML value governs (byte-identical to today)"
    )
    guarded = re.search(
        r"if num_train_epochs is not None:\s*\n"
        r'[^\S\n]*configs\["finetune"\]\.num_train_epochs = num_train_epochs',
        src,
    )
    assert guarded is not None, (
        'no None-guarded "if num_train_epochs is not None: '
        'configs[\\"finetune\\"].num_train_epochs = num_train_epochs" '
        "assignment — the override must write through to the config ONLY "
        "when the flag is given"
    )
    head_idx = src.find('model_name in ["evo2_1b_base", "megaDNA_updated"]')
    assert head_idx != -1, "no custom-head membership check found"
    assert head_idx < guarded.start(), (
        "the epochs override must sit AFTER the custom-head reload — a "
        "with_head reload would otherwise clobber the override for "
        "evo2_1b_base / megaDNA_updated"
    )
    epoch_read_idx = statement_index(
        src, 'epoch = configs["finetune"].num_train_epochs'
    )
    assert epoch_read_idx != -1, "no epoch read found in the dataset loop"
    ctor_idx = statement_index(src, "trainer = DNATrainer(")
    assert guarded.start() < epoch_read_idx < ctor_idx, (
        "the epochs override must land before both the epoch read (which "
        "sizes logging/eval/save steps) and the DNATrainer ctor"
    )


def test_trainable_params_persisted_into_final_metrics_for_every_mode():
    """trainable_params / total_params / trainable_params_pct are computed
    immediately after the DNATrainer ctor — pure arithmetic over the
    constructed model: sums of p.numel() over trainer.model.parameters()
    filtered by requires_grad (trainable) and unfiltered (total), pct
    derived and rounded to 6 decimals — and merged into the metrics payload
    the final_metrics.json write persists, for EVERY mode including none (a
    full run reports 100.0). The suite PRINTS but does not PERSIST this
    accounting (trainer.py:248-288 @ v1.2.1 — _guard_trainable_ratio
    computes and discards it), so run_finetune owns the record value the
    frontier table needs; nothing between the ctor and the computation
    gates on peft_mode (a guard would starve the method=none rows)."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    ctor_idx = statement_index(src, "trainer = DNATrainer(")
    assert ctor_idx != -1, "no DNATrainer ctor call site found"
    trainable_idx = statement_index(src, "trainable_params = sum(")
    assert trainable_idx != -1, (
        "no trainable_params computation — the frontier table's "
        "trainable_params_pct column has no producer without it"
    )
    total_idx = statement_index(src, "total_params = sum(")
    pct_idx = statement_index(src, "trainable_params_pct = round(")
    write_idx = src.find('open(outdir + "final_metrics.json", \'w\')')
    assert total_idx != -1, "no total_params computation found"
    assert pct_idx != -1, "no trainable_params_pct derivation found"
    assert write_idx != -1, "no final_metrics.json write found"
    assert ctor_idx < trainable_idx < total_idx < pct_idx < write_idx, (
        "the persistence arithmetic must sit between the DNATrainer ctor "
        "(the model exists, adapter-wrapped under peft) and the "
        "final_metrics.json write it feeds"
    )
    arithmetic = src[trainable_idx:pct_idx + 300]
    assert "trainer.model.parameters()" in arithmetic, (
        "the sums must run over trainer.model.parameters() — the "
        "CONSTRUCTED model (post adapter attach under peft), not the "
        "pre-ctor module"
    )
    assert "p.requires_grad" in arithmetic, (
        "the trainable sum must filter on p.requires_grad"
    )
    pct_stmt = src[pct_idx:pct_idx + 300]
    assert re.search(r",\s*6\s*\)", pct_stmt), (
        "trainable_params_pct must be rounded to 6 decimals"
    )
    write_block = src[write_idx - 500:write_idx + 800]
    for key in ("trainable_params", "total_params", "trainable_params_pct"):
        assert key in write_block, (
            f"{key} must be merged into the metrics payload at the "
            "final_metrics.json write — the sweep copies final_metrics "
            "verbatim into run_record.metrics, so this is the channel the "
            "frontier reader consumes"
        )
    between = src[ctor_idx:trainable_idx]
    assert "if peft_mode" not in between, (
        "the persistence must run for EVERY mode — a peft_mode guard "
        "between the ctor and the computation would leave method=none "
        "records without trainable_params_pct (the frontier's none rows "
        "derive without special cases only if full runs report 100.0)"
    )


def _yaml_section_keys(text, section):
    """The 4-space-indented keys of a top-level ``section:`` YAML block."""
    match = re.search(
        rf"^{re.escape(section)}:\s*\n(.*?)(?=^\S|\Z)", text,
        re.DOTALL | re.MULTILINE,
    )
    assert match is not None, f"no top-level {section}: section found"
    return re.findall(
        r"^\s{4}([A-Za-z_][A-Za-z0-9_]*):", match.group(1), re.MULTILINE
    )


def test_both_finetune_yamls_carry_suite_validated_lora_and_ia3_sections():
    """Every shipped finetune YAML (base, with_head, and the 06-05 variant
    YAMLs as they land) carries a lora: and an ia3: section whose keys
    are EXACTLY the suite-documented fields (dnallm configs.py:400-423
    LoraConfig, :436-478 Ia3Config @ v1.2.1) — no invented fields — with
    r 8 / lora_alpha 16 / target_modules null (suite preset
    auto-selection). The lora: section is REQUIRED whenever use_lora=True
    (trainer.py:421 indexes config[\"lora\"] directly — KeyError without
    it), which is why it must exist in EVERY variant file: a config
    variant reload must never hit KeyError 'lora'."""
    lora_keys_expected = {
        "r", "lora_alpha", "target_modules", "lora_dropout", "bias",
        "task_type",
    }
    ia3_keys_expected = {"target_modules", "feedforward_modules", "task_type"}
    for config_path in FINETUNE_CONFIGS:
        text = config_path.read_text(encoding="utf-8")
        lora_keys = set(_yaml_section_keys(text, "lora"))
        ia3_keys = set(_yaml_section_keys(text, "ia3"))
        assert lora_keys == lora_keys_expected, (
            f"{config_path.name}: lora: section keys {sorted(lora_keys)} "
            f"!= the suite-validated field set {sorted(lora_keys_expected)} "
            "(dnallm configs.py:400-423 @ v1.2.1)"
        )
        assert ia3_keys == ia3_keys_expected, (
            f"{config_path.name}: ia3: section keys {sorted(ia3_keys)} "
            f"!= the suite-validated field set {sorted(ia3_keys_expected)} "
            "(dnallm configs.py:436-478 @ v1.2.1)"
        )
        lora_match = re.search(
            r"^lora:\s*\n(.*?)(?=^\S|\Z)", text, re.DOTALL | re.MULTILINE
        )
        assert lora_match is not None, f"{config_path.name}: no lora: block"
        lora_block = lora_match.group(1)
        assert re.search(
            r"^\s{4}r: 8\s*(?:#.*)?$", lora_block, re.MULTILINE
        ), (
            f"{config_path.name}: lora.r must be the suite default 8"
        )
        assert re.search(
            r"^\s{4}lora_alpha: 16\s*(?:#.*)?$", lora_block, re.MULTILINE
        ), f"{config_path.name}: lora.lora_alpha must be the suite default 16"
        assert re.search(
            r"^\s{4}target_modules: null\s*(?:#.*)?$", lora_block, re.MULTILINE
        ), (
            f"{config_path.name}: lora.target_modules must be null — "
            "the suite resolves its per-family preset (lora_targets.yaml)"
        )


# =====================================================================
# env_smoke v1.2.1 alignment (06-01) — labels, peft check, sanction
# =====================================================================

def test_env_smoke_carries_zero_stale_version_labels():
    """06-01: env_smoke.py carries ZERO stale 'dnallm 0.8.0' labels —
    every version-label string was relabeled to 1.2.1 with its fact
    re-checked against the v1.2.1 pyproject (datasets<=3.2.0 and the
    numpy>=2 floor hold; the 0.8.x-era pyarrow>=15,<26 cap is GONE —
    v1.2.1 declares no pyarrow constraint, so the claim is dropped, not
    relabeled)."""
    src = ENV_SMOKE.read_text(encoding="utf-8")
    assert "0.8.0" not in src, (
        "a stale 'dnallm 0.8.0' version label survives in env_smoke.py — "
        "labels must be relabeled to 1.2.1 with facts re-checked against "
        "the v1.2.1 pyproject"
    )
    assert "1.2.1" in src, "the 1.2.1 relabel is absent entirely"
    assert "pyarrow>=15,<26" not in src, (
        "the 0.8.x-era pyarrow cap claim survived — v1.2.1 declares NO "
        "pyarrow constraint (verified read-only against its pyproject); "
        "the claim must be dropped, not relabeled"
    )


def test_env_smoke_docstring_records_the_smoke_sanction():
    """06-01: the binding docstring contract is AMENDED to record the
    2026-10-11 maintainer smoke sanction with its exact boundary —
    executed smoke permitted as explicit bounded plan TASKS on this GB10
    host, py_compile no longer the only sanctioned agent-side proof, E2'
    full sweep still maintainer dual-gate, CI still GPU-free. Without
    the amendment a future agent treats execution as out-of-contract
    (Pitfall 7)."""
    docstring = ENV_SMOKE.read_text(encoding="utf-8")[:4200]
    assert "2026-10-11" in docstring and "sanction" in docstring.lower(), (
        "the module docstring must record the 2026-10-11 smoke sanction"
    )
    assert "bounded" in docstring.lower(), (
        "the sanction record must state the bounded-plan-TASKS boundary"
    )
    assert "dual" in docstring.lower() and "gate" in docstring.lower(), (
        "the sanction record must keep E2' maintainer dual-gate explicit"
    )
    assert "GPU-free" in docstring, (
        "the sanction record must keep CI GPU-free explicit"
    )


def test_env_smoke_peft_check_is_gating():
    """06-01: a peft import+version check joins the PASS/FAIL surface and
    is wired into main()'s results — any FAIL forces the final non-zero
    exit like every other check (the SC-6 lanes build on peft; the suite
    hard-imports it at trainer.py:58 @ v1.2.1)."""
    src = ENV_SMOKE.read_text(encoding="utf-8")
    check_match = re.search(r"^def check_peft\(\):", src, re.MULTILINE)
    assert check_match is not None, (
        "no check_peft() function — the lanes depend on peft being "
        "importable and the smoke gate must say so"
    )
    body = src[check_match.start():check_match.start() + 900]
    assert "FAIL" in body and "PASS" in body, (
        "check_peft must print a greppable PASS/FAIL line like every "
        "other check"
    )
    assert "__version__" in body, (
        "check_peft must print the installed peft version"
    )
    wiring = re.search(r"^(\s*)results\.append\(check_peft\(\)\)", src, re.MULTILINE)
    assert wiring is not None, (
        "main() never appends check_peft()'s result — the check would "
        "print without gating the exit code"
    )
    main_idx = src.find("def main():")
    assert main_idx != -1 and wiring.start() > main_idx, (
        "the check_peft wiring must sit inside main()"
    )


# =====================================================================
# --config-variant mechanism + frozen probe (06-05, SC-6 / REV-05 F4)
# =====================================================================

def test_config_variant_flag_declared_with_choices_and_none_default():
    """--config-variant is an argparse choices flag (head/probe/curve)
    defaulting to None — the absent-variant path keeps the base config
    plus the special_models auto-reload (the byte-identical default)."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    idx = src.find('"--config-variant"')
    assert idx != -1, (
        "no --config-variant argument in parse_args() — the frozen-probe "
        "lane is not expressible from the CLI (SC-6/REV-05 F4, 06-05)"
    )
    block = src[idx:idx + 1200]
    assert 'choices=["head", "probe", "curve"]' in block, (
        "--config-variant must be choices=[head, probe, curve] (argparse "
        "rejects any other variant at the argv boundary)"
    )
    assert re.search(r"default=None", block), (
        "--config-variant must default to None — an absent variant keeps "
        "the base config + the special_models auto-reload byte-identical"
    )


def test_variant_config_registry_maps_choices_to_real_files():
    """The module-level VARIANT_CONFIGS mapping resolves every choice to a
    YAML: head maps to today's with_head file (the explicit form of the
    implicit special_models behavior — any model can request the custom-
    head config), probe/curve to this plan's variant files. Every mapping
    is a real file on disk for the variants shipped so far (head + probe
    in Task 1; curve lands with the learning-curve lane in Task 2)."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    match = re.search(r"VARIANT_CONFIGS = \{(.*?)\}", src, re.DOTALL)
    assert match is not None, (
        "no module-level VARIANT_CONFIGS mapping — the variant reload has "
        "no file resolution"
    )
    entries = dict(re.findall(r'"([^"]+)":\s*"([^"]+)"', match.group(1)))
    assert set(entries) == {"head", "probe", "curve"}, (
        f"VARIANT_CONFIGS keys must be exactly the --config-variant "
        f"choices (got {sorted(entries)})"
    )
    assert entries.get("head") == "./finetune_config_with_head.yaml", (
        "the head variant must map to today's with_head file — the "
        "explicit form of the implicit special_models behavior"
    )
    assert entries.get("probe") == "./finetune_config_probe.yaml"
    assert entries.get("curve") == "./finetune_config_curve.yaml"
    # Module level: defined OUTSIDE the __main__ block (referenced by the
    # in-loop reload and testable as a contract surface).
    assert src.find("VARIANT_CONFIGS = {") < src.find(
        'if __name__ == "__main__":'
    ), "VARIANT_CONFIGS must be a module-level mapping"
    for variant in ("head", "probe"):
        assert (REPO_ROOT / "pipeline" / Path(entries[variant]).name).is_file(), (
            f"the {variant} variant's YAML {entries[variant]} does not "
            "exist on disk — the variant reload would crash at load_config"
        )


def test_variant_reload_occupies_the_special_models_slot_before_snapshot():
    """The variant reload sits at the exact in-loop slot the special_models
    reload occupies: AFTER the per-model base reload, BEFORE the unchanged
    special_models membership branch (which still overrides for its own
    members — the byte-identical default), and BEFORE the D-11 grad_accum
    snapshot, so the ACTIVE config's values govern the snapshot. The
    special_models branch itself is pinned verbatim."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    guarded = re.search(
        r"if config_variant is not None:\s*\n"
        r"[^\S\n]*configs = load_config\(VARIANT_CONFIGS\[config_variant\]\)",
        src,
    )
    assert guarded is not None, (
        'no "if config_variant is not None: configs = '
        'load_config(VARIANT_CONFIGS[config_variant])" reload — the '
        "variant mechanism must occupy the special_models reload slot for "
        "ANY model (06-05)"
    )
    base_idx = src.find('load_config("./finetune_config.yaml")')
    special_idx = src.find('model_name in ["evo2_1b_base", "megaDNA_updated"]')
    snapshot_idx = src.find("default_grad_accum = configs")
    assert -1 < base_idx < guarded.start(), (
        "the variant reload must sit AFTER the per-model base reload "
        "(D-11: the variant overrides a fresh base, never a stale one)"
    )
    assert guarded.start() < special_idx, (
        "the variant reload must sit BEFORE the special_models branch — "
        "special models keep their own (overriding) reload, so their "
        "behavior is unchanged under any variant"
    )
    assert special_idx < snapshot_idx, (
        "the D-11 grad_accum snapshot must stay AFTER every config "
        "reload — it snapshots whichever config is actually active"
    )
    special_branch = re.search(
        r'if model_name in \["evo2_1b_base", "megaDNA_updated"\]:\s*\n'
        r'[^\S\n]*configs = load_config\("\./finetune_config_with_head'
        r'\.yaml"\)\s*\n'
        r"[^\S\n]*configs\['task'\]\.head_config\.head = model_name"
        r'\.lower\(\)\.split\("_"\)\[0\]',
        src,
    )
    assert special_branch is not None, (
        "the special_models auto-reload branch must stay byte-identical "
        "(the unchanged default; --config-variant is purely additive)"
    )


def test_probe_ineligible_list_covers_special_loader_families_with_provenance():
    """The module-level PROBE_INELIGIBLE list is the enforced scope
    boundary of the frozen-probe lane: the deeplearning_models four, the
    special_models two, and the two remaining dedicated special-loader
    registry families (gpn, omnidna — evo1 has no registry members).
    Every member is a real registry key and every entry line carries a
    one-line provenance comment naming its special loader."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    match = re.search(r"PROBE_INELIGIBLE = \[(.*?)\]", src, re.DOTALL)
    assert match is not None, (
        "no module-level PROBE_INELIGIBLE list — the probe lane's scope "
        "boundary is not enforced (T-06-16)"
    )
    assert src.find("PROBE_INELIGIBLE = [") < src.find(
        'if __name__ == "__main__":'
    ), "PROBE_INELIGIBLE must be a module-level list"
    block = match.group(1)
    members = re.findall(r'"([^"]+)"', block)
    assert set(members) == {
        "enformer-official-rough", "space",
        "borzoi-replicate-0", "flashzoi-replicate-0",
        "evo2_1b_base", "megaDNA_updated",
        "gpn-brassicales", "Omni-DNA-700M",
    }, (
        "PROBE_INELIGIBLE must be exactly the deeplearning four + the "
        "special_models pair + the gpn/omnidna dedicated-loader registry "
        f"members (got {sorted(members)})"
    )
    assert set(list_members(src, "deeplearning_models")) <= set(members), (
        "every deeplearning_models member must be probe-ineligible — "
        "their dedicated loaders bypass the generic head path"
    )
    assert {"evo2_1b_base", "megaDNA_updated"} <= set(members)
    unresolved = [n for n in members if n not in registry_keys()]
    assert not unresolved, (
        f"PROBE_INELIGIBLE members not in the unified registry: "
        f"{unresolved} (D-10 name authority)"
    )
    entry_lines = [ln for ln in block.splitlines() if '"' in ln]
    assert entry_lines and all("#" in ln for ln in entry_lines), (
        "every PROBE_INELIGIBLE member carries a one-line provenance "
        "comment naming its suite special loader (model.py:1169-1228 "
        "families)"
    )


def test_probe_ineligibility_guard_fails_fast_before_model_loop():
    """--config-variant probe refuses ineligible models at the argv
    boundary with an [Error] message naming the model(s) and disclosing
    the special-loader reason (the suite dispatches them before the
    generic head_config routing, so the frozen field never applies) —
    BEFORE any model load or loop iteration."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    guard_idx = src.find('if config_variant == "probe":')
    assert guard_idx != -1, (
        "no probe ineligibility guard — a probe run against a "
        "special-loader model would silently train an unfrozen model "
        "under a +probe dir (T-06-16)"
    )
    error_idx = src.find("[Error] --config-variant probe")
    assert error_idx != -1, (
        "the guard's fail-fast must carry an [Error] --config-variant "
        "probe message"
    )
    model_loop_idx = src.find("models_info.items():")
    assert guard_idx < model_loop_idx, (
        "the guard must run BEFORE the model loop — an argv-boundary "
        "fail-fast, never discovered mid-sweep after a model load"
    )
    guard_block = src[guard_idx:guard_idx + 900]
    assert "PROBE_INELIGIBLE" in guard_block, (
        "the guard must resolve its hits against the PROBE_INELIGIBLE list"
    )
    assert "target_model" in guard_block, (
        "the guard must honor an explicit --target_model (and refuse the "
        "full-registry run too when any member is ineligible)"
    )
    message = src[error_idx:error_idx + 600]
    assert "special loader" in message, (
        "the refusal must disclose the special-loader boundary as the reason"
    )
    assert "model.py:1169-1228" in message, (
        "the refusal must cite the suite special-dispatch anchor "
        "(model.py:1169-1228 @ v1.2.1)"
    )
    assert "head_config" in message, (
        "the refusal must say WHY the probe cannot apply (the generic "
        "head_config routing these loaders bypass)"
    )


def test_probe_alias_defaults_only_for_the_probe_variant():
    """--config-variant probe with NO explicit --save_model_name defaults
    the save name to {model}+probe — the 06-02 alias seam applied to the
    probe variant ONLY (head/curve do not alias); an explicit
    --save_model_name still wins (first branch), and the chain still ends
    at the bare base name for the no-peft/no-variant default."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    chain = re.search(
        r'if save_model_name:\s*\n'
        r'[^\S\n]*model_save_name = save_model_name\s*\n'
        r'[^\S\n]*elif peft_mode != "none":\s*\n'
        r'[^\S\n]*model_save_name = f"\{model_name\}\+\{peft_mode\}"\s*\n'
        r'[^\S\n]*elif config_variant == "probe":\s*\n'
        r'[^\S\n]*model_save_name = f"\{model_name\}\+probe"\s*\n'
        r"[^\S\n]*else:\s*\n"
        r"[^\S\n]*model_save_name = model_name",
        src,
    )
    assert chain is not None, (
        "the save-name resolution must carry the probe alias branch — "
        "a probe run without an explicit --save_model_name must default "
        "to {model}+probe or it would share the base run's output dir "
        "AND resume marker (Pitfall 3)"
    )
    assert src.count("elif config_variant ==") == 1, (
        "only the probe variant aliases the save name — head/curve must "
        "not gain alias branches"
    )
    assert 'f"{model_name}+head"' not in src, "head must not alias"
    assert 'f"{model_name}+curve"' not in src, "curve must not alias"


def test_probe_yaml_carries_the_frozen_mlp_head_block():
    """pipeline/finetune_config_probe.yaml is the with_head head block with
    head \"mlp\", frozen: true, hidden_dims [512] inside task.head_config —
    using ONLY keys present in finetune_config_with_head.yaml plus the
    suite's frozen field (dnallm configs.py:14-17 HeadConfig.frozen; the
    freeze loop that executes it at model.py:101-103), with a provenance
    comment citing both suite anchors."""
    text = PROBE_CONFIG.read_text(encoding="utf-8")
    with_head_text = WITH_HEAD_CONFIG.read_text(encoding="utf-8")

    def head_block_of(yaml_text, name):
        block = re.search(
            r"^\s{4}head_config:\s*(?:#[^\n]*)?\n(.*?)(?=^\s{0,4}\S)",
            yaml_text, re.DOTALL | re.MULTILINE,
        )
        assert block is not None, f"no task.head_config block in {name}"
        return block.group(1)

    probe_block = head_block_of(text, "finetune_config_probe.yaml")
    assert re.search(r'^\s{8}head: "mlp"', probe_block, re.MULTILINE), (
        'the probe head_config must set head: "mlp"'
    )
    assert re.search(r"^\s{8}frozen: true\b", probe_block, re.MULTILINE), (
        "the probe head_config must set frozen: true — the suite field "
        "that freezes the backbone (configs.py:14-17; model.py:101-103)"
    )
    assert re.search(r"^\s{8}hidden_dims: \[512\]", probe_block,
                     re.MULTILINE), (
        "the probe head must use the single-dim [512] hidden layer"
    )
    with_head_block = head_block_of(with_head_text,
                                    "finetune_config_with_head.yaml")

    def head_keys(block):
        return set(re.findall(r"^\s{8}([A-Za-z_][A-Za-z0-9_]*):", block,
                              re.MULTILINE))

    expected_keys = head_keys(with_head_block) | {"frozen"}
    assert head_keys(probe_block) == expected_keys, (
        "the probe head_config key surface must be exactly with_head's "
        f"keys plus frozen (got {sorted(head_keys(probe_block))} vs "
        f"{sorted(expected_keys)}) — no invented fields"
    )
    assert "configs.py" in text and "model.py" in text, (
        "the probe YAML must cite the suite anchors (configs.py:14-17 "
        "frozen field; model.py:101-103 freeze loop) as provenance"
    )


def test_per_dataset_head_config_task_type_assignment_untouched():
    """The per-dataset head_config.task_type assignment (the :718-719
    region) is untouched by the variant mechanism: guarded only by the
    config's own head_config presence, never by the variant flag — it
    keeps working for every variant that carries a head_config (the
    special_models auto-reload before, the probe variant now)."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    assignment = re.search(
        r'if "head_config" in configs\[\'task\'\]:\s*\n'
        r"[^\S\n]*configs\['task'\]\.head_config\.task_type = row\[\"type\"\]",
        src,
    )
    assert assignment is not None, (
        'no \'if "head_config" in configs[\'task\']: ... task_type = '
        'row["type"]\' assignment — the per-dataset head task_type wiring '
        "is gone (every head-carrying variant breaks)"
    )
    plain_idx = statement_index(src, 'configs["task"].task_type = row["type"]')
    assert plain_idx != -1 and plain_idx < assignment.start(), (
        "the head_config.task_type assignment must sit in the per-dataset "
        "task-config block, right after the plain task_type assignment"
    )
    preceding = src[max(0, assignment.start() - 200):assignment.start()]
    assert "config_variant" not in preceding, (
        "the assignment must not be conditioned on the variant flag — it "
        "applies to every head-carrying config alike"
    )


# =====================================================================
# --train_fraction (06-05, SC-6 / REV-08 F8 learning-curve lane)
# =====================================================================

def test_train_fraction_flag_shape_and_seed_governed_semantics():
    """--train_fraction is a float flag defaulting to None whose help
    documents the A5 decision: the train split is shuffled with the run
    seed then the first int(n * f) rows kept — fraction variance is
    SEED-GOVERNED; plain first-N (selection without a shuffle) is
    explicitly NOT the semantics."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    idx = src.find('"--train_fraction"')
    assert idx != -1, (
        "no --train_fraction argument in parse_args() — the curve lane "
        "cannot subset the train split (REV-08/F8, 06-05)"
    )
    block = src[idx:idx + 1600]
    assert re.search(r"type=float", block), (
        "--train_fraction must be type=float"
    )
    assert re.search(r"default=None", block), (
        "--train_fraction must default to None — an absent flag means the "
        "full train split (byte-identical code path)"
    )
    lowered = block.lower()
    assert "seed" in lowered and "shuffle" in lowered, (
        "the help must document the seed-governed shuffle-then-select "
        "semantics (research A5)"
    )
    assert "first-n" in lowered, (
        "the help must state that plain first-N is explicitly NOT the "
        "semantics (the A5 decision, disclosed)"
    )
    assert "train" in lowered, (
        "the help must say the fraction applies to the TRAIN split only"
    )


def test_train_fraction_validator_rejects_out_of_bounds():
    """The pure validator accepts (0, 1] and rejects f <= 0 and f > 1 with
    a problem naming the bound; None (absent flag) is vacuously valid."""
    validate, _apply = extract_fraction_fns()
    assert validate(None) == []
    for good in (0.25, 0.5, 0.75, 1.0):
        assert validate(good) == [], f"{good} must be a valid fraction"
    for bad in (0.0, -0.5, 1.5, 2.0):
        problems = validate(bad)
        assert problems, f"{bad} must be rejected"
        assert "(0, 1]" in problems[0], (
            "the problem must name the valid bound (0, 1]"
        )


def test_train_fraction_fail_fast_at_argv_boundary():
    """The __main__ wiring validates the fraction and exits non-zero with
    an [Error] message listing the collected problems — before the model
    loop (the --subset_file / _validate_filters discipline)."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    wiring_idx = statement_index(
        src, "fraction_problems = validate_train_fraction(train_fraction)"
    )
    assert wiring_idx != -1, (
        "no validate_train_fraction call in the __main__ wiring — a bad "
        "--train_fraction would be applied unvalidated"
    )
    assert "[Error] invalid --train_fraction" in src, (
        "the fail-fast exit must carry an [Error] invalid "
        "--train_fraction message"
    )
    model_loop_idx = src.find("models_info.items():")
    assert wiring_idx < model_loop_idx, (
        "the fraction validation must run BEFORE the model loop"
    )


def test_apply_train_fraction_train_only_seed_governed():
    """The apply seam composes the train split as
    shuffle(seed=<run seed>).select(range(int(n * f))) — TRAIN SPLIT ONLY:
    dev and test are never shuffled or selected (the eval-invariance
    guarantee: test rows identical across fractions and models, so curve
    points are comparable)."""
    _validate, apply_fn = extract_fraction_fns()
    train, dev, test = ShuffleSplit(100), ShuffleSplit(80), ShuffleSplit(60)
    holder = {"train": train, "dev": dev, "test": test}
    apply_fn(holder, 0.25, 9527)
    assert train.shuffle_calls == [(9527, 100)], (
        "the train split must be shuffled with the RUN seed (A5: fraction "
        "variance is seed-governed)"
    )
    assert train.select_calls == [list(range(25))], (
        "the selection must keep exactly int(n * f) rows "
        "(int(100 * 0.25) = 25)"
    )
    assert dev.shuffle_calls == [] and dev.select_calls == [], (
        "dev must NEVER be touched by the fraction path — dev drives "
        "checkpoint selection and must stay full"
    )
    assert test.shuffle_calls == [] and test.select_calls == [], (
        "test must NEVER be touched by the fraction path — the "
        "eval_subsets discipline keeps test rows identical across "
        "fractions and models (the comparability guarantee)"
    )
    # f = 1.0 keeps the full split (int(n * 1.0) rows).
    full_train = ShuffleSplit(50)
    apply_fn({"train": full_train}, 1.0, 42)
    assert full_train.select_calls == [list(range(50))]


def test_apply_train_fraction_absent_flag_is_noop():
    """Absent flag (None): zero shuffle/select calls anywhere — the code
    path is identical to today."""
    _validate, apply_fn = extract_fraction_fns()
    splits = {name: ShuffleSplit() for name in ("train", "dev", "test")}
    apply_fn(splits, None, 9527)
    for split in splits.values():
        assert split.shuffle_calls == []
        assert split.select_calls == []


def test_train_fraction_seam_sits_between_load_and_validate():
    """The fraction apply seam is wired between the
    DNADataset.load_local_data call and dataset.validate_sequences — the
    same slot as apply_eval_subset, so the subsetted split is what gets
    validated and encoded."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    load_idx = statement_index(src, "dataset = DNADataset.load_local_data(")
    assert load_idx != -1, "no DNADataset.load_local_data call site found"
    apply_idx = statement_index(
        src, "apply_train_fraction(dataset.dataset, train_fraction, seed)"
    )
    assert apply_idx != -1, (
        "no apply_train_fraction(dataset.dataset, ...) wiring — the seam "
        "exists but is never invoked at the load/validate boundary"
    )
    validate_idx = statement_index(src, "dataset.validate_sequences(")
    assert validate_idx != -1, "no validate_sequences call site found"
    assert load_idx < apply_idx < validate_idx, (
        "the fraction select must sit AFTER the dataset load and BEFORE "
        f"validate_sequences (load {load_idx}, apply {apply_idx}, "
        f"validate {validate_idx})"
    )


def test_frac_segment_nests_under_seed_in_default_outdir():
    """With --train_fraction given, the default output composition nests
    frac_{f} UNDER the seed dir — never a sibling — and the
    trainer_state.json resume check that follows is therefore
    (model, task, seed, fraction)-scoped: a full run's marker in
    seed_{s}/ never skips a fraction cell and vice versa."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    outdir_idx = src.find(
        'f"{save_root}/{model_save_name}/{dataset_name}/seed_{seed}/"'
    )
    assert outdir_idx != -1, "the seed-isolated outdir f-string is gone"
    frac_idx = statement_index(
        src, "outdir = f\"{outdir}frac_{train_fraction}/\""
    )
    assert frac_idx != -1, (
        "no frac_{train_fraction} nesting append — a fraction run would "
        "collide with the full run's output dir AND resume marker "
        "(T-06-15)"
    )
    resume_idx = src.find('os.path.exists(outdir + "trainer_state.json")')
    assert resume_idx != -1, "no trainer_state.json resume check found"
    assert outdir_idx < frac_idx < resume_idx, (
        "the frac segment must be appended to the seed dir BEFORE the "
        "resume check reads it — the marker must be fraction-scoped "
        f"(outdir {outdir_idx}, frac {frac_idx}, resume {resume_idx})"
    )


def test_fraction_scales_step_cadence_num_train_data():
    """The dynamic logging/eval/save step calculation uses the
    FRACTION-SCALED train count (int(Train * f)) under the fraction
    guard — otherwise a 0.25 cell's computed cadence would be 4x sparser
    than the actual step count and the learning-curve points would not
    be dense (the lane's whole purpose). Absent fraction: the registry
    Train count, byte-identical to today."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    read_idx = statement_index(
        src, 'num_train_data = int(row["Train"])'
    )
    assert read_idx != -1, "no num_train_data read found"
    guarded = re.search(
        r"if train_fraction is not None:\s*\n"
        r"[^\S\n]*num_train_data = int\(num_train_data \* train_fraction\)",
        src,
    )
    assert guarded is not None, (
        "no fraction-guarded num_train_data rescale — the step-cadence "
        "calculation would use the full registry count for a fraction "
        "cell, making curve checkpoints sparse"
    )
    step_idx = statement_index(
        src, "step = num_train_data * epoch // (bs_new * grad_accum * num_gpus * 10)"
    )
    assert step_idx != -1, "no step cadence calculation found"
    assert read_idx < guarded.start() < step_idx, (
        "the rescale must sit between the registry read and the step "
        "calculation that consumes it"
    )
