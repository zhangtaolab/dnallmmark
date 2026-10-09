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

See also:
    ``script/make_dev_splits.py`` — the remediation the guard names.
    ``tests/test_known_defects.py`` — the read-source-never-import
    rationale's origin.
    ``tests/test_sweep.py`` — the sweep runner whose subprocesses rely
    on this seed-isolated layout contract.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_FINETUNE = REPO_ROOT / "pipeline" / "run_finetune.py"
FINETUNE_CONFIGS = [
    REPO_ROOT / "pipeline" / "finetune_config.yaml",
    REPO_ROOT / "pipeline" / "finetune_config_with_head.yaml",
]


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
    legacy = (REPO_ROOT / "pipeline" / "dnallmmark_pipeline.py").read_text(
        encoding="utf-8")

    def list_members(src, name):
        match = re.search(rf"{name} = \[(.*?)\]", src, re.DOTALL)
        assert match is not None, f"no {name} = [...] list found in source"
        return re.findall(r'"([^"]+)"', match.group(1))

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
