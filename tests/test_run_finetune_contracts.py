"""
Source-contract tests for ``pipeline/run_finetune.py`` (F1 / REV-01).

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

See also:
    ``script/make_dev_splits.py`` — the remediation the guard names.
    ``tests/test_known_defects.py`` — the read-source-never-import
    rationale's origin.
"""

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
