"""
flops_counter.py — CPU-importable FlopsCounter port (Phase 7, PIPE-01).

Ported from the deprecated ``pipeline/dnallmmark_pipeline.py:43-720`` (the
legacy per-architecture FLOPs accounting; that file is scheduled for
deletion per D-04 — git history remains the reference). Hook formulas and
the ``_register_hooks`` dispatch order are ported VERBATIM: the math
encodes non-obvious decisions behind every historical leaderboard number,
so re-derivation is forbidden (Don't-Hand-Roll discipline).

ONE structural change vs legacy (07-CONTEXT discretion clause):
``torch.nn`` resolves through the lazy :func:`_torch_nn` seam (or
constructor injection via ``nn_module=``) — never at module top — so the
torch-free CPU dev/CI lane imports and stub-tests this module with no GPU
and no dnallm (PIPE-01 success criterion 2).

Additions over the legacy report (all additive, D-02/D-03/D-05/D-27):
- ``schema_version`` — always 1 (D-27)
- ``uncovered_layers`` — parameter-owning modules that no dispatch branch
  hooked, listed loudly; a parameter share above
  :data:`UNCOVERED_PARAM_SHARE_THRESHOLD` prints a console WARNING at save
  time (D-03: 宁可噪声不可静默少计 — noise over silent under-counting)
- optional ``hardware`` section (D-05) via ``save_to_json(hardware=...)``
- deterministic write discipline: indent=4, ensure_ascii=False,
  sort_keys=True (the run_sweep._write_json discipline)
"""

import json
from pathlib import Path

# D-03: uncovered parameter share above this fraction triggers a console
# WARNING at save time (planner-set per 07-RESEARCH Pattern 1 item 7 —
# conventional architectures are fully covered with include_* True, so the
# threshold is unreachable noise-free).
UNCOVERED_PARAM_SHARE_THRESHOLD = 0.05


def _torch_nn():
    """Lazily import torch.nn — the module-top seam this file never touches.

    The CPU dev/CI lane has no torch installed; tests monkeypatch this
    accessor with a duck-typed stub module exposing Linear/Conv1d/Conv2d/
    MultiheadAttention/Embedding/LayerNorm/SiLU/GELU/ReLU.
    """
    from torch import nn

    return nn


