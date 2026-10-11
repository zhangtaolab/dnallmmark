"""
flops_counter.py — CPU-importable FlopsCounter port (Phase 7, PIPE-01).

RED-PHASE SKELETON: public API surface only, no behavior yet — the failing
tests in tests/test_flops_counter.py drive the GREEN implementation.
"""

UNCOVERED_PARAM_SHARE_THRESHOLD = 0.05


def _torch_nn():
    import torch.nn as nn

    return nn


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
        self.total_params = 0
        self.layer_flops = {}
        self.hooks = []
        self.uncovered_layers = []

    def remove_hooks(self):
        pass

    def save_to_json(
        self,
        num_tokens=None,
        all_tokens=None,
        filepath="flops_report.json",
        hardware=None,
    ):
        pass

    def uncovered_param_share(self):
        return 0.0


def count_split_tokens(hf_dataset):
    return 0, 0


def build_hardware_section(gpu_device=None, train_time=None, max_mem_gb=None):
    return {}
