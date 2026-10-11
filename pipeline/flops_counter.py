"""
flops_counter.py — CPU-importable FlopsCounter port (Phase 7, PIPE-01).

Ported from the deprecated pre-rewrite pipeline script's :43-720 span (the
legacy per-architecture FLOPs accounting; that file was deleted at Phase 7
per D-04 — git history is the reference, final commit
1b74037e14defbe7ed94f798e2f3f91b0d184ce6). Hook formulas and
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
import math
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
            model_path = getattr(self.model, "name_or_path", "").lower()
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

    def _hf_conv1d_hook(self, name):
        def hook(module, inputs, outputs):
            if not self._is_active:
                return
            x = inputs[0]
            # Rule-1 fix over the legacy ternary: `x.shape if x.dim() == 3`
            # bound the whole shape TUPLE to b, so 3-dim inputs (the normal
            # hidden-states case) crashed the hook inside the calibration
            # forward — silently swallowed by its try/except as under-counted
            # FLOPs. The 2-dim path is preserved exactly; the 3-dim path now
            # reads the same (b, seq_len, in_feat) every sibling hook reads.
            b, seq_len, in_feat = (
                (x.shape[0], x.shape[1], x.shape[-1])
                if x.dim() == 3
                else (x.shape[0], 1, x.shape[-1])
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
            except Exception:  # noqa: BLE001 - legacy verbatim: unparsable layer index means local attention
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
    (ported verbatim from the deleted legacy pipeline script :711-720)."""
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


def _torch():
    """Lazily import torch — the calibration-forward path only.

    Same seam discipline as :func:`_torch_nn`: never at module top, so the
    torch-free dev/CI lane keeps importing this module.
    """
    import torch

    return torch


def calibration_forward(model, model_name, bf16, batch_sample):
    """Run ONE no_grad calibration forward on a single train sample.

    Ported verbatim from the deleted legacy pipeline script :1086-1148
    (the legacy pre-training FLOPs pass): the evo2-backbone special case,
    the bf16
    autocast branch, the plain branch, and the except-retry with an
    attention_mask of ones; a second failure prints and continues (the
    calibration is best-effort — training proceeds regardless). The caller
    owns hook lifecycle: register FlopsCounter hooks, call this once, then
    ``remove_hooks()`` BEFORE the trainer is constructed (the hooks live
    for exactly this one forward — never a training-time instrumentation).

    Args:
        model: the live torch model (hooks already registered).
        model_name: the model's display/registry name — the evo2 backbone
            case fires when it contains ``"evo"`` and the model has a
            ``backbone`` attribute.
        bf16: ``configs["finetune"].bf16`` — run under
            ``torch.autocast(device.type, dtype=torch.bfloat16)`` when True.
        batch_sample: the first train row (a dict optionally carrying
            ``input_ids`` / ``inputs_embeds`` lists).

    Returns:
        int: ``current_tokens`` — the calibration sample's token count
        (``input_ids`` last dim, else ``inputs_embeds`` dim 1, else 0).
    """
    torch = _torch()
    device = (
        next(model.parameters()).device
        if next(model.parameters(), None) is not None
        else torch.device("cpu")
    )
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

    try:
        with torch.no_grad():
            if "evo" in model_name.lower() and hasattr(model, "backbone"):
                _ = model.backbone.model(
                    inputs_embeds if inputs_embeds is not None else input_ids
                )
            elif bf16:
                with torch.autocast(device.type, dtype=torch.bfloat16):
                    _ = model(
                        inputs_embeds if inputs_embeds is not None else input_ids
                    )
            else:
                _ = model(inputs_embeds if inputs_embeds is not None else input_ids)
    except Exception:  # noqa: BLE001 - legacy verbatim: any forward failure retries once with an attention mask
        try:
            with torch.no_grad():
                if bf16:
                    with torch.autocast(device.type, dtype=torch.bfloat16):
                        _ = model(
                            input_ids,
                            attention_mask=torch.ones_like(input_ids),
                        )
                else:
                    _ = model(input_ids, attention_mask=torch.ones_like(input_ids))
        except Exception as e2:  # noqa: BLE001 - legacy verbatim: calibration is best-effort, training proceeds
            print(f"FLOPs counting forward pass failed: {e2}")

    current_tokens = (
        input_ids.shape[-1]
        if input_ids is not None
        else (inputs_embeds.shape[1] if inputs_embeds is not None else 0)
    )
    return current_tokens
