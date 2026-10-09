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
- **grad_accum reset per dataset (D-07)** — the YAML-default
  ``default_grad_accum`` snapshot (taken right after the per-model base
  reload) must be restored at the top of the dataset loop, BEFORE the
  adjustment block reads ``gradient_accumulation_steps`` — a per-task
  grad_accum from dataset A must never persist into dataset B.

See also:
    ``script/make_dev_splits.py`` — the remediation the guard names.
    ``tests/test_known_defects.py`` — the read-source-never-import
    rationale's origin.
    ``tests/test_sweep.py`` — the sweep runner whose subprocesses rely
    on this seed-isolated layout contract.
"""

from pathlib import Path
import re

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
    """D-07: default_grad_accum is snapshotted after the per-model base
    reload and restored inside the dataset loop BEFORE the adjustment
    block reads gradient_accumulation_steps — a per-task grad_accum from
    dataset A never persists into dataset B."""
    src = RUN_FINETUNE.read_text(encoding="utf-8")
    snapshot_idx = src.find("default_grad_accum = configs")
    assert snapshot_idx != -1, (
        "no default_grad_accum snapshot after the per-model base reload "
        "(D-07) — the per-dataset reset needs the YAML default captured "
        "before any dataset can mutate it"
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