def _directly_owns_parameters(module):
    """True when ``module`` carries its own parameters.

    torch keeps directly-owned parameters in ``module._parameters``; pure
    containers (Sequential, the root model) have an empty dict, so they are
    excluded from uncovered accounting by construction.
    """
    return bool(getattr(module, "_parameters", None))


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
        nn_module=None,
    ):
        self.model = model
        self.include_norm = include_norm
        self.include_act = include_act
        self.include_embed = include_embed
        self.architecture = architecture
        self._nn = nn_module if nn_module is not None else _torch_nn()

        self.total_flops = 0
        self.total_params = sum(p.numel() for p in model.parameters())
        self.layer_flops = {}
        self.hooks = []
        self._is_active = True
        self._hooked_names = set()
        self.uncovered_layers = []

        self._register_hooks()

    def _register_hooks(self):
        nn = self._nn
        for name, module in self.model.named_modules():
            classname = module.__class__.__name__
            hooks_before = len(self.hooks)

            # 1. Core Heavy Computation Layers
            if isinstance(module, nn.Linear):
                self.hooks.append(
                    module.register_forward_hook(self._linear_hook(name))
                )
            elif isinstance(module, nn.Conv1d):
                self.hooks.append(
                    module.register_forward_hook(self._conv1d_hook(name))
                )
            elif isinstance(module, nn.Conv2d):
                self.hooks.append(
                    module.register_forward_hook(self._conv2d_hook(name))
                )
            elif isinstance(module, nn.MultiheadAttention):
                self.hooks.append(
                    module.register_forward_hook(self._mha_hook(name))
                )
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
            elif classname in [
                "LlamaAttention",
                "GemmaAttention",
                "GemmaFlashAttention2",
                "GemmaSdpaAttention",
            ]:
                self.hooks.append(
                    module.register_forward_hook(self._gqa_attn_hook(name))
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

            # Uncovered accounting (D-03, new): a parameter-owning module
            # that matched no dispatch branch is recorded loudly.
            if len(self.hooks) > hooks_before:
                self._hooked_names.add(name)
            elif _directly_owns_parameters(module):
                self.uncovered_layers.append(
                    {"name": name, "classname": classname}
                )

    def uncovered_param_share(self):
        """Parameter share under NO hooked module's subtree (D-03).

        Derived by ``named_parameters()`` prefix matching against the hooked
        module names: a parameter counts as covered exactly when its
        qualified name lies inside a hooked module's subtree.
        """
        if self.total_params == 0:
            return 0.0
        uncovered = 0
        for param_name, param in self.model.named_parameters():
            covered = any(
                param_name == hooked or param_name.startswith(hooked + ".")
                for hooked in self._hooked_names
            )
            if not covered:
                uncovered += param.numel()
        return uncovered / self.total_params

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
        self,
        num_tokens=None,
        all_tokens=None,
        filepath="flops_report.json",
        hardware=None,
    ):
        per_token_flops = (
            self.total_flops / num_tokens if num_tokens is not None else None
        )
        all_tokens_flops = (
            self.total_flops * all_tokens / num_tokens
            if all_tokens is not None and num_tokens is not None
            else None
        )
        # Legacy guarded only total_params > 0, so num_tokens=None crashed on
        # ``None / total_params``; the ratio is null whenever the per-token
        # extrapolation is unavailable (schema allows null).
        computation_size_ratio = (
            per_token_flops / self.total_params
            if per_token_flops is not None and self.total_params > 0
            else None
        )
        uncovered_share = self.uncovered_param_share()
        if uncovered_share > UNCOVERED_PARAM_SHARE_THRESHOLD:
            print(
                f"WARNING: uncovered parameter share {uncovered_share:.2%} exceeds "
                f"{UNCOVERED_PARAM_SHARE_THRESHOLD:.0%} — FLOPs are UNDER-counted "
                f"for {len(self.uncovered_layers)} layer(s): "
                f"{[entry['name'] for entry in self.uncovered_layers]}"
            )
        report = {
            "schema_version": 1,
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
            "uncovered_layers": self.uncovered_layers,
        }
        if hardware is not None:
            report["hardware"] = hardware
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False, sort_keys=True)


def count_split_tokens(hf_dataset):
    """Count total input_ids tokens and carrying samples in a HF split
    (ported verbatim from dnallmmark_pipeline.py:711-720)."""
    if hf_dataset is None:
        return 0, 0
    n_tokens = 0
    n_samples = 0
    for x in hf_dataset:
        if "input_ids" in x:
            n_tokens += len(x["input_ids"])
            n_samples += 1
    return n_tokens, n_samples


def build_hardware_section(gpu_device=None, train_time=None, max_mem_gb=None):
    """Build the optional D-05 hardware/runtime section as a plain dict.

    Pure: no torch inside — the pipeline side captures the values
    (``gpu_device`` verbatim from ``torch.cuda.get_device_name()``, no enum
    mapping; ``train_time`` from trainer metrics; ``max_mem_gb`` from the
    peak-memory read) and passes them in; each field is nullable so a
    CPU-only or NPU run records nulls rather than lying.

    Args:
        gpu_device: GPU name string or None.
        train_time: training wall-time in seconds or None.
        max_mem_gb: peak CUDA memory in GiB or None.

    Returns:
        dict: the closed ``hardware`` section for ``save_to_json``.
    """
    return {
        "gpu_device": gpu_device,
        "train_time": train_time,
        "max_mem_gb": max_mem_gb,
    }
