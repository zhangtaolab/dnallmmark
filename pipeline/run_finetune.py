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

import shutil
from glob import glob
import datetime
import argparse
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

# Import torch_npu for Huawei Ascend NPU support
try:
    import torch_npu
    NPU_AVAILABLE = torch.npu.is_available()
except ImportError:
    NPU_AVAILABLE = False

from dnallm import DNADataset, load_config, load_model_and_tokenizer, DNATrainer


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
        help="Filter datasets by index number from datasets_info.txt, supports multiple indices separated by comma (e.g., 1,2,7,10)"
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
        help="Custom model name used in output path (default: use Model_name from models_info.txt)"
    )

    args = parser.parse_args()
    return args


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
    # Use higher threshold for better GPU utilization
    threshold = target_mem_ratio
    if predicted_mem >= gpu_mem_total * threshold:
        batch_new = int(batch_old * (gpu_mem_total * threshold / predicted_mem))
    else:
        # More aggressive when we have headroom
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
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return now


# base_dir is this script's own directory (auto-inferred, no per-machine hardcoding)
base_dir = os.path.dirname(os.path.abspath(__file__)) + os.sep
datasets_info = pd.read_table(base_dir + "datasets_info.txt")

# Load models info
models_info = pd.read_table(base_dir + "models_info.txt")


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

    # Get pre-defined configs
    configs = load_config("./finetune_config.yaml")

    # Define models with specific arguments
    model_not_use_safetensors = [
        "hyenadna-large-1m-seqlen-hf",
        "caduceus-ph_seqlen-131k_d_model-256_n_layer-16",
        "caduceus-ps_seqlen-131k_d_model-256_n_layer-16",
        "Omni-DNA-700M", "plant-dnamamba-BPE",
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

    # Iteratively finetune across different models and datasets
    max_mem = 0.0
    init_max_mem = -1
    init_batch_size = -1
    init_token_len = -1
    for ix, model_row in models_info.iterrows():
        model_name = model_row["Model_name"]
        if target_model is not None:
            if model_name != target_model:
                continue
        model_path = base_dir + model_row["Model_path"]
        tokenizer_type = model_row["Tokenizer"]
        mean_token_len = model_row["Mean_token_length"]

        # Open error log file
        os.makedirs("./logs/", exist_ok=True)
        error_log = open(f"./logs/{model_name}_error_log.txt", "w")

        # Reload configurations for model with custom head
        if model_name in ["evo2_1b_base", "megaDNA_updated"]:
            configs = load_config("./finetune_config_with_head.yaml")
            configs['task'].head_config.head = model_name.lower().split("_")[0]

        # Iterate through datasets
        count = 0
        for idx, row in datasets_info.iterrows():
            dataset_name = row["Dataset_name"]
            dataset_path = base_dir + row["Dataset_path"]

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

            # Set task-specific configurations
            configs["task"].num_labels = row["labels"]
            configs["task"].label_names = [str(i) for i in range(row["labels"])]
            configs["task"].task_type = row["type"]
            if "head_config" in configs['task']:
                configs['task'].head_config.task_type = row["type"]

            # Load model and tokenizer
            current_time = get_current_time()
            print(f"[{current_time}] Loading model: {model_name}")
            try:
                model, tokenizer = load_model_and_tokenizer(
                    model_path,
                    task_config=configs["task"],
                    source="local",
                )
            except Exception as e:
                current_time = get_current_time()
                print(f"[{current_time}] Error loading model {model_name}: {e}")
                print(f"--{ix}----------------"
                      f"[{current_time}] Error loading model {model_name}: {e}"
                      f"--------------------",
                      file=error_log
                )
                error_log.close()
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


            # Disable safetensors for specific models
            if model_name in model_not_use_safetensors:
                # Disable safetensors when shared shades in model
                configs["finetune"].save_safetensors = False
            else:
                configs["finetune"].save_safetensors = True

            # Set output directory for finetuning
            save_root = output_dir if output_dir else "./finetuned"
            model_save_name = save_model_name if save_model_name else model_name
            outdir = f"{save_root}/{model_save_name}/{dataset_name}/"
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
            if max_token_len:
                if max_length > max_token_len:
                    max_length = int(max_token_len)
            
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
                    gpu_mem_total=gpu_mem_total
                )
                print(f"Update batch size, old: {batch_size}, new: {bs_new}.")
            else:
                bs_new = batch_size
            configs["finetune"].per_device_train_batch_size = bs_new
            configs["finetune"].per_device_eval_batch_size = bs_new
            # log and evaluate n times during training
            num_train_data = int(row["Train"])
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
            elif bs_new == 1 and grad_accum == 1:
                grad_accum = 4
                configs["finetune"].gradient_accumulation_steps = grad_accum
            # Calculate steps based on final batch_size and grad_accum
            num_gpus = int(os.environ.get("WORLD_SIZE", 1))
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
                dataset.validate_sequences(minl=0, maxl=10010, valid_chars="ACGTacgt|")
                # Encoding
                dataset.encode_sequences(
                    remove_unused_columns=True,
                    tokenizer=tokenizer,
                    seq_sep=seq_sep
                )
            except Exception as e:
                current_time = get_current_time()
                print(f"[{current_time}] Error encoding dataset {dataset_name} with model {model_name}: {e}")
                print(f"[{current_time}] Error encoding dataset {dataset_name} with model {model_name}: {e}",
                      file=error_log
                )
                print(f"--------------------", file=error_log)
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
            )

            # Start finetuning
            local_rank = int(os.environ.get("LOCAL_RANK", 0))
            try:
                metrics = trainer.train()
                if local_rank == 0:
                    checkpoints = glob(outdir + "checkpoint-*")
                    all_steps = [int(ckpt.split("-")[-1]) for ckpt in checkpoints]
                    last_step = sorted(all_steps)[-1]
                    shutil.copy(outdir + f"checkpoint-{last_step}/trainer_state.json", outdir)
                    with open(outdir + "final_metrics.json", 'w') as f:
                        json.dump(metrics, f, indent=4)
                trainer.evaluate()
            except Exception as e:
                current_time = get_current_time()
                print(f"[{current_time}] Error finetuning dataset {dataset_name} with model {model_name}: {e}")
                print(f"[{current_time}] Error finetuning dataset {dataset_name} with model {model_name}: {e}",
                      file=error_log
                )
                print(f"--------------------", file=error_log)
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

        error_log.close()
