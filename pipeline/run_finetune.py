import os
import sys


def _peek_cache_dir():
    """Extract --cache_dir from argv before argparse runs.

    HF_HOME must be set before huggingface_hub is imported (its constants
    are evaluated at import time), but --cache_dir is a CLI flag parsed by
    argparse later. This pre-scan bridges that ordering gap.
    """
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--cache_dir" and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith("--cache_dir="):
            return a.split("=", 1)[1]
    return None


# Resolve cache dir: --cache_dir flag > existing HF_HOME env > default ../../cache
_cache_dir = _peek_cache_dir()
if _cache_dir:
    os.environ["HF_HOME"] = _cache_dir
    os.environ["MS_CACHE_HOME"] = _cache_dir
elif "HF_HOME" not in os.environ:
    _default_cache = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "cache")
    )
    os.environ.setdefault("HF_HOME", _default_cache)
    os.environ.setdefault("MS_CACHE_HOME", _default_cache)

import argparse
import datetime
import importlib
import json
import shutil
from glob import glob
from pathlib import Path

import numpy as np
import torch
from torch import nn

# Import torch_npu for Huawei Ascend NPU support. Imported for its
# registration side effect (importing it makes torch.npu exist); the
# module object itself is never referenced, hence importlib.
try:
    importlib.import_module("torch_npu")
    NPU_AVAILABLE = torch.npu.is_available()
except ImportError:
    NPU_AVAILABLE = False

from dnallm import DNADataset, DNATrainer, load_config, load_model_and_tokenizer


def parse_args():
    parser = argparse.ArgumentParser(description="DNA LLM Arena")

    parser.add_argument(
        "--target_model",
        type=str,
        default=None,
        help="Name of the target model for training"
    )

    parser.add_argument(
        "--target_dataset",
        type=str,
        default=None,
        help="Name of the target dataset for training"
    )

    parser.add_argument(
        "--batch_size",
        type=int,
        default=1,
        help="Manual batch size"
    )

    parser.add_argument(
        "--max_token_len",
        type=int,
        default=None,
        help="Manual max token length in case model with singlebase tokenizer processing extra-long sequences"
    )

    parser.add_argument(
        "--remove_pt",
        action="store_true",
        default=False,
        help="If set, remove .pt files in checkpoints"
    )

    parser.add_argument(
        "--remove_checkpoints",
        action="store_true",
        default=False,
        help="If set, remove the all checkpoints directory except the last one"
    )

    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Filter datasets by category, supports multiple categories separated by comma (e.g., Plants,Animals,Microbe)"
    )

    parser.add_argument(
        "--task_index",
        type=str,
        default=None,
        help="Filter datasets by index number from datasets_info.json, supports multiple indices separated by comma (e.g., 1,2,7,10)"
    )

    parser.add_argument(
        "--auto_batch_size",
        action="store_true",
        default=False,
        help="If set, automatically adjust batch size based on model size"
    )

    parser.add_argument(
        "--gradient_checkpointing",
        action="store_true",
        default=False,
        help="If set, enable HF gradient checkpointing to trade compute for memory"
    )

    parser.add_argument(
        "--ddp_find_unused_parameters",
        action="store_true",
        default=False,
        help="If set, force DDP find_unused_parameters=True. Required for MoE models under torchrun"
    )

    parser.add_argument(
        "--cache_dir",
        type=str,
        default=None,
        help="Cache directory for HF_HOME and MS_CACHE_HOME. "
             "Overrides env vars. Default: ../../cache relative to this script (or HF_HOME env if set)."
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=9527,
        help="Random seed"
    )

    parser.add_argument(
        "--gpu_memory",
        type=float,
        default=None,
        help="Override GPU memory in GB (useful for multi-GPU or incorrect detection)"
    )

    parser.add_argument(
        "--mem_ratio",
        type=float,
        default=0.70,
        help="Target GPU memory usage ratio (0.0-1.0, default 0.70 for 70%%)"
    )

    parser.add_argument(
        "--effective_batch_size",
        type=int,
        default=None,
        help="Target effective batch size (batch_size * gradient_accumulation_steps). If set, gradient_accumulation will be adjusted to achieve this product."
    )

    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="Custom output directory for saving finetuned models (default: ./finetuned)"
    )

    parser.add_argument(
        "--save_model_name",
        type=str,
        default=None,
        help="Custom model name used in output path (default: use Model_name from models_info.json)"
    )

    parser.add_argument(
        "--subset_file",
        type=Path,
        default=None,
        help="JSON file mapping dataset names to lists of test-split row IDs "
             "(the N audit's pipeline/eval_subsets.json); the TEST split is "
             "restricted to those rows before validation so every model "
             "evaluates an identical sample count. Absent = full evaluation"
    )

    parser.add_argument(
        "--peft",
        type=str,
        default="none",
        choices=["none", "lora", "ia3"],
        help="Parameter-efficient fine-tuning mode (SC-6 lane tracer): "
             "'lora' passes use_lora=True to the DNATrainer ctor (the lora: "
             "YAML section is REQUIRED then — the suite indexes "
             "config['lora'] directly); 'ia3' sets finetune.use_ia3=True "
             "(the ia3: YAML section is optional — suite defaults + "
             "presets); 'none' (default) leaves the run surface unchanged"
    )

    parser.add_argument(
        "--num_train_epochs",
        type=int,
        default=None,
        help="Override the loaded config's finetune num_train_epochs (the "
             "bounded-smoke knob: 06-02's 1-epoch LoRA smoke and 06-05's "
             "probe smoke). Absent = the YAML value governs"
    )

    parser.add_argument(
        "--peft_dry_run",
        action="store_true",
        help="Validate-and-exit (requires --peft lora or --peft ia3): the "
             "suite resolves the adapter config, matches target_modules "
             "against the live model, prints the dry-run report and "
             "performs NO training"
    )

    parser.add_argument(
        "--config-variant",
        type=str,
        default=None,
        choices=["head", "probe", "curve"],
        help="Config variant YAML loaded at the special_models reload "
             "slot for ANY model (SC-6 lanes, 06-05): 'head' = "
             "finetune_config_with_head.yaml (the explicit form of the "
             "implicit evo2/megaDNA auto-reload; aliases the save name to "
             "{model}+head for GENERIC models so a custom-head run never "
             "collides with the base run's dir/marker — the special pair "
             "keeps the base name, their with-head config IS their base "
             "config), 'probe' = finetune_config_probe.yaml (frozen "
             "backbone, trained MLP head — generic-path models ONLY, "
             "special-loader models are refused, and --peft is refused: "
             "adapters-on-frozen is a different experiment; defaults the "
             "save name to {model}+probe), 'curve' = "
             "finetune_config_curve.yaml (dense checkpoint cadence for "
             "learning curves; defaults the save name to {model}+curve "
             "so a curve-cadence run never collides with a base run). "
             "Absent = the base config with the "
             "special_models auto-reload unchanged (byte-identical "
             "default)"
    )

    parser.add_argument(
        "--train_fraction",
        type=float,
        default=None,
        help="Restrict the TRAIN split to a fraction of its rows (SC-6 "
             "learning curves, 06-05): the split is shuffled with the run "
             "--seed then the first int(n * f) rows kept — fraction "
             "variance is SEED-GOVERNED (research A5: selection without "
             "a shuffle — plain first-N — is explicitly NOT the "
             "semantics, it would couple the fraction to registry row "
             "order). TRAIN SPLIT ONLY: dev/test are untouched, so the "
             "eval_subsets discipline keeps test rows identical across "
             "fractions and models (the comparability guarantee the "
             "curve lane exists for). f must satisfy 0 < f <= 1. The "
             "output composition nests .../seed_{seed}/frac_{f}/ so "
             "fraction runs never collide with full runs. Absent = the "
             "full train split (byte-identical code path)"
    )

    args = parser.parse_args()
    return args


