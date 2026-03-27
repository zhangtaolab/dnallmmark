import os

# Uncomment this if you want to use specific directory for cache
# os.environ["HF_HOME"] = "./cache"
# os.environ["MS_CACHE_HOME"] = "./cache"

import shutil
from glob import glob
import datetime
import argparse
import json
import math
import numpy as np
from pathlib import Path

import torch
import torch.nn as nn
from dnallm import DNADataset, load_config, load_model_and_tokenizer, DNATrainer


# ========================================================
# FLOPs Counter Tooling
# ========================================================
class FlopsCounter:
    def __init__(
        self,
        model,
        include_norm=False,
        include_act=False,
        include_embed=False,
        architecture=None,
    ):
        self.model = model
        self.include_norm = include_norm
        self.include_act = include_act
        self.include_embed = include_embed
        self.architecture = architecture

        self.total_flops = 0
        self.total_params = sum(p.numel() for p in model.parameters())
        self.layer_flops = {}
        self.hooks = []
        self._is_active = True

        self._register_hooks()

    def _register_hooks(self):
        for name, module in self.model.named_modules():
            classname = module.__class__.__name__
            model_path = getattr(self.model, "name_or_path", "").lower()

            # 1. Core Heavy Computation Layers
            if isinstance(module, nn.Linear):
                self.hooks.append(module.register_forward_hook(self._linear_hook(name)))
            elif isinstance(module, nn.Conv1d):
                self.hooks.append(module.register_forward_hook(self._conv1d_hook(name)))
            elif isinstance(module, nn.Conv2d):
                self.hooks.append(module.register_forward_hook(self._conv2d_hook(name)))
            elif isinstance(module, nn.MultiheadAttention):
                self.hooks.append(module.register_forward_hook(self._mha_hook(name)))
            elif classname in [
                "BertSelfAttention",
                "JambaAttention",
                "MistralAttention",
                "MistralSdpaAttention",
                "RoPEBertSdpaAttention",
                "OLMoSequentialBlock",
                "GPT2Attention",
                "EsmSelfAttention",
                "MegatronBertSelfAttention",
            ]:
                self.hooks.append(
                    module.register_forward_hook(self._hf_self_attn_hook(name))
                )
            elif classname == "Conv1D":
                self.hooks.append(
                    module.register_forward_hook(self._hf_conv1d_hook(name))
                )
            elif classname == "BertUnpadSelfAttention":
                self.hooks.append(
                    module.register_forward_hook(self._dnabert2_flash_attn_hook(name))
                )
            elif classname in [
                "MistralFlashAttention",
                "MistralFlashAttention2",
                "FlashAttentionBlock",
            ]:
                self.hooks.append(
                    module.register_forward_hook(self._flash_attn_hook(name))
                )
            elif classname == "ModernBertAttention":
                self.hooks.append(
                    module.register_forward_hook(self._modernbert_attn_hook(name))
                )
            elif classname in [
                "LlamaAttention",
                "GemmaAttention",
                "GemmaFlashAttention2",
                "GemmaSdpaAttention",
            ]:
                self.hooks.append(
                    module.register_forward_hook(self._gqa_attn_hook(name))
                )
            elif classname == "BigBirdAttention":
                self.hooks.append(
                    module.register_forward_hook(self._bigbird_attn_hook(name))
                )
            elif classname == "HyenaFilter":
                self.hooks.append(
                    module.register_forward_hook(self._hyena_filter_hook(name))
                )
            elif classname in ["MambaMixer", "JambaMambaMixer"]:
                self.hooks.append(
                    module.register_forward_hook(self._mamba_ssm_hook(name))
                )
            elif classname in ["Mamba2Mixer"]:
                self.hooks.append(
                    module.register_forward_hook(self._mamba2_ssd_hook(name))
                )
            elif classname in ["Mamba"]:
                self.hooks.append(
                    module.register_forward_hook(self._caduceus_ssm_hook(name))
                )
            elif classname in ["Mamba2"]:
                self.hooks.append(
                    module.register_forward_hook(self._caduceus2_ssd_hook(name))
                )
            elif "megadna" in model_path:
                if classname == "Attention" and hasattr(module, "to_q"):
                    self.hooks.append(
                        module.register_forward_hook(self._megabyte_attn_hook(name))
                    )
            elif "enformer" in model_path or "space" in model_path:
                if (
                    classname == "Attention"
                    and hasattr(module, "to_rel_k")
                    and hasattr(module, "use_tf_gamma")
                ):
                    self.hooks.append(
                        module.register_forward_hook(self._enformer_attn_hook(name))
                    )
            elif "borzoi" in model_path or "flashzoi" in model_path:
                if classname == "Attention":
                    self.hooks.append(
                        module.register_forward_hook(self._borzoi_attn_hook(name))
                    )
                elif classname == "FlashAttention":
                    self.hooks.append(
                        module.register_forward_hook(self._borzoi_flash_attn_hook(name))
                    )

            # 2. Optional: Embedding
            elif isinstance(module, nn.Embedding) and self.include_embed:
                self.hooks.append(
                    module.register_forward_hook(self._embedding_hook(name))
                )
            # 3. Optional: Norm
            elif (
                "Norm" in classname or isinstance(module, nn.LayerNorm)
            ) and self.include_norm:
                self.hooks.append(module.register_forward_hook(self._norm_hook(name)))
            # 4. Optional: Activation
            elif (
                "SiLU" in classname or isinstance(module, (nn.SiLU, nn.GELU, nn.ReLU))
            ) and self.include_act:
                self.hooks.append(
                    module.register_forward_hook(self._activation_hook(name))
                )

    def _linear_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            x = inputs[0]
            in_feat, out_feat = x.shape[-1], module.out_features
            num_tokens = x.numel() // in_feat
            flops = 2 * num_tokens * in_feat * out_feat
            self.total_flops += flops
            self.layer_flops[name] = flops

        return hook

    def _conv1d_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            x = inputs[0]
            b, in_channels, seq_len = x.shape
            out_channels, k, groups = (
                module.out_channels,
                module.kernel_size[0],
                module.groups,
            )
            flops = 2 * b * seq_len * (in_channels // groups) * out_channels * k
            self.total_flops += flops
            self.layer_flops[name] = flops

        return hook

    def _conv2d_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            x = inputs[0]
            b, in_channels, h, w = x.shape
            out_channels, (k_h, k_w), groups = (
                module.out_channels,
                module.kernel_size,
                module.groups,
            )
            flops = 2 * b * h * w * (in_channels // groups) * out_channels * k_h * k_w
            self.total_flops += flops
            self.layer_flops[name] = flops

        return hook

    def _mha_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            q = inputs[0]
            b, seq_len, d = (
                (q.shape[0], q.shape[1], q.shape[2])
                if module.batch_first
                else (q.shape[1], q.shape[0], q.shape[2])
            )
            proj_flops = 8 * b * seq_len * (d**2)
            attn_flops = 4 * b * (seq_len**2) * d
            total_mha_flops = proj_flops + attn_flops
            self.total_flops += total_mha_flops
            self.layer_flops[name] = total_mha_flops

        return hook

    def _hf_self_attn_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            x = (
                inputs[0]
                if len(inputs) > 0
                else (outputs[0] if isinstance(outputs, tuple) else outputs)
            )
            b, seq_len, d = x.shape[0], x.shape[1], x.shape[2]
            d_attn = (
                module.q_proj.out_features
                if hasattr(module, "q_proj")
                else (module.query.out_features if hasattr(module, "query") else d)
            )
            attn_core_flops = 4 * b * (seq_len**2) * d_attn
            self.total_flops += attn_core_flops
            self.layer_flops[f"{name}.matmul_core"] = attn_core_flops

        return hook

    def _hf_conv1d_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            x = inputs[0]
            b, seq_len, in_feat = (
                x.shape if x.dim() == 3 else (*x.shape, 1)[0],
                1 if x.dim() != 3 else x.shape[1],
                x.shape[-1],
            )
            out_feat = module.nf
            flops = 2 * b * seq_len * in_feat * out_feat
            self.total_flops += flops
            self.layer_flops[name] = flops

        return hook

    def _dnabert2_flash_attn_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            cu_seqlens = inputs[1]
            d = module.all_head_size
            seq_lens = cu_seqlens[1:] - cu_seqlens[:-1]
            sum_sq_len = (seq_lens**2).sum().item()
            attn_flops = 4 * d * sum_sq_len
            self.total_flops += attn_flops
            self.layer_flops[f"{name}.flash_attn_core"] = attn_flops

        return hook

    def _modernbert_attn_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            x = (
                inputs[0]
                if len(inputs) > 0
                else (outputs[0] if isinstance(outputs, tuple) else outputs)
            )
            b, seq_len, d = x.shape[0], x.shape[1], x.shape[2]
            window_size = getattr(module.config, "local_attention", 128)
            try:
                layer_idx = int(name.split(".")[2])
            except Exception:
                layer_idx = 0
            attn_layer_step = getattr(module.config, "global_attn_every_n_layers", None)
            is_global = (layer_idx % attn_layer_step == 0) if attn_layer_step else False
            attn_core_flops = (
                4 * b * seq_len * window_size * d
                if (not is_global and seq_len > window_size)
                else 4 * b * (seq_len**2) * d
            )
            self.total_flops += attn_core_flops
            self.layer_flops[f"{name}.matmul_core"] = attn_core_flops

        return hook

    def _gqa_attn_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            x = (
                inputs[0]
                if len(inputs) > 0
                else (outputs[0] if isinstance(outputs, tuple) else outputs)
            )
            b, seq_len = x.shape[0], x.shape[1]
            d_q = module.q_proj.out_features
            window_size = getattr(module.config, "sliding_window", None)
            attn_core_flops = (
                4 * b * seq_len * window_size * d_q
                if (
                    window_size is not None
                    and seq_len > window_size
                    and "FlashAttention" in module.__class__.__name__
                )
                else 4 * b * (seq_len**2) * d_q
            )
            self.total_flops += attn_core_flops
            self.layer_flops[f"{name}.matmul_core"] = attn_core_flops

        return hook

    def _flash_attn_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            x = (
                inputs[0]
                if len(inputs) > 0
                else (outputs[0] if isinstance(outputs, tuple) else outputs)
            )
            b, seq_len, d = x.shape[0], x.shape[1], x.shape[2]
            window_size = (
                getattr(module.config, "sliding_window", None)
                if hasattr(module, "config")
                else None
            )
            attn_core_flops = (
                4 * b * seq_len * window_size * d
                if (
                    window_size is not None
                    and seq_len > window_size
                    and module.__class__.__name__.endswith("FlashAttention2")
                )
                else 4 * b * (seq_len**2) * d
            )
            self.total_flops += attn_core_flops
            self.layer_flops[f"{name}.matmul_core"] = attn_core_flops

        return hook

    def _bigbird_attn_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            x = (
                inputs[0]
                if len(inputs) > 0
                else (outputs[0] if isinstance(outputs, tuple) else outputs)
            )
            b, seq_len = x.shape[0], x.shape[1]
            inner_attn = getattr(module, "self", None)
            if inner_attn is None:
                return
            d_q, d_in = inner_attn.query.out_features, inner_attn.query.in_features

            if len(inner_attn.query._forward_hooks) == 0:
                qkv_flops = 3 * (2 * b * seq_len * d_in * d_q)
                self.total_flops += qkv_flops
                self.layer_flops[f"{name}.qkv_dynamic_fused"] = qkv_flops

            is_sparse = inner_attn.__class__.__name__ == "BigBirdBlockSparseAttention"
            if is_sparse:
                effective_seq_len = (
                    5 + getattr(inner_attn, "num_random_blocks", 3)
                ) * getattr(inner_attn, "block_size", 64)
                attn_core_flops = 4 * b * seq_len * effective_seq_len * d_q
            else:
                attn_core_flops = 4 * b * (seq_len**2) * d_q
            self.total_flops += attn_core_flops
            self.layer_flops[f"{name}.matmul_core"] = attn_core_flops

        return hook

    def _hyena_filter_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            x = inputs[0]
            b, d, seq_len = x.shape
            n = 2 * seq_len
            if n <= 0:
                return
            log2_n = math.log2(n)
            total_fft_flops = (
                (5 * b * d * seq_len * log2_n)
                + (5 * d * seq_len * log2_n)
                + (6 * b * d * (seq_len + 1))
                + (5 * b * d * seq_len * log2_n)
                + (4 * b * d * seq_len)
            )
            self.total_flops += total_fft_flops
            self.layer_flops[f"{name}.fftconv_core"] = total_fft_flops

        return hook

    def _caduceus_ssm_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            b, seq_len, _ = inputs[0].shape
            d_inner = module.conv1d.in_channels
            d_state = getattr(module, "ssm_state_size", None) or (
                self.model.config.ssm_cfg["d_state"]
                if hasattr(self.model.config, "ssm_cfg")
                else 16
            )
            d_model = getattr(module, "d_model", getattr(module, "hidden_size", 256))
            dt_rank = getattr(module, "time_step_rank", None) or (
                math.ceil(d_model / 16) if hasattr(self.model.config, "ssm_cfg") else 16
            )

            ssm_flops = 9 * b * seq_len * d_inner * d_state
            self.total_flops += ssm_flops
            self.layer_flops[f"{name}.ssm_core"] = ssm_flops

            if hasattr(module, "conv1d"):
                conv_flops = 2 * b * seq_len * d_inner * module.conv1d.kernel_size[0]
                self.total_flops += conv_flops
                self.layer_flops[f"{name}.conv1d_fused"] = conv_flops

            self.total_flops += 2 * b * seq_len * d_model * (d_inner * 2)  # in_proj
            self.total_flops += (
                2 * b * seq_len * d_inner * (dt_rank + 2 * d_state)
            )  # x_proj
            self.total_flops += 2 * b * seq_len * dt_rank * d_inner  # dt_proj
            self.total_flops += (
                2 * b * seq_len * d_inner * module.out_proj.out_features
            )  # out_proj

        return hook

    def _caduceus2_ssd_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            b, seq_len, _ = inputs[0].shape
            head_dim = getattr(module, "head_dim", 64)
            d_model = getattr(module, "d_model", getattr(module, "hidden_size", 256))
            n_heads = d_model // head_dim if head_dim else 4
            d_state = getattr(
                module,
                "state_size",
                getattr(
                    module,
                    "d_state",
                    getattr(self.model.config, "ssm_cfg", {}).get("d_state", 128),
                ),
            )
            d_inner = (
                getattr(
                    module,
                    "expand",
                    getattr(self.model.config, "ssm_cfg", {}).get("expand", 2),
                )
                * d_model
            )

            flops = 4 * b * seq_len * (n_heads * head_dim) * d_state
            self.total_flops += flops
            self.layer_flops[f"{name}.ssd_core"] = flops

            if hasattr(module, "conv1d"):
                conv_flops = (
                    2
                    * b
                    * seq_len
                    * module.conv1d.in_channels
                    * module.conv1d.kernel_size[0]
                )
                self.total_flops += conv_flops
            self.total_flops += 2 * b * seq_len * d_inner * module.out_proj.out_features

        return hook

    def _mamba_ssm_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            x = (
                inputs[0]
                if len(inputs) > 0
                else (outputs[0] if isinstance(outputs, tuple) else outputs)
            )
            b, seq_len, _ = x.shape
            d_inner = module.conv1d.in_channels
            d_state = getattr(module, "ssm_state_size", 16)
            dt_rank = getattr(module, "time_step_rank", 16)

            ssm_flops = 9 * b * seq_len * d_inner * d_state
            self.total_flops += ssm_flops
            self.layer_flops[f"{name}.ssm_core"] = ssm_flops

            if hasattr(module, "conv1d"):
                conv_flops = 2 * b * seq_len * d_inner * module.conv1d.kernel_size[0]
                self.total_flops += conv_flops
            self.total_flops += 2 * b * seq_len * dt_rank * d_inner  # dt_proj

        return hook

    def _mamba2_ssd_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            b, seq_len, _ = inputs[0].shape
            n_heads, head_dim = (
                getattr(module, "num_heads", 4),
                getattr(module, "head_dim", 64),
            )
            n_state = getattr(
                module, "ssm_state_size", getattr(module, "state_size", 128)
            )

            flops = 4 * b * seq_len * (n_heads * head_dim) * n_state
            self.total_flops += flops
            self.layer_flops[f"{name}.ssd_core"] = flops

            if hasattr(module, "conv1d"):
                conv_flops = (
                    2
                    * b
                    * seq_len
                    * module.conv1d.in_channels
                    * module.conv1d.kernel_size[0]
                )
                self.total_flops += conv_flops

        return hook

    def _megabyte_attn_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            x = (
                inputs[0]
                if len(inputs) > 0
                else (outputs[0] if isinstance(outputs, tuple) else outputs)
            )
            b, seq_len, _ = x.shape
            d_q = module.to_q.out_features
            attn_core_flops = 4 * b * (seq_len**2) * d_q
            self.total_flops += attn_core_flops
            self.layer_flops[f"{name}.matmul_core"] = attn_core_flops

        return hook

    def _borzoi_attn_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            x = (
                inputs[0]
                if len(inputs) > 0
                else (outputs[0] if isinstance(outputs, tuple) else outputs)
            )
            b, seq_len, _ = x.shape
            d_q = module.to_q.out_features
            total_attn_flops = (4 * b * (seq_len**2) * d_q) + (
                2 * b * (seq_len**2) * d_q
            )
            self.total_flops += total_attn_flops
            self.layer_flops[f"{name}.matmul_core"] = total_attn_flops

        return hook

    def _enformer_attn_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            x = (
                inputs[0]
                if len(inputs) > 0
                else (outputs[0] if isinstance(outputs, tuple) else outputs)
            )
            b, seq_len, _ = x.shape
            d_q, d_v = module.to_q.out_features, module.to_v.out_features
            total_attn_flops = (
                (2 * b * (seq_len**2) * d_q)
                + (2 * b * (seq_len**2) * d_q)
                + (2 * b * (seq_len**2) * d_v)
            )
            self.total_flops += total_attn_flops
            self.layer_flops[f"{name}.matmul_core"] = total_attn_flops

        return hook

    def _borzoi_flash_attn_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            b, seq_len, d = inputs[0].shape
            mha_flops = 8 * b * seq_len * (d**2) + 4 * b * (seq_len**2) * d
            self.total_flops += mha_flops
            self.layer_flops[f"{name}.flash_mha_core"] = mha_flops

        return hook

    def _embedding_hook(self, name):
        def hook(module, inputs, outputs):
            pass

        return hook

    def _norm_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            flops = 4 * inputs[0].numel()
            self.total_flops += flops
            self.layer_flops[name] = flops

        return hook

    def _activation_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            flops = 4 * inputs[0].numel()
            self.total_flops += flops
            self.layer_flops[name] = flops

        return hook

    def remove_hooks(self):
        for handle in self.hooks:
            handle.remove()
        self.hooks = []
        self._is_active = False

    def save_to_json(
        self, num_tokens=None, all_tokens=None, filepath="flops_report.json"
    ):
        per_token_flops = (
            self.total_flops / num_tokens if num_tokens is not None else None
        )
        all_tokens_flops = (
            self.total_flops * all_tokens / num_tokens
            if all_tokens is not None and num_tokens is not None
            else None
        )
        computation_size_ratio = (
            per_token_flops / self.total_params if self.total_params > 0 else None
        )
        report = {
            "num_tokens": num_tokens,
            "all_tokens": all_tokens,
            "num_params": self.total_params,
            "total_flops_G": self.total_flops / 1e9,
            "total_flops_exact": self.total_flops,
            "total_flops_per_token": per_token_flops,
            "total_flops_all_tokens": all_tokens_flops,
            "computation_size_ratio": computation_size_ratio,
            "config": {
                "include_norm": self.include_norm,
                "include_act": self.include_act,
                "include_embed": self.include_embed,
            },
            "layer_details": self.layer_flops,
        }
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)


def count_split_tokens(hf_dataset):
    if hf_dataset is None:
        return 0, 0
    n_tokens = 0
    n_samples = 0
    for x in hf_dataset:
        if "input_ids" in x:
            n_tokens += len(x["input_ids"])
            n_samples += 1
    return n_tokens, n_samples


# ========================================================
# Pipeline Core
# ========================================================
def parse_args():
    parser = argparse.ArgumentParser(description="DNALLM-Mark pipeline")

    parser.add_argument(
        "--target_model",
        type=str,
        default=None,
        help="Name of the target model for training",
    )
    parser.add_argument(
        "--target_dataset",
        type=str,
        default=None,
        help="Name of the target dataset for training",
    )
    parser.add_argument("--batch_size", type=int, default=8, help="Manual batch size")
    parser.add_argument(
        "--fix_token_len", type=int, default=None, help="Manual set max token length"
    )
    parser.add_argument(
        "--max_token_len",
        type=int,
        default=None,
        help="Manual max token length in case model with singlebase tokenizer processing extra-long sequences",
    )
    parser.add_argument(
        "--remove_pt",
        action="store_true",
        default=False,
        help="If set, remove .pt files in checkpoints",
    )
    parser.add_argument(
        "--remove_checkpoints",
        action="store_true",
        default=False,
        help="If set, remove the all checkpoints directory except the last one",
    )
    parser.add_argument("--seed", type=int, default=9527, help="Random seed")

    args = parser.parse_args()
    return args


def set_seed(seed=42):
    torch.manual_seed(seed)
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


def get_current_time():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return now


def determine_batch_size(max_length, batch_size):
    # DYNAMIC BATCH SIZE SCALING
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


def main():
    # Load arguments
    args = parse_args()
    target_model = args.target_model
    target_dataset = args.target_dataset
    batch_size = args.batch_size
    fix_token_len = args.fix_token_len
    max_token_len = args.max_token_len
    remove_pt = args.remove_pt
    remove_checkpoints = args.remove_checkpoints
    seed = args.seed

    # Set seed for reproducable results
    set_seed(seed)

    # Get pre-defined configs
    configs = load_config("./finetune_config.yaml")

    # Iteratively finetune across different models and datasets
    for model_key, model_row in models_info.items():
        model_name = model_key
        if target_model is not None:
            if model_name != target_model:
                continue

        model_path = os.path.join(base_dir, "models", model_name)
        tokenizer_type = model_row["tokenizer"]
        mean_token_len = model_row["mean_token_len"]

        # Check model presence
        if not os.path.exists(model_path):
            continue

        # Open error log file
        os.makedirs("./logs/", exist_ok=True)
        error_log = open(f"./logs/{model_name}_error_log.txt", "w")

        # Reload configurations for model with custom head
        if model_name in special_models:
            configs = load_config("./finetune_config_with_head.yaml")
            configs["task"].head_config.head = model_name.lower().split("_")[0]

        # Iterate through datasets
        count = 0
        for dataset_name, row in datasets_info.items():
            dataset_path = os.path.join(base_dir, row["Dataset_path"])

            # Select target dataset if specified
            if target_dataset is not None:
                target_datasets = target_dataset.split(",")
                if dataset_name not in target_datasets:
                    continue

            # Check data presence
            if not os.path.exists(dataset_path):
                continue

            # Set task-specific configurations
            configs["task"].num_labels = row["labels"]
            configs["task"].label_names = [str(i) for i in range(row["labels"])]
            configs["task"].task_type = row["type"]
            if "head_config" in configs["task"]:
                configs["task"].head_config.task_type = row["type"]

            if model_name in models_only_support_fp32:
                configs["finetune"].fp16 = False
                configs["finetune"].bf16 = False

            # Load model and tokenizer
            current_time = get_current_time()
            print(f"[{current_time}] Loading model: {model_name}")
            try:
                try:
                    # Default manner
                    model, tokenizer = load_model_and_tokenizer(
                        model_path,
                        task_config=configs["task"],
                        source="local",
                    )
                except Exception as e:
                    # Fallback to manual loading
                    # For some models that not provide pre-trained weights
                    from transformers import (
                        AutoConfig,
                        AutoModelForSequenceClassification,
                        AutoTokenizer
                    )

                    model_config = AutoConfig.from_pretrained(
                        model_path, num_labels=configs["task"].num_labels
                    )
                    model = AutoModelForSequenceClassification.from_pretrained(
                        model_path, 
                        config=model_config,
                        trust_remote_code=True, 
                        ignore_mismatched_sizes=True
                    )
                    tokenizer = AutoTokenizer.from_pretrained(
                        model_path,
                        trust_remote_code=True
                    )
            except Exception as e:
                current_time = get_current_time()
                print(f"[{current_time}] Error loading model {model_name}: {e}")
                print(
                    f"--{model_name}----------------"
                    f"[{current_time}] Error loading model {model_name}: {e}"
                    f"--------------------",
                    file=error_log,
                )
                error_log.close()
                break

            # get mean token length by check tokens within tokenizer vocab
            if not mean_token_len:
                vocab_tokens = list(tokenizer.vocab.keys())
                mean_token_len = np.mean([len(token) for token in vocab_tokens])

            # Initialize, check and repair meta tensor in the model
            target_layers = ["classifier", "score", "bert.pooler", "weighting_layer"]
            for name, module in model.named_modules():
                for p_name, param in module.named_parameters(recurse=False):
                    if param.device.type == "meta":
                        print(
                            f"Detected meta parameter: {name}.{p_name}, materializing..."
                        )
                        module._parameters[p_name] = torch.nn.Parameter(
                            torch.empty_like(param, device="cpu"),
                            requires_grad=param.requires_grad,
                        )
                for b_name, buffer in module.named_buffers(recurse=False):
                    if buffer.device.type == "meta":
                        print(
                            f"Detected meta buffer: {name}.{b_name}, materializing..."
                        )
                        module.register_buffer(
                            b_name, torch.zeros_like(buffer, device="cpu")
                        )
                for target in target_layers:
                    if name.startswith(target):
                        print("Re-initializing:", name)
                        init_layer(module)

            # Disable safetensors for specific models
            if model_name in model_not_use_safetensors:
                configs["finetune"].save_safetensors = False
            else:
                configs["finetune"].save_safetensors = True

            # Get dataset file paths
            data_dict = {}
            if row["Train"]:
                data_dict["train"] = dataset_path + "/train.csv"
            if row["Dev"]:
                data_dict["dev"] = dataset_path + "/dev.csv"
            if row["Test"]:
                data_dict["test"] = dataset_path + "/test.csv"

            # Determine max sequence length
            data_length = row["length"]
            if tokenizer_type == "singlebase":
                if model_name in deeplearning_models:
                    max_length = int(np.ceil(data_length / 512) * 512)
                else:
                    max_length = int(data_length) + 2
            else:
                len_ranges = list(range(64, 3073, 32))
                max_length = int(data_length / mean_token_len) + 2
                for i in range(len(len_ranges) - 1):
                    len1 = len_ranges[i]
                    len2 = len_ranges[i + 1]
                    if max_length < len1:
                        max_length = len1
                        break
                    elif len1 <= max_length < len2:
                        max_length = len2
                        break

            if max_token_len and max_length > max_token_len:
                max_length = int(max_token_len)

            if fix_token_len and model_name not in deeplearning_models:
                max_length = fix_token_len

            configs["finetune"].metric_for_best_model = row["metric"]
            dynamic_batch_size = determine_batch_size(max_length, batch_size)
            configs["finetune"].per_device_train_batch_size = dynamic_batch_size
            configs["finetune"].per_device_eval_batch_size = dynamic_batch_size

            num_train_data = int(row["Train"])
            epoch = configs["finetune"].num_train_epochs

            scaling_factor = max(1, batch_size // dynamic_batch_size)
            original_grad_accum = configs["finetune"].gradient_accumulation_steps
            configs["finetune"].gradient_accumulation_steps = (
                original_grad_accum * scaling_factor
            )

            step = (
                num_train_data
                * epoch
                // (
                    dynamic_batch_size
                    * configs["finetune"].gradient_accumulation_steps
                    * 10
                )
            )
            configs["finetune"].logging_steps = max(1, step)
            configs["finetune"].eval_steps = max(1, step)
            configs["finetune"].save_steps = max(1, step)

            outdir = f"./finetuned/{model_name}/{dataset_name}/"
            os.makedirs(outdir, exist_ok=True)
            configs["finetune"].output_dir = outdir

            if os.path.exists(outdir + "trainer_state.json"):
                continue

            multi_label_sep = (
                ";"
                if row["labels"] > 1 and row["type"] in ["regression", "multilabel"]
                else None
            )
            dataset = DNADataset.load_local_data(
                data_dict,
                seq_col="sequence",
                label_col="label",
                multi_label_sep=multi_label_sep,
                max_length=max_length,
            )
            seq_sep = "|" if dataset_name == "GUE__EPI_GM12878" else None

            current_time = get_current_time()
            print(f"[{current_time}] Dataset: {dataset_name}")

            # Encode sequences
            try:
                valid_chars = (
                    "ACGTacgt|" if model_name in models_no_char_n else "ACGTNacgtn|"
                )
                dataset.validate_sequences(minl=0, maxl=10010, valid_chars=valid_chars)
                dataset.encode_sequences(
                    remove_unused_columns=True, tokenizer=tokenizer, seq_sep=seq_sep
                )
            except Exception as e:
                current_time = get_current_time()
                print(
                    f"[{current_time}] Error encoding dataset {dataset_name} with model {model_name}: {e}"
                )
                print(
                    f"[{current_time}] Error encoding dataset {dataset_name} with model {model_name}: {e}",
                    file=error_log,
                )
                continue

            # ========================================================
            # Pre-training FLOPs Calculation Block
            # ========================================================
            total_tokens, samples = count_split_tokens(dataset.dataset.get("train", []))

            device = (
                next(model.parameters()).device
                if next(model.parameters(), None) is not None
                else torch.device("cpu")
            )
            flops_counter = FlopsCounter(
                model, include_norm=True, include_act=True, include_embed=True
            )

            if "train" in dataset.dataset and len(dataset.dataset["train"]) > 0:
                batch_sample = dataset.dataset["train"][0]

                input_ids = (
                    torch.tensor(batch_sample["input_ids"]).unsqueeze(0).to(device)
                    if "input_ids" in batch_sample
                    else None
                )
                inputs_embeds = (
                    torch.tensor(batch_sample["inputs_embeds"]).unsqueeze(0).to(device)
                    if "inputs_embeds" in batch_sample
                    else None
                )
                # attention_mask = (
                #     torch.tensor(batch_sample["attention_mask"]).unsqueeze(0).to(device)
                #     if "attention_mask" in batch_sample
                #     else None
                # )

                try:
                    with torch.no_grad():
                        if "evo" in model_name.lower() and hasattr(model, "backbone"):
                            _ = model.backbone.model(
                                inputs_embeds
                                if inputs_embeds is not None
                                else input_ids
                            )
                        elif configs["finetune"].bf16:
                            with torch.autocast(device.type, dtype=torch.bfloat16):
                                _ = model(
                                    inputs_embeds
                                    if inputs_embeds is not None
                                    else input_ids
                                )
                        else:
                            _ = model(
                                inputs_embeds
                                if inputs_embeds is not None
                                else input_ids
                            )
                except Exception:
                    try:
                        with torch.no_grad():
                            if configs["finetune"].bf16:
                                with torch.autocast(device.type, dtype=torch.bfloat16):
                                    _ = model(
                                        input_ids,
                                        attention_mask=torch.ones_like(input_ids),
                                    )
                            else:
                                _ = model(
                                    input_ids, attention_mask=torch.ones_like(input_ids)
                                )
                    except Exception as e2:
                        print(f"FLOPs counting forward pass failed: {e2}")

                flops_counter.remove_hooks()

                current_tokens = (
                    input_ids.shape[-1]
                    if input_ids is not None
                    else (inputs_embeds.shape[1] if inputs_embeds is not None else 0)
                )
                out_stats = os.path.join(outdir, "flops_report.json")
                flops_counter.save_to_json(
                    num_tokens=current_tokens,
                    all_tokens=total_tokens,
                    filepath=out_stats,
                )
            else:
                flops_counter.remove_hooks()
                current_tokens = 0
            # ========================================================

            if model_name in deeplearning_models:
                model.target_length = max_length // model.resolution

            trainer = DNATrainer(model=model, config=configs, datasets=dataset)
            # trainer.trainer.args.auto_find_batch_size = True

            args_all = trainer.trainer.args
            args_epochs = args_all.num_train_epochs
            args_steps = getattr(
                trainer.trainer.state, "global_step", args_all.max_steps
            )
            args_bs = args_all.per_device_train_batch_size
            args_grad_acc_steps = args_all.gradient_accumulation_steps
            args_lr = args_all.learning_rate
            args_warmup = args_all.warmup_ratio
            args_scheduler = args_all.lr_scheduler_type
            args_bf16 = args_all.bf16
            args_fp16 = args_all.fp16

            try:
                # train
                train_metrics = trainer.train()
                if isinstance(train_metrics, dict):
                    train_runtime = train_metrics.get("train_runtime", "")
                    train_flops = train_metrics.get("total_flos", "")
                else:
                    train_runtime = getattr(train_metrics, "metrics", {}).get(
                        "train_runtime", ""
                    )
                    train_flops = getattr(train_metrics, "metrics", {}).get(
                        "total_flos", ""
                    )

                checkpoints = glob(outdir + "checkpoint-*")
                all_steps = [int(ckpt.split("-")[-1]) for ckpt in checkpoints]
                last_step = sorted(all_steps)[-1] if all_steps else 0
                if last_step:
                    shutil.copy(
                        outdir + f"checkpoint-{last_step}/trainer_state.json", outdir
                    )
                with open(outdir + "final_metrics.json", "w") as f:
                    json.dump(
                        train_metrics
                        if isinstance(train_metrics, dict)
                        else train_metrics.metrics,
                        f,
                        indent=4,
                    )

                # test
                test_results = trainer.evaluate()
                with open(outdir + "test_metrics.json", "w") as f:
                    json.dump(test_results, f, indent=4)

                # ========================================================
                # Master Performance JSON Updating
                # ========================================================
                model_top_dir = f"./finetuned/{model_name}/"
                performance_json_path = os.path.join(
                    model_top_dir, f"{model_name}_performance.json"
                )

                if os.path.exists(performance_json_path):
                    with open(performance_json_path, "r") as f:
                        master_performance_dict = json.load(f)
                else:
                    master_performance_dict = {"info": model_row, "performance": {}}

                # Calculate fallback FLOPs
                if current_tokens > 0:
                    manual_train_flops = (
                        flops_counter.total_flops
                        * (total_tokens / current_tokens)
                        * 3
                        * args_epochs
                    )
                    if manual_train_flops >= train_flops:
                        train_flops = manual_train_flops

                # Inject model size if missing
                model_size_m = master_performance_dict["info"].get("size (M)", 0)
                if not model_size_m or model_size_m == 0:
                    master_performance_dict["info"]["size (M)"] = round(
                        flops_counter.total_params / 1e6
                    )

                master_performance_dict["performance"][dataset_name] = {
                    "dataset": {
                        "species": model_row.get("species", "unknown"),
                        "type": row.get("type", ""),
                        "labels": row.get("labels", 0),
                        "train": row.get("Train", 0),
                        "test": row.get("Test", 0),
                        "dev": row.get("Dev", 0),
                        "length": row.get("length", 0),
                        "metric": row.get("metric", ""),
                    },
                    "parameters": {
                        "epochs": args_epochs,
                        "steps": args_steps,
                        "batch_size": args_bs,
                        "gradient_accumulation_steps": args_grad_acc_steps,
                        "learning_rate": args_lr,
                        "warmup": args_warmup,
                        "lr_scheduler_type": args_scheduler,
                        "bf16": args_bf16,
                        "fp16": args_fp16,
                    },
                    "performance": {
                        "runtime": train_runtime,
                        "FLOPs": train_flops,
                        "loss": test_results.get("eval_loss", ""),
                        "accuracy": test_results.get("eval_accuracy", ""),
                        "precision": test_results.get("eval_precision", ""),
                        "recall": test_results.get("eval_recall", ""),
                        "f1": test_results.get("eval_f1", ""),
                        "mcc": test_results.get("eval_mcc", ""),
                        "auroc": test_results.get("eval_auroc", ""),
                        "auprc": test_results.get("eval_auprc", ""),
                        "pearson_r": test_results.get("eval_pearson_r", ""),
                        "spearman_r": test_results.get("eval_spearman_r", ""),
                        "mse": test_results.get("eval_mse", ""),
                        "r2": test_results.get("eval_r2", ""),
                    },
                }

                with open(performance_json_path, "w") as f:
                    json.dump(master_performance_dict, f, indent=4)

            except Exception as e:
                current_time = get_current_time()
                print(
                    f"[{current_time}] Error finetuning dataset {dataset_name} with model {model_name}: {e}"
                )
                print(
                    f"[{current_time}] Error finetuning dataset {dataset_name} with model {model_name}: {e}",
                    file=error_log,
                )
                continue

            if remove_checkpoints:
                for checkpoint in checkpoints:
                    if not checkpoint.endswith("-" + str(last_step)):
                        shutil.rmtree(checkpoint)
            if remove_pt:
                for pt_file in glob(outdir + "checkpoint-*/*.pt"):
                    os.remove(pt_file)

            count += 1

        error_log.close()


if __name__ == "__main__":
    base_dir = "./"

    with open(os.path.join(base_dir, "datasets_info.json"), "r") as f:
        datasets_info = json.load(f)

    with open(os.path.join(base_dir, "models_info.json"), "r") as f:
        models_info = json.load(f)

    model_not_use_safetensors = [
        "hyenadna-large-1m-seqlen-hf",
        "caduceus-ph_seqlen-131k_d_model-256_n_layer-16",
        "caduceus-ps_seqlen-131k_d_model-256_n_layer-16",
        "Omni-DNA-700M",
        "plant-dnamamba-BPE",
        "plant-dnamamba-6mer",
        "enformer-official-rough",
        "space",
        "evo2_1b_base",
        "megaDNA_updated",
    ]
    deeplearning_models = [
        "enformer-official-rough",
        "space",
        "borzoi-replicate-0",
        "flashzoi-replicate-0",
    ]
    models_no_char_n = deeplearning_models + [
        "PlantCAD2-Small-l24-d0768",
        "PlantCAD2-Medium-l48-d1024",
        "PlantCAD2-Large-l48-d1536",
        "prokbert-mini",
        "prokbert-mini-c",
        "prokbert-mini-long",
        "MutBERT",
        "MutBERT-Multi",
        "megaDNA_updated",
    ]
    models_with_limited_length = {
        "prokbert-mini": 1027,
        "plant-dnabert-6mer": 512,
    }
    models_only_support_fp32 = [
        "Jamba-DNA-v1-114M-hg38",
    ]
    special_models = ["evo2_1b_base", "megaDNA_updated"]

    main()