def validate_subset_file(subset_path, datasets_info):
    """Load and fail-fast validate a ``--subset_file`` map (F7 Q3).

    Mirrors ``run_sweep._validate_filters``: every problem is collected
    before the caller exits non-zero, so one run reports ALL malformed
    classes at once (a bad map must abort loudly, never silently no-op
    an evaluation). Checks: the file is readable JSON; the top level is
    an object; every key is a ``datasets_info.json`` key; every key's
    registry row carries a ``Dataset_name`` coincident with the key (the
    map is joined on registry KEYS here but resolved via ``Dataset_name``
    at the apply seam — a divergent row would silently no-op that task's
    subset, so divergence is refused up front); every value is a list of
    integers; every integer is within ``[0, Test)`` for its task
    (``Test`` is the registry's test-split row count, disk-verified by
    ``script/make_dev_splits.py --check``).

    Args:
        subset_path (Path): The ``--subset_file`` path.
        datasets_info (dict): The unified datasets registry.

    Returns:
        tuple: ``(subsets, problems)`` — the loaded map when NO problems
        were found, else ``None``; ``problems`` lists every malformed
        class by name.
    """
    try:
        loaded = json.loads(Path(subset_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, [f"cannot read {subset_path}: {exc}"]
    if not isinstance(loaded, dict):
        return None, [
            (
                f"top-level JSON is {type(loaded).__name__}, expected an "
                "object mapping task names to lists of integer row IDs"
            )
        ]
    problems = []
    unknown = sorted(set(loaded) - set(datasets_info))
    if unknown:
        problems.append(f"task keys not in datasets_info.json: {unknown}")
    for task in sorted(loaded):
        if task not in datasets_info:
            continue
        # Key-space coincidence guard (WR-03, 05 review): the map's keys
        # are registry KEYS here, but the apply seam resolves them via
        # row["Dataset_name"] in the dataset loop. They coincide for all
        # 50 registry rows today; any future divergence would make that
        # task's subset silently no-op (full-split evaluation while the
        # operator believes the unified-N subset is applied), so a row
        # whose Dataset_name differs from its key is refused up front. A
        # row omitting Dataset_name cannot silently diverge — the dataset
        # loop's row["Dataset_name"] lookup would crash the run first.
        registry_name = datasets_info[task].get("Dataset_name", task)
        if registry_name != task:
            problems.append(
                f"{task}: datasets_info.json row has Dataset_name "
                f"{registry_name!r} != registry key {task!r} — the "
                "--subset_file map is keyed on registry keys but applied "
                "by Dataset_name, so this task's subset would silently "
                "no-op"
            )
            continue
        ids = loaded[task]
        if not isinstance(ids, list):
            problems.append(
                f"{task}: value is {type(ids).__name__}, expected a list "
                "of integer row IDs"
            )
            continue
        test_rows = int(datasets_info[task].get("Test") or 0)
        for row_id in ids:
            if isinstance(row_id, bool) or not isinstance(row_id, int):
                problems.append(f"{task}: non-integer ID {row_id!r}")
            elif row_id < 0:
                problems.append(f"{task}: negative ID {row_id}")
            elif row_id >= test_rows:
                problems.append(
                    f"{task}: ID {row_id} out of range [0, {test_rows})"
                )
    return (loaded if not problems else None), problems


def apply_eval_subset(dataset_dict, dataset_name, eval_subsets):
    """Restrict the TEST split to the audited eval-subset rows (F7 Q3).

    Applied between ``DNADataset.load_local_data`` and
    ``validate_sequences`` so the audited IDs are the actually-evaluated
    rows, TEST SPLIT ONLY — train/dev stay full (dev drives checkpoint
    selection, research A4). Uses the wrapped Dataset's ``select``
    primitive (the same call the suite's own ``sampling()`` uses); the
    suite itself is never modified. With no ``--subset_file`` (or no
    entry for this dataset) this is a no-op — the code path is identical
    to today.

    Args:
        dataset_dict (dict): The wrapped ``DatasetDict`` at
            ``dataset.dataset`` (mutated in place on the test split).
        dataset_name (str): The current dataset's registry key.
        eval_subsets (dict | None): The validated subset map (or None).
    """
    if not eval_subsets:
        return
    ids = eval_subsets.get(dataset_name)
    if not ids:
        return
    if "test" in dataset_dict:
        dataset_dict["test"] = dataset_dict["test"].select(ids)


def validate_train_fraction(fraction):
    """Validate a ``--train_fraction`` value (REV-08/F8, 06-05).

    Pure validator mirroring ``validate_subset_file``'s collect-all
    discipline: returns the problem list (empty = valid). Fractions live
    in ``(0, 1]`` — ``f <= 0`` is meaningless and ``f > 1`` is not a
    fraction.

    Args:
        fraction (float | None): the flag value; None (absent flag) is
            vacuously valid.

    Returns:
        list[str]: every problem found (at most one for a scalar).
    """
    if fraction is None:
        return []
    if fraction <= 0 or fraction > 1:
        return [f"{fraction!r} is outside (0, 1]"]
    return []


def apply_train_fraction(dataset_dict, fraction, seed):
    """Restrict the TRAIN split to a fraction of its rows (REV-08/F8).

    Seed-governed shuffle-then-select (research A5): the split is
    shuffled with the RUN seed then the first ``int(n * f)`` rows kept,
    so fraction variance is governed by the seed — plain first-N
    (selection without a shuffle) is explicitly NOT the semantics; it
    would couple the fraction to registry row order. TRAIN SPLIT ONLY:
    dev and test are never touched (dev drives checkpoint selection; the
    eval_subsets discipline keeps test rows identical across fractions
    and models — the comparability guarantee the learning-curve lane
    exists for). With no fraction this is a no-op — the code path is
    identical to today.

    Args:
        dataset_dict (dict): The wrapped ``DatasetDict`` at
            ``dataset.dataset`` (mutated in place on the train split).
        fraction (float | None): The ``--train_fraction`` value
            (None = no-op).
        seed (int): The run's ``--seed``, governing the shuffle.
    """
    if fraction is None:
        return
    if "train" in dataset_dict:
        train = dataset_dict["train"]
        n = len(train)
        dataset_dict["train"] = train.shuffle(seed=seed).select(
            range(int(n * fraction))
        )


# Config-variant YAML resolution (SC-6 lanes, 06-05): each
# --config-variant choice names the YAML loaded at the special_models
# reload slot inside the model loop. "head" maps to today's with_head
# file — --config-variant head is the explicit form of the implicit
# special_models behavior (any model can request the custom-head
# config); "probe"/"curve" are the 06-05 lane variants.
VARIANT_CONFIGS = {
    "head": "./finetune_config_with_head.yaml",
    "probe": "./finetune_config_probe.yaml",
    "curve": "./finetune_config_curve.yaml",
}

# Probe-ineligible models (SC-6/REV-05 F4, 06-05): --config-variant probe
# is refused for these names — the suite's load_model_and_tokenizer
# dispatches each to a dedicated special loader (dnallm/models/model.py
# L1169-1228 @ v1.2.1 (30dfd6d)) that returns BEFORE the generic
# head_config routing (model.py L600-615), so task.head_config.frozen
# (the HeadConfig field at configs.py L14-17; the freeze loop runs at
# model.py L101-103) never reaches them and a probe run would silently
# train an unfrozen model under a +probe dir. One provenance comment per
# member (the suite special/ module each family dispatches to). The space
# family needs BOTH registry spellings (HI-01, phase-06 review): the
# registry carries two distinct rows — uppercase ``SPACE`` (Model_path
# ``models/SPACE``) and lowercase ``space`` (``models/space``) — and the
# suite's space dispatch claims each separately: the native
# ``space_models = ["SPACE"]`` member matches the uppercase row's path
# case-sensitively (``"SPACE" in ".../models/SPACE"``, special/space.py
# substring loop), while the lowercase row is claimed via the ``extra``
# self-append (``extra=model_name if "space" in model_name.lower()``,
# model.py:1207-1215) — both return before the generic head_config
# routing, so BOTH are probe-ineligible.
PROBE_INELIGIBLE = [
    "enformer-official-rough",  # enformer dedicated loader (suite special/enformer.py via model.py:1196-1204)
    "SPACE",                    # UPPERCASE registry row (models/SPACE): native space_models member "SPACE" claims it case-sensitively (suite special/space.py via model.py:1207-1215)
    "space",                    # lowercase registry row (models/space): claimed via the extra self-append ("space" in path.lower()) — the same dedicated loader (suite special/space.py via model.py:1207-1215)
    "borzoi-replicate-0",       # borzoi dedicated loader (suite special/borzoi.py via model.py:1218-1226)
    "flashzoi-replicate-0",     # borzoi-family flashzoi loader (suite special/borzoi.py via model.py:1218-1226)
    "evo2_1b_base",             # evo2 own-head branch (suite special/evo.py via model.py:1170-1172)
    "megaDNA_updated",          # megaDNA own-head branch (suite special/megadna.py via model.py:1183-1185)
    "gpn-brassicales",          # gpn special loader (suite special/gpn.py via model.py:1180)
    "Omni-DNA-700M",            # omnidna special loader (suite special/omnidna.py via model.py:1193)
]


def set_seed(seed=42):
    torch.manual_seed(seed)
    if NPU_AVAILABLE:
        torch.npu.manual_seed_all(seed)
    elif torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def init_layer(module):
    if isinstance(module, (nn.Linear, nn.Embedding)):
        nn.init.xavier_uniform_(module.weight)
        if module.bias is not None:
            nn.init.zeros_(module.bias)
    elif isinstance(module, nn.LayerNorm):
        nn.init.ones_(module.weight)
        nn.init.zeros_(module.bias)


def determine_batch_size(max_length, batch_size):
    # LENGTH-TIER BATCH ROUNDING (WR-04, legacy parity)
    # Ported verbatim from the deprecated pipeline's tier table
    # (pipeline/dnallmmark_pipeline.py:791-811, read-only behavioral
    # reference): the resolved sequence length puts an initial cap on the
    # configured batch size. The VRAM estimators below may reduce further
    # but never raise past this cap.
    if max_length <= 512:
        dynamic_batch_size = batch_size
    elif max_length <= 1024:
        dynamic_batch_size = max(1, batch_size // 2)
    elif max_length <= 2048:
        dynamic_batch_size = max(1, batch_size // 4)
    elif max_length <= 4096:
        dynamic_batch_size = max(1, batch_size // 8)
    elif max_length <= 8192:
        dynamic_batch_size = max(1, batch_size // 16)
    elif max_length <= 16384:
        dynamic_batch_size = max(1, batch_size // 32)
    else:
        dynamic_batch_size = 1

    print(
        f"Base batch size: {batch_size} | "
        f"Dynamic starting batch size: {dynamic_batch_size} "
        f"for max_len {max_length}"
    )

    return dynamic_batch_size


def estimate_batch_size(
    max_mem_measured,        # GB
    seq_len_measured,        # old
    seq_len_target,          # new
    batch_old,               # old batch_size
    gpu_mem_total=32,        # total memory (GB)
    max_change=10,           # max changes between old and new
    target_mem_ratio=0.4    # target GPU memory usage ratio
):
    predicted_mem = max_mem_measured * (seq_len_target / seq_len_measured)
    print(f"Estimated memory usage: {predicted_mem} GB ...")
    # Scale the old batch so the predicted usage lands on the target
    # memory ratio (WR-10: the previous if/else computed the IDENTICAL
    # expression in both branches — dead logic, removed).
    batch_new = int(batch_old * (gpu_mem_total * target_mem_ratio / predicted_mem))
    # Avoid high batch_new if batch_old is very low
    if batch_new // batch_old >= max_change:
        batch_new = batch_old * max_change
    return max(batch_new, 1)


def estimate_batch_size_by_model_params(
    model_params,           # number of model parameters
    gpu_mem_total=24,       # total memory (GB)
    seq_len=512,            # sequence length (token length)
    base_params=100e6,      # base model size (100M params)
    base_seq_len=512,       # base sequence length for estimation
    target_mem_ratio=0.70   # target GPU memory usage ratio
):
    """Estimate batch size based on model parameters and sequence length.
    
    Memory usage scales with:
    - Model parameters (linear)
    - Sequence length (quadratic for attention: O(n²))
    - Batch size (linear)
    
    Key insight: Transformer attention memory is O(seq_len²)
    """
    # Model memory (fp32 params + gradients + optimizer states)
    model_mem = (model_params * 4 * 4) / (1024**3)  # GB
    
    if model_params <= 0:
        return 1
    
    # Target memory usage
    target_mem = gpu_mem_total * target_mem_ratio
    
    # Sequence length scaling factor
    # Transformer attention is O(n²), but activations scale sub-quadratically
    # Use exponent 1.5 as a balance between linear and quadratic
    seq_scale = (seq_len / base_seq_len) ** 1.5
    
    # Base model overhead (model weights + optimizer states + gradients)
    if model_params < 100e6:
        model_overhead = model_mem * 1.3
    elif model_params < 300e6:
        model_overhead = model_mem * 1.4
    elif model_params < 600e6:
        model_overhead = model_mem * 1.5
    else:
        model_overhead = model_mem * 1.6
    
    # Memory per sample (scales with sequence length)
    # Base: ~0.3GB for 100M model at 512 tokens
    # Scales with both model size and sequence length
    base_mem_per_sample = 0.3 * (model_params / 100e6) ** 0.5
    mem_per_sample = base_mem_per_sample * seq_scale
    
    # First sample has extra overhead (input buffers, initial activations)
    first_sample_cost = mem_per_sample * 1.3
    
    # Total fixed overhead
    total_overhead = model_overhead + first_sample_cost
    
    # Available memory for additional samples
    available_for_samples = target_mem - total_overhead
    
    if available_for_samples <= 0:
        print(f"Warning: Memory tight. Model: {model_mem:.2f} GB, Overhead: {total_overhead:.2f} GB")
        return 1
    
    # Calculate batch size (first sample already counted)
    batch_size = 1 + max(0, int(available_for_samples / mem_per_sample))
    
    # Apply scaling based on model size
    scale_factor = (base_params / model_params) ** 0.3
    batch_size = int(batch_size * min(scale_factor, 1.5))
    
    # Safety bounds
    batch_size = max(1, min(batch_size, 64))
    
    print(f"Model params: {model_params:,}, Model memory: {model_mem:.2f} GB")
    print(f"Sequence length: {seq_len}, Seq scale factor: {seq_scale:.2f}x")
    print(f"GPU total: {gpu_mem_total:.2f} GB, Target: {target_mem:.2f} GB")
    print(f"Overhead: {total_overhead:.2f} GB, Mem/sample: {mem_per_sample:.3f} GB")
    print(f"Estimated batch size: {batch_size}")
    
    return batch_size

def get_current_time():
    now = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
    return now


# base_dir is this script's own directory (auto-inferred, no per-machine hardcoding)
base_dir = os.path.dirname(os.path.abspath(__file__)) + os.sep
with open(base_dir + "datasets_info.json", "r", encoding="utf-8") as _registry_file:
    datasets_info = json.load(_registry_file)

# Load models info
with open(base_dir + "models_info.json", "r", encoding="utf-8") as _registry_file:
    models_info = json.load(_registry_file)


if __name__ == "__main__":
    # Load arguments
    args = parse_args()
    target_model = args.target_model
    target_dataset = args.target_dataset
    batch_size = args.batch_size
    max_token_len = args.max_token_len
    remove_pt = args.remove_pt
    remove_checkpoints = args.remove_checkpoints
    category = args.category
    task_index = args.task_index
    auto_batch_size = args.auto_batch_size
    seed = args.seed
    gpu_memory_override = args.gpu_memory
    gpu_memory_override = args.gpu_memory
    mem_ratio = args.mem_ratio
    effective_batch_size = args.effective_batch_size
    output_dir = args.output_dir
    save_model_name = args.save_model_name
    gradient_checkpointing = args.gradient_checkpointing
    ddp_find_unused_parameters = args.ddp_find_unused_parameters
    subset_file = args.subset_file
    peft_mode = args.peft
    peft_dry_run = args.peft_dry_run
    num_train_epochs = args.num_train_epochs
    config_variant = args.config_variant
    train_fraction = args.train_fraction

    # Unified eval subsets (F7 Q3 / REV-07): validate the --subset_file
    # map fail-fast BEFORE any model load — the run_sweep._validate_filters
    # discipline (a bad map must abort loudly with every problem named,
    # never silently no-op an evaluation).
    eval_subsets = None
    if subset_file is not None:
        eval_subsets, subset_problems = validate_subset_file(
            subset_file, datasets_info
        )
        if subset_problems:
            sys.exit(
                f"[Error] invalid --subset_file {subset_file}: "
                + "; ".join(subset_problems)
            )

    # PEFT composition fail-fast (SC-6 lane tracer, 06-01): the dry run
    # is the suite's validate-and-exit adapter check — with --peft none
    # (or absent) there is no adapter to validate, and proceeding would
    # either silently full-train under a dry-run request or die deep in
    # the suite's own ctor refusal instead of at the argv boundary (the
    # suite raises the matching ValueError at trainer.py:411-416 @ v1.2.1
    # — this fail-fast names both flags first).
    if peft_dry_run and peft_mode == "none":
        sys.exit(
            "[Error] --peft_dry_run requires --peft lora or --peft ia3 "
            f"(got --peft {peft_mode}): the dry run is validate-and-exit "
            "and there is no adapter to validate in none mode"
        )

    # Probe x adapter composition refusal (MED-04, phase-06 review):
    # --config-variant probe and --peft lora/ia3 are independently legal
    # flags but must not compose. The probe lane trains a head on a
    # FROZEN backbone — adapters-on-frozen is a different experiment —
    # and the save-name chain resolves the peft alias FIRST, so the
    # composition would silently drop the +probe alias and write the
    # frozen-head adapter run into the PLAIN adapter cell's dir, where
    # the trainer_state.json resume marker makes the two semantically
    # different runs silently skip each other. Refuse fail-fast at the
    # argv boundary (the --peft_dry_run discipline), naming both flags.
    if config_variant == "probe" and peft_mode != "none":
        sys.exit(
            f"[Error] --config-variant probe refuses --peft {peft_mode}: "
            "the frozen-probe lane trains a head on a frozen backbone — "
            "adapters-on-frozen is a different experiment, and the "
            f"composition would share the {{model}}+{peft_mode} output "
            "dir (and resume marker) with the plain adapter cell"
        )

    # Probe ineligibility guard (SC-6/REV-05 F4, 06-05): the frozen-probe
    # lane covers GENERIC-PATH models only. The suite's
    # load_model_and_tokenizer dispatches the dedicated special-loader
    # families (model.py:1169-1228 @ v1.2.1 (30dfd6d)) BEFORE the generic
    # head_config routing (model.py:600-615), so task.head_config.frozen
    # (configs.py:14-17; the freeze loop executes at model.py:101-103)
    # never reaches those models — a probe run against one would silently
    # train an unfrozen model under a +probe dir. Refuse at the argv
    # boundary, naming the model(s) and the special-loader reason; the
    # target set is the explicit --target_model or the full registry when
    # absent (a whole-registry probe run hits the same boundary).
    if config_variant == "probe":
        probe_targets = (
            [target_model] if target_model is not None
            else [row["Model_name"] for row in models_info.values()]
        )
        ineligible_hits = sorted(
            name for name in probe_targets if name in PROBE_INELIGIBLE
        )
        if ineligible_hits:
            sys.exit(
                f"[Error] --config-variant probe refuses model(s) "
                f"{ineligible_hits}: dedicated suite special loaders "
                "(dnallm model.py:1169-1228 @ v1.2.1) return before the "
                "generic head_config routing (model.py:600-615), so the "
                "frozen field (configs.py:14-17, freeze loop "
                "model.py:101-103) never applies — the frozen-probe lane "
                "covers generic-path models only"
            )

    # Curve-lane fraction validation (REV-08/F8, 06-05): fail fast at the
    # argv boundary with every problem named (the --subset_file /
    # run_sweep._validate_filters discipline) — never deep in the
    # dataset loop after a model load.
    fraction_problems = validate_train_fraction(train_fraction)
    if fraction_problems:
        sys.exit(
            f"[Error] invalid --train_fraction {train_fraction!r}: "
            + "; ".join(fraction_problems)
        )

    # Detect GPU/NPU memory with fallbacks
    if torch.cuda.is_available():
        device = torch.device('cuda:0')
        detected_memory = torch.cuda.get_device_properties(device).total_memory / (1024**3)
        if gpu_memory_override is not None:
            gpu_mem_total = gpu_memory_override
            print(f"Using override GPU memory: {gpu_mem_total} GB")
        elif "GPU_MEMORY_GB" in os.environ:
            gpu_mem_total = float(os.environ["GPU_MEMORY_GB"])
            print(f"Using environment GPU memory: {gpu_mem_total} GB")
        else:
            gpu_mem_total = detected_memory
            print(f"Detected GPU memory: {gpu_mem_total:.2f} GB")
    elif NPU_AVAILABLE:
        device = torch.device('npu:0')
        detected_memory = torch.npu.get_device_properties(0).total_memory / (1024**3)
        if gpu_memory_override is not None:
            gpu_mem_total = gpu_memory_override
            print(f"Using override NPU memory: {gpu_mem_total} GB")
        elif "GPU_MEMORY_GB" in os.environ:
            gpu_mem_total = float(os.environ["GPU_MEMORY_GB"])
            print(f"Using environment NPU memory: {gpu_mem_total} GB")
        else:
            gpu_mem_total = detected_memory
            print(f"Detected NPU memory: {gpu_mem_total:.2f} GB")
    else:
        device = "cpu"
        gpu_mem_total = 32
        print("No GPU/NPU available, using default memory estimate: 32 GB")

    # Set seed for reproducable results
    set_seed(seed)

    # Define models with specific arguments
    # Safetensors disabled for these models (WR-03 union fix, ported from
    # the deprecated pipeline's list at :1322-1333): the legacy list
    # carried plant-dnamamba-6mer (the rewrite dropped it) and the rewrite
    # added PlantGFM (the legacy lacked it) — the union keeps BOTH, 11
    # entries total, so no side loses a model that needs the quirk.
    model_not_use_safetensors = [
        "hyenadna-large-1m-seqlen-hf",
        "caduceus-ph_seqlen-131k_d_model-256_n_layer-16",
        "caduceus-ps_seqlen-131k_d_model-256_n_layer-16",
        "Omni-DNA-700M", "plant-dnamamba-BPE",
        "plant-dnamamba-6mer",
        "enformer-official-rough", "space",
        "evo2_1b_base", "megaDNA_updated",
        "PlantGFM"
    ]
    deeplearning_models = [
        "enformer-official-rough",
        "space",
        "borzoi-replicate-0",
        "flashzoi-replicate-0",
    ]
    # Models that validate against the ACGT-only charset (WR-03, ported
    # from the deprecated pipeline's models_no_char_n at :1340-1350):
    # list members reject N bases ("ACGTacgt|"); all other models allow N
    # ("ACGTNacgtn|"). CURRENT unified-registry name forms — the legacy
    # entries prokbert-mini-c / prokbert-mini-long / MutBERT were dropped
    # at the D-10 unification and PlantCAD2-Large-l48-d1536 was renamed to
    # PlantCAD2-Large; the parity contract test in
    # tests/test_run_finetune_contracts.py pins this mapping (a blind
    # verbatim legacy copy FAILS that test, it does not resurrect names).
    models_no_char_n = deeplearning_models + [
        "PlantCAD2-Small-l24-d0768",
        "PlantCAD2-Medium-l48-d1024",
        "PlantCAD2-Large",
        "prokbert-mini",
        "MutBERT-Multi",
        "megaDNA_updated",
    ]
    # Per-model max_length caps (WR-03/AUD-15, ported from the deprecated
    # pipeline's models_with_limited_length at :1351-1354). The legacy dict
    # was defined but never applied (dead config — AUD-15); here it is
    # WIRED: the max_length-determination block clamps to these caps.
    models_with_limited_length = {
        "prokbert-mini": 1027,
        "plant-dnabert-6mer": 512,
    }
    # fp32-only models (CR-01, ported from the deprecated pipeline's quirk
    # list): the global finetune_config.yaml sets bf16: True, but these
    # registry models cannot train in reduced precision — the dataset loop
    # below forces fp16/bf16 off for them before the trainer is built.
    models_only_support_fp32 = [
        "Jamba-DNA-v1-114M-hg38",
        "CrossDNA_8.1M",
        "CrossDNA_71.6M",
        "CrossDNA_519M",
    ]

    # Iteratively finetune across different models and datasets
    max_mem = 0.0
    init_max_mem = -1
    init_batch_size = -1
    init_token_len = -1
    for ix, model_row in models_info.items():
        model_name = model_row["Model_name"]
        if target_model is not None and model_name != target_model:
            continue

        # Reload the base config fresh for EVERY model (D-11): the
        # custom-head override below REPLACES configs with the with_head
        # YAML and never restores it in-process, so a pre-loop load would
        # leak head_config residue into every model processed after
        # evo2_1b_base / megaDNA_updated in the same run.
        configs = load_config("./finetune_config.yaml")

        model_path = base_dir + model_row["Model_path"]
        tokenizer_type = model_row["Tokenizer"]
        mean_token_len = model_row["Mean_token_length"]

        # Open error log file
        os.makedirs("./logs/", exist_ok=True)
        with open(f"./logs/{model_name}_error_log.txt", "w") as error_log:

            # Config-variant reload (SC-6 lanes, 06-05): --config-variant
            # <name> loads the variant's YAML for ANY model at this exact
            # in-loop slot — the generalization of the special_models
            # auto-reload below. With NO variant this is a no-op and the
            # special_models membership check stays the byte-identical
            # default path (--config-variant head is the explicit
            # equivalent of that implicit behavior); the special_models
            # branch below still overrides for its own members under any
            # variant, so evo2/megaDNA keep their required head config.
            # Precedes the num_train_epochs override and the D-11
            # grad_accum snapshot below so the ACTIVE config governs.
            if config_variant is not None:
                configs = load_config(VARIANT_CONFIGS[config_variant])

            # Reload configurations for model with custom head
            if model_name in ["evo2_1b_base", "megaDNA_updated"]:
                configs = load_config("./finetune_config_with_head.yaml")
                configs['task'].head_config.head = model_name.lower().split("_")[0]

            # Bounded-smoke epochs override (06-02, plan-check blocker fix
            # 2026-10-11): --num_train_epochs (default None) OVERRIDES the
            # loaded config's finetune num_train_epochs — the knob this
            # plan's 1-epoch LoRA smoke and 06-05's probe smoke use; when
            # absent the YAML value governs (a None-guarded pure assignment,
            # the --subset_file seam style). Placed AFTER the custom-head
            # reload so the override applies to whichever config is active
            # for this model.
            if num_train_epochs is not None:
                configs["finetune"].num_train_epochs = num_train_epochs

            # Snapshot the ACTIVE config's YAML-default grad_accum (D-07,
            # WR-01): taken AFTER the custom-head reload above so
            # evo2_1b_base / megaDNA_updated snapshot the with_head YAML's
            # default rather than the base config's — the per-dataset reset
            # below must restore whichever config is actually active for
            # this model, or a future with_head grad_accum change would be
            # silently clobbered by the base YAML's value.
            default_grad_accum = configs["finetune"].gradient_accumulation_steps

            # Iterate through datasets
            count = 0
            for idx, row in datasets_info.items():
                dataset_name = row["Dataset_name"]
                dataset_path = base_dir + row["Dataset_path"]

                # Reset grad_accum to this model's YAML default (D-07) so a
                # per-task adjustment from the previous dataset cannot leak
                # into this one — the adjustment block below must start from
                # the default, never dataset A's mutated value.
                configs["finetune"].gradient_accumulation_steps = default_grad_accum

                # Select target dataset if specified
                if target_dataset is not None:
                    target_datasets = target_dataset.split(",")
                    if dataset_name not in target_datasets:
                        continue
            
                # Filter by category if specified
                if category is not None:
                    categories = category.split(",")
                    dataset_category = row.get("Category", "")
                    if dataset_category not in categories:
                        continue
            
                # Filter by task index if specified
                if task_index is not None:
                    task_indices = [int(i.strip()) for i in task_index.split(",")]
                    dataset_index = int(row.get("Index", -1))
                    if dataset_index not in task_indices:
                        continue

                # Refuse Dev-less tasks BEFORE any model load (F1 / REV-01).
                # Suite-side EVAL-01 contract
                # (dnallm/finetune/trainer.py L571-605 @ v1.2.1 (30dfd6d)):
                # dnallm uses test as the eval
                # set only when finetune.allow_test_as_eval is explicitly true
                # (config default False — a setting our configs must never
                # carry) and otherwise raises a hard ValueError for a missing
                # eval split under load_best_model_at_end / early stopping.
                # Refusing here fails fast on any future Dev-less task instead
                # of loading a model first.
                if not row["Dev"]:
                    raise SystemExit(
                        f"REFUSED: dataset '{dataset_name}' has no dev split "
                        "(Dev is falsy in datasets_info.json). Per the suite's "
                        "EVAL-01 contract, dnallm evaluates on test only when "
                        "finetune.allow_test_as_eval is explicitly true "
                        "(default False) and otherwise hard-errors on a "
                        "missing eval split under load_best_model_at_end / "
                        "early stopping — this task needs a dev split before "
                        "any model load. Remediation: carve one with "
                        "script/make_dev_splits.py."
                    )

                # Check data presence (WR-02, ported from the deprecated
                # pipeline's guard): an unlocatable dataset dir is a
                # documented, expected state (run_sweep.py records the
                # suite double-nesting unzip quirk deferred to the E2E
                # gate), so skip with a log line instead of letting
                # DNADataset.load_local_data raise an uncaught exception
                # that kills the whole model loop.
                if not os.path.isdir(dataset_path):
                    current_time = get_current_time()
                    message = (
                        f"[{current_time}] Dataset dir not found for "
                        f"{dataset_name}: {dataset_path} — skipping"
                    )
                    print(message)
                    print(message, file=error_log)
                    continue

                # Set task-specific configurations
                configs["task"].num_labels = row["labels"]
                configs["task"].label_names = [str(i) for i in range(row["labels"])]
                configs["task"].task_type = row["type"]
                if "head_config" in configs['task']:
                    configs['task'].head_config.task_type = row["type"]

                # Load model and tokenizer
                current_time = get_current_time()
                print(f"[{current_time}] Loading model: {model_name}")
                # v1.2.1 behavioral pin (verified read-only, 06-01): the
                # suite hardcodes attn_implementation="eager" in
                # _load_model_by_task_type's model_load_kwargs
                # (dnallm/models/model.py:590-594 @ v1.2.1 (30dfd6d)) for
                # every generic-path load, and trust_remote_code=True is
                # unconditional in all load paths — so our side needs NO
                # per-model attention-implementation or trust quirk list;
                # eager is the pinned suite behavior for every model here.
                try:
                    model, tokenizer = load_model_and_tokenizer(
                        model_path,
                        task_config=configs["task"],
                        source="local",
                    )
                # Blind except is the designed isolation (D-08 sanctioned):
                # a model-load failure logs and BREAKS to the next model;
                # narrowing the exception type risks aborting a multi-day
                # sweep on an unanticipated failure class (unverifiable
                # without GPU runs).
                except Exception as e:  # noqa: BLE001
                    current_time = get_current_time()
                    print(f"[{current_time}] Error loading model {model_name}: {e}")
                    print(f"--{ix}----------------"
                          f"[{current_time}] Error loading model {model_name}: {e}"
                          f"--------------------",
                          file=error_log
                    )
                    break

                # Initialize, check and repair meta tensor in the model
                target_layers = ["classifier", "score", "bert.pooler", "weighting_layer"]
                for name, module in model.named_modules():
                    # check parameters
                    for p_name, param in module.named_parameters(recurse=False):
                        if param.device.type == 'meta':
                            print(f"Detected meta parameter: {name}.{p_name}, materializing...")
                            module._parameters[p_name] = torch.nn.Parameter(
                                torch.empty_like(param, device="cpu"),
                                requires_grad=param.requires_grad
                            )
                    # check buffers
                    for b_name, buffer in module.named_buffers(recurse=False):
                        if buffer.device.type == 'meta':
                            print(f"Detected meta buffer: {name}.{b_name}, materializing...")
                            module.register_buffer(
                                b_name,
                                torch.zeros_like(buffer, device="cpu")  # 0 or 1
                            )
                    for target in target_layers:
                        if name.startswith(target):
                            print("Re-initializing:", name)
                            init_layer(module)
            
            
                # Auto batch size adjustment moved to after max_length calculation
                # to properly account for sequence length


                # Force fp32 for models that cannot train in reduced
                # precision (CR-01): finetune_config.yaml sets bf16: True
                # globally, so this override must land before DNATrainer
                # reads the config — mirrors the deprecated pipeline's
                # models_only_support_fp32 handling.
                if model_name in models_only_support_fp32:
                    configs["finetune"].fp16 = False
                    configs["finetune"].bf16 = False

                # Disable safetensors for specific models
                if model_name in model_not_use_safetensors:
                    # Disable safetensors when shared shades in model
                    configs["finetune"].save_safetensors = False
                else:
                    configs["finetune"].save_safetensors = True

                # IA³ enablement (SC-6 lane tracer, 06-01): use_ia3 IS a
                # TrainingConfig field (dnallm configs.py:326-334 @ v1.2.1
                # (30dfd6d)) — set here in the per-dataset quirk-mutation
                # block (the save_safetensors pattern above) BEFORE the
                # DNATrainer ctor reads it. The ia3: YAML section is
                # OPTIONAL for the suite (config.get default Ia3Config()
                # then preset resolution); the guard keeps the none
                # default a byte-identical no-op.
                if peft_mode == "ia3":
                    configs["finetune"].use_ia3 = True

                # PEFT dry-run request (suite validate-and-exit,
                # trainer.py:335-344/:451-461 @ v1.2.1): the TrainingConfig
                # flag the ctor reads to resolve the adapter config, match
                # target_modules, print the report, and return with
                # trainer=None — no training, no checkpoints.
                if peft_dry_run:
                    configs["finetune"].peft_dry_run = True

                # Set output directory for finetuning (seed-isolated per
                # G1/REV-02: the trainer_state.json resume marker below is
                # scoped to this seed, so resume never skips a different seed).
                # Adapter-run alias isolation (SC-6/REV-05, 06-02): an
                # adapter run (peft lora/ia3) with NO explicit
                # --save_model_name defaults its save name to
                # {model}+lora / {model}+ia3 — a separate model-level
                # output dir and therefore a separate trainer_state.json
                # resume marker, with ZERO layout-code changes. Variant
                # alias isolation (MED-04, phase-06 review): the probe
                # AND curve variants alias ({model}+probe / {model}+curve),
                # and --config-variant head aliases for GENERIC models
                # only ({model}+head) — a variant run that fell through
                # to the BASE name would land in {model}/{task}/seed_{s}/
                # where an existing full run's marker silently skips it
                # (or it completes first and the later REAL base run
                # silently skips, publishing a variant-config run as the
                # full result). The special_models pair (evo2_1b_base,
                # megaDNA_updated) is EXEMPT from the +head alias: their
                # with-head config IS their base config (the unchanged
                # auto-reload branch below), so an explicit
                # --config-variant head run is semantically the plain run
                # and keeps the base name. An explicit --save_model_name
                # always wins; the registry lookup / target_model
                # filtering above stays on the BASE model name (the
                # alias affects only output naming); peft=none with no
                # variant keeps exactly the base name (byte-identical
                # outdir).
                save_root = output_dir if output_dir else "./finetuned"
                if save_model_name:
                    model_save_name = save_model_name
                elif peft_mode != "none":
                    model_save_name = f"{model_name}+{peft_mode}"
                elif config_variant == "probe":
                    model_save_name = f"{model_name}+probe"
                elif config_variant == "curve":
                    model_save_name = f"{model_name}+curve"
                elif config_variant == "head" and model_name not in (
                    "evo2_1b_base", "megaDNA_updated"
                ):
                    model_save_name = f"{model_name}+head"
                else:
                    model_save_name = model_name
                outdir = f"{save_root}/{model_save_name}/{dataset_name}/seed_{seed}/"
                # Curve-lane fraction nesting (REV-08/F8, 06-05): frac_{f}
                # nests UNDER the seed dir — NEVER a sibling — so the
                # trainer_state.json resume check below stays scoped per
                # (model, task, seed, fraction): a full run's marker in
                # seed_{s}/ never skips a fraction cell and vice versa,
                # and fraction runs never collide with full runs.
                # --output_dir (the sweep path) supplies the ROOT
                # verbatim; this composition owns the tail layout.
                if train_fraction is not None:
                    outdir = f"{outdir}frac_{train_fraction}/"
                os.makedirs(outdir, exist_ok=True)
                configs["finetune"].output_dir = outdir

                if os.path.exists(outdir + "trainer_state.json"):
                    continue

                # Get dataset file paths
                data_dict = {}
                if row["Train"]:
                    train_path = dataset_path + "/train.csv"
                    data_dict["train"] = train_path
                if row["Dev"]:
                    val_path = dataset_path + "/dev.csv"
                    data_dict["dev"] = val_path
                if row["Test"]:
                    test_path = dataset_path + "/test.csv"
                    data_dict["test"] = test_path

                # Determine max sequence length
                data_length = row["length"]
                if tokenizer_type == "singlebase":
                    if model_name in [
                        "enformer-official-rough", "space",
                        "borzoi-replicate-0", "flashzoi-replicate-0",
                    ]:
                        max_length = int(np.ceil(data_length / 512) * 512)
                    else:
                        max_length = int(data_length) + 2  # accounting for special tokens
                else:
                    max_length = int(data_length / mean_token_len) + 2
                if max_token_len and max_length > max_token_len:
                    max_length = int(max_token_len)

                # Per-model length caps (WR-03/AUD-15): clamp the resolved
                # max_length to the model's documented cap. The legacy
                # pipeline defined this dict but never applied it (dead
                # config); here it is functional.
                if model_name in models_with_limited_length:
                    max_length = min(
                        max_length, models_with_limited_length[model_name]
                    )

                # WR-04 length-tier rounding: the resolved sequence length
                # caps the configured batch size by the legacy tier table
                # BEFORE any VRAM estimator runs — the estimators may
                # reduce below this cap but never raise past it.
                tier_batch_cap = determine_batch_size(max_length, batch_size)

                # Auto batch size adjustment based on model params and sequence length
                if auto_batch_size and count == 0:
                    model_params = sum(p.numel() for p in model.parameters())
                    print(f"Model parameters: {model_params:,}")
                    batch_size = estimate_batch_size_by_model_params(
                        model_params=model_params,
                        gpu_mem_total=gpu_mem_total,
                        seq_len=max_length,
                        target_mem_ratio=mem_ratio
                    )
                    print(f"Auto-adjusted batch size: {batch_size} (seq_len={max_length})")

                # Record batch size and token length
                if count == 0:
                    init_batch_size = batch_size
                    init_token_len = max_length
                if count == 1:
                    init_max_mem = max_mem

                # Set finetune-specific configurations
                configs["finetune"].metric_for_best_model = row["metric"]
                if init_max_mem > 0 and max_length > init_token_len:
                    bs_new = estimate_batch_size(
                        max_mem_measured=init_max_mem,
                        seq_len_measured=init_token_len,
                        seq_len_target=max_length,
                        batch_old=init_batch_size,
                        gpu_mem_total=gpu_mem_total,
                        # WR-10: honor --mem_ratio here too — previously
                        # this estimator silently used its 0.4 default and
                        # only the first-dataset estimator saw the flag.
                        target_mem_ratio=mem_ratio
                    )
                    print(f"Update batch size, old: {batch_size}, new: {bs_new}.")
                else:
                    bs_new = batch_size
                # Compose with the length-tier cap (WR-04): the VRAM path
                # may RAISE the estimate for a shorter dataset — never past
                # the tier cap for this sequence length.
                bs_new = min(bs_new, tier_batch_cap)
                configs["finetune"].per_device_train_batch_size = bs_new
                configs["finetune"].per_device_eval_batch_size = bs_new
                # log and evaluate n times during training
                num_train_data = int(row["Train"])
                # Curve-lane cadence scaling (REV-08/F8, 06-05): the
                # dynamic step calculation below must see the
                # FRACTION-SCALED train count — a 0.25 cell runs a
                # quarter of the steps, so the full-count cadence would
                # land 4x fewer logging/eval/save points than intended
                # (sparse curves). Guarded: absent fraction keeps the
                # registry count (byte-identical default path).
                if train_fraction is not None:
                    num_train_data = int(num_train_data * train_fraction)
                epoch = configs["finetune"].num_train_epochs
                grad_accum = configs["finetune"].gradient_accumulation_steps
                # In case memory insufficient or effective_batch_size is specified
                if effective_batch_size is not None:
                    # Adjust gradient_accumulation to achieve target effective batch size
                    if bs_new >= effective_batch_size:
                        # batch_size already large enough, no need for gradient accumulation
                        required_grad_accum = 1
                    else:
                        required_grad_accum = max(1, effective_batch_size // bs_new)
                    configs["finetune"].gradient_accumulation_steps = required_grad_accum
                    grad_accum = required_grad_accum
                    print(f"Effective batch size set to {effective_batch_size}: batch_size={bs_new}, gradient_accumulation={grad_accum}")
                elif bs_new < batch_size:
                    # WR-04 grad_accum compensation (legacy parity, ported
                    # from the deprecated pipeline's scaling at :1007-1012):
                    # a tier or VRAM reduction of the per-device batch is
                    # compensated by scaling gradient accumulation —
                    # max(1, batch_size // bs_new) — so the effective batch
                    # is preserved. grad_accum here still holds this
                    # model's YAML default (the D-07 reset at the top of
                    # the dataset loop), matching the legacy
                    # original_grad_accum base.
                    scaling_factor = max(1, batch_size // bs_new)
                    configs["finetune"].gradient_accumulation_steps = (
                        grad_accum * scaling_factor
                    )
                    grad_accum = configs["finetune"].gradient_accumulation_steps
                elif bs_new == 1 and grad_accum == 1:
                    grad_accum = 4
                    configs["finetune"].gradient_accumulation_steps = grad_accum
                # Calculate steps based on final batch_size and grad_accum
                num_gpus = int(os.environ.get("WORLD_SIZE", "1"))
                print(f"World size (num_gpus): {num_gpus}")
                step = num_train_data * epoch // (bs_new * grad_accum * num_gpus * 10)
                configs["finetune"].logging_steps = max(1, step)
                configs["finetune"].eval_steps = max(1, step)
                configs["finetune"].save_steps = max(1, step)

                # Load dataset
                multi_label_sep = None
                if row["labels"] > 1 and row["type"] in ["regression", "multilabel"]:
                    multi_label_sep = ";"
                dataset = DNADataset.load_local_data(
                    data_dict,
                    seq_col="sequence",
                    label_col="label",
                    multi_label_sep=multi_label_sep,
                    max_length=max_length
                )
                # Unified eval subset (F7 Q3): restrict the TEST split to
                # the audited common-filter rows BEFORE validate_sequences
                # (below) so the audited IDs are the actually-evaluated
                # rows. TEST SPLIT ONLY — train/dev stay full (dev drives
                # checkpoint selection, research A4). Without
                # --subset_file this is a no-op (identical code path).
                apply_eval_subset(dataset.dataset, dataset_name, eval_subsets)
                # Curve-lane train fraction (REV-08/F8, 06-05): the same
                # between-load-and-validate slot, TRAIN SPLIT ONLY —
                # seed-governed shuffle-then-select (A5), dev/test
                # untouched (the eval-invariance guarantee); absent flag
                # = the identical code path.
                apply_train_fraction(dataset.dataset, train_fraction, seed)
                # Get dataset statistics
                dataset_stat = dataset.statistics()
                # Processing dataset with sequence pairs
                if dataset_name == "GUE__EPI_GM12878":
                    seq_sep = "|"
                else:
                    seq_sep = None

                current_time = get_current_time()
                print(f"[{current_time}] Index: {idx}, Dataset: {dataset_name}")

                """
                # Sample a small portion for testing
                train_size = dataset_stat["train"]["n_samples"]
                if train_size < 100000:
                    ratio = 0.005
                elif 100000<= train_size < 500000:
                    ratio = 0.002
                else:
                    ratio = 0.001
                dataset.sampling(ratio=ratio, seed=42, overwrite=True)
                """

                # Encode sequences
                try:
                    # Filter sequences (some models do not support N bases)
                    # — WR-03 parity with the deprecated pipeline's
                    # conditional at :1055: models_no_char_n members
                    # validate against the ACGT-only charset; all other
                    # models allow N.
                    valid_chars = (
                        "ACGTacgt|"
                        if model_name in models_no_char_n
                        else "ACGTNacgtn|"
                    )
                    dataset.validate_sequences(
                        minl=0, maxl=10010, valid_chars=valid_chars
                    )
                    # Encoding
                    dataset.encode_sequences(
                        remove_unused_columns=True,
                        tokenizer=tokenizer,
                        seq_sep=seq_sep
                    )
                # Blind except is the designed isolation (D-08 sanctioned):
                # a dataset-encode failure logs and CONTINUEs to the next
                # dataset; narrowing the exception type risks aborting a
                # multi-day sweep on an unanticipated tokenizer failure
                # (unverifiable without GPU runs).
                except Exception as e:  # noqa: BLE001
                    current_time = get_current_time()
                    print(f"[{current_time}] Error encoding dataset {dataset_name} with model {model_name}: {e}")
                    print(f"[{current_time}] Error encoding dataset {dataset_name} with model {model_name}: {e}",
                          file=error_log
                    )
                    print("--------------------", file=error_log)
                    continue
                print(f"Tokenizer type: {tokenizer_type}. Infer max token length: {max_length}")

                # Specific adjustments for deep learning models
                if model_name in deeplearning_models:
                    model.target_length = max_length // model.resolution

                # Record GPU memory usage
                if NPU_AVAILABLE:
                    torch.npu.reset_peak_memory_stats()
                elif torch.cuda.is_available():
                    torch.cuda.reset_peak_memory_stats(device)

                # Initialize the trainer
                extra_args = {}
                if gradient_checkpointing:
                    extra_args["gradient_checkpointing"] = True
                    # use_reentrant=False avoids "marked as ready twice" under DDP
                    # (required for MoE shared_experts + checkpointing + DDP combo)
                    extra_args["gradient_checkpointing_kwargs"] = {"use_reentrant": False}
                    if hasattr(model, "config"):
                        model.config.use_cache = False
                    print("[Info] Gradient checkpointing enabled (use_reentrant=False, use_cache disabled).")
                if ddp_find_unused_parameters:
                    extra_args["ddp_find_unused_parameters"] = True
                    print("[Info] DDP find_unused_parameters forced True (required for MoE models).")
                trainer = DNATrainer(
                    model=model,
                    config=configs,
                    datasets=dataset,
                    extra_args=extra_args or None,
                    # LoRA enablement is a CONSTRUCTOR KWARG, not a config
                    # field (dnallm trainer.py:369-376 @ v1.2.1): a pure
                    # comparison evaluates False under the none default,
                    # so the peft=none ctor call is identical to today's.
                    # use_lora=True requires config["lora"] to exist —
                    # both YAMLs carry the lora: section (06-01).
                    use_lora=(peft_mode == "lora"),
                )

                # Trainable-params persistence (SC-6 frontier producer,
                # 06-02): the suite computes and PRINTS this accounting but
                # does not persist it (trainer.py:248-288 @ v1.2.1 —
                # _guard_trainable_ratio returns and discards it), so
                # run_finetune owns the record value — pure arithmetic over
                # the constructed (adapter-wrapped under peft) model,
                # persisted into final_metrics.json for EVERY mode
                # including none (a full run reports 100.0): the frontier
                # table needs the value in the record chain.
                trainable_params = sum(
                    p.numel() for p in trainer.model.parameters()
                    if p.requires_grad
                )
                total_params = sum(
                    p.numel() for p in trainer.model.parameters()
                )
                trainable_params_pct = round(
                    100.0 * trainable_params / max(total_params, 1), 6
                )

                # Start finetuning
                local_rank = int(os.environ.get("LOCAL_RANK", "0"))
                try:
                    metrics = trainer.train()
                    if local_rank == 0:
                        checkpoints = glob(outdir + "checkpoint-*")
                        all_steps = [int(ckpt.split("-")[-1]) for ckpt in checkpoints]
                        last_step = max(all_steps)
                        # Write final_metrics.json FIRST and copy the
                        # trainer_state.json resume marker LAST (WR-13):
                        # the marker is the completion signal both this
                        # script's resume check and run_sweep.py's skip
                        # check read, so it must be the final act of a
                        # successful cell. Copying it first opens a kill
                        # window (OOM killer / SIGKILL / power loss) in
                        # which the cell is permanently "done" with no
                        # metrics and is never retrained.
                        with open(outdir + "final_metrics.json", 'w') as f:
                            # Merge the post-ctor parameter accounting into
                            # the payload (06-02): the sweep copies
                            # final_metrics verbatim into run_record.metrics,
                            # so trainable_params_pct reaches the frontier
                            # reader through the existing channel.
                            metrics.update({
                                "trainable_params": trainable_params,
                                "total_params": total_params,
                                "trainable_params_pct": trainable_params_pct,
                            })
                            json.dump(metrics, f, indent=4)
                        shutil.copy(outdir + f"checkpoint-{last_step}/trainer_state.json", outdir)
                    trainer.evaluate()
                # Blind except is the designed isolation (D-08 sanctioned):
                # a dataset-train failure logs and CONTINUEs to the next
                # dataset; narrowing the exception type risks aborting a
                # multi-day sweep on an unanticipated training failure
                # (unverifiable without GPU runs).
                except Exception as e:  # noqa: BLE001
                    current_time = get_current_time()
                    print(f"[{current_time}] Error finetuning dataset {dataset_name} with model {model_name}: {e}")
                    print(f"[{current_time}] Error finetuning dataset {dataset_name} with model {model_name}: {e}",
                          file=error_log
                    )
                    print("--------------------", file=error_log)
                    continue

                if local_rank == 0:
                    if remove_checkpoints:
                        for checkpoint in checkpoints:
                            if not checkpoint.endswith("-"+str(last_step)):
                                shutil.rmtree(checkpoint)
                    if remove_pt:
                        for pt_file in glob(outdir + "checkpoint-*/*.pt"):
                            os.remove(pt_file)

                # Get max GPU usage during training
                if NPU_AVAILABLE:
                    max_mem = torch.npu.max_memory_allocated() / (1024**3)
                elif torch.cuda.is_available():
                    max_mem = torch.cuda.max_memory_allocated() / (1024**3)
                else:
                    max_mem = 0.0
                print(f"Training the model using {max_mem} GB memory.\n")
            
                # Update init_max_mem after first training to fix bug with --target_dataset
                if init_max_mem < 0:
                    init_max_mem = max_mem
                    print(f"Recorded initial max memory: {init_max_mem} GB")

                count += 1

